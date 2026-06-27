# Subaru Crosstrek - 7 rows (GU 2018-21 + 3rd-gen 2024-26). Subaru sibling #3, FIRST new engine reads.
# Each engine read FRESH from Crosstrek's own (image-rendered) spec pages. Standalone manual.
# Self-ID: model code A13xx-A16xx (shared Impreza/Crosstrek platform) -> confirmed by impreza=0 differential
#   + filename "07" model-code + doc provenance (illustration = G4-fax, unrenderable here, logged follow-up).
#  GU gen (2018-2021): FB20 2.0L DI (12.5:1, 0W-20, 4.7qt, cool 8.2, plug DILKAR7B8); FB25 2.5L DI added 2021
#      (12.0:1, 0W-20, 4.4qt, cool 8.8, plug DILKAR7Q8). Per 2020 OM (MSA5M2007C) + 2021 OM (MSA5M2107A).
#  3rd gen (2024-2025): FB20 + FB25, BOTH **0W-16** required (0W-20 alt), 4.7qt; cool FB20 8.4/FB25 8.9;
#      plug DILKAR7Q8; battery LN2. Per 2024 OM (MSA5M2407A).
#  2026 (refresh, A16xx): FB25-ONLY (FB20 dropped), 0W-16, 4.7qt, cool 7.9. Per 2026 OM (MSA5M2607B).
# ** NEW ARTIFACTS: FB20 = first FB20 on record. 0W-16 = new viscosity grade (3rd-gen, required vs 0W-20 alt).
#    FB25 capacity 4.4 (GU) -> 4.7 (3rd-gen), proven via FB25-only 2026 OM. FB20 plug DILKAR7B8->DILKAR7Q8. **
# Common (read): SUBARU Super Coolant; diff front 1.4qt/rear 0.8qt GL-5 75W-90 (incl 2026, read); brake
#   FMVSS No.116 DOT 3/4; lug 89 lb-ft (120 N-m, read from Crosstrek OM); fuel 16.6 gal; EPS.
# OM PUBLISHES (write): plug-type, battery, tire. GATED: spark GAP, CVT fluid (consult dealer), drain/filter torque, oil-filter PN.
# PHEV (2019-2021) + Hybrid (2026): gated VARIANT note on the generic gas rows; HV system NEVER written (no PHEV/Hybrid DB row).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_crosstrek_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
def W(vid,visc,oem,oilcw,trans,cc,diff,plugs,batt,tire,tnote,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,batt,None,tire,'33 psi','32 psi',plugs,None,None,None,None,tnote,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',89.0,120.0,'89 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Crosstrek)",'standard',None,None,None)); nid+=1

DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.4 qt/1.3 L","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
PHEV_NOTE=(' PHEV VARIANT (Crosstrek Hybrid plug-in) exists this year: it has an FB20-based Atkinson gas engine PLUS a high-voltage hybrid/traction-battery system - '
  'the HV system, traction battery, and hybrid-specific service specs are GATED (not covered by this gas OM; no separate PHEV row in DB). Gas-side specs above are for the standard (non-plug-in) Crosstrek.')

# ===== GU FB20-only (2018, 2019, 2020) =====
GU_FB20_BN=('OM-published & written: spark-plug type DILKAR7B8 (NGK), battery 75D23L (Q-85 with Auto Start Stop), tire size/pressure. '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 10.8 qt. Fuel: 16.6 gal / 63 L. '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
GU_PLUGS_FB20=json.dumps([{"brand":"NGK","part_number":"DILKAR7B8","description":"2.0L FB20 (direct-injection)","is_oem":True}])
for vid,yr,phev in [(12560,2018,False),(12713,2019,True),(911,2020,True)]:
    bn=GU_FB20_BN+(PHEV_NOTE if phev else '')
    W(vid,'0W-20 synthetic (2.0L FB20)','API SN / SN PLUS, ILSAC GF-5; use SUBARU approved engine oil',
      '4.7 qt / 4.4 L (2.0L FB20)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '8.2 qt / 7.8 L (2.0L FB20, CVT)',DIFF,GU_PLUGS_FB20,'75D23L','P225/60R17 98H',
      'OM-published (by trim): P225/60R17 98H or 225/55R18 98H; 33 psi front / 32 rear.',bn,
      'owner-manual-verified (per 2020 Subaru Crosstrek OM MSA5M2007C, self-ID model code A1370BE-C + filename "07" Crosstrek + impreza=0 differential; GU gen-rep, FB20 EPA-stable 2018-20)')
    print('  Crosstrek %d GU FB20%s'%(yr,' +PHEV note' if phev else ''))

# ===== GU FB20 + FB25 (2021) =====
G21_BN=('OM-published & written: spark-plug type (per engine), battery 75D23L (Q-85 with Auto Start Stop), tire size/pressure. '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 10.8 qt (2.0L) / 12.0 qt (2.5L). Fuel: 16.6 gal / 63 L. '
  'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.'+PHEV_NOTE)
G21_PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7B8","description":"2.0L FB20 (direct-injection)","is_oem":True},{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.5L FB25 (direct-injection)","is_oem":True}])
W(2404,'0W-20 synthetic (2.0L FB20 & 2.5L FB25)','API SN / SN PLUS, ILSAC GF-5; use SUBARU approved engine oil',
  '4.7 qt / 4.4 L (2.0L FB20) / 4.4 qt / 4.2 L (2.5L FB25)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
  '8.2 qt / 7.8 L (2.0L FB20, CVT) / 8.8 qt / 8.3 L (2.5L FB25, CVT)',DIFF,G21_PLUGS,'75D23L','P225/60R17 98H',
  'OM-published (by trim): P225/60R17 98H or 225/55R18 98H; 33 psi front / 32 rear.',G21_BN,
  'owner-manual-verified (per 2021 Subaru Crosstrek OM MSA5M2107A, self-ID code A1410BE-A + filename "07" + impreza=0; GU, FB20+FB25 [FB25 added 2021])')
