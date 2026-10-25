"""ARCH_TAKEOFF_V3.0.18 (T-266): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.17 (engine.source.arch_v30,
arch_v301 .. arch_v3017), extended with ONE closure piece: candidate lines whose status is not the status of the
checker-merged component ledger of their element are brought to it line id by line id. Not a new method family and not
the released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released
ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a line is the sum of the physical pieces of its element; it carries
a quantity only when every piece is closable, at the WEAKEST status of its pieces; otherwise it is held BLANK with its
items, and the closable pieces inside it are not lost (owner 2026-10-22 16:35: a system stays PARTIALLY VERIFIED; the
statuses are per quantity, WORKFLOW_CONTROLS s.5). Four record kinds:

  SPLIT     a HELD parent line (BLOCKED_RFI, blank) that contains closable pieces: the parent stays BLANK in place (same
            line id, its item list restated: the pieces still held, and the line ids that now carry the closable ones);
            each closable group becomes its OWN line (one status per line: VERIFIED / DRAWING-CONFIRMED -> SOURCE_DERIVED,
            ASSUMED - OWNER-APPROVED -> PROVISIONAL with its owner source), the value = the sum of its pieces;
  REBASE    a line whose pieces are all closable (e.g. a BOUNDED line whose high reading a merged ledger retired):
            the ledger value at the weakest status, in place;
  HOLD      a line whose quantity rests on a convention (no printed value): BLOCKED_RFI blank in place, the named item,
            the closable part named (never booked here when the ledger books it elsewhere: cited_from);
  MATERIAL  a finish MATERIAL line for an element another line already measures as floor AREA (one element, one material
            line of a code): value = that element line's quantity, at that element line's own evidence status (never
            VERIFIED unless the record names the checker run), the area line unchanged;
  PIECE_LINE  a drawing-confirmed piece no candidate line carries (an engine strip held on a misread boundary that the
            merged ledger settles): its OWN line beside its sibling (same item, unit, identity and documents), at the
            weakest of its geometry and class statuses; a piece another candidate line books with a quantity is
            refused (one owner per piece).

Refused (InputsError / ValueError, nothing written): a record whose line the candidate does not carry, or whose stated
'before' is not the line's (stale ledger); a line named twice; a part / rebase value <= 0, or not the sum of its pieces;
a piece in two parts or lines; a part whose pieces carry another status than the part (one status per line); a
convention piece (CONVENTION / HELD / CONFLICT / UNKNOWN) in a released part; a split of a parent that carries a figure
(a closable part released while also inside its held parent); a VERIFIED part / rebase with no checker run; an
owner-approved part with no answered-decision source; a HOLD with a figure or no item; a second MATERIAL line of one code
on one element; a material value that is not the element line's; a PIECE_LINE piece another line books. Everything outside
the records is byte-identical to V3.0.17 (asserted), including the project identity block.

Files: V3_0_18_BOQ_LINES.json / .csv, V3_0_18_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.17, after, released
V2.9, evidence status, pieces, source task / merge / checker run, held items), V3_0_18_DIFF.csv (every line against
V3.0.17 and the released V2.9), V3_0_18_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate: every
value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3017 as A3017

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: brings named lines to a merged ledger; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.18"
EXTENDS = A3017.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T266_ARCH_V3_0_18"
INPUTS_SCHEMA = "URBAN_V3018_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3018_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
KINDS = ("SPLIT", "REBASE", "HOLD", "MATERIAL", "PIECE_LINE")
VER, DC, OA = "VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"
STATUSES = (VER, DC, OA)
STATE_OF = {VER: "SOURCE_DERIVED", DC: "SOURCE_DERIVED", OA: "PROVISIONAL"}   # V3.0.10 / V3.0.13 convention
WEAK = {VER: 3, DC: 2, OA: 1}
NOT_CLOSABLE = ("CONVENTION", "HELD", "CONFLICT", "UNKNOWN", "OWNED_ELSEWHERE")
TOL = 1e-6
TOL_SUM = 5e-6
InputsError = A3015.InputsError
_num = A3015._num
RULE_ID, RULE_VERSION = "R-COMPONENT-CLOSURE-1", "T-266"

PIECES = {
    "COMPONENT_CLOSURE": {
        "module": "engine/source/arch_v3018.py (checker-merged component ledgers applied line id by line id)",
        "policy": "COMPONENT_CLOSURE_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["owner 2026-10-22 16:35 / 16:45 (the staircase system stays PARTIALLY VERIFIED; statuses per "
                        "quantity)", "owner 2026-10-24 10:56 (held BLANK in the BOQ)", "owner 2026-10-24 23:57 (2): "
                        "UNSUPPORTED BASIS", "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / "
                        "s.5", "OWNER_RULE_STAIRS_2026-10-21 / 2026-10-24", "R-CONC-OWN-1 (one owner per piece)",
                        "Q-50 A cond (round-stair riser)", "Q-66 B (1F arrival landing marble)",
                        "Q-37 A (pantry wet in its printed box)"],
        "owner_manual_method": "the owner measures a stair flight by its printed treads, risers and waist and a landing "
                               "plate between its drawn edges; where the riser of the round stair is not printed, Q-50 A "
                               "(condition) gives it (ASSUMED - OWNER-APPROVED); an unprinted waist or winder is HELD "
                               "(no owner fallback, WORKFLOW_CONTROLS s.4); a landing finish follows its stair (Q-66 B); "
                               "a pantry is wet within its printed box (Q-37 A)",
        "drawing_method": "each piece from its drawn lines (structural stair sheets: riser / tread lines, landing "
                          "edges, printed T); one line per status group of closable pieces, the rest of the element "
                          "HELD blank with its items; the marble landing is the landing's own measured area; the "
                          "pantry piece is bounded by drawn wall / room / counter lines inside the printed box"},
}
WAITING = dict(A3017.WAITING)
WAITING.update({
    "DOME_DRUMS": "DOME-A / DOME-B drums: a named omission (no candidate line, no number): drum material / thickness "
                  "not printed (G3-b); Lead 2026-10-25 14:15",
    "STAIR_HELD_PIECES": "MS1-L CONFLICT (C-ST-4), MS1-T / turn slab / MS2-TR (C-ST-3 / G2-a / G2-c), D1 / RS-C / E1 "
                         "waists (G2-w), RS-C curved part (Q-50 / Q-51), CA level, 2CC (UNKNOWN): HELD blank",
    "ST03_STEPS": "ST-03 steps 0.355017 m3 DRAWING-CONFIRMED are named on the held ST-03 line (T-289 row ST03), not "
                  "released as their own line in this package",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _slug(s):
    return "".join(c if c.isalnum() else "_" for c in str(s)).strip("_")


# ================================================================================================ inputs
def _source(s, where):
    for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
        if not (isinstance(s, dict) and isinstance(s.get(k), str) and s[k].strip()):
            raise InputsError(f"{where}: source needs {k} (a merged ledger: file sha256, task, merge commit, checker run)")


def _check_before(r, where):
    b = r.get("before") or {}
    if b.get("evidence_state") is None or "measured_net" not in b:
        raise InputsError(f"{where}: before {{evidence_state, measured_net}} is asserted against the line")


def _check_pieces(pieces, status, value, where, seen_pieces):
    if not pieces:
        raise InputsError(f"{where}: a released quantity names its pieces")
    s = 0.0
    for p in pieces:
        pid = p.get("id")
        if not pid:
            raise InputsError(f"{where}: every piece has an id")
        if pid in seen_pieces:
            raise InputsError(f"{where}: piece {pid} is in two lines / parts (one owner per piece)")
        seen_pieces.add(pid)
        if p.get("status") in NOT_CLOSABLE or p.get("status") not in STATUSES:
            raise InputsError(f"{where}: piece {pid} status {p.get('status')!r} is not closable (a convention, held, "
                              "conflict or unknown piece is never released)")
        if p["status"] != status:
            raise InputsError(f"{where}: piece {pid} is {p['status']}, the line {status}: one status per line (split "
                              "by status, never promoted to the strongest)")
        if not (_num(p.get("value")) and p["value"] > 0):
            raise InputsError(f"{where}: piece {pid} carries value > 0 (a missing piece is HELD, never 0)")
        s += p["value"]
    if abs(s - value) > TOL_SUM:
        raise InputsError(f"{where}: value {value} != the sum of its pieces {_r(s)}")


def _check_status(x, where):
    st = x.get("status")
    if st not in STATUSES:
        raise InputsError(f"{where}: status {st!r} not one of {STATUSES}")
    if st == VER and not x.get("verified_by"):
        raise InputsError(f"{where}: VERIFIED names the checker run(s) that re-measured it")
    if st == OA and not x.get("owner_source"):
        raise InputsError(f"{where}: ASSUMED - OWNER-APPROVED names its answered owner decision (WORKFLOW_CONTROLS s.4)")
    if not (_num(x.get("value")) and x["value"] > 0):
        raise InputsError(f"{where}: a released quantity carries value > 0 (a missing value is HELD, never 0)")


def _check_record(r, tasks, seen, seen_pieces):
    kind = r.get("kind")
    if kind not in KINDS:
        raise InputsError(f"record kind {kind!r} not one of {KINDS}")
    lid = r.get("line_id")
    if not lid:
        raise InputsError(f"{kind}: every record names its candidate line id")
    if kind not in ("MATERIAL", "PIECE_LINE"):
        if lid in seen:
            raise InputsError(f"line {lid} named twice (one record per line)")
        seen.add(lid)
    for k in ("item_code", "element_id", "task", "physical_element"):
        if not r.get(k):
            raise InputsError(f"record {lid}: {k} required")
    if r["task"] not in tasks:
        raise InputsError(f"record {lid}: task {r['task']!r} is not one of the merged sources {sorted(tasks)}")
    if kind not in ("MATERIAL", "PIECE_LINE"):
        _check_before(r, f"record {lid}")
    if kind == "SPLIT":
        b = r["before"]
        if b["evidence_state"] != "BLOCKED_RFI" or b["measured_net"] is not None:
            raise InputsError(f"record {lid}: a split parent is a HELD blank line (a closable part released while also "
                              "inside a parent that carries a figure is a double count)")
        if not r.get("still_held"):
            raise InputsError(f"record {lid}: a split names the pieces that stay held (else it is a REBASE)")
        for h in r["still_held"]:
            if not h.get("piece") or not h.get("item"):
                raise InputsError(f"record {lid}: each piece still held names its item")
            if h.get("value") is not None:
                raise InputsError(f"record {lid}: a held piece carries no figure (BLANK, never 0)")
        parts = r.get("parts") or []
        if not parts:
            raise InputsError(f"record {lid}: a split carries at least one closable part")
        names = set()
        for p in parts:
            w = f"record {lid} part {p.get('part')}"
            if not p.get("part") or p["part"] in names:
                raise InputsError(f"{w}: a part name, once")
            names.add(p["part"])
            _check_status(p, w)
            _check_pieces(p.get("pieces"), p["status"], p["value"], w, seen_pieces)
    elif kind == "REBASE":
        _check_status(r, f"record {lid}")
        _check_pieces(r.get("pieces"), r["status"], r["value"], f"record {lid}", seen_pieces)
    elif kind == "HOLD":
        for k in ("value", "low", "high", "pieces"):
            if r.get(k) is not None:
                raise InputsError(f"record {lid}: a HOLD record carries no figure ({k}): BLANK in the BOQ")
        if not r.get("held_item") or not r.get("reasons"):
            raise InputsError(f"record {lid}: a HOLD names the item that holds it and why")
    elif kind == "MATERIAL":
        for k in ("id", "unit", "floor", "item_en", "item_ar", "trade", "material_of"):
            if not r.get(k):
                raise InputsError(f"material {r.get('id')}: {k} required")
        if r["id"] in seen:
            raise InputsError(f"material {r['id']}: an id, once")
        seen.add(r["id"])
        _check_status(r, f"material {r['id']}")
        if r["status"] == VER:
            raise InputsError(f"material {r['id']}: a new material line is never VERIFIED here (the Checker verifies "
                              "the line it sees, not the area line it is taken from)")
    else:  # PIECE_LINE
        for k in ("id", "unit", "floor", "like_line_id"):
            if not r.get(k):
                raise InputsError(f"piece line {r.get('id')}: {k} required")
        if r["id"] in seen:
            raise InputsError(f"piece line {r['id']}: an id, once")
        seen.add(r["id"])
        pc = r.get("piece") or {}
        for k in ("id", "value", "status", "class", "class_source"):
            if pc.get(k) in (None, ""):
                raise InputsError(f"piece line {r['id']}: the piece names {k}")
        if pc["status"] not in (DC, VER):
            raise InputsError(f"piece line {r['id']}: the piece geometry is DRAWING-CONFIRMED or VERIFIED")
        if pc["id"] in seen_pieces:
            raise InputsError(f"piece line {r['id']}: piece {pc['id']} in two records")
        seen_pieces.add(pc["id"])
        _check_status(r, f"piece line {r['id']}")
        if WEAK[r["status"]] > WEAK[pc["status"]] or (r.get("class_status") == OA and r["status"] != OA):
            raise InputsError(f"piece line {r['id']}: the line takes the WEAKEST of its geometry and class statuses")
        if abs(r["value"] - pc["value"]) > TOL:
            raise InputsError(f"piece line {r['id']}: value {r['value']} is not the piece's {pc['value']}")


def load_inputs(doc, project_id=None):
    """URBAN_V3018_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{kind SPLIT | REBASE | HOLD | MATERIAL | PIECE_LINE, line_id, item_code, element_id, task,
                      physical_element, before: {evidence_state, measured_net},
                      SPLIT: still_held [{piece, item}], parts [{part, status, value, pieces [{id, value, status}],
                             verified_by, owner_source, formula}];
                      REBASE: status, value, pieces, verified_by, formula;
                      HOLD: held_item, reasons, cited_from, closable_named;
                      MATERIAL: id, unit, floor, item_en, item_ar, trade, material_of (element line id), status, value,
                                owner_source, formula, like_line_id;
                      PIECE_LINE: id, unit, floor, like_line_id, status, class_status, owner_source, value,
                                  piece {id, value, status, class, class_source}, formula}],
         "declared": {"released_m3_added", ...} (optional totals asserted on the run)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged ledgers the records come from")
    tasks = set()
    for s in srcs:
        _source(s, "sources")
        tasks.add(s["task"])
    recs = doc.get("records") or []
    if not recs:
        raise InputsError("no records")
    seen, seen_pieces = set(), set()
    for r in recs:
        _check_record(r, tasks, seen, seen_pieces)
    return doc


