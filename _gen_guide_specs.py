#!/usr/bin/env python
"""_gen_guide_specs.py -- regenerate wrench_deploy/api/specs.json for the Pro AI repair
guide (wrench_deploy/api/guide.py) from OWNER'S-MANUAL-VERIFIED DB rows ONLY.

P0-2 fix (2026-07-11 audit): the previous specs.json was a frozen, orphaned pre-Integrity-Gate
AI snapshot with NO provenance (1,669 records), feeding fabricated / DB-contradicted specs to
paying Pro users as "use these EXACT values". This generator emits ONLY ver==1 (OM-cited)
values -- the SAME gate the Tier-1 blob uses (files/source_registry.py). Any field that is not
owner's-manual-verified is OMITTED, so guide.py's build_specs() renders nothing for it and the
model hedges to "check your factory service manual" (GUIDE_SYSTEM). The result covers the
current verified cohort instead of 1,669 fabricated records -- fewer, but every value is OM-true.

Deterministic: explicit ORDER BY on every query, sort_keys serialization, no timestamps in the
data. Run twice -> byte-identical. Regenerate after verification changes; DO NOT hand-edit
specs.json (the deploy guard rejects a specs.json without the _meta.generated_by marker).
"""
import sqlite3
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "wrench_vehicles.db")
OUT = os.path.join(HERE, "wrench_deploy", "api", "specs.json")

# IC-02: the exact-token classifier is the SAME production gate the blob build
# uses (files/source_registry.py) -- no more copied substring implementation.
# It hard-fails (SourceRegistryError) on any unknown token BEFORE OUT is
# written, so an unregistered source can never silently ship or silently gate.
try:
    from files.source_registry import assert_frozen_landscape, classify as _classify
except ImportError:  # invoked with a cwd outside the repo root
    sys.path.insert(0, HERE)
    from files.source_registry import assert_frozen_landscape, classify as _classify


def _clean(x):
    return x if (x is not None and x != "") else None


def _plug_from_json(s):
    """Build a single spark-plug string from the structured spark_plugs_json (used when the
    curated summary column is empty). Only reached for OM-verified parts rows, so the values
    are owner's-manual-sourced. Deterministic: preserves JSON array order."""
    if not s:
        return None
    try:
        arr = json.loads(s)
    except Exception:
        return None
    out = []
    for e in arr if isinstance(arr, list) else []:
        pn = str(e.get("part_number") or "").strip()
        if not pn:
            continue
        label = (str(e.get("brand") or "").strip() + " " + pn).strip()
        desc = str(e.get("description") or "").strip()
        if desc:
            label += " (%s)" % desc
        out.append(label)
    return " / ".join(out) or None


def main():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.row_factory = sqlite3.Row
    # try/finally guarantees the SQLite handle closes on EVERY path -- a failing
    # gate or classifier hard-fail must not leak the connection (IC-02 final
    # correction 2); exceptions still propagate and OUT is only written after a
    # fully successful projection.
    try:
        cur = con.cursor()

        # IC-02 frozen-landscape preflight (correction 2): the guide projection must
        # enforce the same source-landscape freeze as the blob build -- dispositioned
        # tables, the ev_specs IC-02E freeze, and the 424-row citation-debt digest --
        # BEFORE any row is projected and before OUT is (re)written.
        assert_frozen_landscape(cur)

        veh = {r["id"]: r for r in cur.execute(
            "SELECT id, year, make, model, engine, trim FROM vehicles ORDER BY id")}

        recs = {}

        def rec(vid):
            k = str(vid)
            if k not in recs:
                v = veh.get(vid)
                if not v:
                    return None
                label = "%s %s %s" % (v["year"], v["make"], v["model"])
                if v["engine"]:
                    label += " (%s)" % v["engine"]
                recs[k] = {"label": label, "oil": {}, "parts": {}, "torque": {}}
            return recs[k]

        # OIL (ver==1) -> viscosity / oil_type / capacity (formatted string) / oem_spec.
        # socket/thread/gasket/oil_filter are gated (not OM-published) -> intentionally OMITTED.
        for r in cur.execute("SELECT rowid, * FROM oil_change ORDER BY vehicle_id, rowid"):
            if _classify(r["source"], "oil_change", r["vehicle_id"]) != 1 or r["vehicle_id"] not in veh:
                continue
            rc = rec(r["vehicle_id"])
            for dst, col in (("viscosity", "viscosity"), ("oil_type", "oil_type"),
                             ("capacity", "capacity_with_filter"), ("oem_spec", "oem_spec")):
                val = _clean(r[col])
                if val is not None:
                    rc["oil"][dst] = val

        # PARTS (ver==1) -> spark_plug / plug_gap / plug_qty / battery_group / battery_cca / tire / psi.
        # air/cabin filters, wipers, battery part are gated for the OM cohort -> OMITTED.
        for r in cur.execute("SELECT rowid, * FROM parts ORDER BY vehicle_id, rowid"):
            if _classify(r["source"], "parts", r["vehicle_id"]) != 1 or r["vehicle_id"] not in veh:
                continue
            rc = rec(r["vehicle_id"])
            for dst, col in (("plug_gap", "spark_plug_gap"),
                             ("plug_qty", "spark_plug_qty"), ("battery_group", "battery_group"),
                             ("battery_cca", "battery_cca"), ("tire", "tire_size"),
                             ("psi_f", "tire_pressure_front"), ("psi_r", "tire_pressure_rear")):
                val = _clean(r[col])
                if val is not None:
                    rc["parts"][dst] = val
            # spark plug: prefer the curated summary column, fall back to the structured JSON.
            plug = _clean(r["spark_plug_type"]) or _plug_from_json(r["spark_plugs_json"])
            if plug:
                rc["parts"]["spark_plug"] = plug

        # TORQUE (ver==1) -> {component: [ft_lb, Nm]} for the comps build_specs reads.
        TQ_KEYS = {"lug_nut", "drain_bolt", "spark_plug"}
        for r in cur.execute("SELECT rowid, * FROM torque_specs ORDER BY vehicle_id, component, rowid"):
            if _classify(r["source"], "torque_specs", r["vehicle_id"]) != 1 or r["vehicle_id"] not in veh:
                continue
            comp = r["component"]
            if comp not in TQ_KEYS or r["torque_ft_lbs"] is None:
                continue
            rec(r["vehicle_id"])["torque"][comp] = [r["torque_ft_lbs"], r["torque_nm"]]

        # Keep only vehicles that actually have >=1 verified value in some section.
        recs = {k: v for k, v in recs.items() if v["oil"] or v["parts"] or v["torque"]}

        out = {"_meta": {
            "generated_by": "_gen_guide_specs.py",
            "source": "wrench_vehicles.db verified rows (ver==1, OM-cited)",
            "db_vehicle_count": len(veh),
            "record_count": len(recs),
            "note": "regenerate via _gen_guide_specs.py -- do not hand-edit",
        }}
        out.update(recs)
    finally:
        con.close()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    print("wrote %s: %d verified vehicles (of %d in DB)" % (OUT, len(recs), len(veh)))


if __name__ == "__main__":
    main()
