"""Room names for the Al Rashed plans, taken from the issued PDF and placed in DWG coordinates.

The DWG's room labels are dynamic blocks: every instance carries the whole room-name library and shows one entry
through a visibility state the decode does not resolve, so the name cannot be read from the DWG.  The PDF is the
plot that was issued and shows exactly one name per label.

So the names come from the PDF and the geometry from the DWG, joined by a transform fitted on the one thing both
files state identically: the dimension values.  A value that appears exactly once on the page and exactly once in
the window is an unambiguous pair of points, and three such pairs fix a similarity transform.  The fit is then
checked against every pair it did not need.
"""

from __future__ import annotations

import collections
import math
import re

import pymupdf

from research.qs_wall_treatment_01.pa09.alrashed import geometry as G

PDF = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/507baa5b-16-11-2025.pdf"
PAGE_OF = {"BASEMENT": 0, "GROUND": 1, "FIRST": 2}
FIT_TOL_M = 0.35          # a pair further than this from the fitted transform is an outlier, not a witness
MIN_INLIERS = 8

ROOM_WORDS = ("BED ROOM", "M.BED ROOM", "BATH", "WASH", "DRESS", "KITCHEN", "HALL", "BALCONY", "ROOF",
              "DEWANIYA", "DRIVER", "PANTRY", "STORE", "MUGALLAT", "CAR PARKING", "MECH.ROOM", "HEATERS",
              "W.C", "MAID", "LAUNDRY", "TOILET", "LIVING", "SALOON", "DINNING", "CORRIDOR", "TERRACE",
              "CLOSET", "LOBBY", "PRAYER", "ELEC.ROOM", "GUEST ROOM", "SITTING")

WET = ("BATH", "WASH", "W.C", "TOILET", "KITCHEN", "PANTRY", "LAUNDRY")
EXTERNAL = ("ROOF", "BALCONY", "TERRACE", "CAR PARKING", "OPEN TO SKY")


def page_items(page_index):
    """Every word on the page with its centre, in page coordinates with y turned upward.

    A PDF page counts y downward and a drawing counts it upward, so the map between them is a reflection.  A
    similarity transform with a positive scale cannot express one - it would come back as a meaningless rotation -
    so the flip is applied here, once, and the fit that follows is an honest rotation and scale.
    """
    pg = pymupdf.open(PDF)[page_index]
    out = []
    for w in pg.get_text("words"):
        t = w[4].strip()
        if t:
            out.append((t, (w[0] + w[2]) / 2, -(w[1] + w[3]) / 2))
    return out


def page_labels(page_index):
    """Room names on the page, with multi-word names rejoined from their parts.

    The plans are turned through 90 degrees on the sheet, so a two-word name is stacked - its words share an x and
    differ in y rather than the other way about.  Parts of one name are therefore taken as words that line up on
    EITHER axis, which reads a rotated sheet and an upright one the same way.
    """
    items = page_items(page_index)
    lab = []
    used = set()
    for i, (t, x, y) in enumerate(items):
        if i in used:
            continue
        for n in (3, 2, 1):
            parts = items[i:i + n]
            if len(parts) < n:
                continue
            aligned = (all(abs(p[2] - y) <= 3 for p in parts) or all(abs(p[1] - x) <= 3 for p in parts))
            if not aligned:
                continue
            name = " ".join(p[0] for p in parts).upper()
            if name in ROOM_WORDS:
                lab.append((name, sum(p[1] for p in parts) / n, sum(p[2] for p in parts) / n))
                used.update(range(i, i + n))
                break
    return lab


def page_paths(page_index):
    """Every point the page draws, with y turned upward like page_items, so one transform serves both."""
    import re as _re
    import pypdf
    c = pypdf.PdfReader(PDF).pages[page_index].get_contents().get_data().decode("latin-1")
    return [(float(m.group(1)), -float(m.group(2)))
            for m in _re.finditer(r"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+[ml]\b", c)]


