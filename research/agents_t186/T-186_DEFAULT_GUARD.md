# T-186 Default guard: no convention value where the project documents print one (every villa)

Worker 3, 2026-10-22. ERS: read, s.2 (steps 1-4), s.3, s.4 (rule + test), s.7 (lessons row below). Lane I, unwired piece
(the board row: "NEW unwired function first, then wired as a V3.0.x extension with Gate B"). Nothing is wired, no
quantity, frozen file, rule version or released default changed. NOT RELEASED.

## 1. What the guard is (the owner's rule, made checkable)

Owner 2026-10-22 (pool lesson): "Before applying any default, search and reconcile all relevant project drawings,
sections, schedules and details. An owner-approved fallback is only used when the project documents genuinely do not
establish the value." `engine/source/default_guard.py` reads BOQ lines that declare their basis (which value came from a
convention, a printed record, a derivation or the drawn geometry; which documents were searched; the plan footprint
measured; the physical zones counted; the scenario; the deductions) and returns guarded copies. A failing line becomes
HELD with every finding and its citation; its value stays visible as `info_qty`, never summed, never 0.

| Check | Code | Physical / evidence meaning | Development-villa case it encodes |
|---|---|---|---|
| DG-1 | CONVENTION_WHERE_PRINTED / PRINTED_VALUES_DISAGREE | a convention used while the documents print the value (cited); two printed values disagree = a conflict, never settled by the guard | pool 0.25 / 1.60 vs printed 0.40 (T-180) |
| DG-2 | SEARCH_NOT_RECORDED / SEARCH_INCOMPLETE / FALLBACK_NOT_APPROVED | a convention is a fallback only after every plan, section, structural detail and schedule of the register was searched, and only with an answered owner approval (WORKFLOW_CONTROLS s.4); then labelled ASSUMED - OWNER-APPROVED | the pool line read only the structural DXF; the 0.40 sits in the PDF detail |
| DG-3 | PARTIAL_FOOTPRINT / FOOTPRINT_EXCEEDS_DRAWN | measured plan area / length vs the drawn element part, tolerance 0.5 % | straight strip of a curved ring |
| DG-4 | FINISHED_AS_STRUCTURAL / UNSUPPORTED_REF | a concrete / rebar / formwork dimension from a FINISHED level or depth; accepted when DERIVED with a printed build-up | T-183 r1: finished water depth 1.15 as the RC wall height (D-T183-1) |
| DG-5 | SILENT_OMISSION | a drawn element or part (one flight on an upper storey) carried by no line, measured or HELD; a HELD placeholder is added | 1F -> 2F flights folded away; a second stair missed |
| DG-6 | DOUBLE_COUNT | one physical zone declared by two live lines of one trade and unit | landing in stair and slab; pool base under the wall in floor and wall |
| DG-7 | CLIENT_CHANGE_AS_APPROVED / REVISION_NOT_ISSUED | approved design S0, client request S1, consultant revision S2 kept apart; S1 never in the approved baseline; S2 only with an issued revision | domes (owner Q-29: client request, no consultant revision) |
| DG-8 | DEDUCTION_EXCEEDS_MEMBER | a framing member covers only its own width of a face | T-163: a beam running through a column face deducted the full face |

## 2. Synthetic villa Q (not the development villa; hand calculation in tests/t186_default_guard/villa_q.py)

Pool with one half-round end: outer 5.00 x 2.50 + pi 1.25^2 / 2 = 14.954369 m2, inner 4.75 x 2.00 + pi 1.00^2 / 2 =
11.070796 m2, wall ring 3.883573 m2 (straight strip only 3.000000: curved half 0.883573 lost). Printed: base 0.35, wall
0.25 (structural detail), FINISHED water depth 1.40 and build-up 0.05 (section): structural wall height 1.45 m.

