"""
garage.py — Per-user saved vehicles + mileage.

Routes (POST with `action` field in body):
- list                                  -> { ok, vehicles: [...], mileage: {vid: int} }
- add    { vehicle }                    -> { ok, vehicles: [...] }
- remove { vehicle_id }                 -> { ok, vehicles: [...] }
- mileage { vehicle_id, mileage }       -> { ok, mileage }

Bearer auth required (Authorization: Bearer <session_token>).

Redis schema:
- user_vehicles:{email}                 -> JSON array of saved-vehicle records
- user_mileage:{email}:{vehicle_id}     -> int (current odometer)

Vehicle record shape:
  { id, year, make, model, engine?, trim?, vin?, added_at }
  - id is the wrench vehicle_id (int), or null for VIN-only records that have no DB match.

Free tier: 0 saved vehicles. Pro tier: 3 saved vehicles.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import time

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

PRO_VEHICLE_CAP = 3
FREE_VEHICLE_CAP = 0
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # No I/O/Q in real VINs.


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


def _whitelist():
    return {e.strip().lower() for e in os.environ.get("PRO_WHITELIST", "").split(",") if e.strip()}


def _bearer(headers):
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    return auth[7:].strip() if auth.lower().startswith("bearer ") else ""


def _session_email(r, token):
    if not r or not token:
        return None
    try:
        return r.get("session:" + token) or None
    except Exception:
        return None


def _tier(email, r):
    if email in _whitelist():
        return "pro"
    try:
        raw = r.get("user:" + email)
        if raw:
            rec = json.loads(raw)
            return rec.get("tier", "free")
    except Exception:
        pass
    return "free"


def _cap_for(tier):
    return PRO_VEHICLE_CAP if tier == "pro" else FREE_VEHICLE_CAP


def _load_vehicles(r, email):
    try:
        raw = r.get("user_vehicles:" + email)
        if not raw:
            return []
        return json.loads(raw)
    except Exception:
        return []


def _save_vehicles(r, email, vehicles):
    r.set("user_vehicles:" + email, json.dumps(vehicles))


def _mileage_map(r, email, vehicles):
    out = {}
    for v in vehicles:
        vid = v.get("id")
        if vid is None and not v.get("vin"):
            continue
        key = "user_mileage:%s:%s" % (email, vid if vid is not None else "vin-" + v["vin"])
        try:
            m = r.get(key)
            if m is not None:
                out[str(vid if vid is not None else "vin-" + v["vin"])] = int(m)
        except Exception:
            continue
    return out


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return self._send(400, {"ok": False, "error": "Invalid JSON."})

        r = _redis()
        if r is None:
            return self._send(503, {"ok": False, "error": "Garage backend not configured."})

        token = _bearer(self.headers) or str(body.get("token") or "")
        email = _session_email(r, token)
        if not email:
            return self._send(401, {"ok": False, "error": "Sign in required."})

        action = str(body.get("action") or "").strip().lower()
        tier = _tier(email, r)

        if action == "list":
            return self._list(r, email, tier)
        if action == "add":
            return self._add(r, email, tier, body.get("vehicle") or {})
        if action == "remove":
            return self._remove(r, email, tier, body.get("vehicle_id"))
        if action == "mileage":
            return self._mileage(r, email, body.get("vehicle_id"), body.get("mileage"))
        return self._send(400, {"ok": False, "error": "Unknown action."})

    def _list(self, r, email, tier):
        vehicles = _load_vehicles(r, email)
        return self._send(200, {
            "ok": True, "tier": tier, "cap": _cap_for(tier),
            "vehicles": vehicles, "mileage": _mileage_map(r, email, vehicles)})

    def _add(self, r, email, tier, vehicle):
        cap = _cap_for(tier)
        if cap <= 0:
            return self._send(402, {"ok": False, "error": "My Garage is a Pro feature. Upgrade to save vehicles."})

        # Normalize the record. id may be None (VIN-only); year/make/model are required if no VIN.
        vin = str(vehicle.get("vin") or "").strip().upper()
        if vin and not VIN_RE.match(vin):
            return self._send(400, {"ok": False, "error": "Invalid VIN format (17 chars, no I/O/Q)."})
        try:
            vid = int(vehicle["id"]) if vehicle.get("id") not in (None, "") else None
        except Exception:
            vid = None
        year = vehicle.get("year")
        make = (vehicle.get("make") or "").strip()
        model = (vehicle.get("model") or "").strip()
        if vid is None and not (year and make and model):
            return self._send(400, {"ok": False, "error": "Need a vehicle id or year+make+model."})

        vehicles = _load_vehicles(r, email)
        # De-dupe: same id, or same VIN.
        for v in vehicles:
            if vid is not None and v.get("id") == vid:
                return self._send(409, {"ok": False, "error": "That vehicle is already in your garage."})
            if vin and v.get("vin") == vin:
                return self._send(409, {"ok": False, "error": "That VIN is already in your garage."})
        if len(vehicles) >= cap:
            return self._send(402, {"ok": False, "error": "Garage is full (%d of %d). Remove one to add another." % (len(vehicles), cap)})

        rec = {
            "id": vid, "year": year, "make": make, "model": model,
            "engine": vehicle.get("engine") or None, "trim": vehicle.get("trim") or None,
            "vin": vin or None, "added_at": int(time.time()),
        }
        vehicles.append(rec)
        try:
            _save_vehicles(r, email, vehicles)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not save your garage."})
        return self._send(200, {"ok": True, "vehicles": vehicles, "mileage": _mileage_map(r, email, vehicles)})

    def _remove(self, r, email, tier, vehicle_id):
        try:
            vid = int(vehicle_id)
        except Exception:
            vid = vehicle_id  # might be a vin-prefixed key for vin-only saves
        vehicles = _load_vehicles(r, email)
        before = len(vehicles)
        vehicles = [v for v in vehicles if v.get("id") != vid and v.get("vin") != vid]
        if len(vehicles) == before:
            return self._send(404, {"ok": False, "error": "Vehicle not in garage."})
        try:
            _save_vehicles(r, email, vehicles)
            r.delete("user_mileage:%s:%s" % (email, vid))
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not update your garage."})
        return self._send(200, {"ok": True, "vehicles": vehicles, "mileage": _mileage_map(r, email, vehicles)})

    def _mileage(self, r, email, vehicle_id, mileage):
        try:
            mi = int(mileage)
        except Exception:
            return self._send(400, {"ok": False, "error": "Mileage must be a number."})
        if mi < 0 or mi > 1_500_000:
            return self._send(400, {"ok": False, "error": "Mileage out of plausible range."})
        try:
            vid = int(vehicle_id)
            key = "user_mileage:%s:%s" % (email, vid)
        except Exception:
            key = "user_mileage:%s:%s" % (email, str(vehicle_id))
        try:
            r.set(key, str(mi))
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not save mileage."})
        return self._send(200, {"ok": True, "mileage": mi})

    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return
