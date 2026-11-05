"""T-522 on the development villa: the three HELD B8-06 pool-court parts of ARCH_TAKEOFF_V3.0.58 (T-507) measured or
narrowed from the drawing. Reads the private decoded P7757.dxf AT RUN TIME (handles in t522_inputs.py, no coordinate
stored); outputs lengths, areas and degrees. Without the drawing every part stays HELD with its V3.0.58 bound.

Run: .work/venv/bin/python -I research/agents_t522/t522_alsenan.py [--dxf PATH]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE, ROOT / "research" / "agents_t486", ROOT / "research" / "agents_t494"):
    sys.path.insert(0, str(p))
import t486_alsenan as A                                   # noqa: E402
import t486_terrace_wp as T                                # noqa: E402
import t494_alsenan as B                                   # noqa: E402
import t522_inputs as I                                    # noqa: E402
import t522_ledge_window as L                              # noqa: E402
from engine.source import wp_applicability_rules_v1 as W   # noqa: E402

MM = 0.001


def _dim(dw, h):
    e = dw.d.entitydb[h]
    blk = dw.d.blocks[e.dxf.geometry]
    txt = [x.text.split(";")[-1] for x in blk if x.dxftype() == "MTEXT"] + \
          [x.dxf.text for x in blk if x.dxftype() == "TEXT"]
    return {"handle": h, "measured_m": round(e.get_measurement() * MM, 6), "printed": txt[0] if txt else None,
            "p2": (e.dxf.defpoint2.x * MM, e.dxf.defpoint2.y * MM), "p3": (e.dxf.defpoint3.x * MM, e.dxf.defpoint3.y * MM),
            "angle": e.dxf.get("angle", 0.0)}


def window_evidence(dw):
    """R-T522-1 checks on the DXF view; returns the printed sill and the checks (no coordinate kept)."""
    s, hd, w, lv, ch = (_dim(dw, h) for h in (I.SILL_DIM, I.SILL_CHAIN_NEXT, I.WINDOW_WIDTH_DIM, I.SLAB_TOP_DIM,
                                              I.BAY_GLAZING_CHORD_DIM))
    slab_top_y = max(lv["p2"][1], lv["p3"][1])
    sill_lo = min(s["p2"][1], s["p3"][1])
    wx0, wx1 = sorted((w["p2"][0], w["p3"][0]))
    checks = {
        "sill_printed_cm": s["printed"], "sill_measured_m": s["measured_m"], "sill_vertical": abs(s["angle"] - 90) < 1e-6,
        "sill_from_slab_top_mm": round((sill_lo - slab_top_y) / MM, 3),
        "sill_inside_window_width": wx0 <= s["p2"][0] <= wx1,
        "head_printed_cm": hd["printed"], "head_starts_on_sill_mm": round((min(hd["p2"][1], hd["p3"][1]) -
                                                                           max(s["p2"][1], s["p3"][1])) / MM, 3),
        "width_printed_cm": w["printed"], "width_measured_m": w["measured_m"],
        "level_dim_m": lv["measured_m"], "bay_chord_printed_cm": ch["printed"], "bay_chord_measured_m": ch["measured_m"],
    }
    ok = (checks["sill_vertical"] and abs(checks["sill_from_slab_top_mm"]) < 1.0 and checks["sill_inside_window_width"]
          and abs(checks["head_starts_on_sill_mm"]) < 1.0 and s["printed"] == "84" and w["printed"] == "50"
          and abs(lv["measured_m"] - 5.5) < 1e-6)
    return (I.SILL_PRINTED_M if ok else None), checks


def bay_pieces(dw):
    """R-T522-2: the bay face pieces measured on their own arcs (same discretisation as T-486 bay_face_lm)."""
    out = []
    for h, stands in I.BAY_PIECES:
        e = dw.d.entitydb[h]
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        a1 = a1 + 360.0 if a1 < a0 else a1
        r = e.dxf.radius * MM
        out.append({"piece": h, "stands": stands, "lm": round(A._len(dw.pts(h)), 6),
                    "arc_exact_lm": round(r * math.radians(a1 - a0), 6),
                    "chord_m": round(2 * r * math.sin(math.radians(a1 - a0) / 2), 6), "layer": e.dxf.layer})
    return out


def ledge_strip(dw):
    """the ledge polygon exactly as T-486 'overhang' (outline - piers - void, west of the wall line) + its cover edge."""
    from shapely.geometry import LineString
    R = A.rings(dw)
    wx, big = R["wall_x"], 1000.0
    whole = T._diff(T._poly(R["outline"]), T.unary_union([T._poly(p) for p in R["piers"].values()]))
    whole = T._diff(whole, T.unary_union([T._poly(R["void"]).buffer(0)]))
    strip = T._areal(T._inter(whole, T._poly([(-big, -big), (wx, -big), (wx, big), (-big, big)])))
    return strip, LineString([(wx, -big), (wx, big)])


def build(dxf=None):
    path = dxf or A.default_dxf()
    if path is None:
        return {"drawing_read": False, "note": "drawing absent: every part stays HELD with its V3.0.58 bound"}
    dw = A.Drawing(path)
    pc, rn, zs = B.zones(path)
    open_sky, ledge = zs
    sill, wchk = window_evidence(dw)
    # open sky: the window run with its printed sill (R-T522-1)
    up = []
    for u in open_sky["upturn_runs"]:
        if u["kind"] == "UNDER_WINDOW":
            u = L.window_run(u["run"], u["lm"], sill, I.SILL_SOURCE if sill is not None else None)
        up.append(u)
    os2 = dict(open_sky, upturn_runs=up)
    os2["evidence"] = dict(open_sky["evidence"], window_face=[
        "C35 (layer 5) on the wall line across the 1F bath window, 0.500002 lm (T-494 partition)",
        "sill printed '84' cm above the +5.50 slab-top line: DXF NW elevation DIMENSION 2EEC (measured 839.27 mm), "
        "head '216' above it (2EFA), width '50' (2D8D); PDF Pages_07-08 p.2 NW elevation chain '84 | 216 | 230'"])
    # ledge: the bay face split by what stands on it (R-T522-2)
    pieces = bay_pieces(dw)
    run_lm = ledge["upturn_runs"][0]["lm"]
    runs, na, rec = L.split_face("bay_face", run_lm,
                                 [dict(p, source=I.BAY_SOURCE) for p in pieces])
    lg2 = dict(ledge, upturn_runs=runs)
    lg2["evidence"] = dict(ledge["evidence"], **{r["run"]: [f"bay face piece {r['run'].split(':')[1]}: "
                                                            + ("wall end (layer 1)" if r["kind"] == "SOLID" else
                                                               "arched glazing '269' x '305' standing on the +5.50 slab "
                                                               "(NW elevation 2E97 / 2D53): floor-level frame")]
                                                 for r in runs})
    rows_os = W.component_rows(os2)
    rows_lg = W.component_rows(lg2) + na
    strip, edge = ledge_strip(dw)
    expo = {h: L.covered_strip_exposure(strip, edge, h) for h in (I.COVER_H_LEVEL_M, 4.00)}
    return {"drawing_read": True, "window_checks": wchk, "sill_m": sill, "bay_pieces": pieces, "bay_reconciliation": rec,
            "rows_open_sky": rows_os, "rows_ledge": rows_lg, "totals": W.totals(rows_os + rows_lg),
            "ledge_area_m2": round(strip.area, 6), "exposure": expo, "effect": effect(rows_os, rows_lg)}


def effect(rows_os, rows_lg):
    """before (V3.0.58 lines) / after (this piece), per line; not wired."""
    win = [r for r in rows_os if r.get("run") == "window_face"]
    led_m = [r for r in rows_lg if r["component"] == "FLAT_MEMBRANE"]
    led_up = [r for r in rows_lg if r["component"] == "UPTURN"]
    led_tr = [r for r in rows_lg if r["component"] == "WINDOW_TRANSITION"]
    w = win[0] if win else None
    w_lm = w["length_lm"] if w and w["status"] == W.MEASURED else None
    t0, u0 = I.V3058_TOTALS["FIN.WP.ROOF_UPTURN"][0], sum(r["held_bound"] / W.UPTURN_H_M for r in led_up)
    return {
        "window_face": {"line": "L-1954878bb02c91139e1b", "before": "HELD 0 .. 0.500002 lm",
                        "after": (f"MEASURED {w_lm:.6f} lm (= {w['qty']:.6f} m2 at 0.20 m)" if w_lm is not None
                                  else "HELD 0 .. 0.500002 lm")},
        "FIN.WP.ROOF_UPTURN_valued_lm": {"before": t0, "after": round(t0 + (w_lm or 0.0), 6),
                                         "change_pct": round(100 * (w_lm or 0.0) / t0, 4)},
        "ledge_membrane": {"line": "L-2361d6ec13c952bd2ae3", "before": "HELD 0 .. 0.639573 m2",
                           "after": f"HELD 0 .. {led_m[0]['held_bound']:.6f} m2 (cause narrowed: one exposure decision)"},
        "ledge_upturn": {"line": "L-d7d1bf8c5991ccf69ea2", "before": "HELD 0 .. 3.528277 lm",
                         "after_upturn_bound_lm": round(u0, 6),
                         "after_transition_lm": round(sum(r["held_bound"] for r in led_tr), 6)},
    }


if __name__ == "__main__":
    r = build(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dxf" else None)
    print(json.dumps({k: v for k, v in r.items() if k not in ("rows_open_sky", "rows_ledge")}, indent=1, default=str))
    for x in r.get("rows_open_sky", []) + r.get("rows_ledge", []):
        print(x["zone_id"], x["component"], x.get("run", ""), x["unit"], x["qty"], x.get("held_bound"), x["status"])
