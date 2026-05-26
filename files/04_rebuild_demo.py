"""
WRENCH — Script 04 (rewrite): Rebuild wrench_demo.html
======================================================
Replaces the original 04_rebuild_html.py, which had three problems:
  1. It embedded EVERY complaint into the HTML (~190 MB) while the demo's
     JS has no UI to render them -> huge, unopenable file, zero new features.
  2. It never loaded the maintenance / maintenance_parts tables, so it would
     have wiped the demo's existing Maintenance tab + "SCHEDULES" badge.
  3. Its TSB badge would read 0 (all 207k TSB titles are NULL).

This version:
  * Rebuilds the embedded __D__ data from the (now enriched) DB so the new
    engine strings (script 01) and MPG / EV-range (script 02) show up.
  * Preserves maintenance + maintenance_parts.
  * Embeds a CAPPED set of complaints per vehicle (CAP, most-recent) and
    injects a real "Complaints" modal tab (mirrors the recalls renderer,
    reusing existing CSS) so script 03's data is actually visible.
  * Keeps the file ~latin-1 (the demo is cp1252, NOT utf-8) and escapes
    "</" in the JSON so a complaint containing "</script>" can't break out.
  * Idempotent: re-runs refresh data+badge; the JS tab is injected once.

Run: python 04_rebuild_demo.py
"""

import sqlite3
import json
import os
import re
import shutil
import datetime

HERE     = os.path.dirname(os.path.abspath(__file__))
ROOT     = os.path.dirname(HERE)                       # "Wrench App Data"
DB_PATH  = os.path.join(ROOT, "wrench_vehicles.db")
OUT_FILE = os.path.join(ROOT, "wrench_demo.html")
CAP      = 15                                          # complaints embedded per vehicle
SENTINEL = "/*WRENCH_COMPLAINTS_TAB*/"


def pj(val):
    if not val or val in ("null", "[]"):
        return None
    try:
        r = json.loads(val)
        # affiliate_url is kept (the tiered-parts feature surfaces it as a Shop link)
        return r if r else None
    except Exception:
        return None


def date_key(s):
    """MM/DD/YYYY -> (Y, M, D) for sorting; bad/empty -> zeros."""
    try:
        m, d, y = s.split("/")
        return (int(y), int(m), int(d))
    except Exception:
        return (0, 0, 0)


def build_data(cur):
    cur.execute("SELECT id,year,make,model,engine,trim FROM vehicles ORDER BY make,year,model")
    veh = {}
    for v in cur.fetchall():
        veh[v["id"]] = {"id": v["id"], "year": v["year"], "make": v["make"],
                        "model": v["model"], "engine": v["engine"], "trim": v["trim"]}

    def each(table, fn):
        cur.execute(f"SELECT * FROM {table}")
        for r in cur.fetchall():
            if r["vehicle_id"] in veh:
                fn(veh[r["vehicle_id"]], r)

    each("oil_change", lambda d, r: d.update(oil={
        "visc": r["viscosity"], "type": r["oil_type"], "cap_w": r["capacity_with_filter"],
        "cap_wo": r["capacity_without_filter"], "spec": r["oem_spec"],
        "filters": pj(r["filters_json"]), "drain": pj(r["drain_bolt_json"])}))

    each("parts", lambda d, r: d.update(parts={
        "plug_type": r["spark_plug_type"], "plug_gap": r["spark_plug_gap"],
        "plug_qty": r["spark_plug_qty"], "batt_group": r["battery_group"],
        "batt_cca": r["battery_cca"], "tire": r["tire_size"],
        "psi_f": r["tire_pressure_front"], "psi_r": r["tire_pressure_rear"],
        "plugs": pj(r["spark_plugs_json"]), "air": pj(r["air_filters_json"]),
        "cabin": pj(r["cabin_filters_json"]), "wipers": pj(r["wiper_blades_json"]),
        "batts": pj(r["batteries_json"])}))

    each("fluids", lambda d, r: d.update(fluids={
        "trans": r["transmission_fluid"], "trans_cap": r["transmission_capacity"],
        "brake": r["brake_fluid"], "coolant": r["coolant_type"],
        "coolant_cap": r["coolant_capacity"], "ps": r["power_steering_fluid"],
        "diff": pj(r["differential_fluids_json"])}))

    each("torque_specs", lambda d, r: d.setdefault("torque", []).append(
        {"comp": r["component"], "ft": r["torque_ft_lbs"], "nm": r["torque_nm"], "notes": r["notes"]}))

    each("recalls", lambda d, r: d.setdefault("recalls", []).append(
        {"camp": r["campaign_number"], "comp": r["component"], "sum": r["summary"],
         "remedy": r["remedy"], "park": bool(r["park_it"])}))

    each("engine_specs", lambda d, r: d.setdefault("engines", []).append(
        {"var": r["variant"], "hp": r["horsepower"], "tq": r["torque_ft_lbs"],
         "disp": r["displacement_l"], "cyl": r["cylinders"], "config": r["cylinder_config"],
         "asp": r["aspiration"], "fuel": r["fuel_system"]}))

    # fuel economy (range_miles/mpge added by script 02)
    cur.execute("PRAGMA table_info(fuel_economy)")
    fe_cols = [c[1] for c in cur.fetchall()]
    cur.execute("SELECT * FROM fuel_economy")
    for r in cur.fetchall():
        if r["vehicle_id"] not in veh:
            continue
        e = {"city": r["city_mpg"], "hwy": r["highway_mpg"], "comb": r["combined_mpg"],
             "cost": r["annual_fuel_cost"], "eng": r["engine"], "trans": r["transmission"],
             "drive": r["drive"]}
        if "range_miles" in fe_cols:
            e["range"] = r["range_miles"]
        if "mpge" in fe_cols:
            e["mpge"] = r["mpge"]
        veh[r["vehicle_id"]].setdefault("mpg", []).append(e)

    each("safety_ratings", lambda d, r: d.update(safety={
        "overall": r["overall_rating"], "front_d": r["frontal_crash_driver"],
        "front_p": r["frontal_crash_passenger"], "side_d": r["side_crash_driver"],
        "side_p": r["side_crash_passenger"], "rollover": r["rollover_rating"],
        "roll_pct": r["rollover_risk_pct"], "pole": r["side_pole_rating"]}))

    each("warranty", lambda d, r: d.setdefault("warranty", {}).__setitem__(
        r["warranty_type"], {"mo": r["months"], "mi": r["miles"], "notes": r["notes"]}))

    each("reliability", lambda d, r: d.update(rel={
        "score": r["overall_score"], "rating": r["rating"], "complaints": r["complaint_count"],
        "crashes": r["crash_count"], "fires": r["fire_count"], "injuries": r["injury_count"],
        "issue": r["top_issue"]}))

    cur.execute("SELECT vehicle_id,service_type,cost_low,cost_high,cost_average,labor_hours_low,labor_hours_high FROM service_costs WHERE region='national'")
    for r in cur.fetchall():
        if r["vehicle_id"] in veh:
            veh[r["vehicle_id"]].setdefault("costs", {})[r["service_type"]] = {
                "lo": r["cost_low"], "hi": r["cost_high"], "avg": r["cost_average"],
                "hr_lo": r["labor_hours_low"], "hr_hi": r["labor_hours_high"]}

    # maintenance + parts (the original 04 dropped these)
    each("maintenance", lambda d, r: d.setdefault("maint", []).append(
        {"id": r["id"], "mi": r["mileage_interval"], "mo": r["months_interval"],
         "desc": r["description"], "src": r["source"], "notes": r["notes"]}))
    each("maintenance_parts", lambda d, r: d.setdefault("maint_parts", []).append(
        {"mid": r["maintenance_id"], "type": r["part_type"], "brand": r["brand"],
         "pn": r["part_number"], "desc": r["description"], "qty": r["qty"]}))

    # complaints: cap to CAP most-recent per vehicle, keep total count
    with_comps = 0
    if cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'").fetchone():
        raw = {}
        cur.execute("SELECT vehicle_id,complaint_number,component,summary,incident_date,crash,fire,injury,deaths FROM complaints")
        for r in cur.fetchall():
            if r["vehicle_id"] in veh:
                raw.setdefault(r["vehicle_id"], []).append(r)
        for vid, rows in raw.items():
            rows.sort(key=lambda r: date_key(r["incident_date"]), reverse=True)
            veh[vid]["comp_n"] = len(rows)
            veh[vid]["comps"] = [{
                "num": r["complaint_number"], "comp": r["component"], "sum": r["summary"],
                "date": r["incident_date"], "crash": r["crash"], "fire": r["fire"],
                "inj": r["injury"], "deaths": r["deaths"]} for r in rows[:CAP]]
            with_comps += 1

    cur.execute("SELECT code,description FROM dtc_codes ORDER BY code")
    dtc = {r["code"]: r["description"] for r in cur.fetchall()}

    # CarMD-style fix probabilities: ranked fixes per code (probability %, avg cost, severity)
    fixes = {}
    if cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dtc_fix_rates'").fetchone():
        cur.execute("SELECT code,fix_description,probability_pct,avg_cost_usd,severity FROM dtc_fix_rates ORDER BY code,rank")
        for r in cur.fetchall():
            fixes.setdefault(r["code"], []).append({
                "fix": r["fix_description"], "prob": r["probability_pct"],
                "cost": r["avg_cost_usd"], "sev": r["severity"]})

    return list(veh.values()), dtc, fixes, with_comps


