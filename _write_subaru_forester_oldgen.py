# Subaru FORESTER SF/SG old-gen - 7 rows (2000-2006). CLOSES the Subaru old-gen arc (Outback + Impreza/WRX + Forester).
# STANDALONE book (no combined-book column isolation). Self-ID confirmed by illustration (HSF code, SUV body,
#   175.2in) + roster. Segment rotated 02 (2000-02) -> 04 (2003) -> 03 (2004-06): resolved by body, never the number.
# Docs (cdn.subarunet.com, TEXT-extractable): 2000 MSA5M0002A, 2001 0102A, 2002 0202A, 2003 0304A, 2004 0403A,
#   2005 0503A, 2006 0603A.
# Engine-era map: SF 2000-02 = EJ251 2.5 NA only; SG 2003 = EJ251 NA only (redesign, XT not yet);
#   SG 2004 = EJ251 NA + EJ255 2.5T XT (XT debut); SG 2005-06 = EJ253 NA + EJ255 2.5T XT. No flat-6, no EJ205, no STI.
# ** THE SLICE'S FINDING - body-decided specs (Forester's own; three-axis thesis as controlled experiment): **
#   - COOLING body-decided: EJ251 = 6.6 (SF) / 7.3-7.2 (SG) - distinct from Outback EJ251 7.2/7.1 AND Impreza
#     EJ251 6.2(GC)/7.4(GD). Same engine code, three bodies, three figures.
#   - EJ255 XT cooling 7.8/7.7 DIVERGES from WRX EJ255 8.1/8.0 (body) but oil 4.2 + plug ILFR6B MATCH WRX (engine).
#   - FUEL 15.9 (= Impreza, NOT Outback 16.9). TIRE Forester's own (SF P205/70R15 / SG P215/60R16; XT P215/55R17 by 2006).
#   - ENGINE-decided held flat: oil 4.2 all; plug EJ251=BKR6E-11, EJ253=FR5AP-11, EJ255 XT=ILFR6B (=WRX).
# ** Per-year drift: SF->SG coolant 6.6->7.3 (redesign); EJ251->EJ253 (2004->2005) moved PLUG (BKR6E-11->FR5AP-11)
#    not oil/cool; GAP published SF 2000-02 (0.039-0.043) -> WRITE, gated SG 2003+. lug 58-72 ALL years (read). **
# Pre-CVT: 4-spd auto Dexron III (2000/01 "Dexron II or III") + 5-spd MT GL-5 75W-90. HYDRAULIC PS. Brake FMVSS 116 DOT 3/4.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_forester_oldgen_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Hydraulic power steering - Subaru PS fluid, 0.7 qt / 0.7 L (this era is HYDRAULIC, NOT EPS)'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both)'
COOLANT='Subaru genuine coolant (50/50 premix; spec number not stated in this era OM)'
def W(vid,visc,oilcw,oilsrc,trans,cc,diff,plug_type,gap,plugs_json,tire,psi_f,psi_r,tnote,src,bn):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oilsrc,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,plug_type,gap,None,'55D23L (MT) / 75D23L (AT)',None,tire,psi_f,psi_r,plugs_json,None,None,None,None,tnote,None,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',58.0,78.0,'58 to 72 lb-ft (78 to 98 N-m), wheel nut tightening torque per owner manual (range)','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Forester)",'standard',None,None,None)); nid+=1

