"""ROOM LABEL GUARD (T-061): a room label that sits in no closed room face is HELD, never silently lost.

T-004a found labelled spaces (yard, courtyard, pool, roof, void) whose label lies in no closed room face of the plan,
so they appear in no output at all. This method piece reports every such label once (UP-QTY-STATUS-001: every
labelled space reported once - released, held or excluded; never 0). It is NOT wired into a released method:
arch_rooms.py and the frozen room builders are not changed, and no face, room or quantity is altered.

    guard(faces, labels, frame=None, unit_m=None, segments=None, tol_m=0.001) -> {"records", "summary", ...}

    faces     the closed room faces of ONE plan frame: {"face_id", "polygon": [(x, y), ...], "hole_polygons": [...]}
    labels    the texts of that frame: {"id", "value" (or "text"), "x", "y"}; only texts the room vocabulary
              ROOM_VOCAB_V2 (engine.source.room_vocab.classify) reads as a room label are guarded
    frame     the plan frame id, copied into every record
    unit_m    metres per drawing unit (1.0 for a metre drawing, 0.001 for mm). None = units not established: no
              length is converted to metres (left None, unit_status UNITS_MISSING), the geometry is still compared in
              the drawing's own units
    segments  optional boundary linework of the frame (walls, parapets, edges): {"id", "a": (x, y), "b": (x, y)};
              used only to name the nearest open boundary gap of a held label (diagnostic)
    tol_m     numerical coincidence tolerance in metres (a point on a line, two endpoints that touch); it is not a
              drafting-gap threshold: no gap of any size is closed here

Each guarded label gets exactly one record:

    IN_FACE                  inside one face (nested faces: the innermost); the face is untouched - the guard passes
                             it through, it measures nothing
    HELD ROOM_LABEL_NO_FACE  inside no face. NO area is computed (an exterior yard has no released scope: knowledge
                             1.5.0 OQ-04 is unresolved; a roof waits on its boundary basis). With linework given, the
                             nearest open boundary gap is named (its size, the two segment ids, its distance to the
                             label, and whether closing that one gap would enclose the label) - a diagnostic, never a
                             closure
    HELD ROOM_LABEL_AMBIGUOUS inside two faces that do not nest, or on a face's boundary line (a label on a shared wall
                             line, or on an outer wall line: in or out cannot be decided from the point)
    HELD ROOM_LABEL_NO_POSITION the label has no insertion point

General: no layer, room or project name is coded; rotated, mirrored, mm and m plans read alike (only distances and
point-in-polygon tests are used). Stdlib, plus shapely for the optional gap closure test.
"""

from __future__ import annotations

import math

from engine.source import room_vocab as RV

POLICY = "ROOM_LABEL_GUARD_V1"
RULE = "UP-QTY-STATUS-001"
ROOM_LABEL_STATUSES = ("TYPED", "HELD_COMPOUND")       # room_vocab.classify statuses that make a text a room label
MAX_GAP_TRIES = 12                                      # nearest open gaps tested for closure, per held label


# ----------------------------------------------------------------------------------------------------- geometry

def _ring(poly):
    pts = [(float(p[0]), float(p[1])) for p in (poly or ())]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


def _inside(x, y, ring):
    """even-odd point in polygon (any vertex order or orientation)."""
    ins = False
    n = len(ring)
    for i in range(n):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _ring_dist(x, y, ring):
    n = len(ring)
    return min(_seg_dist(x, y, ring[i], ring[(i + 1) % n]) for i in range(n)) if n else math.inf


def _area(ring):
    n = len(ring)
    return abs(sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n))) / 2.0


def _contains_ring(outer, inner, tol):
    """every vertex of inner inside outer or on its boundary (nesting test of two faces)."""
    return all(_inside(x, y, outer) or _ring_dist(x, y, outer) <= tol for x, y in inner)


def _tol_du(tol_m, unit_m, faces, segments):
    """the coincidence tolerance in drawing units; with no units a pure numerical one (1e-9 of the drawing extent)."""
    if unit_m:
        return tol_m / unit_m
    xs = [abs(c) for f in faces for p in f["ring"] for c in p]
    xs += [abs(c) for s in segments for p in (s["a"], s["b"]) for c in p]
    return 1e-9 * max(xs + [1.0])


