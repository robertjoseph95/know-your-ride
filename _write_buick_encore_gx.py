# Buick Encore GX - 5 rows (2022-2026). Parked-and-approved write (verified in prior session).
# Separate VSS-F platform (NOT Encore Gen-1 Gamma II) - 3-cyl turbos, nothing from the 1.4L LE2.
# Per-engine (read fresh from the GX's own OMs):
#   1.2L 3-cyl turbo (RPO LIH 2022-23 -> LBP 2024-26): 0W-20 dexos1, 4.2qt oil, 6.7qt cool, gap 0.024-0.028, CVT.
#   1.3L 3-cyl turbo (L3T throughout): 0W-20 dexos1, 4.8qt oil, 7.8qt cool, gap 0.025-0.030, CVT(FWD)/9-spd DEXRON-VI(AWD).
# Common: DOT 4; EPS; lug 100 lb-ft (140 N-m, smaller wheels - NOT the full-size GM 140 lb-ft); fuel 13.2 gal;
#   transfer case (AWD) 0.24 qt; oil filter ACDelco PF64 (GM 12706595).
# ** 2024 refresh changed 1.2L RPO LIH->LBP but NO service spec moved (oil/cool/gap/visc/lug/fuel/transfer
#    byte-identical pre/post, confirmed by reading BOTH 2022 + 2025 OMs). Rep basis sound; cite each era. **
# GATED (do NOT fabricate): battery group/CCA, drain/oil-filter torque, tire (placard), spark-plug PNs,
#   exact GM CVT-fluid product (OM says see dealer), rear axle (AWD punts to dealer).
# 4th GM profile = subcompact/VSS-F (closes the GM group).
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_encoregx_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
VISC='0W-20 (1.2L & 1.3L 3-cyl turbo)'
OEM='dexos1 (ACDelco dexos1)'
OILCW='4.2 qt / 4.0 L (1.2L turbo) / 4.8 qt / 4.5 L (1.3L turbo)'
TRANS=('CVT (1.2L; 1.3L FWD): GM High-Performance CVT Fluid (product per dealer - gated). '
       '9-speed automatic (1.3L AWD): DEXRON-VI ATF. Transfer case (AWD): 0.24 qt / 0.23 L.')
BRAKE='GM-approved DOT 4'
COOLANT='DEX-COOL, 50/50 premix (coolant spec number & color not stated in OM).'
CC='6.7 qt / 6.3 L (1.2L turbo) / 7.8 qt / 7.4 L (1.3L turbo)'
GAP='0.024-0.028 in / 0.60-0.70 mm (1.2L turbo) / 0.025-0.030 in / 0.65-0.75 mm (1.3L turbo)'
def W(vid,src,bn):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,TRANS,None,BRAKE,COOLANT,CC,PS,None,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,GAP,None,None,None,None,None,None,None,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',100.0,140.0,'100 lb-ft (140 N-m), Wheel Nut Torque per owner manual','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Buick Owner's Manual (Encore GX)",'standard',None,None,None)); nid+=1

BN_COMMON=('Oil filter: ACDelco PF64 / GM 12706595. Fuel tank: 13.2 gal / 50 L. Transfer case (AWD): 0.24 qt / 0.23 L. '
  'NOT in OM (pending/gated): battery group/CCA, drain-plug/oil-filter torque, tire size/pressure (placard), '
  'spark-plug part #, exact GM High-Performance CVT-Fluid product (OM says see dealer), rear axle fluid (AWD - OM punts to dealer).')
# pre-refresh 2022/2023 (1.2L LIH)
for vid,yr in [(3297,2022),(4839,2023)]:
    W(vid,'owner-manual-verified (per 2022 Buick Encore GX OM 84783953B; 1.2L turbo LIH + 1.3L turbo L3T, VSS-F; pre-refresh)',
      '1.2L turbo = RPO LIH (pre-2024-refresh). '+BN_COMMON)
    print('  Encore GX %d pre-refresh (1.2L LIH + 1.3L L3T)'%yr)
# post-refresh 2024/2025/2026 (1.2L LBP)
for vid,yr in [(6431,2024),(8016,2025),(9650,2026)]:
    W(vid,'owner-manual-verified (per 2025 Buick Encore GX OM 85602505C; 1.2L turbo LBP + 1.3L turbo L3T, VSS-F; post-2024-refresh, specs byte-identical to pre-refresh per cross-read)',
      '1.2L turbo = RPO LBP (2024 refresh; service specs byte-identical to the LIH pre-refresh). '+BN_COMMON)
    print('  Encore GX %d post-refresh (1.2L LBP + 1.3L L3T)'%yr)

db.commit()
print('\nVerify:')
for vid in [3297,6431,9650]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT spark_plug_gap FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    lug=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d: %s | %s | brake=%s PS=%s | gap=%s | lug=%s'%(vid,o[0][:20],o[1][:34],f[0],f[1][:9],p[:22],lug))
db.close(); print('DONE - 5 rows.')
