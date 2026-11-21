"""Fuel-economy repair, part 9 (ruling (c), 2026-11-20): tests for _repair_fuel_economy_versions.py.

Rule under test (Robert, "Accept the rule" then "Approve approach"): a row keeps, labelled, every version EPA lists
under its nameplate; it gains the own-name records the every-own-record fill held back (hybrids filed under the
plain name, performance-leaning trims, SRT-8, the four-door Wrangler incl. Wrangler Unlimited, the F-150 XL / XLT
trim); chassis-cab lines come out and chassis-cab records stay out; on every row the change touches (adds, removes,
or two fuel-price years) each line with an EPA record takes EPA's current yearly cost. Fixtures are literals; no
test writes to a real database file.

    python -I -m unittest discover -s tests -t . -p "test_fe_versions.py"
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
RWD6 = ("Automatic 6-spd", "Rear-Wheel Drive")
FWD = ("Automatic (AV-S8)", "Front-Wheel Drive")


def V(i, year, make, name, city, hwy, comb, displ, trans, drive, atv="", cost=2000, fuel="Regular"):
    """An EPA record as the repair's load_epa returns it."""
    return {"id": i, "year": year, "make": make, "name": name, "atv": atv, "city": city, "hwy": hwy, "comb": comb,
            "displ": displ, "trans": trans, "drive": drive, "range": None, "tcharger": "", "scharger": "",
            "eng_dscr": "", "vclass": "", "startstop": "", "trans_dscr": "", "engid": "",
            "cost": cost, "fuel": fuel, "displ_text": "%.1f" % displ}


EPA = {
    (2024, "bmw"): [V(11, 2024, "BMW", "X3 sDrive30i", 23, 29, 25, 2.0, *AWD8, cost=2100),
                    V(12, 2024, "BMW", "X3 M40i", 21, 26, 23, 3.0, *AWD8, cost=2500),            # performance-leaning trim: add
                    V(14, 2024, "BMW", "X3 M", 16, 21, 18, 3.0, *AWD8, cost=3100),               # performance version: not stored, not added
                    V(17, 2024, "BMW", "X3 xDrive30i", 24, 30, 26, 2.0, *AWD8, atv="Hybrid", cost=2050)],  # hybrid, plain name: add
    (2019, "chevrolet"): [V(21, 2019, "Chevrolet", "Silverado C15 2WD", 17, 23, 19, 5.3, *RWD6, cost=3000),
                          V(22, 2019, "Chevrolet", "Silverado C15 Cab Chassis 2WD", 15, 19, 17, 4.3, *RWD6, cost=3300),
                          V(23, 2019, "Chevrolet", "Silverado C15 Cab Chassis 4WD", 14, 18, 16, 4.3, *RWD6, cost=3500)],
    (2026, "toyota"): [V(31, 2026, "Toyota", "RAV4 AWD XLE", 43, 38, 41, 2.5, *FWD, atv="Hybrid", cost=1200)],   # revised twin
    (2020, "toyota"): [V(41, 2020, "Toyota", "Camry", 28, 39, 32, 2.5, *FWD, cost=2200),
                       V(42, 2020, "Toyota", "Camry Hybrid LE", 51, 53, 52, 2.5, *FWD, atv="Hybrid", cost=1250)],
    (2021, "ford"): [V(51, 2021, "Ford", "Mustang", 21, 30, 25, 2.3, *RWD6, cost=2400),
                     V(52, 2021, "Ford", "Mustang Convertible", 20, 28, 23, 2.3, *RWD6, cost=2600)],
    (2018, "jeep"): [V(64, 2018, "Jeep", "Wrangler 4dr 4WD", 17, 23, 19, 3.6, *AWD8, cost=2900),           # first of its six fields
                     V(61, 2018, "Jeep", "Wrangler 2dr 4WD", 18, 23, 20, 3.6, *AWD8, cost=2800),
                     V(62, 2018, "Jeep", "Wrangler Unlimited 4WD", 17, 22, 19, 3.6, *AWD8, cost=2950),
                     V(63, 2018, "Jeep", "Wrangler 4dr 4WD", 17, 23, 19, 3.6, *AWD8, cost=2900)],
    (2020, "gmc"): [V(71, 2020, "GMC", "Yukon 2WD", 16, 22, 18, 5.3, *RWD6, cost=3100),
                    V(72, 2020, "GMC", "Yukon XL 2WD", 15, 21, 17, 5.3, *RWD6, cost=3200)],               # longer body: out
}
PLATES = {"BMW": {"X3"}, "Chevrolet": {"Silverado 1500"}, "Toyota": {"RAV4", "Camry"}, "Ford": {"Mustang"},
          "Jeep": {"Wrangler"}, "GMC": {"Yukon"}}
VEHICLES = [(1, 2024, "BMW", "X3"), (2, 2019, "Chevrolet", "Silverado 1500"), (3, 2026, "Toyota", "RAV4"),
            (4, 2020, "Toyota", "Camry"), (5, 2021, "Ford", "Mustang"), (6, 2018, "Jeep", "Wrangler"), (7, 2020, "GMC", "Yukon")]
