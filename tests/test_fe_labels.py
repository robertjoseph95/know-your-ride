"""Fuel-economy version labels: tests for the naming rules, the label text, the build key, the
verifier checks and the label script (plan docs/superpowers/plans/2026-11-20-fuel-economy-version-labels.md).

Expectations are literals taken from the approved design and from running the full comparison's
own rules on the same fixtures; they never import the data under test. Tests that need the
canonical wrench_vehicles.db or EPA's complete file (env KYR_EPA_ZIP) skip when either is absent,
as in CI. No test writes to a real database file.

    python -m unittest discover -s tests -v
"""
import collections
import csv
import io
import os
import sqlite3
import sys
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FILES_DIR = os.path.join(ROOT, "files")
for p in (ROOT, FILES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

DB = os.path.join(ROOT, "wrench_vehicles.db")
COMPARE = os.path.join(ROOT, "_compare_fuel_economy_epa.py")
EPA_ZIP = os.environ.get("KYR_EPA_ZIP", "")


def _classes(mk, md, names, plates):
    import epa_name_rules
    return epa_name_rules.name_classes(2016, mk, md, [{"name": n, "atv": a} for n, a in names], plates)[0]


class TestNameRules(unittest.TestCase):
    def test_silverado_spellings(self):
        c = _classes("Chevrolet", "Silverado 1500", [("Silverado C15 2WD", ""), ("Silverado K15 4WD", ""),
                     ("Silverado C15 Cab Chassis 2WD", ""), ("Silverado 15 Hybrid 2WD", "Hybrid"), ("Tahoe C1500 2WD", "")],
                     {"Chevrolet": {"Silverado 1500", "Tahoe"}})
        self.assertEqual(c, {"Silverado C15 2WD": "own", "Silverado K15 4WD": "own", "Silverado C15 Cab Chassis 2WD": "own",
                             "Silverado 15 Hybrid 2WD": "hybrid or alternative fuel", "Tahoe C1500 2WD": "unrelated"})

    def test_yukon_xl_depends_on_fleet(self):
        names = [("Yukon 2WD", ""), ("Yukon XL 2WD", "")]
        self.assertEqual(_classes("GMC", "Yukon", names, {"GMC": {"Yukon"}})["Yukon XL 2WD"], "longer or different body")
        self.assertEqual(_classes("GMC", "Yukon", names, {"GMC": {"Yukon", "Yukon XL"}})["Yukon XL 2WD"], "another vehicle")

    def test_kona_n_ruled_out(self):
        self.assertEqual(_classes("Hyundai", "Kona", [("Kona FWD", ""), ("Kona N", "")], {"Hyundai": {"Kona"}})["Kona N"],
                         "performance model (N, already ruled out)")

    def test_f150_xl_is_a_trim(self):
        names = [("F150 Pickup 4WD", ""), ("F150 Pickup 4WD XL/XLT", "")]
        self.assertEqual(_classes("Ford", "F-150", names, {"Ford": {"F-150"}})["F150 Pickup 4WD XL/XLT"], "own")

    def test_xl_is_still_a_longer_body_elsewhere(self):
        names = [("Envoy 2WD", ""), ("Envoy XL 2WD", "")]
        self.assertEqual(_classes("GMC", "Envoy", names, {"GMC": {"Envoy"}})["Envoy XL 2WD"], "longer or different body")

    @unittest.skipUnless(os.path.exists(DB) and EPA_ZIP and os.path.exists(EPA_ZIP) and os.path.exists(COMPARE),
                         "needs wrench_vehicles.db, KYR_EPA_ZIP and _compare_fuel_economy_epa.py (local only)")
    def test_rules_equal_comparison_script(self):
        import epa_name_rules
        src = io.open(COMPARE, encoding="utf-8").read()
        a = src.index("# ---------------------------------------------------------------- name rules")
        b = src.index("# ---------------------------------------------------------------- EPA's file")
        c = src.index("def name_classes(")
        d = src.index("key_rec = lambda")
        g = {"__name__": "compare_rules"}
        exec(compile("import re, collections\n" + src[a:b] + src[c:d], COMPARE, "exec"), g)
        z = zipfile.ZipFile(EPA_ZIP)
        recs = collections.defaultdict(list)
        for r in csv.DictReader(io.StringIO(z.read("vehicles.csv").decode("utf-8", "replace"))):
            recs[(int(r["year"]), r["make"].strip().lower())].append({"name": r["model"].strip(), "atv": r["atvType"].strip()})
        con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        try:
            vehicles = con.execute("SELECT id, year, make, model FROM vehicles ORDER BY id").fetchall()
            plates = epa_name_rules.fleet_plates(con.cursor())
        finally:
            con.close()
        g["plates"] = collections.defaultdict(set, plates)
        checked, deliberate = 0, 0
        for vid, yr, mk, md in vehicles:
            rr = recs.get((yr, mk.lower()))
            if not rr:
                continue
            want = g["name_classes"](vid, yr, mk, md, rr)
            got = epa_name_rules.name_classes(yr, mk, md, rr, plates)
            if got != want:
                # The one deliberate difference (ruling (c), 2026-11-20): on the F-150, XL / XLT is a trim, not a longer body.
                diff = {n: (want[0].get(n), got[0].get(n)) for n in set(want[0]) | set(got[0]) if want[0].get(n) != got[0].get(n)}
                self.assertEqual(((mk, md), set(diff), set(diff.values()), got[1]),
                                 (("Ford", "F-150"), {"F150 Pickup 4WD XL/XLT"}, {("longer or different body", "own")}, want[1]),
                                 "%d %s %s %s" % (vid, yr, mk, md))
                deliberate += 1
            checked += 1
        self.assertGreater(checked, 3000)
        self.assertEqual(deliberate, 3)


def R(i, n, atv="", t="", s=""):
    return {"id": i, "name": n, "atv": atv, "tcharger": t, "scharger": s}


class TestLabelText(unittest.TestCase):
    def setUp(self):
        import fe_labels
        self.fl = fe_labels

    def test_xc90_tags(self):
        self.assertEqual(self.fl.label_text([R(1, "XC90 AWD", t="T")]), "XC90 AWD · Turbo")
        self.assertEqual(self.fl.label_text([R(2, "XC90 AWD", t="T", s="S")]), "XC90 AWD · Turbo, Supercharged")
        self.assertEqual(self.fl.label_text([R(3, "XC90 AWD PHEV", "Plug-in Hybrid", "T", "S")]),
                         "XC90 AWD PHEV · Plug-in hybrid, Turbo, Supercharged")

    def test_names_sorted_and_merged(self):
        self.assertEqual(self.fl.label_text([R(5, "Mustang Mach 1"), R(4, "Mustang Convertible")]),
                         "Mustang Convertible, Mustang Mach 1")
        self.assertEqual(self.fl.ids_text([R(5, "a"), R(4, "b"), R(5, "a")]), "4,5")

    def test_tag_needs_every_record(self):
        self.assertEqual(self.fl.label_text([R(6, "Silverado C15 2WD", "FFV"), R(7, "Silverado C15 2WD")]), "Silverado C15 2WD")

    def test_tag_hidden_only_by_whole_words(self):
        self.assertEqual(self.fl.label_text([R(8, "Camry Hybrid LE", "Hybrid")]), "Camry Hybrid LE")
        self.assertEqual(self.fl.label_text([R(9, "911 Turbo S", t="T")]), "911 Turbo S")
        self.assertEqual(self.fl.label_text([R(10, "Pacifica Hybrid", "Plug-in Hybrid")]), "Pacifica Hybrid · Plug-in hybrid")
        self.assertEqual(self.fl.label_text([R(11, "Wrangler 4dr EcoDiesel 4WD", "Diesel")]), "Wrangler 4dr EcoDiesel 4WD · Diesel")

    def test_kept_records_drops_other_vehicles(self):
        recs = [R(12, "Silverado C15 2WD"), R(13, "Tahoe C1500 2WD")]
        kept = self.fl.kept_records(recs, {"Silverado C15 2WD": "own", "Tahoe C1500 2WD": "unrelated"})
        self.assertEqual([r["id"] for r in kept], [12])

    def test_kept_records_falls_back_to_all(self):
        recs = [R(14, "4Runner Hybrid 4WD", "Hybrid")]
        self.assertEqual(self.fl.kept_records(recs, {"4Runner Hybrid 4WD": "another vehicle"}), recs)


def P(i, n, atv="", displ=None):
    return {"id": i, "name": n, "atv": atv, "displ": displ, "tcharger": "", "scharger": ""}


class TestPlainFlag(unittest.TestCase):
    """Ruling (c), 2026-11-20: a row ships its plain lines first, so the search card shows the plain car."""

    def setUp(self):
        import fe_labels
        self.fl = fe_labels

    def test_own_gasoline_record_is_plain(self):
        self.assertEqual(self.fl.plain_flag("Toyota", "Camry", [P(1, "Camry")], {"Camry": "own"}), 1)

    def test_own_electric_record_is_plain(self):
        self.assertEqual(self.fl.plain_flag("Tesla", "Model 3", [P(1, "Model 3 Long Range AWD", "EV")],
                                            {"Model 3 Long Range AWD": "own"}), 1)

    def test_hybrid_typed_own_record_is_not_plain(self):
        self.assertEqual(self.fl.plain_flag("BMW", "330i", [P(1, "330i xDrive Sedan", "Hybrid")], {"330i xDrive Sedan": "own"}), 0)
        self.assertEqual(self.fl.plain_flag("Bentley", "Bentayga", [P(2, "Bentayga", "Plug-in Hybrid")], {"Bentayga": "own"}), 0)

    def test_version_class_is_not_plain(self):
        self.assertEqual(self.fl.plain_flag("Toyota", "Camry", [P(1, "Camry Hybrid LE", "Hybrid")],
                                            {"Camry Hybrid LE": "hybrid or alternative fuel"}), 0)
        self.assertEqual(self.fl.plain_flag("Cadillac", "Escalade", [P(2, "Escalade V AWD")], {"Escalade V AWD": "performance version"}), 0)

    def test_trim_names_ruled_on_are_not_plain(self):
        for mk, md, n in (("BMW", "X3", "X3 M40i"), ("Ford", "Mustang", "Mustang Bullitt"), ("Ford", "Mustang", "Mustang HO Coupe"),
                          ("Toyota", "RAV4", "RAV4 AWD TRD OFFROAD"), ("Toyota", "Tacoma", "Tacoma 4WD D-CAB MT TRD-ORP/PRO"),
                          ("Jeep", "Wrangler", "Wrangler 4dr 4WD"), ("Chevrolet", "Colorado", "Colorado Cab Chassis inc 2WD"),
                          ("RAM", "1500", "1500 HO 4WD"), ("Porsche", "911", "911 Turbo S")):
            self.assertEqual(self.fl.plain_flag(mk, md, [P(1, n)], {n: "own"}), 0, n)

    def test_mustang_performance_trims_are_not_plain(self):
        # Robert, 2026-11-22 ("Mustang card first"): Dark Horse and GTD led or sat among the plain lines of the
        # 2025 / 2026 rows; Mach 1 is the same kind of named trim as Bullitt (2021 / 2022).
        for n in ("Mustang Dark Horse", "Mustang GTD", "Mustang Mach 1"):
            self.assertEqual(self.fl.plain_flag("Ford", "Mustang", [P(1, n)], {n: "own"}), 0, n)

    def test_mustang_plain_names_stay_plain(self):
        for n in ("Mustang", "Mustang Convertible"):
            self.assertEqual(self.fl.plain_flag("Ford", "Mustang", [P(1, n)], {n: "own"}), 1, n)
        recs = [P(1, "Mustang Convertible"), P(2, "Mustang Mach 1")]          # one EPA line, two names
        self.assertEqual(self.fl.plain_flag("Ford", "Mustang", recs, {r["name"]: "own" for r in recs}), 1)

    def test_srt8_only_by_its_engine(self):
        self.assertEqual(self.fl.plain_flag("Chrysler", "300", [P(1, "300/SRT-8", displ=6.1)], {"300/SRT-8": "own"}), 0)
        self.assertEqual(self.fl.plain_flag("Chrysler", "300", [P(2, "300/SRT-8", displ=3.5)], {"300/SRT-8": "own"}), 1)

    def test_one_plain_record_makes_the_line_plain(self):
        recs = [P(1, "Silverado C15 2WD"), P(2, "Silverado C15 Cab Chassis 2WD")]
        self.assertEqual(self.fl.plain_flag("Chevrolet", "Silverado 1500", recs, {r["name"]: "own" for r in recs}), 1)

    def test_no_record_is_not_plain(self):
        self.assertEqual(self.fl.plain_flag("Toyota", "Camry", [], {}), 0)

    def test_ship_order_puts_plain_lines_first(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY, vehicle_id INTEGER, epa_plain INTEGER)")
        con.executemany("INSERT INTO fuel_economy VALUES (?,?,?)", [(1, 7, 0), (2, 7, 1), (3, 7, None), (4, 7, 1), (5, 6, 0)])
        got = [r[0] for r in con.execute("SELECT id FROM fuel_economy ORDER BY " + self.fl.SHIP_ORDER)]
        self.assertEqual(got, [5, 2, 4, 1, 3])


def _load_build():
    import importlib.util
    spec = importlib.util.spec_from_file_location("kyr_build_04_test", os.path.join(FILES_DIR, "04_rebuild_demo.py"))
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    return b


CARD_OLD = "<div class=\"mpg-dr\">'+(m.drive||'')+'</div></div>'"


class TestCardMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = _load_build()
        with open(os.path.join(ROOT, "wrench_demo.html"), "rb") as f:
            cls.html = f.read().decode("utf-8")

    def test_mpg_label_migration_idempotent(self):
        once = self.b.migrate_mpg_label(self.html)
        self.assertEqual(self.b.migrate_mpg_label(once), once)
        self.assertEqual(once.count('<div class="mpg-ver">'), 1)
        self.assertEqual(once.count(".mpg-ver{"), 1)
        self.assertNotIn(CARD_OLD, once)
        self.assertEqual(self.b.fix_js_quotes(once).count('<div class="mpg-ver">'), 1)
        self.assertEqual(self.b.fix_js_quotes(once).count(".mpg-ver{"), 1)

    def test_card_escapes_label(self):
        once = self.b.migrate_mpg_label(self.html)
        self.assertIn("'+htmlEsc(m.lbl)+'", once)
        self.assertNotIn("'+m.lbl+'", once)


@unittest.skipUnless(os.path.exists(DB), "needs wrench_vehicles.db (local only)")
class TestBuildLabel(unittest.TestCase):
    VID = 11447
    LABEL = "X · Turbo"

    @classmethod
    def _build(cls, columns, label_line=None, plain=None, name_all=False):
        src = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        mem = sqlite3.connect(":memory:")
        src.backup(mem)
        src.close()
        # Start every variant from the pre-label schema, whatever the canonical database holds today.
        for (trigger,) in mem.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'fe_label_%'").fetchall():
            mem.execute('DROP TRIGGER "%s"' % trigger)
        have = {r[1] for r in mem.execute("PRAGMA table_info(fuel_economy)")}
        for col in ("epa_plain", "epa_label", "epa_ids"):
            if col in have:
                mem.execute("ALTER TABLE fuel_economy DROP COLUMN %s" % col)
        if columns:
            mem.execute("ALTER TABLE fuel_economy ADD COLUMN epa_ids TEXT")
            mem.execute("ALTER TABLE fuel_economy ADD COLUMN epa_label TEXT")
        if label_line:
            mem.execute("UPDATE fuel_economy SET epa_ids='1', epa_label=? WHERE id=?", (cls.LABEL, label_line))
        if name_all:                                   # every line of the vehicle labelled with its own id, to read the order
            mem.execute("UPDATE fuel_economy SET epa_ids='1', epa_label='L' || id WHERE vehicle_id=?", (cls.VID,))
        if plain is not None:
            mem.execute("ALTER TABLE fuel_economy ADD COLUMN epa_plain INTEGER")
            mem.executemany("UPDATE fuel_economy SET epa_plain=? WHERE id=?", [(f, i) for i, f in plain.items()])
        mem.row_factory = sqlite3.Row
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            vlist = cls.b.build_data(mem.cursor())[0]
        mem.close()
        return {v["id"]: v for v in vlist}

    @classmethod
    def setUpClass(cls):
        cls.b = _load_build()
        con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
        cls.lines = [r[0] for r in con.execute("SELECT id FROM fuel_economy WHERE vehicle_id=? ORDER BY id", (cls.VID,))]
        con.close()
        cls.target = cls.lines[1]
        cls.plain = cls._build(False)
        cls.empty = cls._build(True)
        cls.labelled = cls._build(True, cls.target)

    def test_build_omits_lbl_when_label_null(self):
        for data in (self.plain, self.empty):
            self.assertFalse(any("lbl" in m for v in data.values() for m in (v.get("mpg") or [])))
        self.assertEqual(self.plain, self.empty)

    def test_build_ships_lbl(self):
        changed = [i for i in self.labelled if self.labelled[i] != self.empty[i]]
        self.assertEqual(changed, [self.VID])
        mpg = self.labelled[self.VID]["mpg"]
        self.assertEqual(len(mpg), len(self.lines))
        self.assertEqual([m.get("lbl") for m in mpg], [self.LABEL if i == self.target else None for i in self.lines])

    def test_build_ships_plain_lines_first(self):
        last = self.lines[-1]
        data = self._build(True, plain={i: int(i == last) for i in self.lines}, name_all=True)
        self.assertEqual([m["lbl"] for m in data[self.VID]["mpg"]], ["L%d" % i for i in [last] + self.lines[:-1]])

    def test_build_keeps_stored_order_without_the_flag(self):
        data = self._build(True, name_all=True)
        self.assertEqual([m["lbl"] for m in data[self.VID]["mpg"]], ["L%d" % i for i in self.lines])


def _verifier():
    import _verify_shipped
    return _verify_shipped


def _fe_db(path, columns, rows):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY, vehicle_id INTEGER, city_mpg INTEGER%s)"
                % (", epa_ids TEXT, epa_label TEXT" if columns else ""))
    for r in rows:
        con.execute("INSERT INTO fuel_economy VALUES (%s)" % ",".join("?" * len(r)), r)
    con.commit()
    con.close()


