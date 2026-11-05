"""T-537: R-T498-2 applied to the 2 staged AAC glue hosts of the development villa (the T-498 stage lines that T-530
names), from committed, merged inputs only (no drawing needed):

  research/agents_t453/out/MATERIAL_LEDGER_T453.json   host net, rate, REQUIRED and HELD lintel faces (T-453 r2)
  research/agents_t530/WIRING_MANIFEST_T530.json       the lintel lines after the T-516 / T-519 / T-524 wiring
                                                       (section B x D, length interval, state) and T-530's own after
  research/agents_t523/t523_binding_map_v2.py          the R-T523-1 group function and bindings (merged, not copied)
  research/agents_t516/out/JAMB_BEARING_T516.json      per-end state and bearing ceiling (R-T516-1, Checker AGREE)
  research/agents_t527/out/EFFECT_T527.json            the V1 -> V2 -> V3 end changes (R-T527-1), applied on top

r2 (Checker r1 e/h): a HELD_BY_NAME lintel's T-524 hi is a MIN-BEARING figure (BOUNDED ends kept at 0.40); its L_hi is
re-bound by R.ceiling_length from the V3 end ceilings, or OPEN where a BOUNDED end has none.

Every face is recomputed here as D x L from the lintel line (never read from T-530's face column); T-530's after is
reproduced only under the CONDITIONAL reading (legacy held maxima accepted) and compared, as an independent check.
No file is written: tests/t537_ranged_face asserts every figure against the hand calculation (T-537_RANGED_FACE.md).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import r_t498_2 as R          # noqa: E402

T453_LEDGER = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
T530_MANIFEST = ROOT / "research/agents_t530/WIRING_MANIFEST_T530.json"
T516_BEARING = ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json"
T527_EFFECT = ROOT / "research/agents_t527/out/EFFECT_T527.json"
HOSTS = ("L-2fdc0f971a94348ec855", "L-a3f88ecda2402f67c500")
MIN_BEARING_SUM = 0.80          # T-453 length = w + 2 x 0.40 printed minimum (R-T453-5, R-T516-1 lower bound)
PACK_KG = 25.0
TOL = 1e-6


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _r(x, n=6):
    return R._r(x, n)


def v3_ends():
    """{opening_id: {side: {"state", "bearing_hi_m", "available_m"}}}: the T-516 rows with T-527's V1->V2->V3 end
    changes applied (each change's 'before' must match, else refused)."""
    ends = {}
    for r in _json(T516_BEARING)["rows"]:
        ends[r["opening_id"]] = {e["side"]: {"state": e["state"], "bearing_hi_m": e.get("bearing_hi_m"),
                                             "available_m": e.get("available_m")} for e in r["ends"]}
    steps = _json(T527_EFFECT)["steps"]
    for step in ("V1_to_V2", "V2_to_V3"):
        for oid, changes in steps[step]["t516"].items():
            for path, before, after in changes:
                p = path.split(".")
                if p[0] != "ends" or p[2] not in ("state", "bearing_hi_m", "available_m"):
                    continue
                cur = ends[oid][p[1]]
                if cur[p[2]] != before:
                    raise R.RuleError(f"{oid} {p[1]} {p[2]}: T-527 {step} 'before' {before} != {cur[p[2]]}")
                cur[p[2]] = after
    return ends


def _ceiling_input(li, ends):
    """HELD_BY_NAME (T-524 min-bearing hi) -> the same lintel with L_hi bound by the V3 end ceilings (R-T498-2 (1))."""
    oid = li["opening_id"]
    es = [{"side": side, "state": e["state"], "ceiling_m": e["bearing_hi_m"],
           "a_m": e["bearing_hi_m"] if e["state"] == "FLAGGED_DEFICIT" else None} for side, e in ends[oid].items()]
    c = R.ceiling_length(oid, li["length_m"], es)
    out = dict(li, length_m=c["length_m"], length_hi_basis=c["length_hi_basis"] or "MIN_BEARING",
               t524_length_m=list(li["length_m"]), ceiling_why=c["why"])
    if c["length_hi_basis"] is None:          # no ceiling: the face opens (lintel_face holds it)
        out["length_m"] = [c["length_m"][0], None]
    return out


def _lintel_input(row):
    """a T-530 lintel line -> an R-T498-2 lintel input (pairs are not on these hosts: refused if met)."""
    oid = row["element_id"].split(":", 1)[1]
    a = row["after"]
    if "pair" in a:
        raise R.RuleError(f"{oid}: a paired lintel on a valued host (use pair_faces)")
    if a["state"] not in ("BOUNDED_MIN_BEARING", "HELD_BY_NAME") or "length_m" not in a:
        raise R.RuleError(f"{oid}: lintel line state {a['state']} without a length interval")
    return {"opening_id": oid, "state": a["state"], "section_B_D_m": row["section_B_D_m"],
            "length_m": a["length_m"], "lintel_line_id": row["line_id"]}


def _held_input(h, conditional):
    if abs(h["face_max_m2"] - h["depth_m"] * h["length_m"]) > TOL or \
            abs(h["length_m"] - (h["width_m"] + MIN_BEARING_SUM)) > TOL:
        raise R.RuleError(f"{h['opening_id']}: the held face maximum is not D x (w + 0.80): basis unknown")
    return {"opening_id": h["opening_id"], "state": "HELD_FACE", "face_max_m2": h["face_max_m2"],
            "face_max_basis": "UPPER_PROVEN" if conditional else "MIN_BEARING_LENGTH"}


def host(m, lintels, *, conditional=False):
    """strict (R-T498-2 r2): HELD_BY_NAME lintels carry their ceiling-bound L_hi; conditional: the T-530 reading (the
    T-524 hi and the legacy held maxima taken as ceilings), kept only to reproduce T-530."""
    t = m["thickness_m"]
    faces = []
    for d in m["lintel_deductions"]:
        lz = lintels[d["opening_id"]]
        if abs(lz["section_B_D_m"][1] - d["depth_m"]) > TOL:
            raise R.RuleError(f"{d['opening_id']}: lintel line depth differs from the ledger face depth")
        f = R.lintel_face(lz, t)
        f["lintel_line_id"] = lz["lintel_line_id"]
        f["lintel_state"] = lz["state"]
        f["length_m"] = list(lz["length_m"])
        if "t524_length_m" in lz:
            f["t524_length_m"], f["ceiling_why"] = lz["t524_length_m"], lz["ceiling_why"]
        f["t453_face_m2"] = d["face_m2"]
        faces.append(f)
    for h in m.get("lintel_held_faces") or []:
        f = R.lintel_face(_held_input(h, conditional), t)
        f["t453_face_max_m2"] = h["face_max_m2"]
        faces.append(f)
    base = R.material_base(m["net_m2"], faces)
    glue = R.material_line(base, m["kg_per_m2"], "kg")
    bags = R.material_line(base, m["kg_per_m2"] / PACK_KG, "bags_25kg_net")
    return {"base": base, "glue_kg": glue, "bags_25kg_net": bags}


def _glue_group(moves):
    """the T-523 AAC glue group re-run with its own function on its own bindings, the 2 hosts moved."""
    spec = importlib.util.spec_from_file_location("t523_for_t537_group", ROOT / "research/agents_t523/"
                                                  "t523_binding_map_v2.py")
    m523 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m523)
    t523 = m523.run()
    if t523["failures"]:
        raise R.RuleError("the T-523 map fails its own checks")
    bs = copy.deepcopy(t523["bindings"])
    for b in bs:
        if b["table"] == "T-453" and b["kind"] == "glue_bags_25kg_net" and b["line_id"] in moves:
            ln = moves[b["line_id"]]
            if ln["state"] == "HELD":
                b["value"], b["bound"] = None, None
            elif ln["state"] == "VALUED":
                b["value"], b["bound"] = ln["value"], None
            else:
                b["value"], b["bound"] = None, list(ln["range"])
    g = m523.glue_and_adhesive(bs)["AAC_GLUE_25KG"]
    return {k: g[k] for k in ("status", "at_least", "to_buy_at_least", "open")}


