"""Generic tests: engine.source.delta_correction (link-path authority + CORRECTION_ERRATA records).

Synthetic envelopes and hand-computed answers only. No project number is used."""

import math

import pytest

from engine.source import delta_correction as DC
from engine.source import delta_release as DR
from engine.source import graphic_evidence as GE
from engine.source import link_geometry as LG

DEFICIT = 8.0 - 2.0 * math.pi                                  # per closed link, times R


def _corr(**kw):
    base = dict(correction_id="C1", original_delta_component_id="O:C:CORE_PATH", original_kg=10.0,
                correction_kg=-10.0, correction_reason="sharp path is not a lower bound",
                source_evidence="no bend radius in source", new_authority_state=DC.MODELLED_POLYGONAL_EQUIVALENT,
                new_release_state=DC.BLOCKED_UNQUANTIFIED)
    base.update(kw)
    return DC.correction(**base)


# ------------------------------------------------------------------ geometry
def test_sharp_rectangular_perimeter():
    # 200 x 400, c 25, d 8 -> centreline 142 x 342 -> 2 x 142 + 2 x 342 = 968 mm
    assert DC.sharp_loop_mm(142, 342) == 968.0
    assert DC.sharp_loop_mm(142, 342) == LG.core_path_mm(200, 400, 25, 8)
    for W, T in ((0, 100), (100, 0), (-5, 100), (None, 100)):
        with pytest.raises(DC.CorrectionError):
            DC.sharp_loop_mm(W, T)


def test_rounded_90_degree_corner():
    for R in (0.0, 10.0, 32.0):
        sharp, arc = DC.corner_lengths_mm(R)
        assert sharp == 2 * R and arc == pytest.approx(math.pi * R / 2)
        assert 4 * (sharp - arc) == pytest.approx(DC.corner_deficit_mm(R))
    # a square envelope bent at its largest radius is a circle: 4 x 100 - (8 - 2 pi) 50 = 100 pi
    assert DC.rounded_loop_mm(100, 100, 50) == pytest.approx(math.pi * 100)
    # R = 0 is the sharp polygon
    assert DC.rounded_loop_mm(142, 342, 0) == DC.sharp_loop_mm(142, 342)
    with pytest.raises(DC.CorrectionError):
        DC.rounded_loop_mm(100, 300, 51)                      # R above min(W, T) / 2 is not a closed loop


def test_rounded_loop_is_shorter_than_the_sharp_loop_for_every_positive_radius():
    W, T = 242.0, 542.0
    previous = DC.sharp_loop_mm(W, T)
    for i in range(1, 122):
        R = i * 1.0
        loop = DC.rounded_loop_mm(W, T, R)
        assert loop < DC.sharp_loop_mm(W, T)
        assert DC.sharp_loop_mm(W, T) - loop == pytest.approx(DEFICIT * R)
        assert loop < previous                                # strictly decreasing in R
        previous = loop
    assert DEFICIT == pytest.approx(1.716814, abs=1e-6) and DEFICIT > 0


def test_unknown_bend_radius_gives_no_loop_and_no_lower_bound():
    with pytest.raises(DC.CorrectionError):
        DC.corner_deficit_mm(None)
    with pytest.raises(DC.CorrectionError):
        DC.rounded_loop_mm(142, 342, None)
    with pytest.raises(DC.CorrectionError):
        DC.corner_lengths_mm(-1)
    assert DC.classify_link_path(envelope_exact=True) == DC.MODELLED_POLYGONAL_EQUIVALENT
    assert DC.classify_link_path(envelope_exact=True, hook_length_known=True,
                                 closure_known=True) == DC.MODELLED_POLYGONAL_EQUIVALENT


def test_unknown_hook_length_never_promotes_the_sharp_path():
    for hook in (False, True):
        for closure in (False, True):
            assert DC.classify_link_path(hook_length_known=hook, closure_known=closure) == \
                DC.MODELLED_POLYGONAL_EQUIVALENT                 # no R, no exact envelope
    # with a bounded R and an exact envelope the bound is the rounded loop at R_max, with hooks taken as zero
    assert DC.classify_link_path(bend_radius_max_mm=40, envelope_exact=True) == DC.PROVEN_LOWER_BOUND
    assert DC.classify_link_path(bend_radius_mm=40, envelope_exact=True,
                                 hook_length_known=False) == DC.PROVEN_LOWER_BOUND
    assert DC.rounded_loop_mm(142, 342, 40) < DC.sharp_loop_mm(142, 342)


def test_lower_bound_needs_an_exact_envelope_and_a_source_derived_length_needs_everything():
    assert DC.classify_link_path(bend_radius_mm=40) == DC.MODELLED_POLYGONAL_EQUIVALENT
    assert DC.classify_link_path(bend_radius_max_mm=40, hook_length_known=True,
                                 closure_known=True) == DC.MODELLED_POLYGONAL_EQUIVALENT
    assert DC.classify_link_path(bend_radius_mm=40, hook_length_known=True, closure_known=True,
                                 envelope_exact=True) == DC.SOURCE_DERIVED_CUT_LENGTH
    assert DC.classify_link_path(bend_radius_mm=40, hook_length_known=True, closure_known=False,
                                 envelope_exact=True) == DC.PROVEN_LOWER_BOUND


