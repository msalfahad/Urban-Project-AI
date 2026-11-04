# T-487: B9-02 lintel lines, ARCH_TAKEOFF_V3.0.53 (integration package, Gate B)

Worker 3, 2026-11-04. Stream S. Opt-in candidate only; the released default V2.9 + route G is untouched.

## 1. Physical element (ERS s.2.1)

A lintel is the member that carries the masonry built above an opening's head and bears on the wall each side. It
exists only where masonry is built above the head (a beam or slab soffit at the head serves the opening itself). On the
training villa the structural set PRINTS a LINTEL SCHEDULE: cast-in-situ RC, B = wall width, D by opening-width band
(L1 0-100 cm D 20, L2 101-200 D 20, L3 201-300 D 30, L4 301-500 D 40, L5 501-750 D 55), detail MIN 40 cm bearing each
end. Physical quantity = concrete m3 B x D x (w + 2 x 0.40) per lintel; formwork 2 x D x L + B x w; bars per band
printed, bar kg not computable (cover / bends / anchorage not printed).

| | Owner manual method | Drawing-derived method |
|---|---|---|
| Where | one lintel per opening in a block wall | T-453 r2: opening census r3 widths x the merged fill pieces: REQUIRED only when every drawn piece leaves D + 0.06 m above the head |
| Type / size | owner precast 1.20 .. 4.00 m, 15 cm bearing, > 4.00 m FLAGGED (owner 2026-11-02) | the printed RC schedule (level 1 project document) governs; precast beside only (F-T453-1) |
| Quantity | m3 = B x D x L (cast) or pieces by length (precast) | same formula, recomputed in arch_v3053 from the printed band and asserted equal to the ledger |

## 2. What the package does (engine/source/arch_v3053.py, rule R-T487-1)

- One STR.CONC.LINTEL m3 line per opening in a masonry wall (60), element `LINTEL:<opening>`.
- REQUIRED (16): PROVISIONAL, 1 piece, measured = gross = B x D x (w + 2 x bearing). Formwork m2 and the host face
  (w + 0.80) x D are on the record beside, never in the quantity.
- HELD (42) / FLAGGED (2, W13 and W26): BLOCKED_RFI blank by name with the ledger reason; "at most 1 piece" and the
  minimum-bearing volume IF built beside (not a bound).
- Refused: typed quantities, a width outside its printed band, mm / cm widths, overlapping bands, schedule and precast
  rule together, a held lintel carrying a volume, a host line that is not MAS.BLOCK or whose net drifted, a second
  lintel line for an opening, a candidate that already has lintel lines.
- Host masonry: MAS.BLOCK contract area unchanged (byte-identical); the face goes to the material side only (T-498).
- Hub: a V3.0.53 run IS a V3.0.50 run first (tools/urban_boq_m9.py, method rewrite on the V3043 line; stage after the
  V3.0.50 stage; `--v3053-inputs`). Inputs: research/agents_t487/t487_inputs.py from the pinned merged ledger
  (MATERIAL_LEDGER_T453.json ad9bceee) and schedule transcription (5d5baf16).

## 3. Development-villa run (own, this session)

Drive copies P7757.dxf ab54dd55 and "ST7757 dxf.dxf" 9f9d1179 (decoded into .work/private only). Chain: T-167
v304_run, then research/agents_t487/v3053_run.py: V3_0_47 e86a53a8, V3_0_48 33a81c53, V3_0_50 **d40c4ec5** (candidate
of record reproduced, asserted) -> V3_0_53 (see summary_t487.json `chain`; the final-code apply
v3053_apply.py on that d40c4ec5 file gives the same lines file). 4,936 lines = 4,876 byte-identical + 60 added; 0
replaced; totals move only in STR.CONC.LINTEL.

