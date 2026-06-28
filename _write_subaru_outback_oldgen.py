# Subaru Outback OLD-GEN - 9 rows (2000-06, 08, 09). First EJ-era slice.
# CORRECTED source set (2004/2005 were a name-collision mis-pull -> Impreza-Outback-Sport book; fixed to the
#   real Legacy-based Outback books 0404A/0504A). All 9 pass the EJ205/EJ257-absent test (real Outback, not Sport).
# Docs (cdn.subarunet.com): 2000 MSA5M0001A, 2001 0101A, 2002 0201A, 2003 0301A, 2004 0404A, 2005 0504A,
#   2006 0604A, 2008 0804A, 2009 0904A. Self-ID: combined Legacy/Outback book 2000-02 (code A22xx, Outback
#   illustration) -> Outback-focused 2003+. Combined-book self-ID = illustration + engine-roster, NOT name-count/segment.
# ALL EJ-SERIES, read fresh per year (EJ25 != FB25, EZ30 != EZ36 - nothing carried from modern):
#   BH 2000-2004: EJ251 2.5 NA + EZ30D 3.0 flat-6 (from 2001). 2000 = EJ251 only. NO turbo (XT debuts 2005).
#   BP 2005-2009: EJ253 2.5 NA + EJ255 2.5T turbo (XT) + EZ30D 3.0 flat-6 (3.0R).
# ** EZ30D within-era DRIFT (strict per-year caught): oil 6.0(01/02)->5.9(03)->5.6(04)->5.8(05-09);
#    coolant 8.1(01)->8.4(02-04)->7.6(05-09). EVERY BH year distinct. **
# Pre-CVT: 5-spd MT (gear oil GL-5 75W-90 3.7qt; BP 6MT-turbo 4.3) + 4-spd AT (Dexron III ATF). HYDRAULIC PS (NOT EPS).
# lug BH 58-72 ft-lb / BP 74-89 ft-lb (read per sub-gen, body grew). Brake FMVSS No.116 DOT 3/4. Spark GAP gated (type published).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_oboldgen_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE_NOTE='OM-published (Outback column, isolated from Legacy): P225/60R16 97H (BH/BP base; BP 17in higher trims). Legacy column is P205/55R16 - NOT used.'
PS='Hydraulic power steering - Subaru PS fluid, 0.7 qt / 0.7 L (this era is HYDRAULIC, NOT the modern EPS)'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both)'
COOLANT='Subaru genuine coolant (50/50 premix; spec number not stated in this era OM)'
def W(vid,visc,oilcw,trans,cc,diff,plugs,lug_lb,lug_nm,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,'API SL/SJ (starburst) [BH] / API SM, ILSAC GF-4 [BP]; SUBARU approved oil',None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,'55D23L (MT) / 75D23L (AT)',None,'P225/60R16 97H','30 psi','29 psi',plugs,None,None,None,None,TIRE_NOTE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',lug_lb,lug_nm,'%s lb-ft (%s N-m), wheel nut tightening torque per owner manual (range)'%(lug_lb,lug_nm),'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Legacy/Outback)",'standard',None,None,None)); nid+=1

PLUG_BH_NA=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.5L EJ251 (NA); BKR5E-11 alt","is_oem":True}])
PLUG_BH_BOTH=json.dumps([{"brand":"NGK","part_number":"BKR6E-11","description":"2.5L EJ251 (NA); BKR5E-11 alt","is_oem":True},{"brand":"NGK","part_number":"PLFR6A-11","description":"3.0L EZ30D flat-6","is_oem":True}])
PLUG_BP=json.dumps([{"brand":"NGK","part_number":"FR5AP-11","description":"2.5L EJ253 (NA)","is_oem":True},{"brand":"NGK","part_number":"SILFR6A","description":"2.5L EJ255 turbo (XT)","is_oem":True},{"brand":"NGK","part_number":"ILFR6B","description":"3.0L EZ30D flat-6 (3.0R)","is_oem":True}])
ATF_BH='5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt. 4-speed automatic (4EAT): Dexron III ATF, 9.8 qt. AT front diff 1.3 qt; rear diff 0.8 qt (GL-5).'
def bn(extra=''): return ('Fuel tank: 16.9 gal / 64 L. Pre-CVT era (4-spd auto / 5-spd manual). HYDRAULIC power steering (0.7 qt) - NOT EPS. '+extra+
    ' GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug/oil-filter torque, oil-filter part #.')

# BH 2000: EJ251 only
W(10973,'5W-30 (2.5L EJ251)','4.2 qt / 4.0 L (2.5L EJ251)',ATF_BH,'7.2 qt / 6.8 L (2.5L MT) / 7.1 qt / 6.7 L (2.5L AT)',
  json.dumps({"manual_transmission":"GL-5 75W-90: 3.7 qt","automatic_transmission":"Dexron III ATF: 9.8 qt","front_differential_at":"1.3 qt","rear_differential":"0.8 qt"}),PLUG_BH_NA,58.0,78.0,
  bn('Plug: EJ251 = BKR6E-11/BKR5E-11 (NGK).'),'owner-manual-verified (per 2000 Subaru Legacy/Outback combined OM MSA5M0001A, Outback column; code A2260BE; BH, EJ251 only)')
