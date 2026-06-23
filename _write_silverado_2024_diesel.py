# Chevrolet Silverado 1500 - 2024 (id 13016): ADD the 3.0L Duramax diesel column (LZ0 pickup).
# Un-gates the diesel that was pending in the gas pilot. Re-writes the row with gas + diesel combined.
# Sources: 2024 Silverado 1500 OM (gas 2.7/5.3/6.2, part# 85516379C) + 2024 3.0L Duramax Diesel
#   Engine Supplement (part# 85137419 B, "Chevrolet/GMC", self-ID p1; oil/visc p27, recommended
#   fluids p42, capacities p46, engine codes p47). Diesel = LZ0 (Pickup, VIN 8) for the 1500.
# CONFIRM-DON'T-ASSUME: diesel oil = 0W-20 *dexos D* (NOT dexos1 - diesel-specific spec, READ).
#   2020-2022 1500 diesel = earlier LM2 engine version -> GATED until matching-year LM2 supplement pulled.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silverado2024diesel_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

VID=13016
SRC=('owner-manual-verified (per 2024 Silverado 1500 OM gas 2.7L/5.3L/6.2L '
     '+ 2024 3.0L Duramax Diesel Supplement part# 85137419 B, LZ0 diesel)')

VISC='5W-30 (2.7L turbo) / 0W-20 (5.3L V8, 6.2L V8) / 0W-20 dexos D (3.0L Duramax diesel, LZ0); gas 0W-30 below -29C/-20F'
OEM='dexos1 full synthetic (ACDelco dexos1) - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel'
OILCW='6.0 qt / 5.7 L (2.7L turbo) / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8) / 7.0 qt / 6.6 L (3.0L Duramax diesel)'

TRANS=('8-speed automatic: DEXRON-HP ATF / 10-speed automatic: DEXRON ULV ATF '
       '(3.0L Duramax diesel pairs with the 10-speed = DEXRON ULV, confirmed in Duramax supplement; '
       'gas engine->transmission-speed binding not in OM - gated). '
       'Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L')
BRAKE='GM-approved DOT 4'
COOLANT=('DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water; service 5 yr / 150,000 mi '
         '(color not stated in OM). 3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.')
COOLCAP=('12.4 qt / 11.8 L (2.7L turbo) / 13.8 qt / 13.1 L (5.3L V8) / 13.3 qt / 12.6 L (6.2L V8) / '
         '19.4 qt / 18.4 L (3.0L Duramax diesel, pickup, total incl. charge-air)')
PS='Electric power steering (EPS) - no fluid, no regular maintenance'

PLUG_GAP=('0.026-0.030 in / 0.65-0.75 mm (2.7L turbo); '
          '0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8) [3.0L diesel = compression ignition, no spark plugs]')
PLUGS=json.dumps([
  {"brand":"ACDelco","part_number":"41-106-IP (GM 12688094)","description":"2.7L turbo (L3B)","is_oem":True},
  {"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L84) & 6.2L V8 (L87)","is_oem":True}])

BNOTE=('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
       'Oil filter: ACDelco PF66 / GM 12727115 (2.7L turbo & 3.0L Duramax diesel); ACDelco PF63 / GM 12707246 (5.3L & 6.2L V8). '
       'Engine air filter: ACDelco A3244C (high-capacity, also diesel) / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
       '3.0L Duramax diesel (LZ0, VIN 8): 0W-20 dexos D, 7.0 qt; fuel filter GM 13539108; '
       'DEF (diesel exhaust fluid) tank 5.4 gal / 20.5 L (ISO 22241); pairs with 10-speed (DEXRON ULV). '
       'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
       'tire size/pressure (door placard), per-engine transmission speed (gas). '
       '2020-2022 diesel = earlier LM2 engine version - GATED until the matching-year LM2 supplement is pulled.')
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
    c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(VID,))

c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(VID,VISC,None,OILCW,None,OEM,None,None,None,None,None,SRC))
c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
    VALUES (?,?,?,?,?,?,?,?,?)""",(VID,TRANS,None,BRAKE,COOLANT,COOLCAP,PS,None,SRC))
c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (VID,None,PLUG_GAP,None,None,None,None,None,None,PLUGS,None,None,None,None,TIRE_NOTE,BNOTE,None,None,None,None,SRC))
c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
    (VID,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual (p436)",'owner-manual-verified'))
c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
    VALUES (?,?,?,?,?,?,?,?,?,?)""",(nid,VID,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Chevrolet Owner's Manual (Silverado 1500)",'standard',None,None,None))

db.commit()
print('Updated 2024 Silverado 1500 (id %d) - diesel column added.'%VID)
o=c.execute('SELECT viscosity,capacity_with_filter,oem_spec FROM oil_change WHERE vehicle_id=?',(VID,)).fetchone()
f=c.execute('SELECT coolant_capacity FROM fluids WHERE vehicle_id=?',(VID,)).fetchone()
print('  visc:',o[0]); print('  cap :',o[1]); print('  spec:',o[2]); print('  cool:',f[0])
db.close(); print('DONE.')