| Case | Pool m3 | Guard |
|---|---|---|
| Drawing-derived: floor 14.954369 x 0.35 + walls 3.883573 x 1.45 | 5.234029 + 5.631181 = 10.865210 | PASS, DRAWING-CONFIRMED |
| Old behaviour: rectangle 12.50 x 0.25 + straight strip 3.00 x 1.60, plan sheet only | 3.125 + 4.800 = 7.925 (-2.940, -27.1 %) | both HELD: CONVENTION_WHERE_PRINTED (0.35 cited), PARTIAL_FOOTPRINT (83.6 % / 77.2 %), SEARCH_INCOMPLETE; released pool 0, held never 0 |
| Finished depth as RC height: walls 3.883573 x 1.40 | 5.437002 (-0.194179 = ring x 0.05) | FINISHED_AS_STRUCTURAL |
| Base under the wall counted twice: walls x 1.80 | +1.359251 (= ring x 0.35) | DOUBLE_COUNT on both lines |

Stairs (waist 0.15 printed): flight 1.20 x 3.00 x 0.15 + 10 x 0.5 x 0.30 x 0.17 x 1.20 = 0.846 m3, landing 0.216 m3;
ST-A dog-leg GF -> 1F -> 2F 3.816 m3 + ST-B 0.846 m3. Adverse: ST-B dropped (SILENT_OMISSION, HELD placeholder with no
value), F3 + F4 on the upper storey dropped (2 omissions), landing L1 also in the 1F slab (DOUBLE_COUNT). Dome D1:
shell 12.00 m2 x 0.10 = 1.200 m3 S0; the client's skylight (S1) relabelled S0 with the shell removed ->
CLIENT_CHANGE_AS_APPROVED + SILENT_OMISSION; tagged S2 with no issued revision -> REVISION_NOT_ISSUED. Column C3 face
0.60 m with a 0.20 m through-beam: deducting 0.60 -> DEDUCTION_EXCEEDS_MEMBER.

Tests: 32 in tests/t186_default_guard, each check with a normal and an adverse case; `test_each_check_is_load_bearing`
runs every adverse case with its check disabled and shows the defect passes silently (the old behaviour), so each test
fails if the guard regresses.

## 3. Application on the development villa (read only; released baseline A V29_ROUTEG_NO_PROFILE)

Run: `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` on the Drive copies
(P7757_DXF_COMPRESSED.zip sha ab54dd55, ST7757 dxf.dxf sha 9f9d1179): REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4.
Then `research/agents_t186/t186_apply.py` with `dev_villa_guard_evidence.json` (every printed record names its merged or
answered source: the Q-17 A data file of T-064, Checker T-180, owner Q-26 A, Q-27 A, Q-47 A; T-111 ledger for the stair
inventory). 820 lines rest on a V6 convention: 236.265 m3 concrete, 16,392.647 kg rebar (provisional / released lines).

| Finding | Lines | Quantity the guard holds | What the documents print |
|---|---|---|---|
| Pool floor + walls: CONVENTION_WHERE_PRINTED + PARTIAL_FOOTPRINT | 2 | 3.495 m3 (1.511 + 1.984) | base 0.40 (ST7757.pdf p.7; T-180 VERIFIED 4.374 m3); depth 1.15 FINISHED (Q-26 A; RC height to the structure line still open, T-183 r2); footprint 6.045 of 10.936 m2 (55.3 %), wall band 1.240 of 2.357 m2 (52.6 %) |
| Two domes: shell 0.12 and rise ratio 1.0 conventions | 2 | 7.372 m3 | 'DETAIL OF DOME' 442 / 190 / 10: shell '10', rise 1.90 over 2.21 (ratio 0.8597); the meaning of '10' to be confirmed by T-185 |
| Main stair GF -> 1F and round stair: waist 0.175 convention | 2 | 3.687 m3 (2.786 + 0.901) | 'T 16' in the stair panels (Q-47 A); the entrance flight (no thickness printed) is NOT flagged |
| Continuous-beam bars: bottom extension 0.15 convention | 75 | 1,885.362 kg | '7.5cm' (data file DRAWING-VERIFIED); the same 75 lines also carry PRINTED_VALUES_DISAGREE: support-bar extent 0.25 convention vs printed 0.22 Ln and 0.3 Ln2 (data file HELD, T-044 class DIFFERENT) |
| Blinding projection 0.10 convention | 1 | none (already a bounded exposure) | 0.10 printed, same value: re-basis on the printed record |
| SILENT_OMISSION | 3 placeholders | not measured | ST-01 1F -> 2F flights and the lobby flight (T-111 drawn, no engine stair line on those storeys); third dome on the upper roof (Q-27 A, no structural detail) |

