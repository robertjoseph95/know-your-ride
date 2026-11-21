# Read-only, OFFLINE: every stored fuel-economy line of the fleet against EPA's complete record file.
#   python -I epa_bulk_compare.py <vehicles.csv.zip> <repo root> <out.json>
# Stdlib only. The zip is untrusted data: one member, read in memory, parsed as CSV. The database is opened read-only.
import sys, io, re, csv, json, zipfile, sqlite3, collections

ZIP, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

# ---------------------------------------------------------------- name rules (copied unchanged from the name sweep)
ALIAS = {("Mazda", "Mazda3"): ["3"], ("Mazda", "Mazda6"): ["6"], ("Mazda", "MX-5 Miata"): ["MX-5"], ("Volkswagen", "Golf GTI"): ["GTI"],
         ("Mercedes-Benz", "GLC 300"): ["GLC300"], ("Mercedes-Benz", "GLE 350"): ["GLE350"]}
PLAIN = set("""2wd 4wd awd fwd rwd 4x4 4x2 2dr 3dr 4dr 5dr 2-door 3-door 4-door 5-door door sedan hatchback coupe convertible wagon
pickup cab chassis van cargo passenger ffv di""".split())
SKIP = set("""quattro xdrive 4matic 4motion all4 avant cabriolet roadster sportback spyder spider sportbrake sportcombi gran turismo station soft top
2door 4door crew 4 5 le xle xse sl sr sv ltd plat platinum ultimate touring a-spec eco dynamics fe hf hx sfe hfe xfe v6 v8 v12 elite black sel r-line & manual mt
1-mode 2-mode 3-mode mode tm mud terrain tires tire gvwr>6649 gvwr>6799 gvwr>7599 lbs payload package base lt 2.7l 3.5l 5.0l inc w stop-start non-isg
1500 c1500 k1500""".split())
ALT_ATV = {"Plug-in Hybrid", "EV", "FCV", "CNG", "Bifuel (CNG)", "Bifuel (LPG)"}
FUELW = set("hybrid hev phev plug-in e-hybrid 4xe prime electric ev bev cng natural dual-fuel bi-fuel lpg fcv e-fcev fuel cell energi recharge t8 eawd e-ray e-tron".split())
COMBINED = {("Hyundai", "Accent", "brio"), ("Dodge", "Caravan", "grand caravan"), ("Dodge", "Neon", "srt-4 sx 2.0"), ("Chrysler", "300", "srt-8"),
            ("Jeep", "Wrangler", "tj"), ("Porsche", "Cayenne", "cayenne"), ("Subaru", "Impreza", "outback spt")}
PLAIN_1500 = {("Chevrolet", "Silverado 1500"), ("GMC", "Sierra 1500")}
ANOTHER = {("Nissan", "Rogue"): {"sport", "select"}, ("Nissan", "Pathfinder"): {"armada"}, ("Hyundai", "Santa Fe"): {"sport", "xl"},
           ("Hyundai", "Elantra"): {"gt"}, ("Ford", "Explorer"): {"sport"}, ("Toyota", "Camry"): {"solara"}, ("Toyota", "Corolla"): {"im"},
           ("Toyota", "Prius"): {"c", "v"}, ("Honda", "Accord"): {"crosstour"}, ("Mitsubishi", "Montero"): {"sport"}, ("Isuzu", "Rodeo"): {"sport"},
           ("Suzuki", "Grand Vitara"): {"xl7"}, ("Fiat", "500"): {"l", "x"}, ("Chevrolet", "Traverse"): {"limited"},
           ("RAM", "1500"): {"classic"}, ("Jeep", "Grand Cherokee"): {"wk"}, ("Volkswagen", "Tiguan"): {"limited"}, ("GMC", "Acadia"): {"limited"},
           ("Cadillac", "Escalade"): {"ext"}}
