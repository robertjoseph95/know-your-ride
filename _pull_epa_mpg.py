# EPA MPG backfill for the never-pulled-and-lacking-MPG cohort (the ~114 backfill vehicles).
# Pull fueleconomy.gov -> multi-row insert into fuel_economy -> LOG pull-fuel-economy to pull_log.
# Distinguish: 'ok' (got data), 'empty' (EPA has none / no model match). Do NOT write empty rows.
import sqlite3, urllib.request, urllib.parse, re, shutil, datetime, time

DB='wrench_vehicles.db'
bak=DB+'.bak_epampg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(DB,bak); print('Backup ->',bak)

def get(u, tries=2):
    for _ in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read().decode('utf-8','ignore')
        except: time.sleep(0.5)
    return ''
def tag(x,t):
    m=re.search('<%s>(.*?)</%s>'%(t,t), x); return m.group(1) if m else None
def norm(s): return re.sub(r'[^a-z0-9]','', (s or '').lower())

db=sqlite3.connect(DB); db.row_factory=sqlite3.Row; c=db.cursor()
live=set(r[0] for r in c.execute('SELECT id FROM vehicles WHERE id>0').fetchall())
logged=set(r[0] for r in c.execute('SELECT DISTINCT vehicle_id FROM pull_log').fetchall())
have_mpg=set(r[0] for r in c.execute('SELECT DISTINCT vehicle_id FROM fuel_economy').fetchall())
targets=[v for v in sorted(live-logged) if v not in have_mpg]
print('EPA MPG targets (never-pulled & lacking MPG):', len(targets))

EPA="https://www.fueleconomy.gov/ws/rest/vehicle"
stat={'ok':0,'empty':0,'rows':0}
now=datetime.datetime.now().isoformat()
for vid in targets:
    r=c.execute('SELECT year,make,model FROM vehicles WHERE id=?',(vid,)).fetchone()
    y,mk,md=r['year'],r['make'],r['model']
    mx=get("%s/menu/model?year=%d&make=%s"%(EPA,y,urllib.parse.quote(mk)))
    models=re.findall(r'<text>(.*?)</text>', mx)
    dn=norm(md); first=re.split(r'[^A-Za-z]', md)[0].lower()
    matches=[m for m in models if dn and (dn in norm(m) or norm(m) in dn or (first and norm(m).startswith(norm(first)) and len(first)>2))]
    seen=set(); rows=[]
    for mdl in matches:
        ox=get("%s/menu/options?year=%d&make=%s&model=%s"%(EPA,y,urllib.parse.quote(mk),urllib.parse.quote(mdl)))
        for eid in re.findall(r'<value>(\d+)</value>', ox):
            if eid in seen: continue
            seen.add(eid)
            v=get("%s/%s"%(EPA,eid))
            if not v: continue
            def num(t):
                x=tag(v,t)
                try: return int(float(x)) if x not in (None,'') else None
                except: return None
            city=num('city08'); hwy=num('highway08'); comb=num('comb08')
            cE=num('cityE'); hE=num('highwayE'); combE=num('combE')
            if city is None and comb is None and combE is None: continue
            rows.append((vid,city,hwy,comb,num('fuelCost08'),tag(v,'displ'),
                         (tag(v,'trany') or None),(tag(v,'drive') or None),(tag(v,'fuelType') or None),
                         num('range'),num('phevComb') or combE, cE,hE,combE))
    # dedupe identical trims
    uniq=[]; seenrow=set()
    for rw in rows:
        k=(rw[1],rw[2],rw[3],rw[5],rw[7])  # city,hwy,comb,displ,drive
        if k in seenrow: continue
        seenrow.add(k); uniq.append(rw)
    if uniq:
        c.executemany("""INSERT INTO fuel_economy (vehicle_id,city_mpg,highway_mpg,combined_mpg,annual_fuel_cost,
            engine,transmission,drive,fuel_type,range_miles,mpge,city_ev,hwy_ev,comb_ev)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", uniq)
        c.execute("INSERT INTO pull_log (vehicle_id,endpoint,status,pulled_at) VALUES (?,?,?,?)",(vid,'fuel-economy','ok',now))
        stat['ok']+=1; stat['rows']+=len(uniq)
    else:
        c.execute("INSERT INTO pull_log (vehicle_id,endpoint,status,pulled_at) VALUES (?,?,?,?)",(vid,'fuel-economy','empty',now))
        stat['empty']+=1
    if (stat['ok']+stat['empty'])%20==0:
        db.commit(); print('  progress: %d/%d  (ok=%d empty=%d rows=%d)'%(stat['ok']+stat['empty'],len(targets),stat['ok'],stat['empty'],stat['rows']))

db.commit()
print('\nDONE. ok=%d (got MPG) | empty=%d (EPA none/no-match) | %d fuel_economy rows inserted'%(stat['ok'],stat['empty'],stat['rows']))
print('All %d logged to pull_log (endpoint=fuel-economy) - no longer "never-pulled".'%len(targets))
db.close()
