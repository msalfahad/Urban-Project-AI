"""ARCH_TAKEOFF_V3.0.26 (T-279): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.25 (engine.source.arch_v30,
arch_v301 .. arch_v3025), extended with ONE piece, BLOCKWORK_FILL: the candidate's held blockwork lines (one per
storey x wall thickness x item: MAS.BLOCK m2, ARCH.WALL_PANEL m2, ARCH.WALL_VOLUME m3, all BLOCKED_RFI blank since
V3.0.15) carry the walls a checker-merged wall-by-wall fill established, each wall once, at its own status; the walls
and pieces still held stay BLANK on the parent line, by name. Not a new method family and not the released default
(owner management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a block wall is the masonry between its two faces from the
structural floor to the underside of the member over it, less the openings built into it (each opening once, by id).
A storey / thickness line is the sum of its walls. A wall is released only at the status of its own evidence; a line
whose walls are not all closable stays HELD blank and its closable walls are not lost (owner 2026-10-22 16:35; the
V3.0.18 split convention):

  PART      one line per (status, block type) group of closable walls of a held parent: VERIFIED / DRAWING-CONFIRMED ->
            SOURCE_DERIVED, ASSUMED - OWNER-APPROVED -> PROVISIONAL with its answered owner decision; value = the sum
            of its walls, each wall a named piece (a whole wall, or the ESTABLISHED part of a wall whose other piece is
            held: kind ESTABLISHED_PART, its held piece named on the parent);
  PARENT    the held line in place (same line id): BLANK, its item list restated: every wall still HELD with its
            item, every drop wall with its terms U - L x d (never evaluated, never a range in the BOQ), every held piece
            of a part-established wall, every width-CONFLICT increment (outside every total), and the part line ids;
  RESTATE   a held line with no closable wall: BLANK in place, its held walls named.

Refused (InputsError / ValueError, nothing written): a line the candidate does not carry, or whose stated 'before'
is not the line's (stale fill); a parent that carries a figure (a released part inside a parent with a figure is a
double count); a wall twice in one item (one line per wall per item) or a wall with two statuses; a HELD / drop wall
written with a figure (held is BLANK, never 0; a drop term is never evaluated); a released wall <= 0; a VERIFIED wall
without its checker run; an ASSUMED - OWNER-APPROVED wall without its answered owner decision; an unknown status; an
m3 wall that is not its m2 x the line thickness; a WALL_PANEL wall that is not its MAS.BLOCK wall; a part whose walls
carry another status or block type than the part; the declared per-line figures of the merged fill not reproduced.
Every line outside the records is byte-identical to V3.0.25 (asserted); inside a record only state, quantity, range,
rfi, calculation and notes change.

Files: V3_0_26_BOQ_LINES.json / .csv, V3_0_26_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.25, after,
released V2.9, evidence status, walls with their openings, source task / merge / checker runs, held items),
V3_0_26_WALLS.csv (per wall per item: line, status, carried, held item, drop terms), V3_0_26_DIFF.csv (every line
against V3.0.25 and the released V2.9), V3_0_26_RUN.json. Nothing here names a project, a sheet, a layer or a
coordinate: every value comes from the inputs.
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
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import arch_v3024 as A3024
from engine.source import arch_v3025 as A3025

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: brings named held lines to a merged fill; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.26"
EXTENDS = A3025.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T279_ARCH_V3_0_26"
INPUTS_SCHEMA = "URBAN_V3026_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3026_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
CLOSABLE = (VER, DC, OA)
STATE_OF = A3018.STATE_OF                # VER / DC -> SOURCE_DERIVED, OA -> PROVISIONAL
HELD = "HELD"
DROP = "HELD ON DROP"
PART = "ESTABLISHED PART + HELD"
WALL_STATUSES = CLOSABLE + (HELD, DROP, PART)
AREA_ITEMS = ("MAS.BLOCK", "ARCH.WALL_PANEL")      # m2, the same wall area (material line / geometry line)
VOLUME_ITEM = "ARCH.WALL_VOLUME"                    # m3 = m2 x t
FAMILY = {"MAS.BLOCK": "m2", "ARCH.WALL_PANEL": "m2", VOLUME_ITEM: "m3"}
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
TOL_SUM = 5e-5                            # a declared per-line figure of the merged fill (printed to 4 decimals)
TOL_M3 = 5e-6                             # m3 = m2 x t (m2 printed to 4 decimals, m3 to 6)
RULE_ID, RULE_VERSION = "R-T279-1", "T-279"

PIECES = {
    "BLOCKWORK_FILL": {
        "module": "engine/source/arch_v3026.py (the held storey / thickness blockwork lines carry the walls a "
                  "checker-merged wall-by-wall fill established: one line per status and block type of closable "
                  "walls, the parent BLANK with every held wall, drop term and held piece named)",
        "policy": "BLOCKWORK_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-60 A (block wall from the structural floor to the underside of the member over it)",
                        "Q-55 C (door height 2.20 m where no sheet prints one: ASSUMED - OWNER-APPROVED)",
                        "owner BLOCKWORK rule 2026-10-23 (every wall whose class rises is re-measured by the Checker)",
                        "owner 2026-10-22 16:35 (statuses per quantity; a system stays PARTIALLY VERIFIED)",
                        "owner 2026-10-24 10:56 (held BLANK in the BOQ)", "UP-QTY-STATUS-001 (held never 0)",
                        "R-T261-1 points 8 / 9 (each wall once; each opening once by id)", "R-T333-1 (the fill)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "the owner's manual method measures a block wall by its length x one storey height less "
                               "its openings (one height per storey, parapets in the 15 cm section): kept beside in the "
                               "package, never used",
        "drawing_method": "per wall: drawn face length x height from the structural floor to the soffit of the drawn "
                          "member over it, piece by piece along the wall, less each opening built into it once by id; "
                          "a piece with no drawn / printed top is HELD by name; a wall under a sunken panel of unknown "
                          "drop d is U - L x d (never evaluated); m3 = m2 x the wall thickness"},
}
WAITING = dict(A3025.WAITING)
WAITING.update({
    "BLOCKWORK_HELD_WALLS": "the walls still HELD (no member drawn over them, held strips, annex datum Q-54 B, "
                            "unlabelled bands D-04 / Q-61 C(4)): BLANK on their parent lines by name",
    "BLOCKWORK_DROP_D": "the walls under the six sunken panels (D-41): U - L x d per wall, never evaluated, until the "
                        "drop d is printed / answered",
    "BLOCKWORK_PROCUREMENT": "block units and mortar from the net areas: PROVISIONAL (T-176, supplier dimensions), not "
                             "a line in this version",
    "MASONRY_ACCESSORIES": "mesh strip, sharmat ties, plaster joint mesh: separate optional items (owner 2026-10-29), "
                           "T-363 after T-362",
    "PARAPET_BLOCK_ALTERNATIVE": "parapet blockwork 0 .. 60.5965 m2 (Q-65 C material HELD): in no masonry line, "
                                 "exclusive with its RC twin (T-319), never 0",
})


# ================================================================================================ inputs
def _wall_status(w, where):
    st = w.get("status")
    if st not in WALL_STATUSES:
        raise InputsError(f"{where}: status {st!r} not one of {WALL_STATUSES}")
    c = w.get("carried")
    if st in (HELD, DROP):
        if c is not None:
            raise InputsError(f"{where}: a {st} wall carries no figure ({c!r}): BLANK in the BOQ, never 0; a drop "
                              "term is never evaluated")
        if not w.get("held_item"):
            raise InputsError(f"{where}: a {st} wall names the item that holds it")
        if st == DROP:
            u, k = w.get("upper_at_d0"), w.get("drop_coefficient")
            if not (_num(u) and u > 0 and _num(k) and k > 0):
                raise InputsError(f"{where}: a drop wall carries its terms U > 0 and L > 0 (U - L x d)")
        return None
    if not (_num(c) and c > 0):
        raise InputsError(f"{where}: a released wall carries > 0 (a missing wall is HELD, never 0)")
    ps = w["part_status"] if st == PART else st
    if st == PART:
        if ps not in CLOSABLE:
            raise InputsError(f"{where}: the established part of a held wall needs its own status {CLOSABLE}")
        if not w.get("held_item"):
            raise InputsError(f"{where}: a part-established wall names its held piece")
    if ps == VER and not w.get("verified_by"):
        raise InputsError(f"{where}: VERIFIED names the checker run that re-measured the wall")
    if ps == OA and not w.get("owner_source"):
        raise InputsError(f"{where}: ASSUMED - OWNER-APPROVED names its answered owner decision (WORKFLOW_CONTROLS s.4)")
    if not w.get("block_type"):
        raise InputsError(f"{where}: a released wall names its block type (census)")
    return ps


def load_inputs(doc, project_id=None):
    """URBAN_V3026_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}], "fill_task",
         "lines": [{line_id, item_code, unit, floor, family (thickness m), element_id,
                    before {evidence_state, measured_net},
                    walls [{wall_id, block_type, status, carried | None, part_status, verified_by, owner_source,
                            held_item, upper_at_d0, drop_coefficient, conflict, conflict_increment_outside,
                            openings}],
                    declared {verified, drawing_confirmed, owner_approved, established_parts, drop_upper_at_d0,
                              drop_coefficient}}]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged fill the walls come from")
    for s in srcs:
        A3018._source(s, "sources")
    if doc.get("fill_task") not in {s["task"] for s in srcs}:
        raise InputsError(f"fill_task {doc.get('fill_task')!r} is not a source")
    lines = doc.get("lines") or []
    if not lines:
        raise InputsError("no lines")
    seen_l, seen_w, by_key = set(), {}, {}
    for ln in lines:
        lid = ln.get("line_id")
        w0 = f"line {lid}"
        for k in ("line_id", "item_code", "unit", "floor", "element_id"):
            if not ln.get(k):
                raise InputsError(f"{w0}: {k} required")
        if lid in seen_l:
            raise InputsError(f"{w0}: named twice (one record per line)")
        seen_l.add(lid)
        if FAMILY.get(ln["item_code"]) != ln["unit"]:
            raise InputsError(f"{w0}: item {ln['item_code']} {ln['unit']} is not a blockwork line {FAMILY}")
        t = ln.get("family")
        if not (_num(t) and 0.05 <= t <= 0.60):
            raise InputsError(f"{w0}: wall thickness {t!r} m (mm, a typo or missing)")
        b = ln.get("before") or {}
        if b.get("evidence_state") != "BLOCKED_RFI" or b.get("measured_net", 0) is not None:
            raise InputsError(f"{w0}: the fill replaces a HELD blank line (a line with a figure is corrected by a "
                              "rebase, not filled: a part released inside a parent with a figure is a double count)")
        key = (ln["floor"], round(t, 3))
        if (key, ln["item_code"]) in by_key:
            raise InputsError(f"{w0}: storey / thickness {key} named twice for {ln['item_code']}")
        by_key[(key, ln["item_code"])] = ln
        walls = ln.get("walls") or []
        if not walls:
            raise InputsError(f"{w0}: no walls")
        tot = {VER: 0.0, DC: 0.0, OA: 0.0, "parts": 0.0, "U": 0.0, "L": 0.0}
        for w in walls:
            wid = w.get("wall_id")
            where = f"{w0} wall {wid}"
            if not wid:
                raise InputsError(f"{w0}: every wall has an id")
            prev = seen_w.get((ln["item_code"], wid))
            if prev is not None:
                raise InputsError(f"{where}: also in line {prev} ({ln['item_code']}): one line per wall per item")
            seen_w[(ln["item_code"], wid)] = lid
            ps = _wall_status(w, where)
            if ps is None:
                if w["status"] == DROP:
                    tot["U"] += w["upper_at_d0"]
                    tot["L"] += w["drop_coefficient"]
            elif w["status"] == PART:
                tot["parts"] += w["carried"]
            else:
                tot[ps] += w["carried"]
        dec = ln.get("declared") or {}
        for k, name in ((VER, "verified"), (DC, "drawing_confirmed"), (OA, "owner_approved"),
                        ("parts", "established_parts"), ("U", "drop_upper_at_d0"), ("L", "drop_coefficient")):
            d = dec.get(name)
            if not _num(d) or abs(d - tot[k]) > TOL_SUM:
                raise InputsError(f"{w0}: declared {name} {d!r} != the walls' {round(tot[k], 6)} (the merged fill's "
                                  "per-line figure is reproduced, wall by wall)")
    _cross_items(by_key)
    return doc


