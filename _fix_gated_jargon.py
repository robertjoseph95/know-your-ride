#!/usr/bin/env python
"""Scrub internal gate jargon ("GATED", "pending/gated", "not in OM") out of user-facing
verified spec strings. 2026-11-13.

Why: 312 owner's-manual-verified rows (171 vehicles) carry campaign bookkeeping inside
values that ship to the page -- Battery Notes, the Transmission row, the placard's oil
capacity, the spark-plug gap, a coolant capacity. The facts in those strings are verified
and stay verbatim; only the process clause changes to consumer wording that states the
same thing (the owner's manual does not publish X). Where a value is NOTHING BUT a gate
note it becomes NULL (THE LAW: OM silent -> absent). Nothing is added that the cited
manual does not say. `source` strings are never touched.

Usage:
  python _fix_gated_jargon.py            # dry run: writes KYR_GATED_Jargon_Rewrite_Log.md, no DB change
  python _fix_gated_jargon.py --write    # backs up the DB, applies the SAME rewrites, re-asserts

Refuses to write if any targeted row still carries the jargon after the rules (UNHANDLED).

Batch 1 (2026-11-13 19:44, WRITTEN): 301 rows keyed on the word GATED. The post-write assert then
swept the same columns with the full JARGON pattern and found rows carrying only `pending` /
`not in OM`; batch 2 scans every targeted column by the JARGON pattern itself and adds
coolant_type, tire_size_note (ships as Trim Variants) and differential_fluids_json.
"""
import datetime
import os
import re
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
LOG = os.path.join(ROOT, "KYR_GATED_Jargon_Rewrite_Log.md")
OM = "source LIKE 'owner-manual-verified%'"
JARGON = re.compile(r"\bgated\b|\bpending/gated\b|\bpending\b|\bnot in OM\b|\bin OM\b", re.I)

NOT_PUB = "the owner's manual does not state which engine pairs with which transmission"

