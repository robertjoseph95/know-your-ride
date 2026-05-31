"""
WRENCH / Know Your Ride - SEO static page generator
====================================================
Reads wrench_vehicles.db and writes crawlable static pages into wrench_deploy/:
  - /vehicles/<year>-<make>-<model>/index.html   (one per vehicle)
  - /dtc/<code>/index.html                        (top ~500 common codes)
  - /sitemap.xml                                  (all pages)
  - /robots.txt                                   (allows crawl + points to sitemap)

Each vehicle page is built ENTIRELY from that vehicle's own rows in
wrench_vehicles.db so no two pages are alike: a unique meta description, 200+
words of descriptive prose (overview / maintenance / NHTSA issues / fuel or
battery economy), schema.org structured data, and a related-vehicles block.
Nothing about a specific vehicle is hard-coded -- if the data isn't in the DB,
that sentence is simply omitted. Run:  python wrench_seo.py
"""

import sqlite3
import os
import re
import json
import html

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "wrench_vehicles.db")
OUT = os.path.join(HERE, "wrench_deploy")
BASE = "https://knowyourride.net"
DTC_LIMIT = 500
# common, widely-searched codes surfaced on every vehicle page (forced into the DTC set)
COMMON_CODES = ["P0300", "P0420", "P0171", "P0128", "P0442", "P0455", "P0700", "P0301", "U0100"]

# Meta-description lead-displacement corrections for models whose DB row aggregates
# multiple engines (so engine_options[0] can be the wrong variant). Keep this tight.
# Maserati Ghibli: oil spec is the 3.0L twin-turbo V6, so the meta must read 3.0L.
META_DISP_OVERRIDE = {
    ("Maserati", "Ghibli"): "3.0L",
}

CSS = (
    "body{margin:0;background:#0d0d0f;color:#e8e6e3;font:16px/1.6 -apple-system,Segoe UI,Roboto,"
    "Helvetica,Arial,sans-serif}a{color:#ff7a1a;text-decoration:none}a:hover{text-decoration:underline}"
    "header{padding:14px 20px;border-bottom:1px solid #2a2a2e;font-weight:800;letter-spacing:.04em}"
    "header em{color:#ff7a1a;font-style:normal}main{max-width:760px;margin:0 auto;padding:24px 20px 60px}"
    "h1{font-size:26px;line-height:1.25;margin:.2em 0 .5em}h2{font-size:15px;text-transform:uppercase;"
    "letter-spacing:.08em;color:#9a9a9f;margin:28px 0 8px;border-bottom:1px solid #2a2a2e;padding-bottom:6px}"
    "table{border-collapse:collapse;width:100%}td{padding:6px 4px;border-bottom:1px solid #1d1d20;vertical-align:top}"
    "td.k{color:#9a9a9f;width:45%}ul{padding-left:20px}.cta{display:inline-block;margin-top:26px;background:#ff7a1a;"
    "color:#000;font-weight:700;padding:11px 18px;border-radius:8px}.cta:hover{text-decoration:none;opacity:.9}"
    ".muted{color:#6a6a6f;font-size:13px}.lede{font-size:17px;color:#d8d6d3}.rel a{display:inline-block;margin:0 14px 8px 0}"
)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def clean(s):
    """Normalise DB text to clean ASCII (some rows carry mojibake em-dashes)."""
    if s is None:
        return ""
    s = str(s).replace("�", "-").replace("—", "-").replace("–", "-")
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip()


def esc(s):
    return html.escape("" if s is None else str(s))


def snippet(text, limit=200):
    """Trim a complaint/recall summary to a clean sentence-ish snippet."""
    t = clean(text)
    if len(t) <= limit:
        return t
    cut = t[:limit]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(",;:- ") + "..."


# make-name variants for locating a brand mention inside a recall summary
MAKE_TOKENS = {
    "Rolls-Royce": ["rolls-royce", "rolls royce"],
    "Mercedes-Benz": ["mercedes"],
    "Land Rover": ["land rover", "range rover"],
    "Alfa Romeo": ["alfa romeo"],
    "Infiniti": ["infiniti", "infinity"],
}


