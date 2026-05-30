import sqlite3, requests, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
c = sqlite3.connect("wrench_vehicles.db"); c.row_factory = sqlite3.Row
S = requests.Session(); S.headers.update({"User-Agent": "KnowYourRide/1.0", "Accept": "application/json"})
BASE = "https://api.nhtsa.gov/SafetyRatings"

def gi(v):
    try:
        n = int(str(v).strip()); return n if 1 <= n <= 5 else None
    except Exception:
        return None
def gf(v):
    try: return float(str(v).strip())
    except Exception: return None

targets = c.execute("""SELECT v.id,v.year,v.make,v.model FROM vehicles v
   LEFT JOIN safety_ratings s ON s.vehicle_id=v.id
   WHERE v.year BETWEEN 2020 AND 2026 AND s.overall_rating IS NULL ORDER BY v.year DESC""").fetchall()
print(f"D5: {len(targets)} vehicles (2020-2026) missing overall_rating", flush=True)
updated = no_data = errs = 0
for i, t in enumerate(targets, 1):
    try:
        r = S.get(f"{BASE}/modelyear/{t['year']}/make/{t['make']}/model/{t['model']}", timeout=12)
        res = (r.json() or {}).get("Results") or []
        time.sleep(0.15)
        best = None
        for item in res:
            vidn = item.get("VehicleId")
            if not vidn: continue
            d = S.get(f"{BASE}/VehicleId/{vidn}", timeout=12); time.sleep(0.15)
            rr = (d.json() or {}).get("Results") or []
            if rr and gi(rr[0].get("OverallRating")) is not None:
                best = rr[0]; break
        if not best:
            no_data += 1
            if i % 25 == 0: print(f"  [{i}/{len(targets)}] updated={updated} no_data={no_data}", flush=True)
            continue
        c.execute("""INSERT OR REPLACE INTO safety_ratings
            (vehicle_id,overall_rating,frontal_crash_driver,frontal_crash_passenger,side_crash_driver,side_crash_passenger,rollover_rating,rollover_risk_pct,side_pole_rating)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (t['id'], gi(best.get("OverallRating")), gi(best.get("FrontCrashDriversideRating")),
             gi(best.get("FrontCrashPassengersideRating")), gi(best.get("SideCrashDriversideRating")),
             gi(best.get("SideCrashPassengersideRating")), gi(best.get("RolloverRating")),
             gf(best.get("RolloverPossibility")), gi(best.get("SidePoleCrashRating"))))
        c.commit(); updated += 1
        if i % 25 == 0: print(f"  [{i}/{len(targets)}] updated={updated} no_data={no_data}", flush=True)
    except Exception as e:
        errs += 1
        if errs <= 5: print(f"  err {t['year']} {t['make']} {t['model']}: {e}", flush=True)
print(f"D5 DONE: updated={updated} no_data={no_data} errs={errs}", flush=True)
c.close()
