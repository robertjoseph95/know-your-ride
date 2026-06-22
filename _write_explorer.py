# Ford Explorer 6th gen (2020-2026) - 7 rows.
# Source: 2022 Explorer OM (self-ID p1, Capacities & Specs pp.385-409; lug p380; PS p336; trans-ID p23).
# PER-YEAR roster (EPA-confirmed, hybrid DROPPED 2024 - standing rule, NOT generation-stable):
#   2020-2023: 2.3L EcoBoost / 3.0L EcoBoost / 3.3L Hybrid  (TRIPLE)
#   2024-2026: 2.3L EcoBoost / 3.0L EcoBoost                (DUAL - hybrid stripped)
# Ford specifics CONFIRMED by reading (not assumed): MERCON ULV 10-speed (10R60); hybrid = 10-speed
#   MODULAR-hybrid (NOT the Escape's eCVT); lug 150 (M14x1.5, like F-150 not Escape's 100);
#   tire pressure PLACARD (like F-150, not Escape's in-OM 35); EPAS no fluid; DOT 4 LV; battery 48.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_explorer_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

MSRC="Ford Owner's Manual (2022 Explorer, 6th gen)"
SRC_TRI='owner-manual-verified (per 2022 Explorer OM, 6th gen pp.385-409; engines 2.3T/3.0T/3.3 hybrid)'
SRC_DUO='owner-manual-verified (per 2022 Explorer OM, 6th gen pp.385-409; 2.3T/3.0T - hybrid dropped 2024, engines unchanged)'

# ---- engine-divergent strings ----
VISC_TRI='5W-30 (2.3L EB, 3.0L EB) / 5W-20 (3.3L hybrid)'
VISC_DUO='5W-30 (2.3L EB, 3.0L EB)'
OILCW_TRI='5.2 qt (2.3L EB) / 6.0 qt (3.0L EB) / 6.0 qt (3.3L hybrid)'
OILCW_DUO='5.2 qt (2.3L EB) / 6.0 qt (3.0L EB)'
OEM_TRI='Motorcraft 5W-30 (2.3L/3.0L, WSS-M2C961-A1) / 5W-20 (3.3L hybrid, WSS-M2C960-A1)'
OEM_DUO='Motorcraft 5W-30 (2.3L/3.0L, WSS-M2C961-A1)'
COOL_CAP_TRI='2.3L EB 14.1/15.2 qt / 3.0L EB 15.5/18.0 qt / 3.3L hybrid 13.9/16.4 qt + HEV battery/motor loop 4.6 qt (dual-circuit)'
COOL_CAP_DUO='2.3L EB 14.1/15.2 qt / 3.0L EB 15.5/18.0 qt'
TRANS_CAP_TRI='12.6 qt (2.3L/3.0L) / 13.7 qt (3.3L hybrid) - dry fill'
TRANS_CAP_DUO='12.6 qt (2.3L/3.0L) - dry fill'

COOLANT_TYPE='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
TRANS_TRI='Motorcraft MERCON ULV - 10-speed automatic (10R60); 3.3L hybrid = 10-speed modular-hybrid (NOT an eCVT)'
TRANS_DUO='Motorcraft MERCON ULV - 10-speed automatic (10R60)'
PS='Electric power steering (EPAS, no fluid - OM: no reservoir to check or fill)'
DIFF_JSON=json.dumps({"transfer_case":"Motorcraft MERCON LV 1.1 qt (AWD, WSS-M2C938-A)",
                      "front_axle":"0.6 qt (AWD)","rear_axle":"1.9 qt (gas) / 1.7 qt (hybrid)"})

SPARK_TRI=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-594","description":"2.3L / 3.0L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-520","description":"3.3L hybrid","is_oem":True},
])
SPARK_DUO=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-594","description":"2.3L / 3.0L EcoBoost","is_oem":True},
])
TIRE_NOTE='Tire size & pressure are trim-dependent (door-pillar Tire Label/placard, not in OM body) - pending.'
BATT_NOTE_TRI=("Battery group 48 (Motorcraft BAGM-48H6-760; incl. 3.3L hybrid 12V aux), per OM p383-384. "
    "Oil filter Motorcraft FL-910-S (2.3L) / FL-2062-A (3.0L) / FL-500-S (3.3L hybrid); "
    "air FA-1884 (2.3L/3.0L) / FA-1947 (3.3L hybrid). "
    "NOT in OM (pending): spark-plug GAP (part # given), drain-plug torque, oil-filter torque, tire size/pressure.")
BATT_NOTE_DUO=("Battery group 48 (Motorcraft BAGM-48H6-760), per OM p383-384. "
    "Oil filter Motorcraft FL-910-S (2.3L) / FL-2062-A (3.0L); air FA-1884. "
    "NOT in OM (pending): spark-plug GAP (part # given), drain-plug torque, oil-filter torque, tire size/pressure.")

# (id, year, tri?)
TARGETS=[(12764,2020,True),(12832,2021,True),(12899,2022,True),(12964,2023,True),
         (13030,2024,False),(13096,2025,False),(13162,2026,False)]

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year,tri in TARGETS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    SRC = SRC_TRI if tri else SRC_DUO
    VISC=VISC_TRI if tri else VISC_DUO; OILCW=OILCW_TRI if tri else OILCW_DUO; OEM=OEM_TRI if tri else OEM_DUO
    COOL=COOL_CAP_TRI if tri else COOL_CAP_DUO; TCAP=TRANS_CAP_TRI if tri else TRANS_CAP_DUO
    TRANS=TRANS_TRI if tri else TRANS_DUO; SPARK=SPARK_TRI if tri else SPARK_DUO
    BNOTE=BATT_NOTE_TRI if tri else BATT_NOTE_DUO
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,SRC))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,TRANS,TCAP,BRAKE,COOLANT_TYPE,COOL,PS,DIFF_JSON,SRC))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,'48',None,None,None,None,SPARK,None,None,None,None,TIRE_NOTE,
         BNOTE,None,None,None,None,SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid,'lug_nut',150.0,204.0,"150 lb-ft (204 N-m), M14x1.5, per owner's manual p380",'owner-manual-verified'))
    c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (nid,vid,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor (oil-life based); follow message center',MSRC,'standard',None,None,None)); nid+=1
    print('  wrote %d (%s) %s'%(vid,year,'3-way' if tri else '2-way'))

db.commit()
print('\nVerify:')
for vid,year,tri in TARGETS:
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    f=c.execute('SELECT transmission_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()[0]
    tq=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    hyb='HYBRID' if 'hybrid' in o.lower() else 'no-hyb'
    print('  %d(%s): %s | visc=%s | lug=%s'%(vid,year,hyb,o,tq))
db.close(); print('\nDONE.')
