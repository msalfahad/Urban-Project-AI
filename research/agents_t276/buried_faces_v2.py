"""T-276: buried-concrete liquid waterproofing measured on TRACED faces (research piece, not wired; BURIED_WP_V1 + R-WP-BURIED-1.1).

Pure functions, stdlib only, no I/O, any villa. Builds on research/agents_t263/buried_wp_v1.py (T-263, MERGED c0ab564d:
R-WP-BURIED-1, the per-face height rule) and changes only WHERE a face's length comes from.

Physical element (ERS s.2.1). The ground-beam system in plan is one solid of concrete: straight band strips, curved
bands, the columns (necks) drawn on the ground-beam plan, the lift ring. Earth can stand only against the BOUNDARY of
that solid: the boundary of each slab-panel hole (fill under the slab on grade) and the outer boundary (ground outside
the building). A beam face where another beam frames into it, or a column stands against it, has concrete against it,
not earth. So the length of a coated face is the length of the boundary that the member owns, never the run's
face-to-face length on both sides (T-263 reading), and each boundary piece belongs to exactly ONE member:

- SPAN side A / B (and a span END face where a beam ends free against a panel): a beam face; buried height by
  R-WP-BURIED-1 (panel side: D - slab; outside: max(0, natural ground - soffit)), with the run's own depth.
- PIECE (a band piece in no span: a junction square, a GAP strip beside a column): a beam face of the band it lies in;
  height from that band's depth when every span of it that touches the piece has the same established depth, else HELD
  with the candidates.
- ARC (curved band): the side is the boundary it lies on (panel hole = building side, outer boundary = outside), not
  "convex" or "concave" by assumption.
- COLUMN: a NECK face (the neck runs footing top -> ground-beam top, T-205, and owns the column footprint through the
  beam depth, R-CONC-OWN-1): never in the beam line; HELD with the neck height.
- LIFT_RING: owned by the lift line (T-219 WP.LIFT_PIT, sheet system): EXCLUDED here, never twice.

Necks (T-263 reading: perimeter x neck height). Over the beam depth a neck face is in earth only where it is free on a
panel (below the slab) or outside (below the natural ground); where a beam frames into it the face is concrete against
concrete. `neck_beam_zone_deduction` gives the fixed m2 that the T-263 reading over-counts, per neck, from the traced
contacts (covered length x the covering member's depth + panel length x slab + outside length x the height above the
natural ground). The neck stays HELD (height, Q-21 C); the deduction is DRAWING-CONFIRMED only when every depth in it is.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents_t263"))
import buried_wp_v1 as W  # noqa: E402

METHOD = "BURIED_WP_V1 + R-WP-BURIED-1.1 (traced faces)"
CLOSURE_TOL_M = 0.001          # boundary pieces must sum to the boundary length within 1 mm
RUN_LENGTH_TOL_M = 0.001
OWNER_KINDS = ("SPAN", "PIECE", "ARC", "COLUMN", "LIFT_RING")
BOUNDARY_KINDS = ("PANEL", "OUTER")
RefusedError = W.RefusedError
Row = W.Row
DC, HELD, EXCLUDED = W.DC, W.HELD, W.EXCLUDED


def check_closure(boundary_id, boundary_length, pieces):
    """Every step of a boundary belongs to exactly one member: the piece lengths sum to the boundary length."""
    s = sum(float(p["length_m"]) for p in pieces)
    if abs(s - float(boundary_length)) > CLOSURE_TOL_M:
        raise RefusedError(f"{boundary_id}: pieces sum to {s:.4f} m, boundary is {float(boundary_length):.4f} m "
                           "(a face counted twice or dropped)")
    keys = [(p["member_kind"], p["member"], p.get("face")) for p in pieces]
    if len(keys) != len(set(keys)):
        raise RefusedError(f"{boundary_id}: one member face listed twice on the same boundary")
    return s


def refuse_run_length(run_id, side, run_L, traced_L):
    """The run's face-to-face length on a side whose traced earth face is shorter is refused (tee / column cover)."""
    if float(run_L) > float(traced_L) + RUN_LENGTH_TOL_M:
        raise RefusedError(f"{run_id} side {side}: run length {float(run_L):.4f} m on a face traced at "
                           f"{float(traced_L):.4f} m is refused: {float(run_L) - float(traced_L):.4f} m of that face "
                           "has a beam or a column against it (concrete, not earth)")
    return float(run_L)


