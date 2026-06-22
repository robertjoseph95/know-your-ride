# Ford Mustang gas coupe - 5 rows. S550 (2020-2022) + S650 (2025-2026). Mach-E NOT touched (EV, queued).
# Sources: 2022 Mustang OM (S550, self-ID p1, Capacities pp.343-369; lug p340; PS p206)
#   + 2025 Mustang S650 OM (Edition 202407; Capacities pp.291-297; lug p375; PS p189).
# Per-engine 2.3T / 5.0 (V6 dropped 2018, none in scope). 5.2 GTD/Shelby halo GATED.
# Mustang divergences READ: manual fluid varies by gearbox (MT82=DCT fluid XT-11-QDC; Tremec=MERCON LV);
#   battery 96R (S550) vs not-in-OM (S650); coolant Yellow; auto=MERCON LV (not CD6 ULV); oil caps shrank S550->S650.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_mustang_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
PS='Electric power steering (EPAS, no fluid)'
COOLANT_TYPE='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
# Transmission string (same fluid set both gens; the gearbox-dependent manual fluid is the key Mustang quirk)
TRANS=('Automatic: Motorcraft MERCON LV ATF - 10-speed (10R80). '
       'Manual: Motorcraft Dual Clutch Transmission Fluid (XT-11-QDC, MT82 6-speed: 2.3L & base 5.0 GT) '
       '/ MERCON LV (Tremec TR-3160 6-speed: 5.0 Performance Pack/Mach 1)')
DIFF=json.dumps({"rear_axle":"Motorcraft SAE 75W-85 Synthetic Hypoid (WSS-M2C942-A) + limited-slip Friction Modifier XL-3 (EST-M2C118-A)"})
TIRE_NOTE='Tire size & pressure are config-dependent (driver-side B-pillar Tire Label/placard, not in OM body) - pending.'

# S550 (2020-2022)
S550=dict(
  visc='5W-30 (2.3L EcoBoost, 5.0L V8; 5W-50 for track use)',
  oilcw='6.0 qt (2.3L EcoBoost) / 10.0 qt (5.0L V8)',
  oem='Motorcraft 5W-30 (WSS-M2C961-A1); track 5W-50 (WSS-M2C931-C)',
  coolcap='9.5 qt (2.3L EcoBoost) / 15.2 qt (5.0L V8)',
  spark=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-550","description":"2.3L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-589","description":"5.0L V8","is_oem":True}]),
  batt='96R',
  bnote=('Battery group 96R (Motorcraft BXT-96R-590), per OM p343. Oil filter FL-910-S (2.3L EB) / FL-500-S (5.0L V8); '
    'air FA-1918; cabin FP-78. Rear axle 75W-85 + limited-slip friction modifier. '
    'NOT in OM (pending): spark-plug GAP, drain-plug torque, oil-filter torque, tire size/pressure (B-pillar placard). '
    '5.2L GTD/Shelby halo specs not covered by this OM - gated.'),
  src='owner-manual-verified (per 2022 Mustang OM, S550; 2.3L EcoBoost + 5.0L V8)')

# S650 (2025-2026) - oil caps shrank; battery not in OM
S650=dict(
  visc='5W-30 (2.3L EcoBoost, 5.0L V8)',
  oilcw='5.7 qt (2.3L EcoBoost) / 9.5 qt (5.0L V8)',
  oem='Motorcraft 5W-30 (WSS-M2C961-A1)',
  coolcap=None,
  spark=json.dumps([
    {"brand":"Motorcraft","part_number":"SP-597-X","description":"2.3L EcoBoost","is_oem":True},
    {"brand":"Motorcraft","part_number":"SP-589","description":"5.0L V8","is_oem":True}]),
  batt=None,  # GATED - S650 OM punts to dealer
  bnote=('Oil filter FL-2127 (2.3L EB) / FL-500-S (5.0L V8); air FA-2067 (2.3L) / FA-2066 (5.0L); cabin FP-78. '
    'Rear axle 75W-85 + limited-slip friction modifier. '
    'NOT in OM (pending): BATTERY GROUP (S650 OM punts to dealer), spark-plug GAP, drain-plug torque, '
    'oil-filter torque, tire size/pressure (B-pillar placard). 5.2L GTD/Shelby halo not covered - gated.'),
  src='owner-manual-verified (per 2025 Mustang S650 OM; 2.3L EcoBoost + 5.0L V8 - oil caps differ from S550)')

ROWS=[(12769,2020,S550),(12839,2021,S550),(12904,2022,S550),(13101,2025,S650),(13167,2026,S650)]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for vid,year,s in ROWS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(vid,s['visc'],None,s['oilcw'],None,s['oem'],None,None,None,None,None,s['src']))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",(vid,TRANS,None,BRAKE,COOLANT_TYPE,s['coolcap'],PS,DIFF,s['src']))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,s['batt'],None,None,None,None,s['spark'],None,None,None,None,TIRE_NOTE,s['bnote'],None,None,None,None,s['src']))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',150.0,204.0,"150 lb-ft (204 N-m), M14x1.5, per owner's manual",'owner-manual-verified'))
    c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",(nid,vid,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor; follow message center',"Ford Owner's Manual (Mustang)",'standard',None,None,None)); nid+=1
    g='S550' if year<=2022 else 'S650'
    print('  wrote %d (%s, %s)'%(vid,year,g))

db.commit()
print('\nVerify:')
for vid,year,s in ROWS:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    p=c.execute('SELECT battery_group FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d(%s): oil=%s | batt=%s'%(vid,year,o,p or 'GATED'))
db.close(); print('\nDONE.')
