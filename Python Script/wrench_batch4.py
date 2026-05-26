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
    handlers=[logging.FileHandler("wrench_log4.txt", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # ── 2005-2006 top models ──
    (2006,"Toyota","Camry"),(2005,"Toyota","Camry"),
    (2006,"Toyota","Corolla"),(2005,"Toyota","Corolla"),
    (2006,"Toyota","RAV4"),(2005,"Toyota","RAV4"),
    (2006,"Toyota","Tacoma"),(2005,"Toyota","Tacoma"),
    (2006,"Toyota","Highlander"),(2005,"Toyota","Highlander"),
    (2006,"Toyota","Prius"),(2005,"Toyota","Prius"),
    (2006,"Toyota","Tundra"),(2005,"Toyota","Tundra"),
    (2006,"Toyota","Sienna"),(2005,"Toyota","Sienna"),
    (2006,"Honda","Civic"),(2005,"Honda","Civic"),
    (2006,"Honda","Accord"),(2005,"Honda","Accord"),
    (2006,"Honda","CR-V"),(2005,"Honda","CR-V"),
    (2006,"Honda","Pilot"),(2005,"Honda","Pilot"),
    (2006,"Honda","Odyssey"),(2005,"Honda","Odyssey"),
    (2006,"Ford","F-150"),(2005,"Ford","F-150"),
    (2006,"Ford","Explorer"),(2005,"Ford","Explorer"),
    (2006,"Ford","Escape"),(2005,"Ford","Escape"),
    (2006,"Ford","Mustang"),(2005,"Ford","Mustang"),
    (2006,"Chevrolet","Silverado 1500"),(2005,"Chevrolet","Silverado 1500"),
    (2006,"Chevrolet","Equinox"),(2005,"Chevrolet","Equinox"),
    (2006,"Chevrolet","Tahoe"),(2005,"Chevrolet","Tahoe"),
    (2006,"Chevrolet","Suburban"),(2005,"Chevrolet","Suburban"),
    (2006,"Chevrolet","Colorado"),(2005,"Chevrolet","Colorado"),
    (2006,"Nissan","Altima"),(2005,"Nissan","Altima"),
    (2006,"Nissan","Sentra"),(2005,"Nissan","Sentra"),
    (2006,"Nissan","Rogue"),
    (2006,"Nissan","Pathfinder"),(2005,"Nissan","Pathfinder"),
    (2006,"Nissan","Titan"),(2005,"Nissan","Titan"),
    (2006,"Jeep","Grand Cherokee"),(2005,"Jeep","Grand Cherokee"),
    (2006,"Jeep","Wrangler"),(2005,"Jeep","Wrangler"),
    (2006,"Dodge","Charger"),(2005,"Dodge","Charger"),
    (2006,"Dodge","Durango"),(2005,"Dodge","Durango"),
    (2006,"RAM","1500"),(2005,"RAM","1500"),
    (2006,"Subaru","Outback"),(2005,"Subaru","Outback"),
    (2006,"Subaru","Forester"),(2005,"Subaru","Forester"),
    (2006,"BMW","325i"),(2005,"BMW","325i"),
    (2006,"BMW","330i"),(2005,"BMW","330i"),
    (2006,"Hyundai","Sonata"),(2005,"Hyundai","Sonata"),
    (2006,"Hyundai","Santa Fe"),(2005,"Hyundai","Santa Fe"),
    (2006,"Kia","Sorento"),(2005,"Kia","Sorento"),
    (2006,"Volkswagen","Jetta"),(2005,"Volkswagen","Jetta"),
    # ── More 2024 models ──
    (2024,"Toyota","Highlander"),(2024,"Toyota","Tundra"),
    (2024,"Toyota","Sienna"),(2024,"Toyota","4Runner"),
    (2024,"Honda","Pilot"),(2024,"Honda","Odyssey"),
    (2024,"Honda","HR-V"),(2024,"Honda","Ridgeline"),
    (2024,"Chevrolet","Tahoe"),(2024,"Chevrolet","Suburban"),
    (2024,"Chevrolet","Traverse"),(2024,"Chevrolet","Colorado"),
    (2024,"Chevrolet","Blazer"),(2024,"Chevrolet","Trax"),
    (2024,"GMC","Yukon"),(2024,"GMC","Terrain"),(2024,"GMC","Acadia"),
    (2024,"GMC","Canyon"),(2024,"GMC","Sierra 1500"),
    (2024,"Jeep","Grand Cherokee"),(2024,"Jeep","Wrangler"),
    (2024,"Jeep","Gladiator"),(2024,"Jeep","Compass"),
    (2024,"Subaru","Outback"),(2024,"Subaru","Forester"),
    (2024,"Subaru","Crosstrek"),(2024,"Subaru","Impreza"),
    (2024,"Hyundai","Sonata"),(2024,"Hyundai","Elantra"),
    (2024,"Hyundai","Palisade"),(2024,"Hyundai","Kona"),
    (2024,"Kia","Sportage"),(2024,"Kia","Soul"),(2024,"Kia","Forte"),
    (2024,"Mazda","CX-5"),(2024,"Mazda","CX-50"),(2024,"Mazda","Mazda3"),
    (2024,"Volkswagen","Atlas"),(2024,"Volkswagen","Tiguan"),
    (2024,"BMW","330i"),(2024,"BMW","X3"),(2024,"BMW","X5"),
    (2024,"BMW","X1"),(2024,"BMW","530i"),
    (2024,"Mercedes-Benz","GLC 300"),(2024,"Mercedes-Benz","GLE 350"),
    (2024,"Mercedes-Benz","C-Class"),
    (2024,"Audi","Q5"),(2024,"Audi","A4"),(2024,"Audi","Q7"),
    (2024,"Porsche","Cayenne"),(2024,"Porsche","Macan"),
    (2024,"Volvo","XC90"),(2024,"Volvo","XC60"),
    (2024,"Lincoln","Navigator"),(2024,"Lincoln","Corsair"),
    (2024,"Cadillac","Escalade"),(2024,"Cadillac","XT5"),
    (2024,"Buick","Enclave"),(2024,"Buick","Envision"),
    (2024,"Acura","MDX"),(2024,"Acura","RDX"),
    (2024,"Infiniti","QX60"),(2024,"Infiniti","QX50"),
    (2024,"Lexus","RX 350"),(2024,"Lexus","NX 300"),
    (2024,"Land Rover","Range Rover"),(2024,"Land Rover","Defender"),
    (2024,"Dodge","Charger"),(2024,"Dodge","Durango"),
    (2024,"Chrysler","Pacifica"),
    (2024,"Mitsubishi","Outlander"),
    (2024,"Genesis","GV80"),(2024,"Genesis","GV70"),
    # ── Mazda CX-50 (new model) ──
    (2023,"Mazda","CX-50"),(2022,"Mazda","CX-50"),
    # ── More Honda ──
    (2022,"Honda","Ridgeline"),(2023,"Honda","Ridgeline"),
    (2021,"Honda","Ridgeline"),
    (2020,"Honda","Clarity"),(2021,"Honda","Clarity"),
    # ── More Toyota ──
    (2023,"Toyota","Crown"),(2024,"Toyota","Crown"),
    (2022,"Toyota","Corolla Cross"),(2023,"Toyota","Corolla Cross"),
    (2023,"Toyota","bZ4X"),(2024,"Toyota","bZ4X"),
    # ── Ford commercial / EV ──
    (2022,"Ford","F-150 Lightning"),(2023,"Ford","F-150 Lightning"),
    (2024,"Ford","F-150 Lightning"),
    (2022,"Ford","Transit Connect"),(2023,"Ford","Transit Connect"),
    (2024,"Ford","Expedition"),
    # ── Chevy / GM EV ──
    (2024,"Chevrolet","Bolt EUV"),(2023,"Chevrolet","Bolt EUV"),
    (2022,"Chevrolet","Bolt EUV"),
    (2024,"GMC","Hummer EV"),
    # ── Rivian ──
    (2022,"Rivian","R1T"),(2023,"Rivian","R1T"),(2024,"Rivian","R1T"),
    (2022,"Rivian","R1S"),(2023,"Rivian","R1S"),(2024,"Rivian","R1S"),
    # ── Lucid ──
    (2022,"Lucid","Air"),(2023,"Lucid","Air"),(2024,"Lucid","Air"),
    # ── More VW ──
    (2023,"Volkswagen","ID.4"),(2024,"Volkswagen","ID.4"),
    (2023,"Volkswagen","Atlas Cross Sport"),
    # ── More Hyundai/Kia EV ──
    (2023,"Hyundai","Ioniq 5"),(2024,"Hyundai","Ioniq 5"),
    (2023,"Hyundai","Ioniq 6"),(2024,"Hyundai","Ioniq 6"),
    (2023,"Kia","EV6"),(2024,"Kia","EV6"),
    (2024,"Kia","EV9"),
    # ── Genesis all years ──
    (2022,"Genesis","G80"),(2023,"Genesis","G80"),(2024,"Genesis","G80"),
    (2023,"Genesis","GV80"),(2024,"Genesis","GV80"),
    (2022,"Genesis","GV70"),(2023,"Genesis","GV70"),
    (2022,"Genesis","GV60"),(2023,"Genesis","GV60"),
    # ── More Alfa Romeo ──
    (2023,"Alfa Romeo","Giulia"),(2024,"Alfa Romeo","Giulia"),
    (2023,"Alfa Romeo","Stelvio"),(2024,"Alfa Romeo","Stelvio"),
    # ── Maserati ──
    (2021,"Maserati","Ghibli"),(2022,"Maserati","Ghibli"),
    (2021,"Maserati","Levante"),(2022,"Maserati","Levante"),
    (2023,"Maserati","Grecale"),
    # ── Bentley ──
    (2021,"Bentley","Bentayga"),(2022,"Bentley","Bentayga"),
    # ── Lamborghini ──
    (2021,"Lamborghini","Urus"),(2022,"Lamborghini","Urus"),
    # ── Ferrari ──
    (2021,"Ferrari","Roma"),(2022,"Ferrari","Roma"),
    # ── More Porsche ──
    (2022,"Porsche","Cayenne"),(2023,"Porsche","Cayenne"),(2024,"Porsche","Cayenne"),
    (2022,"Porsche","Macan"),(2023,"Porsche","Macan"),
    (2022,"Porsche","Taycan"),(2023,"Porsche","Taycan"),(2024,"Porsche","Taycan"),
    (2022,"Porsche","911"),(2023,"Porsche","911"),
    # ── More Land Rover ──
    (2022,"Land Rover","Range Rover Sport"),(2023,"Land Rover","Range Rover Sport"),
    (2022,"Land Rover","Defender"),(2023,"Land Rover","Defender"),
    (2022,"Land Rover","Discovery"),(2023,"Land Rover","Discovery"),
    (2022,"Land Rover","Range Rover Velar"),(2023,"Land Rover","Range Rover Velar"),
    (2021,"Land Rover","Range Rover Evoque"),(2022,"Land Rover","Range Rover Evoque"),
    # ── More Tesla ──
    (2023,"Tesla","Model S"),(2024,"Tesla","Model S"),
    (2023,"Tesla","Model X"),(2024,"Tesla","Model X"),
    (2023,"Tesla","Cybertruck"),(2024,"Tesla","Cybertruck"),
    # ── Polestar ──
    (2021,"Polestar","2"),(2022,"Polestar","2"),(2023,"Polestar","2"),(2024,"Polestar","2"),
    # ── Volvo all models ──
    (2022,"Volvo","XC40"),(2023,"Volvo","XC40"),(2024,"Volvo","XC40"),
    (2022,"Volvo","S60"),(2023,"Volvo","S60"),
    (2022,"Volvo","V90"),(2023,"Volvo","V90"),
    (2022,"Volvo","XC40 Recharge"),(2023,"Volvo","XC40 Recharge"),
    # ── Lincoln more models ──
    (2022,"Lincoln","Aviator"),(2023,"Lincoln","Aviator"),(2024,"Lincoln","Aviator"),
    (2022,"Lincoln","Corsair"),(2023,"Lincoln","Corsair"),
    # ── More Subaru older ──
    (2019,"Subaru","Outback"),(2018,"Subaru","Outback"),(2017,"Subaru","Outback"),
    (2019,"Subaru","Forester"),(2018,"Subaru","Forester"),
    (2019,"Subaru","Crosstrek"),(2018,"Subaru","Crosstrek"),
    (2019,"Subaru","Impreza"),
    # ── More Mazda older ──
    (2019,"Mazda","CX-5"),(2018,"Mazda","CX-5"),(2017,"Mazda","CX-5"),
    (2019,"Mazda","Mazda3"),(2018,"Mazda","Mazda3"),
    # ── More Nissan older ──
    (2019,"Nissan","Altima"),(2018,"Nissan","Altima"),(2017,"Nissan","Altima"),
    (2019,"Nissan","Rogue"),(2018,"Nissan","Rogue"),(2017,"Nissan","Rogue"),
    (2019,"Nissan","Sentra"),(2018,"Nissan","Sentra"),
    (2019,"Nissan","Murano"),(2018,"Nissan","Murano"),
    # ── More Kia ──
    (2019,"Kia","Sorento"),(2018,"Kia","Sorento"),(2017,"Kia","Sorento"),
    (2019,"Kia","Sportage"),(2018,"Kia","Sportage"),
    # ── More Hyundai ──
    (2019,"Hyundai","Tucson"),(2018,"Hyundai","Tucson"),(2017,"Hyundai","Tucson"),
    (2019,"Hyundai","Sonata"),(2018,"Hyundai","Sonata"),
    (2019,"Hyundai","Santa Fe"),(2018,"Hyundai","Santa Fe"),
    # ── Mini ──
    (2020,"MINI","Cooper"),(2021,"MINI","Cooper"),(2022,"MINI","Cooper"),
    (2020,"MINI","Countryman"),(2021,"MINI","Countryman"),(2022,"MINI","Countryman"),
    # ── Mitsubishi all models ──
    (2019,"Mitsubishi","Outlander"),(2018,"Mitsubishi","Outlander"),
    (2022,"Mitsubishi","Outlander PHEV"),(2023,"Mitsubishi","Outlander PHEV"),
    (2021,"Mitsubishi","Eclipse Cross"),(2022,"Mitsubishi","Eclipse Cross"),
    # ── More Chrysler/Dodge ──
    (2019,"Chrysler","Pacifica"),(2018,"Chrysler","Pacifica"),
    (2021,"Chrysler","Pacifica Hybrid"),(2022,"Chrysler","Pacifica Hybrid"),
    (2019,"Dodge","Durango"),(2018,"Dodge","Durango"),
    (2019,"Dodge","Charger"),(2018,"Dodge","Charger"),
    (2019,"Dodge","Challenger"),(2018,"Dodge","Challenger"),
    # ── More GMC older ──
    (2019,"GMC","Sierra 1500"),(2018,"GMC","Sierra 1500"),(2017,"GMC","Sierra 1500"),
    (2019,"GMC","Terrain"),(2018,"GMC","Terrain"),
    (2019,"GMC","Acadia"),(2018,"GMC","Acadia"),
    # ── More Cadillac ──
    (2019,"Cadillac","Escalade"),(2018,"Cadillac","Escalade"),
    (2022,"Cadillac","LYRIQ"),(2023,"Cadillac","LYRIQ"),
    # ── Older luxury ──
    (2018,"BMW","530i"),(2019,"BMW","530i"),(2017,"BMW","530i"),
    (2018,"BMW","X5"),(2019,"BMW","X5"),
    (2018,"BMW","X3"),(2019,"BMW","X3"),
    (2018,"Mercedes-Benz","GLC 300"),(2019,"Mercedes-Benz","GLC 300"),
    (2018,"Mercedes-Benz","C-Class"),(2019,"Mercedes-Benz","C-Class"),
    (2018,"Audi","Q5"),(2019,"Audi","Q5"),
    (2018,"Audi","A4"),(2019,"Audi","A4"),
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
        "SELECT id FROM vehicles WHERE year=? AND make=? AND model=?", (year, make, model)
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
        (vid, year, make, model, v.get("engine"), v.get("trim"), datetime.now().isoformat()))
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
    log.info(f"Wrench Batch 4 - {len(TARGET)} target vehicles")
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
    log.info(f"DONE! Added {ok}. Total: {total}. Requests used: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
