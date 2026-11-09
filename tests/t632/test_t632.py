"""T-632: a beam upstand is billed over the extent the plan draws for it, never over the band piece a section mark cuts
(R-T632-1 .. 3). Hand villa "V632" (not the training villa), adverse cases, then the development villa from the
committed census (the private rebuild only when the private drawing is present)."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t632"))
import t632_rules as R  # noqa: E402
import t632_alsenan as A  # noqa: E402

OUT = ROOT / "research" / "agents_t632" / "out" / "T632_UPSTAND_CENSUS.json"
PRIVATE = ROOT.parent / "private" / "ST7757.dxf"
D = Decimal

# ---- villa "V632" (hand, metres) ---------------------------------------------------------------------------------
# beam BM 0.30 x 0.60, band y 0 .. 0.30, x 0 .. 5.00 (one piece between two support faces)
# printed section S-S: base 30, upstand 15 wide x 25 high on the RIGHT, total 85 (cm) -> upstand 0.15 x 0.25 = 0.0375 m2
# plan: level-change hatch x 0 .. 2.40 on the band; hidden top edge y = 0.15, x 0 .. 2.40; cut line at x = 1.00
#       looking -x (arrow tip west) -> the viewer's right is +y (+n): the upstand sits on y 0.15 .. 0.30
# own = 0.0375 x 2.40 = 0.090 m3; the section-mark span (the whole piece, 5.00) would give 0.1875 m3: refused
SECTION_CM = [(15, 60), (15, 85), (30, 85), (30, 0), (0, 0), (0, 60), (15, 60)]
BAND = Polygon([(0.0, 0.0), (5.0, 0.0), (5.0, 0.30), (0.0, 0.30)])   # long side first, as route G writes it
HATCH = box(0.0, 0.0, 2.40, 0.30)
EDGE = ((0.0, 0.15), (2.40, 0.15))


def _ev(band_pts, hatch_poly, edge):
    u, _n = A._axis(band_pts)
    return u, [{"kind": "HATCH", "handle": "H1", "interval": A._proj(u, list(hatch_poly.exterior.coords))},
               {"kind": "TOP_EDGE", "handle": "E1", "interval": A._proj(u, list(edge))}]


def test_v632_section_read():
    up = R.section_take_upstand(SECTION_CM, 0.30, 0.60)
    assert up == {"state": "PRESENT", "w_m": D("0.150000"), "h_m": D("0.250000"), "side": "RIGHT"}


def test_v632_drawn_extent_not_section_span():
    u, ev = _ev(list(BAND.exterior.coords), HATCH, EDGE)
    ext = R.drawn_extent(ev)
    assert ext["state"] == "MEASURED" and ext["length_m"] == D("2.400000")
    q = R.upstand_quantity(D("0.15"), D("0.25"), ext, cut_t=1.0, section_span=A._proj(u, list(BAND.exterior.coords)))
    assert q["volume_m3"] == D("0.090000")
    assert "section-mark span refused" in q["basis"]          # 5.00 m piece is not the upstand's run


def test_v632_section_span_accepted_only_when_equal():
    u, ev = _ev(list(BAND.exterior.coords), HATCH, EDGE)
    q = R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent(ev), cut_t=1.0, section_span=(0.0, 2.40))
    assert q["basis"] == "DRAWN_EXTENT (= section-mark span)" and q["volume_m3"] == D("0.090000")


@pytest.mark.parametrize("angle,mirror", [(0, False), (90, False), (37, False), (180, True), (-63, True)])
def test_v632_mirror_rotation(angle, mirror):
    def tf(g):
        g = rotate(g, angle, origin=(0, 0))
        return scale(g, -1, 1, origin=(0, 0)) if mirror else g
    from shapely.geometry import LineString
    b, h, e = tf(BAND), tf(HATCH), tf(LineString(EDGE))
    pts = list(b.exterior.coords)
    _u, ev = _ev(pts, h, list(e.coords))
    ext = R.drawn_extent(ev)
    assert ext["length_m"] == D("2.400000")
    assert R.upstand_quantity(D("0.15"), D("0.25"), ext)["volume_m3"] == D("0.090000")


def test_plan_side_by_view_direction():
    # band along +x, n = +y; looking west (-x): right hand = +y
    assert R.plan_side("RIGHT", (-1, 0), (0, 1)) == "+n"
    assert R.plan_side("LEFT", (-1, 0), (0, 1)) == "-n"
    assert R.plan_side("RIGHT", (1, 0), (0, 1)) == "-n"       # mirrored arrow flips the side
    with pytest.raises(R.Refused):
        R.plan_side("RIGHT", (0, 1), (0, 1))                  # a view along the band is not a cross-section


def test_tread_series_is_stair_not_edge():
    lines = [("T1", 0, 1.15, 0.10), ("T2", 0, 1.15, 0.40), ("T3", 0, 1.15, 0.70), ("T4", 0, 1.15, 1.00),
             ("UP", 0, 3.00, 0.10)]
    assert R.tread_series(lines) == {"T1", "T2", "T3", "T4"}
    assert R.tread_series(lines[:2] + lines[4:]) == set()   # two lines are not a series


def test_strip_identity():
    assert R.strip_identity(above_convention=False, hatched=False, crossed_by_section=True, printed_on_section=False,
                            outline_continues=True) == {"class": "NOT_UPSTAND", "identity": "slab-edge outline"}
    assert R.strip_identity(above_convention=True, hatched=False, crossed_by_section=True, printed_on_section=True,
                            outline_continues=False)["class"] == "UPSTAND"
    assert R.strip_identity(above_convention=False, hatched=True, crossed_by_section=True, printed_on_section=False,
                            outline_continues=False)["class"] == "UNRESOLVED"


def test_rounded_profile_is_not_an_upstand():
    rounded = [(34.8, 0), (34.8, 55), (24.8, 72.3), (14.8, 75), (0, 75), (0, 0)]
    assert R.section_take_upstand(rounded, 0.348, 0.75)["state"] == "NOT_PRESENT"


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_section_span_when_strip_runs_further():
    """The drawn evidence runs 4.00 m but the section-mark piece is 2.40 m: the piece is refused as the length."""
    ev = [{"kind": "HATCH", "handle": "H", "interval": (0, 4.0)}, {"kind": "TOP_EDGE", "handle": "E", "interval": (0, 4.0)}]
    q = R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent(ev), cut_t=1.0, section_span=(0.0, 2.40))
    assert q["volume_m3"] == D("0.150000") and "refused" in q["basis"]


def test_adverse_evidence_disagrees_is_a_range():
    ev = [{"kind": "HATCH", "handle": "H", "interval": (0, 2.40)}, {"kind": "TOP_EDGE", "handle": "E", "interval": (0, 4.0)}]
    q = R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent(ev))
    assert q["state"] == "HELD" and q["range_m3"] == (D("0.090000"), D("0.150000")) and "volume_m3" not in q


def test_adverse_cut_outside_extent_refused():
    ev = [{"kind": "HATCH", "handle": "H", "interval": (0, 2.40)}]
    with pytest.raises(R.Refused):
        R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent(ev), cut_t=3.5)


def test_adverse_section_only_is_held_never_zero():
    q = R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent([]), piece_span_m=5.0)
    assert q["state"] == "HELD" and "volume_m3" not in q and q["range_m3"][1] == D("0.187500")
    with pytest.raises(R.Refused):
        R.upstand_quantity(D("0.15"), D("0.25"), R.drawn_extent([]))


@pytest.mark.parametrize("w,h", [(0, 0.25), (0.15, 0), (-0.1, 0.2)])
def test_adverse_missing_section_never_zero(w, h):
    with pytest.raises(R.Refused):
        R.upstand_quantity(w, h, R.drawn_extent([{"kind": "HATCH", "handle": "H", "interval": (0, 1)}]))


def test_adverse_units_mm_outline_refused():
    mm = [(x * 10, y * 10) for x, y in SECTION_CM]           # millimetres fed as centimetres: base 3.00 m
    with pytest.raises(R.Refused):
        R.section_take_upstand(mm, 0.30, 0.60)


def test_adverse_bad_evidence():
    with pytest.raises(R.Refused):
        R.drawn_extent([{"kind": "GUESS", "handle": "x", "interval": (0, 1)}])
    with pytest.raises(R.Refused):
        R.drawn_extent([{"kind": "HATCH", "handle": "x", "interval": (1, 1)}])


# ---- development villa (committed census) ---------------------------------------------------------------------------
def _census():
    return json.loads(OUT.read_text(encoding="utf-8"))


def _row(c, st, mark):
    return next(r for r in c["storeys"][st] if r["mark"] == mark and r["class"] not in ("NO_UPSTAND_EVIDENCE",))


@pytest.mark.parametrize("st,mark,edge", [("GF", "B20", "55F"), ("1F", "B23", "7BC")])
def test_dev_b20_b23_settled(st, mark, edge):
    r = _row(_census(), st, mark)
    assert r["class"] == "ENGINE_RIGHT"
    assert r["extent"]["state"] == "MEASURED" and r["extent"]["length_m"] == "3.000000"
    assert any(e.startswith("HATCH") for e in r["extent"]["evidence"]) and f"TOP_EDGE {edge}" in r["extent"]["evidence"]
    assert r["own"]["volume_m3"] == "0.120000" and r["engine_minus_own_m3"] == "0.000000"
    up = r["sections"][0]["upstand"]
    assert (up["w_m"], up["h_m"], up["plan_side"]) == ("0.200000", "0.200000", "+n")
    assert r["top_edge_offsets_m"][0]["to_plus_n_face"] == "0.200000"     # hidden edge bounds the +n 0.20 part


def test_dev_strip_north_of_b20_is_not_the_upstand():
    s = _census()["b20_strip"]
    for st in ("GF", "1F"):
        assert s[st]["identity"]["class"] == "NOT_UPSTAND"
        assert s[st]["length_m"] == "4.325000" and s[st]["hatched"] is False and s[st]["face_layers"] == ["1"]
        assert s[st]["crossed_by_cut"] is not None
        assert s[st]["status"].startswith("HELD")


def test_dev_held_rows_carry_no_volume():
    c = _census()
    held = [r for rows in c["storeys"].values() for r in rows if r["class"] == "HELD"]
    assert {(r["storey"], r["mark"]) for r in held} == {("GF", "B4"), ("GF", "CA"), ("GF", "B24"), ("2F", "B8"),
                                                       ("2F", "B15"), ("2F", "B7")}
    assert all("own" not in r and r["drawn_length_m"] for r in held)


@pytest.mark.skipif(not PRIVATE.exists(), reason="private drawing absent (.work/private/ST7757.dxf)")
def test_private_rebuild_equals_committed():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t632" / "t632_alsenan.py"), str(PRIVATE),
                        "--check"], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
