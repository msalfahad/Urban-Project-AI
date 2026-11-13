"""ARCH_TAKEOFF_V3.0.68 (T-672, lane I, MASONRY GATE B ROUND 1 integration package, the first masonry package after the
last concrete one): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.67 (engine.source.arch_v30, arch_v301 ..
arch_v3067), extended with FOUR pieces built from the Checker-merged masonry research (T-670, T-372 research part,
T-675); no concrete, finish or other line moves:

  MAT_RESTATE   the B9 material lines of the candidate's MAS.BLOCK hosts (black units, black laying mortar, AAC glue,
                AAC units) are re-produced by the MERGED V3.0.59 producer (arch_v3059.materials_for, read-only use) on
                the candidate's CURRENT host and lintel lines: first with the rulebook the candidate was built on
                (COMPANY_RULEBOOK 1.0.0), which must give every current material line back BYTE-IDENTICAL (else
                refused), then with the rulebook that carries the owner answer since (1.1.0: UPC-BLACK-BLOCK-001
                confirms the 0.15 m black block on the 40 x 20 module, owner Q-80 2026-11-07); a line whose 1.1.0
                product differs replaces its candidate line (same line id: same producer, same element); each figure
                is asserted equal to the merged T-670 statement (R-T670-1);
  MAT_NOT_APPLICABLE  the AAC glue / AAC unit lines the producer opened on a host whose element id carries no colour,
                where a printed note makes that host BLACK block (R-T675-1: ST p.1 note 2, Checker own read): retired
                as NOT_APPLICABLE_WITH_EVIDENCE with the evidence in the line (never 0, never a quantity); the host's
                black lines stay HELD with their cause;
  PERIMETER_JOINT  one MAS.MORTAR.BLACK.PERIMETER line per black laying-mortar line (R-T372-1 + R-T675-3): the joint
                increment between the last block and concrete over the panel module figure (R-T520-1), carried BESIDE
                the panel line (never inside it, its own producer key); a valued panel line's perimeter is the merged
                envelope [T-372 low, T-372 high + held junction bands + held piece soffits] (PROVISIONAL value when low
                = high, else HELD BOUNDED); a HELD panel line's perimeter is HELD blank with the host's own cause;
  LINTEL_BED    one MAS.MORTAR.BLACK.LINTEL_BEARING line per lintel whose face the material base deducts (R-T372-1 (5),
                R-T675-2): the bed joint between the bearing course and the lintel underside, which the panel does not
                credit; bearing low .. high from the merged jamb ledger (a deficit end bounded by the drawn available
                masonry at 6 dp, F-C-T372-1), m3 = bearing x kappa x t x joint, kappa = unit face / module face; a
                lintel that is itself HELD gives a HELD BOUNDED bed 0 .. printed bearing.

R-T672-1 (every villa): (a) a rule-version change reaches the candidate only by re-running the merged producer on the
candidate's current lines after the old version reproduces every current line byte-identically; (b) a material line
exists only for the material the host's own evidence prints: a printed contrary note retires it NOT_APPLICABLE with
that evidence; (c) a component measured wall by wall (perimeter joints, lintel beds) is its own line under its own
code, bound to the material line it adds to by id, never summed into it; units, m3 and kg are never summed together;
(d) every line here is ASSUMED - OWNER-APPROVED (Q-75 / Q-80 module, Q-78 mix, owner 2026-10-29 10 mm joint), never
VERIFIED; installed only, waste and procurement HELD; (e) a range is reported low with low and high with high: the
correlated lintel scenarios (built bearing at the printed minimum with the block meeting the lintel end, or the
bearing running to the drawn available length with no end band) are stated BESIDE as two scenario figures, never
mixed into one line; (f) nothing outside the six masonry material codes moves; every other line byte-identical.
Files: V3_0_68_BOQ_LINES.json / .csv, V3_0_68_INTEGRATION_LEDGER.json / .csv, V3_0_68_DIFF.csv, V3_0_68_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3067 as A3067

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-runs the merged producer and books Checker-merged ledgers
METHOD = "ARCH_TAKEOFF_V3.0.68"
EXTENDS = A3067.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T672_ARCH_V3_0_68"
INPUTS_SCHEMA = "URBAN_V3068_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3068_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
RULE_ID, RULE_VERSION = "R-T672-1", "T-672"
REC_KEY = "masonry_gate_b_v3068"
P_MAT, P_NA, P_PER, P_BED = "MAT_RESTATE", "MAT_NOT_APPLICABLE", "PERIMETER_JOINT", "LINTEL_BED"
PERIM, BED = "MAS.MORTAR.BLACK.PERIMETER", "MAS.MORTAR.BLACK.LINTEL_BEARING"
MAT_CODES = A3059.CODES
CODES = MAT_CODES + (PERIM, BED)
UNIT = dict(A3059.UNIT, **{PERIM: "m3", BED: "m3"})
FAMILY = dict(A3059.FAMILY, **{PERIM: "B9-04", BED: "B9-04"})
ITEM_TEXT = {PERIM: ("Black-block perimeter joint mortar (block to concrete, increment over the panel)",
                     "مونة فواصل محيط الطابوق الأسود (طابوق إلى خرسانة)"),
             BED: ("Black-block mortar bed under a lintel bearing", "مونة فرشة تحت ارتكاز العتبة")}
NA_CODES = (A3059.GLUE, A3059.U_WHITE)
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
BOUNDED, BLANK = "BOUNDED_EXPOSURE", "BLOCKED_RFI"
OA = "ASSUMED - OWNER-APPROVED"
TOL = 1e-6
TOT_TOL = 5e-6
line_class = A3063.line_class

PIECES = {
    P_MAT: {"module": "engine/source/arch_v3068.py (the merged V3.0.59 producer re-run on the candidate's lines with "
                      "COMPANY_RULEBOOK 1.1.0 after a byte-identical 1.0.0 reproduction)",
            "policy": "MASONRY_GATE_B_V1", "rule_id": "R-T670-1 (R-T672-1 (a))",
            "owner_rules": ["Q-75 / Q-80 (12.5 / m2 on the 40 x 20 module, 0.15 and 0.20 m black block)",
                            "Q-78 (black-block mortar 1:4)", "owner 2026-10-29 (10 mm bed and head joint, provisional)",
                            "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
            "owner_manual_method": "net wall m2 x 12.5 blocks / m2; joint mortar m3 = net m2 x t x (1 - 0.39 x 0.19 / "
                                   "0.40 x 0.20)",
            "drawing_method": "the candidate's MAS.BLOCK contract net (drawn pieces x clear height - openings) minus "
                              "the REQUIRED RC lintel faces (w + 0.80) x D bound to their STR.CONC.LINTEL lines, x the "
                              "same company rates (T-453 r2 / T-506 / T-487 producer, V3.0.59)"},
    P_NA: {"module": "engine/source/arch_v3068.py (AAC material lines retired on a host a printed note makes black)",
           "policy": "MASONRY_GATE_B_V1", "rule_id": "R-T675-1 (R-T672-1 (b))",
           "owner_rules": ["owner 2026-10-20 10:45 (Q-60: the plan / engineering-office note decides black or white)"],
           "owner_manual_method": "the block type the drawing note prints for the wall",
           "drawing_method": "structural general note on the neighbour-side ground beams (black block from the "
                             "foundation level); architectural DXF silent (no hatch, legend or text): no contrary "
                             "source"},
    P_PER: {"module": "engine/source/arch_v3068.py (perimeter joint increment per black mortar line, beside it)",
            "policy": "MASONRY_GATE_B_V1", "rule_id": "R-T372-1 / R-T520-1 / R-T675-3 (R-T672-1 (c))",
            "owner_rules": ["owner 2026-10-29 (10 mm joint, provisional)", "Q-75 / Q-80 module"],
            "owner_manual_method": "not measured in the owner's manual method (mortar by m3 per m2 of wall only)",
            "drawing_method": "per wall: kappa b j x (soffit run + 2 x vertical ends - corner overlaps) + kappa b j x "
                              "block-end range (butt or bonded, no junction detail printed); held junction bands and "
                              "dome-opening piece soffits 0 .. drawn upper bound (T-520 / T-615 / T-372 / T-675)"},
    P_BED: {"module": "engine/source/arch_v3068.py (bed joint under each deducted lintel's bearings)",
            "policy": "MASONRY_GATE_B_V1", "rule_id": "R-T372-1 (5) / R-T675-2 (R-T672-1 (c))",
            "owner_rules": ["ST p.13 lintel schedule (MIN 40 cm bearing each side)", "owner 2026-10-29 (10 mm joint)"],
            "owner_manual_method": "not measured in the owner's manual method",
            "drawing_method": "bearing per end from the jamb ledger (T-516 / T-527 V3): available >= 0.40 EXACT 0.40; a "
                              "deficit at a column 0.40 .. available; a deficit at a masonry end 0.40 .. drawn "
                              "available (no block beyond the stopper), x kappa x t x 0.010"},
}
WAITING = dict(A3067.WAITING)
WAITING.update({
    "T672_HELD_HOSTS": "12 black units / 12 black mortar / 12 perimeter lines stay HELD blank on 12 HELD masonry "
                       "hosts with each host's cause (2F roof datum D-39, BLOCK_WALL_NOT_ESTABLISHED, MAIN_S / ANNEX_S "
                       "below N.G.): the materials follow the host",
    "T672_AAC_UNITS": "white AAC unit lines stay HELD: the project selects no AAC face (Q-60 supplier faces beside only)",
    "T672_MAIN_S_BESIDE": "MAIN_S black pair HELD blank; CONDITIONAL beside in the T-675 ledger (AT_LEAST 142.3625 pcs / "
                          "0.125991 m3 on one 0.15 leaf): not on the line (host height and leaf not printed)",
    "T672_GF_W22": "GF-W22 perimeter 0.004140 .. 0.004144 m3 stays beside its host by name (parent area CONFLICT D-27)",
    "T672_WASTE": "waste / procurement of every B9 material HELD (no owner rule); bags rounded only at the purchasing "
                  "group",
})


# ================================================================================================ inputs
def _need(d, keys, w):
    for k in keys:
        if d.get(k) is None:
            raise InputsError(f"{w}: missing {k}")


def _producer_doc(p, rb):
    return {"schema": A3059.INPUTS_SCHEMA, "rulebook": rb, "sources": p["sources"], "joint": p["joint"],
            "faces": p["faces"], "faces_on_held_hosts": p.get("faces_on_held_hosts") or []}


def load_inputs(doc, project_id=None):
    """URBAN_V3068_INPUTS_V1 (research/agents_t672/t672_inputs.py builds it from the merged ledgers) -> checked doc.
    {"schema", "project_id", "sources": [{task, file, sha256, merge_commit, checker_run}],
     "producer": {faces, joint, sources, rulebook_before, rulebook_after} (the merged V3.0.59 producer inputs),
     "restate": [{line_id, item_code, host, before, after, changed}] (T-670, the expected figures),
     "not_applicable": [{line_id, item_code, host, evidence, arch_check}] (T-675 part a),
     "perimeter": [{mortar_line_id, host_line_id, host, state, t372 {low, high}, t675 {...}?, bands, evidence_label?}],
     "lintel_bed": [{opening_id, lintel_line_id, mortar_line_id, state, low, high, bearing_m?, ends?}],
     "pieces": [...], "factor_m3_per_m": {...}, "beside": {...}}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    for k in ("rates", "blocks_per_m2", "kg_per_m2"):
        if k in doc:
            raise InputsError(f"a typed rate ({k}) is refused: rates come from the company rulebook records")
    srcs = A3063._sources(doc) if hasattr(A3063, "_sources") else None
    if srcs is None:
        srcs = {}
        for s in doc.get("sources") or ():
            _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
            srcs[s["task"]] = s
    for t in ("T-670", "T-372", "T-675"):
        if t not in srcs:
            raise InputsError(f"sources: the merged {t} ledger is named")
    p = doc.get("producer") or {}
    _need(p, ("faces", "joint", "sources", "rulebook_before", "rulebook_after"), "producer")
    try:
        d_old = A3059.load_inputs(_producer_doc(p, p["rulebook_before"]))
        d_new = A3059.load_inputs(_producer_doc(p, p["rulebook_after"]))
    except A3059.InputsError as e:
        raise InputsError(f"producer inputs (V3.0.59 checks): {e}") from e
    if d_old["rulebook"]["version"] == d_new["rulebook"]["version"]:
        raise InputsError("producer: the restatement names two different rulebook versions")
    seen = set()
    for r in doc.get("restate") or ():
        _need(r, ("line_id", "item_code", "after"), "restate")
        if r["item_code"] not in MAT_CODES or r["line_id"] in seen:
            raise InputsError(f"restate {r['line_id']}: not a material code, or named twice")
        seen.add(r["line_id"])
    for r in doc.get("not_applicable") or ():
        _need(r, ("line_id", "item_code", "host", "evidence"), "not_applicable")
        if r["item_code"] not in NA_CODES:
            raise InputsError(f"not_applicable {r['line_id']}: only AAC glue / AAC unit lines are retired here")
    hosts = set()
    for r in doc.get("perimeter") or ():
        _need(r, ("mortar_line_id", "host_line_id", "host", "state", "t372"), "perimeter")
        if r["state"] not in ("VALUE", "RANGE", "HELD") or r["mortar_line_id"] in hosts:
            raise InputsError(f"perimeter {r['mortar_line_id']}: state {r['state']!r} or named twice")
        hosts.add(r["mortar_line_id"])
    ops = set()
    for r in doc.get("lintel_bed") or ():
        _need(r, ("opening_id", "lintel_line_id", "mortar_line_id", "state", "low", "high"), "lintel_bed")
        if r["state"] not in ("EXACT", "RANGE", "HELD") or r["opening_id"] in ops:
            raise InputsError(f"lintel_bed {r['opening_id']}: state {r['state']!r} or named twice")
        ops.add(r["opening_id"])
    return dict(doc, _sources=srcs, _old=d_old, _new=d_new)


