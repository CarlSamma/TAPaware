# GUIDA PRATICA: Implementazione Step-by-Step OAuth 2.0 PKCE per X API

## Da Token Manuali a Flusso OAuth Automatico — Procedura Operativa

> **Obiettivo:** Sostituire l'autenticazione manuale con un flusso OAuth 2.0 PKCE completo, dal pulsante frontend al rinnovo automatico dei token.
>
> **Prerequisiti:** Account sviluppatore X con app creata su `console.x.com`

---

## FASE 0 — Verifica Prerequisiti

### 0.1 Cosa ti serve prima di iniziare

```
✅ Account X Developer (gratuito o paid)
✅ App creata su console.x.com
✅ Client ID e Client Secret ottenuti
✅ App con "User authentication settings" configurati
✅ Node.js 18+ o Python 3.9+ installato
✅ Server con HTTPS (obbligatorio per redirect_uri)
```

### 0.2 Configurazione su console.x.com — Procedura Dettagliata

1. Vai su `https://developer.x.com` → **Developer Console**
2. Seleziona il tuo progetto → la tua app
3. Nella scheda **"Settings"**, scorri fino a **"User authentication settings"**
4. Clicca **"Set up"** e compila:

```
App permissions:          Read and write
Type of App:              Web App, Automated App or Bot
Callback URI:             https://localhost:3000/api/auth/callback
                         (o il tuo dominio di produzione)
Website URL:              https://localhost:3000
```

5. Clicca **"Save"**
6. Vai nella scheda **"Keys and tokens"**
7. Nella sezione **"OAuth 2.0 Client ID and Client Secret"**:
   - Copia il **Client ID**
   - Genera e copia il **Client Secret**
8. Salvali immediatamente in un posto sicuro

### 0.3 Struttura del Progetto

```
progetto/
├── .env                          # ← Crea questo file
├── .gitignore                    # ← Assicurati che .env sia ignorato
├── server.js                     # ← Entry point (Node.js)
│   oppure app.py                 # ← Entry point (Python)
├── routes/
│   └── auth.js                   # ← Route OAuth
├── services/
│   ├── xOAuth.js                 # ← Logica OAuth
│   └── xApi.js                   # ← Chiamate API
├── public/
│   └── index.html                # ← Frontend con pulsante login
└── package.json
```

### 0.4 Creare il file `.env`

Crea il file `.env` nella root del progetto:

```env
# X API OAuth 2.0 Credentials
X_CLIENT_ID=tuo_client_id_qui
X_CLIENT_SECRET=tuo_client_secret_qui
X_REDIRECT_URI=http://localhost:3000/api/auth/callback

# App
PORT=3000
SESSION_SECRET=una_stringa_casuale_molto_lunga_e_sicura
```

### 0.5 Aggiornare `.gitignore`

```gitignore
# Environment
.env
.env.local
.env.*.local

# Node
node_modules/

# Python
__pycache__/
*.pyc
.venv/
venv/
```

---

## FASE 1 — Setup del Progetto

### Opzione A: Node.js + Express

```bash
# Inizializza progetto
npm init -y

# Installa dipendenze
npm install express express-session axios dotenv

# Per development (opzionale)
npm install --save-dev nodemon
```

Crea `server.js`:

```javascript
require('dotenv').config();
const express = require('express');
const session = require('express-session');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Session middleware (necessario per salvare code_verifier e state)
app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false,        // true in produzione con HTTPS
        httpOnly: true,
        maxAge: 600000        // 10 minuti (sufficienti per il flusso OAuth)
    }
}));

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Importa le route
app.use('/api/auth', require('./routes/auth'));

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
```

### Opzione B: Python + Flask

```bash
# Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Installa dipendenze
pip install flask requests python-dotenv
```

Crea `app.py`:

```python
import os
from flask import Flask, session, redirect, url_for, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ['SESSION_SECRET']
app.config['SESSION_TYPE'] = 'filesystem'

# Importa le route
from routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

if __name__ == '__main__':
    app.run(debug=True, port=3000)
```

---

## FASE 2 — Implementare il Servizio OAuth

### 2.1 Creare `services/xOAuth.js` (Node.js)