def _cross_items(by_key):
    """the three items of one storey / thickness carry the same walls at the same statuses; WALL_PANEL m2 = MAS.BLOCK
    m2 and WALL_VOLUME m3 = MAS.BLOCK m2 x t, wall by wall."""
    for (key, code), ln in by_key.items():
        if code == "MAS.BLOCK":
            continue
        blk = by_key.get((key, "MAS.BLOCK"))
        if blk is None:
            raise InputsError(f"line {ln['line_id']}: no MAS.BLOCK line for storey / thickness {key}")
        bw = {w["wall_id"]: w for w in blk["walls"]}
        if set(bw) != {w["wall_id"] for w in ln["walls"]}:
            raise InputsError(f"line {ln['line_id']}: its walls are not the MAS.BLOCK line's {blk['line_id']}")
        for w in ln["walls"]:
            o = bw[w["wall_id"]]
            if (w["status"], w.get("part_status")) != (o["status"], o.get("part_status")):
                raise InputsError(f"line {ln['line_id']} wall {w['wall_id']}: status differs from MAS.BLOCK")
            if w.get("carried") is None:
                continue
            want = o["carried"] * (key[1] if code == VOLUME_ITEM else 1.0)
            if abs(w["carried"] - want) > (TOL_M3 if code == VOLUME_ITEM else TOL):
                raise InputsError(f"line {ln['line_id']} wall {w['wall_id']}: {w['carried']} {ln['unit']} is not the "
                                  f"MAS.BLOCK {o['carried']} m2" + (f" x t {key[1]}" if code == VOLUME_ITEM else ""))