# ================================================================================================ helpers
def _rec(srcs, **kw):
    return dict({"policy": "MASONRY_GATE_B_V1", "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _state(ln):
    """a line -> ('VALUE', v) | ('RANGE', [lo, hi]) | ('HELD', None) | ('NA', None) (the T-670 tuple form)."""
    if ln["evidence_state"] in A3063.EXCLUDED:
        return ("NA", None)
    if ln["evidence_state"] == BOUNDED:
        b = ln["bounded_range"]
        return ("RANGE", [_r(b["low"]), _r(b["high"])])
    if ln.get("measured_net") is not None and ln["evidence_state"] != BLANK:
        return ("VALUE", _r(ln["measured_net"]))
    return ("HELD", None)


def _same(a, b):
    if a[0] != b[0]:
        return False
    if a[0] == "VALUE":
        return abs(a[1] - b[1]) <= TOL
    if a[0] == "RANGE":
        return abs(a[1][0] - b[1][0]) <= TOL and abs(a[1][1] - b[1][1]) <= TOL
    return True


def joint_factor(joint, t):
    """m3 of mortar per metre of a block-to-concrete or bed joint: kappa x t x j, kappa = unit face / module face
    (R-T520-1: the module figure already holds 1 - kappa of the joint)."""
    u, m = joint["unit_m"], joint["module_m"]
    j = float(joint.get("joint_mm") or 0) / 1000.0
    if not (0 < j < 0.05):
        raise InputsError(f"joint thickness {joint.get('joint_mm')!r} mm is not a joint")
    return (u[0] * u[1]) / (m[0] * m[1]) * t * j


def _host_t(eid):
    m = A3059.EID.match(eid or "")
    return float(m.group("t")) if m else None


def _new_line(src, *, code, state, net=None, rng=None, eid, what, formula, rec, rfi=None, notes):
    from engine.source import boq_line as BL
    en, ar = ITEM_TEXT[code]
    loc = src.get("location") or {}
    ln = BL.make_line(
        project_id=src["project"]["project_id"], revision_set_sha256=src["project"]["revision_set_sha256"],
        item_code=code, unit=UNIT[code], evidence_state=state, measured_net=net, gross=net, bounded_range=rng,
        element_id=eid, floor=loc.get("floor"), physical_element=what, formula=formula[:1500],
        inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]},
        documents=copy.deepcopy(src["source"]["documents"]), geometry_source=src["source"]["geometry_source"],
        geometry_confidence=src["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="PROJECT_OWNER_FACT", rfi=rfi, notes=notes, item_en=en, item_ar=ar, trade=A3059.TRADE)
    return A3046._fin(ln)


# ================================================================================================ pieces
def restate_materials(doc, prev):
    """MAT_RESTATE -> (changes, log). The 1.0.0 product must equal every current material line byte for byte."""
    S = doc["_sources"]
    srcs = [S["T-670"]]
    by = {ln["line_id"]: ln for ln in prev}
    lintels = A3059._lintels(prev)
    hosts = sorted((ln for ln in prev if ln["item_code"] == A3059.SRC_CODE), key=lambda x: x["line_id"])
    exp = {r["line_id"]: r for r in doc.get("restate") or ()}
    changes, log, seen = [], {"reproduced": 0, "changed": 0, "unchanged": 0}, set()
    for h in hosts:
        old = A3059.materials_for(h, doc["_old"], lintels)
        new = A3059.materials_for(h, doc["_new"], lintels)
        if [x["line_id"] for x in old] != [x["line_id"] for x in new]:
            raise InputsError(f"{h['line_id']}: the material line set changed between rulebook versions")
        for o, n in zip(old, new):
            cur = by.get(o["line_id"])
            if cur is None or A30.line_sha(cur) != A30.line_sha(o):
                raise InputsError(f"{o['line_id']} ({o['item_code']} on {h['line_id']}): the merged producer on "
                                  f"rulebook {doc['_old']['rulebook']['version']} does not reproduce the candidate "
                                  f"line byte-identically (R-T672-1 (a))")
            log["reproduced"] += 1
            seen.add(o["line_id"])
            e = exp.get(o["line_id"])
            if e is None:
                raise InputsError(f"{o['line_id']}: the merged T-670 statement has no row for this line")
            if not _same(_state(cur), tuple(e["before"]) if e["before"][0] != "HELD" else ("HELD", None)):
                raise InputsError(f"{o['line_id']}: T-670 'before' {e['before']} is not the candidate {_state(cur)}")
            want = ("HELD", None) if e["after"][0] == "HELD" else tuple(e["after"])
            if not _same(_state(n), want):
                raise InputsError(f"{o['line_id']}: the 1.1.0 product {_state(n)} is not the T-670 figure {want}")
            if _same(_state(n), _state(cur)):
                # the same figure under both rulebook versions (only the rulebook record in the line differs): the
                # candidate line stays byte-identical (R-T672-1 (f)); the 1.1.0 product is checked, not booked
                log["unchanged"] += 1
                continue
            a = copy.deepcopy(n)
            inp = a["calculation"]["inputs"]
            st = OA
            inp[REC_KEY] = _rec(srcs, piece=P_MAT, action="RESTATE", evidence_status=st,
                                was=dict(zip(("state", "q"), _state(cur))), after=dict(zip(("state", "q"), _state(n))),
                                rulebook_was=doc["_old"]["rulebook"]["version"],
                                rulebook_now=doc["_new"]["rulebook"]["version"],
                                basis="owner Q-80 2026-11-07: the 0.15 m black block is laid on the 40 x 20 module "
                                      "(UPC-BLACK-BLOCK-001 1.1.0); rate and joint ASSUMED - OWNER-APPROVED (company "
                                      "rule, not printed); host area status unchanged beside")
            A305._note(a, f"{METHOD}: restated on COMPANY_RULEBOOK {doc['_new']['rulebook']['version']} (R-T670-1); "
                          f"was {A302._q(A30._qty(cur))}; NOT RELEASED")
            a = A3063._fin(a)
            changes.append(A305._change(P_MAT, "CHANGE", cur, a, step="RESTATE", evidence_status=st,
                                        drawing_reference=S["T-670"]["file"], held=None,
                                        verification={"task": "T-670", "merge_commits": [S["T-670"]["merge_commit"]],
                                                      "checker_run": S["T-670"]["checker_run"]}))
            log["changed"] += 1
    missing = sorted(set(exp) - seen)
    if missing:
        raise InputsError(f"T-670 rows name {len(missing)} line(s) the producer does not make: {missing[:3]}")
    mats = [ln["line_id"] for ln in prev if ln["item_code"] in MAT_CODES]
    if sorted(mats) != sorted(seen):
        raise InputsError("a candidate material line is not the producer's (one producer per material)")
    return changes, log


def retire_not_applicable(doc, cur):
    """MAT_NOT_APPLICABLE -> changes on the lines as they stand after MAT_RESTATE."""
    S = doc["_sources"]
    src = S["T-675"]
    out = []
    for e in doc.get("not_applicable") or ():
        b = cur.get(e["line_id"])
        if b is None or b["item_code"] != e["item_code"]:
            raise InputsError(f"{e['line_id']}: not a {e['item_code']} line of the candidate")
        if (b.get("location") or {}).get("element_id") != f"MATERIAL:{e['host']}":
            raise InputsError(f"{e['line_id']}: host {e['host']} is not the line's host")
        if A3059.EID.match(e["host"]):
            raise InputsError(f"{e['line_id']}: a host whose element id carries its colour is not retired here")
        if _state(b)[0] != "HELD":
            raise InputsError(f"{e['line_id']}: only a HELD blank material line is retired (never a figure)")
        a = copy.deepcopy(b)
        a["evidence_state"], a["measured_net"], a["gross"], a["bounded_range"], a["rfi"] = NA_STATE, None, None, None, None
        a["deductions"], a["additions"] = [], []
        why = (f"NOT APPLICABLE WITH EVIDENCE (R-T675-1): {e['evidence']}; architectural check: "
               f"{e.get('arch_check') or 'none'}; the host is BLACK block: no AAC material exists on it")
        a["calculation"] = dict(a["calculation"], formula=f"{METHOD}: {why}"[:1500])
        inp = a["calculation"]["inputs"] = dict(a["calculation"].get("inputs") or {})
        inp[REC_KEY] = _rec([src], piece=P_NA, action="NOT_APPLICABLE", evidence_status="DRAWING-CONFIRMED",
                            was={"state": "HELD", "q": None}, after={"state": "NA", "q": None},
                            basis=e["evidence"], arch_check=e.get("arch_check"))
        A305._note(a, f"{METHOD}: {why}"[:600])
        a = A3063._fin(a)
        out.append(A305._change(P_NA, "CHANGE", b, a, step="NOT_APPLICABLE", evidence_status="DRAWING-CONFIRMED",
                                drawing_reference=src["file"], held=None,
                                verification={"task": "T-675", "merge_commits": [src["merge_commit"]],
                                              "checker_run": src["checker_run"]}))
    return out


def perimeter_lines(doc, cur):
    """PERIMETER_JOINT -> ADD changes, one per black laying-mortar line (bound by id, beside it)."""
    S = doc["_sources"]
    srcs = [S["T-372"], S["T-675"]]
    out, mortar = [], {ln["line_id"]: ln for ln in cur.values() if ln["item_code"] == A3059.MORTAR}
    named = {e["mortar_line_id"] for e in doc.get("perimeter") or ()}
    if named != set(mortar):
        raise InputsError(f"perimeter: {len(set(mortar) - named)} black mortar line(s) without a perimeter entry, "
                          f"{len(named - set(mortar))} entry(ies) on no mortar line")
    for e in doc["perimeter"]:
        m = mortar[e["mortar_line_id"]]
        h = cur.get(e["host_line_id"])
        eid = (m.get("location") or {}).get("element_id") or ""
        if h is None or eid != f"MATERIAL:{(h.get('location') or {}).get('element_id')}" or \
                (h.get("location") or {}).get("element_id") != e["host"]:
            raise InputsError(f"perimeter {e['mortar_line_id']}: host {e['host_line_id']} is not the mortar line's host")
        ms = _state(m)
        t = e["t372"]
        if e["state"] == "HELD":
            if ms[0] != "HELD" or line_class(h) != "HELD":
                raise InputsError(f"perimeter {e['mortar_line_id']}: HELD on a valued panel / host")
            cause = (t.get("held_cause") or "").strip()
            if not cause:
                raise InputsError(f"perimeter {e['mortar_line_id']}: HELD with no named host cause")
            rec = _rec(srcs, piece=P_PER, action="HELD", evidence_status="HELD", mortar_line_id=m["line_id"],
                       host_line_id=h["line_id"], cause=cause[:600])
            ln = _new_line(m, code=PERIM, state=BLANK, eid=f"{eid}#PERIMETER_JOINT", what=ITEM_TEXT[PERIM][0],
                           formula=f"{METHOD}: HELD blank (never 0): the masonry host {h['line_id']} is HELD: {cause}",
                           rec=rec, rfi={"question": f"perimeter joint waits for the host: {cause}"[:400],
                                         "blocks": [h["line_id"]]},
                           notes=f"beside {A3059.MORTAR} {m['line_id']} (never summed into it); HELD with its host")
            out.append(A305._change(P_PER, "ADD", None, ln, step="HELD", evidence_status="HELD",
                                    held=[{"what": "perimeter joint", "why": cause[:300]}],
                                    verification={"task": "T-372", "merge_commits": [S["T-372"]["merge_commit"]]}))
            continue
        if ms[0] not in ("VALUE", "RANGE"):
            raise InputsError(f"perimeter {e['mortar_line_id']}: a valued perimeter on a blank panel line")
        x = e.get("t675")
        lo, hi = float(t["low"]), float(t["high"])
        bands_hi = pieces_hi = 0.0
        if x is not None:
            if abs(x["low"] - lo) > TOL or abs(x["high_drawn_t372"] - hi) > TOL:
                raise InputsError(f"perimeter {e['mortar_line_id']}: T-675 drawn part is not the T-372 ledger")
            bsum = sum(b["high"] for b in e.get("bands") or () if b.get("verdict") == "HELD bounded")
            if abs(bsum - x["held_bands_high"]) > TOL:
                raise InputsError(f"perimeter {e['mortar_line_id']}: bands sum {bsum} is not {x['held_bands_high']}")
            bands_hi, pieces_hi = float(x["held_bands_high"]), float(x["held_pieces_high"])
            env = [lo, _r(hi + bands_hi + pieces_hi)]
            if abs(env[0] - x["envelope"][0]) > TOL or abs(env[1] - x["envelope"][1]) > TOL:
                raise InputsError(f"perimeter {e['mortar_line_id']}: envelope {env} is not T-675 {x['envelope']}")
        else:
            env = [lo, hi]
        lab = e.get("evidence_label") or {}
        basis = lab.get("basis") or ("area per host status; thickness DRAWING-CONFIRMED (host id); module OWNER "
                                     "CONFIRMED Q-75 / Q-80; 10 mm joint ASSUMED - OWNER-APPROVED (owner 2026-10-29): "
                                     "weakest = ASSUMED - OWNER-APPROVED, PROVISIONAL, never VERIFIED")
        comp = {"drawn_t372": [_r(lo), _r(hi)], "held_bands_high": _r(bands_hi), "held_pieces_high": _r(pieces_hi),
                "walls": (x or {}).get("walls") or t.get("walls"),
                "bands": [b for b in e.get("bands") or ()]}
        rec = _rec(srcs, piece=P_PER, action="VALUE" if env[0] == env[1] else "BOUND", evidence_status=OA,
                   mortar_line_id=m["line_id"], host_line_id=h["line_id"], components=comp, basis=basis[:600],
                   beside=(doc.get("beside") or {}).get("gf_w22") if "GF-WALLS:walls t=0.15#BLOCKWORK:DRAWING" in
                   e["host"] else None)
        f = (f"{METHOD}: perimeter joint increment over the panel (R-T520-1) = drawn {_fmt(lo)} .. {_fmt(hi)} m3 "
             f"(T-372, walls {', '.join(comp['walls'] or [])})"
             + (f" + held junction bands 0 .. {_fmt(bands_hi)} + held piece soffits 0 .. {_fmt(pieces_hi)}"
                if (bands_hi or pieces_hi) else "")
             + f" = {_fmt(env[0])}" + ("" if env[0] == env[1] else f" .. {_fmt(env[1])}")
             + " m3 installed; 10 mm joint PROVISIONAL; waste HELD")
        if abs(env[1] - env[0]) <= TOL:
            ln = _new_line(m, code=PERIM, state="PROVISIONAL", net=_r(env[0]), eid=f"{eid}#PERIMETER_JOINT",
                           what=ITEM_TEXT[PERIM][0], formula=f, rec=rec,
                           notes=f"beside {A3059.MORTAR} {m['line_id']} (never summed into it); {OA}")
        else:
            why = "block-end butt / bond and named held bands / pieces (no junction detail, dome top not drawn)"
            ln = _new_line(m, code=PERIM, state=BOUNDED, rng={"low": _r(env[0]), "high": _r(env[1]),
                                                               "basis": why[:200]},
                           eid=f"{eid}#PERIMETER_JOINT", what=ITEM_TEXT[PERIM][0], formula=f, rec=rec,
                           rfi={"question": "the junction detail (butt or bonded block ends) and the drawn top of the "
                                            "dome-opening pieces", "blocks": [m["line_id"]]},
                           notes=f"beside {A3059.MORTAR} {m['line_id']} (never summed into it); {OA}; a range, never "
                                 f"a picked point")
        out.append(A305._change(P_PER, "ADD", None, ln, step=rec["action"], evidence_status=OA,
                                held=None if env[0] == env[1] else [{"what": "perimeter range", "range": env}],
                                verification={"task": "T-372 + T-675", "merge_commits": [s["merge_commit"]
                                                                                        for s in srcs]}))
    return out


def bed_lines(doc, cur):
    """LINTEL_BED -> ADD changes, one per lintel face the material base names (REQUIRED or HELD)."""
    S = doc["_sources"]
    srcs = [S["T-372"], S["T-675"]]
    joint = doc["producer"]["joint"]
    lint = A3059._lintels(list(cur.values()))
    req = {}
    for lid, f in doc["producer"]["faces"].items():
        h = cur.get(lid)
        t = _host_t((h.get("location") or {}).get("element_id")) if h else None
        if h is None or t is None:
            raise InputsError(f"lintel faces on {lid}: not a masonry host of the candidate")
        if A3059.EID.match(h["location"]["element_id"]).group("mat") != "BLACK":
            continue                                            # AAC glue thin-bed: no bed joint line here
        for x in (f.get("required") or []) + (f.get("held") or []):
            req[x["opening_id"]] = (lid, t, "required" if x in (f.get("required") or []) else "held")
    named = {e["opening_id"] for e in doc.get("lintel_bed") or ()}
    if named != set(req):
        raise InputsError(f"lintel bed: entries {sorted(named ^ set(req))[:4]} do not match the black hosts' faces")
    out = []
    for e in doc["lintel_bed"]:
        hid, t, kind = req[e["opening_id"]]
        ll = lint.get(e["opening_id"])
        if ll is None or ll["line_id"] != e["lintel_line_id"]:
            raise InputsError(f"lintel bed {e['opening_id']}: not bound to its STR.CONC.LINTEL line")
        m = cur.get(e["mortar_line_id"])
        if m is None or m["item_code"] != A3059.MORTAR or \
                (m.get("location") or {}).get("element_id") != f"MATERIAL:{cur[hid]['location']['element_id']}":
            raise InputsError(f"lintel bed {e['opening_id']}: mortar line is not the black mortar of host {hid}")
        f = joint_factor(joint, t)
        valued = ll["evidence_state"] in A3059.VALUED
        if e["state"] == "HELD":
            if valued or kind != "held":
                raise InputsError(f"lintel bed {e['opening_id']}: HELD bed on a valued / REQUIRED lintel")
            lo, hi = 0.0, _r(2 * 0.40 * f)
            bear = [0.0, 0.80]
        else:
            if not valued or kind != "required":
                raise InputsError(f"lintel bed {e['opening_id']}: a measured bed under a blank / held lintel")
            bear = [float(e["bearing_m"][0]), float(e["bearing_m"][1])]
            lo, hi = _r(bear[0] * f), _r(bear[1] * f)
            ends = e.get("ends") or []
            if ends and (abs(sum(x["low"] for x in ends) - bear[0]) > TOL or
                         abs(sum(x["high"] for x in ends) - bear[1]) > TOL):
                raise InputsError(f"lintel bed {e['opening_id']}: ends do not sum to the bearing {bear}")
            if (e["state"] == "EXACT") != (abs(bear[1] - bear[0]) <= TOL):
                raise InputsError(f"lintel bed {e['opening_id']}: state {e['state']} with bearing {bear}")
        if abs(lo - e["low"]) > TOL or abs(hi - e["high"]) > TOL:
            raise InputsError(f"lintel bed {e['opening_id']}: recomputed {lo} .. {hi} is not the ledger "
                              f"{e['low']} .. {e['high']}")
        rec = _rec(srcs, piece=P_BED, action=e["state"], evidence_status=OA if e["state"] != "HELD" else "HELD",
                   opening_id=e["opening_id"], lintel_line_id=ll["line_id"], mortar_line_id=m["line_id"],
                   host_line_id=hid, bearing_m=[_r(bear[0]), _r(bear[1])], factor_m3_per_m=_r(f, 9),
                   ends=e.get("ends"), was=e.get("was"), cause=e.get("cause"))
        eid = f"MATERIAL:LINTEL_BEARING:{e['opening_id']}"
        form = (f"{METHOD}: lintel {e['opening_id']} bed joint = bearing {_fmt(bear[0])}"
                + ("" if bear[0] == bear[1] else f" .. {_fmt(bear[1])}")
                + f" m x {_fmt(_r(f, 9))} m3/m (kappa x t {t} x 0.010) = {_fmt(lo)}"
                + ("" if lo == hi else f" .. {_fmt(hi)}") + " m3 installed; not credited by the panel (face deducted)")
        if e["state"] == "EXACT":
            ln = _new_line(m, code=BED, state="PROVISIONAL", net=lo, eid=eid, what=ITEM_TEXT[BED][0], formula=form,
                           rec=rec, notes=f"beside {A3059.MORTAR} {m['line_id']} and {ll['line_id']}; {OA}")
        else:
            why = (e.get("cause") or "the built bearing at a deficit end is not drawn (designer)")[:200]
            ln = _new_line(m, code=BED, state=BOUNDED, rng={"low": lo, "high": hi, "basis": why}, eid=eid,
                           what=ITEM_TEXT[BED][0], formula=form + (f"; {e.get('cause')}" if e.get("cause") else ""),
                           rec=rec, rfi={"question": f"the built bearing of lintel {e['opening_id']} at its deficit "
                                                     f"end(s)" if e["state"] == "RANGE" else
                                                     f"whether lintel {e['opening_id']} is built (dome piece)",
                                         "blocks": [ll["line_id"]]},
                           notes=f"beside {A3059.MORTAR} {m['line_id']} and {ll['line_id']}; a range, never 0")
        out.append(A305._change(P_BED, "ADD", None, ln, step=e["state"], evidence_status=rec["evidence_status"],
                                held=None if e["state"] == "EXACT" else [{"what": "bed range", "range": [lo, hi]}],
                                verification={"task": "T-372 + T-675", "merge_commits": [s["merge_commit"]
                                                                                        for s in srcs]}))
    return out


def scenarios(doc, changes):
    """R-T672-1 (e): the correlated lintel scenarios BESIDE (m3): A = every deficit end built at the printed 0.40 m
    bearing with the block meeting the lintel end in its band (bed low + those bands high); B = the bearing runs to the
    drawn available length, no end band (bed high + 0). Never mixed into one line."""
    bed = [c["after"] for c in changes if c["piece"] == P_BED and c["step"] == "RANGE"]
    lo = sum(ln["bounded_range"]["low"] for ln in bed)
    hi = sum(ln["bounded_range"]["high"] for ln in bed)
    ops = {ln["calculation"]["inputs"][REC_KEY]["opening_id"] for ln in bed}
    bands = 0.0
    for e in doc.get("perimeter") or ():
        for b in e.get("bands") or ():
            if b.get("verdict") == "HELD bounded" and "FLAGGED_DEFICIT" in (b.get("cause") or "") and \
                    any(o in (b.get("end_ids") or "") + (b.get("cause") or "") for o in ops):
                bands += b["high"]
    return {"deficit_lintels": sorted(ops), "A_min_bearing_with_end_bands_m3": _r(lo + bands),
            "B_available_bearing_no_end_bands_m3": _r(hi), "bed_low_m3": _r(lo), "end_bands_high_m3": _r(bands)}


def changes_for(doc, prev):
    """-> (changes, log): MAT_RESTATE, then MAT_NOT_APPLICABLE, PERIMETER_JOINT and LINTEL_BED on the restated lines."""
    if not doc:
        return [], {"piece": "T672", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.68 records (applied once)")
    if any(ln["item_code"] in (PERIM, BED) for ln in prev):
        raise InputsError("the candidate already carries perimeter / lintel bed lines (one producer)")
    mat, log = restate_materials(doc, prev)
    cur = {ln["line_id"]: ln for ln in prev}
    for c in mat:
        cur[c["after"]["line_id"]] = c["after"]
    na = retire_not_applicable(doc, cur)
    if {c["after"]["line_id"] for c in na} & {c["after"]["line_id"] for c in mat}:
        raise InputsError("a line is both restated and retired")
    for c in na:
        cur[c["after"]["line_id"]] = c["after"]
    per = perimeter_lines(doc, cur)
    bed = bed_lines(doc, cur)
    changes = mat + na + per + bed
    log = {"piece": "T672", "state": "RUN", "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")}
                                                        for s in doc["sources"]],
           "mat": log, "not_applicable": len(na), "perimeter": len(per), "lintel_bed": len(bed),
           "scenarios": scenarios(doc, changes), "rulebook": [doc["_old"]["rulebook"]["version"],
                                                              doc["_new"]["rulebook"]["version"]]}
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    """the code totals the changes must give, from the base totals and the changes alone (a NOT_APPLICABLE line
    leaves its code's totals: A304.code_totals skips it)."""
    zero = {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 0}
    want = {}
    for c in changes:
        k = f"{c['after']['item_code']}|{c['after']['unit']}"
        z = want.setdefault(k, dict(t0.get(k) or zero))
        for ln, s in ([(c["before"], -1)] if c["before"] is not None else []) + [(c["after"], 1)]:
            if ln["evidence_state"] in A3063.EXCLUDED:
                continue
            z["lines"] += s
            q = A30._qty(ln)
            if q["value"] is not None and ln["evidence_state"] != BLANK:
                z["released"] += s * q["value"]
            elif q["low"] is not None:
                z["held_low"] += s * q["low"]
                z["held_high"] += s * q["high"]
                z["bounded_lines"] += s
            else:
                z["blocked_lines"] += s
    return want


