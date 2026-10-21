"""Alsenan structural census, Round S1: SOURCE RULES + OCCURRENCE CENSUS (no rebar quantities).

Builds the S1 registers from ST7757.dxf (+ the ST7757.pdf rule pages already transcribed in rules_s1.RULES) and writes
them, with an INDEX, into this folder.

    python research/alsenan_structural_census_s1/build_census_s1.py [--twice]

Firewall: this runner reads only the ST7757 drawing (DXF + the rule transcription). It never opens a benchmark, a
human or freelancer quantity, a kg/m3 allowance or an earlier rebar register. Nothing here computes a bar length or a
weight: S1 stops at occurrences, definitions and the rules that will later govern them.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "external_engine_lab"))
sys.path.insert(0, str(HERE))

from engine.source import structural_census as SC  # noqa: E402
import alsenan_structural_s1 as S  # noqa: E402
import rules_s1  # noqa: E402

ROUND = "S1"
OUT = HERE
FROZEN_BEFORE_BENCHMARK = True  # the census is written before any benchmark / human total is read (none is read here)

SLAB_SHEETS = ("GFRS", "FFRS", "SFRS")
BEAM_FLOOR = {"GFRS": "GF_ROOF", "FFRS": "1F_ROOF", "SFRS": "2F_ROOF", "GBP": "GROUND_BEAMS", "FP": "FOUNDATION"}
SLAB_FLOOR = {"GFRS": "GF_ROOF_SLAB", "FFRS": "1F_ROOF_SLAB", "SFRS": "2F_ROOF_SLAB", "GBP": "GROUND_SLAB_SOG"}
BAND_STOREY = {"FOU": "FOUNDATION", "GR": "GF", "1ST": "1F", "2ND": "2F"}
REGISTERS = [
    "STRUCTURAL_PROJECT_RULE_REGISTER", "STRUCTURAL_LEVEL_REGISTER", "COLUMN_OCCURRENCE_REGISTER",
    "COLUMN_TYPE_FLOOR_MATRIX", "COLUMN_VERTICAL_CHAIN_REGISTER", "COLUMN_DEFINITION_REGISTER",
    "COLUMN_TIE_TOPOLOGY_RULES", "FOOTING_OCCURRENCE_REGISTER", "FOOTING_DEFINITION_REGISTER",
    "FOOTING_REQUIRED_COMPONENT_REGISTER", "BEAM_OCCURRENCE_REGISTER", "BEAM_TYPE_FLOOR_MATRIX",
    "BEAM_DEFINITION_REGISTER", "CONTINUOUS_BEAM_OCCURRENCE_REGISTER", "SLAB_PANEL_REGISTER",
    "SLAB_REBAR_SOURCE_REGISTER", "SLAB_RULE_APPLICATION_MAP", "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER",
    "POOL_STRUCTURAL_REGISTER", "STRUCTURAL_OCCURRENCE_CONSERVATION_REGISTER", "STRUCTURAL_REVIEW_QUEUE"]


# ============================================================================================ serialisation
def clean(o):
    """JSON-safe, deterministic: numpy scalars -> python, floats rounded to 3 dp, tuples -> lists."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        o = o.item()
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            return None
        r = round(o, 3)
        return 0.0 if r == 0 else r
    return o