# Ordered (column, regex, replacement). None replacement == the whole value becomes NULL.
# Column "*" applies to every targeted column AFTER its specific rules.
RULES = [
    # -- fluids.transmission_fluid ------------------------------------------------------
    ("transmission_fluid", r"\(per-engine transmission binding not specified in OM - gated\)", "(" + NOT_PUB + ")"),
    ("transmission_fluid", r"\(engine->transmission-speed binding not specified in OM - gated\)", "(" + NOT_PUB + ")"),
    ("transmission_fluid", r"\(per-engine binding not in OM - gated\)", "(" + NOT_PUB + ")"),
    ("transmission_fluid", r"\(engine->speed binding not specified in OM - gated\)", "(" + NOT_PUB + ")"),
    ("transmission_fluid",
     r"\(3\.0L Duramax diesel pairs with the 10-speed = DEXRON ULV, confirmed in Duramax supplement; gas engine->(?:transmission-)?speed binding not in OM - gated\)",
     "(3.0L Duramax diesel pairs with the 10-speed per the Duramax supplement; the owner's manual does not state which gas engine pairs with which transmission)"),
    ("transmission_fluid", r"\(type not user-serviceable, GATED\)", "(dealer-service item; the owner's manual does not publish the fluid specification)"),
    ("transmission_fluid", r"\(type GATED\)", "(fluid specification not published in the owner's manual)"),
    ("transmission_fluid", r"\(not specified in OM, gated\)", "(not specified in the owner's manual; ask your dealer)"),
    ("transmission_fluid", r"\(product per dealer - gated\)", "(product specified by your dealer; not published in the owner's manual)"),
    ("transmission_fluid", r"\(fluid type per dealer - not specified in OM, gated\)", "(fluid type not published in the owner's manual; ask your dealer)"),
    ("transmission_fluid", r"\(not specified in OM\)", "(not specified in the owner's manual)"),
    # -- oil_change.capacity_with_filter ------------------------------------------------
    ("capacity_with_filter", r"2\.8L Duramax diesel: capacity per supplement \(GATED - multi-model sup, not cleanly read\)",
     "2.8L Duramax diesel: not covered here (see the Duramax supplement)"),
    # -- parts.spark_plug_gap -----------------------------------------------------------
    ("spark_plug_gap", r"^V8 spark gap GATED - 2003 OM is a scanned/OCR copy, technical-data table illegible$", None),
    ("spark_plug_gap", r"; 4\.8/5\.3/6\.0L V8 gap GATED - 2003 OM technical-data table illegible \(scanned\)$",
     " (4.3L V6 only; V8 gap not available from the owner's manual)"),
    # -- fluids.coolant_capacity --------------------------------------------------------
    ("coolant_capacity", r"^config-dependent \(front vs front\+rear A/C\); 2003 OM is scanned - value not legible, GATED$", None),
    # -- parts.battery_notes ------------------------------------------------------------
    ("battery_notes", r"NOT in OM \(pending/gated\): ", "Not published in the owner's manual: "),
    ("battery_notes", r"NOT in OM \(pending\): ", "Not published in the owner's manual: "),
    ("battery_notes", r"GATED \(Subaru OM does NOT (?:print|publish)\): ", "Not published in the owner's manual: "),
    ("battery_notes", r"OM-published & written: .*?\. (?=[A-Z0-9])", ""),
    ("battery_notes", r"ZR2 trim: axle/locker/tire specs differ - GATED, not fabricated\.", "ZR2 trim: axle, locker and tire specs differ and are not covered here."),
    ("battery_notes", r"oil capacity per 2\.8L supplement \(GATED - multi-model\)", "oil capacity: see the 2.8L Duramax supplement"),
    ("battery_notes", r"GM punts group size to the battery label, GATED\.", "GM refers group size to the battery label."),
    ("battery_notes", r"5\.2L GTD/Shelby halo(?: specs)? not covered(?: by this OM)? - gated\.", "5.2L GTD/Shelby models are not covered here."),
    ("battery_notes", r"consult (SUBARU |Subaru )?dealer \(GATED\)", "consult your Subaru dealer (not published in the owner's manual)"),
    ("battery_notes", r"\(GATED\)", "(not published in the owner's manual)"),
    ("battery_notes", r"\bPNs\b", "part numbers"),
    ("battery_notes", r"\(placard\)", "(see the door-jamb placard)"),
    ("battery_notes", r"\(B-pillar placard\)", "(see the B-pillar placard)"),
    ("battery_notes", r"\(door placard\)", "(see the door-jamb placard)"),
    # second pass (residue found by the first dry run, 2026-11-13)
    ("battery_notes", r"Battery: (.*?) - group(?: size)? not in OM, GATED\.", r"Battery: \1; group size not published in the owner's manual."),
    ("battery_notes", r"Battery: maintenance-free - group punts to label, GATED\.", "Battery: maintenance-free; GM refers group size to the battery label."),
    ("battery_notes", r"AGM 12V battery \(Stop/Start\) - group punts to label, GATED\.", "AGM 12V battery (Stop/Start); GM refers group size to the battery label."),
    ("battery_notes", r"GATED: spark-plug GAP(?: \(Subaru OM does NOT print\))?, ", "Not published in the owner's manual: spark-plug gap, "),
    ("battery_notes", r"Escalade V \(supercharged 6\.2\) halo - separate spec, GATED\.", "Escalade V (supercharged 6.2L) is not covered here."),
    ("battery_notes", r"Escalade V \(6\.2L LT4 supercharged\) is a separate halo - own oil spec, GATED\.", "Escalade V (6.2L LT4 supercharged) has its own oil specification and is not covered here."),
    ("battery_notes", r"the HV system, traction battery, and hybrid-specific service specs are GATED \(not covered by this gas OM; no separate PHEV row in DB\)\.",
     "the high-voltage system, traction battery and hybrid-specific service specs are not covered here."),
    ("battery_notes", r"HV system / traction battery / hybrid-specific specs GATED \(no separate Hybrid row in DB\)\.",
     "high-voltage system, traction battery and hybrid-specific specs are not covered here."),
    ("battery_notes", r"A 5\.7L V8 old-body carryover existed for 2000 - NOT covered by this GMT800 OM, GATED\.", "A 5.7L V8 old-body carryover existed for 2000 and is not covered here."),
    ("battery_notes", r"Axle fluids GIVEN in OM: ", "Axle fluids per the owner's manual: "),
    ("battery_notes", r"LUG TORQUE GATED: 2005 OM defers to a spec page that did not extract cleanly - NOT assumed 140 \(midsize/older may diverge, per Encore-100 lesson\)\.",
     "Lug-nut torque: not available from the owner's manual."),
    ("battery_notes", r"Oil filter: ACDelco \(2\.5L LK0\) - part # per OM, GATED \(not transcribed\)\.", "Oil filter (2.5L LK0): ACDelco, part number per the owner's manual."),
    ("battery_notes", r"V8 oil filter # GATED \(2003 OM table illegible\)\.", "V8 oil filter part number not available from the owner's manual."),
    ("battery_notes", r"2003: (.*?) GATED - the 2003(?: GMC Sierra)? OM is a scanned/OCR copy whose technical-data table is illegible\.", r"2003: \1 are not legible in the owner's manual copy."),
    ("battery_notes", r"2020-2022 diesel = earlier LM2 engine version - GATED until the matching-year LM2 supplement is pulled\.", "2020-2022 3.0L diesel (earlier LM2 version): not covered here."),
    ("battery_notes", r"\(AWD - OM punts to dealer\)", "(AWD; the owner's manual refers you to the dealer)"),
    ("battery_notes", r"\*\* Read from .*?\. \*\* ?", ""),
    # -- batch 2 (2026-11-13): rows carrying `pending` / `not in OM` without the word GATED ----
    ("battery_notes", r"Spark-plug type/gap and BCI battery group/CCA are NOT published in the owner's manual \(service-manual fields\) - pending\.",
     "Spark-plug type/gap and BCI battery group/CCA are not published in the owner's manual."),
    ("battery_notes", r"CVT fluid NS-3 type verified; capacity not in OM\.", "CVT fluid: Nissan NS-3 (capacity not published in the owner's manual)."),
    ("battery_notes", r" ARE in the Nissan OM and (?:are )?recorded verified\.", " are published in the Nissan owner's manual."),
    ("battery_notes", r"Transmission-fluid type verified \((.+?)\); capacity not in OM\.", r"Transmission fluid: \1; capacity not published in the owner's manual."),
    ("battery_notes", r"are service-manual fields \(not in this Owner's Guide\) - pending service-manual verification\.", "are not published in this Owner's Guide."),
    ("battery_notes", r" \(service-manual data\) - pending service-manual verification\.", "."),
    ("battery_notes", r"5\.2L supercharged Raptor R \(halo trim\): specs PENDING its own manual - not listed \(not fabricated\)\.",
     "5.2L supercharged Raptor R (halo trim): not covered here."),
    # fluids.coolant_type ships as the Coolant row
    ("coolant_type", r"\bnot stated in OM\b", "not stated in the owner's manual"),
    # parts.tire_size_note ships as the Trim Variants note under tire pressure
    ("tire_size_note", r"\((.+?), not in OM body\) - pending\.", r"(see the \1)."),
    ("tire_size_note", r"Tire SIZE is trim-dependent \(placard, not in OM\) - pending\.", "Tire size is trim-dependent (see the door-jamb placard)."),
    ("tire_size_note", r"Tire size & pressure: see driver door placard \(config-dependent\) - not in OM body; pending\.",
     "Tire size & pressure: see the driver door placard (config-dependent)."),
    # fluids.differential_fluids_json: the whole value is a gate note (OM silent -> NULL; the build already dropped it)
    ("differential_fluids_json", r'^\{"front_rear_axle_4wd": "Fluid type per dealer \(not specified in OM - GATED\)"\}$', None),
    # -- cosmetic, all targeted columns: internal abbreviation -> plain words ----------
    ("*", r"\bnot specified in OM\b", "not specified in the owner's manual"),
    ("*", r"\bnot in OM\b", "not in the owner's manual"),
]

