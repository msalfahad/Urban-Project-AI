"""ARCH_TAKEOFF_V3.0.57 (T-498, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.56
(engine.source.arch_v30, arch_v301 .. arch_v3055, arch_v3056), with ONE new piece, the BLOCKWORK MATERIALS of the
candidate's own MAS.BLOCK lines, as material lines BESIDE them (never inside them):

  BLOCK_MATERIALS  for every MAS.BLOCK line of the base candidate (B9-01 contract area, unchanged):
      black block units   MAS.UNITS.BLACK  pcs  theoretical count = material base x 12.5 / m2 (UPC-BLACK-BLOCK-001, owner
                          Q-75 / 2026-11-02: 40 x 20 installed module, confirmed for 0.20 m only); another thickness:
                          HELD blank (module not stated), the rate is not borrowed;
      black-block mortar  MAS.MORTAR.BLACK m3  installed joint mortar = material base x the joint volume per m2 of the
                          module (T-367 geometry 0.39 x 0.19 unit, 10 mm joints, owner-provisional: PROVISIONAL even on
                          a VERIFIED area), cement bags / loose sand by UPC-BLACK-MORTAR-001 (Q-78 1:4) recorded BESIDE
                          (the cross-trade cement / sand total is not booked here); unconfirmed module: HELD blank,
                          the T-367 figure beside;
      white AAC glue      MAS.GLUE.AAC kg  material base x 3.5 (0.15 m) / 4.5 (0.20 m) kg/m2 (UPC-AAC-GLUE-001, owner
                          2026-11-02); 25 kg bags are rounded once per purchasing group by the materials census, never
                          per line;
      white AAC units     MAS.UNITS.WHITE pcs  HELD blank: the project selects no AAC face (62.5 x 25 / 60 x 20 beside).

R-T498-1 (every villa; integrates R-T453-1 .. 5 and R-T506-1 .. 3 as merged): (1) the material base of a released line =
its contract net minus every REQUIRED lintel face (w + 2 x bearing) x D named in the inputs, each bound to a valued
STR.CONC.LINTEL line of the same candidate (the lintel is concrete, carried once, in B9-02); a HELD / FLAGGED lintel
face is a named range 0 .. face bound to a blank lintel line, the material becomes BOUNDED_EXPOSURE (never deducted
silently, never 0); an unbounded face holds the material; (2) one producer per (line, material): this version is the
PRODUCER of block units, laying mortar and glue (T-453 r2 basis, T-506 verdict); T-367 is a BESIDE figure only;
(3) a HELD / blocked masonry line gives blank material lines by name (colour known: its materials; colour not split:
every material), never 0; (4) every figure is recomputed from the line and the company rulebook and asserted equal
to the expected figure of the inputs (the merged ledgers' machinery on this candidate); (5) a lintel face larger than
its line, a face on a held host, a millimetre width, a typed rate, a second producer are refused.

Nothing else moves: every V3.0.56 line is byte-identical (asserted: this version only ADDS lines); totals move only in
the four material codes (asserted). Files: V3_0_57_BOQ_LINES.json / .csv, V3_0_57_INTEGRATION_LEDGER.json / .csv,
V3_0_57_DIFF.csv, V3_0_57_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3056 as A3056

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged ledgers; rates arrive as rulebook records in the
#                                          inputs (company_rulebook_v1 is an UNWIRED_PRODUCER: never imported here)
METHOD = "ARCH_TAKEOFF_V3.0.57"
EXTENDS = A3056.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T498_ARCH_V3_0_57"
INPUTS_SCHEMA = "URBAN_V3057_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3057_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
RULE_ID = "R-T498-1"
RULE_VERSION = "1.0.0"
REC_KEY = "block_materials_v3057"
P_MAT = "BLOCK_MATERIALS"
SRC_CODE = "MAS.BLOCK"
LINTEL_CODE = "STR.CONC.LINTEL"
U_BLACK, U_WHITE, MORTAR, GLUE = "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC"
CODES = (U_BLACK, U_WHITE, MORTAR, GLUE)
UNIT = {U_BLACK: "pcs", U_WHITE: "pcs", MORTAR: "m3", GLUE: "kg"}
FAMILY = {U_BLACK: "B9-01", U_WHITE: "B9-01", MORTAR: "B9-04", GLUE: "B9-04"}
ITEM_TEXT = {U_BLACK: ("Black block units (theoretical count)", "طابوق أسود (عدد نظري)"),
             U_WHITE: ("White AAC block units (theoretical count)", "طابوق أبيض (عدد نظري)"),
             MORTAR: ("Black block laying mortar 1:4 (installed)", "مونة بناء الطابوق الأسود 1:4"),
             GLUE: ("White AAC block glue", "غراء الطابوق الأبيض")}
BY_COLOUR = {"BLACK": (U_BLACK, MORTAR), "WHITE": (GLUE, U_WHITE), None: (U_BLACK, MORTAR, GLUE, U_WHITE)}
TRADE = "MASONRY"
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
R_BLOCK, R_GLUE, R_MORTAR = "UPC-BLACK-BLOCK-001", "UPC-AAC-GLUE-001", "UPC-BLACK-MORTAR-001"
RULEBOOK_METHOD = "COMPANY_RULEBOOK_V1"
OK = "OK"
TOL = 1e-6                               # a recomputed figure against the expected figure (6 decimals)
FACE_TOL = 0.0005                        # m2: the candidate prints 4 decimals
MM_GUARD = 10.0                          # a face / width above it is millimetres or a unit error (refused)
EID = re.compile(r"^(?P<floor>\w+)-WALLS:walls t=(?P<t>[0-9.]+)(?:#BLOCKWORK:(?P<basis>[A-Z_]+?)_(?P<mat>BLACK|WHITE))?$")
PIECES = {P_MAT: {
    "policy": "R-T498-1: blockwork materials beside the MAS.BLOCK lines (material base = contract net - REQUIRED lintel "
              "faces; HELD lintel faces a named range; held masonry -> blank materials by name)",
    "owner_manual_method": "blocks = net wall m2 x 12.5 (40 x 20, 0.20 m); glue = net m2 x 3.5 / 4.5 kg; mortar 1:4 "
                           "(8 bags + 1.1 m3 sand per m3); waste separate",
    "drawing_method": "the candidate's MAS.BLOCK nets (drawn pieces x clear height - openings) minus the RC lintel faces "
                      "the printed lintel schedule casts inside the panel (T-453 r2 / T-487 lines), x the rulebook rates",
}}
WAITING = dict(A3056.WAITING)
WAITING.update({
    "T498_BLACK_015": "the 0.15 m black block face / module is not stated (owner 2026-11-02 data item): its units and "
                      "joint mortar stay HELD blank (T-367 figure beside)",
    "T498_WHITE_FACE": "the AAC block face is not selected by the project: white unit counts stay HELD blank",
    "T498_WASTE": "no sourced breakage / waste value: procurement counts and bags are not booked (theoretical only)",
})


class InputsError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _num(x, where, hi=MM_GUARD):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise InputsError(f"{where}: {x!r} is not a non-negative number")
    if x > hi:
        raise InputsError(f"{where}: {x} is above {hi} (millimetres or a unit error: refused)")
    return float(x)


# ================================================================================================ inputs
def load_inputs(doc, project_id=None):
    """URBAN_V3057_INPUTS_V1 -> checked dict. Typed rates are refused: every rate comes from the company rulebook."""
    if not isinstance(doc, dict) or doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"inputs schema is not {INPUTS_SCHEMA}")
    if project_id is not None and doc.get("project") not in (None, project_id):
        raise InputsError("inputs name another project")
    for k in ("rates", "blocks_per_m2", "kg_per_m2"):
        if k in doc:
            raise InputsError(f"a typed rate ({k}) is refused: rates come from {RULEBOOK_METHOD} records")
    rb = load_rulebook(doc.get("rulebook"))
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("no source ledger named")
    for s in srcs:
        for k in ("task", "file", "sha256", "merge_commit", "checker_run"):
            if not s.get(k):
                raise InputsError(f"source {s.get('task')}: missing {k}")
    j = doc.get("joint") or {}
    mod, unit = j.get("module_m"), j.get("unit_m")
    if not (isinstance(mod, list) and isinstance(unit, list) and len(mod) == 2 and len(unit) == 2):
        raise InputsError("joint: module_m and unit_m are [length, height] in metres")
    for i in (0, 1):
        _num(mod[i], "joint module", 1.0)
        _num(unit[i], "joint unit", 1.0)
        if not unit[i] < mod[i]:
            raise InputsError("joint: a unit is smaller than its module")
    if not j.get("status") or not j.get("source"):
        raise InputsError("joint: status and source are stated")
    faces = {}
    for lid, f in sorted((doc.get("faces") or {}).items()):
        req, held = [], []
        for x in f.get("required") or ():
            if not x.get("opening_id"):
                raise InputsError(f"{lid}: a lintel face without an opening id")
            req.append({"opening_id": x["opening_id"], "face_m2": _num(x.get("face_m2"), f"{lid} {x['opening_id']} face")})
        for x in f.get("held") or ():
            if not x.get("opening_id"):
                raise InputsError(f"{lid}: a held lintel face without an opening id")
            fm = x.get("face_max_m2")
            held.append({"opening_id": x["opening_id"], "face_max_m2": None if fm is None else
                         _num(fm, f"{lid} {x['opening_id']} held face"), "why": str(x.get("why") or "")[:300]})
        ids = [x["opening_id"] for x in req + held]
        if len(set(ids)) != len(ids):
            raise InputsError(f"{lid}: an opening's face is named twice")
        faces[lid] = {"required": sorted(req, key=lambda x: x["opening_id"]),
                      "held": sorted(held, key=lambda x: x["opening_id"])}
    seen = {}
    for lid, f in faces.items():
        for x in f["required"] + f["held"]:
            if x["opening_id"] in seen:
                raise InputsError(f"lintel {x['opening_id']} deducted from two lines ({seen[x['opening_id']]}, {lid})")
            seen[x["opening_id"]] = lid
    return {"project": doc.get("project"), "sources": srcs, "joint": j, "faces": faces, "rulebook": rb,
            "held_hosts": doc.get("faces_on_held_hosts") or [], "expect": doc.get("expect") or {},
            "beside": doc.get("beside") or {}}


def load_rulebook(rb):
    """the owner rulebook records this version reads, carried in the inputs with their provenance (method, version,
    digest): each OWNER_CONFIRMED with its params; a missing record or param, or another status, is refused."""
    if not isinstance(rb, dict) or rb.get("method") != RULEBOOK_METHOD or not rb.get("version") or not rb.get("digest"):
        raise InputsError(f"rulebook: method {RULEBOOK_METHOD}, version and digest are stated")
    recs = rb.get("records") or {}
    need = {R_BLOCK: ("blocks_per_m2_40x20_module", "confirmed_modules_m"),
            R_GLUE: ("kg_per_m2_by_thickness_m", "bag_kg"), R_MORTAR: ("cement_bags_per_m3", "loose_sand_m3_per_m3")}
    out = {}
    for rid, keys in need.items():
        r = recs.get(rid)
        if not r or r.get("status") != "OWNER_CONFIRMED":
            raise InputsError(f"rulebook: {rid} is not an OWNER_CONFIRMED record")
        p = {}
        for k in keys:
            v = (r.get("params") or {}).get(k)
            if v is None:
                raise InputsError(f"rulebook: {rid} has no {k}")
            p[k] = v
        out[rid] = p
    _num(out[R_BLOCK]["blocks_per_m2_40x20_module"], "blocks per m2", 100.0)
    for k, v in out[R_GLUE]["kg_per_m2_by_thickness_m"].items():
        _num(v, f"glue kg/m2 {k}", 50.0)
    _num(out[R_MORTAR]["cement_bags_per_m3"], "cement bags per m3", 50.0)
    _num(out[R_MORTAR]["loose_sand_m3_per_m3"], "sand per m3", 5.0)
    return {"method": rb["method"], "version": rb["version"], "digest": rb["digest"], "p": out}


def black_rate(rb, t):
    """UPC-BLACK-BLOCK-001: 12.5 / m2 only for a thickness whose installed module is confirmed 40 x 20."""
    p = rb["p"][R_BLOCK]
    key = f"{t:.2f}"
    mod = p["confirmed_modules_m"].get(key)
    if mod is None:
        return {"status": "HELD", "why": f"the installed module of the {key} m black block is not stated (block "
                                          f"schedule, project evidence or supplier data): HELD, the 12.5 / m2 rate is "
                                          f"not borrowed"}
    if abs(mod[0] - 0.40) > 1e-9 or abs(mod[1] - 0.20) > 1e-9:
        return {"status": "HELD", "why": "the 12.5 / m2 company rate applies only to a confirmed 40 x 20 module"}
    return {"status": OK, "blocks_per_m2": p["blocks_per_m2_40x20_module"], "module_m": list(mod),
            "module_basis": f"{R_BLOCK} confirmed_modules_m[{key}]"}


def glue_rate(rb, t):
    k = rb["p"][R_GLUE]["kg_per_m2_by_thickness_m"].get(f"{t:.2f}")
    if k is None:
        return {"status": "HELD", "why": f"no AAC glue rate for {t:.2f} m in {R_GLUE}: HELD"}
    return {"status": OK, "kg_per_m2": k}


def joint_m3_per_m2(j, t):
    """installed joint volume per m2 of wall face: t x (1 - unit face / module face) (T-367 geometry)."""
    return t * (1.0 - (j["unit_m"][0] * j["unit_m"][1]) / (j["module_m"][0] * j["module_m"][1]))


# ================================================================================================ lines
def _rec(d, **kw):
    s = d["sources"]
    return dict({"piece": P_MAT, "policy": PIECES[P_MAT]["policy"], "tasks": [x["task"] for x in s],
                 "ledgers": [x["file"] for x in s], "ledger_sha256": [x["sha256"] for x in s],
                 "merge_commits": [x["merge_commit"] for x in s], "checker_runs": [x["checker_run"] for x in s],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION,
                 "rulebook": f"{d['rulebook']['method']} {d['rulebook']['version']}",
                 "rulebook_digest": d["rulebook"]["digest"], "release_status": "NOT RELEASED", "producer": True}, **kw)


def _new_line(src, *, code, state, net, rng=None, what, formula, rec, rfi=None, notes):
    from engine.source import boq_line as BL
    en, ar = ITEM_TEXT[code]
    loc = src.get("location") or {}
    ln = BL.make_line(
        project_id=src["project"]["project_id"], revision_set_sha256=src["project"]["revision_set_sha256"],
        item_code=code, unit=UNIT[code], evidence_state=state, measured_net=net, gross=net,
        bounded_range=rng, element_id=f"MATERIAL:{loc.get('element_id')}", floor=loc.get("floor"),
        physical_element=what, formula=formula[:1500], inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]},
        documents=copy.deepcopy(src["source"]["documents"]), geometry_source=src["source"]["geometry_source"],
        geometry_confidence=src["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="PROJECT_OWNER_FACT", rfi=rfi, notes=notes, item_en=en, item_ar=ar, trade=TRADE)
    return A3046._fin(ln)


def material_ids(src):
    """the material line ids a MAS.BLOCK line can produce (content keys, computed before the lines)."""
    from engine.source import boq_line as BL
    pid = src["project"]["project_id"]
    eid = f"MATERIAL:{(src.get('location') or {}).get('element_id')}"
    return {c: BL.line_id(pid, c, eid, RULE_ID, RULE_VERSION, UNIT[c]) for c in CODES}


def _lintels(prev):
    out = {}
    for ln in prev:
        if ln["item_code"] != LINTEL_CODE:
            continue
        eid = (ln.get("location") or {}).get("element_id") or ""
        if eid.startswith("LINTEL:"):
            if eid[7:] in out:
                raise InputsError(f"lintel {eid[7:]} has two lines")
            out[eid[7:]] = ln
    return out


def material_base(src, faces, lintels):
    """contract net -> material base and its range; every face bound to its lintel line (valued / blank)."""
    net = float(src["measured_net"])
    f = faces.get(src["line_id"], {"required": [], "held": []})
    binds = []
    for x in f["required"]:
        ll = lintels.get(x["opening_id"])
        if ll is None or ll["evidence_state"] not in VALUED:
            raise InputsError(f"{src['line_id']}: REQUIRED lintel {x['opening_id']} has no valued {LINTEL_CODE} line "
                              f"(the face is concrete only where the lintel is carried)")
        binds.append({"opening_id": x["opening_id"], "lintel_line_id": ll["line_id"], "face_m2": x["face_m2"],
                      "lintel_m3": ll["measured_net"], "kind": "REQUIRED"})
    for x in f["held"]:
        ll = lintels.get(x["opening_id"])
        if ll is None or ll["evidence_state"] in VALUED:
            raise InputsError(f"{src['line_id']}: HELD lintel {x['opening_id']} must be a blank {LINTEL_CODE} line")
        binds.append({"opening_id": x["opening_id"], "lintel_line_id": ll["line_id"], "face_max_m2": x["face_max_m2"],
                      "kind": "HELD_RANGE", "why": x["why"]})
    ded = sum(x["face_m2"] for x in f["required"])
    base = net - ded
    if base < -FACE_TOL:
        raise InputsError(f"{src['line_id']}: lintel faces {_r(ded)} m2 exceed the line net {net} m2")
    base = max(base, 0.0)
    out = {"contract_net_m2": net, "lintel_deduction_m2": _r(ded), "material_base_m2": _r(base), "lintels": binds}
    if not f["held"]:
        return dict(out, base_state="EXACT", range_m2=None)
    if any(x["face_max_m2"] is None for x in f["held"]):
        return dict(out, base_state="HELD", range_m2=None,
                    why="a HELD lintel face cannot be bounded (width / band unknown): the material base is at most "
                        f"{_r(base)} m2, its lower end HELD")
    hi = sum(x["face_max_m2"] for x in f["held"])
    return dict(out, base_state="RANGE", range_m2=[_r(max(base - hi, 0.0)), _r(base)],
                why=f"{len(f['held'])} HELD / FLAGGED lintel(s) ({', '.join(x['opening_id'] for x in f['held'])}) may "
                    f"occupy 0 .. {_r(hi)} m2 of this masonry: a named range, never deducted silently, never 0")


def _blank(src, code, d, why, *, question, beside=None, extra=None):
    rec = _rec(d, evidence_status="HELD", source_line_id=src["line_id"], family=FAMILY[code], why=why[:600],
               figure_beside=beside, **(extra or {}))
    return _new_line(src, code=code, state="BLOCKED_RFI", net=None, what=ITEM_TEXT[code][0],
                     formula=f"HELD: {why}"[:1500], rec=rec,
                     rfi={"question": question[:400], "blocks": [src["line_id"]]},
                     notes=f"blank by name, never 0 (R-T498-1 (3)); source {SRC_CODE} {src['line_id']}")


def _valued(src, code, d, *, state, value, rng, formula, extra):
    st = "BOUNDED_EXPOSURE" if rng else state
    rec = _rec(d, evidence_status=("RANGE" if rng else state), source_line_id=src["line_id"], family=FAMILY[code],
               **extra)
    br = None if not rng else {"low": rng[0], "high": rng[1], "basis": extra.get("why", "")[:200]}
    return _new_line(src, code=code, state=st, net=None if rng else value, rng=br, what=ITEM_TEXT[code][0],
                     formula=formula, rec=rec,
                     notes=f"beside {SRC_CODE} {src['line_id']} (contract area unchanged); theoretical, waste separate "
                           f"(HELD: no sourced value)")


def materials_for(src, d, lintels):
    """one MAS.BLOCK line -> its material lines (R-T498-1)."""
    eid = (src.get("location") or {}).get("element_id") or ""
    m = EID.match(eid)
    colour = m.group("mat") if m else None
    t = float(m.group("t")) if m else None
    if src["evidence_state"] not in VALUED:
        why = (f"the masonry line {src['line_id']} ({eid}) is {src['evidence_state']}: its walls / pieces are held "
               f"by name in the candidate" + ("" if colour else "; its block colour is not split") +
               ": its materials follow it")
        q = ((src.get("rfi") or {}).get("question") or "the held masonry line is released")
        return [_blank(src, c, d, why, question=f"materials wait for {src['line_id']}: {q}") for c in BY_COLOUR[colour]]
    if colour is None or t is None:
        raise InputsError(f"{src['line_id']}: a released masonry line with no block type or thickness")
    mb = material_base(src, d["faces"], lintels)
    out = []
    if colour == "BLACK":
        b = black_rate(d["rulebook"], t)
        if b["status"] != OK:
            out.append(_blank(src, U_BLACK, d, b["why"], question="the installed black block face / module of this "
                              "thickness (block schedule, project evidence or supplier data)", extra={"base": mb}))
            jr = joint_m3_per_m2(d["joint"], t)
            out.append(_blank(src, MORTAR, d, "the joint geometry of this thickness is not established (module not "
                              "stated): the 40 x 20 joint figure is beside only",
                              question="the installed black block face / module of this thickness",
                              beside={"source": "T-367 40 x 20 module, contract net", "mortar_m3": _r(jr * mb["contract_net_m2"]),
                                      "per_m2": _r(jr, 8)}, extra={"base": mb}))
            return out
        if mb["base_state"] == "HELD":
            out.append(_blank(src, U_BLACK, d, mb["why"], question="the held lintel's width / band", extra={"base": mb}))
            out.append(_blank(src, MORTAR, d, mb["why"], question="the held lintel's width / band", extra={"base": mb}))
            return out
        rate = b["blocks_per_m2"]
        jr = joint_m3_per_m2(d["joint"], t)
        mp = d["rulebook"]["p"][R_MORTAR]
        mix = {"cement_bags": mp["cement_bags_per_m3"], "sand_m3_loose": mp["loose_sand_m3_per_m3"]}
        if mb["base_state"] == "RANGE":
            lo, hi = mb["range_m2"]
            ur, mr = [_r(lo * rate), _r(hi * rate)], [_r(lo * jr), _r(hi * jr)]
            uv = mv = None
        else:
            ur = mr = None
            uv, mv = _r(mb["material_base_m2"] * rate), _r(mb["material_base_m2"] * jr)
        ex = {"base": mb, "blocks_per_m2": rate, "module_m": b["module_m"], "module_basis": b["module_basis"],
              "why": mb.get("why", "")}
        out.append(_valued(src, U_BLACK, d, state=src["evidence_state"], value=uv, rng=ur, extra=ex, formula=(
            f"{_r(mb['material_base_m2'], 4)} m2 material base (= {mb['contract_net_m2']} contract net - "
            f"{mb['lintel_deduction_m2']} REQUIRED lintel faces) x {rate} / m2 ({R_BLOCK}, 40 x 20) = "
            f"{uv if ur is None else ur} pcs theoretical; breakage HELD")))
        cb = None if mv is None else _r(mv * mix["cement_bags"])
        sd = None if mv is None else _r(mv * mix["sand_m3_loose"])
        ex2 = dict(ex, joint=d["joint"], mortar_m3_per_m2=_r(jr, 8), beside_materials={
            "cement_bags_50kg": cb, "sand_m3_loose": sd, "per_m3": {"cement_bags": mix["cement_bags"],
                                                                     "sand_m3_loose": mix["sand_m3_loose"]},
            "note": "beside: the cross-trade cement / sand census sums PRODUCER rows once (T-511), not this line"},
            label_why="the 10 mm joint is owner-provisional (T-367): PROVISIONAL even on a VERIFIED area")
        out.append(_valued(src, MORTAR, d, state="PROVISIONAL", value=mv, rng=mr, extra=ex2, formula=(
            f"{_r(mb['material_base_m2'], 4)} m2 material base x {_r(jr, 8)} m3/m2 (t {t} x (1 - "
            f"{d['joint']['unit_m'][0]} x {d['joint']['unit_m'][1]} / {d['joint']['module_m'][0]} x "
            f"{d['joint']['module_m'][1]})) = {mv if mr is None else mr} m3 installed; 1:4 -> {cb} bags, {sd} m3 sand "
            f"beside; procurement HELD")))
        return out
    g = glue_rate(d["rulebook"], t)
    alt = {"62.5x25 (6.4 / m2)": _r(mb["material_base_m2"] * 6.4),
           "60x20 (8.33 / m2)": _r(mb["material_base_m2"] / (0.60 * 0.20)), "on_m2": mb["material_base_m2"]}
    if g["status"] != OK or mb["base_state"] == "HELD":
        out.append(_blank(src, GLUE, d, g.get("why") or mb["why"], question="the held lintel's width / band",
                          extra={"base": mb}))
    else:
        k = g["kg_per_m2"]
        rng = None if mb["base_state"] != "RANGE" else [_r(mb["range_m2"][0] * k), _r(mb["range_m2"][1] * k)]
        v = None if rng else _r(mb["material_base_m2"] * k)
        out.append(_valued(src, GLUE, d, state=src["evidence_state"], value=v, rng=rng,
                           extra={"base": mb, "kg_per_m2": k, "why": mb.get("why", ""),
                                  "bags_25kg_net": None if v is None else _r(v / 25.0),
                                  "bags": "rounded once per purchasing group by the census, never per line"},
                           formula=f"{_r(mb['material_base_m2'], 4)} m2 material base (= {mb['contract_net_m2']} - "
                                   f"{mb['lintel_deduction_m2']} REQUIRED lintel faces) x {k} kg/m2 "
                                   f"({R_GLUE}, t {t}) = {v if rng is None else rng} kg"))
    out.append(_blank(src, U_WHITE, d, "white AAC block face not selected by the project (supplier sheet: 62.5 x 25 "
                      "and 60 x 20); the company rules give no AAC count rule: HELD, never the black 12.5 / m2",
                      question="the AAC block face the project uses", beside=alt, extra={"base": mb}))
    return out


def changes_for(doc, prev):
    """-> (changes, log). Only ADD rows (material lines); every expected figure of the inputs asserted."""
    lintels = _lintels(prev)
    srcs = sorted((ln for ln in prev if ln["item_code"] == SRC_CODE), key=lambda x: x["line_id"])
    have = {ln["line_id"] for ln in prev}
    for c in CODES:
        if any(ln["item_code"] == c for ln in prev):
            raise InputsError(f"the base already carries {c} lines: one producer per material (R-T498-1 (2))")
    for lid in doc["faces"]:
        s = next((x for x in srcs if x["line_id"] == lid), None)
        if s is None:
            raise InputsError(f"lintel faces named on {lid}, not a {SRC_CODE} line of the base")
        if s["evidence_state"] not in VALUED:
            raise InputsError(f"lintel faces named on the HELD line {lid}: its material is HELD, nothing to deduct")
    changes, log = [], {"by_code": {}, "valued": {}, "ranges": {}, "blank": {}, "sources": len(srcs)}
    for s in srcs:
        for ln in materials_for(s, doc, lintels):
            if ln["line_id"] in have:
                raise InputsError(f"{ln['line_id']}: a material line repeats a candidate id")
            have.add(ln["line_id"])
            rec = ln["calculation"]["inputs"][REC_KEY]
            changes.append({"piece": P_MAT, "action": "ADD", "step": "ADD_MATERIAL", "before": None, "after": ln,
                            "evidence_status": rec["evidence_status"],
                            "held": None if ln["evidence_state"] != "BLOCKED_RFI" else
                            [{"what": ln["item_code"], "why": rec.get("why")}],
                            "verification": {"task": "T-453 r2 / T-506 / T-487 / T-488",
                                             "merge_commits": rec["merge_commits"]}})
            c = ln["item_code"]
            log["by_code"][c] = log["by_code"].get(c, 0) + 1
            if ln["measured_net"] is not None:
                log["valued"][c] = _r(log["valued"].get(c, 0.0) + ln["measured_net"])
            elif ln.get("bounded_range"):
                r = log["ranges"].setdefault(c, [0.0, 0.0])
                r[0], r[1] = _r(r[0] + ln["bounded_range"]["low"]), _r(r[1] + ln["bounded_range"]["high"])
            else:
                log["blank"].setdefault(c, []).append(s["line_id"])
    check_expect(changes, doc["expect"])
    return changes, log


def check_expect(changes, expect):
    """each expected figure of the inputs (source line id -> code -> value | [low, high] | 'HELD') equals the line."""
    got = {}
    for c in changes:
        a = c["after"]
        sid = a["calculation"]["inputs"][REC_KEY]["source_line_id"]
        v = a["measured_net"] if a["measured_net"] is not None else (
            [a["bounded_range"]["low"], a["bounded_range"]["high"]] if a.get("bounded_range") else "HELD")
        got.setdefault(sid, {})[a["item_code"]] = v
    for sid, codes in expect.items():
        for code, e in codes.items():
            g = got.get(sid, {}).get(code)
            ok = (g == e) if isinstance(e, str) or g is None or isinstance(g, str) else (
                all(abs(x - y) <= TOL for x, y in zip(g, e)) if isinstance(e, list) and isinstance(g, list)
                else (not isinstance(e, list) and not isinstance(g, list) and abs(g - e) <= TOL))
            if not ok:
                raise InputsError(f"{sid} {code}: line {g} != expected {e} (the merged ledgers' figure)")
    return True


def check_materials(lines):
    """every material line binds one masonry line of the same candidate; a valued material never sits on a held
    masonry line; a blank material is never 0; one producer per (masonry line, material)."""
    src = {ln["line_id"]: ln for ln in lines if ln["item_code"] == SRC_CODE}
    seen, n = set(), 0
    for ln in lines:
        if ln["item_code"] not in CODES:
            continue
        n += 1
        rec = ln["calculation"]["inputs"].get(REC_KEY) or {}
        s = src.get(rec.get("source_line_id"))
        if s is None:
            raise ValueError(f"{METHOD}: {ln['line_id']} binds no {SRC_CODE} line")
        key = (s["line_id"], ln["item_code"])
        if key in seen:
            raise ValueError(f"{METHOD}: two producers of {key}")
        seen.add(key)
        valued = ln["measured_net"] is not None or bool(ln.get("bounded_range"))
        if valued and s["evidence_state"] not in VALUED:
            raise ValueError(f"{METHOD}: {ln['line_id']} values a material on a held masonry line")
        if ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is not None:
            raise ValueError(f"{METHOD}: {ln['line_id']} a blank material carries a figure")
    return {"material_lines": n, "masonry_lines": len(src), "producers": len(seen)}


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.57 lines, identity). Added lines follow the base; every base line byte-identical (asserted)."""
    for c in changes:
        if c["action"] != "ADD" or c["after"]["item_code"] not in CODES:
            raise ValueError(f"{METHOD}: only material lines are added by this version")
    base_lines, ident = A3056.integrate(prev, [], for_lead)
    out = list(base_lines) + [c["after"] for c in changes]
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    bad = [a["line_id"] for a, b in zip(prev, out) if A30.line_sha(a) != A30.line_sha(b)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ")
    ident = {"base_lines": len(prev), "v3_0_57_lines": len(out), "v3_0_57_rows": len(changes), "replaced": 0,
             "added": len(changes), "v3_0_56_checks": {k: v for k, v in ident.items()
                                                      if k not in ("base_lines", "v3_0_56_lines", "v3_0_56_rows",
                                                                   "replaced", "added")},
             "materials": check_materials(out), "outside_rows": len(prev),
             "outside_rows_identical_to_base": len(prev),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in prev).encode()).hexdigest()}
    return out, ident


