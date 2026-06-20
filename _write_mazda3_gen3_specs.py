"""
Write VERIFIED Gen 3 (BM, 2014-2017) curated specs for Mazda 3 ids 38714-38717.

Sources (official Mazda owner's manuals): 2015 + 2017 Mazda3 4-door OMs.
See KYR_Mazda3_Spec_Verification_Log.md for page cites. SkyActiv-G 2.0 & 2.5, 0W-20.
Dual-value strings for engine-divergent fields (rendered as-is by valU()).

Gen-3 specifics (approved): flexible oil-life-monitor interval (mileage NULL, 12 mo);
electric power steering (no fluid); lug torque 108-147 N·m (80-108 ft·lbf). Tire
rotation differs by year (2014-15 = 5,000 mi; 2016-17 = flexible per 2017 manual).
Unverified fields (battery group/CCA, SkyActiv plug gap, drain/plug torque) left NULL.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
SRC = "Mazda Owner's Manual (2017, Schedule 1)"

OIL = dict(viscosity="0W-20", oil_type="Full Synthetic",
           capacity_with_filter="4.4 qt (SkyActiv 2.0) / 4.8 qt (SkyActiv 2.5)",
           capacity_without_filter="4.2 qt (SkyActiv 2.0) / 4.5 qt (SkyActiv 2.5)",
           oem_spec="0W-20 full synthetic (Mazda Genuine recommended); API/ILSAC certified")
PARTS = dict(spark_plug_type="Iridium", spark_plug_gap=None, spark_plug_qty=4,
             tire_size="P205/60R16", tire_pressure_front=36, tire_pressure_rear=36,
             spark_plugs_json=json.dumps([{"brand": "Mazda", "part_number": "PE5R-18-110",
                 "description": "OE iridium (SkyActiv-G 2.0 & 2.5; also PE5S-18-110)", "is_oem": True}]),
             tire_size_note=("Base 16-inch (P205/60R16): 250 kPa (36 psi) front/rear. "
                 "18-inch (215/45R18): 250 kPa (36 psi). Per owner's manual."),
             battery_notes=("i-ELOOP-equipped models use Mazda Q-85 (EFB) battery. BCI group size & CCA "
                 "for non-i-ELOOP models, and the SkyActiv spark-plug gap (factory pre-set), are not "
                 "published in the owner's manual."))
FLUIDS = dict(transmission_fluid="Mazda ATF FZ (6-speed SkyActiv-Drive)", transmission_capacity=None,
              brake_fluid="DOT 3", coolant_type="FL22",
              coolant_capacity="6.7-6.9 qt (varies by engine/transmission)",
              power_steering_fluid="Electric power steering (no fluid)")
TORQUE = [("lug_nut", 94.0, 127.0, "108-147 N·m (80-108 ft·lbf) per owner's manual")]

# maintenance: common rows + a year-specific tire-rotation row
MAINT_COMMON = [
    (None, 12, "Engine oil & filter change - flexible interval (oil-life monitor / wrench indicator); maximum 12 months"),
    (75000, None, "Spark plug replacement (iridium x4)"),
    (120000, 120, "Engine coolant (FL22) first replacement; thereafter every 60,000 mi / 5 yr"),
]
ROT_EARLY = (5000, None, "Tire rotation")                                   # 2014-2015 (per 2015 manual)
ROT_LATE  = (None, None, "Tire rotation - with each oil change (oil-life monitor)")  # 2016-2017 (per 2017 manual)
GROUPS = {38714: ROT_EARLY, 38715: ROT_EARLY, 38716: ROT_LATE, 38717: ROT_LATE}


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, DB + ".bak-gen3specs-" + ts)
    print("Backup:", os.path.basename(DB + ".bak-gen3specs-" + ts))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()

    def nextid(t):
        return c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {t}").fetchone()[0]

    for vid, rot in GROUPS.items():
        for t in ("oil_change", "parts", "fluids", "maintenance", "torque_specs"):
            c.execute(f"DELETE FROM {t} WHERE vehicle_id=?", (vid,))
        c.execute("""INSERT INTO oil_change(vehicle_id,viscosity,oil_type,capacity_with_filter,
                     capacity_without_filter,oem_spec) VALUES(?,?,?,?,?,?)""",
                  (vid, OIL["viscosity"], OIL["oil_type"], OIL["capacity_with_filter"],
                   OIL["capacity_without_filter"], OIL["oem_spec"]))
        c.execute("""INSERT INTO parts(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
                     tire_size,tire_pressure_front,tire_pressure_rear,spark_plugs_json,
                     tire_size_note,battery_notes) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                  (vid, PARTS["spark_plug_type"], PARTS["spark_plug_gap"], PARTS["spark_plug_qty"],
                   PARTS["tire_size"], PARTS["tire_pressure_front"], PARTS["tire_pressure_rear"],
                   PARTS["spark_plugs_json"], PARTS["tire_size_note"], PARTS["battery_notes"]))
        c.execute("""INSERT INTO fluids(vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
                     coolant_type,coolant_capacity,power_steering_fluid) VALUES(?,?,?,?,?,?,?)""",
                  (vid, FLUIDS["transmission_fluid"], FLUIDS["transmission_capacity"], FLUIDS["brake_fluid"],
                   FLUIDS["coolant_type"], FLUIDS["coolant_capacity"], FLUIDS["power_steering_fluid"]))
        for mi, mo, desc in (MAINT_COMMON + [rot]):
            c.execute("""INSERT INTO maintenance(id,vehicle_id,mileage_interval,months_interval,
                         description,source,notes,difficulty_level) VALUES(?,?,?,?,?,?,?,?)""",
                      (nextid("maintenance"), vid, mi, mo, desc, SRC, "standard", None))
        for comp, ft, nm, note in TORQUE:
            c.execute("""INSERT INTO torque_specs(id,vehicle_id,component,torque_ft_lbs,torque_nm,notes)
                         VALUES(?,?,?,?,?,?)""", (nextid("torque_specs"), vid, comp, ft, nm, note))
        con.commit()
        print(f"  wrote id={vid} (rotation={'5,000 mi' if rot is ROT_EARLY else 'flexible'})")

    print("\n=== verification ===")
    for vid in (38714, 38715, 38716, 38717):
        o = c.execute("SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
        f = c.execute("SELECT power_steering_fluid,coolant_type FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()
        oilrow = c.execute("SELECT mileage_interval,months_interval FROM maintenance WHERE vehicle_id=? AND description LIKE 'Engine oil%'", (vid,)).fetchone()
        print(f"  id={vid}: {o['viscosity']} | cap='{o['capacity_with_filter']}' | PS='{f['power_steering_fluid']}' | oil_interval mi={oilrow['mileage_interval']} mo={oilrow['months_interval']}")
    con.close()
    print("\nDONE - Gen 3 verified specs written (4 vehicles).")


if __name__ == "__main__":
    main()
