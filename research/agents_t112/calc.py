"""T-112: Alsenan wall heights per room by BOTH methods side by side (hand table, NO REPO CODE; standard library only).

(a) OWNER MANUAL METHOD (owner Q-43 2026-10-19 21:40, Q-48 A, preserved by the owner correction 2026-10-20 12:15):
    wall height = floor-to-floor (slab to slab from the printed level marks) - 0.60 beam - 0.15 decor - 0.10 floor
    finishing; one height for plaster and paint (Q-43) and for wet-wall tiles (Q-48 A).
(b) DRAWING-DERIVED METHOD (owner Q-52 C modified, directive 2026-10-20 Part 3): per room, what the current drawings
    establish: floor level, floor-to-floor, structural slab 0.16 m (structural general note, ST7757), the beams that
    cross the room (structural roof-slab plans laid over the architectural plans by column translation), printed
    opening heads (T-083), ceiling openings (dome / skylight openings in the roof slab). No sheet prints a ceiling
    level, a false ceiling, a bulkhead or a floor build-up (T-091 census): the finished ceiling plane is UNKNOWN, so
    the drawing-derived paint height and plaster height are HELD in every room; this script gives the envelope the
    drawings allow and the checks of the owner-method line against them. Nothing here is released.
(c) the difference and its cause.

Every input is typed below with its source (Drive "Alsenan chalet project" titles; research/agents_t088, t090, t083,
t091 merged hand tables). No coordinates, no client data. Run: python3 -I calc.py  -> ROOMS_T112.csv + summary.
"""
import csv
import os

SLAB = 0.16          # ST7757 general note (S-NOTE): all slabs 16 cm unless stated otherwise (decoded Arabic SHX)
OWNER_BEAM, OWNER_DECOR, OWNER_FLOOR = 0.60, 0.15, 0.10   # owner Q-43 (decor 0.15 by Q-48 A)
B_OWNER = 0.10       # owner's 0.10 floor finishing, used ONLY as a labelled ASSUMED build-up in the envelope

# zone: (floor-to-floor m or None, source, datum status)
ZONES = {
    "GF_MAIN": (4.50, "+1.00 to +5.50: A-A sheet 10 '450', B-B page 11 '450'", "VERIFIED_MARKS"),
    "GF_ANNEX": (4.00, "+0.30 to +4.30: B-B page 11 '400'", "DATUM_HELD_Q54B"),
    "1F": (4.20, "+5.50 to +9.70: A-A / B-B '420'", "VERIFIED_MARKS"),
    "2F": (4.20, "+9.70 to +13.90: A-A '420'", "VERIFIED_MARKS"),
    "LEVEL_UNCLEAR": (None, "room level +0.30 or +1.00 not drawn (T-088)", "HELD"),
    "STAIR": (None, "stair-shaft walls run through the storeys (T-088)", "HELD"),
}

