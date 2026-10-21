"""ALSENAN S5 - accurate ground-beam + strap-beam rebar through the generic engine (engine.source.ground_system_rebar).

    python3 -I research/alsenan_ground_system_rebar_s5/build_ground_system_rebar_s5.py

Blind build: reads ONLY controlled Urban registers, never a drawing and never a reference or an old total:
  * the frozen PRE-S5.1 package (exterior authority, FOLLOW ARCH depth, length basis, concentrated load, free ends,
    readiness matrix, provenance templates) - verified against its INDEX hashes first;
  * the frozen PRE-S5 strap registers (occurrences, strap schedule rows);
  * the R4 visual source claims (p.13 ground-beam sections) and project rule register (soil cover, the starter
    development note - recorded as NOT applicable to beam ends).
The engine never reinterprets geometry: every length, node, applicability and load state is taken from the registers.
Writes the S5 registers and S5_FREEZE_MANIFEST.json (code, inputs and outputs hashed). The post-freeze comparison is a
separate script that refuses to run unless this manifest still matches. Deterministic: two runs give identical bytes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import ground_system_rebar as GS  # noqa: E402

BASELINE = "cab778a"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
P51 = "research/pre_s5_1_source_resolution"
P50 = "research/pre_s5_ground_system_readiness"
R4 = "research/alsenan_rebar_source_exhaustion_04/registers"
CODE = ["engine/source/ground_system_rebar.py", "engine/source/ground_system_provenance.py",
        "engine/source/rebar_provenance.py", "engine/source/accurate_boq_rebar.py", "engine/source/rebar_model.py",
        "engine/source/rebar_unit_mass.py", "research/alsenan_ground_system_rebar_s5/build_ground_system_rebar_s5.py"]
INPUTS = [f"{P51}/03_EXTERIOR_AUTHORITY_REGISTER.csv", f"{P51}/04_FOLLOW_ARCH_DEPTH_REGISTER.csv",
          f"{P51}/05_LENGTH_BASIS_ANALYSIS.csv", f"{P51}/06_CONCENTRATED_LOAD_REGISTER.csv",
          f"{P51}/09_GROUND_BEAM_FREE_END_REGISTER.csv", f"{P51}/10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv",
          f"{P51}/S5_1_PROVENANCE_TEMPLATES.json", f"{P51}/PRE_S5_1_SUMMARY.json", f"{P51}/INDEX.json",
          f"{P50}/03_STRAP_OCCURRENCE_REGISTER.csv", f"{P50}/05_STRAP_REBAR_SOURCE_REGISTER.csv",
          f"{R4}/VISUAL_SOURCE_CLAIM_REGISTER.json", f"{R4}/PROJECT_REBAR_RULE_REGISTER.json"]
OUTPUTS = ["GROUND_SYSTEM_REBAR_OCCURRENCES.csv", "GROUND_SYSTEM_REBAR_COMPONENTS.csv", "GROUND_SYSTEM_BBS_NET.csv",
           "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json", "GROUND_SYSTEM_REBAR_UNRESOLVED.csv",
           "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", "GROUND_SYSTEM_ENGINEERING_FLAGS.csv",
           "GROUND_SYSTEM_ENGINEERING_QUESTIONS.csv", "GROUND_BEAM_REBAR_SUMMARY.csv", "STRAP_BEAM_REBAR_SUMMARY.csv",
           "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json"]
EXPECTED = {"GROUND_BEAM": 59, "STRAP_BEAM": 3}
EXPECTED_GB_RELEASE = {"LOWER_BOUND": 31, "BLOCKED": 28}            # PRE-S5.1 frozen scope (S5 brief section 6)
UNDEFINED_DETAIL = "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD"

# S5 engineering questions (S5 brief section 29); the PRE-S5.1 id each one continues
QUESTIONS = {
    "Q1": ("Q-L1", "Concentrated load: does a ground beam ending on another ground beam mid-span (or a stair start / "
                   "the '******' marks) count as a 'concentrated load' for the p.13 sections titled 'without "
                   "concentrated load'? Not auto-classified as PRESENT; the interior detail stays blocked."),
    "Q2": ("Q-D1", "Exterior ground-beam depth (FOLLOW ARCH.): the floor build-up is not printed (D <= 1.00 m main "
                   "block); the annex +0.30 bound (D <= 0.30 m) cannot hold the drawn three-level section - "
                   "SOURCE_CONFLICT. What is the depth?"),
    "Q3": ("Q-B1", "Length basis of the p.13 titles (clear span between support faces, or centreline)?"),
    "Q3B": ("Q-G1", "Bar run where the drawn band and the support faces disagree (narrow column, oblique / arc-trimmed "
                    "ends): measure to the support face plane and correct the concrete piece?"),
    "Q4": ("Q-N1", "Below 2.5 m both 'Less than 2.5m' and 'Less than 5m' hold: which governs, and what link (size, "
                   "spacing) has the 2.5 m section? (No stirrup is inherited from the 5 m section.)"),
    "Q5": ("Q-S2", "SB2 governing schedule row: 80x50 (10Ø18 / 10Ø18) or 100x50 (20Ø18 / 10Ø16)? The drawn 987 mm "
                   "width does not choose."),
    "Q6": ("Q-T1", "Link geometry: legs / topology, hook angle and extension of ground-beam and strap links."),
    "Q7": ("Q-A1", "Development / anchorage of ground-beam bars into columns, beams and footings and of strap bars into "
                   "footings (the p.8 70Ø / 40Ø note is for starters only; a code value needs the project's code)."),
    "Q8": ("Q-E1", "Partly exterior / mixed spans and slab-edge beams with no wall: which section applies?"),
    "Q9": ("Q-X1", "Meaning of the two '******' marks on the GBP sheet (S-TEXT, 300 mm, no legend)."),
    "Q10": ("Q-F1", "1811-1812 east end on the plot-boundary line, no column or footing: what supports it?"),
}
SYMBOL_EVIDENCE = "UNIDENTIFIED_SYMBOL"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(ROOT / p, encoding="utf-8")))


def _f(v):
    return None if v in (None, "") else float(v)


def _csv(path, rows, fields=None):
    buf = io.StringIO()
    fields = fields or list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else
                        ("" if v is None else (round(v, 6) if isinstance(v, float) else v))) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=float) + "\n",
                    encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ frozen inputs
def verify_pre_s5_1():
    idx = _j(f"{P51}/INDEX.json")
    bad = [o for o, h in idx["outputs"].items() if _sha(ROOT / P51 / o) != h]
    if bad:
        raise SystemExit(f"PRE-S5.1 package changed since its freeze: {bad}")
    return idx


def rules():
    rr = {r["rule_id"]: r for r in _j(f"{R4}/PROJECT_REBAR_RULE_REGISTER.json")["rules"]}
    cov = rr["COVER_AGAINST_SOIL_70MM"]
    dev = rr["DEVELOPMENT_STARTER_70D_40D"]
    if "STARTER_BARS" not in dev["applies_to"] or "GROUND_BEAM" in dev["applies_to"]:
        raise SystemExit("the starter development rule changed scope - re-open the S5 development decision")
    return {
        "cover": {"value_mm": cov["value"], "rule_id": cov["rule_id"], "claim_id": cov["claim_id"],
                  "authority": "SOURCE_EXPLICIT" if cov["source_state"] == "CROSS_VERIFIED_SOURCE" else "UNRESOLVED"},
        "development": {"state": GS.NOT_ESTABLISHED,
                        "why": "no beam-end anchorage rule in the project source; DEVELOPMENT_STARTER_70D_40D "
                               f"('{dev['scope']}', {dev['source_state']}) is not generalised; no 40D / 70D / ACI / "
                               "BS / EC2 / Kuwait-practice / Urban default is applied"},
        "bar_end_hooks": {"state": GS.NOT_ESTABLISHED,
                          "why": "bar ends at the supports are not detailed (R4 HOOKS_AND_BENDS = NO_PROJECT_SOURCE); "
                                 "no column-hook rule is borrowed"},
        "stirrup_hooks": {"state": GS.NOT_ESTABLISHED,
                          "why": "hook angle / extension NO_PROJECT_SOURCE (engineer / code decision; never verified)"},
        "stirrup_topology": {
            "GROUND_BEAM": {"state": "NOT_VERIFIED", "why": "the p.13 sections draw a closed link but leg count / "
                                                            "topology is not a verified facet"},
            "STRAP_BEAM": {"state": "NOT_STATED", "why": "the SBT schedule gives Ø and count per metre only; no "
                                                         "strap section sketch exists (pp.8, 13-16 searched)"}},
        "source_records": {"cover": cov, "development_starter_note": dev}}


def _auth(state):
    return "SOURCE_EXPLICIT" if state == "CROSS_VERIFIED_SOURCE" else \
        ("UNAPPROVED_METHOD" if state == "AI_VISUAL_TRANSCRIPTION" else "UNRESOLVED")


def definitions():
    cl = {c["claim_id"]: c for c in _j(f"{R4}/VISUAL_SOURCE_CLAIM_REGISTER.json")["claims"]}
    defs = {}
    gb = {"P13-GB-GT5M": ("P13-GB-GT5M", "P13-GB-GT5M", "lower_rows"),
          "P13-GB-LT5M": ("P13-GB-LT5M", "P13-GB-LT5M", "lower_rows"),
          "P13-GB-LT2_5M": ("P13-GB-LT2_5M-BARS", "P13-GB-LT2_5M-SECTION", "lower_rows"),
          "P13-GB-EXTERIOR": ("P13-GB-EXTERIOR", "P13-GB-EXTERIOR", "bottom_rows")}
    for did, (bars_id, sec_id, rows_key) in gb.items():
        b, s = cl[bars_id], cl[sec_id]
        v, sv = b["value"], s["value"]
        rows = v[rows_key]
        if len(rows) != 2:
            raise SystemExit(f"{did}: expected two lower rows, got {rows}")
        st = v.get("stirrup")
        defs[did] = {
            "detail_id": did, "family": "GROUND_BEAM",
            "source_handles": [f"R4-CLAIM:{c}" for c in dict.fromkeys((bars_id, sec_id))],
            "source_text": b["raw_visual_transcription"], "sheet_region": f"ST7757.pdf p.{b['page']} ground-beam sections",
            "authority": {"longitudinal": _auth(b["source_state"]), "stirrup": _auth(b["source_state"]),
                          "section": _auth(s["source_state"])},
            "longitudinal": {"TOP_MAIN": list(v["top"]), "BOTTOM_ROW_1": list(rows[0]), "BOTTOM_ROW_2": list(rows[1])},
            "side": v.get("side"),
            "stirrup": None if st is None else {"dia_mm": st[0], "mode": "SPACING_MM", "value": st[1]},
            "end_zone": None, "extras": [],
            "section": {"B_mm": sv.get("B_mm"), "D_mm": sv.get("D_mm"), "D_state": s["source_state"]}}
    for r in _rows(f"{P50}/05_STRAP_REBAR_SOURCE_REGISTER.csv"):
        if not r["SOURCE_ID"].startswith("SBT:"):
            continue
        c = json.loads(r["CONTENT"])
        defs[r["SOURCE_ID"]] = {
            "detail_id": r["SOURCE_ID"], "family": "STRAP_BEAM", "source_handles": json.loads(r["HANDLES"]),
            "source_text": f"SBT {c['BEAM']}: W {c['W']} H {c['H']} TOP {c['TOP-B']}Ø{c['TOP-D']} BOT "
                           f"{c['BOT-B']}Ø{c['BOT-D']} STIRRUPS {c['STI-B']}Ø{c['D']}/m",
            "sheet_region": r["LOCATION"],
            "authority": {"longitudinal": "SOURCE_EXPLICIT", "stirrup": "SOURCE_EXPLICIT", "section": "SOURCE_EXPLICIT"},
            "longitudinal": {"TOP_MAIN": [int(c["TOP-B"]), int(c["TOP-D"])],
                             "BOTTOM_ROW_1": [int(c["BOT-B"]), int(c["BOT-D"])], "BOTTOM_ROW_2": None},
            "side": None, "stirrup": {"dia_mm": int(c["D"]), "mode": "BARS_PER_METRE", "value": int(c["STI-B"])},
            "end_zone": None, "extras": [],
            "section": {"B_mm": int(c["W"]) * 10, "D_mm": int(c["H"]) * 10, "D_state": "SOURCE_EXPLICIT"}}
    return defs


def _gb_depth(occ_id, ids, defs, arch):
    a = arch.get(occ_id)
    defined = [d for d in ids if d in defs]
    if len(defined) != len(ids):
        return {"state": "UNRESOLVED", "value_mm": None, "bound_max_m": None,
                "candidates": {d: (defs[d]["section"]["D_mm"] if d in defs else "UNKNOWN") for d in ids},
                "why": "an undefined candidate detail"}
    depths = {}
    for d in defined:
        if d == "P13-GB-EXTERIOR":
            depths[d] = "FOLLOW_ARCH"
        else:
            sec = defs[d]["section"]
            depths[d] = sec["D_mm"] if sec["D_state"] == "CROSS_VERIFIED_SOURCE" else f"{sec['D_mm']} (AI only)"
    vals = set(map(str, depths.values()))
    if len(vals) > 1:
        return {"state": "CANDIDATE_CONFLICT", "value_mm": None, "bound_max_m": None, "candidates": depths,
                "why": "candidate sections differ in depth"}
    v = depths[defined[0]]
    if v == "FOLLOW_ARCH":
        if a is None:
            return {"state": "UNRESOLVED", "value_mm": None, "bound_max_m": None, "candidates": depths,
                    "why": "FOLLOW ARCH. with no level register row"}
        mx = _f(a["DERIVED_DEPTH_MAX_M"])
        flagged = any("DEPTH_BOUND_BELOW_TYPICAL_SECTION" in fl for fl in json.loads(a["FLAGS"]))
        if flagged:
            return {"state": "SOURCE_CONFLICT", "value_mm": None, "bound_max_m": mx, "candidates": depths,
                    "why": "annex +0.30: the level bound (D <= 0.30 m) cannot hold the drawn three-level section; "
                           "no 300 mm depth is adopted"}
        if a["OUTCOME"] == "BOUNDED" and mx is not None:
            return {"state": "BOUNDED_ABOVE", "value_mm": None, "bound_max_m": mx, "candidates": depths,
                    "why": a["DERIVATION"]}
        return {"state": "UNRESOLVED", "value_mm": None, "bound_max_m": None, "candidates": depths,
                "why": f"FOLLOW ARCH. {a['OUTCOME']}"}
    if isinstance(v, str):
        return {"state": "AI_TRANSCRIPTION_ONLY", "value_mm": None, "bound_max_m": None, "candidates": depths,
                "why": "section depth is an AI transcription only"}
    return {"state": "SOURCE_EXPLICIT" if len(defined) == 1 else "CANDIDATE_INVARIANT", "value_mm": v,
            "bound_max_m": None, "candidates": depths, "why": "cross-verified section depth"}


def _width(ids, defs):
    if not ids or any(d not in defs for d in ids):
        return {"state": "UNRESOLVED", "value_mm": None, "candidates": {d: (defs[d]["section"]["B_mm"] if d in defs
                                                                              else "UNKNOWN") for d in ids}}
    ws = {d: defs[d]["section"]["B_mm"] for d in ids}
    if len(set(ws.values())) > 1:
        return {"state": "CANDIDATE_CONFLICT", "value_mm": None, "candidates": ws}
    return {"state": "SOURCE_EXPLICIT" if len(ids) == 1 else "CANDIDATE_INVARIANT", "value_mm": next(iter(ws.values())),
            "candidates": ws}


def occurrences(defs):
    tmpl = {t["ELEMENT_OCCURRENCE_ID"]: t for t in _j(f"{P51}/S5_1_PROVENANCE_TEMPLATES.json")["templates"]}
    matrix = defaultdict(dict)
    for r in _rows(f"{P51}/10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv"):
        matrix[r["OCCURRENCE_ID"]][r["COMPONENT"]] = r
    length = {r["GB_SPAN_ID"]: r for r in _rows(f"{P51}/05_LENGTH_BASIS_ANALYSIS.csv")}
    ext = {r["GB_SPAN_ID"]: r for r in _rows(f"{P51}/03_EXTERIOR_AUTHORITY_REGISTER.csv")}
    arch = {r["GB_SPAN_ID"]: r for r in _rows(f"{P51}/04_FOLLOW_ARCH_DEPTH_REGISTER.csv")}
    load = {r["GB_SPAN_ID"]: r for r in _rows(f"{P51}/06_CONCENTRATED_LOAD_REGISTER.csv")}
    free = defaultdict(dict)
    for r in _rows(f"{P51}/09_GROUND_BEAM_FREE_END_REGISTER.csv"):
        free[r["GB_SPAN_ID"]][r["END"]] = r
    straps = {r["STRAP_OCCURRENCE_ID"]: r for r in _rows(f"{P50}/03_STRAP_OCCURRENCE_REGISTER.csv")}
    occs = []
    for oid, m in sorted(matrix.items()):
        t = tmpl[oid]
        m0 = m["TOP_MAIN"]
        fam = t["ELEMENT_FAMILY"]
        ids = list(t["DETAIL_ID"])
        if ids != json.loads(m0["REBAR_DETAIL_ID"]) or t["DETAIL_APPLICABILITY_STATE"] != m0["DETAIL_APPLICABILITY"]:
            raise SystemExit(f"{oid}: template and readiness matrix disagree on the detail")
        flags, questions, node_issues = [], {}, {}
        if fam == "GROUND_BEAM":
            L, e, ld = length[oid], ext[oid], load[oid]
            issues = json.loads(L["LENGTH_ISSUES"])
            consistent = L["LENGTH_STATE"] == "CONSISTENT"
            lengths = {"centreline_m": _f(L["MEMBER_CENTERLINE_LENGTH_M"]),
                       "clear_concrete_m": _f(L["MEMBER_CLEAR_CONCRETE_LENGTH_M"]),
                       "face_to_face_m": _f(L["SUPPORT_FACE_TO_FACE_RUN_M"]),
                       "bar_run_lb_m": _f(L["BAR_STRAIGHT_RUN_LOWER_BOUND_M"]) if L["BAR_RUN_STATE"] == "LOWER_BOUND"
                       else None,
                       "length_state": L["LENGTH_STATE"], "bar_run_state": L["BAR_RUN_STATE"], "issues": issues,
                       "stirrup_distribution_m": _f(L["SUPPORT_FACE_TO_FACE_RUN_M"]) if consistent else None,
                       "stirrup_distribution_basis": "SUPPORT_FACE_TO_FACE_RUN"}
            depth = _gb_depth(oid, ids, defs, arch)
            width = _width(ids, defs)
            kinds = json.loads(ld["EVIDENCE_KINDS"])
            app_q = []
            if UNDEFINED_DETAIL in ids:
                app_q.append("Q1")
                if SYMBOL_EVIDENCE in kinds:
                    app_q.append("Q9")
            if e["EXTERIOR_AUTHORITY"] not in ("EXTERIOR_SOURCE_VERIFIED", "INTERIOR_SOURCE_VERIFIED"):
                app_q.append("Q8")
            if L["SAME_RESULT"] == "False":
                app_q.append("Q3")
            if {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= set(ids):
                app_q.append("Q4")
            questions = {"applicability": "+".join(app_q) or None, "depth": "Q2", "bar_run": "Q3B",
                         "stirrup_supersession": "Q4" if {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= set(ids) else
                         ("+".join(app_q) or None), "stirrup_geometry": "Q6", "development": "Q7", "end": "Q10"}
            for end_key, n in (("start", "1"), ("end", "2")):
                fr = free[oid].get(end_key)
                if fr and fr["CLASSIFICATION"] in ("BOUNDARY", "FREE_END"):
                    node_issues[n] = f"{fr['CLASSIFICATION']} {fr['SUPPORT_REF']}: {fr['WHY']}"
                    flags.append(f"FREE_END_UNRESOLVED end {n}: {node_issues[n]}")
                elif fr:
                    flags.append(f"FREE_END_CLASSIFIED end {n}: {fr['CLASSIFICATION']} {fr['SUPPORT_REF']} "
                                 f"({fr['WHY']})")
            if not consistent:
                flags.append(f"{L['LENGTH_STATE']}: {'; '.join(issues)}")
            if L["SAME_RESULT"] == "False":
                flags.append("LENGTH_BASIS_CHANGES_DETAIL: clear / centreline / clear-concrete give "
                             f"{L['DETAIL_BY_CLEAR_LENGTH']} / {L['DETAIL_BY_CENTRELINE_LENGTH']} / "
                             f"{L['DETAIL_BY_CLEAR_CONCRETE_LENGTH']}")
            if depth["state"] == "SOURCE_CONFLICT":
                flags.append(f"ANNEX_DEPTH_SOURCE_CONFLICT: {depth['why']}")
            if ld["LOAD_STATE"] == "UNKNOWN":
                flags.append(f"CONCENTRATED_LOAD_UNKNOWN: evidence {kinds}; not auto-classified as PRESENT")
            sheet = "ST7757.dxf GBP (ground-beam plan)"
            why_candidate = f"exterior authority {e['EXTERIOR_AUTHORITY']} ({e['WHY']}); load {ld['LOAD_STATE']}; " \
                            f"length details {L['DETAIL_BY_CLEAR_LENGTH']}"
            why_not = "" if len(ids) == 1 else (
                f"{len(ids)} candidates: " + ("concentrated-load case has no project detail; " if UNDEFINED_DETAIL
                                              in ids else "") +
                ("exterior / interior not resolved; " if "P13-GB-EXTERIOR" in ids else "") +
                ("<2.5 m and <5 m titles both hold" if {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= set(ids) else "")).strip()
            mark = t["ELEMENT_MARK"]
        else:
            s = straps[oid]
            clear = _f(s["CLEAR_CONCRETE_LENGTH_M"])
            run = _f(m0["BAR_STRAIGHT_RUN_LOWER_BOUND_M"])
            if run != clear:
                raise SystemExit(f"{oid}: strap bar run {run} != clear concrete length {clear}")
            lengths = {"centreline_m": _f(s["CENTERLINE_SUPPORT_TO_SUPPORT_M"]), "clear_concrete_m": clear,
                       "face_to_face_m": clear, "bar_run_lb_m": run, "length_state": m0["LENGTH_STATE"],
                       "bar_run_state": "LOWER_BOUND", "issues": [],
                       "stirrup_distribution_m": clear if m0["LENGTH_STATE"] == "CONSISTENT" else None,
                       "stirrup_distribution_basis": "CLEAR_CONCRETE_LENGTH between footing faces"}
            width = _width(ids, defs)
            ds = {d: defs[d]["section"]["D_mm"] for d in ids}
            depth = {"state": ("SOURCE_EXPLICIT" if len(ids) == 1 else "CANDIDATE_INVARIANT")
                     if len(set(ds.values())) == 1 else "CANDIDATE_CONFLICT",
                     "value_mm": next(iter(ds.values())) if len(set(ds.values())) == 1 else None,
                     "bound_max_m": None, "candidates": ds, "why": "SBT schedule H"}
            flags = list(json.loads(s["FLAGS"]))
            if len(ids) > 1:
                flags.append(f"SB2_SECTION_CONFLICT: rows {ids} give widths {width['candidates']} mm; drawn width "
                             f"{s['WIDTH_DRAWN_MM']} mm is recorded and NOT used to choose")
            questions = {"applicability": "Q5" if len(ids) > 1 else None, "stirrup_geometry": "Q6",
                         "development": "Q7", "depth": None, "bar_run": None, "stirrup_supersession": "Q5"}
            sheet = "ST7757.dxf FP (foundation plan, PDF p.2)"
            why_candidate = f"SBT schedule key {t['ELEMENT_MARK']}: rows {ids}"
            why_not = "duplicated SBT schedule key: two rows, different bars and widths; the drawn width does not " \
                      "choose" if len(ids) > 1 else ""
            mark = t["ELEMENT_MARK"]
            for k, end_key in (("start_support", "START_SUPPORT"), ("end_support", "END_SUPPORT")):
                sup = json.loads(s[end_key])
                if "|" in str(sup.get("footing_type")):
                    flags.append(f"{end_key}_FOOTING_TYPE_CONFLICT {sup['footing_type']} at {sup['footing']}: "
                                 "preserved in provenance; the development into this footing stays blocked")
        occs.append({"occurrence_id": oid, "family": fam, "mark": mark, "drawing_sha": t["DRAWING_SHA"],
                     "sheet_region": sheet, "start_node": t["START_NODE"], "end_node": t["END_NODE"],
                     "geometry_handles": t["GEOMETRY_HANDLES"], "lengths": lengths, "width": width, "depth": depth,
                     "detail_ids": ids, "applicability": t["DETAIL_APPLICABILITY_STATE"],
                     "why_candidate": why_candidate, "why_not_resolved": why_not, "node_issues": node_issues,
                     "questions": questions, "flags": flags,
                     "_pre": {"exterior": m0["EXTERIOR_AUTHORITY"], "load": m0["LOAD_STATE"],
                              "pre_s5_1_status": m0["OCCURRENCE_S5_STATUS"]}})
    return occs, matrix


# PRE-S5.1 matrix component that each S5 component may only release under (do-not-widen check)
MATRIX_OF = {"TOP_MAIN": "TOP_MAIN", "BOTTOM_ROW_1": "BOTTOM_ROW_1", "BOTTOM_ROW_2": "BOTTOM_ROW_2",
             "BOTTOM_MAIN": "BOTTOM_ROW_1", "STIRRUP_DIAMETER": "STIRRUP_DIAMETER", "STIRRUP_SPACING": "STIRRUP_RATE",
             "STIRRUP_COUNT": "STIRRUP_COUNT", "SIDE_REBAR": "SIDE_BARS", "STIRRUP_CORE_PATH": "STIRRUP_CORE_PATH"}


def scope_check(res, matrix):
    """S5 never widens the frozen PRE-S5.1 scope: a released S5 component must be READY / READY_LOWER_BOUND there.
    Also lists where S5 is narrower (released there, not here)."""
    widened, narrower = [], []
    for c in res["components"]:
        mc = MATRIX_OF.get(c["component"])
        if mc is None:
            if c["state"] in ("VERIFIED", "LOWER_BOUND"):
                widened.append((c["occurrence_id"], c["component"], "no PRE-S5.1 row"))
            continue
        pre = matrix[c["occurrence_id"]][mc]["S5_STATUS"]
        rel = c["state"] in ("VERIFIED", "LOWER_BOUND")
        if rel and pre not in ("READY", "READY_LOWER_BOUND"):
            widened.append((c["occurrence_id"], c["component"], pre))
        if not rel and pre in ("READY", "READY_LOWER_BOUND"):
            narrower.append((c["occurrence_id"], c["component"], pre, c["state"]))
    return widened, narrower


def main():
    verify_pre_s5_1()
    R = rules()
    defs = definitions()
    occs, matrix = occurrences(defs)
    ctx = {"PROJECT_ID": "ALSENAN-ST7757", "DRAWING_ID": "ST7757.dxf", "DRAWING_SHA": DRAWING_SHA,
           "REVISION": "ALSENAN_ST7757_DXF", "ENGINE_COMMIT": f"{BASELINE}+code:{code_digest()[:16]}",
           "REGISTER_VERSION": "GROUND_SYSTEM_REBAR_REGISTER_V1", "CALCULATION_ROUND": "S5",
           "unit_mass": {"method": "D2_OVER_162", "authority": "Urban project default (R3)"}}
    engine_occs = [{k: v for k, v in o.items() if not k.startswith("_")} for o in occs]
    res = GS.run(engine_occs, defs, {k: R[k] for k in ("cover", "development", "bar_end_hooks", "stirrup_hooks",
                                                        "stirrup_topology")}, ctx)
    if not res["conservation"]["all_pass"]:
        raise SystemExit(f"conservation failed: {res['conservation']['checks']}")
    fam_n = Counter(r["family"] for r in res["occurrences"])
    if dict(fam_n) != EXPECTED:
        raise SystemExit(f"occurrence population {dict(fam_n)} != {EXPECTED}")
    gb_rel = Counter(r["occurrence_state"] for r in res["occurrences"] if r["family"] == "GROUND_BEAM")
    if dict(gb_rel) != EXPECTED_GB_RELEASE:
        raise SystemExit(f"ground-beam release {dict(gb_rel)} != frozen PRE-S5.1 scope {EXPECTED_GB_RELEASE}")
    widened, narrower = scope_check(res, matrix)
    if widened:
        raise SystemExit(f"S5 would widen the frozen PRE-S5.1 scope: {widened}")
    occ_by = {o["occurrence_id"]: o for o in occs}

    # ---------------------------------------------------------------------------------------------- registers
    register = [dict(r, lengths=occ_by[r["occurrence_id"]]["lengths"], width=occ_by[r["occurrence_id"]]["width"],
                     depth=occ_by[r["occurrence_id"]]["depth"], questions=occ_by[r["occurrence_id"]]["questions"],
                     node_issues=occ_by[r["occurrence_id"]]["node_issues"], pre_s5_1=occ_by[r["occurrence_id"]]["_pre"])
                for r in res["occurrences"]]
    _json(HERE / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json", {
        "register": "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER", "policy": GS.policy_record(), "context": ctx,
        "rules": R, "definitions": defs, "occurrences": register,
        "scope_check": {"widened": widened, "narrower_than_pre_s5_1": narrower}})
    occ_fields = ["occurrence_id", "family", "mark", "occurrence_state", "known_kg", "known_straight_length_m",
                  "stirrup_count_lower_bound", "unquantified_components", "components_by_state", "start_node",
                  "end_node", "geometry_handles", "member_centerline_length_m", "member_clear_concrete_length_m",
                  "support_face_to_face_run_m", "bar_straight_run_lower_bound_m", "length_state", "width_mm",
                  "width_state", "depth_mm", "depth_state", "depth_bound_max_m", "detail_ids",
                  "detail_applicability_state", "why_candidate", "why_not_resolved", "drawing_sha",
                  "register_version", "flags"]
    _csv(HERE / "GROUND_SYSTEM_REBAR_OCCURRENCES.csv",
         [dict(r, drawing_sha=DRAWING_SHA, register_version=ctx["REGISTER_VERSION"]) for r in res["occurrences"]],
         occ_fields)
    comp_fields = ["occurrence_id", "family", "mark", "component", "accurate_component", "quantity_kind", "state",
                   "dia_mm", "bar_count", "straight_run_m", "total_length_m", "kg_per_m", "kg", "count",
                   "count_convention_not_adopted", "distribution_m", "value", "unit", "candidate_invariant",
                   "candidate_values", "missing", "missing_facets", "node_kind", "question_id", "why"]
    _csv(HERE / "GROUND_SYSTEM_REBAR_COMPONENTS.csv", res["components"], comp_fields)
    _csv(HERE / "GROUND_SYSTEM_BBS_NET.csv", res["bbs"])
    unresolved = [c for c in res["components"] if c["state"] in ("BLOCKED_UNQUANTIFIED", "BLOCKED_MODELLED",
                                                                 "LOWER_BOUND")]
    _csv(HERE / "GROUND_SYSTEM_REBAR_UNRESOLVED.csv", [
        {"occurrence_id": c["occurrence_id"], "family": c["family"], "mark": c["mark"], "component": c["component"],
         "quantity_kind": c["quantity_kind"], "state": c["state"],
         "what_is_missing": c.get("missing") or c["why"], "question_id": c.get("question_id") or "",
         "known_kg": c["kg"], "known_count": c.get("count")} for c in unresolved])
    with open(HERE / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for c in sorted(res["components"], key=lambda z: (z["occurrence_id"], z["component"])):
            f.write(json.dumps({"record_id": f"{c['occurrence_id']}:{c['component']}", "state": c["state"],
                                "quantity_kind": c["quantity_kind"], "kg": c["kg"], "count": c.get("count"),
                                "is_accurate_part": c["quantity_kind"] == GS.MASS and c["state"] in
                                ("VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED_MODELLED", "BLOCKED_UNQUANTIFIED"),
                                "provenance": c["provenance"]}, sort_keys=True, ensure_ascii=False) + "\n")
    flags = []
    for r in register:
        for fl in r["flags"]:
            flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "occurrence_id": r["occurrence_id"],
                          "family": r["family"], "mark": r["mark"], "flag": fl,
                          "effect_on_release": ("BLOCKS_LONGITUDINAL" if fl.startswith(("LENGTH_GEOMETRY",
                                                                                        "BAR_RUN_GEOMETRY"))
                                                else "BLOCKS_THE_INTERIOR_DETAIL" if fl.startswith("CONCENTRATED")
                                                and UNDEFINED_DETAIL in r["detail_ids"]
                                                else "BLOCKS_DEPTH_DEPENDENT_COMPONENTS" if fl.startswith("ANNEX")
                                                else "BLOCKS_LONGITUDINAL_AND_STIRRUP_PATH" if fl.startswith("SB2")
                                                else "BLOCKS_END_TREATMENT" if fl.startswith("FREE_END_UNRESOLVED")
                                                else "NONE (recorded in provenance)")})
    _csv(HERE / "GROUND_SYSTEM_ENGINEERING_FLAGS.csv", flags)
    q_use = defaultdict(set)
    for c in res["components"]:
        for q in (c.get("question_id") or "").split("+"):
            if q:
                q_use[q].add(c["occurrence_id"])
    _csv(HERE / "GROUND_SYSTEM_ENGINEERING_QUESTIONS.csv", [
        {"question_id": q, "continues": QUESTIONS[q][0], "question": QUESTIONS[q][1],
         "occurrences_blocked_or_bounded": len(q_use.get(q, ())), "occurrences": sorted(q_use.get(q, ())),
         "answer": "OPEN (not invented; known components are not held back while waiting)"}
        for q in QUESTIONS])
    for fam, name in (("GROUND_BEAM", "GROUND_BEAM_REBAR_SUMMARY.csv"), ("STRAP_BEAM", "STRAP_BEAM_REBAR_SUMMARY.csv")):
        _csv(HERE / name, [{k: r[k] for k in occ_fields if k in r} for r in res["occurrences"] if r["family"] == fam],
             [k for k in occ_fields if k not in ("drawing_sha", "register_version")])
    s = res["summary"]
    dia, dia_len = Counter(), Counter()
    for c in res["components"]:
        if c["kg"] is not None:
            dia[c["dia_mm"]] += c["kg"]
            dia_len[c["dia_mm"]] += c["total_length_m"]
    comp_counts = Counter((c["family"], c["component"], c["state"]) for c in res["components"])
    s.update(conservation=res["conservation"], context=ctx,
             headline_lines=["KNOWN SOURCE-DERIVED GROUND-SYSTEM REBAR", s["final_ground_system_rebar"]],
             diameter_distribution={str(k): {"kg": dia[k], "length_m": dia_len[k]} for k in sorted(dia)},
             total_source_derived_straight_length_m=sum(dia_len.values()),
             component_population={f"{f}:{c}:{st}": n for (f, c, st), n in sorted(comp_counts.items())},
             provenance={"records": len(res["components"]), "accurate_parts": len(res["parts"]),
                         "validated": len(res["components"]),
                         "contract": "rebar_provenance generic identity + ground_system_provenance S5 fields; mass "
                                     "parts also validate_s5_part"},
             scope_check={"widened": len(widened), "narrower_than_pre_s5_1": narrower},
             questions_open=sorted(QUESTIONS))
    _json(HERE / "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json", s)
    manifest = {"round": "S5", "baseline": BASELINE, "state": "FROZEN_BEFORE_REFERENCE_COMPARISON",
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "engine_commit_stamp": ctx["ENGINE_COMMIT"],
                "references_read_before_freeze": [],
                "rule": "the post-freeze comparison script refuses to run unless every hash above still matches; a "
                        "correction found by the comparison needs a new issue, new evidence, a new regression and a "
                        "new version - never an edit of these outputs and never a tuning to a reference"}
    _json(HERE / "S5_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({"known_kg": s["known_source_derived_ground_system_rebar_kg"],
                      "final": s["final_ground_system_rebar"],
                      "families": {f: {k: v[k] for k in ("occurrences_by_state", "LOWER_BOUND_KNOWN_KG",
                                                         "BLOCKED_UNQUANTIFIED_COMPONENTS",
                                                         "stirrup_counts_quantified")}
                                   for f, v in s["families"].items()},
                      "narrower": len(narrower)}, indent=1, default=float))


if __name__ == "__main__":
    main()
