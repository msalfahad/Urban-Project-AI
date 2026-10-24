"""ARCH_TAKEOFF_V3.0.13 (T-268): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.12 (engine.source.arch_v30,
arch_v301 .. arch_v3012), extended with ONE door-ruling piece: the doors a checker verdict rules leave the held door
lines for the settled pcs AND m2 lines of the ruled class. Not a new method family and not the released default (owner
management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a door is ONE structural opening between the masonry ends (the wall
face line ends on BOTH faces; the door block frame, the leaf and a fabrication frame are symbols, never the opening),
of the class its two side spaces give it (exterior on one side = aluminium, UP-DOOR-CLS-001 .. 006; a main entrance
only with entrance evidence, never by adjacency), counted once and measured once (width x height; head 2.20 only where
no sheet prints one, Q-55 C, ASSUMED - OWNER-APPROVED). V3.0.10 (T-232) carries every door in the type / floor lines
of its class, a door whose class or width was open HELD in each candidate class (from 0). A checker ruling settles the
door: it leaves every held line it was in, in every candidate class and in both units, and enters the settled pcs and
m2 lines of ONE class, with the same opening id in both units (the same-openings rule of V3.0.10).

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.13`):
  1. the run is the V3.0.12 candidate exactly: its V3_0_* .. V3_0_12_* files are written unchanged (arch_v30 ..
     arch_v3012 are not edited);
  2. DOOR_RULING (project inputs URBAN_V3013_INPUTS_V1): one ruling per door, from a checker-merged verdict (source
     file sha256, task, merge commit, checker run): the door's full opening record (the V3.0.10 record schema, checked
     by its own rules), the class and width the checker RULED, the candidate classes it was held in and the census
     width the masonry / finish deductions of the same opening carry;
  3. the candidate's door lines (the V3.0.10 opening policy, item codes and floors of the piece) are read back into
     their per-opening tables. FAITHFULNESS CHECK: every one of those lines is regenerated from its own table by the
     V3.0.10 code and must be byte-identical to the line the candidate carries, or the run is refused (the lines this
     version writes are therefore the V3.0.10 lines of the new membership, never a hand-built line);
  4. each ruled door must be HELD in exactly the candidate classes the ruling names, on its floor, in both units, and
     settled nowhere (a door ruled twice, or a ruling of a door the candidate does not hold, is refused); its held
     entries leave every line, its ruled record enters the lines of its class. A ruled width outside the width range
     the candidate held needs a stated why; a ruled width that differs from the census width the deductions use needs
     a downstream entry naming the package that carries the deduction change (never applied here, never twice);
  5. per (item code, floor, unit, part): a line whose membership is unchanged stays byte-identical; a line whose
     membership changes is REPLACED by the V3.0.10 line of the new membership (same line id); a line left with no
     opening is retired (NOT_APPLICABLE_WITH_EVIDENCE, its figure kept as information); a new group is ADDED. The
     per-code totals after the ruling must equal the declared totals;
  6. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.13 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  7. the V3_0_13_* files are written beside them: every line outside the V3.0.13 rows is byte-identical to the V3.0.12
     line (asserted on every run), and V3_0_13_DIFF.csv lists every line against V3.0.12 and against the released V2.9.

Rules: UP-DOOR-CLS-001 .. 006 (door class by the spaces on each side), UP-DOOR-AREA-001 (door m2 = opening width x
height), Q-55 C (head 2.20 only where no sheet prints one: ASSUMED - OWNER-APPROVED), Q-67 A (a passage open at its
mouth is exterior), R-DOOR-EVID-1 (T-260, proposed: the opening between the wall-face line ends on both faces; class
from the side spaces by drawing evidence); owner 2026-10-23 17:50 (pcs and m2 from one opening definition);
UP-QTY-STATUS-001 (held is a range or blocked, never 0); WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2.1,
s.2.2, s.3, s.7. Nothing here names a project, a sheet, a layer, a room or a coordinate; every number comes from the
run or the inputs.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v308 as A308
from engine.source import arch_v309 as A309
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.13"
EXTENDS = A3012.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T268_ARCH_V3_0_13"
LEDGER_SCHEMA = "URBAN_V3013_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3013_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
OPENINGS_POLICY = A3010.PIECES["OPENINGS"]["policy"]
AS = "ASSUMED - OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
RULED_DIM_STATUS = ("VERIFIED", DC, AS)  # a ruled width may be VERIFIED (checker re-measured both faces)
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
WIDTH_TOL_M = 0.0005                    # a ruled width vs the census / held width (3-decimal ledgers)
InputsError = A307.InputsError
_num = A307._num

PIECES = {
    "DOOR_RULING": {
        "module": "engine/source/arch_v3013.py (checker-ruled doors into the type / floor lines of their class)",
        "policy": "DOOR_RULING_V1", "rule_id": "UP-DOOR-CLS-001", "rule_version": "owner-2026-10-19",
        "owner_rules": ["UP-DOOR-CLS-001 .. 006 (door class by the spaces on each side; main entrance only with "
                        "entrance evidence)",
                        "UP-DOOR-AREA-001 (door m2 = structural opening width x height)",
                        "Q-55 C (door head 2.20 m only where no sheet prints one: ASSUMED - OWNER-APPROVED)",
                        "Q-67 A (a side passage open at its mouth is exterior)",
                        "owner 2026-10-23 17:50 (doors: counts AND measured m2 from one opening definition)",
                        "UP-QTY-STATUS-001 (a held door is a range or blocked, never 0)"],
        "owner_manual_method": "manual QS door schedule: one row per door type and floor, the number of doors and the "
                               "area of each (structural opening width x height, 2.20 high where no sheet prints the "
                               "head), the class by what the door opens onto",
        "drawing_method": "each door's opening between the wall-face line ends on BOTH wall faces at the door insert "
                          "(the door block frame, leaf and fabrication frame are symbols); the class from both side "
                          "spaces on the plan (an open passage mouth confirmed on a second sheet; a main entrance only "
                          "with entrance evidence); ruled by the Checker's own re-measure"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3012.WAITING)
WAITING.update({
    "DOOR_HEADS_PRINTED": "door heights stay Q-55 C 2.20 ASSUMED - OWNER-APPROVED where no sheet prints a head; a door "
                          "line is whole-line VERIFIED only on measured heights (none printed for the settled doors)",
    "MAIN_ENTRANCE_D53": "the main entrance stays HELD (render single leaf vs plan / elevation double; designer D-53)",
    "PVC_WIDTH_REVIEW": "the PVC doors held on width (leaf vs closure readings) stay HELD until a checker ruling",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ project inputs
def _width_value(o):
    w = o.get("width") or {}
    return float(w["value"]) if _num(w.get("value")) else None


def _check_ruling(r, codes, floors):
    oid = r.get("id")
    if not oid:
        raise InputsError("every ruling names its door (the census opening id)")
    for k in ("verdict", "verified_by", "ruled_class", "held_in", "record"):
        if not r.get(k):
            raise InputsError(f"ruling {oid}: {k} is required (a door is settled only by a checker ruling)")
    if r["ruled_class"] not in codes:
        raise InputsError(f"ruling {oid}: ruled class {r['ruled_class']!r} is not an item code of the piece")
    if not (isinstance(r["held_in"], list) and set(r["held_in"]) <= set(codes) and
            len(set(r["held_in"])) == len(r["held_in"])):
        raise InputsError(f"ruling {oid}: held_in lists the candidate classes the door is held in, each once")
    o = r["record"]
    if o.get("id") != oid or o.get("kind") != "DOOR":
        raise InputsError(f"ruling {oid}: the record is this door's (id {o.get('id')!r}, kind DOOR)")
    if o.get("classes") != [r["ruled_class"]]:
        raise InputsError(f"ruling {oid}: a ruled door carries ONE class, the ruled one ({o.get('classes')})")
    if o.get("class_hold"):
        raise InputsError(f"ruling {oid}: a ruled door has no class hold")
    # the V3.0.10 record rules; a VERIFIED width (the checker's own both-face re-measure) is at least DRAWING-CONFIRMED
    chk = copy.deepcopy(o)
    for d in ("width", "height"):
        st = (chk.get(d) or {}).get("status")
        if st not in RULED_DIM_STATUS:
            raise InputsError(f"ruling {oid}: {d} status {st!r} not one of {RULED_DIM_STATUS}")
        if st == "VERIFIED":
            if not (chk[d].get("verified_by")):
                raise InputsError(f"ruling {oid}: a VERIFIED {d} names the checker run that re-measured it")
            chk[d]["status"] = DC
    A3010._check_opening(chk, codes, floors)
    if o["pcs"]["state"] != "SETTLED":
        raise InputsError(f"ruling {oid}: a ruling settles the count (a door still held is not ruled: leave it out)")
    w = _width_value(o)
    cw = r.get("census_width")
    if not _num(cw):
        raise InputsError(f"ruling {oid}: census_width (the width the masonry / finish deductions carry) is required")
    if w is not None and abs(w - float(cw)) > WIDTH_TOL_M and not r.get("downstream"):
        raise InputsError(f"ruling {oid}: ruled width {w} != census width {cw}: name the package that carries the "
                          "deduction change (downstream); it is never applied here")


def load_inputs(doc, project_id=None):
    """URBAN_V3013_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "DOOR_RULING", "item_codes": [...], "source": {file, sha256, task, merge_commit,
                     checker_run}, "sources": [...],
                     "base": {"task", "merge_commit"} (the opening package whose lines are regenerated: V3.0.10),
                     "scope": {"floors"},
                     "rulings": [{id, ruled_class, held_in: [item codes], verdict, verified_by, census_width,
                                  outside_range_why, downstream: [...], record: V3.0.10 opening record}],
                     "declared_totals": {item_code: {"pcs": {settled, held: [low, high], no_figure},
                                                     "m2": {released, bounded: [low, high], unquantified}}}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p != "DOOR_RULING" or p in seen:
            raise InputsError(f"piece {p!r}: DOOR_RULING, once")
        seen.add(p)
        codes = pc.get("item_codes")
        if not (isinstance(codes, list) and codes and all(c.startswith("DOOR.") for c in codes)
                and len(set(codes)) == len(codes)):
            raise InputsError(f"piece {p}: item_codes are door item codes, each once")
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        b = pc.get("base") or {}
        if not b.get("task") or not b.get("merge_commit"):
            raise InputsError(f"piece {p}: base (task, merge_commit of the opening package regenerated) is required")
        sc = pc.get("scope") or {}
        if not sc.get("floors"):
            raise InputsError(f"piece {p}: scope needs floors")
        ids = set()
        for r in pc.get("rulings") or ():
            if r.get("id") in ids:
                raise InputsError(f"piece {p}: door {r.get('id')} ruled twice")
            _check_ruling(r, codes, sc["floors"])
            ids.add(r["id"])
        if not ids:
            raise InputsError(f"piece {p}: no rulings")
        if not pc.get("declared_totals"):
            raise InputsError(f"piece {p}: declared_totals per item code (the line after the ruling) are required")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ read back / regroup
