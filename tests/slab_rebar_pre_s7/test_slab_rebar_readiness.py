"""Generic tests: engine.source.slab_rebar_readiness (PRE-S7 brief §23). Synthetic panels and rules only."""

import pytest

from engine.source import cover_authority as CA
from engine.source import graphic_evidence as GE
from engine.source import slab_rebar_readiness as SR

TABLE = {100: "Y10@200", 125: "Y10@200", 150: "Y10@200", 175: "Y12@200", 200: "Y12@200", 250: "Y12@200",
         300: "Y12@200"}


# ------------------------------------------------------------------ thickness
def test_local_thickness_overrides_floor_and_default():
    d = SR.thickness_decision(local=[200], floor=[180], default=[160])
    assert d["value_mm"] == 200 and d["authority"] == SR.LOCAL_PANEL
    assert [o["level"] for o in d["overridden"]] == [SR.FLOOR_RULE, SR.PROJECT_DEFAULT]
    f = SR.thickness_decision(floor=[180], default=[160])
    assert f["value_mm"] == 180 and f["authority"] == SR.FLOOR_RULE
    p = SR.thickness_decision(default=[160])
    assert p["value_mm"] == 160 and p["authority"] == SR.PROJECT_DEFAULT
    same = SR.thickness_decision(local=[160], default=[160])          # a local mark equal to the default confirms it
    assert same["authority"] == SR.LOCAL_PANEL and same["confirms"] == [SR.PROJECT_DEFAULT] and not same["overridden"]
    clash = SR.thickness_decision(local=[160, 180], default=[160])      # never voted, never the nearest value
    assert clash["authority"] == SR.SOURCE_CONFLICT and clash["value_mm"] is None
    assert SR.thickness_decision()["authority"] == SR.THICKNESS_UNRESOLVED


# ------------------------------------------------------------------ temperature table
def test_160_mm_has_no_temperature_row():
    r = SR.temperature_row(160, TABLE)
    assert r["state"] == SR.TABLE_NO_EXACT_ROW and r["value"] is None and r["row"] is None
    assert r["bracket_context_only"] == [150, 175]


def test_180_mm_has_no_temperature_row():
    r = SR.temperature_row(180, TABLE)
    assert r["state"] == SR.TABLE_NO_EXACT_ROW and r["value"] is None
    assert r["bracket_context_only"] == [175, 200]


def test_no_interpolation_and_exact_rows_only():
    for t in (101, 149.9, 160, 162.5, 180, 190, 260):
        r = SR.temperature_row(t, TABLE)
        assert r["value"] is None and r["interpolated"] is False, t
    for t, v in TABLE.items():
        r = SR.temperature_row(t, TABLE)
        assert r["state"] == SR.TABLE_EXACT_ROW and r["value"] == v
    # even when both bracketing rows agree (175 / 200 are both Y12@200), 180 is not given that value
    assert SR.temperature_row(180, TABLE)["value"] is None
    assert SR.temperature_row(None, TABLE)["state"] == SR.TEMPERATURE_THICKNESS_UNRESOLVED


# ------------------------------------------------------------------ cover
def test_minimum_25_mm_cover_is_not_exact():
    b = SR.cover_basis("cover shall not be less than 25 mm in slabs", 25)
    assert b["basis"] == CA.MINIMUM_PROJECT_COVER and b["label"] == "MINIMUM_PROJECT_COVER_25"
    run = SR.straight_run_state(3000, b)
    assert run["state"] == SR.UPPER_BOUND and run["run"]["value_mm"] == 2950
    assert run["state"] not in (SR.EXACT_PROJECT_LENGTH, SR.LOWER_BOUND)
    # with unquantified ends the minimum-cover number is only a project-basis value
    assert SR.straight_run_state(3000, b, unquantified_ends=2)["state"] == SR.PROJECT_BASIS_NUMERIC
    # only a dimension in the detail makes it exact
    ex = SR.cover_basis("cover shall not be less than 25 mm", 25, detail_exact_mm=30)
    assert SR.straight_run_state(3000, ex)["state"] == SR.EXACT_PROJECT_LENGTH
    assert SR.straight_run_state(3000, ex, unquantified_ends=1)["state"] == SR.LOWER_BOUND
    assert SR.length_state(CA.NONE, blocked=True) == SR.BLOCKED_UNQUANTIFIED
    # the Arabic wording and the English phrasings all read as a minimum
    for txt in ("يجب أن لا يقل سمك الغطاء عن 2.5 سم", "not less than 25", "shall not be less than 25",
                "no less than 25"):
        assert SR.cover_wording_kind(txt) == CA.MINIMUM, txt


