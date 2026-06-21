"""
PHASE 1 — Honda Accord 8th gen (2008-2012). Owner's-manual-VERIFIED curated specs
for ids 11378(2008), 11467(2009), 11561(2010), 11766(2012). Engines 2.4L I4 / 3.5L V6.

Source: official 2008 Honda Accord Sedan Owner's Manual (self-identifies p1),
techinfo.honda.com/rjanisis/pubs/om/acc080/acc0808om.pdf.

NOTE (pipeline finding): this older Honda OM is SPEC-THIN vs the 2013 Civic OM — it
publishes fluid TYPES + tire + lug torque + the Maintenance Minder, but NOT the oil/
coolant capacities or spark-plug part numbers. Those are left NULL -> Jazerie service-
manual queue. Discipline unchanged: verified-from-manual only; NULL anything not in it.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
VIDS = [11378, 11467, 11561, 11766]   # 2008, 2009, 2010, 2012 (8th gen)
V = "owner-manual-verified"
MSRC = "Honda Owner's Manual (2008 Accord Sedan, 8th gen)"

OIL = dict(viscosity="5W-20", oil_type=None, capacity_with_filter=None,
           capacity_without_filter=None, oem_spec="API-certified 5W-20")
PARTS = dict(spark_plug_type=None, spark_plug_gap=None, spark_plug_qty=None,
             tire_size="P215/60R16", tire_pressure_front=30, tire_pressure_rear=30,
             spark_plugs_json=None,
             tire_size_note=("Base 16-inch (P215/60R16) @ 30 psi front/rear; "
                 "17-inch (P225/50R17) @ 32 psi. Per owner's manual."),
             battery_notes=("Spark-plug type/number and oil/coolant capacities are not published in "
                 "the 2008 Accord owner's manual (service-manual data) - pending service-manual verification."))
FLUIDS = dict(transmission_fluid="Honda ATF-Z1 (automatic) / Honda MTF (manual)",
              transmission_capacity=None, brake_fluid="Honda DOT 3",
              coolant_type="Honda Type 2 (Long-Life)", coolant_capacity=None,
              power_steering_fluid="Honda PSF (hydraulic power steering)")
MAINT = [
    (None, 12, "Engine oil & filter change - Maintenance Minder (oil-life display); change at least every 12 months"),
    (None, 36, "Brake fluid replacement (Honda DOT 3) - every 3 years"),
    (None, None, "Tire rotation - per Maintenance Minder"),
]
TORQUE = [("lug_nut", 80.0, 108.0, "80 lbf-ft (108 N-m) per owner's manual")]


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, DB + ".bak-accordpilot-" + ts)
    print("Backup:", os.path.basename(DB + ".bak-accordpilot-" + ts))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()
    nid = lambda t: c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {t}").fetchone()[0]

    for VID in VIDS:
        for t in ("oil_change", "parts", "fluids", "maintenance", "torque_specs"):
            c.execute(f"DELETE FROM {t} WHERE vehicle_id=?", (VID,))
        c.execute("""INSERT INTO oil_change(vehicle_id,viscosity,oil_type,capacity_with_filter,
                     capacity_without_filter,oem_spec,source) VALUES(?,?,?,?,?,?,?)""",
                  (VID, OIL["viscosity"], OIL["oil_type"], OIL["capacity_with_filter"],
                   OIL["capacity_without_filter"], OIL["oem_spec"], V))
        c.execute("""INSERT INTO parts(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,tire_size,
                     tire_pressure_front,tire_pressure_rear,spark_plugs_json,tire_size_note,battery_notes,source)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (VID, PARTS["spark_plug_type"], PARTS["spark_plug_gap"], PARTS["spark_plug_qty"],
                   PARTS["tire_size"], PARTS["tire_pressure_front"], PARTS["tire_pressure_rear"],
                   PARTS["spark_plugs_json"], PARTS["tire_size_note"], PARTS["battery_notes"], V))
        c.execute("""INSERT INTO fluids(vehicle_id,transmission_fluid,transmission_capacity,brake_fluid,
                     coolant_type,coolant_capacity,power_steering_fluid,source) VALUES(?,?,?,?,?,?,?,?)""",
                  (VID, FLUIDS["transmission_fluid"], FLUIDS["transmission_capacity"], FLUIDS["brake_fluid"],
                   FLUIDS["coolant_type"], FLUIDS["coolant_capacity"], FLUIDS["power_steering_fluid"], V))
        for mi, mo, desc in MAINT:
            c.execute("""INSERT INTO maintenance(id,vehicle_id,mileage_interval,months_interval,description,source,notes,difficulty_level)
                         VALUES(?,?,?,?,?,?,?,?)""", (nid("maintenance"), VID, mi, mo, desc, MSRC, "standard", None))
        for comp, ft, nm, note in TORQUE:
            c.execute("""INSERT INTO torque_specs(id,vehicle_id,component,torque_ft_lbs,torque_nm,notes,source)
                         VALUES(?,?,?,?,?,?,?)""", (nid("torque_specs"), VID, comp, ft, nm, note, V))
        con.commit()
        yr = c.execute("SELECT year FROM vehicles WHERE id=?", (VID,)).fetchone()["year"]
        print(f"  wrote {yr} Accord (id={VID})")

    print("\n=== verification ===")
    for VID in VIDS:
        o = c.execute("SELECT viscosity,source FROM oil_change WHERE vehicle_id=?", (VID,)).fetchone()
        f = c.execute("SELECT brake_fluid,power_steering_fluid FROM fluids WHERE vehicle_id=?", (VID,)).fetchone()
        print(f"  id={VID}: oil {o['viscosity']} (src={o['source']}) | {f['brake_fluid']} | PS={f['power_steering_fluid']}")
    con.close()
    print("\nDONE - 8th-gen Accord (4 rows) verified-from-OM (capacities/plug -> Jazerie).")


if __name__ == "__main__":
    main()