def dumps(obj):
    return json.dumps(clean(obj), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def register(name, rows, summary=None, **extra):
    return {"register": name, "round": ROUND, "policy": SC.policy_record(),
            "source": {"drawing": S.DRAWING, "dxf_sha256": None, "pdf": S.PDF, "pdf_sha256": S.PDF_SHA},
            "frozen_before_benchmark": FROZEN_BEFORE_BENCHMARK, "summary": summary or {}, "rows": rows, **extra}


def _sk(s):
    return {k: s.get(k) for k in ("support_kind", "kind", "ref") if s and k in s} | (
        {"refs": [{"kind": r.get("kind"), "ref": r.get("ref"), "relation": r.get("relation")} for r in s.get("refs", [])]}
        if s and s.get("refs") else {})


RULE = {r["rule_id"]: r for r in rules_s1.RULES}


# ============================================================================================ 1-2 rules, levels
def rule_register():
    rows = rules_s1.RULES
    return register("STRUCTURAL_PROJECT_RULE_REGISTER", rows, {
        "rules": len(rows), "by_status": dict(Counter(r["status"] for r in rows)),
        "by_topic": dict(Counter(r["topic"] or "UNSPECIFIED" for r in rows)),
        "slab_thickness_precedence": list(SC.PRECEDENCE),
        "source_conflicts": [r["rule_id"] for r in rows if r["status"] == "SOURCE_CONFLICT"],
        "blocked_methods": [r["rule_id"] for r in rows if r["status"] == "BLOCKED_METHOD"]})


def level_register(B):
    LV = B["levels"]
    return register("STRUCTURAL_LEVEL_REGISTER", LV["levels"], {
        "storey_intervals": {i["storey"]: i.get("floor_to_floor_m") for i in LV["intervals"]},
        "kept_separate": ["floor_to_floor_m", "column_clear_height_m", "main_bar_length_m", "tie_zone_length_m"],
        "lift_tie_beam_required_at": [c["storey"] for c in LV["lift_tie_beam_rule_check"] if c["required"]]},
        intervals=LV["intervals"], printed_marks=LV["printed_marks"],
        lift_tie_beam_rule_check=LV["lift_tie_beam_rule_check"])


# ============================================================================================ 3-7 columns
def column_registers(B):
    CR, C = B["CR"], B["C"]
    occ = CR["occurrences"]
    # 3 occurrences
    dup = [k for k, n in Counter(r["column_id"] for r in occ).items() if n > 1]
    occ_reg = register("COLUMN_OCCURRENCE_REGISTER", occ, {
        "occurrences": len(occ), "physical_positions": len(CR["chains"]),
        "by_floor": dict(Counter(r["floor"] for r in occ)),
        "by_status": dict(Counter(r["status"] for r in occ)),
        "by_terminal_state": dict(Counter(r["terminal_state"] for r in occ)),
        "drawn_vs_schedule_mismatch_by_floor": dict(Counter(r["floor"] for r in occ
                                                            if r["drawn_vs_schedule"] == "MISMATCH")),
        "duplicate_column_ids": dup, "schedule_rows_create_no_occurrence": True})
    # 4 matrix
    types = sorted({r["column_type"] or "UNTYPED" for r in occ}, key=lambda t: (len(t) > 1 and t[1:].isdigit(), _natkey(t)))
    mat = {t: {f: 0 for f in S.FLOORS} for t in types}
    for r in occ:
        mat[r["column_type"] or "UNTYPED"][r["floor"]] += 1
    rows = [{"column_type": t, **mat[t], "total": sum(mat[t].values())} for t in types]
    totals = {f: sum(m[f] for m in mat.values()) for f in S.FLOORS}
    mat_reg = register("COLUMN_TYPE_FLOOR_MATRIX", rows, {"floor_totals": totals, "grand_total": sum(totals.values()),
                                                         "floors": S.FLOORS,
                                                         "type_conflicts": [c["chain_id"] for c in CR["chains"]
                                                                            if c["type_authority"] == "TAG_CONFLICT"]})
    # 5 chains + hard invariant: every outline of every plan is a member of exactly one chain
    member_count = Counter()
    for ch in CR["chains"]:
        for sh, h in ch["members_by_sheet"].items():
            member_count[(sh, h)] += 1
        for sh, h in ch["transition_outlines"].items():
            member_count[(sh, h)] += 1
    inv = []
    for sh in S.CHAIN_SHEETS:
        for o in C["outlines"][sh]:
            n = member_count.get((sh, o["handle"]), 0)
            if n != 1:
                inv.append({"sheet": sh, "handle": o["handle"], "chains": n})
    chain_reg = register("COLUMN_VERTICAL_CHAIN_REGISTER", CR["chains"], {
        "chains": len(CR["chains"]),
        "starts_at": dict(Counter(c["starts_at"] for c in CR["chains"])),
        "terminates_at": dict(Counter(c["terminates_at"] for c in CR["chains"])),
        "planted": [c["chain_id"] for c in CR["chains"] if c["planted_on"]],
        "type_changes": [c["chain_id"] for c in CR["chains"] if c["changes_type_at"]],
        "events": dict(Counter(e["event"] for c in CR["chains"] for e in c["events"])),
        "outlines_per_sheet": {sh: len(C["outlines"][sh]) for sh in S.CHAIN_SHEETS},
        "hard_invariant_every_outline_in_exactly_one_chain": {"violations": inv, "state": "PASS" if not inv else "FAIL"},
        "labels": CR["labels"]})
    # 6 definitions (type x storey band)
    occ_by = Counter((r["column_type"], r["floor"]) for r in occ)
    drows = []
    ties = {b["band_id"]: b for b in B["ties"]["bands"]}
    for t, d in sorted(CR["definitions"].items(), key=lambda kv: _natkey(kv[0])):
        bands = d["fields"]["bands"]
        for key, storey in BAND_STOREY.items():
            b = bands.get(key)
            n_occ = occ_by.get((t, storey), 0)
            if not b:
                drows.append({"definition_id": f"CDEF-{t}-{storey}", "column_type": t, "storey_band": storey,
                              "schedule_band_key": key, "state": "NO_BAND_IN_SCHEDULE" if not n_occ else
                              "OCCURRENCE_WITHOUT_SCHEDULE_BAND", "plan_occurrences": n_occ,
                              "source_row": {"block": d["block"], "insert_handle": d["insert_handle"], "page": d["page"]}})
                continue
            L, T = max(b["B_cm"], b["H_cm"]), min(b["B_cm"], b["H_cm"])
            tb = SC.tie_band(L, S.TIE_BANDS)
            drows.append({"definition_id": f"CDEF-{t}-{storey}", "column_type": t, "storey_band": storey,
                          "schedule_band_key": key, "B_cm": b["B_cm"], "D_cm": b["H_cm"], "L_cm": L, "T_cm": T,
                          "longitudinal_bars": {"count": b["bars"].get("count"), "dia_mm": b["bars"].get("dia_mm"),
                                                "raw": b["bars"].get("raw")},
                          "tie_rule": {"rule_id": "P9-COL-TIES", "dia_mm": 8, "per_m": 6,
                                       "per_metre_semantics": "BLOCKED_METHOD (tie set vs single tie not stated)"},
                          "link_topology": {"state": tb["state"], "band": tb["band"],
                                            "closed_ties_per_set": ties[tb["band"]]["closed_ties_in_section"]
                                            if tb["band"] in ties else None,
                                            "bars_drawn_in_detail": ties[tb["band"]]["bars_drawn"] if tb["band"] in ties
                                            else None,
                                            "bars_in_schedule_vs_detail": None if tb["band"] not in ties else (
                                                "SAME" if b["bars"].get("count") == ties[tb["band"]]["bars_drawn"]
                                                else "DIFFERENT_COUNT_DISTRIBUTION_BLOCKED")},
                          "plan_occurrences": n_occ,
                          "state": "DEFINED" if n_occ else "DEFINED_NO_PLAN_OCCURRENCE",
                          "source_row": {"block": d["block"], "insert_handle": d["insert_handle"], "page": d["page"],
                                         "raw_attributes": {k: v for k, v in d["raw_attributes"].items()
                                                            if k.startswith(key + ".")}}})
    cn = CR["cn_row"]
    if cn:
        tb = SC.tie_band(max(cn["B_cm"], cn["D_cm"]), S.TIE_BANDS)
        drows.append({"definition_id": "CDEF-CN-FOUNDATION", "column_type": "CN", "storey_band": "FOUNDATION",
                      "schedule_band_key": "FOU (loose texts, not a CGT block row)", "B_cm": cn["B_cm"],
                      "D_cm": cn["D_cm"], "L_cm": max(cn["B_cm"], cn["D_cm"]), "T_cm": min(cn["B_cm"], cn["D_cm"]),
                      "longitudinal_bars": {"count": cn["bars"], "dia_mm": cn["dia_mm"], "raw": cn["raw"]},
                      "tie_rule": {"rule_id": "P9-COL-TIES", "dia_mm": 8, "per_m": 6},
                      "link_topology": {"state": tb["state"], "band": tb["band"]},
                      "plan_occurrences": occ_by.get(("CN", "FOUNDATION"), 0), "state": "DEFINED",
                      "other_bands": cn["other_bands"], "source_row": {"handles": cn["handles"], "page": 9}})
    for ch in CR["chains"]:
        for lb in ch["labels"]:
            if not lb["label"].startswith(("P.C", "P/C")):
                continue
            prow = [r for r in occ if r["chain_id"] == ch["chain_id"]]
            for r in prow:
                band = r["schedule_section_cm"]
                tb = SC.tie_band(max(band), S.TIE_BANDS) if band else {"state": "BLOCKED", "band": None}
                drows.append({"definition_id": f"CDEF-P.C-{ch['chain_id']}-{r['floor']}", "column_type": "P.C",
                              "storey_band": r["floor"], "schedule_band_key": "PLAN_LABEL (no schedule row)",
                              "B_cm": band[0] if band else None, "D_cm": band[1] if band else None,
                              "longitudinal_bars": r["longitudinal_bars"],
                              "tie_rule": {"rule_id": "P9-COL-TIES", "applicability_to_planted": "UNRESOLVED"},
                              "link_topology": {"state": tb["state"], "band": tb["band"]}, "plan_occurrences": 1,
                              "state": "DEFINED_BY_PLAN_LABEL" if r["definition_state"] == "FULL" else "PARTIAL",
                              "source_row": {"label_handle": lb["handle"], "sheet": lb["sheet"], "text": lb["text"]}})
    def_reg = register("COLUMN_DEFINITION_REGISTER", drows, {
        "definitions": len(drows), "by_state": dict(Counter(r["state"] for r in drows)),
        "schedule_types": sorted(CR["definitions"], key=_natkey),
        "occurrences_without_band": [r["definition_id"] for r in drows
                                     if r["state"] == "OCCURRENCE_WITHOUT_SCHEDULE_BAND"]})
    # 7 tie topology
    pop = Counter((r["tie_topology_band"]["state"], r["tie_topology_band"]["band"] if
                   isinstance(r["tie_topology_band"]["band"], (str, type(None))) else "+".join(r["tie_topology_band"]["band"]))
                  for r in occ)
    gap_rows = [{"column_id": r["column_id"], "L_cm": max(r["schedule_section_cm"]) if r["schedule_section_cm"] else None}
                for r in occ if r["tie_topology_band"]["state"] in ("BOUNDARY_GAP", "OUT_OF_RANGE")]
    tmin = [{"column_id": r["column_id"], **r["min_thickness_check"]} for r in occ
            if r["min_thickness_check"] and r["min_thickness_check"]["state"] != "PASS"]
    tie_reg = register("COLUMN_TIE_TOPOLOGY_RULES", B["ties"]["bands"], {
        "bands": [b["band_id"] for b in B["ties"]["bands"]],
        "population_by_band": {f"{k[0]}:{k[1]}": v for k, v in sorted(pop.items(), key=str)},
        "boundary_gap_or_out_of_range": gap_rows, "min_thickness_findings": tmin,
        "no_weight_calculated": True},
        ties_rule=B["ties"]["ties_rule"], L_definition=B["ties"]["L_definition"], gaps=B["ties"]["gaps"],
        min_thickness_table=S.MIN_T_TABLE, band_limits=S.TIE_BANDS,
        detail_reading=B["ties"].get("state"),
        open_questions=[
            "6Ø8/m: is the count per metre a count of tie SETS (all closed ties of the band at one level) or of "
            "single closed ties?",
            "L = 80 cm (C7 30x80) sits on the printed limit of both bands (50<L<80, 80<L<120): band 2 (2 ties) or "
            "band 3 (3 ties)?",
            "Tie sizes: take each tie's span from the drawn fractions of L (0.607 / 0.761 / 0.757 / 0.222) or from "
            "the bar positions (tie around bars i..j)?",
            "When the schedule bar count differs from the detail sketch (e.g. 10 bars in band 2, sketch shows 8), "
            "which bars does each overlapping tie enclose?",
            "Do planted (P.C) and turn (T.C) columns use the same tie bands (T.C extras: P15-TWISTED spiral)?",
            "Do ties continue through the beam-column joint (tie zone = floor-to-floor) or stop at the beam soffit "
            "(tie zone = clear height)?"])
    return occ_reg, mat_reg, chain_reg, def_reg, tie_reg


def _natkey(t):
    t = t or ""
    m = re.match(r"([A-Za-z./]*)(\d*)(.*)", t)
    return (m.group(1), int(m.group(2)) if m.group(2) else -1, m.group(3))


# ============================================================================================ 8-10 footings
def footing_registers(B):
    FT = B["footings"]
    rows = FT["rows"] + FT["tag_only"]
    CR = B["CR"]
    found_chains = [c for c in CR["chains"] if "FOUNDATION" in c["continues_through"]]
    col_f = FT["col_to_footing"]
    mism = list(FT["mismatches"])
    for c in found_chains:
        n = len(col_f.get(c["chain_id"], []))
        if n == 0:
            mism.append({"kind": "COLUMN_WITHOUT_FOOTING", "column": c["chain_id"], "type": c["column_type"]})
        elif n > 1:
            mism.append({"kind": "COLUMN_IN_SEVERAL_FOOTINGS", "column": c["chain_id"], "footings": col_f[c["chain_id"]]})
    for r in rows:
        if not r.get("supported_columns"):
            mism.append({"kind": "FOOTING_WITHOUT_COLUMN", "footing": r["footing_id"], "type": r["type"]})
        if r.get("competing_tags"):
            mism.append({"kind": "CONFLICTING_TAG", "footing": r["footing_id"], "candidate_types": r["candidate_types"]})
        for i in r.get("issues", []):
            if i.startswith("TAG_COLUMN_"):
                mism.append({"kind": "TAG_COLUMN_PART_DISAGREES", "footing": r["footing_id"], "detail": i})
    shared = [r for r in rows if len(r.get("supported_columns") or []) > 1]
    by_type = Counter(r["type"] or "CONFLICT(" + "/".join(r["candidate_types"] or []) + ")" for r in rows)
    occ_reg = register("FOOTING_OCCURRENCE_REGISTER", rows, {
        "outlines": len(FT["rows"]), "tag_only": len(FT["tag_only"]),
        "by_type": dict(sorted(by_type.items(), key=lambda kv: _natkey(kv[0]))),
        "by_terminal_state": dict(Counter(r["terminal_state"] for r in rows)),
        "combined_footings_with_several_columns": {r["footing_id"]: r["supported_column_types"] for r in shared},
        "mismatch_counts": dict(Counter(m["kind"] for m in mism)),
        "foundation_column_positions": len(found_chains)},
        mismatches=mism, column_to_footing=col_f)
    # 9 definitions
    used = Counter(r["type"] for r in rows if r["type"])
    for r in rows:
        for t in r.get("candidate_types") or []:
            used[t + "?"] += 1
    drows = []
    for t, d in sorted(FT["definitions"].items(), key=lambda kv: _natkey(kv[0])):
        f = d["fields"]
        if d["element"] == "FOOTING":
            comps = [{"component": "BOTTOM_SHORT", "layer": "SINGLE", "count_mode": "ABSOLUTE_COUNT",
                      "count": f["short_bars"].get("count"), "dia_mm": f["short_bars"].get("dia_mm")},
                     {"component": "BOTTOM_LONG", "layer": "SINGLE", "count_mode": "ABSOLUTE_COUNT",
                      "count": f["long_bars"].get("count"), "dia_mm": f["long_bars"].get("dia_mm")}]
            boxed = f.get("boxed", {})
        else:
            comps = [{"component": f"{lay}_{side}", "layer": lay, "count_mode": "BARS_PER_METRE",
                      "count": f[f"{lay}_{side}"].get("count"), "dia_mm": f[f"{lay}_{side}"].get("dia_mm")}
                     for lay in ("TOP", "BOTTOM") for side in ("short", "long")]
            boxed = {"raw_boxed_value": None, "interpretation": "NOT_A_FIELD (BOXED-T/B are the layer labels TOP/BOT)"}
        n = used.get(t, 0)
        drows.append({"definition_id": f"FDEF-{t}", "footing_type": t, "element": d["element"],
                      "L_cm": f["L_cm"], "W_cm": f["W_cm"], "D_cm": f["D_cm"], "components": comps,
                      "boxed": boxed, "remarks": d.get("notes") or [],
                      "plan_occurrences": n, "conflict_candidate_occurrences": used.get(t + "?", 0),
                      "state": "DEFINED" if n else ("DEFINED_CONFLICT_CANDIDATE_ONLY" if used.get(t + "?") else
                                                    "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE"),
                      "source_row": {"block": d["block"], "insert_handle": d["insert_handle"], "page": d["page"],
                                     "raw_attributes": d["raw_attributes"]}})
    def_reg = register("FOOTING_DEFINITION_REGISTER", drows, {
        "definitions": len(drows), "by_element": dict(Counter(r["element"] for r in drows)),
        "without_plan_occurrence": [r["footing_type"] for r in drows
                                    if r["state"] == "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE"],
        "boxed_values": {r["footing_type"]: r["boxed"].get("raw_boxed_value") for r in drows
                         if r["element"] == "FOOTING"}})
    # 10 required components
    crows = []
    for r in drows:
        t = r["footing_type"]
        base = {"footing_type": t, "plan_occurrences": r["plan_occurrences"]}
        for c in r["components"]:
            crows.append({**base, "component_id": f"FCOMP-{t}-{c['component']}", "component": c["component"],
                          "required": True, "definition": c, "state": "DEFINED", "rule": "schedule row"})
        if r["element"] == "FOOTING":
            raw = (r["boxed"] or {}).get("raw_boxed_value")
            crows.append({**base, "component_id": f"FCOMP-{t}-BOXED", "component": "BOXED",
                          "BOXED_REQUIRED": bool(raw), "BOXED_RAW": raw or None,
                          "BOXED_SEMANTICS": "BLOCKED" if raw else "NOT_PRINTED",
                          "state": "BLOCKED" if raw else "NOT_REQUIRED_BY_SOURCE", "rule": "P13-FOOTING-TYP"})
        crows.append({**base, "component_id": f"FCOMP-{t}-STARTERS", "component": "COLUMN_STARTERS",
                      "required": r["plan_occurrences"] > 0, "rule": "P13-FOOTING-TYP (40D projection, foot >= 30 cm)",
                      "definition": {"bars": "= column bars of each supported column (FOUNDATION band)",
                                     "projection": "40D (CANDIDATE)", "foot_min_cm": 30},
                      "state": "DEFINED_BY_RULE_CANDIDATE"})
        if t == "FF":
            crows.append({**base, "component_id": "FCOMP-FF-LIFT_PIT_WALLS", "component": "LIFT_PIT_WALLS",
                          "required": True, "rule": "P14-LIFT", "definition": {"wall_mm": 200,
                                                                              "bars": ["6Ø12/m", "6Ø16/m"],
                                                                              "pit_depth": "BLOCKED (manufacturer)"},
                          "state": "BLOCKED"})
    crows.append({"footing_type": "ALL", "component_id": "FCOMP-ALL-DEEP_LOWER_GB", "component": "LOWER_GROUND_BEAM",
                  "required": "UNRESOLVED", "rule": "P13-FOOTING-DEEP",
                  "condition": "(upper GB level - footing level) > 2.5 m", "founding_level": "BLOCKED",
                  "state": "BLOCKED"})
    crows.append({"footing_type": "CN", "component_id": "FCOMP-CN-NECK", "component": "NECK_COLUMN_CN",
                  "required": True, "rule": "CN schedule row (FOUNDATION band only)",
                  "definition": "see COLUMN_DEFINITION_REGISTER CDEF-CN-FOUNDATION", "state": "DEFINED"})
    comp_reg = register("FOOTING_REQUIRED_COMPONENT_REGISTER", crows, {
        "components": len(crows), "by_state": dict(Counter(r["state"] for r in crows)),
        "boxed_required_types": [r["footing_type"] for r in crows if r.get("BOXED_REQUIRED")]})
    return occ_reg, def_reg, comp_reg


# ============================================================================================ 11-14 beams
def beam_registers(B, src):
    BS, defs = B["beams"], B["defs"]
    sdefs = {}
    for d in defs["definitions"]:
        if d["element"] in ("SIMPLE_BEAM", "STRAP_BEAM", "CONTINUOUS_BEAM"):
            sdefs.setdefault(d["type"], []).append(d)
    conflict_keys = {c["key"] for c in defs["conflicts"]}
    cb_state = {}
    for c in B["cb"]:
        for t in c["tags"]:
            cb_state[(c["sheet"], t["handle"])] = c
    stair_quals = []
    for sh in SLAB_SHEETS:
        for t in src.texts(sh, None):
            if "WITH STAIR" in t["text"].upper():
                near = sorted((math.dist(o["tag_position_mm"], t["p"]), o["tag_handle"]) for o in BS[sh]["occurrences"])
                stair_quals.append({"sheet": sh, "qualifier_handle": t["handle"], "tag_handle": near[0][1]
                                    if near and near[0][0] < 900 else None, "distance_mm": near[0][0] if near else None})
    stair_tag = {(q["sheet"], q["tag_handle"]): q for q in stair_quals if q["tag_handle"]}
    rows = []
    for sh in SLAB_SHEETS:
        for o in BS[sh]["occurrences"]:
            fam = {"SIMPLE_BEAM": "SIMPLE", "CONTINUOUS_BEAM": "CB", "CANTILEVER_BEAM": "CANTILEVER"}.get(o["family"],
                                                                                                    "OTHER")
            issues, status = [], "COUNTED"
            q = stair_tag.get((sh, o["tag_handle"]))
            if q:
                fam = "STAIR"
            d = sdefs.get(o["tag"], [])
            if not d:
                issues.append("TAG_WITHOUT_SCHEDULE_DEFINITION")
            if o["tag"] in conflict_keys:
                issues.append("SCHEDULE_KEY_CONFLICT")
            if o["binding"] != "BOUND":
                b = BS[sh]["binding"].get(o["tag_handle"], {})
                issues.append("TAG_MEMBER_AMBIGUOUS")
                status = "BLOCKED"
                term = "COUNTED_BLOCKED"
                cand = b.get("candidates")
            else:
                cand = None
                if o.get("same_span_conflict"):
                    issues.append("SAME_SPAN_CARRIES_TWO_TAGS")
                if d and len(d) == 1 and o.get("width_drawn_mm") and d[0]["fields"].get("B_cm") and \
                        abs(o["width_drawn_mm"] - 10 * d[0]["fields"]["B_cm"]) > 25:
                    issues.append("DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE")
                if fam == "CB":
                    c = cb_state.get((sh, o["tag_handle"]))
                    if c and c["match_state"] != "MATCH_CONFIRMED":
                        issues.append("CB_" + c["match_state"])
                if any(s in issues for s in ("SAME_SPAN_CARRIES_TWO_TAGS", "DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE",
                                              "SCHEDULE_KEY_CONFLICT")) or any(i.startswith("CB_") for i in issues):
                    status = "SOURCE_CONFLICT"
                if not d:
                    term = "COUNTED_BLOCKED"
                    status = "UNRESOLVED"
                else:
                    term = "COUNTED_AND_DEFINED" if status == "COUNTED" else "COUNTED_DEFINITION_PARTIAL"
            sp = o.get("span") or {}
            rows.append({"beam_id": f"BM-{BEAM_FLOOR[sh]}-{o['tag']}-{o.get('member') or 'UNBOUND'}-{o['tag_handle']}",
                         "source_id": f"BEAMTAG:{sh}:{o['tag_handle']}", "floor": BEAM_FLOOR[sh], "sheet": sh,
                         "family": fam, "beam_type": o["tag"], "tag_handle": o["tag_handle"],
                         "tag_position_mm": o["tag_position_mm"], "binding": o["binding"], "member": o.get("member"),
                         "member_candidates": cand, "member_kind": o.get("member_kind"),
                         "width_drawn_mm": o.get("width_drawn_mm"),
                         "schedule_B_cm": d[0]["fields"].get("B_cm") if len(d) == 1 else None,
                         "orientation_deg": o.get("orientation_deg"),
                         "start_support": _sk(o.get("start_support")), "end_support": _sk(o.get("end_support")),
                         "span_stations_mm": [sp.get("s0"), sp.get("s1")] if sp else None,
                         "support_centreline_length_m": o.get("support_centreline_length_m"),
                         "clear_length_m": o.get("clear_length_m"), "drawn_length_m": o.get("drawn_length_m"),
                         "bands": o.get("bands"), "stair_qualifier": q, "issues": issues, "status": status,
                         "terminal_state": term})
        # untagged members
        dome_txt = [t["p"] for t in src.texts(sh, None) if t["text"].strip().upper() == "SEE DETAIL"]
        for u in BS[sh]["untagged"]:
            is_arc = u["member"].startswith("BA")
            near_dome = is_arc and dome_txt and any(math.dist(_arc_centre(BS[sh], u["member"]), p) < 3500
                                                    for p in dome_txt)
            sp = u.get("span") or {}
            key = f"{u['member']}-{sp.get('s0', 0):.0f}" if sp else u["member"]
            rows.append({"beam_id": f"BM-{BEAM_FLOOR[sh]}-UNTAGGED-{key}", "source_id": f"MEMBER:{sh}:{key}",
                         "floor": BEAM_FLOOR[sh], "sheet": sh,
                         "family": "DOME_RING" if near_dome else "OTHER", "beam_type": None, "tag_handle": None,
                         "binding": "NO_TAG", "member": u["member"], "member_kind": "ARC" if is_arc else "STRAIGHT",
                         "width_drawn_mm": u.get("width_drawn_mm"),
                         "start_support": _sk(sp.get("start")), "end_support": _sk(sp.get("end")),
                         "span_stations_mm": [sp.get("s0"), sp.get("s1")] if sp else None,
                         "support_centreline_length_m": u.get("support_centreline_length_m"),
                         "clear_length_m": u.get("clear_length_m"), "drawn_length_m": u.get("drawn_length_m"),
                         "bands": u.get("bands"),
                         "issues": ["MEMBER_WITH_NO_TAG"] + (["DOME_RING_BEAM_CANDIDATE (P7-DOME)"] if near_dome else []),
                         "status": "UNRESOLVED",
                         "terminal_state": "COUNTED_DEFINITION_PARTIAL" if near_dome else "COUNTED_BLOCKED"})
    # straps (FP)
    for s in B["straps"]:
        d = sdefs.get(s["tag"], [])
        conflict = s["tag"] in conflict_keys
        issues = (["SCHEDULE_KEY_CONFLICT"] if conflict else []) + (
            ["DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE"] if len(d) == 1 and abs(s["drawn_width_mm"] - 10 * d[0]["fields"]["B_cm"]) > 25
            else [])
        rows.append({"beam_id": f"BM-FOUNDATION-{s['tag']}-{s['band']['band_id']}",
                     "source_id": f"STRAP:FP:{s['band']['band_id']}", "floor": "FOUNDATION", "sheet": "FP",
                     "family": "STRAP", "beam_type": s["tag"], "tag_handle": s["tag_handle"], "binding": "BOUND",
                     "width_drawn_mm": s["drawn_width_mm"],
                     "schedule_B_cm": [x["fields"]["B_cm"] for x in d],
                     "drawn_length_m": s["drawn_length_m"], "edges": s["band"]["edges"],
                     "drawn_width_matches": [x["fields"]["B_cm"] for x in d if abs(s["drawn_width_mm"] - 10 * x["fields"]["B_cm"]) <= 25],
                     "issues": issues, "status": "SOURCE_CONFLICT" if issues else "COUNTED",
                     "terminal_state": "COUNTED_DEFINITION_PARTIAL" if issues else "COUNTED_AND_DEFINED"})
    # ground beams (GBP)
    for g in B["ground_beams"]:
        ext = g["exterior"]
        fam = "EXTERIOR_GB" if ext == "EXTERIOR_CANDIDATE" else "GB"
        rows.append({"beam_id": f"BM-GROUND_BEAMS-{g['gb_id']}", "source_id": f"GBSPAN:GBP:{g['gb_id']}",
                     "floor": "GROUND_BEAMS", "sheet": "GBP", "family": fam, "beam_type": g["category_cc"],
                     "category_clear_basis": g["category_clear"], "category_state": g["category_state"],
                     "exterior_state": ext, "member": g["member"], "member_kind": g["kind"],
                     "width_drawn_mm": g["width_drawn_mm"], "orientation_deg": g.get("orientation_deg"),
                     "start_support": g.get("start_support"), "end_support": g.get("end_support"),
                     "support_centreline_length_m": g["support_centreline_length_m"],
                     "clear_length_m": g["clear_length_m"], "drawn_length_m": g["drawn_length_m"],
                     "issues": [i for i in (g["category_state"] if g["category_state"] != "CATEGORY_BY_LENGTH" else None,
                                            "EXTERIOR_BY_GEOMETRY_CANDIDATE" if ext == "EXTERIOR_CANDIDATE" else None) if i],
                     "status": "PROVISIONAL", "terminal_state": g["terminal_state"]})
    # populations with no plan member
    lift_req = [c for c in B["levels"]["lift_tie_beam_rule_check"] if c["required"]]
    for c in lift_req:
        rows.append({"beam_id": f"BM-{c['storey']}-LIFT_TIE", "source_id": f"RULE:P8-N19:{c['storey']}",
                     "floor": c["storey"], "family": "LIFT_TIE", "beam_type": None,
                     "required_by": c["rule"], "drawn": False, "issues": ["REQUIRED_BY_RULE_NOT_DRAWN"],
                     "status": "BLOCKED", "terminal_state": "COUNTED_BLOCKED"})
    rows.append({"beam_id": "BM-ALL-LINTEL-POPULATION", "source_id": "RULE:P13-LINTEL", "floor": "ALL",
                 "family": "LINTEL", "beam_type": "by opening width (p.13)", "drawn": False,
                 "issues": ["OCCURRENCES_COME_FROM_ARCHITECTURAL_OPENINGS"], "status": "BLOCKED",
                 "terminal_state": "COUNTED_BLOCKED"})
    by_fam = Counter(r["family"] for r in rows)
    occ_reg = register("BEAM_OCCURRENCE_REGISTER", rows, {
        "rows": len(rows), "by_family": dict(by_fam),
        "by_floor_family": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["floor"], r["family"]) for r in rows).items())},
        "by_terminal_state": dict(Counter(r["terminal_state"] for r in rows)),
        "tags_per_sheet": {sh: len(BS[sh]["tags"]) for sh in SLAB_SHEETS},
        "ambiguous_tags": [r["beam_id"] for r in rows if "TAG_MEMBER_AMBIGUOUS" in r["issues"]],
        "stair_qualifiers": stair_quals,
        "schedule_rows_create_no_occurrence": True}, )
    # 12 matrix (tagged spans by type x floor; families without a tag by family)
    floors = ["FOUNDATION", "GROUND_BEAMS", "GF_ROOF", "1F_ROOF", "2F_ROOF"]
    mat = defaultdict(lambda: {f: 0 for f in floors})
    for r in rows:
        if r["floor"] not in floors:
            continue
        key = r["beam_type"] if r["family"] in ("SIMPLE", "CB", "CANTILEVER", "STAIR", "STRAP") else (
            f"{r['family']}:{r['beam_type']}" if r["beam_type"] else (
                f"{r['family']}:CURVED_UNCATEGORISED" if r["family"] in ("GB", "EXTERIOR_GB") else r["family"]))
        mat[key][r["floor"]] += 1
    mrows = [{"beam_type": k, **v, "total": sum(v.values())} for k, v in sorted(mat.items(), key=lambda kv: _natkey(kv[0]))]
    mat_reg = register("BEAM_TYPE_FLOOR_MATRIX", mrows, {
        "floors": floors, "unit": "plan occurrences (one per tagged span / member span); CB groups in "
                                  "CONTINUOUS_BEAM_OCCURRENCE_REGISTER",
        "floor_totals": {f: sum(r[f] for r in mrows) for f in floors}})
    # 13 definitions
    used = Counter(r["beam_type"] for r in rows if r.get("beam_type"))
    drows = []
    for d in defs["definitions"]:
        if d["element"] not in ("SIMPLE_BEAM", "STRAP_BEAM", "CONTINUOUS_BEAM"):
            continue
        f = d["fields"]
        drows.append({"definition_id": f"BDEF-{d['type']}-{d['insert_handle']}", "beam_type": d["type"],
                      "element": d["element"], "B_cm": f.get("B_cm"), "H_cm": f.get("H_cm"),
                      "fields": {k: v for k, v in f.items() if k not in ("B_cm", "H_cm")},
                      "REMARKS_side_bars": f.get("remarks_side_bars"),
                      "plan_occurrences": used.get(d["type"], 0),
                      "state": "SOURCE_CONFLICT_DUPLICATE_KEY" if d["type"] in conflict_keys else (
                          "DEFINED" if used.get(d["type"]) else "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE"),
                      "source_row": {"block": d["block"], "insert_handle": d["insert_handle"], "page": d["page"]}})
    for rid, cat in (("P13-GB-GT5", "GB_GT_5M"), ("P13-GB-LT5", "GB_LT_5M"), ("P13-GB-LT2_5", "GB_LT_2_5M"),
                     ("P13-GB-EXT", "GB_EXTERIOR"), ("P13-LINTEL", "LINTEL")):
        r = RULE[rid]
        drows.append({"definition_id": f"BDEF-{cat}", "beam_type": cat, "element": "TYPICAL_DETAIL",
                      "rule_id": rid, "normalized_rule": r["normalized_rule"], "rule_status": r["status"],
                      "plan_occurrences": sum(1 for x in rows if x.get("beam_type") == cat or
                                              (cat == "GB_EXTERIOR" and x["family"] == "EXTERIOR_GB")),
                      "state": "DEFINED_BY_TYPICAL_DETAIL" if r["status"] == "EXACT_RULE" else "CANDIDATE"})
    tags_without_def = sorted({r["beam_type"] for r in rows if "TAG_WITHOUT_SCHEDULE_DEFINITION" in r["issues"]})
    def_reg = register("BEAM_DEFINITION_REGISTER", drows, {
        "definitions": len(drows), "by_state": dict(Counter(r["state"] for r in drows)),
        "schedule_rows_without_plan_occurrence": [r["beam_type"] for r in drows
                                                  if r["state"] == "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE"],
        "plan_tags_without_definition": tags_without_def,
        "rows_with_REMARKS": [r["beam_type"] for r in drows if r.get("REMARKS_side_bars")]},
        conflicts=defs["conflicts"])
    # 14 CB register
    cb_rows = B["cb"]
    cb_reg = register("CONTINUOUS_BEAM_OCCURRENCE_REGISTER", cb_rows, {
        "groups": len(cb_rows), "by_state": dict(Counter(c["match_state"] for c in cb_rows)),
        "by_type_floor": dict(sorted(Counter(f"{c['type']}|{c['floor']}" for c in cb_rows).items())),
        "never_forced": True})
    return occ_reg, mat_reg, def_reg, cb_reg, stair_quals


