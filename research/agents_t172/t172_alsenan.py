"""T-172 development villa (research only, not a method, not wired): parapets decomposed into physical components,
external vertical corners, and the freelancer's corner line (1,297.35 m.l) reconciled cell by cell.

    python3 -I research/agents_t172/t172_alsenan.py <t159_rings.json> [--workbook <freelancer .xlsx>]
        [--frames <frames.json>] [--out research/agents_t172]

Inputs: the T-159 stage-1 rings (scratch; rebuilt from the Drive plan DXF with research/agents_t159/t159_extract.py),
the merged T-159 face table research/agents_t159/FACADE_SIDES_T159.csv (bands and printed levels), the scratch
ARCH_WALLS.json next to the rings (wall thickness per external wall, the released engine's own reading), optionally
the freelancer workbook (Drive, read-only, scratch copy: the cells are re-read and checked against the values below)
and a scratch frames.json (elevation frame line lengths measured on the DXF elevation frames). Coordinates stay in
the scratch; the repository gets lengths, areas and statuses only. No client name, no drawing content.

Project facts used here (Alsenan only, each with its drawing source) never go into t172_edges.py."""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t159"))
sys.path.insert(0, str(ROOT / "research" / "agents_t172"))
sys.path.insert(0, str(ROOT))

import t159_alsenan as A                                                     # noqa: E402
import t159_sides as S                                                       # noqa: E402
import t172_edges as E                                                       # noqa: E402

# ---------------------------------------------------------------- printed levels (metres) and their sources
ROOF = {
    "ANNEX": (4.30, "annex roof +4.30: 1F plan mark; SE elevation; NE elevation sheet 09"),
    "GF": (5.50, "GF roof / 1F F.F.L. +5.50: 1F plan marks; section A-A sheet 10"),
    "1F": (9.70, "1F roof / 2F F.F.L. +9.70: section A-A sheet 10; all four elevations"),
    "2F": (13.90, "2F roof +13.90: section A-A sheet 10 level mark"),
}
TOP = {
    "ANNEX": (4.80, "annex parapet top +4.80: SE elevation 30 / 400 / 50 ('480'); sheets 07 / 09"),
    "GF": (6.00, "GF roof parapet top +6.00: NW elevation 550 + 50; section A-A '50'"),
    "1F_PRINTED": (11.00, "1F parapet top +11.00 on NE and SW: '130' above +9.70 (sheets 09 / 07)"),
    "2F": (14.40, "2F parapet top +14.40: '1440' overall, section A-A '50' above +13.90"),
}
# the 1F wavy / curved parapet tops (NW sides, SE side) carry no printed end height: T-159 integrated the CAD top
# line for AREAS (mean heights); an end height is not established -> corner parts above +9.70 are HELD in this range
# (lowest and highest 1F parapet tops read by T-159 / T-162: +10.085 .. +11.30)
WAVE_RANGE = (10.085, 11.30)

# ---------------------------------------------------------------- the four parapet chains (outline sides in order)
# ends: what the parapet does at each end of its chain, from the plans / sections (see the report, section 2)
CHAINS = {
    "ANNEX": {"floor": "GF", "roof": "ANNEX", "top": "ANNEX",
              "sides": [("NE-6", None), ("SE-1", None), ("SW-1", None), ("SW-2", None), ("NW-1", None),
                        ("SW-3", ("b", 15.073))],
              "start": ("ABUT_X", 15.073, "annex / passage wall x 15.073..15.273 rises to the +5.50 passage slab "
                                          "(T-159 P-1 band +0.30 -> +5.50): higher construction"),
              "end": ("ABUT_X", 15.073, "1F SE-1 face stands on the annex roof (T-159 OVER_LOWER_ROOF +4.30 -> "
                                        "+5.50)")},
    "GF": {"floor": "GF", "roof": "GF", "top": "GF",
           "sides": [("SW-9", ("a", 34.343)), ("NW-7", None), ("NE-4", None)],
           "start": ("ABUT_X", 34.343, "1F NW-5 face rises from the GF roof at x 34.343 (1F outline)"),
           "end": ("UNKNOWN", None, "NE-4 ends at the 1.20 m side-passage mouth; the passage roof slab is also at "
                                    "+5.50; whether the parapet stops (stop-end) or turns along the mouth is not "
                                    "drawn on the sections read (A-A sheet 10, NE elevation sheet 09)")},
    "1F": {"floor": "1F", "roof": "1F", "top": None,
           "sides": [("SW-3", ("a", 27.573)), ("NW-1", None), ("NW-2", None), ("NW-3", None), ("NE-1", None),
                     ("NW-4", None), ("SW-1", None), ("NW-5", None), ("NE-2", None), ("SE-1", None), ("SW-2", None)],
           "start": ("ABUT_X", 27.573, "2F NW-1 face rises from the 1F roof (2F outline)"),
           "end": ("ABUT_X", 19.473, "2F SE-1 face rises from the 1F roof between y 13.323 and 15.623 (2F outline)")},
    "2F": {"floor": "2F", "roof": "2F", "top": "2F",
           "sides": [("NW-1", None), ("NE-1", None), ("SE-1", None), ("SW-1", None)],
           "start": ("CLOSED", None, "closed ring"), "end": ("CLOSED", None, "closed ring")},
}


