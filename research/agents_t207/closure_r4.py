"""T-207: openings closure (census r4) - pure rules for any villa (research module, not wired; no engine file).

Five physical questions the r3 census and the T-201 heads left open, each answered from drawn evidence or held:

1. OPENING BETWEEN SHUTTER LEAVES (shuttered window on an elevation). The opening is the outline whose jamb-to-jamb
   width binds to the plan width within tol (and, for two or more, whose centre spacing reproduces the plan spacing).
   Shutter leaves drawn BESIDE the jambs are their own item (never the opening); a frame drawn INSIDE the outline is the
   window frame (a fabrication size, never the opening). Height = head - sill of that same outline. Twin openings whose
   outlines are identical may bind as a pair even when which-is-which is ambiguous (the value does not depend on it);
   twins whose outlines differ stay AMBIGUOUS -> HELD. A head is never taken from a neighbouring opening.
2. COUNT OF A GLAZED RUN. The count comes from the drawings: a pier / mullion needs a drawn element in the span (a
   transverse plan line, a column of the architectural overlay, or a structural column that CONTINUES above the floor
   the opening sits on). A structural member that stops below that floor (a neck struck out above the foundation in the
   column schedule) is no pier. A render showing another count is design intent: it never changes the drawn count, but
   under WORKFLOW_CONTROLS s.8 it makes the line HELD (finding DIFFERS) until the designer answers.
3. HEAD SOFFIT. The surface under the head of an opening (width x the member / wall depth) IS the head term of the reveal
   (UP-REVEAL-001: jambs + head depth x width). It is owned by the reveal line and is never a separate BOQ line; its
   length (= the width) is established even while the jambs (= the head level) are held.
4. LINTEL NEED. A lintel (spanning member at the head) is needed when the lowest established member soffit over the
   opening lies above the head by more than the lintel depth; established when the soffit's LOWER bound already clears
   the head + lintel; HELD when the head or the soffit bound is missing.
5. THRESHOLD. A threshold line exists only where a door, a floor-level change or an owner rule makes one. A change of
   finish at the same level without a rule is a finish EDGE (length known) whose item is UNKNOWN; never a threshold by
   default, never 0.

Statuses: WORKFLOW_CONTROLS s.5. Nothing here is VERIFIED (the Checker re-measures) or released.
"""
from __future__ import annotations

DC = "DRAWING-CONFIRMED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
AOA = "ASSUMED — OWNER-APPROVED"
NA = "NOT_APPLICABLE"

UNITS = {"mm": 0.001, "m": 1.0}


class ClosureError(ValueError):
    pass


def _k(units):
    if units not in UNITS:
        raise ClosureError(f"units must be one of {sorted(UNITS)}, got {units!r}")
    return UNITS[units]


