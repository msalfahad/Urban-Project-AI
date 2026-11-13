"""ARCH_TAKEOFF_V3.0.78 (T-738, lane I, TILES H3 + STAIR FINISHES H3s integration package; owner order step 5): the SAME
opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.77 (engine.source.arch_v30, arch_v301 .. arch_v3077), extended with
TWO pieces built from Checker-merged research, by line id as the merged T-730 readiness map (R-T730-1, hubs H3 / H3S)
names them. No line outside the tile / stair finish codes below moves; no released quantity moves:

  TILE_BOUND    (T-702 part (b), R-T686-3) a HELD blank stair-core wall tile line becomes HELD BOUNDED low .. high: the
                wall run x the tile top range (highest head .. ceiling datum less the floor level) less the openings
                range; the floor-level designer item stays named on the line.
  STAIR_WIRE    (T-715 R-T715-1..4, restated by T-718 R-T718-1..3 where T-718 declares it; T-733 tread verdict) every
                mapped HELD stair-finish line takes the ONE live statement of its merged ledger:
                  POINT       HELD at one drawn figure (low = high), DRAWING-CONFIRMED or on an owner-approved riser
                              (Q-46 A / Q-50 A cond); held, never released here (only a Checker record releases);
                  BOUND       HELD BOUNDED low .. high (0 < low <= high);
                  EXCLUDE     EXCLUDED_WITH_REASON: DUPLICATE_READING (R-T715-3: the same physical flight read a
                              second time, e.g. seen through the void; its CARRIER line, same code, is named and must be
                              a live candidate line) or NO_PHYSICAL_ELEMENT (no wall face / no landing in it, the
                              merged ledger named); never valued, never 0 by omission;
                  AT_LEAST / AT_MOST
                              HELD blank, the one-sided figure beside (never in a code total; an AT_MOST of 0 refused);
                  CONDITIONAL HELD blank, the figure of ONE payable skirting form beside, conditional on the owner
                              ruling ORR-007 (zigzag vs sloped: two forms of one physical strip, never additive; the
                              sibling form line named); never in a code total, never released, never 0;
                  NAMED       HELD blank, the cause the merged ledger names restated on the line (no figure);
                  ADD_POINT   a drawn piece no candidate line carries (T-715 new line: the closing riser) as a NEW HELD
                              point line of its code, bound by id to a host line of the same code (never summed into it).

R-T738-1 (every villa): (a) a line is wired only from a Checker-merged ledger that names it by line id, through the
merged readiness map; where two merged pieces state a line, only the one that DECLARES the restatement is wired (T-718
over T-715) and the superseded statement is carried on the record, never summed and never picked by size; a map row
that pends on a piece is wired only once that piece is merged (T-733 for the 1F tread highs); (b) every entry binds the
candidate line as the map read it (item, element, unit, HELD, blank or the named range) and stops on a stale line; (c)
an excluded duplicate names its carrier, a live line of the same code and unit that this version does not exclude; one
physical flight, one carrier (R-T715-3); (d) a skirting form figure is CONDITIONAL on ORR-007 and never enters a total;
the two forms of one piece are siblings, never added; (e) only the codes of this version move, each exactly by the
changes; released lines and every other line byte-identical (asserted); the earlier state checks re-run on the result;
(f) held stays held: nothing here is VERIFIED or released; blank is never 0.
Files: V3_0_78_BOQ_LINES.json / .csv, V3_0_78_INTEGRATION_LEDGER.json / .csv, V3_0_78_DIFF.csv, V3_0_78_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import Decimal

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3046 as A3046
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
from engine.source import arch_v3076 as A3076
from engine.source import arch_v3077 as A3077

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged tile / stair finish ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.78"
EXTENDS = A3077.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T738_ARCH_V3_0_78"
INPUTS_SCHEMA = "URBAN_V3078_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3078_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T738-1", "T-738"
REC_KEY = "tile_stair_gate_b_v3078"
TILE = "FIN.WALL.TILE"
SKIRT_SLOPED, SKIRT_ZIGZAG = "FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG"
CODES = {TILE: "m2", "FIN.MARBLE.LANDING": "m2", "FIN.MARBLE.RISER": "m2", "FIN.MARBLE.TREAD": "m2",
         "FIN.STAIR.SOFFIT": "m2", "FIN.STAIR.FLIGHT": "lm", "FIN.STAIR.STEP_LM": "lm", SKIRT_SLOPED: "lm",
         SKIRT_ZIGZAG: "lm"}
STAIR_CODES = tuple(c for c in CODES if c != TILE)
SKIRT_SIBLING = {SKIRT_SLOPED: SKIRT_ZIGZAG, SKIRT_ZIGZAG: SKIRT_SLOPED}
P_TILE, P_STAIR = "TILE_BOUND", "STAIR_WIRE"
ACTIONS = {P_TILE: ("BOUND",),
           P_STAIR: ("POINT", "BOUND", "EXCLUDE", "AT_LEAST", "AT_MOST", "CONDITIONAL", "NAMED", "ADD_POINT")}
EXCLUDE_CAUSES = ("DUPLICATE_READING", "NO_PHYSICAL_ELEMENT")
RULING = "ORR-007"                       # the owner's open ruling on the payable stair skirting form
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
EXCLUDED_STATE = "EXCLUDED_WITH_REASON"
BESIDE_KIND = {"AT_LEAST": "AT_LEAST", "AT_MOST": "AT_MOST", "CONDITIONAL": "CONDITIONAL_ON_FORM"}
STATUSES = ("DRAWING-CONFIRMED", "HELD", "ASSUMED — OWNER-APPROVED")      # WORKFLOW_CONTROLS s.5; never VERIFIED
TOL = 1e-6
TOT_TOL = 5e-6
MAX_Q = {"m2": 200.0, "lm": 100.0}       # one tile / stair finish line above these is a unit slip
D = Decimal

PIECES = {
    P_TILE: {"module": "engine/source/arch_v3078.py (the two HELD blank GF stair-core wall tile lines bounded from the "
                       "merged T-702 part (b) ledger, as mapped by T-730 hub H3)",
             "policy": "TILE_GATE_B_V1", "rule_id": "R-T686-3 / T-702 (b) (R-T738-1)",
             "owner_rules": ["Q-55 C (tile to the highest door head, owner-approved)",
                             "Q-48 A (tile top to the ceiling datum, owner-approved)",
                             "UP-CER-001..008 (wall tiling, measured net of openings)",
                             "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
             "owner_manual_method": "wall tile m2 = tiled wall run x tile height (floor finish to the tile top) less "
                                    "the openings in the tiled band",
             "drawing_method": "T-702 (b): the drawn wall run x tile top 2.20 (highest head) .. +4.65 - floor +0.30 "
                               "(ceiling datum) less the openings range; the floor level is a designer item (C-SH-2): "
                               "both ends kept, never one picked"},
    P_STAIR: {"module": "engine/source/arch_v3078.py (the mapped HELD stair-finish lines of the merged T-715 ledger "
                        "with the T-718 restatements and the T-733 tread verdict, by line id as mapped by T-730 hub "
                        "H3S: points, bounds, duplicate readings excluded with their carrier, one-sided figures and "
                        "ORR-007 form figures beside, causes named, one closing riser added)",
              "policy": "STAIR_FINISH_GATE_B_V1", "rule_id": "R-T715-1..4, R-T718-1..3, R-T733-1/-2 (R-T738-1)",
              "owner_rules": ["Q-46 A (riser from the section count, owner-approved)",
                              "Q-50 A cond (ST-02 riser 4.50 / 28, owner-approved; curved part HELD)",
                              "UP-STAIR-006 (visible riser = r - tread thickness, owner default)",
                              "UP-STAIR-011 (sloped skirting rakes on the nosing line)",
                              "ORR-007 (payable stair skirting form: zigzag or sloped, owner ruling open)",
                              "register: stair concrete + formwork = S, stair finish faces = A",
                              "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
              "owner_manual_method": "per flight: risers n x width x visible riser (m2), treads by plan area (m2), "
                                     "nosings n x width (lm), pitch line goings x hypot(going, rise) (lm), skirting "
                                     "per walled side in the payable form (lm); one flight once",
              "drawing_method": "section counts and the drawn front edges / riser lines by handle (T-410 / T-412 / "
                                "T-415 / T-684 / T-690 / T-718); turn regions tiled by their area (R-T715-2); a flight "
                                "read twice carried once on its carrier (R-T715-3); undrawn winder subdivision / curved "
                                "band held with the designer items D-67 / D-08 / RFI-S27"},
}
WAITING = dict(A3077.WAITING)
WAITING.update({
    "T738_ORR007": "27 stair skirting form lines (13 walled pieces x zigzag / sloped + MS2-TR zigzag) stay HELD blank "
                   "with their form figure beside, CONDITIONAL on the owner's ORR-007 payable-form ruling: never "
                   "summed, never both forms",
    "T738_LANDING_2F": "2F landing L-5d2be30d (0 .. 9.225 m2) keeps its statement: it closes when the T-493 landing "
                       "lines (2F arrival 4.865 + MS2-LD 2.9325) are wired (B7-04)",
    "T738_D67_D08": "winder subdivision (D-67) and the RS-C curved band / curtail (D-08 / RFI-S27) hold the winder pitch "
                    "line, the RS-C tread and pitch line, and the bounds of the turn / curved risers and nosings",
    "T738_TILE_FLOOR": "the stair-core wall tile bounds keep the floor-level designer item C-SH-2 named",
    "T738_WASTE": "no tile / marble line carries a waste factor: size-based waste belongs to the materials stage",
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


def _status(s, w):
    base = str(s or "")
    if base not in STATUSES:
        raise InputsError(f"{w}: status {s!r} (DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED / HELD; never VERIFIED)")
    return base


def _entry(x, srcs):
    p, a = x.get("piece"), x.get("action")
    lid = x.get("line_id")
    w = f"{p}:{a} {lid or x.get('add_key')}"
    A3043._tasks(x, srcs, w)
    if p not in ACTIONS or a not in ACTIONS[p]:
        raise InputsError(f"{w}: piece / action not one of {ACTIONS}")
    e = dict(x, _status=_status(x.get("status"), w))
    A3063._need(x, ("why", "rule"), w)
    if a == "ADD_POINT":
        A3063._need(x, ("add_key", "host_line_id", "item_code", "unit", "value", "item"), w)
        if lid is not None or not A3063.LINE_ID_RE.match(str(x["host_line_id"])):
            raise InputsError(f"{w}: an added line names its host line, never a line id of its own")
        if CODES.get(x["item_code"]) != x["unit"] or x["item_code"] == TILE:
            raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a stair finish code of this version")
        e["_value"] = _d(x["value"], w, MAX_Q[x["unit"]])
        return e
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    A3063._need(x, ("expect",), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    if CODES.get(ex["item_code"]) != ex["unit"] or ex["class"] != "HELD" or \
            (p == P_TILE) != (ex["item_code"] == TILE):
        raise InputsError(f"{w}: {ex['item_code']} {ex['unit']} {ex['class']} is not a HELD line of this piece")
    top = MAX_Q[ex["unit"]]
    figs = [k for k in ("value", "low", "high") if x.get(k) is not None]
    if a == "POINT":
        e["_value"] = _d(x.get("value"), f"{w} value", top)
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a point carries one value")
    elif a == "BOUND":
        lo, hi = _d(x.get("low"), f"{w} low", top), _d(x.get("high"), f"{w} high", top)
        if lo > hi:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        e.update(_low=lo, _high=hi)
        if x.get("value") is not None:
            raise InputsError(f"{w}: a bound carries no value")
    elif a in BESIDE_KIND:
        if a == "AT_MOST" and x.get("value") is not None and D(str(x["value"])) == 0:
            raise InputsError(f"{w}: a cap of 0 states the quantity as 0: refused (R-T730-1 (4))")
        e["_value"] = _d(x.get("value"), f"{w} value", top)
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a figure beside a blank line, never a range")
        if a == "CONDITIONAL":
            if x.get("ruling") != RULING or ex["item_code"] not in SKIRT_SIBLING:
                raise InputsError(f"{w}: a CONDITIONAL figure is a stair skirting form on ruling {RULING} only")
    elif a == "EXCLUDE":
        if figs:
            raise InputsError(f"{w}: an excluded line carries no figure")
        if x.get("cause") not in EXCLUDE_CAUSES:
            raise InputsError(f"{w}: exclusion cause {x.get('cause')!r} (one of {EXCLUDE_CAUSES})")
        if (x["cause"] == "DUPLICATE_READING") != bool(x.get("carrier_line_id")):
            raise InputsError(f"{w}: a duplicate reading names its carrier line; a missing element none")
        if x.get("carrier_line_id") is not None and not A3063.LINE_ID_RE.match(str(x["carrier_line_id"])):
            raise InputsError(f"{w}: carrier line id")
        if x.get("carrier_line_id") == lid:
            raise InputsError(f"{w}: a line is not its own carrier")
    else:                                                   # NAMED
        if figs:
            raise InputsError(f"{w}: a NAMED line carries no figure")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3078_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"piece" TILE_BOUND | STAIR_WIRE, "action", "line_id" (or "add_key" + "host_line_id" for ADD_POINT),
                  "source_tasks", "rule", "status", "why", "expect" {item_code, element_id, unit, class HELD, low, high},
                  POINT: "value"; BOUND: "low", "high"; AT_LEAST / AT_MOST / CONDITIONAL: "value" (+ "ruling",
                  "sibling_line_id" for CONDITIONAL); EXCLUDE: "cause", "carrier_line_id"; NAMED: -;
                  ADD_POINT: "item_code", "unit", "value", "item", "element"; optional "supersedes" (records only)}],
     "statements": [...] (map rows that move nothing: KEEP, superseded, duplicate; records only),
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
    ids = [e.get("line_id") or f"ADD:{e['add_key']}" for e in ents]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement: R-T730-1 (2))")
    named = set(ids)
    for e in ents:
        if e["action"] == "EXCLUDE" and e.get("carrier_line_id") and \
                any(x.get("line_id") == e["carrier_line_id"] and x["action"] == "EXCLUDE" for x in ents):
            raise InputsError(f"{e['line_id']}: its carrier {e['carrier_line_id']} is excluded here too (R-T738-1 (c))")
        if e["action"] == "CONDITIONAL" and e.get("sibling_line_id") and e["sibling_line_id"] not in named:
            raise InputsError(f"{e['line_id']}: sibling form line {e['sibling_line_id']} is not wired with it")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def beside_of(ln):
    """the one-sided / conditional figure this version carries beside a line: (kind, value, ruling) or None"""
    r = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
    b = (r or {}).get("beside") or {}
    return (b["kind"], float(b["value"]), b.get("ruling")) if b.get("kind") else None


def _rec(srcs, **kw):
    return dict({"policy": PIECES[kw["piece"]]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _assert_before(b, e):
    x, w = e["expect"], f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == "HELD" and b.get("measured_net") is None)
    r = A3063._view_range(b)
    if ok and x.get("low") is not None:
        ok = b["evidence_state"] in (BOUNDED, BLANK) and r is not None and abs(r[0] - x["low"]) <= TOL and \
            abs(r[1] - x["high"]) <= TOL
    elif ok:
        ok = r is None
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} {r} "
                          f"is not the map's {x} (stale binding: re-read)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"{w}: the line already carries this version's record (applied twice)")


def _carrier(by, e, excluded):
    c = by.get(e["carrier_line_id"])
    b = by[e["line_id"]]
    w = f"EXCLUDE {e['line_id']}"
    if c is None or c["item_code"] != b["item_code"] or c["unit"] != b["unit"] or line_class(c) == "EXCLUDED" or \
            c["line_id"] in excluded:
        raise InputsError(f"{w}: carrier {e['carrier_line_id']} is not a live {b['item_code']} line (R-T738-1 (c))")
    ce = e.get("carrier_element_id")
    if ce and (c.get("location") or {}).get("element_id") != ce:
        raise InputsError(f"{w}: carrier {c['line_id']} is not the element the ledger names ({ce})")
    return c


def _restate(b, e, srcs, carrier=None):
    a, piece, u = e["action"], e["piece"], b["unit"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    why = str(e["why"])[:400]
    beside, after, extra = None, {}, {}
    if a in ("POINT", "BOUND"):
        lo, hi = (float(e["_value"]),) * 2 if a == "POINT" else (float(e["_low"]), float(e["_high"]))
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e['rule']}: {why}"[:200]}
        head = (f"HELD at the drawn figure {_fmt(lo)} {u} (low = high; held, not released)" if a == "POINT" else
                f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} {u}")
        after = {"low": _r(lo), "high": _r(hi)}
        ln["rfi"] = {"question": f"open: {e.get('open') or why}"[:400], "blocks": [b["line_id"]]}
    elif a == "EXCLUDE":
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = EXCLUDED_STATE, None, None, None
        ln["rfi"] = None
        if carrier is not None:
            head = (f"EXCLUDED (DUPLICATE_READING: the same physical flight is carried by {carrier['line_id']} "
                    f"{carrier['location']['element_id']})")
            extra = {"cause": "DUPLICATE_READING", "carrier_line_id": carrier["line_id"]}
        else:
            head = "EXCLUDED (NO_PHYSICAL_ELEMENT: the merged ledger finds no element for this line)"
            extra = {"cause": "NO_PHYSICAL_ELEMENT"}
        after = dict(excluded=extra["cause"], **({"carrier_line_id": carrier["line_id"]} if carrier else {}))
        ln["notes"] = (f"{METHOD}: EXCLUDED_WITH_REASON {extra['cause']}"
                       f"{' of ' + carrier['line_id'] if carrier else ''} ({e['rule']}): never valued, never 0 by "
                       f"omission; " + str(b.get("notes") or ""))[:600]
    elif a in BESIDE_KIND:
        v = float(e["_value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        beside = {"kind": BESIDE_KIND[a], "value": _r(v), "basis": why}
        if a == "CONDITIONAL":
            beside.update(ruling=RULING, sibling_line_id=e.get("sibling_line_id"))
            head = (f"HELD BLANK on ruling {RULING} (payable skirting form): this form's figure {_fmt(v)} {u} beside, "
                    f"conditional, never summed, never with its sibling form")
        elif a == "AT_LEAST":
            head = f"HELD, LOWER END ONLY (blank): at least {_fmt(v)} {u} beside, upper end open"
        else:
            head = f"HELD BLANK with a cap beside: at most {_fmt(v)} {u} (never a quantity, never 0)"
        after = {"beside": beside}
        ln["rfi"] = {"question": f"open: {e.get('open') or why}"[:400], "blocks": [b["line_id"]]}
    else:                                                   # NAMED
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        head = "HELD BLANK, CAUSE NAMED: no figure is formed"
        ln["rfi"] = {"question": f"open: {e.get('open') or why}"[:400], "blocks": [b["line_id"]]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e['rule']}: {why}"[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{b['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=piece, action=a, was=was, after=after, beside=beside, why=why, rule=e["rule"],
                        evidence_status=e["_status"], status_text=e.get("status_text"), supersedes=e.get("supersedes"),
                        **extra)
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def _add_line(host, e, srcs):
    from engine.source import boq_line as BL
    code, u = e["item_code"], e["unit"]
    if host["item_code"] != code or host["unit"] != u or line_class(host) == "EXCLUDED":
        raise InputsError(f"ADD_POINT {e['add_key']}: host {host['line_id']} is not a live {code} {u} line")
    loc = host.get("location") or {}
    eid = f"T738:ADD:{(loc.get('element_id') or '').split(':')[0]}#{e['add_key']}"
    v = float(e["_value"])
    why = str(e["why"])[:400]
    rec = _rec(srcs, piece=P_STAIR, action="ADD_POINT", host_line_id=host["line_id"], item=e["item"],
               element=e.get("element"), after={"low": _r(v), "high": _r(v)}, why=why, rule=e["rule"],
               evidence_status=e["_status"], status_text=e.get("status_text"))
    f = (f"{METHOD}: drawn piece no candidate line carries (T-715 new line), HELD at the drawn figure {_fmt(v)} {u} "
         f"(low = high; held, not released): {e['item']}; {e['rule']}: {why}")
    ln = BL.make_line(project_id=host["project"]["project_id"],
                      revision_set_sha256=host["project"]["revision_set_sha256"], item_code=code, unit=u,
                      evidence_state=BOUNDED, element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                      physical_element=str(e.get("element") or e["item"])[:200],
                      bounded_range={"low": _r(v), "high": _r(v), "basis": f"{e['rule']}: {why}"[:200]},
                      formula=f[:1500], inputs={REC_KEY: rec, "evidence_status": e["_status"]},
                      documents=copy.deepcopy(host["source"]["documents"]),
                      geometry_source=host["source"]["geometry_source"],
                      geometry_confidence=host["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state=host.get("material_state") or "BY_SPEC",
                      rfi={"question": f"open: {e.get('open') or why}"[:400], "blocks": [host["line_id"]]},
                      notes=f"own piece beside {host['line_id']} (never summed into it); HELD, never 0; NOT RELEASED",
                      subtrade=host.get("subtrade"), item_en=host.get("item_en"), item_ar=host.get("item_ar"),
                      trade=host.get("trade"))
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"ADD_POINT {e['add_key']}: the formula would conclude on a figure")
    return A3046._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T738", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.78 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    excluded = {e["line_id"] for e in doc["_entries"] if e["action"] == "EXCLUDE"}
    changes = []
    log = {"piece": "T738", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "statements": len(doc.get("statements") or ()),
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        srcs = [S[t] for t in e["source_tasks"]]
        k = f"{e['piece']}:{e['action']}"
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1
        common = dict(drawing_reference="; ".join(s["file"] for s in srcs), downstream=[],
                      verification=A3036._ver(srcs), evidence_status=e["_status"], step=e["action"])
        if e["action"] == "ADD_POINT":
            h = by.get(e["host_line_id"])
            if h is None:
                raise InputsError(f"ADD_POINT {e['add_key']}: host {e['host_line_id']} is not a candidate line")
            after = _add_line(h, e, srcs)
            if after["line_id"] in by:
                raise InputsError(f"ADD_POINT {e['add_key']}: the new id is already a candidate line")
            changes.append(A305._change(e["piece"], "ADD", None, after, group=after["item_code"],
                                        held=[{"what": after["line_id"], "why": str(e["why"])[:300],
                                               "range": [float(e["_value"])] * 2}], **common))
            continue
        b = by.get(e["line_id"])
        _assert_before(b, e)
        if e["action"] == "CONDITIONAL" and e.get("sibling_line_id"):
            s = by.get(e["sibling_line_id"])
            if s is None or s["item_code"] != SKIRT_SIBLING[b["item_code"]] or \
                    (s.get("location") or {}).get("element_id") != (b.get("location") or {}).get("element_id"):
                raise InputsError(f"CONDITIONAL {e['line_id']}: sibling {e['sibling_line_id']} is not the other form "
                                  f"of the same piece")
        car = _carrier(by, e, excluded) if e["action"] == "EXCLUDE" and e.get("carrier_line_id") else None
        after = _restate(b, e, srcs, car)
        q = A30._qty(after)
        held = [] if e["action"] == "EXCLUDE" else [{"what": e["line_id"], "why": str(e["why"])[:300],
                                                     "range": [q["low"], q["high"]] if q["low"] is not None else None,
                                                     "beside": after["calculation"]["inputs"][REC_KEY].get("beside")}]
        changes.append(A305._change(e["piece"], "CHANGE", b, after, group=b["item_code"], held=held, **common))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T738-1 (e): only the tile / stair finish codes move, each exactly by the changes; their released quantity never
    moves."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if CODES.get(k.split("|")[0]) != k.split("|")[1])
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the tile / stair finish codes: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if a is None and z is not None and z["lines"] == 0:     # every line of the code left it (excluded)
            a = {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 0}
        if z is None or a is None:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("released", "held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        if abs(a["released"] - (t0.get(k) or {}).get("released", 0.0)) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released quantity moved")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_78": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every V3.0.78 line is in the state its action names; a carrier is live; with `before`, no
    released line moved and no line became RELEASED. -> {piece:action: n}"""
    out = {}
    by = {x["line_id"]: x for x in lines}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a, p = rec["action"], rec["piece"]
        cls = line_class(ln)
        r = A3063._range(ln)
        bs = rec.get("beside") or {}
        if a == "POINT" or a == "ADD_POINT":
            ok = cls == "HELD" and r is not None and 0 < r[0] and abs(r[1] - r[0]) <= 1e-12 and not bs
        elif a == "BOUND":
            ok = cls == "HELD" and r is not None and 0 < r[0] <= r[1] + 1e-9 and not bs
        elif a in BESIDE_KIND:
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and \
                float(bs.get("value") or 0) > 0 and bs.get("kind") == BESIDE_KIND[a] and \
                (a != "CONDITIONAL" or (bs.get("ruling") == RULING and ln["item_code"] in SKIRT_SIBLING))
        elif a == "EXCLUDE":
            c = by.get(rec.get("carrier_line_id")) if rec.get("carrier_line_id") else None
            ok = ln["evidence_state"] == EXCLUDED_STATE and ln.get("measured_net") is None and \
                rec.get("cause") in EXCLUDE_CAUSES and \
                (rec["cause"] != "DUPLICATE_READING" or (c is not None and line_class(c) != "EXCLUDED" and
                                                         c["item_code"] == ln["item_code"]))
        elif a == "NAMED":
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and not bs
        else:
            ok = False
        ok = ok and CODES.get(ln["item_code"]) == ln["unit"] and rec["release_status"] == "NOT RELEASED" and \
            (p == P_TILE) == (ln["item_code"] == TILE)
        if ok and a != "EXCLUDE":
            ok = bool((ln.get("rfi") or {}).get("question"))
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} {a} line is not in its state")
        out[f"{p}:{a}"] = out.get(f"{p}:{a}", 0) + 1
    if old is not None:
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None:
                continue
            if (line_class(ln) == "RELEASED") != (line_class(o) == "RELEASED") or \
                    (line_class(o) == "RELEASED" and o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released quantity moved or a line became released")
    return out


def census(lines, codes=tuple(CODES)):
    """per code: released n / qty, bounded n / low .. high (points counted apart), blank n with the figures beside
    (AT_LEAST / AT_MOST / CONDITIONAL_ON_FORM: n and run-record sums, never summed into anything else), excluded n."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "points": 0, "low": 0.0, "high": 0.0, "blank": 0, "beside_n": {},
                               "beside_sum_run_record_only": {}, "excluded": 0})
        z["lines"] += 1
        k = line_class(ln)
        r = A3063._range(ln)
        if k == "EXCLUDED":
            z["excluded"] += 1
        elif k == "RELEASED":
            z["released"] += 1
            z["released_q"] += float(ln["measured_net"])
        elif r is not None:
            z["bounded"] += 1
            z["points"] += 1 if abs(r[1] - r[0]) <= 1e-12 else 0
            z["low"] += r[0]
            z["high"] += r[1]
        else:
            z["blank"] += 1
            b = beside_of(ln)
            if b:
                z["beside_n"][b[0]] = z["beside_n"].get(b[0], 0) + 1
                z["beside_sum_run_record_only"][b[0]] = z["beside_sum_run_record_only"].get(b[0], 0.0) + b[1]
    for z in out.values():
        for f in ("released_q", "low", "high"):
            z[f] = round(z[f], 6)
        z["beside_sum_run_record_only"] = {k: round(v, 6) for k, v in z["beside_sum_run_record_only"].items()}
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.78 lines, identity). Changed lines replace their candidate line in place, added lines follow the base;
    every other candidate line byte-identical (asserted); the earlier state checks re-run."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if CODES.get(a["item_code"]) != a["unit"]:
            raise ValueError(f"{METHOD}: {a['item_code']} {a['unit']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["line_id"] in sid or a["item_code"] not in STAIR_CODES:
                raise ValueError(f"{METHOD}: only stair finish pieces are added, never over a candidate id")
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
    v = A3077._older_view(out, prev)
    ident = {"base_lines": len(prev), "v3_0_78_lines": len(out), "v3_0_78_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(v),
             "concrete_v3_0_65": A3065.check_concrete(v), "concrete_v3_0_66": A3066.check_concrete(v),
             "concrete_v3_0_67": A3067.check_concrete(v, prev), "lintels_v3_0_67": A3067.check_lintels(v),
             "masonry_v3_0_68": A3068.check_masonry(v), "finishes_v3_0_69": A3069.check_finishes(v),
             "concrete_v3_0_70": A3070.check_concrete(v, prev), "lintels_v3_0_71": A3071.check_lintels(v, prev),
             "masonry_v3_0_72": A3072.check_masonry(v, prev), "concrete_v3_0_73": A3073.check_concrete(v, prev),
             "finishes_v3_0_74": A3074.check_finishes(v, prev), "formwork_concrete_v3_0_75":
                 A3075.check_lines(v, prev), "beads_ceiling_v3_0_76": A3076.check_lines(v, prev),
             "paint_rule_v3_0_77": A3077.check_lines(out, prev), "tile_stair": check_lines(out, prev),
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
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_78": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "beside": rec.get("beside"), "cause": rec.get("cause"),
                     "carrier_line_id": rec.get("carrier_line_id"), "supersedes": rec.get("supersedes"),
                     "evidence_status": c.get("evidence_status"), "status_text": rec.get("status_text"),
                     "still_held": c.get("held"), "rule": rec.get("rule"), "why": rec.get("why"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_78", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_78")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        if r.get("cause"):
            return f"EXCLUDED: {r['cause']}" + (f" (carrier {r['carrier_line_id']})" if r.get("carrier_line_id") else "")
        if not b:
            return "none"
        t = {"AT_LEAST": "at least", "AT_MOST": "at most"}.get(b["kind"], f"{b['kind']} {b.get('ruling')}")
        return f"{t} {_fmt(b['value'])}" + (f" (sibling {b['sibling_line_id']})" if b.get("sibling_line_id") else "")
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_78": q(r.get("after_v3_0_78")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_77"}, v3_0_78=d["v3_0_77"])
            for d in A3077.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_78_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    files = {"V3_0_78_BOQ_LINES.json": BL.dumps(new),
             "V3_0_78_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_78_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_78_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_78_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_78_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": dict(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "beside_of", "census", "check_lines", "check_totals", "expected_totals", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError", "line_class"]
