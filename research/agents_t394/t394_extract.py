"""T-394 extract: own read of the GF / 1F column outlines on the private copy of Drive "Alsenan chalet project" /
'ST7757 dxf.dxf' (sha256 9f9d1179...). Writes .work/private/t394/OWN_COLUMNS_T394.json (outside every worktree): per member handle its layer, the two sides of its
outline (m, sorted), its area (m2) and its vertex count. No coordinates, no text of the drawing.

    python3 -I research/agents_t394/t394_extract.py <private>/ST7757_dxf.dxf [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
LEDGER = HERE.parent / "agents_t248" / "LEDGER_T248.csv"
OUT = HERE.parents[2] / "private" / "t394" / "OWN_COLUMNS_T394.json"   # drawing-derived: private, never tracked


def main(argv):
    import ezdxf
    from shapely.geometry import Polygon
    src = Path(argv[0])
    raw = src.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA, "not the Drive 'ST7757 dxf.dxf' of the manifest"
    db = ezdxf.readfile(str(src)).entitydb
    rows = []
    for r in csv.DictReader(LEDGER.open(encoding="utf-8")):
        if r["storey"] not in ("GF", "1F") or not r["member"].startswith(("GFRS:", "FFRS:")):
            continue
        h = r["member"].split(":", 1)[1]
        e = db.get(h)
        if e is None or e.dxftype() != "LWPOLYLINE":
            rows.append({"member": r["member"], "found": False})
            continue
        pts = [(p[0] / 1000.0, p[1] / 1000.0) for p in e.get_points()]
        poly = Polygon(pts)
        x0, y0, x1, y1 = poly.bounds
        sides = sorted([round(x1 - x0, 3), round(y1 - y0, 3)])
        rows.append({"member": r["member"], "found": True, "layer": e.dxf.layer, "closed": bool(e.closed),
                     "vertices": len(pts), "sides_m": sides, "area_m2": round(poly.area, 4),
                     "rectangle": abs(poly.area - sides[0] * sides[1]) < 1e-4})
    out = {"schema": "T394_OWN_COLUMNS_V1", "source": "Drive: Urban BOQ private data / Alsenan chalet project / "
           "'ST7757 dxf.dxf'", "source_sha256": SHA, "members": rows}
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    print(len(rows), "outlines;", sum(1 for r in rows if r.get("found")), "found")


if __name__ == "__main__":
    main(sys.argv[1:])
