"""Read-only vector reader for the issued ST7757.pdf detail sheets (pypdf only).

The detail sheets (pp.13-16) and the schedule sheets (pp.9-12) of the issued structural PDF carry their lettering as
plotted SHX strokes, so the page has no extractable text. What the page does carry is the CAD layer of every stroke
(optional-content groups such as S-REIN.D, S-TEXT.D, S-DIM.D) and the exact stroke geometry. This module reads both
with pypdf's content-stream parser:

    paths(pdf, page)          -> [(layer, line_width, [(x, y), ...]), ...]   (PDF points, page coordinates)
    segments(paths, box, ..)  -> 2-point segments inside a box, optionally on given layers
    components(segments)      -> segments grouped by shared end points (a drawn bar is one component)

Nothing is rendered, rasterised or OCR-ed here, and the engine PDF stack (engine/pdf_vector_evidence, PyMuPDF) is not
used: pypdf is a pure-Python BSD reader. The module is research tooling for the source-recovery round, not an
engine module, and it writes nothing.
"""

from __future__ import annotations

import collections
import math

from pypdf import PdfReader
from pypdf.generic import ContentStream

PAINT_OPS = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*"}


def _mul(a, b):
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2],
            a[2] * b[1] + a[3] * b[3], a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def _tp(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def paths(pdf_path, page_no):
    """Every painted path of one page as (layer, line width, points). Curves are flattened to 4 chords."""
    reader = PdfReader(str(pdf_path))
    page = reader.pages[page_no - 1]
    props = page["/Resources"].get("/Properties") or {}
    ocg = {}
    for k, v in props.items():
        try:
            ocg[k] = str(v.get_object().get("/Name"))
        except Exception:  # noqa: BLE001 - an unnamed group stays unnamed
            pass
    ctm, stack, lw, cur, layer, out = [1, 0, 0, 1, 0, 0], [], 1.0, [], [], []
    for operands, op in ContentStream(page.get_contents(), reader).operations:
        o = op.decode("latin1")
        if o == "q":
            stack.append((ctm[:], lw))
        elif o == "Q":
            ctm, lw = stack.pop()
        elif o == "cm":
            ctm = _mul([float(v) for v in operands], ctm)
        elif o == "w":
            lw = float(operands[0])
        elif o == "BDC":
            name = operands[1] if len(operands) > 1 else None
            layer.append(ocg.get(name, str(name)) if not isinstance(name, dict) else "")
        elif o == "EMC":
            if layer:
                layer.pop()
        elif o == "m":
            cur.append([_tp(ctm, float(operands[0]), float(operands[1]))])
        elif o == "l" and cur:
            cur[-1].append(_tp(ctm, float(operands[0]), float(operands[1])))
        elif o == "c" and cur:
            p0 = cur[-1][-1]
            p1, p2, p3 = (_tp(ctm, float(operands[i]), float(operands[i + 1])) for i in (0, 2, 4))
            for t in (0.25, 0.5, 0.75, 1.0):
                u = 1 - t
                cur[-1].append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                                u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
        elif o == "re":
            x, y, w, h = (float(v) for v in operands)
            cur.append([_tp(ctm, x, y), _tp(ctm, x + w, y), _tp(ctm, x + w, y + h), _tp(ctm, x, y + h),
                        _tp(ctm, x, y)])
        elif o == "h" and cur and cur[-1]:
            cur[-1].append(cur[-1][0])
        elif o in PAINT_OPS or o == "n":
            if o != "n":
                width = round(lw * abs(ctm[0]), 3)
                out += [(layer[-1] if layer else "", width, sp) for sp in cur if len(sp) >= 2]
            cur = []
    return out


def segments(all_paths, box, layers=None):
    """2-point segments whose both ends lie inside box = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    out = []
    for lay, lw, sp in all_paths:
        if layers is not None and lay not in layers:
            continue
        for a, b in zip(sp, sp[1:]):
            if math.dist(a, b) > 0.05 and all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in (a, b)):
                out.append((lay, lw, tuple(a), tuple(b)))
    return out


def components(segs, tol=0.15):
    """Group segments that share an end point (within tol): one drawn bar = one component."""
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))  # noqa: E731
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    index = collections.defaultdict(list)
    for i, s in enumerate(segs):
        for p in (s[2], s[3]):
            k = key(p)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in index.get((k[0] + dx, k[1] + dy), []):
                        parent[find(i)] = find(j)
            index[k].append(i)
    groups = collections.defaultdict(list)
    for i, s in enumerate(segs):
        groups[find(i)].append(s)
    return list(groups.values())


def length(comp):
    return sum(math.dist(s[2], s[3]) for s in comp)


def bbox(comp):
    xs = [p[0] for s in comp for p in (s[2], s[3])]
    ys = [p[1] for s in comp for p in (s[2], s[3])]
    return (min(xs), min(ys), max(xs), max(ys))


def is_dot(comp, size=6.0):
    """A bar seen in section is drawn as a small hatched circle: a component inside a size x size box."""
    x0, y0, x1, y1 = bbox(comp)
    return x1 - x0 < size and y1 - y0 < size


def point_to_segment(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    l2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2)) if l2 else 0.0
    return math.dist(p, (ax + t * dx, ay + t * dy))


def leaders_onto(all_paths, target, box, exclude_layers=("S-REIN.D",), touch=1.2, min_len=8.0):
    """Non-reinforcement strokes that end on the target segment (a leader touching a bar): their far ends."""
    a, b = target
    hits = []
    for s in segments(all_paths, box):
        if s[0] in exclude_layers or math.dist(s[2], s[3]) < min_len:
            continue
        for end, other in ((s[2], s[3]), (s[3], s[2])):
            if point_to_segment(end, a, b) < touch and point_to_segment(other, a, b) > 5:
                hits.append({"layer": s[0], "end": [round(v, 1) for v in end], "far": [round(v, 1) for v in other]})
    return hits