def _arc_centre(bs, member):
    for a in bs["arc_bands"]:
        if a["band_id"] == member:
            return a["centre"]
    return (1e12, 1e12)


# ============================================================================================ 15-17 slabs
TEMP_ROWS = {int(k): v for k, v in RULE["P15-TEMP-TABLE"]["values"]["rows"].items()}


def _ground_slab_notes(src):
    out = []
    for t in src.texts("GBP", None):
        if re.search(r"T\s*=\s*10", t["text"]):
            out.append({"handle": t["handle"], "raw": t["text"], "p": t["p"]})
    return out


def slab_registers(B, src):
    prow, srows, mrows = [], [], []
    project = {"value": 160, "source": "P8-N18 + P1-NOTE-A"}
    gs_notes = _ground_slab_notes(src)
    ann_by_panel = defaultdict(list)
    for sh in SLAB_SHEETS:
        for a in B["annotations"][sh][0]:
            if a.get("panel") and a["owner"] == "SLAB":
                ann_by_panel[a["panel"]].append(a)
    sets = [(sh, B["slabs"][sh]) for sh in SLAB_SHEETS] + [("GBP", B["gbp_panels"])]
    unbound_t = []
    for sh, s in sets:
        bound_t = set()
        for p in s["panels"]:
            pid = p["panel_id"]
            tn = p.get("thickness_notes") or []
            for t in tn:
                bound_t.add(t["handle"])
            vals = sorted({t["value_cm"] * 10 for t in tn})
            local = None
            issues = []
            if len(vals) == 1:
                local = {"value": vals[0], "source": [t["handle"] for t in tn]}
            elif len(vals) > 1:
                issues.append("SOURCE_CONFLICT_SEVERAL_LOCAL_THICKNESS_NOTES")
            floor = None
            if sh == "GBP" and p["class"] == "SLAB_PANEL" and gs_notes:
                floor = {"value": 100, "source": [n["handle"] for n in gs_notes] + ["P3-GROUND-SLAB (CANDIDATE)"]}
            eff = SC.effective_value(local=local, floor=floor, project=project if sh != "GBP" else None)
            if issues:
                eff = {"value": None, "authority": "SOURCE_CONFLICT", "source": vals, "overridden": []}
            anns = ann_by_panel.get(p["panel_id"], []) if sh != "GBP" else []
            dirs = {a.get("direction") for a in anns}
            cls = p["class"]
            if cls == "OPEN_TO_BELOW" and ((p.get("stair_treads") or 0) >= 4 or anns):
                # a void that also holds stair treads / a bar text is a stair well, not "nothing": never NOT_IN_SCOPE
                cls = "STAIR_IN_VOID_ZONE"
                issues.append("OPEN_TO_BELOW_WITH_STAIR_EVIDENCE")
            if cls in ("OUTSIDE_BUILDING_OR_COURT", "OPEN_TO_BELOW", "STAIR_IN_VOID_ZONE"):
                eff = {"value": None, "authority": "NOT_APPLICABLE" if cls != "STAIR_IN_VOID_ZONE" else "BLOCKED",
                       "source": None, "overridden": []}
            if cls == "DOME_ZONE":
                eff = {"value": 100, "authority": "TYPICAL_DETAIL (P7-DOME, CANDIDATE)", "source": "P7-DOME",
                       "overridden": [{"authority": "PROJECT_DEFAULT", "value": 160, "source": project["source"]}]}
            if cls in ("OUTSIDE_BUILDING_OR_COURT", "OPEN_TO_BELOW"):
                term, status = "NOT_IN_SCOPE", "NO_SLAB_CONCRETE"
            elif cls == "STAIR_IN_VOID_ZONE":
                term, status = "COUNTED_BLOCKED", "SPECIAL_STAIR_IN_VOID (P16-STAIR BLOCKED_METHOD)"
            elif cls == "DOME_ZONE":
                term, status = "COUNTED_DEFINITION_PARTIAL", "SPECIAL_DOME"
            elif cls == "STAIR_FLIGHT_ZONE":
                term, status = "COUNTED_BLOCKED", "SPECIAL_STAIR (P16-STAIR BLOCKED_METHOD)"
            elif sh == "GBP":
                term, status = "COUNTED_DEFINITION_PARTIAL", "GROUND_SLAB_CANDIDATE (extent of application not drawn)"
            else:
                full = eff["value"] and ("X" in dirs and "Y" in dirs)
                term = "COUNTED_AND_DEFINED" if full else "COUNTED_DEFINITION_PARTIAL"
                status = "COUNTED" if full else ("NO_BAR_ANNOTATION" if not anns else "ANNOTATION_ONE_DIRECTION_ONLY")
            prow.append({"panel_id": pid, "source_id": f"SLABFACE:{sh}:{p['face_id']}", "sheet": sh,
                         "floor": SLAB_FLOOR[sh], "class": cls, "polygon_mm": p["ring"], "holes_mm": p["holes"],
                         "area_m2": p["area_m2"], "perimeter_m": p["perimeter_m"], "Lx_m": p["Lx_m"], "Ly_m": p["Ly_m"],
                         "rectangularity": p["rectangularity"], "orientation_deg": p["orientation_deg"],
                         "edges": p.get("edges"), "support_summary": p.get("support_summary"),
                         "continuity_summary": p.get("continuity_summary"), "local_thickness_notes": tn,
                         "effective_thickness_mm": eff["value"], "thickness_authority": eff["authority"],
                         "thickness_source": eff["source"], "overridden": eff["overridden"],
                         "void_evidence": p.get("void_evidence"), "stair_treads": p.get("stair_treads"),
                         "boundary_handles": p.get("boundary_sources"),
                         "annotations": [a["text_handle"] for a in anns], "annotation_directions": sorted(d for d in dirs if d),
                         "issues": issues, "status": status, "terminal_state": term})
        for t in s.get("t_marks", []):
            if t["handle"] not in bound_t:
                unbound_t.append({"sheet": sh, **t})
    pclass = {r["panel_id"]: r["class"] for r in prow}
    for sh in SLAB_SHEETS:
        rows, orph = B["annotations"][sh]
        for a in rows + [dict(o, owner="ORPHAN_QUALIFIER") for o in orph]:
            p = a.get("parsed") or {}
            layer = a.get("layer")
            layer_n = "T&B" if layer == "T&B" else ("TOP" if layer == "TOP" else (
                "BOTTOM" if layer == "BOTTOM" else "NOT_STATED"))
            owner = a["owner"]
            if owner == "SLAB":
                term = "COUNTED_AND_DEFINED" if a["binding"] in ("BOUND", "BOUND_NEAR_EDGE") else "COUNTED_BLOCKED"
                if term == "COUNTED_AND_DEFINED" and pclass.get(a.get("panel")) != "SLAB_PANEL":
                    term = "COUNTED_DEFINITION_PARTIAL"  # bound to a stair / dome / void face whose method is open
            elif owner == "SLAB_SUPPORT_TOP_BAR":
                term = "COUNTED_AND_DEFINED" if a.get("beam_line") else "COUNTED_BLOCKED"
            elif owner in ("SECTION_DETAIL", "PLAN_NOTE"):
                term = "NOT_IN_SCOPE"
            elif owner == "PLANTED_COLUMN_LABEL":
                term = "COUNTED_AND_DEFINED"
            else:
                term = "COUNTED_BLOCKED"
            srows.append({"source_row_id": f"SRB-{sh}-{a['text_handle']}", "source_id": f"SLABTXT:{sh}:{a['text_handle']}",
                          "sheet": sh, "floor": SLAB_FLOOR[sh], "raw": a.get("raw"), "owner": owner,
                          "panel": a.get("panel"), "panel_candidates": a.get("panel_candidates"),
                          "binding": a.get("binding"), "direction": a.get("direction"), "layer": layer_n,
                          "TandB": layer_n == "T&B", "tb_text_handle": a.get("tb_text_handle"),
                          "dia_mm": p.get("dia_mm"), "count": p.get("count"), "count_mode": p.get("count_mode"),
                          "spacing_mm": p.get("spacing_mm"), "bar_graphic_handle": a.get("bar_graphic_handle"),
                          "support_beam_line": a.get("beam_line"), "corner_reinforcement": a.get("corner_reinforcement"),
                          "text_handle": a["text_handle"], "position_mm": a.get("position_mm"),
                          "note": a.get("note") or a.get("layer_note"), "status": a.get("status") or a.get("binding"),
                          "terminal_state": term, "no_lengths_or_kg": True})
    for n in gs_notes:
        srows.append({"source_row_id": f"SRB-GBP-{n['handle']}", "source_id": f"SLABTXT:GBP:{n['handle']}",
                      "sheet": "GBP", "floor": "GROUND_SLAB_SOG", "raw": n["raw"], "owner": "GROUND_SLAB_NOTE",
                      "panel": None, "binding": "FLOOR_SPECIFIC_NOTE", "direction": "EACH_WAY", "layer": "SINGLE",
                      "TandB": False, "dia_mm": 10, "count": 5, "count_mode": "BARS_PER_METRE",
                      "text_handle": n["handle"], "position_mm": n["p"], "status": "CANDIDATE (extent not drawn)",
                      "terminal_state": "COUNTED_DEFINITION_PARTIAL", "no_lengths_or_kg": True})
    # rule map
    pidx = {r["panel_id"]: r for r in prow}
    for r in prow:
        if r["class"] != "SLAB_PANEL" or r["sheet"] == "GBP":
            continue
        t = r["effective_thickness_mm"]
        st, payload = SC.table_lookup_exact(t, TEMP_ROWS) if t else ("BLOCKED_METHOD", None)
        edges = []
        for e in r["edges"] or []:
            cont = e["continuity"]
            if e["support"] not in ("BEAM",):
                top = {"rule": "P15-SLAB-ON-BEAMS", "state": "BLOCKED_METHOD",
                       "why": f"edge supported by {e['support']} - the slab-on-beams rule needs a beam edge"}
                bot = {"state": "BLOCKED_METHOD"}
            elif cont == "CONTINUOUS":
                nb = pidx.get(e["neighbour_panel"])
                top = {"rule": "P15-SLAB-ON-BEAMS", "state": "EXACT_RULE", "factor": 0.30,
                       "L_basis": "max(L1, L2): this panel and the neighbour across the edge, span perpendicular to "
                                  "the edge", "neighbour": e["neighbour_panel"],
                       "neighbour_rect": [nb["Lx_m"], nb["Ly_m"]] if nb else None}
                bot = {"rule": "P15-SLAB-ON-BEAMS", "state": "EXACT_RULE", "stop_50pct_at": "0.125 L"}
            else:
                top = {"rule": "P15-SLAB-ON-BEAMS", "state": "EXACT_RULE", "factor": 0.25,
                       "L_basis": "L1 = this panel's span perpendicular to the edge",
                       "continuity_basis": cont}
                bot = {"rule": "P15-SLAB-ON-BEAMS", "state": "NOT_APPLICABLE (non-continuous edge)"}
            if r["rectangularity"] is not None and r["rectangularity"] < 0.95:
                top = dict(top, state="BLOCKED_METHOD", why="non-rectangular panel: span perpendicular to the edge "
                                                            "is not a single value")
            edges.append({"edge_index": e["edge_index"], "length_m": e["length_m"], "support": e["support"],
                          "support_ref": e["support_ref"], "continuity": cont, "top_extension": top,
                          "bottom_curtailment": bot,
                          "plan_note_top_over_beam": {"rule": "P4-6-NOTE-2", "state": "CANDIDATE",
                                                      "value": "5Ø10/m, length 1/3 span"} if e["support"] == "BEAM"
                          else None})
        mrows.append({"panel_id": r["panel_id"], "floor": r["floor"], "sheet": r["sheet"],
                      "thickness": {"rule": "P8-N18 / local T mark", "value_mm": t, "authority": r["thickness_authority"],
                                    "state": "EXACT_RULE" if t else "BLOCKED"},
                      "temperature_steel": {"rule": "P15-TEMP-TABLE", "thickness_mm": t, "state": st,
                                            "row": payload, "no_interpolation": True},
                      "TandB_annotation": any(x["TandB"] for x in srows if x["panel"] == r["panel_id"]),
                      "edges": edges})
    panel_sum = {SLAB_FLOOR[sh]: dict(Counter(r["class"] for r in prow if r["sheet"] == sh)) for sh, _ in sets}
    thick = defaultdict(Counter)
    for r in prow:
        if r["class"] in ("SLAB_PANEL", "STAIR_FLIGHT_ZONE", "DOME_ZONE"):
            thick[r["floor"]][f"{r['effective_thickness_mm']}mm:{r['thickness_authority']}"] += 1
    p_reg = register("SLAB_PANEL_REGISTER", prow, {
        "faces": len(prow), "classes_by_floor": panel_sum,
        "thickness_by_floor": {k: dict(v) for k, v in thick.items()},
        "local_overrides": [r["panel_id"] for r in prow if r["thickness_authority"] == "LOCAL_PANEL_NOTE"],
        "t_marks_not_bound_to_a_panel": unbound_t,
        "by_terminal_state": dict(Counter(r["terminal_state"] for r in prow))})
    s_reg = register("SLAB_REBAR_SOURCE_REGISTER", srows, {
        "annotations": len(srows), "by_owner": dict(Counter(r["owner"] for r in srows)),
        "by_floor_owner": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["floor"], r["owner"]) for r in srows).items())},
        "by_layer": dict(Counter(r["layer"] for r in srows)),
        "slab_annotations_unbound": [r["source_row_id"] for r in srows if r["owner"] == "SLAB" and
                                     r["binding"] not in ("BOUND", "BOUND_NEAR_EDGE")],
        "no_lengths_or_kg": True})
    m_reg = register("SLAB_RULE_APPLICATION_MAP", mrows, {
        "panels": len(mrows),
        "temperature_state": dict(Counter(m["temperature_steel"]["state"] for m in mrows)),
        "edge_top_states": dict(Counter(e["top_extension"]["state"] for m in mrows for e in m["edges"])),
        "temperature_table_rows_mm": sorted(TEMP_ROWS)})
    return p_reg, s_reg, m_reg, gs_notes