```javascript
// services/xOAuth.js
const crypto = require('crypto');
const axios = require('axios');

/**
 * Genera code_verifier e code_challenge per PKCE.
 * - code_verifier: stringa casuale URL-safe (43-128 caratteri)
 * - code_challenge: SHA-256 del verifier, codificata Base64URL (senza padding)
 */
function generatePKCE() {
    const codeVerifier = crypto.randomBytes(32).toString('base64url');
    const codeChallenge = crypto
        .createHash('sha256')
        .update(codeVerifier)
        .digest('base64url');  // base64url rimuove automaticamente il padding '='
    return { codeVerifier, codeChallenge };
}

/**
 * Genera un parametro state casuale per prevenire CSRF.
 */
function generateState() {
    return crypto.randomBytes(16).toString('hex');
}

/**
 * Costruisce l'URL di autorizzazione a cui reindirizzare l'utente.
 */
function buildAuthorizationUrl(codeChallenge, state) {
    const params = new URLSearchParams({
        response_type: 'code',
        client_id: process.env.X_CLIENT_ID,
        redirect_uri: process.env.X_REDIRECT_URI,
        scope: 'tweet.read tweet.write users.read offline.access',
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
    });
    return `https://x.com/i/oauth2/authorize?${params.toString()}`;
}

/**
 * Scambia l'authorization code per access_token e refresh_token.
 * Richiede Basic Auth con client_id:client_secret.
 */
async function exchangeCodeForTokens(code, codeVerifier) {
    const clientId = process.env.X_CLIENT_ID;
    const clientSecret = process.env.X_CLIENT_SECRET;
    const authHeader = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

    const params = new URLSearchParams({
        code: code,
        grant_type: 'authorization_code',
        redirect_uri: process.env.X_REDIRECT_URI,
        code_verifier: codeVerifier,
        client_id: clientId,
    });

    const response = await axios.post('https://api.x.com/2/oauth2/token', params.toString(), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Basic ${authHeader}`,
        },
    });

    return {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in || 7200,
        scope: response.data.scope,
        tokenType: response.data.token_type,
    };
}

/**
 * Rinnova l'access_token usando il refresh_token.
 */
async function refreshAccessToken(refreshToken) {
    const clientId = process.env.X_CLIENT_ID;
    const clientSecret = process.env.X_CLIENT_SECRET;
    const authHeader = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

    const params = new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        client_id: clientId,
    });

    const response = await axios.post('https://api.x.com/2/oauth2/token', params.toString(), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Basic ${authHeader}`,
        },
    });

    return {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token || refreshToken,
        expiresIn: response.data.expires_in || 7200,
    };
}

module.exports = {
    generatePKCE,
    generateState,
    buildAuthorizationUrl,
    exchangeCodeForTokens,
    refreshAccessToken,
};
```

### 2.2 Creare `services/xApi.js` (Node.js)

```javascript
// services/xApi.js
const axios = require('axios');
const { refreshAccessToken } = require('./xOAuth');

// Simulazione di un "database" in memoria.
// In produzione: usare un database reale (PostgreSQL, MongoDB, ecc.)
let tokenStore = {
    accessToken: null,
    refreshToken: null,
    expiresAt: null,
};

/**
 * Salva i token nel "database".
 */
function saveTokens(accessToken, refreshToken, expiresIn) {
    tokenStore = {
        accessToken,
        refreshToken,
        expiresAt: Date.now() + (expiresIn * 1000),
    };
}

/**
 * Verifica se il token è scaduto o sta per scadere (5 min di margine).
 */
function isTokenExpired() {
    if (!tokenStore.accessToken || !tokenStore.expiresAt) return true;
    return Date.now() >= (tokenStore.expiresAt - 5 * 60 * 1000);
}

/**
 * Assicura che ci sia un token valido, rinnovandolo se necessario.
 * Lancia un errore se il refresh fallisce (serve riautenticazione).
 */
async function ensureValidToken() {
    if (!isTokenExpired()) return tokenStore.accessToken;

    if (!tokenStore.refreshToken) {
        throw new Error('REAUTH_REQUIRED');
    }

    try {
        const result = await refreshAccessToken(tokenStore.refreshToken);
        saveTokens(result.accessToken, result.refreshToken, result.expiresIn);
        return result.accessToken;
    } catch (error) {
        console.error('Token refresh failed:', error.response?.data || error.message);
        throw new Error('REAUTH_REQUIRED');
    }
}

