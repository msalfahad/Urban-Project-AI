"""ARCH_TAKEOFF_V3.0.37 (T-420): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.36 (engine.source.arch_v30,
arch_v301 .. arch_v3036), extended with the BOQ category the candidate lacked (registry family B3-05 'screed / build-up'):

  FLOOR_BED  the cement-sand layer laid on the structural slab (dry room) or on the membrane (wet room) under the floor
             finish of ONE room, one bed per valued floor-finish line, bound to that line by id, from the Checker-merged
             T-414 room table (FLOOR_BED_V1, MERGED 4f81eda1) with the Checker's drawing bound (F-C-T414-1):

    BED_M2   a NEW m2 line: the bed area = the bound floor-finish line's net (the same line state, the same area
             evidence: DRAWING-CONFIRMED, or ASSUMED - OWNER-APPROVED where the finish area is PROVISIONAL);
    BED_M3   a NEW m3 line, BOUNDED_EXPOSURE (a range, never a chosen value): the INSTALLED bed volume as the owner's
             Q-45 range (dry 0.03 .. 0.04 m, wet 0.04 .. 0.06 m x the area, ASSUMED - OWNER-APPROVED); the
             drawing-derived bound (area x 0 .. b of the room's OWN zone; the tile thickness is printed nowhere, so the
             drawn layer stays HELD inside its bound; a wet / sunken room has no drawn b: HELD, no bound) is carried
             BESIDE in the calculation record, never as the line figure. The two lines are one measure pair: price ONE
             basis (m2 or m3), never both;
    NOT_APPLICABLE  (no line) a floor-finish line that states 'no finish here' with evidence (doorway strips, the
             pantry face) carries no bed: recorded by id, never a held 0.

The physical element (ERS 2026-10-22 s.2.1, s.3; ELEMENT_REGISTER 'FLOOR BUILD-UP LAYER' 2026-11-01 00:18): one bed per
room, owner trade FINISHES (B3-05). Contract form by owner Q-41: dry and wet rooms a MORTAR_BED (a wet room's bed is the
only layer over its membrane, no falls / protection screed line), balconies a SCREED (none on a villa without one); roofs
and terraces belong to the roof build-up (B13-01), stairs to the stair bed (B7), the pool to T-309, foundations to
T-219 / T-353, outdoor ground paving to B13-02, the wet-room membrane to B8-01 .. B8-03 (a different layer). Installed
volume only: cement bags, sand and waste are the procurement view (finish_materials_table, T-086), never mixed in.

Every candidate floor-finish line (FIN.FLOOR.PORCELAIN / FIN.FLOOR.WET_TILE) must be named by the inputs (BED or
NOT_APPLICABLE), and every bound line must stand as the merged table read it (item, element, state, net to the table's
4 decimals): else stop (stale binding). A space with no floor-finish line gets no bed ahead of it (register 'ROOM WITH NO
FLOOR-FINISH LINE'). Every V3.0.36 line is byte-identical in V3.0.37 (this package only ADDS lines; asserted); totals
move only in the two new codes (asserted). Files: V3_0_37_BOQ_LINES.json / .csv, V3_0_37_INTEGRATION_LEDGER.json / .csv,
V3_0_37_DIFF.csv, V3_0_37_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.

R-T420-1 (every villa; integrates R-T414-1): a B3-05 bed line exists only beside a valued floor-finish line and is bound
to it by id (one bed per finish line; none on a NOT_APPLICABLE finish; none on a space without a finish line); its m2 is
that line's net; its installed m3 is the owner's range (ASSUMED - OWNER-APPROVED) with the drawing bound of the room's
own zone beside (an UPPER bound takes the upper end of a drawn range, F-C-T414-1); a wet / sunken room never takes the
dry b; a roof / terrace / stair / pool / foundation / outdoor floor is never a B3-05 row; held is never 0; m2 and m3 are
one measure pair (price one basis).
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
from engine.source import arch_v3036 as A3036

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books a checker-merged ledger; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.37"
EXTENDS = A3036.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T420_ARCH_V3_0_37"
INPUTS_SCHEMA = "URBAN_V3037_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3037_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T420-1", "T-420"
PIECE = "FLOOR_BED"
FAMILY = "B3-05"
REC_KEY = "floor_bed_v3037"
ACTIONS = ("BED", "NOT_APPLICABLE")
KINDS = ("DRY", "WET")                     # BALCONY (SCREED) has no owner thickness: no balcony row is valued here
OWNED_ELSEWHERE = ("ROOF", "TERRACE", "STAIR", "POOL", "FOUNDATION", "OUTDOOR_GROUND", "BALCONY")
FINISH_CODES = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
AREA_STATUS = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "VERIFIED")
OWNER_STATUS = "ASSUMED — OWNER-APPROVED"
LEDGER_TOL = 0.00006                       # the merged table prints 4 decimals
BED_DRY, BED_WET = "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET"
NEW_ITEMS = {   # en, ar, trade, subtrade
    BED_DRY: ("Floor cement-sand bed under the floor finish, dry rooms (B3-05; installed)",
              "مدة أسمنتية تحت تشطيب الأرضيات - الغرف الجافة", "FLOOR_FINISH", "FLOOR_BED"),
    BED_WET: ("Floor cement bed under the tiles, wet rooms (bartash; over the membrane; B3-05; installed)",
              "مدة أسمنتية (برطاش) تحت بلاط المناطق الرطبة", "FLOOR_FINISH", "FLOOR_BED"),
}
CODE = {"DRY": BED_DRY, "WET": BED_WET}
ROW_UNITS = ("m2", "m3")

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3037.py (B3-05 floor bed per valued floor-finish line, bound by id, from the "
                  "Checker-merged T-414 room table: m2 = the finish net, installed m3 = the owner Q-45 range with "
                  "the drawing bound of the room's own zone beside (F-C-T414-1 upper end); doorway strips / pantry "
                  "face NOT_APPLICABLE by id; no other line moves)",
        "policy": "FLOOR_BED_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-41 (owner 2026-10-19 20:45: roofs / balconies a screed; bathrooms a cement bed only)",
                        "Q-45 (owner 2026-10-19 21:40: regular floors 3-4 cm, wet floors / bartash 4-6 cm, every bed "
                        "a range, never one invented number; adhesive up to 3 mm its own item)",
                        "Q-30 A (a room wholly under the membrane is wet)", "Q-37 A (the pantry part is wet)",
                        "UP-QTY-STATUS-001 (held is blank, never 0)",
                        "R-T414-1 (FLOOR_BED_V1; Checker addendum: a bound from a drawn range takes the range end "
                        "on the side it bounds)",
                        "ELEMENT_REGISTER 2026-11-01 00:18 FLOOR BUILD-UP LAYER / 04:15 ROOM WITH NO FLOOR-FINISH LINE",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner method per room: the tiled floor area x the Q-45 bed thickness as a range (dry "
                               "0.03 .. 0.04 m, wet 0.04 .. 0.06 m), the bed under the tile only (no screed line in "
                               "a wet room, Q-41); cement / sand / waste are the procurement view, not this line",
        "drawing_method": "the floor-finish line's net (engine room face, Checker-merged) x the layer thickness t = b "
                          "- t_finish - t_adhesive with b = FFL - structural top of the room's OWN zone (T-214, "
                          "SECTION A-A / B-B); t_finish is printed nowhere, so t is bounded 0 .. b (1F b upper end "
                          "0.051, F-C-T414-1) and stays HELD; wet / sunken rooms: b printed nowhere (D-41), HELD"},
}
WAITING = dict(A3036.WAITING)
WAITING.update({
    "T420_BED_FOLLOWS_T421": "spaces with no floor-finish line yet carry NO bed (register 'ROOM WITH NO FLOOR-FINISH "
                             "LINE'): the T-418 stair-room floor parts (GF stair hall 4.805 + 1.3225 m2, 2F lobby "
                             "2.500 m2): the bed follows T-421, which adds their floor lines and bed rows together",
    "T420_TILE_THICKNESS": "the tile / stone thickness is printed nowhere (designer item D-40): the drawn bed stays "
                           "HELD inside 0 .. b; the owner Q-45 range is the line's range",
    "T420_WET_LEVELS": "wet-room and sunken-panel levels printed nowhere (D-40 / D-41): no drawing bound for any wet "
                       "bed; the owner range stands alone",
    "T420_ADHESIVE": "tile adhesive (Q-45: up to 3 mm, 20 kg / 5 m2 per bag) is its own item, not in the bed; "
                     "procurement (cement bags, sand, waste) stays the finish_materials_table view (T-086)",
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
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    return float(x)


def load_inputs(doc, project_id=None):
    """URBAN_V3037_INPUTS_V1 -> the validated doc. {"schema", "project_id", "sources": [{"task", "file", "sha256",
    "merge_commit", "checker_run"}], "owner": {"DRY"|"WET": {"lo", "hi", "rule"}}, "b_upper": {"<zone>": {"b",
    "source"}}, "rows": [{"action": BED | NOT_APPLICABLE, "finish_line", "kind", "space_kind", "layer", "zone",
    "expect": {"item_code", "element_id", "evidence_state", "measured_net" (BED)}, "area_status", "ledger": {"m3_owner_low",
    "m3_owner_high", "b", "m3_drawing_high", "drawing_status"}, "membrane_in_room", "source_tasks"}]}"""
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
    owner = {}
    for k in KINDS:
        o = (doc.get("owner") or {}).get(k)
        if not o:
            raise InputsError(f"owner range for {k} missing (no default thickness: DEFAULTED_THICKNESS)")
        _need(o, ("rule",), f"owner {k}")
        lo, hi = _num(o.get("lo"), f"owner {k} lo", True), _num(o.get("hi"), f"owner {k} hi", True)
        if lo > hi or hi > 0.2:
            raise InputsError(f"owner {k}: {lo} .. {hi} m is not a bed range in metres")
        owner[k] = dict(o, lo=lo, hi=hi)
    bup = {}
    for z, v in (doc.get("b_upper") or {}).items():
        _need(v, ("source",), f"b_upper {z}")
        bup[z] = dict(v, b=_num(v.get("b"), f"b_upper {z}", True))
    rows, seen = [], set()
    for i, r in enumerate(doc.get("rows") or ()):
        where = f"row {i} {r.get('finish_line')}"
        if r.get("action") not in ACTIONS:
            raise InputsError(f"{where}: action {r.get('action')!r}")
        _need(r, ("finish_line",), where)
        if r["finish_line"] in seen:
            raise InputsError(f"{where}: a finish line named twice (one bed per finish line)")
        seen.add(r["finish_line"])
        if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")
        sk = r.get("space_kind") or r.get("kind")
        if sk in OWNED_ELSEWHERE:
            raise InputsError(f"{where}: OWNED_ELSEWHERE: a {sk} floor is not a B3-05 bed (one layer, one item)")
        if r.get("kind") not in KINDS:
            raise InputsError(f"{where}: kind {r.get('kind')!r} (DRY or WET)")
        e = r.get("expect") or {}
        _need(e, ("item_code", "element_id", "evidence_state"), f"{where} expect")
        if e["item_code"] not in FINISH_CODES:
            raise InputsError(f"{where}: {e['item_code']} is not a floor-finish code (OWNED_ELSEWHERE: a bed only "
                              f"under {FINISH_CODES})")
        if r["action"] == "NOT_APPLICABLE":
            if e["evidence_state"] != NA_STATE or e.get("measured_net") is not None:
                raise InputsError(f"{where}: NOT_APPLICABLE binds a {NA_STATE} finish line without a quantity")
            rows.append(dict(r))
            continue
        if e["evidence_state"] not in VALUED_STATES:
            raise InputsError(f"{where}: a bed under a {e['evidence_state']} finish line (a bed follows a valued "
                              f"finish line, never ahead of it)")
        area = e.get("measured_net")
        if isinstance(area, (int, float)) and not isinstance(area, bool) and abs(area) < 1e-9:
            raise InputsError(f"{where}: HELD_AS_ZERO: a bed area of 0 is refused")
        area = _num(area, f"{where} area", True)
        if r.get("area_status") not in AREA_STATUS:
            raise InputsError(f"{where}: area status {r.get('area_status')!r}")
        lg = r.get("ledger") or {}
        o = owner[r["kind"]]
        for k, t in (("m3_owner_low", o["lo"]), ("m3_owner_high", o["hi"])):
            v = _num(lg.get(k), f"{where} ledger {k}")
            if abs(area * t - v) > LEDGER_TOL + area * 1e-9:
                raise InputsError(f"{where}: ledger {k} {v} is not {_fmt(area)} x {t} (stale ledger)")
        b = lg.get("b")
        if r["kind"] == "WET" and b is not None:
            raise InputsError(f"{where}: STEPPED_SLAB_NOT_OWN_LEVEL: a wet room never takes a dry b ({b})")
        bh = None
        if b is not None:
            b = _num(b, f"{where} b", True)
            dh = _num(lg.get("m3_drawing_high"), f"{where} ledger m3_drawing_high")
            if abs(area * b - dh) > LEDGER_TOL + area * 1e-9:
                raise InputsError(f"{where}: ledger drawing bound {dh} is not {_fmt(area)} x {b}")
            u = bup.get(r.get("zone"))
            bh = u["b"] if u else b
            if bh < b - 1e-9:
                raise InputsError(f"{where}: an upper bound {bh} below the drawn b {b} (an upper bound takes the "
                                  f"upper end)")
        elif lg.get("m3_drawing_high") is not None:
            raise InputsError(f"{where}: a drawing bound without its b")
        rows.append(dict(r, _area=area, _b=b, _bh=bh))
    if not rows:
        raise InputsError("no row in the inputs")
    return dict(doc, _sources=srcs, _owner=owner, _b_upper=bup, _rows=rows)


# ================================================================================================ lines
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _assert_bound(b, r):
    e = r["expect"]
    if b is None:
        raise InputsError(f"finish line {r['finish_line']}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == e["item_code"] and loc.get("element_id") == e["element_id"]
          and b["evidence_state"] == e["evidence_state"])
    if ok and r["action"] == "BED":
        ok = b.get("measured_net") is not None and abs(b["measured_net"] - e["measured_net"]) <= LEDGER_TOL
    if not ok:
        raise InputsError(f"finish line {r['finish_line']}: {b['item_code']} {loc.get('element_id')} "
                          f"{b['evidence_state']} {b.get('measured_net')} is not the table's {e} (stale binding: "
                          f"re-read the line before integrating)")


def _rec(srcs, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "family": FAMILY, "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _beds(fin, r, owner, srcs):
    """-> (m2 line, m3 line) for one valued floor-finish line."""
    from engine.source import boq_line as BL
    code = CODE[r["kind"]]
    en, ar, tr, sub = NEW_ITEMS[code]
    pr, loc = fin["project"], fin["location"]
    area = fin["measured_net"]                       # the candidate's own figure (bound to the table above)
    eid = f"{loc['element_id']}:bed"
    S = "+".join(r["source_tasks"])
    o = owner[r["kind"]]
    lo, hi = _r(area * o["lo"]), _r(area * o["hi"])
    if r["_bh"] is not None:
        dbound = {"status": "HELD", "low": 0.0, "high": _r(area * r["_bh"]), "b": r["_b"], "b_upper": r["_bh"],
                  "missing": "the finish (tile / stone) thickness: printed nowhere, no owner rule (D-40)",
                  "owner_check": "CONSISTENT" if o["hi"] <= r["_bh"] + 1e-9 else "PARTLY_CONSISTENT"}
        dtext = (f"drawing bound beside, HELD: {_fmt(area)} m2 x 0 .. {_fmt(r['_bh'])} m (b of {r.get('zone')}; "
                 f"tile thickness not printed) -> 0 .. {_fmt(dbound['high'])} m3")
    else:
        dbound = {"status": "HELD", "low": None, "high": None, "b": None, "b_upper": None,
                  "missing": "the build-up b of this room's own (wet / sunken) zone: printed nowhere (D-41)",
                  "owner_check": "NOT_CHECKED (drawn build-up HELD)"}
        dtext = "drawing bound: none (the wet / sunken level is printed nowhere; HELD)"
    docs = copy.deepcopy(fin["source"]["documents"])
    common = dict(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=code,
                  element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                  room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                  physical_element=f"{r.get('layer') or 'MORTAR_BED'} under the floor finish of {loc['element_id']}",
                  documents=docs, geometry_source=fin["source"]["geometry_source"],
                  geometry_confidence=fin["source"]["geometry_confidence"], rule_id=RULE_ID,
                  rule_version=RULE_VERSION, material_state="PROJECT_OWNER_FACT", item_en=en, item_ar=ar, trade=tr,
                  subtrade=sub)
    rec2 = _rec(srcs, action="BED", unit="m2", finish_line=fin["line_id"], kind=r["kind"], layer=r.get("layer"),
                zone=r.get("zone"), area_status=r["area_status"], evidence_status=r["area_status"],
                membrane_in_room=r.get("membrane_in_room"), owner_trade="FINISHES (B3-05)")
    m2 = BL.make_line(unit="m2", evidence_state=fin["evidence_state"], measured_net=area, gross=area,
                      formula=(f"bed area = the floor-finish line {fin['line_id']} ({fin['item_code']}, "
                               f"{loc['element_id']}) net {_fmt(area)} m2 ({r['area_status']}; {S})"),
                      inputs={REC_KEY: rec2, "evidence_status": r["area_status"]},
                      notes=(f"{METHOD}: {FAMILY} bed m2, bound to {fin['line_id']}; measure pair with the m3 line: "
                             f"price ONE basis; NOT RELEASED"), **common)
    rec3 = _rec(srcs, action="BED", unit="m3", finish_line=fin["line_id"], kind=r["kind"], layer=r.get("layer"),
                zone=r.get("zone"), area_status=r["area_status"], evidence_status=OWNER_STATUS,
                owner_range={"lo_m": o["lo"], "hi_m": o["hi"], "rule": o["rule"], "low": lo, "high": hi},
                drawing_bound=dbound, membrane_in_room=r.get("membrane_in_room"), owner_trade="FINISHES (B3-05)",
                installed_not_procurement=True)
    basis = (f"owner Q-45 range {_fmt(o['lo'])} .. {_fmt(o['hi'])} m x {_fmt(area)} m2 (ASSUMED — OWNER-APPROVED); "
             f"{dtext}")[:300]
    m3 = BL.make_line(unit="m3", evidence_state="BOUNDED_EXPOSURE", measured_net=None, gross=None,
                      bounded_range={"low": lo, "high": hi, "basis": basis},
                      formula=(f"installed bed volume, a range (never one chosen value): {_fmt(area)} m2 (finish line "
                               f"{fin['line_id']}) x {_fmt(o['lo'])} .. {_fmt(o['hi'])} m (owner Q-45, ASSUMED — "
                               f"OWNER-APPROVED) -> {_fmt(lo)} .. {_fmt(hi)} m3; {dtext} ({S})")[:700],
                      inputs={REC_KEY: rec3, "evidence_status": OWNER_STATUS},
                      notes=(f"{METHOD}: {FAMILY} installed bed m3 as the owner range; procurement (bags, sand, waste) "
                             f"is not in this line; measure pair with the m2 line: price ONE basis; NOT RELEASED"),
                      **common)
    pair = {"price_one_basis": True, "lines": [m2["line_id"], m3["line_id"]], "units": ["m2", "m3"],
            "physical_item": eid, "why": "one bed, two measures: bill the m2 OR the m3, never both"}
    for ln in (m2, m3):
        ln["measure_pair"] = copy.deepcopy(pair)
        ln["project"] = copy.deepcopy(pr)
        BL.validate(ln)
    return m2, m3, dbound


def changes_for(doc, l3036):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    if any(ln["item_code"] in NEW_ITEMS or ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
           for ln in l3036):
        raise InputsError("the candidate already carries B3-05 bed lines (applied once)")
    by = {ln["line_id"]: ln for ln in l3036}
    fin_ids = {ln["line_id"] for ln in l3036 if ln["item_code"] in FINISH_CODES}
    named = {r["finish_line"] for r in doc["_rows"]}
    if fin_ids - named:
        raise InputsError(f"{len(fin_ids - named)} floor-finish line(s) not named by the table (stale ledger: "
                          f"{sorted(fin_ids - named)[:3]}): every finish line gets a bed row or NOT_APPLICABLE")
    S = doc["_sources"]
    changes, records, seen = [], [], set(by)
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines_added": 0,
           "by_kind": {}, "not_applicable": []}
    for r in doc["_rows"]:
        b = by.get(r["finish_line"])
        _assert_bound(b, r)
        srcs = [S[t] for t in r["source_tasks"]]
        log["by_action"][r["action"]] = log["by_action"].get(r["action"], 0) + 1
        if r["action"] == "NOT_APPLICABLE":
            records.append({"version": METHOD, "piece": PIECE, "action": "NOT_APPLICABLE", "family": FAMILY,
                            "finish_line": b["line_id"], "item_code": b["item_code"],
                            "element_id": b["location"].get("element_id"), "floor": b["location"].get("floor"),
                            "evidence_status": "NOT_APPLICABLE", "lines_added": 0,
                            "why": "the finish line states no floor finish here with evidence: no bed (never a held 0)",
                            "verification": _ver(srcs), "release_status": "NOT RELEASED"})
            log["not_applicable"].append(b["line_id"])
            continue
        m2, m3, dbound = _beds(b, r, doc["_owner"], srcs)
        for ln in (m2, m3):
            if ln["line_id"] in seen:
                raise ValueError(f"{METHOD}: added bed line {ln['location']['element_id']} repeats an id")
            seen.add(ln["line_id"])
        common = dict(drawing_reference="; ".join(s["file"] for s in srcs), downstream=[],
                      verification=_ver(srcs), group=m2["item_code"])
        changes.append(A305._change(PIECE, "ADD", None, m2, held=[], evidence_status=r["area_status"],
                                    codes=[PIECE, "BED_M2"], bound_to=b["line_id"], **common))
        held = [{"what": f"{m3['item_code']} {m3['location']['element_id']} drawn layer",
                 "why": dbound["missing"][:300], "range": ([dbound["low"], dbound["high"]]
                                                           if dbound["high"] is not None else None),
                 "scenario": "drawing bound beside the owner range"}]
        changes.append(A305._change(PIECE, "ADD", None, m3, held=held, evidence_status=OWNER_STATUS,
                                    codes=[PIECE, "BED_M3"], bound_to=b["line_id"], drawing_bound=dbound, **common))
        log["lines_added"] += 2
        k = log["by_kind"].setdefault(r["kind"], {"rows": 0, "m2": 0.0, "m3_owner_low": 0.0, "m3_owner_high": 0.0,
                                                  "m3_drawing_bound_high": 0.0, "rows_with_drawing_bound": 0,
                                                  "rows_area_owner_approved": 0})
        k["rows"] += 1
        k["m2"] = _r(k["m2"] + m2["measured_net"])
        k["m3_owner_low"] = _r(k["m3_owner_low"] + m3["bounded_range"]["low"])
        k["m3_owner_high"] = _r(k["m3_owner_high"] + m3["bounded_range"]["high"])
        if dbound["high"] is not None:
            k["m3_drawing_bound_high"] = _r(k["m3_drawing_bound_high"] + dbound["high"])
            k["rows_with_drawing_bound"] += 1
        if r["area_status"] == OWNER_STATUS:
            k["rows_area_owner_approved"] += 1
    log["by_action"] = dict(sorted(log["by_action"].items()))
    log["by_kind"] = dict(sorted(log["by_kind"].items()))
    log["records"] = records
    return changes, log


# ================================================================================================ integrate / write
def check_beds(lines):
    """on finished lines: every B3-05 bed line is of this piece; one m2 + one m3 per bed element, a measure pair of
    each other; the m2 equals its bound finish line's net, the m3 is a range (BOUNDED_EXPOSURE, no value, no gross);
    every bound finish line is a valued floor-finish line; no bed on a NOT_APPLICABLE / held finish. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"beds": 0, "lines": 0, "by_code": {}}
    pairs = {}
    for ln in lines:
        if ln["item_code"] not in NEW_ITEMS:
            continue
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec or rec.get("action") != "BED":
            raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} is not a V3.0.37 bed line")
        fin = by.get(rec["finish_line"])
        if fin is None or fin["item_code"] not in FINISH_CODES or fin["evidence_state"] not in VALUED_STATES:
            raise ValueError(f"{METHOD}: bed {ln['line_id']} is not bound to a valued floor-finish line")
        mp = ln.get("measure_pair") or {}
        if mp.get("price_one_basis") is not True or ln["line_id"] not in (mp.get("lines") or ()):
            raise ValueError(f"{METHOD}: bed {ln['line_id']} is not in its measure pair (price one basis)")
        if ln["unit"] == "m2":
            if ln["evidence_state"] != fin["evidence_state"] or abs(ln["measured_net"] - fin["measured_net"]) > 1e-9:
                raise ValueError(f"{METHOD}: bed m2 {ln['line_id']} is not its finish line's net")
        elif ln["unit"] == "m3":
            br = ln.get("bounded_range") or {}
            if (ln["evidence_state"] != "BOUNDED_EXPOSURE" or ln.get("measured_net") is not None
                    or ln.get("gross") is not None or not br.get("high") or br["low"] <= 0):
                raise ValueError(f"{METHOD}: bed m3 {ln['line_id']} is not a positive owner range (never 0, never "
                                 f"a chosen value)")
        else:
            raise ValueError(f"{METHOD}: bed {ln['line_id']} unit {ln['unit']}")
        key = ln["location"]["element_id"]
        pairs.setdefault(key, {})
        if ln["unit"] in pairs[key]:
            raise ValueError(f"{METHOD}: bed {key} carries two {ln['unit']} lines (one bed, one item)")
        pairs[key][ln["unit"]] = ln["line_id"]
        out["lines"] += 1
        out["by_code"][f"{ln['item_code']}|{ln['unit']}"] = out["by_code"].get(f"{ln['item_code']}|{ln['unit']}",
                                                                                 0) + 1
    fins = {}
    for k, v in pairs.items():
        if set(v) != set(ROW_UNITS):
            raise ValueError(f"{METHOD}: bed {k} has {sorted(v)} (an m2 and an m3 line, a pair)")
        f = by[v["m2"]]["calculation"]["inputs"][REC_KEY]["finish_line"]
        if f in fins:
            raise ValueError(f"{METHOD}: finish line {f} carries two beds")
        fins[f] = k
    out["beds"] = len(pairs)
    out["by_code"] = dict(sorted(out["by_code"].items()))
    return out