| Opening | Floor | Band | B x D | L m | m3 | formwork m2 beside | host face m2 | host line | evidence |
|---|---|---|---|---|---|---|---|---|---|
| D-1F-02 | 1F | L1 | 0.15 x 0.20 | 1.80 | 0.054 | 0.87 | 0.36 | L-a56a8add | ASSUMED - OWNER-APPROVED (door head Q-55 C 2.20) |
| D-1F-03 | 1F | L1 | 0.15 x 0.20 | 1.80 | 0.054 | 0.87 | 0.36 | L-a56a8add | ASSUMED - OWNER-APPROVED |
| D-1F-04 | 1F | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | L-a56a8add | ASSUMED - OWNER-APPROVED |
| D-1F-07 | 1F | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | L-a56a8add | ASSUMED - OWNER-APPROVED |
| D-1F-08 | 1F | L1 | 0.15 x 0.20 | 1.70 | 0.051 | 0.815 | 0.34 | L-a56a8add | ASSUMED - OWNER-APPROVED |
| D-1F-10 | 1F | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | L-a56a8add | ASSUMED - OWNER-APPROVED |
| D-2F-01 | 2F | L1 | 0.15 x 0.20 | 1.80 | 0.054 | 0.87 | 0.36 | L-9056ebed | ASSUMED - OWNER-APPROVED |
| D-2F-03 | 2F | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | L-e1e06ec1 | ASSUMED - OWNER-APPROVED |
| D-GF-06 | GF | L1 | 0.20 x 0.20 | 1.80 | 0.072 | 0.92 | 0.36 | L-a3f88ecd | ASSUMED - OWNER-APPROVED; Checker AGREE |
| D-GF-10 | GF | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | L-abf15bdf | ASSUMED - OWNER-APPROVED |
| D-GF-11 | GF | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | none (wall GF-W32 HELD ON DROP) | ASSUMED - OWNER-APPROVED |
| D-GF-12 | GF | L1 | 0.15 x 0.20 | 1.60 | 0.048 | 0.76 | 0.32 | none (wall GF-W32) | ASSUMED - OWNER-APPROVED |
| D-GF-13 | GF | L1 | 0.15 x 0.20 | 1.80 | 0.054 | 0.87 | 0.36 | L-abf15bdf | ASSUMED - OWNER-APPROVED |
| W14 | 1F | L3 | 0.20 x 0.30 | 3.25 | 0.195 | 2.44 | 0.975 | L-2fdc0f97 | DRAWING-CONFIRMED; Checker AGREE |
| W15 | 1F | L2 | 0.20 x 0.20 | 2.35 | 0.094 | 1.25 | 0.47 | L-2fdc0f97 | DRAWING-CONFIRMED; Checker face AGREE |
| W18 | 1F | L1 | 0.20 x 0.20 | 1.30 | 0.052 | 0.62 | 0.26 | L-2fdc0f97 | DRAWING-CONFIRMED; Checker face AGREE |
| **16 REQUIRED** | | | | | **1.016** | **14.845** | **6.085** | | |

Hand check (any line): B x D x (w + 0.80), e.g. W14 0.20 x 0.30 x (2.45 + 0.80) = 0.195 m3; D-1F-08 0.15 x 0.20 x
(0.90 + 0.80) = 0.051 m3. Host faces: 5.445 m2 on released host lines (= T-453 r2 named deductions) + 0.64 m2 on the held
wall GF-W32.

HELD 42 (by reason): opening head not established 27; opening on a HELD wall 10; in a HELD piece 3; HELD in the fill 2.
FLAGGED 2: W13 (1F, 1.20 m, L2) and W26 (2F, 1.20 m, L2): the head leaves room for the lintel under some pieces only.

## 4. Diffs, downstream, regression

- vs V3.0.50: 60 ADDED, 4,876 SAME, 0 CHANGED (asserted, outside rows sha in V3_0_53_RUN.json).
- vs released V2.9 + route G: STR.CONC.LINTEL NOT_IN_RELEASED on every line (the released run emits no lintel line on
  this villa; registry B9-02 evidence).
- Downstream: B9-02 0 -> 60 lines, 1.016 m3 released-in-candidate (PROVISIONAL), 44 blocked; material side (T-498): the
  16 host faces 6.085 m2 leave the host material base (T-453 r2 already shows this beside the candidate); B10-13 lintel
  formwork 14.845 m2 beside, not booked; B11 lintel bar kg HELD; MAS.BLOCK contract area unchanged.
- Registry: BOQ_FAMILY_MASTER_1.50.0 = 1.47.0 + pending V3.0.53 + B9-02 text (no capability / state change).
- Freelancer: the training-villa key maps (tests/alsenan T001B / T001C) key no lintel row, so there is no freelancer
  lintel figure to compare; verdict proposal for the 16 lines: ENGINE_RIGHT by the printed schedule (hand formula above).
- Tests: tests/t487_lintel_lines (synthetic villa L by hand 0.14225 m3 + 17 adverse cases; inputs; hub; registry; run
  pins). L4 full suite: see the board handoff (task head named there).

## 5. Open / not done

Jamb bearing (MIN 40 cm) at both jambs and RC-column jambs not measured; the 0.06 m build-up is a STAND-IN; lintel
formwork not booked as STR.FORMWORK; bar kg HELD; precast-rule villas (no printed schedule) refused, not wired; the 42
HELD lintels need head levels / held walls from the census and fill.

Lessons row (proposed, ERS s.7): | 2026-11-04 | a family in the registry had no candidate line at any version |
registry 'yes' = covered | coverage is a line census: a missing family is wired as one line per physical element with
held ones blank by name, never a family total | tests/t487_lintel_lines | T-487 |
