"""T-742 Alsenan census (research only, not a method, not wired): every roof / terrace parapet run of the T-172 /
T-311 chains tied to the DXF entities (by handle) that draw its outer and inner top arris on the roof plan.

    python3 -I research/agents_t742/t742_census.py <P7757.dxf> <t159_rings.json> <out.json>

Inputs stay in the private scratch (.work/private): the plan DXF (Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip) and the T-159 rings rebuilt from it (research/agents_t159/t159_extract.py, with its
ARCH_WALLS.json beside it). The output written to <out.json> holds handles, layers, lengths (m) and statuses only:
no coordinate, no drawing content, no client name. Registration of an outline floor on the plan that draws the roof
parapet is by vote: the translation (1 mm grid) under which most chain vertices coincide with entity end points."""
import collections
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t172"))
sys.path.insert(0, str(ROOT / "research" / "agents_t159"))
sys.path.insert(0, str(ROOT))

import ezdxf                                                                   # noqa: E402
import t172_alsenan as T                                                       # noqa: E402
import t172_edges as TE                                                        # noqa: E402

# the plan that draws each chain's roof (site rectangle 31,370 x 15,000 mm, layer 5: 1F plan AC7 / B2F / B2C / B30,
# 2F plan 12A1 .. 12A4); the 2F roof parapet stands on the 2F outer walls (layer 1, as T-737 read them)
PLAN_OF_CHAIN = {"ANNEX": "1F_PLAN", "GF": "1F_PLAN", "1F": "2F_PLAN", "2F": "2F_PLAN"}
PLAN_BOX_MM = {"1F_PLAN": (-205093, -805294, -173723, -790294), "2F_PLAN": (-249945, -805294, -218575, -790294)}
LAYERS = ("5", "1")
# the layers that draw each chain's arrises: roof edges of the lower roofs on layer 5; the 2F block's walls on layer 1
# (the 1F roof parapet SW-3 is collinear with the 2F SW wall, so a layer-5 line there is never a 2F parapet face)
CHAIN_LAYERS = {"ANNEX": ("5",), "GF": ("5",), "1F": ("5", "1"), "2F": ("1",)}
TOL = 1.0          # mm: on-line distance and centre / radius tolerance


def plan_entities(msp):
    out = {k: [] for k in PLAN_BOX_MM}
    for e in msp.query("LINE ARC"):
        if e.dxf.layer not in LAYERS:
            continue
        for k, (x0, y0, x1, y1) in PLAN_BOX_MM.items():
            if e.dxftype() == "LINE":
                a, b = e.dxf.start, e.dxf.end
                if all(x0 - 1 <= p.x <= x1 + 1 and y0 - 1 <= p.y <= y1 + 1 for p in (a, b)):
                    out[k].append({"h": e.dxf.handle, "layer": e.dxf.layer, "type": "LINE",
                                   "a": (a.x, a.y), "b": (b.x, b.y)})
            else:
                c = e.dxf.center
                if x0 <= c.x <= x1 and y0 <= c.y <= y1:
                    out[k].append({"h": e.dxf.handle, "layer": e.dxf.layer, "type": "ARC", "c": (c.x, c.y),
                                   "r": e.dxf.radius, "sa": e.dxf.start_angle, "ea": e.dxf.end_angle})
    return out


def endpoints(ents):
    pts = []
    for e in ents:
        if e["type"] == "LINE":
            pts += [e["a"], e["b"]]
        else:
            for ang in (e["sa"], e["ea"]):
                pts.append((e["c"][0] + e["r"] * math.cos(math.radians(ang)),
                            e["c"][1] + e["r"] * math.sin(math.radians(ang))))
    return pts


def register(verts, ents):
    """Translation (mm, rounded) under which most chain vertices land on entity end points; returns (dx, dy, votes)."""
    pts = endpoints(ents)
    grid = collections.Counter()
    for v in verts:
        for p in pts:
            grid[(round(p[0] - v[0]), round(p[1] - v[1]))] += 1
    (dx, dy), n = grid.most_common(1)[0]
    # refine: count vertices within 1 mm of an end point under (dx, dy)
    hit = sum(1 for v in verts if any(math.hypot(p[0] - v[0] - dx, p[1] - v[1] - dy) <= TOL for p in pts))
    return dx, dy, hit


