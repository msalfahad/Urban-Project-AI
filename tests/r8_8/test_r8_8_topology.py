"""R8.8 §16-§23: the frozen tolerance policy, the stability certificate, labels and site identity."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace

from engine.source import canonical_build as CB, canonical_input as CI, room_topology as RT
from engine.source import topology as T, topology_policy as TP
from tests.r8_8 import helpers as H

def run(parts, texts=(), **kw):
    return RT.run(H.inp(parts, texts=texts, **kw), frame_insert=None)


def summary(r):
    return sorted((s["site_id"], round(s["area"], 6), tuple(s["labels"]), tuple(s["issues"])) for s in r["sites"])


LABELS = [H.text(5, "BED.ROOM", 250, 200), H.text(6, "BATH", 750, 200)]


def test_policy_is_frozen_and_has_no_axis_predicate():
    rec = TP.record()
    assert rec["digest"] == json.load(open("tests/r8_8/registers/TOPOLOGY_TOLERANCE_POLICY.json"))["digest"]
    for p in ("is_horizontal", "is_vertical", "axis_alignment"):
        assert rec["predicates"][p].startswith("NOT USED")
    t = TP.tolerances(1.1e5, 10.0)
    assert t["valid"] and abs(t["eps_r"] - 0.1) < 1e-15 and t["eps_n"] == 1.1e5 * 2 ** -30
    assert TP.tolerances(1.1e5, None)["valid"] is False                     # no unit claim -> nothing certified
    import inspect
    src = inspect.getsource(T) + inspect.getsource(TP)
    assert "is_horizontal(" not in src and "is_vertical(" not in src


def test_noise_below_eps_n_changes_nothing_H584_class():
    base = run(H.two_rooms(), LABELS)
    noisy = H.two_rooms()
    # the H584 defect class: one wall line off horizontal by 4.4e-11 (relative 4e-16)
    noisy[0] = H.seg(100, 0, 0, 1000, 4.4e-11)
    noisy[4] = H.seg(104, 500, 4.4e-11 / 2, 500 + 1e-11, 400)
    r = run(noisy, LABELS)
    assert [s[0] for s in summary(r)] == [s[0] for s in summary(base)]
    assert all(abs(a[1] - b[1]) < 1e-6 for a, b in zip(summary(r), summary(base)))
    assert all(s["status"] == T.CERTIFIED for s in r["sites"])


def test_a_decision_inside_the_ambiguous_band_is_review_not_a_silent_room():
    # the partition stops 0.5 mm short of the outer wall: eps_n says "open", eps_r says "closed"
    parts = H.two_rooms()
    parts[4] = H.seg(104, 500, 0, 500, 400 - 0.05)
    r = run(parts, LABELS)
    assert all(T.TOLERANCE_SENSITIVE in s["issues"] for s in r["sites"])
    assert all(s["status"] == T.REVIEW_REQUIRED for s in r["sites"])


def test_a_perturbation_above_tolerance_genuinely_changes_topology():
    parts = H.two_rooms()
    parts[4] = H.seg(104, 500, 0, 500, 400 - 0.5)                           # 5 mm gap: a real opening
    r = run(parts, LABELS)
    assert len(r["sites"]) == 1 and T.TOLERANCE_SENSITIVE not in r["sites"][0]["issues"]
    assert r["sites"][0]["issues"] == [T.MULTIPLE_SEMANTIC_LABELS]          # merged: explicit, not silent


def test_multiple_conflicting_labels_need_review_and_no_rule_picks_one():
    i = H.box(1, 0, 0, 500, 400)
    for vals in (("BED.ROOM", "BATH"), ("BATH", "BED.ROOM"), ("A", "A")):
        r = run(i, [H.text(5, vals[0], 100, 100), H.text(6, vals[1], 300, 300)])
        s = r["sites"][0]
        assert s["issues"] == [T.MULTIPLE_SEMANTIC_LABELS] and s["status"] == T.REVIEW_REQUIRED
        assert sorted(s["labels"]) == ["E5", "E6"]
    one_stamp = [H.text(5, "BATH", 100, 100, path=("9",)), H.text(6, "plHL", 140, 120, path=("9",))]
    assert run(i, one_stamp)["sites"][0]["status"] == T.CERTIFIED          # two texts of ONE label occurrence


def test_label_on_boundary_is_an_ambiguity_finding():
    r = run(H.two_rooms(), [H.text(5, "BED.ROOM", 500.0, 200.0)])
    assert any(f["code"] == T.LABEL_ON_BOUNDARY for f in r["findings"])
    assert any(T.LABEL_ON_BOUNDARY in s["issues"] for s in r["sites"])


def test_cross_revision_topology_input_is_blocked():
    mixed = H.two_rooms() + [H.seg(900, 10, 10, 20, 20, rid="REV_B")]
    r = RT.run(H.inp(mixed), frame_insert=None)
    assert r["state"] == CI.SOURCE_REVISION_MISMATCH and r["sites"] is None


def test_wrong_plan_variant_is_refused_and_variant_geometry_is_excluded_by_occurrence():
    r = RT.run(H.inp(H.two_rooms(), region_id="R3"), frame_insert=None, selected_region_id="R1")
    assert r["state"] == CI.REGION_NOT_SELECTED
    v4 = H.box(1, 0, 0, 500, 400) + H.box(500, -100, -100, 600, 500, layer="FRAME", path=("156",))
    v3 = H.box(20, 2000, 0, 2500, 400) + H.box(600, 1900, -100, 2600, 500, layer="FRAME", path=("4713",))
    straddle = H.box(40, 550, 100, 1950, 200, layer="WALL", path=("777",))    # a variant-3 occurrence reaching over
    parts = v4 + v3 + straddle
    clip = CB.occurrence_extent(parts, "156")
    i = CB.assemble(H.rev(), "R1", clip, "F", 10.0, "U", parts, [], [])
    kept_occ = {CB.occurrence(p) for p in i.parts}
    assert kept_occ.isdisjoint({"I4713", "I777"}) and not any(p.identity.source_handle in ("20", "21", "22", "23")
                                                               for p in i.parts)
    assert any("777" in k or "parts:" in k for k in i.region_review)           # straddler: held, never cut
    assert RT.run(i, frame_insert="156")["state"] == CI.METHOD_INPUT_INCOMPLETE


def test_site_identity_is_source_based_and_order_free():
    a = run(H.two_rooms(), LABELS)
    b = run(list(reversed(H.two_rooms())), list(reversed(LABELS)))
    assert summary(a) == summary(b)
    # the same geometry under different source handles is a different site; the same handles moved keep the id
    moved = [replace(p, geometry=tuple(v + (7.0 if k % 2 == 0 else 3.0) for k, v in enumerate(p.geometry)))
             for p in H.two_rooms()]
    assert [s[0] for s in summary(run(moved, []))] == [s[0] for s in summary(a)]
    other = H.two_rooms(h0=300)
    assert set(s[0] for s in summary(run(other, []))).isdisjoint(s[0] for s in summary(a))
    # a different revision is a different site
    rc = [replace(p, identity=replace(p.identity, revision_id="REV_C")) for p in H.two_rooms()]
    c = RT.run(H.inp(rc, revision=H.rev("REV_C")), frame_insert=None)
    assert c["sites"] and set(s["site_id"] for s in c["sites"]).isdisjoint(s["site_id"] for s in a["sites"])


def test_arcs_holes_and_slivers_are_exact():
    room = H.box(1, 0, 0, 500, 400)
    col = H.box(20, 200, 150, 230, 180, layer="COL")
    bay = [H.part(30, "ARC", (250.0, 400.0, 100.0, 0.0, math.pi))]
    r = run(room + col + bay, [H.text(5, "R", 50, 50), H.text(6, "BAY", 250, 450)])
    areas = sorted(round(s["area"], 6) for s in r["sites"])
    assert areas == sorted([round(500 * 400 - 900, 6), 900.0, round(math.pi * 100 ** 2 / 2, 6)])


def test_same_fixtures_give_the_same_first_run():
    def digest(r):
        return hashlib.sha256(json.dumps([T.public(s) for s in r["sites"]], sort_keys=True, default=str)
                              .encode()).hexdigest()
    parts = H.two_rooms(gap=(100, 180)) + H.box(20, 100, 100, 200, 150, layer="FURN", path=("7",))
    assert digest(run(parts, LABELS)) == digest(run(parts, LABELS))


def test_post_freeze_fix_near_collinear_overlap_never_creates_a_noise_crossing():
    """F-R88-08 (found by the old-revision K1/K2 run): two overlapping wall lines, one tilted by 4e-12, must not
    produce a 'crossing' from a near-zero determinant; the topology is that of the exact overlap."""
    exact = H.two_rooms() + [H.seg(900, 100, 400, 900, 400)]
    tilted = H.two_rooms() + [H.seg(900, 100, 400, 900, 400 + 4e-12)]
    assert summary(run(exact, LABELS)) == summary(run(tilted, LABELS))


def test_post_freeze_fix_a_probe_meeting_a_site_at_one_point_does_not_touch_it():
    """F-R88-09: an unknown line starting exactly at a room's corner and running into the neighbour touches the
    neighbour only; a 1e-12 change of its start point must not change which sites it blocks."""
    from engine.source import geometry_role as GR
    for dy in (0.0, 1e-12, -1e-12):
        r = run(H.two_rooms() + [H.seg(800, 500, 400 + dy, 700, 300, layer="UNKNOWN_LAYER")], LABELS)
        blocked = sorted(tuple(s["labels"]) for s in r["sites"] if GR.UNKNOWN_PHYSICAL in s["contents"])
        assert blocked == [("E6",)]
