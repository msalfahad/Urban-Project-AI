"""ARCH_TAKEOFF_V3.0.56 (T-508, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.55
(engine.source.arch_v30, arch_v301 .. arch_v3054, arch_v3055), with ONE new piece, the STAIR SKIRTING home of the merged
T-501 stair-side table (5eded7df; Checker own re-measure by handle: MS2-LD 3.700 lm, MS2-L W side sloped 2.737 / zigzag
3.694 lm AGREE; the 1F shaft 9.050 lm at +5.50 ENGINE_WRONG confirmed):

  STAIR_SKIRTING (a) RETIRE  the stretches of a room skirting line measured at a floor level along a stair shaft where no
                             floor of that level stands leave the room line (a deduction by name, the line still closes
                             gross - deductions + additions = net), ONLY when the stair pieces cover each stretch exactly
                             (plan union = the stretch, level-aware: no stair piece at the room floor's own level);
                             the room's held range over the same shaft (its windows) is NOT_APPLICABLE_WITH_EVIDENCE,
                             naming the pieces that carry its faces (no figure, never 0);
                 (b) LANDING   a level piece on a landing (wall face, drawn on the plans that bracket it) is room-trade
                             skirting (FIN.SKIRTING, register ruling STAIR SKIRTING vs ROOM SKIRTING): one valued line
                             per landing = the sum of its confirmed pieces (plan + column returns); a landing piece with
                             an opening whose sill / head is not printed gets its own HELD BLANK line by name;
                 (c) FLIGHT    a piece climbing with a flight (or a closing step) is stair skirting, B7-07 zigzag or
                             B7-08 sloped by the project's FORM (ORR-007). While the form is not chosen every piece has
                             TWO blank lines, one per form family (FIN.STAIR.SKIRTING.ZIGZAG / .SLOPED), each with its
                             own figure beside, never_additive_with each other: both shown, neither picked, never both
                             valued; a held / conflict / unknown piece keeps the same pair, blank with its cause.

R-T508-1 (every villa; integrates R-T501-1 .. 4 as merged, UP-STAIR-009 .. 011, UP-SKIRT-001 1.4.0, OWNER_RULE_STAIRS
2026-10-24 S-9, Q-72, UP-QTY-STATUS-001): (1) the form decides the family, never the side: 'wall' / 'open' as a form is
refused, an open side is no line; (2) one strip, one owner, level-aware: two pieces on one face meeting in stations AND
in level are refused; (3) a room stretch is retired only by closure (residual 0) and never where a stair piece stands at
the room floor's level; the moved length is never dropped (each covering piece has its own line); (4) a landing figure
is recomputed (plan + returns), a flight's sloped figure is recomputed from its stations and levels (hypot) and its
zigzag figure from plan + risers x riser (one riser per flight) + returns, each asserted equal to the table;
(5) held / unknown / conflict stays blank, never 0; millimetres refused.

Nothing else moves: every V3.0.55 line not named by the inputs is byte-identical (asserted); totals move only in
FIN.SKIRTING, FIN.STAIR.SKIRTING.ZIGZAG and FIN.STAIR.SKIRTING.SLOPED (asserted). Version number: built on V3.0.55
(T-488, merge e8143e40; first written as V3.0.55 on V3.0.54 and renumbered by the merge-order rule); V3.0.56 may also be
taken by T-310 in parallel (whichever merges later rebases and renumbers). Files: V3_0_56_BOQ_LINES.json / .csv,
V3_0_56_INTEGRATION_LEDGER.json / .csv, V3_0_56_DIFF.csv, V3_0_56_RUN.json. Nothing here names a project, a sheet, a
layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import math
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041
from engine.source import arch_v3042 as A3042
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3044 as A3044
from engine.source import arch_v3045 as A3045
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3047 as A3047
from engine.source import arch_v3050 as A3050
from engine.source import arch_v3051 as A3051
from engine.source import arch_v3053 as A3053
from engine.source import arch_v3054 as A3054
from engine.source import arch_v3055 as A3055

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books a Checker-merged table; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.56"
EXTENDS = A3055.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T508_ARCH_V3_0_56"
INPUTS_SCHEMA = "URBAN_V3056_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3056_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3051.InputsError
_r = A3050._r
_fmt = A3050._fmt
RULE_ID, RULE_VERSION = "R-T508-1", "T-508"
REC_KEY = "stair_skirting_v3056"
P_STAIR = "STAIR_SKIRTING"
ROOM_CODE, UNIT = "FIN.SKIRTING", "lm"
ZIG, SLO = "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.STAIR.SKIRTING.SLOPED"
FORM_CODE = {"zigzag": ZIG, "sloped": SLO}
FAMILY = {ZIG: "B7-07", SLO: "B7-08"}
ITEM_TEXT = {ZIG: ("Stair skirting zigzag", "توشيح متعرج"), SLO: ("Stair skirting sloped", "توشيح مائل")}
CODES = (ROOM_CODE, ZIG, SLO)
TRADE = "FLOOR_FINISH"                   # the trade of FIN.SKIRTING (engine.source.boq_line.ITEMS)
FLIGHT, LANDING, STEP = "FLIGHT", "LANDING", "STEP"
KINDS = (FLIGHT, LANDING, STEP)
WALL, HELD, CONFLICT, UNKNOWN = "WALL", "HELD", "CONFLICT", "UNKNOWN"
CLASSES = (WALL, HELD, CONFLICT, UNKNOWN)
CONFIRMED, FORM_HELD = "DRAWING-CONFIRMED", "HELD-FORM"
ACTIONS = ("RETIRE_ROOM_STRETCHES", "CLOSE_ROOM_RANGE", "ADD_LANDING", "ADD_LANDING_HELD", "ADD_FORM_PAIR")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
LANDING_STATE, HELD_STATE, NA_STATE = "MEASURED", "BLOCKED_RFI", "NOT_APPLICABLE_WITH_EVIDENCE"
RANGE_STATE = "BOUNDED_EXPOSURE"
TOL = 1e-5                               # a recomputed figure against the table (6 decimals, sums of rounded parts)
BIND_TOL = 0.0005                        # a candidate line against its expected figure (export tolerance)
CLOSE_TOL_M = 0.0005                     # R-T501-1 / -2 station tolerance
LEVEL_TOL_M = 0.001
MM_GUARD = 50.0                          # a length / level above it is millimetres (refused)
MIN_RISER, MAX_RISER = 0.10, 0.25
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
NON_FORMS = ("wall", "open", "wall side", "open side", "both", "average")

PIECES = {
    P_STAIR: {"module": "engine/source/arch_v3056.py (stair skirting home: room stretches along a shaft with no floor "
                        "at their level retired by closure to the stair pieces; landing pieces valued in FIN.SKIRTING; "
                        "flight pieces as a zigzag / sloped pair of blank lines until the form is chosen)",
              "policy": "STAIR_SKIRTING_HOME_V1", "rule_id": "R-T508-1 (on R-T501-1 .. 4)",
              "owner_rules": ["OWNER_RULE_STAIRS 2026-10-24 (S-9: no winder generated; release per item on its own "
                              "evidence)", "UP-STAIR-009 / -010 (zigzag) / -011 (sloped)", "UP-SKIRT-001 1.4.0",
                              "Q-72 (stair shafts at full exposed height)", "ORR-007 (form open: both shown)",
                              "UP-QTY-STATUS-001 (held is blank, never 0)"],
              "owner_manual_method": "zigzag = goings + rises along the wall side (UP-STAIR-010); sloped = the rake "
                                     "from the flight's plan run and total rise (UP-STAIR-011); landings and floors "
                                     "level, with the room skirting",
              "drawing_method": "merged T-501 stair-side table (5eded7df; Verifier 2026-11-04T10:56Z Gate A, own "
                                "re-measure by handle MS2-LD 3.700 lm and MS2-L W side 2.737 / 3.694 lm AGREE): face "
                                "stations of every piece read by handle, risers standing in it, level at each end; "
                                "the 1F room line's shaft stretches bound to the pieces at every level (residual 0)"},
}
WAITING = dict(A3055.WAITING)
for _k in ("T483_1F_SHAFT", "T443_1F_SHAFT"):   # bound by this version (R-T508-1 (3)); no longer waiting
    WAITING.pop(_k, None)
WAITING.update({
    "T508_FORM": "ORR-007: the stair skirting form (zigzag B7-07 / sloped B7-08) is not chosen: every flight piece "
                 "stays a blank pair with both figures beside; with the form chosen the pair's line of that form is "
                 "valued with no re-measure and the other is NOT_APPLICABLE",
    "T508_OPENINGS": "a window / opening in a stair or landing face whose sill / head against the flight or landing is "
                     "not printed stays HELD blank by name",
    "T508_CONFLICT": "a flight end where two drawings disagree (one more tread on the structural sheet) is a CONFLICT "
                     "piece, blank; the room line keeps its figure for those stations until the conflict is closed",
    "T508_WINDERS": "a winder corner (risers on the section vs wedges on the plans) is HELD: winders are never "
                    "generated (OWNER_RULE_STAIRS S-9)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _m(x, where, pos=False, null=False):
    if x is None and null:
        return None
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if abs(x) > MM_GUARD:
        raise InputsError(f"{where}: {x} looks like millimetres (metres required)")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def check_form(form):
    """R-T508-1 (1): the form is 'zigzag' or 'sloped' (ORR-007) or None (not chosen); a side is never a form."""
    if form is None:
        return None
    if str(form).strip().lower() in NON_FORMS or form not in FORM_CODE:
        raise InputsError(f"form {form!r}: only 'zigzag' (B7-07) or 'sloped' (B7-08) (ORR-007); a side is not a form")
    return form


def _piece(p, where):
    w = f"{where} {p.get('pid')}"
    _need(p, ("pid", "element", "face", "kind", "cls", "status", "floor", "source_tasks"), w)
    if p["kind"] not in KINDS:
        raise InputsError(f"{w}: kind {p['kind']!r} is not one of {KINDS} (an open side is no piece)")
    if p["cls"] not in CLASSES:
        raise InputsError(f"{w}: class {p['cls']!r} is not one of {CLASSES}")
    out = dict(p)
    out["_plan"] = _m(p.get("plan_lm"), f"{w} plan_lm")
    out["_ret"] = _m(p.get("returns_lm") or 0.0, f"{w} returns_lm")
    out["_s0"] = _m(p.get("s0"), f"{w} s0", null=True)
    out["_s1"] = _m(p.get("s1"), f"{w} s1", null=True)
    out["_l0"] = _m(p.get("level0"), f"{w} level0", null=True)
    out["_l1"] = _m(p.get("level1"), f"{w} level1", null=True)
    if (out["_s0"] is None) != (out["_s1"] is None) or (out["_l0"] is None) != (out["_l1"] is None):
        raise InputsError(f"{w}: stations / levels come in pairs")
    if out["_s0"] is not None and abs((out["_s1"] - out["_s0"]) - out["_plan"]) > TOL:
        raise InputsError(f"{w}: plan {out['_plan']} is not s1 - s0 {out['_s1'] - out['_s0']}")
    r = p.get("risers")
    if not isinstance(r, int) or isinstance(r, bool) or r < 0:
        raise InputsError(f"{w}: risers {r!r} is not a count")
    if p["cls"] in (HELD, CONFLICT, UNKNOWN) and not str(p.get("cause") or "").strip():
        raise InputsError(f"{w}: {p['cls']} without a cause")
    if p.get("value_lm") is not None and not (p["kind"] == LANDING and p["cls"] == WALL):
        raise InputsError(f"{w}: a {p['status']} piece carries a value (held is blank, never 0)")
    if p["kind"] == LANDING:
        if out["_l0"] is not None and abs(out["_l1"] - out["_l0"]) > LEVEL_TOL_M:
            raise InputsError(f"{w}: a landing piece with two levels")
        if r:
            raise InputsError(f"{w}: a landing piece with risers")
        if p["cls"] == WALL:
            if p["status"] != CONFIRMED:
                raise InputsError(f"{w}: a landing wall piece is {CONFIRMED}, not {p['status']}")
            out["_L"] = _r(out["_plan"] + out["_ret"])
            if p.get("value_lm") is None or abs(out["_L"] - p["value_lm"]) > TOL:
                raise InputsError(f"{w}: landing {p.get('value_lm')} lm is not plan + returns {out['_L']}")
            if out["_L"] <= 0:
                raise InputsError(f"{w}: a confirmed landing piece of 0 lm")
        elif p["status"] != p["cls"]:
            raise InputsError(f"{w}: a {p['cls']} landing piece is {p['cls']}, not {p['status']}")
        return out
    want = FORM_HELD if p["cls"] == WALL else p["cls"]
    if p["status"] != want:
        raise InputsError(f"{w}: a {p['kind']} {p['cls']} piece is {want} (form not chosen), not {p['status']}")
    zz, sl = p.get("zigzag_lm"), p.get("sloped_lm")
    out["_zz"] = None if zz is None else _m(zz, f"{w} zigzag_lm", pos=True)
    out["_sl"] = None if sl is None else _m(sl, f"{w} sloped_lm", pos=True)
    if p["kind"] == STEP:
        if out["_sl"] is not None or out["_plan"] != 0 or r < 1:
            raise InputsError(f"{w}: a closing step has risers, no plan run and no sloped figure")
    if p["cls"] == WALL and (out["_zz"] is None or out["_sl"] is None or r < 1):
        raise InputsError(f"{w}: a flight wall piece needs risers and both form figures")
    if out["_sl"] is not None and out["_l0"] is not None:
        rake = _r(math.hypot(out["_plan"], out["_l1"] - out["_l0"]) + out["_ret"])
        if abs(rake - out["_sl"]) > TOL:
            raise InputsError(f"{w}: sloped {out['_sl']} is not hypot(plan, level change) + returns {rake}")
        out["_sl_recomputed"] = True
    else:
        out["_sl_recomputed"] = False
    return out


def _risers(pieces):
    """R-T508-1 (4): one riser height per flight element, from the zigzag figures (plan + risers x riser + returns);
    every piece of the element must agree, and the riser must be a riser (0.10 .. 0.25 m)."""
    by = {}
    for p in pieces:
        if p["kind"] == FLIGHT and p["_zz"] is not None and p["risers"] > 0:
            by.setdefault(p["element"], []).append((p["_zz"] - p["_plan"] - p["_ret"]) / p["risers"])
    out = {}
    for e, xs in by.items():
        h = sum(xs) / len(xs)
        if any(abs(x - h) > TOL for x in xs):
            raise InputsError(f"flight {e}: its pieces imply riser heights {sorted(set(round(x, 6) for x in xs))} "
                              f"(one flight, one riser)")
        if not MIN_RISER <= h <= MAX_RISER:
            raise InputsError(f"flight {e}: riser {h} m is not a riser ({MIN_RISER} .. {MAX_RISER} m)")
        out[e] = _r(h)
    return out


def _band(p, a, b):
    lo, hi = sorted((p["_l0"], p["_l1"]))
    if p["kind"] != FLIGHT or p["_plan"] <= 0:
        return lo, hi

    def lv(s):
        return p["_l0"] + (p["_l1"] - p["_l0"]) * (s - p["_s0"]) / p["_plan"]
    return tuple(sorted((lv(a), lv(b))))


def _placed(pieces):
    return [p for p in pieces if p["_s0"] is not None and p["_l0"] is not None]


def check_one_owner(pieces):
    """R-T508-1 (2) = R-T501-1: two pieces on one face that overlap in stations AND meet in level are refused."""
    live = _placed(pieces)
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if a["face"] != b["face"]:
                continue
            lo, hi = max(a["_s0"], b["_s0"]), min(a["_s1"], b["_s1"])
            if hi - lo <= CLOSE_TOL_M:
                continue
            ba, bb = _band(a, lo, hi), _band(b, lo, hi)
            if max(ba[0], bb[0]) <= min(ba[1], bb[1]) + LEVEL_TOL_M:
                raise InputsError(f"two owners: {a['pid']} and {b['pid']} on {a['face']} over s {lo:.3f} .. {hi:.3f}")


def plan_union(pieces, face, a, b):
    iv = sorted((max(p["_s0"], a), min(p["_s1"], b)) for p in _placed(pieces)
                if p["face"] == face and min(p["_s1"], b) - max(p["_s0"], a) > CLOSE_TOL_M)
    tot, c0, c1 = 0.0, None, None
    for x0, x1 in iv:
        if c1 is None or x0 > c1 + CLOSE_TOL_M:
            if c1 is not None:
                tot += c1 - c0
            c0, c1 = x0, x1
        else:
            c1 = max(c1, x1)
    if c1 is not None:
        tot += c1 - c0
    return tot


def bind_stretch(seg, pieces, floor_level):
    """R-T508-1 (3) = R-T501-2: the stair pieces cover the room stretch exactly and none stands at the room floor's
    level inside it. -> the pieces that carry it."""
    w = f"stretch {seg['segment']}"
    s0, s1 = seg["_s0"], seg["_s1"]
    owners = [p for p in _placed(pieces) if p["face"] == seg["face"] and
              min(p["_s1"], s1) - max(p["_s0"], s0) > CLOSE_TOL_M]
    for p in owners:
        lo, hi = _band(p, max(p["_s0"], s0), min(p["_s1"], s1))
        flat = hi - lo <= LEVEL_TOL_M
        if (flat and abs(lo - floor_level) <= LEVEL_TOL_M) or \
                (not flat and lo + LEVEL_TOL_M < floor_level < hi - LEVEL_TOL_M):
            raise InputsError(f"{w}: stair piece {p['pid']} stands at the room floor's level {floor_level}: the floor "
                              f"is there, the room skirting is not retired")
    cov = plan_union(owners, seg["face"], s0, s1)
    if abs(cov - (s1 - s0)) > CLOSE_TOL_M:
        raise InputsError(f"{w}: the stair pieces cover {_r(cov)} of {_r(s1 - s0)} m (residual "
                          f"{_r(s1 - s0 - cov)}: the uncovered part stays in the room line; not retired)")
    named = set(seg.get("owners") or ())
    got = {p["pid"] for p in owners}
    if named and named != got:
        raise InputsError(f"{w}: the table names owners {sorted(named)}, the stations give {sorted(got)}")
    return sorted(owners, key=lambda q: (q["_s0"], q["_l0"]))


def load_inputs(doc, project_id=None):
    """URBAN_V3056_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "form": null | "zigzag" | "sloped" (ORR-007),
     "pieces": [{"pid", "element", "face", "kind" FLIGHT / LANDING / STEP, "cls" WALL / HELD / CONFLICT / UNKNOWN,
                 "status", "floor", "s0", "s1", "plan_lm", "risers", "returns_lm", "level0", "level1", "value_lm",
                 "zigzag_lm", "sloped_lm", "cause", "evidence", "source_tasks"}],
     "retire": {"room_line_id", "floor_level", "expect": {"evidence_state", "gross", "measured_net"},
                "stretches": [{"segment", "face", "s0", "s1", "returns_lm", "status_before" certain / held range,
                               "owners": [pid]}],
                "range_line_id", "range_expect": {"low", "high"}, "source_tasks"} | null}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    form = check_form(doc.get("form"))
    pieces, pids = [], set()
    for p in doc.get("pieces") or ():
        A3043._tasks(p, srcs, f"piece {p.get('pid')}")
        x = _piece(p, "piece")
        if x["pid"] in pids:
            raise InputsError(f"piece {x['pid']} named twice")
        pids.add(x["pid"])
        pieces.append(x)
    if not pieces:
        raise InputsError("no stair skirting piece in the inputs")
    check_one_owner(pieces)
    risers = _risers(pieces)
    ret = doc.get("retire")
    if ret:
        w = "retire"
        _need(ret, ("room_line_id", "floor_level", "expect", "stretches", "source_tasks"), w)
        A3043._tasks(ret, srcs, w)
        _lid(ret["room_line_id"], w)
        lvl = _m(ret["floor_level"], f"{w} floor_level")
        segs, keys = [], set()
        for s in ret["stretches"]:
            ww = f"{w} stretch {s.get('segment')}"
            _need(s, ("segment", "face", "status_before"), ww)
            x = dict(s, _s0=_m(s.get("s0"), f"{ww} s0"), _s1=_m(s.get("s1"), f"{ww} s1"),
                     _ret=_m(s.get("returns_lm") or 0.0, f"{ww} returns_lm"))
            if x["_s1"] - x["_s0"] <= CLOSE_TOL_M or (x["face"], x["_s0"]) in keys:
                raise InputsError(f"{ww}: empty or named twice")
            keys.add((x["face"], x["_s0"]))
            if x["status_before"] not in ("certain", "held range"):
                raise InputsError(f"{ww}: status_before {x['status_before']!r} is 'certain' or 'held range'")
            x["_owners"] = bind_stretch(x, pieces, lvl)
            segs.append(x)
        if any(s["status_before"] == "held range" for s in segs):
            _lid(ret.get("range_line_id"), w)
            _need(ret, ("range_expect",), w)
        ret = dict(ret, _level=lvl, _segs=segs,
                   _certain=_r(sum(s["_s1"] - s["_s0"] + s["_ret"] for s in segs if s["status_before"] == "certain")),
                   _range=_r(sum(s["_s1"] - s["_s0"] + s["_ret"] for s in segs if s["status_before"] == "held range")))
    return dict(doc, _sources=srcs, _form=form, _pieces=pieces, _risers=risers, _retire=ret or None)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_STAIR, "policy": PIECES[P_STAIR]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _inputs(ln):
    c = ln["calculation"] = dict(ln.get("calculation") or {})
    c["inputs"] = dict(c.get("inputs") or {})
    return c["inputs"]