def build():
    led = {m["line_id"]: m for m in _json(T453_LEDGER)["block_materials"] if m["item"] == "LAYING_MATERIAL"}
    man = _json(T530_MANIFEST)
    ends = v3_ends()
    lintels, lintels_t530 = {}, {}
    for row in man["stream_S"]["lintel_lines"]:
        if "pair" in row["after"]:
            continue
        li = _lintel_input(row)
        if li["state"] == "HELD_BY_NAME":
            lintels_t530[li["opening_id"]] = dict(li, length_hi_basis="CEILING")     # T-530's reading (conditional)
            lintels[li["opening_id"]] = _ceiling_input(li, ends)
        else:
            lintels_t530[li["opening_id"]] = lintels[li["opening_id"]] = li
    t530_after = {h["host_line_id"]: h for h in man["stream_S"]["host_material_lines"]}
    rows, strict_moves, cond_moves = [], {}, {}
    for lid in HOSTS:
        m = led[lid]
        strict = host(m, lintels)
        cond = host(m, lintels_t530, conditional=True)
        t5 = t530_after[lid]
        agree = (cond["glue_kg"]["range"] == t5["after"]["kg_range"]
                 and cond["base"]["base_m2"] == t5["after"]["material_base_range_m2"])
        if not agree:
            raise R.RuleError(f"{lid}: the CONDITIONAL reading does not reproduce T-530 ({cond['glue_kg']} vs "
                              f"{t5['after']['kg_range']})")
        before = {"material_base_m2": m.get("material_base_m2"), "material_base_range_m2": m.get("material_base_range_m2"),
                  "glue_kg": m.get("consumption_kg"), "glue_kg_range": m.get("consumption_kg_range"),
                  "bags_25kg_net": m.get("bags_25kg_net"), "bags_25kg_net_range": m.get("bags_25kg_net_range"),
                  "state": m["status"], "rule": "R-T498-1 1.0.0 (T-453 r2 machinery)"}
        if (before["glue_kg"], before["glue_kg_range"]) != (t5["before"]["kg"], t5["before"]["kg_range"]):
            raise R.RuleError(f"{lid}: T-453 ledger and T-530 before disagree")
        rows.append({"host_line_id": lid, "t498_stage_line": t5["t498_stage_line"], "host_element": m["element_id"],
                     "contract_net_m2": m["net_m2"], "kg_per_m2": m["kg_per_m2"], "before": before,
                     "after_r_t498_2": strict, "conditional_beside": {
                         "reading": "CONDITIONAL: IF every legacy held face maximum D x (w + 0.80) were a ceiling "
                                    "(not proven: F-T537-1); reproduces T-530's after exactly (independent check)",
                         "base_m2": cond["base"]["base_m2"], "glue_kg": cond["glue_kg"],
                         "bags_25kg_net": cond["bags_25kg_net"], "t530_kg_range": t5["after"]["kg_range"],
                         "agrees_with_t530": agree}})
        strict_moves[lid] = strict["bags_25kg_net"]
        cond_moves[lid] = cond["bags_25kg_net"]
    group = {"group": "AAC_GLUE_25KG (25 kg bags, villa), R-T523-1 via the T-523 function",
             "before_t530": man["stream_S"]["glue_group"]["before"],
             "after_conditional": _glue_group(cond_moves),
             "after_r_t498_2": _glue_group(strict_moves),
             "t530_after": man["stream_S"]["glue_group"]["after"]}
    if group["after_conditional"]["at_least"] != group["t530_after"]["at_least"]:
        raise R.RuleError("the conditional glue group does not reproduce T-530")
    return {"schema": "T537_APPLICATION_V2", "rule": f"{R.RULE_ID} {R.RULE_VERSION}", "extends": R.EXTENDS,
            "inputs": {"t453_ledger": str(T453_LEDGER.relative_to(ROOT)), "t530_manifest": str(T530_MANIFEST.relative_to(ROOT)),
                       "t523": "research/agents_t523/t523_binding_map_v2.py",
                       "t516": str(T516_BEARING.relative_to(ROOT)), "t527": str(T527_EFFECT.relative_to(ROOT))},
            "hosts": rows, "glue_group": group, "released_quantities_changed": 0,
            "note": "opt-in candidate not touched; the 2 lines are T-498 stage lines (not merged); nothing released"}


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
