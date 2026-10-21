"""Generic tests: engine.source.cover_authority (cover basis, straight-run / count directions, cover errata).

Synthetic dimensions and covers only. No project number is used."""

import pytest

from engine.source import cover_authority as CA

D, W = 2400.0, 1800.0


def _basis(kind, v=50.0, **kw):
    return CA.classify_cover_basis(rule_kind=kind, value_mm=v, **kw)


def _corr(**kw):
    base = dict(correction_id="C1", component_id="X:BOTTOM", original_state=CA.LOWER_BOUND, original_kg=10.0,
                cover_basis=CA.MINIMUM_PROJECT_COVER, new_length_state=CA.SOURCE_MAXIMUM_STRAIGHT_RUN,
                new_count_direction=CA.EXACT, new_mass_state=CA.PROJECT_BASIS_NUMERIC,
                correction_reason="minimum cover", source_evidence="note n")
    base.update(kw)
    return CA.cover_correction(**base)


# ------------------------------------------------------------------ wording
def test_wording_kind_reads_minimum_maximum_and_exact():
    assert CA.wording_kind("يجب أن لا يقل سمك الغطاء الخرساني عن 5 سم") == CA.MINIMUM
    assert CA.wording_kind("Cover shall be not less than 50 mm") == CA.MINIMUM     # the minimum marker wins
    assert CA.wording_kind("Min. 30cm") == CA.MINIMUM
    assert CA.wording_kind("Max. 10cm") == CA.MAXIMUM
    assert CA.wording_kind("cover shall be 40 mm") == CA.EXACT_WORDING
    assert CA.wording_kind("cover 40") == CA.UNKNOWN_WORDING and CA.wording_kind(None) == CA.UNKNOWN_WORDING


# ------------------------------------------------------------------ cover basis
def test_exact_cover():
    b = _basis(CA.EXACT_WORDING)
    assert b["basis"] == CA.EXACT_PROJECT_COVER and b["label"] == "EXACT_PROJECT_COVER_50"
    run = CA.straight_run_claim(D, b)
    assert run == {"state": CA.SOURCE_EXACT_STRAIGHT_RUN, "direction": CA.EXACT, "value_mm": D - 100,
                   "interval_mm": [D - 100, D - 100]}


def test_minimum_cover():
    b = _basis(CA.MINIMUM)
    assert b["basis"] == CA.MINIMUM_PROJECT_COVER and b["label"] == "MINIMUM_PROJECT_COVER_50"
    run = CA.straight_run_claim(D, b)
    assert run["state"] == CA.SOURCE_MAXIMUM_STRAIGHT_RUN and run["direction"] == CA.UPPER
    assert run["value_mm"] == D - 100 and run["interval_mm"] == [None, D - 100]      # no lower limit


def test_a_detail_dimension_or_derived_cover_outranks_the_minimum_rule():
    d = _basis(CA.MINIMUM, detail_exact_mm=60)
    assert d["basis"] == CA.EXACT_PROJECT_COVER and d["source"] == "DETAIL_DIMENSION" and d["value_mm"] == 60
    g = _basis(CA.MINIMUM, derived_exact_mm=65)
    assert g["basis"] == CA.DERIVED_EXACT_COVER and CA.straight_run_claim(D, g)["direction"] == CA.EXACT
    # a minimum rule never becomes exact by itself, and a maximum-only rule is no cover authority
    assert _basis(CA.MINIMUM)["basis"] != CA.EXACT_PROJECT_COVER
    assert _basis(CA.MAXIMUM)["basis"] == CA.UNRESOLVED


def test_greater_than_minimum_cover_shortens_the_straight_run():
    at_min = CA.straight_run_mm(D, 50, 50)
    for c in (51, 55, 75, 100):
        assert CA.straight_run_mm(D, c, c) < at_min
        assert CA.straight_run_mm(D, 50, c) < at_min                    # one larger cover is enough
    assert CA.straight_run_mm(D, 75, 75) == at_min - 50