def _src_of(doc, task):
    for s in doc["sources"]:
        if s["task"] == task:
            return s
    raise InputsError(f"no merged source for task {task}")


# ================================================================================================ lines
def _rec(r, src, **kw):
    return dict({"policy": PIECES["COMPONENT_CLOSURE"]["policy"], "kind": r["kind"], "task": src["task"],
                 "ledger": src["file"], "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"],
                 "checker_run": src["checker_run"], "physical_element": r["physical_element"]}, **kw)


def _before_rec(b):
    return {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"),
            "bounded_range": b.get("bounded_range"), "formula": b["calculation"]["formula"]}


def part_element_id(parent_element_id, part):
    return f"{parent_element_id}#CLOSABLE:{_slug(part)}"


def part_line(parent, r, p, src):
    """the line of one closable part of a held parent: same identity / documents / item as the parent, its own element
    id (parent element + part), its own status."""
    from engine.source import boq_line as BL
    pr = parent["project"]
    loc = parent["location"]
    eid = part_element_id(loc.get("element_id"), p["part"])
    st = p["status"]
    rec = _rec(r, src, action="SPLIT_PART", parent_line_id=parent["line_id"], part=p["part"], status=st,
               evidence_status=st, value=_r(p["value"]), pieces=copy.deepcopy(p["pieces"]),
               verified_by=p.get("verified_by"), owner_source=p.get("owner_source"))
    formula = p.get("formula") or (" + ".join(f"{x['id']} {_r(x['value'])}" for x in p["pieces"]) +
                                   f" = {_r(p['value'])} m3 ({st})")
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=parent["item_code"], unit=parent["unit"], evidence_state=STATE_OF[st],
                      measured_net=_r(p["value"]), element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                      room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                      physical_element=f"{r['physical_element']}: {p['part']}", formula=formula[:600],
                      inputs={"component_closure_v3018": rec},
                      documents=copy.deepcopy(parent["source"]["documents"]),
                      geometry_source=parent["source"]["geometry_source"],
                      geometry_confidence="TOLERANCE_CERTIFIED" if st in (VER, DC) else "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=parent["material_state"],
                      notes=f"{METHOD}: closable part of held line {parent['line_id']} ({src['task']} MERGED "
                            f"{src['merge_commit']}, {src['checker_run']}): {st}"
                            + (f" ({p['owner_source']})" if st == OA else "")
                            + (f" (verified: {p['verified_by']})" if st == VER else ""),
                      subtrade=parent.get("subtrade"), item_en=parent.get("item_en"), item_ar=parent.get("item_ar"),
                      trade=parent.get("trade"))
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def split_parent(parent, r, src, part_ids):
    """the parent in place: still BLANK, its item list restated (the pieces still held, the lines carrying the rest)."""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(parent)
    held = "; ".join(f"{h['piece']}: {h['item']}" for h in r["still_held"])
    carried = "; ".join(f"{p['part']} {_r(p['value'])} {p['status']} on {part_ids[p['part']]}" for p in r["parts"])
    ln["evidence_state"] = "BLOCKED_RFI"
    ln["measured_net"] = None
    ln["bounded_range"] = None
    ln["rfi"] = {"question": f"HELD pieces: {held}"[:900], "unlocks": ln["location"].get("element_id")}
    ln["calculation"]["formula"] = (f"HELD remainder (blank in the BOQ, never 0): {held} | closable parts carried on "
                                    f"their own lines: {carried}")[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, component_closure_v3018=_rec(
        r, src, action="SPLIT_PARENT", before=_before_rec(parent), still_held=copy.deepcopy(r["still_held"]),
        parts={p["part"]: part_ids[p["part"]] for p in r["parts"]}))
    A305._note(ln, f"{METHOD}: held remainder of a split ({src['task']} MERGED {src['merge_commit']}); its closable "
                   "parts are their own lines; blank in the BOQ, never 0")
    return BL.validate(ln)


