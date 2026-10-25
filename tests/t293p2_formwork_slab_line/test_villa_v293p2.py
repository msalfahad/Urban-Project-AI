"""T-293 part 2 rules on a hand-calculated villa (V293P2, not Alsenan): the drawing-face walk of formwork r3 attributed
to the candidate runs of one member by where each walked piece lies (R-FW-P2-5), the edge-band owner (R-FW-P2-2), the
element-method span tie (R-FW-P2-4) and the row closure (R-FW-P2-1).

Villa V293P2 (by hand): one roof beam M, 0.20 wide x 0.50 deep (total depth, slab top = beam top), 6.00 m long on the
x axis (plan face B: x 0 .. 6.00, y 0 .. 0.20); slab panels 0.16 thick each side: N (y 0.20 .. 2.20) and S (y -2.00 ..
0); the beam's two ends are free edges. The candidate splits M into runs A (band x 0 .. 2.50) and B (band x 2.50 .. 6.00).
  sides below the slab, per side: L x (0.50 - 0.16) = 0.34 L     -> A 2 x 2.50 x 0.34 = 1.700, B 2 x 3.50 x 0.34 = 2.380
  end faces (free edge): 0.20 x (0.50 - 0.16) = 0.068 each        -> A (x = 0) 0.068, B (x = 6) 0.068
  slab-thickness band at each beam end: 0.20 x 0.16 = 0.032       -> the BEAM's own face (A 0.032, B 0.032)
  soffits: 0.20 x 2.50 = 0.500 (A), 0.20 x 3.50 = 0.700 (B)
  slab free edges: each panel 6.00 + 2 x 2.00 = 10.00 m x 0.16 = 1.600 (the panel's own line)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t293"))
sys.path.insert(0, str(ROOT / "research" / "agents_t163"))
import face_line_ledger as F  # noqa: E402
import t163_formwork as T  # noqa: E402
import t293p2_ledger as L  # noqa: E402
import t293p2_walk as W  # noqa: E402

from shapely.geometry import box  # noqa: E402
from shapely.affinity import scale  # noqa: E402


def villa(mirror=False):
    faces = {"B": box(0, 0, 6.0, 0.2), "N": box(0, 0.2, 6.0, 2.2), "S": box(0, -2.0, 6.0, 0.0)}
    kind = {"B": "BEAM", "N": "SLAB", "S": "SLAB"}
    depth = {"B": 0.50}
    tslab = {"N": 0.16, "S": 0.16}
    bands = {"A": box(0, 0, 2.5, 0.2), "B": box(2.5, 0, 6.0, 0.2)}
    if mirror:
        faces = {k: scale(v, -1, 1, origin=(0, 0)) for k, v in faces.items()}
        bands = {k: scale(v, -1, 1, origin=(0, 0)) for k, v in bands.items()}
    return faces, kind, depth, tslab, bands


def walk(faces, kind, depth, tslab, cuts=None):
    """the merged r3 walk (exact r2 edges) with or without the run attribution; -> acc {(cat, id): m2}"""
    orig_exact, orig_areas = T._exact_edge, T.face_areas
    W.SPLIT.clear()
    W.STATS.clear()
    try:
        if cuts is not None:
            W.SPLIT["B"] = cuts
            T._exact_edge = W.attributed_exact(orig_exact)
            T.face_areas = W.attributed_areas(orig_areas)
        e = T.classify_edges(faces, dict(kind), depth, tslab, probe=T.PROBE_R2, exact=True)
        k2, d2 = dict(kind), dict(depth)
        return T.face_areas(e, k2, d2, tslab)
    finally:
        T._exact_edge, T.face_areas = orig_exact, orig_areas
        W.SPLIT.clear()


def per(acc, cat):
    out = {}
    for (c, i), v in acc.items():
        if c == cat:
            out[i] = out.get(i, 0.0) + v
    return {k: round(v, 9) for k, v in out.items()}


def cuts_of(bands, shift=0.0):
    from shapely.affinity import translate
    return {k: W.cutter(translate(v, 0, shift)) for k, v in bands.items()}


# ------------------------------------------------------------------------------------------------ NORMAL

def test_unattributed_walk_matches_the_hand_figures():
    f, k, d, t, _ = villa()
    acc = walk(f, k, d, t)
    assert per(acc, "BEAM_SIDE") == {"B": round(2 * 6.0 * 0.34 + 2 * 0.068, 9)}
    assert per(acc, "EDGE_BAND") == {"B": 0.064, "N": 1.6, "S": 1.6}


def test_attribution_by_run_matches_the_hand_figures():
    f, k, d, t, bands = villa()
    acc = walk(f, k, d, t, cuts_of(bands))
    assert per(acc, "BEAM_SIDE") == {"B~A": 1.768, "B~B": 2.448}
    assert per(acc, "EDGE_BAND") == {"B~A": 0.032, "B~B": 0.032, "N": 1.6, "S": 1.6}   # beam end band = the beam's
    soff = W.share(f["B"], cuts_of(bands))
    assert {r: round(v * f["B"].area, 9) for r, v in soff.items()} == {"A": 0.5, "B": 0.7}


def test_attribution_adds_up_to_the_walk_exactly():
    f, k, d, t, bands = villa()
    a, b = walk(f, k, d, t), walk(f, k, d, t, cuts_of(bands))
    for cat in ("BEAM_SIDE", "EDGE_BAND"):
        assert abs(sum(per(a, cat).values()) - sum(per(b, cat).values())) < 1e-9


def test_mirror_gives_the_same_runs():
    f, k, d, t, bands = villa(mirror=True)
    acc = walk(f, k, d, t, cuts_of(bands))
    assert per(acc, "BEAM_SIDE") == {"B~A": 1.768, "B~B": 2.448}


def test_a_span_ties_to_its_run_only_by_its_own_recorded_length():
    runs = [{"run": "M#A", "length_m": "2.5"}, {"run": "M#B", "length_m": "3.5"}]
    assert L.span_member("M", 2.5, runs) == "RUN:M#A"
    assert L.span_member("M", 3.5, runs) == "RUN:M#B"
    assert L.span_member("M", 2.5, runs[:1]) == "BEAM:M"            # one run: the member's one line


def test_ledger_ties_runs_and_keeps_rest_split():
    lines = {"L1": dict(item_code="STR.CONC.BEAM", element_id="M#A", evidence_state="PROVISIONAL"),
             "L2": dict(item_code="STR.CONC.BEAM", element_id="M#B", evidence_state="PROVISIONAL")}
    src = [dict(face_id="R-1", revision="villa", status="CALCULATED", members=["AGGREGATE"], m2=4.316, method="G")]
    P = [dict(src[0], face_id="R-1.a", split_of="R-1", members=["RUN:M#A"], m2=1.768),
         dict(src[0], face_id="R-1.b", split_of="R-1", members=["RUN:M#B"], m2=2.448),
         dict(src[0], face_id="R-1.r", split_of="R-1", members=["BEAM:M"], m2=0.100)]
    b = {"RUN:M#A": ["L1"], "RUN:M#B": ["L2"], "BEAM:M": ["L1", "L2"], "_reason": {}}
    out = F.tie(P, b, lines, source=src)
    t = {r["face_id"]: (r["tie"], r.get("line_id"), r["m2"]) for r in out["rows"]}
    assert t["R-1.a"] == ("TIED", "L1", 1.768) and t["R-1.b"] == ("TIED", "L2", 2.448)
    assert t["R-1.r"] == ("SPLIT_UNRESOLVED", None, None)              # blank, HELD by name, never divided
    assert out["closure"][0]["residual_m2"] == 0.0


def test_row_closure_takes_the_unrounded_sum_of_a_3dp_row():
    rec = dict(face_id="R-2", item="x", m2=4.216, lo=None, hi=None)      # printed to 3 dp
    L.close_row(rec, [dict(m2=1.7684, lo=None, hi=None), dict(m2=2.4479, lo=None, hi=None)])
    assert rec["m2"] == pytest.approx(4.2163, abs=1e-12)
    assert rec["printed"]["m2"] == 4.216 and rec["printed_residual"]["m2"] == pytest.approx(-0.0003, abs=1e-9)


# ------------------------------------------------------------------------------------------------ ADVERSE

def test_a_band_fit_error_across_the_axis_changes_nothing():
    f, k, d, t, bands = villa()
    acc = walk(f, k, d, t, cuts_of(bands, shift=0.0006))          # 0.6 mm, the route G fit error
    assert per(acc, "BEAM_SIDE") == {"B~A": 1.768, "B~B": 2.448}


def test_a_gap_between_band_ends_stays_rest():
    f, k, d, t, _ = villa()
    gap = {"A": W.cutter(box(0, 0, 2.4, 0.2)), "B": W.cutter(box(2.6, 0, 6.0, 0.2))}
    acc = walk(f, k, d, t, gap)
    s = per(acc, "BEAM_SIDE")
    assert s["B~REST"] == pytest.approx(2 * 0.2 * 0.34, abs=1e-9)
    assert s["B~A"] == pytest.approx(2 * 2.4 * 0.34 + 0.068, abs=1e-9)


def test_overlapping_band_ends_are_never_divided():
    f, k, d, t, _ = villa()
    ov = {"A": W.cutter(box(0, 0, 2.6, 0.2)), "B": W.cutter(box(2.4, 0, 6.0, 0.2))}
    orig_exact, orig_areas = T._exact_edge, T.face_areas
    try:
        W.SPLIT.clear(); W.STATS.clear()
        W.SPLIT["B"] = ov
        T._exact_edge, T.face_areas = W.attributed_exact(orig_exact), W.attributed_areas(orig_areas)
        e = T.classify_edges(f, dict(k), d, t, probe=T.PROBE_R2, exact=True)
        acc = T.face_areas(e, dict(k), dict(d), t)
        assert W.STATS["overlap"] > 0
    finally:
        T._exact_edge, T.face_areas = orig_exact, orig_areas
        W.SPLIT.clear()
    s = per(acc, "BEAM_SIDE")
    assert s["B~REST"] == pytest.approx(2 * 6.0 * 0.34, abs=1e-9)   # both long sides straddle the overlap


def test_pieces_that_do_not_close_on_their_row_are_refused():
    rec = dict(face_id="R-3", item="x", m2=4.316, lo=None, hi=None)
    with pytest.raises(F.Refused):
        L.close_row(rec, [dict(m2=1.768, lo=None, hi=None), dict(m2=2.448 - 0.01, lo=None, hi=None)])


def test_a_held_row_cannot_gain_a_quantity_from_its_pieces():
    rec = dict(face_id="R-4", item="x", m2=None, lo=0.0, hi=0.5)
    with pytest.raises(F.Refused):
        L.close_row(rec, [dict(m2=0.2, lo=0.0, hi=0.5)])


def test_a_span_whose_length_matches_no_run_or_two_runs_stays_on_the_member():
    runs = [{"run": "M#A", "length_m": "3.0"}, {"run": "M#B", "length_m": "3.0"}]
    assert L.span_member("M", 3.0, runs) == "BEAM:M"                # two runs of the same length: never chosen
    assert L.span_member("M", 2.95, runs) == "BEAM:M"               # no exact match: never the nearest
    assert L.span_member("M", None, runs) == "BEAM:M"
