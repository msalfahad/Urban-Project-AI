"""T-085 BEAM_BINDING_V2: hand-calculated synthetic fixtures (no project data). Every expected number is worked out
in the comment above its assertion. Bands come from the frozen MEMBER_DETECTION_V1.beam_bands on drawn face lines,
so the fixtures exercise the same pairing the route uses; only the V2 functions differ.

Variants: metres and millimetres, a mirrored and a rotated copy of the planted-column plan, and the adversarial
cases the board asks for (a supporting column mid-span, a label without leader, a printed section that differs
from the drawn outline, a planted column wider than its beam, an arc piece beside a straight mark, a section with
and without an upstand, an unprinted upstand height, a schedule width that proves no unit)."""
import math

import pytest

from engine.source import beam_binding_v2 as BV2
from engine.source import member_detection as MD


# --------------------------------------------------------------------------------------------- helpers
def _xf(p, mirror=False, rot_deg=0.0, k=1.0):
    """metres -> drawing units (k = 1 / unit_m), optional mirror in x and rotation about the origin"""
    x, y = p
    if mirror:
        x = -x
    a = math.radians(rot_deg)
    return ((x * math.cos(a) - y * math.sin(a)) * k, (x * math.sin(a) + y * math.cos(a)) * k)


def _seg(i, a, b, layer, **t):
    return {"id": f"S{i}", "layer": layer, "a": _xf(a, **t), "b": _xf(b, **t)}


def _box(x0, y0, x1, y1, **t):
    pts = [_xf(p, **t) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _plan(mirror=False, rot_deg=0.0, unit_m=1.0, label="P.C 20x30", leader=True, planted_w=0.30, tip="circle"):
    """One beam 0.60 m wide (faces y = 0 and 0.60), x = 0 .. 8.00 m, then mirrored / rotated as asked. Columns keep
    the drawing's axes (as drawn on a real plan with an inclined beam): supporting squares 0.60 x 0.60 centred on the
    beam axis at x 0.30 and 7.70, a planted column 0.20 (drawing x) x planted_w (drawing y) centred at x 4.00.
    Label 'P.C 20x30' at (2.00, -1.20), text height 0.20, landing line 0.10 under it from x 1.40 to 3.00, leader from
    (3.00, -1.30) to the circle (r 0.35) round the planted column (or straight into the outline)."""
    k = 1.0 / unit_m
    t = dict(mirror=mirror, rot_deg=rot_deg, k=k)
    segs = [_seg(1, (0.0, 0.0), (8.0, 0.0), "BEAM", **t), _seg(2, (0.0, 0.60), (8.0, 0.60), "BEAM", **t)]

    def sq(c, w, h):
        x, y = _xf(c, **t)
        return (x - w * k / 2, y - h * k / 2, x + w * k / 2, y + h * k / 2)
    cols = [sq((0.30, 0.30), 0.60, 0.60), sq((7.70, 0.30), 0.60, 0.60)]
    planted = sq((4.00, 0.30), 0.20, planted_w)
    cols.append(planted)
    cx, cy = _xf((4.00, 0.30), **t)
    tip_pt = (cx, cy - 0.35 * k) if tip == "circle" else (cx, cy)
    notes = []
    if leader:
        a_, b_ = _xf((1.40, -1.30), **t), _xf((3.00, -1.30), **t)
        notes = [{"id": "N10", "layer": "NOTE", "a": a_, "b": b_}, {"id": "N11", "layer": "NOTE", "a": b_, "b": tip_pt}]
    circles = [{"id": "C1", "layer": "NOTE", "c": (cx, cy), "r": 0.35 * k}] if tip == "circle" else []
    rot_text = ((180.0 if mirror else 0.0) + rot_deg) % 360.0
    tx, ty = _xf((2.00, -1.20), **t)
    texts = [{"id": "T1", "value": label, "x": tx, "y": ty, "height": 0.20 * k, "rotation": rot_text}]
    th = math.radians(rot_deg)
    return {"segs": segs, "notes": notes, "cols": cols, "planted": planted, "circles": circles, "texts": texts,
            "k": k, "unit_m": unit_m, "c": abs(math.cos(th)), "s": abs(math.sin(th))}


def _bands(P, widths_m=(0.60,)):
    u = P["unit_m"]
    E = {"segments": P["segs"], "arcs": []}
    bands, _ = MD.beam_bands(E, {"BEAM"}, [w / u for w in widths_m], 0.012 / u, 0.3 / u)
    return bands


VARIANTS = [dict(), dict(unit_m=0.001), dict(mirror=True), dict(rot_deg=30.0), dict(rot_deg=-127.0, unit_m=0.001),
            dict(mirror=True, rot_deg=60.0)]


# --------------------------------------------------------------------------------------------- 1. planted columns
@pytest.mark.parametrize("v", VARIANTS)
def test_planted_column_does_not_split_its_beam(v):
    P = _plan(**v)
    u = P["unit_m"]
    tol = 0.012 / u
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], u, tol)
    assert [p["state"] for p in pl] == ["LINKED"]
    assert pl[0]["link"] == "TIP_ON_CIRCLE"
    bands = _bands(P)
    assert len(bands) == 1
    v1 = MD.split_at_supports(bands, P["cols"], 0.05 / u)
    v2 = BV2.split_at_supports_v2(bands, P["cols"], 0.05 / u, planted=pl, tol_native=tol)
    # hand: an axis-aligned box w x h projects onto the beam axis (angle th) as w|cos| + h|sin|. End squares 0.60
    # centred 0.30 in from each end -> each end loses 0.30 + 0.30 (|cos| + |sin|); planted box 0.20 x 0.30.
    # unrotated: V2 one span 8.00 - 2 x 0.60 = 6.80 m; V1 two pieces (6.80 - 0.20) / 2 = 3.30 m each
    c, s_ = P["c"], P["s"]
    span = 8.0 - 2 * (0.30 + 0.30 * (c + s_))
    gap = 0.20 * c + 0.30 * s_
    assert [round(b["length"] * u, 6) for b in v2] == [round(span, 6)]
    assert len(v2[0]["carries_planted"]) == 1
    assert len(v1) == 2 and sum(b["length"] for b in v1) * u == pytest.approx(span - gap, abs=1e-6)
    # volume of the one span with a 0.60 x 0.80 row (unrotated): 6.80 x 0.60 x 0.80 = 3.264 m3; V1 pieces lose the
    # 0.20 x 0.60 x 0.80 = 0.096 m3 under the planted column (3.168 m3)
    lib = {("BEAM", "B1"): {"dims_m": {"W": 0.60, "H": 0.80}, "bars": [], "source": "fixture"}}
    bound = [{"mark": "B1", "family": "BEAM", "state": "BOUND", "bands": [v2[0]["band_id"]], "band": v2[0]["band_id"]}]
    q = MD.beam_quantities(v2, bound, lib, [], u, None)
    assert q[0]["v_total_depth"] == pytest.approx(span * 0.60 * 0.80, abs=1e-6)
    if not v.get("rot_deg"):
        assert q[0]["v_total_depth"] == pytest.approx(3.264, abs=1e-9)


