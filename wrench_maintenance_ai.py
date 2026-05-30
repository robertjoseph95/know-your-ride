#!/usr/bin/env python3
"""
Wrench - AI maintenance schedule generation
============================================
Generates a per-vehicle preventive-maintenance schedule for every vehicle that
has grounding specs (a row in oil_change; 1,669 vehicles), using Claude Haiku 4.5
(claude-haiku-4-5 — the drop-in replacement for the now-retired Haiku 3.5).

Grounded in real specs from oil_change, parts, engine_specs, fluids, warranty.
Oil interval rules (precedence): EV -> none; Turbo -> 5,000; Luxury -> 10,000;
Standard -> 7,500. EVs exclude oil/spark-plug/transmission service.

Per vehicle: DELETE existing maintenance rows, INSERT AI-generated rows
(source='ai-haiku-4.5'). Replacement happens only on a successful generation.
maintenance_parts is intentionally NOT touched (out of scope) — it will be
orphaned relative to the new schedule; flagged for a follow-up pass.

Hard stop if cumulative API spend exceeds $35.
"""
import os, sys, io, json, sqlite3, logging, time
from typing import Optional, List
from pydantic import BaseModel
import anthropic

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
CFG = json.load(open(os.path.join(ROOT, "wrench_config.json")))
MODEL = "claude-haiku-4-5"
COST_CAP = 35.0
# Haiku 4.5 pricing ($/1M tokens)
P_IN, P_CW, P_CR, P_OUT = 1.0, 1.25, 0.10, 5.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(os.path.join(ROOT, "wrench_maintenance_ai.log"), encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=CFG["anthropic_api_key"], max_retries=4)

EV_MAKES = {"tesla", "rivian", "lucid", "polestar"}
LUX_MAKES = {"bmw", "mercedes-benz", "mercedes", "audi", "lexus", "acura", "infiniti",
             "cadillac", "lincoln", "porsche", "jaguar", "land rover", "genesis", "volvo",
             "maserati", "bentley", "rolls-royce", "ferrari", "lamborghini", "mclaren",
             "aston martin", "alfa romeo"}

SYSTEM = [{"type": "text", "text": (
    "You are an automotive maintenance expert. Given a vehicle and its real specifications, produce a "
    "realistic preventive-maintenance schedule of 8 to 15 line items. Each item has: a concise service "
    "description, a mileage_interval (miles, integer) and/or a months_interval (integer). Use null where "
    "an interval type does not apply (e.g. a strictly time-based item has null mileage_interval).\n"
    "RULES:\n"
    "1. Use the provided oil_change_interval_miles EXACTLY for engine oil & filter changes.\n"
    "2. EV vehicles: DO NOT include engine oil changes, spark plugs, engine air filter, or transmission "
    "fluid service. Focus on tire rotation, brake fluid, cabin air filter, coolant/battery thermal fluid, "
    "wiper blades, brake pad inspection, and 12V battery checks.\n"
    "3. Turbocharged engines: keep oil changes frequent per the provided interval.\n"
    "4. Ground every item in the supplied specs. DO NOT invent part numbers or torque values.\n"
    "5. Cover the common services for the vehicle type (oil, tires, brakes, fluids, filters, plugs, "
    "belts/timing where applicable, coolant).\n"
    "Output ONLY the structured schedule."
), "cache_control": {"type": "ephemeral"}}]


class Item(BaseModel):
    description: str
    mileage_interval: Optional[int]
    months_interval: Optional[int]


class Schedule(BaseModel):
    items: List[Item]


def classify(make, engine, aspiration, has_oil):
    m = (make or "").strip().lower()
    eng = (engine or "").lower()
    if m in EV_MAKES or "electric" in eng or not has_oil:
        return "EV", None
    asp = (aspiration or "").lower()
    if "turbo" in asp or "turbo" in eng or "supercharg" in asp:
        return "turbo", 5000
    if m in LUX_MAKES:
        return "luxury", 10000
    return "standard", 7500


