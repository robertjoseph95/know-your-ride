# Subaru Outback MODERN - 11 rows (BS 2016-19 + BT 2020-26). FIRST non-GM make.
# Each engine read FRESH from its own Subaru OM spec page (image-rendered tables). Nothing inherited from GM.
#  BS gen (2016-2019): 2.5 FB25 (port-inj, 10.3:1, 0W-20, 5.1qt, cool 8.2) + 3.6 EZ36 flat-6 (5W-30, 6.9qt, cool 7.4).
#      Per 2018 Outback OM (MSA5M1803A, self-ID A2540BE-A Outback; engines EPA-stable 2016-19).
#  BT gen (2020-2026): 2.4T FA24 turbo (0W-20, 4.8qt, cool 9.2) + 2.5 FB25 (DIRECT-inj, 12.0:1, 0W-20, 4.4qt, cool 9.5).
#      Per 2020 Outback OM (MSA5M2003A-2004A, self-ID A2570BE-A; engines EPA-stable 2020-26; 2.5 rode whole gen).
# ** FB25 DIVERGES across the 2020 redesign (port->direct inj): oil 5.1->4.4qt, cooling 8.2->9.5qt. Read each era. **
# Common (read, not assumed): SUBARU Super Coolant; rear diff 0.8qt GL-5 75W-90; brake FMVSS No.116 DOT 3 or DOT 4;
#   lug 88.5 lb-ft (120 N-m, the Subaru passenger value - NOT GM 140); fuel 18.5 gal; EPS (electric, no PS fluid).
# CVT (Lineartronic): fluid = "consult dealer" -> GATED (capacity guideline only, Outback-isolated from Legacy).
# GATED (Subaru OM does NOT publish, unlike GM): spark-plug gap; drain/oil-filter torque; oil-filter PN;
#   battery group; tire (placard). Combined Legacy+Outback manual - Outback values isolated.
# DEFER (gated 2nd pass): BH/BP 2000-2009 (old doc-number discovery + per-doc self-ID needed).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_outback_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
OEM='API SN / SN PLUS, ILSAC GF-5 (starburst); use SUBARU approved engine oil'
BRAKE='FMVSS No. 116, DOT 3 or DOT 4 brake fluid (OM lists both as acceptable)'
COOLANT='SUBARU Super Coolant (Subaru Long Life Coolant; 50/50 premix)'
def W(vid,visc,oilcw,trans,cc,diff,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,OEM,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,BRAKE,COOLANT,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,None,None,None,None,None,None,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',88.5,120.0,'88.5 lb-ft (120 N-m), wheel nut tightening torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Subaru maintenance schedule (severe/normal)',"Subaru Owner's Manual (Legacy/Outback)",'standard',None,None,None)); nid+=1

# ===== BS gen (2016-2019): 2.5 FB25 + 3.6 EZ36 flat-6 =====
BS_DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.3 qt/1.2 L (2.5L) / 1.5 qt/1.4 L (3.6L)","rear_differential":"GL-5 75W-90: 0.8 qt/0.8 L"})
BS_BN=('Fuel tank: 18.5 gal / 70 L. CVT (Lineartronic) fluid type = consult SUBARU dealer (GATED); capacity guideline (Outback): 12.4 qt (2.5L) / 13.4 qt (3.6L). '
  'GATED (Subaru OM does NOT publish): spark-plug gap, drain-plug & oil-filter torque, oil-filter part #, battery group/CCA, tire size/pressure (placard).')
BS_SRC='owner-manual-verified (per 2018 Subaru Outback OM MSA5M1803A, self-ID model code A2540BE-A "Outback"; BS gen-rep, 2.5 FB25 + 3.6 EZ36 EPA-stable 2016-19)'
for vid,yr in [(12286,2016),(12420,2017),(12564,2018),(12717,2019)]:
    W(vid,'0W-20 synthetic (2.5L FB25); 5W-30 (3.6L EZ36 flat-6)',
      '5.1 qt / 4.8 L (2.5L FB25) / 6.9 qt / 6.5 L (3.6L EZ36 flat-6)',
      'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '8.2 qt / 7.8 L (2.5L FB25) / 7.4 qt / 7.0 L (3.6L EZ36 flat-6)',
      BS_DIFF,BS_BN,BS_SRC)
    print('  Outback %d BS (2.5 FB25 0W-20 + 3.6 EZ36 5W-30)'%yr)

# ===== BT gen (2020-2026): 2.4T FA24 + 2.5 FB25 (direct-injection) =====
BT_DIFF=json.dumps({"front_differential":"GL-5 75W-90: 1.3 qt/1.2 L","rear_differential":"GL-5 75W-90 (Outback: 75W-90 or 90): 0.8 qt/0.8 L"})
BT_BN=('Fuel tank: 18.5 gal / 70 L. CVT (Lineartronic) fluid type = consult SUBARU dealer (GATED); capacity guideline (Outback): 12.4 qt (2.5L) / 12.6 qt (2.4L turbo). '
  '2.5L FB25 is DIRECT-injection (12.0:1) for BT - distinct oil/cooling from the BS port-injection FB25. '
  'GATED (Subaru OM does NOT publish): spark-plug gap, drain-plug & oil-filter torque, oil-filter part #, battery group/CCA, tire size/pressure (placard).')
BT_SRC='owner-manual-verified (per 2020 Subaru Outback OM MSA5M2003A-2004A, self-ID model code A2570BE-A "Outback"; BT gen-rep, 2.4T FA24 + 2.5 FB25 EPA-stable 2020-26)'
for vid,yr in [(12800,2020),(12868,2021),(12933,2022),(12999,2023),(13065,2024),(13131,2025),(13193,2026)]:
    W(vid,'0W-20 synthetic (2.5L FB25 & 2.4L turbo FA24)',
      '4.4 qt / 4.2 L (2.5L FB25) / 4.8 qt / 4.5 L (2.4L turbo FA24)',
      'CVT (Lineartronic): Subaru CVT Fluid - consult dealer (type not user-serviceable, GATED).',
      '9.5 qt / 9.0 L (2.5L FB25) / 9.2 qt / 8.7 L (2.4L turbo FA24)',
      BT_DIFF,BT_BN,BT_SRC)
    print('  Outback %d BT (2.4T FA24 + 2.5 FB25 direct-inj, both 0W-20)'%yr)

db.commit()
print('\nVerify:')
for vid,lbl in [(12564,'BS18'),(12717,'BS19'),(12800,'BT20'),(13193,'BT26')]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT brake_fluid,power_steering_fluid,coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %s(%d): %s | %s | lug=%s | cool=%s'%(lbl,vid,o[0][:30],f[1][:9],lug,f[2][:20]))
db.close(); print('DONE - 11 rows.')
