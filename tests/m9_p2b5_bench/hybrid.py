"""HYBRID CAD + VISION RECONCILIATION - Phase 2B-5 Part 6. Vision never makes a BOQ quantity: it can only corroborate
a CAD room, ask for a review, or point at something the CAD reading may have missed. Values are never averaged.

    reconcile(cad, vision, cad_source, vision_source) -> [record]

Each record carries, for both sides, the polygon with its provenance (Part 6.2): drawing identity and revision, input
hash, source type, coordinate system, scale evidence, extraction method (reader, version, method), vertices, room
label, wall and opening associations when the reader gives them; then the confidence indicators (IoU, area
difference, label agreement), the discrepancy flags and one status:

    AGREE              matched, IoU >= 0.98 and area within 1 %          -> the CAD value, corroborated
    REVIEW_CANDIDATE   matched, IoU 0.80 - 0.98 or area within 1 - 5 %   -> the CAD value, flagged for review
    DISAGREEMENT       matched, IoU < 0.80, area beyond 5 % or the
                       labels conflict                                   -> the CAD value held for review
    CAD_ONLY           a CAD room vision did not find                    -> the CAD value, not corroborated
    VISUAL_OMISSION    a vision room with no CAD room                    -> no BOQ quantity: a candidate to look at
"""

from __future__ import annotations

AGREE_IOU, REVIEW_IOU = 0.98, 0.80
AGREE_AREA, REVIEW_AREA = 0.01, 0.05
STATUSES = ("AGREE", "REVIEW_CANDIDATE", "DISAGREEMENT", "CAD_ONLY", "VISUAL_OMISSION")
PROVENANCE_KEYS = ("drawing", "revision", "input_sha256", "kind", "coordinate_system", "scale_evidence", "reader",
                   "version", "method")


def _poly(p):
    from shapely.geometry import Polygon
    g = Polygon(p)
    return g if g.is_valid else g.buffer(0)


def _iou(a, b):
    i = a.intersection(b).area
    u = a.union(b).area
    return i / u if u else 0.0


def _norm(label):
    return "".join(ch for ch in (label or "").upper() if ch.isalnum()) or None


def _side(r, src):
    return {"area_m2": r["area_m2"], "label": r.get("label"),
            "vertices_mm": [[round(x, 1), round(y, 1)] for x, y in r["polygon_mm"]],
            "openings": r.get("openings"), "walls": r.get("walls"),
            "provenance": {k: src.get(k) for k in PROVENANCE_KEYS}}


def _flags(iou, da, conflict):
    out = []
    if iou < AGREE_IOU:
        out.append(f"IOU_{iou:.3f}_BELOW_{AGREE_IOU}")
    if da > AGREE_AREA:
        out.append(f"AREA_DIFF_{100 * da:.2f}_PCT")
    if conflict:
        out.append("LABEL_CONFLICT")
    return out


def reconcile(cad, vision, cad_source, vision_source):
    """cad / vision: [{"label", "polygon_mm", "area_m2", "openings"?, "walls"?}]; *_source: the PROVENANCE_KEYS
    (missing keys are recorded as None, never guessed)."""
    C = [(i, r, _poly(r["polygon_mm"])) for i, r in enumerate(cad)]
    V = [(j, r, _poly(r["polygon_mm"])) for j, r in enumerate(vision)]
    pairs = sorted(((_iou(pc, pv), i, j) for i, _, pc in C for j, _, pv in V), reverse=True)
    used_c, used_v, out = set(), set(), []
    for iou, i, j in pairs:
        if iou < 0.5 or i in used_c or j in used_v:
            continue
        used_c.add(i)
        used_v.add(j)
        c, v = cad[i], vision[j]
        da = abs(v["area_m2"] - c["area_m2"]) / c["area_m2"] if c["area_m2"] else 1.0
        lc, lv = _norm(c.get("label")), _norm(v.get("label"))
        conflict = lc is not None and lv is not None and lc != lv
        if conflict or iou < REVIEW_IOU or da > REVIEW_AREA:
            status = "DISAGREEMENT"
        elif iou >= AGREE_IOU and da <= AGREE_AREA:
            status = "AGREE"
        else:
            status = "REVIEW_CANDIDATE"
        out.append({"status": status, "label": c.get("label") or v.get("label"), "iou": round(iou, 4),
                    "area_diff_pct": round(100 * da, 3), "label_conflict": conflict,
                    "confidence": {"iou": round(iou, 4), "area_diff_pct": round(100 * da, 3),
                                   "label_match": None if lc is None or lv is None else not conflict},
                    "flags": _flags(iou, da, conflict), "boq_basis": "CAD", "boq_area_m2": c["area_m2"],
                    "release": {"AGREE": "CAD_CORROBORATED", "REVIEW_CANDIDATE": "CAD_REVIEW",
                                "DISAGREEMENT": "CAD_HELD_FOR_REVIEW"}[status],
                    "cad": _side(c, cad_source), "vision": _side(v, vision_source)})
    for i, c, _ in C:
        if i not in used_c:
            out.append({"status": "CAD_ONLY", "label": c.get("label"), "confidence": None, "flags": ["NOT_IN_VISION"],
                        "boq_basis": "CAD", "boq_area_m2": c["area_m2"], "release": "CAD_NOT_CORROBORATED",
                        "cad": _side(c, cad_source), "vision": None})
    for j, v, _ in V:
        if j not in used_v:
            out.append({"status": "VISUAL_OMISSION", "label": v.get("label"), "confidence": None,
                        "flags": ["NOT_IN_CAD"], "boq_basis": None, "boq_area_m2": None,
                        "release": "NO_BOQ_CANDIDATE_ONLY", "cad": None, "vision": _side(v, vision_source)})
    return out