def _blank(ln):
    return ln.get("measured_net") is None and not ln.get("bounded_range") and ln.get("gross") is None


def _sum(items):
    return sum(float(x.get("qty") or 0) for x in items or () if isinstance(x, dict))


def _prec(p):
    return {"pid": p["pid"], "element": p["element"], "face": p["face"], "kind": p["kind"], "cls": p["cls"],
            "status": p["status"], "s0": p["_s0"], "s1": p["_s1"], "plan_lm": p["_plan"], "risers": p["risers"],
            "returns_lm": p["_ret"], "level0": p["_l0"], "level1": p["_l1"], "value_lm": p.get("_L"),
            "zigzag_lm": p.get("_zz"), "sloped_lm": p.get("_sl"), "sloped_recomputed": p.get("_sl_recomputed"),
            "cause": str(p.get("cause") or "")[:300], "evidence": str(p.get("evidence") or "")[:300]}


def _new_line(tpl, *, code, eid, floor, state, net, what, formula, rec, rfi=None, notes, nonadd=()):
    from engine.source import boq_line as BL
    en, ar = ITEM_TEXT.get(code, (None, None))
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=code, unit=UNIT, evidence_state=state, measured_net=net, gross=net, element_id=eid, floor=floor,
        physical_element=what, formula=formula[:1500], inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "BY_SPEC", rfi=rfi, notes=notes, never_additive_with=nonadd,
        item_en=en, item_ar=ar, trade=None if code == ROOM_CODE else TRADE)
    return A3046._fin(ln)


