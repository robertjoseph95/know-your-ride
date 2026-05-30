#!/usr/bin/env python3
"""
Pre-fetch frontal/side-pole crash ratings (network only; NO DB writes).

The Vehicle Finder safety-ratings endpoint returns null for frontal_crash_driver,
frontal_crash_passenger, side_pole_rating (source gap, NOT a mapping bug) — but it
DOES return nhtsa_vehicle_id, and our safety_ratings table never stored that id.
So: VF safety-ratings -> nhtsa_vehicle_id -> NHTSA SafetyRatings (authoritative)
-> frontal/pole. Cache to nhtsa_safety_cache.json for the apply phase.
Safe to run while the maintenance writer runs (reads DB once, writes a JSON file).
"""
import os, json, sqlite3, time, threading, logging
from concurrent.futures import ThreadPoolExecutor
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
OUT = os.path.join(ROOT, "nhtsa_safety_cache.json")
VF_KEY = json.load(open(os.path.join(ROOT, "wrench_config.json")))["vehicle_finder_api_key"]
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_safety_ratings_fix.log"), encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
_lock = threading.Lock()


def to_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def get_json(url, headers=None, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def vf_nhtsa_id(vid):
    d = get_json(f"https://api.vehicle-finder.com/v1/vehicles/{vid}/safety-ratings",
                 headers={"X-API-Key": VF_KEY})
    if not d or "data" not in d or d["data"] is None:
        return None
    return d["data"].get("nhtsa_vehicle_id")


def nhtsa_ratings(nid):
    d = get_json(f"https://api.nhtsa.gov/SafetyRatings/VehicleId/{nid}",
                 headers={"User-Agent": "wrench/1.0"})
    res = (d.get("Results") or [{}])[0] if d else {}
    return {"frontal_crash_driver": to_int(res.get("FrontCrashDriversideRating")),
            "frontal_crash_passenger": to_int(res.get("FrontCrashPassengersideRating")),
            "side_pole_rating": to_int(res.get("SidePoleCrashRating"))}


def main():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    vids = [r[0] for r in c.execute("SELECT vehicle_id FROM safety_ratings WHERE vehicle_id>0").fetchall()]
    c.close()
    log.info("=" * 64)
    log.info(f"SAFETY PREFETCH START: {len(vids)} safety_ratings rows (VF->nhtsa_id->NHTSA)")

    cache = {}
    done = [0]
    no_id = [0]
    t0 = time.time()

    def work(vid):
        nid = vf_nhtsa_id(vid)
        d = nhtsa_ratings(nid) if nid else None
        with _lock:
            done[0] += 1
            if nid is None:
                no_id[0] += 1
            if done[0] % 150 == 0:
                log.info(f"  {done[0]}/{len(vids)} | no_nhtsa_id={no_id[0]} | {done[0]/(time.time()-t0)*60:.0f}/min")
        return vid, d

    with ThreadPoolExecutor(max_workers=6) as ex:
        for vid, d in ex.map(work, vids):
            if d:
                cache[str(vid)] = d

    have = sum(1 for v in cache.values()
               if any(v[k] is not None for k in ("frontal_crash_driver", "frontal_crash_passenger", "side_pole_rating")))
    json.dump(cache, open(OUT, "w"))
    log.info(f"SAFETY PREFETCH DONE: {len(cache)} vehicles cached, "
             f"{have} with >=1 frontal/pole rating, {no_id[0]} had no nhtsa_vehicle_id")
    log.info(f"  -> {OUT}")
    log.info("=" * 64)


if __name__ == "__main__":
    main()