# row, room, kind, zone, wall length (None = no closed printed run), length source,
# crossing beams [(mark, depth)], edge beams text, printed head above FFL (m) + source, ceiling special, freelancer m2
R = [
    ("GF-01", "dewaneya", "DRY", "GF_ANNEX", 20.128, "400 x 630 + R1.10 corner (T-088/T-090)",
     [("CB6", 0.75)], "B9 / CB7 / B7 curved 0.75; B2 0.40; B4 0.50", None, "", 72.00),
    ("GF-02", "wash by the dewaneya (Q-06 wet)", "WET", "GF_ANNEX", 7.20, "150 x 210 (T-074/T-090)",
     [], "CB6 0.75 on its edge; B4 0.50", None, "", None),
    ("GF-03", "W.C. by the dewaneya", "WET", "GF_ANNEX", 7.50, "150 x 225", [], "0.75 on edges (T-088)", None, "", None),
    ("GF-04", "driver room", "DRY", "GF_ANNEX", 12.50, "175 x 450", [], "CB6 / CB7 0.75 on edges", None, "", 45.00),
    ("GF-05", "driver W.C. 130 x 150", "WET", "GF_ANNEX", 5.60, "130 x 150", [], "0.75 on edges", None, "", None),
    ("GF-06", "kitchen (Q-30 wet)", "WET", "GF_ANNEX", 14.50, "300 x 270 + 105 x 150 less piers (T-074)",
     [], "CB6 / CB7 0.75 on edges", None, "", None),
    ("GF-07", "pantry (open to the dining, Q-37)", "WET", "GF_MAIN", None, "450 x 300, one side open",
     [("B27", 0.85)], "", None, "", None),
    ("GF-08", "dining / reception / saloon open room", "DRY", "GF_MAIN", None, "partial runs only; part under the GF void",
     [("B26", 0.85), ("B27", 0.85)], "CB3 / CB8 0.75 on edges", (2.50, "D01 main entrance +1.00 to +3.50 (SE p.6, T-083)"),
     "part of the room is under the roof-slab VOID (double height)", 195.30),
    ("GF-09", "GF stair hall", "DRY", "STAIR", None, "landings only", [], "0.75", None, "", None),
    ("GF-10", "W.C. 175 x 135 by the stair", "WET", "LEVEL_UNCLEAR", 6.20, "175 x 135", [], "0.50", None, "", None),
    ("GF-11", "basin space 110 x 135 (Q-06 wet)", "WET", "LEVEL_UNCLEAR", 4.90, "110 x 135, upper bound", [], "0.40",
     None, "", None),
    ("GF-12", "W.C. core wedge 289 x 167", "WET", "GF_MAIN", 7.414, "hand trace (T-074)", [], "0.50", None, "", None),
    ("GF-13", "W.C. core wedge 245 x 167", "WET", "GF_MAIN", 6.81, "hand trace (T-074)", [], "0.50", None, "", None),
    ("GF-14", "wash, core lobby with 2 basins (Q-06 wet)", "WET", "GF_MAIN", 9.50, "drawn outline (T-074)",
     [("B11", 0.75)], "", None, "", None),
    ("GF-15", "master bed room", "DRY", "GF_MAIN", None, "curved / glazed side not closed by printed runs",
     [], "B8 0.75 on the pool-side glazing line; B16 / B24 / B17 0.75 on the others",
     (4.30, "W03 pool-side glazing +1.00 to +5.30 (NW p.8 chain 115/70/430/20, T-083)"), "", 75.78),
    ("GF-16", "bath of the master bed room", "WET", "GF_MAIN", 7.6245, "T-074", [], "0.75 on edges", None, "", None),
    ("1F-01", "master bed room west 425 x 450", "DRY", "1F", 17.50, "425 x 450 printed; DXF faces (T-090)",
     [("B6", 0.50)], "B23 0.75; CB10 0.75", (2.80, "W14 sill +6.70 head +8.30 (SE p.6 chain 220/160/139, T-083)"),
     "west 1F-roof dome opening (ring B4, 4.42 m) over most of the room: open skylight by owner Q-29 / Q-44", 59.50),
    ("1F-02", "bath west upper 245 x 205", "WET", "1F", 9.00, "245 x 205", [], "B6 0.50; B4 0.50; CB10 0.75", None,
     "west dome opening reaches over part of the bath; the bed-room / bath partition runs under the opening", None),
    ("1F-03", "bath west lower 245 x 205", "WET", "1F", 9.00, "245 x 205", [], "B6 0.50; B4 0.50", None,
     "west dome opening reaches over part of the bath; the bed-room / bath partition runs under the opening", None),
    ("1F-04", "master bed room 500 x 365", "DRY", "1F", 17.30, "500 x 365 printed", [], "0.75 on edges", None, "",
     58.82),
    ("1F-05", "corridor / stair landing", "DRY", "1F", None, "runs 195 / 125 / 240 / 305 / 147, open", [], "0.75", None,
     "", None),
    ("1F-06", "1F stair hall", "DRY", "STAIR", None, "-", [], "0.75", (3.30, "W13 +6.50 to +8.80 (SE p.6, T-083)"), "",
     None),
    ("1F-07", "laundry", "WET", "1F", 16.94, "T-074", [], "0.50", None, "", None),
    ("1F-08", "W.C. 147 x 180", "WET", "1F", 6.54, "147 x 180", [], "0.50", None, "", None),
    ("1F-09", "bath by the laundry 200 x 180", "WET", "1F", 7.60, "T-074", [], "0.50", None, "", None),
    ("1F-10", "master bed room 380 x 430", "DRY", "1F", 16.20, "380 x 430 room rectangle",
     [("B19", 0.75), ("B6", 0.50)], "B11 / B4 0.75 / 0.50", None, "", 75.82),
    ("1F-11", "master bed room east (curved glazing W17)", "DRY", "1F", None, "curved wall round W17 not dimensioned",
     [], "CB12 0.75 on the void side (to check)", (3.70, "W17 crown: chain 20 / 305 / 45 above +5.50 (NW p.8, T-083)"),
     "", 74.46),
    ("1F-12", "bath east 210 x 225", "WET", "1F", 8.70, "210 x 225", [], "0.75",
     (3.00, "W18 sill +6.34 head +8.50 (NW p.8, T-083)"), "", None),
    ("1F-13", "living area", "DRY", "1F", None, "open to the void and the curved stair", [], "B25 / CB12 0.75; B6 0.50",
     (3.10, "W15 height 3.10 (NW p.8, sill not printed: head >= 3.10)"),
     "east 1F-roof dome opening (ring, 4.42 m) over the room: open skylight by owner Q-29 / Q-44", 140.88),
    ("2F-01", "2F stair lobby 450 x 195", "DRY", "STAIR", None, "open to the stair", [], "B15 1.20", None, "", 30.60),
    ("2F-02", "W.C. 300 x 185", "WET", "2F", 9.70, "300 x 185", [], "0.75", None, "", None),
    ("2F-03", "maid room 300 x 645", "DRY", "2F", 18.90, "300 x 645 printed", [("B2", 0.40)], "B7 0.75; B3 0.40",
     None, "architecture: third dome drawn over the room (2F plan dashed circle, SE / NW elevations); structure: flat "
     "slab, no opening, no ring (C-1); owner Q-27 A three domes, Q-29 open skylight: CONFLICT", 64.26),
]


