"""SCOREBOARD V2 (task T-177) - the SCOREBOARD v2 table (owner session 2026-10-22 07:30, T-132) computed by script
instead of by hand. Builds on tools/alsenan_keymap.py (canonical lines -> scorer rows through the explicit key map) and
tools/alsenan_scoreboard.py (coverage / compared / WAPE / signed per trade and unit); both stay untouched and their
outputs byte-identical. Reads only; computes, changes and approves no engine quantity; nothing in engine/ imports it.
General: no project name, item code or reference id is written in this module; the key map and the verdict file are
the project's inputs.

Columns, exactly (the dashboard reads them):
| Trade | Unit | Baseline | Ref lines | Coverage % | Compared | WAPE % | Signed % | Verified share % | Held or UNKNOWN |
Rule difference share % |

One row per trade and unit and per scored side (a released baseline run, and optionally a candidate lines file scored
beside that run's release report). Definitions (each is a test in tests/t177_scoreboard_v2/):

- Held or UNKNOWN: per reference line whose outcome is HELD, the same-unit engine rows answering it that are not
  released (tools/alsenan_keymap.py `line_status`: a line outside MEASURED / SOURCE_DERIVED / PROVISIONAL-with-
  measured_net), split into lines with a complete bounded_range {low, high} (summed low .. high, in the line's unit)
  and lines without one (counted UNKNOWN, never 0); every CONDITIONAL scenario set that holds the key is counted apart
  (quantity UNKNOWN); lines excluded with evidence (NOT_APPLICABLE_WITH_EVIDENCE / EXCLUDED_WITH_REASON) are counted
  apart and never become a quantity. A reference line refused for unit (UNIT_MISMATCH) or never answered (silent
  omission) has no held quantity in its unit: the cell says NOT YET MEASURED with the reason. Released lines inside a
  held reference line are reported in the JSON (`released_part`) and never compared.
- Verified share = reference lines whose WHOLE engine quantity a checker verdict re-measured from the drawing / all
  reference lines of the trade and unit. Input: a checker verdict file (URBAN_SCOREBOARD_CHECKER_VERDICTS_V1). A
  re-measure counts only when: kind REMEASURE, scope WHOLE, method CHECKER_REMEASURE_FROM_DRAWING (freelancer agreement
  is refused as a method), a source citation and a commit (the board commit that records the verdict, or the
  merged commit it was made on) are given, the line is COMPARED in this run (its whole
  engine quantity released, same unit), the verdict's engine_qty equals this run's engine quantity (abs. difference
  <= QTY_MATCH_TOL: a verdict on another quantity is STALE, never transferred) and the checker's own qty is within 1 %
  of it (WORKFLOW_CONTROLS s.1: a larger difference is a DISCREPANCY that holds the line, never verified). Every
  verdict that does not count is listed with its reason.
- Rule difference share = reference lines with a standing whole-scope RULE_DIFFERENCE verdict / all reference lines
  of the trade and unit; NOT YET MEASURED while the bucket has no whole-scope rule assessment (RULE_DIFFERENCE or
  NO_RULE_DIFFERENCE) at all. PARTIAL verdicts are listed and never counted.
- Coverage, Compared, WAPE, Signed: tools/alsenan_scoreboard.py `score` unchanged (2 decimals; WAPE / Signed NOT YET
  MEASURED when nothing is compared). HELD / UNKNOWN are never counted correct.

Baseline cell: the --label given, plus provenance read from the files: for a run directory with a
BASELINE_MANIFEST.json (the T-165 baseline runner), "manifest <sha8>, BOQ_LINES.csv <sha8>" after checking that the
BOQ_LINES.json scored has the sha256 the manifest records (refused otherwise); for a candidate lines file, its own
sha8 (and the sha8 of a sibling .csv of the same stem when one exists).

CLI (also through tools/alsenan_keymap.py --v2-* options, which the agent wrapper may run):
    python3 -I tools/scoreboard_v2.py --run RUN_DIR --label "A (released ...)" --reference BENCHMARK_NORMALISED.json
        --key-map KEY_MAP.json --verdicts VERDICTS.json [--candidate-lines V3_0_x_BOQ_LINES.json
        --candidate-label "..."] --out OUT.json [--markdown OUT.md] [--heading "YYYY-MM-DD HH:MM UTC"]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import alsenan_keymap as K      # noqa: E402
from tools import alsenan_scoreboard as S  # noqa: E402

SCHEMA = "URBAN_SCOREBOARD_V2"
VERDICTS_SCHEMA = "URBAN_SCOREBOARD_CHECKER_VERDICTS_V1"
COLUMNS = ("Trade", "Unit", "Baseline", "Ref lines", "Coverage %", "Compared", "WAPE %", "Signed %",
           "Verified share %", "Held or UNKNOWN", "Rule difference share %")
NYM = "NOT YET MEASURED"
QTY_MATCH_TOL = 0.0005          # the engine quantity a verdict re-measured must be this run's quantity
DISCREPANCY_REL = 0.01          # WORKFLOW_CONTROLS s.1: hand vs engine above 1 % -> investigate, the line is HELD

KINDS = ("REMEASURE", "RULE_DIFFERENCE", "NO_RULE_DIFFERENCE")
SCOPES = ("WHOLE", "PARTIAL")
REMEASURE_METHOD = "CHECKER_REMEASURE_FROM_DRAWING"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _nonempty(v):
    return bool(str(v or "").strip())


# ---- checker verdict file -------------------------------------------------------------------------------------------

def load_verdicts(doc, reference_ids):
    """Validated verdict records. Refuses (ValueError) a wrong schema, an unknown kind / scope, a missing citation, a
    re-measure whose method is not the checker's own drawing re-measure, an unknown reference id and two whole-scope
    verdicts of one kind on one reference line."""
    if doc is None:
        return []
    if doc.get("schema") != VERDICTS_SCHEMA:
        raise ValueError(f"verdict file schema {doc.get('schema')!r} is not {VERDICTS_SCHEMA}")
    out, seen = [], set()
    for i, v in enumerate(doc.get("verdicts") or []):
        where = f"verdict {i} ({v.get('ref_id')!r})"
        if v.get("ref_id") not in reference_ids:
            raise ValueError(f"{where}: reference id not in the reference rows")
        if v.get("kind") not in KINDS:
            raise ValueError(f"{where}: kind {v.get('kind')!r} not in {KINDS}")
        if v.get("scope") not in SCOPES:
            raise ValueError(f"{where}: scope {v.get('scope')!r} not in {SCOPES}")
        if not _nonempty(v.get("source")) or not _nonempty(v.get("commit")):
            raise ValueError(f"{where}: a verdict needs its source (board note / file:line) and its commit")
        if v["kind"] == "REMEASURE":
            if v.get("method") != REMEASURE_METHOD:
                raise ValueError(f"{where}: method {v.get('method')!r} is not {REMEASURE_METHOD} "
                                 "(freelancer agreement never counts as verification)")
            if v["scope"] == "WHOLE":
                for f in ("unit", "engine_qty", "checker_qty"):
                    if v.get(f) is None:
                        raise ValueError(f"{where}: a whole-scope re-measure needs {f}")
                S._qty(v["engine_qty"], where)
                S._qty(v["checker_qty"], where)
        if v["scope"] == "WHOLE":
            k = (v["ref_id"], "RULE" if v["kind"] != "REMEASURE" else "REMEASURE")
            if k in seen:
                raise ValueError(f"{where}: a second whole-scope {k[1]} verdict on one reference line")
            seen.add(k)
        out.append(v)
    return out


def _remeasure_status(v, line):
    """(counts, reason) of one re-measure verdict against this run's line result."""
    if v["scope"] != "WHOLE":
        return False, "PARTIAL_SCOPE"
    if line["outcome"] != S.OUT_COMPARED:
        return False, f"LINE_NOT_COMPARED ({line['outcome']})"
    if S.norm_unit(v["unit"]) != line["unit"]:
        return False, "UNIT_DIFFERS"
    eq = line["engine_qty"]
    if abs(float(v["engine_qty"]) - eq) > QTY_MATCH_TOL:
        return False, f"STALE (verdict engine_qty {v['engine_qty']} != this run {eq:.3f})"
    cq = float(v["checker_qty"])
    if eq == 0 or abs(cq - eq) / abs(eq) > DISCREPANCY_REL:
        return False, "DISCREPANCY (checker vs engine above 1 %: the line is HELD, not verified)"
    return True, "COUNTED"


