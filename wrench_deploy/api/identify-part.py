from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import base64
import datetime

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

def _pro_gate(handler):
    """Self-contained server-side Pro gate (NO sibling import -- Vercel's Python builder
    bundles only the entry file, so `import _gate` fails silently and would gate everyone).
    Pro ONLY if a session token (Authorization: Bearer / cookie) resolves to an email that is
    PRO_WHITELIST / sub:{email}=='active' / a live Stripe active subscription. The X-KYR-Email
    header fallback was REMOVED 2026-07-02 (unauthenticated Pro bypass + email enumeration);
    the browser localStorage 'kyr_pro' flag is ignored entirely."""
    import os, http.cookies
    headers = getattr(handler, "headers", None)
    if headers is None:
        return (False, None)

    def _r():
        try:
            from upstash_redis import Redis
        except Exception:
            return None
        u = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
        t = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
        if not (u and t):
            return None
        try:
            return Redis(url=u, token=t)
        except Exception:
            return None

    r = _r()
    email = None
    a = headers.get("Authorization") or headers.get("authorization") or ""
    tok = a[7:].strip() if a.lower().startswith("bearer ") else ""
    if not tok:
        raw = headers.get("Cookie") or headers.get("cookie") or ""
        if raw:
            try:
                jar = http.cookies.SimpleCookie(); jar.load(raw)
                for n in ("kyr_session", "kyr_token", "session"):
                    if n in jar and jar[n].value:
                        tok = jar[n].value.strip(); break
            except Exception:
                pass
    if tok and r is not None:
        try:
            email = r.get("session:" + tok) or None
        except Exception:
            email = None
    if not email or "@" not in email:
        return (False, None)
    email = email.strip().lower()

    if email in {x.strip().lower() for x in os.environ.get("PRO_WHITELIST", "").split(",") if x.strip()}:
        return (True, email)
    if r is not None:
        try:
            v = r.get("sub:" + email)
            if v == "active":
                return (True, email)
            if v == "inactive":
                return (False, email)
        except Exception:
            pass
    active = None
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if key:
        try:
            import stripe
            stripe.api_key = key
            active = False
            for c in stripe.Customer.list(email=email, limit=20).data:
                for status in ("active", "trialing"):
                    if stripe.Subscription.list(customer=c.id, status=status, limit=1).data:
                        active = True; break
                if active:
                    break
        except Exception:
            active = None
    if active is not None and r is not None:
        try:
            r.set("sub:" + email, "active" if active else "inactive", ex=(60 * 60 * 6 if active else 60 * 30))
        except Exception:
            pass
    return (bool(active), email)

