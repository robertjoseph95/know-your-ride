from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse

try:
    from upstash_redis import Redis
except Exception:
    Redis = None


# Owner / comp accounts that always have Pro access, regardless of Redis/Stripe.
WHITELIST = {"robert.joseph95@yahoo.com"}


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
        if email in WHITELIST:
            return self._send(200, {"subscribed": True, "email": email, "whitelisted": True})
        r = _redis()
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
