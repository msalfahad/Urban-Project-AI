"""HYBRID CAD + VISION RECONCILIATION - Phase 2B-5 Part 6. Vision never makes a BOQ quantity: it can only corroborate
a CAD room, ask for a review, or point at something the CAD reading may have missed. Values are never averaged.

    reconcile(cad, vision, cad_source, vision_source) -> [record]

Each record carries the provenance of both sides (source kind, file digest, reader and version, method) and one status:

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


def reconcile(cad, vision, cad_source, vision_source):
    """cad / vision: [{"label", "polygon_mm", "area_m2"}]; *_source: {"kind", "file_sha256", "reader", "version",
    "method"}."""
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
                    "boq_basis": "CAD", "boq_area_m2": c["area_m2"],
                    "release": {"AGREE": "CAD_CORROBORATED", "REVIEW_CANDIDATE": "CAD_REVIEW",
                                "DISAGREEMENT": "CAD_HELD_FOR_REVIEW"}[status],
                    "cad": {"area_m2": c["area_m2"], "provenance": dict(cad_source)},
                    "vision": {"area_m2": v["area_m2"], "provenance": dict(vision_source)}})
    for i, c, _ in C:
        if i not in used_c:
            out.append({"status": "CAD_ONLY", "label": c.get("label"), "boq_basis": "CAD", "boq_area_m2": c["area_m2"],
                        "release": "CAD_NOT_CORROBORATED", "cad": {"area_m2": c["area_m2"],
                                                                   "provenance": dict(cad_source)}, "vision": None})
    for j, v, _ in V:
        if j not in used_v:
            out.append({"status": "VISUAL_OMISSION", "label": v.get("label"), "boq_basis": None, "boq_area_m2": None,
                        "release": "NO_BOQ_CANDIDATE_ONLY", "cad": None,
                        "vision": {"area_m2": v["area_m2"], "provenance": dict(vision_source)}})
    return out
