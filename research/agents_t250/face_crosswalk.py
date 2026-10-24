"""T-250 face crosswalk rules (research, stdlib only, any villa; not wired into any method).

One wall FACE = one straight wall run seen from one side. This module answers, from geometry only:

  (a) FACE LENGTH PER WALL. Every sample of a walked room contour (class WALL / COLUMN / WINDOW / DOOR / GAP /
      VIRTUAL, with its length) is put on the straight wall band whose face line it lies on (perpendicular offset
      t / 2 within FACE_TOL_M, inside the band's length). Each band side is then CLOSED along the run: every metre of
      the run on that side is room face (which room), junction (inside another band: an L / T end or a crossing wall),
      column (inside a column outline), or no room (exterior, court, shaft or an unwalked space), and the residual is
      named. A metre is never counted twice and never dropped.
  (b) ROOM-SIDE LINE OF A CURVED OPENING. The developed line a room deducts is the drawn line that bounds the room
      (the room region lies on it), read as its own arc between the jambs; a glass line the room does not touch, a
      printed window width measured on another face, or a chord is refused as the room face.
  (c) ONE DATUM PER FACE. A wall height and a finish height on one face are two readings of one storey interval: both
      are derived from the same named datum pair; two independent intervals on one face are refused, and a HELD datum
      keeps both readings HELD (never 0, never the other ledger's figure).

Statuses are the board's five (WORKFLOW_CONTROLS s.5). Rule ids: R-T250-1 (a), R-T250-2 (b), R-T250-3 (c), proposed.
"""
from __future__ import annotations

import math
from collections import defaultdict

FACE_TOL_M = 0.025      # a contour sample lies on a band face line within 2.5 cm (wall stage centreline vs drawn faces)
END_REACH_M = 0.03      # ... and inside the band's length (+ 3 cm at each end)
STEP_M = 0.005          # closure step along a run (the walk's own 5 mm sample)
RESIDUAL_OK_M = 0.03    # a face closure residual up to 3 cm is sampling (two 5 mm ends + the 2.5 cm face tolerance)
CLASSES = ("WALL", "COLUMN", "WINDOW", "DOOR", "GAP", "VIRTUAL")
FINISH_CLASSES = ("WALL", "COLUMN")       # plastered / painted (T-128 paintable)
OPENING_CLASSES = ("WINDOW", "DOOR", "GAP")
CAUSES = ("ROOM", "JUNCTION", "COLUMN", "NO_ROOM")
HELD = "HELD"


class CrosswalkError(ValueError):
    """an input that the rules refuse (units, duplicated sample, glass line as room face, two datums ...)."""


