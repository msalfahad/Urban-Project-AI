"""T-444 Alsenan run: the ground-slab cell around the lift shaft (L-41cfb82e, engine cell SITE-c1089bdb, HELD
'1 free-standing column(s) inside a ground-slab cell') bound to its own pieces.

    .work/venv/bin/python -I research/agents_t444/t444_alsenan.py --dxf "<.work/private>/ST7757 dxf.dxf" \
        --geometry <.work/private>/t444/geometry.json [--write]
    .work/venv/bin/python -I research/agents_t444/t444_alsenan.py --check     # no private input: committed tables re-add

Inputs: the structural DXF (sha 9f9d1179, Drive 'Alsenan chalet project', title 'ST7757 dxf.dxf'); the T-391 own
partition rebuilt with the merged extractor (asserted face by face against OWN_GROUND_T391.json); route G's own plan
records of the same DXF (research/agents_t387/t387_geometry.py, written to .work/private only), registered onto the DXF
by the pit ring (route G SH08 ring box from the shaft openings, T-401 `sheet_rings`, = S-BW 7C2 2.200 x 2.200).
Written: values in m2 / m3, sizes in m, DXF handles and engine ids; no coordinates, no names.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t391", ROOT / "research" / "agents_t401"):
    sys.path.insert(0, str(p))
import t444_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OWN = ROOT / "research" / "agents_t391" / "OWN_GROUND_T391.json"
LINES = ROOT / "research" / "agents_t347" / "CANDIDATE_V3024_BURIED_LINES.json"
PIECES = HERE / "PIECES_T444.json"
SUMMARY = HERE / "summary_t444.json"
T_SLAB = 0.10          # 'T=10cm' GROUND BEAMS PLAN (T-206 DRAWING-CONFIRMED; route G t_basis SHEET_UNIFORM)
FP_DX = 117654.3026476346 - 78929.89653886131   # T-141 frames: FOUNDATION PLAN -> GROUND BEAMS PLAN (same size)
CELL = "SITE-c1089bdb4cfcdc4a"
GS_LINE = "L-41cfb82ed733f4d6e3a5"
CELL_FACES = ("OWN-007", "OWN-009", "OWN-010", "OWN-020", "OWN-047", "OWN-060", "OWN-065", "OWN-082", "OWN-083",
              "OWN-086", "OWN-099", "OWN-114", "OWN-151", "OWN-174")       # T-391 binding (> half of each face)
# own kind -> T-444 kind; T-401 P4: the three 0.20 'BEAM' faces on the S-BW ring are the pit ring, not ground beams
RING_FACES = ("OWN-082", "OWN-083", "OWN-086", "OWN-094")
OWNER_LINE = {"PANEL": GS_LINE, "SHAFT": "L-1590b76b2fe8f131dc07 (raft FF; pit floor = raft top, no volume)",
              "RING": "LIFT_PIT:WALLS (T-397 HELD blank; height: pit depth RFI L-1 + GF build-up)",
              "BEAM:OWN-060": "L-c5902fd02c58b85a5df1 (BAND0028)", "BEAM:OWN-065": "L-361f5e913c566c4fe2b5 (BAND0036.1)",
              "COLUMN": "C9 (S-COL.BON 1EC = FP 1090): neck L-953e87a3, GF column L-7b41af57 (T-401)"}
# T-436 parts and T-442's GS line (other GS owners) and the lift-pit ledger faces: must be disjoint from the GS pieces
T436_FACES = ("OWN-011", "OWN-018", "OWN-006", "OWN-022", "OWN-025")
FP_SOLIDS = {"1B2B": "raft FF (lift base, 4.60 x 4.50 x 0.55, founding level)",
             "1ABF": "footing outline (founding level)", "1B19": "footing F6 (founding level)",
             "1B08+1B09": "strap SB2 (founding level, T-141)"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def t444_kind(face):
    if face["face"] in RING_FACES:
        return "RING"
    return {"PANEL": "PANEL", "LIFT": "SHAFT", "BEAM": "BEAM", "COLUMN": "COLUMN"}[face["kind"]]


def measure(dxf, geometry):
    import ezdxf
    import shapely.affinity as A
    from ezdxf import bbox as BB
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import unary_union
    import t391_extract as X
    import t401_alsenan as T401

    if _sha(dxf) != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    out, _ = X.read(dxf)
    own = {f["face"]: f for f in json.loads(OWN.read_text(encoding="utf-8"))["faces"]}
    for r in out:
        if abs(r["area_m2"] - own[r["face"]]["area_m2"]) > 1e-4 or r["kind"] != own[r["face"]]["kind"]:
            raise SystemExit(f"{r['face']}: T-391 partition not reproduced")
    F = {r["face"]: r for r in out}
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb

    # ---- route G cell registered by the pit ring
    geo = json.loads(Path(geometry).read_text(encoding="utf-8"))
    ring_g = T401.sheet_rings(geo)["SH08"]
    xs = [p[0] for p in db["7C2"].get_points("xy")]
    ys = [p[1] for p in db["7C2"].get_points("xy")]
    if abs((max(xs) - min(xs)) - (ring_g[2] - ring_g[0])) > 1 or abs((max(ys) - min(ys)) - (ring_g[3] - ring_g[1])) > 1:
        raise SystemExit("ring 7C2 and the route G SH08 ring differ in size: registration refused")
    dx, dy = min(xs) - ring_g[0], min(ys) - ring_g[1]
    cell = [f for f in geo["sheets"]["SH08"]["slab"]["faces"] if f["face_id"] == CELL][0]
    outer = A.translate(Polygon(cell["polygon"]).buffer(0), dx, dy)
    holes = [A.translate(Polygon(h).buffer(0), dx, dy) for h in cell.get("hole_polygons", [])]
    beams_g = {}
    for b in geo["sheets"]["SH08"].get("beams", []):
        Q = A.translate(Polygon(b["polygon"]).buffer(0), dx, dy)
        if Q.intersection(outer).area > 1e2:
            beams_g[b["band_id"]] = round(Q.intersection(outer).area / 1e6, 4)
    gross = outer.difference(unary_union(holes)) if holes else outer
    engine = {"area_gross_m2": round(cell["area_gross_m2"], 4), "member_overlap_m2": round(cell["member_overlap_m2"], 4),
              "net_m2": round(cell["area_m2"], 4), "t_m": cell["t_m"], "region_reason": cell["region_reason"],
              "free_columns": len(cell.get("free_columns") or []),
              "outline_without_holes_m2": round(outer.area / 1e6, 4),
              "holes_m2": round(sum(h.area for h in holes) / 1e6, 4), "beams_in_cell_m2": beams_g,
              "registered_gross_m2": round(gross.area / 1e6, 4)}

    # ---- piece table: every own face the cell or the T-391 binding touches
    faces = sorted({f for f in CELL_FACES} | {k for k, r in F.items() if r["_g"].intersection(outer).area > 1e2})
    pieces = []
    for fid in faces:
        r = F[fid]
        g = r["_g"]
        b = g.bounds
        kind = t444_kind(own[fid])
        fp = {}
        for h, name in (("1B2B", "1B2B"), ("1ABF", "1ABF"), ("1B19", "1B19")):
            P = A.translate(Polygon(list(db[h].get_points("xy"))), -FP_DX, 0)
            a = g.intersection(P).area / 1e6
            if a > 1e-4:
                fp[name] = round(a, 4)
        sb2 = Polygon([tuple(db["1B08"].dxf.start)[:2], tuple(db["1B08"].dxf.end)[:2],
                       tuple(db["1B09"].dxf.end)[:2], tuple(db["1B09"].dxf.start)[:2]])
        sb2 = A.translate(sb2.buffer(0), -FP_DX, 0)
        if g.intersection(sb2).area / 1e6 > 1e-4:
            fp["1B08+1B09"] = round(g.intersection(sb2).area / 1e6, 4)
        owner_line = OWNER_LINE.get(f"{kind}:{fid}", OWNER_LINE.get(kind))
        pieces.append({"face": fid, "kind": kind, "own_kind_T391": own[fid]["kind"], "host": own[fid]["host"],
                       "edge_handles": own[fid]["edge_handles"], "area_m2": r["area_m2"],
                       "bbox_m": [round((b[2] - b[0]) / 1e3, 3), round((b[3] - b[1]) / 1e3, 3)],
                       "rectangle": abs(g.area - (b[2] - b[0]) * (b[3] - b[1])) < 2e3,
                       "in_T391_binding": fid in CELL_FACES,
                       "in_engine_outline_m2": round(g.intersection(outer).area / 1e6, 4),
                       "in_engine_gross_m2": round(g.intersection(gross).area / 1e6, 4),
                       "t_m": T_SLAB if kind == "PANEL" else None,
                       "m3": round(r["area_m2"] * T_SLAB, 6) if kind == "PANEL" else None,
                       "owner": R.OWNER[kind], "owner_line": owner_line,
                       "foundation_plan_below_m2": fp})

    # ---- what each slab panel carries (stair hall: treads, levels; any void / pit / base drawn?)
    contents = {}
    for p in pieces:
        if p["kind"] != "PANEL":
            continue
        g = F[p["face"]]["_g"].buffer(-5)
        rec = {"hidden_layer2_lines": [], "layer5_lines": [], "level_marks": []}
        for e in doc.modelspace():
            if e.dxftype() == "RTEXT":
                continue
            try:
                bb = BB.extents([e])
            except Exception:
                continue
            if not bb.has_data:
                continue
            c = Point(bb.center.x, bb.center.y)
            if e.dxftype() == "LINE" and e.dxf.layer in ("2", "5"):
                L = LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])
                if g.intersects(L):
                    rec["hidden_layer2_lines" if e.dxf.layer == "2" else "layer5_lines"].append(e.dxf.handle)
            elif e.dxftype() == "TEXT" and e.dxf.layer == "LEVEL" and g.contains(c):
                rec["level_marks"].append({"handle": e.dxf.handle, "text": e.dxf.text})
        contents[p["face"]] = rec
    # foundation plan: any outline under the cell other than footings / raft / straps / rings / columns
    U = unary_union([F[f]["_g"] for f in CELL_FACES])
    fp_other = []
    for e in doc.modelspace().query("LWPOLYLINE"):
        try:
            bb = BB.extents([e])
        except Exception:
            continue
        if not bb.has_data or bb.size.x > 12000:
            continue
        P = box(bb.extmin.x - FP_DX, bb.extmin.y, bb.extmax.x - FP_DX, bb.extmax.y)
        if P.intersection(U).area > 1e3:
            fp_other.append({"handle": e.dxf.handle, "layer": e.dxf.layer,
                             "size_m": [round(bb.size.x / 1e3, 3), round(bb.size.y / 1e3, 3)],
                             "under_cell_m2": round(P.intersection(U).area / 1e6, 4)})
    return pieces, engine, contents, fp_other


def tables(pieces, engine):
    """Re-adds and the lane I proposal from the piece table (no private input needed)."""
    bound = [p for p in pieces if p["in_T391_binding"]]
    by_kind = {k: round(sum(p["area_m2"] for p in bound if p["kind"] == k), 6) for k in R.KINDS}
    own_total = R.readd([{"area_m2": p["area_m2"]} for p in bound], sum(by_kind.values()))
    eng_out = {k: round(sum(p["in_engine_outline_m2"] for p in pieces if p["kind"] == k), 6) for k in R.KINDS}
    eng_gross = {k: round(sum(p["in_engine_gross_m2"] for p in pieces if p["kind"] == k), 6) for k in R.KINDS}
    R.readd([{"area_m2": v} for v in eng_out.values()], engine["outline_without_holes_m2"])
    R.readd([{"area_m2": v} for v in eng_gross.values()], engine["area_gross_m2"])
    if abs(engine["outline_without_holes_m2"] - engine["holes_m2"] - engine["area_gross_m2"]) > R.TOL:
        raise SystemExit("engine outline - holes != engine gross")
    if abs(eng_gross["BEAM"] - engine["member_overlap_m2"]) > R.TOL:
        raise SystemExit("engine member overlap is not the two ground-beam strips")
    eng_net = dict(eng_gross, BEAM=0.0)
    prop = R.proposal(GS_LINE, [{"id": p["face"], "kind": p["kind"], "area_m2": p["area_m2"]} for p in bound],
                      T_SLAB, engine["net_m2"], eng_net)
    R.owners([{"id": p["face"], "kind": p["kind"], "area_m2": p["area_m2"]} for p in pieces],
             {"LIFT_PIT_FLOOR=RAFT_TOP": ["OWN-020"], "LIFT_PIT_WALLS": list(RING_FACES),
              "GROUND_SLAB": [], })
    gs = [p["face"] for p in pieces if p["kind"] == "PANEL"]
    if set(gs) & set(T436_FACES):
        raise SystemExit("a GS piece of this cell is also a T-436 part: double")
    return {"own_bound_by_kind_m2": by_kind, "own_bound_total_m2": own_total,
            "engine_outline_by_kind_m2": eng_out, "engine_gross_by_kind_m2": eng_gross,
            "engine_net_by_kind_m2": eng_net, "proposal": prop}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--geometry")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        d = json.loads(PIECES.read_text(encoding="utf-8"))
        t = tables(d["pieces"], d["engine"])
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if json.dumps(t, sort_keys=True) != json.dumps(s["tables"], sort_keys=True):
            raise SystemExit("summary tables do not follow from the committed pieces")
        print("check: pieces re-add; proposal", t["proposal"]["to"])
        return 0
    pieces, engine, contents, fp_other = measure(a.dxf, a.geometry)
    t = tables(pieces, engine)
    doc = {"schema": "T444_PIECES_V1", "structural_sha256": DXF_SHA, "frame": "T-141 GROUND BEAMS PLAN + FOUNDATION PLAN",
           "cell": CELL, "line": GS_LINE, "engine": engine, "pieces": pieces, "panel_contents": contents,
           "foundation_plan_outlines_under_cell": fp_other}
    summ = {"task": "T-444", "tables": t, "foundation_solids_named": FP_SOLIDS, "t436_faces_disjoint": list(T436_FACES)}
    print(json.dumps(t, indent=1))
    if a.write:
        PIECES.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        SUMMARY.write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps({"engine": engine, "contents": contents, "fp_other": fp_other}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
