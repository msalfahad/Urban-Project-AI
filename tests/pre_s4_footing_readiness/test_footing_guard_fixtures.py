"""Pre-S4 fixtures FT-01 ... FT-06 and RB-01 ... RB-03 (tiny synthetic inputs; no project coordinates, no donor or
reference quantity). The expected answer of each fixture comes from the fixture geometry / text itself.
Production code under test: engine.source.footing_rebar_guard (+ structural_schedule, schedule_table,
accurate_boq_rebar, unchanged consumers)."""

from __future__ import annotations

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import footing_rebar_guard as FG
from engine.source import schedule_grammar as SG
from engine.source import schedule_table as ST
from engine.source import structural_schedule as SS

UMM, TOL, EPS = 1.0, 20.0, 1.0
LIB = {"F": {"L_cm": 90, "W_cm": 80, "H_cm": 30, "keys": ["FT:1"]},
       "F10": {"L_cm": 280, "W_cm": 140, "H_cm": 50, "keys": ["FT:2"]},
       "F3": {"L_cm": 160, "W_cm": 140, "H_cm": 30, "keys": ["FT:3"]},
       "F5": {"L_cm": 240, "W_cm": 210, "H_cm": 40, "keys": ["FT:5"]}}


def rect(x0, y0, x1, y1):
    return SS.rect_candidate({"bounds": (x0, y0, x1, y1)})


def mark(key, value, x, y):
    return {"key": key, "value": value, "x": x, "y": y, "type": value}


def run(marks, outlines, **kw):
    res = SS.footing_occurrences(marks, LIB, outlines, umm=UMM, tol_mm=TOL, eps=EPS)
    return res, FG.occurrence_terminals(res, outlines, **kw)


# ------------------------------------------------------------------ FT-01 two footing tags in one outline
def test_ft01_two_tags_in_one_outline_is_a_source_conflict_with_hypotheses_never_nearest_wins():
    o = rect(0, 0, 3250, 1400)
    res, T = run([mark("a", "F", 2900, 600), mark("b", "F10", 500, 600)], [o])
    assert {r["geometry_state"] for r in res["rows"]} == {SS.COMBINED}
    assert all(r["qty"] is None for r in res["rows"])                      # neither tag wins
    assert {m["terminal"] for m in T["marks"]} == {FG.PARSED_SOURCE_CONFLICT}
    assert {m["occurrence_state"] for m in T["marks"]} == {FG.OCC_BLOCKED}
    hyp = T["marks"][0]["hypotheses"]
    assert hyp["tags_in_outline"] == ["F", "F10"] and hyp["drawn_outline_mm"] == [3250.0, 1400.0]
    assert T["outlines"][0]["terminal"] == FG.PARSED_SOURCE_CONFLICT and T["outlines"][0]["marks"] == ["a", "b"]


def test_ft01_moving_one_tag_closer_does_not_change_the_result():
    o = rect(0, 0, 3250, 1400)
    _, A = run([mark("a", "F", 2900, 600), mark("b", "F10", 500, 600)], [o])
    _, B = run([mark("a", "F", 3240, 10), mark("b", "F10", 1625, 700)], [o])
    assert [m["terminal"] for m in A["marks"]] == [m["terminal"] for m in B["marks"]]


# ------------------------------------------------------------------ FT-02 tag without geometry
def test_ft02_tag_without_outline_is_terminal_and_never_creates_a_count():
    res, T = run([mark("t", "F5", 0, 0)], [rect(9000, 9000, 9900, 9800)])     # the only outline is far away and F-sized
    r = res["rows"][0]
    assert r["geometry_state"] == SS.UNBOUND and r["qty"] is None
    m = T["marks"][0]
    assert m["terminal"] == FG.BLOCKED_GEOMETRY and FG.TAG_WITHOUT_OUTLINE in m["issues"]
    assert m["occurrence_state"] == FG.OCC_BLOCKED
    rel = FG.footing_release([], occurrence_state=m["occurrence_state"])
    assert rel["release_state"] == FG.REBAR_BLOCKED and rel["released_kg"] is None


def test_ft02_census_refuses_a_zero_on_a_blocked_tag():
    C = FG.Census()
    C.admit("TAG-t", "PLAN_TAG", "fixture")
    with pytest.raises(FG.GuardError):
        C.terminate("TAG-t", FG.BLOCKED_GEOMETRY, "TAG_WITHOUT_OUTLINE", quantity=0)
    C.terminate("TAG-t", FG.BLOCKED_GEOMETRY, "TAG_WITHOUT_OUTLINE")
    assert C.check()["conserved"]