@pytest.mark.parametrize("v", [dict(), dict(rot_deg=30.0, unit_m=0.001)])
def test_supporting_column_mid_span_still_splits(v):
    # no label: the mid column is a support; V2 == V1 (two pieces of 3.60 m)
    P = _plan(label="NOTE 1", **v)
    u = P["unit_m"]
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], u, 0.012 / u)
    assert pl == []
    bands = _bands(P)
    v2 = BV2.split_at_supports_v2(bands, P["cols"], 0.05 / u, planted=pl, tol_native=0.012 / u)
    v1 = MD.split_at_supports(bands, P["cols"], 0.05 / u)
    assert [(b["band_id"], round(b["length"], 6)) for b in v2] == [(b["band_id"], round(b["length"], 6)) for b in v1]
    assert len(v2) == 2 and len(v1) == 2


def test_label_without_leader_is_reported_and_column_still_cuts():
    P = _plan(leader=False)
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], 1.0, 0.012)
    assert [p["state"] for p in pl] == ["NO_LEADER"]
    v2 = BV2.split_at_supports_v2(_bands(P), P["cols"], 0.05, planted=pl, tol_native=0.012)
    assert sorted(round(b["length"], 6) for b in v2) == [3.3, 3.3]


def test_printed_section_differs_from_drawn_outline():
    # label 20x50, drawn 0.20 x 0.30: SECTION_MISMATCH (0.20 m off > 0.02 m size tolerance), the column stays a support
    P = _plan(label="P.C 20x50")
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], 1.0, 0.012)
    assert [p["state"] for p in pl] == ["SECTION_MISMATCH"]
    assert pl[0]["drawn_m"] == (0.2, 0.3)
    v2 = BV2.split_at_supports_v2(_bands(P), P["cols"], 0.05, planted=pl, tol_native=0.012)
    assert len(v2) == 2


