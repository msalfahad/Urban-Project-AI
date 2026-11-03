"""PROJECT SCOREBOARD (task T-452, owner directive 2026-11-02 A4) - the project-agnostic key map and scoreboard: any
project in its own folder (drawings -> an engine run, plus its freelancer workbook normalised into reference rows) is
scored from ONE manifest file, with no code change per project. Read only: imports no module that computes a quantity,
changes no quantity, writes only --out / --markdown.

Inputs (URBAN_PROJECT_SCORE_MANIFEST_V1, paths relative to the manifest; --run / --candidate-lines override):
    {"SCHEMA", "project_id", "label", "source_folder" (Drive folder title only, never content),
     "run": RUN_DIR (BOQ_LINES.json [+ BOQ_RELEASE_REPORT.json]), "run_label",
     "candidate_lines"?: canonical lines scored beside the run's release report, "candidate_label"?,
     "reference": normalised workbook {"records": [{id, row_kind, unit, qty, ...}]} (the ORIGINAL freelancer workbook),
     "key_map": URBAN_PROJECT_KEY_MAP_V1 (or a legacy training-villa map URBAN_ALSENAN_KEY_MAP_V1 / V2),
     "reconciled_reference"?: URBAN_CHECKER_REFERENCES_V1 (the Checker's own drawing-based reference per line),
     "pricing_basis"?: URBAN_PRICING_BASIS_V1 (ONE approved, dated basis for both sides),
     "set_bindings"?: URBAN_SCORER_SET_BINDINGS_V1 (T-216 opt-in, unchanged),
     "high_value_keys"?: [key, ...] (line-level view), "tolerance_pct"?: default 3.0 (MISSION Goal B)}

The score itself is NOT re-implemented: each side is scored by tools/alsenan_keymap.py engine_rows / reference_rows and
tools/alsenan_scoreboard.py score (their rules are project-independent; only their file names are historical), so the
training villa's table is reproduced byte for byte (result["sides"][i]["score"] == alsenan_keymap.run(...), markdown
section == its markdown). Added on top (MISSION 'Goal B acceptance', owner follow-up 2026-11-02), each a test in
tests/t452_project_scoreboard:
- BOTH variances per key and per trade and unit: against the ORIGINAL workbook and against the RECONCILED reference,
  (engine - reference) / reference x 100. A reconciled record is used only when it is this project's, VERIFIED, in the
  key's unit and of exactly the key's item codes; otherwise it is listed (NOT_VERIFIED / SCOPE_MISMATCH / FOREIGN) and
  the original is NEVER substituted for it.
- Exception classes, never a division by zero, never a silent drop:
  ZERO_REFERENCE (reference qty 0: absolute difference only), REFERENCE_ONLY (a reference line with no engine answer,
  or a reference row of the keyed kinds that no key names), ENGINE_ONLY (an engine key with no reference line, an
  unmapped engine item code, a line in a unit no reference can use), SCOPE_MISMATCH (unit refused or missing, or the
  engine excludes the key with evidence while the reference carries quantity, or a reconciled record of another scope).
  HELD / UNSUPPORTED keys keep their class: no variance, never 0.
- Quantity AND cost: cost = qty x the basis rate of the key, the SAME rate on both sides; a trade's cost variance is
  given only when every compared key of the trade is priced (otherwise INCOMPLETE_PRICING with the unpriced keys);
  without an approved basis every cost is NO_APPROVED_PRICING_BASIS (never assumed). Quantity variance is always
  reported beside cost, so a low rate never hides an excessive quantity.
- Line-level view of the high-value keys, and OFFSETTING_ERRORS on a trade and unit whose total is within tolerance
  while one of its compared lines is not (a right total from offsetting errors fails).

CLI: python3 -I tools/project_scoreboard.py --manifest MANIFEST.json --out OUT.json [--markdown OUT.md]
     [--run RUN_DIR] [--candidate-lines LINES.json --candidate-label LABEL]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import alsenan_keymap as K      # noqa: E402  (key -> engine rows, reference rows; unchanged)
from tools import alsenan_scoreboard as S  # noqa: E402  (the scorer; unchanged)

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212 property P1: a read-only scorer; comparison only, it produces no quantity

SCHEMA = "URBAN_PROJECT_SCOREBOARD_V1"
MANIFEST_SCHEMA = "URBAN_PROJECT_SCORE_MANIFEST_V1"
KEY_MAP_SCHEMA = "URBAN_PROJECT_KEY_MAP_V1"
LEGACY_KEY_MAPS = ("URBAN_ALSENAN_KEY_MAP_V1", K.KEY_MAP_V2_SCHEMA)
RECONCILED_SCHEMA = "URBAN_CHECKER_REFERENCES_V1"
PRICING_SCHEMA = "URBAN_PRICING_BASIS_V1"
DEFAULT_TOLERANCE_PCT = 3.0

ZERO_REFERENCE, ENGINE_ONLY, REFERENCE_ONLY, SCOPE_MISMATCH = (
    "ZERO_REFERENCE", "ENGINE_ONLY", "REFERENCE_ONLY", "SCOPE_MISMATCH")
EXCEPTION_CLASSES = (ZERO_REFERENCE, ENGINE_ONLY, REFERENCE_ONLY, SCOPE_MISMATCH)
REC_USED, REC_NONE, REC_NOT_VERIFIED, REC_SCOPE, REC_FOREIGN = (
    "USED", "NO_RECONCILED_REFERENCE", "NOT_VERIFIED", SCOPE_MISMATCH, "FOREIGN_PROJECT")
NO_BASIS, INCOMPLETE_PRICING, PRICED, UNPRICED = (
    "NO_APPROVED_PRICING_BASIS", "INCOMPLETE_PRICING", "PRICED", "UNPRICED")


def _nonempty(v):
    return bool(str(v or "").strip())


def _pct(num, den):
    """(num / den) x 100, or None when the denominator is 0 or missing (never a division by zero)."""
    if num is None or den is None or den == 0:
        return None
    return 100.0 * num / den


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


# ---- key map (generic schema, legacy training-villa maps accepted unchanged) ----------------------------------------

def scoring_key_map(doc, project_id):
    """The key map document the scorer reads. A URBAN_PROJECT_KEY_MAP_V1 map must name this project; it is passed to
    the scorer as V1 (plain item codes) or, when it declares typed_records, as V2 (typed selectors). A legacy
    training-villa map is passed unchanged (its outputs stay byte-identical)."""
    schema = doc.get("SCHEMA")
    if schema in LEGACY_KEY_MAPS:
        return doc, "legacy " + schema
    if schema != KEY_MAP_SCHEMA:
        raise ValueError(f"key map schema {schema!r} is not {KEY_MAP_SCHEMA} (or a legacy {', '.join(LEGACY_KEY_MAPS)})")
    if doc.get("project_id") != project_id:
        raise ValueError(f"key map of project {doc.get('project_id')!r} used for project {project_id!r}")
    keys = doc.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError("a key map names its keys")
    for k in keys:
        for f in ("key", "trade", "reference_id"):
            if not _nonempty(k.get(f)):
                raise ValueError(f"key map entry {k!r}: {f} missing")
        if not isinstance(k.get("item_codes"), list):
            raise ValueError(f"key {k['key']!r}: item_codes must be a list")
        if not k["item_codes"] and not k.get("typed_lines"):
            raise ValueError(f"key {k['key']!r}: no item code and no typed selector (it could never be answered)")
    out = dict(doc)
    out["SCHEMA"] = K.KEY_MAP_V2_SCHEMA if doc.get("typed_records") else LEGACY_KEY_MAPS[0]
    return out, KEY_MAP_SCHEMA


# ---- one scored side (exactly the training-villa path) ---------------------------------------------------------------

def score_side(lines, release_report, normalised_doc, key_map_doc):
    """alsenan_keymap.run on given lines: S.score of engine_rows / reference_rows, adapter attached as run() does."""
    eng, report = K.engine_rows(lines, release_report, key_map_doc)
    ref = K.reference_rows(normalised_doc, key_map_doc)
    result = S.score(eng, ref)
    result["adapter"] = dict(report, release_report_present=release_report is not None, boq_lines=len(lines))
    return result


def side_markdown(result, label, set_bindings):
    """The training-villa markdown of one side (alsenan_keymap main(): scorer table + opt-in sections)."""
    md = S.markdown(result)
    if set_bindings:
        md += K.set_bindings_markdown([(label, result["adapter"])])
    md += K.unit_excluded_markdown([(label, result["adapter"])])
    return md


# ---- reconciled reference ---------------------------------------------------------------------------------------------

def reconciled_by_key(doc, project_id, key_map_doc, reference_units):
    """{key: (status, record view)} for every key of the map, and the records no key uses (listed, never dropped)."""
    keys = {k["key"]: k for k in key_map_doc["keys"]}
    out = {k: (REC_NONE, None) for k in keys}
    unused = []
    if doc is None:
        return out, unused
    if doc.get("schema", doc.get("SCHEMA")) != RECONCILED_SCHEMA:
        raise ValueError(f"reconciled reference schema is not {RECONCILED_SCHEMA}")
    seen = set()
    for r in doc.get("references") or ():
        line = r.get("line")
        view = {"line": line, "item_code": r.get("item_code"), "unit": r.get("unit"), "value": r.get("value"),
                "status": r.get("status"), "project_id": r.get("project_id")}
        if line in seen:
            raise ValueError(f"reconciled reference {line!r} repeated")
        seen.add(line)
        if r.get("project_id") != project_id:
            unused.append(dict(view, reason=REC_FOREIGN))
            continue
        if line not in keys:
            unused.append(dict(view, reason="NO_KEY (no key of this map is that line)"))
            continue
        k = keys[line]
        value = S._qty(r.get("value"), f"reconciled {line}")
        codes = r.get("item_codes") or ([r["item_code"]] if r.get("item_code") else [])
        why = []
        if not str(r.get("status") or "").strip().upper().startswith("VERIFIED"):
            out[line] = (REC_NOT_VERIFIED, dict(view, reason=f"status {r.get('status')!r} is not VERIFIED"))
            continue
        if value is None:
            out[line] = (REC_NOT_VERIFIED, dict(view, reason="no value"))
            continue
        if S.norm_unit(r.get("unit")) != reference_units.get(line):
            why.append(f"unit {r.get('unit')!r} is not the key's {reference_units.get(line)!r}")
        if k.get("typed_lines") or sorted(set(codes)) != sorted(set(k["item_codes"])):
            why.append(f"item codes {sorted(set(codes))} are not the key's {sorted(set(k['item_codes']))}"
                       + (" (typed key)" if k.get("typed_lines") else ""))
        if why:
            out[line] = (REC_SCOPE, dict(view, reason="; ".join(why)))
            continue
        out[line] = (REC_USED, dict(view, value=value, unit=reference_units.get(line)))
    return out, unused


# ---- pricing basis ---------------------------------------------------------------------------------------------------

def load_pricing_basis(doc, reference_units):
    """{key: rate} of ONE approved basis, or None without a basis. Refused: no approval / date / currency, a rate in
    another unit than the key's reference unit, a key priced twice, a negative or non-finite rate."""
    if doc is None:
        return None
    if doc.get("SCHEMA") != PRICING_SCHEMA:
        raise ValueError(f"pricing basis schema {doc.get('SCHEMA')!r} is not {PRICING_SCHEMA}")
    ap = doc.get("approval") or {}
    for f in ("by", "date", "source"):
        if not _nonempty(ap.get(f)):
            raise ValueError(f"pricing basis {doc.get('basis_id')!r}: approval {f} missing (never an unapproved rate)")
    if not _nonempty(doc.get("basis_id")) or not _nonempty(doc.get("currency")):
        raise ValueError("pricing basis needs its basis_id and currency")
    rates = {}
    for r in doc.get("rates") or ():
        key = r.get("key")
        if key in rates:
            raise ValueError(f"key {key!r} priced twice in one basis")
        if key not in reference_units:
            raise ValueError(f"priced key {key!r} is not a key of this map")
        rate = r.get("rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0:
            raise ValueError(f"key {key!r}: rate {rate!r} is not a finite non-negative number")
        if S.norm_unit(r.get("unit")) != reference_units[key]:
            raise ValueError(f"key {key!r}: rate per {r.get('unit')!r} but the key is in {reference_units[key]!r} "
                             "(never converted)")
        rates[key] = float(rate)
    return rates


# ---- the Goal B layer ------------------------------------------------------------------------------------------------

def _line_class(ln, excluded_by_key):
    """(exception class or None, reason) of one scored reference line (original workbook side)."""
    out = ln["outcome"]
    if out == S.OUT_SILENT:
        n = excluded_by_key.get(ln["key"], 0)
        if n and ln["reference_qty"]:
            return SCOPE_MISMATCH, f"engine excludes the key with evidence on {n} line(s); the reference carries quantity"
        if n:
            return None, f"engine excludes the key with evidence on {n} line(s); reference quantity 0 or blank"
        return REFERENCE_ONLY, "no engine line answers the key"
    if out == S.OUT_UNIT_MISMATCH:
        return SCOPE_MISMATCH, "every engine answer is in another unit (refused, never converted)"
    if out == S.OUT_REF_UNIT_MISSING:
        return SCOPE_MISMATCH, "the reference line has no unit (never compared)"
    if out == S.OUT_COMPARED and ln["reference_qty"] == 0:
        return ZERO_REFERENCE, "reference quantity 0: absolute difference only, no %"
    return None, ""


def goal_b(result, key_map_doc, normalised_doc, reconciled, pricing, high_value, tol):
    """Per key, per trade and unit and per trade (cost) views of one scored side."""
    excluded_by_key = result["adapter"].get("excluded_lines_by_key", {})
    rec, rec_unused = reconciled
    lines = []
    for ln in result["lines"]:
        cls, why = _line_class(ln, excluded_by_key)
        eq, rq = ln["engine_qty"], ln["reference_qty"]
        compared = ln["outcome"] == S.OUT_COMPARED
        var_o = _pct(eq - rq, rq) if compared and cls is None else None
        rst, rview = rec.get(ln["key"], (REC_NONE, None))
        rq2 = rview["value"] if rst == REC_USED else None
        var_r = _pct(eq - rq2, rq2) if compared and rq2 is not None else None
        rec_cls = None
        if rst == REC_USED and rq2 == 0:
            rec_cls = ZERO_REFERENCE
        elif rst == REC_SCOPE:
            rec_cls = SCOPE_MISMATCH
        rate = None if pricing is None else pricing.get(ln["key"])
        price = NO_BASIS if pricing is None else (PRICED if rate is not None else UNPRICED)
        cost = {"status": price, "rate": rate,
                "reference_cost": _r(rq * rate) if rate is not None and rq is not None else None,
                "engine_cost": _r(eq * rate) if rate is not None and compared else None,
                "reconciled_cost": _r(rq2 * rate) if rate is not None and rq2 is not None else None}
        lines.append({"key": ln["key"], "ref_id": ln["ref_id"], "trade": ln["trade"], "unit": ln["unit"],
                      "outcome": ln["outcome"], "exception": cls, "exception_reason": why,
                      "engine_qty": _r(eq), "engine_ids": len(ln["engine_ids"]),
                      "original": {"qty": rq, "variance_pct": _r(var_o, 4),
                                   "within_tolerance": None if var_o is None else abs(var_o) <= tol},
                      "reconciled": {"status": rst, "qty": rq2, "variance_pct": _r(var_r, 4),
                                     "within_tolerance": None if var_r is None else abs(var_r) <= tol,
                                     "exception": rec_cls, "reason": (rview or {}).get("reason")},
                      "cost": cost, "verdict": ln["verdict"], "high_value": ln["key"] in high_value})

    # reference rows of the keyed kinds that no key names: REFERENCE_ONLY (key-map gap), never dropped
    kinds = set(key_map_doc.get("reference_row_kinds") or ())
    keyed = {k["reference_id"] for k in key_map_doc["keys"]}
    ref_unkeyed = [{"ref_id": r["id"], "trade": r.get("trade"), "unit": r.get("unit"), "qty": r.get("qty"),
                    "row_kind": r.get("row_kind"), "exception": REFERENCE_ONLY,
                    "reason": "no key names this reference row (key-map gap or a total of keyed rows)"}
                   for r in normalised_doc["records"]
                   if r["id"] not in keyed and (not kinds or r.get("row_kind") in kinds)]

    ad = result["adapter"]
    engine_only = ([{"what": "engine key with no reference line", "key": fp["key"], "trade": fp["trade"],
                     "unit": fp["unit"], "lines": 1, "qty": fp["qty"], "class": fp["class"]}
                    for fp in result["false_positives"]]
                   + [{"what": "unmapped item code (no key)", "key": None, "item_code": u["item_code"],
                       "unit": u["unit"], "lines": u["lines"]} for u in ad.get("unmapped_by_item", [])]
                   + [{"what": "unit no reference line can use (UNIT_NOT_IN_REFERENCE)", "key": x["key"],
                       "item_code": x["item_code"], "unit": x["unit"], "lines": 1}
                      for x in ad.get("excluded_unit_not_in_reference", [])])
    for e in engine_only:
        e["exception"] = ENGINE_ONLY

    # per trade and unit (quantity; units never mixed)
    buckets = {}
    for g in lines:
        b = buckets.setdefault((str(g["trade"]), g["unit"]), {
            "trade": g["trade"], "unit": g["unit"], "keys": 0, "compared": 0, "held": 0, "unsupported": 0,
            "exceptions": {c: 0 for c in EXCEPTION_CLASSES}, "sum_reference": 0.0, "sum_engine": 0.0,
            "rec_compared": 0, "sum_reconciled": 0.0, "sum_engine_rec": 0.0, "lines_outside_tolerance": []})
        b["keys"] += 1
        b["held"] += g["outcome"] == S.OUT_HELD
        b["unsupported"] += g["outcome"] == S.OUT_UNSUPPORTED
        if g["exception"]:
            b["exceptions"][g["exception"]] += 1
        if g["outcome"] == S.OUT_COMPARED and g["exception"] is None:
            b["compared"] += 1
            b["sum_reference"] += g["original"]["qty"]
            b["sum_engine"] += g["engine_qty"]
            if g["original"]["within_tolerance"] is False:
                b["lines_outside_tolerance"].append(g["key"])
        if g["reconciled"]["variance_pct"] is not None:
            b["rec_compared"] += 1
            b["sum_reconciled"] += g["reconciled"]["qty"]
            b["sum_engine_rec"] += g["engine_qty"]
    for e in ref_unkeyed:
        u = S.norm_unit(e["unit"]) if K.scorer_unit_known(e["unit"]) else str(e["unit"])
        b = buckets.setdefault((str(e["trade"]), u or S.MISSING_UNIT), {
            "trade": e["trade"], "unit": u or S.MISSING_UNIT, "keys": 0, "compared": 0, "held": 0, "unsupported": 0,
            "exceptions": {c: 0 for c in EXCEPTION_CLASSES}, "sum_reference": 0.0, "sum_engine": 0.0,
            "rec_compared": 0, "sum_reconciled": 0.0, "sum_engine_rec": 0.0, "lines_outside_tolerance": []})
        b["exceptions"][REFERENCE_ONLY] += 1
    trade_units = []
    for key in sorted(buckets):
        b = buckets[key]
        vo = _pct(b["sum_engine"] - b["sum_reference"], b["sum_reference"]) if b["compared"] else None
        vr = _pct(b["sum_engine_rec"] - b["sum_reconciled"], b["sum_reconciled"]) if b["rec_compared"] else None
        b["variance_original_pct"] = _r(vo, 4)
        b["variance_reconciled_pct"] = _r(vr, 4)
        b["within_tolerance_original"] = None if vo is None else abs(vo) <= tol
        b["offsetting_errors"] = bool(vo is not None and abs(vo) <= tol and b["lines_outside_tolerance"])
        b["complete"] = (b["held"] == 0 and b["unsupported"] == 0 and not any(b["exceptions"].values()))
        for f, n in (("sum_reference", "compared"), ("sum_engine", "compared"), ("sum_reconciled", "rec_compared"),
                     ("sum_engine_rec", "rec_compared")):
            b[f] = _r(b[f]) if b[n] else None          # nothing compared: no sum (missing never shown as 0)
        trade_units.append(b)

    # per trade (cost: one currency, units may be summed as money only)
    trades = {}
    for g in lines:
        t = trades.setdefault(str(g["trade"]), {"trade": g["trade"], "compared_keys": 0, "unpriced_keys": [],
                                                "reference_cost": 0.0, "engine_cost": 0.0,
                                                "rec_keys": 0, "reconciled_cost": 0.0, "engine_cost_rec": 0.0})
        if g["outcome"] != S.OUT_COMPARED or g["exception"] is not None:
            continue
        t["compared_keys"] += 1
        c = g["cost"]
        if c["status"] != PRICED:
            if pricing is not None:          # without a basis nothing is priced: the trade status says so
                t["unpriced_keys"].append(g["key"])
            continue
        t["reference_cost"] += c["reference_cost"]
        t["engine_cost"] += c["engine_cost"]
        if c["reconciled_cost"] is not None and g["reconciled"]["variance_pct"] is not None:
            t["rec_keys"] += 1
            t["reconciled_cost"] += c["reconciled_cost"]
            t["engine_cost_rec"] += c["engine_cost"]
    cost = []
    for name in sorted(trades):
        t = trades[name]
        if pricing is None:
            st = NO_BASIS
        elif t["unpriced_keys"]:
            st = INCOMPLETE_PRICING
        else:
            st = PRICED
        ok = st == PRICED and t["compared_keys"] > 0
        vo = _pct(t["engine_cost"] - t["reference_cost"], t["reference_cost"]) if ok else None
        vr = (_pct(t["engine_cost_rec"] - t["reconciled_cost"], t["reconciled_cost"])
              if ok and t["rec_keys"] else None)
        cost.append({"trade": t["trade"], "status": st, "compared_keys": t["compared_keys"],
                     "unpriced_keys": t["unpriced_keys"],
                     "reference_cost": _r(t["reference_cost"]) if ok else None,
                     "engine_cost": _r(t["engine_cost"]) if ok else None,
                     "variance_original_pct": _r(vo, 4),
                     "zero_reference_cost": bool(ok and t["reference_cost"] == 0),
                     "reconciled_keys": t["rec_keys"] if ok else 0, "variance_reconciled_pct": _r(vr, 4),
                     "within_tolerance_original": None if vo is None else abs(vo) <= tol})

    exceptions = ([dict(key=g["key"], ref_id=g["ref_id"], trade=g["trade"], unit=g["unit"], exception=g["exception"],
                        reason=g["exception_reason"], side="original") for g in lines if g["exception"]]
                  + [dict(key=g["key"], ref_id=g["ref_id"], trade=g["trade"], unit=g["unit"],
                          exception=g["reconciled"]["exception"], reason=g["reconciled"]["reason"]
                          or "reconciled quantity 0", side="reconciled")
                     for g in lines if g["reconciled"]["exception"]]
                  + [dict(e, side="original") for e in ref_unkeyed] + [dict(e, side="engine") for e in engine_only])
    counts = {c: sum(1 for e in exceptions if e["exception"] == c) for c in EXCEPTION_CLASSES}
    return {"lines": lines, "trade_units": trade_units, "trade_cost": cost, "exceptions": exceptions,
            "exception_counts": counts, "reconciled_unused": rec_unused,
            "high_value_lines": [g for g in lines if g["high_value"]]}


# ---- manifest --------------------------------------------------------------------------------------------------------

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest(path, run=None, candidate_lines=None, candidate_label=None):
    m = _load(path)
    if m.get("SCHEMA") != MANIFEST_SCHEMA:
        raise ValueError(f"manifest schema {m.get('SCHEMA')!r} is not {MANIFEST_SCHEMA}")
    for f in ("project_id", "label", "reference", "key_map", "run_label"):
        if not _nonempty(m.get(f)):
            raise ValueError(f"manifest: {f} missing")
    base = Path(path).resolve().parent

    def p(v):
        return None if v is None else (Path(v) if Path(v).is_absolute() else base / v)
    m = dict(m)
    m["run"] = Path(run) if run else p(m.get("run"))
    if m["run"] is None:
        raise ValueError("manifest: no run directory (manifest 'run' or --run)")
    m["candidate_lines"] = Path(candidate_lines) if candidate_lines else p(m.get("candidate_lines"))
    # F-C-T452-1 (Checker 2026-11-03): lines given on the command line are not the lines the manifest's
    # candidate_label names, so an override needs its own label; the manifest label is never carried onto them.
    if candidate_lines and not _nonempty(candidate_label):
        raise ValueError("--candidate-lines needs --candidate-label: the manifest's candidate_label names the "
                         "manifest's candidate lines, not these")
    if _nonempty(candidate_label):
        if m["candidate_lines"] is None:
            raise ValueError("--candidate-label given without candidate lines")
        m["candidate_label"] = str(candidate_label)
    if m["candidate_lines"] is not None and not _nonempty(m.get("candidate_label")):
        raise ValueError("a candidate needs its candidate_label")
    if m["candidate_lines"] is not None and str(m["candidate_label"]).strip() == str(m["run_label"]).strip():
        raise ValueError("the candidate label equals the run label: the two sides are never combined")
    for f in ("reference", "key_map", "reconciled_reference", "pricing_basis", "set_bindings"):
        m[f] = p(m.get(f))
    tol = m.get("tolerance_pct", DEFAULT_TOLERANCE_PCT)
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not math.isfinite(tol) or tol < 0:
        raise ValueError(f"tolerance_pct {tol!r} is not a finite non-negative number")
    m["tolerance_pct"] = float(tol)
    return m


def build(manifest):
    """The project scoreboard of one manifest (load_manifest output): JSON-ready dict."""
    pid = manifest["project_id"]
    normalised = _load(manifest["reference"])
    km_raw = _load(manifest["key_map"])
    km, km_kind = scoring_key_map(km_raw, pid)
    if manifest.get("set_bindings") is not None:
        km = K.with_set_bindings(km, _load(manifest["set_bindings"]))
    high = list(manifest.get("high_value_keys") or ())
    known = {k["key"] for k in km["keys"]}
    bad = [k for k in high if k not in known]
    if bad:
        raise ValueError(f"high-value keys {bad} are not keys of the map")
    run_dir = Path(manifest["run"])
    lines = _load(run_dir / "BOQ_LINES.json")
    rel_path = run_dir / "BOQ_RELEASE_REPORT.json"
    rel = _load(rel_path) if rel_path.exists() else None
    # markdown label of the run side = the run directory name, exactly as alsenan_keymap main() writes it
    sides = [(manifest["run_label"], run_dir.name, lines)]
    if manifest.get("candidate_lines") is not None:
        sides.append((manifest["candidate_label"], manifest["candidate_label"], _load(manifest["candidate_lines"])))
    rec_doc = _load(manifest["reconciled_reference"]) if manifest.get("reconciled_reference") else None
    price_doc = _load(manifest["pricing_basis"]) if manifest.get("pricing_basis") else None
    out_sides = []
    for label, md_label, ls in sides:
        res = score_side(ls, rel, normalised, km)
        units = {ln["key"]: ln["unit"] for ln in res["lines"]}
        rec = reconciled_by_key(rec_doc, pid, km, units)
        pricing = load_pricing_basis(price_doc, units)
        gb = goal_b(res, km, normalised, rec, pricing, set(high), manifest["tolerance_pct"])
        out_sides.append({"label": label, "boq_lines": len(ls), "score": res,
                          "score_markdown": side_markdown(res, md_label, manifest.get("set_bindings") is not None),
                          "goal_b": gb})
    return {"SCHEMA": SCHEMA, "project_id": pid, "label": manifest["label"],
            "source_folder": manifest.get("source_folder"), "key_map": km_kind,
            "reconciled_reference": None if rec_doc is None else RECONCILED_SCHEMA,
            "pricing_basis": None if price_doc is None else {"basis_id": price_doc.get("basis_id"),
                                                               "currency": price_doc.get("currency"),
                                                               "approval": price_doc.get("approval")},
            "tolerance_pct": manifest["tolerance_pct"], "sides": out_sides,
            "rule": "the score is tools/alsenan_scoreboard.py unchanged; variance against the original workbook and "
                    "the reconciled reference kept apart; exceptions classed, never a division by zero or a silent "
                    "drop; held never 0; cost only on one approved basis"}


# ---- markdown --------------------------------------------------------------------------------------------------------

def _p(x):
    return "-" if x is None else f"{x:+.2f} %"


def _q(x, n=3):
    return "-" if x is None else f"{x:.{n}f}"


def markdown(res):
    out = [f"# Project scoreboard: {res['label']} ({res['project_id']})", "",
           f"Key map: {res['key_map']}; reconciled reference: {res['reconciled_reference'] or 'none'}; pricing basis: "
           f"{(res['pricing_basis'] or {}).get('basis_id') or 'none (cost NOT priced)'}; tolerance +-"
           f"{res['tolerance_pct']:g} %.", ""]
    for s in res["sides"]:
        g = s["goal_b"]
        out += [f"## {s['label']} ({s['boq_lines']} BOQ lines)", "", "### Score (per trade and unit)", "",
                s["score_markdown"].rstrip("\n"), "",
                "### Variance per trade and unit (original workbook | reconciled reference)", "",
                "| Trade | Unit | Keys | Compared | Reference | Engine | Var. original | Reconciled keys | "
                "Var. reconciled | Held | Exceptions | Offsetting | Complete |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for b in g["trade_units"]:
            ex = ", ".join(f"{k} {v}" for k, v in b["exceptions"].items() if v) or "-"
            out.append(f"| {b['trade']} | {b['unit']} | {b['keys']} | {b['compared']} | {_q(b['sum_reference'])} | "
                       f"{_q(b['sum_engine'])} | {_p(b['variance_original_pct'])} | {b['rec_compared']} | "
                       f"{_p(b['variance_reconciled_pct'])} | {b['held']} | {ex} | "
                       f"{'OFFSETTING_ERRORS' if b['offsetting_errors'] else '-'} | {'yes' if b['complete'] else 'no'} |")
        out += ["", "### Cost per trade (one approved basis, same rate both sides)", "",
                "| Trade | Status | Compared keys | Reference cost | Engine cost | Var. original | Var. reconciled | "
                "Unpriced keys |", "|---|---|---|---|---|---|---|---|"]
        for c in g["trade_cost"]:
            out.append(f"| {c['trade']} | {c['status']} | {c['compared_keys']} | {_q(c['reference_cost'], 2)} | "
                       f"{_q(c['engine_cost'], 2)} | {_p(c['variance_original_pct'])} | "
                       f"{_p(c['variance_reconciled_pct'])} | {', '.join(c['unpriced_keys']) or '-'} |")
        out += ["", "### High-value lines (line level)", "",
                "| Key | Unit | Outcome | Engine | Original | Var. original | Reconciled | Var. reconciled | "
                "Exception |", "|---|---|---|---|---|---|---|---|---|"]
        for h in g["high_value_lines"]:
            rq = h["reconciled"]
            out.append(f"| {h['key']} | {h['unit']} | {h['outcome']} | {_q(h['engine_qty'])} | "
                       f"{_q(h['original']['qty'])} | {_p(h['original']['variance_pct'])} | "
                       f"{_q(rq['qty']) if rq['status'] == REC_USED else rq['status']} | {_p(rq['variance_pct'])} | "
                       f"{h['exception'] or rq['exception'] or '-'} |")
        cnt = g["exception_counts"]
        out += ["", "### Exceptions: " + ", ".join(f"{k} {v}" for k, v in cnt.items()), ""]
        if g["exceptions"]:
            out += ["| Class | Side | Key / ref / item | Unit | Reason |", "|---|---|---|---|---|"]
            for e in g["exceptions"]:
                who = e.get("key") or e.get("ref_id") or e.get("item_code")
                if e.get("item_code") and e.get("key") is None:
                    who = f"{e['item_code']} ({e.get('lines')} line(s))"
                out.append(f"| {e['exception']} | {e['side']} | {who} | {e.get('unit')} | "
                           f"{e.get('reason') or e.get('what')} |")
        out.append("")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run")
    ap.add_argument("--candidate-lines")
    ap.add_argument("--candidate-label", help="label of the --candidate-lines side (required with it)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    a = ap.parse_args(argv)
    res = build(load_manifest(a.manifest, a.run, a.candidate_lines, a.candidate_label))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = markdown(res)
    if a.markdown:
        Path(a.markdown).write_text(md, encoding="utf-8")
    print(md, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
