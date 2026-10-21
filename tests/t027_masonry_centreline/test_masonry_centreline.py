"""T-027: the masonry centreline run per wall thickness (MASONRY_CENTRELINE_V1, UP-WALL-GEOM-001). Hand fixtures only
(none is the development villa). Bands are written as engine.source.arch_walls records: centreline at mid thickness
in drawing units (mm unless said), the extent a band reader gives (an L corner leaves the corner piece out: both bands
stop at the other's inner face; a T's through-wall runs on).

Hand values (m):
  L mixed   A 0.30 along x (outer face y 0, centre y 0.15), drawn x 0.20 .. 5.00; B 0.20 along y (outer face x 0,
            centre x 0.10), drawn y 0.30 .. 4.00. Centrelines meet at (0.10, 0.15): A 5.00 - 0.10 = 4.90,
            B 4.00 - 0.15 = 3.85. Plan check: 0.30 x 4.90 + 0.20 x 3.85 = 2.24 = 0.30 x 5.00 + 0.20 x 3.70.
  T mixed   0.20 through x 0 .. 6.00 (centre y 0.10); 0.10 stem centre x 3.00 from the face y 0.20 to 3.00 free:
            0.20 = 6.00, 0.10 = 2.80 (the stem to the through-wall's face).
  cross 1   one family 0.20, four stems: x -3.00 .. -0.10 and 0.10 .. 3.00, y -2.00 .. -0.10 and 0.10 .. 2.00:
            6.00 + 2 x 1.90 = 9.80 (= 4.00 + 2 x 2.90, whichever runs through).
  cross 2   0.20 x -3.00 .. -0.05 and 0.05 .. 3.00, 0.10 y -2.00 .. -0.10 and 0.10 .. 2.00 (four stems, two
            families): 0.20 = 5.90, 0.10 = 3.80, the 0.20 x 0.10 piece HELD (0.20 + 0.10 or 0.10 + 0.20 m).
            With the 0.20 drawn through (-3.00 .. 3.00): a T each side, 0.20 = 6.00, 0.10 = 3.80, nothing held.
  column    0.20 x 0 .. 8.00 (centre y 0), column 0.30 x 0.30 at x 3.85 .. 4.15 across the wall: 8.00 - 0.30 = 7.70;
            a column beside the wall (y 0.10 .. 0.40) cuts nothing. L at a 0.40 x 0.40 corner column: bands drawn
            from the column faces (x 0.40 .. 5.00, y 0.40 .. 4.00): free ends at the column, 4.60 + 3.60 = 8.20.
  wedge     two 0.20 walls at 45 deg meeting at the origin, drawn to the other's near face (0.1 / sin 45 =
            0.141421 m from the meeting point), far ends 4.00 and 3.00 from it: 4.00 + 3.00 = 7.00.
  opening   two collinear 0.20 bands x 0 .. 2.00 and 2.90 .. 5.00 with a 0.90 door centred at x 2.45: joined, 5.00;
            without an opening record there: not joined, 2.00 + 2.10 = 4.10.
Adversarial: every fixture turned 37 deg and -121 deg, mirrored, and in metres instead of mm gives the same metres.
Missing data: no bands -> NO_WALL_BANDS with None; bands whose units disagree -> HELD; block m2 / m3 always HELD
(UP-MAS-HEIGHT-001, owner Q-60), value None, never 0.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import masonry_centreline as MC  # noqa: E402

TOL = 1e-6


def band(wid, t, p0, p1, unit=0.001, cols=0.0, **kw):
    """a straight band record; p0 / p1 in metres, written in the drawing unit."""
    return {"wall_id": wid, "t_m": t, "family": f"{t:.2f}", "centreline": [(p0[0] / unit, p0[1] / unit),
                                                                          (p1[0] / unit, p1[1] / unit)],
            "gross_lm": round(math.dist(p0, p1), 9), "columns_in_wall_lm": cols, **kw}


def run_of(rec):
    return {b["family"]: b["masonry_run_lm"] for b in rec["by_thickness"]}


# ---- the fixtures in metres (local frame)
FIX = {
    "L_MIXED": [("A", 0.30, (0.20, 0.15), (5.00, 0.15)), ("B", 0.20, (0.10, 0.30), (0.10, 4.00))],
    "T_MIXED": [("TH", 0.20, (0.0, 0.10), (6.00, 0.10)), ("ST", 0.10, (3.00, 0.20), (3.00, 3.00))],
    "CROSS_ONE": [("W", 0.20, (-3.0, 0.0), (-0.10, 0.0)), ("E", 0.20, (0.10, 0.0), (3.0, 0.0)),
                  ("S", 0.20, (0.0, -2.0), (0.0, -0.10)), ("N", 0.20, (0.0, 0.10), (0.0, 2.0))],
    "CROSS_TWO": [("W", 0.20, (-3.0, 0.0), (-0.05, 0.0)), ("E", 0.20, (0.05, 0.0), (3.0, 0.0)),
                  ("S", 0.10, (0.0, -2.0), (0.0, -0.10)), ("N", 0.10, (0.0, 0.10), (0.0, 2.0))],
    "CROSS_THROUGH": [("WE", 0.20, (-3.0, 0.0), (3.0, 0.0)),
                      ("S", 0.10, (0.0, -2.0), (0.0, -0.10)), ("N", 0.10, (0.0, 0.10), (0.0, 2.0))],
    "WEDGE": [("X", 0.20, (0.1 / math.sin(math.pi / 4), 0.0), (4.0, 0.0)),
              ("D", 0.20, (0.1, 0.1), (3.0 / math.sqrt(2), 3.0 / math.sqrt(2)))],
}
HAND = {"L_MIXED": {"0.30": 4.90, "0.20": 3.85}, "T_MIXED": {"0.20": 6.00, "0.10": 2.80},
        "CROSS_ONE": {"0.20": 9.80}, "CROSS_TWO": {"0.20": 5.90, "0.10": 3.80},
        "CROSS_THROUGH": {"0.20": 6.00, "0.10": 3.80}, "WEDGE": {"0.20": 7.00}}


def _xf(p, rot_deg=0.0, mirror=False, shift=(250.0, -40.0)):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    return (c * x - s * y + shift[0], s * x + c * y + shift[1])


def bands_of(name, rot=0.0, mirror=False, unit=0.001):
    return [band(w, t, _xf(a, rot, mirror), _xf(b, rot, mirror), unit=unit) for w, t, a, b in FIX[name]]


VARS = [dict(), dict(rot=37.0), dict(rot=-121.0, mirror=True), dict(unit=1.0), dict(rot=90.0, mirror=True, unit=1.0)]


def test_wedge_fixture_geometry_is_what_the_docstring_says():
    (_, _, a0, a1), (_, _, b0, b1) = FIX["WEDGE"]
    assert math.dist(a0, (0, 0)) == pytest.approx(0.1 / math.sin(math.pi / 4), abs=1e-12)
    assert math.dist(b0, (0, 0)) == pytest.approx(0.1 / math.sin(math.pi / 4), abs=1e-12)
    assert math.dist(b1, (0, 0)) == pytest.approx(3.0, abs=1e-12)


@pytest.mark.parametrize("name", sorted(FIX))
@pytest.mark.parametrize("var", VARS, ids=lambda v: "-".join(f"{k}={v[k]}" for k in v) or "plain")
def test_hand_fixtures_every_variant(name, var):
    rec = MC.measure(bands_of(name, **var))
    got = run_of(rec)
    assert set(got) == set(HAND[name])
    for fam, v in HAND[name].items():
        assert got[fam] == pytest.approx(v, abs=TOL), (name, var, fam)
    for b in rec["by_thickness"]:                   # never a height, never a default, never 0
        assert b["block_m2"]["status"] == b["block_m3"]["status"] == "HELD"
        assert b["block_m2"]["value"] is None and "Q-60" in b["block_m2"]["reason"]


def test_l_corner_conserves_the_plan_area():
    rec = MC.measure(bands_of("L_MIXED"))
    strip = sum(b["plan_strip_m2"] for b in rec["by_thickness"])
    assert strip == pytest.approx(0.30 * 5.00 + 0.20 * 3.70, abs=TOL)
    kinds = {j["kind"] for j in rec["junctions"]}
    assert kinds == {"L"} and rec["held"] == []


def test_t_stem_runs_to_the_face_and_the_through_wall_is_unchanged():
    rec = MC.measure(bands_of("T_MIXED"))
    p = {x["wall_id"]: x for x in rec["pieces"]}
    assert p["ST"]["ends"][0] == "T_STEM" and p["ST"]["ends"][1] == "FREE_END"
    assert p["TH"]["ends"] == ["FREE_END", "FREE_END"] and p["TH"]["corner_ext_m"] == [0.0, 0.0]


def test_cross_of_one_family_is_joined_once():
    rec = MC.measure(bands_of("CROSS_ONE"))
    assert [j["kind"] for j in rec["junctions"]].count("CROSS_SPLIT") == 1
    assert rec["held"] == [] and rec["status"] == "MEASURED"


def test_cross_of_two_families_holds_the_piece_and_says_how_much():
    rec = MC.measure(bands_of("CROSS_TWO"))
    assert rec["status"] == "MEASURED_WITH_HELD_PIECES"
    held = [h for h in rec["held"] if h["what"] == "CROSS_PIECE"]
    assert len(held) == 1 and len(rec["held"]) == 1          # held once, not once per stem
    assert all(e == "CROSS_HELD" for p in rec["pieces"] for e in p["ends"] if e not in ("FREE_END",))
    assert held[0]["max_lm_by_family"] == {"0.20": pytest.approx(0.10, abs=TOL), "0.10": pytest.approx(0.20, abs=TOL)}
    b = {x["family"]: x for x in rec["by_thickness"]}
    assert b["0.20"]["status"] == b["0.10"]["status"] == "MEASURED_WITH_HELD_PIECES"
    # the held piece is in neither family: 0.2 x 5.90 + 0.1 x 3.80 = the plan less the 0.20 x 0.10 piece
    assert sum(x["plan_strip_m2"] for x in rec["by_thickness"]) == pytest.approx(0.2 * 6.0 + 0.1 * 3.8 - 0.02, abs=TOL)


def test_an_irregular_corner_is_held_never_guessed():
    # A drawn 5 cm into B's band (neither on its face nor through it): both ends left as drawn and listed
    w = [band("A", 0.20, (0.05, 0.10), (5.0, 0.10)), band("B", 0.20, (0.10, 0.20), (0.10, 4.0))]
    rec = MC.measure(w)
    assert run_of(rec)["0.20"] == pytest.approx(4.95 + 3.80, abs=TOL)
    assert rec["status"] == "MEASURED_WITH_HELD_PIECES"
    held = {h["wall_id"]: h for h in rec["held"]}
    assert set(held) == {"A", "B"} and held["A"]["max_lm"] == pytest.approx(0.15, abs=TOL)
    assert rec["by_thickness"][0]["status"] == "MEASURED_WITH_HELD_PIECES"


def test_columns_in_the_wall_line_are_concrete():
    w = [band("W", 0.20, (0.0, 0.0), (8.0, 0.0))]
    col_in = [(3.85, -0.15), (4.15, -0.15), (4.15, 0.15), (3.85, 0.15)]
    col_beside = [(6.0, 0.10), (6.3, 0.10), (6.3, 0.40), (6.0, 0.40)]
    rec = MC.measure(w, columns_m=[col_in, col_beside])
    assert run_of(rec)["0.20"] == pytest.approx(7.70, abs=TOL) and rec["column_basis"].startswith("COLUMN_POLYGONS")
    # no polygons: the band's own columns_in_wall_lm is used, and the record says so
    rec2 = MC.measure([band("W", 0.20, (0.0, 0.0), (8.0, 0.0), cols=0.30)])
    assert run_of(rec2)["0.20"] == pytest.approx(7.70, abs=TOL) and rec2["column_basis"].startswith("BAND_COLUMNS")


@pytest.mark.parametrize("given", [True, False])
def test_corner_column_is_never_wall(given):
    w = [band("A", 0.20, (0.40, 0.10), (5.0, 0.10)), band("B", 0.20, (0.10, 0.40), (0.10, 4.0))]
    col = [(0.0, 0.0), (0.4, 0.0), (0.4, 0.4), (0.0, 0.4)]
    rec = MC.measure(w, columns_m=[col] if given else ())
    assert run_of(rec)["0.20"] == pytest.approx(4.60 + 3.60, abs=TOL)
    assert all(p["ends"][0] == "FREE_END" for p in rec["pieces"])


def test_opening_gap_is_in_the_run_and_listed_not_deducted():
    w = [band("W1", 0.20, (0.0, 0.0), (2.0, 0.0)), band("W2", 0.20, (2.9, 0.0), (5.0, 0.0))]
    door = {"opening_id": "D1", "kind": "DOOR", "width_m": 0.90, "wall_t_m": 0.20,
            "position": {"centre_m": [2.45, 0.0]}, "host_wall": None}
    rec = MC.measure(w, openings=[door])
    b = rec["by_thickness"][0]
    assert b["masonry_run_lm"] == pytest.approx(5.00, abs=TOL) and b["openings_lm_listed"] == pytest.approx(0.90)
    assert [j["kind"] for j in rec["junctions"]] == ["OPENING_GAP"]
    rec2 = MC.measure(w)                         # no opening on record: the gap is not wall
    assert run_of(rec2)["0.20"] == pytest.approx(4.10, abs=TOL)
    assert rec2["by_thickness"][0]["openings_lm_listed"] is None


def test_missing_data_is_never_zero():
    rec = MC.measure([])
    assert rec["status"] == "NO_WALL_BANDS" and rec["by_thickness"] == []
    bad = [band("A", 0.2, (0, 0), (4, 0)), band("B", 0.2, (0, 2), (4, 2), unit=1.0)]   # mm and m mixed
    rec2 = MC.measure(bad)
    assert rec2["status"] == "HELD" and rec2["by_thickness"] == [] and rec2["unit_m"] is None


def test_curved_band_takes_its_centreline_arc():
    arc = {"wall_id": "ARC", "t_m": 0.2, "family": "0.20", "centreline": [(2000.0, 0.0), (0.0, 2000.0)],
           "gross_lm": 3.298672, "columns_in_wall_lm": 0.0,
           "curved": {"bases_lm": {"MIN_RADIUS_ARC": 3.141593, "MID_BAND_ARC": math.pi / 2 * 2.1,
                                   "MAX_RADIUS_ARC": 3.455752}}}
    rec = MC.measure([band("S", 0.2, (2.0, -3.0), (2.0, 0.0)), arc], unit_m=0.001)
    assert run_of(rec)["0.20"] == pytest.approx(3.0 + math.pi / 2 * 2.1, abs=TOL)
    assert rec["held"] == []


# ---- the T-019 synthetic villas through the engine (hand truth in tools/synth_villa/villas.py, never the engine)
ENGINE_CASES = [("SV-A", {}), ("SV-A", {"rotate_deg": 37.0}), ("SV-A", {"mirror": True, "units": "m"}),
                ("SV-B", {"mirror": True, "units": "m"}), ("SV-C", {"rotate_deg": 37.0}),
                ("SV-C", {"rotate_deg": -121.0, "mirror": True, "units": "m"})]


@pytest.mark.parametrize("vid,var", ENGINE_CASES, ids=[f"{v}-" + ("-".join(f"{k}={x[k]}" for k in x) or "plain")
                                                        for v, x in ENGINE_CASES])
def test_synthetic_villas_equal_the_hand_centreline(tmp_path, vid, var):
    pytest.importorskip("ezdxf")
    from tools.synth_villa import build as B
    from tools.synth_villa import compare as C
    from tools.synth_villa import villas as V
    got = B.write_villa(vid, tmp_path / f"{vid}.dxf", **var)
    _room, arch, _refusal = C.run_engine(got["path"])      # a COMPLETENESS_FAILED run keeps its walls
    res = MC.measure_arch(arch)
    assert sorted(res) == sorted(V.HAND[vid])
    for fl, rec in res.items():
        hand = V.HAND[vid][fl]["walls"]
        b = {x["family"]: x for x in rec["by_thickness"]}
        assert set(b) == set(hand), (vid, fl)
        for fam, h in hand.items():
            assert b[fam]["masonry_run_lm"] == pytest.approx(h["gross_lm"], abs=0.01), (vid, var, fl, fam)
            assert b[fam]["openings_lm_listed"] == pytest.approx(h["openings_lm"], abs=0.01), (vid, var, fl, fam)
            assert b[fam]["held_max_lm"] == 0.0
        assert rec["held"] == [] and rec["status"] == "MEASURED"
    if vid == "SV-A":                              # the T-019 finding: 54.6 run, 46.2 after the listed openings
        r = res["GF"]["by_thickness"]
        r20 = next(x for x in r if x["family"] == "0.20")
        assert r20["masonry_run_lm"] - r20["openings_lm_listed"] == pytest.approx(46.2, abs=0.01)
        old = next(x for x in next(w for w in arch["walls"] if w["floor"] == "GF")["by_thickness"]
                   if x["family"] == "0.20")
        assert old["net_lm"] == pytest.approx(44.4, abs=0.01)   # the face-band run V2.9 gives, unchanged


def test_not_wired():
    """a new piece: no method imports it, so no released quantity moves."""
    hits = [p for p in (ROOT / "tools").rglob("*.py") if "masonry_centreline" in p.read_text(encoding="utf-8")]
    hits += [p for p in (ROOT / "engine").rglob("*.py")             # T-125: its V2 piece reuses V1 and is itself
             if p.name not in ("masonry_centreline.py", "masonry_centreline_v2.py")     # not wired (t125 checks it)
             and "masonry_centreline" in p.read_text(encoding="utf-8")]
    assert hits == []
