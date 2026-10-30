"""T-352 re-measure helper: the stair-side primitives of 'ST7757 dxf.dxf' (Drive 'Alsenan chalet project', private
copy, sha256 9f9d1179...) by handle, printed as RELATIVE LENGTHS ONLY (no coordinates leave this script).

    python3 -I research/agents_t352/t352_extract.py <ST7757 dxf.dxf>

p.4 ST-01: walls 284 / 296, well 256 / 25A (S-OPENING), MS1-L 45A .. 25E, MS1-U 25B .. 459, B20 face 2C6, landing
edge 279, turn 2F3, winder lines 2F6 / 2F4 / 2F5. p.5 ST-01: walls 5E3 / 5D4, well 62D / 62E / 633, MS2-L 646 .. 632,
MS2-U 62F .. 644, B23 face 5E1, step line 5E2, north edge 5C0. p.4 ST-02: B3 face 283 (band 27E), light-well edge 2D0,
RS-S 2BA .. 2C4, RS-A 2C8 .. 315, lane edge 2CF, free edge 289 (nothing drawn within 0.6 m beyond it but the slab wedge
GF-146), column 374. Requires ezdxf (the pinned venv)."""

from __future__ import annotations

import math
import sys

import ezdxf


def main(path: str) -> int:
    doc = ezdxf.readfile(path)

    def s(h):
        e = doc.entitydb.get(h)
        if e is None or e.dxftype() != "LINE":
            raise SystemExit(f"handle {h} is not a LINE in this file")
        return e.dxf.start.x / 1000, e.dxf.start.y / 1000, e.dxf.end.x / 1000, e.dxf.end.y / 1000

    def ln(h):
        p, q, r, t = s(h)
        return math.hypot(r - p, t - q)

    X = lambda h: s(h)[0]
    Y = lambda h: s(h)[1]
    Ylo = lambda h: min(s(h)[1], s(h)[3])
    out = {
        "p4 west lane 284 -> well 256": X("256") - X("284"),
        "p4 well 256 -> 25A": X("25A") - X("256"),
        "p4 east lane 25A -> 296": X("296") - X("25A"),
        "p4 well length 256": ln("256"),
        "p4 well start - B20 face 2C6": Ylo("256") - Y("2C6"),
        "p4 MS1-L 45A -> 25E (B: 12 lines)": Y("25E") - Y("45A"),
        "p4 MS1-L head 25E - well end": Y("25E") - (Ylo("256") + ln("256")),
        "p4 MS1-U 25B -> 459": Y("25B") - Y("459"),
        "p4 MS1-U 25B -> B20 face 2C6 (stair-owned)": Y("25B") - Y("2C6"),
        "p4 MS1-LD 25B -> 279": Y("279") - Y("25B"),
        "p4 winder 2F6": ln("2F6"), "p4 winder 2F4": ln("2F4"), "p4 winder 2F5": ln("2F5"), "p4 closing 2F3": ln("2F3"),
        "p5 west lane 5E3 -> well 62D": X("62D") - X("5E3"),
        "p5 well 62D -> 62E": X("62E") - X("62D"),
        "p5 east lane 62E -> 5D4": X("5D4") - X("62E"),
        "p5 MS2-L 646 -> 632": Y("632") - Y("646"),
        "p5 MS2-L 646 -> well start (s of the free well side)": Ylo("62D") - Y("646"),
        "p5 MS2-L 646 -> 633 (well end)": Y("633") - Y("646"),
        "p5 MS2-U 62F -> B23 face 5E1 (stair-owned)": Y("62F") - Y("5E1"),
        "p5 MS2-LD-W 632 -> 5C0": Y("5C0") - Y("632"),
        "p5 MS2-LD-W 5E3 -> 5E2": X("5E2") - X("5E3"),
        "p5 MS2-LD-E 62F -> 5C0": Y("5C0") - Y("62F"),
        "p5 MS2-LD-E 5E2 -> 5D4": X("5D4") - X("5E2"),
        "p4 RS-S lane 283 -> 2D0": Y("2D0") - Y("283"),
        "p4 RS-S 2BA -> 2C4": X("2C4") - X("2BA"),
        "p4 RS-S 2BA -> light-well edge end 2CF": X("2CF") - X("2BA"),
        "p4 RS-A lane 2CF -> 289": X("289") - X("2CF"),
        "p4 RS-A 2C8 -> 315": Y("315") - Y("2C8"),
        "p4 RS-LD 2C4 -> 289": X("289") - X("2C4"),
        "p4 RS-LD 283 -> 2C8": Y("2C8") - Y("283"),
        "p4 free edge 289 length": ln("289"),
    }
    c = doc.entitydb.get("374")
    pts = [(p[0] / 1000, p[1] / 1000) for p in c.get_points()]
    out["p4 column 374 along 289 above 283"] = max(b for _, b in pts) - Y("283")
    for k, v in out.items():
        print(f"{k:58s} {v:9.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
