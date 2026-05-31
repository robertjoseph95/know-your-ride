"""Quick fixes: (1) Amazon-only affiliate links; (2) Toyota/Lexus/Scion drain gasket_type."""
import sqlite3, json, io, sys, datetime, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------- FIX 2: drain_bolt_json.gasket_type for Toyota/Lexus/Scion where null ----------
DB = "wrench_vehicles.db"
shutil.copy2(DB, DB + ".bak-quickfix-" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
c = sqlite3.connect(DB)
rows = c.execute("""SELECT o.vehicle_id, o.drain_bolt_json FROM oil_change o JOIN vehicles v ON v.id=o.vehicle_id
                    WHERE v.make IN ('Toyota','Lexus','Scion')""").fetchall()
GASKET = "14mm aluminum crush washer"
upd = 0
for vid, dj in rows:
    try:
        d = json.loads(dj) if dj and dj not in ("", "null") else {}
    except Exception:
        d = {}
    if not isinstance(d, dict):
        d = {}
    if not d.get("gasket_type"):
        d["gasket_type"] = GASKET
        c.execute("UPDATE oil_change SET drain_bolt_json=?, gasket=COALESCE(NULLIF(gasket,''),?) WHERE vehicle_id=?",
                  (json.dumps(d), GASKET, vid))
        upd += 1
c.commit()
print(f"FIX2: set gasket_type='{GASKET}' on {upd} Toyota/Lexus/Scion vehicles (were null)")
chk = c.execute("SELECT drain_bolt_json FROM oil_change WHERE vehicle_id=12802").fetchone()[0]
print("FIX2 Camry now:", chk)
c.close()

# ---------- FIX 1: Amazon-only affiliate links (remove RockAuto/AutoZone) ----------
REPLACES = [
    # affRow: render Amazon only (drop the RockAuto/AutoZone "more" span)
    (b"'<div class=\"aff-row\">'+amz+more+'</div>'", b"'<div class=\"aff-row\">'+amz+'</div>'"),
    # affDtcShop: drop the AutoZone span
    (b"+'<span class=\"aff-more\"><a href=\"'+affAz(comp)+'\" target=\"_blank\" rel=\"noopener\">AutoZone</a></span></div>';",
     b"+'</div>';"),
    # affFtc: Amazon-only disclosure
    (b"Amazon links are affiliate links (we may earn a commission at no extra cost to you). Other retailer links are for convenience only.",
     b"As an Amazon Associate we earn from qualifying purchases, at no extra cost to you."),
    # neutralize the RockAuto/AutoZone URL builders (no URLs generated anywhere)
    (b"function affRock(v){return v?('https://www.rockauto.com/en/catalog/'+affEnc(v.make)+','+affEnc(v.model)+','+affEnc(v.year)):'';}",
     b"function affRock(v){return '';}"),
    (b"function affAz(pn){return 'https://www.autozone.com/searchresult?searchtext='+affEnc(pn);}",
     b"function affAz(pn){return '';}"),
]
for path in ("wrench_demo.html", "files/04_rebuild_demo.py"):
    b = open(path, "rb").read()
    for old, new in REPLACES:
        cnt = b.count(old)
        assert cnt >= 1, f"[{path}] not found: {old[:50]!r}"
        b = b.replace(old, new)
    # sanity: no rendered rockauto/autozone URLs remain
    assert b.count(b"rockauto.com") == 0, f"[{path}] rockauto.com still present"
    assert b.count(b"autozone.com") == 0, f"[{path}] autozone.com still present"
    open(path, "wb").write(b)
    print(f"FIX1: {path} -> Amazon-only (rockauto.com/autozone.com removed)")
print("[quick fixes applied]")