SPECIAL = set("police usps hearse limo incomplete".split())
BODY = set("l xl max ext ewb extended unlimited allroad maxx lwb xc sportwagen alltrack".split())
PERF = set("m v srt srt-8 srt-4 trackhawk type-s si nismo raptor trx rho z06 zr1 zr1x gli trofeo svr viggen ts 707 727 speed gt2 gt3 cs csl".split())
RULED_IN = {("Ford", "Mustang"): {"dark", "gtd"}, ("Fiat", "500"): {"abarth"}, ("MINI", "Countryman"): {"s", "jcw", "john"}}
# Names EPA uses for a fleet nameplate although they do not start with it (added after reading the first run's unrelated-name list).
OTHER_SPELLING = {
    ("Acura", "TL"): [("3[.]2TL.*", "own")],
    ("Chevrolet", "Silverado 1500"): [("Silverado 15 Hybrid.*", "hybrid or alternative fuel"), ("Silverado [CK]1[05]( .*)?", "own")],
    ("GMC", "Sierra 1500"): [("Sierra 15 Hybrid.*", "hybrid or alternative fuel"), ("Sierra [CK]1[05]( .*)?", "own")],
    ("Chrysler", "300"): [("300C.*", "own")],
    ("Infiniti", "G35"): [("G35x.*", "own")],
    ("MINI", "Clubman"): [("(Cooper|Cooper S|John Cooper Works|JCW) Clubman.*", "own")],
    ("MINI", "Countryman"): [("(Cooper|Cooper S|Cooper SE|John Cooper Works|JCW) Countryman.*", "own")],
    ("Porsche", "911"): [(".*911 G[Tt][23].*", "performance version"), ("Carrera GT.*", "unrelated"), ("(Carrera [24]|Targa|Turbo [24] 911).*|(.* )?911( .*)?", "own")],
    ("Subaru", "Outback"): [("Legacy.*[(]incl[.] Outback[)].*|Legacy/Outback.*", "own")],
    ("Toyota", "Supra"): [("GR Supra.*", "own")],
    ("Jeep", "Wrangler"): [("New Wrangler Unlimited.*", "longer or different body"), ("New Wrangler.*", "own")],
    ("Audi", "e-tron GT"): [("(RS|S) e-tron GT.*", "own")],
    ("Saab", "9-3"): [("9-3X.*", "longer or different body")],
    ("Audi", "Q7"): [("SQ7.*", "performance version")],
}
ORDER = ["another vehicle", "special-purpose version", "performance model (N, already ruled out)", "performance version",
         "longer or different body", "hybrid or alternative fuel"]


def words(s):
    return [w for w in re.split(r"[\s/]+", s.strip()) if w]


def strip_prefix(name, token):
    t = "".join(ch for ch in token.lower() if ch.isalnum())
    i = j = 0
    while j < len(t):
        while i < len(name) and not name[i].isalnum():
            i += 1
        if i >= len(name) or name[i].lower() != t[j]:
            return None
        i += 1
        j += 1
    if i < len(name) and name[i].isalnum():
        return None
    return name[i:].strip(" -")


def is_plain(rest):
    return all(w.lower().strip("()") in PLAIN for w in words(rest))


def core(name):
    w = words(name)
    while w and w[-1].lower().strip("()") in PLAIN:
        w.pop()
    return " ".join(w)


def relate(name, tokens):
    best = None
    for t in tokens:
        rest = strip_prefix(name, t)
        if rest is not None:
            r = ("plain", "") if is_plain(rest) else ("longer", " ".join(w for w in words(rest) if w.lower().strip("()") not in PLAIN))
            if best is None or r[0] == "plain":
                best = r
    if best:
        return best
    k = core(name)
    for t in tokens:
        if k and len(words(t)) > 1:
            rest = strip_prefix(t, k)
            if rest:
                return ("shorter", rest)
    return None


def fuelish(extra, atvs):
    w = [t.strip("()").lower() for t in extra.split()]
    return any(t in FUELW for t in w) or any(re.match(r"^xdrive\d\de$", t) for t in w) or bool(set(atvs) & ALT_ATV)


