"""Fuel-economy repair, part 10 (ruling (c), 2026-11-20): tests for _repair_fuel_economy_versions_fill.py.

Rule under test: a row keeps, labelled, every version EPA lists under its nameplate (ruling (c), "Accept the rule"),
so it also gains the version records it never stored (Robert, "Yes, dry run it"): hybrid and plug-in hybrid versions
under their own EPA name, performance versions, body styles. Out, as already ruled: electric and fuel-cell records
on a gasoline row (Kona Electric), hydrogen fuel, longer bodies, special-purpose versions, the Hyundai N models,
another vehicle. Records whose figures a stored line holds in pre-revision form are left (item e). Rows that gain a
line take EPA's current yearly cost on every line with an EPA record. Fixtures are literals.

    python -I -m unittest discover -s tests -t . -p "test_fe_versions_fill.py"
"""
import os
import sqlite3
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "files")):
    if p not in sys.path:
        sys.path.insert(0, p)

AWD8 = ("Automatic (S8)", "All-Wheel Drive")
FWD = ("Automatic (AV-S8)", "Front-Wheel Drive")
A1 = ("Automatic (A1)", "All-Wheel Drive")


def V(i, year, make, name, city, hwy, comb, displ, trans, drive, atv="", cost=2000, fuel="Regular"):
    return {"id": i, "year": year, "make": make, "name": name, "atv": atv, "city": city, "hwy": hwy, "comb": comb,
            "displ": displ, "trans": trans, "drive": drive, "range": None, "tcharger": "", "scharger": "",
            "eng_dscr": "", "vclass": "", "startstop": "", "trans_dscr": "", "engid": "",
            "cost": cost, "fuel": fuel, "displ_text": "%.1f" % displ if displ is not None else None}


EPA = {
    (2020, "toyota"): [V(41, 2020, "Toyota", "Camry", 28, 39, 32, 2.5, *FWD, cost=2200),
                       V(42, 2020, "Toyota", "Camry Hybrid LE", 51, 53, 52, 2.5, *FWD, atv="Hybrid", cost=1250),
                       V(43, 2020, "Toyota", "Camry Hybrid XLE/SE", 44, 47, 46, 2.5, *FWD, atv="Hybrid", cost=1400)],
    (2024, "bmw"): [V(11, 2024, "BMW", "X3 sDrive30i", 23, 29, 25, 2.0, *AWD8, cost=2100),
                    V(14, 2024, "BMW", "X3 M", 16, 21, 18, 3.0, *AWD8, cost=3100)],
    (2021, "ford"): [V(51, 2021, "Ford", "Escape FWD", 28, 34, 30, 1.5, *FWD, cost=1700),
                     V(52, 2021, "Ford", "Escape FWD PHEV", 40, 37, 38, 2.5, *FWD, atv="Plug-in Hybrid", cost=1300,
                       fuel="Regular Gas and Electricity"),
                     V(53, 2021, "Ford", "Escape Police AWD", 20, 26, 22, 2.0, *AWD8, cost=2300)],
    (2023, "ford"): [V(61, 2023, "Ford", "F150 Pickup 4WD", 18, 23, 20, 3.5, *AWD8, cost=2900),
                     V(62, 2023, "Ford", "F150 Lightning 4WD", None, None, 70, None, *A1, atv="EV", cost=900, fuel="Electricity")],
    (2025, "honda"): [V(71, 2025, "Honda", "CR-V FWD", 28, 34, 30, 1.5, *FWD, cost=1700),
                      V(72, 2025, "Honda", "CR-V e-FCEV", 58, 49, 54, 1.0, *A1, atv="Plug-in Hybrid", cost=1900,
                        fuel="Electricity and Hydrogen")],
    (2020, "hyundai"): [V(81, 2020, "Hyundai", "Kona FWD", 30, 35, 32, 2.0, *FWD, cost=1600),
                        V(82, 2020, "Hyundai", "Kona N", 19, 27, 22, 2.0, *FWD, cost=2300)],
    (2020, "gmc"): [V(91, 2020, "GMC", "Yukon 2WD", 16, 22, 18, 5.3, *AWD8, cost=3100),
                    V(92, 2020, "GMC", "Yukon XL 2WD", 15, 21, 17, 5.3, *AWD8, cost=3200)],
    (2020, "audi"): [V(31, 2020, "Audi", "A4", 24, 31, 27, 2.0, *AWD8, cost=2000),
                     V(32, 2020, "Audi", "A4 allroad quattro", 24, 30, 26, 2.0, *AWD8, cost=2050)],
    (2026, "toyota"): [V(21, 2026, "Toyota", "RAV4 AWD", 27, 34, 30, 2.5, *FWD, cost=1700),
                       V(22, 2026, "Toyota", "RAV4 Hybrid AWD", 43, 38, 41, 2.5, *FWD, atv="Hybrid", cost=1200)],
}
PLATES = {"Toyota": {"Camry", "RAV4"}, "BMW": {"X3"}, "Ford": {"Escape", "F-150"}, "Honda": {"CR-V"}, "Hyundai": {"Kona"},
          "GMC": {"Yukon"}, "Audi": {"A4"}}
VEHICLES = [(1, 2020, "Toyota", "Camry"), (2, 2024, "BMW", "X3"), (3, 2021, "Ford", "Escape"), (4, 2023, "Ford", "F-150"),
            (5, 2025, "Honda", "CR-V"), (6, 2020, "Hyundai", "Kona"), (7, 2020, "GMC", "Yukon"), (8, 2020, "Audi", "A4"),
            (9, 2026, "Toyota", "RAV4")]