def load_sides(rings):
    R = json.loads(Path(rings).read_text())
    Ef = {f: A.local(R, f) for f in ("GF", "1F", "2F")}
    p = R["floors"]["GF"]["passage"]
    drop = [m["edge_index"] for ps in p["passages"] if ps["state"] == "OPEN_AIR" for m in ps["mouths"]
            if m["edge_index"] not in p["wall_end_gaps"]]
    out = {}
    for f in Ef:
        ss = S.name_sides(S.split_sides(Ef[f], A.AXES, drop if f == "GF" else ()))
        for s in ss:
            if s["kind"] == "ARC":
                e0 = Ef[f][s["edges"][0]]
                s["c"], s["r"] = tuple(e0["c"]), float(e0["r"])
        out[f] = ss
    boxes = {f: R["floors"][f]["box"] for f in Ef}
    return out, Ef, boxes, R


def wall_thickness(side, floor, walls, box):
    """t of the external wall whose centreline runs parallel to the side at t / 2 inside it (released engine reading
    ARCH_WALLS.json, same DXF). Arcs and short returns take None here (resolved by the caller from neighbours)."""
    if side["kind"] != "STRAIGHT" or side["len_m"] < 0.30:
        return None
    a = (side["a"][0] + box[0], side["a"][1] + box[1])
    b = (side["b"][0] + box[0], side["b"][1] + box[1])
    d = E._unit(E._sub(b, a))
    n = E._unit(side["normal"])
    best = None
    for w in walls:
        if w["kind"] not in ("EXTERNAL", "CURVED_STUB"):
            continue
        p0 = (w["centreline"][0][0] / 1000.0, w["centreline"][0][1] / 1000.0)
        p1 = (w["centreline"][-1][0] / 1000.0, w["centreline"][-1][1] / 1000.0)
        if math.dist(p0, p1) < 0.2:
            continue
        dw = E._unit(E._sub(p1, p0))
        if abs(E._cross(d, dw)) > 1e-3:
            continue
        off = E._dot(E._sub(p0, a), n)          # negative = inside
        t = float(w["t_m"])
        # the wall overlaps the side along its direction
        s0, s1 = sorted((E._dot(E._sub(p0, a), d), E._dot(E._sub(p1, a), d)))
        if s1 < 0.05 or s0 > side["len_m"] - 0.05:
            continue
        if abs(off + t / 2.0) <= 0.01:
            best = t if best is None else max(best, t)
    return best


def build_chain(name, spec, sides, walls, boxes):
    f = spec["floor"]
    byname = {s["name"]: s for s in sides[f]}
    out = []
    for nm, cut in spec["sides"]:
        s = dict(byname[nm])
        if cut:
            end, x = cut
            pt = list(s[end])
            pt[0] = x
            s[end] = pt
        s["a"], s["b"] = tuple(s["a"]), tuple(s["b"])
        t = wall_thickness(dict(s, len_m=E.side_length(dict(s, kind=s["kind"]))), f, walls, boxes[f])
        out.append({"name": nm, "kind": "ARC" if s["kind"] == "ARC" else "STRAIGHT", "a": s["a"], "b": s["b"],
                    "normal": tuple(s["normal"]), "t": t, "c": s.get("c"), "r": s.get("r"),
                    "t_source": "ARCH_WALLS external wall" if t else None})
    # arcs and short returns: the thickness of their straight neighbours when both agree (same wall continues)
    for k, s in enumerate(out):
        if s["t"] is None:
            nb = [out[j]["t"] for j in (k - 1, k + 1) if 0 <= j < len(out) and out[j]["t"]]
            if name == "2F" and not nb:
                nb = [out[j % len(out)]["t"] for j in (k - 1, k + 1) if out[j % len(out)]["t"]]
            if nb and all(abs(x - nb[0]) < 1e-9 for x in nb):
                s["t"], s["t_source"] = nb[0], "neighbour walls (same wall continues)"
    return out