def on_line(e, a, b):
    """Overlap (mm) of a LINE entity lying on the line a-b, measured within [a, b]; 0 when not on it."""
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    def dist(p):
        return abs((p[0] - a[0]) * u[1] - (p[1] - a[1]) * u[0])
    if dist(e["a"]) > TOL or dist(e["b"]) > TOL:
        return 0.0
    s = sorted(((e["a"][0] - a[0]) * u[0] + (e["a"][1] - a[1]) * u[1],
                (e["b"][0] - a[0]) * u[0] + (e["b"][1] - a[1]) * u[1]))
    return max(0.0, min(s[1], L) - max(s[0], 0.0))


def on_arc(e, c, r, a, b):
    if e["type"] != "ARC" or math.dist(e["c"], c) > TOL or abs(e["r"] - r) > TOL:
        return 0.0
    sw = (e["ea"] - e["sa"]) % 360.0
    return e["r"] * math.radians(sw)


def arris(ents, kind, a, b, c=None, r=None):
    hs, cov = [], 0.0
    for e in ents:
        if kind == "ARC":
            o = on_arc(e, c, r, a, b)
        else:
            o = on_line(e, a, b) if e["type"] == "LINE" else 0.0
        if o > TOL:
            hs.append({"handle": e["h"], "layer": e["layer"], "overlap_m": round(o / 1000.0, 4)})
            cov += o
    return hs, cov


def outer_profile(ents, face, n, depth_max=700.0):
    """Entities parallel to an inner-face LINE entity, outside it (direction n) within depth_max mm: the roof-plan
    outer profile of a parapet whose outline side does not draw it. Returns [{handle, depth_m, overlap_m}]."""
    a, b = face["a"], face["b"]
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    out = []
    for e in ents:
        if e["type"] != "LINE" or e["h"] == face["h"]:
            continue
        d0 = (e["a"][0] - a[0]) * n[0] + (e["a"][1] - a[1]) * n[1]
        d1 = (e["b"][0] - a[0]) * n[0] + (e["b"][1] - a[1]) * n[1]
        if abs(d0 - d1) > TOL or not (TOL < d0 <= depth_max):
            continue
        s = sorted(((e["a"][0] - a[0]) * u[0] + (e["a"][1] - a[1]) * u[1],
                    (e["b"][0] - a[0]) * u[0] + (e["b"][1] - a[1]) * u[1]))
        ov = min(s[1], L) - max(s[0], 0.0)
        if ov > TOL:
            out.append({"handle": e["h"], "layer": e["layer"], "depth_m": round(d0 / 1000.0, 4),
                        "overlap_m": round(ov / 1000.0, 4), "from_m": round(max(s[0], 0.0) / 1000.0, 4)})
    return sorted(out, key=lambda x: x["from_m"])


