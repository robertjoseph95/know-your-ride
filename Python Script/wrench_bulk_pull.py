#!/usr/bin/env python3
"""
Wrench App — Vehicle Finder API Bulk Data Puller
================================================
Run this script ONCE on your local machine (not in Claude's sandbox).
It will pull data for 500+ vehicles across all Pro endpoints and save
everything to a local SQLite database you can use forever.

Usage:
  pip install requests
  python wrench_bulk_pull.py

Output:
  wrench_vehicles.db  — SQLite database with all pulled data
  wrench_data.json    — Full JSON export for backup/import
  wrench_log.txt      — Progress log with request counts
"""

import os
import requests
import sqlite3
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
API_KEY   = os.environ.get("VEHICLE_FINDER_KEY", "")
BASE_URL  = "https://api.vehicle-finder.com/v1"
DB_FILE   = "wrench_vehicles.db"
JSON_FILE = "wrench_data.json"
LOG_FILE  = "wrench_log.txt"

# Rate limiting: Pro = 300 req/min. We'll do 250 to be safe.
REQUESTS_PER_MINUTE = 250
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # ~0.24s

# ── TARGET VEHICLES ──────────────────────────────────────────────────────────
# (year, make, model) tuples — top ~200 most common US vehicles 2010-2024
TARGET_VEHICLES = [
    # Toyota
    (2020,"Toyota","Camry"), (2019,"Toyota","Camry"), (2018,"Toyota","Camry"),
    (2022,"Toyota","Camry"), (2021,"Toyota","Camry"), (2023,"Toyota","Camry"),
    (2020,"Toyota","Corolla"), (2021,"Toyota","Corolla"), (2022,"Toyota","Corolla"),
    (2020,"Toyota","RAV4"), (2021,"Toyota","RAV4"), (2022,"Toyota","RAV4"), (2023,"Toyota","RAV4"),
    (2020,"Toyota","Tacoma"), (2021,"Toyota","Tacoma"), (2022,"Toyota","Tacoma"),
    (2020,"Toyota","Highlander"), (2021,"Toyota","Highlander"), (2022,"Toyota","Highlander"),
    (2020,"Toyota","Tundra"), (2021,"Toyota","Tundra"), (2022,"Toyota","Tundra"),
    (2020,"Toyota","Prius"), (2021,"Toyota","Prius"), (2022,"Toyota","Prius"),
    (2020,"Toyota","Sienna"), (2021,"Toyota","Sienna"),
    (2020,"Toyota","4Runner"), (2021,"Toyota","4Runner"), (2022,"Toyota","4Runner"),
    (2010,"Toyota","Camry"), (2012,"Toyota","Camry"), (2015,"Toyota","Camry"),
    (2010,"Toyota","Corolla"), (2012,"Toyota","Corolla"), (2015,"Toyota","Corolla"),
    # Honda
    (2020,"Honda","Civic"), (2021,"Honda","Civic"), (2022,"Honda","Civic"), (2023,"Honda","Civic"),
    (2020,"Honda","Accord"), (2021,"Honda","Accord"), (2022,"Honda","Accord"), (2023,"Honda","Accord"),
    (2020,"Honda","CR-V"), (2021,"Honda","CR-V"), (2022,"Honda","CR-V"), (2023,"Honda","CR-V"),
    (2020,"Honda","Pilot"), (2021,"Honda","Pilot"), (2022,"Honda","Pilot"),
    (2020,"Honda","HR-V"), (2021,"Honda","HR-V"), (2022,"Honda","HR-V"),
    (2020,"Honda","Ridgeline"), (2021,"Honda","Ridgeline"),
    (2020,"Honda","Odyssey"), (2021,"Honda","Odyssey"),
    (2010,"Honda","Civic"), (2012,"Honda","Civic"), (2015,"Honda","Civic"),
    (2010,"Honda","Accord"), (2012,"Honda","Accord"), (2015,"Honda","Accord"),
    # Ford
    (2020,"Ford","F-150"), (2021,"Ford","F-150"), (2022,"Ford","F-150"), (2023,"Ford","F-150"),
    (2020,"Ford","Explorer"), (2021,"Ford","Explorer"), (2022,"Ford","Explorer"),
    (2020,"Ford","Escape"), (2021,"Ford","Escape"), (2022,"Ford","Escape"),
    (2020,"Ford","Edge"), (2021,"Ford","Edge"),
    (2020,"Ford","Expedition"), (2021,"Ford","Expedition"),
    (2020,"Ford","Ranger"), (2021,"Ford","Ranger"), (2022,"Ford","Ranger"),
    (2020,"Ford","Bronco"), (2021,"Ford","Bronco"), (2022,"Ford","Bronco"),
    (2020,"Ford","Mustang"), (2021,"Ford","Mustang"), (2022,"Ford","Mustang"),
    (2018,"Ford","F-150"), (2016,"Ford","F-150"), (2015,"Ford","F-150"),
    # Chevrolet / GMC
    (2020,"Chevrolet","Silverado 1500"), (2021,"Chevrolet","Silverado 1500"), (2022,"Chevrolet","Silverado 1500"),
    (2020,"Chevrolet","Equinox"), (2021,"Chevrolet","Equinox"), (2022,"Chevrolet","Equinox"),
    (2020,"Chevrolet","Traverse"), (2021,"Chevrolet","Traverse"),
    (2020,"Chevrolet","Malibu"), (2021,"Chevrolet","Malibu"),
    (2020,"Chevrolet","Colorado"), (2021,"Chevrolet","Colorado"),
    (2020,"Chevrolet","Trax"), (2021,"Chevrolet","Trax"),
    (2020,"GMC","Sierra 1500"), (2021,"GMC","Sierra 1500"), (2022,"GMC","Sierra 1500"),
    (2020,"GMC","Terrain"), (2021,"GMC","Terrain"),
    (2020,"GMC","Acadia"), (2021,"GMC","Acadia"),
    # Nissan
    (2020,"Nissan","Altima"), (2021,"Nissan","Altima"), (2022,"Nissan","Altima"),
    (2020,"Nissan","Rogue"), (2021,"Nissan","Rogue"), (2022,"Nissan","Rogue"),
    (2020,"Nissan","Sentra"), (2021,"Nissan","Sentra"),
    (2020,"Nissan","Pathfinder"), (2021,"Nissan","Pathfinder"), (2022,"Nissan","Pathfinder"),
    (2020,"Nissan","Frontier"), (2021,"Nissan","Frontier"), (2022,"Nissan","Frontier"),
    (2020,"Nissan","Murano"), (2021,"Nissan","Murano"),
    (2020,"Nissan","Kicks"), (2021,"Nissan","Kicks"),
    (2015,"Nissan","Altima"), (2015,"Nissan","Sentra"), (2015,"Nissan","Rogue"),
    # RAM
    (2020,"RAM","1500"), (2021,"RAM","1500"), (2022,"RAM","1500"), (2023,"RAM","1500"),
    (2020,"RAM","2500"), (2021,"RAM","2500"),
    # Jeep
    (2020,"Jeep","Grand Cherokee"), (2021,"Jeep","Grand Cherokee"), (2022,"Jeep","Grand Cherokee"),
    (2020,"Jeep","Wrangler"), (2021,"Jeep","Wrangler"), (2022,"Jeep","Wrangler"),
    (2020,"Jeep","Cherokee"), (2021,"Jeep","Cherokee"),
    (2020,"Jeep","Compass"), (2021,"Jeep","Compass"),
    # Subaru
    (2020,"Subaru","Outback"), (2021,"Subaru","Outback"), (2022,"Subaru","Outback"),
    (2020,"Subaru","Forester"), (2021,"Subaru","Forester"), (2022,"Subaru","Forester"),
    (2020,"Subaru","Crosstrek"), (2021,"Subaru","Crosstrek"),
    (2020,"Subaru","Impreza"), (2021,"Subaru","Impreza"),
    (2020,"Subaru","Legacy"), (2021,"Subaru","Legacy"),
    # Hyundai / Kia
    (2020,"Hyundai","Tucson"), (2021,"Hyundai","Tucson"), (2022,"Hyundai","Tucson"),
    (2020,"Hyundai","Sonata"), (2021,"Hyundai","Sonata"),
    (2020,"Hyundai","Santa Fe"), (2021,"Hyundai","Santa Fe"),
    (2020,"Hyundai","Elantra"), (2021,"Hyundai","Elantra"), (2022,"Hyundai","Elantra"),
    (2020,"Kia","Sorento"), (2021,"Kia","Sorento"), (2022,"Kia","Sorento"),
    (2020,"Kia","Sportage"), (2021,"Kia","Sportage"), (2022,"Kia","Sportage"),
    (2020,"Kia","Telluride"), (2021,"Kia","Telluride"),
    (2020,"Kia","Soul"), (2021,"Kia","Soul"),
    # BMW / Mercedes / Audi
    (2020,"BMW","330i"), (2021,"BMW","330i"), (2022,"BMW","330i"),
    (2020,"BMW","X5"), (2021,"BMW","X5"),
    (2020,"BMW","X3"), (2021,"BMW","X3"),
    (2020,"Mercedes-Benz","C-Class"), (2021,"Mercedes-Benz","C-Class"),
    (2020,"Mercedes-Benz","E-Class"), (2021,"Mercedes-Benz","E-Class"),
    (2020,"Audi","A4"), (2021,"Audi","A4"),
    (2020,"Audi","Q5"), (2021,"Audi","Q5"),
    # VW / Dodge
    (2020,"Volkswagen","Jetta"), (2021,"Volkswagen","Jetta"), (2022,"Volkswagen","Jetta"),
    (2020,"Volkswagen","Tiguan"), (2021,"Volkswagen","Tiguan"),
    (2020,"Dodge","Charger"), (2021,"Dodge","Charger"),
    (2020,"Dodge","Challenger"), (2021,"Dodge","Challenger"),
    (2020,"Dodge","Durango"), (2021,"Dodge","Durango"),
    # Tesla
    (2022,"Tesla","Model 3"), (2022,"Tesla","Model Y"), (2021,"Tesla","Model 3"),
    (2021,"Tesla","Model Y"), (2020,"Tesla","Model 3"),
    # Mazda / Chrysler
    (2020,"Mazda","CX-5"), (2021,"Mazda","CX-5"), (2022,"Mazda","CX-5"),
    (2020,"Mazda","Mazda3"), (2021,"Mazda","Mazda3"),
    (2020,"Chrysler","Pacifica"), (2021,"Chrysler","Pacifica"),
    # Older popular models
    (2015,"Ford","F-150"), (2016,"Chevrolet","Silverado 1500"),
    (2015,"Honda","Civic"), (2016,"Honda","Civic"),
    (2015,"Toyota","RAV4"), (2016,"Toyota","RAV4"),
    (2010,"Ford","F-150"), (2012,"Chevrolet","Silverado 1500"),
]

