# Hyundai Elantra - SECOND Hyundai slice (cashes the Sonata source foundation). 4 writable; 9 deferred (untouched).
# Writable: 2017/2020 AD, 2021/2022 CN7. Source = owners.hyundaiusa.com glovebox-manual (free, citable).
# Multi-engine per row (base OM only; separate-OM trims noted, NOT written). HEV = gated variant.
# ** CONFIRMS engine-decided/body-decided split across a body-class boundary (compact vs Sonata sedan): **
#   - 1.6T Smartstream oil 5.07 = Sonata DN8 5.07 (engine-decided MATCH). 1.6T Gamma oil 4.76 ~= Sonata LF 4.75
#     (match; visc diverges - Elantra 2020 Gamma 5W-30 vs Sonata LF 5W-20, written as-stated).
#   - BODY-decided diverge: fuel 14.0(AD)/12.4(CN7) vs Sonata 15.9; tire 205/55R16 vs Sonata 205/65R16; coolant Elantra-specific.
# ** Per-year catches: base 2.0 Nu 4.23/5W-20 (AD) -> Smartstream 4.54/0W-20 (CN7), coolant 6.34/6.97->7.82 (engine
#    change across AD->CN7); 1.6T Gamma(2020)->Smartstream(2022) badge-but-different; trans 6AT SP-IV(2017)->IVT SP-CVT1+DCT(2020+).
# ** Gates (banked from Sonata): plug PN GATE (modern OM interval-only, no brand/PN - confirmed transfers);
#    coolant-basis gate APPLIED + PASSED (Elantra coolant 6.34-7.82 all total-system-scale, no anomaly -> WRITE).
#    Battery: AD gated (OM->label) / CN7 AGM70L. EPS all (no PS fluid). SEPARATE-OM engines gated: 1.4T Eco(2017),
#    1.6T Sport(2017), 2.0T Elantra N(2022) - not in base OM; future targeted pull if wanted.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_elantra_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
COOL_TYPE='Ethylene glycol base coolant for aluminum radiator (phosphate-based; Hyundai long-life coolant)'
EPS='Electric power steering (EPS / MDPS) - no serviceable power-steering fluid'
def W(vid,visc,oilcw,oem,trans,cc,brake,batt,tire,src,bn):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,COOL_TYPE,cc,EPS,None,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,None,None,None,batt,None,tire,None,None,None,None,None,None,None,None,None,None,None,None,None,src))
    c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',79.0,107.0,'79 to 94 lb-ft (107 to 127 N-m), wheel nut tightening torque per owner manual (range)','owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Hyundai maintenance schedule',"Hyundai Owner's Manual (Elantra)",'standard',None,None,None)); nid+=1

# 2017 AD - 2.0 Nu (base OM only)
W(12379,'5W-20; API SM or above, ILSAC GF-4 or above (ACEA A5)','4.23 qt / 4.0 L (2.0L Nu MPI)',
  'API SM/GF-4 or above; SAE 5W-20',
  '6-speed automatic: ATF SP-IV (MICHANG/SK/NOCA/Hyundai genuine), 7.08 qt. Manual: MTF 70W (API GL-4, SAE 70W TGO-9), 1.8-1.9 qt.',
  '6.34 qt / 6.0 L (2.0L MT) / 6.97 qt / 6.6 L (2.0L AT)','FMVSS No. 116, DOT 3 or DOT 4',None,'205/55R16',
  'owner-manual-verified (per 2017 Hyundai Elantra OM 2017_Hyundai_Elantra_OM.pdf, MyHyundai glovebox-manual; AD gen, base 2.0 Nu)',
  'Fuel tank: 14.0 gal / 53 L (compact - vs Sonata 15.9). AD gen, 2.0 Nu MPI (base). EPS. 6-speed auto. GATED (modern OM interval-only / OM->label): spark-plug PN/gap, battery group. SEPARATE-OM trims not in this OM (not written): 1.4T Eco, 1.6T Sport.')
print('  2017 AD 2.0 Nu (6AT, coolant 6.34/6.97)')