# ── JS injected for the Complaints tab (reuses existing CSS classes) ──────────
RENDER_FN = SENTINEL + """
function renderComplaints(v){
  var c=v.comps||[];
  if(!c.length)return '<p class="empty-note">No NHTSA complaints on record.</p>';
  var hdr='NHTSA Complaints'+(v.comp_n?' ('+v.comp_n+' total'+(v.comp_n>c.length?', '+c.length+' most recent shown':'')+')':'');
  var h='<div class="sec-head">'+hdr+'</div>';
  h+=c.map(function(x){
    var f='';
    if(x.crash)f+='<span class="bdg bdg-r">CRASH</span> ';
    if(x.fire)f+='<span class="bdg bdg-r">FIRE</span> ';
    if(x.inj)f+='<span class="bdg bdg-r">'+x.inj+' INJ</span> ';
    if(x.deaths)f+='<span class="bdg bdg-r">'+x.deaths+' DEATH</span> ';
    return '<div class="recall-card'+((x.crash||x.fire||x.deaths)?' park':'')+'">'
      +(x.comp?'<div class="rc-comp">'+x.comp+'</div>':'')
      +'<div class="rc-camp">'+(x.date||'')+(x.num?' &middot; #'+x.num:'')+'</div>'
      +(f?'<div style="margin:6px 0">'+f+'</div>':'')
      +(x.sum?'<div class="rc-text">'+x.sum+'</div>':'')
      +'</div>';
  }).join('');
  return h;
}
"""


def inject_tab(html):
    """Add the Complaints tab to the demo JS (idempotent)."""
    if SENTINEL in html:
        return html
    html = html.replace("function switchTab(name){", RENDER_FN + "\nfunction switchTab(name){", 1)
    html = html.replace(
        "var MTABS=['oil','parts','fluids','maint','perf','safety','warranty'];",
        "var MTABS=['oil','parts','fluids','maint','perf','safety','warranty','comps'];", 1)
    html = html.replace(
        "var MLABELS=['Oil / Drain','Parts','Fluids & Torque','Maintenance','Perf & MPG','Safety & Rel.','Warranty & Recalls'];",
        "var MLABELS=['Oil / Drain','Parts','Fluids & Torque','Maintenance','Perf & MPG','Safety & Rel.','Warranty & Recalls','Complaints'];", 1)
    html = html.replace(
        "var fns={oil:renderOil,parts:renderParts,fluids:renderFluids,maint:renderMaint,perf:renderPerf,safety:renderSafety,warranty:renderWarranty};",
        "var fns={oil:renderOil,parts:renderParts,fluids:renderFluids,maint:renderMaint,perf:renderPerf,safety:renderSafety,warranty:renderWarranty,comps:renderComplaints};", 1)
    return html


# ── VIN decode UI (calls the same-origin proxy in wrench_serve.py) ────────────
VIN_STYLE = """<style>
.vin-bar{margin-bottom:14px;padding:14px;background:var(--panel);border:1px solid var(--border);border-radius:10px}
.vin-label{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--faint);margin-bottom:8px}
.vin-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
#vin-input{flex:1;min-width:240px;background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:11px 13px;font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase}
#vin-input:focus{outline:none;border-color:var(--accent)}
#vin-btn{background:var(--accent);color:#000;border:none;border-radius:8px;padding:11px 18px;font-weight:700;font-size:12px;letter-spacing:.08em;cursor:pointer;text-transform:uppercase}
#vin-btn:hover{opacity:.88}
.vin-result{margin-top:10px;font-size:13px;line-height:1.5;color:var(--dim)}
.vin-result.err{color:var(--red)}
.vin-result.warn{color:var(--text)}
.vin-result.ok{color:var(--green)}
.vin-result code{background:var(--p2,#111);padding:2px 6px;border-radius:4px;font-size:11px}
</style>
"""

VIN_BAR = """<div class="vin-bar">
  <div class="vin-label">// Decode by VIN</div>
  <div class="vin-row">
    <input type="text" id="vin-input" maxlength="17" placeholder="Enter 17-character VIN…" autocomplete="off" spellcheck="false" onkeydown="if(event.key==='Enter')decodeVIN()">
    <button id="vin-btn" onclick="decodeVIN()">Decode VIN</button>
  </div>
  <div id="vin-result" class="vin-result"></div>
</div>
"""

VIN_JS = r"""/*WRENCH_VIN*/
function titleCase(s){return String(s||'').toLowerCase().replace(/\b\w/g,function(c){return c.toUpperCase();});}
function decodeVIN(){
  var el=document.getElementById('vin-input'), out=document.getElementById('vin-result');
  var vin=(el.value||'').trim().toUpperCase();
  if(vin.length!==17){out.className='vin-result err';out.innerHTML='VIN must be exactly 17 characters (got '+vin.length+').';return;}
  out.className='vin-result';out.innerHTML='Decoding '+vin+'…';
  fetch('/api/vin/'+encodeURIComponent(vin)).then(function(r){
    if(!r.ok)throw new Error('HTTP '+r.status);return r.json();
  }).then(function(d){
    if(!d||!d.make){out.className='vin-result err';out.innerHTML='No decode result for that VIN.';return;}
    var disp=titleCase(d.make)+' '+d.model;
    var match=DB.v.find(function(v){return v.year==d.year && v.make.toLowerCase()===String(d.make||'').toLowerCase() && v.model.toLowerCase()===String(d.model||'').toLowerCase();});
    if(match){out.className='vin-result ok';out.innerHTML='✓ '+d.year+' '+disp+' — opening full specs…';openModal(match.id);}
    else{
      var eng=(d.displacement_liters?d.displacement_liters+'L ':'')+(d.engine||'')+(d.cylinders?' · '+d.cylinders+'-cyl':'')+(d.fuel_type?' · '+d.fuel_type:'');
      out.className='vin-result warn';
      out.innerHTML='Decoded: <strong>'+d.year+' '+disp+(d.trim?' '+d.trim:'')+'</strong>'+(eng.trim()?'<br><span style="color:var(--dim)">'+eng+'</span>':'')+'<br>Not in our database yet — <em>full specs coming soon.</em>';
    }
  }).catch(function(e){
    out.className='vin-result err';
    out.innerHTML='Could not reach the decode service. VIN decode needs the local server — run <code>python wrench_serve.py</code> and open <code>http://localhost:8000/</code>.';
  });
}
"""


def inject_vin(html):
    """Add the VIN decode bar above the garage dropdowns (idempotent)."""
    if "/*WRENCH_VIN*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", VIN_STYLE + "</head>", 1)
    html = html.replace('<div class="g-controls">', VIN_BAR + '<div class="g-controls">', 1)
    html = html.replace("function switchTab(name){", VIN_JS + "\nfunction switchTab(name){", 1)
    return html


# ── OBD-II live diagnostics panel (talks to /api/obd/* in wrench_serve.py) ────
OBD_STYLE = """<style>
.obd-panel{margin-bottom:14px;background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.obd-head{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;cursor:pointer;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--text);user-select:none}
.obd-head:hover{background:var(--p2,#111)}
.obd-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--red);margin-right:8px;vertical-align:middle;transition:.2s}
.obd-dot.on{background:var(--green);box-shadow:0 0 8px var(--green)}
.obd-caret{transition:transform .2s;color:var(--faint)}
.obd-caret.open{transform:rotate(90deg)}
.obd-body{padding:0 14px 14px}
.obd-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
#obd-connect-btn{background:var(--accent);color:#000;border:none;border-radius:8px;padding:9px 16px;font-weight:700;font-size:12px;cursor:pointer;text-transform:uppercase}
#obd-connect-btn:hover{opacity:.88}
.obd-btn2{background:transparent;color:var(--dim);border:1px solid var(--border);border-radius:8px;padding:9px 14px;font-size:12px;cursor:pointer}
.obd-btn2:hover{color:var(--text);border-color:var(--accent)}
.obd-status{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--faint);margin-left:4px}
.obd-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(108px,1fr));gap:8px}
.obd-metric{background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;padding:10px}
.obd-m-val{font-size:20px;font-weight:700;color:var(--accent);font-family:'JetBrains Mono',monospace}
.obd-m-unit{font-size:11px;color:var(--faint)}
.obd-m-lbl{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin-top:4px}
.obd-msg{margin-top:10px;font-size:12px;color:var(--dim);line-height:1.5}
.obd-msg.err{color:var(--red)} .obd-msg.ok{color:var(--green)}
.obd-msg code{background:var(--p2,#111);padding:2px 6px;border-radius:4px}
.obd-dtc{margin-top:8px;border:1px solid var(--border);border-left:3px solid var(--red);border-radius:8px;padding:10px;background:var(--p2,#111)}
.obd-dtc .c{font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--red)}
.obd-urg{display:inline-block;font-size:9px;padding:2px 7px;border-radius:4px;text-transform:uppercase;letter-spacing:.08em;margin-left:8px;font-weight:700}
</style>
"""

