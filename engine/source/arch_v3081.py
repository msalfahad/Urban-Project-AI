"""ARCH_TAKEOFF_V3.0.81 (T-770, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.79, extended with FILL_WIRE_V1: Checker-verified fix-row sets (MAIN_CHAT_FIX_ROWS_V1 or a
worker FIX_ROWS.json of the same row shape) are applied to the candidate BY LINE ID, each line taking the figure, the
method label and the one-line basis its row gives (DELIVERY_MODE s.3 fallback order: MEASURED / DRAWING-READ /
DEFAULT / ESTIMATE / SAFETY). Nothing here measures, invents or chooses a quantity: the rows carry them.

R-T770-1 (every villa):
  (a) a row binds its line as the set read it: line id present, same item code, unit and element id, and the same
      before state (class, net, held low, held high within 1e-6); a stale or absent line stops the run (never applied
      to the wrong line, never skipped silently); one row per line id across every set of the package;
  (b) after = {"class": "RELEASED", "net": x} with x >= 0 a figure, or {"class": "HELD", "low": a, "high": b} with
      0 <= a <= b (a range stays HELD; blank is never turned into 0 by omission; a HELD row with no bound is refused);
  (c) every applied line carries method_label (one of LABELS) and fill_basis (non-empty); a VALUED figure that is not
      MEASURED is written as evidence_state PROVISIONAL, so it is never mistaken for a measured or verified figure;
  (d) every base line the package does not name is byte-identical to the base (asserted after the apply);
  (e) a set may have been built on an earlier candidate (the package's row_bases) only because (a) re-checks every
      line it names against the base actually used: a line that moved since stops the run.

R-T770-2 (every villa; T-761 / T-762 Gate A findings F-V762-1 and the owner materiality rule 2026-11-13 14:00):
  (f) a NEGATIVE row (a cover / tee-end deduction on a formwork face) is never a line of its own: it is netted into
      the largest positive row of the same host (item code + the first two element-id fields) in the same set; the
      host stays >= 0, its basis names the deduction; the deduction line is EXCLUDED with reason NETTED_INTO_HOST
      (the trade sum is unchanged); a deduction with no positive host row, or one that would drive the host below 0,
      or a negative row outside STR.FORMWORK* stops the run;
  (g) an IGNORED_SMALL row (a known piece 0 < size < 0.05 m3) is EXCLUDED with reason IGNORED_SMALL, its size kept,
      covered by ONE safety line the same set adds (alias NEW:...); the safety line is max(1 m3, sum of the ignored
      pieces it covers); a second safety line for one item code, a piece >= 0.05 m3 or a cover that names no added
      line stops the run; an ignored piece is never written as 0 and never dropped.

Two views, one rule: apply_boq_lines() works on full candidate BOQ lines (evidence_state / measured_net /
bounded_range), apply_index() on a LINE_INDEX_V3_0_x document (class / measured_net / held_low / held_high).
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import json

METHOD = "ARCH_TAKEOFF_V3.0.81"
EXTENDS = "ARCH_TAKEOFF_V3.0.79"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_81"
RULE = "R-T770-1"
RULE_NET = "R-T770-2"
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V1"
ROW_SCHEMAS = ("MAIN_CHAT_FIX_ROWS_V1", "URBAN_FIX_ROWS_V1", "DELIVERY_FIX_ROWS_V1", "T761_FIX_ROWS_V1")
INDEX_SCHEMA = "URBAN_T479_LINE_INDEX_V1"
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
EXCLUDED_STATES = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
BOUNDED = "BOUNDED_EXPOSURE"
PROVISIONAL = "PROVISIONAL"
NETTABLE_PREFIX = "STR.FORMWORK"
MATERIALITY_M3 = 0.05          # owner 2026-11-13 14:00: a known concrete piece below 0.05 m3 is ignored and logged
SAFETY_MIN_M3 = 1.0            # owner 2026-11-13 14:00: safety line = 1 m3 if the ignored sum < 1 m3, else the sum
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


def new_line_id(set_name, alias, item_code, unit):
    """the id of a line a set adds (deterministic: method + set + alias + item + unit)."""
    key = "|".join((METHOD, str(set_name), str(alias), str(item_code), str(unit)))
    return "L-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


# ------------------------------------------------------------------------------------------------ rows
def _check_set(doc, row_bases):
    if not isinstance(doc, dict) or doc.get("schema") not in ROW_SCHEMAS:
        raise FillError(f"fix-row set schema {doc.get('schema') if isinstance(doc, dict) else type(doc)} "
                        f"not one of {ROW_SCHEMAS}")
    if doc.get("candidate_version") not in row_bases:
        raise FillError(f"rows built on {doc.get('candidate_version')}, base accepts {sorted(row_bases)} "
                        f"(rebuild the set)")
    name = doc.get("task") or doc.get("set") or "-"
    rows, new = {}, {}
    for r in copy.deepcopy(doc.get("rows") or []):
        lid = r.get("line_id")
        for k in ("line_id", "item_code", "unit", "before", "after", "label", "basis"):
            if r.get(k) in (None, ""):
                raise FillError(f"{lid}: row lacks {k}")
        if lid in rows:
            raise FillError(f"{lid}: two rows for one line")
        if r["label"] not in LABELS:
            raise FillError(f"{lid}: label {r['label']} not one of {LABELS}")
        if not str(r["basis"]).strip():
            raise FillError(f"{lid}: empty basis")
        r.setdefault("set", name)
        r["set_doc"] = name
        a = r["after"]
        if a.get("class") == "RELEASED":
            if not _num(a.get("net")):
                raise FillError(f"{lid}: RELEASED after needs a figure, got {a.get('net')}")
            if a["net"] < 0 and not str(r["item_code"]).startswith(NETTABLE_PREFIX):
                raise FillError(f"{lid}: RELEASED after needs a figure >= 0, got {a['net']} "
                                f"(only a {NETTABLE_PREFIX} deduction is netted into its host)")
        elif a.get("class") == "HELD":
            lo, hi = a.get("low"), a.get("high")
            if not (_num(lo) and _num(hi)) or lo < 0 or lo > hi:
                raise FillError(f"{lid}: HELD after needs 0 <= low <= high, got {lo} .. {hi}")
        elif a.get("class") == "IGNORED_SMALL":
            s = a.get("size_m3")
            if r["unit"] != "m3" or not _num(s) or not (0 < s < MATERIALITY_M3):
                raise FillError(f"{lid}: IGNORED_SMALL needs a known piece 0 < size < {MATERIALITY_M3} m3, got {s} "
                                f"{r['unit']}")
            if not str(a.get("covered_by") or "").startswith("NEW:"):
                raise FillError(f"{lid}: IGNORED_SMALL names no added safety line")
        else:
            raise FillError(f"{lid}: after class {a.get('class')} not RELEASED / HELD / IGNORED_SMALL")
        rows[lid] = r
    adds = list(doc.get("new_lines") or []) + ([doc["safety_line"]] if doc.get("safety_line") else [])
    for n in copy.deepcopy(adds):
        alias = n.get("line_id")
        if not str(alias or "").startswith("NEW:"):
            raise FillError(f"{alias}: an added line's alias starts with NEW:")
        for k in ("item_code", "unit", "after", "label", "basis"):
            if n.get(k) in (None, ""):
                raise FillError(f"{alias}: added line lacks {k}")
        if n["label"] not in LABELS:
            raise FillError(f"{alias}: label {n['label']} not one of {LABELS}")
        if n["after"].get("class") != "RELEASED" or not _num(n["after"].get("net")) or n["after"]["net"] < 0:
            raise FillError(f"{alias}: an added line carries a RELEASED figure >= 0")
        if alias in new:
            raise FillError(f"{alias}: two added lines with one alias")
        n["set"] = name
        n["new_line_id"] = new_line_id(name, alias, n["item_code"], n["unit"])
        new[alias] = n
    # R-T770-2 (g): ignored pieces under one safety line of the same set
    for alias, n in new.items():
        cov = [r for r in rows.values() if r["after"]["class"] == "IGNORED_SMALL"
               and r["after"]["covered_by"] == alias]
        if n["label"] == "SAFETY" and cov:
            want = max(SAFETY_MIN_M3, sum(float(r["after"]["size_m3"]) for r in cov))
            if n["unit"] != "m3" or not _same(n["after"]["net"], want):
                raise FillError(f"{alias}: safety line {n['after']['net']} {n['unit']} is not max(1 m3, ignored sum) "
                                f"= {round(want, 6)} m3 over {len(cov)} piece(s)")
    for r in rows.values():
        if r["after"]["class"] == "IGNORED_SMALL" and r["after"]["covered_by"] not in new:
            raise FillError(f"{r['line_id']}: covered_by {r['after']['covered_by']} is not a line this set adds")
    # R-T770-2 (f): deductions netted into their host row
    for lid, r in sorted(rows.items()):
        a = r["after"]
        if a["class"] != "RELEASED" or a["net"] >= 0:
            continue
        key = (r["item_code"], ":".join(str(r.get("element_id") or "").split(":")[:2]))
        hosts = [h for h in rows.values() if h["line_id"] != lid and h["after"]["class"] == "RELEASED"
                 and h["after"]["net"] > 0 and (h["item_code"], ":".join(str(h.get("element_id") or "")
                                                                         .split(":")[:2])) == key]
        if not hosts or not key[1]:
            raise FillError(f"{lid}: deduction {a['net']} has no positive host row of {key[1] or '?'} in its set")
        h = sorted(hosts, key=lambda x: (-x["after"]["net"], x["line_id"]))[0]
        if h["after"]["net"] + a["net"] < -TOL:
            raise FillError(f"{lid}: deduction {a['net']} drives host {h['line_id']} below 0")
        h["after"] = dict(h["after"], net=_r(h["after"]["net"] + a["net"]))
        h["basis"] = f"{h['basis']}; nets {lid} {a['net']} ({RULE_NET})"
        r["after"] = {"class": "NETTED", "into": h["line_id"], "deduction": a["net"]}
    return rows, new


def check_package(doc, base_version=EXTENDS):
    """validate a package (one set, a list of sets, or URBAN_FILL_PACKAGE_V1) -> (rows {line_id: row},
    added {new line id: added line}); R-T770-1 a-c and R-T770-2 f-g on the rows alone."""
    if isinstance(doc, dict) and doc.get("schema") == PACKAGE_SCHEMA:
        if doc.get("base") != base_version:
            raise FillError(f"package built for {doc.get('base')}, base is {base_version}")
        sets, row_bases = doc.get("sets") or [], set(doc.get("row_bases") or []) | {base_version}
    elif isinstance(doc, list):
        sets, row_bases = doc, {base_version}
    else:
        sets, row_bases = [doc], {base_version}
    rows, added, safety = {}, {}, {}
    for s in sets:
        r, n = _check_set(s, row_bases)
        for lid in r:
            if lid in rows:
                raise FillError(f"{lid}: two rows for one line (sets {rows[lid]['set']} and {r[lid]['set']})")
        rows.update(r)
        for alias, x in n.items():
            if x["label"] == "SAFETY":
                if x["item_code"] in safety:
                    raise FillError(f"{x['item_code']}: a second safety line (never two safety lines)")
                safety[x["item_code"]] = alias
            if x["new_line_id"] in added:
                raise FillError(f"{alias}: added line id clash")
            added[x["new_line_id"]] = x
    if not rows:
        raise FillError("fix-row set has no rows")
    by_alias = {(x["set"], x["line_id"]): x["new_line_id"] for x in added.values()}
    for r in rows.values():
        if r["after"]["class"] == "IGNORED_SMALL":
            r["after"]["covered_by_line_id"] = by_alias[(r["set_doc"], r["after"]["covered_by"])]
    return rows, added


def check_rows(doc, base_version=None):
    """R-T770-1 a-c on the rows alone (kept for the round 1 callers); returns {line_id: row}."""
    return check_package(doc, base_version or (doc.get("candidate_version") if isinstance(doc, dict) else None))[0]


def _reason(r):
    a = r["after"]
    if a["class"] == "IGNORED_SMALL":
        return (f"IGNORED_SMALL ({RULE_NET}): known piece {a['size_m3']} m3 < {MATERIALITY_M3} m3, covered by safety "
                f"line {a['covered_by_line_id']}; logged in IGNORED_SMALL")
    return f"NETTED_INTO_HOST ({RULE_NET}): deduction {a['deduction']} {r['unit']} netted into {a['into']}"


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
    """the index view: returns (new index doc, applied rows). Base lines not named stay byte-identical; added lines
    are appended after them."""
    if index_doc.get("schema") != INDEX_SCHEMA:
        raise FillError(f"index schema {index_doc.get('schema')} is not {INDEX_SCHEMA}")
    base_version = base_version or index_doc.get("candidate_version")
    rows, added = check_package(rows_doc, base_version)
    by = {ln["line_id"]: ln for ln in index_doc["lines"]}
    if len(by) != len(index_doc["lines"]):
        raise FillError("base index has duplicate line ids")
    clash = sorted(set(added) & set(by))
    if clash:
        raise FillError(f"added line id already in the base: {clash[:3]}")
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
        elif a["class"] == "HELD":
            ln.update({"class": "HELD", "measured_net": None, "held_low": _r(a["low"]), "held_high": _r(a["high"])})
        else:
            ln.update({"class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None,
                       "excluded_reason": _reason(r)})
        ln["method_label"], ln["fill_basis"] = r["label"], r["basis"]
        applied.append(r)
    missing = sorted(set(rows) - {r["line_id"] for r in applied})
    if missing:
        raise FillError(f"{len(missing)} row(s) name no base line: {missing[:5]}")
    for lid, x in sorted(added.items()):
        new["lines"].append({"binding": None, "class": "RELEASED", "element_id": f"{x['set']}:{x['line_id']}",
                             "held_high": None, "held_low": None, "item_code": x["item_code"], "line_id": lid,
                             "measured_net": _r(x["after"]["net"]), "unbound_records": [], "unit": x["unit"],
                             "method_label": x["label"], "fill_basis": x["basis"], "added_by": RULE_NET})
    _assert_outside(index_doc["lines"], new["lines"], rows, len(added))
    new["candidate_version"] = new_version
    new["extends"] = base_version
    new["fill"] = {"rule": [RULE, RULE_NET], "policy": POLICY_ID, "rows": len(applied), "added": len(added),
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


def _boq_added(x, lid, template):
    """an added (safety) line in the shape of a candidate BOQ line, from a covered line of the same set."""
    ln = copy.deepcopy(template)
    ln.update({"line_id": lid, "item_code": x["item_code"], "unit": x["unit"], "evidence_state": PROVISIONAL,
               "measured_net": _r(x["after"]["net"]), "bounded_range": None, "method_label": x["label"],
               "fill_basis": x["basis"], "notes": x["basis"]})
    if "gross" in ln:
        ln["gross"] = None
    for k in ("deductions", "additions"):
        if k in ln:
            ln[k] = []
    ln["item_en"] = "Concrete safety allowance (known pieces below materiality)" \
        if x["item_code"].startswith("STR.CONC") else x["item_code"]
    ln["location"] = dict(ln.get("location") or {}, element_id=f"{x['set']}:{x['line_id']}", room_id=None,
                          room_name_en=None, room_name_ar=None)
    ln["calculation"] = {"formula": x["basis"], "inputs": {}}
    ln["rule"] = dict(ln.get("rule") or {}, rule_id=RULE_NET, version=METHOD)
    for k in ("rfi", "review", "measure_pair"):
        if k in ln:
            ln[k] = None
    return ln


def apply_boq_lines(lines, rows_doc, base_version):
    """the BOQ-line view: returns (new lines, applied rows); a figure that is not MEASURED is PROVISIONAL."""
    rows, added = check_package(rows_doc, base_version)
    new = copy.deepcopy(lines)
    applied = []
    seen = set()
    tmpl = {}
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
        if a["class"] == "IGNORED_SMALL":
            tmpl.setdefault(a["covered_by_line_id"], copy.deepcopy(ln))
        if a["class"] == "RELEASED":
            ln["evidence_state"] = "MEASURED" if r["label"] == "MEASURED" else PROVISIONAL
            ln["measured_net"], ln["bounded_range"] = _r(a["net"]), None
        elif a["class"] == "HELD":
            ln["evidence_state"], ln["measured_net"] = BOUNDED, None
            ln["bounded_range"] = {"low": _r(a["low"]), "high": _r(a["high"]), "rule": RULE}
        else:
            ln["evidence_state"], ln["measured_net"], ln["bounded_range"] = "EXCLUDED_WITH_REASON", None, None
            ln["notes"] = _reason(r)
        if "gross" in ln:
            ln["gross"] = None
        ln["method_label"], ln["fill_basis"] = r["label"], r["basis"]
        applied.append(r)
    missing = sorted(set(rows) - {r["line_id"] for r in applied})
    if missing:
        raise FillError(f"{len(missing)} row(s) name no base line: {missing[:5]}")
    clash = sorted(set(added) & seen)
    if clash:
        raise FillError(f"added line id already in the base: {clash[:3]}")
    for lid, x in sorted(added.items()):
        t = tmpl.get(lid)
        if t is None:
            raise FillError(f"{x['line_id']}: an added line covers no ignored piece of the base (no template)")
        new.append(_boq_added(x, lid, t))
    _assert_outside(lines, new, rows, len(added))
    return new, applied


# ------------------------------------------------------------------------------------------------ checks / diff
def _canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _assert_outside(old, new, rows, n_added=0):
    if len(old) + n_added != len(new):
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


def diff_rows(applied, added=()):
    out = []
    for r in sorted(applied, key=lambda r: r["line_id"]):
        a = r["after"]
        out.append({"line_id": r["line_id"], "set": r.get("set"), "item_code": r["item_code"], "unit": r["unit"],
                    "element_id": r.get("element_id"), "before_class": r["before"].get("class"),
                    "before_net": r["before"].get("net"), "before_low": r["before"].get("low"),
                    "before_high": r["before"].get("high"),
                    "after_class": a["class"] if a["class"] in ("RELEASED", "HELD") else "EXCLUDED",
                    "after_net": a.get("net"), "after_low": a.get("low"), "after_high": a.get("high"),
                    "label": r["label"], "basis": r["basis"] if a["class"] in ("RELEASED", "HELD") else _reason(r)})
    for lid, x in sorted(dict(added).items()):
        out.append({"line_id": lid, "set": x["set"], "item_code": x["item_code"], "unit": x["unit"],
                    "element_id": f"{x['set']}:{x['line_id']}", "before_class": "ABSENT", "before_net": None,
                    "before_low": None, "before_high": None, "after_class": "RELEASED",
                    "after_net": x["after"]["net"], "after_low": None, "after_high": None, "label": x["label"],
                    "basis": x["basis"]})
    return out


def write(out, base_lines, rows_doc, base_version=EXTENDS):
    """the hub's V3_0_81_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied = apply_boq_lines(base_lines, rows_doc, base_version)
    added = check_package(rows_doc, base_version)[1]
    for ln in new[len(base_lines):]:
        BL.validate(ln)
    d = diff_rows(applied, added)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        by_set[r.get("set") or "-"] = by_set.get(r.get("set") or "-", 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_81_lines": len(new), "applied": len(applied), "added": len(added),
             "by_set": by_set, "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": base_version, "rule": [RULE, RULE_NET],
           "released_default": False, "identity": ident}
    files = {"V3_0_81_BOQ_LINES.json": BL.dumps(new), "V3_0_81_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_81_DIFF.csv": buf.getvalue(), "V3_0_81_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return {"policy_id": POLICY_ID, "method": METHOD, "extends": EXTENDS, "rule": [RULE, RULE_NET],
            "labels": list(LABELS), "row_schemas": list(ROW_SCHEMAS), "package_schema": PACKAGE_SCHEMA,
            "valued_state_for_non_measured": PROVISIONAL, "materiality_m3": MATERIALITY_M3,
            "safety_min_m3": SAFETY_MIN_M3, "default_switched": False, "verified": False}
