# Ford F-150 single-vehicle pilot: 2022 (id 12901, 14th gen).
# Source: 2022 Ford F-150 Owner's Manual (Capacities & Specifications chapter, p563-592).
# Multi-engine: 3.3L V6, 2.7L EcoBoost, 5.0L V8, 3.5L EcoBoost, 3.5L PowerBoost HEV, Raptor 3.5 HO.
# Ford specifics: DOT 4 LV brake, MERCON LV (10-speed auto), EPAS, lug 150 ft-lb, battery group 48/94R.
# NULL/gated: drain-plug torque, oil-filter torque, spark-plug gap, tire size+pressure (door placard).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_f150_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

VID=12901
SRC='owner-manual-verified'  # cite 2022 F-150 OM directly
MSRC="Ford Owner's Manual (2022 F-150, 14th gen)"

VISC='5W-20 (3.3L) / 5W-30 (2.7L EB, 3.5L EB, 5.0L V8, PowerBoost, Raptor)'
OIL_CW='6.0 qt (3.3L / 2.7L EB / 3.5L EB / PowerBoost) / 7.75 qt (5.0L V8)'
OEM='Motorcraft Synthetic Blend; 5W-20 (3.3L, WSS-M2C960-A1) / 5W-30 (others, WSS-M2C961-A1)'
COOLANT_TYPE='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
COOLANT_CAP='12.7 qt (3.3L) / 15.1 qt (2.7L EB) / 14.3 qt (3.5L EB) / 13.2 qt (5.0L V8) / 13.7 qt (Raptor)'
BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
TRANS='Motorcraft MERCON LV ATF (10-speed automatic)'
PS='Electric power steering (EPAS, no fluid)'

# AWD/4WD driveline fluids (Ford gives these)
DIFF=json.dumps([
    {"type":"transfer_case_4wd","fluid":"Motorcraft MERCON LV ATF; 1.5 qt (electronic/torque-on-demand) / 1.9 qt (2-speed)"},
    {"type":"front_axle_4wd","fluid":"1.8 qt (standard front axle)"},
])
# Motorcraft part numbers (per engine) - Ford OM provides these
SPARK_JSON=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-520","description":"3.3L V6","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-578","description":"2.7L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-588","description":"5.0L V8","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-596","description":"3.5L EcoBoost / PowerBoost / Raptor","is_oem":True},
])
BATT_NOTE=("Battery group 48 (Motorcraft BAGM-48H6-760, standard) / 94R (BAGM-94RH7-800, optional/HEV), per OM. "
           "Oil filter Motorcraft FL-500-S (most) / FL-2062-A (2.7L EB); air filter FA-1883; cabin FP-92. "
           "NOT in OM (pending): spark-plug GAP (part # given), drain-plug torque, oil-filter torque. "
           "Tire size & pressure are on the driver door placard (config-dependent), not in the OM body.")

db=sqlite3.connect(DB); c=db.cursor()
for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
    c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(VID,))

c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
    capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
    (VID,VISC,None,OIL_CW,None,OEM,None,None,None,None,None,SRC))

c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
    coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
    VALUES (?,?,?,?,?,?,?,?,?)""",
    (VID,TRANS,None,BRAKE,COOLANT_TYPE,COOLANT_CAP,PS,DIFF,SRC))

# tire_size/pressure NULL (door placard); battery_group from Motorcraft part#; spark gap NULL
c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
    battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
    air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
    battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (VID,None,None,None,'48 / 94R',None,None,None,None,SPARK_JSON,None,None,None,None,
     'Tire size & pressure: see driver door placard (config-dependent) - not in OM body; pending.',
     BATT_NOTE,None,None,None,None,SRC))

# torque: Ford OM gives LUG only (150 ft-lb). Drain/oil-filter NOT in OM -> not written (gated/pending).
c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
          (VID,'lug_nut',150.0,204.0,"150 ft-lb (204 N-m) cold, per owner's manual p650",'owner-manual-verified'))

# maintenance: Ford uses Intelligent Oil-Life Monitor
for mi,mo,desc in [
    (None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor (oil-life based); follow message center'),
    (None,None,'Brake fluid - per Ford scheduled maintenance')]:
    pass  # keep minimal; Ford intervals are oil-life based
c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
    VALUES ((SELECT COALESCE(MAX(id),0)+1 FROM maintenance),?,?,?,?,?,?,?,?,?)""",
    (VID,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor (oil-life based); follow message center',MSRC,'standard',None,None,None))

db.commit()
print('\nVerify 2022 F-150 (id %d):'%VID)
o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(VID,)).fetchone()
f=c.execute('SELECT transmission_fluid,brake_fluid,power_steering_fluid,coolant_capacity FROM fluids WHERE vehicle_id=?',(VID,)).fetchone()
p=c.execute('SELECT battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(VID,)).fetchone()
tq=c.execute('SELECT component,torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(VID,)).fetchall()
print('  oil visc:', o[0]); print('  oil cap :', o[1]); print('  coolant :', f[3])
print('  trans   :', f[0]); print('  brake   :', f[1]); print('  PS      :', f[2])
print('  battery_group:', p[0], '| tire_size:', p[1], '| plug_gap:', p[2])
print('  torque  :', dict((x[0],x[1]) for x in tq))
db.close(); print('\nDONE.')
