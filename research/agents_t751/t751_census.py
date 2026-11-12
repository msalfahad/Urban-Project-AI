"""T-751 own DXF census (private input; run by hand, not by the tests).

Reads the architectural DXF (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55..)
from .work/private and writes in/T751_CENSUS.json: handles, layers, levels (metres above the elevation datum) and
lengths only. No coordinate, no drawing content, no client text is written.

    python -I research/agents_t751/t751_census.py <path to P7757.dxf>

Frames: SOUTH EAST ELEVATION (title 24DB) and NORTH WEST ELEVATION (title 2A69); both put +-0.00 on the level blocks
2439 / 2A42 (checked against the +0.30 / +4.30 markers 244A / 244C and the +1.00 / +5.50 markers 2886 / 2888).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "in" / "T751_CENSUS.json"
SHA_PREFIX = "ab54dd55"


def main(path):
    import ezdxf

    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha.startswith(SHA_PREFIX), sha
    doc = ezdxf.readfile(path)
    H = doc.entitydb
    msp = doc.modelspace()

    def ins_y(h):
        return H[h].dxf.insert.y

    frames = {}
    for name, datum, checks in (("SE", "2439", (("244A", 0.30), ("244C", 4.30))),
                                ("NW", "2A42", (("2886", 1.00), ("2888", 5.50)))):
        y0 = ins_y(datum)
        for h, lv in checks:
            assert abs((ins_y(h) - y0) / 1000 - lv) < 1e-6, (name, h)
        frames[name] = y0
    assert H["24DB"].dxf.text == "SOUTH EAST ELEVATION" and H["2A69"].dxf.text == "NORTH WEST ELEVATION"

    def lv(frame, y):
        return round((y - frames[frame]) / 1000, 6)

    def line(frame, h, layer="1"):
        e = H[h]
        assert e.dxftype() == "LINE" and e.dxf.layer == layer, (h, e.dxftype(), e.dxf.layer)
        a, b = e.dxf.start, e.dxf.end
        return {"handle": h, "layer": e.dxf.layer, "lv_lo": lv(frame, min(a.y, b.y)), "lv_hi": lv(frame, max(a.y, b.y)),
                "dx": round(abs(a.x - b.x) / 1000, 6), "len": round(math.dist((a.x, a.y), (b.x, b.y)) / 1000, 6)}

    def chain(handles):
        """Length of a polyline drawn as consecutive LINE handles; checks that each joins the next."""
        tot = 0.0
        prev = None
        for i, h in enumerate(handles):
            e = H[h]
            assert e.dxftype() == "LINE" and e.dxf.layer == "1", h
            a, b = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
            if prev is None and len(handles) > 1:
                n = H[handles[1]]
                ends = [(n.dxf.start.x, n.dxf.start.y), (n.dxf.end.x, n.dxf.end.y)]
                if min(math.dist(a, p) for p in ends) < 1.0:
                    a, b = b, a
            if prev is not None:
                if math.dist(prev, a) < 1.0:
                    pass
                elif math.dist(prev, b) < 1.0:
                    a, b = b, a
                else:
                    raise AssertionError(f"chain break at {h}")
            tot += math.dist(a, b)
            prev = b
        return tot / 1000

    def head_chain(frame, j_left, j_right, box_pad=0.6):
        """Walk the opening's own head line from the top of the left jamb to the top of the right jamb."""
        L, R = H[j_left], H[j_right]
        pl = max((L.dxf.start, L.dxf.end), key=lambda p: p.y)
        pr = max((R.dxf.start, R.dxf.end), key=lambda p: p.y)
        x0, x1 = pl.x - 1, pr.x + 1
        ytop = pl.y + box_pad * 2000
        adj = defaultdict(list)
        for e in msp.query("LINE"):
            if e.dxf.layer != "1" or e.dxf.handle in (j_left, j_right):
                continue
            a, b = e.dxf.start, e.dxf.end
            if not all(x0 <= p.x <= x1 and pl.y - 1 <= p.y <= ytop for p in (a, b)):
                continue
            for p, q in ((a, b), (b, a)):
                adj[(round(p.x), round(p.y))].append((e.dxf.handle, (q.x, q.y)))
        cur, goal = (round(pl.x), round(pl.y)), (round(pr.x), round(pr.y))
        used, path, length = set(), [], 0.0
        prevp = (pl.x, pl.y)
        while cur != goal:
            nxt = [s for s in adj[cur] if s[0] not in used]
            assert nxt, f"head chain stuck after {len(path)} segments"
            h, q = nxt[0]
            used.add(h)
            path.append(h)
            length += math.dist(prevp, q) / 1000
            prevp = q
            cur = (round(q[0]), round(q[1]))
        return path, round(length, 6)

    cen = {"schema": "URBAN_T751_CENSUS_V1", "dxf_sha16": sha[:16], "frames": {"SE": "datum block 2439",
                                                                             "NW": "datum block 2A42"}}

    # 1F parapet-end corners (R-T751-1): the corner's own vertical outline line, its top and any end round.
    rnd_nw = ["2584", "2583", "2582", "2581", "2580", "257F", "257E", "257D", "257C", "257B", "257A", "2579"]
    rnd_se = ["1C46", "1C45", "1C44", "1C43", "1C42", "1C41", "1C40", "1C3F", "1C3E", "1C3D", "1C3C", "1C3B"]
    v_nw_ne2 = line("NW", "27B6")
    v_se_sw2 = line("SE", "2228")
    r_nw = {"handles": rnd_nw, "rise": round(line("NW", "2579")["lv_hi"] - line("NW", "2584")["lv_lo"], 6),
            "run": round(sum(line("NW", h)["dx"] for h in rnd_nw), 6), "developed": round(chain(rnd_nw), 6)}
    r_se = {"handles": rnd_se, "rise": round(line("SE", "1C3B")["lv_hi"] - line("SE", "1C46")["lv_lo"], 6),
            "run": round(sum(line("SE", h)["dx"] for h in rnd_se), 6), "developed": round(chain(rnd_se), 6)}
    cen["corners_1f"] = {
        "NW-5/NE-2": {"frame": "NW", "vertical": v_nw_ne2, "round": r_nw, "top_line": line("NW", "27B9"),
                      "beyond": [line("NW", "27B5", "5"), line("NW", "27B4", "5"), line("NW", "2563", "5")]},
        "SW-1/NW-5": {"frame": "NW", "vertical": line("NW", "2783"), "top_line": line("NW", "27CA"),
                      "pier_round_side": line("NW", "2728")},
        "NW-3/NE-1": {"frame": "NW", "vertical": line("NW", "2792"), "top_line": line("NW", "27CB"),
                      "recess_top": line("NW", "270B")},
        "NW-2/NW-3": {"frame": "NW", "top_line": line("NW", "27CB")},
        "NW-1/NW-2": {"frame": "NW", "top_line": line("NW", "27CB")},
        "SW-3/NW-1": {"frame": "NW", "vertical": line("NW", "27B0"), "arc_lines": [line("NW", h) for h in
                                                                                ("2A51", "2A52", "2A53")],
                      "top_line": line("NW", "27CB")},
        "NE-2/SE-1": {"frame": "SE", "vertical": line("SE", "1BFD"), "top_line": line("SE", "2220"),
                      "band_line": line("SE", "1C21")},
        "SE-1/SW-2": {"frame": "SE", "vertical": v_se_sw2, "round": r_se, "top_line": line("SE", "231A"),
                      "beyond": [line("SE", "23A5", "5"), line("SE", "23A4", "5"), line("SE", "1C53", "5")]},
    }
    # pier of the NW-5 bay frame (T-567 R-T567-6): its top and span in the NW frame
    cen["pier"] = {"top_line": line("NW", "27CA"), "edges": [line("NW", h) for h in ("25B3", "270A", "2728", "2783")]}
    # GF pool-court plinth corners (R-T751-1 at the F.F.L. datum +1.00): the arc ends' plinth lines
    cen["plinth_corners"] = {"NW-3/NW-4": line("NW", "285E"), "NW-4/NW-5": line("NW", "283E"),
                             "arc_inner_rim": [line("NW", h) for h in ("2861", "285C")]}
    # arched windows (R-T751-2)
    win = {}
    for wid, frame, jl, jr, sill_h in (("W15", "NW", "2566", "256A", None), ("W16", "NW", "2889", "288A", None),
                                       ("W26", "SE", "2211", "2229", "2319")):
        jL, jR = line(frame, jl), line(frame, jr)
        hp, head = head_chain(frame, jl, jr)
        crown = max(line(frame, h)["lv_hi"] for h in hp)
        sill = line(frame, sill_h)["lv_lo"] if sill_h else jL["lv_lo"]
        win[wid] = {"frame": frame, "jambs": [jl, jr], "sill_line": sill_h, "sill": sill,
                    "springing": min(jL["lv_hi"], jR["lv_hi"]), "width": round(abs(H[jl].dxf.start.x -
                                                                                 H[jr].dxf.start.x) / 1000, 6),
                    "head_handles": [hp[0], hp[-1]], "head_segments": len(hp), "head_developed": head,
                    "crown": crown}
    cen["windows"] = win
    # the SE entrance surround (T-360 r2 geometry re-run; split against T-747's stated span and at +1.00)
    sys.path.insert(0, str(ROOT / "research" / "agents_t360"))
    import t360_alsenan as T360  # noqa: E402
    from shapely.geometry import box as sbox

    import io
    import contextlib
    src = (ROOT / "research" / "agents_t360" / "t360_alsenan.py").read_text()
    body = src[src.index("def geometry(path):"):src.index("def main(argv):")]
    body = body.replace('print("GEOMETRY OK")', "return U, faces, B, x0, x1, y0")
    ns = dict(vars(T360))
    exec(compile(body, "t360_geometry_copy", "exec"), ns)  # noqa: S102 - the merged T-360 function, unchanged
    with contextlib.redirect_stdout(io.StringIO()):
        U, faces, B, x0, x1, y0 = ns["geometry"](path)
    span = (-279637.0, -277778.0)  # T-747's stated surround span (its md, section 2), absolute DXF x
    ffl = frames["SE"] + 1000
    crown = [g for g, _ in faces if g.bounds[2] > span[1] + 1]
    cen["surround"] = {
        "t360_visible_m2": round(U.area / 1e6, 6),
        "inside_t747_span_m2": round(U.intersection(sbox(span[0], y0 - 10, span[1], y0 + 10000)).area / 1e6, 6),
        "right_of_t747_span_m2": round(U.intersection(sbox(span[1], y0 - 10, x1 + 1, y0 + 10000)).area / 1e6, 6),
        "left_of_t747_span_m2": round(U.intersection(sbox(x0 - 1, y0 - 10, span[0], y0 + 10000)).area / 1e6, 6),
        "below_ffl_m2": round(U.intersection(sbox(x0 - 1, y0 - 10, x1 + 1, ffl)).area / 1e6, 6),
        "above_ffl_m2": round(U.intersection(sbox(x0 - 1, ffl, x1 + 1, y0 + 10000)).area / 1e6, 6),
        "blocks_right_of_span": [{"face_m2": round(g.intersection(B).area / 1e6, 6),
                                  "lv_lo": lv("SE", g.bounds[1]), "lv_hi": lv("SE", g.bounds[3])} for g in crown],
        "crown_inner_handles": "1CC6/1CC7/1CC8/23AC/23AD", "crown_outer_handles": "1CC3/2230/222F/1CAB/1CC2",
        "cut_line": line("SE", "2416"),
        "piece_layer": H["1CC8"].dxf.layer,
        "door_line": line("SE", "1C00", "5"), "landing_line": line("SE", "1BFE", "5"),
    }
    OUT.write_text(json.dumps(cen, indent=1, sort_keys=True) + "\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1])
