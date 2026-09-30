"""R8.2 — K1 vs K2 reconciliation (§14-§16): identity first, tolerance declared, never a vote."""

from __future__ import annotations

import math

import pytest

from engine.source import digests as D
from engine.source import reconcile as R
from engine.source.cad import kernel as K1mod, kernel_ezdxf as K2, libredwg_map as L
from engine.source.cad.affine import Affine2
from engine.source.realised import Lineage, RealisedGeometry, RealisedSegment
from tests.r8_0 import scenes as S
from tests.r8_0.k1_harness import apply_test_schema_extensions

from .pairing import pair

ALL = {c[1]: c for c in S.CURVE_CASES + S.BASE_POINT_CASES + S.MINSERT_CASES}
CURVE = {c[1]: c for c in S.CURVE_CASES}


def both(scene):
    doc, dec = pair(scene)
    d1 = apply_test_schema_extensions(dec, L.to_document(dec))
    return K1mod.realise(d1), K2.realise(doc), d1, doc


def rec(a, b, **kw):
    lim = [(f.obs_id, f.instance_path) for f in b.findings if f.code == "KNOWN_LIBRARY_LIMITATION"]
    return R.reconcile(a, b, R.SYNTHETIC, known_limitations_b=lim, **kw)


@pytest.mark.parametrize("sid", sorted(set(ALL) - {"F06_MINSERT_MIRRORED_PARENT"}))
def test_k1_and_k2_agree_on_every_truth_scene(sid):
    a, b, d1, doc = both(ALL[sid][3])
    r = rec(a, b, insert_blocks_a=L.insert_blocks(d1), insert_blocks_b=K2.insert_blocks(doc))
    assert r["verdict"] == R.PASS, r["counts"]
    assert set(r["correlation_bases"]) == {"SOURCE_HANDLE"}


def test_nested_reflected_minsert_is_the_preregistered_limitation_not_a_k1_fault():
    a, b, _, _ = both(ALL["F06_MINSERT_MIRRORED_PARENT"][3])
    r = rec(a, b)
    assert r["verdict"] == R.KNOWN_LIMITATION and r["counts"] == {"PASS": 3, "KNOWN_LIBRARY_LIMITATION": 3}


def test_the_same_disagreement_without_the_registration_is_a_conflict():
    a, b, _, _ = both(ALL["F06_MINSERT_MIRRORED_PARENT"][3])
    assert R.reconcile(a, b, R.SYNTHETIC)["verdict"] == R.SOURCE_DECODE_CONFLICT


# ---------------------------------------------------------------- reconciliation catches a broken kernel

REFLECTING = [s for s, c in CURVE.items() if S.curve_case_truth(c)["orientation_sign"] < 0
              and not s.startswith("F03")]


@pytest.mark.parametrize("sid", REFLECTING)
def test_mt02_mirror_as_rotation_in_k1_is_a_source_decode_conflict(monkeypatch, sid):
    def mirror_as_rotation(sx, sy):
        m = Affine2.scale(abs(sx), abs(sy))
        return Affine2.rotation(math.pi) @ m if sx * sy < 0 else m
    monkeypatch.setattr(K1mod, "scale_matrix", mirror_as_rotation)
    a, b, _, _ = both(CURVE[sid][3])
    r = rec(a, b)
    assert r["verdict"] == R.SOURCE_DECODE_CONFLICT and r["scope"] == "SOURCE"


@pytest.mark.parametrize("sid", REFLECTING)
def test_mt49_orientation_bug_in_k1_is_an_orientation_block(monkeypatch, sid):
    monkeypatch.setattr(K1mod, "curve_orientation", lambda full, frame: 1 if frame.det() > 0 else -1)
    a, b, _, _ = both(CURVE[sid][3])
    r = rec(a, b)
    assert r["verdict"] == R.SOURCE_DECODE_CONFLICT
    assert r["non_pass_by_field"].get("ORIENTATION", 0) >= 1


@pytest.mark.parametrize("sid", ["F03_OCS_NEG_Z_INSERT", "F03_OCS_NEG_Z_ENTITIES"])
def test_mt03_dropped_ocs_in_k1_is_a_conflict(monkeypatch, sid):
    real = K1mod.frame_matrix

    def drop(ext):
        real(ext)
        return Affine2.identity()
    monkeypatch.setattr(K1mod, "frame_matrix", drop)
    a, b, _, _ = both(CURVE[sid][3])
    assert rec(a, b)["verdict"] == R.SOURCE_DECODE_CONFLICT


def test_a_broken_k2_is_caught_too(monkeypatch):
    """Symmetry: reconciliation has no favourite route."""
    monkeypatch.setattr(K2, "_plan", lambda ext: 1)                  # K2 ignores -Z frames
    a, b, _, _ = both(CURVE["F03_OCS_NEG_Z_ENTITIES"][3])
    assert rec(a, b)["verdict"] == R.SOURCE_DECODE_CONFLICT


# ---------------------------------------------------------------- presence, ambiguity, identity

def _seg(h, a, b, path=()):
    return RealisedSegment(a, b, Lineage(f"X:{h}", str(h), path, "0", "LINE"))