def _door_lines(pc, lines):
    codes, fl = set(pc["item_codes"]), pc["scope"]["floors"]
    out = []
    for ln in lines:
        if ln["item_code"] not in codes:
            continue
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        if inp.get("policy") != OPENINGS_POLICY or ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        floor = (ln.get("location") or {}).get("floor")
        if floor not in fl:
            raise InputsError(f"door line {ln['line_id']} on floor {floor!r} outside the scope {fl}: every door line "
                              "is accounted for")
        out.append(ln)
    return out


def _key(ln):
    agg = ln["calculation"]["inputs"]["aggregation_key"]
    return (agg["item_code"], agg["floor"], agg["unit"], agg["part"])


def _assumption(e):
    """an opening's owner-approved fallback, from its own dimension records (the V3.0.10 record carries it as the
    source of the assumed dimension)."""
    for d in ("width", "height"):
        x = e.get(d) or {}
        if x.get("status") == AS:
            return x.get("source")
    return None


def _regen(pid, rev, docs, base_src, key, entries):
    pcx = {"source": base_src, "openings": [{"id": e["id"], "assumption": _assumption(e)} for e in entries]}
    ln, evs, held = A3010.group_line(pid, rev, docs, pcx, key, entries)
    return ln, evs, held


def _entries(o, code):
    """the table entries of one opening record in one class (both units), as V3.0.10 group_openings builds them."""
    out = {}
    for unit, fn in (("pcs", A3010._part_pcs), ("m2", A3010._part_m2)):
        part, q, rg = fn(o, code)
        a = A3010.area_of(o)
        rec = o["pcs"] if unit == "pcs" else o["m2"]
        status = part.split(":", 1)[1] if part.startswith("SETTLED") else (rec.get("evidence_status") or "HELD")
        out[unit] = (part, {"id": o["id"], "kind": o["kind"], "qty": q, "range": rg, "width": o.get("width"),
                            "height": o.get("height"),
                            "area_from_dims": None if a is None else [_r(a[0], 4), _r(a[1], 4)],
                            "leaves": o.get("leaves"), "class_hold": o.get("class_hold"), "candidate_classes": None,
                            "status": status, "reasons": list(rec.get("reasons") or ()), "info": rec.get("info")})
    return out