def integrate(l3036, changes, for_lead=()):
    """-> (V3.0.37 lines, identity). Every V3.0.36 line is byte-identical (this version only adds lines)."""
    sid = {ln["line_id"] for ln in l3036}
    adds = []
    for c in changes:
        if c["piece"] != PIECE or c["action"] != "ADD":
            raise ValueError(f"{METHOD}: {c['piece']} {c['action']} (this version only adds B3-05 bed lines)")
        a = c["after"]
        if a["line_id"] in sid or a["item_code"] not in NEW_ITEMS:
            raise ValueError(f"{METHOD}: an added line repeats a V3.0.36 id or is not a B3-05 bed code")
        adds.append(a)
    out = list(l3036) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = A3035.check_boundary(out)
    lists = A3036.check_lists(out)
    beds = check_beds(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    outside = out[:len(l3036)]
    bad = [a["line_id"] for a, b in zip(l3036, outside) if A30.line_sha(a) != A30.line_sha(b)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.36 line(s) differ")
    ident = {"v3_0_36_lines": len(l3036), "v3_0_37_lines": len(out), "v3_0_37_rows": len(changes),
             "replaced": 0, "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_36": len(outside), "beds": beds, "lists": lists, "fence": fence,
             "tile_zones": zones, "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, records=(), released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"][REC_KEY]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": "BED_" + ref["unit"].upper(),
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "finish_line": rec["finish_line"],
                     "kind": rec["kind"], "zone": rec.get("zone"), "before_released_v2_9": b29,
                     "before_v3_0_36": A30._qty(None), "after_v3_0_37": A30._qty(ref),
                     "owner_range": rec.get("owner_range"), "drawing_bound": rec.get("drawing_bound"),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    rows += [dict(r) for r in records]
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "element_id", "unit", "finish_line", "kind", "zone",
              "v2_9", "v3_0_36", "v3_0_37", "owner_range_m", "drawing_bound", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_36", "vs_released_v2_9", "v2_9",
            "v3_0_36", "v3_0_37")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def o(r):
        x = r.get("owner_range")
        return "" if not x else f"{_fmt(x['lo_m'])} .. {_fmt(x['hi_m'])}"

    def d(r):
        x = r.get("drawing_bound")
        if not x:
            return ""
        return "HELD, no bound" if x.get("high") is None else f"HELD 0 .. {_fmt(x['high'])} (b {_fmt(x['b_upper'])})"
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r.get("line_id") or "",
                       "item_code": r.get("item_code") or "", "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r.get("unit") or "",
                       "finish_line": r.get("finish_line") or "", "kind": r.get("kind") or "",
                       "zone": r.get("zone") or "", "v2_9": q(r.get("before_released_v2_9")),
                       "v3_0_36": q(r.get("before_v3_0_36")), "v3_0_37": q(r.get("after_v3_0_37")),
                       "owner_range_m": o(r) if r.get("unit") == "m3" else "",
                       "drawing_bound": d(r) if r.get("unit") == "m3" else "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3036, l3037, released_lines=None):
    b36 = {ln["line_id"]: ln for ln in l3036}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3037:
        o = b36.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_36": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_36": A302._q(A30._qty(o)) if o else "", "v3_0_37": A302._q(A30._qty(ln))})
    return out


