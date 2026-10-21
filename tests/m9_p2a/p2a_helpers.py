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


# ------------------------------------------------------------------ the door fixture (mm), hand truth in DOOR_TRUTH
DOOR_ROLES = {"A-WALL": "WALL", "A-DOOR": "DOOR", "A-GLAZ": "WINDOW", "A-COL": "COLUMN"}
DOOR_OUTER = [(0, 0), (12000, 0), (12000, 8000), (0, 8000)]
DOOR_ROOMS = {"HALL": [(200, 200), (4000, 200), (4000, 3000), (200, 3000)],
              "LIVING": [(4200, 200), (11800, 200), (11800, 3000), (4200, 3000)],
              "BEDROOM": [(200, 3200), (4000, 3200), (4000, 7800), (200, 7800)],
              "BATH": [(4200, 3200), (6000, 3200), (6000, 5000), (4200, 5000)],
              "LIFT": [(6200, 3200), (7800, 3200), (7800, 5000), (6200, 5000)],
              "KITCHEN": [(8000, 3200), (11800, 3200), (11800, 7800), (8000, 7800)],
              "CORRIDOR": [(4200, 5200), (7800, 5200), (7800, 7800), (4200, 7800)]}
DOOR_OPENINGS = [
    ("DOOR", "y", 0, 200, 1500, 2500, None),        # D1 HALL | outside 1.00 (main entrance)
    ("DOOR", "x", 4000, 4200, 1000, 1900, None),     # D2 HALL | LIVING 0.90
    ("DOOR", "y", 3000, 3200, 9000, 10600, None),    # D3 LIVING | KITCHEN 1.60, one insert with two leaves
    ("DOOR", "y", 3000, 3200, 1500, 2400, None),     # D4 HALL | BEDROOM 0.90
    ("DOOR", "y", 5000, 5200, 4600, 5400, None),     # D5 BATH | CORRIDOR 0.80
    ("DOOR", "y", 5000, 5200, 6600, 7500, None),     # D6 LIFT | CORRIDOR 0.90 (a hinged landing door)
    ("DOOR", "x", 11800, 12000, 6000, 6900, None)]   # D7 KITCHEN | outside 0.90
DOOR_SWINGS = (((1500, 200), 1000, 0, 90), ((4200, 1000), 900, 0, 90), ((9000, 3000), 800, 270, 360),
               ((10600, 3000), 800, 180, 270), ((1500, 3200), 900, 0, 90), ((4600, 5200), 800, 0, 90),
               ((6600, 5200), 900, 0, 90), ((11800, 6000), 900, 90, 180),
               ((6000, 10500), 900, 0, 90))            # U: a swing standing apart from every wall
DOOR_WORDS = (("ENTRANCE HALL", (2000, 1600)), ("LIVING", (8000, 1600)), ("BEDROOM", (2000, 5500)),
              ("BATH", (5100, 4100)), ("LIFT", (7000, 4100)), ("KITCHEN", (10000, 5500)), ("CORRIDOR", (6000, 6500)))
DOOR_TRUTH = {"PVC": sorted([0.9, 1.6, 0.9, 0.8]), "ALU": [0.9], "MAIN": [1.0], "LIFT": [0.9], "UNRESOLVED": 1,
              "swings": 9, "double_leaf_width": 1.6}


def door_fixture(words=DOOR_WORDS, openings=DOOR_OPENINGS, swings=DOOR_SWINGS):
    from tools import arch_synth as AS
    ents = AS._s4_ents(DOOR_ROOMS, DOOR_OUTER, openings, texts=words, swings=swings)
    for a in ents["arcs"]:                        # D3: both leaves in ONE door insert
        if a["id"] in ("A3", "A4"):
            a["path"] = ["DOOR:DD3"]
    for s in ents["segments"]:
        if (s.get("path") or [None])[0] in ("DOOR:3", "DOOR:4"):
            s["path"] = ["DOOR:DD3"]
    return ents


def door_run(ents, unit_m=1e-3, floor="GF", facts=None, method="V2.1", origin=(0.0, 0.0)):
    """spaces + rooms (arch_measure) + the door model of one floor, roles given."""
    from engine.source import arch_measure as AM
    from engine.source import door_model as DM
    geom = RG.Geometry(unit_m) if method == "V2.1" else None
    S = AR.spaces(ents, DOOR_ROLES, unit_m, region_id="R", tol="UNIT_RELATIVE",
                  **({"geom": geom} if geom is not None else {}))
    M = AM.measure(S, floor=floor, project_id="P", revision_set_sha256="0" * 64, facts=facts, documents=[])
    walls = [k for k, v in DOOR_ROLES.items() if v == "WALL"]
    fm = DM.floor_model(S, M["rooms"], ents, unit_m, floor, wall_layers=walls, facts=facts, origin=origin)
    texts = {t["id"]: t for t in ents["texts"]}
    ft = {f["face_id"]: [texts[i] for i in f.get("label_text_ids") or () if i in texts] for f in S["faces"]}
    model = DM.building_model([(floor, fm)], {floor: ents["texts"]}, {floor: ft}, unit_m, entrance_floor=floor,
                              facts=facts)
    return S, M, model
