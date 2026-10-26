"""BOQ EXPORT V1 (task T-235, hand-in r1) - ONE command that writes a candidate BOQ as BOQ.xlsx + BOQ.csv +
EXPORT_MANIFEST.json from the SAME canonical row list. A read-only tool, NOT a method version: it reads one candidate
V3_0_x_BOQ_LINES.json (engine/source/boq_line.py lines), computes, changes and approves no engine quantity, and nothing
in engine/ imports it. General: no project name, item code or element id is written in this module.

    python3 -I tools/boq_export_v1.py --lines V3_0_x_BOQ_LINES.json --candidate-version ARCH_TAKEOFF_V3.0.x
        --out OUT_DIR [--verdicts-v1 CHECKER_VERDICTS.json --key-map KEY_MAP.json] [--inventory INVENTORY.json]
        [--expect-project ID] [--expect-revision-set SHA256] [--code-commit SHA] [--identity V3_0_16_IDENTITY.json]
        [--engine-units | --contract-units]          (default: the contractual export, reinforcement in t; T-298)

Rows and order. One row per canonical line, plus one UNMEASURED row per inventory element that no line carries; rows
sorted by (trade, item code, floor, element id, line id), so producer order never changes a byte (probe 11). Nothing is
dropped: the row count is checked against lines + unmeasured elements.

Refused (ExportError, nothing written): lines of more than one project id or revision set, or not the expected ones
(probe 10); an inventory of another project / revision set; a quantity line (MEASURED / SOURCE_DERIVED / PROVISIONAL)
whose measured_net is 0 while the line shows no input that produces the 0: no gross and no numeric calculation input
(probe 5b: HELD is never shown as 0); a line that fails boq_line.validate; two lines with one line id; a sealed
benchmark input (engine.reference_mapping.refuse_if_sealed).

A quantity line whose own bounded_range is open (low < high: a convention range) keeps its net in MEASURED UNVERIFIED
and its range in open_range_low / open_range_high, counted per group: the range is never dropped.

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
row VERIFIED: V1 records are shown in the verdict column as V1_NOT_BINDING. Without --verdicts-v2 AND --completeness
the export shows VERIFIED 0 by construction.

r2 (V2 verdicts). The record schema is URBAN_CHECKER_VERDICT_V2 (schema_document(); published as
research/agents_t235/URBAN_CHECKER_VERDICT_V2.schema.json, a test keeps the two equal); a verdict file is a
URBAN_CHECKER_VERDICT_V2_SET {"schema", "verdicts": [records sorted by verdict_id]}. validate_v2() checks one record's
form (every binding field present and well formed, the routine a Checker / Verifier); bind_verdict() then checks it
against the exported line. The Checker never types the binding: 'verdict add' fills project, revision set, candidate
version, BOQ_LINES sha256, unit, engine qty and element scope from the candidate lines; the Checker types line ids (or
one item code), scope, checker qty, evidence and its run identity. A record that binds nothing in this export is listed
in the manifest (v2_verdicts) with its status, never dropped.

    python3 -I tools/boq_export_v1.py verdict-add --lines V3_0_x_BOQ_LINES.json --candidate-version V
        (--line-ids ID,ID,.. | --item-code CODE [--unit U]) --scope WHOLE|PARTIAL|COMPONENT --checker-qty Q
        --evidence "SHEET=PRINTED VALUE" [--evidence ..] (--lock-file docs/agents/locks/checker.lock |
        --run-token T --routine Verifier) --verdict-commit SHA [--time ISO-UTC] --out VERDICTS_V2.json
    python3 -I tools/boq_export_v1.py verdict-validate VERDICTS_V2.json          exit 1 on any problem

Contract units (T-273, opt-in --contract-units). Reinforcement is contracted in metric tons (owner 2026-10-24). The
canonical rows stay in engine units (BOQ.csv / sheet BOQ, the unit every V2 verdict binds to, so no verdict is
invalidated); the flag adds BOQ_CONTRACT_UNITS.csv + BOQ_CONTRACT_TOTALS.csv (schema URBAN_BOQ_CONTRACT_UNITS_V1) and
the XLSX sheets "BOQ (contract units)" / "Contract totals", and raises the manifest to URBAN_BOQ_EXPORT_MANIFEST_V2.
t = kg / 1000 once, here; 6 decimals; totals converted from the unrounded kg sums; kg and t rows of one BOQ line
together are refused (mixed units). Without the flag every byte written is as before.

Contractual default (T-298, owner 2026-10-25 11:51 (0) 'correct tonne reporting'). The COMMAND LINE now writes the
contractual export by default (schema URBAN_BOQ_EXPORT_V2, manifest URBAN_BOQ_EXPORT_MANIFEST_V3): BOQ.csv, sheet BOQ,
BOQ_TRADE_SUMMARY.csv and sheet Trade summary carry reinforcement in t (contract_view: kg / 1000 once, 6 decimals,
totals from the unrounded kg sums), with unit / engine_unit / conversion and the audit columns engine_<quantity column>
(the kg value beside the t value); BOQ_ENGINE_UNITS.csv and BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv are the engine-unit V1
files byte for byte (the rows V2 verdicts bind to; semantic_sha256 is theirs, so no verdict moves with the unit).
Refused: kg and t rows in one BOQ line (mixed), a row converted twice, a t row of an item registered in kg
(pre-converted or relabelled). --engine-units is the opt-out (V1 bytes); --contract-units keeps the T-273 layout.
export() itself keeps its V1 default (contractual=False) for library callers.

Identity (T-245). The verdict binding boq_lines_sha256 is the sha256 of the CANONICAL line content (lines_sha256:
engine/source/boq_line.dumps, sorted keys), never the raw file bytes (the raw sha256 stays in inputs_sha256 as
provenance). A candidate of ARCH_TAKEOFF_V3.0.16 or later carries one project id and one revision set over every
drawing; --identity takes its V3_0_16_IDENTITY.json (URBAN_BOQ_PROJECT_IDENTITY_V1), refused unless it is the lines'
own project and its documents give the lines' revision set (one revision per sheet), and states each drawing's
revision state, the disclosures (an UNCONFIRMED revision with why) and the INTERNAL REVIEW CANDIDATE label in the
manifest (project_identity) and the XLSX Manifest sheet. Probe 10 is unchanged: lines of two project ids or two
revision sets are refused.

Downgrade-only records (T-245 (f), owner 2026-10-24 23:53 / 23:57). --downgrades takes a URBAN_CHECKER_DOWNGRADE_V1_SET
('downgrade-add' fills the binding from the lines; Checker routines only). A record binds project, revision set, line
ids, unit and the candidate quantity it downgrades (engine_qty); it carries no quantity of its own. A VALID unresolved
record moves each of its lines to HELD (reason "HELD: ..." or "CONFLICT: ...", its basis label) even when a V2 verdict
made the line VERIFIED (the verdict is shown OVERRIDDEN); the candidate quantity appears only in
BOQ_AUDIT_UNSUPPORTED_BASIS.csv / the XLSX sheet "Audit (unsupported basis)"; the candidate lines are not changed.
A record of another project, on a missing line, or whose lines' quantity changed binds nothing and is listed (STALE ...).
Without --downgrades every byte written is as before.

Per-line binding (T-294). 'verdict add' / 'downgrade add' now write binding "LINE_CONTENT_V1" and line_content_sha256:
the sha256 of boq_line.dumps of exactly the record's own lines (sorted by line id: every field of each, so its quantity,
rule version, evidence state, unit, element and source drawings). Such a record stays bound while those lines are
byte-identical, whatever happens to any other line or to the candidate version (an integration that leaves its lines
unchanged leaves it valid); a change of any own field, or an own line id that is absent, makes it STALE (a downgrade:
listed STALE, not applied). candidate_version and boq_lines_sha256 remain as provenance. Records without the field
(issued under the T-245 whole-file binding) keep that binding unchanged, never auto-migrated as valid:

    python3 -I tools/boq_export_v1.py verdict-rebind --verdicts OLD_SET.json --old-lines OLD_LINES.json
        --old-candidate-version V_OLD --lines NEW_LINES.json --candidate-version V_NEW (--lock-file .. | --run-token T
        --routine Verifier) --verdict-commit SHA [--time ISO-UTC] --out NEW_SET.json

re-issues (Checker routines only) each record whose own lines are byte-identical in the old and new candidate as a
new LINE_CONTENT_V1 record (rebound_from = the old id, the Checker's quantity and evidence unchanged), after proving
the old record's own binding on the old lines; every other record is reported STALE and nothing is written for it.
A downgrade of an already-HELD row (BLOCKED_RFI, ...) keeps that row's own held reason, class and range and appends
the record (T-294 (h)).

Part (4) (completeness from T-236). --completeness takes the merged T-236 report (tools/trade_completeness.py
TRADE_COMPLETENESS.json, schema URBAN_TRADE_COMPLETENESS_V1; its reference_line_rows() per trade). The report carries no
project id, so it is bound by its line ids: a report naming any line id this BOQ does not carry is refused. Per BOQ
line (trade, item, unit) the record passes only when its lines map to ONE principal trade (line_trade), that trade maps
to this one BOQ line, every line of it is in the report and linked, the trade is COMPLETE_AGAINST_INVENTORY with
missing / duplicated / held / conflict / geometry-only / unresolved / register-only / out-of-scope all 0, no refused
deduction, and inventory count = element scope count; else the summary names each blocker. The report's MISSING,
CONFLICT and geometry-only elements become UNMEASURED rows (in the trade's one BOQ line, or under the principal trade id
with a blank item when the trade maps to none or several), and a principal trade with no line and no inventory is one
UNMEASURED row: nothing is absent. --inventory (V1) and --completeness are one inventory each: both together refused.

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
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL                    # noqa: E402
from engine.source import trade_completeness_v1 as TC       # noqa: E402  (stdlib-only check module, T-236)

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only export tool; it produces no quantity, so no guard to run
SCHEMA = "URBAN_BOQ_EXPORT_V1"
MANIFEST_SCHEMA = "URBAN_BOQ_EXPORT_MANIFEST_V1"
INVENTORY_SCHEMA = "URBAN_BOQ_EXPORT_INVENTORY_V1"
V1_VERDICTS_SCHEMA = "URBAN_SCOREBOARD_CHECKER_VERDICTS_V1"
V2_VERDICT_SCHEMA = "URBAN_CHECKER_VERDICT_V2"
COMPLETENESS_SCHEMA = "URBAN_LINE_COMPLETENESS_V1"
V2_SET_SCHEMA = "URBAN_CHECKER_VERDICT_V2_SET"
IDENTITY_SCHEMA = "URBAN_BOQ_PROJECT_IDENTITY_V1"   # T-245: engine/source/arch_v3016 V3_0_16_IDENTITY.json
# T-245 (f) (owner 2026-10-24 23:53 / 23:57 (1), (2)): a Checker-issued, line-bound DOWNGRADE-ONLY record; it can
# only move an exported line to HELD / CONFLICT, never promote one, and carries no Checker measurement
DOWNGRADE_SCHEMA = "URBAN_CHECKER_DOWNGRADE_V1"
DOWNGRADE_SET_SCHEMA = "URBAN_CHECKER_DOWNGRADE_V1_SET"
DOWNGRADE_REQUIRED = ("schema", "downgrade_id", "project_id", "revision_set_sha256", "candidate_version", "line_ids",
                      "unit", "engine_qty", "state", "basis_label", "reason", "evidence", "checker", "time")
DOWNGRADE_STATES = ("HELD", "CONFLICT")
# T-294 (Verifier 07:58 T-245 Gate B (d)): a record binds the canonical content of ITS OWN lines, not the whole file.
# A record carrying binding LINE_CONTENT_V1 + line_content_sha256 is checked against its own lines only (project id,
# revision set, presence, unit, content); candidate_version / boq_lines_sha256 stay as provenance (where it was
# issued). A record without it is a T-245 record: its whole-file binding is kept as it was (valid only on the candidate
# it was issued on, STALE elsewhere), never migrated: the Checker re-binds it with 'verdict-rebind' or re-verifies.
LINE_BINDING = "LINE_CONTENT_V1"
AUDIT_COLUMNS = ("line_id", "trade", "item_code", "floor", "element_id", "unit", "candidate_qty", "basis_label",
                 "downgrade_state", "downgrade_id", "reason", "verdict_overridden")
REVIEW_LABEL = "INTERNAL REVIEW CANDIDATE (not released; released default ARCH_TAKEOFF_V2.9 + route G)"
# T-273 (owner 2026-10-24 14:23 / 15:31): the contractual BOQ unit of reinforcement is the metric ton. The canonical rows
# (BOQ.csv, kg, the unit every V2 verdict binds to) are unchanged; the CONTRACT-UNIT view is an explicit, opt-in
# migration (--contract-units) with its own schema and a raised manifest schema: t = kg / 1000, applied ONCE here, at
# 6 decimals; group totals are converted from the unrounded kg sums, never summed from rounded t rows.
CONTRACT_SCHEMA = "URBAN_BOQ_CONTRACT_UNITS_V1"
MANIFEST_SCHEMA_CONTRACT = "URBAN_BOQ_EXPORT_MANIFEST_V2"
CONTRACT_UNIT = {"kg": ("t", 1000.0)}           # engine unit -> (contract unit, divisor)
CONTRACT_QTY_COLUMNS = ("gross", "deductions_total", "net", "qty_verified", "qty_verified_zero",
                        "qty_verified_component", "qty_measured_unverified", "open_range_low", "open_range_high",
                        "held_low", "held_high", "checker_qty")
V2_REQUIRED = ("schema", "verdict_id", "project_id", "revision_set_sha256", "candidate_version", "boq_lines_sha256",
               "line_ids", "element_scope", "unit", "engine_qty", "checker_qty", "evidence", "checker", "scope", "time")
V2_SCOPES = ("WHOLE", "PARTIAL", "COMPONENT")
CHECKER_ROUTINES = ("CHECKER", "VERIFIER")      # the run-lock agent names of the Checker (docs/agents/locks)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{6,40}$")
_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?Z$")
PRINTED_KEYS = ("printed_value", "printed", "value")
# T-236 element statuses that are an inventory element with no BOQ line (shown as UNMEASURED rows)
REPORT_UNMEASURED = ("MISSING", "CONFLICT", "INVENTORY_GEOMETRY_ONLY")
REPORT_BLOCKERS = ("missing", "duplicated", "held", "conflict", "geometry_only", "unresolved", "register_only",
                   "out_of_inventory_scope")
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
           "qty_verified_component", "qty_measured_unverified", "open_range_low", "open_range_high", "held_reason", "held_low", "held_high",
           "unmeasured_reason", "excluded_reason", "evidence_state", "line_stated_evidence_status",
           "owner_status_class", "verdict_id", "verdict_commit", "checker_qty", "verdict_status", "source_sheets",
           "project_id", "revision_set_sha256", "candidate_version")
CONTRACT_COLUMNS = COLUMNS[:COLUMNS.index("unit")] + ("unit", "engine_unit", "conversion") + \
    COLUMNS[COLUMNS.index("unit") + 1:]
CONTRACT_TOTAL_COLUMNS = ("trade", "item_code", "unit", "engine_unit", "line_status", "rows",
                          "measured_unverified_engine_sum", "measured_unverified_sum", "verified_engine_sum",
                          "verified_sum", "held_low", "held_high", "rows_without_quantity")
SUMMARY_COLUMNS = ("trade", "item_code", "unit", "line_status", "rows", "verified_rows", "verified_subtotal",
                   "measured_unverified_sum", "measured_unverified_rows", "open_range_rows", "open_range_components",
                   "held_rows", "held_low", "held_high",
                   "unmeasured_rows", "excluded_rows", "rows_without_quantity", "held_components",
                   "unmeasured_components", "trade_status", "trade_verified_whole_lines", "completeness")
# T-298 (owner 2026-10-25 11:51 (0), 'correct tonne reporting'): the CONTRACTUAL export is the DEFAULT of the command
# line (--engine-units is the opt-out that writes the V1 bytes): BOQ.csv / sheet BOQ / the trade summary carry
# reinforcement in t (kg / 1000, once, contract_view); the engine-unit value of every quantity column stays beside it in
# the audit columns engine_<column>, and BOQ_ENGINE_UNITS.csv / BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv are the V1 rows
# byte for byte (the rows every V2 verdict binds to: binding and semantic_sha256 unchanged).
CONTRACTUAL_SCHEMA = "URBAN_BOQ_EXPORT_V2"
MANIFEST_SCHEMA_CONTRACTUAL = "URBAN_BOQ_EXPORT_MANIFEST_V3"
ENGINE_AUDIT_COLUMNS = tuple(f"engine_{c}" for c in CONTRACT_QTY_COLUMNS)
CONTRACTUAL_COLUMNS = CONTRACT_COLUMNS + ENGINE_AUDIT_COLUMNS
CONTRACTUAL_SUMMARY_COLUMNS = SUMMARY_COLUMNS[:3] + ("engine_unit",) + SUMMARY_COLUMNS[3:]


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


def schema_document():
    """the URBAN_CHECKER_VERDICT_V2 record schema (JSON Schema 2020-12 form; the published schema file equals it)."""
    s = {"type": "string", "minLength": 1}
    sha = {"type": "string", "pattern": _SHA_RE.pattern}
    qty = {"type": "number", "minimum": 0}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urban-projects/URBAN_CHECKER_VERDICT_V2",
        "title": V2_VERDICT_SCHEMA,
        "description": ("One Checker verdict bound to the exact exported BOQ line(s) it re-measured (owner 2026-10-23 "
                        "19:45 (0)). The sole authority for VERIFIED in tools/boq_export_v1.py: a record whose binding "
                        "differs from the exported line is STALE; checker vs engine above 1 % is a DISCREPANCY (the line "
                        "is HELD); only scope WHOLE plus a passing completeness record makes a line VERIFIED; COMPONENT "
                        "records never add up to a VERIFIED line. Records live in a " + V2_SET_SCHEMA + " file "
                        "{schema, verdicts: [records sorted by verdict_id]}."),
        "type": "object",
        "required": list(V2_REQUIRED),
        "properties": {
            "schema": {"const": V2_VERDICT_SCHEMA},
            "verdict_id": s,
            "project_id": s,
            "revision_set_sha256": sha,
            "candidate_version": s,
            "boq_lines_sha256": sha,
            "line_ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": s},
            "element_scope": {"type": "object", "required": ["ids", "count"],
                              "properties": {"ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": s},
                                             "count": {"type": "integer", "minimum": 1}},
                              "description": "sorted element ids of the bound lines; count = len(ids)"},
            "unit": {"enum": list(BL.UNITS)},
            "engine_qty": qty | {"description": "sum of measured_net of the bound lines (the exported quantity)"},
            "checker_qty": qty | {"description": "the Checker's own re-measure from the drawing"},
            "evidence": {"type": "array", "minItems": 1,
                         "items": {"type": "object", "required": ["sheet"],
                                   "properties": {"sheet": s, "printed_value": s, "printed": s, "value": s},
                                   "anyOf": [{"required": [k]} for k in PRINTED_KEYS]}},
            "checker": {"type": "object", "required": ["run_token", "routine", "verdict_commit"],
                        "properties": {"run_token": s,
                                       "routine": {"type": "string", "description": "Checker / Verifier (run-lock agent)"},
                                       "verdict_commit": {"type": "string", "pattern": _COMMIT_RE.pattern}}},
            "scope": {"enum": list(V2_SCOPES)},
            "time": {"type": "string", "pattern": _TIME_RE.pattern},
            "notes": {"type": "string"},
            "binding": {"const": LINE_BINDING,
                        "description": "T-294: bound to the canonical content of its own lines (line_content_sha256); "
                                       "absent = a T-245 record bound to the whole candidate (boq_lines_sha256)"},
            "line_content_sha256": sha | {"description": "sha256 of boq_line.dumps of the record's own lines, sorted "
                                                         "by line id"},
            "rebound_from": s | {"description": "the verdict id this record re-binds (verdict-rebind)"}},
        "dependentRequired": {"binding": ["line_content_sha256"], "line_content_sha256": ["binding"]}}


def _isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_v2(v):
    """-> [problem text] for one record's form (empty: well formed). Binding to the export is bind_verdict's job."""
    if not isinstance(v, dict):
        return ["record: not an object"]
    p = []
    if v.get("schema") != V2_VERDICT_SCHEMA:
        p.append(f"schema: {v.get('schema')!r} is not {V2_VERDICT_SCHEMA}")
    for k in V2_REQUIRED:
        if v.get(k) in (None, "", [], {}):
            p.append(f"{k}: required")
    for k in ("verdict_id", "project_id", "candidate_version"):
        if k in v and not (isinstance(v[k], str) and v[k].strip()):
            p.append(f"{k}: a non-empty text")
    for k in ("revision_set_sha256", "boq_lines_sha256"):
        if v.get(k) not in (None, "") and not (isinstance(v[k], str) and _SHA_RE.match(v[k])):
            p.append(f"{k}: 64 lower-case hex characters")
    ids = v.get("line_ids")
    if ids not in (None, []):
        if not isinstance(ids, list) or not all(isinstance(x, str) and x for x in ids):
            p.append("line_ids: a list of line id texts")
        elif len(set(ids)) != len(ids):
            p.append("line_ids: a line id listed twice")
    sc = v.get("element_scope")
    if sc not in (None, {}):
        els = sc.get("ids") if isinstance(sc, dict) else None
        if not isinstance(els, list) or not els or not all(isinstance(x, str) and x for x in els):
            p.append("element_scope: ids is a non-empty list of element id texts")
        elif len(set(els)) != len(els):
            p.append("element_scope: an element id listed twice")
        elif not (isinstance(sc.get("count"), int) and not isinstance(sc.get("count"), bool)
                  and sc["count"] == len(els)):
            p.append(f"element_scope: count {sc.get('count')!r} is not the {len(els)} ids listed")
    if v.get("unit") not in (None, "") and v["unit"] not in BL.UNITS:
        p.append(f"unit: {v['unit']!r} is not one of {BL.UNITS}")
    for k in ("engine_qty", "checker_qty"):
        if k in v and v[k] is not None and not (_isnum(v[k]) and v[k] >= 0):
            p.append(f"{k}: a non-negative number")
    ev = v.get("evidence")
    if ev not in (None, []):
        if not isinstance(ev, list) or not all(
                isinstance(e, dict) and isinstance(e.get("sheet"), str) and e["sheet"].strip()
                and any(e.get(k) not in (None, "") for k in PRINTED_KEYS) for e in ev):
            p.append("evidence: every entry names its sheet and the printed value read there")
    ch = v.get("checker")
    if ch not in (None, {}):
        if not isinstance(ch, dict) or not all(isinstance(ch.get(k), str) and ch[k].strip()
                                               for k in ("run_token", "routine", "verdict_commit")):
            p.append("checker: run_token, routine and verdict_commit are required")
        else:
            if not any(ch["routine"].strip().upper().startswith(r) for r in CHECKER_ROUTINES):
                p.append(f"checker.routine: {ch['routine']!r} is not the Checker (a verdict is the Checker's alone)")
            if not _COMMIT_RE.match(ch["verdict_commit"]):
                p.append("checker.verdict_commit: a commit sha (6 to 40 hex characters)")
    if v.get("scope") not in (None, "") and v["scope"] not in V2_SCOPES:
        p.append(f"scope: {v['scope']!r} is not one of {V2_SCOPES}")
    if v.get("time") not in (None, "") and not (isinstance(v["time"], str) and _TIME_RE.match(v["time"])):
        p.append("time: ISO 8601 UTC, e.g. 2026-10-24T10:00:00Z")
    p += _binding_problems(v)
    if "rebound_from" in v and not (isinstance(v["rebound_from"], str) and v["rebound_from"].strip()):
        p.append("rebound_from: a verdict id text")
    return p


def _binding_problems(r):
    """T-294: binding and line_content_sha256 come together, the binding is the one known kind, the sha well formed."""
    has_b, has_s = "binding" in r, "line_content_sha256" in r
    if not has_b and not has_s:
        return []
    p = []
    if has_b != has_s:
        p.append("binding: binding and line_content_sha256 are given together (a half binding binds nothing)")
    if has_b and r["binding"] != LINE_BINDING:
        p.append(f"binding: {r['binding']!r} is not {LINE_BINDING}")
    if has_s and not (isinstance(r["line_content_sha256"], str) and _SHA_RE.match(r["line_content_sha256"])):
        p.append("line_content_sha256: 64 lower-case hex characters")
    return p


def line_bound(r):
    """True for a T-294 record (bound to its own lines' content); False for a T-245 whole-file record."""
    return isinstance(r, dict) and r.get("binding") == LINE_BINDING


def _set_problems(doc):
    if not isinstance(doc, dict) or doc.get("schema") != V2_SET_SCHEMA:
        return [f"set: schema is not {V2_SET_SCHEMA}"]
    vs = doc.get("verdicts")
    if not isinstance(vs, list):
        return ["set: verdicts is a list"]
    ids = [str(v.get("verdict_id")) for v in vs if isinstance(v, dict)]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    return [f"set: verdict id {i} listed twice" for i in dup]


def validate_v2_set(doc):
    """-> [problem text] for a whole verdict file: the set's form plus each record's (prefixed by its verdict id)."""
    p = _set_problems(doc)
    if any(x.startswith(("set: schema", "set: verdicts")) for x in p):
        return p
    for i, v in enumerate(doc["verdicts"]):
        vid = v.get("verdict_id") if isinstance(v, dict) and v.get("verdict_id") else f"#{i}"
        p += [f"{vid}: {x}" for x in validate_v2(v)]
    return p


def lines_sha256(lines):
    """sha256 of the canonical bytes of a line list (engine/source/boq_line.dumps), as a candidate writes them."""
    return sha256_bytes(BL.dumps(lines).encode("utf-8"))


def line_content_sha256(own_lines):
    """T-294: sha256 of the canonical bytes (boq_line.dumps) of exactly a record's own lines, sorted by line id: every
    field of each line (quantity, unit, rule version, evidence state, element, source drawings) is in it, no other
    line and no candidate version is. Refused for an empty list or a line id given twice."""
    ids = [ln["line_id"] for ln in own_lines]
    if not ids or len(set(ids)) != len(ids):
        raise ExportError("a line content binding needs at least one line, each once")
    return lines_sha256(sorted(own_lines, key=lambda ln: ln["line_id"]))


def own_content_status(r, by_id):
    """T-294: None when a LINE_CONTENT_V1 record's own lines are all in by_id ({line_id: line}) and byte-identical to
    what it bound; else the reason it is STALE (an absent line is STALE, never silently valid)."""
    missing = sorted(i for i in r["line_ids"] if i not in by_id)
    if missing:
        return f"line(s) {missing[:3]} not in this candidate"
    if line_content_sha256([by_id[i] for i in r["line_ids"]]) != r["line_content_sha256"]:
        return "the content of its own line(s) changed"
    return None


def verdict_add(lines, *, candidate_version, boq_lines_sha256, line_ids, scope, checker_qty, evidence, run_token,
                routine, verdict_commit, time, verdict_id=None, notes=None):
    """-> one URBAN_CHECKER_VERDICT_V2 record whose binding is filled from the candidate lines (the Checker types
    only line ids, scope, checker qty, evidence and its own run identity). Refused (ExportError): an unknown or
    repeated line id, a held / excluded line (no quantity to confirm), lines of two units, two project ids or revision
    sets, COMPONENT over more than one line, a record that fails validate_v2 (e.g. a routine that is not the Checker)."""
    for ln in lines:
        BL.validate(ln)
    pid, rev = identity(lines)
    by_id = {ln["line_id"]: ln for ln in lines}
    ids = list(line_ids)
    if len(set(ids)) != len(ids):
        raise ExportError("a line id listed twice")
    if not ids:
        raise ExportError("no line id: a verdict binds at least one line")
    unknown = sorted(set(ids) - set(by_id))
    if unknown:
        raise ExportError(f"unknown line id(s) {unknown[:3]}: not in this candidate")
    sel = [by_id[i] for i in sorted(ids)]
    for ln in sel:
        if ln["evidence_state"] not in BL.QUANTITY_STATES + ("NOT_APPLICABLE_WITH_EVIDENCE",):
            raise ExportError(f"{ln['line_id']}: a {ln['evidence_state']} line is not measured: no quantity for a "
                              "verdict to confirm")
    units = sorted({ln["unit"] for ln in sel})
    if len(units) != 1:
        raise ExportError(f"lines of more than one unit {units}: one verdict, one unit")
    if scope == "COMPONENT" and len(sel) != 1:
        raise ExportError("a COMPONENT verdict binds exactly one line")
    els = sorted(str(ln["location"]["element_id"]) for ln in sel)
    rec = {"schema": V2_VERDICT_SCHEMA, "project_id": pid, "revision_set_sha256": rev,
           "candidate_version": candidate_version, "boq_lines_sha256": boq_lines_sha256,
           "line_ids": sorted(ids), "element_scope": {"ids": els, "count": len(els)}, "unit": units[0],
           "engine_qty": _num(sum(float(ln["measured_net"] or 0.0) for ln in sel)),
           "checker_qty": _num(checker_qty) if _isnum(checker_qty) else checker_qty,
           "evidence": [dict(sorted(e.items())) for e in evidence],
           "checker": {"run_token": run_token, "routine": routine, "verdict_commit": verdict_commit},
           "scope": scope, "time": time, "binding": LINE_BINDING, "line_content_sha256": line_content_sha256(sel)}
    if notes:
        rec["notes"] = notes
    rec["verdict_id"] = verdict_id or "V2-" + sha256_bytes(json.dumps(rec, sort_keys=True, ensure_ascii=False)
                                                           .encode("utf-8"))[:16]
    probs = validate_v2(rec)
    if probs:
        raise ExportError("; ".join(probs))
    return dict(sorted(rec.items()))


def validate_downgrade(d):
    """-> [problem text] for one URBAN_CHECKER_DOWNGRADE_V1 record's form (binding is apply_downgrades' job)."""
    if not isinstance(d, dict):
        return ["record: not an object"]
    p = []
    if d.get("schema") != DOWNGRADE_SCHEMA:
        p.append(f"schema: {d.get('schema')!r} is not {DOWNGRADE_SCHEMA}")
    for k in DOWNGRADE_REQUIRED:
        if d.get(k) in (None, "", [], {}):
            p.append(f"{k}: required")
    for k in ("checker_qty", "qty", "measured_net", "corrected_qty"):
        if k in d:
            p.append(f"{k}: a downgrade carries no quantity of its own (never a Checker measurement; downgrade only)")
    if d.get("state") not in (None, "") and d["state"] not in DOWNGRADE_STATES:
        p.append(f"state: {d['state']!r} is not one of {DOWNGRADE_STATES} (a record can only downgrade)")
    if d.get("revision_set_sha256") not in (None, "") and not (isinstance(d["revision_set_sha256"], str)
                                                               and _SHA_RE.match(d["revision_set_sha256"])):
        p.append("revision_set_sha256: 64 lower-case hex characters")
    ids = d.get("line_ids")
    if ids not in (None, []) and (not isinstance(ids, list) or not all(isinstance(x, str) and x for x in ids)
                                  or len(set(ids)) != len(ids)):
        p.append("line_ids: a list of distinct line id texts")
    if d.get("unit") not in (None, "") and d["unit"] not in BL.UNITS:
        p.append(f"unit: {d['unit']!r}")
    if "engine_qty" in d and d["engine_qty"] is not None and not _isnum(d["engine_qty"]):
        p.append("engine_qty: a number (the candidate quantity the record downgrades)")
    v2like = {"evidence": d.get("evidence"), "checker": d.get("checker"), "time": d.get("time")}
    p += [x for x in validate_v2(dict(v2like, schema=V2_VERDICT_SCHEMA))
          if x.split(":")[0] in ("evidence", "checker", "checker.routine", "checker.verdict_commit", "time")
          and not x.endswith(": required")]
    if "resolved" in d and not isinstance(d["resolved"], bool):
        p.append("resolved: true or false")
    p += _binding_problems(d)
    return p


def downgrade_add(lines, *, candidate_version, line_ids, state, basis_label, reason, evidence, run_token, routine,
                  verdict_commit, time, downgrade_id=None):
    """-> one URBAN_CHECKER_DOWNGRADE_V1 record, binding (project, revision set, unit, engine qty) filled from the
    candidate lines; the Checker types the line ids, state, basis label, reason, evidence and its run identity."""
    for ln in lines:
        BL.validate(ln)
    pid, rev = identity(lines)
    by_id = {ln["line_id"]: ln for ln in lines}
    ids = sorted(line_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ExportError("a downgrade names at least one line, each once")
    unknown = sorted(set(ids) - set(by_id))
    if unknown:
        raise ExportError(f"unknown line id(s) {unknown[:3]}: not in this candidate")
    sel = [by_id[i] for i in ids]
    units = sorted({ln["unit"] for ln in sel})
    if len(units) != 1:
        raise ExportError(f"lines of more than one unit {units}: one record, one unit")
    rec = {"schema": DOWNGRADE_SCHEMA, "project_id": pid, "revision_set_sha256": rev,
           "candidate_version": candidate_version, "line_ids": ids, "unit": units[0],
           "engine_qty": _num(sum(float(ln["measured_net"] or 0.0) for ln in sel)), "state": state,
           "basis_label": basis_label, "reason": reason, "evidence": [dict(sorted(e.items())) for e in evidence],
           "checker": {"run_token": run_token, "routine": routine, "verdict_commit": verdict_commit}, "time": time,
           "resolved": False, "binding": LINE_BINDING, "line_content_sha256": line_content_sha256(sel)}
    rec["downgrade_id"] = downgrade_id or "DG-" + sha256_bytes(json.dumps(rec, sort_keys=True, ensure_ascii=False)
                                                               .encode("utf-8"))[:16]
    probs = validate_downgrade(rec)
    if probs:
        raise ExportError("; ".join(probs))
    return dict(sorted(rec.items()))


def apply_downgrades(records, by_line, pid, rev):
    """T-245 (f) / (f2): apply each VALID downgrade to its rows: HELD (or CONFLICT) with the reason, the candidate
    quantity moved to the audit rows (labelled with the record's basis label), a VERIFIED / COMPONENT verdict on the
    line overridden while the record is unresolved. Never promotes: a row is only ever cleared to HELD. -> (statuses,
    audit rows). A record of another project / revision set, a missing line, another unit or a changed engine
    quantity binds nothing (listed with its status for the Checker; the line keeps its own state)."""
    status, audit = [], []
    for d in sorted(records or (), key=lambda x: str(x.get("downgrade_id"))):
        did = str(d.get("downgrade_id"))
        probs = validate_downgrade(d)
        if probs:
            status.append({"downgrade_id": did, "status": "INVALID: " + "; ".join(probs)})
            continue
        if (d["project_id"], d["revision_set_sha256"]) != (pid, rev):
            status.append({"downgrade_id": did, "status": "OTHER_PROJECT_OR_REVISION_SET"})
            continue
        if d.get("resolved") is True:
            status.append({"downgrade_id": did, "status": "RESOLVED (not applied)"})
            continue
        sel = [by_line.get(i) for i in d["line_ids"]]
        if any(x is None for x in sel):
            status.append({"downgrade_id": did, "status": "NO_LINE_IN_THIS_EXPORT" + (
                " (STALE: a line of the record is absent: Checker to review; not applied)" if line_bound(d) else "")})
            continue
        lns = [x[1] for x in sel]
        why = own_content_status(d, {ln["line_id"]: ln for ln in lns}) if line_bound(d) else None
        if why:                                   # T-294: its own lines changed since it was issued
            status.append({"downgrade_id": did, "status": f"STALE ({why}: Checker to review; not applied)"})
            continue
        eq = sum(float(ln["measured_net"] or 0.0) for ln in lns)
        if any(ln["unit"] != d["unit"] for ln in lns) or abs(eq - float(d["engine_qty"])) > QTY_MATCH_TOL:
            status.append({"downgrade_id": did, "status": "STALE (the lines' unit or quantity changed: Checker to "
                                                         "review; not applied)"})
            continue
        # F-T245-01 (Verifier 2026-10-25 07:58): an EXCLUDED (not-applicable / excluded with reason) row is not a
        # quantity of the BOQ at all; a downgrade never turns it into HELD (that would put a not-applicable element
        # into the held list). It stays EXCLUDED with its own reason, and the status names how many were left.
        kept = [(row, ln) for row, ln in sel if row["quantity_state"] == EXCLUDED]
        sel = [(row, ln) for row, ln in sel if row["quantity_state"] != EXCLUDED]
        for row, ln in sel:
            was = row["quantity_state"]
            over = was in (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT)
            audit.append({"line_id": row["line_id"], "trade": row["trade"], "item_code": row["item_code"],
                          "floor": row["floor"], "element_id": row["element_id"], "unit": row["unit"],
                          "candidate_qty": _num(ln.get("measured_net")), "basis_label": d["basis_label"],
                          "downgrade_state": d["state"], "downgrade_id": did, "reason": d["reason"],
                          "verdict_overridden": f"{was} {row['verdict_id']}".strip() if over else ""})
            text = f"{d['state']}: {d['reason']} ({d['basis_label']}; downgrade {did})"
            if was == HELD:
                # T-294 (h) (Verifier O-T245-03): an already-HELD row (BLOCKED_RFI, a discrepancy, ...) keeps its own
                # held reason, class and range; the record is appended, never written over it (no promotion either way)
                own = row["held_reason"] or ""
                row["held_reason"] = f"{own} | + {text}" if own else text
            else:
                for c in ("net", "qty_verified", "qty_verified_zero", "qty_verified_component",
                          "qty_measured_unverified", "open_range_low", "open_range_high"):
                    row[c] = None
                row["quantity_state"], row["owner_status_class"] = HELD, CLS_HELD
                row["held_reason"] = text
            if over or row["verdict_id"]:
                row["verdict_status"] = f"{row['verdict_status']} | OVERRIDDEN BY DOWNGRADE {did} (unresolved)"
        left = f"; {len(kept)} EXCLUDED row(s) left EXCLUDED" if kept else ""
        status.append({"downgrade_id": did, "status": f"APPLIED ({d['state']}, {len(sel)} line(s){left})"})
    return status, audit


def _dump_set(doc):
    return json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def verdict_set_append(path, rec):
    """add one valid record to a URBAN_CHECKER_VERDICT_V2_SET file (created when absent); records sorted by id;
    a verdict id already in the file is refused (a correction is a new record with its own id)."""
    probs = validate_v2(rec)
    if probs:
        raise ExportError("; ".join(probs))
    p = Path(path)
    if p.exists():
        doc, _sha = _load_json(p)
        sp = _set_problems(doc)
        if sp:
            raise ExportError(f"{p.name}: " + "; ".join(sp))
    else:
        doc = {"schema": V2_SET_SCHEMA, "verdicts": []}
    if any(v.get("verdict_id") == rec["verdict_id"] for v in doc["verdicts"]):
        raise ExportError(f"verdict id {rec['verdict_id']} is already in {p.name} (a correction is a new record)")
    doc["verdicts"] = sorted(doc["verdicts"] + [rec], key=lambda v: str(v.get("verdict_id")))
    p.write_text(_dump_set(doc), encoding="utf-8")
    return doc


def verdict_rebind(v, old_lines, new_lines, *, old_candidate_version, candidate_version, run_token, routine,
                   verdict_commit, time):
    """T-294: re-issue one V2 record on a new candidate as a LINE_CONTENT_V1 record, by the Checker, only when it is
    proven unchanged: (1) the record is well formed and its own binding holds on old_lines (a T-245 record: project,
    revision set, candidate version = old_candidate_version and boq_lines_sha256 = the old lines' canonical sha; a
    LINE_CONTENT_V1 record: project, revision set and its own lines' content); its lines are there with its unit, element
    scope and engine qty; (2) each of its lines is in new_lines byte-identical (same canonical content). The Checker's
    quantity, scope and evidence are carried unchanged; the rebinding run's identity is the record's checker, the old id
    is rebound_from. Refused (ExportError, nothing returned) otherwise: the reason is the record's STALE cause."""
    vid = str(v.get("verdict_id") if isinstance(v, dict) else None)
    probs = validate_v2(v) if isinstance(v, dict) else ["record: not an object"]
    if probs:
        raise ExportError(f"{vid}: not re-bindable: " + "; ".join(probs))
    for ln in list(old_lines) + list(new_lines):
        BL.validate(ln)
    opid, orev = identity(old_lines)
    npid, nrev = identity(new_lines)
    if (v["project_id"], v["revision_set_sha256"]) != (opid, orev):
        raise ExportError(f"{vid}: STALE: the old lines are another project or revision set than the record's")
    if (opid, orev) != (npid, nrev):
        raise ExportError(f"{vid}: STALE: the new candidate is another project or revision set (a new revision set is "
                          "a re-measure, never a re-bind)")
    oby = {ln["line_id"]: ln for ln in old_lines}
    nby = {ln["line_id"]: ln for ln in new_lines}
    if line_bound(v):
        why = own_content_status(v, oby)
        if why:
            raise ExportError(f"{vid}: STALE on the old lines: {why}")
    else:
        if v["candidate_version"] != old_candidate_version:
            raise ExportError(f"{vid}: STALE: issued on {v['candidate_version']}, not on {old_candidate_version}")
        if v["boq_lines_sha256"] != lines_sha256(old_lines):
            raise ExportError(f"{vid}: STALE: the old lines are not the candidate the record was issued on "
                              "(boq_lines_sha256 differs)")
    if any(i not in oby for i in v["line_ids"]):
        raise ExportError(f"{vid}: STALE: a line of the record is not in the old lines")
    own_old = [oby[i] for i in v["line_ids"]]
    if any(ln["unit"] != v["unit"] for ln in own_old):
        raise ExportError(f"{vid}: STALE: unit differs from the old lines")
    if sorted(str(x) for x in v["element_scope"]["ids"]) != sorted(str(ln["location"]["element_id"]) for ln in own_old):
        raise ExportError(f"{vid}: STALE: element scope differs from the old lines")
    if abs(sum(float(ln["measured_net"] or 0.0) for ln in own_old) - float(v["engine_qty"])) > QTY_MATCH_TOL:
        raise ExportError(f"{vid}: STALE: engine qty differs from the old lines")
    missing = sorted(i for i in v["line_ids"] if i not in nby)
    if missing:
        raise ExportError(f"{vid}: STALE: line(s) {missing[:3]} not in the new candidate")
    old_sha = line_content_sha256(own_old)
    new_sha = line_content_sha256([nby[i] for i in v["line_ids"]])
    if old_sha != new_sha:
        raise ExportError(f"{vid}: STALE: the content of its own line(s) changed between the candidates "
                          "(the Checker re-verifies; never re-bound)")
    rec = {k: copy_json(v[k]) for k in ("schema", "project_id", "revision_set_sha256", "line_ids", "element_scope",
                                         "unit", "engine_qty", "checker_qty", "evidence", "scope")}
    rec.update({"candidate_version": candidate_version, "boq_lines_sha256": lines_sha256(new_lines),
                "binding": LINE_BINDING, "line_content_sha256": new_sha, "rebound_from": vid,
                "checker": {"run_token": run_token, "routine": routine, "verdict_commit": verdict_commit},
                "time": time,
                "notes": (f"re-bound from {vid} ({v['candidate_version']}): own lines byte-identical"
                          + (f"; was: {v['notes']}" if v.get("notes") else ""))})
    rec["verdict_id"] = "V2-" + sha256_bytes(json.dumps(rec, sort_keys=True, ensure_ascii=False).encode("utf-8"))[:16]
    probs = validate_v2(rec)
    if probs:
        raise ExportError(f"{vid}: " + "; ".join(probs))
    return dict(sorted(rec.items()))


def copy_json(x):
    return json.loads(json.dumps(x))


def bind_verdict(v, ident, group_lines, group_elements):
    """status of one V2 record against the exported group: COUNTED, or why not (never raises for a stale record)."""
    pid, rev, cver, bsha = ident
    if not isinstance(v, dict) or v.get("schema") != V2_VERDICT_SCHEMA:
        return "NOT_V2"
    if validate_v2(v):
        return "BINDING_INCOMPLETE"
    ch = v["checker"] or {}
    if not all(ch.get(k) for k in ("run_token", "routine", "verdict_commit")):
        return "BINDING_INCOMPLETE"
    if line_bound(v):
        # T-294: bound to its own lines' content; the candidate version and the whole file are provenance only
        if (v["project_id"], v["revision_set_sha256"]) != (pid, rev):
            return "STALE"
    elif (v["project_id"], v["revision_set_sha256"], v["candidate_version"], v["boq_lines_sha256"]) != (pid, rev, cver,
                                                                                                        bsha):
        return "STALE"                            # a T-245 record: its whole-file binding, unchanged (never migrated)
    ids = set(v["line_ids"])
    lines = [ln for ln in group_lines if ln["line_id"] in ids]
    if len(lines) != len(ids):
        return "STALE"
    if line_bound(v) and own_content_status(v, {ln["line_id"]: ln for ln in lines}):
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


NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"


def na_has_evidence(ln):
    """T-298: a NOT_APPLICABLE line carries its evidence when it names WHY (notes) AND the document it was read on
    (at least one source document); a line with a reason but no document is a claim, not evidence."""
    return bool(str(ln.get("notes") or "").strip()) and bool((ln.get("source") or {}).get("documents"))


def scope_split(glines_g, elements):
    """T-298 (F-REC-01): the completeness scope of one BOQ line group. An element whose every line of the group is
    NOT_APPLICABLE with evidence is not an element of this line (a face the drawing classes as something else, a
    retired duplicate): it leaves the scope count, listed. One NA line without evidence keeps its element in the
    scope and is a blocker. -> (scope elements, NA-with-evidence elements, NA-without-evidence elements,
    NA-with-evidence line ids)."""
    by_el = defaultdict(list)
    for ln in glines_g:
        by_el[str(ln["location"].get("element_id"))].append(ln)
    na_ev, na_bad, na_lines = set(), set(), set()
    for e, ls in by_el.items():
        if any(ln["evidence_state"] == NA_STATE and not na_has_evidence(ln) for ln in ls):
            na_bad.add(e)
        elif ls and all(ln["evidence_state"] == NA_STATE for ln in ls):
            na_ev.add(e)
            na_lines |= {ln["line_id"] for ln in ls}
    return sorted(set(elements) - na_ev), sorted(na_ev), sorted(na_bad), na_lines


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
            and rec.get("missing") == 0 and rec.get("duplicated") == 0 and rec.get("held") == 0
            and not rec.get("blockers"))


def _report_line_ids(report):
    ids = set()
    for e in report.get("elements") or []:
        ids |= set(e.get("lines") or [])
    ids |= {d.get("line_id") for d in report.get("deductions") or []}
    for v in (report.get("unlinked_lines") or {}).values():
        ids |= set(v)
    ids.discard(None)
    return ids


def report_check(report, lines):
    """the T-236 report must be about THIS line set: schema, and no line id this BOQ does not carry (refused)."""
    if not isinstance(report, dict) or report.get("schema") != TC.SCHEMA:
        raise ExportError(f"completeness report schema {report.get('schema') if isinstance(report, dict) else None!r} "
                          f"is not {TC.SCHEMA} (tools/trade_completeness.py TRADE_COMPLETENESS.json)")
    known = {ln["line_id"] for ln in lines}
    foreign = sorted(_report_line_ids(report) - known)
    if foreign:
        raise ExportError(f"completeness report names {len(foreign)} line id(s) this BOQ does not carry "
                          f"(e.g. {foreign[0]}): it was computed on other lines (refused)")


def report_unmeasured_rows(report, lines, pid, rev, cver):
    """UNMEASURED rows from the T-236 report: each MISSING / CONFLICT / geometry-only element (placed in its trade's
    one BOQ line, else under the principal trade id with a blank item) and one row per principal trade with no line and
    no independent inventory. -> (rows, {group: set(element ids)})."""
    gt = defaultdict(set)                                 # principal trade -> BOQ line groups of its lines
    carried = set()
    for ln in lines:
        gt[TC.line_trade(ln)].add((str(ln["trade"]), ln["item_code"], ln["unit"]))
        carried.add((str(ln["trade"]), ln["item_code"], ln["unit"], str(ln["location"].get("floor")),
                     str(ln["location"].get("element_id"))))
    rows, inv = [], defaultdict(set)
    added = defaultdict(int)

    def _row(trade, code, unit, floor, eid, reason, source):
        if code in BL.ITEMS:
            en, ar = BL.ITEMS[code][0], BL.ITEMS[code][1]
        else:
            en, ar = trade, ""
        return {c: None for c in COLUMNS} | {
            "line_id": "", "trade": trade, "item_code": code, "item_en": en, "item_ar": ar, "floor": floor,
            "element_id": eid, "unit": unit, "deductions_n": 0, "quantity_state": UNMEASURED, "held_reason": "",
            "unmeasured_reason": reason, "excluded_reason": "", "evidence_state": "", "line_stated_evidence_status": "",
            "owner_status_class": CLS_HELD, "verdict_id": "", "verdict_commit": "", "verdict_status": "NONE",
            "source_sheets": source, "project_id": pid, "revision_set_sha256": rev, "candidate_version": cver}

    for e in sorted(report.get("elements") or [], key=lambda x: (x["trade"], x["key"])):
        if e["status"] not in REPORT_UNMEASURED or e.get("lines"):
            continue
        tr = e["trade"]
        floor, label = e["key"].split(":", 1) if ":" in e["key"] else ("", e["key"])
        g = sorted(gt.get(tr, ()))
        trade, code, unit = g[0] if len(g) == 1 else (tr, "", "")
        if (trade, code, unit, floor, label) in carried:
            continue                                      # a line carries it unlinked: the completeness blocker says so
        why = f"T-236 {e['status']} ({tr}): inventory element with no BOQ line"
        if e.get("reason"):
            why += f"; {e['reason']}"
        src = "; ".join(e.get("sources") or []) + (f" [{'; '.join(e['refs'])}]" if e.get("refs") else "")
        rows.append(_row(trade, code, unit, floor, label, why, src))
        inv[(trade, code, unit)].add(label)
        added[tr] += 1
    for t in report.get("trades") or []:
        tr = t["trade"]
        if t.get("principal") and t.get("status") == "NOT_MEASURED" and not t.get("found") and not added[tr] \
                and not gt.get(tr):
            rows.append(_row(tr, "", "", "", "", f"principal trade {tr} with no line and no independent inventory "
                             "(T-236 NOT_MEASURED): scope not established", ""))
    return rows, inv


def completeness_from_report(report, lines, groups_lines, group_elements, ident):
    """{group: URBAN_LINE_COMPLETENESS_V1 record derived from the T-236 report, with its blockers}."""
    pid, rev, _c, _b = ident
    trades = {t["trade"]: t for t in report.get("trades") or []}
    in_report = _report_line_ids(report)
    lt = defaultdict(set)                                 # principal trade -> line ids
    gt = defaultdict(set)                                 # principal trade -> groups
    for g, ls in groups_lines.items():
        for ln in ls:
            lt[TC.line_trade(ln)].add(ln["line_id"])
            gt[TC.line_trade(ln)].add(g)
    els_by_trade = defaultdict(list)
    for e in report.get("elements") or []:
        els_by_trade[e["trade"]].append(e)
    refused = defaultdict(set)
    for d in report.get("deductions") or []:
        if d.get("status") == "REFUSED":
            refused[d.get("line_id")].add(";".join(d.get("problems") or []))
    out = {}
    for g, ls in groups_lines.items():
        if not ls:
            continue
        trs = sorted({TC.line_trade(ln) for ln in ls})
        blockers = []
        sc, na_ev, na_bad, na_lines = scope_split(ls, group_elements.get(g, ()))
        rec = {"schema": COMPLETENESS_SCHEMA, "source": TC.SCHEMA, "project_id": pid, "revision_set_sha256": rev,
               "trade": g[0], "item_code": g[1], "unit": g[2], "principal_trade": ";".join(trs),
               "element_scope_count": len(sc), "inventory_count": None,
               "missing": None, "duplicated": None, "held": None}
        if na_ev:
            rec["not_applicable_out_of_scope"] = len(na_ev)    # T-298: listed, never silently dropped
        if na_bad:
            blockers.append(f"NOT_APPLICABLE WITHOUT EVIDENCE {len(na_bad)}")
        if len(trs) != 1:
            blockers.append(f"LINE MAPS TO {len(trs)} PRINCIPAL TRADES {trs}")
        else:
            tr = trs[0]
            row = trades.get(tr)
            if row is None:
                blockers.append(f"TRADE {tr} NOT IN THE REPORT")
            else:
                if len(gt[tr]) > 1:
                    blockers.append(f"TRADE {tr} SPANS {len(gt[tr])} BOQ LINES: its completeness is not this line's")
                gone = sorted(lt[tr] - in_report - na_lines)
                if gone:
                    blockers.append(f"LINES NOT IN THE REPORT {len(gone)}")
                unl = [x for x in (report.get("unlinked_lines") or {}).get(tr) or [] if x not in na_lines]
                if unl:
                    blockers.append(f"UNLINKED LINES {len(unl)}")
                for k in REPORT_BLOCKERS:
                    if row.get(k):
                        blockers.append(f"{k.upper()} {row[k]}")
                if row.get("status") != "COMPLETE_AGAINST_INVENTORY":
                    blockers.append(f"STATUS {row.get('status')}")
                bad = sorted(lid for lid in lt[tr] if lid in refused)
                if bad:
                    blockers.append(f"DEDUCTION REFUSED {len(bad)}")
                n_inv = sum(1 for e in els_by_trade[tr] if e.get("sources")      # found + excluded with sources,
                            and not (e.get("status") == "EXCLUDED" and e.get("lines")  # less an inventory element
                                     and set(e["lines"]) <= na_lines))             # only NA-with-evidence lines carry
                rec.update(inventory_count=n_inv, missing=row.get("missing"), duplicated=row.get("duplicated"),
                           held=row.get("held"))
                if n_inv != rec["element_scope_count"]:
                    blockers.append(f"INVENTORY {n_inv} != ELEMENT SCOPE {rec['element_scope_count']}")
        rec["blockers"] = blockers
        out[g] = rec
    return out


def completeness_text(rec, ok):
    if rec is None:
        return ""
    if ok:
        return (f"PASS ({rec.get('principal_trade') or rec.get('trade')}: inventory {rec['inventory_count']} = element "
                f"scope {rec['element_scope_count']}, missing 0, duplicated 0, held 0)")
    why = list(rec.get("blockers") or [])
    if not why:
        why = [f"inventory {rec.get('inventory_count')} / scope {rec.get('element_scope_count')}, missing "
               f"{rec.get('missing')}, duplicated {rec.get('duplicated')}, held {rec.get('held')}"]
    return "FAIL: " + "; ".join(why)


# ---- rows -----------------------------------------------------------------------------------------------------------

def _base_row(ln, pid, rev, cver):
    n, dtot = _deductions(ln)
    return {"line_id": ln["line_id"], "trade": ln["trade"], "item_code": ln["item_code"], "item_en": ln["item_en"],
            "item_ar": ln["item_ar"], "floor": ln["location"].get("floor"),
            "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "gross": _num(ln.get("gross")),
            "deductions_n": n, "deductions_total": _num(dtot), "net": None, "quantity_state": None,
            "qty_verified": None, "qty_verified_zero": None, "qty_verified_component": None,
            "qty_measured_unverified": None, "open_range_low": None, "open_range_high": None, "held_reason": "", "held_low": None, "held_high": None,
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
        br = ln.get("bounded_range") or {}
        if br.get("low") is not None and br.get("high") is not None and float(br["high"]) - float(br["low"]) > 1e-9:
            row["open_range_low"], row["open_range_high"] = _num(br["low"]), _num(br["high"])   # never dropped
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
          v2_records=(), completeness=None, completeness_report=None, expect_project=None, expect_revision_set=None,
          downgrades=None):
    """-> {"rows": [...canonical order], "summary": [...], "trades": [...], "identity": {...}, "counts": {...},
    "v2_verdicts": [{verdict_id, status}]}. completeness: {group: URBAN_LINE_COMPLETENESS_V1 record};
    completeness_report: the T-236 report (part (4)), from which those records and the UNMEASURED rows are derived."""
    if not candidate_version:
        raise ExportError("the candidate version is stated, never read from a file name")
    if inventory_doc is not None and completeness_report is not None:
        raise ExportError("--inventory (V1) and --completeness (T-236): one inventory per export, not two (refused)")
    if completeness is not None and completeness_report is not None:
        raise ExportError("completeness records and a completeness report together: one source (refused)")
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

    # part (4): the T-236 report: refused when about other lines; its unmeasured elements become rows
    if completeness_report is not None:
        report_check(completeness_report, lines)
        extra, inv_from_report = report_unmeasured_rows(completeness_report, lines, pid, rev, candidate_version)
        rows.extend(extra)
        for g, els in inv_from_report.items():
            inv_elements[g] |= els

    # groups (the owner's BOQ line = trade + item + unit)
    groups = defaultdict(list)
    for r in rows:
        groups[group_key(r)].append(r)
    glines = {g: [by_line[r["line_id"]][1] for r in rs if r["line_id"]] for g, rs in groups.items()}
    g_elements = {g: sorted({str(ln["location"]["element_id"]) for ln in glines[g]} | inv_elements.get(g, set()))
                  for g in groups}
    g_scope = {g: scope_split(glines[g], g_elements[g])[0] for g in groups}   # T-298: completeness scope
    if completeness_report is not None:
        completeness = completeness_from_report(completeness_report, lines, glines, g_elements, ident)

    # V1 references (shown only)
    v1 = v1_verdict_refs(v1_doc, key_map_doc)
    for r in rows:
        refs = v1.get(r["item_code"])
        if refs:
            r["verdict_id"] = " | ".join(refs)
            r["verdict_status"] = "V1_NOT_BINDING"

    # V2 bound verdicts
    whole_ok = {}
    v2_status = []
    for v in sorted(v2_records or (), key=lambda x: str(x.get("verdict_id"))):
        ids = set(v.get("line_ids") or ()) if isinstance(v.get("line_ids"), list) else set()
        hit = [g for g, ls in glines.items() if ids & {ln["line_id"] for ln in ls}]
        if len(hit) != 1:                             # a record on no line or across groups binds nothing: listed
            why = "NO_LINE_IN_THIS_EXPORT" if not hit else f"ACROSS_{len(hit)}_BOQ_LINES"
            if validate_v2(v):
                why = "BINDING_INCOMPLETE; " + why
            v2_status.append({"verdict_id": str(v.get("verdict_id")), "status": why})
            continue
        g = hit[0]
        g_el = g_elements[g]
        st = bind_verdict(v, ident, glines[g], g_el)
        v2_status.append({"verdict_id": str(v.get("verdict_id")), "status": f"{st} ({v.get('scope')})",
                          "item_code": g[1], "unit": g[2]})
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
        if not completeness_passes((completeness or {}).get(g), ident, g, g_scope[g]):
            for r in groups[g]:
                if r["line_id"] in set(v["line_ids"]):
                    r["verdict_status"] = "COUNTED (WHOLE; completeness record missing or failing: not VERIFIED)"
            for s in v2_status:
                if s["verdict_id"] == str(v.get("verdict_id")):
                    s["status"] = "COUNTED (WHOLE; completeness record missing or failing: not VERIFIED)"
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

    dg_status, audit = apply_downgrades(downgrades, by_line, pid, rev) if downgrades is not None else ([], [])
    rows.sort(key=sort_key)
    if len(rows) != len(lines) + sum(1 for r in rows if r["quantity_state"] == UNMEASURED):
        raise ExportError("row count differs from lines + unmeasured elements: a row was dropped (refused)")
    comp_text = {}
    for g in groups:
        rec = (completeness or {}).get(g)
        comp_text[g] = completeness_text(rec, completeness_passes(rec, ident, g, g_scope[g]))
    summary, trades = _summary(rows, groups, whole_ok, completeness, ident, inv_elements, glines, comp_text)
    counts = {s: sum(1 for r in rows if r["quantity_state"] == s) for s in QSTATES}
    return {"schema": SCHEMA, "rows": rows, "summary": summary, "trades": trades, "counts": counts,
            "identity": {"project_id": pid, "revision_set_sha256": rev, "candidate_version": candidate_version,
                         "boq_lines_sha256": boq_lines_sha256},
            "v2_verdicts": v2_status, "downgrades": dg_status if downgrades is not None else None,
            "audit_rows": sorted(audit, key=lambda r: (str(r["item_code"]), str(r["floor"]), str(r["element_id"]),
                                                      str(r["line_id"]))),
            "completeness_input": ("T-236 report (URBAN_TRADE_COMPLETENESS_V1)" if completeness_report is not None
                                   else "records given" if completeness
                                   else "none given: no line can read VERIFIED")}


def _summary(rows, groups, whole_ok, completeness, ident, inv_elements, glines, comp_text=None):
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
            "measured_unverified_rows": len(mu),
            "open_range_rows": sum(1 for r in rs if r.get("open_range_low") is not None),
            "open_range_components": "; ".join(
                f"{r['element_id']} [{_fx(r['open_range_low'])} .. {_fx(r['open_range_high'])}, net {_fx(r['net'])}]"
                for r in rs if r.get("open_range_low") is not None),
            "held_rows": len(held),
            "held_low": _num(sum(r["held_low"] for r in bounded)) if bounded else None,
            "held_high": _num(sum(r["held_high"] for r in bounded)) if bounded else None,
            "unmeasured_rows": len(unm), "excluded_rows": len(exc),
            "rows_without_quantity": len(held) + len(unm) + len(exc),
            "held_components": "; ".join(f"{r['element_id']}" + (f" [{_fx(r['held_low'])} .. {_fx(r['held_high'])}]"
                                                                   if r["held_low"] is not None else " [no range]")
                                         for r in held),
            "unmeasured_components": "; ".join(str(r["element_id"]) for r in unm),
            "trade_status": "", "trade_verified_whole_lines": "", "completeness": (comp_text or {}).get(g, "")})
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