def end_spec(e):
    kind, x, _src = e
    if kind == "ABUT_X":
        return {"type": "ABUT", "line": ((x, 0.0), (0.0, 1.0))}
    return {"type": kind}


def facade_rows(csv_path):
    rows = list(csv.DictReader(open(csv_path, newline="")))
    by = {}
    for r in rows:
        by.setdefault((r["FLOOR"], r["SIDE"]), []).append(r)
    return by


def parapet_height(chain, spec, fac):
    roof = ROOF[spec["roof"]][0]

    def h(s):
        if spec["top"]:
            return round(TOP[spec["top"]][0] - roof, 6)
        rows = [r for r in fac[(spec["floor"], s["name"])] if r["PORTION"] == "PARAPET"]
        r = rows[0]
        if r["STATUS"] == "HELD":
            lo, hi = (float(v) for v in r["HELD_RANGE_H_M"].split(".."))
            return ("HELD", lo, hi)
        return round(float(r["TOP_M"]) - roof, 6)
    return h


# ---------------------------------------------------------------- vertical corners
def vertical_corners(sides, Ef, fac):
    """External vertical arrises at every convex junction of each floor's outline (plus the wall ends at the side-
    passage mouths). Height = overlap of the two faces' bands AT the corner point. DRAWING-CONFIRMED part and HELD
    part are kept apart."""
    poly = {f: S._poly_from_edges(Ef[f]) for f in Ef}
    out = []

    def tangent(s, at_end):
        if s["kind"] != "ARC":
            return E._unit(E._sub(s["b"], s["a"]))
        c = s["c"]
        va, vb = E._sub(s["a"], c), E._sub(s["b"], c)
        ccw = E._cross(va, vb) > 0
        v = vb if at_end else va
        t = (-v[1], v[0]) if ccw else (v[1], -v[0])
        return E._unit(t)

    def band_at(f, s, P):
        """(bottom, top_confirmed, held_top_hi, note) of side s at point P; None bottom = HELD."""
        rows = fac.get((f, s["name"]), [])
        if f == "GF":
            plinth = [r for r in rows if r["SOURCE"].startswith("plinth")]
            bots = [float(r["BOTTOM_M"]) for r in plinth if r["BOTTOM_M"]]
            tops = {r["PORTION"]: float(r["TOP_M"]) for r in rows if not r["SOURCE"].startswith("plinth")
                    and r["TOP_M"]}
            note = "GF"
            if bots:
                bottom = min(bots)
            else:
                # plinth below the F.F.L. HELD (outside level not printed): confirmed from the F.F.L. up
                st = [float(r["BOTTOM_M"]) for r in rows if not r["SOURCE"].startswith("plinth") and r["BOTTOM_M"]]
                bottom = min(st) if st else None
                rng = [r["HELD_RANGE_H_M"] for r in plinth if r["HELD_RANGE_H_M"]]
                note = "plinth below the F.F.L. HELD %s m" % (rng[0] if rng else "")
            under_1f = poly["1F"].distance(_pt(P)) <= 0.01
            if "EDGE" in tops and len(tops) > 1:
                top = max(v for k, v in tops.items() if k != "EDGE") if under_1f else tops["EDGE"]
            else:
                top = max(tops.values()) if tops else None
            return bottom, top, top, note
        if f == "1F":
            on_gf = poly["GF"].distance(_pt(P)) <= 0.01
            if on_gf:
                bottom = ROOF["ANNEX"][0] if P[0] <= 15.273 + 0.01 else ROOF["GF"][0]
                note = ""
            else:
                bottom, note = ROOF["GF"][0], "slab edge below +5.50 HELD (Q-68)"
            par = [r for r in rows if r["PORTION"] == "PARAPET"]
            under_2f = poly["2F"].distance(_pt(P)) <= 0.01
            if under_2f or not par:
                return bottom, ROOF["1F"][0], ROOF["1F"][0], note
            r = par[0]
            if r["STATUS"] != "HELD" and "CAD" not in r["SOURCE"]:
                return bottom, float(r["TOP_M"]), float(r["TOP_M"]), note
            return bottom, ROOF["1F"][0], WAVE_RANGE[1], (note + "; parapet end height HELD").strip("; ")
        return ROOF["1F"][0], TOP["2F"][0], TOP["2F"][0], ""

    for f in ("GF", "1F", "2F"):
        ss = sides[f]
        n = len(ss)
        for k in range(n):
            s1, s2 = ss[k], ss[(k + 1) % n]
            P = tuple(s1["b"])
            if "NOT_A_FACE" in (s1["kind"], s2["kind"]):
                # a wall end at a side-passage mouth (owner Q-67 A): the end face (t wide) has two vertical
                # arrises, one on the facade side and one on the passage side. The wall end rises as high as the
                # passage wall it carries (T-159 P-1 / P-2 bands to the +5.50 passage slab) or its own face.
                face = s2 if s1["kind"] == "NOT_A_FACE" else s1
                b = band_at(f, face, P)
                annex_side = P[0] <= 15.273 + 0.01
                pr = [r for r in fac[("GF", "P-1" if annex_side else "P-2")] if not r["SOURCE"].startswith("plinth")]
                pp = [r for r in fac[("GF", "P-1" if annex_side else "P-2")] if r["SOURCE"].startswith("plinth")]
                p_top, p_bot = float(pr[0]["TOP_M"]), float(pp[0]["BOTTOM_M"])
                # up to the passage slab top; a parapet above it at the mouth is the parapet chain's stop-end
                # (HELD there when the chain end is UNKNOWN), never counted twice
                top = p_top
                for kind, bot in (("MOUTH_END (facade-side arris)", b[0]),
                                  ("MOUTH_END (passage-side arris)", p_bot)):
                    out.append({"floor": f, "corner": f"{s1['name']}/{s2['name']}", "type": kind,
                                "bottom": bot, "top": top, "held_top": top,
                                "note": "wall end at the passage mouth up to the passage wall top %.2f (face top "
                                        "%.2f)" % (p_top, b[1])})
                continue
            t1, t2 = tangent(s1, True), tangent(s2, False)
            p1 = {"a": (0, 0), "b": t1, "normal": s1["normal"]}
            p2 = {"a": (0, 0), "b": t2, "normal": s2["normal"]}
            if abs(E._cross(t1, t2)) <= 1e-6:
                continue                                       # tangent or collinear: no arris
            convex = E.turn_is_convex(p1, p2)
            b1, b2 = band_at(f, s1, P), band_at(f, s2, P)
            bot = None if b1[0] is None or b2[0] is None else max(b1[0], b2[0])
            out.append({"floor": f, "corner": f"{s1['name']}/{s2['name']}",
                        "type": "CONVEX (external arris)" if convex else "CONCAVE (internal angle)",
                        "bottom": bot, "top": min(b1[1], b2[1]), "held_top": min(b1[2], b2[2]),
                        "note": "; ".join(x for x in (b1[3], b2[3]) if x and x not in ("GF",))})
    for c in out:
        if c["bottom"] is None:
            c["confirmed_ml"] = None
        else:
            c["confirmed_ml"] = round(max(0.0, c["top"] - c["bottom"]), 6)
        c["held_extra_ml"] = round(max(0.0, c["held_top"] - c["top"]), 6)
    return out