def test_unknown_actual_cover_gives_no_length():
    for b in (CA.classify_cover_basis(rule_kind=CA.UNKNOWN_WORDING, value_mm=50),
              CA.classify_cover_basis(rule_kind=CA.MINIMUM, value_mm=None)):
        assert b["basis"] == CA.UNRESOLVED
        run = CA.straight_run_claim(D, b)
        assert run == {"state": CA.STRAIGHT_RUN_UNRESOLVED, "direction": CA.NONE, "value_mm": None,
                       "interval_mm": [None, None]}


def test_bounded_cover():
    b = _basis(CA.MINIMUM, bounds_mm=(50, 75))
    run = CA.straight_run_claim(D, b)
    assert run["state"] == CA.SOURCE_BOUNDED_STRAIGHT_RUN and run["direction"] == CA.NONE
    assert run["value_mm"] is None and run["interval_mm"] == [D - 150, D - 100]
    for bad in ((0, 50), (75, 50), (None, 50)):
        with pytest.raises(CA.CoverAuthorityError):
            _basis(CA.MINIMUM, bounds_mm=bad)


# ------------------------------------------------------------------ monotonicity
def test_bar_length_is_strictly_decreasing_in_cover():
    covers = [0, 10, 25, 40, 50, 70, 75, 100, 250]
    runs = [CA.straight_run_mm(D, c, c) for c in covers]
    assert all(a > b for a, b in zip(runs, runs[1:]))
    for c1 in covers:
        assert CA.straight_run_mm(D, c1, 10) > CA.straight_run_mm(D, c1, 20)
    with pytest.raises(CA.CoverAuthorityError):
        CA.straight_run_mm(D, 1200, 1200)                                 # no run left
    with pytest.raises(CA.CoverAuthorityError):
        CA.straight_run_mm(D, -5, 50)


def test_minimum_cover_produces_the_maximum_straight_length():
    c_min = 50.0
    v = CA.straight_run_claim(D, _basis(CA.MINIMUM, c_min))["value_mm"]
    # every admissible actual cover (>= c_min) gives a run no longer than the value at the minimum
    for c in (c_min, c_min + 0.5, 60, 80, 120):
        assert CA.straight_run_mm(D, c, c) <= v
    assert max(CA.straight_run_mm(D, c, c) for c in (c_min, 60, 80, 120)) == v


def test_rate_count_is_non_increasing_in_cover_and_the_edge_bar_pulls_the_other_way():
    counts = [CA.count_at_cover(10, W, c) for c in (0, 25, 50, 75, 100, 200)]
    assert all(a >= b for a, b in zip(counts, counts[1:])) and counts[0] > counts[-1]
    assert CA.count_at_cover(10, W, 50) == 17                            # ceil(10 x 1.7)
    assert CA.count_at_cover(5, 1000, 0) == 5                            # exact multiples do not round up
    with pytest.raises(CA.CoverAuthorityError):
        CA.count_at_cover(0, W, 50)
    b = _basis(CA.MINIMUM)
    assert CA.count_direction("BARS_PER_METRE", b) == CA.NONE           # cover UPPER, edge bar LOWER
    assert CA.count_direction("BARS_PER_METRE", b, edge_bar_established=True) == CA.UPPER
    assert CA.count_direction("BARS_PER_METRE", _basis(CA.EXACT_WORDING)) == CA.LOWER
    assert CA.count_direction("EXPLICIT_COUNT", b) == CA.EXACT
    assert CA.count_direction("EXPLICIT_COUNT", CA.classify_cover_basis(rule_kind=CA.UNKNOWN_WORDING)) == CA.EXACT


# ------------------------------------------------------------------ direction algebra
def test_direction_algebra():
    E, U, L, N = CA.EXACT, CA.UPPER, CA.LOWER, CA.NONE
    assert CA.combine() == E and CA.combine(E, E) == E
    assert CA.combine(E, U) == U and CA.combine(U, U) == U
    assert CA.combine(E, L) == L and CA.combine(L, L) == L
    assert CA.combine(U, L) == N and CA.combine(L, U, E) == N
    assert CA.combine(N, E) == N and CA.combine(N, U) == N
    with pytest.raises(CA.CoverAuthorityError):
        CA.combine("ABOUT")
    assert CA.with_unquantified_additions(U, 0) == U
    assert CA.with_unquantified_additions(U, 2) == N and CA.with_unquantified_additions(E, 1) == L
    assert [CA.mass_state(d) for d in (E, L, U, N)] == [CA.SOURCE_DERIVED_EXACT, CA.LOWER_BOUND,
                                                         CA.UPPER_BOUND_KNOWN, CA.PROJECT_BASIS_NUMERIC]


