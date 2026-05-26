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
    handlers=[logging.FileHandler("wrench_log7.txt", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # 1998-1999 top models
    (1999,"Toyota","Camry"),(1998,"Toyota","Camry"),
    (1999,"Toyota","Corolla"),(1998,"Toyota","Corolla"),
    (1999,"Toyota","RAV4"),(1998,"Toyota","RAV4"),
    (1999,"Toyota","Tacoma"),(1998,"Toyota","Tacoma"),
    (1999,"Toyota","4Runner"),(1998,"Toyota","4Runner"),
    (1999,"Toyota","Sienna"),(1998,"Toyota","Sienna"),
    (1999,"Toyota","Land Cruiser"),(1998,"Toyota","Land Cruiser"),
    (1999,"Honda","Civic"),(1998,"Honda","Civic"),
    (1999,"Honda","Accord"),(1998,"Honda","Accord"),
    (1999,"Honda","CR-V"),(1998,"Honda","CR-V"),
    (1999,"Honda","Odyssey"),(1998,"Honda","Odyssey"),
    (1999,"Honda","Passport"),(1998,"Honda","Passport"),
    (1999,"Ford","F-150"),(1998,"Ford","F-150"),
    (1999,"Ford","Explorer"),(1998,"Ford","Explorer"),
    (1999,"Ford","Expedition"),(1998,"Ford","Expedition"),
    (1999,"Ford","Mustang"),(1998,"Ford","Mustang"),
    (1999,"Ford","Ranger"),(1998,"Ford","Ranger"),
    (1999,"Ford","Escort"),(1998,"Ford","Escort"),
    (1999,"Ford","Taurus"),(1998,"Ford","Taurus"),
    (1999,"Chevrolet","Silverado 1500"),(1998,"Chevrolet","K1500"),
    (1999,"Chevrolet","Tahoe"),(1998,"Chevrolet","Tahoe"),
    (1999,"Chevrolet","Suburban"),(1998,"Chevrolet","Suburban"),
    (1999,"Chevrolet","Blazer"),(1998,"Chevrolet","Blazer"),
    (1999,"Chevrolet","Cavalier"),(1998,"Chevrolet","Cavalier"),
    (1999,"Chevrolet","Malibu"),(1998,"Chevrolet","Malibu"),
    (1999,"Chevrolet","S-10"),(1998,"Chevrolet","S-10"),
    (1999,"GMC","Sierra 1500"),(1998,"GMC","K1500"),
    (1999,"GMC","Yukon"),(1998,"GMC","Yukon"),
    (1999,"GMC","Jimmy"),(1998,"GMC","Jimmy"),
    (1999,"Nissan","Altima"),(1998,"Nissan","Altima"),
    (1999,"Nissan","Maxima"),(1998,"Nissan","Maxima"),
    (1999,"Nissan","Pathfinder"),(1998,"Nissan","Pathfinder"),
    (1999,"Nissan","Frontier"),(1998,"Nissan","Frontier"),
    (1999,"Nissan","Sentra"),(1998,"Nissan","Sentra"),
    (1999,"Nissan","Quest"),(1998,"Nissan","Quest"),
    (1999,"Dodge","Ram 1500"),(1998,"Dodge","Ram 1500"),
    (1999,"Dodge","Durango"),(1998,"Dodge","Durango"),
    (1999,"Dodge","Caravan"),(1998,"Dodge","Caravan"),
    (1999,"Dodge","Dakota"),(1998,"Dodge","Dakota"),
    (1999,"Dodge","Neon"),(1998,"Dodge","Neon"),
    (1999,"Dodge","Intrepid"),(1998,"Dodge","Intrepid"),
    (1999,"Jeep","Grand Cherokee"),(1998,"Jeep","Grand Cherokee"),
    (1999,"Jeep","Wrangler"),(1998,"Jeep","Wrangler"),
    (1999,"Jeep","Cherokee"),(1998,"Jeep","Cherokee"),
    (1999,"Subaru","Outback"),(1998,"Subaru","Outback"),
    (1999,"Subaru","Forester"),(1998,"Subaru","Forester"),
    (1999,"Subaru","Impreza"),(1998,"Subaru","Impreza"),
    (1999,"Subaru","Legacy"),(1998,"Subaru","Legacy"),
    (1999,"BMW","323i"),(1998,"BMW","323i"),
    (1999,"BMW","328i"),(1998,"BMW","328i"),
    (1999,"BMW","X5"),
    (1999,"Hyundai","Elantra"),(1998,"Hyundai","Elantra"),
    (1999,"Hyundai","Sonata"),(1998,"Hyundai","Sonata"),
    (1999,"Hyundai","Accent"),(1998,"Hyundai","Accent"),
    (1999,"Kia","Sportage"),(1998,"Kia","Sportage"),
    (1999,"Kia","Sephia"),(1998,"Kia","Sephia"),
    (1999,"Volkswagen","Jetta"),(1998,"Volkswagen","Jetta"),
    (1999,"Volkswagen","Passat"),(1998,"Volkswagen","Passat"),
    (1999,"Volkswagen","Golf"),(1998,"Volkswagen","Golf"),
    (1999,"Volkswagen","New Beetle"),(1998,"Volkswagen","New Beetle"),
    (1999,"Mazda","626"),(1998,"Mazda","626"),
    (1999,"Mazda","B-Series"),(1998,"Mazda","B-Series"),
    (1999,"Mazda","MPV"),(1998,"Mazda","MPV"),
    (1999,"Mazda","Protege"),(1998,"Mazda","Protege"),
    (1999,"Pontiac","Grand Prix"),(1998,"Pontiac","Grand Prix"),
    (1999,"Pontiac","Grand Am"),(1998,"Pontiac","Grand Am"),
    (1999,"Pontiac","Bonneville"),(1998,"Pontiac","Bonneville"),
    (1999,"Pontiac","Montana"),(1998,"Pontiac","Montana"),
    (1999,"Saturn","SL"),(1998,"Saturn","SL"),
    (1999,"Saturn","SW"),(1998,"Saturn","SW"),
    (1999,"Buick","LeSabre"),(1998,"Buick","LeSabre"),
    (1999,"Buick","Century"),(1998,"Buick","Century"),
    (1999,"Buick","Regal"),(1998,"Buick","Regal"),
    (1999,"Buick","Park Avenue"),(1998,"Buick","Park Avenue"),
    (1999,"Oldsmobile","Alero"),(1999,"Oldsmobile","Intrigue"),
    (1999,"Oldsmobile","Bravada"),(1998,"Oldsmobile","Bravada"),
    (1999,"Oldsmobile","Silhouette"),(1998,"Oldsmobile","Silhouette"),
    (1999,"Cadillac","DeVille"),(1998,"Cadillac","DeVille"),
    (1999,"Cadillac","Escalade"),(1999,"Cadillac","Eldorado"),
    (1999,"Lincoln","Town Car"),(1998,"Lincoln","Town Car"),
    (1999,"Lincoln","Navigator"),(1998,"Lincoln","Navigator"),
    (1999,"Mercury","Mountaineer"),(1998,"Mercury","Mountaineer"),
    (1999,"Mercury","Villager"),(1998,"Mercury","Villager"),
    (1999,"Mercury","Grand Marquis"),(1998,"Mercury","Grand Marquis"),
    (1999,"Chrysler","Town & Country"),(1998,"Chrysler","Town & Country"),
    (1999,"Chrysler","300M"),(1999,"Chrysler","Concorde"),
    (1999,"Chrysler","LHS"),(1998,"Chrysler","LHS"),
    (1999,"Acura","TL"),(1998,"Acura","TL"),
    (1999,"Acura","Integra"),(1998,"Acura","Integra"),
    (1999,"Acura","CL"),(1998,"Acura","CL"),
    (1999,"Lexus","RX 300"),(1998,"Lexus","RX 300"),
    (1999,"Lexus","ES 300"),(1998,"Lexus","ES 300"),
    (1999,"Lexus","GS 300"),(1998,"Lexus","GS 300"),
    (1999,"Lexus","LX 470"),(1998,"Lexus","LX 470"),
    (1999,"Infiniti","QX4"),(1998,"Infiniti","QX4"),
    (1999,"Infiniti","I30"),(1998,"Infiniti","I30"),
    (1999,"Mercedes-Benz","C-Class"),(1998,"Mercedes-Benz","C-Class"),
    (1999,"Mercedes-Benz","E-Class"),(1998,"Mercedes-Benz","E-Class"),
    (1999,"Mercedes-Benz","ML 320"),(1998,"Mercedes-Benz","ML 320"),
    (1999,"Volvo","S70"),(1998,"Volvo","S70"),
    (1999,"Volvo","V70"),(1998,"Volvo","V70"),
    (1999,"Volvo","XC70"),(1998,"Volvo","XC70"),
    (1999,"Audi","A4"),(1998,"Audi","A4"),
    (1999,"Audi","A6"),(1998,"Audi","A6"),
    (1999,"Audi","A8"),(1998,"Audi","A8"),
    (1999,"Saab","9-3"),(1998,"Saab","9-3"),
    (1999,"Saab","9-5"),(1998,"Saab","9-5"),
    (1999,"Mitsubishi","Eclipse"),(1998,"Mitsubishi","Eclipse"),
    (1999,"Mitsubishi","Galant"),(1998,"Mitsubishi","Galant"),
    (1999,"Mitsubishi","Montero"),(1998,"Mitsubishi","Montero"),
    (1999,"Isuzu","Rodeo"),(1998,"Isuzu","Rodeo"),
    (1999,"Isuzu","Trooper"),(1998,"Isuzu","Trooper"),
    (1999,"Isuzu","Amigo"),(1998,"Isuzu","Amigo"),
    (1999,"Suzuki","Grand Vitara"),(1998,"Suzuki","Grand Vitara"),
    (1999,"Suzuki","Sidekick"),(1998,"Suzuki","Sidekick"),
    (1999,"Land Rover","Discovery"),(1998,"Land Rover","Discovery"),
    (1999,"Land Rover","Range Rover"),(1998,"Land Rover","Range Rover"),
    (1999,"Land Rover","Freelander"),
    (1999,"Porsche","911"),(1998,"Porsche","911"),
    (1999,"Porsche","Boxster"),(1998,"Porsche","Boxster"),
    # 1996-1997 highest volume
    (1997,"Toyota","Camry"),(1996,"Toyota","Camry"),
    (1997,"Toyota","Corolla"),(1996,"Toyota","Corolla"),
    (1997,"Toyota","4Runner"),(1996,"Toyota","4Runner"),
    (1997,"Toyota","Tacoma"),(1996,"Toyota","Tacoma"),
    (1997,"Honda","Civic"),(1996,"Honda","Civic"),
    (1997,"Honda","Accord"),(1996,"Honda","Accord"),
    (1997,"Honda","CR-V"),
    (1997,"Ford","F-150"),(1996,"Ford","F-150"),
    (1997,"Ford","Explorer"),(1996,"Ford","Explorer"),
    (1997,"Ford","Mustang"),(1996,"Ford","Mustang"),
    (1997,"Ford","Taurus"),(1996,"Ford","Taurus"),
    (1997,"Chevrolet","C/K 1500"),(1996,"Chevrolet","C/K 1500"),
    (1997,"Chevrolet","Tahoe"),(1996,"Chevrolet","Tahoe"),
    (1997,"Chevrolet","Blazer"),(1996,"Chevrolet","Blazer"),
    (1997,"Chevrolet","Cavalier"),(1996,"Chevrolet","Cavalier"),
    (1997,"Chevrolet","S-10"),(1996,"Chevrolet","S-10"),
    (1997,"Nissan","Altima"),(1996,"Nissan","Altima"),
    (1997,"Nissan","Pathfinder"),(1996,"Nissan","Pathfinder"),
    (1997,"Nissan","Maxima"),(1996,"Nissan","Maxima"),
    (1997,"Dodge","Ram 1500"),(1996,"Dodge","Ram 1500"),
    (1997,"Dodge","Caravan"),(1996,"Dodge","Caravan"),
    (1997,"Dodge","Dakota"),(1996,"Dodge","Dakota"),
    (1997,"Jeep","Grand Cherokee"),(1996,"Jeep","Grand Cherokee"),
    (1997,"Jeep","Wrangler"),(1996,"Jeep","Wrangler"),
    (1997,"Jeep","Cherokee"),(1996,"Jeep","Cherokee"),
    (1997,"Subaru","Legacy"),(1996,"Subaru","Legacy"),
    (1997,"Subaru","Outback"),(1997,"Subaru","Impreza"),
    (1997,"BMW","328i"),(1996,"BMW","328i"),
    (1997,"Acura","Integra"),(1996,"Acura","Integra"),
    (1997,"Acura","CL"),(1997,"Acura","TL"),
    (1997,"Lexus","ES 300"),(1996,"Lexus","ES 300"),
    (1997,"Volkswagen","Jetta"),(1996,"Volkswagen","Jetta"),
    (1997,"Volkswagen","Passat"),(1996,"Volkswagen","Passat"),
    (1997,"Pontiac","Grand Am"),(1996,"Pontiac","Grand Am"),
    (1997,"Pontiac","Grand Prix"),(1996,"Pontiac","Grand Prix"),
    (1997,"Buick","LeSabre"),(1996,"Buick","LeSabre"),
    (1997,"Buick","Century"),(1996,"Buick","Century"),
    (1997,"Saturn","SL"),(1996,"Saturn","SL"),
    (1997,"Mercury","Villager"),(1996,"Mercury","Villager"),
    (1997,"Lincoln","Town Car"),(1996,"Lincoln","Town Car"),
    (1997,"Cadillac","DeVille"),(1996,"Cadillac","DeVille"),
    (1997,"Mitsubishi","Eclipse"),(1996,"Mitsubishi","Eclipse"),
    (1997,"Mitsubishi","Galant"),(1996,"Mitsubishi","Galant"),
    (1997,"Isuzu","Rodeo"),(1996,"Isuzu","Rodeo"),
    (1997,"Suzuki","Sidekick"),(1996,"Suzuki","Sidekick"),
    (1997,"Land Rover","Discovery"),(1996,"Land Rover","Discovery"),
    (1997,"Porsche","911"),(1996,"Porsche","911"),
    (1997,"Volvo","850"),(1996,"Volvo","850"),
    (1997,"Saab","900"),(1996,"Saab","900"),
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
    log.info(f"Wrench Batch 7 - {len(TARGET)} target vehicles")
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
