"""
WRENCH — Final 2026 model-year pull from Vehicle Finder (before subscription cancellation).

The API has NO enumeration endpoint (/makes returns the raw NHTSA registry incl. junk;
no models-for-make listing exists; /vehicles requires year+make+model). So "all 2026
vehicles" is bounded by model names we can supply. Strategy:
  * Re-query every (make, model) the DB already tracks (362 nameplates) for YEAR=2026.
  * Plus a curated supplement of new-for-2026 / EV nameplates not yet in the DB.

Mappings match the LIVE 2026 response shapes (verified 2026-05-30):
  * parts.cabin_air_filters  (NOT the old "cabin_filters")
  * recalls: nhtsa_campaign/description  | tsb: tsb_number/description/category/date_issued
    (the corrected names from wrench_fix_ingestion.py — the old bulk scripts wrote NULLs)

Idempotent / resumable via pull_log. Writes to wrench_vehicles.db (backed up first).
Run:  python wrench_2026_final_pull.py
"""

import os, sys, io, json, time, logging, sqlite3
import requests
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_FILE  = "wrench_vehicles.db"
BASE_URL = "https://api.vehicle-finder.com/v1"
YEAR     = 2026
DELAY    = 0.25
KEY      = json.load(open("wrench_config.json", encoding="utf-8")).get("vehicle_finder_api_key", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler("wrench_2026_pull.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

ENDPOINTS = ["oil-change", "parts", "maintenance", "fluids", "torque-specs",
             "recalls", "engine-specs", "fuel-economy", "safety-ratings",
             "warranty", "reliability", "tsb", "service-costs"]

# New-for-2026 / EV nameplates that may not be in the existing DB (deduped vs DB below).
SUPPLEMENT = [
    ("Toyota","Crown"),("Toyota","Crown Signia"),("Toyota","Grand Highlander"),
    ("Toyota","Land Cruiser"),("Toyota","bZ4X"),
    ("Honda","Prologue"),("Acura","ZDX"),
    ("Hyundai","Ioniq 5"),("Hyundai","Ioniq 6"),("Hyundai","Ioniq 9"),("Hyundai","Santa Cruz"),
    ("Kia","EV6"),("Kia","EV9"),("Kia","Carnival"),
    ("Chevrolet","Equinox EV"),("Chevrolet","Blazer EV"),("Chevrolet","Silverado EV"),
    ("Cadillac","Lyriq"),("Cadillac","Optiq"),("Cadillac","Vistiq"),
    ("GMC","Hummer EV"),("GMC","Sierra EV"),
    ("Ford","Mustang Mach-E"),("Ford","F-150 Lightning"),("Ford","Maverick"),
    ("Jeep","Wagoneer"),("Jeep","Wagoneer S"),("Jeep","Recon"),
    ("Dodge","Charger Daytona"),("Dodge","Hornet"),
    ("Subaru","Solterra"),
    ("Volkswagen","ID.4"),("Volkswagen","ID. Buzz"),
    ("Nissan","Ariya"),("Nissan","Z"),
    ("BMW","i4"),("BMW","i5"),("BMW","iX"),
    ("Mercedes-Benz","EQS"),("Mercedes-Benz","EQE"),
    ("Genesis","GV60"),
    ("Polestar","2"),("Polestar","3"),
    ("Volvo","EX30"),("Volvo","EX90"),
    ("Rivian","R1T"),("Rivian","R1S"),
    ("Lucid","Air"),("Lucid","Gravity"),
    ("Tesla","Model 3"),("Tesla","Model Y"),("Tesla","Model S"),("Tesla","Model X"),("Tesla","Cybertruck"),
]

session = requests.Session()
session.headers.update({"X-API-Key": KEY})
req_count = 0


def api_get(path, params=None):
    global req_count
    try:
        r = session.get(f"{BASE_URL}/{path}", params=params, timeout=20)
        req_count += 1
        time.sleep(DELAY)
        if r.status_code == 200:
            return r.json().get("data")
        if r.status_code == 429:
            log.warning("  429 rate-limited; sleeping 15s")
            time.sleep(15)
            return api_get(path, params)
        return None          # 404/422/etc -> no data
    except Exception as e:
        log.error(f"  request error {path}: {e}")
        return None


def setup_db(conn):
    # Tables already exist in the live DB; CREATE IF NOT EXISTS keeps this self-contained.
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT, engine TEXT, trim TEXT, pulled_at TEXT);
        CREATE TABLE IF NOT EXISTS oil_change (vehicle_id INTEGER PRIMARY KEY, viscosity TEXT, oil_type TEXT, capacity_with_filter REAL, capacity_without_filter REAL, oem_spec TEXT, filters_json TEXT, drain_bolt_json TEXT);
        CREATE TABLE IF NOT EXISTS parts (vehicle_id INTEGER PRIMARY KEY, spark_plug_type TEXT, spark_plug_gap TEXT, spark_plug_qty INTEGER, battery_group TEXT, battery_cca INTEGER, tire_size TEXT, tire_pressure_front INTEGER, tire_pressure_rear INTEGER, spark_plugs_json TEXT, air_filters_json TEXT, cabin_filters_json TEXT, wiper_blades_json TEXT, batteries_json TEXT);
        CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, vehicle_id INTEGER, mileage_interval INTEGER, months_interval INTEGER, description TEXT, source TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS maintenance_parts (id INTEGER PRIMARY KEY AUTOINCREMENT, maintenance_id INTEGER, vehicle_id INTEGER, part_type TEXT, brand TEXT, part_number TEXT, description TEXT, qty INTEGER);
        CREATE TABLE IF NOT EXISTS fluids (vehicle_id INTEGER PRIMARY KEY, transmission_fluid TEXT, transmission_capacity REAL, brake_fluid TEXT, coolant_type TEXT, coolant_capacity REAL, power_steering_fluid TEXT, differential_fluids_json TEXT);
        CREATE TABLE IF NOT EXISTS torque_specs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, component TEXT, torque_ft_lbs REAL, torque_nm REAL, notes TEXT);
        CREATE TABLE IF NOT EXISTS recalls (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, campaign_number TEXT, component TEXT, summary TEXT, remedy TEXT, park_it INTEGER);
        CREATE TABLE IF NOT EXISTS engine_specs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, variant TEXT, horsepower INTEGER, torque_ft_lbs INTEGER, displacement_l REAL, cylinders INTEGER, cylinder_config TEXT, aspiration TEXT, fuel_system TEXT);
        CREATE TABLE IF NOT EXISTS fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, drive TEXT);
        CREATE TABLE IF NOT EXISTS safety_ratings (vehicle_id INTEGER PRIMARY KEY, overall_rating INTEGER, frontal_crash_driver INTEGER, frontal_crash_passenger INTEGER, side_crash_driver INTEGER, side_crash_passenger INTEGER, rollover_rating INTEGER, rollover_risk_pct REAL, side_pole_rating INTEGER);
        CREATE TABLE IF NOT EXISTS warranty (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, warranty_type TEXT, months INTEGER, miles INTEGER, notes TEXT);
        CREATE TABLE IF NOT EXISTS reliability (vehicle_id INTEGER PRIMARY KEY, overall_score REAL, rating TEXT, complaint_count INTEGER, crash_count INTEGER, fire_count INTEGER, injury_count INTEGER, top_issue TEXT);
        CREATE TABLE IF NOT EXISTS service_costs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, service_type TEXT, region TEXT, cost_low INTEGER, cost_high INTEGER, cost_average INTEGER, labor_hours_low REAL, labor_hours_high REAL);
        CREATE TABLE IF NOT EXISTS tsb (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, tsb_number TEXT, title TEXT, component TEXT, summary TEXT, date TEXT);
        CREATE TABLE IF NOT EXISTS pull_log (vehicle_id INTEGER, endpoint TEXT, status TEXT, pulled_at TEXT, PRIMARY KEY (vehicle_id, endpoint));
    """)
    conn.commit()


def save_all(conn, vid, ep, data):
    try:
        if ep == "oil-change" and isinstance(data, dict):
            s = data.get("oil_spec") or {}
            db = data.get("drain_bolt") or {}
            conn.execute(
                "INSERT OR REPLACE INTO oil_change "
                "(vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (vid, s.get("viscosity"), s.get("oil_type"), s.get("capacity_with_filter"),
                 s.get("capacity_without_filter"), s.get("oem_spec"),
                 json.dumps(data.get("filters")), json.dumps(db),
                 db.get("socket"), db.get("thread") or db.get("thread_size"),
                 db.get("gasket") or db.get("crush_washer")))
        elif ep == "parts" and isinstance(data, dict):
            sp = data.get("spark_plug_spec") or {}; bat = data.get("battery_spec") or {}; ti = data.get("tire_spec") or {}
            conn.execute(
                "INSERT OR REPLACE INTO parts "
                "(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (vid, sp.get("plug_type"), sp.get("gap"), sp.get("quantity"),
                 bat.get("group_size"), bat.get("cca"), ti.get("size"),
                 ti.get("pressure_front_psi"), ti.get("pressure_rear_psi"),
                 json.dumps(data.get("spark_plugs")), json.dumps(data.get("air_filters")),
                 json.dumps(data.get("cabin_air_filters")),     # FIXED: API key is cabin_air_filters
                 json.dumps(data.get("wiper_blades")), json.dumps(data.get("batteries"))))
        elif ep == "maintenance" and isinstance(data, dict):
            for item in (data.get("schedules") or []):
                sid = item.get("id")
                conn.execute("INSERT OR REPLACE INTO maintenance VALUES (?,?,?,?,?,?,?)",
                    (sid, vid, item.get("mileage_interval"), item.get("months_interval"),
                     item.get("description"), item.get("source"), item.get("notes")))
                if sid is not None:
                    conn.execute("DELETE FROM maintenance_parts WHERE maintenance_id=?", (sid,))
                for part in (item.get("parts") or []):
                    conn.execute("INSERT INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                        (sid, vid, part.get("part_type"), part.get("brand"), part.get("part_number"), part.get("description"), part.get("qty")))
        elif ep == "fluids" and isinstance(data, dict):
            tf = data.get("transmission_fluid") or {}; c = data.get("coolant") or {}
            conn.execute(
                "INSERT OR REPLACE INTO fluids "
                "(vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (vid, tf.get("fluid_type"), tf.get("capacity_quarts"),
                 (data.get("brake_fluid") or {}).get("dot_type"),
                 c.get("coolant_type"), c.get("capacity_quarts"),
                 (data.get("power_steering_fluid") or {}).get("fluid_type"),
                 json.dumps(data.get("differential_fluids"))))
        elif ep == "torque-specs" and isinstance(data, list):
            for t in data:
                conn.execute("INSERT OR IGNORE INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes) VALUES (?,?,?,?,?)",
                    (vid, t.get("component"), t.get("torque_ft_lbs"), t.get("torque_nm"), t.get("notes")))
        elif ep == "recalls" and isinstance(data, list):
            for r in data:                                       # FIXED field names
                conn.execute("INSERT OR IGNORE INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) VALUES (?,?,?,?,?,?)",
                    (vid, r.get("nhtsa_campaign"), r.get("component"),
                     r.get("description"), r.get("remedy"), 1 if r.get("park_it") else 0))
        elif ep == "engine-specs" and isinstance(data, list):
            for e in data:
                conn.execute("INSERT OR IGNORE INTO engine_specs (vehicle_id,variant,horsepower,torque_ft_lbs,displacement_l,cylinders,cylinder_config,aspiration,fuel_system) VALUES (?,?,?,?,?,?,?,?,?)",
                    (vid, e.get("engine_variant"), e.get("horsepower"), e.get("torque_ft_lbs"),
                     e.get("displacement_liters"), e.get("cylinders"), e.get("cylinder_config"),
                     e.get("aspiration"), e.get("fuel_system")))
        elif ep == "fuel-economy" and isinstance(data, list):
            for f in data:
                conn.execute("INSERT OR IGNORE INTO fuel_economy (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,engine,transmission,drive) VALUES (?,?,?,?,?,?,?,?)",
                    (vid, f.get("city_mpg"), f.get("highway_mpg"), f.get("combined_mpg"),
                     f.get("annual_fuel_cost"), f.get("engine_displacement"),
                     f.get("transmission"), f.get("drive")))
        elif ep == "safety-ratings" and isinstance(data, dict):
            conn.execute(
                "INSERT OR REPLACE INTO safety_ratings "
                "(vehicle_id,overall_rating,frontal_crash_driver,frontal_crash_passenger,side_crash_driver,side_crash_passenger,rollover_rating,rollover_risk_pct,side_pole_rating) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (vid, data.get("overall_rating"), data.get("frontal_crash_driver"),
                 data.get("frontal_crash_passenger"), data.get("side_crash_driver"),
                 data.get("side_crash_passenger"), data.get("rollover_rating"),
                 data.get("rollover_risk_pct"), data.get("side_pole_rating")))
        elif ep == "warranty" and isinstance(data, list):
            for w in data:
                conn.execute("INSERT OR IGNORE INTO warranty (vehicle_id,warranty_type,months,miles,notes) VALUES (?,?,?,?,?)",
                    (vid, w.get("warranty_type"), w.get("months"), w.get("miles"), w.get("notes")))
        elif ep == "reliability" and isinstance(data, dict):
            conn.execute(
                "INSERT OR REPLACE INTO reliability "
                "(vehicle_id,overall_score,rating,complaint_count,crash_count,fire_count,injury_count,top_issue) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (vid, data.get("overall_score"), data.get("rating"), data.get("complaint_count"),
                 data.get("crash_count"), data.get("fire_count"), data.get("injury_count"), data.get("top_issue")))
        elif ep == "service-costs" and isinstance(data, list):
            for s in data:
                conn.execute("INSERT OR IGNORE INTO service_costs (vehicle_id,service_type,region,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high) VALUES (?,?,?,?,?,?,?,?)",
                    (vid, s.get("service_type"), s.get("region"), s.get("cost_low"),
                     s.get("cost_high"), s.get("cost_average"), s.get("labor_hours_low"), s.get("labor_hours_high")))
        elif ep == "tsb" and isinstance(data, list):
            for t in data:                                       # FIXED field names
                conn.execute("INSERT OR IGNORE INTO tsb (vehicle_id,tsb_number,title,component,summary,date) VALUES (?,?,?,?,?,?)",
                    (vid, t.get("tsb_number"), t.get("description"), t.get("category"), None, t.get("date_issued")))
        conn.commit()
        return True
    except Exception as e:
        log.error(f"  save error [{ep}] vid={vid}: {e}")
        return False


def pull_vehicle(conn, make, model):
    existing = conn.execute("SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (YEAR, make, model)).fetchone()
    if existing:
        vid = existing[0]
        done = conn.execute("SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status IN ('ok','empty')", (vid,)).fetchone()[0]
        if done >= len(ENDPOINTS):
            return "skip"
    result = api_get("vehicles", {"year": YEAR, "make": make, "model": model})
    if not result:
        return None                                # no 2026 version of this nameplate
    vehicles = result if isinstance(result, list) else [result]
    v = next((x for x in vehicles if x.get("engine")), vehicles[0])
    vid = v["id"]

    # QUALITY GATE — the API returns a 2026 "shell" record (engine=None, only generic
    # templated maintenance/warranty) for some discontinued models (e.g. Acura ILX).
    # A genuine 2026 vehicle has an engine string (gas) OR engine-specs OR fuel-economy
    # (EVs have engine=None but real fuel-economy/MPGe). Probe before inserting; cache the
    # probe results so the endpoint loop doesn't re-fetch them.
    prefetch = {}
    if not v.get("engine"):
        prefetch["fuel-economy"] = api_get(f"vehicles/{vid}/fuel-economy")
        prefetch["engine-specs"] = api_get(f"vehicles/{vid}/engine-specs")
        if not (prefetch["fuel-economy"] or prefetch["engine-specs"]):
            log.info(f"  shell only (no engine / fuel-economy / engine-specs) -> SKIP")
            return "shell"

    conn.execute("INSERT OR IGNORE INTO vehicles (id,year,make,model,engine,trim,pulled_at) VALUES (?,?,?,?,?,?,?)",
        (vid, YEAR, make, model, v.get("engine"), v.get("trim"), datetime.now().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')} | trim={v.get('trim')}")
    for ep in ENDPOINTS:
        done = conn.execute("SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?", (vid, ep)).fetchone()
        if done and done[0] in ("ok", "empty"):
            continue
        data = prefetch[ep] if ep in prefetch else api_get(f"vehicles/{vid}/{ep}")
        if data:
            status = "ok" if save_all(conn, vid, ep, data) else "save_error"
        else:
            status = "empty"
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid, ep, status, datetime.now().isoformat()))
        conn.commit()
    return "new"


def main():
    if not KEY:
        log.error("No vehicle_finder_api_key in wrench_config.json — aborting."); return
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)

    db_models = conn.execute("SELECT DISTINCT make, model FROM vehicles WHERE model IS NOT NULL").fetchall()
    targets = {(mk, md) for (mk, md) in db_models}
    targets |= {(mk, md) for (mk, md) in SUPPLEMENT}
    targets = sorted(targets)
    log.info(f"=== 2026 FINAL PULL === {len(targets)} (make,model) targets "
             f"({len(db_models)} from DB + {len(SUPPLEMENT)} supplement, deduped)")

    found = skipped = nodata = shells = 0
    for i, (mk, md) in enumerate(targets, 1):
        log.info(f"[{i}/{len(targets)}] 2026 {mk} {md}")
        try:
            res = pull_vehicle(conn, mk, md)
        except Exception as e:
            log.error(f"  error: {e}"); res = None
        if res == "new": found += 1
        elif res == "skip": skipped += 1
        elif res == "shell": shells += 1
        else: nodata += 1
        if i % 25 == 0:
            n2026 = conn.execute("SELECT COUNT(*) FROM vehicles WHERE year=2026").fetchone()[0]
            log.info(f"  --- progress {i}/{len(targets)} | new={found} skip={skipped} shell={shells} no2026={nodata} | 2026 rows={n2026} | reqs={req_count} ---")

    n2026 = conn.execute("SELECT COUNT(*) FROM vehicles WHERE year=2026").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"=== DONE === new={found} skip={skipped} shell(skipped)={shells} no2026={nodata} | "
             f"2026 rows now={n2026} | total vehicles={total} | requests={req_count}")
    conn.close()


if __name__ == "__main__":
    main()
