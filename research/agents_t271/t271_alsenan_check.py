"""T-271 Alsenan run: ceilings r2 ledger from ALSENAN_T271_INPUT.json (made by t271_extract.py from the private
drawings; areas / lengths / ids only). Standard library only; writes the committed CSVs and summary.json.

Usage: python3 -I research/agents_t271/t271_alsenan_check.py [--out <dir>]   (default: this folder)"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ceilings_r2 as CR  # noqa: E402

# ---------------------------------------------------------------------------------------- class of every floor piece
# (class, evidence status of the class, basis, closed room perimeter?)
OA = CR.ST_OA
DC = CR.ST_DC
CLASS = {
    "GF-RC99C2A/open": ("DRY", DC, "open room (dining / reception / living / hall), V2.9 face east of B3 / AD", False),
    "GF-RC99C2A/pantry": ("WET", OA, "pantry part west of B3 / AD: wet by owner Q-37 A (Checker 01:12, T-269 8.955)",
                          False),
    "GF-RC06FED": ("WET", OA, "pantry part (Checker 01:12: released porcelain RC06FED is pantry; Q-37 A)", False),
    "GF-R7512EA": ("DRY", DC, "Majlis / diwaniya", True),
    "GF-R75FBAE": ("DRY", DC, "master bedroom", True),
    "GF-R51E127": ("DRY", DC, "driver room", True),
    "GF-RA3AD49": ("WET", OA, "kitchen: wet like a bathroom by owner Q-30 A", True),
    "GF-RD6F891": ("WET", DC, "bath", True),
    "GF-RB62B55": ("WET", DC, "bath", True),
    "GF-RF38DAF": ("WET", DC, "W.C.", True),
    "GF-RB28769": ("WET", DC, "W.C.", True),
    "GF-RDF7D28": ("WET", DC, "W.C.", True),
    "GF-RFAD3C4": ("WET", DC, "bath", True),
    "GF-RDBD4F9": ("WET", OA, "basin-only hand wash, WET by owner Q-06 A (T-208)", False),
    "GF-R8496F0": ("WET", OA, "basin-only hand wash, WET by owner Q-06 A (T-208)", True),
    "GF-RD36087": ("WET", OA, "basin-only hand wash, WET by owner Q-06 A (T-208)", True),
    "GF-R9A05AA": ("HELD_CLASS", CR.ST_H, "garden / yard band 1.30 m under the 1F slab: HELD (P-2, Checker 01:12); "
                   "interior ceiling or soffit over outside air (Q-68 C) not established", False),
    "GF-RFD4E1D": ("HELD_CLASS", CR.ST_H, "merged band cell of the same 1.30 m band: HELD (P-2, Checker 01:12)", False),
    "GF-RF002DC": ("HELD_CLASS", CR.ST_H, "unlabelled space 1.20 x 3.00 (no room word, passages OP-003 / OP-007): "
                   "not identified", False),
    "GF-R7B7A5D": ("HELD_CLASS", CR.ST_H, "unlabelled space 1.20 x 1.30 (door OP-025, passages OP-001 / OP-003): "
                   "not identified", False),
    "GF-R31F8AE": ("STAIR", DC, "main stair, GF part", True),
    "GF-R89E756": ("SHAFT", DC, "lift shaft", True),
    "1F-R78C367": ("DRY", DC, "living / corridor / landing / connector and the footprint of the GF light well (the 1F "
                   "roof slab is closed over it: the double-height ceiling is on this plan)", False),
    "1F-RB72F22": ("DRY", DC, "master bedroom west", True),
    "1F-R3CFCFD": ("DRY", DC, "master bedroom east (curved)", True),
    "1F-RED0D19": ("DRY", DC, "master bedroom 500 x 365", True),
    "1F-R0E919A": ("DRY", DC, "master bedroom 380 x 430", True),
    "1F-RFFE7AF": ("DRY", DC, "dressing between the 380 x 430 bedroom and its bath (T-223 rule, Checker 22:05)", True),
    "1F-R26FA0D": ("WET", DC, "laundry + vestibule", True),
    "1F-R8BDA49": ("WET", DC, "bath", True),
    "1F-R48AA46": ("WET", DC, "bath", True),
    "1F-R48CDA5": ("WET", DC, "bath", True),
    "1F-RED23B8": ("WET", DC, "bath", True),
    "1F-R52AC05": ("WET", DC, "W.C.", True),
    "1F-RCCB686": ("SHAFT", DC, "lift shaft", True),
    "2F-R1DB2D2": ("DRY", DC, "maid room", True),
    "2F-RE83BED": ("WET", DC, "W.C.", True),
    "2F-R4D1B62": ("DRY", DC, "2F stair hall: lobby + the top of the stair box; the 2F roof slab is closed over the "
                   "whole face (no stair zone above); the stair box part is listed apart below", False),
    "2F-R2BDCEE": ("SHAFT", DC, "lift shaft (roofed by the 2F roof slab)", True),
}
# 2F stair hall split (hand box of the stair shaft walls, T-147 ceil_ledger 'sh2', merged d54cfac): 12.9742 m2
STAIR_BOX_2F = ("2F-R4D1B62", 12.9742, "T-147 (MERGED d54cfac) stair-box part of the 2F stair hall")

# floor piece status (Checker floor batches, BOARD.md T-180 SLOT notes) and the floor value it carries
FLOOR_PIECE = {
    "GF-R7512EA": "VERIFIED (Verifier 2026-10-24 01:01)", "GF-R75FBAE": "VERIFIED (Verifier 2026-10-24 01:01)",
    "GF-RF38DAF": "VERIFIED (Verifier 2026-10-24 01:01)", "GF-RB28769": "VERIFIED (Verifier 2026-10-24 01:01)",
    "GF-R51E127": "VERIFIED (Verifier 2026-10-23 23:28)", "GF-RA3AD49": "VERIFIED (Verifier 2026-10-23 23:28)",
    "GF-RB62B55": "VERIFIED (Verifier 2026-10-23 23:28)", "GF-RD6F891": "VERIFIED (Verifier 2026-10-23 23:28)",
    "GF-RDF7D28": "VERIFIED (Verifier 2026-10-23 23:28)", "GF-RFAD3C4": "VERIFIED (Verifier 2026-10-23 23:28)",
    "GF-R8496F0": "VERIFIED (Verifier 2026-10-23 23:28)", "GF-RDBD4F9": "geometry own-checked (Verifier 2026-10-23 20:14)",
    "GF-RD36087": "geometry own-checked (Verifier 2026-10-23 09:07)",
    "GF-RC99C2A/open": "RE-MEASURED, NOT VERIFIED (class / tread rule; Verifier 2026-10-24 01:12)",
    "GF-RC99C2A/pantry": "RE-MEASURED, NOT VERIFIED (class; Verifier 2026-10-24 01:12; T-269 8.955)",
    "GF-RC06FED": "RE-MEASURED, NOT VERIFIED (class; Verifier 2026-10-24 01:12)",
    "GF-R9A05AA": "HELD (P-2; Verifier 2026-10-24 01:12)", "GF-RFD4E1D": "HELD (P-2; Verifier 2026-10-24 01:12)",
    "1F-R78C367": "floor piece 38.6335 own-VERIFIED (T-269, Verifier 13:03) inside this 75.983 face",
    "1F-RB72F22": "VERIFIED (Verifier 2026-10-23 22:05)", "1F-RED0D19": "VERIFIED (Verifier 2026-10-23 22:05)",
    "1F-R0E919A": "VERIFIED (Verifier 2026-10-23 22:05)", "1F-R26FA0D": "VERIFIED (Verifier 2026-10-23 22:05)",
    "1F-RED23B8": "VERIFIED (Verifier 2026-10-23 22:05)", "1F-R52AC05": "VERIFIED (Verifier 2026-10-23 22:05)",
    "1F-R3CFCFD": "re-measured (Verifier 2026-10-23 23:13; curved edge, T-223)",
    "1F-RFFE7AF": "own-measured 2.970 (Verifier 2026-10-23 22:05 FINDING 1; T-223)",
    "1F-R8BDA49": "VERIFIED (T-180 batch, 1F baths)", "1F-R48AA46": "VERIFIED (T-180 batch, 1F baths)",
    "1F-R48CDA5": "VERIFIED (T-180 batch, 1F baths)", "2F-R1DB2D2": "VERIFIED (T-180 batch, 2F)",
    "2F-RE83BED": "VERIFIED (T-180 batch, 2F)",
}

# freelancer FIN workbook, sheet 'decor' (column D, totals H31 / H65 / G31 / G65; comparison only, Q-57)
FL = {"GF": {"DRY": 197.33, "WET": 35.48}, "1F": {"DRY": 112.96, "WET": 30.91}, "2F": {"DRY": 27.28, "WET": 5.62}}
FL_CELLS = {"GF DRY": "D13:D17", "GF WET": "D42:D51", "1F DRY": "D21:D25", "1F WET": "D55:D60", "2F DRY": "D28:D29",
            "2F WET": "D63"}
FL_CORNICE = 282.85 + 144.61
FL_PAINT = 452.33
FL_ROOM = {  # freelancer row -> pieces (only where the row names the same room)
    "D16 diwaniya 24.84": (["GF-R7512EA"], 24.84), "D14 master bed room 16.66": (["GF-R75FBAE"], 16.66),
    "D17 driver 7.87": (["GF-R51E127"], 7.87), "D48 kitchen 9.55": (["GF-RA3AD49"], 9.55),
    "D13 + D15 reception + dining + entrance 147.96": (["GF-RC99C2A/open", "GF-RC99C2A/pantry", "GF-RC06FED"], 147.96),
    "D60 laundry 10.00": (["1F-R26FA0D"], 10.00), "D21 living 38.96": (["1F-R78C367"], 38.96),
    "D22:D25 bed rooms 1-4 74.00": (["1F-RB72F22", "1F-R3CFCFD", "1F-RED0D19", "1F-R0E919A"], 74.00),
    "D28 maid room 19.58": (["2F-R1DB2D2"], 19.58), "D63 roof-floor W.C. 5.62": (["2F-RE83BED"], 5.62),
}


def run(inp, out):
    D = json.load(open(inp))
    faces = {f["face"]: f for f in D["faces"]}
    missing = sorted(set(faces) - set(CLASS)) + sorted(set(CLASS) - set(faces))
    if missing:
        raise SystemExit(f"class table and input disagree: {missing}")
    rows, tots, recon = [], {}, []
    for fid in sorted(faces, key=lambda k: ({"GF": 0, "1F": 1, "2F": 2}[faces[k]["floor"]], k)):
        f = dict(faces[fid])
        cls, cst, basis, closed = CLASS[fid]
        # the floor piece's own area: the engine value of a whole face (exact arcs); a split part keeps its geometry
        geo = f["area_m2"]
        if "/" not in fid:
            f["area_m2"] = f["engine_face_area_m2"]
        hp = [("over the stair box (ceiling over the stair well; its finish / height not printed, Q-72 investigation)",
               STAIR_BOX_2F[1], STAIR_BOX_2F[2])] if fid == STAIR_BOX_2F[0] else ()
        r, t = CR.ledger(f, cls, cst, f"{basis}; class {cst}", closed=closed, held_parts=hp)
        for x in r:
            x["FLOOR_PIECE_STATUS"] = FLOOR_PIECE.get(fid, "")
        rows += r
        fl = f["floor"]
        for k, v in t.items():
            tots.setdefault(fl, {}).setdefault(k, 0.0)
            tots[fl][k] += v
        horiz = sum(x["QTY"] for x in r if x["SURFACE"].startswith("horizontal decor"))
        ef = f.get("engine_fin_ceiling")
        eng_m2 = None if ef is None else round(ef["m2"], 4)
        mine = horiz if cls in ("DRY", "WET") else 0.0
        recon.append({"FACE": fid, "FLOOR": fl, "CLASS": cls, "PIECE_M2": round(f["area_m2"], 4),
                      "GEOM_M2": round(geo, 4), "CHORD_RESIDUAL_M2": round(geo - f["area_m2"], 4),
                      "NO_CEILING_M2": round(t.get("deduct_no_ceiling", 0.0), 4),
                      "STAIR_SOFFIT_M2": round(t.get("deduct_stair", 0.0), 4),
                      "DOME_HELD_M2": round(t.get("held_dome", 0.0), 4),
                      "HORIZONTAL_M2": round(horiz, 4) if cls in ("DRY", "WET") else "",
                      "APART_OR_HELD_M2": round(f["area_m2"], 4) if cls not in ("DRY", "WET") else "",
                      "ENGINE_FIN_CEILING_M2": "" if eng_m2 is None else eng_m2,
                      "ENGINE_LINES": "" if ef is None else f"{ef['lines']} ({ef['blocked']} BLOCKED_RFI)",
                      "R2_MINUS_ENGINE_M2": "" if eng_m2 is None else round(mine - eng_m2, 4),
                      "FLOOR_PIECE_STATUS": FLOOR_PIECE.get(fid, "")})
    # the engine carries ONE line for the whole GF open face: compare it with open + pantry parts together
    po = {x["FACE"]: x for x in recon}
    o, pp = po["GF-RC99C2A/open"], po["GF-RC99C2A/pantry"]
    o["R2_MINUS_ENGINE_M2"] = round(o["HORIZONTAL_M2"] + pp["HORIZONTAL_M2"] - o["ENGINE_FIN_CEILING_M2"], 4)
    o["ENGINE_LINES"] += " (whole face GF-RC99C2A: compared with open + pantry)"
    fr = []
    for fl in ("GF", "1F", "2F"):
        s = tots.get(fl, {})
        for k in ("DRY", "WET"):
            h = s.get("horiz_" + k, 0.0)
            fr.append({"FLOOR": fl, "CLASS": k, "PIECES_M2": round(s.get("piece_" + k, 0.0), 4),
                       "HORIZONTAL_M2": round(h, 4), "PAINT_OWNER_M2": round(s.get("paint_own_" + k, 0.0), 4),
                       "FREELANCER_M2": FL[fl][k], "FREELANCER_CELLS": FL_CELLS[f"{fl} {k}"],
                       "DIFF_M2": round(h - FL[fl][k], 4), "DIFF_PCT": round(100 * (h - FL[fl][k]) / FL[fl][k], 2),
                       "COVE_RUN_M": round(s.get("cove_lm_" + k, 0.0), 3)})
    T = {k: round(sum(tots[fl].get(k, 0.0) for fl in tots), 4) for k in
         {k for fl in tots for k in tots[fl]}}
    horiz = round(T.get("horiz_DRY", 0) + T.get("horiz_WET", 0), 4)
    fl_tot = sum(FL[fl][k] for fl in FL for k in FL[fl])
    cmp_rows = []
    for lab, (ids, v) in FL_ROOM.items():
        h = sum(x["QTY"] for x in rows if x["FACE"] in ids and x["SURFACE"].startswith("horizontal decor"))
        cmp_rows.append({"FREELANCER_ROW": lab, "PIECES": " ".join(ids), "FREELANCER_M2": v, "HORIZONTAL_M2": round(h, 4),
                         "DIFF_M2": round(h - v, 4), "DIFF_PCT": round(100 * (h - v) / v, 2)})
    srows = []
    for x in D.get("strips", ()):
        door = x["kind"] == "DOOR"
        srows.append({"STRIP": x["strip"], "FLOOR": x["floor"], "OPENING": x["opening"], "KIND": x["kind"],
                      "FLOOR_ITEM": x["item"], "M2": x["m2"], "SIDES": x["sides"],
                      "CEILING": ("none: under a door head (the head soffit is the opening reveal, plaster / paint "
                                  "jamb-and-head line)") if door else
                      "UNKNOWN: passage strip - wall-opening head or open-zone ceiling not decided by this ledger",
                      "STATUS": CR.ST_DC if door else CR.ST_U})
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "STRIPS_T271.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(srows[0].keys()))
        w.writeheader()
        w.writerows(srows)
    with open(out / "CEILINGS_T271.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for name, data in (("RECONCILE_T271.csv", recon), ("FLOORS_T271.csv", fr), ("VS_FREELANCER_T271.csv", cmp_rows)):
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
    summ = {"pieces": len(faces), "rows": len(rows), "totals_by_floor": {fl: {k: round(v, 4) for k, v in sorted(s.items())}
                                                                        for fl, s in tots.items()},
            "totals": dict(sorted(T.items())), "horizontal_m2": horiz, "freelancer_decor_m2": round(fl_tot, 2),
            "horizontal_vs_freelancer_m2": round(horiz - fl_tot, 4),
            "horizontal_vs_freelancer_pct": round(100 * (horiz - fl_tot) / fl_tot, 2),
            "paint_owner_m2": round(T.get("paint_own_DRY", 0) + T.get("paint_own_WET", 0), 4),
            "freelancer_paint_m2": FL_PAINT,
            "strips_door_m2": round(sum(x["M2"] for x in srows if x["KIND"] == "DOOR"), 4),
            "strips_passage_unknown_m2": round(sum(x["M2"] for x in srows if x["KIND"] != "DOOR"), 4),
            "strips_passage_unknown_by_floor_m2": {fl: round(sum(x["M2"] for x in srows if x["KIND"] != "DOOR"
                                                                and x["FLOOR"] == fl), 4) for fl in ("GF", "1F", "2F")},
            "engine_fin_ceiling_m2": round(sum(x["ENGINE_FIN_CEILING_M2"] or 0.0 for x in recon), 4),
            "engine_by_floor_m2": {fl: round(sum(x["ENGINE_FIN_CEILING_M2"] or 0.0 for x in recon if x["FLOOR"] == fl), 4)
                                   for fl in ("GF", "1F", "2F")},
            "horizontal_by_floor_m2": {fl: round(tots[fl].get("horiz_DRY", 0) + tots[fl].get("horiz_WET", 0), 4)
                                       for fl in ("GF", "1F", "2F")}, "freelancer_cornice_m": round(FL_CORNICE, 2)}
    json.dump(summ, open(out / "summary.json", "w"), indent=1, sort_keys=True)
    return summ, fr, cmp_rows, recon


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE / "ALSENAN_T271_INPUT.json"))
    ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args(argv)
    s, fr, cmp_rows, recon = run(a.input, Path(a.out))
    print(json.dumps(s, indent=1))
    for x in fr:
        print(x)
    for x in cmp_rows:
        print(x)


if __name__ == "__main__":
    main()