# All endpoints to pull per vehicle
ENDPOINTS = [
    "oil-change", "parts", "maintenance", "fluids",
    "torque-specs", "recalls", "engine-specs",
    "fuel-economy", "safety-ratings", "warranty",
    "reliability", "common-problems", "tsb", "service-costs"
]

# ── SETUP ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({"X-API-Key": API_KEY})

request_count = 0
start_time = time.time()

def api_get(path, params=None):
    global request_count
    url = f"{BASE_URL}/{path}"
    resp = session.get(url, params=params, timeout=15)
    request_count += 1
    time.sleep(DELAY_BETWEEN_REQUESTS)
    if resp.status_code == 200:
        return resp.json().get("data")
    elif resp.status_code == 404:
        return None
    elif resp.status_code == 429:
        log.warning("Rate limited — sleeping 10s")
        time.sleep(10)
        return api_get(path, params)
    else:
        log.error(f"HTTP {resp.status_code} for {path}: {resp.text[:100]}")
        return None

def setup_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            year INTEGER, make TEXT, model TEXT, engine TEXT, trim TEXT,
            pulled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS oil_change (
            vehicle_id INTEGER PRIMARY KEY,
            viscosity TEXT, oil_type TEXT, capacity_with_filter REAL,
            capacity_without_filter REAL, oem_spec TEXT,
            filters_json TEXT, drain_bolt_json TEXT
        );
        CREATE TABLE IF NOT EXISTS parts (
            vehicle_id INTEGER PRIMARY KEY,
            spark_plug_type TEXT, spark_plug_gap TEXT, spark_plug_qty INTEGER,
            battery_group TEXT, battery_cca INTEGER,
            tire_size TEXT, tire_pressure_front INTEGER, tire_pressure_rear INTEGER,
            spark_plugs_json TEXT, air_filters_json TEXT,
            cabin_filters_json TEXT, wiper_blades_json TEXT, batteries_json TEXT
        );
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER, mileage_interval INTEGER, months_interval INTEGER,
            description TEXT, source TEXT, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS maintenance_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maintenance_id INTEGER, vehicle_id INTEGER,
            part_type TEXT, brand TEXT, part_number TEXT,
            description TEXT, qty INTEGER
        );
        CREATE TABLE IF NOT EXISTS fluids (
            vehicle_id INTEGER PRIMARY KEY,
            transmission_fluid TEXT, transmission_capacity REAL,
            brake_fluid TEXT, coolant_type TEXT, coolant_capacity REAL,
            power_steering_fluid TEXT, differential_fluids_json TEXT
        );
        CREATE TABLE IF NOT EXISTS torque_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, component TEXT,
            torque_ft_lbs REAL, torque_nm REAL, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS recalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, campaign_number TEXT,
            component TEXT, summary TEXT, remedy TEXT, park_it INTEGER
        );
        CREATE TABLE IF NOT EXISTS engine_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, variant TEXT,
            horsepower INTEGER, torque_ft_lbs INTEGER,
            displacement_l REAL, cylinders INTEGER,
            cylinder_config TEXT, aspiration TEXT, fuel_system TEXT
        );
        CREATE TABLE IF NOT EXISTS fuel_economy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER,
            combined_mpg INTEGER, annual_fuel_cost INTEGER,
            engine TEXT, transmission TEXT, drive TEXT
        );
        CREATE TABLE IF NOT EXISTS safety_ratings (
            vehicle_id INTEGER PRIMARY KEY,
            overall_rating INTEGER, frontal_crash_driver INTEGER,
            frontal_crash_passenger INTEGER, side_crash_driver INTEGER,
            side_crash_passenger INTEGER, rollover_rating INTEGER,
            rollover_risk_pct REAL, side_pole_rating INTEGER
        );
        CREATE TABLE IF NOT EXISTS warranty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, warranty_type TEXT,
            months INTEGER, miles INTEGER, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS reliability (
            vehicle_id INTEGER PRIMARY KEY,
            overall_score REAL, rating TEXT,
            complaint_count INTEGER, crash_count INTEGER,
            fire_count INTEGER, injury_count INTEGER, top_issue TEXT
        );
        CREATE TABLE IF NOT EXISTS service_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, service_type TEXT, region TEXT,
            cost_low INTEGER, cost_high INTEGER, cost_average INTEGER,
            labor_hours_low REAL, labor_hours_high REAL
        );
        CREATE TABLE IF NOT EXISTS tsb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, tsb_number TEXT,
            title TEXT, component TEXT, summary TEXT, date TEXT
        );
        CREATE TABLE IF NOT EXISTS common_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER, component TEXT,
            complaint_count INTEGER, crash_count INTEGER,
            injury_count INTEGER, sample_description TEXT
        );
        CREATE TABLE IF NOT EXISTS dtc_codes (
            code TEXT PRIMARY KEY,
            description TEXT, urgency TEXT,
            cost_low INTEGER, cost_high INTEGER,
            possible_causes TEXT, systems TEXT
        );
        CREATE TABLE IF NOT EXISTS pull_log (
            vehicle_id INTEGER, endpoint TEXT, status TEXT,
            pulled_at TEXT, PRIMARY KEY (vehicle_id, endpoint)
        );
    """)
    conn.commit()

def save_vehicle(conn, vid, year, make, model, engine=None, trim=None):
    conn.execute("""
        INSERT OR IGNORE INTO vehicles (id, year, make, model, engine, trim, pulled_at)
        VALUES (?,?,?,?,?,?,?)
    """, (vid, year, make, model, engine, trim, datetime.utcnow().isoformat()))
    conn.commit()

def save_oil(conn, vid, d):
    if not d: return
    spec = d.get("oil_spec") or {}
    conn.execute("""
        INSERT OR REPLACE INTO oil_change VALUES (?,?,?,?,?,?,?,?)
    """, (vid, spec.get("viscosity"), spec.get("oil_type"),
          spec.get("capacity_with_filter"), spec.get("capacity_without_filter"),
          spec.get("oem_spec"),
          json.dumps(d.get("filters")), json.dumps(d.get("drain_bolt"))))
    conn.commit()

def save_parts(conn, vid, d):
    if not d: return
    sp = d.get("spark_plug_spec") or {}
    bat = d.get("battery_spec") or {}
    tire = d.get("tire_spec") or {}
    conn.execute("""
        INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (vid, sp.get("plug_type"), sp.get("gap"), sp.get("quantity"),
          bat.get("group_size"), bat.get("cca"),
          tire.get("size"), tire.get("pressure_front_psi"), tire.get("pressure_rear_psi"),
          json.dumps(d.get("spark_plugs")), json.dumps(d.get("air_filters")),
          json.dumps(d.get("cabin_filters")), json.dumps(d.get("wiper_blades"))))
    conn.commit()