DIFF=json.dumps({"manual_transmission":"GL-5 75W-90: 3.7 qt","automatic_transmission":"Dexron III ATF: 9.8 qt","front_differential_at":"1.3 qt","rear_differential":"0.8 qt"})
PLUG_EJ251=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.5L EJ251 NA; BKR5E-11 alt; Champion RC10YC4, Denso K20PR-U11","is_oem":True}])
PLUG_SG04=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.5L EJ251 NA (BKR5E-11 alt)","is_oem":True},{"brand":"NGK","part_number":"IFLR6B","description":"2.5L EJ255 turbo (XT)","is_oem":True}])
PLUG_SG0506=json.dumps([{"brand":"NGK","part_number":"FR5AP-11","description":"2.5L EJ253 NA","is_oem":True},{"brand":"NGK","part_number":"ILFR6B","description":"2.5L EJ255 turbo (XT)","is_oem":True}])
ATF_SF='5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron II or Dexron III ATF, 9.8 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).'
ATF_SG='5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron III ATF, 9.8 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).'
def bn(extra=''): return ('Fuel tank: 15.9 gal / 60 L (= Impreza, NOT Outback 16.9). Pre-CVT (4-spd auto / 5-spd manual). HYDRAULIC power steering (0.7 qt) - NOT EPS. '+extra)
GATE_NOTE=' GATED (SG-gen OM does NOT print): spark-plug GAP, drain/oil-filter torque, oil-filter PN.'
SF_GAP_NOTE=' Spark-plug GAP IS published this SF-gen year (0.039-0.043 in) - WRITTEN. GATED: drain/oil-filter torque, oil-filter PN.'

# SF 2000-2002: EJ251 NA, cool 6.6, GAP PUBLISHED
for vid,yr,doc in [(13769,2000,'MSA5M0002A'),(14671,2001,'MSA5M0102A'),(15632,2002,'MSA5M0202A')]:
    W(vid,'5W-30 (2.5L EJ251 SOHC NA)','4.2 qt / 4.0 L (2.5L EJ251)','API SH/SJ/SL (starburst); SUBARU approved oil',
      ATF_SF,'6.6 qt / 6.2 L (2.5L EJ251)',DIFF,
      'NGK BKR6E-11 / BKR5E-11 (Champion RC10YC4, Denso K20PR-U11 alt)','0.039 to 0.043 in (1.0 to 1.1 mm)',PLUG_EJ251,
      'P205/70R15 95S (base) / P215/60R16 94H','29 psi','26 psi',
      'OM-published (Forester standalone book - body-decided, no column isolation): P205/70R15 (base) / P215/60R16. Distinct from Outback 225/60R16 and Impreza 195/60R15.',
      'owner-manual-verified (per %d Subaru Forester OM %s [SF gen, EJ251 2.5 NA; HSF illustration confirmed]; gap PUBLISHED; cooling 6.6 qt = Forester body-specific, differs from Outback 7.2 & Impreza 6.2/7.4)'%(yr,doc),
      bn('SF gen, EJ251 2.5 NA only (no turbo). Cooling 6.6 qt (Forester body-decided).'+SF_GAP_NOTE))
    print('  %d Forester SF EJ251 (cool 6.6, gap written)'%yr)
# SG 2003: EJ251 NA, cool 7.3/7.2 (redesign jump), GAP GATED
W(11062,'5W-30 (2.5L EJ251 SOHC NA)','4.2 qt / 4.0 L (2.5L EJ251)','API SL (starburst); SUBARU approved oil',
  ATF_SG,'7.3 qt / 6.9 L (MT) / 7.2 qt / 6.8 L (AT)',DIFF,
  'NGK BKR6E-11 / BKR5E-11 (Champion RC10YC4 alt)',None,PLUG_EJ251,
  'P215/60R16 94H','29 psi','28 psi',
  'OM-published (Forester standalone, body-decided): P215/60R16. Distinct from Outback 225/60R16 and Impreza 195/60R15.',
  'owner-manual-verified (per 2003 Subaru Forester OM MSA5M0304A [SG gen redesign, EJ251 2.5 NA; HSF illustration + 175.2in confirmed at odd seg "04"]; cooling JUMPED 6.6->7.3 at SF->SG redesign)',
  bn('SG gen (2003 redesign), EJ251 2.5 NA only (XT not yet). Cooling 7.3/7.2 - JUMPED from SF 6.6 at the redesign (body-decided, redesign-cooling-bump like Impreza GC->GD).'+GATE_NOTE))