def _src_of(doc):
    return A3018._src_of(doc, doc["fill_task"])


# ================================================================================================ lines
def _slug(s):
    return A3018._slug(s)


def part_name(status, block_type):
    return f"{status} {block_type}"


def part_element_id(parent_element_id, part):
    return f"{parent_element_id}#BLOCKWORK:{_slug(part)}"


def parts_of(rec):
    """-> {part name: {status, block_type, value, pieces}} in a stable order (status strength, then type)."""
    out = {}
    for w in rec["walls"]:
        if w["status"] in (HELD, DROP):
            continue
        st = w["part_status"] if w["status"] == PART else w["status"]
        name = part_name(st, w["block_type"])
        p = out.setdefault(name, {"part": name, "status": st, "block_type": w["block_type"], "value": 0.0,
                                  "pieces": []})
        p["value"] += w["carried"]
        p["pieces"].append({"id": w["wall_id"], "value": _r(w["carried"]), "status": st,
                            "kind": "ESTABLISHED_PART" if w["status"] == PART else "WHOLE",
                            "block_type": w["block_type"], "verified_by": w.get("verified_by"),
                            "owner_source": w.get("owner_source"), "openings": w.get("openings")})
    order = {VER: 0, DC: 1, OA: 2}
    return dict(sorted(out.items(), key=lambda kv: (order[kv[1]["status"]], kv[1]["block_type"])))