def test_leader_tip_inside_the_outline_links_without_circle():
    P = _plan(tip="outline", unit_m=0.001)
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], 0.001, 12.0)
    assert [(p["state"], p["link"]) for p in pl] == [("LINKED", "TIP_IN_OUTLINE")]


def test_leader_to_nothing():
    P = _plan()
    far = [P["notes"][0], dict(P["notes"][1], b=(3.0, -3.0))]
    pl = BV2.planted_columns(P["texts"], far, [], P["cols"], 1.0, 0.012)
    assert [p["state"] for p in pl] == ["LEADER_NO_COLUMN"]


def test_planted_column_wider_than_its_beam_still_cuts():
    # a 'planted' outline 0.80 across a 0.60 beam sticks out of both faces: it is not standing on that beam
    P = _plan(label="P.C 20x80", planted_w=0.80)
    pl = BV2.planted_columns(P["texts"], P["notes"], P["circles"], P["cols"], 1.0, 0.012)
    assert [p["state"] for p in pl] == ["LINKED"]
    v2 = BV2.split_at_supports_v2(_bands(P), P["cols"], 0.05, planted=pl, tol_native=0.012)
    assert sorted(round(b["length"], 6) for b in v2) == [3.3, 3.3]


# --------------------------------------------------------------------------------------------- 2. arc-aware binding
def _arc_plan(unit_m=1.0, mirror=False):
    """A straight 0.20 beam (faces y 0 / 0.20, x 0 .. 1.70) and an arc band (radii 1.735 / 1.935 about
    (2.019, 1.823), swept 215 .. 235 deg, i.e. tangent directions 125 .. 145 deg) whose outer face passes 0.27 m from
    the mark (the mark lies on the 225 deg ray, 1.935 + 0.27 = 2.205 m from the centre).
    Mark 'B7' horizontal (rot 0) at (0.46, 0.264), h 0.30: 0.064 m above the straight band."""
    k = 1.0 / unit_m
    t = dict(mirror=mirror, k=k)
    segs = [_seg(1, (0.0, 0.0), (1.70, 0.0), "BEAM", **t), _seg(2, (0.0, 0.20), (1.70, 0.20), "BEAM", **t)]
    c = (0.46 + 2.205 * math.cos(math.radians(45)), 0.264 + 2.205 * math.sin(math.radians(45)))
    arcs = []
    for i, r in enumerate((1.735, 1.935)):
        s = (c[0] + r * math.cos(math.radians(215)), c[1] + r * math.sin(math.radians(215)))
        e = (c[0] + r * math.cos(math.radians(235)), c[1] + r * math.sin(math.radians(235)))
        m = (c[0] + r * math.cos(math.radians(225)), c[1] + r * math.sin(math.radians(225)))
        arcs.append({"id": f"A{i}", "layer": "BEAM", "c": _xf(c, **t), "r": r * k, "s": _xf(s, **t),
                     "m": _xf(m, **t), "e": _xf(e, **t), "dir": "CW" if mirror else "CCW"})
    E = {"segments": segs, "arcs": arcs}
    bands, _ = MD.beam_bands(E, {"BEAM"}, [0.20 * k], 0.012 * k, 0.3 * k)
    mx, my = _xf((0.46, 0.264), **t)
    mark = {"mark": "B7", "family": "BEAM", "x": mx, "y": my, "h": 0.30 * k, "rot": 0.0}
    return bands, mark, k


