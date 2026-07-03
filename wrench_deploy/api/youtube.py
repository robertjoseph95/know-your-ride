from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys
import datetime
import urllib.parse
import requests

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

CACHE_TTL = 60 * 60 * 24 * 30  # 30 days


def _fmt_dur(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return ""
    h, mn, s = (int(x) if x else 0 for x in m.groups())
    return f"{h}:{mn:02d}:{s:02d}" if h else f"{mn}:{s:02d}"


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
        # The browser 'kyr_pro' flag is ignored -- it is no longer a security boundary.
        is_pro, _email = _pro_gate(self)
        if not is_pro:
            return self._send(200, {"videos": [], "pro_required": True,
                                    "message": "Video tutorials are a Pro feature. Upgrade to unlock curated how-to videos."})
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        year = (q.get("year") or [""])[0]
        make = (q.get("make") or [""])[0]
        model = (q.get("model") or [""])[0]
        service = (q.get("service") or [""])[0]
        key = os.environ.get("YOUTUBE_API_KEY", "")
        if not key:
            return self._send(500, {"videos": [], "error": "server not configured (YOUTUBE_API_KEY)"})
        if not (year and make and model and service):
            return self._send(400, {"videos": [], "error": "year, make, model, service required"})

        cache_key = f"yt:{year}|{make}|{model}|{service}".lower()
        r = _redis()
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    return self._send(200, {"videos": json.loads(cached), "cached": True})
            except Exception:
                pass
        # Per-IP daily cap on cache MISSES (LOW audit fix) to protect the YouTube quota.
        if r:
            ip = (self.headers.get("X-Forwarded-For") or self.client_address[0] or "unknown").split(",")[-1].strip()  # rightmost = least spoofable
            day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            ipk = f"yt:ip:{day}:{ip}"
            try:
                n = r.incr(ipk)
                if n == 1:
                    r.expire(ipk, 60 * 60 * 48)
                if n > 50:
                    return self._send(429, {"videos": [], "error": "Daily video-search limit reached. Please try again tomorrow."})
            except Exception:
                pass
        try:
            videos = self._search(year, make, model, service, key)
        except Exception as e:
            print(f"[youtube] search failed: {e}", file=sys.stderr)  # server-side only
            return self._send(200, {"videos": [], "error": "Video search temporarily unavailable."})
        if r:
            try:
                r.set(cache_key, json.dumps(videos), ex=CACHE_TTL)
            except Exception:
                pass
        self._send(200, {"videos": videos, "cached": False})

    def _search(self, year, make, model, service, key):
        # NOTE: the two YouTube calls are DEPENDENT (search returns video IDs, then the
        # videos.list call fetches stats for those IDs), so they cannot run concurrently.
        # Instead we cap each at timeout=12 and make the second (stats) call best-effort:
        # if it times out/fails we return the search results WITHOUT view counts/durations
        # (partial results) rather than failing the whole request. vercel.json sets
        # maxDuration=30 for this function so 2x12s can't be hard-killed mid-request.
        q = f"{year} {make} {model} {service} DIY how to"
        sr = requests.get("https://www.googleapis.com/youtube/v3/search",
                          params={"part": "snippet", "type": "video", "maxResults": 3, "q": q, "key": key},
                          timeout=12).json()
        items = sr.get("items", [])
        ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        stats = {}
        if ids:
            try:
                dv = requests.get("https://www.googleapis.com/youtube/v3/videos",
                                  params={"part": "statistics,contentDetails", "id": ",".join(ids), "key": key},
                                  timeout=12).json()
                for it in dv.get("items", []):
                    stats[it["id"]] = {
                        "views": int(it.get("statistics", {}).get("viewCount", 0) or 0),
                        "duration": _fmt_dur(it.get("contentDetails", {}).get("duration", "")),
                    }
            except Exception as e:
                print(f"[youtube] stats fetch failed, returning partial results: {e}", file=sys.stderr)
        out = []
        for it in items:
            vid = it.get("id", {}).get("videoId")
            if not vid:
                continue
            sn = it.get("snippet", {})
            th = sn.get("thumbnails", {})
            st = stats.get(vid, {})
            out.append({"id": vid, "title": sn.get("title"), "channel": sn.get("channelTitle"),
                        "views": st.get("views"),
                        "thumbnail": (th.get("medium") or th.get("high") or th.get("default") or {}).get("url"),
                        "duration": st.get("duration")})
        return out

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
