"""T-632 rules (research, unwired): the billed extent of a beam upstand (or of any strip drawn on a beam band) is the
extent the plan DRAWS for it, never the span of the band piece a section mark happens to cut; for any villa.

Physical element. An upstand is concrete above the slab top on a beam band: its cross-section is the printed section
minus the schedule b x D (UP-CONC-JOINT-001: the band itself stays with its beam line, counted once); its length is the
run over which the plan shows it. A section proves the upstand AT its cut only; the plan says how far it runs.

R-T632-1 DRAWN EXTENT GOVERNS. Plan evidence of an upstand's run (each an interval along the band axis, metres):
      HATCH        the level-change hatch drawn on the band;
      TOP_EDGE     the upstand's own edge line inside the band, drawn in the sheet's convention for elements ABOVE the
                   slab (on this drawing the HIDDEN linetype: stair treads and upstand edges are hidden, beam faces are
                   continuous); a line of a regular tread series (>= 3 parallel lines of one extent, equal pitch) is a
                   stair, not an upstand edge.
      All evidence intervals agree within TOL_M (1 mm)          -> extent MEASURED (ends = the evidence ends);
      they disagree                                              -> HELD, range [shortest, longest] (never the larger);
      no plan evidence, a printed section only                   -> HELD, range [0, band piece span] (never 0 as value).
      The section's cut point must lie inside the extent, else refused (the section is about another run).
      The section-mark span (the band piece the cut crosses) is accepted as the length only when it equals the drawn
      extent within TOL_M; when the drawn evidence runs further (or shorter), the section-mark span is refused.
R-T632-2 STRIP IDENTITY BEFORE ARITHMETIC. A strip drawn beside a band (outside its faces) is an upstand only if it is
      drawn in the above-slab convention or hatched as a level change, AND every section whose cut crosses it prints
      it. A strip drawn in the continuous (soffit / edge) convention, not hatched, and absent from a section cutting
      across it is NOT_UPSTAND: its identity is named from its own outline (e.g. the slab-edge outline turning a
      corner) and its quantity, if any, belongs to that element's line, never to the upstand.
R-T632-3 SECTION READ. Upstand w x h = the printed outline minus the schedule b x D (dimension texts govern; the scale
      is the printed base dimension over the drawn base); its plan side = the side the outline puts it on, turned into
      plan by the section's view direction (arrow tip = view direction; looking along +u, the viewer's right is -n).
      A printed outline with no part above b x D has no upstand (NOT_PRESENT), whatever its corner rounding.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

RULE_ID = "R-T632-1..3"
TOL_M = Decimal("0.001")
EVIDENCE = ("HATCH", "TOP_EDGE")
D = Decimal


class Refused(ValueError):
    """A rule of R-T632-1 .. 3 refuses the input."""


def d6(x) -> Decimal:
    return D(str(x)).quantize(D("0.000001"), rounding=ROUND_HALF_UP)


def _interval(iv):
    if not isinstance(iv, (tuple, list)) or len(iv) != 2:
        raise Refused(f"interval {iv!r} is not (t0, t1)")
    a, b = (d6(v) for v in iv)
    if a == b:
        raise Refused("zero-length evidence")
    return (min(a, b), max(a, b))


def tread_series(lines, tol=D("0.001")):
    """lines: [(handle, t0, t1, offset)] hidden lines parallel to one axis. Returns the handles that belong to a regular
    tread series (>= 3 lines of one extent at equal pitch): stair, not upstand evidence."""
    groups = {}
    for h, t0, t1, off in lines:
        a, b = sorted((d6(t0), d6(t1)))
        key = next((k for k in groups if abs(k[0] - a) <= tol and abs(k[1] - b) <= tol), (a, b))
        groups.setdefault(key, []).append((d6(off), h))
    out = set()
    for members in groups.values():
        if len(members) < 3:
            continue
        offs = sorted(members)
        steps = [offs[i + 1][0] - offs[i][0] for i in range(len(offs) - 1)]
        if all(abs(s - steps[0]) <= tol for s in steps) and steps[0] > 0:
            out.update(h for _, h in offs)
    return out


def drawn_extent(evidence):
    """evidence: [{"kind": HATCH | TOP_EDGE, "handle": str, "interval": (t0, t1)}] -> {state, t0, t1, length, ...}."""
    ev = []
    for e in evidence or ():
        if e.get("kind") not in EVIDENCE:
            raise Refused(f"evidence kind {e.get('kind')!r} is not one of {EVIDENCE}")
        ev.append((e["kind"], e["handle"], _interval(e["interval"])))
    if not ev:
        return {"state": "NO_PLAN_EVIDENCE"}
    los = [iv[0] for _, _, iv in ev]
    his = [iv[1] for _, _, iv in ev]
    if max(los) - min(los) <= TOL_M and max(his) - min(his) <= TOL_M:
        t0, t1 = min(los), max(his)
        return {"state": "MEASURED", "t0": t0, "t1": t1, "length_m": d6(t1 - t0),
                "evidence": [f"{k} {h}" for k, h, _ in ev]}
    lens = [iv[1] - iv[0] for _, _, iv in ev]
    return {"state": "CONFLICT", "range_m": (d6(min(lens)), d6(max(lens))), "evidence": [f"{k} {h}" for k, h, _ in ev]}


def upstand_quantity(w_m, h_m, extent, *, cut_t=None, section_span=None, piece_span_m=None):
    """R-T632-1: the upstand volume from the drawn extent. w_m, h_m: printed upstand section (m); extent: drawn_extent();
    cut_t: the section cut position on the band axis (None when no section is printed); section_span: (t0, t1) of the
    band piece the cut crosses (the section-mark span, offered as an alternative basis); piece_span_m: that piece's
    length for the no-evidence range. Returns {state MEASURED / HELD, length_m | range_m, volume_m3 | range_m3, basis}."""
    w, h = d6(w_m), d6(h_m)
    if w <= 0 or h <= 0:
        raise Refused("upstand section must be printed and positive (missing is HELD, never 0)")
    area = d6(w * h)
    st = extent.get("state")
    if st == "MEASURED":
        if cut_t is not None and not (extent["t0"] - TOL_M <= d6(cut_t) <= extent["t1"] + TOL_M):
            raise Refused("the section cut lies outside the drawn extent: the section is about another run")
        basis = "DRAWN_EXTENT"
        if section_span is not None:
            s0, s1 = _interval(section_span)
            if abs(s0 - extent["t0"]) > TOL_M or abs(s1 - extent["t1"]) > TOL_M:
                basis = "DRAWN_EXTENT (section-mark span refused: " \
                        f"{d6(s1 - s0)} m vs drawn {extent['length_m']} m)"
            else:
                basis = "DRAWN_EXTENT (= section-mark span)"
        return {"state": "MEASURED", "length_m": extent["length_m"], "area_m2": area,
                "volume_m3": d6(area * extent["length_m"]), "basis": basis}
    if st == "CONFLICT":
        lo, hi = extent["range_m"]
        return {"state": "HELD", "range_m": (lo, hi), "area_m2": area, "range_m3": (d6(area * lo), d6(area * hi)),
                "basis": "plan evidence disagrees; range, never the larger"}
    if st == "NO_PLAN_EVIDENCE":
        if piece_span_m is None:
            raise Refused("no plan evidence and no band piece: nothing bounds the run")
        p = d6(piece_span_m)
        return {"state": "HELD", "range_m": (D("0.000000"), p), "area_m2": area, "range_m3": (D("0.000000"),
                d6(area * p)), "basis": "section only: the run is not drawn"}
    raise Refused(f"extent state {st!r}")


def section_take_upstand(outline_cm, b_m, depth_m):
    """R-T632-3: outline_cm = [(x, y)] of the printed section in centimetres (base at y = 0, already scaled by the
    printed dimensions). Returns NOT_PRESENT or {w_m, h_m, side ('LEFT' / 'RIGHT' of the section)}; refuses a base
    that is not the schedule b."""
    xs = [D(str(x)) for x, _ in outline_cm]
    ys = [D(str(y)) for _, y in outline_cm]
    base = (max(xs) - min(xs)) / 100
    if abs(base - d6(b_m)) > D("0.005"):
        raise Refused(f"section base {base} m is not the schedule b {b_m} m")
    top = max(ys) / 100
    dpt = d6(depth_m)
    if top <= dpt + TOL_M:
        return {"state": "NOT_PRESENT", "h_m": d6(top)}
    above = [x for x, y in zip(xs, ys) if y / 100 > dpt + TOL_M]
    w = (max(above) - min(above)) / 100
    mid = (max(xs) + min(xs)) / 2
    side = "RIGHT" if min(above) >= mid else "LEFT" if max(above) <= mid else "MIDDLE"
    return {"state": "PRESENT", "w_m": d6(w), "h_m": d6(top - dpt), "side": side}


def plan_side(section_side, view_u, band_n):
    """R-T632-3: the plan side (+n / -n of the band) of a section's LEFT / RIGHT part. view_u: the unit view direction
    on plan (arrow tip = view direction); band_n: the band's unit normal. Looking along u, right hand = u rotated -90."""
    rx, ry = view_u[1], -view_u[0]
    dot = rx * band_n[0] + ry * band_n[1]
    if abs(dot) < 0.5:
        raise Refused("the view direction is not across the band")
    right = "+n" if dot > 0 else "-n"
    if section_side == "RIGHT":
        return right
    if section_side == "LEFT":
        return "-n" if right == "+n" else "+n"
    raise Refused(f"section side {section_side!r}")


def strip_identity(*, above_convention, hatched, crossed_by_section, printed_on_section, outline_continues):
    """R-T632-2 for a strip drawn outside a band's faces."""
    if (above_convention or hatched) and (not crossed_by_section or printed_on_section):
        return {"class": "UPSTAND"}
    if not above_convention and not hatched and crossed_by_section and not printed_on_section:
        return {"class": "NOT_UPSTAND", "identity": "slab-edge outline" if outline_continues else "unnamed strip"}
    return {"class": "UNRESOLVED", "why": "convention and section disagree"}
