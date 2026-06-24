# Chevy Tahoe + Suburban GMT800 (2000-2006) - 14 rows, each from its own year's combined Tahoe/Suburban OM.
# Self-ID gate PASSED for all 7 OMs (2003 = scanned/OCR). Per-year transitions read from each year's OM,
# mirroring the GMT800 Silverado profile (same platform/era):
#   oil spec: API-starburst (2000-2003) -> GM6094M (2004-2006)
#   ATF: DEXRON-III (2000-2005) -> DEXRON-VI (2006)
#   V8 spark gap: 0.060 (2000-2002) -> 0.040 (2004-2006); 2003 GATED (scanned OM)
# SUV values read fresh per year: oil cap 6.0qt (V8); cooling per year (config-dependent); fuel per model.
# Engines: Tahoe = 4.8 + 5.3 V8; Suburban (1500) = 5.3 V8. 2000: a 5.7L old-body carryover existed -> gated.
# Common: 5W-30, hydraulic PS (GM 89021184), DOT 3 (Delco Supreme 11), lug 140, axles 80W-90 front/75W-90 rear,
#   transfer case Auto Transfer Case Fluid (GM 12378396) ~2.0 qt.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_tahoesub_gmt800_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE_NOTE='Tire size & pressure are config-dependent (Certification/Tire label on driver door, not in OM body) - pending.'
VISC='5W-30 (all engines); 10W-30 acceptable above 0F/-18C'
PS='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'
BRAKE='GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)'
COOLANT='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
DIFF=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant (GM 1052271)","rear_axle":"SAE 75W-90 Synthetic Axle Lubricant (GM 12378261)"})
XFER='Transfer case (4WD): Automatic Transfer Case Fluid (GM 12378396), ~2.0 qt / 1.9 L'

COOL={
 2000:'14.4 qt / 13.6 L (4.8L & 5.3L V8; up to ~15.8 qt with rear A/C)',
 2001:'14.4 qt / 13.6 L (4.8L & 5.3L V8; up to ~15.8 qt with rear A/C)',
 2002:'14.4 qt / 13.6 L (4.8L & 5.3L V8; up to ~15.8 qt with rear A/C)',
 2003:'config-dependent (front vs front+rear A/C); 2003 OM is scanned - value not legible, GATED',
 2004:'13.0 qt / 12.0 L (5.3L V8, front A/C) / 15.0 qt / 14.0 L (4.8L V8, front A/C); up to 17.0 qt with front+rear A/C',
 2005:'17.2 qt / 16.3 L (4.8L & 5.3L V8, electric cooling fan)',
 2006:'16.8 qt / 15.9 L (4.8L & 5.3L V8; +2.1 qt with rear heating)',
}
SUB_FUEL={2000:'32.5 gal / 123.0 L',2001:'32.5 gal / 123.0 L',2002:'31.0 gal / 117.3 L',2003:'31.0 gal / 117.3 L',
          2004:'31.0 gal / 117.3 L',2005:'31.0 gal / 117.3 L',2006:'31.0 gal / 117.3 L'}

def W(vid,oilcw,oem,trans,cc,gap,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,VISC,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,trans,None,BRAKE,COOLANT,cc,PS,DIFF,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,gap,None,None,None,None,None,None,None,None,None,None,None,TIRE_NOTE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when CHANGE ENGINE OIL message displays (at least once a year)',"Chevrolet Owner's Manual (Tahoe/Suburban)",'standard',None,None,None)); nid+=1

# (year, Tahoe id, Suburban id)
ROWS=[(2000,10964,10963),(2001,10980,10979),(2002,11004,11003),(2003,11037,11036),(2004,11083,11082),(2005,11137,11136),(2006,11204,11203)]
for yr,tah,sub in ROWS:
    oem=('API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM' if yr<=2003
         else 'GM6094M (API Certified for Gasoline Engines)')
    atf='DEXRON-VI' if yr==2006 else 'DEXRON-III'
    trans='4-speed automatic (4L60-E / 4L65-E): %s ATF (per-engine transmission binding not specified in OM - gated). %s'%(atf,XFER)
    if yr<=2002: gap='0.060 in / 1.52 mm (V8 engines)'
    elif yr==2003: gap='V8 spark gap GATED - 2003 OM is a scanned/OCR copy, technical-data table illegible'
    else: gap='0.040 in / 1.01 mm (V8 engines)'
    src='owner-manual-verified (per %d Chevrolet Tahoe/Suburban OM, self-ID p1; GMT800)'%yr
    carry=(' A 5.7L V8 old-body carryover existed for 2000 - NOT covered by this GMT800 OM, GATED.' if yr==2000 else '')
    scanned=(' 2003: V8 spark gap, cooling capacity & part numbers GATED - the 2003 OM is a scanned/OCR copy whose technical-data table is illegible.' if yr==2003 else '')
    # Tahoe
    bn_t=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '
          'Oil filter & spark-plug part numbers are listed per-year in each OM (not transcribed here - gap & oil capacity are the service specs). '
          'Fuel tank: 26.0 gal / 98.4 L (Tahoe).'+carry+
          ' NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed.'+scanned)
    W(tah,'6.0 qt / 5.7 L (4.8L V8, 5.3L V8)',oem,trans,COOL[yr],gap,bn_t,src)
    # Suburban (1500): 5.3 V8
    bn_s=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '
          'Oil filter & spark-plug part numbers are listed per-year in each OM (not transcribed here). '
          'Fuel tank: %s (Suburban 1500).'%SUB_FUEL[yr]+carry+
          ' NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed.'+scanned)
    W(sub,'6.0 qt / 5.7 L (5.3L V8)',oem,trans,COOL[yr],gap,bn_s,src)
    print('  %d Tahoe(%d)+Suburban(%d): oem=%s atf=%s'%(yr,tah,sub,'starburst' if yr<=2003 else 'GM6094M',atf))

db.commit()
print('\nVerify:')
for yr,tah,sub in ROWS:
    o=c.execute('SELECT oem_spec FROM oil_change WHERE vehicle_id=?',(tah,)).fetchone()[0]
    g=c.execute('SELECT spark_plug_gap FROM parts WHERE vehicle_id=?',(tah,)).fetchone()[0]
    print('  %d: oem=%s | gap=%s'%(yr,'GM6094M' if 'GM6094M (' in o else 'starburst',g[:34]))
db.close(); print('DONE.')