def _pt(P):
    from shapely.geometry import Point
    return Point(P)


# ---------------------------------------------------------------- the freelancer's cells (sheet rows 50-93)
# (row, column, value, English label of his row, his length H, his height F). Values are the workbook's own cells
# (Drive "Alsenan chalet project", exterior plaster sheet; already quoted on the board, OWNER_NOTES_SIGMA).
CELLS = [
    (51, "A", 2.5, "SW high facade", 1.5, 6.0), (52, "A", 27.6, "SW middle facade", 6.9, 10.0),
    (53, "A", 38.5, "SW high facade", 7.9, 14.4), (54, "A", 8.0, "SW annex facade", 4.0, 5.25),
    (55, "A", 24.0, "SW annex facade", 13.0, 4.8), (58, "A", 31.75, "SE facade", 6.75, 14.4),
    (59, "A", 20.0, "SE low facade", 5.25, 11.85), (60, "A", 4.5, "SE annex", 1.5, 4.8),
    (61, "A", "8.3.1", "SE frame (2 x 0.45 x 27.7): TEXT cell, not in his SUM", 27.7, 0.45),
    (63, "A", 17.0, "NE facade", 10.0, 4.8), (64, "A", 73.8, "NE high facade", 19.2, 10.0),
    (65, "A", 4.5, "NE annex (2 x 6 x 1.5)", 1.5, 6.0), (65, "B", 100.0, "vertical corners", None, None),
    (66, "B", 48.0, "vertical corners (cont.)", None, None),
    (68, "A", 4.5, "NW annex facade", 1.5, 6.0), (69, "A", 15.15, "NW high facade", 6.75, 9.8),
    (70, "A", 9.9, "NW facade over the pool", 4.95, 5.7), (73, "B", 18.0, "pool-court ceiling", None, 3.05),
    (75, "B", 17.55, "NW frame (0.45 x 8.75)", 8.75, 0.45),
    (77, "A", 51.85, "roof (2F) facade", 17.75, 4.7), (77, "B", 12.6, "roof (2F) facade", 17.75, 4.7),
    (78, "A", 48.47, "parapet (1.70 high)", 48.47, 1.7), (78, "B", 96.94, "parapet (1.70 high)", 48.47, 1.7),
    (79, "A", 28.4, "annex roof parapet (0.70)", 28.4, 0.7), (79, "B", 56.8, "annex roof parapet", 28.4, 0.7),
    (83, "A", 36.2, "annexes roof parapet (0.70)", 36.2, 0.7), (83, "B", 72.45, "annexes roof parapet", 36.2, 0.7),
    (84, "A", 27.2, "parapet (0.70)", 27.2, 0.7), (84, "B", 54.4, "parapet (0.70)", 27.2, 0.7),
    (87, "A", 73.65, "boundary wall 2.40 high", 37.65, 2.4), (87, "B", 75.34, "boundary wall", 37.65, 2.4),
    (88, "B", 16.1, "boundary wall (cont.)", 5.8, 2.4), (92, "B", 181.7, "drip edge 0.28 wide", 181.7, 0.28),
]


