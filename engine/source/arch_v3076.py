"""ARCH_TAKEOFF_V3.0.76 (T-736, lane I, BEADS + CEILING ROUND 3 integration package, hubs H2a / H1R + one Checker
downgrade record): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.75 (engine.source.arch_v30, arch_v301 ..
arch_v3075), extended with THREE pieces built from Checker-merged research and one Checker-issued record, by line id
as the merged T-730 readiness map (R-T730-1) names them. No line outside FIN.PLASTER.BEAD, FIN.CEILING and FIN.WP.ROOF
moves:

  BEAD_ADD  (hub H2a) one NEW FIN.PLASTER.BEAD line (lm, family B4-09, trade plaster: register ruling 'corner beads ->
            plaster') per interior plaster host of the merged T-728 bead restatement (R-T728-1): the bead takes its
            host's HELD state and cause and keeps its OWN ledger length arris by arris (F-T728-1: a host m2 bound is
            never turned into m.l):
              BOUND     every arris of the host measured: HELD BOUNDED sum(lows) .. sum(highs) m.l (a point where every
                        arris is a point);
              AT_LEAST  one or more arrises of the host HELD blank (arch / curved opening / undrawn head): the line is
                        HELD blank with the measured arrises' lower-end sum beside (upper end open: an unmeasured arris
                        only adds), never a closed range, never in a code total; the blank arrises named;
            the host must be the HELD candidate line the map bound (item, element, unit, range): stale = stop; a held
            host never yields a released bead (R-T728-1); an arris is counted once (one id, one host).
  CEIL_EXCL (hub H1R) the merged T-727 ruling R-T727-2: a HELD blank ceiling line that names only a face already
            inside a RELEASED ceiling line of the same code becomes EXCLUDED_WITH_REASON (DUPLICATE_FACE of the owner
            line, named); never valued, never 0 by omission.
  DG_HOLD   a Checker-issued downgrade-only record (URBAN_CHECKER_DOWNGRADE_V1, LINE_CONTENT_V1 binding) on a RELEASED
            line is materialised: released -> HELD BOUNDED at the same-basis band the record states, read from the
            record, never re-derived; the record must name the line, bind its content (sha256) and its engine_qty;
            downgrade only, never the other way.

R-T736-1 (every villa): (a) a line is wired only from a Checker-merged ledger (or a Checker-issued record) that names it
by id, through the merged readiness map; (b) every entry binds to the candidate line as the map read it and stops on a
stale line; (c) a bead line is one per host, its arrises once each, its figure the sum of its own arris lengths; a
blank arris makes the line AT_LEAST (never a closed range), a held host never a released bead; (d) an exclusion names a
RELEASED owner line of the same code and unit; (e) a downgrade moves a RELEASED line to HELD only, at the record's band,
with the record's content binding and engine_qty asserted; (f) only FIN.PLASTER.BEAD|lm, FIN.CEILING|m2 and
FIN.WP.ROOF|m2 code totals move, each exactly by the changes; every other line byte-identical (asserted); the earlier
state checks re-run on the result; nothing here is VERIFIED; blank is never 0.
Files: V3_0_76_BOQ_LINES.json / .csv, V3_0_76_INTEGRATION_LEDGER.json / .csv, V3_0_76_DIFF.csv, V3_0_76_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re
from decimal import Decimal

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3064 as A3064
from engine.source import arch_v3065 as A3065
from engine.source import arch_v3066 as A3066
from engine.source import arch_v3067 as A3067
from engine.source import arch_v3068 as A3068
from engine.source import arch_v3069 as A3069
from engine.source import arch_v3070 as A3070
from engine.source import arch_v3071 as A3071
from engine.source import arch_v3072 as A3072
from engine.source import arch_v3073 as A3073
from engine.source import arch_v3074 as A3074
from engine.source import arch_v3075 as A3075

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged bead / ceiling ledgers and a Checker record
METHOD = "ARCH_TAKEOFF_V3.0.76"
EXTENDS = A3075.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T736_ARCH_V3_0_76"
INPUTS_SCHEMA = "URBAN_V3076_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3076_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T736-1", "T-736"
REC_KEY = "beads_ceiling_v3076"
BEAD = "FIN.PLASTER.BEAD"
BEAD_ITEM = ("Corner beads / profiles (plaster, exposed arris length)", "زوايا معدنية", "PLASTER")
PLASTER, CEILING, WP_ROOF = "FIN.PLASTER", "FIN.CEILING", "FIN.WP.ROOF"
CODES = {BEAD: "lm", CEILING: "m2", WP_ROOF: "m2"}
P_BEAD, P_CEIL, P_DG = "BEAD_ADD", "CEIL_EXCL", "DG_HOLD"
ACTIONS = {P_BEAD: ("BOUND", "AT_LEAST"), P_CEIL: ("EXCLUDE",), P_DG: ("HOLD",)}
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
EXCLUDED_STATE = "EXCLUDED_WITH_REASON"
STATUSES = ("DRAWING-CONFIRMED", "HELD", "ASSUMED — OWNER-APPROVED")      # WORKFLOW_CONTROLS s.5; never VERIFIED
TOL = 1e-6
TOT_TOL = 5e-6
MAX_LM = 500.0                           # one host above 500 m.l of bead is a unit slip
MAX_M2 = 1000.0
ARRIS_RE = re.compile(r"^[A-Za-z0-9#_.:+\-]+(?: [+] [A-Za-z0-9#_.:+\-]+)*$")
DG_BAND_RE = re.compile(r"band (\d+(?:\.\d+)?) \.\. (\d+(?:\.\d+)?) m2")
D = Decimal

PIECES = {
    P_BEAD: {"module": "engine/source/arch_v3076.py (one FIN.PLASTER.BEAD line per interior plaster host of the merged "
                       "T-728 bead restatement, as mapped by T-730 hub H2a: HELD bounded by the arrises' own lengths, "
                       "or HELD blank with the measured lower end beside where an arris is blank)",
             "policy": "BEADS_GATE_B_V1", "rule_id": "R-T728-1 (R-T736-1)",
             "owner_rules": ["OD-V3B-8 / G1 (bead to the finished ceiling, exposed length only; F-T697-1)",
                             "Lead ruling 2026-11-11 16:25 F-T705-1 (the bead takes its host's HELD state)",
                             "register ruling: arris counted once; corner beads -> plaster",
                             "UP-QTY-STATUS-001 (held is blank or bounded, never 0)", "R-T698-1"],
             "owner_manual_method": "every convex plastered arris: external corners and opening jambs / heads x the "
                                    "exposed height to the finished ceiling (G1), once per arris, in m.l",
             "drawing_method": "the merged T-697 / T-728 arris ledger by handle (room corners, door / window jambs and "
                               "heads, wall ends), each arris its own measured length; an arch / curved opening / "
                               "undrawn head HELD blank by name"},
    P_CEIL: {"module": "engine/source/arch_v3076.py (the T-727 R-T727-2 DUPLICATE_FACE exclusion of the ceiling-over-"
                       "void line, hub H1R)",
             "policy": "CEILING_GATE_B_V3", "rule_id": "R-T727-2 (R-T736-1)",
             "owner_rules": ["R-T727-1 (union, not sum)", "R-T727-2 (one face, one line)", "UP-QTY-STATUS-001"],
             "owner_manual_method": "ceiling area once per face at the soffit it is under; a double-height volume "
                                    "takes its ceiling at the upper soffit, inside that room's face",
             "drawing_method": "the upper plan over the well shows no opening outline: the well top is inside the "
                               "released decor ceiling face (T-727 s.3); the void line names only that rectangle"},
    P_DG: {"module": "engine/source/arch_v3076.py (Checker downgrade-only record materialised: released -> HELD at the "
                     "record's same-basis band)",
           "policy": "CHECKER_DOWNGRADE_MATERIALISE_V1", "rule_id": "R-T665-1 (g) / R-T734-1 (c) (R-T736-1)",
           "owner_rules": ["owner 2026-10-24 23:57 (1): DOWNGRADE-ONLY RECORD, never promote", "UP-QTY-STATUS-001"],
           "owner_manual_method": "roof membrane = the roof's closed plan face less the dome openings, once",
           "drawing_method": "the record's two same-basis readings of the closed face less the two true dome "
                             "circles (pi r^2), as the Checker printed them"},
}
WAITING = dict(A3075.WAITING)
WAITING.update({
    "T736_BEADS_HOST_HELD": "the 14 interior bead lines are HELD only because their plaster hosts are HELD (D-39 roof "
                            "build-up, Q-54 B annex datum, shaft exposure): they release with their hosts, no re-measure "
                            "(F-T728-2)",
    "T736_BEADS_BLANK_ARRIS": "6 interior arrises HELD blank (arches A-1F-01 / A-GF-01 D-45, curved W03 / W17 room "
                              "side, OP-003 / OP-020 heads): their lines carry an AT_LEAST figure, upper end open",
    "T736_EXTERIOR_BEADS": "43 exterior bead arrises (H2b) wait T-314 r3 face rows (42) and D-62 (plinth): no line",
    "T736_H4_REST": "the rest of hub H4 (WP + roof) stays in T-750",
})


# ================================================================================================ inputs
def _d(x, w, hi, zero=False):
    if isinstance(x, bool) or x is None:
        raise InputsError(f"{w}: not a number ({x!r})")
    try:
        v = D(str(x))
    except Exception:  # noqa: BLE001
        raise InputsError(f"{w}: not a number ({x!r})") from None
    if not v.is_finite() or v < 0 or v > D(str(hi)) or (v == 0 and not zero):
        raise InputsError(f"{w}: {x!r} outside {'0' if zero else '>0'} .. {hi} (never 0, unit slip)")
    return v


def _arrises(e, w):
    rows = e.get("arrises") or ()
    if not rows:
        raise InputsError(f"{w}: a bead line carries its arrises")
    ids, lo, hi, blank = set(), D(0), D(0), []
    for a in rows:
        A3063._need(a, ("edge_id", "state", "why"), f"{w} arris")
        aid = str(a["edge_id"])
        if not ARRIS_RE.match(aid) or aid in ids:
            raise InputsError(f"{w}: arris {aid!r} malformed or named twice (an arris is counted once)")
        ids.add(aid)
        if a["state"] == "HELD_BOUND":
            l_, h_ = _d(a.get("low"), f"{w} {aid} low", MAX_LM), _d(a.get("high"), f"{w} {aid} high", MAX_LM)
            if l_ > h_:
                raise InputsError(f"{w}: {aid} low {l_} > high {h_}")
            lo, hi = lo + l_, hi + h_
        elif a["state"] == "HELD_BLANK":
            if a.get("low") is not None or a.get("high") is not None:
                raise InputsError(f"{w}: blank arris {aid} carries a figure (blank is never numbered)")
            blank.append(aid)
        else:
            raise InputsError(f"{w}: arris {aid} state {a['state']!r} (HELD_BOUND / HELD_BLANK; a held host never "
                              f"yields a released bead, R-T728-1)")
    if lo == 0:
        raise InputsError(f"{w}: no measured arris: a bead line needs at least one measured arris")
    return lo, hi, blank


def _entry(x, srcs):
    p, a = x.get("piece"), x.get("action")
    w = f"{p} {a} {x.get('line_id') or x.get('host_line_id')}"
    A3043._tasks(x, srcs, w)
    if p not in ACTIONS or a not in ACTIONS[p]:
        raise InputsError(f"{w}: piece / action not one of {ACTIONS}")
    if x.get("status") not in STATUSES:
        raise InputsError(f"{w}: status {x.get('status')!r} ({STATUSES}; never VERIFIED here)")
    A3063._need(x, ("expect", "why"), w)
    e = dict(x)
    if p == P_BEAD:
        A3063._need(x, ("host_line_id", "element_id"), w)
        if x.get("line_id") is not None or not A3063.LINE_ID_RE.match(str(x["host_line_id"])):
            raise InputsError(f"{w}: a bead line names its host line, never a line id of its own")
        ex = x["expect"]
        A3063._need(ex, ("item_code", "element_id", "unit", "class", "low", "high"), w)
        if ex["item_code"] != PLASTER or ex["unit"] != "m2" or ex["class"] != "HELD":
            raise InputsError(f"{w}: the host is a HELD FIN.PLASTER m2 line (the map's), not {ex}")
        lo, hi, blank = _arrises(x, w)
        if (a == "BOUND") == bool(blank):
            raise InputsError(f"{w}: {a} with {len(blank)} blank arris(es): a blank arris makes the line AT_LEAST, "
                              f"never a closed range")
        e.update(_low=lo, _high=hi, _blank=blank)
        return e
    lid = x.get("line_id")
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    if p == P_CEIL:
        A3063._need(x, ("owner_line_id", "owner_expect", "cause"), w)
        if ex["item_code"] != CEILING or ex["unit"] != "m2" or ex["class"] != "HELD" or x["cause"] != "DUPLICATE_FACE":
            raise InputsError(f"{w}: a DUPLICATE_FACE exclusion of a HELD FIN.CEILING m2 line only")
        if (x["owner_expect"] or {}).get("class") != "RELEASED" or x["owner_line_id"] == lid:
            raise InputsError(f"{w}: the owner is another, RELEASED line (never the line itself)")
        return e
    A3063._need(x, ("record",), w)
    if ex["item_code"] != WP_ROOF or ex["unit"] != "m2" or ex["class"] != "RELEASED":
        raise InputsError(f"{w}: a downgrade holds a RELEASED FIN.WP.ROOF m2 line only")
    r = x["record"]
    A3063._need(r, ("downgrade_id", "line_ids", "line_content_sha256", "engine_qty", "unit", "state", "reason",
                    "file", "file_sha256", "checker"), f"{w} record")
    if not str(r["downgrade_id"]).startswith("DG-") or lid not in r["line_ids"] or r["state"] != "HELD" or \
            r["unit"] != "m2":
        raise InputsError(f"{w}: the record {r.get('downgrade_id')} does not hold this line (HELD, m2)")
    bands = DG_BAND_RE.findall(str(r["reason"]))
    if len(set(bands)) != 1:
        raise InputsError(f"{w}: the record states {len(set(bands))} band(s): one same-basis band is read, never "
                          f"chosen")
    lo, hi = _d(bands[0][0], f"{w} band low", MAX_M2), _d(bands[0][1], f"{w} band high", MAX_M2)
    if lo > hi or x.get("low") is None or D(str(x["low"])) != lo or D(str(x["high"])) != hi:
        raise InputsError(f"{w}: the entry's band {x.get('low')} .. {x.get('high')} is not the record's {lo} .. {hi}")
    e.update(_low=lo, _high=hi)
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3076_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"piece" BEAD_ADD | CEIL_EXCL | DG_HOLD, "action", "source_tasks", "rule", "status", "why",
                  "expect" {item_code, element_id, unit, class, low, high},
                  BEAD_ADD: "host_line_id", "element_id", "arrises" [{edge_id, class, state
                            HELD_BOUND | HELD_BLANK, low, high, why}];
                  CEIL_EXCL: "line_id", "owner_line_id", "owner_expect" {item_code, element_id, unit, class,
                             measured_net}, "cause" DUPLICATE_FACE;
                  DG_HOLD: "line_id", "low", "high", "record" {downgrade_id, line_ids, line_content_sha256,
                           engine_qty, unit, state, reason, file, file_sha256, checker}}],
     "expect_totals": {"<code>|<unit>": {...}} (optional)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = [_entry(x, srcs) for x in doc.get("entries") or ()]
    if not ents:
        raise InputsError("no entry in the inputs")
    keys = [e.get("line_id") or f"BEAD@{e['host_line_id']}" for e in ents]
    if len(set(keys)) != len(keys):
        raise InputsError("a line (or a host's bead line) is named twice (one line, one statement)")
    arr = [a["edge_id"] for e in ents if e["piece"] == P_BEAD for a in e["arrises"]]
    if len(set(arr)) != len(arr):
        raise InputsError("an arris is under two hosts (an arris is counted once)")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[kw["piece"]]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _expect(b, x, w):
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"] and \
        line_class(b) == x["class"]
    if ok and x["class"] == "HELD":
        r = A3063._range(b)
        if x.get("low") is None:
            ok = r is None and b.get("measured_net") is None
        else:
            ok = r is not None and abs(r[0] - float(x["low"])) <= TOL and abs(r[1] - float(x["high"])) <= TOL
    if ok and x.get("measured_net") is not None:
        ok = abs(float(b.get("measured_net") or -1) - float(x["measured_net"])) <= TOL
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{A30._qty(b)} is not the map's {x} (stale binding: re-read)")


def host_cause(h):
    """the HELD host's own open question (its current cause), as the candidate carries it"""
    q = ((h.get("rfi") or {}).get("question") or "").strip()
    return q[:500] if q else "host HELD (no question recorded)"