# ---- contract units (T-273) -----------------------------------------------------------------------------------------

def contract_view(rows):
    """the canonical rows in contract units: every kg row becomes t (quantity columns / 1000, ONCE, full precision
    kept until the writer's 6 decimals); every other row keeps its unit. -> (contract rows, contract totals). Refused:
    a BOQ line (trade, item) carrying kg and t rows together (mixed units), a row already in a contract unit with an
    engine-unit label (relabelled), a quantity column that is not a number."""
    by_item = defaultdict(set)
    for r in rows:
        if "engine_unit" in r or "conversion" in r:      # T-298: a row of a contract view converted again
            raise ExportError(f"{r.get('line_id') or r.get('element_id')}: row already in contract units "
                              "(double conversion, refused)")
        by_item[(str(r["trade"] or ""), str(r["item_code"] or ""))].add(r["unit"])
    for k, us in sorted(by_item.items()):
        for eu, (cu, _f) in CONTRACT_UNIT.items():
            if eu in us and cu in us:
                raise ExportError(f"{k[1] or k[0]}: rows in {eu} and {cu} in one BOQ line (mixed units, refused)")
    for r in rows:
        reg = BL.ITEMS.get(r["item_code"] or "")
        if reg and reg[3] in CONTRACT_UNIT and r["unit"] == CONTRACT_UNIT[reg[3]][0]:
            # T-298: the item is registered in kg; a t row is pre-converted or relabelled kg (refused: once, here)
            raise ExportError(f"{r.get('line_id') or r.get('element_id')}: {r['item_code']} is registered in {reg[3]} "
                              f"but the row is in {r['unit']} (pre-converted or relabelled, refused)")
    out = []
    for r in rows:
        c = dict(r)
        eu = r["unit"]
        if eu in CONTRACT_UNIT:
            cu, f = CONTRACT_UNIT[eu]
            for col in CONTRACT_QTY_COLUMNS:
                v = r.get(col)
                if v is None:
                    continue
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise ExportError(f"{r['line_id']}: {col} {v!r} is not a number (refused)")
                c[col] = v / f
            c["unit"], c["engine_unit"], c["conversion"] = cu, eu, f"{eu} / {f:g} (once, at export)"
        else:
            c["engine_unit"], c["conversion"] = eu, "none"
        out.append(c)
    totals = []
    groups = defaultdict(list)
    for r, c in zip(rows, out):
        groups[group_key(r)].append((r, c))
    for g in sorted(groups):
        pairs = groups[g]
        eu = g[2]
        f = CONTRACT_UNIT.get(eu, (eu, 1.0))[1]

        def ssum(col, states):
            vals = [r[col] for r, _c in pairs if r["quantity_state"] in states and r.get(col) is not None]
            return (sum(vals), len(vals)) if vals else (None, 0)
        mu, _n = ssum("qty_measured_unverified", (MEASURED_UNVERIFIED,))
        vq = [sum(x for x in (r.get("qty_verified"), r.get("qty_verified_zero"), r.get("qty_verified_component"))
                  if x is not None) for r, _c in pairs if r["quantity_state"] in (VERIFIED, VERIFIED_ZERO,
                                                                                  VERIFIED_COMPONENT)]
        vs = sum(vq) if vq else None
        hl, _a = ssum("held_low", (HELD,))
        hh, _b = ssum("held_high", (HELD,))
        st = [x for x in set(c["quantity_state"] for _r, c in pairs)]
        totals.append({"trade": g[0], "item_code": g[1], "unit": CONTRACT_UNIT.get(eu, (eu, 1.0))[0],
                       "engine_unit": eu, "line_status": "; ".join(sorted(st)), "rows": len(pairs),
                       "measured_unverified_engine_sum": mu, "measured_unverified_sum": None if mu is None else mu / f,
                       "verified_engine_sum": vs, "verified_sum": None if vs is None else vs / f,
                       "held_low": None if hl is None else hl / f, "held_high": None if hh is None else hh / f,
                       "rows_without_quantity": sum(1 for r, _c in pairs
                                                    if r["quantity_state"] in (HELD, UNMEASURED, EXCLUDED))})
    return out, totals


