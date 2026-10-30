"""T-362 read-only application on the development villa (every villa by R-T362-1 .. 4, t362_masonry_white.py).

Inputs are MERGED ledgers of this repository only (no drawing coordinate, image, note text or client name):
  walls, pieces, openings, lintel depths   research/agents_t355/t355_alsenan.panels() / ledger() (T-355 r2, merged
                                           21f7b58a): register v4 x V2 runs x T-274 pieces x T-261 split, T-237 sizes,
                                           ST p.13 LINTEL SCHEDULE depth bands, printed MIN. 40 cm bearing
  T-261 piece heights                      research/agents_t317/t317_alsenan.build()
  white block families                     owner Q-60 answer (2026-10-20 10:45, OWNER_QUESTIONS_ANSWERED.md): supplier
                                           pallet list, family A 62.5 x 25 face, family B 60 x 20 face
  adhesive / first bed                     owner's stored takeoff notes (quantity-takeoff-rules s.2.2: thin-bed glue
                                           "about 2 mm"; first course on a levelled cement bed "at least 1 cm")
  lintel concrete line (cross-check)       research/alsenan_lintels_s8_6/06_LINTEL_CONCRETE_QTO.csv + 01_OPENING_CENSUS
  opening hosts / thickness                research/agents_t175/T175_OPENING_HOSTS.csv

    python3 -I research/agents_t362/t362_alsenan.py [--write | --check]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(RES / "agents_t355"))
sys.path.insert(2, str(RES / "agents_t317"))
import t362_masonry_white as W  # noqa: E402
import t355_alsenan as T355  # noqa: E402
import t355_masonry_accessories as X  # noqa: E402
import t317_alsenan as T317  # noqa: E402

STATIONS, STATION_WHY, BLACK_TIES = None, None, []
SRC_Q60 = "owner Q-60 answer 2026-10-20 10:45 (supplier pallet list, OWNER_QUESTIONS_ANSWERED.md)"
FAMILIES = [
    W.family("A", 0.250, f"{SRC_Q60}: family A, 62.5 x 25 face (pallet volumes 10 .. 30 cm all close on 0.625 x 0.25)"),
    W.family("B", 0.200, f"{SRC_Q60}: family B, 60 x 20 face (15-20-60, 20-20-60)"),
]
BAND = W.band(0.001, 0.003, 0.010, 0.020,
              "owner's stored takeoff notes s.2.2 ('thin-bed glue mortar, about 2 mm joint' -> band 1 .. 3 mm; 'first "
              "course on a levelled cement bed at least 1 cm' -> 10 mm low end; 20 mm high end = SENSITIVITY WINDOW "
              "only, not a sourced value: a level that moves inside it is HELD, never counted)")
UNKNOWN_WALLS = {
    "GF-W30": "no census run: held opening (T-228 / T-274 hand row); no pieces or block tops",
    "GF-W37": "no wall band or member bound (glazed line / held strip; T-228 designer list): material, base, top",
    "GF-H01": "block type not established ('-' in register v4), 0.40 band; glazed line / held strip: designer",
    "GF-H02": "block type not established ('-' in register v4); glazed line / held strip: designer",
    "1F-W25": "T-222 bay row: area ESTABLISHED 1.490 m2, but no run pieces (base, top, columns) to place levels",
    "1F-W00/W01 BAY-ENDS": "T-222 bay-end row: area ESTABLISHED 0.572 m2, no run pieces (split between the two runs "
                           "of one band not drawn)",
    "GF P-GF-05 ABOVE-LINTEL": "masonry above the P-GF-05 lintel, 2.640 m2 ESTABLISHED; its course datum is the lintel "
                               "top, no piece record: levels not placed",
}


def rd(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stations():
    """jamb stations of each register opening on its V2 run (T-274 OPENING_GAPS, same run coordinates as
    T274_RUN_PIECES): masonry to the next column, opening or run end on each side. Only runs without a '#k' split
    suffix offset problem are used: a gap station must fall inside the run."""
    hosts = {r["ID"]: r for r in rd(RES / "agents_t175/T175_OPENING_HOSTS.csv")}
    gaps = rd(RES / "agents_t274/T274_OPENING_GAPS.csv")
    pieces = defaultdict(list)
    for r in rd(RES / "agents_t274/T274_RUN_PIECES.csv"):
        pieces[r["run_key"]].append(r)
    out, why = {}, {}
    for oid, h in hosts.items():
        run = h["V2_RUN"]
        if not run or not h["ENGINE_OPENING"]:
            why[oid] = "no V2 run / engine opening in T-175: jamb stations not tied"
            continue
        base = run.split("#")[0]
        g = [x for x in gaps if x["floor"] == h["FLOOR"] and x["band_id"] == base and x["ref"] == h["ENGINE_OPENING"]]
        P = pieces.get(f"{h['FLOOR']}|{run}", [])
        if len(g) != 1 or not P:
            why[oid] = "no unique T-274 gap row or no run pieces"
            continue
        a, b = float(g[0]["from_m"]), float(g[0]["to_m"])
        s0 = min(float(x["from_m"]) for x in P)
        s1 = max(float(x["to_m"]) for x in P)
        if a < s0 - 1e-6 or b > s1 + 1e-6:
            why[oid] = f"gap station {a} .. {b} outside run {run} ({s0} .. {s1}): sub-run offset not recorded"
            continue
        cols = [(float(x["from_m"]), float(x["to_m"])) for x in P if x["kind"] == "COLUMN"]
        oth = [(float(x["from_m"]), float(x["to_m"])) for x in gaps if x["floor"] == h["FLOOR"] and
               x["band_id"] == base and x["ref"] != h["ENGINE_OPENING"]]
        left = max([s0] + [t for f, t in cols + oth if t <= a + 1e-6])
        right = min([s1] + [f for f, t in cols + oth if f >= b - 1e-6])
        out[oid] = (round(a - left, 6), round(right - b, 6))
        why[oid] = (f"{run} jambs {a} .. {b}; masonry {a - left:.4f} / {right - b:.4f} to "
                    f"{'run start' if left == s0 else 'column / opening'} / {'run end' if right == s1 else 'column / opening'}")
    return out, why


def white_panels():
    P, unknown, named, lost = T355.panels("PRIMARY")
    _, _, t261, _ = T317.build()
    out = []
    for p in P:
        if p["block_type"] != "WHITE":
            continue
        tie = p["tie"]
        if p["wall_id"] in t261:
            hs = [float(x["height_m"]) if x["height_m"] else None for x in t261[p["wall_id"]]]
            p = dict(p, t261_heights=hs)
        out.append(p)
    return out, unknown, named, lost


def t261_tie_panel(p, fam):
    """T-355's T-261 rule per family: the tie top is known only when every T-261 piece height gives the same level
    count at both band corners; otherwise the junction stays HELD."""
    hs = p.get("t261_heights")
    if hs is None:
        return p["tie"], ""
    known = [h for h in hs if h is not None]
    top = None
    if known and None not in hs:
        counts = set()
        for _, spec, d in W.corners(fam, BAND):
            counts.add(X.n_levels(spec, min(known) - d))
            counts.add(X.n_levels(spec, max(known) - d))
        if len(counts) == 1:
            top = min(known)
    pcs = tuple(x if x.kind == "COLUMN" else replace(x, top=top) for x in p["tie"].pieces)
    note = (f"T-261 heights {min(known)} .. {max(known)} give one tie count" if top is not None else
            "T-261 piece heights not tied to the column stations and not one tie count: HELD")
    return replace(p["tie"], pieces=pcs), note


def white_ledger():
    P, unknown, named, lost = white_panels()
    levels, walls, ties = [], [], []
    for p in P:
        row = {"wall_id": p["wall_id"], "floor": p["floor"], "group": p["group"], "t_m": p["t_m"],
               "block_run_m": round(sum(x.length for x in p["mesh"].pieces if x.kind == "BLOCK"), 6),
               "notes": p["notes"]}
        mp, tied = W.with_stations(p["mesh"], STATIONS)
        for fam in FAMILIES:
            recs, st = W.white_levels(mp, fam, BAND, tied)
            for r in recs:
                r["group"] = p["group"]
            levels += recs
            row[f"{fam.name}_levels"] = len(recs)
            row[f"{fam.name}_state"] = st if not recs else "CONDITIONAL (family not established)"
            row[f"{fam.name}_certain_net_m"] = round(sum(r["certain_net_m"] for r in recs), 6) if recs else None
            row[f"{fam.name}_band_held_m"] = round(sum(r["band_held_m"] for r in recs), 6) if recs else None
            row[f"{fam.name}_other_held_m"] = round(sum(r["held_m"] for r in recs), 6) if recs else None
            tp, note = t261_tie_panel(p, fam)
            for t in W.white_ties(tp, fam, BAND):
                t["family"], t["group"] = fam.name, p["group"]
                if note:
                    t["note"] = note
                ties.append(t)
        walls.append(row)
    for fam in FAMILIES:
        W.check_one_owner([t for t in ties if t["family"] == fam.name])
    return {"levels": levels, "walls": walls, "ties": ties, "unknown": unknown, "named": named, "lost": lost}


def black_restated():
    led = T355.ledger("PRIMARY")
    before = [r for r in led["mesh"] if r["block_type"] == "BLACK"]
    P, *_ = T355.panels("PRIMARY")
    after = []
    for p in P:
        if p["block_type"] != "BLACK" or p["course_held"]:
            continue
        mp, tied = W.with_stations(p["mesh"], STATIONS)
        recs, _ = X.mesh_levels(mp)
        for r in recs:
            r["group"], r["block_type"] = p["group"], p["block_type"]
        after += W.bearing_cut(recs, tied)
    kb = {(r["wall_id"], r["k"]): r for r in before}
    assert set(kb) == {(r["wall_id"], r["k"]) for r in after}, "level population changed"
    for a in after:                     # conservation per level: gross = cuts + held + net
        b = kb[(a["wall_id"], a["k"])]
        assert abs(a["gross_m"] - b["gross_m"]) < 1e-9
        assert abs((a["cut_opening_m"] + a["cut_lintel_m"] + a["held_m"] + a["net_m"]) -
                   (b["cut_opening_m"] + b["cut_lintel_m"] + b["held_m"] + b["net_m"])) < 1e-5, (a, b)
        a["t355_net_m"], a["t355_held_m"] = b["net_m"], b["held_m"]
    after.sort(key=lambda r: (r["floor"], r["wall_id"], r["k"]))
    return before, after, led


def s86_candidates():
    """S8.6 lintel concrete rows as cross-check candidates by floor, width (+-10 mm) and wall thickness. A candidate
    is NOT a binding (the band ids of S8.6 predate register v2): shown beside, never used for a quantity."""
    cen = {r["OPENING_ID"]: r for r in rd(RES / "alsenan_lintels_s8_6/01_OPENING_CENSUS.csv")}
    qto = {r["OPENING_ID"]: r for r in rd(RES / "alsenan_lintels_s8_6/06_LINTEL_CONCRETE_QTO.csv")}
    hosts = {r["ID"]: r for r in rd(RES / "agents_t175/T175_OPENING_HOSTS.csv")}
    out = {}
    for oid, h in hosts.items():
        try:
            w, t = float(h["WIDTH_M"]), float(h["WALL_T_M"])
        except ValueError:
            continue
        c = [o for o, r in cen.items() if r["FLOOR"] == h["FLOOR"] and r["WIDTH_MM"] and r["WALL_THICKNESS_MM"]
             and abs(float(r["WIDTH_MM"]) / 1000 - w) <= 0.010 + 1e-9 and abs(float(r["WALL_THICKNESS_MM"]) / 1000 - t) < 1e-6
             and o in qto]
        out[oid] = [(o, qto[o]["LANE"], qto[o]["ROW"], round(float(qto[o]["BEARING_START_MM"]) / 1000, 4),
                     round(float(qto[o]["BEARING_END_MM"]) / 1000, 4)) for o in sorted(c)]
    return out


def bearings(black_after, white_levels):
    """per opening with a lintel at a mesh level: cut (jambs tied) or held, with the stations and S8.6 candidates."""
    cand = s86_candidates()
    per = defaultdict(lambda: {"levels": [], "cut_m": 0.0})
    for r in black_after + white_levels:
        for c, L, w in r["held"]:
            if c == "LINTEL_BEARING":
                k = (w.split(":")[0], r["wall_id"], "WHITE" if "family" in r else "BLACK", r.get("family", "-"))
                per[k]["levels"].append(r["level_m"])
                per[k]["cut_m"] += 0.0
                per[k].setdefault("held_m", 0.0)
                per[k]["held_m"] += L
    for r in black_after:
        for oid, L in r["bearing_ops"]:
            k = (oid, r["wall_id"], "BLACK", "-")
            per[k]["levels"].append(r["level_m"])
            per[k]["cut_m"] += L
    for r in white_levels:
        for oid, L in r.get("bearing_ops", []):
            k = (oid, r["wall_id"], "WHITE", r["family"])
            per[k]["levels"].append(r["level_m"])
            per[k]["cut_m"] += L
    rows = []
    for (oid, wid, bt, fam), v in sorted(per.items()):
        c = cand.get(oid, [])
        rows.append({"opening": oid, "wall_id": wid, "block_type": bt, "family": fam,
                     "status": "CUT (R-T362-3, jambs tied)" if oid in STATIONS else "HELD (jambs not tied)",
                     "stations": STATION_WHY.get(oid, ""),
                     "printed_min_each_end_m": 0.40, "lintel_levels_m": " ".join(f"{z:.3f}" for z in v["levels"]),
                     "bearing_cut_m": round(v["cut_m"], 6), "bearing_held_m": round(v.get("held_m", 0.0), 6),
                     "per_level_cut_m": round(v["cut_m"] / len(v["levels"]), 6),
                     "below_two_minimums": "YES" if 0 < v["cut_m"] / len(v["levels"]) < 0.80 - 1e-6 else "",
                     "s86_candidates": "; ".join(f"{o} {lane} {row} {a:.4f}/{b:.4f}" for o, lane, row, a, b in c),
                     "s86_binding": ("NONE" if not c else "ONE CANDIDATE (not binding)" if len(c) == 1 else
                                     f"AMBIGUOUS ({len(c)})")})
    return rows


def summarise(wl, before, after):
    def fam_tot(fam):
        L = [r for r in wl["levels"] if r["family"] == fam]
        T = [t for t in wl["ties"] if t["family"] == fam]
        by = defaultdict(lambda: {"certain_net_m": 0.0, "band_held_m": 0.0, "other_held_m": 0.0, "levels": 0,
                                  "ties": 0, "tie_band_held": 0, "junctions": 0, "junctions_held": 0})
        for r in L:
            a = by[r["floor"]]
            a["certain_net_m"] += r["certain_net_m"]
            a["band_held_m"] += r["band_held_m"]
            a["other_held_m"] += r["held_m"]
            a["levels"] += 1
        for t in T:
            a = by[t["floor"]]
            if t["state"] == "MEASURED":
                a["ties"] += t["ties"]
                a["tie_band_held"] += t["band_held"]
                a["junctions"] += 1
            else:
                a["junctions_held"] += 1
        r4 = {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in sorted(by.items())}
        tot = {kk: round(sum(v[kk] for v in by.values()), 4) for kk in
               ("certain_net_m", "band_held_m", "other_held_m", "levels", "ties", "tie_band_held", "junctions",
                "junctions_held")}
        return {"by_floor": r4, "total": tot, "band_stable_levels": sum(1 for r in L if r["band"] == "STABLE"),
                "band_unstable_levels": sum(1 for r in L if r["band"] != "STABLE")}

    def bt(recs):
        return {"net_m": round(sum(r["net_m"] for r in recs), 4), "held_m": round(sum(r["held_m"] for r in recs), 4),
                "cut_lintel_m": round(sum(r["cut_lintel_m"] for r in recs), 4), "levels": len(recs)}

    causes_b = defaultdict(float)
    causes_a = defaultdict(float)
    for r in before:
        for c, L, _ in r["held"]:
            causes_b[c] += L
    for r in after:
        for c, L, _ in r["held"]:
            causes_a[c] += L
    hc = defaultdict(float)
    for r in wl["levels"]:
        for c, L, _ in r["held"]:
            hc[f"{r['family']}|{c}"] += L
    return {
        "schema": W.SCHEMA,
        "families": {f.name: {"block_h": f.block_h, "source": f.source} for f in FAMILIES},
        "band": {"bed_lo": BAND.bed_lo, "bed_hi": BAND.bed_hi, "first_lo": BAND.first_lo, "first_hi": BAND.first_hi,
                 "source": BAND.source},
        "white_status": "CONDITIONAL per family; NOT CHOSEN (no drawing, specification or owner answer names the "
                        "face; T-143 / T-176 report both); HELD for release",
        "white_family_A": fam_tot("A"),
        "white_family_B": fam_tot("B"),
        "white_walls": len(wl["walls"]),
        "white_walls_with_levels": {f.name: sum(1 for w in wl["walls"] if w[f"{f.name}_levels"]) for f in FAMILIES},
        "white_other_held_by_cause_m": {k: round(v, 4) for k, v in sorted(hc.items())},
        "black_t355": bt(before),
        "black_restated_r_t362_3": bt(after),
        "black_held_by_cause_t355_m": {k: round(v, 4) for k, v in sorted(causes_b.items())},
        "black_held_by_cause_restated_m": {k: round(v, 4) for k, v in sorted(causes_a.items())},
        "unknown_walls": sorted(UNKNOWN_WALLS),
        "villa_mesh_conditional_m": {
            f"black restated + white family {f}": {
                "net_m": round(bt(after)["net_m"] + fam_tot(f)["total"]["certain_net_m"], 4),
                "held_m": round(bt(after)["held_m"] + fam_tot(f)["total"]["band_held_m"] +
                                fam_tot(f)["total"]["other_held_m"], 4),
                "plus_unknown_walls": "7 walls HELD by name (UNKNOWN_WALLS_T362.csv), blank, never 0"}
            for f in ("A", "B")},
        "villa_ties_conditional_pcs": {
            f"black + white family {f}": {
                "ties": sum(r["ties"] for r in BLACK_TIES if r["state"] == "MEASURED") + fam_tot(f)["total"]["ties"],
                "junctions_held": sum(1 for r in BLACK_TIES if r["state"] != "MEASURED") +
                fam_tot(f)["total"]["junctions_held"]} for f in ("A", "B")},
        "freelancer": "no mesh-strip or sharmat line in the freelancer workbooks (T-317 / T-355 census): NOT COMPARED",
    }


def _f(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "YES" if v else ""
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, list):
        return " | ".join(f"{c} {L:.4f} ({w})" for c, L, w in v) if v and len(v[0]) == 3 else \
            " | ".join(f"{a} {b:.4f}" for a, b in v)
    return str(v)


def outputs():
    global STATIONS, STATION_WHY
    STATIONS, STATION_WHY = stations()
    wl = white_ledger()
    before, after, led = black_restated()
    global BLACK_TIES
    BLACK_TIES = [r for r in led["ties"] if r["block_type"] == "BLACK"]
    S = summarise(wl, before, after)
    reg = {r["wall_id"]: r for r in rd(RES / "agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv")}
    unk = [{"wall_id": k, "block_type": reg[k]["block_type"], "t_m": reg[k]["t_m"], "length_m": reg[k]["length_m"],
            "register_state": reg[k]["state_v4"].strip() or reg[k]["class_v4"], "mesh": "HELD", "sharmat": "HELD",
            "cause": v} for k, v in sorted(UNKNOWN_WALLS.items())]
    files = {
        "WHITE_MESH_LEVELS_T362.csv": (["wall_id", "floor", "group", "family", "k", "course_below", "level_lo_m",
                                        "level_hi_m", "course_above_h_m", "partial_above", "gross_m", "cut_opening_m",
                                        "cut_lintel_m", "bearing_cut_m", "certain_net_m", "band_held_m", "held_m",
                                        "band", "held"], wl["levels"]),
        "WHITE_MESH_BY_WALL_T362.csv": (["wall_id", "floor", "group", "t_m", "block_run_m", "A_levels", "A_state",
                                         "A_certain_net_m", "A_band_held_m", "A_other_held_m", "B_levels", "B_state",
                                         "B_certain_net_m", "B_band_held_m", "B_other_held_m", "notes"], wl["walls"]),
        "WHITE_SHARMAT_T362.csv": (["wall_id", "floor", "group", "family", "column_at", "face", "block_segment_m", "top",
                                    "state", "ties", "band_held", "held", "note"], wl["ties"]),
        "LINTEL_BEARINGS_T362.csv": (["opening", "wall_id", "block_type", "family", "status", "stations",
                                      "printed_min_each_end_m", "lintel_levels_m", "per_level_cut_m", "bearing_cut_m",
                                      "bearing_held_m", "below_two_minimums", "s86_candidates", "s86_binding"],
                                     bearings(after, wl["levels"])),
        "BLACK_RESTATED_T362.csv": (["wall_id", "floor", "group", "k", "level_m", "gross_m", "cut_opening_m",
                                     "cut_lintel_m", "bearing_cut_m", "held_m", "net_m", "t355_held_m", "t355_net_m",
                                     "held"], [r for r in after if r["bearing_cut_m"] > 0 or
                                               abs(r["net_m"] - r["t355_net_m"]) > 1e-9 or
                                               abs(r["held_m"] - r["t355_held_m"]) > 1e-9]),
        "UNKNOWN_WALLS_T362.csv": (["wall_id", "block_type", "t_m", "length_m", "register_state", "mesh", "sharmat",
                                    "cause"], unk),
    }
    txt = {}
    for name, (cols, rows) in files.items():
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: _f(r.get(k)) for k in cols})
        txt[name] = buf.getvalue()
    txt["summary.json"] = json.dumps(S, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    return txt, S, wl, before, after


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    txt, S, *_ = outputs()
    if a.write:
        for n, t in txt.items():
            (HERE / n).write_text(t, encoding="utf-8")
    if a.check:
        bad = [n for n, t in txt.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        if bad:
            raise SystemExit(f"stale: {bad}")
        print("check: every output reproduced")
    print(json.dumps({k: S[k] for k in ("white_family_A", "white_family_B", "black_t355", "black_restated_r_t362_3",
                                         "black_held_by_cause_restated_m", "white_walls_with_levels")}, indent=1))
    return S


if __name__ == "__main__":
    main()
