"""T-276 villa P (synthetic, not Alsenan, hand-calculated): buried ground-beam faces on TRACED lengths.

Plan (mm): perimeter beams 300 wide round a 6.30 x 4.30 m house, corner columns 300 x 300, an interior beam S5
(x 3000..3300) teeing into the top and bottom beams, and a column C5 300 x 400 standing in the bottom beam at x 4500..4800
(it splits the bottom beam into S1a / S1b and projects 100 mm into panel P2). Levels: beam top +0.75, perimeter D 0.95
(soffit -0.20, natural ground +-0.00), interior D 0.40, slab 0.10.

Hand calculation (m2):
  S1a inner face: P1 2.70 + P2 1.20 = 3.90 m (run 4.20: 0.30 under the S5 tee) x 0.85 = 3.315; outer 4.20 x 0.20 = 0.84
  S1b inner 1.20 x 0.85 = 1.02; outer 1.20 x 0.20 = 0.24
  S2 inner 2.70 + 2.70 = 5.40 x 0.85 = 4.59 (run 5.70); outer 5.70 x 0.20 = 1.14
  S3 / S4 inner 3.70 x 0.85 = 3.145 each; outer 3.70 x 0.20 = 0.74 each
  S5 two faces 3.70 x 0.30 = 1.11 each
  total 21.135; column faces: corners 4 x 0.60 outside, C5 0.30 outside + 0.50 on P2 -> neck line, never here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t276"))
import buried_faces_v2 as F  # noqa: E402
import face_trace as FT  # noqa: E402

W = F.W
shapely = pytest.importorskip("shapely")
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

TOP, NG, SLAB = 0.75, 0.0, 0.10
EXT = {"depth": 0.95, "depth_range": None, "top": TOP, "slab_t": SLAB, "natural_ground": NG}
INT = {"depth": 0.40, "depth_range": None, "top": TOP, "slab_t": SLAB, "natural_ground": NG}


def span(sid, poly, u):
    """Band frame read from the drawn rectangle itself: offsets along n, stations along u (no value typed)."""
    n = (-u[1], u[0])
    cs = list(poly.exterior.coords)
    offs = [x * n[0] + y * n[1] for x, y in cs]
    sts = [x * u[0] + y * u[1] for x, y in cs]
    return ("SPAN", sid, poly, {"u": u, "n": n, "lo": min(offs), "hi": max(offs), "ta": min(sts), "tb": max(sts)})


def villa_p(transform="none"):
    """transform: 'none', 'mirror' (about x = 0) or 'rotate' (90 degrees about the origin)."""
    from shapely import affinity

    def tf(g):
        if transform == "mirror":
            return affinity.scale(g, xfact=-1.0, yfact=1.0, origin=(0, 0))
        if transform == "rotate":
            return affinity.rotate(g, 90.0, origin=(0, 0))
        return g

    def tu(u):
        if transform == "mirror":
            return (-u[0], u[1])
        if transform == "rotate":
            return (-u[1], u[0])
        return u
    X, Y = (1.0, 0.0), (0.0, 1.0)
    owners = [span("S1a", tf(box(300, 0, 4500, 300)), tu(X)), span("S1b", tf(box(4800, 0, 6000, 300)), tu(X)),
              span("S2", tf(box(300, 4000, 6000, 4300)), tu(X)), span("S3", tf(box(0, 300, 300, 4000)), tu(Y)),
              span("S4", tf(box(6000, 300, 6300, 4000)), tu(Y)), span("S5", tf(box(3000, 300, 3300, 4000)), tu(Y))]
    for i, (x0, y0) in enumerate(((0, 0), (6000, 0), (0, 4000), (6000, 4000))):
        owners.append(("COLUMN", f"K{i + 1}", tf(box(x0, y0, x0 + 300, y0 + 300)), {}))
    owners.append(("COLUMN", "C5", tf(box(4500, 0, 4800, 400)), {}))
    solid = unary_union([o[2] for o in owners])
    holes, small, outers = FT.panels_and_outers(solid, 0.05e6)
    rings = [(f"P{k}", list(h.exterior.coords)) for k, h in enumerate(holes, 1)]
    rings += [(f"OUTER-{k}", c) for k, c in enumerate(outers, 1)]
    return owners, rings, small


def ledger(transform="none"):
    owners, rings, small = villa_p(transform)
    t = FT.trace(owners, rings, step=5.0)
    mem = {"S1a": EXT, "S1b": EXT, "S2": EXT, "S3": EXT, "S4": EXT, "S5": INT}
    rows, neck_len, by_span = [], {}, {}
    for bid, _ in rings:
        pieces = [{"member_kind": k, "member": m, "face": f, "length_m": L / 1000.0}
                  for (k, m, f), L in t[bid]["pieces"].items()]
        F.check_closure(bid, t[bid]["length"] / 1000.0, pieces)
        kind = "OUTER" if bid.startswith("OUTER") else "PANEL"
        for p in pieces:
            if p["member_kind"] == "COLUMN":
                neck_len[(p["member"], kind)] = neck_len.get((p["member"], kind), 0.0) + p["length_m"]
                with pytest.raises(F.RefusedError):
                    F.face_row(bid, "COLUMN", "x", kind, "FILL", p["length_m"], {})
                continue
            r = F.face_row(f"{p['member']}|{bid}", "SPAN", p["face"], kind, "FILL" if kind == "PANEL" else None,
                           p["length_m"], mem[p["member"]])
            rows.append(r)
            by_span[(p["member"], kind)] = by_span.get((p["member"], kind), 0.0) + (r.qty or 0.0)
    return rows, neck_len, by_span, small


@pytest.mark.parametrize("transform", ["none", "mirror", "rotate"])
def test_villa_p_by_hand(transform):
    rows, neck_len, by, small = ledger(transform)
    assert not small
    assert all(r.status == W.DC for r in rows)
    assert by[("S1a", "PANEL")] == pytest.approx(3.315, abs=1e-4)
    assert by[("S1a", "OUTER")] == pytest.approx(0.84, abs=1e-4)
    assert by[("S1b", "PANEL")] == pytest.approx(1.02, abs=1e-4)
    assert by[("S1b", "OUTER")] == pytest.approx(0.24, abs=1e-4)
    assert by[("S2", "PANEL")] == pytest.approx(4.59, abs=1e-4)
    assert by[("S2", "OUTER")] == pytest.approx(1.14, abs=1e-4)
    for s in ("S3", "S4"):
        assert by[(s, "PANEL")] == pytest.approx(3.145, abs=1e-4)
        assert by[(s, "OUTER")] == pytest.approx(0.74, abs=1e-4)
    assert by[("S5", "PANEL")] == pytest.approx(2.22, abs=1e-4)
    assert W.measured_total(rows) == pytest.approx(21.135, abs=1e-4)
    # columns: neck faces, never in the beam line
    assert neck_len[("C5", "PANEL")] == pytest.approx(0.50, abs=1e-3)
    assert neck_len[("C5", "OUTER")] == pytest.approx(0.30, abs=1e-3)
    assert sum(v for (c, k), v in neck_len.items() if c.startswith("K")) == pytest.approx(2.40, abs=1e-3)


def test_sides_named_by_frame():
    owners, rings, _ = villa_p()
    t = FT.trace(owners, rings)
    names = {bid: {k: v for k, v in t[bid]["pieces"].items()} for bid, _ in rings}
    p1 = [bid for bid in names if bid.startswith("P") and any(k[1] == "S3" for k in names[bid])][0]
    inner = names[p1]
    # S1a inner face (offset hi, y = 300) on P1 is 2.70 m; the S5 tee covers 0.30 of the 4.20 m run
    assert inner[("SPAN", "S1a", "B")] == pytest.approx(2700, abs=1)
    out = names["OUTER-1"]
    assert out[("SPAN", "S1a", "A")] == pytest.approx(4200, abs=1)          # outer face (offset lo, y = 0)
    assert ("SPAN", "S1a", "END") not in out and t["OUTER-1"]["max_dist"] < 1.0


def test_run_length_on_a_covered_face_refused():
    with pytest.raises(F.RefusedError, match="tee|column"):
        F.refuse_run_length("S1a", "B", 4.20, 3.90)
    assert F.refuse_run_length("S3", "B", 3.70, 3.70) == 3.70


def test_closure_refuses_double_count_and_gaps():
    p = [{"member_kind": "SPAN", "member": "S1", "face": "B", "length_m": 2.0},
         {"member_kind": "COLUMN", "member": "K1", "face": None, "length_m": 0.3}]
    assert F.check_closure("P", 2.3, p) == pytest.approx(2.3)
    with pytest.raises(F.RefusedError, match="twice or dropped"):
        F.check_closure("P", 2.6, p)
    with pytest.raises(F.RefusedError, match="listed twice"):
        F.check_closure("P", 4.3, p + [dict(p[0])])


def test_units_and_kinds_refused():
    with pytest.raises(F.RefusedError, match="unit slip"):
        F.face_row("x", "SPAN", "B", "PANEL", "FILL", 3900.0, EXT)          # mm given as m
    with pytest.raises(F.RefusedError):
        F.face_row("x", "SPAN", "B", "PANEL", "FILL", 3.9, dict(EXT, depth=950))   # depth in mm
    with pytest.raises(F.RefusedError):
        F.face_row("x", "BEAM", "B", "PANEL", "FILL", 3.9, EXT)
    with pytest.raises(F.RefusedError):
        F.face_row("x", "SPAN", "B", "SIDEWAYS", "FILL", 3.9, EXT)


def test_held_faces_never_zero():
    r = F.face_row("x", "SPAN", "B", "PANEL", "FILL", 2.0, dict(INT, depth=None, depth_range=(0.30, 0.40)))
    assert r.status == W.HELD and r.qty is None
    assert r.readings == {"length_m": 2.0, "candidate_low": pytest.approx(0.40), "candidate_high": pytest.approx(0.60)}
    for st in ("HELD", "SPLIT_LEVEL"):
        r = F.face_row("x", "SPAN", "B", "PANEL", st, 2.0, EXT)
        assert r.status == W.HELD and r.qty is None


def test_side_from_the_boundary_not_the_face_name():
    # a CONVEX arc face on the outer boundary is an outside face: plinth above ground when the soffit is at ground
    ring = {"depth": 0.95, "depth_range": None, "top": 0.95, "slab_t": SLAB, "natural_ground": 0.0}
    r = F.face_row("arc", "ARC", "convex face", "OUTER", None, 6.0, ring)
    assert r.status == W.EXCLUDED and r.qty is None
    r = F.face_row("arc", "ARC", "concave face", "PANEL", "FILL", 6.0, ring)
    assert r.status == W.DC and r.qty == pytest.approx(5.10)


def test_lift_ring_faces_owned_elsewhere():
    r = F.face_row("ring", "LIFT_RING", "face", "PANEL", "FILL", 1.2, {})
    assert r.status == W.EXCLUDED and r.member == "LIFT_PIT" and r.qty is None


def test_piece_depth_from_its_own_band_only():
    spans = [{"id": "a#1", "band": "a", **EXT}, {"id": "a#2", "band": "a", **EXT},
             {"id": "b#1", "band": "b", **INT}]
    m = F.piece_member(["a"], spans)
    assert m["depth"] == 0.95                                    # the crossing band b's 0.40 is not borrowed
    m = F.piece_member(["a", "b"], spans)
    assert m["depth"] is None and m["depth_range"] == (0.40, 0.95)
    m = F.piece_member(["c"], spans)
    assert m["depth"] is None and m["why"] == "PIECE_NO_SPAN_OF_ITS_BAND"


def test_neck_beam_zone_deduction_by_hand():
    # C5 300 x 400: S1a 0.30 + S1b 0.30 covered (D 0.95), outside 0.30 above ground over 0.75, panel 0.50 x slab 0.10
    parts = [{"kind": "SPAN", "with": "S1a", "length_m": 0.3}, {"kind": "SPAN", "with": "S1b", "length_m": 0.3},
             {"kind": "FREE", "with": "OUTER", "length_m": 0.3}, {"kind": "FREE", "with": "P2", "length_m": 0.5}]
    d, basis, why = F.neck_beam_zone_deduction("C5", parts, zone_top=TOP, slab_t=SLAB, natural_ground=NG,
                                               member_depth=lambda k, w: 0.95)
    assert why == "" and d == pytest.approx(0.57 + 0.225 + 0.05)
    d, _, why = F.neck_beam_zone_deduction("C5", parts, zone_top=TOP, slab_t=SLAB, natural_ground=NG,
                                           member_depth=lambda k, w: None if w == "S1b" else 0.95)
    assert d is None and why.startswith("DEDUCTION_HELD")
    with pytest.raises(F.RefusedError):
        F.neck_beam_zone_deduction("C5", parts, zone_top=-0.10, slab_t=SLAB, natural_ground=NG,
                                   member_depth=lambda k, w: 0.95)


def test_t263_guards_still_bind():
    with pytest.raises(W.RefusedError):
        W.underlay_face_refused("FOOTING_SIDES")             # T-219 footing side counted again
    run = {"top": TOP, "depth": 0.95, "slab_t": SLAB, "natural_ground": NG}
    with pytest.raises(W.RefusedError, match="above the buried height"):
        W.refuse_coat_height(0.95, run, {"side": "PANEL", "panel_state": "FILL"})   # coat over the slab zone
    with pytest.raises(W.RefusedError):
        W.refuse_coat_height(0.30, run, {"side": "PANEL", "panel_state": "HELD"})   # held panel face


def test_soffit_on_blinding_never_counted():
    # the trace walks the PLAN boundary only (side faces); a soffit cast on the printed blinding stays a named exclusion
    rows = W.gb_run_rows({"id": "S1a", "L": 4.2, "b": 0.3, "top": TOP, "depth": 0.95, "slab_t": SLAB,
                          "natural_ground": NG, "faces": [{"side": "OUTSIDE"}, {"side": "PANEL", "panel_state": "FILL"}]})
    soffit = [r for r in rows if r.face == "soffit"][0]
    assert soffit.status == W.EXCLUDED and soffit.qty is None and soffit.readings["face_m2"] == pytest.approx(1.26)
    with pytest.raises(F.RefusedError):
        F.face_row("S1a", "SOFFIT", "soffit", "PANEL", "FILL", 4.2, EXT)