def _totals(groups, codes):
    tot = {}
    for (code, floor, unit, part), entries in groups.items():
        if code not in codes or not entries:
            continue
        t = tot.setdefault(code, {"pcs": {"settled": 0.0, "held": [0.0, 0.0], "no_figure": 0},
                                  "m2": {"released": 0.0, "bounded": [0.0, 0.0], "unquantified": 0}})
        if part.startswith("SETTLED"):
            t[unit]["settled" if unit == "pcs" else "released"] += sum(e["qty"] for e in entries)
        elif part == "HELD":
            k = "held" if unit == "pcs" else "bounded"
            t[unit][k][0] += sum(e["range"][0] for e in entries)
            t[unit][k][1] += sum(e["range"][1] for e in entries)
        else:
            t[unit]["no_figure" if unit == "pcs" else "unquantified"] += len(entries)
    return {c: {"pcs": {"settled": _r(t["pcs"]["settled"], 4), "held": [_r(x, 4) for x in t["pcs"]["held"]],
                        "no_figure": t["pcs"]["no_figure"]},
                "m2": {"released": _r(t["m2"]["released"], 4), "bounded": [_r(x, 4) for x in t["m2"]["bounded"]],
                       "unquantified": t["m2"]["unquantified"]}} for c, t in sorted(tot.items())}