print('  Crosstrek 2021 GU FB20+FB25 +PHEV note')

# ===== 3rd gen FB20 + FB25 (2024, 2025) - 0W-16 =====
G3_BN=('OM-published & written: spark-plug type DILKAR7Q8 (NGK, both engines), battery LN2 (Q-85 with Auto Start Stop), tire size/pressure. '
  '** 3rd-gen redesign: oil is 0W-16 synthetic REQUIRED (0W-20 acceptable alternative only); FB25 oil cap 4.7 qt (vs GU 4.4). ** '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 10.8 qt (2.0L) / 11.9 qt (2.5L). Fuel: 16.6 gal / 63 L. '
  'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
G3_PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.0L FB20 & 2.5L FB25 (direct-injection, 3rd gen)","is_oem":True}])
for vid,yr,om in [(7041,2024,'2024 Subaru Crosstrek OM MSA5M2407A'),(8618,2025,'2024 Crosstrek OM MSA5M2407A rep')]:
    W(vid,'0W-16 synthetic REQUIRED (2.0L FB20 & 2.5L FB25); 0W-20 acceptable alternative','API SP, ILSAC GF-6B (0W-16) / GF-6A (0W-20); use SUBARU approved engine oil',
      '4.7 qt / 4.4 L (2.0L FB20 & 2.5L FB25)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '8.4 qt / 7.9 L (2.0L FB20, CVT) / 8.9 qt / 8.4 L (2.5L FB25, CVT)',DIFF,G3_PLUGS,'LN2','P225/60R17 99H',
      'OM-published (by trim): 225/60R17 99H or 225/55R18 98V; 33 psi front / 32 rear.',G3_BN,
      'owner-manual-verified (per %s, self-ID code A152x/A1520BE-A + filename "07" + impreza=0; 3rd gen, FB20+FB25 0W-16)'%om)
    print('  Crosstrek %d 3rd-gen FB20+FB25 (0W-16)'%yr)

# ===== 2026 refresh FB25-only - 0W-16 =====
G26_BN=('OM-published & written: spark-plug type DILKAR7Q8 (NGK), battery LN2 (Q-85 with Auto Start Stop), tire size/pressure. '
  '** 2026 refresh: FB20 DROPPED - gas base is FB25 only. Oil 0W-16 REQUIRED (0W-20 alt); FB25 cap 4.7 qt; coolant 7.9 qt (vs 2024 8.9 - refresh). ** '
  'CVT fluid type = consult dealer (GATED); capacity guideline (CVT): 11.9 qt. Fuel: 16.6 gal / 63 L. '
  'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.'
  ' HYBRID VARIANT (2026 Crosstrek Hybrid, series hybrid) exists: HV system / traction battery / hybrid-specific specs GATED (no separate Hybrid row in DB). Gas-side specs above are for the FB25 Crosstrek.')
W(10238,'0W-16 synthetic REQUIRED (2.5L FB25); 0W-20 acceptable alternative','API SP, ILSAC GF-6B (0W-16) / GF-6A (0W-20); use SUBARU approved engine oil',
  '4.7 qt / 4.4 L (2.5L FB25)','CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
  '7.9 qt / 7.5 L (2.5L FB25, CVT)',DIFF,
  json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.5L FB25 (direct-injection)","is_oem":True}]),'LN2','P225/60R17 99H',
  'OM-published (by trim): 225/60R17 99H or 225/55R18 98V (Wilderness 225/60R17 99T); 33 psi front / 32 rear.',G26_BN,
  'owner-manual-verified (per 2026 Subaru Crosstrek OM MSA5M2607B, self-ID code A1630BE-B + filename "07" + impreza=0; 3rd-gen refresh, FB25-only [FB20 dropped], 0W-16)')
print('  Crosstrek 2026 FB25-only (0W-16) +Hybrid note')

db.commit()
print('\nVerify:')
for vid,lbl in [(12560,'18 GU FB20'),(2404,'21 FB20+FB25'),(7041,'24 3rd'),(10238,'26 FB25')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | %s | batt=%s tire=%s gap=%s lug=%s'%(lbl,vid,o[0][:34],o[1][:30],p[0],p[1],p[2],lug))
db.close(); print('DONE - 7 rows.')
