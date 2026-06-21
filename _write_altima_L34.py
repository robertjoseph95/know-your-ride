# Write owner's-manual-verified specs for the Nissan Altima L34 (2019-2025).
# Source: 2019 Altima Sedan OM (generation-representative) + per-year engine config verified
# against each year's own manual; 2025 (2.5L-only) verified vs 2025 OM.
# Nissan advantage: OM publishes drain-plug, oil-filter, AND lug torque -> written verified.
# Service-manual fields still NULL/gated: spark-plug type/gap, battery group/CCA, CVT capacity.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_altima_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

# id, year, kind: 'P'=primary(2019), 'S'=sibling(2020-2024), 'X'=2025 single-engine
TARGETS=[(12702,2019,'P'),(461,2020,'S'),(1959,2021,'S'),(3485,2022,'S'),
         (5023,2023,'S'),(6604,2024,'S'),(8173,2025,'X')]

SRC={'P':'owner-manual-verified',
     'S':'owner-manual-verified (per 2019 Altima Sedan OM, L34 gen, shared drivetrain; engine config confirmed vs each year OM)',
     'X':'owner-manual-verified (per 2025 Altima OM, L34 2.5L-only; 2.0T dropped after 2024)'}
MSRC={'P':"Nissan Owner's Manual (2019 Altima Sedan)",
      'S':"Nissan Owner's Manual (2019 Altima Sedan, L34 gen)",
      'X':"Nissan Owner's Manual (2025 Altima, 2.5L)"}

# engine-divergent strings: dual (2019-2024) vs single 2.5L (2025)
DUAL=dict(visc='0W-20 (2.5L) / 5W-30 (2.0T)', cw='5.4 qt (2.5L) / 5.0 qt (2.0T)',
          cwo='5.1 qt (2.5L) / 4.9 qt (2.0T)',
          oem='Genuine Nissan Motor Oil 0W-20 (2.5L) / Ester 5W-30 (2.0T VC-Turbo), API SN/SP',
          coolant_cap='8.8 qt (2.5L) / 8.7 qt (2.0T)')
SINGLE=dict(visc='0W-20', cw='5.4 qt', cwo='5.1 qt',
            oem='Genuine Nissan Motor Oil 0W-20 (API SP)', coolant_cap='8.8 qt')

TIRE_SIZE='215/60R16 (S) / 215/55R17 (SV/SL) / 235/40R19 (SR/Platinum)'
TIRE_NOTE=("S (16 in): 215/60R16 @ 32 psi. SV/SL (17 in): 215/55R17 @ 33 psi. "
           "SR/Platinum (19 in): 235/40R19 @ 33 psi. Per Altima OM p10-9 + p8-33.")
BATT_NOTE=("Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual "
           "(service-manual fields) - pending. CVT fluid NS-3 type verified; capacity not in OM. "
           "Drain-plug (22-28 ft-lb), oil-filter (11-15 ft-lb), and lug (83 ft-lb) torque ARE in the "
           "Nissan OM and are recorded verified.")
DIFF_JSON=json.dumps([{"type":"rear_diff_awd","fluid":"Nissan Diff Oil Hypoid Super GL-5 80W-90 (AWD)"}])

# torque (Nissan OM provides these) - midpoint value, exact range in notes
TORQUE=[('lug_nut',83.0,113.0,"83 ft-lb (113 N-m) per owner's manual p6-8"),
        ('drain_bolt',25.0,34.0,"22-28 ft-lb (29-39 N-m) per owner's manual p8-12; use new washer"),
        ('oil_filter',13.0,17.7,"11-15 ft-lb (14.7-20.6 N-m) per owner's manual p8-12")]

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year,kind in TARGETS:
    src=SRC[kind]; msrc=MSRC[kind]; E=SINGLE if kind=='X' else DUAL
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))

    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,E['visc'],None,E['cw'],E['cwo'],E['oem'],None,None,None,None,None,src))

    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,'Nissan CVT Fluid NS-3',None,'Nissan DOT 3 (Super Heavy Duty)',
         'Nissan Long Life Antifreeze/Coolant (blue, pre-diluted)',E['coolant_cap'],
         'Electric power steering (no fluid)',DIFF_JSON,src))

    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,4,None,None,TIRE_SIZE,33,33,None,None,None,None,None,TIRE_NOTE,BATT_NOTE,
         None,None,None,None,src))

    for comp,ft,nm,note in TORQUE:
        c.execute("""INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source)
            VALUES (?,?,?,?,?,?)""",(vid,comp,ft,nm,note,'owner-manual-verified'))

    rot='Tire rotation - every 5,000 mi' if kind=='X' else 'Tire rotation - every 5,000 mi (2.5L) / 7,500 mi (2.0T)'
    for mi,mo,desc in [
        (None,None,'Engine oil & filter change - oil control system (oil-life based); follow oil maintenance reminder'),
        (5000,None,rot)]:
        c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,
            source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nid,vid,mi,mo,desc,msrc,'standard',None,None,None)); nid+=1

    print('  wrote %d (%s, %s)'%(vid,year,{'P':'primary','S':'sibling','X':'2025 2.5L-only'}[kind]))

db.commit()
print('\nVerify:')
for vid,year,kind in TARGETS:
    o=c.execute('SELECT viscosity,source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT component,torque_ft_lbs FROM torque_specs WHERE vehicle_id=? ORDER BY component',(vid,)).fetchall()
    print('  %d(%s): visc=%-28s torque=%s'%(vid,year,o[0],dict((x[0],x[1]) for x in tq)))
db.close(); print('\nDONE.')
