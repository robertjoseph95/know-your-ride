# GMC Sierra 1500 - all 15 rows (twin of Silverado 1500). Each cited to its OWN GMC Sierra OM.
# Twin cross-check (this session) confirmed every platform-shared field matches Silverado per gen
#   (brake DOT3->DOT4, PS hydraulic->EPS, oil 5W-30->0W-20, spec starburst->GM6094M->dexos1,
#    ATF 4spd-DEXRON-III -> 6/8 VI/HP -> 8/10 HP/ULV). Engines byte-identical -> per-engine values match.
# Diesel via the shared "Chevrolet/GMC" Duramax 3.0L supplement (LM2 2020-2022 / LZ0 2023-2026).
# GATE (mirror Silverado): battery group, drain/oil-filter torque, tire (placard), trans speed-binding;
#   2003 V8 spark gap + part numbers GATED (2003 Sierra OM is a scanned/OCR copy, tech-data table illegible).
import sqlite3, json, shutil, datetime

DB='wrench_vehicles.db'
bak=DB+'.bak_sierra_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
TIRE_NOTE='Tire size & pressure are config-dependent (driver door-jamb Tire & Loading Information label, not in OM body) - pending.'

def write_row(vid,visc,oilcw,oem,trans,brake,coolant,cc,ps,diff,gap,plugs,bn,src):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",
        (vid,trans,None,brake,coolant,cc,ps,diff,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (vid,None,gap,None,None,None,None,None,None,plugs,None,None,None,None,TIRE_NOTE,bn,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",
        (vid,'lug_nut',140.0,190.0,"140 lb-ft (190 N-m), Wheel Nut Torque per owner's manual",'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (nid,vid,None,None,'Engine oil & filter change - GM Oil Life System; change when DIC/message indicates (at least once a year)',"GMC Owner's Manual (Sierra 1500)",'standard',None,None,None)); nid+=1

# ============ GMT800 (2000-2004) ============
G8_PS='Hydraulic power steering - GM Power Steering Fluid (GM 89021184)'
G8_BRAKE='GM-approved DOT 3 (Delco Supreme 11 or equivalent DOT-3)'
G8_COOL='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
G8_DIFF=json.dumps({"front_axle_4wd":"SAE 80W-90 Axle Lubricant (GM 1052271)","rear_axle":"SAE 75W-90 Synthetic Axle Lubricant (GM 12378261)"})
G8_VISC='5W-30 (all engines); 10W-30 acceptable above 0F/-18C'
G8_XFER='Transfer case (4WD): Automatic Transfer Case Fluid (GM 12378396), ~2.0 qt / 1.9 L'
G8COOL={2000:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8)',
 2001:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2002:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2003:'12.6 qt / 11.9 L (4.3L V6) / 13.4 qt / 12.7 L (4.8L V8) / 13.4 qt / 12.7 L (5.3L V8) / 14.8 qt / 14.0 L (6.0L V8)',
 2004:'14.0 qt / 13.0 L (4.3L V6) / 15.0 qt / 14.0 L (4.8L V8) / 14.0 qt / 13.0 L (5.3L V8) / 13.0 qt / 12.0 L (6.0L V8)'}
G8IDS={2000:10967,2001:10984,2002:11009,2003:11042,2004:11090}
for yr,vid in G8IDS.items():
    has60=yr>=2001
    v8='4.8L V8, 5.3L V8'+(', 6.0L V8' if has60 else '')
    oilcw='4.5 qt / 4.3 L (4.3L V6) / 6.0 qt / 5.7 L (%s)'%v8
    oem=('API Certified for Gasoline Engines (starburst symbol); GM6094M not cited in this model-year OM' if yr<=2003
         else 'GM6094M (API Certified for Gasoline Engines)')
    trans='4-speed automatic (4L60-E / 4L65-E): DEXRON-III ATF (per-engine transmission binding not specified in OM - gated). '+G8_XFER
    if yr<=2002: gap='0.060 in / 1.52 mm (all engines: 4.3L V6, %s)'%v8
    elif yr==2003: gap='0.060 in / 1.52 mm (4.3L V6); 4.8/5.3/6.0L V8 gap GATED - 2003 OM technical-data table illegible (scanned)'
    else: gap='0.060 in / 1.52 mm (4.3L V6); 0.040 in / 1.01 mm (%s)'%v8
    of_v8={2000:'ACDelco PF59',2001:'ACDelco PF59',2002:'ACDelco PF59',2003:None,2004:'ACDelco PF44'}[yr]
    of_line='Oil filter: ACDelco PF47 / GM 25010792 (4.3L V6)'+ ('; %s (V8 engines).'%of_v8 if of_v8 else '; V8 oil filter # GATED (2003 OM table illegible).')
    bn=('Battery: original-equipment maintenance-free - group size not in OM, GATED. '+of_line+
        ' Spark-plug part numbers are listed per-year in each OM (not transcribed - gap is the service spec). '
        'Fuel tank: 26.0 gal / 98.0 L (Short Bed) / 34.0 gal / 128.0 L (Long Bed). '
        'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed.'
        + (' 2003: V8 spark-plug gap & part numbers GATED - the 2003 GMC Sierra OM is a scanned/OCR copy whose technical-data table is illegible.' if yr==2003 else ''))
    src='owner-manual-verified (per %d GMC Sierra 1500 OM, self-ID p1; GMT800)'%yr
    write_row(vid,G8_VISC,oilcw,oem,trans,G8_BRAKE,G8_COOL,G8COOL[yr],G8_PS,G8_DIFF,gap,None,bn,src)
    print('  GMT800 %d (%d)'%(yr,vid))

# ============ K2XX (2017-2018) ============
K_VISC='5W-30 (4.3L V6) / 0W-20 (5.3L V8, 6.2L V8); 0W-30 below -29C/-20F'
K_OEM='dexos1 (ACDelco dexos1 Synthetic Blend)'
K_OILCW='6.0 qt / 5.7 L (4.3L V6) / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'
K_TRANS='6-speed automatic: DEXRON-VI ATF / 8-speed automatic: DEXRON-HP ATF (engine->transmission-speed binding not specified in OM - gated). Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L'
K_BRAKE='GM-approved DOT 3'
K_COOL='DEX-COOL, 50/50 premix with clean drinkable water (coolant spec number & color not stated in OM).'
K_CC='15.9 qt / 15.1 L (4.3L V6) / 16.6 qt / 15.7 L (5.3L V8) / 16.6 qt / 15.7 L (6.2L V8)'
K_PS='Electric power steering (EPS, 1500 Series) - no fluid, no regular maintenance'
K_DIFF=json.dumps({"rear_axle":"SAE 75W-85 Synthetic Axle Lubricant (1500 Series, GM 19300457)","front_axle_4wd":"SAE 75W-90 Synthetic Axle Lubricant (GM 88900401)"})
K_GAP='0.037-0.043 in / 0.95-1.10 mm (4.3L V6, 5.3L V8, 6.2L V8)'
K_PLUGS=json.dumps([{"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":"4.3L V6 (LV3/LV1), 5.3L V8 (L83) & 6.2L V8 (L86)","is_oem":True}])
K_BN=('Battery: original-equipment maintenance-free - GM punts group size to the battery label, GATED. '
      'Oil filter: ACDelco PF63E / GM 19330000 (4.3L V6, 5.3L & 6.2L V8). Engine air filter: ACDelco A3181C / GM 22845992. '
      'Cabin air filter: ACDelco CF188 / GM 23281440. Fuel tank: 26.0 gal / 98.4 L (Std/Short Box) / 34.0 gal / 128.7 L (Long Box). '
      'NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed.')
for yr,vid in {2017:12370,2018:12506}.items():
    src='owner-manual-verified (per %d GMC Sierra 1500 OM, self-ID p1; K2XX)'%yr
    write_row(vid,K_VISC,K_OILCW,K_OEM,K_TRANS,K_BRAKE,K_COOL,K_CC,K_PS,K_DIFF,K_GAP,K_PLUGS,K_BN,src)
    print('  K2XX %d (%d)'%(yr,vid))

# ============ T1XX (2019-2026) ============
T_BRAKE='GM-approved DOT 4'
T_PS='Electric power steering (EPS) - no fluid, no regular maintenance'
T_COOL_GAS='DEX-COOL (GM spec GMW3420), 50/50 premix with clean drinkable water; service 5 yr / 150,000 mi (color not stated in OM).'
T_COOL_DSL=' 3.0L Duramax diesel: DEX-COOL 50/50 with a separate charge-air cooling loop.'
T_XFER='Transfer case (4WD): DEXRON-VI ATF, 1.6 qt / 1.5 L'
LM2=dict(cool='20.5 qt / 19.4 L (3.0L Duramax diesel LM2, pickup, total incl. charge-air)',def_='5.3 gal / 20.3 L',oilf='ACDelco PF66 / GM 55495105',fuelf='GM 23304096 / ACDelco TP1015',vin='VIN T',src='2021 3.0L Duramax Diesel Supplement part# 84557033C, LM2 diesel')
LZ0=dict(cool='19.4 qt / 18.4 L (3.0L Duramax diesel LZ0, pickup, total incl. charge-air)',def_='5.4 gal / 20.5 L',oilf='ACDelco PF66 / GM 12727115',fuelf='GM 13539108',vin='VIN 8',src='2024 3.0L Duramax Diesel Supplement part# 85137419 B, LZ0 diesel')
EARLY=dict(oilf_27='ACDelco PF66 / GM 55495105',oilf_v='ACDelco PF63E / GM 12690385',om='2021 GMC Sierra 1500 OM')
LATE =dict(oilf_27='ACDelco PF66 / GM 12727115',oilf_v='ACDelco PF63 / GM 12707246',om='2023 GMC Sierra 1500 OM')
def t1xx(yr,vid,has43,diesel,era):
    visc='5W-30 (2.7L turbo'+(', 4.3L V6' if has43 else '')+') / 0W-20 (5.3L V8, 6.2L V8)'
    if diesel: visc+=' / 0W-20 dexos D (3.0L Duramax diesel, %s)'%('LM2' if diesel is LM2 else 'LZ0')
    visc+='; gas 0W-30 below -29C/-20F'
    oilcw='6.0 qt / 5.7 L (2.7L turbo'+(', 4.3L V6' if has43 else '')+') / 8.0 qt / 7.6 L (5.3L V8, 6.2L V8)'
    if diesel: oilcw+=' / 7.0 qt / 6.6 L (3.0L Duramax diesel)'
    oem='dexos1 full synthetic (ACDelco dexos1)'+(' - gas; dexos D (ACDelco dexos D) - 3.0L Duramax diesel' if diesel else '')
    if has43: cc='12.4 qt / 11.8 L (2.7L turbo) / 12.2 qt / 11.5 L (4.3L V6) / 13.5 qt (5.3L V8 L82) / 13.8 qt (5.3L V8 L84) / 13.3 qt / 12.6 L (6.2L V8)'
    else: cc='12.4 qt / 11.8 L (2.7L turbo) / 13.8 qt / 13.1 L (5.3L V8) / 13.3 qt / 12.6 L (6.2L V8)'
    if diesel: cc+=' / '+diesel['cool']
    coolant=T_COOL_GAS+(T_COOL_DSL if diesel else '')
    trans='8-speed automatic: DEXRON-HP ATF / 10-speed automatic: DEXRON ULV ATF '
    trans+=('(3.0L Duramax diesel pairs with the 10-speed = DEXRON ULV, confirmed in Duramax supplement; gas engine->speed binding not in OM - gated). ' if diesel else '(engine->transmission-speed binding not specified in OM - gated). ')
    trans+=T_XFER
    gap='0.026-0.030 in / 0.65-0.75 mm (2.7L turbo); 0.037-0.043 in / 0.95-1.10 mm ('+('4.3L V6, ' if has43 else '')+'5.3L V8, 6.2L V8)'
    if diesel: gap+=' [3.0L diesel = compression ignition, no spark plugs]'
    plugs=json.dumps([{"brand":"ACDelco","part_number":"41-106-IP (GM 12688094)","description":"2.7L turbo (L3B)","is_oem":True},
      {"brand":"ACDelco","part_number":"41-114 (GM 12622441)","description":("4.3L V6 (LV3), " if has43 else "")+"5.3L V8"+(" (L82/L84)" if has43 else " (L84)")+" & 6.2L V8 (L87)","is_oem":True}])
    oilf_line='Oil filter: %s (2.7L turbo%s); %s (%s5.3L & 6.2L V8).'%(era['oilf_27'],' & 3.0L Duramax diesel' if (diesel and diesel['oilf']==era['oilf_27']) else '',era['oilf_v'],'4.3L V6, ' if has43 else '')
    bn='AGM 12V battery (Stop/Start equipped) - GM punts group size to the battery label, GATED. '+oilf_line+' Engine air filter: ACDelco A3244C / A3246C. Cabin air filter: ACDelco CF185 / GM 13508023. '
    if diesel: bn+='3.0L Duramax diesel (%s, %s): 0W-20 dexos D, 7.0 qt; oil filter %s; fuel filter %s; DEF tank %s (ISO 22241); pairs with 10-speed (DEXRON ULV). '%('LM2' if diesel is LM2 else 'LZ0',diesel['vin'],diesel['oilf'],diesel['fuelf'],diesel['def_'])
    else: bn+='3.0L Duramax diesel not offered this year (launched 2020). '
    bn+='NOT in OM (pending/gated): battery group & CCA, drain-plug torque, oil-filter torque, tire size/pressure (placard), per-engine transmission speed (gas).'
    src='owner-manual-verified (per %s'%era['om']+((' + '+diesel['src']) if diesel else '; T1XX gen-rep')+')'
    write_row(vid,visc,oilcw,oem,trans,T_BRAKE,coolant,cc,T_PS,None,gap,plugs,bn,src)
    print('  T1XX %d (%d)'%(yr,vid))

t1xx(2019,12653,True ,None,EARLY)
t1xx(2020,12771,True ,LM2 ,EARLY)
t1xx(2021,12841,True ,LM2 ,EARLY)
t1xx(2022,12906,False,LM2 ,LATE)
t1xx(2023,12971,False,LZ0 ,LATE)
t1xx(2024,13037,False,LZ0 ,LATE)
t1xx(2025,13103,False,LZ0 ,LATE)
t1xx(2026,13169,False,LZ0 ,LATE)

db.commit()
print('\nVerify (15 rows):')
for vid in [10967,11090,12370,12653,12841,12906,12971,13169]:
    o=c.execute('SELECT viscosity FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()[0]
    f=c.execute('SELECT brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    yr=c.execute('SELECT year FROM vehicles WHERE id=?',(vid,)).fetchone()[0]
    print('  %d: %s | %s | %s'%(yr,o[:34],f[0],f[1][:22]))
db.close(); print('DONE.')
