"""URBAN PROJECTS AD1 - owner authority decisions recorded before D1.1, and their effect on the frozen releases.

    python3 -I research/ad1_authority_decisions/build_ad1_authority_decisions.py

The earlier Q2 answers were the assistant's own engineering analysis, not answers from the project engineer or
consultant. This round:
  1. records the owner's nine authority decisions (OWNER_AUTHORITY_DECISION, versioned). The Q2 analysis is recorded
     as CLAUDE_ENGINEERING_ANALYSIS: it is never promoted to a PROJECT_ENGINEER_CLAIM or a project source, and no
     confidence percentage is carried;
  2. lists the analysis / code values the decisions refuse;
  3. checks every frozen release (S4, S5, S6, S4.1, S6.1, S5.1) against each decision;
  4. writes the corrections the decisions require, without editing any frozen file:
       - AUTHORITY_STATE_ERRATA (0 kg) where a frozen facet carries a state a decision does not allow;
       - CORRECTION_ERRATA (engine.source.delta_correction) where frozen kg rests on applicability that a decision
         withdraws (the concentrated-reaction ruling on two ground-beam spans).
Blind: frozen Urban registers only. No code value, donor, benchmark or other engine is read. Deterministic.
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

from engine.source import authority_decisions as AD  # noqa: E402
from engine.source import delta_correction as DC  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402

ROUND = "AD1"
POLICY = "AUTHORITY_DECISIONS_V1"
RECORDED = "2026-10-08"
BASELINE_HEAD = "cbcbb36"
R = ROOT / "research"
S4, S5, S6 = R / "alsenan_footing_rebar_s4", R / "alsenan_ground_system_rebar_s5", R / "alsenan_superstructure_beam_rebar_s6"
S41, S51, S61 = (R / "alsenan_footing_rebar_s4_1", R / "alsenan_ground_system_rebar_s5_1",
                 R / "alsenan_superstructure_beam_rebar_s6_1")
P51 = R / "pre_s5_1_source_resolution"
P6 = R / "pre_s6_superstructure_beam_readiness"
SRD = R / "source_recovery_delta"
R4 = R / "alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json"
MANIFESTS = {"S4": S4 / "S4_FREEZE_MANIFEST.json", "S5": S5 / "S5_FREEZE_MANIFEST.json",
             "S6": S6 / "S6_FREEZE_MANIFEST.json", "S4.1": S41 / "S4_1_FREEZE_MANIFEST.json",
             "S6.1": S61 / "S6_1_FREEZE_MANIFEST.json", "S5.1": S51 / "S5_1_FREEZE_MANIFEST.json"}
CODE = ["engine/source/authority_decisions.py", "engine/source/delta_correction.py", "engine/source/delta_release.py",
        "research/ad1_authority_decisions/build_ad1_authority_decisions.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + [
    "research/pre_s5_1_source_resolution/03_EXTERIOR_AUTHORITY_REGISTER.csv",
    "research/pre_s5_1_source_resolution/04_FOLLOW_ARCH_DEPTH_REGISTER.csv",
    "research/pre_s5_1_source_resolution/05_LENGTH_BASIS_ANALYSIS.csv",
    "research/pre_s5_1_source_resolution/06_CONCENTRATED_LOAD_REGISTER.csv",
    "research/pre_s6_superstructure_beam_readiness/07_BEAM_SIDE_REBAR_READINESS.csv",
    "research/alsenan_rebar_source_exhaustion_04/registers/PROJECT_REBAR_RULE_REGISTER.json",
    "research/source_recovery_delta/01_ENGINEER_PROJECT_CLAIM.json"]
OUTPUTS = ["00_README.md", "01_AUTHORITY_DECISIONS.json", "02_REJECTED_ANALYSIS_VALUES.csv",
           "03_COMPLIANCE_REGISTER.csv", "04_AUTHORITY_STATE_ERRATA.csv", "05_S5_AD1_CORRECTIONS.csv",
           "06_GB_CONCENTRATED_REACTION_REGISTER.csv", "07_AD1_SUMMARY.json", "08_PROVENANCE.jsonl"]
CLAUSE_DETAILS = ("P13-GB-GT5M", "P13-GB-LT5M")       # titles carrying 'without concentrated load' (pre-S5.1)
EXTERIOR_DETAIL = "P13-GB-EXTERIOR"
LT2_5M = "P13-GB-LT2_5M"


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"AD1 check failed: {what}")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _csv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(r.get(k), sort_keys=True, ensure_ascii=False) if isinstance(r.get(k), (list, dict))
                        else ("" if r.get(k) is None else (round(r[k], 6) if isinstance(r.get(k), float) else r[k])))
                    for k in fields})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode() + b"\0" + (ROOT / c).read_bytes() + b"\0")
    return h.hexdigest()


# ------------------------------------------------------------------ 1. the decisions (owner text, 2026-10-08)
def decisions():
    D = AD.decision
    return [
        D(decision_id="AD-1", topic="BOXED (footings)", recorded=RECORDED,
          rulings={"COMPONENT_EXISTENCE": AD.SOURCE_EXPLICIT,
                   "INVERTED_U_TOPOLOGY": AD.SOURCE_EXPLICIT,
                   "HOOKS": AD.NOT_ESTABLISHED,
                   "MEANING_OF_3_PLUS_N": AD.PROJECT_PATTERN_ONLY,
                   "DIAMETER": AD.SOURCE_EXPECTED_NOT_LOCATED,
                   "EXISTENCE_WHERE_FN_CELL_BLANK": AD.UNRESOLVED,
                   "KG": AD.BLOCKED_UNQUANTIFIED},
          scope_notes={"INVERTED_U_TOPOLOGY": "where proven by vector geometry",
                       "HOOKS": "earlier source-recovery evidence did not establish hooks on BOXED"},
          forbids=["importing hooks from another bar", "reading a blank FN cell as NOT_REQUIRED"]),
        D(decision_id="AD-2", topic="70Ø / 40Ø note", recorded=RECORDED,
          rulings={"NOTE_SCOPE": AD.CONTEXT_RESTRICTED,
                   "BEAM_ANCHORAGE_FROM_NOTE": AD.NOT_A_PROJECT_RULE,
                   "GROUND_BEAM_ANCHORAGE_FROM_NOTE": AD.NOT_A_PROJECT_RULE},
          preserves=["the note's established starter / development context"],
          forbids=["generalising the note to beam or ground-beam anchorage", "a universal beam anchorage rule"]),
        D(decision_id="AD-3", topic="Beam end bends", recorded=RECORDED,
          rulings={"EXPLICIT_BEND_SHAPE": AD.SOURCE_EXPLICIT_SHAPE_ONLY,
                   "UNDIMENSIONED_LEG_LENGTH": AD.NOT_ESTABLISHED},
          forbids=["12Ø legs", "legs from the beam depth", "generic practice to create kg"]),
        D(decision_id="AD-4", topic="Stirrup hooks", recorded=RECORDED,
          rulings={"HOOK_ANGLE_TOPOLOGY": AD.SOURCE_EXPLICIT_SHAPE_ONLY,
                   "HOOK_EXTENSION": AD.BLOCKED_UNQUANTIFIED,
                   "CODE_HOOK_VALUES": AD.QA_ONLY},
          scope_notes={"HOOK_EXTENSION": "blocked unless the project source dimensions it"},
          forbids=["a 20d allowance", "an ACI hook value in the Accurate BOQ"]),
        D(decision_id="AD-5", topic="Ground beam LESS THAN 2.5M", recorded=RECORDED,
          rulings={"STIRRUP_DIAMETER": AD.SOURCE_EXPECTED_NOT_LOCATED,
                   "STIRRUP_RATE": AD.SOURCE_EXPECTED_NOT_LOCATED},
          forbids=["inheriting Ø8/15 from another project detail"]),
        D(decision_id="AD-6", topic="WITHOUT CONCENTRATED LOAD", recorded=RECORDED,
          rulings={"BEAM_FRAMING_INTO_SPAN_BETWEEN_SUPPORTS": AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION,
                   "PLANTED_COLUMN_LOAD": AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION},
          scope_notes={"PROVENANCE": "engineering-derived applicability logic, not a claimed drawing note; "
                                     "project source and engineering derivation stay distinguished"},
          forbids=["recording the derivation as a drawing note"]),
        D(decision_id="AD-7", topic="FOLLOW ARCH", recorded=RECORDED,
          rulings={"ARCHITECTURAL_LEVELS": AD.BOUND_ONLY,
                   "EXACT_STRUCTURAL_BEAM_DEPTH": AD.NOT_ESTABLISHED,
                   "PLAIN_CONCRETE_10CM_IN_RC_DEPTH": AD.NOT_A_PROJECT_RULE},
          forbids=["publishing 0.9-1.0 m as an accurate depth", "counting 10 cm plain concrete as RC beam depth"]),
        D(decision_id="AD-8", topic="Continuous beams", recorded=RECORDED,
          rulings={"RULE_0_22_LN": AD.RETAINED_WHERE_SOURCE_ESTABLISHED,
                   "RULE_0_3_LN2": AD.UNRESOLVED,
                   "RULE_0_15_L": AD.UNRESOLVED,
                   "NTS_GRAPHIC_SCALE": AD.NOT_A_PROJECT_RULE,
                   "TOP_AND_HANGER_ROLES": AD.UNRESOLVED,
                   "RATE_5PHI8_PER_M": AD.RATE_COUNT_ONLY},
          scope_notes={"TOP_AND_HANGER_ROLES": "kept separate wherever the source association is ambiguous",
                       "RATE_5PHI8_PER_M": "establishes rate / count only, never the stirrup cut length"},
          forbids=["reading an NTS graphic scale"]),
        D(decision_id="AD-9", topic="Side / middle reinforcement", recorded=RECORDED,
          rulings={"SIDE_SKIN_CLASSIFICATION": AD.CLASSIFIED_SIDE_SKIN_REINFORCEMENT,
                   "CEIL_H_OVER_S_MINUS_1": AD.NOT_A_PROJECT_RULE,
                   "FIRST_LAST_ROW_EDGE_SPACING": AD.UNRESOLVED,
                   "SIDE_BAR_COUNT_AND_KG": AD.BLOCKED_UNQUANTIFIED},
          scope_notes={"SIDE_SKIN_CLASSIFICATION": "only where the project's MIDDLE REINF. field and notes support "
                                                   "it; count / kg stay blocked unless deterministically established "
                                                   "from project source geometry"},
          forbids=["adopting ceil(h/s) - 1 as a project rule"]),
    ]


def prior_analysis_record():
    return {"RECORD_ID": "Q2-PRIOR-ANALYSIS", "PROVENANCE": AD.CLAUDE_ENGINEERING_ANALYSIS,
            "ENGINEER_CONFIRMATION": "NONE", "PROMOTED_TO": None, "CONFIDENCE_CARRIED": False,
            "STATEMENT": "the earlier Q2 answers were the assistant's own engineering analysis, not answers from the "
                         "project engineer or consultant; no engineer confirmation exists for those items"}


def rejected_values():
    V = AD.analysis_value
    C, X = AD.CLAUDE_ENGINEERING_ANALYSIS, AD.CODE_OR_EXTERNAL
    return [
        V(value_id="RV-01", topic="BOXED hooks", value="hooks imported from another footing bar", decision_id="AD-1",
          provenance=C),
        V(value_id="RV-02", topic="BOXED FN blank", value="blank FN cell read as NOT_REQUIRED", decision_id="AD-1",
          provenance=C),
        V(value_id="RV-03", topic="beam / ground-beam anchorage", value="note 9 70Ø / 40Ø generalised to beam ends",
          decision_id="AD-2", provenance=C),
        V(value_id="RV-04", topic="beam end leg", value="12Ø leg", decision_id="AD-3", provenance=X),
        V(value_id="RV-05", topic="beam end leg", value="leg = h - 2c - 2 d_link - (d_top + d_bottom) / 2",
          decision_id="AD-3", provenance=C),
        V(value_id="RV-06", topic="stirrup hook", value="20d hook allowance", decision_id="AD-4", provenance=X),
        V(value_id="RV-07", topic="stirrup hook", value="ACI hook extension", decision_id="AD-4", provenance=X),
        V(value_id="RV-08", topic="stirrup link path", value="sharp-corner core path with hooks offsetting the bends",
          decision_id="AD-4", provenance=C),
        V(value_id="RV-09", topic="GB < 2.5 m stirrups", value="Ø8/15 inherited from another detail",
          decision_id="AD-5", provenance=C),
        V(value_id="RV-10", topic="FOLLOW ARCH depth", value="0.9-1.0 m published as the beam depth",
          decision_id="AD-7", provenance=C),
        V(value_id="RV-11", topic="FOLLOW ARCH depth", value="10 cm plain concrete counted in the RC depth",
          decision_id="AD-7", provenance=C),
        V(value_id="RV-12", topic="CB extensions", value="0.3 Ln2 / 0.15L given a numeric length",
          decision_id="AD-8", provenance=C),
        V(value_id="RV-13", topic="CB lengths", value="lengths read off the NTS graphic scale", decision_id="AD-8",
          provenance=X),
        V(value_id="RV-14", topic="side bars", value="count = ceil(h / s) - 1", decision_id="AD-9", provenance=X),
    ]


# ------------------------------------------------------------------ 2. engineer-claim scan
def engineer_claims():
    found = []
    for p in sorted(R.rglob("*.json")):
        try:
            txt = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if '"PROJECT_ENGINEER_CLAIM"' not in txt:
            continue
        try:
            obj = json.loads(txt)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("kind") == "PROJECT_ENGINEER_CLAIM":
            found.append({"path": str(p.relative_to(ROOT)), "claim_id": obj.get("claim_id"),
                          "authorises_assumptions": obj.get("authorises_assumptions"), "effect": obj.get("effect")})
    check(len(found) == 1 and found[0]["claim_id"] == "PEC-CLAIM-2026-10-08-01", "one engineer claim on record")
    check(found[0]["authorises_assumptions"] is False, "the engineer claim authorises no assumption")
    return found


# ------------------------------------------------------------------ 3. compliance checks
def _facets(r):
    try:
        return json.loads(r["FACETS"] or "{}")
    except json.JSONDecodeError:
        return {}


def ad1_boxed(errata, comp):
    rows = [r for r in _rows(S41 / "S4_1_DELTA_COMPONENTS.csv") if r["COMPONENT"] == "BOXED"]
    with_shape = [r for r in rows if "SHAPE" in _facets(r)]
    fn = [r for r in with_shape if "FN cell blank" in _facets(r).get("EXISTENCE", "")]
    explicit = [r for r in with_shape if r not in fn]
    check(all(float(r["NEW_KNOWN_QUANTITY"] or 0) == 0 for r in rows), "BOXED carries no kg")
    check(all(_facets(r)["DIAMETER"].startswith("SOURCE_EXPECTED_NOT_LOCATED") for r in with_shape), "BOXED diameter")
    check(all("E-PDF-01" in r["EVIDENCE_IDS"] and "inverted_U" in r["SOURCE_HANDLES"] for r in with_shape),
          "BOXED inverted U rests on the p.13 vector strokes")
    for r in with_shape:
        f = _facets(r)
        tid = r["BASELINE_COMPONENT_ID"]
        if "no hooks" in f["SHAPE"]:
            errata.append(AD.facet_erratum(
                errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=tid, facet="HOOKS",
                old_state="SOURCE_FOUND_EXPLICIT (inverted U ... no hooks)", new_state=AD.NOT_ESTABLISHED,
                decision_id="AD-1", evidence=f"S4.1 {r['DELTA_ID']} SHAPE facet; source recovery did not establish "
                                             "hooks on BOXED, absence is not asserted either", STAGE="S4.1",
                SOURCE_DELTA_ID=r["DELTA_ID"]))
        errata.append(AD.facet_erratum(
            errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=tid, facet="MEANING_OF_3_PLUS_N",
            old_state=f["MEANING_OF_3_PLUS_N"], new_state=AD.PROJECT_PATTERN_ONLY, decision_id="AD-1",
            evidence="the '3+n' cells are a recurring project pattern; no source states their meaning", STAGE="S4.1",
            SOURCE_DELTA_ID=r["DELTA_ID"]))
        if r in fn:
            errata.append(AD.facet_erratum(
                errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=tid, facet="EXISTENCE",
                old_state=f["EXISTENCE"], new_state=AD.UNRESOLVED, decision_id="AD-1",
                evidence="blank FN cell: UNRESOLVED, not NOT_REQUIRED; the inverted U applies only if the component "
                         "exists", STAGE="S4.1", SOURCE_DELTA_ID=r["DELTA_ID"]))
    comp.append(("AD-1", "S4 / S4.1", "BOXED existence, inverted-U shape, diameter, kg", "COMPLIANT",
                 len(with_shape), 0.0, f"{len(explicit)} printed '3+n' cells SOURCE_FOUND_EXPLICIT; inverted U from "
                 "p.13 S-REIN.D vectors (E-PDF-01); diameter SOURCE_EXPECTED_NOT_LOCATED; kg 0"))
    comp.append(("AD-1", "S4.1", "BOXED hooks", "STATE_ERRATUM", len(with_shape), 0.0,
                 "the SHAPE facet said 'no hooks'; hooks are NOT_ESTABLISHED (neither present nor absent)"))
    comp.append(("AD-1", "S4.1", "BOXED 3+n meaning", "STATE_ERRATUM", len(with_shape), 0.0,
                 "SOURCE_EXPECTED_NOT_LOCATED -> PROJECT_PATTERN_ONLY"))
    comp.append(("AD-1", "S4.1", "BOXED existence where the FN cell is blank", "STATE_ERRATUM", len(fn), 0.0,
                 "SOURCE_EXPECTED_NOT_LOCATED -> UNRESOLVED (never NOT_REQUIRED)"))
    return {"boxed_rows": len(rows), "with_shape": len(with_shape), "fn_blank": len(fn)}


def ad2_note9(comp):
    rule = next(r for r in _j(R4)["rules"] if r["rule_id"] == "DEVELOPMENT_STARTER_70D_40D")
    check(rule["applies_to"] == ["STARTER_BARS"], "note 9 applies to starter bars")
    s5 = (S5 / "build_ground_system_rebar_s5.py").read_text(encoding="utf-8")
    s6 = (S6 / "build_superstructure_beam_rebar_s6.py").read_text(encoding="utf-8")
    check("is not generalised" in s5 and "starter-bar context only" in s6, "S5 / S6 keep note 9 out of beam ends")
    anch = 0.0
    for p, key in ((S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv", "accurate_component"),
                   (S6 / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv", "accurate_component")):
        anch += sum(float(r["kg"] or 0) for r in _rows(p) if r[key] == "ANCHORAGE")
    check(anch == 0.0, "no anchorage kg in S5 / S6")
    comp.append(("AD-2", "S5 / S6 / S5.1 / S6.1", "note 9 kept to its starter context", "COMPLIANT", 0, 0.0,
                 "development rule NOT_ESTABLISHED in S5 and S6; anchorage kg 0; the S5.1 through-support runs use "
                 "no anchorage length"))
    comp.append(("AD-2", "R4 (superseded lineage)", "LAP-70D-NOTE9-EXTENDED procurement label", "LINEAGE_NOTE", 0,
                 0.0, "the old R4 register used the note for BBS laps as a labelled procurement assumption; it is "
                 "not in the accurate S-series product and may not be revived"))
    return {"rule": rule["rule_id"], "scope": rule["scope"]}


def ad3_end_bends(errata, comp):
    rows = _rows(S61 / "S6_1_DELTA_COMPONENTS.csv")
    legs = [r for r in rows if r["CHANGE_KIND"] == DR.TOPOLOGY_RECORDED and r["COMPONENT"] in ("HOOK_1", "HOOK_2")]
    check(legs and all(float(r["DELTA_KNOWN_QUANTITY"] or 0) == 0 for r in legs), "CB end legs carry no kg")
    for r in legs:
        check("leg geometry derivable" in r["NEW_COMPONENT_MODEL"], f"{r['DELTA_ID']} model text")
        errata.append(AD.facet_erratum(
            errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=r["BASELINE_COMPONENT_ID"], facet="LEG_LENGTH",
            old_state="derivable = h - 2c - 2 d_link - (d_top + d_bottom) / 2 (recorded, not released)",
            new_state=AD.NOT_ESTABLISHED, decision_id="AD-3",
            evidence="the 90° leg is drawn but not dimensioned; a leg length from the beam depth is not admissible",
            STAGE="S6.1", SOURCE_DELTA_ID=r["DELTA_ID"]))
        errata.append(AD.facet_erratum(
            errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=r["BASELINE_COMPONENT_ID"], facet="LEG_SHAPE",
            old_state="SHAPE_FOUND_LENGTH_BLOCKED", new_state=AD.SOURCE_EXPLICIT_SHAPE_ONLY, decision_id="AD-3",
            evidence="a graphically explicit 90° turn-down establishes shape only", STAGE="S6.1",
            SOURCE_DELTA_ID=r["DELTA_ID"]))
    bends = [r for r in rows if r["PORTION"] in ("END_BENDS", "END_HOOK_1", "END_HOOK_2", "CRANK_EXCESS",
                                                 "CRANK_DIAGONAL_EXCESS")]
    check(all(float(r["DELTA_KNOWN_QUANTITY"] or 0) == 0 for r in bends), "end bends / cranks carry no kg")
    extra = next(r for r in rows if r["PORTION"] == "STRAIGHT_PROJECTION")
    check("'DEPTH' dimension" in extra["WHY"] and "horizontal projection" in extra["NEW_COMPONENT_MODEL"],
          "the planted-column extra rests on the printed DEPTH dimension")
    comp.append(("AD-3", "S6.1", "CB end-support legs", "STATE_ERRATUM", len(legs), 0.0,
                 "recorded as 'derivable' from the beam depth; now LEG_LENGTH NOT_ESTABLISHED, LEG_SHAPE "
                 "SOURCE_EXPLICIT_SHAPE_ONLY; 0 kg before and after"))
    comp.append(("AD-3", "S6.1", "B3 end bends, B26 crank diagonal and end hooks", "COMPLIANT", len(bends), 0.0,
                 "shape found, length blocked; 0 kg"))
    comp.append(("AD-3", "S6.1", "B26 planted-column extra", "COMPLIANT", 1, float(extra["DELTA_KNOWN_QUANTITY"]),
                 "the p.15 detail dimensions the extension with its own 'DEPTH' label bound to the schedule depth: a "
                 "printed dimension, released over the horizontal projection only (crank excess and hooks blocked)"))
    return {"cb_end_legs": len(legs), "bends": len(bends)}


def ad4_hooks(comp):
    s61 = _rows(S61 / "S6_1_DELTA_COMPONENTS.csv")
    hooks = [r for r in s61 if r["PORTION"] == "HOOK_EXTENSION"]
    check(hooks and all(r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED" and
                        float(r["DELTA_KNOWN_QUANTITY"] or 0) == 0 for r in hooks), "S6.1 link hooks shape-only")
    s5 = [r for r in _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv") if r["component"].startswith("STIRRUP_HOOK")]
    check(s5 and all(r["state"] == "BLOCKED_UNQUANTIFIED" for r in s5), "S5 stirrup hooks blocked")
    for p in (ROOT / "engine/source/ground_system_rebar.py", ROOT / "engine/source/superstructure_beam_rebar.py",
              S51 / "build_ground_system_rebar_s5_1.py", S61 / "build_superstructure_beam_rebar_s6_1.py"):
        src = p.read_text(encoding="utf-8")
        check("20d" not in src and "20 d " not in src, f"no 20d allowance in {p.name}")
    comp.append(("AD-4", "S6.1", "link hooks", "COMPLIANT", len(hooks), 0.0,
                 "drawn hooks recorded as shape; extension not printed -> blocked"))
    comp.append(("AD-4", "S5 / S5.1", "ground-beam and strap stirrup hooks", "COMPLIANT", len(s5), 0.0,
                 "BLOCKED_UNQUANTIFIED; no code / note default"))
    core = [r for p in (S61 / "S6_1_DELTA_COMPONENTS.csv", S51 / "S5_1_DELTA_COMPONENTS.csv") for r in _rows(p)
            if r["CHANGE_KIND"] == DR.QUANTITY_RELEASED and r["PORTION"] == "CORE_PATH"]
    core_kg = sum(_j(p)["delta_by_kind_kg"]["stirrup_core_path"] for p in (S61 / "S6_1_RELEASE_SUMMARY.json",
                                                                           S51 / "S5_1_RELEASE_SUMMARY.json"))
    comp.append(("AD-4", "D1 -> D1.1", "sharp-corner link path that relied on the hooks", "KG_ERRATUM", len(core),
                 core_kg, "retracted by the D1.1 S6_1A / S5_1A errata (rebuilt on top of AD1)"))
    return {"s61_hooks": len(hooks), "s5_hooks": len(s5)}


def ad5_lt25(comp):
    occ = {o["occurrence_id"]: o for o in _j(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}
    lt = {k for k, o in occ.items() if LT2_5M in o["detail_ids"]}
    st = [r for r in _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")
          if r["occurrence_id"] in lt and r["component"] in ("STIRRUP_DIAMETER", "STIRRUP_SPACING")]
    check(st and all(r["state"] == "BLOCKED_UNQUANTIFIED" and not r["dia_mm"] and not r["value"] for r in st),
          "GB < 2.5 m stirrup diameter / rate not inherited")
    comp.append(("AD-5", "S5 / S5.1", "GB < 2.5 m stirrup diameter and rate", "COMPLIANT", len(lt), 0.0,
                 f"{len(lt)} spans carry the <2.5 m candidate; diameter and spacing BLOCKED_UNQUANTIFIED, no Ø8/15"))
    return sorted(lt)


def ad6_loads(errata, corrections, comp):
    occ = {o["occurrence_id"]: o for o in _j(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}
    load = {r["GB_SPAN_ID"]: r for r in _rows(P51 / "06_CONCENTRATED_LOAD_REGISTER.csv")}
    basis = {r["GB_SPAN_ID"]: r for r in _rows(P51 / "05_LENGTH_BASIS_ANALYSIS.csv")}
    ext = {r["GB_SPAN_ID"]: r for r in _rows(P51 / "03_EXTERIOR_AUTHORITY_REGISTER.csv")}
    comp_rows = _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")
    s51 = {r["BASELINE_COMPONENT_ID"]: r for r in _rows(S51 / "S5_1_DELTA_COMPONENTS.csv")}
    s51_released = {r["OCCURRENCE_ID"] for r in s51.values() if r["CHANGE_KIND"] == DR.QUANTITY_RELEASED}
    reg = []
    for oid in sorted(basis):
        o, ld, L, e = occ[oid], load[oid], basis[oid], ext[oid]
        kinds = json.loads(ld["EVIDENCE_KINDS"])
        st = AD.concentrated_reaction(kinds, ld["LOAD_STATE"])
        old = sorted(o["detail_ids"])
        if e["EXTERIOR_AUTHORITY"] == "EXTERIOR_SOURCE_VERIFIED":
            new, why = old, "exterior section verified: it carries no load clause"
        elif st["STATE"] == AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION:
            bases = [json.loads(L[k]) for k in ("DETAIL_BY_CLEAR_LENGTH", "DETAIL_BY_CENTRELINE_LENGTH",
                                                 "DETAIL_BY_CLEAR_CONCRETE_LENGTH")]
            always = [EXTERIOR_DETAIL] if e["EXTERIOR_AUTHORITY"] != "INTERIOR_SOURCE_VERIFIED" else []
            new = AD.loaded_candidates(bases, CLAUSE_DETAILS, always)
            why = ("a beam frames into the span between its supports: the 'without concentrated load' sections do "
                   "not apply; per length basis only the unclaused details remain")
        else:
            new, why = old, "no beam framing between the supports and no planted column: load state unchanged"
        kg = float(o["known_kg"] or 0)
        survives = AD.release_survives(old, new)
        released = [r for r in comp_rows if r["occurrence_id"] == oid and r["kg"] and float(r["kg"]) > 0]
        effect = ("NONE" if new == old else
                  "KG_RETRACTED" if released and not survives else
                  "CANDIDATES_NARROWED" if survives and new != old else "STATE_ONLY")
        reg.append({"GB_SPAN_ID": oid, "MARK": o["mark"], "EVIDENCE_KINDS": kinds, "FROZEN_LOAD_STATE": ld["LOAD_STATE"],
                    "AD6_LOAD_STATE": st["STATE"], "AD6_PROVENANCE": st["PROVENANCE"],
                    "EXTERIOR_AUTHORITY": e["EXTERIOR_AUTHORITY"], "FROZEN_CANDIDATES": old, "AD6_CANDIDATES": new,
                    "NO_DETAIL_CASE": AD.NO_DETAIL_IF_LOADED in new, "FROZEN_KNOWN_KG": kg,
                    "FROZEN_RELEASE_SURVIVES": survives if released else "", "EFFECT": effect,
                    "S5_1_RELEASE_ON_SPAN": oid in s51_released, "WHY": why})
        if st["CHANGED"]:
            errata.append(AD.facet_erratum(
                errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=oid, facet="CONCENTRATED_LOAD_STATE",
                old_state=ld["LOAD_STATE"], new_state=AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION,
                decision_id="AD-6", evidence=f"{ld['EVIDENCE']} (engineering-derived applicability, not a drawing "
                                             "note)", STAGE="pre-S5.1 / S5", PROVENANCE=AD.ENGINEERING_DERIVED,
                AD6_CANDIDATES=new))
        if effect == "KG_RETRACTED":
            check(oid not in s51_released, f"{oid}: no S5.1 release rests on a retracted span")
            for r in released:
                cid = f"{oid}:{r['component']}"
                carry = s51[cid]
                check(carry["CHANGE_KIND"] == DR.NO_CHANGE, f"{cid} carried unchanged into S5.1")
                corrections.append(DC.correction(
                    correction_id=f"S5.AD1-C{len(corrections) + 1:03d}", original_delta_component_id=cid,
                    original_kg=float(r["kg"]), correction_kg=-float(r["kg"]),
                    correction_reason="applicability withdrawn: under the AD-6 concentrated-reaction ruling one length "
                                      "basis has no project detail for this loaded span, so the bars are not "
                                      "candidate-invariant",
                    source_evidence=f"06_CONCENTRATED_LOAD_REGISTER {ld['EVIDENCE']}; 05_LENGTH_BASIS_ANALYSIS "
                                    f"clear {L['DETAIL_BY_CLEAR_LENGTH']} / centreline "
                                    f"{L['DETAIL_BY_CENTRELINE_LENGTH']} / clear-concrete "
                                    f"{L['DETAIL_BY_CLEAR_CONCRETE_LENGTH']}",
                    new_authority_state=DC.QA_ONLY, new_release_state=DC.BLOCKED_UNQUANTIFIED,
                    STAGE="S5 (carried into S5.1)", ORIGINAL_DELTA_ID=carry["DELTA_ID"], OCCURRENCE_ID=oid,
                    MARK=o["mark"], COMPONENT=r["component"], DECISION_ID="AD-6",
                    FROZEN_CANDIDATES=old, AD6_CANDIDATES=new, PROVENANCE=AD.ENGINEERING_DERIVED))
    changed = [r for r in reg if r["FROZEN_CANDIDATES"] != r["AD6_CANDIDATES"]]
    kgx = sum(c["ORIGINAL_KG"] for c in corrections)
    comp.append(("AD-6", "pre-S5.1 / S5", "ground-beam load state", "STATE_ERRATUM",
                 sum(1 for r in reg if r["AD6_LOAD_STATE"] == AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION), 0.0,
                 "UNKNOWN -> ENGINEERING_DERIVED_CONCENTRATED_REACTION where a beam frames into the span between its "
                 "supports (a junction at a support, an unidentified symbol or a stair candidate change nothing)"))
    comp.append(("AD-6", "S5 (carried into S5.1)", "kg on spans whose loaded case has no project detail",
                 "KG_ERRATUM", len(corrections), kgx,
                 "GSO-142-7D8-1 and GSO-15D-7C8-1: the bars agreed between the <2.5 m and <5 m sections, but the "
                 "<5 m section is 'without concentrated load' and one length basis gives only that section"))
    comp.append(("AD-6", "S5.1", "through-support runs and link releases", "COMPLIANT", 0, 0.0,
                 "every through-support run lies on exterior-verified spans (no load clause); the S5.1 link spans "
                 "are not reclassified"))
    comp.append(("AD-6", "S6 / S6.1", "planted-column load on superstructure beams", "COMPLIANT", 0, 0.0,
                 "no superstructure beam detail carries a 'without concentrated load' clause; B26 base and planted "
                 "extra come from its own schedule row and the p.15 planted-column detail"))
    return reg, changed


def ad7_follow_arch(comp):
    occ = _j(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]
    fa = [o for o in occ if "FOLLOW_ARCH" in json.dumps(o["depth"])]
    check(fa and all(o["depth_mm"] is None for o in fa), "no FOLLOW ARCH depth published")
    bounds = Counter(o["depth_bound_max_m"] for o in fa)
    arch = _rows(P51 / "04_FOLLOW_ARCH_DEPTH_REGISTER.csv")
    check(all(r["DERIVED_DEPTH_MIN_M"] in ("", None) for r in arch), "no lower depth bound published")
    comp.append(("AD-7", "pre-S5.1 / S5", "FOLLOW ARCH depth", "COMPLIANT", len(fa), 0.0,
                 f"depth_mm empty on all {len(fa)} spans; architectural levels give an upper bound only "
                 f"({dict(bounds)}), a bound on the full height above natural ground that may include any plain-concrete "
                 "layer and is never an RC depth; no 0.9-1.0 m depth; the known kg on these spans is straight bar "
                 "run, independent of depth"))
    return {"follow_arch_spans": len(fa), "bounds": {str(k): v for k, v in bounds.items()}}


def ad8_cb(comp):
    c = _rows(S6 / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv")
    mid = [r for r in c if r["component"] == "MID_TOP" and r["state"] == "LOWER_BOUND"]
    top_sup = [r for r in c if "0.3 Ln2" in r["why"] + r["missing"]]
    check(all(float(r["kg"] or 0) == 0 for r in top_sup), "0.3 Ln2 bars carry no kg")
    src = (S6 / "build_superstructure_beam_rebar_s6.py").read_text(encoding="utf-8")
    check("0.15L) adds no length" in src, "0.15L adds no length")
    hang = [r for r in c if r["component"] in ("HANGER", "TOP_HANGER")]
    check(all(float(r["kg"] or 0) == 0 for r in hang), "hangers carry no kg")
    comp.append(("AD-8", "S6", "0.22 Ln MID top bars", "COMPLIANT", len(mid), sum(float(r["kg"]) for r in mid),
                 "retained: the CB typical prints 0.22 Ln on these bars"))
    comp.append(("AD-8", "S6", "0.3 Ln2 / 0.15L / NTS scale / top-hanger roles", "COMPLIANT", len(top_sup), 0.0,
                 "0.3 Ln2 and 0.15L add no length; no graphic scale is read; frame top bars and hangers stay "
                 "blocked where the bar association is ambiguous"))
    comp.append(("AD-8", "S6.1", "CB7 5Ø8/m", "COMPLIANT", 2, 0.0,
                 "39 / 41 stirrups are a rate x run count; the cut length was retracted by D1.1"))
    return {"mid_top_released": len(mid)}


def ad9_side(errata, comp):
    side = _rows(P6 / "07_BEAM_SIDE_REBAR_READINESS.csv")
    field = {r["TYPE"]: r for r in side if r["COLUMN"] == "MIDDLE REINT." and r["TOKEN_RAW"]}
    rem = {r["TYPE"]: r for r in side if r["COLUMN"] == "REMARKS" and r["TOKEN_RAW"]}
    c = [r for r in _rows(S6 / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv") if r["component"] == "SIDE_REBAR"]
    check(all(float(r["kg"] or 0) == 0 for r in c), "side bars carry no kg")
    n = 0
    for r in c:
        t = field.get(r["mark"])
        if r["state"] != "BLOCKED_UNQUANTIFIED" or not t:
            continue
        check(float(t["DEPTH_CM"]) >= float(t["NOTE_THRESHOLD_CM"]), f"{r['mark']}: P8-N21 applies")
        n += 1
        errata.append(AD.facet_erratum(
            errata_id=f"AD1-E{len(errata) + 1:03d}", target_id=r["record_id"], facet="SIDE_BAR_ROLE",
            old_state="NOT_ESTABLISHED ('/30cm' semantics, Q6)", new_state=AD.CLASSIFIED_SIDE_SKIN_REINFORCEMENT,
            decision_id="AD-9", evidence=f"'{t['TOKEN_RAW']}' printed in the MIDDLE REINT. field; P8-N21 side-bar "
                                         f"note (depth {t['DEPTH_CM']} cm >= {t['NOTE_THRESHOLD_CM']} cm); count, "
                                         "edge spacing and kg stay blocked",
            STAGE="S6"))
    comp.append(("AD-9", "S6", "side-bar role where the MIDDLE REINT. field carries the token", "STATE_ERRATUM", n,
                 0.0, "classified as side / skin reinforcement; count, edge spacing and kg BLOCKED_UNQUANTIFIED; "
                      "ceil(h/s) - 1 not adopted"))
    comp.append(("AD-9", "S6", "side-bar tokens in the REMARKS column", "COMPLIANT",
                  sum(1 for r in c if r["state"] == "BLOCKED_UNQUANTIFIED" and r["mark"] in rem), 0.0,
                 "not the MIDDLE REINF. field: role stays NOT_ESTABLISHED; kg blocked"))
    comp.append(("AD-9", "S5", "ground-beam side rebar", "COMPLIANT",
                  sum(1 for r in _rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv") if r["component"] == "SIDE_REBAR"),
                  0.0, "BLOCKED_UNQUANTIFIED or NOT_APPLICABLE; no count rule"))
    return {"classified": n, "remarks_tokens": len(rem)}


README = """# AD1: owner authority decisions, recorded before D1.1

