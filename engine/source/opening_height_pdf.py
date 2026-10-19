"""OPENING HEIGHT FROM A PDF (T-082): printed opening heights read from VECTOR PDF elevation and section sheets and
bound to plan openings with the SAME rules as engine/source/opening_area.py (OPENING_AREA_V1), which this piece reads
only and calls unchanged. Method piece, NOT wired into a released method: no frozen file, rule or released quantity
changes.

Why (T-078, L-P9-02): on many villas the elevations and sections exist only on the PDF set, not in the CAD file, so the
heights printed there never reach the window / door areas. A vector PDF carries the same evidence as a DXF elevation,
only without dimension entities: a printed number, the dimension line it sits on, the extension lines and the drawn
openings. This piece rebuilds that evidence and hands opening_area.measure an ordinary view:

    page_primitives(path, page_no)          -> {"state", "words", "segments", ...}  (pymupdf, lazy; one PDF page)
    view_from_page(prims, box, view_id, *, scale_den=None)
                                            -> a view for opening_area.measure (+ "pdf" diagnostics)
    measure_pdf(plan_openings, *, floors, elevation_views=(), section_views=(), raster_sheets=(),
                curved_width_basis=None)    -> {"records", "views", "summary", "policy"}

Reading one vector page region (view_from_page), each step evidence, never a guess:
1. Scale: the view must print exactly one scale ("1:100", "1/50", "SCALE 1:100") inside its box, or the caller passes
   one read from the sheet title (scale_source CALLER). None or two different -> SCALE_NOT_PRINTED / SCALE_CONFLICT:
   the view gets no usable dimension (a PDF is never measured with a scale ruler: a scaled value is not a height).
   Drawing unit = one PDF point; unit_m = 0.0254 / 72 x scale.
2. Dimension: a number word whose text runs along an axis-parallel line within 1.5 text heights of it, the line
   ended on each side of the number by a stop: a short oblique stroke through or touching it (a tick, an arrow side,
   a dot chord) that is not part of a longer drawn curve (an arch crossing the line is no tick); a square segment
   that ENDS within 3 pt of the line at a stop is its extension line (an edge passing through it is not). A plain
   corner is no stop, so a jamb or a sill is never read as a dimension line. A chain drawn as one long line is split
   at its stops; the number belongs to the piece it stands over. A dimension style without ticks, arrows or dots is
   not read (its numbers stay unbound). Two lines with different stops equally near (within 0.25 pt) -> the number
   is AMBIGUOUS and not used.
3. Witness origins (p2, p3): the far end of the extension line at each stop (the end nearer the measured object); a
   stop with no extension line keeps the stop point. Record format = tools/arch_dimensions.py LINEAR records, so
   opening_area.printed applies its own check: the printed number equals the geometry within half a unit of its last
   printed digit, else STALE and never used.
4. Printed unit (m, cm or mm): the unit under which most bound dimensions agree with the geometry, at least two, and
   strictly more than any other unit; otherwise UNITS_NOT_PROVEN and no dimension of the view is used.
5. Segments that are parts of dimensions (lines, extension lines, ticks) leave the view: they are not jambs or arches.
   Curves (Bezier) are flattened into chords so an arched head is seen as curved lines (owner Q-32 = A in
   opening_area).

Merging (measure_pdf): elevation views (PDF views from this piece and DXF views from opening_area.read_view, together)
go through opening_area.measure exactly as T-078 defined it. SECTION views also show interior doors and windows
(a section sees the walls beyond the cut), so they are measured in a second call in which no opening is skipped as
"interior"; the two results are merged per opening:
    one MEASURED height                      -> that record (its source view named)
    MEASURED on both and the heights differ  -> HELD HEIGHT_CONFLICT with both values (never an average)
    no MEASURED height                       -> the elevation record (its hold reason), section notes as evidence
A RASTER_ONLY sheet (a scan: no words, no vectors) is never read by this piece (no OCR, no scaling): every held record
lists it under "raster_sheets_not_read", so a person can read it into the controlled project data file (owner Q-17 =
A, T-064). Status names, hold reasons and the never-list are opening_area's (UP-QTY-STATUS-001: held never 0).

Rules: UP-OPEN-SCHED-001, UP-DOOR-AREA-001, UP-DOOR-HGT-001, UP-QTY-STATUS-001, OWNER-Q32-A, OWNER-Q33-A,
OWNER-Q17-A (typed values only through the project data file), L-P9-02. Project-agnostic: no layer, title, sheet or
project name is coded. Stdlib only, except page_primitives (pymupdf, lazy).
"""

