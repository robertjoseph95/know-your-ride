# Ford F-150 bulk - 13th gen (2015-2020) + 14th gen (2021,2023-2026). 11 rows (2022 pilot already done).
# Sources: 2016 OM (13th early), 2017 OM (trans transition confirm), 2018 OM (13th late + diesel), 2022 pilot (14th).
# Per-year EPA roster; engine-specific oil travels with the engine, generation coolant with the generation.
# KEY confirmed-by-reading: 13th gen=ORANGE coolant + MERCON LV + 6-spd(6R80)->mixed 6/10-spd; 14th gen=YELLOW
#   + 10-spd(10R80). 5.0L=5W-20 (13th, 7.7->8.8 qt) vs 5W-30 7.75qt (14th). Lug 150, EPAS, DOT 4 LV all gens.
# 5.2L Raptor R (2023+) GATED (no OM read - not fabricated). No Lightning EV rows exist.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_f150bulk_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
PS='Electric power steering (EPAS, no fluid)'
BATT='48 / 94R'
ORANGE='Motorcraft Orange Prediluted Antifreeze/Coolant (WSS-M97B44-D2)'
YELLOW='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
DIFF13=json.dumps({"transfer_case":"Motorcraft Transfer Case Fluid XL-12, 1.5 qt (ESOF) / MERCON LV (ToD)",
    "front_axle":"SAE 80W-90 (WSP-M2C197-A), 1.7 L (4WD)","rear_axle":"SAE 75W-85 (WSS-M2C942-A), 2.6 L"})

SPARK_E=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-542","description":"2.7L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-534","description":"3.5L V6 NA (TiVCT)","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-520","description":"3.5L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-519","description":"5.0L V8","is_oem":True}])
SPARK_PILOT=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-520","description":"3.3L V6","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-578","description":"2.7L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-588","description":"5.0L V8","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-596","description":"3.5L EcoBoost / PowerBoost / Raptor","is_oem":True}])

GATED_NOTE="NOT in OM (pending): spark-plug GAP, drain-plug torque, oil-filter torque; tire size & pressure (door placard - truck has many configs)."

# Each spec set: (visc, oilcw, oem, cool_type, cool_cap, trans, trans_cap, spark_json, src, batt_note, diff_json)
def S(**k): return k

# 13th-gen EARLY 2015-2016 (6-speed)
E13=S(visc='5W-30 (2.7L EB, 3.5L EB) / 5W-20 (3.5L NA, 5.0L V8)',
  oilcw='6.0 qt (2.7L EB) / 6.3 qt (3.5L NA) / 6.0 qt (3.5L EB) / 7.7 qt (5.0L V8)',
  oem='Motorcraft 5W-30 (2.7L/3.5L EcoBoost, WSS-M2C946-A) / 5W-20 (3.5L NA, 5.0L V8, WSS-M2C945-A)',
  cool_type=ORANGE,
  cool_cap='16.4 qt (2.7L EB) / 15.1 qt (3.5L NA) / 15.6 qt (3.5L EB) / 15.9 qt (5.0L V8)',
  trans='Motorcraft MERCON LV ATF - 6-speed automatic (6R80)', trans_cap='13.1 qt (dry fill)',
  spark=SPARK_E, src='owner-manual-verified (per 2016 F-150 OM, 13th gen; 2.7T/3.5NA/3.5T/5.0)',
  batt='Battery group 48 (Motorcraft BAGM-48H6-760) / 94R (BAGM-94RH7-800, King Ranch/Lariat/Platinum), per OM. '
       'Oil filter FL-2062 (2.7L EB) / FL-500-S (3.5L NA, 3.5L EB, 5.0L V8); air FA-1883. '+GATED_NOTE, diff=DIFF13)

# 13th-gen 2017 (6-speed + 10-speed on 3.5EB) - confirmed via 2017 OM
T17=dict(E13); T17.update(
  trans='Motorcraft MERCON LV ATF - 6-speed automatic (6R80); 10-speed (10R80) on 3.5L EcoBoost',
  src='owner-manual-verified (per 2016+2017 F-150 OM, 13th gen; 2017 trans transition confirmed)')