def held_of(rec):
    """the parent's named held items: held walls, drop terms, held pieces of part walls, conflict increments."""
    out = []
    for w in rec["walls"]:
        if w["status"] == HELD:
            out.append({"wall": w["wall_id"], "kind": "HELD_WALL", "item": w["held_item"]})
        elif w["status"] == DROP:
            out.append({"wall": w["wall_id"], "kind": "DROP", "item": w["held_item"],
                        "terms": f"{_r(w['upper_at_d0'], 4)} - {_r(w['drop_coefficient'], 4)} d",
                        "upper_at_d0": w["upper_at_d0"], "drop_coefficient": w["drop_coefficient"]})
        elif w["status"] == PART:
            out.append({"wall": w["wall_id"], "kind": "HELD_PIECE", "item": w["held_item"]})
        if w.get("conflict_increment_outside"):
            out.append({"wall": w["wall_id"], "kind": "CONFLICT_INCREMENT_OUTSIDE",
                        "item": f"{w['conflict_increment_outside']} {rec['unit']} by name, never added, never 0"})
    return out


def _rec(src, **kw):
    return dict({"policy": PIECES["BLOCKWORK_FILL"]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION}, **kw)


def part_line(parent, rec, p, src):
    """the line of one (status, block type) group of closable walls: the parent's identity / documents / item, its own
    element id (parent element + part), its own status."""
    from engine.source import boq_line as BL
    pr = parent["project"]
    loc = parent["location"]
    st = p["status"]
    eid = part_element_id(loc.get("element_id"), p["part"])
    lrec = _rec(src, action="PART", parent_line_id=parent["line_id"], part=p["part"], status=st, evidence_status=st,
                block_type=p["block_type"], thickness_m=rec["family"], value=_r(p["value"]),
                pieces=copy.deepcopy(p["pieces"]), release_status="NOT RELEASED")
    terms = " + ".join(f"{x['id']}{' (part)' if x['kind'] == 'ESTABLISHED_PART' else ''} {x['value']}"
                       for x in p["pieces"])
    formula = f"{terms} = {_r(p['value'], 6)} {parent['unit']} ({st}, {p['block_type']} t {rec['family']} m)"
    owner = sorted({x["owner_source"] for x in p["pieces"] if x.get("owner_source")})
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=parent["item_code"], unit=parent["unit"], evidence_state=STATE_OF[st],
                      measured_net=_r(p["value"]), element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                      room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                      physical_element=f"block walls t {rec['family']} m: {p['part']}", formula=formula[:700],
                      inputs={"blockwork_fill_v3026": lrec},
                      documents=copy.deepcopy(parent["source"]["documents"]),
                      geometry_source=parent["source"]["geometry_source"],
                      geometry_confidence="TOLERANCE_CERTIFIED" if st in (VER, DC) else "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=parent["material_state"],
                      notes=(f"{METHOD}: {len(p['pieces'])} wall(s) of held line {parent['line_id']} ({src['task']} "
                             f"MERGED {src['merge_commit'][:8]}): {st}"
                             + (f" ({'; '.join(owner)})" if st == OA else "")
                             + (" (each wall re-measured by the Checker: verified_by per wall)" if st == VER else ""))
                      [:600],
                      subtrade=parent.get("subtrade"), item_en=parent.get("item_en"), item_ar=parent.get("item_ar"),
                      trade=parent.get("trade"))
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln), lrec