def drawn_points(floor, ents):
    """The plotted geometry of one floor, in drawing coordinates."""
    tr = transform_for(floor, ents)
    if not tr or not tr["ESTABLISHED"]:
        return []
    return [apply(tr, x, y) for x, y in page_paths(PAGE_OF[floor])]


def dwg_dims(ents, window):
    x0, x1, y0, y1 = window
    out = []
    for o in ents:
        if o["entity"] not in ("DIMENSION_LINEAR", "DIMENSION_ALIGNED"):
            continue
        p = o.get("text_midpt") or o.get("def_pt")
        m = o.get("act_measurement")
        if p and m and x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
            out.append((round(m), p[0], p[1]))
    return out


def _fit(pairs):
    """Least-squares similarity transform (uniform scale, rotation, translation) from page to drawing."""
    n = len(pairs)
    sx = sum(p[0] for p, _ in pairs) / n; sy = sum(p[1] for p, _ in pairs) / n
    tx = sum(q[0] for _, q in pairs) / n; ty = sum(q[1] for _, q in pairs) / n
    num_c = num_s = den = 0.0
    for (px, py), (qx, qy) in pairs:
        ax, ay = px - sx, py - sy
        bx, by = qx - tx, qy - ty
        num_c += ax * bx + ay * by
        num_s += ax * by - ay * bx
        den += ax * ax + ay * ay
    if den == 0:
        return None
    a, b = num_c / den, num_s / den          # a = s cos, b = s sin
    return {"A": a, "B": b, "SX": sx, "SY": sy, "TX": tx, "TY": ty,
            "SCALE": math.hypot(a, b), "ROT_DEG": round(math.degrees(math.atan2(b, a)), 3)}


def apply(tr, x, y):
    ax, ay = x - tr["SX"], y - tr["SY"]
    return (tr["A"] * ax - tr["B"] * ay + tr["TX"], tr["B"] * ax + tr["A"] * ay + tr["TY"])


def transform_for(floor, ents):
    """Fit page -> drawing on unique dimension values, then report how well it holds on every pair."""
    win = G.WINDOWS[floor]
    dd = dwg_dims(ents, win)
    pw = [(int(t), x, y) for t, x, y in page_items(PAGE_OF[floor]) if re.fullmatch(r"\d{2,4}", t)]
    dc = collections.Counter(v for v, _, _ in dd)
    pc = collections.Counter(v for v, _, _ in pw)
    uniq = {v for v in dc if dc[v] == 1 and pc.get(v) == 1}
    pairs = []
    for v in sorted(uniq):
        p = next((x, y) for t, x, y in pw if t == v)
        q = next((x, y) for t, x, y in dd if t == v)
        pairs.append((p, q))
    if len(pairs) < 3:
        return None
    tr = _fit(pairs)
    # one refit without the pairs the first fit cannot explain: a label misread as a dimension is an outlier
    res = [math.dist(apply(tr, *p), q) for p, q in pairs]
    keep = [pr for pr, r in zip(pairs, res) if r <= FIT_TOL_M]
    if len(keep) >= 3 and len(keep) < len(pairs):
        tr = _fit(keep)
        res = [math.dist(apply(tr, *p), q) for p, q in keep]
    tr["PAIRS"] = len(pairs); tr["INLIERS"] = len(keep) if keep else len(pairs)
    tr["MAX_RESIDUAL_M"] = round(max(res), 4); tr["MEAN_RESIDUAL_M"] = round(sum(res) / len(res), 4)
    tr["ESTABLISHED"] = tr["INLIERS"] >= MIN_INLIERS and tr["MAX_RESIDUAL_M"] <= FIT_TOL_M
    return tr


def labels_in_drawing(floor, ents):
    tr = transform_for(floor, ents)
    if not tr or not tr["ESTABLISHED"]:
        return tr, []
    out = [{"NAME": n, "X": round(x, 4), "Y": round(y, 4)}
           for n, px, py in page_labels(PAGE_OF[floor]) for x, y in [apply(tr, px, py)]]
    return tr, out
