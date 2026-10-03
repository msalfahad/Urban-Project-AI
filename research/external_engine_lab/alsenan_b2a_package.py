"""ALSENAN PHASE B2A - package URBAN_QTO_ALSENAN_PHASE_B2A_OWNER_METHODS (21 md + 14 json + xlsx + review image + zip),
built from the frozen registers, the post-freeze evaluation and the one full-suite junit.

    python3 research/external_engine_lab/alsenan_b2a_package.py <out_dir> <junit.xml> <rc> <head> <review_png>
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import alsenan_b2a_registers as REGS                                                                # noqa: E402

REG = ROOT / "tests/alsenan/registers_b2a"
EVAL = ROOT / "tests/alsenan/registers_b2a_eval/BENCHMARK_EVALUATION.json"
NAME = "URBAN_QTO_ALSENAN_PHASE_B2A_OWNER_METHODS"
JSONS = ["OWNER_FACT_REGISTER", "URBAN_METHOD_REGISTER", "STRUCTURAL_VERTICAL_INTERVAL_REGISTER", "BEAM_BINDING_REGISTER",
         "SLAB_REGION_REGISTER", "STAIR_REGISTER", "OPENING_AUTHORITY_REGISTER", "CURVED_OPENING_REGISTER",
         "WALL_HEIGHT_REGISTER", "WATERPROOFING_REGISTER", "ALSENAN_B2A_DELTA", "QORTUBA_REGRESSION", "REMAINING_BLOCKERS",
         "TEST_RESULTS"]


def R(n):
    return json.loads((REG / f"{n}.json").read_text())


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def junit(path, rc):
    t = ET.parse(path).getroot()
    s = t if t.tag == "testsuite" else t.find("testsuite")
    a = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    xf = sum(1 for c in s.iter("testcase") for k in c if k.tag == "skipped" and "xfail" in (k.get("type", "") + k.get("message", "")))
    return {"tests": a["tests"], "failures": a["failures"], "errors": a["errors"], "skipped_total": a["skipped"],
            "xfailed": xf, "skipped": a["skipped"] - xf, "passed": a["tests"] - a["failures"] - a["errors"] - a["skipped"],
            "exit_code": int(rc), "time_s": float(s.get("time", 0))}


def md(regs, ev, tr, head) -> dict:
    fz = regs["ALSENAN_PHASE_B2A_FREEZE"]
    sm = fz["summary"]
    sv, bb, sl = regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"], regs["BEAM_BINDING_REGISTER"], regs["SLAB_REGION_REGISTER"]
    pc, op, cu = regs["PHYSICAL_CONCRETE_REGISTER"], regs["OPENING_AUTHORITY_REGISTER"], regs["CURVED_OPENING_REGISTER"]
    wh, wp = regs["WALL_HEIGHT_REGISTER"], regs["WATERPROOFING_REGISTER"]
    sal = op["salon"]
    M = {}
    M["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan Phase B2A - executive summary

Head `{head}`; B2A code commit `{fz['code_commit']}`; base `f820263` (B1 accepted). Frozen before the benchmark
evaluation (BENCHMARK_OPENED = {fz['BENCHMARK_OPENED']}). QA gates: **{regs['QA_GATES']['state']}**. A3 behaviour:
**{regs['A3_PRESERVATION']['state']}**. Qortuba: **{regs['QORTUBA_REGRESSION']['state']}**.
Full suite: {tr['passed']} passed / {tr['failures']} failed / {tr['errors']} errors / {tr['skipped']} skipped /
{tr['xfailed']} xfailed, exit {tr['exit_code']}.

- Beam tags bound (BEAM_BINDING_V2): {json.dumps(sm['beam_tags'])}
- Beam occurrences: {json.dumps(sm['beam_occurrences'])}
- Columns by storey (interval - D of the member framing into each column): {json.dumps(sm['columns'])}
- Slabs: {json.dumps(sm['slabs'])}
- Physical concrete computed (non-overlapping, blocked parts excluded): {json.dumps(sm['physical_concrete_m3'])}
- Salon beam: {sal.get('beam_above', {}).get('type')} {sal.get('beam_above', {}).get('B_cm')} x {sal.get('beam_above', {}).get('D_cm')};
  soffit bound {sal.get('structural_soffit_upper_bound_m')} m; height {sal.get('height_m')} m stays {sal.get('state')}.
- Openings: {json.dumps(sm['openings'])}
- GF master bedroom: {sm['mbr']} ({wh['mbr']['floor_area_m2']} m2).

NO BENCHMARK CALIBRATION. NO PRICING. NO PRODUCTION MIGRATION.
"""
    M["01_OWNER_ACTIONS"] = """# Owner actions - Mohammad

1. Floor build-up (screed + finish) above each storey - needed for paint, wall tile and the salon aluminium head
   (structural soffit under CB1 is 3.75 m above GF FFL less that build-up).
2. GF entry: is the street entry an exterior door / screen, or open? (the GF Salon / Reception / Dining site cannot
   close without it; nothing is invented).
3. GF-W14 (1.00 m glazing between Wash and the room to its east): window, glazed door or fixed screen?
4. F / F10 footing size (SOURCE_CONFLICT carried from A3).
5. Founding level / footing-top level (column necks) and stair waist + riser (stair concrete).
"""
    rec = json.loads((ROOT / REGS.RECOMMENDATION).read_text())
    M["02_CLAUDE_RECOMMENDATION"] = "# Recommendation (committed before code)\n\n```json\n" + json.dumps(rec["answers"], indent=1, ensure_ascii=False)[:20000] + "\n```\n"
    M["03_OWNER_FACTS"] = "# Owner facts\n\n" + table(["id", "class", "statement"], [[f["id"], f["class"], f["statement"]] for f in regs["OWNER_FACT_REGISTER"]["facts"]]) + \
        "\n\nNo owner fact for F / F10. No benchmark statement is a fact.\n"
    M["04_URBAN_METHODS"] = "# Urban methods (versioned, scoped, overrideable)\n\n" + table(
        ["id", "statement", "never applies to"], [[m["id"], m["statement"], ", ".join(m["never_applies_to"])] for m in regs["URBAN_METHOD_REGISTER"]["methods"]])
    M["05_COLUMN_VERTICAL_INTERVALS"] = "# Column vertical intervals\n\nIntervals: " + json.dumps(sv["intervals"], ensure_ascii=False) + "\n\n" + table(
        ["floor", "type", "B x D cm", "state", "controlling member", "D_ctrl m", "height m", "volume m3", "joint m3"],
        [[r["floor"], r["type"], f"{r.get('B_cm')} x {r.get('D_cm')}", r["state"], r.get("controlling_member"), r.get("controlling_depth_m"),
          r.get("height_m"), r.get("volume_m3"), r.get("joint_m3")] for r in sv["rows"] if r["state"] not in ("NOT_IN_STOREY",)]) + \
        f"\n\nNeck: {sv['neck']['state']} - {sv['neck_why']}\n"
    rows = []
    for fl, s in bb["sheets"].items():
        for o in s["occurrences"]:
            L = o.get("lengths") or {}
            rows.append([fl, o["type"], o["namespace"], f"{o['B_cm']} x {o['D_cm']}", o["state"], L.get("PLAN_DRAWN_EXTENT"),
                         L.get("CLEAR_FACE_TO_FACE_LENGTH"), L.get("SUPPORT_CENTRELINE_LENGTH"), L.get("SCHEDULE_SPAN_LENGTH")])
    M["06_BEAM_TYPE_AND_LENGTH"] = "# Beam type and length\n\nTag states: " + json.dumps({k: v["binding_states"] for k, v in bb["sheets"].items()}) + \
        "\n\n" + table(["floor", "type", "ns", "B x D", "state", "drawn", "clear", "centre line", "schedule spans"], rows)
    M["07_SLAB_POLICY"] = "# Slab policy\n\n" + table(["floor", "closure", "gross m2", "openings m2", "net m2", "t cm", "volume m3", "dangles"],
        [[fl, s["closure"], s["gross_outline_area_m2"], s["openings_area_m2"], s["net_plate_area_m2"], s["sheet_thickness_tags_cm"], s["volume_m3"],
          s["dangling_line_ends"]] for fl, s in sl["sheets"].items()]) + \
        "\n\nPhysical model: slab = net plate x t; downstand = clear x B x (D - t); joint = column area x (D_ctrl - t); gross beam view separate.\n\n" + \
        table(["floor", "computed m3", "by component", "gross beam view m3", "state"],
              [[fl, s["model"]["computed_total_m3"], json.dumps(s["model"]["by_component_m3"]), s["gross_beam_view_m3"], s["model"]["total_state"]]
               for fl, s in pc["storeys"].items()]) + "\n\n" + table(["item", "state", "volume m3"],
              [[r["item"], r["state"], r.get("volume_m3")] for r in pc["explicit_items"]])
    st = regs["STAIR_REGISTER"]
    M["08_STAIR_CONCRETE"] = f"# Stair concrete\n\nState: **{st['result']['state']}** - missing {st['result'].get('missing')}.\n\nEvidence: {json.dumps(st['evidence'], ensure_ascii=False)}\n\nNever: {st['never']}.\n"
    M["09_OPENING_AUTHORITY"] = "# Opening authority\n\n" + table(["id", "width mm", "function", "basis"],
        [[r["id"], r["geometry"]["width_mm"], r["function"], r["function_basis"][:140]] for r in op["rows"]]) + \
        "\n\nAnnotated source image: `GF_1M_OPENINGS_REVIEW.png`.\n\nSalon: " + json.dumps(sal, ensure_ascii=False) + "\n"
    M["10_CURVED_ALUMINIUM"] = "# Curved aluminium\n\n" + table(["id", "inner m", "centre m", "outer m", "chord m", "commercial m", "basis"],
        [[r["id"]] + [r["bases_m"][k] for k in ("INNER", "CENTRE", "OUTER", "CHORD")] + [r["commercial_m"], r["authority"]] for r in cu["rows"]])
    M["11_WALL_HEIGHTS"] = "# Wall heights\n\nBlockwork / plaster: interval - D of the termination over each face; paint / tile: BLOCKED_FLOOR_BUILDUP.\n\n" + table(
        ["floor", "room", "wet", "faces terminated", "faces", "plaster gross (terminated faces) m2", "state"],
        [[r["floor"], r["room"], r["wet"], r["faces_terminated"], r["faces_total"], r["plaster_gross_computed_faces_m2"], r["room_plaster_state"]]
         for r in wh["rows"]]) + "\n\nGF open site: " + json.dumps(wh["gf_open_site"], ensure_ascii=False) + "\n\nReception: " + \
        json.dumps({k: v for k, v in wh["reception"].items() if k != "region"}, ensure_ascii=False) + "\n\nMBR: " + \
        json.dumps({k: v for k, v in wh["mbr"].items() if k not in ("unknown_parts",)}, ensure_ascii=False) + "\n"
    M["12_WET_ROOM_FINISHES"] = "# Wet-room finishes\n\nWall tile: URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 (to the finished ceiling) - blocked on the floor build-up. Floor tile: wet-room floor region; floor continues under cabinetry.\n\n" + \
        table(["room", "floor m2", "upturn m2", "physical WP m2"], [[r["room"], r.get("floor_m2"), r.get("upturn_m2"), r.get("physical_m2")] for r in wp["wet"]])
    M["13_WATERPROOFING"] = "# Waterproofing\n\nRoof upturn 0.20 m; wet upturn 0.15 m; laps NOT included (system unknown).\n\n" + table(
        ["region", "state", "flat m2", "upturn m2", "physical m2", "note"], [[r["region"], r["state"], r.get("flat_m2"), r.get("upturn_m2"), r.get("physical_m2"),
                                                                          r.get("note") or r.get("why")] for r in wp["roof"]])
    M["14_ALSENAN_REBUILD"] = "# Alsenan rebuild - A3 -> B2A delta\n\nRebuilt from the ORIGINAL SOURCE (A2 + A3 + B2A in one run). A3 registers rebuilt identical ignoring provenance: " + \
        str(len(regs["A3_PRESERVATION"]["identical_ignoring_provenance"])) + ".\n\n" + table(
        ["item", "A3 status", "A3 value", "B2A status", "B2A value", "unit", "generic fix", "fact / method"],
        [[r["item"], r["a3_status"], r["a3_value"], r["b2a_status"], r["b2a_value"], r["unit"], r["generic_fix"][:70], r["fact_or_method"]]
         for r in regs["ALSENAN_B2A_DELTA"]["rows"]])
    M["15_BENCHMARK_EVALUATION"] = "# Benchmark evaluation (after the freeze)\n\nFreeze sha256 `" + ev["b2a_freeze_sha256"] + "`. Evaluation only - nothing here feeds any engine.\n\n" + table(
        ["id", "item", "A3", "B2A", "bench", "% B2A vs bench", "comparability", "finding"],
        [[r["id"], r["item"][:45], r["a3_urban"], r["b2a_urban"], r["bench"], r["pct_b2a_vs_bench"], r["b2a_comparability"], r["finding"][:120]]
         for r in ev["rows"]]) + "\n\nSlab + downstand per storey (B2A): " + json.dumps(ev["slab_plus_downstand_m3"]) + "\n"
    q = regs["QORTUBA_REGRESSION"]
    M["16_QORTUBA_REGRESSION"] = f"# Qortuba regression\n\nState: **{q['state']}**; registers {q['registers']}; identical {len(q['identical'])}; changed {q['changed']}; extra {q['extra']}.\n\nNo Qortuba file edited; no Qortuba-specific code.\n"
    M["17_REMAINING_BLOCKERS"] = "# Remaining blockers\n\n" + table(["item", "state", "count / why"],
        [[r["item"], r["state"], r.get("count", r.get("why"))] for r in regs["REMAINING_BLOCKERS"]["rows"]])
    M["18_NEXT_BLIND_TEST"] = """# Next blind test

Run the unseen villa through the same adapters with no project fact carried over: registration by column outlines,
beam binding V2, vertical intervals, slab regions, opening authority. Owner facts are re-asked per project; methods
carry (versioned). Stop after B2A on Alsenan unless a silent critical engine defect is found.
"""
    M["19_TEST_RESULTS"] = "# Test results\n\n```json\n" + json.dumps(tr, indent=1) + "\n```\n\nSynthetic engine tests: tests/alsenan/test_b2a_engines_synthetic.py; frozen register tests: tests/alsenan/test_alsenan_b2a_real.py.\n"
    M["20_FINAL_RECOMMENDATION"] = """# Final recommendation

- Accept B2A as a generic-engine round: beam binding, column vertical intervals, slab regions, the physical concrete
  model, opening authority and curved bases are project-agnostic and Qortuba is unchanged.
- Do not tune Alsenan further. Remaining blockers are owner facts (build-up, entry, GF-W14, F/F10, founding level,
  stair waist/riser) or source gaps (2F slab outline, unbound tags).
- Next: the unseen villa as a blind test. NO PRODUCTION MIGRATION.
"""
    return M