# ----------------------------------------------------------------------------------------------------- open gaps

def _free_ends(segments, tol):
    """endpoints that touch no other segment (neither its end nor its body): the open ends of the linework."""
    out = []
    for i, s in enumerate(segments):
        for end in ("a", "b"):
            p = s[end]
            if not any(j != i and _seg_dist(p[0], p[1], o["a"], o["b"]) <= tol for j, o in enumerate(segments)):
                out.append((s["id"], end, p))
    return out


def _gaps(segments, tol):
    """pairs of open ends, shortest first, each end used once (greedy mutual pairing); no size limit is applied."""
    ends = _free_ends(segments, tol)
    pairs = sorted(((math.dist(ends[i][2], ends[j][2]), i, j) for i in range(len(ends))
                    for j in range(i + 1, len(ends)) if ends[i][0] != ends[j][0]), key=lambda t: t[0])
    used, gaps = set(), []
    for d, i, j in pairs:
        if i in used or j in used:
            continue
        used.update((i, j))
        gaps.append({"a": ends[i][2], "b": ends[j][2], "segments": [ends[i][0], ends[j][0]], "size_du": d})
    return gaps


def _closes_around(segments, gap, x, y):
    """True when the linework plus this one gap closes a ring round the point; None when shapely is missing."""
    try:
        from shapely.geometry import LineString, Point
        from shapely.ops import polygonize, unary_union
    except ImportError:                                     # pragma: no cover - shapely is in requirements.txt
        return None
    lines = [LineString([s["a"], s["b"]]) for s in segments if tuple(s["a"]) != tuple(s["b"])]
    lines.append(LineString([gap["a"], gap["b"]]))
    pt = Point(x, y)
    return any(p.contains(pt) for p in polygonize(unary_union(lines)))


def _nearest_gap(segments, gaps, x, y, unit_m):
    if not gaps:
        return None, "NO_OPEN_GAP_IN_LINEWORK"
    ranked = sorted(gaps, key=lambda g: _seg_dist(x, y, g["a"], g["b"]))
    pick, closes = ranked[0], False
    for g in ranked[:MAX_GAP_TRIES]:
        c = _closes_around(segments, g, x, y)
        if c:
            pick, closes = g, True
            break
        if c is None:
            closes = None
            break
    d = _seg_dist(x, y, pick["a"], pick["b"])
    return {"segments": pick["segments"], "size_du": round(pick["size_du"], 9),
            "size_m": round(pick["size_du"] * unit_m, 6) if unit_m else None,
            "distance_du": round(d, 9), "distance_m": round(d * unit_m, 6) if unit_m else None,
            "closes_around_label": closes, "gaps_tested": min(len(ranked), MAX_GAP_TRIES)}, "GAP_FOUND"


# ----------------------------------------------------------------------------------------------------- the guard

def _face(f):
    return {"face_id": f.get("face_id"), "ring": _ring(f.get("polygon")),
            "holes": [_ring(h) for h in (f.get("hole_polygons") or ())]}


