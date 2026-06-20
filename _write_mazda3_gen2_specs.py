"""
Write VERIFIED Gen 2 (BL, 2010-2013) curated specs for Mazda 3 ids 38710-38713.

Sources (official Mazda owner's manuals):
- 2010 Mazda3 4-door OM -> 2010-2011 rows (MZR 2.0 + MZR 2.5)
- 2013 Mazda3 4-door OM -> 2012-2013 rows (SkyActiv-G 2.0 + MZR 2.5)
See KYR_Mazda3_Spec_Verification_Log.md for page cites.

Per Robert's decision: engine-divergent fields are stored as labeled dual strings
("4.5 qt (2.0L) / 5.3 qt (2.5L)"); uniform fields as single values; viscosity per-year
(5W-20 for 2010-11, 0W-20 for 2012-13). The valU() UI helper renders these as-is.
Unverified fields (battery group/CCA, drain/plug torque, SkyActiv plug gap) left NULL.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")

# ---- 2010-2011 (MZR 2.0 + MZR 2.5) ----
EARLY = dict(
    vids=[38710, 38711], src="Mazda Owner's Manual (2010, Schedule 1)",
    oil=dict(viscosity="5W-20", oil_type=None,
             capacity_with_filter="4.5 qt (2.0L) / 5.3 qt (2.5L)",
             capacity_without_filter="4.1 qt (2.0L) / 4.9 qt (2.5L)",
             oem_spec="API SM / ILSAC"),
    parts=dict(spark_plug_type="Iridium", spark_plug_gap="0.049-0.053", spark_plug_qty=4,
               tire_size="P205/55R16", tire_pressure_front=35, tire_pressure_rear=35,
               spark_plugs_json=json.dumps([{"brand": "Mazda", "part_number": "LFG1-18-110",
                   "description": "OE iridium (2.0L & 2.5L MZR)", "is_oem": True}]),
               tire_size_note=("Base 16-inch: 240 kPa (35 psi) front/rear. Options: 17-inch "
                   "(P205/50R17) 220 kPa (32 psi); 18-inch (P225/40R18) 240/230 kPa (35/34 psi). "
                   "Per owner's manual."),
               battery_notes="OE battery 40-52 Ah; BCI group size & CCA not specified by Mazda."),
    fluids=dict(transmission_fluid="Mazda ATF M-V (automatic)", transmission_capacity=None,
                brake_fluid="DOT 3", coolant_type="FL22", coolant_capacity=7.9,
                power_steering_fluid="Mazda ATF M-III / M-V (Dexron II equiv.)"),
)

# ---- 2012-2013 (SkyActiv-G 2.0 + MZR 2.5) ----
LATE = dict(
    vids=[38712, 38713], src="Mazda Owner's Manual (2013, Schedule 1)",
    oil=dict(viscosity="0W-20", oil_type="Full Synthetic",
             capacity_with_filter="4.4 qt (SkyActiv 2.0) / 5.3 qt (MZR 2.5)",
             capacity_without_filter="4.2 qt (SkyActiv 2.0) / 4.9 qt (MZR 2.5)",
             oem_spec="API SM / ILSAC GF-4/GF-5; 0W-20 full synthetic"),
    parts=dict(spark_plug_type="Iridium", spark_plug_gap=None, spark_plug_qty=4,
               tire_size="P205/55R16", tire_pressure_front=36, tire_pressure_rear=36,
               spark_plugs_json=json.dumps([
                   {"brand": "Mazda", "part_number": "PE5R-18-110", "description": "OE iridium (SkyActiv-G 2.0)", "is_oem": True},
                   {"brand": "Mazda", "part_number": "LFJD-18-110", "description": "OE iridium (MZR 2.5)", "is_oem": True}]),
               tire_size_note=("SkyActiv-G 2.0 base 16-inch: 250 kPa (36 psi) front/rear. Options: "
                   "17-inch (P205/50R17) 220 kPa (32 psi); 18-inch (P225/40R18) 240/230 kPa (35/34 psi). "
                   "Per owner's manual."),
               battery_notes=("OE battery 50-65 Ah; BCI group size & CCA not specified by Mazda. "
                   "SkyActiv-G 2.0 spark-plug gap is factory pre-set and not published in the owner's manual.")),
    fluids=dict(transmission_fluid="Mazda ATF M-V (5-spd) / ATF FZ (6-spd SkyActiv)",
                transmission_capacity=None, brake_fluid="DOT 3", coolant_type="FL22",
                coolant_capacity="7.8-8.7 qt (SkyActiv 2.0) / 7.9 qt (MZR 2.5)",
                power_steering_fluid="Mazda ATF M-III / M-V (Dexron II equiv.)"),
)

MAINT = [(7500, 12, "Engine oil & filter change"),
         (7500, None, "Tire rotation"),
         (75000, None, "Spark plug replacement (iridium x4)"),
         (120000, 120, "Engine coolant (FL22) first replacement; thereafter every 60,000 mi / 5 yr")]
TORQUE = [("lug_nut", 76.0, 103.0, "88-118 N·m (65-87 ft·lbf) per owner's manual")]


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, DB + ".bak-gen2specs-" + ts)
    print("Backup:", os.path.basename(DB + ".bak-gen2specs-" + ts))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()

    def nextid(t):
        return c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {t}").fetchone()[0]

    for grp in (EARLY, LATE):
        O, P, F, SRC = grp["oil"], grp["parts"], grp["fluids"], grp["src"]
        for vid in grp["vids"]:
            for t in ("oil_change", "parts", "fluids", "maintenance", "torque_specs"):
                c.execute(f"DELETE FROM {t} WHERE vehicle_id=?", (vid,))
            c.execute("""INSERT INTO oil_change(vehicle_id,viscosity,oil_type,capacity_with_filter,
                         capacity_without_filter,oem_spec) VALUES(?,?,?,?,?,?)""",
                      (vid, O["viscosity"], O["oil_type"], O["capacity_with_filter"],
                       O["capacity_without_filter"], O["oem_spec"]))
            c.execute("""INSERT INTO parts(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
                         tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
                         tire_size_note,battery_notes) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                      (vid, P["spark_plug_type"], P["spark_plug_gap"], P["spark_plug_qty"],
                       P["tire_size"], P["tire_pressure_front"], P["tire_pressure_rear"],
                       P["spark_plugs_json"], P["tire_size_note"], P["battery_notes"]))
            c.execute("""INSERT INTO fluids(vehicle_id,transmission_fluid,transmission_capacity,
                         brake_fluid,coolant_type,coolant_capacity,power_steering_fluid)
                         VALUES(?,?,?,?,?,?,?)""",
                      (vid, F["transmission_fluid"], F["transmission_capacity"], F["brake_fluid"],
                       F["coolant_type"], F["coolant_capacity"], F["power_steering_fluid"]))
            for mi, mo, desc in MAINT:
                c.execute("""INSERT INTO maintenance(id,vehicle_id,mileage_interval,months_interval,
                             description,source,notes,difficulty_level) VALUES(?,?,?,?,?,?,?,?)""",
                          (nextid("maintenance"), vid, mi, mo, desc, SRC, "standard", None))
            for comp, ft, nm, note in TORQUE:
                c.execute("""INSERT INTO torque_specs(id,vehicle_id,component,torque_ft_lbs,torque_nm,notes)
                             VALUES(?,?,?,?,?,?)""", (nextid("torque_specs"), vid, comp, ft, nm, note))
            con.commit()
            print(f"  wrote id={vid} (visc {O['viscosity']})")

    print("\n=== verification ===")
    for vid in [38710, 38711, 38712, 38713]:
        o = c.execute("SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
        f = c.execute("SELECT coolant_type,coolant_capacity FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()
        print(f"  id={vid}: {o['viscosity']} | cap='{o['capacity_with_filter']}' | coolant {f['coolant_type']}/{f['coolant_capacity']}")
    con.close()
    print("\nDONE — Gen 2 verified specs written (4 vehicles).")


if __name__ == "__main__":
    main()