def pair_ids(tpl, p):
    """the two line ids of a flight / step piece's form pair (line ids are content keys: computed before either line)."""
    from engine.source import boq_line as BL
    pid = tpl["project"]["project_id"]
    return {c: BL.line_id(pid, c, f"STAIR-SKIRT:{p['pid']}", RULE_ID, RULE_VERSION, UNIT) for c in (ZIG, SLO)}


def _pair(tpl, p, form, srcs):
    """R-T508-1 (1) / (5): the zigzag and the sloped line of one piece; valued only for the chosen form of a WALL
    piece; the other form NOT_APPLICABLE; blank otherwise."""
    ids = pair_ids(tpl, p)
    out = []
    for code in (ZIG, SLO):
        fig = p["_zz"] if code == ZIG else p["_sl"]
        frm = "zigzag" if code == ZIG else "sloped"
        what = (f"stair skirting piece {p['pid']} ({p['element']} {p['kind'].lower()}, {p['face']}), "
                f"form {frm} ({FAMILY[code]})")
        beside = f"{_fmt(fig)} lm" if fig is not None else "not defined"
        other = ids[SLO if code == ZIG else ZIG]
        if p["cls"] == WALL and form is not None:
            if form == frm:
                state, net, st = LANDING_STATE, fig, CONFIRMED
                formula = (f"{METHOD}: {what}: {frm} = {_fmt(fig)} lm (plan {_fmt(p['_plan'])}, {p['risers']} "
                           f"riser(s), returns {_fmt(p['_ret'])}; form {form} chosen, ORR-007) ({RULE_ID})")
                notes, rfi = f"{METHOD}: {FAMILY[code]} valued, form {form}; NOT RELEASED", None
            else:
                state, net, st = NA_STATE, None, CONFIRMED
                formula = f"NOT_APPLICABLE: form {form} chosen (ORR-007); the {frm} figure {beside} is not built"
                notes, rfi = f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: the project form is {form}", None
        else:
            st = p["status"]
            why = ("ORR-007: the stair skirting form (zigzag B7-07 / sloped B7-08) is not chosen" if p["cls"] == WALL
                   else str(p["cause"]))
            state, net = HELD_STATE, None
            formula = (f"{METHOD}: HELD BLANK (never a value, never 0) {what}, {st}: {why}; {frm} figure beside "
                       f"{beside}, never additive with its {('sloped' if code == ZIG else 'zigzag')} pair line "
                       f"({RULE_ID})")
            notes = f"{METHOD}: {st} by name, blank (never 0); both forms shown, neither picked; NOT RELEASED"
            rfi = {"question": f"{what}: {why}"[:900], "unlocks": f"STAIR-SKIRT:{p['pid']}"}
        rec = _rec(srcs, action="ADD_FORM_PAIR", form_code=code, family=FAMILY[code], form_chosen=form,
                   pair_line=other, figure_beside_lm=fig, stair_piece=_prec(p), evidence_status=st)
        ln = _new_line(tpl, code=code, eid=f"STAIR-SKIRT:{p['pid']}", floor=p["floor"], state=state, net=net,
                       what=what, formula=formula, rec=rec, rfi=rfi, notes=notes, nonadd=(other,))
        if ln["line_id"] != ids[code]:
            raise ValueError(f"{METHOD}: pair id {ln['line_id']} is not the precomputed {ids[code]}")
        out.append(ln)
    return out