from __future__ import annotations

import math
import re
from collections import Counter

from engine.source import opening_area as OA

POLICY_ID = "OPENING_HEIGHT_PDF_V1"
PT_M = 0.0254 / 72.0                 # one PDF point on paper, in metres
TEXT_NEAR = 1.5                      # a number lies within this many text heights of its dimension line
AMBIG_PT = 0.25                      # two candidate lines nearer than this to each other's distance: ambiguous
STOP_PT = 0.6                        # a stop crosses or ends at the dimension line within this
TICK_MAX_PT = 6.0                    # a tick / arrow stroke is at most this long
EXT_END_PT = 3.0                     # an extension line ends within this of its dimension line (a drawn edge that
                                     # passes through the line, e.g. a ground line or a sill, is not an extension)
AXIS_TOL = 0.02                      # |sin| below which a segment or text direction is axis-parallel
PRINT_UNITS = (("m", 1.0), ("cm", 0.01), ("mm", 0.001))
RULES = OA.RULES + ("OWNER-Q17-A", "L-P9-02")
NUMBER = re.compile(r"^\d+(?:[.,]\d+)?$")
SCALE = re.compile(r"(?:^|[^\d.])1\s*[:/]\s*(\d+(?:\.\d+)?)\s*$")


# ------------------------------------------------------------------------------------------- page primitives
def page_primitives(path, page_no=1):
    """One PDF page -> words (span text, box and direction, y UP) and segments (lines, rectangle sides and Bezier
    curves flattened into 8 chords; y UP). state VECTOR when it has words or vectors, RASTER_ONLY otherwise (the same
    test as tools/urban_intake.read_pdf)."""
    import pymupdf                                                    # lazy: the reading core is stdlib only

    doc = pymupdf.open(str(path))
    pg = doc[page_no - 1]
    H = pg.rect.height
    words = []
    for blk in pg.get_text("dict").get("blocks", ()):
        for line in blk.get("lines", ()):
            d = line.get("dir", (1.0, 0.0))
            for sp in line.get("spans", ()):
                t = (sp.get("text") or "").strip()
                if not t:
                    continue
                x0, y0, x1, y1 = sp["bbox"]
                words.append({"value": t, "x0": x0, "y0": H - y1, "x1": x1, "y1": H - y0,
                              "dir": (round(d[0], 6), round(-d[1], 6))})
    segs = []
    n = 0
    for dr in pg.get_drawings():
        for it in dr.get("items", ()):
            n += 1
            if it[0] == "l":
                pts = [it[1], it[2]]
            elif it[0] == "re":
                r = it[1]
                pts = [r.tl, r.tr, r.br, r.bl, r.tl]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
            elif it[0] == "c":
                p0, c1, c2, p3 = it[1], it[2], it[3], it[4]
                pts = []
                for k in range(9):
                    t = k / 8.0
                    a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                    pts.append(pymupdf.Point(a * p0.x + b * c1.x + c * c2.x + e * p3.x,
                                             a * p0.y + b * c1.y + c * c2.y + e * p3.y))
            else:
                continue
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                if (p.x, p.y) != (q.x, q.y):
                    segs.append((p.x, H - p.y, q.x, H - q.y, f"pdf{n}.{i}"))
    has_img = bool(pg.get_images())
    state = "VECTOR" if (words or segs) else ("RASTER_ONLY" if has_img else "EMPTY")
    return {"page": page_no, "width_pt": pg.rect.width, "height_pt": H, "state": state, "words": words,
            "segments": segs, "has_image": has_img}


