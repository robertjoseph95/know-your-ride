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
