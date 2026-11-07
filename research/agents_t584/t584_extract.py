"""T-584 development-villa DRAWING READ (research, unwired): the level change at every external door / gate and the
entrance stair E1 step fronts, read BY ENTITY HANDLE from the architectural DXF (Drive "Alsenan chalet project"
P7757_DXF_COMPRESSED.zip, decoded into .work/private only).

    .work/venv/bin/python -I research/agents_t584/t584_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t584/t584_extract.py --dxf <P7757.dxf>          (re-read, compare)

Per opening (door block insert, handle from the merged censuses T-260 / T-150 / T-175):
  * the insert's own frame (block x = along the wall, block y = across the wall: the drawn wall faces lie at y = 0 and
    y = wall depth), so mirror and rotation never change a length;
  * every LINE on layer 5 (solid) or 2 (hidden / above the cut) parallel to the wall, inside the opening span, lying ON
    a wall face (|y| <= 10 mm) or 0.050 inside it: a front edge + its 0.050 companion is the drawn step convention of
    every flight of this villa (T-412: front edge downhill, companion uphill);
  * a layer 5 / 2 line ON the face running through the whole opening (a fence or wall line drawn through a gate);
  * any parallel layer 5 / 2 line BEYOND either wall face within 2.0 m in the opening span (a step outside the door);
  * the printed level on each side: the nearest level text (or the +-0.00 datum block LEL) whose sight line from the
    opening's mid point on that face crosses no wall line (layer 1); its distance is recorded, never its position.
Writes T584_DRAWN.json (handles, lengths in m, levels as printed, distances; no coordinate, no drawing text other than
the level figures, no client name). The builder t584_alsenan.py reads only that JSON."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T584_DRAWN.json"
MM = 0.001
LEVEL_RE = re.compile(r"^[+\-]?\d+\.\d\d$")

# opening id -> (insert handle, source of the id binding)
OPENINGS = {
    "D-GF-01": ("15E", "T-260 (insert 15E, D120)"),
    "D-GF-03": ("1B5", "T-260 control (insert 1B5, d220)"),
    "D-GF-05": ("192", "T-260 (insert 192, D120)"),
    "D-GF-06": ("33E", "T-260 (insert 33E, D120)"),
    "D-GF-07": ("281", "T-260 entrance note (insert 281, D200)"),
    "D-GF-09": ("3FF", "T-260 (insert 3FF, D120)"),
    "D-2F-01": ("12BA", "own read: the only 1.00 door block (D115) of the 2F stair lobby wall; T-175 / T-150: 2F lobby "
                        "-> roof, 1.00, wall 0.150"),
    "D-GF-15": ("2D8", "own read: the D120 block in the sea-side fence line (T-175: gate 1.00 in the 7.00 fence)"),
}
# E1 front edges (T-412 NOSING_TABLE: 36E 36C 36A 30B treads, 30A platform edge), re-read here
E1_FRONTS = ["36E", "36C", "36A", "30B", "30A"]


def _xy(p):
    return float(p[0]), float(p[1])


def _cross(a, b, c, d):
    """segments ab and cd properly intersect"""
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = o(c, d, a), o(c, d, b), o(a, b, c), o(a, b, d)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def read(dxf_path):
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    levels = []
    for e in msp.query("TEXT MTEXT"):
        t = (e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).strip()
        if LEVEL_RE.match(t):
            levels.append((e.dxf.handle, t, _xy(e.dxf.insert)))
    for e in msp.query("INSERT"):
        if e.dxf.name == "LEL":      # the datum level block: its only text is the +-0.00 figure
            txt = [b.dxf.text for b in doc.blocks.get("LEL") if b.dxftype() == "TEXT"]
            assert txt == ["%%p0.00"], txt
            levels.append((e.dxf.handle, "+-0.00", _xy(e.dxf.insert)))
    walls = [(_xy(q.dxf.start), _xy(q.dxf.end)) for q in msp.query("LINE") if q.dxf.layer == "1"]
    lines = [(q.dxf.handle, q.dxf.layer, q.dxf.start, q.dxf.end) for q in msp.query("LINE")
             if q.dxf.layer in ("5", "2")]

    out = {}
    for oid, (h, src) in OPENINGS.items():
        ins = doc.entitydb.get(h)
        assert ins is not None and ins.dxftype() == "INSERT", (oid, h)
        blk = doc.blocks.get(ins.dxf.name)
        xs, ys = [], []
        for b in blk:
            if b.dxftype() == "LINE":
                xs += [b.dxf.start.x, b.dxf.end.x]
                ys += [b.dxf.start.y, b.dxf.end.y]
        assert xs, (oid, "block without lines")
        m = ins.matrix44()
        inv = m.copy()
        inv.inverse()
        span = (min(xs), max(xs))
        # wall depth from the frame jamb lines (block frame drawn across the wall at x = 0 .. 50)
        jamb = sorted({round(y, 3) for b in blk if b.dxftype() == "LINE"
                       for y in (b.dxf.start.y, b.dxf.end.y)
                       if abs(b.dxf.start.x - b.dxf.end.x) < 1e-6 and abs(b.dxf.start.x - span[0]) < 1e-6})
        on_face, beyond, through = [], [], []
        for lh, lay, s, e in lines:
            a, b = inv.transform(s), inv.transform(e)
            if abs(a.y - b.y) > 2 or abs(a.x - b.x) < 300:
                continue
            x0, x1 = min(a.x, b.x), max(a.x, b.x)
            y = (a.y + b.y) / 2
            if x0 < span[0] - 60 or x1 > span[1] + 60:
                if -10 <= y <= 10 and x0 <= span[0] + 60 and x1 >= span[1] - 60:     # a face line running through
                    through.append({"handle": lh, "layer": lay, "length_m": round((x1 - x0) * MM, 6),
                                    "covers_block_span": True})
                continue
            rec = {"handle": lh, "layer": lay, "length_m": round((x1 - x0) * MM, 6), "offset_from_face_y0_m": round(y * MM, 3)}
            if -60 <= y <= 60:
                on_face.append(rec)
            elif -2000 <= y < -60 or 60 < y <= 2000 + max(jamb or [0]):
                beyond.append(rec)
        # printed level on each side of the y = 0 face, sight line from the face mid point
        mid0 = m.transform(((span[0] + span[1]) / 2, 0, 0))
        sides = {"neg": [], "pos": []}
        for lh, t, p in levels:
            q = inv.transform((p[0], p[1], 0))
            dist = math.hypot(p[0] - mid0.x, p[1] - mid0.y)
            if dist > 6000:
                continue
            blocked = sum(1 for w in walls if _cross((mid0.x, mid0.y), p, w[0], w[1]))
            side = "neg" if q.y < 0 else "pos"
            sides[side].append({"handle": lh, "level": t, "distance_m": round(dist * MM, 3), "walls_crossed": blocked})
        for k in sides:
            sides[k].sort(key=lambda z: (z["walls_crossed"], z["distance_m"]))
        out[oid] = {"insert": h, "block": ins.dxf.name, "id_source": src,
                    "block_span_m": round((span[1] - span[0]) * MM, 3),
                    "edges_on_face": sorted(on_face, key=lambda z: (z["offset_from_face_y0_m"], z["handle"])),
                    "face_lines_through_opening": sorted(through, key=lambda z: z["handle"]),
                    "lines_beyond_face": sorted(beyond, key=lambda z: (z["offset_from_face_y0_m"], z["handle"])),
                    "levels_side_neg": sides["neg"][:3], "levels_side_pos": sides["pos"][:3]}
    e1 = []
    for h in E1_FRONTS:
        q = doc.entitydb.get(h)
        assert q.dxftype() == "LINE" and q.dxf.layer == "5", h
        (ax, ay), (bx, by) = _xy(q.dxf.start), _xy(q.dxf.end)
        e1.append({"handle": h, "layer": q.dxf.layer, "length_m": round(math.hypot(bx - ax, by - ay) * MM, 6)})
    dim = doc.entitydb.get("A06")
    e1_dim = None if dim is None else round(dim.get_measurement() * MM, 3)
    return {"schema": "T584_DRAWN_V1", "drawing": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip (architectural "
            "DXF), read by handle", "units": "m", "openings": out, "E1_fronts": e1, "E1_width_dimension_A06_m": e1_dim}


def main(argv):
    if "--dxf" not in argv:
        raise SystemExit("--dxf <P7757.dxf> required (private input, .work/private)")
    got = read(argv[argv.index("--dxf") + 1])
    txt = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(txt, encoding="utf-8")
        print(f"wrote {OUT.name}")
    else:
        print("REPRODUCED" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")


if __name__ == "__main__":
    main(sys.argv[1:])
