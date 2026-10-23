"""BOQ EXPORT V1 (task T-235, hand-in r1) - ONE command that writes a candidate BOQ as BOQ.xlsx + BOQ.csv +
EXPORT_MANIFEST.json from the SAME canonical row list. A read-only tool, NOT a method version: it reads one candidate
V3_0_x_BOQ_LINES.json (engine/source/boq_line.py lines), computes, changes and approves no engine quantity, and nothing
in engine/ imports it. General: no project name, item code or element id is written in this module.

    python3 -I tools/boq_export_v1.py --lines V3_0_x_BOQ_LINES.json --candidate-version ARCH_TAKEOFF_V3.0.x
        --out OUT_DIR [--verdicts-v1 CHECKER_VERDICTS.json --key-map KEY_MAP.json] [--inventory INVENTORY.json]
        [--expect-project ID] [--expect-revision-set SHA256] [--code-commit SHA]

Rows and order. One row per canonical line, plus one UNMEASURED row per inventory element that no line carries; rows
sorted by (trade, item code, floor, element id, line id), so producer order never changes a byte (probe 11). Nothing is
dropped: the row count is checked against lines + unmeasured elements.

Refused (ExportError, nothing written): lines of more than one project id or revision set, or not the expected ones
(probe 10); an inventory of another project / revision set; a quantity line (MEASURED / SOURCE_DERIVED / PROVISIONAL)
whose measured_net is 0 while the line shows no input that produces the 0: no gross and no numeric calculation input
(probe 5b: HELD is never shown as 0); a line that fails boq_line.validate; two lines with one line id; a sealed
benchmark input (engine.reference_mapping.refuse_if_sealed).

Quantity state, one column each, never merged (owner 19:45 (0c)): VERIFIED, VERIFIED ZERO, VERIFIED COMPONENT (owner
20:59), MEASURED UNVERIFIED, HELD (blank quantity + reason + range when bounded), UNMEASURED (blank: an inventory
element with no line), EXCLUDED (blank + reason). An unknown is an EMPTY cell in CSV and XLSX, never 0.

VERIFIED comes ONLY from a structured bound verdict (URBAN_CHECKER_VERDICT_V2 records, owner 19:45 (0)) that this
module re-binds to the exported line: project, revision set, candidate version, BOQ_LINES sha256, unit, engine qty and
element scope must all equal the line's (else STALE); checker vs engine above 1 % is a DISCREPANCY (the line becomes
HELD); a WHOLE verdict needs the group's complete line and element scope and a passing completeness record
(T-236: inventory count = element scope count, MISSING 0, DUPLICATED 0, HELD 0) before any row reads VERIFIED;
COMPONENT verdicts make single rows VERIFIED COMPONENT and never add up to a VERIFIED line. Records of the V1 file
(URBAN_SCOREBOARD_CHECKER_VERDICTS_V1), the line's own evidence_state / evidence_status and board text never make a
row VERIFIED: V1 records are shown in the verdict column as V1_NOT_BINDING. r1 (this hand-in) offers no CLI input for
V2 records and no completeness input: the export shows VERIFIED 0 by construction; r2 adds the V2 schema file, its
validator, the CLI flag and the 'verdict add' helper.

Owner status class per row (BLOCKWORK_RESOLUTION_PROGRAMME s.2): VERIFIED (a bound counted verdict); PROJECT-SPECIFIC
(a quantity that rests on an owner-approved input: the line states "ASSUMED - OWNER-APPROVED", material state
PROJECT_OWNER_FACT or geometry OWNER_FACT); SOURCE-SUPPORTED PENDING INDEPENDENT CHECK (any other quantity);
OWNER DECISION REQUIRED (a held line whose rfi says so explicitly: rfi.owner_decision_required true); HELD (every other
held, unmeasured or discrepant row). EXCLUDED rows carry the class EXCLUDED.

Line groups. A BOQ line in the owner's sense (CONC.FOOTING, ...) is the group (trade, item code, unit) of its element
lines plus the inventory elements of that item. The trade summary reports per group: VERIFIED / PARTIALLY VERIFIED n / m
/ NOT VERIFIED, the verified subtotal apart (never labelled the line quantity), the unverified measured sum, the held
range, held and unmeasured components by name; per trade: verified whole lines n / d, and VERIFIED only when every
group of it is. Totals sum numeric rows only and state how many rows carry no quantity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.source import boq_line as BL                    # noqa: E402

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only export tool; it produces no quantity, so no guard to run
SCHEMA = "URBAN_BOQ_EXPORT_V1"
MANIFEST_SCHEMA = "URBAN_BOQ_EXPORT_MANIFEST_V1"
INVENTORY_SCHEMA = "URBAN_BOQ_EXPORT_INVENTORY_V1"
V1_VERDICTS_SCHEMA = "URBAN_SCOREBOARD_CHECKER_VERDICTS_V1"
V2_VERDICT_SCHEMA = "URBAN_CHECKER_VERDICT_V2"
COMPLETENESS_SCHEMA = "URBAN_LINE_COMPLETENESS_V1"
DISCREPANCY_REL = 0.01          # WORKFLOW_CONTROLS s.1
QTY_MATCH_TOL = 0.0005          # tools/scoreboard_v2.py QTY_MATCH_TOL: the verdict's engine qty must be this line's
DEC = 6                         # fixed decimals of every quantity written

VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT = "VERIFIED", "VERIFIED ZERO", "VERIFIED COMPONENT"
MEASURED_UNVERIFIED, HELD, UNMEASURED, EXCLUDED = "MEASURED UNVERIFIED", "HELD", "UNMEASURED", "EXCLUDED"
QSTATES = (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT, MEASURED_UNVERIFIED, HELD, UNMEASURED, EXCLUDED)
CLS_VERIFIED, CLS_SOURCE = "VERIFIED", "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
CLS_PROJECT, CLS_OWNER, CLS_HELD, CLS_EXCLUDED = "PROJECT-SPECIFIC", "OWNER DECISION REQUIRED", "HELD", "EXCLUDED"
OWNER_APPROVED_WORDS = ("ASSUMED - OWNER-APPROVED", "ASSUMED — OWNER-APPROVED", "ASSUMED_OWNER_APPROVED")

COLUMNS = ("line_id", "trade", "item_code", "item_en", "item_ar", "floor", "element_id", "unit", "gross",
           "deductions_n", "deductions_total", "net", "quantity_state", "qty_verified", "qty_verified_zero",
           "qty_verified_component", "qty_measured_unverified", "held_reason", "held_low", "held_high",
           "unmeasured_reason", "excluded_reason", "evidence_state", "line_stated_evidence_status",
           "owner_status_class", "verdict_id", "verdict_commit", "checker_qty", "verdict_status", "source_sheets",
           "project_id", "revision_set_sha256", "candidate_version")
SUMMARY_COLUMNS = ("trade", "item_code", "unit", "line_status", "rows", "verified_rows", "verified_subtotal",
                   "measured_unverified_sum", "measured_unverified_rows", "held_rows", "held_low", "held_high",
                   "unmeasured_rows", "excluded_rows", "rows_without_quantity", "held_components",
                   "unmeasured_components", "trade_status", "trade_verified_whole_lines")


class ExportError(ValueError):
    pass


# ---- small helpers --------------------------------------------------------------------------------------------------

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _fx(x):
    """a quantity as fixed decimals text ('' for an unknown: never 0)."""
    if x is None:
        return ""
    v = round(float(x), DEC)
    if v == 0:
        v = 0.0                                   # no '-0.000000'
    return f"{v:.{DEC}f}"


def _num(x):
    return None if x is None else round(float(x), DEC)


def _has_numeric_leaf(obj):
    if isinstance(obj, bool):
        return False
    if isinstance(obj, (int, float)):
        return True
    if isinstance(obj, dict):
        return any(_has_numeric_leaf(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_numeric_leaf(v) for v in obj)
    return False


def _deductions(ln):
    ds = ln.get("deductions") or []
    vals = []
    for d in ds:
        v = None
        if isinstance(d, (int, float)) and not isinstance(d, bool):
            v = d
        elif isinstance(d, dict):
            for k in ("area", "qty", "quantity", "value", "net"):
                if isinstance(d.get(k), (int, float)) and not isinstance(d.get(k), bool):
                    v = d[k]
                    break
        vals.append(v)
    total = sum(vals) if vals and all(v is not None for v in vals) else None
    return len(ds), total


def _doc_text(d):
    if isinstance(d, dict):
        for k in ("title", "file", "name", "sheet", "path", "id"):
            if d.get(k):
                s = str(d[k])
                if d.get("sheet") and k != "sheet":
                    s += f" / {d['sheet']}"
                if d.get("page") is not None:
                    s += f" p.{d['page']}"
                return s
        return json.dumps(d, sort_keys=True, ensure_ascii=False)
    return str(d)


def _stated_status(ln):
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    v = inp.get("evidence_status") if isinstance(inp, dict) else None
    return str(v) if v else ""


def _project_specific(ln):
    st = _stated_status(ln).upper()
    return (any(w.upper() == st for w in OWNER_APPROVED_WORDS) or ln.get("material_state") == "PROJECT_OWNER_FACT"
            or (ln.get("source") or {}).get("geometry_source") == "OWNER_FACT")


def sort_key(row):
    return (str(row["trade"] or ""), str(row["item_code"] or ""), str(row["floor"] or ""), str(row["element_id"] or ""),
            str(row["line_id"] or ""))


def group_key(row):
    return (str(row["trade"] or ""), str(row["item_code"] or ""), str(row["unit"] or ""))


# ---- identity -------------------------------------------------------------------------------------------------------

def identity(lines, expect_project=None, expect_revision_set=None):
    """(project_id, revision_set_sha256) shared by every line; refused when mixed or not the expected pair (probe 10)."""
    pids = sorted({str((ln.get("project") or {}).get("project_id")) for ln in lines})
    revs = sorted({str((ln.get("project") or {}).get("revision_set_sha256")) for ln in lines})
    if not lines:
        raise ExportError("no lines: an empty BOQ is not exported")
    if len(pids) != 1:
        raise ExportError(f"lines of {len(pids)} project ids {pids}: one BOQ is one project (refused)")
    if len(revs) != 1:
        raise ExportError(f"lines of {len(revs)} revision sets: one BOQ is one pinned revision set (refused)")
    pid, rev = pids[0], revs[0]
    if pid in ("None", "") or rev in ("None", ""):
        raise ExportError("a line without its project id or revision set (refused)")
    if expect_project is not None and pid != expect_project:
        raise ExportError(f"project id {pid} is not the expected {expect_project} (refused)")
    if expect_revision_set is not None and rev != expect_revision_set:
        raise ExportError(f"revision set {rev[:12]} is not the expected {expect_revision_set[:12]} (refused)")
    return pid, rev


def check_zero(ln):
    """probe 5b: a quantity line at 0 must show the input that gives 0 (a gross, or a numeric calculation input)."""
    if ln["evidence_state"] in BL.QUANTITY_STATES and ln.get("measured_net") is not None \
            and abs(float(ln["measured_net"])) <= 1e-12:
        inputs = (ln.get("calculation") or {}).get("inputs") or {}
        if ln.get("gross") is None and not _has_numeric_leaf(inputs):
            raise ExportError(f"{ln['line_id']}: a {ln['evidence_state']} zero with no gross and no numeric input: "
                              "a missing quantity is HELD, never 0 (refused)")


# ---- verdicts -------------------------------------------------------------------------------------------------------

def v1_verdict_refs(v1_doc, key_map_doc):
    """{item_code: [V1 verdict reference text]} (shown, never binding). Without a key map nothing can be placed."""
    if v1_doc is None:
        return {}
    if v1_doc.get("schema") != V1_VERDICTS_SCHEMA:
        raise ExportError(f"V1 verdict file schema {v1_doc.get('schema')!r} is not {V1_VERDICTS_SCHEMA}")
    if key_map_doc is None:
        raise ExportError("V1 verdicts need the key map that places their reference ids on item codes")
    codes_by_ref = {}
    for k in key_map_doc.get("keys") or []:
        codes_by_ref[k["reference_id"]] = list(k.get("item_codes") or [])
    out = defaultdict(list)
    for i, v in enumerate(v1_doc.get("verdicts") or []):
        txt = f"V1#{i} {v.get('kind')}/{v.get('scope')} commit {v.get('commit')}"
        if v.get("checker_qty") is not None:
            txt += f" checker {v.get('checker_qty')} {v.get('unit') or ''}".rstrip()
        for code in codes_by_ref.get(v.get("ref_id"), []):
            out[code].append(txt)
    return {k: sorted(v) for k, v in out.items()}


def bind_verdict(v, ident, group_lines, group_elements):
    """status of one V2 record against the exported group: COUNTED, or why not (never raises for a stale record)."""
    pid, rev, cver, bsha = ident
    if v.get("schema") != V2_VERDICT_SCHEMA:
        return "NOT_V2"
    need = ("verdict_id", "project_id", "revision_set_sha256", "candidate_version", "boq_lines_sha256", "line_ids",
            "element_scope", "unit", "engine_qty", "checker_qty", "evidence", "checker", "scope", "time")
    if any(v.get(k) in (None, "", [], {}) for k in need):
        return "BINDING_INCOMPLETE"
    ch = v["checker"] or {}
    if not all(ch.get(k) for k in ("run_token", "routine", "verdict_commit")):
        return "BINDING_INCOMPLETE"
    if (v["project_id"], v["revision_set_sha256"], v["candidate_version"], v["boq_lines_sha256"]) != (pid, rev, cver,
                                                                                                      bsha):
        return "STALE"
    ids = set(v["line_ids"])
    lines = [ln for ln in group_lines if ln["line_id"] in ids]
    if len(lines) != len(ids):
        return "STALE"
    if any(ln["unit"] != v["unit"] for ln in lines):
        return "STALE"
    scope = v["element_scope"] or {}
    els = sorted(str(x) for x in scope.get("ids") or [])
    if scope.get("count") != len(els):
        return "BINDING_INCOMPLETE"
    if els != sorted(str(ln["location"]["element_id"]) for ln in lines):
        return "SCOPE_DIFFERS"
    if any(ln["evidence_state"] not in BL.QUANTITY_STATES + ("NOT_APPLICABLE_WITH_EVIDENCE",) for ln in lines):
        return "LINE_NOT_MEASURED"                # a held or excluded line has no quantity a verdict could confirm
    eq = sum(float(ln["measured_net"] or 0.0) for ln in lines)
    if abs(float(v["engine_qty"]) - eq) > QTY_MATCH_TOL:
        return "STALE"
    if v["scope"] == "WHOLE":
        if sorted(ids) != sorted(ln["line_id"] for ln in group_lines) or els != sorted(group_elements):
            return "SCOPE_DIFFERS"
    elif v["scope"] == "COMPONENT":
        if len(lines) != 1:
            return "SCOPE_DIFFERS"
    else:
        return "PARTIAL_SCOPE"
    cq = float(v["checker_qty"])
    if eq == 0:
        if abs(cq) > QTY_MATCH_TOL:
            return "DISCREPANCY"
    elif abs(cq - eq) / abs(eq) > DISCREPANCY_REL:
        return "DISCREPANCY"
    return "COUNTED"


def completeness_passes(rec, ident, gkey, group_elements):
    """a T-236 completeness record for one group: same project / revision set, inventory = element scope, MISSING 0,
    DUPLICATED 0, HELD 0."""
    if not rec or rec.get("schema") != COMPLETENESS_SCHEMA:
        return False
    pid, rev, _c, _b = ident
    if (rec.get("project_id"), rec.get("revision_set_sha256")) != (pid, rev):
        return False
    if (rec.get("trade"), rec.get("item_code"), rec.get("unit")) != gkey:
        return False
    return (rec.get("inventory_count") == len(group_elements) == rec.get("element_scope_count")
            and rec.get("missing") == 0 and rec.get("duplicated") == 0 and rec.get("held") == 0)


# ---- rows -----------------------------------------------------------------------------------------------------------

def _base_row(ln, pid, rev, cver):
    n, dtot = _deductions(ln)
    return {"line_id": ln["line_id"], "trade": ln["trade"], "item_code": ln["item_code"], "item_en": ln["item_en"],
            "item_ar": ln["item_ar"], "floor": ln["location"].get("floor"),
            "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "gross": _num(ln.get("gross")),
            "deductions_n": n, "deductions_total": _num(dtot), "net": None, "quantity_state": None,
            "qty_verified": None, "qty_verified_zero": None, "qty_verified_component": None,
            "qty_measured_unverified": None, "held_reason": "", "held_low": None, "held_high": None,
            "unmeasured_reason": "", "excluded_reason": "", "evidence_state": ln["evidence_state"],
            "line_stated_evidence_status": _stated_status(ln), "owner_status_class": None, "verdict_id": "",
            "verdict_commit": "", "checker_qty": None, "verdict_status": "NONE",
            "source_sheets": "; ".join(_doc_text(d) for d in (ln.get("source") or {}).get("documents") or []),
            "project_id": pid, "revision_set_sha256": rev, "candidate_version": cver}


def _state_row(row, ln):
    ev = ln["evidence_state"]
    if ev in BL.QUANTITY_STATES:
        row["quantity_state"] = MEASURED_UNVERIFIED
        row["net"] = row["qty_measured_unverified"] = _num(ln["measured_net"])
        row["owner_status_class"] = CLS_PROJECT if _project_specific(ln) else CLS_SOURCE
    elif ev in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
        row["quantity_state"] = EXCLUDED
        row["excluded_reason"] = f"{ev}: {ln.get('notes') or ''}".strip()
        row["owner_status_class"] = CLS_EXCLUDED
    else:                                            # BOUNDED_EXPOSURE, BLOCKED_RFI
        row["quantity_state"] = HELD
        rfi = ln.get("rfi") or {}
        row["held_reason"] = f"{ev}: {rfi.get('question') or ln.get('notes') or 'unresolved'}"
        br = ln.get("bounded_range") or {}
        if br.get("low") is not None and br.get("high") is not None:
            row["held_low"], row["held_high"] = _num(br["low"]), _num(br["high"])
        row["owner_status_class"] = CLS_OWNER if rfi.get("owner_decision_required") is True else CLS_HELD
    return row


def build(lines, *, candidate_version, boq_lines_sha256, v1_doc=None, key_map_doc=None, inventory_doc=None,
          v2_records=(), completeness=None, expect_project=None, expect_revision_set=None):
    """-> {"rows": [...canonical order], "summary": [...], "trades": [...], "identity": {...}, "counts": {...}}.
    v2_records / completeness: r1 accepts them only here (tests); the CLI passes none -> VERIFIED 0 by construction."""
    if not candidate_version:
        raise ExportError("the candidate version is stated, never read from a file name")
    seen = set()
    for ln in lines:
        BL.validate(ln)
        if ln["line_id"] in seen:
            raise ExportError(f"{ln['line_id']}: one line id twice (refused)")
        seen.add(ln["line_id"])
        check_zero(ln)
    pid, rev = identity(lines, expect_project, expect_revision_set)
    ident = (pid, rev, candidate_version, boq_lines_sha256)

    rows = []
    by_line = {}
    for ln in lines:
        row = _state_row(_base_row(ln, pid, rev, candidate_version), ln)
        rows.append(row)
        by_line[ln["line_id"]] = (row, ln)

    # inventory elements no line carries -> UNMEASURED rows (a silently dropped held row shows up here)
    inv_elements = defaultdict(set)
    if inventory_doc is not None:
        if inventory_doc.get("schema") != INVENTORY_SCHEMA:
            raise ExportError(f"inventory schema {inventory_doc.get('schema')!r} is not {INVENTORY_SCHEMA}")
        if (inventory_doc.get("project_id"), inventory_doc.get("revision_set_sha256")) != (pid, rev):
            raise ExportError("inventory of another project or revision set (refused)")
        carried = {(ln["item_code"], ln["unit"], str(ln["location"].get("element_id"))) for ln in lines}
        names = {}
        for e in inventory_doc.get("elements") or []:
            code, unit, eid = e.get("item_code"), e.get("unit"), str(e.get("element_id") or "")
            if not code or not unit or not eid:
                raise ExportError(f"inventory element {e!r}: item_code, unit and element_id are required")
            if (code, unit, eid) in names:
                raise ExportError(f"inventory element {code} {eid} listed twice (refused)")
            names[(code, unit, eid)] = e
            if code in BL.ITEMS:
                trade, en, ar = BL.ITEMS[code][2], BL.ITEMS[code][0], BL.ITEMS[code][1]
            else:
                trade, en, ar = e.get("trade"), e.get("item_en") or code, e.get("item_ar") or ""
            inv_elements[(str(trade), code, unit)].add(eid)
            if (code, unit, eid) in carried:
                continue
            rows.append({c: None for c in COLUMNS} | {
                "line_id": "", "trade": trade, "item_code": code, "item_en": en, "item_ar": ar,
                "floor": e.get("floor"), "element_id": eid, "unit": unit, "deductions_n": 0, "quantity_state": UNMEASURED,
                "held_reason": "", "unmeasured_reason": f"inventory element with no BOQ line ({e.get('label') or eid})",
                "excluded_reason": "", "evidence_state": "", "line_stated_evidence_status": "",
                "owner_status_class": CLS_HELD, "verdict_id": "", "verdict_commit": "", "verdict_status": "NONE",
                "source_sheets": str(e.get("source") or ""), "project_id": pid, "revision_set_sha256": rev,
                "candidate_version": candidate_version})

    # groups (the owner's BOQ line = trade + item + unit)
    groups = defaultdict(list)
    for r in rows:
        groups[group_key(r)].append(r)
    glines = {g: [by_line[r["line_id"]][1] for r in rs if r["line_id"]] for g, rs in groups.items()}

    # V1 references (shown only)
    v1 = v1_verdict_refs(v1_doc, key_map_doc)
    for r in rows:
        refs = v1.get(r["item_code"])
        if refs:
            r["verdict_id"] = " | ".join(refs)
            r["verdict_status"] = "V1_NOT_BINDING"

    # V2 bound verdicts
    whole_ok = {}
    for v in sorted(v2_records or (), key=lambda x: str(x.get("verdict_id"))):
        ids = set(v.get("line_ids") or ())
        hit = [g for g, ls in glines.items() if ids & {ln["line_id"] for ln in ls}]
        if len(hit) != 1:
            continue                                  # a record on no line or across groups binds nothing here
        g = hit[0]
        g_el = sorted({str(ln["location"]["element_id"]) for ln in glines[g]} | inv_elements.get(g, set()))
        st = bind_verdict(v, ident, glines[g], g_el)
        for lid in sorted(ids):
            if lid not in by_line:
                continue
            row, ln = by_line[lid]
            row["verdict_id"] = str(v.get("verdict_id"))
            row["verdict_commit"] = str((v.get("checker") or {}).get("verdict_commit") or "")
            row["checker_qty"] = _num(v.get("checker_qty")) if v.get("scope") == "COMPONENT" else None
            row["verdict_status"] = f"{st} ({v.get('scope')})"
            if st == "DISCREPANCY" and row["quantity_state"] == MEASURED_UNVERIFIED:
                row["quantity_state"], row["qty_measured_unverified"], row["net"] = HELD, None, None
                row["held_reason"] = (f"Checker DISCREPANCY above 1 %: engine {_fx(ln['measured_net'])} vs checker "
                                      f"{_fx(v.get('checker_qty'))} {ln['unit']} (verdict {v.get('verdict_id')})")
                row["owner_status_class"] = CLS_HELD
            elif st == "COUNTED" and v.get("scope") == "COMPONENT" and row["quantity_state"] == MEASURED_UNVERIFIED:
                row["quantity_state"] = VERIFIED_COMPONENT
                row["qty_verified_component"], row["qty_measured_unverified"] = row["net"], None
                row["owner_status_class"] = CLS_VERIFIED
        if st == "COUNTED" and v.get("scope") == "WHOLE":
            whole_ok[g] = v

    for g, v in whole_ok.items():
        g_el = sorted({str(ln["location"]["element_id"]) for ln in glines[g]} | inv_elements.get(g, set()))
        if not completeness_passes((completeness or {}).get(g), ident, g, g_el):
            for r in groups[g]:
                if r["line_id"] in set(v["line_ids"]):
                    r["verdict_status"] = "COUNTED (WHOLE; completeness record missing or failing: not VERIFIED)"
            continue
        for r in groups[g]:
            if r["quantity_state"] == EXCLUDED and r["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
                r["quantity_state"], r["qty_verified_zero"] = VERIFIED_ZERO, 0.0
                r["owner_status_class"], r["verdict_status"] = CLS_VERIFIED, "COUNTED (WHOLE)"
            elif r["quantity_state"] in (MEASURED_UNVERIFIED, VERIFIED_COMPONENT):
                q = r["net"]
                r["qty_measured_unverified"] = r["qty_verified_component"] = None
                if q == 0:
                    r["quantity_state"], r["qty_verified_zero"] = VERIFIED_ZERO, 0.0
                else:
                    r["quantity_state"], r["qty_verified"] = VERIFIED, q
                r["owner_status_class"] = CLS_VERIFIED
                r["checker_qty"] = _num(v["checker_qty"])
                r["verdict_status"] = "COUNTED (WHOLE)"

    rows.sort(key=sort_key)
    if len(rows) != len(lines) + sum(1 for r in rows if r["quantity_state"] == UNMEASURED):
        raise ExportError("row count differs from lines + unmeasured elements: a row was dropped (refused)")
    summary, trades = _summary(rows, groups, whole_ok, completeness, ident, inv_elements, glines)
    counts = {s: sum(1 for r in rows if r["quantity_state"] == s) for s in QSTATES}
    return {"schema": SCHEMA, "rows": rows, "summary": summary, "trades": trades, "counts": counts,
            "identity": {"project_id": pid, "revision_set_sha256": rev, "candidate_version": candidate_version,
                         "boq_lines_sha256": boq_lines_sha256},
            "completeness_input": "none (T-236 not merged): no line can read VERIFIED" if not completeness else "given"}


def _summary(rows, groups, whole_ok, completeness, ident, inv_elements, glines):
    out = []
    for g in sorted(groups):
        rs = sorted(groups[g], key=sort_key)
        ver_rows = [r for r in rs if r["quantity_state"] in (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT)]
        whole = all(r["quantity_state"] in (VERIFIED, VERIFIED_ZERO, EXCLUDED) for r in rs) and \
            any(r["quantity_state"] in (VERIFIED, VERIFIED_ZERO) for r in rs)
        if whole:
            status = "VERIFIED"
        elif ver_rows:
            status = f"PARTIALLY VERIFIED {len(ver_rows)} / {len(rs)}"
        else:
            status = "NOT VERIFIED"
        vsub = sum((r["qty_verified"] or 0.0) + (r["qty_verified_zero"] or 0.0) + (r["qty_verified_component"] or 0.0)
                   for r in ver_rows)
        mu = [r for r in rs if r["quantity_state"] == MEASURED_UNVERIFIED]
        held = [r for r in rs if r["quantity_state"] == HELD]
        bounded = [r for r in held if r["held_low"] is not None]
        unm = [r for r in rs if r["quantity_state"] == UNMEASURED]
        exc = [r for r in rs if r["quantity_state"] == EXCLUDED]
        out.append({
            "trade": g[0], "item_code": g[1], "unit": g[2], "line_status": status, "rows": len(rs),
            "verified_rows": len(ver_rows), "verified_subtotal": _num(vsub) if ver_rows else None,
            "measured_unverified_sum": _num(sum(r["qty_measured_unverified"] for r in mu)) if mu else None,
            "measured_unverified_rows": len(mu), "held_rows": len(held),
            "held_low": _num(sum(r["held_low"] for r in bounded)) if bounded else None,
            "held_high": _num(sum(r["held_high"] for r in bounded)) if bounded else None,
            "unmeasured_rows": len(unm), "excluded_rows": len(exc),
            "rows_without_quantity": len(held) + len(unm) + len(exc),
            "held_components": "; ".join(f"{r['element_id']}" + (f" [{_fx(r['held_low'])} .. {_fx(r['held_high'])}]"
                                                                   if r["held_low"] is not None else " [no range]")
                                         for r in held),
            "unmeasured_components": "; ".join(str(r["element_id"]) for r in unm),
            "trade_status": "", "trade_verified_whole_lines": ""})
    trades = []
    for t in sorted({s["trade"] for s in out}):
        ss = [s for s in out if s["trade"] == t]
        n = sum(1 for s in ss if s["line_status"] == "VERIFIED")
        tstat = "VERIFIED" if n == len(ss) else ("PARTIALLY VERIFIED" if n or any(
            s["line_status"].startswith("PARTIALLY") for s in ss) else "NOT VERIFIED")
        for s in ss:
            s["trade_status"], s["trade_verified_whole_lines"] = tstat, f"{n} / {len(ss)}"
        trades.append({"trade": t, "status": tstat, "verified_whole_lines": n, "lines": len(ss),
                       "partially_verified": [f"{s['item_code']} [{s['unit']}] {s['line_status']}" for s in ss
                                              if s["line_status"].startswith("PARTIALLY")]})
    return out, trades


# ---- writers --------------------------------------------------------------------------------------------------------

def _cell_text(c, v):
    if v is None:
        return ""
    if isinstance(v, float) or (isinstance(v, int) and c not in ("deductions_n",) and not isinstance(v, bool)):
        return _fx(v) if c not in ("rows", "verified_rows", "measured_unverified_rows", "held_rows",
                                   "unmeasured_rows", "excluded_rows", "rows_without_quantity",
                                   "deductions_n") else str(v)
    return str(v)


def csv_bytes(rows, columns=COLUMNS):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(columns)
    for r in rows:
        w.writerow([_cell_text(c, r.get(c)) for c in columns])
    return buf.getvalue().encode("utf-8")


def xlsx_write(path, rows, summary, manifest_rows):
    from openpyxl import Workbook

    from engine.reporting_v3 import book as BK
    wb = Workbook()
    wb.properties.creator = "Urban Projects"
    wb.properties.created = wb.properties.modified = BK.CREATED
    for title, cols, data in (("BOQ", COLUMNS, rows), ("Trade summary", SUMMARY_COLUMNS, summary),
                              ("Manifest", ("key", "value"), manifest_rows)):
        ws = wb.active if title == "BOQ" else wb.create_sheet(title)
        ws.title = title
        ws.append(list(cols))
        for r in data:
            vals = []
            for c in cols:
                v = r.get(c)
                if v is None or v == "":
                    vals.append(None)                 # an unknown is an EMPTY cell, never 0
                elif isinstance(v, float):
                    vals.append(round(v, DEC))
                else:
                    vals.append(v)
            ws.append(vals)
    wb.save(path)
    BK._repack(path)                                  # fixed core.xml and zip entry times: same content, same bytes


def _code_commit(given):
    if given:
        return given
    try:
        return subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[1]), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=10, check=True).stdout.strip() or "UNKNOWN"
    except Exception:                                 # noqa: BLE001 - outside a checkout the commit is unknown
        return "UNKNOWN"


def export(lines, out_dir, *, candidate_version, boq_lines_sha256, input_sha256=None, code_commit="NOT_RECORDED",
           **kw):
    """build + write BOQ.csv, BOQ.xlsx, EXPORT_MANIFEST.json into out_dir; -> the manifest."""
    res = build(lines, candidate_version=candidate_version, boq_lines_sha256=boq_lines_sha256, **kw)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cb = csv_bytes(res["rows"])
    (out / "BOQ.csv").write_bytes(cb)
    (out / "BOQ_TRADE_SUMMARY.csv").write_bytes(csv_bytes(res["summary"], SUMMARY_COLUMNS))
    ident = res["identity"]
    mrows = [{"key": k, "value": str(v)} for k, v in (
        ("schema", SCHEMA), ("candidate_version", ident["candidate_version"]), ("project_id", ident["project_id"]),
        ("revision_set_sha256", ident["revision_set_sha256"]), ("boq_lines_sha256", ident["boq_lines_sha256"]),
        ("code_commit", code_commit), ("rows", len(res["rows"])),
        ("completeness_input", res["completeness_input"]),
        ("verified_rule", "VERIFIED only from a bound V2 verdict + passing completeness record; V1 never"))]
    for k in sorted(res["counts"]):
        mrows.append({"key": f"rows {k}", "value": str(res["counts"][k])})
    xlsx_write(out / "BOQ.xlsx", res["rows"], res["summary"], mrows)
    manifest = {"schema": MANIFEST_SCHEMA, "export_schema": SCHEMA, "identity": ident, "code_commit": code_commit,
                "inputs_sha256": dict(sorted((input_sha256 or {}).items())),
                "outputs": {f: sha256_bytes((out / f).read_bytes())
                            for f in ("BOQ.csv", "BOQ.xlsx", "BOQ_TRADE_SUMMARY.csv")},
                "row_counts": res["counts"] | {"total": len(res["rows"])},
                "trades": res["trades"], "completeness_input": res["completeness_input"],
                "semantic_sha256": semantic_sha256(res["rows"])}
    (out / "EXPORT_MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
    return manifest


def semantic_sha256(rows):
    """identity of rows, quantities, states and order, independent of the file format bytes."""
    sem = [[r.get(c) if not isinstance(r.get(c), float) else _fx(r.get(c)) for c in COLUMNS] for r in rows]
    return sha256_bytes(json.dumps(sem, ensure_ascii=False, sort_keys=False).encode("utf-8"))


def read_csv(path):
    """read-back: rows as dicts of text (an empty cell stays '')."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path):
    from engine.reference_mapping import refuse_if_sealed
    refuse_if_sealed(str(path))
    b = Path(path).read_bytes()
    return json.loads(b.decode("utf-8")), sha256_bytes(b)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--lines", required=True)
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verdicts-v1")
    ap.add_argument("--key-map")
    ap.add_argument("--inventory")
    ap.add_argument("--expect-project")
    ap.add_argument("--expect-revision-set")
    ap.add_argument("--code-commit")
    a = ap.parse_args(argv)
    lines, lsha = _load_json(a.lines)
    if isinstance(lines, dict):
        raise ExportError("--lines must be a list of canonical lines (V3_0_x_BOQ_LINES.json)")
    shas = {"lines": lsha}
    docs = {}
    for k, p in (("verdicts_v1", a.verdicts_v1), ("key_map", a.key_map), ("inventory", a.inventory)):
        if p:
            docs[k], shas[k] = _load_json(p)
    m = export(lines, a.out, candidate_version=a.candidate_version, boq_lines_sha256=lsha, input_sha256=shas,
               code_commit=_code_commit(a.code_commit), v1_doc=docs.get("verdicts_v1"),
               key_map_doc=docs.get("key_map"), inventory_doc=docs.get("inventory"),
               expect_project=a.expect_project, expect_revision_set=a.expect_revision_set)
    print(json.dumps({"outputs": m["outputs"], "row_counts": m["row_counts"],
                      "trades": [{k: t[k] for k in ("trade", "status", "verified_whole_lines", "lines")}
                                 for t in m["trades"]]}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
