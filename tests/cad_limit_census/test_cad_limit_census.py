"""T-025a: CAD LIMIT census (engine/source/cad_limit_census.py) on hand-made drawings with HAND-COUNTED truth.

Hand truth (counts are what a person counts on the drawing; caps are the frozen comparisons, all strict ">"):
    LAYER-ALPHA    4001 lines           -> over the 4000 rectangle cap only
    LAYER-BRAVO    3999 lines           -> nothing
    LAYER-CHARLIE  6001 lines in a block inserted rotated 37 deg and mirrored (xscale -1)
                                        -> 4000 rectangle cap, 6000 edge-face cap, 6000 unmarked-network cap,
                                           6000 strap-face cap (role UNKNOWN; no rectangles -> outline share 0)
    the same drawing in mm (INSUNITS 4) and in m (INSUNITS 6) -> the same records (counts carry no unit)
    20001 lines 0.5 drawing units long: in mm (0.5 mm <= 1 mm) not counted by the line-ring cap, in m (0.5 m) counted;
    unit unknown -> a UNIT_UNKNOWN record with the upper bound 20001, never a silent pass.
The census is tied to the frozen search itself: member_detection.candidate_rects finds a drawn rectangle on a layer
of exactly 4000 lines and not on one of 4001, and only the 4001 layer gets a LIMIT record.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from engine.source import cad_limit_census as CL
from engine.source import member_detection as MD

ROOT = Path(__file__).resolve().parents[2]


def _hlines(layer, n, length, step, y0=0.0, kind="LINE", prefix=None):
    """n horizontal segments (no two form a rectangle), as intake segment records."""
    p = prefix or layer
    return [{"id": f"{p}:{k}", "layer": layer, "a": (0.0, y0 + k * step), "b": (length, y0 + k * step), "kind": kind}
            for k in range(n)]


def _caps(recs, layer):
    return [r["cap_id"] for r in recs if r["layer"] == layer]


ALL_6000 = ["MD_CANDIDATE_RECTS_SEGMENTS", "MD_EDGE_LAYER_FACES", "MD_STRAP_LAYER_FACES", "GR_UNMARKED_NETWORK_FACES"]


# ------------------------------------------------------------------ the cap table matches the frozen source
@pytest.mark.parametrize("cap", CL.CAPS, ids=lambda c: c["cap_id"])
def test_cap_line_points_at_the_frozen_comparison(cap):
    src = (ROOT / cap["module"]).read_text(encoding="utf-8").splitlines()
    line = src[cap["line"] - 1]
    if cap["cap_id"] == "ARCH_V27_RECT_SEGMENTS":
        assert "MAX_RECT_SEGMENTS" in line and ">" in line
        assert "MAX_RECT_SEGMENTS = 20000" in src[48]
    else:
        assert str(cap["cap"]) in line and "len(" in line


# ------------------------------------------------------------------ hand synthetic DXF, mm and m, rotated + mirrored
def _dxf(tmp_path, insunits, per_m):
    ezdxf = pytest.importorskip("ezdxf")
    from tools import urban_intake as UI
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = insunits
    msp = doc.modelspace()
    L, step = 0.2 * per_m, 0.05 * per_m
    for lay, n, x0 in (("LAYER-ALPHA", 4001, 0.0), ("LAYER-BRAVO", 3999, 1.0 * per_m)):
        for k in range(n):
            msp.add_line((x0, k * step), (x0 + L, k * step), dxfattribs={"layer": lay})
    blk = doc.blocks.new("FILL6001")
    for k in range(6001):
        blk.add_line((0, k * step), (L, k * step), dxfattribs={"layer": "LAYER-CHARLIE"})
    msp.add_blockref("FILL6001", (5.0 * per_m, 0), dxfattribs={"layer": "LAYER-CHARLIE", "rotation": 37.0,
                                                                 "xscale": -1.0})
    p = tmp_path / f"limits_{insunits}.dxf"
    doc.saveas(p)
    return UI.read(p)


@pytest.mark.parametrize("insunits,per_m", [(4, 1000.0), (6, 1.0)], ids=["mm", "m"])
def test_synthetic_dxf_lists_exactly_the_over_cap_layers(tmp_path, insunits, per_m):
    intake = _dxf(tmp_path, insunits, per_m)
    counts = {}
    for s in intake["segments"]:
        counts[s["layer"]] = counts.get(s["layer"], 0) + 1
    assert counts == {"LAYER-ALPHA": 4001, "LAYER-BRAVO": 3999, "LAYER-CHARLIE": 6001}    # intake drops nothing
    recs = CL.census(intake, intake["unit_m"], sheet="S1")
    assert _caps(recs, "LAYER-ALPHA") == ["MD_CANDIDATE_RECTS_SEGMENTS"]
    assert _caps(recs, "LAYER-BRAVO") == []
    assert sorted(_caps(recs, "LAYER-CHARLIE")) == sorted(ALL_6000)
    assert {r["layer"] for r in recs} == {"LAYER-ALPHA", "LAYER-CHARLIE"}
    for r in recs:
        assert r["record"] == "LIMIT" and r["state"] == "HELD" and r["reason_code"] == "CAD_LAYER_OVER_CAP"
        assert r["count"] == counts[r["layer"]] and r["count"] > r["cap"] and r["sheet"] == "S1"
        assert r["module"].startswith("engine/source/") and isinstance(r["line"], int)


def test_mm_and_m_give_the_same_records(tmp_path):
    a = CL.census(_dxf(tmp_path, 4, 1000.0), 0.001)
    b = CL.census(_dxf(tmp_path, 6, 1.0), 1.0)
    key = lambda rs: [(r["layer"], r["cap_id"], r["count"]) for r in rs]    # noqa: E731
    assert key(a) == key(b) and key(a)


# ------------------------------------------------------------------ boundaries and roles (hand counts)
def test_cap_is_strict_greater_than():
    ents = {"segments": _hlines("LAYER-A", 4000, 1.0, 1.0) + _hlines("LAYER-B", 6000, 1.0, 1.0)}
    assert _caps(CL.census(ents, 1.0), "LAYER-A") == []
    assert _caps(CL.census(ents, 1.0), "LAYER-B") == ["MD_CANDIDATE_RECTS_SEGMENTS"]


def test_roles_follow_each_search():
    ents = {"segments": _hlines("S-FOOTING-1", 6001, 1.0, 1.0) + _hlines("S-COLUMN-1", 6001, 1.0, 1.0) +
            _hlines("DIM-1", 20001, 1.0, 1.0)}
    recs = CL.census(ents, 1.0)
    # a footing layer is admitted by the strap search only; a column layer by neither face search
    assert _caps(recs, "S-FOOTING-1") == ["MD_CANDIDATE_RECTS_SEGMENTS", "MD_STRAP_LAYER_FACES"]
    assert _caps(recs, "S-COLUMN-1") == ["MD_CANDIDATE_RECTS_SEGMENTS"]
    # an annotation layer is skipped by role by every member search; only the arch rectangle cap counts any role
    assert _caps(recs, "DIM-1") == ["ARCH_V27_RECT_SEGMENTS"]


def test_outline_layer_is_skipped_before_the_face_cap():
    """A layer whose segments are mostly sides of closed rectangles is refused by outline share (a named filter), not
    by the 6000 cap, so the two face caps do not list it; the rectangle and strap caps still do."""
    segs, rects = [], []
    for k in range(1501):                                     # 1501 squares = 6004 sides, all outlines
        x = 3.0 * k
        src = f"SQ{k}"
        pts = [(x, 0.0), (x + 1, 0.0), (x + 1, 1.0), (x, 1.0)]
        for j in range(4):
            segs.append({"id": f"{src}:{j}", "layer": "LAYER-OUTLINE", "a": pts[j], "b": pts[(j + 1) % 4],
                         "kind": "LWPOLYLINE"})
        rects.append({"layer": "LAYER-OUTLINE", "source": src, "box": (x, 0.0, x + 1, 1.0)})
    ents = {"segments": segs, "rects": rects}
    assert MD.outline_share({"segments": segs, "rects": rects}, "LAYER-OUTLINE") == 1.0
    assert _caps(CL.census(ents, 1.0), "LAYER-OUTLINE") == ["MD_CANDIDATE_RECTS_SEGMENTS", "MD_STRAP_LAYER_FACES"]


def test_line_ring_cap_counts_lines_over_1_mm_by_unit():
    ents = {"segments": _hlines("LAYER-E", 20001, 0.5, 1.0) + _hlines("LAYER-P", 20001, 5.0, 1.0, kind="LWPOLYLINE")}
    mm = CL.census(ents, 0.001)                               # 0.5 mm lines: not over 1 mm -> not counted
    m = CL.census(ents, 1.0)                                  # 0.5 m lines: counted
    assert "MD_LINE_RINGS_LINES" not in _caps(mm, "LAYER-E")
    assert "MD_LINE_RINGS_LINES" in _caps(m, "LAYER-E")
    assert next(r["count"] for r in m if r["cap_id"] == "MD_LINE_RINGS_LINES") == 20001
    # polyline spans are not LINEs: line_rings never sees them (other caps still list the layer)
    assert "MD_LINE_RINGS_LINES" not in _caps(m, "LAYER-P")
    assert "ARCH_V27_RECT_SEGMENTS" in _caps(m, "LAYER-P")


@pytest.mark.parametrize("unit", [None, 0, -1.0, float("nan"), True])
def test_unknown_unit_is_held_with_an_upper_bound_never_zero(unit):
    ents = {"segments": _hlines("LAYER-E", 20001, 0.5, 1.0)}
    recs = [r for r in CL.census(ents, unit) if r["cap_id"] == "MD_LINE_RINGS_LINES"]
    assert len(recs) == 1
    r = recs[0]
    assert r["count"] is None and r["count_upper_bound"] == 20001
    assert r["reason_code"] == "CAD_LAYER_OVER_CAP_UNIT_UNKNOWN" and r["state"] == "HELD"


def test_unknown_unit_under_the_upper_bound_lists_nothing():
    assert CL.census({"segments": _hlines("LAYER-E", 3000, 0.5, 1.0)}, None) == []


# ------------------------------------------------------------------ tied to the frozen search's own behaviour
def _rect_layer(layer, filler):
    sq = [((10.0, 10.0), (11.0, 10.0)), ((11.0, 10.0), (11.0, 11.0)), ((11.0, 11.0), (10.0, 11.0)),
          ((10.0, 11.0), (10.0, 10.0))]
    segs = [{"id": f"{layer}R:{k}", "layer": layer, "a": a, "b": b, "kind": "LINE"} for k, (a, b) in enumerate(sq)]
    return segs + _hlines(layer, filler, 0.5, 0.01, y0=20.0, prefix=f"{layer}F")


def test_census_agrees_with_frozen_candidate_rects():
    ents = {"segments": _rect_layer("LAYER-OK", 3996) + _rect_layer("LAYER-BIG", 3997), "rects": [], "options": {}}
    found = {r["layer"] for r in MD.candidate_rects(ents, 1.0)}
    assert "LAYER-OK" in found                                # 4000 segments: searched, the square is found
    assert "LAYER-BIG" not in found                           # 4001 segments: skipped, the square vanishes
    recs = CL.census(ents, 1.0)
    assert [(r["layer"], r["count"]) for r in recs if r["cap_id"] == "MD_CANDIDATE_RECTS_SEGMENTS"] == \
        [("LAYER-BIG", 4001)]


# ------------------------------------------------------------------ empty and missing data
@pytest.mark.parametrize("ents", [None, {}, {"segments": []}, {"segments": None},
                                  {"arcs": [{"id": "a", "layer": "X"}], "texts": []}])
def test_empty_drawing_gives_empty_list(ents):
    assert CL.census(ents, 0.001) == []
    assert CL.census(ents, None) == []


def test_summary_counts():
    ents = {"segments": _hlines("LAYER-A", 4001, 1.0, 1.0) + _hlines("LAYER-E", 20001, 0.5, 1.0)}
    s = CL.summary(CL.census(ents, None))
    assert s["layers"] == ["LAYER-A", "LAYER-E"]
    assert s["by_reason"] == {"CAD_LAYER_OVER_CAP": 6, "CAD_LAYER_OVER_CAP_UNIT_UNKNOWN": 1}
    assert s["limit_records"] == 7
    assert CL.summary([]) == {"policy": CL.POLICY_ID, "limit_records": 0, "by_cap": {}, "by_reason": {}, "layers": []}


def test_records_are_sorted_and_deterministic():
    ents = {"segments": _hlines("Z-LAYER", 4001, 1.0, 1.0) + _hlines("A-LAYER", 4001, 1.0, 1.0)}
    a, b = CL.census(ents, 1.0, sheet="S2"), CL.census(dict(ents), 1.0, sheet="S2")
    assert a == b and [r["layer"] for r in a] == ["A-LAYER", "Z-LAYER"]
    assert all(math.isfinite(r["count"]) for r in a)
