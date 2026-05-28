"""
auth.py — Email/password auth backed by Upstash Redis.

Routes (all POST, dispatched by `action` field in JSON body):
- signup  { email, password }                 -> { ok, token, email, tier }
- login   { email, password }                 -> { ok, token, email, tier }
- logout  { token }                            -> { ok }
- me      { token }   OR  Authorization: Bearer <token>
                                              -> { ok, email, tier }

Redis schema:
- user:{email}             -> JSON {pw, salt, created_at, tier}
- session:{token}          -> email                  (TTL = SESSION_TTL)

Passwords are hashed with stdlib scrypt (no external crypto deps).
Whitelisted emails (PRO_WHITELIST env var) get Pro tier automatically.
"""

from http.server import BaseHTTPRequestHandler
import hashlib
import hmac
import json
import os
import re
import secrets
import time

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

SESSION_TTL = 60 * 60 * 24 * 30   # 30 days
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# scrypt cost params — n=2**14 is the standard "interactive" target; ~50ms on a serverless cold start.
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32


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


def _hash_pw(password, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_DKLEN)
    return salt.hex(), digest.hex()


def _verify_pw(password, salt_hex, expected_hex):
    _, got = _hash_pw(password, salt_hex)
    # Constant-time compare to defeat timing oracles.
    return hmac.compare_digest(got, expected_hex)


def _norm_email(s):
    return (str(s or "").strip().lower())


def _bearer(headers):
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _tier_for(email):
    return "pro" if email in _whitelist() else "free"


def session_lookup(r, token):
    """Resolve a session token to an email or None. Public so other endpoints can import."""
    if not r or not token:
        return None
    try:
        email = r.get("session:" + token)
        return email if email else None
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return self._send(400, {"ok": False, "error": "Invalid JSON."})

        action = str(body.get("action") or "").strip().lower()
        r = _redis()
        if r is None and action in ("signup", "login", "logout", "me"):
            return self._send(503, {"ok": False, "error": "Auth backend not configured."})

        if action == "signup":
            return self._signup(body, r)
        if action == "login":
            return self._login(body, r)
        if action == "logout":
            return self._logout(body, r)
        if action == "me":
            return self._me(body, r)
        return self._send(400, {"ok": False, "error": "Unknown action."})

    # GET /api/auth?action=me with bearer token, for convenience on page load.
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        action = (q.get("action") or [""])[0].strip().lower()
        if action != "me":
            return self._send(400, {"ok": False, "error": "Use POST."})
        r = _redis()
        if r is None:
            return self._send(503, {"ok": False, "error": "Auth backend not configured."})
        return self._me({}, r)

    def _signup(self, body, r):
        email = _norm_email(body.get("email"))
        password = str(body.get("password") or "")
        if not EMAIL_RE.match(email):
            return self._send(400, {"ok": False, "error": "Enter a valid email address."})
        if len(password) < 8:
            return self._send(400, {"ok": False, "error": "Password must be at least 8 characters."})
        try:
            if r.get("user:" + email):
                return self._send(409, {"ok": False, "error": "An account with that email already exists. Try signing in."})
        except Exception:
            return self._send(503, {"ok": False, "error": "Auth backend unavailable."})
        salt, digest = _hash_pw(password)
        tier = _tier_for(email)
        rec = {"pw": digest, "salt": salt, "created_at": int(time.time()), "tier": tier}
        try:
            r.set("user:" + email, json.dumps(rec))
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not create account."})
        token = self._new_session(r, email)
        return self._send(200, {"ok": True, "token": token, "email": email, "tier": tier})

    def _login(self, body, r):
        email = _norm_email(body.get("email"))
        password = str(body.get("password") or "")
        if not email or not password:
            return self._send(400, {"ok": False, "error": "Email and password required."})
        try:
            raw = r.get("user:" + email)
        except Exception:
            return self._send(503, {"ok": False, "error": "Auth backend unavailable."})
        if not raw:
            return self._send(401, {"ok": False, "error": "No account found for that email."})
        try:
            rec = json.loads(raw)
        except Exception:
            return self._send(500, {"ok": False, "error": "Account record corrupt — contact support."})
        if not _verify_pw(password, rec.get("salt", ""), rec.get("pw", "")):
            return self._send(401, {"ok": False, "error": "Incorrect password."})
        # Refresh tier in case a whitelist change promoted this user.
        tier = _tier_for(email) if _tier_for(email) == "pro" else rec.get("tier", "free")
        token = self._new_session(r, email)
        return self._send(200, {"ok": True, "token": token, "email": email, "tier": tier})

    def _logout(self, body, r):
        token = (str(body.get("token") or "").strip() or _bearer(self.headers))
        if token:
            try:
                r.delete("session:" + token)
            except Exception:
                pass
        return self._send(200, {"ok": True})

    def _me(self, body, r):
        token = (str(body.get("token") or "").strip() or _bearer(self.headers))
        if not token:
            return self._send(401, {"ok": False, "error": "No session."})
        email = session_lookup(r, token)
        if not email:
            return self._send(401, {"ok": False, "error": "Session expired."})
        try:
            raw = r.get("user:" + email)
            rec = json.loads(raw) if raw else {}
        except Exception:
            rec = {}
        tier = _tier_for(email) if _tier_for(email) == "pro" else rec.get("tier", "free")
        return self._send(200, {"ok": True, "email": email, "tier": tier})

    def _new_session(self, r, email):
        token = secrets.token_urlsafe(32)
        try:
            r.set("session:" + token, email, ex=SESSION_TTL)
        except Exception:
            pass
        return token

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
