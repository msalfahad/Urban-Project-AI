"""T-073: PLOT_EDGE_MEMBERS_V1 - foundation members at the plot edge as separate lines
(engine.source.plot_edge_members).

Synthetic plot (not a client drawing), drawn in mm; the same plot is also run rotated 37 degrees and drawn in metres.
Hand truth, worked on paper from the drawn geometry, never from engine output:

  Plot 24.00 x 12.00 m, closed foundation band 0.20 m wide inside the plot line.
    centre line = 2 x (23.80 + 11.80) = 71.20 m;  plan = 71.20 x 0.20 = 14.24 m2 (= 24 x 12 - 23.60 x 11.60)

  Footings (layer FOUND), drawn five different ways:
    A  block insert on an ANNOTATION layer, block geometry (unit square +-0.5) on FOUND, scale 1.6 x 1.2 at
       (1.00, 0.60): x 0.20-1.80, y 0.00-1.20. Band south centre line y = 0.10 inside x 0.20-1.80 = 1.60 m.
    B  MIRRORED insert (x scale -1.5, y scale 2.0) of a block drawn from x 0 to +1.0 at (24.00, 6.00):
       x 22.50-24.00, y 5.00-7.00. Band east centre line x = 23.90 inside y 5.00-7.00 = 2.00 m.
       (Read without the mirror the footing would sit at x 24.00-25.50, outside the band: 0 m.)
    C  OPEN polyline x 8.00-11.00, y 10.80-12.00, its south side interrupted 9.20-9.80 where a strap enters (gap
       0.60 m on the line of that side). Band north centre line y = 11.90 inside x 8.00-11.00 = 3.00 m: HELD.
    D  closed polyline x 8.50-10.50, y 5.00-7.00 (inside the plot, not on the band).
    E  closed polyline x 3.00-5.00, y 5.50-6.50 (inside the plot).
    F  four loose LINEs x 0.00-1.00, y 5.00-6.00 AND a closed polyline on the same outline (drawn twice):
       one footing. Band west centre line x = 0.10 inside y 5.00-6.00 = 1.00 m.
  Columns: 0.30 x 0.30 at x 12.00-12.30, y 0.00-0.30 (on the band, no footing): 0.30 m in a column only;
           0.30 x 0.30 at x 0.70-1.00, y 0.00-0.30 (inside footing A: stays in A).
  Not footings: an L of two lines and a U of three lines whose gap is across its legs (x 15.00-15.50).

  Band split:  in closed footings A 1.60 + B 2.00 + F 1.00 = 4.60 m;  in the open outline C 3.00 m;
               in a column only 0.30 m;  free 71.20 - 4.60 - 3.00 - 0.30 = 63.30 m (12.66 m2).
  Section CANDIDATE 0.20 x 0.60 (two drawings disagree): free 63.30 x 0.20 x 0.60 = 7.596 m3 PROVISIONAL, not in a total.
  Crossing levels: band -1.20 / -0.60; A -1.50 / -1.10 -> overlap 0.10, band's own depth 0.50:
               1.60 x 0.20 x 0.50 = 0.160 m3 (0.032 m3 already in A);  F -1.50 / -1.30 -> overlap 0 (different
               elevations): 1.00 x 0.20 x 0.60 = 0.120 m3, nothing deducted;  B no levels -> HELD (2.00 m, 0.40 m2).

  Straps (faces on layer STRAP, schedule sections):
    S1 faces x 9.20 / 9.80, y 7.00-11.30, W 0.60 H 0.50: centre line 4.30 m; from D's face (y 7.00) to the open
       outline C (y 10.80) clear 3.80 m -> 3.80 x 0.60 x 0.50 = 1.140 m3; 0.50 m inside C HELD.
    S2 faces y 5.80 / 6.20, x 4.50-9.00, W 0.40 H 0.40: inside E 4.50-5.00 and D 8.50-9.00 (1.00 m left to the
       footings), clear 3.50 m -> 3.50 x 0.40 x 0.40 = 0.560 m3.
    S3 faces y 2.00 / 2.30 (drawn 0.30), schedule W 0.40: width conflict -> HELD, 2.00 m.

  Natural-ground boundary beam: L band on two sides (drawn at x + 40 m), outer 24.00 and 12.00 m, width 0.20:
    centre line (24.00 - 0.10) + (12.00 - 0.10) = 35.80 m, plan 7.16 m2 (= 24 x 0.20 + 11.80 x 0.20);
    printed 0.20 x 0.40: 35.80 x 0.08 = 2.864 m3 MEASURED; no section -> HELD with 35.80 m.
  Typical pads 1.30 x 0.80 x 0.30 with no printed count: HELD, never a volume.

  Totals that may enter a total: straps 1.140 + 0.560 = 1.700 m3; natural-ground beam 2.864 m3; the band none.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import ezdxf
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import plot_edge_members as PM     # noqa: E402

TOL = 1e-6
CASES = [(0.0, 1.0, 0.001), (37.0, 1.0, 0.001), (37.0, 0.001, 1.0), (0.0, 0.001, 1.0)]   # (deg, k, unit_m)


class Plot:
    """the synthetic plot of the docstring, rotated by deg and scaled by k (drawing units = mm x k)."""

    def __init__(self, deg=0.0, k=1.0):
        self.deg, self.k = deg, k
        self.c, self.s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def P(self, x, y):
        return ((x * self.c - y * self.s) * self.k, (x * self.s + y * self.c) * self.k)

    def lines(self, pts, closed=True):
        q = [self.P(*p) for p in pts]
        n = len(q)
        return [(q[i], q[(i + 1) % n]) for i in range(n if closed else n - 1)]

    def poly(self, pts):
        return [self.P(*p) for p in pts]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def build(pl, *, xclip=False):
    doc = ezdxf.new()
    msp = doc.modelspace()
    bu = doc.blocks.new("FTU")
    bu.add_lwpolyline(rect(-500, -500, 500, 500), close=True, dxfattribs={"layer": "FOUND"})
    bl = doc.blocks.new("FTL")
    bl.add_lwpolyline(rect(0, -500, 1000, 500), close=True, dxfattribs={"layer": "FOUND"})
    k = pl.k
    ia = msp.add_blockref("FTU", pl.P(1000, 600), dxfattribs={"layer": "ANNO", "xscale": 1.6 * k, "yscale": 1.2 * k,
                                                              "rotation": pl.deg})
    msp.add_blockref("FTL", pl.P(24000, 6000), dxfattribs={"layer": "ANNO", "xscale": -1.5 * k, "yscale": 2.0 * k,
                                                           "rotation": pl.deg})
    if xclip:
        from ezdxf.xclip import XClip
        XClip(ia).set_block_clipping_path([(-500, -500), (0, -500), (0, 500), (-500, 500)])
    msp.add_lwpolyline(pl.poly([(9800, 10800), (11000, 10800), (11000, 12000), (8000, 12000), (8000, 10800),
                                (9200, 10800)]), dxfattribs={"layer": "FOUND"})
    msp.add_lwpolyline(pl.poly(rect(8500, 5000, 10500, 7000)), close=True, dxfattribs={"layer": "FOUND"})
    msp.add_lwpolyline(pl.poly(rect(3000, 5500, 5000, 6500)), close=True, dxfattribs={"layer": "FOUND"})
    for a, b in pl.lines(rect(0, 5000, 1000, 6000)):
        msp.add_line(a, b, dxfattribs={"layer": "FOUND"})
    msp.add_lwpolyline(pl.poly(rect(0, 5000, 1000, 6000)), close=True, dxfattribs={"layer": "FOUND"})
    for a, b in pl.lines([(15000, 3000), (15000, 4000), (16000, 4000)], closed=False):        # an L
        msp.add_line(a, b, dxfattribs={"layer": "FOUND"})
    for a, b in pl.lines([(15000, 8000), (15000, 9000), (15500, 9000), (15500, 8000)], closed=False):   # a U
        msp.add_line(a, b, dxfattribs={"layer": "FOUND"})
    msp.add_text("F1", dxfattribs={"layer": "FOUND", "insert": pl.P(9000, 6000)})
    return doc


def band(pl):
    return [{"id": f"O{i}", "layer": "BAND", "a": a, "b": b} for i, (a, b) in
            enumerate(pl.lines(rect(0, 0, 24000, 12000)))] + \
           [{"id": f"I{i}", "layer": "BAND", "a": a, "b": b} for i, (a, b) in
            enumerate(pl.lines(rect(200, 200, 23800, 11800)))]


def columns(pl):
    return [{"id": "COL_FREE", "kind": "COLUMN", "poly": pl.poly(rect(12000, 0, 12300, 300))},
            {"id": "COL_IN_A", "kind": "COLUMN", "poly": pl.poly(rect(700, 0, 1000, 300))}]


def straps(pl):
    return [{"id": "S1", "mark": "SBx", "faces": pl.lines([(9200, 7000), (9200, 11300)], False) +
             pl.lines([(9800, 11300), (9800, 7000)], False), "W_m": 0.60, "H_m": 0.50, "row_source": "row SBx"},
            {"id": "S2", "mark": "SBy", "faces": pl.lines([(4500, 5800), (9000, 5800)], False) +
             pl.lines([(4500, 6200), (9000, 6200)], False), "W_m": 0.40, "H_m": 0.40, "row_source": "row SBy"},
            {"id": "S3", "mark": "SBz", "faces": pl.lines([(12000, 2000), (14000, 2000)], False) +
             pl.lines([(12000, 2300), (14000, 2300)], False), "W_m": 0.40, "H_m": 0.40, "row_source": "row SBz"}]


def ng_lines(pl):
    pts = [(40000, 0), (64000, 0), (64000, 200), (40200, 200), (40200, 12000), (40000, 12000)]
    return [{"id": f"N{i}", "layer": "NGB", "a": a, "b": b} for i, (a, b) in enumerate(pl.lines(pts))]


def member_at(members, pl, x, y, unit_m):
    from engine.source import concrete_strip_guard as SG
    px, py = pl.P(x, y)
    hits = [m for m in members if SG._point_in_poly(px, py, m["poly"])]
    assert len(hits) == 1, (x, y, [m["id"] for m in hits])
    return hits[0]


def intake(pl, unit_m, **kw):
    doc = build(pl, **kw)
    res = PM.footing_outlines(doc.modelspace(), ["FOUND"], unit_m)
    members, dups = PM.merge_members(res["members"], unit_m=unit_m)
    return res, members, dups


# ---------------------------------------------------------------------------------------------- intake
@pytest.mark.parametrize("deg,k,unit_m", CASES)
def test_intake_finds_every_drawn_footing_once(deg, k, unit_m):
    pl = Plot(deg, k)
    res, members, dups = intake(pl, unit_m)
    assert len(members) == 6                                   # A, B, C, D, E, F (F drawn twice -> once)
    assert len(dups) == 1
    src = {member_at(members, pl, *xy, unit_m)["source"] for xy in [(1000, 600), (23250, 6000)]}
    assert src == {"BLOCK_INSERT"}
    b = member_at(members, pl, 23250, 6000, unit_m)
    assert b["mirrored"] is True
    assert abs(b["plan_m2"] - 1.5 * 2.0) <= TOL
    c = member_at(members, pl, 9500, 11400, unit_m)
    assert c["source"] == "OPEN_OUTLINE" and abs(c["open_gap_m"] - 0.60) <= TOL
    assert abs(c["plan_m2"] - 3.0 * 1.2) <= TOL
    assert any(h["reason"] == "FOOTING_OUTLINE_OPEN" and abs(h["gap_m"] - 0.60) <= TOL for h in res["held"])
    reasons = sorted(ch["reason"] for ch in res["chains"])
    assert reasons == ["OPEN_CHAIN_NOT_AN_OUTLINE", "OPEN_CHAIN_NOT_AN_OUTLINE"]      # the L and the U
    assert any(s["type"] == "TEXT" for s in res["skipped"])


def test_mirror_is_not_normalised_away():
    """the mirrored block lands at x 22.50-24.00 (hand), not at 24.00-25.50."""
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    b = member_at(members, pl, 23250, 6000, 0.001)
    xs = [p[0] for p in b["poly"]]
    assert abs(min(xs) - 22500) <= 1e-6 and abs(max(xs) - 24000) <= 1e-6


def test_xclipped_insert_is_held_not_measured():
    pl = Plot()
    res, members, _ = intake(pl, 0.001, xclip=True)
    assert len(members) == 5
    assert any(h["reason"] == "XCLIPPED_INSERT" for h in res["held"])


def test_unknown_unit_is_unsupported():
    res = PM.footing_outlines(build(Plot()).modelspace(), ["FOUND"], None)
    assert res["members"] == [] and res["unsupported"][0]["reason"] == "UNIT_UNKNOWN"


def test_gap_tolerance_is_one_micrometre():
    """a 4-line outline whose last corner misses by 0.5 mm is open, never closed silently."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    for a, b in [((0, 0), (1000, 0)), ((1000, 0), (1000, 1000)), ((1000, 1000), (0, 1000)), ((0, 1000), (0, 0.5))]:
        msp.add_line(a, b, dxfattribs={"layer": "FOUND"})
    res = PM.footing_outlines(msp, ["FOUND"], 0.001)
    assert res["members"] == []
    assert res["chains"] and abs(res["chains"][0]["gap_m"] - 0.0005) <= 1e-9


