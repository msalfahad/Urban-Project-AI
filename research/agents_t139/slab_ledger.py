"""T-139 Alsenan roof slabs panel by panel (research only, NO engine code; reads no drawing).

Input: the faces JSON written by slab_faces.py from the structural DXF (Drive "Alsenan chalet project" / "ST7757 dxf.dxf",
sha256 9f9d1179...38079). Every face was classified BY EYE on the drawing (ST7757.pdf p.4 / p.5 / p.6 at 220 dpi and the
DXF), one decision per face below; nothing here is inferred by the code. Rules:
  URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1  slab = panel area (between beam faces) x t; beams take their own footprint
  thickness                                 printed panel tag 'T 16' / 'T 18'; else ST p.8 general note 18 "roof slabs 16 cm
                                            unless otherwise stated" (read by eye this run)
  Q-44 A (owner)                            dome openings stay open (skylights), ring beam B4 stays: no slab inside
  Q-62 A cond (owner)                       stair / landing / slab concrete once: stair zones belong to the stair ledger
  UP-QTY-STATUS-001                         HELD never 0; listed with its candidate value
Usage: python -I slab_ledger.py <faces.json> <out_dir>   (writes PANELS.csv, ledger_summary.json)"""
import csv
import json
import math
import os
import sys

from shapely import wkt
from shapely.geometry import Point
from shapely.ops import unary_union

T16_NOTE = "ST p.8 note 18: roof slabs 16 cm unless otherwise stated"
SUNKEN = "hatched ANSI31 scale 2000 = legend 'Sunken slab' (depth of the drop not printed)"

# ---- slab panels: face id -> (thickness m, thickness basis, extra evidence) --------------------------------------
SLAB = {
    # GROUND FLOOR ROOF SLAB (ST p.4)
    "GF-015": (0.16, "note", SUNKEN), "GF-016": (0.16, "note", SUNKEN), "GF-018": (0.16, "note", ""),
    "GF-020": (0.16, "note", "north of the pool-court bay, B24 / B7"), "GF-027": (0.16, "note", ""),
    "GF-032": (0.16, "note", ""), "GF-039": (0.16, "note", "T.C turn column at its corner"),
    "GF-052": (0.16, "note", ""), "GF-076": (0.16, "note", ""), "GF-077": (0.16, "note", "1F arrival landing of the main "
    "stair (2.50 x 1.95) = B20 band 0.40 + 1.55 m of this panel (Q-62: slab, not stair)"), "GF-078": (0.16, "tag", ""),
    "GF-079": (0.16, "note", ""), "GF-081": (0.16, "note", SUNKEN), "GF-098": (0.16, "note", "D.C dead column inside"),
    "GF-101": (0.16, "note", ""), "GF-105": (0.16, "note", ""), "GF-124": (0.16, "note", ""), "GF-126": (0.16, "note", ""),
    "GF-128": (0.16, "note", SUNKEN), "GF-134": (0.16, "note", ""), "GF-135": (0.16, "note", ""),
    "GF-137": (0.16, "note", ""), "GF-139": (0.16, "note", ""), "GF-141": (0.16, "tag", SUNKEN),
    "GF-146": (0.16, "note", "wedge between the round-stair flight edge (tread lines stop) and B21"),
    "GF-169": (0.16, "note", ""), "GF-172": (0.16, "note", ""), "GF-173": (0.16, "note", ""), "GF-176": (0.16, "note", ""),
    # pool-court bay corners outside the B7 ring faces (T-127: 0.2343 m2): outside every beam footprint
    "GF-034": (0.16, "note", "bay corner outside the B7 ring"), "GF-036": (0.16, "note", "bay corner outside the B7 ring"),
    "GF-059": (0.16, "note", "bay corner outside the B7 ring"), "GF-061": (0.16, "note", "bay corner outside the B7 ring"),
    # FIRST FLOOR ROOF SLAB (ST p.5)
    "1F-018": (0.16, "note", SUNKEN), "1F-020": (0.16, "note", ""), "1F-023": (0.16, "note", "P.C 20x50 planted column"),
    "1F-025": (0.16, "note", ""), "1F-041": (0.16, "note", ""), "1F-057": (0.16, "note", ""), "1F-062": (0.16, "note", "2F arrival landing of the main stair "
    "(2.50 x 1.95) = B23 band 0.45 + 1.50 m of this panel (Q-62: slab, not stair)"),
    "1F-063": (0.16, "note", ""), "1F-065": (0.16, "note", ""), "1F-084": (0.16, "tag", ""), "1F-086": (0.16, "note", ""), "1F-088": (0.16, "note", ""),
    "1F-094": (0.16, "note", ""), "1F-096": (0.16, "note", ""),
    "1F-060": (0.16, "note", "west dome square corner outside the ring (r 2.4111)"),
    "1F-090": (0.16, "note", "west dome square corner outside the ring"),
    "1F-091": (0.16, "note", "east dome square corner outside the ring"),
    "1F-092": (0.16, "note", "east dome square corner outside the ring"),
    # SECOND FLOOR ROOF SLAB (ST p.6): only the water-tank / stair core is slab; the rest of the sheet is the 1F roof
    "2F-011": (0.18, "tag", "water tank, 'T 18 (T&B)'"), "2F-013": (0.18, "tag", "water tank, 'T 18'"),
    "2F-016": (0.16, "note", ""), "2F-025": (0.16, "note", "closed box (bars 5d10/m both ways), not an opening"),
    "2F-033": (0.16, "note", ""), "2F-045": (0.16, "note", ""), "2F-047": (0.16, "note", ""),
}
# dome corners that the polygonisation left inside the dome face (circle centre, inner r, outer r, face id); read from
# the 1F sheet: ARC / CIRCLE layer 1, centres (16.380, 41.651) and (30.828, 41.651), r 2.2111 (opening) / 2.4111 (ring)
DOME_SPLIT = {"1F-073": (16.380, 41.651, 2.2111, 2.4111), "1F-076": (30.828, 41.651, 2.2111, 2.4111),
              "1F-077": (30.828, 41.651, 2.2111, 2.4111)}

