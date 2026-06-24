# Chevrolet Silverado 1500 GMT800 bulk - 7 rows (2000-2006), EACH from its own year's GM-hosted OM.
# Self-ID gate PASSED for all 7 in-text. Pages vary by year (older Section-6 / newer Section-5 layouts).
# Per-year EPA roster: 2000 = 4.3/4.8/5.3 (no 6.0); 2001-2006 = +6.0 V8.
# CONFIRM-DON'T-ASSUME per-year (read from each year's own OM, NOT interpolated):
#   oil spec API-starburst-only (2000-2003) vs GM6094M (2004-2006);
#   ATF DEXRON-III (2000-2005) vs DEXRON-VI (2006);
#   V8 spark gap 0.060" (2000-2002) vs 0.040" (2004-2006); 2003 V8 gap GATED (scanned OM table illegible).
# Common: 5W-30, oil cap 4.5qt(V6)/6.0qt(V8), HYDRAULIC PS (GM PS fluid 89021184), DOT 3, lug 140,
#   axles 80W-90 front/75W-90 rear, transfer case ~2.0qt, fuel tank 26/34, DEX-COOL (no spec#/color).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silv_gmt800_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

PS='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'
BRAKE='GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)'
COOLANT='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
DIFF=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant (GM 1052271)",
                 "rear_axle":"SAE 75W-90 Synthetic Axle Lubricant (GM 12378261, meeting GM 9986115)"})
TIRE_NOTE='Tire size & pressure are config-dependent (Certification/Tire label on driver door rear edge, not in OM body) - pending.'
VISC='5W-30 (all engines); 10W-30 acceptable above 0F/-18C'
XFER='Transfer case (4WD): Automatic Transfer Case Fluid (GM 12378396), ~2.0 qt / 1.9 L'

# coolant caps per year (base auto, approximate - varies by A/C config), 6.0 only where offered
COOL={
 2000:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8)',
 2001:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2002:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2003:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2004:'14.0 qt / 13.0 L (4.3L V6) / 15.0 qt / 14.0 L (4.8L V8) / 14.0 qt / 13.0 L (5.3L V8) / 13.0 qt / 12.0 L (6.0L V8)',
 2005:'14.8 qt / 14.0 L (4.3L V6) / 16.8 qt / 15.9 L (4.8L V8) / 16.8 qt / 15.9 L (5.3L V8) / 16.0 qt / 15.1 L (6.0L V8)',
 2006:'14.8 qt / 14.0 L (4.3L V6) / 15.2 qt / 14.4 L (4.8L V8) / 15.2 qt / 14.4 L (5.3L V8) / 16.2 qt / 15.3 L (6.0L V8)',
}

def cfg(year):
    has60 = year>=2001
    v8='4.8L V8, 5.3L V8'+(', 6.0L V8' if has60 else '')
    oilcw='4.5 qt / 4.3 L (4.3L V6) / 6.0 qt / 5.7 L (%s)'%v8
    early = year<=2003
    oem=('API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM'
         if early else 'GM6094M (API Certified for Gasoline Engines)')
    atf='DEXRON-VI' if year==2006 else 'DEXRON-III'
    trans=('4-speed automatic (4L60-E / 4L65-E): %s ATF '
           '(per-engine transmission binding not specified in OM - gated). %s'%(atf,XFER))
    # spark gap per year
    if year<=2002:
        gap='0.060 in / 1.52 mm (all engines: 4.3L V6, %s)'%v8
    elif year==2003:
        gap='0.060 in / 1.52 mm (4.3L V6); 4.8/5.3/6.0L V8 gap GATED - 2003 OM technical-data table illegible (scanned)'
    else:
        gap='0.060 in / 1.52 mm (4.3L V6); 0.040 in / 1.01 mm (%s)'%v8
    # V8 oil filter per era
    of_v8={2000:'ACDelco PF59',2001:'ACDelco PF59',2002:'ACDelco PF59',2003:None,
           2004:'ACDelco PF44',2005:'ACDelco PF46',2006:'ACDelco PF46'}[year]
    of_line='Oil filter: ACDelco PF47 / GM 25010792 (4.3L V6)'
    of_line += ('; %s (4.8L/5.3L%s V8).'%(of_v8,'/6.0L' if has60 else '') if of_v8 else '; V8 oil filter # GATED (2003 OM table illegible).')
    bn=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '
        + of_line + ' Spark-plug part numbers are listed per-year in each OM (not transcribed here - gap is the service spec). '
        'Fuel tank: 26.0 gal / 98.0 L (Short Bed) / 34.0 gal / 128.0 L (Long Bed). '
        'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
        'tire size/pressure (door placard), per-engine transmission speed.'
        + (' 2003: V8 spark-plug gap & part numbers GATED - the 2003 OM is a scanned/OCR copy whose technical-data table is illegible.' if year==2003 else ''))
    src='owner-manual-verified (per %d Silverado 1500 OM, self-ID p1; GMT800)'%year
    return dict(visc=VISC,oilcw=oilcw,oem=oem,trans=trans,cc=COOL[year],gap=gap,bn=bn,src=src)

ROWS=[(10962,2000),(10978,2001),(11002,2002),(11035,2003),(11081,2004),(11135,2005),(11202,2006)]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for vid,year in ROWS:
    r=cfg(year)
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,r['visc'],None,r['oilcw'],None,r['oem'],None,None,None,None,None,r['src']))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,r['trans'],None,BRAKE,COOLANT,r['cc'],PS,DIFF,r['src']))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,r['gap'],None,None,None,None,None,None,None,None,None,None,None,TIRE_NOTE,r['bn'],None,None,None,None,r['src']))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), 6 bolts (14mm), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when CHANGE ENGINE OIL message displays (at least once a year)',"Chevrolet Owner's Manual (Silverado 1500)",'standard',None,None,None)); nid+=1
    print('  wrote %d (%s): oem=%s atf=%s'%(vid,year,'starburst' if year<=2003 else 'GM6094M', 'VI' if year==2006 else 'III'))

db.commit()
print('\nVerify:')
for vid,year in ROWS:
    o=c.execute('SELECT viscosity,oem_spec FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT power_steering_fluid,transmission_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    g=c.execute('SELECT spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d: oem=%s | ATF=%s | gap=%s'%(year, 'GM6094M' if 'GM6094' in o[1] else 'starburst-only', 'VI' if 'VI' in f[1] else 'III', g[:48]))
db.close(); print('DONE.')
