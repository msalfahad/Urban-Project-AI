"""T-058: CONCRETE_STRIP_GUARD_V1 - a band face is never lost because a member is cast against it
(engine.source.concrete_strip_guard).

Synthetic plots (not a client drawing). Hand truth, worked on paper from the drawn faces, never from engine output:

  Plot 20.00 x 10.00 m, closed band 0.20 m wide inside the plot line (outer loop = plot line, inner loop offset 0.20 m).
    centre line = (20 - 0.20) x 2 + (10 - 0.20) x 2 = 59.20 m;  plan = 59.20 x 0.20 = 11.84 m2
    (check: 20 x 10 - 19.60 x 9.60 = 200 - 188.16 = 11.84 m2);  at a 0.60 m section: 11.84 x 0.60 = 7.104 m3

  Neighbour side (south) as on a Kuwait villa: corner columns 0.30 x 0.30 at both south corners, footings 1.50 x 1.50
  cast against the plot line at x = 4.25-5.75, 9.25-10.75, 12.00-13.50.
    frozen 5-point sample of the south plot line (x = 0, 5, 10, 15, 20): column edge, footing edge, footing edge,
    nothing, column edge -> 4 / 5 = 0.8 -> the frozen ledger removes it (EXPLAINED_BY_MEMBER), its inner partner is left
    unpaired and the 19.80 m side vanishes. Covered length of that line: 0.30 + 0.30 + 3 x 1.50 = 5.10 m of 20 m
    (+ the 0.03 m explain tolerance past each member end that lies on the line: 4 x 0.03 for the 3 footings' free
    ends is 6 x 0.03 = 0.18 m, the columns' inner ends 2 x 0.03 = 0.06 m) = 5.34 m -> share 0.267, far under 0.8.
    Centre line (y = 0.10) inside members: south 0.20 (column, x 0.10-0.30) + 0.20 (column, x 19.70-19.90)
    + 3 x 1.50 (footings) = 4.90 m; west and east centre lines (x = 0.10 / 19.90) inside the corner columns from
    y = 0.10 to 0.30: 0.20 m each. Held under members = 4.90 + 0.40 = 5.30 m (1.06 m2; check: 2 column overlaps
    0.30 x 0.30 - 0.10 x 0.10 = 0.08 m2 each + 3 footings 1.50 x 0.20 = 0.30 m2 each = 1.06 m2).
    Released = 59.20 - 5.30 = 53.90 m -> 10.78 m2 -> 6.468 m3 at 0.60.
    Frozen view: kept pairs north 19.60 + east 9.60 + west 9.60 = 38.80 m (paired overlap = inner-face basis);
    omissions: the south plot line (20.00 m, removed) and its inner partner (19.60 m, left unpaired); the frozen
    overlap basis also loses 0.20 m on each of the 3 kept sides (centre line 19.80 / 9.80 / 9.80 vs overlap
    19.60 / 9.60 / 9.60) = 0.60 m.

  Footing over the whole south side (0, 0)-(20, 1.50): south 19.80 m under, west and east 0.10-1.50 = 1.40 m each:
    held 22.60 m, released 36.60 m. Never lost.
  Half-covered south side, footing (0, 0)-(10, 1.00): south 0.10-10.00 = 9.90 m, west 0.10-1.00 = 0.90 m:
    held 10.80 m, released 48.40 m.
  South inner face not drawn: north 19.80 (both corners joined), east and west from the inner face end 0.20 to the
    north corner 9.90 = 9.70 m each -> centre line 39.20 m; HELD unpaired: south plot line 20.00 m + the outer east
    and west faces 0.00-0.20 = 0.20 m each = 20.40 m. Nothing is 0, nothing is silent.
  Gap of 1.00 m in the south inner face (x 8.00-9.00): centre line 59.20 - 1.00 = 58.20 m; the plot line over the gap
    HELD unpaired 1.00 m (58.20 + 1.00 = 59.20).
  Open L band, arms along x (outer 6.00 m) and y (outer 4.00 m), width 0.25: centre line (6 - 0.125) + (4 - 0.125)
    = 9.75 m; area 0.25 x (6 + 4 - 0.25) = 2.4375 m2 (exact L-shape area); the two short end faces are not band faces.
  T joint: a 0.20 m stem from the inner face of the north side down to y = 5.00: the stem is not joined to the
    side's centre line (no double count): stem length = its paired overlap 9.80 - 5.00 = 4.80 m.
"""