def rebased_line(before, r, src):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    st = r["status"]
    ln["evidence_state"] = STATE_OF[st]
    ln["measured_net"] = _r(r["value"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["calculation"]["formula"] = (r.get("formula") or " + ".join(
        f"{x['id']} {_r(x['value'])}" for x in r["pieces"]))[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, component_closure_v3018=_rec(
        r, src, action="REBASE", before=_before_rec(before), status=st, evidence_status=st, value=_r(r["value"]),
        pieces=copy.deepcopy(r["pieces"]), verified_by=r.get("verified_by"), owner_source=r.get("owner_source"),
        retired=r.get("retired")))
    A305._note(ln, f"{METHOD}: every piece closable ({src['task']} MERGED {src['merge_commit']}, {src['checker_run']}): "
                   f"{st}")
    return BL.validate(ln)


def held_line(before, r, src):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    ln["evidence_state"] = "BLOCKED_RFI"
    ln["measured_net"] = None
    ln["bounded_range"] = None
    ln["rfi"] = {"question": (f"{r['held_item']}: " + "; ".join(r["reasons"]))[:900],
                 "unlocks": ln["location"].get("element_id")}
    ln["calculation"]["formula"] = (f"HOLD (blank in the BOQ, never 0): {r['held_item']}"
                                    + (f" | closable part named, not booked here: {r['closable_named']}"
                                       if r.get("closable_named") else ""))[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, component_closure_v3018=_rec(
        r, src, action="HOLD", before=_before_rec(before), held_item=r["held_item"], reasons=list(r["reasons"]),
        cited_from=r.get("cited_from"), closable_named=r.get("closable_named"), resolves=r.get("resolves")))
    A305._note(ln, f"{METHOD}: HOLD on a convention basis ({src['task']} MERGED {src['merge_commit']}"
                   + (f"; cited from {r['cited_from']}" if r.get("cited_from") else "") + "); blank, never 0")
    return BL.validate(ln)


def material_line(lines, r, src):
    """a finish MATERIAL line of an element another line measures as floor AREA: the element line's own quantity."""
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in lines}
    el = by.get(r["material_of"])
    if el is None:
        raise InputsError(f"material {r['id']}: material_of {r['material_of']} is not a candidate line")
    if el["evidence_state"] not in BL.QUANTITY_STATES or not (el.get("measured_net") or 0) > 0:
        raise InputsError(f"material {r['id']}: the element line {el['line_id']} carries no quantity (a material line "
                          "of a held area is HELD with it, its own package)")
    if el["unit"] != r["unit"] or abs(el["measured_net"] - r["value"]) > TOL:
        raise InputsError(f"material {r['id']}: value {r['value']} {r['unit']} is not the element line's "
                          f"{el['measured_net']} {el['unit']}")
    eid = el["location"].get("element_id")
    if eid != r["element_id"]:
        raise InputsError(f"material {r['id']}: element {r['element_id']} is not the element line's {eid}")
    for ln in lines:
        if ln["item_code"] == r["item_code"] and (
                ln["location"].get("element_id") == eid or
                ((ln.get("calculation") or {}).get("inputs") or {}).get("component_closure_v3018", {}).get(
                    "material_of") == el["line_id"]):
            raise InputsError(f"material {r['id']}: {ln['line_id']} already carries {r['item_code']} on element {eid} "
                              "(one element, one material line of a code)")
    sib = by.get(r.get("like_line_id")) if r.get("like_line_id") else None
    if r.get("like_line_id") and (sib is None or sib["item_code"] != r["item_code"] or sib["unit"] != r["unit"]):
        raise InputsError(f"material {r['id']}: like_line_id is not a candidate line of the same item / unit")
    pr = el["project"]
    st = r["status"]
    rec = _rec(r, src, action="MATERIAL", material_of=el["line_id"], element_line_state=el["evidence_state"],
               status=st, evidence_status=st, value=_r(r["value"]), owner_source=r.get("owner_source"))
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=r["item_code"], unit=r["unit"], evidence_state=STATE_OF[st],
                      measured_net=_r(r["value"]), element_id=f"{eid}#MATERIAL:{_slug(r['item_code'])}",
                      floor=r["floor"], room_id=el["location"].get("room_id"),
                      room_name_en=el["location"].get("room_name_en"), room_name_ar=el["location"].get("room_name_ar"),
                      physical_element=r["physical_element"],
                      formula=(r.get("formula") or f"= element line {el['line_id']} {_r(el['measured_net'])} "
                                                   f"{el['unit']} (the area measure stays that line)")[:600],
                      inputs={"component_closure_v3018": rec}, documents=copy.deepcopy(el["source"]["documents"]),
                      geometry_source=el["source"]["geometry_source"],
                      geometry_confidence=el["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state="PROJECT_OWNER_FACT" if r.get("owner_source")
                      else "BY_SPEC",
                      notes=f"{METHOD}: material line of element line {el['line_id']} ({src['task']} MERGED "
                            f"{src['merge_commit']}, {src['checker_run']}): {st}; never additive with it as AREA",
                      never_additive_with=[], subtrade=(sib or {}).get("subtrade"), item_en=r["item_en"],
                      item_ar=r["item_ar"], trade=r["trade"])
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def piece_line(lines, r, src):
    """a confirmed piece no line carries, as its own line beside its sibling (identity / documents / item of the
    sibling); a piece another line books with a quantity is refused."""
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in lines}
    sib = by.get(r["like_line_id"])
    if sib is None or sib["item_code"] != r["item_code"] or sib["unit"] != r["unit"]:
        raise InputsError(f"piece line {r['id']}: like_line_id is not a candidate line of the same item / unit")
    pc = r["piece"]
    for ln in lines:      # a piece another line books with a quantity is a double count
        blob = json.dumps(ln.get("calculation") or {}, sort_keys=True, default=str)
        if pc["id"] in blob and ln["evidence_state"] in BL.QUANTITY_STATES and (ln.get("measured_net") or 0) > 0:
            raise InputsError(f"piece line {r['id']}: piece {pc['id']} is already booked with a quantity on "
                              f"{ln['line_id']} ({ln['item_code']}): one owner per piece")
    pr = sib["project"]
    st = r["status"]
    rec = _rec(r, src, action="PIECE_LINE", like_line_id=sib["line_id"], piece=copy.deepcopy(pc), status=st,
               evidence_status=st, value=_r(r["value"]), owner_source=r.get("owner_source"),
               floor_key=r.get("floor_key"))
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=r["item_code"], unit=r["unit"], evidence_state=STATE_OF[st],
                      measured_net=_r(r["value"]), element_id=r["element_id"], floor=r["floor"],
                      room_id=sib["location"].get("room_id"), physical_element=sib.get("physical_element"),
                      formula=(r.get("formula") or f"piece {pc['id']} {_r(pc['value'])} {r['unit']} ({pc['class']}, "
                                                   f"{pc['class_source']})")[:600],
                      inputs={"component_closure_v3018": rec}, documents=copy.deepcopy(sib["source"]["documents"]),
                      geometry_source=sib["source"]["geometry_source"],
                      geometry_confidence="TOLERANCE_CERTIFIED" if pc["status"] in (VER, DC) else "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=sib["material_state"],
                      notes=f"{METHOD}: piece {pc['id']} no line carried ({src['task']} MERGED {src['merge_commit']}, "
                            f"{src['checker_run']}): geometry {pc['status']}, class {pc['class']} by "
                            f"{pc['class_source']}; line {st}",
                      subtrade=sib.get("subtrade"), item_en=sib.get("item_en"), item_ar=sib.get("item_ar"),
                      trade=sib.get("trade"))
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def _assert_before(b, r):
    if b is None:
        raise InputsError(f"record {r['line_id']}: the candidate does not carry this line")
    if b["item_code"] != r["item_code"] or b["location"].get("element_id") != r["element_id"]:
        raise InputsError(f"record {r['line_id']}: item / element {r['item_code']} {r['element_id']} is not the line's "
                          f"{b['item_code']} {b['location'].get('element_id')}")
    bq, rb = b.get("measured_net"), r["before"]
    if b["evidence_state"] != rb["evidence_state"] or (bq is None) != (rb["measured_net"] is None) or \
            (bq is not None and abs(bq - rb["measured_net"]) > TOL):
        raise InputsError(f"record {r['line_id']}: the ledger's before {rb} is not the line's {b['evidence_state']} "
                          f"{bq} (stale ledger: refused)")