def reconcile(chains, vc, frames, void_area_m2=3.6901):
    """One row per freelancer cell: decode, drawing counterpart, drawing m.l, status, verdict proposal, cause."""
    P = {k: v["components"] for k, v in chains.items()}
    conv = [c for c in vc if c["type"].startswith("CONVEX")]
    mouth = [c for c in vc if c["type"].startswith("MOUTH")]
    v_gf1f = round(sum(c["confirmed_ml"] for c in conv if c["floor"] in ("GF", "1F")), 4)
    v_2f = round(sum(c["confirmed_ml"] for c in conv if c["floor"] == "2F"), 4)
    v_held = round(sum(c["held_extra_ml"] for c in conv), 4)
    v_mouth = round(sum(c["confirmed_ml"] for c in mouth), 4)
    n2f = sum(1 for c in conv if c["floor"] == "2F")
    void_c = round(2 * math.pi * math.sqrt(void_area_m2 / math.pi), 4)
    fr_se = frames["SE_frame_stair_tower"]["lines_m"] if frames else None
    fr_nw = frames["NW_frame_pool_court_arch"]["lines_m"] if frames else None

    def par(k):
        return f"outer {P[k]['outer_top_arris_ml']:.3f} + inner {P[k]['inner_top_arris_ml']:.3f} = " \
               f"{P[k]['outer_top_arris_ml'] + P[k]['inner_top_arris_ml']:.3f} (inner run {P[k]['inner_top_arris_ml']:.3f})"
    M = {
        "WALL_A": ("facade rows: no item description; candidates: opening edges (heads / jambs / sills) and horizontal "
                   "band lines of that facade", None, "UNKNOWN", "UNRESOLVED (per cell); group RULE_DIFFERENCE pending",
                   "the cell carries no breakdown; it cannot be mapped to a drawn edge one by one"),
        (65, "B"): ("external vertical corners, all floors (with B66)",
                    f"GF + 1F convex {v_gf1f:.3f} + 2F {v_2f:.3f} (+ HELD parapet end parts <= {v_held:.3f}; "
                    f"+ passage-mouth wall ends {v_mouth:.3f}, exterior under Q-67 A cond.)", "DRAWING-CONFIRMED + HELD",
                    "UNRESOLVED", "his 100 + 48 has no corner list; see the corner table"),
        (66, "B"): ("see row 65 B", None, "-", "UNRESOLVED", "continuation of row 65 B"),
        (73, "B"): ("pool-court soffit: edge of the circular void through the floor plate",
                    f"{void_c:.3f} (one soffit arris, circle of the verified void area {void_area_m2} m2)",
                    "DRAWING-CONFIRMED (void area verified, T-154)", "UNRESOLVED",
                    "18.00 matches no drawn edge; the lower slab-edge arrises over the open court are HELD (Q-68)"),
        (75, "B"): ("NW frame round the 1F pool-court arch: its two drawn edge lines",
                    (f"{fr_nw[0][0] + fr_nw[1][0]:.3f} (one arris per drawn line) .. "
                     f"{sum(sum(x) for x in fr_nw):.3f} (each line a 50 mm moulding, two arrises)") if fr_nw else None,
                    "HELD (frame profile not detailed)", "RULE_DIFFERENCE (dimension)",
                    "his 2 x 8.775 = mean developed length x 2; the drawn arches are 9.316 and 7.893 m"),
        (61, "A"): ("SE frame round the stair tower: three drawn nested arch lines",
                    (f"{sum(x[0] for x in fr_se):.3f} (one arris per line) .. {sum(sum(x) for x in fr_se):.3f}")
                    if fr_se else None, "HELD (frame profile not detailed)",
                    "FREELANCER OMISSION (text cell '8.3.1' is not summed); quantity HELD",
                    "a text cell inside SUM(A51:A90) contributes 0: the SE frame's edges are missing from his 1,297.35"),
        (77, "A"): ("2F (roof) facade: no description", None, "UNKNOWN", "UNRESOLVED", "not decomposable"),
        (77, "B"): ("2F external vertical corners", f"{n2f} x 4.700 = {v_2f:.3f} (+9.70 -> +14.40 parapet top)",
                    "DRAWING-CONFIRMED", "ENGINE_RIGHT on the height (hand: section A-A / elevations)",
                    "his 12.60 = 3 x 4.20 (to the +13.90 slab, 3 corners); the arris runs to the parapet top (the "
                    "2F walls continue as the parapet, section A-A); the 4th corner continues the house's SE / SW "
                    "corner from the ground and may sit in his facade rows"),
        (78, "A"): ("1F roof parapet: third line per metre", f"no external arris; inner base junction "
                    f"{P['1F']['inner_base_junction_ml']:.3f} is a termination", "-", "RULE_DIFFERENCE",
                    "his A = 1 x L (48.47 ~ inner run 48.784)"),
        (78, "B"): ("1F roof parapet: two top arrises", par("1F"), "DRAWING-CONFIRMED", "RULE_DIFFERENCE",
                    "his 2 x 48.47 on the inner run; the outer arris is 50.569 (longer)"),
        (79, "A"): ("annex roof parapet: third line", f"no external arris; inner base "
                    f"{P['ANNEX']['inner_base_junction_ml']:.3f}", "-", "RULE_DIFFERENCE", "his 28.40 ~ inner 28.428"),
        (79, "B"): ("annex roof parapet: two top arrises", par("ANNEX"), "DRAWING-CONFIRMED", "RULE_DIFFERENCE",
                    "his 2 x 28.40"),
        (83, "A"): ("'annexes' roof parapet 36.20: no drawn parapet of that length", None, "UNKNOWN", "UNRESOLVED",
                    "rows 83 + 84 = 63.40 m against GF house 27.970 + 2F 28.300 = 56.270 m inner (+7.130)"),
        (83, "B"): ("see 83 A", par("2F") + " [2F, nearest]", "DRAWING-CONFIRMED", "UNRESOLVED", "2 x 36.20 + 0.05"),
        (84, "A"): ("GF house roof parapet (nearest): third line", f"no external arris; inner base "
                    f"{P['GF']['inner_base_junction_ml']:.3f}", "-", "RULE_DIFFERENCE", "his 27.20 vs inner 27.970"),
        (84, "B"): ("GF house roof parapet: two top arrises", par("GF"), "DRAWING-CONFIRMED + HELD stop-end",
                    "RULE_DIFFERENCE", "2 x 27.20"),
        (87, "A"): ("boundary wall: top line + vertical edges", "boundary wall height not printed; HELD",
                    "HELD (owner Q-65; boundary wall not answered for Sigma)", "HELD",
                    "73.65 = 37.65 + 15 x 2.40 (decoded): one line along the wall + 15 vertical edges of 2.40 m"),
        (87, "B"): ("boundary wall: two top arrises", "drawn wall lines (GF plan): neighbour side 31.37 outer / "
                    "30.97 inner, street side 8.30 outer / 5.60 inner (t 0.20): 39.67 + 36.57 = 76.24 if both "
                    "faces are plastered", "HELD (Q-65; neighbour-side face ownership)", "HELD",
                    "75.34 ~ 2 x 37.65 + 0.04"),
        (88, "B"): ("boundary wall continuation", "see 87 B", "HELD", "HELD", "16.10 not decomposable"),
        (92, "B"): ("drip edge 0.28 wide", "none drawn (section A-A: plain parapet tops, slab edges flush; no drip "
                    "line on the elevations read)", "NOT IN THE DRAWING -> HELD", "HELD (designer item)",
                    "181.70 m matches no drawn line"),
    }
    rows = []
    for row, col, val, label, L, h in CELLS:
        key = (row, col)
        m = M.get(key) or (M["WALL_A"] if col == "A" and 51 <= row <= 70 else ("-", None, "-", "-", "-"))
        dec = E.decode_cell(val if not isinstance(val, str) else None, L, h)
        rows.append({"ROW": row, "COL": col, "HIS_ML": val, "HIS_ROW": label, "HIS_L": L, "HIS_H": h,
                     "DECODE_aL_plus_bH": ";".join(f"{x}xL+{y}xH" for x, y in dec[:4]) or "none",
                     "DRAWING_COUNTERPART": m[0], "DRAWING_ML": m[1] or "-", "STATUS": m[2],
                     "VERDICT_PROPOSAL": m[3], "CAUSE": m[4]})
    return rows


