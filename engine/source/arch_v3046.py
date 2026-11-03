"""ARCH_TAKEOFF_V3.0.46 (T-443, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.45
(engine.source.arch_v30, arch_v301 .. arch_v3045), extended with the STAIR-ROOM SKIRTING SPLIT of the Checker-verified
T-441 face tables (merged ece154fe) in ONE step:

  SPLIT_PART   a stair room's skirting line that is BLOCKED whole gets one CHILD line per FLOOR PART of the room
               (R-T418-1 parts): its drawn wall / column faces at the part's floor level, stretch by stretch, gross =
               faces + openings on those sides, deductions by opening id (door, passage, LIFT opening whole), net =
               gross - deductions. The child's material follows its own floor line (bound by id): a material the
               owner approved (Q-70 A) is carried as such; otherwise the length is valued and the material is HELD
               with the floor finish (named, never assumed).
  SPLIT_HELD   a face whose role or extent is not established (guard band, reveal jambs, an undrawn boundary) becomes
               its own HELD BLANK child (BLOCKED_RFI, no value, never 0), its drawn candidate length beside.
  PARENT       the parent keeps its id and carries only what no child and no other line owns: HELD BLANK with the
               named remainder, or NOT_APPLICABLE_WITH_EVIDENCE (no figure) when nothing remains. Faces along a
               flight stay with the merged stair side table (B7-07 / B7-08 owners named, one face one owner); faces
               beside a slab opening with no floor at the part's level carry no skirting (named, not held).

R-T443-1 (every villa; integrates R-T441-1 .. 4, UP-SKIRT-001 1.4.0, UP-CER-003, R-T246 deductions by opening id,
register rulings LIFT LANDING THRESHOLD and LIFT DOOR GAP IN SKIRTING): (a) each side of a floor part is covered by
its stretches exactly once; (b) WALL / COLUMN faces carry a drawn handle and are skirted; (c) every opening is
deducted by its id; a LIFT opening is deducted whole and never gets jamb skirting, a DOOR jamb never; (d) a face that
shares wall line, plan interval and level with a merged stair side stretch is refused (one base, one owner); (e) no
face handle-and-interval is carried by two children; (f) HELD is blank with its cause, never 0; (g) the parent's
engine wall + column run closes: children faces + faces owned by other lines + faces with no floor + the named
remainder = run (residual <= TOL), otherwise the split is refused.

Nothing else moves: every V3.0.45 line not named by the inputs is byte-identical (asserted); totals move only in
FIN.SKIRTING (asserted). Files: V3_0_46_BOQ_LINES.json / .csv, V3_0_46_INTEGRATION_LEDGER.json / .csv,
V3_0_46_DIFF.csv, V3_0_46_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re

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
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041
from engine.source import arch_v3042 as A3042
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3044 as A3044
from engine.source import arch_v3045 as A3045

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.46"
EXTENDS = A3045.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T443_ARCH_V3_0_46"
INPUTS_SCHEMA = "URBAN_V3046_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3046_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T443-1", "T-443"
REC_KEY = "stair_room_skirting_v3046"
CODE, UNIT = "FIN.SKIRTING", "lm"
P_PART, P_HELD, P_PARENT = "SPLIT_PART", "SPLIT_HELD", "PARENT"
ACTIONS = ("SPLIT_PART", "SPLIT_HELD", "PARENT_HELD", "PARENT_NA")
FACE = ("WALL", "COLUMN")
OPENINGS = ("DOOR", "PASSAGE", "LIFT_OPENING")
HELD_KINDS = ("GUARD_HELD", "HELD", "UNKNOWN")
KINDS = FACE + OPENINGS + ("OPEN", "STAIR_SIDE") + HELD_KINDS
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
HELD_STATE, NA_STATE = "BLOCKED_RFI", "NOT_APPLICABLE_WITH_EVIDENCE"
MATERIAL = ("OWNER_APPROVED", "HELD_WITH_FLOOR")
EVIDENCE_STATUS = ("VERIFIED", "DRAWING-CONFIRMED")
TOL = 0.0005                             # tools/boq_export_v1.QTY_MATCH_TOL (the T-330 check's tolerance)
GEOM_TOL = 1e-6
MAX_M = 50.0                             # one side / stretch in m; above it is a unit slip (mm / cm)
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
FLOOR_CODES = ("FIN.FLOOR.", "FIN.MARBLE.LANDING")   # the finish line a part child follows (floor or stair landing)

PIECES = {
    P_PART: {"module": "engine/source/arch_v3046.py (a BLOCKED stair-room skirting line split into one child per "
                       "floor part: drawn faces stretch by stretch, openings deducted by id, a lift opening whole)",
             "policy": "STAIR_ROOM_SKIRTING_SPLIT_V1", "rule_id": "R-T441-1 .. 4 (R-T443-1 a-c, e)",
             "owner_rules": ["UP-SKIRT-001 1.4.0 (dry-room wall and column faces at floor level)",
                             "UP-CER-002 (skirting in lm)", "UP-CER-003 (doors / passages deducted)",
                             "R-T246 (deductions by opening id)", "Q-70 A (stair landing / lobby finish)",
                             "register LIFT LANDING THRESHOLD / LIFT DOOR GAP IN SKIRTING (Lead 2026-11-01 20:17)",
                             "UP-QTY-STATUS-001 (held is blank, never 0)"],
             "owner_manual_method": "perimeter of each floored part at its floor level less each door / lift opening "
                                    "width by id; no skirting along a flight, a void or a guard",
             "drawing_method": "the merged T-441 face table: every side of the part cut into stretches by DXF handle "
                               "(room-local metres), faces skirted, openings deducted by id, the lift opening whole "
                               "with no jambs; Checker own re-measure of the 2F lobby AGREE"},
    P_HELD: {"module": "engine/source/arch_v3046.py (a face whose role or extent is open: its own HELD BLANK child)",
             "policy": "STAIR_ROOM_SKIRTING_HELD_FACE_V1", "rule_id": "R-T441-4 (R-T443-1 f)",
             "owner_rules": ["UP-QTY-STATUS-001", "defect B12 (no skirting along a void / railing edge assumed)"],
             "owner_manual_method": "not measured: the face's existence or finish is a designer item",
             "drawing_method": "the merged T-441 held stretches with their cause; the drawn candidate length beside, "
                               "never the quantity"},
    P_PARENT: {"module": "engine/source/arch_v3046.py (the parent keeps only the named remainder, or is not "
                         "applicable when nothing remains; the run closes in lm)",
               "policy": "STAIR_ROOM_SKIRTING_PARENT_V1", "rule_id": "R-T441-2 (R-T443-1 d, g)",
               "owner_rules": ["OWNER_RULE_STAIRS (skirting along a flight = stair skirting, B7-07 / B7-08)",
                               "UP-QTY-STATUS-001"],
               "owner_manual_method": "the stair room is not one skirting quantity: floored parts, flights and the "
                                      "open well are taken apart",
               "drawing_method": "closure of the engine's wall + column run of the room: children faces + flight "
                                 "faces (stair side table owners) + faces with no floor + named remainder"},
}
WAITING = dict(A3045.WAITING)
WAITING.update({
    "T443_GF_DIVIDER_BAND": "GF stair divider band between the two lower flights: guard upstand or wall face, its south "
                            "end and finish not printed (designer item): HELD BLANK child, 2.200 / 3.400 lm beside",
    "T443_GF_REVEAL_JAMBS": "doorless opening from the GF stair hall to the wet wash space: reveal owner (tile return or "
                            "skirting) not printed: HELD BLANK child, 0.400 lm beside",
    "T443_GF_LOBBY_WEST": "GF back lobby west boundary under the winders (open or enclosed not drawn): HELD BLANK child, "
                          "1.150 lm beside if the face stands on the drawn line",
    "T443_FLIGHT_FACES": "faces along the flights stay with the stair side table (B7-07 / B7-08), whose form waits on "
                         "ORR-007: not in any room line",
    "T443_1F_SHAFT": "1F living line: the ST-1F shaft split R-T481-3 (9.050 lm to B7, merged a8609a7a, not "
                     "re-measured at its Gate A) needs the engine edges of that line by handle: a separate package",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False, top=MAX_M):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    if x > top:
        raise InputsError(f"{where}: {x} m is not a length in m (mm / cm refused)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def _sources(doc):
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    if not srcs:
        raise InputsError("sources: the merged ledgers the rows come from")
    return srcs


def _tasks(r, srcs, where):
    if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
        raise InputsError(f"{where}: no merged source named")


def check_side(side, where):
    """R-T443-1 a-c, f: the side's stretches cover [0, length] once, in order. -> list of checked stretches."""
    L = _num(side.get("length"), f"{where} length", pos=True)
    pos, out = 0.0, []
    for st in side.get("stretches") or ():
        k = st.get("kind")
        if k not in KINDS:
            raise InputsError(f"{where}: unknown stretch kind {k!r}")
        a = _num(st.get("s0"), f"{where} s0")
        b = _num(st.get("s1"), f"{where} s1")
        if b - a <= GEOM_TOL:
            raise InputsError(f"{where}: empty or reversed stretch {a} .. {b}")
        if abs(a - pos) > GEOM_TOL:
            raise InputsError(f"{where}: {'gap' if a > pos else 'overlap'} at s {pos:.4f} .. {a:.4f}")
        if k in OPENINGS and not st.get("opening_id"):
            raise InputsError(f"{where}: {k} at s {a:.4f} deducted without an opening id (R-T246)")
        if k in FACE and not str(st.get("handles") or "").split():
            raise InputsError(f"{where}: {k} face at s {a:.4f} without a drawn handle")
        if k == "STAIR_SIDE" and not st.get("flight"):
            raise InputsError(f"{where}: STAIR_SIDE at s {a:.4f} without the owning stair stretch")
        if k in HELD_KINDS:
            if not st.get("cause"):
                raise InputsError(f"{where}: {k} at s {a:.4f} without a cause (held is named)")
            if st.get("lm") == 0 or st.get("value") not in (None, ""):
                raise InputsError(f"{where}: {k} at s {a:.4f} carried with a value (held is blank, never 0)")
        out.append(dict(st, s0=a, s1=b, _len=_r(b - a)))
        pos = b
    if abs(pos - L) > GEOM_TOL:
        raise InputsError(f"{where}: stretches end at {pos:.4f}, the side is {L:.4f} (short cover)")
    return out