@pytest.mark.parametrize("v", [dict(), dict(unit_m=0.001), dict(mirror=True)])
def test_arc_piece_no_longer_makes_a_straight_mark_ambiguous(v):
    bands, mark, k = _arc_plan(**v)
    u = 1.0 / k
    kinds = sorted(b["kind"] for b in bands)
    assert kinds == ["ARC", "STRAIGHT"]
    wof = {("BEAM", "B7"): (0.20,)}
    arc = next(b for b in bands if b["kind"] == "ARC")
    st = next(b for b in bands if b["kind"] == "STRAIGHT")
    # distances: straight 0.064 m, arc outer face < 0.064 + 0.30 (the ambiguity margin = h): V1 cannot tell them apart
    d_st = MD.dist_point_poly(mark["x"], mark["y"], st["polygon"]) * u
    d_arc = MD.dist_point_poly(mark["x"], mark["y"], arc["polygon"]) * u
    assert d_st == pytest.approx(0.064, abs=1e-6)
    assert d_arc == pytest.approx(0.27, abs=1e-3)
    assert d_arc - d_st <= 0.30 and d_arc <= 0.75
    v1 = MD.bind_marks(bands, [mark], wof, u)
    assert v1[0]["state"] == "AMBIGUOUS"
    v2 = BV2.bind_marks_v2(bands, [mark], wof, u)
    # the arc's tangents run 125 .. 145 deg (mirror: 35 .. 55): at least 35 deg from the horizontal mark > 12
    assert BV2.arc_angle_gap(0.0, arc) == pytest.approx(35.0, abs=1e-6)
    assert v2[0]["state"] == "BOUND" and v2[0]["bands"] == [st["band_id"]]


def test_mark_parallel_to_an_arc_piece_still_binds_it():
    bands, mark, k = _arc_plan()
    arc = next(b for b in bands if b["kind"] == "ARC")
    # a mark written along the arc (rot 135 = its mid tangent) 0.10 outside its outer face binds the arc, as in V1
    c = arc["centre"]
    r = arc["r_outer"] + 0.10
    m = dict(mark, x=c[0] + r * math.cos(math.radians(225)), y=c[1] + r * math.sin(math.radians(225)), rot=135.0)
    wof = {("BEAM", "B7"): (0.20,)}
    v1 = MD.bind_marks(bands, [m], wof, 1.0)
    v2 = BV2.bind_marks_v2(bands, [m], wof, 1.0)
    assert v2[0]["state"] == "BOUND" and v2[0]["bands"] == [arc["band_id"]]
    assert (v1[0]["state"], v1[0].get("bands")) == (v2[0]["state"], v2[0].get("bands"))


def test_arc_without_range_keeps_v1_and_says_so():
    bands, mark, k = _arc_plan()
    nb = [dict(b, OVERLAP_RANGE=None, start_rad=None) if b["kind"] == "ARC" else b for b in bands]
    v2 = BV2.bind_marks_v2(nb, [mark], {("BEAM", "B7"): (0.20,)}, 1.0)
    assert v2[0]["state"] == "AMBIGUOUS" and v2[0]["arc_angle_untested"]


def test_arc_angle_gap_wraps():
    b = {"OVERLAP_RANGE": [350.0, 20.0]}                 # tangents 80 .. 110 deg across the 0/360 seam
    assert BV2.arc_directions(b) == (80.0, 30.0)
    assert BV2.arc_angle_gap(95.0, b) == 0.0
    assert BV2.arc_angle_gap(275.0, b) == 0.0           # the same undirected line
    assert BV2.arc_angle_gap(60.0, b) == pytest.approx(20.0)
    assert BV2.arc_angle_gap(130.0, b) == pytest.approx(20.0)


# --------------------------------------------------------------------------------------------- 3. upstands
def _section(k=40.0, upstand=True, left=False, print_h=True, unit="cm"):
    """A 40 x 75 beam drawn at 4 units per cm (x0 = 0), with a 20 x 20 upstand on the right (or left) top.
    Dimensions print cm (or mm: x10) with DIMLFAC already applied (the shown value)."""
    f = 10.0 if unit == "mm" else 1.0
    W, D, w, h = 40 * k / 10, 75 * k / 10, 20 * k / 10, 20 * k / 10      # drawing units (k / 10 per cm)
    if upstand and not left:
        pts = [(0, 0), (W, 0), (W, D + h), (W - w, D + h), (W - w, D), (0, D)]
    elif upstand:
        pts = [(0, 0), (W, 0), (W, D), (w, D), (w, D + h), (0, D + h)]
    else:
        pts = [(0, 0), (W, 0), (W, D), (0, D)]
    dims = [{"axis": "x", "lo": 0, "hi": W, "shown": 40 * f}, {"axis": "y", "lo": 0, "hi": D, "shown": 75 * f}]
    if upstand:
        ux0, ux1 = (W - w, W) if not left else (0, w)
        dims.append({"axis": "x", "lo": ux0, "hi": ux1, "shown": 20 * f})
        if print_h:
            dims.append({"axis": "y", "lo": D, "hi": D + h, "shown": 20 * f})
    return pts, dims


