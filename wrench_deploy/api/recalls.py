from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse
import urllib.request

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

# Free NHTSA recalls API (no key). The VIN-specific endpoint (recallsByVehicleId)
# is not publicly accessible (403), so we query by make/model/year — which the VIN
# decode already produces, so it's still automatic for the user.
NHTSA = "https://api.nhtsa.gov/recalls/recallsByVehicle"
UA = "Mozilla/5.0 (compatible; KnowYourRide/1.0; +https://knowyourride.net)"
RECALLS_CACHE_TTL = 60 * 60 * 24  # 24h — recalls change rarely


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
        make = (q.get("make") or [""])[0].strip()
        model = (q.get("model") or [""])[0].strip()
        year = (q.get("year") or q.get("modelYear") or [""])[0].strip()
        if not (make and model and year):
            return self._send(400, {"error": "make, model and year are required", "recalls": []})
        rc = _redis()
        cache_key = f"recalls:{make}|{model}|{year}".lower()
        if rc:
            try:
                cached = rc.get(cache_key)
                if cached:
                    return self._send(200, {**json.loads(cached), "cached": True})
            except Exception:
                pass
        try:
            url = NHTSA + "?" + urllib.parse.urlencode({"make": make, "model": model, "modelYear": year})
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", "ignore"))
            items = data.get("results") or data.get("Results") or []
            payload = {"count": len(items), "recalls": items}
            if rc:
                try:
                    rc.set(cache_key, json.dumps(payload), ex=RECALLS_CACHE_TTL)
                except Exception:
                    pass
            return self._send(200, payload)
        except Exception as e:
            print(f"[recalls] lookup failed: {e}", file=sys.stderr)  # server-side only
            return self._send(502, {"error": "Recall lookup temporarily unavailable.", "recalls": []})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