def _same_totals(got, v):
    tol = A3010.AREA_TOL_M2 * 4
    return (got is not None and abs(got["pcs"]["settled"] - v["pcs"]["settled"]) <= 1e-9
            and all(abs(a - b) <= 1e-9 for a, b in zip(got["pcs"]["held"], v["pcs"]["held"]))
            and got["pcs"]["no_figure"] == v["pcs"]["no_figure"]
            and abs(got["m2"]["released"] - v["m2"]["released"]) <= tol
            and all(abs(a - b) <= tol for a, b in zip(got["m2"]["bounded"], v["m2"]["bounded"]))
            and got["m2"]["unquantified"] == v["m2"]["unquantified"])


def ruling_changes(pc, lines, earlier_changed=()):
    """the DOOR_RULING piece on the V3.0.12 lines. -> (changes, log)"""
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    src, base = pc["source"], pc["base"]
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "source": src["file"], "source_sha256": src["sha256"],
             "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                            for s in pc.get("sources") or ()]}
    codes = set(pc["item_codes"])
    dl = _door_lines(pc, lines)
    if not dl:
        raise InputsError("piece DOOR_RULING: the candidate carries no door line of the opening policy (V3.0.10)")
    by_key, groups = {}, {}
    for ln in dl:
        k = _key(ln)
        if k in by_key:
            raise ValueError(f"{METHOD}: two candidate lines for {k}")
        by_key[k] = ln
        groups[k] = copy.deepcopy(ln["calculation"]["inputs"]["openings"])
    # (3) faithfulness: each candidate door line is the V3.0.10 line of its own table
    for k, ln in by_key.items():
        inp = ln["calculation"]["inputs"]
        bsrc = {"file": inp["source"], "sha256": inp["source_sha256"], "task": base["task"],
                "merge_commit": base["merge_commit"]}
        again, _evs, _h = _regen(pid, rev, docs, bsrc, k, groups[k])
        if A30.line_sha(again) != A30.line_sha(ln):
            raise InputsError(f"door line {ln['line_id']} {k}: not reproduced by the V3.0.10 code from its own table "
                              "(the candidate line is not the V3.0.10 line the ruling extends)")
    log = {"piece": "DOOR_RULING", "state": "RUN", "source": src, "sources": pc.get("sources") or [], "base": base,
           "item_codes": pc["item_codes"], "scope": {"floors": pc["scope"]["floors"]}, "rulings": [], "lines": [],
           "evidence_status": {}, "totals_v3_0_12": _totals(groups, codes)}
    new = {k: list(v) for k, v in groups.items()}
    for r in pc["rulings"]:
        o, oid = r["record"], r["id"]
        where = {}
        for k, ents in groups.items():
            for e in ents:
                if e["id"] == oid:
                    where.setdefault(k, []).append(e)
        settled = [k for k in where if k[3].startswith("SETTLED")]
        if settled:
            raise InputsError(f"ruling {oid}: the candidate already settles it in {settled}: a door is ruled once")
        held_codes = sorted({k[0] for k in where})
        if held_codes != sorted(r["held_in"]):
            raise InputsError(f"ruling {oid}: the candidate holds it in {held_codes}, the ruling says {r['held_in']}")
        if {k[1] for k in where} != {o["floor"]}:
            raise InputsError(f"ruling {oid}: held on floor(s) {sorted({k[1] for k in where})}, the record says "
                              f"{o['floor']}")
        for c in held_codes:
            if sorted(k[2] for k in where if k[0] == c) != ["m2", "pcs"]:
                raise InputsError(f"ruling {oid}: held in {c} not in both units once (the same-openings rule)")
        # the held width range, if the candidate held one: a ruled width outside it needs a why
        w = _width_value(o)
        held_w = [e.get("width") or {} for es in where.values() for e in es]
        rng = next((x.get("range") for x in held_w if x.get("range")), None)
        hval = next((x.get("value") for x in held_w if _num(x.get("value"))), None)
        if rng and w is not None and not (rng[0] - WIDTH_TOL_M <= w <= rng[1] + WIDTH_TOL_M) and \
                not r.get("outside_range_why"):
            raise InputsError(f"ruling {oid}: ruled width {w} outside the held range {rng}: state why")
        if not rng and hval is not None and w is not None and abs(w - hval) > WIDTH_TOL_M and \
                not r.get("outside_range_why"):
            raise InputsError(f"ruling {oid}: ruled width {w} != the held reading {hval}: state why")
        held_h = {(e.get("height") or {}).get("value") for es in where.values() for e in es}
        if held_h != {(o.get("height") or {}).get("value")}:
            raise InputsError(f"ruling {oid}: height {(o.get('height') or {}).get('value')} != the held height "
                              f"{sorted(x for x in held_h if x is not None)} (a ruling of class / width never moves "
                              "the head)")
        held_was = {f"{k[0]} {k[2]}": (es[0]["range"] if es[0]["range"] is not None else "NO_FIGURE")
                    for k, es in where.items()}
        for k in where:
            new[k] = [e for e in new[k] if e["id"] != oid]
        for unit, (part, e) in _entries(o, r["ruled_class"]).items():
            e["info"] = dict(e.get("info") or {}, ruled_by={"task": src["task"], "merge_commit": src["merge_commit"],
                                                            "checker_run": r["verified_by"], "verdict": r["verdict"]})
            nk = (r["ruled_class"], o["floor"], unit, part)
            if any(x["id"] == oid for x in new.setdefault(nk, [])):
                raise InputsError(f"ruling {oid}: already in {nk}")
            new[nk].append(e)
            new[nk].sort(key=lambda x: x["id"])
        log["rulings"].append({"id": oid, "floor": o["floor"], "held_in": held_codes, "held_was": held_was,
                               "ruled_class": r["ruled_class"], "width": o.get("width"), "height": o.get("height"),
                               "area_m2": o["m2"].get("value"), "m2_status": o["m2"].get("evidence_status"),
                               "verified_by": r["verified_by"], "census_width": r["census_width"],
                               "deduction_change": (r.get("downstream") or "none: ruled width = census width (the "
                                                    "masonry / finish deductions already carry it)"),
                               "outside_range_why": r.get("outside_range_why")})
    changes = []
    for k in sorted(set(groups) | set(new)):
        before, after = groups.get(k) or [], new.get(k) or []
        if [e["id"] for e in before] == [e["id"] for e in after] and before == after:
            continue
        old = by_key.get(k)
        rid = sorted({e["id"] for e in after} ^ {e["id"] for e in before})
        if after:
            bsrc = ({"file": old["calculation"]["inputs"]["source"],
                     "sha256": old["calculation"]["inputs"]["source_sha256"]} if old else
                    {"file": src["file"], "sha256": src["sha256"]})
            bsrc.update(task=base["task"], merge_commit=base["merge_commit"])
            ln, evs, held = _regen(pid, rev, docs, bsrc, k, after)
            ln["calculation"]["inputs"]["ruled_openings"] = [
                {"id": e["id"], **e["info"]["ruled_by"]} for e in after if (e.get("info") or {}).get("ruled_by")]
            note = (f"{METHOD}: door ruling ({src['task']}, MERGED {src['merge_commit']}, {src['checker_run']}): "
                    f"opening(s) {', '.join(rid)} {'enter' if len(after) > len(before) else 'leave'} this line")
            A305._note(ln, note)
            if old is not None:
                if ln["line_id"] != old["line_id"]:
                    raise ValueError(f"{METHOD}: the line of {k} changed its id")
                A308._check_replaceable(old, earlier, {"earlier_change": "the V3.0.10 type / floor line (T-232) whose "
                                                                         "opening membership the ruling changes"})
                ch = A305._change("DOOR_RULING", "REPLACE", old, ln, drawing_reference=src["file"], held=held,
                                  downstream=[], verification=verif, evidence_status=evs,
                                  codes=["MEMBERSHIP_CHANGED", "EARLIER_CHANGE"], why=note)
            else:
                if ln["line_id"] in have:
                    raise ValueError(f"{METHOD}: group {k} repeats a candidate line id")
                have.add(ln["line_id"])
                ch = A305._change("DOOR_RULING", "ADD", None, ln, drawing_reference=src["file"], held=held,
                                  downstream=[], verification=verif, evidence_status=evs,
                                  guard_element={"element_id": ln["location"]["element_id"], "part": k[3]},
                                  codes=["NEW_GROUP"])
        else:
            A308._check_replaceable(old, earlier, {"earlier_change": "the V3.0.10 type / floor line (T-232) left with "
                                                                     "no opening by the ruling"})
            why = f"every opening of this line ({', '.join(rid)}) is ruled into a settled line of its class"
            note = (f"{METHOD}: RETIRED - {A302._q(A30._qty(old))} {old['unit']} held: {why} ({src['task']}, MERGED "
                    f"{src['merge_commit']}); figure kept as information, never summed")
            ch = A307._retire(old, why, note, verif, "DOOR_RULING", ["EMPTIED_BY_RULING", "EARLIER_CHANGE"],
                              src["file"])
            ln, evs = ch["after"], "DRAWING-CONFIRMED"
        changes.append(ch)
        log["lines"].append({"key": {"item_code": k[0], "floor": k[1], "unit": k[2], "part": k[3]},
                             "line_id": ln["line_id"], "action": ch["action"],
                             "openings_before": [e["id"] for e in before], "openings_after": [e["id"] for e in after],
                             "before": A30._qty(old) if old is not None else None, "after": A30._qty(ln),
                             "evidence_status": evs})
        log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
    log["totals"] = _totals(new, codes)
    for c, v in pc["declared_totals"].items():
        if not _same_totals(log["totals"].get(c), v):
            raise ValueError(f"{METHOD}: {c} totals {log['totals'].get(c)} != the declared {v}")
    log["declared_totals"] = pc["declared_totals"]
    return changes, log


