try:  # Sentry server-side error monitoring (F-D3); inert until SENTRY_DSN is set
    import os as _os, sentry_sdk as _sentry; _sentry.init(dsn=_os.environ.get("SENTRY_DSN"))
except Exception: pass
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import datetime
import urllib.parse

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

SAFETY = ("brake", "suspension", "fuel pump", "fuel system", "airbag",
          "timing belt", "timing chain", "steering", "clutch")
CACHE_TTL = 60 * 60 * 24 * 90  # 90 days
MODEL = "claude-sonnet-4-6"
GUIDE_MONTHLY_BUDGET = 30.0          # hard cap on Claude spend per month (USD)
IN_RATE = 3.0 / 1_000_000            # claude-sonnet input  $/token
OUT_RATE = 15.0 / 1_000_000          # claude-sonnet output $/token
BUDGET_MSG = "Guide temporarily unavailable. Please try again later."

GUIDE_SYSTEM = (
    "You are an expert auto mechanic writing a concise DIY guide for a home mechanic. "
    "Follow these rules strictly:\n"
    "- Use ONLY the exact specifications provided in the user message. NEVER invent, guess, or "
    "recall from memory any torque value, fluid capacity, fluid type, part number, socket size, "
    "or gap. If a number needed for a step was not provided, write \"check your factory service "
    "manual\" instead of a value.\n"
    "- Begin with a one-line intro, then a \"## Safety\" section (jack stands not just a jack, "
    "gloves, hot engine/fluids, disconnect the battery when relevant).\n"
    "- Then a \"## Steps\" numbered list, then a \"## Specs\" recap as a simple bullet list (no tables, "
    "no horizontal rules) listing only the provided values. Use **bold** for key values. "
    "Keep it under ~400 words.\n"
    "- Only cover the single named service. Do not branch into other repairs."
)

_SPECS = None


def _specs():
    global _SPECS
    if _SPECS is None:
        for p in (os.path.join(os.path.dirname(__file__), "specs.json"),
                  os.path.join(os.getcwd(), "api", "specs.json")):
            try:
                with open(p, encoding="utf-8") as f:
                    _SPECS = json.load(f)
                    break
            except Exception:
                continue
        if _SPECS is None:
            _SPECS = {}
    return _SPECS


