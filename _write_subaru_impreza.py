# Subaru Impreza - 5 modern rows (GK 2019-21 + new-gen 2024/2026). Subaru sibling #4, Crosstrek mirror-twin.
# Self-ID via mirror differential: impreza=0 AND crosstrek=0 + filename "01" + model code A13-16xx (Crosstrek's +10:
#   A1380 2020 / A1530 2024 / A1640 2026 vs Crosstrek A1370/A1520/A1630). crosstrek=0 rules out the twin.
# Each engine read FRESH from Impreza's own (image-rendered) spec pages - twin predicts, OM decides.
#  GK gen (2019-2021): FB20 2.0L DI (12.5:1, 0W-20, 4.7qt, cool 8.2, plug DILKAR7B8, batt 75D23L, fuel 13.2gal,
#      tire 205/55R16). Per 2020 OM MSA5M2001A (A1380BE-A). [matches Crosstrek FB20 on oil/cool; diverges on fuel/tire]
#  new-gen (2024): FB20 + FB25, 0W-16 REQUIRED (0W-20 alt), 4.7qt; cool FB20 8.4/FB25 8.9; plug DILKAR7Q8;
#      batt Q-85; fuel 16.6gal (jumped at redesign). Per 2024 OM MSA5M2401A (A1530BE-A).
#  2026 (refresh A1640): FB20 + FB25 (KEPT - Crosstrek 2026 dropped FB20), 0W-16, 4.7qt; cool FB20 8.4/**FB25 7.9**
#      (2026 platform-wide refresh, confirmed on both twins); plug DILKAR7Q8; batt Q-85. Per 2026 OM MSA5M2601A.
# ** TWIN DIVERGENCES (read, not carried): fuel 13.2(GK)->16.6; tire 205/55R16 (vs Crosstrek 225/60R17);
#    2026 keeps FB20+FB25 (Crosstrek dropped FB20); battery Q-85 (Crosstrek new-gen LN2). **
# Common (read): SUBARU Super Coolant; diff front 1.4qt/rear 0.8qt GL-5 75W-90; brake FMVSS No.116 DOT 3/4;
#   lug 89 lb-ft (120 N-m, read from Impreza OM); EPS. OM publishes -> WRITE plug/battery/tire; GATE spark gap,
#   CVT fluid (consult dealer), drain/filter torque, oil-filter PN.
# DEFER: 2000-2004 GD/GG EJ-series (old-doc discovery). EXCLUDED: WRX/STI (separate model). Ignored: 1993-99 neg-id.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_impreza_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.4 qt/1.3 L","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
def W(vid,visc,oem,oilcw,trans,cc,plugs,batt,tire,tnote,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,DIFF,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,batt,None,tire,'33 psi','32 psi',plugs,None,None,None,None,tnote,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',89.0,120.0,'89 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Impreza)",'standard',None,None,None)); nid+=1

