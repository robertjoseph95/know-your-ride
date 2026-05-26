from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request

# Free NHTSA recalls API (no key). The VIN-specific endpoint (recallsByVehicleId)
# is not publicly accessible (403), so we query by make/model/year — which the VIN
# decode already produces, so it's still automatic for the user.
NHTSA = "https://api.nhtsa.gov/recalls/recallsByVehicle"
UA = "Mozilla/5.0 (compatible; KnowYourRide/1.0; +https://knowyourride.net)"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        make = (q.get("make") or [""])[0].strip()
        model = (q.get("model") or [""])[0].strip()
        year = (q.get("year") or q.get("modelYear") or [""])[0].strip()
        if not (make and model and year):
            return self._send(400, {"error": "make, model and year are required", "recalls": []})
        try:
            url = NHTSA + "?" + urllib.parse.urlencode({"make": make, "model": model, "modelYear": year})
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            items = data.get("results") or data.get("Results") or []
            return self._send(200, {"count": len(items), "recalls": items})
        except Exception as e:
            return self._send(502, {"error": f"recall lookup failed: {e}", "recalls": []})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
