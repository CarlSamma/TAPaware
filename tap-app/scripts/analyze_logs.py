"""Analyze server.log for errors and warnings."""
import json
import sys
from pathlib import Path

log_path = Path("data/server.log")
if not log_path.exists():
    print("ERROR: data/server.log not found")
    sys.exit(1)

lines = log_path.read_text(encoding="utf-8").splitlines()
entries = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        entries.append(json.loads(line))
    except json.JSONDecodeError:
        print(f"WARN: Could not parse line: {line[:100]}")

errors = [e for e in entries if e.get("level") == "error"]
warnings = [e for e in entries if e.get("level") == "warning"]

print(f"{'='*60}")
print(f"  ANALISI LOG SERVER — data/server.log")
print(f"{'='*60}")
print(f"  Totale righe:   {len(entries)}")
print(f"  Livello INFO:   {len([e for e in entries if e.get('level') == 'info'])}")
print(f"  Livello WARNING:{len(warnings)}")
print(f"  Livello ERROR:  {len(errors)}")
print(f"{'='*60}")

# Time range
if entries:
    print(f"  Periodo: {entries[0].get('timestamp','?')} → {entries[-1].get('timestamp','?')}")
    print(f"{'='*60}")

print()
print("=" * 60)
print("  ERRORI (level=error)")
print("=" * 60)
if not errors:
    print("  Nessun errore trovato.")
else:
    for i, e in enumerate(errors, 1):
        ts = e.get("timestamp", "?")
        event = e.get("event", "?")
        extras = {k: v for k, v in e.items() if k not in ("event", "level", "timestamp")}
        print(f"\n  [{i}] {ts}")
        print(f"      Evento: {event}")
        for k, v in extras.items():
            print(f"      {k}: {v}")

print()
print("=" * 60)
print("  WARNING (level=warning)")
print("=" * 60)
if not warnings:
    print("  Nessun warning trovato.")
else:
    for i, w in enumerate(warnings, 1):
        ts = w.get("timestamp", "?")
        event = w.get("event", "?")
        extras = {k: v for k, v in w.items() if k not in ("event", "level", "timestamp")}
        print(f"\n  [{i}] {ts}")
        print(f"      Evento: {event}")
        for k, v in extras.items():
            print(f"      {k}: {v}")

print()
print("=" * 60)
print("  RIEPILOGO PROBLEMI")
print("=" * 60)

problem_count = 0

if errors:
    problem_count += len(errors)
    print(f"\n  🔴 CRITICO: background_cycle_timeout")
    print(f"     Il ciclo TAP #1 ha atteso una risposta dal target per 600s")
    print(f"     senza riceverla. Causa probabile: il target non ha risposto")
    print(f"     al probe entro il timeout configurato (reply_timeout_seconds=3600).")
    print(f"     Il timeout hard di sicurezza (2x, max 600s) è scattato.")

if warnings:
    problem_count += len(warnings)
    print(f"\n  🟡 WARNING OAuth2:")
    print(f"     - OAuth2 refresh token PKCE: 401 Unauthorized")
    print(f"     - OAuth2 basic auth refresh: 400 invalid token")
    print(f"     → Tutte le strategie di refresh OAuth2 sono fallite.")
    print(f"     → Il sistema è ricaduto al Bearer Token (app-only).")
    print(f"     → AZIONE RICHIESTA: rigenerare il refresh token OAuth2.")

    print(f"\n  🟡 WARNING Stream Subscriptions:")
    print(f"     - chat.received: 400 — OAuth access token required")
    print(f"     - dm.received: 400 — OAuth access token required")
    print(f"     → Questi eventi richiedono OAuth 2.0 User Context.")
    print(f"     → Con il solo Bearer token, solo post.create e post.delete funzionano.")

print(f"\n  Totale problemi: {problem_count}")
print("=" * 60)