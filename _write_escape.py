# Ford Escape 4th gen (2020-2026) bulk — 6 rows.
# Source: 2024 Escape OM (4th-gen rep, Capacities & Specs p415-430); EPA-confirmed roster STABLE
# across 2020-2026: 1.5L EcoBoost / 2.0L EcoBoost / 2.5L Duratec hybrid (FHEV/PHEV) every year.
# Ford specifics CONFIRMED (not assumed): 8-speed MERCON ULV (gas) / eCVT (hybrid) - NOT F-150's
# MERCON LV; lug 100 ft-lb (NOT 150); tire pressure 35 (in-OM); EPAS; battery 48/99R; DOT 4 LV.
# NULL/gated: drain-plug torque, oil-filter torque, spark-plug gap, tire SIZE (trim placard).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_escape_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

SRC='owner-manual-verified (per 2024 Escape OM, 4th gen; EPA-confirmed roster 1.5T/2.0T/2.5 hybrid 2020-2026)'
MSRC="Ford Owner's Manual (2024 Escape, 4th gen)"
TARGETS=[(12762,2020),(12830,2021),(12897,2022),(12962,2023),(13094,2025),(13160,2026)]

VISC='0W-20 (1.5L EB, 2.5L hybrid) / 5W-30 (2.0L EB)'
OIL_CW='5.0 qt (1.5L EB) / 6.1 qt (2.0L EB) / 5.7 qt (2.5L hybrid)'
OEM='Motorcraft 0W-20 (1.5L/hybrid, WSS-M2C962-A1) / 5W-30 (2.0L, WSS-M2C961-A1)'
COOLANT_TYPE='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
COOLANT_CAP='8.0 qt (1.5L EB) / 9.0 qt (2.0L EB) / hybrid dual-circuit (FHEV 5.0+9.6 qt; PHEV 6.6+10.1 qt)'
BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
TRANS='Motorcraft MERCON ULV - 8-speed automatic (8F35, gas) / eCVT 1-speed (2.5L hybrid)'
PS='Electric power steering (EPAS, no fluid)'

SPARK_JSON=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-597-X","description":"1.5L / 2.0L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-530-X","description":"2.5L Duratec hybrid","is_oem":True},
])
TIRE_NOTE='Tire SIZE is trim-dependent (placard, not in OM) - pending. Tire pressure 35 psi (P-metric) per OM p389.'
BATT_NOTE=("Battery group 48 (Motorcraft BAGM-48H6-760; 1.5L/2.0L) / 99R (BXT-99RT4-A; 2.5L hybrid 12V), per OM. "
           "Oil filter Motorcraft FL-910-S (1.5L/hybrid) / FL-2127 (2.0L); air FA-2065/2064/1948; cabin FP-100-A. "
           "NOT in OM (pending): spark-plug GAP (part # given), drain-plug torque, oil-filter torque, tire size.")

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year in TARGETS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,VISC,None,OIL_CW,None,OEM,None,None,None,None,None,SRC))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,TRANS,None,BRAKE,COOLANT_TYPE,COOLANT_CAP,PS,None,SRC))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,'48 / 99R',None,None,35,35,SPARK_JSON,None,None,None,None,TIRE_NOTE,
         BATT_NOTE,None,None,None,None,SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
              (vid,'lug_nut',100.0,135.0,"100 ft-lb (135 N-m), M12x1.5, per owner's manual p411",'owner-manual-verified'))
    c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (nid,vid,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor (oil-life based); follow message center',MSRC,'standard',None,None,None)); nid+=1
    print('  wrote %d (%s)'%(vid,year))

db.commit()
print('\nVerify:')
for vid,year in TARGETS:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    f=c.execute('SELECT transmission_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT tire_pressure_front,battery_group FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d(%s): oil=%s | trans=%s | PS=%s | tire_psi=%s batt=%s lug=%s'%(vid,year,o,f[0][:40],f[1][:20],p[0],p[1],tq))
db.close(); print('\nDONE.')