# ===== GK gen (2019-2021): FB20 only =====
GK_PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7B8","description":"2.0L FB20 (direct-injection)","is_oem":True}])
GK_BN=('OM-published & written: spark-plug type DILKAR7B8 (NGK), battery 75D23L, tire size/pressure. '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 11.3 qt. Fuel: 13.2 gal / 50 L (sedan & 5-door). '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
GK_SRC='owner-manual-verified (per 2020 Subaru Impreza OM MSA5M2001A, self-ID model code A1380BE-A + filename "01" Impreza + mirror differential impreza=0 AND crosstrek=0; GK gen-rep, FB20 EPA-stable 2019-21)'
for vid,yr in [(12715,2019),(908,2020),(2401,2021)]:
    W(vid,'0W-20 synthetic (2.0L FB20)','API SN / SN PLUS, ILSAC GF-5; use SUBARU approved engine oil',
      '4.7 qt / 4.4 L (2.0L FB20)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '8.2 qt / 7.8 L (2.0L FB20, CVT)',GK_PLUGS,'75D23L','P205/55R16 89V',
      'OM-published (by trim): P205/55R16 89V / 205/50R17 89V / P225/40R18 88V; 33 psi front / 32 rear.',GK_BN,GK_SRC)
    print('  Impreza %d GK FB20 (0W-20/4.7, fuel 13.2, tire 205/55R16)'%yr)

# ===== new-gen 2024: FB20 + FB25, 0W-16 =====
NG_PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.0L FB20 & 2.5L FB25 (direct-injection)","is_oem":True}])
W(7038,'0W-16 synthetic REQUIRED (2.0L FB20 & 2.5L FB25); 0W-20 acceptable alternative','API SP, ILSAC GF-6B (0W-16) / GF-6A (0W-20); use SUBARU approved engine oil',
  '4.7 qt / 4.4 L (2.0L FB20 & 2.5L FB25)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
  '8.4 qt / 7.9 L (2.0L FB20, CVT) / 8.9 qt / 8.4 L (2.5L FB25, CVT)',NG_PLUGS,'Q-85','205/55R16 91V',
  'OM-published (by trim): 205/55R16 91V / 205/50R17 89V / P225/40R18 88V; 16in 36/35 psi, 17-18in 33/32 psi.',
  ('OM-published & written: spark-plug type DILKAR7Q8 (NGK, both engines), battery Q-85, tire size/pressure. '
   '** 2024 redesign: oil 0W-16 REQUIRED (0W-20 alt); FB25 added (RS). Fuel jumped to 16.6 gal / 63 L (was 13.2 GK - now matches platform). ** '
   'CVT fluid type = consult dealer (GATED); capacity guideline (CVT): 10.8 qt (2.0L) / 12.0 qt (2.5L). '
   'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.'),
  'owner-manual-verified (per 2024 Subaru Impreza OM MSA5M2401A, self-ID A1530BE-A + filename "01" + impreza=0/crosstrek=0; new-gen, FB20+FB25 0W-16)')
print('  Impreza 2024 new-gen FB20+FB25 (0W-16/4.7, fuel 16.6, batt Q-85)')

# ===== 2026 refresh (A1640): FB20 + FB25 kept, FB25 coolant 7.9 =====
W(10235,'0W-16 synthetic REQUIRED (2.0L FB20 & 2.5L FB25); 0W-20 acceptable alternative','API SP, ILSAC GF-6B (0W-16) / GF-6A (0W-20); use SUBARU approved engine oil',
  '4.7 qt / 4.4 L (2.0L FB20 & 2.5L FB25)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
  '8.4 qt / 7.9 L (2.0L FB20, CVT) / 7.9 qt / 7.5 L (2.5L FB25, CVT)',NG_PLUGS,'Q-85','205/55R16 91V',
  'OM-published (by trim): 205/55R16 91V / 205/50R17 89V / P225/40R18 88V; 16in 36/35 psi, 17-18in 33/32 psi.',
  ('OM-published & written: spark-plug type DILKAR7Q8 (NGK, both engines), battery Q-85, tire size/pressure. '
   '** 2026 refresh: KEEPS FB20+FB25 (unlike Crosstrek 2026 which dropped FB20). FB25 coolant 7.9 qt (was 8.9 in 2024) - '
   '2026 platform-wide refresh, confirmed on both Impreza & Crosstrek. Oil 0W-16 REQUIRED (0W-20 alt). Fuel 16.6 gal. ** '
   'CVT fluid type = consult dealer (GATED); capacity guideline (CVT): 10.8 qt (2.0L) / 12.0 qt (2.5L). '
   'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.'),
  'owner-manual-verified (per 2026 Subaru Impreza OM MSA5M2601A, self-ID A1640BE-A + filename "01" + impreza=0/crosstrek=0; 2026 refresh, FB20+FB25 0W-16, FB25 cool 7.9)')
print('  Impreza 2026 refresh FB20+FB25 (FB25 cool 7.9, kept FB20)')

db.commit()
print('\nVerify:')
for vid,lbl in [(12715,'19 GK'),(7038,'24 new-gen'),(10235,'26 refresh')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()[0]
    p=c.execute('SELECT battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | cool=%s | batt=%s tire=%s gap=%s lug=%s'%(lbl,vid,o[0][:30],f[:34],p[0],p[1],p[2],lug))
print('\nDEFER check (untouched):')
for vid,yr in [(11023,2002),(11114,2004)]:
    s=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d (%d): %s'%(vid,yr,s[0] if s else 'no row'))
db.close(); print('DONE - 5 rows.')