def bucket(make, model, rel, extra, atvs, only_fuel):
    w = [t.strip("()").lower() for t in extra.split()]
    if rel == "shorter":
        return "own (EPA spelling)" if (make, model) in PLAIN_1500 else "another vehicle"
    if rel.startswith("sibling:"):
        return "another vehicle"
    if (make, model, " ".join(w)) in COMBINED:
        return "own (EPA spelling)"
    if fuelish(extra, atvs):
        return "own (electrified nameplate)" if only_fuel else "hybrid or alternative fuel"
    if w and w[0] in ANOTHER.get((make, model), ()):
        return "another vehicle"
    if any(t in SPECIAL for t in w):
        return "special-purpose version"
    if w and w[0] in RULED_IN.get((make, model), ()):
        return "own (trim, already ruled in)"
    if make == "Hyundai" and "n" in w:
        return "performance model (N, already ruled out)"
    if ("type" in w and "r" in w) or (make == "Volkswagen" and w == ["r"]):
        return "performance version"
    if make == "BMW" and len(model) > 1 and model[0] == "M" and model[1].isdigit():
        return "own (trim or engine name)"
    if any(t in BODY for t in w):
        return "longer or different body"
    if any(t in PERF for t in w) or (w[:2] == ["red", "sport"]) or (w[:2] == ["black", "badge"]):
        return "performance version"
    return "own (trim or engine name)"


def fnum(x):
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(x)) if x not in (None, "") else None
    return float(m.group(1)) if m else None


def num(x):
    try:
        return int(float(x)) if x not in ("", None) else None
    except ValueError:
        return None


# ---------------------------------------------------------------- EPA's file
z = zipfile.ZipFile(ZIP)
assert [i.filename for i in z.infolist()] == ["vehicles.csv"]
EPA = collections.defaultdict(list)
for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
    EPA[(int(r["year"]), r["make"].strip().lower())].append({
        "id": r["id"], "name": r["model"].strip(), "city": num(r["city08"]), "hwy": num(r["highway08"]), "comb": num(r["comb08"]),
        "displ": fnum(r["displ"]), "trans": r["trany"].strip() or None, "drive": r["drive"].strip() or None, "atv": r["atvType"].strip(),
        "cost": num(r["fuelCost08"]), "range": num(r["range"]) or None})
n_epa = sum(len(v) for v in EPA.values())

# ---------------------------------------------------------------- the fleet (read-only)
c = sqlite3.connect("file:%s/wrench_vehicles.db?mode=ro" % ROOT.replace("\\", "/"), uri=True)
ver = {r[0] for r in c.execute("SELECT vehicle_id FROM oil_change WHERE source LIKE 'owner-manual-verified%' OR source LIKE 'service-manual-verified%'")}
pulled = dict(c.execute("SELECT vehicle_id, status || ' ' || substr(pulled_at,1,10) FROM pull_log WHERE endpoint='fuel-economy'"))
V = c.execute("SELECT id, year, make, model, engine FROM vehicles ORDER BY id").fetchall()
plates = collections.defaultdict(set)
for vid, yr, mk, md, _e in V:
    plates[mk].add(md)
LINES = collections.defaultdict(list)
for r in c.execute("SELECT vehicle_id, id, city_mpg, highway_mpg, combined_mpg, engine, transmission, drive, fuel_type, mpge, range_miles, annual_fuel_cost FROM fuel_economy ORDER BY id"):
    LINES[r[0]].append(list(r[1:]))
c.close()


def name_classes(vid, yr, mk, md, recs):
    """EPA model name -> class for this vehicle: 'own', one of ORDER, or 'unrelated'."""
    toks = [md] + ALIAS.get((mk, md), [])
    by_name = collections.defaultdict(list)
    for r in recs:
        by_name[r["name"]].append(r)
    rel = {n: relate(n, toks) for n in by_name}
    def sibling(n):      # a longer name that belongs to a longer fleet nameplate of the same make (Outlander Sport for Outlander)
        return any(o != md and len(o) > len(md) and strip_prefix(o, md) is not None and strip_prefix(n, o) is not None for o in plates[mk])
    has_plain = any(r and r[0] == "plain" for r in rel.values())
    nonfuel_longer = any(r and r[0] == "longer" and not sibling(n) and not fuelish(r[1], []) for n, r in rel.items())
    near = [x for n, r in rel.items() if r and r[0] in ("plain", "longer") and not sibling(n) for x in by_name[n]]
    all_alt = bool(near) and all(x["atv"] in ALT_ATV for x in near)       # every record of the nameplate is electric or plug-in
    only_fuel = (not has_plain and not nonfuel_longer) or all_alt
    out = {}
    for n, r in rel.items():
        if r is None:
            out[n] = next((cl for p, cl in OTHER_SPELLING.get((mk, md), ()) if re.fullmatch(p, n)), "unrelated")
            continue
        kind, extra = r
        if kind == "plain":
            out[n] = "own"
            continue
        owner = None
        if kind == "longer":
            for other in plates[mk]:
                if other != md and len(other) > len(md) and strip_prefix(other, md) is not None and strip_prefix(n, other) is not None:
                    owner = other
            if not owner and all(w.lower().strip("()") in SKIP for w in words(extra)):
                out[n] = "own"
                continue
        b = bucket(mk, md, "shorter" if kind == "shorter" else ("sibling:" + owner if owner else "longer"), extra, {x["atv"] for x in by_name[n]}, only_fuel)
        out[n] = "own" if b.startswith("own") else b
    return out, has_plain


