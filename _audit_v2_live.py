import requests, time, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
S=requests.Session(); BASE="https://knowyourride.net"
def cb(): return str(time.time_ns())

print("##### SECTION 5: PERFORMANCE / PAGE #####")
r=S.get(BASE+"/?cb="+cb(), timeout=40); html=r.text
print("index HTTP:", r.status_code, "| size: %.1f KB"%(len(r.content)/1024))
import re
def has(p): return ("YES" if p in html else "NO")
ver=re.search(r'kyr-version" content="([^"]+)"', html); print("kyr-version:", ver.group(1) if ver else "?")
dref=re.search(r'/data\.[a-f0-9]+\.js', html); dref=dref.group(0) if dref else None; print("data ref:", dref)
print("GA4 G-7RE1GC9S5Q:", has("G-7RE1GC9S5Q"))
print("footer /terms.html:", has('href="/terms.html"'), "| /privacy.html:", has('href="/privacy.html"'))
print("hero:", has('id="kyr-hero"'), "| sample card:", has('id="kyr-sample"'), "| upsell banner:", has('id="kyr-save-banner"'))
print("OBD disclaimer:", has("Not available in the browser"), "| DTC disclaimer:", has("Diagnostic codes indicate possible causes"))
print("onboard text removed:", "YES" if "Search for your car above" not in html else "NO (still present)")
print("rockauto/autozone in shell:", "present" if re.search(r'rockauto|autozone', html, re.I) else "none")
md=re.search(r'<meta name="description" content="([^"]*)"', html); print("meta description:", (md.group(1)[:80] if md else "MISSING"))
ogt=re.search(r'og:title" content="([^"]*)"', html); print("og:title:", ogt.group(1)[:60] if ogt else "MISSING")
ogd=re.search(r'og:description" content="([^"]*)"', html); print("og:description:", "present" if ogd else "MISSING")
can=re.search(r'rel="canonical" href="([^"]*)"', html); print("canonical:", can.group(1) if can else "MISSING")
# data file headers
if dref:
    h=S.head(BASE+dref, timeout=60)
    print("data file:", dref, "| HTTP", h.status_code, "| Cache-Control:", h.headers.get("Cache-Control"), "| size: %.2f MB"%(int(h.headers.get("Content-Length",0))/1048576))
# 404
n=S.get(BASE+"/no-such-page-"+cb(), timeout=20); print("404 test:", n.status_code, "(branded:", ("YES" if "wrong turn" in n.text.lower() else "NO")+")")
# sitemap / robots
sm=S.get(BASE+"/sitemap.xml", timeout=20); print("sitemap.xml:", sm.status_code, "(%d bytes)"%len(sm.content))
rb=S.get(BASE+"/robots.txt", timeout=20); print("robots.txt:", rb.status_code)

print("\n##### API HEALTH (live status codes) #####")
def probe(method, path, **kw):
    try:
        r=S.request(method, BASE+path, timeout=40, **kw); return r.status_code, r
    except Exception as e: return "ERR("+str(e)[:40]+")", None
checks=[
 ("GET","/api/vin/1HGCM82633A004352?cb="+cb(),{}),
 ("GET","/api/recalls?make=Toyota&model=Camry&year=2020",{}),
 ("GET","/api/youtube?year=2020&make=Toyota&model=Camry&service=oil%20change",{}),
 ("GET","/api/guide?vehicle_id=12802&service=brakes",{}),     # safety-blocked -> 200, no Claude cost
 ("GET","/api/obd/status",{}),
 ("GET","/api/subscribe?plan=monthly",{"allow_redirects":False}),
 ("GET","/api/auth?action=me",{}),
 ("POST","/api/garage",{"json":{"action":"list"}}),           # no token -> 401 expected
 ("GET","/api/verify-subscription?email=audit-probe@example.com",{}),
 ("GET","/api/identify-part",{}),                              # POST-only -> method status
]
for m,p,kw in checks:
    code,resp=probe(m,p,**kw); note=""
    if resp is not None:
        try: j=resp.json(); note=str({k:j[k] for k in list(j)[:2]})[:70]
        except: note=resp.text[:50].replace("\n"," ")
    print(f"  {m} {p.split('?')[0]:<28} -> {code}  {note}")

print("\n##### ACTIVE SECURITY TESTS #####")
ts=cb()
# 1) signup -> me -> delete-account E2E (self-cleaning)
em=f"audit-e2e-{ts}@example.com"; pw="AuditTest!2026"
r=S.post(BASE+"/api/auth",json={"action":"signup","email":em,"password":pw},timeout=30); sj=r.json()
print("signup:",r.status_code, {k:sj.get(k) for k in("ok","tier")}, "token:",("yes" if sj.get("token") else "no"))
tok=sj.get("token")
if tok:
    me=S.post(BASE+"/api/auth",json={"action":"me","token":tok},timeout=30); print("me(token):",me.status_code, me.json())
    dl=S.post(BASE+"/api/auth",json={"action":"delete-account","token":tok},timeout=30); print("delete-account:",dl.status_code, dl.json())
    me2=S.post(BASE+"/api/auth",json={"action":"me","token":tok},timeout=30); print("me after delete (expect 401):",me2.status_code)
# 2) login throttle: 6 wrong attempts (junk email) -> 6th should be 429
print("login throttle (6 attempts on junk email):")
for i in range(1,7):
    r=S.post(BASE+"/api/auth",json={"action":"login","email":f"throttle-{ts}@example.com","password":"wrongpw"},timeout=30)
    print(f"   attempt {i}: HTTP {r.status_code}")
    time.sleep(0.3)
# 3) promo BETA2026 (throwaway token)
pr=S.post(BASE+"/api/promo",json={"code":"BETA2026","token":"audit-"+ts},timeout=30)
try: print("promo BETA2026:",pr.status_code, pr.json())
except: print("promo BETA2026:",pr.status_code, pr.text[:80])
print("\n[LIVE AUDIT COMPLETE]  (test account "+em+" was created and deleted)")
