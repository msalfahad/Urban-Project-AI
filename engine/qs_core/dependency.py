"""What a single unanswered question actually holds up.

Blocking a whole floor because one door's host is unproved is a different error from allocating that door to the
wrong wall, but it costs the same thing: quantities that nobody can use.  Most of those quantities could not
change whatever the answer turns out to be, and saying so is the difference between a bill with two open
questions and a bill with none of it released.

So the engine follows the actual chain - opening, its candidate hosts, the wall lines those are, the thickness
subtotal each line feeds, the bill line that subtotal becomes - and blocks the nodes whose VALUE could move.  A
question about a door between two 100 mm partitions does not hold up the external walls, and the graph says so
in a form a reviewer can follow node by node.
"""

from __future__ import annotations

from engine.qs_core import geom, masonry as MA, openings as OP
from engine.qs_core.entities import HOST_ASSIGNED

NODE_OPENING = "OPENING"
NODE_WALL_LINE = "WALL_LINE"
NODE_SUBTOTAL = "THICKNESS_SUBTOTAL"
NODE_BOQ = "BOQ_LINE"

BLOCK_HOST_UNRESOLVED = "HOST_WALL_UNRESOLVED"
BLOCK_ADMISSION_UNRESOLVED = "OPENING_CANDIDATE_UNRESOLVED"
BLOCK_HEIGHT_NOT_ESTABLISHED = "OPENING_HEIGHT_NOT_ESTABLISHED"
BLOCK_WALL_HEIGHT_NOT_ESTABLISHED = "WALL_HEIGHT_NOT_ESTABLISHED"
BLOCK_BASIS_UNRESOLVED = "OPENING_BASIS_UNRESOLVED"
BLOCK_IDENTITY_UNRESOLVED = "WALL_IDENTITY_UNRESOLVED"
UNASSOCIATED_OPENING = "UNRESOLVED_OPENING_NOT_ASSOCIATED_WITH_ANY_WALL"


def _thickness_key(thickness, tolerance):
    """The same quantised family the identity stage used, so a line and its subtotal agree on what it is."""
    return MA.family_key(thickness, tolerance)


