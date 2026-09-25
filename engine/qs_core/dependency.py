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
BLOCK_MATERIAL_UNRESOLVED = "WALL_MATERIAL_NOT_ESTABLISHED"
BLOCK_GEOMETRY_UNRESOLVED = "WALL_GEOMETRY_NOT_ESTABLISHED"
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
        cands = sorted({ref for c in o["HOST_CANDIDATES"]
                        for ref in (c.get("WALL_LINES") or
                                    ([c["COMPONENT_REF"]] if c.get("COMPONENT_REF") else []))})
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
                # an opening whose host is unresolved may have no footprint at all; its own span about its
                # centre is the extent within which a wall could still turn out to be the answer
                if o.get("GEOMETRY"):
                    rect = geom.Rect(*o["GEOMETRY"])
                else:
                    cx, cy = o["CENTRE"]
                    half = (o.get("SPAN_M") or tolerance) / 2.0
                    rect = geom.Rect(cx - half, cy - half, cx + half, cy + half)
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
                        "OPENING_REF": ref, "FLOOR": o["FLOOR"], "GEOMETRY": o.get("GEOMETRY"),
                        "CENTRE": o.get("CENTRE"), "SPAN_M": o.get("SPAN_M"), "AREA_M2": o["AREA_M2"],
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
        # an unresolved candidate has no depth and so no footprint; its own span, about its centre, is the
        # extent within which a wall could turn out to be affected
        if c.get("GEOMETRY"):
            rect = geom.Rect(*c["GEOMETRY"])
        else:
            cx, cy = c["CENTRE"]
            half = c["SPAN_M"] / 2.0
            rect = (geom.Rect(cx - half, cy - tolerance, cx + half, cy + tolerance)
                    if c["AXIS"] != geom.AXIS_Y else
                    geom.Rect(cx - tolerance, cy - half, cx + tolerance, cy + half))
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

    # a line whose own identity is open is held up by that, and the graph has to say so: a row reported as
    # blocked and a line reported as non-blocked are the same line, and only one of them can be true
    for ref in lines:
        for reason in MA.identity_blocks(identity_by_ref.get(ref) or {}):
            block(ref, NODE_WALL_LINE, dict(reason, WALL_LINE=ref))

    # subtotals and bill lines: a subtotal moves if any line that feeds it moves, and a line whose identity is
    # unresolved feeds it if the answer turns out to be masonry
    subtotals = {}
    for ln in wall_lines:
        rec = identity_by_ref.get(ln.component_ref) or {}
        geometry = rec.get("GEOMETRY_IDENTITY")
        material = rec.get("MATERIAL_IDENTITY")
        billable = rec.get("BILLABLE_AS_MASONRY")
        key = _thickness_key(ln.thickness, tolerance)
        s = subtotals.setdefault(key, {"THICKNESS_M": key, "LINES": [], "BILLABLE_LINES": [],
                                       "CANDIDATE_LINES": []})
        s["LINES"].append(ln.component_ref)
        if billable:
            s["BILLABLE_LINES"].append(ln.component_ref)
            edges.append({"FROM": ln.component_ref, "FROM_KIND": NODE_WALL_LINE, "TO": f"SUBTOTAL::{key}",
                          "TO_KIND": NODE_SUBTOTAL, "RELATION": "CONTRIBUTES_TO"})
        elif geometry != MA.NON_WALL_ARTEFACT:
            # wall geometry whose material is unstated, or a band not yet established to be a wall: if the
            # answer turns out to be masonry this subtotal is larger than anything released here
            s["CANDIDATE_LINES"].append(ln.component_ref)
            s.setdefault("CANDIDATE_REASONS", {})[ln.component_ref] = (
                "WALL_MATERIAL_NOT_ESTABLISHED" if geometry == MA.CONFIRMED_WALL_GEOMETRY
                else "WALL_GEOMETRY_NOT_ESTABLISHED")
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
            kind = (s.get("CANDIDATE_REASONS", {}) or {}).get(ref, BLOCK_IDENTITY_UNRESOLVED)
            block(node, NODE_SUBTOTAL,
                  {"KIND": kind, "WALL_LINE": ref,
                   "WHY": ("no applicable source states what this band is made of; if it is masonry, this "
                           "subtotal is larger than any figure released here"
                           if kind == "WALL_MATERIAL_NOT_ESTABLISHED" else
                           "this band is not established to be a wall; if it is, this subtotal is larger "
                           "than any figure released here")})
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
        # NOT "released": a line can be outside the blocked set because it is excluded from the trade
        # altogether.  An excluded row is not a released quantity, and a field that conflates the two reads
        # as more finished work than exists.
        "NON_BLOCKED_WALL_LINES": sorted(r for r in lines if r not in blocked),
        "NON_BLOCKED_MEANS": "not held up by an open question; it may still be excluded from the trade",
        "BLOCKED_SUBTOTALS": sorted(r for r, b in blocked.items() if b["NODE_KIND"] == NODE_SUBTOTAL),
        "SUBTOTALS": {str(k): v for k, v in sorted(subtotals.items(), key=lambda kv: (kv[0] is None, kv[0]))},
        "UNASSOCIATED_OPENINGS": sorted(unassociated, key=lambda u: u["OPENING_REF"]),
        "RULE": "a node is blocked when its value could change once an open question is answered, and for no "
                "other reason; blocking a node whose value cannot change hides a quantity that is finished, "
                "and releasing one whose value can change publishes a guess",
    }