# ============================================================================================ 18-19 special, pool
POOL_TEXT_MAP = {  # DET (p.7) bar texts -> pool component; read against the p.7 render (CANDIDATE, one AI channel)
    "1896": ("DEEP_WALL", "TOP_COPING_BARS"), "1893": ("DEEP_WALL", "VERTICAL_OUTER_FACE"),
    "188D": ("DEEP_WALL", "HORIZONTAL_OUTER_FACE"), "1906": ("DEEP_WALL", "VERTICAL_INNER_FACE"),
    "18FC": ("DEEP_WALL", "HORIZONTAL_INNER_FACE"), "1881": ("DEEP_END_BASE", "CORNER_BARS"),
    "18B0": ("DEEP_END_BASE", "TOP_BARS"), "18AA": ("DEEP_END_BASE", "BOTTOM_BARS"),
    "19B0": ("DEEP_END_BASE", "BOTTOM_BARS (second label)"), "18D3": ("SLOPED_BASE", "TOP_BARS"),
    "18AD": ("SLOPED_BASE", "BOTTOM_BARS"), "1907": ("SHALLOW_BASE", "TOP_BARS"),
    "18F0": ("SHALLOW_BASE", "BOTTOM_BARS"), "18F8": ("SHALLOW_BASE", "BOTTOM_BARS (second label)"),
    "192F": ("SHALLOW_WALL", "VERTICAL_BARS"), "191F": ("SHALLOW_WALL", "HORIZONTAL_INNER_FACE"),
    "192E": ("SHALLOW_WALL", "HORIZONTAL_OUTER_FACE"), "192B": ("SHALLOW_END_BASE", "CORNER_BARS"),
    "187C": ("CORNER_DETAIL_DEEP", "WALL_VERTICAL_L_BAR"), "18A8": ("CORNER_DETAIL_DEEP", "BASE_L_BAR"),
    "1860": ("CORNER_DETAIL_SLOPE", "BASE_TOP_BAR"), "1869": ("CORNER_DETAIL_SLOPE", "BASE_BOTTOM_BAR"),
    "18DB": ("CORNER_DETAIL_SLOPE_SHALLOW", "TOP_BAR"), "18D7": ("CORNER_DETAIL_SLOPE_SHALLOW", "BOTTOM_BAR"),
    "18DD": ("CORNER_DETAIL_SHALLOW", "BASE_BAR"), "1929": ("CORNER_DETAIL_SHALLOW", "WALL_VERTICAL_L_BAR"),
}
DOME_TEXT_MAP = {"1A47": ("RING_BEAM", "TOP_BARS"), "1A68": ("RING_BEAM", "TOP_BARS"),
                 "1A29": ("RING_BEAM", "STIRRUPS_PER_M"), "1A58": ("RING_BEAM", "STIRRUPS_PER_M"),
                 "1A37": ("RING_BEAM", "SIDE_BARS"), "1A66": ("RING_BEAM", "SIDE_BARS"),
                 "1A4B": ("RING_BEAM", "BOTTOM_BARS"), "1A6C": ("RING_BEAM", "BOTTOM_BARS"),
                 "1A15": ("SHELL", "MESH_TWO_LAYERS"), "1A0E": ("SHELL", "MESH_TWO_LAYERS (second label)")}


