"""ARCH_TAKEOFF_V3.0.80 (T-750, lane I, WATERPROOFING + ROOF H4 integration package; owner gap order 2026-11-13 step
"waterproofing"): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.79 (engine.source.arch_v30, arch_v301 ..
arch_v3079), extended with TWO pieces built from Checker-merged research only, by line id as the merged T-748 readiness
map (R-T748-1, hub H4, rows NO_PACKAGE_ROW) names them. No line outside the waterproofing / roof-layer codes below moves;
no released quantity moves:

  WP_WIRE     (T-691 R-T691-2 / -3, restated by T-734 R-T734-3 where it declares it) every mapped HELD waterproofing line
              takes the ONE live statement of its merged ledger:
                POINT       HELD at one drawn figure (low = high): a drawn count (floor drains printed) or area; held,
                            never released here (only a Checker record releases);
                BOUND       HELD BOUNDED low .. high (0 < low <= high): e.g. 1 FD printed + the W.C. pan outlet open
                            (floor S-trap or wall P-trap printed nowhere) = 1 .. 2 pcs;
                ADD_POINT   a drawn piece no candidate line carries (the GF pantry wet room: its doorway membrane, its
                            doorway transition count, its open-side termination, its floor penetration) as a NEW HELD
                            point line of its code, keyed to its room, bound by id to a host line of the same code
                            (a template only: never summed into it);
                ADD_NAMED   a missing line whose quantity is printed nowhere (the pantry doorway transition m2): a NEW
                            HELD BLANK line with its cause named, never 0.
  ROOF_WIRE   (T-702 R-T702-3 roof layers) every mapped HELD roof-layer line stays HELD BLANK (the V3.0.31 roof
              build-up invariant: a roof layer line is MEASURED or BLOCKED_RFI, nothing between):
                AT_LEAST    the falls-screed volume's merged lower end beside (never a quantity, never in a total);
                NAMED       the cause the merged ledger names restated on the line (owner Q-34 parked top roof, D-39
                            insulation unprinted, protection carried by the one Q-41 screed line).

R-T750-1 (every villa): (a) a line is wired only from a Checker-merged ledger that names it by line id (or, for an ADD,
by room and code) through the merged readiness map; where two merged pieces state one line, only the one that DECLARES
the restatement is wired and the other is carried as a statement, never summed and never picked by size; (b) every
entry binds the candidate line as the map read it (item, element, unit, HELD, blank or the named range) and stops on a
stale line; an ADD's room must carry no live line of that code (one physical piece, one line); (c) counts are whole
numbers; a roof layer line never takes a figure (AT_LEAST beside only); (d) a downgrade never raises a released value
and nothing here releases: a released line named by the map moves only by a Checker record, otherwise it is a
statement; (e) only the codes of this version move, each exactly by the changes; released lines and every other line
byte-identical (asserted); the earlier state checks re-run on the result; (f) held stays held: nothing here is VERIFIED
or released; blank is never 0.
Files: V3_0_80_BOQ_LINES.json / .csv, V3_0_80_INTEGRATION_LEDGER.json / .csv, V3_0_80_DIFF.csv, V3_0_80_RUN.json.
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
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3068 as A3068
from engine.source import arch_v3077 as A3077
from engine.source import arch_v3078 as A3078
from engine.source import arch_v3079 as A3079

DEFAULT_GUARD_CLASS = "TOOLING"          # books Checker-merged waterproofing / roof-layer ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.80"
EXTENDS = A3079.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T750_ARCH_V3_0_80"
INPUTS_SCHEMA = "URBAN_V3080_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3080_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T750-1", "T-750"
REC_KEY = "wp_roof_gate_b_v3080"
WP_CODES = {"FIN.WP.PENETRATION": "pcs", "FIN.WP.WALL_UPTURN": "m2", "FIN.WP.DOORWAY": "m2",
            "FIN.WP.DOORWAY_TRANSITION_NR": "pcs", "FIN.WP.DOORWAY_TRANSITION": "m2", "FIN.WP.TERMINATION": "lm"}
ROOF_CODES = {A3031.SCREED: "m3", A3031.INSUL: "m2", A3031.PROT: "m2", A3031.FINISH: "m2"}
CODES = dict(WP_CODES, **ROOF_CODES)
P_WP, P_ROOF = "WP_WIRE", "ROOF_WIRE"
ACTIONS = {P_WP: ("POINT", "BOUND", "ADD_POINT", "ADD_NAMED"), P_ROOF: ("AT_LEAST", "NAMED")}
ADDS = ("ADD_POINT", "ADD_NAMED")
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
STATUSES = ("DRAWING-CONFIRMED", "HELD", "ASSUMED — OWNER-APPROVED")      # WORKFLOW_CONTROLS s.5; never VERIFIED
TOL = 1e-6
TOT_TOL = 5e-6
MAX_Q = {"m2": 200.0, "lm": 100.0, "pcs": 10.0, "m3": 50.0}   # one WP / roof-layer line above these is a unit slip
D = Decimal

PIECES = {
    P_WP: {"module": "engine/source/arch_v3080.py (the mapped HELD waterproofing lines of the merged T-691 ledger with "
                     "the T-734 restatement, by line id as mapped by T-748 hub H4: penetration counts as points / "
                     "bounds, the GF pantry wall upturn bounded, the four pantry pieces no line carries added as HELD "
                     "points and its doorway transition m2 added HELD blank)",
           "policy": "WP_GATE_B_V1", "rule_id": "R-T691-2 / R-T691-3, R-T734-3 (R-T750-1)",
           "owner_rules": ["Q-37 A (wet-room membrane to the box line; open side terminated, owner-approved)",
                           "Q-35 C (doorway transition counted per door; its m2 held until a detail prints it)",
                           "owner 2026-10-24 23:57 (downgrade only by a Checker record, never a raise)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
           "owner_manual_method": "wet room: floor membrane + wall upturn (run x upturn height less door gaps) + one "
                                  "transition per door + one penetration per floor outlet (drain, W.C. pan through the "
                                  "slab); edges where the membrane stops on an open side as lm",
           "drawing_method": "the room box line from the dimensioned plan (T-685 / T-691 own reads), drains counted "
                             "from the sanitary layout (FD printed), the W.C. pan outlet open (floor or wall outlet "
                             "printed on no sheet: the high end of each bound), the door gap x wall thickness for "
                             "the doorway membrane"},
    P_ROOF: {"module": "engine/source/arch_v3080.py (the mapped HELD roof-layer lines of the merged T-702 part (a) "
                       "ledger: the falls-screed lower end beside, the causes named; every roof layer line stays "
                       "HELD BLANK)",
             "policy": "ROOF_LAYER_GATE_B_V1", "rule_id": "R-T702-3 (R-T750-1)",
             "owner_rules": ["Q-41 (roof -> one falls / protection screed line, owner-approved scope)",
                             "Q-34 (2F top roof: PARKED by the owner, held by name)",
                             "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
             "owner_manual_method": "roof build-up per roof: falls screed m3 = area x mean thickness (minimum t0 + "
                                    "half the falls rise), insulation / protection / finish m2 by the membrane face",
             "drawing_method": "T-702 (a): finish hatch areas measured; the falls rise from the printed 1 % falls; "
                               "the minimum screed t0 and every layer thickness printed nowhere (D-39): screed AT "
                               "LEAST its falls volume, the other layers blank with their cause"},
}
WAITING = dict(A3079.WAITING)
WAITING.update({
    "T750_WC_OUTLET": "12 penetration lines stay HELD BOUNDED (low = floor drains printed, high + 1 per W.C. pan): the "
                      "W.C. pan outlet (floor S-trap or wall P-trap) is printed on no sheet (T-691 missing datum); a "
                      "wet-room / W.C. installation detail closes them",
    "T750_D41_SUNKEN": "D-41 sunken wet-room slab panels: membrane on the structural slab (tray: + loop x depth, 0 .. "
                       "13.335040 m2 over loop 51.8980 m) or on the fill under the tile (+0): DESIGNER_QUESTIONS item "
                       "9; no line formed, the six released wall-upturn hosts unchanged; never 0 by omission",
    "T750_D_BAND": "the 2F terrace membrane L-636fd3ff keeps its band 115.656474 .. 115.813974 m2 (Checker downgrade "
                   "record carried by V3.0.76): the 0.075 layer-D feature at the 2F west wall foot (D-BAND 0.1575 m2) "
                   "is printed nowhere; neither end chosen",
    "T750_Q34": "2F top roof (owner Q-34 PARKED, no roof plan D-62): its membrane, upturn, rolls and four roof-layer "
                "lines stay HELD BLANK by name",
    "T750_ROOF_LAYERS": "insulation (D-39 unprinted) and the minimum screed t0 wait the owner's company default values "
                        "(BOARD 2026-11-13 defaults list); protection is carried by the one Q-41 screed line",
    "T750_W09_W10": "the GF pantry wall upturn L-8090ff20 stays 1.400 .. 1.900 m2 until the W09 / W10 sills print (D-45)",
    "T750_IGNORED_SMALL": "owner materiality 2026-11-13 (below 1 % of its line, not worked): roof upturn L-5ce5ba49 "
                          "92.922 -> 92.925396 lm (+0.003396 lm, 0.004 %, a raise of a released value: no record, "
                          "stays released 92.922); pool-court ledge membrane L-2361d6ec 0 .. 0.639573 m2, ledge "
                          "upturn L-d7d1bf8c 0 .. 3.528277 lm (ledger 0.551614), window-run upturn L-1954878b 0 .. "
                          "0.500002 lm: left as they are",
})


# ================================================================================================ inputs
def _d(x, w, hi, unit):
    if isinstance(x, bool) or x is None:
        raise InputsError(f"{w}: not a number ({x!r})")
    try:
        v = D(str(x))
    except Exception:  # noqa: BLE001
        raise InputsError(f"{w}: not a number ({x!r})") from None
    if not v.is_finite() or v <= 0 or v > D(str(hi)):
        raise InputsError(f"{w}: {x!r} outside >0 .. {hi} (never 0, unit slip)")
    if unit == "pcs" and v != v.to_integral_value():
        raise InputsError(f"{w}: a count {x!r} is a whole number (R-T750-1 (c))")
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
    if a in ADDS:
        A3063._need(x, ("add_key", "host_line_id", "item_code", "unit", "item", "room", "floor"), w)
        if lid is not None or not A3063.LINE_ID_RE.match(str(x["host_line_id"])):
            raise InputsError(f"{w}: an added line names its host line, never a line id of its own")
        if WP_CODES.get(x["item_code"]) != x["unit"]:
            raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a waterproofing code of this version")
        if a == "ADD_POINT":
            e["_value"] = _d(x.get("value"), w, MAX_Q[x["unit"]], x["unit"])
        elif x.get("value") is not None:
            raise InputsError(f"{w}: a named (blank) added line carries no figure")
        return e
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    A3063._need(x, ("expect",), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    mine = WP_CODES if p == P_WP else ROOF_CODES
    if mine.get(ex["item_code"]) != ex["unit"] or ex["class"] != "HELD":
        raise InputsError(f"{w}: {ex['item_code']} {ex['unit']} {ex['class']} is not a HELD line of this piece "
                          f"(a released line moves only by a Checker record, R-T750-1 (d))")
    top, u = MAX_Q[ex["unit"]], ex["unit"]
    figs = [k for k in ("value", "low", "high") if x.get(k) is not None]
    if a == "POINT":
        e["_value"] = _d(x.get("value"), f"{w} value", top, u)
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a point carries one value")
    elif a == "BOUND":
        lo, hi = _d(x.get("low"), f"{w} low", top, u), _d(x.get("high"), f"{w} high", top, u)
        if lo > hi:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        e.update(_low=lo, _high=hi)
        if x.get("value") is not None:
            raise InputsError(f"{w}: a bound carries no value")
    elif a == "AT_LEAST":
        if ex["item_code"] != A3031.SCREED:
            raise InputsError(f"{w}: only the falls-screed volume carries a lower end beside")
        e["_value"] = _d(x.get("value"), f"{w} value", top, u)
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a figure beside a blank line, never a range")
    else:                                                   # NAMED
        if figs:
            raise InputsError(f"{w}: a NAMED line carries no figure")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3080_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"piece" WP_WIRE | ROOF_WIRE, "action", "line_id" (or "add_key" + "host_line_id" + "room" + "floor"
                  for an ADD), "source_tasks", "rule", "status", "why", "open", "expect" {item_code, element_id, unit,
                  class HELD, low, high}, POINT / AT_LEAST: "value"; BOUND: "low", "high"; NAMED / ADD_NAMED: -;
                  ADD_POINT: "item_code", "unit", "value", "item"; optional "supersedes" (records only)}],
     "statements": [...] (map rows that move nothing: KEEP, duplicate, ignored small; records only),
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
    ids = [e.get("line_id") or f"ADD:{e['item_code']}:{e['room']}" for e in ents]
    if len(set(ids)) != len(ids):
        raise InputsError("a line (or an added room piece) is named twice (one line, one statement: R-T750-1 (a))")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def beside_of(ln):
    """the lower end this version carries beside a roof screed line: (kind, value) or None"""
    r = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
    b = (r or {}).get("beside") or {}
    return (b["kind"], float(b["value"])) if b.get("kind") else None


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
        ok = r is not None and abs(r[0] - x["low"]) <= TOL and abs(r[1] - x["high"]) <= TOL
    elif ok:
        ok = r is None
    if ok and e["piece"] == P_ROOF:
        ok = b["evidence_state"] == BLANK and bool(((b.get("calculation") or {}).get("inputs") or {})
                                                   .get(A3031.REC_KEY))
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} {r} "
                          f"is not the map's {x} (stale binding: re-read)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"{w}: the line already carries this version's record (applied twice)")


def _restate(b, e, srcs):
    a, piece, u = e["action"], e["piece"], b["unit"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    why = str(e["why"])[:400]
    beside, after = None, {}
    if a in ("POINT", "BOUND"):
        lo, hi = (float(e["_value"]),) * 2 if a == "POINT" else (float(e["_low"]), float(e["_high"]))
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e['rule']}: {why}"[:200]}
        head = (f"HELD at the drawn figure {_fmt(lo)} {u} (low = high; held, not released)" if a == "POINT" else
                f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} {u}")
        after = {"low": _r(lo), "high": _r(hi)}
        ln["deductions"], ln["additions"] = [], []
    elif a == "AT_LEAST":
        v = float(e["_value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        beside = {"kind": "AT_LEAST", "value": _r(v), "basis": why}
        head = f"HELD, LOWER END ONLY (blank): at least {_fmt(v)} {u} beside, upper end open"
        after = {"beside": beside}
    else:                                                   # NAMED
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        head = "HELD BLANK, CAUSE NAMED: no figure is formed"
    ln["rfi"] = dict(b.get("rfi") or {}, question=f"open: {e.get('open') or why}"[:400], blocks=[b["line_id"]])
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e['rule']}: {why}"[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{b['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=piece, action=a, was=was, after=after, beside=beside, why=why, rule=e["rule"],
                        evidence_status=e["_status"], status_text=e.get("status_text"), supersedes=e.get("supersedes"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def add_element_id(e):
    return f"T750:ADD:{e['room']}#{e['add_key']}"


def _add_line(host, e, srcs):
    from engine.source import boq_line as BL
    code, u = e["item_code"], e["unit"]
    if host["item_code"] != code or host["unit"] != u or line_class(host) == "EXCLUDED":
        raise InputsError(f"{e['action']} {e['add_key']}: host {host['line_id']} is not a live {code} {u} line")
    why = str(e["why"])[:400]
    if e["action"] == "ADD_POINT":
        v = float(e["_value"])
        rng = {"low": _r(v), "high": _r(v), "basis": f"{e['rule']}: {why}"[:200]}
        state, after = BOUNDED, {"low": _r(v), "high": _r(v)}
        f = (f"{METHOD}: drawn piece no candidate line carries, HELD at the drawn figure {_fmt(v)} {u} (low = high; "
             f"held, not released): {e['item']}; {e['rule']}: {why}")
    else:
        rng, state, after = None, BLANK, {}
        f = (f"{METHOD}: missing piece no candidate line carries, HELD BLANK, CAUSE NAMED (no figure is formed): "
             f"{e['item']}; {e['rule']}: {why}")
    rec = _rec(srcs, piece=P_WP, action=e["action"], host_line_id=host["line_id"], item=e["item"], room=e["room"],
               after=after, why=why, rule=e["rule"], evidence_status=e["_status"], status_text=e.get("status_text"))
    ln = BL.make_line(project_id=host["project"]["project_id"],
                      revision_set_sha256=host["project"]["revision_set_sha256"], item_code=code, unit=u,
                      evidence_state=state, element_id=add_element_id(e), floor=e["floor"], room_id=e["room"],
                      physical_element=str(e.get("element") or e["item"])[:200], bounded_range=rng,
                      formula=f[:1500], inputs={REC_KEY: rec, "evidence_status": e["_status"]},
                      documents=copy.deepcopy(host["source"]["documents"]),
                      geometry_source=host["source"]["geometry_source"],
                      geometry_confidence=host["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state=host.get("material_state") or "BY_SPEC",
                      rfi={"question": f"open: {e.get('open') or why}"[:400], "blocks": []},
                      notes=f"own piece of room {e['room']}; template line {host['line_id']} (never summed into it); "
                            f"HELD, never 0; NOT RELEASED",
                      subtrade=host.get("subtrade"), item_en=host.get("item_en"), item_ar=host.get("item_ar"),
                      trade=host.get("trade"))
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['action']} {e['add_key']}: the formula would conclude on a figure")
    return A3046._fin(ln)


def _room_of(ln):
    loc = ln.get("location") or {}
    return loc.get("room_id") or str(loc.get("element_id") or "").split(":")[0]


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T750", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.80 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    live = {(ln["item_code"], _room_of(ln)) for ln in prev if line_class(ln) != "EXCLUDED"}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T750", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "statements": len(doc.get("statements") or ()),
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        srcs = [S[t] for t in e["source_tasks"]]
        k = f"{e['piece']}:{e['action']}"
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1
        common = dict(drawing_reference="; ".join(s["file"] for s in srcs), downstream=[],
                      verification=A3036._ver(srcs), evidence_status=e["_status"], step=e["action"])
        if e["action"] in ADDS:
            h = by.get(e["host_line_id"])
            if h is None:
                raise InputsError(f"{e['action']} {e['add_key']}: host {e['host_line_id']} is not a candidate line")
            if (e["item_code"], e["room"]) in live:
                raise InputsError(f"{e['action']} {e['add_key']}: room {e['room']} already carries a live "
                                  f"{e['item_code']} line (one physical piece, one line: R-T750-1 (b))")
            after = _add_line(h, e, srcs)
            if after["line_id"] in by:
                raise InputsError(f"{e['action']} {e['add_key']}: the new id is already a candidate line")
            q = A30._qty(after)
            changes.append(A305._change(e["piece"], "ADD", None, after, group=after["item_code"],
                                        held=[{"what": after["line_id"], "why": str(e["why"])[:300],
                                               "range": [q["low"], q["high"]] if q["low"] is not None else None}],
                                        **common))
            continue
        b = by.get(e["line_id"])
        _assert_before(b, e)
        after = _restate(b, e, srcs)
        q = A30._qty(after)
        changes.append(A305._change(e["piece"], "CHANGE", b, after, group=b["item_code"],
                                    held=[{"what": e["line_id"], "why": str(e["why"])[:300],
                                           "range": [q["low"], q["high"]] if q["low"] is not None else None,
                                           "beside": after["calculation"]["inputs"][REC_KEY].get("beside")}],
                                    **common))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T750-1 (e): only the waterproofing / roof-layer codes move, each exactly by the changes; their released
    quantity never moves."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if CODES.get(k.split("|")[0]) != k.split("|")[1])
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the waterproofing / roof-layer codes: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
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
        out[k] = {"base": t0.get(k), "v3_0_80": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every V3.0.80 line is in the state its action names; counts are whole; a roof layer line is
    blank; one added piece per (room, code); with `before`, no released line moved and no line became RELEASED.
    -> {piece:action: n}"""
    out, seen = {}, set()
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a, p = rec["action"], rec["piece"]
        cls = line_class(ln)
        r = A3063._range(ln)
        bs = rec.get("beside") or {}
        if a in ("POINT", "ADD_POINT"):
            ok = cls == "HELD" and r is not None and 0 < r[0] and abs(r[1] - r[0]) <= 1e-12 and not bs
        elif a == "BOUND":
            ok = cls == "HELD" and r is not None and 0 < r[0] <= r[1] + 1e-9 and not bs
        elif a == "AT_LEAST":
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and \
                float(bs.get("value") or 0) > 0 and bs.get("kind") == "AT_LEAST" and ln["item_code"] == A3031.SCREED
        elif a in ("NAMED", "ADD_NAMED"):
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and not bs
        else:
            ok = False
        mine = WP_CODES if p == P_WP else ROOF_CODES
        ok = ok and mine.get(ln["item_code"]) == ln["unit"] and rec["release_status"] == "NOT RELEASED" and \
            bool((ln.get("rfi") or {}).get("question"))
        if ok and ln["unit"] == "pcs" and r is not None:
            ok = all(abs(x - round(x)) <= 1e-9 for x in r)
        if ok and p == P_ROOF:
            ok = ln["evidence_state"] == BLANK
        if ok and a in ADDS:
            k = (ln["item_code"], rec.get("room"))
            ok = k not in seen
            seen.add(k)
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
    """per code: released n / qty, bounded n / low .. high (points counted apart), blank n with the lower ends beside
    (run-record sums only, never summed into anything else), excluded n."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "points": 0, "low": 0.0, "high": 0.0, "blank": 0, "at_least_n": 0,
                               "at_least_sum_run_record_only": 0.0, "excluded": 0})
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
                z["at_least_n"] += 1
                z["at_least_sum_run_record_only"] += b[1]
    for z in out.values():
        for f in ("released_q", "low", "high", "at_least_sum_run_record_only"):
            z[f] = round(z[f], 6)
    return out


# ================================================================================================ integrate / write
def older_view(lines, base):
    """the lines as the V3.0.64 .. V3.0.79 state checks see them: a line this version changed in its V3.0.79 form (the
    base line of the same id), the lines this version added left out. It must BE the base (asserted in integrate):
    the earlier checks then hold on it exactly as they held on the V3.0.79 run."""
    b = {ln["line_id"]: ln for ln in base}
    view = []
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            view.append(ln)
        elif rec["action"] not in ADDS:
            view.append(b[ln["line_id"]])
    return view


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.80 lines, identity). Changed lines replace their candidate line in place, added lines follow the base;
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
            if a["line_id"] in sid or a["item_code"] not in WP_CODES:
                raise ValueError(f"{METHOD}: only waterproofing pieces are added, never over a candidate id")
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
    v = older_view(out, prev)
    if len(v) != len(prev) or any(A30.line_sha(x) != A30.line_sha(y) for x, y in zip(v, prev)):
        raise ValueError(f"{METHOD}: the older-check view is not the base")
    roof = None
    if any(ln["item_code"] in ROOF_CODES for ln in out):
        try:                                                # the V3.0.31 invariant as it stood on the base ...
            A3031.check_roof_layers(prev)
        except ValueError as x:
            roof = {"base_fails_v3_0_31_check": str(x)[:300]}
        if roof is None:                                    # ... must still hold on the result
            roof = A3031.check_roof_layers(out)
    ident = {"base_lines": len(prev), "v3_0_80_lines": len(out), "v3_0_80_rows": len(changes), "replaced": len(repl),
             "added": len(add), "older_checks_view_is_base": True,
             "roof_buildup_v3_0_31": roof,
             "paint_rule_v3_0_77": A3077.check_lines(out, prev), "tile_stair_v3_0_78": A3078.check_lines(out, prev),
             "ext_render_paint_v3_0_79": A3079.check_lines(out, prev), "wp_roof": check_lines(out, prev),
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
                     "after_v3_0_80": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "beside": rec.get("beside"), "supersedes": rec.get("supersedes"),
                     "evidence_status": c.get("evidence_status"), "status_text": rec.get("status_text"),
                     "still_held": c.get("held"), "rule": rec.get("rule"), "why": rec.get("why"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_80", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_80")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        return f"at least {_fmt(b['value'])}" if b else "none"
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_80": q(r.get("after_v3_0_80")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_79"}, v3_0_80=d["v3_0_79"])
            for d in A3079.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_80_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    files = {"V3_0_80_BOQ_LINES.json": BL.dumps(new),
             "V3_0_80_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_80_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_80_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_80_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_80_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": dict(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "beside_of", "census", "check_lines", "check_totals", "expected_totals", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError", "line_class", "add_element_id"]