def opening_between_leaves(plan_w_m, jamb_x, outline_y, units, *, leaves=None, frame=None, tol_m=0.02,
                           source=None, neighbour_of=None):
    """plan_w_m: printed / plan jamb-to-jamb width (m). jamb_x: (x_left, x_right) of the outline between the leaves;
    outline_y: (y_bottom, y_top) of that outline, both in the elevation's drawing units. leaves: [(x0, x1)] of the leaf
    outlines beside the jambs; frame: (x0, y0, x1, y1) of a frame drawn inside. neighbour_of: if the edges were read
    on ANOTHER opening (e.g. a neighbouring window), the id of that opening -> refused."""
    if neighbour_of:
        raise ClosureError(f"head / sill read on opening {neighbour_of}: a value is never taken from a neighbouring opening")
    if not source:
        raise ClosureError("a drawn value needs its source (sheet / view)")
    k = _k(units)
    if plan_w_m is None or jamb_x is None or outline_y is None:
        return {"status": HELD, "width_m": plan_w_m, "height_m": None, "why": "outline or plan width missing"}
    w_drawn = abs(jamb_x[1] - jamb_x[0]) * k
    h = round(abs(outline_y[1] - outline_y[0]) * k, 2)
    rec = {"width_drawn_m": round(w_drawn, 4), "width_m": plan_w_m, "height_m": None, "status": HELD, "why": "",
           "leaves": [], "frame": None, "source": source}
    for x0, x1 in (leaves or []):
        lw = abs(x1 - x0) * k
        inside = min(x0, x1) * k > min(jamb_x) * k - 1e-9 and max(x0, x1) * k < max(jamb_x) * k + 1e-9
        if inside:
            raise ClosureError("a leaf drawn inside the jambs covers the opening: the outline is not the opening's")
        rec["leaves"].append(round(lw, 4))
    if frame is not None:
        fw, fh = abs(frame[2] - frame[0]) * k, abs(frame[3] - frame[1]) * k
        rec["frame"] = (round(fw, 4), round(fh, 4))   # fabrication size, never the opening
    if abs(w_drawn - plan_w_m) > tol_m:
        rec["why"] = (f"outline width {w_drawn:.3f} m differs from the plan width {plan_w_m:.3f} m by more than {tol_m} m: "
                      "the drawn edges are not the opening's (a frame or a shutter box); candidates only")
        return rec
    if h <= 0:
        raise ClosureError("head not above sill")
    rec.update(status=DC, height_m=h, why="outline between the leaves binds to the plan width; height = its head - sill")
    return rec


def bind_twins(plan_centres_m, drawn, units, tol_m=0.02):
    """plan_centres_m: [(id, centre_m)] along the facade; drawn: [(x0, x1, y0, y1)] outlines. A pair (or set) binds when
    the drawn centre spacings reproduce the plan spacings within tol. If the plan order cannot be decided (mirror or the
    elevation is seen from the other side), the values transfer only when every drawn outline is identical within tol."""
    k = _k(units)
    if len(plan_centres_m) != len(drawn) or len(drawn) < 2:
        return {"status": UNKNOWN, "why": "need the same number (>= 2) of plan openings and drawn outlines"}
    pc = sorted(c for _, c in plan_centres_m)
    dc = sorted(((x0 + x1) / 2 * k) for x0, x1, _, _ in drawn)
    sp_p = [round(b - a, 4) for a, b in zip(pc, pc[1:])]
    sp_d = [round(b - a, 4) for a, b in zip(dc, dc[1:])]
    if any(abs(a - b) > tol_m for a, b in zip(sp_p, sp_d)):
        return {"status": HELD, "why": f"spacing {sp_d} does not reproduce the plan {sp_p}", "spacing_plan": sp_p,
                "spacing_drawn": sp_d}
    dims = [(abs(x1 - x0) * k, abs(y1 - y0) * k, min(y0, y1) * k) for x0, x1, y0, y1 in drawn]
    same = all(abs(a - b) <= tol_m for d in dims for a, b in zip(d, dims[0]))
    if not same and sp_p != sp_p[::-1]:
        return {"status": "BOUND", "why": "spacing reproduces the plan; order fixed by asymmetric spacing",
                "spacing_plan": sp_p, "spacing_drawn": sp_d}
    if not same:
        return {"status": "AMBIGUOUS", "why": "symmetric spacing and outlines that differ: which outline is which opening "
                                              "is not decidable -> HELD", "spacing_plan": sp_p, "spacing_drawn": sp_d}
    return {"status": "BOUND", "why": "spacing reproduces the plan; the outlines are identical, so the values do not "
                                      "depend on which is which", "spacing_plan": sp_p, "spacing_drawn": sp_d}