# ---- one scored side --------------------------------------------------------------------------------------------------

def score_side(lines, release_report, normalised_doc, key_map_doc, verdicts_doc, label, provenance=""):
    """The v2 rows of one side (a run, or candidate lines beside a base run's release report)."""
    eng, adapter = K.engine_rows(lines, release_report, key_map_doc)
    ref = K.reference_rows(normalised_doc, key_map_doc)
    result = S.score(eng, ref)
    bounds = {ln["line_id"]: (ln.get("bounded_range") or {}) for ln in lines}
    cls = {e["id"]: S.release_class(e["status"]) for e in eng}
    eqty = {e["id"]: e["qty"] for e in eng}
    verdicts = load_verdicts(verdicts_doc, {r["id"] for r in ref})
    by_ref = {}
    for v in verdicts:
        by_ref.setdefault(v["ref_id"], []).append(v)
    _, by_key = K.load_key_map(key_map_doc)
    excluded = adapter["excluded_lines_by_key"]

    buckets = {}
    audit = []
    for ln in result["lines"]:
        b = buckets.setdefault((ln["trade"], ln["unit"]), {
            "trade": ln["trade"], "unit": ln["unit"], "ref_lines": 0, "held_ref_lines": 0, "bounded_lines": 0,
            "bounded_low": 0.0, "bounded_high": 0.0, "unknown_lines": 0, "conditional_sets": 0, "excluded_lines": 0,
            "released_part_lines": 0, "released_part_qty": 0.0, "not_measured": [], "verified": 0,
            "rule_difference": 0, "rule_assessed": 0, "partial_remeasures": 0, "partial_rule_verdicts": 0})
        b["ref_lines"] += 1
        b["excluded_lines"] += excluded.get(ln["key"], 0)
        out = ln["outcome"]
        if out == S.OUT_HELD:
            b["held_ref_lines"] += 1
            for eid in ln["engine_ids"]:
                if cls[eid] == S.RELEASED:
                    b["released_part_lines"] += 1
                    b["released_part_qty"] += eqty[eid]
                elif eid.startswith("COND:"):
                    b["conditional_sets"] += 1
                else:
                    br = bounds.get(eid) or {}
                    if br.get("low") is not None and br.get("high") is not None:
                        b["bounded_lines"] += 1
                        b["bounded_low"] += float(br["low"])
                        b["bounded_high"] += float(br["high"])
                    else:
                        b["unknown_lines"] += 1
        elif out == S.OUT_UNIT_MISMATCH:
            units = sorted({str(e["unit"]) for e in eng if e["id"] in set(ln["refused_engine_ids"])})
            b["not_measured"].append(f"unit refused: the engine answers {ln['key']} in {', '.join(units)}, "
                                     f"the reference in {ln['unit']}")
        elif out == S.OUT_SILENT:
            b["not_measured"].append(f"silent omission: no engine line answers {ln['key']}")
        elif out == S.OUT_UNSUPPORTED:
            b["not_measured"].append(f"unsupported: {ln['key']}")
        elif out == S.OUT_REF_UNIT_MISSING:
            b["not_measured"].append(f"reference unit missing: {ln['key']}")
        for v in by_ref.get(ln["ref_id"], []):
            if v["scope"] == "PARTIAL":
                b["partial_remeasures" if v["kind"] == "REMEASURE" else "partial_rule_verdicts"] += 1
                audit.append({"ref_id": ln["ref_id"], "kind": v["kind"], "counted": False, "reason": "PARTIAL_SCOPE",
                              "source": v["source"]})
                continue
            if v["kind"] == "REMEASURE":
                ok, why = _remeasure_status(v, ln)
                b["verified"] += ok
            else:
                ok, why = True, "COUNTED"
                b["rule_assessed"] += 1
                b["rule_difference"] += v["kind"] == "RULE_DIFFERENCE"
            audit.append({"ref_id": ln["ref_id"], "kind": v["kind"], "counted": ok, "reason": why,
                          "source": v["source"], "commit": v["commit"]})

    score_by = {(x["trade"], x["unit"]): x for x in result["buckets"]}
    rows = []
    for key in sorted(buckets, key=lambda k: (str(k[0]), str(k[1]))):
        b = buckets[key]
        s = score_by[key]
        b["cells"] = _cells(b, s, label + provenance)
        rows.append(b)
    return {"label": label, "provenance": provenance.lstrip(", "), "rows": rows, "verdict_audit": audit,
            "score": result, "adapter": adapter}