def changes_for(doc, l3017):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "COMPONENT_CLOSURE", "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3017}
    changes = []
    work = list(l3017)
    for r in doc["records"]:
        src = _src_of(doc, r["task"])
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"]}
        if r["kind"] in ("MATERIAL", "PIECE_LINE"):
            ln = material_line(work, r, src) if r["kind"] == "MATERIAL" else piece_line(work, r, src)
            if ln["line_id"] in by:
                raise ValueError(f"{METHOD}: added line {r['id']} repeats a candidate line id")
            work.append(ln)
            changes.append(A305._change("COMPONENT_CLOSURE", "ADD", None, ln, drawing_reference=r.get("printed"),
                                        held=[], downstream=list(r.get("downstream") or ()),
                                        verification=dict(ver, record_status=r["status"],
                                                          owner_source=r.get("owner_source")),
                                        evidence_status=r["status"], codes=["COMPONENT_CLOSURE", r["kind"]],
                                        group=r.get("group") or r["kind"]))
            continue
        b = by.get(r["line_id"])
        _assert_before(b, r)
        grp = r.get("group") or r["kind"]
        if r["kind"] == "SPLIT":
            pids = {}
            adds = []
            for p in r["parts"]:
                pl = part_line(b, r, p, src)
                if pl["line_id"] in by or pl["line_id"] in pids.values():
                    raise ValueError(f"{METHOD}: part {p['part']} of {b['line_id']} repeats a line id")
                pids[p["part"]] = pl["line_id"]
                adds.append((p, pl))
            after = split_parent(b, r, src, pids)
            changes.append(A305._change("COMPONENT_CLOSURE", "REPLACE", b, after,
                                        drawing_reference=r.get("printed"),
                                        held=[{"what": f"{r['item_code']} {r['element_id']}: {h['piece']}",
                                               "why": h["item"], "range": None, "scenario": None}
                                              for h in r["still_held"]],
                                        downstream=list(r.get("downstream") or ()), verification=ver,
                                        evidence_status="HELD (remainder of a split)",
                                        codes=["COMPONENT_CLOSURE", "SPLIT_PARENT"], group=grp))
            for p, pl in adds:
                work.append(pl)
                changes.append(A305._change("COMPONENT_CLOSURE", "ADD", None, pl, drawing_reference=p.get("printed"),
                                            held=[], downstream=list(r.get("downstream") or ()),
                                            verification=dict(ver, record_verified_by=p.get("verified_by"),
                                                              owner_source=p.get("owner_source")),
                                            evidence_status=p["status"], codes=["COMPONENT_CLOSURE", "SPLIT_PART"],
                                            group=grp, parent_line_id=b["line_id"]))
        elif r["kind"] == "REBASE":
            after = rebased_line(b, r, src)
            changes.append(A305._change("COMPONENT_CLOSURE", "REPLACE", b, after, drawing_reference=r.get("printed"),
                                        held=[], downstream=list(r.get("downstream") or ()),
                                        verification=dict(ver, record_verified_by=r.get("verified_by")),
                                        evidence_status=r["status"], codes=["COMPONENT_CLOSURE", "REBASE"], group=grp))
        elif r["kind"] == "HOLD":
            after = held_line(b, r, src)
            changes.append(A305._change("COMPONENT_CLOSURE", "REPLACE", b, after, drawing_reference=r.get("printed"),
                                        held=[{"what": f"{r['item_code']} {r['element_id']}",
                                               "why": f"{r['held_item']}: " + "; ".join(r["reasons"]), "range": None,
                                               "scenario": None}],
                                        downstream=list(r.get("downstream") or ()), verification=ver,
                                        evidence_status="HELD", codes=["COMPONENT_CLOSURE", "HOLD"], group=grp))
    groups = {}
    for c in changes:
        g = groups.setdefault(c["group"], {"rows": 0, "before_released": 0.0, "after_released": 0.0, "held_lines": 0})
        g["rows"] += 1
        if c["before"] is not None and c["before"]["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL"):
            g["before_released"] += c["before"]["measured_net"]
        if c["after"]["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL"):
            g["after_released"] += c["after"]["measured_net"]
        elif c["after"]["evidence_state"] == "BLOCKED_RFI":
            g["held_lines"] += 1
    groups = {k: {kk: (_r(v) if isinstance(v, float) else v) for kk, v in d.items()} for k, d in sorted(groups.items())}
    dec = doc.get("declared") or {}
    for g, d in dec.items():
        got = groups.get(g)
        if got is None or abs(got["before_released"] - d["before_released"]) > TOL_SUM or \
                abs(got["after_released"] - d["after_released"]) > TOL_SUM:
            raise ValueError(f"{METHOD}: group {g} gives {got}, declared {d}")
    log = {"piece": "COMPONENT_CLOSURE", "state": "RUN", "sources": doc["sources"], "groups": groups,
           "adds": [c["after"]["line_id"] for c in changes if c["action"] == "ADD"]}
    return changes, log


