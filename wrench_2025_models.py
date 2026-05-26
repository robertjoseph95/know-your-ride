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
    handlers=[logging.FileHandler("wrench_2025.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # 2025 models
    (2025,"Toyota","Camry"),(2025,"Toyota","RAV4"),(2025,"Toyota","Corolla"),
    (2025,"Toyota","Tacoma"),(2025,"Toyota","Highlander"),(2025,"Toyota","Tundra"),
    (2025,"Toyota","4Runner"),(2025,"Toyota","Sienna"),(2025,"Toyota","bZ4X"),
    (2025,"Honda","Civic"),(2025,"Honda","Accord"),(2025,"Honda","CR-V"),
    (2025,"Honda","Pilot"),(2025,"Honda","Odyssey"),(2025,"Honda","Ridgeline"),
    (2025,"Honda","Prologue"),
    (2025,"Ford","F-150"),(2025,"Ford","Explorer"),(2025,"Ford","Escape"),
    (2025,"Ford","Bronco"),(2025,"Ford","Ranger"),(2025,"Ford","Mustang"),
    (2025,"Ford","Mustang Mach-E"),(2025,"Ford","F-150 Lightning"),
    (2025,"Chevrolet","Silverado 1500"),(2025,"Chevrolet","Equinox"),
    (2025,"Chevrolet","Tahoe"),(2025,"Chevrolet","Suburban"),
    (2025,"Chevrolet","Colorado"),(2025,"Chevrolet","Traverse"),
    (2025,"Chevrolet","Trax"),(2025,"Chevrolet","Equinox EV"),
    (2025,"GMC","Sierra 1500"),(2025,"GMC","Yukon"),(2025,"GMC","Terrain"),
    (2025,"GMC","Canyon"),(2025,"GMC","Acadia"),
    (2025,"Nissan","Altima"),(2025,"Nissan","Rogue"),(2025,"Nissan","Frontier"),
    (2025,"Nissan","Pathfinder"),(2025,"Nissan","Ariya"),
    (2025,"RAM","1500"),(2025,"RAM","2500"),
    (2025,"Jeep","Grand Cherokee"),(2025,"Jeep","Wrangler"),(2025,"Jeep","Gladiator"),
    (2025,"Jeep","Compass"),
    (2025,"Subaru","Outback"),(2025,"Subaru","Forester"),(2025,"Subaru","Crosstrek"),
    (2025,"Subaru","Solterra"),
    (2025,"Hyundai","Tucson"),(2025,"Hyundai","Santa Fe"),(2025,"Hyundai","Palisade"),
    (2025,"Hyundai","Elantra"),(2025,"Hyundai","Sonata"),
    (2025,"Hyundai","Ioniq 5"),(2025,"Hyundai","Ioniq 6"),
    (2025,"Kia","Sorento"),(2025,"Kia","Sportage"),(2025,"Kia","Telluride"),
    (2025,"Kia","EV6"),(2025,"Kia","EV9"),(2025,"Kia","Carnival"),
    (2025,"Mazda","CX-5"),(2025,"Mazda","CX-50"),(2025,"Mazda","CX-90"),
    (2025,"Mazda","Mazda3"),
    (2025,"Volkswagen","Jetta"),(2025,"Volkswagen","Tiguan"),(2025,"Volkswagen","Atlas"),
    (2025,"Volkswagen","ID.4"),
    (2025,"BMW","330i"),(2025,"BMW","X3"),(2025,"BMW","X5"),(2025,"BMW","X1"),
    (2025,"BMW","530i"),(2025,"BMW","i4"),(2025,"BMW","iX"),
    (2025,"Mercedes-Benz","C-Class"),(2025,"Mercedes-Benz","GLC 300"),
    (2025,"Mercedes-Benz","GLE 350"),(2025,"Mercedes-Benz","EQS"),
    (2025,"Audi","A4"),(2025,"Audi","Q5"),(2025,"Audi","Q7"),(2025,"Audi","e-tron GT"),
    (2025,"Tesla","Model 3"),(2025,"Tesla","Model Y"),(2025,"Tesla","Model S"),
    (2025,"Tesla","Model X"),(2025,"Tesla","Cybertruck"),
    (2025,"Rivian","R1T"),(2025,"Rivian","R1S"),
    (2025,"Lucid","Air"),
    (2025,"Polestar","2"),(2025,"Polestar","3"),
    (2025,"Porsche","Cayenne"),(2025,"Porsche","Macan"),(2025,"Porsche","Taycan"),
    (2025,"Porsche","911"),
    (2025,"Land Rover","Range Rover"),(2025,"Land Rover","Defender"),
    (2025,"Volvo","XC90"),(2025,"Volvo","XC60"),(2025,"Volvo","XC40"),
    (2025,"Genesis","GV80"),(2025,"Genesis","GV70"),(2025,"Genesis","G80"),
    (2025,"Acura","MDX"),(2025,"Acura","RDX"),
    (2025,"Lexus","RX 350"),(2025,"Lexus","NX 300"),(2025,"Lexus","ES 350"),
    (2025,"Infiniti","QX60"),(2025,"Infiniti","QX50"),
    (2025,"Cadillac","Escalade"),(2025,"Cadillac","XT5"),(2025,"Cadillac","LYRIQ"),
    (2025,"Lincoln","Navigator"),(2025,"Lincoln","Aviator"),
    (2025,"Buick","Enclave"),(2025,"Buick","Encore GX"),
    (2025,"Dodge","Durango"),
    (2025,"Chrysler","Pacifica"),
    (2025,"Mitsubishi","Outlander"),
    (2025,"Alfa Romeo","Stelvio"),(2025,"Alfa Romeo","Giulia"),
    # Trim variants not yet covered
    (2024,"Ford","F-150 Raptor"),(2023,"Ford","F-150 Raptor"),
    (2024,"Chevrolet","Silverado ZR2"),(2023,"Chevrolet","Silverado ZR2"),
    (2024,"Jeep","Wrangler Rubicon"),(2023,"Jeep","Wrangler Rubicon"),
    (2024,"Jeep","Wrangler Sahara"),(2023,"Jeep","Wrangler Sahara"),
    (2024,"RAM","1500 TRX"),(2023,"RAM","1500 TRX"),
    (2024,"Toyota","Tacoma TRD Pro"),(2023,"Toyota","Tacoma TRD Pro"),
    (2024,"Toyota","4Runner TRD Pro"),(2023,"Toyota","4Runner TRD Pro"),
    (2024,"Ford","Bronco Raptor"),(2023,"Ford","Bronco Raptor"),
    (2024,"Chevrolet","Colorado ZR2"),(2023,"Chevrolet","Colorado ZR2"),
    (2024,"GMC","Canyon AT4X"),(2023,"GMC","Canyon AT4X"),
    (2024,"BMW","M3"),(2024,"BMW","M4"),(2023,"BMW","M4"),
    (2024,"Mercedes-Benz","AMG C 63"),(2023,"Mercedes-Benz","AMG C 63"),
    (2024,"Audi","RS5"),(2023,"Audi","RS5"),
    (2024,"Porsche","911 GT3"),(2023,"Porsche","911 GT3"),
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
            sp=data.get("spark_plug_spec") or {}; bat=data.get("battery_spec") or {}; ti=data.get("tire_spec") or {}
            conn.execute("INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (vid,sp.get("plug_type"),sp.get("gap"),sp.get("quantity"),
                 bat.get("group_size"),bat.get("cca"),ti.get("size"),
                 ti.get("pressure_front_psi"),ti.get("pressure_rear_psi"),
                 json.dumps(data.get("spark_plugs")),json.dumps(data.get("air_filters")),
                 json.dumps(data.get("cabin_filters")),json.dumps(data.get("wiper_blades")),
                 json.dumps(data.get("batteries"))))
        elif ep == "maintenance" and data:
            for item in (data.get("schedules",[]) if isinstance(data,dict) else []):
                sid=item.get("id")
                conn.execute("INSERT OR REPLACE INTO maintenance VALUES (?,?,?,?,?,?,?)",
                    (sid,vid,item.get("mileage_interval"),item.get("months_interval"),
                     item.get("description"),item.get("source"),item.get("notes")))
                for part in (item.get("parts") or []):
                    conn.execute("INSERT OR IGNORE INTO maintenance_parts (maintenance_id,vehicle_id,part_type,brand,part_number,description,qty) VALUES (?,?,?,?,?,?,?)",
                        (sid,vid,part.get("part_type"),part.get("brand"),part.get("part_number"),part.get("description"),part.get("qty")))
        elif ep == "fluids" and data:
            tf=data.get("transmission_fluid") or {}; c=data.get("coolant") or {}
            conn.execute("INSERT OR REPLACE INTO fluids VALUES (?,?,?,?,?,?,?,?)",
                (vid,tf.get("fluid_type"),tf.get("capacity_quarts"),
                 (data.get("brake_fluid") or {}).get("dot_type"),
                 c.get("coolant_type"),c.get("capacity_quarts"),
                 (data.get("power_steering_fluid") or {}).get("fluid_type"),
                 json.dumps(data.get("differential_fluids"))))
        elif ep == "torque-specs" and data:
            for t in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes) VALUES (?,?,?,?,?)",
                    (vid,t.get("component"),t.get("torque_ft_lbs"),t.get("torque_nm"),t.get("notes")))
        elif ep == "recalls" and data:
            for r in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) VALUES (?,?,?,?,?,?)",
                    (vid,r.get("campaign_number") or r.get("nhtsa_campaign_number"),
                     r.get("component"),r.get("summary"),r.get("remedy"),1 if r.get("park_it") else 0))
        elif ep == "engine-specs" and data:
            for e in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO engine_specs (vehicle_id,variant,horsepower,torque_ft_lbs,displacement_l,cylinders,cylinder_config,aspiration,fuel_system) VALUES (?,?,?,?,?,?,?,?,?)",
                    (vid,e.get("engine_variant"),e.get("horsepower"),e.get("torque_ft_lbs"),
                     e.get("displacement_liters"),e.get("cylinders"),e.get("cylinder_config"),
                     e.get("aspiration"),e.get("fuel_system")))
        elif ep == "fuel-economy" and data:
            for f in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO fuel_economy (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,engine,transmission,drive) VALUES (?,?,?,?,?,?,?,?)",
                    (vid,f.get("city_mpg"),f.get("highway_mpg"),f.get("combined_mpg"),
                     f.get("annual_fuel_cost"),f.get("engine_displacement"),
                     f.get("transmission"),f.get("drive")))
        elif ep == "safety-ratings" and data:
            conn.execute("INSERT OR REPLACE INTO safety_ratings VALUES (?,?,?,?,?,?,?,?,?)",
                (vid,data.get("overall_rating"),data.get("frontal_crash_driver"),
                 data.get("frontal_crash_passenger"),data.get("side_crash_driver"),
                 data.get("side_crash_passenger"),data.get("rollover_rating"),
                 data.get("rollover_risk_pct"),data.get("side_pole_rating")))
        elif ep == "warranty" and data:
            for w in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO warranty (vehicle_id,warranty_type,months,miles,notes) VALUES (?,?,?,?,?)",
                    (vid,w.get("warranty_type"),w.get("months"),w.get("miles"),w.get("notes")))
        elif ep == "reliability" and data:
            conn.execute("INSERT OR REPLACE INTO reliability VALUES (?,?,?,?,?,?,?,?)",
                (vid,data.get("overall_score"),data.get("rating"),data.get("complaint_count"),
                 data.get("crash_count"),data.get("fire_count"),data.get("injury_count"),data.get("top_issue")))
        elif ep == "service-costs" and data:
            for s in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO service_costs (vehicle_id,service_type,region,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high) VALUES (?,?,?,?,?,?,?,?)",
                    (vid,s.get("service_type"),s.get("region"),s.get("cost_low"),
                     s.get("cost_high"),s.get("cost_average"),s.get("labor_hours_low"),s.get("labor_hours_high")))
        elif ep == "tsb" and data:
            for t in (data if isinstance(data,list) else []):
                conn.execute("INSERT OR IGNORE INTO tsb (vehicle_id,tsb_number,title,component,summary,date) VALUES (?,?,?,?,?,?)",
                    (vid,t.get("tsb_number") or t.get("number"),t.get("title"),
                     t.get("component"),t.get("summary"),t.get("date") or t.get("issued_date")))
        conn.commit()
    except Exception as e:
        log.error(f"  Save error [{ep}]: {e}")