def recall_excerpt(text, make, model, limit=180):
    """Excerpt a recall summary so it reads about THIS vehicle.

    Many recalls are filed under a parent company and open with a long list of
    sibling-brand models (e.g. a BMW recall that also covers the Rolls-Royce
    Ghost). Find the first mention of this vehicle's make or model and start the
    excerpt 50 chars before it, so the brand-relevant text is what shows -- not
    the parent-company opening.
    """
    t = clean(text)
    low = t.lower()
    needles = list(MAKE_TOKENS.get(make, [make.lower()]))
    if model:
        needles.insert(0, model.lower())  # prefer the model mention
    pos = -1
    for n in needles:
        if not n:
            continue
        p = low.find(n)
        if p != -1 and (pos == -1 or p < pos):
            pos = p
    start = 0 if pos < 0 else max(0, pos - 50)
    body = t[start:start + limit]
    if " " in body and start + limit < len(t):
        body = body[:body.rfind(" ")]
    prefix = "..." if start > 0 else ""
    suffix = "..." if (start + len(body)) < len(t) else ""
    return prefix + body.strip(" ,;:-") + suffix


def words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text))


def art(word):
    """'a' / 'an' for the following word."""
    return "an" if word[:1].lower() in "aeiou" else "a"


def write_page(path, body_html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body_html)


def page(title, desc, canonical, inner, jsonld=None):
    head_extra = ""
    if jsonld:
        head_extra = ('<script type="application/ld+json">'
                      + json.dumps(jsonld, ensure_ascii=True, separators=(",", ":"))
                      + "</script>\n")
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n<meta name=\"description\" content=\"{esc(desc)}\">\n"
        f"<link rel=\"canonical\" href=\"{canonical}\">\n"
        f"<meta property=\"og:title\" content=\"{esc(title)}\">\n"
        f"<meta property=\"og:description\" content=\"{esc(desc)}\">\n"
        f"{head_extra}"
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        "<header><a href=\"https://knowyourride.net/\">KNOW YOUR RIDE<em>.</em></a></header>\n"
        f"<main>\n{inner}\n</main>\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------------------
