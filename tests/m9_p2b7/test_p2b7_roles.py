"""Phase 2B-7 acceptance (written before the engine change): ARCH_TAKEOFF_V2.7 reads a layer's role from what its
geometry does - a single exploded door is a DOOR (its swing never bounds a floor), one or two glazing lines in a
door-free wall gap are a WINDOW, a column rectangle of any orientation drawn as one polyline or four LINEs is a
COLUMN - and refuses, with an explicit record, where the geometry does not decide (a drain is never a column, a
layer carrying a door and a window is not given either role). Truth by hand from the coordinates."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402

PLAN_ROLES = ("A-WALL=WALL", "A-GLAZ=WINDOW", "A-DOOR=DOOR")    # the plan's own layers; the adversary is inferred


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_roles")


def _refusals(out, layer):
    return [r for r in R.load(out, "CORRECTIONS_V2_7.json")["refusals"] if r["layer"] == layer]


def test_exploded_single_door_is_a_door(work):
    """PLAIN with every role inferred: the door layer holds one exploded door (jamb and frame lines, leaf, 90-degree
    swing hinged at the wall gap's jamb) -> DOOR; the east window's single glazing line in a door-free gap ->
    WINDOW. The room is the 4.00 x 3.00 m interior (V2.6: 12 - pi 0.49 / 4 and its perimeter + the swing)."""
    out = R.run(F.door_plan(work / "PLAIN.dxf", "PLAIN"), work / "o_plain")
    roles = R.roles_of(out)
    assert roles["A-DOOR"] == "DOOR" and roles["A-GLAZ"] == "WINDOW"
    r = R.room(out, "Bathroom")[0]
    assert (r["area_m2"], r["perimeter_lm"]) == (12.0, 14.0)
    kinds = sorted((o["kind"], round(o["width_m"], 6)) for o in R.openings(out))
    assert kinds == [("DOOR", 0.8), ("WINDOW", 0.6)]


@pytest.mark.parametrize("kind", ["rot30", "mirror", "metres", "rot37_metres", "nest"])
def test_exploded_single_door_invariant(work, kind):
    base = F.door_plan(work / f"PLAIN_{kind}.dxf", "PLAIN")
    a = R.run(base, work / f"o_plain_{kind}_a")
    b = R.run(F.variant(base, work / f"PLAIN_{kind}_v.dxf", kind), work / f"o_plain_{kind}_b")
    assert R.roles_of(b)["A-DOOR"] == "DOOR" and R.roles_of(b)["A-GLAZ"] == "WINDOW"
    assert R.invariant(a, b, tol=1e-5), R.diff(a, b, 1e-5)


def test_single_door_block_is_a_door(work):
    """B10: one door INSERT on A-DOOR with every role inferred -> DOOR (V2.6: OTHER, the opening a PASSAGE)."""
    out = R.run(F.arc_room(work / "B10.dxf"), work / "o_b10")
    assert R.roles_of(out)["A-DOOR"] == "DOOR"
    assert [(o["kind"], round(o["width_m"], 6)) for o in R.openings(out)] == [("DOOR", 0.8)]


@pytest.mark.parametrize("kind", ["WARDROBE", "THRESHOLD"])
def test_lookalikes_stay_other(work, kind):
    """a wardrobe leaf + swing hinged off a wall face (not at a wall-gap jamb), a threshold line across a door gap:
    never DOOR / WINDOW; the room is unchanged (12.00 m2, 14.00 m), with every role inferred and with the plan's
    own layers declared."""
    lay = {"WARDROBE": "A-FURN", "THRESHOLD": "A-THR"}[kind]
    dxf = F.lookalike(work / f"L_{kind}.dxf", kind)
    for tag, roles in (("inf", None), ("dec", PLAN_ROLES)):
        out = R.run(dxf, work / f"o_L_{kind}_{tag}", roles=roles)
        assert R.roles_of(out)[lay] == "OTHER"
        r = R.room(out, "Bedroom")[0]
        assert (r["area_m2"], r["perimeter_lm"]) == (12.0, 14.0)


def test_a_layer_holding_a_door_and_a_window_is_refused(work):
    """MIXED: one layer A-OPEN draws the door symbol and the east window's glazing. Neither role explains it: the
    layer is refused (OTHER) with an explicit record and a reviewer item naming the two roles; the swing does not
    bound the floor (12.00 m2, 14.00 m; V2.6 typed the layer WINDOW and carved the floor)."""
    out = R.run(F.door_plan(work / "MIXED.dxf", "MIXED"), work / "o_mixed")
    assert R.roles_of(out)["A-OPEN"] == "OTHER"
    ref = _refusals(out, "A-OPEN")
    assert len(ref) == 1 and ref[0]["code"] == "LAYER_ROLE_REFUSED" and set(ref[0]["candidates"]) == {"DOOR", "WINDOW"}
    assert any("A-OPEN" in str(u.get("reason")) and "LAYER_ROLE_REFUSED" in str(u.get("reason"))
               for u in R.unresolved(out))
    r = R.room(out, "Bedroom")[0]
    assert (r["area_m2"], r["perimeter_lm"]) == (12.0, 14.0)


@pytest.mark.parametrize("kind", ["DRAIN", "THREE_DRAINS", "DRAIN_AT_WALL"])
def test_drains_are_never_columns(work, kind):
    """hatched 0.15 m squares (a drain grating) - one free, three free, one touching the wall: never COLUMN (too
    small for a column: under a 0.20 x 0.20 m section); the room is 12.00 m2 / 14.00 m. Three of them (V2.6: typed
    COLUMN by the count rule, deducted) are refused with a record."""
    out = R.run(F.lookalike(work / f"L_{kind}.dxf", kind), work / f"o_L_{kind}", roles=PLAN_ROLES)
    assert R.roles_of(out)["P-DRAIN"] == "OTHER"
    r = R.room(out, "Bedroom")[0]
    assert (r["area_m2"], r["perimeter_lm"]) == (12.0, 14.0)
    if kind == "THREE_DRAINS":
        ref = _refusals(out, "P-DRAIN")
        assert ref and ref[0]["code"] == "COLUMN_ROLE_REFUSED" and "TOO_SMALL" in ref[0]["reason"]


@pytest.mark.parametrize("kind", ["COLUMN", "FOUR_LINE_COLUMNS", "TURNED_COLUMNS"])
def test_columns_of_any_drawing(work, kind):
    """COLUMN: one hatched 0.30 m square of four LINEs against the south wall -> 12 - 0.09 = 11.91 m2, the
    boundary round its two sides 14 + 0.60 = 14.60 m. FOUR_LINE_COLUMNS: three hatched 0.40 m squares of four LINEs
    (two against walls, one free) -> 12 - 3 x 0.16 = 11.52 m2, boundary 14 + 4 x 0.40 + 1.60 (the hole) = 17.20 m.
    TURNED_COLUMNS: three 0.40 m squares turned 30 degrees, all free -> 11.52 m2, three holes, 14 + 3 x 1.60 m."""
    out = R.run(F.lookalike(work / f"L_{kind}.dxf", kind), work / f"o_L_{kind}", roles=PLAN_ROLES)
    area, per, role = F.LOOK_TRUTH[kind]
    assert R.roles_of(out)["S-COL"] == role
    r = R.room(out, "Bedroom")[0]
    assert abs(r["area_m2"] - area) < 1e-6
    if per is not None:
        assert abs(r["perimeter_lm"] - per) < 1e-6
    assert r["obstructions"] == {"COLUMN": 0, "FOUR_LINE_COLUMNS": 1, "TURNED_COLUMNS": 3}[kind]


@pytest.mark.parametrize("kind", ["FOUR_LINES", "TURNED"])
def test_villa_columns_redrawn(work, kind):
    """the synthetic villa with its three 0.40 m columns drawn as four LINEs each, or turned 30 degrees about their
    centres, every role inferred: the columns are found and every room keeps the villa's hand truth (LIVING 66.00 -
    2 x 0.16 m2, BEDROOM 13.44 - 0.16 m2; tools/arch_synth truth)."""
    from tools import arch_synth as AS
    t = AS.TRUTH["GF"]["rooms"]
    out = R.run(F.column_villa(work / f"villa_{kind}.dxf", kind), work / f"o_villa_{kind}")
    assert R.roles_of(out)["A-COL"] == "COLUMN"
    got = {r["codes"][0]: r for r in R.rooms(out) if r["floor"] == "GF" and r.get("codes")}
    assert abs(got["LIVING"]["area_m2"] - t["LIVING"]["net_m2"]) < 1e-6
    assert abs(got["BEDROOM"]["area_m2"] - t["BEDROOM"]["net_m2"]) < 1e-6
    assert sum(r.get("obstructions") or 0 for r in R.rooms(out)) == 3


def test_turned_villa_keeps_its_columns(work):
    """D-P6-04: the whole villa turned 30 degrees inside its frame, roles inferred: the three columns are found and
    every quantity equals the unturned villa's (V2.6: 0 columns, plaster -10.4 % in one room)."""
    from tools import arch_synth as AS
    base = work / "villa.dxf"
    AS.villa(base)
    a = R.run(base, work / "o_villa")
    b = R.run(F.variant(base, work / "villa_rot30.dxf", "rot30"), work / "o_villa_rot30")
    assert sum(r.get("obstructions") or 0 for r in R.rooms(b)) == 3
    assert R.invariant(a, b, tol=1e-5), R.diff(a, b, 1e-5)


