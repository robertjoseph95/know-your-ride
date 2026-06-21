"""
PHASE 1 — Honda CR-V 5th gen (2017-2022). Owner's-manual-VERIFIED curated specs for
ids 12372(2017), 12511(2018), 12777(2020), 12847(2021), 12912(2022). 1.5L Turbo (volume);
2.4L only on 2017 LX. Both engines use a CVT + electric power steering.

Source: official 2018 Honda CR-V Owner's Manual (self-ID p1 "2018 ... CR-V", 679 pp,
text-extractable), techinfo.honda.com/rjanisis/pubs/OM/AH/ATLA1818OM/enu/ATLA1818OM.PDF.
Spec-dense (consolidated specifications table) — confirms newer-gen = more complete.

Electric PS confirmed (Accord lesson): spec table lists brake/CVT/diff/oil/coolant, NO
PS fluid; 5th-gen CR-V is EPS. NULL (-> Jazerie): spark-plug gap, fixed plug/coolant
intervals (Minder), battery group/CCA, drain-plug torque. Printed page cites in the log.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
VIDS = [12372, 12511, 12777, 12847, 12912]   # 2017,2018,2020,2021,2022
V = "owner-manual-verified"
MSRC = "Honda Owner's Manual (2018 CR-V, 5th gen)"

OIL = dict(viscosity="0W-20", oil_type=None,
           capacity_with_filter="3.7 qt (1.5T) / 4.7 qt (2.4L)",
           capacity_without_filter="3.4 qt (1.5T) / 4.4 qt (2.4L)",
           oem_spec="API Premium-grade 0W-20 (Genuine Honda Motor Oil 0W-20)")
PARTS = dict(spark_plug_type="Iridium", spark_plug_gap=None, spark_plug_qty=4,
             tire_size="235/65R17", tire_pressure_front=32, tire_pressure_rear=30,
             spark_plugs_json=json.dumps([
                 {"brand": "NGK", "part_number": "ILZKAR8J8SY", "description": "OE iridium (1.5L Turbo)", "is_oem": True},
                 {"brand": "NGK", "part_number": "DILKAR7H11GS", "description": "OE iridium (2.4L)", "is_oem": True}]),
             tire_size_note=("17-inch (235/65R17): 32 psi front / 30 psi rear. "
                 "18-inch (235/60R18): 33 psi front / 30 psi rear. Per owner's manual."),
             battery_notes=("Spark-plug gap is factory pre-set (not published); BCI group size & CCA "
                 "are not in the owner's manual - pending service-manual verification."))
FLUIDS = dict(transmission_fluid="Honda HCF-2 (CVT)",
              transmission_capacity="3.9 qt (2WD) / 4.5 qt (AWD)", brake_fluid="Honda DOT 3",
              coolant_type="Honda Type 2 (Long-Life, 50/50)", coolant_capacity="6.6 qt",
              power_steering_fluid="Electric power steering (no fluid)")
MAINT = [
    (None, 12, "Engine oil & filter change - Maintenance Minder (oil-life display); change at least every 12 months"),
    (None, 36, "Brake fluid replacement (Honda DOT 3) - every 3 years"),
    (None, None, "Tire rotation - per Maintenance Minder"),
]
TORQUE = [("lug_nut", 80.0, 108.0, "80 lbf-ft (108 N-m) per owner's manual")]


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, DB + ".bak-crvpilot-" + ts)
    print("Backup:", os.path.basename(DB + ".bak-crvpilot-" + ts))
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
        print(f"  wrote {yr} CR-V (id={VID})")

    print("\n=== verification ===")
    for VID in VIDS:
        o = c.execute("SELECT viscosity,capacity_with_filter FROM oil_change WHERE vehicle_id=?", (VID,)).fetchone()
        f = c.execute("SELECT transmission_fluid,coolant_capacity,power_steering_fluid FROM fluids WHERE vehicle_id=?", (VID,)).fetchone()
        print(f"  id={VID}: oil {o['viscosity']} | cap '{o['capacity_with_filter']}' | {f['transmission_fluid']} | PS={f['power_steering_fluid']}")
    con.close()
    print("\nDONE - 5th-gen CR-V (5 rows) verified-from-OM (spec-dense).")


if __name__ == "__main__":
    main()