from __future__ import annotations

import math

import pytest

from engine.source import concrete_strip_guard as SG

W = (0.08, 0.80)                 # the profile's STRIP_WIDTH_M, passed in
RING_CL, RING_AREA, RING_VOL = 59.20, 11.84, 7.104


def _ring(W_=20.0, H=10.0, w=0.20, skip=(), split=None):
    o = [(0, 0), (W_, 0), (W_, H), (0, H)]
    i = [(w, w), (W_ - w, w), (W_ - w, H - w), (w, H - w)]
    lines = []
    for n, P in (("o", o), ("i", i)):
        for k in range(4):
            lid = f"{n}{k}"
            if lid in skip:
                continue
            a, b = P[k], P[(k + 1) % 4]
            if split and lid == split[0]:
                g0, g1 = split[1]
                lines.append({"id": lid + "a", "layer": "BOUNDARY", "a": a, "b": (g0, a[1])})
                lines.append({"id": lid + "b", "layer": "BOUNDARY", "a": (g1, a[1]), "b": b})
                continue
            lines.append({"id": lid, "layer": "BOUNDARY", "a": a, "b": b})
    return lines


def _rect(mid, kind, x0, y0, x1, y1):
    return {"id": mid, "kind": kind, "poly": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]}


NEIGHBOUR = [_rect("C1", "COLUMN", 0, 0, 0.3, 0.3), _rect("C2", "COLUMN", 19.7, 0, 20, 0.3),
             _rect("F1", "FOOTING", 4.25, 0, 5.75, 1.5), _rect("F2", "FOOTING", 9.25, 0, 10.75, 1.5),
             _rect("F3", "FOOTING", 12.0, 0, 13.5, 1.5)]


def _xf(lines, members, f):
    L = [dict(ln, a=f(ln["a"]), b=f(ln["b"])) for ln in lines]
    M = [dict(m, poly=[f(p) for p in m["poly"]]) for m in members]
    return L, M


