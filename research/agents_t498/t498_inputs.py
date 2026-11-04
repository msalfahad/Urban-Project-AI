"""T-498: the URBAN_V3058_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.58 (engine.source.arch_v3058), built ONLY from
pinned, merged files (an edited file stops the build):

  research/agents_t508/out/LINE_INDEX_V3_0_55.json  candidate line index V3.0.55 (a498fc61); its MAS.BLOCK and
      STR.CONC.LINTEL lines are those of V3.0.56 and V3.0.57 (T-508 moved skirting, T-310 waterproofing only: asserted by
      the runner against the V3_0_57 lines of the run of record);
  research/agents_t453/t453_material_ledger.py  T-453 r2 machinery (MERGED b16f686b, Verifier Gate A 2026-11-03):
      lintel decisions and faces (R-T453-4 / -5), materials per line (R-T453-1 .. 3), its own pinned inputs;
  research/agents_t488/t488_inputs.py  T-488 conditions (MERGED e8143e40, Gate B): the 8 roof-storey walls HELD
      (D-39) and GF-W22 CONFLICT (D-27) leave the released lines: their fill figures are carried as HELD here, so
      T-453's reconciliation closes against the V3.0.55 lines (residual 0 per line, asserted by build_from);
  research/agents_t367/MORTAR_BY_LINE_T367.csv  the T-367 joint (BESIDE only; T-506 verdict: T-453 r2 produces).

The T-367 row of a line whose net T-488 changed (GF 0.15 DC BLACK 21.5261 -> 8.595 m2) is restated at the same
per-m2 joint rate (uniform 40 x 20 geometry) for the BESIDE figure only (that line's mortar is HELD: 0.15 m module).

    python3 -I research/agents_t498/t498_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t279", ROOT / "research" / "agents_t453", ROOT / "research" / "agents_t488"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t453_material_ledger as T453  # noqa: E402
import t279_inputs as L26            # noqa: E402
import t488_inputs as I488           # noqa: E402
from engine.source import company_rulebook_v1 as CR  # noqa: E402  (research reads the rulebook; the engine does not)

SCHEMA = "URBAN_V3058_INPUTS_V1"
INDEX = ROOT / "research/agents_t508/out/LINE_INDEX_V3_0_55.json"
INDEX_SHA = None                     # pinned below after the first read (asserted in build)
CANDIDATE_LINES = "a498fc61c8484534d6682aff9409efd87733db6636ab4c366f7f5bb68b0e62cd"
JOINT = {"module_m": [0.40, 0.20], "unit_m": [0.39, 0.19], "joint_mm": 10,
         "status": "OWNER-PROVISIONAL (T-367 MASONRY_JOINT_MORTAR_V1, owner 2026-10-29: 10 mm bed and head joints)",
         "source": "research/agents_t367/MORTAR_BY_LINE_T367.csv (merged T-367; geometry re-derived by T-506 "
                   "R-T506-1: 0.07375 t m3/m2)"}
SOURCES = [
    {"task": "T-453 r2", "file": "research/agents_t453/t453_material_ledger.py", "merge_commit": "b16f686b",
     "checker_run": "Verifier 2026-11-03T08:55Z Gate A PASS on e4e9742c (R-T453-5 material base; hand checks)"},
    {"task": "T-506", "file": "research/agents_t506/t506_mortar_reconcile.py", "merge_commit": "T-506 MERGED (board)",
     "checker_run": "Verifier 2026-11-04 Gate A: one producer per key; T-453 r2 produces the mortar"},
    {"task": "T-487", "file": "engine/source/arch_v3053.py", "merge_commit": "dbc619fd",
     "checker_run": "Verifier 2026-11-04T10:02Z Gate B PASS: 16 REQUIRED / 44 blank lintel lines"},
    {"task": "T-488", "file": "research/agents_t488/t488_inputs.py", "merge_commit": "e8143e40",
     "checker_run": "Verifier 2026-11-04 Gate B PASS: own chain V3_0_54 c85c4630 -> V3_0_55 a498fc61"},
]


def rulebook():
    """the owner rulebook records V3.0.58 reads, copied from COMPANY_RULEBOOK_V1 with its digest (no value typed)."""
    return {"method": CR.METHOD, "version": CR.VERSION, "digest": CR.digest(),
            "records": {rid: {"status": CR.record(rid).get("status"),
                              "params": {k: (v.get("value") if isinstance(v, dict) else v)
                                         for k, v in CR.record(rid)["params"].items()}}
                        for rid in ("UPC-BLACK-BLOCK-001", "UPC-AAC-GLUE-001", "UPC-BLACK-MORTAR-001")}}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ledger():
    """the T-453 r2 machinery on the V3.0.55 MAS.BLOCK lines with the T-488 held walls carried HELD."""
    for p in T453.PINS:
        T453._pinned(p)
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    if idx["inputs"]["lines"] != CANDIDATE_LINES:
        raise SystemExit("the line index is not V3.0.55 a498fc61")
    other = [ln for ln in idx["lines"] if ln["item_code"] == "MAS.BLOCK" and not T453.EID.match(ln["element_id"])]
    if any(ln["class"] != "HELD" for ln in other):
        raise SystemExit("a released MAS.BLOCK line outside the wall keys")
    idx = dict(idx, lines=[ln for ln in idx["lines"] if ln not in other])
    fill = L26.build()
    c = I488.build()
    held = {w["wall_id"] for w in c["roof_datum"]["walls"]} | {x["wall_id"] for x in c["conflicts"]}
    nulled = []
    for ln in fill["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        for w in ln["walls"]:
            if w["wall_id"] in held and w["carried"] is not None:
                nulled.append({"wall_id": w["wall_id"], "carried_m2_v3054": w["carried"], "why": "T-488 HELD"})
                w["carried"] = None
    net = {ln["line_id"]: ln["measured_net"] for ln in idx["lines"]}
    mrows, restated = list(csv.DictReader(T453.MORTAR.open(encoding="utf-8", newline=""))), []
    for r in mrows:
        lid = r["part_line_id_v3026"]
        if net.get(lid) is not None and r["mortar_installed_m3"].strip() and \
                abs(float(r["area_m2 (established)"]) - net[lid]) > T453.TOL:
            rate = float(r["mortar_installed_m3"]) / float(r["area_m2 (established)"])
            restated.append({"line_id": lid, "area_v3026": float(r["area_m2 (established)"]), "area_now": net[lid],
                             "per_m2": round(rate, 8)})
            r["mortar_installed_m3"], r["area_m2 (established)"] = repr(rate * net[lid]), repr(net[lid])
    out = T453.build_from(idx, fill, json.loads(T453.REGISTER.read_text(encoding="utf-8")),
                          list(csv.DictReader(T453.OPENINGS.open(encoding="utf-8", newline=""))),
                          list(csv.DictReader(T453.SCHEDULE.open(encoding="utf-8", newline=""))), mrows)
    return out, {"held_walls_carried_held": sorted(nulled, key=lambda x: x["wall_id"]),
                 "t367_rows_restated_beside": restated,
                 "non_wall_held_lines": sorted(ln["line_id"] for ln in other)}


def _expect(mats):
    ex = {}
    for m in mats:
        if m["item"] == "BLOCK_COUNT":
            code = "MAS.UNITS.BLACK" if m["material_type"] == "BLACK" else "MAS.UNITS.WHITE"
            v = (m.get("theoretical_count") if m["status"] == "COMPUTED" else
                 m.get("theoretical_count_range") if m["status"] == "RANGE" else "HELD")
        elif m.get("material") == "white AAC glue":
            code = "MAS.GLUE.AAC"
            v = (m.get("consumption_kg") if m["status"] == "COMPUTED" else
                 m.get("consumption_kg_range") if m["status"] == "RANGE" else "HELD")
        elif m.get("material") == "black-block mortar 1:4":
            code = "MAS.MORTAR.BLACK"
            v = (m.get("mortar_installed_m3") if m["status"] == "COMPUTED" else
                 m.get("mortar_installed_m3_range") if m["status"] == "RANGE" else "HELD")
        else:
            continue
        if m["source_label"] == "HELD":
            # a held source line: T-453 names BLOCK_COUNT / LAYING_MATERIAL generically; the colour decides codes
            continue
        ex.setdefault(m["line_id"], {})[code] = v
    return ex


def build(project_id=None):
    led, notes = ledger()
    faces = {}
    for m in led["block_materials"]:
        if "lintel_deductions" not in m:
            continue
        req = [{"opening_id": x["opening_id"], "face_m2": x["face_m2"]} for x in m["lintel_deductions"]]
        held = [{"opening_id": x["opening_id"], "face_max_m2": x.get("face_max_m2"), "why": (x.get("why") or "")[:300]}
                for x in m["lintel_held_faces"]]
        if req or held:
            faces[m["line_id"]] = {"required": req, "held": held}
    srcs = [dict(s, sha256=_sha(ROOT / s["file"])) for s in SOURCES]
    return {"schema": SCHEMA, "project": project_id, "sources": srcs, "joint": JOINT, "faces": faces,
            "rulebook": rulebook(),
            "faces_on_held_hosts": [{"opening_id": x["opening_id"], "host": x["host"], "decision": x["decision"]}
                                    for x in led["lintel_reconciliation"]["faces_on_held_hosts"]],
            "expect": _expect(led["block_materials"]),
            "beside": {"t453_totals_on_v3_0_55": {"block_totals": led["block_totals"]["black_0_20_by_label"],
                                                  "glue_known_part": led["glue_groups"]["known_part_by_label"],
                                                  "glue_project_group": led["glue_groups"]["PROJECT"]["status"],
                                                  "mortar": led["mortar"]["black_0_20_provisional_net"],
                                                  "mortar_range": led["mortar"]["range_net"]},
                       "reconciliation_residuals": [r["residual_m2"] for r in led["reconciliation"]],
                       **notes}}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"faces": {k: [len(v["required"]), len(v["held"])] for k, v in d["faces"].items()},
                      "expect": d["expect"], "beside": d["beside"]["t453_totals_on_v3_0_55"],
                      "held_hosts": len(d["faces_on_held_hosts"])}, indent=1))
