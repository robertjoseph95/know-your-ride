# Owner's-manual-verified specs for Nissan Rogue T32 (2015-2020) + T33 (2021-2026).
# Per-year engine sourced from vPIC (NHTSA, gov authoritative); per-engine values from the OM.
#   T32: gas QR25DE 2.5L single (hybrid 2.0L NOT claimed). CVT NS-3. Electric PS.
#   T33 2021: DUAL (1.5T KR15DDT + 2.5L PR25DD) - transition year, vPIC shows both.
#   T33 2022-2026: 1.5T KR15DDT single. CVT NS-3. Electric PS.
# S35 (2008/2009) HELD (manuals don't self-ID). Nissan torque bonus written verified.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_rogue_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

TORQUE=[('lug_nut',83.0,113.0,"83 ft-lb (113 N-m) per owner's manual p6-8"),
        ('drain_bolt',25.0,34.0,"22-29 ft-lb (29.4-39.2 N-m) per owner's manual; use new washer"),
        ('oil_filter',13.0,17.7,"11-15 ft-lb (14.7-20.6 N-m) per owner's manual")]

DIFF_T32=json.dumps([{"type":"rear_diff_awd","fluid":"Nissan Diff Oil Hypoid Super GL-5 80W-90 (AWD)"},
                     {"type":"transfer_awd","fluid":"Nissan Diff Oil Hypoid Super GL-5 80W-90 (AWD)"}])
DIFF_T33=json.dumps([{"type":"rear_diff_awd","fluid":"Nissan Hypoid Fluid S1 GL-5 75W-80 (AWD)"},
                     {"type":"transfer_awd","fluid":"Nissan Diff Oil Hypoid Super-S GL-5 synthetic 75W-90 (AWD)"}])

# value sets
T32=dict(oil_cw='4.9 qt', oil_cwo='4.5 qt', oem='Genuine Nissan Motor Oil 0W-20 (2.5L QR25DE), API SN/SP',
         coolant='8.6 qt', diff=DIFF_T32, trans='Nissan CVT Fluid NS-3',
         tire='225/65R17 (S) / 225/60R18 (SV) / 225/55R19 (SL)', tf=33, tr=33,
         tire_note='Tire pressure 33 psi front/rear all sizes (230 kPa). Per 2020 Rogue OM.', ic='')
T33_DUAL=dict(oil_cw='5.0 qt (1.5T) / 5.4 qt (2.5L)', oil_cwo='4.9 qt (1.5T) / 5.1 qt (2.5L)',
         oem='Genuine Nissan Motor Oil 0W-20 (1.5T KR15DDT / 2.5L PR25DD), API SN',
         coolant='9.0 qt (1.5T) / 9.3 qt (2.5L)', diff=DIFF_T33, trans='Nissan CVT Fluid NS-3',
         tire='235/65R17 (S) / 235/60R18 (SV) / 235/55R19 (SL/Platinum)', tf=33, tr=30,
         tire_note='Tire pressure: 235/65R17 @ 36F/33R; 235/60R18 @ 33F/30R; 235/55R19 @ 33F/30R. Per 2023 Rogue OM p8-34.',
         ic=' 1.5T VC-Turbo has a separate intercooler coolant circuit: 3 qt (3 L).')
T33_15=dict(oil_cw='5.0 qt', oil_cwo='4.9 qt', oem='Genuine Nissan Motor Oil 0W-20 (1.5L VC-Turbo KR15DDT), API SN/SP',
         coolant='9.0 qt', diff=DIFF_T33, trans='Nissan CVT Fluid NS-3',
         tire='235/65R17 (S) / 235/60R18 (SV) / 235/55R19 (SL/Platinum)', tf=33, tr=30,
         tire_note='Tire pressure: 235/65R17 @ 36F/33R; 235/60R18 @ 33F/30R; 235/55R19 @ 33F/30R. Per 2023 Rogue OM p8-34.',
         ic=' 1.5T VC-Turbo has a separate intercooler coolant circuit: 3 qt (3 L).')

