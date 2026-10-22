"""T-162 corners of the development villa's facade, in m.l (research only, not a method, not wired).

    python3 -I research/agents_t162/t162_alsenan_corners.py <t159 code dir> <t159_rings.json> [--csv CORNERS_T162.csv]

<t159 code dir> holds T-159's t159_sides.py / t159_alsenan.py (branch agents/task-T-159, READY f35bafb; research only).
<t159_rings.json> is T-159's stage-1 output from the Drive plan DXF (scratchpad, never in the repository).
Uses T-159's sides, side names and printed levels unchanged, and t162_corners.py for the corners. Prints and writes
lengths only (no coordinates, no names).

Per corner: the two sides that meet, CONVEX (external arris) / CONCAVE (internal angle) / MOUTH_END (free wall end at a
passage mouth, owner Q-67 A), and the height over which both faces exist, from the printed levels:
  GF: bottom = the outside level in front of the side (T-159 GF_OUTSIDE; pool-court faces HELD +0.15 / +0.30);
      top = +5.50 where the 1F plate is over the face at the corner (FLUSH or COVERED, owner Q-07 slab-top bands),
      else the roof parapet top (+4.80 annex / +6.00 house).
  1F: bottom = +4.30 on SE-1 where it stands on the annex roof, else +5.50 (where the 1F face stands over open air the
      slab edge below +5.50 is HELD, Q-68, and is listed apart); top = +9.70 under the 2F plate, else the parapet top
      of that side (printed +11.00 on NE-2 / SW-3; the T-159 CAD-line mean on the wavy SE / NW parapets: a mean, said
      so; HELD range on SW-2 and the recess returns).
  2F: +9.70 -> +14.40 (printed on all four elevations).
Horizontal arrises: the outer top edge of every parapet (the EDGE / PARAPET portions of T-159) and the reveals of the
facade openings (head + jambs + sill) from the T-150 census (READY 8bbf39d), with the heights T-150 gives (PRINTED,
owner reference 2.20 for doors = ASSUMED, else HELD)."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t162_corners as C                                                     # noqa: E402

EPS = 0.04       # step from the corner along the side and inward (m) to test which plate stands above / below
PASSAGE_FACE = {"annex": ("P-1", 0.15, 5.50), "house": ("P-2", 0.15, 5.50)}
# the top of the wavy / stepped 1F parapets AT EACH END of the side (a corner needs the end, not the mean), read on the
# DXF SE / NW elevation frames as T-159 lists them (P1_PARAPET sources): SE-1 NE end +11.30 printed ('6800' from +4.30
# and '200'), SW end +10.085 (CAD top line); NW-5 NE end +10.80, SW end +11.00; NW-1 / NW-3 +11.00; NW-4 +10.80.
# key: (side, "a" = start of the side in outline order, "b" = its end)
CAD_END_TOP = {("SE-1", "a"): 11.30, ("SE-1", "b"): 10.085, ("NW-5", "a"): 11.00, ("NW-5", "b"): 10.80,
               ("NW-1", "a"): 11.00, ("NW-1", "b"): 11.00, ("NW-3", "a"): 11.00, ("NW-3", "b"): 11.00,
               ("NW-4", "a"): 10.80, ("NW-4", "b"): 10.80}

# facade openings (T-150 census, READY 8bbf39d, OPENINGS_T150.csv; the side from T-159's outline openings):
# (id, floor, side, width m, height m or None, height status, has sill)
OPENINGS = [
    ("W11", "GF", "SE-1", 1.95, None, "HELD", True), ("W12", "GF", "SE-1", 1.95, None, "HELD", True),
    ("D-GF-01", "GF", "SW-1", 1.00, 2.20, "ASSUMED", False), ("W04", "GF", "SW-3", 0.60, None, "HELD", True),
    ("D-GF-03", "GF", "SW-3", 0.90, 2.20, "ASSUMED", False), ("W08", "GF", "SW-3", 1.50, None, "HELD", True),
    ("D-GF-06", "GF", "SW-5", 1.00, 2.20, "ASSUMED", False), ("D-GF-07", "GF", "SE-2", 2.00, 2.50, "PRINTED", False),
    ("W01", "GF", "SE-4", 1.20, 2.00, "PRINTED", True), ("D-GF-09", "GF", "SW-7", 0.90, 2.20, "ASSUMED", False),
    ("W05", "GF", "SW-7", 0.60, None, "HELD", True), ("W06", "GF", "SW-7", 0.60, None, "HELD", True),
    ("W07", "GF", "SW-7", 0.60, None, "HELD", True), ("W02", "GF", "NW-7", 6.33, None, "HELD", True),
    ("W03", "GF", "NW-4", 6.57, 4.30, "PRINTED", True), ("D-GF-05", "GF", "P-1", 1.00, 2.20, "ASSUMED", False),
    ("W09", "GF", "P-2", 1.50, None, "HELD", True), ("W10", "GF", "P-2", 1.00, None, "HELD", True),
    ("W17", "1F", "NW-2", 3.29, 3.50, "PRINTED", False), ("W15", "1F", "NW-5", 1.55, 3.10, "PRINTED", False),
    ("W16", "1F", "NW-5", 1.55, 3.10, "INFERRED", False), ("W18", "1F", "NW (not on the engine outline)", 0.50, 2.16,
                                                           "PRINTED", True),
    ("W19", "1F", "NE-2", 0.60, None, "HELD", True), ("W20", "1F", "NE-2", 0.60, None, "HELD", True),
    ("W24", "1F", "NE-2", 1.55, None, "HELD", True), ("W14", "1F", "SE-1", 2.45, 1.60, "PRINTED", True),
    ("W13", "1F", "SE-2", 1.20, 2.30, "PRINTED", True), ("W25", "1F", "SW-3", 1.00, None, "HELD", True),
    ("W21", "1F", "SW-3", 0.60, None, "HELD", True), ("W22", "1F", "SW-3", 0.60, None, "HELD", True),
    ("W23", "1F", "SW-3", 0.60, None, "HELD", True), ("D-2F-01", "2F", "NE-1", 1.00, 2.20, "ASSUMED", False),
    ("W26", "2F", "SE-1", 1.20, 1.70, "PRINTED", True), ("W27", "2F", "SW-1", 1.00, None, "HELD", True),
    ("W28", "2F", "SW-1", 0.60, None, "HELD", True), ("W29", "2F", "SW-1", 1.20, None, "HELD", True),
]


def main():
    t159dir, rings = Path(sys.argv[1]), Path(sys.argv[2])
    sys.path.insert(0, str(t159dir))
    import t159_alsenan as A                                                 # noqa: E402
    from shapely.geometry import Point
    import t159_sides as S                                                   # noqa: E402
    R = json.loads(rings.read_text())
    sides, rows = A.build(R)
    E = {f: A.local(R, f) for f in ("GF", "1F", "2F")}
    poly = {f: S._poly_from_edges(E[f]) for f in E}
    row = {(r["floor"], r["side"]): r for r in rows}
    p = R["floors"]["GF"]["passage"]
    drop = [m["edge_index"] for ps in p["passages"] if ps["state"] == "OPEN_AIR" for m in ps["mouths"]
            if m["edge_index"] not in p["wall_end_gaps"]]
    annex = set(A.GF_OUTSIDE["annex"])

    def side_of(f, ei):
        return next(s for s in sides[f] if ei in s["edges"])

    def probe(f, s, at, toward_start):
        """a point just inside the floor next to the corner, on side s (step back along the side, then inward)."""
        a, b = s["a"], s["b"]
        L = max(1e-9, ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5)
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if s["radius_m"] is None else (0.0, 0.0)
        sgn = -1.0 if toward_start else 1.0
        n = s["normal"]
        return Point(at[0] + sgn * u[0] * EPS - n[0] * EPS, at[1] + sgn * u[1] * EPS - n[1] * EPS)

    def band(f, s, pt, end):
        """(bottom, top, status, note, (lo, hi) range of the height part that is HELD)"""
        nm = s["name"]
        if f == "GF":
            blk = "annex" if nm in annex else "house"
            out = A.GF_OUTSIDE[blk][nm]
            under = poly["1F"].contains(pt)
            top = 5.50 if under else (4.80 if blk == "annex" else 6.00)
            if isinstance(out, tuple):
                return (None, top, "HELD", "pool-court face: stands on +0.15 or +0.30", (A.lv(out[0]), A.lv(out[1])))
            return (A.lv(out), top, "DRAWING-CONFIRMED", "under 1F plate" if under else "roof edge", None)
        if f == "1F":
            over_gf = poly["GF"].contains(pt)
            bot = 4.30 if (over_gf and nm in A.LOWER_ROOF) else 5.50
            note = "" if over_gf else "over open air: slab edge below +5.50 HELD (Q-68)"
            if poly["2F"].contains(pt):
                return (bot, 9.70, "DRAWING-CONFIRMED", ("under 2F plate; " + note).strip("; "), None)
            kind, h, area, _src = A.P1_PARAPET[nm]
            if kind == "PRINTED" or kind == "CAD_ARC":
                return (bot, 9.70 + h, "DRAWING-CONFIRMED", ("parapet printed" if kind == "PRINTED" else
                                                             "parapet CAD mean") + ("; " + note if note else ""), None)
            if kind == "CAD" and (nm, end) in CAD_END_TOP:
                return (bot, CAD_END_TOP[(nm, end)], "DRAWING-CONFIRMED", "parapet top at this end (DXF frame)"
                        + ("; " + note if note else ""), None)
            if kind == "CAD":
                edge_len = next(pr["len_m"] for pr in row[(f, nm)]["portions"] if pr["cls"] == "PARAPET")
                return (bot, round(9.70 + area / edge_len, 4), "DRAWING-CONFIRMED (CAD mean)",
                        "wavy parapet: CAD-line mean top" + ("; " + note if note else ""), None)
            return (bot, None, "HELD", "parapet top not printed" + ("; " + note if note else ""),
                    (9.70 + h[0], 9.70 + h[1]))
        return (9.70, 14.40, "DRAWING-CONFIRMED", "2F printed 420 + 50", None)

    out = []
    for f in ("GF", "1F", "2F"):
        for c in C.ring_corners(E[f], drop if f == "GF" else ()):
            si = side_of(f, c["prev"])
            if c["kind"] == "MOUTH_END":
                real = si if c["prev"] not in drop else side_of(f, c["next"])
                at_start = c["prev"] in drop
                bi = band(f, real, probe(f, real, c["at"], toward_start=not at_start), "a" if at_start else "b")
                blk = "annex" if real["name"] in annex else "house"
                pn, pb, pt = PASSAGE_FACE[blk]
                bj = (pb, pt, "DRAWING-CONFIRMED", "passage face to the +5.50 slab", None)
                names = (real["name"], pn)
            else:
                sj = side_of(f, c["next"])
                bi = band(f, si, probe(f, si, c["at"], toward_start=True), "b")
                bj = band(f, sj, probe(f, sj, c["at"], toward_start=False), "a")
                names = (si["name"], sj["name"])
            h = C.corner_height(bi[:2], bj[:2])
            lo = hi = None
            if h is None:
                # bound it with the HELD ranges (bottom range on the GF pool court, top range on the 1F parapets)
                def opt(b, k):
                    bot = b[0] if b[0] is not None else (b[4][1] if k == "lo" else b[4][0])
                    top = b[1] if b[1] is not None else (b[4][0] if k == "lo" else b[4][1])
                    return bot, top
                lo = C.corner_height(opt(bi, "lo"), opt(bj, "lo"))
                hi = C.corner_height(opt(bi, "hi"), opt(bj, "hi"))
                if abs(hi - lo) <= 0.001:          # within 1 mm (T-159 ranges carry 1.0996 for +10.80)
                    # the unknown level does not govern: the corner ends at the neighbour's printed level
                    h, lo, hi = hi, None, None
            facing = "/".join(sorted({n.split("-")[0] for n in names}))
            out.append({"floor": f, "sides": " | ".join(names), "facing": facing, "kind": c["kind"],
                        "turn_deg": c["turn_deg"], "height_m": h, "held_lo_m": lo, "held_hi_m": hi,
                        "status": "HELD" if h is None else ("DRAWING-CONFIRMED (CAD mean)" if "CAD mean" in bi[2] + bj[2]
                                                            else "DRAWING-CONFIRMED"),
                        "note": "; ".join(x for x in (bi[3], bj[3]) if x)})
    # the passage's inner corners where the passage faces meet the outline at its far end are the MOUTH_END rows;
    # the passage faces themselves are straight (T-123): no corner inside them.
    print("1. VERTICAL CORNERS (m.l)")
    tot = {}
    for r in out:
        k = (r["floor"], r["kind"])
        t = tot.setdefault(k, [0, 0.0, 0.0, 0.0])
        t[0] += 1
        if r["height_m"] is not None:
            t[1] += r["height_m"]
        else:
            t[2] += r["held_lo_m"]
            t[3] += r["held_hi_m"]
        print(f"   {r['floor']} {r['kind']:9s} {r['sides']:16s} turn {r['turn_deg']!s:>9}  h "
              f"{'HELD %.3f..%.3f' % (r['held_lo_m'], r['held_hi_m']) if r['height_m'] is None else '%.3f' % r['height_m']}"
              f"  {r['note']}")
    G = {"CONVEX": [0, 0.0, 0.0, 0.0], "MOUTH_END": [0, 0.0, 0.0, 0.0], "CONCAVE": [0, 0.0, 0.0, 0.0]}
    for (f, k), t in sorted(tot.items()):
        print(f"   {f} {k}: {t[0]} corners, {t[1]:.3f} m.l measured + HELD {t[2]:.3f}..{t[3]:.3f}")
        for i in range(4):
            G[k][i] += t[i]
    for k, t in G.items():
        print(f"   ALL {k}: {t[0]} corners, {t[1]:.3f} m.l + HELD {t[2]:.3f}..{t[3]:.3f}")
    ext = G["CONVEX"][1] + G["MOUTH_END"][1]
    print(f"   external arrises (CONVEX + MOUTH_END): {ext:.3f} m.l + HELD {G['CONVEX'][2] + G['MOUTH_END'][2]:.3f}.."
          f"{G['CONVEX'][3] + G['MOUTH_END'][3]:.3f}")
    # 2. parapet top edges
    print("\n2. PARAPET TOP, OUTER EDGE (m.l, plan length; wavy tops on 1F SE / NW: the top line is longer)")
    par = {"GF annex (+4.80)": 0.0, "GF house (+6.00)": 0.0, "1F (+11.00 / wave)": 0.0, "2F (+14.40)": 0.0}
    for r in rows:
        for pr in r["portions"]:
            if r["floor"] == "GF" and pr["cls"] == "EDGE":
                par["GF annex (+4.80)" if r.get("block") == "annex" else "GF house (+6.00)"] += pr["len_m"]
            if r["floor"] == "1F" and pr["cls"] == "PARAPET":
                par["1F (+11.00 / wave)"] += pr["len_m"]
            if r["floor"] == "2F":
                par["2F (+14.40)"] += pr["len_m"]
    for k, v in par.items():
        print(f"   {k}: {v:.3f} m.l")
    ptot = sum(par.values())
    print(f"   total outer parapet top edges {ptot:.3f} m.l (the inner top edge of each parapet belongs to the parapet "
          f"inner face, his parapet rows; not in T-159's faces)")
    # 3. opening reveals
    print("\n3. OPENING REVEALS ON THE FACADE (head + jambs + sill; m.l)")
    orows = []
    # r2: composed once by C.opening_arrises (r1 added 2 x height a second time here: jambs double counted)
    agg = C.opening_arrises([(oid, w, hgt, st, sill) for oid, f, sd, w, hgt, st, sill in OPENINGS])
    known, assumed, held_ids = agg["measured"], agg["assumed"], agg["held_ids"]
    for oid, f, sd, w, hgt, st, sill in OPENINGS:
        k, _ = C.opening_reveal_ml(w, hgt, sill)
        orows.append((oid, f, sd, w, hgt, st, sill, agg["per"][oid], k))
    print(f"   {len(OPENINGS)} facade openings: printed / inferred heights -> {known:.3f} m.l (incl. the head / sill "
          f"of the {len(held_ids)} with HELD heights); door jambs at the owner reference 2.20 (ASSUMED) {assumed:.3f} m.l;"
          f" jambs HELD on {len(held_ids)}: {', '.join(held_ids)}")
    se = sum(pr["len_m"] for r in rows for pr in r["portions"] if pr["cls"] == "SLAB_EDGE_BELOW")
    print(f"\n4. 1F slab edge over open air: {se:.3f} m of lower arris (finish HELD, Q-68; depth not printed)")
    summary = {"vertical": {k: {"count": t[0], "measured_ml": round(t[1], 3), "held_ml": [round(t[2], 3),
                                                                                       round(t[3], 3)]}
                            for k, t in G.items()},
               "external_vertical_ml": round(ext, 3),
               "parapet_top_outer_ml": {k: round(v, 3) for k, v in par.items()}, "parapet_top_outer_total_ml":
               round(ptot, 3), "opening_reveals_measured_ml": round(known, 3), "opening_reveals_assumed_ml":
               round(assumed, 3), "opening_jambs_held": held_ids, "slab_edge_over_open_air_m": round(se, 3)}
    print("\nSUMMARY " + json.dumps(summary))
    if len(sys.argv) > 4 and sys.argv[3] == "--csv":
        with open(sys.argv[4], "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["GROUP", "FLOOR", "WHERE", "FACING", "KIND", "TURN_DEG", "LENGTH_ML", "HELD_RANGE_ML", "STATUS",
                        "NOTE"])
            for r in out:
                w.writerow(["VERTICAL", r["floor"], r["sides"], r["facing"], r["kind"], r["turn_deg"],
                            "" if r["height_m"] is None else f"{r['height_m']:.3f}",
                            "" if r["height_m"] is not None else f"{r['held_lo_m']:.3f}..{r['held_hi_m']:.3f}",
                            r["status"], r["note"]])
            for k, v in par.items():
                w.writerow(["PARAPET_TOP_OUTER", k.split()[0], k, "", "HORIZONTAL", "", f"{v:.3f}", "",
                            "DRAWING-CONFIRMED (plan length)", "T-159 EDGE / PARAPET portions; inner edge not here"])
            for oid, f, sd, wd, hgt, st, sill, ml, k in orows:
                w.writerow(["OPENING_REVEAL", f, f"{oid} on {sd}", "", "HEAD+JAMBS" + ("+SILL" if sill else ""), "",
                            "" if ml is None else f"{ml:.3f}", "" if ml is not None else f"{k:.3f}+jambs HELD",
                            st if hgt is not None else "HELD (height)",
                            f"width {wd:.2f}" + ("" if hgt is None else f", height {hgt:.2f}")])
            w.writerow(["SLAB_EDGE_ARRIS", "1F", "porch / pool court", "", "HORIZONTAL", "", f"{se:.3f}", "",
                        "HELD (finish, Q-68)", "length known, depth and finish not printed"])
        print("wrote", sys.argv[4])
    return summary


if __name__ == "__main__":
    main()
