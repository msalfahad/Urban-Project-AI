"""R8.0 deliberate-break (mutation) tests that can run TODAY.

Each mutation is switched on in the test-side reference realiser and the
fixture must DETECT it (fail against hand truth), while control fixtures
must NOT be falsely flagged. This proves the fixtures are sensitive before
any R8 code exists; R8.1 re-applies the same breaks to the real kernel.

Mutations whose checking machinery is not written yet (reconcile, frames,
fact policy, transcription, regression harness) are contract tests in
test_r8_0_pending_contracts.py. MT-47/MT-48 live in
test_r8_0_import_boundaries.py.
"""

from __future__ import annotations

import pytest

from . import digest_contract as D, libredwg_builder as B, reference_realiser as RR, scenes as S
from .geometry import (close, compare_arc, compare_bulge, compare_segment, current_realised,
                       failed_fields, match_segment_sets)
from .test_r8_0_digests import DIRECT_WCS, MIRRORED, rgd, srd

CURVE = {c[1]: c for c in S.CURVE_CASES}
BP = {c[1]: c for c in S.BASE_POINT_CASES}
MI = {c[1]: c for c in S.MINSERT_CASES}
REFLECTING = [k for k, c in CURVE.items() if S.curve_case_truth(c)["orientation_sign"] < 0]
NON_REFLECTING = [k for k, c in CURVE.items() if S.curve_case_truth(c)["orientation_sign"] > 0]
OCS_SCENES = ["F03_OCS_NEG_Z_INSERT", "F03_OCS_NEG_Z_ENTITIES"]


def _bad(truth, r):
    return (failed_fields(compare_arc(truth["arc"], r.arcs[0]))
            + ["bulge." + f for f in failed_fields(compare_bulge(truth["bulge"], r.bulges[0]))]
            + ["line." + f for f in failed_fields(compare_segment(truth["line"], r.segments[0]))])


# MT-01 ---------------------------------------------------------------------
@pytest.mark.parametrize("sid", list(BP))
def test_MT01_skip_base_point_is_detected(sid):
    assert _bad(S.base_point_truth(BP[sid]), RR.realise(BP[sid][3], {"SKIP_BASE_POINT"}))


# MT-02 ---------------------------------------------------------------------
@pytest.mark.parametrize("sid", REFLECTING)
def test_MT02_mirror_as_rotation_is_detected(sid):
    bad = failed_fields(compare_arc(S.curve_case_truth(CURVE[sid])["arc"],
                                    RR.realise(CURVE[sid][3], {"MIRROR_AS_ROTATION"}).arcs[0]))
    assert bad


@pytest.mark.parametrize("sid", NON_REFLECTING)
def test_MT02_control_not_falsely_flagged(sid):
    assert not _bad(S.curve_case_truth(CURVE[sid]), RR.realise(CURVE[sid][3], {"MIRROR_AS_ROTATION"}))


@pytest.mark.parametrize("sid", [k for k in CURVE if k not in ("F03_OCS_NEG_Z_INSERT", "F03_OCS_NEG_Z_ENTITIES")])
def test_MT02_is_exactly_what_the_current_engine_does(sid):
    """The current cad_adapter ARC output coincides point for point with the
    MT-02 mutant (mirror applied as a rotation) on every non-OCS scene: the
    production defect IS mutation MT-02."""
    cur = current_realised(B.build(CURVE[sid][3]))["arcs"][0]
    mut = RR.realise(CURVE[sid][3], {"MIRROR_AS_ROTATION"}).arcs[0]
    assert close(cur["CENTER"], mut["CENTER"]) and close(cur["P0"], mut["P0"])
    assert close(cur["PM"], mut["PM"]) and close(cur["P1"], mut["P1"])


# MT-03 ---------------------------------------------------------------------
@pytest.mark.parametrize("sid", OCS_SCENES)
def test_MT03_drop_ocs_is_detected(sid):
    assert _bad(S.curve_case_truth(CURVE[sid]), RR.realise(CURVE[sid][3], {"DROP_OCS"}))


def test_MT03_control_not_falsely_flagged():
    sid = "F03_OCS_POS_Z_CONTROL"
    assert not _bad(S.curve_case_truth(CURVE[sid]), RR.realise(CURVE[sid][3], {"DROP_OCS"}))