SS='owner-manual-verified'
# id, year, valueset, hybrid_flag, spec_src, maint_src
T32SRC='owner-manual-verified (per 2020 Rogue OM, T32 gen; gas 2.5L QR25DE; per-year engine vs vPIC)'
TARGETS=[
 # T32 (gas 2.5L)
 (470,  2020,T32,False,SS,"Nissan Owner's Manual (2020 Rogue, T32)"),
 (12145,2015,T32,False,T32SRC,"Nissan Owner's Manual (2020 Rogue, T32 gen)"),
 (12274,2016,T32,False,T32SRC,"Nissan Owner's Manual (2020 Rogue, T32 gen)"),
 (12408,2017,T32,True, T32SRC,"Nissan Owner's Manual (2020 Rogue, T32 gen)"),
 (12552,2018,T32,True, T32SRC,"Nissan Owner's Manual (2020 Rogue, T32 gen)"),
 (12705,2019,T32,True, T32SRC,"Nissan Owner's Manual (2020 Rogue, T32 gen)"),
 # T33 2021 DUAL
 (1968, 2021,T33_DUAL,False,'owner-manual-verified (2021 Rogue OM; DUAL 1.5T+2.5L - transition year per vPIC)',"Nissan Owner's Manual (2021 Rogue, T33)"),
 # T33 1.5T single
 (3494, 2022,T33_15,False,'owner-manual-verified (per 2023 Rogue OM, T33 gen; 1.5T per vPIC)',"Nissan Owner's Manual (2023 Rogue, T33 gen)"),
 (5027, 2023,T33_15,False,SS,"Nissan Owner's Manual (2023 Rogue, T33)"),
 (6608, 2024,T33_15,False,'owner-manual-verified (per 2023 Rogue OM, T33 gen; 1.5T per vPIC)',"Nissan Owner's Manual (2023 Rogue, T33 gen)"),
 (8177, 2025,T33_15,False,'owner-manual-verified (per 2023/2025 Rogue OM, T33; 1.5T - 2.5L dropped)',"Nissan Owner's Manual (2025 Rogue, T33)"),
 (9790, 2026,T33_15,False,'owner-manual-verified (per 2026 Rogue OM, T33; 1.5T)',"Nissan Owner's Manual (2026 Rogue, T33)"),
]

BATT=("Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual "
      "(service-manual fields) - pending. CVT fluid NS-3 type verified; capacity not in OM. "
      "Drain-plug, oil-filter, and lug torque ARE in the Nissan OM and recorded verified.{ic}{hyb}")
HYB=" NOTE: 2017-2019 Rogue also offered a low-volume Hybrid (2.0L QR20DE + motor, separate manual) - NOT covered here; these are the gas 2.5L specs."

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year,G,hyb,src,msrc in TARGETS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,'0W-20',None,G['oil_cw'],G['oil_cwo'],G['oem'],None,None,None,None,None,src))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,G['trans'],None,'Nissan DOT 3','Nissan Long Life Antifreeze/Coolant (blue, pre-diluted)',
         G['coolant'],'Electric power steering (no fluid)',G['diff'],src))
    bnote=BATT.format(ic=G['ic'], hyb=(HYB if hyb else ''))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,None,None,None,G['tire'],G['tf'],G['tr'],None,None,None,None,None,G['tire_note'],
         bnote,None,None,None,None,src))
    for comp,ft,nm,note in TORQUE:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
                  (vid,comp,ft,nm,note,'owner-manual-verified'))
    for mi,mo,desc in [
        (None,None,'Engine oil & filter change - oil control system (oil-life based); follow oil maintenance reminder'),
        (5000,None,'Tire rotation - every 5,000 mi (severe) per maintenance schedule')]:
        c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,
            source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nid,vid,mi,mo,desc,msrc,'standard',None,None,None)); nid+=1
    tag='T32 2.5L' if G is T32 else ('T33 DUAL' if G is T33_DUAL else 'T33 1.5T')
    print('  wrote %d (%s, %s)'%(vid,year,tag))

db.commit()
print('\nVerify:')
for vid,year,G,hyb,src,msrc in TARGETS:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    f=c.execute('SELECT transmission_fluid,coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d(%s): oil=%-28s cool=%-22s %s'%(vid,year,o,f[1],f[0]))
db.close(); print('\nDONE. S35 (2008/2009) untouched - stays gated.')
