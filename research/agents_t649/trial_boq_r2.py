"""T-649 THE TRIAL BOQ r2 (R-T649-2; lane I, non-candidate document, research only).

Regenerates the T-636 trial BOQ (R-T636-1, read only: columns, cause resolution, guards, proofs, report) on
ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V18 (T-649, rebuilt with its own calls and checked against the committed V18),
grouped once by BOQ_FAMILY_MASTER 1.57.0 (T-525, merged c7565fb9).

R-T649-2 (every villa on the engine's line-index scheme; adds to R-T636-1, which stands whole):
  (a) CAUSE SOURCES r2 = the T-636 sources + the merged T-646 roof / fence census (cause per line) + the merged T-650
      payable-form census (the 'why' per opening on its STR.CONC.LINTEL line) + the V18 ops (downgrade reasons, the
      strip companion cause, the 'Checker re-measure pending' names); the latest task wins as in R-T636-1 (a).
  (b) A WORKER DOWNGRADE PROPOSAL IS SHOWN, NEVER APPLIED: a released line under a proposal (F-T645-1) keeps its
      column and carries the proposal id beside it; its quantity is never counted as HELD and never dropped.
  (c) A REGISTRY TEXT FINDING IS A READER CORRECTION: the stale B8-06 'open' sentence (F-T525-1) is shown beside the
      family as read, with the stale part named; the master file is never edited (version files are never edited).
  (d) A STATEMENT-ONLY OP (T-633 D-GF-06 class move) is carried by name for statement V12 (T-635), never as a line.
  (e) HELD WITH CAUSE n / N is reported against the T-636 trial of record (2314 / 2750) and may not fall.
Rebuild through the wrapper: `URBAN_T649_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-649
tests/t649_manifest_v18/test_t649.py::test_write_outputs`; check: `... pytest --tree task-T-649 tests/t649_manifest_v18`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT / "research/agents_t636", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trial_boq as T                      # noqa: E402  (R-T636-1, read only)
import manifest_v18 as M18                 # noqa: E402  (R-T649-1)

E, OV, M9 = T.E, T.OV, T.M9
D, S = T.D, T.S
SCHEMA, RULE = "URBAN_T649_TRIAL_BOQ_R2", "R-T649-2"
OUT_JSON = HERE / "out/TRIAL_BOQ_R2_T649.json"
OUT_MD = HERE / "out/TRIAL_BOQ_R2_T649.md"
OUT_CSV = HERE / "out/TRIAL_BOQ_R2_T649_LINES.csv"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.57.0.json"
V18 = HERE / "out/WIRING_MANIFEST_V18.json"
T636 = ROOT / "research/agents_t636/out/TRIAL_BOQ_T636.json"
BASELINE_HELD = (2314, 2750)               # T-636 trial of record: HELD with cause / HELD lines
STALE_B8_06 = "no verified piece integrated; the lines are the base run's"
MERGED_SINCE_V17 = {
    "T-642": "FR-T642-2 strip low end + companion, FR-T642-4 stamp (V18 STRIP_COL353)",
    "T-643": "4 Checker-validated downgrades (V18 CHECKER_DOWNGRADES)",
    "T-645": "16 stair finish fix rows (V18 STAIR_FINISH_HOLD_RELEASE) + F-T645-1 proposals",
    "T-646": "3 roof screed AT_LEAST rows (V18) + 40 census causes",
    "T-650": "lintel RC bounds chained in T-498 (V18) + 42 census causes; D-1F-07 / L-GF-01 re-measure pending",
    "T-633": "D-GF-06 statement-only class move",
    "T-525": "master 1.57.0 (this grouping); F-T525-1 reader correction",
}
OPEN_ROWS = (("STR.REBAR", "T-647 (TODO r2, B11 HELD causes)"), ("STR.", "T-647 (TODO r2, structural HELD causes)"),
             ("FIN.", "T-648 (READY, finishes HELD causes)"), ("EXT.", "T-648 (READY, finishes HELD causes)"),
             ("MAS.", "T-498 (READY, blockwork materials Gate B)"))


class TrialError(Exception):
    pass


def open_row(code):
    return next((r for p, r in OPEN_ROWS if code.startswith(p)), None)


def text_causes(order):
    """the cause a V18 TEXT_ONLY op names for a HELD line it leaves blank (re-measure pending, pair carried once)."""
    return {op["line_id"]: op["beside"]["cause"] for _, ops in order for op in ops
            if op["kind"] == "TEXT_ONLY" and op["op_id"].find("R-T650-1/") >= 0 and (op.get("beside") or {}).get("cause")}


def extra_records(t646, t650, named=None):
    """R-T649-2 (a): the merged T-646 / T-650 census causes, by line; a line V18 names (TEXT_ONLY) carries that text."""
    named = named or {}
    out = {}
    for l in t646["lines"]:
        if l.get("cause"):
            out.setdefault(l["line_id"], []).append(T._rec(646, "T-646 roof / fence hold census (merged af50c864)",
                                                           l["cause"], kind="T-646 roof / fence census"))
    for oid, v in t650["per_opening"].items():
        if v["line_id"] in named:
            out.setdefault(v["line_id"], []).append(T._rec(650, f"T-650 payable form {oid} (merged 2a2e28ca) as named "
                                                           "by V18 R-T649-1 (g)", f"{oid}: {named[v['line_id']]}",
                                                           kind="T-650 lintel payable-form census"))
        elif v.get("why"):
            out.setdefault(v["line_id"], []).append(T._rec(650, f"T-650 payable form {oid} (merged 2a2e28ca)",
                                                           f"{oid}: {v['why']}", kind="T-650 lintel payable-form census"))
    return out


def b8_06_correction(master):
    f = next(x for x in master["families"] if x["code"] == "B8-06")
    text = f["candidate"]["open"]
    parts = text.split(" | ")
    if not parts[0].startswith(STALE_B8_06) or len(parts) < 2:
        raise TrialError("F-T525-1: the B8-06 open text no longer carries the stale sentence: drop the correction")
    return {"family": "B8-06", "finding": "F-T525-1", "as_in_master_1_57_0": text, "stale_part": parts[0],
            "reads_as": " | ".join(parts[1:]),
            "why": "the promotion function keeps the earlier 'open' sentence of a family that left the base lines "
                   "(T-525 s. finding); state, packages, released and held figures are right; a no-quantity reader "
                   "correction, the master file is not edited"}


def overlay():
    idx, order, rul, after, rep, after17, rep17, rows, outs, src, t584 = M18.overlay_v18()
    v18 = T._json(V18)
    if len(after) != v18["overlay"]["lines"]["after_v18"]:
        raise TrialError("STALE_INPUT: the V18 rebuild differs from the committed V18 line count")
    t18 = OV.totals(after)
    for k, d in v18["overlay"]["v18_vs_v17_totals"].items():
        if t18.get(k) != d["after"]:
            raise TrialError(f"STALE_INPUT: V18 rebuild total {k} differs from the committed V18")
    return idx, order, after, rep, outs, src, v18


def build():
    master = T._json(MASTER)
    if master.get("version") != "1.57.0":
        raise TrialError("STALE_INPUT: BOQ_FAMILY_MASTER is not 1.57.0")
    src = T.load_sources()
    idx, order, after, rep, outs, src18, v18 = overlay()
    bound, base_ids = E.bindings(), set(idx)
    T.guard_held(after)
    ops = T.last_ops(order)
    owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded = E.aggregate(after, bound, order, master)
    checks = E.proof(after, item_acc, fam_acc, grp_acc, unit_acc)
    recs = T.census_records(src)
    ext, stale = T.extract_records(src, after)
    for k, v in list(ext.items()) + list(extra_records(src18["T646"], src18["T650"], text_causes(order)).items()):
        recs.setdefault(k, []).extend(v)
    causes = T.resolve_causes(after, ops, recs)
    proposals = {p["line_ids"][0]: p for p in outs["f_t645_1"]["proposals"]}
    for p in per_line:
        p["column"] = T.column_of(p["line_id"], after[p["line_id"]], ops.get(p["line_id"]), p["evidence"])
        p["origin"] = "overlay op" if p["line_id"] in ops else "candidate V3.0.58"
        if p["line_id"] in proposals:
            if p["class"] != "RELEASED":
                raise TrialError(f"{p['line_id']}: a downgrade proposal on a line that is not RELEASED")
            p["downgrade_proposed"] = proposals[p["line_id"]]["proposal_id"]
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
    if out["held"]["with_cause"] < BASELINE_HELD[0]:
        raise TrialError(f"HELD with cause fell: {out['held']['with_cause']} < the T-636 {BASELINE_HELD[0]}")
    t636 = T._json(T636)
    out.update({
        "schema": SCHEMA, "rule": RULE, "task": "T-649", "revision": "r2 (of the T-636 trial BOQ of record)",
        "overlay": "WIRING MANIFEST V18 (T-649, this package; V17 T-641 merged 57620ab8 + V18 rows)",
        "master": "BOQ_FAMILY_MASTER 1.57.0 (T-525, merged c7565fb9)",
        "merged_since_v17_not_in_overlay": {}, "merged_since_v17_in_overlay": MERGED_SINCE_V17,
        "inputs": {str(p.relative_to(ROOT)): T.sha256(p) for p in (MASTER, T.SCORECARD, V18, T.INDEX57, T636,
                                                                    *T.SRC.values(), *M18.IN.values())},
        "vs_t636": {"held_with_cause": [t636["held"]["with_cause"], out["held"]["with_cause"]],
                    "held_lines": [t636["held"]["lines"], out["held"]["lines"]],
                    "finding_F_T636_1": [t636["held"]["finding_F_T636_1"], out["held"]["finding_F_T636_1"]],
                    "released_lines": [t636["lines"]["released"], out["lines"]["released"]],
                    "lines": [t636["lines"]["after_v17"], len(after)]},
        "downgrade_proposals_not_applied": outs["f_t645_1"],
        "statement_only_ops": v18["statement_only_ops"],
        "registry_text_corrections": [b8_06_correction(master)],
    })
    out["lines"]["after_v18"] = out["lines"].pop("after_v17")
    out["contains"] = [c.replace("overlay V17", "overlay V18") for c in out["contains"]]
    return relabel(out)


OP_KIND_V17, OP_KIND_V18 = "overlay op (V17 manifest row)", "overlay op (V18 manifest row)"


def relabel(o):
    """the R-T636-1 op cause kind names its manifest; on r2 the ops are the V18 manifest's (label only)."""
    if isinstance(o, dict):
        return {(OP_KIND_V18 if k == OP_KIND_V17 else k): relabel(v) for k, v in o.items()}
    if isinstance(o, list):
        return [relabel(v) for v in o]
    return OP_KIND_V18 if o == OP_KIND_V17 else o