def _bead_line(h, e, srcs):
    from engine.source import boq_line as BL
    lo, hi, blank = float(e["_low"]), float(e["_high"]), e["_blank"]
    hc = host_cause(h)
    meas = [a for a in e["arrises"] if a["state"] == "HELD_BOUND"]
    arr_txt = ", ".join(f"{a['edge_id']} {_fmt(float(a['low']))}" + ("" if a["low"] == a["high"] else
                                                                     f"..{_fmt(float(a['high']))}") for a in meas)
    rec = _rec(srcs, piece=P_BEAD, action=e["action"], host_line_id=h["line_id"],
               host_element=(h.get("location") or {}).get("element_id"), host_range=list(A3063._range(h) or ()),
               host_cause=hc, arrises=e["arrises"], blank_arrises=blank, why=str(e["why"])[:400],
               rule=e.get("rule"), evidence_status=e["status"],
               beside=({"kind": "AT_LEAST_LM", "value": _r(lo), "basis": "sum of the measured arrises' lower ends; "
                        f"{len(blank)} arris(es) blank: upper end open"} if blank else None))
    if blank:
        state, br = BLANK, None
        head = (f"HELD, LOWER END ONLY (blank): at least {_fmt(lo)} m.l beside, upper end open "
                f"({len(meas)} arris(es) measured, blank: {', '.join(blank)})")
    else:
        state, br = BOUNDED, {"low": _r(lo), "high": _r(hi), "basis": f"{e.get('rule')}: sum of {len(meas)} arris "
                                                                     f"length(s), host HELD"[:200]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m.l ({len(meas)} arris(es), each its own length)"
    f = (f"{METHOD}: {head}; {e.get('rule')}: bead takes its host's HELD state, keeps its own arris lengths "
         f"(F-T728-1: no m2 bound becomes m.l); arrises: {arr_txt}; held on: host {h['line_id']}: {hc}")[:1500]
    eid = e["element_id"]
    ln = BL.make_line(project_id=h["project"]["project_id"], revision_set_sha256=h["project"]["revision_set_sha256"],
                      item_code=BEAD, unit="lm", evidence_state=state, element_id=eid,
                      floor=(h.get("location") or {}).get("floor"), room_id=(h.get("location") or {}).get("room_id"),
                      room_name_en=(h.get("location") or {}).get("room_name_en"),
                      room_name_ar=(h.get("location") or {}).get("room_name_ar"),
                      physical_element="corner bead on the convex plastered arrises of the host face (exposed length)",
                      bounded_range=br, formula=f, inputs={REC_KEY: rec, "evidence_status": e["status"]},
                      documents=copy.deepcopy(h["source"]["documents"]), geometry_source=h["source"]["geometry_source"],
                      geometry_confidence=h["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state="BY_SPEC",
                      rfi={"question": f"open: host {h['line_id']} HELD: {hc}"[:400] +
                           (f"; blank arrises: {', '.join(blank)}" if blank else ""), "blocks": [h["line_id"]]},
                      notes=f"bead line of host {h['line_id']} (B4-09; never summed into the m2 host); HELD, never 0; "
                            f"NOT RELEASED", item_en=BEAD_ITEM[0], item_ar=BEAD_ITEM[1], trade=BEAD_ITEM[2],
                      subtrade="CORNER_BEAD")
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{eid}: the formula would conclude on a figure")
    return A3063._fin(ln)


def _restate(b, e, srcs, owner=None):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    why = str(e["why"])[:400]
    if e["piece"] == P_CEIL:
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = EXCLUDED_STATE, None, None, None
        ln["rfi"] = None
        head = (f"EXCLUDED (DUPLICATE_FACE of {owner['line_id']} {owner['location']['element_id']}, released "
                f"{_fmt(float(owner['measured_net']))} m2): the face this line names is inside the owner's face")
        after = {"excluded": "DUPLICATE_FACE", "owner_line_id": owner["line_id"]}
        extra = {"owner_line_id": owner["line_id"], "cause": "DUPLICATE_FACE"}
        ln["notes"] = (f"{METHOD}: EXCLUDED_WITH_REASON DUPLICATE_FACE of {owner['line_id']} (R-T727-2): never "
                       f"valued, never 0 by omission; " + str(b.get("notes") or ""))[:600]
    else:
        lo, hi = float(e["_low"]), float(e["_high"])
        r = e["record"]
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi),
                               "basis": f"Checker downgrade {r['downgrade_id']}: same-basis band"[:200]}
        ln["rfi"] = {"question": f"open: {r['downgrade_id']} (Checker, UNSUPPORTED BASIS): {why}"[:400],
                     "blocks": [b["line_id"]]}
        head = (f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m2 under Checker downgrade {r['downgrade_id']} (was "
                f"released {_fmt(float(b['measured_net']))}; downgrade only)")
        after = {"low": _r(lo), "high": _r(hi)}
        extra = {"downgrade": {k: r[k] for k in ("downgrade_id", "line_ids", "line_content_sha256", "engine_qty",
                                                 "file", "file_sha256", "checker")}}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e.get('rule')}: {why}"[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{b['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=e["piece"], action=e["action"], was=was, after=after, why=why,
                        rule=e.get("rule"), evidence_status=e["status"], **extra)
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def assert_record(e, b):
    """R-T736-1 (e): the Checker record names this line, binds its content and its released quantity."""
    r = e["record"]
    if A3063._content_sha([b]) != r["line_content_sha256"]:
        raise InputsError(f"{r['downgrade_id']}: the line changed since the Checker bound it (stale record)")
    if abs(float(b["measured_net"]) - float(r["engine_qty"])) > TOT_TOL or r["line_ids"] != [b["line_id"]]:
        raise InputsError(f"{r['downgrade_id']}: released {b['measured_net']} / lines {r['line_ids']} are not the "
                          f"record's {r['engine_qty']} / [{b['line_id']}]")


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T736", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.76 records (applied once)")
    if any(ln["item_code"] == BEAD for ln in prev):
        raise InputsError(f"the candidate already carries {BEAD} lines")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T736", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        srcs = [S[t] for t in e["source_tasks"]]
        k = f"{e['piece']}:{e['action']}"
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1
        ref = "; ".join(s["file"] for s in srcs)
        if e["piece"] == P_BEAD:
            h = by.get(e["host_line_id"])
            _expect(h, e["expect"], f"{k} host {e['host_line_id']}")
            after = _bead_line(h, e, srcs)
            if after["line_id"] in by:
                raise InputsError(f"{k}: the bead line id is already a candidate line")
            q = A30._qty(after)
            changes.append(A305._change(e["piece"], "ADD", None, after, drawing_reference=ref, held=[
                {"what": h["line_id"], "why": host_cause(h)[:300],
                 "range": [q["low"], q["high"]] if q["low"] is not None else None,
                 "beside": after["calculation"]["inputs"][REC_KEY].get("beside")}], downstream=[],
                verification=A3036._ver(srcs), evidence_status=e["status"], group=BEAD, step=e["action"]))
            continue
        b = by.get(e["line_id"])
        _expect(b, e["expect"], k)
        owner = None
        if e["piece"] == P_CEIL:
            owner = by.get(e["owner_line_id"])
            _expect(owner, e["owner_expect"], f"{k} owner")
            if owner["item_code"] != b["item_code"] or owner["unit"] != b["unit"] or line_class(owner) != "RELEASED":
                raise InputsError(f"{k}: the owner {e['owner_line_id']} is not a RELEASED line of the same code")
        else:
            assert_record(e, b)
        after = _restate(b, e, srcs, owner)
        q = A30._qty(after)
        held = [] if e["piece"] == P_CEIL else [{"what": e["line_id"], "why": str(e["why"])[:300],
                                                 "range": [q["low"], q["high"]]}]
        changes.append(A305._change(e["piece"], "CHANGE", b, after, drawing_reference=ref, held=held, downstream=[],
                                    verification=A3036._ver(srcs), evidence_status=e["status"], group=b["item_code"],
                                    step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T736-1 (f): only the three codes move, each exactly by the changes."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if CODES.get(k.split("|")[0]) != k.split("|")[1])
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside {sorted(CODES)}: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if z is None or a is None:
            if a is None and z is not None and z["lines"] == 0:
                out[k] = {"base": t0.get(k), "v3_0_76": None}
                continue
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("released", "held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_76": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every V3.0.76 line is in the state its piece names; a bead line binds a HELD FIN.PLASTER
    host by id, one per host, its arrises once; with `before`: no line outside this version became RELEASED, and the
    only released line that moved is a downgraded one (to HELD). -> {piece:action: n}"""
    by = {ln["line_id"]: ln for ln in lines}
    out, hosts, arr = {}, set(), set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] == BEAD:
                raise ValueError(f"{METHOD}: {ln['line_id']} a bead line with no V3.0.76 record")
            continue
        p, a, cls, r = rec["piece"], rec["action"], line_class(ln), A3063._range(ln)
        if p == P_BEAD:
            h = by.get(rec["host_line_id"])
            ids = [x["edge_id"] for x in rec["arrises"]]
            ok = ln["item_code"] == BEAD and ln["unit"] == "lm" and cls == "HELD" and ln.get("measured_net") is None \
                and h is not None and h["item_code"] == PLASTER and line_class(h) == "HELD" and \
                rec["host_line_id"] not in hosts and not (set(ids) & arr)
            if a == "BOUND":
                ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9 and not rec.get("blank_arrises")
            else:
                ok = ok and ln["evidence_state"] == BLANK and r is None and bool(rec.get("blank_arrises")) and \
                    float((rec.get("beside") or {}).get("value") or 0) > 0
            hosts.add(rec["host_line_id"])
            arr.update(ids)
        elif p == P_CEIL:
            o = by.get(rec["owner_line_id"])
            ok = ln["evidence_state"] == EXCLUDED_STATE and ln.get("measured_net") is None and o is not None and \
                line_class(o) == "RELEASED" and o["item_code"] == ln["item_code"] and bool(ln.get("notes"))
        else:
            ok = cls == "HELD" and r is not None and 0 < r[0] <= r[1] and rec["was"]["class"] == "RELEASED" and \
                bool((rec.get("downgrade") or {}).get("downgrade_id"))
        ok = ok and rec["release_status"] == "NOT RELEASED" and (cls == "EXCLUDED" or
                                                                  bool((ln.get("rfi") or {}).get("question")))
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} {a} line is not in its state")
        out[f"{p}:{a}"] = out.get(f"{p}:{a}", 0) + 1
    if before is not None:
        old = {x["line_id"]: x for x in before}
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None:
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released quantity moved")
            rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
            if line_class(o) == "RELEASED" and line_class(ln) != "RELEASED" and (rec or {}).get("piece") != P_DG:
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released line left RELEASED with no Checker record")
    return out


def census(lines, codes=tuple(CODES)):
    """per code: released n / qty, bounded n / low .. high, blank n with the AT_LEAST figures beside (run-record sums
    only, never summed into anything else), excluded n."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "low": 0.0, "high": 0.0, "blank": 0, "at_least_n": 0,
                               "at_least_sum_run_record_only": 0.0, "excluded": 0})
        z["lines"] += 1
        k, r = line_class(ln), A3063._range(ln)
        if k == "EXCLUDED":
            z["excluded"] += 1
        elif k == "RELEASED":
            z["released"] += 1
            z["released_q"] += float(ln["measured_net"])
        elif r is not None:
            z["bounded"] += 1
            z["low"] += r[0]
            z["high"] += r[1]
        else:
            z["blank"] += 1
            b = ((((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)) or {}).get("beside") or {}
            if b.get("kind") == "AT_LEAST_LM":
                z["at_least_n"] += 1
                z["at_least_sum_run_record_only"] += float(b["value"])
    for z in out.values():
        for f in ("released_q", "low", "high", "at_least_sum_run_record_only"):
            z[f] = round(z[f], 6)
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.76 lines, identity). Changed lines replace their candidate line in place, added bead lines follow the
    base; every other candidate line byte-identical (asserted); the earlier state checks re-run."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if CODES.get(a["item_code"]) != a["unit"]:
            raise ValueError(f"{METHOD}: {a['item_code']} {a['unit']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl or c["piece"] == P_BEAD:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if c["piece"] != P_BEAD or a["line_id"] in sid or a["item_code"] != BEAD:
                raise ValueError(f"{METHOD}: only bead lines are added, never over a candidate id")
            add.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + add
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    ident = {"base_lines": len(prev), "v3_0_76_lines": len(out), "v3_0_76_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(out),
             "concrete_v3_0_65": A3065.check_concrete(out), "concrete_v3_0_66": A3066.check_concrete(out),
             "concrete_v3_0_67": A3067.check_concrete(out, prev), "lintels_v3_0_67": A3067.check_lintels(out),
             "masonry_v3_0_68": A3068.check_masonry(out), "finishes_v3_0_69": A3069.check_finishes(out),
             "concrete_v3_0_70": A3070.check_concrete(out, prev), "lintels_v3_0_71": A3071.check_lintels(out, prev),
             "masonry_v3_0_72": A3072.check_masonry(out, prev), "concrete_v3_0_73": A3073.check_concrete(out, prev),
             "finishes_v3_0_74": A3074.check_finishes(out, prev), "formwork_concrete_v3_0_75":
                 A3075.check_lines(out, prev), "beads_ceiling": check_lines(out, prev),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        a = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(a)]) if A30._key(a) in rel else dict(A30._qty(None), state="NOT_IN_RELEASED")
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": a["line_id"], "item_code": a["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": a["unit"], "host_line_id": rec.get("host_line_id"),
                     "owner_line_id": rec.get("owner_line_id"), "before_released_v2_9": b29,
                     "before_base": A30._qty(c.get("before")), "after_v3_0_76": A30._qty(a),
                     "class": [None if c.get("before") is None else line_class(c["before"]), line_class(a)],
                     "evidence_state_after": a["evidence_state"], "beside": rec.get("beside"),
                     "arrises": rec.get("arrises"), "blank_arrises": rec.get("blank_arrises"),
                     "host_range_m2_reference_only": rec.get("host_range"), "host_cause": rec.get("host_cause"),
                     "downgrade": rec.get("downgrade"), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "rule": rec.get("rule"), "why": rec.get("why"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_76", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_76")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        t = "none" if not b else f"at least {_fmt(b['value'])} m.l (upper end open)"
        if r.get("owner_line_id"):
            t = f"EXCLUDED: DUPLICATE_FACE of {r['owner_line_id']}"
        if r.get("downgrade"):
            t = f"downgrade {r['downgrade']['downgrade_id']}"
        return t
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_76": q(r.get("after_v3_0_76")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_75"}, v3_0_76=d["v3_0_75"])
            for d in A3075.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_76_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] != "SAME" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, census_before=census(prev), census_after=census(new))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_76_BOQ_LINES.json": BL.dumps(new),
             "V3_0_76_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_76_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_76_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_76_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_76_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": sorted(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "census", "check_lines", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class", "host_cause", "assert_record"]
