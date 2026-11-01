"""ARCH_TAKEOFF_V3.0.36 (T-246): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.35 (engine.source.arch_v30,
arch_v301 .. arch_v3035), with ONE piece, DEDUCTION_LISTING: a traceability fill. No quantity moves.

A canonical line carries gross, measured_net and a 'deductions' / 'additions' list. On the candidate of record many
valued lines carried a list a consumer cannot reconcile (T-330 check): the deductions only in calculation.inputs
(plaster / paint / wall tile), the floor-level window-threshold halves deducted by the net but never listed (skirting),
a gross written equal to the net beside a list (porcelain), a stale base list under a piece-set net (the 1F porcelain
line, T-345), or one aggregate per kind without an opening id and with a unit-named key the export does not read.
This piece rewrites, line id by line id, ONLY the canonical list (and, where a verified ledger restates it, the gross
field to the face the list starts from), from Checker-merged ledgers pinned by sha256:

  LIST_FILL      the line's list replaced by the fill rows of the merged ledger (T-341 FILL_TABLE: each deducted opening /
                 element by id, face, amount in the line's unit, source; a signed ledger row is an ADDITION, never a
                 negative deduction); the gross field stays.
  GROSS_RESTATE  as LIST_FILL, and the gross field restated to the face area the list starts from (T-341
                 RECONCILED_GROSS_RESTATED, T-345 TRACED): the line's net and state stay.

Every row binds its line as the ledger read it (item, element, state, gross field, net: else stop, stale binding). The
module asserts per line gross - sum(deductions) + sum(additions) = measured_net within the export tolerance 0.0005 (the
owner lists carry 4 decimals), every item with an id, a non-negative 'qty' in the line's unit (the key the export
reads), no id twice in one list, and that no unlisted deduction is accepted (the list must close the gap: a gap no row
names stops). A window-threshold row carries the T-296 physical reading of its window (SKIRTED: the wall base continues
under a sill above the floor, so the deduction is physically wrong -> physical_check UNRESOLVED, never applied here;
NOT_SKIRTED: right; HELD: UNRESOLVED); the quantity is not judged and does not move (T-246: flag, do not apply).

Every line outside the rows is byte-identical to V3.0.35; inside a row only deductions, additions, gross (restate),
calculation (a record) and notes change, measured_net / state / range never (asserted); every code total is unchanged
(asserted). Files: V3_0_36_BOQ_LINES.json / .csv, V3_0_36_INTEGRATION_LEDGER.json / .csv, V3_0_36_DIFF.csv,
V3_0_36_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.

R-T246-1 (every villa): every valued line with a numeric gross exports a canonical list that closes gross to net in its
own unit (gross - deductions + additions = net), each item with the id of what it deducts and one number under a key
the export reads; a piece that re-nets a line writes the list WITH the net (never a new net over a stale base list); a
signed ledger row is an addition, never a negative deduction; a deduction a verified reading shows to be physically
wrong is listed with that flag (UNRESOLVED) and changed only by a quantity package; listing never moves a quantity.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no value
METHOD = "ARCH_TAKEOFF_V3.0.36"
EXTENDS = A3035.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T246_ARCH_V3_0_36"
INPUTS_SCHEMA = "URBAN_V3036_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3036_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T246-1", "T-246"
PIECE = "DEDUCTION_LISTING"
REC_KEY = "deduction_listing_v3036"
ACTIONS = ("LIST_FILL", "GROSS_RESTATE")
ROLES = ("DEDUCTION", "ADDITION")
PHYSICAL = ("CONSISTENT", "UNRESOLVED", "NOT_A_WINDOW")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
TOL = 0.0005                             # tools/boq_export_v1.QTY_MATCH_TOL (the T-330 check's tolerance)
BIND_TOL = 1e-6
ROW_KEYS = ("deductions", "additions", "gross", "calculation", "notes")

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3036.py (canonical deduction lists from the Checker-merged T-341 FILL table and "
                  "the T-345 trace; the porcelain gross fields restated to their faces; window-threshold rows "
                  "carry the T-296 physical reading; no quantity moves)",
        "policy": "DEDUCTION_LISTING_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["UP-SKIRT-001 (doors deducted once by opening; window base by sill)",
                        "UP-CER-003 (door openings deducted)", "Q-55 C (door head 2.20, ASSUMED - OWNER-APPROVED)",
                        "Q-37 A / Q-48 A (wet room: the wall tile owns the base)", "Q-66 B (1F arrival landing)",
                        "UP-STAIR-005 (treads are marble, never also porcelain)",
                        "UP-QTY-STATUS-001", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner method per line: gross face / run less each opening by id (doors at the Q-55 C "
                               "head, windows by printed sill / head; skirting: door widths, the window base only "
                               "where no wall continues under the sill); the list is the owner's own, read here",
        "drawing_method": "engine faces and runs (gross) and the band openings by engine id (T-249 census id beside), "
                          "the stair piece's exact tread / void / residue cells (T-345), all as the Checker-merged "
                          "ledgers recorded them; nothing re-measured"},
}
WAITING = dict(A3035.WAITING)
WAITING.update({
    "T246_SKIRTING_RELEASE": "T-296 readings SKIRTED (W04 / W14 / W24 / W29: sill above the floor, the base continues; "
                             "+5.802 lm of threshold credit) and NOT_SKIRTED (W15 / W16 floor glazing) are listed with "
                             "their physical flag; the quantity change waits a lane I quantity package (not listing)",
    "T246_CEILING_V3032": "6 FIN.CEILING lines restated by V3.0.32 (T-284 ceiling fill) close only through their "
                          "still_held items (dome positions, stair zones): their list needs the T-284 ledger rows by "
                          "id (follow-up row), left as in V3.0.35",
    "T246_T388_T327": "T-388 F1 (deductions on the OFF:DOORWAY face piece) / F3 (pantry paint NOT_APPLICABLE) and "
                      "T-327 O-1 / O-2 (threshold material_state, measure_pair fields) are not in this package",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is negative (a signed row is an ADDITION, never a negative deduction)")
    return float(x)


def load_inputs(doc, project_id=None):
    """URBAN_V3036_INPUTS_V1 -> the validated doc. {"schema", "project_id", "sources": [{"task", "file", "sha256",
    "merge_commit", "checker_run"}], "lines": [{"action": LIST_FILL | GROSS_RESTATE, "line_id", "expect": {"item_code",
    "element_id", "unit", "evidence_state", "gross", "measured_net"}, "gross_after" (GROSS_RESTATE), "items": [{"role",
    "id", "census_id", "face", "qty", "source", "note", "physical_check", "physical_why"}], "status", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    rows, seen = [], set()
    for i, r in enumerate(doc.get("lines") or ()):
        where = f"line {i} {r.get('line_id')}"
        if r.get("action") not in ACTIONS:
            raise InputsError(f"{where}: action {r.get('action')!r}")
        _need(r, ("line_id", "status"), where)
        if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")
        if r["line_id"] in seen:
            raise InputsError(f"{where}: a line listed twice (one list per line)")
        seen.add(r["line_id"])
        e = r.get("expect") or {}
        _need(e, ("item_code", "element_id", "unit"), f"{where} expect")
        if e.get("evidence_state") not in (None,) + VALUED_STATES:
            raise InputsError(f"{where}: a held / excluded line has no arithmetic to list")
        g, n = _num(e.get("gross"), f"{where} gross", True), _num(e.get("measured_net"), f"{where} net")
        g2 = g
        if r["action"] == "GROSS_RESTATE":
            g2 = _num(r.get("gross_after"), f"{where} gross_after", True)
            if g2 < g - BIND_TOL:
                raise InputsError(f"{where}: a restated gross {g2} below the gross field {g} (the face never shrinks)")
        elif r.get("gross_after") is not None:
            raise InputsError(f"{where}: LIST_FILL keeps the gross field (GROSS_RESTATE restates it)")
        items = r.get("items") or []
        if not items:
            raise InputsError(f"{where}: no row (an empty list is the defect, never the fill)")
        ids = set()
        d = a = 0.0
        for j, it in enumerate(items):
            w = f"{where} item {j}"
            _need(it, ("role", "id", "source"), w)
            if it["role"] not in ROLES:
                raise InputsError(f"{w}: role {it['role']!r}")
            q = _num(it.get("qty"), f"{w} qty")
            if it["id"] in ids:
                raise InputsError(f"{w}: {it['id']} listed twice in one line (a deduction counted twice)")
            ids.add(it["id"])
            if it.get("physical_check") not in (None,) + PHYSICAL:
                raise InputsError(f"{w}: physical_check {it.get('physical_check')!r}")
            if it["role"] == "DEDUCTION":
                d += q
            else:
                a += q
        if d > g2 + TOL:
            raise InputsError(f"{where}: deductions {_r(d)} above the gross {g2}")
        res = g2 - d + a - n
        if abs(res) > TOL:
            raise InputsError(f"{where}: gross {g2} - {_r(d)} + {_r(a)} = {_r(g2 - d + a)} is not the net {n} "
                              f"(residual {_r(res)}: an unlisted deduction is refused, never plugged)")
        rows.append(dict(r, _ded=_r(d), _add=_r(a), _residual=_r(res), _gross_after=g2))
    if not rows:
        raise InputsError("no line in the inputs")
    return dict(doc, _sources=srcs, _rows=rows)


# ================================================================================================ lines
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _assert_bound(b, r):
    e = r["expect"]
    if b is None:
        raise InputsError(f"line {r['line_id']}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == e["item_code"] and loc.get("element_id") == e["element_id"] and b["unit"] == e["unit"]
          and b["evidence_state"] in VALUED_STATES
          and e.get("evidence_state") in (None, b["evidence_state"]) and isinstance(b.get("gross"), (int, float))
          and abs(b["gross"] - e["gross"]) <= BIND_TOL and b.get("measured_net") is not None
          and abs(b["measured_net"] - e["measured_net"]) <= BIND_TOL)
    if not ok:
        raise InputsError(f"line {r['line_id']}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} gross "
                          f"{b.get('gross')} net {b.get('measured_net')} is not the ledger's {e} (stale binding: "
                          f"re-read the line before listing)")


def _item(it, unit):
    out = {"id": it["id"], "qty": _r(it["qty"]), "unit": unit}
    for k in ("census_id", "face", "source", "note", "physical_check", "physical_why"):
        if it.get(k) not in (None, ""):
            out[k] = it[k]
    return out


def changes_for(doc, l3035):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3035):
        raise InputsError("the candidate already carries V3.0.36 lists (applied once)")
    by = {ln["line_id"]: ln for ln in l3035}
    S = doc["_sources"]
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0,
           "rows": 0, "by_family": {}, "physical": {}}
    for r in doc["_rows"]:
        b = by.get(r["line_id"])
        _assert_bound(b, r)
        unit = b["unit"]
        srcs = [S[t] for t in r["source_tasks"]]
        ded = [_item(it, unit) for it in r["items"] if it["role"] == "DEDUCTION"]
        add = [_item(it, unit) for it in r["items"] if it["role"] == "ADDITION"]
        ln = copy.deepcopy(b)
        rec = {"policy": PIECES[PIECE]["policy"], "action": r["action"], "status": r["status"],
               "tasks": [s["task"] for s in srcs], "ledgers": [s["file"] for s in srcs],
               "ledger_sha256": [s["sha256"] for s in srcs], "merge_commits": [s["merge_commit"] for s in srcs],
               "checker_runs": [s["checker_run"] for s in srcs], "rule_id": RULE_ID, "rule_version": RULE_VERSION,
               "before": {"gross": b.get("gross"), "deductions": copy.deepcopy(b.get("deductions") or []),
                          "additions": copy.deepcopy(b.get("additions") or [])},
               "deductions_sum": r["_ded"], "additions_sum": r["_add"], "residual": r["_residual"],
               "release_status": "NOT RELEASED"}
        ln["deductions"], ln["additions"] = ded, add
        if r["action"] == "GROSS_RESTATE":
            ln["gross"] = _r(r["_gross_after"])
        ln["calculation"] = dict(ln.get("calculation") or {},
                                 inputs=dict((ln.get("calculation") or {}).get("inputs") or {}, **{REC_KEY: rec}))
        A305._note(ln, f"{METHOD}: canonical list by id ({'+'.join(r['source_tasks'])}): gross {_fmt(ln['gross'])} - "
                       f"{_fmt(r['_ded'])}" + (f" + {_fmt(r['_add'])}" if add else "") +
                   f" = {_fmt(ln['measured_net'])} {unit}; quantity unchanged; NOT RELEASED")
        from engine.source import boq_line as BL
        after = BL.validate(ln)
        unres = [x["id"] for x in ded + add if x.get("physical_check") == "UNRESOLVED"]
        held = [{"what": f"{after['item_code']} {after['location'].get('element_id')} {i}",
                 "why": "listed deduction physically questioned by a merged reading (flag only, never applied)",
                 "range": None, "scenario": None} for i in unres]
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=_ver(srcs),
                                    evidence_status="DRAWING-CONFIRMED", codes=[PIECE, r["action"]],
                                    group=after["item_code"]))
        log["by_action"][r["action"]] = log["by_action"].get(r["action"], 0) + 1
        log["lines"] += 1
        log["rows"] += len(ded) + len(add)
        k = f"{after['item_code']}|{unit}"
        f = log["by_family"].setdefault(k, {"lines": 0, "rows": 0, "listed": 0.0})
        f["lines"] += 1
        f["rows"] += len(ded) + len(add)
        f["listed"] = _r(f["listed"] + r["_ded"] - r["_add"])
        for x in ded + add:
            if x.get("physical_check"):
                log["physical"][x["physical_check"]] = log["physical"].get(x["physical_check"], 0) + 1
    log["by_action"] = dict(sorted(log["by_action"].items()))
    log["by_family"] = dict(sorted(log["by_family"].items()))
    return changes, log


