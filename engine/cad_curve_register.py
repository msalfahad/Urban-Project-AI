"""CAD CURVE REGISTER - exact arc geometry from the authored DWG (§6, §13, §14).

The raster path cannot establish a curve's length: a visual reader can say
"a curved band of four concentric lines" and nothing more, and the A21
result for such a face is CURVE_DIMENSION_NOT_ESTABLISHED_FROM_VISUAL_SOURCE.
The DWG carries the same design as authored arcs, and an arc's length is
arithmetic on its radius and sweep. So the DWG is read on its own
deterministic path and the result carries

    CAD_GEOMETRY_STATUS = ESTABLISHED_FROM_DWG

for the geometry, while the A21 record keeps its own status. Nothing here
is fed back into the frozen A21 register.

TWO THINGS THIS MODULE IS CAREFUL ABOUT

  1. The DWG and the PDF are one design family. Agreement between them is
     not independent corroboration and the output says so
     (EVIDENCE_INDEPENDENCE = SHARED_SOURCE_FAMILY).

  2. Which arcs ARE the curve a trace describes is a correspondence, not a
     measurement. Arcs are located by a declared anchor (a room label in
     the model) and a radius band, the located sets are reported with
     CORRESPONDENCE_STATUS = PROPOSED_BY_ANCHOR_LOCATOR and
     SEMANTIC_LINK_STATUS = NOT_ESTABLISHED. A human links a curve set to a
     traced face; the code never does.
"""

from __future__ import annotations

import math

from engine.qs_measurement_region import canon_hash

CURVE_RULE_VERSION = "CADC-1.0"
DEFAULT_SEARCH_MM = 8000.0
DEFAULT_RADIUS_BAND_MM = (150.0, 6000.0)


def arc_length_mm(radius: float, start: float, end: float) -> float:
    sweep = (end - start) % (2 * math.pi)
    if sweep == 0.0:
        sweep = 2 * math.pi
    return radius * sweep


def frames(normalized) -> list:
    """Drawing frames: the large closed rectangles on the border layer.
    Floor identity is NOT established from them (the title text does not
    survive the decoder); they are reported as FRAME_n by x-range."""
    rects = {}
    for p in normalized.primitives:
        if p.kind != "SEGMENT" or p.provenance.layer != "1":
            continue
        L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
        if L < 20000:
            continue
        rects.setdefault(p.provenance.handle, []).append(p)
    out = []
    for h, segs in sorted(rects.items()):
        if len(segs) != 4:
            continue
        xs = [q for s in segs for q in (s.x1, s.x2)]
        ys = [q for s in segs for q in (s.y1, s.y2)]
        out.append({"FRAME_ID": f"FRAME_{len(out) + 1}", "HANDLE": h,
                    "X_MM": [round(min(xs)), round(max(xs))],
                    "Y_MM": [round(min(ys)), round(max(ys))],
                    "FLOOR_IDENTITY": "NOT_ESTABLISHED_FROM_CAD"})
    return out


def _frame_of(fr: list, x: float, y: float):
    for f in fr:
        if f["X_MM"][0] <= x <= f["X_MM"][1] and f["Y_MM"][0] <= y <= f["Y_MM"][1]:
            return f["FRAME_ID"]
    return None


