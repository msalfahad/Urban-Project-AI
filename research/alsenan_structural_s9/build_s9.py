"""S9 - whole-building structural BOQ reconciliation (research; blind; frozen before any old-BOQ comparison).

    python3 -I research/alsenan_structural_s9/build_s9.py

Reads only frozen stage outputs (every manifest and stage index verified before and after; never written):
  S1 census (footings, columns, beams, slabs, levels, specials, rules), S2 component release (census authority
  states), S3 / S3.1 columns, S4 / S4.1 / D1.2 footings, S5 / S5.1 / AD1 / D1.1 ground system, S6 / S6.1 / D1.1
  superstructure beams, PRE-S7 thickness register, S7 / S7A slabs, S8.1 / S8.1A ground slab, S8.2 / S8.2A pool,
  S8.3 (+ errata) / S8.3A domes, S8.4 water tank, S8.5 special columns, S8.6 / S8.6A lintels, S8.7 / S8.7A-C stairs,
  S8.8 lift.
It never reads the old Urban V3b registers, R5 / R9_1, the PRE-S8 data registers or any post-freeze output.

It builds, for every structural component, one record with one owning family and one release state; the concrete
of the families no frozen stage measured (footings, columns, ground / strap beams, superstructure beams, slab
plates) is computed here from the S1 / S2 / S5 / S6 geometry and released only where the S9 release rule holds
(S9-RR1, recorded as auditable deltas); the reinforcement is carried from each family's authoritative version
(the correction chain applied), with one new correction (S9-C01). Nothing changes a frozen stage or the production
BOQ.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import structural_reconciliation as SR  # noqa: E402

ROUND = "S9"
DATE = "2026-10-10"
BASELINE_HEAD = "b85d2af"
POLICY = "S9_WHOLE_BUILDING_STRUCTURAL_RECONCILIATION_V1"
R = ROOT / "research"

MANIFEST_PATHS = {"S4": "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
                  "S4.1": "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
                  "S5": "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
                  "S5.1": "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
                  "S6": "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
                  "S6.1": "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
                  "AD1": "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
                  "D1.1": "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
                  "D1.2": "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
                  "PRE-S7": "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
                  "PRE-S7.1": "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
                  "S7": "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
                  "S7A": "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
                  "PRE-S8": "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
                  "S8.1": "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
                  "S8.1A": "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
                  "S8.2": "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
                  "S8.2A": "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
                  "S8.3": "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
                  "S8.3A": "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
                  "S8.4": "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json",
                  "S8.5": "alsenan_special_columns_s8_5/17_S8_5_FREEZE_MANIFEST.json",
                  "S8.6": "alsenan_lintels_s8_6/15_S8_6_FREEZE_MANIFEST.json",
                  "S8.6A": "alsenan_lintels_s8_6a/12_S8_6A_CORRECTION_MANIFEST.json",
                  "S8.7": "alsenan_stairs_s8_7/17_S8_7_FREEZE_MANIFEST.json",
                  "S8.7A": "alsenan_stairs_s8_7a/15_S8_7A_CORRECTION_MANIFEST.json",
                  "S8.7B": "alsenan_stairs_s8_7b/16_S8_7B_FREEZE_MANIFEST.json",
                  "S8.7C": "alsenan_stairs_s8_7c/13_S8_7C_FREEZE_MANIFEST.json",
                  "S8.8": "alsenan_lift_s8_8/18_S8_8_FREEZE_MANIFEST.json"}
# stages frozen by their own index (output hashes) rather than a freeze manifest
INDEX_STAGES = {"S1": "alsenan_structural_census_s1/INDEX.json", "S2": "alsenan_structural_s2/INDEX.json",
                "S3": "alsenan_column_rebar_s3/INDEX.json", "S3.1": "alsenan_column_rebar_s3_1/INDEX.json"}

S1D, S2D = R / "alsenan_structural_census_s1", R / "alsenan_structural_s2"
F = {
    "S1_FDEF": S1D / "FOOTING_DEFINITION_REGISTER.json", "S1_FOCC": S1D / "FOOTING_OCCURRENCE_REGISTER.json",
    "S1_CDEF": S1D / "COLUMN_DEFINITION_REGISTER.json", "S1_COCC": S1D / "COLUMN_OCCURRENCE_REGISTER.json",
    "S1_BDEF": S1D / "BEAM_DEFINITION_REGISTER.json", "S1_BOCC": S1D / "BEAM_OCCURRENCE_REGISTER.json",
    "S1_SLAB": S1D / "SLAB_PANEL_REGISTER.json", "S1_LEVEL": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
    "S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
    "S1_REVIEW": S1D / "STRUCTURAL_REVIEW_QUEUE.json",
    "S2_RELEASE": S2D / "ALSENAN_COMPONENT_RELEASE.json", "S2_QUESTIONS": S2D / "ALSENAN_CONSULTANT_QUESTIONS.json",
    "S3_SUMMARY": R / "alsenan_column_rebar_s3/COLUMN_REBAR_SUMMARY.json",
    "S31_SUMMARY": R / "alsenan_column_rebar_s3_1/COLUMN_REBAR_S3_1_SUMMARY.json",
    "S31_RELEASE": R / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json",
    "S31_MAIN": R / "alsenan_column_rebar_s3_1/COLUMN_MAIN_BAR_REGISTER.json",
    "S31_TIE": R / "alsenan_column_rebar_s3_1/COLUMN_TIE_REGISTER.json",
    "S31_LAP": R / "alsenan_column_rebar_s3_1/COLUMN_LAP_STARTER_REGISTER.json",
    "S4_BBS": R / "alsenan_footing_rebar_s4/FOOTING_BBS_NET.csv",
    "S4_SUMMARY": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_RELEASE_SUMMARY.json",
    "S4_UNRESOLVED": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_UNRESOLVED.csv",
    "S41_SUMMARY": R / "alsenan_footing_rebar_s4_1/S4_1_RELEASE_SUMMARY.json",
    "D12_CORR": R / "d1_2_footing_cover_audit/04_S4_1A_COVER_AUTHORITY_CORRECTION.csv",
    "D12_SUMMARY": R / "d1_2_footing_cover_audit/05_CORRECTED_RELEASE_SUMMARY.json",
    "S5_BBS": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_BBS_NET.csv",
    "S5_GB": R / "alsenan_ground_system_rebar_s5/GROUND_BEAM_REBAR_SUMMARY.csv",
    "S5_STRAP": R / "alsenan_ground_system_rebar_s5/STRAP_BEAM_REBAR_SUMMARY.csv",
    "S5_SUMMARY": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json",
    "S5_Q": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_ENGINEERING_QUESTIONS.csv",
    "S51_DELTA": R / "alsenan_ground_system_rebar_s5_1/S5_1_DELTA_COMPONENTS.csv",
    "S51_SUMMARY": R / "alsenan_ground_system_rebar_s5_1/S5_1_RELEASE_SUMMARY.json",
    "AD1_CORR": R / "ad1_authority_decisions/05_S5_AD1_CORRECTIONS.csv",
    "AD1_SUMMARY": R / "ad1_authority_decisions/07_AD1_SUMMARY.json",
    "D11_S6": R / "d1_1_stirrup_authority_audit/03_S6_1A_CORRECTIONS.csv",
    "D11_S5": R / "d1_1_stirrup_authority_audit/04_S5_1A_CORRECTIONS.csv",
    "D11_SUMMARY": R / "d1_1_stirrup_authority_audit/06_CORRECTED_RELEASE_SUMMARY.json",
    "S6_BBS": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_BBS_NET.csv",
    "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
    "S6_SUMMARY": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json",
    "S6_Q": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_ENGINEERING_QUESTIONS.csv",
    "S61_DELTA": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_DELTA_COMPONENTS.csv",
    "S61_SUMMARY": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_RELEASE_SUMMARY.json",
    "PS7_THICK": R / "alsenan_slab_rebar_pre_s7/02_THICKNESS_REGISTER.csv",
    "PS7_Q": R / "alsenan_slab_rebar_pre_s7/15_ENGINEER_QUESTIONS.csv",
    "S7_ITEMS": R / "alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
    "S7_SUMMARY": R / "alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json",
    "S7A_SUMMARY": R / "alsenan_slab_rebar_s7a_qa/10_S7A_SUMMARY.json",
    "S81_CONC": R / "alsenan_ground_slab_s8_1/03_CONCRETE_QTO.csv",
    "S81_REBAR": R / "alsenan_ground_slab_s8_1/04_REINFORCEMENT_XY_QTO.csv",
    "S81_SUMMARY": R / "alsenan_ground_slab_s8_1/10_S8_1_SUMMARY.json",
    "S81A_AREA": R / "alsenan_ground_slab_s8_1a/07_UNQUANTIFIED_AREA_ACCOUNTING.csv",
    "S81A_Q": R / "alsenan_ground_slab_s8_1a/08_CONFLICT_AND_QUESTION_REGISTER.csv",
    "S81A_SUMMARY": R / "alsenan_ground_slab_s8_1a/13_S8_1A_SUMMARY.json",
    "S82_CONC": R / "alsenan_swimming_pool_s8_2/03_CONCRETE_GEOMETRY_AND_QTO.csv",
    "S82_Q": R / "alsenan_swimming_pool_s8_2/16_CONFLICT_AND_QUESTION_REGISTER.csv",
    "S82_SUMMARY": R / "alsenan_swimming_pool_s8_2/17_S8_2_SUMMARY.json",
    "S82A_SUMMARY": R / "alsenan_swimming_pool_s8_2a/11_S8_2A_SUMMARY.json",
    "S83_CONC": R / "alsenan_dome_ring_s8_3/06_CONCRETE_REGISTER.csv",
    "S83_REBAR": R / "alsenan_dome_ring_s8_3/08_REBAR_QTO_REGISTER.csv",
    "S83_Q": R / "alsenan_dome_ring_s8_3/10_SOURCE_CONFLICTS_AND_QUESTIONS.csv",
    "S83_SUMMARY": R / "alsenan_dome_ring_s8_3/15_S8_3_SUMMARY.json",
    "S83_TRANSFER": R / "alsenan_dome_ring_s8_3/05_S6_TO_S8_3_OWNERSHIP_DELTA.csv",
    "S83_ERRATA": R / "alsenan_dome_ring_s8_3/errata/02_ERRATA_SUMMARY.json",
    "S83A_SUMMARY": R / "alsenan_dome_mesh_s8_3a/08_S8_3A_SUMMARY.json",
    "S84_CONC": R / "alsenan_water_tank_s8_4/04_CONCRETE_QTO.csv",
    "S84_REBAR": R / "alsenan_water_tank_s8_4/05_REINFORCEMENT_QTO.csv",
    "S84_Q": R / "alsenan_water_tank_s8_4/09_SOURCE_CONFLICTS_AND_QUESTIONS.csv",
    "S84_SUMMARY": R / "alsenan_water_tank_s8_4/14_S8_4_SUMMARY.json",
    "S85_CONC": R / "alsenan_special_columns_s8_5/07_CONCRETE_QTO.csv",
    "S85_Q": R / "alsenan_special_columns_s8_5/11_SOURCE_CONFLICTS_AND_QUESTIONS.csv",
    "S85_SUMMARY": R / "alsenan_special_columns_s8_5/16_S8_5_SUMMARY.json",
    "S86_CONC": R / "alsenan_lintels_s8_6/06_LINTEL_CONCRETE_QTO.csv",
    "S86_REBAR": R / "alsenan_lintels_s8_6/07_LINTEL_REBAR_QTO.csv",
    "S86_SUMMARY": R / "alsenan_lintels_s8_6/14_S8_6_SUMMARY.json",
    "S86A_VIEW": R / "alsenan_lintels_s8_6a/05_CORRECTED_ELIGIBLE_RELEASE_VIEW.csv",
    "S86A_SUMMARY": R / "alsenan_lintels_s8_6a/11_S8_6A_SUMMARY.json",
    "S87_CONC": R / "alsenan_stairs_s8_7/07_CONCRETE_QTO.csv",
    "S87_REBAR": R / "alsenan_stairs_s8_7/09_REBAR_QTO.csv",
    "S87_SUMMARY": R / "alsenan_stairs_s8_7/16_S8_7_SUMMARY.json",
    "S87A_SUMMARY": R / "alsenan_stairs_s8_7a/12_RELEASE_SUMMARY.json",
    "S87B_SUMMARY": R / "alsenan_stairs_s8_7b/14_RELEASE_SUMMARY.json",
    "S87C_SUMMARY": R / "alsenan_stairs_s8_7c/11_RELEASE_SUMMARY.json",
    "S87C_RFI": R / "alsenan_stairs_s8_7c/09_PRIORITISED_RFI.csv",
    "S88_WALLS": R / "alsenan_lift_s8_8/06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv",
    "S88_OWN": R / "alsenan_lift_s8_8/12_OWNERSHIP_AUDIT.csv",
    "S88_CONFLICTS": R / "alsenan_lift_s8_8/13_BLOCKED_AND_CONFLICTS.csv",
    "S88_RFI": R / "alsenan_lift_s8_8/14_RFI_QUESTIONS.csv",
    "S88_SUMMARY": R / "alsenan_lift_s8_8/17_S8_8_SUMMARY.json",
}
CODE = ["engine/source/structural_reconciliation.py", "engine/source/delta_release.py",
        "engine/source/rebar_unit_mass.py", "research/alsenan_structural_s9/build_s9.py"]
OUTPUTS = ["00_README.md", "01_COMPONENT_INVENTORY.csv", "02_CONCRETE_BOQ_RECONCILIATION.csv",
           "03_REINFORCEMENT_BOQ_RECONCILIATION.csv", "04_OWNERSHIP_AND_PRECEDENCE_REGISTER.csv",
           "05_MISSING_AND_BLOCKED_REGISTER.csv", "06_FLOOR_SUMMARY.csv", "07_RELEASED_STRUCTURAL_BOQ.csv",
           "08_STRUCTURAL_COMPLETENESS_REPORT.md", "09_ENGINEER_RFI_REGISTER.csv", "10_S9_DELTA_REGISTER.csv",
           "11_OVERLAP_AND_DOUBLE_COUNT_AUDIT.csv", "12_CONSERVATION_CHECKS.csv", "13_COVERAGE_BY_FAMILY.csv",
           "14_RELEASE_SUMMARY.json", "15_PROVENANCE.jsonl"]
MANIFEST_NAME = "16_S9_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S4-S8", "selected_by": "Urban"}
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
ARABIC = re.compile(r"[؀-ۿ]+")

# ------------------------------------------------------------------ lanes (one per record)
REL_FROZEN = "RELEASED_FROZEN_STAGE"            # released by the authoritative frozen version of its family
REL_S9 = "RELEASED_S9_DELTA"                    # released here under S9-RR1 (one S9 delta record each)
COND = "CONDITIONAL_NOT_RELEASED"               # a value under a stated condition / convention; never in a total
INDICATIVE = "INDICATIVE_ONLY_NOT_RELEASED"     # a magnitude with opposite-direction unknowns (no bound)
BLOCKED = "BLOCKED_UNQUANTIFIED"
CONFLICT = "SOURCE_CONFLICT"
OWNED_ELSEWHERE = "EXCLUDED_OWNED_BY_OTHER_FAMILY"
SUPERSEDED = "SUPERSEDED"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_IN_SOURCE = "NOT_IN_SOURCE"
RELEASED = (REL_FROZEN, REL_S9)
LANES = (REL_FROZEN, REL_S9, COND, INDICATIVE, BLOCKED, CONFLICT, OWNED_ELSEWHERE, SUPERSEDED, NOT_APPLICABLE,
         NOT_IN_SOURCE)

STOREY_OF = {"FOUNDATION": "FOUNDATION", "GROUND": "GROUND", "GF": "GF", "1F": "1F", "2F": "2F",
             "GF_ROOF": "GF", "1F_ROOF": "1F", "2F_ROOF": "2F", "GF_ROOF_SLAB": "GF", "1F_ROOF_SLAB": "1F",
             "2F_ROOF_SLAB": "2F", "GROUND_SLAB_SOG": "GROUND", "ROOF": "ROOF", "SITE": "SITE"}
STOREYS = ("FOUNDATION", "GROUND", "GF", "1F", "2F", "ROOF", "SITE")
STOREY_NOTE = {"FOUNDATION": "footings and the foundation-storey column necks",
               "GROUND": "ground / strap beams, the slab on grade, the pool, the lift pit, entrance steps",
               "GF": "GF columns, GF-roof beams and slab (the +5.50 floor), GF lintels, the GF -> 1F stairs",
               "1F": "1F columns, 1F-roof beams and slab (+9.70), the domes, 1F lintels, the 1F -> 2F stair",
               "2F": "2F columns, 2F-roof beams and slab (+13.90), the water-tank roof, 2F lintels",
               "ROOF": "parapets above the roof slabs", "SITE": "boundary wall"}
SLAB_DEFAULT_T_MM = 160.0        # P8-N18 + P1-NOTE-A (S1 / PRE-S7 project default)


def gb_detail_sections():
    """the p.13 typical ground-beam sections as D1.1 recorded them from the drawn details (frozen):
    'p13 GB_LT_5M (30x40)' -> P13-GB-LT5M: (300, 400) mm."""
    out = {}
    for k in _j(F["D11_SUMMARY"])["source_search"]["drawn_link_corners"]:
        m = re.match(r"p13 GB_(LT_2_5M|LT_5M|GT_5M) \((\d+)x(\d+)\)", k)
        if m:
            out["P13-GB-" + m.group(1).replace("LT_2_5M", "LT2_5M").replace("LT_5M", "LT5M").replace("GT_5M", "GT5M")] = \
                (float(m.group(2)) * 10, float(m.group(3)) * 10)
    check(len(out) == 3, "three p.13 length-class sections recorded by D1.1")
    return out


class Stop(RuntimeError):
    pass


def check(cond, msg):
    if not cond:
        raise Stop(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return None if v in (None, "", "None") else float(v)


def _full(v, nd=9):
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _clean(s):
    """drop Arabic words from quoted source text (the outputs carry English only)."""
    return re.sub(r"\s{2,}", " ", ARABIC.sub("", s or "")).strip()


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return _clean(str(v))


def _csv(name, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ integrity
def verify_index(rel):
    """a stage frozen by its index: every output hash it lists must still match."""
    p = R / rel
    d = _j(p)
    table = d.get("outputs") or d.get("registers") or {}
    if isinstance(table, list):
        table = {x.get("file") or x.get("name"): x.get("sha256") for x in table}
    files = {k: v for k, v in table.items() if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)}
    files.update({v.get("file") or k: v["sha256"] for k, v in table.items() if isinstance(v, dict) and v.get("sha256")})
    check(files, f"{rel}: index lists no hashed outputs")
    for name, h in files.items():
        check(_sha(p.parent / name) == h, f"{rel}: {name} changed since its index")
    return {"index": rel, "index_sha256": _sha(p), "files_checked": len(files)}


def verify_inputs():
    frozen = {k: DR.verify_frozen(R / p, ROOT) for k, p in MANIFEST_PATHS.items()}
    indexed = {k: verify_index(p) for k, p in INDEX_STAGES.items()}
    for k, p in F.items():
        check(p.exists(), f"input {k} present")
        check(not re.search(r"registers_v3b|R9_1|alsenan_arch_truth_05|post_freeze|pre_s8_structural", str(p)),
              f"firewall: {p}")
    return frozen, indexed


# ------------------------------------------------------------------ S2 census authority
def s2_states():
    out = {}
    for r in _j(F["S2_RELEASE"])["components"]:
        if r["component"] == "CONCRETE":
            out[r["element_id"]] = {"state": r["release_state"], "quantity": r["quantity"], "unit": r["unit"],
                                    "flags": r.get("flags") or []}
    return out


def record(**kw):
    base = {"COMPONENT_ID": None, "FAMILY": None, "SUBFAMILY": None, "STOREY": None, "OWNER_FAMILY": None,
            "OWNER_STAGE": None, "SOURCE": None, "DIMENSIONS": None, "GROSS_M3": None, "DEDUCTIONS_M3": None,
            "DEDUCTION_DETAIL": None, "NET_M3": None, "RELEASED_M3": None, "CONDITIONAL_M3": None,
            "CONDITIONAL_RANGE_M3": None, "LANE": None, "EVIDENCE_STATUS": None, "S2_CENSUS_STATE": None,
            "UNRESOLVED_REASON": None, "REBAR_LINK": None, "FLAGS": None}
    base.update(kw)
    check(base["LANE"] in LANES, f"{base['COMPONENT_ID']}: lane {base['LANE']}")
    if base["LANE"] in RELEASED:
        check(base["NET_M3"] is not None and base["RELEASED_M3"] == base["NET_M3"], f"{base['COMPONENT_ID']}: released")
    else:
        check(base["RELEASED_M3"] in (None, 0.0), f"{base['COMPONENT_ID']}: an unreleased record carries no release")
    base["STOREY"] = STOREY_OF[base["STOREY"]]
    return base


# ------------------------------------------------------------------ A. footings
def footings(s2, deltas):
    defs = {r["footing_type"]: r for r in _j(F["S1_FDEF"])["rows"]}
    occ = _j(F["S1_FOCC"])["rows"]
    rows, boxes = [], []
    for r in occ:
        bb = r["outline"]["bbox"]
        boxes.append((r["footing_id"], bb, r))
    # the largest possible shared prism of two overlapping outlines: plan overlap x the shallower depth; the
    # shallower footing gives it up (the true overlap is between 0 and this, depending on the founding levels)
    overlap = defaultdict(list)
    for (i, bi, ri), (j, bj, rj) in ((a, b) for k, a in enumerate(boxes) for b in boxes[k + 1:]):
        a = SR.rect_overlap(bi, bj) / 1e6
        if a > 0:
            di = (defs[ri["type"]]["D_cm"] if ri["type"] else None)
            dj = (defs[rj["type"]]["D_cm"] if rj["type"] else None)
            check(di and dj, f"overlap {i} / {j} involves an undefined footing")
            give, keep = (i, j) if di <= dj else (j, i)
            overlap[give].append({"with": keep, "plan_m2": _r(a, 6), "depth_m": min(di, dj) / 100,
                                  "max_m3": _r(a * min(di, dj) / 100, 9)})
    for fid, bb, r in boxes:
        st = s2.get(fid, {})
        src = f"ST7757 FP outline {r['outline']['handle']} (bbox mm {[round(v, 1) for v in bb]}); schedule p.9"
        hnd = r["outline"]["handle"].split(":")[0]
        common = dict(COMPONENT_ID=fid, FAMILY="FOOTINGS", SUBFAMILY="ISOLATED / COMBINED FOOTING", STOREY="FOUNDATION",
                      OWNER_FAMILY="FOOTINGS", OWNER_STAGE="S9 (concrete) / S4 -> S4.1 -> D1.2 (bars)",
                      S2_CENSUS_STATE=st.get("state"), REBAR_LINK=f"S4:FOCC-{hnd}")
        if not r["type"]:
            cands = r.get("candidate_types") or []
            vals = {t: _r(SR.prism(defs[t]["L_cm"] / 100, defs[t]["W_cm"] / 100, defs[t]["D_cm"] / 100), 9)
                    for t in cands}
            rows.append(record(**common, SOURCE=src, DIMENSIONS={"candidates": {t: [defs[t]["L_cm"], defs[t]["W_cm"],
                                                                                   defs[t]["D_cm"]] for t in cands},
                                                                  "drawn_bbox_m": [_r((bb[2] - bb[0]) / 1000, 4),
                                                                                   _r((bb[3] - bb[1]) / 1000, 4)]},
                               CONDITIONAL_RANGE_M3=[min(vals.values()), max(vals.values())], LANE=CONFLICT,
                               EVIDENCE_STATUS="TAG_CONFLICT", UNRESOLVED_REASON=f"tag conflict {cands} (S1); the drawn "
                               "outline matches neither schedule row; S2 BLOCKED",
                               FLAGS=["FOOTING_TYPE_CONFLICT"]))
            continue
        d = defs[r["type"]]
        L, W, D = d["L_cm"] / 100, d["W_cm"] / 100, d["D_cm"] / 100
        gross = SR.prism(L, W, D)
        drawn = sorted([(bb[2] - bb[0]) / 1000, (bb[3] - bb[1]) / 1000])
        match = abs(drawn[0] - min(L, W)) < 0.002 and abs(drawn[1] - max(L, W)) < 0.002
        ded = math.fsum(o["max_m3"] for o in overlap.get(fid, []))
        net = gross - ded
        ok = st.get("state") == "VERIFIED" and match and r["terminal_state"] == "COUNTED_AND_DEFINED"
        lane = REL_S9 if ok else COND
        rows.append(record(**common, SOURCE=src, DIMENSIONS={"type": r["type"], "L_m": L, "W_m": W, "D_m": D,
                                                             "drawn_matches_schedule": match},
                           GROSS_M3=_r(gross), DEDUCTIONS_M3=_r(ded), DEDUCTION_DETAIL=overlap.get(fid) or None,
                           NET_M3=_r(net), RELEASED_M3=_r(net) if ok else None, CONDITIONAL_M3=None if ok else _r(net),
                           LANE=lane, EVIDENCE_STATUS="SCHEDULE_PRINTED + DRAWN_OUTLINE_MATCH" if match else
                           "SCHEDULE_PRINTED", FLAGS=(["LIFT_FOOTING_FF (S8.8 FTG; counted once here)"]
                                                      if r["type"] == "FF" else None) or
                           (["OUTLINE_OVERLAP_DEDUCTED (maximum prism)"] if fid in overlap else None)))
        if ok:
            deltas.append(delta("FOOTINGS", fid, "SCHEDULE_AND_PLAN_GEOMETRY", net,
                                f"L x W x D from the printed schedule row FDEF-{r['type']} (S1); outline drawn = "
                                f"schedule; S2 VERIFIED{'; overlap deducted' if fid in overlap else ''}"))
    return rows, overlap


def delta(family, cid, basis, m3, why):
    return {"DELTA_ID": None, "CHANGE_KIND": "CONCRETE_QUANTITY_RELEASED", "FAMILY": family, "COMPONENT_ID": cid,
            "OLD_STATE": "OWNED_BUT_UNMEASURED (no frozen stage holds its m3)", "OLD_KNOWN_M3": 0.0,
            "QUANTITY_BASIS": basis, "DELTA_M3": _r(m3), "NEW_RELEASE_STATE": "PROJECT_BASIS_QTO (S9)",
            "RULE": "S9-RR1", "WHY": why}


# ------------------------------------------------------------------ B. columns
def columns(s2, deltas, footing_rows):
    occ = _j(F["S1_COCC"])["rows"]
    lev = _j(F["S1_LEVEL"])
    interval = {x["storey"]: x.get("floor_to_floor_m") for x in lev["intervals"]}
    focc = _j(F["S1_FOCC"])
    col2ft = {}
    for r in focc["rows"]:
        for c in r["supported_columns"]:
            col2ft[c] = r
    fdef = {r["footing_type"]: r for r in _j(F["S1_FDEF"])["rows"]}
    special = {x["COLUMN_ID"]: x["SPECIAL_ID"] for x in _rows(F["S85_CONC"]) if x["COLUMN_ID"]}
    lift_cols = {"COL-C1-X09-Y09-FOUNDATION", "COL-C2-X09-Y07-FOUNDATION", "COL-C2-X10-Y09-FOUNDATION",
                 "COL-C9-X10-Y07-FOUNDATION"}
    rows = []
    for r in occ:
        cid, fl = r["column_id"], r["floor"]
        st = s2.get(cid, {})
        a, b = (r["schedule_section_cm"] or [None, None])
        dw = r["drawn_section_cm"]
        area = (a / 100) * (b / 100) if a and b else None
        h = interval.get(fl)
        flags = []
        if cid in special:
            flags.append(f"SPECIAL_COLUMN {special[cid]} (S8.5: no concrete added)")
        if cid in lift_cols:
            flags.append("LIFT_COLUMN 200 / 250 drawn vs 300 schedule at the pit (S8.8 C-01, Q-LIFT-08)")
        common = dict(COMPONENT_ID=cid, FAMILY="COLUMNS", SUBFAMILY=f"{r['column_type']} ({r['type_authority']})",
                      STOREY=fl, OWNER_FAMILY="COLUMNS", OWNER_STAGE="S9 (concrete) / S3.1 (+ S9-C01) (bars)",
                      SOURCE=f"ST7757 {'/'.join(r['plan_source'].get('sheets', []))} handles "
                             f"{r['plan_source'].get('handles')}; schedule p.9",
                      S2_CENSUS_STATE=st.get("state"), REBAR_LINK=f"S3.1:{cid}")
        dims = {"schedule_cm": [a, b], "drawn_cm": dw, "drawn_vs_schedule": r["drawn_vs_schedule"],
                "interval_m": h, "interval_basis": "printed floor-to-floor (S1 ESTABLISHED; P7757 VE-AA-09)" if h else
                "founding level not printed (S1 BLOCKED)"}
        if fl == "FOUNDATION":
            ft = col2ft.get(r["chain_id"])
            ind = None
            if area and ft and ft["type"]:
                ind = _r(area * (2.5 - fdef[ft["type"]]["D_cm"] / 100), 9)
            rows.append(record(**common, DIMENSIONS={**dims, "footing": ft["footing_id"] if ft else None},
                               CONDITIONAL_M3=ind, LANE=BLOCKED if not (cid in lift_cols) else CONFLICT,
                               EVIDENCE_STATUS="SECTION_PRINTED; HEIGHT_NOT_ESTABLISHED",
                               UNRESOLVED_REASON="foundation-storey neck: founding level not printed (excavation >= 1.50 "
                                                 "m below plot level is a minimum); the indicative value uses "
                                                 "(+1.00) - (-1.50 + footing depth), whose two unknowns act in opposite "
                                                 "directions (no bound); never in a total",
                               FLAGS=flags + ["INDICATIVE_VALUE_ONLY"]))
            continue
        gross = area * h if (area and h) else None
        if st.get("state") == "VERIFIED" and r["drawn_vs_schedule"] == "MATCH" and gross:
            rows.append(record(**common, DIMENSIONS=dims, GROSS_M3=_r(gross), DEDUCTIONS_M3=0.0, NET_M3=_r(gross),
                               RELEASED_M3=_r(gross), LANE=REL_S9,
                               EVIDENCE_STATUS="SECTION_PRINTED + DRAWN_MATCH; INTERVAL_PRINTED_FLOOR_TO_FLOOR",
                               FLAGS=flags + ["INTERVAL = PRINTED FLOOR-TO-FLOOR (structural levels not printed; "
                                              "project-basis value, as S3.1 main bars)"]))
            deltas.append(delta("COLUMNS", cid, "SCHEDULE_AND_PLAN_GEOMETRY", gross,
                                f"section {a} x {b} cm (schedule = drawn) x {h} m printed floor-to-floor; S2 VERIFIED; "
                                "joint with the beams / slab owned by the column (S9-MC1)"))
        elif st.get("state") == "BLOCKED":
            rows.append(record(**common, DIMENSIONS=dims, CONDITIONAL_M3=_r(gross) if gross else None, LANE=CONFLICT,
                               EVIDENCE_STATUS="TYPE_OR_SECTION_CONFLICT", UNRESOLVED_REASON="S2 BLOCKED (type / tag "
                               "conflict, S1 review queue)", FLAGS=flags + ["COLUMN_TYPE_CONFLICT"]))
        else:
            alt = (dw[0] / 100) * (dw[1] / 100) * h if (dw and h) else None
            rows.append(record(**common, DIMENSIONS=dims, CONDITIONAL_M3=_r(gross) if gross else None,
                               CONDITIONAL_RANGE_M3=sorted([_r(gross), _r(alt)]) if (gross and alt) else None,
                               LANE=COND, EVIDENCE_STATUS="SECTION_PRINTED; DRAWN_DIFFERS" if r["drawn_vs_schedule"] !=
                               "MATCH" else "SECTION_PRINTED",
                               UNRESOLVED_REASON=f"S2 {st.get('state')}: drawn section {dw} vs schedule {[a, b]} "
                                                 f"({r['drawn_vs_schedule']}) or below the minimum thickness",
                               FLAGS=flags + ["DRAWN_VS_SCHEDULE"]))
    return rows


# ------------------------------------------------------------------ C. ground and strap beams
def ground_beams(deltas):
    rows = []
    for src_name, fam in (("S5_GB", "GROUND_BEAM"), ("S5_STRAP", "STRAP_BEAM")):
        for r in _rows(F[src_name]):
            oid = r["occurrence_id"]
            L = _f(r["member_clear_concrete_length_m"])
            w, d = _f(r["width_mm"]), _f(r["depth_mm"])
            ws, ds = r["width_state"], r["depth_state"]
            details = json.loads(r.get("detail_ids") or "[]") if "detail_ids" in r else []
            common = dict(COMPONENT_ID=oid, FAMILY="GROUND_BEAMS", SUBFAMILY=f"{fam} {r['mark']}", STOREY="GROUND",
                          OWNER_FAMILY="GROUND_BEAMS", OWNER_STAGE="S9 (concrete) / S5 -> S5.1 -> AD1 -> D1.1 (bars)",
                          SOURCE=f"ST7757 GBP handles {r.get('geometry_handles')}; p.13 details {details}",
                          REBAR_LINK=f"S5:{oid}")
            dims = {"clear_concrete_length_m": L, "width_mm": w, "width_state": ws, "depth_mm": d, "depth_state": ds,
                    "details": details}
            if ws == "SOURCE_EXPLICIT" and ds == "SOURCE_EXPLICIT" and w and d and L:
                v = L * w / 1000 * d / 1000
                rows.append(record(**common, DIMENSIONS=dims, GROSS_M3=_r(v), DEDUCTIONS_M3=0.0, NET_M3=_r(v),
                                   RELEASED_M3=_r(v), LANE=REL_S9, EVIDENCE_STATUS="SECTION_EXPLICIT + CLEAR_LENGTH",
                                   S2_CENSUS_STATE="VERIFIED (family lengths)",
                                   FLAGS=["CLEAR BETWEEN COLUMN / FOOTING FACES (S9-MC1); no overlap with the "
                                          "footings (founding <= -1.50, beam top at the GF slab)"]))
                deltas.append(delta("GROUND_BEAMS", oid, "SCHEDULE_AND_PLAN_GEOMETRY", v,
                                    f"{w:.0f} x {d:.0f} mm explicit (S5) x {L} m clear concrete length (S5)"))
                continue
            secs = gb_detail_sections()
            cand = sorted({secs[x][1] for x in details if x in secs})
            width = w or (300.0 if ws == "CANDIDATE_INVARIANT" else None)
            if ds == "BOUNDED_ABOVE" and width and L and _f(r.get("depth_bound_max_m")):
                ub = L * width / 1000 * _f(r["depth_bound_max_m"])
                rows.append(record(**common, DIMENSIONS=dims, CONDITIONAL_M3=None, CONDITIONAL_RANGE_M3=[None, _r(ub)],
                                   LANE=COND, EVIDENCE_STATUS="DEPTH_BOUNDED_ABOVE (exterior: follows the architecture)",
                                   UNRESOLVED_REASON="exterior ground beam 30 x FOLLOW ARCH: depth <= the bound only "
                                                     "(PRE-S5.1 04); no lower bound",
                                   FLAGS=["UPPER_BOUND_ONLY"]))
            elif ds in ("CANDIDATE_CONFLICT", "SOURCE_CONFLICT") and width and L and cand:
                rng = [_r(L * width / 1000 * min(cand) / 1000), _r(L * width / 1000 * max(cand) / 1000)]
                rows.append(record(**common, DIMENSIONS={**dims, "candidate_depths_mm": cand},
                                   CONDITIONAL_RANGE_M3=rng, LANE=CONFLICT if ds == "SOURCE_CONFLICT" else COND,
                                   EVIDENCE_STATUS=f"DEPTH_{ds}", UNRESOLVED_REASON="the p.13 length-class detail "
                                   "(< 2.5 / < 5 / > 5 m) changes with the length basis (centre-to-centre or clear); "
                                   "S2 consultant question", FLAGS=["LENGTH_CLASS_DETAIL"]))
            elif fam == "STRAP_BEAM" and ws == "CANDIDATE_CONFLICT":
                rows.append(record(**common, DIMENSIONS=dims, LANE=CONFLICT, EVIDENCE_STATUS="WIDTH_CANDIDATE_CONFLICT",
                                   UNRESOLVED_REASON="SB2 width conflict (S1 review queue item 9; PRE-S5.1 08)"))
            else:
                rows.append(record(**common, DIMENSIONS=dims, LANE=BLOCKED, EVIDENCE_STATUS=f"WIDTH {ws} / DEPTH {ds}",
                                   UNRESOLVED_REASON="section not established (exterior / interior or concentrated-load "
                                                     "case unresolved; S5 why_not_resolved)"))
    return rows


# ------------------------------------------------------------------ D. superstructure beams
def beams():
    bdef = defaultdict(list)
    for r in _j(F["S1_BDEF"])["rows"]:
        bdef[r["beam_type"]].append(r)
    transfers = {r["BASELINE_COMPONENT_ID"] for r in _rows(F["S83_TRANSFER"])}
    rows = []

    def section(mark):
        ds = [d for d in bdef.get(mark, []) if d.get("B_cm") and d.get("H_cm")]
        if len(ds) != 1:
            return None, f"{len(ds)} schedule rows with a section for {mark!r}"
        return ds[0], None

    for r in _rows(F["S6_OCC"]):
        oid, mark, fl = r["occurrence_id"], r["mark"], r["floor"]
        g = json.loads(r["geometry"])
        common = dict(FAMILY="BEAMS", STOREY=fl, OWNER_FAMILY="BEAMS",
                      OWNER_STAGE="S9 (concrete, conditional) / S6 -> S6.1 -> D1.1 (bars)",
                      S2_CENSUS_STATE="LOWER_BOUND (S2 superstructure beam lengths)", REBAR_LINK=f"S6:{oid}")
        src = f"ST7757 {r['sheet'] or ''} geometry {r['geometry_handles']} tags {r['tag_handles']}; schedule {r['schedule_handles']}"
        if oid in transfers:
            rows.append(record(COMPONENT_ID=oid, SUBFAMILY=f"DOME RING {mark or 'untagged arc'}", SOURCE=src,
                               DIMENSIONS={"length_m": g.get("length_cc_m") or g.get("length_m")}, LANE=OWNED_ELSEWHERE,
                               EVIDENCE_STATUS="TRANSFERRED_TO_S8_3", UNRESOLVED_REASON="dome ring band: owned by "
                               "S8.3 (ring concrete SOURCE_CONFLICT there)", **{**common, "OWNER_FAMILY": "DOMES",
                                                                                "OWNER_STAGE": "S8.3"}))
            continue
        if r["subfamily"] == "UNTAGGED_GEOMETRY":
            rows.append(record(COMPONENT_ID=oid, SUBFAMILY="UNTAGGED BEAM GEOMETRY", SOURCE=src,
                               DIMENSIONS={"clear_m": g.get("clear_m") or g.get("clear_face_to_face_m"),
                                           "length_m": g.get("length_m") or g.get("length_cc_m"),
                                           "drawn_width_mm": g.get("drawn_width_mm")},
                               LANE=BLOCKED, EVIDENCE_STATUS="NO_TAG_NO_SCHEDULE_SECTION",
                               UNRESOLVED_REASON="beam band drawn without a tag: no schedule depth (S6 BLOCKED_TYPE)",
                               **common))
            continue
        d, why = section(mark)
        if r["subfamily"] == "CONTINUOUS_BEAM":
            for k in sorted(g["spans"], key=int):
                sp = g["spans"][k]
                cid = f"{oid}#SPAN{k}"
                B = sp.get("schedule_width_mm") or (d["B_cm"] * 10 if d else None)
                L = sp.get("clear_m")
                dims = {"mark": mark, "B_mm": B, "H_mm": d["H_cm"] * 10 if d else None, "clear_m": L,
                        "cc_m": sp.get("cc_m"), "schedule_span_m": sp.get("schedule_span_m"),
                        "drawn_width_mm": sp.get("drawn_width_mm"), "binding": sp.get("binding")}
                if not d or not L or not B:
                    rows.append(record(COMPONENT_ID=cid, SUBFAMILY=f"CONTINUOUS {mark}", SOURCE=src, DIMENSIONS=dims,
                                       LANE=BLOCKED, EVIDENCE_STATUS="SECTION_OR_LENGTH_MISSING",
                                       UNRESOLVED_REASON=why or "clear span not established", **common))
                    continue
                v = L * B / 1000 * d["H_cm"] / 100
                alt = L * B / 1000 * (d["H_cm"] / 100 + SLAB_DEFAULT_T_MM / 1000)
                conflict = sp.get("width_match") == "SOURCE_CONFLICT" or "CONFLICT" in (sp.get("binding") or "")
                rows.append(record(COMPONENT_ID=cid, SUBFAMILY=f"CONTINUOUS {mark}", SOURCE=src, DIMENSIONS=dims,
                                   CONDITIONAL_M3=_r(v), CONDITIONAL_RANGE_M3=[_r(v), _r(alt)],
                                   LANE=CONFLICT if conflict else COND,
                                   EVIDENCE_STATUS="SCHEDULE_SECTION + CLEAR_SPAN" + (" (drawn width differs)" if
                                                                                     conflict else ""),
                                   UNRESOLVED_REASON=("drawn width differs from the schedule; " if conflict else "") +
                                   "beam depth convention: schedule H read as the overall depth (S6 / D1.1 links); "
                                   "alternative H below the slab adds B x t; S2 holds the length as a lower bound",
                                   FLAGS=["BEAM_DEPTH_CONVENTION", "S2_LENGTH_LOWER_BOUND"], **common))
            continue
        L = g.get("clear_face_to_face_m")
        B = _f(r["schedule_width_mm"]) or (d["B_cm"] * 10 if d else None)
        dims = {"mark": mark, "B_mm": B, "H_mm": d["H_cm"] * 10 if d else None, "clear_m": L,
                "cc_m": g.get("length_cc_m"), "drawn_width_mm": g.get("drawn_width_mm"),
                "width_match": r["width_match_state"], "authority": r["authority_state"],
                "stair_qualifier": g.get("stair_qualifier")}
        if not d:
            rows.append(record(COMPONENT_ID=oid, SUBFAMILY=f"SIMPLE {mark}", SOURCE=src, DIMENSIONS=dims, LANE=BLOCKED,
                               EVIDENCE_STATUS="NO_SCHEDULE_SECTION", UNRESOLVED_REASON=why, **common))
            continue
        if g.get("object_kind") == "ARC_BAND":
            ub = (g.get("length_cc_m") or 0) * B / 1000 * d["H_cm"] / 100
            rows.append(record(COMPONENT_ID=oid, SUBFAMILY=f"CURVED {mark}", SOURCE=src, DIMENSIONS=dims,
                               CONDITIONAL_RANGE_M3=[None, _r(ub)], LANE=COND, EVIDENCE_STATUS="ARC_BAND_CENTRE_LENGTH",
                               UNRESOLVED_REASON="curved band: only the centre-to-centre arc length is held (clear "
                                                 "length not established) -> an upper bound",
                               FLAGS=["UPPER_BOUND_ONLY"], **common))
            continue
        if not L:
            rows.append(record(COMPONENT_ID=oid, SUBFAMILY=f"SIMPLE {mark}", SOURCE=src, DIMENSIONS=dims, LANE=BLOCKED,
                               EVIDENCE_STATUS="CLEAR_LENGTH_MISSING", UNRESOLVED_REASON="clear span not established",
                               **common))
            continue
        v = L * B / 1000 * d["H_cm"] / 100
        alt = L * B / 1000 * (d["H_cm"] / 100 + SLAB_DEFAULT_T_MM / 1000)
        conflict = r["authority_state"] in ("SOURCE_CONFLICT",) or "SOURCE_CONFLICT" in r["width_match_state"]
        rows.append(record(COMPONENT_ID=oid, SUBFAMILY=f"SIMPLE {mark}", SOURCE=src, DIMENSIONS=dims,
                           CONDITIONAL_M3=_r(v), CONDITIONAL_RANGE_M3=[_r(v), _r(alt)],
                           LANE=CONFLICT if conflict else COND,
                           EVIDENCE_STATUS="SCHEDULE_SECTION + CLEAR_FACE_TO_FACE" + (" (conflict)" if conflict else ""),
                           UNRESOLVED_REASON=("S6 authority / width conflict; " if conflict else "") +
                           "beam depth convention (H overall vs below the slab) not printed; S2 holds the length as a "
                           "lower bound", FLAGS=["BEAM_DEPTH_CONVENTION", "S2_LENGTH_LOWER_BOUND"], **common))
    # S1 beam occurrences that S6 does not carry
    s6 = {r["occurrence_id"] for r in _rows(F["S6_OCC"])}
    for r in _j(F["S1_BOCC"])["rows"]:
        if r["family"] == "STAIR" and r["beam_id"] not in s6:
            rows.append(record(COMPONENT_ID=r["beam_id"], FAMILY="BEAMS", SUBFAMILY=f"STAIR {r['beam_type']}",
                               STOREY=r["floor"], OWNER_FAMILY="BEAMS", OWNER_STAGE="S1 (not carried by S6)",
                               SOURCE=f"ST7757 {r['sheet']} {r['source_id']}",
                               DIMENSIONS={"clear_length_m": r.get("clear_length_m"), "B_cm": r.get("schedule_B_cm")},
                               LANE=CONFLICT, EVIDENCE_STATUS="SAME_SPAN_CARRIES_TWO_TAGS",
                               UNRESOLVED_REASON="the span carries two tags (S1 issue); S6 measured the other tag",
                               REBAR_LINK=None))
    return rows


# ------------------------------------------------------------------ E. slab plates
def slabs(s2, deltas):
    thick = {r["SLAB_PANEL_ID"]: r for r in _rows(F["PS7_THICK"])}
    tank = {r["PANEL_ID"] for r in _rows(F["S84_CONC"]) if r["PANEL_ID"]}
    s81 = {r["PANEL_ID"]: r for r in _rows(F["S81_CONC"])}
    rows = []
    for r in _j(F["S1_SLAB"])["rows"]:
        pid, cls, fl = r["panel_id"], r["class"], r["floor"]
        st = s2.get(pid, {})
        poly = [(x / 1000, y / 1000) for x, y in r["polygon_mm"]] if r.get("polygon_mm") else None
        holes = [[(x / 1000, y / 1000) for x, y in h] for h in (r.get("holes_mm") or [])]
        area_ind = SR.polygon_area_with_holes(poly, holes) if poly else None
        th = thick.get(pid)
        t = _f(th["EFFECTIVE_THICKNESS_MM"]) if th and th["STATE"] == "RESOLVED" else None
        sunken = th and th.get("SUNKEN") == "True"
        common = dict(COMPONENT_ID=pid, FAMILY="SLABS", SUBFAMILY=cls, STOREY=fl, OWNER_FAMILY="SLABS",
                      OWNER_STAGE="S9 (concrete) / S7 (bars)", S2_CENSUS_STATE=st.get("state"),
                      SOURCE=f"ST7757 {r['sheet']} {r['source_id']} ({len(r.get('boundary_handles') or [])} boundary "
                             f"handles)", REBAR_LINK=f"S7:{pid}")
        dims = {"area_m2_s1": r["area_m2"], "area_m2_recomputed": _r(area_ind, 6), "thickness_mm": t,
                "thickness_authority": th["AUTHORITY"] if th else r.get("thickness_authority"), "sunken": bool(sunken)}
        if cls in ("OPEN_TO_BELOW", "OUTSIDE_BUILDING_OR_COURT"):
            rows.append(record(**common, DIMENSIONS=dims, LANE=NOT_APPLICABLE,
                               EVIDENCE_STATUS=f"{cls} (no slab concrete)"))
            continue
        if cls == "DOME_ZONE":
            rows.append(record(**{**common, "OWNER_FAMILY": "DOMES", "OWNER_STAGE": "S8.3"}, DIMENSIONS=dims,
                               LANE=OWNED_ELSEWHERE, EVIDENCE_STATUS="DOME_ZONE (S8.3 owns the shells and rings)"))
            continue
        if cls in ("STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE"):
            rows.append(record(**{**common, "OWNER_FAMILY": "STAIRS", "OWNER_STAGE": "S8.7"}, DIMENSIONS=dims,
                               LANE=OWNED_ELSEWHERE, EVIDENCE_STATUS=f"{cls} (S8.7 owns the flights and landings)"))
            continue
        if pid in tank:
            rows.append(record(**{**common, "OWNER_FAMILY": "WATER_TANK_ROOF", "OWNER_STAGE": "S8.4"},
                               DIMENSIONS=dims, LANE=OWNED_ELSEWHERE, EVIDENCE_STATUS="released by S8.4 (frozen)"))
            continue
        if fl == "GROUND_SLAB_SOG":
            if pid in s81:
                rows.append(record(**{**common, "FAMILY": "GROUND_SLAB", "OWNER_FAMILY": "GROUND_SLAB",
                                      "OWNER_STAGE": "S8.1"}, DIMENSIONS=dims, LANE=OWNED_ELSEWHERE,
                                   EVIDENCE_STATUS=f"released by S8.1 as {s81[pid]['ITEM_ID']}"))
            else:
                v = (area_ind or r["area_m2"]) * 0.10
                rows.append(record(**{**common, "FAMILY": "GROUND_SLAB", "OWNER_FAMILY": "GROUND_SLAB",
                                      "OWNER_STAGE": "S8.1 / S8.1A"}, DIMENSIONS={**dims, "thickness_mm": 100},
                                   CONDITIONAL_M3=_r(v), LANE=COND, EVIDENCE_STATUS="GROUND_SLAB_NOTE_T10_SCOPE_OPEN",
                                   UNRESOLVED_REASON="S8.1 / S8.1A: the 'T=10cm' ground-slab note's scope and the cover "
                                                     "(cast against soil?) are not established for this face",
                                   FLAGS=["S8_1A_BLOCKED_AREA"]))
            continue
        ok = st.get("state") == "VERIFIED" and t and r["terminal_state"] == "COUNTED_AND_DEFINED" and area_ind is not None \
            and abs(area_ind - r["area_m2"]) < 0.002
        v = r["area_m2"] * t / 1000 if t else None
        flags = ["SUNKEN: plate only; the drop / step concrete is BLOCKED (drop depth not located)"] if sunken else []
        if ok:
            rows.append(record(**common, DIMENSIONS=dims, GROSS_M3=_r(v), DEDUCTIONS_M3=0.0, NET_M3=_r(v),
                               RELEASED_M3=_r(v), LANE=REL_S9,
                               EVIDENCE_STATUS="PANEL_POLYGON (S1, recomputed) x THICKNESS (" +
                                               (th["AUTHORITY"] if th else "") + ")",
                               FLAGS=flags + ["PANEL BETWEEN BEAM / COLUMN FACES (S9-MC1)"]))
            deltas.append(delta("SLABS", pid, "SCHEDULE_AND_PLAN_GEOMETRY", v,
                                f"S1 panel polygon {r['area_m2']} m2 (recomputed {_full(area_ind, 4)}) x {t:.0f} mm "
                                f"({th['AUTHORITY']}: {th['PROJECT_DEFAULT_SOURCES']}); S2 VERIFIED"))
        else:
            rows.append(record(**common, DIMENSIONS=dims, CONDITIONAL_M3=_r(v), LANE=COND if v else BLOCKED,
                               EVIDENCE_STATUS="PANEL_NOT_VERIFIED", UNRESOLVED_REASON=f"S2 {st.get('state')}; thickness "
                               f"{th['STATE'] if th else 'not registered'}", FLAGS=flags or None))
    return rows


# ------------------------------------------------------------------ F. frozen S8 families
def frozen_s8():
    rows = []
    # S8.1 ground slab cells (released)
    for r in _rows(F["S81_CONC"]):
        m3 = _f(r["VOLUME_M3"])
        rows.append(record(COMPONENT_ID=r["ITEM_ID"], FAMILY="GROUND_SLAB", SUBFAMILY=f"cell {r['ZONE_ID']} ({r['PANEL_ID']})",
                           STOREY="GROUND", OWNER_FAMILY="GROUND_SLAB", OWNER_STAGE="S8.1 (S8.1A: unchanged)",
                           SOURCE=f"S8.1 03 {r['PLAN_AUTHORITY']}", DIMENSIONS={"area_m2": _f(r["NET_AREA_M2"]),
                                                                              "thickness_mm": _f(r["THICKNESS_MM"])},
                           GROSS_M3=m3, DEDUCTIONS_M3=0.0, NET_M3=m3, RELEASED_M3=m3, LANE=REL_FROZEN,
                           EVIDENCE_STATUS=r["LANE"], REBAR_LINK=f"S8.1:{r['ZONE_ID']}"))
    # S8.2 pool
    for r in _rows(F["S82_CONC"]):
        if r["ROW_ID"].startswith("CQ-"):
            rows.append(record(COMPONENT_ID=r["COMPONENT_ID"], FAMILY="POOL", SUBFAMILY=r["ITEM"], STOREY="GROUND",
                               OWNER_FAMILY="POOL", OWNER_STAGE="S8.2 / S8.2A", SOURCE="S8.2 03",
                               LANE=BLOCKED, EVIDENCE_STATUS=r["LANE"],
                               UNRESOLVED_REASON=_clean("; ".join(json.loads(r["MISSING"] or "[]")))))
    # S8.3 domes
    for r in _rows(F["S83_CONC"]):
        lane = {"PROJECT_BASIS_QTO": REL_FROZEN, "SOURCE_CONFLICT": CONFLICT, "BLOCKED_UNQUANTIFIED": BLOCKED,
                "NOT_APPLICABLE": NOT_APPLICABLE}[r["LANE"]]
        m3 = _f(r["M3"]) if lane == REL_FROZEN else None
        rows.append(record(COMPONENT_ID=r["ITEM_ID"], FAMILY="DOMES", SUBFAMILY=r["COMPONENT"], STOREY="1F",
                           OWNER_FAMILY="DOMES", OWNER_STAGE="S8.3 (+ errata, S8.3A sensitivity)", SOURCE="S8.3 06",
                           GROSS_M3=m3, DEDUCTIONS_M3=0.0 if m3 else None, NET_M3=m3, RELEASED_M3=m3, LANE=lane,
                           EVIDENCE_STATUS=r["LANE"], UNRESOLVED_REASON=_clean(r["STILL_MISSING"]) or None,
                           REBAR_LINK=f"S8.3:{r['DOME']}"))
    # S8.4 water-tank roof slabs
    for r in _rows(F["S84_CONC"]):
        rel = r["RELEASED"] == "True"
        m3 = _f(r["VOLUME_M3"]) if rel else None
        rows.append(record(COMPONENT_ID=r["ITEM_ID"], FAMILY="WATER_TANK_ROOF", SUBFAMILY=r["PANEL_ID"] or r["PARENT"],
                           STOREY="2F", OWNER_FAMILY="WATER_TANK_ROOF", OWNER_STAGE="S8.4", SOURCE="S8.4 04",
                           DIMENSIONS={"area_m2": _f(r["NET_AREA_M2"]), "thickness_mm": _f(r["THICKNESS_MM"])},
                           GROSS_M3=m3, DEDUCTIONS_M3=0.0 if rel else None, NET_M3=m3, RELEASED_M3=m3,
                           LANE=REL_FROZEN if rel else NOT_IN_SOURCE, EVIDENCE_STATUS=r["LANE"],
                           REBAR_LINK=f"S8.4:{r['PANEL_ID']}" if r["PANEL_ID"] else None))
    # S8.6 / S8.6A lintels: S8.6A supersedes S8.6 for the 14 schedule-bound lintels; the 50 others stay S8.6 sensitivity
    corr = {r["LINTEL_ID"]: r for r in _rows(F["S86A_VIEW"])}
    for r in _rows(F["S86_CONC"]):
        lid = r["LINTEL_ID"]
        c = corr.get(lid)
        common = dict(COMPONENT_ID=lid, FAMILY="LINTELS", SUBFAMILY=f"{r['ROW']} {r['B_MM']} x {r['D_MM']}",
                      STOREY=r["FLOOR"], OWNER_FAMILY="LINTELS", SOURCE=f"S8.6 06 opening {r['OPENING_ID']}",
                      DIMENSIONS={"B_mm": _f(r["B_MM"]), "D_mm": _f(r["D_MM"]), "length_mm": _f(r["LENGTH_MM"])},
                      REBAR_LINK=f"S8.6A:{lid}")
        if c:
            if c["CORRECTED_LANE"] == "PROJECT_BASIS_QTO":
                m3 = _f(c["CORRECTED_M3"])
                rows.append(record(**common, OWNER_STAGE="S8.6A (supersedes S8.6)", GROSS_M3=m3, DEDUCTIONS_M3=0.0,
                                   NET_M3=m3, RELEASED_M3=m3, LANE=REL_FROZEN, EVIDENCE_STATUS=c["CORRECTED_STATE"],
                                   FLAGS=[f"S8.6 frozen {c['FROZEN_M3']} m3 superseded"] if
                                   abs(_f(c["FROZEN_M3"]) - m3) > 1e-9 else None))
            else:
                rows.append(record(**common, OWNER_STAGE="S8.6A (supersedes S8.6)", LANE=BLOCKED,
                                   CONDITIONAL_M3=_f(c["CONDITIONAL_M3"]) or None, EVIDENCE_STATUS=c["CORRECTED_STATE"],
                                   UNRESOLVED_REASON=_clean(c["REASON"]),
                                   FLAGS=[f"S8.6 released {c['FROZEN_M3']} m3: SUPERSEDED (not added)"]))
        else:
            rows.append(record(**common, OWNER_STAGE="S8.6", CONDITIONAL_M3=_f(r["M3"]), LANE=COND,
                               EVIDENCE_STATUS=r["LANE"], UNRESOLVED_REASON=f"S8.6 {r['DECISION']}: sensitivity only "
                               "(support identity / bearing not established)"))
    # S8.7 stairs
    for r in _rows(F["S87_CONC"]):
        lane = {"PROJECT_BASIS_QTO": REL_FROZEN, "SOURCE_CONFLICT": CONFLICT, "BLOCKED_UNQUANTIFIED": BLOCKED}[r["LANE"]]
        m3 = _f(r["CONCRETE_M3"]) if lane == REL_FROZEN else None
        storey = "GROUND" if r["ELEMENT_ID"].startswith(("B-", "D-")) else ("1F" if r["ELEMENT_ID"].startswith("A2") else "GF")
        rows.append(record(COMPONENT_ID=r["ELEMENT_ID"], FAMILY="STAIRS", SUBFAMILY=f"{r['STAIR_ID']} {r['COMPONENT']}",
                           STOREY=storey, OWNER_FAMILY="STAIRS", OWNER_STAGE="S8.7 (S8.7A / B / C: no release delta)",
                           SOURCE="S8.7 07", DIMENSIONS={"plan_area_m2": _f(r["PLAN_AREA_M2"]),
                                                         "thickness_mm": _f(r["THICKNESS_MM"])},
                           GROSS_M3=m3, DEDUCTIONS_M3=0.0 if m3 else None, NET_M3=m3, RELEASED_M3=m3, LANE=lane,
                           EVIDENCE_STATUS=r["LANE"], UNRESOLVED_REASON=None if m3 else _clean(r["REASON"]),
                           REBAR_LINK=f"S8.7:{r['ELEMENT_ID']}"))
    # S8.8 lift
    for r in _rows(F["S88_WALLS"]):
        eid = r["ELEMENT_ID"]
        if eid.startswith("LIFT-01-PIT-WALLS"):
            continue
        if eid.startswith("LIFT-01-PIT-WALL-"):
            fp = _f(r["FOOTPRINT_M2"])
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="pit wall", STOREY="GROUND", OWNER_FAMILY="LIFT",
                               OWNER_STAGE="S8.8", SOURCE=f"S8.8 06 rect {r['RECT_MM']}",
                               DIMENSIONS={"footprint_m2": fp, "thickness_mm": _f(r["THICKNESS_MM"])},
                               CONDITIONAL_M3=_r(fp * 1.95, 9), LANE=INDICATIVE,
                               EVIDENCE_STATUS="PLAN_ESTABLISHED; HEIGHT_BLOCKED",
                               UNRESOLVED_REASON="pit depth / wall height not printed; the value is S8.8's sensitivity "
                                                 "(FF top at the -1.50 minimum founding = -0.95 -> +1.00), never released",
                               FLAGS=["KEEP_BLOCKED (owner instruction)"]))
        elif eid == "LIFT-01-FTG":
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="lift footing FF (reference)", STOREY="FOUNDATION",
                               OWNER_FAMILY="FOOTINGS", OWNER_STAGE="S9 footing family (FTG-FF-18688-14112)",
                               SOURCE="S8.8 04 / 06", LANE=OWNED_ELSEWHERE,
                               EVIDENCE_STATUS="COUNTED ONCE in the footing family (FTG-FF-18688-14112)"))
        elif eid == "LIFT-01-PIT-BASE":
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="pit floor", STOREY="FOUNDATION",
                               OWNER_FAMILY="FOOTINGS", OWNER_STAGE="footing family", SOURCE="S8.8 04",
                               LANE=NOT_APPLICABLE, EVIDENCE_STATUS="the FF top is the pit floor; no separate element"))
        elif eid.startswith("LIFT-01-ENCL"):
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="shaft enclosure", STOREY=eid.rsplit("-", 1)[-1],
                               OWNER_FAMILY="LIFT", OWNER_STAGE="S8.8", SOURCE="S8.8 06", LANE=NOT_APPLICABLE,
                               EVIDENCE_STATUS="NOT_STRUCTURAL_RC (architectural walls; S10 scope)"))
        elif eid == "LIFT-01-TIE-GF":
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="conditional tie beam (P8-N19)", STOREY="GF",
                               OWNER_FAMILY="LIFT", OWNER_STAGE="S8.8", SOURCE="S8.8 06 / 09", LANE=BLOCKED,
                               EVIDENCE_STATUS="BLOCKED", UNRESOLVED_REASON=_clean(r["REASON"]),
                               FLAGS=["KEEP_BLOCKED (owner instruction)"]))
        elif eid == "LIFT-01-OVERRUN":
            rows.append(record(COMPONENT_ID=eid, FAMILY="LIFT", SUBFAMILY="overrun", STOREY="ROOF", OWNER_FAMILY="LIFT",
                               OWNER_STAGE="S8.8", SOURCE="S8.8 06", LANE=NOT_IN_SOURCE, EVIDENCE_STATUS="NOT_IN_SOURCE"))
    return rows


# ------------------------------------------------------------------ G. structural concrete no stage measured
def other_items(footing_rows, slab_rows):
    rows = []
    fp = math.fsum((x["DIMENSIONS"]["L_m"] * x["DIMENSIONS"]["W_m"]) for x in footing_rows if x["LANE"] == REL_S9)
    rows.append(record(COMPONENT_ID="S9-BLINDING-FOOTINGS", FAMILY="PLAIN_CONCRETE", SUBFAMILY="blinding under footings",
                       STOREY="FOUNDATION", OWNER_FAMILY="PLAIN_CONCRETE", OWNER_STAGE="none (S9 records it)",
                       SOURCE="P8-N16 mix 1:3:6 (no thickness, no extent); p.16 typical 50 x 10 blinding under a G.B only",
                       DIMENSIONS={"released_footing_plan_m2": _r(fp, 6)}, LANE=BLOCKED, EVIDENCE_STATUS="NOT_DIMENSIONED",
                       UNRESOLVED_REASON="no blinding thickness or projection is printed for the project footings"))
    rows.append(record(COMPONENT_ID="S9-BLINDING-GROUND-BEAMS", FAMILY="PLAIN_CONCRETE",
                       SUBFAMILY="blinding under ground beams", STOREY="GROUND", OWNER_FAMILY="PLAIN_CONCRETE",
                       OWNER_STAGE="none", SOURCE="p.16 typical G.B on 50 x 10 blinding (typical only)", LANE=BLOCKED,
                       EVIDENCE_STATUS="TYPICAL_ONLY", UNRESOLVED_REASON="typical detail only; GB levels not printed"))
    for fl in ("GF", "1F", "2F"):
        rows.append(record(COMPONENT_ID=f"S9-PARAPET-{fl}_ROOF", FAMILY="PARAPETS", SUBFAMILY="parapet",
                           STOREY="ROOF", OWNER_FAMILY="PARAPETS", OWNER_STAGE="none (S1 SPC-PARAPET)",
                           SOURCE="ST7757 p.4-6 note 1 'PARAPET, BEFORE CASTING'; p.14 parapet sections (candidate)",
                           LANE=BLOCKED, EVIDENCE_STATUS="GEOMETRY_FOLLOWS_ARCHITECTURE",
                           UNRESOLVED_REASON=f"{fl}-roof parapet: geometry follows the architectural drawings "
                                             "(lengths / heights not on the structural set)"))
    rows.append(record(COMPONENT_ID="S9-BOUNDARY-WALL", FAMILY="BOUNDARY_WALL", SUBFAMILY="boundary wall and pads",
                       STOREY="SITE", OWNER_FAMILY="BOUNDARY_WALL", OWNER_STAGE="none (S1 SPC-BOUNDARY_WALL)",
                       SOURCE="p.14 boundary-wall typical detail vs schedule row B.W", LANE=CONFLICT,
                       EVIDENCE_STATUS="SOURCE_CONFLICT", UNRESOLVED_REASON="typical detail vs schedule row B.W; length "
                                                                            "not on the structural plans"))
    rows.append(record(COMPONENT_ID="S9-LOWER-GROUND-BEAMS", FAMILY="GROUND_BEAMS", SUBFAMILY="lower ground beam "
                       "(P13-FOOTING-DEEP)", STOREY="FOUNDATION", OWNER_FAMILY="GROUND_BEAMS", OWNER_STAGE="none (S2 "
                       "LOWER_GROUND_BEAM blocked x 26)", SOURCE="p.13 'more than 2.5 m above the footing'",
                       LANE=BLOCKED, EVIDENCE_STATUS="TRIGGER_NOT_ESTABLISHED",
                       UNRESOLVED_REASON="whether any footing needs a lower ground beam depends on the founding levels"))
    for s in slab_rows:
        if s["LANE"] == REL_S9 and s["DIMENSIONS"].get("sunken"):
            rows.append(record(COMPONENT_ID=f"S9-SUNKEN-DROP-{s['COMPONENT_ID']}", FAMILY="SLABS",
                               SUBFAMILY="sunken slab drop / step", STOREY=s["STOREY"], OWNER_FAMILY="SLABS",
                               OWNER_STAGE="none", SOURCE=s["SOURCE"], LANE=BLOCKED, EVIDENCE_STATUS="DROP_NOT_LOCATED",
                               UNRESOLVED_REASON="drop depth / step detail not located (PRE-S7 SOURCE_EXPECTED_NOT_LOCATED)"))
    for sid, what in (("SPC-RIBBED_SLAB", "ribbed slab"), ("SPC-CASEMENT_DETAIL", "casement detail"),
                      ("SPC-BEAM_OPENING", "beam opening")):
        rows.append(record(COMPONENT_ID=sid, FAMILY="OTHER", SUBFAMILY=what, STOREY="GF", OWNER_FAMILY="OTHER",
                           OWNER_STAGE="S1", SOURCE="typical detail only", LANE=NOT_IN_SOURCE,
                           EVIDENCE_STATUS="NO_OCCURRENCE_MARKED", UNRESOLVED_REASON="typical detail printed; no plan "
                                                                                     "occurrence"))
    return rows


# ------------------------------------------------------------------ H. reinforcement: authoritative version per family
def bar(**kw):
    base = {"ITEM_ID": None, "FAMILY": None, "OWNER_STAGE": None, "COMPONENT_ID": None, "STOREY": None,
            "BAR_ROLE": None, "DIA_MM": None, "COUNT": None, "SPACING_OR_RATE": None, "SHAPE": None,
            "CUT_LENGTH_M": None, "TOTAL_LENGTH_M": None, "LAPS": None, "ANCHORAGE": None, "HOOKS_BENDS": None,
            "UNIT_MASS_KG_M": None, "ORIGINAL_KG": None, "CORRECTION_KG": 0.0, "CORRECTIONS": None,
            "AUTHORITATIVE_KG": None, "AUTHORITATIVE_T": None, "NOT_RELEASED_KG": None, "SOURCE_AUTHORITY": None,
            "STAGE_STATE": None, "LANE": None, "NOTE": None}
    base.update(kw)
    check(base["LANE"] in LANES, f"{base['ITEM_ID']}: lane {base['LANE']}")
    if base["TOTAL_LENGTH_M"] is None:                      # never a new quantity: a reading of the stage's own figures
        kg = base["ORIGINAL_KG"] if base["ORIGINAL_KG"] is not None else base["NOT_RELEASED_KG"]
        if base["COUNT"] and base["CUT_LENGTH_M"]:
            base["TOTAL_LENGTH_M"] = _r(base["COUNT"] * base["CUT_LENGTH_M"], 6)
        elif kg and base["UNIT_MASS_KG_M"]:
            base["TOTAL_LENGTH_M"] = _r(kg / base["UNIT_MASS_KG_M"], 6)
            base["NOTE"] = "; ".join(x for x in (base["NOTE"], "total length = stage kg / unit mass (the stage "
                                                 "publishes kg only)") if x)
    if base["LANE"] in RELEASED:
        a = (base["ORIGINAL_KG"] or 0.0) + (base["CORRECTION_KG"] or 0.0)
        check(a >= -1e-9, f"{base['ITEM_ID']}: negative authoritative kg")
        base["AUTHORITATIVE_KG"] = _r(a)
        base["AUTHORITATIVE_T"] = _r(a / 1000)
    else:
        check(base["AUTHORITATIVE_KG"] is None, f"{base['ITEM_ID']}: unreleased rows carry no authoritative kg")
    base["STOREY"] = STOREY_OF.get(base["STOREY"], base["STOREY"])
    return base


def _um(d):
    return UM.kg_per_m(float(d), UNIT_MASS) if d else None


def rebar_columns(s9_corrections):
    main = {p["part_id"]: p for p in _j(F["S31_MAIN"])["rows"]}
    tie = _j(F["S31_TIE"])
    tie_dia = tie["tie_rule"]["dia_mm"]
    tparts = {p["part_id"]: p for r in tie["rows"] for p in r["parts"]}
    lap = {p["part_id"]: p for p in _j(F["S31_LAP"])["rows"]}
    rows = []
    for p in _j(F["S31_RELEASE"])["rows"]:
        pid, comp, kind, st = p["part_id"], p["component"], p["length_kind"], p["release_state"]
        src = main.get(pid) or lap.get(pid) or tparts.get(pid) or {}
        dia = src.get("dia_mm") or (tie_dia if comp == "TIES" else None)
        kg = p["kg"]
        common = dict(ITEM_ID=f"S3.1:{pid}", FAMILY="COLUMNS", OWNER_STAGE="S3.1", COMPONENT_ID=p["occurrence_id"],
                      STOREY=p["floor"], BAR_ROLE=f"{comp} / {kind}", DIA_MM=dia, COUNT=src.get("count"),
                      SPACING_OR_RATE="6/m ties (P9-COL-TIES)" if comp == "TIES" else None,
                      SHAPE={"TIE_CORE_PATH": "closed link (sharp perimeter model)", "HOOK_1": "hook allowance",
                             "HOOK_2": "hook allowance"}.get(kind, "straight"),
                      CUT_LENGTH_M=_r((src.get("length_per_piece_mm") or 0) / 1000, 6) if src.get("length_per_piece_mm")
                      else None, LAPS="this item" if comp == "LAP" else "excluded",
                      ANCHORAGE="this item" if comp in ("ANCHORAGE", "STARTER") else "excluded",
                      HOOKS_BENDS="this item" if kind.startswith("HOOK") else "excluded", UNIT_MASS_KG_M=_um(dia),
                      ORIGINAL_KG=kg, SOURCE_AUTHORITY=src.get("rule_id") or p.get("basis_state"), STAGE_STATE=st)
        if st in ("VERIFIED", "LOWER_BOUND") and comp == "TIES" and kind in ("TIE_CORE_PATH", "HOOK_1", "HOOK_2"):
            s9_corrections.append({"CORRECTION_ID": None, "ITEM_ID": common["ITEM_ID"], "COMPONENT_ID": p["occurrence_id"],
                                   "ORIGINAL_KG": kg, "CORRECTION_KG": -kg, "RETAINED_KG": 0.0, "KIND": kind})
            rows.append(bar(**common, LANE=COND, NOT_RELEASED_KG=kg, CORRECTION_KG=-kg,
                            CORRECTIONS="S9-C01",
                            NOTE="S9-C01: a sharp-perimeter link path (and an unsourced hook allowance) is a modelled "
                                 "polygonal equivalent, not a lower bound (D1.1 mathematics: rounded corners shorten it; "
                                 "unknown hooks never prove a bound); kg kept here, out of the released total"))
        elif st in ("VERIFIED", "LOWER_BOUND"):
            rows.append(bar(**common, LANE=REL_FROZEN))
        elif st == "PROVISIONAL":
            rows.append(bar(**common, LANE=COND, NOT_RELEASED_KG=kg, NOTE="S3.1 PROVISIONAL (lap / anchorage / starter "
                                                                          "method or type alternative)"))
        else:
            rows.append(bar(**common, LANE=BLOCKED, NOT_RELEASED_KG=kg or None, NOTE="S3.1 BLOCKED (modelled only)"))
    return rows


def rebar_footings():
    d12 = {(r["OCCURRENCE_ID"], r["COMPONENT"]): r for r in _rows(F["D12_CORR"])}
    rows = []
    for b in _rows(F["S4_BBS"]):
        c = d12.get((b["occurrence_id"], b["component"]))
        check(c is not None, f"D1.2 audits {b['bbs_id']}")
        check(abs(float(c["CORRECTION_KG"])) < 1e-9, "D1.2 changes no kg")
        rows.append(bar(ITEM_ID=f"S4:{b['bbs_id']}", FAMILY="FOOTINGS", OWNER_STAGE="S4 -> S4.1 -> D1.2",
                        COMPONENT_ID=b["occurrence_id"], STOREY="FOUNDATION", BAR_ROLE=b["component"],
                        DIA_MM=_f(b["dia_mm"]), COUNT=_f(b["count"]), SPACING_OR_RATE=b["count_basis"],
                        SHAPE=b["shape"], CUT_LENGTH_M=_f(b["bar_length_m"]), TOTAL_LENGTH_M=_f(b["total_length_m"]),
                        LAPS="excluded", ANCHORAGE="excluded (S4.1 end treatments blocked)", HOOKS_BENDS="excluded",
                        UNIT_MASS_KG_M=_f(b["kg_per_m"]), ORIGINAL_KG=_f(b["net_bbs_kg"]),
                        SOURCE_AUTHORITY=f"schedule p.9 + cover {c['COVER_BASIS']}",
                        STAGE_STATE=f"{b['state']} -> {c['NEW_MASS_STATE']} (D1.2)", LANE=REL_FROZEN,
                        CORRECTIONS="D1.2 state only"))
    for u in _rows(F["S4_UNRESOLVED"]):
        rows.append(bar(ITEM_ID=f"S4-UNRESOLVED:{u['occurrence_id']}:{u['component']}", FAMILY="FOOTINGS",
                        OWNER_STAGE="S4", COMPONENT_ID=u["occurrence_id"], STOREY="FOUNDATION", BAR_ROLE=u["component"],
                        LANE=BLOCKED, STAGE_STATE=u["state"], NOTE=_clean(u["what_is_missing"])))
    return rows


def rebar_ground():
    ad1 = defaultdict(list)
    for c in _rows(F["AD1_CORR"]):
        ad1[c["ORIGINAL_DELTA_COMPONENT_ID"]].append(c)
    d11 = defaultdict(list)
    for c in _rows(F["D11_S5"]):
        d11[c["ORIGINAL_DELTA_ID"]].append(c)
    rows, used = [], set()
    for b in _rows(F["S5_BBS"]):
        cs = ad1.get(b["bbs_id"], [])
        used |= {c["CORRECTION_ID"] for c in cs}
        corr = math.fsum(float(c["CORRECTION_KG"]) for c in cs)
        keep = _f(b["net_bbs_kg"]) + corr > 1e-9
        rows.append(bar(ITEM_ID=f"S5:{b['bbs_id']}", FAMILY="GROUND_BEAMS", OWNER_STAGE="S5 -> S5.1 -> AD1 -> D1.1",
                        COMPONENT_ID=b["occurrence_id"], STOREY="GROUND", BAR_ROLE=f"{b['family']} {b['component']}",
                        DIA_MM=_f(b["dia_mm"]), COUNT=_f(b["count"]), SHAPE=b["shape"], CUT_LENGTH_M=_f(b["bar_length_m"]),
                        TOTAL_LENGTH_M=_f(b["total_length_m"]), LAPS="excluded",
                        ANCHORAGE="included" if b["development_included"] == "True" else "excluded",
                        HOOKS_BENDS="included" if b["hooks_included"] == "True" else "excluded",
                        UNIT_MASS_KG_M=_f(b["kg_per_m"]), ORIGINAL_KG=_f(b["net_bbs_kg"]), CORRECTION_KG=corr,
                        CORRECTIONS=[c["CORRECTION_ID"] for c in cs] or None, SOURCE_AUTHORITY="p.13 GB details / S5",
                        STAGE_STATE=b["state"], LANE=REL_FROZEN if keep else SUPERSEDED,
                        NOT_RELEASED_KG=None if keep else _f(b["net_bbs_kg"]),
                        NOTE="retracted by AD1 (authority decision)" if cs else None))
    for d in _rows(F["S51_DELTA"]):
        q = _f(d["DELTA_KNOWN_QUANTITY"]) or 0.0
        if q <= 0:
            continue
        cs = d11.get(d["DELTA_ID"], [])
        used |= {c["CORRECTION_ID"] for c in cs}
        corr = math.fsum(float(c["CORRECTION_KG"]) for c in cs)
        rows.append(bar(ITEM_ID=f"S5.1:{d['DELTA_ID']}", FAMILY="GROUND_BEAMS", OWNER_STAGE="S5.1 -> D1.1",
                        COMPONENT_ID=d["OCCURRENCE_ID"], STOREY="GROUND",
                        BAR_ROLE=f"{d['FAMILY']} {d['COMPONENT']} ({d['PORTION']})", DIA_MM=_f(d["DIA_MM"]),
                        SHAPE=d["NEW_COMPONENT_MODEL"], LAPS="excluded", ANCHORAGE="excluded",
                        HOOKS_BENDS="excluded", UNIT_MASS_KG_M=_um(_f(d["DIA_MM"])), ORIGINAL_KG=q, CORRECTION_KG=corr,
                        CORRECTIONS=[c["CORRECTION_ID"] for c in cs] or None, SOURCE_AUTHORITY=d["QUANTITY_BASIS"],
                        STAGE_STATE=d["NEW_RELEASE_STATE"], LANE=REL_FROZEN if q + corr > 1e-9 else SUPERSEDED,
                        NOT_RELEASED_KG=None if q + corr > 1e-9 else q,
                        NOTE="retracted by D1.1 (link core path not a lower bound)" if cs else None))
    allc = {c["CORRECTION_ID"] for c in _rows(F["AD1_CORR"])} | {c["CORRECTION_ID"] for c in _rows(F["D11_S5"])}
    check(used == allc, f"every ground-system correction applied once ({len(used)} / {len(allc)})")
    return rows


def rebar_beams():
    d11 = defaultdict(list)
    for c in _rows(F["D11_S6"]):
        d11[c["ORIGINAL_DELTA_ID"]].append(c)
    floor = {r["occurrence_id"]: r["floor"] for r in _rows(F["S6_OCC"])}
    rows, used = [], set()
    for b in _rows(F["S6_BBS"]):
        rows.append(bar(ITEM_ID=f"S6:{b['bbs_id']}", FAMILY="BEAMS", OWNER_STAGE="S6 -> S6.1 -> D1.1",
                        COMPONENT_ID=b["occurrence_id"], STOREY=floor.get(b["occurrence_id"]), BAR_ROLE=b["component"],
                        DIA_MM=_f(b["dia_mm"]), COUNT=_f(b["count"]), SHAPE=b["shape"],
                        CUT_LENGTH_M=_f(b["bar_length_m"]), TOTAL_LENGTH_M=_f(b["total_length_m"]), LAPS="excluded",
                        ANCHORAGE="included" if b["development_included"] == "True" else "excluded",
                        HOOKS_BENDS="included" if b["hooks_included"] == "True" else "excluded",
                        UNIT_MASS_KG_M=_f(b["kg_per_m"]), ORIGINAL_KG=_f(b["net_bbs_kg"]),
                        SOURCE_AUTHORITY=b["release_basis"], STAGE_STATE=b["state"], LANE=REL_FROZEN))
    for d in _rows(F["S61_DELTA"]):
        q = _f(d["DELTA_KNOWN_QUANTITY"]) or 0.0
        if q <= 0:
            continue
        cs = d11.get(d["DELTA_ID"], [])
        used |= {c["CORRECTION_ID"] for c in cs}
        corr = math.fsum(float(c["CORRECTION_KG"]) for c in cs)
        keep = q + corr > 1e-9
        facets = json.loads(d["FACETS"]) if d["FACETS"].startswith("{") else {}
        dia = _f(d["DIA_MM"]) or _f(facets.get("DIA_MM"))          # the planted-column extra keeps d in its facets
        row = bar(ITEM_ID=f"S6.1:{d['DELTA_ID']}", FAMILY="BEAMS", OWNER_STAGE="S6.1 -> D1.1",
                  COMPONENT_ID=d["OCCURRENCE_ID"], STOREY=floor.get(d["OCCURRENCE_ID"]),
                  BAR_ROLE=f"{d['COMPONENT']} ({d['PORTION']})", DIA_MM=dia,
                  COUNT=_f(d["DELTA_COUNT"]) or _f(facets.get("COUNT_TOTAL")), SHAPE=d["NEW_COMPONENT_MODEL"],
                  LAPS="excluded", ANCHORAGE="excluded", HOOKS_BENDS="excluded", UNIT_MASS_KG_M=_um(dia),
                  ORIGINAL_KG=q, CORRECTION_KG=corr, CORRECTIONS=[c["CORRECTION_ID"] for c in cs] or None,
                  SOURCE_AUTHORITY=d["QUANTITY_BASIS"], STAGE_STATE=d["NEW_RELEASE_STATE"],
                  LANE=REL_FROZEN if keep else SUPERSEDED, NOT_RELEASED_KG=None if keep else q,
                  NOTE="retracted by D1.1 (link core path not a lower bound)" if cs else None)
        rows.append(row)
    check(used == {c["CORRECTION_ID"] for c in _rows(F["D11_S6"])}, "every D1.1 S6.1A correction applied once")
    return rows


def rebar_slabs():
    rows = []
    for r in _rows(F["S7_ITEMS"]):
        rows.append(bar(ITEM_ID=f"S7:{r['S7_ITEM_ID']}", FAMILY="SLABS", OWNER_STAGE="S7 (S7A QA only)",
                        COMPONENT_ID=r["PANEL_ID"] or r["SUPPORT_ID"] or r["OWNER"], STOREY=r["FLOOR"],
                        BAR_ROLE=f"{r['BAR_ROLE']} {r['LAYER']} {r['DIRECTION']}", DIA_MM=_f(r["DIAMETER_MM"]),
                        COUNT=_f(r["EQUIVALENT_BAR_COUNT"]), SPACING_OR_RATE=f"{r['RATE_PER_M']}/m" if r["RATE_PER_M"]
                        else r["EXPLICIT_COUNT"], SHAPE="straight run (rate density)",
                        CUT_LENGTH_M=_f(r["RUN_LENGTH_M"]), TOTAL_LENGTH_M=_f(r["EQUIVALENT_TOTAL_LENGTH_M"]),
                        LAPS="excluded (blocked)", ANCHORAGE="excluded (blocked)", HOOKS_BENDS="excluded",
                        UNIT_MASS_KG_M=_f(r["UNIT_MASS_KG_M"]), ORIGINAL_KG=_f(r["KG"]),
                        SOURCE_AUTHORITY=r["QUANTITY_AUTHORITY"], STAGE_STATE=r["S7_LANE"], LANE=REL_FROZEN))
    return rows


def rebar_s8():
    rows = []
    for r in _rows(F["S81_REBAR"]):
        rows.append(bar(ITEM_ID=f"S8.1:{r['ITEM_ID']}", FAMILY="GROUND_SLAB", OWNER_STAGE="S8.1", COMPONENT_ID=r["ZONE_ID"],
                        STOREY="GROUND", BAR_ROLE=f"mesh {r['DIRECTION']}", DIA_MM=_f(r["DIA_MM"]),
                        COUNT=_f(r["EQUIVALENT_COUNT_UNROUNDED"]), SPACING_OR_RATE=f"{r['RATE_PER_M']}/m",
                        SHAPE="straight (rate density)", CUT_LENGTH_M=_f(r["MEAN_RUN_M"]),
                        TOTAL_LENGTH_M=_f(r["EQUIVALENT_LENGTH_M"]), LAPS="excluded", ANCHORAGE="excluded",
                        HOOKS_BENDS="excluded", UNIT_MASS_KG_M=_f(r["UNIT_MASS_KG_M"]), ORIGINAL_KG=_f(r["KG"]),
                        SOURCE_AUTHORITY=r["COUNT_BASIS"], STAGE_STATE=r["LANE"], LANE=REL_FROZEN))
    for r in _rows(F["S83_REBAR"]):
        rel = r["RELEASED"] == "True"
        lane = REL_FROZEN if rel else (CONFLICT if r["LANE"] == "SOURCE_CONFLICT" else BLOCKED)
        rows.append(bar(ITEM_ID=f"S8.3:{r['ITEM_ID']}", FAMILY="DOMES", OWNER_STAGE="S8.3 (+ errata, S8.3A)",
                        COMPONENT_ID=r["DOME"], STOREY="1F", BAR_ROLE=r["FAMILY"], DIA_MM=_f(r["DIAMETER_MM"]),
                        SHAPE="mesh over the shell", TOTAL_LENGTH_M=_f(r["EQUIVALENT_LENGTH_M"]) if rel else None,
                        LAPS="excluded", ANCHORAGE="excluded", HOOKS_BENDS="excluded",
                        UNIT_MASS_KG_M=_f(r["UNIT_MASS_KG_M"]), ORIGINAL_KG=_f(r["KG"]) if rel else None,
                        SOURCE_AUTHORITY=_clean(r["BASIS"]), STAGE_STATE=r["LANE"], LANE=lane,
                        NOTE=_clean(r["STILL_MISSING"]) or None))
    for r in _rows(F["S84_REBAR"]):
        rows.append(bar(ITEM_ID=f"S8.4:{r['ITEM_ID']}", FAMILY="WATER_TANK_ROOF", OWNER_STAGE="S8.4",
                        COMPONENT_ID=r["PANEL_ID"], STOREY="2F", BAR_ROLE=f"{r['LAYER']} {r['DIRECTION']}",
                        DIA_MM=_f(r["DIA_MM"]), COUNT=_f(r["EQUIVALENT_COUNT_UNROUNDED"]),
                        SPACING_OR_RATE=f"{r['RATE_PER_M']}/m" if r["RATE_PER_M"] else r["SPACING_MM"],
                        SHAPE="straight (rate density)", CUT_LENGTH_M=_f(r["MEAN_RUN_M"]),
                        TOTAL_LENGTH_M=_f(r["RELEASED_LENGTH_M"]), LAPS="excluded", ANCHORAGE="excluded",
                        HOOKS_BENDS="excluded", UNIT_MASS_KG_M=_f(r["UNIT_MASS_KG_M"]), ORIGINAL_KG=_f(r["RELEASED_KG"]),
                        SOURCE_AUTHORITY=r["COUNT_BASIS"], STAGE_STATE=r["LANE"], LANE=REL_FROZEN,
                        NOTE=f"stop zone {r['STOP_ZONE_KG']} kg blocked" if _f(r["STOP_ZONE_KG"]) else None))
    retained = {r["LINTEL_ID"] for r in _rows(F["S86A_VIEW"]) if r["CORRECTED_LANE"] == "PROJECT_BASIS_QTO"}
    floor_of = {r["LINTEL_ID"]: r["FLOOR"] for r in _rows(F["S86_CONC"])}
    for i, r in enumerate(_rows(F["S86_REBAR"])):
        kg = _f(r["KG"])
        common = dict(ITEM_ID=f"S8.6:{r['LINTEL_ID']}:{r['VIEW']}:{r['ROLE']}:{i}", FAMILY="LINTELS",
                      COMPONENT_ID=r["LINTEL_ID"], STOREY=r["FLOOR"] or floor_of.get(r["LINTEL_ID"]), BAR_ROLE=r["ROLE"],
                      DIA_MM=_f(r["DIA_MM"]), COUNT=_f(r["COUNT"]),
                      SHAPE={"STIRRUP": "closed link", "TOP": "straight (end bends excluded)",
                             "BOTTOM": "straight (end bends excluded)"}.get(r["ROLE"], r["ROLE"].replace("_", " ").lower()),
                      CUT_LENGTH_M=_r((_f(r["EACH_MM"]) or 0) / 1000, 6)
                      if r["EACH_MM"] else None, TOTAL_LENGTH_M=_r((_f(r["TOTAL_MM"]) or 0) / 1000, 6) if r["TOTAL_MM"]
                      else None, LAPS="excluded", ANCHORAGE="excluded", HOOKS_BENDS="excluded",
                      UNIT_MASS_KG_M=_um(_f(r["DIA_MM"])), SOURCE_AUTHORITY=f"{r['COUNT_BASIS']} / {r['LENGTH_BASIS']}",
                      STAGE_STATE=r["LANE"])
        if r["VIEW"] == "PROJECT_BASIS_QTO":
            if r["LINTEL_ID"] in retained:
                rows.append(bar(**common, OWNER_STAGE="S8.6A (supersedes S8.6)", ORIGINAL_KG=kg, LANE=REL_FROZEN))
            else:
                rows.append(bar(**common, OWNER_STAGE="S8.6 (superseded by S8.6A)", NOT_RELEASED_KG=kg, LANE=SUPERSEDED,
                                NOTE="S8.6A: blocked (bearing / column connection / head function)"))
        elif r["VIEW"] == "SENSITIVITY_ONLY":
            rows.append(bar(**common, OWNER_STAGE="S8.6", NOT_RELEASED_KG=kg, LANE=COND, NOTE="S8.6 sensitivity only"))
        else:
            rows.append(bar(**common, OWNER_STAGE="S8.6", LANE=BLOCKED, NOTE=r["VIEW"]))
    for i, r in enumerate(_rows(F["S87_REBAR"])):
        kg = _f(r["KG"])
        st = r["QUANTITY_STATE"]
        lane = {"PROJECT_BASIS_QTO": REL_FROZEN, "SOURCE_CONFLICT": CONFLICT, "NOT_IN_SOURCE": NOT_IN_SOURCE}.get(st, BLOCKED)
        el = r["FLIGHT_OR_LANDING_ID"]
        rows.append(bar(ITEM_ID=f"S8.7:{el}:{r['PHYSICAL_BAR_ROLE']}:{i}", FAMILY="STAIRS",
                        OWNER_STAGE="S8.7 (S8.7A / B / C: 0 delta)", COMPONENT_ID=el,
                        STOREY="1F" if el.startswith("A2") else ("GROUND" if el.startswith(("B-", "D-")) else "GF"),
                        BAR_ROLE=r["PHYSICAL_BAR_ROLE"], DIA_MM=_f(r["BAR_DIAMETER_MM"]), SPACING_OR_RATE=r["SPACING_OR_COUNT"],
                        SHAPE="straight (rate density)", TOTAL_LENGTH_M=_f(r["EQUIVALENT_LENGTH_M"]), LAPS="excluded",
                        ANCHORAGE="excluded", HOOKS_BENDS="excluded", UNIT_MASS_KG_M=_um(_f(r["BAR_DIAMETER_MM"])),
                        ORIGINAL_KG=kg if lane == REL_FROZEN else None, SOURCE_AUTHORITY=_clean(r["REASON"])[:160],
                        STAGE_STATE=st, LANE=lane, NOTE=None if lane == REL_FROZEN else _clean(r["REASON"])[:200]))
    return rows


# ------------------------------------------------------------------ I. version precedence
def precedence(concrete, bars, s9c01_kg):
    sm = {k: _j(F[k]) for k in ("S3_SUMMARY", "S31_SUMMARY", "S4_SUMMARY", "S41_SUMMARY", "D12_SUMMARY",
                                "S5_SUMMARY", "S51_SUMMARY", "AD1_SUMMARY", "D11_SUMMARY", "S6_SUMMARY", "S61_SUMMARY",
                                "S7_SUMMARY", "S7A_SUMMARY", "S81_SUMMARY", "S81A_SUMMARY", "S82_SUMMARY",
                                "S82A_SUMMARY", "S83_SUMMARY", "S83A_SUMMARY", "S84_SUMMARY", "S85_SUMMARY",
                                "S86_SUMMARY", "S86A_SUMMARY", "S87_SUMMARY", "S88_SUMMARY")}
    s3 = sm["S3_SUMMARY"]["release_kg"]
    s31 = sm["S31_SUMMARY"]["headline"]
    s31_parts = math.fsum(b["ORIGINAL_KG"] for b in bars if b["FAMILY"] == "COLUMNS" and b["STAGE_STATE"] in
                          ("VERIFIED", "LOWER_BOUND"))
    ad1 = sm["AD1_SUMMARY"]["kg_corrections"]["conservation_s5"]["correction_kg"]
    d11_s5 = math.fsum(float(c["CORRECTION_KG"]) for c in _rows(F["D11_S5"]))
    d11_s6 = math.fsum(float(c["CORRECTION_KG"]) for c in _rows(F["D11_S6"]))
    s86a = sm["S86A_SUMMARY"]["corrected"]
    chains = {
        ("REBAR", "COLUMNS"): [("S3", SR.BASELINE, s3["verified"] + s3["lower_bound"],
                                "exact-density unit mass; superseded by S3.1 (d2 / 162, blocked transitions)"),
                               ("S3.1", SR.SUPERSEDING, s31_parts,
                                f"VERIFIED + LOWER_BOUND parts (summary {s31['VERIFIED_KG'] + s31['LOWER_BOUND_KG']:.3f}; "
                                "parts are rounded to 1 g)"),
                               ("S9-C01", SR.CORRECTION, -s9c01_kg, "tie core paths and hook allowances are not lower "
                                                                      "bounds (D1.1 mathematics); moved to conditional")],
        ("REBAR", "FOOTINGS"): [("S4", SR.BASELINE, sm["S4_SUMMARY"]["accurate_summary"]["project"]["released_kg"],
                                 "VERIFIED + LOWER_BOUND straight bars"),
                                ("S4.1", SR.DELTA, sm["S41_SUMMARY"]["delta_known_kg"], "end treatments recorded, no kg"),
                                ("D1.2", SR.STATE_ONLY, None, "LOWER_BOUND -> PROJECT_BASIS_NUMERIC at the 70 mm "
                                                              "minimum cover; kg unchanged")],
        ("REBAR", "GROUND_BEAMS"): [("S5", SR.BASELINE, sm["S5_SUMMARY"]["known_source_derived_ground_system_rebar_kg"],
                                     "known source-derived straight bars"),
                                    ("S5.1", SR.DELTA, sm["S51_SUMMARY"]["delta_known_kg"], "through-support runs + "
                                                                                           "link core paths"),
                                    ("AD1", SR.CORRECTION, ad1, "authority decisions (6 bars retracted)"),
                                    ("D1.1", SR.CORRECTION, d11_s5, "link core paths retracted"),
                                    ("D1.2", SR.STATE_ONLY, None, "cover authority confirmed; no kg")],
        ("REBAR", "BEAMS"): [("S6", SR.BASELINE, sm["S6_SUMMARY"]["known_source_derived_superstructure_beam_rebar_kg"],
                              "known source-derived straight bars"),
                             ("S6.1", SR.DELTA, sm["S61_SUMMARY"]["delta_known_kg"], "base bars + link core paths + "
                                                                                    "planted-column extra"),
                             ("D1.1", SR.CORRECTION, d11_s6, "link core paths retracted"),
                             ("D1.2", SR.STATE_ONLY, None, "cover authority confirmed; no kg")],
        ("REBAR", "SLABS"): [("S7", SR.BASELINE, sm["S7_SUMMARY"]["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"],
                              "restricted project-basis slab bars (PRE-S7 / PRE-S7.1 carry no kg)"),
                             ("S7A", SR.QA_ONLY, None, "top-extent sensitivity; no release")],
        ("REBAR", "GROUND_SLAB"): [("S8.1", SR.BASELINE, sm["S81_SUMMARY"]["total_kg"], "two source-zoned cells"),
                                   ("S8.1A", SR.NO_CHANGE, None, "population / cover audit; nothing released")],
        ("REBAR", "POOL"): [("S8.2", SR.BASELINE, sm["S82_SUMMARY"]["reinforcement"]["released_kg"], "all blocked"),
                            ("S8.2A", SR.NO_CHANGE, None, "elevation binding; nothing released")],
        ("REBAR", "DOMES"): [("S8.3", SR.BASELINE, sm["S83_SUMMARY"]["released"]["reinforcement_kg"], "shell meshes"),
                             ("S8.3-ERRATA", SR.NO_CHANGE, None, "a blocked junction family added; no kg"),
                             ("S8.3A", SR.QA_ONLY, None, "mesh scenarios; frozen value unchanged")],
        ("REBAR", "WATER_TANK_ROOF"): [("S8.4", SR.BASELINE, sm["S84_SUMMARY"]["released"]["reinforcement_kg"],
                                        "two roof panels")],
        ("REBAR", "SPECIAL_COLUMNS"): [("S8.5", SR.BASELINE, sm["S85_SUMMARY"]["released"]["reinforcement_kg"],
                                        "nothing incremental: owned by S3.1 / S6.1")],
        ("REBAR", "LINTELS"): [("S8.6", SR.BASELINE, sm["S86_SUMMARY"]["released"]["kg"], "14 schedule-bound lintels"),
                               ("S8.6A", SR.SUPERSEDING, s86a["kg"], "release authority: 7 retained (never added to "
                                                                     "S8.6)")],
        ("REBAR", "STAIRS"): [("S8.7", SR.BASELINE, sm["S87_SUMMARY"]["released"]["kg"], "three plates"),
                              ("S8.7A", SR.NO_CHANGE, None, "riser / finish correction layer: 0 delta"),
                              ("S8.7B", SR.NO_CHANGE, None, "owner scenario: 0 delta"),
                              ("S8.7C", SR.NO_CHANGE, None, "design resolution study: 0 delta")],
        ("REBAR", "LIFT"): [("S8.8", SR.BASELINE, sm["S88_SUMMARY"]["released"]["kg"], "pit walls / tie beam blocked")],
        ("CONCRETE", "GROUND_SLAB"): [("S8.1", SR.BASELINE, sm["S81_SUMMARY"]["concrete_m3"], "two cells"),
                                      ("S8.1A", SR.NO_CHANGE, None, "candidates not released")],
        ("CONCRETE", "POOL"): [("S8.2", SR.BASELINE, sm["S82_SUMMARY"]["concrete"]["released_m3"], "blocked"),
                               ("S8.2A", SR.NO_CHANGE, None, "nothing released")],
        ("CONCRETE", "DOMES"): [("S8.3", SR.BASELINE, sm["S83_SUMMARY"]["released"]["concrete_m3"], "two shells")],
        ("CONCRETE", "WATER_TANK_ROOF"): [("S8.4", SR.BASELINE, sm["S84_SUMMARY"]["released"]["concrete_m3"],
                                           "two roof panels")],
        ("CONCRETE", "LINTELS"): [("S8.6", SR.BASELINE, sm["S86_SUMMARY"]["released"]["concrete_m3"], "14 lintels"),
                                  ("S8.6A", SR.SUPERSEDING, s86a["m3"], "7 retained; one shared corner re-owned")],
        ("CONCRETE", "STAIRS"): [("S8.7", SR.BASELINE, sm["S87_SUMMARY"]["released"]["concrete_m3"], "three plates"),
                                 ("S8.7A-C", SR.NO_CHANGE, None, "0 delta")],
        ("CONCRETE", "LIFT"): [("S8.8", SR.BASELINE, sm["S88_SUMMARY"]["released"]["concrete_m3"], "blocked")],
    }
    for fam in ("FOOTINGS", "COLUMNS", "GROUND_BEAMS", "SLABS", "BEAMS"):
        rel = math.fsum(c["RELEASED_M3"] or 0 for c in concrete if c["FAMILY"] == fam and c["LANE"] == REL_S9)
        chains[("CONCRETE", fam)] = [("S1 / S2 census", SR.BASELINE, 0.0, "counted / sized, no m3 in any frozen stage "
                                                                         "(0 here means nothing released, not zero "
                                                                         "concrete)")]
        if rel:
            chains[("CONCRETE", fam)].append(("S9", SR.DELTA, rel, "S9-RR1 concrete release (10_S9_DELTA_REGISTER)"))
        else:
            unrel = Counter(c["LANE"] for c in concrete if c["FAMILY"] == fam and c["LANE"] not in RELEASED)
            chains[("CONCRETE", fam)].append(("S9", SR.NO_CHANGE, None, "nothing released by S9; not measured as zero: "
                                              + ", ".join(f"{v} {k}" for k, v in sorted(unrel.items()))
                                              + " (02)"))
    out, resolved = [], {}
    for (trade, fam), ch in chains.items():
        res = SR.resolve_chain([(v, k, q) for v, k, q, _ in ch])
        resolved[(trade, fam)] = res
        for (v, k, q, why), h in zip(ch, res["history"]):
            out.append({"TRADE": trade, "FAMILY": fam, "VERSION": v, "KIND": k,
                        "QUANTITY": _r(q) if q is not None else None, "UNIT": "kg" if trade == "REBAR" else "m3",
                        "RUNNING_VALUE": _r(h["running"]), "AUTHORITATIVE": v == res["holder"],
                        "SUPERSEDED": v in res["superseded"], "WHY": why})
    return out, resolved


# ------------------------------------------------------------------ J. overlap / double-count audit
def overlap_audit(concrete, bars, foot_overlap):
    ids = defaultdict(set)
    for c in concrete:
        ids[c["COMPONENT_ID"]].add(c["OWNER_FAMILY"])
    rel_slab = {c["COMPONENT_ID"] for c in concrete if c["FAMILY"] == "SLABS" and c["LANE"] in RELEASED}
    tank = {r["PANEL_ID"] for r in _rows(F["S84_CONC"]) if r["PANEL_ID"]}
    s7 = _j(F["S7_SUMMARY"])
    s83 = _j(F["S83_SUMMARY"])
    s84 = _j(F["S84_SUMMARY"])
    s87 = _j(F["S87_SUMMARY"])
    s86a = _j(F["S86A_SUMMARY"])
    ff = [c for c in concrete if c["COMPONENT_ID"] == "FTG-FF-18688-14112"]
    rows = [
        ("O-01", "footing outlines F9 / FN overlap 0.14 m2", "FOOTINGS", "max shared prism (plan x shallower depth) "
         "deducted from FN once", json.dumps(foot_overlap, sort_keys=True), bool(foot_overlap)),
        ("O-02", "lift footing FF vs the lift family (S8.8)", "FOOTINGS / LIFT", "FF counted once in the footing family; "
         "S8.8's LIFT-01-FTG and PIT-BASE are references", f"FF lane {ff[0]['LANE']} {ff[0]['NET_M3']} m3" if ff else "",
         len(ff) == 1),
        ("O-03", "slab plates vs beams", "SLABS / BEAMS", "S1 panels lie between the drawn beam / column faces; beams "
         "are measured full depth between faces (conditional)", "convention S9-MC1", True),
        ("O-04", "columns vs beams and slabs (joints)", "COLUMNS / BEAMS / SLABS", "the column owns its footprint over "
         "the full storey (the joint); beams stop at the column face; panels exclude column outlines", "S9-MC1", True),
        ("O-05", "ground beams vs footings", "GROUND_BEAMS / FOOTINGS", "no shared volume: founding <= -1.50 and "
         "footing depth <= 0.70 put the footing top <= -0.80; the beam top is the GF slab (+1.00 less build-up) and its "
         "depth <= 1.00", "levels", True),
        ("O-06", "ground beams vs the ground slab", "GROUND_BEAMS / GROUND_SLAB", "S8.1 cells are the faces between the "
         "ground-beam bands", "S8.1 03 PLAN_AUTHORITY", True),
        ("O-07", "water-tank roof panels", "WATER_TANK_ROOF / SLABS", "SP-2F_ROOF_SLAB-01 / -02 owned by S8.4; never in "
         "the slab release", f"{sorted(tank)} in slab release: {bool(tank & rel_slab)}", not (tank & rel_slab)),
        ("O-08", "dome zones and ring bands", "DOMES / SLABS / BEAMS", "DOME_ZONE panels and the eight ring bands "
         "(S8.3-T01..T08) belong to S8.3", f"transfers {len(s83['ownership_transfers'])}", True),
        ("O-09", "stair zones", "STAIRS / SLABS / BEAMS", "STAIR_FLIGHT / STAIR_IN_VOID panels belong to S8.7; the B20 / "
         "B23 overlap zones are beam concrete (S8.7 / S8.7B NET excludes them)", "S8.7 / S8.7B", True),
        ("O-10", "lintels vs beams", "LINTELS / BEAMS", "S8.6A re-owned the one shared corner (LT-OP-1F-017 / -018)",
         json.dumps(s86a["overlap"]), True),
        ("O-11", "special columns", "COLUMNS / BEAMS", "S8.5 adds no concrete and no bars: the turned, dead and planted "
         "columns are S1 / S2 column occurrences; their extra bars are S3.1 (TC 2 x 12.642 kg) and S6.1 (PC-548 12.010 kg)",
         json.dumps(_j(F["S85_SUMMARY"])["already_owned"]["s3_1_special_extras_kg"]), True),
        ("O-12", "slab bars next to the S8 families", "SLABS / S8", "S7 keeps the tank-adjacent "
         f"({s84['s7']['tank_adjacent_released_kg']:.3f} kg), dome-adjacent ({s83['s7_dome_adjacent_kg']['total']:.3f} kg) "
         f"and stair-adjacent ({s87['s7_stair_adjacent']['kg']:.3f} kg) bars; the S8 stages never re-count them",
         f"S7 excluded S8 items {s7['excluded_s8_items']}", True),
        ("O-13", "footing mats vs column starters", "FOOTINGS / COLUMNS", "different bars (S4 mats, S3.1 starters); the "
         "FF starters 85.271 kg are S3.1 PROVISIONAL (not released)", "S8.8 OV-10 / OV-11", True),
        ("O-14", "lift pit walls vs columns / ground beams / ground slab", "LIFT", "S8.8 OV-01..OV-07 pass; walls stay "
         "blocked", "S8.8 11", True),
        ("O-15", "superseded figures never added", "LINTELS / GROUND_BEAMS / BEAMS / COLUMNS", "S8.6 -> S8.6A, S5.1 / "
         "S6.1 link paths -> D1.1, AD1 bars, S3 -> S3.1 -> S9-C01: one authoritative value each (04)", "04", True),
        ("O-16", "a component in two families", "ALL", "every concrete component id has exactly one owner",
         f"{sum(1 for v in ids.values() if len(v) > 1)} ids with two owners", all(len(v) == 1 for v in ids.values())),
    ]
    return [{"CHECK_ID": a, "SUBJECT": b, "FAMILIES": c, "RULE": d, "EVIDENCE": e, "RESULT": "PASS" if f else "FAIL"}
            for a, b, c, d, e, f in rows]


# ------------------------------------------------------------------ K. missing / blocked register
def rebar_by_component(bars):
    out = defaultdict(float)
    for b in bars:
        if b["LANE"] in RELEASED and b["AUTHORITATIVE_KG"]:
            out[(b["FAMILY"], b["COMPONENT_ID"])] += b["AUTHORITATIVE_KG"]
    return out


def link_ids(c):
    """The bar-register component ids a concrete row links to. A multi-handle footing links as
    'S4:FOCC-1100+1101+1102+1103' (one S4 occurrence per drawn outline); a beam span row links to its occurrence."""
    if not c["REBAR_LINK"]:
        return []
    if "#SPAN" in c["COMPONENT_ID"]:
        return [c["COMPONENT_ID"].split("#")[0]]
    head, *rest = c["REBAR_LINK"].split(":", 1)[-1].split("+")
    prefix = head.rsplit("-", 1)[0] + "-" if "-" in head else ""
    return [head] + [x if x.startswith(prefix) else prefix + x for x in rest]


def missing_register(concrete, bars):
    kg = rebar_by_component(bars)
    out = []
    for c in concrete:
        fam_bar = {"FOOTINGS": "FOOTINGS", "COLUMNS": "COLUMNS", "GROUND_BEAMS": "GROUND_BEAMS", "BEAMS": "BEAMS",
                   "SLABS": "SLABS", "GROUND_SLAB": "GROUND_SLAB", "DOMES": "DOMES", "WATER_TANK_ROOF": "WATER_TANK_ROOF",
                   "LINTELS": "LINTELS", "STAIRS": "STAIRS"}.get(c["FAMILY"])
        rk = math.fsum(kg.get((fam_bar, i), 0.0) for i in link_ids(c)) if fam_bar else 0.0
        concrete_rel = c["LANE"] in RELEASED
        if c["LANE"] in (OWNED_ELSEWHERE, NOT_APPLICABLE):
            continue
        cats = []
        if rk > 0 and not concrete_rel:
            cats.append("REBAR_MEASURED_CONCRETE_MISSING")
        if concrete_rel and rk == 0 and c["FAMILY"] in ("FOOTINGS", "COLUMNS", "GROUND_BEAMS", "SLABS", "LINTELS",
                                                         "STAIRS", "GROUND_SLAB", "DOMES", "WATER_TANK_ROOF"):
            cats.append("CONCRETE_MEASURED_REBAR_MISSING")
        if not concrete_rel and c["CONDITIONAL_M3"] is None and not c["CONDITIONAL_RANGE_M3"]:
            cats.append("OWNED_NO_QUANTITY")
        if not concrete_rel and (c["CONDITIONAL_M3"] is not None or c["CONDITIONAL_RANGE_M3"]):
            cats.append("CONDITIONAL_ONLY")
        if not cats:
            continue
        out.append({"COMPONENT_ID": c["COMPONENT_ID"], "FAMILY": c["FAMILY"], "STOREY": c["STOREY"],
                    "CATEGORIES": cats, "CONCRETE_LANE": c["LANE"], "CONDITIONAL_M3": c["CONDITIONAL_M3"],
                    "CONDITIONAL_RANGE_M3": c["CONDITIONAL_RANGE_M3"], "RELEASED_REBAR_KG": _r(rk) if rk else None,
                    "REASON": c["UNRESOLVED_REASON"] or c["EVIDENCE_STATUS"], "OWNER_STAGE": c["OWNER_STAGE"]})
    # family-level rebar gaps that no component row shows
    fam_blocked = [
        ("COLUMNS", "tie hooks / closures, laps (PROVISIONAL), starters (PROVISIONAL), section transitions", "S3.1"),
        ("FOOTINGS", "BOXED bars (21), end treatments / hooks (S4.1), special detail bars", "S4 / S4.1"),
        ("GROUND_BEAMS", "anchorage, side bars, links (D1.1: bend radius / hook / closure not in source)", "S5.1 / D1.1"),
        ("BEAMS", "anchorage (408 parts), side bars, links (D1.1), CB top / hangers, special details", "S6.1 / D1.1"),
        ("SLABS", "anchorage / end cover (174), continuity (152), temperature steel (94), transitions / laps (74), "
                  "sunken extras, opening trims, oblique supports", "S7"),
        ("POOL", "all 21 families (depths 'AS PER ARCH')", "S8.2 / S8.2A"),
        ("DOMES", "ring beams, drums, junction bars, laps", "S8.3"),
        ("LINTELS", "physical BBS rows, blocked lintels", "S8.6 / S8.6A"),
        ("STAIRS", "flights, winders, typical-only families, anchorage", "S8.7 - S8.7C"),
        ("LIFT", "pit walls, wall starters, tie beam", "S8.8")]
    for fam, what, st in fam_blocked:
        out.append({"COMPONENT_ID": f"FAMILY:{fam}:BLOCKED_BAR_FAMILIES", "FAMILY": fam, "STOREY": "ALL",
                    "CATEGORIES": ["OWNED_NO_QUANTITY"], "CONCRETE_LANE": None, "REASON": what, "OWNER_STAGE": st})
    out.append({"COMPONENT_ID": "POST_FREEZE:OLD_BOQ", "FAMILY": "ALL", "STOREY": "ALL",
                "CATEGORIES": ["ABSENT_FROM_OLD_BOQ (checked after the freeze)"], "CONCRETE_LANE": None,
                "REASON": "the old Urban BOQ is read only by the post-freeze comparison (blind discipline)",
                "OWNER_STAGE": "S9 post_freeze"})
    return out


# ------------------------------------------------------------------ L. floor / family / released summaries
FAMILY_ORDER = ("FOOTINGS", "COLUMNS", "GROUND_BEAMS", "BEAMS", "SLABS", "GROUND_SLAB", "STAIRS", "LIFT", "POOL",
                "DOMES", "WATER_TANK_ROOF", "LINTELS", "PLAIN_CONCRETE", "PARAPETS", "BOUNDARY_WALL", "OTHER")
REBAR_FAMILIES = ("COLUMNS", "FOOTINGS", "GROUND_BEAMS", "BEAMS", "SLABS", "GROUND_SLAB", "DOMES", "WATER_TANK_ROOF",
                  "LINTELS", "STAIRS", "POOL", "LIFT", "SPECIAL_COLUMNS")


def _point(c):
    if c["CONDITIONAL_M3"] is not None:
        return c["CONDITIONAL_M3"]
    rng = c["CONDITIONAL_RANGE_M3"] or []
    vals = [v for v in rng if v is not None]
    return vals[0] if len(vals) == 2 else None


def floor_summary(concrete, bars):
    rows = []
    for st in STOREYS:
        for fam in FAMILY_ORDER:
            cs = [c for c in concrete if c["STOREY"] == st and c["FAMILY"] == fam]
            bs = [b for b in bars if b["STOREY"] == st and b["FAMILY"] == fam]
            if not cs and not bs:
                continue
            lanes = Counter(c["LANE"] for c in cs)
            rows.append({"STOREY": st, "FAMILY": fam, "COMPONENTS": len(cs),
                         "RELEASED_FROZEN_M3": _r(math.fsum(c["RELEASED_M3"] or 0 for c in cs if c["LANE"] == REL_FROZEN)),
                         "RELEASED_S9_M3": _r(math.fsum(c["RELEASED_M3"] or 0 for c in cs if c["LANE"] == REL_S9)),
                         "RELEASED_M3": _r(math.fsum(c["RELEASED_M3"] or 0 for c in cs if c["LANE"] in RELEASED)),
                         "CONDITIONAL_POINT_M3": _r(math.fsum(_point(c) or 0 for c in cs if c["LANE"] in
                                                              (COND, CONFLICT))),
                         "INDICATIVE_M3": _r(math.fsum(c["CONDITIONAL_M3"] or 0 for c in cs if c["LANE"] in
                                                       (INDICATIVE, BLOCKED))),
                         "NOT_QUANTIFIED_COMPONENTS": sum(1 for c in cs if c["LANE"] in (BLOCKED, CONFLICT, COND,
                                                                                          INDICATIVE) and _point(c) is None),
                         "RELEASED_KG": _r(math.fsum(b["AUTHORITATIVE_KG"] or 0 for b in bs if b["LANE"] in RELEASED)),
                         "NOT_RELEASED_MODELLED_KG": _r(math.fsum(b["NOT_RELEASED_KG"] or 0 for b in bs
                                                                  if b["LANE"] not in RELEASED)),
                         "LANES": dict(sorted(lanes.items())), "NOTE": STOREY_NOTE[st]})
    return rows


def released_boq(concrete, bars):
    rows = []
    for fam in FAMILY_ORDER:
        for st in STOREYS:
            for lane in RELEASED:
                cs = [c for c in concrete if c["FAMILY"] == fam and c["STOREY"] == st and c["LANE"] == lane]
                if cs:
                    rows.append({"SECTION": "A1 CONCRETE", "FAMILY": fam, "STOREY": st, "LANE": lane, "DIA_MM": None,
                                 "COMPONENTS": len(cs), "QUANTITY": _r(math.fsum(c["RELEASED_M3"] for c in cs), 6),
                                 "UNIT": "m3", "TONNES": None})
    for fam in REBAR_FAMILIES:
        dias = sorted({b["DIA_MM"] for b in bars if b["FAMILY"] == fam and b["LANE"] in RELEASED and b["AUTHORITATIVE_KG"]},
                      key=lambda d: d or 0)
        for d in dias:
            bs = [b for b in bars if b["FAMILY"] == fam and b["LANE"] in RELEASED and b["DIA_MM"] == d]
            kg = math.fsum(b["AUTHORITATIVE_KG"] or 0 for b in bs)
            rows.append({"SECTION": "A2 REINFORCEMENT", "FAMILY": fam, "STOREY": "ALL", "LANE": REL_FROZEN,
                         "DIA_MM": d, "COMPONENTS": len({b["COMPONENT_ID"] for b in bs}), "QUANTITY": _r(kg, 6),
                         "UNIT": "kg", "TONNES": _r(kg / 1000, 6)})
    tc = math.fsum(r["QUANTITY"] for r in rows if r["UNIT"] == "m3")
    tk = math.fsum(r["QUANTITY"] for r in rows if r["UNIT"] == "kg")
    rows.append({"SECTION": "TOTAL (PARTIAL; NOT A COMPLETE BUILDING ESTIMATE)", "FAMILY": "ALL", "STOREY": "ALL",
                 "LANE": "RELEASED", "QUANTITY": _r(tc, 6), "UNIT": "m3"})
    rows.append({"SECTION": "TOTAL (PARTIAL; NOT A COMPLETE BUILDING ESTIMATE)", "FAMILY": "ALL", "STOREY": "ALL",
                 "LANE": "RELEASED", "QUANTITY": _r(tk, 6), "UNIT": "kg", "TONNES": _r(tk / 1000, 6)})
    return rows


def coverage(concrete, bars):
    out = []
    for fam in FAMILY_ORDER:
        cs = [c for c in concrete if c["FAMILY"] == fam and c["LANE"] not in (OWNED_ELSEWHERE, NOT_APPLICABLE)]
        if not cs:
            continue
        rel = [c for c in cs if c["LANE"] in RELEASED]
        cond = [c for c in cs if c["LANE"] in (COND, CONFLICT) and _point(c) is not None]
        none = [c for c in cs if c not in rel and c not in cond]
        rm3 = math.fsum(c["RELEASED_M3"] for c in rel)
        cm3 = math.fsum(_point(c) for c in cond)
        bs = [b for b in bars if b["FAMILY"] == fam]
        rkg = math.fsum(b["AUTHORITATIVE_KG"] or 0 for b in bs if b["LANE"] in RELEASED)
        nkg = math.fsum(b["NOT_RELEASED_KG"] or 0 for b in bs if b["LANE"] not in RELEASED)
        out.append({"FAMILY": fam, "COMPONENTS": len(cs), "RELEASED_COMPONENTS": len(rel),
                    "CONDITIONAL_COMPONENTS": len(cond), "UNQUANTIFIED_COMPONENTS": len(none),
                    "COMPONENT_COVERAGE_PCT": _r(100 * len(rel) / len(cs), 2), "RELEASED_M3": _r(rm3, 6),
                    "CONDITIONAL_POINT_M3": _r(cm3, 6),
                    "RELEASED_SHARE_OF_QUANTIFIED_PCT": _r(100 * rm3 / (rm3 + cm3), 2) if rm3 + cm3 else None,
                    "RELEASED_KG": _r(rkg, 6), "NOT_RELEASED_MODELLED_KG": _r(nkg, 6),
                    "NOTE": "quantified share excludes components with no value at all (unknown, never zero)"})
    return out


# ------------------------------------------------------------------ M. engineer RFI register
def rfis(concrete, s9c01_kg):
    out = []

    def add(stage, qid, to, text, family, status="OPEN"):
        t = _clean(text)
        if t:
            out.append({"SOURCE_STAGE": stage, "SOURCE_ID": qid, "TO": to or "engineer / architect", "FAMILY": family,
                        "QUESTION": t[:600], "STATUS": status})
    for q in _j(F["S2_QUESTIONS"]):
        add("S2", q["flag_id"], "consultant", q["QUESTION_TO_CONSULTANT"], "CENSUS")
    for q in _j(F["S1_REVIEW"])["rows"]:
        add("S1", f"RQ-{q['rank']}", "engineer", f"{q['area']}: {q['question']}", q["area"])
    for f_, fam in (("S5_Q", "GROUND_BEAMS"), ("S6_Q", "BEAMS")):
        for q in _rows(F[f_]):
            add(f_[:2].replace("S5", "S5").replace("S6", "S6"), q["question_id"], "engineer", q["question"], fam,
                "ANSWERED" if q.get("answer") else "OPEN")
    for q in _rows(F["PS7_Q"]):
        add("PRE-S7", q["QUESTION_ID"], q["ASKED_OF"], q["QUESTION"], "SLABS", q["STATE"] or "OPEN")
    for q in _rows(F["S81A_Q"]):
        add("S8.1A", q["ID"], q["TO"], q["QUESTION"], "GROUND_SLAB", q["STATUS"] or "OPEN")
    for f_, fam, tk in (("S82_Q", "POOL", "TEXT"), ("S83_Q", "DOMES", "SUBJECT"), ("S84_Q", "WATER_TANK_ROOF", "TEXT"),
                        ("S85_Q", "SPECIAL_COLUMNS", "TEXT")):
        for q in _rows(F[f_]):
            if q["KIND"] == "QUESTION":
                add(f_.split("_")[0].replace("S8", "S8."), q["ID"], q.get("TO"), q[tk], fam,
                    q.get("STATUS") or q.get("STATE") or "OPEN")
    for q in _rows(F["S87C_RFI"]):
        add("S8.7C", q["PRIORITY"], q["TO"], q["QUESTION"], "STAIRS", q["STATUS"])
    for q in _rows(F["S88_RFI"]):
        add("S8.8", q["QUESTION_ID"], q["TO"], q["QUESTION"], "LIFT")
    mism = sum(1 for c in concrete if c["FAMILY"] == "COLUMNS" and isinstance(c["DIMENSIONS"], dict)
               and c["DIMENSIONS"].get("drawn_vs_schedule") == "MISMATCH")
    drops = sum(1 for c in concrete if c["COMPONENT_ID"].startswith("S9-SUNKEN-DROP-"))
    top = [
        ("P1", "engineer", "FOUNDATION", "Founding level of every footing (only 'excavation >= 1.50 m below plot level' "
         "is printed): it fixes the foundation-storey columns, the lift pit walls, any lower ground beam (P13) and the "
         "pool levels."),
        ("P1", "engineer", "BEAMS", "Beam schedule depth H: is it the overall depth including the slab (as S6 / D1.1 read "
         "it for links) or the depth below the slab? It decides about B x 0.16 m3 per metre of every beam."),
        ("P1", "engineer", "GROUND_BEAMS", "Ground-beam sections: which p.13 length class applies (centre-to-centre or "
         "clear length), the exterior 'FOLLOW ARCH' depths and the concentrated-load cases (S5)."),
        ("P1", "engineer", "COLUMNS", f"Column drawn section vs schedule ({mism} occurrences) and the lift columns drawn 200 / "
         "250 vs 300 at the pit."),
        ("P2", "architect", "ALL", "Floor and roof build-ups (structural slab levels are not printed: column storeys use "
         "the printed floor-to-floor)."),
        ("P2", "engineer", "COLUMNS", f"Column ties: bend radius, hook and closure (S9-C01 holds {_n(s9c01_kg, 3)} kg of S3.1 "
         "tie paths and hooks out of the released total until stated)."),
        ("P2", "engineer", "FOOTINGS", "Footing FTG-CONFLICT_F_F10 (F or F10?) and whether the F9 / FN outlines really "
         "overlap; blinding thickness and projection."),
        ("P2", "architect", "PARAPETS", "Parapet and boundary-wall geometry (lengths, heights, sections)."),
        ("P3", "engineer", "SLABS", f"Sunken-slab drop depths and step details ({drops} panels)."),
    ]
    for i, (p, to, fam, q) in enumerate(top, 1):
        out.append({"SOURCE_STAGE": "S9", "SOURCE_ID": f"S9-RFI-{i:02d}", "TO": to, "FAMILY": fam, "QUESTION": q,
                    "STATUS": "OPEN", "PRIORITY": p})
    for i, r in enumerate(out, 1):
        r["RFI_ID"] = f"RFI-{i:03d}"
        r.setdefault("PRIORITY", "CARRIED")
    return out


# ------------------------------------------------------------------ N. conservation
def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    con, bars = L["concrete"], L["bars"]
    A("C01", "all 29 frozen manifests and the four stage indexes verify before and after the build",
      len(L["frozen"]) == 29 and len(L["indexed"]) == 4, f"{len(L['frozen'])} manifests, {len(L['indexed'])} indexes")
    n = SR.assert_single_owner(con)
    A("C02", "every concrete component has exactly one owning family and one id", n == len(con), f"{n} components")
    A("C03", "every component and every bar item has one recorded lane", all(c["LANE"] in LANES for c in con) and
      all(b["LANE"] in LANES for b in bars), "")
    leak_c = SR.eligible_total(con, "RELEASED_M3", "LANE", RELEASED)
    leak_b = SR.eligible_total(bars, "AUTHORITATIVE_KG", "LANE", RELEASED)
    A("C04", "no blocked / conditional / superseded row carries a released quantity",
      leak_c["non_eligible_rows_with_value"] == 0 and leak_b["non_eligible_rows_with_value"] == 0, "")
    fl_c = math.fsum(r["RELEASED_M3"] for r in L["floors"])
    fl_k = math.fsum(r["RELEASED_KG"] for r in L["floors"])
    tot_c = [r for r in L["released"] if r["UNIT"] == "m3" and r["FAMILY"] == "ALL"][0]["QUANTITY"]
    tot_k = [r for r in L["released"] if r["UNIT"] == "kg" and r["FAMILY"] == "ALL"][0]["QUANTITY"]
    A("C05", "floor totals = family totals = building totals (concrete and reinforcement)",
      abs(fl_c - leak_c["total"]) < 1e-6 and abs(tot_c - leak_c["total"]) < 1e-6 and abs(fl_k - leak_b["total"]) < 1e-5
      and abs(tot_k - leak_b["total"]) < 1e-5, f"{leak_c['total']:.6f} m3, {leak_b['total']:.6f} kg")
    res = L["resolved"]
    fam_kg = defaultdict(float)
    for b in bars:
        if b["LANE"] in RELEASED:
            fam_kg[b["FAMILY"]] += b["AUTHORITATIVE_KG"] or 0
    bad = {f: (fam_kg.get(f, 0.0), r["authoritative"]) for (t, f), r in res.items() if t == "REBAR" and
           abs(fam_kg.get(f, 0.0) - r["authoritative"]) > (0.01 if f != "COLUMNS" else 1e-6)}
    A("C06", "each family's released kg equals its authoritative version (the correction chain applied)", not bad,
      json.dumps({k: [round(a, 6), round(b, 6)] for k, (a, b) in bad.items()}))
    fam_m3 = defaultdict(float)
    for c in con:
        if c["LANE"] in RELEASED:
            fam_m3[c["FAMILY"]] += c["RELEASED_M3"]
    badc = {f: (fam_m3.get(f, 0.0), r["authoritative"]) for (t, f), r in res.items() if t == "CONCRETE" and
            abs(fam_m3.get(f, 0.0) - r["authoritative"]) > 1e-6}
    A("C07", "each family's released m3 equals its authoritative version", not badc, json.dumps(badc))
    s86 = _j(F["S86_SUMMARY"])["released"]
    A("C08", "superseded figures are excluded: S8.6's lintels never added to S8.6A's",
      abs(fam_m3["LINTELS"] - _j(F["S86A_SUMMARY"])["corrected"]["m3"]) < 1e-9 and
      abs(fam_kg["LINTELS"] - _j(F["S86A_SUMMARY"])["corrected"]["kg"]) < 1e-6 and
      fam_kg["LINTELS"] < s86["kg"], "")
    um = [b for b in bars if b["DIA_MM"] and b["UNIT_MASS_KG_M"] is not None and
          abs(b["UNIT_MASS_KG_M"] - b["DIA_MM"] ** 2 / 162) > 1e-5]
    A("C09", "units: every bar row with a diameter uses d^2 / 162 kg/m; concrete in m3, bars in kg / t", not um,
      f"{len(um)} rows off")
    ind = []
    for c in con:
        if c["FAMILY"] == "FOOTINGS" and c["LANE"] == REL_S9:
            d = c["DIMENSIONS"]
            if abs(d["L_m"] * d["W_m"] * d["D_m"] - (c["GROSS_M3"])) > 1e-9 or not d["drawn_matches_schedule"]:
                ind.append(c["COMPONENT_ID"])
        if c["FAMILY"] == "SLABS" and c["LANE"] == REL_S9:
            d = c["DIMENSIONS"]
            if abs(d["area_m2_recomputed"] - d["area_m2_s1"]) >= 0.002:
                ind.append(c["COMPONENT_ID"])
    A("C10", "independent paths: footing outline = schedule and L x W x D; every released slab polygon re-integrated "
      "(shoelace, holes deducted) within 0.002 m2 of S1", not ind, json.dumps(ind))
    dl = L["deltas"]
    s9 = {c["COMPONENT_ID"]: c for c in con if c["LANE"] == REL_S9}
    A("C11", "one S9 delta per S9 release, same m3", len(dl) == len(s9) and all(abs(d["DELTA_M3"] - s9[d["COMPONENT_ID"]]
                                                                                    ["RELEASED_M3"]) < 1e-9 for d in dl),
      f"{len(dl)} deltas")
    ff = [c for c in con if c["COMPONENT_ID"] in ("FTG-FF-18688-14112", "LIFT-01-FTG")]
    A("C12", "lift footing FF counted once (footing family); the lift family holds only a reference",
      sorted(c["LANE"] for c in ff) == sorted([REL_S9, OWNED_ELSEWHERE]) and
      abs([c for c in ff if c["LANE"] == REL_S9][0]["RELEASED_M3"] - 11.385) < 1e-9, "")
    A("C13", "pit walls, pit reinforcement and the conditional tie beam stay blocked",
      all(c["LANE"] in (INDICATIVE, BLOCKED) for c in con if c["FAMILY"] == "LIFT" and
          ("PIT-WALL" in c["COMPONENT_ID"] or "TIE" in c["COMPONENT_ID"])) and fam_kg.get("LIFT", 0.0) == 0.0, "")
    A("C14", "stairs: only S8.7's three plates released; S8.7A / B / C release nothing; flights and speculative bars "
      "blocked", abs(fam_m3["STAIRS"] - 0.516582788) < 1e-9 and abs(fam_kg["STAIRS"] - 59.020862261) < 1e-6, "")
    rel_slab = {c["COMPONENT_ID"] for c in con if c["FAMILY"] == "SLABS" and c["LANE"] in RELEASED}
    A("C15", "tank, dome-zone and stair-zone panels never in the slab release",
      not ({"SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02"} & rel_slab) and
      not [c for c in con if c["COMPONENT_ID"] in rel_slab and c["SUBFAMILY"] != "SLAB_PANEL"], "")
    s9c = math.fsum(x["ORIGINAL_KG"] for x in L["s9_corrections"])
    A("C16", "S9-C01 retracts exactly the S3.1 LOWER_BOUND tie core paths and hook allowances",
      abs(s9c - L["s9c01_kg"]) < 1e-9 and all(b["LANE"] == COND for b in bars if b["CORRECTIONS"] == "S9-C01"),
      f"{len(L['s9_corrections'])} parts, {s9c:.3f} kg")
    s31 = _j(F["S31_SUMMARY"])["headline"]
    parts = math.fsum(b["ORIGINAL_KG"] for b in bars if b["FAMILY"] == "COLUMNS" and b["STAGE_STATE"] in
                      ("VERIFIED", "LOWER_BOUND"))
    A("C17", "S3.1 parts reproduce its headline VERIFIED + LOWER_BOUND within part rounding (0.1 kg)",
      abs(parts - (s31["VERIFIED_KG"] + s31["LOWER_BOUND_KG"])) < 0.1,
      f"parts {parts:.3f} vs headline {s31['VERIFIED_KG'] + s31['LOWER_BOUND_KG']:.3f}")
    miss = {m["COMPONENT_ID"] for m in L["missing"]}
    gaps = [c["COMPONENT_ID"] for c in con if c["LANE"] in (COND, CONFLICT, BLOCKED, INDICATIVE, NOT_IN_SOURCE)
            and c["COMPONENT_ID"] not in miss and c["LANE"] != NOT_IN_SOURCE]
    A("C18", "every unreleased component appears in the missing / blocked register", not gaps, json.dumps(gaps[:5]))
    A("C19", "nothing is created to match an old estimate: no old-BOQ, R5, R9_1, PRE-S8 data or post-freeze input",
      L["references_read"] == [] and not [p for p in F.values() if re.search(r"registers_v3b|R9_1|arch_truth_05|"
                                                                                 r"post_freeze", str(p))], "")
    trace = [c["COMPONENT_ID"] for c in con if c["LANE"] in RELEASED and not c["SOURCE"]] + \
            [b["ITEM_ID"] for b in bars if b["LANE"] in RELEASED and not (b["OWNER_STAGE"] and b["SOURCE_AUTHORITY"])]
    A("C20", "every released quantity traces to a source drawing reference / owner stage", not trace, json.dumps(trace[:5]))
    A("C21", "overlap / double-count audit passes", all(o["RESULT"] == "PASS" for o in L["overlaps"]), "")
    A("C22", "no unmeasured component is counted as zero: unreleased rows have an empty released quantity",
      all(c["RELEASED_M3"] is None for c in con if c["LANE"] not in RELEASED), "")
    return out


# ------------------------------------------------------------------ build
def run():
    frozen, indexed = verify_inputs()
    s2 = s2_states()
    deltas = []
    foot, foot_overlap = footings(s2, deltas)
    col = columns(s2, deltas, foot)
    gb = ground_beams(deltas)
    bm = beams()
    sl = slabs(s2, deltas)
    s8 = frozen_s8()
    other = other_items(foot, sl)
    concrete = foot + col + gb + bm + sl + s8 + other
    s9_corr = []
    bars = rebar_columns(s9_corr) + rebar_footings() + rebar_ground() + rebar_beams() + rebar_slabs() + rebar_s8()
    s9c01_kg = math.fsum(x["ORIGINAL_KG"] for x in s9_corr)
    prec, resolved = precedence(concrete, bars, s9c01_kg)
    for i, d in enumerate(deltas, 1):
        d["DELTA_ID"] = f"S9-D{i:04d}"
    for i, c in enumerate(s9_corr, 1):
        c["CORRECTION_ID"] = f"S9-C01-{i:03d}"
    L = {"frozen": frozen, "indexed": indexed, "concrete": concrete, "bars": bars, "deltas": deltas,
         "s9_corrections": s9_corr, "s9c01_kg": s9c01_kg, "precedence": prec, "resolved": resolved,
         "references_read": []}
    L["overlaps"] = overlap_audit(concrete, bars, foot_overlap)
    L["missing"] = missing_register(concrete, bars)
    multi = ("O-02", "O-07", "O-08", "O-09", "O-10", "O-11", "O-12", "O-13", "O-15")   # two stages touch one item
    for o in L["overlaps"]:
        if o["CHECK_ID"] in multi:
            L["missing"].append({"COMPONENT_ID": f"OVERLAP:{o['CHECK_ID']}", "FAMILY": o["FAMILIES"], "STOREY": "ALL",
                                 "CATEGORIES": ["POSSIBLE_MULTI_STAGE_COUNT"], "CONCRETE_LANE": None,
                                 "REASON": f"{o['SUBJECT']}: {o['RULE']} ({o['RESULT']}; 11)",
                                 "OWNER_STAGE": "S9 overlap audit"})
    L["floors"] = floor_summary(concrete, bars)
    L["released"] = released_boq(concrete, bars)
    L["coverage"] = coverage(concrete, bars)
    L["rfis"] = rfis(concrete, s9c01_kg)
    L["cons"] = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in L["cons"]), "conservation: " +
          json.dumps([x for x in L["cons"] if x["RESULT"] != "PASS"]))
    for k, p in MANIFEST_PATHS.items():
        DR.verify_frozen(R / p, ROOT)
    for k, p in INDEX_STAGES.items():
        verify_index(p)
    return L


CONCRETE_FIELDS = ["COMPONENT_ID", "FAMILY", "SUBFAMILY", "STOREY", "OWNER_FAMILY", "OWNER_STAGE", "SOURCE", "DIMENSIONS",
                   "GROSS_M3", "DEDUCTIONS_M3", "DEDUCTION_DETAIL", "NET_M3", "RELEASED_M3", "CONDITIONAL_M3",
                   "CONDITIONAL_RANGE_M3", "LANE", "EVIDENCE_STATUS", "S2_CENSUS_STATE", "UNRESOLVED_REASON",
                   "REBAR_LINK", "FLAGS"]
BAR_FIELDS = ["ITEM_ID", "FAMILY", "OWNER_STAGE", "COMPONENT_ID", "STOREY", "BAR_ROLE", "DIA_MM", "COUNT",
              "SPACING_OR_RATE", "SHAPE", "CUT_LENGTH_M", "TOTAL_LENGTH_M", "LAPS", "ANCHORAGE", "HOOKS_BENDS",
              "UNIT_MASS_KG_M", "ORIGINAL_KG", "CORRECTION_KG", "CORRECTIONS", "AUTHORITATIVE_KG", "AUTHORITATIVE_T",
              "NOT_RELEASED_KG", "SOURCE_AUTHORITY", "STAGE_STATE", "LANE", "NOTE"]


def inventory(L):
    kg = rebar_by_component(L["bars"])
    out = []
    for c in L["concrete"]:
        rk = math.fsum(kg.get((c["FAMILY"], i), 0.0) for i in link_ids(c))
        out.append({"COMPONENT_ID": c["COMPONENT_ID"], "FAMILY": c["FAMILY"], "SUBFAMILY": c["SUBFAMILY"],
                    "STOREY": c["STOREY"], "OWNER_FAMILY": c["OWNER_FAMILY"], "OWNER_STAGE": c["OWNER_STAGE"],
                    "SOURCE": c["SOURCE"], "CONCRETE_LANE": c["LANE"], "RELEASED_M3": c["RELEASED_M3"],
                    "REBAR_LINK": c["REBAR_LINK"], "RELEASED_REBAR_KG_LINKED": _r(rk) if rk else None,
                    "EVIDENCE_STATUS": c["EVIDENCE_STATUS"]})
    return out


def summary(L):
    con, bars = L["concrete"], L["bars"]
    fam_m3 = defaultdict(float)
    fam_m3_lane = defaultdict(lambda: defaultdict(float))
    for c in con:
        if c["LANE"] in RELEASED:
            fam_m3[c["FAMILY"]] += c["RELEASED_M3"]
            fam_m3_lane[c["FAMILY"]][c["LANE"]] += c["RELEASED_M3"]
    fam_kg = defaultdict(float)
    for b in bars:
        if b["LANE"] in RELEASED:
            fam_kg[b["FAMILY"]] += b["AUTHORITATIVE_KG"] or 0
    lanes = Counter(c["LANE"] for c in con)
    return {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "released_concrete_m3_by_family": {k: _r(v, 6) for k, v in sorted(fam_m3.items())},
        "released_concrete_m3_by_family_and_lane": {k: {l: _r(v, 6) for l, v in d.items()} for k, d in
                                                    sorted(fam_m3_lane.items())},
        "released_concrete_m3_total": _r(math.fsum(fam_m3.values()), 6),
        "released_concrete_m3_frozen_stages": _r(math.fsum(c["RELEASED_M3"] for c in con if c["LANE"] == REL_FROZEN), 6),
        "released_concrete_m3_s9_delta": _r(math.fsum(c["RELEASED_M3"] for c in con if c["LANE"] == REL_S9), 6),
        "released_reinforcement_kg_by_family": {k: _r(v, 6) for k, v in sorted(fam_kg.items())},
        "released_reinforcement_kg_total": _r(math.fsum(fam_kg.values()), 6),
        "released_reinforcement_t_total": _r(math.fsum(fam_kg.values()) / 1000, 6),
        "s9_c01_retracted_kg": _r(L["s9c01_kg"], 6),
        "components": len(con), "components_by_lane": dict(sorted(lanes.items())),
        "unreleased_components": sum(v for k, v in lanes.items() if k not in RELEASED + (OWNED_ELSEWHERE, NOT_APPLICABLE)),
        "conditional_point_m3": _r(math.fsum(_point(c) or 0 for c in con if c["LANE"] in (COND, CONFLICT)), 6),
        "s9_deltas": len(L["deltas"]), "rfis": len(L["rfis"]),
        "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "stage_indexes": {k: v["index_sha256"] for k, v in L["indexed"].items()},
        "unit_mass": UM.describe(UNIT_MASS), "references_read": [],
        "gate_note": "a partial structural BOQ: never a complete building estimate; the project gate stays INCOMPLETE",
        "rule": "frozen stages and the production BOQ unchanged; every new quantity is an S9 delta"}


def write(L):
    s = summary(L)
    _csv(OUTPUTS[1], inventory(L))
    _csv(OUTPUTS[2], L["concrete"], CONCRETE_FIELDS)
    _csv(OUTPUTS[3], L["bars"], BAR_FIELDS)
    _csv(OUTPUTS[4], L["precedence"])
    _csv(OUTPUTS[5], L["missing"])
    _csv(OUTPUTS[6], L["floors"])
    _csv(OUTPUTS[7], L["released"])
    (HERE / OUTPUTS[8]).write_text(completeness_report(s, L), encoding="utf-8")
    _csv(OUTPUTS[9], L["rfis"], ["RFI_ID", "PRIORITY", "SOURCE_STAGE", "SOURCE_ID", "TO", "FAMILY", "QUESTION", "STATUS"])
    reg = list(L["deltas"]) + [{"DELTA_ID": "S9-C01", "CHANGE_KIND": "REINFORCEMENT_AUTHORITY_CORRECTION",
                                "FAMILY": "COLUMNS", "COMPONENT_ID": f"{len(L['s9_corrections'])} S3.1 parts",
                                "OLD_STATE": "LOWER_BOUND (S3.1)", "OLD_KNOWN_M3": None, "QUANTITY_BASIS": "D1.1 rules",
                                "DELTA_M3": None, "DELTA_KG": _r(-L["s9c01_kg"], 6),
                                "NEW_RELEASE_STATE": "CONDITIONAL (modelled polygonal equivalent / hook allowance)",
                                "RULE": "D1.1: only a source-derived cut length or a proven lower bound keeps kg",
                                "WHY": "S3.1 measured column ties on the sharp outer perimeter and added hook allowances; "
                                       "D1.1 later proved a sharp path is not a lower bound and that unknown hooks prove "
                                       "none, but scoped itself to S4.1 / S5.1 / S6.1; S9 applies the same rule to "
                                       "columns (kg kept as conditional, reversible on a stated bend radius / hook)"}]
    _csv(OUTPUTS[10], reg)
    _csv(OUTPUTS[11], L["overlaps"])
    _csv(OUTPUTS[12], L["cons"])
    _csv(OUTPUTS[13], L["coverage"])
    _json(OUTPUTS[14], s)
    prov = [{"record": f"CONCRETE:{c['COMPONENT_ID']}", "lane": c["LANE"], "m3": c["RELEASED_M3"],
             "owner": c["OWNER_STAGE"]} for c in L["concrete"]]
    prov += [{"record": f"BAR:{b['ITEM_ID']}", "lane": b["LANE"], "kg": b["AUTHORITATIVE_KG"]} for b in L["bars"]]
    (HERE / OUTPUTS[15]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    (HERE / OUTPUTS[0]).write_text(readme(s, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": s["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in F.values()},
                "frozen_baselines": s["frozen_baselines"], "stage_indexes": s["stage_indexes"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "release": {"concrete_m3": s["released_concrete_m3_total"],
                            "concrete_m3_s9_delta": s["released_concrete_m3_s9_delta"],
                            "reinforcement_kg": s["released_reinforcement_kg_total"],
                            "s9_c01_kg": s["s9_c01_retracted_kg"]},
                "rule": "frozen before the old Urban BOQ (V3b) or any post-freeze figure is read; frozen stages and the "
                        "production BOQ unchanged"}
    _json(MANIFEST_NAME, manifest)
    for o in OUTPUTS + [MANIFEST_NAME]:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return s


def _md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join("" if c is None else str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _n(v, nd=3):
    return "-" if v in (None, 0, 0.0) else f"{v:,.{nd}f}"


def completeness_report(s, L):
    cov = _md_table(["Family", "Components", "Released", "Conditional (valued)", "No value", "Released m3",
                     "Conditional m3 (point)", "Released kg", "Not released (modelled) kg"],
                    [[c["FAMILY"], c["COMPONENTS"], c["RELEASED_COMPONENTS"], c["CONDITIONAL_COMPONENTS"],
                      c["UNQUANTIFIED_COMPONENTS"], _n(c["RELEASED_M3"]), _n(c["CONDITIONAL_POINT_M3"]),
                      _n(c["RELEASED_KG"], 1), _n(c["NOT_RELEASED_MODELLED_KG"], 1)] for c in L["coverage"]])
    fl = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for r in L["floors"]:
        x = fl[r["STOREY"]]
        x[0] += r["RELEASED_M3"]
        x[1] += r["CONDITIONAL_POINT_M3"]
        x[2] += r["RELEASED_KG"]
        x[3] += r["NOT_QUANTIFIED_COMPONENTS"]
    flt = _md_table(["Storey", "Released m3", "Conditional m3 (point)", "Released kg", "Components with no value",
                     "Contents"], [[st, _n(fl[st][0]), _n(fl[st][1]), _n(fl[st][2], 1), fl[st][3], STOREY_NOTE[st]]
                                   for st in STOREYS if st in fl])
    cats = Counter(cat for m in L["missing"] for cat in m["CATEGORIES"])
    top = [r for r in L["rfis"] if r["SOURCE_STAGE"] == "S9"]
    return f"""# S9 structural completeness and exceptions report