DAILY_CAP = 100
PER_IP = 3
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MONTHLY_BUDGET = 50.0
DAILY_ALERT = 1.50
IN_RATE = 3.0 / 1_000_000
OUT_RATE = 15.0 / 1_000_000
MODEL = "claude-sonnet-4-6"
VISION_SYSTEM = (
    "You are an expert auto-parts identifier. Identify the automotive part in the image: its "
    "common name, what it does, and any markings/part numbers actually visible in the image. Be "
    "concise (under 150 words). Never invent a part number that is not visibly printed. If the "
    "image is not a car part, say so plainly."
)


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
        # PHASE 2 (server-side Pro gate): validate the REAL subscription on every paid call.
        # The browser 'kyr_pro' flag is ignored -- it is no longer a security boundary.
        is_pro, _email = _pro_gate(self)
        if not is_pro:
            return self._send(200, {"identification": None, "pro_required": True,
                                    "message": "Part identification is a Pro feature. Upgrade to scan and identify parts."})
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return self._send(503, {"error": "server not configured (ANTHROPIC_API_KEY)"})
        ip = (self.headers.get("X-Forwarded-For") or self.client_address[0] or "unknown").split(",")[-1].strip()  # rightmost = least spoofable
        now = datetime.datetime.now(datetime.timezone.utc)
        today, month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
        r = _redis()
        # FAIL CLOSED: without Redis we cannot enforce caps/budget, so do not allow paid scans.
        if r is None:
            return self._send(503, {"error": "rate limiting/budget store unavailable; identify-part disabled for cost safety"})
        # cost-control gates -- all BEFORE the paid vision call
        try:
            if r.get("idp:disabled") == "1":
                return self._send(503, {"error": "identify-part disabled (monthly budget exceeded)"})
            if float(r.get(f"idp:spend:{month}") or 0) > MONTHLY_BUDGET:
                r.set("idp:disabled", "1")
                return self._send(503, {"error": "identify-part disabled (monthly budget exceeded)"})
            if int(r.get(f"idp:count:{today}") or 0) >= DAILY_CAP:
                return self._send(429, {"error": f"daily scan cap reached ({DAILY_CAP}/day)"})
            if int(r.get(f"idp:ip:{today}:{ip}") or 0) >= PER_IP:
                return self._send(429, {"error": f"per-IP daily limit reached ({PER_IP}/day)"})
        except Exception:
            return self._send(503, {"error": "budget store error; identify-part disabled for cost safety"})

        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length <= 0:
            return self._send(400, {"error": "POST a base64-encoded image in the body"})
        # base64 inflates ~33%; cap the body read with headroom, drain on reject
        if length > MAX_IMAGE_BYTES * 2:
            self._drain(length)
            return self._send(413, {"error": "image exceeds the 2 MB limit"})
        raw = self.rfile.read(length)
        try:
            txt = raw.decode("ascii", "ignore").strip()
            if txt.startswith("data:"):
                txt = txt.split(",", 1)[1]
            image = base64.b64decode(txt, validate=False)
        except Exception:
            image = raw  # tolerate raw image bytes too
        if len(image) > MAX_IMAGE_BYTES:
            return self._send(413, {"error": "image exceeds the 2 MB limit"})

        media = (self.headers.get("X-Image-Type") or "image/jpeg").split(";")[0].strip().lower()
        if media not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            media = "image/jpeg"
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=key)
            b64 = base64.b64encode(image).decode("ascii")
            msg = client.messages.create(model=MODEL, max_tokens=400, system=VISION_SYSTEM,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                    {"type": "text", "text": "What automotive part is this?"}]}])
            text = "".join(b.text for b in msg.content if b.type == "text").strip()
            in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
        except Exception as e:
            print(f"[identify-part] vision failed: {e}", file=sys.stderr)  # server-side only
            return self._send(200, {"identification": None, "error": "Part identification temporarily unavailable. Please try again."})

        cost = in_tok * IN_RATE + out_tok * OUT_RATE
        daily_total = monthly_total = None
        if r:
            try:
                r.incr(f"idp:count:{today}"); r.expire(f"idp:count:{today}", 60 * 60 * 48)
                r.incr(f"idp:ip:{today}:{ip}"); r.expire(f"idp:ip:{today}:{ip}", 60 * 60 * 48)
                # Atomic spend increments (avoid read-modify-write races under concurrency).
                daily_total = float(r.incrbyfloat(f"idp:spend:day:{today}", cost)); r.expire(f"idp:spend:day:{today}", 86400 * 31)
                monthly_total = float(r.incrbyfloat(f"idp:spend:{month}", cost)); r.expire(f"idp:spend:{month}", 86400 * 31)
                prev_day = daily_total - cost
                if prev_day < DAILY_ALERT <= daily_total:
                    r.set(f"idp:alert:{today}", f"Daily spend ${daily_total:.2f} reached ${DAILY_ALERT:.2f}", ex=60 * 60 * 48)
                if monthly_total > MONTHLY_BUDGET:
                    r.set("idp:disabled", "1")
                    r.set(f"idp:alert:month:{month}", "Monthly budget exceeded -- identify-part disabled", ex=60 * 60 * 24 * 40)
            except Exception:
                pass
        out = {"identification": text, "tokens_used": in_tok + out_tok, "estimated_cost": round(cost, 4)}
        if daily_total is not None:
            out["daily_total"] = round(daily_total, 4)
            out["monthly_total"] = round(monthly_total, 4)
        self._send(200, out)

    def _drain(self, length):
        try:
            remaining = min(length, 5 * 1024 * 1024)
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except Exception:
            pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
