"""T-486 on the development villa: every candidate balcony / terrace / exposed-slab zone, classified and reconciled
against the candidate roof WP lines (ARCH_TAKEOFF_V3.0.46, research/agents_t485/out/LINE_INDEX_V3_0_46.json).

Drawings by Drive title and entity handle only (Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf
sha256 ab54dd55..., sanitary-7757.pdf). The one zone measured here (POOLCOURT-550, the slab round the oval void) is
read AT RUN TIME from the private drawing (decoded into the git-excluded private folder): this file holds entity
handles only, no coordinate; outputs are areas and lengths. Without the drawing, the measured zone is HELD (never 0).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t486_terrace_wp as T  # noqa: E402

ROOT = HERE.parents[1]
LINE_INDEX = ROOT / "research" / "agents_t485" / "out" / "LINE_INDEX_V3_0_46.json"
DXF_SHA256_PREFIX = "ab54dd554c31"
ORIGIN = "BBF"                       # the VOID label block on the 1F plan: local origin (metres)

# ---- POOLCOURT-550 by entity handle (P7757.dxf, 1F frame) ----------------------------------------------------------
BAY_FACE = ("BCD", "BCE", "BD0")     # outer face of the 1F curved bay wall (layer 1 / 5 / 1), one circle, wall line to line
VOID = ("BCF", "2F1C", "C7A", "2F1B")   # void edge (layer 5); C7A = the GF pool water edge seen from above
WALL = "B62"                         # 1F east wall outer face (layer 1), with B61 / C35 / B60 on the same line
NORTH = "C7D"                        # slab north edge (layer 5; no parapet: the parallel C7E is layer 2 = a GF wall below)
EAST = "B30"                         # slab east edge on the plot line (layer 5; no parapet north of C7F)
PARAPET_END = ("C7F", "B32")         # end of the SE-strip parapet
SOUTH = "BDC"                        # north face of the 0.20 m parapet pair BDC / BDB to the SE strip
PIERS = {                            # bay-frame piers standing on the slab (layer D on 1F; same outlines layer 5 on 2F)
    "north_pier": ("CAA", "CA8", "CA9", "CA7", "CA6", "B64", "CA5", "B63", "CA4"),
    "south_pier": ("CB2", "CB0", "CB1", "CAF", "CAE", "CAC", "CAD", "CAB", "CA2"),
    "southwest_pier": ("CA1", "CA3", "C9E"),     # C9E runs on into the SE strip: cut at the SOUTH face
}


def default_dxf():
    p = os.environ.get("T486_DXF") or str(ROOT.parent / "private" / "P7757" / "P7757.dxf")
    return p if os.path.exists(p) else None


class Drawing:
    """the entities named above, in local metres about ORIGIN (kept in memory only)."""

    def __init__(self, path):
        import hashlib
        import ezdxf
        h = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if not h.startswith(DXF_SHA256_PREFIX):
            raise ValueError("not the drawing this census was measured on (sha256 differs)")
        self.d = ezdxf.readfile(path)
        b = self.d.entitydb[ORIGIN].dxf.insert
        self.o = (b.x, b.y)

    def _p(self, v):
        return ((v[0] - self.o[0]) / 1000.0, (v[1] - self.o[1]) / 1000.0)

    def pts(self, handle, n=720):
        e = self.d.entitydb[handle]
        if e.dxftype() == "LINE":
            return [self._p(e.dxf.start), self._p(e.dxf.end)]
        c, r = self._p(e.dxf.center), e.dxf.radius / 1000.0
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        if a1 < a0:
            a1 += 360.0
        return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def chain(self, handles):
        ring = []
        for i, h in enumerate(handles):
            p = self.pts(h)
            if i == 0 and len(handles) > 1:        # orient the first piece so that it ends where the second begins
                q = self.pts(handles[1])
                if min(math.dist(p[0], q[0]), math.dist(p[0], q[-1])) < min(math.dist(p[-1], q[0]),
                                                                             math.dist(p[-1], q[-1])):
                    p = p[::-1]
            if ring and math.dist(ring[-1], p[-1]) < math.dist(ring[-1], p[0]):
                p = p[::-1]
            if ring and math.dist(ring[-1], p[0]) > 2e-3:
                raise ValueError(f"{h} does not join the chain")
            ring += p[1:] if ring else p
        return ring

    def x(self, h):
        return self.pts(h)[0][0]

    def y(self, h):
        return self.pts(h)[0][1]


def rings(dw):
    wx, ny, ex, sy = dw.x(WALL), dw.y(NORTH), dw.x(EAST), dw.y(SOUTH)
    pe_y, pe_x = dw.y(PARAPET_END[0]), dw.x(PARAPET_END[1])
    bay = dw.chain(BAY_FACE)
    bay = bay if bay[0][1] > bay[-1][1] else bay[::-1]          # top end -> apex -> bottom end
    outline = ([(wx, ny), (ex, ny), (ex, pe_y), (pe_x, pe_y), (pe_x, sy), (wx, sy)] + bay[::-1])
    piers = {}
    for k, hs in PIERS.items():
        r = dw.chain(hs)
        if k == "southwest_pier":            # C9E continues south past the parapet face: stop it there, close on the wall
            r = [p for p in r if p[1] >= sy - 1e-9] + [(r[-1][0], sy), (wx, sy)]
        piers[k] = r
    return {"wall_x": wx, "north_y": ny, "east_x": ex, "pe_y": pe_y, "outline": outline, "void": dw.chain(VOID),
            "piers": piers}


def poolcourt_geometry(dxf=None):
    """the whole slab top round the void, and its split at the wall line: east of it the slab is open to the sky; west
    of it (the bulge inside the bay's outer face) the 2F roof slab (+9.70, its east edge straight on the parapet at the
    wall line, T-062 / T-321) passes overhead: that part is under an overhang. None when the drawing is absent."""
    path = dxf or default_dxf()
    if path is None:
        return None
    from shapely.geometry import Polygon
    R = rings(Drawing(path))
    wx, ny, ex = R["wall_x"], R["north_y"], R["east_x"]
    kw = dict(footprints=list(R["piers"].values()), openings=[R["void"]],
              open_edges=[[(wx, ny), (ex, ny), (ex, R["pe_y"])]])
    g = T.zone_geometry(R["outline"], **kw)
    big = 1000.0
    g["open_sky"] = T.zone_geometry(R["outline"], clip=[(wx, -big), (big, -big), (big, big), (wx, big)], **kw)
    g["overhang"] = T.zone_geometry(R["outline"], clip=[(-big, -big), (wx, -big), (wx, big), (-big, big)], **kw)
    g["footprint_each_m2"] = {k: round(Polygon(v).area, 6) for k, v in R["piers"].items()}
    g["footprint_free_faces_lm"] = {k: round(Polygon(v).length - _on_outline(v, R["outline"]), 6)
                                    for k, v in R["piers"].items()}
    v = Polygon(R["void"]).buffer(0)
    g["void_m2"], g["void_perimeter_lm"] = round(v.area, 6), round(v.length, 6)
    g["t062_basis_m2"] = round(g["gross_m2"] - g["openings_m2"], 6)   # T-062: gross less the void, piers not deducted
    g["bay_face_lm"] = round(sum(_len(Drawing(path).pts(h)) for h in BAY_FACE), 6)
    return g


def _len(p):
    return sum(math.dist(a, b) for a, b in zip(p, p[1:]))


def _on_outline(ring, outline):
    from shapely.geometry import Polygon
    a, b = Polygon(ring), Polygon(outline)
    return a.boundary.intersection(b.boundary.buffer(1e-6)).length


def candidate_roof_lines():
    d = json.loads(LINE_INDEX.read_text())
    out = {}
    for x in d["lines"]:
        if x["item_code"] in ("FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "FIN.WP.BALCONY"):
            out[x["element_id"]] = {"line_id": x["line_id"], "item_code": x["item_code"], "class": x["class"],
                                    "qty": x["measured_net"], "unit": x["unit"]}
    return d["candidate_version"], out


def zones(dxf=None):
    ver, L = candidate_roof_lines()
    pc = poolcourt_geometry(dxf)
    os_ = (pc or {}).get("open_sky") or {}
    oh = (pc or {}).get("overhang") or {}

    def car(eid):
        x = L[eid]
        return [{"line_id": x["line_id"], "item_code": x["item_code"], "m2": x["qty"]}]
    return ver, L, pc, [
        {"zone_id": "ROOF-430", "label": "ROOF", "exposed": True, "below": "HABITABLE", "doors": 0,
         "membrane_m2": 55.560332, "upturn_lm": 35.727, "residual_tol_m2": 0.005,
         "carried": car("1F-ROOF-AT220:wp_membrane"),
         "evidence": ["ROOF label block B8D at printed +4.30 (LEVEL D20), 1.20 m below the 1F FFL +5.50",
                      "no door insert on its boundary (1F door census: 11 inserts, all inside the house walls)",
                      "under it: the GF floor plate, 100 % (T-062 shift check)",
                      "sanitary sheet 1F: SLOPE 1 % x 3 arrows to one gully + RWP T/B; one RWP F/A free discharge",
                      "own area = T-062 / T-321 hand trace 55.560 (Verifier re-multiplied)"]},
        {"zone_id": "TERRACE-550", "label": "ROOF", "exposed": True, "below": "HABITABLE", "doors": 0,
         "membrane_m2": 32.721, "upturn_lm": 52.940, "residual_tol_m2": 0.005,
         "carried": car("1F-ROOF-AT216:wp_membrane"),
         "evidence": ["ROOF label block B81 at +5.50 = the 1F FFL (living +5.50); sanitary sheet labels it ROOF",
                      "no door insert on its boundary: windows of the living / bath only; the T-321 'door closure "
                      "0.406' is the Q-25 drafting gap on a layer-D line, not a door",
                      "under it: GF floor plate 100 % (T-062)", "sanitary: SLOPE 1 % to a gully, RWP F/A free discharge",
                      "own area 18.97 x 1.30 + 1.30 x 6.20 = 32.721 (T-062)"]},
        {"zone_id": "ROOF-970", "label": "ROOF", "exposed": True, "below": "HABITABLE", "doors": 1,
         "membrane_m2": 115.814, "upturn_lm": 92.924, "residual_tol_m2": 0.05,
         "carried": car("2F-ROOF-AT379:wp_membrane"),
         "evidence": ["ROOF labels 12AA / 12C3 at +9.70 on the 2F plan; reached by the 2F roof door (its swing cuts "
                      "the finish hatch, T-321 s.2): an accessible ROOF TERRACE",
                      "under it: 145.079 of 146.532 m2 on the 1F plate (99.0 %, T-062)",
                      "dome footprints 2 x 15.359 m2 SCOPE_UNKNOWN under Q-24 / Q-29 (not this family)",
                      "own area 146.532 - 2 domes (circles) = 115.814; line deducts polygons: -0.018 named (T-321)"]},
        {"zone_id": "ROOF-1390", "label": None, "exposed": True, "below": "HABITABLE", "doors": 0,
         "membrane_m2": None, "upturn_lm": None, "carried": [{"line_id": L["2F-ROOF-TOP:wp_membrane"]["line_id"],
                                                               "item_code": "FIN.WP.ROOF", "m2": None}],
         "evidence": ["the 2F block's own roof: on no plan sheet (D-62), HELD by owner Q-34 (49.665 m2 drawing-"
                      "derived beside, T-321); no stair or door to it on any plan: a roof, not a terrace"]},
        {"zone_id": "POOLCOURT-550", "label": None, "exposed": True, "below": "EXTERIOR", "doors": 0,
         "membrane_m2": os_.get("net_m2"), "upturn_lm": os_.get("upturn_lm"),
         "open_edge_lm": (round(os_["open_edge_lm"] + os_["opening_edge_lm"], 6) if os_ else None), "carried": [],
         "evidence": ["slab top round the oval VOID (label BBF) at printed +5.50 (LEVEL 1251), no ROOF label; the part "
                      "east of the 1F wall line (open to the sky)",
                      "a slab exists: the GF roof-slab sheet slabs the pool court (T-121 / T-127 / T-154 soffit 12.834 "
                      ".. 14.704 m2, Q-68)", "under it: the GF pool court (exterior), not a habitable space",
                      "open to the sky: the 2F plan draws nothing east of the 2F parapet at the wall line (12A7 / 131B)",
                      "no door: the bay is glazed (W arcs BD2..BD5), the bath has a 0.50 m window (C33..C3E)",
                      "no parapet on the north / east edges (one layer-5 line each; the inner lines are layer 2 = GF "
                      "walls below); elevation: rounded slab nose, piers of the bay frame rise from the slab",
                      "sanitary sheet 1F: NO gully, NO RWP and NO slope arrow on this area (the other roofs have them)"]},
        {"zone_id": "POOLCOURT-550-OVERHANG", "label": None, "exposed": None, "below": "EXTERIOR", "doors": 0,
         "membrane_m2": oh.get("net_m2"), "upturn_lm": oh.get("upturn_lm"), "carried": [],
         "evidence": ["the same slab's 0.20 m ledge between the bay's outer face (BCD / BCE / BD0, r 1.935) and the void "
                      "edge (BCF, r 1.735), west of the wall line: under the 2F roof slab's straight east edge, 4.20 m "
                      "above (+5.50 to +9.70), open on the void side: covered, yet open to driven rain; no rule or print "
                      "says whether such a ledge is waterproofed: HELD (area shown, never 0)"]},
    ]


def build(dxf=None):
    ver, L, pc, zs = zones(dxf)
    c = T.census(zs)
    return {"candidate_version": ver, "candidate_lines": L, "poolcourt": pc, "census": c}


if __name__ == "__main__":
    r = build(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dxf" else None)
    print(json.dumps({"poolcourt": r["poolcourt"], "families": r["census"]["families"],
                      "rows": [{k: x[k] for k in ("zone_id", "status", "family", "function", "membrane_m2",
                                                  "carried_m2", "residual_m2", "add_m2", "flags")}
                               for x in r["census"]["rows"]]}, indent=1))