# 2020 AD - 2.0 MPI + 1.6 T-GDI (Gamma)
W(669,'5W-20 (2.0L Nu MPI) / 5W-30 (1.6L T-GDI Gamma); API Latest/ILSAC Latest','4.23 qt / 4.0 L (2.0L Nu MPI) / 4.76 qt / 4.5 L (1.6L T-GDI Gamma)',
  'API Latest (ILSAC Latest); 2.0L 5W-20, 1.6T 5W-30',
  '2.0L: Intelligent Variable Transmission (IVT/CVT), IVTF SP-CVT1, 6.86 qt. 1.6L T-GDI: 7-speed dual-clutch (DCT), DCTF (API GL-4 SAE 70W), 2.01-2.11 qt. Manual: MTF 70W GL-4, 1.6-1.7 qt.',
  '6.34 qt / 6.0 L (2.0L MT) / 6.97 qt / 6.6 L (2.0L IVT) / 6.45 qt / 6.1 L (1.6L T-GDI)','FMVSS No. 116, DOT 3 or DOT 4',None,'205/55R16 (225/40R18 Sport)',
  'owner-manual-verified (per 2020 Hyundai Elantra OM [2020 Elantra Owners Manual.pdf, note misspelled portal slug /elentra/]; AD gen, 2.0 Nu MPI + 1.6 T-GDI Gamma)',
  'Fuel tank: 14.0 gal / 53 L (compact). AD gen. 2.0 Nu MPI (IVT) + 1.6 T-GDI Gamma (7-DCT). 1.6T Gamma oil 4.76 ~= Sonata LF 4.75 (engine match); visc 5W-30 (Elantra) vs Sonata LF 5W-20 (as-stated). EPS. GATED: spark-plug PN/gap, battery group. Separate-OM: 1.4T Eco.')
print('  2020 AD 2.0 Nu + 1.6T Gamma (IVT+DCT)')

# 2021 CN7 - 2.0 Smartstream (base OM only)
W(2163,'0W-20; API SN PLUS/SP or ILSAC GF-6','4.54 qt / 4.3 L (2.0L Smartstream G2.0 Atkinson)',
  'API SN PLUS/SP, ILSAC GF-6; SAE 0W-20',
  '2.0L: Intelligent Variable Transmission (IVT/CVT), Hyundai genuine SP-CVT1, 6.87 qt.',
  '7.82 qt / 7.4 L (2.0L Smartstream)','FMVSS No. 116, DOT 4 brake fluid','AGM70L','205/55R16',
  'owner-manual-verified (per 2021 Hyundai Elantra OM 2021-Elantra-Owners-Manual.pdf, MyHyundai glovebox-manual; CN7 gen, base 2.0 Smartstream)',
  'Fuel tank: 12.4 gal / 47 L (compact, CN7 tank shrank from AD 14.0). CN7 gen, 2.0 Smartstream Atkinson (IVT). EPS. Base 2.0 oil 4.54/0W-20 = Smartstream (vs AD Nu 4.23/5W-20 - engine change across AD->CN7). GATED (modern OM interval-only): spark-plug PN/gap. Separate-OM (not in base): 1.6T N-Line, Hybrid (HEV gated).')
print('  2021 CN7 2.0 Smartstream (IVT, AGM70L)')

# 2022 CN7 - 2.0 Smartstream + 1.6 T-GDI Smartstream (N-Line)
W(3691,'0W-20; API SN PLUS/SP or ILSAC GF-6','4.54 qt / 4.3 L (2.0L Smartstream G2.0 Atkinson) / 5.07 qt / 4.8 L (1.6L T-GDI Smartstream N-Line)',
  'API SN PLUS/SP, ILSAC GF-6; SAE 0W-20',
  '2.0L: IVT (Intelligent Variable Transmission), Hyundai genuine SP-CVT1, 6.87 qt. 1.6L T-GDI (N-Line): 7-speed dual-clutch (DCT), DCTF (API GL-4 SAE 70W), 1.7-1.8 qt. Manual: MTF 70W GL-4, 1.6-1.7 qt.',
  '7.82 qt / 7.4 L (2.0L Smartstream) / 7.19 qt / 6.8 L (1.6L T-GDI)','FMVSS No. 116, DOT 4 brake fluid','AGM70L','205/55R16 (235/40R18 N-Line)',
  'owner-manual-verified (per 2022 Hyundai Elantra OM 2022-Elantra-Owners-Manual.pdf; CN7 gen, 2.0 Smartstream + 1.6 T-GDI Smartstream N-Line)',
  'Fuel tank: 12.4 gal / 47 L (compact). CN7 gen. 2.0 Smartstream (IVT) + 1.6 T-GDI Smartstream N-Line (7-DCT). 1.6T oil 5.07/0W-20 = Sonata DN8 5.07 (engine-decided MATCH, twin confirmed); coolant 7.19 fresh (compact). EPS. GATED: spark-plug PN/gap. Separate-OM (not written): 2.0T Elantra N, Hybrid (HEV gated) - future targeted pull for the N performance engine.')
print('  2022 CN7 2.0 Smartstream + 1.6T Smartstream N-Line (AGM70L)')

db.commit()
print('\\nVerify (9 deferred untouched):')
for vid,y in [(11013,2002),(11096,2004),(12520,2018),(6785,2024),(8360,2025),(9974,2026)]:
    o=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d %s DEFER -> %s'%(vid,y,(o[0] if o and o[0] else 'none')))
for vid,l in [(12379,'2017'),(669,'2020'),(2163,'2021'),(3691,'2022')]:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s(%d): oil=%s | cool=%s'%(l,vid,o[0][:38],(f[0][:24] if f[0] else 'GATED')))
db.close(); print('DONE - 4 Elantra rows written, 9 deferred untouched.')