def parent_line(parent, rec, src, part_ids):
    """the parent in place: BLANK, its held walls / drop terms / held pieces named and the part lines listed."""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(parent)
    held = held_of(rec)
    groups = {}
    for h in held:   # every held item by id in the question (complete); its full text in the inputs record
        groups.setdefault(h["kind"], []).append(h["wall"] + (f" {h['terms']}" if h.get("terms") else ""))
    htxt = "; ".join(f"{k}: {', '.join(v)}" for k, v in groups.items())
    q = (f"HELD walls / pieces (blank, never 0; drop terms never evaluated; each item's reason in "
         f"calculation.inputs.blockwork_fill_v3026.still_held): {htxt}")
    if len(q) > 900:
        raise ValueError(f"{METHOD}: the held list of {parent['line_id']} does not fit the RFI question ({len(q)} > 900)")
    carried = "; ".join(f"{k} on {v}" for k, v in part_ids.items())
    ln["evidence_state"] = "BLOCKED_RFI"
    ln["measured_net"] = None
    ln["bounded_range"] = None
    ln["rfi"] = {"question": q, "unlocks": ln["location"].get("element_id")}
    ln["calculation"]["formula"] = (f"HELD remainder (blank in the BOQ, never 0): {len(held)} named item(s)"
                                    + (f" | closable walls carried on their own lines: {carried}" if part_ids else
                                       " | no closable wall in this line"))[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, blockwork_fill_v3026=_rec(
        src, action="PARENT" if part_ids else "RESTATE", before=A3018._before_rec(parent), thickness_m=rec["family"],
        still_held=held, parts=dict(part_ids)))
    A305._note(ln, f"{METHOD}: held remainder of the blockwork fill ({src['task']} MERGED {src['merge_commit'][:8]}); "
                   + ("its closable walls are their own lines; " if part_ids else "") + "blank in the BOQ, never 0")
    return BL.validate(ln)


