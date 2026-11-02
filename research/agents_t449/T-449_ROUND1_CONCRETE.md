# T-449 round 1 (CONCRETE): A1 correction register

Owner follow-up directive 2026-11-02, A1. Every concrete entry (STR.CONC.*) of the V3.0.16+ project inputs is classed
(A) drawing-derived rule, (B) declared project fact or (C) unexplained patch. Rebuild:
`python3 -I research/agents_t449/t449_concrete_register.py research/agents_t449/out`.

## What is here

| File | What |
|---|---|
| `engine/source/concrete_basis_rules_v1.py` | NEW, CONCRETE_BASIS_RULES_V1 (UNWIRED_PRODUCER, stdlib, no engine import): R-GB-EXT-DEPTH-1, R-COL-LEVEL-HEIGHT-1, R-COL-SECTION-CONFLICT-1, R-PARAPET-RC-FLOOR-1, R-GB-NECK-CUT-1 |
| `research/agents_t449/DEVELOPMENT-VILLA-T131.concrete_facts.json` | class B: 8 declared facts (URBAN_PROJECT_CONFIG_V1), drawing refs by sheet only |
| `research/agents_t449/t449_concrete_register.py` | read-only register builder over the merged builders T-254 / T-266 / T-319 / T-397 / T-430 |
| `research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.{json,csv}` | 83 entries, one per corrected concrete line |
| `tests/t449_correction_register/` | synthetic rule fixture (VILLA-SYNTH-03) + register checks |

## Result

| Class | Entries | Meaning |
|---|---|---|
| A-REPRODUCED | 66 | generic rule + declared facts + Checker-merged geometry give the patch's state and quantity |
| A-SPECIFIED | 17 | drawing-derived, Checker-verified, rule named, generic code not written: NOT_PRESENT 5 (R-COL-ABSENCE-1), stairs 5 (R-STAIR-PIECES-1), ring-overlap GAP 4 (R-T392-1/2, a band-subtraction defect), held bound 1, boundary GB add 1, lift-pit walls 1 |
| B | 0 | no entry is itself a fact: the facts are in the config file |
| C | 0 | no basis names a freelancer, benchmark or earlier-result figure (text scan of every entry and its source ledgers) |

Valued lines reproduced: 19 (16 exterior ground beams, 3 columns): patch 17.807512 m3, rule 17.807491 m3,
-0.000021 m3 (-0.0001 %); 9 lines differ by at most +-0.00005 m3, the merged ledgers' 4-decimal print. Held / conflict:
15 column CONFLICT ranges (schedule vs drawn x storey height from the declared levels), 8 annex GB CONFLICT, 3 court GB
HELD, 13 columns HELD at an undeclared roof datum, 4 parapet RC HELD ranges, 2 neck-cut splits (unloaded runs 0.423 m3
each = candidate - 0.2115, the Checker's T-426 figure; loaded runs HELD 0.423 .. 0.6435 / 0.6345), 2 neck holds.

Undeclared on purpose (open items keep their lines HELD): LEVEL.STRUCTURAL_TOP.ROOF.MAIN (D-39, 13 lines),
LEVEL.STRUCTURAL_TOP.ROOF.ANNEX (Q-54B, 5), court GB basis / levels (GS-16, 3). GB.EXTERIOR.DEPTH_BASIS.ANNEX is declared
PENDING (designer D-35) and reads HELD.

## Findings

- F-T449-1: the T-253 annex literal readings (shown beside CONFLICT lines, never adopted) are not L x b x 0.25 on 4
  lines: 137+138#1 0.1725 vs 0.18, 136+7D5#1 0.4425 vs 0.45, 13D+7D2#1 0.4425 vs 0.435; line L-402dbe61 carries the run #1
  reading 0.4012 only while it bills two runs (0.7275). No BOQ quantity moves.
- F-T449-2: wiring the rules in place of the per-line values moves 9 ground-beam lines by the ledger print (sum
  -0.000021 m3); a correction of a rounding, documented, never forced back.
- F-T449-3: the geometry (run lengths / widths, sections, parapet tops, neck spans) still comes from project research
  ledgers; A-REPRODUCED means the rule reproduces the line from that Checker-merged geometry. A generic reader of that
  geometry is the next gap of A1.
- F-T449-4: tests/t450_project_config `test_part_1_wires_nothing_into_the_engine` is a part-1 snapshot; the rules module
  takes any object with lookup() / history() and imports nothing, so the guard holds; the Lead decides the guard before
  a candidate version reads the config.

## Not done (next)

Wiring: a new candidate version V3.0.x that computes the 66 lines from these rules and facts instead of the per-line
values (Checker Gate B, full line diff); generic code for the 17 A-SPECIFIED entries; rebar and blockwork rounds.
