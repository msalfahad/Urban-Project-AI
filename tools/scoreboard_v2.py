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
        [--layout five --min-accuracy-scope 0.50]

FIVE MEASURES layout (task T-182, owner scoreboard review 2026-10-22; opt-in `layout=LAYOUT_FIVE`, heading
"## SCOREBOARD v2.1 <time>"; the default layout above and its JSON stay byte-identical). The five measures are kept
apart, each with its numerator and denominator, and released / candidate sides are always separate rows:

| Trade | Unit | Baseline | Ref lines | Coverage % (n / d) | Verified n / d | Accuracy vs independent (lines, scope
share) | Freelancer variance | Held or UNKNOWN | Rule difference share % |

1. Coverage % (n / d): reference lines the engine answers (compared, held, unsupported, released without a reference
   quantity) / reference lines; tools/alsenan_scoreboard.py `covered` unchanged.
2. Verified n / d: exactly the T-177 Verified share (whole-scope checker re-measures of THIS side's compared quantity,
   within 1 %); nothing else raises it (a partial re-measure, a rule verdict, a re-measure of another line, a stale or
   discrepant re-measure, freelancer agreement).
3. Accuracy vs independent: engine against the CHECKER's own quantity, never against the freelancer. Lines: every
   reference line with a whole-scope checker re-measure in the line's unit whose engine quantity is released on this
   side (outcome COMPARED or REFERENCE_QTY_MISSING); a discrepant (> 1 %) or stale re-measure is INCLUDED (the checker
   quantity is a property of the element, not of the engine run; leaving discrepancies out would flatter the figure);
   a HELD line has no engine quantity and is listed, never 0. WAPE = sum |engine - checker| / sum checker, signed =
   sum (engine - checker) / sum checker. Scope share = sum checker quantity of those lines / the trade-and-unit size,
   where each reference line's size is its checker quantity when one exists, else this side's released engine
   quantity; the freelancer's quantity is never a weight (so a smaller freelancer variance can never move this
   column). A reference line with neither (HELD / unit refused / silent) leaves the size incomplete: the share is
   then only an upper bound and the cell says NOT YET MEASURED. Rule: reported only when at least one line, the size
   is complete and the share >= MIN_ACCURACY_SCOPE (0.50, an initial operational value like the WORKFLOW_CONTROLS s.1
   thresholds, for the Lead / owner to review; --min-accuracy-scope); otherwise NOT YET MEASURED with the reason.
4. Freelancer variance: the v1 WAPE / signed against the freelancer on the compared lines, with compared / reference
   lines; a comparison, not accuracy (the freelancer is not ground truth).
5. Held or UNKNOWN: the T-177 cell unchanged (bounded sums, UNKNOWN, conditional sets, NOT YET MEASURED causes).
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

LAYOUT_V2 = "V2"
LAYOUT_FIVE = "FIVE_MEASURES"
COLUMNS_FIVE = ("Trade", "Unit", "Baseline", "Ref lines", "Coverage % (n / d)", "Verified n / d",
                "Accuracy vs independent (lines, scope share)", "Freelancer variance", "Held or UNKNOWN",
                "Rule difference share %")
HEADING_FIVE = "SCOREBOARD v2.1"
MIN_ACCURACY_SCOPE = 0.50       # initial operational value (T-182); the Lead / owner review it with actual results
ACCURACY_OUTCOMES = (S.OUT_COMPARED, S.OUT_REF_QTY_MISSING)   # the side's whole engine quantity is released
FIVE_RULES = ("five measures kept apart (T-182): coverage = answered / reference lines; verified = whole-scope checker "
              "re-measures of this side's compared quantity within 1 %, nothing else raises it; accuracy = engine vs "
              "the checker's own quantity (discrepant and stale re-measures included, held lines listed, never 0), "
              "scope share = checker quantity of those lines / sizes of all reference lines (checker quantity, else "
              "this side's released engine quantity; never the freelancer's), reported only with a complete size and "
              "share >= the minimum; freelancer variance = comparison only, never accuracy; released and candidate "
              "sides never combined")

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

def score_side(lines, release_report, normalised_doc, key_map_doc, verdicts_doc, label, provenance="",
               layout=LAYOUT_V2, min_scope=MIN_ACCURACY_SCOPE):
    """The v2 rows of one side (a run, or candidate lines beside a base run's release report); layout LAYOUT_FIVE
    gives the T-182 five-measures cells and an accuracy_audit."""
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
    five = layout == LAYOUT_FIVE
    if layout not in (LAYOUT_V2, LAYOUT_FIVE):
        raise ValueError(f"layout {layout!r} not in {(LAYOUT_V2, LAYOUT_FIVE)}")
    acc_audit = _accuracy(result["lines"], by_ref, buckets, min_scope) if five else None
    rows = []
    for key in sorted(buckets, key=lambda k: (str(k[0]), str(k[1]))):
        b = buckets[key]
        s = score_by[key]
        b["cells"] = _cells_five(b, s, label + provenance) if five else _cells(b, s, label + provenance)
        rows.append(b)
    out = {"label": label, "provenance": provenance.lstrip(", "), "rows": rows, "verdict_audit": audit,
           "score": result, "adapter": adapter}
    if five:
        out["accuracy_audit"] = acc_audit
    return out


