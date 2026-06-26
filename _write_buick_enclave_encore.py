# Buick Enclave (8 gas) + Encore (Gen-1) - 8 rows. GM crossover profile (EPS/DOT4/dexos1/DEXRON-VI).
# Each engine read FRESH from its own Buick OM - nothing inherited from truck/SUV/HD.
# Enclave: 2020/21/22/24 = 3.6L V6 LFY (per 2024 BUI Enclave OM 85158970B, gen-stable LFY 2020-24 per EPA);
#          2025/26 = 2.5L turbo-4 LK0 (per 2026 BUI Enclave OM 19344861A - 2025 redesign, NOT gen-stable).
# Encore: 2020/21 = 1.4L turbo LE2 (per 2022 BUI Encore OM 84857911B, gen-stable LE2 2020-22 per EPA).
# Encore lug = 100 lb-ft (140 N-m) READ from Encore OM - NOT the Enclave 140 (smaller wheels).
# DEFER: Encore 2026 (id 9648) phantom (EPA empty, no US 2026 base Encore); Encore GX = separate VSS-F slice.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_buick_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
def W(vid,visc,oilcw,oem,trans,brake,coolant,cc,diff,gap,bn,src,lug_lb,lug_nm):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,coolant,cc,PS,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,gap,None,None,None,None,None,None,None,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',float(lug_lb),float(lug_nm),'%d lb-ft (%d N-m), Wheel Nut Torque per owner manual'%(lug_lb,lug_nm),'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Buick Owner's Manual",'standard',None,None,None)); nid+=1

# ===== Enclave 3.6 V6 (LFY) 2020/21/22/24 =====
E36_BN=('Battery: maintenance-free - group not in OM, GATED. Oil filter: ACDelco PF63 / GM 12707246 (3.6L V6). '
  'Fuel tank: 19.4 gal / 73.4 L (FWD) / 21.7 gal / 82.1 L (AWD). '
  'NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire size/pressure (placard), '
  'spark-plug part #, rear axle fluid (AWD - OM punts to dealer).')
for vid,yr in [(285,2020),(1784,2021),(3294,2022),(6428,2024)]:
    W(vid,'5W-30 (3.6L V6); 0W-30 below -29C/-20F','6.0 qt / 5.7 L (3.6L V6)','dexos1 (ACDelco dexos1)',
      '9-speed automatic: DEXRON-VI ATF. Rear axle (AWD): fluid per dealer (not specified in OM, gated).',
      'GM-approved DOT 4','DEX-COOL (50/50 premix; spec number & color not stated in OM).',
      '15.4 qt / 14.6 L (FWD) / 15.5 qt / 14.7 L (AWD)',None,
      '0.037-0.043 in / 0.95-1.10 mm (3.6L V6, LFY)',E36_BN,
      'owner-manual-verified (per 2024 Buick Enclave OM, 3.6L V6 gen-rep [LFY unchanged 2020-2024 per EPA]; Gen-2 C1XX)',140,190)
    print('  Enclave %d 3.6 V6'%yr)

# ===== Enclave 2.5T (LK0) 2025/26 =====
E25_BN=('Battery: AGM maintenance-free - group not in OM, GATED. Oil filter: ACDelco (2.5L LK0) - part # per OM, GATED (not transcribed). '
  'Fuel tank: 19.4 gal / 73.0 L (FWD) / 21.7 gal / 82.0 L (AWD). '
  'NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire size/pressure (placard), '
  'spark-plug & oil-filter part #, rear axle fluid (AWD - OM punts to dealer).')
for vid,yr in [(8013,2025),(9647,2026)]:
    W(vid,'0W-20 (2.5L turbo-4); 0W-30 below -29C/-20F','5.5 qt / 5.2 L (2.5L turbo-4)','dexos1 (ACDelco dexos1)',
      '8-speed automatic: DEXRON-VI ATF. Rear axle (AWD): fluid per dealer (not specified in OM, gated).',
      'GM-approved DOT 4','DEX-COOL (50/50 premix; spec number & color not stated in OM).',
      '17.9 qt / 16.9 L (2.5L turbo-4)',None,
      '0.026-0.030 in / 0.65-0.75 mm (2.5L turbo-4, LK0)',E25_BN,
      'owner-manual-verified (per 2026 Buick Enclave OM, 2.5L turbo-4 LK0; 2025 redesign - distinct engine era from the 3.6 V6)',140,190)
    print('  Enclave %d 2.5T'%yr)

# ===== Encore 1.4T (LE2) Gen-1 2020/21 =====
EN_BN=('Battery: maintenance-free - group not in OM, GATED. Oil filter: ACDelco PF64 / GM 12706595 (1.4L turbo). '
  'Fuel tank: 14.0 gal / 53 L. Transfer case (AWD): 0.36 qt / 0.35 L. '
  'NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire size/pressure (placard), spark-plug part #.')
for vid,yr in [(286,2020),(1785,2021)]:
    W(vid,'0W-20 (1.4L turbo-4); 0W-30 below -29C/-20F','4.2 qt / 4.0 L (1.4L turbo-4)','dexos1 (ACDelco dexos1)',
      '6-speed automatic: DEXRON-VI ATF. Transfer case (AWD): 0.36 qt / 0.35 L.',
      'GM-approved DOT 4','DEX-COOL (50/50 premix; spec number & color not stated in OM).',
      '7.7 qt / 7.3 L (1.4L turbo-4)',None,
      '0.024-0.028 in / 0.60-0.70 mm (1.4L turbo-4, LE2)',EN_BN,
      'owner-manual-verified (per 2022 Buick Encore OM, 1.4L turbo LE2 gen-rep [unchanged 2020-2022 per EPA]; Gen-1 Gamma II)',100,140)
    print('  Encore %d 1.4T (lug 100 lb-ft - Encore-specific)'%yr)

db.commit()
print('\\nDEFER: Encore 2026 (id 9648):', c.execute('SELECT source FROM oil_change WHERE vehicle_id=9648').fetchone())
print('Verify:')
for vid in [6428,8013,286]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d: %s | %s | lug=%s'%(vid,o[0][:24],o[1][:30],tq))
db.close(); print('DONE.')
