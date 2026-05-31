import sqlite3, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
c = sqlite3.connect("wrench_vehicles.db"); c.row_factory = sqlite3.Row
def q1(s, p=()): return c.execute(s, p).fetchone()[0]

ev=set()
for vid,comb in c.execute("SELECT vehicle_id,MAX(combined_mpg) FROM fuel_economy GROUP BY vehicle_id"):
    if comb and comb>=90: ev.add(vid)
ev|={r[0] for r in c.execute("SELECT vehicle_id FROM fuel_economy WHERE LOWER(COALESCE(fuel_type,'')) LIKE '%electric%'")}
ev|={r[0] for r in c.execute("SELECT vehicle_id FROM ev_specs")}
EVN=['Model 3','Model Y','Model S','Model X','Cybertruck','Ioniq 5','Ioniq 6','Ioniq 9','EV6','EV9','Mustang Mach-E','F-150 Lightning','ID.4','ID. Buzz','Ariya','bZ4X','Solterra','Prologue','ZDX','LYRIQ','Lyriq','Optiq','Vistiq','Hummer EV','Sierra EV','Silverado EV','Blazer EV','Equinox EV','i4','i5','iX','EQS','EQE','Air','Gravity','R1T','R1S','Taycan','e-tron GT','EX30','EX90','Leaf','Bolt','Bolt EUV','Kona Electric','Niro EV','Soul EV','GV60']
ev|={r[0] for r in c.execute("SELECT id FROM vehicles WHERE model IN (%s)"%",".join("?"*len(EVN)),EVN)}
evl=list(ev); evph=",".join("?"*len(evl))
print(f"TOTAL vehicles={q1('SELECT COUNT(*) FROM vehicles')} | EVs detected={len(ev)}")

