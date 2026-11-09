"""T-654 THE 10 NOV TRIAL BOQ r4 (R-T654-2; lane I, non-candidate document, research only).

Regenerates the trial BOQ (R-T636-1, R-T649-2 and R-T652-2, read only: columns, cause resolution, guards, proofs,
report) on the merged candidate of record ARCH_TAKEOFF_V3.0.61 + WIRING MANIFEST V20 (T-654, rebuilt with its own calls),
grouped once by the newest merged master BOQ_FAMILY_MASTER 1.61.0 (T-563, merged e04d99d9; F-C-T652-1: the trial reads
the newest master; 1.62.0 = T-655 was CLAIMED, not merged, at this claim).

R-T654-2 (every villa on the engine's line-index scheme; adds to R-T652-2, which stands whole):
  (a) THE DIFF r3 -> r4 IS LINE BY LINE AND EVERY CHANGED LINE IS NAMED: a line whose class, net, held bound, column,
      origin or chosen cause moved must belong to a Gate B merge in between (T-423 r3 V3.0.60, T-563 V3.0.61) or to a
      V20 row (F-T652-1); a quantity field may move only on a V20 row line (a merge that was already in the overlay
      moves provenance, never quantity); anything else is refused.
  (b) A MERGED RESTATEMENT STATES THE HOLD CAUSE OF ITS LINES: on a line a Gate B package restated, the merged record
      (the cause the verdict accepted: T-563 'why_held' + the RFI the module keeps) is the chosen cause; older census
      or overlay causes are kept as 'also stated by', never dropped.
  (c) HELD WITH CAUSE MAY NOT FALL BELOW r3 (2,728); HELD never 0, never summed into a released total.
Rebuild through the wrapper: `URBAN_T654_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-654
tests/t654_manifest_v20/test_t654.py::test_write_outputs`; check: `... pytest --tree task-T-654 tests/t654_manifest_v20`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT / "research/agents_t636", ROOT / "research/agents_t649", ROOT / "research/agents_t652", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trial_boq as T                      # noqa: E402  (R-T636-1, read only)
import trial_boq_r2 as R2                  # noqa: E402  (R-T649-2, read only)
import trial_boq_r3 as R3                  # noqa: E402  (R-T652-2, read only)
import manifest_v20 as M20                 # noqa: E402  (R-T654-1)

E, OV, M9 = T.E, T.OV, T.M9
D, S = T.D, T.S
SCHEMA, RULE = "URBAN_T654_TRIAL_BOQ_R4", "R-T654-2"
OUT_JSON = HERE / "out/TRIAL_BOQ_R4_T654.json"
OUT_MD = HERE / "out/TRIAL_BOQ_R4_T654.md"
OUT_CSV = HERE / "out/TRIAL_BOQ_R4_T654_LINES.csv"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json"
MASTER_VERSION = "1.61.0"
V20 = HERE / "out/WIRING_MANIFEST_V20.json"
R3_JSON = ROOT / "research/agents_t652/out/TRIAL_BOQ_R3_T652.json"
BASELINE_HELD_R3 = 2728
WIRED61 = "WIRED IN V3.0.61"
GATEB563 = "V3.0.61 GATE B (T-563, merged e04d99d9)"
MERGED_SINCE_V19 = {
    "T-423": "ARCH_TAKEOFF_V3.0.60 (22 text-only lines; the 17 pre-merge 'T-423 r2' TEXT_ONLY rows leave the overlay); "
             "master 1.60.0",
    "T-563": "ARCH_TAKEOFF_V3.0.61 = the base (11 FIN.PLASTER restated, the 22 pre-merge rows leave the overlay, "
             "FR-T617-1 stays chained); master 1.61.0 (the grouping of this BOQ)",
    "T-652": "F-T652-1 accepted as a Lead fix row: D-1F-07 face bound wired as HELD on the 1F 0.15 m host units / mortar "
             "(V20)",
    "T-653": "no quantity (Decimal context); the rebuild is order-independent",
}
OPEN_ROWS = (("FIN.EXT.", "T-314 r3 (TODO, external faces)"),)


class TrialError(Exception):
    pass


def open_row(code):
    return next((r for p, r in OPEN_ROWS if code.startswith(p)), None)


def overlay():
    base, order, rul, after, rep, after19, rep19, rows, outs, src = M20.overlay_v20()
    v20 = T._json(V20)
    if len(after) != v20["overlay"]["lines"]["after_v20"]:
        raise TrialError("STALE_INPUT: the V20 rebuild differs from the committed V20 line count")
    t20 = OV.totals(after)
    for k, d in v20["overlay"]["v20_vs_v19_totals"].items():
        if t20.get(k) != d["after"]:
            raise TrialError(f"STALE_INPUT: V20 rebuild total {k} differs from the committed V20")
    return base, order, after, rep, outs, src, v20


def r4_records(stage, entries):
    """R-T654-2 (b): the merged T-563 record per restated line (its 'why_held' and the RFI the module keeps)."""
    out = {}
    by = {e["line_id"]: e for e in entries}
    for lid, s in stage.items():
        e = by[lid]
        out[lid] = T._rec(563, "candidate record V3.0.61 (T-563 Gate B, merged e04d99d9)",
                          f"{e['why_held']}; RFI kept: {e['question']}",
                          kind="candidate record V3.0.61 (T-563)")
    return out


def merged_cause_first(causes, merged):
    """(b): the merged record is the chosen cause on its lines; what was chosen before goes to 'also stated by'."""
    for lid, rec in merged.items():
        old = causes.get(lid)
        also = sorted(set((old or {}).get("also_stated_by", [])) | ({old["source"]} if old else set()))
        causes[lid] = dict(rec, also_stated_by=also)
    return causes


def _sub(t):
    return R3._sub(t)


def vs_r3(r3, trades, by_trade_r4):
    a = {f"{t['trade']}|{t['unit']}": _sub(t) for t in r3["trades"]}
    b = {f"{t['trade']}|{t['unit']}": _sub(t) for t in trades}
    out = {k: {"r3": a.get(k), "r4": b.get(k)} for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}
    ht = {g: [r3["held_cause_by_trade"].get(g, {}).get("with_cause"), v.get("with_cause")]
          for g, v in by_trade_r4.items() if r3["held_cause_by_trade"].get(g, {}).get("with_cause") != v.get("with_cause")}
    return {"trade_unit": out, "held_with_cause_by_trade": ht}


QKEYS = ("class", "measured_net", "held_low", "held_high")


def line_diff(r3_lines, r4_lines, allowed, qty_allowed):
    """(a): every line whose quantity, column, origin or cause moved, each with its reason; refuses anything else."""
    a = {p["line_id"]: p for p in r3_lines}
    b = {p["line_id"]: p for p in r4_lines}
    if set(a) != set(b):
        raise TrialError(f"line set moved: {sorted(set(a) ^ set(b))[:3]}")
    out = []
    lab = {R3.WIRED59: WIRED61}                 # the WIRED column's label names the candidate: relabel, not a move
    for lid in sorted(b):
        x, y = dict(a[lid], column=lab.get(a[lid].get("column"), a[lid].get("column")),
                    origin=str(a[lid].get("origin")).replace("candidate V3.0.59", "candidate V3.0.61")), b[lid]
        q = [k for k in QKEYS if x.get(k) != y.get(k)]
        o = [k for k in ("column", "origin", "cause", "cause_source") if x.get(k) != y.get(k)]
        if not q and not o:
            continue
        why = allowed.get(lid)
        if why is None:
            raise TrialError(f"{lid}: moved {q + o} with no Gate B merge or V20 row in between (R-T654-2 (a))")
        if q and lid not in qty_allowed:
            raise TrialError(f"{lid}: quantity {q} moved by {why}: only a V20 row line may move a quantity")
        out.append({"line_id": lid, "item_code": y["item_code"], "unit": y["unit"], "why": why,
                    "r3": {k: x.get(k) for k in (*QKEYS, "column", "origin", "cause_source")},
                    "r4": {k: y.get(k) for k in (*QKEYS, "column", "origin", "cause_source")}, "moved": q + o,
                    "quantity_moved": bool(q)})
    return out


def build():
    master = T._json(MASTER)
    if master.get("version") != MASTER_VERSION:
        raise TrialError(f"STALE_INPUT: BOQ_FAMILY_MASTER is not {MASTER_VERSION}")
    src = T.load_sources()
    base, order, after, rep, outs, src20, v20 = overlay()
    gops = R3.gateb_ops(src20["T498"]["rows"], order)
    gateb = {o["line_id"] for o in gops}
    bound, base_ids = E.bindings(), set(base)
    T.guard_held(after)
    ops = T.last_ops(order)
    owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded = E.aggregate(after, bound, order + [(R3.GATEB, gops)],
                                                                                 master)
    checks = E.proof(after, item_acc, fam_acc, grp_acc, unit_acc)
    recs = T.census_records(src)
    ext, stale = T.extract_records(src, after)
    t646, t650 = R2.M18._json(R2.M18.IN["T646"]), R2.M18._json(R2.M18.IN["T650"])
    for k, v in (list(ext.items()) + list(R2.extra_records(t646, t650, R3.text_causes(order)).items())
                 + list(R3.r3_records(src20["T647"], src20["T648"], src20["T498"]["rows"]).items())):
        recs.setdefault(k, []).extend(v)
    stage = outs["stage"]
    merged = r4_records(stage, M20.I563.build()["entries"])
    causes = merged_cause_first(T.resolve_causes(after, ops, recs), merged)
    for p in per_line:
        p["column"] = R3.column_r3(p["line_id"], after[p["line_id"]], ops.get(p["line_id"]), p["evidence"], gateb)
        p["origin"] = "overlay op" if p["line_id"] in ops else "candidate V3.0.61"
        if p["class"] == "HELD":
            c = causes.get(p["line_id"])
            p["cause"] = None if c is None else c["cause"]
            p["cause_source"] = None if c is None else c["source"]
            p["cause_kind"] = None if c is None else c["kind"]
            p["cause_ids"] = [] if c is None else c["ids"]
            p["cause_also_stated_by"] = [] if c is None else c.get("also_stated_by", [])
            p["finding"] = "F-T636-1" if c is None else None
    T.guard_columns(per_line, ops)
    col = T.columns(per_line)
    cproof = T.column_proof(col, item_acc, fam_acc, grp_acc, unit_acc)
    trades = T.trade_tables(item_acc, fam_acc, grp_acc, col, per_line, causes)
    T.guard_totals(trades)
    held = [p for p in per_line if p["class"] == "HELD"]
    no_cause = [p for p in held if p["cause"] is None]
    out = {"trades": trades, "per_line": per_line, "column_proof": cproof, "aggregation_proof": checks,
           "unit_grand": {u: dict(E._out(a, u), **T._cout(col["unit"][u])) for u, a in sorted(unit_acc.items())},
           "held": {"lines": len(held), "with_cause": len(held) - len(no_cause), "finding_F_T636_1": len(no_cause)},
           "uncoded": [{"bucket": b, "item_code": c, "unit": u, "lines": n} for (b, c, u), n in sorted(uncoded.items())],
           "t297_stale_lines": sorted(stale)}
    old_open = T.open_row
    T.open_row = open_row                  # the open board rows at this claim (pointer only), restored below
    try:
        out = T.finish(out, master, src, after, order, rep, fam_acc, base_ids)
    finally:
        T.open_row = old_open
    if out["held"]["with_cause"] < BASELINE_HELD_R3:
        raise TrialError(f"HELD with cause fell: {out['held']['with_cause']} < r3 {BASELINE_HELD_R3}")
    r3 = T._json(R3_JSON)
    out = relabel(out)
    per = out["per_line"]
    allowed = {}
    for lid in outs["text60"]:
        allowed[lid] = "T-423 r3 V3.0.60 text-only line (pre-merge TEXT_ONLY row left the overlay)"
    for lid in outs["set_aside_60"]:
        allowed[lid] = "T-423 r3 V3.0.60 named set-aside (pre-merge TEXT_ONLY row left the overlay)"
    for lid, s in stage.items():
        allowed[lid] = f"T-563 V3.0.61 restated {s['room']} plaster line (pre-merge row left the overlay)"
        allowed[s["paint"]] = f"T-563 V3.0.61 {s['room']} paint pair (byte-identical; pre-merge TEXT_ONLY row left)"
    fl = {M20.F_T652_1["units"], M20.F_T652_1["mortar"]}
    for lid in fl:
        allowed[lid] = "V20 row F-T652-1 (D-1F-07 face bound, R-T654-1 (c))"
    diff = line_diff(r3["per_line"], per, allowed, fl)
    if {d["line_id"] for d in diff if d["quantity_moved"]} != fl:
        raise TrialError("the F-T652-1 lines did not move, or another line moved a quantity")
    flagged = R3.stale_causes(per)
    out.update({
        "schema": SCHEMA, "rule": RULE, "task": "T-654", "revision": "r4 (of the T-636 trial BOQ of record)",
        "candidate": M20.CANDIDATE,
        "overlay": "WIRING MANIFEST V20 (T-654, this package; V19 T-652 merged 2e80c03f rebased on V3.0.61 + the "
                   "F-T652-1 rows)",
        "master": f"BOQ_FAMILY_MASTER {MASTER_VERSION} (T-563, merged e04d99d9; newest merged at claim; 1.62.0 = T-655 "
                  "CLAIMED, not merged)",
        "merged_since_v17_not_in_overlay": {}, "merged_since_v19": MERGED_SINCE_V19,
        "inputs": {str(p.relative_to(ROOT)): T.sha256(p) for p in (MASTER, T.SCORECARD, V20, T.INDEX57, R3_JSON,
                                                                    *T.SRC.values(), *M20.IN.values())},
        "vs_r3": {"held_with_cause": [r3["held"]["with_cause"], out["held"]["with_cause"]],
                  "held_lines": [r3["held"]["lines"], out["held"]["lines"]],
                  "finding_F_T636_1": [r3["held"]["finding_F_T636_1"], out["held"]["finding_F_T636_1"]],
                  "released_lines": [r3["lines"]["released"], out["lines"]["released"]],
                  "excluded_lines": [r3["lines"]["excluded"], out["lines"]["excluded"]],
                  "lines": [r3["lines"]["after_v19"], len(after)],
                  **vs_r3(r3, out["trades"], out["held_cause_by_trade"])},
        "diff_r3_r4": diff,
        "diff_r3_r4_count": {"lines": len(diff), "quantity_moved": sum(d["quantity_moved"] for d in diff)},
        "gate_b_wired_lines": sorted(gateb),
        "gate_b_restated_held_lines": {lid: s["room"] for lid, s in sorted(stage.items())},
        "stale_causes_F_T652_2": flagged,
        "f_t652_1": v20["f_t652_1"],
        "registry_text_corrections": [R2.b8_06_correction(master)],
    })
    out["lines"]["base_v3_0_61"] = out["lines"].pop("base_v3_0_58")
    out["lines"]["after_v20"] = out["lines"].pop("after_v17")
    return out


def relabel(o):
    """label only: the WIRED column is the V3.0.61 candidate's; op cause kinds name the V20 manifest."""
    if isinstance(o, dict):
        return {relabel(k): relabel(v) for k, v in o.items()}
    if isinstance(o, list):
        return [relabel(v) for v in o]
    if isinstance(o, str):
        if o == R2.OP_KIND_V17:
            return "overlay op (V20 manifest row)"
        return o.replace("WIRED IN V3.0.58", WIRED61).replace("V3.0.58 candidate + overlay V17",
                                                              "V3.0.61 candidate + overlay V20")
    return o


