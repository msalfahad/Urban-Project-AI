"""T-507: the development-villa inputs (research/agents_t507/t507_inputs.py) restate the merged T-494 zones from the
sha-pinned rows file only (no drawing); the engine recomputes the component rows and they equal the merged rows; the
figures the Checker re-measured are what the lines carry. Adverse: the rows file changed (sha), a merged row edited."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t507"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t507_inputs as I  # noqa: E402
from engine.source import arch_v3058 as A  # noqa: E402


def test_inputs_validate_and_recompute_the_merged_rows():
    d = A.load_inputs(I.build("P"), "P")
    z = {x["zone_id"]: x for x in d["_zones"]}
    assert sorted(z) == ["POOLCOURT-550", "POOLCOURT-550-LEDGE"]
    open_sky = A._parts(z["POOLCOURT-550"])
    assert [(p[0], p[1], p[2], p[3], p[4]) for p in open_sky] == [
        ("FIN.WP.ROOF", "wp_membrane", "SOURCE_DERIVED", 4.906867, None),
        ("FIN.WP.ROOF_UPTURN", "wp_upturn", "SOURCE_DERIVED", 5.193544, None),
        ("FIN.WP.ROOF_UPTURN", "wp_upturn window_face", "BOUNDED_EXPOSURE", None, 0.500002)]
    ledge = A._parts(z["POOLCOURT-550-LEDGE"])
    assert [(p[0], p[1], p[2], p[4]) for p in ledge] == [
        ("FIN.WP.ROOF", "wp_membrane", "BOUNDED_EXPOSURE", 0.639573),
        ("FIN.WP.ROOF_UPTURN", "wp_upturn", "BOUNDED_EXPOSURE", 3.528277)]
    b = {(x["what"], x["bound"]) for x in A._beside_items(z["POOLCOURT-550"])}
    assert b == {("SLAB_EDGE_TERMINATION", 6.869158), ("VOID_EDGE_TERMINATION", 4.321407), ("DRAINAGE_FALLS", None)}
    assert [(x["what"], x["bound"]) for x in A._beside_items(z["POOLCOURT-550-LEDGE"])] == [
        ("VOID_EDGE_TERMINATION", 2.817214)]
    assert {o: d["_overlap"][o]["overlap_m2"] for o in d["_overlap"]} == {v: 0.0 for v in I.ROOF_LINES.values()}


def test_upturn_m2_matches_the_checker_figure():
    d = A.load_inputs(I.build("P"), "P")
    rows = [r for r in d["_zones"][0]["_rows"] if r["component"] == "UPTURN" and r["status"] == "MEASURED"]
    assert round(sum(r["qty"] for r in rows), 6) == 1.03871 and round(sum(r["length_lm"] for r in rows), 6) == 5.193544


def test_adverse_rows_file_changed(monkeypatch):
    monkeypatch.setattr(I, "ROWS_SHA", "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        I.build("P")


def test_adverse_merged_row_edited():
    doc = I.build("P")
    bad = copy.deepcopy(doc)
    bad["zones"][0]["expected_rows"][0]["qty"] = 4.95
    with pytest.raises(A.InputsError, match="stale"):
        A.load_inputs(bad, "P")