def face_row(element, owner_kind, face, boundary_kind, panel_state, length, member):
    """One traced face piece -> Row. member: {depth, depth_range, top, slab_t, natural_ground} of the owning beam."""
    if owner_kind not in OWNER_KINDS:
        raise RefusedError(f"owner kind {owner_kind!r} not declared")
    if boundary_kind not in BOUNDARY_KINDS:
        raise RefusedError(f"boundary kind {boundary_kind!r} not declared")
    L = float(length)
    if L < 0:
        raise RefusedError("negative face length")
    if L > 50.0:
        raise RefusedError(f"face length {L} m: a unit slip (mm as m) is refused")
    name = f"{face} on {'panel ' + str(panel_state) if boundary_kind == 'PANEL' else 'OUTSIDE'}"
    if owner_kind == "COLUMN":
        raise RefusedError("a column face is a neck face (neck line, T-205 / T-263): never in the ground-beam line")
    if owner_kind == "LIFT_RING":
        return Row(element, "LIFT_PIT", name, "m2", None, EXCLUDED,
                   f"traced {L:.4f} m on the lift ring: owned by the p.14 lift sheet system (T-219 WP.LIFT_PIT), "
                   "never twice", {"length_m": L})
    side = "PANEL" if boundary_kind == "PANEL" else "OUTSIDE"
    h, why = W.gb_face_height(side, top=member.get("top"), depth=member.get("depth"), slab_t=member.get("slab_t"),
                              natural_ground=member.get("natural_ground"),
                              panel_state=panel_state if side == "PANEL" else None)
    if h is None:
        rd = {"length_m": L}
        rng = member.get("depth_range")
        if side == "PANEL" and rng and panel_state == "FILL":
            rd.update({"candidate_low": L * (rng[0] - member["slab_t"]), "candidate_high": L * (rng[1] - member["slab_t"])})
        return Row(element, "GROUND_BEAM", name, "m2", None, HELD, f"traced {L:.4f} m x buried height (held)", rd, why)
    if h <= W.TOL:
        return Row(element, "GROUND_BEAM", name, "m2", None, EXCLUDED,
                   f"traced {L:.4f} m; soffit {member['top'] - member['depth']:+.2f} at or above the natural ground "
                   f"{member['natural_ground']:+.2f}: no earth against it (plinth face)",
                   {"length_m": L, "face_m2": L * float(member["depth"])})
    basis = (f"traced {L:.4f} x (D {member['depth']:.2f} - slab {member['slab_t']:.2f}) = {L * h:.4f}" if side == "PANEL"
             else f"traced {L:.4f} x max(0, NG {member['natural_ground']:+.2f} - soffit "
                  f"{member['top'] - member['depth']:+.2f}) = {L * h:.4f}")
    return Row(element, "GROUND_BEAM", name, "m2", L * h, DC, basis, {"length_m": L})


def piece_member(piece_bands, touching_spans):
    """Depth of a junction / GAP piece: the spans of ITS band(s) that touch it must share one established depth.

    piece_bands: band ids the piece lies in; touching_spans: [{id, band, depth, depth_range, top, slab_t, ng}].
    Returns the member dict (depth None + depth_range when not settled)."""
    own = [s for s in touching_spans if s["band"] in piece_bands]
    if not own:
        return {"depth": None, "depth_range": None, "why": "PIECE_NO_SPAN_OF_ITS_BAND"}
    depths = {s["depth"] for s in own}
    base = {k: own[0][k] for k in ("top", "slab_t", "natural_ground")}
    if None not in depths and len(depths) == 1:
        return dict(base, depth=depths.pop(), depth_range=None)
    cands = []
    for s in own:
        if s["depth"] is not None:
            cands.append(s["depth"])
        elif s.get("depth_range"):
            cands.extend(s["depth_range"])
    return dict(base, depth=None, depth_range=(min(cands), max(cands)) if cands else None)


def neck_beam_zone_deduction(neck_id, parts, *, zone_top, slab_t, natural_ground, member_depth):
    """Fixed m2 inside 'perimeter x neck height' that has no earth against it, from the traced column contacts.

    parts: [{kind (SPAN / PIECE / ARC / COLUMN / LIFT_RING / FREE), with, length_m}]; member_depth(kind, with) -> depth
    or None. FREE on a panel: the top slab_t is against the slab; FREE outside: the part above the natural ground;
    covered by a member of depth D: D (concrete against concrete). Returns (m2 or None, basis, held_why)."""
    total, terms, held = 0.0, [], []
    for p in parts:
        L = float(p["length_m"])
        if p["kind"] == "FREE":
            if p["with"] == "OUTER":
                above = float(zone_top) - float(natural_ground)
                if above < 0:
                    raise RefusedError(f"{neck_id}: ground-beam top below the natural ground is not this case")
                total += L * above
                terms.append(f"outside {L:.4f} x {above:.2f}")
            else:
                total += L * float(slab_t)
                terms.append(f"panel {p['with']} {L:.4f} x slab {float(slab_t):.2f}")
            continue
        if p["kind"] in ("COLUMN", "LIFT_RING"):
            held.append(f"{p['kind']} {p['with']}")
            continue
        d = member_depth(p["kind"], p["with"])
        if d is None:
            held.append(f"{p['with']} depth held")
            continue
        total += L * d
        terms.append(f"{p['with']} {L:.4f} x {d:.2f}")
    basis = " + ".join(terms)
    if held:
        return None, basis, "DEDUCTION_HELD: " + "; ".join(held)
    return total, basis, ""
