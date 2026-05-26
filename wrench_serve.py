"""
WRENCH — Local demo server + VIN decode proxy
=============================================
The Vehicle Finder API sends no CORS headers and requires the X-API-Key
header, so a browser cannot call it directly (a file:// demo or any page is
blocked). This tiny stdlib server fixes both problems:

  * Serves wrench_demo.html at  http://localhost:8000/
  * Proxies  GET /api/vin/<vin>  ->  https://api.vehicle-finder.com/v1/vin/<vin>
    server-side, so the API KEY stays here (never shipped to the browser) and
    the demo's JS calls a same-origin URL (no CORS).
  * OBD-II (ELM327 over Bluetooth/USB) endpoints via the python-obd library:
        GET /api/obd/status               adapter / connection state
        GET /api/obd/connect[?port=COM5]  connect to the adapter
        GET /api/obd/dtcs                 active + pending codes, enriched from dtc_codes
        GET /api/obd/live                 RPM, speed, coolant, throttle, fuel, load, intake, MAF
        GET /api/obd/clear?confirm=yes    clear stored codes (confirmation required)
    These degrade gracefully if python-obd isn't installed or no adapter is found.

Run:  python wrench_serve.py     (then open http://localhost:8000/)
Deps: pip install obd   (only needed for the OBD-II features; VIN/serving are stdlib)
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import sqlite3
import threading
import logging
import datetime
import json
import os
import re

try:
    import obd
    obd.logger.setLevel(logging.CRITICAL)      # the library is very chatty otherwise
    OBD_AVAILABLE = True
except Exception:
    OBD_AVAILABLE = False

BASE_URL = "https://api.vehicle-finder.com/v1"
PORT     = 8000
ROOT     = os.path.dirname(os.path.abspath(__file__))
DB_FILE  = os.path.join(ROOT, "wrench_vehicles.db")


def _load_config():
    """API keys live in wrench_config.json (not hardcoded). Returns {} if absent."""
    try:
        with open(os.path.join(ROOT, "wrench_config.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: could not read wrench_config.json ({e}) -- API features disabled")
        return {}


CONFIG   = _load_config()
API_KEY  = CONFIG.get("vehicle_finder_api_key", "")   # VIN proxy key
YT_KEY   = CONFIG.get("youtube_api_key", "")           # YouTube Data API v3 key
ANTHROPIC_KEY = CONFIG.get("anthropic_api_key", "")    # Claude API key (repair guides)
YT_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YT_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GUIDE_MODEL = "claude-sonnet-4-6"   # user-requested claude-sonnet-4-20250514 is retired (404); 4-6 is current Sonnet

# Services we will NOT auto-generate guides for (no verified specs in the DB).
SAFETY_CRITICAL = ("brake", "suspension", "fuel pump", "fuel system", "airbag",
                   "timing belt", "timing chain", "steering", "clutch")

GUIDE_SYSTEM = (
    "You are an expert auto mechanic writing a concise DIY guide for a home mechanic. "
    "Follow these rules strictly:\n"
    "- Use ONLY the exact specifications provided in the user message. NEVER invent, guess, "
    "or recall from memory any torque value, fluid capacity, fluid type, part number, socket "
    "size, or gap. If a number needed for a step was not provided, write \"check your factory "
    "service manual\" instead of a value.\n"
    "- Begin with a one-line intro, then a \"## Safety\" section (jack stands not just a jack, "
    "gloves, hot engine/fluids, disconnect the battery when relevant).\n"
    "- Then a \"## Steps\" numbered list, then a \"## Specs\" recap listing only the provided values.\n"
    "- Use markdown: ## for section headings, a numbered list for steps, and a simple bullet "
    "list for the Specs recap. Do NOT use tables or horizontal-rule lines. Use **bold** for key "
    "values. Keep it practical and under ~400 words.\n"
    "- Only cover the single named service. Do not branch into other repairs."
)

# ── identify-part (vision) cost controls ─────────────────────────────────────
IDP_MODEL            = "claude-sonnet-4-6"        # vision-capable
IDP_DAILY_CAP        = 100                        # scans/day total
IDP_PER_IP_DAILY     = 3                          # scans/day per IP
IDP_MAX_IMAGE_BYTES  = 2 * 1024 * 1024            # 2 MB
IDP_DAILY_ALERT_USD  = 1.50                       # write cost_alert.log at/above this
IDP_MONTHLY_BUDGET   = 50.0                        # disable endpoint above this
IDP_IN_RATE          = 3.0 / 1_000_000            # $3 / 1M input tokens
IDP_OUT_RATE         = 15.0 / 1_000_000           # $15 / 1M output tokens
COST_ALERT_LOG       = os.path.join(ROOT, "cost_alert.log")
IDP_DISABLED_FLAG    = os.path.join(ROOT, "identify_part_disabled.flag")
IDP_OK_MEDIA         = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _cost_alert(msg):
    line = f"{datetime.datetime.now().isoformat()} {msg}"
    try:
        with open(COST_ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print("COST ALERT:", msg)


def _client_ip(handler):
    xff = handler.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return handler.client_address[0]


def _claude_vision(image_b64, media_type):
    """Returns (text, usage_dict). Raises on HTTP error."""
    import base64  # noqa (image_b64 already base64 str)
    body = json.dumps({
        "model": IDP_MODEL, "max_tokens": 400,
        "system": ("You are an expert auto-parts identifier. Identify the automotive part in the "
                   "image: its common name, what it does, and any markings/part numbers actually "
                   "visible in the image. Be concise (under 150 words). Never invent a part number "
                   "that is not visibly printed. If the image is not a car part, say so plainly."),
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
            {"type": "text", "text": "What automotive part is this?"}]}],
    }).encode("utf-8")
    req = urllib.request.Request(ANTHROPIC_URL, data=body, method="POST", headers={
        "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()
    return text, d.get("usage", {"input_tokens": 0, "output_tokens": 0})
VIN_RE   = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")        # standard VIN charset (no I,O,Q)

# OBD live-data PIDs -> (python-obd command name, display unit)
OBD_LIVE = {
    "rpm":          ("RPM", "rpm"),
    "speed":        ("SPEED", "km/h"),
    "coolant_temp": ("COOLANT_TEMP", "°C"),
    "throttle":     ("THROTTLE_POS", "%"),
    "fuel_level":   ("FUEL_LEVEL", "%"),
    "engine_load":  ("ENGINE_LOAD", "%"),
    "intake_temp":  ("INTAKE_TEMP", "°C"),
    "maf":          ("MAF", "g/s"),
}

_obd_conn = None                 # the live OBD connection (created on /connect)
_obd_lock = threading.Lock()     # python-obd queries must be serialized over the link


def _obd_value(resp):
    """Pint Quantity -> plain float (rounded), or None when unavailable."""
    if resp is None or resp.is_null():
        return None
    v = resp.value
    try:
        return round(float(v.magnitude), 1)
    except AttributeError:
        try:
            return round(float(v), 1)
        except (TypeError, ValueError):
            return str(v)


def _enrich_dtcs(codes):
    """Attach description/urgency/cost from our dtc_codes table to each code."""
    out = []
    try:
        con = sqlite3.connect(DB_FILE)
        con.execute("PRAGMA busy_timeout=4000")
    except Exception:
        con = None
    for item in codes:
        code = item[0] if isinstance(item, (list, tuple)) else str(item)
        obd_desc = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else None
        row = None
        if con is not None:
            row = con.execute(
                "SELECT description,urgency,cost_low,cost_high,possible_causes FROM dtc_codes WHERE code=?",
                (code,)).fetchone()
        if row:
            desc, urg, clo, chi, causes = row
        else:
            desc, urg, clo, chi, causes = obd_desc, None, None, None, None
        try:
            causes = json.loads(causes) if causes else []
        except Exception:
            causes = []
        out.append({"code": code, "description": desc or obd_desc, "urgency": urg,
                    "cost_low": clo, "cost_high": chi, "possible_causes": causes,
                    "in_db": bool(row)})
    if con is not None:
        con.close()
    return out


# ── YouTube helpers ──────────────────────────────────────────────────────────

def _yt_get(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=20) as r:
        return json.loads(r.read())


def _yt_duration(iso):
    """ISO-8601 (PT#H#M#S) -> 'H:MM:SS' or 'M:SS'."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return ""
    h, mn, s = (int(x) if x else 0 for x in m.groups())
    return f"{h}:{mn:02d}:{s:02d}" if h else f"{mn}:{s:02d}"


def yt_search(year, make, model, service):
    """Top 3 DIY videos with stats. Returns list of dicts; raises on HTTP error."""
    q = f"{year} {make} {model} {service} DIY how to"
    sr = _yt_get(YT_SEARCH, {"part": "snippet", "type": "video",
                             "maxResults": 3, "q": q, "key": YT_KEY})
    items = sr.get("items", [])
    ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
    stats = {}
    if ids:
        dv = _yt_get(YT_VIDEOS, {"part": "statistics,contentDetails",
                                 "id": ",".join(ids), "key": YT_KEY})
        for it in dv.get("items", []):
            stats[it["id"]] = {
                "views": int(it.get("statistics", {}).get("viewCount", 0) or 0),
                "duration": _yt_duration(it.get("contentDetails", {}).get("duration", "")),
            }
    out = []
    for it in items:
        vid = it["id"].get("videoId")
        if not vid:
            continue
        sn = it.get("snippet", {})
        th = sn.get("thumbnails", {})
        thumb = (th.get("medium") or th.get("high") or th.get("default") or {}).get("url")
        st = stats.get(vid, {})
        out.append({"id": vid, "title": sn.get("title"), "channel": sn.get("channelTitle"),
                    "views": st.get("views"), "thumbnail": thumb, "duration": st.get("duration")})
    return out


# ── Repair-guide helpers (Claude) ─────────────────────────────────────────────

def _claude(system, user, max_tokens=1400):
    body = json.dumps({"model": GUIDE_MODEL, "max_tokens": max_tokens,
                       "system": system, "messages": [{"role": "user", "content": user}]}).encode("utf-8")
    req = urllib.request.Request(ANTHROPIC_URL, data=body, method="POST", headers={
        "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()


def _first(jsonstr):
    try:
        a = json.loads(jsonstr) if jsonstr else []
        return a[0] if isinstance(a, list) and a else None
    except Exception:
        return None


def guide_specs(con, vid, service):
    """Gather only the REAL specs relevant to this service. Returns (label, {spec: value})."""
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    v = cur.execute("SELECT year,make,model,engine FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not v:
        return None, {}
    label = f"{v['year']} {v['make']} {v['model']}" + (f" ({v['engine']})" if v['engine'] else "")
    tq = {r['component']: (r['torque_ft_lbs'], r['torque_nm'])
          for r in cur.execute("SELECT component,torque_ft_lbs,torque_nm FROM torque_specs WHERE vehicle_id=?", (vid,))}

    def torque(comp):
        if comp in tq and tq[comp][0] is not None:
            ft, nm = tq[comp]
            return f"{ft} ft-lb" + (f" ({nm} Nm)" if nm else "")
        return None

    o = cur.execute("SELECT * FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
    p = cur.execute("SELECT * FROM parts WHERE vehicle_id=?", (vid,)).fetchone()
    s = service.lower()
    spec = {}
    if "oil" in s:
        if o:
            if o["viscosity"]: spec["Oil viscosity"] = o["viscosity"]
            if o["oil_type"]: spec["Oil type"] = o["oil_type"]
            if o["capacity_with_filter"]: spec["Oil capacity (with filter)"] = f"{o['capacity_with_filter']} qt"
            if o["oem_spec"]: spec["OEM oil spec"] = o["oem_spec"]
            db = _first(o["drain_bolt_json"])
            if db:
                if db.get("socket_size_mm"): spec["Drain plug socket"] = f"{db['socket_size_mm']} mm"
                if db.get("thread_size"): spec["Drain plug thread"] = db["thread_size"]
                if db.get("gasket_type"): spec["Drain gasket"] = db["gasket_type"]
            of = _first(o["filters_json"])
            if of and of.get("part_number"): spec["Oil filter"] = f"{of.get('brand','')} {of['part_number']}".strip()
        if torque("drain_bolt"): spec["Drain plug torque"] = torque("drain_bolt")
    elif "spark" in s:
        sp = _first(p["spark_plugs_json"]) if p else None
        if sp and sp.get("part_number"): spec["Spark plug"] = f"{sp.get('brand','')} {sp['part_number']}".strip()
        if p and p["spark_plug_gap"]: spec["Plug gap"] = p["spark_plug_gap"]
        if p and p["spark_plug_qty"]: spec["Plug count"] = p["spark_plug_qty"]
        if torque("spark_plug"): spec["Spark plug torque"] = torque("spark_plug")
    elif "air filter" in s:
        af = _first(p["air_filters_json"]) if p else None
        if af and af.get("part_number"): spec["Air filter"] = f"{af.get('brand','')} {af['part_number']}".strip()
        if af and af.get("change_interval_miles"): spec["Change interval"] = f"{af['change_interval_miles']} mi"
    elif "cabin" in s:
        cf = _first(p["cabin_filters_json"]) if p else None
        if cf and cf.get("part_number"): spec["Cabin filter"] = f"{cf.get('brand','')} {cf['part_number']}".strip()
    elif "tire" in s:
        if torque("lug_nut"): spec["Lug nut torque"] = torque("lug_nut")
        if p and p["tire_size"]: spec["Tire size"] = p["tire_size"]
        if p and p["tire_pressure_front"]: spec["Tire pressure (front)"] = f"{p['tire_pressure_front']} psi"
        if p and p["tire_pressure_rear"]: spec["Tire pressure (rear)"] = f"{p['tire_pressure_rear']} psi"
    elif "battery" in s:
        if p and p["battery_group"]: spec["Battery group size"] = p["battery_group"]
        if p and p["battery_cca"]: spec["Battery CCA"] = p["battery_cca"]
        bt = _first(p["batteries_json"]) if p else None
        if bt and bt.get("part_number"): spec["Battery"] = f"{bt.get('brand','')} {bt['part_number']}".strip()
    elif "wiper" in s:
        try:
            wp = json.loads(p["wiper_blades_json"]) if (p and p["wiper_blades_json"]) else []
        except Exception:
            wp = []
        for w in (wp or [])[:3]:
            if w.get("size_inches"):
                spec[f"Wiper blade ({w.get('position','')})".replace(" ()", "")] = f"{w['size_inches']} in"
    return label, spec


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/vin/"):
            return self._decode_vin(self.path[len("/api/vin/"):])
        if self.path.startswith("/api/recalls"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self._recalls((q.get("make") or [""])[0], (q.get("model") or [""])[0],
                                 (q.get("year") or q.get("modelYear") or [""])[0])
        if self.path.startswith("/api/youtube/"):
            parsed = urllib.parse.urlparse(self.path)
            parts = [urllib.parse.unquote(p) for p in parsed.path[len("/api/youtube/"):].split("/") if p != ""]
            if len(parts) >= 4:
                return self._youtube(parts[0], parts[1], parts[2], parts[3])
            return self._json(400, {"error": "usage: /api/youtube/{year}/{make}/{model}/{service}"})
        if self.path.startswith("/api/guide/"):
            parsed = urllib.parse.urlparse(self.path)
            parts = [urllib.parse.unquote(p) for p in parsed.path[len("/api/guide/"):].split("/") if p != ""]
            if len(parts) >= 2:
                return self._guide(parts[0], parts[1])
            return self._json(400, {"error": "usage: /api/guide/{vehicle_id}/{service}"})
        if self.path.startswith("/api/obd/"):
            parsed = urllib.parse.urlparse(self.path)
            action = parsed.path[len("/api/obd/"):]
            q = urllib.parse.parse_qs(parsed.query)
            if action == "status":  return self._obd_status()
            if action == "connect": return self._obd_connect((q.get("port") or [None])[0])
            if action == "dtcs":    return self._obd_dtcs()
            if action == "live":    return self._obd_live()
            if action == "clear":   return self._obd_clear((q.get("confirm") or [""])[0])
            return self._json(404, {"error": "unknown OBD action"})
        if self.path == "/" or self.path == "":
            self.path = "/wrench_demo.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/identify-part":
            return self._identify_part()
        return self._json(404, {"error": "not found"})

    # ── identify-part (vision) with cost controls ────────────────────────────
    def _identify_part(self):
        if not ANTHROPIC_KEY:
            return self._json(503, {"error": "No Anthropic API key configured."})
        # (1) monthly budget kill-switch -- fail closed
        if os.path.exists(IDP_DISABLED_FLAG):
            return self._json(503, {"error": "identify-part is disabled (monthly budget exceeded)."})
        ip = _client_ip(self)
        now = datetime.datetime.now()
        today, month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
        con = sqlite3.connect(DB_FILE)
        con.execute("PRAGMA busy_timeout=8000")
        con.execute("""CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ip TEXT, tokens_used INTEGER,
            estimated_cost REAL, running_daily_total REAL, running_monthly_total REAL)""")
        # (2) global daily cap  (3) per-IP daily limit  (4) image size -- all BEFORE any paid call
        daily_n = con.execute("SELECT COUNT(*) FROM api_usage WHERE substr(ts,1,10)=?", (today,)).fetchone()[0]
        if daily_n >= IDP_DAILY_CAP:
            con.close()
            return self._json(429, {"error": f"Daily scan cap reached ({IDP_DAILY_CAP}/day)."})
        ip_n = con.execute("SELECT COUNT(*) FROM api_usage WHERE substr(ts,1,10)=? AND ip=?", (today, ip)).fetchone()[0]
        if ip_n >= IDP_PER_IP_DAILY:
            con.close()
            return self._json(429, {"error": f"Per-IP daily limit reached ({IDP_PER_IP_DAILY}/day)."})
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length <= 0:
            con.close()
            return self._json(400, {"error": "POST an image in the request body."})
        if length > IDP_MAX_IMAGE_BYTES:
            # drain a bounded amount of the rejected upload so the client gets a clean 413
            try:
                remaining = min(length, 5 * 1024 * 1024)
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
            except Exception:
                pass
            con.close()
            return self._json(413, {"error": "Image exceeds the 2 MB limit."})
        media = (self.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip().lower()
        if media not in IDP_OK_MEDIA:
            media = "image/jpeg"
        image_bytes = self.rfile.read(length)
        if len(image_bytes) > IDP_MAX_IMAGE_BYTES:
            con.close()
            return self._json(413, {"error": "Image exceeds the 2 MB limit."})
        # (5) paid vision call -- only reached after every gate passes
        import base64
        b64 = base64.b64encode(image_bytes).decode("ascii")
        try:
            text, usage = _claude_vision(b64, media)
        except urllib.error.HTTPError as e:
            con.close()
            return self._json(200, {"identification": None, "error": f"Vision API error {e.code}."})
        except Exception as e:
            con.close()
            return self._json(200, {"identification": None, "error": f"Vision request failed: {e}"})
        in_tok = int(usage.get("input_tokens", 0) or 0)
        out_tok = int(usage.get("output_tokens", 0) or 0)
        tokens_used = in_tok + out_tok
        cost = in_tok * IDP_IN_RATE + out_tok * IDP_OUT_RATE
        # (6) running totals + log
        prev_day = con.execute("SELECT COALESCE(SUM(estimated_cost),0) FROM api_usage WHERE substr(ts,1,10)=?", (today,)).fetchone()[0]
        prev_month = con.execute("SELECT COALESCE(SUM(estimated_cost),0) FROM api_usage WHERE substr(ts,1,7)=?", (month,)).fetchone()[0]
        daily_total, monthly_total = prev_day + cost, prev_month + cost
        con.execute("INSERT INTO api_usage (ts,ip,tokens_used,estimated_cost,running_daily_total,running_monthly_total) VALUES (?,?,?,?,?,?)",
                    (now.isoformat(), ip, tokens_used, cost, daily_total, monthly_total))
        con.commit()
        con.close()
        # daily spend alert (log once, when the threshold is first crossed today)
        if prev_day < IDP_DAILY_ALERT_USD <= daily_total:
            _cost_alert(f"Daily spend alert: ${daily_total:.2f} reached threshold ${IDP_DAILY_ALERT_USD:.2f} (identify-part)")
        # monthly budget -> disable
        if monthly_total > IDP_MONTHLY_BUDGET:
            try:
                with open(IDP_DISABLED_FLAG, "w", encoding="utf-8") as f:
                    f.write(now.isoformat())
            except Exception:
                pass
            _cost_alert("Monthly budget exceeded — identify-part disabled")
        return self._json(200, {"identification": text, "tokens_used": tokens_used,
                                "estimated_cost": round(cost, 4),
                                "daily_total": round(daily_total, 4),
                                "monthly_total": round(monthly_total, 4)})

    # ── YouTube handler ──────────────────────────────────────────────────────
    def _youtube(self, year, make, model, service):
        if not YT_KEY:
            return self._json(200, {"videos": [],
                                    "error": "No YouTube API key configured in wrench_config.json."})
        cache_key = f"{year}|{make}|{model}|{service}".lower()
        con = sqlite3.connect(DB_FILE)
        con.execute("PRAGMA busy_timeout=8000")
        con.execute("""CREATE TABLE IF NOT EXISTS youtube_cache (
            cache_key TEXT PRIMARY KEY, payload TEXT, fetched_at TEXT)""")
        row = con.execute("SELECT payload, fetched_at FROM youtube_cache WHERE cache_key=?",
                          (cache_key,)).fetchone()
        if row:
            try:
                age = datetime.datetime.now() - datetime.datetime.fromisoformat(row[1])
                if age.days < 30:
                    con.close()
                    return self._json(200, {"videos": json.loads(row[0]), "cached": True})
            except Exception:
                pass
        try:
            videos = yt_search(year, make, model, service)
        except urllib.error.HTTPError as e:
            con.close()
            msg = ("YouTube daily quota exceeded (resets at midnight Pacific)."
                   if e.code == 403 else f"YouTube API error {e.code}.")
            return self._json(200, {"videos": [], "error": msg})
        except Exception as e:
            con.close()
            return self._json(200, {"videos": [], "error": f"YouTube request failed: {e}"})
        con.execute("INSERT OR REPLACE INTO youtube_cache VALUES (?,?,?)",
                    (cache_key, json.dumps(videos), datetime.datetime.now().isoformat()))
        con.commit()
        con.close()
        return self._json(200, {"videos": videos, "cached": False})

    # ── Repair-guide handler ─────────────────────────────────────────────────
    def _guide(self, vehicle_id, service):
        if not ANTHROPIC_KEY:
            return self._json(200, {"guide": None,
                                    "error": "No Anthropic API key configured in wrench_config.json."})
        try:
            vid = int(vehicle_id)
        except ValueError:
            return self._json(400, {"error": "vehicle_id must be an integer"})
        cache_key = f"{vid}|{service}".lower()
        con = sqlite3.connect(DB_FILE)
        con.execute("PRAGMA busy_timeout=8000")
        con.execute("""CREATE TABLE IF NOT EXISTS guides_cache (
            cache_key TEXT PRIMARY KEY, payload TEXT, fetched_at TEXT)""")
        row = con.execute("SELECT payload, fetched_at FROM guides_cache WHERE cache_key=?",
                          (cache_key,)).fetchone()
        if row:
            try:
                if (datetime.datetime.now() - datetime.datetime.fromisoformat(row[1])).days < 90:
                    con.close()
                    return self._json(200, {**json.loads(row[0]), "cached": True})
            except Exception:
                pass

        label, spec = guide_specs(con, vid, service)
        if label is None:
            con.close()
            return self._json(404, {"error": "vehicle not found"})

        # Safety-critical services: we have no verified specs -> do NOT generate a guide.
        if any(k in service.lower() for k in SAFETY_CRITICAL):
            payload = {"guide": None, "safety_blocked": True, "label": label,
                       "message": (f"{service.title()} is safety-critical and we don't have verified "
                                   "torque/procedure specs for this vehicle. Get the exact figures from the "
                                   "factory service manual, or have a professional do it — incorrect fastener "
                                   "torque here can cause failure.")}
            con.execute("INSERT OR REPLACE INTO guides_cache VALUES (?,?,?)",
                        (cache_key, json.dumps(payload), datetime.datetime.now().isoformat()))
            con.commit()
            con.close()
            return self._json(200, {**payload, "cached": False})

        speclines = "\n".join(f"- {k}: {val}" for k, val in spec.items()) or \
            "(no specs available in our database for this service)"
        user = (f"Vehicle: {label}\nService: {service}\n\n"
                f"Known specs (use these EXACT values; invent nothing else):\n{speclines}\n\n"
                "Write the DIY guide.")
        try:
            guide = _claude(GUIDE_SYSTEM, user)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            con.close()
            return self._json(200, {"guide": None, "error": f"Claude API error {e.code}. {detail}"})
        except Exception as e:
            con.close()
            return self._json(200, {"guide": None, "error": f"Guide generation failed: {e}"})

        payload = {"guide": guide, "label": label, "specs": spec, "safety_blocked": False}
        con.execute("INSERT OR REPLACE INTO guides_cache VALUES (?,?,?)",
                    (cache_key, json.dumps(payload), datetime.datetime.now().isoformat()))
        con.commit()
        con.close()
        return self._json(200, {**payload, "cached": False})

    # ── OBD-II handlers ──────────────────────────────────────────────────────
    def _obd_status(self):
        if not OBD_AVAILABLE:
            return self._json(200, {"available": False, "connected": False,
                                    "message": "python-obd not installed on the server. Run: pip install obd"})
        with _obd_lock:
            connected = bool(_obd_conn and _obd_conn.is_connected())
            status = str(_obd_conn.status()) if _obd_conn else "Not Connected"
        return self._json(200, {"available": True, "connected": connected, "status": status})

    def _obd_connect(self, port):
        global _obd_conn
        if not OBD_AVAILABLE:
            return self._json(200, {"available": False, "connected": False,
                                    "error": "python-obd not installed. Run: pip install obd"})
        with _obd_lock:
            try:
                if _obd_conn:
                    try: _obd_conn.close()
                    except Exception: pass
                _obd_conn = obd.OBD(port) if port else obd.OBD()
                connected = _obd_conn.is_connected()
                try: pname = _obd_conn.port_name()
                except Exception: pname = None
                if not connected:
                    return self._json(200, {"available": True, "connected": False,
                                            "status": str(_obd_conn.status()),
                                            "error": "No ELM327 adapter responded. Pair the adapter (it shows up as a COM port) and try again, or target it directly: /api/obd/connect?port=COM5"})
                return self._json(200, {"available": True, "connected": True,
                                        "status": str(_obd_conn.status()), "port": pname})
            except Exception as e:
                _obd_conn = None
                return self._json(200, {"available": True, "connected": False,
                                        "error": f"Could not open adapter: {e}. Try pairing it or passing ?port=COM5."})

    def _obd_dtcs(self):
        if not OBD_AVAILABLE:
            return self._json(503, {"error": "python-obd not installed."})
        with _obd_lock:
            if not (_obd_conn and _obd_conn.is_connected()):
                return self._json(409, {"connected": False, "error": "Not connected. Call /api/obd/connect first."})
            active = _obd_conn.query(obd.commands.GET_DTC)
            pending = _obd_conn.query(obd.commands.GET_CURRENT_DTC)
        a = active.value if (active and not active.is_null()) else []
        p = pending.value if (pending and not pending.is_null()) else []
        return self._json(200, {"connected": True,
                                "active": _enrich_dtcs(a), "pending": _enrich_dtcs(p)})

    def _obd_live(self):
        if not OBD_AVAILABLE:
            return self._json(503, {"error": "python-obd not installed."})
        with _obd_lock:
            if not (_obd_conn and _obd_conn.is_connected()):
                return self._json(409, {"connected": False, "error": "Not connected."})
            data = {}
            for key, (cmd, unit) in OBD_LIVE.items():
                try:
                    resp = _obd_conn.query(getattr(obd.commands, cmd))
                    data[key] = {"value": _obd_value(resp), "unit": unit}
                except Exception:
                    data[key] = {"value": None, "unit": unit}
        return self._json(200, {"connected": True, "data": data})

    def _obd_clear(self, confirm):
        if not OBD_AVAILABLE:
            return self._json(503, {"error": "python-obd not installed."})
        if confirm != "yes":
            return self._json(400, {"cleared": False,
                                    "error": "Confirmation required. Call /api/obd/clear?confirm=yes"})
        with _obd_lock:
            if not (_obd_conn and _obd_conn.is_connected()):
                return self._json(409, {"connected": False, "error": "Not connected."})
            try:
                _obd_conn.query(obd.commands.CLEAR_DTC)
                return self._json(200, {"cleared": True})
            except Exception as e:
                return self._json(502, {"cleared": False, "error": str(e)})

    def _decode_vin(self, vin):
        vin = vin.strip().upper()
        if not VIN_RE.match(vin):
            return self._json(400, {"error": "VIN must be 17 valid characters (A-Z except I/O/Q, 0-9)."})
        req = urllib.request.Request(f"{BASE_URL}/vin/{vin}", headers={"X-API-Key": API_KEY})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                payload = json.loads(r.read())
            data = payload.get("data", payload) if isinstance(payload, dict) else payload
            return self._json(200, data)
        except urllib.error.HTTPError as e:
            msg = "VIN not found." if e.code == 404 else f"Decode service error ({e.code})."
            return self._json(e.code, {"error": msg})
        except Exception as e:
            return self._json(502, {"error": f"Could not reach decode service: {e}"})

    def _recalls(self, make, model, year):
        make, model, year = (make or "").strip(), (model or "").strip(), (year or "").strip()
        if not (make and model and year):
            return self._json(400, {"error": "make, model and year are required", "recalls": []})
        try:
            url = "https://api.nhtsa.gov/recalls/recallsByVehicle?" + urllib.parse.urlencode(
                {"make": make, "model": model, "modelYear": year})
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; KnowYourRide/1.0)", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            items = data.get("results") or data.get("Results") or data.get("recalls") or []
            return self._json(200, {"count": len(items), "recalls": items})
        except Exception as e:
            return self._json(502, {"error": f"recall lookup failed: {e}", "recalls": []})

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):          # quieter console
        if "/api/vin/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    os.chdir(ROOT)
    with Server(("", PORT), Handler) as httpd:
        print(f"WRENCH demo running:  http://localhost:{PORT}/")
        print(f"VIN proxy:            http://localhost:{PORT}/api/vin/<17-char-vin>")
        print("Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped.")