# ------------------------------------------------------------------------------------------------ geometry helpers
def frame(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L <= 0:
        raise CrosswalkError("zero-length band")
    ux, uy = dx / L, dy / L
    return ux, uy, -uy, ux, L


def project(p, band):
    ux, uy, nx, ny, L = band["_f"]
    a = band["a"]
    vx, vy = p[0] - a[0], p[1] - a[1]
    return vx * ux + vy * uy, vx * nx + vy * ny


def point_at(band, s, off):
    ux, uy, nx, ny, _ = band["_f"]
    a = band["a"]
    return a[0] + s * ux + off * nx, a[1] + s * uy + off * ny


def in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xc > x:
                inside = not inside
    return inside


def prepare(bands):
    """bands: [{'band', 't_m', 'a', 'b'}] straight centrelines in metres. Units guard: 0.05 <= t <= 0.60 m."""
    out = []
    for b in bands:
        t = float(b["t_m"])
        if not 0.05 <= t <= 0.60:
            raise CrosswalkError(f"band {b['band']}: thickness {t} m outside 0.05 .. 0.60 (units?)")
        q = dict(b)
        q["_f"] = frame(b["a"], b["b"])
        out.append(q)
    return out


def in_band(p, band, grow=0.0):
    s, d = project(p, band)
    L = band["_f"][4]
    return -grow <= s <= L + grow and abs(d) <= band["t_m"] / 2 + grow


# ----------------------------------------------------------------------------------------------- (a) face crosswalk
def locate(p, bands):
    """the band whose face line p lies on: (band, s, side +1/-1, residual) or None. Ties at a corner (p on two faces)
    go to the smaller residual; an exact tie goes to the band listed first (deterministic)."""
    best = None
    for b in bands:
        s, d = project(p, b)
        L = b["_f"][4]
        if not -END_REACH_M <= s <= L + END_REACH_M:
            continue
        r = abs(abs(d) - b["t_m"] / 2)
        if r <= FACE_TOL_M and (best is None or r < best[3] - 1e-9):
            best = (b, s, 1 if d > 0 else -1, r)
    return best


def _in_room(p, parts):
    for q in parts:
        if in_poly(p, q["ext"]) and not any(in_poly(p, h) for h in q.get("holes", [])):
            return True
    return False


PROBE_M = 0.01          # the room must lie OUTSIDE the band strip, beyond the face, at 1 cm


def assign_samples(samples, bands, room_polys=None):
    """samples: {room: [(cls, x, y, seg_m, ring)]}. Returns (faces, unassigned):
    faces[(band, side)][room] = {'by_class': {cls: m}, 'iv': [(s0, s1)], 'pts': [(s, seg, cls, handle)]};
    unassigned[room][cls] = m; inside_strip[room][cls] = m (part of unassigned: the room lies inside the band strip, so
    the sample is not a face of that band; only checked when room_polys are given). Every sample is in faces or in
    unassigned, never both (closure from the room side is exact)."""
    faces = defaultdict(lambda: defaultdict(lambda: {"by_class": defaultdict(float), "iv": [], "pts": []}))
    unassigned = defaultdict(lambda: defaultdict(float))
    inside_strip = defaultdict(lambda: defaultdict(float))
    seen = set()
    for room, rows in samples.items():
        for row in rows:
            cls, x, y, seg, ring = row[:5]
            handle = row[5] if len(row) > 5 else None
            if cls not in CLASSES:
                raise CrosswalkError(f"{room}: unknown sample class {cls}")
            if not 0 < seg < 0.05:
                raise CrosswalkError(f"{room}: sample length {seg} m (units?)")
            key = (room, round(x, 4), round(y, 4), ring)
            if key in seen:
                raise CrosswalkError(f"{room}: sample at ({x}, {y}) given twice")
            seen.add(key)
            hit = locate((x, y), bands)
            if hit is not None and room_polys is not None:
                # a face of the band only when the room lies beyond that face (outside the strip): a room region
                # lying inside the strip (a niche or duct between the two lines) does not face this band
                b0, s0_, side0, _ = hit
                ux, uy, nx, ny, _L = b0["_f"]
                probe = (x + side0 * nx * PROBE_M, y + side0 * ny * PROBE_M)
                inner = (x - side0 * nx * PROBE_M, y - side0 * ny * PROBE_M)
                if not _in_room(probe, room_polys[room]) and _in_room(inner, room_polys[room]):
                    unassigned[room][cls] += seg
                    inside_strip[room][cls] += seg
                    continue
            if hit is None:
                unassigned[room][cls] += seg
                continue
            b, s, side, _ = hit
            f = faces[(b["band"], side)][room]
            f["by_class"][cls] += seg
            f["iv"].append((s - seg / 2, s + seg / 2))
            f["pts"].append((s, seg, cls, handle))
    return faces, unassigned, inside_strip


def split_by_piece(face_side, pieces):
    """face_side: {room: face} of one band side; pieces: [(s0, s1, run_id)] sorted. Each sample goes to the piece that
    holds its s (within END_REACH_M; the nearer piece when two reach), else to None (a stretch the run does not
    cover). Returns {run_id | None: {room: {'by_class', 'iv', 'm'}}}."""
    out = defaultdict(dict)
    for room, f in face_side.items():
        for s, seg, cls, handle in f["pts"]:
            best, dist = None, None
            for s0, s1, rid in pieces:
                d = 0.0 if s0 <= s <= s1 else min(abs(s - s0), abs(s - s1))
                if d <= END_REACH_M and (dist is None or d < dist):
                    best, dist = rid, d
            g = out[best].setdefault(room, {"by_class": defaultdict(float), "iv": [], "m": 0.0,
                                            "handles": defaultdict(float)})
            if handle:
                g["handles"][handle] += seg
            g["by_class"][cls] += seg
            g["iv"].append((s - seg / 2, s + seg / 2))
            g["m"] += seg
    return out


def _merge(iv):
    iv = sorted(iv)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def close_side(band, side, s0, s1, faces_side, others, columns, step=STEP_M):
    """closure of one band side over the run [s0, s1]: {'ROOM': {room: m}, 'JUNCTION': {band: m}, 'COLUMN': m,
    'NO_ROOM': m, 'length_m', 'residual_m'}. Sampling at mid-steps; a step on a room face goes to that room, else to the
    first other band whose strip holds the face point, else to a column outline, else NO_ROOM."""
    if s1 < s0:
        raise CrosswalkError("run span reversed")
    cov = {room: _merge(f["iv"]) for room, f in faces_side.items()}
    n = max(1, int(round((s1 - s0) / step)))
    h = (s1 - s0) / n
    res = {"ROOM": defaultdict(float), "JUNCTION": defaultdict(float), "COLUMN": 0.0, "NO_ROOM": 0.0}
    off = side * band["t_m"] / 2
    for k in range(n):
        s = s0 + (k + 0.5) * h
        room = next((r for r, ivs in cov.items() if any(a - 1e-6 <= s <= b + 1e-6 for a, b in ivs)), None)
        if room:
            res["ROOM"][room] += h
            continue
        p = point_at(band, s, off)
        ob = next((o for o in others if o["band"] != band["band"] and in_band(p, o, 0.005)), None)
        if ob is not None:
            res["JUNCTION"][ob["band"]] += h
            continue
        if any(in_poly(p, c) for c in columns):
            res["COLUMN"] += h
            continue
        res["NO_ROOM"] += h
    total = sum(res["ROOM"].values()) + sum(res["JUNCTION"].values()) + res["COLUMN"] + res["NO_ROOM"]
    res["length_m"] = s1 - s0
    res["residual_m"] = (s1 - s0) - total
    res["ROOM"] = dict(res["ROOM"])
    res["JUNCTION"] = dict(res["JUNCTION"])
    return res


def room_faces_outside_run(faces_side, s0, s1):
    """room face metres of this band side that fall OUTSIDE the run span (a face carried past the run end: the band is
    split there, or the run stops at a junction the room wraps)."""
    out = {}
    for room, f in faces_side.items():
        m = 0.0
        for a, b in _merge(f["iv"]):
            m += max(0.0, min(b, s0) - a) + max(0.0, b - max(a, s1))
        if m > 1e-6:
            out[room] = m
    return out


# ------------------------------------------------------------------------------- (b) room-side line, curved opening
def room_side_line(candidates, room_touch_m, jamb_returns_m=0.0, partition_ends_m=0.0, printed_width_m=None):
    """candidates: [{'id', 'kind': 'GLASS' | 'BAND_FACE' | 'DIMENSION', 'arc_m', 'touch_m'}] the drawn curved lines of
    one opening; touch_m = metres of the room contour lying on that line (from the walk). Returns the room-side record.
    The room face is the ONE candidate the rooms touch (touch_m >= 50 % of its arc); none or two -> refused. Developed
    room-side line = its arc + the jamb returns on the wall face line - the ends of partitions that stop on it. The
    printed window width (owner Q-38 A) is the WINDOW line's width and is kept beside, never used as the room face."""
    touched = [c for c in candidates if c["arc_m"] > 0 and c["touch_m"] >= 0.5 * c["arc_m"]]
    if len(touched) != 1:
        raise CrosswalkError(f"room-side line not unique: {len(touched)} candidate lines touched by the rooms")
    c = touched[0]
    if c["kind"] == "DIMENSION":
        raise CrosswalkError("a dimension line is not a room face")
    developed = c["arc_m"] + jamb_returns_m - partition_ends_m
    if abs(developed - room_touch_m) > RESIDUAL_OK_M + 0.01:
        raise CrosswalkError(f"developed {developed:.4f} m does not close with the walked room face {room_touch_m:.4f} m")
    rec = {"room_face_id": c["id"], "room_face_kind": c["kind"], "arc_m": c["arc_m"], "jamb_returns_m": jamb_returns_m,
           "partition_ends_m": partition_ends_m, "developed_m": developed, "walk_m": room_touch_m,
           "closure_m": developed - room_touch_m, "refused": [x["id"] for x in candidates if x is not c]}
    if printed_width_m is not None:
        rec["printed_width_m"] = printed_width_m
        rec["finish_minus_window_m"] = developed - printed_width_m
        rec["verdict"] = "RULE_DIFFERENCE" if abs(developed - printed_width_m) > 0.005 else "AGREE"
    return rec


# -------------------------------------------------------------------------------------------- (c) one datum per face
def one_datum(face):
    """face: {'floor_top': (value | None, status), 'ceiling_top': (value | None, status), 'slab_t': m,
    'member_d': m | None, 'readings': {'block': interval_used, 'finish': interval_used}} with each reading the storey
    interval the ledger used. Returns {'interval', 'block_h', 'plaster_h', 'status', 'refused'}. Two readings that used
    different intervals are refused (two datums on one face); a HELD datum holds both heights."""
    used = {k: v for k, v in (face.get("readings") or {}).items() if v is not None}
    if len({round(v, 3) for v in used.values()}) > 1:
        raise CrosswalkError(f"two datums on one face: {used}")
    (ft, fs), (ct, cs) = face["floor_top"], face["ceiling_top"]
    if ft is None or ct is None or HELD in (fs, cs):
        return {"interval": None, "block_h": None, "plaster_h": None, "status": HELD,
                "missing": [n for n, (v, s) in (("floor structural top", face["floor_top"]),
                                                ("slab top above", face["ceiling_top"])) if v is None or s == HELD]}
    I = ct - ft
    if not 1.5 <= I <= 8.0:
        raise CrosswalkError(f"storey interval {I} m outside 1.5 .. 8.0 (units?)")
    d = face.get("member_d")
    return {"interval": I, "plaster_h": I - face["slab_t"], "block_h": None if d is None else I - d,
            "status": "DRAWING-CONFIRMED", "missing": []}


def sensitivity_m2(face_len_m, d_interval_m):
    """m2 a face moves when its storey interval moves by d (block and plaster alike: one datum)."""
    if face_len_m is None:
        raise CrosswalkError("face length HELD: no m2 formed")
    return face_len_m * d_interval_m
