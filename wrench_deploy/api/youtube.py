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

try:
    import _gate                      # PHASE 2: shared server-side Pro gate (closes the localStorage bypass)
except Exception:
    _gate = None

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
        is_pro, _email = (_gate.check(self) if _gate else (False, None))
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
