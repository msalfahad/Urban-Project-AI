"""T-601 R-T601-1 doorless opening jamb census: a non-Alsenan drawn fixture (arch, passage, door, framed lift opening,
glazed window; plain, rotated and mirrored) read by the T-601 extractor, the rule's adverse cases, and the Alsenan
rebuild (byte-identical, no private input)."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t601"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import t601_rules as R  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ drawn fixture (not Alsenan)
T = 150.0
GAPS = {"arch": (2000.0, 3000.0), "passage": (5000.0, 6200.0), "door": (8000.0, 8900.0), "lift": (10000.0, 11000.0),
        "window": (12500.0, 13700.0)}


def _fixture(path, rot_deg=0.0, mirror=False):
    import ezdxf

    th = math.radians(rot_deg)

    def P(x, y):
        x = -x if mirror else x
        return (x * math.cos(th) - y * math.sin(th) - 300000.0, x * math.sin(th) + y * math.cos(th) - 800000.0)

    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    for nm in ("GF", "arch120", "D90"):
        doc.blocks.new(name=nm)
    a = doc.blocks.get("arch120")
    a.add_line((0, 0), (0, T))
    a.add_line((1000, 0), (1000, T))
    d = doc.blocks.get("D90")
    d.add_line((0, 0), (50, 0))
    d.add_line((50, 0), (50, T))
    d.add_line((850, 0), (900, 0))
    d.add_line((850, 0), (850, T))
    msp = doc.modelspace()
    cuts = sorted(GAPS.values())
    xs = [0.0] + [v for g in cuts for v in g] + [15000.0]
    for x0, x1 in zip(xs[0::2], xs[1::2]):
        for y in (0.0, T):
            msp.add_line(P(x0, y), P(x1, y), dxfattribs={"layer": "1"})
    for x in [v for g in cuts for v in g] + [0.0, 15000.0]:
        msp.add_line(P(x, 0), P(x, T), dxfattribs={"layer": "1"})
    ang = (rot_deg + (180.0 if mirror else 0.0)) % 360.0
    sx = -1.0 if mirror else 1.0
    msp.add_blockref("arch120", P(*((GAPS["arch"][0], 0.0))), dxfattribs={"layer": "4", "rotation": rot_deg,
                                                                          "xscale": sx})
    msp.add_blockref("D90", P(GAPS["door"][0], 0.0), dxfattribs={"layer": "4", "rotation": rot_deg, "xscale": sx})
    x0, x1 = GAPS["lift"]
    for y in (0.0, 50.0, 100.0, T):
        msp.add_line(P(x0, y), P(x1, y), dxfattribs={"layer": "5"})
    x0, x1 = GAPS["window"]
    for y in (50.0, 100.0):
        msp.add_line(P(x0, y), P(x1, y), dxfattribs={"layer": "W"})
    msp.add_line(P(GAPS["passage"][0], 0.0), P(GAPS["passage"][1], 0.0), dxfattribs={"layer": "2"})
    msp.add_line(P(GAPS["passage"][0], T), P(GAPS["passage"][1], T), dxfattribs={"layer": "2"})
    msp.add_blockref("GF", P(7000.0, -3000.0), dxfattribs={"layer": "4"})
    _ = ang
    doc.saveas(path)


def _read(tmp_path, **kw):
    ex = _load("t601_extract")
    p = tmp_path / "fixture.dxf"
    _fixture(p, **kw)
    return ex.read(str(p))["storeys"]["GF"]["gaps"]


def _by_width(rows):
    return {round(r["width_m"], 3): r for r in rows}


@pytest.mark.parametrize("kw", [{}, {"rot_deg": 90.0}, {"rot_deg": 33.0}, {"mirror": True}])
def test_fixture_census_arch_and_passage_skirted_door_lift_window_not(tmp_path, kw):
    rows = _by_width(_read(tmp_path, **kw))
    assert sorted(rows) == [0.9, 1.0, 1.2], rows.keys()   # arch 1.0 and lift 1.0 share a width: check by kind
    kinds = sorted(R.kind_of(r["evidence"]) for r in _read(tmp_path, **kw))
    assert kinds == ["DOOR", "DOORLESS", "DOORLESS", "FRAMED", "WINDOW"]
    out = {}
    for r in _read(tmp_path, **kw):
        res = R.classify({"evidence": r["evidence"], "ends": r["ends"], "wall_t_m": str(r["wall_t_m"]),
                          "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
        out.setdefault(res["kind"], []).append((r["width_m"], res["status"], res["jamb_lm"]))
    assert sorted(out["DOORLESS"]) == [(1.0, "FIX_ROW", "0.30"), (1.2, "FIX_ROW", "0.30")]
    assert out["DOOR"] == [(0.9, "NO_JAMB_SKIRTING", "0")]
    assert out["FRAMED"] == [(1.0, "NO_JAMB_SKIRTING", "0")]
    assert out["WINDOW"][0][1] == "NO_JAMB_SKIRTING"
    arch = [r for r in _read(tmp_path, **kw) if "ARCH_BLOCK" in r["evidence"]]
    assert len(arch) == 1 and arch[0]["ends"] == ["MASONRY_JAMB", "MASONRY_JAMB"]
    passage = [r for r in _read(tmp_path, **kw) if "HEAD_LINES" in r["evidence"]]
    assert len(passage) == 1 and passage[0]["width_m"] == 1.2


def test_fixture_hand_calculation():
    # two real jambs x 0.15 m wall = 0.30 lm per doorless opening; the door's 2 x 0.15 is never skirted
    r = R.classify({"evidence": ["ARCH_BLOCK"], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.15",
                    "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
    assert Decimal(r["fix_lm"]) == Decimal("2") * Decimal("0.15")


# ------------------------------------------------------------------ adverse cases
def test_framed_opening_refused_as_doorless():
    r = R.classify({"evidence": ["PANEL_LINES"], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.20",
                    "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
    assert r["kind"] == "FRAMED" and r["jamb_lm"] == "0" and r["fix_lm"] is None


def test_door_with_head_lines_is_still_a_door():
    r = R.classify({"evidence": ["DOOR_BLOCK", "HEAD_LINES"], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"],
                    "wall_t_m": "0.15", "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
    assert r["kind"] == "DOOR" and r["fix_lm"] is None


@pytest.mark.parametrize("t", [None, ""])
def test_unknown_depth_held_never_zero(t):
    r = R.classify({"evidence": [], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": t,
                    "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
    assert r["status"] == "HELD" and r["jamb_lm"] is None and r["fix_lm"] is None


def test_unknown_side_held_with_bound():
    r = R.classify({"evidence": ["ARCH_BLOCK"], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.20",
                    "sides": ["DRY", None], "treatment": "DEDUCTED"})
    assert r["status"] == "HELD" and r["jamb_lm"] is None and r["bound_lm"] == "0.40"


def test_wet_side_not_applicable_and_outdoor_held_by_name():
    wet = R.classify({"evidence": ["ARCH_BLOCK"], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.15",
                      "sides": ["DRY", "WET"], "treatment": "DEDUCTED"})
    assert wet["status"] == "NOT_APPLICABLE" and wet["fix_lm"] is None
    out = R.classify({"evidence": [], "ends": ["COLUMN_JAMB", "COLUMN_JAMB"], "wall_t_m": "0.20",
                      "sides": ["OUTDOOR", "OUTDOOR"], "treatment": "NO_LINE"})
    assert out["status"] == "OUTDOOR_SCOPE" and out["jamb_lm"] is None and out["bound_lm"] == "0.40"
    fix, held = R.tally([("w", wet), ("o", out)])
    assert fix == 0 and held == ["o"]


def test_continuous_face_is_not_a_jamb_and_in_cell_needs_no_fix():
    r = R.classify({"evidence": ["HEAD_LINES"], "ends": ["MASONRY_JAMB", "CONTINUOUS_FACE"], "wall_t_m": "0.15",
                    "sides": ["DRY", "DRY"], "treatment": "IN_CELL"})
    assert r["status"] == "INCLUDED_IN_OUTLINE" and r["jamb_lm"] == "0.15" and r["fix_lm"] is None


def test_unbounded_end_and_unknown_treatment_held():
    r = R.classify({"evidence": [], "ends": ["MASONRY_JAMB", "UNBOUNDED"], "wall_t_m": "0.15",
                    "sides": ["DRY", "DRY"], "treatment": "DEDUCTED"})
    assert r["status"] == "HELD" and r["jamb_lm"] is None
    r = R.classify({"evidence": [], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.15",
                    "sides": ["DRY", "DRY"], "treatment": None})
    assert r["status"] == "HELD" and r["bound_lm"] == "0.30"


def test_bad_inputs_refused():
    with pytest.raises(R.CensusError):
        R.kind_of(["SOMETHING"])
    with pytest.raises(R.CensusError):
        R.classify({"evidence": [], "ends": ["MASONRY_JAMB"], "wall_t_m": "0.15", "sides": ["DRY", "DRY"]})
    with pytest.raises(R.CensusError):
        R.classify({"evidence": [], "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "-0.15",
                    "sides": ["DRY", "DRY"]})
    with pytest.raises(R.CensusError):
        R.tally([("x", {"status": "HELD", "jamb_lm": "0"})])


# ------------------------------------------------------------------ Alsenan rebuild (committed inputs only)
def test_alsenan_rebuild_byte_identical_and_pinned():
    b = _load("t601_alsenan")
    data = b.build()
    assert json.dumps(data, indent=1, sort_keys=True) + "\n" == b.JSON_OUT.read_text(encoding="utf-8")
    assert b.md(data) == b.MD_OUT.read_text(encoding="utf-8")
    for p, h in b.PINS.items():
        if h:
            assert b.sha(ROOT / p) == h, p


def test_alsenan_census_outcome():
    data = json.loads((HERE / "out" / "T601_DOORLESS_CENSUS.json").read_text(encoding="utf-8"))
    by = {c["opening"].split(" ")[0]: c for c in data["census"]}
    assert by["A-1F-01"]["status"] == "FIX_ROW" and by["A-1F-01"]["fix_lm"] == "0.30" == by["A-1F-01"]["his_lm"]
    assert by["A-GF-01"]["status"] == by["P-GF-01"]["status"] == "NOT_APPLICABLE"
    assert by["P-1F-01"]["status"] == "INCLUDED_IN_OUTLINE"
    assert by["P-GF-05"]["status"] == "OUTDOOR_SCOPE" and by["P-GF-05"]["jamb_lm"] is None
    lifts = [c for c in data["census"] if c["kind"] == "FRAMED"]
    assert len(lifts) == 3 and all(c["jamb_lm"] == "0" for c in lifts)
    assert data["valued_fix_lm"] == "0.30" and data["after_fix_rows_lm"] == "209.728592"
    assert data["gap_counts"]["GF:DOOR_INSERTS_NOT_IN_A_GAP"] == ["2D8"]     # the fence gate, outside the house
    assert all(data["gap_counts"][f"{s}:DOOR_INSERTS_NOT_IN_A_GAP"] == [] for s in ("1F", "2F"))