/**
 * Esegue una chiamata API con gestione automatica del token.
 * Se riceve 401, tenta un refresh e riprova una volta.
 */
async function xApiRequest(method, endpoint, data = null) {
    const token = await ensureValidToken();

    const config = {
        method,
        url: `https://api.x.com/2${endpoint}`,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    };

    if (data) config.data = data;

    try {
        const response = await axios(config);
        return response.data;
    } catch (error) {
        // Se 401, tenta un refresh forzato e riprova
        if (error.response?.status === 401 && tokenStore.refreshToken) {
            console.log('Received 401, attempting token refresh...');
            const result = await refreshAccessToken(tokenStore.refreshToken);
            saveTokens(result.accessToken, result.refreshToken, result.expiresIn);

            // Riprova con il nuovo token
            config.headers.Authorization = `Bearer ${result.accessToken}`;
            const retryResponse = await axios(config);
            return retryResponse.data;
        }
        throw error;
    }
}

// === API METHODS ===

async function postTweet(text) {
    return xApiRequest('POST', '/tweets', { text });
}

async function deleteTweet(tweetId) {
    return xApiRequest('DELETE', `/tweets/${tweetId}`);
}

async function getCurrentUser() {
    return xApiRequest('GET', '/users/me');
}

module.exports = {
    saveTokens,
    isTokenExpired,
    ensureValidToken,
    postTweet,
    deleteTweet,
    getCurrentUser,
    tokenStore,
};
```

---

## FASE 3 — Implementare le Route OAuth

### 3.1 Creare `routes/auth.js` (Node.js)

```javascript
// routes/auth.js
const express = require('express');
const router = express.Router();
const { generatePKCE, generateState, buildAuthorizationUrl, exchangeCodeForTokens } = require('../services/xOAuth');
const { saveTokens } = require('../services/xApi');

/**
 * GET /api/auth/login
 * Avvia il flusso OAuth: genera PKCE + state, salva in sessione, redirect a X.
 */
router.get('/login', (req, res) => {
    // 1. Genera PKCE
    const { codeVerifier, codeChallenge } = generatePKCE();

    // 2. Genera state (CSRF protection)
    const state = generateState();

    // 3. Salva in sessione
    req.session.codeVerifier = codeVerifier;
    req.session.oauthState = state;

    // 4. Costruisci URL e redirect
    const authUrl = buildAuthorizationUrl(codeChallenge, state);
    console.log('Redirecting to:', authUrl);
    res.redirect(authUrl);
});

/**
 * GET /api/auth/callback
 * X reindirizza qui dopo l'autorizzazione dell'utente.
 * Query params: ?code=xxx&state=xxx  (oppure ?error=xxx)
 */
router.get('/callback', async (req, res) => {
    const { code, state, error, error_description } = req.query;

    // 1. Gestione errore (utente ha negato)
    if (error) {
        return res.redirect(`/?error=${encodeURIComponent(error_description || error)}`);
    }

    // 2. Verifica state (CSRF protection)
    if (!state || state !== req.session.oauthState) {
        return res.status(403).send('Errore: state parameter non valido (possibile CSRF attack)');
    }

    // 3. Recupera code_verifier dalla sessione
    const codeVerifier = req.session.codeVerifier;
    if (!codeVerifier) {
        return res.status(400).send('Sessione scaduta. Ripeti il login.');
    }

    // 4. Scambia il codice per i token
    try {
        const tokens = await exchangeCodeForTokens(code, codeVerifier);
        console.log('Tokens ottenuti con successo!');
        console.log('  access_token:', tokens.accessToken.substring(0, 20) + '...');
        console.log('  refresh_token:', tokens.refreshToken ? 'presente' : 'ASSENTE');
        console.log('  expires_in:', tokens.expiresIn, 'secondi');

        // 5. Salva i token
        saveTokens(tokens.accessToken, tokens.refreshToken, tokens.expiresIn);

        // 6. Pulisci sessione
        delete req.session.codeVerifier;
        delete req.session.oauthState;

        // 7. Redirect alla dashboard
        res.redirect('/?success=connected');
    } catch (error) {
        console.error('Errore scambio token:', error.response?.data || error.message);
        res.redirect(`/?error=${encodeURIComponent('Errore durante il login: ' + (error.response?.data?.error_description || error.message))}`);
    }
});

