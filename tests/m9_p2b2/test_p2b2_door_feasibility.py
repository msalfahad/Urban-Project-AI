"""Phase 2B-2 (Part 4): the door feasibility engine - the CAD wall opening against the owner standard (nominal door +
0.10 m), the available nominal under the allowance, the plain wall beyond each jamb and what ends it (column, wall
junction, corner, opening), the larger leaf's swing, the host wall's structural status, the five classes, the four
views never combined, and no proposed modification in the as-drawn quantities. Synthetic plans (mm, wall 0.20 m)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import p2b2_fixtures as F                                     # noqa: E402
from engine.source import door_model as DM                   # noqa: E402

COLUMN_FAR = ((600, 3400),)                                   # a column frame drawn away from the door


def door(**kw):
    return F.party_door(F.two_rooms(**kw))


def test_an_opening_already_large_enough_and_one_exactly_at_the_standard():
    big, exact = door(s0=1500, s1=2700), door(s0=1500, s1=2600)
    assert (big["cad_wall_opening_m"], big["enlargement_m"], big["compliance"], big["feasibility"]) == (
        1.2, 0.0, "MEETS_STANDARD", "STANDARD_FITS_AS_DRAWN")
    assert big["available_nominal_m"] == 1.1                     # the larger door the opening takes (1.20 - 0.10)
    assert (exact["enlargement_m"], exact["feasibility"]) == (0.0, "STANDARD_FITS_AS_DRAWN")
    assert big["view"] == exact["view"] == "OWNER_STANDARD" and "proposed_modification" not in big


def test_openings_10_and_20_cm_undersized():
    a, b = door(s0=1500, s1=2500), door(s0=1500, s1=2400)
    assert (a["enlargement_m"], a["feasibility"], a["placements"][0]["placement"]) == (
        0.1, "ENLARGEMENT_GEOMETRICALLY_POSSIBLE", "SPLIT_EQUAL")
    assert (b["enlargement_m"], b["feasibility"]) == (0.2, "ENLARGEMENT_GEOMETRICALLY_POSSIBLE")
    assert b["proposed_modification"]["status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"
    assert b["proposed_modification"]["if_not_approved"]["door_that_fits_m"] == 0.8


def test_bathroom_0_80_needs_0_20_and_is_not_treated_as_fitting():
    """the owner's example: required nominal 0.90 m, required wall opening 1.00 m, CAD 0.80 m -> available nominal
    under the allowance 0.70 m, enlargement 0.20 m, ENLARGEMENT_REQUIRED."""
    r = door(a_word="BATH", s0=1500, s1=2300)
    assert r["category"] == "BATHROOM_PVC"
    assert (r["standard"]["required_nominal_door_m"], r["standard"]["required_wall_opening_m"]) == (0.9, 1.0)
    assert (r["cad_wall_opening_m"], r["available_nominal_m"], r["enlargement_m"]) == (0.8, 0.7, 0.2)
    assert r["compliance"] == "ENLARGEMENT_REQUIRED" and r["feasibility"] != "STANDARD_FITS_AS_DRAWN"
    assert r["standard"]["state"] == "OWNER_STANDARD_ASSUMED"


def test_opening_beside_a_column():
    """a column is the start jamb: the enlargement goes to the masonry side only (the column is never cut); with a
    column at both jambs the opening can only widen by altering structure: engineering review."""
    r = door(columns=((3900, 1100), (600, 3400)))
    assert (r["clearances"]["START"]["constraint"], r["clearances"]["START"]["plain_m"]) == ("COLUMN", 0.0)
    assert r["feasibility"] == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"
    assert r["placements"][0]["placement"] == "END_SIDE" and r["placements"][0]["start_m"] == 0.0
    assert r["proposed_modification"]["dependency_impacts"]["structural"].startswith("STRUCTURAL_INTERFACE_REVIEW")
    r2 = door(columns=((3900, 1100), (3900, 2400)))
    assert r2["feasibility"] == "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW" and r2["placements"] == []
    assert "never recommended" in r2["reasons"][0]


def test_opening_beside_a_non_structural_wall_return():
    """a wall returns 0.10 m from the start jamb (a T-junction on the A face): the 0.10 m minimum pier leaves nothing
    there, the end side has 0.50 m: possible to the end side; with a window 0.10 m beyond the end jamb as well, there
    is no room on either side: constrained (a smaller door, or a redesign)."""
    r = door(a_partition=2500, s0=2800, s1=3700)
    assert (r["clearances"]["START"]["constraint"], r["clearances"]["START"]["plain_m"]) == ("JUNCTION", 0.1)
    assert r["feasibility"] == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE" and r["placements"][0]["placement"] == "END_SIDE"
    g = [((x0, y0), (x1, y1), lay, p) for ((x0, y0), (x1, y1)), lay, p in F.glazing(4000, 4200, 3800, 4100)]
    r2 = door(a_partition=2500, s0=2800, s1=3700, extra_openings=[("WINDOW", "x", 4000, 4200, 3800, 4100, None)],
              extra=g)
    assert r2["feasibility"] == "ENLARGEMENT_CONSTRAINED" and r2["placements"] == []
    assert r2["proposed_modification"]["if_not_approved"]["door_that_fits_m"] == 0.8


def test_opening_at_a_corner():
    r = door(s0=300, s1=1200)
    assert (r["clearances"]["START"]["constraint"], r["clearances"]["START"]["plain_m"]) == ("JUNCTION", 0.1)
    assert r["placements"][0]["placement"] == "END_SIDE"
    # 0.05 m from the corner the opening census reads no band opening: a provisional door, never measured
    p = F.two_rooms(s0=250, s1=1150)
    assert [x["feasibility"] for x in p["rep"]["rows"]] == ["INSUFFICIENT_DRAWING_EVIDENCE"]


def test_door_beside_a_window():
    g = [((x0, y0), (x1, y1), lay, p) for ((x0, y0), (x1, y1)), lay, p in F.glazing(4000, 4200, 2500, 3600)]
    r = door(extra_openings=[("WINDOW", "x", 4000, 4200, 2500, 3600, None)], extra=g)
    end = r["clearances"]["END"]
    assert (end["constraint"], end["plain_m"]) == ("OPENING", 0.1) and end["constraint_id"].startswith("WINDOW")
    assert r["placements"][0]["placement"] == "START_SIDE"


def test_door_opening_into_a_corridor_swing_clearance():
    """a 0.95 m corridor: the drawn 0.90 m leaf swings clear, the owner-standard 1.00 m leaf hits the far wall."""
    r = door(b_word="CORRIDOR", b_right=5150)
    assert r["swing"]["state"] == "CONFLICT" and r["swing"]["as_drawn"] == "CLEAR"
    assert r["swing"]["leaf_m"] == 1.0 and r["feasibility"] == "ENLARGEMENT_CONSTRAINED"
    # a fixture inside the larger swing only
    r2 = door(inserts=[{"id": "I1", "name": "WC-01", "x": 5150.0, "y": 1460.0}])
    assert r2["swing"]["obstructions"] == [{"kind": "FIXTURE", "id": "WC-01"}] and r2["swing"]["as_drawn"] == "CLEAR"


def test_double_leaf_main_entrance():
    run = F.two_rooms(b_word="ENTRANCE HALL", extra_openings=[("DOOR", "y", 0, 200, 5000, 6600, None)],
                      extra_swings=(((5000, 200), 800, 0, 90), ((6600, 200), 800, 90, 180)))
    main = next(r for r in run["rep"]["rows"] if r["category"] == "MAIN_ENTRANCE")
    el = next(e for e in run["model"]["elements"] if e["element_id"] == main["element_id"])
    assert el["leaf_count"] == 2 and main["cad_wall_opening_m"] == 1.6
    assert main["feasibility"] == "STANDARD_FITS_AS_DRAWN" and main["enlargement_m"] is None
    assert main["height"]["value_m"] == 2.5 and main["height"]["state"] == "OWNER_STANDARD_ASSUMED"


def test_door_with_conflicting_dimensions_and_unknown_structure():
    """the Phase 2B-0 guard floor: a 0.90 m opening with a 1.00 m frame is held (both values kept): insufficient
    evidence; the floor draws no column frame, so every enlargement needs an engineer."""
    g = F.guard_floor()
    held = [r for r in g["rep"]["rows"] if r["state"] == "CONFIRMED" and r["feasibility"] ==
            "INSUFFICIENT_DRAWING_EVIDENCE" and any("width held" in x for x in r["reasons"])]
    assert len(held) == 1 and held[0]["cad_wall_opening_m"] == 0.9
    assert all(r["host_wall"]["structure"] == "UNKNOWN" for r in g["rep"]["rows"] if r.get("host_wall"))


def test_unknown_structural_classification_requires_engineering_review():
    r = door(columns=())
    assert r["host_wall"]["structure"] == "UNKNOWN" and r["feasibility"] == "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW"
    assert r["view"] == "UNRESOLVED"
    ok = door(columns=(), rules=[F.rule("PR-1", "UP-DOOR-FEAS-001", "wall_structure", "NON_STRUCTURAL",
                                        kind="DRAWING", ref="structural plan S-101")])
    assert ok["host_wall"]["structure"] == "NON_STRUCTURAL_SPECIFIED"
    assert ok["feasibility"] == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"
    st = door(rules=[F.rule("PR-1", "UP-DOOR-FEAS-001", "wall_structure", "STRUCTURAL", kind="DRAWING",
                            ref="structural plan S-101")])
    assert st["feasibility"] == "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW"
    assert any(a["who"] == "structural engineer" for a in st["proposed_modification"]["approvals"])


def test_door_with_missing_height():
    r = door()
    assert (r["height"]["value_m"], r["height"]["state"]) == (2.2, "OWNER_STANDARD_ASSUMED")
    facts = {"schema": "URBAN_ARCH_FACTS_V1",
             "opening_heights": {"DOOR": {"value_m": 2.1, "authority": "SOURCE: door schedule D-01"}}}
    r2 = door(facts=facts)
    assert (r2["height"]["value_m"], r2["height"]["state"]) == (2.1, "DRAWING_CONFIRMED")
    assert r2["feasibility"] == r["feasibility"]                 # the width analysis does not depend on the height


def test_a_project_specific_width_standard():
    """the project's approved bathroom door is 0.80 m: required wall opening 0.90 m; the Urban 0.90 m is kept."""
    rule = F.rule("PR-1", "UP-DOOR-OPEN-002", "required_nominal_door_m", 0.8,
                  {"kind": "DOOR_CATEGORY", "categories": ["BATHROOM_PVC"]}, kind="SCHEDULE", ref="door schedule")
    r = door(a_word="BATH", s0=1500, s1=2300, rules=[rule])
    s = r["standard"]
    assert (s["required_nominal_door_m"], s["urban_nominal_m"], s["state"], s["project_rule_ids"]) == (
        0.8, 0.9, "PROJECT_SPECIFIED", ["PR-1"])
    assert (s["required_wall_opening_m"], r["enlargement_m"]) == (0.9, 0.1)
    other = door(s0=1500, s1=2400, rules=[rule])                  # an internal door: the rule is out of its scope
    assert other["standard"]["required_nominal_door_m"] == 1.0