def check_jambs(part, where):
    """R-T443-1 c: a jamb return belongs to a PASSAGE of this part; a lift-opening or door jamb is refused."""
    kinds = {st["opening_id"]: st["kind"] for sd in part["sides"] for st in sd["_st"] if st["kind"] in OPENINGS}
    out = []
    for j in part.get("jambs") or ():
        _need(j, ("id", "opening_id", "cause"), f"{where} jamb {j.get('id')}")
        k = kinds.get(j["opening_id"])
        if k is None:
            raise InputsError(f"{where} jamb {j['id']}: opening {j['opening_id']} is not deducted on this part")
        if k == "LIFT_OPENING":
            raise InputsError(f"{where} jamb {j['id']}: a lift-opening jamb given skirting (the lift surround owns it)")
        if k == "DOOR":
            raise InputsError(f"{where} jamb {j['id']}: a door jamb given skirting (the frame covers it)")
        if j.get("value") not in (None, ""):
            raise InputsError(f"{where} jamb {j['id']}: a jamb return is held blank here (owner of the reveal open)")
        out.append(dict(j, _depth=_num(j.get("depth"), f"{where} jamb {j['id']} depth", pos=True, top=1.0)))
    return out


def overlaps(part, owners):
    """R-T443-1 d: WALL / COLUMN stretches of the part that share wall line, plan interval and level with an owner
    stretch (a merged stair side stretch). Sides and owners name their wall line and plan interval in the same
    along-line frame; an owner carries its level range (lo, hi). -> list."""
    out = []
    for sd in part["sides"]:
        for st in sd["_st"]:
            if st["kind"] not in FACE:
                continue
            t0 = sd["t0"] + sd["dir"] * st["s0"]
            t1 = sd["t0"] + sd["dir"] * st["s1"]
            lo_t, hi_t = min(t0, t1), max(t0, t1)
            for f in owners:
                if f["line"] != sd["line"] or not (f["lo"] - GEOM_TOL <= part["level"] <= f["hi"] + GEOM_TOL):
                    continue
                ov = min(hi_t, f["t1"]) - max(lo_t, f["t0"])
                if ov > GEOM_TOL:
                    out.append({"part": part["part"], "side": sd["id"], "s0": st["s0"], "owner": f["id"],
                                "overlap_m": _r(ov)})
    return out