OBD_PANEL = """<div class="obd-panel">
  <div class="obd-head" onclick="obdToggle()">
    <span><span class="obd-dot" id="obd-dot"></span>OBD-II Live Diagnostics</span>
    <span class="obd-caret" id="obd-caret">&#9656;</span>
  </div>
  <div class="obd-body" id="obd-body" style="display:none">
    <div class="obd-actions">
      <button id="obd-connect-btn" onclick="obdConnect()">Connect OBD-II</button>
      <button class="obd-btn2" onclick="obdReadDTCs()">Read Codes</button>
      <button class="obd-btn2" onclick="obdClear()">Clear Codes</button>
      <span class="obd-status" id="obd-status">Not connected</span>
    </div>
    <div class="obd-grid" id="obd-live"></div>
    <div id="obd-dtcs"></div>
    <div id="obd-msg" class="obd-msg"></div>
  </div>
</div>
"""

OBD_JS = """/*WRENCH_OBD*/
var __obdTimer=null;
function obdToggle(){
  var b=document.getElementById('obd-body'),c=document.getElementById('obd-caret');
  var open=b.style.display==='none';
  b.style.display=open?'block':'none';c.classList.toggle('open',open);
  if(!open&&__obdTimer){clearInterval(__obdTimer);__obdTimer=null;}
}
function obdMsg(html,cls){var m=document.getElementById('obd-msg');m.className='obd-msg'+(cls?' '+cls:'');m.innerHTML=html||'';}
function obdDown(){obdMsg('Local server not reachable. Start it with <code>python wrench_serve.py</code> and open <code>http://localhost:8000/</code> (OBD-II only works through the local server).','err');if(__obdTimer){clearInterval(__obdTimer);__obdTimer=null;}}
function obdStat(on,txt){document.getElementById('obd-dot').classList.toggle('on',!!on);document.getElementById('obd-status').textContent=txt;}
function obdConnect(){
  obdMsg('Connecting to adapter…');
  fetch('/api/obd/connect').then(function(r){return r.json();}).then(function(d){
    if(d.available===false){obdStat(false,'Unavailable');obdMsg('python-obd is not installed on the server. Run <code>pip install obd</code>, then restart <code>wrench_serve.py</code>.','err');return;}
    if(d.connected){obdStat(true,'Connected · '+(d.status||'OBD'));obdMsg('');obdLive();obdReadDTCs();if(__obdTimer)clearInterval(__obdTimer);__obdTimer=setInterval(obdLive,2000);}
    else{obdStat(false,'No adapter');obdMsg(d.error||'No ELM327 adapter found. Pair it (it appears as a COM port) and try again.','err');}
  }).catch(obdDown);
}
function obdLive(){
  fetch('/api/obd/live').then(function(r){return r.json();}).then(function(d){
    if(!d.connected){obdStat(false,'Disconnected');if(__obdTimer){clearInterval(__obdTimer);__obdTimer=null;}return;}
    var L=[['rpm','RPM'],['speed','Speed'],['coolant_temp','Coolant'],['throttle','Throttle'],['fuel_level','Fuel'],['engine_load','Load'],['intake_temp','Intake'],['maf','MAF']];
    document.getElementById('obd-live').innerHTML=L.map(function(x){
      var m=(d.data&&d.data[x[0]])||{};var v=(m.value===null||m.value===undefined)?'&mdash;':m.value;
      return '<div class="obd-metric"><div><span class="obd-m-val">'+v+'</span> <span class="obd-m-unit">'+(m.unit||'')+'</span></div><div class="obd-m-lbl">'+x[1]+'</div></div>';
    }).join('');
  }).catch(obdDown);
}
function obdUrgColor(u){u=(u||'').toLowerCase();if(u.indexOf('high')>=0||u.indexOf('severe')>=0||u.indexOf('critical')>=0)return 'var(--red)';if(u.indexOf('med')>=0||u.indexOf('moder')>=0)return '#e0a23b';if(u.indexOf('low')>=0||u.indexOf('minor')>=0)return 'var(--green)';return 'var(--faint)';}
function obdReadDTCs(){
  fetch('/api/obd/dtcs').then(function(r){return r.json();}).then(function(d){
    if(!d.connected)return;
    var box=document.getElementById('obd-dtcs');
    var all=(d.active||[]).map(function(x){x._t='Active';return x;}).concat((d.pending||[]).map(function(x){x._t='Pending';return x;}));
    if(!all.length){box.innerHTML='<div class="obd-msg ok">&#10003; No trouble codes found.</div>';return;}
    box.innerHTML='<div style="font-family:\\'JetBrains Mono\\',monospace;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--faint);margin:10px 0 2px">// '+all.length+' Trouble Code'+(all.length>1?'s':'')+' &mdash; matched to WRENCH DTC database</div>'+all.map(function(x){
      var cost=(x.cost_low||x.cost_high)?('Est. repair: $'+(x.cost_low||'?')+'&ndash;$'+(x.cost_high||'?')):'';
      var urg=x.urgency?'<span class="obd-urg" style="background:'+obdUrgColor(x.urgency)+';color:#000">'+x.urgency+'</span>':'';
      return '<div class="obd-dtc"><div><span class="c">'+x.code+'</span> <span style="font-size:10px;color:var(--faint)">'+x._t+'</span>'+urg+'</div>'+
        '<div style="margin-top:5px;color:var(--text);font-size:13px">'+(x.description||'No description available')+'</div>'+
        (cost?'<div style="margin-top:4px;color:var(--green);font-size:12px">'+cost+'</div>':'')+
        (x.in_db?'':'<div style="font-size:10px;color:var(--faint);margin-top:3px">(not in local DTC database)</div>')+
        '</div>';
    }).join('');
  }).catch(obdDown);
}
function obdClear(){
  if(!confirm('Clear all stored trouble codes? This turns off the check-engine light and erases freeze-frame data. Only do this after the underlying problem is fixed.'))return;
  fetch('/api/obd/clear?confirm=yes').then(function(r){return r.json();}).then(function(d){
    if(d.cleared){obdMsg('&#10003; Trouble codes cleared.','ok');obdReadDTCs();}
    else obdMsg(d.error||'Could not clear codes.','err');
  }).catch(obdDown);
}
"""


def fix_js_quotes(html):
    """The base template has  font-family:'JetBrains Mono'  inside single-quoted JS
    strings (renderMaint/renderSafety) -> a syntax error that kills the whole app
    <script>. Escape the apostrophes, but only in the app-script region after the
    data block (the CSS before it uses the same text validly). Idempotent."""
    cut = html.find("</script>", html.find("const __D__="))
    if cut < 0:
        return html
    head, tail = html[:cut], html[cut:]
    tail = tail.replace("'JetBrains Mono'", "\\'JetBrains Mono\\'")
    # renderMTabs embeds the tab name into an onclick handler but uses '' where it
    # needs an escaped quote, so the JS string runs together -> "Unexpected string".
    tail = tail.replace("switchMTab(''+t+'','+v.id+')", "switchMTab(\\''+t+'\\','+v.id+')")
    return head + tail


def inject_obd(html):
    """Add the collapsible OBD-II panel below the VIN bar (idempotent)."""
    if "/*WRENCH_OBD*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", OBD_STYLE + "</head>", 1)
    html = html.replace('<div class="g-controls">', OBD_PANEL + '<div class="g-controls">', 1)
    html = html.replace("function switchTab(name){", OBD_JS + "\nfunction switchTab(name){", 1)
    return html


# ── Tiered parts recommendations (OEM / Premium / Best Value) ─────────────────
# Tiers are derived in-browser from each vehicle's REAL part options (is_oem flag
# + brand/keyword). Upsell copy is generic per-part-type education (no fabricated
# prices). NOTE: the underlying parts data is templated (not verified per-VIN
# fitment), so every block carries a fitment caveat + an affiliate disclosure.
PARTTIERS_STYLE = """<style>
.pt-wrap{margin-bottom:8px}
.pt-group{margin-bottom:14px}
.pt-title{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);margin:10px 0 6px}
.pt-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.pt-card{background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;padding:10px;border-top:3px solid var(--border)}
.pt-oem{border-top-color:var(--accent)}
.pt-premium{border-top-color:var(--purple,#a06cd5)}
.pt-value{border-top-color:var(--green)}
.pt-tier{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin-bottom:6px}
.pt-prod{font-weight:700;font-size:13px;margin-bottom:6px}
.pt-any{color:var(--faint);font-weight:500;font-style:italic}
.pt-copy{font-size:11px;color:var(--dim);line-height:1.45;margin-bottom:8px}
.pt-shop{display:inline-block;background:var(--accent);color:#000;font-size:11px;font-weight:700;padding:5px 11px;border-radius:6px;text-decoration:none}
.pt-shop:hover{opacity:.88}
.pt-caveat{font-size:11px;color:var(--amber,#e0a23b);margin-top:6px;line-height:1.45}
.pt-disc{font-size:10px;color:var(--faint);margin-top:6px;font-style:italic}
</style>
"""