# ------------------------------------------------------------------------------------------- reading one view
def _inbox(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _axis(dx, dy):
    L = math.hypot(dx, dy)
    if L == 0:
        return None
    if abs(dy) / L <= AXIS_TOL:
        return "H"
    if abs(dx) / L <= AXIS_TOL:
        return "V"
    return None


def scale_of(words):
    """the printed scales among the words: sorted distinct denominators."""
    out = set()
    for w in words:
        m = SCALE.search(w["value"].strip())
        if m:
            out.add(float(m.group(1)))
    return sorted(out)


def _lines(segs):
    """axis-parallel segments -> {"o": orientation, "c": constant coordinate, "lo", "hi", "id"}"""
    out = []
    for s in segs:
        o = _axis(s[2] - s[0], s[3] - s[1])
        if o == "H":
            out.append({"o": "H", "c": (s[1] + s[3]) / 2.0, "lo": min(s[0], s[2]), "hi": max(s[0], s[2]), "id": s[4]})
        elif o == "V":
            out.append({"o": "V", "c": (s[0] + s[2]) / 2.0, "lo": min(s[1], s[3]), "hi": max(s[1], s[3]), "id": s[4]})
    return out


def _curve_ids(segs):
    """ids of oblique strokes that belong to a longer drawn curve (an arch, a dome): strokes joined end to end whose
    total length exceeds 2 x TICK_MAX_PT. Such a stroke is never a tick, even where it crosses a dimension line."""
    obl = [s for s in segs if _axis(s[2] - s[0], s[3] - s[1]) is None]
    key = lambda x, y: (round(x / 0.05), round(y / 0.05))            # noqa: E731
    parent = {s[4]: s[4] for s in obl}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    at = {}
    for s in obl:
        for k in (key(s[0], s[1]), key(s[2], s[3])):
            if k in at:
                parent[find(s[4])] = find(at[k])
            else:
                at[k] = s[4]
    total = Counter()
    for s in obl:
        total[find(s[4])] += math.hypot(s[2] - s[0], s[3] - s[1])
    return {s[4] for s in obl if total[find(s[4])] > 2 * TICK_MAX_PT}


def _stops(line, segs):
    """points along `line` that end a dimension: a short oblique stroke (a tick, an arrow side or a dot chord) through
    or touching the line. A square segment at the same point is its extension line. A plain corner (a jamb meeting a
    sill) is not a stop, so a drawn edge is never read as a dimension line.
    -> [(t along the line, extension segment or None, tick id)]"""
    ticks, squares = [], []
    curve = _curve_ids(segs)
    for s in segs:
        if s[4] == line["id"]:
            continue
        x1, y1, x2, y2 = s[:4]
        o = _axis(x2 - x1, y2 - y1)
        if line["o"] == "H":
            a1, b1, a2, b2 = x1, y1, x2, y2                     # a = along, b = across
        else:
            a1, b1, a2, b2 = y1, x1, y2, x2
        c = line["c"]
        if o is not None and o != line["o"]:
            if min(b1, b2) - STOP_PT <= c <= max(b1, b2) + STOP_PT and min(abs(b1 - c), abs(b2 - c)) <= EXT_END_PT:
                squares.append(((a1 + a2) / 2.0, s))         # an extension line ENDS at (or just past) the line
        elif o is None and math.hypot(x2 - x1, y2 - y1) <= TICK_MAX_PT and s[4] not in curve:
            if abs(b2 - b1) < 1e-12:
                continue
            if (b1 - c) * (b2 - c) <= 0:
                a = a1 + (a2 - a1) * (c - b1) / (b2 - b1)
            elif abs(b1 - c) <= STOP_PT:
                a = a1
            elif abs(b2 - c) <= STOP_PT:
                a = a2
            else:
                continue
            if line["lo"] - STOP_PT <= a <= line["hi"] + STOP_PT:
                ticks.append((a, s[4]))
    out = []
    for a, tid in sorted(ticks):
        if out and abs(out[-1][0] - a) <= STOP_PT:
            continue
        ext = min((q for q in squares if abs(q[0] - a) <= STOP_PT), key=lambda q: abs(q[0] - a), default=None)
        out.append((a, ext[1] if ext else None, tid))
    return out


def _origin(line, t, ext):
    """witness origin at stop t: the far end of the extension line from the dimension line (nearer the object)."""
    if line["o"] == "H":
        if ext is None:
            return (t, line["c"])
        ends = [(ext[0], ext[1]), (ext[2], ext[3])]
        far = max(ends, key=lambda p: abs(p[1] - line["c"]))
        return (t, far[1])
    if ext is None:
        return (line["c"], t)
    ends = [(ext[0], ext[1]), (ext[2], ext[3])]
    far = max(ends, key=lambda p: abs(p[0] - line["c"]))
    return (far[0], t)


def view_from_page(prims, box, view_id, *, scale_den=None, kind="ELEVATION"):
    """One elevation or section region of a VECTOR page -> an opening_area view (drawing unit = 1 pt) with LINEAR
    dimension records rebuilt from the printed numbers; "pdf" holds the diagnostics (scale, unit, unbound numbers)."""
    diag = {"state": prims.get("state"), "kind": kind, "scale": None, "scale_source": None, "print_unit": None,
            "numbers": 0, "bound": 0, "unbound": [], "ambiguous": [], "why": None}
    base = {"view_id": view_id, "header_dimlfac": None, "dims": [], "segments": [], "pdf": diag, "kind": kind}
    if prims.get("state") != "VECTOR":
        diag["why"] = "RASTER_ONLY: a scan has no printed text or vectors this piece reads (no OCR, no scaling)"
        return {**base, "unit_m": PT_M}
    words = [w for w in prims["words"] if _inbox(box, (w["x0"] + w["x1"]) / 2.0, (w["y0"] + w["y1"]) / 2.0)]
    segs = [s for s in prims["segments"] if _inbox(box, s[0], s[1]) and _inbox(box, s[2], s[3])]
    scales = scale_of(words)
    if len(scales) > 1:
        diag.update(why="SCALE_CONFLICT", scales=scales)
        return {**base, "unit_m": PT_M, "segments": segs}
    if scales:
        sc, src = scales[0], "PRINTED"
        if scale_den is not None and abs(float(scale_den) - sc) > 1e-9:
            diag.update(why="SCALE_CONFLICT", scales=[sc, float(scale_den)])
            return {**base, "unit_m": PT_M, "segments": segs}
    elif scale_den is not None:
        sc, src = float(scale_den), "CALLER (read from the sheet title)"
    else:
        diag["why"] = "SCALE_NOT_PRINTED: no scale inside the view and none passed: no dimension is used"
        return {**base, "unit_m": PT_M, "segments": segs}
    unit_m = PT_M * sc
    diag.update(scale=sc, scale_source=src)
    lines = _lines(segs)
    used = set()
    found = []
    for w in words:
        v = w["value"].strip()
        if not NUMBER.match(v):
            continue
        diag["numbers"] += 1
        dx, dy = w["dir"]
        o = "H" if abs(dy) <= AXIS_TOL else "V" if abs(dx) <= AXIS_TOL else None
        if o is None:
            diag["unbound"].append((v, "TEXT_NOT_AXIS_PARALLEL"))
            continue
        cx, cy = (w["x0"] + w["x1"]) / 2.0, (w["y0"] + w["y1"]) / 2.0
        along, across = (cx, cy) if o == "H" else (cy, cx)
        th = (w["y1"] - w["y0"]) if o == "H" else (w["x1"] - w["x0"])
        cands = []
        for ln in lines:
            if ln["o"] != o or not (ln["lo"] - STOP_PT <= along <= ln["hi"] + STOP_PT):
                continue
            dist = abs(ln["c"] - across)
            if dist > TEXT_NEAR * th + STOP_PT:
                continue
            stops = _stops(ln, segs)
            below = [q for q in stops if q[0] < along]
            above = [q for q in stops if q[0] > along]
            if not below or not above:
                continue
            lo, hi = below[-1], above[0]
            cands.append((dist, ln, lo, hi))
        if not cands:
            diag["unbound"].append((v, "NO_DIMENSION_LINE"))
            continue
        cands.sort(key=lambda q: q[0])
        if len(cands) > 1 and cands[1][0] - cands[0][0] <= AMBIG_PT and \
                (abs(cands[1][2][0] - cands[0][2][0]) > STOP_PT or abs(cands[1][3][0] - cands[0][3][0]) > STOP_PT):
            diag["ambiguous"].append(v)
            continue
        _, ln, lo, hi = cands[0]
        p2, p3 = _origin(ln, lo[0], lo[1]), _origin(ln, hi[0], hi[1])
        found.append({"value": float(v.replace(",", ".")), "text": v, "o": o, "p2": p2, "p3": p3,
                      "geom": hi[0] - lo[0], "parts": {ln["id"], lo[2], hi[2]} | {q[1][4] for q in (lo, hi) if q[1]}})
    diag["bound"] = len(found)
    # the printed unit: the one under which most bound numbers equal their geometry (half a last digit)
    votes = {}
    for name, um in PRINT_UNITS:
        ok = 0
        for f in found:
            dec = len(f["text"].replace(",", ".").split(".")[1]) if "." in f["text"].replace(",", ".") else 0
            half = 0.5 * 10.0 ** -dec * um
            if abs(f["value"] * um - f["geom"] * unit_m) <= max(half, 0.0005) + 1e-9:
                ok += 1
        votes[name] = ok
    ranked = sorted(votes.items(), key=lambda kv: -kv[1])
    if ranked[0][1] < 2 or ranked[0][1] == ranked[1][1]:
        diag.update(why="UNITS_NOT_PROVEN: fewer than two printed numbers agree with the geometry under one unit, "
                        "or two units tie", unit_votes=votes)
        for f in found:
            used |= f["parts"]
        return {**base, "unit_m": unit_m, "segments": [s for s in segs if s[4] not in used]}
    pu = dict(PRINT_UNITS)[ranked[0][0]]
    diag.update(print_unit=ranked[0][0], unit_votes=votes)
    lfac = unit_m / pu                                         # printed units per drawing unit (pt)
    dims = []
    for i, f in enumerate(found):
        used |= f["parts"]
        dims.append({"handle": f"{view_id}:d{i}", "type": "LINEAR", "p2": list(f["p2"]), "p3": list(f["p3"]),
                     "angle": 0.0 if f["o"] == "H" else 90.0, "style_dimlfac": None, "override_dimlfac": lfac,
                     "measurement": None, "text": "", "shown_text": f["text"]})
    return {**base, "unit_m": unit_m, "dims": dims, "segments": [s for s in segs if s[4] not in used]}


# --------------------------------------------------------------------------------------------- measure / merge
def measure_pdf(plan_openings, *, floors, elevation_views=(), section_views=(), raster_sheets=(),
                curved_width_basis=None):
    elev = OA.measure(plan_openings, list(elevation_views), floors=floors, curved_width_basis=curved_width_basis)
    sect = None
    if section_views:
        seen = [dict(p) for p in plan_openings]
        for p in seen:
            if p.get("kind") in ("WINDOW", "DOOR"):
                p.pop("faces_outside", None)                     # a section sees interior openings too
        sect = OA.measure(seen, list(section_views), floors=floors, curved_width_basis=curved_width_basis)
    s_by = {(r["id"], r["floor"]): r for r in (sect["records"] if sect else ())}
    records = []
    for r in elev["records"]:
        k = (r["id"], r["floor"])
        s = s_by.get(k)
        out = r
        if s is not None and s["status"] == OA.MEASURED and s.get("height_source") == "ELEVATION":
            if r["status"] == OA.MEASURED and r.get("height_source") == "ELEVATION":
                if abs(r["height_m"] - s["height_m"]) > OA.TOL_M:
                    out = OA._held(next(p for p in plan_openings if (p["id"], p["floor"]) == k), "HEIGHT_CONFLICT",
                                   values_m=sorted({r["height_m"], s["height_m"]}),
                                   elevation=r["evidence"], section=s["evidence"])
                else:
                    out = {**r, "evidence": {**r["evidence"], "section_agrees": s["evidence"]}}
            elif r["status"] == OA.HELD:
                out = {**s, "height_source": "SECTION",
                       "evidence": {**s["evidence"], "elevation_hold": {"reason": r["reason"],
                                                                         "evidence": r["evidence"]}}}
        elif s is not None and r["status"] == OA.HELD:
            out = {**r, "evidence": {**r["evidence"], "section": {"status": s["status"], "reason": s["reason"]}}}
        if out["status"] == OA.HELD and raster_sheets:
            out = {**out, "evidence": {**out["evidence"], "raster_sheets_not_read": list(raster_sheets),
                                       "route": "a person reads the printed height into the controlled project data "
                                                "file (owner Q-17 = A); never scaled, never a default"}}
        records.append(out)
    views = elev["views"] + (sect["views"] if sect else [])
    return {"records": records, "views": views, "summary": OA.summary(records),
            "policy": {**OA.policy_record(), "policy": POLICY_ID, "uses": OA.POLICY_ID, "rules": list(RULES),
                       "raster_sheets_not_read": list(raster_sheets)}}