def _face_keys(part):
    """(line, interval) of every skirted face of the part, in the along-line frame (R-T443-1 e)."""
    keys = []
    for sd in part["sides"]:
        for st in sd["_st"]:
            if st["kind"] in FACE:
                t0, t1 = sd["t0"] + sd["dir"] * st["s0"], sd["t0"] + sd["dir"] * st["s1"]
                keys.append((sd["line"], part["level"], min(t0, t1), max(t0, t1), part["part"], sd["id"]))
    return keys


def measure(part):
    """one floor part -> {gross, deductions, net, held, jambs, rows}; gross = faces + openings, net = faces."""
    gross, ded, held, rows, net = 0.0, [], [], [], 0.0
    for sd in part["sides"]:
        for st in sd["_st"]:
            k, L = st["kind"], st["_len"]
            rows.append({"side": sd["id"], "s0": st["s0"], "s1": st["s1"], "kind": k, "length_m": L,
                         "handles": st.get("handles") or "", "opening_id": st.get("opening_id") or "",
                         "owner": st.get("flight") or ""})
            if k in FACE:
                gross += L
                net += L
            elif k in OPENINGS:
                gross += L
                ded.append({"opening_id": st["opening_id"], "kind": k, "qty": L, "side": sd["id"],
                            "jamb_skirting": False if k != "PASSAGE" else "LISTED_SEPARATELY"})
            elif k in HELD_KINDS:
                held.append({"side": sd["id"], "kind": k, "s0": st["s0"], "s1": st["s1"], "candidate_lm": L,
                             "group": st.get("group") or sd["id"], "cause": st["cause"]})
    return {"gross": _r(gross), "deductions": ded, "deducted": _r(sum(d["qty"] for d in ded)), "net": _r(net),
            "held": held, "rows": rows}