def _fe_full_db(path, rows):
    """Rows: (id, vehicle_id, city, hwy, comb, cost, epa_ids, epa_label, epa_plain)."""
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY, vehicle_id INTEGER, city_mpg INTEGER, highway_mpg INTEGER, "
                "combined_mpg INTEGER, annual_fuel_cost INTEGER, epa_ids TEXT, epa_label TEXT, epa_plain INTEGER)")
    con.executemany("INSERT INTO fuel_economy VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


class TestVerifierChecks(unittest.TestCase):
    def setUp(self):
        import tempfile
        import types
        self.vs = _verifier()
        self.ns = types.SimpleNamespace
        self.tmp = tempfile.mkdtemp(prefix="kyr_fe_labels_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _a(self, *mpg):
        return self.ns(D={"v": [{"id": 1, "mpg": list(mpg)}]})

    def test_entry_shape_ok(self):
        self.assertEqual(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "hwy": 2, "comb": 3, "lbl": "A · Turbo"})), [])

    def test_entry_shape_rejects(self):
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "epa_ids": "5"}))), 1)
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "lbl": ""}))), 1)
        self.assertEqual(len(self.vs.s1_13_mpg_entry_shape(self._a({"city": 1, "lbl": "x" * 401}))), 1)

    def test_label_provenance(self):
        bad, good, none = (os.path.join(self.tmp, n) for n in ("bad.db", "good.db", "none.db"))
        _fe_db(bad, True, [(1, 1, 20, "", "A")])
        _fe_db(good, True, [(1, 1, 20, "5", "A")])
        _fe_db(none, False, [(1, 1, 20)])
        self.assertEqual(len(self.vs.s1_14_label_provenance(self.ns(db_path=bad))), 1)
        self.assertEqual(self.vs.s1_14_label_provenance(self.ns(db_path=good)), [])
        self.assertEqual(self.vs.s1_14_label_provenance(self.ns(db_path=none)), [])

    def test_unassessed_lines_warn_only(self):
        path = os.path.join(self.tmp, "warn.db")
        _fe_db(path, True, [(1, 1, 20, None, None), (2, 1, 21, None, None), (3, 1, 22, "", None)])
        out = self.vs.s1_15_unassessed_lines(self.ns(db_path=path))
        self.assertEqual(len(out), 1)
        self.assertIn("2", out[0])
        tiers = {cid: tier for cid, tier, _venue, _fn in self.vs.CHECKS}
        self.assertEqual(tiers["S1.15-unassessed-lines"], "WARN")
        self.assertEqual(tiers["S1.13-mpg-entry-shape"], "FAIL")
        self.assertEqual(tiers["S1.14-label-provenance"], "FAIL")

    def test_shipped_order_matches_the_database(self):
        path = os.path.join(self.tmp, "order.db")
        _fe_full_db(path, [(1, 1, 20, 27, 23, 2000, "5", "A", 0), (2, 1, 18, 25, 21, 2100, "6", "B", 1)])
        ent = lambda c, h, m, cost, lbl: {"city": c, "hwy": h, "comb": m, "cost": cost, "lbl": lbl}
        good = self.ns(db_path=path, D={"v": [{"id": 1, "mpg": [ent(18, 25, 21, 2100, "B"), ent(20, 27, 23, 2000, "A")]}]})
        stale = self.ns(db_path=path, D={"v": [{"id": 1, "mpg": [ent(20, 27, 23, 2000, "A"), ent(18, 25, 21, 2100, "B")]}]})
        self.assertEqual(self.vs.s1_16_ship_order(good), [])
        self.assertEqual(len(self.vs.s1_16_ship_order(stale)), 1)
        self.assertEqual(self.vs.s1_16_ship_order(self.ns(db_path=path)), [])          # no blob: nothing to compare
        self.assertEqual(self.vs.s1_14_label_provenance(good), [])
        self.assertEqual(len(self.vs.s1_14_label_provenance(stale)), 1)
        tiers = {cid: tier for cid, tier, _venue, _fn in self.vs.CHECKS}
        self.assertEqual(tiers["S1.16-ship-order"], "FAIL")

    def test_unassessed_counts_a_missing_plain_flag(self):
        path = os.path.join(self.tmp, "plainwarn.db")
        _fe_full_db(path, [(1, 1, 20, 27, 23, 2000, "5", "A", None), (2, 1, 18, 25, 21, 2100, "6", "B", 1)])
        out = self.vs.s1_15_unassessed_lines(self.ns(db_path=path))
        self.assertEqual(len(out), 1)
        self.assertIn("1 fuel-economy line", out[0])