def test_single_free_standing_column_is_refused(work):
    """benchmark B04: one hatched 0.40 m square standing free in a bedroom (one instance, bound to no wall): a
    column, a planter or a fixture is not decided by geometry - refused with a record (declare --layer-roles); the
    room keeps its V2.6 reading."""
    import bench_cases as BC
    import bench_drawings as BD
    BD.dxf(BC.BY_ID["B04"], work / "B04.dxf")
    a = R.run(work / "B04.dxf", work / "o_b04_26", method=R.V26)
    b = R.run(work / "B04.dxf", work / "o_b04_27")
    ref = _refusals(b, "A-COL")
    assert ref and ref[0]["code"] == "COLUMN_ROLE_REFUSED" and "FREE_STANDING" in ref[0]["reason"]
    assert R.room(a, "Bedroom")[0]["area_m2"] == R.room(b, "Bedroom")[0]["area_m2"]


@pytest.mark.parametrize("kind", ["AT_WALL", "FREE_ROW"])
def test_a_row_of_aligned_columns_stays_columns(work, kind):
    """found on the reference plan (Phase 2B-7 validation): columns standing in one row put their faces on two lines
    0.40 m apart that span the whole row - one long band of the column layer. Only the columns' own sides are drawn
    (no wall face runs between them), so the layer is searched for columns (arch_v27.paired_long_m, not the band
    span) and stays COLUMN; the hall is the hand truth (12.00 x 4.00 m less the columns, holes in the perimeter).
    V2.6 keeps the columns too, but types the exploded door a window and subtracts its swing (pi x 0.70^2 / 4)."""
    dxf = F.column_row(work / f"ROW_{kind}.dxf", kind)
    b = R.run(dxf, work / f"o_row_{kind}")
    assert R.roles_of(b)["A-COL"] == "COLUMN" and R.roles_of(b)["A-WALL"] == "WALL"
    hall = R.room(b, "Bedroom")
    assert len(hall) == 1
    assert abs(hall[0]["area_m2"] - F.COLUMN_ROW_TRUTH[kind]["area_m2"]) < 1e-6
    assert abs(hall[0]["perimeter_lm"] - F.COLUMN_ROW_TRUTH[kind]["perimeter_m"]) < 1e-6
    a = R.run(dxf, work / f"o_row_{kind}_26", method=R.V26)
    assert R.roles_of(a)["A-COL"] == "COLUMN"
    assert abs(R.room(a, "Bedroom")[0]["area_m2"] - (F.COLUMN_ROW_TRUTH[kind]["area_m2"] - math.pi * 0.49 / 4)) < 1e-4


@pytest.mark.parametrize("kind", ["rot30", "mirror", "metres", "nest"])
def test_column_row_invariant(work, kind):
    base = F.column_row(work / f"ROWI_{kind}.dxf", "AT_WALL")
    a = R.run(base, work / f"o_rowi_{kind}_a")
    b = R.run(F.variant(base, work / f"ROWI_{kind}_v.dxf", kind), work / f"o_rowi_{kind}_b")
    assert R.invariant(a, b, tol=1e-5), R.diff(a, b, 1e-5)
