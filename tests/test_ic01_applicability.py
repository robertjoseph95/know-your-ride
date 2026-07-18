import importlib.util
import copy
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "files" / "ic01_quarantine.py"
WRITER_PATH = ROOT / "_write_crv_5thgen_pilot.py"
BUILD_PATH = ROOT / "files" / "04_rebuild_demo.py"
VERIFIER_PATH = ROOT / "_verify_shipped.py"


def verified_shell_records():
    identities = {
        12372: (2017, "Honda", "CR-V", "1.5L Turbo"),
        12511: (2018, "Honda", "CR-V", "1.5L Turbo"),
        12777: (2020, "Honda", "CR-V", "1.5L Turbo"),
        12847: (2021, "Honda", "CR-V", "1.5L Turbo"),
        12912: (2022, "Honda", "CR-V", "1.5L Turbo"),
    }
    records = []
    for vehicle_id, (year, make, model, engine) in identities.items():
        records.append({
            "id": vehicle_id,
            "year": year,
            "make": make,
            "model": model,
            "engine": engine,
            "oil": {"ver": 0},
            "parts": {"ver": 0},
            "fluids": {"ver": 0},
            "recalls": [{"camp": "government-data-survives"}],
            "mpg": [{"comb": 30}],
            "safety": {"overall": 5},
            "comps_agg": {"n": 1, "topics": [["ENGINE", 1]], "through": "2026-05"},
        })
    return records