# ---------------------------------------------------------------------------------------------- band
@pytest.mark.parametrize("deg,k,unit_m", CASES)
def test_band_every_metre_in_one_record(deg, k, unit_m):
    pl = Plot(deg, k)
    _, members, _ = intake(pl, unit_m)
    B = PM.band_records(band(pl), members, unit_m, (0.15, 0.25), columns=columns(pl))
    c = B["by_class_m"]
    assert abs(B["conservation"]["centre_line_m"] - 71.20) <= TOL
    assert abs(B["conservation"]["difference_m"]) <= TOL
    assert abs(c[PM.FREE] - 63.30) <= TOL
    assert abs(c[PM.IN_FOOTING] - 4.60) <= TOL
    assert abs(c[PM.IN_OPEN] - 3.00) <= TOL
    assert abs(c[PM.IN_COLUMN] - 0.30) <= TOL
    assert B["unpaired"] == []


@pytest.mark.parametrize("deg,k,unit_m", CASES)
def test_band_lines_provisional_and_crossings_by_elevation(deg, k, unit_m):
    pl = Plot(deg, k)
    _, members, _ = intake(pl, unit_m)
    B = PM.band_records(band(pl), members, unit_m, (0.15, 0.25), columns=columns(pl))
    A = member_at(members, pl, 1000, 600, unit_m)["id"]
    F = member_at(members, pl, 500, 5500, unit_m)["id"]
    sec = {"W_m": 0.20, "H_m": 0.60, "source": "schedule row (candidate)", "status": "CANDIDATE"}
    L = PM.band_lines(B, section=sec, band_levels={"bottom_m": -1.20, "top_m": -0.60},
                      member_levels={A: {"bottom_m": -1.50, "top_m": -1.10}, F: {"bottom_m": -1.50, "top_m": -1.30}})
    free = [x for x in L if x["part"] == "FREE"][0]
    assert free["status"] == "PROVISIONAL" and not free["in_total"]
    assert abs(free["volume_m3"] - 7.596) <= TOL and abs(free["length_m"] - 63.30) <= TOL
    inf = {tuple(x["members"]): x for x in L if x["part"] == "IN_FOOTING"}
    assert abs(inf[(A,)]["volume_m3"] - 0.160) <= TOL and abs(inf[(A,)]["deducted_m3"] - 0.032) <= TOL
    assert abs(inf[(F,)]["volume_m3"] - 0.120) <= TOL and inf[(F,)]["deducted_m3"] == 0
    held_b = [x for x in inf.values() if x["status"] == "HELD"]
    assert len(held_b) == 1 and held_b[0]["reason"] == "CROSSING_LEVELS_NOT_PRINTED"
    assert abs(held_b[0]["length_m"] - 2.00) <= TOL and held_b[0]["volume_m3"] is None
    op = [x for x in L if x["part"] == "IN_OPEN_FOOTING_OUTLINE"][0]
    assert op["status"] == "HELD" and abs(op["length_m"] - 3.00) <= TOL and abs(op["open_gap_m"] - 0.60) <= TOL
    col = [x for x in L if x["part"] == "IN_COLUMN_ONLY"][0]
    assert col["status"] == "HELD" and abs(col["length_m"] - 0.30) <= TOL
    assert abs(sum(x["length_m"] for x in L) - 71.20) <= TOL          # every metre once, none 0


