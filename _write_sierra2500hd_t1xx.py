# GMC Sierra 2500 HD T1XX-HD - 3 rows (2020/2021/2022), per-engine (gas 6.6L L8T + diesel 6.6L Duramax L5P).
# Source: 2021 Sierra 2500HD OM (84744494C, T1XX-HD gen-rep, self-ID p1) + 2020 6.6L Duramax supplement (L5P).
# 2020/2022 GM-hosted OMs not available -> 2021 rep + L5P sup w/ STABILITY NOTE (engines L8T+L5P confirmed
#   across 2020-2022; no 6.0L). NOTHING inherited from the 1500s - HD diesel read fresh.
# DEFER (stays gated, pending): 2019 K2XX-HD (id 38664) - different gen (6.0 L96 + Allison 6-spd), no GM OM.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_sierra2500hd_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE='Tire size & pressure are config-dependent (door-jamb / Certification label, not in OM body) - pending.'

VISC='5W-30 (6.6L L8T gas V8) / 15W-40 CK-4 (6.6L Duramax L5P turbo-diesel)'
OEM='dexos1 (6.6L L8T gas) / API CK-4 15W-40 (6.6L Duramax L5P diesel)'
OILCW='8.0 qt / 7.6 L (6.6L L8T gas V8) / 10.0 qt / 9.5 L (6.6L Duramax L5P diesel)'
TRANS=('Gas (6.6L L8T): 6-speed automatic, DEXRON-VI ATF. '
       'Diesel (6.6L Duramax L5P): Allison automatic, DEXRON ULV ATF (Allison TES spec). '
       'Transfer case (4WD): 2.4 qt / 2.3 L (fluid type per dealer - not specified in OM, gated).')
BRAKE='GM-approved DOT 3'
COOLANT=('DEX-COOL, 50/50 premix (coolant spec number & color not stated in OM). '
         '6.6L Duramax L5P diesel uses a much larger system + a separate low-temperature charge-air cooling circuit.')
CC=('15.4 qt / 14.6 L (6.6L L8T gas V8) / 30.7 qt / 29.1 L + 3.7 qt / 3.5 L low-temp circuit (6.6L Duramax L5P diesel)')
PS='Hydraulic power steering - GM Power Steering Fluid, 2.1 qt / 2.0 L (HD stays hydraulic - NOT EPS)'
GAP=('0.037-0.043 in / 0.95-1.10 mm (6.6L L8T gas V8, VIN 7) '
     '[6.6L Duramax L5P diesel = compression ignition: glow plugs, no spark plugs]')
BN=('Battery: maintenance-free (diesel = dual battery) - group size not in OM, GATED. '
    '6.6L Duramax L5P diesel: 15W-40 CK-4 oil, 10.0 qt; DEF (diesel exhaust fluid) tank 7.0 gal / 26.5 L; '
    'Allison transmission (DEXRON ULV / Allison TES); fuel/water separator service per diesel maintenance. '
    'Fuel tank: 36.0 gal / 136.3 L (standard; 28.0 / 40.0 gal options). '
    'Oil-filter & spark-plug (gas) / fuel-filter (diesel) part numbers per OM + 6.6L supplement (not transcribed). '
    'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), '
    'front/rear axle fluid (OM punts to dealer - HD axles), transfer-case fluid TYPE.')
SRC=('owner-manual-verified (per 2021 GMC Sierra 2500HD OM, T1XX-HD gen-rep [gas 6.6L L8T + 6.6L Duramax L5P '
     'confirmed across 2020-2022; 2020/2022 GM OMs unavailable] + 2020 6.6L Duramax Supplement, L5P diesel)')

for vid,yr in [(38665,2020),(38666,2021),(38667,2022)]:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,SRC))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,TRANS,None,BRAKE,COOLANT,CC,PS,None,SRC))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,GAP,None,None,None,None,None,None,None,None,None,None,None,TIRE,BN,None,None,None,None,SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; diesel interval per Duramax supplement',"GMC Owner's Manual (Sierra 2500HD) + 6.6L Duramax Supplement",'standard',None,None,None)); nid+=1
    print('  wrote %d (%d) T1XX-HD gas L8T + diesel L5P'%(vid,yr))

db.commit()
print('\nVerify:')
for vid in [38665,38666,38667]:
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT power_steering_fluid,coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d: %s | %s | PS=%s'%(vid,o[0][:38],o[1][:40],f[0][:34]))
d2019=c.execute('SELECT source FROM oil_change WHERE vehicle_id=38664').fetchone()
print('2019 DEFER check (id 38664): oil.source=%r (unchanged/gated)'%(d2019[0] if d2019 else 'no row'))
db.close(); print('DONE.')
