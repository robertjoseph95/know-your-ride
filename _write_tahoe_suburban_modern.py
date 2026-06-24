# Chevy Tahoe + Suburban - T1XX (10 rows) + K2XX (2 rows). Gas twins of the Escalade.
# Sources: 2021 Tahoe/Suburban OM (84266975B, T1XX rep, self-ID p1) + 2021 LM2 Duramax supplement;
#   2020 Tahoe/Suburban OM (84367240B, K2XX, self-ID p1). Combined OM covers both models.
# SUV-specific values READ FRESH from the Tahoe/Suburban OM (NOT carried from Escalade or pickups):
#   T1XX cooling 5.3=15.6 / 6.2=15.1 / diesel=21.9 (SUV); K2XX cooling 17.8. Oil 8.0 gas / 7.0 diesel.
#   Fuel PER MODEL: Tahoe (SWB) 24.0 (T1XX) / 26.0 (K2XX); Suburban (LWB) 28.0 (T1XX) / 31.5 (K2XX).
# Diesel = LM2 SUV variant (all T1XX years; SUVs never got the pickups' LZ0). Axles + transfer-case
#   fluid TYPE punted to dealer in the OM -> GATED (do NOT carry pickup DEXRON-VI). dexos D diesel oil.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_tahoesub_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

def W(vid,visc,oilcw,oem,trans,brake,coolant,cc,ps,gap,plugs,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,trans,None,brake,coolant,cc,ps,None,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,gap,None,None,None,None,None,None,plugs,None,None,None,None,TIRE_NOTE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Chevrolet Owner's Manual (Tahoe/Suburban)",'standard',None,None,None)); nid+=1

# ===== T1XX (2021-2026): 5.3 L84 + 6.2 L87 + 3.0 LM2 diesel =====
T_VISC='0W-20 (5.3L V8, 6.2L V8) / 0W-20 dexos D (3.0L Duramax diesel, LM2 SUV); gas 0W-30 below -29C/-20F'
T_OEM='dexos1 full synthetic (ACDelco dexos1) - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel'
T_OILCW='8.0 qt / 7.6 L (5.3L V8, 6.2L V8) / 7.0 qt / 6.6 L (3.0L Duramax diesel)'
T_TRANS=('10-speed automatic: DEXRON ULV ATF (3.0L Duramax diesel also pairs with the 10-speed = DEXRON ULV). '
         'Transfer case (4WD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L')
T_BRAKE='GM-approved DOT 4'
T_COOLANT=('DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water (color not stated in OM). '
           '3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.')
T_CC='15.6 qt / 14.8 L (5.3L V8) / 15.1 qt / 14.3 L (6.2L V8) / 21.9 qt / 20.7 L (3.0L Duramax diesel, SUV, total incl. charge-air)'
T_PS='Electric power steering (EPS) - no fluid, no regular maintenance'
T_GAP='0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8) [3.0L diesel = compression ignition, no spark plugs]'
T_PLUGS=json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L84) & 6.2L V8 (L87)","is_oem":True}])
def t_bn(fuel):
    return ('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 12690385 (5.3L & 6.2L V8); ACDelco PF66 / GM 55495105 (3.0L Duramax diesel). '
      'Engine air filter: ACDelco A3244C (high-cap) / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
      '3.0L Duramax diesel (LM2 SUV variant, VIN T): 0W-20 dexos D, 7.0 qt; fuel filter GM 23304096 / ACDelco TP1015; '
      'DEF tank 5.3 gal / 20.3 L (ISO 22241); pairs with 10-speed (DEXRON ULV). Fuel tank: %s. '
      'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), '
      'transmission speed-binding, front/rear axle & transfer-case fluid TYPE (OM punts to dealer - NOT carried back from pickup OM).'%fuel)
T_SRC='owner-manual-verified (per 2021 Chevrolet Tahoe/Suburban OM, T1XX gen-rep [5.3L+6.2L+3.0L LM2 unchanged 2021-2026 per EPA] + 2021 LM2 Duramax Supplement)'
TAHOE_FUEL='24.0 gal / 90.8 L (Tahoe, short wheelbase)'
SUB_FUEL='28.0 gal / 106.0 L (Suburban, long wheelbase)'
T1XX=[(1759,'Tahoe',TAHOE_FUEL),(3264,'Tahoe',TAHOE_FUEL),(6396,'Tahoe',TAHOE_FUEL),(7982,'Tahoe',TAHOE_FUEL),(9616,'Tahoe',TAHOE_FUEL),
      (1758,'Suburban',SUB_FUEL),(3263,'Suburban',SUB_FUEL),(6395,'Suburban',SUB_FUEL),(7981,'Suburban',SUB_FUEL),(9615,'Suburban',SUB_FUEL)]
for vid,mdl,fuel in T1XX:
    W(vid,T_VISC,T_OILCW,T_OEM,T_TRANS,T_BRAKE,T_COOLANT,T_CC,T_PS,T_GAP,T_PLUGS,t_bn(fuel),T_SRC)
    print('  T1XX %d %s'%(vid,mdl))

# ===== K2XX (2020): 5.3 L83 + 6.2 L86 =====
K_VISC='0W-20 (5.3L V8, 6.2L V8); 0W-30 below -29C/-20F'
K_OEM='dexos1 (ACDelco dexos1)'
K_OILCW='8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'
K_TRANS=('6-speed automatic: DEXRON-VI ATF / 10-speed automatic: DEXRON ULV ATF '
         '(engine->transmission-speed binding not specified in OM - gated). '
         'Transfer case (4WD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L')
K_BRAKE='GM-approved DOT 3'
K_COOLANT='DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water (color not stated in OM).'
K_CC='17.8 qt / 16.8 L (5.3L V8, 6.2L V8)'
K_GAP='0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8)'
K_PLUGS=json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L83) & 6.2L V8 (L86)","is_oem":True}])
def k_bn(fuel):
    return ('Battery: original-equipment maintenance-free - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 12690385 (5.3L & 6.2L V8). Engine air filter: ACDelco A3181C / GM 22845992. '
      'Fuel tank: %s. NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
      'tire size/pressure (placard), transmission speed-binding, front/rear axle & transfer-case fluid TYPE (OM punts to dealer).'%fuel)
K_SRC='owner-manual-verified (per 2020 Chevrolet Tahoe/Suburban OM, self-ID p1; K2XX)'
K_PS=T_PS  # EPS, same as T1XX
for vid,mdl,fuel in [(260,'Tahoe','26.0 gal / 98.4 L (Tahoe, short wheelbase)'),(259,'Suburban','31.5 gal / 119.2 L (Suburban, long wheelbase)')]:
    W(vid,K_VISC,K_OILCW,K_OEM,K_TRANS,K_BRAKE,K_COOLANT,K_CC,K_PS,K_GAP,K_PLUGS,k_bn(fuel),K_SRC)
    print('  K2XX %d %s'%(vid,mdl))

db.commit()
print('\nVerify:')
for vid in [1759,1758,6396,6395,260,259]:
    r=c.execute('SELECT v.year,v.model,o.viscosity,f.coolant_capacity,f.brake_fluid FROM vehicles v JOIN oil_change o ON o.vehicle_id=v.id JOIN fluids f ON f.vehicle_id=v.id WHERE v.id=?',(vid,)).fetchone()
    fuel=c.execute('SELECT battery_notes FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    import re; fm=re.search(r'Fuel tank: ([^.]*)',fuel)
    print('  %d %s: %s | cool=%s | %s | %s'%(r[0],r[1],r[2][:18],r[3][:30],r[4],fm.group(1)[:30] if fm else '?'))
db.close(); print('DONE.')