def _assert_before(b, rec):
    if b is None:
        raise InputsError(f"line {rec['line_id']}: the candidate does not carry this line (stale fill)")
    if (b["item_code"], b["unit"], b["location"].get("floor"), b["location"].get("element_id")) != \
            (rec["item_code"], rec["unit"], rec["floor"], rec["element_id"]):
        raise InputsError(f"line {rec['line_id']}: item / unit / storey / element is not the line's")
    if b["evidence_state"] != "BLOCKED_RFI" or b.get("measured_net") is not None or b.get("bounded_range"):
        raise InputsError(f"line {rec['line_id']}: the candidate line is {b['evidence_state']} "
                          f"{b.get('measured_net')}, not the HELD blank the fill was made on (stale fill: refused)")
    if (b.get("calculation") or {}).get("inputs", {}).get("blockwork_fill_v3026"):
        raise InputsError(f"line {rec['line_id']}: already filled (the fill is applied once)")


def changes_for(doc, l3025):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "BLOCKWORK_FILL", "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3025}
    src = _src_of(doc)
    ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
           "ledger": src["file"], "ledger_sha256": src["sha256"]}
    changes, seen_ids = [], set(by)
    log = {"piece": "BLOCKWORK_FILL", "state": "RUN", "sources": doc["sources"], "by_item": {}, "lines": {}}
    for rec in doc["lines"]:
        b = by.get(rec["line_id"])
        _assert_before(b, rec)
        parts = parts_of(rec)
        pids, adds = {}, []
        for name, p in parts.items():
            pl, lrec = part_line(b, rec, p, src)
            if pl["line_id"] in seen_ids:
                raise ValueError(f"{METHOD}: part {name} of {b['line_id']} repeats a line id")
            seen_ids.add(pl["line_id"])
            pids[name] = pl["line_id"]
            adds.append((p, pl))
        after = parent_line(b, rec, src, pids)
        held = held_of(rec)
        changes.append(A305._change("BLOCKWORK_FILL", "REPLACE", b, after, drawing_reference=src["file"],
                                    held=[{"what": f"{rec['item_code']} {rec['element_id']}: {h['wall']}",
                                           "why": f"{h['kind']}: {h['item']}"[:300], "range": None,
                                           "scenario": h.get("terms")} for h in held],
                                    downstream=[], verification=ver,
                                    evidence_status="HELD (remainder of the fill)",
                                    codes=["BLOCKWORK_FILL", "PARENT" if pids else "RESTATE"], group=rec["item_code"]))
        for p, pl in adds:
            changes.append(A305._change("BLOCKWORK_FILL", "ADD", None, pl, drawing_reference=src["file"], held=[],
                                        downstream=[], verification=dict(ver, walls=[x["id"] for x in p["pieces"]]),
                                        evidence_status=p["status"], codes=["BLOCKWORK_FILL", "PART"],
                                        group=rec["item_code"], parent_line_id=b["line_id"]))
        k = f"{rec['item_code']} {rec['unit']}"
        g = log["by_item"].setdefault(k, {VER: 0.0, DC: 0.0, OA: 0.0, "lines_added": 0, "held_items": 0})
        for p in parts.values():
            g[p["status"]] = _r(g[p["status"]] + p["value"])
        g["lines_added"] += len(parts)
        g["held_items"] += len(held)
        log["lines"][rec["line_id"]] = {"parts": {k2: _r(v["value"]) for k2, v in parts.items()},
                                        "held": len(held), "part_line_ids": pids}
    return changes, log


