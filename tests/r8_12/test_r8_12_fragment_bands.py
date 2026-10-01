"""R8.12 §11, §34, §37: fragment-aware wall bands (WALL_BAND_POLICY_V3) - face chains, local band spans, assemblies.
Synthetic only: written and frozen BEFORE any Qortuba run (anti-calibration, §1)."""

from __future__ import annotations

import ast
import math
import random
from pathlib import Path

from engine.source import geometry_role as GR, room_topology as RT, topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

POL = TC.POLICY_ID
LAB = [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)]


def box(w=1000, h=800):
    return [H.seg(1, 0, 0, w, 0), H.seg(2, w, 0, w, h), H.seg(3, w, h, 0, h), H.seg(4, 0, h, 0, 0)]


def wall(lower=((0, 600),), upper=((0, 600),), cap=0.0, y=(400, 420), cap_x=None, h0=10):
    """A double-line stub from the left room wall; each face drawn as the given fragments; right end capped on DIM
    (cap = shortfall at the lower face; None = no cap)."""
    p, h = [], h0
    for x0, x1 in lower:
        p.append(H.seg(h, x0, y[0], x1, y[0]))
        h += 1
    for x0, x1 in upper:
        p.append(H.seg(h, x0, y[1], x1, y[1]))
        h += 1
    end = max(x for _, x in lower)
    if cap is not None:
        p.append(H.seg(90, cap_x if cap_x is not None else end, y[0] + cap, cap_x if cap_x is not None else end, y[1],
                       layer="DIM"))
    return p


def run(parts, texts=LAB):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=POL)


