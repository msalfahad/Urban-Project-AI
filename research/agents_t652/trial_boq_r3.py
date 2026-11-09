"""T-652 THE 10 NOV TRIAL BOQ r3 (R-T652-2; lane I, non-candidate document, research only).

Regenerates the trial BOQ (R-T636-1 and R-T649-2, read only: columns, cause resolution, guards, proofs, report) on the
merged candidate ARCH_TAKEOFF_V3.0.59 + WIRING MANIFEST V19 (T-652, rebuilt with its own calls), grouped once by
BOQ_FAMILY_MASTER 1.58.0 (T-498, merged 4c37ce2c).

R-T652-2 (every villa on the engine's line-index scheme; adds to R-T636-1 and R-T649-2, which stand whole):
  (a) A GATE B LINE IS WIRED WITH THE STATUS ITS VERDICT STATES: a candidate line a Gate B package merged (here the
      V3.0.59 stage, T-498) and no overlay op moved goes in the WIRED IN V3.0.59 column with the WORKFLOW_CONTROLS
      s.5 status the Gate B verdict states (units / glue DRAWING-CONFIRMED, mortar ASSUMED — OWNER-APPROVED); it is
      never a Checker-verified whole line unless the verdict says VERIFIED.
  (b) CAUSE SOURCES r3 = r2 + the merged T-647 r2 structural census, the merged T-648 r2 finishes census, the merged
      V3.0.59 stage records (T-498 'why' per line) and the V19 ops (re-measure, NOT_APPLICABLE, downgrade causes); the
      latest task wins as in R-T636-1 (a).
  (c) A STALE CAUSE ON AN ANSWERED DECISION IS FLAGGED: a HELD line whose chosen cause still states a question the
      owner or the Checker has answered (0.15 m module not stated: Q-80 A; 'Checker re-measure pending': Verifier
      07:06) is listed as finding F-T652-2 by line id; it is never silently kept, never re-typed.
  (d) BEFORE / AFTER vs r2 per trade and unit (released, released lines, HELD lines, HELD with cause); HELD with cause
      may not fall below r2 (2351).
Rebuild through the wrapper: `URBAN_T652_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-652
tests/t652_manifest_v19/test_t652.py::test_write_outputs`; check: `... pytest --tree task-T-652 tests/t652_manifest_v19`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT / "research/agents_t636", ROOT / "research/agents_t649", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trial_boq as T                      # noqa: E402  (R-T636-1, read only)
import trial_boq_r2 as R2                  # noqa: E402  (R-T649-2, read only)
import manifest_v19 as M19                 # noqa: E402  (R-T652-1)

E, OV, M9 = T.E, T.OV, T.M9
D, S = T.D, T.S
SCHEMA, RULE = "URBAN_T652_TRIAL_BOQ_R3", "R-T652-2"
OUT_JSON = HERE / "out/TRIAL_BOQ_R3_T652.json"
OUT_MD = HERE / "out/TRIAL_BOQ_R3_T652.md"
OUT_CSV = HERE / "out/TRIAL_BOQ_R3_T652_LINES.csv"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json"
V19 = HERE / "out/WIRING_MANIFEST_V19.json"
R2_JSON = ROOT / "research/agents_t649/out/TRIAL_BOQ_R2_T649.json"
BASELINE_HELD_R2 = 2351
GATEB = "V3.0.59 GATE B (T-498, merged 4c37ce2c)"
GATEB_STATUS = {"SOURCE_DERIVED": "DRAWING-CONFIRMED", "PROVISIONAL": "ASSUMED — OWNER-APPROVED"}
WIRED59 = "WIRED IN V3.0.59"
STALE_ANSWERED = (
    (re.compile(r"module of the 0\.15 m black block is not stated|0\.15 m module not stated|module not stated"),
     "Q-80 A (owner 2026-11-07: 0.15 m black block 40 x 20, 12.5 / m2)"),
    (re.compile(r"re-measure pending"), "Checker re-measure 2026-11-09 07:06 (T-650 row: D-1F-07, L-GF-01)"),
)
MERGED_SINCE_V18 = {
    "T-498": "ARCH_TAKEOFF_V3.0.59 = the base (74 stage lines out of the overlay, R-T652-1 (a)); master 1.58.0",
    "T-647": "5 CN NOT_APPLICABLE (V19) + 183 structural causes; 17 count-convention bounds listed",
    "T-648": "A-GF-01 threshold strip 0.150 m2 (V19) + 198 finishes causes",
    "T-649": "F-T645-1 downgrades CHECKER-VALIDATED, applied in V19",
    "T-650": "Checker re-measure 07:06: D-1F-07 bound wired, L-GF-01 register hold restated (V19)",
    "T-635": "F-C-T635-1 statement op (2 B10 rows PARTIALLY VERIFIED)",
}
OPEN_ROWS = (("FIN.PLASTER", "T-563 (TODO, plaster height Gate B)"), ("FIN.EXT.", "T-314 r2 (TODO, external faces)"),
             ("FIN.", "T-423 r3 (TODO, finishes split remainder)"))


class TrialError(Exception):
    pass


def open_row(code):
    return next((r for p, r in OPEN_ROWS if code.startswith(p)), None)


def gateb_ops(stage_rows, order):
    """R-T652-2 (a): evidence-only pseudo ops for stage lines no overlay quantity op moved (never applied)."""
    moved = set(T.last_ops(order))
    ops = []
    for r in stage_rows:
        st = GATEB_STATUS.get(r["after"]["state"])
        if st is None or r["line_id"] in moved:
            continue
        s = M19.stage_state(r)
        ops.append({"op_id": f"{GATEB}|{r['line_id']}", "package": GATEB, "row": "GATE_B", "kind": "SET",
                    "line_id": r["line_id"], "before": s, "after": s, "source": GATEB,
                    "evidence": {"status": st, "verdict_line": M19.MERGED["T-498"]["verdict"]}})
    return ops


def column_r3(lid, line, op, evidence, gateb):
    if op is None and lid in gateb and line["class"] == "RELEASED":
        if evidence not in (*T.CHECKER_STATUSES, "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED"):
            raise TrialError(f"{lid}: a Gate B line with status {evidence!r}")
        return T.WIRED
    return T.column_of(lid, line, op, evidence)


def text_causes(order):
    """the cause a V19 TEXT_ONLY op names for a HELD line it leaves blank (register hold, pair carried once)."""
    return {op["line_id"]: op["beside"]["cause"] for _, ops in order for op in ops
            if op["kind"] == "TEXT_ONLY" and re.search(r"R-T65[02]-1/", op["op_id"])
            and (op.get("beside") or {}).get("cause")}


def r3_records(t647, t648, stage_rows):
    out = {}
    for r in t647["records"]:
        if r.get("cause"):
            out.setdefault(r["line_id"], []).append(T._rec(647, "T-647 r2 structural hold census (merged a521da8a)",
                                                           r["cause"], kind="T-647 structural census"))
    for l in t648["lines"]:
        if l.get("cause"):
            out.setdefault(l["line_id"], []).append(T._rec(648, "T-648 r2 finishes hold census (merged 57db7053)",
                                                           l["cause"], kind="T-648 finishes census"))
    for r in stage_rows:
        if r["after"]["state"] in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") and r.get("why"):
            out.setdefault(r["line_id"], []).append(T._rec(498, "candidate record V3.0.59 (T-498 stage, merged "
                                                                "4c37ce2c)", r["why"],
                                                           kind="candidate record V3.0.59 (T-498)"))
    return out


def stale_causes(per_line, patterns=STALE_ANSWERED):
    """R-T652-2 (c): HELD lines whose chosen cause states an answered question."""
    out = []
    for p in per_line:
        if p["class"] != "HELD" or not p.get("cause"):
            continue
        for rx, ans in patterns:
            if rx.search(p["cause"]):
                out.append({"line_id": p["line_id"], "item_code": p["item_code"], "answered_by": ans,
                            "cause_source": p["cause_source"]})
                break
    return out


def overlay():
    base, order, rul, after, rep, after18, rep18, rows, outs, src19 = M19.overlay_v19()
    v19 = T._json(V19)
    if len(after) != v19["overlay"]["lines"]["after_v19"]:
        raise TrialError("STALE_INPUT: the V19 rebuild differs from the committed V19 line count")
    t19 = OV.totals(after)
    for k, d in v19["overlay"]["v19_vs_v18_totals"].items():
        if t19.get(k) != d["after"]:
            raise TrialError(f"STALE_INPUT: V19 rebuild total {k} differs from the committed V19")
    return base, order, after, rep, outs, src19, v19


def _sub(t):
    s = t["subtotal"]
    return {"released": s["released"], "released_n": s["released_n"], "held_n": s["held_n"], "live": s["live_lines"],
            "wired": s["wired"], "overlay": s["overlay"], "unverified": s["unverified"]}


def vs_r2(r2, trades, by_trade_r3):
    a = {f"{t['trade']}|{t['unit']}": _sub(t) for t in r2["trades"]}
    b = {f"{t['trade']}|{t['unit']}": _sub(t) for t in trades}
    out = {}
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            out[k] = {"r2": a.get(k), "r3": b.get(k)}
    ht = {g: [r2["held_cause_by_trade"].get(g, {}).get("with_cause"), v.get("with_cause")]
          for g, v in by_trade_r3.items() if r2["held_cause_by_trade"].get(g, {}).get("with_cause") != v.get("with_cause")}
    return {"trade_unit": out, "held_with_cause_by_trade": ht}


def build():
    master = T._json(MASTER)
    if master.get("version") != "1.58.0":
        raise TrialError("STALE_INPUT: BOQ_FAMILY_MASTER is not 1.58.0")
    src = T.load_sources()
    base, order, after, rep, outs, src19, v19 = overlay()
    stage_rows = src19["T498"]["rows"]
    gops = gateb_ops(stage_rows, order)
    gateb = {o["line_id"] for o in gops}
    bound, base_ids = E.bindings(), set(base)
    T.guard_held(after)
    ops = T.last_ops(order)
    owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded = E.aggregate(after, bound, order + [(GATEB, gops)],
                                                                                 master)
    checks = E.proof(after, item_acc, fam_acc, grp_acc, unit_acc)
    recs = T.census_records(src)
    ext, stale = T.extract_records(src, after)
    t646, t650 = R2.M18._json(R2.M18.IN["T646"]), R2.M18._json(R2.M18.IN["T650"])
    for k, v in (list(ext.items()) + list(R2.extra_records(t646, t650, text_causes(order)).items())
                 + list(r3_records(src19["T647"], src19["T648"], stage_rows).items())):
        recs.setdefault(k, []).extend(v)
    causes = T.resolve_causes(after, ops, recs)
    for p in per_line:
        p["column"] = column_r3(p["line_id"], after[p["line_id"]], ops.get(p["line_id"]), p["evidence"], gateb)
        p["origin"] = "overlay op" if p["line_id"] in ops else "candidate V3.0.59"
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
    if out["held"]["with_cause"] < BASELINE_HELD_R2:
        raise TrialError(f"HELD with cause fell: {out['held']['with_cause']} < r2 {BASELINE_HELD_R2}")
    r2 = T._json(R2_JSON)
    flagged = stale_causes(per_line)
    out.update({
        "schema": SCHEMA, "rule": RULE, "task": "T-652", "revision": "r3 (of the T-636 trial BOQ of record)",
        "candidate": M19.CANDIDATE,
        "overlay": "WIRING MANIFEST V19 (T-652, this package; V18 T-649 merged 89afbd85 rebased on V3.0.59 + V19 rows)",
        "master": "BOQ_FAMILY_MASTER 1.58.0 (T-498, merged 4c37ce2c); 1.59.0 (T-651, READY) changes no family's group "
                  "or item codes (registry status only)",
        "merged_since_v17_not_in_overlay": {}, "merged_since_v18": MERGED_SINCE_V18,
        "inputs": {str(p.relative_to(ROOT)): T.sha256(p) for p in (MASTER, T.SCORECARD, V19, T.INDEX57, R2_JSON,
                                                                    *T.SRC.values(), *M19.IN.values())},
        "vs_r2": {"held_with_cause": [r2["held"]["with_cause"], out["held"]["with_cause"]],
                  "held_lines": [r2["held"]["lines"], out["held"]["lines"]],
                  "finding_F_T636_1": [r2["held"]["finding_F_T636_1"], out["held"]["finding_F_T636_1"]],
                  "released_lines": [r2["lines"]["released"], out["lines"]["released"]],
                  "excluded_lines": [r2["lines"]["excluded"], out["lines"]["excluded"]],
                  "lines": [r2["lines"]["after_v18"], len(after)],
                  **vs_r2(r2, trades, out["held_cause_by_trade"])},
        "gate_b_wired_lines": sorted(gateb),
        "stale_causes_F_T652_2": flagged,
        "f_c_t498_1": v19["f_c_t498_1"],
        "statement_only_ops": v19["statement_only_ops"],
        "registry_text_corrections": [R2.b8_06_correction(master)],
    })
    out["lines"]["base_v3_0_59"] = out["lines"].pop("base_v3_0_58")
    out["lines"]["after_v19"] = out["lines"].pop("after_v17")
    return relabel(out)


def relabel(o):
    """label only: the WIRED column is the V3.0.59 candidate's; op cause kinds name the V19 manifest."""
    if isinstance(o, dict):
        return {relabel(k): relabel(v) for k, v in o.items()}
    if isinstance(o, list):
        return [relabel(v) for v in o]
    if isinstance(o, str):
        if o == R2.OP_KIND_V17:
            return "overlay op (V19 manifest row)"
        return o.replace("WIRED IN V3.0.58", WIRED59).replace("V3.0.58 candidate + overlay V17",
                                                              "V3.0.59 candidate + overlay V19")
    return o


