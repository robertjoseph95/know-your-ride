# GMC Yukon - T1XX (5 rows) + K2XX (1 row). Tahoe twin; values confirmed identical from the Yukon's own OMs.
# Sources: 2021 GMC Yukon OM (84266976B, T1XX rep, self-ID p1) + 2021 LM2 Duramax supplement;
#   2020 GMC Yukon OM (84367243B, K2XX, self-ID p1). DB has only "Yukon" (SWB) - no Yukon XL rows.
# Values read fresh from the Yukon OMs: T1XX cooling 5.3=15.6/6.2=15.1/diesel=21.9(SUV), oil 8.0/7.0,
#   fuel 24.0 gal (Yukon SWB); K2XX cooling 17.8, fuel 26.0 gal. Diesel = LM2 SUV variant.
# Axles + transfer-case fluid TYPE punt to dealer -> GATED. dexos D diesel oil.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_yukon_modern_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
def W(vid,visc,oilcw,oem,trans,brake,coolant,cc,gap,plugs,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,coolant,cc,PS,None,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,gap,None,None,None,None,None,None,plugs,None,None,None,None,TIRE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"GMC Owner's Manual (Yukon)",'standard',None,None,None)); nid+=1

# T1XX
T_VISC='0W-20 (5.3L V8, 6.2L V8) / 0W-20 dexos D (3.0L Duramax diesel, LM2 SUV); gas 0W-30 below -29C/-20F'
T_OEM='dexos1 full synthetic (ACDelco dexos1) - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel'
T_OILCW='8.0 qt / 7.6 L (5.3L V8, 6.2L V8) / 7.0 qt / 6.6 L (3.0L Duramax diesel)'
T_TRANS=('10-speed automatic: DEXRON ULV ATF (3.0L Duramax diesel also pairs with the 10-speed = DEXRON ULV). '
         'Transfer case (4WD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L')
T_BRAKE='GM-approved DOT 4'
T_COOLANT=('DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water (color not stated in OM). '
           '3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.')
T_CC='15.6 qt / 14.8 L (5.3L V8) / 15.1 qt / 14.3 L (6.2L V8) / 21.9 qt / 20.7 L (3.0L Duramax diesel, SUV, total incl. charge-air)'
T_GAP='0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8) [3.0L diesel = compression ignition, no spark plugs]'
T_PLUGS=json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L84) & 6.2L V8 (L87)","is_oem":True}])
T_BN=('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 12690385 (5.3L & 6.2L V8); ACDelco PF66 / GM 55495105 (3.0L Duramax diesel). '
      'Engine air filter: ACDelco A3244C / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
      '3.0L Duramax diesel (LM2 SUV variant, VIN T): 0W-20 dexos D, 7.0 qt; fuel filter GM 23304096 / ACDelco TP1015; '
      'DEF tank 5.3 gal / 20.3 L (ISO 22241); pairs with 10-speed (DEXRON ULV). Fuel tank: 24.0 gal / 90.8 L (Yukon, short wheelbase). '
      'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), '
      'transmission speed-binding, front/rear axle & transfer-case fluid TYPE (OM punts to dealer).')
T_SRC='owner-manual-verified (per 2021 GMC Yukon OM, T1XX gen-rep [5.3L+6.2L+3.0L LM2 unchanged 2021-2026 per EPA] + 2021 LM2 Duramax Supplement)'
for vid in [1811,3322,6459,8047,9683]:
    W(vid,T_VISC,T_OILCW,T_OEM,T_TRANS,T_BRAKE,T_COOLANT,T_CC,T_GAP,T_PLUGS,T_BN,T_SRC); print('  T1XX',vid)

# K2XX 2020
K_BN=('Battery: original-equipment maintenance-free - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 12690385 (5.3L & 6.2L V8). Engine air filter: ACDelco A3181C / GM 22845992. '
      'Fuel tank: 26.0 gal / 98.4 L (Yukon, short wheelbase). NOT in OM (pending/gated): battery group & CCA, drain-plug torque, '
      'oil-filter torque, tire size/pressure (placard), transmission speed-binding, front/rear axle & transfer-case fluid TYPE (OM punts to dealer).')
W(313,'0W-20 (5.3L V8, 6.2L V8); 0W-30 below -29C/-20F','8.0 qt / 7.6 L (5.3L V8, 6.2L V8)','dexos1 (ACDelco dexos1)',
  '6-speed automatic: DEXRON-VI ATF / 10-speed automatic: DEXRON ULV ATF (engine->transmission-speed binding not specified in OM - gated). Transfer case (4WD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L',
  'GM-approved DOT 3','DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water (color not stated in OM).',
  '17.8 qt / 16.8 L (5.3L V8, 6.2L V8)','0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8)',
  json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L83) & 6.2L V8 (L86)","is_oem":True}]),
  K_BN,'owner-manual-verified (per 2020 GMC Yukon OM, self-ID p1; K2XX)'); print('  K2XX 313')

db.commit()
print('\nVerify:')
for vid in [6459,313]:
    r=c.execute('SELECT v.year,o.viscosity,f.brake_fluid,f.coolant_capacity FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id JOIN fluids f ON f.vehicle_id=v.id WHERE v.id=?',(vid,)).fetchone()
    print('  %d: %s | %s | %s'%(r[0],r[1][:24],r[2],r[3][:30]))
db.close(); print('DONE.')
