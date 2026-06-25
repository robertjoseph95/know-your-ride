# GMC Yukon GMT800 (2000-2004) - 5 rows, each from its own year's GMC Yukon OM (all legible incl. 2003).
# Per-year (read from each OM): oil-spec starburst (2000-2003) -> GM6094M (2004); V8 gap 0.060 (2000-2003)
#   -> 0.040 (2004); ATF DEXRON-III throughout. 2003 written NORMALLY (its OM is a 3.6MB text PDF, legible -
#   no scanned-OM gating, unlike Silverado/Tahoe 2003). Engines: 2000 = 4.8+5.3 V8 (+5.7 old-body carryover,
#   gated - not OM-covered); 2001-2004 = 4.8+5.3+6.0 V8 (Denali). 6.0 oil cap 6.0 qt.
# Common: 5W-30, oil 6.0 qt (V8), hydraulic PS (GM 89021184), DOT 3 (Delco Supreme 11), lug 140,
#   axles 80W-90 front/75W-90 rear, transfer Auto Transfer Case Fluid ~2.0 qt, fuel 26.0 gal (Yukon SWB).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_yukon_gmt800_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (Certification/Tire label on driver door, not in OM body) - pending.'
VISC='5W-30 (all engines); 10W-30 acceptable above 0F/-18C'
PS='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'
BRAKE='GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)'
COOLANT='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
DIFF=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant (GM 1052271)","rear_axle":"SAE 75W-90 Synthetic Axle Lubricant (GM 12378261)"})
XFER='Transfer case (4WD): Automatic Transfer Case Fluid (GM 12378396), ~2.0 qt / 1.9 L'
FUEL='26.0 gal / 98.4 L (Yukon, short wheelbase)'
COOL={
 2000:'14.4 qt / 13.6 L (4.8L & 5.3L V8, front A/C; up to 15.8 qt with rear A/C)',
 2001:'14.4 qt / 13.6 L (4.8L & 5.3L V8, front A/C) / ~15.8 qt (6.0L V8 or with rear A/C)',
 2002:'14.4 qt / 13.6 L (4.8L & 5.3L V8, front A/C) / ~15.8 qt (6.0L V8 or with rear A/C)',
 2003:'14.4 qt / 13.6 L (4.8L & 5.3L V8, front A/C) / 15.8 qt / 15.0 L (6.0L V8; 4.8/5.3 with rear A/C)',
 2004:'15.0 qt / 14.0 L (4.8L & 5.3L V8, front A/C) / 13.0 qt / 12.0 L (6.0L V8); 5.3 with rear A/C 14.0 qt',
}
def W(vid,oilcw,oem,gap,cc,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,VISC,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,'4-speed automatic (4L60-E / 4L65-E): DEXRON-III ATF (per-engine transmission binding not specified in OM - gated). '+XFER,None,BRAKE,COOLANT,cc,PS,DIFF,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,gap,None,None,None,None,None,None,None,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when CHANGE ENGINE OIL message displays (at least once a year)',"GMC Owner's Manual (Yukon)",'standard',None,None,None)); nid+=1

ROWS=[(2000,13441),(2001,14254),(2002,15182),(2003,16130),(2004,17101)]
for yr,vid in ROWS:
    has60=yr>=2001
    v8='4.8L V8, 5.3L V8'+(', 6.0L V8 (Denali)' if has60 else '')
    oilcw='6.0 qt / 5.7 L (%s)'%v8
    oem=('API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM' if yr<=2003 else 'GM6094M (API Certified for Gasoline Engines)')
    gap=('0.060 in / 1.52 mm (V8 engines)' if yr<=2003 else '0.040 in / 1.01 mm (V8 engines)')
    carry=(' A 5.7L V8 old-body carryover existed for 2000 - NOT covered by this GMT800 OM, GATED.' if yr==2000 else '')
    bn=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '
        'Oil filter & spark-plug part numbers are listed per-year in each OM (not transcribed here - gap & oil capacity are the service specs). '
        'Fuel tank: %s.'%FUEL+carry+
        ' NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed.')
    src='owner-manual-verified (per %d GMC Yukon OM, self-ID p1; GMT800%s)'%(yr,' - 2003 OM legible (text PDF), no scanned-OM gating' if yr==2003 else '')
    W(vid,oilcw,oem,gap,COOL[yr],bn,src)
    print('  %d (%d): oem=%s gap=%s eng=%s'%(yr,vid,'starburst' if yr<=2003 else 'GM6094M', '0.060' if yr<=2003 else '0.040','+6.0' if has60 else '4.8/5.3'))

db.commit()
print('\nVerify:')
for yr,vid in ROWS:
    o=c.execute('SELECT oem_spec FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    g=c.execute('SELECT spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    oc=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d: oem=%s gap=%s | %s'%(yr,'GM6094M' if 'GM6094M (' in o else 'starburst',g[:22],oc[:48]))
db.close(); print('DONE.')