def test_band_without_section_is_held_never_zero():
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    B = PM.band_records(band(pl), members, 0.001, (0.15, 0.25))
    L = PM.band_lines(B)
    assert all(x["status"] == "HELD" and x["volume_m3"] is None for x in L)
    assert abs(sum(x["length_m"] for x in L) - 71.20) <= TOL


def test_band_proven_section_enters_total():
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    B = PM.band_records(band(pl), members, 0.001, (0.15, 0.25), columns=columns(pl))
    sec = {"W_m": 0.20, "H_m": 0.60, "source": "section X", "status": "PROVEN"}
    led = PM.ledger(band=B, band_section=sec)
    assert abs(led["totals_m3"]["FOUNDATION_BOUNDARY_BAND"] - 7.596) <= TOL


def test_section_without_source_is_refused():
    with pytest.raises(ValueError):
        PM.band_lines({"records": []}, section={"W_m": 0.2, "H_m": 0.6, "status": "PROVEN"})


def test_v2_style_members_merge_without_double_count():
    """a member list from another source (the CONCRETE_LEDGER_V2 geometry) with footing D again: used once."""
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    v2 = [{"id": "v2:D", "kind": "FOOTING", "poly": list(reversed(pl.poly(rect(8500, 5000, 10500, 7000))))}]
    merged, dups = PM.merge_members(v2, members, unit_m=0.001)
    assert len(merged) == 6 and dups[0]["same_as"] == "v2:D"


