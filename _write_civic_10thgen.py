# Write owner's-manual-verified specs for the 10th-gen Honda Civic Sedan (2016-2021)
# Source: 2017 Honda Civic Sedan Owner's Guide (OG-05950), pages cited in the verification log.
# Discipline: ONLY owner's-manual fields. Service-manual fields (drain-plug torque/size,
# spark-plug gap, battery group/CCA, lug torque) left NULL/gated (purge fabricated ai-haiku rows).
import sqlite3, json, shutil, datetime, os

DB = 'wrench_vehicles.db'
bak = DB + '.bak_civic10_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.cop2 = shutil.copy2  # noop alias
shutil.copy2(DB, bak)
print('Backup ->', bak)

# id -> (year, is_primary_manual_year)
TARGETS = [(12240,2016,False),(12374,2017,True),(12513,2018,False),
           (38592,2019,False),(12778,2020,False),(12848,2021,False)]

PRIMARY_SRC = 'owner-manual-verified'
SIB_SRC     = 'owner-manual-verified (per 2017 Civic Sedan OG-05950, 10th-gen, shared drivetrain)'
PRIMARY_MAINT_SRC = "Honda Owner's Manual (2017 Civic Sedan, 10th gen, OG-05950)"
SIB_MAINT_SRC     = "Honda Owner's Manual (2017 Civic Sedan, 10th gen, OG-05950) - generation-stable (shared drivetrain)"

SPARK_JSON = json.dumps([
    {"brand":"NGK","part_number":"ILZKAR8H8S","description":"OE iridium (1.5T)","is_oem":True},
    {"brand":"NGK","part_number":"DILKAR7H11GS","description":"OE iridium (2.0L)","is_oem":True},
    {"brand":"DENSO","part_number":"DXE22HQR-D11S","description":"OE alt (2.0L)","is_oem":True},
])
TIRE_NOTE = ("2.0L (LX): 215/55R16 @ 32 psi. 1.5T (EX and up): 215/50R17 @ 32 psi. "
             "Sport 1.5T: 235/40R18 @ 33 psi front / 32 rear. "
             "Per 2017 Civic Sedan Owner's Guide (OG-05950), pp.149-150.")
BATT_NOTE = ("Spark-plug gap factory pre-set, not published in the Owner's Guide. "
             "BCI battery group size & CCA not specified. Drain-plug torque/size, spark-plug gap, "
             "and lug-nut torque are service-manual fields (not in this Owner's Guide) - pending service-manual verification.")

db = sqlite3.connect(DB); c = db.cursor()
mx = c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]
nextid = mx + 1

for vid, year, primary in TARGETS:
    src  = PRIMARY_SRC if primary else SIB_SRC
    msrc = PRIMARY_MAINT_SRC if primary else SIB_MAINT_SRC
    # purge existing rows in every spec table for this vehicle
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))

    # oil_change
    c.execute("""INSERT INTO oil_change
        (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,
         filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,'0W-20',None,'3.7 qt (1.5T) / 4.4 qt (2.0L)','3.4 qt (1.5T) / 4.2 qt (2.0L)',
         'API Premium-grade 0W-20 (Genuine Honda Motor Oil 0W-20)',
         None,None,None,None,None,src))

    # fluids
    c.execute("""INSERT INTO fluids
        (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,
         coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,'Honda HCF-2 (CVT) / Honda MTF (6MT Sport)',
         '3.9 qt (1.5T CVT) / 3.7 qt (2.0L CVT) / 2.0 qt (6MT)',
         'Honda DOT 3','Honda Type 2 (Long-Life, 50/50)','5.4 qt (1.5T) / 5.6 qt (2.0L)',
         'Electric power steering (no fluid)',None,src))

    # parts (gap/battery NULL = service-manual/gated)
    c.execute("""INSERT INTO parts
        (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,
         tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,
         cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,
         timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,'Iridium',None,4,None,None,'215/55R16 (2.0L) / 215/50R17 (1.5T)',32,32,
         SPARK_JSON,None,None,None,None,TIRE_NOTE,BATT_NOTE,None,None,None,None,src))

    # maintenance (Maintenance Minder - 3 verified rows, matching 2012 Civic template)
    for mi,mo,desc in [
        (None,12,'Engine oil & filter change - Maintenance Minder (oil-life display); change at least every 12 months'),
        (None,36,'Brake fluid replacement (Honda DOT 3) - every 3 years'),
        (None,None,'Tire rotation - per Maintenance Minder (service item 1)')]:
        c.execute("""INSERT INTO maintenance
            (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nextid,vid,mi,mo,desc,msrc,'standard',None,None,None))
        nextid += 1

    print('  wrote id %s (%s)%s'%(vid,year,'  <-- primary manual' if primary else ''))

db.commit()

# verify
print('\nPost-write source check:')
for vid,year,_ in TARGETS:
    o=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT source FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT source FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    m=c.execute('SELECT COUNT(*) FROM maintenance WHERE vehicle_id=?',(vid,)).fetchone()[0]
    ts=c.execute('SELECT COUNT(*) FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    es=c.execute('SELECT COUNT(*) FROM engine_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%s): oil=%s | maint_rows=%s | torque_rows=%s engine_rows=%s'%(
        year,vid,(o[0][:30] if o else None),m,ts,es))
db.close()
print('\nDONE. Service-manual fields (torque/gap/battery/lug) left empty -> pending verification.')
