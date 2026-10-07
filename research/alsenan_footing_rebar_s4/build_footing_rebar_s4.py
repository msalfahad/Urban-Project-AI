"""ALSENAN S4 - accurate footing rebar through the generic engine (engine.source.footing_rebar).

    python3 -I research/alsenan_footing_rebar_s4/build_footing_rebar_s4.py

Blind build: reads ONLY controlled Urban structures, never the drawing and never a reference / donor / old total:
  * the frozen S1 footing registers (occurrences, definitions);
  * the frozen pre-S4 readiness package (token parity register, BOXED occurrences, header binding, its INDEX);
  * the R4 project rule register (soil-contact cover).
Every bar token is re-admitted live through engine.source.footing_rebar_guard. Writes the S4 registers and the
S4_FREEZE_MANIFEST.json (code, inputs and outputs hashed). The post-freeze comparison is a separate script that
refuses to run unless this manifest still matches. Deterministic: two runs give identical bytes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import footing_rebar as FR  # noqa: E402
from engine.source import footing_rebar_guard as FG  # noqa: E402

BASELINE = "e3633af"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
S1 = ROOT / "research/alsenan_structural_census_s1"
PRE = ROOT / "research/pre_s4_footing_readiness"
R4_RULES = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
CODE = ["engine/source/footing_rebar.py", "engine/source/footing_rebar_guard.py", "engine/source/accurate_boq_rebar.py",
        "engine/source/rebar_model.py", "engine/source/rebar_unit_mass.py", "engine/source/schedule_grammar.py",
        "engine/source/structural_schedule.py", "engine/source/slab_rebar_binding.py",
        "research/alsenan_footing_rebar_s4/build_footing_rebar_s4.py"]
INPUTS = ["research/alsenan_structural_census_s1/FOOTING_OCCURRENCE_REGISTER.json",
          "research/alsenan_structural_census_s1/FOOTING_DEFINITION_REGISTER.json",
          "research/pre_s4_footing_readiness/01_FOOTING_TOKEN_PARITY_REGISTER.csv",
          "research/pre_s4_footing_readiness/03_BOXED_OCCURRENCES.csv",
          "research/pre_s4_footing_readiness/PRE_S4_SUMMARY.json",
          "research/pre_s4_footing_readiness/INDEX.json",
          "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"]
OUTPUTS = ["F3_AUTHORITY_DECISION.json", "FOOTING_REBAR_OCCURRENCE_REGISTER.json", "FOOTING_REBAR_OCCURRENCES.csv",
           "FOOTING_REBAR_COMPONENTS.csv", "FOOTING_BBS_NET.csv", "FOOTING_REBAR_RELEASE_SUMMARY.json",
           "FOOTING_REBAR_UNRESOLVED.csv", "FOOTING_REBAR_PROVENANCE.jsonl", "FOOTING_REBAR_ENGINEERING_FLAGS.csv"]

# Section 0: the F3 authority decision (recorded before any calculation)
F3_DECISION = {
    "question": "OQ-11 (V3C donor audit, 'F3 is tagged twice on the foundation plan; the [reference] has one')",
    "origin": "an external reference-count comparison only (V3C_FORENSIC_ACCURACY_DONOR_AUDIT.md line 187 / 529)",
    "is_owner_instruction": False, "is_consultant_instruction": False, "is_project_claim": False,
    "is_source_conflict_in_project_documents": False,
    "project_source": "two independent outlines (166B, 166C), each with its own C3/F3 tag (168F, 168E), both drawn at "
                      "the scheduled 160 x 140 cm (S1 FOOTING_OCCURRENCE_REGISTER; R9.1 08 FO10 / FO11)",
    "decision": "F3 occurrence count = 2, SOURCE_VERIFIED; the reference disagreement is a comparison / engineering "
                "flag and never changes the project-source release state",
    "supersedes": "pre-S4 COUNT_QUERIES {F3: OQ-11} (which held F3 PROVISIONAL); the pre-S4 package itself is frozen "
                  "and unchanged"}

QUESTION_BOXED = "Q-R3-6"
QUESTION_FF_SIDE = "S4-Q1"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def verify_pre_s4():
    idx = _j(PRE / "INDEX.json")
    for n in ("01_FOOTING_TOKEN_PARITY_REGISTER.csv", "03_BOXED_OCCURRENCES.csv", "PRE_S4_SUMMARY.json"):
        if _sha(PRE / n) != idx["files"][n]:
            raise SystemExit(f"pre-S4 package altered: {n}")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode() + b"\0" + (ROOT / c).read_bytes() + b"\0")
    return h.hexdigest()


def rules():
    cov = next(r for r in _j(R4_RULES)["rules"] if r["rule_id"] == "COVER_AGAINST_SOIL_70MM")
    if "FOOTING" not in cov["applies_to"] or cov["value"] != 70:
        raise SystemExit("cover rule does not apply to footings")
    summ = _j(PRE / "PRE_S4_SUMMARY.json")
    direction = summ["boxed"]["diagnostics"]
    return {
        "cover": {"value_mm": float(cov["value"]), "rule_id": cov["rule_id"], "authority": "SOURCE_EXPLICIT",
                  "evidence": f"{cov['claim_id']} ({cov['source_state']}); applies to {cov['applies_to']}"},
        "direction": {"rule_id": "PRE-S4-SHORT-SPANS-W-ALONG-L", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                      "evidence": {"note": direction["bar_direction_note"],
                                   "spacing_cm_short_long": direction["bar_direction_check"],
                                   "spacing_cm_if_reversed": direction["bar_direction_check_if_reversed"]}},
        "distribution": {"rule_id": "COUNT_PER_METRE_LB_INSIDE_COVER", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                         "evidence": "verified n = ceil(rate x (dimension - 2 x cover)); the +1 edge bar is BEST only"},
        "end_bottom": {"state": FR.END_STRAIGHT, "rule_id": "P13-FOOTING-TYP-STRAIGHT-BOTTOM",
                       "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                       "evidence": "ST7757.pdf p.13 TYP. DETAIL OF ISOLATED FOOTING (and deep variant): bottom long / "
                                   "short bars drawn straight between the side legs; no hook drawn"},
        "end_top": {"state": FR.END_UNKNOWN, "rule_id": "TOP_LAYER_END_DETAIL_NOT_DRAWN",
                    "authority": "UNRESOLVED", "evidence": "no detail shows the top-layer bar ends of a two-layer "
                                                          "footing (bend down / hook not drawn or dimensioned)"}}


def definitions(R):
    """Normalised schedule interpretation: one definition per schedule row (mark)."""
    defs = {r["footing_type"]: r for r in _j(S1 / "FOOTING_DEFINITION_REGISTER.json")["rows"]}
    tokens = _rows(PRE / "01_FOOTING_TOKEN_PARITY_REGISTER.csv")
    boxed = {r["FOOTING_MARK"]: r for r in _rows(PRE / "03_BOXED_OCCURRENCES.csv") if r["BLOCK"] == "FT"}
    hb = {(r["mark"], r["sub_row"]): r for r in _j(PRE / "PRE_S4_SUMMARY.json")["header_binding"]["rows"]}
    out = []
    for mark, d in sorted(defs.items()):
        bind = hb.get((mark, "ROW")) or hb.get((mark, "TOP"))
        if bind is None or bind["state"] != "BOUND_BY_HEADER":
            raise SystemExit(f"{mark}: schedule row not bound by drawn header")
        raw = d["source_row"]["raw_attributes"]
        hdr = bind["derived"]
        dims = {}
        for tag, head in hdr.items():
            if head in ("L", "W", "H"):
                dims[head] = float(raw[tag]) * 10.0                         # cm -> mm, bound by drawn header
        if (dims["L"], dims["W"], dims["H"]) != (d["L_cm"] * 10, d["W_cm"] * 10, d["D_cm"] * 10):
            raise SystemExit(f"{mark}: header-bound dimensions disagree with the S1 definition")
        short_run = "W" if dims["W"] <= dims["L"] else "L"
        long_run = "L" if short_run == "W" else "W"
        layers = "SINGLE_LAYER" if d["element"] == "FOOTING" else "TWO_LAYER"
        comps = []
        for t in tokens:
            if t["FOOTING_MARK"] != mark or not t["SOURCE_TYPE"].startswith("SCHEDULE_ATTRIB_CELL_PAIR"):
                continue
            cnt, dia = [x.strip() for x in t["RAW_TEXT"].split("|")]
            adm = FG.admit_cells(cnt, dia)                                  # live, production guard
            comp = t["COMPONENT"]
            is_short = comp.endswith("SHORT")
            per_m = bool(adm.get("form") and adm["form"]["per_m"])
            ins, cells = t["SOURCE_HANDLE"].split(":")
            comps.append({
                "component": comp, "count_mode": FR.BARS_PER_METRE if per_m else FR.EXPLICIT_COUNT,
                "count_value": adm["form"]["count"] if adm.get("form") else None,
                "dia_mm": adm["form"]["dia_mm"] if adm.get("form") else None,
                "run_dir": short_run if is_short else long_run, "dist_dir": long_run if is_short else short_run,
                "end_treatment": R["end_top"] if comp.startswith("TOP") else R["end_bottom"],
                "source_handles": [ins] + cells.split("+"), "source_text": t["RAW_TEXT"] + f" ({t['SOURCE_TYPE']})",
                "admission": adm, "authority": "SOURCE_EXPLICIT", "token_id": t["TOKEN_ID"]})
        bx = None
        if mark in boxed:
            b = boxed[mark]
            raw_v = "" if b["RAW_VALUE"] == "(empty)" else b["RAW_VALUE"]
            bx = {"raw_value": raw_v, "source_handles": b["HANDLE"].split(":"), "semantics_class": b["SEMANTICS_CLASS"],
                  "question_id": QUESTION_BOXED, "detail_reference": b["DETAIL_REFERENCES"],
                  "reason": (f"BOXED '{raw_v}': component exists (p.13 'Boxed bars.'); count / diameter / shape / "
                             "length not stated anywhere (pre-S4 source exhaustion: UNRESOLVED)") if raw_v else
                            ("BOXED cell EMPTY (template default '3+-' cleared); whether the footing has boxed bars is "
                             "not stated (pre-S4: UNRESOLVED (EMPTY CELL))")}
        extras = []
        if mark == "FF":
            extras.append({"reason": "p.14 lift-footing detail: '2 Ø16' labels at the footing side / wall base - "
                                     "applicability (footing side bar or wall-base bar) and length not stated",
                           "source_handles": ["PDF:p14:P14_LIFT_FOOTING"], "source_text": "2 Ø16",
                           "question_id": QUESTION_FF_SIDE})
        out.append({"mark": mark, "layers": layers, "L_mm": dims["L"], "W_mm": dims["W"], "D_mm": dims["H"],
                    "row_handle": d["source_row"]["insert_handle"], "drawing_sha": DRAWING_SHA,
                    "sheet_region": "Schedule of Footings (p.9)", "components": comps, "boxed": bx, "extras": extras,
                    "schedule_state": d["state"]})
    return out


def occurrences():
    occ = _j(S1 / "FOOTING_OCCURRENCE_REGISTER.json")
    overlap = {h for m in occ["mismatches"] if m["kind"] == "FOOTING_OUTLINES_OVERLAP" for h in m["footings"]}
    shared = occ["summary"]["combined_footings_with_several_columns"]
    out = []
    for r in occ["rows"]:
        o = r["outline"]
        oh = o["handle"].split(":")[0]
        oid = f"FOCC-{oh.split('+')[0]}"
        flags = []
        if any(x.split(":")[-1] == oh for x in overlap):
            flags.append("OUTLINE_OVERLAP_0.14_M2 (S1 FOOTING_OUTLINES_OVERLAP 180F / 180C) - no rebar effect")
        if r["footing_id"] in shared:
            flags.append(f"SEVERAL_COLUMNS {'/'.join(shared[r['footing_id']])}")
        tags = [r["tag"]["handle"]] + [c["handle"] for c in r["competing_tags"]]
        base = {"occurrence_id": oid, "s1_footing_id": r["footing_id"], "drawing_sha": DRAWING_SHA,
                "outline": {"handle": o["handle"], "handles": oh.split("+"), "geometry": o["geometry"],
                            "bbox_mm_frame": o["bbox"], "drawn_L_cm": (r.get("sizes") or {}).get("drawn_L_cm"),
                            "drawn_W_cm": (r.get("sizes") or {}).get("drawn_W_cm")},
                "tag_handles": [h.split(":")[0] for h in tags], "tag_texts": [r["tag"]["text"]] + [
                    c["text"] for c in r["competing_tags"]],
                "columns": r["supported_columns"], "column_types": r["supported_column_types"],
                "sheet_region": "Foundation plan (FP, p.2)"}
        if r["type"] is None:
            out.append(dict(base, mark="F|F10", state=FR.OCC_SOURCE_CONFLICT, candidate_marks=r["candidate_types"],
                            why="one outline holds tags F and F10 (SOURCE_CONFLICT_COMPETING_TAGS_ON_ONE_OUTLINE)",
                            flags=flags + ["SOURCE_CONFLICT F/F10: hypotheses {2 x F, F10, drawn outline}; none "
                                           "enters the accurate BOQ"]))
            continue
        if not r["sizes"]["match"]:
            out.append(dict(base, mark=r["type"], state=FR.OCC_BLOCKED, why="drawn size differs from the schedule",
                            flags=flags))
            continue
        if r["type"] == "F3":
            flags.append("REFERENCE_COUNT_DISAGREEMENT OQ-11 (external reference only; project drawing "
                         "establishes this occurrence) - comparison flag, not a release condition")
        out.append(dict(base, mark=r["type"], state=FR.OCC_ESTABLISHED, flags=flags))
    return out


# ------------------------------------------------------------------ writers
def _csv(path, rows, fields=None):
    buf = io.StringIO()
    fields = fields or list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (list, dict)) else
                        ("" if v is None else (round(v, 6) if isinstance(v, float) else v))) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=float) + "\n",
                    encoding="utf-8")


def main():
    verify_pre_s4()
    R = rules()
    defs = definitions(R)
    occs = occurrences()
    ctx = {"PROJECT_ID": "ALSENAN-ST7757", "DRAWING_ID": "ST7757.dxf", "DRAWING_SHA": DRAWING_SHA,
           "REVISION": "ALSENAN_ST7757_DXF", "ENGINE_COMMIT": f"{BASELINE}+code:{code_digest()[:16]}",
           "REGISTER_VERSION": "FOOTING_REBAR_REGISTER_V1", "CALCULATION_ROUND": "S4",
           "unit_mass": {"method": "D2_OVER_162", "authority": "Urban project default (R3)"}}
    res = FR.run(occs, defs, {k: R[k] for k in ("cover", "direction", "distribution")}, ctx)
    if not res["conservation"]["all_pass"]:
        raise SystemExit(f"conservation failed: {res['conservation']['checks']}")
    _json(HERE / "F3_AUTHORITY_DECISION.json", F3_DECISION)
    occ_by = {o["occurrence_id"]: o for o in occs}
    def_by = {d["mark"]: d for d in defs}
    register = []
    for r in res["occurrences"]:
        o = occ_by[r["occurrence_id"]]
        d = def_by.get(o["mark"])
        register.append(dict(r, s1_footing_id=o["s1_footing_id"], outline=o["outline"], tag_handles=o["tag_handles"],
                             tag_texts=o["tag_texts"], columns=o["columns"], column_types=o["column_types"],
                             schedule_row=None if d is None else {"mark": d["mark"], "insert_handle": d["row_handle"],
                                                                  "L_mm": d["L_mm"], "W_mm": d["W_mm"],
                                                                  "D_mm": d["D_mm"], "layers": d["layers"]}))
    unused = sorted(set(def_by) - {o["mark"] for o in occs})
    _json(HERE / "FOOTING_REBAR_OCCURRENCE_REGISTER.json", {
        "register": "FOOTING_REBAR_OCCURRENCE_REGISTER", "policy": FR.policy_record(), "context": ctx,
        "rules": R, "occurrences": register,
        "schedule_rows_without_occurrence": {m: def_by[m]["schedule_state"] for m in unused}})
    _csv(HERE / "FOOTING_REBAR_OCCURRENCES.csv", [
        {"occurrence_id": r["occurrence_id"], "mark": r["mark"], "occurrence_state": r["occurrence_state"],
         "release_state": r["release_state"], "known_kg": r["known_kg"], "known_length_m": r["known_length_m"],
         "unquantified_components": r["unquantified_components"], "components_by_state": r["components_by_state"],
         "outline": r["outline"]["handle"], "tags": r["tag_handles"], "columns": r["columns"],
         "schedule_row": (r["schedule_row"] or {}).get("insert_handle"), "candidate_marks": r["candidate_marks"],
         "flags": r["flags"]} for r in register])
    comp_fields = ["occurrence_id", "mark", "component", "accurate_component", "state", "dia_mm", "count_mode",
                   "count", "count_convention", "raw_span_mm", "cover_1_mm", "cover_2_mm", "net_straight_mm",
                   "bar_length_m", "total_length_m", "kg_per_m", "kg", "end_treatment", "missing", "question_id",
                   "raw_value", "candidates", "why"]
    _csv(HERE / "FOOTING_REBAR_COMPONENTS.csv", res["components"], comp_fields)
    _csv(HERE / "FOOTING_BBS_NET.csv", res["bbs"])
    unresolved = [c for c in res["components"] if c["state"] in ("BLOCKED_UNQUANTIFIED", "BLOCKED_MODELLED")
                  or c["state"] == "LOWER_BOUND"]
    _csv(HERE / "FOOTING_REBAR_UNRESOLVED.csv", [
        {"occurrence_id": c["occurrence_id"], "mark": c["mark"], "component": c["component"], "state": c["state"],
         "what_is_missing": c.get("missing") or c["why"], "question_id": c.get("question_id") or (
             QUESTION_BOXED if c["component"] == FR.BOXED else ""),
         "raw_value": c.get("raw_value"), "candidates": c.get("candidates"),
         "known_kg": c["kg"]} for c in unresolved])
    with open(HERE / "FOOTING_REBAR_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for p in sorted(res["parts"], key=lambda z: z["part_id"]):
            f.write(json.dumps({"part_id": p["part_id"], "state": p["state"], "kg": p["kg"],
                                "provenance": p["provenance"]}, sort_keys=True, ensure_ascii=False) + "\n")
    flags = []
    for r in register:
        for fl in r["flags"]:
            flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "occurrence_id": r["occurrence_id"],
                          "mark": r["mark"], "flag": fl,
                          "effect_on_release": ("BLOCKS_OCCURRENCE" if fl.startswith("SOURCE_CONFLICT") else
                                                "NONE (comparison / information)")})
    for m in ("F8", "F12", "F13", "F14", "FF"):
        flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "occurrence_id": "", "mark": m,
                      "flag": "OQ-4 open (donor audit): do two-layer footings carry boxed bars? The schedule BOXED "
                              "column holds TOP/BOT labels for this row (pre-S4 03) -> BOXED NOT_APPLICABLE",
                      "effect_on_release": "NONE until answered"})
    for m, st in sorted({m: def_by[m]["schedule_state"] for m in unused}.items()):
        flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "occurrence_id": "", "mark": m,
                      "flag": f"schedule row with no own plan occurrence ({st}) - no rebar is created from a schedule "
                              "row", "effect_on_release": "NONE"})
    _csv(HERE / "FOOTING_REBAR_ENGINEERING_FLAGS.csv", flags)
    s = res["summary"]
    dia = Counter()
    dia_len = Counter()
    for c in res["components"]:
        if c["kg"] is not None:
            dia[c["dia_mm"]] += c["kg"]
            dia_len[c["dia_mm"]] += c["total_length_m"]
    s.update(conservation=res["conservation"], context=ctx,
             diameter_distribution={str(k): {"kg": dia[k], "length_m": dia_len[k]} for k in sorted(dia)},
             total_source_derived_length_m=sum(dia_len.values()),
             provenance={"parts": len(res["parts"]), "validated": len(res["parts"]),
                         "fields": "accurate_boq_rebar.S4_PROVENANCE_FIELDS (+ bounds on lower-bound parts)"},
             f3_authority=F3_DECISION["decision"], schedule_rows_without_occurrence=unused,
             questions_open=[QUESTION_BOXED, QUESTION_FF_SIDE, "OQ-4"])
    _json(HERE / "FOOTING_REBAR_RELEASE_SUMMARY.json", s)
    manifest = {"round": "S4", "baseline": BASELINE, "state": "FROZEN_BEFORE_ANY_REFERENCE_COMPARISON",
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "engine_commit_stamp": ctx["ENGINE_COMMIT"],
                "references_read_before_freeze": [],
                "rule": "the post-freeze comparison script refuses to run unless every hash above still matches; a "
                        "correction found by the comparison needs a new issue, new evidence, a new regression and a "
                        "new version - never an edit of these outputs"}
    _json(HERE / "S4_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: s[k] for k in ("verified_kg", "lower_bound_known_kg", "provisional_kg",
                                        "blocked_modelled_kg", "blocked_unquantified_component_count",
                                        "occurrences_by_release", "final_footing_rebar")}, indent=1, default=float))


if __name__ == "__main__":
    main()
