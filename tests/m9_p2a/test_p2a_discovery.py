"""Phase 2A P2-05 (ARCH_TAKEOFF_V2.1): fills read at every depth (nested blocks, MINSERT cells, layer-0 inheritance,
SOLID / TRACE) reach the plan as column evidence; what V2.1 still cannot read stays a REVIEW flag. The synthetic
variants are the S6 consultant-drawing variants (tests/m9_s6/conftest.py); V2 behaviour is unchanged."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("s6_variants", ROOT / "tests/m9_s6/conftest.py")
S6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S6)

RECOVERED = ("nested_2", "nested_3", "col_minsert", "col_layer0", "col_solid")
STILL_FLAGGED = ("col_solid_only", "col_exploded", "col_two_only")


def _run(tmp_path, variant, method):
    from tools import urban_boq_m9 as M9
    p = tmp_path / f"{variant}.dxf"
    S6.VARIANTS[variant](p)
    try:
        room, arch, _E = M9.arch_compute(str(p), method=method)
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    st = arch["discovery"]["stages"]["6_geometry_readiness"]
    gf = next(c for c in st["column_evidence"] if c["floor"] == "GF")
    codes = {f["code"] for f in st["findings"]}
    rooms = sorted((r["floor"], r["class"], "+".join(r.get("codes") or []), round(r["area_m2"] or 0, 6))
                   for r in arch["rooms"])
    return gf, codes, rooms, arch


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("base"), "base", "ARCH_TAKEOFF_V2.1")


@pytest.mark.parametrize("variant", RECOVERED)
def test_v2_1_reads_the_fills_and_measures_the_columns_like_the_base_drawing(tmp_path, base, variant):
    gf0, _c0, rooms0, _a0 = base
    gf, codes, rooms, arch = _run(tmp_path, variant, "ARCH_TAKEOFF_V2.1")
    assert gf["measured_columns"] == gf0["measured_columns"] == 3 and gf["unmeasured"] == 0
    assert not codes & {"COLUMN_EVIDENCE_NOT_MEASURED", "FILLS_NOT_READ_IN_PLAN"}
    assert rooms == rooms0                                       # the columns are deducted as in the base drawing
    assert arch["run"]["v2_1"]["fills_merged"]["fills"] >= 3


@pytest.mark.parametrize("variant", RECOVERED)
def test_v2_keeps_its_review_flag_for_the_same_variants(tmp_path, variant):
    gf, codes, _rooms, _arch = _run(tmp_path, variant, "ARCH_TAKEOFF_V2")
    assert gf["measured_columns"] == 0 and "COLUMN_EVIDENCE_NOT_MEASURED" in codes


@pytest.mark.parametrize("variant", STILL_FLAGGED)
def test_what_v2_1_still_cannot_read_stays_a_review_flag(tmp_path, variant):
    """no outline (SOLID only), an exploded outline, or too few columns to class the layer: never silently dropped."""
    gf, codes, _rooms, _arch = _run(tmp_path, variant, "ARCH_TAKEOFF_V2.1")
    assert gf["unmeasured"] > 0 and "COLUMN_EVIDENCE_NOT_MEASURED" in codes