Totals the guard holds (substantive checks DG-1 / 3 / 4 / 5 / 7): 14.554 m3 concrete (6.2 % of the 236.265 m3 on
conventions) and 1,885.362 kg rebar (11.5 % of 16,392.647 kg). With DG-2 on, ALL 820 lines are HELD: every route G
canonical line cites exactly one source document (the structural DXF), so no line can show that the PDF details,
schedules or architectural sections were searched. That is a real gap of the line format, not 820 defects.

Engine vs freelancer (concrete, the three element families above): engine A pool 3.495 vs freelancer 12.348 m3, stairs
4.635 vs 15.053, domes 7.372 vs 6.780: under the guard all 14.554 m3 become HELD with the printed values cited; no line
is moved to a printed value by the guard (that is the measuring tasks' job, T-183 r2 / T-184 / T-185). No accuracy claim.

Verdict proposals: none new. The guard measures nothing, so it proposes no who-is-right verdict; it only shows that
these engine lines are not drawing-based. Pool: the Checker's own re-measure (T-180, 7.084 m3 with walls still to
re-basis) already differs from both engine 3.495 and freelancer 12.348; stairs / domes: UNRESOLVED until T-184 / T-185;
beam bottom extension: no freelancer line compares at that level.

## 4. General rule (proposed; scope and provenance)

R-DG-1 (any villa; owner 2026-10-22 pool lesson + WORKFLOW_CONTROLS s.4 / s.5): a quantity may rest on a convention value
only when (a) every plan, section, structural detail and schedule of the project register was searched and none prints
the value for that element, (b) an answered owner decision or the rule library approves that fallback, and (c) the line
records (a) and (b); it is then ASSUMED - OWNER-APPROVED. A convention where a printed value exists, a FINISHED value used
as a structural dimension, a partial footprint, a drawn element with no line, one zone in two lines, a client change in
the approved baseline or a deduction wider than its member makes the line HELD with the cause, never 0. Provenance: owner
rule 2026-10-22 (ERS s.7 DEFAULT GUARD row), D-T183-1, D-T163 (Checker 2026-10-22 12:05), Q-29 scenario rule. The Lead
records it in the rule library as a NEW rule version if accepted (no existing rule file edited here).

## 5. Lessons-register row (proposed for ERS section 7)

| 2026-10-22 | The default guard was a rule in words only; 75 beam-bar lines (1,885.36 kg) of the released baseline still use the
0.15 m bottom-extension convention where the drawing prints 7.5 cm, and every route G line cites only one source
document | Conventions applied per line with no check against the project's printed-value register; the line format
records one source file, not the documents searched | R-DG-1 above (any villa) | tests/t186_default_guard (normal +
adverse per check, load-bearing mutation test) | guard built, unwired; wiring = V3.0.x (after T-167) |

## 6. Missing / for the Lead

- Wiring: a V3.0.x extension (new arch_v30x module) applying the guard to the candidate, AFTER T-167 V3.0.4 merges (same
  candidate chain; T-179 also waits on it). Gate B then.
- The canonical line format needs a `documents_searched` field (DG-2), emitted zones (`covers`, DG-6) and deductions
  (DG-8): route G emits none today, so on engine output DG-6 / DG-8 run only where a ledger declares them.
- The evidence file is a development-villa data file built from merged / answered sources only; the Lead's element
  register (ELEMENT_REGISTER.md) should own the inventory and the engine -> element mapping (the stair mapping here rests on
  the 2026-10-22 reconciliation file and T-184, READY, Gate A pending).
- V3.0.3 / V3.0.4 not run here: T-167 reports the beam-bar lines superseded by the T-149 ledger there; the pool, stair
  and dome lines are unchanged in the candidate.
- One baseline-A rebar line has measured_net 0.0 (a CB bottom bar D18): a live zero quantity, for the Lead to route.
