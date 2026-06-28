# Subaru IMPREZA + WRX EJ-era - 9 rows (Impreza 2000-04 x5; WRX 2003/04/05/07 x4). 2 WRX defer (2006,2008).
# PAIRED slice: Impreza + WRX share the combined Impreza/WRX/Outback-Sport/STI book (the book the Outback
#   catch pre-protected). THREE-WAY column isolation per shared book: base Impreza (EJ22/EJ25) | WRX-turbo
#   (EJ205/EJ255) | Outback-Sport trim (-> base Impreza) | STI EJ257 (NO DB row -> EXCLUDED, never folded).
# Docs (cdn.subarunet.com, all TEXT-extractable, self-ID by illustration+roster): Impreza 2000 MSA5M0003A,
#   2001 0103A, 2002 0203A, 2003 0303A, 2004 0401A; WRX 2003 0303A, 2004 0401A, 2005 0501A, 2007 0701A.
# ALL EJ-series read FRESH per column (EJ22/EJ205 are NEW; Impreza EJ25 != Outback EJ251/253; WRX EJ255 != Outback BP EJ255):
#   IMPREZA base: 2000-01 = EJ222 2.2 + EJ251 2.5 (GC gen); 2002-04 = EJ251 2.5 only (GD gen, EJ22 dropped).
#   WRX turbo: 2003-05 = EJ205 2.0T; 2007 = EJ255 2.5T (2.0->2.5 switch was 2006 = DEFERRED switch year).
# ** KEY CATCHES (read-fresh, OM-stated): **
#   - WRX turbo OIL 4.8 (2003-04) -> 4.2 (2005 & 2007). OM-stated, corroborated 2 yrs. The famous community
#     figure is 4.8; we WRITE 4.2 per the manual (verified-source > prior knowledge). DO NOT "correct" to 4.8.
#   - Impreza coolant GC 6.2 -> GD 7.4/7.3 (redesign). Impreza EJ251 cool 7.4 != Outback EJ251 7.2 (body-decides-cooling).
#   - Spark GAP published 2000/01 (0.039-0.043 in) -> WRITE; gated 2002+ (modern Subaru gates it, old OMs print it 2 yrs).
#   - lug 58-72 ft-lb BOTH nameplates (read; lighter than Outback BP 74-89, matches BH).
# Pre-CVT: 4-spd auto = Dexron III ATF; 5-spd MT (WRX 5MT; 6-spd is STI); HYDRAULIC PS. Brake FMVSS 116 DOT 3/4.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_imprezawrx_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Hydraulic power steering - Subaru PS fluid, 0.7 qt / 0.7 L (this era is HYDRAULIC, NOT EPS)'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both)'
COOLANT='Subaru genuine coolant (50/50 premix; spec number not stated in this era OM)'
def W(vid,visc,oilcw,oilsrc,trans,cc,diff,bgroup,plug_type,gap,plugs_json,tire,psi_f,psi_r,tnote,lug_lb,lug_nm,src,bn):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oilsrc,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,plug_type,gap,None,bgroup,None,tire,psi_f,psi_r,plugs_json,None,None,None,None,tnote,None,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',lug_lb,lug_nm,'%s lb-ft (%s N-m), wheel nut tightening torque per owner manual (range)'%(lug_lb,lug_nm),'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Impreza/WRX)",'standard',None,None,None)); nid+=1