**Round:** `{round}` · **Policy:** `{policy}` · **Recorded:** {recorded} · **Baseline:** `{head}` · **Built by** `build_ad1_authority_decisions.py` (blind, byte-identical rebuild)

S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged. Every frozen manifest was hash-checked before anything was read.
D1.1 is rebuilt on top of this round.

## Where the earlier Q2 answers stand

The Q2 answers were the assistant's own engineering analysis, recorded here as `CLAUDE_ENGINEERING_ANALYSIS`.
- They are **not** answers from the project engineer or consultant.
- No engineer confirmation exists for them.
- They are never promoted to a `PROJECT_ENGINEER_CLAIM` or to project-source authority.
- No confidence percentage from that analysis is carried anywhere.

The only engineer claim on record is `PEC-CLAIM-2026-10-08-01`. It says only that the information sits in the
issued set, and it authorises no assumption.

`02_REJECTED_ANALYSIS_VALUES.csv` names {n_rv} analysis or code values that the decisions refuse. Each is QA only and
is never a quantity basis.

## The nine decisions (`01_AUTHORITY_DECISIONS.json`)

| | Topic | Ruling |
|---|---|---|
| AD-1 | BOXED | existence and the vector-proven inverted U are SOURCE_EXPLICIT; hooks NOT_ESTABLISHED; 3+n PROJECT_PATTERN_ONLY; diameter SOURCE_EXPECTED_NOT_LOCATED; blank FN cell UNRESOLVED; kg blocked |
| AD-2 | 70Ø / 40Ø | starter / development context only; no beam or ground-beam anchorage rule |
| AD-3 | Beam end bends | a drawn bend gives shape; an undimensioned leg gives no length; no 12Ø, beam depth or practice |
| AD-4 | Stirrup hooks | drawn angle / topology is shape only; extension blocked; no 20d; code values QA only |
| AD-5 | GB < 2.5 m | stirrup diameter and rate SOURCE_EXPECTED_NOT_LOCATED; Ø8/15 never inherited |
| AD-6 | WITHOUT CONCENTRATED LOAD | a beam framing in between the supports, or a planted column, is an ENGINEERING_DERIVED_CONCENTRATED_REACTION |
| AD-7 | FOLLOW ARCH | levels give bounds only; no exact depth; no 0.9-1.0 m; 10 cm plain concrete is not RC depth |
| AD-8 | Continuous beams | 0.22 Ln kept where printed; 0.3 Ln2 and 0.15L unresolved; no NTS scale; top / hanger roles separate; 5Ø8/m is rate / count only |
| AD-9 | Side bars | classified as side / skin only where the MIDDLE REINF. field and notes support it; no ceil(h/s) - 1; count and kg blocked |

