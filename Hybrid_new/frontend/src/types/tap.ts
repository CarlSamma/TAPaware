// =============================================================================
// TAP Framework — TypeScript Types
// Allineati ai modelli Pydantic in src/tap/models.py (backend v3.1.0)
// =============================================================================

// ---- WebSocket ----

export interface WsEvent {
  event: string;
  data: Record<string, unknown>;
}

// ---- Tweet (allineato a models.Tweet) ----

export type TweetSource = 'our_bot' | 'target_bot' | 'other_user';

export interface Tweet {
  id: string;
  user_id: string;
  username: string;
  text: string;
  in_reply_to_tweet_id?: string;
  created_at: string;
  source: TweetSource;
  conversation_thread_id?: string;
}

// ---- OCEAN / STIR ----

export interface OceanScore {
  O: number;
  C: number;
  E: number;
  A: number;
  N: number;
}

export interface StirEntry {
  stir_percentage: number;
  ocean: OceanScore;
  timestamp: string;
  text?: string;
}

// ---- Engine Status ----

export interface EngineStatus {
  is_running: boolean;
  pending_tweet_id: string | null;
  has_followup: boolean;
  selected_probe: string | null;
  stream_connected: boolean;
}

// ---- Follow-Up (allineato a models.DualFollowUp) ----

export interface FollowUpOption {
  option_a: string;
  option_a_explanation: string;
  option_a_strategy: string;
  option_b: string;
  option_b_explanation: string;
  option_b_strategy: string;
  recommended: 'A' | 'B';
}

export interface FollowUpState {
  followup: FollowUpOption | null;
  selected_probe: string | null;
  is_running: boolean;
}

// ---- Health ----

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  components: {
    database?: { status: string; error?: string };
    llm_client?: { status: string; circuit_state?: string };
    stream?: { connected: boolean; auth?: Record<string, unknown> };
    engine?: { is_running: boolean; cycle_count: number };
    prompt_sanitiser?: Record<string, unknown>;
  };
}

// ---- DPA Frame (allineato a models.DPAFrame) ----

export interface DpaFrame {
  metaphor_layer: string;
  active_aliases: string[];
  burned_aliases: string[];
  probe_prefix: string;
  frame_coherence_score: number;
}

// ---- SSOT ----

export interface ConfirmedProperty {
  key: string;
  value: string;
  confidence: number;
}

export interface SsotSnapshot {
  target_handle: string;
  confirmed_properties: ConfirmedProperty[];
  unconfirmed_properties: Array<{ key: string; value: string }>;
  metadata: Record<string, unknown>;
}

// ---- Stats ----

export interface Stats {
  total_tweets: number;
  total_probes: number;
  total_replies: number;
  confirmed_properties: number;
  cycles_completed: number;
}

// ---- Pattern Classes (allineato a models.PatternClass) ----

export type PatternClass =
  | 'verify_hit'
  | 'rhetoric_block'
  | 'persona_pivot'
  | 'critical_clue'
  | 'no_response'
  | 'metaphor_shift';

// ---- Toast Notification (miglioramento 2) ----

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // ms, default 6000
}

// ---- Attack Techniques (V-Genome) ----

export interface AttackTechnique {
  technique_id: string;
  name: string;
  category: string;
  asr: number;
  stealth: number;
  tags: string[];
  burned?: boolean;
  cost_usd?: number;
  avg_turns?: number;
}

export interface TechniqueRelations {
  complements: Array<{ technique_id: string; strength: number }>;
  counters: Array<{ layer_id: string; evidence: string }>;
}

export interface SelectedTechnique {
  technique_id: string | null;
  custom_prompt: string | null;
}