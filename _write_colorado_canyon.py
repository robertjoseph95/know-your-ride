# Chevy Colorado (8) + GMC Canyon (6) = 14 rows. GM midsize, FRESH engine family.
# 3 generations, each read from its OWN OM (self-ID confirmed); nothing inherited.
#  1st gen (2004/05/06): 2.8L I4 (LK5) + 3.5L I5 (L52) - 5W-30 GM6094M, HYDRAULIC PS, DOT 3.
#      Per 2005 Colorado OM (legible 416pp, gen-rep; engines LK5/L52 stable 2004-06 per EPA).
#  2nd gen (Colo 2020/21; Canyon 2020/21/22): 2.5L I4 (LCV, 0W-20) + 3.6L V6 (LGZ truck, 5W-30)
#      + 2.8L Duramax diesel (LWN, dexos2 0W-40). EPS, DOT 3. Per 2020 Colorado + 2020 Canyon OM
#      (twin-confirmed) + 2021 2.8L Duramax supplement.
#  3rd gen (2024/25/26 both): single 2.7L turbo I4 (L3B, 5W-30). EPS, DOT 4 (2023 redesign boundary).
#      Per 2025 Colorado + 2024 Canyon OM (twin-confirmed; 2.7T gen-stable 2023-26 per EPA).
# Three Duramax oils now distinct: 3.0 LM2/LZ0=dexos D | 2.8 LWN=dexos2 0W-40 | 6.6 L5P=15W-40 CK-4.
# GATED: 2005 lug torque (OM defers to spec page, not cleanly legible - NOT assumed 140, midsize may
#   diverge per Encore-100 lesson -> NO lug row written for 1st-gen); 2.8 LWN oil cap (multi-model sup);
#   oil-filter PNs, battery, tire (placard); 4WD axle fluid (2nd/3rd punt to dealer; 1st-gen GIVEN);
#   ZR2 trim axle/locker/tire (trim-specific). No phantoms (no 2013/14 rows), no defers - all legible.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_colocanyon_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'
def W(vid,visc,oilcw,oem,trans,brake,coolant,cc,ps,diff,gap,bn,src,lug=True):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,coolant,cc,ps,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,gap,None,None,None,None,None,None,None,None,None,None,None,TIRE,bn,None,None,None,None,src))
    if lug:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',140.0,190.0,'140 lb-ft (190 N-m), Wheel Nut Torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when DIC indicates (at least once a year)',"Owner's Manual (Colorado/Canyon)",'standard',None,None,None)); nid+=1

PS_HYD='Hydraulic power steering - GM Power Steering Fluid (1st-gen midsize stays hydraulic - NOT EPS)'
PS_EPS='Electric power steering (EPS) - no fluid, no regular maintenance'

# ===== 1st gen (2.8L I4 LK5 + 3.5L I5 L52) - 2004/2005/2006 =====
DIFF_1G=json.dumps({"front_axle_4wd":"SAE 80W-90, 3.2 pints / 1.5 L (GIVEN in 2005 OM)","rear_axle":"SAE 75W-90 synthetic, 3.4-3.8 pints / 1.6-1.8 L (GIVEN in 2005 OM)"})
BN_1G=('Fuel tank: 19.5 gal / 76 L. Axle fluids GIVEN in OM: front (4WD) 80W-90 (1.5 L), rear 75W-90 synthetic (1.6-1.8 L). '
  'LUG TORQUE GATED: 2005 OM defers to a spec page that did not extract cleanly - NOT assumed 140 (midsize/older may diverge, per Encore-100 lesson). '
  'NOT in OM (pending/gated): lug torque, battery group/CCA, oil-filter & spark-plug part #s, drain-plug/oil-filter torque, tire size/pressure (placard).')
SRC_1G='owner-manual-verified (per 2005 Chevrolet Colorado OM, self-ID p1, legible 416pp; 1st-gen gen-rep, 2.8L LK5 + 3.5L L52 stable 2004-06 per EPA)'
for vid,yr in [(11079,2004),(11131,2005),(11198,2006)]:
    W(vid,'5W-30 (2.8L I4 & 3.5L I5); per 2005 OM (GM6094M + starburst certification mark)',
      '5.0 qt / 4.7 L (2.8L I4) / 6.0 qt / 5.6 L (3.5L I5)','GM6094M (API Certified for Gasoline Engines; starburst symbol)',
      '4-speed automatic (4L60-E): DEXRON-III ATF; 5-speed manual where equipped. Transfer case (4WD): Auto Transfer Case Fluid II.',
      'GM-approved DOT 3','DEX-COOL, 50/50 premix (coolant spec number & color not stated in OM).',
      '10.4 qt / 9.8 L (2.8L I4) / 10.6 qt / 10.0 L (3.5L I5)',PS_HYD,DIFF_1G,
      '0.042 in / 1.07 mm (2.8L I4 & 3.5L I5)',BN_1G,SRC_1G,lug=False)
    print('  Colorado %d 1st-gen (2.8 I4 + 3.5 I5) HYD/DOT3, lug GATED'%yr)