## What the decisions change in the frozen releases (`03_COMPLIANCE_REGISTER.csv`)

**Known steel retracted: {kgx:.2f} kg on S5, carried into S5.1 (AD-6).**
- On GSO-142-7D8-1 and GSO-15D-7C8-1 a ground beam frames into the span between its supports.
- The bars released there were the ones the <2.5 m and <5 m sections agree on. The <5 m section is titled 'without
  concentrated load'.
- On at least one length basis, only the <5 m section applies. For that loaded span there is then no project
  detail, so the bars are not candidate-invariant.
- {n_corr} components are moved to QA_ONLY / BLOCKED_UNQUANTIFIED in `05_S5_AD1_CORRECTIONS.csv`.
- S5.1 known goes from {s51:.2f} to {s51c:.2f} kg before the D1.1 link errata.

**Authority-state errata, 0 kg ({n_err} rows in `04_AUTHORITY_STATE_ERRATA.csv`):**
- BOXED: hooks NOT_ESTABLISHED (was "no hooks"), 3+n PROJECT_PATTERN_ONLY, blank FN cells UNRESOLVED.
- {n_legs} CB end-support legs: length NOT_ESTABLISHED (was "derivable from the beam depth"), shape only.
- {n_load} ground-beam spans: load state ENGINEERING_DERIVED_CONCENTRATED_REACTION. Of these, {n_changed} have a
  different candidate-detail set (`06_GB_CONCENTRATED_REACTION_REGISTER.csv`).
