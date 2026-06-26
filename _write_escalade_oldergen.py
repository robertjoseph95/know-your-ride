# Cadillac Escalade older gens - 8 rows, each from its OWN Escalade OM. Completes the no-gap set.
# 2000 1st-gen (5.7L Vortec 5700); GMT800 2002/2003/2004 (5.3 + 6.0 H.O. V8); K2XX 2018/2019 (6.2 L86);
# T1XX 2025/2026 (6.2 L87, diesel dropped). 2003 written NORMALLY (legible 471pp OM, gap 0.060, NO gate).
# DEFER (NOT written, stay gated): 2005 GMT800 (id 18105, only partial OM), 2020 K2XX (id 291, no GM OM).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_escalade_old_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'
def W(vid,visc,oilcw,oem,trans,brake,coolant,cc,ps,diff,gap,plugs,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,coolant,cc,ps,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,gap,None,None,None,None,None,None,plugs,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when DIC/CHANGE ENGINE OIL indicates (at least once a year)',"Cadillac Owner's Manual (Escalade)",'standard',None,None,None)); nid+=1

PS_HYD='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'
PS_EPS='Electric power steering (EPS) - no fluid, no regular maintenance'
DIFF_OLD=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant","rear_axle":"SAE 75W-90 Synthetic Axle Lubricant"})
GATE_MOD='front/rear axle & transfer-case fluid TYPE (OM punts to dealer)'

# ---- 2000 1st-gen (5.7L Vortec 5700) ----
W(13430,'5W-30 (5.7L V8); 10W-30 acceptable above 0F/-18C','5.0 qt / 4.8 L (5.7L V8, Vortec 5700)',
  'API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM',
  '4-speed automatic (4L60-E): DEXRON-III ATF (per-engine binding not in OM - gated). Transfer case (AWD): Automatic Transfer Case Fluid, ~2.0 qt',
  'GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)','DEX-COOL, 50/50 premix (coolant spec number & color not stated in OM).',
  '17.5 qt / 16.5 L (5.7L V8)',PS_HYD,DIFF_OLD,None,None,
  'Battery: maintenance-free - group not in OM, GATED. Oil filter & spark-plug part numbers + spark-plug gap per OM (not transcribed). Fuel tank: 30.0 gal / 113.6 L (1st-gen Escalade). NOT in OM (pending/gated): battery group/CCA, spark-plug gap, drain-plug/oil-filter torque, tire (placard), per-engine transmission speed.',
  'owner-manual-verified (per 2000 Cadillac Escalade OM, self-ID p1; 1st-gen 5.7L Vortec 5700)')
print('  wrote 2000 (13430) 1st-gen 5.7L')

# ---- GMT800 2002/2003/2004 (5.3 + 6.0 H.O. V8) ----
GMT800=[(2002,15171,'starburst','0.060','18.6 qt / 17.6 L (5.3L V8) / 19.0 qt / 18.0 L (6.0L H.O. V8)'),
        (2003,16119,'starburst','0.060','18.6 qt / 17.6 L (5.3L V8) / 19.0 qt / 18.0 L (6.0L H.O. V8)'),
        (2004,17091,'GM6094M','0.040','16.0 qt / 15.0 L (5.3L V8) / 18.0 qt / 17.0 L (6.0L H.O. V8)')]
for yr,vid,spec,gapv,cc in GMT800:
    oem=('API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM' if spec=='starburst' else 'GM6094M (API Certified for Gasoline Engines)')
    legible=' - 2003 OM legible (471pp text PDF), gap read directly, no scanned-OM gating' if yr==2003 else ''
    W(vid,'5W-30 (all engines); 10W-30 acceptable above 0F/-18C','6.0 qt / 5.7 L (5.3L V8, 6.0L H.O. V8)',oem,
      '4-speed automatic (4L60-E / 4L65-E): DEXRON-III ATF (per-engine binding not in OM - gated). Transfer case (AWD): Automatic Transfer Case Fluid, ~2.0 qt / 1.9 L',
      'GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)','DEX-COOL, 50/50 premix (coolant spec number & color not stated in OM).',
      cc,PS_HYD,DIFF_OLD,'%s in / %s mm (5.3L V8, 6.0L H.O. V8)'%(gapv,'1.52' if gapv=='0.060' else '1.01'),None,
      'Battery: maintenance-free - group not in OM, GATED. Oil filter & spark-plug part numbers per OM (not transcribed - gap & oil cap are the service specs). Fuel tank: 26.0 gal / 98.0 L (Escalade). NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire (placard), per-engine transmission speed.',
      'owner-manual-verified (per %d Cadillac Escalade OM, self-ID p1; GMT800%s)'%(yr,legible))
    print('  wrote %d (%d) GMT800 spec=%s gap=%s'%(yr,vid,spec,gapv))

# ---- K2XX 2018/2019 (6.2 V8 L86) ----
for yr,vid in [(2018,12456),(2019,12602)]:
    W(vid,'0W-20 (6.2L V8); 0W-30 below -29C/-20F','8.0 qt / 7.6 L (6.2L V8)','dexos1 (ACDelco dexos1)',
      '10-speed automatic: DEXRON ULV ATF / 6-speed (early-config): DEXRON-VI ATF (engine->speed binding not specified in OM - gated). Transfer case (AWD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L',
      'GM-approved DOT 3','DEX-COOL (GM spec GMW3420), 50/50 premix (color not stated in OM).','17.8 qt / 16.8 L (6.2L V8)',
      PS_EPS,None,'0.037-0.043 in / 0.95-1.10 mm (6.2L V8)',
      json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"6.2L V8 (L86)","is_oem":True}]),
      'Battery: maintenance-free - group punts to label, GATED. Oil filter ACDelco PF63E / GM 12690385 (6.2L V8). Fuel tank: 26.0 gal / 98.4 L (Escalade SWB). NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire (placard), transmission speed-binding, %s.'%GATE_MOD,
      'owner-manual-verified (per %d Cadillac Escalade OM, self-ID p1; K2XX 6.2L)'%yr)
    print('  wrote %d (%d) K2XX 6.2'%(yr,vid))

