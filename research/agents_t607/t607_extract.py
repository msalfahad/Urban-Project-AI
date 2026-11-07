"""T-607 development-villa DRAWING READ (research, unwired): every stair-family line drawn in the ST-01 stair shaft on the
GF, 1F and 2F plans of the architectural DXF (Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip, decoded into
.work/private only), classed against the merged T-412 nosing census (+ the T-598 closing-riser pair), BY HANDLE.

    .work/venv/bin/python -I research/agents_t607/t607_extract.py --dxf <P7757.dxf> --st <ST7757.dxf> --write
    .work/venv/bin/python -I research/agents_t607/t607_extract.py --dxf <P7757.dxf> --st <ST7757.dxf>   (compare)

Second drawing (Drive "ST7757 dxf.dxf", .work/private only): the riser-face lines of ST p.4 / p.5 by handle, counted per
lane, plus every other stair-family line in their windows; and the 2F diagonal face compared with ST p.5 line 648.

Question it answers (T-607): is there any drawn ST-01 front edge that the 56-riser census does not hold (a piece a
counter could add), and what is every other stair-family line in the shaft?

Method (any villa):
  * window per plan = the ST-01 census edges of that plan, widened 2.5 m;
  * stair-family line = LINE on layer 5 (solid) or 2 (above the cut / companion) whose length is a drawn ST-01 front
    length: 1150 (lane), 1258.65 / 1626.35 (the drawn turn fans), +-3 mm;
  * plans are registered to each other by WALL lines (layer 1): the translation with the most coincident wall end
    points (1 mm grid) wins; its vote count and the runner-up are recorded, never the translation (no coordinate);
  * a non-census line is classed: DUPLICATE (coincides with a census line of the same plan), SECOND_READING (coincides,
    after registration, with a census line of another plan: the same physical edge drawn twice), or UNMATCHED (a
    candidate piece: reported, never dropped).
Writes T607_DRAWN.json: handles, layers, lengths (m), angles (deg mod 180), residuals (mm), vote counts and the printed
level figures with their handles; no coordinate, no drawing text other than level figures, no client name."""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t607_rules as R  # noqa: E402

OUT = HERE / "T607_DRAWN.json"
CENSUS = ROOT / "research" / "agents_t412" / "NOSING_TABLE_T412.csv"
PLAN_OF = {"MS1-L": "GF", "MS1-T": "GF", "D1": "GF", "MS1-U": "1F", "MS2-L": "1F", "MS2-U": "2F", "MS2-TR": "2F"}
# T-598 (MERGED): the MS2-TR closing riser is drawn on the 2F plan as front 12B4 + face 12B5 (T-412 had no handle)
EXTRA_CENSUS = {"12B4": ("ST01-MS2TR-N01", "MS2-TR"), "12B5": ("ST01-MS2TR-N01", "MS2-TR"),
                # T-434 (MERGED): 49D is the riser face of the MS1-T landing nosing 2C6 (T-412 lists 2C6 alone)
                "49D": ("ST01-MS1T-N05", "MS1-T")}
STOREY = {"GF": 0, "1F": 1, "2F": 2}
# T-598 (MERGED) item 3 / Q-ST-11: the 2F diagonal pair, on one drawing only, never added
NAMED_OPEN = {"2F1F": "Q-ST-11 2F diagonal front (T-598 s.5 item 3; one drawing; never added)",
              "2F20": "Q-ST-11 2F diagonal face (T-598 s.5 item 3; one drawing; never added)"}
FAMILY = (1150.0, 1258.652, 1626.346)
TOL_LEN = 3.0
TOL_POS = 2.0
LEVELS = ("+0.30", "+1.00", "+5.50", "+9.70")
LEVEL_RE = re.compile(r"^[+\-]?\d+\.\d\d$")


def census():
    c = {}
    for r in csv.DictReader(CENSUS.open()):
        if r["stair"] != "ST-01":
            continue
        for h in r["handles"].split():
            c[h] = (r["eid"], r["flight"])
    c.update(EXTRA_CENSUS)
    return c


def lines(doc):
    out = {}
    for e in doc.modelspace().query("LINE"):
        s, t = e.dxf.start, e.dxf.end
        out[e.dxf.handle] = {"mx": (s.x + t.x) / 2, "my": (s.y + t.y) / 2, "len": math.hypot(t.x - s.x, t.y - s.y),
                             "layer": e.dxf.layer, "ang": math.degrees(math.atan2(t.y - s.y, t.x - s.x)) % 180.0,
                             "ends": ((s.x, s.y), (t.x, t.y))}
    return out