def save_maintenance(conn, vid, d):
    if not d: return
    # API returns {"schedules": [...]}; fall back to a bare list for safety.
    schedules = d.get("schedules", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
    for item in schedules:
        sid = item.get("id")
        conn.execute("""
            INSERT OR REPLACE INTO maintenance (id, vehicle_id, mileage_interval, months_interval, description, source, notes)
            VALUES (?,?,?,?,?,?,?)
        """, (sid, vid, item.get("mileage_interval"), item.get("months_interval"),
              item.get("description"), item.get("source"), item.get("notes")))
        if sid is not None:
            conn.execute("DELETE FROM maintenance_parts WHERE maintenance_id=?", (sid,))
        for p in (item.get("parts") or []):
            conn.execute("""
                INSERT INTO maintenance_parts (maintenance_id, vehicle_id, part_type, brand, part_number, description, qty)
                VALUES (?,?,?,?,?,?,?)
            """, (sid, vid, p.get("part_type"), p.get("brand"), p.get("part_number"),
                  p.get("description"), p.get("qty")))
    conn.commit()

def save_fluids(conn, vid, d):
    if not d: return
    tf = d.get("transmission_fluid") or {}
    c = d.get("coolant") or {}
    conn.execute("""
        INSERT OR REPLACE INTO fluids VALUES (?,?,?,?,?,?,?,?)
    """, (vid, tf.get("fluid_type"), tf.get("capacity_quarts"),
          (d.get("brake_fluid") or {}).get("dot_type"),
          c.get("coolant_type"), c.get("capacity_quarts"),
          (d.get("power_steering_fluid") or {}).get("fluid_type"),
          json.dumps(d.get("differential_fluids"))))
    conn.commit()

def save_torque(conn, vid, d):
    if not d: return
    for item in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO torque_specs (vehicle_id, component, torque_ft_lbs, torque_nm, notes)
            VALUES (?,?,?,?,?)
        """, (vid, item.get("component"), item.get("torque_ft_lbs"), item.get("torque_nm"), item.get("notes")))
    conn.commit()

def save_recalls(conn, vid, d):
    if not d: return
    for r in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO recalls (vehicle_id, campaign_number, component, summary, remedy, park_it)
            VALUES (?,?,?,?,?,?)
        """, (vid, r.get("campaign_number") or r.get("nhtsa_campaign_number"),
              r.get("component"), r.get("summary"), r.get("remedy"),
              1 if r.get("park_it") else 0))
    conn.commit()

