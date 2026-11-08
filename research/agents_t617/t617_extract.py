"""T-617 DRAWING READ (research, unwired): which structural member spans over each lift landing door, read from the
private copies (Drive "Alsenan chalet project": ST7757 dxf.dxf and P7757_DXF_COMPRESSED.zip / P7757.dxf, decoded into
.work/private only). Writes T617_DRAWN.json: handles, marks, side letters and offsets in mm relative to the shaft box
only (no absolute coordinate, no drawing text beyond beam marks, no client name). The builder reads only that JSON.

    .work/venv/bin/python -I research/agents_t617/t617_extract.py --st <ST7757 dxf.dxf> --arch <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t617/t617_extract.py --st <ST7757 dxf.dxf> --arch <P7757.dxf>  (compare)

Method (generic):
  * architectural side: for each storey's lift gap (T-608 jamb / panel handles), the side of the shaft the gap lies on
    = the side opposite the shaft cross (the drawn car symbol is inside the shaft): N / S / E / W in drawing axes;
  * structural side: each slab plan's shaft box = the S-OPENING cross (two diagonals of one square); a slab plan with
    no opening (closed roof over the shaft) takes the box of the plan above / below shifted by the sheet pitch (the
    distance between the two open boxes' sheets, verified equal to the sheet-note pitch);
  * the member on each side = the beam mark (TEXT matching B<n> / CB<n>) nearest to that side, inside the box margin,
    rotation 0 for N / S sides and 90 for E / W sides; plus the band of two parallel LINEs along that side (beam width).
Both drawings are read in their own axes; they share orientation (stair hall west of the shaft in both, verified by the
worker on the rendered plans; recorded as a reading, not inferred here).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T617_DRAWN.json"
T608 = HERE.parent / "agents_t608" / "T608_DRAWN.json"
MARK = re.compile(r"^C?B\d+$")
MARGIN = 700.0          # mm around the box in which a side's label is searched


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def crosses(msp):
    """Pairs of S-OPENING diagonals forming one square box: returns [(handles, x0, y0, x1, y1)]."""
    lines = [e for e in msp.query("LINE") if e.dxf.layer.upper() == "S-OPENING"]
    diag = []
    for e in lines:
        (ax, ay), (bx, by) = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
        if abs(bx - ax) > 500 and abs(abs(by - ay) / abs(bx - ax) - 1) < 0.05:
            diag.append((e.dxf.handle, min(ax, bx), min(ay, by), max(ax, bx), max(ay, by), (by - ay) * (bx - ax) > 0))
    out = []
    for i, a in enumerate(diag):
        for b in diag[i + 1:]:
            if a[5] != b[5] and all(abs(a[k] - b[k]) < 1 for k in (1, 2, 3, 4)):
                out.append(((a[0], b[0]), a[1], a[2], a[3], a[4]))
    return out


def side_members(msp, box):
    x0, y0, x1, y1 = box
    res = {}
    for e in msp.query("TEXT"):
        t = e.dxf.text.strip()
        if not MARK.match(t):
            continue
        x, y, r = e.dxf.insert.x, e.dxf.insert.y, round(e.dxf.rotation) % 180
        if not (x0 - MARGIN < x < x1 + MARGIN and y0 - MARGIN < y < y1 + MARGIN):
            continue
        if r == 0:
            side = "S" if y < (y0 + y1) / 2 else "N"
            d = abs(y - (y0 if side == "S" else y1))
        elif r == 90:
            side = "W" if x < (x0 + x1) / 2 else "E"
            d = abs(x - (x0 if side == "W" else x1))
        else:
            continue
        if side not in res or d < res[side]["dist_mm"]:
            res[side] = {"mark": t, "handle": e.dxf.handle, "dist_mm": round(d, 1)}
    # the beam band along the south side: horizontal lines spanning the box mid-point within 400 mm below / at y0
    band = sorted({round(e.dxf.start.y - y0, 1) for e in msp.query("LINE")
                   if abs(e.dxf.start.y - e.dxf.end.y) < 1 and y0 - 400 < e.dxf.start.y < y0 + 100
                   and min(e.dxf.start.x, e.dxf.end.x) < (x0 + x1) / 2 < max(e.dxf.start.x, e.dxf.end.x)})
    return res, band


def read_st(path):
    import ezdxf
    msp = ezdxf.readfile(path).modelspace()
    cx = sorted(crosses(msp), key=lambda c: c[1])
    if len(cx) != 2:
        raise SystemExit(f"expected 2 open shaft boxes (GF roof, 1F roof), found {len(cx)}: read the plans again")
    one, gf = cx[0], cx[1]           # sheet order in model space: 1F roof plan left of the GF roof plan (sheet notes)
    pitch = round(gf[1] - one[1], 1)
    if abs(gf[2] - one[2]) > 1 or abs((gf[3] - gf[1]) - (one[3] - one[1])) > 1:
        raise SystemExit("open boxes not stacked: stop")
    boxes = {"GF_ROOF": ("S-OPENING", gf), "1F_ROOF": ("S-OPENING", one),
             "2F_ROOF": ("CLOSED (box = 1F roof box - sheet pitch)", (None, one[1] - pitch, one[2], one[3] - pitch, one[4]))}
    out = {"sheet_pitch_mm": pitch}
    for k, (how, c) in boxes.items():
        box = c[1:5]
        sides, band = side_members(msp, box)
        out[k] = {"box_source": how, "cross_handles": list(c[0]) if c[0] else [],
                  "box_mm": [round(box[2] - box[0], 1), round(box[3] - box[1], 1)], "sides": sides,
                  "south_band_line_offsets_mm": band}
    return out


def read_arch(path):
    import ezdxf
    db = ezdxf.readfile(path).entitydb
    t608 = json.loads(T608.read_text(encoding="utf-8"))["lift_gaps"]
    out = {}
    for st, g in t608.items():
        ys = []
        for h in g["jamb_face_handles"]:
            e = db[h]
            ys += [e.dxf.start.y, e.dxf.end.y]
        cr = db[g["shaft_cross_handles"][0]]
        cy = (cr.dxf.start.y + cr.dxf.end.y) / 2
        gap_y = sum(ys) / len(ys)
        xs = [db[h].dxf.start.x for h in g["jamb_face_handles"]] + [db[h].dxf.end.x for h in g["jamb_face_handles"]]
        horizontal = all(abs(db[h].dxf.start.y - db[h].dxf.end.y) < 1 for h in g["jamb_face_handles"])
        if not horizontal:
            raise SystemExit(f"{st}: gap wall not horizontal: read by hand")
        out[st] = {"door_side": "S" if gap_y < cy else "N", "wall_span_mm": round(max(xs) - min(xs), 1),
                   "cross_handle": g["shaft_cross_handles"][0]}
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--st", required=True)
    ap.add_argument("--arch", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    data = {"schema": "T617_DRAWN_V1", "source": {"structural": "Drive 'Alsenan chalet project' / ST7757 dxf.dxf",
                                                   "architectural": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)"},
            "input_sha256": {"structural": sha256(a.st), "architectural": sha256(a.arch)},
            "structural": read_st(a.st), "architectural": read_arch(a.arch)}
    j = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if a.write:
        OUT.write_text(j, encoding="utf-8")
        print(f"wrote {OUT.name}")
        return 0
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == j
    print("re-read identical" if same else "DIFFERS from T617_DRAWN.json")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
