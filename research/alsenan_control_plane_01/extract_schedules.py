"""ALSENAN CONTROL-PLANE AUDIT R1 - ST7757 schedule evidence extractor (diagnosis only; changes nothing).

Reads every attributed schedule block of the structural DXF and the loose schedule / slab texts beside them, and writes
them unchanged (plus a row binding for the beam REMARKS column) to evidence/ST7757_SCHEDULE_EXTRACT.json so the
coverage registers and the diagnostic tests can run without the source drawing.

    FT       isolated footing rows    FO-TY W H DEPHT SH-B SH-D LO-B LO-D BOXED
    FTB      two-layer footing rows   FO-TY W H DEPHT SH-T-* LO-T-* SH-B-* LO-B-* BOXED-T BOXED-B
    SBT      simple / strap beams     BEAM W H BOT-B BOT-D TOP-B TOP-D STI-B D
    C-BEAM2  2-span continuous beams  BEAM-NAME W H L1-M L2-M T/M-n BOTn-B BOTn-D MID-B MID-D STRn-B STRn-D
    C-BEAM3  3-span continuous beams  ... MID1-* MID2-* ...
    CGT      column groups            COL-T FOU.* GR.* 1ST.* 2ND.* LOAD

T/M-n are design loads (t/m), not bars.  STI-B / STRn-B are stirrups per metre.

    python3 research/alsenan_control_plane_01/extract_schedules.py [ST7757.dxf] [out.json]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
BLOCKS = ("FT", "FTB", "SBT", "C-BEAM2", "C-BEAM3", "CGT")
LOOSE = re.compile(r"%%c|P\.C|T&B|/\d+cm", re.I)


def _xy(p):
    return [round(p.x, 1), round(p.y, 1)]


def extract(path: Path) -> dict:
    import ezdxf
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    out = {"SCHEMA": "URBAN_ALSENAN_ST7757_SCHEDULE_EXTRACT_V1", "source_file": path.name,
           "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "blocks": {b: [] for b in BLOCKS},
           "loose_texts": [], "beam_remarks": []}
    for b in BLOCKS:
        for i in msp.query(f'INSERT[name=="{b}"]'):
            att = {a.dxf.tag: a.dxf.text for a in i.attribs}
            out["blocks"][b].append({"handle": i.dxf.handle, "layer": i.dxf.layer, "insert": _xy(i.dxf.insert),
                                     "attribute_y": round(min(a.dxf.insert.y for a in i.attribs), 1),
                                     "attributes": att})
    for e in msp.query("TEXT MTEXT"):
        t = e.dxf.text if e.dxftype() == "TEXT" else e.text
        if t and LOOSE.search(t):
            out["loose_texts"].append({"handle": e.dxf.handle, "layer": e.dxf.layer, "text": t.strip(),
                                       "xy": _xy(e.dxf.insert)})
    # REMARKS column of the simple-beam schedule (p.10): side-bar texts in the column right of the SBT rows,
    # bound to the row whose attribute baseline is nearest (row pitch 672 drawing units)
    rows = out["blocks"]["SBT"]
    xmax = max(a["insert"][0] for a in rows) if rows else 0.0
    for t in out["loose_texts"]:
        if t["layer"] != "S-TEXT.SCH" or not re.search(r"/\d+cm", t["text"]) or t["xy"][0] < xmax:
            continue
        r = min(rows, key=lambda a: abs(a["attribute_y"] - t["xy"][1]))
        out["beam_remarks"].append({"beam": r["attributes"]["BEAM"], "row_handle": r["handle"],
                                    "text": t["text"].replace("%%C", "Ø").replace("%%c", "Ø"),
                                    "text_handle": t["handle"], "dy": round(t["xy"][1] - r["attribute_y"], 1)})
    out["blocks"] = {k: sorted(v, key=lambda a: -a["insert"][1]) for k, v in out["blocks"].items()}
    out["loose_texts"].sort(key=lambda t: (t["layer"], t["text"], t["handle"]))
    out["beam_remarks"].sort(key=lambda r: -next(a["attribute_y"] for a in rows if a["handle"] == r["row_handle"]))
    return out


def main(src=None, dest=None):
    ex = extract(Path(src) if src else DXF)
    dest = Path(dest) if dest else Path(__file__).parent / "evidence" / "ST7757_SCHEDULE_EXTRACT.json"
    dest.write_text(json.dumps(ex, indent=1, ensure_ascii=False) + "\n")
    print(dest, {k: len(v) for k, v in ex["blocks"].items()}, len(ex["loose_texts"]), len(ex["beam_remarks"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