def save_engine(conn, vid, d):
    if not d: return
    for e in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO engine_specs (vehicle_id, variant, horsepower, torque_ft_lbs, displacement_l, cylinders, cylinder_config, aspiration, fuel_system)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (vid, e.get("engine_variant"), e.get("horsepower"), e.get("torque_ft_lbs"),
              e.get("displacement_liters"), e.get("cylinders"), e.get("cylinder_config"),
              e.get("aspiration"), e.get("fuel_system")))
    conn.commit()

def save_fuel(conn, vid, d):
    if not d: return
    for f in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO fuel_economy (vehicle_id, city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, transmission, drive)
            VALUES (?,?,?,?,?,?,?,?)
        """, (vid, f.get("city_mpg"), f.get("highway_mpg"), f.get("combined_mpg"),
              f.get("annual_fuel_cost"), f.get("engine_displacement"),
              f.get("transmission"), f.get("drive")))
    conn.commit()

def save_safety(conn, vid, d):
    if not d: return
    conn.execute("""
        INSERT OR REPLACE INTO safety_ratings VALUES (?,?,?,?,?,?,?,?,?)
    """, (vid, d.get("overall_rating"), d.get("frontal_crash_driver"),
          d.get("frontal_crash_passenger"), d.get("side_crash_driver"),
          d.get("side_crash_passenger"), d.get("rollover_rating"),
          d.get("rollover_risk_pct"), d.get("side_pole_rating")))
    conn.commit()

def save_warranty(conn, vid, d):
    if not d: return
    for w in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO warranty (vehicle_id, warranty_type, months, miles, notes)
            VALUES (?,?,?,?,?)
        """, (vid, w.get("warranty_type"), w.get("months"), w.get("miles"), w.get("notes")))
    conn.commit()