# (fe id, vehicle id, city, hwy, comb, cost, engine, trans, drive)
LINES = [(101, 1, 28, 39, 32, 2000, "2.5", *FWD),            # Camry, older cost: refreshed when the row gains lines
         (102, 1, 51, 53, 52, 1250, "2.5", *FWD),            # Camry Hybrid LE already stored
         (201, 2, 23, 29, 25, 2100, "2.0", *AWD8),
         (301, 3, 28, 34, 30, 1700, "1.5", *FWD),
         (401, 4, 18, 23, 20, 2900, "3.5", *AWD8),
         (501, 5, 28, 34, 30, 1700, "1.5", *FWD),
         (601, 6, 30, 35, 32, 1600, "2.0", *FWD),
         (701, 7, 16, 22, 18, 3100, "5.3", *AWD8),
         (801, 8, 24, 31, 27, 2000, "2.0", *AWD8),
         (901, 9, 27, 34, 30, 1700, "2.5", *FWD),
         (902, 9, 40, 37, 39, 1300, "2.5", *FWD)]           # a RAV4 Hybrid line EPA has since revised (item e)


def fleet():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT)")
    con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, "
                "highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, "
                "drive TEXT, range_miles INTEGER, mpge INTEGER, fuel_type TEXT, range_ev INTEGER, city_ev INTEGER, "
                "hwy_ev INTEGER, comb_ev INTEGER)")
    con.executemany("INSERT INTO vehicles VALUES (?,?,?,?)", VEHICLES)
    con.executemany("INSERT INTO fuel_economy (id, vehicle_id, city_mpg, highway_mpg, combined_mpg, annual_fuel_cost, engine, "
                    "transmission, drive) VALUES (?,?,?,?,?,?,?,?,?)", LINES)
    con.commit()
    return con


class TestDiscoverVersions(unittest.TestCase):
    def setUp(self):
        import _repair_fuel_economy_versions_fill
        self.rf = _repair_fuel_economy_versions_fill
        self.ops, self.revised, self.left_out = self.rf.discover(fleet().cursor(), EPA, PLATES)
        self.by_id = {o["id"]: o for o in self.ops}

    def test_rows_that_gain_lines(self):
        self.assertEqual(sorted(self.by_id), [1, 2, 3, 8])

    def test_hybrid_version_added_once(self):
        self.assertEqual(self.by_id[1]["add"], [43])                    # Camry Hybrid LE (42) is already stored

    def test_performance_version_added(self):
        self.assertEqual(self.by_id[2]["add"], [14])

    def test_plug_in_hybrid_added_special_purpose_not(self):
        self.assertEqual(self.by_id[3]["add"], [52])

    def test_body_style_added_longer_body_not(self):
        self.assertEqual(self.by_id[8]["add"], [32])
        self.assertNotIn(7, self.by_id)

    def test_electric_hydrogen_and_n_models_stay_out(self):
        for vid in (4, 5, 6):
            self.assertNotIn(vid, self.by_id)
        self.assertEqual(sorted(self.left_out), [(4, 62, "electric or fuel cell"), (5, 72, "hydrogen fuel")])

    def test_revised_twin_left_for_item_e(self):
        self.assertNotIn(9, self.by_id)
        self.assertEqual(self.revised, [(9, 22)])

    def test_rows_that_gain_lines_take_the_current_cost(self):
        self.assertEqual(self.by_id[1]["cost"], 1)                      # Camry 2000 -> 2200
        self.assertEqual(self.by_id[2]["cost"], 0)


class TestPlanVersions(unittest.TestCase):
    def setUp(self):
        import _repair_fuel_economy_versions_fill
        self.rf = _repair_fuel_economy_versions_fill

    def test_plan_kinds_and_rows(self):
        cur = fleet().cursor()
        ops, _r, _l = self.rf.discover(cur, EPA, PLATES)
        plan = {p["id"]: p for p in self.rf.plan_ops(cur, EPA, PLATES, ops)}
        self.assertEqual(plan[1]["kinds"], ["hybrid version"])
        self.assertEqual(plan[2]["kinds"], ["performance version"])
        self.assertEqual(plan[3]["kinds"], ["plug-in hybrid version"])
        self.assertEqual(plan[8]["kinds"], ["body style"])
        self.assertEqual(plan[1]["cost_updates"], [[101, 2000, 2200]])
        self.assertEqual(plan[3]["insert"][0][:7], [40, 37, 38, 1300, "2.5", *FWD])
        self.assertEqual(plan[3]["remove"], [])

    def test_plan_refuses_an_op_that_is_not_the_rule(self):
        cur = fleet().cursor()
        ops, _r, _l = self.rf.discover(cur, EPA, PLATES)
        bad = [dict(o, add=o["add"] + [92]) if o["id"] == 1 else o for o in ops]
        with self.assertRaises(self.rf.PlanError):
            self.rf.plan_ops(cur, EPA, PLATES, bad)

    def test_new_lines_are_versions_after_the_plain_car(self):
        import _label_fuel_economy as lf
        import _repair_fuel_economy_versions as v9
        con = fleet()
        cur = con.cursor()
        ops, _r, _l = self.rf.discover(cur, EPA, PLATES)
        v9.apply_ops(cur, self.rf.plan_ops(cur, EPA, PLATES, ops))
        lf.ensure_columns(cur)
        lf.apply(cur, lf.plan_labels(cur, EPA, PLATES))
        rows = {r[0]: r[1:] for r in cur.execute("SELECT combined_mpg, epa_label, epa_plain FROM fuel_economy WHERE vehicle_id=2")}
        self.assertEqual(rows, {25: ("X3 sDrive30i", 1), 18: ("X3 M", 0)})
        self.assertEqual(self.rf.discover(cur, EPA, PLATES)[0], [])     # a second run finds nothing left to add


if __name__ == "__main__":
    unittest.main()