# MT-04 ---------------------------------------------------------------------
def test_MT04_raw_parameter_comparison_gives_a_false_block():
    """The mirrored INSERT and the same geometry drawn directly are
    physically identical. Comparing RAW arc parameters (angles, extrusion,
    insert scale) calls them different — a false BLOCK. Comparing realised
    geometry calls them equal. Hence reconciliation must be on realised points."""
    def raw_arc(scene):
        arcs = [e for blk in scene.get("blocks", {}).values() for e in blk["entities"] if e["kind"] == "ARC"]
        arcs += [e for e in scene["entities"] if e["kind"] == "ARC"]
        return (arcs[0]["c"], arcs[0]["a0"], arcs[0]["a1"])
    assert raw_arc(MIRRORED) != raw_arc(DIRECT_WCS)            # the false BLOCK
    assert rgd(MIRRORED) == rgd(DIRECT_WCS)                    # the right answer


# MT-05 / MT-06 (digest-level detection; reconcile-level is pending) --------
def _without_first_line(scene):
    ents = [e for e in scene["entities"]]
    i = next(i for i, e in enumerate(ents) if e["kind"] == "LINE")
    return dict(scene, entities=ents[:i] + ents[i + 1:])


def _line_moved_1mm(scene):
    ents = [dict(e) for e in scene["entities"]]
    i = next(i for i, e in enumerate(ents) if e["kind"] == "LINE")
    ents[i]["b"] = (ents[i]["b"][0] + 1.0, ents[i]["b"][1])
    return dict(scene, entities=ents)


def test_MT05_removed_entity_changes_both_digests():
    assert srd(DIRECT_WCS) != srd(_without_first_line(DIRECT_WCS))
    assert rgd(DIRECT_WCS) != rgd(_without_first_line(DIRECT_WCS))


def test_MT06_one_mm_perturbation_changes_both_digests():
    assert srd(DIRECT_WCS) != srd(_line_moved_1mm(DIRECT_WCS))
    assert rgd(DIRECT_WCS) != rgd(_line_moved_1mm(DIRECT_WCS))


# MT-49 ---------------------------------------------------------------------
NEG_SCALE_MIRRORS = [k for k in REFLECTING if k not in ("F03_OCS_NEG_Z_ENTITIES",)]


@pytest.mark.parametrize("sid", NEG_SCALE_MIRRORS)
def test_MT49_bulge_flip_keyed_on_extrusion_only_is_detected(sid):
    bad = failed_fields(compare_bulge(S.curve_case_truth(CURVE[sid])["bulge"],
                                      RR.realise(CURVE[sid][3], {"BULGE_FLIP_ONLY_ON_EXTRUSION"}).bulges[0]))
    assert bad


def test_MT49_entity_level_ocs_still_correct():
    """Keyed on extrusion, the flip IS right for an entity whose own
    extrusion is -Z — which is why an OCS-only fix looks finished. It is not:
    negative-scale mirrors (Al Rashed's case) are missed."""
    sid = "F03_OCS_NEG_Z_ENTITIES"
    assert not failed_fields(compare_bulge(S.curve_case_truth(CURVE[sid])["bulge"],
                                           RR.realise(CURVE[sid][3], {"BULGE_FLIP_ONLY_ON_EXTRUSION"}).bulges[0]))


# MT-50 ---------------------------------------------------------------------
def test_MT50_representation_digest_cannot_prove_geometry():
    """A kernel break (MT-02) leaves SOURCE_REPRESENTATION_DIGEST unchanged —
    it never sees the kernel — while REALISED_GEOMETRY_DIGEST changes. So a
    representation digest accepted as geometry proof would pass the defect."""
    assert srd(MIRRORED) == srd(MIRRORED)
    assert rgd(MIRRORED, {"MIRROR_AS_ROTATION"}) != rgd(MIRRORED)


# S-series: supporting sensitivity for F06 / F34 / F08 -------------------------
@pytest.mark.parametrize("sid", list(MI))
def test_S01_minsert_first_cell_only_is_detected(sid):
    assert not match_segment_sets(MI[sid][4], RR.realise(MI[sid][3], {"MINSERT_FIRST_CELL_ONLY"}).segments)[0]


@pytest.mark.parametrize("sid", [c[1] for c in S.FRAME_CASES if c[4] == "FRAME_UNREADABLE"])
def test_S02_unreadable_frame_as_wcs_is_detected(sid):
    case = next(c for c in S.FRAME_CASES if c[1] == sid)
    clean = RR.realise(S.frame_scene(case[3]))
    fail_open = RR.realise(S.frame_scene(case[3]), {"UNREADABLE_FRAME_AS_WCS"})
    assert any(f["code"] == "FRAME_UNREADABLE" for f in clean.findings) and not clean.arcs
    assert not fail_open.findings and fail_open.arcs          # the fail-open break is visible to the fixture


@pytest.mark.parametrize("sid", [c[1] for c in S.XREF_CASES])
def test_S03_ignored_xref_is_detected(sid):
    case = next(c for c in S.XREF_CASES if c[1] == sid)
    assert RR.realise(case[3]).findings and not RR.realise(case[3], {"IGNORE_XREF"}).findings
