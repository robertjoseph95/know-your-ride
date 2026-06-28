# Subaru Legacy - 2 rows (BT 2020-2021). Subaru sibling #5, Outback's combined-manual mate.
# Read from the LEGACY COLUMN of the combined Legacy+Outback OM MSA5M2003A-2004A (self-ID: legacy+outback
#   both high-count = normal for combined book; A25xx code; "03" segment). 2021 = 2020 BT rep + stability
#   note (full 2021 combined OM MSA5M2103A-2104A NOT on CDN, only 140pp partial 2113A; FB25+FA24 EPA-stable 2020-21).
#  BT (7th gen, 2020-2021): FB25 2.5L DI (12.0:1, 0W-20, 4.4qt, cool 9.5, plug DILKAR7Q8) + FA24 2.4L TURBO
#      (10.6:1, 0W-20, 4.8qt, cool 9.2, plug SILKFR8A6). No 3.6 flat-6 (dropped). No WRX (separate model).
# ** LEGACY-vs-OUTBACK divergences (same book, Legacy column isolated): TIRE 225/55R17 (sedan) vs Outback
#    225/65R17 (wagon); TIRE PRESSURE 33/32 vs 35/33; CVT capacity 11.9/12.3 vs 12.4/12.6. FUEL 18.5 gal =
#    SAME (predicted-divergence read identical). FB25/FA24 oil+cool, battery LN2, plugs, lug 88.5, diff = SAME. **
# Lug 88.5 lb-ft (combined book prints 88.5, NOT the 89 of standalone Forester/Crosstrek/Impreza) - read from Legacy column.
# OM publishes -> WRITE plug/battery/tire; GATE spark gap, CVT fluid (consult dealer), drain/filter torque, oil-filter PN.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_legacy_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.4 qt/1.3 L (2.4L) / 1.3 qt/1.2 L (2.5L)","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
PLUGS=json.dumps([{"brand":"NGK","part_number":"DILKAR7Q8","description":"2.5L FB25 (direct-injection)","is_oem":True},{"brand":"NGK","part_number":"SILKFR8A6","description":"2.4L FA24 turbo","is_oem":True}])
BN=('OM-published & written (Legacy column): spark-plug type (per engine: FB25 DILKAR7Q8 / FA24 turbo SILKFR8A6), battery LN2, tire size/pressure. '
  'Fuel: 18.5 gal / 70 L (SAME as Outback - read, not assumed). '
  'CVT (Lineartronic) fluid type = consult dealer (GATED); LEGACY capacity guideline (CVT): 11.9 qt (2.5L) / 12.3 qt (2.4L turbo) '
  '[Outback differs: 12.4/12.6 - Legacy column isolated]. '
  'LEGACY-specific (sedan, vs Outback wagon): tire 225/55R17 / 225/50R18, pressure 33 front/32 rear. '
  'GATED (Subaru OM does NOT print): spark-plug GAP, drain-plug & oil-filter torque, oil-filter part #.')
def W(vid,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,'0W-20 synthetic (2.5L FB25 & 2.4L turbo FA24)',None,'4.4 qt / 4.2 L (2.5L FB25) / 4.8 qt / 4.5 L (2.4L turbo FA24)',None,'API SN / SN PLUS, ILSAC GF-5; use SUBARU approved engine oil',None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',None,BRAKE,COOLANT,'9.5 qt / 9.0 L (2.5L FB25, CVT) / 9.2 qt / 8.7 L (2.4L turbo FA24, CVT)',PS,DIFF,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,None,None,'LN2',None,'225/55R17 97V','33 psi','32 psi',PLUGS,None,None,None,None,'OM-published (Legacy, by trim): 225/55R17 97V / 225/50R18 95V; 33 psi front / 32 rear (Legacy sedan - Outback wagon differs).',BN,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',88.5,120.0,'88.5 lb-ft (120 N-m), wheel nut tightening torque per owner manual (Legacy/Outback combined book)','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Legacy/Outback)",'standard',None,None,None)); nid+=1

SRC2020='owner-manual-verified (per 2020 Subaru Legacy/Outback combined OM MSA5M2003A-2004A, LEGACY column isolated; self-ID legacy+outback both present, code A2570BE-A; BT gen, FB25+FA24)'
SRC2021='owner-manual-verified (per 2020 Subaru Legacy/Outback combined OM MSA5M2003A-2004A, LEGACY column, BT gen-rep [full 2021 OM not on CDN; FB25+FA24 EPA-confirmed unchanged 2020-21])'
W(905,SRC2020); print('  Legacy 2020 BT (FB25 4.4 + FA24 4.8, tire 225/55R17, lug 88.5)')
W(2398,SRC2021); print('  Legacy 2021 BT (2020 rep + stability note)')

db.commit()
print('\nVerify:')
for vid,lbl in [(905,'2020'),(2398,'2021')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity,brake_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT battery_group,tire_size,spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | cool=%s | batt=%s tire=%s gap=%s lug=%s'%(lbl,vid,o[1][:34],f[0][:24],p[0],p[1],p[2],lug))
db.close(); print('DONE - 2 rows.')