def test_section_with_upstand_cm():
    pts, dims = _section()
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    assert p["state"] == "PRINTED" and p["unit_m"] == 0.01
    assert (p["beam_w_m"], p["beam_d_m"]) == (0.40, 0.75)
    assert p["upstand"] == {"w_m": 0.20, "h_m": 0.20, "side": "FLUSH_RIGHT"}


def test_section_mirrored_and_in_mm():
    pts, dims = _section(left=True, unit="mm")
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    assert p["unit_m"] == 0.001 and p["upstand"]["side"] == "FLUSH_LEFT"
    assert (p["upstand"]["w_m"], p["upstand"]["h_m"]) == (0.20, 0.20)


def test_section_without_upstand():
    pts, dims = _section(upstand=False)
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    assert p["state"] == "PRINTED" and p["upstand"] is None
    assert BV2.upstand_lines(p, None, [], 1.0)["state"] == "NOT_PRESENT"


def test_upstand_height_not_printed_is_held_never_zero():
    pts, dims = _section(print_h=False)
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    assert p["state"] == "HELD" and "not printed" in p["why"]
    up = BV2.upstand_lines(p, {"state": "CUT", "bands": ["X"]}, [], 1.0)
    assert up["state"] == "HELD" and "volume_m3" not in up


def test_schedule_width_that_proves_no_unit():
    pts, dims = _section()
    p = BV2.section_profile(pts, dims, 0.45, 0.75, 1.0)   # 0.45 / 40 = 0.01125: neither cm, mm nor m
    assert p["state"] == "HELD"


def test_section_depth_differs_from_schedule():
    pts, dims = _section()
    p = BV2.section_profile(pts, dims, 0.40, 0.70, 1.0)
    assert p["state"] == "HELD" and "RFI" in p["why"]


def test_dimension_at_another_scale_is_not_used():
    pts, dims = _section()
    dims = [dict(d, shown=30.0) if d["axis"] == "y" and d["lo"] > 0 else d for d in dims]   # 30 printed on a 20 edge
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    assert p["state"] == "HELD"


def _cut_plan(rot_deg=0.0):
    """Beam 0.40 wide, faces y 0 / 0.40, x 0 .. 3.00 (clear span 3.00); a cut line x = 1.20 from y -0.60 to 1.00 with
    view arrows (0.80 long, x 0.90 .. 1.70) at y -0.40 and y 0.80; letter 'A' at (0.60, -0.40) and (0.60, 0.80).
    A rebar line x = 2.00 from y -0.60 to 1.00, crossed by a distribution bar, but no letter near it."""
    t = dict(rot_deg=rot_deg)
    segs = [_seg(1, (0, 0), (3, 0), "BEAM", **t), _seg(2, (0, 0.40), (3, 0.40), "BEAM", **t)]
    sym = [_seg(3, (1.20, -0.60), (1.20, 1.00), "SEC", **t), _seg(4, (0.90, -0.40), (1.70, -0.40), "SEC", **t),
           _seg(5, (0.90, 0.80), (1.70, 0.80), "SEC", **t), _seg(6, (2.00, -0.60), (2.00, 1.00), "REIN", **t),
           _seg(7, (2.40, 0.70), (5.40, 0.70), "REIN", **t)]
    texts = []
    for i, y in enumerate((-0.40, 0.80)):
        x, y_ = _xf((0.60, y), **t)
        texts.append({"id": f"L{i}", "value": "A", "x": x, "y": y_, "height": 0.35})
    x, y_ = _xf((5.00, 0.90), **t)
    texts.append({"id": "R", "value": "5T10/m", "x": x, "y": y_, "height": 0.20})
    bands, _ = MD.beam_bands({"segments": segs, "arcs": []}, {"BEAM"}, [0.40], 0.012, 0.3)
    return segs + sym, texts, bands


@pytest.mark.parametrize("rot", [0.0, 37.0])
def test_cut_line_upstand_line(rot):
    segs, texts, bands = _cut_plan(rot)
    cuts = BV2.section_cuts(texts, segs, bands, 1.0, edge_layers={"BEAM"}, titles={"A"})
    assert cuts["A"]["state"] == "CUT" and cuts["A"]["bands"] == [bands[0]["band_id"]]
    assert cuts["A"]["segment"][0] == "S3"
    pts, dims = _section()
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    up = BV2.upstand_lines(p, cuts["A"], bands, 1.0, section="A-A", mark="B1")
    # 0.20 x 0.20 x 3.00 = 0.120 m3
    assert up["state"] == "MEASURED"
    assert up["length_m"] == pytest.approx(3.0) and up["volume_m3"] == pytest.approx(0.12)


