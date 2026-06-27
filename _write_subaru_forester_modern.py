# Subaru Forester MODERN - 8 rows (SJ 2017-18 + SK 2019-24). Subaru sibling #2.
# Each engine read FRESH from Forester's OWN (image-rendered) spec pages. Standalone manual.
#  SJ gen (2017-2018): FB25 NA (port-inj, 10.3:1, 0W-20, 5.1qt, cool 8.1, plug SILZKAR7B11)
#      + FA20 2.0 TURBO (5W-30, 5.4qt, cool 9.5, plug ILKAR8H6). Per 2018 OM MSA5M1802B (self-ID A8230BE-B).
#  SK gen (2019-2024): FB25 NA DIRECT-inj (12.0:1, 0W-20, 4.4qt, cool 9.0, plug DILKAR7Q8). Turbo dropped.
#      Per 2019 OM MSA5M1902B (self-ID A8240BE-B). FB25 port->direct divergence = platform-level (matches Outback).
# Common: SUBARU Super Coolant; front diff GL-5 75W-90 (SJ 1.3 NT/1.5 turbo, SK 1.4); rear diff 0.8qt;
#   brake FMVSS No.116 DOT 3 or DOT 4; lug 89 lb-ft (120 N-m, Forester prints 89 vs Outback 88.5); EPS.
# OM PUBLISHES (write, not gate): spark-plug TYPE, battery type, tire size/pressure (Electrical/Tires spec pages).
# GATED (genuinely not in OM): spark-plug GAP, CVT fluid (consult dealer), drain/oil-filter torque, oil-filter PN.
# DEFER: 2025/2026 (no full OM - only 216pp partial - + new Hybrid variant); 2000-2006 (old-doc discovery).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_forester_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
OEM='API SN / SN PLUS, ILSAC GF-5 (starburst); use SUBARU approved engine oil'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
def W(vid,visc,oilcw,trans,cc,diff,plugs_json,batt,tire,tirep_f,tirep_r,tnote,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,OEM,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,batt,None,tire,tirep_f,tirep_r,plugs_json,None,None,None,None,tnote,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',89.0,120.0,'89 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Forester)",'standard',None,None,None)); nid+=1

# ===== SJ gen (2017-2018): FB25 port + FA20 turbo =====
SJ_DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.3 qt/1.2 L (FB25 non-turbo) / 1.5 qt/1.4 L (FA20 turbo)","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
SJ_PLUGS=json.dumps([{"brand":"NGK","part_number":"SILZKAR7B11","description":"2.5L FB25 (non-turbo)","is_oem":True},{"brand":"NGK","part_number":"ILKAR8H6","description":"2.0L FA20 turbo","is_oem":True}])
SJ_TNOTE='OM-published (by trim): P225/60R17 98H (30 psi front / 29 rear) or P225/55R18 97H (32/30); FA20 turbo P225/55R18 97H (33/32).'
SJ_BN=('OM-published & written: spark-plug TYPE (per engine), battery 75D23L (US), tire size/pressure. '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 12.6 qt (non-turbo) / 13.1 qt (turbo). '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
SJ_SRC='owner-manual-verified (per 2018 Subaru Forester OM MSA5M1802B, self-ID model code A8230BE-B + p2 vehicle illustration; SJ gen-rep, FB25 + FA20 turbo EPA-stable 2017-18)'
for vid,yr in [(12417,2017),(12561,2018)]:
    W(vid,'0W-20 synthetic (2.5L FB25 non-turbo); 5W-30 (2.0L FA20 turbo)',
      '5.1 qt / 4.8 L (2.5L FB25 non-turbo) / 5.4 qt / 5.1 L (2.0L FA20 turbo)',
      'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '8.1 qt / 7.7 L (2.5L FB25 non-turbo) / 9.5 qt / 9.0 L (2.0L FA20 turbo)',
      SJ_DIFF,SJ_PLUGS,'75D23L (US)','P225/60R17 98H','30 psi (non-turbo, base 17in)','29 psi (non-turbo, base 17in)',SJ_TNOTE,SJ_BN,SJ_SRC)
    print('  Forester %d SJ (FB25 0W-20/5.1 + FA20 turbo 5W-30/5.4)'%yr)

# ===== SK gen (2019-2024): FB25 direct-injection =====
SK_DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.4 qt/1.3 L","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
SK_PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.5L FB25 (direct-injection)","is_oem":True}])
SK_TNOTE='OM-published (by trim): P225/60R17 99H (33 psi front / 32 rear) or P225/55R18 98H (35/33).'
SK_BN=('OM-published & written: spark-plug TYPE DILKAR7Q8 (NGK), battery Q85, tire size/pressure. '
  '2.5L FB25 is DIRECT-injection (12.0:1) for SK - distinct oil/cooling from SJ port-injection FB25 (platform-level boundary, matches Outback). '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 12.7 qt. '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
SK_SRC='owner-manual-verified (per 2019 Subaru Forester OM MSA5M1902B, self-ID model code A8240BE-B + Specifications chapter; SK gen-rep, FB25 DI EPA-stable 2019-24, turbo dropped)'
for vid,yr in [(12714,2019),(907,2020),(2400,2021),(3934,2022),(5462,2023),(7037,2024)]:
    W(vid,'0W-20 synthetic (2.5L FB25, direct-injection)',
      '4.4 qt / 4.2 L (2.5L FB25, direct-injection)',
      'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '9.0 qt / 8.5 L (2.5L FB25, direct-injection)',
      SK_DIFF,SK_PLUGS,'Q85','P225/60R17 99H','33 psi (base 17in)','32 psi (base 17in)',SK_TNOTE,SK_BN,SK_SRC)
    print('  Forester %d SK (FB25 DI 0W-20/4.4, plug DILKAR7Q8, batt Q85)'%yr)

db.commit()
print('\nVerify:')
for vid,lbl in [(12561,'SJ18'),(12714,'SK19'),(7037,'SK24')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | batt=%s tire=%s gap=%s | lug=%s'%(lbl,vid,o[1][:34],p[0],p[1],p[2],lug))
print('\nDEFER check (untouched):')
for vid,yr in [(8614,2025),(10234,2026),(11062,2003)]:
    s=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d (%d): %s'%(vid,yr,s[0] if s else 'no row'))
db.close(); print('DONE - 8 rows.')
