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

Free tier (signed in): 2 saved vehicles. Pro tier: 5 saved vehicles.
Saving is a free-with-account benefit (not Pro-gated); Pro raises the cap 2 -> 5.
"""

try:  # Sentry server-side error monitoring (F-D3); inert until SENTRY_DSN is set
    import os as _os, sentry_sdk as _sentry; _sentry.init(dsn=_os.environ.get("SENTRY_DSN"))
except Exception: pass

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import time

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

PRO_VEHICLE_CAP = 5
FREE_VEHICLE_CAP = 2
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


def _is_pro(r, email):
    """Canonical email-based Pro model, identical to expenses.py / service-log.py /
    the paid AI-endpoint gate: PRO_WHITELIST, then sub:{email} cache, then user record
    tier, then live Stripe (cached back). Copy-pasted per endpoint because Vercel's
    Python builder bundles only the entry file, so a shared import fails silently."""
    if email in _whitelist():
        return True
    try:
        v = r.get("sub:" + email)
        if v == "active":
            return True
        if v == "inactive":
            return False
    except Exception:
        pass
    try:
        raw = r.get("user:" + email)
        if raw and json.loads(raw).get("tier") == "pro":
            return True
    except Exception:
        pass
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if key:
        try:
            import stripe
            stripe.api_key = key
            for c in stripe.Customer.list(email=email, limit=20).data:
                for status in ("active", "trialing"):
                    if stripe.Subscription.list(customer=c.id, status=status, limit=1).data:
                        try:
                            r.set("sub:" + email, "active", ex=60 * 60 * 6)
                        except Exception:
                            pass
                        return True
            try:
                r.set("sub:" + email, "inactive", ex=60 * 30)
            except Exception:
                pass
        except Exception:
            pass
    return False


def _tier(email, r):
    # Garage cap must follow the SAME entitlement as every other paid feature.
    # This previously checked only the whitelist + user:{email}.tier, but the Stripe
    # webhook writes sub:{email} and NEVER user.tier -- so a paying subscriber was
    # wrongly capped at the free limit (2). Delegate to the canonical _is_pro chain
    # (which consults sub:{email} + live Stripe). 2026-07-11 audit P1-5.
    return "pro" if _is_pro(r, email) else "free"


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
        # Pro entitlement (_tier -> _is_pro, which can hit live Stripe on a sub: cache
        # miss) is resolved LAZILY inside the handlers that use it (list, add), so
        # remove/mileage never pay for a billing lookup they don't need -- matching the
        # expenses.py / service-log.py pattern.
        if action == "list":
            return self._list(r, email)
        if action == "add":
            return self._add(r, email, body.get("vehicle") or {})
        if action == "remove":
            return self._remove(r, email, body.get("vehicle_id"))
        if action == "mileage":
            return self._mileage(r, email, body.get("vehicle_id"), body.get("mileage"))
        return self._send(400, {"ok": False, "error": "Unknown action."})

    def _list(self, r, email):
        tier = _tier(email, r)
        vehicles = _load_vehicles(r, email)
        return self._send(200, {
            "ok": True, "tier": tier, "cap": _cap_for(tier),
            "vehicles": vehicles, "mileage": _mileage_map(r, email, vehicles)})

    def _add(self, r, email, vehicle):
        tier = _tier(email, r)
        cap = _cap_for(tier)
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
            if tier != "pro":
                return self._send(402, {"ok": False, "error": "Upgrade to Pro to save up to %d vehicles →" % PRO_VEHICLE_CAP})
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

    def _remove(self, r, email, vehicle_id):
        try:
            vid = int(vehicle_id)
        except Exception:
            vid = vehicle_id  # might be a bare VIN for vin-only saves
        vehicles = _load_vehicles(r, email)
        removed = [v for v in vehicles if v.get("id") == vid or v.get("vin") == vid]
        if not removed:
            return self._send(404, {"ok": False, "error": "Vehicle not in garage."})
        kept = [v for v in vehicles if v.get("id") != vid and v.get("vin") != vid]
        try:
            _save_vehicles(r, email, kept)
            # Delete each removed record's mileage key, mirroring _mileage_map's key shape
            # (int id -> "<id>", vin-only -> "vin-<VIN>") so no orphaned key is left behind.
            for v in removed:
                mk = v.get("id") if v.get("id") is not None else ("vin-" + v["vin"] if v.get("vin") else None)
                if mk is not None:
                    r.delete("user_mileage:%s:%s" % (email, mk))
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not update your garage."})
        return self._send(200, {"ok": True, "vehicles": kept, "mileage": _mileage_map(r, email, kept)})

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
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return
