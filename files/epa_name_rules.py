"""EPA naming rules for fuel-economy lines: which EPA model names are a fleet vehicle's own, which are
one of its versions, and which belong to another vehicle.

Copied verbatim from the full comparison (`_compare_fuel_economy_epa.py`, the two rule parts: from the
`name rules` marker to the `EPA's file` marker, and `name_classes`) with one change: `name_classes`
takes the fleet's nameplates as a parameter instead of a module global, and no longer takes the unused
vehicle id. tests/test_fe_labels.py proves the two agree on the whole fleet.
No file or database is touched at import.
"""
import re
import collections

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


def name_classes(yr, mk, md, recs, plates):
    """EPA model name -> class for this vehicle: 'own', one of ORDER, or 'unrelated'.

    `plates` maps each make to every model of the fleet (any year); see fleet_plates()."""
    plates = collections.defaultdict(set, plates)
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


def fleet_plates(cur):
    """make -> every model the fleet holds for that make, in any year."""
    plates = collections.defaultdict(set)
    for mk, md in cur.execute("SELECT DISTINCT make, model FROM vehicles"):
        plates[mk].add(md)
    return dict(plates)