def _f2(x):
    return NYM if x is None else f"{100.0 * x:.2f}"


def _q(x):
    return f"{x:.3f}"


def held_text(b):
    """The Held or UNKNOWN cell; never 0 for a held line."""
    parts = []
    if b["held_ref_lines"]:
        n = b["held_ref_lines"]
        head = f"{n} ref line{'s' if n != 1 else ''} HELD"
        eng = []
        m = b["bounded_lines"] + b["unknown_lines"]
        if b["bounded_lines"]:
            eng.append(f"{b['bounded_lines']} bounded {_q(b['bounded_low'])} .. {_q(b['bounded_high'])} {b['unit']}")
        if b["unknown_lines"]:
            eng.append(f"{b['unknown_lines']} UNKNOWN (no bound)")
        if m:
            head += f"; {m} engine line{'s' if m != 1 else ''}: " + " + ".join(eng)
        if b["conditional_sets"]:
            c = b["conditional_sets"]
            head += f"; {c} conditional review set{'s' if c != 1 else ''}, quantity UNKNOWN (no bound)"
        parts.append(head)
    if b["excluded_lines"] and b["held_ref_lines"]:
        parts.append(f"{b['excluded_lines']} more excluded with reason")
    for t in b["not_measured"]:
        parts.append(f"{NYM} ({t})")
    if not parts:
        return "0 ref lines HELD"
    return "; ".join(parts)