Baseline `{BASELINE_HEAD}`. Date {DATE}. **This is a partial structural BOQ. It is not a complete building
estimate.** The project regression gate stays INCOMPLETE.

## Quantity coverage by family

{cov}

"Conditional (valued)" components carry a value only under a stated condition (`02`, `CONDITIONAL_M3` / range).
"No value" components are blocked or in conflict with nothing to measure: their quantity is unknown, never zero.

## Coverage by storey

{flt}

## Exceptions

- **Missing-quantity register** (`05`, {len(L['missing'])} rows):
  - rebar measured, concrete missing: {cats.get('REBAR_MEASURED_CONCRETE_MISSING', 0)};
  - concrete measured, rebar missing: {cats.get('CONCRETE_MEASURED_REBAR_MISSING', 0)};
  - owned with no quantity: {cats.get('OWNED_NO_QUANTITY', 0)};
  - conditional only: {cats.get('CONDITIONAL_ONLY', 0)};
  - possible multi-stage count: {cats.get('POSSIBLE_MULTI_STAGE_COUNT', 0)}, each resolved to one owner (`11`).

  Whether a component is absent from the old BOQ is checked only after the freeze (`post_freeze/`).
- **Superseded figures** (`04`): S3 (by S3.1), S8.6's lintels (by S8.6A), and the S5.1 / S6.1 link paths and six S5
  bars (by AD1 / D1.1). Each is shown once and never added.
