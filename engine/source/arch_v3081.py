"""ARCH_TAKEOFF_V3.0.81 (T-770 round 1, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.78, extended with FILL_WIRE_V1: a fix-row set (schema MAIN_CHAT_FIX_ROWS_V1 or a worker
FIX_ROWS.json of the same row shape) is applied to the candidate BY LINE ID, each line taking the figure, the method
label and the one-line basis its row gives (DELIVERY_MODE s.3 fallback order: MEASURED / DRAWING-READ / DEFAULT /
ESTIMATE / SAFETY). Nothing here measures, invents or chooses a quantity: the rows carry them.

R-T770-1 (every villa):
  (a) a row binds its line as the set read it: line id present, same item code, unit and element id, and the same
      before state (class, net, held low, held high within 1e-6); a stale or absent line stops the run (never applied
      to the wrong line, never skipped silently); one row per line id;
  (b) after = {"class": "RELEASED", "net": x} with x >= 0 a figure, or {"class": "HELD", "low": a, "high": b} with
      0 <= a <= b (a range stays HELD; blank is never turned into 0 by omission; a HELD row with no bound is refused);
  (c) every applied line carries method_label (one of LABELS) and fill_basis (non-empty); a VALUED figure that is not
      MEASURED is written as evidence_state PROVISIONAL, so it is never mistaken for a measured or verified figure;
  (d) every line the set does not name is byte-identical to the base (asserted after the apply);
  (e) the base version is whatever candidate the rows were built on (the set's candidate_version must match the base
      the caller names): the package stays line-id bound and re-runs on a newer base without renumbering.

Two views, one rule: apply_boq_lines() works on full candidate BOQ lines (evidence_state / measured_net /
bounded_range), apply_index() on a LINE_INDEX_V3_0_x document (class / measured_net / held_low / held_high).
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json

METHOD = "ARCH_TAKEOFF_V3.0.81"
EXTENDS = "ARCH_TAKEOFF_V3.0.78"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_81"
RULE = "R-T770-1"
ROW_SCHEMAS = ("MAIN_CHAT_FIX_ROWS_V1", "URBAN_FIX_ROWS_V1")
INDEX_SCHEMA = "URBAN_T479_LINE_INDEX_V1"
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
EXCLUDED_STATES = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
BOUNDED = "BOUNDED_EXPOSURE"
PROVISIONAL = "PROVISIONAL"
TOL = 1e-6


class FillError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= TOL


# ------------------------------------------------------------------------------------------------ rows
def check_rows(doc, base_version=None):
    """validate a fix-row set (R-T770-1 a-c on the rows alone); returns {line_id: row}."""
    if not isinstance(doc, dict) or doc.get("schema") not in ROW_SCHEMAS:
        raise FillError(f"fix-row set schema {doc.get('schema') if isinstance(doc, dict) else type(doc)} "
                        f"not one of {ROW_SCHEMAS}")
    if base_version is not None and doc.get("candidate_version") != base_version:
        raise FillError(f"rows built on {doc.get('candidate_version')}, base is {base_version} (rebuild the set)")
    out = {}
    for r in doc.get("rows") or []:
        lid = r.get("line_id")
        for k in ("line_id", "item_code", "unit", "before", "after", "label", "basis"):
            if r.get(k) in (None, ""):
                raise FillError(f"{lid}: row lacks {k}")
        if lid in out:
            raise FillError(f"{lid}: two rows for one line")
        if r["label"] not in LABELS:
            raise FillError(f"{lid}: label {r['label']} not one of {LABELS}")
        if not str(r["basis"]).strip():
            raise FillError(f"{lid}: empty basis")
        a = r["after"]
        if a.get("class") == "RELEASED":
            if not _num(a.get("net")) or a["net"] < 0:
                raise FillError(f"{lid}: RELEASED after needs a figure >= 0, got {a.get('net')}")
        elif a.get("class") == "HELD":
            lo, hi = a.get("low"), a.get("high")
            if not (_num(lo) and _num(hi)) or lo < 0 or lo > hi:
                raise FillError(f"{lid}: HELD after needs 0 <= low <= high, got {lo} .. {hi}")
        else:
            raise FillError(f"{lid}: after class {a.get('class')} not RELEASED / HELD")
        out[lid] = r
    if not out:
        raise FillError("fix-row set has no rows")
    return out


# ------------------------------------------------------------------------------------------------ index view
def _index_before(ln):
    return {"class": ln["class"], "net": ln.get("measured_net"), "low": ln.get("held_low"),
            "high": ln.get("held_high")}


def _bind(lid, ln, r, before):
    if ln is None:
        raise FillError(f"{lid}: no such line in the base")
    if ln["item_code"] != r["item_code"] or ln["unit"] != r["unit"]:
        raise FillError(f"{lid}: base {ln['item_code']} {ln['unit']}, row {r['item_code']} {r['unit']} (stale)")
    if r.get("element_id") is not None and str(before.get("element_id") or "") != str(r["element_id"]):
        raise FillError(f"{lid}: base element {before.get('element_id')}, row {r['element_id']} (stale)")
    b = r["before"]
    if before["class"] != b.get("class") or not all(_same(before[k], b.get(k)) for k in ("net", "low", "high")):
        raise FillError(f"{lid}: base {before['class']} {before['net']} {before['low']}..{before['high']}, row read "
                        f"{b.get('class')} {b.get('net')} {b.get('low')}..{b.get('high')} (stale)")
    if before["class"] == "EXCLUDED":
        raise FillError(f"{lid}: an excluded line is never filled")


def apply_index(index_doc, rows_doc, base_version=None, new_version=METHOD):
    """the index view: returns (new index doc, applied rows). Lines not named stay byte-identical."""
    if index_doc.get("schema") != INDEX_SCHEMA:
        raise FillError(f"index schema {index_doc.get('schema')} is not {INDEX_SCHEMA}")
    base_version = base_version or index_doc.get("candidate_version")
    rows = check_rows(rows_doc, base_version)
    by = {ln["line_id"]: ln for ln in index_doc["lines"]}
    if len(by) != len(index_doc["lines"]):
        raise FillError("base index has duplicate line ids")
    new = copy.deepcopy(index_doc)
    applied = []
    for ln in new["lines"]:
        r = rows.get(ln["line_id"])
        if r is None:
            continue
        before = dict(_index_before(ln), element_id=ln.get("element_id"))
        _bind(ln["line_id"], ln, r, before)
        a = r["after"]
        if a["class"] == "RELEASED":
            ln.update({"class": "RELEASED", "measured_net": _r(a["net"]), "held_low": None, "held_high": None})
        else:
            ln.update({"class": "HELD", "measured_net": None, "held_low": _r(a["low"]), "held_high": _r(a["high"])})
        ln["method_label"], ln["fill_basis"] = r["label"], r["basis"]
        applied.append(r)
    missing = sorted(set(rows) - {r["line_id"] for r in applied})
    if missing:
        raise FillError(f"{len(missing)} row(s) name no base line: {missing[:5]}")
    _assert_outside(index_doc["lines"], new["lines"], rows)
    new["candidate_version"] = new_version
    new["extends"] = base_version
    new["fill"] = {"rule": RULE, "policy": POLICY_ID, "rows": len(applied),
                   "sets": sorted({r.get("set") or "-" for r in applied})}
    return new, applied


# ------------------------------------------------------------------------------------------------ BOQ-line view
def line_class(ln):
    if ln.get("evidence_state") in EXCLUDED_STATES:
        return "EXCLUDED"
    if ln.get("evidence_state") in VALUED_STATES and ln.get("measured_net") is not None:
        return "RELEASED"
    return "HELD"


def _boq_before(ln):
    c = line_class(ln)
    lo = hi = None
    if c == "HELD":
        b = ln.get("bounded_range")
        if isinstance(b, dict) and ln.get("evidence_state") == BOUNDED:
            lo, hi = b.get("low"), b.get("high")
    return {"class": c, "net": ln.get("measured_net") if c == "RELEASED" else None, "low": lo, "high": hi,
            "element_id": (ln.get("location") or {}).get("element_id")}


def apply_boq_lines(lines, rows_doc, base_version):
    """the BOQ-line view: returns (new lines, applied rows); a figure that is not MEASURED is PROVISIONAL."""
    rows = check_rows(rows_doc, base_version)
    new = copy.deepcopy(lines)
    applied = []
    seen = set()
    for ln in new:
        lid = ln["line_id"]
        if lid in seen:
            raise FillError(f"{lid}: duplicate line id in the base")
        seen.add(lid)
        r = rows.get(lid)
        if r is None:
            continue
        _bind(lid, ln, r, _boq_before(ln))
        a = r["after"]
        if a["class"] == "RELEASED":
            ln["evidence_state"] = "MEASURED" if r["label"] == "MEASURED" else PROVISIONAL
            ln["measured_net"], ln["bounded_range"] = _r(a["net"]), None
        else:
            ln["evidence_state"], ln["measured_net"] = BOUNDED, None
            ln["bounded_range"] = {"low": _r(a["low"]), "high": _r(a["high"]), "rule": RULE}
        if "gross" in ln:
            ln["gross"] = None
        ln["method_label"], ln["fill_basis"] = r["label"], r["basis"]
        applied.append(r)
    missing = sorted(set(rows) - {r["line_id"] for r in applied})
    if missing:
        raise FillError(f"{len(missing)} row(s) name no base line: {missing[:5]}")
    _assert_outside(lines, new, rows)
    return new, applied


# ------------------------------------------------------------------------------------------------ checks / diff
def _canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _assert_outside(old, new, rows):
    if len(old) != len(new):
        raise FillError("line count changed")
    for o, n in zip(old, new):
        if o["line_id"] != n["line_id"]:
            raise FillError("line order changed")
        if o["line_id"] not in rows and _canon(o) != _canon(n):
            raise FillError(f"{o['line_id']}: a line outside the set moved")


def totals_by_code(index_lines):
    """per (item code, unit): released sum, held low / high sums, blank held lines (the scoreboard's first number)."""
    t = {}
    for ln in index_lines:
        if ln["class"] == "EXCLUDED":
            continue
        a = t.setdefault((ln["item_code"], ln["unit"]), {"released": 0.0, "held_low": 0.0, "held_high": 0.0,
                                                          "blank": 0, "lines": 0})
        a["lines"] += 1
        if ln["class"] == "RELEASED":
            a["released"] += float(ln["measured_net"] or 0)
        elif ln.get("held_low") is None and ln.get("held_high") is None:
            a["blank"] += 1
        else:
            a["held_low"] += float(ln.get("held_low") or 0)
            a["held_high"] += float(ln.get("held_high") if ln.get("held_high") is not None else ln.get("held_low"))
    return t


def diff_rows(applied):
    return [{"line_id": r["line_id"], "set": r.get("set"), "item_code": r["item_code"], "unit": r["unit"],
             "element_id": r.get("element_id"), "before_class": r["before"].get("class"),
             "before_net": r["before"].get("net"), "before_low": r["before"].get("low"),
             "before_high": r["before"].get("high"), "after_class": r["after"]["class"],
             "after_net": r["after"].get("net"), "after_low": r["after"].get("low"),
             "after_high": r["after"].get("high"), "label": r["label"], "basis": r["basis"]}
            for r in sorted(applied, key=lambda r: r["line_id"])]


def write(out, base_lines, rows_doc, base_version=EXTENDS):
    """the hub's V3_0_81_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied = apply_boq_lines(base_lines, rows_doc, base_version)
    d = diff_rows(applied)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        by_set[r.get("set") or "-"] = by_set.get(r.get("set") or "-", 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_81_lines": len(new), "applied": len(applied), "by_set": by_set,
             "outside_rows_identical_to_base": True, "rows_candidate_version": rows_doc.get("candidate_version")}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": base_version, "rule": RULE, "released_default": False,
           "identity": ident}
    files = {"V3_0_81_BOQ_LINES.json": BL.dumps(new), "V3_0_81_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_81_DIFF.csv": buf.getvalue(), "V3_0_81_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return {"policy_id": POLICY_ID, "method": METHOD, "extends": EXTENDS, "rule": RULE, "labels": list(LABELS),
            "row_schemas": list(ROW_SCHEMAS), "valued_state_for_non_measured": PROVISIONAL,
            "default_switched": False, "verified": False}
