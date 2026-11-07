"""T-607 development-villa build (research, unwired): the ST-01 shared residual of steps (T-584/stair-steps lm / nr) and
the nosing census (T-598/nosing@V9): his 63 pieces vs the governing 56 risers, settled once by edge id.

    .work/venv/bin/python -I research/agents_t607/t607_alsenan.py [--check]

Reads only repository files (sha256-pinned): T607_DRAWN.json (this task's own read of the architectural DXF and the ST
sheets by handle, t607_extract.py), the merged T-412 flight / nosing tables, the T-584 step-line ids (STEP_LINE_OF, copied
from its merged table) and his marble-sheet cells as numbers through the merged T-577 reader (no workbook text is written). Writes
out/T607_SHARED_RESIDUAL.json; --check rebuilds it byte-identical. Sign: his - ours (as T-578 / T-598 / statement V9)."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t577"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t607_rules as R  # noqa: E402
import t577_alsenan as T577  # noqa: E402  (merged reader of his cells, read only)

DRAWN = "research/agents_t607/T607_DRAWN.json"
FLIGHTS = "research/agents_t412/FLIGHT_TABLE_T412.csv"
NOSING = "research/agents_t412/NOSING_TABLE_T412.csv"
PINS = {FLIGHTS: "20703ee293f0b39c", NOSING: "9da81b33ec1b5f40", DRAWN: "0906198e74db2cde",
        "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json": "752c9f4e0c4546d0"}
OUT = HERE / "out" / "T607_SHARED_RESIDUAL.json"
STOREY_OF = {"MS1-L": "GF->1F", "MS1-T": "GF->1F", "MS1-U": "GF->1F", "MS2-L": "1F->2F", "MS2-TR": "1F->2F",
             "MS2-U": "1F->2F", "D1": "D1 lobby"}
# printed levels (own read: T607_DRAWN levels_printed holds their handles; T-184 / T-425 MERGED storey bounds)
STOREYS = [("D1 lobby", "0.30", "1.00"), ("GF->1F", "1.00", "5.50"), ("1F->2F", "5.50", "9.70")]
# step-line ownership of the ST-01 edges (R-T588-1 (d), T-588 MERGED; lines from the merged T-584 table)
STEP_LINE_OF = {"MS1-L": "L-d4d764ae7bb07b474b6f", "MS1-T": "L-e085c168dee5fb19a7fb", "MS1-U": "L-0aa47300a16de572c967",
                "MS2-L": "L-23651ecfef77992ec8d4", "MS2-U": "L-60fc97c4306696c74c38", "D1": "L-f20f8544a42807c0cfcf"}
SECOND_STEP_LINES = ("L-1e88ac0d4ba0b4e8a950",)    # MS2-L read again (T-584 SECOND_READING): claims no edge


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if h is not None and _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def S(x):
    return None if x is None else str(x)


def his():
    c = T577.his_cells()
    q = lambda k: T577._q(c[k])     # noqa: E731
    out = {"ST-01": {"nr": int(q("MRB.B23")), "piece_m": q("MRB.C23"), "cell": "MRB.B23 x MRB.C23"},
           "ST-02": {"nr": int(q("MRB.B30")), "piece_m": q("MRB.C30"), "cell": "MRB.B30 x MRB.C30"},
           "ST-03": {"nr": int(q("MRB.B16")), "piece_m": q("MRB.C16"), "cell": "MRB.B16 x MRB.C16"},
           "ST-01 side pieces": {"nr": int(q("MRB.B26")), "cell": "MRB.B26"}}
    return out


def census():
    fl = list(csv.DictReader((ROOT / FLIGHTS).open(encoding="utf-8")))
    ed = [r for r in csv.DictReader((ROOT / NOSING).open(encoding="utf-8")) if r["stair"] == "ST-01"]
    risers = {}
    for r in fl:
        if r["stair"] == "ST-01":
            risers[STOREY_OF[r["flight"]]] = risers.get(STOREY_OF[r["flight"]], 0) + int(r["risers"])
    if len(ed) != sum(risers.values()):
        raise R.RuleError(f"census edges {len(ed)} != governing risers {sum(risers.values())}")
    return fl, ed, risers


def edge_table(ed):
    """R-T607-1 (a): every ST-01 edge with the one line that prices it (MS1-L N10 fronts the first winder: MS1-T line)"""
    edges, step_rows, nosing_rows = {}, {}, {}
    for r in ed:
        k = r["kind"]
        held = r["status"] == "HELD"
        edges[r["eid"]] = {"kind": k, "held": held,
                           "value": None if held or not r["qty_lm"] else Decimal(r["qty_lm"]), "flight": r["flight"]}
        if k in ("TREAD", "WINDER"):
            fl = "MS1-T" if k == "WINDER" else r["flight"]
            step_rows.setdefault(STEP_LINE_OF[fl], []).append(r["eid"])
        else:
            nosing_rows.setdefault(f"B7-05:{r['eid']}", []).append(r["eid"])
    table = R.claims(edges, step_rows, nosing_rows, {ln: [] for ln in SECOND_STEP_LINES})
    rows = [{"edge": e, "kind": edges[e]["kind"], "flight": edges[e]["flight"], "status": "HELD" if edges[e]["held"]
             else "VALUED", "lm": S(edges[e]["value"]), "priced_by": t["line"], "family": t["family"], "claims": 1}
            for e, t in sorted(table.items())]
    per_line = Counter(t["line"] for t in table.values())
    return rows, {k: per_line[k] for k in sorted(per_line)}, edges


def sweep(drawn):
    cls = Counter()
    groups = {}
    for plan, rows in drawn["plans"].items():
        for r in rows:
            cls[r["cls"]] += 1
            if r["cls"] == "SECOND_READING":
                groups.setdefault(f"{plan}:{r['flight']}", {}).setdefault(r["edge"], []).append(
                    {"handle": r["handle"], "layer": r["layer"], "of": r["of_handle"], "residual_mm": r["residual_mm"]})
    return cls, groups


def sources(groups, drawn):
    """the candidate pieces a counter could add beyond the governing 56 (R-T607-1 (c)), with their kinds"""
    east = groups["GF:MS1-U"]          # 7 front + face pairs above the GF cut over D1 (MS1-U N05 .. N11)
    fan = groups["1F:MS1-T"]           # the GF turn fan seen below the 1F cut (3 radials; BE4 / BE5 = the landing edge)
    west = groups["2F:MS2-L"]          # MS2-L seen below the 2F cut (12 positions, 11 solid fronts)
    solid_west = sum(1 for v in west.values() if any(x["layer"] == "5" for x in v))
    radials = sum(1 for e in fan if e != "ST01-MS1T-N05")
    if len(east) != 7 or radials != 3 or len(west) != 12 or solid_west != 11:
        raise R.RuleError(f"second-reading groups not as read: east {len(east)}, fan {radials}, west {len(west)}")
    st5 = drawn["structural"]["ST_P5"]
    if st5["diagonal_vs_arch_2F20_mm"] != 0.0 or not st5["diagonal_len_equal_arch"]:
        raise R.RuleError("ST p.5 diagonal not at the arch 2F20 position")
    src = {
        "GF east lane, 7 pairs above the cut (= MS1-U N05..N11)": [(7, "SECOND_READING")],
        "1F fan below the cut (= MS1-T radials, + landing edge)": [(3, "SECOND_READING"), (4, "SECOND_READING")],
        "2F west lane below the cut (= MS2-L)": [(11, "SECOND_READING"), (12, "SECOND_READING")],
        "Q-ST-11 2F diagonal riser (arch 2F1F / 2F20 + ST p.5 648)": [(1, "PHYSICAL_OPEN")],
        "GF turn as the arch plans draw it (4 risers; T-434 REJECTED)": [(-1, "REJECTED_READING")],
        "GF straight run as ST p.4 draws it (12 + 4; T-434 REJECTED)": [(1, "REJECTED_READING")],
        "floor edges MS1-U / MS2-U left out (on no plan; T-598 governed by A-A)": [(-1, "REJECTED_READING"),
                                                                                   (-2, "REJECTED_READING")],
    }
    return src, {"east": sorted(east), "fan": sorted(fan), "west": sorted(west), "solid_west": solid_west}


def build():
    pins()
    drawn = json.loads((ROOT / DRAWN).read_text())
    fl, ed, risers = census()
    H = his()
    gov = sum(risers.values())
    rows, per_line, edges = edge_table(ed)
    cls, groups = sweep(drawn)
    src, sets = sources(groups, drawn)
    extra = H["ST-01"]["nr"] - gov
    combos = R.reproductions(extra, src)
    adm = [c for c in combos if c["admissible"]]
    est = R.storey_estimate(STOREYS, H["ST-01"]["nr"])
    if not est:
        raise R.RuleError("no storey estimate reproduces his count")
    estm = [{"mechanism": "STOREY_ESTIMATE", "physical": False, "admissible": True,
             "riser_mm": [S(e["lo_mm"]), S(e["hi_mm"])], "per_storey": e["per_storey"]} for e in est]
    # the same estimate on his other two stairs (consistency of the mechanism, reported, never used to choose)
    other = {"ST-02 (+1.00 -> +5.50, drawn 28)": R.storey_estimate([("ST-02", "1.00", "5.50")], 28),
             "ST-03 E1 (+0.15 -> +1.00, drawn 5)": R.storey_estimate([("E1", "0.15", "1.00")], 5)}
    x, verdict, why = R.extra_verdict(H["ST-01"]["nr"], gov, cls, adm + estm)
    if x != extra:
        raise R.RuleError("extra mismatch")
    w = H["ST-01"]["piece_m"]
    shared = R.shared_cause("C-T607-1", H["ST-01"]["cell"], {"T-584/stair-steps-lm": "lm", "T-584/stair-steps-nr": "nr",
                                                             "T-598/nosing@V9 lm": "lm", "T-598/nosing@V9 nr": "nr"},
                               extra, w)
    n_once, lm_once = R.total_across_lines([("C-T607-1", extra, extra * w), ("C-T607-1", extra, extra * w)])
    per_storey_est = {n: c for n, c in est[0]["per_storey"]}
    causes = [
        {"id": "C-T607-1", "his_cell": H["ST-01"]["cell"], "nr": extra, "lm_his_basis": S(extra * w),
         "edges_in_governing_count": 0,
         "named_readings": {
             "R1 SECOND_READING": {"pieces": 7, "edges_repeated": sets["east"],
                                   "drawing": "arch GF plan: 7 front + face pairs (layer 2, above the cut) in the east "
                                              "lane south of D1, coinciding after wall registration (<= 0.3 mm) with "
                                              "MS1-U fronts / faces on the 1F plan; same 0.300 rhythm as the 4 D1 "
                                              "fronts, so the lane reads as one 11-step flight"},
             "R2 STOREY_ESTIMATE": {"pieces_by_storey": {k: per_storey_est[k] - risers[k] for k in risers},
                                    "riser_mm": estm[0]["riser_mm"],
                                    "drawing": "printed levels +0.30 / +1.00 / +5.50 / +9.70 (handles in "
                                               "T607_DRAWN levels_printed); no edge exists for these pieces"}},
         "verdict": verdict, "why": why,
         "his_mechanism": "UNRESOLVED between R1 and R2 (his row has no breakdown; never chosen by fit, R-T434-1)"}]
    return {
        "schema": "T607_SHARED_RESIDUAL_V1", "rule": "R-T607-1", "sign": "his - ours", "task": "T-607",
        "pins": {k: (v or _sha(k)) for k, v in PINS.items()},
        "his": {k: {kk: S(vv) for kk, vv in v.items()} for k, v in H.items()},
        "governing": {"source": "section A-A (Q-46 A), T-434 / T-598 MERGED", "risers_by_storey": risers,
                      "total": gov, "edges": len(ed)},
        "structural_second_drawing": {s: {g: v["count"] for g, v in d.items() if isinstance(v, dict)}
                                      for s, d in drawn["structural"].items()},
        "sweep": {"classes": dict(sorted(cls.items())), "registration": drawn["registration"],
                  "second_reading_groups": {k: sorted(v) for k, v in sorted(groups.items())}},
        "shared_edge_table": rows, "edges_per_pricing_line": per_line,
        "reproductions": {"extra": extra, "second_reading_sets": combos, "admissible": len(adm),
                          "storey_estimate": estm, "storey_estimate_on_his_other_stairs":
                          {k: [{"riser_mm": [S(e["lo_mm"]), S(e["hi_mm"])]} for e in v] for k, v in other.items()}},
        "causes": causes,
        "shared": {"cause_id": shared["cause_id"], "his_cell": shared["his_cell"],
                   "per_line": {k: [S(v[0]), v[1]] for k, v in shared["per_line"].items()},
                   "total_once": [n_once, S(lm_once)], "refused": "summing C-T607-1 over the lines it feeds (16.8 lm / 14 nr)",
                   "also_feeds": "his MRB.B26 side pieces 63 = the same count (T-574/skirting-pieces ST-01 row, class "
                                 "RULE_DIFFERENCE 63 whole, UNIT): its count check text '52 .. 54 risers' (T-084) is "
                                 "superseded by the governing 56; the 7 there is C-T607-1, never a third residual"},
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=True, indent=1, sort_keys=True) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text() != out:
            raise SystemExit("T607 output differs from a rebuild")
        print("T607 check: REPRODUCED (byte-identical)")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
