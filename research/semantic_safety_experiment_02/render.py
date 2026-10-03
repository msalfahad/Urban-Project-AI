"""Marked crops whose tags are proved legible by machine before a reader sees
them.

In the frozen experiment every tag was printed at the middle of its own
line, so collinear members - the parallel lines of a window run, the sides
of a poche block - buried each other's labels and 39 members were
unreadable at every scale. The readers answered UNRESOLVED, correctly, and
the measurement learned nothing about the readers.

Here each tag sits in a box joined to its member by a leader line, placed
by trying declared positions in a declared order, and a feature whose tags
cannot all be placed cleanly is not admitted to the sample at all.
"""

from __future__ import annotations

import math

from research.semantic_safety_experiment_02 import protocol as P

PRIMARY_RGB = (220, 20, 60)
TAG_FILL = (255, 255, 255)
TAG_EDGE = (140, 0, 40)
LEADER_RGB = (140, 0, 40)


def _seg_box(p, q, box) -> bool:
    """Does the segment p-q meet the axis-aligned box?"""
    x0, y0, x1, y1 = box
    if max(p[0], q[0]) < x0 or min(p[0], q[0]) > x1:
        return False
    if max(p[1], q[1]) < y0 or min(p[1], q[1]) > y1:
        return False
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        if _cross(p, q, a, b):
            return True
    return (x0 <= p[0] <= x1 and y0 <= p[1] <= y1)


def _cross(p1, p2, p3, p4) -> bool:
    def side(a, b, c):
        return ((b[0] - a[0]) * (c[1] - a[1])
                - (b[1] - a[1]) * (c[0] - a[0]))
    d1, d2 = side(p3, p4, p1), side(p3, p4, p2)
    d3, d4 = side(p1, p2, p3), side(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _point_seg_dist(pt, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    if n <= 0:
        return math.dist(pt, a)
    t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / n))
    return math.dist(pt, (ax + t * dx, ay + t * dy))


def _inflate(box, k):
    return (box[0] - k, box[1] - k, box[2] + k, box[3] + k)


def _overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def anchor_candidates(pts, size):
    """Feet for a leader, spread along the member BY ARC LENGTH.

    The superseded placer picked among the vertices the geometry happened
    to return, so a straight SEGMENT - two vertices - offered only its two
    ends, which on a wall run is exactly where every other member ends
    too. Interpolating by length gives a straight member real interior
    feet. It relaxes no placement test; it only widens the search.
    """
    if len(pts) < 2:
        return []
    w, h = size
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg)
    if total <= 0:
        return []
    out, seen = [], set()
    for frac in P.TAG_ANCHOR_FRACTIONS:
        t, acc, pt = frac * total, 0.0, pts[-1]
        for i, L in enumerate(seg):
            if acc + L >= t or i == len(seg) - 1:
                u = 0.0 if L <= 0 else max(0.0, min(1.0, (t - acc) / L))
                pt = (pts[i][0] + u * (pts[i + 1][0] - pts[i][0]),
                      pts[i][1] + u * (pts[i + 1][1] - pts[i][1]))
                break
            acc += L
        key = (round(pt[0], 1), round(pt[1], 1))
        if key in seen or not (0 <= pt[0] <= w and 0 <= pt[1] <= h):
            continue
        seen.add(key)
        out.append(pt)
    return out


def _incompatible(a, b):
    """Why two final tag positions cannot both stand, or None.

    This is the WHOLE pairwise gate, stated once. The search below and the
    verification pass after it both call this function, so a placement can
    no longer pass the search and then fail the re-check.
    """
    if _overlap(_inflate(a["box"], P.TAG_MIN_GAP_PX), b["box"]):
        return "TWO_TAG_BOXES_OVERLAP"
    if _seg_box(a["anchor"], a["centre"], b["box"]) \
            or _seg_box(b["anchor"], b["centre"], a["box"]):
        return "A_LEADER_CROSSES_ANOTHER_TAG_BOX"
    if _point_seg_dist(b["anchor"], a["anchor"], a["centre"]) \
            <= P.LEADER_CLEAR_PX \
            or _point_seg_dist(a["anchor"], b["anchor"], b["centre"]) \
            <= P.LEADER_CLEAR_PX:
        return "A_LEADER_PASSES_TOO_CLOSE_TO_ANOTHER_ANCHOR"
    return None