def special_registers(B, src, stair_quals, gs_notes, slab_reg):
    rows = []
    CR = B["CR"]
    for lb in CR["labels"]:
        kind = {"T.C": "TURN_COLUMN", "D.C": "DEAD_COLUMN"}.get(lb["label"], "PLANTED_COLUMN")
        rule = {"TURN_COLUMN": "P15-TWISTED", "DEAD_COLUMN": "P3-LEGEND", "PLANTED_COLUMN": "P15-PLANTED"}[kind]
        rows.append({"special_id": f"SPC-{kind}-{lb['sheet']}-{lb['handle']}", "source_id": f"SLABLABEL:{lb['sheet']}:{lb['handle']}",
                     "kind": kind, "floor": SLAB_FLOOR[lb["sheet"]], "label": lb["text"], "bound_chain": lb["bound_chain_id"],
                     "binding": lb["state"], "rule": rule, "rule_status": RULE[rule]["status"],
                     "status": "COUNTED" if lb["state"] == "BOUND" else "UNRESOLVED",
                     "terminal_state": "COUNTED_DEFINITION_PARTIAL" if lb["state"] == "BOUND" else "COUNTED_BLOCKED"})
    for p in slab_reg["rows"]:
        if p["class"] in ("STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE"):
            rows.append({"special_id": f"SPC-STAIR-{p['panel_id']}", "source_id": None, "kind": "STAIR_FLIGHT",
                         "floor": p["floor"], "panel": p["panel_id"], "area_m2": p["area_m2"], "treads": p["stair_treads"],
                         "thickness_note_mm": p["effective_thickness_mm"], "rule": "P16-STAIR",
                         "rule_status": RULE["P16-STAIR"]["status"], "status": "BLOCKED",
                         "terminal_state": "COUNTED_BLOCKED", "accounted_in": "SLAB_PANEL_REGISTER"})
    for q in stair_quals:
        rows.append({"special_id": f"SPC-STAIR_BEAM-{q['sheet']}-{q['qualifier_handle']}",
                     "source_id": f"STAIRQUAL:{q['sheet']}:{q['qualifier_handle']}", "kind": "STAIR_BEAM",
                     "floor": BEAM_FLOOR[q["sheet"]], "tag_handle": q["tag_handle"], "rule": "schedule row of the tag",
                     "status": "COUNTED" if q["tag_handle"] else "UNRESOLVED",
                     "terminal_state": "COUNTED_AND_DEFINED" if q["tag_handle"] else "COUNTED_BLOCKED",
                     "accounted_in": "BEAM_OCCURRENCE_REGISTER (family STAIR)"})
    ff = [r for r in B["footings"]["rows"] if r["type"] == "FF"]
    rows.append({"special_id": "SPC-LIFT_PIT", "source_id": None, "kind": "LIFT_PIT", "floor": "FOUNDATION",
                 "footing": [r["footing_id"] for r in ff], "rule": "P14-LIFT", "rule_status": RULE["P14-LIFT"]["status"],
                 "walls": "200 mm, 6Ø12/m + 6Ø16/m; pit depth BLOCKED (manufacturer)", "status": "BLOCKED",
                 "terminal_state": "COUNTED_BLOCKED"})
    for c in B["levels"]["lift_tie_beam_rule_check"]:
        if c["required"]:
            rows.append({"special_id": f"SPC-LIFT_TIE_BEAM-{c['storey']}", "source_id": None, "kind": "LIFT_TIE_BEAM",
                         "floor": c["storey"], "rule": "P8-N19", "rule_status": RULE["P8-N19"]["status"],
                         "drawn": False, "status": "BLOCKED", "terminal_state": "COUNTED_BLOCKED",
                         "accounted_in": "BEAM_OCCURRENCE_REGISTER"})
    rows.append({"special_id": "SPC-LINTELS", "source_id": None, "kind": "LINTEL_POPULATION", "floor": "ALL",
                 "rule": "P13-LINTEL", "status": "BLOCKED", "terminal_state": "COUNTED_BLOCKED",
                 "why": "occurrences come from the architectural opening register (not structural plans)"})
    rows.append({"special_id": "SPC-BOUNDARY_WALL", "source_id": None, "kind": "BOUNDARY_WALL", "floor": "SITE",
                 "rule": "P14-BOUNDARY", "rule_status": RULE["P14-BOUNDARY"]["status"],
                 "schedule_row": "B.W (SBT) 20x60", "status": "SOURCE_CONFLICT", "terminal_state": "COUNTED_BLOCKED",
                 "why": "boundary wall typical detail vs schedule row B.W; length not on the structural plans"})
    for sh in SLAB_SHEETS:
        for t in src.texts(sh, None):
            if t["text"].upper().startswith("PARAPET"):
                rows.append({"special_id": f"SPC-PARAPET-{sh}", "source_id": f"NOTE:{sh}:{t['handle']}",
                             "kind": "PARAPET", "floor": SLAB_FLOOR[sh], "raw": t["text"], "rule": "P4-6-NOTE-1",
                             "rule2": "P14-PARAPETS", "status": "BLOCKED", "terminal_state": "COUNTED_BLOCKED",
                             "why": "parapet geometry follows the architectural drawings"})
            if t["text"].upper().startswith("WATER TANK"):
                rows.append({"special_id": f"SPC-WATER_TANK-{sh}", "source_id": f"NOTE:{sh}:{t['handle']}",
                             "kind": "WATER_TANK_SLAB", "floor": SLAB_FLOOR[sh], "raw": t["text"],
                             "panels": [p["panel_id"] for p in slab_reg["rows"] if p["sheet"] == sh and
                                        p["thickness_authority"] == "LOCAL_PANEL_NOTE"],
                             "status": "COUNTED", "terminal_state": "COUNTED_AND_DEFINED",
                             "accounted_in": "SLAB_PANEL_REGISTER (T 18 local note)"})
    # domes: cluster the FFRS SEE DETAIL labels
    sd = sorted([t for t in src.texts("FFRS", None) if t["text"].strip().upper() == "SEE DETAIL"], key=lambda t: t["p"][0])
    groups = []
    for t in sd:
        if groups and abs(t["p"][0] - groups[-1][-1]["p"][0]) < 4000:
            groups[-1].append(t)
        else:
            groups.append([t])
    for i, g in enumerate(groups, 1):
        cx = sum(t["p"][0] for t in g) / len(g)
        zones = [p["panel_id"] for p in slab_reg["rows"] if p["class"] == "DOME_ZONE" and abs(
            sum(v[0] for v in p["polygon_mm"]) / len(p["polygon_mm"]) - cx) < 4000]
        rows.append({"special_id": f"SPC-DOME-{i}", "source_id": None, "kind": "DOME", "floor": "1F_ROOF_SLAB",
                     "see_detail_labels": [t["handle"] for t in g], "dome_zone_faces": zones,
                     "rule": "P7-DOME", "rule_status": RULE["P7-DOME"]["status"],
                     "detail": "span 442 cm, rise 190 cm (p.7, N.I.S = not to scale)",
                     "status": "PROVISIONAL", "terminal_state": "COUNTED_DEFINITION_PARTIAL"})
    rows.append({"special_id": "SPC-POOL", "source_id": None, "kind": "SWIMMING_POOL", "floor": "GROUND",
                 "rule": "P7-POOL", "see": "POOL_STRUCTURAL_REGISTER", "status": "PROVISIONAL",
                 "terminal_state": "COUNTED_DEFINITION_PARTIAL"})
    rows.append({"special_id": "SPC-GROUND_SLAB", "source_id": None, "kind": "GROUND_SLAB", "floor": "GROUND_SLAB_SOG",
                 "notes": [n["handle"] for n in gs_notes], "cells": sum(1 for p in slab_reg["rows"] if p["sheet"] == "GBP"
                                                                       and p["class"] == "SLAB_PANEL"),
                 "rule": "P3-GROUND-SLAB", "status": "PROVISIONAL", "terminal_state": "COUNTED_DEFINITION_PARTIAL",
                 "accounted_in": "SLAB_PANEL_REGISTER (GBP cells)"})
    corner = [r for r in B["annotations"]["FFRS"][0] + B["annotations"]["GFRS"][0] + B["annotations"]["SFRS"][0]
              if r.get("corner_reinforcement")]
    if corner:
        rows.append({"special_id": "SPC-CORNER_BARS", "source_id": None, "kind": "SLAB_CORNER_BARS",
                     "texts": [f"{r['sheet']}:{r['text_handle']}" for r in corner],
                     "panels": sorted({r.get("panel") for r in corner if r.get("panel")}), "status": "COUNTED",
                     "terminal_state": "COUNTED_AND_DEFINED", "accounted_in": "SLAB_REBAR_SOURCE_REGISTER"})
    for kind, rid in (("BEAM_OPENING", "P16-BEAM-OPENING"), ("CASEMENT_DETAIL", "P15-CASEMENT"), ("RIBBED_SLAB", "P16-RIBS")):
        rows.append({"special_id": f"SPC-{kind}", "source_id": None, "kind": kind, "floor": "ALL", "rule": rid,
                     "plan_occurrences": 0, "status": "NO_OCCURRENCE_MARKED", "terminal_state": "NOT_IN_SCOPE",
                     "why": "typical detail printed; no occurrence marked on any plan"})
    for sh in ("GFRS", "FFRS"):
        for t in src.texts(sh, None):
            if t["text"].upper().startswith("%%USECTION"):
                rows.append({"special_id": f"SPC-SECTION-{sh}-{t['handle']}", "source_id": f"NOTE:{sh}:{t['handle']}",
                             "kind": "SECTION_DETAIL_CALLOUT", "floor": SLAB_FLOOR[sh], "raw": t["text"].replace("%%U", ""),
                             "status": "DETAIL", "terminal_state": "NOT_IN_SCOPE",
                             "why": "section drawing inside the plan sheet (its bar texts are SECTION_DETAIL owners)"})
    sp_reg = register("SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER", rows, {
        "rows": len(rows), "by_kind": dict(Counter(r["kind"] for r in rows)),
        "by_terminal_state": dict(Counter(r["terminal_state"] for r in rows)),
        "special_population_cannot_disappear": True})
    # pool
    det = {t["handle"]: t for t in src.texts("DET", None)}
    prow = []
    for h, (comp, role) in sorted(POOL_TEXT_MAP.items()):
        t = det.get(h)
        p = SC.parse_slab_rebar(t["text"].replace("%%C", "%%c")) if t else None
        prow.append({"pool_item_id": f"POOL-{comp}-{h}", "source_id": f"DETTXT:DET:{h}", "component": comp,
                     "role": role, "raw": t["text"] if t else None, "parsed": p, "position_mm": t["p"] if t else None,
                     "mapping_channel": "AI visual reading of the p.7 render (CANDIDATE)",
                     "status": "PROVISIONAL" if t else "MISSING_SOURCE_TEXT",
                     "terminal_state": "COUNTED_DEFINITION_PARTIAL" if t else "COUNTED_BLOCKED"})
    gb_pool = [r for r in B["ground_beams"] if r["kind"] == "CURVED"]
    pool_summary = {
        "occurrence": {"plan_label": "GBP 'swimming pool' (block SWIM)", "plan_sheet": "GBP",
                       "curved_ground_beams": [r["gb_id"] for r in gb_pool]},
        "geometry": {"wall_thickness_cm": 20, "deep_base_thickness_cm": 40, "lengths_and_depths": "AS PER ARCH (BLOCKED)"},
        "components": sorted({v[0] for v in POOL_TEXT_MAP.values()}),
        "build_up_non_structural": ["5cm SECREED", "5cm INSULATION MEMBRANE", "10cm PLAIN CONCRETE"],
        "pump_room": "NOT_DRAWN (no structural occurrence)", "scale_note": "(N.I.S) = not to scale"}
    pool_reg = register("POOL_STRUCTURAL_REGISTER", prow, {"items": len(prow),
                                                           "by_component": dict(Counter(r["component"] for r in prow))},
                        pool=pool_summary)
    drow = []
    for h, (comp, role) in sorted(DOME_TEXT_MAP.items()):
        t = det.get(h)
        drow.append({"dome_item_id": f"DOME-{comp}-{h}", "source_id": f"DETTXT:DET:{h}", "component": comp,
                     "role": role, "raw": t["text"] if t else None, "position_mm": t["p"] if t else None,
                     "terminal_state": "COUNTED_DEFINITION_PARTIAL" if t else "COUNTED_BLOCKED"})
    sp_reg["dome_detail_items"] = drow
    other_det = [{"handle": h, "raw": t["text"], "p": t["p"]} for h, t in sorted(det.items())
                 if h not in POOL_TEXT_MAP and h not in DOME_TEXT_MAP]
    pool_reg["det_texts_not_bar_annotations"] = other_det
    return sp_reg, pool_reg