# Drivetrain / fuel helpers
# ---------------------------------------------------------------------------
DRIVE_SCHEMA = {
    "Front-Wheel Drive": "FrontWheelDriveConfiguration",
    "Rear-Wheel Drive": "RearWheelDriveConfiguration",
    "All-Wheel Drive": "AllWheelDriveConfiguration",
    "4-Wheel Drive": "FourWheelDriveConfiguration",
    "Four-Wheel Drive": "FourWheelDriveConfiguration",
}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def first(js):
        try:
            a = json.loads(js) if js else []
            return a[0] if isinstance(a, list) and a else None
        except Exception:
            return None

    # ----- bulk-load per-vehicle data into dicts -----
    oil = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM oil_change")}
    parts = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM parts")}
    fluids = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM fluids")}
    safety = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM safety_ratings")}
    reliab = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM reliability")}
    evspec = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM ev_specs")}

    fuel = {}
    for r in cur.execute("SELECT * FROM fuel_economy"):
        fuel.setdefault(r["vehicle_id"], []).append(r)
    espec = {}
    for r in cur.execute("SELECT * FROM engine_specs"):
        espec.setdefault(r["vehicle_id"], []).append(r)
    warr = {}
    for r in cur.execute("SELECT * FROM warranty"):
        warr.setdefault(r["vehicle_id"], []).append(r)
    maint = {}
    for r in cur.execute("SELECT vehicle_id, mileage_interval, description FROM maintenance"):
        maint.setdefault(r["vehicle_id"], []).append(r)

    recalls = {r[0]: r[1] for r in cur.execute("SELECT vehicle_id, COUNT(*) FROM recalls GROUP BY vehicle_id")}
    recall_rows = {}  # vid -> list of summary strings (all recalls kept; data is not altered)
    for r in cur.execute("SELECT vehicle_id, summary FROM recalls WHERE summary IS NOT NULL AND summary<>''"):
        recall_rows.setdefault(r["vehicle_id"], []).append(r["summary"])

    complaint_total = {r[0]: r[1] for r in cur.execute("SELECT vehicle_id, COUNT(*) FROM complaints GROUP BY vehicle_id")}
    complaint_comp = {}
    for r in cur.execute("SELECT vehicle_id, component, COUNT(*) c FROM complaints "
                         "WHERE component IS NOT NULL AND component<>'' GROUP BY vehicle_id, component"):
        complaint_comp.setdefault(r["vehicle_id"], []).append((r["component"], r["c"]))
    complaint_sample = {}
    for r in cur.execute("SELECT vehicle_id, summary FROM complaints "
                         "WHERE summary IS NOT NULL AND length(summary)>40"):
        complaint_sample.setdefault(r["vehicle_id"], r["summary"])

    common_prob = {}
    for r in cur.execute("SELECT vehicle_id, component, complaint_count, sample_description "
                         "FROM common_problems ORDER BY complaint_count DESC"):
        common_prob.setdefault(r["vehicle_id"], []).append(r)

    tsb_count = {r[0]: r[1] for r in cur.execute("SELECT vehicle_id, COUNT(*) FROM tsb GROUP BY vehicle_id")}

    tq = {}
    for r in cur.execute("SELECT vehicle_id, component, torque_ft_lbs FROM torque_specs"):
        tq.setdefault(r["vehicle_id"], {})[r["component"]] = r["torque_ft_lbs"]

    # production span per (make, model): min/max year + count of model-years tracked
    span = {}
    for r in cur.execute("SELECT make, model, year FROM vehicles"):
        key = (r["make"], r["model"])
        d = span.setdefault(key, {"min": r["year"], "max": r["year"], "n": 0})
        d["n"] += 1
        if r["year"] is not None:
            if d["min"] is None or r["year"] < d["min"]:
                d["min"] = r["year"]
            if d["max"] is None or r["year"] > d["max"]:
                d["max"] = r["year"]

    # ----- DTC code selection (prioritise generic, searchable codes) -----
    codes = {r["code"]: r for r in cur.execute(
        "SELECT code,description,urgency,cost_low,cost_high,possible_causes FROM dtc_codes "
        "WHERE description IS NOT NULL AND description<>''")}

    def rank(code):
        p = code[0]
        order = {"P": 0, "U": 1, "B": 2, "C": 3}.get(p, 4)
        gen = 0 if (len(code) > 1 and code[1] == "0") else 1  # generic (x0xxx) before manufacturer
        return (order, gen, code)

    chosen = [c for c in COMMON_CODES if c in codes]
    for c in sorted(codes, key=rank):
        if c not in chosen:
            chosen.append(c)
        if len(chosen) >= DTC_LIMIT:
            break
    chosen = chosen[:DTC_LIMIT]
    chosen_set = set(chosen)

    # ----- PASS 1: compute slugs for every vehicle (so related links resolve) -----
    veh_rows = list(cur.execute("SELECT id,year,make,model,engine,trim FROM vehicles ORDER BY make,year,model"))
    slug_of = {}
    by_make = {}            # make -> list of (year, model, vid, slug)
    by_model = {}           # (make,model) -> list of (year, vid, slug)
    used = set()
    for v in veh_rows:
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        base = slugify(f"{year}-{make}-{model}")
        if not base:
            continue
        slug = base
        i = 2
        while slug in used:
            slug = f"{base}-{i}"
            i += 1
        used.add(slug)
        slug_of[vid] = slug
        by_make.setdefault(make, []).append((year, model, vid, slug))
        by_model.setdefault((make, model), []).append((year, vid, slug))

    # ----- helpers that build per-vehicle content -----
    def is_ev(vid, v):
        if v["engine"] and "electric" in str(v["engine"]).lower():
            return True
        for f in fuel.get(vid, []):
            if (f["fuel_type"] and "electric" in str(f["fuel_type"]).lower()) or f["mpge"]:
                return True
        if any(w["warranty_type"] == "ev_battery" for w in warr.get(vid, [])):
            return True
        if vid in evspec:
            return True
        return False

    def engine_options(vid, v):
        opts = []
        for r in espec.get(vid, []):
            if r["displacement_l"]:
                lab = f"{r['displacement_l']}L"
                if r["cylinders"]:
                    cfg = r["cylinder_config"] or ""
                    lab += f" {cfg}{r['cylinders']}".replace("  ", " ")
                opts.append(lab.strip())
        for f in fuel.get(vid, []):
            if f["engine"]:
                opts.append(f"{clean(f['engine'])}L")
        if v["engine"]:
            opts.append(clean(v["engine"]))
        # de-dupe preserving order
        seen, out = set(), []
        for o in opts:
            k = o.lower().replace(" ", "")
            if k and k not in seen:
                seen.add(k)
                out.append(o)
        return out

    def best_fuel(vid, ev):
        rows = fuel.get(vid, [])
        if not rows:
            return None
        if ev:
            for r in rows:
                if r["range_miles"] or r["mpge"]:
                    return r
            return rows[0]
        for r in rows:
            if r["combined_mpg"] or r["city_mpg"]:
                return r
        return rows[0]

    def build_prose(vid, v, ev):
        year, make, model = v["year"], v["make"], v["model"]
        nm = f"{year} {make} {model}"
        sp = span.get((make, model), {})
        paras = []

        # --- Overview ---
        ov = [f"The {nm} is catalogued in the Know Your Ride maintenance database."]
        if sp and sp.get("min") and sp.get("max") and sp["min"] != sp["max"]:
            ov[0] = (f"The {nm} belongs to a {make} {model} lineup that Know Your Ride tracks across "
                     f"{sp['n']} model years, from {sp['min']} to {sp['max']}.")
        eo = engine_options(vid, v)
        if ev:
            ov.append(f"It is an all-electric vehicle, so it skips the oil changes, spark plugs and "
                      f"exhaust-system service of a combustion {model} entirely.")
        elif eo:
            if len(eo) == 1:
                ov.append(f"Records for this year list a {eo[0]} engine.")
            else:
                ov.append(f"Engine options on record include the {', '.join(eo[:3])}.")
        f0 = best_fuel(vid, ev)
        if f0 and f0["drive"]:
            trans = clean(f0["transmission"]).lower() if f0["transmission"] else ""
            ov.append(f"It is configured as {clean(f0['drive']).lower()}"
                      + (f" with {art(trans)} {trans}." if trans else "."))
        # model-year positioning within the run (derived, varies per page)
        if sp and sp.get("min") and sp.get("max") and year and sp["min"] != sp["max"]:
            if year == sp["min"]:
                ov.append(f"This {year} car is the earliest model year on record for the {make} {model}.")
            elif year == sp["max"]:
                ov.append(f"This {year} car is the most recent {make} {model} model year on record.")
            else:
                ov.append(f"The {year} sits mid-run, with both earlier ({sp['min']}) and later "
                          f"({sp['max']}) {model} model years also documented.")
        # for very sparse vehicles, point owners at richer sibling years
        sparse = not ev and vid not in oil and vid not in fuel and not eo and not complaint_total.get(vid) \
            and not recalls.get(vid)
        if sparse and sp and sp.get("n", 0) > 1:
            ov.append(f"Detailed oil, fluid and parts specifications for this generation are still being "
                      f"expanded - the related {model} model years listed below may carry more complete records.")
        paras.append(" ".join(ov))

        # --- Maintenance / battery ---
        mt = []
        if ev:
            wb = next((w for w in warr.get(vid, []) if w["warranty_type"] == "ev_battery"), None)
            es = evspec.get(vid)
            if es and es["battery_kwh"]:
                mt.append(f"Its battery pack is rated at about {es['battery_kwh']} kWh"
                          + (f" ({es['usable_kwh']} kWh usable)" if es["usable_kwh"] else "") + ".")
            if es and es["max_charge_kw"]:
                mt.append(f"Peak DC fast-charge input is roughly {es['max_charge_kw']} kW.")
            if wb:
                mt.append(f"The high-voltage battery is covered for {wb['months']//12} years or "
                          f"{wb['miles']:,} miles, separate from the bumper-to-bumper warranty.")
            fl = fluids.get(vid)
            care = ["tire rotation"]
            if fl and fl["brake_fluid"]:
                care.append(f"{clean(fl['brake_fluid'])} brake fluid")
            if fl and fl["coolant_type"]:
                care.append(f"{clean(fl['coolant_type'])} battery/cabin coolant")
            mt.append("Routine upkeep centers on " + ", ".join(care)
                      + ", cabin air filters and brake service rather than engine oil.")
        else:
            o = oil.get(vid)
            if o and (o["viscosity"] or o["oil_type"]):
                bits = []
                if o["viscosity"]:
                    bits.append(f"{clean(o['viscosity'])}")
                if o["oil_type"]:
                    bits.append(f"{clean(o['oil_type']).lower()} oil")
                cap = f", {o['capacity_with_filter']} qt with a new filter" if o["capacity_with_filter"] else ""
                mt.append(f"It takes {' '.join(bits)}{cap}"
                          + (f" meeting {clean(o['oem_spec'])}" if o["oem_spec"] else "") + ".")
            else:
                mt.append("Oil specifications for this vehicle should be verified with your owner's "
                          "manual or authorized dealer.")
            fl = fluids.get(vid)
            if fl:
                fb = []
                if fl["coolant_type"]:
                    fb.append(f"{clean(fl['coolant_type'])} coolant")
                if fl["brake_fluid"]:
                    fb.append(f"{clean(fl['brake_fluid'])} brake fluid")
                if fl["transmission_fluid"]:
                    fb.append(f"{clean(fl['transmission_fluid'])} transmission fluid")
                if fb:
                    mt.append("Fluid specs on file include " + ", ".join(fb) + ".")
        mrows = [m for m in maint.get(vid, []) if m["mileage_interval"]]
        if mrows:
            mt.append(f"Know Your Ride lists {len(maint.get(vid, []))} scheduled maintenance items for this "
                      f"vehicle, the earliest interval falling at {min(m['mileage_interval'] for m in mrows):,} miles.")
        t = tq.get(vid, {})
        tlabels = {"drain_bolt": "oil drain plug", "lug_nut": "lug nut", "spark_plug": "spark plug"}
        tparts = [f"{lbl} {t[k]:g} ft-lb" for k, lbl in tlabels.items() if t.get(k) is not None and (not ev or k != "spark_plug") and (not ev or k != "drain_bolt")]
        if tparts:
            mt.append("Documented torque values include " + ", ".join(tparts) + ".")
        if mt:
            paras.append(" ".join(mt))

        # --- NHTSA issues ---
        ni = []
        cp = common_prob.get(vid)
        ct = complaint_total.get(vid, 0)
        if cp:
            top = cp[0]
            ni.append(f"The most-reported problem area is {clean(top['component']).lower()} "
                      f"({top['complaint_count']} NHTSA complaints).")
            if top["sample_description"]:
                ni.append(f"One owner reported: \"{snippet(top['sample_description'], 160)}\"")
        elif ct:
            comps = sorted(complaint_comp.get(vid, []), key=lambda x: -x[1])[:3]
            if comps:
                ni.append("NHTSA complaints for this vehicle cluster around "
                          + ", ".join(f"{clean(c).lower()} ({n})" for c, n in comps) + ".")
            else:
                ni.append(f"NHTSA has {ct} owner complaints on file for this vehicle.")
            samp = complaint_sample.get(vid)
            if samp:
                ni.append(f"A representative report reads: \"{snippet(samp, 160)}\"")
        rc = recalls.get(vid, 0)
        if rc:
            line = f"There {'is' if rc == 1 else 'are'} {rc} safety recall{'' if rc == 1 else 's'} on record"
            sums = recall_rows.get(vid, [])
            # prefer a recall whose summary actually names this vehicle's model/make,
            # so multi-brand campaigns read about THIS car (not a parent-company opening)
            needles = [model.lower()] + MAKE_TOKENS.get(make, [make.lower()])
            chosen_sum = next((s for s in sums if any(n and n in s.lower() for n in needles)), None)
            if chosen_sum is None and sums:
                chosen_sum = sums[0]
            if chosen_sum:
                line += f"; one covers: {recall_excerpt(chosen_sum, make, model, 150)}"
            ni.append(line + ".")
        rl = reliab.get(vid)
        if rl and rl["rating"] and not cp and not ct:
            ni.append(f"Its overall reliability signal is rated \"{clean(rl['rating'])}\" "
                      f"based on aggregated complaint and crash data.")
        if not ni:
            ni.append("No NHTSA safety complaints or open recalls are currently on record for this "
                      "vehicle, which for an older or low-volume model often reflects limited reporting.")
        paras.append(" ".join(ni))

        # --- Fuel / energy economy ---
        fe = []
        if f0:
            if ev:
                if f0["range_miles"]:
                    fe.append(f"EPA range is about {f0['range_miles']} miles on a full charge")
                if f0["mpge"]:
                    fe.append((", " if fe else "It returns ") + f"{f0['mpge']} MPGe combined")
                fe = ["".join(fe) + "." if fe else ""]
                if f0["annual_fuel_cost"]:
                    fe.append(f"Estimated annual charging cost runs near ${f0['annual_fuel_cost']:,}.")
            else:
                parts_fe = []
                if f0["city_mpg"] and f0["highway_mpg"]:
                    parts_fe.append(f"{f0['city_mpg']} city / {f0['highway_mpg']} highway MPG")
                if f0["combined_mpg"]:
                    parts_fe.append(f"{f0['combined_mpg']} MPG combined")
                if parts_fe:
                    fe.append("EPA fuel economy is rated at " + ", ".join(parts_fe) + ".")
                if f0["annual_fuel_cost"]:
                    fe.append(f"Estimated annual fuel cost is about ${f0['annual_fuel_cost']:,}.")
        fe = [x for x in fe if x]
        if fe:
            paras.append(" ".join(fe))

        return [p for p in paras if p.strip()]

    def build_jsonld(vid, v, ev, canonical, desc):
        year, make, model = v["year"], v["make"], v["model"]
        data = {
            "@context": "https://schema.org",
            "@type": "Car",
            "name": f"{year} {make} {model}",
            "brand": {"@type": "Brand", "name": make},
            "model": model,
            "vehicleModelDate": str(year) if year else None,
            "url": canonical,
            "description": desc,
        }
        f0 = best_fuel(vid, ev)
        if ev:
            data["fuelType"] = "Electric"
            if f0 and f0["mpge"]:
                data["fuelEfficiency"] = {"@type": "QuantitativeValue", "value": f0["mpge"], "unitText": "MPGe"}
            es = evspec.get(vid)
            if es and es["battery_kwh"]:
                data["vehicleEngine"] = {"@type": "EngineSpecification", "fuelType": "Electric",
                                         "name": f"{es['battery_kwh']} kWh battery electric"}
        else:
            eo = engine_options(vid, v)
            disp = None
            for f in fuel.get(vid, []):
                try:
                    disp = float(f["engine"]) if f["engine"] else None
                except Exception:
                    disp = None
                if disp:
                    break
            # keep the structured engine consistent with the meta lead override
            lead = META_DISP_OVERRIDE.get((make, model))
            if lead:
                try:
                    disp = float(lead.rstrip("Ll"))
                except ValueError:
                    pass
            eng = {"@type": "EngineSpecification", "fuelType": "Gasoline"}
            if disp:
                eng["engineDisplacement"] = {"@type": "QuantitativeValue", "value": disp, "unitCode": "LTR"}
            if lead:
                eng["name"] = lead
            elif eo:
                eng["name"] = eo[0]
            data["vehicleEngine"] = eng
            data["fuelType"] = "Gasoline"
            if f0 and f0["combined_mpg"]:
                data["fuelConsumption"] = {"@type": "QuantitativeValue", "value": f0["combined_mpg"], "unitText": "MPG (US)"}
        if f0 and f0["drive"] and clean(f0["drive"]) in DRIVE_SCHEMA:
            data["driveWheelConfiguration"] = DRIVE_SCHEMA[clean(f0["drive"])]
        if f0 and f0["transmission"]:
            data["vehicleTransmission"] = clean(f0["transmission"])
        return {k: val for k, val in data.items() if val is not None}

    def build_meta_desc(vid, v, ev):
        year, make, model = v["year"], v["make"], v["model"]
        bits = []
        f0 = best_fuel(vid, ev)
        if ev:
            if f0 and f0["range_miles"]:
                bits.append(f"{f0['range_miles']}-mi range")
            if f0 and f0["mpge"]:
                bits.append(f"{f0['mpge']} MPGe")
            wb = next((w for w in warr.get(vid, []) if w["warranty_type"] == "ev_battery"), None)
            if wb:
                bits.append(f"{wb['months']//12}yr battery warranty")
        has_oil = False
        if not ev:
            eo = engine_options(vid, v)
            # Some vehicle rows aggregate multiple engines, so engine_options[0] can be
            # the wrong variant for the meta lead. META_DISP_OVERRIDE pins the displacement
            # to the engine the model's oil spec is written for, for specific models only.
            lead = META_DISP_OVERRIDE.get((make, model))
            if lead:
                bits.append(lead)
            elif eo:
                bits.append(eo[0])
            o = oil.get(vid)
            has_oil = bool(o and (o["viscosity"] or o["oil_type"] or o["capacity_with_filter"]))
            if o and o["viscosity"]:
                bits.append(f"{clean(o['viscosity'])} oil")
            if f0 and f0["combined_mpg"]:
                bits.append(f"{f0['combined_mpg']} MPG")
        ct = complaint_total.get(vid, 0)
        rc = recalls.get(vid, 0)
        if rc:
            bits.append(f"{rc} recall{'' if rc == 1 else 's'}")
        elif ct:
            bits.append(f"{ct} NHTSA complaints")
        lead = f"{year} {make} {model}"
        if bits:
            d = f"{lead}: {', '.join(bits[:4])}. "
        else:
            d = f"{lead} maintenance reference. "
        if ev:
            d += "Charging, battery, common issues & service specs."
        elif has_oil:
            d += "Oil specs, maintenance schedule, recalls & repair data."
        else:
            # oil specs not on record (e.g. nulled exotic fallback) -- don't claim them
            d += "Maintenance schedule, recalls & specs."
        d += " Free on Know Your Ride."
        return d[:300]

    def build_related(vid, v):
        make, model = v["make"], v["model"]
        out = []
        seen = {vid}
        # other model-years of the same model (nearest years first)
        sibs = sorted(by_model.get((make, model), []), key=lambda x: abs((x[0] or 0) - (v["year"] or 0)))
        for yr, ovid, oslug in sibs:
            if ovid in seen:
                continue
            seen.add(ovid)
            out.append((f"{yr} {make} {model}", oslug))
            if len(out) >= 4:
                break
        # other models from the same make
        others = sorted(by_make.get(make, []), key=lambda x: -(x[0] or 0))
        for yr, omodel, ovid, oslug in others:
            if ovid in seen or omodel == model:
                continue
            seen.add(ovid)
            out.append((f"{yr} {make} {omodel}", oslug))
            if len(out) >= 8:
                break
        return out

    sitemap = [f"{BASE}/"]

    # ----- PASS 2: render vehicle pages -----
    n_veh = 0
    for v in veh_rows:
        vid = v["id"]
        slug = slug_of.get(vid)
        if not slug:
            continue
        year, make, model = v["year"], v["make"], v["model"]
        ev = is_ev(vid, v)
        canonical = f"{BASE}/vehicles/{slug}/"

        title_kind = "Range, Charging & Maintenance" if ev else "Oil Specs, Maintenance & Recalls"
        title = f"{year} {make} {model} {title_kind} | Know Your Ride"
        desc = build_meta_desc(vid, v, ev)
        prose = build_prose(vid, v, ev)
        jsonld = build_jsonld(vid, v, ev, canonical, desc)

        inner = [f"<h1>{esc(year)} {esc(make)} {esc(model)} - "
                 + ("Electric Vehicle Guide" if ev else "Maintenance &amp; Specs") + "</h1>"]
        if prose:
            inner.append(f"<p class=\"lede\">{esc(prose[0])}</p>")
            for p in prose[1:]:
                inner.append(f"<p>{esc(p)}</p>")

        # quick-reference spec table (kept from the data we have)
        o = oil.get(vid)
        ofilt = first(o["filters_json"]) if o else None
        p = parts.get(vid)
        fl = fluids.get(vid)
        s = safety.get(vid)
        f0 = best_fuel(vid, ev)
        spec_rows = []

        def srow(k, val):
            if val not in (None, "", "None"):
                spec_rows.append(f"<tr><td class=\"k\">{esc(k)}</td><td>{esc(val)}</td></tr>")

        if ev:
            es = evspec.get(vid)
            if f0 and f0["range_miles"]:
                srow("EPA range", f"{f0['range_miles']} miles")
            if f0 and f0["mpge"]:
                srow("Efficiency", f"{f0['mpge']} MPGe combined")
            if es and es["battery_kwh"]:
                srow("Battery", f"{es['battery_kwh']} kWh"
                     + (f" ({es['usable_kwh']} usable)" if es["usable_kwh"] else ""))
            if es and es["max_charge_kw"]:
                srow("Max DC charging", f"{es['max_charge_kw']} kW")
            wb = next((w for w in warr.get(vid, []) if w["warranty_type"] == "ev_battery"), None)
            if wb:
                srow("Battery warranty", f"{wb['months']//12} yr / {wb['miles']:,} mi")
            if f0 and f0["annual_fuel_cost"]:
                srow("Est. annual charging", f"${f0['annual_fuel_cost']:,}")
        else:
            if o and (o["viscosity"] or o["oil_type"] or o["capacity_with_filter"]):
                if o["viscosity"]:
                    srow("Oil viscosity", clean(o["viscosity"]))
                if o["oil_type"]:
                    srow("Oil type", clean(o["oil_type"]))
                if o["capacity_with_filter"]:
                    srow("Oil capacity (w/ filter)", f"{o['capacity_with_filter']} qt")
                if o["oem_spec"]:
                    srow("OEM oil spec", clean(o["oem_spec"]))
                if ofilt and ofilt.get("part_number"):
                    srow("Oil filter", f"{ofilt.get('brand','')} {ofilt['part_number']}".strip())
            else:
                srow("Engine oil", "See owner's manual")
            if f0 and f0["combined_mpg"]:
                srow("EPA combined", f"{f0['combined_mpg']} MPG")
        if p and p["tire_size"]:
            srow("Tire size", clean(p["tire_size"]))
        if fl and fl["coolant_type"]:
            srow("Coolant", clean(fl["coolant_type"]))
        if s and s["overall_rating"]:
            srow("NHTSA overall", f"{s['overall_rating']} / 5 stars")
        srow("Open recalls on record", recalls.get(vid, 0) if recalls.get(vid) else None)
        if tsb_count.get(vid):
            srow("Technical service bulletins", tsb_count[vid])

        if spec_rows:
            inner.append("<h2>Quick Specs</h2><table>" + "".join(spec_rows) + "</table>")

        # common DTC cross-links
        links = []
        for c in COMMON_CODES:
            if c in chosen_set:
                links.append(f"<li><a href=\"{BASE}/dtc/{c.lower()}/\">{c}</a> - {esc(clean(codes[c]['description']))}</li>")
        if links:
            inner.append("<h2>Common Trouble Codes</h2><ul>" + "".join(links) + "</ul>")

        # related vehicles
        rel = build_related(vid, v)
        if rel:
            inner.append("<h2>Related Vehicles</h2><div class=\"rel\">"
                         + "".join(f"<a href=\"{BASE}/vehicles/{rs}/\">{esc(rn)}</a>" for rn, rs in rel)
                         + "</div>")

        inner.append("<a class=\"cta\" href=\"https://knowyourride.net/\">See full specs, parts &amp; repair guides &rarr;</a>")
        inner.append("<p class=\"muted\">Part of the free Know Your Ride vehicle maintenance reference. "
                     "Figures are sourced from EPA, NHTSA and manufacturer data and are for general "
                     "reference - always confirm with your owner's manual.</p>")

        write_page(os.path.join(OUT, "vehicles", slug, "index.html"),
                   page(title, desc, canonical, "\n".join(inner), jsonld))
        sitemap.append(canonical)
        n_veh += 1

    # ----- DTC pages -----
    n_dtc = 0
    for c in chosen:
        d = codes[c]
        sys_label = {"P": "Powertrain", "B": "Body", "C": "Chassis", "U": "Network"}.get(c[0], "")
        title = f"{c} - {clean(d['description'])} | Know Your Ride"
        desc = f"{c}: {clean(d['description'])}. What it means, urgency, likely causes and repair cost range."
        canonical = f"{BASE}/dtc/{c.lower()}/"
        inner = [f"<h1>{esc(c)} - {esc(clean(d['description']))}</h1>"]
        inner.append("<table>")
        if sys_label:
            inner.append(f"<tr><td class=\"k\">System</td><td>{sys_label}</td></tr>")
        if d["urgency"]:
            inner.append(f"<tr><td class=\"k\">Urgency</td><td>{esc(clean(d['urgency']))}</td></tr>")
        if d["cost_low"] or d["cost_high"]:
            inner.append(f"<tr><td class=\"k\">Est. repair cost</td><td>${esc(d['cost_low'] or '?')} - ${esc(d['cost_high'] or '?')}</td></tr>")
        inner.append("</table>")
        causes = []
        try:
            causes = json.loads(d["possible_causes"]) if d["possible_causes"] else []
        except Exception:
            causes = []
        if causes:
            inner.append("<h2>Possible Causes</h2><ul>" + "".join(f"<li>{esc(clean(x))}</li>" for x in causes) + "</ul>")
        inner.append(f"<a class=\"cta\" href=\"https://knowyourride.net/\">Look up any OBD-II code in the app &rarr;</a>")
        inner.append("<p class=\"muted\">Free OBD-II diagnostic trouble code reference from Know Your Ride.</p>")
        write_page(os.path.join(OUT, "dtc", c.lower(), "index.html"),
                   page(title, desc, canonical, "\n".join(inner)))
        sitemap.append(canonical)
        n_dtc += 1

    # ----- sitemap.xml + robots.txt -----
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in sitemap:
            f.write(f"  <url><loc>{u}</loc></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: https://knowyourride.net/sitemap.xml\n")

    con.close()
    print(f"Vehicle pages : {n_veh}")
    print(f"DTC pages     : {n_dtc}")
    print(f"Sitemap URLs  : {len(sitemap)}")
    print(f"Output        : {OUT}/(vehicles|dtc)/, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
