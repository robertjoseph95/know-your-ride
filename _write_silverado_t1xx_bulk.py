# Chevrolet Silverado 1500 T1XX bulk - 7 rows (2019,2020,2021,2022,2023,2025,2026). 2024 already done.
# Sources: 2021 Silverado 1500 OM (84550389C, early-T1XX rep incl. 4.3 V6) + 2024 OM (85516379C, late-T1XX)
#   + 2021 LM2 Duramax 3.0L sup (84557033C) + 2024 LZ0 Duramax 3.0L sup (85137419 B).
# Per-year EPA gas roster: 2019-2021 = 2.7T/4.3 V6/5.3/6.2; 2022-2026 = 2.7T/5.3/6.2 (4.3 dropped after 2021).
# Diesel: 2019 none; 2020-2022 = LM2 (20.5qt coolant, DEF 5.3gal); 2023/2025/2026 = LZ0 (19.4qt, DEF 5.4gal).
# CONFIRM-DON'T-ASSUME: LM2 != LZ0 (coolant/DEF/filters differ - read both sups); 4.3 V6 = 5W-30 like 2.7T.
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_silv_t1xx_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

# ---- shared (generation-stable) ----
BRAKE='GM-approved DOT 4'
PS='Electric power steering (EPS) - no fluid, no regular maintenance'
COOLANT_GAS='DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water; service 5 yr / 150,000 mi (color not stated in OM).'
COOLANT_DSL=' 3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.'
XFER='Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L'
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

# diesel version specs
LM2=dict(cool='20.5 qt / 19.4 L (3.0L Duramax diesel LM2, pickup, total incl. charge-air)',
         def_='5.3 gal / 20.3 L', oilf='ACDelco PF66 / GM 55495105', fuelf='GM 23304096 / ACDelco TP1015', vin='VIN T',
         src='2021 3.0L Duramax Diesel Supplement part# 84557033C, LM2 diesel')
LZ0=dict(cool='19.4 qt / 18.4 L (3.0L Duramax diesel LZ0, pickup, total incl. charge-air)',
         def_='5.4 gal / 20.5 L', oilf='ACDelco PF66 / GM 12727115', fuelf='GM 13539108', vin='VIN 8',
         src='2024 3.0L Duramax Diesel Supplement part# 85137419 B, LZ0 diesel')

# per-era gas part numbers
ERA_EARLY=dict(  # 2019-2021 (2021 OM)
  oilf_27='ACDelco PF66 / GM 55495105', oilf_v='ACDelco PF63E / GM 12690385',
  spark27='ACDelco 41-106-IP (GM 12688094)', sparkv='ACDelco 41-114 (GM 12622441)', omname='2021 Silverado 1500 OM')
ERA_LATE=dict(   # 2022-2026 (2024 OM)
  oilf_27='ACDelco PF66 / GM 12727115', oilf_v='ACDelco PF63 / GM 12707246',
  spark27='ACDelco 41-106-IP (GM 12688094)', sparkv='ACDelco 41-114 (GM 12622441)', omname='2024 Silverado 1500 OM')

