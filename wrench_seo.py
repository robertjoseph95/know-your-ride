"""
WRENCH / Know Your Ride - SEO static page generator
====================================================
Reads wrench_vehicles.db and writes crawlable static pages into wrench_deploy/:
  - /vehicles/<year>-<make>-<model>/index.html   (one per vehicle)
  - /dtc/<code>/index.html                        (top ~500 common codes)
  - /sitemap.xml                                  (all pages)
  - /robots.txt                                   (allows crawl + points to sitemap)

Plain semantic HTML (UTF-8, ASCII content) with meta title/description, canonical
URL, internal links back to the app. Run:  python wrench_seo.py
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
    ".muted{color:#6a6a6f;font-size:13px}"
)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def esc(s):
    return html.escape("" if s is None else str(s))


def write_page(path, body_html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body_html)


def page(title, desc, canonical, inner):
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n<meta name=\"description\" content=\"{esc(desc)}\">\n"
        f"<link rel=\"canonical\" href=\"{canonical}\">\n"
        f"<meta property=\"og:title\" content=\"{esc(title)}\">\n"
        f"<meta property=\"og:description\" content=\"{esc(desc)}\">\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        "<header><a href=\"https://knowyourride.net/\">KNOW YOUR RIDE<em>.</em></a></header>\n"
        f"<main>\n{inner}\n</main>\n</body>\n</html>\n"
    )


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

    oil = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM oil_change")}
    parts = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM parts")}
    safety = {r["vehicle_id"]: r for r in cur.execute("SELECT * FROM safety_ratings")}
    recalls = {r[0]: r[1] for r in cur.execute("SELECT vehicle_id, COUNT(*) FROM recalls GROUP BY vehicle_id")}
    tq = {}
    for r in cur.execute("SELECT vehicle_id, component, torque_ft_lbs FROM torque_specs"):
        tq.setdefault(r["vehicle_id"], {})[r["component"]] = r["torque_ft_lbs"]

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

    sitemap = [f"{BASE}/"]

    # ----- vehicle pages -----
    used = set()
    n_veh = 0
    for v in cur.execute("SELECT id,year,make,model FROM vehicles ORDER BY make,year,model"):
        vid, year, make, model = v["id"], v["year"], v["make"], v["model"]
        slug = slugify(f"{year}-{make}-{model}")
        if not slug:
            continue
        base_slug = slug
        i = 2
        while slug in used:
            slug = f"{base_slug}-{i}"; i += 1
        used.add(slug)

        o = oil.get(vid)
        p = parts.get(vid)
        s = safety.get(vid)
        t = tq.get(vid, {})
        ofilt = first(o["filters_json"]) if o else None

        rows = []
        def row(k, val):
            if val not in (None, "", "None"):
                rows.append(f"<tr><td class=\"k\">{esc(k)}</td><td>{esc(val)}</td></tr>")
        oil_rows = []
        if o:
            row_local = lambda k, val: oil_rows.append(f"<tr><td class=\"k\">{esc(k)}</td><td>{esc(val)}</td></tr>") if val not in (None, "", "None") else None
            row_local("Oil viscosity", o["viscosity"])
            row_local("Oil type", o["oil_type"])
            row_local("Capacity (with filter)", f"{o['capacity_with_filter']} qt" if o["capacity_with_filter"] else None)
            row_local("OEM spec", o["oem_spec"])
            if ofilt and ofilt.get("part_number"):
                row_local("Oil filter", f"{ofilt.get('brand','')} {ofilt['part_number']}".strip())
        tire = p["tire_size"] if p else None
        title = f"{year} {make} {model} Oil Specs, Maintenance & More | Know Your Ride"
        desc = (f"Full maintenance specs for your {year} {make} {model} - oil viscosity, capacity, "
                "filter part numbers, torque specs and more. Free.")
        canonical = f"{BASE}/vehicles/{slug}/"

        inner = [f"<h1>{esc(year)} {esc(make)} {esc(model)} - Maintenance Specs</h1>"]
        inner.append("<h2>Oil &amp; Filter</h2>")
        inner.append("<table>" + ("".join(oil_rows) if oil_rows else "<tr><td class=\"muted\">No oil data on record.</td></tr>") + "</table>")
        inner.append("<h2>Tires</h2><table>" + (f"<tr><td class=\"k\">Tire size</td><td>{esc(tire)}</td></tr>" if tire else "<tr><td class=\"muted\">No tire data on record.</td></tr>") + "</table>")
        torque_rows = []
        labels = {"drain_bolt": "Oil drain plug", "spark_plug": "Spark plug", "lug_nut": "Lug nut"}
        for comp, lbl in labels.items():
            if t.get(comp) is not None:
                torque_rows.append(f"<tr><td class=\"k\">{lbl}</td><td>{esc(t[comp])} ft-lb</td></tr>")
        if torque_rows:
            inner.append("<h2>Torque Specs</h2><table>" + "".join(torque_rows) + "</table>")
        inner.append("<h2>Safety &amp; Recalls</h2><table>")
        if s and s["overall_rating"]:
            inner.append(f"<tr><td class=\"k\">NHTSA overall rating</td><td>{esc(s['overall_rating'])} / 5 stars</td></tr>")
        inner.append(f"<tr><td class=\"k\">Open recalls on record</td><td>{recalls.get(vid, 0)}</td></tr>")
        inner.append("</table>")
        # common DTC cross-links
        links = []
        for c in COMMON_CODES:
            if c in chosen_set:
                d = codes[c]["description"]
                links.append(f"<li><a href=\"{BASE}/dtc/{c.lower()}/\">{c}</a> - {esc(d)}</li>")
        if links:
            inner.append("<h2>Common Trouble Codes</h2><ul>" + "".join(links) + "</ul>")
        inner.append(f"<a class=\"cta\" href=\"https://knowyourride.net/\">See full specs, parts &amp; repair guides &rarr;</a>")
        inner.append("<p class=\"muted\">Part of the free Know Your Ride vehicle maintenance reference.</p>")

        write_page(os.path.join(OUT, "vehicles", slug, "index.html"),
                   page(title, desc, canonical, "\n".join(inner)))
        sitemap.append(canonical)
        n_veh += 1

    # ----- DTC pages -----
    n_dtc = 0
    for c in chosen:
        d = codes[c]
        sys_label = {"P": "Powertrain", "B": "Body", "C": "Chassis", "U": "Network"}.get(c[0], "")
        title = f"{c} - {d['description']} | Know Your Ride"
        desc = f"{c}: {d['description']}. What it means, urgency, likely causes and repair cost range."
        canonical = f"{BASE}/dtc/{c.lower()}/"
        inner = [f"<h1>{esc(c)} - {esc(d['description'])}</h1>"]
        inner.append("<table>")
        if sys_label:
            inner.append(f"<tr><td class=\"k\">System</td><td>{sys_label}</td></tr>")
        if d["urgency"]:
            inner.append(f"<tr><td class=\"k\">Urgency</td><td>{esc(d['urgency'])}</td></tr>")
        if d["cost_low"] or d["cost_high"]:
            inner.append(f"<tr><td class=\"k\">Est. repair cost</td><td>${esc(d['cost_low'] or '?')} - ${esc(d['cost_high'] or '?')}</td></tr>")
        inner.append("</table>")
        causes = []
        try:
            causes = json.loads(d["possible_causes"]) if d["possible_causes"] else []
        except Exception:
            causes = []
        if causes:
            inner.append("<h2>Possible Causes</h2><ul>" + "".join(f"<li>{esc(x)}</li>" for x in causes) + "</ul>")
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
