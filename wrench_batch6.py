import os
import requests, sqlite3, json, time, sys, io, logging
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_KEY  = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL = "https://api.vehicle-finder.com/v1"
DB_FILE  = "wrench_vehicles.db"
DELAY    = 0.25

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler("wrench_log6.txt", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # 2000-2002 top models
    (2002,"Toyota","Camry"),(2001,"Toyota","Camry"),(2000,"Toyota","Camry"),
    (2002,"Toyota","Corolla"),(2001,"Toyota","Corolla"),(2000,"Toyota","Corolla"),
    (2002,"Toyota","RAV4"),(2001,"Toyota","RAV4"),(2000,"Toyota","RAV4"),
    (2002,"Toyota","Tacoma"),(2001,"Toyota","Tacoma"),(2000,"Toyota","Tacoma"),
    (2002,"Toyota","Tundra"),(2001,"Toyota","Tundra"),(2000,"Toyota","Tundra"),
    (2002,"Toyota","4Runner"),(2001,"Toyota","4Runner"),(2000,"Toyota","4Runner"),
    (2002,"Toyota","Highlander"),(2001,"Toyota","Highlander"),
    (2002,"Toyota","Sienna"),(2001,"Toyota","Sienna"),(2000,"Toyota","Sienna"),
    (2002,"Toyota","Prius"),(2001,"Toyota","Prius"),
    (2002,"Honda","Civic"),(2001,"Honda","Civic"),(2000,"Honda","Civic"),
    (2002,"Honda","Accord"),(2001,"Honda","Accord"),(2000,"Honda","Accord"),
    (2002,"Honda","CR-V"),(2001,"Honda","CR-V"),(2000,"Honda","CR-V"),
    (2002,"Honda","Pilot"),(2001,"Honda","Pilot"),
    (2002,"Honda","Odyssey"),(2001,"Honda","Odyssey"),(2000,"Honda","Odyssey"),
    (2002,"Ford","F-150"),(2001,"Ford","F-150"),(2000,"Ford","F-150"),
    (2002,"Ford","Explorer"),(2001,"Ford","Explorer"),(2000,"Ford","Explorer"),
    (2002,"Ford","Escape"),(2001,"Ford","Escape"),
    (2002,"Ford","Focus"),(2001,"Ford","Focus"),(2000,"Ford","Focus"),
    (2002,"Ford","Mustang"),(2001,"Ford","Mustang"),(2000,"Ford","Mustang"),
    (2002,"Ford","Ranger"),(2001,"Ford","Ranger"),(2000,"Ford","Ranger"),
    (2002,"Chevrolet","Silverado 1500"),(2001,"Chevrolet","Silverado 1500"),(2000,"Chevrolet","Silverado 1500"),
    (2002,"Chevrolet","Tahoe"),(2001,"Chevrolet","Tahoe"),(2000,"Chevrolet","Tahoe"),
    (2002,"Chevrolet","Suburban"),(2001,"Chevrolet","Suburban"),(2000,"Chevrolet","Suburban"),
    (2002,"Chevrolet","Impala"),(2001,"Chevrolet","Impala"),(2000,"Chevrolet","Impala"),
    (2002,"Chevrolet","Malibu"),(2001,"Chevrolet","Malibu"),(2000,"Chevrolet","Malibu"),
    (2002,"Chevrolet","TrailBlazer"),(2001,"Chevrolet","TrailBlazer"),
    (2002,"Chevrolet","Cavalier"),(2001,"Chevrolet","Cavalier"),(2000,"Chevrolet","Cavalier"),
    (2002,"GMC","Sierra 1500"),(2001,"GMC","Sierra 1500"),(2000,"GMC","Sierra 1500"),
    (2002,"GMC","Yukon"),(2001,"GMC","Yukon"),(2000,"GMC","Yukon"),
    (2002,"Nissan","Altima"),(2001,"Nissan","Altima"),(2000,"Nissan","Altima"),
    (2002,"Nissan","Maxima"),(2001,"Nissan","Maxima"),(2000,"Nissan","Maxima"),
    (2002,"Nissan","Pathfinder"),(2001,"Nissan","Pathfinder"),(2000,"Nissan","Pathfinder"),
    (2002,"Nissan","Frontier"),(2001,"Nissan","Frontier"),(2000,"Nissan","Frontier"),
    (2002,"Nissan","Xterra"),(2001,"Nissan","Xterra"),(2000,"Nissan","Xterra"),
    (2002,"Nissan","Sentra"),(2001,"Nissan","Sentra"),(2000,"Nissan","Sentra"),
    (2002,"Dodge","Ram 1500"),(2001,"Dodge","Ram 1500"),(2000,"Dodge","Ram 1500"),
    (2002,"Dodge","Durango"),(2001,"Dodge","Durango"),(2000,"Dodge","Durango"),
    (2002,"Dodge","Caravan"),(2001,"Dodge","Caravan"),(2000,"Dodge","Caravan"),
    (2002,"Dodge","Dakota"),(2001,"Dodge","Dakota"),(2000,"Dodge","Dakota"),
    (2002,"Jeep","Grand Cherokee"),(2001,"Jeep","Grand Cherokee"),(2000,"Jeep","Grand Cherokee"),
    (2002,"Jeep","Wrangler"),(2001,"Jeep","Wrangler"),(2000,"Jeep","Wrangler"),
    (2002,"Jeep","Cherokee"),(2001,"Jeep","Cherokee"),(2000,"Jeep","Cherokee"),
    (2002,"Jeep","Liberty"),
    (2002,"Subaru","Outback"),(2001,"Subaru","Outback"),(2000,"Subaru","Outback"),
    (2002,"Subaru","Forester"),(2001,"Subaru","Forester"),(2000,"Subaru","Forester"),
    (2002,"Subaru","Impreza"),(2001,"Subaru","Impreza"),(2000,"Subaru","Impreza"),
    (2002,"BMW","325i"),(2001,"BMW","325i"),(2000,"BMW","325i"),
    (2002,"BMW","330i"),(2001,"BMW","330i"),
    (2002,"BMW","X5"),(2001,"BMW","X5"),(2000,"BMW","X5"),
    (2002,"Hyundai","Elantra"),(2001,"Hyundai","Elantra"),(2000,"Hyundai","Elantra"),
    (2002,"Hyundai","Sonata"),(2001,"Hyundai","Sonata"),(2000,"Hyundai","Sonata"),
    (2002,"Hyundai","Santa Fe"),(2001,"Hyundai","Santa Fe"),
    (2002,"Kia","Sportage"),(2001,"Kia","Sportage"),(2000,"Kia","Sportage"),
    (2002,"Kia","Optima"),(2001,"Kia","Optima"),
    (2002,"Volkswagen","Jetta"),(2001,"Volkswagen","Jetta"),(2000,"Volkswagen","Jetta"),
    (2002,"Volkswagen","Passat"),(2001,"Volkswagen","Passat"),(2000,"Volkswagen","Passat"),
    (2002,"Volkswagen","Golf"),(2001,"Volkswagen","Golf"),(2000,"Volkswagen","Golf"),
    (2002,"Mazda","Mazda6"),(2002,"Mazda","626"),(2001,"Mazda","626"),(2000,"Mazda","626"),
    (2002,"Mazda","MPV"),(2001,"Mazda","MPV"),(2000,"Mazda","MPV"),
    (2002,"Mazda","Tribute"),(2001,"Mazda","Tribute"),
    (2002,"Pontiac","Grand Prix"),(2001,"Pontiac","Grand Prix"),(2000,"Pontiac","Grand Prix"),
    (2002,"Pontiac","Grand Am"),(2001,"Pontiac","Grand Am"),(2000,"Pontiac","Grand Am"),
    (2002,"Pontiac","Bonneville"),(2001,"Pontiac","Bonneville"),
    (2002,"Saturn","SL"),(2001,"Saturn","SL"),(2000,"Saturn","SL"),
    (2002,"Saturn","Vue"),(2001,"Saturn","Vue"),
    (2002,"Buick","LeSabre"),(2001,"Buick","LeSabre"),(2000,"Buick","LeSabre"),
    (2002,"Buick","Century"),(2001,"Buick","Century"),(2000,"Buick","Century"),
    (2002,"Buick","Regal"),(2001,"Buick","Regal"),(2000,"Buick","Regal"),
    (2002,"Oldsmobile","Alero"),(2001,"Oldsmobile","Alero"),(2000,"Oldsmobile","Alero"),
    (2002,"Oldsmobile","Silhouette"),(2001,"Oldsmobile","Silhouette"),
    (2002,"Oldsmobile","Intrigue"),(2001,"Oldsmobile","Intrigue"),(2000,"Oldsmobile","Intrigue"),
    (2002,"Cadillac","DeVille"),(2001,"Cadillac","DeVille"),(2000,"Cadillac","DeVille"),
    (2002,"Cadillac","Escalade"),(2001,"Cadillac","Escalade"),(2000,"Cadillac","Escalade"),
    (2002,"Lincoln","Town Car"),(2001,"Lincoln","Town Car"),(2000,"Lincoln","Town Car"),
    (2002,"Lincoln","Navigator"),(2001,"Lincoln","Navigator"),(2000,"Lincoln","Navigator"),
    (2002,"Mercury","Mountaineer"),(2001,"Mercury","Mountaineer"),(2000,"Mercury","Mountaineer"),
    (2002,"Mercury","Grand Marquis"),(2001,"Mercury","Grand Marquis"),(2000,"Mercury","Grand Marquis"),
    (2002,"Chrysler","Town & Country"),(2001,"Chrysler","Town & Country"),(2000,"Chrysler","Town & Country"),
    (2002,"Chrysler","300M"),(2001,"Chrysler","300M"),(2000,"Chrysler","300M"),
    (2002,"Mitsubishi","Eclipse"),(2001,"Mitsubishi","Eclipse"),(2000,"Mitsubishi","Eclipse"),
    (2002,"Mitsubishi","Galant"),(2001,"Mitsubishi","Galant"),(2000,"Mitsubishi","Galant"),
    (2002,"Mitsubishi","Montero"),(2001,"Mitsubishi","Montero"),(2000,"Mitsubishi","Montero"),
    (2002,"Acura","MDX"),(2001,"Acura","MDX"),
    (2002,"Acura","TL"),(2001,"Acura","TL"),(2000,"Acura","TL"),
    (2002,"Acura","RSX"),
    (2002,"Lexus","RX 300"),(2001,"Lexus","RX 300"),(2000,"Lexus","RX 300"),
    (2002,"Lexus","ES 300"),(2001,"Lexus","ES 300"),(2000,"Lexus","ES 300"),
    (2002,"Lexus","GS 300"),(2001,"Lexus","GS 300"),(2000,"Lexus","GS 300"),
    (2002,"Infiniti","QX4"),(2001,"Infiniti","QX4"),(2000,"Infiniti","QX4"),
    (2002,"Infiniti","I35"),(2001,"Infiniti","I30"),(2000,"Infiniti","I30"),
    (2002,"Mercedes-Benz","C-Class"),(2001,"Mercedes-Benz","C-Class"),(2000,"Mercedes-Benz","C-Class"),
    (2002,"Mercedes-Benz","E-Class"),(2001,"Mercedes-Benz","E-Class"),(2000,"Mercedes-Benz","E-Class"),
    (2002,"Volvo","S60"),(2001,"Volvo","S60"),
    (2002,"Volvo","V70"),(2001,"Volvo","V70"),(2000,"Volvo","V70"),
    (2002,"Audi","A4"),(2001,"Audi","A4"),(2000,"Audi","A4"),
    (2002,"Audi","A6"),(2001,"Audi","A6"),(2000,"Audi","A6"),
    (2002,"Saab","9-3"),(2001,"Saab","9-3"),(2000,"Saab","9-3"),
    (2002,"Saab","9-5"),(2001,"Saab","9-5"),(2000,"Saab","9-5"),
    (2002,"Isuzu","Rodeo"),(2001,"Isuzu","Rodeo"),(2000,"Isuzu","Rodeo"),
    (2002,"Isuzu","Trooper"),(2001,"Isuzu","Trooper"),(2000,"Isuzu","Trooper"),
    (2002,"Suzuki","Grand Vitara"),(2001,"Suzuki","Grand Vitara"),(2000,"Suzuki","Grand Vitara"),
    (2002,"Suzuki","Vitara"),(2001,"Suzuki","Vitara"),(2000,"Suzuki","Vitara"),
]