# ---- not slab: face id -> (class, reason) --------------------------------------------------------------------------
NOT_SLAB = {
    "GF-025": ("STAIR", "main stair zone GF->1F ('T 16', 8d16/m): flights, turn, half landing are the stair ledger's"),
    "GF-130": ("VOID+STAIR", "VOID (light well, X) with the round stair inside ('T 16' on the flight): stair ledger"),
    "GF-132": ("STAIR", "round-stair straight flight strip (tread lines cross it)"),
    "GF-131": ("STAIR", "round-stair flight edge strip"), "GF-145": ("STAIR", "round-stair flight strip"),
    "GF-048": ("OPENING", "'Open to below' X box (B1 / B14 / B7)"),
    "GF-040": ("OPENING+RING", "pool-court void 3.690 m2 inside the B7 ring + 0.391 m2 of B7 ring band (beam register "
               "BM-GF-049..052, contested piece BM-GF-060 HELD)"),
    "GF-035": ("BEAM", "B7 ring band piece"), "GF-060": ("BEAM", "B7 ring band piece"),
    "GF-014": ("NOT_SLAB", "break-line sliver west of B2 (drafting break mark), no slab"),
    "GF-063": ("EDGE_HELD", "0.20 strip north of B20 / rounded corner (beam register BM-GF-058 HELD, designer D-05)"),
    "GF-096": ("EDGE_HELD", "outer west strip 0.20 (beam register BM-GF-061 HELD, D-26)"),
    "GF-097": ("BEAM", "CB5 span 2 (printed spans 2.5 / 4.5 m; second CB5 label on this span): beam footprint, "
               "missing in the beam register"),
    "GF-011": ("BEAM", "B24 band + its east cantilever end (hatched, BM-GF-059 HELD)"),
    "GF-159": ("BEAM_HELD", "CB3 / 'B3 (With Stair)' band (BM-GF-057 HELD, Q-61 C)"),
    "GF-133": ("BEAM", "B26 65 x 85 band (beam register BM-GF-047)"),
    "GF-142": ("BEAM", "B27 90 x 85 band (beam register BM-GF-048)"),
    "GF-021": ("DETAIL", "section A-A drawing"), "GF-022": ("DETAIL", "section C-C drawing"),
    "GF-023": ("DETAIL", "section D-D drawing"),
    "1F-016": ("STAIR", "main stair zone 1F->2F ('T 16', 8d16/m): stair ledger"),
    "1F-036": ("OPENING", "X box (B1 / B7): open to below"),
    "1F-073": ("DOME_OPENING+RING", "west dome: opening r 2.2111 (Q-44 A skylight) + ring B4 band (BM-1F-028); its two "
               "east corners are slab rows below"),
    "1F-076": ("DOME_OPENING+RING", "east dome: part of the opening / ring; its two north corners are slab rows below"),
    "1F-077": ("DOME_OPENING+RING", "east dome opening + ring (BM-1F-039)"),
    "1F-043": ("EDGE_HELD", "0.20 strip north of B23, east piece (BM-1F-033 HELD, D-05)"),
    "1F-069": ("EDGE_HELD", "rounded box outside CB12 (BM-1F-037 HELD, D-26)"),
    "1F-027": ("EDGE_HELD", "strip outside CB12 0.30 (BM-1F-036 HELD, D-05)"),
    "1F-028": ("EDGE_HELD", "strip outside CB12, north part (BM-1F-036 HELD, D-05)"),
    "1F-059": ("EDGE_HELD", "outer west strip 0.20 (BM-1F-034 HELD)"), "1F-079": ("EDGE_HELD", "outer west strip"),
    "1F-093": ("EDGE_HELD", "outer west strip"),
    "2F-008": ("NOT_SLAB", "break-line sliver west of B15 (drafting break mark)"),
    "2F-031": ("EDGE_HELD", "0.10 strip west of the B15 / bearing-wall band: no tag, no bars, depth not printed"),
    "2F-058": ("NOT_THIS_SLAB", "the 1F roof seen around the core (+9.70 'ROOF', domes): measured on the 1F sheet"),
}


