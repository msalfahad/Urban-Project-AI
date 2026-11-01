"""T-427 on the development villa: the dry floor-finish residual against the freelancer after T-418 (-40.7967 m2,
-12.09 %) split to physical causes, the GF garden band re-read under ZONE_EXTENT_V1 (R-T427-1), and the same split for
the wet floor. Research only; nothing is wired and no candidate or released quantity changes.

    python3 -I research/agents_t427/t427_alsenan.py           # print
    python3 -I research/agents_t427/t427_alsenan.py --write   # write summary.json + RESIDUAL_T427.csv
    python3 -I research/agents_t427/t427_alsenan.py --check   # committed files reproduce

Geometry: ROOM-LOCAL dimensions only (origin = the inner south-west corner of the printed pantry box, x east along the
south wall, y north), read on the architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip ->
P7757.dxf, sha256 ab54dd55) by entity handle, and on sheet 03 (p7757_arch_sheet03.pdf, read at 250 dpi); no client
coordinate, name or drawing content is committed. Engine faces: the released ARCH_TAKEOFF_V2.9 run on the same DXF
(own run, this task): GF-RC99C2A 126.9277, GF-R9A05AA 9.101, GF-RFD4E1D 4.885, GF-RC06FED 2.800 m2, strips
SITE-baa7db7fb0d465b6 (OP-003, 1.964) and SITE-0a31aaa10796d33a (1.100); candidate lines as the merged ledgers carry
them (T-240 OP-003 split, T-343 closure list, T-345 survey, T-414 room table).

Drawn lines used (handle, layer, local m):
  104 L1 south wall face y 0.00, x 3.00 .. 18.97;  B3 L5 pantry east edge x 3.00, y 0 .. 4.00;
  2FCF S-COL.BON column 3.275 .. 4.375 x -0.20 .. 0.05 (0.05 proud into the room);
  310 L5 band WEST END x 6.80, y 0 .. 1.50;  30F L5 band EAST END x 13.82, y 0 .. 1.45;
  4B4 L2 y 1.30, x 6.80 .. 9.62;  A9 L5 y 1.45, x 6.80 .. 10.62;  A8 L2 y 1.50, x 6.80 .. 13.82;
  A7 L5 y 1.50, x 9.566 .. 11.526;  337 L1 y 1.30, x 10.62 .. 13.87;  336 L1 y 1.50, x 10.62 .. 13.27;
  2FD2 S-COL.BON column 9.82 .. 10.62 x 1.30 .. 1.55;  2FC6 S-COL.BON column 13.27 .. 13.87 x 1.30 .. 1.55;
  4B1 L2 x 6.80, y 1.50 .. 5.45 (the light-well box over the round stair).
  Searched and NOT drawn: any line at y 1.30 / 1.45 / 1.50 between x 3.00 and 6.80 (layers 1, 2, 5, W, S-COL.BON, D;
  sheet 03 draws none either). The GARDEN label block sits at x 10.46 (band 6.80 .. 13.82 centre 10.31).
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import zone_extent_v1 as Z  # noqa: E402

SUMMARY = HERE / "summary.json"
TABLE = HERE / "RESIDUAL_T427.csv"
CANDIDATE = "ARCH_TAKEOFF_V3.0.36 (candidate of record, NOT RELEASED); floor lines unchanged since V3.0.34 (T-414 / T-418)"


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def band_pieces():
    """the GF south band as the V2.9 faces / strips cut it (local m)"""
    return [
        {"id": "ROOM-DINING (open room floor north of the band, V2.9 GF-RC99C2A)", "engine_class": "ROOM_FLOOR",
         "poly": R(3.0, 1.5, 6.8, 4.0), "status": "ASSUMED — OWNER-APPROVED (finish; open-room line L-7625f35c)"},
        {"id": "GF-RFD4E1D band west face", "engine_class": "ZONE", "zone": "GARDEN (D-48)",
         "poly": [(3.0, 1.3), (3.0, 0.0), (3.275, 0.0), (3.275, 0.05), (4.375, 0.05), (4.375, 0.0), (6.8, 0.0),
                  (6.8, 1.3)]},
        {"id": "OP-003 band strip, west 3.80 (x 3.00 .. 6.80)", "engine_class": "STRIP", "zone": "GARDEN (D-48)",
         "poly": R(3.0, 1.3, 6.8, 1.5)},
        {"id": "OP-003 band strip, curb 3.02 (x 6.80 .. 9.82)", "engine_class": "STRIP", "zone": "GARDEN (D-48)",
         "poly": R(6.8, 1.3, 9.82, 1.5)},
        {"id": "GF-R9A05AA garden band", "engine_class": "ZONE", "zone": "GARDEN (D-48)",
         "poly": [(13.27, 1.3), (6.8, 1.3), (6.8, 0.0), (10.12, 0.0), (10.12, 0.05), (10.62, 0.05), (10.62, 0.0),
                  (13.82, 0.0), (13.82, 1.3)]},
        {"id": "columns 2FD2 + 2FC6 and wall 336 / 337 between them", "engine_class": "SOLID",
         "poly": [(9.82, 1.3), (13.87, 1.3), (13.87, 1.55), (13.27, 1.55), (13.27, 1.5), (10.62, 1.5), (10.62, 1.55),
                  (9.82, 1.55)]},
    ]


DRAWN = [
    ((3.0, 0.0), (18.97, 0.0)),                       # 104 south wall face
    ((3.0, 0.0), (3.0, 4.0)),                         # B3 pantry east edge
    ((3.275, 0.05), (4.375, 0.05)), ((3.275, 0.0), (3.275, 0.05)), ((4.375, 0.0), (4.375, 0.05)),   # 2FCF column
    ((6.8, 0.0), (6.8, 1.5)),                         # 310 band west end
    ((13.82, 0.0), (13.82, 1.45)),                    # 30F band east end
    ((6.8, 1.3), (9.62, 1.3)),                        # 4B4
    ((6.8, 1.45), (10.62, 1.45)),                     # A9
    ((6.8, 1.5), (13.82, 1.5)),                       # A8
    ((10.62, 1.3), (13.87, 1.3)), ((10.62, 1.5), (13.27, 1.5)),                                    # 337 / 336
    ((9.82, 1.3), (10.62, 1.3)), ((9.82, 1.55), (10.62, 1.55)), ((9.82, 1.3), (9.82, 1.55)), ((10.62, 1.3), (10.62, 1.55)),
    ((13.27, 1.3), (13.87, 1.3)), ((13.27, 1.55), (13.87, 1.55)), ((13.27, 1.3), (13.27, 1.55)), ((13.87, 1.3), (13.87, 1.55)),
    ((10.12, 0.0), (10.12, 0.05)), ((10.12, 0.05), (10.62, 0.05)),   # south-wall column notch inside the band
    ((6.8, 1.5), (6.8, 5.45)),                        # 4B1 light-well box (round stair B7 to its east)
]

FREELANCER_DRY = 337.57          # FIN workbook, tiles sheet, dry floor total (quantities only)
FREELANCER_WET = 72.01
CANDIDATE_DRY_WITH_T418 = 296.7733
# GF open room: his two rows (reception + dining 137.50, entrance 10.46) against the drawn gross outline of the open room
FREELANCER_GF_OPEN = 147.96
# drawn gross outline of the open room (wall faces, layers 1 / W / S-COL.BON, own polygonization of P7757.dxf; doors
# closed on their wall faces): 151.6802 m2 = V2.9 GF-RC99C2A 126.928 + GF-R9A05AA 9.101 + GF-RFD4E1D 4.885 + GF-RC06FED
# 2.800 + pantry strips 1.700 (0.600 + 1.100) + band strip 1.364 + columns / wall 0.880 + the wash lobby part open to the
# room 3.8321 (wet, his own wet row) + its 1.256 x 0.15 mouth strip 0.1901 (ARCH.THRESHOLD L-1c71cd45 BLOCKED_RFI)
OUTLINE = {"gross": 151.6802, "wash_lobby_part": 3.8321, "lobby_mouth": 0.1901}


def dry_components(zone):
    rows = {r["id"]: r for r in zone["rows"]}
    west_face = rows["GF-RFD4E1D band west face"]["area_m2"]
    west_strip = rows["OP-003 band strip, west 3.80 (x 3.00 .. 6.80)"]["area_m2"]
    curb = rows["OP-003 band strip, curb 3.02 (x 6.80 .. 9.82)"]["area_m2"]
    band = rows["GF-R9A05AA garden band"]["area_m2"]
    solid = rows["columns 2FD2 + 2FC6 and wall 336 / 337 between them"]["area_m2"]
    # the open room's physical parts as the candidate lines carry them: dry 111.8484 (109.7784 + under-stair 2.07),
    # B7 treads 6.1244, wet pantry 13.4549, HELD band faces 13.986 + strip 1.364, wall / columns 0.88 (no line)
    comparable = round(111.8484 + 6.1244 + 13.4549 + west_face + band + west_strip + curb + solid, 4)
    # independent check: the drawn gross outline less what is not in his two dry rows
    outline_comparable = round(OUTLINE["gross"] - OUTLINE["wash_lobby_part"] - OUTLINE["lobby_mouth"], 4)
    if abs(outline_comparable - comparable) > 0.001:
        raise SystemExit(f"outline {outline_comparable} does not re-add to the candidate parts {comparable}")
    gross_gap = round(FREELANCER_GF_OPEN - comparable, 4)
    C = [
        # (component, m2 engine - freelancer, class, verdict proposal, evidence)
        ("GF pantry floored WET", -13.4549, "TRACED", "RULE_DIFFERENCE",
         "UP-WET-001 (pantry on the wet list) + owner Q-37 A (printed 4.50 x 3.00 box wet) + URBAN-WET-FLOOR-TILED@v1; "
         "he keeps the pantry inside his dry reception + dining row; the wet side carries +13.4549 (2.800 + 8.9549 + "
         "0.600 + 1.100, T-240 / T-286)"),
        ("GF round-stair treads below the cut (B7)", -6.1244, "TRACED", "RULE_DIFFERENCE",
         "UP-CER-001 (a stair footprint is deducted from the floor tile) + UP-STAIR-005 (treads are stair marble, B7): "
         "8.194412 drawn treads - 2.07 under-stair floor kept in the floor line (L-224e2fa4)"),
        ("GF garden band proper, x 6.80 .. 13.82 (planter or floor)", -round(band, 4), "HELD", "UNRESOLVED (designer D-48)",
         "own outline: layer-5 ends 310 / 30F, edge lines 4B4 / A9 / A8, wall 337 / 336 between columns; GARDEN label "
         "inside; finish class open (planter soil or floor)"),
        ("GF band curb strip x 6.80 .. 9.82 (0.20, three drawn edge lines)", -round(curb, 4), "HELD",
         "UNRESOLVED (with D-48)", "candidate line L-554a525e ARCH.SPACE HELD carries 1.364 = this 0.604 + the 0.760 below"),
        ("GF band west part x 3.00 .. 6.80: DINING FLOOR (R-T427-1)", -round(west_face + west_strip, 4), "TRACED",
         "ENGINE_WRONG / FREELANCER_RIGHT (corrected: -> 0)",
         f"no drawn line between it and the dining floor (searched, DXF + sheet 03); the band ends at 310; the engine "
         f"prolonged the band edge 3.80 m west (T-240 OP-003). GF-RFD4E1D {west_face} (L-6b6412e8) + strip {west_strip} "
         f"(part of L-554a525e) move from HELD to dry floor; his row floors them too, so the correction closes this part"),
        ("GF wall + two columns inside his gross outline (2FD2, 2FC6, 336 / 337)", -round(solid, 4), "TRACED",
         "ENGINE_RIGHT (net floor) / FREELANCER gross",
         "his rows have no dimensions; his figure re-adds to the drawn GROSS outline (T-147: 147.90; this run 147.6577), "
         "which holds 0.88 m2 of wall and columns no floor tile covers"),
        ("GF open room: his rows above the drawn gross outline", -gross_gap, "UNEXPLAINED", "UNRESOLVED",
         f"{FREELANCER_GF_OPEN} - {comparable} (candidate parts of the open room; the drawn outline {OUTLINE['gross']} - wash "
         f"lobby part {OUTLINE['wash_lobby_part']} (his wet row) - lobby mouth {OUTLINE['lobby_mouth']} (held threshold) = "
         f"{outline_comparable}) = {gross_gap} m2 (+0.20 %); if his row "
         f"also holds the lobby mouth, {round(gross_gap - OUTLINE['lobby_mouth'], 4)}; no breakdown, no match by figure"),
        ("GF stair-room floor parts (T-418; area DC, finish HELD)", 6.1275, "TRACED",
         "UNRESOLVED (no floor row of his: his reception + dining + entrance re-add to the open-room outline, so the "
         "stair-room hall is in none of his floor rows; his main-stair landing row 6.20 has no breakdown)",
         "T-418 MERGED 361f6e47"),
        ("GF master / dewaneya / driver", -0.0051, "TRACED", "T-086 verdicts", "T-086"),
        ("GF doorway strips valued in the candidate (OP-010 0.20, OP-012 0.15)", 0.35, "TRACED", "engine-only strips",
         "T-240 WP2 (Checker 01:12)"),
        ("1F living: arrival landing marble (Q-66 B) + T-345 trace", -5.249, "TRACED", "RULE_DIFFERENCE", "T-345 / T-122"),
        ("1F bed rooms (380 x 430 passage, curved east room)", -1.3785, "TRACED", "T-086 verdicts", "T-086 / T-153"),
        ("1F doorway strips valued in the candidate", 0.72, "TRACED", "engine-only strips", "T-240"),
        ("2F maid room", -0.23, "TRACED", "T-086 verdict", "T-086"),
        ("2F arrival 4.875 marble (Q-70 A, B7)", -4.875, "TRACED", "RULE_DIFFERENCE", "T-129 / T-418"),
        ("2F corridor residual against his 7.70 (his row has no dimensions)",
         -0.325, "UNEXPLAINED", "UNRESOLVED", "T-418"),
        ("2F doorway strip valued in the candidate", 0.18, "TRACED", "engine-only strip", "T-240"),
    ]
    return C, comparable, gross_gap, outline_comparable


def wet_components():
    # T-074 hand table (MERGED, VERIFIED) row by row against his wet rows; quantities only
    return [
        ("GF pantry (Q-37 A)", 13.4549, "TRACED", "RULE_DIFFERENCE", "mirror of the dry pantry component"),
        ("GF wash by the dewaneya 3.1325 vs 3.15", -0.0175, "TRACED", "RULE_DIFFERENCE (T-074: column corner)", "T-074"),
        ("GF W.C. by the dewaneya 3.375 vs 3.37", 0.005, "TRACED", "AGREE (rounding)", "T-074"),
        ("GF driver W.C. 1.95 vs 1.95", 0.0, "TRACED", "AGREE", "T-074"),
        ("GF kitchen 9.63 vs 9.55", 0.08, "TRACED", "ENGINE_RIGHT (two piers, entrance 1.05 x 1.50)", "T-074"),
        ("GF W.C. 175 x 135 2.3625 vs 2.36", 0.0025, "TRACED", "AGREE", "T-074"),
        ("GF basin space 110 x 135 1.485 vs 1.70", -0.215, "TRACED", "RULE_DIFFERENCE (his 0.20 reveal, UP-THR-001)", "T-074"),
        ("GF W.C. wedge A 2.6752 vs 2.67", 0.0052, "TRACED", "AGREE", "T-074"),
        ("GF W.C. wedge B 2.3676 vs 2.30", 0.0676, "TRACED", "ENGINE_RIGHT (shoelace on wall faces)", "T-074"),
        ("GF wash lobby 4.7307 vs 4.73 (T-074 hand 4.7321)", 0.0007, "TRACED", "AGREE", "T-074 / V2.9 face"),
        ("GF master bath 3.7177 vs 3.70 (T-074 hand 3.7173)", 0.0177, "TRACED", "AGREE", "T-074"),
        ("1F west bath upper 5.0225 vs 5.00", 0.0225, "TRACED", "ENGINE_RIGHT", "T-074"),
        ("1F west bath lower 5.0225 vs 5.00", 0.0225, "TRACED", "ENGINE_RIGHT", "T-074"),
        ("1F laundry 10.151 vs 10.00", 0.151, "TRACED", "ENGINE_RIGHT (W.C. corner cut, printed parts)", "T-074"),
        ("1F W.C. by the laundry 2.646 vs 2.59", 0.056, "TRACED", "ENGINE_RIGHT (his 1.44 for printed 1.47)", "T-074"),
        ("1F bath by the laundry 3.5775 vs 3.60", -0.0225, "TRACED", "AGREE (jamb)", "T-074"),
        ("1F east bath 4.725 vs 4.72", 0.005, "TRACED", "AGREE", "T-074"),
        ("2F W.C. 5.55 vs 5.62", -0.07, "TRACED", "ENGINE_RIGHT (printed 300 x 185)", "T-074"),
    ]


# what the same reclassification means for other lines (findings for their owners; nothing changed here)
CROSS_TRADE = [
    {"line": "L-71e2e002a3af624097f0 FIN.SKIRTING GF-RC99C2A (open room)", "unit": "lm", "before": 24.6716,
     "after": round(24.6716 + 2.7 + 1.2, 4), "delta": 3.9, "status": "DRAWING-CONFIRMED geometry (V2.9 runs of "
     "GF-RFD4E1D: wall 2.70 = 3.80 - 1.10 column + column 2FCF faces 1.20 = 0.05 + 1.10 + 0.05)",
     "why": "the dining's south wall face x 3.00 .. 6.80 lies on the cut-off band face, which carries no finish line; the "
            "open room's run along the prolonged edge (y 1.50) is already deducted as OP-003 (T-296 PASSAGE_RUN_RESIDUAL)"},
    {"line": "ceiling ledger GF-RFD4E1D (T-283 r3 / T-295)", "unit": "m2", "before": "4.885 HELD_CLASS (P-2) + 6.5428 m "
     "bulkhead edges HELD", "after": "the dining ceiling's class (decidable; type as the open room)", "delta": None,
     "status": "for the ceiling owner", "why": "R-T427-1: the piece is dining, not band"},
    {"line": "designer list D-48", "unit": "m2", "before": 13.986, "after": round(9.101 + 0.604, 4), "delta": None,
     "status": "HELD (planter or floor)", "why": "band proper 9.101 + curb 0.604; the west 5.645 is floor"},
]

CANDIDATE_WET = 85.5756          # T-414 room table, 21 wet lines (V3.0.34 = V3.0.35 = V3.0.36 on floor lines)


def summarize():
    zone = Z.classify(band_pieces(), DRAWN)
    C, comparable, gross_gap, outline_comparable = dry_components(zone)
    diff = round(CANDIDATE_DRY_WITH_T418 - FREELANCER_DRY, 4)
    tot = round(sum(c[1] for c in C), 4)
    if abs(tot - diff) > 1e-4:
        raise SystemExit(f"dry components {tot} do not close on {diff}")
    moved = round(zone["moved_to_floor_m2"], 4)
    corrected = round(CANDIDATE_DRY_WITH_T418 + moved, 4)
    W = wet_components()
    wdiff = round(CANDIDATE_WET - FREELANCER_WET, 4)
    wtot = round(sum(c[1] for c in W), 4)
    wet_rounding = round(wdiff - wtot, 4)      # the per-room figures above are T-074 hand values; the lines differ by this
    by = lambda comps, k: round(sum(c[1] for c in comps if c[2] == k), 4)  # noqa: E731
    return {
        "method": Z.METHOD, "rule": Z.RULE, "candidate": CANDIDATE,
        "zone_extent": zone,
        "dry": {"freelancer_m2": FREELANCER_DRY, "candidate_with_t418_m2": CANDIDATE_DRY_WITH_T418, "diff_m2": diff,
                "diff_pct": round(100 * diff / FREELANCER_DRY, 2), "components_sum_m2": tot,
                "by_class": {k: by(C, k) for k in ("TRACED", "HELD", "UNEXPLAINED")},
                "gf_open_room": {"freelancer_rows_m2": FREELANCER_GF_OPEN, "drawn_outline_m2": OUTLINE["gross"],
                                 "comparable_m2": comparable, "freelancer_above_outline_m2": gross_gap,
                                 "outline_check_m2": outline_comparable},
                "correction": {"moved_to_dry_floor_m2": moved, "corrected_candidate_dry_m2": corrected,
                               "corrected_diff_m2": round(corrected - FREELANCER_DRY, 4),
                               "corrected_diff_pct": round(100 * (corrected - FREELANCER_DRY) / FREELANCER_DRY, 2),
                               "held_band_before_m2": 15.35, "held_band_after_m2": round(zone["held_m2"], 4)},
                "components": [{"component": c[0], "m2": c[1], "class": c[2], "verdict": c[3], "evidence": c[4]}
                               for c in C]},
        "cross_trade": CROSS_TRADE,
        "wet": {"freelancer_m2": FREELANCER_WET, "candidate_m2": CANDIDATE_WET, "diff_m2": wdiff,
                "diff_pct": round(100 * wdiff / FREELANCER_WET, 2), "components_sum_m2": wtot,
                "line_vs_hand_rounding_m2": wet_rounding,
                "components": [{"component": c[0], "m2": c[1], "class": c[2], "verdict": c[3], "evidence": c[4]}
                               for c in W]},
    }


def table_csv(s):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["family", "component", "m2_engine_minus_freelancer", "class", "verdict", "evidence"])
    for fam in ("dry", "wet"):
        for c in s[fam]["components"]:
            w.writerow([fam, c["component"], f"{c['m2']:.4f}", c["class"], c["verdict"], c["evidence"]])
    return out.getvalue()


def main(argv):
    s = summarize()
    if "--check" in argv:
        assert json.loads(SUMMARY.read_text(encoding="utf-8")) == json.loads(json.dumps(s)), "summary.json stale"
        assert TABLE.read_text(encoding="utf-8") == table_csv(s), "RESIDUAL_T427.csv stale"
        print("check OK")
        return 0
    print(json.dumps(s, indent=1, ensure_ascii=False))
    if "--write" in argv:
        SUMMARY.write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        TABLE.write_text(table_csv(s), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
