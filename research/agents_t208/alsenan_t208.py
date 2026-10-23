"""T-208 development-villa ledger: the floor-area reference line (key FLOOR.INTERNAL, freelancer 'total floors')
made comparable. Reads only committed files: ALSENAN_T208_INPUT.json (extracted from the pinned released run
V29_ROUTEG_NO_PROFILE), T208_BOUNDARY_CONFIRMATIONS.json and the freelancer's normalised rows
(tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json). Writes SETS_T208.csv, RECONCILIATION_T208.csv, summary.json.

    python3 -I research/agents_t208/alsenan_t208.py            # write the three files
    python3 -I research/agents_t208/alsenan_t208.py --check    # exit 1 when the committed files do not reproduce

The pairing of engine spaces with the freelancer's rows below is this project's data (by name, floor and area; his
rows carry no dimensions), never engine logic. Every quantity keeps its status; nothing here is released.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import review_sets as RS                                                # noqa: E402

KEY_ITEMS = ("FIN.FLOOR.PORCELAIN [m2]", "FIN.FLOOR.WET_TILE [m2]")
REF_TOTAL = "FIN:الغلاف:15"                      # 'total floors' 409.58 m2 = dry 337.57 + wet 72.01 (his tiles sheet)
SH = "FIN:سيراميك:"

# (group id, floor, engine room ids (line location room_id), freelancer row numbers on his tiles sheet, cause, verdict)
PAIRS = [
    ("GF-OPEN", "GF", ["GF-RC99C2A", "GF-RC06FED"] + [f"GF-STRIP-OP-{n:03d}" for n in (1, 3, 5, 7, 8, 9, 10, 11, 12,
                                                                                    13, 21)],
     [13, 15], "open space + its doorway strips vs his reception + dining + entrance hall; scope items S1 / S2 below "
     "are taken out first (like for like); the pantry 13.500 is inside both", "AGREE within 0.2 %"),
    ("GF-DIWANIYA", "GF", ["GF-R7512EA"], [16], "printed 400 x 630 less the R1.10 corner (T-153)", "ENGINE_RIGHT (+0.4 %)"),
    ("GF-MASTER", "GF", ["GF-R75FBAE"], [14], "drawn room face", "AGREE (-0.7 %)"),
    ("GF-DRIVER", "GF", ["GF-R51E127"], [17], "printed 1.75 x 4.50", "AGREE"),
    ("GF-KITCHEN", "GF", ["GF-RA3AD49"], [48], "printed 300 x 270 + 105 x 150 less two piers (T-074); V2.9 floors it as "
     "porcelain (dry), he as wet: same area, the class differs (Q-30 A: a kitchen is wet like a bathroom)",
     "area ENGINE_RIGHT (+0.8 %); class FREELANCER_RIGHT vs V2.9"),
    ("GF-BATHS", "GF", ["GF-RD6F891", "GF-RB62B55", "GF-RF38DAF", "GF-RB28769", "GF-RDF7D28", "GF-RFAD3C4"],
     [44, 45, 46, 47, 49, 50], "six W.C. faces (T-074 per room)", "AGREE (+0.6 %)"),
    ("GF-HANDWASH", "GF", ["COND:GF-RDBD4F9", "COND:GF-R8496F0", "COND:GF-RD36087"], [42, 43, 51],
     "the three review sets bound WET by Q-06 A (this task); wet tile 9.348 + the two doorless passage strips 0.330 "
     "(porcelain, PROVISIONAL, UP-THR-001 as the engine applies it)", "AGREE on class; area see SETS_T208.csv"),
    ("1F-LIVING", "1F", ["1F-R78C367"], [21], "engine living 44.869 = 33.594 porcelain + arrival landing 4.865 (Q-66 B) "
     "+ held strips 0.520 + stair footprint 5.890 (T-153 / T-116 / T-122); scope item S4 taken out first",
     "AGREE after S4 (+0.05 %)"),
    ("1F-BEDROOMS", "1F", ["1F-RB72F22", "1F-R3CFCFD", "1F-RED0D19", "1F-R0E919A"], [22, 23, 24, 25],
     "19.050 / 19.017 (curved east room, PROVISIONAL) / 18.215 / 16.340 vs 19.00 / 19.46 / 18.25 / 17.29: the 380 x 430 "
     "room's passage and the curved edge (T-086 / T-153)", "UNRESOLVED (-1.9 %), as T-153"),
    ("1F-STRIPS", "1F", [f"1F-STRIP-OP-{n:03d}" for n in (5, 6, 7, 11, 20)], [],
     "doorway strips of dry doors: engine lines, no freelancer row", "RULE_DIFFERENCE (strip measured apart)"),
    ("1F-WET", "1F", ["1F-R26FA0D", "1F-R8BDA49", "1F-R48AA46", "1F-R48CDA5", "1F-RED23B8", "1F-R52AC05"],
     [55, 56, 57, 58, 59, 60], "laundry + five baths (T-074)", "AGREE (+0.8 %)"),
    ("2F-MAID", "2F", ["2F-R1DB2D2"], [28], "drawn room face 19.350", "UNRESOLVED (-1.2 %)"),
    ("2F-STRIPS", "2F", [f"2F-STRIP-OP-{n:03d}" for n in (1, 2, 7)], [], "doorway strips: engine lines, no freelancer row",
     "RULE_DIFFERENCE (strip measured apart)"),
    ("2F-WC", "2F", ["2F-RE83BED"], [63], "W.C. face", "AGREE (-1.2 %)"),
    ("2F-CORRIDOR", "2F", [], [29], "scope item S3: his corridor 7.70 is inside the engine's 2F stair room (landings "
     "bound 11.725, FIN.MARBLE.LANDING HELD 0 .. 11.725): T-129 2.500 porcelain + 4.875 arrival marble (Q-70 A)",
     "SCOPE (not in the floor key on the engine side)"),
]

# scope items: physical floor that one side keeps in this key and the other side in another line (m2, + = engine only)
SCOPE = [
    ("S1", "GF", "garden band 1.30 x 10.82 (EXTERNAL 9.101 + merged cell 4.885): he floors it in his reception row; the "
     "engine keeps it outside the floor key (HELD CONFLICT, T-153 P-2, defect B9)", "freelancer", None),
    ("S2", "GF", "round-stair treads inside the open space (STAIR_FLIGHTS of GF-RC99C2A): he floors them in his "
     "reception row; the engine bills them as FIN.MARBLE.TREAD", "freelancer", None),
    ("S3", "2F", "2F corridor (his row 29): engine side inside the 2F stair room landing range, not in this key",
     "freelancer", None),
    ("S4", "1F", "1F stair footprint inside the engine's living porcelain (T-116 / T-122 5.890): his stair sheet holds "
     "it", "engine", 5.890),
]


def _load():
    inp = json.loads((HERE / "ALSENAN_T208_INPUT.json").read_text(encoding="utf-8"))
    conf = json.loads((HERE / "T208_BOUNDARY_CONFIRMATIONS.json").read_text(encoding="utf-8"))["confirmations"]
    ref = json.loads((ROOT / "tests" / "alsenan" / "registers_b1" / "BENCHMARK_NORMALISED.json")
                     .read_text(encoding="utf-8"))
    return inp, conf, {r["id"]: r for r in ref["records"]}


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


def build():
    inp, conf, ref = _load()
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": inp["conditional_sets"]}}}
    doc = RS.bind_run(rr, inp["rooms"], RS.ANSWERED_RULES, conf)
    line = RS.floor_line(inp["lines"], doc, KEY_ITEMS)
    held_without = RS.floor_line(inp["lines"], RS.bind_run(rr, inp["rooms"], RS.ANSWERED_RULES, None), KEY_ITEMS)
    key_codes = {i.rsplit(" [", 1)[0] for i in KEY_ITEMS}
    eng = {}
    for ln in inp["lines"]:
        if ln["item_code"] in key_codes:
            eng[ln["room_id"]] = eng.get(ln["room_id"], 0.0) + float(ln["measured_net"])
    bound = {b["subject"]: sum(float((b["quantities"] or {}).get(i, 0.0)) for i in KEY_ITEMS) for b in doc["bindings"]}
    for s, q in bound.items():
        eng["COND:" + s] = q
    facts = inp["floor_area_facts"]
    scope_val = {"S1": facts["GF_garden_external_m2"] + facts["GF_garden_merged_cell_m2"],
                 "S2": facts["GF_open_space_stair_flights_m2"], "S3": ref[SH + "29"]["qty"]}
    used, rows = set(), []
    for gid, fl, eids, fids, cause, verdict in PAIRS:
        e = sum(eng[i] for i in eids) if eids else 0.0
        used.update(eids)
        f = sum(float(ref[SH + str(n)]["qty"]) for n in fids)
        adj = 0.0
        if gid == "GF-OPEN":
            adj = -(scope_val["S1"] + scope_val["S2"])          # his reception row holds S1 + S2
        if gid == "1F-LIVING":
            adj = 5.890                                          # S4: engine living holds the stair footprint
        rows.append({"group": gid, "floor": fl, "engine_m2": _r(e), "freelancer_m2": _r(f),
                     "diff_raw_m2": _r(e - f), "scope_adjustment_m2": _r(adj),
                     "diff_like_for_like_m2": None if gid == "2F-CORRIDOR" else _r(e - f - adj),
                     "engine_ids": " ".join(eids), "freelancer_rows": " ".join(str(n) for n in fids),
                     "cause": cause, "verdict_proposal": verdict})
    missing = sorted(set(eng) - used)
    if missing:
        raise SystemExit(f"engine floor lines not paired: {missing}")
    e_tot = sum(r["engine_m2"] for r in rows)
    f_tot = float(ref[REF_TOTAL]["qty"])
    f_sum = sum(r["freelancer_m2"] for r in rows)
    scope_sum = -(scope_val["S1"] + scope_val["S2"] + scope_val["S3"]) + 5.890
    residual = (line["total_m2"] - f_tot) - scope_sum
    sets = []
    for b in doc["bindings"]:
        q = b["quantities"] or {}
        sets.append({"set_id": b["set_id"], "subject": b["subject"], "status": b["status"],
                     "scenario": b["scenario"], "rule": b["rule_id"], "reason": b["reason"],
                     "wet_tile_m2": _r(q.get("FIN.FLOOR.WET_TILE [m2]"), 6),
                     "strip_porcelain_m2": _r(q.get("FIN.FLOOR.PORCELAIN [m2]", 0.0), 6),
                     "membrane_floor_m2": _r(q.get("FIN.WP.FLOOR [m2]"), 6),
                     "membrane_upturn_m2": _r(q.get("FIN.WP.WALL_UPTURN [m2]"), 6),
                     "boundary_confirmation": "yes" if b.get("boundary_confirmation") else "not needed",
                     "fixtures": " ".join(b["profile"]["fixture_kinds"]), "issues": " ".join(b["profile"]["issue_codes"])})
    wet_rel = line["released_by_item"]["FIN.FLOOR.WET_TILE [m2]"]
    wet_all = wet_rel + line["assumed_by_item"]["FIN.FLOOR.WET_TILE [m2]"]
    f_wet = sum(float(ref[SH + str(n)]["qty"]) for n in (42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 55, 56, 57, 58, 59,
                                                           60, 63))
    summary = {
        "task": "T-208", "key": "FLOOR.INTERNAL", "reference_id": REF_TOTAL, "reference_m2": f_tot,
        "freelancer_rows_sum_m2": _r(f_sum, 2),
        "review_sets": {"count": len(doc["bindings"]), "bound": sum(b["status"] == RS.ASSUMED for b in doc["bindings"]),
                        "held": [b["set_id"] for b in doc["bindings"] if b["status"] != RS.ASSUMED],
                        "rule": "Q-06 A", "ignored_non_floor_sets": [s["set_id"] for s in doc["ignored_sets"]]},
        "engine_released_m2": _r(line["released_m2"], 4),
        "engine_assumed_owner_approved_m2": _r(line["assumed_owner_approved_m2"], 4),
        "engine_total_m2": _r(line["total_m2"], 4),
        "without_boundary_confirmation_total_m2": held_without["total_m2"],
        "raw": {"diff_m2": _r(line["total_m2"] - f_tot), "diff_pct": _r(100 * (line["total_m2"] - f_tot) / f_tot, 2),
                "wape_pct": _r(100 * abs(line["total_m2"] - f_tot) / f_tot, 2)},
        "scope_items_m2": {"S1_garden_band": _r(scope_val["S1"]), "S2_GF_round_stair_treads": _r(scope_val["S2"]),
                           "S3_2F_corridor": _r(scope_val["S3"]), "S4_1F_stair_footprint": 5.890,
                           "net": _r(scope_sum)},
        "like_for_like": {"diff_m2": _r(residual), "diff_pct": _r(100 * residual / (f_tot - scope_val["S1"] -
                                                                                     scope_val["S2"] - scope_val["S3"]), 2)},
        "engine_rows_sum_check_m2": _r(e_tot - line["total_m2"], 6),
        "wet": {"engine_released_m2": _r(wet_rel), "engine_with_sets_m2": _r(wet_all), "freelancer_m2": _r(f_wet, 2),
                "diff_m2": _r(wet_all - f_wet), "kitchen_in_engine_porcelain_m2": _r(eng["GF-RA3AD49"]),
                "diff_after_kitchen_class_m2": _r(wet_all + eng["GF-RA3AD49"] - f_wet)},
    }
    return sets, rows, summary


def _csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def outputs():
    sets, rows, summary = build()
    return {"SETS_T208.csv": _csv(sets), "RECONCILIATION_T208.csv": _csv(rows),
            "summary.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    outs = outputs()
    if "--check" in argv:
        bad = [n for n, t in outs.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        print("T-208 ledger:", "reproduces" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in outs.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(outs["summary.json"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