def write(out, l3036, changes, log, released_lines=None, for_lead=()):
    """the V3_0_37_* files beside the V3_0_36_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3037, ident = integrate(l3036, changes, for_lead)
    rows = ledger_rows(changes, log.get("records") or (), released_lines)
    diff = diff_rows(l3036, l3037, released_lines)
    if any(d["vs_v3_0_36"] == "CHANGED" for d in diff):
        raise ValueError(f"{METHOD}: a V3.0.36 line changed (this version only adds)")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_36", {}).setdefault(d["vs_v3_0_36"], 0)
        dsum["vs_v3_0_36"][d["vs_v3_0_36"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t36, t37 = A304.code_totals(l3036), A304.code_totals(l3037)
    moved = {k: {"v3_0_36": t36.get(k), "v3_0_37": t37.get(k)} for k in sorted(set(t36) | set(t37))
             if t36.get(k) != t37.get(k)}
    if any(k.split("|")[0] not in NEW_ITEMS for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the bed codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_37_BOQ_LINES.json": BL.dumps(l3037),
             "V3_0_37_BOQ_LINES.csv": A30._lines_csv(l3037),
             "V3_0_37_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_37_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_37_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_37_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "NEW_ITEMS", "load_inputs",
           "changes_for", "check_beds", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
