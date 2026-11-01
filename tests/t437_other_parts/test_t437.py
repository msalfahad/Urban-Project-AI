"""T-437: other unexplained concrete parts (pool-wall height, beam lengths, boundary lengths) tested construction by
construction.

Villa R437 (hand fixture, NOT Alsenan):
  POOL  rim +0.45, RC base top -1.05 (RC wall 1.50), base 0.35, screed 0.05, membrane 0.03, blinding 0.10; deck structure
        top +0.25 (upstand 0.20 above it); wall band 3.000 m2.
        His wall height 2.03: rim to formation = 1.50 + 0.35 + 0.05 + 0.03 + 0.10 = 2.03 (exact, unique: rim to base
        underside + upstand again = 1.85 + 0.20 = 2.05, misfit -0.02 > 0.005) -> TRACED NOT_RC_WALL;
        the part beyond rim .. base underside = 3.000 x (2.03 - 1.85) = 0.540 m3, not RC wall.
        His 2.00: no construction within 0.005 -> UNRESOLVED (nearest listed, never taken).
  BOUNDARY band 0.20 wide: axis 25.40, outer run 25.80, inner run 25.00; outer 13.00 + inner 12.40 = 25.40 is a MIXED
        construction (refused even though it is exact against an axis-like 25.40).
        His 25.6 (to 0.05): none -> UNRESOLVED; his 26 (to 0.5): outer 25.80 only -> TRACED.
  BEAM  0.20 x 0.50, runs between columns 0.30 / 0.25 (interior) / 0.40 along the axis: drawn runs 3.00 / 2.40 / 2.40;
        engine valued length of the 3.00 run 3.25 = 3.00 + a 0.25 beside-support piece already valued.
        Outermost drawn extent of that run (outer faces of its end columns) 3.00 + 0.30 + 0.25 = 3.55.
        Room for a through-support length = 3.55 - 3.25 = 0.30 (NOT 0.55: the 0.25 is already in the valued length).
        His 3.80: untraced at least 3.80 - 3.55 = 0.25 m; an allowance of 0.55 claimed over-reads the room by 0.25 m
        ('length taken through a column already deducted').
        His rows 3.00 x 1, 2.40 x 3 against drawn 3.00 / 2.40 / 2.40, room 0.95 -> one 2.40 row left over > 0.95: COUNT.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t437"))
import t437_rules as R  # noqa: E402

SUMMARY = ROOT / "research" / "agents_t437" / "summary_t437.json"


def pool_cons(rim=0.45, top=-1.05, base=0.35, screed=0.05, memb=0.03, blind=0.10, deck_str=0.25):
    wall = rim - top
    return [
        {"name": "rim to base top", "value": wall, "cls": "ENGINE_BASIS"},
        {"name": "rim to base underside", "value": wall + base, "cls": "BASE_AGAIN"},
        {"name": "rim to formation", "value": wall + base + screed + memb + blind, "cls": "NOT_RC_WALL"},
        {"name": "rim to base underside + upstand again", "value": wall + base + (rim - deck_str), "cls": "NOT_RC_WALL"},
    ]


# ---------------- R-T437-1 construction test ----------------

def test_pool_height_rim_to_formation_traced_unique():
    res = R.construction_test(2.03, pool_cons(), tol=R.precision_tol("2.03"))
    assert res["status"] == "TRACED" and res["cls"] == "NOT_RC_WALL" and not res["cause_ambiguous"]
    assert [h["name"] for h in res["hits"]] == ["rim to formation"]
    assert R.r6(3.000 * (2.03 - 1.85)) == 0.54


def test_pool_height_two_exact_constructions_same_class_is_traced_cause_ambiguous():
    # Alsenan-like levels where both readings land on the same figure
    res = R.construction_test(1.80, pool_cons(rim=0.30, top=-0.90, base=0.40, screed=0.05, memb=0.05, blind=0.10,
                                              deck_str=0.10), tol=R.precision_tol("1.8"))
    assert res["status"] == "TRACED" and res["cause_ambiguous"] and len(res["hits"]) == 2


def test_pool_height_no_construction_unresolved_nearest_not_taken():
    res = R.construction_test(2.00, pool_cons(), tol=R.precision_tol("2.00"))
    assert res["status"] == "UNRESOLVED" and "cls" not in res
    assert res["nearest"][0]["name"] == "rim to formation"      # listed only


def test_ambiguous_different_classes_unresolved():
    cons = [{"name": "a", "value": 2.00, "cls": "X"}, {"name": "b", "value": 2.01, "cls": "Y"}]
    res = R.construction_test(2.0, cons, tol=R.precision_tol("2.0"))
    assert res["status"] == "UNRESOLVED" and res["why"].startswith("AMBIGUOUS")


def boundary_cons():
    return [{"name": "axis", "value": 25.40, "cls": "BAND_SOLID"},
            {"name": "outer run", "value": 25.80, "cls": "BAND_SOLID"},
            {"name": "inner run", "value": 25.00, "cls": "INNER"},
            {"name": "outer 13.00 + inner 12.40", "value": 25.40, "cls": "MIXED", "mixed_faces": True}]


def test_boundary_precision_005_none():
    res = R.construction_test(25.6, boundary_cons(), tol=R.precision_tol("25.6"))
    assert res["status"] == "UNRESOLVED"


def test_boundary_whole_metres_outer_only():
    res = R.construction_test(26, boundary_cons(), tol=R.precision_tol("26"))
    assert res["status"] == "TRACED" and [h["name"] for h in res["hits"]] == ["outer run"]


def test_mixed_face_construction_refused_even_when_exact():
    cons = [{"name": "outer 13.00 + inner 12.40", "value": 25.40, "cls": "MIXED", "mixed_faces": True},
            {"name": "inner run", "value": 25.00, "cls": "INNER"}]
    res = R.construction_test(25.40, cons, tol=R.precision_tol("25.40"))
    assert res["status"] == "UNRESOLVED" and res["refused_mixed"][0]["misfit"] == 0.0


def test_mirror_and_order_do_not_change_the_result():
    a = R.construction_test(26, boundary_cons(), tol=0.5)
    b = R.construction_test(26, list(reversed(boundary_cons())), tol=0.5)
    assert a["status"] == b["status"] and {h["name"] for h in a["hits"]} == {h["name"] for h in b["hits"]}


@pytest.mark.parametrize("bad", [dict(target=None), dict(unit="mm"), dict(cons=[])])
def test_construction_refusals(bad):
    with pytest.raises(R.RefusedT437):
        R.construction_test(bad.get("target", 2.0), bad.get("cons", pool_cons()), tol=0.005, unit=bad.get("unit", "m"))


def test_precision_tolerance():
    assert R.precision_tol("42") == 0.5 and R.precision_tol("71.7") == 0.05 and R.precision_tol("2.95") == 0.005
    assert R.precision_tol("1.2345") == 0.0005
    with pytest.raises(R.RefusedT437):
        R.precision_tol("")


# ---------------- R-T437-2 through bound ----------------

def test_through_bound_normal():
    tb = R.through_bound(his_len=3.40, engine_len=3.00, outermost_len=3.55)
    assert tb["room_m"] == 0.55 and tb["untraced_lower_bound_m"] == 0.0


def test_length_through_a_column_already_deducted_adverse():
    tb = R.through_bound(his_len=3.80, engine_len=3.25, outermost_len=3.55, allowance_claimed=0.55)
    assert tb["room_m"] == 0.30 and tb["untraced_lower_bound_m"] == 0.25 and tb["allowance_over_room_m"] == 0.25


def test_support_already_in_engine_length_gives_no_more_room():
    tb = R.through_bound(his_len=3.80, engine_len=3.00, outermost_len=3.55, support_in_engine_len=0.25)
    assert tb["room_m"] == 0.30


def test_through_bound_refusals():
    with pytest.raises(R.RefusedT437):
        R.through_bound(his_len=None, engine_len=3.0, outermost_len=3.5)
    with pytest.raises(R.RefusedT437):
        R.through_bound(his_len=3.6, engine_len=3.6, outermost_len=3.5)


# ---------------- R-T437-3 count binding ----------------

def test_count_binding_left_over_row_is_count():
    cb = R.count_binding([(3.0, 1), (2.4, 3)], [3.0, 2.4, 2.4], through_room=0.95)
    assert cb["class"] == "COUNT" and cb["his_left_over"] == [2.4]


def test_count_binding_short_left_over_stays_length():
    cb = R.count_binding([(3.0, 1), (2.4, 2), (0.5, 1)], [3.0, 2.4, 2.4], through_room=0.95)
    assert cb["class"] == "LENGTH"


def test_count_binding_mirror_order_independent():
    a = R.count_binding([(2.4, 3), (3.0, 1)], [2.4, 2.4, 3.0], through_room=0.95)
    b = R.count_binding([(3.0, 1), (2.4, 3)], [3.0, 2.4, 2.4], through_room=0.95)
    assert a["class"] == b["class"] == "COUNT" and a["left_over_m"] == b["left_over_m"]


def test_count_binding_refusals():
    with pytest.raises(R.RefusedT437):
        R.count_binding([(3.0, None)], [3.0], through_room=0.5)
    with pytest.raises(R.RefusedT437):
        R.count_binding([(3.0, 1.5)], [3.0], through_room=0.5)


# ---------------- R-T437-5 step ----------------

def test_step_normal_and_adverse():
    assert R.within_step(engine_len=4.577, his_len=4.55, step=0.05)["is_step"]
    assert not R.within_step(engine_len=4.62, his_len=4.55, step=0.05)["is_step"]        # one step or more
    assert not R.within_step(engine_len=4.50, his_len=4.55, step=0.05)["is_step"]        # his longer: never a step


# ---------------- R-T437-4 split / disjoint ----------------

def test_split_readds_and_refusals():
    subs = [{"id": "a", "m3": -0.3, "verdict": "UNRESOLVED"}, {"id": "b", "m3": -0.2, "verdict": "ENGINE_RIGHT"}]
    assert R.check_split(-0.5, subs) == -0.5
    with pytest.raises(R.RefusedT437):
        R.check_split(-0.6, subs)
    with pytest.raises(R.RefusedT437):
        R.check_split(0.0, [{"id": "h", "m3": 0.0, "verdict": "HELD"}])
    with pytest.raises(R.RefusedT437):
        R.check_split(-0.1, [{"id": "w", "m3": -0.1, "verdict": "ENGINE_WRONG"}])
    with pytest.raises(R.RefusedT437):
        R.check_split(-0.2, [{"id": "x", "m3": -0.1, "verdict": "UNRESOLVED"}, {"id": "x", "m3": -0.1,
                                                                                 "verdict": "UNRESOLVED"}])


def test_disjoint_refuses_a_shared_part():
    assert R.disjoint(["PL-WALLS"], {"T-430": ["GB-MAIN"]})
    with pytest.raises(R.RefusedT437):
        R.disjoint(["GB-MAIN"], {"T-430": ["GB-MAIN"]})


# ---------------- committed Alsenan summary ----------------

def S():
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def test_alsenan_parts_readd_to_the_row():
    s = S()
    tot = sum(p["m3"] for k, p in s["parts"].items() if k != "CL-1F")
    assert abs(tot - (-1.033946)) <= 0.000002 + 1e-9
    for comp, p in s["parts"].items():
        assert abs(sum(x["m3"] for x in p["subparts"]) - p["m3"]) <= 0.000002


def test_alsenan_disjoint_from_t430_t436_t444_t445():
    s = S()
    ids = set(s["parts"]) | {x["id"] for p in s["parts"].values() for x in p["subparts"]}
    for bad in ("GB-MAIN", "GS-SLAB", "S-PANEL", "I-07", "FOOTING"):
        assert bad not in ids


def test_alsenan_classes():
    s = S()
    sub = {x["id"]: x for p in s["parts"].values() for x in p["subparts"]}
    assert all(x["verdict"] == "UNRESOLVED" for x in sub.values())             # classes wait for the Checker
    assert sub["PLW-H020"]["proposal"] == "ENGINE_RIGHT"
    assert sub["BM2F-B2"]["proposal"] == "ENGINE_RIGHT"
    assert sub["BM1F-CB12"]["proposal"] == "UNRESOLVED" and sub["BMGF-B7"]["proposal"] == "UNRESOLVED"
    assert s["tests"]["beams"]["2F:B2"]["binding"]["class"] == "COUNT"
    assert s["tests"]["beams"]["1F:CB12"]["untraced_lower_bound_m3"] == 0.1875
    assert abs(sum(s["by_proposal_m3"].values()) - (-1.033944)) <= 0.000002


def test_alsenan_summary_has_no_coordinate_sized_number():
    txt = SUMMARY.read_text(encoding="utf-8")
    nums = [float(x) for x in re.findall(r"-?\d+\.\d+", txt)]
    assert max(abs(x) for x in nums) < 1000.0


def test_alsenan_script_reproduces_the_summary(tmp_path):
    out = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t437" / "t437_alsenan.py")],
                         capture_output=True, text=True, check=True)
    assert '"row_total_m3": -1.033944' in out.stdout