# opening whose wall line carries a drawn beam (overlay): row -> (beam, depth, certainty)
HEAD_WALL_BEAM = {"GF-15": ("B8", 0.75, "PROBABLE: the straight pool-side glazing of the room is drawn under B8; that "
                                        "W03 is this glazing (and not the curved pool wall) is T-083's reading"),
                  "1F-11": ("CB12", 0.75, "TO CHECK: CB12 runs on the void side near W17")}


def r3(x):
    return None if x is None else round(x + 1e-12, 3)


def row(rec):
    rid, room, kind, zone, L, lsrc, cross, edge, head, special, fl = rec
    f2f, f2f_src, datum = ZONES[zone]
    trade = "plaster + paint (dry)" if kind == "DRY" else "wall tile to the decor ceiling (wet, Q-48 A)"
    out = {"ROW": rid, "ROOM": room, "KIND": kind, "TRADE": trade, "ZONE": zone,
           "FLOOR_TO_FLOOR_M": f2f if f2f else "HELD", "FTF_SOURCE": f2f_src, "DATUM": datum,
           "WALL_LENGTH_M": L if L else "HELD", "LENGTH_SOURCE": lsrc}
    # (a) owner manual method
    if f2f is None:
        h_o, st_o = None, "HELD (" + f2f_src + ")"
    else:
        h_o = round(f2f - OWNER_BEAM - OWNER_DECOR - OWNER_FLOOR, 3)
        st_o = "OWNER METHOD, CALCULATED" if datum == "VERIFIED_MARKS" else \
            "OWNER METHOD on the printed marks; NOT RELEASABLE: +4.30 datum HELD (owner Q-54 B)"
    out.update({"OWNER_H_M": h_o if h_o else "HELD", "OWNER_STATUS": st_o,
                "OWNER_GROSS_M2": r3(h_o * L) if (h_o and L) else "HELD"})
    # (b) drawing-derived envelope
    dg = f2f if datum == "VERIFIED_MARKS" else None          # the drawing envelope needs a verified datum (Q-54 B)
    s0 = r3(dg - SLAB) if dg else None                        # slab soffit above own FFL, build-up above = 0
    s1 = r3(dg - SLAB - B_OWNER) if dg else None              # same with the owner's 0.10 build-up (ASSUMED)
    hx = max([d for _, d in cross], default=None)
    bx1 = r3(f2f - hx - B_OWNER) if (f2f and hx) else None     # on the printed marks (annex: owner-method check only)
    hd = head[0] if head else None
    out.update({
        "DWG_SLAB_SOFFIT_MAX_M (b=0)": s0 if s0 else "HELD",
        "DWG_SLAB_SOFFIT_M (b=0.10 ASSUMED)": s1 if s1 else "HELD",
        "CROSSING_BEAMS": "; ".join(f"{m} {d:.2f}" for m, d in cross) or "none",
        "DWG_CROSSING_BEAM_SOFFIT_M (b=0.10 ASSUMED)": bx1 if bx1 else "-",
        "EDGE_BEAMS": edge,
        "PRINTED_HEAD_MAX_M": hd if hd else "none printed", "HEAD_SOURCE": head[1] if head else "",
        "CEILING_SPECIAL": special or "-",
    })
    # status of the drawing-derived heights (never a number: no ceiling plane is drawn)
    why = ["no ceiling level, false ceiling or bulkhead printed on any sheet (T-091)",
           "floor build-up not printed (slab top below FFL unknown)"]
    if datum == "DATUM_HELD_Q54B":
        why.insert(0, "+4.30 is not shown to be the structural slab (owner Q-54 B; see note section 2)")
    if f2f is None:
        why.insert(0, f2f_src)
    if special:
        why.insert(0, "ceiling opening / conflict above the room")
    out["DWG_PAINT_H"] = "HELD"
    out["DWG_PLASTER_H"] = "HELD (plaster to the ceiling or to the slab soffit: specification not printed)"
    out["DWG_HELD_REASON"] = "; ".join(why)
    # envelope of the paint height the drawings allow: lower = printed head, upper = slab soffit (b=0)
    lo = hd
    out["DWG_PAINT_H_RANGE_M"] = (f"{lo:.2f} .. {s0:.2f}" if (lo and s0) else
                                  f"(no printed lower bound) .. {s0:.2f}" if s0 else "HELD")
    out["DWG_M2_UPPER (L x soffit b=0)"] = r3(L * s0) if (L and s0) else "HELD"
    out["DWG_M2_LOWER (L x printed head)"] = r3(L * lo) if (L and lo) else "-"
    # (c) differences and checks of the owner line against the drawings
    flags = []
    if h_o and s1:
        out["OWNER_MINUS_SOFFIT_M (b=0.10)"] = r3(h_o - s1)
        out["OWNER_MINUS_SOFFIT_M2"] = r3((h_o - s1) * L) if L else "HELD"
    else:
        out["OWNER_MINUS_SOFFIT_M (b=0.10)"] = "HELD"
        out["OWNER_MINUS_SOFFIT_M2"] = "HELD"
    if h_o and bx1 is not None:
        gap = r3(bx1 - h_o)
        if gap < 0:
            flags.append(f"CHECK-BEAM: owner line {h_o:.2f} is {-gap:.2f} m ABOVE the soffit of crossing "
                         f"{'/'.join(m for m, d in cross if d == hx)} ({bx1:.2f}): a flat ceiling at {h_o:.2f} cuts the "
                         "beam; needs a bulkhead round it or a lower ceiling (designer / owner)")
        elif gap < OWNER_DECOR:
            flags.append(f"CHECK-BEAM: owner line {h_o:.2f} leaves {gap:.2f} m under crossing "
                         f"{'/'.join(m for m, d in cross if d == hx)} (soffit {bx1:.2f}), less than the 0.15 decor "
                         "depth: bulkhead or lower ceiling")
    if h_o and hd and hd > h_o:
        flags.append(f"CHECK-HEAD: printed opening head {hd:.2f} is {hd - h_o:.2f} m ABOVE the owner line {h_o:.2f}: "
                     "the ceiling cannot stop below the head on that wall")
    if hd and s1 and hd > s1:
        flags.append(f"CONFLICT-HEAD: printed head {hd:.2f} is above the slab soffit {s1:.2f} (b=0.10)")
    if hd and rid in HEAD_WALL_BEAM and f2f:
        m, d, cert = HEAD_WALL_BEAM[rid]
        sb = r3(f2f - d)
        if hd > sb:
            flags.append(f"CONFLICT-HEAD-BEAM ({cert}): printed head {hd:.2f} is {hd - sb:.2f} m above the soffit of {m} "
                         f"{d:.2f} on the same wall line ({sb:.2f} even with no floor build-up): architecture vs "
                         "structure, designer request")
    if special:
        flags.append("CEILING: " + special)
    out["FLAGS"] = " | ".join(flags) or "-"
    out["FREELANCER_M2 (same room, gross)"] = fl if fl is not None else "-"
    return out