def dumps(o):
    return T.dumps(o)


def render_md(b):
    b0 = dict(b, lines=dict(b["lines"], after_v17=b["lines"]["after_v18"]))
    md = T.render_md(b0).replace("# T-636 the 10 Nov trial BOQ (generated; R-T636-1)",
                                "# T-649 the trial BOQ r2 (generated; R-T649-2 on R-T636-1)")
    md = md.replace("- Lines after V17:", "- Lines after V18:")
    v = b["vs_t636"]
    add = ["", "## 7. r2 changes against the T-636 trial of record", "",
           f"- HELD with cause {v['held_with_cause'][0]} -> {v['held_with_cause'][1]} of HELD lines "
           f"{v['held_lines'][0]} -> {v['held_lines'][1]}; F-T636-1 {v['finding_F_T636_1'][0]} -> "
           f"{v['finding_F_T636_1'][1]}; released lines {v['released_lines'][0]} -> {v['released_lines'][1]}.",
           "- Downgrade PROPOSED, not applied (F-T645-1): " + "; ".join(
               f"{x['line_id']} {x['item_code']} {x['released']} {x['unit']} ({x['proposal']}, goings "
               f"{x['goings_disputed'][0]} .. {x['goings_disputed'][1]})" for x in b["downgrade_proposals_not_applied"]["lines"]) + ".",
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