def _landing(tpl, element, ps, srcs):
    L = _r(sum(p["_L"] for p in ps))
    floor = ps[0]["floor"]
    parts = " + ".join(f"{p['pid']} {_fmt(p['_plan'])}" + (f" + returns {_fmt(p['_ret'])}" if p["_ret"] else "")
                       for p in ps)
    what = f"landing skirting {element} (level, wall faces)"
    rec = _rec(srcs, action="ADD_LANDING", element=element, length_lm=L, pieces=[_prec(p) for p in ps],
               evidence_status=CONFIRMED)
    ln = _new_line(tpl, code=ROOM_CODE, eid=f"STAIR-SKIRT:{element}:landing", floor=floor, state=LANDING_STATE,
                   net=L, what=what, formula=f"{METHOD}: {what}: {parts} = {_fmt(L)} lm ({RULE_ID})", rec=rec,
                   notes=f"{METHOD}: landing skirting {element} {_fmt(L)} lm DRAWING-CONFIRMED; NOT RELEASED")
    return ln, L


def _landing_held(tpl, p, srcs):
    what = f"landing skirting piece {p['pid']} ({p['element']}, {p['face']})"
    rec = _rec(srcs, action="ADD_LANDING_HELD", element=p["element"], stair_piece=_prec(p),
               evidence_status=p["status"])
    return _new_line(tpl, code=ROOM_CODE, eid=f"STAIR-SKIRT:{p['pid']}", floor=p["floor"], state=HELD_STATE, net=None,
                     what=what, formula=(f"{METHOD}: HELD BLANK (never a value, never 0) {what}, {p['status']}: "
                                         f"{p['cause']}; plan {_fmt(p['_plan'])} m beside ({RULE_ID})"), rec=rec,
                     rfi={"question": f"{what}: {p['cause']}"[:900], "unlocks": f"STAIR-SKIRT:{p['pid']}"},
                     notes=f"{METHOD}: {p['status']} by name, blank (never 0); NOT RELEASED")


