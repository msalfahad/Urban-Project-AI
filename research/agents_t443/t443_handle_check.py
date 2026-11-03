"""T-443 own re-measure (read-only): every handle the T-441 face tables name for the four stair-room floor parts is
re-read on the architectural DXF (Drive 'Alsenan chalet project', P7757_DXF_COMPRESSED.zip -> P7757.dxf), its drawn
length compared with the sum of the stretches that cite it, and the openings checked as gaps (the face stretches on
each side of an opening do not reach across it: the drawn length beside the gap is the cited length). Printed: handle,
entity type, layer, drawn length (m) and the cited sum only (no coordinate, no text).

    .work/venv/bin/python -I research/agents_t443/t443_handle_check.py <P7757.dxf>
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t441"))
import t441_alsenan as T  # noqa: E402


def _len(e):
    t = e.dxftype()
    if t == "LINE":
        a, b = e.dxf.start, e.dxf.end
        return math.hypot(b.x - a.x, b.y - a.y) / 1000.0
    if t == "LWPOLYLINE":
        p = [(x, y) for x, y, *_ in e.get_points()]
        if e.closed:
            p.append(p[0])
        return sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)) / 1000.0
    return None


def main(dxf):
    import ezdxf
    db = ezdxf.readfile(str(dxf)).entitydb
    cited = defaultdict(float)
    for part in T.parts():
        for sd in part["sides"]:
            for st in sd["stretches"]:
                if st["kind"] in ("WALL", "COLUMN"):
                    hs = st["handles"].split()
                    cited[hs[0]] += st["s1"] - st["s0"]    # first handle carries the face; a second is the joining one
    rows = []
    for h in sorted(cited):
        e = db.get(h)
        L = _len(e) if e is not None else None
        rows.append((h, e.dxftype() if e is not None else "MISSING", e.dxf.layer if e is not None else "",
                     None if L is None else round(L, 4), round(cited[h], 4)))
    for r in rows:
        flag = "" if r[3] is None else ("FULL" if abs(r[3] - r[4]) <= 0.002 else
                                        ("PART" if r[4] < r[3] + 0.002 else "OVER"))
        print(f"{r[0]:>6} {r[1]:<11} {r[2]:<10} drawn {r[3]!s:>8}  cited {r[4]:>8}  {flag}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1])
