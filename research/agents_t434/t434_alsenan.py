"""T-434 development-villa reading of the ST-01 GF winder turn MS1-T (Alsenan is one sample; method winder_turn.py).

Build (needs PRIVATE inputs decoded into .work/private only: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip
(architectural DXF), "ST7757 dxf.dxf" (structural DXF) and p7757_arch_sheet10.pdf (section A-A)):
    python3 -I research/agents_t434/t434_alsenan.py --dxf <P7757.dxf> --st <ST7757.dxf> --pdf <sheet10.pdf> --write
reads every line BY HANDLE, asserts layer / position / length, converts to run positions and lengths relative to the
turn (metres; no drawing coordinates), scales the section's dashed winder treads from the raster against the two printed
finished levels (+0.30 and +3.50, the printed '320'), and writes ALSENAN_TURN_T434.json. Check (no private input):
    python3 -I research/agents_t434/t434_alsenan.py --check
recomputes the reading table, the governing count and the turn quantities from the committed JSON: REPRODUCED.
No drawing text, client name, image or freelancer row text is written; freelancer piece counts are quantities only.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import winder_turn as W  # noqa: E402

MM = 0.001
OUT = HERE / "ALSENAN_TURN_T434.json"

# Printed finished levels (section A-A '+0.30' + '320' = +3.50 half landing; GF FFL +1.00; 1F +5.50): T-184 / Q-46.
FFL_GF = 1.00
LANDING = 3.50
# Main-stair (ST-01 incl. D1) risers per drawn reading, as merged (Q-46 problem statement, T-184, T-412): used only for
# the freelancer reach test. GF->1F: section 27, arch plan 25, ST p.4 28; 1F->2F: section 25, arch 1F 27, ST p.5 24;
# D1 4 on every sheet.
MAIN_STAIR_RANGES = {"GF->1F": (25, 28), "1F->2F": (24, 27), "D1": (4, 4)}
FREELANCER_ST01_PIECES = 63            # T-412 s.5 (quantity only)
DRAWN_ST01_RISERS = 56                 # section A-A (Q-46 A): 27 + 25 + D1 4


def _dxf(path):
    import ezdxf
    msp = ezdxf.readfile(path).modelspace()
    return {e.dxf.handle: e for e in msp if e.dxftype() == "LINE"}


def _ln(H, h, layer=None):
    e = H[h]
    if layer is not None:
        assert e.dxf.layer == layer, (h, e.dxf.layer)
    a, b = e.dxf.start, e.dxf.end
    return (a.x, a.y), (b.x, b.y)


def read_cad(arch, st):
    A = _dxf(arch)
    S = _dxf(st)
    # ---- architectural GF plan: MS1-L fronts (west lane, ascending +y), the turn and its landing edge
    (x0, yDC), (x1, _) = _ln(A, "DC", "5")
    (_, y485), (_, _) = _ln(A, "485", "2")
    (_, y486), _ = _ln(A, "486", "2")
    (_, yc4), _ = _ln(A, "C4", "2")
    assert abs(yc4 - y485) < 1 and abs(y486 - y485 - 50) < 1         # 485 drawn twice (C4); 486 = its riser face
    xw, xi = min(x0, x1), max(x0, x1)                                  # west wall face, inner (well) edge of the lane
    assert abs((xi - xw) * MM - 1.150) < 1e-6
    fronts = ["DC", "DD", "CE", "CF", "C6", "C7", "C9", "C8", "C5", "485"]
    s = []
    for h in fronts:
        (_, y), _ = _ln(A, h)
        s.append(round((y - y485) * MM, 6))
    assert s == [round(-2.7 + 0.3 * i, 6) for i in range(10)], s       # 10 straight fronts at 0.300, the 10th = 485
    rad = {}
    ends = {}
    for h, comp in (("4A2", "4A3"), ("49E", "49F"), ("4A0", "4A1")):
        (ax, ay), (bx, by) = _ln(A, h, "2")
        assert abs(ax - xi) < 1 and abs(ay - y486) < 1, h                # every radial leaves the inner corner
        rad[h] = round(math.hypot(bx - ax, by - ay) * MM, 6)
        ends[h] = (round((bx - xi) * MM, 6), round((by - y486) * MM, 6))
    (xe, ye0), (_, ye1) = _ln(A, "2C6", "2")
    (xe2, _), _ = _ln(A, "49C", "2")
    (xf, yf0), (_, yf1) = _ln(A, "49D", "2")
    assert abs(xe - xe2) < 1                                           # 2C6 drawn twice (49C): one edge
    assert abs((xf - xe) * MM - 0.050) < 1e-6                          # front 2C6 + riser face 49D 0.050 uphill (east)
    ynorth = max(ye0, ye1)
    assert abs(min(ye0, ye1) - y486) < 1 and abs((ynorth - y486) * MM - 1.150) < 1e-6
    for h in ("26E", "2AB"):                                           # north wall face of the turn
        (p, q), (r, t) = _ln(A, h, "1")
        assert abs(q - ynorth) < 1 and abs(t - ynorth) < 1
    # no line separates the 0.100 head strip (inner edge .. 2C6, north of 486) from the last winder
    for h, e in A.items():
        (ax, ay), (bx, by) = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
        if abs(ax - xi) < 1 and abs(bx - xi) < 1 and min(ay, by) > y486 + 1 - 1e-9 and max(ay, by) <= ynorth + 1:
            raise AssertionError(f"line {h} on the inner edge north of 486")
    region = [(-1.150, -0.050), (0.0, -0.050), (0.0, 0.0), (round((xe - xi) * MM, 6), 0.0),
              (round((xe - xi) * MM, 6), 1.150), (-1.150, 1.150)]       # front 485 .. front 2C6, relative to the corner
    # ---- structural GF roof slab plan (ST p.4): riser-face lines (layer 2) 45A .. 25E, radials, closing 2F3
    (sx0, sy45), (sx1, _) = _ln(S, "45A", "2")
    (_, sy25), _ = _ln(S, "25E", "2")
    sxi = max(sx0, sx1)
    dx, dy = xi - sxi, y486 - sy25                                     # 25E = arch 486 (both riser faces)
    st_rad = {}
    for h, ah in (("2F6", "4A3"), ("2F4", "49F"), ("2F5", "4A1")):     # ST radials = arch radial riser faces
        (ax, ay), (bx, by) = _ln(S, h, "2")
        (cx, cy), (ex, ey) = _ln(A, ah)
        assert abs(ax + dx - cx) < 1 and abs(ay + dy - cy) < 1 and abs(bx + dx - ex) < 1 and abs(by + dy - ey) < 1, h
        st_rad[h] = round(math.hypot(bx - ax, by - ay) * MM, 6)
    (sx3, _), _ = _ln(S, "2F3", "2")
    assert abs(sx3 + dx - xf) < 1                                      # ST closing riser = arch riser face 49D
    st_face_foot = round((sy45 - sy25) * MM, 6)                        # -3.300 from the 10th arch riser face
    assert abs(st_face_foot + 3.300) < 1e-6
    return {
        "arch_ms1l_front_s_m": s, "lane_m": 1.150, "radial_fronts_m": rad, "radial_end_rel_corner_m": ends,
        "landing_edge": {"handles": ["2C6", "49C (same line)", "49D (riser face)"], "len_m": 1.150,
                         "offset_from_corner_m": round((xe - xi) * MM, 6), "riser_face_offset_m": 0.050},
        "st_p4": {"face_lines": 12, "face_foot_rel_486_m": st_face_foot, "radials_m": st_rad,
                  "radials_equal_arch_riser_faces": True, "closing_face_equals_arch_49D": True},
        "region_polygon_rel_corner_m": region,
    }


def read_section(pdf):
    """Scale the dashed winder treads below the half landing of section A-A from a 800 dpi raster against the two
    printed finished-level lines (+3.50 landing and +0.30 lobby; printed '320'). Indicative (scaled), never a quantity."""
    import numpy as np
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "800", "-png", "-x", "2300", "-y", "6000", "-W", "3400", "-H", "2400",
                        pdf, f"{td}/s"], check=True)
        im = Image.open(next(Path(td).glob("s*.png"))).rotate(90, expand=True)
        a = np.array(im.convert("L")) < 128
    x = 1992                                                            # the '320' dimension line column
    def runs(rows):
        out, start, prev = [], None, None
        for y in rows:
            if start is None:
                start = prev = y
            elif y == prev + 1:
                prev = y
            else:
                out.append((start, prev)); start = prev = y
        if start is not None:
            out.append((start, prev))
        return out
    lv = [y for y in range(2100, 3400) if a[y, x - 200:x - 5].sum() > 100]
    rr = runs(lv)
    top = [r for r in rr if r[0] < 2300][0]                             # +3.50 finished line (first thin line)
    bot = [r for r in rr if 3150 < r[0] < 3260][0]                      # +0.30 finished line
    ytop, ybot = (top[0] + top[1]) / 2, (bot[0] + bot[1]) / 2
    pxm = (ybot - ytop) / 3.20
    dash = [y for y in range(2300, 2520) if 150 < a[y, 1730:2060].sum() < 300]
    dr = runs(dash)
    levels = [round(LANDING - ((r0 + r1) / 2 - ytop) / pxm, 4) for r0, r1 in dr]
    return {"px_per_m": round(pxm, 2), "dashed_tread_levels_m": sorted(levels),
            "note": "scaled (indicative); the fifth winder at +3.333 would lie on the cut landing slab's soffit line"}


def readings(data):
    sec = tuple(data["section"]["dashed_tread_levels_m"])
    arch_foot = data["cad"]["arch_ms1l_front_s_m"][0]
    st_foot = round(data["cad"]["st_p4"]["face_foot_rel_486_m"] + 0.0, 6)   # face vs face: same reference shift
    return [
        W.Reading("SECTION_A_A", "section", 10, 5, foot_s=data["section_foot_s_m"], going=0.300),
        W.Reading("ARCH_GF_PLAN", "arch_plan", 10, 4, foot_s=arch_foot, going=0.300),
        W.Reading("ST_P4", "structural_plan", 12, 4, foot_s=st_foot, going=0.300),
    ], sec


def compute(data):
    rs, sec = readings(data)
    g = W.governing(rs, FFL_GF, LANDING, owner_rule_source="section", section_levels=sec)
    cad = data["cad"]
    td = W.TurnDrawing(
        winder_fronts=[(h, v, "drawn") for h, v in cad["radial_fronts_m"].items()],
        landing_edge_m=cad["landing_edge"]["len_m"],
        landing_edge_drawings=("ARCH_GF 2C6 / 49D", "ST_P4 2F3"),
        region_polygon=[tuple(p) for p in cad["region_polygon_rel_corner_m"]])
    q = W.turn_quantities(g["turn_risers"], td)
    lo, hi = W.reach(MAIN_STAIR_RANGES)
    fl = {"freelancer_pieces": FREELANCER_ST01_PIECES, "drawn_risers": DRAWN_ST01_RISERS,
          "reach_of_drawn_readings": [lo, hi],
          "verdict": "NOT_A_DRAWN_READING" if not lo <= FREELANCER_ST01_PIECES <= hi else "WITHIN_READINGS"}
    return {"governing": g, "turn": q, "freelancer": fl}


def main(argv):
    if "--check" in argv:
        data = json.loads(OUT.read_text())
        res = compute(data)
        assert json.loads(json.dumps(res)) == data["result"], "result differs from the committed one"
        print("REPRODUCED", res["governing"]["governing"], res["governing"]["turn_risers"],
              res["turn"]["landing_edge"]["status"], res["turn"]["tread_marble"]["beside_m2"])
        return 0
    arg = dict(zip(argv[::2], argv[1::2])) if "--write" not in argv else dict(
        zip([a for a in argv if a != "--write"][::2], [a for a in argv if a != "--write"][1::2]))
    data = {"schema": "t434.turn.v1", "units": "m", "flight": "ST-01 MS1-T (GF winder turn +2.667 -> +3.50)",
            "cad": read_cad(arg["--dxf"], arg["--st"]), "section": read_section(arg["--pdf"]),
            # foot of MS1-L in section A-A, scaled (research/alsenan_stairs_s8_7c 01_SOURCE_EVIDENCE_REGISTER S-04:
            # 16728 vs the arch plan's 16761.856 in that frame): -2.700 - 0.034 relative to the 485 front
            "section_foot_s_m": round(-2.700 - (16761.856 - 16728) * MM, 6)}
    data["result"] = json.loads(json.dumps(compute(data)))
    if "--write" in argv:
        OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(json.dumps(data["result"]["governing"]["table"], indent=1))
    print(json.dumps(data["result"]["turn"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
