"""R8.14 §21-§23: WALL_BAND_POLICY_V5 - the elongation tie against the declared tolerance (V4-O2) and band geometry
vs band physical authority (V4-O1). Synthetic only: written and frozen BEFORE the V5 Qortuba run."""

from __future__ import annotations

import random

from engine.source import geometry_role as GR, room_topology as RT, topology as T, topology_closures as TC
from engine.source import wall_bands as WB
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import D2_TEXT, box, d2_replica, handles, ids, rect, wall

POL = TC.POLICY_ID
LAB = [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)]


def run(parts, texts=LAB):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=POL)


def est(r):
    return [b for b in r["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]


def window(w):
    """Two long faces (H10, H11) 100 apart, locally mutual nearest only over a window of length w between two
    intervening faces (H12, H13)."""
    return box() + [H.seg(10, 0, 300, 700, 300), H.seg(11, 0, 400, 700, 400), H.seg(12, 0, 320, 380, 320),
                    H.seg(13, 380 + w, 320, 700, 320), H.seg(14, 700, 300, 700, 400)]


def pair_state(r):
    b = [x for x in r["wall_bands"]["bands"] if handles(x) == ["H10", "H11"]]
    u = [x for x in r["wall_bands"]["unsupported_runs"] if x["separation"] == 100]
    return b, u


# ------------------------------------------------------------------------------- V4-O2: the tie
def test_square_run_equal_to_its_separation_is_not_elongated_and_says_why():
    b, (u,) = pair_state(run(window(100)))
    assert b == [] and u["reason"] == WB.BOUNDARY_CASE


def test_a_run_within_tolerance_either_side_of_equality_is_the_same_boundary_case():
    eps = 0.1                                                                   # eps_r of the synthetic input (1 mm)
    for w in (100 - eps / 2, 100 + eps / 2, 100 + 1e-9, 100 - 1e-9):
        b, (u,) = pair_state(run(window(w)))
        assert b == [] and u["reason"] == WB.BOUNDARY_CASE, w


def test_a_run_longer_by_a_clear_margin_is_a_band_and_a_shorter_one_is_not_elongated():
    b, u = pair_state(run(window(101)))
    assert b and b[0]["evidence"]["structural_support"]["state"] == WB.SELF_SUPPORTED and u == []
    b, (u,) = pair_state(run(window(60)))
    assert b == [] and u["reason"] == "NOT_ELONGATED_LOCAL_RUN"


def test_float_noise_cannot_flip_the_decision():
    outs = {pair_state(run(window(w)))[1][0]["reason"] for w in (100.0, 100.00000000001, 99.99999999999)}
    assert outs == {WB.BOUNDARY_CASE}


def test_legitimate_long_bands_are_untouched():
    r = run(box() + wall(), [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)])
    (b,) = est(r)
    assert b["evidence"]["physical_authority"]["state"] == WB.PHYSICAL
    (c,) = [c for c in r["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]
    assert c["geometry"] == (600, 400, 600, 420)


# ------------------------------------------------------------------------------- V4-O1: geometry vs authority
def nested(x0=300, y0=300, x1=510, y1=340, inset=10, layer="WALL"):
    """Two model-space closed polylines, the inner one inset on every side (the V4-O1 shape)."""
    return rect(50, x0, y0, x1, y1, layer=layer), rect(60, x0 + inset, y0 + inset, x1 - inset, y1 - inset, layer=layer)


def test_an_isolated_nested_rectangle_is_a_geometric_candidate_never_physical_authority():
    outer, inner = nested()
    r = run(box() + outer + inner)
    ring = [b for b in r["wall_bands"]["bands"] if set(handles(b)) <= {"H50", "H60"}]
    assert ring and all(b["state"] == WB.GEOMETRIC_CANDIDATE for b in ring)
    assert all(b["evidence"]["physical_authority"]["why"] == WB.ISOLATED_CLOSED_LOOP and b["ends"] == [] for b in ring)
    assert not ({f for b in ring for f in b["faces"]} & set(r["wall_bands"].get("face_ids_in_bands", [])))
    assert not [c for c in r["topology_closures"]["closures"] if c["band_id"] in {b["band_id"] for b in ring}]
    assert not [p for p in r["passages"] if p["band_id"] in {b["band_id"] for b in ring}]
    assert {x["entity"].split("|")[1] for x in r["wall_bands"]["isolated_loops"]} == {"H50", "H60"}


def test_a_loop_connected_to_the_wall_network_is_not_isolated_and_isolation_fails_closed():
    """Connectivity is structural evidence for the OUTER loop; the nested inner loop still touches nothing, so a band
    with a face on it stays a candidate (fail closed) until positive authority exists."""
    outer, inner = nested()
    tie = [H.seg(70, 0, 320, 300, 320), H.seg(71, 510, 320, 1000, 320)]      # walls running into the outer loop
    r = run(box() + outer + inner + tie, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)])
    iso = {x["entity"].split("|")[1] for x in r["wall_bands"]["isolated_loops"]}
    assert "H50" not in iso and "H60" in iso
    ring = [b for b in r["wall_bands"]["bands"] if set(handles(b)) == {"H50", "H60"}]
    assert ring and all(b["state"] == WB.GEOMETRIC_CANDIDATE for b in ring)


def test_the_same_geometry_inside_a_detail_block_occurrence_never_becomes_physical_authority():
    blk = [H.part(50, "SEGMENT", s.geometry, layer="WALL", idx=s.identity.part_index, path=("900",))
           for s in rect(50, 300, 300, 510, 340)] + \
          [H.part(60, "SEGMENT", s.geometry, layer="WALL", idx=s.identity.part_index, path=("900",))
           for s in rect(60, 310, 310, 500, 330)]
    r = run(box() + blk)
    assert not [b for b in est(r) if set(handles(b)) <= {"H50", "H60"}]


def test_a_shaft_like_obstacle_with_positive_authority_is_physical():
    outer, inner = nested()
    items = [T.BoundaryItem(p.identity.key, "SEGMENT", tuple(p.geometry), GR.TOPOLOGY_BOUNDARY)
             for p in box() + outer + inner]
    kw = dict(eps_r=0.1, band_review=5.0, revision_id=H.REV, region_id=H.REGION, eps_n=1e-4)
    plain = WB.detect(items, **kw)
    proven = WB.detect(items, physical_authority={p.identity.key for p in outer + inner}, **kw)
    ring = lambda w: [b for b in w["bands"] if set(handles(vars(b))) <= {"H50", "H60"}]
    assert ring(plain) and all(b.state == WB.GEOMETRIC_CANDIDATE for b in ring(plain))
    assert ring(proven) and all(b.state == WB.ESTABLISHED for b in ring(proven))
    assert proven["physical_authority_entities"] and proven["isolated_loops"] == []


def test_furniture_and_window_frame_rectangles_make_no_band():
    for layer in ("FURNITURE", "GLAZING"):
        outer, inner = nested(layer=layer)
        r = run(box() + outer + inner)
        assert not [b for b in r["wall_bands"]["bands"] if set(handles(b)) & {"H50", "H60"}]


# ------------------------------------------------------------------------------- regressions
def test_h2430_class_h2431_class_and_h1316_class_regressions():
    col = [H.part(80, "SEGMENT", g, layer="COLUMN", idx=i) for i, g in
           enumerate([(100, 400, 200, 400), (200, 400, 200, 420), (200, 420, 100, 420), (100, 420, 100, 400)])]
    hl = [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)]
    r = run(box() + wall(lower=((0, 300), (300, 600))) + col, hl)
    (c,) = [c for c in r["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]
    assert c["geometry"] == (600, 400, 600, 420) and c["corroboration"][0]["grade"] == WB.CAP_PROVEN
    r = run(box() + wall(lower=((0, 300), (300, 600)), cap=0.92, cap_x=600.05), hl)
    (c,) = [c for c in r["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]
    assert c["corroboration"][0]["grade"] == WB.CAP_CANDIDATE and c["physical_material"] == "NONE"
    p = box() + [H.seg(20, 300, 0.14, 300, 19.86)] + \
        [H.seg(21 + k, 300, y, 500, y, layer="GLAZING") for k, y in enumerate((0.0, 7.0, 13.0, 20.0))]
    assert run(p, [H.text(5, "A", 500, 400)])["topology_closures"]["closures"] == []


def test_v3_d2_false_band_and_v4_chain_id_collision_regressions():
    r = run(d2_replica(), D2_TEXT)
    assert not [b for b in r["wall_bands"]["bands"] if handles(b) == ["H1", "H2"]]
    assert not [p for p in r["passages"] if p["width"] > 500]
    r = run(box() + rect(50, 300, 300, 700, 340))
    wb = r["wall_bands"]
    assert wb["chain_id_collisions"] == [] and len({c["chain_id"] for c in wb["chains"]}) == len(wb["chains"])


def test_everything_above_is_order_independent():
    outer, inner = nested()
    base = box() + wall() + outer + inner + [H.seg(77, 850, 150, 950, 150)]
    want = ids(run(base))
    st = sorted((b["band_id"], b["state"]) for b in run(base)["wall_bands"]["bands"])
    for seed in range(3):
        p = list(base)
        random.Random(seed).shuffle(p)
        r = run(p)
        assert ids(r) == want and sorted((b["band_id"], b["state"]) for b in r["wall_bands"]["bands"]) == st
    for w in (100.0, 101.0):
        p = window(w)
        random.Random(5).shuffle(p)
        assert pair_state(run(p))[1] == pair_state(run(window(w)))[1]


def test_v5_policy_record():
    rec = WB.policy_record()
    assert WB.POLICY_ID == "WALL_BAND_POLICY_V5" and rec["params"] == WB.PARAMS
    assert rec["band_authority"] == [WB.PHYSICAL, WB.GEOMETRIC_CANDIDATE]
    assert rec["unsupported_reasons"] == ["NOT_ELONGATED_LOCAL_RUN", WB.BOUNDARY_CASE]
    assert rec["history"][-1].startswith("V5 (R8.14)")
    assert "binary floating-point equality as an elongation decision" in rec["never"]
    assert TC.policy_record()["digest"] == "46742c570b4d8a036fd6b7446f28055bfd4e1adbff51966e800e5986ca99ccb2"