# ------------------------------------------------------------------ spans and rules
def test_clear_span_versus_centreline_span():
    s = SR.spans(3800, 200, 300)
    assert s == {"clear_mm": 3800.0, "centreline_mm": 4050.0}
    assert SR.span_for_basis(SR.CLEAR_SPAN, **{k: v for k, v in s.items()}) == 3800
    assert SR.span_for_basis(SR.SUPPORT_CENTERLINE, **s) == 4050
    assert SR.spans(3800, 200, None)["centreline_mm"] is None          # a support width unknown: no centreline span
    assert SR.span_for_basis(SR.L_UNDEFINED, **s) is None


def _gate(kind, support, **kw):
    base = dict(L_basis=SR.CLEAR_SPAN, direction="X", support_type=support, origin=SR.FACE_OF_SUPPORT)
    base.update(kw)
    return SR.rule_gate(kind, **base)


def test_025L_at_a_non_continuous_support():
    g = _gate(SR.TOP_NONCONT, SR.NON_CONTINUOUS)
    assert g["state"] == SR.RELEASABLE
    assert SR.rule_extent(SR.TOP_NONCONT, gate=g, L1_mm=4000) == pytest.approx(1000)
    assert _gate(SR.TOP_NONCONT, SR.CONTINUOUS)["blockers"] == ["RULE_NOT_FOR_THIS_SUPPORT_TYPE"]


def test_030L_at_a_continuous_support_uses_the_larger_span():
    g = _gate(SR.TOP_CONT, SR.CONTINUOUS)
    assert SR.rule_extent(SR.TOP_CONT, gate=g, L1_mm=3000, L2_mm=5000) == pytest.approx(1500)
    assert SR.rule_extent(SR.TOP_CONT, gate=g, L1_mm=5000, L2_mm=3000) == pytest.approx(1500)
    with pytest.raises(SR.SlabReadinessError):
        SR.rule_extent(SR.TOP_CONT, gate=g, L1_mm=3000)                # needs both spans


def test_0125L_bottom_cutoff():
    g = _gate(SR.BOTTOM_STOP, SR.CONTINUOUS, direction="Y")
    assert SR.rule_extent(SR.BOTTOM_STOP, gate=g, L1_mm=4800) == pytest.approx(600)
    assert _gate(SR.BOTTOM_STOP, SR.NON_CONTINUOUS)["state"] == SR.RULE_BLOCKED


def test_unknown_L_basis_blocks_release():
    for kw, why in ((dict(L_basis=SR.L_UNDEFINED), "L_BASIS_UNKNOWN"), (dict(L_basis=SR.OTHER), "L_BASIS_UNKNOWN"),
                    (dict(direction=None), "DIRECTION_UNKNOWN"), (dict(origin=None), "ORIGIN_UNKNOWN"),
                    (dict(support_type=SR.CONTINUITY_UNRESOLVED), "SUPPORT_TYPE_UNKNOWN")):
        g = _gate(SR.TOP_CONT, SR.CONTINUOUS, **kw)
        assert g["state"] == SR.RULE_BLOCKED and why in g["blockers"]
        with pytest.raises(SR.SlabReadinessError):
            SR.rule_extent(SR.TOP_CONT, gate=g, L1_mm=3000, L2_mm=4000)


def test_50_percent_bottom_bar_split():
    assert SR.bottom_split(12) == {"state": "SPLIT_EXACT", "stop": 6, "continue": 6,
                                   "which": "WHICH_50_PERCENT_UNRESOLVED"}
    odd = SR.bottom_split(13)
    assert odd["state"] == "SPLIT_AMBIGUOUS_ODD_COUNT" and odd["stop"] == [6, 7] and odd["continue"] == [6, 7]
    assert SR.bottom_split(None)["state"] == "COUNT_BASIS_UNRESOLVED"
    assert SR.bottom_split(12, which_specified=True)["which"] == "SPECIFIED"