# ================================================================================================ integrate / write
def changes_for(inputs, l3012, earlier_changed=()):
    """the door rulings, then the guard re-check over the result. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        ch_g, log_g = A307.guard_changes(inputs, l3012, [], set())
        return ch_g, [{"piece": "DOOR_RULING", "state": "NO_PROJECT_INPUT"}, log_g]
    ch, logs = [], []
    for pc in inputs["pieces"]:
        c, lg = ruling_changes(pc, l3012, earlier_changed)
        ch += c
        logs.append(lg)
    rep = {c["before"]["line_id"]: c["after"] for c in ch if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l3012]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, logs + [log_g]


def integrate(l3012, v3013_changes):
    """-> (V3.0.13 lines, identity). Every line outside the V3.0.13 rows is byte-identical to the V3.0.12 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3012}
    rep, adds = {}, []
    for c in v3013_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.12 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.12 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3012] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    same = A3010.check_same_openings(out)
    A3012.check_partition(out)
    by12 = {ln["line_id"]: ln for ln in l3012}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by12[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3012):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.13 rows differ from {EXTENDS}")
    ident = {"v3_0_12_lines": len(l3012), "v3_0_13_lines": len(out), "v3_0_13_rows": len(v3013_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_12": len(outside), "same_openings": same,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b12 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_12")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_12": b12, "after_v3_0_13": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_12", "v3_0_13", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_12": A302._q(r["before_v3_0_12"]), "v3_0_13": A302._q(r["after_v3_0_13"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_12", "vs_released_v2_9", "v2_9",
            "v3_0_12", "v3_0_13")


