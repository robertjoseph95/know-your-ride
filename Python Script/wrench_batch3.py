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
    handlers=[logging.FileHandler("wrench_log3.txt",encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # Older years 2005-2009 for top models
    (2009,"Toyota","Camry"),(2008,"Toyota","Camry"),(2007,"Toyota","Camry"),
    (2009,"Toyota","Corolla"),(2008,"Toyota","Corolla"),(2007,"Toyota","Corolla"),
    (2009,"Toyota","RAV4"),(2008,"Toyota","RAV4"),(2007,"Toyota","RAV4"),
    (2009,"Toyota","Tacoma"),(2008,"Toyota","Tacoma"),(2007,"Toyota","Tacoma"),
    (2009,"Toyota","Prius"),(2008,"Toyota","Prius"),(2007,"Toyota","Prius"),
    (2009,"Toyota","Highlander"),(2008,"Toyota","Highlander"),
    (2009,"Honda","Civic"),(2008,"Honda","Civic"),(2007,"Honda","Civic"),
    (2009,"Honda","Accord"),(2008,"Honda","Accord"),(2007,"Honda","Accord"),
    (2009,"Honda","CR-V"),(2008,"Honda","CR-V"),(2007,"Honda","CR-V"),
    (2009,"Ford","F-150"),(2008,"Ford","F-150"),(2007,"Ford","F-150"),
    (2009,"Ford","Escape"),(2008,"Ford","Escape"),
    (2009,"Chevrolet","Silverado 1500"),(2008,"Chevrolet","Silverado 1500"),
    (2009,"Nissan","Altima"),(2008,"Nissan","Altima"),(2007,"Nissan","Altima"),
    (2009,"Nissan","Rogue"),(2008,"Nissan","Rogue"),
    (2009,"Subaru","Outback"),(2008,"Subaru","Outback"),
    (2009,"Jeep","Wrangler"),(2008,"Jeep","Wrangler"),
    (2009,"BMW","328i"),(2008,"BMW","328i"),
    # More Toyota models
    (2020,"Toyota","Venza"),(2021,"Toyota","Venza"),(2022,"Toyota","Venza"),
    (2020,"Toyota","C-HR"),(2021,"Toyota","C-HR"),(2022,"Toyota","C-HR"),
    (2020,"Toyota","Sequoia"),(2021,"Toyota","Sequoia"),(2022,"Toyota","Sequoia"),
    (2020,"Toyota","Land Cruiser"),(2021,"Toyota","Land Cruiser"),
    (2022,"Toyota","GR86"),(2023,"Toyota","GR86"),
    (2021,"Toyota","Sienna"),
    # More Honda
    (2020,"Honda","Passport"),(2021,"Honda","Passport"),(2022,"Honda","Passport"),
    (2020,"Honda","Insight"),(2021,"Honda","Insight"),
    (2020,"Honda","Fit"),
    # More Nissan
    (2020,"Nissan","Armada"),(2021,"Nissan","Armada"),(2022,"Nissan","Armada"),
    (2020,"Nissan","Titan"),(2021,"Nissan","Titan"),
    (2020,"Nissan","Maxima"),(2021,"Nissan","Maxima"),
    (2020,"Nissan","Leaf"),(2021,"Nissan","Leaf"),(2022,"Nissan","Leaf"),
    # More Hyundai
    (2020,"Hyundai","Palisade"),(2021,"Hyundai","Palisade"),(2022,"Hyundai","Palisade"),
    (2020,"Hyundai","Kona"),(2021,"Hyundai","Kona"),(2022,"Hyundai","Kona"),
    (2020,"Hyundai","Venue"),(2021,"Hyundai","Venue"),
    (2022,"Hyundai","Ioniq 5"),(2023,"Hyundai","Ioniq 5"),
    (2021,"Hyundai","Ioniq 6"),(2022,"Hyundai","Ioniq 6"),
    # More Kia
    (2020,"Kia","Carnival"),(2021,"Kia","Carnival"),(2022,"Kia","Carnival"),
    (2020,"Kia","Forte"),(2021,"Kia","Forte"),(2022,"Kia","Forte"),
    (2020,"Kia","Seltos"),(2021,"Kia","Seltos"),(2022,"Kia","Seltos"),
    (2022,"Kia","EV6"),(2023,"Kia","EV6"),
    (2018,"Kia","Stinger"),(2019,"Kia","Stinger"),(2020,"Kia","Stinger"),
    # More Subaru
    (2020,"Subaru","BRZ"),(2021,"Subaru","BRZ"),(2022,"Subaru","BRZ"),
    (2020,"Subaru","WRX"),(2021,"Subaru","WRX"),(2022,"Subaru","WRX"),
    (2020,"Subaru","Ascent"),(2021,"Subaru","Ascent"),(2022,"Subaru","Ascent"),
    # More Ford
    (2022,"Ford","Maverick"),(2023,"Ford","Maverick"),(2024,"Ford","Maverick"),
    (2021,"Ford","Mustang Mach-E"),(2022,"Ford","Mustang Mach-E"),(2023,"Ford","Mustang Mach-E"),
    (2020,"Ford","Transit"),(2021,"Ford","Transit"),(2022,"Ford","Transit"),
    (2020,"Ford","Edge"),(2021,"Ford","Edge"),(2022,"Ford","Edge"),
    (2020,"Ford","Expedition"),(2021,"Ford","Expedition"),(2022,"Ford","Expedition"),
    # More Chevy/GMC
    (2020,"Chevrolet","Tahoe"),(2021,"Chevrolet","Tahoe"),(2022,"Chevrolet","Tahoe"),
    (2020,"Chevrolet","Suburban"),(2021,"Chevrolet","Suburban"),(2022,"Chevrolet","Suburban"),
    (2020,"Chevrolet","Blazer"),(2021,"Chevrolet","Blazer"),(2022,"Chevrolet","Blazer"),
    (2020,"Chevrolet","Trailblazer"),(2021,"Chevrolet","Trailblazer"),
    (2020,"Chevrolet","Silverado 2500HD"),(2021,"Chevrolet","Silverado 2500HD"),
    (2022,"Chevrolet","Bolt EV"),(2023,"Chevrolet","Bolt EV"),
    (2020,"GMC","Yukon"),(2021,"GMC","Yukon"),(2022,"GMC","Yukon"),
    (2020,"GMC","Sierra 2500HD"),(2021,"GMC","Sierra 2500HD"),
    (2020,"GMC","Canyon"),(2021,"GMC","Canyon"),(2022,"GMC","Canyon"),
    # More RAM
    (2020,"RAM","2500"),(2021,"RAM","2500"),(2022,"RAM","2500"),
    (2020,"RAM","ProMaster"),(2021,"RAM","ProMaster"),
    (2020,"RAM","1500 Classic"),(2021,"RAM","1500 Classic"),
    # More Jeep
    (2020,"Jeep","Gladiator"),(2021,"Jeep","Gladiator"),(2022,"Jeep","Gladiator"),
    (2020,"Jeep","Renegade"),(2021,"Jeep","Renegade"),(2022,"Jeep","Renegade"),
    (2020,"Jeep","Wagoneer"),(2021,"Jeep","Wagoneer"),
    # More BMW
    (2020,"BMW","530i"),(2021,"BMW","530i"),(2022,"BMW","530i"),
    (2020,"BMW","X1"),(2021,"BMW","X1"),(2022,"BMW","X1"),
    (2020,"BMW","X7"),(2021,"BMW","X7"),
    (2020,"BMW","430i"),(2021,"BMW","430i"),
    (2020,"BMW","M3"),(2021,"BMW","M3"),
    # More Mercedes
    (2020,"Mercedes-Benz","GLC 300"),(2021,"Mercedes-Benz","GLC 300"),(2022,"Mercedes-Benz","GLC 300"),
    (2020,"Mercedes-Benz","GLE 350"),(2021,"Mercedes-Benz","GLE 350"),
    (2020,"Mercedes-Benz","A-Class"),(2021,"Mercedes-Benz","A-Class"),
    # More Audi
    (2020,"Audi","Q7"),(2021,"Audi","Q7"),(2022,"Audi","Q7"),
    (2020,"Audi","A6"),(2021,"Audi","A6"),
    (2020,"Audi","Q3"),(2021,"Audi","Q3"),
    (2020,"Audi","A3"),(2021,"Audi","A3"),
    # More VW
    (2020,"Volkswagen","Atlas"),(2021,"Volkswagen","Atlas"),(2022,"Volkswagen","Atlas"),
    (2020,"Volkswagen","Taos"),(2021,"Volkswagen","Taos"),
    (2020,"Volkswagen","ID.4"),(2021,"Volkswagen","ID.4"),(2022,"Volkswagen","ID.4"),
    (2020,"Volkswagen","Passat"),(2021,"Volkswagen","Passat"),
    # More Dodge
    (2020,"Dodge","Durango"),(2021,"Dodge","Durango"),(2022,"Dodge","Durango"),
    (2020,"Dodge","Journey"),
    # Porsche
    (2020,"Porsche","Cayenne"),(2021,"Porsche","Cayenne"),(2022,"Porsche","Cayenne"),
    (2020,"Porsche","Macan"),(2021,"Porsche","Macan"),(2022,"Porsche","Macan"),
    (2020,"Porsche","911"),(2021,"Porsche","911"),
    (2020,"Porsche","Panamera"),(2021,"Porsche","Panamera"),
    (2020,"Porsche","Taycan"),(2021,"Porsche","Taycan"),(2022,"Porsche","Taycan"),
    # Land Rover
    (2020,"Land Rover","Range Rover"),(2021,"Land Rover","Range Rover"),(2022,"Land Rover","Range Rover"),
    (2020,"Land Rover","Range Rover Sport"),(2021,"Land Rover","Range Rover Sport"),
    (2020,"Land Rover","Defender"),(2021,"Land Rover","Defender"),(2022,"Land Rover","Defender"),
    (2020,"Land Rover","Discovery"),(2021,"Land Rover","Discovery"),
    # Tesla more models
    (2020,"Tesla","Model S"),(2021,"Tesla","Model S"),(2022,"Tesla","Model S"),
    (2020,"Tesla","Model X"),(2021,"Tesla","Model X"),(2022,"Tesla","Model X"),
    (2022,"Tesla","Model 3"),(2023,"Tesla","Model S"),(2023,"Tesla","Model X"),
    # More Mazda
    (2020,"Mazda","CX-9"),(2021,"Mazda","CX-9"),(2022,"Mazda","CX-9"),
    (2020,"Mazda","CX-30"),(2021,"Mazda","CX-30"),(2022,"Mazda","CX-30"),
    (2020,"Mazda","MX-5 Miata"),(2021,"Mazda","MX-5 Miata"),
    # Alfa Romeo
    (2020,"Alfa Romeo","Giulia"),(2021,"Alfa Romeo","Giulia"),(2022,"Alfa Romeo","Giulia"),
    (2020,"Alfa Romeo","Stelvio"),(2021,"Alfa Romeo","Stelvio"),(2022,"Alfa Romeo","Stelvio"),
    # Chrysler/Fiat
    (2020,"Chrysler","300"),(2021,"Chrysler","300"),(2022,"Chrysler","300"),
    # Cadillac more
    (2021,"Cadillac","Escalade ESV"),(2022,"Cadillac","Escalade ESV"),
    (2020,"Cadillac","CT5"),(2021,"Cadillac","CT5"),
    (2020,"Cadillac","XT6"),(2021,"Cadillac","XT6"),
    # Lincoln more
    (2020,"Lincoln","Navigator L"),(2021,"Lincoln","Navigator L"),
    (2020,"Lincoln","MKZ"),(2021,"Lincoln","MKZ"),
    # More Acura
    (2020,"Acura","ILX"),(2021,"Acura","ILX"),
    (2020,"Acura","NSX"),(2021,"Acura","NSX"),
    # More Infiniti
    (2020,"Infiniti","QX80"),(2021,"Infiniti","QX80"),
    (2020,"Infiniti","QX55"),(2021,"Infiniti","QX55"),
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
    existing = conn.execute(
        "SELECT id FROM vehicles WHERE year=? AND make=? AND model=?",
        (year, make, model)
    ).fetchone()
    if existing:
        vid = existing[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status='ok'", (vid,)
        ).fetchone()[0]
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
        (vid, year, make, model, v.get("engine"), v.get("trim"),
         datetime.now().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')}")

    for ep in ENDPOINTS:
        done = conn.execute(
            "SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?", (vid, ep)
        ).fetchone()
        if done and done[0] == "ok":
            continue
        data = api_get(f"vehicles/{vid}/{ep}")
        if data:
            save_all(conn, vid, ep, data)
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid, ep, "ok" if data else "empty", datetime.now().isoformat()))
        conn.commit()
    return vid

def main():
    log.info(f"Wrench Batch 3 - {len(TARGET)} target vehicles")
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
            log.info(f"--- {ok}/{i} ok | {req_count} reqs | {total} total in DB ---")
    total = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"Done! {ok} new vehicles. Total in DB: {total}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