def test_known_topology_with_unknown_cut_length():
    # topology is a count of closed links and legs: it needs no bend radius, hook or closure
    for n, legs in ((1, 2), (2, 4), (3, 6)):
        assert LG.topology_from_closed_links(n)["legs"] == legs
    assert DC.classify_link_path() == DC.MODELLED_POLYGONAL_EQUIVALENT


def test_known_count_with_unknown_mass():
    # the count is ceil(rate x clear run): no length of the bar itself enters it (6.67 / m over 3.0 m -> 20)
    n = LG.count_lower_bound(20 / 3.0, 3.0)
    assert n == 20
    rec = _corr(original_kg=n * 0.968 * 64 / 162.0, correction_kg=-(n * 0.968 * 64 / 162.0), COUNT=n,
                COUNT_KEPT="YES")
    assert rec["RETAINED_KG"] == 0.0 and rec["COUNT"] == 20 and rec["NEW_RELEASE_STATE"] == DC.BLOCKED_UNQUANTIFIED


# ------------------------------------------------------------------ errata records
def test_correction_record_carries_every_brief_field():
    r = _corr()
    assert set(DC.FIELDS) <= set(r)
    assert r["RECORD_TYPE"] == DC.RECORD_TYPE == "CORRECTION_ERRATA"
    assert r["CORRECTION_KG"] == -10.0 and r["RETAINED_KG"] == 0.0
    assert DC.policy_record()["fields"] == list(DC.FIELDS)


def test_correction_may_be_negative_but_never_adds_steel():
    neg = _corr(correction_kg=-3.5, new_authority_state=DC.PROVEN_LOWER_BOUND, new_release_state=DC.LOWER_BOUND)
    assert neg["CORRECTION_KG"] == -3.5 and neg["RETAINED_KG"] == pytest.approx(6.5)
    with pytest.raises(DC.CorrectionError):
        _corr(correction_kg=+0.5)
    with pytest.raises(DC.CorrectionError):
        _corr(original_kg=10.0, correction_kg=-10.5)          # cannot remove more than was released
    with pytest.raises(DC.CorrectionError):
        _corr(original_kg=-1.0, correction_kg=0.0)


def test_modelled_qa_and_rejected_states_keep_no_kg():
    for state in (DC.MODELLED_POLYGONAL_EQUIVALENT, DC.QA_ONLY, DC.REJECT_FOR_MASS):
        assert _corr(new_authority_state=state)["RETAINED_KG"] == 0.0
        with pytest.raises(DC.CorrectionError):
            _corr(new_authority_state=state, correction_kg=-4.0, new_release_state=DC.LOWER_BOUND)


def test_retained_steel_is_a_lower_bound_and_a_full_retraction_is_blocked():
    part = _corr(new_authority_state=DC.PROVEN_LOWER_BOUND, correction_kg=-2.0, new_release_state=DC.LOWER_BOUND)
    assert part["RETAINED_KG"] == pytest.approx(8.0)
    with pytest.raises(DC.CorrectionError):
        _corr(new_authority_state=DC.PROVEN_LOWER_BOUND, correction_kg=-2.0,
              new_release_state=DC.BLOCKED_UNQUANTIFIED)
    with pytest.raises(DC.CorrectionError):
        _corr(new_release_state=DC.LOWER_BOUND)                 # nothing retained -> BLOCKED_UNQUANTIFIED
    with pytest.raises(DC.CorrectionError):
        _corr(new_authority_state="VERIFIED")
    with pytest.raises(DC.CorrectionError):
        _corr(new_release_state="VERIFIED")


def test_correction_states_its_reason_and_evidence():
    with pytest.raises(DC.CorrectionError):
        _corr(correction_reason="  ")
    with pytest.raises(DC.CorrectionError):
        _corr(source_evidence="")


def test_correction_conservation():
    cs = [_corr(correction_id="C1", original_kg=10.0, correction_kg=-10.0),
          _corr(correction_id="C2", original_kg=4.0, correction_kg=-4.0),
          _corr(correction_id="C3", original_kg=6.0, correction_kg=-1.5, new_authority_state=DC.PROVEN_LOWER_BOUND,
                new_release_state=DC.LOWER_BOUND)]
    ok = DC.conservation(100.0, cs, 100.0 - 15.5)
    assert ok["all_pass"] and ok["correction_kg"] == pytest.approx(-15.5)
    assert not DC.conservation(100.0, cs, 100.0)["all_pass"]
    bad = dict(cs[0], RETAINED_KG=1.0)
    assert not DC.conservation(100.0, [bad] + cs[1:], 84.5)["checks"]["retained_plus_removed_is_original"]


def test_the_normal_delta_rule_is_unchanged():
    """An erratum is its own record type: delta_release still refuses every negative delta."""
    base = dict(delta_id="D1", change_kind=DR.NO_CHANGE, frozen_baseline="X (stamp)", baseline_component_id="O:C",
                old_state="LOWER_BOUND", old_known_quantity=10.0, new_project_source="", source_page="",
                source_handles="", graphic_evidence_class=GE.NO_GRAPHIC_EVIDENCE, new_component_model="",
                delta_known_quantity=-1.0, new_blocked_components=[], new_release_state=DR.LOWER_BOUND)
    with pytest.raises(DR.DeltaReleaseError):
        DR.record(**base)
    assert DC.RECORD_TYPE not in DR.CHANGE_KINDS