def dumps(o):
    return T.dumps(o)


def render_md(b):
    b0 = dict(b, lines=dict(b["lines"], after_v17=b["lines"]["after_v19"], base_v3_0_58=b["lines"]["base_v3_0_59"]))
    md = T.render_md(b0).replace("# T-636 the 10 Nov trial BOQ (generated; R-T636-1)",
                                "# T-652 the 10 Nov trial BOQ r3 (generated; R-T652-2 on R-T649-2 / R-T636-1)")
    md = md.replace("- Lines after V17:", "- Lines after V19:").replace("(base V3.0.58 ", "(base V3.0.59 ")
    md = md.replace("in the V3.0.58 candidate with a Checker binding", "in the V3.0.59 candidate with a Checker "
                    "binding or the status its Gate B verdict states").replace("master 1.56.0", "master 1.58.0")
    v = b["vs_r2"]
    f = b["f_c_t498_1"]["totals"]
    add = ["", "## 7. r3 changes against r2 (T-649)", "",
           f"- Base: ARCH_TAKEOFF_V3.0.59 (74 stage lines now the candidate's own; V18 re-applied byte-equal). HELD with "
           f"cause {v['held_with_cause'][0]} -> {v['held_with_cause'][1]} of HELD lines {v['held_lines'][0]} -> "
           f"{v['held_lines'][1]}; F-T636-1 {v['finding_F_T636_1'][0]} -> {v['finding_F_T636_1'][1]}; released lines "
           f"{v['released_lines'][0]} -> {v['released_lines'][1]}; excluded {v['excluded_lines'][0]} -> "
           f"{v['excluded_lines'][1]}.", "",
           "| Trade x unit | r2 released (n) | r3 released (n) | r2 HELD | r3 HELD |", "|---|---|---|---|---|"]
    for k, d in v["trade_unit"].items():
        a, c = d["r2"] or {}, d["r3"] or {}
        add.append(f"| {k} | {a.get('released')} ({a.get('released_n')}) | {c.get('released')} ({c.get('released_n')}) "
                   f"| {a.get('held_n')} | {c.get('held_n')} |")
    add += ["", "- HELD with cause by trade (r2 -> r3): " + "; ".join(f"{g} {x[0]} -> {x[1]}" for g, x in
                                                                     v["held_with_cause_by_trade"].items()) + ".",
            f"- F-C-T498-1: 0.15 m black hosts contract {f['contract_m2']} m2, material base {f['base_m2']} (low "
            f"{f['low_m2']}) m2: units {f['units_low']} .. {f['units_high']} pcs, panel mortar {f['panel_low']} .. "
            f"{f['panel_high']} m3 (low end released, the HELD face its companion); 'module not stated' retired (Q-80 A).",
            f"- F-T652-2 stale causes on answered decisions: {len(b['stale_causes_F_T652_2'])} line(s).",
            "- Statement-only: " + "; ".join(f"{s['source']} {s['row']} {s['from']} -> {s['to']}"
                                             for s in b["statement_only_ops"]) + ".",
            "- Registry text (F-T525-1): B8-06 'open' reads as: " + b["registry_text_corrections"][0]["reads_as"] + "."]
    return md.rstrip("\n") + "\n" + "\n".join(add) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    OUT_CSV.write_text(T.render_csv(b), encoding="utf-8")
    return b
