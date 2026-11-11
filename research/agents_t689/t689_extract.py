"""T-689 own read of the structural DXF (private copy; Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf').
Writes values only (handles, lengths in m, schedule attributes, text counts): no coordinate, no drawing content.

    python3 -I research/agents_t689/t689_extract.py <ST dxf> --write
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import ezdxf

OUT = Path(__file__).resolve().parent / "out" / "T689_OWN_READ.json"
SFRS_COLS = ["40F", "412", "415", "418", "41B", "41E", "421", "424", "778"]
B8_EDGES = ["38D", "38E"]


def bbox(e):
    p = [(x, y) for x, y, *_ in e.get_points()]
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return min(xs), max(xs), min(ys), max(ys)


def main(path, write):
    raw = Path(path).read_bytes()
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    db = doc.entitydb
    cols = {}
    for h in SFRS_COLS:
        e = db.get(h)
        x0, x1, y0, y1 = bbox(e)
        cols[h] = {"layer": e.dxf.layer, "w_m": round((x1 - x0) / 1000, 3), "d_m": round((y1 - y0) / 1000, 3),
                   "_b": (float(x0), float(x1), float(y0), float(y1))}
    e1, e2 = db.get("38D"), db.get("38E")
    band_w = abs(e1.dxf.start[1] - e2.dxf.start[1]) / 1000
    # B8 clear span on the north band: from the east face of 412 to the west face of 415 (both sit on the band)
    span = (cols["415"]["_b"][0] - cols["412"]["_b"][1]) / 1000
    on_band = {h: bool(cols[h]["_b"][3] >= min(e1.dxf.start[1], e2.dxf.start[1]) - 1 and
                   cols[h]["_b"][2] <= max(e1.dxf.start[1], e2.dxf.start[1]) + 1) for h in ("40F", "412", "415")}
    lab = db.get("79E")
    lab_x = lab.dxf.insert[0]
    label_in_span = bool(cols["412"]["_b"][1] < lab_x < cols["415"]["_b"][0])
    sched = None
    for ins in msp.query('INSERT[name=="SBT"]'):
        a = {x.dxf.tag: x.dxf.text for x in ins.attribs}
        if a.get("BEAM") == "B8":
            sched = {"handle": ins.dxf.handle, "W_cm": a["W"], "H_cm": a["H"], "bottom": f"{a['BOT-B']} d{a['BOT-D']}",
                     "top": f"{a['TOP-B']} d{a['TOP-D']}"}
        if a.get("BEAM") == "B15":
            b15 = {"handle": ins.dxf.handle, "W_cm": a["W"], "H_cm": a["H"], "bottom": f"{a['BOT-B']} d{a['BOT-D']}",
                   "top": f"{a['TOP-B']} d{a['TOP-D']}"}
    # texts inside the SFRS outline (392 south edge .. 38D north edge, 397 west .. 39A east)
    xs = (db.get("397").dxf.start[0], db.get("39A").dxf.start[0])
    ys = (db.get("392").dxf.start[1], db.get("38D").dxf.start[1])
    inside = lambda x, y: min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys)
    level, thick = [], []
    for t in msp.query("TEXT MTEXT"):
        x, y = t.dxf.insert[0], t.dxf.insert[1]
        if not inside(x, y):
            continue
        s = (t.dxf.text if t.dxftype() == "TEXT" else t.plain_text()).strip()
        if t.dxf.layer == "LEVEL" or s.startswith("+") or s.startswith("%%p"):
            level.append(t.dxf.handle)
        if s in ("T", "18", "16"):
            thick.append((t.dxf.handle, s))
    res = {
        "schema": "T689_OWN_READ_V1",
        "source": {"file": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'", "bytes": len(raw),
                   "sha256": hashlib.sha256(raw).hexdigest()},
        "sfrs_columns": {h: {k: v for k, v in c.items() if k != "_b"} for h, c in cols.items()},
        "b8": {"label": "79E", "label_in_span_412_415": label_in_span, "edges": B8_EDGES, "band_width_m": round(band_w, 3),
               "clear_span_412_to_415_m": round(span, 3), "supports_on_band": on_band, "schedule_row": sched,
               "edge_layer_linetype": doc.layers.get(e1.dxf.layer).dxf.linetype},
        "b15_schedule_row": b15,
        "sfrs_texts": {"level_marks_inside": level, "thickness_texts_inside": thick},
    }
    if write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], "--write" in sys.argv)
