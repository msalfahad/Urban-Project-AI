"""ARCH_TAKEOFF_V3.0.60 (T-314, lane I, stage r1): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.59
(engine.source.arch_v30 .. arch_v3059), with ONE new piece, the EXTERIOR PLASTER / SIGMA FACE ROWS of the
Checker-verified facade face ledger, booked into the FIN.EXT.FINISH lines by face, never by run x storey height:

  FACADE_FACES  every drawn exterior face band is ONE row with its element (STOREY / PARAPET_OUTER / PARAPET_INNER /
                PARAPET_TOP / PLINTH / SLAB_EDGE), its levels and its area (point, range or blank); every opening is
                ONE hole on the face that holds it (fixed area, or a HELD range 0 .. cap). A FIN.EXT.FINISH line is the
                sum of its face rows: gross = sum of faces, net = gross - fixed holes; a HELD hole or a HELD face makes
                the line a bounded range with NO point value; a blank face (no printed dimension) makes the line blank.

R-T314-1 (every villa): (1) a line takes face rows of ONE element only: a parapet / plinth / slab-edge band in a STOREY
line is refused (the element owns the band, never the formula of the floor whose outline draws it); (2) a STOREY face
lies inside one level part [F.F.L., next level) of its line (a two-F.F.L. ground floor is two parts of one line); a band
crossing a part boundary is refused until split; (3) every face once, every opening once, on a face of the same line,
its sill / head inside the face band, never larger than the face; a HELD hole has a cap above 0; (4) a HELD face or
hole is never 0: blank stays blank, a range stays a range (no point value); DRAWING-CONFIRMED faces carry one value;
(5) the existing line keeps its id, element and rule (CHANGE), the new lines are ADDED with their element; every other
V3.0.59 line is byte-identical (asserted); totals move only in FIN.EXT.FINISH (asserted); (6) the owner manual method
(OWNER_NOTES_SIGMA 2026-10-21, Q-07 B bands from the floor, Q-73 full holes) is recorded BESIDE each line, never as its
quantity; (7) every line figure is recomputed here from the rows and asserted equal to the expected figure of the
inputs (the merged ledgers' own figure).

m.l items (corners, drips, copings) are never FIN.EXT.FINISH m2 rows (refused); they are listed as named MISSING items
of this stage until their item codes have a registry family. Nothing here names a project, a sheet or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import math

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3058 as A3058
from engine.source import arch_v3059 as A3059

DEFAULT_GUARD_CLASS = "TOOLING"          # books Checker-merged face ledgers; computes sums of their rows only
METHOD = "ARCH_TAKEOFF_V3.0.60"
EXTENDS = A3059.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T314_ARCH_V3_0_60"
INPUTS_SCHEMA = "URBAN_V3060_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3060_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
RULE_ID = "R-T314-1"
RULE_VERSION = "1.0.0"
REC_KEY = "facade_faces_v3060"
P_FACE = "FACADE_FACES"
CODE = "FIN.EXT.FINISH"
UNIT = "m2"
FAMILY = "B4"
ELEMENTS = ("STOREY", "PARAPET_OUTER", "PARAPET_INNER", "PARAPET_TOP", "PLINTH", "SLAB_EDGE")
LEVELLED = ("STOREY", "PARAPET_OUTER", "PLINTH")       # bands with a bottom / top level (a slab edge has none printed)
STATUS = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD")
LINEAR_UNITS = ("lm", "m.l", "m")
TOL = 1e-6
FACE_TOL = 0.0005
MM_GUARD_AREA = 5000.0                   # m2 of one face: above it is a unit error (mm2 / cm2)
MM_GUARD_LEVEL = 200.0                   # m: a level above it is millimetres
ITEM_TEXT = ("Exterior plaster / Sigma finish (face rows)", "لياسة خارجية / سيجما (حسب الواجهات)")
PIECES = {P_FACE: {
    "policy": "R-T314-1: face rows of the Checker-verified facade ledger, one element per line, holes once by face",
    "owner_manual_method": "OWNER_NOTES_SIGMA 2026-10-21: Sigma is the exterior plaster area; Q-07 B bands measured "
                           "from the floor; every actual opening deducted in full where masonry exists (Q-73 A); "
                           "corners their own m.l line (owner correction 2026-10-22)",
    "drawing_method": "drawn face band length x band height by element and levels; openings by schedule size on the "
                      "face that holds them; plinth / parapet / slab-edge bands each their own line"}}
WAITING = dict(A3059.WAITING)


class InputsError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _num(x, where, hi):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise InputsError(f"{where}: {x!r} is not a non-negative number")
    if x > hi:
        raise InputsError(f"{where}: {x} is above {hi} (millimetres or a unit error: refused)")
    return float(x)


def _lvl(x, where):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise InputsError(f"{where}: {x!r} is not a level")
    if abs(x) > MM_GUARD_LEVEL:
        raise InputsError(f"{where}: level {x} is millimetres (refused)")
    return float(x)


# ================================================================================================ inputs
def load_inputs(doc, project_id=None):
    """URBAN_V3060_INPUTS_V1 -> checked dict:
        {"schema", "project", "sources": [{task, file, sha256, merge_commit, checker_run}],
         "lines": [{"key", "line_id" (existing FIN.EXT.FINISH line) | null, "element", "floor", "element_id" (new),
                    "parts": [[bottom, top], ...] (levelled elements), "why_held"}],
         "faces": [{"face_id", "line", "element", "bottom", "top", "lo", "hi", "status", "owner_q07"}],
         "openings": [{"opening_id", "face_id", "hole_m2" | null, "cap_m2" (held), "status", "sill", "head"}],
         "items": [{"key", "unit", "status", "why"}]  (named MISSING m.l / unregistered items, never a number here),
         "expect": {line key: {"gross": [lo, hi] | null, "net": [lo, hi] | null}}}"""
    if not isinstance(doc, dict) or doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"inputs schema is not {INPUTS_SCHEMA}")
    if project_id is not None and doc.get("project") not in (None, project_id):
        raise InputsError("inputs name another project")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("no source ledger named")
    for s in srcs:
        for k in ("task", "file", "sha256", "merge_commit", "checker_run"):
            if not s.get(k):
                raise InputsError(f"source {s.get('task')}: missing {k}")
    lines = {}
    for ln in doc.get("lines") or ():
        k = ln.get("key")
        if not k or k in lines:
            raise InputsError(f"line key {k!r} missing or repeated")
        el = ln.get("element")
        if el not in ELEMENTS:
            raise InputsError(f"{k}: element {el!r} is not one of {ELEMENTS}")
        if not ln.get("line_id") and not ln.get("element_id"):
            raise InputsError(f"{k}: a new line names its element id")
        parts = []
        for p in ln.get("parts") or ():
            b, t = _lvl(p[0], f"{k} part"), _lvl(p[1], f"{k} part")
            if not b < t:
                raise InputsError(f"{k}: a level part needs bottom < top")
            parts.append((b, t))
        if el in LEVELLED and not parts:
            raise InputsError(f"{k}: a {el} line states its level parts")
        lines[k] = dict(ln, parts=sorted(parts))
    faces, by_line = {}, {k: [] for k in lines}
    for f in doc.get("faces") or ():
        fid, k = f.get("face_id"), f.get("line")
        if not fid or fid in faces:
            raise InputsError(f"face {fid!r} missing or booked twice (every face once)")
        if k not in lines:
            raise InputsError(f"face {fid}: line {k!r} is not an input line")
        L = lines[k]
        if f.get("element") != L["element"]:
            raise InputsError(f"face {fid}: a {f.get('element')} band in the {L['element']} line {k} (R-T314-1 (1))")
        st = f.get("status")
        if st not in STATUS:
            raise InputsError(f"face {fid}: status {st!r}")
        lo, hi = f.get("lo"), f.get("hi")
        if (lo is None) != (hi is None):
            raise InputsError(f"face {fid}: a range names both ends")
        if lo is not None:
            lo, hi = _num(lo, f"face {fid} lo", MM_GUARD_AREA), _num(hi, f"face {fid} hi", MM_GUARD_AREA)
            if lo > hi + TOL:
                raise InputsError(f"face {fid}: lo > hi")
            if st != "HELD" and abs(hi - lo) > TOL:
                raise InputsError(f"face {fid}: a {st} face carries one value, not a range")
            if st == "HELD" and hi <= TOL:
                raise InputsError(f"face {fid}: a HELD face carried as 0 (blank or a range, never 0)")
        elif st != "HELD":
            raise InputsError(f"face {fid}: a {st} face without an area")
        b = t = None
        if L["element"] in LEVELLED:
            b = None if f.get("bottom") is None else _lvl(f.get("bottom"), f"face {fid}")
            t = None if f.get("top") is None else _lvl(f.get("top"), f"face {fid}")
            if (b is None or t is None) and st != "HELD":
                raise InputsError(f"face {fid}: a {st} face states both levels (an unprinted level is HELD)")
            if b is None and t is None:
                raise InputsError(f"face {fid}: a {L['element']} band states at least one printed level")
            if b is not None and t is not None and not b < t:
                raise InputsError(f"face {fid}: bottom < top")
            bb, tt = (t if b is None else b), (b if t is None else t)
            if not any(pb - TOL <= bb and tt <= pt + TOL for pb, pt in L["parts"]):
                raise InputsError(f"face {fid}: band {b} -> {t} crosses a level part of {k} {L['parts']} "
                                  f"(split it first, R-T314-1 (2))")
        faces[fid] = dict(f, lo=lo, hi=hi, bottom=b, top=t)
        by_line[k].append(fid)
    ops = {}
    for o in doc.get("openings") or ():
        oid, fid = o.get("opening_id"), o.get("face_id")
        if not oid or oid in ops:
            raise InputsError(f"opening {oid!r} missing or deducted twice (every opening once)")
        F = faces.get(fid)
        if F is None:
            raise InputsError(f"opening {oid}: face {fid!r} is not an input face")
        st = o.get("status")
        if st not in STATUS:
            raise InputsError(f"opening {oid}: status {st!r}")
        if st == "HELD":
            if o.get("hole_m2") is not None:
                raise InputsError(f"opening {oid}: a HELD hole carries no point value")
            cap = _num(o.get("cap_m2"), f"opening {oid} cap", MM_GUARD_AREA)
            if cap <= TOL:
                raise InputsError(f"opening {oid}: a HELD hole bounded at 0 (name its cap)")
            hole = None
        else:
            hole, cap = _num(o.get("hole_m2"), f"opening {oid} hole", MM_GUARD_AREA), None
        size = hole if hole is not None else cap
        if F["lo"] is not None and size > F["hi"] + FACE_TOL:
            raise InputsError(f"opening {oid}: hole {size} m2 larger than its face {fid} ({F['hi']} m2)")
        if o.get("sill") is not None and o.get("head") is not None:
            s, h = _lvl(o["sill"], f"opening {oid}"), _lvl(o["head"], f"opening {oid}")
            if not s < h:
                raise InputsError(f"opening {oid}: sill < head")
            if (F["bottom"] is not None and s < F["bottom"] - TOL) or (F["top"] is not None and h > F["top"] + TOL):
                raise InputsError(f"opening {oid}: {s} -> {h} leaves its band {F['bottom']} -> {F['top']}")
        ops[oid] = dict(o, hole_m2=hole, cap_m2=cap)
    items = []
    for it in doc.get("items") or ():
        if any(it.get(k) is not None for k in ("value", "lo", "hi", "quantity")):
            raise InputsError(f"item {it.get('key')}: a named MISSING item carries no number in this stage")
        items.append({"key": it.get("key"), "unit": it.get("unit"), "status": it.get("status"),
                      "why": str(it.get("why") or "")[:300]})
    return {"project": doc.get("project"), "sources": srcs, "lines": lines, "faces": faces, "by_line": by_line,
            "openings": ops, "items": items, "expect": doc.get("expect") or {}}


# ================================================================================================ the rule
def line_figures(d, key):
    """R-T314-1: one line from its face rows -> gross / fixed / held / net and the line state."""
    fids = d["by_line"][key]
    if not fids:
        raise InputsError(f"{key}: a line with no face row")
    F = [d["faces"][f] for f in fids]
    O = [o for o in d["openings"].values() if o["face_id"] in fids]
    fixed = sum(o["hole_m2"] for o in O if o["hole_m2"] is not None)
    held = sum(o["cap_m2"] for o in O if o["cap_m2"] is not None)
    blank = [f["face_id"] for f in F if f["lo"] is None]
    out = {"faces": len(F), "faces_blank": blank, "openings": len(O), "deduct_fixed": _r(fixed),
           "deduct_held": [0.0, _r(held)] if held else None,
           "assumed_holes": _r(sum(o["hole_m2"] for o in O if o["status"] == "ASSUMED — OWNER-APPROVED")),
           "owner_q07": _r(sum(float(f["owner_q07"]) for f in F if f.get("owner_q07") is not None))
           if any(f.get("owner_q07") is not None for f in F) else None}
    if blank:
        return dict(out, gross=None, net=None, state="BLANK")
    g_lo, g_hi = sum(f["lo"] for f in F), sum(f["hi"] for f in F)
    n_lo, n_hi = g_lo - fixed - held, g_hi - fixed
    if n_lo < -FACE_TOL:
        raise InputsError(f"{key}: holes {_r(fixed + held)} m2 exceed the faces {_r(g_lo)} m2")
    out = dict(out, gross=[_r(g_lo), _r(g_hi)], net=[_r(max(n_lo, 0.0)), _r(n_hi)])
    if abs(n_hi - n_lo) > TOL or any(f["status"] == "HELD" for f in F) or \
            any(o["status"] == "HELD" for o in O):
        return dict(out, state="RANGE")
    st = "ASSUMED" if (any(f["status"] != "DRAWING-CONFIRMED" for f in F) or
                       any(o["status"] != "DRAWING-CONFIRMED" for o in O)) else "DC"
    return dict(out, state=st)


def _rec(d, key, fig, **kw):
    s = d["sources"]
    L = d["lines"][key]
    return dict({"piece": P_FACE, "policy": PIECES[P_FACE]["policy"], "line_key": key, "element": L["element"],
                 "tasks": [x["task"] for x in s], "ledgers": [x["file"] for x in s],
                 "ledger_sha256": [x["sha256"] for x in s], "merge_commits": [x["merge_commit"] for x in s],
                 "checker_runs": [x["checker_run"] for x in s], "rule_id": RULE_ID, "rule_version": RULE_VERSION,
                 "face_ids": sorted(d["by_line"][key]),
                 "opening_ids": sorted(o for o, x in d["openings"].items() if x["face_id"] in d["by_line"][key]),
                 "figures": fig, "owner_manual_method": PIECES[P_FACE]["owner_manual_method"],
                 "owner_q07_beside_m2": fig["owner_q07"], "release_status": "NOT RELEASED"}, **kw)


def _shape(fig):
    """-> (evidence_state, measured_net, bounded_range, evidence_status)."""
    if fig["state"] == "BLANK":
        return "BLOCKED_RFI", None, None, "HELD"
    if fig["state"] == "RANGE":
        return ("BOUNDED_EXPOSURE", None, {"low": fig["net"][0], "high": fig["net"][1],
                                           "basis": "HELD face / hole: a named range, no point value (R-T314-1 (4))"},
                "HELD")
    return ("MEASURED" if fig["state"] == "DC" else "PROVISIONAL", fig["net"][0], None,
            "DRAWING-CONFIRMED" if fig["state"] == "DC" else "ASSUMED — OWNER-APPROVED")


def _gross(fig, ev):
    """a numeric gross only on a point line (a bounded / blank line states one state: its range, R-T241 / V3.0.24)."""
    if ev not in ("MEASURED", "PROVISIONAL") or fig["gross"] is None or fig["gross"][0] != fig["gross"][1]:
        return None
    return fig["gross"][0]


def _formula(fig):
    if fig["gross"] is None:
        return f"HELD: {len(fig['faces_blank'])} face(s) without a printed dimension: blank by name, never 0"
    g = fig["gross"]
    gs = f"{g[0]}" if g[0] == g[1] else f"{g[0]} .. {g[1]}"
    h = f" - HELD holes 0 .. {fig['deduct_held'][1]}" if fig["deduct_held"] else ""
    n = fig["net"]
    ns = f"{n[0]}" if n[0] == n[1] else f"{n[0]} .. {n[1]}"
    return (f"sum of {fig['faces']} face rows {gs} m2 - {fig['openings']} holes fixed {fig['deduct_fixed']} m2{h} = "
            f"{ns} m2 (R-T314-1)")


def _question(d, key, fig):
    L = d["lines"][key]
    return (L.get("why_held") or f"{fig['faces_blank'] or 'a held face / hole'} on {key}: the printed dimension")[:400]


def changed_line(before, d, key):
    fig = line_figures(d, key)
    ev, net, br, es = _shape(fig)
    ln = copy.deepcopy(before)
    ln["evidence_state"], ln["measured_net"], ln["bounded_range"] = ev, net, br
    ln["gross"] = _gross(fig, ev)
    ln["deductions"] = []
    ln["calculation"] = {"formula": _formula(fig)[:1500],
                         "inputs": dict(copy.deepcopy(before["calculation"].get("inputs") or {}),
                                        **{REC_KEY: _rec(d, key, fig, evidence_status=es),
                                           "evidence_status": es})}
    ln["rfi"] = {"question": _question(d, key, fig), "blocks": [before["line_id"]]} if ev in (
        "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None
    ln["notes"] = (f"{METHOD}: face rows by element ({d['lines'][key]['element']}), holes once by face; owner Q-07 B "
                   f"part {fig['owner_q07']} m2 beside; NOT RELEASED")
    return A3046._fin(ln), fig, es


def new_line(tpl, d, key):
    from engine.source import boq_line as BL
    fig = line_figures(d, key)
    ev, net, br, es = _shape(fig)
    L = d["lines"][key]
    rec = _rec(d, key, fig, evidence_status=es, geometry_line_id=tpl["line_id"])
    g = _gross(fig, ev)
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=ev, measured_net=net, gross=g, bounded_range=br,
        element_id=L["element_id"], floor=L.get("floor"), physical_element=f"exterior finish face band: {L['element']}",
        formula=_formula(fig)[:1500], inputs={REC_KEY: rec, "evidence_status": es},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "BY_SPEC",
        rfi=None if ev == "MEASURED" or ev == "PROVISIONAL" else {"question": _question(d, key, fig), "blocks": []},
        notes=f"{METHOD}: its own line by element (never folded into a storey line); owner Q-07 B part "
              f"{fig['owner_q07']} m2 beside; NOT RELEASED",
        item_en=tpl.get("item_en") or ITEM_TEXT[0], item_ar=tpl.get("item_ar") or ITEM_TEXT[1], trade=tpl["trade"],
        subtrade=tpl.get("subtrade"))
    return A3046._fin(ln), fig, es


def changes_for(doc, prev):
    """-> (changes, log). CHANGE the named FIN.EXT.FINISH lines in place (same id), ADD the new element lines."""
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.60 face records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    have = set(by)
    ext = [ln for ln in prev if ln["item_code"] == CODE]
    named = {L["line_id"] for L in doc["lines"].values() if L.get("line_id")}
    for lid in named:
        ln = by.get(lid)
        if ln is None or ln["item_code"] != CODE:
            raise InputsError(f"{lid} is not a {CODE} line of the base (stale binding)")
    left = sorted(ln["line_id"] for ln in ext if ln["line_id"] not in named)
    if left:
        raise InputsError(f"{CODE} line(s) of the base not bound by the face rows: {left}")
    tpl = by[sorted(named)[0]] if named else None
    changes, log = [], {"piece": P_FACE, "changed": 0, "added": 0, "by_state": {}, "missing_items": doc["items"]}
    for key in sorted(doc["lines"]):
        L = doc["lines"][key]
        if L.get("line_id"):
            before = by[L["line_id"]]
            after, fig, es = changed_line(before, doc, key)
            act = "CHANGE"
            log["changed"] += 1
        else:
            if tpl is None:
                raise InputsError("a new face line needs an existing line of the base as its template")
            after, fig, es = new_line(tpl, doc, key)
            if after["line_id"] in have:
                raise InputsError(f"{key}: an added line repeats a candidate id")
            have.add(after["line_id"])
            before, act = None, "ADD"
            log["added"] += 1
        log["by_state"][es] = log["by_state"].get(es, 0) + 1
        changes.append({"piece": P_FACE, "action": act, "step": f"{act}_FACE_LINE", "before": before, "after": after,
                        "line_key": key, "figures": fig, "evidence_status": es,
                        "held": None if es != "HELD" else [{"what": key, "why": _question(doc, key, fig)}],
                        "verification": {"task": "T-305 / T-311 / T-324 / T-337 / T-349",
                                         "merge_commits": [s["merge_commit"] for s in doc["sources"]]}})
    check_expect(changes, doc["expect"])
    return changes, log


def check_expect(changes, expect):
    """each expected figure (line key -> gross / net [lo, hi] | None) equals the recomputed one."""
    got = {c["line_key"]: c["figures"] for c in changes}
    for key, e in expect.items():
        g = got.get(key)
        if g is None:
            raise InputsError(f"{key}: expected, but no line was built")
        for k in ("gross", "net"):
            if k not in e:
                continue
            a, b = g[k], e[k]
            if (a is None) != (b is None) or (a is not None and any(abs(x - y) > TOL for x, y in zip(a, b))):
                raise InputsError(f"{key} {k}: line {a} != expected {b} (the merged ledgers' figure)")
    return True


def check_faces(lines):
    """every V3.0.60 face record: one element per line, held never 0, a range never a point, faces / holes once."""
    seen_f, seen_o, n = {}, {}, 0
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        n += 1
        if ln["item_code"] != CODE or ln["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {ln['line_id']} a face record on {ln['item_code']} {ln['unit']}")
        for f in rec["face_ids"]:
            if f in seen_f:
                raise ValueError(f"{METHOD}: face {f} booked in two lines ({seen_f[f]}, {ln['line_id']})")
            seen_f[f] = ln["line_id"]
        for o in rec["opening_ids"]:
            if o in seen_o:
                raise ValueError(f"{METHOD}: opening {o} deducted on two lines")
            seen_o[o] = ln["line_id"]
        if rec["evidence_status"] == "HELD" and ln["measured_net"] is not None:
            raise ValueError(f"{METHOD}: {ln['line_id']} a HELD face line carries a point value")
        br = ln.get("bounded_range")
        if br and br["high"] <= TOL:
            raise ValueError(f"{METHOD}: {ln['line_id']} a held range carried as 0")
    return {"face_lines": n, "faces": len(seen_f), "openings": len(seen_o)}


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.60 lines, identity). Changed lines in place, added lines follow; every other line byte-identical."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, adds, repl = list(prev), [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change or add")
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
    same = [x for x in prev if x["line_id"] not in repl]
    bad = [x["line_id"] for x in same if A30.line_sha(x) != A30.line_sha(out[sid[x["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) outside the named changes differ")
    _l59, ident59 = A3059.integrate(out, [], for_lead)        # every V3.0.10 .. V3.0.59 check on the result
    ident = {"base_lines": len(prev), "v3_0_60_lines": len(out), "v3_0_60_rows": len(changes),
             "replaced": len(repl), "added": len(adds),
             "v3_0_59_checks": {k: v for k, v in ident59.items()
                                if k not in ("base_lines", "v3_0_59_lines", "v3_0_59_rows", "replaced", "added",
                                             "outside_rows", "outside_rows_identical_to_base", "outside_rows_sha256")},
             "faces": check_faces(out), "outside_rows": len(same), "outside_rows_identical_to_base": len(same),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in same).encode()).hexdigest()}
    return out, ident


def check_totals(t0, t1):
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] != CODE:
            raise ValueError(f"{METHOD}: totals moved outside {CODE}: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_60": t1.get(k),
                    "view_base": None if t0.get(k) is None else A3058.total_view(t0[k]),
                    "view_v3_0_60": None if t1.get(k) is None else A3058.total_view(t1[k])}
    return moved


def ledger_rows(changes, released_lines=None):
    rows = []
    for c in changes:
        a = c["after"]
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["step"], "change": c["action"],
                     "line_id": a["line_id"], "line_key": c["line_key"], "item_code": a["item_code"],
                     "family": FAMILY, "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "element": rec["element"], "unit": a["unit"], "before_base": A30._qty(c["before"]),
                     "after_v3_0_60": A30._qty(a), "figures": c["figures"], "evidence_status": c["evidence_status"],
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[P_FACE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[P_FACE]["drawing_method"], "record": rec,
                     "verification": c["verification"], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "change", "line_id", "line_key", "item_code", "element", "floor", "element_id",
              "unit", "base", "v3_0_60", "owner_q07_beside", "evidence_status", "still_held")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_60")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
                       "line_key": r["line_key"], "item_code": r["item_code"], "element": r["element"],
                       "floor": r.get("floor") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "base": q(r.get("before_base")), "v3_0_60": q(r.get("after_v3_0_60")),
                       "owner_q07_beside": "" if r["figures"]["owner_q07"] is None else r["figures"]["owner_q07"],
                       "evidence_status": r["evidence_status"],
                       "still_held": "; ".join(f"{x['what']}: {x['why']}" for x in (r.get("still_held") or ()))[:300]}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_60=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_60_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
        dsum[d["vs_base"]] = dsum.get(d["vs_base"], 0) + 1
    ident = dict(ident, diff={"vs_base": dsum})
    t1 = A304.code_totals(new)
    moved = check_totals(A304.code_totals(prev), t1)
    view = A3058.totals_view(t1)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "code_totals_view": {k: v for k, v in view.items()
                                                               if k.split("|")[0] == CODE},
           "missing_items": log["missing_items"], "waiting_pieces": WAITING}
    files = {"V3_0_60_BOQ_LINES.json": BL.dumps(new),
             "V3_0_60_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_60_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_60_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_60_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_60_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": [CODE]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODE", "ELEMENTS", "load_inputs",
           "line_figures", "changes_for", "check_expect", "check_faces", "integrate", "check_totals", "ledger_rows",
           "diff_rows", "write", "InputsError"]
