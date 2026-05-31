"""Landing-page fixes (Problem 1: About stats; Problem 2: hero + demo Camry). Edits base wrench_demo.html."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
F = "wrench_demo.html"
b = open(F, "rb").read()

def rep(old, new, n=1, label=""):
    global b
    c = b.count(old)
    assert c == n, f"[{label}] expected {n} occurrence(s), found {c}: {old[:60]!r}"
    b = b.replace(old, new)
    print(f"OK  {label}")

# ===================== PROBLEM 1: About-section stats =====================
rep(b'<div class="astat-n">1,669</div><div class="astat-l">Vehicles</div>',
    b'<div class="astat-n">3,540</div><div class="astat-l">Vehicles</div>', label="P1 vehicles")
rep(b'<div class="astat-n">47</div><div class="astat-l">Makes</div>',
    b'<div class="astat-n">48</div><div class="astat-l">Makes</div>', label="P1 makes")
rep(b'<div class="astat-n">5,022</div><div class="astat-l">DTC Codes</div>',
    b'<div class="astat-n">12,196</div><div class="astat-l">DTC Codes</div>', label="P1 dtc")
rep(b'<div class="astat-n">971</div><div class="astat-l">With Recalls</div>',
    b'<div class="astat-n">1,557</div><div class="astat-l">With Recalls</div>', label="P1 recalls")
rep(b'<div class="astat-n">171</div><div class="astat-l">With Schedules</div>',
    b'<div class="astat-n">1,668</div><div class="astat-l">With Schedules</div>', label="P1 schedules")
rep(b'971 vehicles with active NHTSA recall data',
    b'1,557 vehicles with active NHTSA recall data', label="P1 feat-recall")
rep(b'464 OBD-II codes searchable',
    b'12,196 OBD-II codes searchable', label="P1 feat-dtc")
rep(b'<h3>39 MAKES - 23 YEARS</h3><p>2003-2025 coverage',
    b'<h3>48 MAKES &middot; 45 YEARS</h3><p>1981-2026 coverage', label="P1 feat-header")

# ===================== PROBLEM 2a: hero (static, pure HTML/CSS) =====================
CHIP = ("font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accent);"
        "background:rgba(255,107,0,.1);border:1px solid rgba(255,107,0,.25);padding:5px 12px;border-radius:100px")
HERO = (
    '<div id="kyr-hero" style="max-height:160px;overflow:hidden;text-align:center;padding:18px 16px 6px">'
    '<div style="font-family:\'Anton\',sans-serif;font-size:36px;letter-spacing:.04em;line-height:1.05;'
    'background:linear-gradient(180deg,#fff 0%,#aaa 100%);-webkit-background-clip:text;background-clip:text;'
    '-webkit-text-fill-color:transparent">KNOW YOUR RIDE</div>'
    '<div style="font-family:\'Manrope\',sans-serif;font-size:14px;color:var(--dim);max-width:580px;'
    'margin:7px auto 0;line-height:1.5">Exact specs for your car &mdash; oil type, drain plug size, '
    'maintenance schedules, and recall alerts.</div>'
    '<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px">'
    f'<span style="{CHIP}">3,540 Vehicles</span>'
    f'<span style="{CHIP}">12,196 DTC Codes</span>'
    f'<span style="{CHIP}">Free Forever</span>'
    '</div></div>'
).encode()
rep(b'<div class="pane active" id="pane-garage">',
    b'<div class="pane active" id="pane-garage">\r\n  ' + HERO, label="P2 hero")

# ===================== PROBLEM 2b: demo banner element in modal (above header) =====================
rep(b'    <div class="m-top">',
    b'    <div id="m-demo-banner" style="display:none;margin:0 0 6px;padding:9px 12px;background:#3a2e00;'
    b'border:1px solid #e0a23b;border-radius:8px;color:#ffd97a;font-size:12.5px;line-height:1.45"></div>\r\n'
    b'    <div class="m-top">', label="P2 banner-el")

# ===================== PROBLEM 2c: JS — openModal demo arg + banner/session, autoload =====================
rep(b'function openModal(vid){', b'var KYR_DEMO_ID=12802;\r\nfunction openModal(vid,demo){', label="P2 openModal-sig")
rep(b"document.getElementById('m-title').innerHTML=v.year+' '+v.make+' <em>'+v.model+'</em>';",
    b"document.getElementById('m-title').innerHTML=v.year+' '+v.make+' <em>'+v.model+'</em>';"
    b"var __b=document.getElementById('m-demo-banner');"
    b"if(demo){if(__b){__b.innerHTML='&#128203; Demo &mdash; showing 2020 Toyota Camry &middot; Search your car above to load your specs';__b.style.display='block';}}"
    b"else{if(__b)__b.style.display='none';try{sessionStorage.setItem('kyr_last_vehicle',vid);}catch(e){}}",
    label="P2 openModal-body")
rep(b'function closeModal(){',
    b'function kyrAutoLoad(){var last=null;try{last=sessionStorage.getItem(\'kyr_last_vehicle\');}catch(e){}'
    b'if(last&&VEH[last]){openModal(last,false);}else if(VEH[KYR_DEMO_ID]){openModal(KYR_DEMO_ID,true);}}\r\n'
    b'function closeModal(){', label="P2 autoload-fn")
rep(b'  lookupCode();\r\n});', b'  lookupCode();\r\n  kyrAutoLoad();\r\n});', label="P2 autoload-call")

open(F, "wb").write(b)
print("\n[landing fixes applied to wrench_demo.html]")
