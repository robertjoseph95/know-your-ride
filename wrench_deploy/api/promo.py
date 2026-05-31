from http.server import BaseHTTPRequestHandler
import json
import os
import time
import uuid

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

# Valid promo codes -> days of free Pro access. Validated server-side so the code
# list is not exposed in the client bundle.
VALID = {"BETA2026": 30}


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
        code = str(body.get("code") or "").strip().upper()
        days = VALID.get(code)
        if not days:
            return self._send(200, {"ok": False, "error": "Invalid promo code."})
        until = int(time.time()) + days * 86400
        # Record the activation in Redis (per-device token), TTL = the grant window.
        r = _redis()
        if r is not None:
            try:
                token = (str(body.get("token") or "").strip() or uuid.uuid4().hex)[:64]
                r.set(f"promo:{code}:{token}", str(until), ex=days * 86400)
                r.incr(f"promo:{code}:uses")
            except Exception:
                pass
        return self._send(200, {"ok": True, "days": days, "until": until,
                                "message": f"Pro access unlocked for {days} days!"})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
