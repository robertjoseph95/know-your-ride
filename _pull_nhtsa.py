# NHTSA backfill for the 127 never-pulled cohort (ids >=38591, never run through ANY pull).
# Endpoints: recalls, safety-ratings, complaints. LOG every pull (ok/empty) to pull_log.
# Discipline: ONLY the 127 never-pulled (never touch genuinely-empty vehicles). Gov tables not gated.
# Complaints: determinable for the 127 (never-pulled for everything); capped at 100 most-recent/vehicle.
# SKIPPED (not clean NHTSA): tsb (other source), warranty (factory), reliability (derived).
import sqlite3, urllib.request, urllib.parse, json, shutil, datetime, time

DB='wrench_vehicles.db'
bak=DB+'.bak_nhtsa_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

def getj(u, tries=2):
    for _ in range(tries):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25)
            return r.getcode(), json.loads(r.read().decode('utf-8','ignore'))
        except urllib.error.HTTPError as e: return e.code, None
        except Exception: time.sleep(0.5)
    return 0, None
Q=urllib.parse.quote
B=lambda x: 1 if (x is True or str(x).lower()=='true') else 0

db=sqlite3.connect(DB); db.row_factory=sqlite3.Row; c=db.cursor()
live=set(r[0] for r in c.execute('SELECT id FROM vehicles WHERE id>0').fetchall())
# Anchor cohort on 'recalls' (originally logged for ALL non-backfill vehicles) so the 114 EPA-MPG
# logs from last turn don't shrink it. Vehicles lacking a 'recalls' log = the 127 backfill cohort.
rec_logged=set(r[0] for r in c.execute("SELECT DISTINCT vehicle_id FROM pull_log WHERE endpoint='recalls'").fetchall())
cohort=sorted(live-rec_logged)
print('NHTSA backfill cohort (never-pulled-for-recalls):', len(cohort))
now=datetime.datetime.now().isoformat()
st={'rec_ok':0,'rec_empty':0,'rec_rows':0,'saf_ok':0,'saf_empty':0,'cmp_ok':0,'cmp_empty':0,'cmp_rows':0}

def log(vid,ep,status): c.execute("INSERT INTO pull_log (vehicle_id,endpoint,status,pulled_at) VALUES (?,?,?,?)",(vid,ep,status,now))

for i,vid in enumerate(cohort,1):
    r=c.execute('SELECT year,make,model FROM vehicles WHERE id=?',(vid,)).fetchone()
    y,mk,md=r['year'],r['make'],r['model']
    # idempotent: clear any existing rows for this cohort vehicle (no-op on first run)
    for t in ['recalls','safety_ratings','complaints']:
        c.execute('DELETE FROM %s WHERE vehicle_id=?'%t,(vid,))
    # --- RECALLS (retry no-spaces on 400/empty) ---
    rec=None
    for m in [md, md.replace(' ','')]:
        code,j=getj("https://api.nhtsa.gov/recalls/recallsByVehicle?make=%s&model=%s&modelYear=%d"%(Q(mk),Q(m),y))
        if code==200 and j is not None: rec=j;
        if rec and rec.get('Count',0)>0: break
    rows=[]
    if rec:
        for x in rec.get('results',[]):
            rows.append((vid,x.get('NHTSACampaignNumber'),x.get('Component'),(x.get('Summary') or '')[:2000],(x.get('Remedy') or '')[:2000],B(x.get('parkIt'))))
    if rows:
        c.executemany("INSERT INTO recalls (vehicle_id,campaign_number,component,summary,remedy,park_it) VALUES (?,?,?,?,?,?)",rows)
        log(vid,'recalls','ok'); st['rec_ok']+=1; st['rec_rows']+=len(rows)
    else: log(vid,'recalls','empty'); st['rec_empty']+=1
    # --- SAFETY RATINGS (2-step, first VehicleId) ---
    code,s=getj("https://api.nhtsa.gov/SafetyRatings/modelyear/%d/make/%s/model/%s"%(y,Q(mk),Q(md)))
    vids=[x.get('VehicleId') for x in (s.get('Results',[]) if s else [])]
    wrote_saf=False
    if vids:
        code,d=getj("https://api.nhtsa.gov/SafetyRatings/VehicleId/%s"%vids[0])
        res=(d.get('Results',[{}])[0] if d and d.get('Results') else {})
        def g(k):
            v=res.get(k);
            return v if v not in ('','Not Rated',None) else None
        ov=g('OverallRating')
        if ov is not None or res:
            c.execute("""INSERT OR REPLACE INTO safety_ratings (vehicle_id,overall_rating,frontal_crash_driver,frontal_crash_passenger,
                side_crash_driver,side_crash_passenger,rollover_rating,rollover_risk_pct,side_pole_rating)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (vid,ov,g('FrontCrashDriversideRating'),g('FrontCrashPassengersideRating'),
                 g('SideCrashDriversideRating'),g('SideCrashPassengersideRating'),g('RolloverRating'),
                 res.get('RolloverPossibility'),g('SidePoleCrashRating') or g('combinedSideBarrierAndPoleRating-Front')))
            log(vid,'safety-ratings','ok'); st['saf_ok']+=1; wrote_saf=True
    if not wrote_saf: log(vid,'safety-ratings','empty'); st['saf_empty']+=1
    # --- COMPLAINTS (lowercase keys; cap 100 most-recent) ---
    cmp=None
    for m in [md, md.replace(' ','')]:
        code,j=getj("https://api.nhtsa.gov/complaints/complaintsByVehicle?make=%s&model=%s&modelYear=%d"%(Q(mk),Q(m),y))
        if code==200 and j is not None: cmp=j
        if cmp and cmp.get('count',0)>0: break
    crows=[]
    if cmp and cmp.get('results'):
        results=sorted(cmp['results'], key=lambda x: x.get('odiNumber',0), reverse=True)[:100]
        for x in results:
            crows.append((vid,str(x.get('odiNumber')),x.get('components'),(x.get('summary') or '')[:2000],
                          x.get('dateOfIncident'),B(x.get('crash')),B(x.get('fire')),
                          x.get('numberOfInjuries') or 0,x.get('numberOfDeaths') or 0))
    if crows:
        c.executemany("INSERT INTO complaints (vehicle_id,complaint_number,component,summary,incident_date,crash,fire,injury,deaths) VALUES (?,?,?,?,?,?,?,?,?)",crows)
        log(vid,'complaints','ok'); st['cmp_ok']+=1; st['cmp_rows']+=len(crows)
    else: log(vid,'complaints','empty'); st['cmp_empty']+=1

    if i%15==0:
        db.commit(); print('  %d/%d | rec ok=%d/empty=%d | saf ok=%d/empty=%d | cmp ok=%d/empty=%d'%(
            i,len(cohort),st['rec_ok'],st['rec_empty'],st['saf_ok'],st['saf_empty'],st['cmp_ok'],st['cmp_empty']))

db.commit()
print('\nDONE.')
print('  recalls:  ok=%d empty=%d (%d rows)'%(st['rec_ok'],st['rec_empty'],st['rec_rows']))
print('  safety:   ok=%d empty=%d'%(st['saf_ok'],st['saf_empty']))
print('  complaints: ok=%d empty=%d (%d rows, capped 100/veh)'%(st['cmp_ok'],st['cmp_empty'],st['cmp_rows']))
print('  All %d cohort vehicles logged for recalls/safety-ratings/complaints.'%len(cohort))
db.close()
