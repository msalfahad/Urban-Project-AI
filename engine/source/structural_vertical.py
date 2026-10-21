"""STRUCTURAL VERTICAL INTERVAL ENGINE (V1) - the concrete height of every column occurrence from ITS OWN upper
termination, never from a global depth.

storey_intervals()   printed levels -> storey intervals with their authority. Finished-floor levels give
                     STRUCTURAL_INTERVAL_FROM_FFL_EQUAL_BUILDUP (the structural top-to-top interval equals the FFL
                     difference only when the floor build-ups above and below are equal); a printed structural level
                     (top of slab) outranks it (STRUCTURAL_LEVEL). Context only - never a column height by itself.
framing_members()    the members whose plan footprint enters a column outline on the sheet ABOVE the storey.
controlling_member() the deepest member framing into the column:
                       every framing member bound to a scheduled type                -> PROVEN (its D)
                       some unbound, each dominated by the bound maximum             -> PROVEN_UNBOUND_DOMINATED
                         (an unbound band's depth is bounded by the deepest scheduled section of its drawn breadth)
                       an unbound member could be deeper                             -> BLOCKED_UPPER_MEMBER_UNBOUND
                       an unbound member whose drawn breadth matches no schedule row -> BLOCKED_UPPER_MEMBER_UNSCHEDULED
                       no member frames in, slab thickness printed for the region    -> SLAB_SOFFIT (D = t)
                       no member, no thickness                                       -> BLOCKED_UPPER_TERMINATION
column_interval()    height = interval - D_ctrl; joint (beam-column node below the slab) = plan area x (D_ctrl - t);
                     concrete = plan area x height. The joint is a separate component so a column measured to the
                     controlling soffit and beams measured face to face neither double count nor omit the node.
neck()               footing top (or other lower structural support) to the ground beam / slab / column start; any
                     level missing -> BLOCKED_HEIGHT. A finished floor level is corroboration only; a step count is
                     never a height.

Project-agnostic; stdlib only. Lengths in metres, sections in cm, plan coordinates native.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "STRUCTURAL_VERTICAL_INTERVAL_V1"
FFL_INTERVAL = "STRUCTURAL_INTERVAL_FROM_FFL_EQUAL_BUILDUP"
STRUCTURAL_LEVEL = "STRUCTURAL_LEVEL"
PROVEN = "PROVEN"
DOMINATED = "PROVEN_UNBOUND_DOMINATED"
SLAB = "SLAB_SOFFIT"
BLOCK_UNBOUND = "BLOCKED_UPPER_MEMBER_UNBOUND"
BLOCK_UNSCHED = "BLOCKED_UPPER_MEMBER_UNSCHEDULED"
BLOCK_TERM = "BLOCKED_UPPER_TERMINATION"
COMPUTED_STATES = (PROVEN, DOMINATED, SLAB)


def storey_intervals(levels) -> list:
    """levels [{"name", "level_m", "kind": "FFL" | "STRUCTURAL_TOP", "source"}] bottom to top."""
    out = []
    for a, b in zip(levels, levels[1:]):
        auth = STRUCTURAL_LEVEL if a.get("kind") == b.get("kind") == "STRUCTURAL_TOP" else FFL_INTERVAL
        out.append({"from": a["name"], "to": b["name"], "interval_m": round(b["level_m"] - a["level_m"], 6),
                    "authority": auth, "sources": [a.get("source"), b.get("source")],
                    "assumption": None if auth == STRUCTURAL_LEVEL else
                    "equal floor build-up above and below (a printed structural level outranks this interval)"})
    return out


# ------------------------------------------------------------------ plan geometry (convex polygons)
def _axes(poly):
    out = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5
        if L > 0:
            out.append((-dy / L, dx / L))
    return out


def convex_overlap(p, q, eps) -> bool:
    """Separating-axis test for two convex polygons; touching within eps counts as overlap."""
    for ax in _axes(p) + _axes(q):
        pa = [x * ax[0] + y * ax[1] for x, y in p]
        qa = [x * ax[0] + y * ax[1] for x, y in q]
        if max(pa) < min(qa) - eps or max(qa) < min(pa) - eps:
            return False
    return True


def framing_members(column_polygon, members, *, eps) -> list:
    """members [{"id", "polygon", "bound": bool, "type", "D_cm", "drawn_breadth_mm", "candidate_types"?}]."""
    return [m for m in members if convex_overlap(column_polygon, m["polygon"], eps)]


def depth_upper_bound(drawn_breadth_mm, libraries, tol_mm, candidate_types=None):
    """Deepest scheduled section whose breadth equals the drawn breadth (any namespace), or among candidate_types."""
    best = None
    for lib in libraries.values():
        for t, row in lib.items():
            if row.get("B_cm") is None or row.get("D_cm") is None:
                continue
            if candidate_types is not None and t not in candidate_types:
                continue
            if candidate_types is None and abs(row["B_cm"] * 10.0 - drawn_breadth_mm) > tol_mm:
                continue
            if best is None or row["D_cm"] > best[1]:
                best = (t, row["D_cm"])
    return best


def controlling_member(framing, libraries, *, tol_mm, slab_thickness_cm=None) -> dict:
    if not framing:
        if slab_thickness_cm:
            return {"state": SLAB, "D_cm": slab_thickness_cm, "member": "SLAB", "framing": []}
        return {"state": BLOCK_TERM, "D_cm": None, "member": None, "framing": []}
    bound = [m for m in framing if m["bound"]]
    unbound = [m for m in framing if not m["bound"]]
    dmax = max((m["D_cm"] for m in bound), default=None)
    ctrl = max(bound, key=lambda m: (m["D_cm"], m["type"]), default=None)
    ubs = []
    for m in unbound:
        ub = depth_upper_bound(m["drawn_breadth_mm"], libraries, tol_mm, m.get("candidate_types"))
        ubs.append({"id": m["id"], "drawn_breadth_mm": m["drawn_breadth_mm"], "upper_bound": ub})
    rec = {"framing": [{"id": m["id"], "bound": m["bound"], "type": m.get("type"), "D_cm": m.get("D_cm"),
                        "drawn_breadth_mm": m.get("drawn_breadth_mm")} for m in framing], "unbound_bounds": ubs}
    if any(u["upper_bound"] is None for u in ubs):
        return dict(rec, state=BLOCK_UNSCHED, D_cm=None, member=None)
    if not unbound:
        return dict(rec, state=PROVEN, D_cm=dmax, member=ctrl["type"])
    if dmax is not None and all(u["upper_bound"][1] <= dmax for u in ubs):
        return dict(rec, state=DOMINATED, D_cm=dmax, member=ctrl["type"])
    return dict(rec, state=BLOCK_UNBOUND, D_cm=None, member=None,
                could_reach_cm=max(u["upper_bound"][1] for u in ubs))


def column_interval(*, B_cm, D_cm_col, interval, control, slab_thickness_cm) -> dict:
    """interval: a storey_intervals() record; control: controlling_member() result."""
    area = B_cm * D_cm_col / 1e4
    if control["state"] not in COMPUTED_STATES or interval is None:
        return {"state": control["state"] if interval else "BLOCKED_INTERVAL", "height_m": None, "volume_m3": None,
                "joint_m3": None, "plan_area_m2": round(area, 6)}
    Dm = control["D_cm"] / 100.0
    h = interval["interval_m"] - Dm
    t = (slab_thickness_cm or 0) / 100.0
    joint = area * max(Dm - t, 0.0) if control["state"] != SLAB else 0.0
    return {"state": control["state"], "interval_m": interval["interval_m"], "interval_authority": interval["authority"],
            "controlling_member": control["member"], "controlling_depth_m": round(Dm, 6), "height_m": round(h, 6),
            "plan_area_m2": round(area, 6), "volume_m3": round(area * h, 6),
            "joint_m3": round(joint, 6) if slab_thickness_cm is not None else None,
            "joint_state": "COMPUTED" if slab_thickness_cm is not None else "BLOCKED_SLAB_THICKNESS",
            "formula": "B x D x (interval - D_ctrl); joint = B x D x (D_ctrl - t)"}


def neck(*, footing_top_m=None, upper_start_m=None, B_cm=None, D_cm=None) -> dict:
    if footing_top_m is None or upper_start_m is None or B_cm is None or D_cm is None:
        missing = [n for n, v in (("footing top / lower support level", footing_top_m),
                                  ("ground beam / slab / column start level", upper_start_m),
                                  ("neck section", B_cm)) if v is None]
        return {"state": "BLOCKED_HEIGHT", "height_m": None, "volume_m3": None, "missing": missing,
                "never": ["a finished floor level as the neck top", "a step count", "a benchmark neck height"]}
    h = upper_start_m - footing_top_m
    return {"state": "COMPUTED", "height_m": round(h, 6), "volume_m3": round(B_cm * D_cm / 1e4 * h, 6)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "interval_authorities": [STRUCTURAL_LEVEL, FFL_INTERVAL],
           "states": [PROVEN, DOMINATED, SLAB, BLOCK_UNBOUND, BLOCK_UNSCHED, BLOCK_TERM],
           "joint": "column plan area x (D_ctrl - slab t): separate component",
           "never": ["one global beam depth", "floor-to-floor minus a fixed depth for every column", "a neck from steps",
                     "an architectural ceiling as a structural level"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