/**
 * GET /api/auth/status
 * Verifica lo stato dell'autenticazione.
 */
router.get('/status', (req, res) => {
    const { tokenStore, isTokenExpired } = require('../services/xApi');
    res.json({
        connected: !!tokenStore.accessToken,
        tokenExpired: isTokenExpired(),
        expiresAt: tokenStore.expiresAt,
    });
});

/**
 * GET /api/auth/logout
 * Rimuove i token (logout).
 */
router.get('/logout', (req, res) => {
    saveTokens(null, null, 0);
    res.redirect('/?success=logout');
});

module.exports = router;
```

---

## FASE 4 — Creare il Frontend

### 4.1 Creare `public/index.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X API OAuth Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #15202b;
            color: #e7e9ea;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: #192734;
            border-radius: 12px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        h1 { margin-bottom: 8px; font-size: 24px; }
        .subtitle { color: #71767b; margin-bottom: 32px; font-size: 15px; }
        .btn-x-login {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #1d9bf0;
            color: white;
            border: none;
            border-radius: 9999px;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
            text-decoration: none;
        }
        .btn-x-login:hover { background: #1a8cd8; }
        .btn-x-login svg { width: 18px; height: 18px; fill: white; }
        .btn-secondary {
            display: inline-block;
            margin-top: 12px;
            padding: 8px 16px;
            background: transparent;
            color: #71767b;
            border: 1px solid #38444d;
            border-radius: 9999px;
            text-decoration: none;
            font-size: 14px;
        }
        .btn-secondary:hover { background: #192734; }
        .status {
            margin-top: 24px;
            padding: 16px;
            background: #1e2732;
            border-radius: 8px;
            font-size: 14px;
            text-align: left;
        }
        .status.connected { border-left: 4px solid #00ba7c; }
        .status.disconnected { border-left: 4px solid #f4212e; }
        .status.error { border-left: 4px solid #f4212e; }
        .tweet-box {
            margin-top: 24px;
            display: none;
        }
        .tweet-box.visible { display: block; }
        textarea {
            width: 100%;
            background: #15202b;
            color: #e7e9ea;
            border: 1px solid #38444d;
            border-radius: 8px;
            padding: 12px;
            font-size: 15px;
            resize: vertical;
            min-height: 80px;
            font-family: inherit;
        }
        .btn-tweet {
            margin-top: 12px;
            background: #1d9bf0;
            color: white;
            border: none;
            border-radius: 9999px;
            padding: 10px 20px;
            font-weight: 700;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-tweet:hover { background: #1a8cd8; }
        .btn-tweet:disabled { background: #38444d; cursor: not-allowed; }
        .alert {
            margin-top: 16px;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
        }
        .alert-success { background: rgba(0, 186, 124, 0.1); color: #00ba7c; }
        .alert-error { background: rgba(244, 33, 46, 0.1); color: #f4212e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>X API OAuth 2.0 Demo</h1>
        <p class="subtitle">Connetti il tuo account X per usare le API</p>

        <!-- Pulsante Login -->
        <a href="/api/auth/login" class="btn-x-login">
            <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            Accedi con X
        </a>

        <!-- Pulsante Logout (nascosto finché non connesso) -->
        <br>
        <a href="/api/auth/logout" class="btn-secondary" id="logout-btn" style="display:none;">
            Disconnetti
        </a>

        <!-- Alert messaggi -->
        <div id="alert-container"></div>

        <!-- Status -->
        <div id="status" class="status disconnected">
            <strong>Stato:</strong> <span id="status-text">Non connesso</span>
        </div>

        <!-- Tweet Box (visibile solo se connesso) -->
        <div id="tweet-box" class="tweet-box">
            <h3 style="margin-bottom: 8px; font-size: 18px;">Pubblica un Tweet</h3>
            <textarea id="tweet-text" placeholder="Cosa stai pensando?" maxlength="280"></textarea>
            <button class="btn-tweet" id="btn-tweet" onclick="publishTweet()">Tweet</button>
        </div>
    </div>

    <script>
        // === Gestione messaggi URL ===
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('success') === 'connected') {
            showAlert('Connesso con successo a X!', 'success');
        } else if (urlParams.get('success') === 'logout') {
            showAlert('Disconnesso.', 'success');
        } else if (urlParams.get('error')) {
            showAlert(urlParams.get('error'), 'error');
        }

        // === Verifica stato connessione ===
        async function checkStatus() {
            try {
                const res = await fetch('/api/auth/status');
                const data = await res.json();

                const statusEl = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                const tweetBox = document.getElementById('tweet-box');
                const logoutBtn = document.getElementById('logout-btn');

                if (data.connected) {
                    statusEl.className = 'status connected';
                    statusText.textContent = 'Connesso a X';
                    tweetBox.classList.add('visible');
                    logoutBtn.style.display = 'inline-block';
                } else {
                    statusEl.className = 'status disconnected';
                    statusText.textContent = 'Non connesso';
                    tweetBox.classList.remove('visible');
                    logoutBtn.style.display = 'none';
                }
            } catch (err) {
                console.error('Errore verifica stato:', err);
            }
        }

        // === Pubblica Tweet ===
        async function publishTweet() {
            const text = document.getElementById('tweet-text').value.trim();
            if (!text) return;

            const btn = document.getElementById('btn-tweet');
            btn.disabled = true;
            btn.textContent = 'Pubblicazione...';

            try {
                const res = await fetch('/api/tweet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text }),
                });

                const data = await res.json();

                if (res.ok) {
                    showAlert('Tweet pubblicato! ID: ' + (data.id || 'sconosciuto'), 'success');
                    document.getElementById('tweet-text').value = '';
                } else {
                    showAlert('Errore: ' + (data.error || 'pubblicazione fallita'), 'error');
                }
            } catch (err) {
                showAlert('Errore di rete: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Tweet';
            }
        }

        // === Helper Alert ===
        function showAlert(message, type) {
            const container = document.getElementById('alert-container');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            container.appendChild(alert);
            setTimeout(() => alert.remove(), 5000);
        }

        // === Init ===
        checkStatus();
    </script>
</body>
</html>
```

---

## FASE 5 — Aggiungere le Route API per i Tweet

### 5.1 Aggiungere route tweet a `server.js`

```javascript
// Aggiungi in server.js, prima di app.listen()

const { postTweet, getCurrentUser } = require('./services/xApi');

// POST /api/tweet — Pubblica un tweet
app.post('/api/tweet', async (req, res) => {
    try {
        const { text } = req.body;
        if (!text) return res.status(400).json({ error: 'Testo mancante' });

        const result = await postTweet(text);
        res.json(result);
    } catch (error) {
        if (error.message === 'REAUTH_REQUIRED') {
            res.status(401).json({
                error: 'Token scaduto o non valido. Riautenticazione necessaria.',
                reauthUrl: '/api/auth/login'
            });
        } else {
            console.error('Errore pubblicazione tweet:', error.response?.data || error.message);
            res.status(500).json({
                error: error.response?.data?.detail || error.message
            });
        }
    }
});

// GET /api/me — Info utente corrente
app.get('/api/me', async (req, res) => {
    try {
        const user = await getCurrentUser();
        res.json(user);
    } catch (error) {
        if (error.message === 'REAUTH_REQUIRED') {
            res.status(401).json({
                error: 'Riautenticazione necessaria',
                reauthUrl: '/api/auth/login'
            });
        } else {
            res.status(500).json({ error: error.message });
        }
    }
});
```

---

## FASE 6 — Testare il Flusso Completo

### 6.1 Avviare il Server

```bash
# Node.js
node server.js

# oppure con nodemon (auto-reload)
npx nodemon server.js
```

### 6.2 Procedura di Test

```
1. Apri il browser su http://localhost:3000
2. Clicca "Accedi con X"
3. Vieni reindirizzato a x.com → autorizza l'app
4. Vieni reindirizzato a http://localhost:3000/api/auth/callback
5. Il backend scambia il codice per i token
6. Vieni reindirizzato alla dashboard con ?success=connected
7. Prova a pubblicare un tweet dal form
```

### 6.3 Verificare i Log

Output atteso nel terminale:

```
Server running on http://localhost:3000
Redirecting to: https://x.com/i/oauth2/authorize?response_type=code&client_id=...
Tokens ottenuti con successo!
  access_token: ZGFzZGhqc2FkamhzYWRq...
  refresh_token: presente
  expires_in: 7200 secondi
```

### 6.4 Testare il Rinnovo Automatico

Per simulare un token scaduto:

```javascript
// In services/xApi.js, modifica temporaneamente:
function isTokenExpired() {
    return true;  // Forza sempre scaduto per testare il refresh
}
```

Pubblica un tweet → il sistema dovrebbe:
1. Rilevare il token scaduto
2. Chiamare `refreshAccessToken()`
3. Ottenere un nuovo access_token
4. Eseguire la chiamata API con il nuovo token
5. Restituire il risultato

---

## FASE 7 — Gestione del Caso "Must Reauthorize"

### Quando il Refresh Token Fallisce

Se il refresh token è scaduto, revocato o non valido, il sistema deve:

1. **Rilevare il fallimento** del refresh
2. **Lanciare l'errore `REAUTH_REQUIRED`**
3. **Reindirizzare l'utente a `/api/auth/login`** per ripetere il flusso OAuth

### Implementazione nel Frontend

Aggiungi questo gestore globale nel frontend:

```javascript
// Intercetta tutte le risposte 401
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason?.reauthUrl) {
        showAlert('Sessione scaduta. Reindirizzamento al login...', 'error');
        setTimeout(() => window.location.href = event.reason.reauthUrl, 2000);
    }
});

// Per ogni fetch API, gestisci il 401
async function apiCall(url, options) {
    const res = await fetch(url, options);
    if (res.status === 401) {
        const data = await res.json();
        if (data.reauthUrl) {
            showAlert('Sessione scaduta. Reindirizzamento al login...', 'error');
            setTimeout(() => window.location.href = data.reauthUrl, 2000);
        }
        throw new Error(data.error || 'Non autorizzato');
    }
    return res;
}
```

---

## FASE 8 — Checklist Finale

### Prima di andare in produzione

```
✅ .env creato con credenziali reali
✅ .env aggiunto al .gitignore
✅ HTTPS abilitato (redirect_uri DEVE essere https)
✅ Session secret lungo e casuale
✅ cookie.secure = true in produzione
✅ Token salvati in database (non in memoria)
✅ Gestione errori 401 implementata
✅ Gestione errori 429 (rate limit) implementata
✅ Exponential backoff per retry
✅ Logging degli errori attivo
✅ Redirect URI su console.x.com corrisponde esattamente
✅ Scope offline.access richiesto (per refresh token)
✅ State parameter verificato in callback (CSRF)
✅ PKCE generato per ogni login
✅ Frontend gestisce redirect a /api/auth/login su REAUTH_REQUIRED
```

### Problemi Comuni e Soluzioni

| Problema | Causa | Soluzione |
|---|---|---|
| `redirect_uri mismatch` | URI nel codice ≠ URI nel Developer Portal | Copia esattamente l'URI dal Developer Portal |
| `invalid_client` | Client Secret errato o non inviato come Basic Auth | Verifica Basic Auth header: `Basic base64(id:secret)` |
| `Missing code_verifier` | Sessione scaduta tra redirect e callback | Aumenta `maxAge` della sessione a 10+ minuti |
| `invalid_grant` | Codice già usato o scaduto | Il codice è monouso; l'utente deve ripetere il login |
| `unauthorized_client` | Client non abilitato per OAuth 2.0 | Verifica "Type of App" = "Web App" nel Developer Portal |
| `No refresh_token` | Scope `offline.access` non richiesto | Aggiungi `offline.access` agli scope |
| `401 su chiamata API` | Token scaduto | Verifica che il refresh automatico funzioni |
| `429 Too Many Requests` | Rate limit superato | Implementa exponential backoff, usa header `Retry-After` |
| `Session scaduta` | Cookie di sessione scaduto | Aumenta `maxAge` o usa sessioni persistenti |