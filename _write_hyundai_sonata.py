# Hyundai Sonata - FIRST HYUNDAI slice (fresh make). 5 writable rows; 9 deferred (untouched).
# Writable: 2005/2006 NF (2.4 Theta + 3.3 Lambda V6), 2018 LF (2.4 GDI + 2.0T + 1.6T), 2021 DN8 (2.5 + 1.6T),
#   2024 DN8-FL (2.5 GDI + 2.5T N-Line). Source = owners.hyundaiusa.com MyHyundai glovebox-manual (free, citable).
# All multi-engine (turbos/N-Line are trims within the year's row). HEV = gated variant (own OM slug) - gas specs written.
# ** MAKE-LEVEL FINDINGS (banked to source map for the Kia/Optima unlock): **
#   - 2005 = NF gen (2.4 Theta + 3.3 Lambda), NOT EF - Hyundai filename year = badged MY; confirm gen by displacement.
#   - Coolant-basis inconsistent across OM eras: 2021 DN8 lists anomalously-low (5.49/4.76, refill/partial?) vs
#     2018 (7.60) & 2024 (9.2) total-system -> GATE 2021 coolant capacity (write type).
#   - Plug PN: NF-era OM publishes PN + gap (SK16PR-A11/IFR5G-11, 0.039-0.043); MODERN OMs publish interval-only
#     -> GATE modern plug PN (OM-does-not-publish, like modern Subaru's gap). Same gate hits Optima/K5 modern rows.
#   - PS: NF hydraulic (PSF-3) -> modern EPS (no PS fluid).
# GATES (honest, per field): modern plug PN (unpublished) ; 2021 coolant cap (suspect basis) ; 2018/2021 battery
#   group (OM->label) ; NF lug (not surfaced) ; 2024 tire (not cleanly read) ; all HEV-specific.
import sqlite3, json, shutil, datetime
DB='wrench_vehicles.db'
shutil.copy2(DB,DB+'.bak_sonata_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
db=sqlite3.connect(DB); c=db.cursor()
nid=c.execute('SELECT COALESCE(MAX(id),0) FROM maintenance').fetchone()[0]+1
COOL_TYPE='Ethylene glycol base coolant for aluminum radiator (Hyundai long-life coolant)'
def W(vid,visc,oilcw,oem,trans,cc,ps,brake,plug_type,gap,plugs_json,batt,tire,lug_lb,lug_nm,src,bn):
    for t in ['oil_change','fluids','parts','maintenance','torque_specs','engine_specs']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    c.execute("INSERT INTO oil_change (vehicle_id,viscosity,oil_type,capacity_with_filter,capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(vid,visc,None,oilcw,None,oem,None,None,None,None,None,src))
    c.execute("INSERT INTO fluids (vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json,source) VALUES (?,?,?,?,?,?,?,?,?)",(vid,trans,None,brake,COOL_TYPE,cc,ps,None,src))
    c.execute("INSERT INTO parts (vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(vid,plug_type,gap,None,batt,None,tire,None,None,plugs_json,None,None,None,None,None,None,None,None,None,None,src))
    if lug_lb:
        c.execute("INSERT INTO torque_specs (vehicle_id,component,torque_ft_lbs,torque_nm,notes,source) VALUES (?,?,?,?,?,?)",(vid,'lug_nut',lug_lb,lug_nm,'%s lb-ft (%s N-m), wheel nut tightening torque per owner manual (range)'%(lug_lb,lug_nm),'owner-manual-verified'))
    global nid
    c.execute("INSERT INTO maintenance (id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level,tool_required,time_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,vid,None,None,'Engine oil & filter change - per Hyundai maintenance schedule',"Hyundai Owner's Manual (Sonata)",'standard',None,None,None)); nid+=1

# ---- NF 2005 + 2006 (2.4 Theta + 3.3 Lambda V6) ----
PLUG_NF=json.dumps([{"brand":"Champion","part_number":"SK16PR-A11","description":"2.4L Theta (also NGK equiv)","is_oem":True},{"brand":"NGK","part_number":"IFR5G-11","description":"3.3L Lambda V6","is_oem":True}])
NF_TRANS='Automatic (SHIFTRONIC): ATF SP-III (Diamond ATF SP-III / SK ATF SP-III) - 2.4L 8.24 qt / 3.3L 11.52 qt. Manual: MTF 75W/85 (API GL-4), 2.0 qt.'
for vid,yr,doc in [(35202,2005,'2005_Hyundai_Sonata_OM.pdf'),(11226,2006,'2006_Hyundai_Sonata_OM.pdf')]:
    W(vid,'5W-20 (5W-30 all-temp alt; 10W-30 above 0F); API SJ/SL, ILSAC GF-3',
      '4.54 qt / 4.3 L (2.4L Theta I4) / 6.02 qt / 5.7 L (3.3L Lambda V6)',
      'API SJ/SL or above, ILSAC GF-3 or above; SAE 5W-20',NF_TRANS,
      '6.66 qt / 6.3 L (2.4L AT; 6.87 qt MT) / 8.66 qt / 8.2 L (3.3L)',
      'Hydraulic power steering - PSF-3 type fluid, 0.95 qt (vane pump; this era is HYDRAULIC, not EPS)',
      'FMVSS No. 116, DOT 3 or DOT 4 brake fluid',
      'NGK/Champion - 2.4L Theta: SK16PR-A11 ; 3.3L Lambda V6: IFR5G-11','0.039 to 0.043 in (1.0 to 1.1 mm)',PLUG_NF,
      'MF68AH','P215/60R16 (option P225/50R17)',None,None,
      'owner-manual-verified (per %d Hyundai Sonata OM %s, MyHyundai glovebox-manual; NF gen confirmed by displacement 2359cc Theta + 3342cc Lambda + cover; gap PUBLISHED this era)'%(yr,doc),
      'Fuel tank: 17.7 gal / 67 L. NF gen (2.4 Theta I4 + 3.3 Lambda V6). HYDRAULIC power steering (PSF-3). GATED (OM does not publish / not surfaced): lug torque, drain/oil-filter torque, oil-filter PN.')
    print('  %d NF 2.4 Theta + 3.3 Lambda (gap written, lug gated)'%yr)

# ---- LF 2018 (2.4 GDI + 2.0 T-GDI Theta II ; 1.6 T-GDI Gamma) ----
W(12523,'5W-20; API SM or above, ILSAC GF-4 or above (ACEA A5)',
  '5.07 qt / 4.8 L (2.4L GDI Theta II) / 5.07 qt / 4.8 L (2.0L T-GDI Theta II) / 4.75 qt / 4.5 L (1.6L T-GDI Gamma)',
  'API SM/GF-4 or above; SAE 5W-20',
  '6-speed automatic: ATF SP-IV (MICHANG/SK/NOCA/Hyundai genuine), 7.5 qt (2.4L & 2.0T). 1.6L T-GDI: 7-speed dual-clutch (DCT) - DCTF, API GL-4 SAE 70W, 2.0 qt.',
  '7.60 qt / 7.2 L (2.4L GDI) / 7.92 qt / 7.5 L (2.0L T-GDI) / 7.50 qt / 7.1 L (1.6L T-GDI)',
  'Electric power steering (EPS / MDPS) - no serviceable power-steering fluid',
  'FMVSS No. 116, DOT 3 or DOT 4 brake fluid',
  None,None,None,None,'205/65R16 (215/55R17 & 235/45R18 by trim)',79.0,107.0,
  'owner-manual-verified (per 2018 Hyundai Sonata OM 2018_Hyundai_Sonata_OM.pdf, MyHyundai glovebox-manual; LF gen)',
  'Fuel tank: 18.5 gal / 70 L. LF gen (Theta II 2.4 GDI + 2.0 T-GDI; Gamma 1.6 T-GDI). EPS. HYBRID variant exists (separate OM) - HEV traction/battery/transaxle GATED. GATED (modern OM does not publish): spark-plug PN/brand/gap (interval-only), battery group (OM refers to capacity label), drain/oil-filter torque.')
print('  2018 LF 2.4 GDI + 2.0T + 1.6T (plug PN + battery gated, HEV gated)')

# ---- DN8 2021 (2.5 GDI + 1.6 T-GDI Smartstream) - coolant GATED (suspect basis) ----
W(12853,'0W-20; API SN PLUS/SP or ILSAC GF-6',
  '5.49 qt / 5.2 L (2.5L GDI Smartstream) / 5.07 qt / 4.8 L (1.6L T-GDI Smartstream)',
  'API SN PLUS/SP, ILSAC GF-6; SAE 0W-20',
  '8-speed automatic: ATF SP-IV (MICHANG/SK/NOCA/Hyundai genuine ATF SP-IV), 6.89 qt.',
  None,
  'Electric power steering (EPS / MDPS) - no serviceable power-steering fluid',
  'FMVSS No. 116, DOT 4 brake fluid (DOT-4 LV)',
  None,None,None,None,'205/65R16',79.0,107.0,
  'owner-manual-verified (per 2021 Hyundai Sonata OM 2021-Sonata-Owners-Manual.pdf, MyHyundai glovebox-manual; DN8 gen)',
  'Fuel tank: 15.85 gal / 60 L. DN8 gen (Smartstream 2.5 GDI + 1.6 T-GDI). EPS. COOLANT CAPACITY GATED: the 2021 OM lists an anomalously-low coolant (2.5=5.49 / 1.6T=4.76 qt) that is out of family with the same Smartstream 2.5 in the 2024 OM (9.2 qt, total-system) and the 2018 scale - a refill/partial basis, not total system; written type only, capacity gated pending a clean total-system figure. Also GATED: spark-plug PN (modern OM interval-only), battery group, HEV system.')
print('  2021 DN8 2.5 + 1.6T (coolant GATED suspect-basis, plug/battery gated, HEV gated)')

# ---- DN8-FL 2024 (2.5 GDI + 2.5 T-GDI N-Line Smartstream) ----
W(13049,'0W-20 (2.5L GDI) / 0W-30 (2.5L T-GDI); API SN PLUS/SP or ILSAC GF-6',
  '6.13 qt / 5.8 L (2.5L GDI Smartstream) / 6.13 qt / 5.8 L (2.5L T-GDI Smartstream N-Line)',
  'API SN PLUS/SP, ILSAC GF-6; 0W-20 (GDI) / 0W-30 (T-GDI)',
  '8-speed automatic: ATF SP4-M1 (SK/MICHANG/S-OIL/Hyundai genuine), 6.8 qt (2.5L GDI). 2.5L T-GDI (N-Line): 8-speed wet dual-clutch (DCT) - gear oil 3.5 qt (GS WDCTF HD G) + control oil 2.6 qt (GS WDCTF HD H).',
  '9.2 qt / 8.7 L (2.5L GDI) / 9.3 qt / 8.8 L (2.5L T-GDI)',
  'Electric power steering (EPS / MDPS) - no serviceable power-steering fluid',
  'FMVSS No. 116, DOT 4 brake fluid',
  None,None,None,'AGM70L','205/65R16',79.0,107.0,
  'owner-manual-verified (per 2024 Hyundai Sonata OM (24 Sonata OM.pdf), MyHyundai glovebox-manual; DN8 facelift)',
  'Fuel tank: 15.9 gal / 60 L. DN8 facelift (Smartstream 2.5 GDI + 2.5 T-GDI N-Line via wet-DCT). EPS. Battery AGM70L. Facelift moved 2.5 oil 5.49->6.13 qt vs 2021. GATED (modern OM does not publish): spark-plug PN/gap (interval-only), HEV system.')
print('  2024 DN8-FL 2.5 GDI + 2.5T N-Line (battery AGM70L, plug gated, HEV gated)')

db.commit()
print('\nVerify (9 deferred rows untouched):')
for vid,y in [(11015,2002),(11098,2004),(12676,2019),(12783,2020),(13115,2025),(13181,2026)]:
    o=c.execute('SELECT source FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %d %s DEFER -> %s'%(vid,y,(o[0] if o and o[0] else 'none')))
for vid,l in [(35202,'2005NF'),(12523,'2018LF'),(12853,'2021DN8'),(13049,'2024FL')]:
    o=c.execute('SELECT capacity_with_filter FROM oil_change WHERE vehicle_id=?',(vid,)).fetchone()
    f=c.execute('SELECT coolant_capacity,power_steering_fluid FROM fluids WHERE vehicle_id=?',(vid,)).fetchone()
    print('  %s(%d): oil=%s | cool=%s | ps=%s'%(l,vid,o[0][:34],(f[0][:20] if f[0] else 'GATED'),f[1][:22]))
db.close(); print('DONE - 5 Sonata rows written, 9 deferred untouched.')
