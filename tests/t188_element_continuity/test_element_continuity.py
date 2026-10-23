"""T-188 ELEMENT_CONTINUITY_V1 on synthetic villa K (not the development villa): normal and adverse cases."""

import copy
import math

import pytest

from engine.source import element_continuity_v1 as M
from tests.t188_element_continuity import villa_k as K


def keys(res):
    return sorted(((f["code"], f["element"], f["storey"]) for f in res["findings"]),
                  key=lambda t: (t[0], t[1] or "", t[2] or ""))


def codes_of(res, el):
    return sorted(f["code"] for f in res["findings"] if f["element"] == el)


def el(p, i):
    return next(e for e in p["elements"] if e["id"] == i)


def test_villa_k_hand_truth():
    res = M.check(K.project())
    assert keys(res) == K.EXPECTED
    assert res["summary"]["elements"] == 10 and res["summary"]["lines"] == 13


def test_findings_never_carry_a_quantity():
    for f in M.check(K.project())["findings"]:
        assert set(f) == {"review", "code", "status", "element", "kind", "storey", "lines", "refs", "why"}


# ---- R3 storey continuity ------------------------------------------------------------------------------------------

def test_stair_folded_storey_is_held_normal_vs_adverse():
    p = K.project()
    assert codes_of(M.check(p), "K-SB") == ["STOREY_WITHOUT_LINE"]
    p["lines"].append({"line_id": "L-11", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "1F",
                       "trade": "STRUCTURE", "state": "MEASURED", "element": "K-SB"})
    assert codes_of(M.check(p), "K-SB") == []


def test_held_placeholder_line_accounts_for_the_storey_and_keeps_its_state():
    p = K.project()
    p["lines"].append({"line_id": "L-12", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "1F",
                       "trade": "STRUCTURE", "state": "HELD", "element": "K-SB"})
    res = M.check(p)
    assert codes_of(res, "K-SB") == []
    row = next(r for r in res["elements"] if r["element"] == "K-SB")
    assert row["storeys"][1] == {"storey": "1F", "drawn": ["A-102", "S-102"], "lines": ["L-12"]}


def test_a_storey_with_no_drawing_is_held():
    res = M.check(K.project())
    f = next(x for x in res["findings"] if x["code"] == "STOREY_NOT_DRAWN")
    assert (f["element"], f["storey"], f["status"]) == ("K-SC", "1F", "HELD")


def test_correct_end_not_flagged_but_unevidenced_end_is_review_only():
    p = K.project()
    assert "END_NOT_EVIDENCED" not in codes_of(M.check(p), "K-SA")
    del el(p, "K-SA")["ends"]
    f = [x for x in M.check(p)["findings"] if x["element"] == "K-SA" and x["code"] == "END_NOT_EVIDENCED"]
    assert len(f) == 1 and f[0]["status"] == "REVIEW" and f[0]["storey"] == "1F"
    assert f[0]["refs"] == ["A-103 flights seen through the opening"]


def test_seen_below_never_makes_a_storey_occupied_but_a_drawn_flight_is_a_conflict():
    p = K.project()
    res = M.check(p)
    assert next(r for r in res["elements"] if r["element"] == "K-SA")["occupies"] == ["GF", "1F"]
    el(p, "K-SA")["presence"][-1]["what"] = "DRAWN"
    f = [x for x in M.check(p)["findings"] if x["code"] == "DRAWN_OUTSIDE_SPAN"]
    assert [(x["element"], x["storey"], x["status"]) for x in f] == [("K-SA", "2F", "CONFLICT")]


def test_occupancy_from_drawings_when_no_levels():
    p = K.project()
    e = el(p, "K-SB")
    del e["occupies"], e["occupies_ref"]
    row = next(r for r in M.check(p)["elements"] if r["element"] == "K-SB")
    assert row["occupies"] == ["GF", "1F"] and row["occupies_basis"] == "DRAWN"
    e["presence"] = []
    assert "SPAN_UNDETERMINED" in codes_of(M.check(p), "K-SB")


def test_mirror_and_rotation_do_not_change_findings():
    base = keys(M.check(K.project()))
    assert keys(M.check(M.mirror(K.project(), "x"))) == base
    assert keys(M.check(M.mirror(K.project(), "y"))) == base
    p = K.project()
    a = math.radians(90.0)
    for e in p["elements"]:
        for pr in e["presence"]:
            if pr.get("xy"):
                x, y = pr["xy"]
                pr["xy"] = [x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)]
    assert keys(M.check(p)) == base


def test_place_mismatch_when_one_storey_is_another_element():
    p = K.project()
    el(p, "K-SB")["presence"][3]["xy"] = [15.0, 3.0]
    f = [x for x in M.check(p)["findings"] if x["code"] == "PLACE_MISMATCH"]
    assert [(x["element"], x["storey"]) for x in f] == [("K-SB", "1F")]
    assert "3.000 m" in f[0]["why"]


def test_column_missing_top_storey_line():
    assert codes_of(M.check(K.project()), "K-C4") == ["STOREY_WITHOUT_LINE"]


