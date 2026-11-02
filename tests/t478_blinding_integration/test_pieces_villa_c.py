"""T-478 R-T478-1 on a hand-calculated villa C (not the development villa): 3 pits + one strap crossing two pits.

Hand calculation (t = p = 0.10 m printed):
  P1 2.00 x 2.00 -> grown 2.20 x 2.20 = 4.84 m2 -> 0.484 m3
  P2 1.50 x 1.50 -> grown 1.70 x 1.70 = 2.89 m2 -> 0.289 m3
  P3 1.80 x 1.20 -> grown 2.00 x 1.40 = 2.80 m2 -> 0.280 m3      pit layer 10.53 m2 -> 1.053 m3 (no overlap)
  strap 0.30 wide, x 1.00 .. 5.75 (P1 centre to P2 centre) -> grown 4.95 x 0.50 = 2.475 m2 (own layer 0.2475 m3)
    over P1's grown plan 1.20 x 0.50 = 0.600, over P2's 0.95 x 0.50 = 0.475 -> overlap 1.075 m2 netted ONCE
    merged = (2.475 - 1.075) x 0.10 = 0.140 m3 = the clear 2.80 between grown faces x 0.50 x 0.10
"""
import math

import pytest

from engine.source import arch_v3045 as M


def rect(x, y, a, b):
    return [(x, y), (x + a, y), (x + a, y + b), (x, y + b)]


def villa(t3=0.10, p3=0.10):
    pits = [{"id": "P1", "outline": rect(0, 0, 2.0, 2.0), "depth": 1.0, "t": 0.10, "p": 0.10},
            {"id": "P2", "outline": rect(5.0, 0, 1.5, 1.5), "depth": 1.2, "t": 0.10, "p": 0.10},
            {"id": "P3", "outline": rect(0, 5.0, 1.8, 1.2), "depth": 1.0, "t": t3, "p": p3}]
    strap = [{"id": "S1", "strip": rect(1.0, 0.85, 4.75, 0.30), "t": 0.10, "p": 0.10}]
    return pits, strap


def tf(pits, members, f):
    out = []
    for x in pits:
        out.append(dict(x, outline=[f(*q) for q in x["outline"]]))
    mem = [dict(m, strip=[f(*q) for q in m["strip"]]) for m in members]
    return out, mem


def test_normal_hand_values():
    pits, strap = villa()
    r = M.blinding_pieces(pits, None, strap)
    by = {p["id"]: p for p in r["pits"]}
    assert by["P1"]["inside_m3"] == 0.484 and by["P2"]["inside_m3"] == 0.289 and by["P3"]["inside_m3"] == 0.28
    assert r["layer"]["inside_m2"] == 10.53 and r["layer"]["inside_m3"] == 1.053
    m = r["members"][0]
    assert m["strip_m2"] == 2.475 and m["overlap_m2"] == 1.075
    assert m["merged_m3"] == 0.14 and m["own_layer_m3"] == 0.2475
    assert r["layer"]["members_merged_m3"] == 0.14 and r["layer"]["members_overlap_with_pits_m2"] == 1.075


@pytest.mark.parametrize("f,u", [(lambda x, y: (-x, y), 1.0), (lambda x, y: (-y, x), 1.0),
                                 (lambda x, y: (x * 1000.0, y * 1000.0), 0.001)])
def test_mirror_rotation_units_identical(f, u):
    pits, strap = tf(*villa(), f)
    r = M.blinding_pieces(pits, None, strap, unit_m=u)
    assert r["layer"]["inside_m3"] == 1.053 and r["members"][0]["merged_m3"] == 0.14
    assert r["members"][0]["overlap_m2"] == 1.075


def test_adverse_plot_line_clips_a_pit():
    pits, strap = villa()
    plot = rect(-1.0, -1.0, 7.5, 11.0)              # right edge x = 6.50 cuts P2's grown plan (to 6.60)
    r = M.blinding_pieces(pits, plot, strap)
    p2 = {p["id"]: p for p in r["pits"]}["P2"]
    assert p2["beyond_m2"] == 0.17 and p2["beyond_high_m3"] == 0.017 and p2["inside_m3"] == 0.272
    assert r["layer"]["inside_m3"] == 1.036 and r["layer"]["beyond_high_m3"] == 0.017
    assert math.isclose(p2["inside_m3"] + p2["beyond_high_m3"], 0.289, abs_tol=1e-9)


def test_adverse_thickness_not_printed_is_held_never_zero():
    pits, strap = villa(t3=None)
    r = M.blinding_pieces(pits, None, strap)
    p3 = {p["id"]: p for p in r["pits"]}["P3"]
    assert p3["status"] == "HELD" and p3["inside_m3"] is None
    assert r["layer"]["held"] == ["P3"] and r["layer"]["inside_m3"] == 0.773
    with pytest.raises(M.InputsError):
        M.blinding_pieces(villa(t3=0)[0], None)


def test_adverse_projection_not_printed_is_at_least():
    pits, _ = villa(p3=None)
    p3 = {p["id"]: p for p in M.blinding_pieces(pits, None)["pits"]}["P3"]
    assert p3["status"] == "AT_LEAST" and p3["inside_m3"] == 0.216     # 1.80 x 1.20 x 0.10, no projection


def test_adverse_overlap_owner():
    a = {"id": "A", "outline": rect(0, 0, 2.0, 2.0), "depth": 1.0, "t": 0.1, "p": 0.1}
    b = {"id": "B", "outline": rect(2.1, 0, 2.0, 2.0), "depth": 1.5, "t": 0.1, "p": 0.1}
    r = M.blinding_pieces([a, b], None)
    by = {p["id"]: p for p in r["pits"]}
    # grown plans overlap 0.10 x 2.20 = 0.22 m2; the deeper B owns it, A is clipped: one layer
    assert by["A"]["ceded"] == [{"to": "B", "m2": 0.22}] and by["A"]["own_m2"] == 4.62
    assert r["layer"]["inside_m2"] == 9.46
    with pytest.raises(M.InputsError, match="no deeper owner"):
        M.blinding_pieces([a, dict(b, depth=1.0)], None)


def test_plate_restated_term_by_term_closes_both_ends():
    r = M.plate_terms(5.0, [{"term": "pits", "low": 1.053, "high": 1.053, "cause": "VERIFIED"},
                            {"term": "strap", "low": 0.14, "high": 0.2475, "cause": "detail"}])
    rd = r["rows"][-1]
    assert rd["term"] == "RULE_DIFFERENCE" and rd["low"] == 3.6995 and rd["high"] == 3.807
    assert r["closes_low"] and r["closes_high"]
    with pytest.raises(M.InputsError):
        M.plate_terms(1.0, [{"term": "pits", "low": 1.053, "high": 1.053, "cause": "x"}])