def save_reliability(conn, vid, d):
    if not d: return
    conn.execute("""
        INSERT OR REPLACE INTO reliability VALUES (?,?,?,?,?,?,?,?)
    """, (vid, d.get("overall_score"), d.get("rating"), d.get("complaint_count"),
          d.get("crash_count"), d.get("fire_count"), d.get("injury_count"), d.get("top_issue")))
    conn.commit()

def save_service_costs(conn, vid, d):
    if not d: return
    for s in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO service_costs (vehicle_id, service_type, region, cost_low, cost_high, cost_average, labor_hours_low, labor_hours_high)
            VALUES (?,?,?,?,?,?,?,?)
        """, (vid, s.get("service_type"), s.get("region"), s.get("cost_low"),
              s.get("cost_high"), s.get("cost_average"),
              s.get("labor_hours_low"), s.get("labor_hours_high")))
    conn.commit()

def save_tsb(conn, vid, d):
    if not d: return
    for t in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO tsb (vehicle_id, tsb_number, title, component, summary, date)
            VALUES (?,?,?,?,?,?)
        """, (vid, t.get("tsb_number") or t.get("number"), t.get("title"),
              t.get("component"), t.get("summary"), t.get("date") or t.get("issued_date")))
    conn.commit()

def save_common_problems(conn, vid, d):
    if not d: return
    for p in (d if isinstance(d, list) else []):
        conn.execute("""
            INSERT OR IGNORE INTO common_problems (vehicle_id, component, complaint_count, crash_count, injury_count, sample_description)
            VALUES (?,?,?,?,?,?)
        """, (vid, p.get("component"), p.get("complaint_count"),
              p.get("crash_count"), p.get("injury_count"), p.get("sample_description")))
    conn.commit()