# ================================================================================================ integrate / write
def check_blockwork(lines):
    """on finished lines: every part names a held blank parent that names it; a wall released once per item; one
    status and one block type per part; MAS.BLOCK and WALL_PANEL parts equal, WALL_VOLUME = m2 x t. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    seen, out = set(), {"part_lines": 0, "parents": 0, "released": {}}
    groups = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("blockwork_fill_v3026") or {}
        if rec.get("action") in ("PARENT", "RESTATE"):
            out["parents"] += 1
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: parent {ln['line_id']} carries a figure (held is BLANK)")
            continue
        if rec.get("action") != "PART":
            continue
        out["part_lines"] += 1
        par = by.get(rec.get("parent_line_id"))
        if par is None:
            raise ValueError(f"{METHOD}: part {ln['line_id']} names a parent the run does not carry")
        if par["evidence_state"] != "BLOCKED_RFI" or par.get("measured_net") is not None or par.get("bounded_range"):
            raise ValueError(f"{METHOD}: part {ln['line_id']} released while its parent carries a figure (double count)")
        prec = ((par.get("calculation") or {}).get("inputs") or {}).get("blockwork_fill_v3026") or {}
        if ln["line_id"] not in (prec.get("parts") or {}).values():
            raise ValueError(f"{METHOD}: parent {par['line_id']} does not name its part {ln['line_id']}")
        if ln["evidence_state"] != STATE_OF[rec["status"]] or not (ln.get("measured_net") or 0) > 0:
            raise ValueError(f"{METHOD}: part {ln['line_id']} state {ln['evidence_state']} / {ln.get('measured_net')}")
        s = 0.0
        for p in rec["pieces"]:
            if p["status"] != rec["status"] or p["block_type"] != rec["block_type"]:
                raise ValueError(f"{METHOD}: part {ln['line_id']}: wall {p['id']} is {p['status']} {p['block_type']}")
            k = (ln["item_code"], p["id"])
            if k in seen:
                raise ValueError(f"{METHOD}: wall {p['id']} released twice in {ln['item_code']}")
            seen.add(k)
            s += p["value"]
        if abs(s - ln["measured_net"]) > TOL_SUM:
            raise ValueError(f"{METHOD}: part {ln['line_id']} {ln['measured_net']} != its walls {_r(s)}")
        groups[(ln["location"].get("floor"), rec["thickness_m"], rec["part"], ln["item_code"])] = ln["measured_net"]
        kk = f"{ln['item_code']} {ln['unit']} {rec['status']}"
        out["released"][kk] = _r(out["released"].get(kk, 0.0) + ln["measured_net"])
    for (fl, t, part, code), v in groups.items():
        if code == "MAS.BLOCK":
            continue
        m = groups.get((fl, t, part, "MAS.BLOCK"))
        if m is None:
            raise ValueError(f"{METHOD}: {code} part {fl} {t} {part} has no MAS.BLOCK twin")
        want = m * (t if code == VOLUME_ITEM else 1.0)
        if abs(v - want) > (TOL_SUM * max(1.0, t * 10) if code == VOLUME_ITEM else TOL):
            raise ValueError(f"{METHOD}: {code} part {fl} {t} {part} {v} != MAS.BLOCK {m}"
                             + (f" x {t}" if code == VOLUME_ITEM else ""))
    out["released"] = dict(sorted(out["released"].items()))
    return out


def integrate(l3025, changes, for_lead=()):
    """-> (V3.0.26 lines, identity). Every line outside the V3.0.26 rows is byte-identical to the V3.0.25 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3025}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != "BLOCKWORK_FILL":
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only fills the blockwork lines)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.25, or its id changed")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid or c["after"]["item_code"] not in FAMILY:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.25 line id or is not a blockwork item")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3025] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    tile = A3021.check_tile_family(out)
    par = A3023.check_parapet_family(out)
    state = A3024.check_line_state(out, for_lead)
    outdoor = A3025.check_outdoor_family(out)
    blk = check_blockwork(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by25 = {ln["line_id"]: ln for ln in l3025}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by25[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3025):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.26 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by25[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_25_lines": len(l3025), "v3_0_26_lines": len(out), "v3_0_26_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_25": len(outside), "blockwork": blk, "outdoor_family": outdoor,
             "parapet_family": par, "wall_tile_family": tile, "line_state": state,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"]["blockwork_fill_v3026"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "action": rec["action"], "line_id": ref["line_id"],
                     "parent_line_id": rec.get("parent_line_id"), "item_code": ref["item_code"],
                     "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "thickness_m": rec.get("thickness_m"), "part": rec.get("part"),
                     "block_type": rec.get("block_type"),
                     "before_released_v2_9": b29,
                     "before_v3_0_25": (A30._qty(c["before"]) if c["before"] is not None else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_25")),
                     "after_v3_0_26": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "walls": [p["id"] for p in rec.get("pieces") or ()],
                     "pieces": rec.get("pieces"), "still_held": rec.get("still_held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES["BLOCKWORK_FILL"]["owner_manual_method"],
                     "drawing_derived_method": PIECES["BLOCKWORK_FILL"]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "parent_line_id", "item_code", "floor", "element_id", "unit",
              "thickness_m", "part", "v2_9", "v3_0_25", "v3_0_26", "evidence_status", "walls", "held", "verification")
WALLS_CSV = ("line_id", "item_code", "unit", "floor", "thickness_m", "wall_id", "block_type", "status", "part_status",
             "carried", "carried_on_line", "held_item", "drop_terms", "verified_by", "owner_source", "openings")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_25", "vs_released_v2_9", "v2_9",
            "v3_0_25", "v3_0_26")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "parent_line_id": r["parent_line_id"] or "", "item_code": r["item_code"], "floor": r["floor"],
                       "element_id": r["element_id"], "unit": r["unit"], "thickness_m": r["thickness_m"],
                       "part": r["part"] or "", "v2_9": _fmt_q(r["before_released_v2_9"]),
                       "v3_0_25": _fmt_q(r["before_v3_0_25"]), "v3_0_26": _fmt_q(r["after_v3_0_26"]),
                       "evidence_status": r["evidence_status"], "walls": " ".join(r["walls"]),
                       "held": "; ".join(f"{h['wall']} {h['kind']}" + (f" {h['terms']}" if h.get("terms") else "")
                                         for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       .strip()} for r in rows], LEDGER_CSV)