def build_specs(v, service):
    s = service.lower()
    spec = {}

    def tq(comp):
        t = (v.get("torque") or {}).get(comp)
        if t and t[0] is not None:
            return f"{t[0]} ft-lb" + (f" ({t[1]} Nm)" if t[1] else "")
        return None

    o = v.get("oil") or {}
    p = v.get("parts") or {}
    if "oil" in s:
        if o.get("viscosity"): spec["Oil viscosity"] = o["viscosity"]
        if o.get("oil_type"): spec["Oil type"] = o["oil_type"]
        if o.get("capacity"): spec["Oil capacity (with filter)"] = f"{o['capacity']} qt"
        if o.get("oem_spec"): spec["OEM oil spec"] = o["oem_spec"]
        if o.get("drain_socket"): spec["Drain plug socket"] = f"{o['drain_socket']} mm"
        if o.get("drain_thread"): spec["Drain plug thread"] = o["drain_thread"]
        if o.get("drain_gasket"): spec["Drain gasket"] = o["drain_gasket"]
        if o.get("oil_filter"): spec["Oil filter"] = o["oil_filter"]
        if tq("drain_bolt"): spec["Drain plug torque"] = tq("drain_bolt")
    elif "spark" in s:
        if p.get("spark_plug"): spec["Spark plug"] = p["spark_plug"]
        if p.get("plug_gap"): spec["Plug gap"] = p["plug_gap"]
        if p.get("plug_qty"): spec["Plug count"] = p["plug_qty"]
        if tq("spark_plug"): spec["Spark plug torque"] = tq("spark_plug")
    elif "air filter" in s:
        if p.get("air_filter"): spec["Air filter"] = p["air_filter"]
        if p.get("air_interval"): spec["Change interval"] = f"{p['air_interval']} mi"
    elif "cabin" in s:
        if p.get("cabin_filter"): spec["Cabin filter"] = p["cabin_filter"]
    elif "tire" in s:
        if tq("lug_nut"): spec["Lug nut torque"] = tq("lug_nut")
        if p.get("tire"): spec["Tire size"] = p["tire"]
        if p.get("psi_f"): spec["Tire pressure (front)"] = f"{p['psi_f']} psi"
        if p.get("psi_r"): spec["Tire pressure (rear)"] = f"{p['psi_r']} psi"
    elif "battery" in s:
        if p.get("battery_group"): spec["Battery group size"] = p["battery_group"]
        if p.get("battery_cca"): spec["Battery CCA"] = p["battery_cca"]
        if p.get("battery"): spec["Battery"] = p["battery"]
    elif "wiper" in s:
        for w in (p.get("wipers") or [])[:3]:
            if w.get("size"):
                lbl = f"Wiper blade ({w.get('pos')})" if w.get("pos") else "Wiper blade"
                spec[lbl] = f"{w['size']} in"
    return spec


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
    def do_GET(self):
        # PHASE 2 (server-side Pro gate): validate the REAL subscription on every paid call.
        # The browser localStorage 'kyr_pro' flag is ignored -- it is no longer a security boundary.
        is_pro, _email = _pro_gate(self)
        if not is_pro:
            return self._send(200, {"guide": None, "pro_required": True, "label": None,
                                    "message": "AI repair guides are a Pro feature. Upgrade to unlock step-by-step, vehicle-specific guides."})
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        vid = (q.get("vehicle_id") or [""])[0]
        service = (q.get("service") or [""])[0]
        if not (vid and service):
            return self._send(400, {"guide": None, "error": "vehicle_id and service required"})
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return self._send(500, {"guide": None, "error": "server not configured (ANTHROPIC_API_KEY)"})
        v = _specs().get(str(vid))
        if not v:
            return self._send(404, {"guide": None, "error": "vehicle not found"})
        label = v.get("label")
        if any(k in service.lower() for k in SAFETY):
            return self._send(200, {"guide": None, "safety_blocked": True, "label": label,
                                    "message": (f"{service.title()} is safety-critical and we don't have "
                                                "verified torque/procedure specs for this vehicle. Get the exact "
                                                "figures from the factory service manual, or have a professional "
                                                "do it -- incorrect fastener torque here can cause failure.")})
        cache_key = f"guide:{vid}|{service}".lower()
        r = _redis()
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    return self._send(200, {**json.loads(cached), "cached": True})
            except Exception:
                pass
        sp = build_specs(v, service)
        speclines = "\n".join(f"- {k}: {val}" for k, val in sp.items()) or \
            "(no specs available in our database for this service)"
        user = (f"Vehicle: {label}\nService: {service}\n\n"
                f"Known specs (use these EXACT values; invent nothing else):\n{speclines}\n\n"
                "Write the DIY guide.")
        # Budget cap: stop paid generation once monthly Claude spend hits the limit.
        month = datetime.datetime.now(datetime.timezone.utc).strftime("%Y_%m")
        spend_key = f"guide_api_spend_{month}"
        if r:
            try:
                if float(r.get(spend_key) or 0) >= GUIDE_MONTHLY_BUDGET:
                    return self._send(200, {"guide": None, "budget_exceeded": True, "label": label, "message": BUDGET_MSG})
            except Exception:
                pass
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=key)
            msg = client.messages.create(model=MODEL, max_tokens=1400, system=GUIDE_SYSTEM,
                                         messages=[{"role": "user", "content": user}])
            guide = "".join(b.text for b in msg.content if b.type == "text").strip()
            in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
        except Exception as e:
            print(f"[guide] generation failed: {e}", file=sys.stderr)  # server-side only
            return self._send(200, {"guide": None, "error": BUDGET_MSG})
        # Track spend against the monthly budget.
        if r:
            try:
                cost = in_tok * IN_RATE + out_tok * OUT_RATE
                # Atomic increment (avoids read-modify-write races under concurrency).
                r.incrbyfloat(spend_key, cost)
                r.expire(spend_key, 86400 * 31)
            except Exception:
                pass
        payload = {"guide": guide, "label": label, "specs": sp, "safety_blocked": False}
        if r:
            try:
                r.set(cache_key, json.dumps(payload), ex=CACHE_TTL)
            except Exception:
                pass
        self._send(200, {**payload, "cached": False})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