# ---------------------------------------------------------------------------------------------- straps
@pytest.mark.parametrize("deg,k,unit_m", CASES)
def test_straps_clear_length_open_outline_and_conflict(deg, k, unit_m):
    pl = Plot(deg, k)
    _, members, _ = intake(pl, unit_m)
    S = {s["id"]: s for s in PM.strap_records(straps(pl), members, unit_m)}
    assert abs(S["S1"]["clear_length_m"] - 3.80) <= TOL and abs(S["S1"]["in_open_outline_m"] - 0.50) <= TOL
    assert abs(S["S2"]["clear_length_m"] - 3.50) <= TOL and abs(S["S2"]["in_footing_m"] - 1.00) <= TOL
    v = {(ln["strap"], ln["part"]): ln for s in S.values() for ln in s["lines"]}
    assert abs(v[("S1", "CLEAR")]["volume_m3"] - 1.140) <= TOL
    assert v[("S1", "IN_OPEN_FOOTING_OUTLINE")]["status"] == "HELD"
    assert abs(v[("S2", "CLEAR")]["volume_m3"] - 0.560) <= TOL
    assert v[("S2", "IN_FOOTING")]["status"] == "LEFT_TO_FOOTING" and v[("S2", "IN_FOOTING")]["volume_m3"] is None
    assert v[("S3", "CLEAR")]["status"] == "HELD" and v[("S3", "CLEAR")]["reason"] == "STRAP_WIDTH_CONFLICT"
    assert abs(v[("S3", "CLEAR")]["length_m"] - 2.00) <= TOL


