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
    handlers=[logging.FileHandler("wrench_log5.txt", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TARGET = [
    # ── 2003-2004 top models ──
    (2004,"Toyota","Camry"),(2003,"Toyota","Camry"),
    (2004,"Toyota","Corolla"),(2003,"Toyota","Corolla"),
    (2004,"Toyota","RAV4"),(2003,"Toyota","RAV4"),
    (2004,"Toyota","Tacoma"),(2003,"Toyota","Tacoma"),
    (2004,"Toyota","Tundra"),(2003,"Toyota","Tundra"),
    (2004,"Toyota","Highlander"),(2003,"Toyota","Highlander"),
    (2004,"Toyota","Prius"),(2003,"Toyota","Prius"),
    (2004,"Toyota","Sienna"),(2003,"Toyota","Sienna"),
    (2004,"Toyota","4Runner"),(2003,"Toyota","4Runner"),
    (2004,"Toyota","Sequoia"),(2003,"Toyota","Sequoia"),
    (2004,"Honda","Civic"),(2003,"Honda","Civic"),
    (2004,"Honda","Accord"),(2003,"Honda","Accord"),
    (2004,"Honda","CR-V"),(2003,"Honda","CR-V"),
    (2004,"Honda","Pilot"),(2003,"Honda","Pilot"),
    (2004,"Honda","Odyssey"),(2003,"Honda","Odyssey"),
    (2004,"Honda","Element"),(2003,"Honda","Element"),
    (2004,"Ford","F-150"),(2003,"Ford","F-150"),
    (2004,"Ford","Explorer"),(2003,"Ford","Explorer"),
    (2004,"Ford","Expedition"),(2003,"Ford","Expedition"),
    (2004,"Ford","Escape"),(2003,"Ford","Escape"),
    (2004,"Ford","Mustang"),(2003,"Ford","Mustang"),
    (2004,"Ford","Focus"),(2003,"Ford","Focus"),
    (2004,"Ford","Ranger"),(2003,"Ford","Ranger"),
    (2004,"Chevrolet","Silverado 1500"),(2003,"Chevrolet","Silverado 1500"),
    (2004,"Chevrolet","Tahoe"),(2003,"Chevrolet","Tahoe"),
    (2004,"Chevrolet","Suburban"),(2003,"Chevrolet","Suburban"),
    (2004,"Chevrolet","Avalanche"),(2003,"Chevrolet","Avalanche"),
    (2004,"Chevrolet","Colorado"),(2003,"Chevrolet","Colorado"),
    (2004,"Chevrolet","Impala"),(2003,"Chevrolet","Impala"),
    (2004,"Chevrolet","Malibu"),(2003,"Chevrolet","Malibu"),
    (2004,"Chevrolet","TrailBlazer"),(2003,"Chevrolet","TrailBlazer"),
    (2004,"GMC","Sierra 1500"),(2003,"GMC","Sierra 1500"),
    (2004,"GMC","Envoy"),(2003,"GMC","Envoy"),
    (2004,"GMC","Yukon"),(2003,"GMC","Yukon"),
    (2004,"Nissan","Altima"),(2003,"Nissan","Altima"),
    (2004,"Nissan","Sentra"),(2003,"Nissan","Sentra"),
    (2004,"Nissan","Maxima"),(2003,"Nissan","Maxima"),
    (2004,"Nissan","Pathfinder"),(2003,"Nissan","Pathfinder"),
    (2004,"Nissan","Xterra"),(2003,"Nissan","Xterra"),
    (2004,"Nissan","Frontier"),(2003,"Nissan","Frontier"),
    (2004,"Nissan","Murano"),(2003,"Nissan","Murano"),
    (2004,"Dodge","Ram 1500"),(2003,"Dodge","Ram 1500"),
    (2004,"Dodge","Durango"),(2003,"Dodge","Durango"),
    (2004,"Dodge","Caravan"),(2003,"Dodge","Caravan"),
    (2004,"Dodge","Neon"),(2003,"Dodge","Neon"),
    (2004,"Dodge","Stratus"),(2003,"Dodge","Stratus"),
    (2004,"Jeep","Grand Cherokee"),(2003,"Jeep","Grand Cherokee"),
    (2004,"Jeep","Wrangler"),(2003,"Jeep","Wrangler"),
    (2004,"Jeep","Liberty"),(2003,"Jeep","Liberty"),
    (2004,"BMW","325i"),(2003,"BMW","325i"),
    (2004,"BMW","330i"),(2003,"BMW","330i"),
    (2004,"BMW","X5"),(2003,"BMW","X5"),
    (2004,"Subaru","Outback"),(2003,"Subaru","Outback"),
    (2004,"Subaru","Forester"),(2003,"Subaru","Forester"),
    (2004,"Subaru","Impreza"),(2003,"Subaru","Impreza"),
    (2004,"Hyundai","Elantra"),(2003,"Hyundai","Elantra"),
    (2004,"Hyundai","Sonata"),(2003,"Hyundai","Sonata"),
    (2004,"Hyundai","Santa Fe"),(2003,"Hyundai","Santa Fe"),
    (2004,"Kia","Sorento"),(2003,"Kia","Sorento"),
    (2004,"Kia","Optima"),(2003,"Kia","Optima"),
    (2004,"Volkswagen","Jetta"),(2003,"Volkswagen","Jetta"),
    (2004,"Volkswagen","Passat"),(2003,"Volkswagen","Passat"),
    (2004,"Volkswagen","Golf"),(2003,"Volkswagen","Golf"),
    (2004,"Mazda","Mazda6"),(2003,"Mazda","Mazda6"),
    (2004,"Mazda","Mazda3"),(2003,"Mazda","Mazda3"),
    (2004,"Mazda","MPV"),(2003,"Mazda","MPV"),
    # ── Saturn (popular 2000s brand, discontinued 2010) ──
    (2007,"Saturn","Vue"),(2008,"Saturn","Vue"),(2009,"Saturn","Vue"),
    (2007,"Saturn","Outlook"),(2008,"Saturn","Outlook"),(2009,"Saturn","Outlook"),
    (2007,"Saturn","Aura"),(2008,"Saturn","Aura"),(2009,"Saturn","Aura"),
    (2005,"Saturn","Ion"),(2006,"Saturn","Ion"),(2007,"Saturn","Ion"),
    (2005,"Saturn","Vue"),(2006,"Saturn","Vue"),
    # ── Pontiac (discontinued 2010) ──
    (2007,"Pontiac","G6"),(2008,"Pontiac","G6"),(2009,"Pontiac","G6"),
    (2007,"Pontiac","Torrent"),(2008,"Pontiac","Torrent"),
    (2007,"Pontiac","Vibe"),(2008,"Pontiac","Vibe"),(2009,"Pontiac","Vibe"),
    (2007,"Pontiac","Grand Prix"),(2008,"Pontiac","Grand Prix"),
    (2005,"Pontiac","G6"),(2006,"Pontiac","G6"),
    (2008,"Pontiac","Solstice"),(2009,"Pontiac","Solstice"),
    # ── Scion (Toyota sub-brand, discontinued 2016) ──
    (2010,"Scion","tC"),(2011,"Scion","tC"),(2012,"Scion","tC"),
    (2013,"Scion","tC"),(2014,"Scion","tC"),(2015,"Scion","tC"),
    (2010,"Scion","xB"),(2011,"Scion","xB"),(2012,"Scion","xB"),
    (2008,"Scion","xB"),(2009,"Scion","xB"),
    (2012,"Scion","FR-S"),(2013,"Scion","FR-S"),(2014,"Scion","FR-S"),
    (2015,"Scion","FR-S"),(2016,"Scion","FR-S"),
    (2010,"Scion","xD"),(2011,"Scion","xD"),(2012,"Scion","xD"),
    # ── Mercury (Ford sub-brand, discontinued 2011) ──
    (2008,"Mercury","Mountaineer"),(2009,"Mercury","Mountaineer"),(2010,"Mercury","Mountaineer"),
    (2008,"Mercury","Milan"),(2009,"Mercury","Milan"),(2010,"Mercury","Milan"),
    (2007,"Mercury","Mariner"),(2008,"Mercury","Mariner"),(2009,"Mercury","Mariner"),
    (2010,"Mercury","Mariner"),(2011,"Mercury","Mariner"),
    # ── Hummer ──
    (2005,"Hummer","H2"),(2006,"Hummer","H2"),(2007,"Hummer","H2"),(2008,"Hummer","H2"),
    (2006,"Hummer","H3"),(2007,"Hummer","H3"),(2008,"Hummer","H3"),(2009,"Hummer","H3"),
    # ── Saab (discontinued 2011) ──
    (2007,"Saab","9-3"),(2008,"Saab","9-3"),(2009,"Saab","9-3"),(2010,"Saab","9-3"),
    (2007,"Saab","9-5"),(2008,"Saab","9-5"),(2009,"Saab","9-5"),
    # ── Commercial vans ──
    (2015,"Ford","E-Series"),(2016,"Ford","E-Series"),(2014,"Ford","E-Series"),
    (2018,"Chevrolet","Express 1500"),(2019,"Chevrolet","Express 1500"),(2020,"Chevrolet","Express 1500"),
    (2018,"GMC","Savana 1500"),(2019,"GMC","Savana 1500"),(2020,"GMC","Savana 1500"),
    (2018,"Ford","Transit-150"),(2019,"Ford","Transit-150"),(2020,"Ford","Transit-150"),
    (2021,"Ford","Transit-150"),(2022,"Ford","Transit-150"),
    # ── Truck trims not yet covered ──
    (2021,"Ford","F-150 Raptor"),(2022,"Ford","F-150 Raptor"),(2023,"Ford","F-150 Raptor"),
    (2021,"Jeep","Wrangler Rubicon"),(2022,"Jeep","Wrangler Rubicon"),
    (2021,"Chevrolet","Silverado 1500 LTZ"),(2022,"Chevrolet","Silverado 1500 LTZ"),
    # ── More Lexus ──
    (2020,"Lexus","IS 300"),(2021,"Lexus","IS 300"),(2022,"Lexus","IS 300"),
    (2020,"Lexus","ES 300h"),(2021,"Lexus","ES 300h"),
    (2020,"Lexus","UX 200"),(2021,"Lexus","UX 200"),(2022,"Lexus","UX 200"),
    (2020,"Lexus","LX 570"),(2021,"Lexus","LX 570"),
    (2020,"Lexus","RX 450h"),(2021,"Lexus","RX 450h"),
    # ── More Acura ──
    (2020,"Acura","MDX Sport Hybrid"),(2021,"Acura","MDX Sport Hybrid"),
    (2020,"Acura","RDX A-Spec"),(2022,"Acura","Integra"),(2023,"Acura","Integra"),
    # ── More Infiniti ──
    (2020,"Infiniti","QX80"),(2021,"Infiniti","QX80"),(2022,"Infiniti","QX80"),
    (2020,"Infiniti","Q60"),(2021,"Infiniti","Q60"),
    # ── Cadillac more ──
    (2022,"Cadillac","CT4"),(2023,"Cadillac","CT4"),
    (2022,"Cadillac","CT5"),(2023,"Cadillac","CT5"),
    (2023,"Cadillac","LYRIQ"),(2024,"Cadillac","LYRIQ"),
    # ── More Lincoln ──
    (2022,"Lincoln","Nautilus"),(2023,"Lincoln","Nautilus"),(2024,"Lincoln","Nautilus"),
    (2022,"Lincoln","Navigator"),(2023,"Lincoln","Navigator"),
    # ── Buick more ──
    (2022,"Buick","Encore GX"),(2023,"Buick","Encore GX"),(2024,"Buick","Encore GX"),
    (2022,"Buick","Envista"),(2023,"Buick","Envista"),
    # ── More Genesis ──
    (2024,"Genesis","G80"),(2024,"Genesis","GV80"),(2024,"Genesis","GV70"),
    (2024,"Genesis","GV60"),(2023,"Genesis","G70"),
    # ── More Volvo ──
    (2024,"Volvo","XC90"),(2024,"Volvo","XC60"),(2024,"Volvo","XC40"),
    (2023,"Volvo","C40 Recharge"),(2024,"Volvo","C40 Recharge"),
    # ── More Porsche ──
    (2024,"Porsche","911"),(2024,"Porsche","Panamera"),
    (2023,"Porsche","Cayenne Coupe"),(2024,"Porsche","Cayenne Coupe"),
    # ── More Land Rover ──
    (2024,"Land Rover","Discovery Sport"),(2023,"Land Rover","Discovery Sport"),
    (2024,"Land Rover","Range Rover Evoque"),
    # ── More Alfa Romeo ──
    (2024,"Alfa Romeo","Tonale"),(2023,"Alfa Romeo","Tonale"),
    # ── More Mazda ──
    (2024,"Mazda","CX-90"),(2023,"Mazda","CX-90"),
    (2024,"Mazda","CX-70"),(2023,"Mazda","CX-70"),
    # ── More VW ──
    (2024,"Volkswagen","ID.4"),(2024,"Volkswagen","Atlas"),
    (2023,"Volkswagen","ID Buzz"),(2024,"Volkswagen","ID Buzz"),
    # ── More BMW ──
    (2024,"BMW","iX"),(2023,"BMW","iX"),
    (2024,"BMW","i4"),(2023,"BMW","i4"),
    (2024,"BMW","X5 PHEV"),(2023,"BMW","X5 PHEV"),
    # ── More Mercedes ──
    (2024,"Mercedes-Benz","EQS"),(2023,"Mercedes-Benz","EQS"),
    (2024,"Mercedes-Benz","EQE"),(2023,"Mercedes-Benz","EQE"),
    (2024,"Mercedes-Benz","GLS 450"),(2023,"Mercedes-Benz","GLS 450"),
    # ── More Audi ──
    (2024,"Audi","e-tron GT"),(2023,"Audi","e-tron GT"),
    (2024,"Audi","Q8 e-tron"),(2023,"Audi","Q8 e-tron"),
    (2024,"Audi","Q8"),(2023,"Audi","Q8"),
    # ── Hyundai/Kia more ──
    (2024,"Hyundai","Ioniq 5 N"),(2023,"Hyundai","Ioniq 5 N"),
    (2024,"Kia","EV9"),(2023,"Kia","EV9"),
    (2024,"Kia","Carnival"),(2023,"Kia","Carnival"),
    # ── More Tesla ──
    (2024,"Tesla","Cybertruck"),(2023,"Tesla","Cybertruck"),
    (2024,"Tesla","Model 3"),(2024,"Tesla","Model Y"),
    # ── Rivian / Lucid / Polestar more ──
    (2024,"Rivian","R1T"),(2024,"Rivian","R1S"),
    (2024,"Lucid","Air"),(2024,"Polestar","2"),
    (2024,"Polestar","3"),(2023,"Polestar","3"),
    # ── Chevy Trax / Equinox EV ──
    (2024,"Chevrolet","Trax"),(2024,"Chevrolet","Equinox EV"),
    (2023,"Chevrolet","Equinox EV"),
    # ── Honda more ──
    (2024,"Honda","Prologue"),(2023,"Honda","Prologue"),
    (2024,"Honda","Passport"),(2024,"Honda","Ridgeline"),
    # ── Subaru more ──
    (2024,"Subaru","Solterra"),(2023,"Subaru","Solterra"),
    # ── Nissan more ──
    (2024,"Nissan","Ariya"),(2023,"Nissan","Ariya"),
    (2024,"Nissan","Frontier"),(2024,"Nissan","Titan"),
    # ── Ram more ──
    (2024,"RAM","TRX"),(2023,"RAM","TRX"),
    (2024,"RAM","ProMaster"),(2024,"RAM","2500"),
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
    log.info(f"Wrench Batch 5 - {len(TARGET)} target vehicles")
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
    log.info(f"DONE! Added {ok}. Total: {total}. Requests: {req_count}")
    conn.close()

if __name__ == "__main__":
    main()
