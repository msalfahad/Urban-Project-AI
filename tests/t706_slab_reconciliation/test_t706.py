"""T-706 R-T706-1 (typed reference split by thickness zone), R-T706-2 (own re-measure as a check; physical class of
every excluded / unowned face), R-T706-3 (a reference arithmetic slip explained only with its member).
Villa V706 is hand-made (not the development villa); the last tests rebuild the development-villa statement from
committed files only (the own re-measure and the reference read are committed as numbers; the drawing never is)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t706"))
import t706_rules as R  # noqa: E402

SECTIONS = ("0.20", "0.25", "0.30", "0.40", "0.90")


# V706 roof by hand: panel A 4.70 x 3.00 = 14.10 m2 with 'T 18' printed inside; B 3.00 x 3.00 = 9.00 m2 and
# C 2.00 x 1.50 = 3.00 m2 without a mark (sheet default 0.16). Engine m3 = 14.10 x 0.18 + 12.00 x 0.16 = 4.458.
RECTS = {"A": (0, 0, 4700, 3000, [X("0.18")]), "B": (4900, 0, 7900, 3000, []), "C": (0, 3200, 2000, 4700, [])}


def villa(mirror=False, rotate=False, unit_m=0.001):
    """engine panels + own panels (areas from the drawn corners, in any orientation and unit)."""
    from shapely.geometry import Polygon
    eng, own = [], {}
    for k, (x0, y0, x1, y1, marks) in RECTS.items():
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if mirror:
            pts = [(-x, y) for x, y in pts]
        if rotate:
            pts = [(-y, x) for x, y in pts]
        pts = [(x * 0.001 / unit_m, y * 0.001 / unit_m) for x, y in pts]
        a = X(str(round(Polygon(pts).area * unit_m * unit_m, 6)))
        eng.append({"id": k, "m2": a, "marks": marks})
        own[k] = a
    return eng, own


def test_v706_hand_areas_and_agreement():
    eng, own = villa()
    assert {p["id"]: p["m2"] for p in eng} == {"A": X("14.1"), "B": X("9"), "C": X("3")}
    r = R.zone_reconcile(eng, own, {"0.16": "12.00", "0.18": "14.10"}, sheet_default_t="0.16")
    assert r["engine_m3"] == X("4.458") and r["difference_m3"] == 0 and r["status"] == "ROUNDING_ONLY"


@pytest.mark.parametrize("mirror,rotate,unit", [(True, False, 0.001), (False, True, 0.001), (True, True, 1.0)])
def test_invariant_under_mirror_rotation_units(mirror, rotate, unit):
    eng, own = villa(mirror, rotate, unit)
    r = R.zone_reconcile(eng, own, {"0.16": "12.59", "0.18": "13.82"}, sheet_default_t="0.16")
    assert r["difference_m3"] == X("12.59") * X("0.16") + X("13.82") * X("0.18") - X("4.458")


def test_zone_terms_re_add_and_partial_panels_not_named():
    """the development-villa pattern by hand: 0.16 zone +0.59 m2, 0.18 zone -0.28 m2, no whole panel fits."""
    eng, own = villa()
    r = R.zone_reconcile(eng, own, {"0.16": "12.59", "0.18": "13.82"}, sheet_default_t="0.16")
    z = {row["t_m"]: row for row in r["zones"]}
    assert z[X("0.16")]["term_m3"] == X("0.0944") and z[X("0.16")]["status"] == "REFERENCE_LARGER"
    assert z[X("0.18")]["term_m3"] == X("-0.0504") and z[X("0.18")]["status"] == "NOT_WHOLE_PANELS"
    assert r["terms_sum_m3"] == r["difference_m3"] == X("0.0440")
    assert r["transfers"] == [] and r["status"] == "NOT_WHOLE_PANELS"


def test_whole_panel_transfer_between_zones():
    """the reference measured panel A at 0.16: 0.18 zone lacks 14.10, 0.16 zone has 14.10 extra."""
    eng, own = villa()
    r = R.zone_reconcile(eng, own, {"0.16": "26.10", "0.18": "0"}, sheet_default_t="0.16")
    assert r["status"] == "TRANSFER_CANDIDATE"
    assert r["transfers"] == [{"from_t": X("0.18"), "to_t": X("0.16"), "panels": 1, "m2": X("14.1")}]
    assert r["difference_m3"] == X("14.10") * (X("0.16") - X("0.18"))


def test_single_zone_keeps_its_own_status():
    eng, own = villa()
    eng = [dict(p, marks=[]) for p in eng]
    r = R.zone_reconcile(eng, own, {"0.16": "23"}, sheet_default_t="0.16")   # 26.10 drawn vs 23 typed
    assert r["status"] == "UNIQUE_CANDIDATE"                                  # only panel C (3.00) fits 2.6 .. 3.6


def test_adverse_no_thickness_stays_held_never_zero():
    eng, own = villa()
    with pytest.raises(R.Refused, match="stays HELD"):
        R.zone_reconcile(eng, own, {"0.16": "12", "0.18": "14.1"}, sheet_default_t=None)


def test_adverse_conflicting_marks_refused():
    eng, own = villa()
    eng[0]["marks"] = [X("0.18"), X("0.16")]
    with pytest.raises(R.Refused, match="conflicting"):
        R.zone_reconcile(eng, own, {"0.16": "12", "0.18": "14.1"}, sheet_default_t="0.16")


def test_adverse_unlocated_panel_refused_and_our_error_named_first():
    eng, own = villa()
    with pytest.raises(R.Refused, match="locate every engine panel"):
        R.zone_reconcile(eng, {"A": own["A"], "B": own["B"]}, {"0.16": "12", "0.18": "14.1"}, sheet_default_t="0.16")
    own["B"] = own["B"] + X("0.02")
    r = R.zone_reconcile(eng, own, {"0.16": "12", "0.18": "14.1"}, sheet_default_t="0.16")
    assert r["status"] == "OUR_ERROR"


# ------------------------------------------------------------------------------------------------ R-T706-2
def test_check_location_normal_and_merged_face_refused():
    ok = R.check_location([{"line_id": "a", "class": "RELEASED", "own_face": 1, "engine_m2": "5", "own_m2": "5"},
                           {"line_id": "b", "class": "RELEASED", "own_face": 2, "engine_m2": "3", "own_m2": "3.0001"}])
    assert ok["geometry_claim_allowed"] and [x["check"] for x in ok["lines"]] == ["CHECKED", "CHECKED"]
    bad = R.check_location([{"line_id": "a", "class": "RELEASED", "own_face": 1, "engine_m2": "5", "own_m2": "8"},
                            {"line_id": "b", "class": "RELEASED", "own_face": 1, "engine_m2": "3", "own_m2": "8"},
                            {"line_id": "c", "class": "EXCLUDED", "own_face": None, "engine_m2": "1", "own_m2": "0"}])
    assert not bad["geometry_claim_allowed"]
    assert [x["check"] for x in bad["lines"]] == ["NOT_CHECKED", "NOT_CHECKED", "UNLOCATED"]
    assert all(x["own_minus_engine_m2"] is None for x in bad["lines"])     # a merged face is never compared


@pytest.mark.parametrize("face,cls", [
    ({"mean_width_m": "0.20"}, "MEMBER_STRIP"),
    ({"mean_width_m": "0.90", "member_label": True}, "MEMBER_STRIP"),
    ({"mean_width_m": "0.70", "member_label": True}, "MEMBER_STRIP"),
    ({"mean_width_m": "0.077"}, "NARROW_BAND"),
    ({"mean_width_m": "1.0", "opening_lines": 2}, "OPENING"),
    ({"mean_width_m": "2.9", "opening_lines": 8, "inner_lines": 29}, "STAIR_ZONE"),      # flights decide first
    ({"mean_width_m": "2.2", "opening_lines": 20}, "DOME_OPENING"),
    ({"mean_width_m": "0.6", "radial_ring_segment": True}, "DOME_SEGMENT"),
    ({"mean_width_m": "0.20", "thickness_mark": True}, "UNRESOLVED"),                    # a marked face is a panel
    ({"mean_width_m": "1.2"}, "UNRESOLVED"),
])
def test_classify_face(face, cls):
    assert R.classify_face(face, member_sections_m=SECTIONS) == cls


def test_storey_closure_needs_every_face_classed():
    assert R.storey_closure({"x": "MEMBER_STRIP", "y": "OPENING"})["closed"]
    c = R.storey_closure({"x": "MEMBER_STRIP", "y": "UNRESOLVED"})
    assert not c["closed"] and c["unresolved"] == ["y"]
    with pytest.raises(R.Refused):
        R.classify_face({"mean_width_m": "0"}, member_sections_m=SECTIONS)


# ------------------------------------------------------------------------------------------------ R-T706-3
VALS = {59: "0.128", 60: "0.32", 61: "0.24"}


def test_omitted_first_row_explained_with_member():
    s = R.omitted_rows(VALS, range(59, 62), range(60, 62), "0.688", "0.56")
    assert s["omitted"] == [59] and s["extra"] == [] and s["gap_m3"] == X("-0.128")
    e = R.explain_slip(s, {59: {"mark": "B1", "storey": "1F", "section": "0.20 x 0.40", "engine": "OWNED"}})
    assert e["explained"] and e["rows"][0]["status"] == "REFERENCE_ARITHMETIC" and e["engine_quantity_moved_m3"] == 0


def test_adverse_slip_without_member_or_not_owned_is_not_explained():
    s = R.omitted_rows(VALS, range(59, 62), range(60, 62), "0.688", "0.56")
    assert R.explain_slip(s, {})["rows"][0]["status"] == "UNRESOLVED"
    e = R.explain_slip(s, {59: {"mark": "B1", "storey": "1F", "section": "0.20 x 0.40", "engine": "NOT_OWNED"}})
    assert not e["explained"] and e["rows"][0]["status"] == "ENGINE_SCOPE_QUESTION"


def test_doubled_row_blank_rows_and_bad_cells():
    vals = {1: "1.0", 2: "2.0", 4: "0.5"}                      # row 3 blank
    s = R.omitted_rows(vals, range(1, 5), range(1, 5), "3.5", "3.5")
    assert s["omitted"] == [] and s["extra"] == []
    with pytest.raises(R.Refused, match="expand the chain"):
        R.omitted_rows(vals, range(1, 5), range(2, 5), "3.5", "9.9")
    s2 = R.omitted_rows({1: "1.0", 2: "2.0"}, [1], [1, 2], "1.0", "3.0")
    assert s2["extra"] == [2] and s2["gap_m3"] == X("2.0")


# ------------------------------------------------------------------------------------------------ development villa
def _statement():
    sys.path.insert(0, str(ROOT / "research" / "agents_t706"))
    import t706_alsenan as A
    return A


def test_development_villa_statement_reproduces():
    A = _statement()
    s = A.build()
    committed = json.loads((ROOT / "research/agents_t706/out/T706_STATEMENT.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(s, default=str)) == committed


def test_development_villa_closes_to_storey_causes():
    s = _statement().build()
    assert s["key_residual_m3"] == "-0.462755" and s["storey_terms_sum_m3"] == "-0.462755"
    st = s["storeys"]
    assert [st[k]["difference_m3"] for k in ("GF", "1F", "2F")] == ["0.050478", "-0.556333", "0.043100"]
    for k in st:
        assert st[k]["geometry_claim_allowed"] and st[k]["checked"] == st[k]["released_lines"]
        assert st[k]["closure"]["closed"], k                    # every excluded / unowned face has a physical class
    assert st["GF"]["status"] == "ROUNDING_ONLY" and st["2F"]["status"] == "NOT_WHOLE_PANELS"
    assert st["1F"]["status"] == "UNRESOLVED_AMBIGUOUS"
    assert st["2F"]["radial_rings"] == [{"segments": 20, "segment_m2": 0.7679, "radius_m": 1.468}] * 2
    b = s["beam_slip"]
    assert b["omitted_rows"] == [59] and b["gap_m3"] == "-0.128000" and b["explained"]
    assert b["released_1f_beam_lines_unchanged_since_v3_0_58"] and b["engine_quantity_moved_m3"] == "0.000000"
