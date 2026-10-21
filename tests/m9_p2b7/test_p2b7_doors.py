"""Phase 2B-7 acceptance (written before the engine change): ARCH_TAKEOFF_V2.7 takes a door's structural opening
from its own jamb evidence when the rest of the wall gap is proven wall on both faces (a verified wall return or a
junction mouth), and keeps a genuinely wider opening (open side, column, glazed side panel, a wall on one face only)
with its reason. Every expected value is derived by hand from the fixture coordinates (tests/m9_p2b7/p2b7_fixtures);
ARCH_TAKEOFF_V2.6 keeps its own as-found values (tests/m9_p2b6/test_p2b6_found_defects.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_doors")


@pytest.fixture(scope="module")
def crossing(work):
    return R.run(F.door_plan(work / "CROSSING.dxf", "CROSSING"), work / "o_crossing", roles=F.ROLES, facts=True)


def _door(out):
    d = R.openings(out, "DOOR")
    assert len(d) == 1
    return d[0]


def test_crossing_door_takes_its_jamb_span(crossing):
    """CROSSING: wall gap 1.027 m (x 1000 .. 2027); the symbol's jamb lines at 1000 and 1800; the rest is a 77 mm
    return drawn on both faces and the 150 mm partition's mouth on both faces -> proven wall. Structural opening
    0.80 m; the door fits it strictly (hinge at the jamb, leaf 0.70 m in a 0.80 m frame), so it is not held."""
    d = _door(crossing)
    assert round(d["width_m"], 6) == 0.80
    assert not d.get("door_fit_review")
    rec = d["opening_v27"]
    assert rec["decision"] == "NARROWED_TO_JAMB_SPAN"
    assert round(rec["wall_gap_m"], 6) == 1.027 and round(rec["jamb_span_m"], 6) == 0.80
    assert [x["nature"] for x in rec["remainder"]] == ["WALL_BOTH_FACES"]
    assert round(rec["remainder"][0]["m"], 6) == 0.227
    # the opening's position is the middle of the jamb span at mid wall: (1.400, 0.100) m
    assert d["position"]["centre_m"] == [1.4, 0.1]


def test_crossing_quantities_from_the_jamb_span(crossing):
    """bath = x 200 .. 1877, y 200 .. 3200 (1.677 x 3.0 m), wall heights 3.0 / tile 2.4, door 2.10 m (facts):
    threshold 0.80 x 0.20 = 0.16 m2; doorway waterproofing 0.16 m2; plaster (1.677 + 3.0) x 2 x 3.0 - 0.80 x 2.10
    = 26.382 m2; wall tile 9.354 x 2.4 - 0.80 x 2.10 = 20.7696 m2; skirting 9.354 - 0.80 = 8.554 m; door opening plaster
    2 x 2.10 x 0.20 + 0.80 x 0.20 = 1.00 m2; waterproofing upturn: the wall boundary 9.354 - 0.80 = 8.554 m x 0.20 m
    = 1.7108 m2 (the 77 mm return is wall, no longer an unresolved piece). The rooms themselves are unchanged."""
    out = crossing
    assert R.net(out, "FIN.MARBLE.THRESHOLD") == 0.16
    assert R.net(out, "FIN.WP.DOORWAY", "Bathroom") == 0.16
    assert R.net(out, "FIN.PLASTER", "Bathroom") == 26.382
    assert R.net(out, "FIN.WALL.TILE", "Bathroom") == 20.7696
    assert R.net(out, "FIN.SKIRTING", "Bathroom") == 8.554
    assert R.net(out, "FIN.PLASTER", "door opening") == 1.0
    assert R.net(out, "FIN.WP.WALL_UPTURN", "Bathroom") == 1.7108
    assert [round(r["area_m2"], 6) for r in R.room(out, "Bathroom")] == [round(1.677 * 3.0, 6)]
    assert [round(r["area_m2"], 6) for r in R.room(out, "Bedroom")] == [round(2.173 * 3.0, 6)]
    # the door is released: one external aluminium door (exterior beyond the south wall)
    assert R.net(out, "DOOR.EXTERNAL.ALUMINIUM") == 1.0
    assert not [ln for ln in R.lines(out) if ln["item_code"] == "FIN.SKIRTING" and
                ln["evidence_state"] == "BOUNDED_EXPOSURE"]


@pytest.mark.parametrize("variant", ["OPEN_SIDE", "COLUMN_JAMB", "SIDE_PANEL", "ONE_FACE"])
def test_a_wider_opening_is_kept_with_its_reason(work, variant):
    """the 0.80 m door in a wider gap whose rest is NOT proven wall on both faces: open on both faces (1.027 m gap),
    an undrawn 77 mm strip against a column jamb (0.877 m gap), a glazed side panel, a wall on one face only. The
    structural opening stays the whole gap and the remainder's nature is named; every quantity is V2.6's (a door
    the V2.6 review fit held stays held, with the reason)."""
    dxf = F.door_plan(work / f"{variant}.dxf", variant)
    a = R.run(dxf, work / f"o_{variant}_26", roles=F.ROLES, facts=True, method=R.V26)
    b = R.run(dxf, work / f"o_{variant}_27", roles=F.ROLES, facts=True)
    d = _door(b)
    assert round(d["width_m"], 6) == F.TRUTH[variant]["structural_m"]
    assert bool(d.get("door_fit_review")) == bool(_door(a).get("door_fit_review"))
    rec = d["opening_v27"]
    assert rec["decision"] == "WIDER_OPENING_KEPT"
    assert round(rec["jamb_span_m"], 6) == F.TRUTH[variant]["door_m"]
    assert [x["nature"] for x in rec["remainder"]] == [F.TRUTH[variant]["remainder"]]
    assert R.invariant(a, b, tol=1e-9)


@pytest.mark.parametrize("variant", ["PLAIN", "TEE", "DOUBLE"])
def test_no_change_where_the_gap_is_the_door(work, variant):
    """the wall gap already is the door's own opening (PLAIN 0.80, TEE 0.80: the junction mouth is outside the gap,
    DOUBLE 1.60 with no jamb line between the leaves): nothing is narrowed, every quantity is V2.6's."""
    dxf = F.door_plan(work / f"{variant}.dxf", variant)
    a = R.run(dxf, work / f"o_{variant}_26", roles=F.ROLES, facts=True, method=R.V26)
    b = R.run(dxf, work / f"o_{variant}_27", roles=F.ROLES, facts=True)
    d = _door(b)
    assert round(d["width_m"], 6) == F.TRUTH[variant]["door_m"]
    assert (d.get("opening_v27") or {}).get("decision") in (None, "GAP_IS_THE_DOOR")
    assert R.invariant(a, b, tol=1e-9)