def dumps(o):
    return T.dumps(o)


def render_md(b):
    b0 = dict(b, lines=dict(b["lines"], after_v17=b["lines"]["after_v20"], base_v3_0_58=b["lines"]["base_v3_0_61"]))
    md = T.render_md(b0).replace("# T-636 the 10 Nov trial BOQ (generated; R-T636-1)",
                                "# T-654 the 10 Nov trial BOQ r4 (generated; R-T654-2 on R-T652-2 / R-T649-2 / "
                                "R-T636-1)")
    md = md.replace("- Lines after V17:", "- Lines after V20:").replace("(base V3.0.58 ", "(base V3.0.61 ")
    md = md.replace("in the V3.0.58 candidate with a Checker binding", "in the V3.0.61 candidate with a Checker "
                    "binding or the status its Gate B verdict states").replace("master 1.56.0",
                                                                               f"master {MASTER_VERSION}")
    v, f = b["vs_r3"], b["f_t652_1"]
    add = ["", "## 7. r4 changes against r3 (T-652)", "",
           f"- Base: ARCH_TAKEOFF_V3.0.61 (T-423 r3 22 text-only lines + T-563 11 FIN.PLASTER restated; 39 pre-merge "
           f"overlay rows left by equality; V19 re-applied byte-equal). HELD with cause {v['held_with_cause'][0]} -> "
           f"{v['held_with_cause'][1]} of HELD lines {v['held_lines'][0]} -> {v['held_lines'][1]}; F-T636-1 "
           f"{v['finding_F_T636_1'][0]} -> {v['finding_F_T636_1'][1]}; released lines {v['released_lines'][0]} -> "
           f"{v['released_lines'][1]}; excluded {v['excluded_lines'][0]} -> {v['excluded_lines'][1]}.",
           f"- Line diff r3 -> r4: {b['diff_r3_r4_count']['lines']} lines, {b['diff_r3_r4_count']['quantity_moved']} "
           "with a quantity (only the F-T652-1 pair); every other changed line moved provenance / cause only, "
           "each named by its merge.", "",
           "| Trade x unit | r3 released (n) | r4 released (n) | r3 HELD | r4 HELD |", "|---|---|---|---|---|"]
    for k, d in v["trade_unit"].items():
        a, c = d["r3"] or {}, d["r4"] or {}
        add.append(f"| {k} | {a.get('released')} ({a.get('released_n')}) | {c.get('released')} ({c.get('released_n')}) "
                   f"| {a.get('held_n')} | {c.get('held_n')} |")
    add += ["", "- HELD with cause by trade (r3 -> r4): " + ("; ".join(f"{g} {x[0]} -> {x[1]}" for g, x in
                                                                       v["held_with_cause_by_trade"].items()) or "none")
            + ".",
            f"- F-T652-1: D-1F-07 face {f['face_m2'][0]} .. {f['face_m2'][1]} m2 (was 0.32): 1F 0.15 m host base "
            f"{f['base_m2'][0]} .. {f['base_m2'][1]} m2; units {f['units']['was']} -> HELD {f['units']['bound'][0]} .. "
            f"{f['units']['bound'][1]} pcs; panel mortar {f['panel mortar']['was']} -> HELD "
            f"{f['panel mortar']['bound'][0]} .. {f['panel mortar']['bound'][1]} m3.",
            "- The 11 FIN.PLASTER lines of V3.0.61 are HELD with the merged cause (roof build-up D-39 / DCR-6), "
            "never 0; 3 of them keep the FR-T617-1 low end (+0.59 / +0.59 / +0.24 m2) from the overlay.",
            f"- F-T652-2 stale causes on answered decisions: {len(b['stale_causes_F_T652_2'])} line(s).",
            "- Registry text (F-T525-1): B8-06 'open' reads as: " + b["registry_text_corrections"][0]["reads_as"] + "."]
    return md.rstrip("\n") + "\n" + "\n".join(add) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    OUT_CSV.write_text(T.render_csv(b), encoding="utf-8")
    return b