def est(r):
    return [b for b in r["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]


def authorised(r):
    return [c for c in r["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]


def labelled_area(r):
    return sorted(round(s["area"], 6) for s in r["sites"] if s["labels"])


def chain_of(r, handle):
    return next((c for c in r["wall_bands"]["chains"] if any(f"|H{handle}|" in f["source"] for f in c["fragments"])),
                {"chain_id": f"NOT_A_FACE:{handle}", "nodes": [], "duplicate_intervals": []})


# ------------------------------------------------------------------------------- A: the H2430 class
def test_A_one_face_against_two_contiguous_fragments_is_one_band_with_exact_intervals():
    r = run(box() + wall(lower=((0, 300), (300, 600))))
    (b,) = est(r)
    assert [e["kind"] for e in b["ends"]][1] == WB.ALIGNED_FREE_END
    assert chain_of(r, 10)["chain_id"] == chain_of(r, 11)["chain_id"]          # the two fragments: one face chain
    (sp,) = [s for s in r["wall_bands"]["spans"] if s["band_id"] == b["band_id"]]
    srcs = {x["source"].split("|")[1]: x["parameter_interval"] for x in sp["source_intervals"]}
    assert srcs == {"H10": [0.0, 300.0], "H11": [0.0, 300.0], "H12": [0.0, 600.0]}


def test_A_fragmented_and_one_piece_faces_give_the_same_end_closure_and_areas():
    one, frag = run(box() + wall()), run(box() + wall(lower=((0, 300), (300, 600))))
    assert [e["kind"] for e in est(one)[0]["ends"]] == [e["kind"] for e in est(frag)[0]["ends"]]
    assert [c["geometry"] for c in authorised(one)] == [c["geometry"] for c in authorised(frag)] == \
        [(600, 400, 600, 420)]
    assert labelled_area(one) == labelled_area(frag)


def test_a_face_meeting_a_t_junction_still_spans_the_whole_wall():
    """The two lower fragments meet at a T-junction (a node, not a break): one chain, spans over the whole wall."""
    p = box() + [H.seg(10, 0, 400, 300, 400), H.seg(11, 300, 400, 600, 400), H.seg(12, 0, 420, 600, 420),
                 H.seg(13, 300, 400, 300, 0)]                                  # a single-line wall ends between them
    r = run(p, [H.text(5, "A", 150, 100), H.text(6, "C", 450, 100), H.text(7, "B", 500, 700)])
    bands = est(r)
    assert bands and all("H12" in "".join(b["faces"]) for b in bands)
    covered = sorted((round(s["s"][0]), round(s["s"][1])) for s in r["wall_bands"]["spans"])
    assert covered[0][0] == 0 and covered[-1][1] == 600


# ------------------------------------------------------------------------------- B, C, D: real gaps and openings
def test_B_a_5_mm_authored_gap_is_never_joined_and_invents_no_wall():
    r = run(box() + wall(lower=((0, 300), (300.5, 600))))                    # 0.5 native = 5 mm
    assert chain_of(r, 10)["chain_id"] != chain_of(r, 11)["chain_id"]
    for c in r["topology_closures"]["closures"]:
        assert not (299 < c["geometry"][0] < 302)                             # nothing closes the gap
    for b in est(r):
        if b["interval"][1] < 301:
            assert b["ends"][1]["kind"] == WB.JUNCTION                         # H12 continues: no free end at the gap


def test_B_the_50_mm_review_band_is_never_chain_continuity():
    r = run(box() + wall(lower=((0, 300), (304.9, 600))))                    # 49 mm
    assert chain_of(r, 10)["chain_id"] != chain_of(r, 11)["chain_id"]


def test_C_a_door_opening_between_same_axis_fragments_is_preserved():
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    r = run(walls + door, [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    assert chain_of(r, 5)["chain_id"] != chain_of(r, 8)["chain_id"]
    assert r["openings"]["I70"]["state"] == "CLOSED" and r["passages"] == []
    assert not [c for c in r["topology_closures"]["closures"] if 150 < c["geometry"][1] < 250]


def test_D_a_window_opening_between_same_axis_fragments_is_preserved():
    p = [H.seg(1, 0, 0, 400, 0), H.seg(2, 600, 0, 1000, 0), H.seg(3, 0, 20, 400, 20), H.seg(4, 600, 20, 1000, 20),
         H.seg(5, 400, 0, 400, 20), H.seg(6, 600, 0, 600, 20),
         H.seg(7, 400, 7, 600, 7, layer="GLAZING"), H.seg(8, 400, 13, 600, 13, layer="GLAZING"),
         H.seg(9, 1000, 0, 1000, 800), H.seg(11, 1000, 800, 0, 800), H.seg(12, 0, 800, 0, 0)]
    r = run(p, [H.text(5, "A", 500, 400)])
    assert chain_of(r, 3)["chain_id"] != chain_of(r, 4)["chain_id"]
    assert not [c for c in r["topology_closures"]["closures"] if 400 < c["geometry"][0] < 600]


def test_a_glazing_end_at_a_touching_joint_is_an_opening_break():
    p = box() + [H.seg(10, 0, 400, 300, 400), H.seg(11, 300, 400, 600, 400), H.seg(12, 0, 420, 600, 420),
                 H.seg(30, 300, 400, 300, 380, layer="GLAZING")]
    r = run(p)
    assert chain_of(r, 10)["chain_id"] != chain_of(r, 11)["chain_id"]
    assert any(b["kind"] == WB.OPENING_BREAK for b in r["wall_bands"]["chain_breaks"])
    # one long face (H12) pairs LOCALLY with two different opposite chains (H10, H11)
    bands = [b for b in r["wall_bands"]["bands"] if any("|H12|" in f for f in b["faces"])]
    assert {tuple(sorted(f.split("|")[1] for f in b["faces"])) for b in bands} == {("H10", "H12"), ("H11", "H12")}


# ------------------------------------------------------------------------------- E, F: junctions and columns
def test_E_a_t_junction_on_one_face_is_a_node_not_the_end_of_the_face():
    p = box() + wall(lower=((0, 300), (300, 600))) + [H.seg(40, 300, 400, 300, 0)]
    r = run(p, [H.text(5, "A", 150, 100), H.text(6, "C", 450, 100), H.text(7, "B", 500, 700)])
    ch = chain_of(r, 10)
    assert ch["chain_id"] == chain_of(r, 11)["chain_id"]
    assert any(n["kind"] == WB.BRANCH and abs(n["s"] - 300) < 1e-6 for n in ch["nodes"])
    (b,) = est(r)
    assert b["ends"][1]["kind"] == WB.ALIGNED_FREE_END


def column(x0, x1, y0=400, y1=420, h=50):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [H.part(h, "SEGMENT", (*pts[i], *pts[(i + 1) % 4]), layer="COLUMN", idx=i) for i in range(4)]


def test_F_a_column_over_part_of_the_strip_blocks_only_its_interval():
    r = run(box() + wall(lower=((0, 300), (300, 600))) + column(100, 200))
    (b,) = est(r)
    classes = [(iv["class"], round(iv["s"][0]), round(iv["s"][1])) for iv in b["evidence"]["intervals"]]
    assert (WB.OBSTACLE_OVERLAP, 100, 200) in classes
    assert [c for c in classes if c[0] == WB.SPAN] == [(WB.SPAN, 0, 100), (WB.SPAN, 200, 600)]
    (c,) = authorised(r)                                                    # the free end at the jamb still closes
    assert c["geometry"] == (600, 400, 600, 420)
    (piece,) = c["safety"]["separated_pieces"]
    assert piece["pure_band_interior"] and abs(piece["area"] - 400 * 20) < 1e-6


def test_a_crossing_wall_is_a_node_and_both_sides_stay_spans():
    p = box() + wall(cap=None) + [H.seg(60, 300, 0, 300, 800), H.seg(61, 320, 0, 320, 800)]
    r = run(p, [H.text(5, "A", 150, 100), H.text(6, "C", 650, 100), H.text(7, "B", 150, 700),
                H.text(8, "D", 650, 700)])
    found = [iv["class"] for b in r["wall_bands"]["bands"] for iv in b["evidence"]["intervals"]]
    assert WB.CROSSING_WALL_NODE in found or not any(b["interval"][0] < 300 < b["interval"][1]
                                                     for b in r["wall_bands"]["bands"])


# ------------------------------------------------------------------------------- G, H, I, J
def test_G_three_fragments_in_shuffled_order_give_identical_ids():
    base = box() + wall(lower=((0, 200), (200, 400), (400, 600)))
    ids = None
    for seed in range(4):
        p = list(base)
        random.Random(seed).shuffle(p)
        r = run(p)
        got = (sorted(c["chain_id"] for c in r["wall_bands"]["chains"]), sorted(b["band_id"] for b in est(r)),
               sorted(s["span_id"] for s in r["wall_bands"]["spans"]),
               sorted(c["closure_id"] for c in r["topology_closures"]["closures"]),
               sorted(s["site_id"] for s in r["sites"]))
        ids = ids or got
        assert got == ids


def test_reversed_fragment_orientation_gives_the_same_ids():
    a = run(box() + wall(lower=((0, 300), (300, 600))))
    p = [x if x.identity.source_handle != "11" else H.seg(11, 600, 400, 300, 400)
         for x in box() + wall(lower=((0, 300), (300, 600)))]
    b = run(p)
    assert [x["band_id"] for x in est(a)] == [x["band_id"] for x in est(b)]
    assert [c["closure_id"] for c in authorised(a)] == [c["closure_id"] for c in authorised(b)]


def test_equivalent_resegmentation_of_one_entity_keeps_chain_band_and_closure_ids():
    """Route A gives one authored segment; route B realises the SAME entity as two computational pieces."""
    a = run(box() + wall())
    split = [H.part(10, "SEGMENT", (0, 400, 300, 400), idx=0), H.part(10, "SEGMENT", (300, 400, 600, 400), idx=1)]
    b = run(box() + split + [x for x in wall() if x.identity.source_handle != "10"])
    assert chain_of(a, 10)["chain_id"] == chain_of(b, 10)["chain_id"]
    assert [x["band_id"] for x in est(a)] == [x["band_id"] for x in est(b)]
    assert [c["closure_id"] for c in authorised(a)] == [c["closure_id"] for c in authorised(b)]


def test_unrelated_entity_insertion_keeps_ids():
    a = run(box() + wall())
    b = run(box() + wall() + [H.seg(77, 800, 100, 900, 100)])
    assert [x["band_id"] for x in est(a)] == [x["band_id"] for x in est(b)]


def test_H_an_overlapping_duplicate_fragment_is_an_ambiguity_not_a_double_wall():
    r = run(box() + wall(lower=((0, 600), (200, 400))))
    assert chain_of(r, 10)["chain_id"] == chain_of(r, 11)["chain_id"]
    assert chain_of(r, 10)["duplicate_intervals"]
    assert not est(r) and not authorised(r)
    assert all(b["state"] == WB.AMBIGUOUS for b in r["wall_bands"]["bands"])


def test_a_zero_length_fragment_changes_nothing():
    a = run(box() + wall(lower=((0, 300), (300, 600))))
    b = run(box() + wall(lower=((0, 300), (300, 600))) + [H.seg(66, 300, 400, 300, 400)])
    assert [x["band_id"] for x in est(a)] == [x["band_id"] for x in est(b)] and labelled_area(a) == labelled_area(b)


def test_I_a_near_collinear_furniture_line_is_no_face_chain():
    r = run(box() + wall() + [H.seg(70, 600, 400, 700, 400, layer="FURNITURE")])
    assert not any("|H70|" in f["source"] for c in r["wall_bands"]["chains"] for f in c["fragments"])


def test_J_fragmented_dimension_lines_never_make_a_band():
    p = box() + [H.seg(10, 0, 400, 300, 400, layer="DIM"), H.seg(11, 300, 400, 600, 400, layer="DIM"),
                 H.seg(12, 0, 420, 600, 420, layer="DIM")]
    r = run(p)
    assert r["wall_bands"]["bands"] == []
    assert not any("DIM" in f["source"] or f["source"].split("|")[1] in ("H10", "H11", "H12")
                   for c in r["wall_bands"]["chains"] for f in c["fragments"])


def test_furniture_fragments_never_make_a_band():
    p = box() + [H.seg(10, 0, 400, 300, 400, layer="FURNITURE"), H.seg(11, 300, 400, 600, 400, layer="FURNITURE"),
                 H.seg(12, 0, 420, 600, 420, layer="FURNITURE")]
    assert run(p)["wall_bands"]["bands"] == []


def test_an_unlabelled_slice_of_a_room_is_never_a_band():
    """Local pairing hazard: the room's floor and ceiling walls are locally mutual nearest where no stub lies between
    them; the label anywhere in their RAW strip keeps the room a room."""
    r = run(box() + wall())
    assert all({b["face_a"].split("|")[1], b["face_b"].split("|")[1]} != {"H1", "H3"} for b in r["wall_bands"]["bands"])


# ------------------------------------------------------------------------------- §34 second family
def test_angled_fragmented_double_wall():
    a = math.radians(30)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    P = lambda s, t: (100 + s * ux + t * nx, 100 + s * uy + t * ny)
    p = box() + [H.seg(10, *P(0, 0), *P(250, 0)), H.seg(11, *P(250, 0), *P(500, 0)), H.seg(12, *P(0, 20), *P(500, 20)),
                 H.seg(13, *P(500, 0), *P(500, 20))]
    r = run(p, [H.text(5, "A", 900, 100), H.text(6, "B", 100, 700)])
    (b,) = est(r)
    assert chain_of(r, 10)["chain_id"] == chain_of(r, 11)["chain_id"] and abs(b["width"] - 20) < 1e-6


def block(path, dx=0.0, mirror=False):
    X = (lambda x: dx - x) if mirror else (lambda x: dx + x)
    segs = [(1, 0, 0, 1000, 0), (2, 1000, 0, 1000, 800), (3, 1000, 800, 0, 800), (4, 0, 800, 0, 0),
            (10, 0, 400, 300, 400), (11, 300, 400, 600, 400), (12, 0, 420, 600, 420)]
    return ([H.seg(h, X(a), b, X(c), d, path=path) for h, a, b, c, d in segs],
            [H.text(5, "A", X(300), 100, path=path), H.text(6, "B", X(300), 700, path=path)])


def test_mirrored_fragmented_wall_in_block_occurrences():
    p1, t1 = block(("900",))
    p2, t2 = block(("901",), dx=3000, mirror=True)
    r = run(p1 + p2, t1 + t2)
    bands = est(r)
    assert len(bands) == 2 and len({b["band_id"] for b in bands}) == 2
    assert {b["face_a"].split("|")[2] for b in bands} == {"900", "901"}


def test_fragments_in_different_occurrences_never_join():
    p = box() + [H.seg(10, 0, 400, 300, 400, path=("900",)), H.seg(11, 300, 400, 600, 400),
                 H.seg(12, 0, 420, 600, 420)]
    r = run(p)
    assert all(not ({"H10", "H11"} <= {f["source"].split("|")[1] for f in c["fragments"]})
               for c in r["wall_bands"]["chains"])


def test_nested_fragmented_block_wall_fails_closed_when_not_admitted():
    p, t = block(("900", "901"))
    r = run(p, t)
    if not any(a.role == GR.TOPOLOGY_BOUNDARY for a in r["roles"]["roles"].values()):
        assert r["wall_bands"]["bands"] == [] and r["topology_closures"]["closures"] == []


def test_both_sides_fragmented_differently():
    r = run(box() + wall(lower=((0, 400), (400, 600)), upper=((0, 150), (150, 350), (350, 600))))
    (b,) = est(r)
    assert b["ends"][1]["kind"] == WB.ALIGNED_FREE_END
    assert [c["geometry"] for c in authorised(r)] == [(600, 400, 600, 420)]


def test_open_passage_between_fragmented_wall_ends():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    r = run(p)
    widths = sorted(round(x["width"]) for x in r["passages"])
    assert 120 in widths and len([s for s in r["sites"] if s["labels"]]) == 1       # the passage stays open


# ------------------------------------------------------------------------------- regressions and negative controls
def test_the_9_mm_cap_pattern_still_closes_from_the_face_end_points():
    r = run(box() + wall(lower=((0, 300), (300, 600)), cap=0.92, cap_x=600.05))
    (c,) = authorised(r)
    assert c["corroboration"][0]["grade"] == WB.CAP_CANDIDATE and c["geometry"] == (600, 400, 600, 420)
    assert c["physical_material"] == "NONE" and not c["affects_wall_quantity"]


def test_a_window_jamb_line_beside_glazing_is_still_not_a_wall_end():
    p = box() + [H.seg(20, 300, 0.14, 300, 19.86)] + \
        [H.seg(21 + k, 300, y, 500, y, layer="GLAZING") for k, y in enumerate((0.0, 7.0, 13.0, 20.0))]
    assert run(p, [H.text(5, "A", 500, 400)])["topology_closures"]["closures"] == []


def test_a_single_line_wall_is_unaffected():
    r = run(H.two_rooms(), [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    assert r["wall_bands"]["bands"] == []


def test_corridor_walls_do_not_pair_across_the_corridor():
    walls = [H.seg(10, 0, 300, 500, 300), H.seg(11, 500, 300, 1000, 300), H.seg(12, 0, 320, 1000, 320),
             H.seg(13, 0, 440, 1000, 440), H.seg(14, 0, 460, 1000, 460)]
    r = run(box() + walls, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)])
    pairs = {tuple(sorted({f.split("|")[1] for f in b["faces"]})) for b in est(r)}
    assert pairs == {("H10", "H11", "H12"), ("H13", "H14")}


# ------------------------------------------------------------------------------- policy provenance (§32)
def test_every_behaviour_constant_is_in_the_policy_record():
    rec = WB.policy_record()
    assert rec["params"] == WB.PARAMS and WB.POLICY_ID == "WALL_BAND_POLICY_V3"
    assert (WB.ELONGATION, WB.ID_DECIMALS, WB.CANON_GUARD) == (
        WB.PARAMS["elongation_ratio"], WB.PARAMS["id_coordinate_decimals"], WB.PARAMS["canonical_direction_guard"])
    tree = ast.parse(Path(WB.__file__).read_text())
    params = next(n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "PARAMS"
                                                                           for t in n.targets))
    allowed = {0, 1, 2, -1, 3, 4, 8, 16}      # indices, halving, id length, record truncation, a loop has >= 3 sides
    loose = [(n.lineno, n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant)
             and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
             and not params.lineno <= n.lineno <= params.end_lineno and n.value not in allowed]
    assert loose == []


def test_a_policy_parameter_change_changes_the_policy_digest(monkeypatch):
    before = WB.policy_record()["digest"]
    monkeypatch.setitem(WB.PARAMS, "elongation_ratio", 1.5)
    assert WB.policy_record()["digest"] != before


def test_the_closure_policy_is_untouched():
    assert TC.POLICY_ID == "TOPOLOGY_CLOSURE_POLICY_V1"
    assert TC.policy_record()["digest"] == "46742c570b4d8a036fd6b7446f28055bfd4e1adbff51966e800e5986ca99ccb2"


def test_a_band_carries_no_material():
    r = run(box() + wall(lower=((0, 300), (300, 600))))
    assert WB.policy_record()["means"] == "TOPOLOGY_OBSTACLE_GEOMETRY, not MASONRY_CONFIRMED"
    assert not any(k in b for b in r["wall_bands"]["bands"] for k in ("wall_length", "area", "material", "plaster"))