@pytest.mark.parametrize("kind", ["translate", "rot30", "rot90", "mirror", "metres", "rot37_metres", "reorder",
                                  "nest"])
def test_crossing_invariant_under_transformations(work, crossing, kind):
    """CROSSING moved, turned 30 / 90 / 37 degrees, mirrored, drawn in metres, its entities reordered, nested in two
    levels of blocks: the jamb span is found every time and every quantity equals the untransformed run."""
    base = work / "CROSSING.dxf"
    out = R.run(F.variant(base, work / f"CROSSING_{kind}.dxf", kind), work / f"o_crossing_{kind}", roles=F.ROLES,
                facts=True)
    assert round(_door(out)["width_m"], 6) == 0.80
    assert R.invariant(crossing, out, tol=1e-5), R.diff(crossing, out, 1e-5)


def test_crossing_door_opening_record(crossing):
    """Section 4: the door's opening values kept apart (UP-DOOR-OPEN-003, knowledge 1.2.0). The external door of
    CROSSING: structural opening 0.80 m (jamb span); leaf 0.70 m (the swing radius); frame not drawn (an exploded
    symbol); clear passage not established; owner minimum 1.00 m (ordinary external door); allowance not
    established (the 1.1.0 registry's 0.10 m requires confirmation - never imposed). Shortfall 0.20 m against the
    structural opening, 0.30 m against the leaf: below the minimum on both readings; the enlargement is proposed,
    never applied, and the reference of the minimum is an owner question."""
    rows = [r for r in R.load(crossing, "DOOR_SCENARIOS.json")["doors"]["rows"]]
    assert len(rows) == 1
    o = rows[0]["opening_record"]
    assert o["category"] == "EXTERNAL_ALUMINIUM"
    assert o["structural_opening_m"] == 0.8 and o["structural_opening_source"].startswith("JAMB_SPAN")
    assert o["door_leaf_m"] == [0.7]
    assert o["frame_m"] is None and o["clear_passage_m"] is None
    assert o["owner_minimum_m"] == 1.0
    assert o["allowance"]["state"] == "NOT_ESTABLISHED" and o["allowance"]["value_m"] is None
    assert o["allowance"]["registry_1_1_0_m"] == 0.1
    i = {x["reading"]: x for x in o["readings"]}
    assert i["STRUCTURAL_OPENING"]["shortfall_m"] == 0.2 and i["STRUCTURAL_OPENING"]["proposed_enlargement_m"] == 0.2
    assert i["DOOR_LEAF"]["shortfall_m"] == 0.3
    assert i["DOOR_LEAF"]["proposed_enlargement_m"] == {"low": 0.2, "high_with_registry_allowance": 0.3}
    assert i["CLEAR_PASSAGE"]["state"] == "NOT_ESTABLISHED"
    assert o["status"] == "BELOW_MINIMUM_ON_EVERY_READING"
    assert o["review_status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"
    assert o["owner_question"] == "OQ-05"
