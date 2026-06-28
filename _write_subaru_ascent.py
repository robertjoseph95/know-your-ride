# Subaru Ascent - 4 rows (2020/21/22 pre-refresh + 2026 post-refresh). Subaru sibling #6, 3-row SUV.
# Standalone manual, FA24-ONLY (all years). Self-ID: model code A32xx (UNIQUE block, no platform-twin),
#   filename segment "00" (MSA5M YY00 A). 2021 OM MSA5M2100A (A3220BE-A), 2026 OM MSA5M2600A (A3270BE-A).
# Read FA24 FRESH from Ascent's own column - the heaviest Subaru body.
#  pre-refresh (2020-2022): FA24 2.4T DI (0W-20, 4.8qt, cool 11.7, plug SILKFR8A6), battery 75D23L,
#      fuel 19.3gal, tire 245/60R18 105H. Per 2021 OM.
#  2026 (post-refresh): same FA24/cool/oil/fuel/tire/lug; ONLY change = battery 75D23L -> LN2. Per 2026 OM.
# ** BODY-vs-ENGINE split (the slice's thesis): FA24 engine-bound fields HOLD across bodies (0W-20, 4.8qt oil,
#    plug SILKFR8A6, lug 89) but COOLING DIVERGES 9.2qt(Outback) -> 11.7qt(Ascent) - biggest same-engine
#    cross-body divergence in the campaign. Fuel 19.3 vs 18.5; tire 245/60R18 vs 225/65R17. **
# ** FA24 STAYS 0W-20 (did NOT follow FB20/FB25 to 0W-16) -> 0W-16 is an FB-new-gen fact, not Subaru-wide. **
# OM publishes -> WRITE plug/battery/tire; GATE spark gap, CVT fluid (consult dealer), drain/filter torque, oil-filter PN.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_ascent_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.3 qt/1.2 L","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
PLUGS=json.dumps([{"brand":"NGK","part_number":"SILKFR8A6","description":"2.4L FA24 turbo (direct-injection)","is_oem":True}])
TNOTE='OM-published (by trim): 245/60R18 105H (18in, 35/35 psi) / 245/50R20 102H (20in, 33/33 psi).'
def W(vid,batt,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,'0W-20 synthetic (2.4L FA24 turbo)',None,'4.8 qt / 4.5 L (2.4L FA24 turbo)',None,'API SN / SN PLUS / SP, ILSAC GF-5 / GF-6A; use SUBARU approved engine oil',None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',None,BRAKE,COOLANT,'11.7 qt / 11.1 L (2.4L FA24 turbo, CVT)',PS,DIFF,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,'SILKFR8A6 (NGK)',None,None,batt,None,'245/60R18 105H','35 psi','35 psi',PLUGS,None,None,None,None,TNOTE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',89.0,120.0,'89 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Ascent)",'standard',None,None,None)); nid+=1

BN_PRE=('OM-published & written: spark-plug type SILKFR8A6 (NGK), battery 75D23L, tire size/pressure. Fuel: 19.3 gal / 73 L (3-row SUV). '
  '** FA24 cooling 11.7 qt - LARGER than the same engine in the Outback (9.2 qt): body-dependent divergence. FA24 oil stays 0W-20 (not 0W-16). ** '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 12.3 qt (no air-cooled CVT cooler) / 12.7 qt (with cooler). '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
BN_26=('OM-published & written: spark-plug type SILKFR8A6 (NGK), battery LN2, tire size/pressure. Fuel: 19.3 gal / 73 L. '
  '** 2026 (post-2023-refresh): ONLY change vs 2020-22 = battery 75D23L -> LN2; cooling 11.7, oil 0W-20/4.8, fuel, tire, lug all held. ** '
  'FA24 cooling 11.7 qt (vs Outback FA24 9.2 - body divergence). FA24 oil stays 0W-20 (not 0W-16). '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); capacity guideline (CVT): 12.7 qt. '
  'GATED: spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
SRC_PRE='owner-manual-verified (per 2021 Subaru Ascent OM MSA5M2100A, self-ID model code A3220BE-A + filename "00", standalone; FA24-only, pre-refresh rep for 2020-22)'
SRC_26='owner-manual-verified (per 2026 Subaru Ascent OM MSA5M2600A, self-ID A3270BE-A + filename "00", standalone; FA24-only, post-2023-refresh)'
for vid,yr in [(912,2020),(2405,2021),(3939,2022)]:
    W(vid,'75D23L',BN_PRE,SRC_PRE); print('  Ascent %d pre-refresh (FA24 0W-20/4.8, cool 11.7, batt 75D23L, tire 245/60R18)'%yr)
W(10239,'LN2',BN_26,SRC_26); print('  Ascent 2026 post-refresh (battery -> LN2; rest held)')

db.commit()
print('\nVerify:')
for vid,lbl in [(912,'2020 pre'),(10239,'2026')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()[0]
    p=c.execute('SELECT battery_group,tire_size,spark_plug_type,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | cool=%s | batt=%s tire=%s plug=%s gap=%s lug=%s'%(lbl,vid,o[1][:26],f[:24],p[0],p[1],p[2],p[3],lug))
db.close(); print('DONE - 4 rows.')