# ------------------------------------------------------------------ FT-03 geometry without tag
def test_ft03_outline_without_tag_is_terminal_measured_type_unresolved():
    tagged, untagged = rect(0, 0, 900, 800), rect(5000, 0, 6600, 1400)
    res, T = run([mark("t", "F", 450, 400)], [tagged, untagged])
    assert len(res["rows"]) == 1                                            # the mark-driven binder never sees it
    by = {o["outline"]: o for o in T["outlines"]}
    assert by[untagged["id"]]["terminal"] == FG.BLOCKED_SEMANTICS
    assert by[untagged["id"]]["issues"] == [FG.OUTLINE_WITHOUT_TAG]
    assert by[tagged["id"]]["terminal"] == FG.PARSED_BOUND
    assert T["summary"]["outlines"] == 2                                    # nothing disappears


# ------------------------------------------------------------------ FT-04 schedule header-position binding
def _table(attr_xs):
    """Three columns (0-100-200-300); header band 100->50 prints L / W / H; data band 50->0 holds ATTRIBs tagged
    W, H, DEPHT at the given x positions."""
    h = [(100.0, 0.0, 300.0, "h0"), (50.0, 0.0, 300.0, "h1"), (0.0, 0.0, 300.0, "h2")]
    v = [(x, 0.0, 100.0, f"v{x}") for x in (0.0, 100.0, 200.0, 300.0)]
    items = [ST.Item("hL", "L", 50, 75), ST.Item("hW", "W", 150, 75), ST.Item("hH", "H", 250, 75)]
    items += [ST.Item(f"a{t}", "90", x, 25, "ATTRIB", t, "INS") for t, x in attr_xs.items()]
    return ST.read(items, h, v, eps=1.0)


def test_ft04_binding_comes_from_the_drawn_header_not_the_attribute_tag():
    tab = _table({"W": 50, "H": 150, "DEPHT": 250})                         # tags W/H/DEPHT print under L/W/H
    good = FG.header_binding(tab, [0], 1, {"W": "L", "H": "W", "DEPHT": "H"})
    assert good["state"] == "BOUND_BY_HEADER" and good["conflicts"] == []
    naive = FG.header_binding(tab, [0], 1, {"W": "W", "H": "H", "DEPHT": "H"})   # binding by tag name
    assert naive["state"] == FG.HEADER_BINDING_CONFLICT
    assert {c["tag"] for c in naive["conflicts"]} == {"W", "H"}


def test_ft04_a_silent_column_swap_in_the_drawing_is_caught():
    tab = _table({"W": 150, "H": 50, "DEPHT": 250})                         # the block was redrawn with W/H swapped
    r = FG.header_binding(tab, [0], 1, {"W": "L", "H": "W", "DEPHT": "H"})
    assert r["state"] == FG.HEADER_BINDING_CONFLICT
    assert {c["tag"]: c["derived"] for c in r["conflicts"]} == {"W": ["W"], "H": ["L"]}


# ------------------------------------------------------------------ FT-05 F / F10 conflict survives to release
def test_ft05_source_conflict_survives_to_the_release_state():
    o = rect(0, 0, 3250, 1400)
    _, T = run([mark("a", "F", 2900, 600), mark("b", "F10", 500, 600)], [o])
    occ_state = T["marks"][0]["occurrence_state"]
    blocked = {"part_id": "OCC-CONFLICT:BOTTOM_SHORT", "category": "FOUNDATIONS", "component": "FOOTING_BOTTOM_SHORT",
               "state": AR.BLOCKED_UNQUANTIFIED, "kg": None, "basis": ["SCHEDULE", "DRAWING_OCCURRENCE"]}
    rel = FG.footing_release([blocked], occurrence_state=occ_state)
    assert rel["release_state"] == FG.REBAR_BLOCKED and rel["released_kg"] is None
    # even a fully computed part cannot release a blocked occurrence
    computed = dict(blocked, part_id="OCC-CONFLICT:LONG", component="FOOTING_BOTTOM_LONG", state=AR.VERIFIED, kg=9.9)
    assert FG.footing_release([computed], occurrence_state=occ_state)["release_state"] == FG.REBAR_BLOCKED
    s = AR.summarise([blocked])
    assert s["project"]["final_rebar"] == AR.FINAL_REBAR_NOT_ESTABLISHED
    assert s["categories"]["FOUNDATIONS"]["official_status"] == AR.BLOCKED