# (fe id, vehicle id, city, hwy, comb, cost, engine, trans, drive)
LINES = [(101, 1, 23, 29, 25, 2000, "2.0", *AWD8),           # X3 sDrive30i, older cost
         (201, 2, 17, 23, 19, 3000, "5.3", *RWD6),           # Silverado C15 2WD, current cost
         (202, 2, 15, 19, 17, 3300, "4.3", *RWD6),           # chassis cab only: comes out
         (301, 3, 40, 37, 39, 1300, "2.5", *FWD),            # RAV4 2026: figures EPA has since revised (item e)
         (401, 4, 28, 39, 32, 2000, "2.5", *FWD),            # Camry, older cost, row untouched
         (501, 5, 21, 30, 25, 2400, "2.3", *RWD6),           # Mustang, current cost
         (502, 5, 20, 28, 23, 2500, "2.3", *RWD6),           # Mustang Convertible, older cost: two price years
         (601, 6, 18, 23, 20, 2800, "3.6", *AWD8),           # Wrangler 2dr
         (701, 7, 16, 22, 18, 3100, "5.3", *RWD6)]           # Yukon


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


class TestDiscover(unittest.TestCase):
    def setUp(self):
        import _repair_fuel_economy_versions
        self.rv = _repair_fuel_economy_versions
        self.ops, self.revised = self.rv.discover(fleet().cursor(), EPA, PLATES)
        self.by_id = {o["id"]: o for o in self.ops}

    def test_rows_touched(self):
        self.assertEqual(sorted(self.by_id), [1, 2, 5, 6])

    def test_held_own_names_are_added(self):
        self.assertEqual(self.by_id[1]["add"], [12, 17])               # M40i trim, mild hybrid under the plain name

    def test_versions_never_stored_are_not_added(self):
        self.assertNotIn(14, self.by_id[1]["add"])                     # X3 M (performance version): a later fill
        self.assertNotIn(4, self.by_id)                                # Camry Hybrid LE (hybrid version): a later fill

    def test_chassis_cab_line_comes_out_and_records_stay_out(self):
        self.assertEqual((self.by_id[2]["add"], self.by_id[2]["remove"]), ([], [202]))

    def test_four_door_wrangler_and_unlimited_added_first_record_of_its_line(self):
        self.assertEqual(self.by_id[6]["add"], [62, 64])               # 64 comes before its twin 63 in EPA's file

    def test_longer_body_stays_out(self):
        self.assertNotIn(7, self.by_id)

    def test_revised_twin_left_for_item_e(self):
        self.assertNotIn(3, self.by_id)
        self.assertEqual(self.revised, [(3, 31)])

    def test_cost_refresh_only_on_touched_rows(self):
        self.assertEqual(self.by_id[1]["cost"], 1)                     # row gains lines: its older cost is refreshed
        self.assertEqual(self.by_id[5]["cost"], 1)                     # two price years: refreshed
        self.assertEqual(self.by_id[2]["cost"], 0)


class TestPlanAndApply(unittest.TestCase):
    def setUp(self):
        import _repair_fuel_economy_versions
        self.rv = _repair_fuel_economy_versions

    def _planned(self):
        con = fleet()
        cur = con.cursor()
        ops, _rev = self.rv.discover(cur, EPA, PLATES)
        return con, cur, self.rv.plan_ops(cur, EPA, PLATES, ops)

    def test_plan_rows(self):
        _con, _cur, plan = self._planned()
        p1 = next(p for p in plan if p["id"] == 1)
        self.assertEqual(p1["cost_updates"], [[101, 2000, 2100]])
        self.assertEqual([x[:7] for x in p1["insert"]], [[21, 26, 23, 2500, "3.0", *AWD8], [24, 30, 26, 2050, "2.0", *AWD8]])
        self.assertEqual(p1["sources"], [["X3 M40i", 12, ""], ["X3 xDrive30i", 17, "Hybrid"]])

    def test_apply_writes_exactly_the_plan(self):
        _con, cur, plan = self._planned()
        self.rv.apply_ops(cur, plan)
        rows = lambda vid: [r[0] for r in cur.execute("SELECT combined_mpg FROM fuel_economy WHERE vehicle_id=? ORDER BY id", (vid,))]
        self.assertEqual(rows(1), [25, 23, 26])
        self.assertEqual(rows(2), [19])
        self.assertEqual(cur.execute("SELECT annual_fuel_cost FROM fuel_economy WHERE id=502").fetchone()[0], 2600)
        self.assertEqual(cur.execute("SELECT annual_fuel_cost FROM fuel_economy WHERE id=401").fetchone()[0], 2000)

    def test_plan_refuses_an_op_that_is_not_the_rule(self):
        con = fleet()
        cur = con.cursor()
        ops, _rev = self.rv.discover(cur, EPA, PLATES)
        bad = [dict(o, add=o["add"] + [14]) if o["id"] == 1 else o for o in ops]
        with self.assertRaises(self.rv.PlanError):
            self.rv.plan_ops(cur, EPA, PLATES, bad)

    def test_apply_refuses_a_changed_row(self):
        _con, cur, plan = self._planned()
        cur.execute("UPDATE fuel_economy SET combined_mpg=26 WHERE id=101")
        with self.assertRaises(RuntimeError):
            self.rv.apply_ops(cur, plan)

    def test_labels_and_order_after_the_repair(self):
        import _label_fuel_economy as lf
        _con, cur, plan = self._planned()
        self.rv.apply_ops(cur, plan)
        lf.ensure_columns(cur)
        lf.apply(cur, lf.plan_labels(cur, EPA, PLATES))
        self.assertEqual(lf.plan_labels(cur, EPA, PLATES), [])
        new = {r[0]: r[1:] for r in cur.execute("SELECT combined_mpg, epa_label, epa_plain FROM fuel_economy WHERE vehicle_id=1")}
        self.assertEqual(new, {25: ("X3 sDrive30i", 1), 23: ("X3 M40i", 0), 26: ("X3 xDrive30i · Hybrid", 0)})
        order = lf.ship_order(cur)
        self.assertEqual(order[6][0], 601)                              # the two-door Wrangler stays first


if __name__ == "__main__":
    unittest.main()
