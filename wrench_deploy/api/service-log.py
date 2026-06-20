"""
service-log.py — Per-user vehicle service history (V1).

Routes (POST with `action` field in body):
- list   { vehicle_id }                          -> { ok, entries:[...], count, isPro, limit }
- create { vehicle_id, entry:{date, mileage,     -> { ok, entry, count, remaining }
           service_type, cost?, shop_name?,          or { ok:false, limit_reached:true, upgrade:true, message }
           notes? } }
- delete { vehicle_id, id }                      -> { ok, count }

Bearer auth required (Authorization: Bearer <session_token>); email is derived from the
session, never trusted from the body.

Redis schema:
- user_logs:{email}:{vehicle_id}  -> JSON array of entries (already purged by
  auth.py delete-account's `user_logs:{email}:*` sweep, so GDPR erasure is automatic).

Entry shape:
  { id, date, mileage, service_type, cost, shop_name, notes, parts, created_at }

Free tier: 3 entries per vehicle. Pro tier: unlimited. Enforced server-side.
Self-contained on purpose — Vercel's Python builder does not bundle sibling modules.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import time
import secrets

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

FREE_LIMIT = 3
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_MILEAGE = 1_500_000


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


def _whitelist():
    return {e.strip().lower() for e in os.environ.get("PRO_WHITELIST", "").split(",") if e.strip()}


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


def _is_pro(r, email):
    """Same email-based Pro model as the paid-endpoint gate: PRO_WHITELIST, then the
    sub:{email} cache the Stripe webhook / verify-subscription maintain, then the user
    record tier, then a live Stripe check (cached)."""
    if email in _whitelist():
        return True
    try:
        v = r.get("sub:" + email)
        if v == "active":
            return True
        if v == "inactive":
            return False
    except Exception:
        pass
    try:
        raw = r.get("user:" + email)
        if raw and json.loads(raw).get("tier") == "pro":
            return True
    except Exception:
        pass
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if key:
        try:
            import stripe
            stripe.api_key = key
            for c in stripe.Customer.list(email=email, limit=20).data:
                for status in ("active", "trialing"):
                    if stripe.Subscription.list(customer=c.id, status=status, limit=1).data:
                        try:
                            r.set("sub:" + email, "active", ex=60 * 60 * 6)
                        except Exception:
                            pass
                        return True
            try:
                r.set("sub:" + email, "inactive", ex=60 * 30)
            except Exception:
                pass
        except Exception:
            pass
    return False


def _vkey(email, vehicle_id):
    return "user_logs:%s:%s" % (email, vehicle_id)


def _load(r, email, vehicle_id):
    try:
        raw = r.get(_vkey(email, vehicle_id))
        data = json.loads(raw) if raw else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(r, email, vehicle_id, entries):
    r.set(_vkey(email, vehicle_id), json.dumps(entries))


def _sorted(entries):
    # Newest first: by date desc, tie-break created_at desc.
    return sorted(entries, key=lambda e: (str(e.get("date") or ""), int(e.get("created_at") or 0)), reverse=True)


def _opt_num(v):
    try:
        if v in (None, ""):
            return None
        n = float(v)
        return round(n, 2)
    except Exception:
        return None


def _opt_str(v):
    s = str(v or "").strip()
    return s or None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return self._send(400, {"ok": False, "error": "Invalid JSON."})

        r = _redis()
        if r is None:
            return self._send(503, {"ok": False, "error": "Service log backend not configured."})

        token = _bearer(self.headers) or str(body.get("token") or "")
        email = _session_email(r, token)
        if not email:
            return self._send(401, {"ok": False, "error": "Sign in required."})

        vid = body.get("vehicle_id")
        vid = str(vid).strip() if vid not in (None, "") else ""
        if not vid:
            return self._send(400, {"ok": False, "error": "vehicle_id is required."})

        action = str(body.get("action") or "").strip().lower()
        if action == "list":
            return self._list(r, email, vid)
        if action == "create":
            return self._create(r, email, vid, body.get("entry") or {})
        if action == "delete":
            return self._delete(r, email, vid, str(body.get("id") or "").strip())
        return self._send(400, {"ok": False, "error": "Unknown action."})

    def _list(self, r, email, vid):
        entries = _sorted(_load(r, email, vid))
        return self._send(200, {
            "ok": True, "entries": entries, "count": len(entries),
            "isPro": _is_pro(r, email), "limit": FREE_LIMIT})

    def _create(self, r, email, vid, entry):
        date = str(entry.get("date") or "").strip()
        if not DATE_RE.match(date):
            return self._send(400, {"ok": False, "error": "A valid date (YYYY-MM-DD) is required."})
        try:
            mileage = int(entry.get("mileage"))
        except Exception:
            return self._send(400, {"ok": False, "error": "Mileage is required and must be a number."})
        if mileage < 0 or mileage > MAX_MILEAGE:
            return self._send(400, {"ok": False, "error": "Mileage is out of plausible range."})
        service_type = (str(entry.get("service_type") or "").strip()) or "Other"

        entries = _load(r, email, vid)
        pro = _is_pro(r, email)
        if not pro and len(entries) >= FREE_LIMIT:
            return self._send(200, {
                "ok": False, "limit_reached": True, "upgrade": True, "count": len(entries),
                "message": "Upgrade to Pro for unlimited service history — $2.99/month"})

        rec = {
            "id": secrets.token_hex(4),
            "date": date,
            "mileage": mileage,
            "service_type": service_type[:120],
            "cost": _opt_num(entry.get("cost")),
            "shop_name": (_opt_str(entry.get("shop_name")) or None),
            "notes": (str(entry.get("notes") or "").strip()[:2000]),
            "parts": entry.get("parts") if isinstance(entry.get("parts"), list) else [],
            "created_at": int(time.time()),
        }
        if rec["shop_name"]:
            rec["shop_name"] = rec["shop_name"][:120]
        entries.append(rec)
        try:
            _save(r, email, vid, entries)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not save the service entry."})
        remaining = None if pro else max(0, FREE_LIMIT - len(entries))
        return self._send(200, {"ok": True, "entry": rec, "count": len(entries), "remaining": remaining, "isPro": pro})

    def _delete(self, r, email, vid, entry_id):
        if not entry_id:
            return self._send(400, {"ok": False, "error": "Entry id is required."})
        entries = _load(r, email, vid)
        kept = [e for e in entries if str(e.get("id")) != entry_id]
        if len(kept) == len(entries):
            return self._send(404, {"ok": False, "error": "Entry not found."})
        try:
            _save(r, email, vid, kept)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not delete the entry."})
        return self._send(200, {"ok": True, "count": len(kept)})

    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return