print('  2000 BH EJ251')
# BH 2001-2004: EJ251 + EZ30D (per-year EZ30 drift)
BH=[(10994,2001,'MSA5M0101A','A2280BE','6.0 qt / 5.7 L','8.1 qt / 7.7 L'),
    (11025,2002,'MSA5M0201A','A2290BE','6.0 qt / 5.7 L','8.4 qt / 7.9 L'),
    (11065,2003,'MSA5M0301A','A23xx','5.9 qt / 5.6 L','8.4 qt / 7.9 L'),
    (11116,2004,'MSA5M0404A','A24xx','5.6 qt / 5.3 L','8.4 qt / 7.9 L')]
for vid,yr,doc,code,ez_oil,ez_cool in BH:
    W(vid,'5W-30 (2.5L EJ251 & 3.0L EZ30D flat-6)','4.2 qt / 4.0 L (2.5L EJ251) / %s (3.0L EZ30D flat-6)'%ez_oil,ATF_BH,
      '7.2 qt / 6.8 L (2.5L MT) / 7.1 qt / 6.7 L (2.5L AT) / %s (3.0L EZ30D)'%ez_cool,
      json.dumps({"manual_transmission":"GL-5 75W-90: 3.7 qt","automatic_transmission":"Dexron III ATF: 9.8 qt","front_differential_at":"1.3 qt","rear_differential":"0.8 qt"}),PLUG_BH_BOTH,58.0,78.0,
      bn('Plugs: EJ251 = BKR6E-11/BKR5E-11 (NGK); EZ30D = PLFR6A-11 (NGK).'),
      'owner-manual-verified (per %d Subaru Legacy/Outback OM %s, Outback column; BH, EJ251 + EZ30D flat-6; lug 58-72)'%(yr,doc))
    print('  %d BH EJ251+EZ30D (EZ oil %s, cool %s)'%(yr,ez_oil[:7],ez_cool[:7]))
# BP 2005-2009: EJ253 + EJ255 turbo + EZ30D
BP=[(11178,2005,'MSA5M0504A'),(11249,2006,'MSA5M0604A'),(11411,2008,'MSA5M0804A'),(11502,2009,'MSA5M0904A')]
for vid,yr,doc in BP:
    W(vid,'5W-30 (2.5L EJ253 NA & 2.5L EJ255 turbo & 3.0L EZ30D flat-6)',
      '4.2 qt / 4.0 L (2.5L EJ253 NA) / 4.2 qt / 4.0 L (2.5L EJ255 turbo) / 5.8 qt / 5.5 L (3.0L EZ30D flat-6)',
      '5-speed manual (5MT): GL-5 75W-90 gear oil, 3.7 qt (6-speed MT turbo: 4.3 qt). 4-speed automatic: Dexron III ATF, 9.8 qt (turbo & 3.0L: 10.4 qt). AT front diff 1.3 qt (NA) / 1.5 qt (turbo & 3.0L); rear diff 0.8 qt (GL-5).',
      '6.8 qt / 6.4 L (2.5L NA MT) / 6.7 qt / 6.3 L (2.5L NA AT) / 7.7 qt / 7.3 L (2.5L turbo MT) / 7.6 qt / 7.2 L (2.5L turbo AT) / 7.6 qt / 7.2 L (3.0L EZ30D)',
      json.dumps({"manual_transmission":"GL-5 75W-90: 3.7 qt (turbo 6MT 4.3)","automatic_transmission":"Dexron III ATF: 9.8 qt (turbo/3.0 10.4)","front_differential_at":"1.3 qt NA / 1.5 qt turbo+3.0","rear_differential":"0.8 qt"}),PLUG_BP,74.0,100.0,
      bn('Plugs: EJ253 = FR5AP-11; EJ255 turbo = SILFR6A; EZ30D = ILFR6B (all NGK). XT turbo debuts 2005.'),
      'owner-manual-verified (per %d Subaru Outback OM %s, Outback column [EJ205/EJ257-absent verified = real Outback]; BP, EJ253 + EJ255 turbo + EZ30D; lug 74-89)'%(yr,doc))
    print('  %d BP EJ253+EJ255T+EZ30D'%yr)

db.commit()
print('\nVerify:')
for vid,lbl in [(10973,'2000'),(11025,'2002'),(11116,'2004'),(11178,'2005'),(11502,'2009')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT power_steering_fluid,transmission_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | lug=%s | PS=%s'%(lbl,vid,o[1][:38],lug,f[0][:24]))
db.close(); print('DONE - 9 rows.')
