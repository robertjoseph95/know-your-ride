"""Fuel-economy version labels: the text a card shows under the drive line, built only from EPA's own
record fields (spec: docs/superpowers/specs/2026-11-20-fuel-economy-version-labels-design.md).

A record dict carries at least: id (int), name (EPA `model`), atv (EPA `atvType`, '' for gasoline),
tcharger (EPA `tCharger`), scharger (EPA `sCharger`).
"""
import re

SEP = " · "

# (tag, test) in the order the label shows them; a tag shows only if every record behind the line passes.
TAGS = (
    ("Hybrid", lambda r: r["atv"] == "Hybrid"),
    ("Plug-in hybrid", lambda r: r["atv"] == "Plug-in Hybrid"),
    ("Flex-fuel", lambda r: r["atv"] == "FFV"),
    ("Diesel", lambda r: r["atv"] == "Diesel"),
    ("CNG", lambda r: r["atv"] == "CNG"),
    ("Dual-fuel CNG", lambda r: r["atv"] == "Bifuel (CNG)"),
    ("Dual-fuel LPG", lambda r: r["atv"] == "Bifuel (LPG)"),
    ("Turbo", lambda r: bool((r.get("tcharger") or "").strip())),
    ("Supercharged", lambda r: bool((r.get("scharger") or "").strip())),
)

# Name classes (files/epa_name_rules.py) whose names a label keeps; every other class is another vehicle.
KEEP_CLASSES = frozenset({"own", "performance version", "hybrid or alternative fuel",
                          "longer or different body", "special-purpose version"})


def kept_records(recs, classes):
    """The records whose EPA name is the vehicle's own or one of its versions; all of them if none is."""
    kept = [r for r in recs if classes.get(r["name"]) in KEEP_CLASSES]
    return kept if kept else list(recs)


# ---------------------------------------------------------------- the plain car first (ruling (c), 2026-11-20)
# A row keeps every version EPA lists under its nameplate, labelled. So that the search card (which shows the
# row's first line) and the top of the card list show the plain car, a row ships its plain lines first:
# fuel_economy.epa_plain = 1 when a record behind the line is the vehicle's own name, is not typed hybrid or
# plug-in hybrid by EPA, and is not one of the trim kinds ruled on 2026-11-20 below.
NOT_PLAIN_ATV = ("Hybrid", "Plug-in Hybrid")
# The every-own-record fill's HOLD list, with TRD and chassis cab on any nameplate:
# (make or None, model or None, full-match pattern on EPA's model name, engine size or None)
VERSION_NAMES = (
    ("Chrysler", "300", r"300C?/SRT-8", 6.1),
    ("Jeep", "Wrangler", r"Wrangler .*4dr.*", None),
    (None, None, r".*Cab Chassis.*", None),
    ("BMW", None, r".* M\d\di( .*)?", None),
    ("Ford", "Mustang", r"Mustang (Bullitt|HO .*|Performance Package|Dark Horse|GTD|Mach 1)( .*)?", None),  # +Dark Horse, GTD, Mach 1 (2026-11-22)
    (None, None, r".*\bTRD\b.*", None),
    ("RAM", "1500", r"1500 HO .*", None),
    ("Porsche", "911", r"911 Turbo S.*", None),
)
# The order the build ships a row's lines in (and the verifier checks): plain lines first, then the rest, each in
# stored order. Unassessed lines (epa_plain NULL) count as not plain.
SHIP_ORDER = "vehicle_id, CASE WHEN epa_plain = 1 THEN 0 ELSE 1 END, id"


def _size(x):
    try:
        return float(x) if x not in (None, "") else None
    except (TypeError, ValueError):
        return None


def version_name(make, model, rec):
    """True when the record's EPA name is one of the trim kinds that is not the plain car."""
    for mk, md, rx, size in VERSION_NAMES:
        if (mk is None or mk == make) and (md is None or md == model) and re.fullmatch(rx, rec["name"]) \
                and (size is None or _size(rec.get("displ")) == size):
            return True
    return False


def plain_flag(make, model, kept, classes):
    """1 when any record behind the line is the plain car (see above), else 0."""
    return 1 if any(classes.get(r["name"]) == "own" and (r.get("atv") or "") not in NOT_PLAIN_ATV
                    and not version_name(make, model, r) for r in kept) else 0


def _says(name, tag):
    """True when the tag's full text stands in the name as whole words, ignoring case."""
    return re.search(r"(?<![0-9A-Za-z])" + re.escape(tag) + r"(?![0-9A-Za-z])", name, re.I) is not None


def label_text(recs):
    """`<names> · <tags>`: EPA names verbatim, unique, sorted; tags every record carries and no name already says."""
    names = sorted({r["name"] for r in recs})
    text = ", ".join(names)
    tags = [t for t, has in TAGS if all(has(r) for r in recs) and not all(_says(n, t) for n in names)]
    return text + SEP + ", ".join(tags) if tags else text


def ids_text(recs):
    """The EPA record ids behind the line, unique, ascending, comma-separated."""
    return ",".join(str(i) for i in sorted({int(r["id"]) for r in recs}))