def test_strap_without_section_is_held():
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    s = dict(straps(pl)[1], H_m=None)
    ln = PM.strap_records([s], members, 0.001)[0]["lines"][0]
    assert ln["status"] == "HELD" and ln["reason"] == "STRAP_SECTION_NOT_PRINTED" and ln["volume_m3"] is None


# ---------------------------------------------------------------------------------------------- natural-ground beam
@pytest.mark.parametrize("deg,k,unit_m", CASES)
def test_natural_ground_beam_own_band_own_section(deg, k, unit_m):
    pl = Plot(deg, k)
    sec = {"W_m": 0.20, "H_m": 0.40, "source": "typical boundary wall section, printed 20 x 40", "status": "PROVEN"}
    ln = PM.ng_beam(ng_lines(pl), unit_m, (0.15, 0.25), section=sec)[0]
    assert ln["status"] == "MEASURED" and ln["in_total"]
    assert abs(ln["length_m"] - 35.80) <= TOL and abs(ln["area_m2"] - 7.16) <= TOL
    assert abs(ln["volume_m3"] - 2.864) <= TOL
    held = PM.ng_beam(ng_lines(pl), unit_m, (0.15, 0.25))[0]
    assert held["status"] == "HELD" and held["volume_m3"] is None and abs(held["length_m"] - 35.80) <= TOL


