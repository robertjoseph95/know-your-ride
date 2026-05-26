from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.parse
import requests

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

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
        try:
            videos = self._search(year, make, model, service, key)
        except Exception as e:
            return self._send(200, {"videos": [], "error": f"youtube error: {e}"})
        if r:
            try:
                r.set(cache_key, json.dumps(videos), ex=CACHE_TTL)
            except Exception:
                pass
        self._send(200, {"videos": videos, "cached": False})

    def _search(self, year, make, model, service, key):
        q = f"{year} {make} {model} {service} DIY how to"
        sr = requests.get("https://www.googleapis.com/youtube/v3/search",
                          params={"part": "snippet", "type": "video", "maxResults": 3, "q": q, "key": key},
                          timeout=15).json()
        items = sr.get("items", [])
        ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        stats = {}
        if ids:
            dv = requests.get("https://www.googleapis.com/youtube/v3/videos",
                              params={"part": "statistics,contentDetails", "id": ",".join(ids), "key": key},
                              timeout=15).json()
            for it in dv.get("items", []):
                stats[it["id"]] = {
                    "views": int(it.get("statistics", {}).get("viewCount", 0) or 0),
                    "duration": _fmt_dur(it.get("contentDetails", {}).get("duration", "")),
                }
        out = []
        for it in items:
            vid = it["id"].get("videoId")
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