def main():
    dxf, rings, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    msp = ezdxf.readfile(dxf).modelspace()
    ents = plan_entities(msp)
    sides, Ef, boxes, R = T.load_sides(rings)
    walls = {fl["floor"]: fl["walls"] for fl in json.loads((Path(rings).parent / "ARCH_WALLS.json").read_text())["floors"]}
    chains = {n: T.build_chain(n, s, sides, walls[s["floor"]], boxes) for n, s in T.CHAINS.items()}
    reg, rows = {}, []
    # one translation per (outline floor, target plan): every chain of that floor votes together
    groups = collections.defaultdict(list)
    for name, ch in chains.items():
        groups[(T.CHAINS[name]["floor"], PLAN_OF_CHAIN[name])].append(name)
    shift = {}
    for (f, plan), names in groups.items():
        bx = boxes[f]
        verts = [((s[k][0] + bx[0]) * 1000.0, (s[k][1] + bx[1]) * 1000.0) for n_ in names for s in chains[n_]
                 for k in ("a", "b")]
        dx, dy, hit = register(verts, ents[plan])
        for n_ in names:
            shift[n_] = (dx, dy)
        reg["+".join(names)] = {"outline_floor": f, "plan": plan, "vertices": len(verts), "on_entity_end_points": hit}
    for name, ch in chains.items():
        f = T.CHAINS[name]["floor"]
        bx = boxes[f]
        dx, dy = shift[name]
        def mm(p):
            return ((p[0] + bx[0]) * 1000.0, (p[1] + bx[1]) * 1000.0)
        for s in ch:
            a, b = mm(s["a"]), mm(s["b"])
            a, b = (a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)
            t = (s["t"] or 0.0) * 1000.0
            n = s["normal"]
            Lo = TE.side_length(s) * 1000.0
            E = [e for e in ents[PLAN_OF_CHAIN[name]] if e["layer"] in CHAIN_LAYERS[name]]
            if s["kind"] == "ARC":
                c = mm(s["c"])
                c = (c[0] + dx, c[1] + dy)
                r = s["r"] * 1000.0
                oh, oc = arris(E, "ARC", a, b, c, r)
                ri = None
                for cand in (r - t, r + t):
                    ih, ic = arris(E, "ARC", a, b, c, cand)
                    if ih:
                        ri = cand
                        break
            else:
                oh, oc = arris(E, "LINE", a, b)
                ih, ic = [], 0.0
                for sg in (-1.0, 1.0):      # the other face of the wall: inside first, then outside
                    # the other face's arris may run t past either end (concave corner): search a + -t .. b + t
                    L_ = math.dist(a, b)
                    u_ = ((b[0] - a[0]) / L_, (b[1] - a[1]) / L_)
                    ai = (a[0] + sg * n[0] * t - u_[0] * t, a[1] + sg * n[1] * t - u_[1] * t)
                    bi = (b[0] + sg * n[0] * t + u_[0] * t, b[1] + sg * n[1] * t + u_[1] * t)
                    ih, ic = arris(E, "LINE", ai, bi)
                    if ih:
                        break
            rows.append({"chain": name, "side": s["name"], "kind": s["kind"], "t_m": s["t"],
                         "outer_line_m": round(Lo / 1000.0, 4), "outer_handles": oh,
                         "outer_drawn_m": round(oc / 1000.0, 4), "inner_handles": ih,
                         "inner_drawn_m": round(ic / 1000.0, 4)})
    # roof-plan outer profiles of the runs whose outline side is not drawn on the roof plan (outer arris drawn < 90 %)
    profiles = {}
    for r_ in rows:
        if r_["outer_drawn_m"] >= 0.9 * r_["outer_line_m"] or not r_["inner_handles"]:
            continue
        E = [e for e in ents[PLAN_OF_CHAIN[r_["chain"]]] if e["layer"] in CHAIN_LAYERS[r_["chain"]]]
        hmax = max(r_["inner_handles"], key=lambda h: h["overlap_m"])["handle"]
        face = next(e for e in E if e["h"] == hmax)
        if hmax in profiles:
            continue
        s = next(x for x in chains[r_["chain"]] if x["name"] == r_["side"])
        profiles[hmax] = {"chain": r_["chain"], "first_side": r_["side"], "inner_face_m": round(
            math.dist(face["a"], face["b"]) / 1000.0, 4), "profile": outer_profile(E, face, s["normal"])}
    out.write_text(json.dumps({"registration": reg, "runs": rows, "outer_profiles": profiles}, indent=1))
    print(json.dumps(profiles, indent=0))
    for r_ in rows:
        print(r_["chain"], r_["side"], r_["outer_line_m"], "outer", "+".join(h["handle"] for h in r_["outer_handles"]),
              r_["outer_drawn_m"], "| inner", "+".join(h["handle"] for h in r_["inner_handles"]), r_["inner_drawn_m"])
    print(json.dumps(reg))


if __name__ == "__main__":
    main()
