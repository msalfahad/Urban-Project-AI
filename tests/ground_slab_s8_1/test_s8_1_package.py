"""S8.1 (research/alsenan_ground_slab_s8_1): ground slab, the two source-zoned cells only.

The checks below re-derive the package from its own outputs and from the frozen inputs, never from an earlier
ground-slab figure:

- the zones are exactly the cells the two T=10 markers sit in;
- every PRE-S8 face terminates once, the parent carries no quantity of its own;
- concrete is net area x the printed thickness, and only in the zones;
- each mesh direction has its own strips, each covering the zone area exactly (no +1, no rounding, one family);
- blocked records carry no quantity, unknown is never written as 0;
- zone / direction / diameter / parent / floor totals reconcile, and nothing overlaps another owner;
- the builder is blind and its rebuild is byte-identical."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_ground_slab_s8_1"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
OUTPUTS = ["00_README.md", "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv", "02_SOURCE_RULE_REGISTER.csv",
           "03_CONCRETE_QTO.csv", "04_REINFORCEMENT_XY_QTO.csv", "05_REINFORCEMENT_STRIPS.csv",
           "06_BLOCKED_UNRESOLVED_COMPONENTS.csv", "07_OVERLAP_AND_OWNERSHIP_AUDIT.csv",
           "08_FLOOR_ZONE_SUMMARY.csv", "09_PROVENANCE.jsonl", "10_S8_1_SUMMARY.json",
           "12_PRE_S8_POPULATION_RECONCILIATION.csv"]
ZONES = {"GS-ZONE-1690": "SP-GBP-08", "GS-ZONE-169D": "SP-GBP-14"}
S7_TOTAL = 3802.015364542223


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return float(v)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("build_s8_1", PKG / "build_s8_1.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def pop():
    return rows(PKG / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv")


@pytest.fixture(scope="module")
def bars():
    return rows(PKG / "04_REINFORCEMENT_XY_QTO.csv")


@pytest.fixture(scope="module")
def conc():
    return rows(PKG / "03_CONCRETE_QTO.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "10_S8_1_SUMMARY.json")


# ------------------------------------------------------------------ freeze and frozen inputs
def test_freeze_manifest_still_matches():
    m = J(PKG / "11_S8_1_FREEZE_MANIFEST.json")
    assert m["round"] == "S8_1" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    DR.verify_frozen(PKG / "11_S8_1_FREEZE_MANIFEST.json", ROOT)


def test_every_frozen_baseline_still_matches_and_s7_is_unchanged(mod, summary):
    for name, man in mod.MANIFESTS.items():
        assert DR.verify_frozen(man, ROOT)["manifest_sha256"] == summary["frozen_baselines"][name]
    s7 = J(ROOT / "research/alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json")
    assert s7["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"] == summary["s7_total_kg"] == S7_TOTAL


# ------------------------------------------------------------------ zones and population
def _inside(poly, p):
    x, y = p
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def test_the_zones_are_the_cells_the_two_markers_sit_in(pop, summary):
    assert {z: v["panel_id"] for z, v in summary["zones"].items()} == ZONES
    cells = [r for r in pop if r["S1_CLASS"] == "SLAB_PANEL"]
    for r in pop:
        if not r["ZONE_ID"]:
            continue
        mk = json.loads(r["ZONE_MARKER"])
        assert mk["texts"] == ["T=10cm", "5Ø10/m E.W."]
        hits = [c["PANEL_ID"] for c in cells if _inside(json.loads(c["POLYGON_MM"]), mk["circle_centre_mm"])]
        assert hits == [r["PANEL_ID"]]                         # one marker, one cell, independently re-tested
    assert sum(1 for r in pop if r["ZONE_ID"]) == 2


def test_every_face_terminates_once_and_the_parent_owns_nothing(pop):
    faces = [r for r in pop if r["ROW_KIND"] == "FACE"]
    assert len(faces) == len({r["ROW_ID"] for r in faces}) == 21
    assert Counter(r["TERMINAL_STATE"] for r in faces) == {"MEASURED_ONCE_IN_ZONE": 2,
                                                          "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH": 19}
    assert all(r["PARENT_ELEMENT"] == "SPC-GROUND_SLAB" for r in faces)
    parent = [r for r in pop if r["ROW_KIND"] == "PARENT"]
    assert len(parent) == 1 and parent[0]["TERMINAL_STATE"] == "PARENT_AGGREGATE_ONLY"
    other = {r["ROW_ID"]: r["TERMINAL_STATE"] for r in pop if r["ROW_KIND"] == "SHEET_RECORD_OUTSIDE_POPULATION"}
    assert set(other) == {"SP-GBP-01", "SP-GBP-12"}
    assert other["SP-GBP-12"].startswith("OTHER_OWNER (S8 STAIR")


def test_thickness_and_mesh_only_where_the_source_puts_them(pop):
    for r in pop:
        if r["ZONE_ID"]:
            assert f(r["SOURCE_THICKNESS_MM"]) == 100 and r["SOURCE_REBAR_CALLOUT"] == "5Ø10/m E.W."
        else:
            assert r["SOURCE_THICKNESS_MM"] == "" and r["SOURCE_REBAR_CALLOUT"] == ""
            if r["ROW_KIND"] == "FACE":
                assert r["THICKNESS_AUTHORITY"].startswith("NOT_ESTABLISHED")


def test_exact_zone_areas_from_the_drawn_geometry(summary):
    z = summary["zones"]
    assert z["GS-ZONE-1690"]["area_m2"] == pytest.approx(4.225 * 3.525, abs=1e-9)
    assert z["GS-ZONE-169D"]["area_m2"] == pytest.approx(3.8 * 6.1 - (1 - math.pi / 4) * 1.0, abs=1e-9)
    assert z["GS-ZONE-169D"]["arc_chords_replaced"] > 0          # the R1000 corner is an arc, not chords
    assert z["GS-ZONE-169D"]["levels"] == ["+0.30"]


# ------------------------------------------------------------------ quantities
def test_concrete_is_net_area_times_the_printed_thickness(conc, summary):
    assert {r["ZONE_ID"] for r in conc} == set(ZONES)
    for r in conc:
        assert f(r["VOLUME_M3"]) == pytest.approx(f(r["NET_AREA_M2"]) * 0.100, rel=1e-12)
        assert f(r["THICKNESS_MM"]) == 100 and r["LANE"] == "PROJECT_BASIS_QTO"
        assert "no earlier register line" in r["MEASUREMENT_ORIGIN"]
    assert summary["concrete_m3"] == pytest.approx(sum(f(r["VOLUME_M3"]) for r in conc), rel=1e-12)


def test_each_direction_is_rate_times_its_own_strip_integral(bars):
    assert Counter((r["ZONE_ID"], r["DIRECTION"]) for r in bars) == {(z, d): 1 for z in ZONES for d in ("X", "Y")}
    strips = rows(PKG / "05_REINFORCEMENT_STRIPS.csv")
    for r in bars:
        own = [s for s in strips if s["ZONE_ID"] == r["ZONE_ID"] and s["DIRECTION"] == r["DIRECTION"]]
        assert len(own) == int(r["STRIP_COUNT"]) > 0
        integ = math.fsum(f(s["INTEGRAL_MM2"]) for s in own) / 1e6
        assert integ == pytest.approx(f(r["STRIP_INTEGRAL_M2"]), rel=1e-12)
        assert integ == pytest.approx(f(r["ZONE_AREA_M2"]), rel=1e-9)          # strips cover the zone exactly
        assert f(r["EQUIVALENT_LENGTH_M"]) == pytest.approx(5 * integ, rel=1e-12)
        assert f(r["KG"]) == pytest.approx(5 * integ * 10 ** 2 / 162, rel=1e-12)
        assert math.fsum(f(s["KG"]) for s in own) == pytest.approx(f(r["KG"]), rel=1e-12)
        assert f(r["DISTRIBUTION_WIDTH_M"]) == pytest.approx(math.fsum(f(s["WIDTH_MM"]) for s in own) / 1000)
    by = {(r["ZONE_ID"], r["DIRECTION"]): r for r in bars}
    for z in ZONES:                                              # the two families are measured independently
        sx = [(s["T0_MM"], s["T1_MM"]) for s in strips if s["ZONE_ID"] == z and s["DIRECTION"] == "X"]
        sy = [(s["T0_MM"], s["T1_MM"]) for s in strips if s["ZONE_ID"] == z and s["DIRECTION"] == "Y"]
        assert sx != sy
        assert by[(z, "X")]["DISTRIBUTION_WIDTH_M"] != by[(z, "Y")]["DISTRIBUTION_WIDTH_M"]


def test_no_plus_one_no_rounding_no_second_mat(bars):
    counts = [f(r["EQUIVALENT_COUNT_UNROUNDED"]) for r in bars]
    assert any(c != int(c) for c in counts)                      # 17.625 bars stays 17.625
    for r in bars:
        assert f(r["EQUIVALENT_COUNT_UNROUNDED"]) == pytest.approx(5 * f(r["DISTRIBUTION_WIDTH_M"]))
        assert r["PHYSICAL_BBS_COUNT"] == "UNRESOLVED" and int(r["BAR_FAMILIES_IN_DIRECTION"]) == 1
        assert r["LANE"] == "PROJECT_BASIS_QTO" and r["END_TREATMENT"].startswith("BLOCKED")


def test_blocked_records_carry_no_quantity(summary):
    b = rows(PKG / "06_BLOCKED_UNRESOLVED_COMPONENTS.csv")
    assert len(b) == summary["blocked_records"] == 19 * 2 + 2 * 9
    assert all(r["KG"] == "" and r["M3"] == "" for r in b)       # unknown is not zero
    assert Counter(r["LANE"] for r in b) == {"BLOCKED_UNQUANTIFIED": 54, "SOURCE_CONFLICT": 2}
    for z in ZONES:
        comps = {r["COMPONENT"] for r in b if r["SUBJECT"] == z}
        assert {"END_ANCHORAGE_X", "END_ANCHORAGE_Y", "FABRICATION_COUNT_X", "FABRICATION_COUNT_Y",
                "SUPPORT_INTERFACE", "SUPPLEMENTARY_BARS", "LAP_SPLICES", "LAYER_POSITION_AND_COVER"} <= comps
    cells = {r["SUBJECT"] for r in b if r["SUBJECT"].startswith("SP-GBP")}
    assert len(cells) == 19 and not cells & set(ZONES.values())


def test_totals_reconcile_by_zone_direction_parent_floor_and_project(bars, conc, summary):
    s = rows(PKG / "08_FLOOR_ZONE_SUMMARY.csv")
    zone = [r for r in s if r["LEVEL"] == "ZONE"]
    total = math.fsum(f(r["KG"]) for r in bars)
    assert math.fsum(f(r["TOTAL_KG"]) for r in zone) == pytest.approx(total, rel=1e-12)
    for lvl in ("FLOOR", "PARENT", "PROJECT"):
        row = [r for r in s if r["LEVEL"] == lvl][0]
        assert f(row["TOTAL_KG"]) == pytest.approx(total, rel=1e-12)
        assert f(row["CONCRETE_M3"]) == pytest.approx(math.fsum(f(r["VOLUME_M3"]) for r in conc), rel=1e-12)
        assert f(row["X_KG"]) + f(row["Y_KG"]) == pytest.approx(total, rel=1e-12)
    assert [r["ID"] for r in s if r["LEVEL"] == "PROJECT"] == ["RESTRICTED_S8_1_PROJECT_BASIS"]
    assert summary["total_kg"] == pytest.approx(total, rel=1e-12)
    assert all(summary["reconciliation"]["mass"].values()) and all(summary["reconciliation"]["concrete"].values())


# ------------------------------------------------------------------ rules, overlaps, ownership
def test_only_the_ground_slab_note_sizes_a_quantity():
    rr = {r["ITEM"]: r for r in rows(PKG / "02_SOURCE_RULE_REGISTER.csv")}
    assert rr["P3-GROUND-SLAB"]["S8_1_ROLE"] == "APPLIED_IN_THE_TWO_MARKED_CELLS"
    assert rr["P8-N22"]["S8_1_ROLE"] == "SOURCE_CONFLICT_RECORDED"
    for rid in ("P8-N18", "P1-NOTE-A", "P4-6-NOTE-2", "P15-TEMP-TABLE", "P15-TEMP-NOTES", "P15-SLAB-ON-BEAMS"):
        assert rr[rid]["S8_1_ROLE"] == "EXCLUDED_SUSPENDED_SLAB_RULE"
    ex = json.loads(rr["TEXT_EXHAUSTION"]["TEXT"])
    assert ex == {"DET: 10cm PLAIN CONCRETE.": 1, "GBP: 5Ø10/m E.W.": 2, "GBP: T=10cm": 2}
    for p in (json.loads(x) for x in (PKG / "09_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()):
        assert p["rules"] == ["P3-GROUND-SLAB"]


def test_nothing_overlaps_another_owner():
    a = rows(PKG / "07_OVERLAP_AND_OWNERSHIP_AUDIT.csv")
    assert all(r["RESULT"].startswith("PASS") for r in a)
    ftg = [json.loads(r["EVIDENCE"]) for r in a if "FTG-" in r["CHECK_ID"]]
    assert ftg and all(e["build_up_needed_for_contact_m"] > 0 and e["footing_top_at_most_m"] < 0 for e in ftg)
    lw = [json.loads(r["EVIDENCE"]) for r in a if r["CHECK_ID"].endswith("-LINEWORK")]
    assert len(lw) == 2 and all(set(e) <= {"S-AXIS", "S-FOOTINGS"} for e in lw)
    ids = {r["CHECK_ID"] for r in a}
    assert {"OV-LIFT-FF", "OV-POOL", "OV-STAIR", "OV-S7", "OV-PARENT", "OV-LEGACY"} <= ids


def test_pre_s8_column_and_footing_populations_reconcile_by_id():
    r = {x["POPULATION"].split(" ")[0]: x for x in rows(PKG / "12_PRE_S8_POPULATION_RECONCILIATION.csv")}
    assert r["COLUMN"]["ID_SETS_EQUAL"] == "True" and int(r["COLUMN"]["STAGE_IDS"]) == 95
    assert json.loads(r["COLUMN"]["PRE_S8_BREAKDOWN"]) == {"COLUMN": 59, "NECK_PEDESTAL": 36}
    assert r["FOOTING"]["ID_SETS_EQUAL"] == "True" and int(r["FOOTING"]["STAGE_IDS"]) == 26
    assert sum(json.loads(r["FOOTING"]["PRE_S8_BREAKDOWN"]).values()) == 26


def test_no_forbidden_label_and_no_final_claim():
    from engine.source import slab_rebar_qto as SR
    for name in OUTPUTS:
        text = (PKG / name).read_text(encoding="utf-8")
        for bad in SR.FORBIDDEN_LABELS:
            assert bad not in text, (name, bad)


def test_builder_is_blind(mod):
    src = (PKG / "build_s8_1.py").read_text(encoding="utf-8")
    for tok in ("BOQ_LINES", "registers_v3b", "coverage_recovery", "ground_slab_recovery", "freelancer", "donor",
                "christ", "U-C4N", "kg/m3", "benchmark", "post_freeze_comparison"):
        assert tok not in src, tok
    assert "CONCRETE_QUANTITY_STATE" not in mod.CENSUS_COLUMNS and "REBAR_COMPONENTS" not in mod.CENSUS_COLUMNS


def test_registry_declares_the_engine_and_the_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "engine/source/ground_slab_qto.py" in RP.ACCURATE_MODULES
    assert "research/alsenan_ground_slab_s8_1/build_s8_1.py" in RP.ACCURATE_BUILDERS


def test_rebuild_is_byte_identical():
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in OUTPUTS}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_1.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in OUTPUTS}
    assert before == after