def guard(faces, labels, frame=None, unit_m=None, segments=None, tol_m=0.001):
    if unit_m is not None and not (isinstance(unit_m, (int, float)) and unit_m > 0):
        raise ValueError(f"unit_m must be a positive number of metres per drawing unit or None, got {unit_m!r}")
    fs = [_face(f) for f in (faces or ())]
    readable = [f for f in fs if len(f["ring"]) >= 3]
    unreadable = [f["face_id"] for f in fs if len(f["ring"]) < 3]
    segs = [{"id": s.get("id"), "a": tuple(map(float, s["a"][:2])), "b": tuple(map(float, s["b"][:2]))}
            for s in (segments or ())]
    tol = _tol_du(tol_m, unit_m, readable, segs)
    gaps = _gaps(segs, tol) if segs else []
    records, skipped = [], 0
    for t in labels or ():
        text = t.get("value", t.get("text"))
        cls = RV.classify(text or "")
        if cls["status"] not in ROOM_LABEL_STATUSES:
            skipped += 1
            continue
        rec = {"policy": POLICY, "rule": RULE, "frame": frame, "text_id": t.get("id"), "text": text,
               "vocab": cls["vocab"], "code": cls["code"], "kind": cls["kind"], "wet": cls["wet"],
               "vocab_status": cls["status"], "face_id": None, "candidate_faces": [], "status": None,
               "reason": None, "area_m2": None, "nearest_gap": None, "gap_status": None,
               "unit_status": "OK" if unit_m else "UNITS_MISSING"}
        x, y = t.get("x"), t.get("y")
        if x is None or y is None:
            rec.update(status="HELD", reason="ROOM_LABEL_NO_POSITION", area_status="NOT_COMPUTED")
            records.append(rec)
            continue
        x, y = float(x), float(y)
        on_edge = [f for f in readable if _ring_dist(x, y, f["ring"]) <= tol or
                   any(_ring_dist(x, y, h) <= tol for h in f["holes"])]
        inside = [f for f in readable if f not in on_edge and _inside(x, y, f["ring"]) and
                  not any(_inside(x, y, h) for h in f["holes"])]
        if on_edge:
            cands = on_edge + inside
            rec.update(status="HELD", reason="ROOM_LABEL_AMBIGUOUS", area_status="NOT_COMPUTED",
                       candidate_faces=[f["face_id"] for f in cands],
                       basis="label on a face boundary line: in or out of the face is not decidable from the point")
        elif not inside:
            rec.update(status="HELD", reason="ROOM_LABEL_NO_FACE", area_status="NOT_COMPUTED",
                       basis="inside no closed room face; no area is computed (no released scope or boundary basis)")
            if unreadable:
                rec["unreadable_faces"] = list(unreadable)
            if segs:
                rec["nearest_gap"], rec["gap_status"] = _nearest_gap(segs, gaps, x, y, unit_m)
            else:
                rec["gap_status"] = "NO_LINEWORK_GIVEN"
        else:
            inner = min(inside, key=lambda f: _area(f["ring"]))
            nested = all(f is inner or _contains_ring(f["ring"], inner["ring"], tol) for f in inside)
            if nested:
                rec.update(status="IN_FACE", reason=None, face_id=inner["face_id"],
                           candidate_faces=[f["face_id"] for f in inside])
            else:
                rec.update(status="HELD", reason="ROOM_LABEL_AMBIGUOUS", area_status="NOT_COMPUTED",
                           candidate_faces=[f["face_id"] for f in inside],
                           basis="inside two faces that do not nest")
        records.append(rec)
    held = [r for r in records if r["status"] == "HELD"]
    summary = {"policy": POLICY, "rule": RULE, "frame": frame, "room_labels": len(records),
               "in_face": sum(1 for r in records if r["status"] == "IN_FACE"), "held": len(held),
               "held_by_reason": {k: sum(1 for r in held if r["reason"] == k) for k in
                                  ("ROOM_LABEL_NO_FACE", "ROOM_LABEL_AMBIGUOUS", "ROOM_LABEL_NO_POSITION")},
               "dropped": 0, "texts_not_room_labels": skipped, "faces": len(fs), "unreadable_faces": unreadable,
               "open_gaps": len(gaps), "unit_status": "OK" if unit_m else "UNITS_MISSING"}
    assert summary["in_face"] + summary["held"] == summary["room_labels"]      # every label reported once
    return {"records": records, "held": held, "summary": summary}


def census_rows(result):
    """one flat row per held label for a census table (no geometry, no coordinates)."""
    return [{"frame": r["frame"], "text_id": r["text_id"], "text": r["text"], "code": r["code"], "kind": r["kind"],
             "status": r["status"], "reason": r["reason"], "candidate_faces": ";".join(map(str, r["candidate_faces"])),
             "gap_size_m": (r["nearest_gap"] or {}).get("size_m"), "gap_status": r["gap_status"],
             "gap_closes_label": (r["nearest_gap"] or {}).get("closes_around_label")} for r in result["held"]]