# ---- T-182: accuracy against the checker's independent quantity --------------------------------------------------------

def _accuracy(result_lines, by_ref, buckets, min_scope):
    """Fill b['accuracy'] per bucket; return the per-line audit. Never reads the freelancer quantity."""
    if not (0.0 < float(min_scope) <= 1.0):
        raise ValueError(f"minimum accuracy scope {min_scope!r} must be in (0, 1]")
    audit = []
    for b in buckets.values():
        b["accuracy"] = {"lines": 0, "sum_checker": 0.0, "sum_abs": 0.0, "sum_signed": 0.0, "stale_lines": 0,
                         "discrepant_lines": 0, "independent_not_compared": 0, "size_known": 0.0,
                         "size_unknown_lines": 0, "min_scope": float(min_scope)}
    for ln in result_lines:
        a = buckets[(ln["trade"], ln["unit"])]["accuracy"]
        whole = [v for v in by_ref.get(ln["ref_id"], [])
                 if v["kind"] == "REMEASURE" and v["scope"] == "WHOLE" and S.norm_unit(v["unit"]) == ln["unit"]]
        v = whole[0] if whole else None      # load_verdicts allows one whole re-measure per reference line
        released = ln["outcome"] in ACCURACY_OUTCOMES and ln["engine_qty"] is not None
        if v is not None:
            c = float(v["checker_qty"])
            a["size_known"] += c
            rec = {"ref_id": ln["ref_id"], "outcome": ln["outcome"], "checker_qty": c, "engine_qty": ln["engine_qty"],
                   "source": v["source"], "commit": v["commit"]}
            if not released:
                a["independent_not_compared"] += 1
                audit.append(rec | {"counted": False, "reason": f"NO_RELEASED_ENGINE_QTY ({ln['outcome']}): the "
                                                                "line stays HELD, never 0"})
                continue
            e = float(ln["engine_qty"])
            a["lines"] += 1
            a["sum_checker"] += c
            a["sum_abs"] += abs(e - c)
            a["sum_signed"] += e - c
            stale = abs(float(v["engine_qty"]) - e) > QTY_MATCH_TOL
            disc = c == 0 or abs(e - c) / abs(c) > DISCREPANCY_REL
            a["stale_lines"] += stale
            a["discrepant_lines"] += disc
            audit.append(rec | {"counted": True, "reason": "COUNTED" + (" (stale: re-measured against another engine "
                                                                        "quantity)" if stale else "")
                                + (" (discrepancy above 1 %)" if disc else "")})
        elif released:
            a["size_known"] += float(ln["engine_qty"])
        else:
            a["size_unknown_lines"] += 1
    for b in buckets.values():
        a = b["accuracy"]
        a["scope_share"] = (a["sum_checker"] / a["size_known"]) if a["size_known"] > 0 else None
        a["size_complete"] = a["size_unknown_lines"] == 0
        ok = (a["lines"] > 0 and a["sum_checker"] > 0 and a["size_complete"] and a["scope_share"] is not None
              and a["scope_share"] + 1e-12 >= a["min_scope"])
        a["reported"] = ok
        a["wape"] = a["sum_abs"] / a["sum_checker"] if ok else None
        a["signed"] = a["sum_signed"] / a["sum_checker"] if ok else None
    return audit


def accuracy_text(b):
    """The Accuracy vs independent cell; NOT YET MEASURED unless the scope rule is met."""
    a, u = b["accuracy"], b["unit"]
    n = a["lines"]
    head = f"{n} line{'s' if n != 1 else ''}"
    extra = []
    if a["discrepant_lines"]:
        extra.append(f"{a['discrepant_lines']} above 1 %")
    if a["stale_lines"]:
        extra.append(f"{a['stale_lines']} stale")
    if a["independent_not_compared"]:
        k = a["independent_not_compared"]
        extra.append(f"{k} checker-measured line{'s' if k != 1 else ''} HELD in the engine, not counted")
    tail = ("; " + "; ".join(extra)) if extra else ""
    mn = f"{100.0 * a['min_scope']:.0f} %"
    if n == 0:
        return f"{NYM} (0 lines with an independent checker quantity{tail})"
    share = f"{100.0 * a['scope_share']:.2f} % = {_q(a['sum_checker'])} / {_q(a['size_known'])} {u}"
    if not a["size_complete"]:
        k = a["size_unknown_lines"]
        return (f"{NYM} ({head}; scope at most {share}: {k} ref line{'s' if k != 1 else ''} without a quantity "
                f"independent of the freelancer{tail})")
    if not a["reported"]:
        return f"{NYM} ({head}; scope {share}, below the {mn} minimum{tail})"
    return (f"WAPE {100.0 * a['wape']:.2f} %, signed {100.0 * a['signed']:.2f} % ({head}; scope {share}, "
            f"minimum {mn}{tail})")


