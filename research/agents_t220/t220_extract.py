"""T-220 re-read for the Checker: prints, from the private DXF, every DXF fact ALSENAN_PLANTED_INPUT.json relies on
(sizes in mm, texts, hatch patterns, beam edge lines), and the route G band overlap shares from the committed overlays.
Nothing is written. Coordinates are printed to the console only (never committed).

    python3 -I research/agents_t220/t220_extract.py <path to 'ST7757 dxf.dxf'> [<bands.json from agents_t110/scripts/bands.py>]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import planted_columns as pcm  # noqa: E402

SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OUTLINES = ["329", "66A", "386", "69D", "77B", "778"]
TEXTS = ["544", "543", "548", "547", "77C", "77D"]
HATCHES = ["77A", "777", "391"]
LINES = ["39A", "39B", "6B1", "6B2"]
# footprint (outline handle) -> route G bands to test (storey key of bands.json)
BANDS = {"329": ["BAND0048.1@GF", "BAND0048.2@GF"], "386": ["BAND0047.1@GF", "BAND0047.2@GF"],
         "77B": ["BAND0030.1@1F"], "66A": ["BAND0002.1@1F", "BAND0024.1@1F", "BAND0027.1@1F"],
         "69D": ["BAND0018.1@1F", "BAND0027.3@1F", "BAND0023@1F"], "778": ["BAND0009@2F"]}


def _ring(pts):
    pts = [tuple(q) for q in pts]
    return pts[:-1] if pts[0] == pts[-1] else pts


def main(dxf, bands=None):
    import ezdxf
    from ezdxf import bbox
    if hashlib.sha256(Path(dxf).read_bytes()).hexdigest() != SHA:
        raise SystemExit("not the route G input (sha256 differs)")
    doc = ezdxf.readfile(dxf)
    fp = {}
    for h in OUTLINES:
        e = doc.entitydb[h]
        b = bbox.extents([e])
        fp[h] = _ring([(p[0] / 1000, p[1] / 1000) for p in e.get_points("xy")])
        print("outline", h, e.dxf.layer, round(b.size.x), "x", round(b.size.y), "mm")
    for h in TEXTS:
        e = doc.entitydb[h]
        print("text", h, e.dxf.layer, repr(e.dxf.text))
    for h in HATCHES:
        e = doc.entitydb[h]
        b = bbox.extents([e])
        print("hatch", h, e.dxf.layer, e.dxf.pattern_name, round(b.size.x), "x", round(b.size.y), "mm")
    for h in LINES:
        e = doc.entitydb[h]
        print("line", h, e.dxf.layer, "length", round(e.dxf.start.distance(e.dxf.end)), "mm")
    if bands:
        B = json.loads(Path(bands).read_text())
        for h, ids in BANDS.items():
            shares = {i: round(float(pcm.overlap_share(fp[h], _ring(B[i]["pts"]))), 4) for i in ids}
            print("overlap", h, shares)


if __name__ == "__main__":
    main(*sys.argv[1:3])