print('  2003 Forester SG EJ251 (cool 7.3/7.2 redesign jump, gap gated)')
# SG 2004: EJ251 NA + EJ255 XT
W(11113,'5W-30 (2.5L EJ251 NA & 2.5L EJ255 turbo XT)','4.2 qt / 4.0 L (2.5L EJ251 NA) / 4.2 qt / 4.0 L (2.5L EJ255 turbo XT)',
  'API SL (starburst); SUBARU approved oil',ATF_SG,
  '7.3 qt / 6.9 L (2.5L NA MT) / 7.2 qt / 6.8 L (2.5L NA AT) / 7.8 qt / 7.4 L (2.5L XT turbo MT) / 7.7 qt / 7.3 L (2.5L XT turbo AT)',DIFF,
  'NGK BKR6E-11/BKR5E-11 (NA) ; IFLR6B (XT turbo)',None,PLUG_SG04,
  'P215/60R16 94H (NA) / P215/55R17 (XT)','29 psi','28 psi',
  'OM-published (Forester standalone, body-decided): NA P215/60R16; XT P215/55R17. Distinct from Outback/Impreza.',
  'owner-manual-verified (per 2004 Subaru Forester OM MSA5M0403A [SG gen, EJ251 NA + EJ255 2.5T XT DEBUT]; XT cooling 7.8/7.7 = Forester body-specific, DIVERGES from WRX EJ255 8.1/8.0; XT oil 4.2 + plug match WRX = engine-decided)',
  bn('SG gen, EJ251 2.5 NA + EJ255 2.5T XT (XT debut 2004). XT cooling 7.8/7.7 DIVERGES from WRX EJ255 8.1/8.0 (body-decided); XT oil 4.2 & plug = WRX (engine-decided).'+GATE_NOTE))
print('  2004 Forester SG EJ251+EJ255-XT (XT debut)')
# SG 2005-2006: EJ253 NA + EJ255 XT (NA code change EJ251->EJ253 moved plug)
for vid,yr,doc in [(11175,2005,'MSA5M0503A'),(11246,2006,'MSA5M0603A')]:
    W(vid,'5W-30 (2.5L EJ253 NA & 2.5L EJ255 turbo XT)','4.2 qt / 4.0 L (2.5L EJ253 NA) / 4.2 qt / 4.0 L (2.5L EJ255 turbo XT)',
      'API SL/SM (starburst); SUBARU approved oil',ATF_SG,
      '7.3 qt / 6.9 L (2.5L NA MT) / 7.2 qt / 6.8 L (2.5L NA AT) / 7.8 qt / 7.4 L (2.5L XT turbo MT) / 7.7 qt / 7.3 L (2.5L XT turbo AT)',DIFF,
      'NGK FR5AP-11 (NA) ; ILFR6B (XT turbo)',None,PLUG_SG0506,
      'P215/60R16 94H (NA) / P215/55R17 93H (XT)','29 psi','28 psi',
      'OM-published (Forester standalone, body-decided): NA P215/60R16; XT P215/55R17.',
      'owner-manual-verified (per %d Subaru Forester OM %s [SG gen, EJ253 NA + EJ255 2.5T XT]; NA code EJ251->EJ253 moved the PLUG BKR6E-11->FR5AP-11, not oil/cooling; XT cooling 7.8/7.7 diverges from WRX, oil/plug engine-decided)'%(yr,doc),
      bn('SG gen, EJ253 2.5 NA (code change from EJ251 moved plug to FR5AP-11) + EJ255 2.5T XT. XT cooling 7.8/7.7 (body) vs oil 4.2 + plug ILFR6B = WRX (engine).'+GATE_NOTE))
    print('  %d Forester SG EJ253+EJ255-XT'%yr)

db.commit()
print('\nVerify:')
for vid,lbl in [(13769,'2000SF'),(11062,'2003SG'),(11113,'2004XT'),(11246,'2006XT')]:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s(%d): oil=%s | cool=%s | gap=%s'%(lbl,vid,o[0][:30],f[0][:30],p[0]))
db.close(); print('DONE - 7 Forester rows. Subaru old-gen arc CLOSED.')
