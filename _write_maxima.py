# Owner's-manual-verified specs for Nissan Maxima A36 (2019/2020/2021).
# Source: 2020 Maxima OM (rep); engine config (VQ35DE 3.5L V6, single) verified vs each year's manual.
# KEY: HYDRAULIC power steering (Nissan E-PSF) - diverges from 4-cyl Sentra/Altima (electric).
# Nissan torque bonus written verified. Service-manual fields NULL/gated.
import sqlite3, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_maxima_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

SS='owner-manual-verified'
SIB='owner-manual-verified (per 2020 Maxima OM, A36 gen; engine config confirmed vs each year OM)'
TARGETS=[
 (479, 2020, SS,  "Nissan Owner's Manual (2020 Maxima Sedan)"),
 (38633,2019, SIB,"Nissan Owner's Manual (2020 Maxima, A36 gen)"),
 (1977, 2021, SIB,"Nissan Owner's Manual (2020 Maxima, A36 gen)"),
]
TORQUE=[('lug_nut',83.0,113.0,"83 ft-lb (113 N-m) per owner's manual p6-8"),
        ('drain_bolt',25.0,34.0,"22-29 ft-lb (29.4-39.2 N-m) per owner's manual p8-10; use new washer"),
        ('oil_filter',13.0,17.7,"11-15 ft-lb (14.7-20.6 N-m) per owner's manual p8-10")]
TIRE='245/45R18 (SV) / 245/40R19 (SR/Platinum)'
TIRE_NOTE="Tire pressure 33 psi front/rear all grades (230 kPa). Per 2020 Maxima OM p8-30."
BATT_NOTE=("Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual "
           "(service-manual fields) - pending. CVT fluid NS-3 type verified; capacity not in OM. "
           "Drain-plug, oil-filter, and lug torque ARE in the Nissan OM and are recorded verified.")

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year,src,msrc in TARGETS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,'0W-20',None,'5.1 qt','4.8 qt','Genuine Nissan Motor Oil 0W-20 (3.5L V6 VQ35DE), API SN/SP',
         None,None,None,None,None,src))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,'Nissan CVT Fluid NS-3',None,'Nissan DOT 3',
         'Nissan Long Life Antifreeze/Coolant (blue, pre-diluted)','9.7 qt',
         'Nissan E-PSF (hydraulic)',None,src))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,6,None,None,TIRE,33,33,None,None,None,None,None,TIRE_NOTE,BATT_NOTE,
         None,None,None,None,src))
    for comp,ft,nm,note in TORQUE:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
                  (vid,comp,ft,nm,note,'owner-manual-verified'))
    for mi,mo,desc in [
        (None,None,'Engine oil & filter change - oil control system (oil-life based); follow oil maintenance reminder'),
        (5000,None,'Tire rotation - every 5,000 mi (severe) per maintenance schedule')]:
        c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,
            source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nid,vid,mi,mo,desc,msrc,'standard',None,None,None)); nid+=1
    print('  wrote %d (%s A36, 3.5L V6)'%(vid,year))

db.commit()
print('\nVerify:')
for vid,year,src,msrc in TARGETS:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT component,torque_ft_lbs FROM torque_specs WHERE vehicle_id=? ORDER BY component',(vid,)).fetchall()
    print('  %d(%s): oil=%s %s | PS=%s | torque=%s'%(vid,year,o[0],o[1],f[0],dict((x[0],x[1]) for x in tq)))
db.close(); print('\nDONE.')