# ---------------------------------------------------------------------------------------------- ledger
def test_ledger_separate_lines_and_totals():
    pl = Plot()
    _, members, _ = intake(pl, 0.001)
    B = PM.band_records(band(pl), members, 0.001, (0.15, 0.25), columns=columns(pl))
    S = PM.strap_records(straps(pl), members, 0.001)
    ng = PM.ng_beam(ng_lines(pl), 0.001, (0.15, 0.25),
                    section={"W_m": 0.20, "H_m": 0.40, "source": "printed 20 x 40", "status": "PROVEN"})
    led = PM.ledger(band=B, band_section={"W_m": 0.20, "H_m": 0.60, "source": "schedule row", "status": "CANDIDATE"},
                    straps=S, ng=ng, pads=[{"id": "PAD", "L_m": 1.30, "W_m": 0.80, "H_m": 0.30, "count": None,
                                            "source": "typical plan"}],
                    columns=[{"id": "BWCOL", "L_m": 0.20, "W_m": 0.30, "H_m": None, "count": None}])
    assert set(led["totals_m3"]) == {"STRAP_BEAM", "NG_BOUNDARY_GROUND_BEAM"}
    assert abs(led["totals_m3"]["STRAP_BEAM"] - 1.700) <= TOL
    assert abs(led["totals_m3"]["NG_BOUNDARY_GROUND_BEAM"] - 2.864) <= TOL
    members_listed = {ln["member"] for ln in led["lines"]}
    assert members_listed == {"FOUNDATION_BOUNDARY_BAND", "STRAP_BEAM", "NG_BOUNDARY_GROUND_BEAM",
                              "BOUNDARY_WALL_PAD", "BOUNDARY_WALL_COLUMN"}
    pad = [ln for ln in led["lines"] if ln["member"] == "BOUNDARY_WALL_PAD"][0]
    assert pad["status"] == "HELD" and pad["reason"] == "COUNT_NOT_PRINTED" and pad["volume_m3"] is None
    assert all(ln["volume_m3"] != 0 for ln in led["lines"])            # missing is never 0
    assert led["provisional_not_in_total"] and all(not x["in_total"] for x in led["provisional_not_in_total"])
