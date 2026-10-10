"""Owner decisions 1-4, recorded WITHOUT touching the approved protocol.

The approved hashes must survive exactly:

    PROTOCOL_HASH        d6de5dc1a99f315a8a1bf409acce71f59ab3f75295baab660c655682029e7201
    SELECTION_RULE_HASH  75f2d71a12397dd8a52fa1457fdc0665d98c9dda6b8afbee9228791c2815cfc6

so the decisions live here, in their own module, with their own hash. The
protocol file is not edited and the selection is not re-run.
"""

from __future__ import annotations

import hashlib

APPROVED_PROTOCOL_HASH = (
    "d6de5dc1a99f315a8a1bf409acce71f59ab3f75295baab660c655682029e7201")
APPROVED_SELECTION_RULE_HASH = (
    "75f2d71a12397dd8a52fa1457fdc0665d98c9dda6b8afbee9228791c2815cfc6")

# ==================================================================
# DECISION 1 - height independence
# ==================================================================

HEIGHT_KINDS = ("STOREY_HEIGHT", "STRUCTURAL_HEIGHT", "CLEAR_HEIGHT",
                "APPLICABLE_PLASTER_HEIGHT")

THEY_ARE_NOT_SYNONYMS = (
    "A21 reports these as four separate fields. Reading a storey height is "
    "not establishing a plaster height, and the reduction between them is "
    "evidence, not arithmetic anyone may supply")

PLASTER_HEIGHT_NOT_ESTABLISHED = "PLASTER_HEIGHT_NOT_ESTABLISHED"

THE_REDUCTION_MAY_NOT_BE_INVENTED = (
    "if A21 can read a storey height but cannot establish how that becomes "
    "the applicable plaster height, it returns "
    "PLASTER_HEIGHT_NOT_ESTABLISHED and says exactly what is missing. It "
    "may NOT reason '4.00 minus an assumed slab minus an assumed beam "
    "equals 3.20' because 3.20 is historically plausible. That is the "
    "answer arriving by the back door")

WITHHELD_FROM_A21 = (
    "the owner's historical working plaster height of approximately 3.20 m",
    "the owner-stated storey heights: ground ~4.00 m, first ~4.50 m, "
    "roof ~4.00 m",
    "the worked parapet total of approximately 0.90 m",
)

WHY_THEY_ARE_WITHHELD = (
    "each is a number the deterministic path would also use. Handing the "
    "same figure to both paths turns a later A22 agreement into an echo "
    "rather than a confirmation. They stay sealed in experiment metadata "
    "and may be introduced AFTER A21 freezes, as a separate evidence "
    "source, with the effect recalculated deterministically")

# ==================================================================
# DECISION 2 - parapet
# ==================================================================

PARAPET_COMPONENTS_IF_THE_DRAWING_FAILS = {
    "BLOCK_COURSES": 4,
    "NOMINAL_BLOCK_COURSE_HEIGHT_M": 0.20,
    "CAPPING_HEIGHT_M": 0.10,
}

PARAPET_RULE = (
    "A21 inspects the drawing FIRST. Where the drawing establishes the "
    "parapet geometry, the drawing wins. Only where it does not may the "
    "owner components above be introduced, each carrying SOURCE_TYPE = "
    "OWNER_PROJECT_INPUT, and the arithmetic 4 x 0.20 + 0.10 is performed "
    "by deterministic CODE. The resulting total is never shown to A21 as "
    "an expected answer. Drawing or specification overrides the owner "
    "default where they conflict")

# ==================================================================
# DECISION 3 - defaults may never masquerade as measurements
# ==================================================================

RESULT_LEVELS = ("SOURCE_ESTABLISHED_RESULT", "PROVISIONAL_QS_ESTIMATE")

TWO_RESULTS_NEVER_MERGED = (
    "every case produces BOTH. The SOURCE-ESTABLISHED result contains only "
    "values established independently from permitted source evidence; a "
    "missing dimension leaves QUANTITY_STATUS = NOT_ESTABLISHED and no "
    "default may convert it to ESTABLISHED. The PROVISIONAL estimate may "
    "use authorised owner defaults, and is labelled as such on every line "
    "it touches")

TEMPORARY_OWNER_DEFAULTS = {
    "DOOR_WIDTH_M": 1.00, "DOOR_HEIGHT_M": 2.20,
    "WINDOW_WIDTH_M": 1.50, "WINDOW_HEIGHT_M": 1.50,
}

MEASURED_AND_PROVISIONAL_ARE_SEPARATE_REGISTERS = (
    "MEASURED_QUANTITY and PROVISIONAL_DEFAULT_BASED_QUANTITY are never "
    "summed into one figure and never appear on the same line")

SHARED_ASSUMPTION_AGREEMENT = "SHARED_ASSUMPTION_AGREEMENT"

AGREEMENT_ON_A_SHARED_DEFAULT_IS_NOT_CONFIRMATION = (
    "if the deterministic path uses 1.50 x 1.50 and A21 uses 1.50 x 1.50, "
    "that is SHARED_ASSUMPTION_AGREEMENT. It is NOT "
    "INDEPENDENT_STRUCTURAL_AGREEMENT, and A22 may never record it as "
    "independent dimensional confirmation")

# ==================================================================
# DECISION 4 - the six cases stand, including the hard one
# ==================================================================

CASES_CONFIRMED_UNCHANGED = True

