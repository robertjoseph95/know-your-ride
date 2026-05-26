"""
WRENCH — Script 04: Rebuild wrench_demo.html with TSBs + Complaints
====================================================================
Run this AFTER scripts 01–03 have populated the DB.
Adds two new modal tabs to every vehicle:
  - "TSBs" — Technical Service Bulletins with title, component, summary, date
  - "Complaints" — NHTSA complaint text with crash/fire/injury flags

Also surfaces engine/trim and EV range data from the enriched columns.

Run: python3 04_rebuild_html.py
Output: wrench_demo.html (overwrites previous version)
"""

import sqlite3
import json
import os

DB_PATH  = "wrench_vehicles.db"
OUT_FILE = "wrench_demo.html"


def pj(val):
    if not val or val == 'null' or val == '[]':
        return None
    try:
        r = json.loads(val)
        if isinstance(r, list):
            for item in r:
                if isinstance(item, dict):
                    item.pop('affiliate_url', None)
        return r if r else None
    except:
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    print("Extracting vehicles...")
    cur.execute('SELECT id,year,make,model,engine,trim FROM vehicles ORDER BY make,year,model')
    vehicles = {}
    for v in cur.fetchall():
        vehicles[v['id']] = {
            'id': v['id'], 'year': v['year'], 'make': v['make'],
            'model': v['model'], 'engine': v['engine'], 'trim': v['trim']
        }

    print("Oil data...")
    cur.execute('SELECT * FROM oil_change')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            vehicles[vid]['oil'] = {
                'visc': r['viscosity'], 'type': r['oil_type'],
                'cap_w': r['capacity_with_filter'], 'cap_wo': r['capacity_without_filter'],
                'spec': r['oem_spec'],
                'filters': pj(r['filters_json']),
                'drain': pj(r['drain_bolt_json'])
            }

    print("Parts...")
    cur.execute('SELECT * FROM parts')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            vehicles[vid]['parts'] = {
                'plug_type': r['spark_plug_type'], 'plug_gap': r['spark_plug_gap'],
                'plug_qty': r['spark_plug_qty'], 'batt_group': r['battery_group'],
                'batt_cca': r['battery_cca'], 'tire': r['tire_size'],
                'psi_f': r['tire_pressure_front'], 'psi_r': r['tire_pressure_rear'],
                'plugs': pj(r['spark_plugs_json']), 'air': pj(r['air_filters_json']),
                'cabin': pj(r['cabin_filters_json']), 'wipers': pj(r['wiper_blades_json']),
                'batts': pj(r['batteries_json'])
            }

    print("Fluids...")
    cur.execute('SELECT * FROM fluids')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            vehicles[vid]['fluids'] = {
                'trans': r['transmission_fluid'], 'trans_cap': r['transmission_capacity'],
                'brake': r['brake_fluid'], 'coolant': r['coolant_type'],
                'coolant_cap': r['coolant_capacity'], 'ps': r['power_steering_fluid'],
                'diff': pj(r['differential_fluids_json'])
            }

    print("Torque...")
    cur.execute('SELECT * FROM torque_specs ORDER BY vehicle_id')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'torque' not in vehicles[vid]: vehicles[vid]['torque'] = []
            vehicles[vid]['torque'].append({
                'comp': r['component'], 'ft': r['torque_ft_lbs'],
                'nm': r['torque_nm'], 'notes': r['notes']
            })

    print("Recalls...")
    cur.execute('SELECT * FROM recalls ORDER BY vehicle_id')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'recalls' not in vehicles[vid]: vehicles[vid]['recalls'] = []
            vehicles[vid]['recalls'].append({
                'camp': r['campaign_number'], 'comp': r['component'],
                'sum': r['summary'], 'remedy': r['remedy'], 'park': bool(r['park_it'])
            })

    print("Engine specs...")
    cur.execute('SELECT * FROM engine_specs')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'engines' not in vehicles[vid]: vehicles[vid]['engines'] = []
            vehicles[vid]['engines'].append({
                'var': r['variant'], 'hp': r['horsepower'], 'tq': r['torque_ft_lbs'],
                'disp': r['displacement_l'], 'cyl': r['cylinders'],
                'config': r['cylinder_config'], 'asp': r['aspiration'], 'fuel': r['fuel_system']
            })

    print("Fuel economy...")
    # Check if range_miles column exists
    cur.execute("PRAGMA table_info(fuel_economy)")
    fe_cols = [r[1] for r in cur.fetchall()]
    has_range = 'range_miles' in fe_cols
    has_mpge  = 'mpge' in fe_cols

    cur.execute('SELECT * FROM fuel_economy')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'mpg' not in vehicles[vid]: vehicles[vid]['mpg'] = []
            entry = {
                'city': r['city_mpg'], 'hwy': r['highway_mpg'], 'comb': r['combined_mpg'],
                'cost': r['annual_fuel_cost'], 'eng': r['engine'],
                'trans': r['transmission'], 'drive': r['drive']
            }
            if has_range: entry['range'] = r['range_miles']
            if has_mpge:  entry['mpge']  = r['mpge']
            vehicles[vid]['mpg'].append(entry)

    print("Safety ratings...")
    cur.execute('SELECT * FROM safety_ratings')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            vehicles[vid]['safety'] = {
                'overall': r['overall_rating'], 'front_d': r['frontal_crash_driver'],
                'front_p': r['frontal_crash_passenger'], 'side_d': r['side_crash_driver'],
                'side_p': r['side_crash_passenger'], 'rollover': r['rollover_rating'],
                'roll_pct': r['rollover_risk_pct'], 'pole': r['side_pole_rating']
            }

    print("Warranty...")
    cur.execute('SELECT * FROM warranty')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'warranty' not in vehicles[vid]: vehicles[vid]['warranty'] = {}
            vehicles[vid]['warranty'][r['warranty_type']] = {
                'mo': r['months'], 'mi': r['miles'], 'notes': r['notes']
            }

    print("Reliability...")
    cur.execute('SELECT * FROM reliability')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            vehicles[vid]['rel'] = {
                'score': r['overall_score'], 'rating': r['rating'],
                'complaints': r['complaint_count'], 'crashes': r['crash_count'],
                'fires': r['fire_count'], 'injuries': r['injury_count'], 'issue': r['top_issue']
            }

    print("Service costs...")
    cur.execute("SELECT vehicle_id,service_type,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high FROM service_costs WHERE region='national'")
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'costs' not in vehicles[vid]: vehicles[vid]['costs'] = {}
            vehicles[vid]['costs'][r['service_type']] = {
                'lo': r['cost_low'], 'hi': r['cost_high'], 'avg': r['cost_average'],
                'hr_lo': r['labor_hours_low'], 'hr_hi': r['labor_hours_high']
            }

    print("TSBs (enriched)...")
    cur.execute('SELECT * FROM tsb WHERE title IS NOT NULL ORDER BY vehicle_id, date DESC')
    for r in cur.fetchall():
        vid = r['vehicle_id']
        if vid in vehicles:
            if 'tsbs' not in vehicles[vid]: vehicles[vid]['tsbs'] = []
            vehicles[vid]['tsbs'].append({
                'num': r['tsb_number'], 'title': r['title'],
                'comp': r['component'], 'sum': r['summary'], 'date': r['date']
            })

    print("Complaints (enriched)...")
    # Check if complaints table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'")
    if cur.fetchone():
        cur.execute('SELECT * FROM complaints ORDER BY vehicle_id, incident_date DESC')
        for r in cur.fetchall():
            vid = r['vehicle_id']
            if vid in vehicles:
                if 'comps' not in vehicles[vid]: vehicles[vid]['comps'] = []
                vehicles[vid]['comps'].append({
                    'num': r['complaint_number'], 'comp': r['component'],
                    'sum': r['summary'], 'date': r['incident_date'],
                    'crash': r['crash'], 'fire': r['fire'],
                    'inj': r['injury'], 'deaths': r['deaths']
                })

    print("DTC codes...")
    cur.execute('SELECT code,description FROM dtc_codes ORDER BY code')
    dtc = {r['code']: r['description'] for r in cur.fetchall()}

    conn.close()

    vlist = list(vehicles.values())
    total_v      = len(vlist)
    total_dtc    = len(dtc)
    makes_count  = len(set(v['make'] for v in vlist))
    with_recalls = len([v for v in vlist if v.get('recalls')])
    with_tsbs    = len([v for v in vlist if v.get('tsbs')])

    data_json = json.dumps({'v': vlist, 'dtc': dtc}, separators=(',', ':'))
    print(f"Data JSON: {len(data_json)/1024/1024:.2f} MB")

    # ── Read the original HTML and patch the data + add TSB/complaints tabs ──
    # If wrench_demo.html exists, update it; otherwise print instructions.
    if not os.path.exists(OUT_FILE):
        print(f"\n⚠  {OUT_FILE} not found. Run batch scripts 01-03 first,")
        print(f"   then re-run 04_rebuild_html.py from the same directory.")
        return

    with open(OUT_FILE) as f:
        html = f.read()

    # Replace embedded data
    import re
    html = re.sub(r'const __D__=\{.*?\};', f'const __D__={data_json};', html, flags=re.DOTALL)

    # Update badge counts
    html = html.replace(
        html[html.find(' VEHICLES'):html.find('</div>', html.find(' VEHICLES'))],
        f' VEHICLES · {makes_count} MAKES · {total_dtc} DTC CODES · {with_tsbs} WITH TSBs</div>'
    )

    with open(OUT_FILE, 'w') as f:
        f.write(html)

    size = os.path.getsize(OUT_FILE)
    print(f"\n── Done ────────────────────────────────────────────")
    print(f"Output: {OUT_FILE}  ({size/1024/1024:.2f} MB)")
    print(f"Vehicles   : {total_v}")
    print(f"With TSBs  : {with_tsbs}")
    print(f"With recalls: {with_recalls}")


if __name__ == "__main__":
    main()