def diff_rows(l3012, l3013, released_lines=None):
    b12 = {ln["line_id"]: ln for ln in l3012}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3013:
        o = b12.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_12": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_12": A302._q(A30._qty(o)) if o else "", "v3_0_13": A302._q(A30._qty(ln))})
    return out


def door_summary(lines, item_codes=("DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE")):
    """per door item code and unit: settled total, held low / high, no-figure count, opening ids (held never 0)."""
    out = {}
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        if ln["item_code"] not in item_codes or inp.get("policy") != OPENINGS_POLICY or \
                ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        d = out.setdefault(ln["item_code"], {}).setdefault(ln["unit"], {"settled": 0.0, "low": 0.0, "high": 0.0,
                                                                       "no_figure": 0, "settled_ids": [],
                                                                       "held_ids": []})
        ids = list(inp.get("opening_ids") or ())
        if ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None:
            d["settled"] += float(ln["measured_net"])
            d["settled_ids"] += ids
        elif ln["evidence_state"] == "BOUNDED_EXPOSURE":
            d["low"] += float(ln["bounded_range"]["low"])
            d["high"] += float(ln["bounded_range"]["high"])
            d["held_ids"] += ids
        else:
            d["no_figure"] += len(ids)
            d["held_ids"] += ids
    return {c: {u: {k: (_r(v, 4) if isinstance(v, float) else (sorted(v) if isinstance(v, list) else v))
                    for k, v in d.items()} for u, d in sorted(us.items())} for c, us in sorted(out.items())}


def write(out, l3012, v3013_changes, logs, inputs, released_lines=None):
    """the V3_0_13_* files beside the V3_0_12_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3013, ident = integrate(l3012, v3013_changes)
    rows = ledger_rows(v3013_changes, released_lines)
    diff = diff_rows(l3012, l3013, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_12", {}).setdefault(d["vs_v3_0_12"], 0)
        dsum["vs_v3_0_12"][d["vs_v3_0_12"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t12, t13 = A304.code_totals(l3012), A304.code_totals(l3013)
    moved = {k: {"v3_0_12": t12.get(k), "v3_0_13": t13.get(k)} for k in sorted(set(t12) | set(t13))
             if t12.get(k) != t13.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "item_codes", "source", "sources", "base", "scope",
                                                         "declared_totals")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "doors_v3_0_12": door_summary(l3012), "doors_v3_0_13": door_summary(l3013),
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_13_BOQ_LINES.json": BL.dumps(l3013),
             "V3_0_13_BOQ_LINES.csv": A30._lines_csv(l3013),
             "V3_0_13_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_13_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_13_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_13_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "load_inputs", "ruling_changes", "changes_for",
           "integrate", "ledger_rows", "diff_rows", "door_summary", "write", "InputsError"]
