"""T-258 re-measure helper: the ST-01 landing / flight-edge readings of 'ST7757 dxf.dxf' (Drive, private copy) by
handle, printed as LENGTHS ONLY (no coordinates). For the Checker's own re-measure of the half landings.

    python3 -I research/agents_t258/t258_extract.py <ST7757 dxf.dxf>

Readings (drawing units mm):
  p.5 (1F roof slab plan): MS2-L riser lines 631 / 632, MS2-U first riser 62F, step line 5E2, north edge 5C0, shaft
      walls 5E3 / 5D4, well lines 62D / 62E and the well closure 633
  p.4 (GF roof slab plan): MS1-U first riser 25B, closing line 2F3, north edge 279, shaft walls 284 / 296, the last
      straight MS1-L line 25E, the winder lines 2F6 / 2F4 / 2F5, B20 faces 458 / 2C6 and the MS1-U arrival line 459
"""

from __future__ import annotations

import sys

import ezdxf

P5 = ("631", "632", "62F", "5E2", "5C0", "5E3", "5D4", "62D", "62E", "633")
P4 = ("25B", "2F3", "279", "284", "296", "25E", "2F6", "2F4", "2F5", "458", "2C6", "459")


def lines(doc, handles):
    out = {}
    for h in handles:
        e = doc.entitydb.get(h)
        if e is None or e.dxftype() != "LINE":
            raise SystemExit(f"handle {h} is not a LINE in this file")
        out[h] = (tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2])
    return out


def ys(seg):
    return seg[0][1]


def xs(seg):
    return seg[0][0]


def main(path):
    doc = ezdxf.readfile(path)
    a = lines(doc, P5)
    b = lines(doc, P4)
    mm = 1000.0
    r = {
        "p5 MS2-L going 631 -> 632": (ys(a["632"]) - ys(a["631"])) / mm,
        "p5 west landing depth 632 -> 5C0": (ys(a["5C0"]) - ys(a["632"])) / mm,
        "p5 west landing width 5E3 -> 5E2": (xs(a["5E2"]) - xs(a["5E3"])) / mm,
        "p5 east landing depth 62F -> 5C0": (ys(a["5C0"]) - ys(a["62F"])) / mm,
        "p5 east landing width 5E2 -> 5D4": (xs(a["5D4"]) - xs(a["5E2"])) / mm,
        "p5 62F -> 632 (the 0.480 reading's extra depth on the west half)": (ys(a["632"]) - ys(a["62F"])) / mm,
        "p5 well width 62D -> 62E": (xs(a["62E"]) - xs(a["62D"])) / mm,
        "p5 well closure 633 at the 62F line (offset)": (ys(a["633"]) - ys(a["62F"])) / mm,
        "p5 step line 5E2 length": abs(a["5E2"][1][1] - a["5E2"][0][1]) / mm,
        "p4 MS1-LD depth 25B -> 279": (ys(b["279"]) - ys(b["25B"])) / mm,
        "p4 MS1-LD width 2F3 -> 296": (xs(b["296"]) - xs(b["2F3"])) / mm,
        "p4 winder region width 284 -> 2F3": (xs(b["2F3"]) - xs(b["284"])) / mm,
        "p4 winder region depth 25E -> 279": (ys(b["279"]) - ys(b["25E"])) / mm,
        "p4 MS1-U arrival 459 inside B20 (2C6 - 459)": (ys(b["2C6"]) - ys(b["459"])) / mm,
        "p4 B20 band 458 -> 2C6": (ys(b["2C6"]) - ys(b["458"])) / mm,
    }
    for k, v in r.items():
        print(f"{k:70s} {v:8.3f} m")
    print(f"{'p5 west landing m3 (x 0.16)':70s} {r['p5 west landing depth 632 -> 5C0'] * r['p5 west landing width 5E3 -> 5E2'] * 0.16:8.4f}")
    print(f"{'p5 east landing m3 (x 0.16)':70s} {r['p5 east landing depth 62F -> 5C0'] * r['p5 east landing width 5E2 -> 5D4'] * 0.16:8.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
