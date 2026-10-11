"""M4 slab and blinding corrections on hand-made sheet records (mm drawing), hand-derived truth.

Slab faces (generic_route._slab_m4):
    panel 4.0 x 3.0 = 12.00 m2, untagged, the sheet's one printed tag 0.18 extended to it (SHEET_UNIFORM)
      a beam band 4.0 x 0.10 inside it and a 0.30 column in its corner: 0.40 + 0.09 = 0.49 m2 owned by the members
      -> 11.51 m2 x the project default 0.16 (PROJECT_DEFAULT_FIRST) = 1.8416 m3; SHEET_UNIFORM_FIRST keeps 0.18
    a tagged panel keeps its own tag; a ground slab never takes the suspended-slab default
Blinding (generic_route._blinding_overlap): footings 1.5 x 1.5 at (0, 0) and (6000, 0) and (0, 6000); the ground-beam
plan drawn 50 m to the left, its columns at the footing centres; a 0.30 band between the first two columns
    p = 0.10: strip y 500 - 1000 (0.5) over footing blinding x -100 - 1600 and 5900 - 7600 -> 2 x 0.7 x 0.5 = 0.70
    p = 0.00: 2 x 0.6 x 0.3 = 0.36;  p = 0.15: 2 x 0.75 x 0.6 = 0.90
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.source import generic_route as GR               # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _conv(**over):
    gen = json.loads((ROOT / "engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json").read_text())
    prof = {"profile": "T", "conventions": [
        {"id": "SLAB_PROJECT_DEFAULT_THICKNESS_M", "title": "d", "kind": "number", "unit": "m", "base": 0.16,
         "low": 0.16, "high": 0.16, "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}]}
    return GR.merge_conventions(gen, prof, over)


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _sheet(t_basis="SHEET_UNIFORM", t=0.18):
    face = {"face_id": "F1", "class": "PANEL", "polygon": _rect(0, 0, 4000, 3000), "area_m2": 12.0, "t_m": t,
            "t_basis": t_basis, "volume_m3": 12.0 * t}
    rec = {"bands": [{"kind": "STRAIGHT", "polygon": _rect(0, 1000, 4000, 1100)}],
           "column_boxes": [(0, 0, 300, 300)]}
    return {"faces": [face]}, rec


def test_member_overlap_deducted_and_project_default_first():
    slab, rec = _sheet()
    risk = []
    GR._slab_m4(slab, rec, 0.001, _conv(), False, risk, "SH1")
    f = slab["faces"][0]
    assert f["member_overlap_m2"] == pytest.approx(0.49) and f["area_gross_m2"] == 12.0
    assert f["area_m2"] == pytest.approx(11.51) and f["t_m"] == 0.16 and f["t_basis"] == "PROJECT_DEFAULT"
    assert f["t_sheet_uniform_m"] == 0.18 and f["volume_m3"] == pytest.approx(11.51 * 0.16)
    assert [r["KIND"] for r in risk] == ["SLAB_FACE_MEMBER_OVERLAP_DEDUCTED",
                                         "SLAB_THICKNESS_SHEET_TAG_VS_PROJECT_DEFAULT"]
    GR._slab_m4(slab, rec, 0.001, _conv(), False, risk, "SH1")          # once only
    assert f["area_m2"] == pytest.approx(11.51) and len(risk) == 2


def test_sheet_uniform_first_tagged_panel_and_ground_slab():
    slab, rec = _sheet()
    GR._slab_m4(slab, rec, 0.001, _conv(SLAB_UNTAGGED_THICKNESS_SOURCE="SHEET_UNIFORM_FIRST"), False, [], "SH1")
    assert slab["faces"][0]["t_m"] == 0.18 and slab["faces"][0]["volume_m3"] == pytest.approx(11.51 * 0.18)
    slab, rec = _sheet(t_basis="TAG", t=0.18)                          # a panel that prints its own thickness
    GR._slab_m4(slab, rec, 0.001, _conv(), False, [], "SH1")
    assert slab["faces"][0]["t_m"] == 0.18
    slab, rec = _sheet()
    GR._slab_m4(slab, rec, 0.001, _conv(), True, [], "SH1")            # ground slab: no suspended-slab default
    assert slab["faces"][0]["t_m"] == 0.18 and slab["faces"][0]["area_m2"] == pytest.approx(11.51)


def _D(gb_cols):
    boxes = [(0, 0, 1500, 1500), (6000, 0, 7500, 1500), (0, 6000, 1500, 7500)]
    return {"unit_m": 0.001, "sheets": {
        "SH1": {"sheet": {"role": "FOUNDATION_PLAN", "sheet_id": "SH1"}, "footings": [{"box": b} for b in boxes]},
        "SH2": {"sheet": {"role": "GROUND_BEAM_PLAN", "sheet_id": "SH2"}, "column_boxes": gb_cols}}}


X = -50000.0
COLS = [(X + 600, 600, X + 900, 900), (X + 6600, 600, X + 6900, 900), (X + 600, 6600, X + 900, 6900)]
BAND = {"kind": "STRAIGHT", "u": (1.0, 0.0), "lo_off": 600.0, "hi_off": 900.0, "t0": X + 900, "t1": X + 6600}


def test_blinding_overlap_on_footing_blinding():
    r = GR._blinding_overlap(_D(COLS), [(1.71, 5.7, BAND, "SH2")], (0.0, 0.10, 0.15))
    assert r["state"] == "REGISTERED" and r["matched"] == 3 and r["strips_over_footings"] == 1
    assert r["area_m2"] == pytest.approx((0.36, 0.70, 0.90))
    far = dict(BAND, lo_off=3000.0, hi_off=3300.0)                     # a band clear of every footing
    assert GR._blinding_overlap(_D(COLS), [(1.7, 5.7, far, "SH2")], (0.10,))["area_m2"] == pytest.approx((0.0,))


def test_blinding_overlap_needs_registration():
    assert GR._blinding_overlap(_D([]), [(1.7, 5.7, BAND, "SH2")], (0.1,))["state"] == "NO_COMMON_MEMBERS"
    two = [(X + 600, 600, X + 900, 900), (X + 600 + 30000, 600, X + 900 + 30000, 900)]
    r = GR._blinding_overlap(_D(two), [(1.7, 5.7, BAND, "SH2")], (0.1,))
    assert r["state"] == "NOT_REGISTERED" and r["area_m2"] == (0.0, 0.0, 0.0)