def test_cut_line_on_a_beam_of_another_width_is_held():
    segs, texts, bands = _cut_plan()
    cuts = BV2.section_cuts(texts, segs, bands, 1.0, edge_layers={"BEAM"}, titles={"A"})
    pts, dims = _section()
    p = BV2.section_profile(pts, dims, 0.40, 0.75, 1.0)
    p = dict(p, beam_w_m=0.30)                             # the section shows a 0.30 beam; the cut crosses a 0.40 one
    assert BV2.upstand_lines(p, cuts["A"], bands, 1.0)["state"] == "HELD"


def test_letter_without_title_gives_no_cut():
    segs, texts, bands = _cut_plan()
    assert BV2.section_cuts(texts, segs, bands, 1.0, edge_layers={"BEAM"}, titles={"B"}) == {}


def test_policy_record():
    r = BV2.policy_record()
    assert r["policy"] == "BEAM_BINDING_V2" and "member_detection.py" in r["frozen_untouched"]


# --------------------------------------------------------------------------------------------- 4. ring beams
def _ring_plan(inner_circle=False, half=False, mirror=False, unit_m=1.0):
    """Ring 0.20 wide (r 1.00 / 1.20) round an opening centred (5, 5), crossed through its centre by a straight beam
    0.30 wide (faces y 4.85 / 5.15, x 2.5 .. 7.5). The ring's faces are drawn where they are not inside that beam:
    inner from 8.627 to 171.373 deg and 188.627 to 351.373 deg (asin 0.15 / 1.00), outer from 7.181 deg
    (asin 0.15 / 1.20) likewise; inner_circle: the inner face is one full CIRCLE instead; half: only the upper outer
    and inner arcs are drawn. Mark 'B4' along the upper outer arc at 90 deg, 0.15 outside it."""
    k = 1.0 / unit_m
    t = dict(mirror=mirror, k=k)
    c = (5.0, 5.0)
    segs = [_seg(1, (2.5, 4.85), (7.5, 4.85), "BEAM", **t), _seg(2, (2.5, 5.15), (7.5, 5.15), "BEAM", **t)]
    arcs, circles = [], []

    def arc(i, r, a0, a1):
        s = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
        e = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
        m = (c[0] + r * math.cos(math.radians((a0 + a1) / 2)), c[1] + r * math.sin(math.radians((a0 + a1) / 2)))
        if mirror:
            s, e = e, s
        arcs.append({"id": f"A{i}", "layer": "BEAM", "c": _xf(c, **t), "r": r * k, "s": _xf(s, **t),
                     "m": _xf(m, **t), "e": _xf(e, **t), "dir": "CCW"})
    for i, r in enumerate((1.0, 1.2)):
        d = math.degrees(math.asin(0.15 / r))
        if r == 1.0 and inner_circle:
            circles.append({"id": "C0", "layer": "BEAM", "c": _xf(c, **t), "r": r * k})
            continue
        arc(2 * i, r, d, 180 - d)
        if not half:
            arc(2 * i + 1, r, 180 + d, 360 - d)
    E = {"segments": segs, "arcs": arcs}
    bands, _ = MD.beam_bands(E, {"BEAM"}, [0.20 * k, 0.30 * k], 0.012 * k, 0.3 * k)
    mx, my = _xf((5.0, 6.35), **t)
    marks = [{"mark": "B4", "family": "BEAM", "x": mx, "y": my, "h": 0.30 * k, "rot": 0.0}]
    wof = {("BEAM", "B4"): (0.20,), ("BEAM", "B1"): (0.30,)}
    lib = {("BEAM", "B4"): {"dims_m": {"W": 0.20, "H": 0.50}, "bars": [], "source": "fixture"},
           ("BEAM", "B1"): {"dims_m": {"W": 0.30, "H": 0.60}, "bars": [], "source": "fixture"}}
    bound = BV2.bind_marks_v2(bands, marks, wof, unit_m)
    return arcs, circles, bands, bound, wof, lib, k