# ---- IMPREZA base column ----
DIFF_IMP=json.dumps({"manual_transmission":"GL-5 75W-90: 3.7 qt","automatic_transmission":"Dexron III ATF: 9.8 qt (2000-01) / 10.0 qt (2002+)","front_differential_at":"1.3 qt","rear_differential":"0.8 qt"})
# 2000-2001 GC: EJ222 2.2 + EJ251 2.5, gap PUBLISHED
PLUG_GC=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.2L EJ222 & 2.5L EJ251; Champion RC10YC4/RC8YC4, Denso K20PR-U11 alt","is_oem":True}])
for vid,yr,doc,code in [(13770,2000,'MSA5M0003A','A2160BE'),(14672,2001,'MSA5M0103A','A2180BE')]:
    W(vid,'5W-30 (2.2L EJ222 & 2.5L EJ251)','4.2 qt / 4.0 L (2.2L EJ222) / 4.2 qt / 4.0 L (2.5L EJ251)',
      'API SH/SJ (starburst); SUBARU approved oil',
      '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron II or Dexron III ATF, 9.8 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).',
      '6.2 qt / 5.8 L (2.2L EJ222) / 6.2 qt / 5.8 L (2.5L EJ251)',DIFF_IMP,'55D23L (MT) / 75D23L (AT)',
      'NGK BKR6E-11 (Champion RC10YC4/RC8YC4, Denso K20PR-U11 alt)','0.039 to 0.043 in (1.0 to 1.1 mm)',PLUG_GC,
      'P195/60R15 (base L/2.5) / P205/55R16 (RS) / P205/60R15 (Outback Sport)','32 psi','29 psi',
      'OM-published (base Impreza column, isolated from WRX/STI): base P195/60R15; RS P205/55R16; Outback Sport P205/60R15. WRX 215/45R17 / STI 225/45R17 NOT used (separate models).',
      58.0,78.0,
      'owner-manual-verified (per %d Subaru Impreza OM %s, base-Impreza column [EJ222 2.2 + EJ251 2.5, GC gen]; code %s; gap PUBLISHED)'%(yr,doc,code),
      'Fuel tank: 15.9 gal / 60 L. Pre-CVT (4-spd auto / 5-spd manual). HYDRAULIC power steering (0.7 qt) - NOT EPS. Spark-plug GAP IS published this year (0.039-0.043 in). GATED (OM does NOT print): drain/oil-filter torque, oil-filter part #.')
    print('  %d Impreza GC EJ222+EJ251 (gap written)'%yr)
# 2002-2004 GD: EJ251 2.5 only (EJ22 dropped); coolant jumped to 7.4/7.3; gap GATED
PLUG_GD=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.5L EJ251 (SOHC); BKR5E-11 alt; Champion RC10YC4","is_oem":True}])
for vid,yr,doc in [(11023,2002,'MSA5M0203A'),(11063,2003,'MSA5M0303A'),(11114,2004,'MSA5M0401A')]:
    W(vid,'5W-30 (2.5L EJ251 SOHC)','4.2 qt / 4.0 L (2.5L EJ251)',
      'API SJ/SL (starburst); SUBARU approved oil',
      '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron III ATF, 10.0 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).',
      '7.4 qt / 7.0 L (2.5L MT) / 7.3 qt / 6.9 L (2.5L AT)',DIFF_IMP,'55D23L (MT) / 75D23L (AT)',
      'NGK BKR6E-11 / BKR5E-11 (Champion RC10YC4 alt)',None,PLUG_GD,
      'P195/60R15 88H (base) / P205/55R16 89V (RS)','32 psi','29 psi',
      'OM-published (base Impreza column, isolated from WRX/STI): base P195/60R15; RS P205/55R16. WRX 215/45R17 / STI 225/45R17 NOT used.',
      58.0,78.0,
      'owner-manual-verified (per %d Subaru Impreza/WRX OM %s, base-Impreza column [EJ251 2.5 SOHC, GD gen]; WRX/STI columns excluded)'%(yr,doc),
      'Fuel tank: 15.9 gal / 60 L. Pre-CVT (4-spd auto / 5-spd manual). HYDRAULIC PS (0.7 qt) - NOT EPS. GATED (GD-gen OM does NOT print): spark-plug GAP, drain/oil-filter torque, oil-filter PN. (GC 2000/01 OM did print the gap; GD dropped it.)')
    print('  %d Impreza GD EJ251 (cool 7.4/7.3, gap gated)'%yr)

# ---- WRX turbo column ----
DIFF_WRX=json.dumps({"manual_transmission":"5-speed (5MT): GL-5 75W-90 gear oil, 3.7 qt","automatic_transmission":"Dexron III ATF: 10.0 qt","front_differential_at":"1.3 qt","rear_differential":"0.8 qt"})
PLUG_EJ205=json.dumps([{"brand":"NGK","part_number":"PFR6G","description":"2.0L EJ205 turbo (WRX)","is_oem":True}])
PLUG_EJ255=json.dumps([{"brand":"NGK","part_number":"ILFR6B","description":"2.5L EJ255 turbo (WRX)","is_oem":True}])
WRXTNOTE='OM-published (WRX turbo column, isolated from base Impreza/STI): WRX 215/45R17. Base Impreza 195/60R15 & STI 225/45R17 NOT used.'
def wrx_bn(extra=''): return ('Fuel tank: 15.9 gal / 60 L. Pre-CVT: WRX 5-speed MANUAL (6-spd is STI) + 4-spd auto (Dexron III). HYDRAULIC PS (0.7 qt) - NOT EPS. '+extra+' GATED (OM does NOT print): spark-plug GAP, drain/oil-filter torque, oil-filter PN.')
# 2003/2004 EJ205 oil 4.8
for vid,yr,doc in [(11066,2003,'MSA5M0303A'),(11117,2004,'MSA5M0401A')]:
    W(vid,'5W-30 (2.0L EJ205 turbo)','4.8 qt / 4.5 L (2.0L EJ205 turbo)',
      'API SJ/SL (starburst); SUBARU approved oil',
      '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron III ATF, 10.0 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).',
      '8.1 qt / 7.7 L (MT) / 8.0 qt / 7.6 L (AT)',DIFF_WRX,'55D23L (MT) / 65D23L (AT)',
      'NGK PFR6G',None,PLUG_EJ205,'215/45R17 87W','33 psi','32 psi',WRXTNOTE,58.0,78.0,
      'owner-manual-verified (per %d Subaru Impreza/WRX OM %s, WRX-turbo column [EJ205 2.0T]; base-Impreza & STI EJ257 columns excluded)'%(yr,doc),
      wrx_bn('Engine: EJ205 2.0L turbo; oil 4.8 qt (OM-stated for 2003-04).'))
    print('  %d WRX EJ205 2.0T (oil 4.8)'%yr)