def _cells_five(b, s, baseline):
    n = b["ref_lines"]
    cov = NYM if not n else f"{100.0 * s['covered'] / n:.2f} ({s['covered']} / {n})"
    verified = f"{b['verified']} / {n} ({100.0 * b['verified'] / n:.2f} %)"
    p = b["partial_remeasures"]
    if p:
        verified += f"; {p} partial re-measure{'s' if p != 1 else ''} not counted"
    k = s["compared"]
    var = (f"{NYM} (0 / {n} compared)" if not k or s["wape"] is None else
           f"WAPE {_f2(s['wape'])} %, signed {_f2(s['signed_error_ratio'])} % ({k} / {n} compared)")
    rule = (NYM if not b["rule_assessed"] else f"{100.0 * b['rule_difference'] / n:.2f} ({b['rule_difference']} / {n})")
    p = b["partial_rule_verdicts"]
    if p:
        rule += f" ({p} partial rule verdict{'s' if p != 1 else ''} not counted)"
    return [str(b["trade"]), str(b["unit"]), baseline, str(n), cov, verified, accuracy_text(b), var, held_text(b),
            rule]


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


def build(run_dir, label, normalised_doc, key_map_doc, verdicts_doc, candidate_lines=None, candidate_label=None,
          layout=LAYOUT_V2, min_scope=MIN_ACCURACY_SCOPE):
    """Score the run (and the candidate lines beside the run's release report) into one SCOREBOARD v2 result
    (layout LAYOUT_FIVE: the T-182 five-measures table)."""
    run_dir = Path(run_dir)
    five = layout == LAYOUT_FIVE
    kw = {"layout": layout, "min_scope": min_scope} if five else {"layout": layout}
    rel_path = run_dir / "BOQ_RELEASE_REPORT.json"
    rel = _load(rel_path) if rel_path.exists() else None
    sides = [score_side(_load(run_dir / "BOQ_LINES.json"), rel, normalised_doc, key_map_doc, verdicts_doc, label,
                        run_provenance(run_dir), **kw)]
    if candidate_lines is not None:
        if not _nonempty(candidate_label):
            raise ValueError("a candidate needs its label")
        if five and candidate_label.strip() == str(label).strip():
            raise ValueError("the candidate label equals the released label: the two sides are never combined")
        sides.append(score_side(_load(candidate_lines), rel, normalised_doc, key_map_doc, verdicts_doc,
                                candidate_label, lines_provenance(candidate_lines), **kw))
    res = {"SCHEMA": SCHEMA, "columns": list(COLUMNS_FIVE if five else COLUMNS), "release_report_present": rel is not None,
           "sides": [{k: v for k, v in s.items() if k != "score"} | {"buckets_v1": s["score"]["buckets"]}
                     for s in sides],
           "rule": "per trade and unit, never mixed; HELD / UNKNOWN never 0 and never counted correct; verified "
                   "share only from whole-scope checker re-measures of this run's quantity; development reference "
                   "only, no product accuracy claim"}
    if five:
        res |= {"layout": LAYOUT_FIVE, "min_accuracy_scope": float(min_scope), "five_measures_rule": FIVE_RULES}
    return res


def markdown(result, heading=None):
    """The SCOREBOARD v2 table: rows grouped by trade and unit, one per side in side order (the T-182 layout under
    '## SCOREBOARD v2.1', which the T-132 dashboard parser of '## SCOREBOARD v2 ' does not pick up by mistake)."""
    five = result.get("layout") == LAYOUT_FIVE
    cols = COLUMNS_FIVE if five else COLUMNS
    out = []
    if heading:
        out += [f"## {HEADING_FIVE if five else 'SCOREBOARD v2'} {heading}", ""]
    out.append("| " + " | ".join(cols) + " |")
    out.append("|" + "---|" * len(cols))
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
    ap.add_argument("--layout", choices=("v2", "five"), default="v2",
                    help="five = the T-182 five-measures table (## SCOREBOARD v2.1)")
    ap.add_argument("--min-accuracy-scope", type=float, help=f"default {MIN_ACCURACY_SCOPE} (layout five only)")
    a = ap.parse_args(argv)
    if a.layout != "five" and a.min_accuracy_scope is not None:
        ap.error("--min-accuracy-scope needs --layout five")
    extra = {} if a.layout != "five" else {"layout": LAYOUT_FIVE, "min_scope": (
        MIN_ACCURACY_SCOPE if a.min_accuracy_scope is None else a.min_accuracy_scope)}
    result = build(a.run, a.label, _load(a.reference), _load(a.key_map), _load(a.verdicts), a.candidate_lines,
                   a.candidate_label, **extra)
    print(write(result, a.out, a.markdown, a.heading), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
