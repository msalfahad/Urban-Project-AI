"""T-271 extractor (research only, NOT engine code): what is built over each verified floor piece of the Alsenan plans.

Room basis (r2): the floor faces of the released architectural run (ARCH_TAKEOFF_V2.9 on P7757.dxf, pickled
(boq, arch, extra) from tools.urban_boq_m9.arch_compute), i.e. the pieces the Checker re-measured as floor area
(Verifier 2026-10-23 21:15 .. 2026-10-24 01:12 and T-269), NOT the T-147 hand regions. Above each face: the roof-slab
faces of the same storey's structural slab plan (research/agents_t139/slab_faces.py on 'ST7757 dxf.dxf', classes in
research/agents_t139/PANELS.csv), moved onto the plan by the column-fit translation (research/agents_t147/scripts/
align.py; spread 0.000 m on 30 / 20 / 9 columns). Beam member: research/agents_t110/BEAM_MEMBER_REGISTER.csv (span
binding as T-147 ceil_ledger.regmatch); beam status and depth: the CONC.BEAM ledger r2 (research/agents_t252/
LEDGER_T252.csv, live rows only). Writes ONLY areas, lengths, ids, marks and statuses (no coordinates, no texts).

The GF open face GF-RC99C2A is split at the pantry box (west of the layer-5 line pair B3 / AD of the architectural
plan, the line the Checker 01:12 and T-269 used: pantry WET by owner Q-37 A) before the overlay.

Usage: python -I t271_extract.py <v29.pkl> <st_faces.json> <align.json> <arch.dxf> <out.json>"""
import csv
import json
import math
import pickle
import sys
from pathlib import Path

from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ceilings_r2 as CR  # noqa: E402

HERE = Path(__file__).resolve().parent
RES = HERE.parent
EDGE_TOL = 0.012          # m: a piece edge within 12 mm of the room face is the room face (T-147)
MIN_PIECE = 0.005         # m2
# Q-44 A dome openings: circle r 2.2111 m (p.3 dome detail diameter 442), structural sheet metres (T-110 / T-139)
DOMES = [(16.380, 41.651), (30.828, 41.651)]
DOME_R = 2.2111
PANTRY_FACE, PANTRY_LINES = "GF-RC99C2A", ["B3", "AD"]
BEAMISH = ("BEAM_OR_COLUMN", "BEAM", "BEAM_HELD", "EDGE_HELD")
OPENISH = ("OPENING", "VOID+STAIR", "DOME_OPENING+RING", "OPENING+RING", "STAIR", "NOT_THIS_SLAB", "NOT_SLAB", "DETAIL")


def _register():
    return list(csv.DictReader(open(RES / "agents_t110" / "BEAM_MEMBER_REGISTER.csv")))


def _r2():
    out = {}
    for r in csv.DictReader(open(RES / "agents_t252" / "LEDGER_T252.csv")):
        if r["status"] == "SUPERSEDED_R2":
            continue
        out.setdefault(r["member"], []).append(r)
    return out


def regmatch(reg, fl, face):
    """T-147 ceil_ledger.regmatch, unchanged in substance: register span whose midpoint lies on the face's long axis."""
    c = list(face.minimum_rotated_rectangle.exterior.coords)
    e1 = (c[1][0] - c[0][0], c[1][1] - c[0][1])
    e2 = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    L1, L2 = math.hypot(*e1), math.hypot(*e2)
    ax = e1 if L1 >= L2 else e2
    La, nw = max(L1, L2), min(L1, L2)
    ux, uy = ax[0] / La, ax[1] / La
    cx, cy = face.centroid.x, face.centroid.y
    best = None
    for r in reg:
        if r["floor"] != fl:
            continue
        try:
            x, y, Ls = float(r["x"]), float(r["y"]), float(r["length_m"])
        except ValueError:
            continue
        dx, dy = x - cx, y - cy
        along, off = abs(dx * ux + dy * uy), abs(-dx * uy + dy * ux)
        if off > 0.12 or along > Ls / 2 + La / 2 + 0.15:
            continue
        ws = []
        for tok in r["width_m"].replace("schedule", "").replace("drawn", "").split("/"):
            try:
                ws.append(float(tok))
            except ValueError:
                pass
        if ws and min(abs(w - nw) for w in ws) > 0.06 and nw > 0.12:
            continue
        k = off + along * 0.01
        if best is None or k < best[0]:
            best = (k, r)
    return best[1] if best else None


def r2_status(rows):
    if not rows:
        return "NO_R2_ROW", ""
    st = {r["status"] for r in rows}
    s = "CONFLICT" if "CONFLICT" in st else "HELD" if "HELD" in st else "CALCULATED"
    deps = sorted({r["depth_m"] for r in rows if r["depth_m"]})
    return s, "/".join(deps)