# ------------------------------------------------------------------ FT-06 multiple occurrences + count query
def test_ft06_count_query_keeps_the_plan_count_and_survives_as_occurrence_conflict():
    outs = [rect(0, 0, 1600, 1400), rect(5000, 0, 6600, 1400)]
    res, T = run([mark("p", "F3", 800, 700), mark("q", "F3", 5800, 700)], outs, count_queries={"F3": "OQ-QUERY"})
    assert sum(1 for r in res["rows"] if r["geometry_state"] == SS.CONFIRMED) == 2      # plan count = 2 outlines
    assert {m["terminal"] for m in T["marks"]} == {FG.PARSED_BOUND}
    assert all(FG.OCCURRENCE_COUNT_CONFLICT in m["issues"] and m["count_query"] == "OQ-QUERY" for m in T["marks"])
    assert {m["occurrence_state"] for m in T["marks"]} == {FG.OCC_PROVISIONAL}
    v = {"part_id": "p:SHORT", "category": "FOUNDATIONS", "component": "FOOTING_BOTTOM_SHORT", "state": AR.VERIFIED,
         "kg": 10.0, "basis": ["SCHEDULE"]}
    rel = FG.footing_release([v], occurrence_state=FG.OCC_PROVISIONAL)
    assert rel["release_state"] == FG.REBAR_PROVISIONAL                    # never VERIFIED while the query is open


def test_ft06_without_a_query_the_same_occurrences_are_established():
    outs = [rect(0, 0, 1600, 1400), rect(5000, 0, 6600, 1400)]
    _, T = run([mark("p", "F3", 800, 700), mark("q", "F3", 5800, 700)], outs)
    assert {m["occurrence_state"] for m in T["marks"]} == {FG.OCC_RELEASED}


@pytest.mark.parametrize("q", [1, "1", 2.0, " 3 ", ""])
def test_ft06_a_count_query_never_carries_a_number(q):
    outs = [rect(0, 0, 1600, 1400)]
    res = SS.footing_occurrences([mark("p", "F3", 800, 700)], LIB, outs, umm=UMM, tol_mm=TOL, eps=EPS)
    with pytest.raises(FG.GuardError):
        FG.occurrence_terminals(res, outs, count_queries={"F3": q})


# ------------------------------------------------------------------ RB-01 ambiguous bar-token parity
@pytest.mark.parametrize("raw,cls", [("2%%c14/20cm", FG.COUNT_DIA_AT_SPACING), ("%%c12/20cm", FG.DIA_AT_SPACING),
                                     ("%%C12MM/15cm", FG.DIA_AT_SPACING),
                                     ("* ST. OF COLUMN- 6%%C8/m", FG.SENTENCE_EMBEDDED),
                                     ("T=10cm / 5%%c10/m E.W.", FG.SENTENCE_EMBEDDED)])
def test_rb01_known_disagreement_classes_fail_closed(raw, cls):
    a = FG.admit_token(raw)
    assert a["token_class"] == cls and a["decision"] == FG.FAIL_CLOSED
    assert a["reason"].startswith("KNOWN_DISAGREEMENT_CLASS")


@pytest.mark.parametrize("raw,form", [("6%%c14/m", (6, 14, True, None, None)), ("8%%c12", (8, 12, False, None, None)),
                                      ("4%%c16/Top", (4, 16, False, None, "TOP"))])
def test_rb01_agreeing_classes_are_admitted_with_one_normalised_form(raw, form):
    a = FG.admit_token(raw)
    assert a["decision"] == FG.ADMITTED and a["parity"] == "ALL_APPLICABLE_PARSERS_AGREE"
    f = a["form"]
    assert (f["count"], f["dia_mm"], f["per_m"], f["spacing_cm"], f["position"]) == form
    assert len({repr(sorted(v.items())) for v in a["parsers"].values()}) == 1


def test_rb01_a_live_parser_drift_fails_closed(monkeypatch):
    from engine.source import structural_schedule as SSm
    real = SSm.bar_spec
    monkeypatch.setattr(SSm, "bar_spec", lambda t: [dict(x, per_m=False) for x in real(t)])   # drops '/m'
    a = FG.admit_token("6%%c14/m")
    assert a["decision"] == FG.FAIL_CLOSED and a["reason"].startswith("LIVE_PARSER_DISAGREEMENT")