# 13th-gen LATE 2018-2020 (6-spd 3.3 base / 10-spd others) + diesel
L13=S(visc='5W-30 (2.7L EB, 3.5L EB) / 5W-30 Diesel (3.0L Power Stroke, WSS-M2C214-B1) / 5W-20 (3.3L NA, 5.0L V8)',
  oilcw='6.0 qt (2.7L EB) / 6.5 qt (3.0L diesel) / 6.0 qt (3.3L NA) / 6.0 qt (3.5L EB) / 8.8 qt (5.0L V8)',
  oem='Motorcraft 5W-30 (gas EcoBoost) / 5W-30 Diesel (3.0L Power Stroke, WSS-M2C214-B1) / 5W-20 (3.3L, 5.0L)',
  cool_type=ORANGE,
  cool_cap='3.3L NA 13.6 qt / 3.0L diesel 13.7 qt / 3.5L EB 15.2 qt / 5.0L V8 13.9 qt',
  trans='Motorcraft MERCON LV ATF - 6-speed (6R80, 3.3L base) / 10-speed (10R80, 2.7L EB/3.0L diesel/3.5L EB/5.0L V8)',
  trans_cap='13.1 qt (dry fill)', spark=None,
  src='owner-manual-verified (per 2018 F-150 OM, 13th gen late; +3.0L Power Stroke diesel +3.3L Duratec)',
  batt='Battery group 48 / 94R, per OM. 2.7L EB: oil filter FL-2062, spark SP-542, air FA-1883. '
       '3.0L Power Stroke diesel: 5W-30 Diesel oil (WSS-M2C214-B1), DEF tank 22.5 qt, fuel 26 gal. '+GATED_NOTE, diff=DIFF13)

# 14th-gen 2021 (Yellow, 10-spd) + diesel (engine-specific) + Yellow coolant (generation)
G21=S(visc='5W-30 (2.7L EB, 3.5L EB, 5.0L V8, PowerBoost) / 5W-30 Diesel (3.0L Power Stroke) / 5W-20 (3.3L)',
  oilcw='6.0 qt (2.7L EB, 3.3L, 3.5L EB, PowerBoost) / 6.5 qt (3.0L diesel) / 7.75 qt (5.0L V8)',
  oem='Motorcraft 5W-30 / 5W-30 Diesel (3.0L, WSS-M2C214-B1) / 5W-20 (3.3L)', cool_type=YELLOW,
  cool_cap='12.7 qt (3.3L) / 15.1 qt (2.7L EB) / 14.3 qt (3.5L EB) / 13.2 qt (5.0L V8) / 13.7 qt (3.0L diesel) / Raptor 13.7 qt; PowerBoost dual-circuit',
  trans='Motorcraft MERCON LV ATF (10-speed automatic, 10R80)', trans_cap=None, spark=SPARK_PILOT,
  src='owner-manual-verified (per 2022 F-150 OM, 14th gen; +3.0L diesel last year 2021, engine spec from 2018 OM)',
  batt='Battery group 48 / 94R. 3.0L Power Stroke diesel (last year 2021): 5W-30 Diesel oil (WSS-M2C214-B1), DEF 22.5 qt. '
       'Oil filter FL-500-S (most) / FL-2062-A (2.7L EB). '+GATED_NOTE, diff=DIFF13)

