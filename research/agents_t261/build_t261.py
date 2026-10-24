"""T-261 builder: blocker-by-blocker resolution of blockwork register v2 (T-228 r2, MERGED bf4dd2a9).

Reads research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv and BLOCKERS_V2.csv (read only), applies rule R-T261-1
(piece_split.py) to the walls whose opening-to-piece assignment this run established from the drawings, and writes:
  T261_BLOCKERS.csv  one row per v2 blocker: SPLIT (part established, rest HELD) or STILL-HELD, the exact missing item,
                     what was searched this run, gross / deductions / net deltas apart, black / white, next owner
  T261_SPLIT.csv     the pieces and openings of every split wall (lengths, heights, jamb offsets, handles)
  T261_COVERAGE.csv  established net v2 -> proposed, by floor x thickness x type (nothing applied to the register)
  summary.json
Usage: python3 -I research/agents_t261/build_t261.py [--check]
Drawings are cited by Drive title and entity handle only; no coordinate, image or client name is written.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import piece_split as P  # noqa: E402

V2 = ROOT / "research" / "agents_t228" / "BLOCKWORK_WALL_REGISTER_V2.csv"
BLK = ROOT / "research" / "agents_t228" / "BLOCKERS_V2.csv"
ARCH = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55)"
ST = "Drive 'Alsenan chalet project' / ST7757 dxf.dxf (sha 9f9d1179)"
SS = "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"

# Pieces between drawn faces. GF-W10 / 1F-W10 / 2F-W02 sit on one plan line (SL-1, the ST-01 shaft beside the lift):
# the arch plan draws the same column outlines on every storey frame (S-COL.BON GF 2F7E / 2F81 / 2F84 / 2FC9,
# 1F 2FE1 / 2FE4 / 2FE7 / 300B, 2F 2F63 / 2F66 / 2F69); faces give 2.500 | 3.470 | 3.350 | 3.550 m (= 12.870).
SL1_EVID = (f"{ARCH}: column outlines S-COL.BON GF 2F7E / 2F81 / 2F84 / 2FC9, 1F 2FE1 / 2FE4 / 2FE7 / 300B, "
            "2F 2F63 / 2F66 / 2F69 (same plan position on each storey frame)")

WALLS = {
    "GF-W10": dict(
        census=12.870,
        pieces=[
            P.Piece("SF B3 (With Stair) stair-foot", 2.500, 4.10, "member", base_is_storey_basis=False,
                    top_is_stair_member=True,
                    held_item="base +0.30 stair-foot landing (plan LEVEL 4AB / 4AC; section A-A sheet10), top = the "
                              "stair landing member / cranked 'B3 (With Stair)' (6B6), size and soffit not printed "
                              "(T-228 F1, R-T228-3)",
                    held_figure_m2="2.500 x 4.10 = 10.250 - D-GF-09 1.980 = 8.270 on the +1.00 / B3 basis"),
            P.Piece("E1 CB2 span 1", 3.470, 4.00, "checker"),
            P.Piece("E2 CB2 span 2", 3.350, 4.00, "checker"),
            P.Piece("E3 B24", 3.550, 3.75, "checker"),
        ],
        openings=[
            P.Opening("D-GF-09", "SF B3 (With Stair) stair-foot", 1.453, 2.353, 1.980),
            P.Opening("W05", "E1 CB2 span 1", 0.375, 0.975, 0.480),
            P.Opening("W06", "E1 CB2 span 1", 2.870, 3.470, 0.480),
            P.Opening("W07", "E2 CB2 span 2", 0.400, 1.000, 0.480),
        ],
        extra_held="W.C. stretch 1.350 m below the +1.00 basis: 0 .. 0.945 (W.C. floor level drawn on no sheet)",
        handles=("D-GF-09 outer-face gap 0.900 between 2B8 and 2B9 (lintel line 3FD); W05 jambs 3E2 / 3E1, W06 3EF / "
                 "3EE, W07 3FC / 3FB; stair-foot piece between 2F7E and stub 213 / 21A"),
        class_="SS (Checker 09:59 / 11:59 own arithmetic 13.880 + 13.400 + 13.3125 - 1.440; not a VERIFIED ruling)"),
    "1F-W10": dict(
        census=12.870,
        pieces=[
            P.Piece("SF B3 (With Stair)", 2.500, 3.80, "member", top_is_stair_member=True,
                    held_item="no floor at +5.50 on the shaft line (A-A sheet10); top = 'B3 (With Stair)' 6B8 with no "
                              "floor-level member printed; base / top = the +3.50 and about +7.6 landing members "
                              "(R-T228-3, F3)",
                    held_figure_m2="2.500 x 3.80 = 9.500 - W25 1.500 = 8.000 on the +5.50 basis"),
            P.Piece("E1 CB9 span 1", 3.470, 3.70, "member"),
            P.Piece("E2 CB9 span 2", 3.350, 3.70, "member"),
            P.Piece("E3 CB9 span 3", 3.550, 3.70, "member"),
        ],
        openings=[
            P.Opening("W25", "SF B3 (With Stair)", 1.400, 2.400, 1.500),
            P.Opening("W21", "E1 CB9 span 1", 0.375, 0.975, 0.480),
            P.Opening("W22", "E1 CB9 span 1", 2.870, 3.470, 0.480),
            P.Opening("W23", "E2 CB9 span 2", 0.400, 1.000, 0.480),
        ],
        extra_held="",
        handles=("W25 jambs CEB / CEA (glazing CDF .. CE9), W21 CC4 / CC3, W22 CD1 / CD0, W23 CDE / CDD; "
                 f"CB9 20x50 continuous (T-110 BM-1F-002, {ST} FFRS), 1F 4.20 - 0.50 = 3.70"),
        class_="SS"),
    "2F-W02": dict(
        census=7.000,
        pieces=[
            P.Piece("SF B3", 2.500, 3.80, "member", top_is_stair_member=True,
                    held_item="SL-1 shaft piece: no floor at +9.70 on the stair-wall line (A-A sheet10; R-T228-3, F4)",
                    held_figure_m2="2.500 x 3.80 = 9.500 - W27 1.500 = 8.000"),
            P.Piece("E1 B8", 3.470, 3.45, "member"),
            P.Piece("R length residual", 0.097, None,
                    held_item="0.097 m between the drawn faces (2.500 + 3.470) and the ledger pieces "
                              "(B3 2.500 + B8 3.567); location not established (T-017 census AGREE 7.000)",
                    held_figure_m2="0.097 x 3.45 = 0.335"),
            P.Piece("H BM-2F-015", 0.933, None,
                    held_item="unlabelled east end span past the column (T-110 BM-2F-015, D-04): depth not printed, "
                              "candidates B8 H75 / B3 H40 (Q-61 C(4): a bound, never a value)",
                    held_figure_m2="0.933 x 3.45 .. 3.80 = 3.219 .. 3.545"),
        ],
        openings=[
            P.Opening("W27", "SF B3", 1.400, 2.400, 1.500),
            P.Opening("W28", "E1 B8", 0.375, 0.975, 0.480),
            P.Opening("W29", "E1 B8", 2.270, 3.470, 1.800),
        ],
        extra_held="",
        handles=(f"W27 jambs 134B / 134A (glazing 133F .. 1349), W28 133D / 133C, W29 1330 / 132F; B8 20x75 "
                 f"(T-110 BM-2F-002, {ST} SFRS), 2F 4.20 - 0.75 = 3.45"),
        class_="SS"),
    "1F-W04": dict(
        census=3.600,
        pieces=[
            P.Piece("E B2 (closed to census)", 2.777, 3.80, "member"),
            P.Piece("H BM-1F-032", 0.823, None,
                    held_item="unlabelled span from the B23 face to the column (T-110 BM-1F-032, D-04): depth not "
                              "printed (Q-61 C(4))",
                    held_figure_m2="0.823 m; T-226 bound 3.040 on 0.80 m at the only candidate B2 H40"),
        ],
        openings=[P.Opening("W13", "E B2 (closed to census)", 0.750, 1.950, 2.760)],
        extra_held="",
        handles=(f"W13 glazing C5A / C5B / C5C (axis Y) lies inside the B2 BM-1F-006 extent (2.70 m) and clear of "
                 f"BM-1F-032 (0.80 m) by 1.000 m; {ST} FFRS B2 20x40, 1F 4.20 - 0.40 = 3.80"),
        class_="SS"),
    "2F-W03": dict(
        census=7.900,
        pieces=[
            P.Piece("E B2 BM-2F-004", 2.430, 3.80, "member"),
            P.Piece("E B1 BM-2F-005", 1.740, 3.80, "member"),
            P.Piece("E B2 BM-2F-006 (closed to census)", 3.196, 3.80, "member"),
            P.Piece("H BM-2F-018", 0.267, None,
                    held_item="unlabelled vertical piece below the column (T-110 BM-2F-018, D-04): depth not printed",
                    held_figure_m2="0.267 x 3.80 = 1.015 at the only candidate B1"),
            P.Piece("H BM-2F-017", 0.267, None,
                    held_item="unlabelled vertical piece below the column (T-110 BM-2F-017, D-04): depth not printed",
                    held_figure_m2="0.267 x 3.80 = 1.015 at the only candidate B1"),
        ],
        openings=[P.Opening("D-2F-01", "E B2 BM-2F-004", 0.416, 1.416, 2.200)],
        extra_held="",
        handles=(f"D-2F-01 door block D115 insert 12BA (1.000 m extent) inside the B2 BM-2F-004 extent, 0.83 m and "
                 f"2.83 m clear of the two unlabelled pieces; {ST} SFRS B1 / B2 20x40, 2F 4.20 - 0.40 = 3.80"),
        class_="SS"),
    "2F-W07": dict(
        census=5.725,
        pieces=[
            P.Piece("E B15 (closed to census)", 2.741, 3.00, "member"),
            P.Piece("H BM-2F-016", 2.984, None,
                    held_item="west band south span (T-110 BM-2F-016, D-04): B15 printed on the north span only; "
                              "depth not printed (candidates B15 H120 or a 20x40 type, Q-61 C(4))",
                    held_figure_m2="2.984 x 3.00 .. 3.80 = 8.952 .. 11.339"),
        ],
        openings=[P.Opening("W26", "E B15 (closed to census)", 0.749, 1.949, 1.875)],
        extra_held="",
        handles=(f"W26 glazing 12CF / 12D0 / 12D1 (axis Y) inside the B15 BM-2F-007 extent (2.70 m) and 0.55 m clear "
                 f"of BM-2F-016; deduction 1.875 = true arched outline (T-238, Checker 22:50); {ST} SFRS B15 20x120, "
                 "2F 4.20 - 1.20 = 3.00"),
        class_="SS"),
    "1F-W18": dict(
        census=5.200,
        pieces=[
            P.Piece("E B5 + slab 1F-057 + B6 (register gross 17.934)", 4.761, round(17.934 / 4.761, 6), "member"),
            P.Piece("H dome opening 1F-076", 0.439, None,
                    held_item="under the open dome ring (T-139 face 1F-076): top of wall not drawn; DETAIL OF DOME "
                              "(1A18, '(N.I.S)' 1A19) prints ring bars only (3%%c16 1A47, 3%%c18 1A4B, 8%%c8/m 1A29)",
                    held_figure_m2="0.439 m, height not drawn"),
        ],
        openings=[],
        extra_held="",
        handles="no opening in the run (T-175 hosts, T-249 inventory 29 / 29 windows)",
        class_="SS"),
    "1F-W24": dict(
        census=2.450,
        pieces=[
            P.Piece("E slab 1F-094 + B6 (register gross 5.651)", 1.426, round(5.651 / 1.426, 6), "member"),
            P.Piece("H dome opening 1F-073", 1.024, None,
                    held_item="under the open dome ring (T-139 face 1F-073): top of wall not drawn; dome detail N.I.S. "
                              "prints no ring depth",
                    held_figure_m2="1.024 m, height not drawn"),
        ],
        openings=[],
        extra_held="",
        handles="no opening in the run (T-175 hosts, T-249 inventory)",
        class_="SS"),
}

SEARCHED = {
    "annex datum (Q-54 B)": "not re-searched beyond T-227 (B-B +4.30 on a layer over the roof band; sanitary SLOPE 1 %); "
                            "owner Q-54 B HOLD stands",
    "lift tie beam size (ST p.8 n.19)": f"{ST}: full text scan this run, 0 texts 'LIFT' / 'TIE BEAM'; the size lives "
                                        "only in the PDF note (consultant row 7, D-43)",
    "beam depth / register conflict": f"{ST}: full text scan this run for a general note on unmarked beams ('UNLESS', "
                                      "'OTHERWISE', 'NOT SHOWN / MARKED', 'ALL BEAMS'): 0 hits; T-226 re-read each span",
    "no member drawn above": f"{ST}: DETAIL OF DOME (1A18, '(N.I.S)' 1A19) prints bars only, no ring size or level",
    "held opening": "heads / sizes: not on any sheet incl. the vector DWF (T-201 / T-227); not re-searched",
    "no wall band or member bound (glazed line / held strip)": "material / base / top printed nowhere (T-227 c)",
    "held increment": "CB2 width CONFLICT schedule 0.20 vs drawn 0.25 (Q-61 C(1)), designer",
}


def read(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(x):
    return float(x) if x not in ("", None, "-") else 0.0


def build():
    v2 = {r["wall_id"]: r for r in read(V2)}
    blockers = read(BLK)
    splits, split_rows = {}, []
    for wid, d in WALLS.items():
        s = P.split_wall(wid, d["pieces"], d["openings"], d["census"])
        splits[wid] = s
        for pc in d["pieces"]:
            ok, why = P.piece_established(pc)
            ops = [o for o in d["openings"] if o.piece == pc.pid]
            split_rows.append(dict(
                wall_id=wid, piece=pc.pid, length_m=f"{pc.length_m:.3f}",
                height_m="" if (pc.height_m is None or not ok) else f"{pc.height_m:.4f}",
                piece_status=SS if ok else "HELD",
                gross_m2=f"{pc.length_m * pc.height_m:.4f}" if ok else "",
                openings="; ".join(f"{o.oid} {o.jamb_a_m:.3f}..{o.jamb_b_m:.3f} m {o.area_m2:.3f}" for o in ops),
                deductions_m2=f"{sum(o.area_m2 for o in ops):.4f}" if ok else "",
                held_item="" if ok else why, held_figure_not_a_quantity="" if ok else pc.held_figure_m2,
                evidence=d["handles"] + " | " + SL1_EVID if wid in ("GF-W10", "1F-W10", "2F-W02") else d["handles"]))
    out = []
    for b in blockers:
        wid = b["wall_id"]
        r = v2[wid]
        row = dict(wall_id=wid, floor=b["floor"], t_m=b["t_m"], block_type=b["block_type"], cause_class=b["cause_class"],
                   v2_status=b["status"], v2_gross_figure_m2=b["gross_figure_m2 (not a quantity when HELD)"],
                   v2_deductions_m2=r["deductions_m2"])
        if wid in splits:
            s = splits[wid]
            d = WALLS[wid]
            hf = "; ".join(p.held_figure_m2 for p in d["pieces"] if p.pid in s.held_pieces)
            if d["extra_held"]:
                hf += "; " + d["extra_held"]
            row.update(t261_verdict="SPLIT: part established, rest STILL-HELD",
                       settled_item=("opening-to-piece assignment from the drawn jambs and the drawn column / band "
                                     "faces (R-T261-1); the established pieces' heights are those already in register "
                                     "v2 / the Checker's own figure"),
                       established_gross_m2=f"{s.established_gross_m2:.4f}",
                       established_deductions_m2=f"{s.established_deductions_m2:.4f}",
                       established_net_m2=f"{s.established_m2:.4f}", established_class=d["class_"],
                       established_m3=f"{s.established_m2 * f(b['t_m']):.4f}",
                       still_held=f"pieces {', '.join(s.held_pieces)}; openings {', '.join(s.held_openings) or 'none'}",
                       held_figure_not_a_quantity=hf,
                       wall_net_text=P.wall_total_text(s, hf),
                       searched_this_run="plan geometry by handle (T261_SPLIT.csv); " + d["handles"])
        else:
            row.update(t261_verdict="STILL-HELD", settled_item="", established_gross_m2="",
                       established_deductions_m2="", established_net_m2="", established_class="", established_m3="",
                       still_held=b["exact_missing_item"],
                       held_figure_not_a_quantity=b["smallest_affected_quantity"],
                       wall_net_text="HELD" if b["status"] != "net established + HELD increment" else
                       f"{r['net_m2']} established (v2, unchanged) + HELD increment",
                       searched_this_run=_searched(b, wid))
        row["next"] = _next(b, wid)
        out.append(row)
    cov = coverage(v2, splits)
    return out, split_rows, cov, splits


def _searched(b, wid):
    if wid == "2F-W05":
        return (f"{ARCH}: door D-2F-02 block d220 insert 12C2 (0.90 m) lies under the unlabelled BM-2F-017 extent, so its "
                "1.980 belongs to the held piece; no split proposed: the mapped member extents (B1 BM-2F-009 1.00 m, "
                "BM-2F-017 1.40 m) leave 0.70 m of the 2.250 m run under neither member (re-measure first). "
                + SEARCHED["beam depth / register conflict"])
    if wid in ("1F-W11", "1F-W13", "1F-W17"):
        return ("no split proposed: the door(s) " + {"1F-W11": "D-1F-01 (0.80 m) against 0.240 m of established pieces",
                                                     "1F-W13": "D-1F-08 / D-1F-09", "1F-W17": "D-1F-10"}[wid]
                + " were not located against the dome-face pieces this run. " + SEARCHED["no member drawn above"])
    if wid == "GF-W03":
        return "two marks CB3 20x75 / 'B3 (With Stair)' 1826 / 1827 on one span (D-03) and the GF base under the ST-02 " \
               "flight not printed (R-T228-3 SL-2, Verifier 11:59); not re-searched"
    return SEARCHED.get(b["cause_class"], "not re-searched this run")


def _next(b, wid):
    if wid in WALLS:
        return "Checker: re-measure the split (pieces, jambs, openings) before any class rises; lane I to carry it"
    return b["next"] or "designer / consultant item as named"


def coverage(v2, splits):
    g = defaultdict(lambda: [0.0, 0.0, 0, 0])
    for wid, r in v2.items():
        k = (r["floor"], r["t_m"], r["block_type"])
        if r["net_class"] != "HELD" and r["net_m2"] not in ("", "-"):
            g[k][0] += f(r["net_m2"])
        if wid in splits:
            g[k][1] += splits[wid].established_m2
            g[k][3] += 1
        if r["net_class"] == "HELD":
            g[k][2] += 1
    rows = []
    for k in sorted(g):
        a, add, nh, ns = g[k]
        rows.append(dict(floor=k[0], t_m=k[1], block_type=k[2], net_established_v2_m2=f"{a:.4f}",
                         split_established_added_m2=f"{add:.4f}", net_established_proposed_m2=f"{a + add:.4f}",
                         walls_net_held_v2=nh, of_which_split=ns))
    return rows


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def outputs():
    out, split_rows, cov, splits = build()
    tot_v2 = sum(f(c["net_established_v2_m2"]) for c in cov)
    add = sum(f(c["split_established_added_m2"]) for c in cov)
    m3 = sum(splits[w].established_m2 * f(WALLS_T[w]) for w in splits)
    summ = dict(
        task="T-261", base_register="research/agents_t228 (T-228 r2, MERGED bf4dd2a9)",
        blockers=len(out), split=sum(1 for r in out if r["t261_verdict"].startswith("SPLIT")),
        still_held=sum(1 for r in out if r["t261_verdict"] == "STILL-HELD"),
        established_net_v2_m2=round(tot_v2, 3), split_established_added_m2=round(add, 4),
        established_net_proposed_m2=round(tot_v2 + add, 3), split_established_added_m3=round(m3, 4),
        by_wall={w: s.established_m2 for w, s in splits.items()},
        applied_to_register=False, released_default="V2.9 + route G (unchanged)")
    return {"T261_BLOCKERS.csv": to_csv(out), "T261_SPLIT.csv": to_csv(split_rows), "T261_COVERAGE.csv": to_csv(cov),
            "summary.json": json.dumps(summ, indent=2) + "\n"}


WALLS_T = {"GF-W10": 0.2, "1F-W10": 0.2, "2F-W02": 0.2, "1F-W04": 0.2, "2F-W03": 0.15, "2F-W07": 0.2, "1F-W18": 0.15,
           "1F-W24": 0.15}


def main(argv=None):
    argv = argv or sys.argv[1:]
    outs = outputs()
    if "--check" in argv:
        bad = [n for n, t in outs.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-261 outputs " + ("STALE: " + ", ".join(bad) if bad else "reproduce"))
        return 1 if bad else 0
    for n, t in outs.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(outs["summary.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
