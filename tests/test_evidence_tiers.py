"""§8, §9: orthogonality is not independence, and a doorway may release.

The Round 2 rule — two SOURCE_INDEPENDENCE classes for VALIDATED — meant
no doorway on a single architectural sheet could ever be validated. These
tests pin both halves of the correction: correlated repeats still count for
nothing, and differently authored channels on one drawing now count.
"""

import pytest

from engine import evidence_tiers as et


def _obs(oid, channel, source=et.SRC_SAME_DRAWING, relays="", what="x"):
    return et.Observation(oid, what, channel, source, relays)


# --- axis 2: orthogonality -----------------------------------------------

def test_one_observation_is_a_single_observation():
    got = et.assess([_obs("O1", et.CH_GEOMETRY)])
    assert got.tier == et.TIER_SINGLE


def test_two_observations_in_one_channel_are_a_correlated_repeat():
    """A wall measured twice off one polyline is one observation."""
    got = et.assess([_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_GEOMETRY)])
    assert got.tier == et.TIER_CORRELATED
    assert "repeated, not two agreeing" in got.why


def test_a_raster_render_relays_the_geometry_it_renders():
    """The Round 2 finding that was RIGHT and must survive the refactor.

    The render is discounted outright, so what remains is ONE observation
    — not two correlated ones. A render adds nothing at all.
    """
    got = et.assess([_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_RENDER, relays="O1")])
    assert got.tier == et.TIER_SINGLE
    assert got.discounted
    assert "render of geometry is that geometry" in got.discounted[0][1]
    assert len(got.observations) == 1


def test_a_render_with_no_original_still_contributes_only_geometry():
    got = et.assess([_obs("O1", et.CH_RENDER)])
    assert got.channels == (et.CH_GEOMETRY,)


def test_a_gap_and_a_swing_symbol_are_orthogonal_on_one_drawing():
    """§8's central example: the correction Round 3 asks for."""
    got = et.assess([_obs("O1", et.CH_GEOMETRY, what="opening gap"),
                     _obs("O2", et.CH_SYMBOL, what="door swing arc")])
    assert got.tier == et.TIER_DRAWING_ORTHOGONAL
    assert "could have disagreed" in got.why


def test_wall_geometry_plus_a_printed_dimension_is_orthogonal():
    got = et.assess([_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_ANNOTATION, what="printed 900")])
    assert got.tier == et.TIER_DRAWING_ORTHOGONAL


def test_a_schedule_row_lifts_the_tier_to_the_document_set():
    got = et.assess([
        _obs("O1", et.CH_GEOMETRY),
        _obs("O2", et.CH_STRUCTURE, source=et.SRC_SAME_DOCUMENT_SET,
             what="door schedule row")])
    assert got.tier == et.TIER_DOCUMENT_ORTHOGONAL


def test_an_independent_source_outranks_everything():
    got = et.assess([_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_GEOMETRY,
                          source=et.SRC_INDEPENDENT, what="site measure")])
    assert got.tier == et.TIER_INDEPENDENT


def test_the_record_keeps_the_two_axes_apart():
    rec = et.assess([_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_SYMBOL)]).record()
    axes = rec["the_two_axes"]
    assert "how far from this document" in axes["SOURCE_INDEPENDENCE"]
    assert "how differently it was authored" in axes[
        "EVIDENCE_ORTHOGONALITY"]
    assert "one observation wearing two hats" in axes["why_both"]


# --- §9 portal grades ----------------------------------------------------

def _door(width=900.0, obs=None, **kw):
    base = dict(geometry_exact=True, host_compatible=True,
                contradicted=False, opening_width_mm=width)
    base.update(kw)
    return et.grade_portal(
        "PT-1",
        obs if obs is not None else [_obs("O1", et.CH_GEOMETRY),
                                     _obs("O2", et.CH_SYMBOL)],
        **base)


def test_an_ordinary_doorway_read_off_a_plan_may_release():
    """§9: production takeoff may use a strong DRAWING_VALIDATED portal."""
    got = _door()
    assert got.grade == et.PORTAL_DRAWING_VALIDATED
    assert got.may_release
    assert "no site visit is required" in got.why


def test_geometry_alone_does_not_validate_a_portal():
    got = _door(obs=[_obs("O1", et.CH_GEOMETRY)])
    assert got.grade == et.PORTAL_UNVALIDATED
    assert not got.may_release


def test_a_schedule_makes_it_document_validated():
    got = _door(obs=[_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_STRUCTURE,
                          source=et.SRC_SAME_DOCUMENT_SET)])
    assert got.grade == et.PORTAL_DOCUMENT_VALIDATED
    assert got.may_release


def test_inexact_geometry_refuses_whatever_the_evidence_tier():
    got = _door(geometry_exact=False)
    assert got.grade == et.PORTAL_UNVALIDATED
    assert "does not come from source lines" in got.why


def test_an_incompatible_host_wall_refuses():
    got = _door(host_compatible=False)
    assert got.grade == et.PORTAL_UNVALIDATED
    assert "host wall" in got.why


def test_contradicted_evidence_refuses():
    got = _door(contradicted=True)
    assert got.grade == et.PORTAL_UNVALIDATED
    assert "contradicts it" in got.why


def test_a_wide_opening_is_held_for_human_qa():
    """§9: higher-risk openings may require stronger evidence."""
    got = _door(width=4000.0)
    assert got.grade == et.PORTAL_DRAWING_VALIDATED
    assert got.needs_human_qa
    assert not got.may_release
    assert "moves square metres" in got.why


def test_a_wide_opening_with_document_evidence_releases():
    got = _door(width=4000.0,
                obs=[_obs("O1", et.CH_GEOMETRY),
                     _obs("O2", et.CH_STRUCTURE,
                          source=et.SRC_SAME_DOCUMENT_SET)])
    assert got.grade == et.PORTAL_DOCUMENT_VALIDATED
    assert not got.needs_human_qa
    assert got.may_release


def test_the_grade_never_supplies_a_coordinate():
    rec = _door().record()
    assert "never where it is" in rec["geometric_standard_unchanged"]
    assert "drawn jamb" in rec["geometric_standard_unchanged"]


def test_the_summary_says_what_changed_and_what_did_not():
    got = et.summary([_door(), _door(width=4000.0),
                      _door(geometry_exact=False)])
    assert got["by_grade"][et.PORTAL_DRAWING_VALIDATED] == 2
    assert got["may_release"] == 1
    assert got["held_for_human_qa"] == 1
    assert "not how a professional takeoff works" in got[
        "what_changed_from_round_2"]
    assert "never lets a model's reading supply a millimetre" in got[
        "what_did_not_change"].replace("No tier lets", "never lets")