PARTTIERS_JS = """/*WRENCH_PARTTIERS*/
var PART_UPSELL={
 plugs:{t:'Spark Plugs',oem:'Exact factory heat range and gap, a safe match for your engine.',premium:'Iridium or platinum tips fire reliably and can last up to ~100k miles.',value:'Copper plugs cost the least up front; plan to change them around every 30k miles.'},
 air:{t:'Engine Air Filter',oem:'Factory-spec element with exact airbox fit.',premium:'Washable, reusable high-flow filter (e.g. K&N) that lasts the life of the car.',value:'Disposable paper filter at the lowest price; swap every 15-30k miles.'},
 batts:{t:'Battery',oem:'Factory group size and cold-cranking amps, a guaranteed drop-in fit.',premium:'AGM design (e.g. Optima): spill-proof, more charge cycles, stronger cold starts.',value:'Standard flooded battery with a solid warranty for everyday driving.'},
 wipers:{t:'Wiper Blades',oem:null,premium:'Beam blades (e.g. Bosch) apply even pressure and shed snow and ice better.',value:'Conventional blades (e.g. Rain-X) are inexpensive and quick to swap.'}
};
var TIER_LABEL={oem:'OEM',premium:'Premium',value:'Best Value'};
function partTier(it){
 if(it.is_oem) return 'oem';
 var s=((it.brand||'')+' '+(it.description||'')+' '+(it.part_number||'')).toLowerCase();
 if(/iridium|platinum|laser|agm|beam|ceramic|optima/.test(s)) return 'premium';
 var b=(it.brand||'').toLowerCase();
 if(b==='k&n'||b==='optima'||b==='bosch') return 'premium';
 return 'value';
}
function ptCard(tier,it,copy){
 var prod=it?('<div class="pt-prod">'+(it.brand||'')+' <span class="pn">'+(it.part_number||'')+'</span></div>')
            :('<div class="pt-prod pt-any">Any reputable '+TIER_LABEL[tier].toLowerCase()+' option</div>');
 var shop=(it&&it.affiliate_url)?('<a class="pt-shop" href="'+it.affiliate_url+'" target="_blank" rel="nofollow sponsored noopener">Shop &#9656;</a>'):'';
 return '<div class="pt-card pt-'+tier+'"><div class="pt-tier">'+TIER_LABEL[tier]+'</div>'+prod+'<div class="pt-copy">'+copy+'</div>'+shop+'</div>';
}
function renderPartTiers(v){
 var p=v.parts; if(!p) return '';
 var groups=[['plugs',p.plugs],['air',p.air],['batts',p.batts],['wipers',p.wipers]];
 var html=''; var any=false;
 groups.forEach(function(g){
   var key=g[0], items=g[1]; if(!items||!items.length) return;
   any=true; var u=PART_UPSELL[key];
   var byTier={}; items.forEach(function(it){var t=partTier(it); if(!byTier[t]) byTier[t]=it;});
   var cards=['oem','premium','value'].filter(function(t){return u[t]!=null;})
     .map(function(t){return ptCard(t,byTier[t]||null,u[t]);}).join('');
   html+='<div class="pt-group"><div class="pt-title">'+u.t+'</div><div class="pt-row">'+cards+'</div></div>';
 });
 if(!any) return '';
 return '<div class="pt-wrap"><div class="sec-head">Recommended Parts by Tier</div>'+html
   +'<div class="pt-caveat">&#9888; Verify fitment for your exact year, trim and VIN before buying. Listings are suggestions, not a fitment guarantee.</div>'
   +'<div class="pt-disc">As an Amazon Associate, qualifying purchases may earn a commission at no extra cost to you.</div></div>';
}
function renderPartsTiered(v){return renderPartTiers(v)+renderParts(v);}
"""