SAVERS = {
    "oil-change": save_oil,
    "parts": save_parts,
    "maintenance": save_maintenance,
    "fluids": save_fluids,
    "torque-specs": save_torque,
    "recalls": save_recalls,
    "engine-specs": save_engine,
    "fuel-economy": save_fuel,
    "safety-ratings": save_safety,
    "warranty": save_warranty,
    "reliability": save_reliability,
    "service-costs": save_service_costs,
    "tsb": save_tsb,
    "common-problems": save_common_problems,
}

def pull_vehicle(conn, year, make, model):
    """Pull all endpoints for one vehicle. Returns vehicle_id or None."""
    # Step 1: Get vehicle ID
    result = api_get("vehicles", {"year": year, "make": make, "model": model})
    if not result:
        log.warning(f"  No match: {year} {make} {model}")
        return None

    # Pick the best match (prefer specific engine over generic)
    vehicles = result if isinstance(result, list) else [result]
    vehicle = next((v for v in vehicles if v.get("engine")), vehicles[0])
    vid = vehicle["id"]

    save_vehicle(conn, vid, year, make, model, vehicle.get("engine"), vehicle.get("trim"))
    log.info(f"  → ID {vid} ({vehicle.get('engine','?')})")

    # Step 2: Pull all endpoints
    for ep in ENDPOINTS:
        # Check if already pulled
        already = conn.execute(
            "SELECT status FROM pull_log WHERE vehicle_id=? AND endpoint=?", (vid, ep)
        ).fetchone()
        if already and already[0] == "ok":
            continue

        data = api_get(f"vehicles/{vid}/{ep}")
        status = "ok" if data is not None else "empty"

        if data and ep in SAVERS:
            try:
                SAVERS[ep](conn, vid, data)
            except Exception as e:
                log.error(f"    Save error for {ep}: {e}")
                status = "save_error"

        conn.execute(
            "INSERT OR REPLACE INTO pull_log VALUES (?,?,?,?)",
            (vid, ep, status, datetime.utcnow().isoformat())
        )
        conn.commit()

    return vid