def pull_vehicle(conn, year, make, model):
    existing = conn.execute("SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (year,make,model)).fetchone()
    if existing:
        vid=existing[0]
        done=conn.execute("SELECT COUNT(*) FROM pull_log WHERE vehicle_id=? AND status='ok'",(vid,)).fetchone()[0]
        if done >= len(ENDPOINTS)-2:
            log.info(f"  SKIP"); return vid
    result = api_get("vehicles", {"year":year,"make":make,"model":model})
    if not result: log.warning(f"  No results"); return None
    vehicles = result if isinstance(result,list) else [result]
    v = next((x for x in vehicles if x.get("engine")), vehicles[0])
    vid = v["id"]
    conn.execute("INSERT OR IGNORE INTO vehicles VALUES (?,?,?,?,?,?,?)",
        (vid,year,make,model,v.get("engine"),v.get("trim"),datetime.now().isoformat()))
    conn.commit()
    log.info(f"  -> ID {vid} | {v.get('engine','?')}")
    for ep in ENDPOINTS:
        done=conn.execute("SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?",(vid,ep)).fetchone()
        if done and done[0]=="ok": continue
        data=api_get(f"vehicles/{vid}/{ep}")
        if data: save_all(conn,vid,ep,data)
        conn.execute("INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid,ep,"ok" if data else "empty",datetime.now().isoformat()))
        conn.commit()
    return vid

def main():
    log.info(f"2025 Models + Trim Variants - {len(TARGET)} targets")
    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)
    ok = 0
    for i,(yr,mk,mdl) in enumerate(TARGET,1):
        log.info(f"[{i}/{len(TARGET)}] {yr} {mk} {mdl}")
        try:
            if pull_vehicle(conn,yr,mk,mdl): ok+=1
        except Exception as e:
            log.error(f"  Error: {e}")
        if i%25==0:
            total=conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            log.info(f"--- {ok}/{i} ok | {req_count} reqs | {total} total ---")
    total=conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    log.info(f"DONE! Added {ok}. Total: {total}. Requests: {req_count}")
    conn.close()

if __name__=="__main__":
    main()
