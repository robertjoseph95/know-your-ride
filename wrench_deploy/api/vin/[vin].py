from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import requests


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        key = os.environ.get("VEHICLE_FINDER_KEY", "")
        path = urllib.parse.urlparse(self.path).path
        vin = urllib.parse.unquote(path.rstrip("/").split("/")[-1]).strip().upper()
        if not key:
            return self._send(500, {"error": "server not configured (VEHICLE_FINDER_KEY)"})
        if len(vin) != 17:
            return self._send(400, {"error": "VIN must be 17 characters"})
        try:
            r = requests.get(f"https://api.vehicle-finder.com/v1/vin/{vin}",
                             headers={"X-API-Key": key}, timeout=15)
            if r.status_code == 404:
                return self._send(200, {"error": "VIN not found"})
            data = r.json()
            return self._send(200, data.get("data", data) if isinstance(data, dict) else data)
        except Exception as e:
            return self._send(502, {"error": f"decode failed: {e}"})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
