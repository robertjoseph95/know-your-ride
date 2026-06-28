# Subaru WRX - 4 modern rows (VA 2020/21 FA20-DIT + VB 2022/2026 FA24-DIT). Separate performance model.
# Self-ID: VA 2021 = combined WRX/STI book (code A1760, filename "05") - isolated the base-WRX "Except STI"
#   column (FA20-DIT 2.0T, EPS); STI (EJ257 2.5T, hydraulic PS) EXCLUDED (no DB row). VB 2022 (A9020) / 2026
#   (A9100) = WRX-only (STI discontinued). Each turbo read fresh from the WRX's own column - nothing carried.
#  VA FA20-DIT (2020-21): 5W-30 (NOT 0W-20!), 5.4qt oil, cool MT 8.6/CVT 8.8, plug ILKAR8H6, fuel 15.9gal,
#      tire 235/45R17. Per 2021 WRX/STI OM MSA5M2105A.
#  VB FA24-DIT (2022): 0W-20, 4.8qt, cool MT 9.0/CVT 9.2, plug SILKFR8D6Y, fuel 16.6gal, tire 235/45R17. Per 2022 OM MSA5M2205A.
#  VB FA24-DIT (2026): 0W-20, 4.8qt, cool MT 9.0/CVT 9.2, plug SILKFR8A6, fuel 16.6gal, tire 245/40R18. Per 2026 OM MSA5M2605A.
# ** FA24-DIT cross-check vs mainstream FA24 (0W-20/4.8/9.2/SILKFR8A6): oil + cooling HOLD; PLUG MOVES -
#    VB 2022 = SILKFR8D6Y (vs mainstream SILKFR8A6), 2026 reverted to SILKFR8A6 (per-year plug drift). Read each. **
# ** FA20-DIT = own engine: 5W-30/5.4qt (NOT the mainstream NA 0W-20). **
# TRANSMISSION not CVT-universal: 6MT (gear oil GL-5 75W-90, 3.5qt - WRITTEN) + CVT (consult dealer - GATED), both eras incl 2026.
# Common: lug 89 lb-ft (120 N-m); battery 75D23L; EPS (base WRX; STI hydraulic excluded); brake FMVSS No.116 DOT 3/4; SUBARU Super Coolant.
# OM publishes -> WRITE plug/battery/tire/MT-gear-oil; GATE spark gap (Subaru), CVT fluid, drain/filter torque, oil-filter PN.
# DEFER: 2003-2008 old EJ (EJ205/EJ255, EPA-empty "Impreza WRX" era) -> old-doc discovery. STI excluded (no DB row).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_wrx_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance (base WRX; STI was hydraulic)'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
def W(vid,visc,oilcw,cc,plug,plugs,tire,tnote,fdiff,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,visc,None,oilcw,None,'API SN / SN PLUS / SP, ILSAC GF-5 / GF-6A; use SUBARU approved engine oil',None,None,None,None,None,src))
    trans=('6-speed manual (6MT): GL-5 75W-90 gear oil, 3.5 qt / 3.3 L. CVT (Subaru Performance Transmission, where equipped): Subaru CVT Fluid - consult dealer (type GATED). '
           'Front differential (CVT models): %s. Rear differential: 0.8 qt / 0.8 L, GL-5 75W-90.'%fdiff)
    diffj=json.dumps({"manual_transmission":"GL-5 75W-90: 3.5 qt/3.3 L","front_differential_cvt":fdiff,"rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,trans,None,BRAKE,COOLANT,cc,PS,diffj,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,plug,None,None,'75D23L',None,tire,'33 psi','32 psi',plugs,None,None,None,None,tnote,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',89.0,120.0,'89 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal; turbo)',"Subaru Owner's Manual (WRX)",'standard',None,None,None)); nid+=1

# VA FA20-DIT 2020/2021
VA_BN=('OM-published & written: spark-plug type ILKAR8H6 (NGK), battery 75D23L, tire size/pressure, 6MT gear oil. Fuel: 15.9 gal / 60 L. '
  '** FA20-DIT (2.0L turbo) is its OWN engine: 5W-30 / 5.4 qt (NOT the mainstream NA 0W-20). ** Read from base-WRX column of combined WRX/STI book (STI EJ257 excluded). '
  'Transmission: 6MT gear oil written; CVT fluid = consult dealer (GATED). GATED: spark-plug GAP (Subaru OM does NOT print), drain/oil-filter torque, oil-filter part #.')
for vid,yr in [(909,2020),(2402,2021)]:
    W(vid,'5W-30 synthetic (2.0L FA20-DIT turbo); 5W-40 acceptable alternative','5.4 qt / 5.1 L (2.0L FA20-DIT turbo)',
      '8.6 qt / 8.1 L (2.0L FA20-DIT, MT) / 8.8 qt / 8.3 L (CVT)','ILKAR8H6 (NGK)',
      json.dumps([{"brand":"NGK","part_number":"ILKAR8H6","description":"2.0L FA20-DIT turbo","is_oem":True}]),
      '235/45R17 94W','OM-published (base WRX, by trim): 235/45R17 94W (17in) / 245/40R18 97W (18in); 33/32 psi.',
      'GL-5 75W-90: 1.5 qt/1.4 L',VA_BN,
      'owner-manual-verified (per 2021 Subaru WRX/STI combined OM MSA5M2105A, self-ID code A1760BE-A + filename "05"; base-WRX "Except STI" column, FA20-DIT; VA gen-rep 2020-21)')
    print('  WRX %d VA FA20-DIT (5W-30/5.4, plug ILKAR8H6)'%yr)

# VB FA24-DIT 2022 (plug SILKFR8D6Y)
W(3936,'0W-20 synthetic (2.4L FA24-DIT turbo); 5W-30 acceptable alternative','4.8 qt / 4.5 L (2.4L FA24-DIT turbo)',
  '9.0 qt / 8.5 L (2.4L FA24-DIT, MT) / 9.2 qt / 8.7 L (CVT)','SILKFR8D6Y (NGK)',
  json.dumps([{"brand":"NGK","part_number":"SILKFR8D6Y","description":"2.4L FA24-DIT turbo (VB)","is_oem":True}]),
  '235/45R17 97W','OM-published (by trim): 235/45R17 97W (17in) / 245/40R18 97Y (18in); 33/32 psi.',
  'GL-5 75W-90: 1.3 qt/1.2 L',
  ('OM-published & written: spark-plug type SILKFR8D6Y (NGK), battery 75D23L, tire, 6MT gear oil. Fuel: 16.6 gal / 63 L. '
   '** FA24-DIT cross-check vs mainstream FA24 (0W-20/4.8/9.2/SILKFR8A6): oil + cooling HOLD; PLUG MOVES to SILKFR8D6Y (performance tune). ** '
   'Transmission: 6MT gear oil written; CVT = consult dealer (GATED). GATED: spark-plug GAP, drain/oil-filter torque, oil-filter part #.'),
  'owner-manual-verified (per 2022 Subaru WRX OM MSA5M2205A, self-ID code A9020BE-A + filename "05"; VB FA24-DIT)')
print('  WRX 2022 VB FA24-DIT (0W-20/4.8, plug SILKFR8D6Y)')

# VB FA24-DIT 2026 (plug SILKFR8A6 - reverted)
W(10236,'0W-20 synthetic (2.4L FA24-DIT turbo); 5W-30 acceptable alternative','4.8 qt / 4.5 L (2.4L FA24-DIT turbo)',
  '9.0 qt / 8.5 L (2.4L FA24-DIT, MT) / 9.2 qt / 8.7 L (CVT)','SILKFR8A6 (NGK)',
  json.dumps([{"brand":"NGK","part_number":"SILKFR8A6","description":"2.4L FA24-DIT turbo (VB 2026)","is_oem":True}]),
  '245/40R18 97Y','OM-published (by trim): 245/40R18 97Y (18in) / 245/35R19 93Y (19in); 33/32 psi (18in 17in dropped).',
  'GL-5 75W-90: 1.3 qt/1.2 L',
  ('OM-published & written: spark-plug type SILKFR8A6 (NGK), battery 75D23L, tire, 6MT gear oil. Fuel: 16.6 gal / 63 L. '
   '** 2026 plug = SILKFR8A6 (reverted from 2022 SILKFR8D6Y - per-year plug drift within VB; now matches mainstream FA24). Oil/cooling unchanged. 2026 still offers 6MT (not CVT-only). ** '
   'Transmission: 6MT gear oil written; CVT = consult dealer (GATED). GATED: spark-plug GAP, drain/oil-filter torque, oil-filter part #.'),
  'owner-manual-verified (per 2026 Subaru WRX OM MSA5M2605A, self-ID code A9100BE-A + filename "05"; VB FA24-DIT, 2026)')
print('  WRX 2026 VB FA24-DIT (0W-20/4.8, plug SILKFR8A6 reverted)')

db.commit()
print('\nVerify:')
for vid,lbl in [(909,'20 VA'),(3936,'22 VB'),(10236,'26 VB')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT spark_plug_type,battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | %s | plug=%s tire=%s gap=%s lug=%s'%(lbl,vid,o[0][:24],o[1][:22],p[0],p[2],p[3],lug))
print('\nDEFER check (untouched):')
for vid in [11066,11412]:
    s=c.execute('SELECT v.year,o.source FROM vehicles v LEFT JOIN oil_change o ON o.vehicle_id=v.id WHERE v.id=?',(vid,)).fetchone()
    print('  id %d (%s): %s'%(vid,s[0],s[1]))
db.close(); print('DONE - 4 rows.')