def contractual_rows(rows):
    """T-298: the contractual BOQ rows (the default export): contract_view() rows (kg -> t once) plus the audit columns
    engine_<quantity column>, the same row's value in the engine unit (kg kept beside t; the unit verdicts bind to).
    -> (rows, contract totals)."""
    crow, ctot = contract_view(rows)
    out = []
    for r, c in zip(rows, crow):
        out.append(c | {f"engine_{col}": r.get(col) for col in CONTRACT_QTY_COLUMNS})
    return out, ctot


def contract_summary(summary, crow):
    """T-298: the trade summary in contract units: a kg group's sums are its unrounded kg sums / 1000 (once), its
    component texts are re-read from the contract rows; every other group is unchanged. Adds engine_unit."""
    by_g = defaultdict(list)
    for c in crow:
        by_g[(str(c["trade"] or ""), str(c["item_code"] or ""), str(c["engine_unit"] or ""))].append(c)
    out = []
    for s in summary:
        s2 = dict(s, engine_unit=s["unit"])
        if s["unit"] in CONTRACT_UNIT:
            cu, f = CONTRACT_UNIT[s["unit"]]
            for col in ("verified_subtotal", "measured_unverified_sum", "held_low", "held_high"):
                if s.get(col) is not None:
                    s2[col] = s[col] / f
            rs = sorted(by_g[(str(s["trade"]), str(s["item_code"]), str(s["unit"]))], key=sort_key)
            s2["open_range_components"] = "; ".join(
                f"{r['element_id']} [{_fx(r['open_range_low'])} .. {_fx(r['open_range_high'])}, net {_fx(r['net'])}]"
                for r in rs if r.get("open_range_low") is not None)
            s2["held_components"] = "; ".join(
                f"{r['element_id']}" + (f" [{_fx(r['held_low'])} .. {_fx(r['held_high'])}]"
                                        if r["held_low"] is not None else " [no range]")
                for r in rs if r["quantity_state"] == HELD)
            s2["unit"] = cu
        out.append(s2)
    return out