def walls_csv(doc, changes):
    on = {}
    for c in changes:
        rec = c["after"]["calculation"]["inputs"]["blockwork_fill_v3026"]
        for p in rec.get("pieces") or ():
            on[(c["after"]["item_code"], p["id"])] = c["after"]["line_id"]
    rows = []
    for ln in doc["lines"]:
        for w in ln["walls"]:
            rows.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
                         "floor": ln["floor"], "thickness_m": ln["family"], "wall_id": w["wall_id"],
                         "block_type": w.get("block_type") or "", "status": w["status"],
                         "part_status": w.get("part_status") or "",
                         "carried": "" if w.get("carried") is None else _r(w["carried"]),
                         "carried_on_line": on.get((ln["item_code"], w["wall_id"]), ""),
                         "held_item": str(w.get("held_item") or "")[:300],
                         "drop_terms": (f"{w['upper_at_d0']} - {w['drop_coefficient']} d" if w["status"] == DROP
                                        else ""),
                         "verified_by": str(w.get("verified_by") or "")[:160],
                         "owner_source": str(w.get("owner_source") or "")[:200],
                         "openings": str(w.get("openings") or "")[:300]})
    return A305._csv(rows, WALLS_CSV)


def diff_rows(l3025, l3026, released_lines=None):
    b25 = {ln["line_id"]: ln for ln in l3025}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3026:
        o = b25.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_25": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_25": A302._q(A30._qty(o)) if o else "", "v3_0_26": A302._q(A30._qty(ln))})
    return out


def write(out, l3025, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_26_* files beside the V3_0_25_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3026, ident = integrate(l3025, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3025, l3026, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_25", {}).setdefault(d["vs_v3_0_25"], 0)
        dsum["vs_v3_0_25"][d["vs_v3_0_25"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t25, t26 = A304.code_totals(l3025), A304.code_totals(l3026)
    moved = {k: {"v3_0_25": t25.get(k), "v3_0_26": t26.get(k)} for k in sorted(set(t25) | set(t26))
             if t25.get(k) != t26.get(k)}
    if any(not any(str(k).startswith(c) for c in FAMILY) for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the blockwork family: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_26_BOQ_LINES.json": BL.dumps(l3026),
             "V3_0_26_BOQ_LINES.csv": A30._lines_csv(l3026),
             "V3_0_26_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_26_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_26_WALLS.csv": walls_csv(doc, changes),
             "V3_0_26_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_26_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(FAMILY)}


__all__ = ["METHOD", "PIECES", "WAITING", "FAMILY", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "parts_of",
           "held_of", "part_line", "parent_line", "changes_for", "check_blockwork", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError"]