def pull_dtc_codes(conn):
    """Pull common DTC codes — P0001 through P1999 and C/B/U ranges."""
    log.info("\n=== Pulling DTC Codes ===")
    # Common codes to pull
    codes = []
    # P codes: P0001-P0999 (OBDII standard), P1000-P1999 (manufacturer)
    for i in range(1, 800):  # most common range
        codes.append(f"P{i:04d}")
    # Common specific codes
    for c in ["P0420","P0430","P0300","P0301","P0302","P0303","P0304",
               "P0171","P0174","P0401","P0411","P0440","P0455","P0456",
               "P0500","P0505","P0600","P0700","P0740","P0750",
               "C0035","C0040","B1000","U0100","U0101"]:
        if c not in codes:
            codes.append(c)

    pulled = 0
    for code in codes:
        exists = conn.execute("SELECT 1 FROM dtc_codes WHERE code=?", (code,)).fetchone()
        if exists:
            continue
        data = api_get(f"diagnostics/{code}")
        if data:
            conn.execute("""
                INSERT OR IGNORE INTO dtc_codes VALUES (?,?,?,?,?,?,?)
            """, (code, data.get("description"), data.get("urgency"),
                  data.get("cost_low"), data.get("cost_high"),
                  json.dumps(data.get("possible_causes")),
                  json.dumps(data.get("systems"))))
            conn.commit()
            pulled += 1
        if pulled % 50 == 0 and pulled > 0:
            log.info(f"  DTCs pulled: {pulled}")

    log.info(f"  Total DTCs saved: {pulled}")

def main():
    log.info("=" * 60)
    log.info("Wrench Bulk Data Pull — Starting")
    log.info(f"Target vehicles: {len(TARGET_VEHICLES)}")
    log.info(f"Endpoints per vehicle: {len(ENDPOINTS)}")
    log.info(f"Estimated requests: ~{len(TARGET_VEHICLES) * (len(ENDPOINTS) + 1) + 800:,}")
    log.info("=" * 60)

    conn = sqlite3.connect(DB_FILE)
    setup_db(conn)

    success = 0
    for i, (year, make, model) in enumerate(TARGET_VEHICLES, 1):
        log.info(f"\n[{i}/{len(TARGET_VEHICLES)}] {year} {make} {model}")
        try:
            vid = pull_vehicle(conn, year, make, model)
            if vid:
                success += 1
        except Exception as e:
            log.error(f"  Failed: {e}")

        # Progress report every 20 vehicles
        if i % 20 == 0:
            elapsed = time.time() - start_time
            rate = request_count / elapsed * 60
            log.info(f"\n  ── Progress: {i}/{len(TARGET_VEHICLES)} vehicles, "
                     f"{request_count:,} requests, {rate:.0f} req/min ──\n")

    # Pull DTC codes
    pull_dtc_codes(conn)

    # Final report
    elapsed = time.time() - start_time
    log.info("\n" + "=" * 60)
    log.info("COMPLETE")
    log.info(f"  Vehicles pulled: {success}/{len(TARGET_VEHICLES)}")
    log.info(f"  Total requests: {request_count:,}")
    log.info(f"  Time elapsed: {elapsed/60:.1f} minutes")
    log.info(f"  Database: {DB_FILE}")
    log.info("=" * 60)

    conn.close()

if __name__ == "__main__":
    main()