print("\n##### SECTION 1: PRIOR FIXES #####")
print("[HIGH] EV oil_change rows (want 0):", q1(f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN ({evph})",evl))
print("[HIGH] EV parts w/ spark plug (want 0):", q1(f"SELECT COUNT(*) FROM parts WHERE vehicle_id IN ({evph}) AND (spark_plug_type IS NOT NULL OR spark_plug_qty>0)",evl))
print("[HIGH] EV drain torque_specs (want 0):", q1(f"SELECT COUNT(*) FROM torque_specs WHERE vehicle_id IN ({evph}) AND LOWER(component) LIKE '%drain%'",evl))
print("[HIGH] EV fuel rows w/ combined_mpg set (want 0):", q1(f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id IN ({evph}) AND combined_mpg IS NOT NULL",evl))
print("[HIGH] EV fuel rows w/ mpge set:", q1(f"SELECT COUNT(*) FROM fuel_economy WHERE vehicle_id IN ({evph}) AND mpge IS NOT NULL",evl))
EX=['Ferrari','Lamborghini','Rolls-Royce','Bentley','Aston Martin','McLaren']; exph=",".join("?"*len(EX))
print("[HIGH] exotic w/ non-null tire:", [tuple(r) for r in c.execute(f"SELECT v.make,p.tire_size FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE v.make IN ({exph}) AND p.tire_size IS NOT NULL AND p.tire_size<>''",EX)])
print("[HIGH] exotic w/ 215/55R17 (want 0):", q1(f"SELECT COUNT(*) FROM parts p JOIN vehicles v ON v.id=p.vehicle_id WHERE v.make IN ({exph}) AND p.tire_size='215/55R17'",EX))
print("[MED] max TSBs/vehicle (want <=200):", q1("SELECT MAX(n) FROM (SELECT COUNT(*) n FROM tsb GROUP BY vehicle_id)"))
print("[MED] vehicles >200 TSBs (want 0):", q1("SELECT COUNT(*) FROM (SELECT vehicle_id FROM tsb GROUP BY vehicle_id HAVING COUNT(*)>200)"))
print("[MED] non-EV>=2000 missing coolant:", q1(f"SELECT COUNT(*) FROM fluids f JOIN vehicles v ON v.id=f.vehicle_id WHERE v.year>=2000 AND (f.coolant_type IS NULL OR f.coolant_type='') AND f.vehicle_id NOT IN ({evph})",evl))
print("[MED] non-EV>=2000 missing brake:", q1(f"SELECT COUNT(*) FROM fluids f JOIN vehicles v ON v.id=f.vehicle_id WHERE v.year>=2000 AND (f.brake_fluid IS NULL OR f.brake_fluid='') AND f.vehicle_id NOT IN ({evph})",evl))
evbatt=[vid for vid in ev if c.execute("SELECT 1 FROM warranty WHERE vehicle_id=? AND LOWER(warranty_type) LIKE '%batter%'",(vid,)).fetchone()]
print(f"[MED] EVs with battery warranty: {len(evbatt)}/{len(ev)} (missing {len(ev)-len(evbatt)})")

print("\n##### SECTION 2: NEW DATA #####")
v2026=[r[0] for r in c.execute("SELECT id FROM vehicles WHERE year=2026")]; p2026=",".join("?"*len(v2026))
print(f"2026 vehicles: {len(v2026)}")
print("  with oil_change:", q1(f"SELECT COUNT(DISTINCT vehicle_id) FROM oil_change WHERE vehicle_id IN ({p2026})",v2026))
print("  with maintenance:", q1(f"SELECT COUNT(DISTINCT vehicle_id) FROM maintenance WHERE vehicle_id IN ({p2026})",v2026))
print("  with engine_specs:", q1(f"SELECT COUNT(DISTINCT vehicle_id) FROM engine_specs WHERE vehicle_id IN ({p2026})",v2026))
print("  2026 EVs w/ oil_change (want 0):", q1(f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN ({p2026}) AND vehicle_id IN ({evph})",v2026+evl))
print("  2026 non-EV missing oil:", [r[0] for r in c.execute(f"SELECT v.year||' '||v.make||' '||v.model FROM vehicles v WHERE v.year=2026 AND NOT EXISTS(SELECT 1 FROM oil_change o WHERE o.vehicle_id=v.id) AND v.id NOT IN ({evph})",evl)][:25])

djc={'socket_size_mm':0,'thread_size':0,'torque_nm':0,'gasket_type':0,'notes':0,'rows':0,'all4_missing_nonev':0}
honda={'rows':0,'m14':0,'s17':0,'turbo_note':0}; tls={'rows':0,'gasket_ok':0}; exotic_notes={}
for r in c.execute("SELECT o.vehicle_id vid,o.drain_bolt_json dj,v.make mk FROM oil_change o JOIN vehicles v ON v.id=o.vehicle_id"):
    try: d=json.loads(r['dj']) if r['dj'] and r['dj'] not in('','null') else {}
    except: d={}
    if not isinstance(d,dict): d={}
    djc['rows']+=1
    for k in ('socket_size_mm','thread_size','torque_nm','gasket_type','notes'):
        if d.get(k) not in (None,''): djc[k]+=1
    if all(d.get(k) in (None,'') for k in ('socket_size_mm','thread_size','torque_nm','gasket_type')) and r['vid'] not in ev: djc['all4_missing_nonev']+=1
    mk=r['mk']
    if mk in ('Honda','Acura'):
        honda['rows']+=1; th=str(d.get('thread_size') or ''); sk=str(d.get('socket_size_mm') or ''); nt=str(d.get('notes') or '').lower()
        if 'M14' in th and '1.5' in th: honda['m14']+=1
        if sk in ('17','17.0'): honda['s17']+=1
        if '1.5' in nt and ('turbo' in nt or 'alum' in nt): honda['turbo_note']+=1
    if mk in ('Toyota','Lexus','Scion'):
        tls['rows']+=1
        if d.get('gasket_type')=='14mm aluminum crush washer': tls['gasket_ok']+=1
    if mk in ('Maserati','Ferrari','McLaren','Rolls-Royce','Bentley','Lamborghini','Aston Martin'):
        exotic_notes.setdefault(mk,[]).append({'th':d.get('thread_size'),'sk':d.get('socket_size_mm'),'tq':d.get('torque_nm'),'notes':(d.get('notes') or '')[:90]})
print("\n-- DRAIN PLUG (oil_change cols):")
print("  socket col set:", q1("SELECT COUNT(*) FROM oil_change WHERE socket IS NOT NULL AND socket<>''"),
      "| thread col:", q1("SELECT COUNT(*) FROM oil_change WHERE thread IS NOT NULL AND thread<>''"),
      "| gasket col:", q1("SELECT COUNT(*) FROM oil_change WHERE gasket IS NOT NULL AND gasket<>''"))
print("  drain_bolt_json field coverage:", {k:djc[k] for k in ('rows','socket_size_mm','thread_size','torque_nm','gasket_type','notes')})
print("  non-EV oil rows missing all 4 drain fields:", djc['all4_missing_nonev'])
print("  EVs w/ drain_bolt_json non-empty (want 0):", q1(f"SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN ({evph}) AND drain_bolt_json IS NOT NULL AND drain_bolt_json NOT IN ('','{{}}','null')",evl) if evl else 0)
print("-- HONDA/ACURA:", honda)
prologue=[r[0] for r in c.execute("SELECT id FROM vehicles WHERE model='Prologue'")]
if prologue: print("  Prologue oil_change rows (want 0):", q1("SELECT COUNT(*) FROM oil_change WHERE vehicle_id IN (%s)"%",".join("?"*len(prologue)),prologue))
print("-- TOYOTA/LEXUS/SCION gasket:", tls)
print("-- EXOTIC drain notes (1 sample each):")
for mk in sorted(exotic_notes): print(f"   {mk}: {exotic_notes[mk][0]}")

print("\n##### MAINTENANCE #####")
print("vehicles with 0 maintenance:", q1("SELECT COUNT(*) FROM vehicles v WHERE NOT EXISTS(SELECT 1 FROM maintenance m WHERE m.vehicle_id=v.id)"))
print("EVs w/ oil-change maint item (want 0):", q1(f"SELECT COUNT(*) FROM maintenance WHERE vehicle_id IN ({evph}) AND (LOWER(description) LIKE '%oil change%' OR LOWER(description) LIKE '%engine oil%')",evl))
print("max maintenance items/vehicle:", q1("SELECT MAX(n) FROM (SELECT COUNT(*) n FROM maintenance GROUP BY vehicle_id)"))

print("\n##### SECTION 7: ABOUT STATS (DB truth) #####")
print("vehicles:", q1("SELECT COUNT(*) FROM vehicles"), "| makes:", q1("SELECT COUNT(DISTINCT make) FROM vehicles"),
      "| dtc:", q1("SELECT COUNT(*) FROM dtc_codes"))
print("with_recalls:", q1("SELECT COUNT(DISTINCT vehicle_id) FROM recalls"), "| with_maint:", q1("SELECT COUNT(DISTINCT vehicle_id) FROM maintenance"),
      "| years:", tuple(c.execute("SELECT MIN(year),MAX(year) FROM vehicles").fetchone()))
c.close(); print("\n[DB AUDIT COMPLETE]")