# ---- writers --------------------------------------------------------------------------------------------------------

def _cell_text(c, v):
    if v is None:
        return ""
    if isinstance(v, float) or (isinstance(v, int) and c not in ("deductions_n",) and not isinstance(v, bool)):
        return _fx(v) if c not in ("rows", "verified_rows", "measured_unverified_rows", "held_rows", "open_range_rows",
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


def xlsx_write(path, rows, summary, manifest_rows, extra_sheets=(), boq_columns=COLUMNS,
               summary_columns=SUMMARY_COLUMNS):
    from openpyxl import Workbook

    from engine.reporting_v3 import book as BK
    wb = Workbook()
    wb.properties.creator = "Urban Projects"
    wb.properties.created = wb.properties.modified = BK.CREATED
    for title, cols, data in (("BOQ", boq_columns, rows), ("Trade summary", summary_columns, summary),
                              *tuple(extra_sheets), ("Manifest", ("key", "value"), manifest_rows)):
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


def project_identity(doc, ident):
    """T-245: check a URBAN_BOQ_PROJECT_IDENTITY_V1 record against the exported lines' identity; -> the rows the
    manifest and the XLSX Manifest sheet state (revision set, each drawing's revision state, the disclosures)."""
    if doc.get("schema") != IDENTITY_SCHEMA:
        raise ExportError(f"--identity schema {doc.get('schema')!r} is not {IDENTITY_SCHEMA}")
    if doc.get("project_id") != ident["project_id"]:
        raise ExportError(f"--identity project {doc.get('project_id')!r} is not the lines' {ident['project_id']!r}")
    docs = doc.get("documents") or []
    shas = [d.get("sha256") for d in docs]
    if not docs or len(set(shas)) != len(shas) or any(not isinstance(x, str) or len(x) != 64 for x in shas):
        raise ExportError("--identity: documents missing, repeated or without a sha256")
    sheets = [(d.get("discipline"), d.get("sheet")) for d in docs]
    if len(set(sheets)) != len(sheets):
        raise ExportError("--identity: two revisions of one sheet (refused)")
    rev = hashlib.sha256("|".join(sorted(shas)).encode("utf-8")).hexdigest()
    if rev != doc.get("revision_set_sha256") or rev != ident["revision_set_sha256"]:
        raise ExportError("--identity: its documents do not give the lines' revision set sha256 (refused)")
    rows = [("identity_schema", IDENTITY_SCHEMA), ("review_label", REVIEW_LABEL)]
    for d in sorted(docs, key=lambda d: (str(d.get("discipline")), str(d.get("sheet")))):
        st = d.get("revision_state")
        rows.append((f"document {d.get('discipline')} {d.get('sheet')}",
                     f"{d.get('title')} | revision {d.get('revision')} ({st}"
                     + (f": {d.get('reason')}" if st == "UNCONFIRMED" else "") + f") | sha256 {d.get('sha256')}"))
    for i, t in enumerate(doc.get("disclosures") or []):
        rows.append((f"disclosure {i + 1}", t))
    rows.append(("provenance", "a file sha256 proves the file used, not that it is the latest approved revision"))
    return rows


def export(lines, out_dir, *, candidate_version, boq_lines_sha256, input_sha256=None, code_commit="NOT_RECORDED",
           contract_units=False, identity_doc=None, contractual=False, **kw):
    """build + write BOQ.csv, BOQ.xlsx, EXPORT_MANIFEST.json into out_dir; -> the manifest. contract_units (T-273,
    opt-in): also BOQ_CONTRACT_UNITS.csv + BOQ_CONTRACT_TOTALS.csv and two XLSX sheets, manifest schema V2.
    contractual (T-298; the command line's default): BOQ.csv / BOQ_TRADE_SUMMARY.csv / sheets BOQ and Trade summary
    in contract units (reinforcement t, engine_<column> audit columns in kg), BOQ_ENGINE_UNITS.csv +
    BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv (the engine-unit rows, byte for byte the V1 files) and BOQ_CONTRACT_TOTALS.csv,
    manifest schema V3; it excludes contract_units (one contract view per export)."""
    if contractual and contract_units:
        raise ExportError("the contractual export already is the contract-unit view; --contract-units is the V1 "
                          "opt-in (with --engine-units) (refused)")
    res = build(lines, candidate_version=candidate_version, boq_lines_sha256=boq_lines_sha256, **kw)
    crow, ctot = contract_view(res["rows"]) if contract_units else (None, None)
    if contractual:                                   # refused before anything is written
        krow, ctot = contractual_rows(res["rows"])
        ksum = contract_summary(res["summary"], krow)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cb = csv_bytes(res["rows"])
    sb = csv_bytes(res["summary"], SUMMARY_COLUMNS)
    if contractual:
        (out / "BOQ_ENGINE_UNITS.csv").write_bytes(cb)
        (out / "BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv").write_bytes(sb)
        (out / "BOQ_CONTRACT_TOTALS.csv").write_bytes(csv_bytes(ctot, CONTRACT_TOTAL_COLUMNS))
        (out / "BOQ.csv").write_bytes(csv_bytes(krow, CONTRACTUAL_COLUMNS))
        (out / "BOQ_TRADE_SUMMARY.csv").write_bytes(csv_bytes(ksum, CONTRACTUAL_SUMMARY_COLUMNS))
    else:
        (out / "BOQ.csv").write_bytes(cb)
        (out / "BOQ_TRADE_SUMMARY.csv").write_bytes(sb)
    ident = res["identity"]
    mrows = [{"key": k, "value": str(v)} for k, v in (
        ("schema", SCHEMA), ("candidate_version", ident["candidate_version"]), ("project_id", ident["project_id"]),
        ("revision_set_sha256", ident["revision_set_sha256"]), ("boq_lines_sha256", ident["boq_lines_sha256"]),
        ("code_commit", code_commit), ("rows", len(res["rows"])),
        ("completeness_input", res["completeness_input"]),
        ("verified_rule", "VERIFIED only from a bound V2 verdict + passing completeness record; V1 never"))]
    id_rows = project_identity(identity_doc, ident) if identity_doc is not None else None
    for k, v in id_rows or ():
        mrows.append({"key": k, "value": str(v)})
    for k in sorted(res["counts"]):
        mrows.append({"key": f"rows {k}", "value": str(res["counts"][k])})
    for s in res["v2_verdicts"]:
        mrows.append({"key": f"verdict {s['verdict_id']}", "value": s["status"]})
    extra, outs = (), ["BOQ.csv", "BOQ.xlsx", "BOQ_TRADE_SUMMARY.csv"]
    if res["downgrades"] is not None:
        (out / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv").write_bytes(csv_bytes(res["audit_rows"], AUDIT_COLUMNS))
        for s in res["downgrades"]:
            mrows.append({"key": f"downgrade {s['downgrade_id']}", "value": s["status"]})
        extra = extra + (("Audit (unsupported basis)", AUDIT_COLUMNS, res["audit_rows"]),)
        outs += ["BOQ_AUDIT_UNSUPPORTED_BASIS.csv"]
    if contract_units:
        (out / "BOQ_CONTRACT_UNITS.csv").write_bytes(csv_bytes(crow, CONTRACT_COLUMNS))
        (out / "BOQ_CONTRACT_TOTALS.csv").write_bytes(csv_bytes(ctot, CONTRACT_TOTAL_COLUMNS))
        mrows.append({"key": "contract_units", "value": f"{CONTRACT_SCHEMA}: kg -> t = kg / 1000 once at export; "
                                                         "BOQ sheet / BOQ.csv stay in engine units (verdict binding)"})
        extra = extra + (("BOQ (contract units)", CONTRACT_COLUMNS, crow),
                         ("Contract totals", CONTRACT_TOTAL_COLUMNS, ctot))
        outs += ["BOQ_CONTRACT_UNITS.csv", "BOQ_CONTRACT_TOTALS.csv"]
    if contractual:
        mrows.append({"key": "contractual_units", "value": f"{CONTRACTUAL_SCHEMA}: BOQ / Trade summary in contract "
                                                           "units (kg -> t = kg / 1000 once at export); engine-unit "
                                                           "values in the engine_* columns and the sheet 'BOQ (engine "
                                                           "units)' (verdict binding)"})
        extra = extra + (("Contract totals", CONTRACT_TOTAL_COLUMNS, ctot),
                         ("BOQ (engine units)", COLUMNS, res["rows"]),
                         ("Trade summary (engine units)", SUMMARY_COLUMNS, res["summary"]))
        outs += ["BOQ_ENGINE_UNITS.csv", "BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv", "BOQ_CONTRACT_TOTALS.csv"]
        xlsx_write(out / "BOQ.xlsx", krow, ksum, mrows, extra, CONTRACTUAL_COLUMNS, CONTRACTUAL_SUMMARY_COLUMNS)
    else:
        xlsx_write(out / "BOQ.xlsx", res["rows"], res["summary"], mrows, extra)
    schema = MANIFEST_SCHEMA_CONTRACTUAL if contractual else MANIFEST_SCHEMA_CONTRACT if contract_units \
        else MANIFEST_SCHEMA
    manifest = {"schema": schema, "export_schema": CONTRACTUAL_SCHEMA if contractual else SCHEMA,
                "identity": ident, "code_commit": code_commit,
                "inputs_sha256": dict(sorted((input_sha256 or {}).items())),
                "outputs": {f: sha256_bytes((out / f).read_bytes()) for f in sorted(outs)},
                "row_counts": res["counts"] | {"total": len(res["rows"])},
                "trades": res["trades"], "completeness_input": res["completeness_input"],
                "v2_verdicts": res["v2_verdicts"],
                "semantic_sha256": semantic_sha256(res["rows"])}
    if res["downgrades"] is not None:
        manifest["downgrades"] = {"schema": DOWNGRADE_SCHEMA, "records": res["downgrades"],
                                  "rule": "downgrade only: a valid unresolved record moves its lines to HELD / "
                                          "CONFLICT (a VERIFIED verdict included); never promotes; the candidate "
                                          "quantity is shown only in BOQ_AUDIT_UNSUPPORTED_BASIS.csv"}
    if identity_doc is not None:
        manifest["project_identity"] = {"review_label": REVIEW_LABEL,
                                        "documents": sorted(identity_doc.get("documents") or [],
                                                            key=lambda d: (str(d.get("discipline")),
                                                                           str(d.get("sheet")))),
                                        "disclosures": list(identity_doc.get("disclosures") or []),
                                        "routes": identity_doc.get("routes") or [],
                                        "boq_lines_binding": "sha256 of the canonical line content "
                                                             "(engine/source/boq_line.dumps), not the raw file bytes"}
    if contract_units:
        manifest["contract_units"] = {"schema": CONTRACT_SCHEMA, "conversion": {k: f"{k} / {v[1]:g} -> {v[0]}"
                                                                                  for k, v in CONTRACT_UNIT.items()},
                                      "decimals": DEC, "totals": "from unrounded engine-unit sums, converted once",
                                      "verdict_binding": "engine unit (BOQ.csv); unchanged"}
    if contractual:
        manifest["contractual_units"] = {
            "schema": CONTRACTUAL_SCHEMA, "conversion": {k: f"{k} / {v[1]:g} -> {v[0]}" for k, v in CONTRACT_UNIT.items()},
            "decimals": DEC, "totals": "from unrounded engine-unit sums, converted once",
            "audit_columns": list(ENGINE_AUDIT_COLUMNS),
            "engine_unit_files": ["BOQ_ENGINE_UNITS.csv", "BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv"],
            "verdict_binding": "the canonical line content in the engine unit (boq_lines_sha256); semantic_sha256 is "
                               "of the engine-unit rows; a unit change never invalidates a verdict",
            "semantic_sha256_contract": sha256_bytes(json.dumps(
                [[r.get(c) if not isinstance(r.get(c), float) else _fx(r.get(c)) for c in CONTRACTUAL_COLUMNS]
                 for r in krow], ensure_ascii=False).encode("utf-8")),
            "rows_converted": sum(1 for r in krow if r["unit"] != r["engine_unit"])}
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


def _parse_evidence(items):
    out = []
    for it in items or []:
        if "=" not in it:
            raise ExportError(f"--evidence {it!r}: write SHEET=PRINTED VALUE")
        sheet, val = it.split("=", 1)
        out.append({"sheet": sheet.strip(), "printed_value": val.strip()})
    return out


def main_verdict_add(argv):
    ap = argparse.ArgumentParser(prog="boq_export_v1.py verdict-add",
                                 description="add one URBAN_CHECKER_VERDICT_V2 record, binding filled from the lines")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--candidate-version", required=True)
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--line-ids", help="comma-separated line ids")
    sel.add_argument("--item-code", help="every line of this item code (one unit; see --unit)")
    ap.add_argument("--unit")
    ap.add_argument("--scope", required=True, choices=V2_SCOPES)
    ap.add_argument("--checker-qty", required=True, type=float)
    ap.add_argument("--evidence", action="append", required=True, help="SHEET=PRINTED VALUE (repeat)")
    ap.add_argument("--lock-file", help="the Checker's run lock (docs/agents/locks/checker.lock): token + routine")
    ap.add_argument("--run-token")
    ap.add_argument("--routine")
    ap.add_argument("--verdict-commit", required=True)
    ap.add_argument("--time", help="ISO 8601 UTC (default: now)")
    ap.add_argument("--verdict-id")
    ap.add_argument("--notes")
    ap.add_argument("--out", required=True, help="the URBAN_CHECKER_VERDICT_V2_SET file to append to")
    a = ap.parse_args(argv)
    lines, _raw = _load_json(a.lines)
    if isinstance(lines, dict):
        raise ExportError("--lines must be a list of canonical lines (V3_0_x_BOQ_LINES.json)")
    lsha = lines_sha256(lines)          # T-245: the canonical line content, never the raw file bytes
    if a.line_ids:
        ids = [x.strip() for x in a.line_ids.split(",") if x.strip()]
    else:
        ids = [ln["line_id"] for ln in lines if ln["item_code"] == a.item_code and (a.unit is None or ln["unit"] == a.unit)]
    token, routine = a.run_token, a.routine
    if a.lock_file:
        lk, _s = _load_json(a.lock_file)
        token, routine = token or lk.get("token"), routine or lk.get("agent")
    rec = verdict_add(lines, candidate_version=a.candidate_version, boq_lines_sha256=lsha, line_ids=ids, scope=a.scope,
                      checker_qty=a.checker_qty, evidence=_parse_evidence(a.evidence), run_token=token or "",
                      routine=routine or "", verdict_commit=a.verdict_commit,
                      time=a.time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      verdict_id=a.verdict_id, notes=a.notes)
    verdict_set_append(a.out, rec)
    print(json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


def main_downgrade_add(argv):
    ap = argparse.ArgumentParser(prog="boq_export_v1.py downgrade-add",
                                 description="add one URBAN_CHECKER_DOWNGRADE_V1 record (Checker only; downgrade only)")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--line-ids", required=True, help="comma-separated line ids")
    ap.add_argument("--state", required=True, choices=DOWNGRADE_STATES)
    ap.add_argument("--basis-label", default="UNSUPPORTED BASIS")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--evidence", action="append", required=True, help="SHEET=PRINTED VALUE (repeat)")
    ap.add_argument("--lock-file")
    ap.add_argument("--run-token")
    ap.add_argument("--routine")
    ap.add_argument("--verdict-commit", required=True)
    ap.add_argument("--time")
    ap.add_argument("--downgrade-id")
    ap.add_argument("--out", required=True, help="the URBAN_CHECKER_DOWNGRADE_V1_SET file to append to")
    a = ap.parse_args(argv)
    lines, _raw = _load_json(a.lines)
    if isinstance(lines, dict):
        raise ExportError("--lines must be a list of canonical lines (V3_0_x_BOQ_LINES.json)")
    token, routine = a.run_token, a.routine
    if a.lock_file:
        lk, _s = _load_json(a.lock_file)
        token, routine = token or lk.get("token"), routine or lk.get("agent")
    rec = downgrade_add(lines, candidate_version=a.candidate_version,
                        line_ids=[x.strip() for x in a.line_ids.split(",") if x.strip()], state=a.state,
                        basis_label=a.basis_label, reason=a.reason, evidence=_parse_evidence(a.evidence),
                        run_token=token or "", routine=routine or "", verdict_commit=a.verdict_commit,
                        time=a.time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        downgrade_id=a.downgrade_id)
    p = Path(a.out)
    doc = _load_json(p)[0] if p.exists() else {"schema": DOWNGRADE_SET_SCHEMA, "downgrades": []}
    if doc.get("schema") != DOWNGRADE_SET_SCHEMA:
        raise ExportError(f"{p.name}: schema is not {DOWNGRADE_SET_SCHEMA}")
    if any(x.get("downgrade_id") == rec["downgrade_id"] for x in doc["downgrades"]):
        raise ExportError(f"downgrade id {rec['downgrade_id']} is already in {p.name}")
    doc["downgrades"] = sorted(doc["downgrades"] + [rec], key=lambda x: str(x.get("downgrade_id")))
    p.write_text(_dump_set(doc), encoding="utf-8")
    print(json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


def main_verdict_rebind(argv):
    ap = argparse.ArgumentParser(prog="boq_export_v1.py verdict-rebind",
                                 description="T-294: re-issue unchanged V2 records on a new candidate (Checker only)")
    ap.add_argument("--verdicts", required=True, help="the old URBAN_CHECKER_VERDICT_V2_SET file")
    ap.add_argument("--old-lines", required=True, help="the candidate lines the old records were issued on")
    ap.add_argument("--old-candidate-version", required=True)
    ap.add_argument("--lines", required=True, help="the new candidate lines")
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--lock-file")
    ap.add_argument("--run-token")
    ap.add_argument("--routine")
    ap.add_argument("--verdict-commit", required=True)
    ap.add_argument("--time")
    ap.add_argument("--out", required=True, help="the new URBAN_CHECKER_VERDICT_V2_SET file to append to")
    a = ap.parse_args(argv)
    if Path(a.out).resolve() == Path(a.verdicts).resolve():
        raise ExportError("--out is the old set: a re-bound record goes into the new candidate's set (refused)")
    old, _s = _load_json(a.verdicts)
    sp = _set_problems(old)
    if sp:
        raise ExportError("--verdicts: " + "; ".join(sp))
    ol, _r1 = _load_json(a.old_lines)
    nl, _r2 = _load_json(a.lines)
    if isinstance(ol, dict) or isinstance(nl, dict):
        raise ExportError("--old-lines / --lines must be lists of canonical lines (V3_0_x_BOQ_LINES.json)")
    token, routine = a.run_token, a.routine
    if a.lock_file:
        lk, _s = _load_json(a.lock_file)
        token, routine = token or lk.get("token"), routine or lk.get("agent")
    when = a.time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = []
    for v in sorted(old["verdicts"], key=lambda x: str(x.get("verdict_id"))):
        try:
            rec = verdict_rebind(v, ol, nl, old_candidate_version=a.old_candidate_version,
                                 candidate_version=a.candidate_version, run_token=token or "", routine=routine or "",
                                 verdict_commit=a.verdict_commit, time=when)
        except ExportError as e:
            report.append({"verdict_id": str(v.get("verdict_id")), "status": f"NOT RE-BOUND: {e}"})
            continue
        verdict_set_append(a.out, rec)
        report.append({"verdict_id": str(v.get("verdict_id")), "status": f"RE-BOUND as {rec['verdict_id']}"})
    print(json.dumps(report, indent=1, sort_keys=True, ensure_ascii=False))
    return 0 if all(r["status"].startswith("RE-BOUND") for r in report) else 1


def main_verdict_validate(argv):
    ap = argparse.ArgumentParser(prog="boq_export_v1.py verdict-validate")
    ap.add_argument("file")
    a = ap.parse_args(argv)
    doc, _s = _load_json(a.file)
    probs = validate_v2_set(doc)
    for p in probs:
        print(p)
    print(f"{len(doc.get('verdicts') or []) if isinstance(doc, dict) else 0} record(s), {len(probs)} problem(s)")
    return 1 if probs else 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "verdict-add":
        return main_verdict_add(argv[1:])
    if argv and argv[0] == "verdict-validate":
        return main_verdict_validate(argv[1:])
    if argv and argv[0] == "downgrade-add":
        return main_downgrade_add(argv[1:])
    if argv and argv[0] == "verdict-rebind":
        return main_verdict_rebind(argv[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--lines", required=True)
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verdicts-v1")
    ap.add_argument("--key-map")
    ap.add_argument("--inventory")
    ap.add_argument("--verdicts-v2", help="a URBAN_CHECKER_VERDICT_V2_SET file")
    ap.add_argument("--completeness", help="the T-236 report TRADE_COMPLETENESS.json")
    ap.add_argument("--expect-project")
    ap.add_argument("--expect-revision-set")
    ap.add_argument("--code-commit")
    ap.add_argument("--downgrades", help="a URBAN_CHECKER_DOWNGRADE_V1_SET file (T-245 (f)): Checker-issued records "
                                         "that can only move lines to HELD / CONFLICT")
    ap.add_argument("--identity", help="the candidate's V3_0_16_IDENTITY.json (URBAN_BOQ_PROJECT_IDENTITY_V1, T-245): "
                                       "project id, revision set and each drawing's revision state, stated in the "
                                       "manifest and the XLSX Manifest sheet; it must be the lines' own identity")
    ap.add_argument("--contract-units", action="store_true",
                    help="T-273 layout: the V1 engine-unit files plus a separate contract-unit view "
                         "(BOQ_CONTRACT_UNITS.csv); implies --engine-units for BOQ.csv")
    ap.add_argument("--engine-units", action="store_true",
                    help="opt out of the contractual default (T-298): BOQ.csv / BOQ.xlsx in engine units (kg), "
                         "the V1 bytes")
    a = ap.parse_args(argv)
    contractual = not (a.engine_units or a.contract_units)
    lines, raw = _load_json(a.lines)
    if isinstance(lines, dict):
        raise ExportError("--lines must be a list of canonical lines (V3_0_x_BOQ_LINES.json)")
    lsha = lines_sha256(lines)          # T-245: verdicts bind the canonical line content, never the raw file bytes
    shas = {"lines": raw}
    docs = {}
    for k, p in (("verdicts_v1", a.verdicts_v1), ("key_map", a.key_map), ("inventory", a.inventory),
                 ("verdicts_v2", a.verdicts_v2), ("completeness", a.completeness), ("identity", a.identity),
                 ("downgrades", a.downgrades)):
        if p:
            docs[k], shas[k] = _load_json(p)
    v2 = ()
    if "verdicts_v2" in docs:
        sp = _set_problems(docs["verdicts_v2"])
        if sp:
            raise ExportError("--verdicts-v2: " + "; ".join(sp))
        v2 = docs["verdicts_v2"]["verdicts"]
    dg = None
    if "downgrades" in docs:
        if docs["downgrades"].get("schema") != DOWNGRADE_SET_SCHEMA or not isinstance(
                docs["downgrades"].get("downgrades"), list):
            raise ExportError(f"--downgrades: schema must be {DOWNGRADE_SET_SCHEMA} with a downgrades list")
        dg = docs["downgrades"]["downgrades"]
    m = export(lines, a.out, candidate_version=a.candidate_version, boq_lines_sha256=lsha, input_sha256=shas,
               code_commit=_code_commit(a.code_commit), contract_units=a.contract_units, contractual=contractual,
               identity_doc=docs.get("identity"), downgrades=dg, v1_doc=docs.get("verdicts_v1"),
               key_map_doc=docs.get("key_map"), inventory_doc=docs.get("inventory"), v2_records=v2,
               completeness_report=docs.get("completeness"),
               expect_project=a.expect_project, expect_revision_set=a.expect_revision_set)
    print(json.dumps({"outputs": m["outputs"], "row_counts": m["row_counts"],
                      "trades": [{k: t[k] for k in ("trade", "status", "verified_whole_lines", "lines")}
                                 for t in m["trades"]]}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