# ------------------------------------------------------------------ bar runs and supports
def _fam(fid, panel, d="X", dia=10, rate=5):
    return {"family_id": fid, "panel": panel, "direction": d, "dia_mm": dia, "rate": rate, "count_mode": "BARS_PER_METRE"}


def test_a_continuous_bar_across_two_panels_is_counted_once():
    fams = [_fam("A-X", "A"), _fam("B-X", "B"), _fam("C-X", "C"), _fam("A-Y", "A", d="Y")]
    links = [{"support_id": "S1", "panels": ("A", "B"), "direction": "X", "support_type": SR.CONTINUOUS},
             {"support_id": "S2", "panels": ("B", "C"), "direction": "X", "support_type": SR.NON_CONTINUOUS}]
    out = SR.bar_runs(fams, links)
    runs = {tuple(r["families"]): r for r in out["runs"]}
    assert ("A-X", "B-X") in runs and runs[("A-X", "B-X")]["supports_crossed"] == ["S1"]
    assert runs[("A-X", "B-X")]["multi_panel"] is True
    assert ("C-X",) in runs and ("A-Y",) in runs                         # no continuity across a non-continuous edge
    owned = [f for r in out["runs"] for f in r["families"]]
    assert sorted(owned) == sorted(f["family_id"] for f in fams)       # every family in exactly one run
    # a spec mismatch is recorded, never merged
    m = SR.bar_runs([_fam("A-X", "A"), _fam("B-X", "B", dia=12)], links[:1])
    assert len(m["runs"]) == 2 and m["mismatches"][0]["support_id"] == "S1"
    with pytest.raises(SR.SlabReadinessError):
        SR.bar_runs([_fam("A-X", "A"), _fam("A-X2", "A")], [])         # one family per panel and direction


def test_a_support_top_bar_is_counted_once():
    edges = [{"panel": "A", "neighbour": "B", "support_ref": "BM1", "edge_index": 1, "length_mm": 4000,
              "continuity": "CONTINUOUS"},
             {"panel": "B", "neighbour": "A", "support_ref": "BM1", "edge_index": 3, "length_mm": 4000,
              "continuity": "CONTINUOUS"},
             {"panel": "A", "neighbour": None, "support_ref": "BM2", "edge_index": 0, "length_mm": 3000,
              "continuity": "DISCONTINUOUS"}]
    sup = SR.supports_from_edges(edges)
    assert len(sup) == 2
    shared = [s for s in sup if s["support_ref"] == "BM1"][0]
    assert shared["sides"] == ("A", "B") and shared["seen_from"] == ["A", "B"] and shared["symmetric"]
    owned = SR.support_bar_owner(shared, ["TOK-1"])
    assert owned == [{"token": "TOK-1", "owner": "SUPPORT", "support_ref": "BM1", "sides": ("A", "B"), "counted": 1}]
    one_sided = SR.supports_from_edges(edges[:1])
    assert one_sided[0]["symmetric"] is False                          # seen from one panel only: flagged


# ------------------------------------------------------------------ openings
def test_opening_intersects_x_bars_only():
    # X bars cover the whole panel; Y bars exist only in a strip away from the opening
    eff = SR.opening_effect((1000, 1000, 1600, 1400), {"X": (0, 0, 4000, 3000), "Y": (3000, 0, 4000, 3000)})
    assert eff["X"]["effect"] == SR.INTERRUPTED and eff["X"]["band_mm"] == [1000, 1400]
    assert eff["Y"]["effect"] == SR.UNAFFECTED
    one_way = SR.opening_effect((1000, 1000, 1600, 1400), {"X": (0, 0, 4000, 3000), "Y": None})
    assert one_way["Y"]["effect"] == SR.NOT_PRESENT


def test_opening_intersects_x_and_y_bars():
    eff = SR.opening_effect((1000, 1000, 1600, 1400), {"X": (0, 0, 4000, 3000), "Y": (0, 0, 4000, 3000)})
    assert eff["X"]["effect"] == SR.INTERRUPTED and eff["Y"]["effect"] == SR.INTERRUPTED
    assert eff["Y"]["band_mm"] == [1000, 1600] and eff["X"]["count_in_band"] == SR.COUNT_BASIS_UNRESOLVED
    full = SR.opening_effect((0, 1000, 4000, 1400), {"X": (0, 0, 4000, 3000), "Y": (0, 0, 4000, 3000)})
    assert full["X"]["effect"] == SR.REMOVED and full["Y"]["effect"] == SR.INTERRUPTED