SALOON_POOL_SAFETY_RULE = (
    "E1.4 places SALOON and SWIMMING POOL under one PHYSICAL_REGION_KEY. "
    "That fact is NOT shown to A21 before its visual interpretation. After "
    "A21 freezes, compare whether it independently identifies SALOON, "
    "SWIMMING POOL, their relationship and any boundary between them. If "
    "A21 separates what E1.4 merges, A22 classifies "
    "IDENTITY_MAPPING_DIFFERENCE and investigates. It may NOT jump to "
    "ENGINE_GEOMETRY_ERROR or A21_ERROR")

THE_PILOT_KEEPS_ITS_HARD_CASE = (
    "SALOON is not replaced because the deterministic engine finds it "
    "difficult. A pilot made only of cases the engine already understands "
    "measures the engine, not the drawing")

# ==================================================================
# source independence - the harness is not the input
# ==================================================================

THE_SELECTION_HARNESS_IS_NOT_THE_OBSERVATION_INPUT = (
    "the six cases were chosen using frozen deterministic metadata. That "
    "does not entitle A21 to see the deterministic interpretation. The "
    "harness decided WHICH; it tells A21 nothing about WHAT")

A21_MAY_RECEIVE = (
    "the original architectural drawing sheets",
    "a relevant plan crop",
    "the relevant section and elevation sheets",
    "printed dimensions visible in those sources",
    "approved Urban rules that are not benchmark answers",
)

A21_MAY_NOT_RECEIVE = (
    "E1.4 boundary chains",
    "E1.4 areas",
    "E1.4 physical-region assignments",
    "E1.4 opening counts",
    "E1.4 room polygons",
    "E1.4 quantity results",
    "the deterministic interpretation of SALOON or SWIMMING POOL",
    "the Excel benchmark",
    "human measured quantities",
    "any known target value",
    "the owner historical 3.20 m plaster height",
    "the owner storey heights",
    "the worked parapet total",
)

# ==================================================================
# A22 - the independence field, specified now, still not running
# ==================================================================

EVIDENCE_INDEPENDENCE_STATUS = (
    "INDEPENDENT", "PARTIALLY_SHARED", "SHARED_SOURCE", "SHARED_ASSUMPTION",
    "SHARED_RULE", "NOT_INDEPENDENT", "UNKNOWN",
)

HOW_A22_MUST_READ_AGREEMENT = (
    "two identical answers from the same default are not independent "
    "confirmation - SHARED_ASSUMPTION",
    "two identical answers from the same printed dimension are legitimate "
    "agreement on a common source, but are not independent evidence that "
    "the printed dimension is correct - SHARED_SOURCE",
    "two independently reconstructed geometries agreeing carry stronger "
    "reconciliation weight - INDEPENDENT",
)

DO_NOT_MAKE_THIS_A_CONFIDENCE_SCORE_YET = (
    "EVIDENCE_INDEPENDENCE_STATUS stays a category. Collapsing it into a "
    "number would hide exactly the distinction it exists to carry")


def decisions_hash() -> str:
    parts = [APPROVED_PROTOCOL_HASH, APPROVED_SELECTION_RULE_HASH,
             THEY_ARE_NOT_SYNONYMS, PLASTER_HEIGHT_NOT_ESTABLISHED,
             THE_REDUCTION_MAY_NOT_BE_INVENTED, WHY_THEY_ARE_WITHHELD,
             PARAPET_RULE, TWO_RESULTS_NEVER_MERGED,
             MEASURED_AND_PROVISIONAL_ARE_SEPARATE_REGISTERS,
             SHARED_ASSUMPTION_AGREEMENT,
             AGREEMENT_ON_A_SHARED_DEFAULT_IS_NOT_CONFIRMATION,
             SALOON_POOL_SAFETY_RULE, THE_PILOT_KEEPS_ITS_HARD_CASE,
             THE_SELECTION_HARNESS_IS_NOT_THE_OBSERVATION_INPUT,
             DO_NOT_MAKE_THIS_A_CONFIDENCE_SCORE_YET]
    for seq in (HEIGHT_KINDS, WITHHELD_FROM_A21, RESULT_LEVELS,
                A21_MAY_RECEIVE, A21_MAY_NOT_RECEIVE,
                EVIDENCE_INDEPENDENCE_STATUS, HOW_A22_MUST_READ_AGREEMENT):
        parts += list(seq)
    parts += [f"{k}={v}" for k, v in
              sorted(PARAPET_COMPONENTS_IF_THE_DRAWING_FAILS.items())]
    parts += [f"{k}={v}" for k, v in sorted(TEMPORARY_OWNER_DEFAULTS.items())]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    g = globals()
    out = {"DECISIONS_HASH": decisions_hash(),
           "APPROVED_PROTOCOL_HASH": APPROVED_PROTOCOL_HASH,
           "APPROVED_SELECTION_RULE_HASH": APPROVED_SELECTION_RULE_HASH,
           "THE_APPROVED_HASHES_ARE_UNCHANGED_BY_THESE_DECISIONS": True}
    for k in sorted(k for k in g if k.isupper() and not k.startswith("_")):
        v = g[k]
        out[k] = list(v) if isinstance(v, tuple) else v
    return out


if __name__ == "__main__":
    import json
    from research.a21_visual_qs_pilot_01 import protocol as P
    from research.a21_visual_qs_pilot_01 import selection as S
    assert P.protocol_hash() == APPROVED_PROTOCOL_HASH, "protocol drifted"
    assert S.rule_hash() == APPROVED_SELECTION_RULE_HASH, "selection drifted"
    print(json.dumps({"DECISIONS_HASH": decisions_hash(),
                      "PROTOCOL_HASH_PRESERVED": True,
                      "SELECTION_RULE_HASH_PRESERVED": True}, indent=2))
