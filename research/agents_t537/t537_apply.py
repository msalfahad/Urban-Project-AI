"""T-537: R-T498-2 applied to the 2 staged AAC glue hosts of the development villa (the T-498 stage lines that T-530
names), from committed, merged inputs only (no drawing needed):

  research/agents_t453/out/MATERIAL_LEDGER_T453.json   host net, rate, REQUIRED and HELD lintel faces (T-453 r2)
  research/agents_t530/WIRING_MANIFEST_T530.json       the lintel lines after the T-516 / T-519 / T-524 wiring
                                                       (section B x D, length interval, state) and T-530's own after
  research/agents_t523/t523_binding_map_v2.py          the R-T523-1 group function and bindings (merged, not copied)

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
HOSTS = ("L-2fdc0f971a94348ec855", "L-a3f88ecda2402f67c500")
MIN_BEARING_SUM = 0.80          # T-453 length = w + 2 x 0.40 printed minimum (R-T453-5, R-T516-1 lower bound)
PACK_KG = 25.0
TOL = 1e-6


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _r(x, n=6):
    return R._r(x, n)


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
    t = m["thickness_m"]
    faces = []
    for d in m["lintel_deductions"]:
        lz = lintels[d["opening_id"]]
        if abs(lz["section_B_D_m"][1] - d["depth_m"]) > TOL:
            raise R.RuleError(f"{d['opening_id']}: lintel line depth differs from the ledger face depth")
        f = R.lintel_face(lz, t)
        f["lintel_line_id"] = lz["lintel_line_id"]
        f["lintel_state"] = lz["state"]
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
    lintels = {}
    for row in man["stream_S"]["lintel_lines"]:
        if "pair" in row["after"]:
            continue
        li = _lintel_input(row)
        lintels[li["opening_id"]] = li
    t530_after = {h["host_line_id"]: h for h in man["stream_S"]["host_material_lines"]}
    rows, strict_moves, cond_moves = [], {}, {}
    for lid in HOSTS:
        m = led[lid]
        strict = host(m, lintels)
        cond = host(m, lintels, conditional=True)
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
    return {"schema": "T537_APPLICATION_V1", "rule": f"{R.RULE_ID} {R.RULE_VERSION}", "extends": R.EXTENDS,
            "inputs": {"t453_ledger": str(T453_LEDGER.relative_to(ROOT)), "t530_manifest": str(T530_MANIFEST.relative_to(ROOT)),
                       "t523": "research/agents_t523/t523_binding_map_v2.py"},
            "hosts": rows, "glue_group": group, "released_quantities_changed": 0,
            "note": "opt-in candidate not touched; the 2 lines are T-498 stage lines (not merged); nothing released"}


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