def _rot(deg, scale=1.0, mirror=False, shift=(0.0, 0.0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def f(p):
        x, y = (-p[0] if mirror else p[0]), p[1]
        return ((c * x - s * y) * scale + shift[0], (s * x + c * y) * scale + shift[1])
    return f


def _faces_conserved(res, lines):
    held = {}
    for h in res["held"]:
        if h["reason"] == "STRIP_FACE_UNPAIRED":
            held[h["id"]] = held.get(h["id"], 0.0) + h["length_m"]
    for f in res["faces"]:
        assert f["in_strip_length_m"] + held.get(f["id"], 0.0) == pytest.approx(f["length_m"], abs=2e-6), f["id"]
    assert len(res["faces"]) + len(res["unsupported"]) >= len(lines)


def test_clean_ring_centre_line_exact():
    lines = _ring()
    res = SG.guard(lines, [], 1.0, W, section_depth_m=0.60)
    t = res["totals"]
    assert t["released_length_m"] == pytest.approx(RING_CL, abs=1e-6)
    assert t["released_area_m2"] == pytest.approx(RING_AREA, abs=1e-6)
    assert t["released_volume_m3"] == pytest.approx(RING_VOL, abs=1e-6)
    assert t["held_under_member_length_m"] == 0 and t["held_unpaired_face_length_m"] == 0
    assert res["held"] == [] and res["unsupported"] == []
    assert res["rings"] == [{"ring": 0, "strips": 4, "closed": True, "centre_line_m": RING_CL, "area_m2": RING_AREA}]
    _faces_conserved(res, lines)


def test_neighbour_side_kept_not_lost():
    lines = _ring()
    res = SG.guard(lines, NEIGHBOUR, 1.0, W, section_depth_m=0.60)
    t = res["totals"]
    assert t["strip_centre_line_m"] == pytest.approx(RING_CL, abs=1e-6)          # conservation
    assert t["held_under_member_length_m"] == pytest.approx(5.30, abs=1e-6)
    assert t["held_under_member_area_m2"] == pytest.approx(1.06, abs=1e-6)
    assert t["released_length_m"] == pytest.approx(53.90, abs=1e-6)
    assert t["released_area_m2"] == pytest.approx(10.78, abs=1e-6)
    assert t["released_volume_m3"] == pytest.approx(6.468, abs=1e-6)
    under = [h for h in res["held"] if h["reason"] == "STRIP_UNDER_MEMBER"]
    assert sorted({m for h in under for m in h["members"]}) == ["C1", "C2", "F1", "F2", "F3"]
    assert all(h["strip_length_m"] > 0 and h["area_m2"] > 0 for h in under)
    assert t["held_unpaired_face_length_m"] == 0
    _faces_conserved(res, lines)


def test_covered_length_share_vs_frozen_five_points():
    res = SG.guard(_ring(), NEIGHBOUR, 1.0, W)
    south = next(f for f in res["faces"] if f["id"] == "o0")
    assert south["frozen_5pt_share"] == pytest.approx(0.8)
    assert south["frozen_rule_explained"] is True                                 # the frozen defect, reproduced
    assert south["covered_length_m"] == pytest.approx(5.34, abs=1e-6)
    assert south["covered_share"] == pytest.approx(0.267, abs=1e-6)
    assert south["in_strip_length_m"] == pytest.approx(20.0, abs=1e-6)            # and here it stays in the strip
    inner = next(f for f in res["faces"] if f["id"] == "i0")
    assert inner["frozen_5pt_share"] == pytest.approx(0.4)                         # footing interior does not count


def test_frozen_view_reports_the_silent_omission():
    lines = _ring()
    for ln in lines:
        ln["state"] = "EXPLAINED_BY_MEMBER" if ln["id"] == "o0" else "UNEXPLAINED"
    res = SG.guard(lines, NEIGHBOUR, 1.0, W, frozen_strip_length_m=38.80)
    fv = res["frozen_view"]
    assert fv["kept_overlap_length_m"] == pytest.approx(38.80, abs=1e-6)
    assert fv["frozen_strip_length_m"] == 38.80
    om = {o["id"]: o for o in fv["omissions"]}
    assert set(om) == {"o0", "i0"}
    assert om["o0"]["length_m"] == pytest.approx(20.0) and om["o0"]["frozen_state"] == "EXPLAINED_BY_MEMBER"
    assert om["i0"]["length_m"] == pytest.approx(19.6) and "partner" in om["i0"]["detail"]
    assert all(o["status"] == "HELD" and o["reason"] == "FROZEN_SILENT_OMISSION" for o in om.values())
    assert fv["corner_basis_loss_m"] == pytest.approx(0.60, abs=1e-6)               # 3 kept sides x 0.20
    assert res["totals"]["strip_centre_line_m"] == pytest.approx(RING_CL, abs=1e-6)


def test_no_frozen_states_no_frozen_view():
    assert SG.guard(_ring(), [], 1.0, W)["frozen_view"] is None


@pytest.mark.parametrize("name,f,unit", [
    ("rotated 37", _rot(37, shift=(1234.5, -987.6)), 1.0),
    ("mirrored", _rot(0, mirror=True), 1.0),
    ("mirrored and rotated 37", _rot(37, mirror=True, shift=(50, 50)), 1.0),
    ("mm", _rot(0, scale=1000.0), 0.001),
    ("mm rotated 37 mirrored", _rot(37, scale=1000.0, mirror=True, shift=(1e6, 2e6)), 0.001),
])
def test_adversarial_frames(name, f, unit):
    lines, members = _xf(_ring(), NEIGHBOUR, f)
    res = SG.guard(lines, members, unit, W, section_depth_m=0.60)
    t = res["totals"]
    assert t["strip_centre_line_m"] == pytest.approx(RING_CL, abs=1e-6), name
    assert t["held_under_member_length_m"] == pytest.approx(5.30, abs=1e-6), name
    assert t["released_volume_m3"] == pytest.approx(6.468, abs=1e-6), name
    assert t["held_unpaired_face_length_m"] == pytest.approx(0.0, abs=1e-6), name
    assert t["n_rings"] == 1, name
    _faces_conserved(res, lines)


def test_footing_over_whole_side_held_never_lost():
    res = SG.guard(_ring(), [_rect("FS", "FOOTING", 0, 0, 20, 1.5)], 1.0, W)
    t = res["totals"]
    assert t["held_under_member_length_m"] == pytest.approx(22.60, abs=1e-6)
    assert t["released_length_m"] == pytest.approx(36.60, abs=1e-6)
    assert t["strip_centre_line_m"] == pytest.approx(RING_CL, abs=1e-6)
    south = [h for h in res["held"] if h["reason"] == "STRIP_UNDER_MEMBER" and h["faces"] == ["o0", "i0"]]
    assert len(south) == 1 and south[0]["strip_length_m"] == pytest.approx(19.80) and south[0]["members"] == ["FS"]


def test_half_covered_side_releases_the_uncovered_part():
    res = SG.guard(_ring(), [_rect("FH", "FOOTING", 0, 0, 10, 1.0)], 1.0, W)
    t = res["totals"]
    assert t["held_under_member_length_m"] == pytest.approx(10.80, abs=1e-6)
    assert t["released_length_m"] == pytest.approx(48.40, abs=1e-6)
    assert t["released_length_m"] + t["held_under_member_length_m"] == pytest.approx(RING_CL, abs=1e-6)


def test_missing_inner_face_held_with_length():
    lines = _ring(skip=("i0",))
    res = SG.guard(lines, [], 1.0, W)
    t = res["totals"]
    assert t["strip_centre_line_m"] == pytest.approx(39.20, abs=1e-6)
    assert t["held_unpaired_face_length_m"] == pytest.approx(20.40, abs=1e-6)
    south = [h for h in res["held"] if h["id"] == "o0"]
    assert len(south) == 1 and south[0]["reason"] == "STRIP_FACE_UNPAIRED" and south[0]["length_m"] == 20.0
    assert t["n_rings"] == 0                                                     # open: no ring claimed
    _faces_conserved(res, lines)


def test_gap_in_inner_face():
    lines = _ring(split=("i0", (8.0, 9.0)))
    res = SG.guard(lines, [], 1.0, W)
    t = res["totals"]
    assert t["strip_centre_line_m"] == pytest.approx(58.20, abs=1e-6)
    gap = [h for h in res["held"] if h["reason"] == "STRIP_FACE_UNPAIRED"]
    assert len(gap) == 1 and gap[0]["id"] == "o0" and gap[0]["length_m"] == pytest.approx(1.0)
    assert gap[0]["from_m"] == pytest.approx(8.0) and gap[0]["to_m"] == pytest.approx(9.0)
    assert t["strip_centre_line_m"] + t["held_unpaired_face_length_m"] == pytest.approx(RING_CL, abs=1e-6)
    _faces_conserved(res, lines)


def test_open_l_band_exact_area():
    w = 0.25
    lines = [{"id": "ox", "a": (0, 0), "b": (6, 0)}, {"id": "ix", "a": (w, w), "b": (6, w)},
             {"id": "oy", "a": (0, 0), "b": (0, 4)}, {"id": "iy", "a": (w, w), "b": (w, 4)},
             {"id": "ex", "a": (6, 0), "b": (6, w)}, {"id": "ey", "a": (0, 4), "b": (w, 4)}]
    res = SG.guard(lines, [], 1.0, (0.1, 0.5))
    t = res["totals"]
    assert t["released_length_m"] == pytest.approx(9.75, abs=1e-6)
    assert t["released_area_m2"] == pytest.approx(2.4375, abs=1e-6)
    assert {h["id"] for h in res["held"]} == {"ex", "ey"}                        # end caps: reported, not measured
    assert t["n_rings"] == 0
    _faces_conserved(res, lines)


def test_t_joint_not_joined():
    lines = _ring() + [{"id": "s1", "a": (9.9, 9.8), "b": (9.9, 5.0)}, {"id": "s2", "a": (10.1, 9.8), "b": (10.1, 5.0)}]
    res = SG.guard(lines, [], 1.0, W)
    stem = [s for s in res["strips"] if set(s["faces"]) == {"s1", "s2"}]
    assert len(stem) == 1 and stem[0]["strip_length_m"] == pytest.approx(4.80, abs=1e-6)
    assert stem[0]["corner_joined"] == [False, False]
    assert res["totals"]["released_length_m"] == pytest.approx(RING_CL + 4.80, abs=1e-6)


def test_lone_face_held():
    lines = [{"id": "L1", "layer": "BOUNDARY", "a": (0, 0), "b": (7.5, 0)}]
    res = SG.guard(lines, [_rect("F", "FOOTING", 0, 0, 1, 1)], 1.0, W)
    assert res["strips"] == []
    assert [(h["id"], h["reason"], h["length_m"]) for h in res["held"]] == [("L1", "STRIP_FACE_UNPAIRED", 7.5)]


def test_wide_offset_is_not_a_strip():
    lines = [{"id": "a", "a": (0, 0), "b": (5, 0)}, {"id": "b", "a": (0, 1.2), "b": (5, 1.2)}]
    res = SG.guard(lines, [], 1.0, W)
    assert res["strips"] == [] and res["totals"]["held_unpaired_face_length_m"] == pytest.approx(10.0)


@pytest.mark.parametrize("unit,width,reason", [(None, W, "UNIT_UNKNOWN"), (0, W, "UNIT_UNKNOWN"),
                                               (1.0, None, "STRIP_WIDTH_UNKNOWN"),
                                               (1.0, (0.5, 0.1), "STRIP_WIDTH_UNKNOWN"),
                                               (1.0, (float("nan"), 0.8), "STRIP_WIDTH_UNKNOWN")])
def test_missing_unit_or_width_unsupported_never_zero(unit, width, reason):
    res = SG.guard(_ring(), [], unit, width)
    assert res["totals"] is None and res["strips"] == []
    assert len(res["unsupported"]) == 8 and {u["reason"] for u in res["unsupported"]} == {reason}


def test_bad_line_and_member_data_unsupported():
    lines = _ring() + [{"id": "bad", "a": (1, None), "b": (2, 2)}, {"id": "zero", "a": (3, 3), "b": (3, 3)}]
    members = [{"id": "M0", "kind": "FOOTING", "poly": [(0, 0), (1, 1)]}]
    res = SG.guard(lines, members, 1.0, W)
    assert {u["id"]: u["reason"] for u in res["unsupported"]} == {"bad": "BAD_LINE_DATA", "zero": "BAD_LINE_DATA",
                                                                  "M0": "BAD_MEMBER_DATA"}
    assert res["totals"]["strip_centre_line_m"] == pytest.approx(RING_CL, abs=1e-6)


def test_no_depth_no_volume_and_bad_depth_refused():
    res = SG.guard(_ring(), [], 1.0, W)
    assert res["totals"]["released_volume_m3"] is None
    assert all("volume_m3" not in s for s in res["strips"])
    with pytest.raises(ValueError):
        SG.guard(_ring(), [], 1.0, W, section_depth_m=0)


def test_deterministic_and_input_untouched():
    lines = _ring()
    snap = [dict(x) for x in lines]
    a = SG.guard(lines, NEIGHBOUR, 1.0, W)
    b = SG.guard(list(reversed(lines)), list(reversed(NEIGHBOUR)), 1.0, W)
    assert lines == snap
    assert a["totals"] == b["totals"]