def main(out, junit_path, rc, head, review_png):
    out = Path(out) / NAME
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    regs = {p.stem: json.loads(p.read_text()) for p in sorted(REG.glob("*.json"))}
    ev = json.loads(EVAL.read_text())
    tr = junit(junit_path, rc)
    regs["TEST_RESULTS"] = dict(regs["TEST_RESULTS"], state="RECORDED", full_suite=tr, head=head)
    for n, t in md(regs, ev, tr, head).items():
        (out / f"{n}.md").write_text(t)
    for n in JSONS:
        (out / f"{n}.json").write_text(json.dumps(regs[n], indent=1, ensure_ascii=False) + "\n")
    (out / "BENCHMARK_EVALUATION.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False) + "\n")
    model = REGS.workbook(regs)
    x = REGS.write_xlsx(model, out / REGS.XLSX_NAME)
    rb = REGS.readback(out / REGS.XLSX_NAME, model)
    shutil.copy(review_png, out / "GF_1M_OPENINGS_REVIEW.png")
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    (out / "MANIFEST.json").write_text(json.dumps({"head": head, "files": man, "xlsx": x, "xlsx_readback": rb["state"]}, indent=1) + "\n")
    z = out.parent / f"{NAME}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(out.iterdir()):
            zi = zipfile.ZipInfo(f"{NAME}/{p.name}", date_time=(2026, 10, 3, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, p.read_bytes())
    print(json.dumps({"dir": str(out), "md": len(list(out.glob("*.md"))), "json": len(list(out.glob("*.json"))),
                      "xlsx": x["file_sha256"], "readback": rb["state"], "zip": str(z),
                      "zip_sha256": hashlib.sha256(z.read_bytes()).hexdigest(), "tests": tr}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:6])