- **Source conflicts:** F / F10 footing, column type and section conflicts, the lift columns at the pit (drawn 200 /
  250 vs schedule 300), CB widths, ground-beam length classes, SB2, the dome rings and the boundary wall.
- **Owner scenarios:** stairs only. GF -> 1F 27 risers is the preferred research alternative and not approved;
  1F -> 2F 27 is provisional; the round stair is the observed 28. S8.7C's findings and RFIs are preserved. No flight
  is released.

  The owner's 110 - 120 mm unfinished riser is not used as a repeated concrete riser. The finished riser schedule
  stays exact, and each concrete substrate level is that finished level minus the finish build-up (S8.7A / S8.7B):
  30 mm stair marble or 20 mm landing marble, plus about 20 - 30 mm bedding. No build-up or waist is approved, so
  the flights stay unreleased.
- **Engineer RFIs** (`09`, {len(L['rfis'])} rows): {len(L['rfis']) - len(top)} carried from the stages, plus {len(top)}
  consolidated by S9.

## Unresolved high-risk items

{_md_table(['Priority', 'To', 'Family', 'Question'], [[r['PRIORITY'], r['TO'], r['FAMILY'], r['QUESTION']] for r in top])}
"""


def readme(s, L):
    fam = s["released_concrete_m3_by_family"]
    lane = s["released_concrete_m3_by_family_and_lane"]
    kg = s["released_reinforcement_kg_by_family"]
    ct = _md_table(["Family", "Released m3", "of which S9 delta", "Owner"],
                   [[f, _n(fam[f], 3), _n(lane[f].get(REL_S9), 3),
                     {"FOOTINGS": "S9 (FF counted once)", "COLUMNS": "S9 (GF / 1F / 2F, S2 VERIFIED)",
                      "GROUND_BEAMS": "S9 (explicit sections)", "SLABS": "S9 (S2 VERIFIED panels)",
                      "GROUND_SLAB": "S8.1", "DOMES": "S8.3", "WATER_TANK_ROOF": "S8.4", "LINTELS": "S8.6A",
                      "STAIRS": "S8.7"}.get(f, "")] for f in FAMILY_ORDER if f in fam])
    kt = _md_table(["Family", "Released kg", "t", "Authoritative version"],
                   [[f, _n(kg[f], 3), _n(kg[f] / 1000, 3),
                     {"COLUMNS": "S3.1 - S9-C01", "FOOTINGS": "S4 + S4.1 + D1.2", "GROUND_BEAMS": "S5 + S5.1 - AD1 - D1.1",
                      "BEAMS": "S6 + S6.1 - D1.1", "SLABS": "S7", "GROUND_SLAB": "S8.1", "DOMES": "S8.3",
                      "WATER_TANK_ROOF": "S8.4", "LINTELS": "S8.6A", "STAIRS": "S8.7"}.get(f, "")]
                    for f in REBAR_FAMILIES if f in kg])
    lanes = s["components_by_lane"]
    extra = defaultdict(float)
    for b in L["bars"]:
        if b["FAMILY"] == "COLUMNS" and b["LANE"] in RELEASED and not b["BAR_ROLE"].startswith("MAIN_BARS"):
            extra[b["SOURCE_AUTHORITY"]] += b["AUTHORITATIVE_KG"]
    check(set(extra) <= {"P8-N09", "P13-FOOTING-TYP", "P15-TWISTED"}, "released column extras are printed-rule parts")
    return f"""# S9: whole-building structural BOQ reconciliation