def test_a_minimum_cover_straight_bar_with_unquantified_ends_is_no_bound():
    run = CA.straight_run_claim(D, _basis(CA.MINIMUM))
    d = CA.with_unquantified_additions(CA.combine(run["direction"], CA.EXACT), 1)
    assert CA.mass_state(d) == CA.PROJECT_BASIS_NUMERIC
    # straight with no additions: the number is a known upper bound, still not a lower bound
    assert CA.mass_state(CA.combine(run["direction"], CA.EXACT)) == CA.UPPER_BOUND_KNOWN
    # an exact cover with unquantified ends is what a lower bound needs
    ex = CA.straight_run_claim(D, _basis(CA.EXACT_WORDING))
    assert CA.mass_state(CA.with_unquantified_additions(ex["direction"], 1)) == CA.LOWER_BOUND


# ------------------------------------------------------------------ records
def test_no_silent_lower_bound_classification():
    with pytest.raises(CA.CoverAuthorityError, match="silent lower bound"):
        _corr(original_state="SOURCE_DERIVED_EXACT", new_mass_state=CA.LOWER_BOUND)
    rec = _corr()
    assert rec["NEW_MASS_STATE"] == CA.PROJECT_BASIS_NUMERIC and rec["RECORD_TYPE"] == CA.RECORD_TYPE
    assert rec["CORRECTION_KG"] == 0.0 and rec["RETAINED_NUMERIC_KG"] == 10.0
    # an exact cover may keep a lower bound: the refusal is specific to the minimum-cover maximum run
    ok = _corr(original_state=CA.PROJECT_BASIS_NUMERIC, cover_basis=CA.EXACT_PROJECT_COVER,
               new_length_state=CA.SOURCE_EXACT_STRAIGHT_RUN, new_mass_state=CA.LOWER_BOUND)
    assert ok["NEW_MASS_STATE"] == CA.LOWER_BOUND


def test_a_correction_never_adds_steel_and_always_changes_something():
    for bad in (dict(correction_kg=0.5), dict(correction_kg=-10.5), dict(original_kg=-1.0),
                dict(original_state=CA.PROJECT_BASIS_NUMERIC), dict(correction_reason=" "),
                dict(source_evidence=""), dict(cover_basis="ASSUMED_75"), dict(new_mass_state="PROBABLE"),
                dict(new_count_direction="ROUGHLY")):
        with pytest.raises(CA.CoverAuthorityError):
            _corr(**bad)
    retract = _corr(original_state=CA.PROJECT_BASIS_NUMERIC, correction_kg=-10.0)
    assert retract["RETAINED_NUMERIC_KG"] == 0.0 and retract["CORRECTION_KG"] == -10.0
    assert _corr(extra_field="x")["extra_field"] == "x"


def test_correction_conservation():
    cs = [_corr(correction_id="C1"), _corr(correction_id="C2", original_kg=4.0),
          _corr(correction_id="C3", original_kg=6.0, correction_kg=-6.0)]
    ok = CA.conservation(20.0, cs, 14.0)
    assert ok["all_pass"] and ok["correction_kg"] == -6.0
    assert not CA.conservation(20.0, cs, 20.0)["all_pass"]
    tampered = [dict(cs[0], RETAINED_NUMERIC_KG=11.0)] + cs[1:]
    assert not CA.conservation(20.0, tampered, 14.0)["checks"]["retained_plus_removed_is_original"]
    added = [dict(cs[0], CORRECTION_KG=1.0)]
    assert not CA.conservation(10.0, added, 11.0)["checks"]["no_positive_correction"]


def test_policy_record():
    p = CA.policy_record()
    assert p["record_type"] == CA.RECORD_TYPE and set(p["cover_bases"]) == set(CA.COVER_BASES)
    assert any("never a lower bound" in r for r in p["rules"])
    assert any("no actual cover is assumed" in r for r in p["rules"])