# ================================================================================================ integrate / write
def check_lists(lines, only=None):
    """on finished lines: every V3.0.36 line closes gross - deductions + additions = net (TOL), each item with an id
    and a 'qty' in the line's unit, no id twice; -> summary."""
    out = {"lines": 0, "items": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec or (only is not None and ln["line_id"] not in only):
            continue
        items = (ln.get("deductions") or []) + (ln.get("additions") or [])
        ids = [x.get("id") for x in items]
        if any(i in (None, "") for i in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"{METHOD}: {ln['line_id']}: an item without an id or an id twice")
        for x in items:
            if x.get("unit") != ln["unit"] or not isinstance(x.get("qty"), (int, float)) or x["qty"] < 0:
                raise ValueError(f"{METHOD}: {ln['line_id']}: an item {x.get('id')} not one non-negative qty in "
                                 f"{ln['unit']}")
        d = sum(x["qty"] for x in ln.get("deductions") or [])
        a = sum(x["qty"] for x in ln.get("additions") or [])
        if abs(ln["gross"] - d + a - ln["measured_net"]) > TOL:
            raise ValueError(f"{METHOD}: {ln['line_id']}: gross - deductions + additions is not the net")
        out["lines"] += 1
        out["items"] += len(items)
    return out


def integrate(l3035, changes, for_lead=()):
    """-> (V3.0.36 lines, identity). Every line outside the rows is byte-identical to V3.0.35."""
    sid = {ln["line_id"] for ln in l3035}
    rep = {}
    for c in changes:
        if c["piece"] != PIECE or c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: {c['piece']} {c['action']} (this version only re-lists existing lines)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.35 or its id changed")
        rep[lid] = c["after"]
    out = [rep.get(ln["line_id"], ln) for ln in l3035]
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = A3035.check_boundary(out)
    lists = check_lists(out)
    by35 = {ln["line_id"]: ln for ln in l3035}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by35[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3035):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.36 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only the list, the gross field, calculation and notes change
        a, b = copy.deepcopy(by35[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside its list / gross / text (a quantity moved)")
    ident = {"v3_0_35_lines": len(l3035), "v3_0_36_lines": len(out), "v3_0_36_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_35": len(outside), "lists": lists, "fence": fence, "tile_zones": zones,
             "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref, bef = c["after"], c["before"]
        rec = ref["calculation"]["inputs"][REC_KEY]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": rec["action"], "status": rec["status"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_v3_0_35": A30._qty(bef), "after_v3_0_36": A30._qty(ref),
                     "gross_v3_0_35": bef.get("gross"), "gross_v3_0_36": ref.get("gross"),
                     "list_n_v3_0_35": len(bef.get("deductions") or []) + len(bef.get("additions") or []),
                     "list_n_v3_0_36": len(ref.get("deductions") or []) + len(ref.get("additions") or []),
                     "deductions_sum": rec["deductions_sum"], "additions_sum": rec["additions_sum"],
                     "residual": rec["residual"],
                     "unresolved_items": [x["id"] for x in (ref.get("deductions") or []) + (ref.get("additions") or [])
                                          if x.get("physical_check") == "UNRESOLVED"],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "status", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_35",
              "v3_0_36", "gross_v3_0_35", "gross_v3_0_36", "list_n_v3_0_35", "list_n_v3_0_36", "deductions_sum",
              "additions_sum", "residual", "unresolved_items", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_35", "vs_released_v2_9", "v2_9",
            "v3_0_35", "v3_0_36")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x else ""
    return A305._csv([{"version": r["version"], "action": r["action"], "status": r["status"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r["floor"] or "",
                       "element_id": r["element_id"] or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_35": q(r["before_v3_0_35"]),
                       "v3_0_36": q(r["after_v3_0_36"]), "gross_v3_0_35": _fmt(r["gross_v3_0_35"]),
                       "gross_v3_0_36": _fmt(r["gross_v3_0_36"]), "list_n_v3_0_35": r["list_n_v3_0_35"],
                       "list_n_v3_0_36": r["list_n_v3_0_36"], "deductions_sum": _fmt(r["deductions_sum"]),
                       "additions_sum": _fmt(r["additions_sum"]), "residual": _fmt(r["residual"]),
                       "unresolved_items": " ".join(r["unresolved_items"]),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3035, l3036, released_lines=None):
    b35 = {ln["line_id"]: ln for ln in l3035}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3036:
        o = b35.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if (A30._qty(o) != A30._qty(ln) or
                                                       o.get("bounded_range") != ln.get("bounded_range"))
                                         else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_35": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_35": A302._q(A30._qty(o)) if o else "", "v3_0_36": A302._q(A30._qty(ln))})
    return out


def write(out, l3035, changes, log, released_lines=None, for_lead=()):
    """the V3_0_36_* files beside the V3_0_35_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3036, ident = integrate(l3035, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3035, l3036, released_lines)
    if any(d["vs_v3_0_35"] == "CHANGED" for d in diff):
        raise ValueError(f"{METHOD}: a quantity moved (listing never moves a quantity)")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_35", {}).setdefault(d["vs_v3_0_35"], 0)
        dsum["vs_v3_0_35"][d["vs_v3_0_35"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t35, t36 = A304.code_totals(l3035), A304.code_totals(l3036)
    if t35 != t36:
        raise ValueError(f"{METHOD}: a code total moved (listing never moves a total)")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": {}, "waiting_pieces": WAITING}
    files = {"V3_0_36_BOQ_LINES.json": BL.dumps(l3036),
             "V3_0_36_BOQ_LINES.csv": A30._lines_csv(l3036),
             "V3_0_36_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_36_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_36_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_36_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_lists", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