def check_totals(t0, t1, changes):
    """only the six masonry material codes move, each exactly by the changes (R-T672-1 (f))."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if k.split("|")[0] not in CODES)
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the masonry material codes: {bad}")
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
        out[k] = {"base": t0.get(k), "v3_0_68": a, "view": A3058.total_view(a)}
    return out


def check_masonry(lines):
    """on finished lines: every V3.0.68 record is in its state; a perimeter / bed line binds a black mortar line of
    the same candidate and is never valued on a blank panel; one perimeter line per mortar line, one bed per lintel;
    no material line valued on a held host (the V3.0.59 producer check, re-run). -> summary"""
    by = {ln["line_id"]: ln for ln in lines}
    per, bed, out = set(), set(), {"restated": 0, "not_applicable": 0, "perimeter": 0, "lintel_bed": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] in (PERIM, BED):
                raise ValueError(f"{METHOD}: {ln['line_id']} a {ln['item_code']} line with no V3.0.68 record")
            continue
        p = rec["piece"]
        if p == P_MAT:
            out["restated"] += 1
            if ln["item_code"] not in MAT_CODES:
                raise ValueError(f"{METHOD}: {ln['line_id']} restated outside the material codes")
        elif p == P_NA:
            if ln["evidence_state"] != NA_STATE or ln["item_code"] not in NA_CODES or not ln.get("notes"):
                raise ValueError(f"{METHOD}: {ln['line_id']} not applicable without its state / evidence")
            out["not_applicable"] += 1
        elif p in (P_PER, P_BED):
            m = by.get(rec["mortar_line_id"])
            if m is None or m["item_code"] != A3059.MORTAR:
                raise ValueError(f"{METHOD}: {ln['line_id']} binds no black mortar line")
            q = _state(ln)
            if p == P_PER:
                if rec["mortar_line_id"] in per:
                    raise ValueError(f"{METHOD}: two perimeter lines on {rec['mortar_line_id']}")
                per.add(rec["mortar_line_id"])
                if q[0] != "HELD" and _state(m)[0] == "HELD":
                    raise ValueError(f"{METHOD}: {ln['line_id']} a valued perimeter on a blank panel")
                if q[0] == "HELD" and not (ln.get("rfi") or {}).get("question"):
                    raise ValueError(f"{METHOD}: {ln['line_id']} held with no question")
                out["perimeter"] += 1
            else:
                if rec["opening_id"] in bed:
                    raise ValueError(f"{METHOD}: two bed lines for lintel {rec['opening_id']}")
                bed.add(rec["opening_id"])
                if by.get(rec["lintel_line_id"]) is None:
                    raise ValueError(f"{METHOD}: {ln['line_id']} binds no lintel line")
                out["lintel_bed"] += 1
            if rec["evidence_status"] == "VERIFIED":
                raise ValueError(f"{METHOD}: {ln['line_id']} a masonry material line is never VERIFIED here")
    mats = [ln for ln in lines if ln["item_code"] in MAT_CODES]
    out["v3_0_59_materials"] = A3059.check_materials([ln for ln in lines if ln["item_code"] in MAT_CODES + (
        A3059.SRC_CODE,) and ln["evidence_state"] != NA_STATE])
    out["material_lines"] = len(mats)
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.68 lines, identity). Changed lines replace their candidate line in place, added lines follow the base;
    every other candidate line byte-identical (asserted); the V3.0.67 concrete / lintel checks re-run (nothing of
    theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if a["item_code"] not in CODES:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["item_code"] not in (PERIM, BED) or a["line_id"] in sid:
                raise ValueError(f"{METHOD}: only perimeter / bed lines are added, never over a candidate id")
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
    ident = {"base_lines": len(prev), "v3_0_68_lines": len(out), "v3_0_68_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry": check_masonry(out),
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
                     "line_id": a["line_id"], "item_code": a["item_code"], "family": FAMILY[a["item_code"]],
                     "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": a["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_68": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "record": {k: v for k, v in rec.items() if k not in ("ledger_sha256",)},
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "family", "floor", "element_id", "unit",
              "v2_9", "base", "v3_0_68", "class", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_68")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "family": r["family"],
                       "floor": r.get("floor") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_68": q(r.get("after_v3_0_68")), "class": " -> ".join(str(x) for x in r["class"]),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_58"}, v3_0_68=d["v3_0_58"])
            for d in A3058.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_68_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, scenarios=log.get("scenarios"))
    t1 = A304.code_totals(new)
    moved = check_totals(A304.code_totals(prev), t1, changes)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_68_BOQ_LINES.json": BL.dumps(new),
             "V3_0_68_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_68_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_68_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_68_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_68_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": list(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "PERIM", "BED",
           "load_inputs", "changes_for", "joint_factor", "expected_totals", "check_totals", "check_masonry", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
