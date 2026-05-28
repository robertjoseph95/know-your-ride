"""
garage-logs.py — Per-vehicle maintenance log entries.

Routes (POST with `action`):
- list   { vehicle_id }                            -> { ok, logs: [...] }
- add    { vehicle_id, entry }                     -> { ok, logs: [...] }
   entry: { date, mileage, service_type, notes?, cost? }
- delete { vehicle_id, entry_id }                  -> { ok, logs: [...] }

Bearer auth (Authorization: Bearer <session_token>).

Redis schema:
- user_logs:{email}:{vehicle_id}                   -> JSON array of entries.
  Each entry: { id, date, mileage, service_type, notes, cost, created_at }
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
import time

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

MAX_LOG_ENTRIES = 500
MAX_NOTES_LEN = 600


def _redis():
    if Redis is None:
        return None
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    if not (url and token):
        return None
    try:
        return Redis(url=url, token=token)
    except Exception:
        return None


def _bearer(headers):
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    return auth[7:].strip() if auth.lower().startswith("bearer ") else ""


def _session_email(r, token):
    if not r or not token:
        return None
    try:
        return r.get("session:" + token) or None
    except Exception:
        return None


def _key(email, vehicle_id):
    return "user_logs:%s:%s" % (email, vehicle_id)


def _load(r, email, vehicle_id):
    try:
        raw = r.get(_key(email, vehicle_id))
        if not raw:
            return []
        return json.loads(raw)
    except Exception:
        return []


def _save(r, email, vehicle_id, logs):
    r.set(_key(email, vehicle_id), json.dumps(logs))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return self._send(400, {"ok": False, "error": "Invalid JSON."})

        r = _redis()
        if r is None:
            return self._send(503, {"ok": False, "error": "Logs backend not configured."})

        email = _session_email(r, _bearer(self.headers) or str(body.get("token") or ""))
        if not email:
            return self._send(401, {"ok": False, "error": "Sign in required."})

        action = str(body.get("action") or "").strip().lower()
        try:
            vid = int(body.get("vehicle_id"))
        except Exception:
            return self._send(400, {"ok": False, "error": "vehicle_id required."})

        if action == "list":
            return self._send(200, {"ok": True, "logs": _load(r, email, vid)})
        if action == "add":
            return self._add(r, email, vid, body.get("entry") or {})
        if action == "delete":
            return self._delete(r, email, vid, body.get("entry_id"))
        return self._send(400, {"ok": False, "error": "Unknown action."})

    def _add(self, r, email, vid, entry):
        date = str(entry.get("date") or "").strip()
        if not date:
            date = time.strftime("%Y-%m-%d")
        try:
            mileage = int(entry.get("mileage"))
        except Exception:
            return self._send(400, {"ok": False, "error": "Mileage must be a number."})
        if mileage < 0 or mileage > 1_500_000:
            return self._send(400, {"ok": False, "error": "Mileage out of plausible range."})
        service = str(entry.get("service_type") or "").strip()
        if not service:
            return self._send(400, {"ok": False, "error": "Service type required."})
        notes = str(entry.get("notes") or "")[:MAX_NOTES_LEN]
        try:
            cost = float(entry.get("cost")) if entry.get("cost") not in (None, "") else None
        except Exception:
            cost = None
        if cost is not None and (cost < 0 or cost > 100000):
            return self._send(400, {"ok": False, "error": "Cost out of plausible range."})

        logs = _load(r, email, vid)
        if len(logs) >= MAX_LOG_ENTRIES:
            return self._send(400, {"ok": False, "error": "Log is full. Delete older entries to add more."})

        rec = {
            "id": secrets.token_hex(8),
            "date": date,
            "mileage": mileage,
            "service_type": service[:80],
            "notes": notes,
            "cost": cost,
            "created_at": int(time.time()),
        }
        logs.append(rec)
        # Newest-first for convenient client rendering.
        logs.sort(key=lambda x: (x.get("date", ""), x.get("created_at", 0)), reverse=True)
        try:
            _save(r, email, vid, logs)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not save the entry."})
        return self._send(200, {"ok": True, "logs": logs})

    def _delete(self, r, email, vid, entry_id):
        if not entry_id:
            return self._send(400, {"ok": False, "error": "entry_id required."})
        logs = _load(r, email, vid)
        before = len(logs)
        logs = [x for x in logs if x.get("id") != entry_id]
        if len(logs) == before:
            return self._send(404, {"ok": False, "error": "Entry not found."})
        try:
            _save(r, email, vid, logs)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not update the log."})
        return self._send(200, {"ok": True, "logs": logs})

    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return
