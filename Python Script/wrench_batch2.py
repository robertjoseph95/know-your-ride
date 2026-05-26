import os
import requests, sqlite3, json, time, sys, logging
from datetime import datetime

# Fix Windows Unicode
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY  = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL = "https://api.vehicle-finder.com/v1"
DB_FILE  = "wrench_vehicles.db"
HEADERS  = {"X-API-Key": API_KEY}
DELAY    = 0.25

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler("wrench_log2.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

# NEW VEHICLES TO ADD - brands and years not yet in database
TARGET_VEHICLES = [
    # Acura
    (2020,"Acura","MDX"),(2021,"Acura","MDX"),(2022,"Acura","MDX"),
    (2020,"Acura","RDX"),(2021,"Acura","RDX"),(2022,"Acura","RDX"),
    (2020,"Acura","TLX"),(2021,"Acura","TLX"),(2019,"Acura","MDX"),
    (2018,"Acura","MDX"),(2018,"Acura","RDX"),
    # Lexus
    (2020,"Lexus","RX 350"),(2021,"Lexus","RX 350"),(2022,"Lexus","RX 350"),
    (2020,"Lexus","ES 350"),(2021,"Lexus","ES 350"),(2022,"Lexus","ES 350"),
    (2020,"Lexus","NX 300"),(2021,"Lexus","NX 300"),
    (2020,"Lexus","GX 460"),(2021,"Lexus","GX 460"),
    (2018,"Lexus","RX 350"),(2019,"Lexus","RX 350"),
    # Infiniti
    (2020,"Infiniti","QX60"),(2021,"Infiniti","QX60"),(2022,"Infiniti","QX60"),
    (2020,"Infiniti","QX50"),(2021,"Infiniti","QX50"),
    (2020,"Infiniti","Q50"),(2021,"Infiniti","Q50"),
    (2018,"Infiniti","QX60"),(2019,"Infiniti","QX60"),
    # Buick
    (2020,"Buick","Enclave"),(2021,"Buick","Enclave"),(2022,"Buick","Enclave"),
    (2020,"Buick","Encore"),(2021,"Buick","Encore"),
    (2020,"Buick","Envision"),(2021,"Buick","Envision"),
    # Cadillac
    (2020,"Cadillac","Escalade"),(2021,"Cadillac","Escalade"),(2022,"Cadillac","Escalade"),
    (2020,"Cadillac","XT5"),(2021,"Cadillac","XT5"),
    (2020,"Cadillac","XT4"),(2021,"Cadillac","XT4"),
    # Lincoln
    (2020,"Lincoln","Navigator"),(2021,"Lincoln","Navigator"),(2022,"Lincoln","Navigator"),
    (2020,"Lincoln","Aviator"),(2021,"Lincoln","Aviator"),
    (2020,"Lincoln","Corsair"),(2021,"Lincoln","Corsair"),
    # Mitsubishi
    (2020,"Mitsubishi","Outlander"),(2021,"Mitsubishi","Outlander"),(2022,"Mitsubishi","Outlander"),
    (2020,"Mitsubishi","Eclipse Cross"),(2021,"Mitsubishi","Eclipse Cross"),
    (2020,"Mitsubishi","Outlander Sport"),(2021,"Mitsubishi","Outlander Sport"),
    # Volvo
    (2020,"Volvo","XC90"),(2021,"Volvo","XC90"),(2022,"Volvo","XC90"),
    (2020,"Volvo","XC60"),(2021,"Volvo","XC60"),(2022,"Volvo","XC60"),
    (2020,"Volvo","XC40"),(2021,"Volvo","XC40"),
    # Genesis
    (2020,"Genesis","G80"),(2021,"Genesis","G80"),(2022,"Genesis","G80"),
    (2021,"Genesis","GV80"),(2022,"Genesis","GV80"),
    (2021,"Genesis","GV70"),(2022,"Genesis","GV70"),
    # Older popular models not yet covered
    (2018,"Toyota","Camry"),(2017,"Toyota","Camry"),(2016,"Toyota","Camry"),
    (2018,"Toyota","RAV4"),(2017,"Toyota","RAV4"),(2016,"Toyota","RAV4"),
    (2018,"Toyota","Corolla"),(2017,"Toyota","Corolla"),
    (2018,"Toyota","Highlander"),(2017,"Toyota","Highlander"),
    (2018,"Honda","Civic"),(2017,"Honda","Civic"),(2016,"Honda","Civic"),
    (2018,"Honda","Accord"),(2017,"Honda","Accord"),(2016,"Honda","Accord"),
    (2018,"Honda","CR-V"),(2017,"Honda","CR-V"),(2016,"Honda","CR-V"),
    (2017,"Ford","F-150"),(2014,"Ford","F-150"),(2013,"Ford","F-150"),
    (2018,"Ford","F-150"),(2019,"Ford","F-150"),
    (2018,"Chevrolet","Silverado 1500"),(2017,"Chevrolet","Silverado 1500"),
    (2018,"Nissan","Altima"),(2017,"Nissan","Altima"),(2016,"Nissan","Altima"),
    (2018,"Nissan","Rogue"),(2017,"Nissan","Rogue"),(2016,"Nissan","Rogue"),
    (2018,"RAM","1500"),(2017,"RAM","1500"),(2016,"RAM","1500"),
    (2018,"Jeep","Grand Cherokee"),(2017,"Jeep","Grand Cherokee"),
    (2018,"Jeep","Wrangler"),(2017,"Jeep","Wrangler"),
    (2018,"Subaru","Outback"),(2017,"Subaru","Outback"),(2016,"Subaru","Outback"),
    (2018,"Subaru","Forester"),(2017,"Subaru","Forester"),
    (2018,"Hyundai","Tucson"),(2017,"Hyundai","Tucson"),
    (2018,"Hyundai","Elantra"),(2017,"Hyundai","Elantra"),
    (2018,"Kia","Sorento"),(2017,"Kia","Sorento"),
    (2018,"Volkswagen","Jetta"),(2017,"Volkswagen","Jetta"),
    (2018,"BMW","330i"),(2017,"BMW","330i"),
    (2023,"Toyota","Tacoma"),(2023,"Toyota","Corolla"),
    (2023,"Honda","Civic"),(2023,"Honda","CR-V"),(2023,"Honda","Accord"),
    (2023,"Nissan","Altima"),(2023,"Nissan","Rogue"),
    (2023,"Chevrolet","Silverado 1500"),(2023,"Chevrolet","Equinox"),
    (2023,"GMC","Sierra 1500"),
    (2023,"Subaru","Outback"),(2023,"Subaru","Forester"),
    (2023,"Jeep","Grand Cherokee"),(2023,"Jeep","Wrangler"),
    (2023,"Hyundai","Tucson"),(2023,"Hyundai","Santa Fe"),
    (2023,"Kia","Sorento"),(2023,"Kia","Telluride"),
    (2023,"Ford","Explorer"),(2023,"Ford","Escape"),(2023,"Ford","Bronco"),
    (2023,"Mazda","CX-5"),(2023,"Mazda","Mazda3"),
    (2023,"Volkswagen","Jetta"),(2023,"Volkswagen","Tiguan"),
    (2023,"BMW","330i"),(2023,"BMW","X3"),(2023,"BMW","X5"),
    (2024,"Toyota","Camry"),(2024,"Toyota","RAV4"),(2024,"Toyota","Tacoma"),
    (2024,"Honda","Civic"),(2024,"Honda","Accord"),(2024,"Honda","CR-V"),
    (2024,"Ford","F-150"),(2024,"Ford","Explorer"),
    (2024,"Chevrolet","Silverado 1500"),(2024,"Chevrolet","Equinox"),
    (2024,"Nissan","Altima"),(2024,"Nissan","Rogue"),
    (2024,"RAM","1500"),
    (2024,"Jeep","Grand Cherokee"),(2024,"Jeep","Wrangler"),
    (2024,"Subaru","Outback"),(2024,"Subaru","Forester"),
    (2024,"Hyundai","Tucson"),(2024,"Kia","Sorento"),
    (2024,"Tesla","Model 3"),(2024,"Tesla","Model Y"),
    (2024,"BMW","X5"),(2024,"Mercedes-Benz","C-Class"),
]

ENDPOINTS = ["oil-change","parts","maintenance","fluids","torque-specs",
             "recalls","engine-specs","fuel-economy","safety-ratings",
             "warranty","reliability","tsb","service-costs"]

session = requests.Session()
session.headers.update(HEADERS)
req_count = 0

def api_get(path, params=None):
    global req_count
    try:
        r = session.get(f"{BASE_URL}/{path}", params=params, timeout=15)
        req_count += 1
        time.sleep(DELAY)
        if r.status_code == 200: return r.json().get("data")
        if r.status_code == 429:
            log.warning("Rate limited - sleeping 15s")
            time.sleep(15)
            return api_get(path, params)
        return None
    except Exception as e:
        log.error(f"Request error: {e}")
        return None

def setup_db(conn):
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
        CREATE TABLE IF NOT EXISTS fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, hwy_mpg INTEGER, combined_mpg INTEGER, annual_cost INTEGER, drive TEXT);
        CREATE TABLE IF NOT EXISTS safety_ratings (vehicle_id INTEGER PRIMARY KEY, overall_rating INTEGER, frontal_crash_driver INTEGER, frontal_crash_passenger INTEGER, side_crash_driver INTEGER, side_crash_passenger INTEGER, rollover_rating INTEGER, rollover_risk_pct REAL, side_pole_rating INTEGER);
        CREATE TABLE IF NOT EXISTS warranty (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, warranty_type TEXT, months INTEGER, miles INTEGER, notes TEXT);
        CREATE TABLE IF NOT EXISTS reliability (vehicle_id INTEGER PRIMARY KEY, overall_score REAL, rating TEXT, complaint_count INTEGER, crash_count INTEGER, fire_count INTEGER, injury_count INTEGER, top_issue TEXT);
        CREATE TABLE IF NOT EXISTS service_costs (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, service_type TEXT, region TEXT, cost_low INTEGER, cost_high INTEGER, cost_average INTEGER, labor_hours_low REAL, labor_hours_high REAL);
        CREATE TABLE IF NOT EXISTS tsb (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, tsb_number TEXT, title TEXT, component TEXT, summary TEXT, date TEXT);
        CREATE TABLE IF NOT EXISTS dtc_codes (code TEXT PRIMARY KEY, description TEXT, urgency TEXT, cost_low INTEGER, cost_high INTEGER, possible_causes TEXT, systems TEXT);
        CREATE TABLE IF NOT EXISTS pull_log (vehicle_id INTEGER, endpoint TEXT, status TEXT, pulled_at TEXT, PRIMARY KEY (vehicle_id, endpoint));
    """)
    conn.commit()

def save_all(conn, vid, ep, data):
    try:
        if ep == "oil-change" and data:
            s = data.get("oil_spec") or {}
            conn.execute("INSERT OR REPLACE INTO oil_change VALUES (?,?,?,?,?,?,?,?)",
                (vid, s.get("viscosity"), s.get("oil_type"), s.get("capacity_with_filter"),
                 s.get("capacity_without_filter"), s.get("oem_spec"),
                 json.dumps(data.get("filters")), json.dumps(data.get("drain_bolt"))))
        elif ep == "parts" and data:
            sp = data.get("spark_plug_spec") or {}
            bat = data.get("battery_spec") or {}
            ti = data.get("tire_spec") or {}
            conn.execute("INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (vid, sp.get("plug_type"), sp.get("gap"), sp.get("quantity"),
                 bat.get("group_size"), bat.get("cca"),
                 ti.get("size"), ti.get("pressure_front_psi"), ti.get("pressure_rear_psi"),
                 json.dumps(data.get("spark_plugs")), json.dumps(data.get("air_filters")),
                 json.dumps(data.get("cabin_filters")), json.dumps(data.get("wiper_blades")),
                 json.dumps(data.get("batteries"))))
        elif ep == "maintenance" and data:
            schedules = data.get("schedules", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in schedules:
                sid = item.get("id")
                conn.execute("INSERT OR REPLACE INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes) VALUES (?,?,?,?,?,?,?)",
                    (sid, vid, item.get("mileage_interval"), item.get("months_interval"),
                     item.get("description"), item.get("source"), item.get("notes")))
                if sid is not None:
                    conn.execute("DELETE FROM maintenance_parts WHERE maintenance_id=?", (sid,))
                for p in (item.get("parts") or []):
                    conn.execute("INSERT INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                        (sid, vid, p.get("part_type"), p.get("brand"), p.get("part_number"), p.get("description"), p.get("qty")))
        elif ep == "fluids" and data:
            tf = data.get("transmission_fluid") or {}
            c  = data.get("coolant") or {}
            conn.execute("INSERT OR REPLACE INTO fluids VALUES (?,?,?,?,?,?,?,?)",
                (vid, tf.get("fluid_type"), tf.get("capacity_quarts"),
                 (data.get("brake_fluid") or {}).get("dot_type"),
                 c.get("coolant_type"), c.get("capacity_quarts"),
                 (data.get("power_steering_fluid") or {}).get("fluid_type"),
                 json.dumps(data.get("differential_fluids"))))
        elif ep == "torque-specs" and data:
            for t in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes) VALUES (?,?,?,?,?)",
                    (vid, t.get("component"), t.get("torque_ft_lbs"), t.get("torque_nm"), t.get("notes")))
        elif ep == "recalls" and data:
            for r in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) VALUES (?,?,?,?,?,?)",
                    (vid, r.get("campaign_number") or r.get("nhtsa_campaign_number"),
                     r.get("component"), r.get("summary"), r.get("remedy"),
                     1 if r.get("park_it") else 0))
        elif ep == "engine-specs" and data:
            for e in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO engine_specs (vehicle_id,variant,horsepower,torque_ft_lbs,displacement_l,cylinders,cylinder_config,aspiration,fuel_system) VALUES (?,?,?,?,?,?,?,?,?)",
                    (vid, e.get("engine_variant"), e.get("horsepower"), e.get("torque_ft_lbs"),
                     e.get("displacement_liters"), e.get("cylinders"), e.get("cylinder_config"),
                     e.get("aspiration"), e.get("fuel_system")))
        elif ep == "fuel-economy" and data:
            for f in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO fuel_economy (vehicle_id,city_mpg,hwy_mpg,combined_mpg,annual_cost,drive) VALUES (?,?,?,?,?,?)",
                    (vid, f.get("city_mpg"), f.get("highway_mpg"), f.get("combined_mpg"),
                     f.get("annual_fuel_cost"), f.get("drive")))
        elif ep == "safety-ratings" and data:
            conn.execute("INSERT OR REPLACE INTO safety_ratings VALUES (?,?,?,?,?,?,?,?,?)",
                (vid, data.get("overall_rating"), data.get("frontal_crash_driver"),
                 data.get("frontal_crash_passenger"), data.get("side_crash_driver"),
                 data.get("side_crash_passenger"), data.get("rollover_rating"),
                 data.get("rollover_risk_pct"), data.get("side_pole_rating")))
        elif ep == "warranty" and data:
            for w in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO warranty (vehicle_id,warranty_type,months,miles,notes) VALUES (?,?,?,?,?)",
                    (vid, w.get("warranty_type"), w.get("months"), w.get("miles"), w.get("notes")))
        elif ep == "reliability" and data:
            conn.execute("INSERT OR REPLACE INTO reliability VALUES (?,?,?,?,?,?,?,?)",
                (vid, data.get("overall_score"), data.get("rating"), data.get("complaint_count"),
                 data.get("crash_count"), data.get("fire_count"), data.get("injury_count"), data.get("top_issue")))
        elif ep == "service-costs" and data:
            for s in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO service_costs (vehicle_id,service_type,region,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high) VALUES (?,?,?,?,?,?,?,?)",
                    (vid, s.get("service_type"), s.get("region"), s.get("cost_low"),
                     s.get("cost_high"), s.get("cost_average"),
                     s.get("labor_hours_low"), s.get("labor_hours_high")))
        elif ep == "tsb" and data:
            for t in (data if isinstance(data, list) else []):
                conn.execute("INSERT OR IGNORE INTO tsb (vehicle_id,tsb_number,title,component,summary,date) VALUES (?,?,?,?,?,?)",
                    (vid, t.get("tsb_number") or t.get("number"), t.get("title"),
                     t.get("component"), t.get("summary"), t.get("date") or t.get("issued_date")))
        conn.commit()
    except Exception as e:
        log.error(f"  Save error [{ep}]: {e}")

def pull_vehicle(conn, year, make, model):
    # Skip if already in DB with full pull
    existing = conn.execute("SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (year, make, model)).fetchone()
    if existing:
        vid = existing[0]
        done_count = conn.execute("SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status='ok'", (vid,)).fetchone()[0]
        if done_count >= len(ENDPOINTS) - 2:
            log.info(f"  SKIP (already complete)")
            return vid

    result = api_get("vehicles", {"year": year, "make": make, "model": model})
    if not result:
        log.warning(f"  No results")
        return None

    vehicles = result if isinstance(result, list) else [result]
    v = next((x for x in vehicles if x.get("engine")), vehicles[0])
    vid = v["id"]

    conn.execute("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?,?)",
        (vid, year, make, model, v.get("engine"), v.get("trim"), datetime.utcnow().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')}")

    for ep in ENDPOINTS:
        done = conn.execute("SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?", (vid, ep)).fetchone()
        if done and done[0] == "ok":
            continue
        data = api_get(f"vehicles/{vid}/{ep}")
        if data:
            save_all(conn, vid, ep, data)
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid, ep, "ok" if data else "empty", datetime.utcnow().isoformat()))
        conn.commit()
    return vid

def main():
    log.info(f"Wrench Batch 2 - {len(TARGET_VEHICLES)} target vehicles")
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)

    ok = 0
    for i, (yr, mk, mdl) in enumerate(TARGET_VEHICLES, 1):
        log.info(f"[{i}/{len(TARGET_VEHICLES)}] {yr} {mk} {mdl}")
        try:
            if pull_vehicle(conn, yr, mk, mdl): ok += 1
        except Exception as e:
            log.error(f"  Error: {e}")
        if i % 20 == 0:
            total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            log.info(f"--- {ok}/{i} ok | {req_count} requests | {total} total vehicles in DB ---")

    total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"Done! Added {ok} vehicles. Total in DB: {total}. Requests used: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
