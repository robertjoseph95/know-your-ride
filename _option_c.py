"""Option C: replace auto-modal demo with a compact static preview card. Edits base wrench_demo.html."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
F = "wrench_demo.html"
b = open(F, "rb").read()

def rep(old, new, label):
    global b
    c = b.count(old)
    assert c == 1, f"[{label}] expected 1, found {c}: {old[:70]!r}"
    b = b.replace(old, new); print("OK", label)

# A. Remove the in-modal demo banner element (revert to plain m-top)
rep(b'    <div id="m-demo-banner" style="display:none;margin:0 0 6px;padding:9px 12px;background:#3a2e00;'
    b'border:1px solid #e0a23b;border-radius:8px;color:#ffd97a;font-size:12.5px;line-height:1.45"></div>\r\n'
    b'    <div class="m-top">',
    b'    <div class="m-top">', "remove demo banner el")

# B. openModal: drop the demo arg + KYR_DEMO_ID const
rep(b'var KYR_DEMO_ID=12802;\r\nfunction openModal(vid,demo){', b'function openModal(vid){', "openModal sig")

# C. openModal body: drop banner logic; keep sessionStorage; hide the sample card
rep(b"document.getElementById('m-title').innerHTML=v.year+' '+v.make+' <em>'+v.model+'</em>';"
    b"var __b=document.getElementById('m-demo-banner');if(demo){if(__b){__b.innerHTML='&#128203; Demo &mdash; showing 2020 Toyota Camry &middot; Search your car above to load your specs';__b.style.display='block';}}else{if(__b)__b.style.display='none';try{sessionStorage.setItem('kyr_last_vehicle',vid);}catch(e){}}",
    b"document.getElementById('m-title').innerHTML=v.year+' '+v.make+' <em>'+v.model+'</em>';"
    b"try{sessionStorage.setItem('kyr_last_vehicle',vid);}catch(e){}"
    b"var __sc=document.getElementById('kyr-sample');if(__sc)__sc.style.display='none';", "openModal body")

# D. Remove kyrAutoLoad function entirely
rep(b"function kyrAutoLoad(){var last=null;try{last=sessionStorage.getItem('kyr_last_vehicle');}catch(e){}"
    b"if(last&&VEH[last]){openModal(last,false);}else if(VEH[KYR_DEMO_ID]){openModal(KYR_DEMO_ID,true);}}\r\n"
    b"function closeModal(){", b"function closeModal(){", "remove kyrAutoLoad")

# E. DOMContentLoaded: no auto-demo; restore last vehicle for returning visitors only
rep(b"  lookupCode();\r\n  kyrAutoLoad();\r\n});",
    b"  lookupCode();\r\n  try{var __lv=sessionStorage.getItem('kyr_last_vehicle');if(__lv&&VEH[__lv])openModal(__lv);}catch(e){}\r\n});",
    "DOMContentLoaded restore")

# F. Insert the compact sample preview card (below search, above grid/onboard)
CARD = (
    '<div id="kyr-sample" style="max-width:880px;margin:0 0 16px;background:var(--panel);border:1px solid var(--border);'
    'border-left:3px solid var(--accent);border-radius:10px;padding:13px 16px">'
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px">'
    '<div style="font-weight:700;font-size:15px;color:var(--text)">2020 Toyota Camry</div>'
    '<div style="font-family:\'JetBrains Mono\',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;'
    'color:var(--faint);background:var(--p2,#1c1c1c);border:1px solid var(--border);padding:3px 9px;border-radius:100px">Sample Data</div></div>'
    '<div style="display:flex;gap:12px;margin-bottom:13px">'
    '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700;color:var(--text)">&#128738; 0W-20 Full Synthetic</div>'
    '<div style="font-size:11px;color:var(--faint);margin-top:2px">Oil Type</div></div>'
    '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700;color:var(--text)">&#128295; 14mm &middot; M12x1.25</div>'
    '<div style="font-size:11px;color:var(--faint);margin-top:2px">Drain Plug</div></div>'
    '<div style="flex:1;min-width:0"><div style="font-size:13.5px;font-weight:700;color:var(--text)">&#9888;&#65039; 0 Open Recalls</div>'
    '<div style="font-size:11px;color:var(--faint);margin-top:2px">Recall Status</div></div></div>'
    '<button onclick="openModal(12802)" style="width:100%;background:var(--accent);color:#000;border:none;border-radius:8px;'
    'padding:11px;font-weight:700;font-size:13px;cursor:pointer">See Full Specs for This Car &#8594;</button></div>'
).encode()
rep(b'<div id="g-onboard"', CARD + b'\r\n  <div id="g-onboard"', "insert sample card")

open(F, "wb").write(b)
print("\n[Option C applied to wrench_demo.html]")