# ============================================================================================ 20-21 conservation, queue
def conservation_register(B, src, regs):
    C = B["C"]
    src_objs, rows = [], []
    chain_term = {}
    for r in regs["COLUMN_OCCURRENCE_REGISTER"]["rows"]:
        prev = chain_term.get(r["chain_id"])
        chain_term[r["chain_id"]] = _worst(prev, r["terminal_state"])
    for ch in regs["COLUMN_VERTICAL_CHAIN_REGISTER"]["rows"]:
        for sh, h in list(ch["members_by_sheet"].items()) + list(ch["transition_outlines"].items()):
            rows.append({"source_id": f"COLOUTLINE:{sh}:{h}", "register": "COLUMN_VERTICAL_CHAIN_REGISTER",
                         "row_id": ch["chain_id"], "terminal_state": chain_term.get(ch["chain_id"], "COUNTED_BLOCKED")})
        for sh, t in ch["tags_by_plan"].items():
            rows.append({"source_id": f"COLTAG:{sh}:{t['handle']}", "register": "COLUMN_VERTICAL_CHAIN_REGISTER",
                         "row_id": ch["chain_id"], "terminal_state": chain_term.get(ch["chain_id"], "COUNTED_BLOCKED")})
    for sh in S.CHAIN_SHEETS:
        for o in C["outlines"][sh]:
            src_objs.append({"source_id": f"COLOUTLINE:{sh}:{o['handle']}", "family": "COLUMN_OUTLINE"})
    for sh, t in C["tags"].items():
        for rec in t["assigned"].values():
            src_objs.append({"source_id": f"COLTAG:{sh}:{rec['tag_handle']}", "family": "COLUMN_TAG"})
        for u in t["unbound"]:
            h = u if isinstance(u, str) else u["handle"]
            src_objs.append({"source_id": f"COLTAG:{sh}:{h}", "family": "COLUMN_TAG"})
            rows.append({"source_id": f"COLTAG:{sh}:{h}", "register": "COLUMN_OCCURRENCE_REGISTER",
                         "row_id": None, "terminal_state": "COUNTED_BLOCKED"})
    # footings: outlines and every FP footing tag text (enumerated from the source, not from the census)
    for r in regs["FOOTING_OCCURRENCE_REGISTER"]["rows"]:
        oid = f"FTGOUTLINE:FP:{(r['outline'] or {}).get('handle') or r['footing_id']}"
        src_objs.append({"source_id": oid, "family": "FOOTING_OUTLINE"})
        rows.append({"source_id": oid, "register": "FOOTING_OCCURRENCE_REGISTER", "row_id": r["footing_id"],
                     "terminal_state": r["terminal_state"]})
        for t in ([r["tag"]] if r.get("tag") else []) + (r.get("competing_tags") or []):
            rows.append({"source_id": f"FTGTAG:FP:{t['handle']}", "register": "FOOTING_OCCURRENCE_REGISTER",
                         "row_id": r["footing_id"], "terminal_state": r["terminal_state"]})
    for t in src.texts("FP", None):
        m = S.FOOT_TAG.match(t["text"].strip().upper())
        if m and t["layer"] not in ("S-TEXT.SCH",):
            src_objs.append({"source_id": f"FTGTAG:FP:{t['handle']}", "family": "FOOTING_TAG"})
    # straps / beams / GB / slab / special / pool
    for r in regs["BEAM_OCCURRENCE_REGISTER"]["rows"]:
        if r["source_id"].startswith(("RULE:",)):
            continue
        fam = r["source_id"].split(":")[0]
        src_objs.append({"source_id": r["source_id"], "family": {"BEAMTAG": "BEAM_TAG", "MEMBER": "UNTAGGED_BEAM_MEMBER",
                                                                 "STRAP": "STRAP_BEAM_BAND", "GBSPAN": "GROUND_BEAM_SPAN"}[fam]})
        rows.append({"source_id": r["source_id"], "register": "BEAM_OCCURRENCE_REGISTER", "row_id": r["beam_id"],
                     "terminal_state": r["terminal_state"]})
    tagged = {f"BEAMTAG:{sh}:{t['handle']}" for sh in SLAB_SHEETS for t in B["beams"][sh]["tags"]}
    missing_tags = tagged - {o["source_id"] for o in src_objs}
    for sid in sorted(missing_tags):
        src_objs.append({"source_id": sid, "family": "BEAM_TAG"})
    for r in regs["SLAB_PANEL_REGISTER"]["rows"]:
        src_objs.append({"source_id": r["source_id"], "family": "SLAB_FACE"})
        rows.append({"source_id": r["source_id"], "register": "SLAB_PANEL_REGISTER", "row_id": r["panel_id"],
                     "terminal_state": r["terminal_state"]})
        for t in r["local_thickness_notes"]:
            sid = f"TMARK:{r['sheet']}:{t['handle']}"
            if not any(x["source_id"] == sid for x in rows):
                rows.append({"source_id": sid, "register": "SLAB_PANEL_REGISTER", "row_id": r["panel_id"],
                             "terminal_state": r["terminal_state"]})
    for sh, s in [(sh, B["slabs"][sh]) for sh in SLAB_SHEETS] + [("GBP", B["gbp_panels"])]:
        for t in s.get("t_marks", []):
            src_objs.append({"source_id": f"TMARK:{sh}:{t['handle']}", "family": "SLAB_THICKNESS_MARK"})
    for r in regs["SLAB_REBAR_SOURCE_REGISTER"]["rows"]:
        src_objs.append({"source_id": r["source_id"], "family": "SLAB_BAR_TEXT"})
        rows.append({"source_id": r["source_id"], "register": "SLAB_REBAR_SOURCE_REGISTER",
                     "row_id": r["source_row_id"], "terminal_state": r["terminal_state"]})
    for r in regs["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]["rows"]:
        if r.get("source_id"):
            src_objs.append({"source_id": r["source_id"], "family": "SPECIAL_" + r["kind"]})
            rows.append({"source_id": r["source_id"], "register": "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER",
                         "row_id": r["special_id"], "terminal_state": r["terminal_state"]})
    for r in regs["POOL_STRUCTURAL_REGISTER"]["rows"]:
        src_objs.append({"source_id": r["source_id"], "family": "POOL_DETAIL_TEXT"})
        rows.append({"source_id": r["source_id"], "register": "POOL_STRUCTURAL_REGISTER", "row_id": r["pool_item_id"],
                     "terminal_state": r["terminal_state"]})
    for r in regs["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]["dome_detail_items"]:
        src_objs.append({"source_id": r["source_id"], "family": "DOME_DETAIL_TEXT"})
        rows.append({"source_id": r["source_id"], "register": "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER",
                     "row_id": r["dome_item_id"], "terminal_state": r["terminal_state"]})
    for t in regs["POOL_STRUCTURAL_REGISTER"]["det_texts_not_bar_annotations"]:
        sid = f"DETTXT:DET:{t['handle']}"
        src_objs.append({"source_id": sid, "family": "DETAIL_SHEET_OTHER_TEXT"})
        rows.append({"source_id": sid, "register": "POOL_STRUCTURAL_REGISTER", "row_id": None,
                     "terminal_state": "NOT_IN_SCOPE"})
    # schedule rows (definitions): counted only through plan occurrences
    for name, idf, st_key in (("COLUMN_DEFINITION_REGISTER", "definition_id", "state"),
                              ("FOOTING_DEFINITION_REGISTER", "definition_id", "state"),
                              ("BEAM_DEFINITION_REGISTER", "definition_id", "state")):
        for r in regs[name]["rows"]:
            sid = f"SCHEDROW:{r[idf]}"
            src_objs.append({"source_id": sid, "family": "SCHEDULE_DEFINITION"})
            st = r[st_key]
            term = ("COUNTED_AND_DEFINED" if st.startswith("DEFINED") and r.get("plan_occurrences") else
                    "NOT_IN_SCOPE" if st == "NO_BAND_IN_SCHEDULE" else "COUNTED_BLOCKED")
            rows.append({"source_id": sid, "register": name, "row_id": r[idf], "terminal_state": term})
    # dedupe identical (source, row) pairs produced by two passes over the same footing tag
    seen, uniq = set(), []
    for r in rows:
        k = (r["source_id"], r["register"], r["row_id"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    res = SC.conservation(src_objs, uniq)
    out_rows = sorted(uniq, key=lambda r: r["source_id"])
    return register("STRUCTURAL_OCCURRENCE_CONSERVATION_REGISTER", out_rows, {
        "source_objects": len(src_objs), "register_rows": len(uniq), "violations": res["violations"],
        "silent_disappearances": sum(1 for v in res["violations"] if v["kind"] == "SILENT_DISAPPEARANCE"),
        "by_state": res["by_state"], "by_family": res["by_family"]})


_ORDER = ["COUNTED_AND_DEFINED", "NOT_IN_SCOPE", "COUNTED_DEFINITION_PARTIAL", "COUNTED_BLOCKED"]


def _worst(a, b):
    if a is None:
        return b
    return a if _ORDER.index(a) >= _ORDER.index(b) else b


def review_queue(B, regs):
    q = []

    def add(rank, area, item, question, evidence, impact):
        q.append({"rank": rank, "area": area, "item": item, "question": question, "evidence": evidence,
                  "impact": impact})
    ties = regs["COLUMN_TIE_TOPOLOGY_RULES"]
    add(1, "COLUMN_TIES", "6Ø8/m semantics", ties["open_questions"][0],
        "p.9 'ST. OF COLUMN- 6Ø8/m' (DXF 1BAA) + detail sketches 1BAB / 1BBA+1BBF / 1BB6+1BD3+1BDA",
        "every column tie count (bands 2 and 3 double / triple)")
    gaps = ties["summary"]["boundary_gap_or_out_of_range"]
    add(2, "COLUMN_TIES", "L = 80 cm boundary", ties["open_questions"][1],
        f"{len(gaps)} occurrences on the boundary: {[g['column_id'] for g in gaps]}", "C7 tie topology")
    tmin = ties["summary"]["min_thickness_findings"]
    add(3, "COLUMNS", "GF columns below Tmin", "GF storey is 4.50 m -> Tmin 25 cm (p.9); these columns are 20 cm in "
        "the schedule. Accept the schedule (engineer's design) or flag to the engineer?",
        f"{len(tmin)} occurrences: {sorted({t['column_id'].split('-')[1] for t in tmin})}", "information only; no "
        "quantity change unless the section changes")
    conf = [c for c in B["CR"]["chains"] if c["type_authority"] == "TAG_CONFLICT"]
    for c in conf:
        add(4, "COLUMNS", f"tag conflict {c['chain_id']}", "Which tag is right for this column position?",
            {k: v["tag"] for k, v in c["tags_by_plan"].items()} | {"CAP_size_label": c["axis_plan_size_label"]},
            "type of the whole chain")
    mis = regs["COLUMN_OCCURRENCE_REGISTER"]["summary"]["drawn_vs_schedule_mismatch_by_floor"]
    add(5, "COLUMNS", "drawn section vs schedule", "Plan outline size differs from the schedule band for these "
        "occurrences (e.g. lift columns 20X50 / 25X100 on the axis plan vs 30 cm in the schedule). Schedule governs?",
        mis, "section per storey")
    fconf = [r for r in regs["FOOTING_OCCURRENCE_REGISTER"]["rows"] if r.get("competing_tags")]
    for r in fconf:
        add(6, "FOOTINGS", r["footing_id"], "One outline carries tags F and F10 (and holds C + C10). Which footing "
            "is it, or is it two footings drawn as one outline?", {"outline_bbox": r["outline"]["bbox"],
                                                                    "candidates": r["candidate_types"]},
            "one combined footing")
    add(7, "FOOTINGS", "BOXED '3+4'", "What does the BOXED value '3+4' (single-layer footings) mean - box/cage bars "
        "(3 one way + 4 the other) or starters?", regs["FOOTING_DEFINITION_REGISTER"]["summary"]["boxed_values"],
        "every single-layer footing")
    sb = [c for c in B["defs"]["conflicts"]]
    for c in sb:
        add(8, "STRAPS", c["key"], "SB2 appears twice in the schedule (100x50 and 80x50). Drawn width on FP is "
            "~987 mm (favours 100). Which row governs?", c["rows"], "SB2 section and bars")
    for r in regs["CONTINUOUS_BEAM_OCCURRENCE_REGISTER"]["rows"]:
        if r["match_state"] != "MATCH_CONFIRMED":
            add(9, "CONTINUOUS_BEAMS", r["cb_id"], "Schedule spans vs plan spans disagree - which plan members form "
                "this CB?", {"schedule_spans_m": r["schedule_spans_m"],
                             "plan_spans_cc_m": [s["cc_m"] for s in r["plan_spans"]],
                             "extension_check": r["extension_check"]}, "CB occurrence")
    amb = regs["BEAM_OCCURRENCE_REGISTER"]["summary"]["ambiguous_tags"]
    add(10, "BEAMS", "ambiguous beam tags", "These tags sit between two parallel beams at similar distance. Which "
        "beam does each tag name?", amb, "simple-beam occurrences")
    same = [r["beam_id"] for r in regs["BEAM_OCCURRENCE_REGISTER"]["rows"] if "SAME_SPAN_CARRIES_TWO_TAGS" in r["issues"]]
    add(11, "BEAMS", "B3 (With Stair) vs CB3", "One span carries both 'B3 (With Stair)' and 'CB3'. Is B3 a separate "
        "stair beam beside CB3, or the same member?", same, "stair beam / CB3")
    untag = [r["beam_id"] for r in regs["BEAM_OCCURRENCE_REGISTER"]["rows"]
             if r["family"] == "OTHER" and r["binding"] == "NO_TAG"]
    add(12, "BEAMS", "untagged beam members", "Members drawn as beams with no tag - which type are they (or are they "
        "drop / edge details)?", untag, "simple-beam population")
    add(13, "GROUND_BEAMS", "GB category length basis", "GB category (<2.5 / <5 / >5 m): measured centre-to-centre of "
        "supports or clear span? These spans change category between the two.",
        [r["beam_id"] for r in regs["BEAM_OCCURRENCE_REGISTER"]["rows"]
         if r.get("category_state") == "AMBIGUOUS_LENGTH_BASIS"], "GB section")
    add(14, "SLABS", "temperature steel 160 / 180 mm", "The p.15 temperature table has rows 150 and 175 only. For "
        "160 mm and 180 mm slabs: which row (no interpolation is done)?", "P15-TEMP-TABLE", "temperature steel")
    add(15, "SLABS", "top steel over beams", "Plan note (pp.4-6): 5Ø10/m over beams for 1/3 span, vs p.15: top bars "
        "0.25L / 0.30L. Is the plan note a minimum where no top bar is drawn, or an override?", "P4-6-NOTE-2 vs "
        "P15-SLAB-ON-BEAMS", "slab top steel")
    siv = [r["panel_id"] for r in regs["SLAB_PANEL_REGISTER"]["rows"] if r["class"] == "STAIR_IN_VOID_ZONE"]
    add(15, "STAIRS", "stair inside a void", "These faces are drawn as open-to-below (X lines) but hold stair treads "
        "and a bar text (8Ø16/m). Is this the main stair well (stair slab + landings), and which stair detail applies?",
        siv, "stair concrete / stair bars")
    add(16, "LEVELS", "founding level / column heights", "Founding level is not printed (>= 1.5 m excavation). "
        "Confirm footing founding level and floor build-up, needed for column bar lengths next round.",
        "STRUCTURAL_LEVEL_REGISTER", "foundation-storey column length")
    add(17, "POOL", "pool dimensions", "Pool lengths / depths are 'AS PER ARCH'. Provide the architectural pool "
        "plan and section.", "p.7 detail", "pool occurrence geometry")
    q = sorted(q, key=lambda r: (r["rank"], str(r["item"])))
    for i, r in enumerate(q, 1):
        r["priority_group"], r["rank"] = r["rank"], i
    return register("STRUCTURAL_REVIEW_QUEUE", q,
                    {"items": len(q), "top_10": [f"{r['rank']}. {r['area']}: {r['item']}" for r in
                                                 sorted(q, key=lambda r: r["rank"])[:10]]})


# ============================================================================================ build + write
def build_all():
    B = S.build()
    src = B["src"]
    regs = {}
    regs["STRUCTURAL_PROJECT_RULE_REGISTER"] = rule_register()
    regs["STRUCTURAL_LEVEL_REGISTER"] = level_register(B)
    (regs["COLUMN_OCCURRENCE_REGISTER"], regs["COLUMN_TYPE_FLOOR_MATRIX"], regs["COLUMN_VERTICAL_CHAIN_REGISTER"],
     regs["COLUMN_DEFINITION_REGISTER"], regs["COLUMN_TIE_TOPOLOGY_RULES"]) = column_registers(B)
    (regs["FOOTING_OCCURRENCE_REGISTER"], regs["FOOTING_DEFINITION_REGISTER"],
     regs["FOOTING_REQUIRED_COMPONENT_REGISTER"]) = footing_registers(B)
    (regs["BEAM_OCCURRENCE_REGISTER"], regs["BEAM_TYPE_FLOOR_MATRIX"], regs["BEAM_DEFINITION_REGISTER"],
     regs["CONTINUOUS_BEAM_OCCURRENCE_REGISTER"], stair_quals) = beam_registers(B, src)
    (regs["SLAB_PANEL_REGISTER"], regs["SLAB_REBAR_SOURCE_REGISTER"], regs["SLAB_RULE_APPLICATION_MAP"],
     gs_notes) = slab_registers(B, src)
    regs["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"], regs["POOL_STRUCTURAL_REGISTER"] = special_registers(
        B, src, stair_quals, gs_notes, regs["SLAB_PANEL_REGISTER"])
    regs["STRUCTURAL_OCCURRENCE_CONSERVATION_REGISTER"] = conservation_register(B, src, regs)
    regs["STRUCTURAL_REVIEW_QUEUE"] = review_queue(B, regs)
    for r in regs.values():
        r["source"]["dxf_sha256"] = src.sha256
    return regs


def serialise(regs):
    return {name: dumps(regs[name]) for name in REGISTERS}


def write(texts, twice_identical=None):
    files = {}
    for name, txt in texts.items():
        p = OUT / f"{name}.json"
        p.write_text(txt, encoding="utf-8")
        files[name] = {"file": p.name, "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
                       "rows": len(json.loads(txt)["rows"])}
    idx = {"round": ROUND, "title": "Alsenan structural census S1 - source rules + occurrence census",
           "drawing": S.DRAWING, "frozen_before_benchmark": FROZEN_BEFORE_BENCHMARK,
           "built_twice_identical": twice_identical, "no_rebar_kg_calculated": True, "registers": files,
           "report": "ALSENAN_STRUCTURAL_CENSUS_S1.md"}
    (OUT / "INDEX.json").write_text(dumps(idx), encoding="utf-8")
    return idx


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--twice", action="store_true", help="build twice and require byte-identical registers")
    a = ap.parse_args(argv)
    t1 = serialise(build_all())
    same = None
    if a.twice:
        t2 = serialise(build_all())
        same = t1 == t2
        if not same:
            diff = [k for k in t1 if t1[k] != t2[k]]
            raise SystemExit(f"non-deterministic registers: {diff}")
    idx = write(t1, same)
    for k, v in idx["registers"].items():
        print(f"{k:48s} rows={v['rows']:5d} {v['sha256'][:12]}")
    return idx


if __name__ == "__main__":
    main()
