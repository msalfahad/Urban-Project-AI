"""T-617 R-T617-1 opening head bound from drawn members: a non-Alsenan hand fixture (villa Y), adverse cases, the
side reading on a synthetic DXF (plain, mirrored, rotated labels), and the Alsenan rebuild (byte-identical, no private
input)."""
from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t617"
sys.path.insert(0, str(HERE))
import t617_rules as R  # noqa: E402

D = Decimal


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ villa Y (not Alsenan), by hand
# storey FFL +0.50 -> +4.10 (interval 3.60), floor build-up b 0.08, slab t 0.15, ring beam over the lift door D 0.60:
#   soffit = 3.60 - 0.08 - 0.60 = 2.92 m above the FFL
#   paint face (finished ceiling) 2.90 -> 2.92 >= 2.90: no narrowing (0.000 m2)
#   plaster face to the slab soffit 3.60 - 0.08 - 0.15 = 3.37 -> deduction <= 1.10 x 2.92 = 3.212; kept 1.10 x 0.45 = 0.495
#   (0.45 = D - t)
def test_villa_y_soffit_and_faces_by_hand():
    s = R.beam_soffit("3.60", "0.08", "0.60")
    assert s == D("2.92")
    hb = R.head_bound([{"id": "RB-1", "soffit": s, "on_wall_line": True}])
    assert hb["high"] == D("2.92") and hb["low"] == D("0") and hb["basis"] == "DRAWN_MEMBER_BOUND"
    paint = R.face_deduction_bound("1.10", "2.90", hb["high"])
    assert paint["high"] == D("3.190") and paint["narrowing"] == D("0")
    plaster = R.face_deduction_bound("1.10", D("3.60") - D("0.08") - D("0.15"), hb["high"])
    assert plaster["high"] == D("3.2120") and plaster["narrowing"] == D("0.4950")
    assert plaster["narrowing"] / D("1.10") == D("0.60") - D("0.15")      # the (D - t) band, independent of b


def test_band_independent_of_buildup():
    for b in ("0", "0.05", "0.12"):
        face = D("3.60") - D(b) - D("0.15")
        cap = R.face_deduction_bound("1", face, R.beam_soffit("3.60", b, "0.60"))
        assert cap["narrowing"] == D("0.45")


def test_note_member_scenario_kept_apart():
    beam = {"id": "RB", "soffit": R.beam_soffit("4.60", "0.05", "0.75"), "on_wall_line": True}   # 3.80
    tie = {"id": "note tie 3.00", "soffit": R.note_member_soffit("3.00"), "on_wall_line": "SCENARIO"}
    hb = R.head_bound([beam, tie])
    assert hb["high"] == D("3.80") and hb["high_scenario"] == D("3.00")   # never silently applied as firm
    off = R.head_bound([beam, {**tie, "on_wall_line": False}])
    assert off["high_scenario"] == D("3.80")


def test_printed_height_settles():
    hb = R.head_bound([{"id": "RB", "soffit": D("2.92"), "on_wall_line": True}], printed_height="2.10")
    assert hb["low"] == hb["high"] == D("2.10") and hb["basis"] == "PRINTED"


# ------------------------------------------------------------------ adverse
def test_default_door_height_refused():
    for v in ("2.20", "2.40"):
        with pytest.raises(R.BoundError):
            R.default_height(v)


def test_missing_depth_gives_no_bound_never_zero():
    assert R.beam_soffit("3.60", "0.08", None) is None
    hb = R.head_bound([{"id": "RB-x", "soffit": None, "on_wall_line": True}])
    assert hb["high"] is None and hb["basis"] == "NO_BOUND" and hb["named_missing"] == ["RB-x"]
    f = R.face_deduction_bound("1.00", "3.35", hb["high"])
    assert f["high"] == D("3.35") and f["narrowing"] == 0                # face range kept whole, nothing invented