# ---- R2 cross-discipline ---------------------------------------------------------------------------------------------

def test_dome_without_structure_normal_vs_adverse():
    res = M.check(K.project())
    assert codes_of(res, "K-DT") == ["NO_BOQ_LINE", "NO_STRUCTURAL_COUNTERPART", "NO_STRUCTURAL_DETAIL"]
    assert codes_of(res, "K-DR") == ["KIND_MISMATCH"]          # detail PROJECT: counts as its structural drawing


def test_absence_needs_a_search():
    p = K.project()
    del el(p, "K-DT")["searched"]["STRUCT"]
    assert "NOT_SEARCHED" in codes_of(M.check(p), "K-DT")
    assert "NO_STRUCTURAL_COUNTERPART" not in codes_of(M.check(p), "K-DT")


def test_lift_without_pit_normal_vs_adverse():
    p = K.project()
    assert codes_of(M.check(p), "K-LF") == ["MISSING_COMPONENT"]
    el(p, "K-LF")["components"] = [{"name": "PIT", "state": "DRAWN", "ref": "S-001 pit section"}]
    assert codes_of(M.check(p), "K-LF") == []
    el(p, "K-LF")["components"] = [{"name": "PIT", "state": "HELD", "ref": "S-001", "note": "depth not printed"}]
    f = [x for x in M.check(p)["findings"] if x["element"] == "K-LF"]
    assert [(x["code"], x["status"]) for x in f] == [("COMPONENT_HELD", "HELD")]


def test_misread_line_is_held_never_relabelled():
    res = M.check(K.project())
    f = next(x for x in res["findings"] if x["code"] == "KIND_MISMATCH")
    assert f["lines"] == ["L-41"] and f["status"] == "HELD"
    row = next(r for r in res["elements"] if r["element"] == "K-DR")
    assert row["owner_lines"] == ["L-40"]                       # the stair line is not the dome's own line


def test_trade_not_allowed():
    p = K.project()
    p["lines"].append({"line_id": "L-70", "item": "POOL PAINT", "kind": "POOL", "storey": "GF", "trade": "PAINT",
                       "state": "MEASURED", "element": "K-PL"})
    f = [x for x in M.check(p)["findings"] if x["code"] == "TRADE_NOT_ALLOWED"]
    assert [x["lines"] for x in f] == [["L-70"]]


def test_reference_row_on_no_drawing_is_not_drawn_never_zero():
    res = M.check(K.project())
    f = [x for x in res["findings"] if x["code"] == "NOT_DRAWN"]
    assert len(f) == 1 and f[0]["lines"] == ["REF:8"] and f[0]["status"] == "NOT_DRAWN"


def test_optional_component_not_drawn_vs_required():
    p = K.project()
    el(p, "K-PL")["components"].append({"name": "STEPS", "state": "NOT_DRAWN", "ref": "S-203 / A-101",
                                        "note": "consultant item"})
    assert codes_of(M.check(p), "K-PL") == ["COMPONENT_NOT_DRAWN"]
    el(p, "K-PL")["components"][1]["state"] = "NOT_DRAWN"     # WALLS (required) not drawn
    assert "MISSING_COMPONENT" in codes_of(M.check(p), "K-PL")


def test_ambiguous_binding_counts_for_each_candidate_and_is_reported():
    p = K.project()
    p["lines"].append({"line_id": "L-42", "item": "DOME SHELL", "kind": "DOME", "storey": "ROOF",
                       "trade": "STRUCTURE", "state": "MEASURED", "element_any": ["K-DT", "K-DR"]})
    res = M.check(p)
    assert "NO_BOQ_LINE" not in codes_of(res, "K-DT")
    assert [x["lines"] for x in res["findings"] if x["code"] == "BINDING_AMBIGUOUS"] == [["L-42"]]


def test_void_needs_no_line_of_its_own():
    assert codes_of(M.check(K.project()), "K-VD") == []


# ---- guards ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("mutate, msg", [
    (lambda p: el(p, "K-SA").update(kind="STAIRS"), "unknown kind"),
    (lambda p: el(p, "K-SA")["presence"][0].pop("ref"), "without ref"),
    (lambda p: el(p, "K-SA")["presence"][0].update(storey="3F"), "unknown storey"),
    (lambda p: el(p, "K-SA")["presence"][0].update(discipline="MEP"), "unknown discipline"),
    (lambda p: p.pop("place_tol_m"), "place_tol_m"),
    (lambda p: p["elements"].append(copy.deepcopy(el(p, "K-SA"))), "duplicate element id"),
    (lambda p: el(p, "K-SA").pop("occupies_ref"), "occupies_ref"),
    (lambda p: el(p, "K-DT")["detail"].update(state="SOME"), "detail state"),
    (lambda p: p["lines"][0].update(element_any=["K-SB"]), "both set"),
    (lambda p: p.update(storeys=["GF", "GF"]), "unique"),
])
def test_guards(mutate, msg):
    p = K.project()
    mutate(p)
    with pytest.raises(ValueError, match=msg):
        M.check(p)