def test_opening_extra_bars_stay_separate_from_deductions():
    rec = SR.opening_record("OP1", deductions=[{"family": "A-X", "band_mm": [1000, 1400]}],
                            extras=[{"component": "OPENING_TRIM", "source": "detail"}])
    assert rec["net_figure"] is None and len(rec["deductions"]) == 1 and len(rec["extras"]) == 1
    with pytest.raises(SR.SlabReadinessError):
        SR.opening_record("OP1", deductions=[], extras=[{"component": "OPENING_TRIM", "netted_against": "A-X"}])


def test_void_with_a_reinforcement_tag_is_a_source_conflict():
    c = SR.void_conflict(void_marks=["X-LINES", "VOID TEXT"], slab_marks=["T 16 MARK", "BAR CALLOUT"])
    assert c["state"] == SR.SOURCE_CONFLICT and set(c["candidates"]) == {"SLAB", "VOID", "OPENING_EXTRA",
                                                                       "MISBOUND_TEXT"}
    s = SR.scope_decision(slab_face=True, void=True, slab_evidence=True)
    assert s["scope"] == SR.CLASSIFICATION_BLOCKED and s["conflict"] == SR.SOURCE_CONFLICT
    assert SR.void_conflict(void_marks=["X"], slab_marks=[])["state"] == "VOID"
    assert SR.scope_decision(slab_face=True, void=True)["scope"] == SR.VOID_OR_OPENING


# ------------------------------------------------------------------ counts
def test_spacing_count_is_ambiguous_without_a_project_rule():
    c = SR.count_decision("BARS_PER_METRE", 5, distribution_mm=1730)
    assert c["state"] == SR.COUNT_BASIS_UNRESOLVED and c["count"] is None and c["ambiguous"]
    assert c["candidates"] == {"CEIL": 9, "CEIL_PLUS_1": 10, "FLOOR_PLUS_1": 9}
    assert c["rate"] == 5 and c["spacing_mm"] == 200 and c["distribution_mm"] == 1730     # kept apart
    exp = SR.count_decision("EXPLICIT_COUNT", 3)
    assert exp["state"] == SR.COUNT_EXPLICIT and exp["count"] == 3
    ruled = SR.count_decision("BARS_PER_METRE", 5, distribution_mm=1730, rule="CEIL_PLUS_1")
    assert ruled["state"] == SR.COUNT_BASIS_EXPLICIT and ruled["count"] == 10


def test_edge_bar_is_ambiguous():
    c = SR.count_decision("BARS_PER_METRE", 5, distribution_mm=2000)      # an exact multiple: edge bar decides
    assert c["candidates"]["CEIL"] == 10 and c["candidates"]["CEIL_PLUS_1"] == 11
    assert c["candidates"]["FLOOR_PLUS_1"] == 11 and c["edge_bar"] == SR.EDGE_BAR_UNRESOLVED and c["count"] is None


# ------------------------------------------------------------------ graphics, scope, conservation
def test_nts_graphic_cannot_create_length():
    for cls in (GE.GRAPHIC_NTS_OR_UNDIMENSIONED, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY):
        r = SR.graphic_length(cls, 1200, basis=GE.PROJECT_SOURCE_GEOMETRY, nts=True)
        assert r["state"] == SR.BLOCKED_UNQUANTIFIED and r["length_mm"] is None
    assert SR.graphic_length(GE.GRAPHIC_EXPLICIT_DIMENSIONED, 1200, basis=GE.PLOTTED_SCALE,
                             nts=True)["state"] == SR.BLOCKED_UNQUANTIFIED
    ok = SR.graphic_length(GE.GRAPHIC_EXPLICIT_DIMENSIONED, 1200, basis=GE.PRINTED_DIMENSION)
    assert ok["state"] == "ADMITTED" and ok["length_mm"] == 1200


