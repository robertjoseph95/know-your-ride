# Owner's-manual-verified specs for Nissan Pathfinder R52 (2019/2020) + R53 (2022/2025/2026).
# CRITICAL per-generation divergence:
#   R52 = CVT (NS-3) + HYDRAULIC PS (E-PSF)
#   R53 = 9-speed auto (Matic-R ATF) + ELECTRIC PS (no fluid)
# Do NOT carry NS-3/hydraulic across to R53. Both gens single V6 (VQ35DD). Nissan torque bonus written.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_pathfinder_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

TORQUE_R52=[('lug_nut',83.0,113.0,"83 ft-lb (113 N-m) per owner's manual p6-8"),
            ('drain_bolt',25.0,34.0,"22-29 ft-lb (29.4-39.2 N-m) per owner's manual p8-10; use new washer"),
            ('oil_filter',13.0,18.0,"11-15 ft-lb (15.0-21.0 N-m) per owner's manual p8-10")]
TORQUE_R53=TORQUE_R52  # same torque figures both gens

R52_DIFF=json.dumps([
    {"type":"rear_diff_awd","fluid":"Nissan Diff Oil Hypoid Super Semi-synthetic GL-5 75W-90 (AWD/4WD)"},
    {"type":"transfer_case_awd","fluid":"Nissan Diff Oil Hypoid Super GL-5 80W-90 (4WD)"}])
R53_DIFF=json.dumps([
    {"type":"rear_diff_awd","fluid":"Nissan Diff Oil Hypoid Super Semi-synthetic GL-5 75W-90 (AWD/4WD)"},
    {"type":"transfer_case_awd","fluid":"Nissan Diff Oil Hypoid Super-S GL-5 synthetic 75W-90 (4WD)"},
    {"type":"awd_coupling","fluid":"LSC Transmission Fluid 12-301 (AWD coupling)"}])

# R52 (CVT, hydraulic)
R52=dict(oil_cw='5.1 qt', oil_cwo='4.8 qt', oem='Genuine Nissan Motor Oil 0W-20 (3.5L V6 VQ35DD), API SN/SP',
         coolant_cap='10.4 qt', trans='Nissan CVT Fluid NS-3', ps='Nissan E-PSF (hydraulic)',
         tire='235/65R18 (S/SV) / 235/55R20 (SL) / 255/60R18 (Platinum)', tf=33, tr=33,
         tire_note=("Tire pressure by size: 235/65R18 @ 33 psi; 235/55R20 @ 35 psi; 255/60R18 @ 36 psi. "
                    "Per 2020 Pathfinder OM p8-31."), diff=R52_DIFF, torque=TORQUE_R52,
         tow_note="Towing: OM gives a GCWR-based Towing Load/Specification chart (no single published max-tow value).")
# R53 (9-speed auto, electric)
R53=dict(oil_cw='5.1 qt', oil_cwo='4.8 qt', oem='Genuine Nissan Motor Oil 0W-20 (3.5L V6 VQ35DD), API SP',
         coolant_cap='12.3 qt (12.6 qt w/ tow package)', trans='Nissan Matic-R ATF (9-speed automatic)',
         ps='Electric power steering (no fluid)',
         tire='255/60R18 (S/SV) / 255/50R20 (SL/Platinum)', tf=33, tr=33,
         tire_note=("Tire pressure by size: 255/60R18 @ 33 psi; 255/50R20 @ 35 psi. Per 2022 Pathfinder OM p8-33."),
         diff=R53_DIFF, torque=TORQUE_R53,
         tow_note="Towing: OM gives a GCWR-based Towing Load/Specification chart (no single published max-tow value); coolant capacity is larger with the tow package.")

BATT_NOTE_BASE=("Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual "
                "(service-manual fields) - pending. Transmission-fluid type verified ({trans_type}); capacity not in OM. "
                "Drain-plug, oil-filter, and lug torque ARE in the Nissan OM and are recorded verified. {tow}")

# id, year, gen-config, spec_src, maint_src
SS='owner-manual-verified'
TARGETS=[
 (469,  2020,R52, SS, "Nissan Owner's Manual (2020 Pathfinder, R52)"),
 (38632,2019,R52,'owner-manual-verified (per 2020 Pathfinder OM, R52 gen; engine config confirmed vs each year OM)',"Nissan Owner's Manual (2020 Pathfinder, R52 gen)"),
 (3493, 2022,R53, SS, "Nissan Owner's Manual (2022 Pathfinder, R53)"),
 (8176, 2025,R53,'owner-manual-verified (per 2022 Pathfinder OM, R53 gen; confirmed vs each year OM)',"Nissan Owner's Manual (2022 Pathfinder, R53 gen)"),
 (9789, 2026,R53,'owner-manual-verified (per 2026 Pathfinder OM, R53)',"Nissan Owner's Manual (2026 Pathfinder, R53)"),
]

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for vid,year,G,src,msrc in TARGETS:
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    trans_type = 'CVT NS-3' if G is R52 else 'Matic-R ATF (9-speed)'
    batt_note=BATT_NOTE_BASE.format(trans_type=trans_type, tow=G['tow_note'])
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,'0W-20',None,G['oil_cw'],G['oil_cwo'],G['oem'],None,None,None,None,None,src))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,G['trans'],None,'Nissan DOT 3','Nissan Long Life Antifreeze/Coolant (blue, pre-diluted)',
         G['coolant_cap'],G['ps'],G['diff'],src))
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,6,None,None,G['tire'],G['tf'],G['tr'],None,None,None,None,None,G['tire_note'],
         batt_note,None,None,None,None,src))
    for comp,ft,nm,note in G['torque']:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
                  (vid,comp,ft,nm,note,'owner-manual-verified'))
    for mi,mo,desc in [
        (None,None,'Engine oil & filter change - oil control system (oil-life based); follow oil maintenance reminder'),
        (5000,None,'Tire rotation - every 5,000 mi (severe) per maintenance schedule')]:
        c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,
            source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nid,vid,mi,mo,desc,msrc,'standard',None,None,None)); nid+=1
    print('  wrote %d (%s %s)'%(vid,year,'R52 CVT/hydraulic' if G is R52 else 'R53 Matic-R/electric'))

db.commit()
print('\nVerify (per-gen split):')
for vid,year,G,src,msrc in TARGETS:
    f=c.execute('SELECT transmission_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT COUNT(*) FROM torque_specs WHERE vehicle_id=?',(vid,)).fetchone()[0]
    print('  %d(%s): trans=%-35s PS=%-32s torque_rows=%s'%(vid,year,f[0],f[1],tq))
db.close(); print('\nDONE.')
