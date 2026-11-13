"""T-754 own DXF census (private input; run by hand, not by the tests).

Reads the architectural DXF (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55..)
from .work/private and writes in/T754_CENSUS.json: handles, layers, levels (m above the elevation datum), lengths and
offsets along a named line only. No coordinate, no drawing content, no client text is written.

    python -I research/agents_t754/t754_census.py <path to P7757.dxf>

Frames as T-751: SOUTH EAST ELEVATION (title 24DB, datum block 2439) and NORTH WEST ELEVATION (title 2A69, datum
block 2A42), datums re-checked on 244A / 244C and 2886 / 2888.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "in" / "T754_CENSUS.json"
SHA_PREFIX = "ab54dd55"
TOL = 1.0  # mm


def main(path):
    import ezdxf

    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha.startswith(SHA_PREFIX), sha
    doc = ezdxf.readfile(path)
    H = doc.entitydb
    msp = doc.modelspace()
    assert H["24DB"].dxf.text == "SOUTH EAST ELEVATION" and H["2A69"].dxf.text == "NORTH WEST ELEVATION"
    datum = {}
    for name, d, checks in (("SE", "2439", (("244A", 0.30), ("244C", 4.30))),
                            ("NW", "2A42", (("2886", 1.00), ("2888", 5.50)))):
        y0, x0 = H[d].dxf.insert.y, H[d].dxf.insert.x
        for h, lv in checks:
            assert abs((H[h].dxf.insert.y - y0) / 1000 - lv) < 1e-6, (name, h)
        datum[name] = (x0, y0)

    def lv(fr, y):
        return round((y - datum[fr][1]) / 1000, 6)

    def seg(h):
        e = H[h]
        assert e.dxftype() == "LINE", h
        return e.dxf.start, e.dxf.end

    def rec(fr, h):
        a, b = seg(h)
        return {"handle": h, "layer": H[h].dxf.layer, "lv_lo": lv(fr, min(a.y, b.y)), "lv_hi": lv(fr, max(a.y, b.y)),
                "dx": round(abs(a.x - b.x) / 1000, 6)}

    def xspan(h):
        a, b = seg(h)
        return min(a.x, b.x), max(a.x, b.x)

    cen = {"schema": "URBAN_T754_CENSUS_V1", "dxf_sha16": sha[:16]}

    # (1) D-GF-07 on the SE frame: masonry jamb / head (beyond, layer 5) and the frame outline drawn inside it.
    x_j = xspan("1C00")[0]
    door = {}
    for h in ("1C00", "220F", "1CF1", "1CF3", "2234", "223A", "1BFE"):
        r = rec("SE", h)
        r["offset_from_jamb_1C00"] = round((xspan(h)[0] - x_j) / 1000, 6)
        door[h] = r
    cen["door_gf07_se"] = door

    # (2) NW-1 / NW-2 / NW-3 parapet band: the top line 27CB, its end lines, and every vertical layer-1 line strictly
    # inside its span that crosses the band +9.70 .. +11.00 (a convex corner between two faces seen from NW would be one).
    x0, x1 = xspan("27CB")
    inside = []
    for e in msp.query("LINE"):
        a, b = e.dxf.start, e.dxf.end
        if abs(a.x - b.x) > TOL or e.dxf.layer != "1":
            continue
        if not (x0 + TOL < a.x < x1 - TOL):
            continue
        lo, hi = lv("NW", min(a.y, b.y)), lv("NW", max(a.y, b.y))
        if hi <= 9.70 + 1e-6 or lo >= 11.0 - 1e-6:
            continue
        inside.append({"handle": e.dxf.handle, "lv_lo": lo, "lv_hi": hi, "offset_from_27CB_start": round((a.x - x0) / 1000, 6)})
    cen["nw_parapet_band"] = {"top_line": rec("NW", "27CB"), "end_lines": [rec("NW", "2792"), rec("NW", "27B0")],
                              "verticals_inside_band": sorted(inside, key=lambda r: r["offset_from_27CB_start"])}

    # (3) NW frame bands at +5.30 .. +5.50 (GF roof strip and pool-court front) and the two end columns.
    cen["nw_bands"] = {h: rec("NW", h) for h in ("27E4", "27E5", "27E2", "2841", "2842", "2843", "2844", "2845", "2846",
                                                  "2840", "27B1", "27E6", "27E9", "27D6", "27D7", "27DF", "27E0")}

    # (4) SE frame: every horizontal line with +4.70 < level <= +5.60 and whether it lies over the porch-mouth piece top
    # 2232 (+4.70); a slab-edge band under the 1F SE-1 wall would be drawn there.
    m0, m1 = xspan("2232")
    hz = []
    for e in msp.query("LINE"):
        a, b = e.dxf.start, e.dxf.end
        if abs(a.y - b.y) > TOL:
            continue
        L = lv("SE", a.y)
        if not (4.70 + 1e-6 < L <= 5.60):
            continue
        s0, s1 = min(a.x, b.x), max(a.x, b.x)
        if abs(s0 - m0) > 40000:      # outside the SE frame
            continue
        hz.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "lv": L, "len": round((s1 - s0) / 1000, 6),
                   "overlaps_mouth_span": bool(s1 > m0 + TOL and s0 < m1 - TOL)})
    cen["se_over_mouth"] = {"mouth_top": rec("SE", "2232"), "horizontals_4p70_5p60": sorted(hz, key=lambda r: r["handle"])}

    OUT.write_text(json.dumps(cen, indent=1, sort_keys=True) + "\n")
    print("written", OUT.relative_to(HERE.parents[1]))


if __name__ == "__main__":
    main(sys.argv[1])
