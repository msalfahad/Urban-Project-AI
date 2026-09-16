"""Round 6, steps 1-5: what a wall is, and what UNKNOWN is allowed to mean.

Round 5's P7757 run reported 3,272 wall bands and called 43 of 57 polygons
VOID_OR_SHAFT. Neither number was a threshold to tune. Both were the same
kind of mistake made twice — reading an absence as a claim:

    two parallel lines a wall-like distance apart are not therefore a wall
    a band paired on nothing may recover nothing
    nobody naming a space is not evidence that it is a void
    a repeated thickness ranks a contested pair and defines nothing
    and where no site line is drawn, there is no exterior to enumerate

The trade cases in the same fixture set are held here too — by asserting
that they CANNOT yet pass. Steps 6-12 are not written.
"""

from __future__ import annotations

import io
import re
import tokenize

import pytest

from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_profile as cp
from engine import cad_space_role as srole
from engine import freeze_manifest as fman
from engine import interior_exterior as iexr
from engine import partition_continuity as pcont
from engine import physical_wall as pwall
from engine import round6_fixtures as fx
from engine import round6_selftest as r6
from engine import semantic_seed as seeds_mod
from engine import supervised_benchmark as sup


def _joined(module):
    """The module's source with string-literal line breaks closed up."""
    src = open(module.__file__, encoding="utf-8").read()
    return re.sub(r'"\s*\n\s*"', "", src)


def _code(module):
    """Source with docstrings, comments and string literals taken out.

    A module may DISCUSS P7757 or a millimetre figure in its prose. These
    tests are about what it computes, so they read the code only.
    """
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


def _measured(name):
    case = next(c for c in fx.cases() if c.name.startswith(name))
    nd = ad.normalize(case.decode, source_file=name, source_hash="FIXTURE")
    sem = seeds_mod.classify(nd.texts)
    return cm.measure(nd, cp.build(nd), semantic=sem)


# ------------------------------------------------- §16.2 the cases themselves

@pytest.mark.parametrize("case", fx.geometry_cases(),
                         ids=lambda c: c.name)
def test_every_round_6_geometry_case_holds(case):
    res = r6.check(case)
    assert res.passed, f"{case.name}: {res.failures} observed={res.observed}"


@pytest.mark.parametrize("case", fx.trade_cases(), ids=lambda c: c.name)
def test_the_trade_cases_cannot_pass_before_the_trade_layer_exists(case):
    """Step 2 wrote these to fail. Nothing in steps 3-5 may satisfy them."""
    res = r6.check(case)
    assert not res.passed
    assert res.failures == [r6.NOT_YET]
    assert res.pending, "a trade case must say what it is waiting for"


def test_the_round_6_geometry_requirements_are_frozen():
    """The CASES are the score. The hash is a replay, and it may move."""
    rep = r6.assert_geometry_frozen()
    assert rep["geometry_cases"] == 15
    assert rep["geometry_passed"] == 15
    assert rep["trade_cases_awaiting_implementation"] == 3

    fr = next(f for f in fman.ROUNDS if f.round_name.startswith("ROUND_6"))
    assert fr.synthetic_artifact_hash["ROUND_6_SYNTHETIC_HASH"] == \
        "ac4752e4fc44ce02932586a3"
    rec = fman.replay(fr)
    if rep["ROUND_6_SYNTHETIC_HASH"] != "ac4752e4fc44ce02932586a3":
        assert "ROUND_6_SYNTHETIC_HASH" in rec["predicted"]


# ------------------------------------------- addendum §1 one line, one wall

def test_a_line_may_not_face_two_walls_over_the_same_stretch():
    rep = _measured("O_ONE_LINE_OFFERED_THREE_PARTNERS")
    assert not r6._overlapping_shared_lines(rep)


def test_a_refused_pair_is_counted_and_named_rather_than_silently_dropped():
    rep = _measured("O_ONE_LINE_OFFERED_THREE_PARTNERS")
    assert sum(wr.pairs_offered for wr in rep.walls) >= \
        sum(len(wr.walls) for wr in rep.walls)
    assert any(wr.pairs_refused_for_overlap for wr in rep.walls)


def test_evidence_is_ordered_and_never_summed():
    """PRIORITY is a lexicographic ranking, so no two tokens add up to one."""
    assert pwall.PRIORITY[0] == pwall.EV_HOSTS_AN_OPENING
    assert pwall.EV_OVERLAP not in pwall.PRIORITY
    assert pwall.PRIORITY.index(pwall.EV_THICKNESS_MODE) > \
        pwall.PRIORITY.index(pwall.EV_MUTUAL_NEAREST)


def test_a_repeated_thickness_ranks_a_pair_and_defines_no_wall():
    """No millimetre figure is declared to be, or not to be, a wall."""
    src = _code(pwall)
    for forbidden in ("== 50", "!= 50", "== 100", "thickness_mm == ",
                      "thickness_mm in ("):
        assert forbidden not in src, f"physical_wall judges a figure: {forbidden}"
    assert pwall.MODE_MIN_SUPPORT >= 2
    assert pwall.frozen_parameters()["why"]["thickness_never_defines"]