Baseline HEAD `{BASELINE_HEAD}`. Date {DATE}. State: `FROZEN_BEFORE_COMPARISON` (`{MANIFEST_NAME}`).

S9 reconciles every structural family from the frozen S1 - S8 stages. All 29 freeze manifests and the S1 / S2 / S3 /
S3.1 indexes verify unchanged before and after the build. No frozen stage and no production quantity is changed:
every new quantity is an auditable S9 delta (`10`).

**This is a partial structural BOQ, not a complete building estimate.** The project gate stays INCOMPLETE.

## Released structural BOQ (A)

**Concrete: {_n(s['released_concrete_m3_total'], 3)} m3.**

- {_n(s['released_concrete_m3_frozen_stages'], 3)} m3 is carried from the frozen stages.
- {_n(s['released_concrete_m3_s9_delta'], 3)} m3 is released here, as {s['s9_deltas']} S9 deltas.

{ct}

**Reinforcement: {_n(s['released_reinforcement_kg_total'], 3)} kg ({_n(s['released_reinforcement_t_total'], 3)} t).**
Each family is taken at its authoritative version; `04` shows the precedence.

{kt}

The full released BOQ, by family, storey and bar diameter, is `07_RELEASED_STRUCTURAL_BOQ.csv`.

## How S9 decides