def glazed_run_count(plan_transverse_lines, arch_columns_in_span, structural_in_span, render_count=None):
    """plan_transverse_lines: number of drawn lines crossing the glazing symbol inside its span (mullion / pier);
    arch_columns_in_span: columns of the architectural column overlay inside the span;
    structural_in_span: [(mark, continues_above_this_floor: bool)] structural columns inside the span (plan position).
    Returns the drawn count and its status; a render count that differs makes the line HELD (s.8), count unchanged."""
    if plan_transverse_lines < 0 or arch_columns_in_span < 0:
        raise ClosureError("counts cannot be negative")
    piers = plan_transverse_lines + arch_columns_in_span
    cont = [m for m, up in structural_in_span if up]
    stop = [m for m, up in structural_in_span if not up]
    if cont and not (plan_transverse_lines or arch_columns_in_span):
        return {"count": None, "status": HELD, "candidates": [1, 1 + len(cont)],
                "why": f"structural column(s) {cont} continue through the span but the architecture draws no pier: "
                       "drawings conflict (designer)"}
    count = 1 + piers
    rec = {"count": count, "status": DC, "why": "count from the drawn span", "members_stopping_below": stop}
    if stop:
        rec["why"] += f"; {stop} stop below this floor (no pier)"
    if render_count is not None and render_count != count:
        rec.update(status=HELD, candidates=sorted({count, render_count}),
                   why=rec["why"] + f"; a render shows {render_count}: design intent DIFFERS (WORKFLOW_CONTROLS s.8) -> "
                                    "HELD until the designer answers; the drawn count is not changed by the render")
    return rec


def head_reveal(width_m, depth_m, width_status=DC, depth_status=DC, reveal_line_includes_head=True):
    """The head soffit of an opening as the head term of its reveal (UP-REVEAL-001). Returns its length (m.l) and area
    (m2) for the REVEAL line; refuses to emit it as a separate line when the reveal line already includes the head."""
    if width_m is None or depth_m is None:
        return {"head_lm": width_m, "head_m2": None, "status": HELD, "owner": "reveal line (UP-REVEAL-001 head term)"}
    st = DC if (width_status == DC and depth_status == DC) else HELD
    return {"head_lm": round(width_m, 3), "head_m2": round(width_m * depth_m, 4), "status": st,
            "owner": "reveal line (UP-REVEAL-001 head term)",
            "separate_line": False if reveal_line_includes_head else None,
            "why": "the head soffit is the reveal's head term; a separate soffit line would count the same surface twice"}


def lintel_need(head_level_m, soffit_lower_bound_m, lintel_depth_m, tol=0.005):
    """Spanning member at the head: established when the lowest possible member soffit clears head + lintel depth."""
    if head_level_m is None or soffit_lower_bound_m is None or lintel_depth_m is None:
        return {"status": HELD, "needed": None, "why": "head level or member soffit bound not established"}
    gap = round(soffit_lower_bound_m - head_level_m, 3)
    if gap <= tol:
        return {"status": HELD, "needed": None, "gap_lower_bound_m": gap,
                "why": "the member soffit may reach the head: whether the member is the lintel is not decided"}
    if gap < lintel_depth_m - tol:
        return {"status": HELD, "needed": True, "gap_lower_bound_m": gap,
                "why": "a spanning member is needed but the room for a full-depth lintel is not established"}
    return {"status": DC, "needed": True, "gap_lower_bound_m": gap,
            "why": f"wall remains above the head (>= {gap:.2f} m to the lowest member soffit): a lintel spans it"}


def threshold_at(kind, door=False, level_change=False, rule=None, finish_a=None, finish_b=None, width_m=None):
    """A threshold line exists only for a door, a level change or an owner rule; a finish change alone is an edge."""
    if door or level_change or rule:
        return {"line": "THRESHOLD", "m": width_m, "status": DC if width_m is not None else HELD,
                "why": "door" if door else ("level change" if level_change else f"owner rule {rule}")}
    if finish_a and finish_b and finish_a != finish_b:
        return {"line": "FINISH EDGE", "m": width_m, "status": UNKNOWN,
                "why": f"{finish_a} meets {finish_b} at the same level: the boundary length is drawn, the item built "
                       "there (threshold strip, edge restraint, plain joint) is not specified by any drawing or rule"}
    return {"line": None, "m": None, "status": NA, "why": "no door, no level change, no finish change: nothing to bill"}
