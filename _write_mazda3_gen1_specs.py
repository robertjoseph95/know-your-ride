"""
Write VERIFIED Gen 1 (BK, 2005-2009) curated specs to the DB for Mazda 3 ids 38705-38709.

Every value here was read from the official Mazda owner's manual PDFs (2008 5-door,
cross-checked vs 2006 4-door) — see KYR_Mazda3_Spec_Verification_Log.md for page cites.
Unverified fields (battery group/CCA, drain-plug & spark-plug torque, filter part numbers,
oil_type synthetic/conventional, auto trans capacity which differs by 4-sp/5-sp) are left
NULL so the specSoon() "coming soon" state remains.

UNIT CONVENTION (confirmed by Robert): store values in the unit the UI label displays.
Oil/coolant capacities are stored in US QUARTS (the Oil/Fluids tabs label them "qts").

Idempotent: clears any existing curated rows for these 5 vids, then inserts.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
VIDS = [38705, 38706, 38707, 38708, 38709]   # 2005-2009
SRC = "Mazda Owner's Manual (2008, Schedule 1)"

# ---- verified values (Gen 1 BK, 2.0L & 2.3L non-turbo) ----
OIL = dict(viscosity="5W-20", oil_type=None, capacity_with_filter=4.5,
           capacity_without_filter=4.1, oem_spec="API SM / ILSAC GF-4",
           filters_json=None, drain_bolt_json=None, socket=None, thread=None, gasket=None)

PARTS = dict(
    spark_plug_type="Iridium", spark_plug_gap="0.050-0.053", spark_plug_qty=4,
    battery_group=None, battery_cca=None,
    tire_size="P195/65R15", tire_pressure_front=34, tire_pressure_rear=34,
    spark_plugs_json=json.dumps([{"brand": "Mazda", "part_number": "LFG1-18-110",
                                  "description": "OE iridium spark plug", "is_oem": True}]),
    air_filters_json=None, cabin_filters_json=None, wiper_blades_json=None, batteries_json=None,
    tire_size_note=("Base 15-inch wheel: 230 kPa (34 psi) front/rear. Optional 16-inch "
                    "(P205/55R16) & 17-inch (P205/50R17): 220 kPa (32 psi). Per owner's manual "
                    "tire-pressure label."),
    battery_notes=("Owner's manual lists OE battery as 40-55 Ah; BCI group size and CCA are not "
                   "specified by Mazda."),
    timing_type=None, timing_notes=None, real_world_interval_miles=None, real_world_notes=None)

FLUIDS = dict(transmission_fluid="Mazda ATF M-V (automatic)", transmission_capacity=None,
              brake_fluid="DOT 3", coolant_type="FL22", coolant_capacity=7.9,
              power_steering_fluid="Mazda ATF M-III (Dexron II equiv.)", differential_fluids_json=None)

MAINT = [
    (7500, 12,  "Engine oil & filter change (SAE 5W-20)"),
    (7500, None, "Tire rotation"),
    (25000, 24, "Cabin air filter replacement"),
    (75000, None, "Spark plug replacement (iridium x4)"),
    (120000, 120, "Engine coolant (FL22) first replacement; thereafter every 60,000 mi / 5 yr"),
]
TORQUE = [("lug_nut", 76.0, 103.0, "89-117 N·m (66-86 ft·lbf) per owner's manual")]


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DB + ".bak-gen1specs-" + ts
    shutil.copy2(DB, bak)
    print("Backup:", os.path.basename(bak))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()

    def nextid(table):
        return c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {table}").fetchone()[0]

    for vid in VIDS:
        # idempotent clear
        for t in ("oil_change", "parts", "fluids", "maintenance", "torque_specs"):
            c.execute(f"DELETE FROM {t} WHERE vehicle_id=?", (vid,))

        c.execute("""INSERT INTO oil_change(vehicle_id,viscosity,oil_type,capacity_with_filter,
                     capacity_without_filter,oem_spec,filters_json,drain_bolt_json,socket,thread,gasket)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (vid, OIL["viscosity"], OIL["oil_type"], OIL["capacity_with_filter"],
                   OIL["capacity_without_filter"], OIL["oem_spec"], OIL["filters_json"],
                   OIL["drain_bolt_json"], OIL["socket"], OIL["thread"], OIL["gasket"]))

        c.execute("""INSERT INTO parts(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,
                     battery_group,battery_cca,tire_size,tire_pressure_front,tire_pressure_rear,
                     spark_plugs_json,air_filters_json,cabin_filters_json,wiper_blades_json,batteries_json,
                     tire_size_note,battery_notes,timing_type,timing_notes,real_world_interval_miles,real_world_notes)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (vid, PARTS["spark_plug_type"], PARTS["spark_plug_gap"], PARTS["spark_plug_qty"],
                   PARTS["battery_group"], PARTS["battery_cca"], PARTS["tire_size"],
                   PARTS["tire_pressure_front"], PARTS["tire_pressure_rear"], PARTS["spark_plugs_json"],
                   PARTS["air_filters_json"], PARTS["cabin_filters_json"], PARTS["wiper_blades_json"],
                   PARTS["batteries_json"], PARTS["tire_size_note"], PARTS["battery_notes"],
                   PARTS["timing_type"], PARTS["timing_notes"], PARTS["real_world_interval_miles"],
                   PARTS["real_world_notes"]))

        c.execute("""INSERT INTO fluids(vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
                     coolant_type,coolant_capacity,power_steering_fluid,differential_fluids_json)
                     VALUES(?,?,?,?,?,?,?,?)""",
                  (vid, FLUIDS["transmission_fluid"], FLUIDS["transmission_capacity"], FLUIDS["brake_fluid"],
                   FLUIDS["coolant_type"], FLUIDS["coolant_capacity"], FLUIDS["power_steering_fluid"],
                   FLUIDS["differential_fluids_json"]))

        for mi, mo, desc in MAINT:
            c.execute("""INSERT INTO maintenance(id,vehicle_id,mileage_interval,months_interval,
                         description,source,notes,difficulty_level) VALUES(?,?,?,?,?,?,?,?)""",
                      (nextid("maintenance"), vid, mi, mo, desc, SRC, "standard", None))

        for comp, ft, nm, note in TORQUE:
            c.execute("""INSERT INTO torque_specs(id,vehicle_id,component,torque_ft_lbs,torque_nm,notes)
                         VALUES(?,?,?,?,?,?)""", (nextid("torque_specs"), vid, comp, ft, nm, note))

        con.commit()
        print(f"  wrote curated specs for id={vid}")

    # verify
    print("\n=== verification ===")
    for vid in VIDS:
        o = c.execute("SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?", (vid,)).fetchone()
        p = c.execute("SELECT spark_plug_type,spark_plug_gap,tire_size FROM parts WHERE vehicle_id=?", (vid,)).fetchone()
        f = c.execute("SELECT brake_fluid,coolant_type,coolant_capacity FROM fluids WHERE vehicle_id=?", (vid,)).fetchone()
        m = c.execute("SELECT COUNT(*) FROM maintenance WHERE vehicle_id=?", (vid,)).fetchone()[0]
        tq = c.execute("SELECT COUNT(*) FROM torque_specs WHERE vehicle_id=?", (vid,)).fetchone()[0]
        print(f"  id={vid}: oil {o['viscosity']}/{o['capacity_with_filter']}qt | plug {p['spark_plug_type']} {p['spark_plug_gap']} | tire {p['tire_size']} | {f['brake_fluid']}/{f['coolant_type']}/{f['coolant_capacity']}qt | maint={m} torque={tq}")
    con.close()
    print("\nDONE — Gen 1 verified specs written (5 vehicles).")


if __name__ == "__main__":
    main()