def _retired_room(b, ret, homes, srcs):
    lid = b["line_id"]
    e = ret["expect"]
    if b["item_code"] != ROOM_CODE or b["unit"] != UNIT:
        raise InputsError(f"retire {lid}: not a {ROOM_CODE} {UNIT} line of the candidate (stale binding)")
    if b["evidence_state"] not in VALUED_STATES or b.get("measured_net") is None or \
            not isinstance(b.get("gross"), (int, float)) or b["evidence_state"] != e.get("evidence_state") or \
            abs(b["measured_net"] - e["measured_net"]) > BIND_TOL or abs(b["gross"] - e["gross"]) > BIND_TOL:
        raise InputsError(f"retire {lid}: {b['evidence_state']} gross {b.get('gross')} net {b.get('measured_net')} is "
                          f"not the table's {e} (stale binding)")
    if (b.get("location") or {}).get("floor") is None:
        raise InputsError(f"retire {lid}: the room line has no floor")
    gone = ret["_certain"]
    if gone <= 0:
        raise InputsError(f"retire {lid}: no certain stretch to retire")
    net = _r(b["measured_net"] - gone)
    if net < -TOL:
        raise InputsError(f"retire {lid}: retiring {gone} lm from {b['measured_net']} lm leaves a negative net")
    new = copy.deepcopy(b)
    segs = [s for s in ret["_segs"] if s["status_before"] == "certain"]
    item = {"id": "STAIR-SHAFT-NO-FLOOR", "unit": UNIT, "qty": gone, "kind": "STAIR_SHAFT_NO_FLOOR_AT_LEVEL",
            "rule_id": RULE_ID, "source": f"{METHOD} (stair pieces at their own levels)",
            "why": f"no floor at {_fmt(ret['_level'])} along these shaft stretches: the skirting there is the stair "
                   f"and landing pieces at their own levels, each its own line",
            "stretches": [{"segment": s["segment"], "face": s["face"], "s0": s["_s0"], "s1": s["_s1"],
                           "returns_lm": s["_ret"], "lm": _r(s["_s1"] - s["_s0"] + s["_ret"]),
                           "carried_by": [p["pid"] for p in s["_owners"]]} for s in segs]}
    new["deductions"] = list(new.get("deductions") or []) + [item]
    new["measured_net"] = net
    if abs(new["gross"] - _sum(new["deductions"]) + _sum(new.get("additions")) - net) > TOL:
        raise InputsError(f"retire {lid}: gross - deductions + additions is not the new net {net}")
    stx = "; ".join(f"{s['segment']} {_fmt(_r(s['_s1'] - s['_s0'] + s['_ret']))}" for s in segs)
    new["calculation"]["formula"] = (f"{b['calculation'].get('formula') or ''}; {METHOD}: - {_fmt(gone)} lm stair-shaft "
                                     f"stretches with no floor at {_fmt(ret['_level'])} ({stx}), carried by the stair "
                                     f"/ landing piece lines = {_fmt(net)} lm")[:1500]
    _inputs(new)[REC_KEY] = _rec(srcs, action="RETIRE_ROOM_STRETCHES", was={"measured_net": b["measured_net"]},
                                 retired_lm=gone, floor_level=ret["_level"], stretches=item["stretches"],
                                 home_lines=sorted(homes), evidence_status=CONFIRMED)
    A305._note(new, f"{METHOD}: shaft stretches {_fmt(gone)} lm retired (no floor at their level): net "
                    f"{_fmt(b['measured_net'])} -> {_fmt(net)} lm; NOT RELEASED")
    return A3046._fin(new)