TARGETS = [  # (table, column)
    ("fluids", "transmission_fluid"),
    ("oil_change", "capacity_with_filter"),
    ("parts", "spark_plug_gap"),
    ("fluids", "coolant_capacity"),
    ("parts", "battery_notes"),
    ("fluids", "coolant_type"),
    ("parts", "tire_size_note"),
    ("fluids", "differential_fluids_json"),
]


def rewrite(col, s):
    if s is None:
        return None
    out = s
    for rcol, pat, rep in RULES:
        if rcol not in (col, "*") or out is None:
            continue
        if rep is None:
            if re.search(pat, out):
                return None
            continue
        out = re.sub(pat, rep, out)
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out


def main(write):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    veh = {r[0]: "%s %s %s" % (r[1], r[2], r[3]) for r in cur.execute("SELECT id, year, make, model FROM vehicles")}
    changes, unhandled = [], []
    for t, col in TARGETS:
        rows = cur.execute("SELECT vehicle_id, %s FROM %s WHERE %s IS NOT NULL AND %s ORDER BY vehicle_id" % (col, t, col, OM)).fetchall()
        for vid, val in rows:
            if not isinstance(val, str) or not JARGON.search(val):
                continue
            new = rewrite(col, val)
            if new is not None and JARGON.search(new):
                unhandled.append((t, col, vid, val, new))
            elif new != val:
                changes.append((t, col, vid, val, new))
    # -- log -------------------------------------------------------------------------
    by_col = {}
    for t, col, vid, old, new in changes:
        by_col.setdefault((t, col), []).append((vid, old, new))
    lines = ["# GATED-jargon rewrite log (%s)" % ("WRITTEN" if write else "DRY RUN, nothing written"),
             "", "Generated %s by `_fix_gated_jargon.py`. %d rows change, %d set to NULL, %d UNHANDLED."
             % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(changes),
                sum(1 for c in changes if c[4] is None), len(unhandled)), ""]
    if unhandled:
        lines += ["## UNHANDLED (jargon remains; the script refuses to write while this list is non-empty)", ""]
        for t, col, vid, old, new in unhandled:
            lines += ["- `%s.%s` %s (id %s)" % (t, col, veh.get(vid), vid), "  - before: %s" % old, "  - after:  %s" % new]
        lines.append("")
    for (t, col), items in by_col.items():
        lines += ["## %s.%s - %d rows" % (t, col, len(items)), ""]
        # group identical before->after pairs
        groups = {}
        for vid, old, new in items:
            groups.setdefault((old, new), []).append(vid)
        for (old, new), vids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            names = sorted({veh.get(v, str(v)) for v in vids})
            lines += ["### x%d: %s%s" % (len(vids), ", ".join(names[:3]), " +%d more" % (len(names) - 3) if len(names) > 3 else ""),
                      "- **before:** %s" % old,
                      "- **after:**  %s" % ("NULL (value was only a gate note)" if new is None else new), ""]
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("rows changing: %d  (NULL: %d)  unhandled: %d  -> log %s"
          % (len(changes), sum(1 for c in changes if c[4] is None), len(unhandled), os.path.relpath(LOG, ROOT)))
    for (t, col), items in by_col.items():
        print("  %4d  %s.%s" % (len(items), t, col))
    if unhandled:
        print("UNHANDLED rows exist; refusing to write.")
        return 1
    if not write:
        return 0
    # -- write -----------------------------------------------------------------------
    bak = DB + ".bak_gatedjargon_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, bak)
    print("backup:", os.path.basename(bak))
    for t, col, vid, old, new in changes:
        n = cur.execute("UPDATE %s SET %s=? WHERE vehicle_id=? AND %s=?" % (t, col, col), (new, vid, old)).rowcount
        assert n == 1, (t, col, vid, n)
    con.commit()
    # post-assert over every targeted column: no jargon left in verified rows
    left = 0
    for t, col in TARGETS:
        for vid, val in cur.execute("SELECT vehicle_id, %s FROM %s WHERE %s IS NOT NULL AND %s" % (col, t, col, OM)):
            if JARGON.search(str(val)):
                left += 1
                print("  STILL:", t, col, vid, str(val)[:120])
    print("post-write jargon rows remaining:", left)
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv[1:]))