# ================================================================================================ integrate / write
def check_splits(lines):
    """on finished lines: every closable part names a parent that is a HELD blank line naming that part; no part twice.
    -> number of parts."""
    by = {ln["line_id"]: ln for ln in lines}
    n = 0
    seen = set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("component_closure_v3018") or {}
        if rec.get("action") != "SPLIT_PART":
            continue
        n += 1
        par = by.get(rec.get("parent_line_id"))
        if par is None:
            raise ValueError(f"{METHOD}: part {ln['line_id']} names a parent the run does not carry")
        if par["evidence_state"] != "BLOCKED_RFI" or par.get("measured_net") is not None or par.get("bounded_range"):
            raise ValueError(f"{METHOD}: part {ln['line_id']} released while its parent {par['line_id']} carries a "
                             "figure (double count)")
        prec = ((par.get("calculation") or {}).get("inputs") or {}).get("component_closure_v3018") or {}
        if ln["line_id"] not in (prec.get("parts") or {}).values():
            raise ValueError(f"{METHOD}: parent {par['line_id']} does not name its part {ln['line_id']}")
        for p in rec.get("pieces") or ():
            if p["id"] in seen:
                raise ValueError(f"{METHOD}: piece {p['id']} released on two lines")
            seen.add(p["id"])
    return n