def windows(L, cen):
    w = {}
    for h, (_, fl) in cen.items():
        if h not in L:
            raise SystemExit(f"census handle {h} not in the drawing")
        p = PLAN_OF[fl]
        b = w.setdefault(p, [1e30, 1e30, -1e30, -1e30])
        b[0], b[1] = min(b[0], L[h]["mx"]), min(b[1], L[h]["my"])
        b[2], b[3] = max(b[2], L[h]["mx"]), max(b[3], L[h]["my"])
    return {p: (b[0] - 2500, b[1] - 2500, b[2] + 2500, b[3] + 2500) for p, b in w.items()}


def inside(l, b, grow=0.0):
    return b[0] - grow <= l["mx"] <= b[2] + grow and b[1] - grow <= l["my"] <= b[3] + grow


def register(L, a, b, wa, wb):
    """translation mapping plan a onto plan b by wall (layer 1) end points (R-T607-1 (b), t607_rules.register)"""
    pa = [pt for l in L.values() if l["layer"] == "1" and inside(l, wa, 3000) for pt in l["ends"]]
    pb = [pt for l in L.values() if l["layer"] == "1" and inside(l, wb, 3000) for pt in l["ends"]]
    dx, dy, hit, n1, n2 = R.register(pa, pb)
    return (dx, dy), hit, n1, n2, len(pa)


def family(l):
    return l["layer"] in ("2", "5") and any(abs(l["len"] - f) <= TOL_LEN for f in FAMILY)


def coincide(l, m, dx=0.0, dy=0.0):
    return R.coincide(l, m, dx, dy, tol_len=TOL_LEN, tol_pos=TOL_POS)