def E(i, name, city, hwy, comb, displ, trans, drive, atv="", rng=None, t="", s=""):
    """An EPA record as _label_fuel_economy.load_epa returns it (report-only fields left empty)."""
    return {"id": i, "year": 0, "make": "", "name": name, "atv": atv, "city": city, "hwy": hwy, "comb": comb,
            "displ": displ, "trans": trans, "drive": drive, "range": rng, "tcharger": t, "scharger": s,
            "eng_dscr": "", "vclass": "", "startstop": "", "trans_dscr": "", "engid": ""}


def L(city, hwy, comb, engine, trans, drive, fuel_type=None, mpge=None, rng=None):
    return {"city_mpg": city, "highway_mpg": hwy, "combined_mpg": comb, "engine": engine, "transmission": trans,
            "drive": drive, "fuel_type": fuel_type, "mpge": mpge, "range_miles": rng}


AWD8 = ("Automatic (S8)", "All-Wheel Drive")
EV_ROW = (None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 113, 353)


class TestLabelScript(unittest.TestCase):
    EPA = {(2020, "volvo"): [E(101, "XC90 AWD", 20, 27, 23, 2.0, *AWD8, t="T"),
                             E(102, "XC90 AWD", 18, 26, 21, 2.0, *AWD8, t="T", s="S")],
           (2021, "tesla"): [E(201, "Model 3 Long Range AWD", None, None, 113, None, "Automatic (A1)", "All-Wheel Drive",
                               atv="EV", rng=353)]}
    PLATES = {"Volvo": {"XC90"}, "Tesla": {"Model 3"}}

    def setUp(self):
        import _label_fuel_economy
        self.lf = _label_fuel_economy

    def _fleet(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE vehicles (id INTEGER PRIMARY KEY, year INTEGER, make TEXT, model TEXT)")
        con.execute("CREATE TABLE fuel_economy (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER, city_mpg INTEGER, "
                    "highway_mpg INTEGER, combined_mpg INTEGER, annual_fuel_cost INTEGER, engine TEXT, transmission TEXT, "
                    "drive TEXT, range_miles INTEGER, mpge INTEGER, fuel_type TEXT)")
        con.executemany("INSERT INTO vehicles VALUES (?,?,?,?)", [(1, 2020, "Volvo", "XC90"), (2, 2021, "Tesla", "Model 3")])
        rows = [(1, 20, 27, 23, 2.0, *AWD8, None, None, None), (1, 18, 26, 21, 2.0, *AWD8, None, None, None),
                (1, 30, 30, 30, 2.0, *AWD8, None, None, None),
                (2, None, None, None, None, "Automatic (A1)", "All-Wheel Drive", 353, 113, "Electric")]
        con.executemany("INSERT INTO fuel_economy (vehicle_id, city_mpg, highway_mpg, combined_mpg, engine, transmission, "
                        "drive, range_miles, mpge, fuel_type) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [(r[0], r[1], r[2], r[3], str(r[4]) if r[4] is not None else None, r[5], r[6], r[7], r[8], r[9])
                         for r in rows])
        con.commit()          # an open write transaction would block Connection.backup() forever
        return con

    def test_gas_line_matches_six_fields(self):
        recs = [E(1, "A", 20, 27, 23, 2.0, *AWD8), E(2, "B", 20, 27, 24, 2.0, *AWD8)]
        self.assertEqual([r["id"] for r in self.lf.match_line(L(20, 27, 23, "2.0", *AWD8), recs)], [1])

    def test_electric_line_matches_mpge_and_range(self):
        recs = [E(3, "EV", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", atv="EV", rng=256),
                E(4, "Gas", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", rng=256)]
        line = L(None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 110, 256)
        self.assertEqual([r["id"] for r in self.lf.match_line(line, recs)], [3])

    def test_electric_without_range_matches_nothing(self):
        recs = [E(3, "EV", None, None, 110, None, "Automatic (A1)", "All-Wheel Drive", atv="EV", rng=256)]
        line = L(None, None, None, None, "Automatic (A1)", "All-Wheel Drive", "Electric", 110, None)
        self.assertEqual(self.lf.match_line(line, recs), [])

    def test_plan_labels_values(self):
        con = self._fleet()
        plan = self.lf.plan_labels(con.cursor(), self.EPA, self.PLATES)
        self.assertEqual([(p["fe_id"], p["old"], p["new"]) for p in plan],
                         [(1, [None, None, None], ["101", "XC90 AWD · Turbo", 1]),
                          (2, [None, None, None], ["102", "XC90 AWD · Turbo, Supercharged", 1]),
                          (3, [None, None, None], ["", None, 0]),
                          (4, [None, None, None], ["201", "Model 3 Long Range AWD", 1])])

    def test_unmatched_line_marked_assessed(self):
        con = self._fleet()
        plan = {p["fe_id"]: p for p in self.lf.plan_labels(con.cursor(), self.EPA, self.PLATES)}
        self.assertEqual(plan[3]["new"], ["", None, 0])

    def test_plan_is_empty_after_apply(self):
        con = self._fleet()
        cur = con.cursor()
        self.assertEqual(self.lf.ensure_columns(cur), ["epa_ids", "epa_label", "epa_plain"])
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        self.assertEqual(self.lf.plan_labels(cur, self.EPA, self.PLATES), [])
        self.assertEqual(self.lf.ensure_columns(cur), [])
        self.assertEqual(cur.execute("SELECT COUNT(*) FROM fuel_economy WHERE epa_ids IS NULL OR epa_plain IS NULL").fetchone()[0], 0)

    def test_ensure_columns_upgrades_the_first_triggers(self):
        con = self._fleet()
        cur = con.cursor()
        for name in ("epa_ids", "epa_label"):                                   # the database as the first label write left it
            cur.execute("ALTER TABLE fuel_economy ADD COLUMN %s TEXT" % name)
        for sql in self.lf._TRIGGERS:
            cur.execute(sql.replace(", epa_plain = NULL", ""))
        self.assertEqual(self.lf.ensure_columns(cur), ["epa_plain"])
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        cur.execute("UPDATE fuel_economy SET combined_mpg=24 WHERE id=1")
        self.assertEqual(cur.execute("SELECT epa_ids, epa_label, epa_plain FROM fuel_economy WHERE id=1").fetchone(), (None, None, None))
        self.assertEqual(cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0], 2)

    def test_ship_order_follows_the_plain_flag(self):
        con = self._fleet()
        cur = con.cursor()
        self.assertEqual(self.lf.ship_order(cur), {1: [1, 2, 3], 2: [4]})              # no flag yet: stored order
        self.lf.ensure_columns(cur)
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        cur.execute("UPDATE fuel_economy SET epa_plain=0 WHERE id=1")
        self.assertEqual(self.lf.ship_order(cur), {1: [2, 1, 3], 2: [4]})

    def test_shipped_lines_compare_by_line_not_position(self):
        ok = self.lf.shipped_lines_ok
        a, b = {"comb": 23, "cost": 2000}, {"comb": 21, "cost": 2100}
        self.assertTrue(ok([a, b], [dict(b, lbl="B"), dict(a, lbl="A")], [1, 2], [2, 1], {1: "A", 2: "B"}))   # reordered, labelled
        self.assertFalse(ok([a, b], [dict(b, lbl="B"), dict(a, comb=24, lbl="A")], [1, 2], [2, 1], {1: "A", 2: "B"}))
        self.assertFalse(ok([a, b], [dict(a, lbl="A")], [1, 2], [1], {1: "A"}))                               # a line lost

    def test_rehearsal_accepts_a_rerun(self):
        ok = self.lf.label_change_ok
        base = {"city": 20, "hwy": 27, "comb": 23, "cost": 2000}
        self.assertTrue(ok(dict(base), dict(base, lbl="A"), 7, {7: "A"}))                 # first run: label added
        self.assertTrue(ok(dict(base, lbl="A"), dict(base, lbl="A"), 7, {}))              # re-run: line not planned, label kept
        self.assertTrue(ok(dict(base, lbl="A"), dict(base, lbl="B"), 7, {7: "B"}))        # re-run: label changed as planned
        self.assertTrue(ok(dict(base, lbl="A"), dict(base), 7, {7: None}))                # re-run: label planned away
        self.assertFalse(ok(dict(base), dict(base, lbl="B"), 7, {7: "A"}))                # wrong label
        self.assertFalse(ok(dict(base), dict(base, cost=2100, lbl="A"), 7, {7: "A"}))     # a figure moved
        self.assertFalse(ok(dict(base, lbl="A"), dict(base), 7, {}))                      # label lost without a plan

    def test_lookalike_verdicts(self):
        def item(vid, fid, comb, label, dscr="SIDI", kept=True):
            rec = dict(E(fid, "X", 20, 27, comb, 2.0, *AWD8), eng_dscr=dscr)
            return {"fe_id": fid, "vehicle_id": vid, "line": L(20, 27, comb, "2.0", *AWD8),
                    "kept": [rec] if kept else [], "hit": [rec] if kept else [], "new": ["1", label] if kept else ["", None]}
        assessed = [item(1, 1, 23, "A"), item(1, 2, 24, "B"),                         # told apart
                    item(2, 3, 23, "A"), item(2, 4, 24, "A", "SIDI; Stop-Start"),     # only engine notes differ
                    item(3, 5, 23, "A"), item(3, 6, 24, None, kept=False),            # a line has no EPA record
                    item(4, 7, 23, "A"), item(4, 8, 23, "A")]                         # same figures: not a group
        verdicts = {key[0]: self.lf.group_verdict(figs) for key, figs in self.lf.lookalike_groups(assessed)}
        self.assertEqual(verdicts, {1: "told apart", 2: "only EPA engine notes differ", 3: "a line matches no EPA record"})

    # ---------------------------------------------------------------- final-review fixes (2026-11-20)
    def _item(self, vid, fid, comb, kept, hit=None):
        return {"fe_id": fid, "vehicle_id": vid, "line": L(20, 27, comb, "2.0", *AWD8), "kept": kept,
                "hit": hit if hit is not None else kept, "new": ["1", self.lf.fe_labels.label_text(kept)] if kept else ["", None]}

    def test_verdict_names_the_review_causes(self):
        own = lambda i, n, **k: dict(E(i, n, 20, 27, 23, 2.0, *AWD8), **k)
        a = [self._item(1, 1, 23, [own(1, "Tahoe 2WD")], [own(1, "Tahoe 2WD")]),                       # another vehicle's name
             self._item(1, 2, 24, [own(2, "Tahoe 2WD")], [own(2, "Tahoe 2WD"), own(9, "Silverado TrailBoss")]),
             self._item(2, 3, 23, [own(3, "Sierra 2WD"), own(4, "Sierra 2WD", atv="FFV")]),             # fuel held by some
             self._item(2, 4, 24, [own(5, "Sierra 2WD")]),
             self._item(3, 5, 23, [own(6, "9-5 Sedan")]), self._item(3, 6, 24, [own(7, "9-5 Wagon")]),   # partly told apart
             self._item(3, 7, 25, [own(8, "9-5 Wagon")])]
        verdicts = {key[0]: self.lf.group_verdict(figs) for key, figs in self.lf.lookalike_groups(a)}
        self.assertEqual(verdicts, {1: "only another vehicle's name differs (dropped by the keep rule)",
                                    2: "a fuel type or charger only some records carry (hidden by the every-record rule)",
                                    3: "partly told apart"})

    def test_label_words_come_from_epa(self):
        ok = self.lf.label_words_ok
        rec = E(1, "XC90 AWD", 20, 27, 23, 2.0, *AWD8, t="T")
        self.assertTrue(ok("XC90 AWD · Turbo", "1", [rec]))
        self.assertTrue(ok(None, "", []))
        self.assertFalse(ok("XC90 AWD · Hybrid", "1", [rec]))                # tag no record carries
        self.assertFalse(ok("XC90 AWD Sport · Turbo", "1", [rec]))           # a name no record has
        self.assertFalse(ok("XC90 AWD · Turbo", "2", [rec]))                 # ids that are not the records'
        self.assertFalse(ok("XC90 AWD · Fast", "1", [rec]))                  # a word that is no tag

    def test_apply_refuses_a_changed_line_or_vehicle(self):
        for change in ("UPDATE fuel_economy SET combined_mpg=24 WHERE id=1", "UPDATE vehicles SET model='XC60' WHERE id=1"):
            con = self._fleet()
            cur = con.cursor()
            plan = self.lf.plan_labels(cur, self.EPA, self.PLATES)
            self.lf.ensure_columns(cur)
            cur.execute(change)
            with self.assertRaises(RuntimeError, msg=change):
                self.lf.apply(cur, plan)

    def test_trigger_clears_label_when_matched_fields_change(self):
        con = self._fleet()
        cur = con.cursor()
        self.lf.ensure_columns(cur)
        self.lf.apply(cur, self.lf.plan_labels(cur, self.EPA, self.PLATES))
        lab = lambda i: cur.execute("SELECT epa_ids, epa_label, epa_plain FROM fuel_economy WHERE id=?", (i,)).fetchone()
        cur.execute("UPDATE fuel_economy SET annual_fuel_cost=2500 WHERE id=1")            # cost is not matched on
        self.assertEqual(lab(1), ("101", "XC90 AWD · Turbo", 1))
        cur.execute("UPDATE fuel_economy SET combined_mpg=24 WHERE id=1")
        self.assertEqual(lab(1), (None, None, None))
        self.assertEqual(lab(2), ("102", "XC90 AWD · Turbo, Supercharged", 1))
        cur.execute("UPDATE fuel_economy SET mpge=NULL WHERE id=4")                       # electric figure cleared
        self.assertEqual(lab(4), (None, None, None))
        cur.execute("UPDATE vehicles SET model='XC60' WHERE id=1")
        self.assertEqual(lab(2), (None, None, None))

    def test_write_is_one_transaction(self):
        import tempfile
        import shutil
        tmp = tempfile.mkdtemp(prefix="kyr_fe_write_")
        try:
            db = os.path.join(tmp, "fleet.db")
            disk = sqlite3.connect(db)
            self._fleet().backup(disk)
            disk.execute("CREATE TABLE oil_change (source TEXT)")
            for t in ("parts", "fluids", "torque_specs"):
                disk.execute("CREATE TABLE %s (source TEXT)" % t)
            disk.executemany("INSERT INTO oil_change VALUES (?)", [("owner-manual-verified",)] * self.lf.BARE_FROZEN)
            disk.commit()
            plan = self.lf.plan_labels(disk.cursor(), self.EPA, self.PLATES)
            disk.execute("UPDATE fuel_economy SET combined_mpg=24 WHERE id=3")               # stale after the dry run
            disk.commit()
            disk.close()
            saved = (self.lf.DB, self.lf.PLAN_FILE)
            self.lf.DB, self.lf.PLAN_FILE = db, os.path.join(tmp, "plan_cache.json")
            try:
                sha = self.lf.save_plan(plan, self.lf.plates_sha(self.PLATES))
                with self.assertRaises(RuntimeError):
                    self.lf.write(sha)
            finally:
                self.lf.DB, self.lf.PLAN_FILE = saved
            con = sqlite3.connect(db)
            cols = {r[1] for r in con.execute("PRAGMA table_info(fuel_economy)")}
            triggers = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
            con.close()
            self.assertNotIn("epa_ids", cols)
            self.assertEqual(triggers, 0)
            self.assertEqual(len([n for n in os.listdir(tmp) if ".bak_fe_labels_" in n]), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestLabelEquivalence(unittest.TestCase):
    def test_shipped_labels_equal_the_database(self):
        import tempfile
        import shutil
        import types
        vs = _verifier()
        tmp = tempfile.mkdtemp(prefix="kyr_fe_equiv_")
        try:
            path = os.path.join(tmp, "eq.db")
            _fe_db(path, True, [(1, 7, 20, "5", "A"), (2, 7, 21, "", None), (3, 8, 22, "6", "B")])
            a = lambda m7, m8: types.SimpleNamespace(db_path=path, D={"v": [{"id": 7, "mpg": m7}, {"id": 8, "mpg": m8}]})
            self.assertEqual(vs.s1_14_label_provenance(a([{"lbl": "A"}, {}], [{"lbl": "B"}])), [])
            self.assertEqual(len(vs.s1_14_label_provenance(a([{"lbl": "A"}, {}], [{}]))), 1)           # label not shipped
            self.assertEqual(len(vs.s1_14_label_provenance(a([{"lbl": "X"}, {}], [{"lbl": "B"}]))), 1)  # wrong label
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
