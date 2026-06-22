# Lincoln Aviator 2nd gen (2020-2026) - 7 rows.
# Source: 2023 Aviator OM (self-ID p1, Capacities pp.467-487; lug p467; PS p414; tire p270)
#   + 2020 Lincoln Aviator Technical Specifications (media.lincoln.com) for the 10-speed SelectShift designation.
# EPA roster: 2020-2023 = gas 3.0TT V6 + PHEV (Grand Touring plug-in); 2024-2026 = gas 3.0TT only (PHEV dropped 2024).
# Twin of Explorer (CD6) was HYPOTHESIS - every field READ from Aviator's own OM. Confirmed shared: MERCON ULV
#   (NOT F-150 LV), Yellow coolant, EPAS, lug 150. Diverged (luxury, read): battery 94R (NOT Explorer's 48); PHEV
#   is plug-in (Explorer=FHEV) with dual-circuit coolant. PHEV fully covered by OM -> written, not gated.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_aviator_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

MSRC="Lincoln Owner's Manual (2023 Aviator, 2nd gen) + 2020 Aviator Technical Specifications"
SRC_2W='owner-manual-verified (per 2023 Lincoln Aviator OM, 2nd gen; gas 3.0TT V6 + PHEV; 10-spd per Lincoln tech-specs)'
SRC_1W='owner-manual-verified (per 2023 Lincoln Aviator OM, 2nd gen; gas 3.0TT V6 - PHEV dropped 2024; 10-spd per Lincoln tech-specs)'

VISC='5W-30 (3.0L twin-turbo V6; gas & PHEV)'
OILCW='6.0 qt (with filter)'
OEM='Motorcraft 5W-30 (WSS-M2C961-A1)'
COOLANT_TYPE='Motorcraft Yellow Prediluted Antifreeze/Coolant (WSS-M97B57-A2)'
BRAKE='Motorcraft DOT 4 LV (WSS-M6C65-A2)'
PS='Electric power steering (EPAS, no fluid)'
DIFF=json.dumps({"transfer_case":"Motorcraft MERCON LV 1.1 qt (AWD, WSS-M2C938-A)",
                 "front_axle":"0.6 qt (AWD)","rear_axle":"SAE 75W-85 (WSS-M2C942-A), 1.9 qt"})
SPARK=json.dumps([{"brand":"Motorcraft","part_number":"SP-594","description":"3.0L twin-turbo V6 (gas & PHEV)","is_oem":True}])

# 2-way (2020-2023): gas + PHEV
COOL_2W='18.0 qt (gas 3.0TT) / PHEV dual-circuit: 19.3 qt engine loop + 5.1 qt battery/motor-electronics loop'
TRANS_2W='Motorcraft MERCON ULV ATF - 10-speed automatic (10R60); PHEV = 10-speed modular-hybrid'
TCAP_2W='12.6 qt (gas) / 13.7 qt (PHEV) - dry fill'
BNOTE_2W=('Battery group 94R (Motorcraft BAGM-94RH7-800); PHEV adds rear auxiliary battery (BHAGM-AUX1-A), per OM. '
    'Oil filter FL-2062-A; air FA-1884; cabin FP-103 (both powertrains). PHEV fuel tank 18.0 gal vs gas 20.2 gal. '
    'NOT in OM (pending): spark-plug GAP, drain-plug torque, oil-filter torque, tire size/pressure (driver-door Tire Label).')
# 1-way (2024-2026): gas only
COOL_1W='18.0 qt (gas 3.0TT V6)'
TRANS_1W='Motorcraft MERCON ULV ATF - 10-speed automatic (10R60)'
TCAP_1W='12.6 qt - dry fill'
BNOTE_1W=('Battery group 94R (Motorcraft BAGM-94RH7-800), per OM. Oil filter FL-2062-A; air FA-1884; cabin FP-103. '
    'NOT in OM (pending): spark-plug GAP, drain-plug torque, oil-filter torque, tire size/pressure (driver-door Tire Label).')
TIRE_NOTE='Tire size & pressure are config-dependent (driver-door Tire Label/placard, not in OM body) - pending.'

# (id, year, two_way)
ROWS=[(233,2020,True),(1733,2021,True),(3238,2022,True),(4780,2023,True),
      (6369,2024,False),(7954,2025,False),(9588,2026,False)]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for vid,year,tw in ROWS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    SRC=SRC_2W if tw else SRC_1W
    COOL=COOL_2W if tw else COOL_1W; TRANS=TRANS_2W if tw else TRANS_1W
    TCAP=TCAP_2W if tw else TCAP_1W; BNOTE=BNOTE_2W if tw else BNOTE_1W
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(vid,VISC,None,OILCW,None,OEM,None,None,None,None,None,SRC))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",(vid,TRANS,TCAP,BRAKE,COOLANT_TYPE,COOL,PS,DIFF,SRC))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,'94R',None,None,None,None,SPARK,None,None,None,None,TIRE_NOTE,BNOTE,None,None,None,None,SRC))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',150.0,204.0,"150 lb-ft (204 N-m), M14x1.5, per owner's manual p467",'owner-manual-verified'))
    c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",(nid,vid,None,None,'Engine oil & filter change - Intelligent Oil-Life Monitor; follow message center',MSRC,'standard',None,None,None)); nid+=1
    print('  wrote %d (%s) %s'%(vid,year,'gas+PHEV' if tw else 'gas only'))

db.commit()
print('\nVerify:')
for vid,year,tw in ROWS:
    f=c.execute('SELECT transmission_fluid,coolant_capacity,transmission_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    p=c.execute('SELECT battery_group FROM parts WHERE vehicle_id=?',(vid,)).fetchone()[0]
    phev='PHEV' if 'PHEV' in f[1] else 'gas-only'
    print('  %d(%s): %s | batt=%s | %s'%(vid,year,phev,p,f[0][:45]))
db.close(); print('\nDONE.')