def test_no_proposed_modification_is_released_as_drawn():
    run = F.two_rooms()
    r = F.party_door(run)
    assert r["proposed_modification"]["status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"
    el = next(e for e in run["model"]["elements"] if e["element_id"] == r["element_id"])
    assert round(el["structural_opening_width_m"], 6) == 0.9            # the drawn width is untouched
    lines = DM.boq_lines({"project_id": "P", "revision_set_sha256": "0" * 64, "documents": []}, run["model"])
    widths = {round(ln["calculation"]["inputs"].get("width_m") or 0, 6) for ln in lines if ln["item_code"].startswith("DOOR.")}
    assert 1.1 not in widths and 0.9 in widths
    v = run["rep"]["views"]
    assert v["PROPOSED_MODIFICATION"] and "never added together" in v["note"]
    assert set(v) == {"AS_DRAWN", "OWNER_STANDARD", "PROPOSED_MODIFICATION", "UNRESOLVED", "EXCLUDED", "note"}
    assert run["rep"]["conservation"]["ok"]


def test_mirrored_and_rotated_geometry_give_the_same_result(tmp_path):
    """the synthetic villa, its mirror, a quarter turn, a move and all three together (inside the generator's sheet
    frames, as tests/m9_s2_arch) through the V2.4 command: every door keeps its class, enlargement and the multiset of
    its two clearances."""
    from tools import arch_synth as AS
    from tools import urban_boq_m9 as M9

    def sig(**kw):
        p = tmp_path / ("v_" + "_".join(f"{k}{v}" for k, v in sorted(kw.items())) + ".dxf")
        AS.villa(p, **kw)
        try:
            arch = M9.arch_compute(str(p), method="ARCH_TAKEOFF_V2.4")[1]
        except M9.CompletenessFailed as ex:
            arch = ex.arch
        rows = arch["door_feasibility"]["rows"]
        return sorted(json.dumps([r["floor"], r["category"], r["cad_wall_opening_m"], r.get("enlargement_m"),
                                  r.get("feasibility"),
                                  sorted((c["constraint"], c["plain_m"]) for c in (r.get("clearances") or {}).values())])
                      for r in rows)
    base = sig()
    assert base == sig(mirror=True) == sig(quarter_turns=1) == sig(dx=1234.5, dy=-987.25) == \
        sig(mirror=True, quarter_turns=3, dx=50.0)


def test_a_swing_symbol_closing_outside_its_gap_is_reported_not_evaluated():
    """a door symbol whose closed leaf ends outside the jambs (turned half a turn about the hinge - a mis-mirrored
    block) gives no swing side: SWING_SYMBOL_INCONSISTENT, never a CLEAR or CONFLICT claim from a sector on the wrong
    side; the same door drawn consistently is evaluated."""
    bad = door(swing=False, extra_swings=(((4200, 1500), 900, 270, 360),))
    assert bad["swing"]["state"] == "NOT_EVALUATED" and bad["swing"]["why"].startswith("SWING_SYMBOL_INCONSISTENT")
    assert bad["feasibility"] == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"
    assert any(x.startswith("SWING_SYMBOL_INCONSISTENT") for x in bad["reasons"])
    good = door()
    assert good["swing"]["state"] == "CLEAR" and good["feasibility"] == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"


def test_a_stair_at_the_enlarged_jamb_constrains_and_says_why_first():
    """a door into a stair hall: the plain wall would allow the enlargement, but the space at the enlarged jamb is a
    stair - CONSTRAINED, the stair reason first, the placement kept only as what the plain wall alone would allow."""
    r = door(b_word="STAIR")
    assert r["feasibility"] == "ENLARGEMENT_CONSTRAINED"
    assert r["reasons"][0] == "a stair space at the enlarged jamb"
    assert all(x.startswith("plain wall alone would allow") for x in r["reasons"][1:]) and len(r["reasons"]) >= 2