def read(path):
    import ezdxf
    doc = ezdxf.readfile(path)
    L = lines(doc)
    cen = census()
    W = windows(L, cen)
    reg = {}
    T = {("GF", "GF"): (0, 0), ("1F", "1F"): (0, 0), ("2F", "2F"): (0, 0)}
    for a, b in (("GF", "1F"), ("1F", "2F")):
        t, hit, n1, n2, npts = register(L, a, b, W[a], W[b])
        reg[f"{a}->{b}"] = {"wall_end_points": npts, "coincident": hit, "votes": n1, "runner_up_votes": n2}
        T[(a, b)] = t
        T[(b, a)] = (-t[0], -t[1])
    T[("GF", "2F")] = (T[("GF", "1F")][0] + T[("1F", "2F")][0], T[("GF", "1F")][1] + T[("1F", "2F")][1])
    T[("2F", "GF")] = (-T[("GF", "2F")][0], -T[("GF", "2F")][1])
    plans = {}
    for p, b in W.items():
        rows = []
        for h, l in sorted(L.items(), key=lambda kv: (kv[1]["ang"], kv[1]["mx"], kv[1]["my"])):
            if not (inside(l, b) and family(l)):
                continue
            r = {"handle": h, "layer": l["layer"], "length_m": round(l["len"] / 1000, 6), "angle_deg": round(l["ang"], 1)}
            if h in cen:
                r.update({"cls": "CENSUS", "edge": cen[h][0], "flight": cen[h][1]})
            elif h in NAMED_OPEN:
                r.update({"cls": "NAMED_OPEN", "why": NAMED_OPEN[h]})
            else:
                found = []
                for q in ("GF", "1F", "2F"):
                    dx, dy = T[(p, q)]
                    for k, (eid, fl) in sorted(cen.items()):
                        if PLAN_OF[fl] == q and coincide(l, L[k], dx, dy):
                            res = math.hypot(l["mx"] + dx - L[k]["mx"], l["my"] + dy - L[k]["my"])
                            found.append((q, k, eid, fl, res))
                if not found:
                    r.update({"cls": "UNMATCHED"})
                else:
                    # attribution: same plan first (DUPLICATE); else the nearest storey in the direction the line is
                    # seen (layer 2 = above the cut -> the storey above first; layer 5 = below -> the storey below)
                    up = l["layer"] == "2"

                    def key(m):
                        d = STOREY[m[0]] - STOREY[p]
                        return (abs(d), 0 if d == 0 or (d > 0) == up else 1)
                    found.sort(key=key)
                    q, k, eid, fl, res = found[0]
                    r.update({"cls": "DUPLICATE" if q == p else "SECOND_READING", "of_handle": k, "edge": eid,
                              "flight": fl, "on_plan": q, "residual_mm": round(res, 1),
                              "also_coincides": [f"{m[2]} ({m[1]}, {m[0]})" for m in found[1:]]})
            rows.append(r)
        plans[p] = rows
    lv = {}
    for e in doc.modelspace().query("TEXT"):
        t = e.dxf.text.strip()
        if t in LEVELS and LEVEL_RE.match(t):
            lv.setdefault(t, []).append(e.dxf.handle)
    return {"schema": "T607_DRAWN_V1", "source": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip (architectural "
            "DXF), read by handle; ST-01 census = research/agents_t412/NOSING_TABLE_T412.csv + T-598 12B4 / 12B5",
            "tolerances": {"length_mm": TOL_LEN, "position_mm": TOL_POS, "angle_deg": 0.5},
            "family_lengths_mm": list(FAMILY), "registration": reg, "plans": plans,
            "levels_printed": {k: sorted(v) for k, v in sorted(lv.items())}}


# structural sheets (second drawing): riser-face lines by handle (T-434 / T-598 MERGED lists + this task's sweep)
ST_SETS = {
    "ST_P4": {"east_lane_MS1U": ["25B", "25C", "261", "263", "262", "260", "267", "266", "265", "264", "270", "459"],
              "west_lane_MS1L": ["45A", "271", "26C", "26D", "26E", "26F", "268", "269", "26A", "26B", "25D", "25E"],
              "turn_radials": ["2F6", "2F4", "2F5"], "closing_face": ["2F3"]},
    "ST_P5": {"east_lane_MS2U": ["62F", "630", "635", "637", "636", "634", "63B", "63A", "639", "638", "644"],
              "west_lane_MS2L": ["646", "645", "640", "641", "642", "643", "63C", "63D", "63E", "63F", "631", "632"],
              "closing_face": ["5E2"], "diagonal_face": ["648"]},
}


def st_read(path, arch_lines):
    import ezdxf
    L = lines(ezdxf.readfile(path))
    out = {}
    for sheet, groups in ST_SETS.items():
        hs = [h for g in groups.values() for h in g]
        for h in hs:
            if h not in L or L[h]["layer"] not in ("2", "5"):
                raise SystemExit(f"{sheet}: handle {h} not a stair line")
        xs = [L[h]["mx"] for h in hs]
        ys = [L[h]["my"] for h in hs]
        b = (min(xs) - 3000, min(ys) - 3000, max(xs) + 3000, max(ys) + 3000)
        rest = sorted(h for h, l in L.items() if h not in hs and inside(l, b) and family(l))
        out[sheet] = {g: {"handles": v, "count": len(v), "lengths_m": sorted({round(L[h]["len"] / 1000, 6) for h in v})}
                      for g, v in groups.items()}
        out[sheet]["other_stair_family_lines_in_window"] = rest
    # the 2F diagonal face: arch 2F20 relative to the closing face 12B5 vs ST p.5 648 relative to 5E2 (same frame)
    va = (arch_lines["2F20"]["mx"] - arch_lines["12B5"]["mx"], arch_lines["2F20"]["my"] - arch_lines["12B5"]["my"])
    vs = (L["648"]["mx"] - L["5E2"]["mx"], L["648"]["my"] - L["5E2"]["my"])
    out["ST_P5"]["diagonal_vs_arch_2F20_mm"] = round(math.hypot(va[0] - vs[0], va[1] - vs[1]), 1)
    out["ST_P5"]["diagonal_len_equal_arch"] = abs(L["648"]["len"] - arch_lines["2F20"]["len"]) <= TOL_LEN
    return out


def main(argv):
    if "--dxf" not in argv:
        raise SystemExit("usage: t607_extract.py --dxf <P7757.dxf> --st <ST7757.dxf> [--write]")
    data = read(argv[argv.index("--dxf") + 1])
    if "--st" not in argv:
        raise SystemExit("usage: t607_extract.py --dxf <P7757.dxf> --st <ST7757.dxf> [--write]")
    import ezdxf
    arch = lines(ezdxf.readfile(argv[argv.index("--dxf") + 1]))
    data["structural"] = st_read(argv[argv.index("--st") + 1], arch)
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(text)
        print("WRITTEN", OUT.name)
    else:
        print("SAME AS COMMITTED" if OUT.exists() and OUT.read_text() == text else "DIFFERS FROM COMMITTED")


if __name__ == "__main__":
    main(sys.argv[1:])
