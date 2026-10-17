"""S8.2 (research/alsenan_swimming_pool_s8_2): swimming-pool source-controlled concrete and reinforcement QTO.

The checks re-derive the package from its own outputs, the frozen earlier stages and the S1 census, never from an
earlier pool figure:

- the package is frozen before comparison and every earlier frozen stage still matches;
- the plan geometry is exact (rectangle + semicircle) and the wall runs tile the band once;
- every one of the 26 S1 pool records terminates, each bar family has one owner, no bar is counted twice;
- nothing is released: no blocked or conflicting row carries kg, m3 or m2, totals stay unknown (empty), never 0;
- no NTS drawn length becomes a measurement and no ratio enters a total;
- the build-up keeps its printed wording as separate BOQ families and the pool's plain concrete is counted once;
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
from engine.source import pool_qto as PQ
from engine.source import slab_rebar_qto as SR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_swimming_pool_s8_2"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
MANIFEST = PKG / "18_S8_2_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_POOL_SOURCE_AND_RULE_REGISTER.csv", "02_POOL_POPULATION_AND_OWNERSHIP.csv",
           "03_CONCRETE_GEOMETRY_AND_QTO.csv", "04_BASE_REINFORCEMENT_QTO.csv", "05_WALL_REINFORCEMENT_QTO.csv",
           "06_BAR_RUN_AND_BENT_BAR_REGISTER.csv", "07_BLOCKED_REINFORCEMENT_REGISTER.csv",
           "08_WALL_BASE_INTERFACE_AUDIT.csv", "09_PLAIN_CONCRETE_AND_BUILD_UP_REGISTER.csv",
           "10_FLOOR_POOL_SUMMARY.csv", "11_PROVENANCE.jsonl", "12_CONSERVATION_CHECKS.csv",
           "13_REBAR_EVIDENCE_BINDING.csv", "14_COVER_APPLICABILITY.csv", "15_SENSITIVITY_SCENARIOS.csv",
           "16_CONFLICT_AND_QUESTION_REGISTER.csv", "17_S8_2_SUMMARY.json"]
DRAWINGS = [ROOT / "data/inputs/by_sha256" / n for n in (
    "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf",
    "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf",
    "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf")]
needs_drawings = pytest.mark.skipif(not all(p.exists() for p in DRAWINGS),
                                    reason="private client drawings not restored in data/inputs/by_sha256")
A_OUT = 3.5 * 1.75 + math.pi * 1.75 ** 2 / 2          # structural outline: 3.50 x 1.75 rectangle + R1.75 semicircle
A_IN = 3.1 * 1.55 + math.pi * 1.55 ** 2 / 2           # water outline: 3.10 x 1.55 rectangle + R1.55 semicircle


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def L(v):
    return json.loads(v) if v else []


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("build_s8_2", PKG / "build_s8_2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "17_S8_2_SUMMARY.json")


# ------------------------------------------------------------------ freeze and frozen inputs
def test_frozen_before_comparison_and_still_matching():
    m = J(MANIFEST)
    assert m["round"] == "S8_2" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    assert m["released"] == {"concrete_m3": 0.0, "reinforcement_kg": 0.0}
    assert m["drawing_sha256"] == {"ST7757.dxf": DRAWINGS[0].stem, "P7757.dxf": DRAWINGS[1].stem,
                                   "ST7757.pdf": DRAWINGS[2].stem}
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_frozen_stage_matches(mod, summary):
    assert len(mod.MANIFESTS) == 16 and {"S7", "S8.1", "S8.1A"} <= set(mod.MANIFESTS)
    for name, man in mod.MANIFESTS.items():
        assert DR.verify_frozen(man, ROOT)["manifest_sha256"] == summary["frozen_baselines"][name]


# ------------------------------------------------------------------ plan geometry
def test_plan_areas_are_exact_and_the_runs_tile_the_band(summary):
    pm = summary["plan_m2"]
    assert pm["structural_footprint"] == pytest.approx(A_OUT, abs=1e-12)
    assert pm["water"] == pytest.approx(A_IN, abs=1e-12)
    assert pm["wall_band"] == pytest.approx(A_OUT - A_IN, abs=1e-12)
    runs = pm["wall_runs"]
    assert runs["PL-WALL-RUN-E"] == pytest.approx(0.2 * 3.5) and runs["PL-WALL-RUN-N"] == pytest.approx(0.2 * 1.55)
    assert runs["PL-WALL-RUN-S"] == pytest.approx(0.2 * 1.55)
    assert runs["PL-WALL-RUN-W"] == pytest.approx(math.pi * (1.75 ** 2 - 1.55 ** 2) / 2, abs=1e-12)
    assert math.fsum(runs.values()) == pytest.approx(pm["wall_band"], abs=1e-9)
    assert summary["perimeter_m"]["outer"] == pytest.approx(3.5 + 3.5 + math.pi * 1.75, abs=1e-12)
    assert summary["perimeter_m"]["water"] == pytest.approx(3.1 + 3.1 + math.pi * 1.55, abs=1e-12)


def test_the_water_outline_is_not_the_base_footprint():
    g = {r["ROW_ID"]: r for r in rows("03_CONCRETE_GEOMETRY_AND_QTO.csv")}
    assert "base footprint" in g["CG-02"]["ITEM"] and "water" in g["CG-01"]["ITEM"]
    assert float(g["CG-02"]["VALUE"]) > float(g["CG-01"]["VALUE"])
    assert "wall / base intersection" in g["CO-01"]["ITEM"] and "owned once, by the BASE" in g["CO-01"]["NOTE"]


# ------------------------------------------------------------------ population and ownership
def test_one_parent_one_owner_and_absent_components_are_not_assumed():
    pop = rows("02_POOL_POPULATION_AND_OWNERSHIP.csv")
    ids = {r["COMPONENT_ID"] for r in pop}
    assert [r["COMPONENT_ID"] for r in pop if r["ROW_KIND"] == "PARENT"] == ["SPC-POOL"]
    assert all(r["PARENT"] == "SPC-POOL" for r in pop if r["ROW_KIND"] != "PARENT")
    assert all(r["COMPONENT_OWNER_ID"] for r in pop)
    absent = {r["COMPONENT_ID"] for r in pop if r["EXISTS"] == "NOT_SHOWN_IN_SOURCE"}
    assert absent == {"PL-STEPS", "PL-THICKENING", "PL-OPENINGS", "PL-PUMP-ROOM"}
    assert all(not r["PLAN_AREA_M2"] for r in pop if r["COMPONENT_ID"] in absent)
    fams = rows("04_BASE_REINFORCEMENT_QTO.csv") + rows("05_WALL_REINFORCEMENT_QTO.csv")
    assert len(fams) == 21 and all(f["COMPONENT_OWNER_ID"] in ids for f in fams)


def test_the_dome_detail_is_kept_out():
    pool_handles = {h for r in rows("02_POOL_POPULATION_AND_OWNERSHIP.csv") for h in L(r["DXF_HANDLES"])}
    bound = {h for r in rows("13_REBAR_EVIDENCE_BINDING.csv") for h in [r["HANDLE"]] + L(r["LEADER"])}
    assert not ({"182B", "182E", "19B1", "182F"} & (pool_handles | bound))


# ------------------------------------------------------------------ the 26 records
EXPECTED_26 = {"FAMILY_PRIMARY_LABEL": 17, "SAME_FAMILY_SECOND_LABEL (counted once)": 1, "SECOND_VIEW_OF_FAMILY": 5,
               "SECOND_VIEW_DIAMETER_CONFLICT": 1, "SECOND_VIEW_TOPOLOGY_DIFFERS": 1,
               "SUB_DETAIL_BINDING_AMBIGUOUS": 1}


def test_all_26_records_terminate():
    ev = rows("13_REBAR_EVIDENCE_BINDING.csv")
    s1 = J(S1 / "POOL_STRUCTURAL_REGISTER.json")["rows"]
    assert sorted(r["S1_SOURCE_ID"] for r in ev) == sorted(r["source_id"] for r in s1) and len(ev) == 26
    assert dict(Counter(r["TERMINAL_STATE"] for r in ev)) == EXPECTED_26
    assert all(r["KG"] == "" for r in ev)
    by = {r["HANDLE"]: r for r in ev}
    assert (by["18A8"]["TERMINAL_STATE"], by["18DD"]["TERMINAL_STATE"], by["1869"]["TERMINAL_STATE"]) == (
        "SECOND_VIEW_DIAMETER_CONFLICT", "SECOND_VIEW_TOPOLOGY_DIFFERS", "SUB_DETAIL_BINDING_AMBIGUOUS")
    assert {h: by[h]["FAMILY_ID"] for h in ("1860", "187C", "18D7", "18DB", "1929")} == {
        "1860": "BF-R5", "187C": "BF-R1-D14", "18D7": "BF-R6", "18DB": "BF-R2", "1929": "BF-R4"}
    # sub-detail labels are second views, never families of their own
    assert all(r["QUANTITY_LANE"] == "VIEW_ONLY" for r in ev if r["BINDING_METHOD"] == "PROXIMITY_SUB_DETAIL")


def test_a_finite_group_is_never_a_rate():
    fams = {f["FAMILY_ID"]: f for f in rows("04_BASE_REINFORCEMENT_QTO.csv") + rows("05_WALL_REINFORCEMENT_QTO.csv")}
    for fid, n in (("BF-1881", 3), ("BF-1896", 3), ("BF-192B", 4)):
        assert fams[fid]["NOTATION_KIND"] == PQ.FINITE_GROUP and fams[fid]["PER_M"] == "" and int(fams[fid]["COUNT"]) == n
    runs = {r["BAR_RUN_ID"]: r for r in rows("06_BAR_RUN_AND_BENT_BAR_REGISTER.csv")}
    for fid, row in (("BF-1881", "DOTROW-DEEP_BASE-UNDER_WALL_BOTTOM"), ("BF-1896", "DOTROW-DEEP_WALL-TOP"),
                     ("BF-192B", "DOTROW-SHALLOW_BASE-UNDER_WALL_BOTTOM")):
        assert len(L(runs[row]["SEGMENTS"])) == int(fams[fid]["COUNT"])          # drawn dots = the group's count


def test_one_drawn_diameter_conflict_splits_the_run_and_releases_nothing():
    fams = {f["FAMILY_ID"]: f for f in rows("05_WALL_REINFORCEMENT_QTO.csv")}
    assert {fams[f]["LANE"] for f in ("BF-R1-D12", "BF-R1-D14", "BF-R1-CONNECTOR")} == {PQ.CONFLICT}
    assert (fams["BF-R1-D12"]["DIA_MM"], fams["BF-R1-D14"]["DIA_MM"]) == ("12", "14")


# ------------------------------------------------------------------ nothing released; unknown is not zero
def test_no_blocked_row_carries_a_quantity_and_totals_stay_unknown(summary):
    for name, keys in (("03_CONCRETE_GEOMETRY_AND_QTO.csv", ("M3",)), ("04_BASE_REINFORCEMENT_QTO.csv", ("KG", "LENGTH_M")),
                       ("05_WALL_REINFORCEMENT_QTO.csv", ("KG", "LENGTH_M")),
                       ("07_BLOCKED_REINFORCEMENT_REGISTER.csv", ("KG", "LENGTH_M")),
                       ("09_PLAIN_CONCRETE_AND_BUILD_UP_REGISTER.csv", ("AREA_M2", "VOLUME_M3"))):
        for r in rows(name):
            assert r.get("LANE") != PQ.RELEASED, (name, r)
            assert all(r[k] == "" for k in keys), (name, r)
    assert summary["concrete"] == {"released_m3": 0.0, "blocked_rows": 7, "total_m3": None}
    assert summary["reinforcement"]["released_kg"] == 0.0 and summary["reinforcement"]["total_kg"] is None
    assert summary["reinforcement"]["lanes"] == {PQ.BLOCKED: 16, PQ.CONFLICT: 5}
    for r in rows("10_FLOOR_POOL_SUMMARY.csv"):
        assert r["RELEASED_ROWS"] == "0" and r["TOTAL_QTY"] == "" and r["TOTAL_STATE"].startswith("UNKNOWN")


def test_totals_reconcile_component_trade_floor():
    s = rows("10_FLOOR_POOL_SUMMARY.csv")
    for trade in {r["TRADE"] for r in s}:
        t = [r for r in s if r["TRADE"] == trade]
        comp = sum(int(r["ROWS"]) for r in t if r["LEVEL"] == "COMPONENT")
        assert [int(r["ROWS"]) for r in t if r["LEVEL"] in ("POOL_TRADE", "FLOOR")] == [comp, comp]
    assert {r["TRADE"] for r in s} == {"RC_CONCRETE", "REINFORCEMENT", "PLAIN_CONCRETE", "SCREED",
                                       "WATERPROOFING_OR_INSULATION"}


def test_no_nts_length_is_made_exact():
    for name in ("04_BASE_REINFORCEMENT_QTO.csv", "05_WALL_REINFORCEMENT_QTO.csv", "06_BAR_RUN_AND_BENT_BAR_REGISTER.csv"):
        for r in rows(name):
            for k in ("CUT_LENGTH_MM", "BAR_RUN_M", "LENGTH_M", "DISTRIBUTION_WIDTH_M"):
                assert r.get(k, "") == "", (name, k, r)
    for r in rows("06_BAR_RUN_AND_BENT_BAR_REGISTER.csv"):
        if r["ROW_KIND"] in ("DRAWN_RUN", "SUB_DETAIL_SHAPE"):
            assert r["STRAIGHT_PORTIONS"].startswith("NOT_MEASURABLE")


def test_sensitivity_never_enters_a_total():
    sen = rows("15_SENSITIVITY_SCENARIOS.csv")
    assert sen and all(r["LANE"] == PQ.SENSITIVITY_ONLY and r["IN_OFFICIAL_TOTAL"] == "False" for r in sen)
    assert not any(r["UNIT"].replace(" ", "").split("/") == ["kg", "m3"] for r in sen)


# ------------------------------------------------------------------ interfaces
def test_each_run_has_one_interface_row_per_junction_and_one_owner():
    it = rows("08_WALL_BASE_INTERFACE_AUDIT.csv")
    assert len(it) == 14 and len({r["INTERFACE_ID"] for r in it}) == 14
    assert dict(Counter(r["VERDICT"] for r in it)) == {"BASE_ONLY": 3, "SINGLE_BENT_BAR": 5, "UNRESOLVED": 6}
    owners = {}
    for r in it:
        owners.setdefault(r["BAR_RUN_ID"], set()).add(r["COMPONENT_OWNER_ID"])
    assert all(len(v) == 1 for v in owners.values())
    # a level-change junction lists only bars that cross it
    assert all(float(r["IN_UPPER_UNITS"]) > 1 and float(r["IN_LOWER_UNITS"]) > 1 for r in it
               if r["JUNCTION"] in ("J-DEEP-SLOPE", "J-SLOPE-SHALLOW"))


def test_drawn_segments_belong_to_one_run_and_one_family():
    runs = [r for r in rows("06_BAR_RUN_AND_BENT_BAR_REGISTER.csv") if r["ROW_KIND"] == "DRAWN_RUN"]
    seg = Counter(s for r in runs for s in L(r["SEGMENTS"]))
    assert seg and max(seg.values()) == 1
    assert [r["SHAPE"] for r in runs] == ["COMPOUND", "CRANKED", "CRANKED", "COMPOUND", "CRANKED", "CRANKED"]


# ------------------------------------------------------------------ build-up and cover
def test_build_up_keeps_its_wording_and_separate_families():
    bu = {r["LAYER_ID"]: r for r in rows("09_PLAIN_CONCRETE_AND_BUILD_UP_REGISTER.csv")}
    assert {k: (v["SOURCE_WORDING"], v["BOQ_FAMILY"], v["POSITION_FROM_CONCRETE"]) for k, v in bu.items()} == {
        "PL-BUILDUP-SCREED": ("5cm SECREED.", "SCREED", "1"),
        "PL-BUILDUP-INSULATION_MEMBRANE": ("5cm INSULATION MEMBRANE.", "WATERPROOFING_OR_INSULATION", "2"),
        "PL-BUILDUP-PLAIN_CONCRETE": ("10cm PLAIN CONCRETE.", "PLAIN_CONCRETE", "3")}
    assert bu["PL-BUILDUP-INSULATION_MEMBRANE"]["MEANING_NOT_ESTABLISHED"]
    assert "PS8-BLINDING-UNDER-FOOTINGS" in bu["PL-BUILDUP-PLAIN_CONCRETE"]["INTERFACE"]
    assert all("not the ground slab" in v["NOT_GROUND_SLAB"] for v in bu.values())


def test_cover_is_applied_only_where_its_scope_is_established():
    cv = {r["FACE"]: r for r in rows("14_COVER_APPLICABILITY.csv")}
    assert all(r[k] == "" for r in cv.values() for k in ("SOURCE_MINIMUM_MM", "NOMINAL_DESIGN_COVER_MM",
                                                           "FABRICATION_COVER_MM"))
    assert cv["WALL_INNER_AND_BASE_TOP (water-facing)"]["STATE"] == "UNKNOWN_EXPOSURE_CONDITION"
    assert cv["CHECKER"]["STATE"] == "CHALLENGE_ONLY"


# ------------------------------------------------------------------ conflicts, questions, checks
def test_conflicts_and_questions():
    q = rows("16_CONFLICT_AND_QUESTION_REGISTER.csv")
    ids = [r["ID"] for r in q]
    assert {"CF-S8.2-R1", "CF-S8.2-18A8", "CF-S8.2-18DD", "CF-S8.2-1869", "CF-S8.2-M1",
            "CF-S8.2-NTS-SCALE", "CF-S8.2-BLINDING"} <= set(ids)
    assert [i for i in ids if i.startswith("Q-")] == [f"Q-S8.2-{i:02d}" for i in range(1, 12)]
    assert not any(r["TO"].lower().startswith("owner") for r in q)


def test_every_conservation_check_passes():
    c = rows("12_CONSERVATION_CHECKS.csv")
    assert [r["CHECK_ID"] for r in c] == [f"C-{i:02d}" for i in range(1, 17)]
    assert all(r["RESULT"] == "PASS" for r in c)


def test_provenance_covers_every_record():
    prov = [json.loads(l) for l in (PKG / "11_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    recs = {p["record"] for p in prov}
    assert {r["COMPONENT_ID"] for r in rows("02_POOL_POPULATION_AND_OWNERSHIP.csv")} <= recs
    assert {r["S1_SOURCE_ID"] for r in rows("13_REBAR_EVIDENCE_BINDING.csv")} <= recs
    assert all(p.get("drawing_sha256") for p in prov)


# ------------------------------------------------------------------ hygiene
def test_no_forbidden_label():
    for name in OUTPUTS:
        text = (PKG / name).read_text(encoding="utf-8")
        for bad in SR.FORBIDDEN_LABELS:
            assert bad not in text, (name, bad)


def test_builder_and_engine_are_blind(mod):
    for src in (PKG / "build_s8_2.py", ROOT / "engine" / "source" / "pool_qto.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ",
                    "U-C4N", "kg/m3", "benchmark", "post_freeze"):
            assert tok not in text, (src.name, tok)
    assert "QUANTITY" not in " ".join(mod.CENSUS_COLUMNS) and "KG" not in " ".join(mod.CENSUS_COLUMNS)


def test_registry_declares_the_engine_and_the_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "engine/source/pool_qto.py" in RP.ACCURATE_MODULES
    assert "research/alsenan_swimming_pool_s8_2/build_s8_2.py" in RP.ACCURATE_BUILDERS


@needs_drawings
def test_rebuild_is_byte_identical():
    names = OUTPUTS + [MANIFEST.name]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_2.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