def curve_register(normalized, *, anchors: dict,
                   search_mm: float = DEFAULT_SEARCH_MM,
                   radius_band_mm: tuple = DEFAULT_RADIUS_BAND_MM,
                   layers: tuple | None = None) -> dict:
    """anchors: {ANCHOR_ID: {"LABEL": text, "PROPOSED_A21": [...],
    "RADIUS_BAND_MM": (lo, hi) optional, "LAYERS": (...) optional}}"""
    fr = frames(normalized)
    arcs = [p for p in normalized.primitives if p.kind == "ARC"]
    texts = normalized.texts
    sets, unlocated = [], []
    for aid, a in anchors.items():
        lab = a["LABEL"].strip().lower()
        hits = [t for t in texts if (t.value or "").strip().lower() == lab]
        if not hits:
            unlocated.append({"ANCHOR_ID": aid, "LABEL": a["LABEL"],
                              "STATUS": "ANCHOR_LABEL_NOT_FOUND_IN_MODEL"})
            continue
        lo, hi = a.get("RADIUS_BAND_MM", radius_band_mm)
        lay = a.get("LAYERS", layers)
        for t in hits:
            groups = {}
            for p in arcs:
                if lay and p.provenance.layer not in lay:
                    continue
                if not (lo <= p.radius <= hi):
                    continue
                if math.hypot(p.cx - t.x, p.cy - t.y) > search_mm:
                    continue
                key = (round(p.cx), round(p.cy))
                groups.setdefault(key, []).append(p)
            for (cx, cy), ps in sorted(groups.items()):
                members = []
                for p in sorted(ps, key=lambda q: (q.radius, q.start_angle, q.object_id)):
                    members.append({
                        "CAD_ID": p.object_id, "LAYER": p.provenance.layer,
                        "RADIUS_MM": round(float(p.radius), 2),
                        "START_ANGLE_RAD": round(p.start_angle, 6),
                        "END_ANGLE_RAD": round(p.end_angle, 6),
                        "SWEEP_DEG": round(math.degrees(
                            (p.end_angle - p.start_angle) % (2 * math.pi)), 3),
                        "ARC_LENGTH_M": round(arc_length_mm(
                            p.radius, p.start_angle, p.end_angle) / 1000.0, 4),
                        "CAD_GEOMETRY_STATUS": "ESTABLISHED_FROM_DWG",
                    })
                radii = sorted({m["RADIUS_MM"] for m in members})
                sets.append({
                    "CURVE_SET_ID": f"CS-{aid}-{len(sets) + 1}",
                    "ANCHOR_ID": aid, "ANCHOR_LABEL": a["LABEL"],
                    "ANCHOR_TEXT_AT_MM": [round(t.x), round(t.y)],
                    "ANCHOR_INSTANCE_PATH": list(t.provenance.instance_path),
                    "FRAME_ID": _frame_of(fr, cx, cy),
                    "CENTER_MM": [cx, cy],
                    "DISTANCE_CENTER_TO_ANCHOR_M": round(
                        math.hypot(cx - t.x, cy - t.y) / 1000.0, 3),
                    "RADII_MM": radii,
                    "N_ARCS": len(members), "ARCS": members,
                    "LENGTH_BY_RADIUS_M": {
                        str(r): round(sum(m["ARC_LENGTH_M"] for m in members
                                          if m["RADIUS_MM"] == r), 4) for r in radii},
                    "CAD_GEOMETRY_STATUS": "ESTABLISHED_FROM_DWG",
                    "CORRESPONDENCE": {
                        "PROPOSED_A21_TRACES": a.get("PROPOSED_A21", []),
                        "CORRESPONDENCE_STATUS": "PROPOSED_BY_ANCHOR_LOCATOR",
                        "SEMANTIC_LINK_STATUS": "NOT_ESTABLISHED",
                        "WHO_LINKS": "a human, never this code",
                    },
                })
    # one curve set per center: keep the anchor nearest to it, record the
    # others as additional anchors (the geometry is the same arcs)
    by_center = {}
    for s in sets:
        key = tuple(s["CENTER_MM"])
        if key not in by_center or s["DISTANCE_CENTER_TO_ANCHOR_M"] < \
                by_center[key]["DISTANCE_CENTER_TO_ANCHOR_M"]:
            if key in by_center:
                s.setdefault("ALSO_NEAR_ANCHORS", []).append(
                    {"ANCHOR_ID": by_center[key]["ANCHOR_ID"],
                     "DISTANCE_M": by_center[key]["DISTANCE_CENTER_TO_ANCHOR_M"]})
                s["CORRESPONDENCE"]["PROPOSED_A21_TRACES"] = sorted(set(
                    s["CORRESPONDENCE"]["PROPOSED_A21_TRACES"]
                    + by_center[key]["CORRESPONDENCE"]["PROPOSED_A21_TRACES"]))
            by_center[key] = s
        else:
            by_center[key].setdefault("ALSO_NEAR_ANCHORS", []).append(
                {"ANCHOR_ID": s["ANCHOR_ID"], "DISTANCE_M": s["DISTANCE_CENTER_TO_ANCHOR_M"]})
            by_center[key]["CORRESPONDENCE"]["PROPOSED_A21_TRACES"] = sorted(set(
                by_center[key]["CORRESPONDENCE"]["PROPOSED_A21_TRACES"]
                + s["CORRESPONDENCE"]["PROPOSED_A21_TRACES"]))
    sets = [dict(s, CURVE_SET_ID=f"CS-{i + 1}")
            for i, s in enumerate(sorted(by_center.values(),
                                         key=lambda s: tuple(s["CENTER_MM"])))]
    body = {
        "CURVE_RULE_VERSION": CURVE_RULE_VERSION,
        "SOURCE_FILE": normalized.source_file,
        "DRAWING_UNIT": normalized.drawing_unit,
        "INSUNITS_CODE": normalized.insunits_code,
        "FRAMES": fr,
        "CURVE_SETS": sets,
        "ANCHORS_NOT_LOCATED": unlocated,
        "ARCS_IN_MODEL": len(arcs),
        "EVIDENCE_INDEPENDENCE": "SHARED_SOURCE_FAMILY",
        "DWG_AND_PDF_ARE_ONE_DESIGN_FAMILY": True,
        "A21_STATUS_FOR_THESE_CURVES": "CURVE_DIMENSION_NOT_ESTABLISHED_FROM_VISUAL_SOURCE",
        "NEVER_FED_BACK_INTO_FROZEN_A21": True,
    }
    body["REGISTER_SHA256"] = canon_hash(body)
    return body