def load_inputs(doc, project_id=None):
    """URBAN_V3046_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "owners": [{"id", "line", "t0", "t1", "lo", "hi"}]      (merged stair side stretches, room-local frame),
     "splits": [{"parent", "room", "floor", "expect": {"evidence_state"}, "engine_run_lm", "source_tasks",
                 "parts": [{"part", "level", "floor_line", "evidence_status", "evidence_state",
                            "material": {"kind" OWNER_APPROVED / HELD_WITH_FLOOR, "basis"},
                            "sides": [{"id", "line", "t0", "dir", "length", "stretches": [...]}],
                            "jambs": [{"id", "opening_id", "depth", "cause"}]}],
                 "held_groups": [{"group", "part", "cause", "beside": "<candidate lm text>", "rfi"}],
                 "owned_elsewhere": [{"what", "lm", "owner", "owner_line" (optional)}],
                 "no_floor": [{"what", "lm", "why"}],
                 "remainder": [{"what", "lm", "why", "rfi"}]}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = _sources(doc)
    owners = []
    for f in doc.get("owners") or ():
        _need(f, ("id", "line"), "owner stretch")
        owners.append(dict(f, t0=float(f["t0"]), t1=float(f["t1"]), lo=float(f["lo"]), hi=float(f["hi"])))
    splits, parents, keys = [], set(), []
    for s in doc.get("splits") or ():
        w = f"split {s.get('parent')}"
        _need(s, ("parent", "room", "floor", "expect", "parts"), w)
        _tasks(s, srcs, w)
        if _lid(s["parent"], w) in parents:
            raise InputsError(f"{w}: parent named twice")
        parents.add(s["parent"])
        run = _num(s.get("engine_run_lm"), f"{w} engine_run_lm", pos=True, top=2000)
        parts, names = [], set()
        for p in s["parts"]:
            pw = f"{w} part {p.get('part')}"
            _need(p, ("part", "level", "floor_line", "evidence_status", "evidence_state", "material", "sides"), pw)
            if p["part"] in names:
                raise InputsError(f"{pw}: part named twice")
            names.add(p["part"])
            _lid(p["floor_line"], pw)
            if p["evidence_status"] not in EVIDENCE_STATUS:
                raise InputsError(f"{pw}: evidence status {p['evidence_status']!r} not in {EVIDENCE_STATUS}")
            if p["evidence_state"] not in VALUED_STATES:
                raise InputsError(f"{pw}: a part child is valued ({VALUED_STATES}); held faces go to held_groups")
            m = p["material"]
            if m.get("kind") not in MATERIAL or not m.get("basis"):
                raise InputsError(f"{pw}: material kind {m.get('kind')!r} not in {MATERIAL} or no basis")
            if m["kind"] == "OWNER_APPROVED" and "Q-" not in m["basis"]:
                raise InputsError(f"{pw}: an owner-approved material names its owner answer (Q-nn)")
            if not isinstance(p["level"], (int, float)):
                raise InputsError(f"{pw}: level {p['level']!r} is not a level in m")
            sides = []
            for sd in p["sides"]:
                sw = f"{pw} side {sd.get('id')}"
                _need(sd, ("id", "line"), sw)
                if sd.get("dir") not in (1, -1):
                    raise InputsError(f"{sw}: dir must be +1 or -1")
                sides.append(dict(sd, t0=float(sd["t0"]), _st=check_side(sd, sw)))
            q = dict(p, sides=sides)
            q["_jambs"] = check_jambs(q, pw)
            ov = overlaps(q, owners)
            if ov:
                raise InputsError(f"{pw}: wall face shared with a stair side stretch {ov} (one base, one owner)")
            q["_m"] = measure(q)
            if q["_m"]["net"] <= 0:
                raise InputsError(f"{pw}: no skirted face: a part child needs at least one drawn face")
            keys += _face_keys(q)
            parts.append(q)
        hg = []
        held_by_group = {}
        for q in parts:
            for h in q["_m"]["held"]:
                held_by_group.setdefault((q["part"], h["group"]), []).append(h)
            for j in q["_jambs"]:
                held_by_group.setdefault((q["part"], j.get("group") or f"{j['opening_id']}-JAMBS"), []).append(
                    {"side": "jamb", "kind": "JAMB", "candidate_lm": j["_depth"], "cause": j["cause"]})
        named_groups = set()
        for g in s.get("held_groups") or ():
            gw = f"{w} held group {g.get('group')}"
            _need(g, ("group", "part", "cause", "beside", "rfi"), gw)
            k = (g["part"], g["group"])
            if k not in held_by_group:
                raise InputsError(f"{gw}: no held stretch or jamb of the face table in this group")
            if k in named_groups:
                raise InputsError(f"{gw}: named twice")
            if g.get("value") not in (None, ""):
                raise InputsError(f"{gw}: HELD_WITH_VALUE: a held face group is blank, never a figure")
            named_groups.add(k)
            hg.append(dict(g, _stretches=held_by_group[k]))
        missing = sorted(set(held_by_group) - named_groups)
        if missing:
            raise InputsError(f"{w}: held stretches with no held line {missing} (a held face is named, never dropped)")
        own = [dict(x, _lm=_num(x.get("lm"), f"{w} owned {x.get('what')}", pos=True)) for x in
               s.get("owned_elsewhere") or ()]
        for x in own:
            _need(x, ("what", "owner"), f"{w} owned elsewhere")
        nof = [dict(x, _lm=_num(x.get("lm"), f"{w} no floor {x.get('what')}", pos=True)) for x in s.get("no_floor") or ()]
        for x in nof:
            _need(x, ("what", "why"), f"{w} no floor")
        rem = [dict(x, _lm=_num(x.get("lm"), f"{w} remainder {x.get('what')}", pos=True)) for x in
               s.get("remainder") or ()]
        for x in rem:
            _need(x, ("what", "why", "rfi"), f"{w} remainder")
        faces = _r(sum(q["_m"]["net"] for q in parts))
        clos = _r(faces + sum(x["_lm"] for x in own) + sum(x["_lm"] for x in nof) + sum(x["_lm"] for x in rem))
        if abs(clos - run) > TOL:
            raise InputsError(f"{w}: closure {clos} lm (children {faces} + owned + no floor + remainder) is not the "
                              f"engine run {run} lm (residual {_r(clos - run)}): a face is missing or counted twice")
        splits.append(dict(s, parts=parts, _held=hg, _own=own, _nof=nof, _rem=rem, _run=run, _faces=faces,
                           _closure=clos))
    seen = []
    for k in sorted(keys):
        for o in seen:
            if o[0] == k[0] and abs(o[1] - k[1]) <= GEOM_TOL and min(o[3], k[3]) - max(o[2], k[2]) > GEOM_TOL:
                raise InputsError(f"face {k[4]} {k[5]} and {o[4]} {o[5]} share line {k[0]} at the same level: "
                                  f"one face, one owner")
        seen.append(k)
    if not splits:
        raise InputsError("no stair-room split in the inputs")
    return dict(doc, _sources=srcs, _owners=owners, _splits=splits)


# ================================================================================================ lines
def _plain(text):
    """a held text shown in a held / not-applicable line's formula: 'a = 0.5 lm' -> 'a equals 0.5 lm' and 'net 0.5 lm'
    -> 'net of 0.5 lm', so the formula never reads as concluding on a figure (T-334); the record keeps the text."""
    t = re.sub(r"=\s*(-?\d+(?:\.\d+)?\s*lm(?![A-Za-z0-9]))", r"equals \1", str(text or ""))
    return re.sub(r"\bnet\s+(?=-?\d)", "net of ", t)


def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _is_skirting(ln):
    return ln is not None and ln["item_code"] == CODE and ln["unit"] == UNIT


def _room(ln):
    return (ln.get("location") or {}).get("room_id")


def _child(parent, s, p, floor_ln, srcs):
    from engine.source import boq_line as BL
    m = p["_m"]
    mat = p["material"]
    ded = [{"opening_id": d["opening_id"], "kind": d["kind"], "qty": d["qty"], "side": d["side"],
            "jamb_skirting": d["jamb_skirting"],
            "why": ("lift opening deducted WHOLE, no jamb skirting (lift surround / threshold own the jambs and band)"
                    if d["kind"] == "LIFT_OPENING" else "opening deducted by id (UP-CER-003)")} for d in m["deductions"]]
    faces = "; ".join(f"{r['side']} {_fmt(r['length_m'])} ({r['handles']})" for r in m["rows"] if r["kind"] in FACE)
    dtxt = " + ".join(f"{d['opening_id']} {_fmt(d['qty'])}{' LIFT' if d['kind'] == 'LIFT_OPENING' else ''}"
                      for d in ded) or "none"
    mtxt = (f"material {mat['basis']}" if mat["kind"] == "OWNER_APPROVED" else
            f"material HELD with its floor finish (line {floor_ln['line_id']}): {mat['basis']}")
    formula = (f"{METHOD}: floor part {p['part']} at {_fmt(p['level'])}: gross {_fmt(m['gross'])} lm (faces + openings "
               f"on its sides) - {dtxt} = {_fmt(m['net'])} lm; faces {faces}; {mtxt}")[:1500]
    rec = _rec(P_PART, srcs, action="SPLIT_PART", parent=parent["line_id"], part=p["part"], level=p["level"],
               floor_line=floor_ln["line_id"], material=mat, evidence_status=p["evidence_status"],
               stretches=m["rows"], gross=m["gross"], deducted=m["deducted"], net=m["net"])
    ln = BL.make_line(
        project_id=parent["project"]["project_id"], revision_set_sha256=parent["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=p["evidence_state"], measured_net=m["net"], gross=m["gross"],
        deductions=ded, element_id=f"SKIRT-T443:{p['part']}", floor=s["floor"], room_id=s["room"],
        room_name_en=(parent.get("location") or {}).get("room_name_en"),
        room_name_ar=(parent.get("location") or {}).get("room_name_ar"),
        physical_element=f"skirting at the foot of the drawn wall / column faces of the floor part {p['part']}",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": p["evidence_status"]},
        documents=copy.deepcopy(parent["source"]["documents"]), geometry_source=parent["source"]["geometry_source"],
        geometry_confidence=parent["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="PROJECT_OWNER_FACT" if mat["kind"] == "OWNER_APPROVED" else "BY_SPEC",
        notes=(f"{METHOD}: child of {parent['line_id']} (stair room split); lm {p['evidence_status']}; "
               f"{'material ' + mat['basis'] if mat['kind'] == 'OWNER_APPROVED' else 'material HELD with floor line ' + floor_ln['line_id']}"
               f"; NOT RELEASED"),
        trade=parent.get("trade"), subtrade=parent.get("subtrade"))
    return _fin(ln)


def _held_child(parent, s, g, srcs):
    from engine.source import boq_line as BL
    st = g["_stretches"]
    what = "; ".join(f"{x['side']} {x['kind']} {_fmt(x['candidate_lm'])}" for x in st)
    formula = _plain(f"{METHOD}: HELD (never a value) skirting face(s) {g['group']} of the floor part {g['part']}: "
                     f"{g['cause'][:500]} | drawn beside, never the quantity: {g['beside'][:200]} ({what})")[:1500]
    rec = _rec(P_HELD, srcs, action="SPLIT_HELD", parent=parent["line_id"], part=g["part"], group=g["group"],
               stretches=[{k: x.get(k) for k in ("side", "kind", "s0", "s1", "candidate_lm")} for x in st],
               cause=g["cause"][:600], beside=g["beside"][:300], evidence_status="HELD")
    ln = BL.make_line(
        project_id=parent["project"]["project_id"], revision_set_sha256=parent["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=f"SKIRT-T443:{g['part']}:{g['group']}", floor=s["floor"], room_id=s["room"],
        room_name_en=(parent.get("location") or {}).get("room_name_en"),
        room_name_ar=(parent.get("location") or {}).get("room_name_ar"),
        physical_element=f"skirting of the face(s) {g['group']} of the floor part {g['part']} (role / extent open)",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(parent["source"]["documents"]), geometry_source=parent["source"]["geometry_source"],
        geometry_confidence=parent["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="BY_SPEC",
        rfi={"question": g["rfi"][:900], "unlocks": f"SKIRT-T443:{g['part']}:{g['group']}",
             "bound_beside": g["beside"][:300]},
        notes=f"{METHOD}: child of {parent['line_id']}; HELD BLANK (never 0); NOT RELEASED",
        trade=parent.get("trade"), subtrade=parent.get("subtrade"))
    return _fin(ln)


def _parent_after(parent, s, kids, srcs):
    new = copy.deepcopy(parent)
    c = new["calculation"] = dict(new.get("calculation") or {})
    c["inputs"] = dict(c.get("inputs") or {})
    own = "; ".join(f"{x['what']} {_fmt(x['_lm'])} -> {x['owner']}" for x in s["_own"]) or "none"
    nof = "; ".join(f"{x['what']} {_fmt(x['_lm'])} ({x['why'][:120]})" for x in s["_nof"]) or "none"
    rem = "; ".join(f"{x['what']} {_fmt(x['_lm'])} ({x['why'][:160]})" for x in s["_rem"])
    ktxt = ", ".join(k["line_id"] for k in kids)
    closure = {"engine_run_lm": s["_run"], "children_faces_lm": s["_faces"],
               "owned_elsewhere": [{"what": x["what"], "lm": x["_lm"], "owner": x["owner"],
                                    "owner_line": x.get("owner_line")} for x in s["_own"]],
               "no_floor": [{"what": x["what"], "lm": x["_lm"], "why": x["why"][:300]} for x in s["_nof"]],
               "remainder": [{"what": x["what"], "lm": x["_lm"], "why": x["why"][:300]} for x in s["_rem"]],
               "closure_lm": s["_closure"], "residual_lm": _r(s["_closure"] - s["_run"])}
    was = {"evidence_state": parent["evidence_state"], "rfi": parent.get("rfi")}
    if s["_rem"]:
        action = "PARENT_HELD"
        new["evidence_state"] = HELD_STATE
        new["measured_net"], new["gross"], new["bounded_range"] = None, None, None
        q = "; ".join(x["rfi"] for x in s["_rem"])
        new["rfi"] = {"question": q[:900], "unlocks": f"remainder of {parent['line_id']}",
                      "bound_beside": f"remainder {_fmt(_r(sum(x['_lm'] for x in s['_rem'])))} lm drawn beside"[:300]}
        c["formula"] = _plain(f"{METHOD}: HELD (never a value) remainder of the stair room after the split into {ktxt}: "
                        f"{rem} | flight faces owned by: {own} | no floor: {nof} | run {_fmt(s['_run'])} lm closes "
                        f"(residual {_fmt(closure['residual_lm'])})")[:1500]
        A305._note(new, f"{METHOD}: split into {len(kids)} child line(s); parent HELD BLANK with the named remainder")
    else:
        action = "PARENT_NA"
        new["evidence_state"] = NA_STATE
        new["measured_net"], new["gross"], new["bounded_range"], new["rfi"] = None, None, None, None
        c["formula"] = _plain(f"NOT_APPLICABLE: the stair room's skirting is carried by its floor-part lines {ktxt}; flight "
                        f"faces owned by: {own}; no floor (no skirting): {nof}; run {_fmt(s['_run'])} lm closes "
                        f"(residual {_fmt(closure['residual_lm'])}) ({METHOD})")[:1500]
        A305._note(new, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: split into {ktxt}; nothing remains")
    c["inputs"][REC_KEY] = _rec(P_PARENT, srcs, action=action, children=[k["line_id"] for k in kids], was=was,
                                closure=closure, evidence_status="HELD" if s["_rem"] else "NOT_APPLICABLE")
    return _fin(new), action


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a candidate line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_PART, P_HELD, P_PARENT)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.46 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_PART, P_HELD, P_PARENT)), "state": "RUN", "sources": doc["sources"],
           "by_action": {}, "lines_added": 0, "lines_changed": 0, "valued_lm": 0.0, "held_groups": 0, "parents": {}}

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs), verification=A3043._ver(srcs),
                                    downstream=kw.pop("downstream", []), group=after["item_code"], **kw))

    for s in doc["_splits"]:
        w = f"split {s['parent']}"
        par = by.get(s["parent"])
        if not _is_skirting(par):
            raise InputsError(f"{w}: not a {CODE} {UNIT} line of the candidate (stale binding)")
        if par["evidence_state"] != s["expect"].get("evidence_state") or par.get("measured_net") is not None:
            raise InputsError(f"{w}: {par['evidence_state']} net {par.get('measured_net')} is not the blocked parent "
                              f"the ledger split (stale binding)")
        if _room(par) != s["room"] or (par.get("location") or {}).get("floor") != s["floor"]:
            raise InputsError(f"{w}: parent room / floor is not {s['floor']} {s['room']}")
        srcs = [S[t] for t in s["source_tasks"]]
        kids = []
        for p in s["parts"]:
            fl = by.get(p["floor_line"])
            if fl is None or not fl["item_code"].startswith(FLOOR_CODES) or _room(fl) != s["room"]:
                raise InputsError(f"{w} part {p['part']}: floor line {p['floor_line']} is not a FIN.FLOOR / landing "
                                  f"line of {s['room']} (stale binding)")
            kid = _child(par, s, p, fl, srcs)
            kids.append(kid)
            add(P_PART, "SPLIT_PART", kid, srcs=srcs, evidence_status=p["evidence_status"],
                held=[] if p["material"]["kind"] == "OWNER_APPROVED" else [
                    {"what": f"material of {kid['line_id']}", "why": p["material"]["basis"][:300], "range": None,
                     "scenario": "lm valued; material HELD with the floor finish"}],
                downstream=[f"skirting roll-up: certain lm +{_fmt(p['_m']['net'])} (was inside a BLOCKED parent)"])
            log["valued_lm"] = _r(log["valued_lm"] + p["_m"]["net"])
        for g in s["_held"]:
            kid = _held_child(par, s, g, srcs)
            kids.append(kid)
            add(P_HELD, "SPLIT_HELD", kid, srcs=srcs, evidence_status="HELD",
                held=[{"what": f"{CODE} {g['part']} {g['group']}", "why": g["cause"][:300], "range": None,
                       "scenario": "held blank; drawn length beside"}],
                downstream=["skirting completeness: the open face is its own line (held)"])
            log["held_groups"] += 1
        after, action = _parent_after(par, s, kids, srcs)
        add(P_PARENT, action, after, before=par, srcs=srcs,
            evidence_status="HELD" if action == "PARENT_HELD" else "NOT_APPLICABLE",
            held=[{"what": f"{CODE} {par['line_id']}", "why": x["why"][:300], "range": None,
                   "scenario": "held remainder"} for x in s["_rem"]],
            downstream=["skirting roll-up: parent carries no figure (was BLOCKED, no figure)"])
        log["parents"][par["line_id"]] = {"action": action, "children": [k["line_id"] for k in kids],
                                          "faces_lm": s["_faces"], "run_lm": s["_run"],
                                          "residual_lm": _r(s["_closure"] - s["_run"])}
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_stair_rooms(lines, before=None):
    """R-T443-1 on the integrated lines: a part child is valued, closes gross - deductions = net, carries no lift jamb
    skirting; a held child is BLOCKED BLANK; a parent is HELD BLANK or NOT_APPLICABLE without a figure and every child
    it names is in the lines; a child names its parent. -> summary."""
    out = {"parts": 0, "parts_lm": 0.0, "held_children": 0, "parents_held": 0, "parents_na": 0}
    ids = {ln["line_id"]: ln for ln in lines}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if not _is_skirting(ln):
            raise ValueError(f"{METHOD}: a V3.0.46 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        if act == "SPLIT_PART":
            if ln["evidence_state"] not in VALUED_STATES or ln.get("measured_net") is None:
                raise ValueError(f"{METHOD}: part child {ln['line_id']} is not valued")
            d = sum(float(x.get("qty") or 0) for x in ln.get("deductions") or ())
            if abs(ln["gross"] - d - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: part child {ln['line_id']} does not close gross - deductions = net")
            for x in ln.get("deductions") or ():
                if x.get("kind") == "LIFT_OPENING" and x.get("jamb_skirting") is not False:
                    raise ValueError(f"{METHOD}: part child {ln['line_id']}: lift opening {x.get('opening_id')} "
                                     f"skirted as a passage")
            if ln.get("additions"):
                raise ValueError(f"{METHOD}: part child {ln['line_id']} carries additions (jambs are held lines)")
            if rec.get("parent") not in ids:
                raise ValueError(f"{METHOD}: part child {ln['line_id']} names no candidate parent")
            out["parts"] += 1
            out["parts_lm"] = _r(out["parts_lm"] + ln["measured_net"])
        elif act == "SPLIT_HELD":
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or \
                    ln.get("gross") is not None or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: held child {ln['line_id']} is not HELD BLANK (never 0)")
            out["held_children"] += 1
        elif act in ("PARENT_HELD", "PARENT_NA"):
            want = HELD_STATE if act == "PARENT_HELD" else NA_STATE
            if ln["evidence_state"] != want or ln.get("measured_net") is not None or ln.get("gross") is not None:
                raise ValueError(f"{METHOD}: parent {ln['line_id']} carries a figure or is not {want}")
            if any(k not in ids for k in rec.get("children") or ()):
                raise ValueError(f"{METHOD}: parent {ln['line_id']} names a child not in the lines")
            if abs((rec.get("closure") or {}).get("residual_lm", 1)) > TOL:
                raise ValueError(f"{METHOD}: parent {ln['line_id']} run does not close")
            out["parents_held" if act == "PARENT_HELD" else "parents_na"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.46 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not the code this version may change or add")
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_46_lines": len(out), "v3_0_46_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3043.check_earthworks(out), "skirting": A3044.check_skirting(out),
             "blinding": A3045.check_blinding(out), "stair_rooms": check_stair_rooms(out, prev)}
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
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_46": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "room_id", "element_id", "unit",
              "v2_9", "base", "v3_0_46", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_46")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "room_id": r.get("room_id") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_46": q(r.get("after_v3_0_46")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    b = {ln["line_id"]: ln for ln in prev}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in new:
        o = b.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_base": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_46": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_46_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = {k: {"base": t0.get(k), "v3_0_46": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k in moved:
        if k.split("|")[0] != CODE:
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_46_BOQ_LINES.json": BL.dumps(new),
             "V3_0_46_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_46_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_46_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_46_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_46_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_side", "check_jambs", "overlaps", "measure", "check_stair_rooms", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError"]