def _rg(segs):
    g = RealisedGeometry()
    g.segments.extend(segs)
    return g


def test_content_in_one_route_only_is_a_presence_block():
    r = R.reconcile(_rg([_seg(1, (0, 0), (1, 0)), _seg(2, (0, 1), (1, 1))]), _rg([_seg(1, (0, 0), (1, 0))]))
    assert r["verdict"] == R.BLOCK and r["field_class"] == "PRESENCE" and r["counts"][R.UNMATCHED_A] == 1


def test_no_nearest_neighbour_matching_across_objects():
    """Same geometry, different source identity: never matched."""
    r = R.reconcile(_rg([_seg(1, (0, 0), (1, 0))]), _rg([_seg(2, (0, 0), (1, 0))]))
    assert r["verdict"] == R.BLOCK and r["counts"] == {R.UNMATCHED_A: 1, R.UNMATCHED_B: 1}


def test_two_equally_good_candidates_in_one_object_are_ambiguous_not_guessed():
    a = _rg([_seg(1, (0, 0), (1, 0))])
    b = _rg([_seg(1, (0, 0), (1, 0)), _seg(1, (0, 0), (1, 0))])
    r = R.reconcile(a, b)
    assert r["counts"].get(R.AMBIGUOUS) == 1 and r["verdict"] == R.BLOCK


def test_reversed_segment_and_reversed_arc_are_the_same_physical_object():
    a = _rg([_seg(1, (0, 0), (1, 0))])
    b = _rg([_seg(1, (1, 0), (0, 0))])
    assert R.reconcile(a, b)["verdict"] == R.PASS


def test_truncated_d1_handle_correlates_only_by_its_low_bits_and_says_so():
    a = _rg([_seg("10388+3B", (0, 0), (1, 0))])
    b = _rg([_seg(str(0x10000 + 10388), (0, 0), (1, 0))])
    r = R.reconcile(a, b)
    assert r["verdict"] == R.PASS and r["correlation_bases"] == {"TRUNCATED_HANDLE_LOW_BITS": 1}
    wrong = _rg([_seg(str(10388), (0, 0), (1, 0))])                 # low bits equal but <= 0xFFFF: not a match
    assert R.reconcile(a, wrong)["verdict"] == R.BLOCK


def test_visibility_disagreement_blocks():
    a, b = _rg([]), _rg([])
    a.hidden.append({"obs_id": "D1:5", "kind": "LINE", "instance_path": []})
    assert R.reconcile(a, b)["field_class"] == "VISIBILITY"


def test_block_lineage_is_by_record_handle_not_name():
    r = R.reconcile(_rg([]), _rg([]), insert_blocks_a={"7": "3"}, insert_blocks_b={"7": "4"})
    assert r["verdict"] == R.BLOCK and r["field_class"] == "BLOCK_LINEAGE"


# ---------------------------------------------------------------- tolerance

def test_synthetic_and_real_tolerances_are_separate_and_declared():
    assert R.SYNTHETIC.position_pass == 1e-9 and R.SYNTHETIC.position_warn == 1e-6
    t = R.real_tolerance(1e6)
    assert t.name == "REAL" and abs(t.position_pass - 1024 * 2.0 ** -52 * 1e6) < 1e-18
    assert t.position_warn >= 10 * t.position_pass


def test_real_tolerance_honours_a_route_with_fewer_printed_digits():
    assert R.real_tolerance(1e6, decimal_digits=12).position_pass == pytest.approx(2e-5)


def test_sub_tolerance_noise_passes_and_significant_difference_conflicts():
    a = _rg([_seg(1, (0, 0), (1000, 0))])
    assert R.reconcile(a, _rg([_seg(1, (0, 0), (1000 + 5e-10, 0))]))["verdict"] == R.PASS
    assert R.reconcile(a, _rg([_seg(1, (0, 0), (1000 + 5e-7, 0))]))["verdict"] == R.WARN
    assert R.reconcile(a, _rg([_seg(1, (0, 0), (1001, 0))]))["verdict"] == R.SOURCE_DECODE_CONFLICT


def test_a_digest_difference_is_not_a_geometry_conflict():
    """Different RGD (rounding boundary) yet reconciliation PASSES."""
    a = _rg([_seg(1, (0, 0), (1000.0000005 - 1e-10, 0))])
    b = _rg([_seg(1, (0, 0), (1000.0000005 + 1e-10, 0))])
    assert D.realised_geometry_digest(a, 1.0) != D.realised_geometry_digest(b, 1.0)
    assert R.reconcile(a, b)["verdict"] == R.PASS


def test_the_same_digest_does_not_prove_completeness():
    """Two routes that both missed the same object digest identically; only the
    source census (conservation) reveals the missing row."""
    from engine.source.conservation import conservation
    from tests.r8_0 import libredwg_builder as B
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    doc = L.to_document(dec)
    rg = K1mod.realise(doc)
    same = D.realised_geometry_digest(rg, 1.0) == D.realised_geometry_digest(rg, 1.0)
    c = conservation(doc, rg, raw_entity_rows=doc.notes["raw_entity_rows"] + 1)
    assert same and c["source_level"]["BALANCED"] is False