# hand: annulus pi (1.2^2 - 1.0^2) = 1.382301; strip |y| <= a inside a disc R: S(R) = 2 (a sqrt(R^2 - a^2) +
# R^2 asin(a / R)); S(1.2) - S(1.0) = 0.7181217 - 0.5977426 = 0.1203791 (in the straight beam) -> 1.2619225 m2
# x 0.50 = 0.6309613 m3
RING_NET_M2 = math.pi * 0.44 - (2 * (0.15 * math.sqrt(1.44 - 0.0225) + 1.44 * math.asin(0.125)) -
                                2 * (0.15 * math.sqrt(1 - 0.0225) + math.asin(0.15)))


@pytest.mark.parametrize("v", [dict(), dict(mirror=True), dict(unit_m=0.001)])
def test_ring_beam_with_printed_mark(v):
    arcs, circles, bands, bound, wof, lib, k = _ring_plan(**v)
    u = 1.0 / k
    assert bound[0]["state"].startswith("BOUND")
    r = BV2.ring_beams(arcs, circles, bands, [], bound, wof, lib, u, 0.012 * k)
    assert len(r) == 1 and r[0]["state"] == "PRINTED_MARK" and r[0]["mark"] == "B4"
    assert RING_NET_M2 == pytest.approx(1.2619225, abs=1e-6)
    assert r[0]["net_plan_m2"] == pytest.approx(RING_NET_M2, rel=2e-4)
    assert r[0]["volume_m3"] == pytest.approx(0.6309613, rel=2e-4)
    assert r[0]["pieces"] == 2 and len(r[0]["arc_bands"]) == 2


def test_ring_drawn_with_a_full_inner_circle_has_no_v1_band_but_a_ring_line():
    arcs, circles, bands, bound, wof, lib, k = _ring_plan(inner_circle=True)
    assert not [b for b in bands if b["kind"] == "ARC"]          # V1 pairs arcs only: no band, nothing bound
    held = BV2.ring_beams(arcs, circles, bands, [], bound, wof, lib, 1.0, 0.012)
    assert [x["state"] for x in held] == ["HELD"]                  # no mark of its own: held, never 0
    assert "volume_m3" not in held[0]
    fb = {"family": "BEAM", "mark": "B4", "basis": "owner answer"}
    r = BV2.ring_beams(arcs, circles, bands, [], bound, wof, lib, 1.0, 0.012, fallback=fb)
    assert r[0]["state"] == "OWNER_RULE" and r[0]["volume_m3"] == pytest.approx(0.6309613, rel=2e-4)


def test_half_drawn_ring_is_measured_as_drawn():
    # only the upper half is drawn: the lower half has no face at all, so it is no concrete; the upper piece is
    # half the symmetric net: 1.2619225 / 2 = 0.6309613 m2 x 0.50 = 0.3154806 m3
    arcs, circles, bands, bound, wof, lib, k = _ring_plan(half=True)
    r = BV2.ring_beams(arcs, circles, bands, [], bound, wof, lib, 1.0, 0.012)
    assert [x["state"] for x in r] == ["PRINTED_MARK"] and r[0]["pieces"] == 1
    assert r[0]["volume_m3"] == pytest.approx(0.3154806, rel=2e-4)


def test_ring_piece_half_drawn_is_partial_and_changes_nothing():
    # the upper outer arc stops at 45 / 135 deg while its inner arc runs on: that piece meets the outer circle where
    # nothing is drawn -> PARTIAL, no volume (the arc band pieces stay as V1 / V2 give them)
    arcs, circles, bands, bound, wof, lib, k = _ring_plan()
    c = (5.0, 5.0)
    a = next(x for x in arcs if x["r"] == 1.2 and x["s"][1] > 5.0)
    a.update(s=(c[0] + 1.2 * math.cos(math.radians(45)), c[1] + 1.2 * math.sin(math.radians(45))),
             e=(c[0] + 1.2 * math.cos(math.radians(135)), c[1] + 1.2 * math.sin(math.radians(135))))
    r = BV2.ring_beams(arcs, circles, bands, [], bound, wof, lib, 1.0, 0.012)
    assert [x["state"] for x in r] == ["PARTIAL_RING"] and "volume_m3" not in r[0]


def test_ring_width_not_scheduled_is_no_ring():
    arcs, circles, bands, bound, wof, lib, k = _ring_plan()
    assert BV2.ring_beams(arcs, circles, bands, [], bound, {("BEAM", "B1"): (0.30,)}, lib, 1.0, 0.012) == []