def test_units_floats_and_nonsense_refused():
    with pytest.raises(R.BoundError):
        R.beam_soffit("3600", "80", "600", unit="mm")
    with pytest.raises(R.BoundError):
        R.beam_soffit(3.6, "0.08", "0.60")
    with pytest.raises(R.BoundError):
        R.beam_soffit("3.60", "0.08", "3.70")                            # deeper than the storey
    with pytest.raises(R.BoundError):
        R.beam_soffit("3.60", "-0.05", "0.60")
    with pytest.raises(R.BoundError):
        R.head_bound([{"id": "RB", "soffit": D("2.9"), "on_wall_line": "maybe"}])
    with pytest.raises(R.BoundError):
        R.face_deduction_bound("1.00", None, D("2.9"))


def test_opening_in_two_storeys_refused():
    assert R.opening_in_storeys("OP-1", {"GF": {"OP-1"}, "1F": {"OP-2"}}) == "GF"
    with pytest.raises(R.BoundError):
        R.opening_in_storeys("OP-1", {"GF": {"OP-1"}, "1F": {"OP-1"}})


# ------------------------------------------------------------------ side reading on a synthetic DXF
def _doc(labels, mirror=False):
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new()
    msp = doc.modelspace()
    sx = -1 if mirror else 1
    x0, x1 = sorted((0, sx * 2000))
    msp.add_line((x0, 0), (x1, 2000), dxfattribs={"layer": "S-OPENING"})
    msp.add_line((x0, 2000), (x1, 0), dxfattribs={"layer": "S-OPENING"})
    msp.add_line((x0 - 200, 0), (x1 + 200, 0))
    msp.add_line((x0 - 200, -200), (x1 + 200, -200))
    pos = {"S": ((x0 + x1) / 2, 120, 0), "N": ((x0 + x1) / 2, 1700, 0), "W": (x0 + 150, 1000, 90),
           "E": (x1 - 150, 1000, 90)}
    for side, mark in labels.items():
        x, y, r = pos[side]
        msp.add_text(mark, dxfattribs={"insert": (x, y), "rotation": r})
    return msp


def test_side_members_plain_and_mirrored():
    ex = _load("t617_extract")
    labels = {"S": "B9", "N": "B1", "W": "B4", "E": "B2"}
    for mirror in (False, True):
        msp = _doc(labels, mirror)
        c = ex.crosses(msp)
        assert len(c) == 1
        sides, band = ex.side_members(msp, c[0][1:5])
        assert {k: v["mark"] for k, v in sides.items()} == labels
        assert band == [-200.0, 0.0]


def test_text_not_a_mark_ignored():
    ex = _load("t617_extract")
    msp = _doc({"S": "5010/m", "N": "B1"})
    sides, _ = ex.side_members(msp, ex.crosses(msp)[0][1:5])
    assert set(sides) == {"N"}


# ------------------------------------------------------------------ Alsenan (training villa) rebuild
def test_alsenan_rebuild_byte_identical():
    b = _load("t617_alsenan")
    assert b.main([]) == 0


def test_alsenan_bounds_and_no_candidate_move():
    b = _load("t617_alsenan")
    d = b.build()
    rows = {r["storey"]: r for r in d["rows"]}
    assert [rows[s]["member_over_door"]["mark"] for s in ("GF", "1F", "2F")] == ["B14", "B7", "B2"]
    assert [rows[s]["head"]["high_at_drawn_buildup"] for s in ("GF", "1F", "2F")] == ["3.70", "3.40", "3.75"]
    assert rows["GF"]["head"]["high_note19_scenario"] == "3.00"
    assert d["summary"]["candidate_m2_narrowed_all_lines"] == "0.0000"
    assert d["summary"]["candidate_m2_narrowed_note19_scenario"] == "1.3000"
    assert all(r["head"]["printed"] is None for r in d["rows"])          # nothing assumed, height stays HELD
    assert [rows[s]["q72_plaster_for_T558"]["always_plastered_above_head_m2"] for s in ("GF", "1F", "2F")] == \
        ["0.5900", "0.5900", "0.2400"]


def test_alsenan_refuses_changed_input(monkeypatch):
    b = _load("t617_alsenan")
    monkeypatch.setitem(b.PINNED, "T608", "0" * 64)
    with pytest.raises(SystemExit):
        b.build()