# 2005 EJ205 oil 4.2 (OM-stated, divergent from 03/04 4.8)
W(11179,'5W-30 (2.0L EJ205 turbo)','4.2 qt / 4.0 L (2.0L EJ205 turbo)',
  'API SL (starburst); SUBARU approved oil',
  '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron III ATF, 10.0 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).',
  '8.1 qt / 7.7 L (MT) / 8.0 qt / 7.6 L (AT)',DIFF_WRX,'55D23L (MT) / 65D23L (AT)',
  'NGK PFR6G',None,PLUG_EJ205,'215/45R17','33 psi','32 psi',WRXTNOTE,58.0,78.0,
  'owner-manual-verified (per 2005 Subaru Impreza/WRX OM MSA5M0501A, WRX-turbo column [EJ205 2.0T]; oil 4.2 qt OM-stated [single engine-oil value, NOT split], divergent from 2003-04 4.8 - written per manual not the common 4.8 figure; STI EJ257 excluded)',
  wrx_bn('Engine: EJ205 2.0L turbo. NOTE: 2005 OM states engine oil 4.2 qt (single value, all engines) - DIVERGENT from 2003-04 4.8 qt and from the common community figure (4.8). Written as the OM states it; do NOT "correct" to 4.8.'))
print('  2005 WRX EJ205 2.0T (oil 4.2 OM-stated, flagged)')
# 2007 EJ255 2.5T oil 4.2 plug ILFR6B
W(11327,'5W-30 (2.5L EJ255 turbo)','4.2 qt / 4.0 L (2.5L EJ255 turbo)',
  'API SL/SM (starburst); SUBARU approved oil',
  '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic: Dexron III ATF, 10.0 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).',
  '8.1 qt / 7.7 L (MT) / 8.0 qt / 7.6 L (AT)',DIFF_WRX,'55D23L (MT) / 75D23L (AT)',
  'NGK ILFR6B',None,PLUG_EJ255,'215/45R17','33 psi','32 psi',WRXTNOTE,58.0,78.0,
  'owner-manual-verified (per 2007 Subaru Impreza/WRX OM MSA5M0701A, WRX-turbo column [EJ255 2.5T - the 2.0->2.5 switch, distinct from Outback BP EJ255 tune]; oil 4.2 OM-stated; STI EJ257 excluded)',
  wrx_bn('Engine: EJ255 2.5L turbo (WRX switched 2.0->2.5; 2006 switch year DEFERRED). Oil 4.2 qt OM-stated. Plug ILFR6B.'))
print('  2007 WRX EJ255 2.5T (oil 4.2, plug ILFR6B)')

db.commit()
print('\nVerify (2006/2008 WRX left UNTOUCHED = still gated):')
for vid in [11250,11412]:
    o=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    y=c.execute('SELECT year,model FROM vehicles WHERE id=?',(vid,)).fetchone()
    print('  %d %s %s -> oil src: %s (DEFER, unchanged)'%(vid,y[0],y[1],o[0] if o else 'none'))
for vid,lbl in [(13770,'2000imp'),(11023,'2002imp'),(11066,'2003wrx'),(11179,'2005wrx'),(11327,'2007wrx')]:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT spark_plug_gap,tire_size FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s(%d): oil=%s | gap=%s | tire=%s'%(lbl,vid,o[0][:34],p[0],p[1][:18]))
db.close(); print('DONE - 9 written, 2 deferred-untouched.')