# 14th-gen 2023 (Yellow, 10-spd) = pilot 5 engines; 5.2 Raptor R GATED
G23=S(visc='5W-20 (3.3L) / 5W-30 (2.7L EB, 3.5L EB, 5.0L V8, PowerBoost)',
  oilcw='6.0 qt (3.3L / 2.7L EB / 3.5L EB / PowerBoost) / 7.75 qt (5.0L V8)',
  oem='Motorcraft 5W-20 (3.3L) / 5W-30 (others)', cool_type=YELLOW,
  cool_cap='12.7 qt (3.3L) / 15.1 qt (2.7L EB) / 14.3 qt (3.5L EB) / 13.2 qt (5.0L V8); PowerBoost dual-circuit',
  trans='Motorcraft MERCON LV ATF (10-speed automatic, 10R80)', trans_cap=None, spark=SPARK_PILOT,
  src='owner-manual-verified (per 2022 F-150 OM, 14th gen; 5.2L Raptor R present but specs gated - not in OM)',
  batt='Battery group 48 / 94R. Oil filter FL-500-S (most) / FL-2062-A (2.7L EB). '
       '5.2L supercharged Raptor R (halo trim): specs PENDING its own manual - not listed (not fabricated). '+GATED_NOTE, diff=DIFF13)

# 14th-gen 2024-2026 (Yellow, 10-spd) - NO 3.3; 5.2 Raptor R GATED
G24=S(visc='5W-30 (2.7L EB, 3.5L EB, 5.0L V8, PowerBoost)',
  oilcw='6.0 qt (2.7L EB, 3.5L EB, PowerBoost) / 7.75 qt (5.0L V8)',
  oem='Motorcraft 5W-30 (2.7L/3.5L EcoBoost, 5.0L V8, PowerBoost)', cool_type=YELLOW,
  cool_cap='15.1 qt (2.7L EB) / 14.3 qt (3.5L EB) / 13.2 qt (5.0L V8); PowerBoost dual-circuit',
  trans='Motorcraft MERCON LV ATF (10-speed automatic, 10R80)', trans_cap=None,
  spark=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-578","description":"2.7L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-588","description":"5.0L V8","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-596","description":"3.5L EcoBoost / PowerBoost","is_oem":True}]),
  src='owner-manual-verified (per 2022 F-150 OM, 14th gen; 3.3L dropped 2024; 5.2L Raptor R gated)',
  batt='Battery group 48 / 94R. Oil filter FL-500-S (most) / FL-2062-A (2.7L EB). '
       '5.2L supercharged Raptor R (halo trim): specs PENDING its own manual - not listed (not fabricated). '+GATED_NOTE, diff=DIFF13)

# (id, year, specset)
ROWS=[(12102,2015,E13),(12228,2016,E13),(12360,2017,T17),
      (12496,2018,L13),(12641,2019,L13),(12766,2020,L13),
      (12834,2021,G21),(12966,2023,G23),
      (13032,2024,G24),(13098,2025,G24),(13164,2026,G24)]
MSRC="Ford Owner's Manual (F-150, per generation: 2016/2017/2018 OM 13th gen, 2022 OM 14th gen)"

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for vid,year,s in ROWS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(vid,s['visc'],None,s['oilcw'],None,s['oem'],None,None,None,None,None,s['src']))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",(vid,s['trans'],s['trans_cap'],BRAKE,s['cool_type'],s['cool_cap'],PS,s['diff'],s['src']))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,BATT,None,None,None,None,s['spark'],None,None,None,None,
         'Tire size & pressure are config-dependent (door placard, not in OM body) - pending.',s['batt'],None,None,None,None,s['src']))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',150.0,204.0,"150 lb-ft (204 N-m), M14x1.5, per owner's manual",'owner-manual-verified'))
    c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",(nid,vid,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor; follow message center',MSRC,'standard',None,None,None)); nid+=1
    g='13th' if year<=2020 else '14th'
    print('  wrote %d (%s, %s gen)'%(vid,year,g))

db.commit()
print('\nVerify (coolant color + trans must differ by gen):')
for vid,year,s in ROWS:
    f=c.execute('SELECT coolant_type,transmission_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    col='ORANGE' if 'Orange' in f[0] else 'YELLOW'
    dz='+diesel' if 'Diesel' in o else ''
    print('  %d(%s): %s | %s %s'%(vid,year,col,f[1][:48],dz))
db.close(); print('\nDONE.')
