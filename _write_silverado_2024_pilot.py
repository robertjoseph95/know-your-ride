# Chevrolet Silverado 1500 - 2024 GM/Chevy PILOT (gas engines only). 1 row, id 13016.
# Source: 2024 Silverado 1500 OM (part# 85516379C, self-ID p1, GM contentdelivery.ext.gm.com).
#   Pages cited are OM printed-page numbers (PDF page - 1).
#   Oil/visc/dexos p347; Capacities (coolant/oil/transfer/wheel-nut) pp.434-436; Engine Specs (spark gap) p436;
#   Recommended Fluids (ATF/brake/transfer/coolant) pp.429-430; Replacement Parts (filters/plugs) pp.430-431;
#   Brake DOT 4 p358; EPS p199.
# Gas engines: 2.7L turbo-4 (L3B), 5.3L V8 (L84), 6.2L V8 (L87).
# CONFIRM-DON'T-ASSUME READ: 2.7T uses 5W-30 (V8s 0W-20 - thinner oil is the V8, counterintuitive);
#   coolant color NOT stated in OM (DEX-COOL conventionally orange, but not written -> omit);
#   EPS confirmed (no PS fluid); torque is lug-only (no drain/filter torque in OM).
# GATED: 3.0L Duramax diesel (entirely in separate Duramax supplement - queued as discrete pull);
#   battery group (OM punts to label); per-engine transmission speed binding (OM gives ATF by speed,
#   not engine->speed - confirm from GM source or leave gated); drain/oil-filter torque; tire (placard).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silverado2024_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

VID=13016; YEAR=2024
SRC='owner-manual-verified (per 2024 Silverado 1500 OM; gas 2.7L/5.3L/6.2L; 3.0L Duramax diesel gated to separate supplement)'

VISC='5W-30 (2.7L turbo) / 0W-20 (5.3L V8, 6.2L V8); 0W-30 below -29C/-20F'
OEM='dexos1 full synthetic (ACDelco dexos1)'   # OM states "dexos1" - no Gen qualifier, recorded as-is
OILCW='6.0 qt / 5.7 L (2.7L turbo) / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'

# OM gives ATF per transmission speed (both verified); engine->speed binding NOT in OM -> gated
TRANS=('8-speed automatic: DEXRON-HP ATF / 10-speed automatic: DEXRON ULV ATF '
       '(engine->transmission-speed binding not specified in OM - gated). '
       'Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L')
BRAKE='GM-approved DOT 4'
COOLANT='DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water; service 5 yr / 150,000 mi (color not stated in OM)'
COOLCAP='12.4 qt / 11.8 L (2.7L turbo) / 13.8 qt / 13.1 L (5.3L V8) / 13.3 qt / 12.6 L (6.2L V8)'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
# Front/rear axle fluid = OM says "See your dealer" -> not authoritative, gated (None)

PLUG_GAP=('0.026-0.030 in / 0.65-0.75 mm (2.7L turbo); '
          '0.037-0.043 in / 0.95-1.10 mm (5.3L V8, 6.2L V8)')
PLUGS=json.dumps([
  {"brand":"ACDelco","part_number":"41-106-IP (GM 12688094)","description":"2.7L turbo (L3B)","is_oem":True},
  {"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"5.3L V8 (L84) & 6.2L V8 (L87)","is_oem":True}])

BNOTE=('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
       'Oil filter: ACDelco PF66 / GM 12727115 (2.7L turbo); ACDelco PF63 / GM 12707246 (5.3L & 6.2L V8). '
       'Engine air filter: ACDelco A3244C (high-capacity) / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
       'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
       'tire size/pressure (door placard), per-engine transmission speed. '
       '3.0L Duramax diesel: oil/coolant/ATF/capacities/parts in a SEPARATE Duramax supplement - GATED (not fabricated from gas OM).')
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1

# purge fabricated ai-haiku across the 6 gated spec tables
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
print('Wrote 2024 Silverado 1500 (id %d) gas pilot.'%VID)
o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(VID,)).fetchone()
f=c.execute('SELECT brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(VID,)).fetchone()
p=c.execute('SELECT spark_plug_gap,battery_group FROM parts WHERE vehicle_id=?',(VID,)).fetchone()
tq=c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?',(VID,)).fetchone()
print('  oil visc:',o[0])
print('  oil cap :',o[1])
print('  brake   :',f[0],'| PS:',f[1])
print('  gap     :',p[0])
print('  battery :',p[1] or 'GATED')
print('  lug     :',tq[0],'lb-ft')
db.close(); print('DONE.')