class Ic01ContractTests(unittest.TestCase):
    def load_contract(self):
        self.assertTrue(
            CONTRACT_PATH.exists(),
            "IC-01 contract module must exist before quarantined data can ship",
        )
        spec = importlib.util.spec_from_file_location("ic01_quarantine", CONTRACT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_contract_uses_exact_ids_token_sample_and_row_counts(self):
        contract = self.load_contract()
        self.assertEqual(
            contract.QUARANTINED_VEHICLE_IDS,
            frozenset({12372, 12511, 12777, 12847, 12912}),
        )
        self.assertEqual(contract.QUARANTINE_SOURCE, "quarantine-applicability-ic01")
        self.assertEqual(contract.HOMEPAGE_SAMPLE_ID, 467)
        self.assertEqual(
            contract.EXPECTED_HOMEPAGE_SAMPLE,
            {
                "id": 467,
                "identity": (2020, "Nissan", "Sentra", None, "2.0L I4"),
                "oil_visc": "0W-20",
                "oil_cap_w": "4.4 qt",
                "recall_count": 4,
            },
        )
        self.assertEqual(
            contract.EXPECTED_DB_ROWS,
            {
                "oil_change": 5,
                "parts": 5,
                "fluids": 5,
                "torque_specs": 5,
                "maintenance": 15,
            },
        )

    def test_projection_accepts_only_bare_shells_and_preserves_government_data(self):
        contract = self.load_contract()
        self.assertEqual(contract.projection_problems(verified_shell_records()), [])

    def test_projection_rejects_a_value_beside_ver_zero(self):
        contract = self.load_contract()
        records = verified_shell_records()
        records[0]["oil"]["visc"] = "0W-20"
        self.assertTrue(contract.projection_problems(records))

    def test_projection_rejects_restored_torque_or_maintenance(self):
        contract = self.load_contract()
        records = verified_shell_records()
        records[0]["torque"] = [{"ver": 1, "comp": "lug_nut"}]
        records[1]["maint"] = [{"ver": 1, "desc": "oil change"}]
        records[2]["maint_parts"] = [{"name": "filter"}]
        problems = contract.projection_problems(records)
        self.assertGreaterEqual(len(problems), 3)

    def test_projection_rejects_a_missing_quarantined_vehicle(self):
        contract = self.load_contract()
        records = verified_shell_records()[:-1]
        self.assertTrue(contract.projection_problems(records))

    def test_projection_rejects_identity_drift_or_lost_government_data(self):
        contract = self.load_contract()
        records = verified_shell_records()
        records[0]["year"] = 2020
        records[1].pop("mpg")
        records[2]["recalls"] = []
        records[3].pop("safety")
        records[4].pop("comps_agg")
        records[4]["trim"] = "EX"
        problems = contract.projection_problems(records)
        self.assertGreaterEqual(len(problems), 6)


class Ic01WriterTests(unittest.TestCase):
    def load_writer(self):
        spec = importlib.util.spec_from_file_location("ic01_crv_writer", WRITER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def make_db(self):
        con = sqlite3.connect(":memory:")
        for table in ("oil_change", "parts", "fluids"):
            con.execute("CREATE TABLE %s (vehicle_id INTEGER, source TEXT)" % table)
        con.execute("CREATE TABLE torque_specs (id INTEGER PRIMARY KEY, vehicle_id INTEGER, source TEXT)")
        con.execute("CREATE TABLE maintenance (id INTEGER PRIMARY KEY, vehicle_id INTEGER, source TEXT)")
        con.execute("CREATE TABLE maintenance_parts (id INTEGER PRIMARY KEY, maintenance_id INTEGER, vehicle_id INTEGER)")
        row_id = 1000
        for vehicle_id in (12372, 12511, 12777, 12847, 12912):
            for table in ("oil_change", "parts", "fluids"):
                con.execute(
                    "INSERT INTO %s(vehicle_id, source) VALUES (?, ?)" % table,
                    (vehicle_id, "owner-manual-verified"),
                )
            con.execute(
                "INSERT INTO torque_specs(id, vehicle_id, source) VALUES (?, ?, ?)",
                (row_id, vehicle_id, "owner-manual-verified"),
            )
            row_id += 1
            for _ in range(3):
                con.execute(
                    "INSERT INTO maintenance(id, vehicle_id, source) VALUES (?, ?, ?)",
                    (row_id, vehicle_id, "Honda Owner's Manual (2018 CR-V, 5th gen)"),
                )
                row_id += 1
        con.execute(
            "INSERT INTO maintenance_parts(id, maintenance_id, vehicle_id) VALUES (1, 1001, 12372)"
        )
        for table in ("oil_change", "parts", "fluids"):
            con.execute(
                "INSERT INTO %s(vehicle_id, source) VALUES (999999, 'owner-manual-verified')"
                % table
            )
        con.execute(
            "INSERT INTO torque_specs(id, vehicle_id, source) VALUES (?, 999999, 'owner-manual-verified')",
            (row_id,),
        )
        row_id += 1
        con.execute(
            "INSERT INTO maintenance(id, vehicle_id, source) VALUES (?, 999999, 'owner-manual-verified')",
            (row_id,),
        )
        con.commit()
        return con

    def test_writer_only_relabels_expected_rows_and_preserves_unrelated_rows(self):
        writer = self.load_writer()
        self.assertTrue(
            hasattr(writer, "apply_quarantine"),
            "legacy CR-V writer must expose a replay-safe apply_quarantine operation",
        )
        con = self.make_db()
        counts = writer.apply_quarantine(con)
        self.assertEqual(
            counts,
            {
                "oil_change": 5,
                "parts": 5,
                "fluids": 5,
                "torque_specs": 5,
                "maintenance": 15,
            },
        )
        for table, expected in counts.items():
            got = con.execute(
                "SELECT COUNT(*) FROM %s WHERE source=?" % table,
                ("quarantine-applicability-ic01",),
            ).fetchone()[0]
            self.assertEqual(got, expected)
            unrelated = con.execute(
                "SELECT source FROM %s WHERE vehicle_id=999999" % table
            ).fetchone()[0]
            self.assertEqual(unrelated, "owner-manual-verified")
        con.close()

    def test_writer_is_idempotent_and_preserves_ids_and_part_links(self):
        writer = self.load_writer()
        con = self.make_db()
        before_torque = con.execute(
            "SELECT id, vehicle_id FROM torque_specs ORDER BY id"
        ).fetchall()
        before_maint = con.execute(
            "SELECT id, vehicle_id FROM maintenance ORDER BY id"
        ).fetchall()
        before_links = con.execute(
            "SELECT id, maintenance_id, vehicle_id FROM maintenance_parts ORDER BY id"
        ).fetchall()

        first = writer.apply_quarantine(con)
        after_first = {
            table: con.execute(
                "SELECT * FROM %s ORDER BY rowid" % table
            ).fetchall()
            for table in ("oil_change", "parts", "fluids", "torque_specs", "maintenance", "maintenance_parts")
        }
        second = writer.apply_quarantine(con)
        after_second = {
            table: con.execute(
                "SELECT * FROM %s ORDER BY rowid" % table
            ).fetchall()
            for table in after_first
        }

        self.assertEqual(first, second)
        self.assertEqual(after_first, after_second)
        self.assertEqual(before_torque, con.execute("SELECT id, vehicle_id FROM torque_specs ORDER BY id").fetchall())
        self.assertEqual(before_maint, con.execute("SELECT id, vehicle_id FROM maintenance ORDER BY id").fetchall())
        self.assertEqual(before_links, con.execute("SELECT id, maintenance_id, vehicle_id FROM maintenance_parts ORDER BY id").fetchall())
        con.close()

    def test_writer_rejects_equal_total_with_one_missing_and_one_duplicate_vehicle(self):
        writer = self.load_writer()
        con = self.make_db()
        con.execute("DELETE FROM oil_change WHERE vehicle_id=12912")
        con.execute(
            "INSERT INTO oil_change(vehicle_id, source) VALUES (12372, 'owner-manual-verified')"
        )
        con.commit()
        with self.assertRaises(RuntimeError):
            writer.apply_quarantine(con)
        sources = con.execute(
            "SELECT DISTINCT source FROM oil_change WHERE vehicle_id IN (12372,12511,12777,12847,12912)"
        ).fetchall()
        self.assertEqual(sources, [("owner-manual-verified",)])
        con.close()


class Ic01BuildGuardTests(unittest.TestCase):
    def load_build(self):
        files_path = str(ROOT / "files")
        if files_path not in sys.path:
            sys.path.insert(0, files_path)
        spec = importlib.util.spec_from_file_location("ic01_build", BUILD_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_build_guard_rejects_a_poisoned_quarantine_projection(self):
        build = self.load_build()
        self.assertTrue(
            hasattr(build, "_assert_ic01_projection"),
            "the normal site rebuild must enforce the IC-01 projection contract",
        )
        records = verified_shell_records()
        records[0]["fluids"]["coolant"] = "unsupported value"
        with self.assertRaises(SystemExit):
            build._assert_ic01_projection(records)

    def test_build_refreshes_every_verified_count_claim_without_touching_svg_numbers(self):
        build = self.load_build()
        self.assertTrue(
            hasattr(build, "_refresh_verified_count_copy"),
            "verified-count marketing copy must be generated from the rebuilt projection",
        )
        html = """
        <meta content="3,667 vehicles searchable; 290 with owner's-manual-verified specifications">
        <meta content="3,667 vehicles searchable; 290 with owner's-manual-verified specifications">
        <h1>3,667 vehicles searchable, 290 with owner's-manual-verified specifications</h1>
        <span>290 Owner's-Manual-Verified</span>
        <div class="astat"><div class="astat-n">290</div><div class="astat-l">Verified Specs</div></div>
        <li>Owner's-manual-verified maintenance schedules &mdash; 290 vehicles and growing</li>
        <svg><rect x="290" height="290"></rect></svg>
        """
        refreshed = build._refresh_verified_count_copy(html, 285)
        self.assertIn("searchable; 285 with owner's-manual-verified", refreshed)
        self.assertIn(">285 Owner's-Manual-Verified<", refreshed)
        self.assertIn('<div class="astat-n">285</div>', refreshed)
        self.assertIn("&mdash; 285 vehicles and growing", refreshed)
        self.assertIn('<rect x="290" height="290">', refreshed)

    def test_build_refresh_rejects_a_missing_required_count_surface(self):
        build = self.load_build()
        incomplete = """
        <meta content="3,667 vehicles searchable; 290 with owner's-manual-verified specifications">
        <span>290 Owner's-Manual-Verified</span>
        <div class="astat"><div class="astat-n">290</div><div class="astat-l">Verified Specs</div></div>
        <li>Owner's-manual-verified maintenance schedules &mdash; 290 vehicles and growing</li>
        """
        with self.assertRaises(RuntimeError):
            build._refresh_verified_count_copy(incomplete, 285)


def sentra_record():
    return {
        "id": 467,
        "year": 2020,
        "make": "Nissan",
        "model": "Sentra",
        "trim": None,
        "engine": "2.0L I4",
        "oil": {"ver": 1, "visc": "0W-20", "cap_w": "4.4 qt"},
        "parts": {"ver": 1},
        "recalls": [{"camp": str(i)} for i in range(4)],
    }


def sample_markup(extra_selector=""):
    selector = "VEH[467]" + extra_selector
    return """
    <div id="kyr-sample"><div>2020 Nissan Sentra</div>
      <div>&#128738; 0W-20</div><div>&#128167; 4.4 qt</div>
      <div>4 Open Recalls</div><button onclick="openModal(467)">Open</button>
    </div>
    <script>function kyrHsDefaultPlacard(){var s=kyrPlSlot();if(!s)return;var v=%s;if(v)s.innerHTML=renderPlacard(v);}
    function kyrHsShowTrims(){return true;}</script>
    """ % selector


def count_markup(count):
    return """
    <meta name="description" content="3,667 vehicles searchable; {0} with owner's-manual-verified specifications">
    <meta property="og:description" content="3,667 vehicles searchable; {0} with owner's-manual-verified specifications">
    <h1 class="sr-only">3,667 vehicles searchable, {0} with owner's-manual-verified specifications</h1>
    <div class="db-badge">3667 SEARCHABLE - {0} OWNER'S-MANUAL-VERIFIED</div>
    <span>{0} Owner's-Manual-Verified</span>
    <div class="astat"><div class="astat-n">{0}</div><div class="astat-l">Verified Specs</div></div>
    <li>Owner's-manual-verified maintenance schedules &mdash; {0} vehicles and growing</li>
    """.format(count)


class Ic01VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("ic01_verifier", VERIFIER_PATH)
        cls.verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.verifier)

    def require_check(self, name):
        self.assertTrue(hasattr(self.verifier, name), "missing additive verifier check %s" % name)
        return getattr(self.verifier, name)

    def artifact(self):
        records = verified_shell_records() + [sentra_record()]
        markup = sample_markup() + count_markup(1)
        data_json = json.dumps({"v": records, "dtc": {}, "fixes": {}}, separators=(",", ":"))
        return SimpleNamespace(
            D={"v": records, "dtc": {}, "fixes": {}},
            specs={"_meta": {"record_count": 1}, "467": {"label": "2020 Nissan Sentra"}},
            index=markup,
            demo_markup=markup,
            readme=(
                "3,667 vehicles searchable; 1 with owner's-manual-verified specifications.\n"
                "Coverage: **1 vehicles with owner's-manual-verified specifications**"
            ),
            blob_json_raw=data_json,
            demo_json_raw=data_json,
        )

    def test_projection_check_rejects_value_and_restored_rows(self):
        check = self.require_check("s9_1_ic01_projection")
        artifact = self.artifact()
        self.assertEqual(check(artifact), [])
        artifact.D["v"][0]["oil"]["visc"] = "0W-20"
        artifact.D["v"][1]["maint"] = [{"ver": 1}]
        self.assertTrue(check(artifact))

    def test_guide_check_rejects_reinserted_quarantined_id(self):
        check = self.require_check("s9_2_ic01_guide_absent")
        artifact = self.artifact()
        self.assertEqual(check(artifact), [])
        artifact.specs["12912"] = {"label": "2022 Honda CR-V"}
        self.assertTrue(check(artifact))

    def test_sample_check_rejects_wrong_id_and_hidden_fallbacks(self):
        check = self.require_check("s9_3_ic01_sample_pin")
        artifact = self.artifact()
        self.assertEqual(check(artifact), [])
        artifact.demo_markup = sample_markup("||VEH[12912]||DB.v[0]") + count_markup(1)
        self.assertTrue(check(artifact))
        artifact.demo_markup = artifact.index.replace("openModal(467)", "openModal(12912)")
        self.assertTrue(check(artifact))

    def test_sample_check_requires_every_blob_derived_card_value(self):
        check = self.require_check("s9_3_ic01_sample_pin")
        for value in ("0W-20", "4.4 qt", "4 Open Recalls"):
            artifact = self.artifact()
            artifact.index = artifact.index.replace(value, "")
            artifact.demo_markup = artifact.demo_markup.replace(value, "")
            self.assertTrue(check(artifact), "missing %r must fail the sample contract" % value)

    def test_sample_check_scans_past_nested_braces_for_a_hidden_fallback(self):
        check = self.require_check("s9_3_ic01_sample_pin")
        artifact = self.artifact()
        safe = (
            "function kyrHsDefaultPlacard(){var s=kyrPlSlot();if(!s)return;"
            "var v=VEH[467];if(v)s.innerHTML=renderPlacard(v);}"
        )
        poisoned = (
            "function kyrHsDefaultPlacard(){var v=VEH[467];"
            "if(v){renderPlacard(v);}v=VEH[12912]||DB.v[0];}"
        )
        artifact.index = artifact.index.replace(safe, poisoned)
        artifact.demo_markup = artifact.demo_markup.replace(safe, poisoned)
        self.assertTrue(check(artifact))

    def test_sample_check_rejects_coordinated_blob_and_card_drift(self):
        check = self.require_check("s9_3_ic01_sample_pin")
        artifact = self.artifact()
        sample = next(v for v in artifact.D["v"] if v["id"] == 467)
        sample["year"] = 2021
        sample["oil"]["visc"] = "5W-30"
        sample["oil"]["cap_w"] = "9.9 qt"
        sample["recalls"] = sample["recalls"][:3]
        for surface in ("index", "demo_markup"):
            text = getattr(artifact, surface)
            text = text.replace("2020 Nissan Sentra", "2021 Nissan Sentra")
            text = text.replace("0W-20", "5W-30")
            text = text.replace("4.4 qt", "9.9 qt")
            text = text.replace("4 Open Recalls", "3 Open Recalls")
            setattr(artifact, surface, text)
        self.assertTrue(check(artifact))

    def test_count_check_rejects_one_stale_surface_and_readme_claim(self):
        check = self.require_check("s9_4_ic01_count_copy")
        artifact = self.artifact()
        self.assertEqual(check(artifact), [])
        artifact.index = artifact.index.replace(">1 Owner's-Manual-Verified<", ">290 Owner's-Manual-Verified<")
        artifact.readme = artifact.readme.replace("Coverage: **1 vehicles", "Coverage: **290 vehicles")
        self.assertTrue(check(artifact))

    def test_demo_blob_check_rejects_payload_drift(self):
        check = self.require_check("s9_5_demo_blob_equivalence")
        artifact = self.artifact()
        self.assertEqual(check(artifact), [])
        artifact.demo_json_raw = artifact.demo_json_raw.replace('"id":467', '"id":468')
        self.assertTrue(check(artifact))

    def test_mobile_nav_check_rejects_uncontained_primary_navigation(self):
        check = self.require_check("s9_7_mobile_nav_containment")
        artifact = self.artifact()
        containment = (
            "<style>@media (max-width:600px){"
            ".tabs{overflow-x:auto;-webkit-overflow-scrolling:touch}"
            "}</style>"
        )
        artifact.index += containment
        artifact.demo_markup += containment
        self.assertEqual(check(artifact), [])
        artifact.index = artifact.index.replace("overflow-x:auto", "overflow-x:visible")
        self.assertTrue(check(artifact))

    def make_scope_db(self, path):
        con = sqlite3.connect(path)
        for table in ("oil_change", "parts", "fluids", "torque_specs", "engine_specs", "maintenance", "ev_specs"):
            con.execute("CREATE TABLE %s (vehicle_id INTEGER, source TEXT)" % table)
        ids = (12372, 12511, 12777, 12847, 12912)
        for vehicle_id in ids:
            for table in ("oil_change", "parts", "fluids", "torque_specs"):
                con.execute(
                    "INSERT INTO %s(vehicle_id, source) VALUES (?, ?)" % table,
                    (vehicle_id, "quarantine-applicability-ic01"),
                )
            for _ in range(3):
                con.execute(
                    "INSERT INTO maintenance(vehicle_id, source) VALUES (?, ?)",
                    (vehicle_id, "quarantine-applicability-ic01"),
                )
        con.commit()
        return con

    def test_source_scope_rejects_restoration_concatenation_and_outsider_use(self):
        check = self.require_check("s9_6_ic01_source_scope")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scope.db")
            con = self.make_scope_db(path)
            artifact = SimpleNamespace(db_path=path)
            self.assertEqual(check(artifact), [])

            con.execute("UPDATE oil_change SET source='owner-manual-verified' WHERE vehicle_id=12372")
            con.commit()
            self.assertTrue(check(artifact))
            con.execute(
                "UPDATE oil_change SET source='quarantine-applicability-ic01' WHERE vehicle_id=12372"
            )

            con.execute(
                "UPDATE parts SET source='owner-manual-verified | quarantine-applicability-ic01' WHERE vehicle_id=12511"
            )
            con.commit()
            self.assertTrue(check(artifact))
            con.execute(
                "UPDATE parts SET source='quarantine-applicability-ic01' WHERE vehicle_id=12511"
            )

            con.execute(
                "INSERT INTO engine_specs(vehicle_id, source) VALUES (999999, 'quarantine-applicability-ic01')"
            )
            con.commit()
            self.assertTrue(check(artifact))
            con.execute("DELETE FROM engine_specs WHERE vehicle_id=999999")

            con.execute(
                "INSERT INTO ev_specs(vehicle_id, source) VALUES (999999, 'quarantine-applicability-ic01')"
            )
            con.commit()
            self.assertTrue(check(artifact))
            con.close()


if __name__ == "__main__":
    unittest.main()
