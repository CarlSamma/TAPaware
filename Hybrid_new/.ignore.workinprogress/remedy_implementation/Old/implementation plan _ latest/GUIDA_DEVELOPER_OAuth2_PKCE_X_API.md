# GUIDA DEVELOPER: X (Twitter) API v2 — OAuth 2.0 con PKCE

## Da Token Manuali a Flusso OAuth 2.0 via Callback URL

> **Starting Point:** I token di accesso in uso sono scaduti o non più validi e il sistema non riesce a rinnovarli automaticamente, richiedendo un nuovo intervento manuale dell'utente tramite il flusso di login.
>
> **Obiettivo:** Implementare un pulsante "Accedi con X" nel frontend che avvii il flusso OAuth 2.0 con PKCE, gestisca il callback, scambi l'authorization code per token, e implementi il rinnovo automatico — eliminando la necessità di intervento manuale.

---

## Indice

1. [Panoramica del Flusso](#1-panoramica-del-flusso)
2. [Prerequisiti e Configurazione su console.x.com](#2-prerequisiti-e-configurazione-su-consolexcom)
3. [Step 1 — Generazione PKCE (code_verifier + code_challenge)](#3-step-1--generazione-pkce)
4. [Step 2 — Pulsante Login e Redirect a X](#4-step-2--pulsante-login-e-redirect-a-x)
5. [Step 3 — Gestione del Callback URL](#5-step-3--gestione-del-callback-url)
6. [Step 4 — Scambio Authorization Code → Token](#6-step-4--scambio-authorization-code--token)
7. [Step 5 — Utilizzo del Token per le API](#7-step-5--utilizzo-del-token-per-le-api)
8. [Step 6 — Rinnovo Automatico del Token (Refresh Flow)](#8-step-6--rinnovo-automatico-del-token)
9. [Step 7 — Gestione Errori e Recovery](#9-step-7--gestione-errori-e-recovery)
10. [Sicurezza e Best Practices](#10-sicurezza-e-best-practices)
11. [Riferimenti Endpoint](#11-riferimenti-endpoint)

---

## 1. Panoramica del Flusso

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   FRONTEND  │────▶│  X AUTH PAGE │────▶│  CALLBACK URL   │────▶│  TOKEN EXCHANGE  │
│  (Pulsante) │     │  (Browser)   │     │  (Backend)      │     │  (Backend)       │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────────┘
                                                                            │
                                                                            ▼
                                                                     ┌──────────────┐
                                                                     │ ACCESS TOKEN │
                                                                     │ REFRESH TOKEN│
                                                                     └──────────────┘
                                                                            │
                                                                            ▼
                                                                     ┌──────────────┐
                                                                     │  X API v2    │
                                                                     │  (Chiamate)  │
                                                                     └──────────────┘
```

**Passaggi principali:**

1. L'utente clicca "Accedi con X" → viene reindirizzato a `https://x.com/i/oauth2/authorize`
2. L'utente autorizza l'app su X
3. X reindirizza alla tua `redirect_uri` con un **authorization code**
4. Il backend scambia il code per **Access Token** + **Refresh Token** via `POST`
5. Il backend usa il token per le chiamate API, rinnovandolo automaticamente quando scade

---

## 2. Prerequisiti e Configurazione su console.x.com

### 2.1 Creare l'App su X Developer Portal

1. Vai su `https://developer.x.com` → "Go to Console"
2. Crea un nuovo progetto e una nuova app
3. Nella sezione **"Keys and tokens"** della tua app, annota:
   - **Client ID** (OAuth 2.0)
   - **Client Secret** (OAuth 2.0)

### 2.2 Configurare le Impostazioni di Autenticazione

Nella pagina dell'app, sezione **"User authentication settings"** → clicca **"Set up"**:

| Impostazione | Valore |
|---|---|
| **App Permissions** | Read and Write |
| **Type of App** | Web App, Automated App or Bot (Confidential Client) |
| **Callback URI / Redirect URL** | `https://tuodominio.com/api/auth/callback` |
| **Website URL** | `https://tuodominio.com` |

> ⚠️ **CRITICO:** La `redirect_uri` nel codice DEVE corrispondere ESATTAMENTE a quella configurata nel Developer Portal. Anche una differenza di `/` finale causa errore `redirect_uri mismatch`.

### 2.3 Scope Necessari

```
tweet.read tweet.write users.read offline.access
```

| Scope | Perché |
|---|---|
| `tweet.read` | Leggere tweet |
| `tweet.write` | Pubblicare tweet |
| `users.read` | Leggere profilo utente |
| `offline.access` | **FONDAMENTALE** — Ottenere il Refresh Token per il rinnovo automatico |

### 2.4 Variabili d'Ambiente

Crea un file `.env` (mai committare in git):

```env
X_CLIENT_ID=il_tuo_client_id
X_CLIENT_SECRET=il_tuo_client_secret
X_REDIRECT_URI=https://tuodominio.com/api/auth/callback
```

---

## 3. Step 1 — Generazione PKCE

Il protocollo PKCE (Proof Key for Code Exchange) protegge lo scambio del codice di autorizzazione.

- **code_verifier**: stringa casuale crittografica (43-128 caratteri)
- **code_challenge**: SHA-256 del verifier, codificato in Base64URL (senza padding `=`)

### Python

```python
import hashlib
import base64
import secrets

def generate_pkce():
    """Genera code_verifier e code_challenge per PKCE."""
    # code_verifier: stringa casuale URL-safe (43-128 caratteri)
    code_verifier = secrets.token_urlsafe(64)

    # code_challenge: SHA-256 del verifier, codificato Base64URL (no padding)
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').replace('=', '')

    return code_verifier, code_challenge

# Utilizzo:
verifier, challenge = generate_pkce()
# Salva 'verifier' nella sessione dell'utente — servirà allo Step 4
```

### JavaScript (Node.js)

```javascript
const crypto = require('crypto');

function generatePKCE() {
    // code_verifier: 32 bytes casuali → stringa base64url
    const codeVerifier = crypto.randomBytes(32).toString('base64url');

    // code_challenge: SHA-256 del verifier, codificato base64url
    const codeChallenge = crypto
        .createHash('sha256')
        .update(codeVerifier)
        .digest('base64url');

    return { codeVerifier, codeChallenge };
}

// Utilizzo:
const { codeVerifier, codeChallenge } = generatePKCE();
// Salva codeVerifier in session/DB — servirà allo Step 4
```

> **IMPORTANTE:** Il `code_verifier` deve essere salvato nella sessione utente o in un database temporaneo. Servirà obbligatoriamente nello Step 4 per lo scambio del token.

---

## 4. Step 2 — Pulsante Login e Redirect a X

### Costruzione dell'URL di Autorizzazione

```
https://x.com/i/oauth2/authorize
    ?response_type=code
    &client_id={CLIENT_ID}
    &redirect_uri={REDIRECT_URI}
    &scope=tweet.read%20tweet.write%20users.read%20offline.access
    &state={STATE}
    &code_challenge={CODE_CHALLENGE}
    &code_challenge_method=S256
```

### Implementazione Backend (Generazione URL + Redirect)

**Python (Flask):**

```python
import os
import secrets
from urllib.parse import urlencode

@app.route('/api/auth/login')
def x_login():
    """Reindirizza l'utente alla pagina di autorizzazione di X."""

    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)

    # Salva nella sessione
    session['x_code_verifier'] = code_verifier
    session['x_oauth_state'] = state

    params = urlencode({
        'response_type': 'code',
        'client_id': os.environ['X_CLIENT_ID'],
        'redirect_uri': os.environ['X_REDIRECT_URI'],
        'scope': 'tweet.read tweet.write users.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    })

    auth_url = f'https://x.com/i/oauth2/authorize?{params}'
    return redirect(auth_url)
```

**Node.js (Express):**

```javascript
const crypto = require('crypto');

app.get('/api/auth/login', (req, res) => {
    const { codeVerifier, codeChallenge } = generatePKCE();
    const state = crypto.randomBytes(16).toString('hex');

    // Salva nella sessione
    req.session.xCodeVerifier = codeVerifier;
    req.session.xOAuthState = state;

    const params = new URLSearchParams({
        response_type: 'code',
        client_id: process.env.X_CLIENT_ID,
        redirect_uri: process.env.X_REDIRECT_URI,
        scope: 'tweet.read tweet.write users.read offline.access',
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
    });

    res.redirect(`https://x.com/i/oauth2/authorize?${params}`);
});
```

### Frontend (Pulsante HTML)

```html
<button onclick="window.location.href='/api/auth/login'" class="btn-x-login">
    <svg><!-- Logo X --></svg>
    Accedi con X
</button>
```

---

## 5. Step 3 — Gestione del Callback URL

Dopo l'autorizzazione, X reindirizza l'utente alla tua `redirect_uri` con parametri query:

```
https://tuodominio.com/api/auth/callback?code={AUTHORIZATION_CODE}&state={STATE}
```

### Implementazione del Callback Handler

**Python (Flask):**

```python
@app.route('/api/auth/callback')
def x_callback():
    """Gestisce il callback dopo l'autorizzazione dell'utente su X."""

    # 1. Estrai parametri dalla query string
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    # 2. Gestione errore (utente ha negato l'autorizzazione)
    if error:
        error_description = request.args.get('error_description', 'Autorizzazione negata')
        return redirect(f'/dashboard?error={error_description}')

    # 3. Verifica state per prevenire CSRF
    expected_state = session.get('x_oauth_state')
    if not state or state != expected_state:
        return jsonify({'error': 'Invalid state parameter'}), 403

    # 4. Recupera il code_verifier dalla sessione
    code_verifier = session.get('x_code_verifier')
    if not code_verifier:
        return jsonify({'error': 'Session expired, please login again'}), 400

    # 5. Scambia il codice per i token (→ Step 4)
    tokens = exchange_code_for_tokens(code, code_verifier)

    if 'error' in tokens:
        return redirect(f'/dashboard?error={tokens["error"]}')

    # 6. Salva i token in modo sicuro
    save_tokens_to_db(
        access_token=tokens['access_token'],
        refresh_token=tokens.get('refresh_token'),
        expires_in=tokens['expires_in'],
    )

    # 7. Pulisci la sessione
    session.pop('x_code_verifier', None)
    session.pop('x_oauth_state', None)

    return redirect('/dashboard?success=connected')
```

**Node.js (Express):**

```javascript
app.get('/api/auth/callback', async (req, res) => {
    const { code, state, error, error_description } = req.query;

    // 1. Errore dall'utente
    if (error) {
        return res.redirect(`/dashboard?error=${error_description || 'denied'}`);
    }

    // 2. Verifica state (CSRF protection)
    if (!state || state !== req.session.xOAuthState) {
        return res.status(403).json({ error: 'Invalid state parameter' });
    }

    // 3. Recupera code_verifier
    const codeVerifier = req.session.xCodeVerifier;
    if (!codeVerifier) {
        return res.status(400).json({ error: 'Session expired' });
    }

    try {
        // 4. Scambia codice per token
        const tokens = await exchangeCodeForTokens(code, codeVerifier);

        // 5. Salva i token
        await saveTokensToDB(tokens.access_token, tokens.refresh_token, tokens.expires_in);

        // 6. Pulisci sessione
        delete req.session.xCodeVerifier;
        delete req.session.xOAuthState;

        res.redirect('/dashboard?success=connected');
    } catch (err) {
        res.redirect(`/dashboard?error=${err.message}`);
    }
});
```

---

## 6. Step 4 — Scambio Authorization Code → Token

### Specifiche della Richiesta

| Campo | Valore |
|---|---|
| **URL** | `POST https://api.x.com/2/oauth2/token` |
| **Content-Type** | `application/x-www-form-urlencoded` |
| **Authorization** | `Basic base64(client_id:client_secret)` |
| **Body params** | `code`, `grant_type=authorization_code`, `redirect_uri`, `code_verifier`, `client_id` |

### Python

```python
import base64
import os
import requests
from datetime import datetime, timedelta

def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    """Scambia l'authorization code per access_token e refresh_token."""

    client_id = os.environ['X_CLIENT_ID']
    client_secret = os.environ['X_CLIENT_SECRET']
    redirect_uri = os.environ['X_REDIRECT_URI']

    # Basic Auth: base64(client_id:client_secret)
    auth_string = f'{client_id}:{client_secret}'
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_bytes}',
    }

    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
        'client_id': client_id,
    }

    response = requests.post(
        'https://api.x.com/2/oauth2/token',
        headers=headers,
        data=data,  # requests codifica automaticamente come form-urlencoded
    )

    if response.status_code != 200:
        return {'error': f'Token exchange failed: {response.status_code} - {response.text}'}

    token_data = response.json()

    return {
        'access_token': token_data['access_token'],
        'refresh_token': token_data.get('refresh_token'),
        'expires_in': token_data.get('expires_in', 7200),  # Default 2 ore
        'scope': token_data.get('scope'),
        'token_type': token_data.get('token_type'),
    }
```

### Node.js

```javascript
async function exchangeCodeForTokens(code, codeVerifier) {
    const clientId = process.env.X_CLIENT_ID;
    const clientSecret = process.env.X_CLIENT_SECRET;
    const redirectUri = process.env.X_REDIRECT_URI;

    // Basic Auth
    const authString = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

    const params = new URLSearchParams({
        code: code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
        code_verifier: codeVerifier,
        client_id: clientId,
    });

    const response = await fetch('https://api.x.com/2/oauth2/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Basic ${authString}`,
        },
        body: params.toString(),
    });

    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Token exchange failed: ${response.status} - ${errText}`);
    }

    const data = await response.json();

    return {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        expiresIn: data.expires_in || 7200,
        scope: data.scope,
        tokenType: data.token_type,
    };
}
```

### Risposta Attesa da X

```json
{
    "token_type": "bearer",
    "expires_in": 7200,
    "access_token": "ZGFzZGhqc2FkamhzYWRqaGRzY...",
    "scope": "tweet.read tweet.write users.read offline.access",
    "refresh_token": "ZHNha2Roc2FkaGpza2FkaGpza..."
}
```

> **Nota:** Il `refresh_token` viene restituito SOLO se hai richiesto lo scope `offline.access`.

---

## 7. Step 5 — Utilizzo del Token per le API

Una volta ottenuto l'access token, usalo nell'header `Authorization: Bearer` per tutte le chiamate API.

### Esempio: Pubblicare un Tweet

**Python:**

```python
def post_tweet(access_token: str, text: str) -> dict:
    """Pubblica un tweet usando l'access token."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        'https://api.x.com/2/tweets',
        headers=headers,
        json={'text': text},
    )

    if response.status_code == 401:
        # Token scaduto → tenta refresh (Step 6)
        raise TokenExpiredError("Access token scaduto, necessario refresh")

    return response.json()
```

**Node.js:**

```javascript
async function postTweet(accessToken, text) {
    const response = await fetch('https://api.x.com/2/tweets', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
    });

    if (response.status === 401) {
        throw new TokenExpiredError('Access token scaduto');
    }

    return response.json();
}
```

---

## 8. Step 6 — Rinnovo Automatico del Token

### Quando Rinnovare

- Gli **Access Token scadono ogni 2 ore** (7200 secondi)
- Monitora il campo `expires_in` e rinnova PRIMA della scadenza (es. 5 minuti prima)
- Se ricevi un errore **401 Unauthorized**, tenta il refresh come recovery

### Specifiche della Richiesta di Refresh

| Campo | Valore |
|---|---|
| **URL** | `POST https://api.x.com/2/oauth2/token` |
| **Content-Type** | `application/x-www-form-urlencoded` |
| **Authorization** | `Basic base64(client_id:client_secret)` |
| **Body params** | `grant_type=refresh_token`, `refresh_token`, `client_id` |

### Python

```python
def refresh_access_token(refresh_token: str) -> dict:
    """Rinnova l'access token usando il refresh token."""

    client_id = os.environ['X_CLIENT_ID']
    client_secret = os.environ['X_CLIENT_SECRET']

    auth_string = f'{client_id}:{client_secret}'
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_bytes}',
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
    }

    response = requests.post(
        'https://api.x.com/2/oauth2/token',
        headers=headers,
        data=data,
    )

    if response.status_code != 200:
        # Refresh fallito → serve riautenticazione manuale
        return {'error': 'must reauthorize via /api/auth/login'}

    token_data = response.json()

    return {
        'access_token': token_data['access_token'],
        'refresh_token': token_data.get('refresh_token', refresh_token),  # A volte X restituisce un nuovo refresh token
        'expires_in': token_data.get('expires_in', 7200),
    }
```

### Node.js

```javascript
async function refreshAccessToken(refreshToken) {
    const clientId = process.env.X_CLIENT_ID;
    const clientSecret = process.env.X_CLIENT_SECRET;
    const authString = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

    const params = new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        client_id: clientId,
    });

    const response = await fetch('https://api.x.com/2/oauth2/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Basic ${authString}`,
        },
        body: params.toString(),
    });

    if (!response.ok) {
        throw new ReauthorizationRequired('must reauthorize via /api/auth/login');
    }

    const data = await response.json();

    return {
        accessToken: data.access_token,
        refreshToken: data.refresh_token || refreshToken,
        expiresIn: data.expires_in || 7200,
    };
}
```

### Wrapper con Auto-Refresh Integrato

**Python:**

```python
class XApiClient:
    """Client API con refresh automatico del token."""

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def load_tokens_from_db(self):
        """Carica i token dal database."""
        token_data = get_tokens_from_db()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.token_expires_at = token_data['expires_at']

    def is_token_expired(self) -> bool:
        """Verifica se il token è scaduto o sta per scadere (5 min di margine)."""
        if not self.token_expires_at:
            return True
        from datetime import datetime, timedelta
        return datetime.utcnow() >= (self.token_expires_at - timedelta(minutes=5))

    def ensure_valid_token(self):
        """Assicura che abbiamo un token valido, rinnovando se necessario."""
        if not self.is_token_expired():
            return

        if not self.refresh_token:
            raise ReauthorizationRequired("No refresh token. must reauthorize via /api/auth/login")

        result = refresh_access_token(self.refresh_token)

        if 'error' in result:
            raise ReauthorizationRequired("must reauthorize via /api/auth/login")

        self.access_token = result['access_token']
        self.refresh_token = result['refresh_token']
        self.token_expires_at = datetime.utcnow() + timedelta(seconds=result['expires_in'])

        # Salva nel database
        save_tokens_to_db(self.access_token, self.refresh_token, result['expires_in'])

    def request(self, method: str, url: str, **kwargs):
        """Esegue una richiesta API con gestione automatica 401 + refresh."""
        self.ensure_valid_token()

        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'

        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            # Tenta un refresh forzato
            result = refresh_access_token(self.refresh_token)
            if 'error' in result:
                raise ReauthorizationRequired("must reauthorize via /api/auth/login")

            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
            save_tokens_to_db(self.access_token, self.refresh_token, result['expires_in'])

            # Riprova la richiesta con il nuovo token
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.request(method, url, headers=headers, **kwargs)

        return response


class ReauthorizationRequired(Exception):
    """Eccezione lanciata quando serve la riautenticazione manuale."""
    pass
```

---

## 9. Step 7 — Gestione Errori e Recovery

### Tabella Errori Comuni

| Errore | HTTP Status | Causa | Soluzione |
|---|---|---|---|
| **Unauthorized** | 401 | Token scaduto o non valido | Tenta refresh; se fallisce → reauthorize |
| **Forbidden** | 403 | Scope insufficienti | Ri-autorizzare con scope aggiuntivi |
| **Rate Limited** | 429 | Troppo richieste | Implementare exponential backoff |
| **Quota Exceeded** | 429 | Quota mensile esaurita | Attendere il mese successivo o acquistare crediti |
| **Invalid State** | 403 | Errore CSRF / state non corrisponde | Verificare che state sia salvato correttamente in sessione |
| **redirect_uri mismatch** | 400 | URI non corrisponde al Developer Portal | Verificare che sia identico carattere per carattere |
| **unauthorized_client** | 401 | Client Secret errato o mancante | Verificare il Client Secret e che sia inviato come Basic Auth |
| **Missing code_verifier** | 400 | Sessione scaduta tra redirect e callback | Aumentare TTL della sessione |

### Implementazione Exponential Backoff (per errori 429)

```python
import time

def api_request_with_backoff(func, max_retries=5):
    """Esegue una richiesta API con exponential backoff per errori 429."""
    for attempt in range(max_retries):
        response = func()

        if response.status_code == 429:
            # Usa l'header Retry-After se presente
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_seconds = int(retry_after)
            else:
                # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                wait_seconds = 2 ** attempt

            print(f"Rate limited. Waiting {wait_seconds}s before retry...")
            time.sleep(wait_seconds)
            continue

        return response

    raise Exception("Max retries exceeded for rate-limited request")
```

### Flusso di Recovery Completo

```python
def handle_api_call(client: XApiClient, method: str, url: str, **kwargs):
    """
    Flusso completo di gestione chiamate API con recovery automatico.

    1. Token valido? → Esegui chiamata
    2. 401? → Tenta refresh token
    3. Refresh riuscito? → Riprova chiamata
    4. Refresh fallito? → Redirect a /api/auth/login (riautenticazione manuale)
    5. 429? → Exponential backoff e retry
    """
    try:
        response = client.request(method, url, **kwargs)
        return response
    except ReauthorizationRequired:
        # L'utente DEVE riautenticarsi manualmente
        return {'redirect': '/api/auth/login', 'reason': 'Token refresh failed, reauthorization required'}
```

---

## 10. Sicurezza e Best Practices

### DO ✅

| Pratica | Dettaglio |
|---|---|
| **Variabili d'ambiente** | Memorizzare `CLIENT_ID`, `CLIENT_SECRET` in `.env` o secrets manager |
| **State parameter** | Sempre generare e verificare il parametro `state` per prevenire CSRF |
| **PKCE** | Sempre usare `code_challenge_method=S256` |
| **HTTPS** | Tutti gli endpoint (redirect_uri, callback) devono essere HTTPS |
| **Token refresh proattivo** | Rinnovare il token PRIMA della scadenza (5-10 minuti prima) |
| **Basic Auth per Client Secret** | Inviare `client_id:client_secret` come `Authorization: Basic base64(...)` |
| **Scope minimo** | Richiedere solo gli scope necessari |
| **Gestione errori 401** | Implementare logica di retry + refresh su ogni chiamata API |
| **Audit logging** | Loggare tentativi di autenticazione e rinnovi |

### NON FARE ❌

| Anti-pattern | Perché |
|---|---|
| **Hardcoding token nel codice** | Espone le credenziali nel repository |
| **Commit di `.env`** | Aggiungere `.env` al `.gitignore` |
| **Salvare token in localStorage** | Vulnerabile a XSS; usare sessioni server-side o cookie HttpOnly |
| **Ignorare errore 401** | Il sistema deve gestire il rinnovo automaticamente |
| **Riutilizzare state** | Ogni login deve generare un nuovo `state` casuale |
| **URL con HTTP** | OAuth richiede HTTPS per redirect_uri |

---

## 11. Riferimenti Endpoint

### Endpoint X API v2

| Endpoint | Metodo | Descrizione |
|---|---|---|
| `https://x.com/i/oauth2/authorize` | GET | Pagina di autorizzazione dell'utente |
| `https://api.x.com/2/oauth2/token` | POST | Scambio code→token e refresh token |
| `https://api.x.com/2/tweets` | POST | Pubblicare un tweet |
| `https://api.x.com/2/tweets/{id}` | DELETE | Eliminare un tweet |
| `https://api.x.com/2/users/me` | GET | Info sull'utente corrente |

### SDK Ufficiali

| Linguaggio | Pacchetto | Installazione |
|---|---|---|
| Python | `xdk` | `pip install xdk` |
| TypeScript | `@xdevplatform/xdk` | `npm install @xdevplatform/xdk` |
| Python (community) | `tweepy` | `pip install tweepy` |
| Node.js (community) | `node-twitter-api-v2` | `npm install node-twitter-api-v2` |

### Note su Crediti e Costi

- X utilizza un sistema **pay-per-use** con crediti prepagati
- Acquista crediti su `console.x.com` → Billing → Credits
- Endpoint `GET /2/users/me` funziona senza crediti
- La maggior parte delle operazioni (post, lettura tweet) richiede crediti

---

## Schema Riassuntivo del Flusso Completo

```
UTENTE                    FRONTEND               BACKEND                      X API
  │                          │                      │                            │
  │──clicca "Accedi con X"──▶│                      │                            │
  │                          │──GET /api/auth/login─▶│                            │
  │                          │                      │──genera PKCE (verifier+     │
  │                          │                      │  challenge) + state         │
  │                          │                      │──salva in sessione          │
  │                          │◀──302 redirect───────│                            │
  │◀──redirect a X───────────│                      │                            │
  │                          │                      │                            │
  │──autorizza app─────────────────────────────────────────────▶│                │
  │                          │                      │                            │
  │◀──redirect a callback──────────────────────────────────────│                │
  │                          │                      │                            │
  │──GET /api/auth/callback──────────────────────▶│                            │
  │                          │                      │──verifica state (CSRF)      │
  │                          │                      │──recupera code_verifier     │
  │                          │                      │──POST /oauth2/token─────────▶│
  │                          │                      │◀──access_token+refresh_token│
  │                          │                      │──salva token in DB          │
  │◀──redirect a /dashboard──│◀─────────────────────│                            │
  │                          │                      │                            │
  │                          │                      │──(chiamate API con Bearer   │
  │                          │                      │  token, auto-refresh ogni   │
  │                          │                      │  2h, reauthorize se         │
  │                          │                      │  refresh fallisce)          │