def test_a_detail_line_beside_a_face_does_not_become_a_second_wall():
    rep = _measured("N_A_DETAIL_LINE_BESIDE_A_WALL_FACE")
    assert not r6._overlapping_shared_lines(rep)


# --------------------------------------- step 4 what a weak band may recover

def test_a_band_paired_on_nothing_but_proximity_recovers_nothing():
    assert not r6._unsupported_recovering_bands(
        _measured("O_ONE_LINE_OFFERED_THREE_PARTNERS"))
    assert "has_pairing_evidence" in _joined(pcont)
    assert "Z_THE_BAND_ITSELF_IS_PAIRED_ON_NOTHING_BUT_PROXIMITY" in \
        _joined(pcont)


def test_a_recovered_span_still_carries_two_separate_authorities():
    rep = _measured("A_KITCHEN_WITH_AN_ENTRANCE_RECESS")
    for cont in rep.continuity:
        for span in cont.spans:
            assert span.topology_authority
            assert span.material_authority


# ------------------------------------------------ step 3 UNKNOWN is not VOID

def test_a_void_needs_positive_evidence_and_both_halves_of_it():
    assert srole.UNNAMED_PENETRATION_NEEDS == (
        srole.EV_NO_OPENING, srole.EV_REPEATED_ACROSS_PLANS)
    assert len(srole.UNNAMED_PENETRATION_NEEDS) == 2


def test_an_unnamed_room_with_a_door_is_unclassified_rather_than_void():
    rep = _measured("G_AN_INTERIOR_ROOM_NOBODY_NAMED")
    roles = [v.role for v in rep.space_roles.verdicts]
    assert srole.VOID_OR_SHAFT not in roles
    assert srole.INTERIOR_SPACE_UNCLASSIFIED in roles


def test_a_penetration_with_evidence_is_still_called_one():
    rep = _measured("H_A_SHAFT_WITH_EVIDENCE")
    assert any(v.role in srole.PENETRATION_ROLES
               for v in rep.space_roles.verdicts)


def test_no_space_role_is_decided_by_area():
    src = _code(srole)
    assert "area" not in src, "a space role is being decided by size"
    assert srole.frozen_parameters()["why"]["no_area_rule"]


def test_unreadable_identity_does_not_destroy_valid_geometry():
    rep = _measured("M_VALID_GEOMETRY_UNREADABLE_IDENTITY")
    assert rep.rows
    assert all(v.role != srole.VOID_OR_SHAFT
               for v in rep.space_roles.verdicts)


# ------------------------------------ step 3 interior, exterior and the site

def test_the_exterior_is_the_site_minus_the_fabric():
    rep = _measured("F_AN_EXTERIOR_STRIP_INSIDE_THE_SITE")
    assert any(v.role in srole.EXTERIOR_ROLES
               for v in rep.space_roles.verdicts)


def test_with_no_site_line_there_is_no_exterior_to_enumerate():
    """P7757 draws no site boundary. Zero is the honest answer, not a guess."""
    rep = _measured("G_AN_INTERIOR_ROOM_NOBODY_NAMED")
    for model in rep.space_roles.envelopes.values():
        if model.site is None:
            assert not model.exterior_faces
    assert all(v.role not in srole.EXTERIOR_ROLES
               for v in rep.space_roles.verdicts)


def test_an_envelope_that_holds_no_room_is_not_an_envelope():
    assert iexr.EV_NO_ENVELOPE in iexr.EVIDENCE
    assert "room_points" in _code(iexr), \
        "an envelope is validated against the rooms it should contain"


# --------------------------------------- §16.1 the manifest, and §0 semantics

def test_round_5_is_in_the_manifest_and_is_immutable():
    fr = next(f for f in fman.ROUNDS if f.round_name.startswith("ROUND_5"))
    assert fr.project_output_hash["PROJECT_2_CAD_ROUND5_HASH"] == \
        "8a90def3ac70301a1398aed5"
    assert fr.synthetic_artifact_hash["ROUND_5_SYNTHETIC_HASH"] == \
        "852363123a94453174791e42"
    assert fr.record()["immutable"]


def test_no_historical_artifact_was_rewritten_by_round_6():
    fman.assert_no_artifact_was_rewritten()


def test_every_replay_divergence_round_6_causes_was_predicted():
    for fr in fman.ROUNDS:
        rec = fman.replay(fr)
        assert not rec["UNPREDICTED_DIVERGENCE"], rec["round"]
        for name in rec["diverged"]:
            assert name in rec["predicted"], f"{rec['round']}: {name}"


# ------------------------------------------- §17 the supervised benchmark is

def test_the_supervised_benchmark_scores_assertions_not_figures():
    for ex in sup.EXAMPLES:
        assert ex.assertion
        assert ex.disclosed
        assert ex.protected_by, f"{ex.example_id} protects nothing"
    assert set(sup.SCOREBOARDS) == {
        "GEOMETRY", "SPACE_ROLE", "TRADE_ZONE", "QUANTITY"}


def test_the_disclosed_figures_are_never_read_by_the_engine():
    for module in (pwall, pcont, srole, iexr):
        src = open(module.__file__, encoding="utf-8").read()
        for figure in ("9.675", "9.55", "3.375", "3.15", "5.616", "3.85"):
            assert figure not in src, f"{module.__name__} reads {figure}"