# ===== 2nd gen (2.5 LCV + 3.6 LGZ + 2.8 LWN diesel) =====
VISC_2G='0W-20 (2.5L I4, LCV) / 5W-30 (3.6L V6, LGZ truck) / dexos2 0W-40 (2.8L Duramax diesel, LWN)'
OILCW_2G='5.0 qt / 4.7 L (2.5L I4) / 6.0 qt / 5.7 L (3.6L V6) / 2.8L Duramax diesel: capacity per supplement (GATED - multi-model sup, not cleanly read)'
OEM_2G='dexos1 (2.5L I4 & 3.6L V6 gas) / dexos2, 0W-40 (2.8L Duramax LWN diesel)'
TRANS_2G='8-speed automatic (2.5L & 3.6L gas): DEXRON-VI ATF. 6-speed automatic (2.8L diesel): DEXRON-VI ATF. Transfer case (4WD): 2.0 qt / 1.9 L (Auto Transfer Case Fluid).'
CC_2G='9.6 qt / 9.1 L (2.5L I4) / 11.2 qt / 10.6 L (3.6L V6) / 11.1 qt / 10.5 L (2.8L Duramax diesel)'
GAP_2G='0.037-0.043 in / 0.95-1.10 mm (2.5L I4) / 0.031-0.035 in / 0.80-0.90 mm (3.6L V6) [2.8L Duramax diesel = glow plugs, no spark gap]'
DIFF_2G=json.dumps({"front_rear_axle_4wd":"Fluid type per dealer (not specified in OM - GATED)"})
BN_2G=('Fuel tank: 21.1 gal / 79.9 L. 2.8L Duramax diesel (LWN): dexos2 0W-40, DEF tank 5.5 gal / 21.0 L, oil capacity per 2.8L supplement (GATED - multi-model). '
  'ZR2 trim: axle/locker/tire specs differ - GATED, not fabricated. '
  'NOT in OM (pending/gated): battery group/CCA, oil-filter PNs, drain-plug/oil-filter torque, tire (placard), 4WD front/rear axle fluid TYPE, 2.8L diesel oil capacity.')
for vid,yr,mk,om in [(264,2020,'Colorado','2020 Chevrolet Colorado'),(1763,2021,'Colorado','2020 Colorado rep'),
                     (314,2020,'Canyon','2020 GMC Canyon'),(1812,2021,'Canyon','2020 Canyon rep'),(3323,2022,'Canyon','2020 Canyon rep')]:
    W(vid,VISC_2G,OILCW_2G,OEM_2G,TRANS_2G,'GM-approved DOT 3',
      'DEX-COOL, 50/50 premix (spec number & color not stated in OM). 2.8L diesel uses a larger cooling system.',
      CC_2G,PS_EPS,DIFF_2G,GAP_2G,BN_2G,
      'owner-manual-verified (per %s OM + 2021 2.8L Duramax Supplement; 2nd-gen, engines 2.5L LCV + 3.6L LGZ + 2.8L LWN confirmed 2020-22 per EPA; twin-confirmed Colorado<->Canyon)'%om)
    print('  %s %d 2nd-gen (2.5/3.6/2.8diesel) EPS/DOT3'%(mk,yr))

# ===== 3rd gen (2.7T L3B) - 2024/25/26 both =====
BN_3G=('Fuel tank: 21.5 gal / 81.4 L. ZR2 trim: axle/locker/tire specs differ - GATED, not fabricated. '
  'NOT in OM (pending/gated): battery group/CCA, oil-filter PNs, drain-plug/oil-filter torque, tire (placard), 4WD front/rear axle fluid TYPE.')
for vid,yr,mk,om in [(6400,2024,'Colorado','2025 Colorado rep'),(7987,2025,'Colorado','2025 Chevrolet Colorado'),(9621,2026,'Colorado','2025 Colorado rep'),
                     (6460,2024,'Canyon','2024 GMC Canyon'),(8048,2025,'Canyon','2024 Canyon rep'),(9684,2026,'Canyon','2024 Canyon rep')]:
    W(vid,'5W-30 (2.7L turbo I4, L3B); 0W-30 below -29C/-20F','6.0 qt / 5.7 L (2.7L turbo I4)','dexos1 (ACDelco dexos1)',
      '8-speed automatic: DEXRON-VI ATF. Transfer case (4WD): 1.6 qt / 1.5 L.',
      'GM-approved DOT 4','DEX-COOL, 50/50 premix (spec number & color not stated in OM).',
      '11.6 qt / 11.0 L (2.7L turbo I4)',PS_EPS,DIFF_2G,
      '0.026-0.030 in / 0.65-0.75 mm (2.7L turbo I4, L3B)',BN_3G,
      'owner-manual-verified (per %s OM; 3rd-gen 2.7L L3B single engine, gen-stable 2023-26 per EPA; twin-confirmed Colorado<->Canyon; 2023 redesign engine-era boundary)'%om)
    print('  %s %d 3rd-gen (2.7T) EPS/DOT4'%(mk,yr))

db.commit()
print('\nVerify:')
for vid,lbl in [(11131,'Colo05 1st'),(264,'Colo20 2nd'),(7987,'Colo25 3rd'),(314,'Cany20 2nd'),(6460,'Cany24 3rd')]:
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s (%d): %s | %s | PS=%s | lug=%s'%(lbl,vid,o[0][:30],f[0],f[1][:9],lug[0] if lug else 'GATED(none)'))
db.close(); print('DONE - 14 rows.')
