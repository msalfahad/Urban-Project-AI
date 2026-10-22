"""T-125: MASONRY_CENTRELINE_V2 (open floor split, doorway at a free end, curved glazed bay, glazed lines, a crossing
drawn through by both walls, the Q-69 B lengths, the plan identity). Hand fixtures only, none is the development villa.
Bands are written as engine.source.arch_walls records (centreline at mid thickness, the extent a band reader gives);
the wall-layer faces, glazing and door swings are the evidence V2 reads (drawing units, mm unless said).

Hand values (m):
  GARDEN     one 0.20 band x 0 .. 18.00 (centre y 0) that a band reader drew across a garden: faces drawn only over
             x 0 .. 3.00 and 14.20 .. 18.00 (the garden edge between them is on another layer): run = 3.00 + 3.80 =
             6.80, split out 11.20 (V1: 18.00). A passage record 11.20 wide with a symbol block in it: still split
             (wider than the 3.00 m an opening can be). Gap 1.20 instead (faces 0 .. 3.00 and 4.20 .. 8.00): clear
             passage -> split, 3.00 + 3.80 = 6.80; with a head line drawn over it -> kept, run 8.00, opening 1.20,
             physical 6.80.
  DOORWAY    L room: W1 0.20 along x (centre y 0) drawn x 0.10 .. 6.00, W2 0.20 along y (centre x 0) drawn y 0.10 ..
             4.00 (an L: both to (0, 0)): 6.00 + 4.00 = 10.00. Partition P 0.10 on x 3.00 drawn y 0.90 .. 4.00 (top
             end free); a 0.75 door leaf hinged at (3.00, 0.86) swings in the 0.80 gap between W1's face (y 0.10)
             and P's free end: P = 4.00 - 0.10 = 3.90 (doorway in the run, a T stem on W1's face), physical 3.10.
             Without the swing: 3.10. A 0.50 leaf in a 1.20 gap (P drawn from y 1.30): not a doorway (1.20 > 0.50 +
             0.25 frames), 2.70.
  BAY        0.20 wall along x (centre y 0), x 0 .. 10.00, faces drawn x 0 .. 3.00 and 7.00 .. 10.00; two glazing
             arcs centred (5.00, 3.00), radii sqrt(13) -/+ 0.02 (mid sqrt(13) = 3.605551), drawn to the wall face
             y -0.10. The mid circle meets the centreline at x 3.00 and 7.00: arc = sqrt(13) x 2 acos(3 / sqrt(13)) =
             4.240148; run = 3.00 + 3.00 + 4.240148 = 10.240148; glass 4.240148, physical 6.00.
  GLAZED     two parallel window-layer lines 0.10 apart, 5.00 long, standing clear of every wall band: one glazed
             line of 5.00, in no thickness family. Two concentric window arcs r 2.00 / 2.10 over a quarter turn:
             2.05 x pi / 2 = 3.220132. Glazing inside a wall band (a window) is not a glazed line.
  CROSS      0.20 WE x -3.00 .. 3.00 and 0.20 SN y -2.00 .. 2.00, both drawn through the crossing (each band's faces
             stop at the other): V1 alone counts the 0.20 x 0.20 piece twice (10.00); V2 9.80. SN 0.10 instead: 0.20
             = 5.90, 0.10 = 3.80, the piece HELD (two families, no rule chooses).
  PIER       a 0.20 wall 0.60 long (< 4 t = 0.80): in the run and listed as a pier.
Every fixture turned 37 deg and -121 deg, mirrored, and in metres instead of mm gives the same metres. The plan
identity sum(run x t) = the union of the run strips holds (PASS) on every fixture. Missing data: no bands ->
NO_WALL_BANDS; no column outlines or no evidence -> HELD (never V1 figures, never 0); block m2 / m3 HELD (T-108).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import masonry_centreline as V1  # noqa: E402
from engine.source import masonry_centreline_v2 as V2  # noqa: E402

TOL = 1e-6


# ------------------------------------------------------------------------------------------------ fixture builder
class Fx:
    """a floor in metres; out(rot, mirror, unit) writes it in drawing units."""

    def __init__(self):
        self.bands, self.faces, self.glz, self.garcs, self.doors, self.ops, self.cols = [], [], [], [], [], [], []

    def band(self, wid, t, p0, p1, faces=None):
        """a band and, unless faces=(), both faces drawn over the station intervals in `faces` (default whole)."""
        self.bands.append((wid, t, p0, p1))
        L = math.dist(p0, p1)
        u = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
        n = (-u[1], u[0])
        for a, b in (faces if faces is not None else [(0.0, L)]):
            for o in (t / 2, -t / 2):
                self.faces.append(((p0[0] + u[0] * a + n[0] * o, p0[1] + u[1] * a + n[1] * o),
                                   (p0[0] + u[0] * b + n[0] * o, p0[1] + u[1] * b + n[1] * o)))
        return self

    def opening(self, oid, kind, width, centre, head=0, blocks=(), marks=0):
        self.ops.append({"opening_id": oid, "kind": kind, "width_m": width, "centre": centre,
                         "evidence": {"marks": {"head_lines": head, "marks": marks, "blocks": list(blocks)},
                                      "glazing_lm": 0.0}})
        return self

    def out(self, rot=0.0, mirror=False, unit=0.001, shift=(250.0, -40.0)):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

        def X(p):                        # metres -> transformed metres
            x, y = p
            if mirror:
                x = -x
            return (c * x - s * y + shift[0], s * x + c * y + shift[1])

        def D(p):                        # -> drawing units
            q = X(p)
            return (q[0] / unit, q[1] / unit)
        walls = [{"wall_id": w, "t_m": t, "family": f"{t:.2f}", "centreline": [D(a), D(b)],
                  "gross_lm": round(math.dist(a, b), 9), "columns_in_wall_lm": 0.0} for w, t, a, b in self.bands]
        ev = {"face_segments": [(D(a), D(b)) for a, b in self.faces],
              "glazing_segments": [(D(a), D(b)) for a, b in self.glz],
              "glazing_arcs": [{"c": D(g["c"]), "r": g["r"] / unit, "s": D(g["s"]), "m": D(g["m"]), "e": D(g["e"])}
                               for g in self.garcs],
              "door_arcs": [{"c": D(g["c"]), "r": g["r"] / unit} for g in self.doors]}
        ops = []
        for o in self.ops:
            q = X(o["centre"])
            r = {k: v for k, v in o.items() if k != "centre"}
            r["position"] = {"centre_m": [q[0], q[1]]}
            ops.append(r)
        cols = [[X(p) for p in q] for q in self.cols]
        return walls, ev, ops, cols, unit


def arc(c, r, a0, a1):
    am = (a0 + a1) / 2
    return {"c": c, "r": r, "s": (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)),
            "m": (c[0] + r * math.cos(am), c[1] + r * math.sin(am)),
            "e": (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))}


def run(fx, **kw):
    walls, ev, ops, cols, unit = fx.out(**kw)
    return V2.measure(walls, unit_m=unit, openings=ops, columns_m=cols, floor="T", evidence=ev)


def fam(rec, key="arch_run_lm"):
    return {b["family"]: b[key] for b in rec["by_thickness"]}


XFORMS = [dict(), dict(rot=37.0), dict(rot=-121.0), dict(mirror=True), dict(rot=37.0, mirror=True),
          dict(unit=1.0, shift=(0.25, -0.04))]


# ------------------------------------------------------------------------------------------------------ fixtures
def garden(gap=11.2, passage=None):
    fx = Fx().band("G", 0.20, (0.0, 0.0), (3.0 + gap + 3.8, 0.0), faces=[(0.0, 3.0), (3.0 + gap, 6.8 + gap)])
    if passage:
        fx.opening("P1", "PASSAGE", gap, (3.0 + gap / 2, 0.0), **passage)
    return fx


def doorway(leaf=0.75, p_from=0.90, hinge=(3.0, 0.86)):
    fx = Fx().band("W1", 0.20, (0.10, 0.0), (6.0, 0.0)).band("W2", 0.20, (0.0, 0.10), (0.0, 4.0))
    fx.band("P", 0.10, (3.0, p_from), (3.0, 4.0))
    if leaf:
        fx.doors.append({"c": hinge, "r": leaf})
    return fx


def bay():
    fx = Fx().band("B", 0.20, (0.0, 0.0), (10.0, 0.0), faces=[(0.0, 3.0), (7.0, 10.0)])
    c = (5.0, 3.0)
    for r in (math.sqrt(13) - 0.02, math.sqrt(13) + 0.02):
        dx = math.sqrt(r * r - 3.1 ** 2)          # drawn to the face y -0.10
        a0 = math.atan2(-3.1, -dx)
        a1 = math.atan2(-3.1, dx)
        fx.garcs.append(arc(c, r, a0, a1))
    return fx


def glazed():
    fx = Fx().band("A", 0.20, (0.0, 0.0), (6.0, 0.0))
    fx.glz += [((0.0, 5.0), (5.0, 5.0)), ((0.0, 5.10), (5.0, 5.10))]          # a free straight glass line
    fx.glz += [((1.0, -0.03), (2.5, -0.03)), ((1.0, 0.03), (2.5, 0.03))]      # a window inside wall A
    fx.garcs += [arc((20.0, 0.0), 2.0, 0.0, math.pi / 2), arc((20.0, 0.0), 2.1, 0.0, math.pi / 2)]
    return fx


def cross(t2=0.20):
    h1, h2 = 0.10, t2 / 2
    return Fx().band("WE", 0.20, (-3.0, 0.0), (3.0, 0.0), faces=[(0.0, 3.0 - h2), (3.0 + h2, 6.0)]) \
        .band("SN", t2, (0.0, -2.0), (0.0, 2.0), faces=[(0.0, 2.0 - h1), (2.0 + h1, 4.0)])


# ---------------------------------------------------------------------------------------------------------- tests
@pytest.mark.parametrize("xf", XFORMS)
def test_garden_edge_split(xf):
    r = run(garden(), **xf)
    assert fam(r)["0.20"] == pytest.approx(6.80, abs=TOL)
    assert fam(r, "split_out_lm")["0.20"] == pytest.approx(11.20, abs=1e-4)
    st = [s for s in r["stretches"] if not s["in_run"]]
    assert len(st) == 1 and st[0]["bridged_by"] is None and st[0]["length_m"] == pytest.approx(11.2, abs=1e-4)
    # V1 on the same band runs across the garden
    walls, ev, ops, cols, unit = garden().out(**xf)
    assert V1.measure(walls, unit_m=unit, columns_m=cols)["by_thickness"][0]["masonry_run_lm"] == \
        pytest.approx(18.0, abs=TOL)


def test_wide_passage_with_symbol_still_split():
    r = run(garden(passage={"blocks": ["BLK"], "marks": 5}))
    assert fam(r)["0.20"] == pytest.approx(6.80, abs=TOL)


@pytest.mark.parametrize("xf", XFORMS)
def test_passage_clear_split_head_kept(xf):
    clear = run(garden(gap=1.2, passage={}), **xf)
    assert fam(clear)["0.20"] == pytest.approx(6.80, abs=TOL)
    head = run(garden(gap=1.2, passage={"head": 2}), **xf)
    assert fam(head)["0.20"] == pytest.approx(8.00, abs=TOL)
    assert fam(head, "physical_blockwork_lm")["0.20"] == pytest.approx(6.80, abs=TOL)
    assert fam(head, "openings_lm")["0.20"] == pytest.approx(1.20, abs=TOL)
    assert [s["bridged_by"] for s in head["stretches"]] == ["OPENING_HEAD_LINE"]


@pytest.mark.parametrize("xf", XFORMS)
def test_doorway_at_free_end(xf):
    r = run(doorway(), **xf)
    f = fam(r)
    assert f["0.20"] == pytest.approx(10.00, abs=TOL)
    assert f["0.10"] == pytest.approx(3.90, abs=TOL)
    assert fam(r, "physical_blockwork_lm")["0.10"] == pytest.approx(3.10, abs=TOL)
    assert len(r["doorways"]) == 1 and r["doorways"][0]["gap_m"] == pytest.approx(0.80, abs=1e-4)
    assert r["doorways"][0]["evidence"] == "DOOR_SWING"
    p = [x for x in r["runs"] if x["run_id"] == "P"][0]
    assert p["ends"][0] == "T_STEM"


def test_doorway_needs_evidence_and_fit():
    assert fam(run(doorway(leaf=None)))["0.10"] == pytest.approx(3.10, abs=TOL)
    # a 0.50 leaf cannot close a 1.20 gap (leaf + 0.25 frames): no doorway
    r = run(doorway(leaf=0.50, p_from=1.30, hinge=(3.0, 1.26)))
    assert fam(r)["0.10"] == pytest.approx(2.70, abs=TOL) and r["doorways"] == []


def test_doorway_from_a_door_record():
    fx = doorway(leaf=None)
    fx.opening("D1", "DOOR", 0.80, (3.0, 0.50))
    r = run(fx)
    assert fam(r)["0.10"] == pytest.approx(3.90, abs=TOL)
    p = [x for x in r["runs"] if x["run_id"] == "P"][0]
    # the door record and the doorway are one opening: counted once
    assert p["openings_lm"] == pytest.approx(0.80, abs=1e-4) and p["physical_blockwork_lm"] == pytest.approx(3.10, abs=1e-4)


@pytest.mark.parametrize("xf", XFORMS)
def test_curved_glazed_bay(xf):
    r = run(bay(), **xf)
    arc_m = math.sqrt(13) * 2 * math.acos(3 / math.sqrt(13))
    assert fam(r)["0.20"] == pytest.approx(6.0 + arc_m, abs=1e-4)
    assert fam(r, "glass_aluminium_lm")["0.20"] == pytest.approx(arc_m, abs=1e-4)
    assert fam(r, "physical_blockwork_lm")["0.20"] == pytest.approx(6.0, abs=1e-4)
    assert len(r["bays"]) == 1 and r["bays"][0]["basis"] == "CENTRELINE_MEETING"
    assert r["bays"][0]["chord_m"] == pytest.approx(4.0, abs=1e-4)


@pytest.mark.parametrize("xf", XFORMS)
def test_glazed_lines_listed_not_in_family(xf):
    r = run(glazed(), **xf)
    lens = sorted(g["length_m"] for g in r["glazed_lines"])
    assert lens == pytest.approx([2.05 * math.pi / 2, 5.0], abs=1e-4)
    assert fam(r) == {"0.20": pytest.approx(6.0, abs=TOL)}
    assert all("GLAZED_LINE" in g["status"] for g in r["glazed_lines"])


@pytest.mark.parametrize("xf", XFORMS)
def test_cross_drawn_through_by_both(xf):
    walls, ev, ops, cols, unit = cross().out(**xf)
    v1 = V1.measure(walls, unit_m=unit, columns_m=cols)
    assert v1["by_thickness"][0]["masonry_run_lm"] == pytest.approx(10.0, abs=TOL)       # V1 counts it twice
    assert fam(run(cross(), **xf))["0.20"] == pytest.approx(9.80, abs=TOL)
    r2 = run(cross(0.10), **xf)
    assert fam(r2)["0.20"] == pytest.approx(5.90, abs=TOL) and fam(r2)["0.10"] == pytest.approx(3.80, abs=TOL)
    assert any(h["what"] == "CROSS_PIECE" for h in r2["held"])


def test_pier_listed_and_in_run():
    r = run(Fx().band("PI", 0.20, (0.0, 0.0), (0.60, 0.0)))
    assert fam(r)["0.20"] == pytest.approx(0.60, abs=TOL)
    assert [p["run_id"] for p in r["piers"]] == ["PI"]


@pytest.mark.parametrize("make", [garden, doorway, bay, glazed, cross, lambda: garden(1.2, {"head": 1})])
@pytest.mark.parametrize("xf", [dict(), dict(rot=37.0, mirror=True)])
def test_plan_identity(make, xf):
    idn = run(make(), **xf)["identity"]
    assert idn["status"] == "PASS", idn


@pytest.mark.parametrize("make", [garden, doorway, bay, cross, lambda: garden(1.2, {"head": 1})])
def test_lengths_re_add(make):
    r = run(make())
    for x in r["runs"]:
        assert x["physical_blockwork_lm"] + x["openings_lm"] == pytest.approx(x["arch_run_lm"], abs=1e-4)
        assert x["masonry_above_below"]["status"] == "HELD" and x["masonry_above_below"]["value"] is None
    for b in r["by_thickness"]:
        assert b["block_m2"]["value"] is None and b["block_m3"]["value"] is None


def test_missing_data_never_zero():
    walls, ev, ops, cols, unit = garden().out()
    assert V2.measure([], unit_m=unit, columns_m=[], evidence=ev)["status"] == "NO_WALL_BANDS"
    for kw in (dict(columns_m=None, evidence=ev), dict(columns_m=cols, evidence=None)):
        r = V2.measure(walls, unit_m=unit, openings=ops, **kw)
        assert r["status"] == "HELD" and r["by_thickness"] == [] and "required input" in r["why"]


def test_column_in_gap_not_split():
    fx = Fx().band("C", 0.20, (0.0, 0.0), (8.0, 0.0), faces=[(0.0, 3.85), (4.15, 8.0)])
    fx.cols.append([(3.85, -0.15), (4.15, -0.15), (4.15, 0.15), (3.85, 0.15)])
    r = run(fx)
    assert fam(r)["0.20"] == pytest.approx(7.70, abs=TOL)
    assert [s["bridged_by"] for s in r["stretches"]] == ["COLUMN"]


def test_policy_record():
    p = V2.policy_record()
    assert p["policy_id"] == "MASONRY_CENTRELINE_V2" and p["reuses"] == "MASONRY_CENTRELINE_V1"


def test_not_wired():
    """a new piece: no method imports V1 or V2, so no released quantity moves."""
    hits = [p for p in (ROOT / "tools").rglob("*.py") if "masonry_centreline" in p.read_text(encoding="utf-8")]
    hits += [p for p in (ROOT / "engine").rglob("*.py")
             if p.name not in ("masonry_centreline.py", "masonry_centreline_v2.py")
             and "masonry_centreline" in p.read_text(encoding="utf-8")]
    assert hits == []


def test_stretch_longer_than_its_door_is_listed():
    fx = Fx().band("S", 0.20, (0.0, 0.0), (9.0, 0.0), faces=[(0.0, 3.0), (6.0, 9.0)])
    fx.opening("D1", "DOOR", 1.0, (4.5, 0.0))
    r = run(fx)
    assert fam(r)["0.20"] == pytest.approx(9.0, abs=TOL)                 # kept, as V1 keeps it ...
    h = [x for x in r["held"] if x["what"] == "STRETCH_PARTLY_EVIDENCED"]
    assert len(h) == 1 and h[0]["max_lm"] == pytest.approx(2.0, abs=1e-4)   # ... but the 2.00 m is listed
    assert r["by_thickness"][0]["status"] == "MEASURED_WITH_HELD_PIECES"
    assert r["by_thickness"][0]["held_max_lm"] == pytest.approx(2.0, abs=1e-4)


# ------------------------------------------------------------------------------- T-169: jamb stub at a free-end doorway
# Defect D-T125-1 (checker, T-125 merge): a wall-layer jamb stub standing on the face of the wall across a free-end
# doorway was absorbed into the doorway, so the physical length lost it. Hand values (m), the DOORWAY room above with P
# drawn from y 0.95 (face-to-face gap 0.85 from W1's face y 0.10) and a 0.69 leaf hinged at (3.00, 0.20):
#   STUB 0.06  both of P's faces (x 3.00 -/+ 0.05) drawn y 0.10 .. 0.16 on W1's face, no line across its end:
#              arch run P = 4.00 - 0.10 = 3.90 (unchanged), doorway 0.85 - 0.06 = 0.79, physical 3.90 - 0.79 = 3.11
#              (wall 3.05 + stub 0.06); before T-169: doorway 0.85, physical 3.05.
#   STUB 0.03  under the L-P9-04 0.05 m convention: doorway 0.85, physical 3.05, the stub listed BELOW_L-P9-04_LISTED.
#   ONE FACE   one face line 0.06 only: doorway 0.85, listed ONE_FACE_LISTED (a frame line is not a wall).
#   FLOATING   both faces drawn y 0.30 .. 0.36 (not on W1's face): no stub, doorway 0.85.
#   RECORD     the 0.06 stub is its own 0.10 wall record (an arch_v28 RETURN_STUB): P stops at y 0.16 (3.84), the stub
#              record 0.06 (a T stem on W1), family 0.10 arch 3.90, doorway 0.79, physical 3.11 (counted once).
#   DOOR REC   no swing, a door record 0.80 centred (3.00, 0.56), P from y 0.96 (gap 0.86), stub 0.06: doorway 0.80,
#              physical 3.90 - 0.80 = 3.10; the door record and the doorway are one opening.
#   MID-WALL   0.20 wall x 0 .. 6.00, faces drawn 0 .. 2.00 and 2.85 .. 6.00 (a 0.05 jamb nib inside the drawn
#              faces), door record 0.80 at x 2.45: V1 opening gap, physical 6.00 - 0.80 = 5.20; no free-end doorway,
#              no jamb stub listed: the fix does not touch it.
def jamb(stub=0.06, faces=(1, -1), at=0.10, record=False, leaf=0.69, p_from=0.95, hinge=(3.0, 0.20)):
    fx = doorway(leaf=None, p_from=p_from)
    if leaf:
        fx.doors.append({"c": hinge, "r": leaf})
    if record:
        fx.band("J", 0.10, (3.0, 0.10), (3.0, 0.10 + stub))
    else:
        for side in faces:
            fx.faces.append(((3.0 + 0.05 * side, at), (3.0 + 0.05 * side, at + stub)))
    return fx


def _p(r):
    return [x for x in r["runs"] if x["run_id"] == "P"][0]


@pytest.mark.parametrize("xf", XFORMS)
def test_t169_jamb_stub_stays_wall(xf):
    r = run(jamb(), **xf)
    assert fam(r)["0.10"] == pytest.approx(3.90, abs=TOL)                          # the architectural run unchanged
    assert fam(r, "physical_blockwork_lm")["0.10"] == pytest.approx(3.11, abs=1e-6)
    assert len(r["doorways"]) == 1
    d = r["doorways"][0]
    assert d["gap_m"] == pytest.approx(0.79, abs=1e-4) and d["face_to_face_m"] == pytest.approx(0.85, abs=1e-4)
    assert d["jamb_stub"]["status"] == "WALL" and d["jamb_stub"]["basis"] == "FACE_LINES"
    assert d["jamb_stub"]["stub_m"] == pytest.approx(0.06, abs=1e-4)
    assert [s["stub_m"] for s in r["jamb_stubs"]] == [pytest.approx(0.06, abs=1e-4)]
    p = _p(r)
    assert p["openings_lm"] == pytest.approx(0.79, abs=1e-4) and p["ends"][0] == "T_STEM"
    assert p["physical_blockwork_lm"] + p["openings_lm"] == pytest.approx(p["arch_run_lm"], abs=1e-6)
    assert r["identity"]["status"] == "PASS", r["identity"]


@pytest.mark.parametrize("xf", [dict(), dict(rot=-121.0, mirror=True), dict(unit=1.0, shift=(0.25, -0.04))])
def test_t169_short_one_face_and_floating_are_listed_not_wall(xf):
    short = run(jamb(stub=0.03), **xf)
    assert short["doorways"][0]["gap_m"] == pytest.approx(0.85, abs=1e-4)
    assert fam(short, "physical_blockwork_lm")["0.10"] == pytest.approx(3.05, abs=1e-6)
    assert short["jamb_stubs"][0]["status"] == "BELOW_L-P9-04_LISTED"
    assert short["jamb_stubs"][0]["stub_m"] == pytest.approx(0.03, abs=1e-4)
    one = run(jamb(faces=(1,)), **xf)
    assert one["doorways"][0]["gap_m"] == pytest.approx(0.85, abs=1e-4)
    assert one["jamb_stubs"][0]["status"] == "ONE_FACE_LISTED"
    assert fam(one, "physical_blockwork_lm")["0.10"] == pytest.approx(3.05, abs=1e-6)
    fl = run(jamb(at=0.30), **xf)
    assert fl["doorways"][0]["gap_m"] == pytest.approx(0.85, abs=1e-4) and fl["jamb_stubs"] == []
    assert "jamb_stub" not in fl["doorways"][0]


@pytest.mark.parametrize("xf", [dict(), dict(rot=37.0), dict(mirror=True), dict(unit=1.0, shift=(0.25, -0.04))])
def test_t169_stub_as_its_own_record_counted_once(xf):
    r = run(jamb(record=True), **xf)
    assert fam(r)["0.10"] == pytest.approx(3.90, abs=1e-6)
    assert fam(r, "physical_blockwork_lm")["0.10"] == pytest.approx(3.11, abs=1e-6)
    d = r["doorways"][0]
    assert d["gap_m"] == pytest.approx(0.79, abs=1e-4)
    assert d["jamb_stub"]["basis"] == "WALL_RECORD" and d["jamb_stub"]["record_id"] == "J"
    assert r["identity"]["status"] == "PASS", r["identity"]


def test_t169_short_record_stub_never_counted_twice():
    """a 0.03 wall record on the face (under L-P9-04 but a record V1 measures): the end stops at it, run 3.90 once."""
    r = run(jamb(stub=0.03, record=True))
    assert fam(r)["0.10"] == pytest.approx(3.90, abs=1e-6)
    assert r["doorways"][0]["gap_m"] == pytest.approx(0.82, abs=1e-4)
    assert r["jamb_stubs"][0]["status"] == "WALL" and r["jamb_stubs"][0]["basis"] == "WALL_RECORD"
    assert fam(r, "physical_blockwork_lm")["0.10"] == pytest.approx(3.08, abs=1e-6)


def test_t169_door_record_fits_the_gap_between_jambs():
    fx = jamb(leaf=None, p_from=0.96)
    fx.opening("D1", "DOOR", 0.80, (3.0, 0.56))
    r = run(fx)
    assert r["doorways"][0]["evidence"] == "DOOR_RECORD" and r["doorways"][0]["gap_m"] == pytest.approx(0.80, abs=1e-4)
    p = _p(r)
    assert p["arch_run_lm"] == pytest.approx(3.90, abs=1e-6)
    assert p["openings_lm"] == pytest.approx(0.80, abs=1e-4)
    assert p["physical_blockwork_lm"] == pytest.approx(3.10, abs=1e-4)


@pytest.mark.parametrize("xf", XFORMS)
def test_t169_mid_wall_door_untouched(xf):
    fx = Fx().band("M", 0.20, (0.0, 0.0), (6.0, 0.0), faces=[(0.0, 2.0), (2.85, 6.0)])
    fx.opening("D1", "DOOR", 0.80, (2.45, 0.0))
    r = run(fx, **xf)
    assert fam(r)["0.20"] == pytest.approx(6.0, abs=TOL)
    assert fam(r, "physical_blockwork_lm")["0.20"] == pytest.approx(5.20, abs=1e-6)
    assert r["doorways"] == [] and r["jamb_stubs"] == []


def test_t169_no_stub_doorway_unchanged():
    """the T-125 doorway fixture (no jamb drawn): byte-identical figures, no jamb_stub key."""
    r = run(doorway())
    assert r["doorways"][0]["gap_m"] == pytest.approx(0.80, abs=1e-4) and "jamb_stub" not in r["doorways"][0]
    assert r["jamb_stubs"] == [] and fam(r, "physical_blockwork_lm")["0.10"] == pytest.approx(3.10, abs=TOL)


def test_t169_policy_names_the_stub_convention():
    assert V2.policy_record()["jamb_stub_min_m"] == 0.05 == V2.MIN_STRETCH_M