ENDPOINTS = ["oil-change","parts","maintenance","fluids","torque-specs",
             "recalls","engine-specs","fuel-economy","safety-ratings",
             "warranty","reliability","tsb","service-costs"]

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})
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
        CREATE TABLE IF NOT EXISTS fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, drive TEXT);
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
                 bat.get("group_size"), bat.get("cca"), ti.get("size"),
                 ti.get("pressure_front_psi"), ti.get("pressure_rear_psi"),
                 json.dumps(data.get("spark_plugs")), json.dumps(data.get("air_filters")),
                 json.dumps(data.get("cabin_filters")), json.dumps(data.get("wiper_blades")),
                 json.dumps(data.get("batteries"))))
        elif ep == "maintenance" and data:
            schedules = data.get("schedules", []) if isinstance(data, dict) else []
            for item in schedules:
                sid = item.get("id")
                conn.execute("INSERT OR REPLACE INTO maintenance VALUES (?,?,?,?,?,?,?)",
                    (sid, vid, item.get("mileage_interval"), item.get("months_interval"),
                     item.get("description"), item.get("source"), item.get("notes")))
                for part in (item.get("parts") or []):
                    conn.execute("INSERT OR IGNORE INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                        (sid, vid, part.get("part_type"), part.get("brand"),
                         part.get("part_number"), part.get("description"), part.get("qty")))
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
                conn.execute("INSERT OR IGNORE INTO fuel_economy (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,engine,transmission,drive) VALUES (?,?,?,?,?,?,?,?)",
                    (vid, f.get("city_mpg"), f.get("highway_mpg"), f.get("combined_mpg"),
                     f.get("annual_fuel_cost"), f.get("engine_displacement"),
                     f.get("transmission"), f.get("drive")))
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
                 data.get("crash_count"), data.get("fire_count"), data.get("injury_count"),
                 data.get("top_issue")))
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
    existing = conn.execute("SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (year, make, model)).fetchone()
    if existing:
        vid = existing[0]
        done = conn.execute("SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status='ok'", (vid,)).fetchone()[0]
        if done >= len(ENDPOINTS) - 2:
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
        (vid, year, make, model, v.get("engine"), v.get("trim"), datetime.now().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')}")
    for ep in ENDPOINTS:
        done = conn.execute("SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?", (vid, ep)).fetchone()
        if done and done[0] == "ok": continue
        data = api_get(f"vehicles/{vid}/{ep}")
        if data: save_all(conn, vid, ep, data)
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid, ep, "ok" if data else "empty", datetime.now().isoformat()))
        conn.commit()
    return vid

def main():
    log.info(f"Wrench Batch 6 - {len(TARGET)} target vehicles")
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)
    ok = 0
    for i, (yr, mk, mdl) in enumerate(TARGET, 1):
        log.info(f"[{i}/{len(TARGET)}] {yr} {mk} {mdl}")
        try:
            if pull_vehicle(conn, yr, mk, mdl): ok += 1
        except Exception as e:
            log.error(f"  Error: {e}")
        if i % 25 == 0:
            total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            log.info(f"--- {ok}/{i} ok | {req_count} reqs | {total} total ---")
    total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"DONE! Added {ok}. Total: {total}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