def main():
    rows = [row(r) for r in R]
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "ROOMS_T112.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def tot(keys, col, cond=lambda r: True):
        s = 0.0
        for r in rows:
            if r["ROW"] in keys and isinstance(r[col], float) and cond(r):
                s += r[col]
        return round(s, 3)
    sets = (("5 matched dry rooms (2 annex)", ["GF-01", "GF-04", "1F-01", "1F-04", "2F-03"], 299.58),
            ("6 dry rooms (2 annex)", ["GF-01", "GF-04", "1F-01", "1F-04", "2F-03", "1F-10"], 375.40),
            ("4 dry rooms on verified datums", ["1F-01", "1F-04", "2F-03", "1F-10"], 59.50 + 58.82 + 64.26 + 75.82))
    print("rows", len(rows))
    for name, keys, fl in sets:
        o = tot(keys, "OWNER_GROSS_M2")
        up = tot(keys, "DWG_M2_UPPER (L x soffit b=0)")
        print(f"{name}: owner {o} ({o - fl:+.2f} m2, {100 * (o - fl) / fl:+.1f} %) | drawing upper bound {up or 'HELD'}"
              + (f" ({up - fl:+.2f}, {100 * (up - fl) / fl:+.1f} %)" if up else "") + f" | freelancer {fl:.2f}")
    wet = [r["ROW"] for r in rows if r["KIND"] == "WET"]
    annex = ["GF-02", "GF-03", "GF-05", "GF-06"]
    ow = tot(wet, "OWNER_GROSS_M2"); oa = tot(annex, "OWNER_GROSS_M2")
    print(f"wet-wall tiles owner method: {ow} (annex, datum held: {oa}; verified datums {round(ow - oa, 3)});"
          f" drawing upper bound on verified datums {tot(wet, 'DWG_M2_UPPER (L x soffit b=0)')}; freelancer 433.83 "
          "(one total)")
    for r in rows:
        if r["FLAGS"] != "-":
            print(r["ROW"], "|", r["FLAGS"])


if __name__ == "__main__":
    main()
