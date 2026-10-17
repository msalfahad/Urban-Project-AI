"""Phase 2B-6: defects of ARCH_TAKEOFF_V2.6 found by the controlled experiments, asserted AS FOUND next to their hand
truth (research/urban_m9_p2b6/ENGINEERING_DEFECT_REGISTER.md). A method that corrects one of them is a new opt-in
method; these assertions then move to that method's tests with the truth, and V2.6 keeps these.

    D-P6-01  a held door takes its wall gap's width, not its symbol's (the reference plan's D-V26-06 residual)
    D-P6-02  a single exploded door symbol (jambs, frames, leaf, swing) types its layer WINDOW: the swing bounds the
             room
    D-P6-03  three hatched floor-drain squares type their layer COLUMN: deducted, faces finished
    D-P6-04  a plan turned 30 degrees inside its sheet loses its inferred columns
    D-P6-05  a plan nested in blocks holds every door (frame evidence read across the whole occurrence)
    D-P6-06  a plan turned 37 degrees and drawn in metres gets a zero-length waterproofing termination line
    D-P6-07  an unlabelled space holding only a wash basin is typed a wet room
and, for contrast, the transformations under which every quantity is invariant (Experiment F)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b6_fixtures as F                                     # noqa: E402
import p2b6_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b6_defects")


def _room(out, name):
    return [r for r in R.rooms(out) if r["name_en"].startswith(name)]


def _net(out, code, room=None):
    return round(sum(ln["measured_net"] or 0.0 for ln in R.lines(out) if ln["item_code"] == code and
                     (room is None or ((ln.get("location") or {}).get("room_name_en") or "").startswith(room))), 6)


def test_d_p6_01_held_door_takes_the_wall_gap(work):
    """CROSSING: the symbol's jamb lines are 0.80 m apart in a 1.027 m wall gap (a 77 mm return, then a 150 mm
    partition crossing the wall). Truth (hand): door 0.80 m; threshold 0.80 x 0.20 = 0.16 m2; bath plaster
    (1.677 + 3.0) x 2 x 3.0 - 0.80 x 2.10 = 26.382 m2; wall tile 9.354 x 2.4 - 1.68 = 20.7696 m2; skirting
    9.354 - 0.80 = 8.554 m; door reveal plaster 2 x 2.10 x 0.20 + 0.80 x 0.20 = 1.00 m2."""
    out = R.run(F.door_plan(work / "CROSSING.dxf", "CROSSING"), work / "o_crossing", roles=F.ROLES, facts=True)
    door = [o for o in R.load(out, "ARCH_OPENINGS.json")["openings"] if o["kind"] == "DOOR"]
    assert len(door) == 1 and door[0]["door_fit_review"]                       # held (D-V26-06)
    assert round(door[0]["width_m"], 3) == 1.027                               # truth 0.80
    assert _net(out, "FIN.MARBLE.THRESHOLD") == 0.2054                         # truth 0.16
    assert _net(out, "FIN.PLASTER", "Bathroom") == 26.2203                     # truth 26.382
    assert _net(out, "FIN.WALL.TILE", "Bathroom") == 20.6079                   # truth 20.7696
    assert _net(out, "FIN.SKIRTING", "Bathroom") == 8.477                      # truth 8.554
    assert _net(out, "FIN.PLASTER", "door opening") == 1.0454                  # truth 1.00
    # the rooms themselves are right: the partition bounds both
    assert [round(r["area_m2"], 6) for r in _room(out, "Bathroom")] == [F.TRUTH["CROSSING"]["bath_m2"]]


def test_d_p6_02_exploded_door_typed_window(work):
    """PLAIN with the layer roles inferred: the door layer (4 jamb / frame lines, a leaf, a swing - a single door)
    falls under the window rule (lines inside the wall gaps), the swing bounds the room. Truth: 12.00 m2, perimeter
    14.00 m (declared roles give exactly that); as found: 12 - pi 0.7^2 / 4 and 14 - 0.7 + 0.7 + pi 0.7 / 2."""
    dxf = F.door_plan(work / "PLAIN.dxf", "PLAIN")
    inf = R.run(dxf, work / "o_plain_inferred")
    dec = R.run(dxf, work / "o_plain_declared", roles=F.ROLES)
    assert R.roles_of(inf)["A-DOOR"] == "WINDOW"
    a, p = _room(inf, "Bathroom")[0]["area_m2"], _room(inf, "Bathroom")[0]["perimeter_lm"]
    assert abs(a - (12.0 - math.pi * 0.7 ** 2 / 4)) < 1e-5 and abs(p - (14.0 + math.pi * 0.7 / 2)) < 1e-5
    assert (_room(dec, "Bathroom")[0]["area_m2"], _room(dec, "Bathroom")[0]["perimeter_lm"]) == (12.0, 14.0)


def test_d_p6_03_three_drains_typed_columns(work):
    """three hatched 0.15 m floor-drain squares on their own layer: typed COLUMN by the count rule (three filled
    squares), deducted (3 x 0.0225 m2) and their faces added to the room boundary (3 x 0.60 m). Truth: they are
    drains - 12.00 m2, 14.00 m."""
    # the plan's own layers declared; the drain layer is left to the inference
    out = R.run(F.lookalike(work / "DRAINS.dxf", "THREE_DRAINS"), work / "o_drains", roles=F.ROLES)
    assert R.roles_of(out)["P-DRAIN"] == "COLUMN"
    r = _room(out, "Bedroom")[0]
    assert (r["area_m2"], r["perimeter_lm"]) == (round(12.0 - 3 * 0.0225, 6), 14.0 + 1.8)


def test_d_p6_04_turned_plan_loses_inferred_columns(work):
    """the synthetic villa turned 30 degrees inside its frame: with inferred roles its three 0.40 m columns are no
    longer found (the column rule reads axis-aligned rectangles); with declared roles every quantity is unchanged."""
    from tools import arch_synth as AS
    base = work / "villa.dxf"
    AS.villa(base)
    turned = F.variant(base, work / "villa_rot30.dxf", "rot30")
    b, t = R.run(base, work / "o_villa"), R.run(turned, work / "o_villa_rot30")
    nb = sum(r.get("obstructions") or 0 for r in R.rooms(b))
    nt = sum(r.get("obstructions") or 0 for r in R.rooms(t))
    assert (nb, nt) == (3, 0)
    roles = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")
    assert R.totals(R.run(base, work / "o_villa_d", roles=roles)) == \
        R.totals(R.run(turned, work / "o_villa_rot30_d", roles=roles))


def test_d_p6_05_nested_plan_holds_every_door(work):
    """the villa's plan moved into two levels of blocks: every quantity is unchanged except the door sets - the
    frame evidence spans the whole occurrence, so every internal door is held (DOOR_CLOSURE_FRAME_DISAGREE)."""
    from tools import arch_synth as AS
    base = work / "villa_n.dxf"
    AS.villa(base)
    a = R.totals(R.run(base, work / "o_villa_n"))
    b = R.totals(R.run(F.variant(base, work / "villa_nest.dxf", "nest"), work / "o_villa_nest"))
    diff = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    assert diff == {("DOOR.INTERNAL.PVC", "-")} and a[("DOOR.INTERNAL.PVC", "-")] == (5.0, 5)
    assert ("DOOR.INTERNAL.PVC", "-") not in b


def test_d_p6_06_zero_length_termination_turned_metres(work):
    dxf = F.door_plan(work / "PLAIN_m.dxf", "PLAIN")
    a = R.run(dxf, work / "o_plain_mm", roles=F.ROLES)
    b = R.run(F.variant(dxf, work / "PLAIN_r37m.dxf", "rot37_metres"), work / "o_plain_r37m", roles=F.ROLES)
    term = [ln for ln in R.lines(b) if ln["item_code"] == "FIN.WP.TERMINATION"]
    assert [ln["calculation"]["inputs"]["length_m"] for ln in term] == [0.0]
    assert not [ln for ln in R.lines(a) if ln["item_code"] == "FIN.WP.TERMINATION"]
    # every quantity is otherwise the same (to 1e-5: a turned polygon in metres rounds at the sixth decimal)
    ta, tb = R.totals(a), {k: v for k, v in R.totals(b).items() if k[0] != "FIN.WP.TERMINATION"}
    assert set(ta) == set(tb) and all(ta[k][1] == tb[k][1] and abs(ta[k][0] - tb[k][0]) <= 1e-5 for k in ta)


def test_d_p6_07_basin_only_space_typed_wet(work):
    """an unlabelled lobby holding only a WASH block is typed a wet room from the fixture (owner statement: a basin
    alone does not make a space wet; the type is for review)."""
    out = R.run(F.basin_plan(work / "BASIN.dxf"), work / "o_basin", roles=F.ROLES)
    lobby = [r for r in R.rooms(out) if r.get("label_source") == "FIXTURES"]
    assert len(lobby) == 1 and lobby[0]["kind"] == "WET" and lobby[0]["name_en"].startswith("Bathroom")
    assert {x["fixture"] for x in lobby[0]["evidence"]["fixtures"]} == {"BASIN"}


@pytest.mark.parametrize("kind", ["translate", "rot30", "rot90", "mirror", "metres", "reorder", "nest"])
def test_invariant_quantities_crossing(work, kind):
    """CROSSING with declared roles: every quantity is invariant under each transformation (Experiment F)."""
    base = F.door_plan(work / f"C_{kind}.dxf", "CROSSING")
    a = R.totals(R.run(base, work / f"o_c_{kind}_a", roles=F.ROLES, facts=True))
    b = R.totals(R.run(F.variant(base, work / f"C_{kind}_v.dxf", kind), work / f"o_c_{kind}_b", roles=F.ROLES,
                       facts=True))
    bad = {k: (a.get(k), b.get(k)) for k in set(a) | set(b)
           if a.get(k, (0, 0))[1] != b.get(k, (0, 0))[1] or abs(a.get(k, (0, 0))[0] - b.get(k, (0, 0))[0]) > 1e-5}
    assert not bad, bad
