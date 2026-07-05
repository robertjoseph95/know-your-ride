try:  # Sentry server-side error monitoring (F-D3); inert until SENTRY_DSN is set
    import os as _os, sentry_sdk as _sentry; _sentry.init(dsn=_os.environ.get("SENTRY_DSN"))
except Exception: pass
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse

try:
    from upstash_redis import Redis
except Exception:
    Redis = None


def _whitelist():
    # Comma-separated emails from the PRO_WHITELIST env var (kept out of the public repo).
    # These always have Pro access, regardless of Redis/Stripe.
    return {e.strip().lower() for e in os.environ.get("PRO_WHITELIST", "").split(",") if e.strip()}


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


def _stripe_active(email):
    """Source-of-truth fallback when Redis has no record yet (e.g. restore on a new device)."""
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return None
    try:
        import stripe
        stripe.api_key = key
        for c in stripe.Customer.list(email=email, limit=20).data:
            for status in ("active", "trialing"):
                if stripe.Subscription.list(customer=c.id, status=status, limit=1).data:
                    return True
        return False
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    """GET /api/verify-subscription?email=... -> {"subscribed": bool}. Checks the Upstash
    Redis record maintained by the webhook; falls back to Stripe if there's no record."""

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        email = (q.get("email") or [""])[0].strip().lower()
        if not email:
            return self._send(400, {"subscribed": False, "error": "email parameter required"})
        r = _redis()
        # Per-IP rate limit (LOW audit fix). This endpoint accepts an email for the
        # "restore Pro on a new device" flow, so it cannot require auth — instead we
        # cap requests per IP to prevent bulk subscriber-status enumeration.
        if r is not None:
            ip = (self.headers.get("X-Forwarded-For") or self.headers.get("x-forwarded-for")
                  or self.client_address[0] or "unknown").split(",")[-1].strip()  # rightmost = least spoofable
            rk = "vsub:ip:" + ip
            try:
                n = r.incr(rk)
                r.expire(rk, 3600)  # always (re)set TTL so a crash between incr/expire can't orphan the key
                if n > 20:
                    return self._send(429, {"subscribed": False, "error": "Too many requests. Please try again in a bit."})
            except Exception:
                pass
        if email in _whitelist():
            return self._send(200, {"subscribed": True, "email": email, "whitelisted": True})
        if r is not None:
            try:
                v = r.get("sub:" + email)
                if v == "active":
                    return self._send(200, {"subscribed": True, "email": email})
                if v == "inactive":
                    return self._send(200, {"subscribed": False, "email": email})
            except Exception:
                pass
        # No Redis record yet -> ask Stripe and backfill the cache.
        active = _stripe_active(email)
        if active is not None and r is not None:
            try:
                r.set("sub:" + email, "active" if active else "inactive",
                      ex=(60 * 60 * 6 if active else 60 * 30))
            except Exception:
                pass
        return self._send(200, {"subscribed": bool(active), "email": email})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