def integrate(l3017, changes):
    """-> (V3.0.18 lines, identity). Every line outside the V3.0.18 rows is byte-identical to the V3.0.17 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3017}
    rep, adds = {}, []
    for c in changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.17 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.17 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3017] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
        if ln["evidence_state"] in BL.QUANTITY_STATES and (ln.get("calculation") or {}).get("inputs", {}).get(
                "component_closure_v3018") and not (ln["measured_net"] or 0) > 0:
            raise ValueError(f"{METHOD}: {ln['line_id']} closed to 0")
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    nparts = check_splits(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by17 = {ln["line_id"]: ln for ln in l3017}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by17[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3017):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.18 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by17[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_17_lines": len(l3017), "v3_0_18_lines": len(out), "v3_0_18_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "split_parts": nparts, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_17": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    p = PIECES["COMPONENT_CLOSURE"]
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b17 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_17")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        rec = c["after"]["calculation"]["inputs"]["component_closure_v3018"]
        loc = c["after"].get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "kind": rec.get("action"),
                     "line_id": c["after"]["line_id"], "parent_line_id": c.get("parent_line_id"),
                     "item_code": c["after"]["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": c["after"]["unit"], "group": c.get("group"),
                     "before_released_v2_9": b29, "before_v3_0_17": b17, "after_v3_0_18": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status"), "release_status": "NOT RELEASED",
                     "pieces": rec.get("pieces") or ([rec["piece"]] if rec.get("piece") else []),
                     "codes": c.get("codes") or [], "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"], "verification": dict(c.get("verification") or {},
                                                                            module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "kind", "group", "line_id", "parent_line_id", "item_code", "floor", "element_id", "unit",
              "v2_9", "v3_0_17", "v3_0_18", "evidence_status", "release_status", "pieces", "verification", "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "kind": r["kind"], "group": r["group"], "line_id": r["line_id"],
                       "parent_line_id": r["parent_line_id"] or "", "item_code": r["item_code"], "floor": r["floor"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_17": A302._q(r["before_v3_0_17"]), "v3_0_18": A302._q(r["after_v3_0_18"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "pieces": " + ".join(f"{p.get('id')} {_r(p.get('value'))}" for p in r["pieces"])[:400],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')} "
                                       f"{r['verification'].get('verifier_run')}",
                       "held": "; ".join(f"{h.get('what')}: {h.get('why')}" for h in r["held"])[:600]} for r in rows],
                     LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_17", "vs_released_v2_9", "v2_9",
            "v3_0_17", "v3_0_18")


def diff_rows(l3017, l3018, released_lines=None):
    b17 = {ln["line_id"]: ln for ln in l3017}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3018:
        o = b17.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_17": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_17": A302._q(A30._qty(o)) if o else "", "v3_0_18": A302._q(A30._qty(ln))})
    return out


def write(out, l3017, changes, log, doc, released_lines=None):
    """the V3_0_18_* files beside the V3_0_17_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3018, ident = integrate(l3017, changes)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3017, l3018, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_17", {}).setdefault(d["vs_v3_0_17"], 0)
        dsum["vs_v3_0_17"][d["vs_v3_0_17"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t17, t18 = A304.code_totals(l3017), A304.code_totals(l3018)
    moved = {k: {"v3_0_17": t17.get(k), "v3_0_18": t18.get(k)} for k in sorted(set(t17) | set(t18))
             if t17.get(k) != t18.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_log": log,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_18_BOQ_LINES.json": BL.dumps(l3018),
             "V3_0_18_BOQ_LINES.csv": A30._lines_csv(l3018),
             "V3_0_18_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_18_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_18_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_18_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "part_line",
           "split_parent", "rebased_line", "held_line", "material_line", "piece_line", "changes_for",
           "check_splits", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
