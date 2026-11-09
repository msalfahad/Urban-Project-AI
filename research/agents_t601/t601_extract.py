"""T-601 DRAWING READ (research, unwired): every straight wall-band gap on every storey plan of the architectural DXF
(Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only), with the evidence that
decides whether it carries a leaf / frame (door, lift landing door, window) or none (doorless), the kind of each jamb
end and the printed level figures on each side. Writes T601_DRAWN.json (handles and figures only: no coordinate, no
drawing text other than level figures, no client name). The builder t601_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t601/t601_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t601/t601_extract.py --dxf <P7757.dxf>          (re-read, compare)

Method (generic; layer roles are read from this drawing's own conventions and stated in the JSON):
  * storeys: layer-1 LINE midpoints clustered along x (a jump > 8 m starts a new plan); each storey title insert (GF / FF / SF)
    takes the largest cluster within 10 m of it; other clusters (sections, elevations) are
    skipped and counted;
  * wall bands and gaps: the frozen engine.source.opening_census face_lines / wall_bands (0.09 .. 0.26 m) / band_gaps
    (min 0.50 m, columns = closed S-COL.BON polylines as jamb obstacles, every layer-1 segment as a closure); curved
    bands with opening_census.arc_bands / arc_gaps on layer-1 ARCs;
  * evidence inside the gap strip (gap length x wall thickness, widened across the band as stated per test):
      DOOR_BLOCK   an insert of a door block (name D* / d*) with >= 2 of its points strictly inside the gap (0.03 m
                   clear of each jamb) and within 0.03 m of the wall thickness (its frame / closed leaf);
      DOOR_DRAWN   a layer-D ARC (leaf swing) with radius >= 0.5 x the gap, centre within 0.10 m of the strip;
      ARCH_BLOCK   an 'arch120' insert inside the strip widened 0.20 m (an arch head, no leaf);
      GLAZING      >= 2 layer-W lines parallel to the band, inside the wall thickness, covering >= 90 % of the gap;
      PANEL_LINES  >= 3 non-wall lines parallel to the band inside the wall thickness covering >= 90 % of the gap, with
                   no glazing (a landing-door / frame symbol: the lift shaft openings);
      HEAD_LINES   layer-2 lines on both faces covering >= 90 % of the gap (a head drawn above a doorless gap);
      CROSSED      a layer-1 line not parallel to the band crossing the strip interior (two collinear wall pieces, not
                   an opening);
  * jamb ends: MASONRY_JAMB / COLUMN_JAMB as band_gaps reads them; a CLOSURE_JAMB is CONTINUOUS_FACE when a layer-1
    line collinear with the closure continues beyond a face (the jamb line is part of a cross wall's face), else
    CAPPED_END;
  * levels: the printed level figure (LEVEL-layer text) nearest to a point 0.60 m beyond each face, within 4.0 m.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
OUT = HERE / "T601_DRAWN.json"
MM = 0.001
TITLES = {"GF": "GF", "FF": "1F", "SF": "2F"}
WALL, GLAZE, HEAD, DOORL, COL = "1", "W", "2", "D", "S-COL.BON"


def _r(x, n=3):
    return round(x * MM, n)


def read(path):
    import ezdxf
    from engine.source import opening_census as OC

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    lines = [e for e in msp.query("LINE")]
    wall = [e for e in lines if e.dxf.layer == WALL]
    xs = sorted((((e.dxf.start.x + e.dxf.end.x) / 2, e) for e in wall), key=lambda q: q[0])
    clusters, cur = [], []
    for x, e in xs:
        if cur and x - cur[-1][0] > 8000:
            clusters.append(cur)
            cur = []
        cur.append((x, e))
    clusters.append(cur)
    titles = {e.dxf.name: e.dxf.insert.x for e in msp.query("INSERT") if e.dxf.name in TITLES}
    storeys, used = {}, set()
    for n, tx in sorted(titles.items()):
        near = [i for i, c in enumerate(clusters) if c[0][0] - 10000 <= tx <= c[-1][0] + 10000]
        if near:
            i = max(near, key=lambda k: len(clusters[k]))
            storeys[TITLES[n]] = (clusters[i][0][0] - 1000, clusters[i][-1][0] + 1000)
            used.add(i)
    skipped = len(clusters) - len(used)

    inserts = []
    for e in msp.query("INSERT"):
        pts = []
        try:
            for v in e.virtual_entities():
                t = v.dxftype()
                if t == "LINE":
                    pts += [(v.dxf.start.x, v.dxf.start.y), (v.dxf.end.x, v.dxf.end.y)]
                elif t == "ARC":
                    pts += [(p.x, p.y) for p in v.flattening(50)]
                elif t == "LWPOLYLINE":
                    pts += [(q[0], q[1]) for q in v.get_points()]
        except Exception:
            pts = []
        inserts.append((e.dxf.name, e.dxf.handle, (e.dxf.insert.x, e.dxf.insert.y), pts))
    levels = [(e.dxf.text.strip(), (e.dxf.insert.x, e.dxf.insert.y)) for e in msp.query("TEXT")
              if e.dxf.layer == "LEVEL"]
    arcs_d = [e for e in msp.query("ARC") if e.dxf.layer == DOORL]

    out = {"schema": "T601_DRAWN_V1", "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
           "units": "m", "layer_roles": {"wall_face": WALL, "glazing": GLAZE, "head / overhead": HEAD,
                                         "door leaf / frame": DOORL, "columns": COL},
           "clusters_skipped": skipped, "storeys": {}}
    for st in ("GF", "1F", "2F"):
        if st not in storeys:
            continue
        a0, b0 = storeys[st]

        def inx(x):
            return a0 < x < b0

        segs = [(e.dxf.handle, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)) for e in wall
                if inx(e.dxf.start.x)]
        others = [(e.dxf.handle, e.dxf.layer, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
                  for e in lines if e.dxf.layer != WALL and inx(e.dxf.start.x)]
        cols = []
        for e in msp.query("LWPOLYLINE"):
            if e.dxf.layer == COL:
                p = [(q[0], q[1]) for q in e.get_points()]
                if inx(p[0][0]):
                    cols.append((e.dxf.handle, p))
        fl = OC.face_lines(segs)
        bands = OC.wall_bands(fl, 90, 260)
        rows = []
        for bd in bands:
            u, n = bd["u"], bd["n"]
            fa, fb = sorted((bd["A"]["off"], bd["B"]["off"]))
            for g in OC.band_gaps(bd, min_gap=500, obstacles=cols, closures=segs):
                if g["state"] != OC.OPENING:
                    continue
                s0, s1, w, t = g["s0"], g["s1"], g["width"], g["t"]

                def strip(p, across=0.0, along_m=5.0):
                    s, o = OC.along(p, u), OC.along(p, n)
                    return s0 - along_m <= s <= s1 + along_m and fa - across <= o <= fb + across

                def par(a, b):
                    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
                    d = abs(ang - bd["ang"]) % 180.0
                    return min(d, 180.0 - d) <= 0.5

                def cover(ss):
                    iv = sorted((max(min(OC.along(a, u), OC.along(b, u)), s0), min(max(OC.along(a, u), OC.along(b, u)), s1))
                                for _, a, b in ss)
                    tot, end = 0.0, -1e18
                    for x0, x1 in iv:
                        if x1 <= end:
                            continue
                        tot += x1 - max(x0, end)
                        end = x1
                    return tot

                ev, ids = [], {}
                doors = [h for nm, h, _, pts in inserts if nm[:1] in "Dd" and nm[1:2].isdigit()
                         and sum(1 for p in pts if strip(p, 30, -30)) >= 2]
                if doors:
                    ev.append("DOOR_BLOCK")
                    ids["door_inserts"] = doors
                drawn = []
                for e in arcs_d:
                    c = (e.dxf.center.x, e.dxf.center.y)
                    if e.dxf.radius >= 0.5 * w and strip(c, 100):
                        drawn.append(e.dxf.handle)
                if drawn:
                    ev.append("DOOR_DRAWN")
                    ids["swing_arcs"] = drawn
                arch = [h for nm, h, ip, _ in inserts if nm == "arch120" and strip(ip, 200)]
                if arch:
                    ev.append("ARCH_BLOCK")
                    ids["arch_inserts"] = arch
                inside = [(h, a, b) for h, L, a, b in others if par(a, b) and strip(a, 1) and strip(b, 1)]
                glz = [(h, a, b) for h, a, b in [(h, a, b) for h, L, a, b in others
                                                 if L == GLAZE and par(a, b) and strip(a, 1) and strip(b, 1)]]
                if len(glz) >= 2 and cover(glz) >= 0.9 * w:
                    ev.append("GLAZING")
                    ids["glazing_lines"] = sorted(h for h, _, _ in glz)
                elif len(inside) >= 3 and cover(inside) >= 0.9 * w:
                    ev.append("PANEL_LINES")
                    ids["panel_lines"] = sorted(h for h, _, _ in inside)
                heads = [(h, a, b) for h, L, a, b in others if L == HEAD and par(a, b) and strip(a, 30) and strip(b, 30)
                         and min(abs(OC.along(a, n) - fa), abs(OC.along(a, n) - fb)) <= 30]
                on_a = [x for x in heads if abs(OC.along(x[1], n) - fa) <= 30]
                on_b = [x for x in heads if abs(OC.along(x[1], n) - fb) <= 30]
                if on_a and on_b and cover(on_a) >= 0.9 * w and cover(on_b) >= 0.9 * w:
                    ev.append("HEAD_LINES")
                    ids["head_lines"] = sorted(h for h, _, _ in heads)
                crossed = []
                for h, a, b in segs:
                    if par(a, b):
                        continue
                    sa, sb = OC.along(a, u), OC.along(b, u)
                    oa, ob = OC.along(a, n), OC.along(b, n)
                    if abs(oa - ob) < 1:
                        continue
                    for o in ((fa + fb) / 2,):
                        if min(oa, ob) <= o <= max(oa, ob):
                            s = sa + (sb - sa) * (o - oa) / (ob - oa)
                            if s0 + 30 < s < s1 - 30:
                                crossed.append(h)
                if crossed:
                    ev.append("CROSSED")
                    ids["crossing_lines"] = sorted(crossed)

                def end_kind(kind, s):
                    if kind != OC.CLOSURE_JAMB:
                        return kind
                    for h, a, b in segs:
                        if par(a, b):
                            continue
                        sa, sb = OC.along(a, u), OC.along(b, u)
                        if abs(sa - s) <= 30 and abs(sb - s) <= 30:
                            oa, ob = sorted((OC.along(a, n), OC.along(b, n)))
                            if oa < fa - 30 or ob > fb + 30:
                                return "CONTINUOUS_FACE"
                    return "CAPPED_END"

                ends = [end_kind(g["start_jamb"], s0), end_kind(g["end_jamb"], s1)]
                jh = []
                for cov in (bd["A"]["cover"], bd["B"]["cover"]):
                    jh += [ids_[0] for x0, x1, ids_ in cov if abs(x1 - s0) <= 30 or abs(x0 - s1) <= 30]
                sm = (s0 + s1) / 2
                side_lv = []
                for o in (fa - 600, fb + 600):
                    p = (sm * u[0] + o * n[0], sm * u[1] + o * n[1])
                    best = min(((math.dist(p, q), txt) for txt, q in levels if inx(q[0])), default=(1e18, None))
                    side_lv.append(best[1] if best[0] <= 4000 else None)
                rows.append({"storey": st, "jamb_face_handles": sorted(set(jh)), "width_m": _r(w), "wall_t_m": _r(t),
                             "ends": ends, "evidence": ev, "ids": ids, "levels_face_a_b": side_lv,
                             "band_angle_deg": bd["ang"]})
        arcs = []
        for e in msp.query("ARC"):
            if e.dxf.layer == WALL and inx(e.dxf.center.x):
                arcs.append((e.dxf.handle, (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, e.dxf.start_angle,
                             e.dxf.end_angle))
        curved = []
        for ab in OC.arc_bands(arcs, 90, 260):
            for g in OC.arc_gaps(ab, min_gap_mm=500):
                glz = sorted(h for h, L, a, b in others if L == GLAZE and OC.in_arc_strip(a, ab, g["a0"], g["a1"])
                             and OC.in_arc_strip(b, ab, g["a0"], g["a1"]))
                curved.append({"band": "arc band", "width_mid_arc_m": _r(g["width_mid_arc"]), "wall_t_m": _r(g["t"]),
                               "state": g["state"], "evidence": ["GLAZING"] if len(glz) >= 2 else [],
                               "glazing_lines": glz})
        rows.sort(key=lambda r: (r["jamb_face_handles"], r["width_m"]))
        out["storeys"][st] = {"gaps": rows, "curved_gaps": curved,
                              "door_inserts_on_plan": sorted(h for nm, h, ip, _ in inserts
                                                             if nm[:1] in "Dd" and nm[1:2].isdigit() and inx(ip[0])),
                              "arch_inserts_on_plan": sorted(h for nm, h, ip, _ in inserts
                                                             if nm == "arch120" and inx(ip[0]))}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    data = read(a.dxf)
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(text, encoding="utf-8")
        print("wrote", OUT.relative_to(ROOT))
        return 0
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
    print("re-read identical to T601_DRAWN.json:", same)
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
