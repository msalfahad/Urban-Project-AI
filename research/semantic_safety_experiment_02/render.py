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


def place_tags(anchor_candidates, size):
    """Where each tag goes, or why it cannot go anywhere.

    `anchor_candidates` maps label -> a list of points ON THAT MEMBER, in
    declared order. A leader may start anywhere along the member it names,
    so a dense cluster is solved by moving the foot of the leader rather
    than by relaxing the clearance test. Positions are tried anchor by
    anchor, radius by radius, direction by direction, and the first that
    passes every test is taken.
    """
    w, h = size
    hw, hh = P.TAG_BOX_W_PX / 2.0, P.TAG_BOX_H_PX / 2.0
    m = P.TAG_MARGIN_PX
    best = {lab: pts[0] for lab, pts in anchor_candidates.items() if pts}
    placed, failed = {}, {}

    for lab in sorted(anchor_candidates):
        cands = anchor_candidates[lab]
        if not cands:
            failed[lab] = "A_TAGGED_MEMBER_IS_NOT_INSIDE_THE_CROP"
            continue
        others = [v for k, v in best.items() if k != lab]
        got = None
        for ax, ay in cands:
            for r in P.TAG_RADII_PX:
                for deg in P.TAG_DIRECTIONS_DEG:
                    cx = ax + r * math.cos(math.radians(deg))
                    cy = ay + r * math.sin(math.radians(deg))
                    box = (cx - hw, cy - hh, cx + hw, cy + hh)
                    if box[0] < m or box[1] < m or box[2] > w - m \
                            or box[3] > h - m:
                        continue
                    if any(_overlap(_inflate(box, P.TAG_MIN_GAP_PX),
                                    o["box"]) for o in placed.values()):
                        continue
                    if any(_seg_box((ax, ay), (cx, cy), o["box"])
                           for o in placed.values()):
                        continue
                    if any(_point_seg_dist(o, (ax, ay), (cx, cy))
                           <= P.LEADER_CLEAR_PX for o in others):
                        continue
                    got = {"box": box, "centre": (cx, cy),
                           "anchor": (ax, ay), "radius_px": r,
                           "direction_deg": deg}
                    break
                if got:
                    break
            if got:
                break
        if got is None:
            failed[lab] = "NO_POSITION_PASSES_EVERY_TEST"
        else:
            placed[lab] = got
            best[lab] = got["anchor"]

    # every tag is re-checked against every OTHER tag's final position,
    # not only the ones placed before it, because a later box or a moved
    # anchor can spoil an earlier leader
    for lab, o in placed.items():
        rest = [(k, v) for k, v in placed.items() if k != lab]
        if any(_overlap(_inflate(o["box"], P.TAG_MIN_GAP_PX), q["box"])
               for _, q in rest):
            failed[lab] = "TWO_TAG_BOXES_OVERLAP"
        elif any(_seg_box(o["anchor"], o["centre"], q["box"])
                 for _, q in rest):
            failed[lab] = "A_LEADER_CROSSES_ANOTHER_TAG_BOX"
        elif any(_point_seg_dist(q["anchor"], o["anchor"], o["centre"])
                 <= P.LEADER_CLEAR_PX for _, q in rest):
            failed[lab] = "A_LEADER_PASSES_TOO_CLOSE_TO_ANOTHER_ANCHOR"
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