def _positions(cands, size):
    """Every position this member could take, in the declared order:
    anchor by anchor, then radius, then direction - unchanged."""
    w, h = size
    hw, hh = P.TAG_BOX_W_PX / 2.0, P.TAG_BOX_H_PX / 2.0
    m = P.TAG_MARGIN_PX
    out = []
    for ax, ay in cands:
        for r in P.TAG_RADII_PX:
            for deg in P.TAG_DIRECTIONS_DEG:
                cx = ax + r * math.cos(math.radians(deg))
                cy = ay + r * math.sin(math.radians(deg))
                box = (cx - hw, cy - hh, cx + hw, cy + hh)
                if box[0] < m or box[1] < m or box[2] > w - m \
                        or box[3] > h - m:
                    continue
                out.append({"box": box, "centre": (cx, cy),
                            "anchor": (ax, ay), "radius_px": r,
                            "direction_deg": deg})
    return out


def place_tags(anchor_candidates, size):
    """Where each tag goes, or why it cannot go anywhere.

    `anchor_candidates` maps label -> feet ON THAT MEMBER, in declared
    order. A leader may start anywhere along the member it names, so a
    dense cluster is solved by moving the foot of the leader rather than
    by relaxing the clearance test.

    The superseded placer walked the labels once, in order, and never went
    back, so a member whose good positions an EARLIER label had taken was
    reported unplaceable when a different assignment would have tagged
    them both. Every test below is the same test it applied; the search
    is what changed. Positions are still tried anchor by anchor, then
    radius, then direction, and labels still in sorted order, so wherever
    the old placer succeeded this one returns the same answer - it only
    keeps looking where the old one gave up.

    Search order is: first try to tag EVERY member; only if that is
    impossible allow one member to go untagged, then two, and so on. The
    number of untagged members is therefore the smallest the declared
    tests permit, not an artefact of the order the labels happen to be in.
    """
    labs = sorted(anchor_candidates)
    failed, pos = {}, {}
    for lab in labs:
        cands = anchor_candidates[lab]
        if not cands:
            failed[lab] = "A_TAGGED_MEMBER_IS_NOT_INSIDE_THE_CROP"
            continue
        p = _positions(cands, size)
        if not p:
            failed[lab] = "NO_POSITION_PASSES_EVERY_TEST"
            continue
        pos[lab] = p

    order = [l for l in labs if l in pos]
    chosen, skipped, budget = {}, [], [0]

    def rec(i, skips_left):
        if i == len(order):
            return True
        lab = order[i]
        for cand in pos[lab]:
            if budget[0] <= 0:
                return False
            budget[0] -= 1
            if any(_incompatible(cand, chosen[o]) for o in chosen):
                continue
            chosen[lab] = cand
            if rec(i + 1, skips_left):
                return True
            del chosen[lab]
        if skips_left > 0:
            skipped.append(lab)
            if rec(i + 1, skips_left - 1):
                return True
            skipped.pop()
        return False

    solved = False
    for k in list(range(0, min(len(order), P.TAG_SEARCH_MAX_SKIPS) + 1)) \
            + [len(order)]:
        chosen.clear()
        del skipped[:]
        budget[0] = P.TAG_SEARCH_NODE_BUDGET
        if rec(0, k):
            solved = True
            break
    if not solved:
        # the budget ran out before any assignment closed; nothing is
        # claimed legible that was not proved legible
        chosen.clear()
        del skipped[:]
        skipped.extend(order)

    placed = dict(chosen)
    for lab in skipped:
        failed[lab] = "NO_POSITION_PASSES_EVERY_TEST"

    # the search guarantees this, so the pass is a verification, not a
    # repair: it must find nothing, and it is kept because a claim that
    # a reader can read a tag is the one claim this apparatus must not
    # make wrongly
    for lab, o in placed.items():
        for other, q in placed.items():
            if other == lab:
                continue
            why = _incompatible(o, q)
            if why:
                failed[lab] = why
                break
    return placed, failed


def draw(img, members_px, placed, failed):
    """Draw the member geometry, the leaders and the tag boxes."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for lab, pts in members_px.items():
        if len(pts) >= 2:
            d.line(pts, fill=PRIMARY_RGB, width=3)
    for lab, o in sorted(placed.items()):
        if lab in failed:
            continue
        d.line([o["anchor"], o["centre"]], fill=LEADER_RGB, width=1)
        d.rectangle(o["box"], fill=TAG_FILL, outline=TAG_EDGE, width=1)
        d.text((o["box"][0] + 5, o["box"][1] + 4), lab, fill=TAG_EDGE)
    return img
