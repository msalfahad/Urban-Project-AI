"""T-203: build rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json from 1.1.0 (never edited) + the candidate-level state of
every family, re-derived from the merged ARCH_TAKEOFF_V3.0.x candidate packages.

    python3 -I research/agents_t203/build_master_1_2_0.py [--check]

--check rebuilds in memory and exits 1 when the file on disk differs (or the candidate check finds a problem).

Sources (no run is repeated here; every figure below is the merged package's own run, reproduced by its Gate B verdict):
the package reports research/agents_t131/T-131_ARCH_V30.md, agents_t133/T-133_ARCH_V301.md, agents_t142/T-142_ARCH_V302.md,
agents_t151/T-151_ARCH_V303.md, agents_t167/T-167_ARCH_V304.md, agents_t179/T-179_ARCH_V305.md (r2 section),
agents_t187/T-187_ARCH_V306.md, agents_t193/T-193_ARCH_V307.md (r2 of T-203, after the Verifier 13:03 rejection), and the checker verdicts on the board (agents/control docs/agents/BOARD.md and
BOARD_ARCHIVE.md; quoted by verdict head only). Families are bound by the registry's own item-code ownership (1.1.0
'item_codes'); where a package's lines carry another family's item code (stair / pool / tank steel under STR.REBAR,
the dome ring under STR.CONC.BEAM) the physical family says so and the line is counted once.

What changes against 1.1.0: version / supersedes / source / loaded_by; v3_0_candidate (the candidate is now V3.0.7);
in_v3_0_candidate per family (re-derived; the 1.1.0 value kept as in_v3_0_candidate_1_1_0) and its counts;
v3_0_planned_tasks (packages since merged removed, queued lane I packages added); new: candidate_states,
candidate_state_definitions, candidate, candidate_packages, candidate_state_counts, each family's 'candidate' block.
Every released-configuration field (capability, capability_1_0_0, capability_change, evidence, implementation,
released_method_reads, opt_in_readers, missing, development_villa, item_codes, ...) is copied unchanged.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json"
OUT = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json"
CAND = "ARCH_TAKEOFF_V3.0.7"
AS_OF = "T-193"

PACKAGES = [
    {"task": "T-131", "method_version": "ARCH_TAKEOFF_V3.0", "module": "engine/source/arch_v30.py",
     "merge_commit": "b1a6d6dbeab00c79744fa28008b1d2042656ee93",
     "verdict": "MERGED (verifier 2026-10-21 02:30 UTC; r2 67f760a; integration check by the verifier's own script on a "
                "fresh run, every line that differs from V2.9 has a ledger row; before Gate B was defined)",
     "gate": "VERIFIER_MERGE_BEFORE_GATE_B",
     "integrates": ["T-073", "T-109", "T-123", "T-116"],
     "pieces": "STRAPS (PLOT_EDGE_MEMBERS_V1), FACADE_PASSAGE (FACADE_PASSAGE_WALLS_V1), STAIR_FLOOR_RESIDUE "
               "(STAIR_FLOOR_RESIDUE_V1), MEMBRANE_V2_13 (the V2.13 roll lines as they are) on ARCH_TAKEOFF_V2.13 + route G",
     "tests": ["tests/t131_arch_v30"]},
    {"task": "T-133", "method_version": "ARCH_TAKEOFF_V3.0.1", "module": "engine/source/arch_v301.py",
     "merge_commit": "967d6d5351f687edce2bd14572f744eb9bbdce61",
     "verdict": "MERGED, PARTIAL (verifier 2026-10-21 17:40 UTC; Gate A + Gate B; defects D1 runner without --profile, "
                "D3 held blinding lower bounds, both fixed in V3.0.2; pieces T-122 / T-135 / T-111 / T-105 / T-102 left WAITING)",
     "gate": "GATE_B",
     "integrates": ["T-126", "T-124"],
     "pieces": "ROUTE_G_SCOPE_V1 scope piece (columns not drawn above, blinding by member family), MEMBRANE_FOLD_V5 audit",
     "tests": ["tests/t133_arch_v301"]},
    {"task": "T-142", "method_version": "ARCH_TAKEOFF_V3.0.2", "module": "engine/source/arch_v302.py",
     "merge_commit": "5de8657e5202aa744fe76f89128f5475d551a531",
     "verdict": "MERGED, Gate B PASS with one evidence-text defect D4 (verifier 2026-10-22 00:30 UTC; D4 fixed in V3.0.3)",
     "gate": "GATE_B",
     "integrates": ["T-136", "T-137", "T-127"],
     "pieces": "FOOTING_REBAR_POPULATION_V1, MEMBRANE_COVERAGE_PROOF_V1, soffits over outside air, V3.0.1 fixes D1 / D2 / D3",
     "tests": ["tests/t142_arch_v302"]},
    {"task": "T-151", "method_version": "ARCH_TAKEOFF_V3.0.3", "module": "engine/source/arch_v303.py",
     "merge_commit": "47df193077b5f2450179359b11682c56dd50f6e8",
     "verdict": "MERGED (verifier 2026-10-22 08:12 UTC; Gate B slices (a) re-check, (b), (c) all PASS on r2 34765d8)",
     "gate": "GATE_B",
     "integrates": ["T-148", "T-138", "T-149", "T-141"],
     "pieces": "COLUMN_STEEL, GROUND_SYSTEM_STEEL, BEAM_STEEL hand ledgers; EVIDENCE_FIX (V3.0.2 defect D4)",
     "tests": ["tests/t151_arch_v303"]},
    {"task": "T-167", "method_version": "ARCH_TAKEOFF_V3.0.4", "module": "engine/source/arch_v304.py",
     "merge_commit": "cf5819c6fb0c529fe2e8c98abc4139908b97a086",
     "verdict": "MERGED, Gate B PASS (verifier 2026-10-22 15:00 UTC; merge of a2b8c0f)",
     "gate": "GATE_B",
     "integrates": ["T-064", "T-044"],
     "pieces": "PROFILE_AUDIT: every route G profile value checked against the owner Q-17 A project data file; lines "
               "resting on a non-usable value HELD",
     "tests": ["tests/t167_arch_v304"],
     "holds": ["B10-03"]},
    {"task": "T-179", "method_version": "ARCH_TAKEOFF_V3.0.5", "module": "engine/source/arch_v305.py",
     "merge_commit": "90d0b769ada207d70d68ba53eb12d660f9d997ac",
     "verdict": "MERGED r2 (verifier 2026-10-23 01:05 UTC; Gate B PASS on 85bba0ff; r1 rejected 2026-10-22 21:02 UTC "
                "on D-T179-1 / D-T179-2, both fixed)",
     "gate": "GATE_B",
     "integrates": ["T-152", "T-166", "T-160"],
     "pieces": "SLAB_STEEL, STAIR_POOL_TANK_STEEL, DOME_RING hand ledgers (route lines of each scope superseded)",
     "tests": ["tests/t179_arch_v305"]},
    {"task": "T-187", "method_version": "ARCH_TAKEOFF_V3.0.6", "module": "engine/source/arch_v306.py",
     "merge_commit": "8a6d604aae8ff6396662e5568b161f0d8ab746d0",
     "verdict": "MERGED (Verifier 2026-10-23 06:24 UTC; Gate B PASS, head 5922d4ea)",
     "gate": "GATE_B",
     "integrates": ["T-186", "T-190", "T-184", "T-189", "T-192"],
     "pieces": "STAIR_CONCRETE (ST-01 ledger rev3, 1F -> 2F), DEFAULT_GUARD over every candidate line",
     "tests": ["tests/t187_arch_v306"],
     "holds": ["B10-09", "B10-10"]},
    {"task": "T-193", "method_version": "ARCH_TAKEOFF_V3.0.7", "module": "engine/source/arch_v307.py",
     "merge_commit": "e866328a66149abe881c0d1329f904170b631402",
     "verdict": "MERGED (verifier 2026-10-23 11:52 UTC, e866328a, Gate B PASS)",
     "gate": "GATE_B",
     "integrates": ["T-183", "T-185"],
     "pieces": "POOL_CONCRETE (T-183 r2 base + walls), DOME_SHELL (T-185 S0 terrace shells), the 1F 'winder' misread "
               "retired as the east dome, DEFAULT_GUARD re-check on evidence version 2 (conventions V6 + the M4 profile)",
     "tests": ["tests/t193_arch_v307"],
     "releases": ["B10-09", "B10-10"]},
]

RUNS = {  # the packages' own development-villa runs (Gate B reproduced), line counts and BOQ_LINES.csv sha prefixes
    "ARCH_TAKEOFF_V3.0.1": "1,698 lines",
    "ARCH_TAKEOFF_V3.0.2": "1,757 lines (110 rows changed against V3.0.1)",
    "ARCH_TAKEOFF_V3.0.3": "3,132 lines, V3_0_3_BOQ_LINES.csv 5ba4ae93 (1,880 rows changed)",
    "ARCH_TAKEOFF_V3.0.4": "3,132 lines, V3_0_4_BOQ_LINES.csv d86de34a (84 rows changed)",
    "ARCH_TAKEOFF_V3.0.5": "3,534 lines, V3_0_5_BOQ_LINES.csv 76d75bde (r2; 478 rows changed against V3.0.4)",
    "ARCH_TAKEOFF_V3.0.6": "3,540 lines, V3_0_6_BOQ_LINES.csv 3e622799 (13 rows changed, 3,527 byte-identical to V3.0.5)",
    "ARCH_TAKEOFF_V3.0.7": "3,545 lines, V3_0_7_BOQ_LINES.csv 197c5599 (5 changed + 5 added, 3,535 byte-identical to "
                           "V3.0.6)",
}
for _p in PACKAGES:
    if _p["method_version"] in RUNS:
        _p["development_villa_run"] = RUNS[_p["method_version"]]

# Families a package changed. state, packages, changed, open, released_in_candidate, optional note.
I, H = "INTEGRATED_IN_CANDIDATE_AND_TESTED", "HELD_IN_CANDIDATE"
SPEC = {
    "B3-01": (I, ["T-131"],
              "STAIR_FLOOR_RESIDUE (T-116): the first-floor living porcelain line 44.869 m2 -> 38.459 .. 38.979 m2 "
              "BOUNDED_EXPOSURE (tread union, opening and well netted out; T-113 hand 38.588 .. 38.990 inside)",
              "that range stays held (owner Q-66 B piece T-122 never integrated); no printed tile size, so the tile count "
              "holds every room; every other dry-floor line is the V2.13 base line", "yes"),
    "B4-07": (I, ["T-131"],
              "FACADE_PASSAGE (T-109 / T-123): ground-floor facade run 98.887 -> 105.887 lm under owner Q-67 A "
              "(conditional; without the decision 98.887 .. 105.887 lm BOUNDED_EXPOSURE); T-123 hand 105.887",
              "facade area and external finish carry no quantity until a facade height is printed (Q-07); the external "
              "finish lines are base lines", "yes"),
    "B5-01": (I, ["T-142"],
              "soffits over outside air (T-127): 5 lines added, 44.446 m2 (0 in V2.9 / V3.0.1): PL-02 5.640 and PL-03 "
              "12.834 m2 VERIFIED, PL-01 19.181, PL-04 4.374, PL-05 2.417 m2 DRAWING-CONFIRMED (owner Q-67 A cond., Q-68 C)",
              "soffit finish HELD (Q-68 C: plaster / paint only in the provisional field); the five areas are typed "
              "records, no geometric reader of slabs over outside air yet; every room ceiling line is a base line and "
              "PROVISIONAL by design (O-P8-02, no ceiling type in a plan)", "yes"),
    "B6-01": (I, ["T-131"],
              "FACADE_PASSAGE (T-109): the two ground-floor open-air passage mouths OP-001 / OP-007 (2 pcs) "
              "NOT_APPLICABLE_WITH_EVIDENCE: not building openings",
              "doors and windows are base lines, counted by class under B6-02 .. B6-04", "yes"),
    "B7-12": (I, ["T-187", "T-193"],
              "STAIR_CONCRETE (T-184 / T-189 / T-192 rev3), ST-01 first to second floor: MS2-L 1.033445 m3 VERIFIED, "
              "MS2-U 1.001373 DRAWING-CONFIRMED, MS2-LD 0.4696 .. 0.4800 HELD, MS2-TR UNKNOWN; DEFAULT_GUARD (T-186) holds "
              "the route lines of ST-01 ground to first floor 2.785981 and ST-02 1.769462 m3 (waist convention 0.175 where "
              "'T 16' is printed) and the first-floor 'winder' line 4.450745 m3 as MISREAD (dome ribs); lobby flight "
              "placeholder UNKNOWN. STR.CONC.STAIR released 9.954455 -> 2.983085 m3, held 0.4696 .. 0.4800, 5 blocked. "
              "V3.0.7 (T-193): that 'winder' line RETIRED: it is the east terrace dome DOME-B drawn on its own slab "
              "sheet, now carried once by the verified DOME-B shell under B10-09; STR.CONC.STAIR released 2.983085 and "
              "held 0.4696 .. 0.4800 unchanged, blocked 5 -> 4",
              "the ST-01 ground-to-first pieces, ST-01b, ST-02 and ST-03 ledger lines are not integrated (later V3.0.x); "
              "ST-02 curved parts held (Q-50); MS2-TR landing levels scaled, not printed; the ST-01 shaft floor in no line",
              "yes"),
    "B7-14": (H, ["T-179"],
              "STAIR_POOL_TANK_STEEL (T-166), stair part: stair steel by flight, strip and component as held ranges "
              "(1,039.160 .. 1,443.671 kg, r2 high from count B) and UNKNOWN lines; none released. Carried under item "
              "code STR.REBAR (owned by B11-01) with physical element STAIRS; counted here, never under B11-03",
              "every stair bar count held (the '/m' notation is settled for footings only, T-171); typical-only stair "
              "families (T-184 p.16 reading not ruled); stair top-bar length, curved flight, winders, entrance / lobby "
              "flights", "none"),
    "B8-05": (I, ["T-131", "T-133", "T-142"],
              "22 roll lines (52 rolls on 21 lines + 1 held; owner Q-58 A cutting plans) carried from V2.13 by V3.0; "
              "MEMBRANE_FOLD_V5 audit attached as evidence by V3.0.1 (T-124: 21 AGREES, 1 NOT_COMPARABLE); coverage proof "
              "by V3.0.2 (T-137: 12 PROVEN, 9 PROVEN_EXCEPT_DETAIL, 1 NOT_PROVEN); roll counts unchanged",
              "the second-floor top roof roll line holds its area with no count (NOT_PROVEN); 9 lines proven except the "
              "internal-corner / thin-wall details they list", "yes"),
    "B10-01": (I, ["T-133", "T-142", "T-187", "T-193"],
               "ROUTE_G_SCOPE_V1 (T-126) by member family: footings 15.179 m3 released (verifier hand 15.213, -0.2 %), "
               "separate HELD lines F10 0.480 .. 0.590, under ground beams 4.949 .. 9.423 m3 and under straps 0.378 .. "
               "0.772 m3 after the V3.0.2 REACH fix of defect D3 (hand 5.189 .. 9.387 and 0.670 inside); V3.0.6 default "
               "guard: the released footing line REBASED_ON_PRINTED (convention 0.10 = printed projection 0.10), unchanged; "
               "V3.0.7 guard evidence version 2 (T-193): the 0.10 thickness now confirmed by the printed footing note "
               "(structural PDF p.13 '10cm Plain con.', EV-BLINDING-T), so the line is REBASED_ON_PRINTED on both "
               "conventions; 15.179437 m3 and the line itself byte-identical (evidence only, no quantity moved)",
               "the three held lines are never summed (F10 two labels Q-31 C; ground-beam lines Q-21 C; no strap section "
               "printed); pool blinding (its projection) HELD outside these lines (T-183 line B); DG-2 recorded only",
               "yes"),
    "B10-03": (H, ["T-167"],
               "PROFILE_AUDIT (T-064 data file, owner Q-17 A): the 28 necks released 10.855 m3 on FOUNDING_DEPTH_M "
               "(a printed excavation minimum, owner Q-21 C) become HELD; all 36 neck lines held 3.075 .. 15.375 m3, "
               "0 released",
               "neck height not established until the founding level is verified (Q-21 C); NECK_TOP_LEVEL_M (INFERRED) "
               "becomes controlling after that", "none"),
    "B10-04": (I, ["T-131"],
               "STRAPS (T-073): straps 3.781 -> 3.390 m3 measured (clear length between footing faces x printed section) "
               "+ 0 .. 1.809 m3 HELD inside open footing outlines (owner Q-31)",
               "the ground-beam concrete lines are route G profiled base lines (27.365 m3 on generic V6 conventions, e.g. "
               "the centre-to-centre length basis, not audited: T-167 s.5); GROUND_SYSTEM_SPANS_V2 (T-141) not wired; "
               "angled straps at their axis length (T-174) not integrated", "yes"),
    "B10-06": (I, ["T-133"],
               "ROUTE_G_SCOPE_V1 (T-126): columns above the necks 36.714 -> 34.446 m3, 5 pieces no upper slab plan draws "
               "NOT_APPLICABLE_WITH_EVIDENCE (2.268 m3, re-confirmed by the verifier on the structural drawing)",
               "5 held column lines (1.134 .. 3.483 m3); 3 planted columns on the slab plans not evaluated by the scope "
               "piece (first floor +1.008, second floor +0.420 m3, V3.0.2 D2); column heights rest on T-119", "yes"),
    "B10-07": (I, ["T-179"],
               "DOME_RING (T-160): the west dome ring VERIFIED 0.7552 m3 (checker 0.7553, 0.01 %) replaces route G's 4 arc "
               "bands of the same ring (0.2811 m3 + 0.2249 .. 0.6746 held, superseded by name); STR.CONC.BEAM released "
               "64.8196 -> 65.2937 m3, held 8.449 .. 14.434 -> 8.224 .. 13.759 m3",
               "east ring BLOCKED (section not printed, D-28); 24 held spans; BEAM_BINDING_V2 (T-085) and "
               "CONCRETE_LEDGER_V3 not wired; slab faces that are not slab (T-146) still in the slab line. The ring is a "
               "dome element (B10-09) carried under STR.CONC.BEAM, counted once, here. Since V3.0.7 carries the S0 "
               "shells (T-193 s.9, line byte-identical): T-185 reads the released 0.7552 m3 as the S1 edge-beam value, "
               "under S0 a CONFLICT 0.7552 .. 1.1422 m3 (plan band vs detail ring, depth 'AS PER ARCH'); its scenario "
               "tag needs a ruling in a later V3.0.x package", "yes"),
    "B10-09": (I, ["T-187", "T-193"],
               "DEFAULT_GUARD (T-186, V3.0.6): the two second-floor dome lines 3.685858 m3 each HELD (shell 0.12 / rise "
               "1.0 conventions where 10 / 190 over 442 are printed); third dome placeholder DOME-3:SHELL UNKNOWN (Q-27 A); "
               "STR.CONC.DOME released 7.371716 -> 0, 3 blocked. V3.0.7 (T-193): DOME_SHELL (T-185, scenario S0) adds "
               "DOME-A (west) and DOME-B (east) 2.540681 m3 each VERIFIED (exact solid between concentric spheres from "
               "the printed chord 4.42, rise 1.90, shell 0.10) and supersedes the two convention lines (3.685858 each, "
               "-2.290355 m3 in total: rise, thickness and outer-area basis); the east dome's second reading as a 1F "
               "'winder' stair (4.450745 m3) retired under B7-12, so each dome is carried once. STR.CONC.DOME released "
               "0 -> 5.081362 m3, blocked 3 -> 1",
               "DOME-3 (upper-roof dome) stays an UNKNOWN / HELD placeholder (no structural detail, Q-27 A; never 0); "
               "S0 rings (west ring under B10-07, CONFLICT; east ring BLOCKED), drums and shell bars (298.34 .. 432.93 kg "
               "per dome) HELD; scenario S1 / S2 rows beside in the run file only, never in the candidate totals; NOT "
               "RELEASED", "yes"),
    "B10-10": (I, ["T-187", "T-193"],
               "DEFAULT_GUARD (T-186, V3.0.6): pool floor 1.51125 and walls 1.984 m3 HELD (0.25 / 1.60 conventions where "
               "0.40 is printed; footprint 6.045 of 10.936 m2, wall band 1.24 of 2.357 m2); STR.CONC.POOL released "
               "3.49525 -> 0, 2 blocked. V3.0.7 (T-193): POOL_CONCRETE (T-183 r2) adds base 4.374226 m3 (footprint "
               "10.935564 m2 x printed 0.40) and walls 2.828071 m3 (band 2.356726 m2 x 1.20 m structural height, never "
               "the 1.15 finished depth), both VERIFIED, and supersedes the two convention lines (+3.707047 m3 against "
               "them); the steps line POOL-1:STEPS added BLOCKED. STR.CONC.POOL released 0 -> 7.202297 m3, blocked 2 -> 1",
               "the pool line group is PARTIALLY VERIFIED: steps HELD 'NOT DRAWN, consultant item' (never 0); pool bar "
               "populations (T-191, merged in lane S) not integrated; pool blinding projection HELD; joints / waterstop, "
               "membrane termination and finishes UNKNOWN; no tank, lift-pit or pump-room concrete line of the candidate "
               "(not established); NOT RELEASED", "yes"),
    "B11-01": (I, ["T-142", "T-151", "T-167", "T-179"],
               "footing steel by bar population 874.86 kg DRAWING-CONFIRMED + 2,742.51 .. 2,836.40 kg HELD (V3.0.2, T-136; "
               "owner Q-71); column 1,887.13 kg + held 1,280.99 .. 2,119.35, ground system 1,252.91 + held 1,297.14 .. "
               "2,269.56, beam 5,171.03 + held 4,247.22 .. 6,120.24 kg (V3.0.3, T-148 / T-138 / T-149; route lines "
               "superseded); neck steel 1,428.571 kg BLOCKED (V3.0.4, Q-21 C); route slab steel 2,584.35 kg superseded by "
               "held 4,643.766 .. 6,832.326 kg (V3.0.5, T-152). STR.REBAR item totals in V3.0.5 r2 = V3.0.6 (all families, "
               "incl. the stair / pool / tank lines of B7-14 / B11-03): 10,250.168 kg released, held 15,250.786 .. "
               "21,621.545 kg, 579 blocked lines",
               "links per metre (Q-71), straps (Q-74 directive, T-174), laps / development (note 9), planted-column bars "
               "(D-46), neck steel (Q-21 C), every slab bar count held; all NOT RELEASED", "yes"),
    "B11-03": (H, ["T-179"],
               "STAIR_POOL_TANK_STEEL (T-166), pool and tank part: 21 pool lines UNQUANTIFIED (their geometry superseded by "
               "T-183 r2: wall 1.20 m to the structure line; designer item D-57; the T-166 readings kept as information "
               "only), tank 2F-011 held 143.382 .. 149.310 kg, tank walls held; stair steel is counted under B7-14, the "
               "dome ring steel under B11-01 (beam ledger BM-1F-028), never twice",
               "pool steel re-derived on the verified structure (T-191, merged in lane S, not yet integrated); tank walls; "
               "dome shell steel", "none"),
}

PLANNED = {  # queued / TODO lane I packages that name the family (board 2026-10-23 14:20); merged ones removed
    "B10-13": ["T-199"], "B7-09": ["T-199"], "B6-05": ["T-199"],
    "B4-03": ["T-211"], "B4-06": ["T-211"], "B10-08": ["T-146"],
}
MERGED_TASKS = {t for p in PACKAGES for t in [p["task"], *p["integrates"]]}

DEFS = {
    "INTEGRATED_IN_CANDIDATE_AND_TESTED":
        "a merged candidate package (candidate_packages: task, merge commit, checker verdict, tests) wired a "
        "checker-verified piece into this family's lines of the opt-in candidate; HELD / UNKNOWN lines may remain and "
        "are named in 'open'; NOT RELEASED, and not a claim that the whole family is measured correctly",
    "HELD_IN_CANDIDATE":
        "a merged candidate package changed this family's candidate lines and the candidate releases no quantity of the "
        "family: every line the packages name is held, blocked or a placeholder (never 0)",
    "IN_CANDIDATE_BASE_LINES":
        "the candidate emits the family's lines exactly as its base run (ARCH_TAKEOFF_V2.13 + route G with the M4 "
        "profile) gives them; no package changed them; each Gate B since asserted them byte-identical, which is "
        "regression, not verification",
    "NOT_IN_CANDIDATE": "the candidate emits no line of this family",
}


def build():
    old_bytes = OLD.read_bytes()
    doc = json.loads(old_bytes)
    new = copy.deepcopy(doc)
    new["version"] = "1.2.0"
    new["supersedes"] = "1.1.0 (kept unchanged on disk; every released-configuration state copied unchanged)"
    new["source"] = ("1.1.0 + a candidate-level state per family re-derived from the merged ARCH_TAKEOFF_V3.0 .. V3.0.7 "
                     "candidate packages (task T-203, pilot 2026-10-23 prerequisite 6; builder "
                     "research/agents_t203/build_master_1_2_0.py; check tools/family_master_candidate.py)")
    new["loaded_by"] = ("nothing: engine/source/rule_store.py keeps 1.0.0 and engine/source/coverage_census_v2.py reads "
                        "1.1.0, so no run, census or quantity changes with this file")
    new["v3_0_candidate"] = (
        f"{CAND} (T-193 merge e866328a, Verifier 2026-10-23 11:52 UTC, Gate B PASS): the same opt-in candidate extended "
        "in place since ARCH_TAKEOFF_V3.0 (T-131 b1a6d6d): ARCH_TAKEOFF_V2.13 + route G with the M4 profile + the "
        "checker-verified pieces of candidate_packages; every line outside a package's rows byte-identical to the "
        "previous version (asserted by each package). NOT the released default (ARCH_TAKEOFF_V2.9 + route G stays "
        "released; the owner switches it). 'in_v3_0_candidate' = the candidate emits lines of the family; "
        "'candidate.state' says how; 'v3_0_planned_tasks' = queued or READY lane I packages that change them next")
    new["candidate_states"] = list(FMC.STATES)
    new["candidate_state_definitions"] = DEFS
    new["candidate"] = {
        "method_version": CAND, "as_of_package": AS_OF, "released": False,
        "released_default": "ARCH_TAKEOFF_V2.9 + route G (unchanged)",
        "scope_of_the_figures": "the development villa runs of each package (own run, reproduced by its Gate B "
                                "verdict); the methods are generic and each package tests them on a synthetic villa",
        "default_guard_note": "V3.0.6 records DG-2 SEARCH_INCOMPLETE on every convention line (one source document); "
                              "it is recorded, not holding (T-187 s.5.5): convention lines stay live in the candidate. "
                              "V3.0.7 re-runs the guard over its own lines on evidence version 2 with the convention "
                              "set the route ran on (V6 + the 17 M4 profile conventions, T-193 s.5.5); V3.0.6 lines are "
                              "not re-evaluated by it",
    }
    new["candidate_packages"] = PACKAGES
    new["in_v3_0_candidate_counts"] = {"yes": 0, "no": 0}
    counts = {s: 0 for s in FMC.STATES}
    for f in new["families"]:
        code = f["code"]
        f["in_v3_0_candidate_1_1_0"] = f["in_v3_0_candidate"]
        planned = [t for t in f.get("v3_0_planned_tasks", []) if t not in MERGED_TASKS]
        for t in PLANNED.get(code, []):
            if t not in planned:
                planned.append(t)
        f["v3_0_planned_tasks"] = planned
        if code in SPEC:
            state, pk, changed, open_, rel = SPEC[code]
            f["in_v3_0_candidate"] = "yes"
            c = {"state": state, "method_version": CAND, "packages": pk, "as_of_package": AS_OF,
                 "changed": changed, "open": open_, "released_in_candidate": rel}
        elif f["in_v3_0_candidate"] == "yes":
            c = {"state": "IN_CANDIDATE_BASE_LINES", "method_version": CAND, "packages": [], "as_of_package": AS_OF,
                 "changed": "", "open": "no verified piece integrated; the lines are the base run's (see 'missing' "
                                        "for the released path, which shares their code)",
                 "released_in_candidate": "base lines"}
        else:
            c = {"state": "NOT_IN_CANDIDATE", "method_version": CAND, "packages": [], "as_of_package": AS_OF,
                 "changed": "", "open": "no candidate line; the released capability above is unchanged",
                 "released_in_candidate": "none"}
        f["candidate"] = c
        counts[c["state"]] += 1
        new["in_v3_0_candidate_counts"][f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    assert OLD.read_bytes() == old_bytes  # 1.1.0 never written
    return new


def text(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main(argv):
    doc = build()
    bad = FMC.check(doc, is_ancestor=FMC.git_is_ancestor)
    for b in bad:
        print("PROBLEM", b)
    if bad:
        return 1
    t = text(doc)
    if "--check" in argv:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == t
        print("1.2.0 up to date" if same else "1.2.0 differs from a rebuild")
        return 0 if same else 1
    OUT.write_text(t, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['candidate_state_counts']} in_v3_0_candidate {doc['in_v3_0_candidate_counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