def build(register, wall_lines, basis_by_ref, identity_by_ref, wall_height_established, tolerance,
          population=None):
    """The graph, the blocked set, and the reason attached to every blocked node."""
    lines = {ln.component_ref: ln for ln in wall_lines}
    blocked = {}
    edges = []
    unassociated = []

    def block(ref, kind, reason):
        blocked.setdefault(ref, {"NODE": ref, "NODE_KIND": kind, "REASONS": []})
        if reason not in blocked[ref]["REASONS"]:
            blocked[ref]["REASONS"].append(reason)

    for o in register["REGISTER"]:
        ref, status = o["OPENING_REF"], o["HOST_ASSIGNMENT_STATUS"]
        cands = [c["COMPONENT_REF"] for c in o["HOST_CANDIDATES"]]
        for c in cands:
            edges.append({"FROM": ref, "FROM_KIND": NODE_OPENING, "TO": c, "TO_KIND": NODE_WALL_LINE,
                          "RELATION": "COULD_BE_HOSTED_BY" if status != HOST_ASSIGNED else "IS_HOSTED_BY"})
        if status != HOST_ASSIGNED:
            if cands:
                for c in cands:
                    block(c, NODE_WALL_LINE,
                          {"KIND": BLOCK_HOST_UNRESOLVED, "OPENING_REF": ref,
                           "WHY": "this wall line is one of the candidate hosts of an opening whose host is "
                                  "not proved, so its deduction could change",
                           "CANDIDATES": cands})
            else:
                # nothing intersects it; widen the search by the opening's own size before saying it is
                # associated with nothing.  The radius is the object's own extent, not a chosen distance.
                g = o["GEOMETRY"]
                rect = geom.Rect(*g)
                radius = max(rect.width, rect.height)
                near = sorted(ln.component_ref for ln in wall_lines
                              if ln.floor == o["FLOOR"] and rect.expanded(radius).overlaps(ln.bbox))
                if near:
                    for c in near:
                        block(c, NODE_WALL_LINE,
                              {"KIND": BLOCK_HOST_UNRESOLVED, "OPENING_REF": ref,
                               "WHY": "no wall line contains this opening; these lines are close enough that "
                                      "the answer could turn out to be one of them",
                               "ASSOCIATION_RADIUS_M": round(radius, 6), "CANDIDATES": near})
                        edges.append({"FROM": ref, "FROM_KIND": NODE_OPENING, "TO": c,
                                      "TO_KIND": NODE_WALL_LINE, "RELATION": "NEAR_ENOUGH_TO_BE_AFFECTED"})
                else:
                    unassociated.append({
                        "OPENING_REF": ref, "FLOOR": o["FLOOR"], "GEOMETRY": g, "AREA_M2": o["AREA_M2"],
                        "KIND": UNASSOCIATED_OPENING,
                        "WHY": "this opening has no candidate host and no wall line lies within its own "
                               "extent; nothing in the wall quantities can be shown to depend on it, so "
                               "nothing is blocked and the uncertainty is reported on its own",
                        "RISK": "if it is real, a deduction is missing from a wall this extraction did not "
                                "produce; that is a completeness question about the source, not a value "
                                "question about a wall line"})
        elif o["AREA_M2"] is None:
            block(o["HOST_COMPONENT_REF"], NODE_WALL_LINE,
                  {"KIND": BLOCK_HEIGHT_NOT_ESTABLISHED, "OPENING_REF": ref,
                   "WHY": "this line hosts an opening whose height is not established, so the area to deduct "
                          "from it is not known",
                   "HEIGHT_SOURCE": o["HEIGHT_SOURCE"]})

    # A gap whose nature the source does not state is upstream of every host question: if it turns out to be
    # an opening it will be deducted from the wall it sits in, and that wall's net area moves.  Leaving these
    # out of the graph is how a subtotal gets released over a drawing full of unexplained holes.
    for c in ((population or {}).get("POPULATION") or []):
        if c["CLASSIFICATION"] != "OPENING_CANDIDATE_UNRESOLVED":
            continue
        rect = geom.Rect(*c["GEOMETRY"])
        near = sorted(ln.component_ref for ln in wall_lines
                      if ln.floor == c["FLOOR"] and rect.expanded(tolerance).overlaps(ln.bbox))
        for ref in near:
            block(ref, NODE_WALL_LINE,
                  {"KIND": BLOCK_ADMISSION_UNRESOLVED, "CANDIDATE_REF": c["CANDIDATE_REF"],
                   "WHY": "a gap in this wall line has not been established to be an opening or not; if it "
                          "is one, this line's net area is smaller than the figure computed here",
                   "CANDIDATES": near})
            edges.append({"FROM": c["CANDIDATE_REF"], "FROM_KIND": NODE_OPENING, "TO": ref,
                          "TO_KIND": NODE_WALL_LINE, "RELATION": "UNRESOLVED_CANDIDATE_IN_THIS_LINE"})
        if not near:
            unassociated.append({
                "OPENING_REF": c["CANDIDATE_REF"], "FLOOR": c["FLOOR"], "GEOMETRY": c["GEOMETRY"],
                "AREA_M2": None, "KIND": UNASSOCIATED_OPENING,
                "WHY": "an unresolved candidate that lies in no wall line; nothing in the wall quantities "
                       "can be shown to depend on it",
                "RISK": "a completeness question about the extraction, not a value question about a line"})

    for ref, b in sorted(basis_by_ref.items()):
        if b["BASIS"] == OP.BASIS_UNRESOLVED:
            block(ref, NODE_WALL_LINE,
                  {"KIND": BLOCK_BASIS_UNRESOLVED,
                   "WHY": "the openings in this line disagree about whether its drawn material spans them, so "
                          "its gross length is not established",
                   "OPENINGS_TESTED": [t["OPENING_REF"] for t in b["OPENINGS_TESTED"]]})

    if not wall_height_established:
        for ref in lines:
            block(ref, NODE_WALL_LINE,
                  {"KIND": BLOCK_WALL_HEIGHT_NOT_ESTABLISHED,
                   "WHY": "no established source gives the height of this wall, so no area can be computed "
                          "from its length"})

    # subtotals and bill lines: a subtotal moves if any line that feeds it moves, and a line whose identity is
    # unresolved feeds it if the answer turns out to be masonry
    subtotals = {}
    for ln in wall_lines:
        ident = (identity_by_ref.get(ln.component_ref) or {}).get("IDENTITY")
        key = _thickness_key(ln.thickness, tolerance)
        s = subtotals.setdefault(key, {"THICKNESS_M": key, "LINES": [], "BILLABLE_LINES": [],
                                       "CANDIDATE_LINES": []})
        s["LINES"].append(ln.component_ref)
        if ident in MA.BILLABLE:
            s["BILLABLE_LINES"].append(ln.component_ref)
            edges.append({"FROM": ln.component_ref, "FROM_KIND": NODE_WALL_LINE, "TO": f"SUBTOTAL::{key}",
                          "TO_KIND": NODE_SUBTOTAL, "RELATION": "CONTRIBUTES_TO"})
        elif ident == MA.WALL_IDENTITY_UNRESOLVED:
            s["CANDIDATE_LINES"].append(ln.component_ref)
            edges.append({"FROM": ln.component_ref, "FROM_KIND": NODE_WALL_LINE, "TO": f"SUBTOTAL::{key}",
                          "TO_KIND": NODE_SUBTOTAL, "RELATION": "MIGHT_CONTRIBUTE_TO"})

    for key, s in sorted(subtotals.items(), key=lambda kv: (kv[0] is None, kv[0])):
        node = f"SUBTOTAL::{key}"
        for ref in s["BILLABLE_LINES"]:
            if ref in blocked:
                block(node, NODE_SUBTOTAL,
                      {"KIND": "CONTRIBUTING_LINE_BLOCKED", "WALL_LINE": ref,
                       "WHY": "a line that feeds this subtotal is blocked, so the subtotal could change",
                       "LINE_REASONS": [r["KIND"] for r in blocked[ref]["REASONS"]]})
        for ref in s["CANDIDATE_LINES"]:
            block(node, NODE_SUBTOTAL,
                  {"KIND": BLOCK_IDENTITY_UNRESOLVED, "WALL_LINE": ref,
                   "WHY": "a band of this thickness has not been established to be masonry; if it is, this "
                          "subtotal is larger than the released figure"})
        edges.append({"FROM": node, "FROM_KIND": NODE_SUBTOTAL, "TO": f"BOQ::MASONRY::{key}",
                      "TO_KIND": NODE_BOQ, "RELATION": "IS_BILLED_AS"})
        if node in blocked:
            block(f"BOQ::MASONRY::{key}", NODE_BOQ,
                  {"KIND": "SUBTOTAL_BLOCKED", "SUBTOTAL": node,
                   "WHY": "the subtotal behind this bill line is not final"})

    return {
        "NODES": {
            NODE_OPENING: sorted(o["OPENING_REF"] for o in register["REGISTER"]),
            NODE_WALL_LINE: sorted(lines),
            NODE_SUBTOTAL: [f"SUBTOTAL::{k}" for k in sorted(subtotals, key=lambda k: (k is None, k))],
            NODE_BOQ: [f"BOQ::MASONRY::{k}" for k in sorted(subtotals, key=lambda k: (k is None, k))]},
        "EDGES": sorted(edges, key=lambda e: (e["FROM_KIND"], e["FROM"], e["TO"])),
        "BLOCKED": dict(sorted(blocked.items())),
        "BLOCKED_WALL_LINES": sorted(r for r, b in blocked.items() if b["NODE_KIND"] == NODE_WALL_LINE),
        "RELEASED_WALL_LINES": sorted(r for r in lines if r not in blocked),
        "BLOCKED_SUBTOTALS": sorted(r for r, b in blocked.items() if b["NODE_KIND"] == NODE_SUBTOTAL),
        "SUBTOTALS": {str(k): v for k, v in sorted(subtotals.items(), key=lambda kv: (kv[0] is None, kv[0]))},
        "UNASSOCIATED_OPENINGS": sorted(unassociated, key=lambda u: u["OPENING_REF"]),
        "RULE": "a node is blocked when its value could change once an open question is answered, and for no "
                "other reason; blocking a node whose value cannot change hides a quantity that is finished, "
                "and releasing one whose value can change publishes a guess",
    }