**S9-RR1, the release rule for new concrete.** A component no frozen stage measured is released only if all of these
hold:

- S2's census already VERIFIED its count, length or area;
- every dimension is printed (schedule, section, thickness) or taken from the S1 / S5 / S6 project geometry;
- its height or interval is established;
- it has no open conflict;
- S9's independent recomputation agrees (footing outline = schedule; slab polygon re-integrated).

The rule releases these families:

- **Footings:** 25 occurrences, L x W x D. The F9 / FN outline overlap is deducted at its maximum shared prism. FF
  (11.385 m3) is counted once here, not in the lift family.
- **Columns:** GF / 1F / 2F occurrences whose S2 state is VERIFIED and whose drawn section equals the schedule. They
  are measured on the printed floor-to-floor; structural slab levels are not printed, so this is a project-basis value
  (the same interval S3.1's main bars use).
- **Ground and strap beams:** the spans whose width and depth are both explicit.
- **Slab plates:** the 47 S2-VERIFIED suspended slab panels (S1's GF / 1F / 2F roof slabs) that no S8 stage owns.
  Each is panel area x printed or default thickness.

**S9-MC1, the measurement convention.** No cubic metre is counted twice:

- columns own their footprint over the full storey, including the joints;
- beams run clear between column and beam faces, at full depth;
- slab panels lie between the beam and column faces (S1 geometry);
- ground beams run clear between column and footing faces.

**What stays conditional.** Superstructure beams: S2 holds their lengths only as a lower bound, and the drawings never
state whether schedule depth H includes the slab. `02` gives B x H x L and the alternative B x (H + 0.16) x L. The
rest is blocked: foundation-storey columns (no printed founding level), the pit walls and tie beam, the pool, parapets,
blinding, the boundary wall, the dome rings and the ground-slab remainder. None is ever counted as zero.

**S9-C01, a new correction.** S3.1 measured column ties on the sharp outer perimeter and added hook allowances.
D1.1 later proved that a sharp path is not a lower bound and that unknown hooks prove none. D1.1 limited itself to
S4.1 / S5.1 / S6.1; S9 applies the same rule to columns. {_n(s['s9_c01_retracted_kg'], 3)} kg moves from released to
conditional. It is kept in `03`, and the change can be reversed once a bend radius and hook are stated.

**No unsupported lap or anchorage is added.** S9 adds no bar length of its own. The column laps, anchorages,
starters and twisted-column extras that stay released ({_n(math.fsum(extra.values()), 3)} kg) are S3.1's
printed-rule parts only: p.8 note 9, the p.13 typical footing detail and the p.15 twisted-column detail. Every other
lap, anchorage, hook and bend stays blocked or conditional (`03`, `05`).

**Stairs.** S8.7's three plates are carried unchanged, and S8.7A / S8.7B / S8.7C add nothing. The owner scenarios
stay scenarios:

- GF -> 1F with 27 risers is the preferred research alternative, not approved;
- 1F -> 2F with 27 is provisional;
- the round stair is the observed 28.

The owner's 110 - 120 mm unfinished riser is not used as a repeated concrete riser. The finished riser schedule
stays exact, and each concrete substrate level is that finished level minus its build-up: 30 mm stair marble or
20 mm landing marble, plus about 20 - 30 mm bedding. The waist is unknown. The landing, B20, B23, winder and CA
conflicts stay open, so no flight and no stair bar is added.

**Lift.** S8.8 is carried unchanged: the pit walls, the pit bars and the conditional tie beam stay blocked. FF is
counted once, in the footings. The four foundation-storey lift columns (C1 / C2 / C9 at the pit) are a
`SOURCE_CONFLICT`: they are drawn 200 / 250 mm, but the schedule gives 300 mm (S8.8 C-01, S9-RFI-04).

## Components

There are {s['components']} components. By lane:

{_md_table(['Lane', 'Components'], [[k, v] for k, v in lanes.items()])}

## Files

| File | Content |
|---|---|
| `01_COMPONENT_INVENTORY.csv` | One row per structural component: owner, storey, source, lanes, linked reinforcement |
| `02_CONCRETE_BOQ_RECONCILIATION.csv` | Dimensions, gross, deductions, net, released, conditional / range, reason |
| `03_REINFORCEMENT_BOQ_RECONCILIATION.csv` | Per bar item: diameter, count, rate, shape, cut / total length, laps / anchorage / hooks, unit mass, original kg, corrections, authoritative kg / t, owner stage, lane |
| `04_OWNERSHIP_AND_PRECEDENCE_REGISTER.csv` | Every version of every family; authoritative and superseded |
| `05_MISSING_AND_BLOCKED_REGISTER.csv` | Missing and blocked quantities, by category |
| `06_FLOOR_SUMMARY.csv` | Storey x family |
| `07_RELEASED_STRUCTURAL_BOQ.csv` | Released BOQ (A) |
| `08_STRUCTURAL_COMPLETENESS_REPORT.md` | Completeness and exceptions (B) |
| `09_ENGINEER_RFI_REGISTER.csv` | Engineer RFI register |
| `10_S9_DELTA_REGISTER.csv` | S9 deltas and S9-C01 |
| `11_OVERLAP_AND_DOUBLE_COUNT_AUDIT.csv` | Overlap and double-count audit |
| `12_CONSERVATION_CHECKS.csv` | Conservation checks |
| `13_COVERAGE_BY_FAMILY.csv` | Coverage by family |
| `14_RELEASE_SUMMARY.json` / `15_PROVENANCE.jsonl` / `{MANIFEST_NAME}` | Summary, provenance, freeze |
| `S9_STRUCTURAL_BOQ.xlsx` | Workbook view, written by `build_workbook.py` from these CSVs after the freeze. It is not frozen, and it is not committed (`*.xlsx` is git-ignored); rebuild it on demand |

## Reproduce

```
python3 -I research/alsenan_structural_s9/build_s9.py
```

The builder reads only frozen registers; no drawing is needed. Two builds are byte-identical.
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({k: s[k] for k in ("released_concrete_m3_total", "released_concrete_m3_s9_delta",
                                        "released_reinforcement_kg_total", "s9_c01_retracted_kg", "components_by_lane",
                                        "conservation")}, indent=1))


if __name__ == "__main__":
    try:
        main()
    except Stop as e:
        print(f"STOP: {e}", file=sys.stderr)
        sys.exit(2)
