# Chevrolet Silverado 1500 K2XX bulk - 3 rows (2016, 2017, 2018).
# Source: 2017 Silverado 1500 OM (23476161A, K2XX gen-rep; self-ID p1 "Silverado Owner's Manual 2017").
#   Pages = printed (PDF-1): oil/visc p361; cooling/DEX-COOL p369; capacities (oil/coolant/transfer/wheel-nut)
#   pp.467-469; engine specs (spark gap) p470; recommended fluids (ATF/brake/coolant/axle) pp.462-463; parts pp.464-465.
# Engines (EPA-confirmed identical 2016-2018): 4.3L V6 (LV3/LV1), 5.3L V8 (L83), 6.2L V8 (L86). No 2.7T, no diesel.
# CONFIRM-DON'T-ASSUME / K2XX-specific (READ, NOT carried back from T1XX):
#   brake = DOT 3 (T1XX=DOT 4); ATF 6-spd DEXRON-VI / 8-spd DEXRON-HP (T1XX=8/10 HP/ULV); coolant ~16qt (T1XX ~13);
#   fuel tank 26/34 gal (T1XX 24/28.3); axle fluids GIVEN (T1XX punted); DEX-COOL has NO GMW3420 number stated.
#   Oil viscosity SAME as T1XX (0W-20 V8 / 5W-30 4.3) - confirmed by reading the 2017 OM, not assumed.
# 2016 honest provenance: 2017 gen-rep applied (engines byte-identical 2016-2018 per EPA); no GM 2016 OM sourced.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silv_k2xx_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

SRC='owner-manual-verified (per 2017 Silverado 1500 OM, K2XX gen-rep; engines identical 2016-2018 per EPA)'

VISC='5W-30 (4.3L V6) / 0W-20 (5.3L V8, 6.2L V8); 0W-30 below -29C/-20F'
OEM='dexos1 (ACDelco dexos1 Synthetic Blend)'
OILCW='6.0 qt / 5.7 L (4.3L V6) / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'

TRANS=('6-speed automatic: DEXRON-VI ATF / 8-speed automatic: DEXRON-HP ATF '
       '(engine->transmission-speed binding not specified in OM - gated). '
       'Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L')
BRAKE='GM-approved DOT 3'   # K2XX = DOT 3 (T1XX moved to DOT 4)
COOLANT='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
COOLCAP='15.9 qt / 15.1 L (4.3L V6) / 16.6 qt / 15.7 L (5.3L V8) / 16.6 qt / 15.7 L (6.2L V8)'
PS='Electric power steering (EPS, 1500 Series) - no fluid, no regular maintenance'
DIFF=json.dumps({"rear_axle":"SAE 75W-85 Synthetic Axle Lubricant (1500 Series, GM 19300457)",
                 "front_axle_4wd":"SAE 75W-90 Synthetic Axle Lubricant (GM 88900401)"})

PLUG_GAP='0.037-0.043 in / 0.95-1.10 mm (4.3L V6, 5.3L V8, 6.2L V8)'
PLUGS=json.dumps([
  {"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"4.3L V6 (LV3/LV1), 5.3L V8 (L83) & 6.2L V8 (L86)","is_oem":True}])

BNOTE=('Battery: original-equipment maintenance-free - GM punts group size to the battery label, GATED. '
       'Oil filter: ACDelco PF63E / GM 19330000 (4.3L V6, 5.3L & 6.2L V8). '
       'Engine air filter: ACDelco A3181C / GM 22845992. Cabin air filter: ACDelco CF188 / GM 23281440. '
       'Fuel tank: 26.0 gal / 98.4 L (Standard & Short Box) / 34.0 gal / 128.7 L (Long Box). '
       'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
       'tire size/pressure (door placard), per-engine transmission speed.')
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

ROWS=[(12202,2016),(12332,2017),(12467,2018)]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for vid,year in ROWS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,SRC))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,TRANS,None,BRAKE,COOLANT,COOLCAP,PS,DIFF,SRC))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,PLUG_GAP,None,None,None,None,None,None,PLUGS,None,None,None,None,TIRE_NOTE,BNOTE,None,None,None,None,SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Chevrolet Owner's Manual (Silverado 1500)",'standard',None,None,None)); nid+=1
    print('  wrote %d (%s)'%(vid,year))

db.commit()
print('\nVerify:')
for vid,year in ROWS:
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    b=c.execute('SELECT brake_fluid,transmission_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d: oil=%s | brake=%s | trans=%s'%(year,o[:40],b[0],b[1][:42]))
db.close(); print('DONE.')