def face_geom(room):
    g = Polygon(room["polygon_m"])
    g = g if g.is_valid else g.buffer(0)
    for h in room.get("hole_polygons_m") or ():
        g = g.difference(Polygon(h))
    return g


def main(argv=None):
    a = argv or sys.argv[1:]
    boq, A, extra = pickle.load(open(a[0], "rb"))
    SF = json.load(open(a[1]))
    AL = json.load(open(a[2]))
    cls = {r["id"]: r["cls"] for r in csv.DictReader(open(RES / "agents_t139" / "PANELS.csv"))}
    reg, r2 = _register(), _r2()
    domes = [Point(*c).buffer(DOME_R, 256) for c in DOMES]
    import ezdxf
    from shapely.geometry import box as _box
    doc = ezdxf.readfile(a[3])
    pts = []
    for h in PANTRY_LINES:
        e = doc.entitydb.get(h)
        if e is None or e.dxftype() != "LINE":
            raise SystemExit(f"handle {h}: not a LINE in this drawing")
        pts += [(e.dxf.start.x * 0.001, e.dxf.start.y * 0.001), (e.dxf.end.x * 0.001, e.dxf.end.y * 0.001)]
    xb = pts[0][0]
    ylo, yhi = min(p[1] for p in pts), max(p[1] for p in pts)
    pieces = []
    for room in A["rooms"]:
        g0 = face_geom(room)
        if room["room_id"] == PANTRY_FACE:
            pbox = _box(g0.bounds[0] - 1, ylo, xb, yhi)
            pieces.append((room, room["room_id"] + "/pantry", g0.intersection(pbox), "pantry part (west of B3 / AD)"))
            pieces.append((room, room["room_id"] + "/open", g0.difference(pbox), "open room part (east of B3 / AD)"))
        else:
            pieces.append((room, room["room_id"], g0, ""))
    eng = {}
    for ln in boq["lines"]:
        if ln["item_code"] == "FIN.CEILING":
            rid = ln["location"]["room_id"]
            e = eng.setdefault(rid, {"m2": 0.0, "lines": 0, "blocked": 0})
            e["lines"] += 1
            if ln["measured_net"] is None:
                e["blocked"] += 1
            else:
                e["m2"] += float(ln["measured_net"])
    strips = []
    for ln in boq["lines"]:
        el = str(ln["location"].get("element_id") or "")
        if "-STRIP-" in el and ln["unit"] == "m2" and ln["item_code"].startswith("FIN."):
            inp = ln["calculation"]["inputs"]
            strips.append({"strip": el.split(":")[0], "floor": ln["location"]["floor"], "item": ln["item_code"],
                           "opening": inp.get("opening_id"), "kind": inp.get("opening_kind"),
                           "m2": round(float(ln["measured_net"] or 0.0), 6), "sides": inp.get("sides")})
    out = []
    for room, pid, g0, part in pieces:
        fl = room["floor"]
        g = translate(g0, *AL[fl])
        slab = []
        for f in SF[fl]:
            fg = wkt.loads(f["wkt"])
            c = cls.get(f["id"], "?")
            info = None
            if c in CR.BEAMISH:
                m = regmatch(reg, fl, fg)
                if m:
                    st, dep = r2_status(r2.get(m["member_id"]))
                    info = {"member": m["member_id"], "mark": m["mark"], "t110_status": m["status"],
                            "t110_depth": m["depth_m"], "r2_status": st, "r2_depth": dep}
            slab.append((f["id"], c, fg, info))
        rec = CR.overlay(g, slab, domes=domes)
        rec.update({"face": pid, "floor": fl, "kind": room["kind"], "name": room["name_en"], "part": part,
                    "engine_face_area_m2": round(float(room["area_m2"]), 6),
                    "engine_fin_ceiling": None if pid.endswith("/pantry") else
                    ({k: round(v, 6) for k, v in eng[room["room_id"]].items()} if room["room_id"] in eng else None)})
        out.append(rec)
    json.dump({"inputs": {"v29_faces": len(A["rooms"]), "pieces": len(out)}, "pantry_split": {"face": PANTRY_FACE, "lines": PANTRY_LINES},
               "basis": "ARCH_TAKEOFF_V2.9 floor faces x T-139 roof-slab faces (translation fit)",
               "align_m": {k: [round(v[0], 4), round(v[1], 4)] for k, v in AL.items()},
               "faces": out, "strips": strips}, open(a[4], "w"), indent=1)
    for r in out:
        print(r["face"], r["kind"], r["area_m2"], r["engine_face_area_m2"], "cov", r["covered_m2"], r["above"])


if __name__ == "__main__":
    main()
