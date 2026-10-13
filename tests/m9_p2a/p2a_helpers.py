"""Phase 2A (ARCH_TAKEOFF_V2.1) test helpers: the synthetic villa's plan-region entities, transformed in one way at a
time (translate, rotate, mirror, units), and the room / opening engine run on them directly - a rotated drawing's
title frame is refused by the admission (NO_PLAN_REGION), so the metamorphic suite runs below the plan-region split."""

from __future__ import annotations

import math
from collections import Counter

from engine.source import arch_plan as AP
from engine.source import arch_rooms as AR
from engine.source import robust_geometry as RG


def villa_regions(tmp_path):
    from tools import arch_intake as AI
    from tools import arch_synth as AS
    from tools import urban_intake as UI
    p = tmp_path / "villa.dxf"
    AS.villa(str(p))
    E = UI.read(str(p))
    A = AI.read_arch(p, unit_m=E["unit_m"])
    E = dict(E, hatches=[dict(h, ring=h["rings"][0]) for h in A["hatches"] if h["rings"]], texts=A["texts"],
             inserts=A["inserts"], segments=E["segments"] + A["extra_segments"], arcs=E["arcs"] + A["extra_arcs"])
    P = AP.plan_regions(E, split="EMPTY_BANDS", frames_from_lines_fallback=True)
    out = {}
    for r in P["regions"]:
        b = r["box"]
        ents = AP.region_entities(E, b)
        eps = max(1e-3 / E["unit_m"], max(b[2] - b[0], b[3] - b[1]) * 1e-6)
        ents = dict(ents, segments=[s for s in ents["segments"] if not AP._on_frame_side(s["a"], s["b"], b, eps)])
        out[r["floor"]] = ents
    return out, E["unit_m"]


def transform(ents, f, *, scale=1.0, mirror=False):
    """every point through f; lengths (radii, text heights) x scale; a mirror flips the arc direction."""
    def P(p):
        q = f((p[0], p[1]))
        return (q[0], q[1])
    out = dict(ents)
    out["segments"] = [dict(s, a=P(s["a"]), b=P(s["b"])) for s in ents["segments"]]
    arcs = []
    for a in ents["arcs"]:
        d = a.get("dir")
        if mirror and d in ("CCW", "CW"):
            d = "CW" if d == "CCW" else "CCW"
        arcs.append(dict(a, c=P(a["c"]), s=P(a["s"]), e=P(a["e"]), m=P(a["m"]) if a.get("m") else a.get("m"),
                         r=a["r"] * scale, dir=d))
    out["arcs"] = arcs
    out["circles"] = [dict(c, c=P(c["c"]), r=c["r"] * scale) for c in ents.get("circles", [])]
    out["texts"] = [dict(t, x=P((t["x"], t["y"]))[0], y=P((t["x"], t["y"]))[1]) for t in ents["texts"]]
    out["hatches"] = [dict(h, ring=[P(p) for p in h["ring"]],
                           rings=[[P(p) for p in r] for r in h.get("rings") or [h["ring"]]]) for h in ents["hatches"]]
    out["inserts"] = [dict(i, x=P((i["x"], i["y"]))[0], y=P((i["x"], i["y"]))[1]) for i in ents.get("inserts", [])]
    return out


def rot(deg, at=(0.0, 0.0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (p[0] * c - p[1] * s + at[0], p[0] * s + p[1] * c + at[1])


def run(ents, unit_m, method):
    """the V2 (geometry None) or V2.1 room / opening engine on one region's entities."""
    geom = RG.Geometry(unit_m) if method == "V2.1" else None
    kw = {"geom": geom} if geom is not None else {}
    L = AP.layer_roles(ents, unit_m, tol="UNIT_RELATIVE", **kw)
    S = AR.spaces(ents, L["roles"], unit_m, region_id="R", tol="UNIT_RELATIVE", **kw)
    return S, geom


def fingerprint(S):
    """unit- and placement-free: opening kinds and widths (m), space classes / names and areas (m2), door states."""
    ops = sorted((o["kind"], o["width_m"]) for o in S["openings"])
    sp = sorted((f["class"], "+".join(f.get("codes") or []), f["area_m2"]) for f in S["spaces"])
    return {"openings": ops, "spaces": sp, "doors": dict(Counter(v.get("state") for v in S["door_status"].values()))}


def same(a, b, rel=1e-6):
    """two fingerprints equal: identical keys and labels, numbers within rel (and 1e-9 absolute)."""
    if a["doors"] != b["doors"] or len(a["openings"]) != len(b["openings"]) or len(a["spaces"]) != len(b["spaces"]):
        return False
    for x, y in zip(a["openings"] + a["spaces"], b["openings"] + b["spaces"]):
        if x[:-1] != y[:-1] or abs(x[-1] - y[-1]) > max(1e-9, rel * abs(x[-1])):
            return False
    return True
