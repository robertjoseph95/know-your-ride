# Chevrolet Silverado 1500 GMT900 bulk - 3 rows (2008, 2009, 2012).
# Sources (each year's OWN GM-hosted OM, self-ID gate PASSED in-text):
#   2008 OM (596pp), 2009 OM (598pp), 2012 OM (608pp). Pages: oil/visc 2008 p5-15/2009 p6/2012 p10-9;
#   capacities (oil/coolant/fuel/transfer) ~Section 5/12; engine specs (spark gap) 2008/09 p5-131, 2012 p12-5;
#   recommended fluids (PS/brake/ATF/axle) 2008 p6-14, 2009 p6-15, 2012 p11-13.
# Per-year EPA roster: 2008 = 4.3/4.8/5.3/6.0; 2009 = +6.2 (5 eng); 2012 = 4.3/4.8/5.3/6.2 (6.0 dropped).
# CONFIRM-DON'T-ASSUME (READ, not carried back from K2XX/T1XX):
#   oil 5W-30 (NOT 0W-20); oil SPEC per-year GM6094M (2008/09) vs dexos1 (2012); PS HYDRAULIC (not EPS);
#   ATF DEXRON-VI 4-spd(4L60-E)/6-spd(6L80/6L90); oil cap V8 6.0qt / V6 4.5qt; coolant ~16-17qt; 4.3 gap 0.060".
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silv_gmt900_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

# common (gen-stable)
PS='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'   # GMT900 = hydraulic, NOT EPS
BRAKE='GM-approved DOT 3'
TRANS=('4-speed automatic (4L60-E): DEXRON-VI ATF / 6-speed automatic (6L80-E, 6L90-E): DEXRON-VI ATF '
       '(engine->transmission-speed binding not specified in OM - gated). '
       'Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L')
COOLANT='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
DIFF=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant (1500 Series, GM 89021671)",
                 "rear_axle":"SAE 75W-90 Synthetic Axle Lubricant (GM 89021677)"})
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'
VISC='5W-30 (all engines); 0W-30 below -20F/-29C'

# coolant capacity by engine (qt)
COOL={'4.3':'16.5 qt / 15.6 L (4.3L V6)','4.8':'16.9 qt / 16.0 L (4.8L V8)','5.3':'16.9 qt / 16.0 L (5.3L V8)',
      '6.0':'16.8 qt / 15.9 L (6.0L V8)','6.2_09':'17.6 qt / 16.7 L (6.2L V8)','6.2_12':'16.8 qt / 15.9 L (6.2L V8)'}

def v8list(engs):  # engs like ['4.8','5.3','6.0']
    return ', '.join('%sL V8'%e for e in engs)

def build(year, vid, v8s, has62, oemspec, sp_v6, sp_v8):
    # oil cap
    oilcw='4.5 qt / 4.3 L (4.3L V6) / 6.0 qt / 5.7 L (%s)'%v8list(v8s)
    # coolant cap string
    cc_parts=[COOL['4.3']]+[COOL[e] for e in v8s if e in ('4.8','5.3','6.0')]
    if has62: cc_parts.append(COOL['6.2_09'] if year==2009 else COOL['6.2_12'])
    cc=' / '.join(cc_parts)
    gap='0.060 in / 1.52 mm (4.3L V6); 0.040 in / 1.01 mm (%s)'%v8list(v8s)
    plugs=json.dumps([
      {"brand":"ACDelco","part_number":sp_v6,"description":"4.3L V6","is_oem":True},
      {"brand":"ACDelco","part_number":sp_v8,"description":v8list(v8s),"is_oem":True}])
    bn=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '
        'Oil filter: ACDelco PF47 / GM 25010792 (4.3L V6); ACDelco PF48 / GM 89017524 (%s). '
        'Fuel tank: 26.0 gal / 98.4 L (Standard & Short Box) / 34.0 gal / 128.7 L (Long Box). '
        'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
        'tire size/pressure (door placard), per-engine transmission speed (4L60-E vs 6L80-E/6L90-E).'%v8list(v8s))
    src='owner-manual-verified (per %d Silverado 1500 OM, self-ID p1; GMT900)'%year
    return dict(vid=vid,year=year,visc=VISC,oilcw=oilcw,oem=oemspec,cc=cc,gap=gap,plugs=plugs,bn=bn,src=src)

ROWS=[
  build(2008,11359,['4.8','5.3','6.0'],False,'GM6094M (API Certified for Gasoline Engines)','41-932 (GM 89017883)','41-985 (GM 12571164)'),
  build(2009,11447,['4.8','5.3','6.0'],True ,'GM6094M (API Certified for Gasoline Engines)','41-993 (GM 12607234)','41-985 (GM 12609877)'),
  build(2012,11742,['4.8','5.3'],      True ,'dexos1 (ACDelco dexos1 Synthetic Blend)','41-101 (GM 12568387)','41-110 (GM 12621258)'),
]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for r in ROWS:
    vid=r['vid']
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,r['visc'],None,r['oilcw'],None,r['oem'],None,None,None,None,None,r['src']))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,TRANS,None,BRAKE,COOLANT,r['cc'],PS,DIFF,r['src']))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,r['gap'],None,None,None,None,None,None,r['plugs'],None,None,None,None,TIRE_NOTE,r['bn'],None,None,None,None,r['src']))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Chevrolet Owner's Manual (Silverado 1500)",'standard',None,None,None)); nid+=1
    print('  wrote %d (%s): oem=%s engines=4.3+%s%s'%(vid,r['year'],r['oem'][:8],v8list(['4.8','5.3']),'+6.0/6.2 etc'))

db.commit()
print('\nVerify:')
for r in ROWS:
    o=c.execute('SELECT viscosity,oem_spec FROM oil_change WHERE vehicle_id=?',(r['vid'],)).fetchone()
    f=c.execute('SELECT power_steering_fluid,brake_fluid FROM fluids WHERE vehicle_id=?',(r['vid'],)).fetchone()
    print('  %d: visc=%s | oem=%s | PS=%s | brake=%s'%(r['year'],o[0][:10],o[1][:9],f[0][:18],f[1]))
db.close(); print('DONE.')