def build_user(v, o, p, es, f, w, vclass, oil_int):
    L = [f"Vehicle: {v['year']} {v['make']} {v['model']} ({v['engine'] or 'engine n/a'})",
         f"Vehicle class: {vclass}",
         f"oil_change_interval_miles: {oil_int if oil_int else 'N/A (electric — no engine oil)'}"]
    if o:
        L.append(f"Oil spec: {o['viscosity']} {o['oil_type']}, capacity {o['capacity_with_filter']} qt, OEM {o['oem_spec']}")
    if p:
        L.append(f"Spark plugs: {p['spark_plug_type']} x{p['spark_plug_qty']}; battery group {p['battery_group']}")
    if es:
        L.append(f"Engine: {es['displacement_l']}L {es['cylinders']}cyl, aspiration {es['aspiration']}")
    if f:
        L.append(f"Fluids: transmission={f['transmission_fluid']}, brake={f['brake_fluid']}, coolant={f['coolant_type']}")
    if w:
        L.append(f"Warranty: {w['warranty_type']} {w['months']}mo/{w['miles']}mi")
    return "\n".join(x for x in L if x is not None)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    vids = [r[0] for r in conn.execute(
        "SELECT vehicle_id FROM oil_change WHERE vehicle_id>0 ORDER BY vehicle_id")]
    total = len(vids)
    log.info("=" * 70)
    log.info(f"AI MAINTENANCE GENERATION START — model={MODEL}, {total} vehicles, cap=${COST_CAP}")

    spend = 0.0
    ok = fail = items_total = 0
    t0 = time.time()
    stopped = False

    for i, vid in enumerate(vids, 1):
        if spend >= COST_CAP:
            log.warning(f"HARD STOP: cumulative spend ${spend:.2f} >= ${COST_CAP}. Halting at {i-1}/{total}.")
            stopped = True
            break
        v = conn.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
        o = conn.execute("SELECT * FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
        p = conn.execute("SELECT * FROM parts WHERE vehicle_id=?", (vid,)).fetchone()
        es = conn.execute("SELECT * FROM engine_specs WHERE vehicle_id=?", (vid,)).fetchone()
        f = conn.execute("SELECT * FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()
        w = conn.execute("SELECT * FROM warranty WHERE vehicle_id=? LIMIT 1", (vid,)).fetchone()
        has_oil = bool(o and o["viscosity"])
        vclass, oil_int = classify(v["make"], v["engine"], es["aspiration"] if es else None, has_oil)
        name = f"{v['year']} {v['make']} {v['model']}"

        try:
            r = client.messages.parse(
                model=MODEL, max_tokens=1500, system=SYSTEM,
                messages=[{"role": "user", "content": build_user(v, o, p, es, f, w, vclass, oil_int)}],
                output_format=Schedule)
            sched = r.parsed_output
            u = r.usage
            call_cost = (u.input_tokens * P_IN + (u.cache_creation_input_tokens or 0) * P_CW
                         + (u.cache_read_input_tokens or 0) * P_CR + u.output_tokens * P_OUT) / 1e6
            spend += call_cost
            rows = [(vid, it.mileage_interval, it.months_interval, it.description.strip(), "ai-haiku-4.5", vclass)
                    for it in sched.items if it.description and it.description.strip()]
            if not rows:
                raise ValueError("empty schedule")
            # replace only on success
            conn.execute("DELETE FROM maintenance WHERE vehicle_id=?", (vid,))
            conn.executemany(
                "INSERT INTO maintenance (vehicle_id,mileage_interval,months_interval,description,source,notes) "
                "VALUES (?,?,?,?,?,?)", rows)
            conn.commit()
            ok += 1
            items_total += len(rows)
            log.info(f"  [{i}/{total}] {name} [{vclass}] -> {len(rows)} items | ${call_cost:.5f} | cum ${spend:.3f}")
        except Exception as e:
            fail += 1
            log.error(f"  [{i}/{total}] {name} FAILED: {e} (kept existing rows)")

        if i % 50 == 0:
            rate = i / (time.time() - t0) * 60
            log.info(f"  --- batch checkpoint {i}/{total} | ok={ok} fail={fail} | "
                     f"{items_total} items | ${spend:.3f} | {rate:.0f}/min ---")

    elapsed = (time.time() - t0) / 60
    log.info("=" * 70)
    log.info("AI MAINTENANCE GENERATION COMPLETE" + (" (HARD-STOPPED)" if stopped else ""))
    log.info(f"  Vehicles processed: {ok+fail}/{total}  (ok={ok}, failed={fail})")
    log.info(f"  Maintenance items inserted: {items_total}")
    log.info(f"  Total API cost: ${spend:.2f}")
    log.info(f"  Time: {elapsed:.1f} min")
    log.info("=" * 70)
    conn.close()


if __name__ == "__main__":
    main()
