"""T-117: MASONRY_CENTRELINE_V1 on Alsenan vs the T-103 hand table, wall run by wall run; walls that contain columns
(designer item D-12); the T-107 block-type table. Reads the JSON of alsenan_centreline_run.py (scratchpad, outside the
repository) and research/agents_t103/WALLS_BY_FLOOR_THICKNESS.csv; writes the CSVs of research/agents_t117 and
research/agents_t107 (lengths, thicknesses, marks and LOCAL metres only: origin = the lower-left corner of each floor's
wall centrelines; no drawing coordinates, no names).
Usage: python3 -I research/agents_t117/t117_compare.py <t117.json> [--write]"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAND = ROOT / "research/agents_t103/WALLS_BY_FLOOR_THICKNESS.csv"
OUT117 = ROOT / "research/agents_t117"
OUT107 = ROOT / "research/agents_t107"

# engine piece (floor, wall_id suffix) -> T-103 rows, the cause of the difference and the verdict proposal.
# Read off the plots of the wall layer (scratchpad) by the worker; each cause is re-checked in the write-up.
J = "JUNCTION: the hand table runs a T stem to the through-wall centreline (the T piece counted twice); " \
    "the piece stops it on the through-wall face (T piece once, in the wall that runs through)"
MAP = {
    "GF": [
        ("FL0001-FL0002", ["GF-W00", "GF-W01"], "BAND_ACROSS_PASSAGE_MOUTH: the band runs 1.20 m across the south "
         "mouth of the open-air side passage (x 10.70-11.90 local; both lines there are on a non-wall layer) plus "
         "0.10 m of the passage wall line", "HAND_RIGHT"),
        ("FL0007-FL0008", ["GF-W02", "GF-W03"], "BAND_ACROSS_OPEN_FLOOR: one band from the annex W.C. wall (x 7.80) "
         "to the reception garden wall (x 25.37) on y 1.50: 1.00 m + 11.22 m with no wall face on any side, no "
         "opening (side passage, garden strip); only 4.30 m of the 16.52 m is wall", "HAND_RIGHT"),
        ("FL0010-FL0011", ["GF-W27"], "DOORWAY_AT_FREE_END: the 0.80 door between the wall end (x 5.12) and the "
         "0.15 wall x 4.175 is not in the run (OPENING_GAP joins only two collinear bands) 0.874 m; T piece 0.15",
         "HAND_RIGHT (0.874) / ENGINE_RIGHT (0.150)"),
        ("FL0017-FL0018", ["GF-W04", "GF-W05"], "BAND_ACROSS_PASSAGE_MOUTH: the band runs 1.20 m across the north "
         "mouth of the side passage (x 10.70-11.90, no wall face, no opening)", "HAND_RIGHT"),
        ("FL0020-FL0021", ["GF-W06"], "", "EQUAL"),
        ("FL0023-FL0024", ["GF-W07"], "", "EQUAL"),
        ("FL0025-FL0026", ["GF-W08"], J, "ENGINE_RIGHT"),
        ("FL0028-FL0029", ["GF-H01"], "0.40 BAND: released by the piece as family 0.40 (0.60 m); the hand table "
         "HOLDS it (0.40 is no block family on this drawing, material not printed); outside the 0.15 / 0.20 totals",
         "HAND_RIGHT on status (HELD)"),
        ("FL0030-FL0031", ["GF-W28"], "", "EQUAL"),
        ("FL0032-FL0033", ["GF-W09"], "", "EQUAL"),
        ("FL0038-FL0039", ["GF-W29"], "DOORWAY_AT_FREE_END: the W.C. door between the wall end and the next wall "
         "is not in the run; T piece 0.075", "HAND_RIGHT (0.649) / ENGINE_RIGHT (0.075)"),
        ("FL0041-FL0042", ["GF-W10"], "", "EQUAL"),
        ("FL0046-FL0047", ["GF-W33"], "45 DEG JUNCTION: one end HELD by the piece (max 0.137 m listed) and the "
         "other cut square at the drawn end", "UNRESOLVED (piece HELD)"),
        ("FL0048-FL0049", ["GF-W32"], "45 DEG JUNCTION: one end HELD (max 0.278 m listed)", "UNRESOLVED (piece HELD)"),
        ("FL0055-FL0056", ["GF-W11"], "", "EQUAL"),
        ("FL0057-FL0058", ["GF-W12"], "", "EQUAL"),
        ("FL0059-FL0060", ["GF-W19"], J, "ENGINE_RIGHT"),
        ("FL0063-FL0064", ["GF-W20", "GF-W21"], "BAND_ACROSS_OPEN_FLOOR: the two 0.15 stubs on x 21.925 (bottom "
         "1.05 m, top 1.00 m) joined across the 1.96 m inside the wedge-shaped W.C. pair (diagonal walls only, no "
         "face on x 21.925)", "HAND_RIGHT"),
        ("FL0068-FL0069", ["GF-W13"], "corner end HELD by the piece (max 0.20 m listed)", "UNRESOLVED (piece HELD)"),
        ("FL0070-FL0072", ["GF-W22"], J + "; top end cut at 13.087 where the diagonal W.C. wall meets it",
         "ENGINE_RIGHT (0.100) / UNRESOLVED (0.181)"),
        ("FL0076-FL0077", ["GF-W14"], "", "EQUAL"),
        ("FL0078-FL0079", ["GF-W15"], "", "EQUAL"),
        ("FL0081-FL0082", ["GF-W16"], "", "EQUAL"),
        ("FL0083-FL0084", ["GF-W17"], J, "ENGINE_RIGHT"),
        ("FL0086-FL0087", ["GF-W23"], J, "ENGINE_RIGHT"),
        ("FL0089-FL0090", ["GF-W24"], J, "ENGINE_RIGHT"),
        ("FL0092-FL0093", ["GF-W25"], J, "ENGINE_RIGHT"),
        ("FL0094-FL0096", ["GF-W36"], "", "EQUAL"),
        ("FL0095-FL0096", ["GF-W26"], J, "ENGINE_RIGHT"),
        ("FL0097-FL0098", ["GF-W18"], "", "EQUAL"),
        ("FL0100-FL0101", ["GF-W31"], "45 DEG JUNCTION: one end HELD (max 0.137 m listed)", "UNRESOLVED (piece HELD)"),
        ("FL0102-FL0103", ["GF-W34"], "45 DEG JUNCTION: both ends cut square at the drawn ends (0.256 m short of "
         "the hand centreline lengths)", "UNRESOLVED"),
        ("ARCBAND|D2:269:0|D2:270:0", ["GF-W35"], "", "EQUAL"),
        (None, ["GF-W30"], "NOT_IN_RUN: the 0.30 m stub from the wedge corner and the 0.797 m door beside it form "
         "no band (stub under the 0.30 m band rule, door at a free end)", "HAND_RIGHT"),
        (None, ["GF-W37"], "NO_BAND: the pool-side line is drawn as a 0.20 band filled with glazing (4.95 m chord; "
         "the PDF prints a curved glass wall); 0.10 m of it is block", "ENGINE_RIGHT on run (glass screen) / "
         "HAND_RIGHT (0.10 m solid)"),
        (None, ["GF-H02"], "HELD in the hand table (0.20 x 0.90 outline on the stair layer); not on the wall layer",
         "EQUAL (neither measures it)"),
    ],
    "1F": [
        ("FL0002-FL0003", ["1F-W06"], "", "EQUAL"),
        ("FL0006-FL0007", ["1F-W11"], J, "ENGINE_RIGHT"),
        ("FL0011-FL0012", ["1F-W12"], "DOORWAY_AT_FREE_END: the 1.00 doorway between the wall end (x 5.589) and the "
         "0.15 wall x 4.425 is not in the run 1.089 m; T piece 0.075", "HAND_RIGHT (1.089) / ENGINE_RIGHT (0.075)"),
        ("FL0013-FL0014", ["1F-W13"], J, "ENGINE_RIGHT"),
        ("FL0016-FL0018", ["1F-W07"], J, "ENGINE_RIGHT"),
        ("FL0020-FL0021", ["1F-W08"], "", "EQUAL"),
        ("FL0022-FL0023", ["1F-W14", "1F-W15"], "OPEN_DOORWAY_IN_HAND: the 1.375 m doorless opening between the two "
         "pieces (x 15.27-16.645) is in the piece's run and in neither hand row (the T-103 basis keeps openings in "
         "the run); east end stops at the mitred cap of the curved bay (0.234 m)",
         "ENGINE_RIGHT (1.375) / UNRESOLVED (0.234)"),
        ("FL0024-FL0025", ["1F-W09"], "", "EQUAL"),
        ("FL0027-FL0028", ["1F-W16"], J + " (and the L corner given to the vertical x 9.125)", "ENGINE_RIGHT"),
        ("FL0030-FL0031", ["1F-W10"], "", "EQUAL"),
        ("FL0041-FL0042", ["1F-W00", "1F-W01", "1F-W25"], "CURVED_BAY_AS_CHORD: the east band runs straight across "
         "the concave curved bay (glazing on the chord line, y 7.67-10.73) instead of the 3.673 m arc wall; the arc "
         "becomes a 0.169 m curved stub", "HAND_RIGHT"),
        ("1F-STUB-001", [], "curved stub of the bay (counted with FL0041)", ""),
        ("FL0043-FL0044", ["1F-W17"], J, "ENGINE_RIGHT"),
        ("FL0046-FL0047", ["1F-W18"], J, "ENGINE_RIGHT"),
        ("FL0050-FL0051", ["1F-W19"], J, "ENGINE_RIGHT"),
        ("FL0054-FL0055", ["1F-W20"], "", "EQUAL"),
        ("FL0059-FL0060", ["1F-W21"], J + " (L corner held by this wall)", "ENGINE_RIGHT"),
        ("FL0059-FL0061", ["1F-W02"], "", "EQUAL"),
        ("FL0063-FL0065", ["1F-W22"], J, "ENGINE_RIGHT"),
        ("FL0068-FL0070", ["1F-W03"], "", "EQUAL"),
        ("FL0074-FL0075", ["1F-W23"], "DOORWAY_AT_FREE_END: the door between the wall end (y 0.98) and the south "
         "wall is not in the run 0.88 m; T piece 0.10", "HAND_RIGHT (0.880) / ENGINE_RIGHT (0.100)"),
        ("FL0074-FL0076", ["1F-W04"], "", "EQUAL"),
        ("FL0078-FL0079", ["1F-W24"], J, "ENGINE_RIGHT"),
        ("FL0082-FL0083", ["1F-W05"], "", "EQUAL"),
    ],
    "2F": [
        ("FL0002-FL0003", ["2F-W03"], "", "EQUAL"),
        ("FL0004-FL0005", ["2F-W00"], "", "EQUAL"),
        ("FL0006-FL0007", ["2F-W01"], "", "EQUAL"),
        ("FL0010-FL0011", ["2F-W02"], "", "EQUAL"),
        ("FL0020-FL0021", ["2F-W04"], "", "EQUAL"),
        ("FL0024-FL0025", ["2F-W08"], J, "ENGINE_RIGHT"),
        ("FL0024-FL0026", ["2F-W05"], J, "ENGINE_RIGHT"),
        ("FL0031-FL0032", ["2F-W06"], "", "EQUAL"),
        ("FL0035-FL0036", ["2F-W07"], "", "EQUAL"),
    ],
}
FREELANCER = {"GF": 134.28, "1F": 120.31, "2F": 39.10}      # T-103 / verifier 11:35 (his blockwork workbook, Drive)


def hand_rows():
    rows = {}
    for r in csv.DictReader(open(HAND)):
        if r["row_id"] and r["row_id"][:3] in ("GF-", "1F-", "2F-"):
            rows[r["row_id"]] = r
    return rows


def short(wid):
    return wid[3:] if wid.startswith("WB-") else wid


def col_width(q, ux, uy, nx, ny):
    us = [x * ux + y * uy for x, y in q]
    ns = [x * nx + y * ny for x, y in q]
    return max(us) - min(us), max(ns) - min(ns)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    write = "--write" in argv
    D = json.load(open([a for a in argv if not a.startswith("--")][0]))
    H = hand_rows()
    from shapely.geometry import LineString, Polygon
    runs, d12, used = [], [], set()
    floor_tot = {}
    for fl, items in MAP.items():
        f = D["floors"][fl]
        P = {short(p["wall_id"]): p for p in f["record"]["pieces"]}
        Bb = {short(b["wall_id"]): b for b in f["bands"]}
        band_run = {}
        for b in D["band_basis"].get(fl) or ():
            band_run[b["family"]] = b["masonry_run_lm"]
        seen = set()
        for wid, hids, cause, verdict in items:
            p = P.get(wid) if wid else None
            if wid:
                assert p is not None, (fl, wid)
                seen.add(wid)
            hm = sum(float(H[h]["gross_minus_columns_m"]) for h in hids if H[h]["status"] == "MEASURED")
            held = [h for h in hids if H[h]["status"] != "MEASURED"]
            used.update(hids)
            e = p["run_lm"] if p else None
            b = Bb.get(wid) if wid else None
            loc = b["local_m"] if b else None
            runs.append({"floor": fl, "engine_piece": wid or "-", "t_m": (p or {}).get("t_m") or
                         (H[hids[0]]["thickness_m"] if hids else ""),
                         "engine_ends": "/".join(p["ends"]) if p else "",
                         "local_start_m": "%.3f %.3f" % tuple(loc[0]) if loc else "",
                         "local_end_m": "%.3f %.3f" % tuple(loc[-1]) if loc else "",
                         "engine_columns_cut_m": "%.3f" % p["columns_lm"] if p else "",
                         "engine_run_m": "%.3f" % e if e is not None else "not measured (no band)",
                         "hand_rows": " + ".join(hids), "hand_run_m": "%.3f" % hm if not held else
                         ("HELD (%s)" % ", ".join(held) if not hm else "%.3f + HELD" % hm),
                         "diff_m": "%+.3f" % ((e or 0.0) - hm) if not held and hids else "",
                         "cause": cause, "verdict_proposal": verdict})
            # D-12: columns inside this run (centreline stretch inside a column polygon), width across the wall
            if p and b and len(loc) == 2 and p["ends"][0] != "CURVED":
                (ax, ay), (bx, by) = loc
                L = math.hypot(bx - ax, by - ay)
                ux, uy = (bx - ax) / L, (by - ay) / L
                nx, ny = -uy, ux
                s0, s1 = -p["corner_ext_m"][0], L + p["corner_ext_m"][1]
                ln = LineString([(ax + ux * s0, ay + uy * s0), (ax + ux * s1, ay + uy * s1)])
                for q in f["columns_local_m"]:
                    g = ln.intersection(Polygon(q))
                    if g.is_empty or g.length <= 0:
                        continue
                    along, across = col_width(q, ux, uy, nx, ny)
                    d12.append({"floor": fl, "engine_piece": wid, "hand_rows": " + ".join(hids),
                                "wall_t_drawn_m": "%.3f" % p["t_m"], "column_across_wall_m": "%.3f" % across,
                                "column_along_wall_m": "%.3f" % along, "centreline_inside_column_m": "%.3f" % g.length,
                                "kind": ("COLUMN_IN_LINE" if g.length >= 0.5 * along - 1e-6 and along >= across - 1e-6
                                         else "END_OR_CORNER_COLUMN" if g.length >= 0.08 else "CONTACT"),
                                "wider_than_wall": "YES" if across > p["t_m"] + 0.005 else "no"})
        missing = sorted(set(P) - seen)
        assert not missing, (fl, missing)
        fams = {}
        for p in f["record"]["by_thickness"]:
            fams[p["family"]] = p["masonry_run_lm"]
        hand_f = {}
        for h, r in H.items():
            if h.startswith(fl) and r["status"] == "MEASURED":
                t = "%.2f" % float(r["thickness_m"])
                hand_f[t] = hand_f.get(t, 0.0) + float(r["gross_minus_columns_m"])
        floor_tot[fl] = (fams, band_run, hand_f)
    # D-12 summary: per run with a column IN LINE wider than the drawn wall, metres as drawn vs at the column width
    d12_runs = {}
    for x in d12:
        if x["kind"] == "COLUMN_IN_LINE" and x["wider_than_wall"] == "YES":
            k = (x["floor"], x["engine_piece"], x["hand_rows"], x["wall_t_drawn_m"])
            d12_runs[k] = max(d12_runs.get(k, 0.0), float(x["column_across_wall_m"]))
    run_m = {(r["floor"], r["engine_piece"]): r for r in runs}
    d12_sum = []
    for (fl, wid, hr, t), w in sorted(d12_runs.items()):
        r = run_m[(fl, wid)]
        d12_sum.append({"floor": fl, "engine_piece": wid, "hand_rows": hr, "t_drawn_m": t,
                        "t_by_note_s2_m": "%.3f" % w, "engine_run_m": r["engine_run_m"], "hand_run_m": r["hand_run_m"],
                        "status": "CONFLICT (designer D-12): drawn %s vs column width %.2f; never chosen" % (t, w)})
    unmatched = sorted(h for h in H if h not in used)
    assert not unmatched, unmatched

    # per floor and thickness: engine (column polygons) / engine (band basis) / hand / freelancer
    tot = []
    for fl, (fams, band_run, hand_f) in floor_tot.items():
        for t in sorted(set(fams) | set(hand_f)):
            e, h = fams.get(t), hand_f.get(t)
            tot.append({"floor": fl, "thickness": t, "engine_run_m": "%.3f" % e if e is not None else "-",
                        "engine_band_basis_m": "%.3f" % band_run[t] if t in band_run else "-",
                        "hand_t103_m": "%.3f" % h if h is not None else "-",
                        "engine_minus_hand_m": "%+.3f" % (e - h) if e is not None and h is not None else "",
                        "engine_vs_hand_pct": "%+.1f" % (100 * (e - h) / h) if e is not None and h else "",
                        "freelancer_m": "", "note": "0.40 band: hand HELD (GF-H01)" if t == "0.40" else ""})
        e = sum(v for k, v in fams.items() if k in ("0.15", "0.20"))
        b = sum(v for k, v in band_run.items() if k in ("0.15", "0.20"))
        h = sum(hand_f.values())
        fr = FREELANCER[fl]
        tot.append({"floor": fl, "thickness": "0.15+0.20", "engine_run_m": "%.3f" % e, "engine_band_basis_m": "%.3f" % b,
                    "hand_t103_m": "%.3f" % h, "engine_minus_hand_m": "%+.3f" % (e - h),
                    "engine_vs_hand_pct": "%+.1f" % (100 * (e - h) / h), "freelancer_m": "%.2f" % fr,
                    "note": "engine vs freelancer %+.3f m (%+.1f %%); hand vs freelancer %+.3f m (%+.1f %%)"
                            % (e - fr, 100 * (e - fr) / fr, h - fr, 100 * (h - fr) / fr)})
    for t in tot:
        print(" | ".join(str(v) for v in t.values()))
    agg = {}
    for x in d12_sum:
        k = (x["floor"], x["t_drawn_m"], x["t_by_note_s2_m"])
        try:
            agg[k] = agg.get(k, 0.0) + float(x["hand_run_m"])
        except ValueError:
            pass
    for x in d12_sum:
        print("D12", x["floor"], x["engine_piece"], x["hand_rows"], x["t_drawn_m"], "->", x["t_by_note_s2_m"],
              x["engine_run_m"], x["hand_run_m"])
    for k in sorted(agg):
        print("D12 hand metres", k, round(agg[k], 3))
    if write:
        OUT117.mkdir(exist_ok=True)
        for name, rows in (("ENGINE_VS_HAND_BY_RUN.csv", runs), ("TOTALS_BY_FLOOR_THICKNESS.csv", tot),
                           ("D12_WALLS_WITH_COLUMNS.csv", d12), ("D12_CONFLICT_RUNS.csv", d12_sum)):
            with open(OUT117 / name, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
        block_types(H)
    return runs, tot, d12


# T-107 typed table (worker 2, 14:45; verifier 15:10 reconciled the totals): every T-103 row with block type, source
# note and status. Sources: S1 = structural set p.1 notes box note 2 (neighbour-side external ground beams cast with
# black block above and below, built from foundation level; extent D-11); Q-60 fallback (owner 10:45: "if not,
# consider outer is white, inner black"); Q-65 open (parapets, street fence); Q-63 C (sea-side element unresolved).
S1 = {"GF-W00", "GF-W01"}


def block_types(H):
    rows = []
    for r in csv.DictReader(open(HAND)):
        rid, grp = r["row_id"], r["group"]
        if not rid or rid == "TOTAL" or not grp:
            continue
        shape, m = r["shape"], r["gross_minus_columns_m"]
        if rid in S1:
            typ, src, st = "BLACK", "S1 structural p.1 note 2 (extent: designer D-11)", "PROVISIONAL"
        elif grp == "EXTERNAL":
            typ, src, st = "WHITE", "owner Q-60 fallback 10:45 (outer white); no block-type note on any sheet", "ASSUMED"
        elif grp == "INTERNAL":
            typ, src, st = "BLACK", "owner Q-60 fallback 10:45 (inner black); no block-type note on any sheet", "ASSUMED"
        elif grp == "FENCE" and shape.startswith("north"):
            typ, src, st = "BLACK", "S1 structural p.1 note 2 (neighbour-side ground beams; extent D-11)", "PROVISIONAL"
        elif grp == "FENCE" and shape.startswith("street"):
            typ, src, st = "-", "owner Q-65 open (fallback names walls, not fences)", "HELD"
        elif grp == "FENCE":
            typ, src, st = "-", "owner Q-63 C: visible unresolved element, material unknown", "UNRESOLVED"
        elif grp == "PARAPET":
            typ, src, st = "-", "owner Q-65 open (parapet 'Brick Wall', structural p.14, no colour)", "HELD"
        else:
            typ, src, st = "-", "hand table HELD: " + r["status"], "HELD"
        d12 = rid in ("GF-W28", "1F-W18", "1F-W23")
        rows.append({"row_id": rid, "floor": r["floor"], "group": grp, "thickness_m": r["thickness_m"] or "HELD",
                     "metres_gross_minus_columns": m or "HELD", "block_type": typ, "source": src, "status": st,
                     "thickness_conflict_d12": "CONFLICT: 0.15 drawn with a column inside (S2 p.8 rec. 20)" if d12 else ""})
    OUT107.mkdir(exist_ok=True)
    with open(OUT107 / "BLOCK_TYPE_BY_RUN.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    agg = {}
    for x in rows:
        k = (x["floor"].split()[0], x["block_type"], x["status"])
        try:
            agg[k] = agg.get(k, 0.0) + float(x["metres_gross_minus_columns"])
        except ValueError:
            agg[k] = agg.get(k, 0.0)
    for k in sorted(agg):
        print("type", k, round(agg[k], 3))
    print("typed rows", len(rows))


if __name__ == "__main__":
    main()
