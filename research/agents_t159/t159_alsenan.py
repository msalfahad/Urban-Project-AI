"""T-159 the outside of the house, side by side (development villa; research only, not a method, not wired).

    python3 -I research/agents_t159/t159_alsenan.py <out_dir of t159_extract.py> [--csv FACADE_SIDES_T159.csv]

Reads t159_rings.json (the released engine's facade outline per floor, ARCH_TAKEOFF_V2.9, plus the GF side-passage
reading of FACADE_PASSAGE_WALLS_V1 under owner Q-67 A), splits every outline into SIDES (t159_sides.split_sides),
classifies every straight side against the floor above and below (t159_sides.against_upper: FLUSH / COVERED /
EDGE, computed, not typed in), and gives each side its height bands from the PRINTED levels listed in LEVELS (each
with its sheet). Prints and writes lengths, heights and areas only: no coordinates, no names.

Statuses (WORKFLOW_CONTROLS section 5): DRAWING-CONFIRMED (a printed level / dimension, or the CAD line geometry of
the elevation frame where no dimension is printed: said which), HELD (with the cause and, where the drawing bounds it,
the range), never 0. Nothing here is VERIFIED: the Checker re-measures (Gate A)."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t159_sides as S                                                       # noqa: E402

# plan axes -> compass names of the outward normal. Source: the north arrow on the GF / 1F / 2F plan frames (N points
# to the lower right of the sheet) and the elevation titles: the plan's +x end is marked SEA VIEW and is the NORTH
# WEST elevation (DXF frame title), the street end (-x) is the SOUTH EAST elevation (DXF frame title); +y is the SOUTH
# WEST elevation (sheet 07) side and -y the NORTH EAST (sheet 09) side.
AXES = {"+x": "NW", "-x": "SE", "+y": "SW", "-y": "NE"}

# printed levels (m). Every one is printed; sources are Drive "Alsenan chalet project" sheets / DXF frames.
LEVELS = {
    "G0": (0.00, "external ground +-0.00: all four elevations (DXF SE / NW frames, sheets 07 / 09) and the plot corners"),
    "C15": (0.15, "court / forecourt / porch / passage / pool court +0.15: GF plan level marks; SE elevation chain starts "
                  "at +0.15 under the stair tower; NW elevation +0.15"),
    "R30": (0.30, "pool rim +0.30: NW elevation chain 115 / 70 on the pool axis (+1.00 - 0.70)"),
    "AF": (0.30, "annex F.F.L. +0.30: GF plan marks; SE elevation chain 30 / 400 / 50"),
    "HF": (1.00, "house GF F.F.L. +1.00: GF plan marks; elevation chains 100 / 870 / 420 / 50"),
    "AR": (4.30, "annex roof +4.30: 1F plan mark; SE elevation; sheet 09 NE elevation"),
    "AP": (4.80, "annex parapet top +4.80: SE elevation 30 / 400 / 50 (480); sheets 07 and 09 '480'"),
    "F1": (5.50, "1F F.F.L. and GF roof +5.50: 1F plan marks; NW elevation 100 + 450; sheets 07 / 09 '550'"),
    "GP": (6.00, "GF roof parapet top +6.00: NW elevation 550 + 50; sheets 07 / 09 '550' + '50'"),
    "F2": (9.70, "2F F.F.L. and 1F roof +9.70: 2F plan marks; 100 + 870 on all four elevations"),
    "P1": (11.00, "1F roof parapet top +11.00 on the NE and SW faces: sheets 09 and 07 print '130' above the +9.70 line"),
    "TP": (14.40, "2F parapet top +14.40: '1440' overall and 420 + 50 above +9.70 on all four elevations (the NW frame "
                  "prints 3200 to +14.20 and a 200 top band to +14.40)"),
}

# the outside level in front of each GF side, read on the GF plan / elevations (by hand; T-153's space census agrees)
GF_OUTSIDE = {
    "annex": {"SE-1": "G0", "SW-1": "C15", "SW-2": "C15", "NW-1": "C15", "SW-3": "C15", "NE-6": "G0", "P-1": "C15"},
    "house": {"SW-5": "C15", "SE-2": "C15", "NE-1": "C15", "SE-3": "C15", "SW-6": "C15", "SE-4": "C15", "SW-7": "C15",
              "NW-2": "C15", "NE-2": "C15", "SE-5": "C15", "NE-3": "C15", "NW-3": ("C15", "R30"), "NW-4": ("C15", "R30"),
              "NW-5": ("C15", "R30"), "SW-8": ("C15", "R30"), "NW-6": "C15", "SW-9": "C15", "NW-7": "G0",
              "NE-4": "G0", "P-2": "C15"},
}
# GF arcs (no straight-line classification): what stands above, read by hand
GF_ARC_ABOVE = {"SW-2": ("EDGE", "annex dewaneya corner: annex roof, no 1F above (1F plan)"),
                "NW-4": ("COVERED", "pool glazing W03: NW elevation chain 430 + 20 from +1.00 to the +5.50 slab")}

# 1F parapet over the +9.70 roof on EDGE sides: printed (P1) or the CAD top line of the elevation frame (area above
# +9.70 integrated along the side; t159 profile reading in the scratchpad, re-measurable by the Checker)
P1_PARAPET = {
    "NE-2": ("PRINTED", 1.30, None, "sheet 09 NE elevation '130' above +9.70"),
    "SW-3": ("PRINTED", 1.30, None, "sheet 07 SW elevation '130' above +9.70"),
    "SE-1": ("CAD", None, 7.8070, "DXF SE frame: top line of the wavy parapet + coping, +11.30 at the NE end ('6800' "
                                  "from +4.30 and '200'), falling to +10.085 at the SW end; 7.807 m2 over 7.500 m, mean "
                                  "+10.741; railing above it (layer 5) not a wall face"),
    "NW-1": ("CAD", None, 1.5206, "DXF NW frame: top line +11.00 (mean 1.2996 above +9.70)"),
    "NW-2": ("CAD_ARC", 1.2996, None, "DXF NW frame: top line +11.00 over the arc's chord; area = mean x TRUE arc length"),
    "NW-3": ("CAD", None, 0.7511, "DXF NW frame: top line +11.00"),
    "NW-4": ("CAD", None, 0.5135, "DXF NW frame: top line +10.80 over the window recess (mean 1.0996)"),
    "NW-5": ("CAD", None, 3.0134, "DXF NW frame: +10.80 at the NE corner curving down to a +9.80 wall top (X railing "
                                  "above it, not a wall face), then +11.00; 3.0037 m2 integrated + 0.0097 m2 for 0.057 m "
                                  "where the same curve is drawn on layer 4 (+9.87)"),
    "NE-1": ("HELD_RANGE", (1.0996, 1.2996), None, "0.08 m return of the 1F window recess: top between the recess "
                                                    "(+10.80) and the face (+11.00); no line shows which"),
    "SW-1": ("HELD_RANGE", (1.0996, 1.2996), None, "0.08 m return of the 1F window recess, as NE-1"),
    "SW-2": ("HELD_RANGE", (0.385, 1.60), None, "1F SW face over the porch: its parapet top is drawn as a curve on "
                                                "sheet 07 (raster) with no dimension; bounded by the SE wave's end "
                                                "(+10.085) and its top (+11.30)"),
}
# 1F arcs: what is under them on the GF, read by hand: the 1F curved window band (W17) stands over the pool court,
# outside the GF plate (the GF pool glazing curves the same way 1.83 m further in)
ARC_BELOW = {"NW-2": "EDGE"}
# 1F portions over a lower roof (COVERED by the GF plate): that roof's printed level
LOWER_ROOF = {"SE-1": "AR"}           # the 1F SE face stands on the annex roof (+4.30) over its NE 3.40 m


def lv(k):
    return LEVELS[k][0]


def band(lo, hi, src, status="DRAWING-CONFIRMED", rng=None):
    return {"bottom": lo, "top": hi, "h": None if lo is None or hi is None else round(hi - lo, 6), "source": src,
            "status": status, "range_h": rng}


def local(R, f):
    b = R["floors"][f]["box"]
    out = []
    for e in R["floors"][f]["edges"]:
        g = dict(e)
        g["a"] = [e["a"][0] - b[0], e["a"][1] - b[1]]
        g["b"] = [e["b"][0] - b[0], e["b"][1] - b[1]]
        if "c" in e:
            g["c"] = [e["c"][0] - b[0], e["c"][1] - b[1]]
        out.append(g)
    return out


def build(R):
    E = {f: local(R, f) for f in ("GF", "1F", "2F")}
    p = R["floors"]["GF"]["passage"]
    drop = [m["edge_index"] for ps in p["passages"] if ps["state"] == "OPEN_AIR" for m in ps["mouths"]
            if m["edge_index"] not in p["wall_end_gaps"]]
    sides = {f: S.name_sides(S.split_sides(E[f], AXES, drop if f == "GF" else ())) for f in E}
    rows = []
    # ---------------------------------------------------------------- GF
    annex = set(GF_OUTSIDE["annex"])
    for s in sides["GF"]:
        if s["kind"] == "NOT_A_FACE":
            rows.append(dict(floor="GF", side=s["name"], kind="NOT_A_FACE", len_m=s["len_m"], facing=s["facing"],
                             portions=[], bands=[], openings=s["openings"],
                             note="passage mouth / boundary-wall end removed from the run (owner Q-67 A, T-109 / T-123)"))
            continue
        blk = "annex" if s["name"] in annex else "house"
        out = GF_OUTSIDE[blk][s["name"]]
        ffl = "AF" if blk == "annex" else "HF"
        if s["kind"] == "ARC":
            cls = {GF_ARC_ABOVE[s["name"]][0]: s["len_m"]}
        else:
            c = S.against_upper(s, E["GF"], E["1F"])
            cls = {k: v for k, v in c.items() if v > 1e-6}
            # the classifier gives the split of the straight length; keep the exact side length on the last portion
        portions = []
        for k, L in cls.items():
            if k == "EDGE":
                top = "AP" if blk == "annex" else "GP"
            else:
                top = "F1"           # FLUSH: the 1F face continues from +5.50; COVERED: the 1F plate is over the face
            bands = []
            if isinstance(out, tuple):
                lo, hi = lv(out[0]), lv(out[1])
                bands.append(band(None, lv(ffl), "plinth: outside level " + LEVELS[out[0]][1] + " / " + LEVELS[out[1]][1],
                                  "HELD", (round(lv(ffl) - hi, 6), round(lv(ffl) - lo, 6))))
            else:
                bands.append(band(lv(out), lv(ffl), "plinth: " + LEVELS[out][1] + " -> " + LEVELS[ffl][1]))
            bands.append(band(lv(ffl), lv(top), "storey: " + LEVELS[ffl][1] + " -> " + LEVELS[top][1]
                              + ("" if k != "COVERED" else " (face under the 1F plate: band to the slab top, owner "
                                                           "Q-07; the soffit level itself is not printed)")))
            portions.append({"cls": k, "len_m": L, "bands": bands})
        rows.append(dict(floor="GF", side=s["name"], kind=s["kind"], len_m=s["len_m"], facing=s["facing"],
                         block=blk, portions=portions, openings=s["openings"]))
    # the two passage faces (owner Q-67 A, T-109 / T-123): 4.700 m each, under the GF roof slab / 1F floor
    # P-1: the annex's face across the passage looks along +x (NW); P-2: the house's face looks along -x (SE)
    walls = [w for ps in p["passages"] for w in ps["walls"]]
    xs = sorted({round(w["at"][0][0], 3) for w in walls})
    for nm, blk, ffl, x in (("P-1", "annex", "AF", xs[0]), ("P-2", "house", "HF", xs[-1])):
        ops = [(w["opening_id"], w["len_m"]) for w in walls if w["opening_id"] and round(w["at"][0][0], 3) == x]
        Lp = round(sum(w["len_m"] for w in walls if round(w["at"][0][0], 3) == x), 6)
        rows.append(dict(floor="GF", side=nm, kind="PASSAGE", len_m=Lp,
                         facing="NW" if nm == "P-1" else "SE", block=blk, openings=ops,
                         portions=[{"cls": "COVERED", "len_m": Lp, "bands": [
                             band(lv("C15"), lv(ffl), "plinth: " + LEVELS["C15"][1] + " -> " + LEVELS[ffl][1]),
                             band(lv(ffl), lv("F1"), "storey: to the +5.50 slab top over the roofed passage (T-123 "
                                                     "section 4; owner Q-07)")]}],
                         note="passage walls of FACADE_PASSAGE_WALLS_V1 total %.3f m (both faces)" %
                              sum(w["len_m"] for w in walls)))
    # ---------------------------------------------------------------- 1F
    for s in sides["1F"]:
        up = S.against_upper(s, E["1F"], E["2F"])
        down = S.against_upper(s, E["1F"], E["GF"])
        L = s["len_m"]
        portions = []
        # bottom: over a lower roof (the GF plate under the face) -> that roof; flush / overhang -> +5.50 (Q-07)
        if down is None:
            # a 1F arc: read by hand (ARC_BELOW)
            parts_b = [("FROM_F1", L)] + ([("SLAB_EDGE_BELOW", L)] if ARC_BELOW.get(s["name"]) == "EDGE" else [])
        else:
            lo_roof = down["COVERED"] if s["name"] in LOWER_ROOF else 0.0
            parts_b = [("OVER_LOWER_ROOF", lo_roof)] if lo_roof > 1e-6 else []
            if L - lo_roof > 1e-6:
                parts_b.append(("FROM_F1", L - lo_roof))
            if down["EDGE"] > 1e-6:
                parts_b.append(("SLAB_EDGE_BELOW", down["EDGE"]))
        for k, Lp in parts_b:
            if k == "OVER_LOWER_ROOF":
                r = LOWER_ROOF[s["name"]]
                portions.append({"cls": k, "len_m": Lp, "bands": [
                    band(lv(r), lv("F1"), "face between the lower roof and the 1F floor: " + LEVELS[r][1] +
                         "; SE elevation '6800' is measured from it")]})
            elif k == "SLAB_EDGE_BELOW":
                portions.append({"cls": k, "len_m": Lp, "bands": [
                    band(None, lv("F1"), "1F slab edge over open air (porch / pool court) below +5.50: slab depth "
                                         "not printed on the architectural sheets (owner Q-68: candidate exterior "
                                         "slab edge, finish HELD)", "HELD")]})
        # storey band +5.50 -> +9.70 over the whole side (flush to 2F, covered, or to the 1F roof)
        storey = band(lv("F1"), lv("F2"), "storey: " + LEVELS["F1"][1] + " -> " + LEVELS["F2"][1])
        portions.append({"cls": "STOREY", "len_m": L, "bands": [storey]})
        # parapet above +9.70 where the side is a roof edge (EDGE against 2F); arcs are roof edges here (2F is
        # far behind: hand)
        edge_len = L if up is None else up["EDGE"]
        if edge_len > 1e-6:
            kind, h, area, src = P1_PARAPET[s["name"]]
            if kind == "PRINTED":
                b = band(lv("F2"), lv("F2") + h, "parapet: " + src)
            elif kind == "CAD":
                b = band(lv("F2"), round(lv("F2") + area / edge_len, 6), "parapet (CAD line, no dimension): " + src)
                b["area_m2"] = area
            elif kind == "CAD_ARC":
                b = band(lv("F2"), lv("F2") + h, "parapet (CAD line): " + src)
            else:
                b = band(lv("F2"), None, "parapet HELD: " + src, "HELD", h)
            portions.append({"cls": "PARAPET", "len_m": edge_len, "bands": [b]})
        rows.append(dict(floor="1F", side=s["name"], kind=s["kind"], len_m=L, facing=s["facing"], block="house",
                         portions=portions, openings=s["openings"], above=up, below=down))
    # ---------------------------------------------------------------- 2F
    for s in sides["2F"]:
        rows.append(dict(floor="2F", side=s["name"], kind=s["kind"], len_m=s["len_m"], facing=s["facing"],
                         block="house", openings=s["openings"],
                         portions=[{"cls": "STOREY+PARAPET", "len_m": s["len_m"], "bands": [
                             band(lv("F2"), lv("TP"), "2F: " + LEVELS["F2"][1] + " -> " + LEVELS["TP"][1])]}]))
    return sides, rows


def areas(row):
    """-> (measured m2, held low, held high, held without a bound?) of one side; a band with an area of its own
    (CAD) uses it; a HELD band adds its range."""
    m, lo, hi, unb = 0.0, 0.0, 0.0, False
    for pr in row["portions"]:
        for b in pr["bands"]:
            if b.get("area_m2") is not None:
                m += b["area_m2"]
            elif b["h"] is not None:
                m += pr["len_m"] * b["h"]
            elif b.get("range_h"):
                lo += pr["len_m"] * b["range_h"][0]
                hi += pr["len_m"] * b["range_h"][1]
            else:
                unb = True
    return m, lo, hi, unb


# openings on the facade whose height IS printed (T-144 evidence, READY, not yet verified; widths as printed / answered)
PRINTED_OPENINGS = [
    ("GF", "SE-2", "OP-021 main door D01", 2.00, 2.50, "SE elevation chain 85 / 250 from +0.15: +1.00 to +3.50"),
    ("GF", "NW-4", "pool glazing W03", 6.57, 4.30, "NW elevation 430 from +1.00 to +5.30; width printed 6.57 (owner "
                                                   "Q-38 A); the outline walks its frame arc 6.658 m"),
    ("1F", "SE-1", "OP-022 W14", 2.45, 1.60, "SE elevation chain: +6.90 to +8.50 (T-144 corrected reading)"),
    ("1F", "NW-2", "COP-001 W17 (outer face width)", 2.976663, 3.50, "NW elevation 305 + 45 from +5.50: to +9.00"),
]


# the freelancer's exterior plaster rows (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, file PLS rows 51-93):
# wall rows per elevation (height x length) and the other rows, as he wrote them
FREELANCER = {
    "SW": [(6.0, 1.5), (10.0, 6.9), (14.4, 7.9), (5.25, 4.0), (4.8, 13.0)],
    "SE": [(14.4, 6.75), (11.85, 5.25), (4.8, 1.5)],
    "NE": [(4.8, 10.0), (10.0, 19.2), (6.0 * 2, 1.5)],
    "NW": [(6.0, 1.5), (9.8, 6.75), (5.7, 4.95), (5.5, 4.95), (5.5 * 2, 4.95)],
    "ROOF": [(4.7, 17.75)],
}
FREELANCER_OTHER = {"frames (SE 24.93, NW 3.9375)": 28.8675, "dome inside + outside": 181.806,
                    "soffit over the pool": 19.154, "parapets (1.7 x 48.47, 0.7 x 28.4, 0.7 x 36.2, 0.7 x 27.2)": 146.659,
                    "boundary fence": 107.24, "drip edge (0.28 x 181.7)": 50.876}


def main():
    out = Path(sys.argv[1])
    R = json.loads((out / "t159_rings.json").read_text())
    sides, rows = build(R)
    # 1. re-add check
    print("1. SIDES RE-ADD TO THE RUN")
    for f in ("GF", "1F", "2F"):
        tot = sum(s["len_m"] for s in sides[f])
        print(f"   {f}: {len(sides[f])} sides = {tot:.6f} m; engine run {R['floors'][f]['perimeter_m']:.6f} m; "
              f"difference {tot - R['floors'][f]['perimeter_m']:+.6f} m")
    gf_faces = sum(r["len_m"] for r in rows if r["floor"] == "GF" and r["kind"] != "NOT_A_FACE")
    print(f"   GF faces (mouths removed, passage faces added) {gf_faces:.6f} m; FACADE_PASSAGE_WALLS_V1 run "
          f"{R['floors']['GF']['passage']['run_m']:.6f} m; Q-64 B billable 105.786694 m once a reveal line measures "
          f"the two 0.050 m notch returns (none does: T-123)")
    # 2. per side
    print("\n2. SIDE BY SIDE (length m; bands bottom -> top m; area m2; HELD as a range, never 0)")
    table, by_face = [], {}
    for r in rows:
        m, lo, hi, unb = areas(r)
        r.update(measured_m2=m, held_lo_m2=lo, held_hi_m2=hi, held_unbounded=unb)
        bands_txt = "; ".join(
            f"{pr['cls']} {pr['len_m']:.4f} m: " + ", ".join(
                (f"{b['bottom']:+.2f}" if b['bottom'] is not None else "?") + "->" +
                (f"{b['top']:+.3f}" if b['top'] is not None else "?") +
                (f" HELD{list(b['range_h'])}" if b['status'] == "HELD" and b.get('range_h') else
                 (" HELD" if b['status'] == "HELD" else "")) for b in pr["bands"]) for pr in r["portions"])
        ops = ", ".join(f"{k.split('|')[0]} {w:.3f}" for k, w in r["openings"])
        print(f"   {r['floor']} {r['side']:5s} {r['facing']} {r['kind']:10s} L {r['len_m']:8.4f}  "
              f"measured {m:9.3f}  held {lo:7.3f}..{hi:7.3f}{' +unbounded' if unb else ''}  | {bands_txt}"
              + (f" | openings {ops}" if ops else ""))
        if r["kind"] != "NOT_A_FACE":
            f = by_face.setdefault(r["facing"], [0.0, 0.0, 0.0, 0.0])
            f[0] += r["len_m"] if r["floor"] == "GF" else 0.0
            f[1] += m
            f[2] += lo
            f[3] += hi
        table.append(r)
    # 3. totals
    print("\n3. TOTALS BY ELEVATION (gross: openings included, plinth included, railings / domes / parapet inner "
          "faces / soffits / slab edges over open air excluded)")
    T = [0.0, 0.0, 0.0]
    for k in ("NE", "SE", "SW", "NW"):
        f = by_face.get(k, [0, 0, 0, 0])
        fl = sum(fr[1] for fr in FREELANCER[k] for fr in [(fr[0], fr[0] * fr[1])]) if False else \
            sum(h * l for h, l in FREELANCER[k])
        print(f"   {k}: measured {f[1]:9.3f} m2 + held {f[2]:7.3f}..{f[3]:7.3f} m2 | freelancer wall rows {fl:9.3f} m2"
              f" | measured vs freelancer {f[1] - fl:+9.3f} m2 ({(f[1] - fl) / fl * 100:+.1f} %)")
        T[0] += f[1]
        T[1] += f[2]
        T[2] += f[3]
    flw = sum(h * l for k in FREELANCER for h, l in FREELANCER[k])
    print(f"   ALL: measured {T[0]:9.3f} m2 + held {T[1]:7.3f}..{T[2]:7.3f} m2 (gross {T[0] + T[1]:.3f}..{T[0] + T[2]:.3f})"
          f" | freelancer wall rows incl. 'roof facade' {flw:.3f} m2 | difference on the measured part "
          f"{T[0] - flw:+.3f} m2 ({(T[0] - flw) / flw * 100:+.1f} %)")
    print(f"   freelancer other exterior plaster rows: " + "; ".join(f"{k} {v}" for k, v in FREELANCER_OTHER.items()))
    q07 = sum(r["len_m"] * 0 for r in rows)
    plinth = 0.0
    for r in rows:
        for pr in r["portions"]:
            for b in pr["bands"]:
                if b["source"].startswith("plinth") and b["h"] is not None:
                    plinth += pr["len_m"] * b["h"]
    print(f"   of the measured part, plinth bands (outside level -> F.F.L.) {plinth:.3f} m2 (UP-FACADE-001 holds the "
          f"plinth as an RFI; owner Q-07 bands start at the floor) -> storey + parapet bands {T[0] - plinth:.3f} m2"
          + ("" if q07 == 0 else ""))
    # 4. per floor, slab edges, openings
    print("\n4. PER FLOOR, HELD ITEMS AND OPENINGS")
    for f in ("GF", "1F", "2F"):
        rs = [r for r in rows if r["floor"] == f and r["kind"] != "NOT_A_FACE"]
        print(f"   {f}: faces {sum(r['len_m'] for r in rs):.6f} m, measured {sum(r['measured_m2'] for r in rs):.3f} m2, "
              f"held {sum(r['held_lo_m2'] for r in rs):.3f}..{sum(r['held_hi_m2'] for r in rs):.3f} m2")
    se = sum(pr["len_m"] for r in rows for pr in r["portions"] if pr["cls"] == "SLAB_EDGE_BELOW")
    print(f"   1F slab edge over open air (porch, pool court): {se:.4f} m, height HELD (slab depth not printed on the "
          f"architectural sheets; owner Q-68 lists slab edges as a candidate, finish HELD) - not in the totals")
    ow = sum(w for r in rows if r["kind"] != "NOT_A_FACE" for _, w in r["openings"])
    print(f"   openings on the faces (widths on the outline, every floor): {ow:.4f} m; heights printed for:")
    tot_p = 0.0
    for fl, sd, op, w, h, src in PRINTED_OPENINGS:
        a = w * h
        tot_p += a
        print(f"     {fl} {sd} {op}: {w:.3f} x {h:.2f} = {a:.3f} m2 ({src})")
    print(f"     subtotal with printed heights {tot_p:.3f} m2; every other opening: height HELD (T-144: no head / sill "
          f"printed); net facade HELD: UP-GEN-003 1.1.0 leaves PLASTER_PAINT openings to owner decision Q-OPN-1")
    summary = {"runs_m": {f: R["floors"][f]["perimeter_m"] for f in ("GF", "1F", "2F")},
               "gf_faces_m": round(gf_faces, 6),
               "by_facing_m2": {k: {"measured": round(v[1], 3), "held_lo": round(v[2], 3), "held_hi": round(v[3], 3)}
                                for k, v in by_face.items()},
               "measured_m2": round(T[0], 3), "held_m2": [round(T[1], 3), round(T[2], 3)],
               "plinth_m2": round(plinth, 3), "storey_and_parapet_m2": round(T[0] - plinth, 3),
               "slab_edge_over_open_air_m": round(se, 4), "opening_widths_m": round(ow, 4),
               "printed_opening_area_m2": round(tot_p, 3),
               "freelancer_wall_rows_m2": round(flw, 3), "freelancer_other_rows_m2": FREELANCER_OTHER}
    (out / "t159_summary.json").write_text(json.dumps(summary, indent=1))
    if len(sys.argv) > 3 and sys.argv[2] == "--csv":
        with open(sys.argv[3], "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["FLOOR", "SIDE", "FACING", "KIND", "LENGTH_M", "PORTION", "PORTION_LEN_M", "BOTTOM_M", "TOP_M",
                        "HEIGHT_M", "AREA_M2", "STATUS", "HELD_RANGE_H_M", "SOURCE", "OPENINGS_ON_OUTLINE_M"])
            for r in table:
                ops = "; ".join(f"{k.split('|')[0]} {wd:.3f}" for k, wd in r["openings"])
                if not r["portions"]:
                    w.writerow([r["floor"], r["side"], r["facing"], r["kind"], f"{r['len_m']:.4f}", "", "", "", "",
                                "", "", "NOT A FACE", "", r.get("note", ""), ops])
                for pr in r["portions"]:
                    for b in pr["bands"]:
                        a = b.get("area_m2")
                        if a is None and b["h"] is not None:
                            a = pr["len_m"] * b["h"]
                        w.writerow([r["floor"], r["side"], r["facing"], r["kind"], f"{r['len_m']:.4f}", pr["cls"],
                                    f"{pr['len_m']:.4f}",
                                    "" if b["bottom"] is None else f"{b['bottom']:.3f}",
                                    "" if b["top"] is None else f"{b['top']:.3f}",
                                    "" if b["h"] is None else f"{b['h']:.4f}",
                                    "" if a is None else f"{a:.4f}", b["status"],
                                    "" if not b.get("range_h") else f"{b['range_h'][0]:.4f}..{b['range_h'][1]:.4f}",
                                    b["source"], ops])
        print(f"\nwrote {sys.argv[3]}")


if __name__ == "__main__":
    main()