# ---- T1XX 2025/2026 (6.2 L87, diesel dropped; Escalade V gated) ----
for yr,vid,om in [(2025,8019,'2025'),(2026,9653,'2025 rep')]:
    W(vid,'0W-20 (6.2L V8); 0W-30 below -29C/-20F','8.0 qt / 7.6 L (6.2L V8)','dexos1 full synthetic (ACDelco dexos1)',
      '10-speed automatic: DEXRON ULV ATF. Transfer case (AWD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L',
      'GM-approved DOT 4','DEX-COOL (GM spec GMW3420), 50/50 premix (color not stated in OM).','15.1 qt / 14.3 L (6.2L V8)',
      PS_EPS,None,'0.037-0.043 in / 0.95-1.10 mm (6.2L V8)',
      json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"6.2L V8 (L87)","is_oem":True}]),
      'AGM 12V battery (Stop/Start) - group punts to label, GATED. Oil filter ACDelco PF63E / GM 12690385 (6.2L V8). Cabin ACDelco CF185. Fuel tank: 24.0 gal / 90.8 L (Escalade SWB) / 28.0 gal / 106.0 L (Escalade ESV, long wheelbase). 3.0L Duramax diesel DROPPED for 2025+ (not offered). Escalade V (6.2L LT4 supercharged) is a separate halo - own oil spec, GATED. NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire (placard), transmission speed-binding, %s.'%GATE_MOD,
      'owner-manual-verified (per %s Cadillac Escalade OM; T1XX 6.2L, diesel dropped; Escalade V gated)'%om)
    print('  wrote %d (%d) T1XX 6.2 diesel-dropped'%(yr,vid))

db.commit()
print('\nDEFER check (should remain ai-haiku/scraped, untouched):')
for vid in [18105,291]:
    s=c.execute('SELECT v.year,v.model,o.source FROM vehicles v LEFT JOIN oil_change o ON o.vehicle_id=v.id WHERE v.id=?',(vid,)).fetchone()
    print('  id %d %s %s -> oil.source=%r (gated/deferred)'%(vid,s[0],s[1],s[2]))
db.close(); print('DONE.')