def build(year, vid, has43, diesel, era):
    g43 = has43
    # oil viscosity
    visc = '5W-30 (2.7L turbo' + (', 4.3L V6' if g43 else '') + ') / 0W-20 (5.3L V8, 6.2L V8)'
    if diesel: visc += ' / 0W-20 dexos D (3.0L Duramax diesel, %s)' % ('LM2' if diesel is LM2 else 'LZ0')
    visc += '; gas 0W-30 below -29C/-20F'
    # oil cap
    oilcw = '6.0 qt / 5.7 L (2.7L turbo' + (', 4.3L V6' if g43 else '') + ') / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'
    if diesel: oilcw += ' / 7.0 qt / 6.6 L (3.0L Duramax diesel)'
    # oem spec
    oem = 'dexos1 full synthetic (ACDelco dexos1)' + (' - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel' if diesel else '')
    # coolant cap
    if g43:
        cc = '12.4 qt / 11.8 L (2.7L turbo) / 12.2 qt / 11.5 L (4.3L V6) / 13.5 qt (5.3L V8 L82) / 13.8 qt (5.3L V8 L84) / 13.3 qt / 12.6 L (6.2L V8)'
    else:
        cc = '12.4 qt / 11.8 L (2.7L turbo) / 13.8 qt / 13.1 L (5.3L V8) / 13.3 qt / 12.6 L (6.2L V8)'
    if diesel: cc += ' / ' + diesel['cool']
    coolant = COOLANT_GAS + (COOLANT_DSL if diesel else '')
    # transmission
    trans = '8-speed automatic: DEXRON-HP ATF / 10-speed automatic: DEXRON ULV ATF '
    if diesel:
        trans += '(3.0L Duramax diesel pairs with the 10-speed = DEXRON ULV, confirmed in Duramax supplement; gas engine->transmission-speed binding not in OM - gated). '
    else:
        trans += '(engine->transmission-speed binding not specified in OM - gated). '
    trans += XFER
    # spark gap + plugs
    gap = '0.026-0.030 in / 0.65-0.75 mm (2.7L turbo); 0.037-0.043 in / 0.95-1.10 mm (' + ('4.3L V6, ' if g43 else '') + '5.3L V8, 6.2L V8)'
    if diesel: gap += ' [3.0L diesel = compression ignition, no spark plugs]'
    plugs = [{"brand":"ACDelco","part_number":era['spark27'].split('(')[1][:-1] if '(' in era['spark27'] else era['spark27'],"description":"2.7L turbo (L3B)","is_oem":True}]
    # simpler: rebuild plug entries explicitly
    plugs = [
      {"brand":"ACDelco","part_number":"41-106-IP (GM 12688094)","description":"2.7L turbo (L3B)","is_oem":True},
      {"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":("4.3L V6 (LV3), " if g43 else "")+"5.3L V8"+(" (L82/L84)" if g43 else " (L84)")+" & 6.2L V8 (L87)","is_oem":True}]
    # battery_notes
    oilf_line = 'Oil filter: %s (2.7L turbo%s); %s (%s5.3L & 6.2L V8).' % (
        era['oilf_27'], ' & 3.0L Duramax diesel' if (diesel and diesel['oilf']==era['oilf_27']) else '',
        era['oilf_v'], '4.3L V6, ' if g43 else '')
    bn = ('AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '
          + oilf_line + ' Engine air filter: ACDelco A3244C (high-capacity) / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. ')
    if diesel:
        bn += ('3.0L Duramax diesel (%s): 0W-20 dexos D, 7.0 qt; oil filter %s; fuel filter %s; '
               'DEF (diesel exhaust fluid) tank %s (ISO 22241); pairs with 10-speed (DEXRON ULV). ' % (
               'LM2, '+diesel['vin'] if diesel is LM2 else 'LZ0, '+diesel['vin'], diesel['oilf'], diesel['fuelf'], diesel['def_']))
    else:
        bn += '3.0L Duramax diesel not offered this year (launched 2020). '
    bn += ('NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, '
           'tire size/pressure (door placard), per-engine transmission speed (gas).')
    # source
    if diesel:
        src = 'owner-manual-verified (per %s + %s)' % (era['omname'], diesel['src'])
    else:
        src = 'owner-manual-verified (per %s, T1XX gen-rep; gas 2.7L/4.3L/5.3L/6.2L; %d EPA roster - no diesel)' % (era['omname'], year)
    return dict(vid=vid,year=year,visc=visc,oilcw=oilcw,oem=oem,trans=trans,coolant=coolant,cc=cc,
                gap=gap,plugs=json.dumps(plugs),bn=bn,src=src)

ROWS=[
  build(2019,38591,True ,None,ERA_EARLY),
  build(2020,12750,True ,LM2 ,ERA_EARLY),
  build(2021,12819,True ,LM2 ,ERA_EARLY),
  build(2022,12885,False,LM2 ,ERA_LATE),
  build(2023,12950,False,LZ0 ,ERA_LATE),
  build(2025,13082,False,LZ0 ,ERA_LATE),
  build(2026,13148,False,LZ0 ,ERA_LATE),
]

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
for r in ROWS:
    vid=r['vid']
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,r['visc'],None,r['oilcw'],None,r['oem'],None,None,None,None,None,r['src']))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,r['trans'],None,BRAKE,r['coolant'],r['cc'],PS,None,r['src']))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,r['gap'],None,None,None,None,None,None,r['plugs'],None,None,None,None,TIRE_NOTE,r['bn'],None,None,None,None,r['src']))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Engine Oil Life System; change when DIC indicates (at least once a year)',"Chevrolet Owner's Manual (Silverado 1500)",'standard',None,None,None)); nid+=1
    print('  wrote %d (%s): diesel=%s 4.3=%s'%(vid,r['year'],'LM2' if 'LM2' in r['oem'] and 'LM2' in r['visc'] else ('LZ0' if 'LZ0' in r['visc'] else 'none'),'Y' if '4.3L V6' in r['oilcw'] else 'N'))

db.commit()
print('\nVerify:')
for r in ROWS:
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(r['vid'],)).fetchone()[0]
    print('  %d: %s'%(r['year'],o[:70]))
db.close(); print('DONE.')