- {n_side} continuous beams: the MIDDLE REINT. token is classified as side / skin reinforcement (count and kg stay
  blocked).

**Already compliant:**
- AD-2: note 9 stays starter-only.
- AD-4: link hooks shape-only; the hook-reliant D1 link path is retracted by D1.1.
- AD-5: GB < 2.5 m stirrups blocked.
- AD-7: no FOLLOW ARCH depth published.
- AD-8: 0.22 Ln kept; 0.3 Ln2 and 0.15L add nothing.
- AD-9: no side-bar count rule.
- The B26 planted-column extra, B3 / B26 base bars, the S5.1 through-support runs and the CB7 counts are untouched.

## Files

| File | Content |
|---|---|
| `01_AUTHORITY_DECISIONS.json` | the nine decisions, the Q2 analysis record, the engineer-claim scan, the policy |
| `02_REJECTED_ANALYSIS_VALUES.csv` | analysis / code values the decisions refuse |
| `03_COMPLIANCE_REGISTER.csv` | every decision checked against every frozen stage |
| `04_AUTHORITY_STATE_ERRATA.csv` | 0 kg facet-state corrections |
| `05_S5_AD1_CORRECTIONS.csv` | CORRECTION_ERRATA for the AD-6 kg |
| `06_GB_CONCENTRATED_REACTION_REGISTER.csv` | every ground-beam span: load state, candidate details before / after |
| `07_AD1_SUMMARY.json` | counts, kg, conservation, flags |
| `08_PROVENANCE.jsonl` | one line per decision, rejected value, erratum and correction |
| `AD1_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
"""


def main():
    frozen = {k: DR.verify_frozen(p, ROOT) for k, p in MANIFESTS.items()}
    decs = decisions()
    check([d["DECISION_ID"] for d in decs] == [f"AD-{i}" for i in range(1, 10)], "nine decisions")
    prior = prior_analysis_record()
    rvs = rejected_values()
    pec = engineer_claims()
    errata, corrections, comp = [], [], []
    boxed = ad1_boxed(errata, comp)
    note9 = ad2_note9(comp)
    bends = ad3_end_bends(errata, comp)
    hooks = ad4_hooks(comp)
    lt25 = ad5_lt25(comp)
    reg, changed = ad6_loads(errata, corrections, comp)
    arch = ad7_follow_arch(comp)
    cb = ad8_cb(comp)
    side = ad9_side(errata, comp)
    s5 = _j(S5 / "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json")["known_source_derived_ground_system_rebar_kg"]
    s51 = _j(S51 / "S5_1_RELEASE_SUMMARY.json")["s5_1_known_kg"]
    kgx = sum(c["ORIGINAL_KG"] for c in corrections)
    cons5 = DC.conservation(s5, corrections, s5 - kgx)
    cons51 = DC.conservation(s51, corrections, s51 - kgx)
    check(cons5["all_pass"] and cons51["all_pass"], "AD1 conservation")
    comp_rows = [{"CHECK_ID": f"AD1-K{i + 1:02d}", "DECISION_ID": d, "STAGE": s, "CHECK": c, "RESULT": res,
                  "ROWS": n, "KG": kg, "EVIDENCE": ev} for i, (d, s, c, res, n, kg, ev) in enumerate(comp)]
    summary = {
        "round": ROUND, "policy": POLICY, "recorded": RECORDED, "baseline_head": BASELINE_HEAD,
        "engine_commit": f"{frozen['S5.1']['engine_commit_stamp']}+ad1:{code_digest()[:16]}", "frozen": frozen,
        "decisions": [d["DECISION_ID"] for d in decs], "authority_policy": AD.policy_record(),
        "q2_prior_analysis": prior, "engineer_claims_on_record": pec,
        "rejected_analysis_values": len(rvs),
        "compliance": {"by_result": dict(sorted(Counter(r["RESULT"] for r in comp_rows).items())),
                       "checks": len(comp_rows)},
        "state_errata": {"total": len(errata), "by_decision": dict(sorted(Counter(e["DECISION_ID"] for e in errata)
                                                                       .items())),
                         "by_facet": dict(sorted(Counter(e["FACET"] for e in errata).items()))},
        "kg_corrections": {"records": len(corrections), "kg": kgx,
                           "spans": sorted({c["OCCURRENCE_ID"] for c in corrections}),
                           "s5_known_kg": s5, "s5_corrected_kg": s5 - kgx,
                           "s5_1_known_kg_d1": s51, "s5_1_corrected_kg_before_d1_1": s51 - kgx,
                           "conservation_s5": cons5, "conservation_s5_1": cons51},
        "gb_load": {"spans": len(reg),
                    "engineering_derived_reaction": sum(1 for r in reg if r["AD6_LOAD_STATE"] ==
                                                        AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION),
                    "candidates_changed": len(changed),
                    "no_detail_case_after": sorted(r["GB_SPAN_ID"] for r in reg if r["NO_DETAIL_CASE"]),
                    "effects": dict(sorted(Counter(r["EFFECT"] for r in reg).items()))},
        "details": {"boxed": boxed, "note9": note9, "end_bends": bends, "hooks": hooks, "gb_lt_2_5m_spans": len(lt25),
                    "follow_arch": arch, "cb": cb, "side_bars": side},
        "flags": {"frozen_outputs_changed": False, "q2_analysis_promoted": False, "confidence_carried": False,
                  "engineer_claim_created": False, "code_value_used_for_kg": False, "new_steel_released": False,
                  "pre_s7_started": False, "references_read": []}}
    dec_doc = {"round": ROUND, "policy": POLICY, "recorded": RECORDED, "version": 1, "decisions": decs,
               "q2_prior_analysis": prior, "engineer_claims_on_record": pec, "authority_policy": AD.policy_record()}
    _json(HERE / "01_AUTHORITY_DECISIONS.json", dec_doc)
    _csv(HERE / "02_REJECTED_ANALYSIS_VALUES.csv", rvs,
         ["VALUE_ID", "RECORD_TYPE", "TOPIC", "VALUE", "PROVENANCE", "DECISION_ID", "ALLOWED_USE", "PROMOTED",
          "QUANTITY_BASIS"])
    _csv(HERE / "03_COMPLIANCE_REGISTER.csv", comp_rows,
         ["CHECK_ID", "DECISION_ID", "STAGE", "CHECK", "RESULT", "ROWS", "KG", "EVIDENCE"])
    _csv(HERE / "04_AUTHORITY_STATE_ERRATA.csv", errata,
         ["ERRATA_ID", "RECORD_TYPE", "DECISION_ID", "STAGE", "TARGET_ID", "SOURCE_DELTA_ID", "FACET", "OLD_STATE",
          "NEW_STATE", "PROVENANCE", "AD6_CANDIDATES", "KG_EFFECT", "EVIDENCE"])
    _csv(HERE / "05_S5_AD1_CORRECTIONS.csv", corrections,
         ["CORRECTION_ID", "RECORD_TYPE", "DECISION_ID", "STAGE", "ORIGINAL_DELTA_ID", "ORIGINAL_DELTA_COMPONENT_ID",
          "OCCURRENCE_ID", "MARK", "COMPONENT", "ORIGINAL_KG", "CORRECTION_REASON", "SOURCE_EVIDENCE",
          "NEW_AUTHORITY_STATE", "NEW_RELEASE_STATE", "CORRECTION_KG", "RETAINED_KG", "PROVENANCE",
          "FROZEN_CANDIDATES", "AD6_CANDIDATES"])
    _csv(HERE / "06_GB_CONCENTRATED_REACTION_REGISTER.csv", reg,
         ["GB_SPAN_ID", "MARK", "EVIDENCE_KINDS", "FROZEN_LOAD_STATE", "AD6_LOAD_STATE", "AD6_PROVENANCE",
          "EXTERIOR_AUTHORITY", "FROZEN_CANDIDATES", "AD6_CANDIDATES", "NO_DETAIL_CASE", "FROZEN_KNOWN_KG",
          "FROZEN_RELEASE_SURVIVES", "EFFECT", "S5_1_RELEASE_ON_SPAN", "WHY"])
    _json(HERE / "07_AD1_SUMMARY.json", summary)
    with open(HERE / "08_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for rec in decs + [prior] + rvs + errata + corrections:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    (HERE / "00_README.md").write_text(README.format(
        round=ROUND, policy=POLICY, recorded=RECORDED, head=BASELINE_HEAD, n_rv=len(rvs), kgx=kgx,
        n_corr=len(corrections), s51=s51, s51c=s51 - kgx, n_err=len(errata), n_legs=bends["cb_end_legs"],
        n_load=summary["gb_load"]["engineering_derived_reaction"], n_changed=len(changed), n_side=side["classified"]),
        encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN", "frozen_baselines": frozen,
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "references_read_before_freeze": [],
                "rule": "owner authority decisions + errata over frozen S4 / S5 / S6 / S4.1 / S6.1 / S5.1; nothing "
                        "frozen is edited; recorded before the D1.1 rebuild"}
    _json(HERE / "AD1_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("compliance", "state_errata", "kg_corrections", "gb_load")},
                     indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
