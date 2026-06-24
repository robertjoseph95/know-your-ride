# Cadillac Escalade T1XX modern slice - 5 rows: Escalade 2021/2022/2024 + Escalade ESV 2021/2022.
# Source: 2021 Cadillac Escalade OM (84266974B, T1XX gen-rep, self-ID p1) + 2021 LM2 Duramax 3.0L supplement.
#   Engines (EPA): 6.2L V8 (L87) + 3.0L Duramax diesel (LM2 *SUV* variant) - unchanged 2021-2024.
# SUV-specific values READ from the Escalade's OWN OM (NOT carried back from the pickups):
#   cooling 15.1qt (gas) vs pickup 13.3; diesel cooling 21.9qt (SUV) from supplement vs pickup 20.5;
#   fuel tank 24.0 gal (Escalade short WB) / 28.0 gal (ESV long WB); axles + transfer-case fluid TYPE
#   punted to dealer in the Escalade OM (truck OM gave DEXRON-VI - do NOT carry back) -> gated.
# Common GM (confirmed on Escalade OM): 0W-20 dexos1, DEX-COOL GMW3420 (no color), DOT 4, EPS, lug 140,
#   DEXRON ULV 10-speed; diesel 0W-20 dexos D 7.0qt, DEF 5.3 gal, fuel filter LM2.
# Escalade V (SC 6.2) GATED (halo, own spec). 2001 phantom row purged (no 2001 Escalade existed).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_escalade_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1

# --- purge 2001 phantom row's fabricated specs (id 14243) ---
for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
    c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(14243,))
print('Purged 2001 phantom Escalade (id 14243) fabricated specs -> clean-gated.')

VISC='0W-20 (6.2L V8) / 0W-20 dexos D (3.0L Duramax diesel, LM2); gas 0W-30 below -29C/-20F'
OEM='dexos1 full synthetic (ACDelco dexos1) - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel'
OILCW='8.0 qt / 7.6 L (6.2L V8) / 7.0 qt / 6.6 L (3.0L Duramax diesel)'
TRANS=('10-speed automatic: DEXRON ULV ATF (3.0L Duramax diesel also pairs with the 10-speed = DEXRON ULV). '
       'Transfer case (4WD): fluid type per dealer (not specified in OM), 1.6 qt / 1.5 L')
BRAKE='GM-approved DOT 4'
COOLANT=('DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water (color not stated in OM). '
         '3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.')
CC='15.1 qt / 14.3 L (6.2L V8) / 21.9 qt / 20.7 L (3.0L Duramax diesel, SUV, total incl. charge-air)'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
GAP='0.037-0.043 in / 0.95-1.10 mm (6.2L V8) [3.0L diesel = compression ignition, no spark plugs]'
PLUGS=json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"6.2L V8 (L87)","is_oem":True}])
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

def bnote(fuel):
    return ('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 12690385 (6.2L V8); ACDelco PF66 / GM 55495105 (3.0L Duramax diesel). '
      'Engine air filter: ACDelco A3244C (high-cap) / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
      '3.0L Duramax diesel (LM2 SUV variant, VIN T): 0W-20 dexos D, 7.0 qt; fuel filter GM 23304096 / ACDelco TP1015; '
      'DEF tank 5.3 gal / 20.3 L (ISO 22241); pairs with 10-speed (DEXRON ULV). '
      'Fuel tank: %s. '
      'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
      'tire size/pressure (placard), transmission speed-binding, front/rear axle & transfer-case fluid TYPE '
      '(Escalade OM punts to dealer - NOT carried back from the pickup OM). Escalade V (supercharged 6.2) halo - separate spec, GATED.'%fuel)

# (id, year, model, fuel_tank_text, source)
ESC_SRC='owner-manual-verified (per 2021 Cadillac Escalade OM, T1XX gen-rep [6.2L V8 + 3.0L LM2 diesel unchanged 2021-2024 per EPA] + 2021 LM2 Duramax Supplement)'
ROWS=[
 (1789,2021,'Escalade','24.0 gal / 90.8 L (Escalade, short wheelbase)'),
 (3299,2022,'Escalade','24.0 gal / 90.8 L (Escalade, short wheelbase)'),
 (6434,2024,'Escalade','24.0 gal / 90.8 L (Escalade, short wheelbase)'),
 (1791,2021,'Escalade ESV','28.0 gal / 106.0 L (Escalade ESV, long wheelbase)'),
 (3301,2022,'Escalade ESV','28.0 gal / 106.0 L (Escalade ESV, long wheelbase)'),
]
for vid,yr,model,fuel in ROWS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,ESC_SRC))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,TRANS,None,BRAKE,COOLANT,CC,PS,None,ESC_SRC))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,GAP,None,None,None,None,None,None,PLUGS,None,None,None,None,TIRE_NOTE,bnote(fuel),None,None,None,None,ESC_SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Cadillac Owner's Manual (Escalade)",'standard',None,None,None)); nid+=1
    print('  wrote %d %s %d'%(vid,model,yr))

db.commit()
print('\nVerify:')
for vid,yr,model,fuel in ROWS:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity,brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s %d: %s | cool=%s | %s'%(model,yr,o[0][:30],f[0][:38],f[1]))
ph=c.execute('SELECT COUNT(*) FROM oil_change WHERE vehicle_id=14243').fetchone()[0]
print('2001 phantom oil_change rows remaining (should be 0):',ph)
db.close(); print('DONE.')
