"""Phase B2A - frozen Alsenan registers (built twice from the committed code, byte-identical) and the post-freeze
benchmark evaluation. These tests read the frozen files only."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tests/alsenan/registers_b2a"
EVAL = ROOT / "tests/alsenan/registers_b2a_eval/BENCHMARK_EVALUATION.json"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="B2A registers not frozen yet")


def R(n):
    return json.loads((REG / f"{n}.json").read_text())


def test_freeze_is_before_the_benchmark_and_qa_passes():
    fz = R("ALSENAN_PHASE_B2A_FREEZE")
    assert fz["BENCHMARK_OPENED"] is False
    assert R("QA_GATES")["state"] == "PASS" and all(v == 0 for v in R("QA_GATES")["gates"].values())
    assert fz["xlsx"]["rewrite_identical"] and fz["xlsx"]["readback"] == "PASS"


def test_register_digests_match_the_freeze():
    fz = R("ALSENAN_PHASE_B2A_FREEZE")
    for n, d in fz["register_digests"].items():
        if n == "ALSENAN_PHASE_B2A_FREEZE":
            continue
        o = R(n)
        if n == "QORTUBA_REGRESSION":
            continue                                    # written by the regression step after the build
        assert hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest() == d, n


def test_b2a_engines_unchanged_since_the_latest_freeze():
    """B2A.1 legitimately patched concrete_model (stair) and curved_opening (names): the engines are pinned to the newest
    freeze (B2A.1), which pins this B2A freeze by digest."""
    latest = ROOT / "tests/alsenan/registers_b2a1/ALSENAN_PHASE_B2A1_REGISTER_FREEZE.json"
    fz = json.loads(latest.read_text()) if latest.exists() else R("ALSENAN_PHASE_B2A_FREEZE")
    if latest.exists():
        assert fz["parent_b2a_freeze"]["sha256"] == hashlib.sha256((REG / "ALSENAN_PHASE_B2A_FREEZE.json").read_bytes()).hexdigest()
    for m, h in fz["b2a_engine_sha256"].items():
        assert hashlib.sha256((ROOT / "engine/source" / f"{m}.py").read_bytes()).hexdigest() == h, m


def test_b1_and_cb1_are_different_sections():
    lib = R("BEAM_BINDING_REGISTER")["libraries"]
    assert (lib["SIMPLE"]["B1"]["B_cm"], lib["SIMPLE"]["B1"]["D_cm"]) == (20.0, 40.0)
    assert (lib["CONTINUOUS"]["CB1"]["B_cm"], lib["CONTINUOUS"]["CB1"]["D_cm"]) == (35, 75)
    assert R("BEAM_BINDING_REGISTER")["namespace_audit"]["state"] == "PASS"


def test_salon_beam_is_cb1_and_height_stays_owner_derived():
    s = R("OPENING_AUTHORITY_REGISTER")["salon"]
    assert s["beam_above"]["type"] == "CB1" and s["beam_above"]["namespace"] == "CONTINUOUS"
    assert s["structural_soffit_upper_bound_m"] == pytest.approx(3.75)
    assert s["height_m"] == 3.65 and s["state"] == "OWNER_DERIVED_REVIEW_REQUIRED"


def test_column_heights_follow_their_own_member():
    rows = [r for r in R("STRUCTURAL_VERTICAL_INTERVAL_REGISTER")["rows"] if r.get("height_m") is not None]
    assert rows
    for r in rows:
        assert r["height_m"] == pytest.approx(r["interval_m"] - r["controlling_depth_m"])
        assert r["state"] in ("PROVEN", "PROVEN_UNBOUND_DOMINATED", "SLAB_SOFFIT")
    gf = {r["controlling_member"]: r["height_m"] for r in rows if r["floor"] == "GF"}
    assert gf.get("CB1") == pytest.approx(3.75) and gf.get("B2") == pytest.approx(4.10)
    assert R("STRUCTURAL_VERTICAL_INTERVAL_REGISTER")["neck"]["state"] == "BLOCKED_HEIGHT"


def test_blocked_columns_have_no_height():
    for r in R("STRUCTURAL_VERTICAL_INTERVAL_REGISTER")["rows"]:
        if "BLOCKED" in r["state"] or r["state"].startswith("NOT_"):
            assert r.get("height_m") is None and r.get("volume_m3") is None


def test_slabs_and_stairs():
    sl = R("SLAB_REGION_REGISTER")["sheets"]
    for fl in ("GF", "1F", "2F"):
        s = sl[fl]
        assert s["closure"] == "CLOSED" and s["bands_outside_plate"] == []
        assert s["net_plate_area_m2"] == pytest.approx(s["gross_outline_area_m2"] - s["openings_area_m2"])
        assert s["volume_m3"] is not None and len(s["sheet_thickness_tags_cm"]) == 1
    assert R("STAIR_REGISTER")["result"]["state"] == "BLOCKED_INPUT_MISSING"


def test_physical_model_partition_and_gross_view_separate():
    for fl, s in R("PHYSICAL_CONCRETE_REGISTER")["storeys"].items():
        m = s["model"]
        assert m["computed_total_m3"] == pytest.approx(sum(c["volume_m3"] for c in m["components"]))
        assert "GROSS" not in m["by_component_m3"]


def test_openings_never_published_as_window():
    rows = R("OPENING_AUTHORITY_REGISTER")["rows"]
    fn = {r["id"]: r["function"] for r in rows}
    assert "WINDOW" not in fn.values()
    assert fn["GF-W03"] == "DOOR" and fn["GF-W13"] == "DOOR" and fn["GF-W14"] == "GLAZED_OPENING_FUNCTION_UNKNOWN"


def test_curved_bases_and_inner_method():
    for r in R("CURVED_OPENING_REGISTER")["rows"]:
        b = r["bases_m"]
        assert b["INNER"] < b["CENTRE"] < b["OUTER"] and r["commercial_m"] == b["INNER"] and r["commercial_basis"] == "INNER"


def test_mbr_certified_with_owner_fact_and_f_f10_still_blocked():
    m = R("WALL_HEIGHT_REGISTER")["mbr"]
    assert m["state"] == "CERTIFIED_WITH_OWNER_FACT" and m["floor_area_m2"] == m["candidate_area_m2"]
    items = {r["item"]: r for r in R("PHYSICAL_CONCRETE_REGISTER")["explicit_items"]}
    assert len(items["FOOTINGS"]["blocked"]) == 2
    assert R("OWNER_FACT_REGISTER")["no_fact"]["F_F10"].startswith("no owner fact")


def test_a3_preserved_and_qortuba_regression():
    assert R("A3_PRESERVATION")["state"] == "PRESERVED"
    assert R("QORTUBA_REGRESSION")["state"] in ("UNCHANGED", "PROVENANCE_ONLY")


def test_frozen_a3_and_b1_registers_untouched():
    for d, c in (("tests/alsenan/registers_a3", "9aa2741"), ("tests/alsenan/registers_b1", "f820263")):
        out = subprocess.run(["git", "-C", str(ROOT), "diff", "--stat", c, "--", d], capture_output=True, text=True)
        assert out.returncode == 0 and out.stdout.strip() == "", out.stdout


def test_benchmark_evaluation_ran_after_the_freeze():
    e = json.loads(EVAL.read_text())
    assert e["run"] == "AFTER_FREEZE" and e["b2a_freeze_benchmark_opened"] is False
    assert e["b2a_freeze_sha256"] == hashlib.sha256((REG / "ALSENAN_PHASE_B2A_FREEZE.json").read_bytes()).hexdigest()
