"""DIMENSION EVIDENCE (M9 Phase 2A P2-09a, ARCH_TAKEOFF_V2.1) - read-only: the authored dimensions of a plan, their
effective DIMLFAC per dimension, and a cross-check of opening widths, wall thicknesses and door closures against them.
Nothing here changes a quantity or overrides geometry: a disagreement is a REVIEW finding.

A dimension is three things (engine/cad_adapter.py): the defpoint geometry (drawing units), the number it shows, and
that number brought back through DIMLFAC. The effective DIMLFAC of ONE dimension is, in order:
    its own DSTYLE override  >  its dimension style's DIMLFAC  >  the header $DIMLFAC (only when the style sets none)
                             >  1.0
(cad_adapter reads the header only - finding F-7.) The stored measurement (group 42) is compared with the defpoints
both unscaled and scaled; which one matches is reported, never assumed.

    effective_dimlfac(rec, header)       -> (value, source)
    resolve(rec, header, unit_m)         -> a normalised dimension (geometry, shown value, value in drawing units,
                                            usable flag and why not)
    census(dims, header, unit_m, regions)
    crosscheck(dims, openings, unit_m, doors=())
                                         -> {checks, findings, door_evidence}
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
import re
from collections import Counter

POLICY_ID = "DIMENSION_EVIDENCE_V1"
AGREE_MM = 5.0                     # a dimension agrees with the plan within this
ALONG_MM = 15.0                    # an extension origin projects onto a jamb within this
NEAR_WALL_MM = 400.0               # ... and stands within this of the wall
ON_FACE_MM = 5.0                   # a thickness dimension's origins lie on the faces within this
DEFPOINT_MM = 0.5                  # the shown value agrees with the defpoints within this
NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def effective_dimlfac(rec, header):
    if rec.get("override_dimlfac") not in (None, 0):
        return float(rec["override_dimlfac"]), "ENTITY_OVERRIDE"
    if rec.get("style_dimlfac") not in (None, 0):
        return float(rec["style_dimlfac"]), "DIMENSION_STYLE"
    if header not in (None, 0):
        return float(header), "HEADER (style sets none)"
    return 1.0, "DEFAULT"


def _number(text):
    if not text:
        return None
    m = NUM.search(text.replace("\\P", " "))
    return float(m.group(0).replace(",", ".")) if m else None


def resolve(rec, header, unit_m):
    k = 1.0 / unit_m / 1000.0                       # drawing units per mm
    out = dict(rec)
    lfac, src = effective_dimlfac(rec, header)
    out.update(dimlfac=lfac, dimlfac_source=src, usable=False, why_not=None)
    if rec["type"] not in ("LINEAR", "ALIGNED") or not rec.get("p2") or not rec.get("p3"):
        out["why_not"] = "NOT_LINEAR"
        return out
    p2, p3 = rec["p2"], rec["p3"]
    if rec["type"] == "LINEAR":
        a = math.radians(rec.get("angle") or 0.0)
        u = (math.cos(a), math.sin(a))
    else:
        L = math.dist(p2, p3) or 1.0
        u = ((p3[0] - p2[0]) / L, (p3[1] - p2[1]) / L)
    geom = abs((p3[0] - p2[0]) * u[0] + (p3[1] - p2[1]) * u[1])
    out.update(dir=list(u), geometry_du=geom, geometry_mm=geom / k)
    overridden = rec.get("text") not in (None, "", "<>")
    shown = _number(rec["text"]) if overridden else _number(rec.get("shown_text"))
    out["text_overridden"] = overridden
    out["shown_value"] = shown
    out["value_du"] = shown / lfac if shown is not None else None
    if rec.get("measurement") is not None:
        m = float(rec["measurement"])
        out["measurement_matches"] = ("UNSCALED" if abs(m - geom) / k <= DEFPOINT_MM else
                                      "SCALED_BY_DIMLFAC" if abs(m - geom * lfac) / k <= DEFPOINT_MM else "NEITHER")
    if shown is None:
        out["why_not"] = "NO_SHOWN_VALUE"
        return out
    out["defpoint_agreement_mm"] = abs(out["value_du"] - geom) / k
    if out["defpoint_agreement_mm"] > DEFPOINT_MM:
        out["why_not"] = "SHOWN_VALUE_DIFFERS_FROM_DEFPOINTS" + (" (text override)" if overridden else
                                                               " (stale or non-associative)")
        return out
    out["usable"] = True
    return out


def census(dims, header, unit_m, regions=()):
    rs = [resolve(d, header, unit_m) for d in dims]
    seen = Counter((d["type"], tuple(map(lambda v: round(v, 3), (d.get("p2") or [0, 0]) + (d.get("p3") or [0, 0]))))
                   for d in rs)
    for d in rs:
        key = (d["type"], tuple(map(lambda v: round(v, 3), (d.get("p2") or [0, 0]) + (d.get("p3") or [0, 0]))))
        d["duplicate"] = seen[key] > 1
        mid = ((d["p2"][0] + d["p3"][0]) / 2, (d["p2"][1] + d["p3"][1]) / 2) if d.get("p2") and d.get("p3") else None
        d["where"] = next((f for f, b in regions if mid and b[0] <= mid[0] <= b[2] and b[1] <= mid[1] <= b[3]),
                          "OUTSIDE_PLAN_REGIONS")
    return {"dimensions": rs, "counts": {"total": len(rs), "by_type": dict(Counter(d["type"] for d in rs)),
                                         "usable": sum(1 for d in rs if d["usable"]),
                                         "why_not": dict(Counter(d["why_not"] for d in rs if d["why_not"])),
                                         "text_overridden": sum(1 for d in rs if d.get("text_overridden")),
                                         "duplicates": sum(1 for d in rs if d["duplicate"]),
                                         "dimlfac_sources": dict(Counter(d["dimlfac_source"] for d in rs)),
                                         "by_region": dict(Counter(d["where"] for d in rs))}}


def _span_match(d, u, n, s0, s1, off_lo, off_hi, k):
    """True when the dimension runs along u and its two origins project onto s0 / s1 (either order), near the wall."""
    du = d["dir"]
    if abs(du[0] * u[0] + du[1] * u[1]) < math.cos(math.radians(1.0)):
        return False
    ss = sorted(p[0] * u[0] + p[1] * u[1] for p in (d["p2"], d["p3"]))
    oo = [p[0] * n[0] + p[1] * n[1] for p in (d["p2"], d["p3"])]
    near = all(off_lo - NEAR_WALL_MM * k <= o <= off_hi + NEAR_WALL_MM * k for o in oo)
    return near and abs(ss[0] - s0) <= ALONG_MM * k and abs(ss[1] - s1) <= ALONG_MM * k


def _across_match(d, u, n, s0, s1, off_lo, off_hi, k):
    """True when the dimension runs across the wall (along n) with its origins on the two faces, beside the opening."""
    du = d["dir"]
    if abs(du[0] * n[0] + du[1] * n[1]) < math.cos(math.radians(1.0)):
        return False
    oo = sorted(p[0] * n[0] + p[1] * n[1] for p in (d["p2"], d["p3"]))
    ss = [p[0] * u[0] + p[1] * u[1] for p in (d["p2"], d["p3"])]
    beside = all(s0 - 1000.0 * k <= s <= s1 + 1000.0 * k for s in ss)
    return beside and abs(oo[0] - off_lo) <= ON_FACE_MM * k and abs(oo[1] - off_hi) <= ON_FACE_MM * k


def crosscheck(dims, openings, unit_m, doors=()):
    """dims: resolved, usable dimensions of one plan; openings: band openings (u, n, s0, s1, o0, o1, width_m, wall_t_m);
    doors: door elements (V2.1) without a band opening (centre, u, n, structural width) for closure evidence."""
    k = 1.0 / unit_m / 1000.0
    use = [d for d in dims if d.get("usable") and not d.get("duplicate")]
    checks, findings, door_ev = [], [], []
    for o in openings:
        u, n = o["u"], o["n"]
        lo, hi = sorted((o["o0"], o["o1"]))
        for d in use:
            if _span_match(d, u, n, o["s0"], o["s1"], lo, hi, k):
                diff = d["value_du"] / k - o["width_m"] * 1000.0
                checks.append({"kind": "OPENING_WIDTH", "opening_id": o["opening_id"], "handle": d["handle"],
                               "dimension_mm": round(d["value_du"] / k, 3), "plan_mm": round(o["width_m"] * 1000, 3),
                               "diff_mm": round(diff, 3), "state": "AGREES" if abs(diff) <= AGREE_MM else "REVIEW"})
            elif _across_match(d, u, n, o["s0"], o["s1"], lo, hi, k):
                diff = d["value_du"] / k - o["wall_t_m"] * 1000.0
                checks.append({"kind": "WALL_THICKNESS", "opening_id": o["opening_id"], "handle": d["handle"],
                               "dimension_mm": round(d["value_du"] / k, 3), "plan_mm": round(o["wall_t_m"] * 1000, 3),
                               "diff_mm": round(diff, 3), "state": "AGREES" if abs(diff) <= AGREE_MM else "REVIEW"})
    for e in doors:
        if e.get("opening_id") or not e.get("u") or e.get("structural_opening_width_m") is None:
            continue
        u, n, c = e["u"], e["n"], e["centre"]
        w = e["structural_opening_width_m"] / unit_m
        sc = c[0] * u[0] + c[1] * u[1]
        oc = c[0] * n[0] + c[1] * n[1]
        for d in use:
            if _span_match(d, u, n, sc - w / 2, sc + w / 2, oc - 0.25 / unit_m, oc + 0.25 / unit_m, k):
                diff = d["value_du"] / k - e["structural_opening_width_m"] * 1000.0
                door_ev.append({"element_id": e["element_id"], "handle": d["handle"],
                                "value_mm": round(d["value_du"] / k, 3), "closure_mm":
                                round(e["structural_opening_width_m"] * 1000, 3), "diff_mm": round(diff, 3),
                                "agrees": abs(diff) <= AGREE_MM})
    for c in checks:
        if c["state"] == "REVIEW":
            findings.append({"level": "REVIEW", "code": f"DIMENSION_{c['kind']}_DIFFERS", "opening_id": c["opening_id"],
                             "message": f"{c['kind'].lower().replace('_', ' ')}: dimension {c['dimension_mm']:.1f} mm "
                                        f"vs plan {c['plan_mm']:.1f} mm ({c['diff_mm']:+.1f} mm); the plan geometry "
                                        "is kept, the difference needs review"})
    for d in dims:
        if d.get("why_not", "") and d["why_not"].startswith("SHOWN_VALUE_DIFFERS"):
            findings.append({"level": "REVIEW", "code": "DIMENSION_STALE_OR_OVERRIDDEN", "handle": d["handle"],
                             "message": f"shown {d.get('shown_value')} vs defpoints {d['geometry_mm']:.1f} mm "
                                        f"(DIMLFAC {d['dimlfac']:g}, {d['dimlfac_source']}): not used"})
    return {"checks": checks, "findings": findings, "door_evidence": door_ev,
            "counts": {f"{a}:{b}": n for (a, b), n in sorted(Counter((c["kind"], c["state"]) for c in checks).items())}}


def policy_record():
    return {"policy": POLICY_ID, "agree_mm": AGREE_MM, "along_mm": ALONG_MM, "near_wall_mm": NEAR_WALL_MM,
            "on_face_mm": ON_FACE_MM, "defpoint_mm": DEFPOINT_MM,
            "dimlfac_order": ["ENTITY_OVERRIDE", "DIMENSION_STYLE", "HEADER (style sets none)", "DEFAULT"],
            "never": ["a plan quantity changed by a dimension", "a stale or overridden dimension used",
                      "the group-42 scaling assumed", "a door promoted by a dimension without the owner's approval"]}