def check_totals(t0, t1):
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] not in CODES:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_57": t1.get(k)}
    return moved


def ledger_rows(changes, released_lines=None):
    rows = []
    for c in changes:
        a = c["after"]
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["step"], "change": c["action"],
                     "line_id": a["line_id"], "item_code": a["item_code"], "family": FAMILY[a["item_code"]],
                     "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": a["unit"],
                     "source_line_id": rec["source_line_id"], "before_released_v2_9": dict(A30._qty(None),
                                                                                          state="NOT_IN_RELEASED"),
                     "before_base": A30._qty(None), "after_v3_0_57": A30._qty(a),
                     "evidence_status": c["evidence_status"], "still_held": c.get("held"),
                     "release_status": "NOT RELEASED", "owner_manual_method": PIECES[P_MAT]["owner_manual_method"],
                     "drawing_derived_method": PIECES[P_MAT]["drawing_method"], "record": rec,
                     "verification": c["verification"], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "change", "line_id", "item_code", "family", "floor", "element_id", "unit",
              "source_line_id", "base", "v3_0_57", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_57")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "family": r["family"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "source_line_id": r["source_line_id"], "base": q(r.get("before_base")),
                       "v3_0_57": q(r.get("after_v3_0_57")), "evidence_status": r["evidence_status"],
                       "still_held": h(r), "verification": r["verification"]["task"]} for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_57=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_57_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_57_BOQ_LINES.json": BL.dumps(new),
             "V3_0_57_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_57_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_57_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_57_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_57_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": list(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "U_BLACK", "U_WHITE",
           "MORTAR", "GLUE", "load_inputs", "joint_m3_per_m2", "material_base", "materials_for", "material_ids",
           "changes_for", "check_expect", "check_materials", "integrate", "check_totals", "ledger_rows", "diff_rows",
           "write", "InputsError"]