def _closed_range(rg, ret, homes, srcs):
    lid = rg["line_id"]
    br, e = rg.get("bounded_range") or {}, ret["range_expect"]
    if rg["item_code"] != ROOM_CODE or rg["unit"] != UNIT or rg["evidence_state"] != RANGE_STATE or \
            rg.get("measured_net") is not None or abs((br.get("low") or 0) - e["low"]) > BIND_TOL or \
            abs((br.get("high") or 0) - e["high"]) > BIND_TOL:
        raise InputsError(f"range line {lid}: {rg['evidence_state']} {br.get('low')} .. {br.get('high')} is not the "
                          f"table's held range {e['low']} .. {e['high']} (stale binding)")
    if abs(br["high"] - ret["_range"]) > TOL:
        raise InputsError(f"range line {lid}: the shaft stretches take {ret['_range']} lm of a held high {br['high']} "
                          f"(a range is closed only whole)")
    segs = [s for s in ret["_segs"] if s["status_before"] == "held range"]
    text = (f"held range over stair-shaft window stretches with no floor at {_fmt(ret['_level'])}: "
            + "; ".join(f"{s['segment']} carried by {' '.join(p['pid'] for p in s['_owners'])}" for s in segs))
    new = copy.deepcopy(rg)
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    new["evidence_state"], new["bounded_range"], new["rfi"] = NA_STATE, None, None
    new["calculation"]["formula"] = (f"NOT_APPLICABLE: {text} ({METHOD}); was range {_fmt(was['low'])} .. "
                                     f"{_fmt(was['high'])}")[:1500]
    _inputs(new)[REC_KEY] = _rec(srcs, action="CLOSE_ROOM_RANGE", was=was, closed_lm=ret["_range"],
                                 stretches=[{"segment": s["segment"], "carried_by": [p["pid"] for p in s["_owners"]]}
                                            for s in segs], home_lines=sorted(homes), evidence_status=CONFIRMED)
    A305._note(new, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: {text}"[:400])
    return A3046._fin(new)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). ADD: landing lines, held landing lines, form pairs; CHANGE: the room line, its range."""
    if not doc:
        return [], {"piece": P_STAIR, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.56 records (applied once)")
    if any(ln["item_code"] in (ZIG, SLO) for ln in prev):
        raise InputsError("the candidate already carries stair skirting form lines")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    form = doc["_form"]
    changes, ids = [], set(by)
    log = {"piece": P_STAIR, "state": "RUN", "sources": doc["sources"], "form": form, "by_action": {},
           "landings": {}, "landing_lm": 0.0, "landing_held": [], "pairs": 0, "form_beside": {"zigzag_lm": 0.0,
           "sloped_lm": 0.0, "wall_pieces": 0, "risers": 0}, "held_pieces": [], "retired_lm": 0.0,
           "closed_range_lm": 0.0, "risers_by_flight": doc["_risers"]}
    tpl = next((ln for ln in prev if ln["item_code"] == ROOM_CODE), None)
    if tpl is None:
        raise InputsError(f"no {ROOM_CODE} line in the candidate to take the source documents from")

    def add(action, after, before, srcs, ev, held, down):
        if before is not None and before["line_id"] != after["line_id"]:
            raise ValueError(f"{METHOD}: a changed line keeps its id")
        if before is None:
            if after["line_id"] in ids:
                raise ValueError(f"{METHOD}: an added line {after['line_id']} repeats an id")
            ids.add(after["line_id"])
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        changes.append(A305._change(P_STAIR, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), evidence_status=ev, held=held, downstream=down,
                                    group=after["item_code"]))

    pieces = doc["_pieces"]
    homes = {}
    lands = {}
    for p in pieces:
        if p["kind"] == LANDING and p["cls"] == WALL:
            lands.setdefault(p["element"], []).append(p)
    for el in sorted(lands):
        ps = lands[el]
        srcs = [S[t] for t in sorted({t for p in ps for t in p["source_tasks"]})]
        ln, L = _landing(tpl, el, ps, srcs)
        add("ADD_LANDING", ln, None, srcs, CONFIRMED, [], [f"FIN.SKIRTING +{_fmt(L)} lm (landing {el})"])
        for p in ps:
            homes[p["pid"]] = ln["line_id"]
        log["landings"][el] = L
        log["landing_lm"] = _r(log["landing_lm"] + L)
    for p in pieces:
        srcs = [S[t] for t in p["source_tasks"]]
        if p["kind"] == LANDING:
            if p["cls"] == WALL:
                continue
            ln = _landing_held(tpl, p, srcs)
            add("ADD_LANDING_HELD", ln, None, srcs, p["status"],
                [{"what": p["pid"], "why": p["cause"], "range": None, "scenario": "held blank"}],
                ["FIN.SKIRTING: blocked-line count +1; no figure moves"])
            homes[p["pid"]] = ln["line_id"]
            log["landing_held"].append(p["pid"])
            continue
        pair = _pair(tpl, p, form, srcs)
        for ln in pair:
            add("ADD_FORM_PAIR", ln, None, srcs, p["status"] if form is None or p["cls"] != WALL else CONFIRMED,
                [] if (form is not None and p["cls"] == WALL) else
                [{"what": p["pid"], "why": p.get("cause") or "ORR-007 form", "range": None, "scenario": "held blank"}],
                [f"{ln['item_code']}: one line of the {p['pid']} form pair"])
        homes[p["pid"]] = pair[0]["line_id"]
        log["pairs"] += 1
        if p["cls"] == WALL:
            fb = log["form_beside"]
            fb["zigzag_lm"] = _r(fb["zigzag_lm"] + p["_zz"])
            fb["sloped_lm"] = _r(fb["sloped_lm"] + p["_sl"])
            fb["wall_pieces"] += 1
            fb["risers"] += p["risers"] if p["kind"] == FLIGHT else 0
        else:
            log["held_pieces"].append(f"{p['pid']} {p['status']}")
    ret = doc["_retire"]
    if ret:
        srcs = [S[t] for t in ret["source_tasks"]]
        carried = sorted({homes[p["pid"]] for s in ret["_segs"] for p in s["_owners"]})
        b = by.get(ret["room_line_id"])
        if b is None:
            raise InputsError(f"retire {ret['room_line_id']}: not a line of the candidate (stale binding)")
        if ret["_certain"] > 0:
            add("RETIRE_ROOM_STRETCHES", _retired_room(b, ret, carried, srcs), b, srcs, CONFIRMED, [],
                [f"FIN.SKIRTING -{_fmt(ret['_certain'])} lm (moved to the stair / landing piece lines)"])
            log["retired_lm"] = ret["_certain"]
        if ret["_range"] > 0:
            rg = by.get(ret.get("range_line_id"))
            if rg is None:
                raise InputsError(f"retire: range line {ret.get('range_line_id')} not in the candidate (stale)")
            add("CLOSE_ROOM_RANGE", _closed_range(rg, ret, carried, srcs), rg, srcs, CONFIRMED, [],
                [f"FIN.SKIRTING held range -{_fmt(ret['_range'])} lm (faces carried by the piece lines)"])
            log["closed_range_lm"] = ret["_range"]
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_stair_skirting(lines):
    """R-T508-1 on the integrated lines: every form pair complete (two lines, one per form, never_additive_with each
    other, never both valued; blank unless the form is chosen); a landing line = the sum of its confirmed pieces; a
    held landing / pair line BLOCKED_RFI blank with its question; the room line closes and fell by exactly its retired
    stretches; a closed range is NOT_APPLICABLE with no figure; every carrier named exists. -> summary."""
    out = {"landings": 0, "landing_lm": 0.0, "landing_held": 0, "pairs": 0, "valued_pairs": 0, "retired_lm": 0.0,
           "closed": 0}
    by = {ln["line_id"]: ln for ln in lines}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] in (ZIG, SLO):
                raise ValueError(f"{METHOD}: stair skirting line {ln['line_id']} without its record")
            continue
        if ln["item_code"] not in CODES or ln["unit"] != UNIT:
            raise ValueError(f"{METHOD}: a V3.0.56 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        if act == "ADD_FORM_PAIR":
            o = by.get(rec.get("pair_line"))
            orec = ((o or {}).get("calculation") or {}).get("inputs", {}).get(REC_KEY) if o else None
            if o is None or not orec or orec.get("pair_line") != ln["line_id"] or o["item_code"] == ln["item_code"] \
                    or {o["item_code"], ln["item_code"]} != {ZIG, SLO} or rec["pair_line"] not in ln["never_additive_with"]:
                raise ValueError(f"{METHOD}: form pair of {ln['line_id']} incomplete or not never-additive")
            if ln["evidence_state"] in VALUED_STATES and o["evidence_state"] in VALUED_STATES:
                raise ValueError(f"{METHOD}: both forms valued for piece {rec['stair_piece']['pid']}")
            if rec.get("form_chosen") is None:
                if ln["evidence_state"] != HELD_STATE or not _blank(ln) or not (ln.get("rfi") or {}).get("question"):
                    raise ValueError(f"{METHOD}: pair line {ln['line_id']} is not BLOCKED_RFI blank (form not chosen)")
            elif ln["evidence_state"] in VALUED_STATES:
                if ln["measured_net"] is None or abs(ln["measured_net"] - rec["figure_beside_lm"]) > TOL:
                    raise ValueError(f"{METHOD}: valued pair line {ln['line_id']} is not its form figure")
                out["valued_pairs"] += 1
            out["pairs"] += 1
        elif act == "ADD_LANDING":
            L = _r(sum(p["plan_lm"] + p["returns_lm"] for p in rec["pieces"]))
            if ln["item_code"] != ROOM_CODE or ln["evidence_state"] not in VALUED_STATES or \
                    abs((ln.get("measured_net") or -1) - L) > TOL or ln.get("gross") != ln.get("measured_net"):
                raise ValueError(f"{METHOD}: landing line {ln['line_id']} is not the sum of its pieces {L}")
            out["landings"] += 1
            out["landing_lm"] = _r(out["landing_lm"] + L)
        elif act == "ADD_LANDING_HELD":
            if ln["evidence_state"] != HELD_STATE or not _blank(ln) or not (ln.get("rfi") or {}).get("question"):
                raise ValueError(f"{METHOD}: held landing line {ln['line_id']} is not BLOCKED_RFI blank")
            out["landing_held"] += 1
        elif act == "RETIRE_ROOM_STRETCHES":
            if ln["evidence_state"] not in VALUED_STATES or ln.get("measured_net") is None or \
                    abs(ln["gross"] - _sum(ln.get("deductions")) + _sum(ln.get("additions")) - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: room line {ln['line_id']} does not close")
            if abs(rec["was"]["measured_net"] - rec["retired_lm"] - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: room line {ln['line_id']} moved by other than its retired stretches")
            if any(h not in by for h in rec["home_lines"]):
                raise ValueError(f"{METHOD}: room line {ln['line_id']} names a carrier not in the candidate")
            out["retired_lm"] = _r(out["retired_lm"] + rec["retired_lm"])
        elif act == "CLOSE_ROOM_RANGE":
            if ln["evidence_state"] != NA_STATE or not _blank(ln) or any(h not in by for h in rec["home_lines"]):
                raise ValueError(f"{METHOD}: closed range line {ln['line_id']} carries a figure or names no carrier")
            out["closed"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.56 lines, identity). Changed lines replace their candidate line in place, added lines follow; every
    other candidate line is byte-identical (asserted). Every V3.0.55 check runs as V3.0.55 runs it."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, adds, repl = list(prev), [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] not in CODES:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    # the V3.0.44 skirting check reads a line as V3.0.44 left it: a line a later version re-recorded (V3.0.51, or a room
    # range closed here) is checked by that version's own check, as V3.0.51 does
    older = [ln for ln in out if not any(((ln.get("calculation") or {}).get("inputs") or {}).get(k)
                                         for k in (A3051.REC_KEY, REC_KEY))]
    ident = {"base_lines": len(prev), "v3_0_56_lines": len(out), "v3_0_56_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3050.check_zone_owner(out), "skirting": A3044.check_skirting(older),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out), "remainder": A3051.check_remainder(out),
             "lintels": A3053.check_lintels(out), "rail_runs": A3054.check_runs(out),
             "wiring": A3055.check_wiring(out), "stair_skirting": check_stair_skirting(out)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(outside), outside_rows_identical_to_base=len(outside),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest())
    return out, ident


def check_totals(t0, t1):
    """totals move only in FIN.SKIRTING and the two stair skirting form codes (asserted)."""
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] not in CODES:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_56": t1.get(k)}
    return moved


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "stair_piece": (rec.get("stair_piece") or {}).get("pid") or rec.get("element"),
                     "figure_beside_lm": rec.get("figure_beside_lm"),
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_56": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "downstream": c.get("downstream"), "record": rec, "verification": c.get("verification") or {},
                     "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "stair_piece",
              "figure_beside_lm", "v2_9", "base", "v3_0_56", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_56")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "stair_piece": r.get("stair_piece") or "",
                       "figure_beside_lm": "" if r.get("figure_beside_lm") is None else _fmt(r["figure_beside_lm"]),
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_56": q(r.get("after_v3_0_56")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_56=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_56_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": {k: log.get(k) for k in ("form", "by_action", "landings", "landing_lm", "landing_held", "pairs",
                                               "form_beside", "held_pieces", "retired_lm", "closed_range_lm",
                                               "risers_by_flight")},
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_56_BOQ_LINES.json": BL.dumps(new),
             "V3_0_56_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_56_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_56_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_56_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_56_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "ZIG", "SLO", "load_inputs",
           "check_form", "check_one_owner", "plan_union", "bind_stretch", "pair_ids", "changes_for",
           "check_stair_skirting", "integrate", "check_totals", "ledger_rows", "diff_rows", "write", "InputsError"]
