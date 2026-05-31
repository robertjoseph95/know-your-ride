"""
VIN decode — NHTSA vPIC (free, no API key).

Replaces the paid Vehicle Finder proxy (api.vehicle-finder.com) with NHTSA's
public vPIC DecodeVIN endpoint so the $99/mo subscription can be cancelled.

Response contract (unchanged — the demo's decodeVIN() in the front-end reads
these flat keys; do not rename):
  make, model, year, trim, displacement_liters, engine, cylinders, fuel_type
On no decode: {"error": "VIN not found"} (200), matching the old behavior so the
client shows "No decode result for that VIN."
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys
import urllib.parse
import requests

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # real VINs exclude I/O/Q
VPIC_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"
VIN_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days — a VIN's decode never changes


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


def fetch_vpic(vin):
    """Call vPIC DecodeVIN; return {Variable: Value} with blank/N-A values dropped."""
    r = requests.get(VPIC_URL.format(vin=urllib.parse.quote(vin)), timeout=15)
    r.raise_for_status()
    payload = r.json()
    vals = {}
    for item in payload.get("Results") or []:
        var, val = item.get("Variable"), item.get("Value")
        if var and val not in (None, "", "Not Applicable"):
            vals[var] = val
    return vals


def map_vpic(vals):
    """Map vPIC Variable/Value pairs to our flat VIN-decode contract."""
    def first(*names):
        for n in names:
            if vals.get(n):
                return vals[n]
        return None

    make = first("Make")
    model = first("Model")
    year = first("Model Year")
    trim = first("Trim", "Series", "Trim2", "Series2")
    disp = first("Displacement (L)")
    cyl = first("Engine Number of Cylinders")
    fuel = first("Fuel Type - Primary")
    engine = first("Engine Model")

    if disp:
        try:
            disp = f"{float(disp):.1f}"          # normalize "2.3960000" -> "2.4"
        except (TypeError, ValueError):
            pass

    return {
        "make": make,                            # vPIC returns UPPERCASE; client matches case-insensitively
        "model": model,
        "year": int(year) if year and str(year).isdigit() else year,
        "trim": trim,
        "displacement_liters": disp,
        "cylinders": int(cyl) if cyl and str(cyl).isdigit() else cyl,
        "fuel_type": fuel,
        "engine": engine,
        "source": "nhtsa-vpic",
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        vin = urllib.parse.unquote(path.rstrip("/").split("/")[-1]).strip().upper()
        if not VIN_RE.match(vin):
            return self._send(400, {"error": "VIN must be 17 characters (A-Z except I/O/Q, 0-9)."})
        # Cache: a decoded VIN never changes, so cache 30 days in Redis.
        r = _redis()
        cache_key = "vin_decode_" + vin
        if r:
            try:
                cached = r.get(cache_key)
                if cached:
                    return self._send(200, {**json.loads(cached), "cached": True})
            except Exception:
                pass
        try:
            vals = fetch_vpic(vin)
        except Exception as e:
            print(f"[vin] decode failed: {e}", file=sys.stderr)  # server-side only
            return self._send(502, {"error": "VIN decode service temporarily unavailable. Please try again."})
        decoded = map_vpic(vals)
        if not decoded.get("make"):
            return self._send(200, {"error": "VIN not found"})
        if r:
            try:
                r.set(cache_key, json.dumps(decoded), ex=VIN_CACHE_TTL)
            except Exception:
                pass
        return self._send(200, decoded)

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return