# ------------------------------------------------------------------ RB-02 split count / diameter cells
@pytest.mark.parametrize("c,d,form", [("13", "12", (13, 12, False)), ("9", "14/m", (9, 14, True)),
                                      ("8", "16/m", (8, 16, True))])
def test_rb02_split_cells_route_through_bar_from_cells_only(c, d, form):
    a = FG.admit_cells(c, d)
    assert a["decision"] == FG.ADMITTED and a["route"] == FG.P_CELLS
    assert (a["form"]["count"], a["form"]["dia_mm"], a["form"]["per_m"]) == form
    assert list(a["parsers"]) == [FG.P_CELLS]
    assert SG.parse_bar(c)["grammar"] == "UNPARSED"                        # the single-text parsers cannot read a cell


@pytest.mark.parametrize("c,d,why", [("", "", "EMPTY_CELL"), ("x", "12", "UNREADABLE"), ("6", "14/cm", "UNREADABLE")])
def test_rb02_empty_or_unreadable_cells_fail_closed(c, d, why):
    a = FG.admit_cells(c, d)
    assert a["decision"] == FG.FAIL_CLOSED and a["reason"].startswith(why)


# ------------------------------------------------------------------ RB-03 BOXED pair without semantics
@pytest.mark.parametrize("raw", ["3+4", "3+5", "3 + 6", "3+8"])
def test_rb03_boxed_pair_is_never_a_bar_token(raw):
    assert FG.token_class(raw) == FG.BOXED_PAIR
    a = FG.admit_token(raw)
    assert a["decision"] == FG.FAIL_CLOSED and a["reason"].startswith("BLOCKED_SEMANTICS")
    for p in (FG.P_PARSE_BAR, FG.P_BAR_SPEC, FG.P_SLAB):
        assert FG._run(p, raw) is None                                     # no Urban parser accepts it today


@pytest.mark.parametrize("sem", [FG.UNRESOLVED, FG.PROJECT_PATTERN_ONLY, FG.GENERIC_HYPOTHESIS])
def test_rb03_unresolved_boxed_is_blocked_unquantified_and_caps_the_footing_at_lower_bound(sem):
    b = FG.boxed_part(part_id="X:BOXED", semantics_class=sem, raw_value="3+4")
    assert b["state"] == AR.BLOCKED_UNQUANTIFIED and b["kg"] is None
    bottom = {"part_id": "X:SHORT", "category": "FOUNDATIONS", "component": "FOOTING_BOTTOM_SHORT",
              "state": AR.VERIFIED, "kg": 5.0, "basis": ["SCHEDULE"]}
    rel = FG.footing_release([bottom, b])
    assert rel["release_state"] == FG.REBAR_LOWER_BOUND                     # not blocked as a whole
    assert rel["released_kg"] == 5.0 and rel["unquantified_components"] == ["BOXED_REBAR"]


@pytest.mark.parametrize("sem", [FG.SOURCE_EXPLICIT, FG.SOURCE_DERIVED_HIGH_CONFIDENCE])
def test_rb03_quantifiable_semantics_are_not_placeholdered(sem):
    with pytest.raises(FG.GuardError):
        FG.boxed_part(part_id="X:BOXED", semantics_class=sem, raw_value="3+4")


def test_rb03_census_keeps_boxed_blocked_and_never_zero():
    C = FG.Census()
    C.admit("CELL-boxed", "SCHEDULE_CELL", "fixture")
    with pytest.raises(FG.GuardError):
        C.terminate("CELL-boxed", FG.BLOCKED_SEMANTICS, "3+4 unexplained", quantity=0.0)
    C.terminate("CELL-boxed", FG.BLOCKED_SEMANTICS, "3+4 unexplained")
    C.admit("CELL-lost", "SCHEDULE_CELL", "fixture")                        # admitted, never terminated
    chk = C.check()
    assert not chk["conserved"] and chk["unterminated"] == ["CELL-lost"]
    assert chk["source_items"] == 2 and chk["terminal_items"] == 1


def test_census_rejects_a_state_outside_the_list():
    C = FG.Census()
    C.admit("i", "X", "fixture")
    with pytest.raises(FG.GuardError):
        C.terminate("i", "COUNTED", "not a pre-S4 terminal")