def classify(F):
    rows = []
    for sh in ("GF", "1F", "2F"):
        for f in F[sh]:
            fid, g = f["id"], wkt.loads(f["wkt"])
            tagged = [t for t in f["texts"] if t.startswith("T ")]
            if fid in SLAB:
                t, basis, ev = SLAB[fid]
                if basis == "tag":
                    assert tagged and abs(float(tagged[0][2:]) / 100 - t) < 1e-9, fid
                    bt = "printed panel tag '%s'" % tagged[0]
                else:
                    assert not tagged, fid
                    bt = T16_NOTE
                rows.append(dict(id=fid, floor=sh, cls="SLAB", area=f["area"], t=t, m3=round(f["area"] * t, 4),
                                 basis=bt, evidence="; ".join(x for x in [", ".join(m for m in f["texts"] if not
                                 m.startswith("T ")), ev] if x), cx=f["cx"], cy=f["cy"], w=f["w"], l=f["l"]))
                continue
            if fid in DOME_SPLIT:
                cx, cy, r_in, r_out = DOME_SPLIT[fid]
                corners = g.difference(Point(cx, cy).buffer(r_out, quad_segs=256))
                for k, c in enumerate(getattr(corners, "geoms", [corners])):
                    if c.area < 0.02:
                        continue
                    rows.append(dict(id="%s/c%d" % (fid, k), floor=sh, cls="SLAB", area=round(c.area, 4), t=0.16,
                                     m3=round(c.area * 0.16, 4), basis=T16_NOTE,
                                     evidence="dome square corner outside the ring r %.4f (split from %s)" % (r_out, fid),
                                     cx=round(c.centroid.x, 3), cy=round(c.centroid.y, 3), w="", l=""))
                rest = round(g.area - sum(r["area"] for r in rows if r["id"].startswith(fid + "/")), 4)
                rows.append(dict(id=fid, floor=sh, cls=NOT_SLAB[fid][0], area=rest, t="", m3="", basis="",
                                 evidence=NOT_SLAB[fid][1], cx=f["cx"], cy=f["cy"], w=f["w"], l=f["l"]))
                continue
            if fid in NOT_SLAB:
                cls, why = NOT_SLAB[fid]
            elif sh == "2F" and not (-20.5 < f["cx"] < -12.2 and 42.9 < f["cy"] < 50.0):
                cls, why = "NOT_THIS_SLAB", "1F roof outline / upper-roof dome repeated around the 2F core (1F sheet)"
            elif f["w"] <= 0.55 and not any("/m" in t or t.startswith("T ") for t in f["texts"]):
                cls, why = "BEAM_OR_COLUMN", "beam band / column / junction piece (width %.3f m)" % f["w"]
            elif f["w"] <= 0.55:
                cls, why = "BEAM_OR_COLUMN", "beam band crossed by a bar label (width %.3f m)" % f["w"]
            else:
                raise SystemExit("unclassified face %s %s" % (fid, f))
            rows.append(dict(id=fid, floor=sh, cls=cls, area=f["area"], t="", m3="", basis="", evidence=why,
                             cx=f["cx"], cy=f["cy"], w=f["w"], l=f["l"]))
    return rows


def main(argv=None):
    fj, out = (argv or sys.argv[1:])[:2]
    F = json.load(open(fj))
    rows = classify(F)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "PANELS.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summ = {}
    for sh in ("GF", "1F", "2F"):
        s = [r for r in rows if r["floor"] == sh and r["cls"] == "SLAB"]
        by = {}
        for r in rows:
            if r["floor"] == sh:
                by[r["cls"]] = round(by.get(r["cls"], 0) + r["area"], 4)
        summ[sh] = {"panels": len(s), "slab_m2": round(sum(r["area"] for r in s), 4),
                    "slab_m3": round(sum(r["m3"] for r in s), 4),
                    "m2_by_thickness": {str(t): round(sum(r["area"] for r in s if r["t"] == t), 4)
                                        for t in sorted({r["t"] for r in s})},
                    "sunken_m2": round(sum(r["area"] for r in s if "Sunken" in r["evidence"]), 4),
                    "area_by_class": by,
                    "all_faces_m2": round(sum(r["area"] for r in rows if r["floor"] == sh), 4)}
    summ["TOTAL"] = {"slab_m2": round(sum(summ[s]["slab_m2"] for s in ("GF", "1F", "2F")), 4),
                     "slab_m3": round(sum(summ[s]["slab_m3"] for s in ("GF", "1F", "2F")), 4)}
    # re-add check: every face classified once, classes add back to all faces
    for sh in ("GF", "1F", "2F"):
        assert abs(sum(summ[sh]["area_by_class"].values()) - summ[sh]["all_faces_m2"]) < 1e-3
        assert abs(sum(r["m3"] for r in rows if r["floor"] == sh and r["cls"] == "SLAB") - summ[sh]["slab_m3"]) < 1e-6
    json.dump(summ, open(os.path.join(out, "ledger_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