# ------------------------------------------------------------------ blocker sets
#
# "Affects", "removes a blocker" and "releases" are three different statements, and R6's report used the third
# where only the first was true: four material questions were called the whole bottleneck, when many of the
# rows they touch are also waiting on an unresolved host, an unresolved height or an unsettled basis.  A
# question that removes one of three blockers releases nothing.  These are the definitions everything
# downstream - including every sentence of prose - is generated from.

AFFECTS = "the answer participates in determining this node"
REMOVES_ONE = "answering this removes one of the blockers on this node"
RELEASES = "answering this alone makes this node publishable under the current state"

NODE_BLOCKED = "BLOCKED"
NODE_PUBLISHABLE = "PUBLISHABLE_UNDER_THE_CURRENT_STATE"
NODE_EXCLUDED = "EXCLUDED_FROM_THE_TRADE"


def blocker_sets(graph, questions, wall_rows=()):
    """Per node: which unique facts it waits on, and - separately - which single answers would free it.

    Set-valued and idempotent by construction: building this twice from the same graph gives the same object,
    and an edge recorded from two construction paths counts once.
    """
    by_node, downstream = {}, {}
    for i in questions.get("DEPENDENCY_IMPACTS", []):
        by_node.setdefault(str(i["NODE"]), set()).add(i["ROOT_QUESTION_ID"])
    for e in graph.get("EDGES", []):
        if e["FROM_KIND"] in (NODE_WALL_LINE, NODE_SUBTOTAL):
            downstream.setdefault(str(e["FROM"]), set()).add(str(e["TO"]))

    excluded = {r["COMPONENT_REF"] for r in wall_rows or () if r.get("STATUS") == "EXCLUDED_NOT_MASONRY"}
    kind_of = {}
    for kind, refs in (graph.get("NODES") or {}).items():
        for ref in refs:
            kind_of[str(ref)] = kind

    nodes = {}
    for node in sorted(set(by_node) | set(kind_of)):
        blockers = sorted(by_node.get(node, set()))
        status = (NODE_EXCLUDED if node in excluded else
                  NODE_BLOCKED if blockers else NODE_PUBLISHABLE)
        nodes[node] = {
            "NODE": node,
            "NODE_KIND": kind_of.get(node, "UNKNOWN"),
            "NODE_STATUS": status,
            "BLOCKER_IDS": blockers,
            "BLOCKER_COUNT": len(blockers),
            "DIRECTLY_AFFECTED_BY": blockers,
            "ANSWER_ALONE_RELEASES_NODE": blockers[0] if len(blockers) == 1 else None,
            "REMAINING_BLOCKERS_IF_ANSWERED": {q: sorted(set(blockers) - {q}) for q in blockers},
            "DOWNSTREAM": sorted(downstream.get(node, set())),
        }

    per_question = {}
    for q in questions.get("ROOT_QUESTIONS", []):
        qid = q["ROOT_QUESTION_ID"]
        affected = sorted(n for n, rec in nodes.items() if qid in rec["BLOCKER_IDS"])
        releases = sorted(n for n in affected if nodes[n]["ANSWER_ALONE_RELEASES_NODE"] == qid)
        per_question[qid] = {
            "ROOT_QUESTION_ID": qid,
            "KIND": q["KIND"],
            "AFFECTS_NODES": affected,
            "AFFECTS_NODE_COUNT": len(affected),
            "RELEASES_NODES": releases,
            "RELEASES_NODE_COUNT": len(releases),
            "REMOVES_A_BLOCKER_BUT_LEAVES_OTHERS": sorted(set(affected) - set(releases)),
            "RELEASES_WALL_LINES": [n for n in releases if nodes[n]["NODE_KIND"] == NODE_WALL_LINE],
            "RELEASES_SUBTOTALS": [n for n in releases if nodes[n]["NODE_KIND"] == NODE_SUBTOTAL],
        }

    return {
        "DEFINITIONS": {"AFFECTS": AFFECTS, "REMOVES_ONE_BLOCKER": REMOVES_ONE, "RELEASES": RELEASES},
        "NODES": nodes,
        "BY_ROOT_QUESTION": dict(sorted(per_question.items())),
        "BLOCKED_NODE_COUNT": sum(1 for r in nodes.values() if r["NODE_STATUS"] == NODE_BLOCKED),
        "NODES_RELEASED_BY_ONE_ANSWER": sum(1 for r in nodes.values()
                                            if r["ANSWER_ALONE_RELEASES_NODE"] is not None),
        "NODES_WITH_SEVERAL_BLOCKERS": sum(1 for r in nodes.values() if r["BLOCKER_COUNT"] > 1),
        "RULE": "a root question may be said to RELEASE a node only when it is that node's only remaining "
                "blocker.  Anything else removes one blocker and leaves the rest, and must be reported that "
                "way, whatever the headline would prefer",
    }


def simulate(blockers, answered):
    """What would actually be released if this set of questions were answered, and what would still not be."""
    answered = set(answered or ())
    released, still = [], []
    for node, rec in sorted(blockers["NODES"].items()):
        if rec["NODE_STATUS"] != NODE_BLOCKED:
            continue
        remaining = sorted(set(rec["BLOCKER_IDS"]) - answered)
        (released if not remaining else still).append(
            {"NODE": node, "NODE_KIND": rec["NODE_KIND"], "REMAINING_BLOCKERS": remaining})
    return {
        "ANSWERED": sorted(answered),
        "RELEASED_NODES": released,
        "RELEASED_NODE_COUNT": len(released),
        "STILL_BLOCKED": still,
        "STILL_BLOCKED_COUNT": len(still),
        "RULE": "this is the only statement about what an answer is worth that may be published; a count of "
                "affected nodes is not a count of released ones",
    }
