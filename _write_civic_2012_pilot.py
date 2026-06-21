"""
PILOT — verify-method generalization test (Honda).
Write owner's-manual-VERIFIED curated specs for the 2012 Honda Civic (id 11768,
9th gen 2012-2015). Source: official 2013 Honda Civic Sedan Owner's Manual
(techinfo.honda.com/rjanisis/pubs/om/r31313/r31313om.pdf), pp. 348-351 (specs),
p.322 (lug torque), pp.259-261 (Maintenance Minder). Same generation as the 2012;
exact-year 2012 OM not separately pulled (documented pilot limitation).

Discipline identical to the Mazda method: manufacturer source only, page-cited,
engine-divergent values as labeled dual strings, NULL anything not in the manual,
US-quart convention. 1.5L Hybrid is a separate manual -> not covered here.
"""
import sqlite3, os, shutil, datetime, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "wrench_vehicles.db")
VID = 11768  # 2012 Honda Civic
V = "owner-manual-verified"
MSRC = "Honda Owner's Manual (2013 Civic Sedan, 9th gen)"

OIL = dict(viscosity="0W-20", oil_type=None,
           capacity_with_filter="3.9 qt (1.8L) / 4.4 qt (2.4L Si)",
           capacity_without_filter="3.7 qt (1.8L) / 4.2 qt (2.4L Si)",
           oem_spec="API Premium-grade 0W-20 (Genuine Honda Motor Oil 0W-20)")
PARTS = dict(spark_plug_type="Iridium", spark_plug_gap=None, spark_plug_qty=4,
             tire_size="P195/65R15", tire_pressure_front=30, tire_pressure_rear=30,
             spark_plugs_json=json.dumps([
                 {"brand": "NGK", "part_number": "DILZKR7B11GS", "description": "OE iridium (1.8L)", "is_oem": True},
                 {"brand": "NGK", "part_number": "ILZKR7B-11S", "description": "OE iridium (2.4L Si)", "is_oem": True}]),
             tire_size_note=("1.8L LX/DX: P195/65R15 @ 30 psi. EX: P205/55R16 @ 32 psi. "
                 "Si (2.4L): P215/45R17 @ 32 psi. Per owner's manual specifications."),
             battery_notes=("OE battery 38Ah(5)/47Ah(20) per owner's manual; BCI group size & CCA "
                 "not specified. Iridium spark-plug gap is factory pre-set and not published in the OM."))
FLUIDS = dict(transmission_fluid="Honda ATF DW-1 (automatic) / Honda MTF (manual)",
              transmission_capacity=None, brake_fluid="Honda DOT 3",
              coolant_type="Honda Type 2 (Long-Life, 50/50)",
              coolant_capacity="5.9 qt (1.8L) / 5.8 qt (2.4L Si)",
              power_steering_fluid="Electric power steering (no fluid)")
MAINT = [
    (None, 12, "Engine oil & filter change - Maintenance Minder (oil-life display); change at least every 12 months"),
    (None, 36, "Brake fluid replacement (Honda DOT 3) - every 3 years"),
    (None, None, "Tire rotation - per Maintenance Minder (service item 1)"),
]
TORQUE = [("lug_nut", 80.0, 108.0, "80 lbf-ft (108 N-m) per owner's manual")]


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB, DB + ".bak-civicpilot-" + ts)
    print("Backup:", os.path.basename(DB + ".bak-civicpilot-" + ts))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; c = con.cursor()
    nid = lambda t: c.execute(f"SELECT COALESCE(MAX(id),0)+1 FROM {t}").fetchone()[0]

    for t in ("oil_change", "parts", "fluids", "maintenance", "torque_specs"):
        c.execute(f"DELETE FROM {t} WHERE vehicle_id=?", (VID,))
    c.execute("""INSERT INTO oil_change(vehicle_id,viscosity,oil_type,capacity_with_filter,
                 capacity_without_filter,oem_spec,source) VALUES(?,?,?,?,?,?,?)""",
              (VID, OIL["viscosity"], OIL["oil_type"], OIL["capacity_with_filter"],
               OIL["capacity_without_filter"], OIL["oem_spec"], V))
    c.execute("""INSERT INTO parts(vehicle_id,spark_plug_type,spark_plug_gap,spark_plug_qty,tire_size,
                 tire_pressure_front,tire_pressure_rear,spark_plugs_json,tire_size_note,battery_notes,source)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
              (VID, PARTS["spark_plug_type"], PARTS["spark_plug_gap"], PARTS["spark_plug_qty"], PARTS["tire_size"],
               PARTS["tire_pressure_front"], PARTS["tire_pressure_rear"], PARTS["spark_plugs_json"],
               PARTS["tire_size_note"], PARTS["battery_notes"], V))
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

    print("\n=== verification (2012 Civic id 11768) ===")
    o = c.execute("SELECT viscosity,capacity_with_filter,source FROM oil_change WHERE vehicle_id=?", (VID,)).fetchone()
    f = c.execute("SELECT brake_fluid,coolant_type,power_steering_fluid,source FROM fluids WHERE vehicle_id=?", (VID,)).fetchone()
    print(f"  oil: {o['viscosity']} | {o['capacity_with_filter']} | src={o['source']}")
    print(f"  fluids: {f['brake_fluid']} / {f['coolant_type']} / PS={f['power_steering_fluid']} | src={f['source']}")
    print(f"  maintenance rows: {c.execute('SELECT COUNT(*) FROM maintenance WHERE vehicle_id=?', (VID,)).fetchone()[0]}")
    print(f"  torque: {c.execute('SELECT torque_ft_lbs FROM torque_specs WHERE vehicle_id=?', (VID,)).fetchone()['torque_ft_lbs']} ft-lb")
    con.close()
    print("\nDONE - Civic pilot specs written (verified).")


if __name__ == "__main__":
    main()