def _cells(b, s, baseline):
    n = b["ref_lines"]
    verified = f"{100.0 * b['verified'] / n:.2f} ({b['verified']} / {n})"
    p = b["partial_remeasures"]
    if p:
        verified += f"; {p} partial re-measure{'s' if p != 1 else ''} not counted"
    rule = (NYM if not b["rule_assessed"] else f"{100.0 * b['rule_difference'] / n:.2f} ({b['rule_difference']} / {n})")
    p = b["partial_rule_verdicts"]
    if p:
        rule += f" ({p} partial rule verdict{'s' if p != 1 else ''} not counted)"
    return [str(b["trade"]), str(b["unit"]), baseline, str(n), _f2(s["coverage"]), str(s["compared"]),
            _f2(s["wape"]), _f2(s["signed_error_ratio"]), verified, held_text(b), rule]


# ---- inputs -----------------------------------------------------------------------------------------------------------

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_provenance(run_dir):
    """', manifest <sha8>, BOQ_LINES.csv <sha8>' for a run with a BASELINE_MANIFEST.json, after checking that the
    BOQ_LINES.json scored is the one the manifest records; '' for a run without a manifest."""
    run_dir = Path(run_dir)
    man = run_dir / "BASELINE_MANIFEST.json"
    if not man.exists():
        return ""
    doc = _load(man)
    outs = (doc.get("run") or {}).get("outputs_sha256") or {}
    want = outs.get("BOQ_LINES.json")
    if want is None or _sha(run_dir / "BOQ_LINES.json") != want:
        raise ValueError(f"{man.name}: BOQ_LINES.json sha256 differs from the manifest (a drifted or foreign run)")
    csv = outs.get("BOQ_LINES.csv")
    return f", manifest {_sha(man)[:8]}" + (f", BOQ_LINES.csv {csv[:8]}" if csv else "")


def lines_provenance(lines_path):
    p = Path(lines_path)
    out = f", {p.name} {_sha(p)[:8]}"
    csv = p.with_suffix(".csv")
    if csv.exists():
        out += f", {csv.name} {_sha(csv)[:8]}"
    return out


def build(run_dir, label, normalised_doc, key_map_doc, verdicts_doc, candidate_lines=None, candidate_label=None):
    """Score the run (and the candidate lines beside the run's release report) into one SCOREBOARD v2 result."""
    run_dir = Path(run_dir)
    rel_path = run_dir / "BOQ_RELEASE_REPORT.json"
    rel = _load(rel_path) if rel_path.exists() else None
    sides = [score_side(_load(run_dir / "BOQ_LINES.json"), rel, normalised_doc, key_map_doc, verdicts_doc, label,
                        run_provenance(run_dir))]
    if candidate_lines is not None:
        if not _nonempty(candidate_label):
            raise ValueError("a candidate needs its label")
        sides.append(score_side(_load(candidate_lines), rel, normalised_doc, key_map_doc, verdicts_doc,
                                candidate_label, lines_provenance(candidate_lines)))
    return {"SCHEMA": SCHEMA, "columns": list(COLUMNS), "release_report_present": rel is not None,
            "sides": [{k: v for k, v in s.items() if k != "score"} | {"buckets_v1": s["score"]["buckets"]}
                      for s in sides],
            "rule": "per trade and unit, never mixed; HELD / UNKNOWN never 0 and never counted correct; verified "
                    "share only from whole-scope checker re-measures of this run's quantity; development reference "
                    "only, no product accuracy claim"}


def markdown(result, heading=None):
    """The SCOREBOARD v2 table: rows grouped by trade and unit, one per side in side order."""
    out = []
    if heading:
        out += [f"## SCOREBOARD v2 {heading}", ""]
    out.append("| " + " | ".join(COLUMNS) + " |")
    out.append("|" + "---|" * len(COLUMNS))
    keys = []
    for s in result["sides"]:
        for r in s["rows"]:
            if (r["trade"], r["unit"]) not in keys:
                keys.append((r["trade"], r["unit"]))
    for k in keys:
        for s in result["sides"]:
            for r in s["rows"]:
                if (r["trade"], r["unit"]) == k:
                    out.append("| " + " | ".join(c.replace("|", "/") for c in r["cells"]) + " |")
    return "\n".join(out) + "\n"


def write(result, out, md_path=None, heading=None):
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md = markdown(result, heading)
    if md_path:
        Path(md_path).write_text(md, encoding="utf-8")
    return md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--key-map", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--candidate-lines")
    ap.add_argument("--candidate-label")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--heading")
    a = ap.parse_args(argv)
    result = build(a.run, a.label, _load(a.reference), _load(a.key_map), _load(a.verdicts), a.candidate_lines,
                   a.candidate_label)
    print(write(result, a.out, a.markdown, a.heading), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
