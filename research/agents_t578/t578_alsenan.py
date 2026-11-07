"""T-578 development-villa build (research, unwired): HANDRAILS / BALUSTRADES / GUARDS and STAIR NOSING vs the
freelancer in lm (and nr where he counts pieces) on the candidate of record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 lines
for every code read here: arch_v3058 adds only FIN.WP.ROOF / FIN.WP.ROOF_UPTURN lines, T-507 / T-577).

    .work/venv/bin/python -I research/agents_t578/t578_alsenan.py [--check]

Reads only merged repository files (sha256-pinned): the V3.0.57 line index (T-507), his rows as numbers
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, finishes workbook: cover and marble sheets keyed by a hash of the
title, row and column labels checked by hash; no workbook text is written), the T-476 flight census (rail pieces) and
the T-412 nosing census (one nosing per riser). Nothing is re-measured from a drawing here: every figure names the
merged source that measured it; every inclined rail piece is recomputed from its plan and rise. Writes
out/T578_RAIL_NOSING_RECONCILE.json; --check rebuilds it byte-identical. No coordinate, no client name is written."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t578_rules as R  # noqa: E402

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
NOSING = "research/agents_t412/NOSING_TABLE_T412.csv"
CENSUS = "research/agents_t476/FLIGHT_CENSUS_T476.csv"
PINS = {LINE_INDEX: "fed5141ea31bfdd9", RAW: "752c9f4e0c4546d0", NOSING: "9da81b33ec1b5f40", CENSUS: "77f5fc462a71e253"}
OUT = HERE / "out" / "T578_RAIL_NOSING_RECONCILE.json"
D = R.D
Z = Decimal(0)


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def _h(s):
    return hashlib.sha256(str(s).replace("(", "").replace(")", "").replace(" ", "").strip().encode()).hexdigest()[:12]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def S(x):
    return None if x is None else str(x)


def B(b):
    return None if b is None else [S(b[0]), S(b[1])]


# ---- candidate lines ------------------------------------------------------------------------------------------------
RAIL_CODES = ("FIN.RAILING", "MET.RAILING.GUARD", "FIN.HANDRAIL")
FAMILY = {"FIN.RAILING": "BALUSTRADE", "MET.RAILING.GUARD": "GUARD", "FIN.HANDRAIL": "WALL_HANDRAIL"}


def index_lines():
    return {x["line_id"]: x for x in json.loads((ROOT / LINE_INDEX).read_text())["lines"]}


def rail_lines(L):
    xs = [x for x in L.values() if x["item_code"] in RAIL_CODES]
    by = {}
    for x in xs:
        if x["element_id"].startswith("RAIL:"):
            if x["element_id"] in by:
                raise R.RuleError(f"run {x['element_id']} on two lines")
            by[x["element_id"]] = x
    readers = [x for x in xs if not x["element_id"].startswith("RAIL:")]
    if any(x["item_code"] != "FIN.RAILING" or x["class"] != "EXCLUDED" for x in readers):
        raise R.RuleError("a per-flight reader line is not a retired FIN.RAILING line")
    return by, readers


# ---- rail pieces (T-476 census, every inclined piece recomputed) ---------------------------------------------------
def census():
    return list(csv.DictReader((ROOT / CENSUS).open(encoding="utf-8")))


# held / unknown runs: bound of what each would add (R-T578-1 (a) TURN chord; existence 0 .. drawn extent)
def held_bounds(cen):
    turn = {r["FLIGHT"]: r for r in cen if r["KIND"] == "TURN" and r["STATUS"] == "HELD"}
    return {
        "RAIL:RL-07:ST-01:T-MS1-N": (R.turn_bound(turn["T-MS1-N"]["PLAN_M"], turn["T-MS1-N"]["RISE_M"]),
                                     "rail drawn on both sides of the 5-winder turn (well band); profile over the 0.10 m "
                                     "well not drawn: at least the chord between its drawn ends, no upper bound"),
        "RAIL:RL-07:ST-01:T-MS2-LD": (R.turn_bound(turn["T-MS2-LD"]["PLAN_M"], turn["T-MS2-LD"]["RISE_M"]),
                                      "closing riser MS2-TR position against the turn not drawn: at least the chord"),
        "RAIL:RL-09": (R.existence_bound(None),
                       "ST-02 RS-C outer band: balustrade or string not established (designer RFI); band end differs "
                       "between the plans (259.1 vs 270.4 deg), so no upper bound is formed"),
        "RAIL:RL-11": (R.existence_bound(None),
                       "ST-03 E1 entrance stair (0.85 m rise): no guard drawn on either side; extent not printed"),
        "RAIL:ST-01b:GF east-lane band beyond D1": (R.existence_bound("1.875"),
                                                    "F-T476-1: 1.875 m (centreline plan) of layer-5 band beyond D1, no "
                                                    "level change printed across it: rail or drafting edge UNKNOWN"),
        "RAIL:RL-04": (R.existence_bound("7.500"),
                       "GF roof strip sea edge: plan band 6.127 vs elevation 7.500 between piers; railing / glazing / "
                       "parapet not established (T-164 / T-393): 0 .. the larger drawn extent"),
        "RAIL:RL-10": (R.existence_bound(None), "street fence X railing: length not printed (never scaled), T-164"),
    }


def rail_pieces(cen):
    out = []
    for r in cen:
        if r["FAMILY"] not in ("B7-09", "B13-08") or r["STATUS"] != "DRAWING-CONFIRMED":
            continue
        fam = "BALUSTRADE" if r["FAMILY"] == "B7-09" else "GUARD"
        rise = None if r["KIND"] == "HORIZONTAL" else r["RISE_M"]
        p = R.rail_piece(f"{r['STAIR']}:{r['FLIGHT']}:{r['SIDE']}", fam, r["KIND"], "DRAWING-CONFIRMED",
                         plan=r["PLAN_M"], rise=rise, billed=r["LENGTH_LM"], run=r["RUN"],
                         curved="per going" in r["SOURCE"])
        p["plan"] = D(r["PLAN_M"])
        p["rise"] = None if rise is None else D(rise)
        out.append(p)
    return out


def rail_table(L, cen, cells):
    by, readers = rail_lines(L)
    pcs = rail_pieces(cen)
    hb = held_bounds(cen)
    runs = []
    for eid, x in sorted(by.items(), key=lambda kv: kv[0]):
        fam = FAMILY[x["item_code"]]
        if x["class"] == "RELEASED":
            v = D(x["measured_net"])
            run = eid.split(":")[1]
            mine = [p for p in pcs if p["run"] == run]
            ext = not mine
            s = sum((p["value"] for p in mine), Z) if mine else None
            tol = None if s is None else v - s
            if tol is not None and abs(tol) > Decimal("0.0005"):
                raise R.RuleError(f"{eid}: line {v} vs census pieces {s}")
            runs.append({"run": eid, "line": x["line_id"], "code": x["item_code"], "family": fam,
                         "status": "DRAWING-CONFIRMED", "value": v, "bound": None,
                         "pieces": [{"id": p["id"], "kind": p["kind"], "plan": S(p["plan"]), "rise": S(p["rise"]),
                                     "installed": S(p["value"])} for p in mine],
                         "pieces_sum": S(s), "line_minus_pieces": S(tol),
                         "note": ("roof / terrace guard measured by T-164 (no flight piece)" if ext else
                                  "line rounding to 3 dp" if tol else "")})
        elif x["class"] == "HELD":
            b, why = hb[eid]
            runs.append({"run": eid, "line": x["line_id"], "code": x["item_code"], "family": fam, "status": "HELD",
                         "value": None, "bound": b, "why": why})
        elif x["class"] == "EXCLUDED":
            if x["item_code"] != "FIN.HANDRAIL":
                raise R.RuleError(f"{eid}: excluded run line not expected")
            runs.append({"run": eid, "line": x["line_id"], "code": x["item_code"], "family": fam,
                         "status": "NOT_APPLICABLE", "value": None, "bound": None,
                         "why": "UP-STAIR-013: no wall handrail drawn on any wall side of the 9 flights (T-476 scan)"})
    if set(hb) != {r["run"] for r in runs if r["status"] == "HELD"}:
        raise R.RuleError("a held run without a bound, or a bound without a held run")
    # census pieces must all have a valued home
    homes = {r["run"].split(":")[1] for r in runs if r["status"] == "DRAWING-CONFIRMED"}
    if any(p["run"] not in homes for p in pcs):
        raise R.RuleError("a confirmed census piece without a valued run line")

    val = lambda fam: sum((r["value"] for r in runs if r["family"] == fam and r["value"] is not None), Z)  # noqa
    ours = {f: val(f) for f in R.FAMILIES}
    ours_all = sum(ours.values(), Z)
    v = lambda e: next(r["value"] for r in runs if r["run"] == e)  # noqa
    # his side: one typed cover constant (no formula, no rows), label 'lm', row label pinned by hash
    if _h(cells["COV.A39"]) != "63aec2478957" or _h(cells["COV.F39"]) != "d2c6c24b21e4":
        raise R.RuleError("his railing row / its lm label not as expected")
    if cells["COV.B39.f"] is not None:
        raise R.RuleError("his railing figure is now a formula: re-read his rows")
    his = D(repr(cells["COV.B39"]))
    ext = v("RAIL:RL-01") + v("RAIL:RL-02") + v("RAIL:RL-03")
    rl05, rl06, rl07, rl08 = v("RAIL:RL-05"), v("RAIL:RL-06"), v("RAIL:RL-07"), v("RAIL:RL-08")
    held_b = [r for r in runs if r["status"] == "HELD"]
    hb7 = R.held_bound([{"status": "HELD", "bound": r["bound"]} for r in held_b if r["family"] == "BALUSTRADE"])
    hb13 = R.held_bound([{"status": "HELD", "bound": r["bound"]} for r in held_b if r["family"] == "GUARD"])
    residual = his - (rl05 + rl06)
    sloped05 = [p for p in pcs if p["run"] == "RL-05" and p["kind"] == "INCLINED"]
    pitch_excess = sum((p["value"] - p["plan"] for p in sloped05), Z)
    causes = [
        R.cause("roof / terrace guards RL-01 + RL-02 + RL-03 (B13-08): in our list only; his only railing row is "
                "labelled internal and none of his 885 rows names an external railing", -ext, "ENGINE_RIGHT", "SCOPE",
                "T-164 / T-199 (RL-02 + RL-03 Checker VERIFIED 12.888; RL-01 DRAWING-CONFIRMED)"),
        R.cause("ST-01 balustrade run RL-07 (4 flights + 2 level pieces): outside his 18.95 under every decomposition "
                "(two balustraded staircases are drawn; his one figure covers at most one)", -rl07, "ENGINE_RIGHT",
                "SCOPE", "T-393 / T-476 / T-480 (MS2-L Checker own 3.782209)"),
        R.cause("ST-01b D1 lobby flight rail RL-08: in our list only under decomposition A (his = ST-02 system + D-23)",
                -rl08, "ENGINE_RIGHT", "SCOPE", "T-393 s.4 (section A-A draws it)"),
        R.cause("unexplained: his 18.95 - (RL-05 16.324 + RL-06 2.400); his row has no breakdown", residual,
                "UNRESOLVED", "RESIDUAL", "T-393 s.4 decomposition A; T-578 re-read of his rows"),
        R.cause("held / unknown balustrade pieces (5 lines blank): his share not separable from a typed constant",
                0, "HELD", "HELD", "T-476 / T-480", bound=hb7),
        R.cause("held guards RL-04 / RL-10 (2 lines blank)", 0, "HELD", "HELD", "T-164 / T-199", bound=hb13),
        R.cause("pitch vs plan length: tested, 0 in the closure (if his were plan length, ST-02 sloped pieces would be "
                f"{S(pitch_excess)} lower and decomposition A would leave {S(residual + pitch_excess)}, a worse fit; "
                "every flight piece here is installed along the pitch, R-T578-1 (a))", 0, "ENGINE_RIGHT", "MEASURE",
                "T-476 census, recomputed"),
        R.cause("both sides vs one side of a flight: 0 (no wall rail drawn on any wall side, UP-STAIR-013; B7-10 "
                "NOT_APPLICABLE)", 0, "AGREE", "MEASURE", "T-476 scan"),
    ]
    gap = R.close(his, ours_all, causes)
    return {
        "unit": "lm", "sign": "his - ours",
        "ours": {"by_family": {k: S(v) for k, v in ours.items()}, "total": S(ours_all),
                 "held_bound": {"BALUSTRADE": B(hb7), "GUARD": B(hb13)}},
        "his": {"cell": "COV.B39", "value": S(his), "label": "lm", "typed_constant": True,
                "rows_behind_it": 0},
        "gap": S(gap), "pct": S(R.pct(his, ours_all, causes)),
        "pct_withheld": "SCOPE and HELD causes (R-T578-1 (e))",
        "like_for_like_hypothesis_A": {"ours": S(rl05 + rl06), "his": S(his), "his_minus_ours": S(residual),
                                       "status": "a hypothesis about his scope, never proven; not a % claim"},
        "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"], "amount": S(c["amount"]),
                    **({"bound": B(c["bound"])} if "bound" in c else {}), "source": c["source"]} for c in causes],
        "runs": [{**{k: (S(v) if isinstance(v, Decimal) else v) for k, v in r.items() if k != "bound"},
                  "bound": B(r["bound"])} for r in runs],
        "reader_lines_retired": {"count": len(readers), "class": "EXCLUDED (NOT_APPLICABLE_WITH_EVIDENCE, T-480)",
                                 "figure": None},
    }


# ---- nosing (T-412 census) -----------------------------------------------------------------------------------------
STAIRS = {"ST-01": 23, "ST-02": 30, "ST-03": 16}       # his marble rows: main / inner / entrance step rows
SECTION = {"ST-01": ("A22", "5de713ef29d8"), "ST-02": ("A29", "a0b5f46b23e4"), "ST-03": ("A15", "0debe1b7d0fe")}
STEP_ROW_LABEL = "bc06b03be870"


def nosings():
    out = []
    for r in csv.DictReader((ROOT / NOSING).open(encoding="utf-8")):
        if r["status"] == "DRAWING-CONFIRMED":
            p = R.nosing_piece(r["eid"], r["stair"], r["kind"], "DRAWING-CONFIRMED", edge=r["length_m"],
                               notch=r["notch_m"])
            if p["value"] != D(r["qty_lm"]):
                raise R.RuleError(f"{r['eid']}: edge - notch {p['value']} != census {r['qty_lm']}")
        else:
            p = R.nosing_piece(r["eid"], r["stair"], r["kind"], "HELD", beside=(r["beside_lm"] or None))
        p["flight"] = r["flight"]
        out.append(p)
    return out


def nosing_tables(cells):
    ns = nosings()
    if [_h(cells[f"MRB.{c}"]) for c in ("B8", "C9")] != ["a760cfd5140e", "0b606bfc7e9d"]:
        raise R.RuleError("marble sheet count / length labels not as expected")
    lm_groups, nr_groups = [], []
    for st, row in STAIRS.items():
        a, hh = SECTION[st]
        if _h(cells[f"MRB.{a}"]) != hh or _h(cells[f"MRB.A{row}"]) != STEP_ROW_LABEL:
            raise R.RuleError(f"his step row {row} / section for {st} not as expected")
        n_his = D(cells[f"MRB.B{row}"])
        w_his = D(repr(cells[f"MRB.C{row}"]))
        his_lm = R.his_row_lm(n_his, w_his)
        mine = [p for p in ns if p["stair"] == st]
        conf = [p for p in mine if p["status"] == "DRAWING-CONFIRMED"]
        held = [p for p in mine if p["status"] == "HELD"]
        ours = R.ours_total(mine)
        n_ours = len(mine)
        extra = n_his - n_ours
        if extra < 0:
            raise R.RuleError(f"{st}: fewer pieces in his row than risers drawn: a new cause is needed")
        widths = {p["edge"] for p in conf}
        if len(widths) != 1:
            raise R.RuleError(f"{st}: confirmed edges of more than one width")
        w = widths.pop()
        notch = sum((p["notch"] for p in conf), Z)
        hb = R.held_bound(held)
        lm_c, nr_c = [], []
        if extra:
            lm_c.append(R.cause(f"{S(extra)} pieces in his row beyond the {n_ours} risers drawn (one nosing per riser); "
                                "every reading of his count tested fails (T-412 s.5)", extra * w_his, "UNRESOLVED",
                                "RESIDUAL", "T-412 (risers by section A-A, Q-46 A)"))
            nr_c.append(R.cause("pieces beyond the risers drawn", extra, "UNRESOLVED", "RESIDUAL", "T-412"))
        if held:
            lm_c.append(R.cause(f"{len(held)} nosings HELD on our side (his pieces opposite them at his width)",
                                len(held) * w_his, "HELD", "HELD", "T-412 (winder CONFLICT, undrawn floor edges, MS2-TR, "
                                "RS-C curved Q-50 A cond)", bound=hb))
            nr_c.append(R.cause(f"{len(held)} nosings HELD on our side", len(held), "HELD", "HELD", "T-412",
                                bound=(Z, D(len(held)))))
        if w_his != w:
            lm_c.append(R.cause(f"width basis: his {S(w_his)} (the structural lane) vs the drawn front edge {S(w)} on "
                                f"{len(conf)} confirmed nosings", len(conf) * (w_his - w), "ENGINE_RIGHT", "MEASURE",
                                "T-412 s.4 (every drawn marble front edge 1.150, both DXFs)"))
        if notch:
            lm_c.append(R.cause("drawn column notches on the front edge (he deducts none)", notch, "ENGINE_RIGHT",
                                "MEASURE", "T-412 / T-410 R-T410-4"))
        if not lm_c:
            lm_c.append(R.cause("same count and width", 0, "AGREE", "MEASURE", "T-412"))
            nr_c.append(R.cause("same count", 0, "AGREE", "MEASURE", "T-412"))
        gap = R.close(his_lm, ours, lm_c)
        ngap = R.close(n_his, D(len(conf)), nr_c)
        lm_groups.append({"stair": st, "his_cells": f"MRB.B{row} x MRB.C{row}", "his_count": S(n_his),
                          "his_width": S(w_his), "his": S(his_lm), "ours": S(ours), "ours_confirmed_n": len(conf),
                          "ours_held_n": len(held), "held_bound": B(hb) if held else None,
                          "held_drawn_beside": {"lm": S(sum((p["bound"][1] for p in held if p["bound"][1] is not None),
                                                            Z)),
                                                "n_drawn": sum(1 for p in held if p["bound"][1] is not None),
                                                "n_not_drawn": sum(1 for p in held if p["bound"][1] is None)},
                          "gap": S(gap),
                          "pct": S(R.pct(his_lm, ours, lm_c)),
                          "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"],
                                      "amount": S(c["amount"]), **({"bound": B(c["bound"])} if "bound" in c else {}),
                                      "source": c["source"]} for c in lm_c],
                          "held": [{"id": p["id"], "flight": p["flight"], "kind": p["kind"], "bound": B(p["bound"])}
                                   for p in held]})
        nr_groups.append({"stair": st, "his": S(n_his), "ours": len(conf), "gap": S(ngap),
                          "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"],
                                      "amount": S(c["amount"]), **({"bound": B(c["bound"])} if "bound" in c else {})}
                                     for c in nr_c]})
    tot = lambda gs, k: sum((D(g[k]) for g in gs), Z)  # noqa
    conf_all = R.ours_total(ns)
    if conf_all != tot(lm_groups, "ours") or conf_all != D("87.35"):
        raise R.RuleError(f"nosing confirmed total {conf_all} is not the merged T-412 87.350")
    hb_all = R.held_bound([p for p in ns if p["status"] == "HELD"])
    return {
        "lm": {"unit": "lm", "sign": "his - ours", "groups": lm_groups,
               "totals": {"his": S(tot(lm_groups, "his")), "ours": S(conf_all),
                          "gap": S(tot(lm_groups, "his") - conf_all), "held_n": sum(g["ours_held_n"] for g in lm_groups),
                          "held_bound": B(hb_all), "pct": None,
                          "pct_withheld": "HELD and UNRESOLVED count causes (R-T578-1 (e))"},
               "his_note": "he carries no nosing row; his only lm along the nosing edges is each step row's count x "
                           "width (cells in his marble sheet booked in its area column, T-577 F-T577-3)"},
        "nr": {"unit": "nr", "sign": "his - ours", "groups": nr_groups,
               "totals": {"his": S(tot(nr_groups, "his")), "ours": sum(g["ours"] for g in nr_groups),
                          "gap": S(tot(nr_groups, "his") - sum(g["ours"] for g in nr_groups))}},
    }


# ---- his cells -----------------------------------------------------------------------------------------------------
SHEETS = {("FIN", "6329cb4ab3f1"): "COV", ("FIN", "3a9d8cc3e07d"): "MRB"}


def his_cells():
    d = json.loads((ROOT / RAW).read_text())
    cells = {}
    for x in d["rows"]:
        key = SHEETS.get((x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]))
        if key:
            for c, v in x["cells"].items():
                cells[f"{key}.{c}"] = v["v"]
                cells[f"{key}.{c}.f"] = v["f"]
    return cells


def code_closure(L):
    out = {}
    for code in RAIL_CODES + ("FIN.STAIR.STEP_LM",):
        xs = [x for x in L.values() if x["item_code"] == code]
        cls = {}
        for x in xs:
            cls[x["class"]] = cls.get(x["class"], 0) + 1
        rel = sum((D(x["measured_net"]) for x in xs if x["class"] == "RELEASED"), Z)
        out[code] = {"lines": len(xs), "by_class": dict(sorted(cls.items())), "valued_lm": S(rel)}
    out["FIN.STAIR.STEP_LM"]["why"] = ("not this element: the commercial step lm per tread (UP-STAIR-008, tread + "
                                       "riser + nosing in one step basis), reconciled under T-412 / T-577; the nosing "
                                       "is one edge per riser and has no candidate line yet (T-424 QUEUED)")
    nos = [x for x in L.values() if "NOSING" in (x["item_code"] or "")]
    out["nosing_lines_in_candidate"] = len(nos)
    if nos:
        raise R.RuleError("a nosing line exists in the candidate: compare it, not the census only")
    return out


def build():
    pins()
    L = index_lines()
    cells = his_cells()
    rails = rail_table(L, census(), cells)
    nos = nosing_tables(cells)
    return {
        "schema": "T578_RAIL_NOSING_RECONCILE_V1", "rule": "R-T578-1", "candidate": "ARCH_TAKEOFF_V3.0.58",
        "line_index": LINE_INDEX, "pins": PINS,
        "rails_lm": rails, "nosing_lm": nos["lm"], "nosing_nr": nos["nr"], "code_closure": code_closure(L),
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != out:
            raise SystemExit("T578 output differs from a rebuild")
        print("T578 check: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
