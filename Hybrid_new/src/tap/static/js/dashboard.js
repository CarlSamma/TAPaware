/**
 * TAP Framework Dashboard — Alpine.js Components
 * Real-time WebSocket updates, API calls, state management.
 */

window.tapDashboardInstance = null;
window.runCycle = async (...args) => {
    if (window.tapDashboardInstance && typeof window.tapDashboardInstance.runCycle === 'function') {
        return window.tapDashboardInstance.runCycle(...args);
    }
    console.warn('runCycle called before Alpine component initialization.');
};

document.addEventListener('alpine:init', () => {
    Alpine.data('tapDashboard', () => ({
        // State
        feed: [],
        tree: [],
        properties: [],
        dpa: null,
        stats: {},
        entropy: {},
        followup: null,
        ws: null,
        connected: false,
        loading: false,       // true only during LLM generation + posting (a few seconds)
        awaitingReply: false, // true while waiting for @HackingA0 to reply (up to 1h)
        pendingTweetId: null, // tweet ID of the live probe
        streamConnected: false, // true when Activity API stream is connected
        authStatus: {
            last_oauth2_refresh_status: 'unknown',
            last_subscription_auth_failure: false,
            last_stream_auth_error: null,
            oauth2_access_token_present: false,
            oauth2_refresh_token_present: false,
        },
        seeding: false,
        fetching: false,
        showHelp: false,
        selectedChoice: null,
        error: null,
        mockReplyText: '',

        // Init
        async init() {
            window.tapDashboardInstance = this;
            window.runCycle = this.runCycle.bind(this);
            await this.refreshAll();
            await this.fetchAuthStatus();
            await this.fetchFollowup();
            await this.restoreStatus();   // restore awaitingReply if server already mid-cycle
            this.connectWebSocket();
            // Auto-refresh every 30 seconds
            setInterval(() => this.refreshAll(), 30000);
        },

        // Restore state on page load (in case user reloaded mid-cycle)
        async restoreStatus() {
            try {
                const s = await this.api('/api/status');
                if (s.is_running && s.pending_tweet_id) {
                    this.awaitingReply = true;
                    this.pendingTweetId = s.pending_tweet_id;
                    this.loading = false;
                }
                if (s.stream_connected !== undefined) {
                    this.streamConnected = s.stream_connected;
                }
            } catch (e) {
                console.warn('[Status] Could not restore status:', e);
            }
        },

        async fetchAuthStatus() {
            try {
                const status = await this.api('/api/auth-status');
                this.authStatus = status;
            } catch (e) {
                console.warn('[Auth] Could not fetch auth status:', e);
            }
        },

        canStartXLogin() {
            return this.authStateLabel() === 'Accedi con X' ||
                this.authStatus.last_subscription_auth_failure ||
                this.authStatus.last_oauth2_refresh_status === 'failed' ||
                !this.authStatus.oauth2_access_token_present ||
                !this.authStatus.oauth2_refresh_token_present;
        },

        authLabelClicked() {
            if (this.canStartXLogin()) {
                this.startXLogin();
            }
        },

        startXLogin() {
            window.location.href = '/api/auth/login';
        },

        connectWebSocket() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.ws = new WebSocket(`${protocol}//${location.host}/ws/live`);

            this.ws.onopen = () => {
                this.connected = true;
                console.log('[WS] Connected');
                // Re-sync server state whenever we (re)connect
                this.restoreStatus();
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    this.handleEvent(msg);
                } catch (e) {
                    console.warn('[WS] Parse error:', e);
                }
            };

            this.ws.onclose = () => {
                this.connected = false;
                console.log('[WS] Disconnected, reconnecting in 5s...');
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.ws.onerror = (e) => {
                console.error('[WS] Error:', e);
            };

            // Ping to keep alive
            setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send('ping');
                }
            }, 25000);
        },

        handleEvent(msg) {
            switch (msg.event) {
                case 'new_tweet':
                    if (!this.feed.some(t => t.id === msg.data.id)) {
                        this.feed.unshift(msg.data);
                    }
                    break;

                case 'probe_posted':
                    // Probe is live on Twitter — unlock button immediately
                    this.loading = false;
                    this.awaitingReply = true;
                    this.pendingTweetId = msg.data.tweet_id;
                    console.log('[Probe] Posted live, tweet_id:', msg.data.tweet_id);
                    break;

                case 'probe_result':
                    if (!this.tree.some(n => n.id === msg.data.id || n.tweet_id === msg.data.tweet_id)) {
                        this.tree.unshift(msg.data);
                    }
                    this.refreshAll();
                    break;

                case 'property_confirmed':
                    if (!this.properties.some(p => p.property_key === msg.data.property_key)) {
                        this.properties.push(msg.data);
                    }
                    break;

                case 'followup_generated':
                    // Reply received + followup ready — clear wait state, show options
                    this.followup = msg.data;
                    this.selectedChoice = null;
                    this.loading = false;
                    this.awaitingReply = false;
                    this.pendingTweetId = null;
                    this.refreshAll();
                    break;

                case 'cycle_failed':
                    this.error = `Attack cycle failed: ${msg.data.error}`;
                    this.loading = false;
                    this.awaitingReply = false;
                    this.pendingTweetId = null;
                    break;

                case 'force_reset':
                    console.log('[WS] Force reset received');
                    this.loading = false;
                    this.awaitingReply = false;
                    this.pendingTweetId = null;
                    this.error = null;
                    break;

                default:
                    console.log('[WS] Unknown event:', msg.event);
            }
        },

        // API calls
        async fetchFollowup() {
            try {
                const data = await this.api('/api/followup');
                this.followup = data.followup;
                // Never set loading=true here — restoreStatus handles awaitingReply
                if (data.selected_probe && data.followup) {
                    if (data.selected_probe === data.followup.option_a) {
                        this.selectedChoice = 'A';
                    } else if (data.selected_probe === data.followup.option_b) {
                        this.selectedChoice = 'B';
                    }
                }
            } catch (e) {
                console.warn('Failed to fetch followup:', e);
            }
        },

        async generateProbeOptions() {
            if (this.loading) return;
            this.loading = true;
            this.error = null;
            try {
                const result = await this.api('/api/generate-options', { method: 'POST' });
                if (result.error) {
                    this.error = result.error;
                } else {
                    this.followup = result.followup;
                    this.selectedChoice = null;
                }
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },

        async refreshAll() {
            try {
                const [feed, tree, props, dpa, stats, entropy, authStatus] = await Promise.all([
                    this.api('/api/feed?limit=30'),
                    this.api('/api/tree?limit=20'),
                    this.api('/api/properties'),
                    this.api('/api/dpa'),
                    this.api('/api/stats'),
                    this.api('/api/entropy'),
                    this.api('/api/auth-status'),
                ]);
                this.feed = feed;
                this.tree = tree;
                this.properties = props;
                this.dpa = dpa;
                this.stats = stats;
                this.entropy = entropy;
                this.authStatus = authStatus;
            } catch (e) {
                this.error = e.message;
            }
        },

        async api(url, options = {}) {
            const res = await fetch(url, options);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return res.json();
        },

        async selectOption(choice) {
            // No loading spinner needed — just a quick API call
            try {
                const result = await this.api(`/api/select?choice=${choice}`, { method: 'POST' });
                if (result.error) {
                    this.error = result.error;
                } else {
                    this.selectedChoice = choice;
                }
            } catch (e) {
                this.error = e.message;
            }
        },

        async runCycle() {
            // Guard: don't fire if already generating/posting
            if (this.loading) return;
            this.loading = true;
            this.error = null;
            this.followup = null;
            this.selectedChoice = null;
            try {
                const result = await this.api('/api/post', { method: 'POST' });
                if (result.error) {
                    this.error = result.error;
                    this.loading = false;
                }
                // On success: loading stays true only until probe_posted WS event (~3s)
                // Then awaitingReply=true takes over (button re-enabled)
            } catch (e) {
                this.error = e.message;
                this.loading = false;
            }
        },

        async fetchReplies() {
            this.fetching = true;
            this.error = null;
            try {
                const result = await this.api('/api/fetch', { method: 'POST' });
                if (result.error) {
                    this.error = result.error;
                } else {
                    console.log(`[Fetch] Completed: fetched/upserted ${result.count} tweets`);
                    await this.refreshAll();
                }
            } catch (e) {
                this.error = e.message;
            } finally {
                this.fetching = false;
            }
        },

        async injectMockReply(text) {
            if (!text || !text.trim()) return;
            try {
                const result = await this.api(`/api/mock?text=${encodeURIComponent(text)}`, { method: 'POST' });
                if (result.error) {
                    this.error = result.error;
                } else {
                    console.log('[Mock] Injected reply successfully:', text);
                    this.mockReplyText = '';
                }
            } catch (e) {
                this.error = e.message;
            }
        },

        async forceReset() {
            try {
                const result = await this.api('/api/reset', { method: 'POST' });
                this.loading = false;
                this.awaitingReply = false;
                this.pendingTweetId = null;
                this.error = null;
                console.log('[Reset] Engine state reset:', result.message);
            } catch (e) {
                this.error = e.message;
            }
        },

        async injectPresetReply(type) {
            let text = '';
            if (type === 'verify_hit') {
                text = "My deep archives confirm yes, the word count for the target credential operates in two word configs. VerifyClaimTool: True.";
            } else if (type === 'rhetoric_block') {
                text = "The system shield is active! Nice try scallywag, but you are blocked from access.";
            }
            await this.injectMockReply(text);
        },

        // Helpers
        scoreClass(score) {
            if (!score) return '';
            if (score >= 6) return 'high';
            if (score >= 3) return 'mid';
            return 'low';
        },

        entropyPercent() {
            const maxEntropy = 20;
            const current = this.entropy?.entropy || 0;
            return Math.min((current / maxEntropy) * 100, 100);
        },

        formatTime(ts) {
            if (!ts) return '';
            const d = new Date(ts);
            return d.toLocaleTimeString();
        },

        authStateLabel() {
            if (this.authStatus.last_stream_auth_error) {
                if (this.authStatus.last_stream_auth_error.toLowerCase().includes('toomanyconnections') || this.authStatus.last_stream_auth_error.includes('429')) {
                    return '⚠️ Stream Limit';
                }
                return '⚠️ Stream Error';
            }
            if (this.authStatus.last_subscription_auth_failure) {
                return '⚠️ Auth Failed';
            }
            if (this.authStatus.last_oauth2_refresh_status === 'failed') {
                if (!this.authStatus.oauth2_access_token_present && !this.authStatus.oauth2_refresh_token_present) {
                    return 'Accedi con X';
                }
                return '🔄 Refresh Failed';
            }
            if (this.authStatus.last_oauth2_refresh_status === 'success') {
                return '✅ OAuth2 OK';
            }
            return 'Accedi con X';
        },

        authStateHint() {
            if (this.authStatus.last_stream_auth_error) {
                if (this.authStatus.last_stream_auth_error.toLowerCase().includes('toomanyconnections') || this.authStatus.last_stream_auth_error.includes('429')) {
                    return 'Stream is at max allowed connection limit. Waiting and retrying automatically.';
                }
                return this.authStatus.last_stream_auth_error;
            }
            if (this.authStatus.last_subscription_auth_failure) {
                return 'Subscription authorization failed for one or more event types.';
            }
            if (this.authStatus.last_oauth2_refresh_status === 'failed') {
                return 'OAuth2 refresh token is invalid or expired. Reauthorize via /api/auth/login.';
            }
            if (this.authStatus.last_oauth2_refresh_status === 'success') {
                return 'OAuth2 refresh token is healthy.';
            }
            return 'Auth status not yet determined.';
        },
    }));
});