key_rec = lambda r: (r["city"], r["hwy"], r["comb"], r["displ"], r["trans"], r["drive"])
key_line = lambda ln: (ln[1], ln[2], ln[3], fnum(ln[4]), ln[5], ln[6])
res, empties = [], []
for vid, yr, mk, md, eng in V:
    lines = LINES.get(vid, [])
    recs = EPA.get((yr, mk.lower()), [])
    cls, has_plain = name_classes(vid, yr, mk, md, recs) if recs else ({}, False)
    own_recs = [r for r in recs if cls.get(r["name"]) == "own"]
    if not lines:
        empties.append({"id": vid, "year": yr, "make": mk, "model": md, "verified": vid in ver, "pulled": pulled.get(vid), "epa_make_year": bool(recs),
                        "own_names": sorted({r["name"] for r in own_recs}), "own_records": len(own_recs)})
        continue
    by_key = collections.defaultdict(list)
    for r in recs:
        by_key[key_rec(r)].append(r)
    gas = [ln for ln in lines if ln[7] != "Electric"]
    ele = [ln for ln in lines if ln[7] == "Electric"]
    groups = collections.OrderedDict()
    for ln in gas:
        groups.setdefault(key_line(ln), []).append(ln)
    out_lines, stored_keys = [], set(groups)
    own_keys = collections.defaultdict(list)
    for r in own_recs:
        if r["atv"] not in ("EV", "FCV") and r["city"] is not None:
            own_keys[key_rec(r)].append(r)
    missing = [rs[0] for k, rs in own_keys.items() if k not in stored_keys]
    spare_missing = list(missing)
    for k, g in groups.items():
        hits = by_key.get(k, [])
        own = [r for r in hits if cls[r["name"]] == "own"]
        rel = [r for r in hits if cls[r["name"]] in ORDER]
        unr = [r for r in hits if cls[r["name"]] == "unrelated"]
        for i, ln in enumerate(g):
            e = {"line": ln[0], "key": list(k), "cost": ln[10]}
            if own and i < max(len(own), 1 if not (rel or unr) else len(own)):
                e["status"] = "own"
                e["names"] = sorted({r["name"] for r in own})
                costs = {r["cost"] for r in own}
                e["cost_now"] = sorted(x for x in costs if x is not None)
                e["cost_stale"] = ln[10] not in costs
            elif own:
                b = min({cls[r["name"]] for r in rel}, key=ORDER.index) if rel else "unrelated name"
                e["status"] = "copy"
                e["bucket"] = b
                e["names"] = sorted({r["name"] for r in (rel if rel else unr)})
            elif rel:
                b = min({cls[r["name"]] for r in rel}, key=ORDER.index)
                e["status"], e["bucket"], e["names"] = "only", b, sorted({r["name"] for r in rel if cls[r["name"]] == b})
            else:
                tw = [r for r in spare_missing if (r["displ"], r["trans"], r["drive"]) == (k[3], k[4], k[5])]
                if unr:                      # equal to another vehicle's record in all six fields: that is the evidence
                    e["status"], e["names"] = "unrelated", sorted({r["name"] for r in unr})
                    e["own_same_powertrain"] = [tw[0]["name"], tw[0]["city"], tw[0]["hwy"], tw[0]["comb"]] if tw else None
                elif tw:
                    spare_missing.remove(tw[0])
                    e["status"] = "revised"
                    e["names"] = [tw[0]["name"]]
                    e["now"] = [tw[0]["city"], tw[0]["hwy"], tw[0]["comb"]]
                else:
                    e["status"] = "no record"
            out_lines.append(e)
    never = [r for r in spare_missing]
    stored_sizes = {k[3] for k in stored_keys}
    ele_out = []
    for ln in ele:
        m = [r for r in recs if r["atv"] in ("EV", "FCV") and r["comb"] == ln[8] and r["range"] == ln[9] and r["trans"] == ln[5] and r["drive"] == ln[6]]
        ele_out.append({"line": ln[0], "classes": sorted({cls[r["name"]] for r in m}), "names": sorted({r["name"] for r in m}), "key": [ln[8], ln[9], ln[5], ln[6]]})
    res.append({"id": vid, "year": yr, "make": mk, "model": md, "label": eng, "verified": vid in ver, "pulled": pulled.get(vid), "epa_make_year": bool(recs),
                "has_plain": has_plain, "own_names": sorted({r["name"] for r in own_recs}), "own_records": len(own_keys), "lines": out_lines, "electric": ele_out,
                "never": [{"name": r["name"], "city": r["city"], "hwy": r["hwy"], "comb": r["comb"], "displ": r["displ"], "trans": r["trans"], "drive": r["drive"],
                           "other_engine": r["displ"] not in stored_sizes} for r in never]})
