"""S8.3A (research/alsenan_dome_mesh_s8_3a): independent audit of the frozen dome-shell mesh quantity.

S8.3 and its errata are untouched; scenario A reproduces the frozen 602.111304 kg exactly; scenario B reproduces the
fixed-meridian cross-check (about 798.915 kg) from first principles; nothing new is released; the frozen quantity is
re-classified IDEALIZED_SURFACE_DENSITY_QTO with no lower-bound or BBS claim; no bar object is counted twice."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_dome_mesh_s8_3a"
S83 = ROOT / "research" / "alsenan_dome_ring_s8_3"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
KG12 = 144 / 162


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, pkg=PKG):
    with open(pkg / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PKG / "08_S8_3A_SUMMARY.json")


def _first_principles():
    c, h, t = 4.42, 1.90, 0.10                             # p.7 printed span, rise, thickness
    R = (c * c / 4 + h * h) / (2 * h)
    d = R - h
    Rm = R - t / 2
    psi0 = math.acos(d / Rm)
    area = 2 * math.pi * Rm * Rm * (1 - math.cos(psi0))
    rim = 2 * math.pi * Rm * math.sin(psi0)
    return {"area": area, "rim": rim, "meridian": Rm * psi0, "n": rim / 0.15}


def test_s8_3_and_its_errata_are_untouched():
    v = J(PKG / "07_FROZEN_VERIFICATION.json")
    assert v["s8_3_manifest_sha256"] == DR.verify_frozen(S83 / "16_S8_3_FREEZE_MANIFEST.json", ROOT)["manifest_sha256"]
    assert v["s8_3_errata_sha256"] == {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((S83 / "errata").glob("0*"))}
    m = J(PKG / "09_S8_3A_FREEZE_MANIFEST.json")
    assert m["state"] == "DATED_CORRECTION_LAYER" and m["references_read"] == []
    DR.verify_frozen(PKG / "09_S8_3A_FREEZE_MANIFEST.json", ROOT)


def test_scenario_a_reproduces_the_frozen_quantity_exactly(s):
    fp = _first_principles()
    a = s["scenarios"]["A"]
    assert a["meridional_m_per_dome"] == a["hoop_m_per_dome"] == pytest.approx(fp["area"] / 0.15, abs=1e-8)
    assert a["meridional_m_per_dome"] == pytest.approx(169.343804, abs=1e-6)
    assert a["kg_two_domes"] == pytest.approx(602.111304, abs=1e-6) == J(S83 / "15_S8_3_SUMMARY.json")["released"]["reinforcement_kg"]
    frozen = {r["ITEM_ID"]: float(r["EQUIVALENT_LENGTH_M"]) for r in rows("08_REBAR_QTO_REGISTER.csv", S83)
              if r["RELEASED"] == "True"}
    assert all(v == pytest.approx(a["meridional_m_per_dome"], abs=1e-9) for v in frozen.values()) and len(frozen) == 4


def test_scenario_b_from_first_principles(s):
    fp = _first_principles()
    b = s["scenarios"]["B"]
    assert s["mid_surface"]["rim_circumference_m"] == pytest.approx(fp["rim"], abs=1e-9)
    assert s["meridian_count_unrounded"] == pytest.approx(fp["n"], abs=1e-6)
    assert b["meridional_m_per_dome"] == pytest.approx(fp["n"] * fp["meridian"], abs=1e-8)
    assert b["hoop_m_per_dome"] == pytest.approx(fp["area"] / 0.15, abs=1e-8)
    assert b["kg_two_domes"] == pytest.approx(2 * (fp["n"] * fp["meridian"] + fp["area"] / 0.15) * KG12, abs=1e-6)
    assert b["kg_two_domes"] == pytest.approx(798.915, abs=0.001)


def test_nothing_new_is_released(s):
    sc = {r["SCENARIO"]: r for r in rows("02_SCENARIOS.csv")}
    assert set(sc) == {"A", "B", "B-FAB", "C"}
    assert sc["A"]["LANE"].startswith("PROJECT_BASIS_QTO") and sc["A"]["AUTHORITY"] == "IDEALIZED_SURFACE_DENSITY_QTO"
    assert all(sc[k]["LANE"] == "SENSITIVITY_ONLY" for k in ("B", "B-FAB", "C"))
    assert sc["C"]["AUTHORITY"].startswith("TEST_ASSUMPTION")
    assert float(sc["A"]["KG_TWO_DOMES"]) < float(sc["C"]["KG_TWO_DOMES"]) < float(sc["B"]["KG_TWO_DOMES"])
    assert s["frozen_quantity_changed"] is False


def test_status_change_is_a_confidence_correction_only(s):
    st = rows("04_STATUS_CHANGES.csv")
    assert len(st) == 5
    for r in st:
        assert r["S8_3_KG"] == r["S8_3A_KG"] and r["S8_3_LANE"] == r["S8_3A_LANE"] == "PROJECT_BASIS_QTO"
        assert (r["QUANTITY_CONFIDENCE"], r["FABRICATION_GRADE"], r["LOWER_BOUND_CLAIM"], r["BBS"]) == \
            ("IDEALIZED_SURFACE_DENSITY_QTO", "UNRESOLVED", "NONE", "NOT_VALIDATED")
    assert {r["PHYSICAL_DISTRIBUTION"] for r in st if "MERIDIONAL" in r["ITEM_ID"]} == {"NOT_ESTABLISHED"}
    assert (s["quantity_confidence"], s["lower_bound_claim"], s["bbs"]) == ("IDEALIZED_SURFACE_DENSITY_QTO", "NONE",
                                                                           "NOT_VALIDATED")


def test_the_drawing_is_a_specification_not_a_layout(s):
    ev = {r["ID"]: r for r in rows("01_SOURCE_EVIDENCE.csv")}
    assert "NOT stated" in ev["SE-03"]["CONCLUSION"] and "crosses the crown: True" in ev["SE-05"]["OBSERVED"]
    assert "none drawn" in ev["SE-06"]["OBSERVED"] and "[20, 20]" in ev["SE-07"]["OBSERVED"]
    assert s["drawing"]["bar_crosses_crown"] is True and s["drawing"]["dot_step_spread"] < 1e-3
    f = {r["ITEM"]: r for r in rows("03_PHYSICAL_LAYOUT_FEASIBILITY.csv")}
    touch = float(next(r["VALUE"] for k, r in f.items() if k.startswith("fixed Ø12 meridians touch")))
    assert touch == pytest.approx(0.012 * s["meridian_count_unrounded"] / (2 * math.pi), abs=1e-9)


def test_no_bar_object_is_counted_twice(s):
    rec = rows("05_BAR_OBJECT_RECONCILIATION.csv")
    assert not [r for r in rec if r["STATE"] == "NEW_OBJECT"] and s["new_bar_objects"] == 0
    e02 = [r for r in rec if r["HANDLE"] in ("1A4D", "1A4F")]
    assert len(e02) == 2 and all(r["STATE"] == "ALREADY_RECORDED" and "S8.3-E02" in r["MAPS_TO"] for r in e02)
    assert any(r["STATE"].startswith("MISSING_INFORMATION") and r["ZONE"] == "SHELL_CROWN" for r in rec)
    assert all(r["QUANTITY_EFFECT"] != "" for r in rec)


def test_missing_evidence_is_listed():
    m = {r["ID"] for r in rows("06_MISSING_EVIDENCE.csv")}
    assert m == {f"ME-0{i}" for i in range(1, 8)}


def test_builder_and_engine_are_blind_and_declared():
    for src in (PKG / "build_s8_3a.py", ROOT / "engine/source/shell_line_distribution.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ",
                    "U-C4N", "kg/m3", "benchmark", "post_freeze", "control_plane", "CONTRACTOR"):
            assert tok not in text, (src.name, tok)
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_dome_mesh_s8_3a/build_s8_3a.py" in RP.ACCURATE_BUILDERS


@pytest.mark.skipif(not ST.exists(), reason="private client drawings not restored in data/inputs/by_sha256")
def test_rebuild_is_byte_identical():
    m = J(PKG / "09_S8_3A_FREEZE_MANIFEST.json")
    names = list(m["outputs"]) + ["09_S8_3A_FREEZE_MANIFEST.json"]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_3a.py")], check=True, cwd=ROOT, capture_output=True)
    assert before == {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