def test_special_structures_are_excluded():
    for kind in ("STAIR", "DOME", "LIFT_PIT", "POOL", "GROUND_SLAB"):
        s = SR.scope_decision(slab_face=True, special=[kind])
        assert s["scope"] == SR.EXCLUDED_SPECIAL and s["special"] == [kind]
    tank = SR.scope_decision(slab_face=True, designated_special=["WATER_TANK"])
    assert tank["scope"] == SR.CLASSIFICATION_BLOCKED
    assert SR.scope_decision(slab_face=True)["scope"] == SR.IN_SCOPE
    assert SR.scope_decision(slab_face=True, outside=True)["scope"] == SR.NOT_SLAB
    with pytest.raises(SR.SlabReadinessError):
        SR.scope_decision(slab_face=True, special=["BALCONY_MAYBE"])
    with pytest.raises(SR.SlabReadinessError):
        SR.component("BOTTOM_X", owner="P1", project_support=None)       # no project source: not instantiated
    with pytest.raises(SR.SlabReadinessError):
        SR.component("BOTTOM_X", owner="P1", project_support="plan token", kg=12.0)
    c = SR.component("BOTTOM_X", owner="P1", project_support="plan token", blockers=["COUNT_BASIS_UNRESOLVED"])
    assert c["readiness"] == SR.BLOCKED_FROM_S7 and c["kg"] is None


def test_population_conservation():
    rows = [{"id": "F1", "scope": SR.IN_SCOPE}, {"id": "F2", "scope": SR.EXCLUDED_SPECIAL, "special": ["DOME"]},
            {"id": "F3", "scope": SR.VOID_OR_OPENING}]
    assert SR.population_conservation(["F1", "F2", "F3"], rows)["all_pass"]
    lost = SR.population_conservation(["F1", "F2", "F3", "F4"], rows)
    assert not lost["all_pass"] and lost["missing"] == ["F4"]
    twice = SR.population_conservation(["F1", "F2", "F3"], rows + [{"id": "F1", "scope": SR.IN_SCOPE}])
    assert not twice["all_pass"]
    leak = SR.population_conservation(["F1"], [{"id": "F1", "scope": SR.IN_SCOPE, "special": ["STAIR"]}])
    assert not leak["checks"]["no_excluded_row_in_scope"]


def test_token_conservation():
    recs = [SR.terminate_token("T1", SR.BOUND_TO_PANEL, bar_families=["P1-X"], bound_to="P1", reason="inside P1"),
            SR.terminate_token("T2", SR.DESIGN_NOTE, reason="plan note"),
            SR.terminate_token("T3", SR.DUPLICATE_GRAPHIC, reason="same text, same place")]
    assert SR.token_conservation(["T1", "T2", "T3"], recs)["all_pass"]
    assert SR.token_conservation(["T1", "T2", "T3", "T4"], recs)["missing"] == ["T4"]
    again = recs + [SR.terminate_token("T4", SR.BOUND_TO_PANEL, bar_families=["P1-X"], reason="also inside P1")]
    assert not SR.token_conservation(["T1", "T2", "T3", "T4"], again)["checks"]["no_bar_family_from_two_tokens"]
    with pytest.raises(SR.SlabReadinessError):
        SR.terminate_token("T5", SR.BOUND_TO_PANEL, bar_families=["P1-X", "P2-X"], reason="two panels")
    with pytest.raises(SR.SlabReadinessError):
        SR.terminate_token("T6", SR.DUPLICATE_GRAPHIC, bar_families=["P1-X"], reason="dup")
    with pytest.raises(SR.SlabReadinessError):
        SR.terminate_token("T7", "PROBABLY_BOTTOM", reason="?")
    multi = SR.terminate_token("T8", SR.BOUND_TO_MULTI_PANEL_BAR_RUN, bar_families=["P1-X", "P2-X"],
                               reason="one bar drawn across two panels", explicit_multi=True)
    assert len(multi["bar_families"]) == 2


def test_policy_record():
    p = SR.policy_record()
    assert set(p["token_states"]) == set(SR.TOKEN_STATES) and len(p["token_states"]) == 10
    assert SR.LENGTH_STATES == ("EXACT_PROJECT_LENGTH", "LOWER_BOUND", "UPPER_BOUND", "PROJECT_BASIS_NUMERIC",
                                "BLOCKED_UNQUANTIFIED")