json.dump({"epa_records": n_epa, "vehicles": res, "empties": empties}, open(OUT, "w", encoding="utf-8"), indent=1)

# ---------------------------------------------------------------- summary
print("EPA records in the file: %d | fleet rows: %d | rows with lines: %d | rows without: %d" % (n_epa, len(V), len(res), len(empties)))
st = collections.Counter(l["status"] for e in res for l in e["lines"])
print("gasoline-type lines: %d ->" % sum(st.values()), dict(st.most_common()))
bk = collections.Counter(); bv = collections.defaultdict(set)
for e in res:
    for l in e["lines"]:
        if l["status"] in ("only", "copy"):
            bk[(l["bucket"], l["status"])] += 1
            bv[l["bucket"]].add(e["id"])
for b in ORDER + ["unrelated name"]:
    if bv[b]:
        print("   %-42s only %4d  copies %4d  vehicles %4d  verified %3d" % (b, bk[(b, "only")], bk[(b, "copy")], len(bv[b]), sum(1 for e in res if e["id"] in bv[b] and e["verified"])))
for s in ("unrelated", "revised", "no record"):
    vs = [e for e in res if any(l["status"] == s for l in e["lines"])]
    print("   %-42s lines %4d  vehicles %4d  verified %3d" % (s, st[s], len(vs), sum(1 for e in vs if e["verified"])))
nv = [e for e in res if e["never"]]
print("rows with an own EPA record never stored: %d (verified %d) | records: %d | rows where a missing record is another engine: %d | rows storing no own line at all: %d" % (
    len(nv), sum(1 for e in nv if e["verified"]), sum(len(e["never"]) for e in nv), sum(1 for e in nv if any(r["other_engine"] for r in e["never"])),
    sum(1 for e in res if e["own_records"] and not any(l["status"] in ("own",) for l in e["lines"]))))
stale = [e for e in res if any(l.get("cost_stale") for l in e["lines"])]
print("own lines whose yearly cost differs from EPA's current one: %d of %d own lines, on %d vehicles" % (
    sum(1 for e in res for l in e["lines"] if l.get("cost_stale")), st["own"], len(stale)))
noname = [e for e in res if e["epa_make_year"] and not e["own_names"]]
print("rows with lines but no own EPA name found: %d | make-year absent from EPA: %d" % (len(noname), sum(1 for e in res if not e["epa_make_year"])))
el = collections.Counter("matched own" if "own" in l["classes"] else ("matched other: " + ",".join(l["classes"]) if l["classes"] else "no match") for e in res for l in e["electric"])
print("electric lines:", dict(el))
em = collections.Counter(("EPA lists it" if x["own_records"] else "EPA has the make-year, not the nameplate" if x["epa_make_year"] else "EPA has no such make-year") for x in empties)
print("rows without fuel economy:", dict(em), "| verified among 'EPA lists it':", sum(1 for x in empties if x["own_records"] and x["verified"]))