def inject_parttiers(html):
    """Add tiered parts recommendations atop the Parts tab (idempotent)."""
    if "/*WRENCH_PARTTIERS*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", PARTTIERS_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", PARTTIERS_JS + "\nfunction switchTab(name){", 1)
    html = html.replace("parts:renderParts,", "parts:renderPartsTiered,", 1)
    return html


# ── "Watch It Done" YouTube DIY videos (server proxies /api/youtube/...) ──────
# Click-to-load per service (not on modal open) to conserve YouTube quota; the
# server caches 30 days. Falls back to a "start the server" message on file://.
YT_STYLE = """<style>
.yt-wrap{margin:8px 0 6px}
.yt-svcs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.yt-svc{background:var(--p2,#111);border:1px solid var(--border);color:var(--dim);font-size:11px;padding:6px 11px;border-radius:6px;cursor:pointer;text-transform:capitalize}
.yt-svc:hover{color:var(--text);border-color:var(--accent)}
.yt-svc.active{background:var(--accent);color:#000;border-color:var(--accent);font-weight:700}
.yt-hint{font-size:12px;color:var(--faint);padding:6px 0;line-height:1.5}
.yt-hint.yt-err{color:var(--amber,#e0a23b)}
.yt-hint code{background:var(--p2,#111);padding:2px 6px;border-radius:4px}
.yt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.yt-card{display:block;background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;overflow:hidden;text-decoration:none;transition:border-color .15s}
.yt-card:hover{border-color:var(--accent)}
.yt-thumb{position:relative;aspect-ratio:16/9;background:#000}
.yt-thumb img{width:100%;height:100%;object-fit:cover;display:block}
.yt-dur{position:absolute;right:6px;bottom:6px;background:rgba(0,0,0,.85);color:#fff;font-size:10px;font-weight:700;padding:1px 5px;border-radius:3px}
.yt-meta{padding:8px}
.yt-vtitle{font-size:12px;font-weight:700;color:var(--text);line-height:1.3;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.yt-vch{font-size:11px;color:var(--accent)}
.yt-vviews{font-size:10px;color:var(--faint);margin-top:2px}
.yt-cache{font-size:9px;color:var(--faint);margin-top:6px;font-style:italic}
</style>
"""

YT_JS = """/*WRENCH_YOUTUBE*/
var YT_SVCS=['oil change','air filter','cabin filter','spark plugs','brake pads','tire rotation','battery replacement','wiper blades'];
function ytEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function ytViews(n){if(n==null)return '';n=+n;if(n>=1e6)return (n/1e6).toFixed(1)+'M views';if(n>=1e3)return Math.round(n/1e3)+'K views';return n+' views';}
function renderWatchItDone(v){
  var btns=YT_SVCS.map(function(s){return '<button class="yt-svc" data-svc="'+s+'" onclick="ytLoad(this)">'+s+'</button>';}).join('');
  return '<div class="yt-wrap" data-y="'+ytEsc(v.year)+'" data-mk="'+ytEsc(v.make)+'" data-md="'+ytEsc(v.model)+'">'
    +'<div class="sec-head">Watch It Done</div><div class="yt-svcs">'+btns+'</div>'
    +'<div id="yt-results"><div class="yt-hint">Pick a service above to load the top 3 DIY videos for this vehicle.</div></div></div>';
}
function ytCard(vd){
  return '<a class="yt-card" href="https://www.youtube.com/watch?v='+encodeURIComponent(vd.id)+'" target="_blank" rel="noopener">'
    +'<div class="yt-thumb"><img loading="lazy" alt="" src="'+ytEsc(vd.thumbnail||'')+'">'+(vd.duration?'<span class="yt-dur">'+ytEsc(vd.duration)+'</span>':'')+'</div>'
    +'<div class="yt-meta"><div class="yt-vtitle">'+ytEsc(vd.title)+'</div><div class="yt-vch">'+ytEsc(vd.channel)+'</div><div class="yt-vviews">'+ytViews(vd.views)+'</div></div></a>';
}
function ytLoad(btn){
  var svc=btn.getAttribute('data-svc'), wrap=btn.parentNode.parentNode;
  var y=wrap.getAttribute('data-y'), mk=wrap.getAttribute('data-mk'), md=wrap.getAttribute('data-md');
  var bs=wrap.querySelectorAll('.yt-svc'); for(var i=0;i<bs.length;i++) bs[i].classList.remove('active'); btn.classList.add('active');
  var box=wrap.querySelector('#yt-results');
  box.innerHTML='<div class="yt-hint">Loading top videos for '+svc+'\\u2026</div>';
  var url='/api/youtube/'+encodeURIComponent(y)+'/'+encodeURIComponent(mk)+'/'+encodeURIComponent(md)+'/'+encodeURIComponent(svc);
  fetch(url).then(function(r){return r.json();}).then(function(d){
    if(d.error){box.innerHTML='<div class="yt-hint yt-err">'+ytEsc(d.error)+'</div>';return;}
    var vids=d.videos||[];
    if(!vids.length){box.innerHTML='<div class="yt-hint">No DIY videos found for '+svc+'.</div>';return;}
    box.innerHTML='<div class="yt-grid">'+vids.map(ytCard).join('')+'</div>'+(d.cached?'<div class="yt-cache">cached result</div>':'');
  }).catch(function(){
    box.innerHTML='<div class="yt-hint yt-err">Video search needs the local server. Run <code>python wrench_serve.py</code> and open <code>http://localhost:8000/</code>.</div>';
  });
}
function renderPartsTieredYT(v){return renderPartTiers(v)+renderWatchItDone(v)+renderParts(v);}
"""


def inject_youtube(html):
    """Add the 'Watch It Done' video section below tiered parts (idempotent)."""
    if "/*WRENCH_YOUTUBE*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", YT_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", YT_JS + "\nfunction switchTab(name){", 1)
    html = html.replace("parts:renderPartsTiered,", "parts:renderPartsTieredYT,", 1)
    return html


# ── "How To Do It" AI repair guides (server proxies /api/guide/...) ───────────
GUIDES_STYLE = """<style>
.gh-wrap{margin:8px 0 6px}
.gh-banner{background:#3a2e00;border:1px solid #e0a23b;color:#ffd97a;font-size:12px;font-weight:600;padding:9px 12px;border-radius:8px;margin-bottom:10px;line-height:1.45}
.gh-svcs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.gh-svc{background:var(--p2,#111);border:1px solid var(--border);color:var(--dim);font-size:11px;padding:6px 11px;border-radius:6px;cursor:pointer;text-transform:capitalize}
.gh-svc:hover{color:var(--text);border-color:var(--accent)}
.gh-svc.active{background:var(--accent);color:#000;border-color:var(--accent);font-weight:700}
.gh-hint{font-size:12px;color:var(--faint);padding:6px 0;line-height:1.5}
.gh-hint.gh-err{color:var(--amber,#e0a23b)}
.gh-hint code{background:var(--p2,#111);padding:2px 6px;border-radius:4px}
.gh-safety{background:#3a1500;border:1px solid var(--red);color:#ffb3a0;font-size:13px;padding:11px 13px;border-radius:8px;line-height:1.5}
.gh-guide{background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;padding:14px;font-size:13px;line-height:1.6;color:var(--text)}
.gh-h{font-weight:700;color:var(--accent);font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin:12px 0 6px}
.gh-guide .gh-ol,.gh-guide .gh-ul{margin:6px 0 6px 20px;padding:0}
.gh-guide li{margin-bottom:5px}
.gh-p{margin:6px 0;color:var(--dim)}
.gh-cache{font-size:9px;color:var(--faint);margin-top:6px;font-style:italic}
</style>
"""

GUIDES_JS = r"""/*WRENCH_GUIDES*/
var GH_SVCS=['oil change','air filter','cabin filter','spark plugs','tire rotation','battery replacement','wiper blades','brake pads'];
function ghEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function ghMd(t){
  var lines=ghEsc(t).split('\n'), out=[], inList=null;
  function close(){ if(inList){out.push('</'+inList+'>');inList=null;} }
  for(var i=0;i<lines.length;i++){
    var ln=lines[i].replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    if(/^\s*-{3,}\s*$/.test(ln)){continue;}
    var h=ln.match(/^\s*#{1,4}\s+(.*)$/), ol=ln.match(/^\s*\d+\.\s+(.*)$/), ul=ln.match(/^\s*[-*]\s+(.*)$/);
    if(h){close();out.push('<div class="gh-h">'+h[1]+'</div>');}
    else if(ol){if(inList!=='ol'){close();out.push('<ol class="gh-ol">');inList='ol';}out.push('<li>'+ol[1]+'</li>');}
    else if(ul){if(inList!=='ul'){close();out.push('<ul class="gh-ul">');inList='ul';}out.push('<li>'+ul[1]+'</li>');}
    else if(ln.trim()===''){close();}
    else {close();out.push('<p class="gh-p">'+ln+'</p>');}
  }
  close(); return out.join('');
}
function renderHowToDoIt(v){
  var btns=GH_SVCS.map(function(s){return '<button class="gh-svc" data-svc="'+s+'" onclick="ghLoad(this)">'+s+'</button>';}).join('');
  return '<div class="gh-wrap" data-vid="'+ghEsc(v.id)+'"><div class="sec-head">How To Do It</div>'
    +'<div class="gh-banner">&#9888; AI-generated guide — always verify specs before use. Consult a professional for safety-critical work.</div>'
    +'<div class="gh-svcs">'+btns+'</div>'
    +'<div id="gh-results"><div class="gh-hint">Pick a service to generate a step-by-step guide for this vehicle.</div></div></div>';
}
function ghLoad(btn){
  var svc=btn.getAttribute('data-svc'), wrap=btn.parentNode.parentNode, vid=wrap.getAttribute('data-vid');
  var bs=wrap.querySelectorAll('.gh-svc'); for(var i=0;i<bs.length;i++) bs[i].classList.remove('active'); btn.classList.add('active');
  var box=wrap.querySelector('#gh-results');
  box.innerHTML='<div class="gh-hint">Generating '+svc+' guide… (a few seconds)</div>';
  fetch('/api/guide/'+encodeURIComponent(vid)+'/'+encodeURIComponent(svc)).then(function(r){return r.json();}).then(function(d){
    if(d.error){box.innerHTML='<div class="gh-hint gh-err">'+ghEsc(d.error)+'</div>';return;}
    if(d.safety_blocked){box.innerHTML='<div class="gh-safety">&#9888; '+ghEsc(d.message)+'</div>';return;}
    if(!d.guide){box.innerHTML='<div class="gh-hint">No guide available.</div>';return;}
    box.innerHTML='<div class="gh-guide">'+ghMd(d.guide)+'</div>'+(d.cached?'<div class="gh-cache">cached</div>':'');
  }).catch(function(){
    box.innerHTML='<div class="gh-hint gh-err">Guide generation needs the local server. Run <code>python wrench_serve.py</code> and open <code>http://localhost:8000/</code>.</div>';
  });
}
function renderPartsTieredYTG(v){return renderPartTiers(v)+renderWatchItDone(v)+renderHowToDoIt(v)+renderParts(v);}
"""


def inject_guides(html):
    """Add the 'How To Do It' AI guide section below the videos (idempotent)."""
    if "/*WRENCH_GUIDES*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", GUIDES_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", GUIDES_JS + "\nfunction switchTab(name){", 1)
    html = html.replace("parts:renderPartsTieredYT,", "parts:renderPartsTieredYTG,", 1)
    return html


def ascii_polish(html):
    """Convert typographic + double-encoded-mojibake characters to plain ASCII, then strip any
    remaining non-ASCII outside the data blob. The embedded __D__ JSON is already ASCII (json
    ensure_ascii), so only markup/JS is affected. Guarantees the page can't render as mojibake
    under any charset."""
    repl = [
        # double-encoded mojibake (UTF-8 misread as Windows-1252, then re-saved)
        ("â€”", "-"), ("â€“", '"'),
        ("â€¦", "..."), ("â€™", "'"), ("â€˜", "'"),
        ("Â·", "-"), ("Â ", " "),
        # clean typographic characters
        ("—", "-"), ("–", "-"), ("…", "..."), ("·", "-"),
        ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'), (" ", " "),
    ]
    for a, b in repl:
        html = html.replace(a, b)
    ds = html.find("const __D__=")
    de = html.find("</script>", ds) if ds >= 0 else -1
    if ds >= 0 and de > ds:
        head = html[:ds].encode("ascii", "ignore").decode("ascii")
        tail = html[de:].encode("ascii", "ignore").decode("ascii")
        html = head + html[ds:de] + tail
    return html


def inject_branding(html):
    """Rebrand to Know Your Ride / knowyourride.net: title, meta, canonical, About."""
    html = re.sub(r"<title>.*?</title>",
                  "<title>Know Your Ride — Vehicle Maintenance Reference</title>",
                  html, count=1, flags=re.S)
    if "<!--KYR_META-->" not in html:
        desc = "Free vehicle maintenance specs for 1,669 vehicles. Oil specs, parts, torque, DTC codes, recalls and more."
        meta = ("<!--KYR_META-->\n"
                f'<meta name="description" content="{desc}">\n'
                '<link rel="canonical" href="https://knowyourride.net/">\n'
                '<meta property="og:title" content="Know Your Ride — Vehicle Maintenance Reference">\n'
                f'<meta property="og:description" content="{desc}">\n'
                '<meta property="og:url" content="https://knowyourride.net/">\n'
                '<meta property="og:type" content="website">\n')
        html = html.replace("</head>", meta + "</head>", 1)
    # Google Search Console domain verification (HTML-tag method)
    if "google-site-verification" not in html:
        html = html.replace(
            "</head>",
            '<meta name="google-site-verification" content="I2glmAltse1Ocnz_L11XgRKQWk8zyW3a7PY0VoC-QIM">\n</head>', 1)
    # full wordmark rebrand (topbar logo + about hero); the <em>.</em> stays the orange accent
    html = html.replace("WRENCH<em>.</em>", "KNOW YOUR RIDE<em>.</em>")
    # taglines (topbar + about share this exact text)
    html = html.replace("// know your ride. fix it yourself.",
                        "Your pocket owner's manual for every car")
    # official URL under the about hero (idempotent)
    if 'class="about-url"' not in html:
        html = html.replace(
            '<div class="about-brand">KNOW YOUR RIDE<em>.</em></div>',
            '<div class="about-brand">KNOW YOUR RIDE<em>.</em></div>\n    '
            "<div class=\"about-url\" style=\"margin-top:12px;font-family:'JetBrains Mono',monospace;font-size:14px\">"
            '<a href="https://knowyourride.net/" style="color:var(--accent);text-decoration:none" target="_blank" rel="noopener">knowyourride.net</a>'
            ' <span style="color:var(--faint);font-size:11px">// official site</span></div>', 1)
    # refresh stale About stats
    html = html.replace('<div class="astat-n">1071</div>', '<div class="astat-n">1,669</div>', 1)
    html = html.replace('<div class="astat-n">39</div>', '<div class="astat-n">47</div>', 1)
    html = html.replace('<div class="astat-n">464</div>', '<div class="astat-n">5,022</div>', 1)
    # year-range coverage badge: fix "2003<dash>2024" (stray curly-quote/em-dash) -> "2003-2025"
    html = re.sub(r"2003[^0-9]2024 coverage", "2003-2025 coverage", html)
    html = html.replace("39 MAKES - 22 YEARS", "39 MAKES - 23 YEARS")
    return html


# ── "Know Your Part" tab: photo -> /api/identify-part -> result + DB matches ──
KYP_STYLE = """<style>
.kyp-wrap{max-width:640px;margin:0 auto}
.kyp-intro{color:var(--dim);font-size:14px;margin-bottom:16px;text-align:center;line-height:1.5}
.kyp-uploader{border:2px dashed var(--border);border-radius:12px;padding:28px 20px;text-align:center;background:var(--panel)}
.kyp-btn{background:var(--accent);color:#000;border:none;border-radius:8px;padding:12px 22px;font-weight:700;font-size:14px;cursor:pointer}
.kyp-btn:hover{opacity:.88}
.kyp-hint{font-size:11px;color:var(--faint);margin-top:10px}
.kyp-preview-wrap{margin-top:16px;text-align:center}
#kyp-preview{max-width:100%;max-height:320px;border-radius:10px;border:1px solid var(--border)}
.kyp-scan{display:block;margin:14px auto 0;background:var(--accent);color:#000;border:none;border-radius:8px;padding:11px 24px;font-weight:700;cursor:pointer}
.kyp-scan:hover{opacity:.88} .kyp-scan:disabled{opacity:.5;cursor:default}
.kyp-card{margin-top:18px;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px;border-left:3px solid var(--accent)}
.kyp-card h3{margin:0 0 8px;color:var(--accent);font-size:15px}
.kyp-desc{color:var(--text);font-size:13px;line-height:1.6;white-space:pre-wrap}
.kyp-match-title{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin:16px 0 8px}
.kyp-match{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;padding:9px 12px;margin-bottom:6px}
.kyp-match .b{font-weight:700;font-size:13px} .kyp-match .pn{font-size:11px}
.kyp-shop{background:var(--accent);color:#000;font-size:11px;font-weight:700;padding:5px 11px;border-radius:6px;text-decoration:none;white-space:nowrap}
.kyp-msg{font-size:13px;color:var(--dim);margin-top:14px;line-height:1.5}
.kyp-msg.err{color:var(--amber,#e0a23b)} .kyp-msg code{background:var(--p2,#111);padding:2px 6px;border-radius:4px}
</style>
"""

KYP_PANE = """<div class="pane" id="pane-identify">
  <div class="kyp-wrap">
    <div class="sec-head">Know Your Part</div>
    <div class="kyp-intro">Snap or upload a photo of a car part and AI will identify it.</div>
    <div class="kyp-uploader">
      <input type="file" id="kyp-file" accept="image/*" capture="environment" onchange="kypPreview(this)" style="display:none">
      <button class="kyp-btn" onclick="document.getElementById('kyp-file').click()">&#128247; &nbsp;Take / Upload Photo</button>
      <div class="kyp-hint">JPG or PNG. Photos are auto-resized before upload (2 MB max).</div>
    </div>
    <div class="kyp-preview-wrap" id="kyp-preview-wrap" style="display:none">
      <img id="kyp-preview" alt="preview">
      <button class="kyp-scan" id="kyp-scan-btn" onclick="kypScan()">Identify Part</button>
    </div>
    <div id="kyp-results"></div>
  </div>
</div>
"""

KYP_JS = r"""/*WRENCH_KYP*/
var KYP_CAT=null, KYP_DATAURL=null;
function kypEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function kypPreview(inp){
  var f=inp.files&&inp.files[0]; if(!f) return;
  var rd=new FileReader();
  rd.onload=function(e){KYP_DATAURL=e.target.result;document.getElementById('kyp-preview').src=KYP_DATAURL;
    document.getElementById('kyp-preview-wrap').style.display='block';document.getElementById('kyp-results').innerHTML='';};
  rd.readAsDataURL(f);
}
function kypScan(){
  if(!KYP_DATAURL) return;
  var btn=document.getElementById('kyp-scan-btn'); btn.disabled=true; btn.textContent='Identifying...';
  var res=document.getElementById('kyp-results'); res.innerHTML='<div class="kyp-msg">Analyzing photo...</div>';
  var img=new Image();
  img.onload=function(){
    var max=1280,w=img.width,h=img.height;
    if(w>max||h>max){var s=Math.min(max/w,max/h);w=Math.round(w*s);h=Math.round(h*s);}
    var c=document.createElement('canvas'); c.width=w; c.height=h; c.getContext('2d').drawImage(img,0,0,w,h);
    var b64=c.toDataURL('image/jpeg',0.85).split(',')[1];
    fetch('/api/identify-part',{method:'POST',headers:{'Content-Type':'text/plain','X-Image-Type':'image/jpeg'},body:b64})
      .then(function(r){return r.json();}).then(function(d){
        btn.disabled=false; btn.textContent='Identify Part';
        if(d.error){res.innerHTML='<div class="kyp-msg err">'+kypEsc(d.error)+'</div>';return;}
        if(!d.identification){res.innerHTML='<div class="kyp-msg">No identification returned.</div>';return;}
        res.innerHTML=kypRender(d.identification);
      }).catch(function(){
        btn.disabled=false; btn.textContent='Identify Part';
        res.innerHTML='<div class="kyp-msg err">Part identification needs the API backend. On the live site it works automatically; locally, run <code>python wrench_serve.py</code>.</div>';
      });
  };
  img.src=KYP_DATAURL;
}
function kypCatalog(){
  if(KYP_CAT) return KYP_CAT;
  var cat={plug:{},air:{},cabin:{},battery:{},wiper:{},oil:{}};
  function add(b,arr){(arr||[]).forEach(function(p){if(p&&(p.part_number||p.brand)){var k=(p.brand||'')+'|'+(p.part_number||'');if(!b[k])b[k]={brand:p.brand,part_number:p.part_number,url:p.affiliate_url};}});}
  DB.v.forEach(function(v){var p=v.parts||{},o=v.oil||{};add(cat.plug,p.plugs);add(cat.air,p.air);add(cat.cabin,p.cabin);add(cat.battery,p.batts);add(cat.wiper,p.wipers);add(cat.oil,o.filters);});
  KYP_CAT={}; for(var t in cat){KYP_CAT[t]=[];for(var k in cat[t])KYP_CAT[t].push(cat[t][k]);}
  return KYP_CAT;
}
function kypRender(text){
  var html='<div class="kyp-card"><h3>Identification</h3><div class="kyp-desc">'+kypEsc(text)+'</div></div>';
  var cat=kypCatalog(), t=(text||'').toLowerCase(), hits=[];
  [['plug',/spark plug|ignition plug/],['air',/air filter|air cleaner|intake filter/],['cabin',/cabin (air )?filter|pollen filter/],['battery',/\bbattery\b/],['wiper',/wiper|windshield blade/],['oil',/oil filter/]].forEach(function(rl){if(rl[1].test(t))hits=hits.concat(cat[rl[0]].slice(0,6));});
  var seen={},uniq=[]; hits.forEach(function(p){var k=(p.brand||'')+(p.part_number||'');if(!seen[k]){seen[k]=1;uniq.push(p);}});
  uniq=uniq.slice(0,8);
  if(uniq.length){
    html+='<div class="kyp-match-title">// Matching parts in our database</div>';
    html+=uniq.map(function(p){
      var shop=p.url?('<a class="kyp-shop" href="'+p.url+'" target="_blank" rel="nofollow sponsored noopener">Shop</a>'):'';
      return '<div class="kyp-match"><div><span class="b">'+kypEsc(p.brand||'')+'</span> <span class="pn">'+kypEsc(p.part_number||'')+'</span></div>'+shop+'</div>';
    }).join('');
    html+='<div class="kyp-msg" style="font-size:11px;color:var(--faint)">Suggestions by part type — verify fitment for your specific vehicle.</div>';
  }
  return html;
}
"""


def inject_identify(html):
    """Add the 'Know Your Part' nav tab + pane wired to /api/identify-part (idempotent)."""
    if "/*WRENCH_KYP*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", KYP_STYLE + "</head>", 1)
    html = html.replace(
        '<div class="tab-btn" data-tab="about" onclick="switchTab(\'about\')">&#9881; &nbsp;About</div>',
        '<div class="tab-btn" data-tab="identify" onclick="switchTab(\'identify\')">&#128247; &nbsp;Know Your Part</div>\n'
        '  <div class="tab-btn" data-tab="about" onclick="switchTab(\'about\')">&#9881; &nbsp;About</div>', 1)
    html = html.replace('<div class="pane" id="pane-about">', KYP_PANE + '\n<div class="pane" id="pane-about">', 1)
    html = html.replace("function switchTab(name){", KYP_JS + "\nfunction switchTab(name){", 1)
    return html


def inject_partial(html):
    """vPIC pre-2003 vehicles have negative ids and only year/make/model/engine (no oil/parts/
    torque). Badge them 'Partial data - pre-2003' so users know specs are limited, and stop the
    no-oil heuristic from mislabelling them as EVs. Idempotent."""
    if "bdg-partial" in html:
        return html
    if "</head>" in html:
        html = html.replace(
            "</head>",
            "<style>.bdg-partial{background:#3a2e00;color:#ffd97a;border:1px solid #e0a23b}</style>\n</head>", 1)
    # don't treat 'no oil data' as EV for the sparse pre-2003 (negative-id) vehicles
    html = html.replace("isEV=!o||!o.visc;", "isEV=(v.id>=0)&&(!o||!o.visc);", 1)
    # add the partial-data badge on those cards
    html = html.replace(
        "const bdg=[];",
        "const bdg=[];if(v.id<0)bdg.push('<span class=\"bdg bdg-partial\">Partial data - pre-2003</span>');", 1)
    return html


# ── KBB "Vehicle Value" button on the Warranty & Recalls tab (after recalls) ──
KBB_STYLE = """<style>
.kbb-btn{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(180deg,var(--accent),#d4881f);color:#000;font-weight:700;font-size:13px;letter-spacing:.03em;text-decoration:none;padding:12px 20px;border-radius:9px;border:1px solid #e0a23b;transition:.15s}
.kbb-btn:hover{opacity:.9;transform:translateY(-1px)}
</style>
"""

KBB_JS = r"""/*WRENCH_KBB*/
function kbbSlug(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');}
function kbbButton(v){
  if(!v||!v.make||!v.model||!v.year)return '';
  var url='https://www.kbb.com/'+kbbSlug(v.make)+'/'+kbbSlug(v.model)+'/'+v.year+'/';
  return '<div class="sec-head" style="margin-top:18px">Vehicle Value</div>'
    +'<p class="empty-note" style="margin-bottom:10px">Get a current trade-in &amp; private-party value estimate from Kelley Blue Book.</p>'
    +'<a class="kbb-btn" href="'+url+'" target="_blank" rel="noopener noreferrer">Check Your Car&#39;s Value on KBB &rarr;</a>';
}
function renderWarrantyKbb(v){return renderWarranty(v)+kbbButton(v);}
"""


def inject_kbb(html):
    """Append a Kelley Blue Book value button to the Warranty & Recalls tab,
    after the recalls section, for every vehicle (year/make/model). Idempotent."""
    if "/*WRENCH_KBB*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", KBB_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", KBB_JS + "\nfunction switchTab(name){", 1)
    html = html.replace("warranty:renderWarranty,comps:renderComplaints",
                        "warranty:renderWarrantyKbb,comps:renderComplaints", 1)
    return html


# ── DTC lookup: CarMD-style ranked fixes (probability %, avg cost, severity) ──
FIXRATES_STYLE = """<style>
.dtc-fixes{margin-top:11px;border-top:1px solid var(--border);padding-top:10px}
.dtc-fix-h{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-bottom:9px}
.dtc-fix-src{letter-spacing:.04em;text-transform:none;color:var(--faint);opacity:.8}
.dtc-fix{margin-bottom:11px}
.dtc-fix-top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:4px}
.dtc-fix-name{color:var(--text);font-size:13px}
.dtc-fix-prob{color:var(--accent);font-weight:700;font-size:13px;font-family:'JetBrains Mono',monospace;flex-shrink:0}
.dtc-fix-track{height:5px;background:var(--p2,#111);border-radius:3px;overflow:hidden}
.dtc-fix-bar{height:100%;background:linear-gradient(90deg,var(--accent),#d4881f)}
.dtc-fix-meta{font-size:11px;color:var(--dim);margin-top:4px}
.dtc-fix-sev{text-transform:capitalize;font-weight:600}
</style>
"""

FIXRATES_JS = r"""/*WRENCH_FIXRATES*/
function dtcEsc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function dtcSevColor(s){s=String(s||'').toLowerCase();return s.indexOf('high')>=0?'var(--red)':(s.indexOf('med')>=0?'#e0a23b':'var(--green)');}
function dtcFixes(code){
  var fx=(DB.fixes&&DB.fixes[code])||[];
  if(!fx.length)return '';
  var rows=fx.map(function(f){
    var prob=(f.prob!=null?f.prob:0);
    var cost=(f.cost!=null?'$'+f.cost:'cost varies');
    var sev=f.sev?'<span class="dtc-fix-sev" style="color:'+dtcSevColor(f.sev)+'">'+dtcEsc(f.sev)+'</span>':'';
    return '<div class="dtc-fix">'
      +'<div class="dtc-fix-top"><span class="dtc-fix-name">'+dtcEsc(f.fix)+'</span><span class="dtc-fix-prob">'+prob+'%</span></div>'
      +'<div class="dtc-fix-track"><div class="dtc-fix-bar" style="width:'+prob+'%"></div></div>'
      +'<div class="dtc-fix-meta">avg '+cost+(sev?' &middot; '+sev:'')+'</div>'
      +'</div>';
  }).join('');
  return '<div class="dtc-fixes"><div class="dtc-fix-h">Most likely fixes <span class="dtc-fix-src">(ranked by reported success)</span></div>'+rows+'</div>';
}
"""


def inject_fixrates(html):
    """Show ranked fix probabilities under each matched DTC card in the code lookup. Idempotent."""
    if "/*WRENCH_FIXRATES*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", FIXRATES_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", FIXRATES_JS + "\nfunction switchTab(name){", 1)
    html = html.replace(
        "+(desc||'No description available')+'</span></div></div>';}",
        "+(desc||'No description available')+'</span></div>'+dtcFixes(code)+'</div>';}", 1)
    return html


# ── Affiliate shopping links (Amazon-only affiliate; others = convenience) ────
# Amazon is the affiliate CTA (wrenchapp20-20). RockAuto / AutoZone are small,
# de-emphasized, NON-affiliate convenience links. One FTC note per section.
AFF_STYLE = """<style>
.aff-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:8px}
.aff-az{display:inline-flex;align-items:center;gap:6px;background:linear-gradient(180deg,#ff9b30,#e07b12);color:#000;font-size:11px;font-weight:700;padding:6px 12px;border-radius:7px;text-decoration:none;border:1px solid #ff9900}
.aff-az:hover{filter:brightness(1.07)}
.aff-az.aff-mini{padding:3px 9px;font-size:10px;border-radius:6px}
.aff-more{display:inline-flex;gap:10px;font-size:10px}
.aff-more a{color:var(--faint);text-decoration:none;border-bottom:1px dotted var(--border)}
.aff-more a:hover{color:var(--dim)}
.aff-ftc{font-size:10px;color:var(--faint);margin:6px 0 4px;font-style:italic;line-height:1.4}
.sp-wrap{margin:2px 0 16px}
.sp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}
.sp-item{background:var(--p2,#111);border:1px solid var(--border);border-radius:8px;padding:9px 11px}
.sp-name{font-size:12px;font-weight:700;margin-bottom:2px}
.aff-guide{margin-top:14px;border-top:1px solid var(--border);padding-top:10px}
</style>
"""

AFF_JS = r"""/*WRENCH_AFF*/
function affEnc(s){return encodeURIComponent(String(s==null?'':s).replace(/\s+/g,' ').trim());}
function affAmz(term){return 'https://www.amazon.com/s?k='+affEnc(term)+'&tag=wrenchapp20-20';}
function affRock(v){return v?('https://www.rockauto.com/en/catalog/'+affEnc(v.make)+','+affEnc(v.model)+','+affEnc(v.year)):'';}
function affAz(pn){return 'https://www.autozone.com/searchresult?searchtext='+affEnc(pn);}
function affFtc(){return '<div class="aff-ftc">Amazon links are affiliate links (we may earn a commission at no extra cost to you). Other retailer links are for convenience only.</div>';}
// Amazon = affiliate CTA; RockAuto/AutoZone = small NON-affiliate convenience links.
function affRow(v,term,pn,compact){
  pn=pn||term;
  var amz='<a class="aff-az'+(compact?' aff-mini':'')+'" href="'+affAmz(term)+'" target="_blank" rel="nofollow sponsored noopener">Shop on Amazon'+(compact?'':' &#9656;')+'</a>';
  var more='<span class="aff-more">'
    +(v?'<a href="'+affRock(v)+'" target="_blank" rel="noopener">RockAuto</a>':'')
    +'<a href="'+affAz(pn)+'" target="_blank" rel="noopener">AutoZone</a></span>';
  return '<div class="aff-row">'+amz+more+'</div>';
}
// Garage overview: compact "Shop Parts" quick-links for the common wear items.
function affShopParts(v){
  if(!v||!v.make||v.id<0)return '';
  var ymm=v.year+' '+v.make+' '+v.model+' ';
  var items=['Oil Filter','Engine Air Filter','Cabin Air Filter','Wiper Blades'];
  var blocks=items.map(function(name){
    return '<div class="sp-item"><div class="sp-name">'+name+'</div>'+affRow(v,ymm+name,ymm+name,true)+'</div>';
  }).join('');
  return '<div class="sp-wrap"><div class="sec-head">Shop Parts</div>'+affFtc()+'<div class="sp-grid">'+blocks+'</div></div>';
}
function renderOilShop(v){return affShopParts(v)+renderOil(v);}
// Maintenance: per-item Amazon "Buy Parts" button.
function affMaintBtn(v,desc){
  if(!v||!v.make)return '';
  var term=(v.year+' '+v.make+' '+v.model+' '+String(desc||'')).replace(/replacement|service|inspect(ion)?|rotate|rotation|flush|check|adjust/gi,'').replace(/\s+/g,' ').trim()+' parts';
  return ' <a class="aff-az aff-mini" href="'+affAmz(term)+'" target="_blank" rel="nofollow sponsored noopener">Buy Parts</a>';
}
// AI guide: "Parts You'll Need" using the exact service + any known part number.
function affGuideParts(vid,svc){
  var v=(DB.v||[]).find(function(x){return x.id==vid;}); if(!v)return '';
  var ymm=v.year+' '+v.make+' '+v.model+' ';
  var term=ymm+svc, pn=ymm+svc, p=v.parts||{};
  var s=String(svc||'').toLowerCase();
  if(s.indexOf('oil')>=0){term=ymm+'oil filter and motor oil';pn=ymm+'oil filter';}
  else if(s.indexOf('air filter')>=0){pn=(p.air&&p.air[0]&&p.air[0].part_number)||ymm+'air filter';}
  else if(s.indexOf('cabin')>=0){pn=(p.cabin&&p.cabin[0]&&p.cabin[0].part_number)||ymm+'cabin filter';}
  else if(s.indexOf('spark')>=0){pn=(p.plugs&&p.plugs[0]&&p.plugs[0].part_number)||ymm+'spark plugs';}
  else if(s.indexOf('wiper')>=0){pn=ymm+'wiper blades';}
  else if(s.indexOf('battery')>=0){pn=ymm+'battery';}
  return '<div class="aff-guide"><div class="gh-h">Parts You&#39;ll Need</div>'+affFtc()+affRow(v,term,pn)+'</div>';
}
// DTC lookup: shop the component named in a likely fix (no vehicle context).
function affDtcShop(fixText){
  var comp=String(fixText||'').replace(/replacement|replace|repair|cleaning|clean|service|\bof\b|\bthe\b/gi,'').replace(/\s+/g,' ').trim();
  if(!comp)return '';
  return '<div class="aff-row"><a class="aff-az aff-mini" href="'+affAmz(comp)+'" target="_blank" rel="nofollow sponsored noopener">Shop '+comp+'</a>'
    +'<span class="aff-more"><a href="'+affAz(comp)+'" target="_blank" rel="noopener">AutoZone</a></span></div>';
}
"""


def inject_affiliate(html):
    """Amazon-affiliate shopping links across the app: garage 'Shop Parts' quick-links,
    parts-tier cards, maintenance 'Buy Parts', AI-guide 'Parts You'll Need', and DTC
    fix shopping. Amazon is the affiliate CTA; other retailers are convenience links.
    Idempotent. Must run after inject_parttiers / inject_guides / inject_fixrates."""
    if "/*WRENCH_AFF*/" in html:
        return html
    if "</head>" in html:
        html = html.replace("</head>", AFF_STYLE + "</head>", 1)
    html = html.replace("function switchTab(name){", AFF_JS + "\nfunction switchTab(name){", 1)
    # 1) garage overview Shop Parts -> prepend to the default (oil) tab
    html = html.replace("oil:renderOil,", "oil:renderOilShop,", 1)
    # 3) maintenance: Buy Parts button beside each scheduled item
    html = html.replace(
        '\'<tr><td style="font-weight:700">\'+s.desc+\'</td>',
        '\'<tr><td style="font-weight:700">\'+s.desc+affMaintBtn(v,s.desc)+\'</td>', 1)
    # 4) AI guide: append Parts You'll Need under each generated guide
    html = html.replace(
        "box.innerHTML='<div class=\"gh-guide\">'+ghMd(d.guide)+'</div>'+(d.cached?",
        "box.innerHTML='<div class=\"gh-guide\">'+ghMd(d.guide)+'</div>'+affGuideParts(vid,svc)+(d.cached?", 1)
    # 2) parts-tier cards: replace the single (broken) affiliate_url 'Shop' link with the
    #    Amazon CTA + convenience links. ptCard never had the vehicle/part-type, so add them.
    html = html.replace("function ptCard(tier,it,copy){",
                        "function ptCard(tier,it,copy,v,ptype){", 1)
    html = html.replace(
        "var shop=(it&&it.affiliate_url)?('<a class=\"pt-shop\" href=\"'+it.affiliate_url+'\" target=\"_blank\" rel=\"nofollow sponsored noopener\">Shop &#9656;</a>'):'';",
        "var term=(it&&it.part_number)?((it.brand?it.brand+' ':'')+it.part_number+' '+(ptype||'')):((v?(v.year+' '+v.make+' '+v.model+' '):'')+(ptype||''));var pn=(it&&it.part_number)?it.part_number:term;var shop=(typeof affRow==='function')?affRow(v,term,pn):'';", 1)
    html = html.replace("return ptCard(t,byTier[t]||null,u[t]);",
                        "return ptCard(t,byTier[t]||null,u[t],v,u.t);", 1)
    # 5) DTC fixes: shop the named component + one FTC note at the top of the block
    html = html.replace(
        "+'<div class=\"dtc-fix-meta\">avg '+cost+(sev?' &middot; '+sev:'')+'</div>'",
        "+'<div class=\"dtc-fix-meta\">avg '+cost+(sev?' &middot; '+sev:'')+'</div>'+(typeof affDtcShop==='function'?affDtcShop(f.fix):'')", 1)
    html = html.replace(
        "<span class=\"dtc-fix-src\">(ranked by reported success)</span></div>'+rows",
        "<span class=\"dtc-fix-src\">(ranked by reported success)</span></div>'+(typeof affFtc==='function'?affFtc():'')+rows", 1)
    return html


def main():
    if not os.path.exists(OUT_FILE):
        print(f"ERROR: {OUT_FILE} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("Building data from DB...")
    vlist, dtc, fixes, with_comps = build_data(cur)
    conn.close()

    data_json = json.dumps({"v": vlist, "dtc": dtc, "fixes": fixes}, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")        # can't break out of <script>
    print(f"Data JSON: {len(data_json)/1024/1024:.2f} MB  | vehicles={len(vlist)}  with complaints={with_comps}")

    # back up the existing demo
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(OUT_FILE, f"{OUT_FILE}.{stamp}.bak")

    # The demo declares <meta charset="UTF-8"> but the original bytes are cp1252
    # (e.g. 0xB7 mid-dots), which renders as mojibake. Read robustly (utf-8, then
    # cp1252) and we'll write genuine UTF-8 so bytes match the declared charset.
    raw = open(OUT_FILE, "rb").read()
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("cp1252")

    # 1) swap the embedded data, bounded by the data <script> (no fragile regex)
    start = html.find("const __D__=")
    sci = html.find("</script>", start)
    html = html[:start] + "const __D__=" + data_json + ";\n" + html[sci:]

    # 2) inject the Complaints tab + VIN decode + OBD-II UI (once each)
    html = inject_tab(html)
    html = inject_vin(html)
    html = inject_obd(html)
    html = inject_parttiers(html)
    html = inject_youtube(html)
    html = inject_guides(html)
    html = inject_identify(html)
    html = inject_partial(html)
    html = inject_kbb(html)
    html = inject_fixrates(html)
    html = inject_affiliate(html)
    html = inject_branding(html)
    html = fix_js_quotes(html)

    # 3) refresh the badge
    makes = len(set(v["make"] for v in vlist))
    badge = f"{len(vlist)} VEHICLES · {makes} MAKES · {len(dtc)} DTC CODES · {with_comps} WITH COMPLAINTS"
    html = re.sub(r'(<div class="db-badge">)[^<]*(</div>)', lambda m: m.group(1) + badge + m.group(2), html, count=1)
    html = ascii_polish(html)   # truly last: guarantee pure ASCII outside data (badge included)

    with open(OUT_FILE, "wb") as f:
        f.write(html.encode("utf-8"))     # genuine UTF-8, matching the meta charset

    size = os.path.getsize(OUT_FILE)
    print("\n--- Done ---------------------------")
    print(f"Output: {OUT_FILE}  ({size/1024/1024:.2f} MB)")
    print(f"Complaints tab injected: {'yes' if SENTINEL in html else 'already present'}")


if __name__ == "__main__":
    main()
