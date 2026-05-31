from http.server import BaseHTTPRequestHandler
import json
import os
import re
import time
import uuid
import datetime

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

# Valid promo codes -> days of free Pro access. Validated server-side so the code
# list is not exposed in the client bundle.
VALID = {"BETA2026": 30}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_USES = 500                        # max total redemptions per code
# Codes are dead after this date (UTC).
PROMO_EXPIRY = int(datetime.datetime(2026, 8, 31, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp())
LIMIT_MSG = "Promo code expired or limit reached"


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


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            body = {}
        ip = self._client_ip()
        r = _redis()
        # Per-IP attempt cap (uses the least-spoofable rightmost X-Forwarded-For IP).
        if r is not None:
            try:
                k = f"promo:ip:{ip}:{int(time.time() // 3600)}"
                n = r.incr(k)
                if n == 1:
                    r.expire(k, 3600)
                if n > 20:
                    return self._send(429, {"ok": False, "error": "Too many attempts. Please try again later."})
            except Exception:
                pass
        code = str(body.get("code") or "").strip().upper()
        days = VALID.get(code)
        if not days:
            return self._send(200, {"ok": False, "error": "Invalid promo code."})
        # Expired?
        if time.time() > PROMO_EXPIRY:
            return self._send(200, {"ok": False, "error": LIMIT_MSG})
        # Require a valid email to redeem (ties each redemption to an identity).
        email = str(body.get("email") or "").strip().lower()
        if not EMAIL_RE.match(email):
            return self._send(200, {"ok": False, "error": "A valid email is required to redeem a promo code."})
        # Enforce the total-redemption cap.
        if r is not None:
            try:
                uses = int(r.get(f"promo:{code}:count") or 0)
            except Exception:
                uses = 0
            if uses >= MAX_USES:
                return self._send(200, {"ok": False, "error": LIMIT_MSG})
        until = int(time.time()) + days * 86400
        # Record the activation in Redis (per-device token), TTL = the grant window.
        if r is not None:
            try:
                token = (str(body.get("token") or "").strip() or uuid.uuid4().hex)[:64]
                r.set(f"promo:{code}:{token}", str(until), ex=days * 86400)
                r.incr(f"promo:{code}:count")
            except Exception:
                pass
        return self._send(200, {"ok": True, "days": days, "until": until,
                                "message": f"Pro access unlocked for {days} days!"})

    def _client_ip(self):
        xff = self.headers.get("X-Forwarded-For") or self.headers.get("x-forwarded-for") or ""
        if xff:
            return xff.split(",")[-1].strip()
        try:
            return self.client_address[0]
        except Exception:
            return "unknown"

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