def check_workbook(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    bad = []
    for row, col, val, *_ in CELLS:
        got = ws[f"{col}{row}"].value
        if isinstance(val, str):
            ok = str(got) == val
        else:
            ok = isinstance(got, (int, float)) and abs(float(got) - val) < 1e-9
        if not ok:
            bad.append((row, col, val, got))
    tot_a = ws["A93"].value
    tot_b = ws["B93"].value
    return bad, tot_a, tot_b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rings")
    ap.add_argument("--workbook")
    ap.add_argument("--frames")
    ap.add_argument("--out", default=str(ROOT / "research" / "agents_t172"))
    a = ap.parse_args()
    out = Path(a.out)
    sides, Ef, boxes, R = load_sides(a.rings)
    walls = {fl["floor"]: fl["walls"] for fl in
             json.loads((Path(a.rings).parent / "ARCH_WALLS.json").read_text())["floors"]}
    fac = facade_rows(ROOT / "research" / "agents_t159" / "FACADE_SIDES_T159.csv")

    # ------------------------------------------------ parapets
    comp_rows, chains = [], {}
    for name, spec in CHAINS.items():
        ch = build_chain(name, spec, sides, walls[spec["floor"]], boxes)
        st, en = end_spec(spec["start"]), end_spec(spec["end"])
        c = E.parapet_components(ch, st, en, parapet_height(ch, spec, fac))
        hfun = parapet_height(ch, spec, fac)
        inner = dict(c["inner_by_side"])
        merged = {}
        for g in c["niches"]:
            for i in g:
                merged[ch[i]["name"]] = [ch[j]["name"] for j in g]
        for s in ch:
            h = hfun(s)
            Lo = E.side_length(s)
            comp_rows.append({
                "CHAIN": name, "SIDE": s["name"], "KIND": s["kind"], "OUTER_TOP_ARRIS_ML": round(Lo, 4),
                "INNER_TOP_ARRIS_ML": round(inner[s["name"]], 4),
                "NICHE_GROUP": "+".join(merged.get(s["name"], [])),
                "T_M": s["t"], "T_SOURCE": s["t_source"],
                "H_ABOVE_ROOF_M": (f"HELD {h[1]}..{h[2]}" if isinstance(h, tuple) else round(h, 4)),
                "OUTER_FACE_M2": (f"{Lo * h[1]:.4f}..{Lo * h[2]:.4f}" if isinstance(h, tuple) else round(Lo * h, 4)),
                "STATUS": "HELD (height)" if isinstance(h, tuple) else "DRAWING-CONFIRMED"})
        chains[name] = {"components": c, "start": spec["start"][2], "end": spec["end"][2],
                        "roof": ROOF[spec["roof"]], "top": TOP.get(spec["top"]) if spec["top"] else
                        "per side: printed +11.00 (NE / SW) or the CAD top line (NW / SE waves, T-159)",
                        "edges_per_metre": E.edges_per_metre(c)}
    with open(out / "PARAPET_COMPONENTS_T172.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(comp_rows[0].keys()))
        w.writeheader()
        w.writerows(comp_rows)

    # ------------------------------------------------ vertical corners
    vc = vertical_corners(sides, Ef, fac)
    with open(out / "VERTICAL_CORNERS_T172.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["floor", "corner", "type", "bottom", "top", "held_top", "confirmed_ml",
                                           "held_extra_ml", "note"])
        w.writeheader()
        w.writerows(vc)
    conv = [c for c in vc if c["type"].startswith(("CONVEX", "MOUTH"))]
    v_conf = round(sum(c["confirmed_ml"] or 0.0 for c in conv), 4)
    v_held = round(sum(c["held_extra_ml"] for c in conv), 4)
    v_heldn = [c["corner"] for c in conv if c["confirmed_ml"] is None]

    # ------------------------------------------------ frames (elevation lines, scratch measurement)
    frames = json.loads(Path(a.frames).read_text()) if a.frames else None

    rec = reconcile(chains, vc, frames)
    with open(out / "RECONCILIATION_T172.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rec[0].keys()))
        w.writeheader()
        w.writerows(rec)

    # ------------------------------------------------ workbook check
    wbcheck = None
    if a.workbook:
        bad, ta, tb = check_workbook(a.workbook)
        wbcheck = {"cells_checked": len(CELLS), "mismatches": bad, "A93": ta, "B93": tb}

    summ = {
        "parapets": {k: {"outer_top_arris_ml": v["components"]["outer_top_arris_ml"],
                         "inner_top_arris_ml": v["components"]["inner_top_arris_ml"],
                         "top_surface_m2": v["components"]["top_surface_m2"],
                         "outer_face_m2": v["components"]["outer_face_m2"],
                         "inner_face_m2": v["components"]["inner_face_m2"],
                         "stop_ends": v["components"]["stop_ends"],
                         "held_height_sides": v["components"]["held_height_sides"],
                         "t_mean_m": v["components"]["t_mean_m"],
                         "edges_per_metre": v["edges_per_metre"],
                         "start": v["start"], "end": v["end"]} for k, v in chains.items()},
        "vertical_corners": {"convex_and_mouth_count": len(conv), "confirmed_ml": v_conf,
                             "held_extra_ml_max": v_held, "held_bottom_corners": v_heldn,
                             "concave_count": len(vc) - len(conv)},
        "frames": frames,
        "workbook_check": wbcheck,
        "cells": {"A_sum": round(sum(v for _, c, v, *_ in CELLS if c == "A" and not isinstance(v, str)), 4),
                  "B_sum": round(sum(v for _, c, v, *_ in CELLS if c == "B"), 4)},
    }
    tot_o = sum(v["components"]["outer_top_arris_ml"] for v in chains.values())
    tot_i = sum(v["components"]["inner_top_arris_ml"] for v in chains.values())
    summ["parapet_totals"] = {"outer_top_arris_ml": round(tot_o, 4), "inner_top_arris_ml": round(tot_i, 4),
                              "top_surface_m2": round(sum(v["components"]["top_surface_m2"]
                                                          for v in chains.values()), 4)}
    (out / "summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
