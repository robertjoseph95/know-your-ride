# Owner's-manual-verified specs for Nissan Sentra B17 (2015/2018/2019) + B18 (2020/2021/2026).
# Sources: 2019 Sentra OM (B17 rep) + 2020 Sentra OM (B18 rep); per-year engine config verified
# vs each year's own manual (2015=1.8L only; 2018/2019=1.8L+1.6T; 2020-2026=2.0L only; 2026 vs 2026 OM).
# Nissan torque bonus: drain/lug/oil-filter torque written verified. Service-manual fields NULL/gated.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_sentra_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

COMMON=dict(trans='Nissan CVT Fluid NS-3', coolant_type='Nissan Long Life Antifreeze/Coolant (blue, pre-diluted)',
            ps='Electric power steering (no fluid)')

# per-vehicle config: id, year, gen, spec_src, maint_src, oil dict, coolant_cap, tire, brake, torque set
B17_DRAIN=('drain_bolt',25.0,34.0,"25 ft-lb (34 N-m) per owner's manual p8-9; use new washer")
B17_FILT =('oil_filter',13.0,18.0,"13 ft-lb (18 N-m) per owner's manual p8-11")
B18_DRAIN=('drain_bolt',25.0,34.0,"22-29 ft-lb (29.4-39.2 N-m) per owner's manual p8-10; use new washer")
B18_FILT =('oil_filter',13.0,17.7,"11-15 ft-lb (14.7-20.6 N-m) per owner's manual p8-10")
LUG=('lug_nut',83.0,113.0,"83 ft-lb (113 N-m) per owner's manual p6-8")

B17_TIRE='205/55R16 (S) / 205/50R17 (SV/SR/SL) / 215/45R18 (NISMO/SR Turbo)'
B17_TIRE_15='205/55R16 (S) / 205/50R17 (SV/SR/SL)'   # 2015: no NISMO/SR-Turbo yet
B18_TIRE='205/60R16 (S) / 215/50R17 (SV) / 215/45R18 (SR)'

OIL_18ONLY=dict(visc='0W-20', cw='4.3 qt', cwo='4.0 qt',
                oem='Genuine Nissan Motor Oil 0W-20 (API SN/SP)')
OIL_DUAL  =dict(visc='0W-20', cw='4.3 qt (1.8L) / 4.6 qt (1.6T)', cwo='4.0 qt (1.8L) / 4.4 qt (1.6T)',
                oem='Genuine Nissan Motor Oil 0W-20 (1.8L & 1.6T VC-Turbo), API SN/SP')
OIL_20    =dict(visc='0W-20', cw='4.4 qt', cwo='4.0 qt',
                oem='Genuine Nissan Motor Oil 0W-20 (2.0L), API SN/SP')

def row(vid,year,gen,kind,spec_src,maint_src):
    if kind=='15':   oil,cc,tire,tor = OIL_18ONLY,'9.0 qt',B17_TIRE_15,[LUG,B17_DRAIN,B17_FILT]
    elif kind=='dual': oil,cc,tire,tor = OIL_DUAL,'9.0 qt (1.8L) / 9.2 qt (1.6T)',B17_TIRE,[LUG,B17_DRAIN,B17_FILT]
    else:            oil,cc,tire,tor = OIL_20,'7.5 qt',B18_TIRE,[LUG,B18_DRAIN,B18_FILT]
    brake='Nissan DOT 3 or DOT 4' if year==2026 else 'Nissan DOT 3'
    return dict(vid=vid,year=year,gen=gen,oil=oil,cc=cc,tire=tire,tor=tor,brake=brake,
                spec_src=spec_src,maint_src=maint_src)

SS='owner-manual-verified'
TARGETS=[
 row(12146,2015,'B17','15',  'owner-manual-verified (per 2015 Sentra OM, B17, 1.8L only)', "Nissan Owner's Manual (2015 Sentra, B17)"),
 row(12553,2018,'B17','dual','owner-manual-verified (per 2019 Sentra OM, B17 gen; engine config confirmed vs each year OM)', "Nissan Owner's Manual (2019 Sentra, B17 gen)"),
 row(12706,2019,'B17','dual', SS, "Nissan Owner's Manual (2019 Sentra Sedan)"),
 row(467,  2020,'B18','20',   SS, "Nissan Owner's Manual (2020 Sentra Sedan)"),
 row(1965, 2021,'B18','20',  'owner-manual-verified (per 2020 Sentra OM, B18 gen)', "Nissan Owner's Manual (2020 Sentra, B18 gen)"),
 row(9788, 2026,'B18','20',  'owner-manual-verified (per 2026 Sentra OM, B18, 2.0L)', "Nissan Owner's Manual (2026 Sentra, B18)"),
]

TIRE_NOTE_B17="Tire pressure 33 psi front/rear all grades (230 kPa). Per 2019 Sentra OM p8-37."
TIRE_NOTE_B18="Tire pressure 33 psi front/rear all grades (230 kPa). Per 2020 Sentra OM p8-31."
BATT_NOTE=("Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual "
           "(service-manual fields) - pending. CVT fluid NS-3 type verified; capacity not in OM. "
           "Drain-plug, oil-filter, and lug torque ARE in the Nissan OM and are recorded verified.")

db=sqlite3.connect(DB); c=db.cursor()
mx=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]; nid=mx+1

for r in TARGETS:
    vid=r['vid']
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    o=r['oil']
    c.execute("""INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,
        capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,o['visc'],None,o['cw'],o['cwo'],o['oem'],None,None,None,None,None,r['spec_src']))
    c.execute("""INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
        coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (vid,COMMON['trans'],None,r['brake'],COMMON['coolant_type'],r['cc'],COMMON['ps'],None,r['spec_src']))
    tnote=TIRE_NOTE_B17 if r['gen']=='B17' else TIRE_NOTE_B18
    c.execute("""INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
        battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
        air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,
        battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid,None,None,4,None,None,r['tire'],33,33,None,None,None,None,None,tnote,BATT_NOTE,
         None,None,None,None,r['spec_src']))
    for comp,ft,nm,note in r['tor']:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
                  (vid,comp,ft,nm,note,'owner-manual-verified'))
    rot='Tire rotation - every 5,000 mi (severe) per maintenance schedule'
    for mi,mo,desc in [
        (None,None,'Engine oil & filter change - oil control system (oil-life based); follow oil maintenance reminder'),
        (5000,None,rot)]:
        c.execute("""INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,
            source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (nid,vid,mi,mo,desc,r['maint_src'],'standard',None,None,None)); nid+=1
    print('  wrote %d (%s %s, %s)'%(vid,r['year'],r['gen'],{'15':'1.8L-only','dual':'1.8L+1.6T','20':'2.0L'}[ '15' if r['year']==2015 else ('dual' if r['gen']=='B17' else '20')]))

db.commit()
print('\nVerify:')
for r in TARGETS:
    vid=r['vid']
    o=c.execute('SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    tq=c.execute('SELECT component,torque_ft_lbs FROM torque_specs WHERE vehicle_id=? ORDER BY component',(vid,)).fetchall()
    print('  %d(%s): cap=%-26s torque=%s'%(vid,r['year'],o[1],dict((x[0],x[1]) for x in tq)))
db.close(); print('\nDONE.')
