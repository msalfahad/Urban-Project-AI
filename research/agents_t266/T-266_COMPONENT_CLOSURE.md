# T-266 Integration package ARCH_TAKEOFF_V3.0.18: stairs, the 1F landing marble and the GF pantry piece

Worker 3 (lane I), 2026-10-25, run session_01SpTFTZhva37HmL1jJWFgWz. Integration package for Checker Gate B. Opt-in
candidate only: the released default stays ARCH_TAKEOFF_V2.9 + route G (no switch); nothing here is RELEASED. ERS
2026-10-22 read and applied (s.2.1 element first, s.2.3 owner manual vs drawing method, s.3 build before deduct, s.4
statuses). Drawings named by Drive folder and title only; no coordinates, no client text committed.

## 1. What the package does (line id by line id, from merged ledgers only)

| Kind | Line | Before (V3.0.17) | After (V3.0.18) | Status | Source |
|---|---|---|---|---|---|
| SPLIT parent | L-7863355dfcb68a681d2d ST-01 GF -> 1F | blank (BLOCKED_RFI) | blank, items restated | HELD: MS1-L CONFLICT 0.863029 .. 1.054813 (C-ST-4), MS1-T 0.12 .. 0.13 and turn slab (C-ST-3 / G2-a) | T-290 / T-258 r2 |
| SPLIT part | L-e37d81a8be8e0aa0010c (new) | - | **1.227952 m3** (SOURCE_DERIVED) | VERIFIED: MS1-LD 0.2304 (Checker 22-10 17:18) + MS1-U 0.997552 (Checker own 0.9976, D-CHK-T180-1 rev2) | T-258 r2 |
| SPLIT parent | L-b6b0354b7842f0ed6e41 ST-02 round stair | blank | blank, items restated | HELD: RS-C (Q-50 / Q-51, G2-w), RS-C soffit, CA 0 .. 0.09, 2CC UNKNOWN | T-290 / T-258 r2 |
| SPLIT part | L-056402f98a6dbbcde0a0 (new) | - | **1.536225 m3** (PROVISIONAL) | ASSUMED - OWNER-APPROVED (Q-50 A cond): RS-S 0.942732 + RS-LD 0.2164 + RS-A 0.377093 | T-258 r2 |
| SPLIT parent | L-821032bc04a0b0d02133 ST-01b lobby D1 | blank | blank, items restated | HELD: D1 waist (G2-w) | T-290 / T-258 r2 |
| SPLIT part | L-85f64587588af8537b4b (new) | - | **0.100286 m3** (SOURCE_DERIVED) | DRAWING-CONFIRMED: D1 steps net of the GS-08 wedge | T-258 r2 |
| REBASE | L-2416e65f053a14199cfc MS2-LD | BOUNDED 0.4696 .. 0.48 | **0.4696 m3** | DRAWING-CONFIRMED: plates 1.495 + 1.440 m2 x T 16 (Checker own 11:05); 0.480 retired (double count) | T-290 |
| HOLD | L-061e18cf35a4b6b33d68 ST-03 | 0.948267 PROVISIONAL (convention riser 0.165 / waist 0.175) | **blank** (BLOCKED_RFI) | HELD: S-9 / G2-w, E1 waist not printed; steps 0.355017 DC named, not booked | T-289 row ST03 (cited) |
| MATERIAL | L-8011889d84788553a6b1 (new) FIN.MARBLE.LANDING 1F | none (gap named by the T-278 verdict) | **4.9225 m2** (PROVISIONAL) | ASSUMED - OWNER-APPROVED (Q-66 B marble); area VERIFIED on ARCH.SPACE L-428b44ee (unchanged) | T-278 |
| PIECE_LINE | L-6c83b9fcaa8684a4b85b (new) FIN.FLOOR.WET_TILE GF | not in any line (engine strip held on a misread boundary) | **1.100 m2** (PROVISIONAL) | geometry DRAWING-CONFIRMED (T-286), class ASSUMED - OWNER-APPROVED (Q-37 A): the line takes the weaker | T-286 |

Everything else: 3,695 lines byte-identical to V3.0.17 (asserted by the module: whole-line sha, outside-rows hash
`83b1467b`), project identity block unchanged. 3,700 -> 3,705 lines: 5 CHANGED, 5 ADDED, 0 removed.

Line-status mapping (the V3.0.10 / V3.0.13 convention): VERIFIED and DRAWING-CONFIRMED -> SOURCE_DERIVED; ASSUMED -
OWNER-APPROVED -> PROVISIONAL with its owner source on the line. The evidence status itself is on every line
(`calculation.inputs.component_closure_v3018.evidence_status`) and in the integration ledger.

## 2. Engineering effect (candidate, NOT RELEASED)

| Measure | V3.0.17 | V3.0.18 | Change | Freelancer |
|---|---|---|---|---|
| Stair concrete released (STR.CONC.STAIR, m3) | 2.983085 (incl. ST-03 0.948267 on a convention) | 5.368881 | +2.385796 | - |
| of which VERIFIED / DRAWING-CONFIRMED / OWNER-APPROVED | 2.034818 / 0 / 0 (+0.948267 convention) | 3.262770 / 0.569886 / 1.536225 | - | - |
| Stair + dome concrete (CONC.STAIR_DOME key, m3) | 8.064447 | 10.450243 | +2.385796 | 21.8328 (-11.382557, -52.1 %; was -13.768353, -63.1 %) |
| Held stair lines (blank, never 0) | 4 + 1 bounded | 5 | MS2-LD leaves bounded, ST-03 enters held | - |
| Internal floor area (key T001C, m2) | 380.364050 on 40 lines | 381.464050 on 41 lines | +1.100 (+0.29 %) | 409.58 (-28.116, -6.86 %; was -7.13 %) |
| Pantry wet floor (FIN.FLOOR.WET_TILE, m2) | 12.354868 | 13.454868 | +1.100 = box 13.455 (residual -0.0001) | no pantry wet row (Q-37) |
| Stair landing marble (FIN.MARBLE.LANDING, m2, released) | 0 (GF / 2F landing lines BOUNDED) | 4.9225 | +4.9225 | - |

The freelancer gap on stairs / domes is NOT an accuracy figure: it is the held pieces (MS1-L, MS1-T, MS2-TR, RS-C, D1 /
E1 waists, DOME-3, the drums) plus the rule / reading differences T-258 s.4 reconciled by component (ST-01 his 5.3 m
run incl. the floor landing and 0.28 / 0.20 thickness vs T 16; ST-03 his 1.8 m run vs drawn 1.2 m; ST-02 UNRESOLVED;
domes area not established). Released V2.9 + route G unchanged (still carries ST-01 GF 2.78598, ST-02 1.76946 and ST-03
0.948267 on conventions: an owner-only switch; the candidate shows what a release would correct).

## 3. Owner manual method vs drawing method (ERS s.2.3)

- Stairs: the owner measures a flight by printed treads / risers / waist and a landing between drawn edges; where the
  round-stair riser is not printed, Q-50 A (condition) gives it (ASSUMED - OWNER-APPROVED); an unprinted waist or
  winder has no owner fallback (WORKFLOW_CONTROLS s.4): HELD. Drawing method: each piece from its drawn lines on the
  structural stair sheets (T-258 r2 handles), one line per status group of closable pieces, the remainder blank. They
  agree on every released piece; they differ only where the owner rule supplies the riser (ST-02, labelled).
- 1F landing marble: owner Q-66 B (marble with the stair, once, its own element); drawing: the landing area 4.9225 m2
  = printed 2.50 x 1.95 - well end 0.20 x 0.05 + nosing band 1.15 x 0.05 (RULE_DIFFERENCE 0.0475 vs printed 4.875,
  T-122 / T-269). One element, two measures: AREA on ARCH.SPACE (FLOOR.INTERNAL), MATERIAL on FIN.MARBLE.LANDING; the
  1F living porcelain keeps deducting it; no second floor-area count.
- Pantry piece: owner Q-37 A (wet within the printed 4.50 x 3.00 box); drawing: 1.40 x 0.50 + 0.50 x 0.80 = 1.100 m2
  bounded by drawn wall / room / counter lines inside the box (one 0.50 m undrawn engine zone line). Agree.

## 4. Decisions taken in this package (for the Checker)

1. **ST-03 is held IN THE LINE.** The Lead's 14:15 note says ST-03 is already HELD in V3.0.17. Own run: the V3.0.17
   line is still PROVISIONAL 0.948267 (T-254 left it byte-identical "for T-266"); only the Checker's downgrade record
   DG-5678660edb059395 holds it in the export, and that record binds the V3.0.17 file hash, not V3.0.18. Leaving the
   line would carry an unsupported-basis quantity into a new file with no record. The line becomes BLOCKED_RFI blank,
   citing T-289 row ST03 (booked once there) and naming the downgrade it resolves; the steps 0.355017 m3 DC are named,
   not released (not in the Lead's closable list; a later package may split them).
2. **Drums: no line** (Lead 14:15 "named omission, no line, no number"; the 10:15 note and the T-290 verdict said two
   HELD lines; the later Lead note governs). Named in WAITING_PIECES `DOME_DRUMS` of the run and ledger.
3. **E1 waist**: carried as the Checker settled it (11:05): concrete HELD (G2-w), soffit form NOT_APPLICABLE; no
   CONFLICT remains.
4. **D1 width residual** (Checker 11:05): 1.150 vs 1.200 lane -> -0.004179 m3 (-4.2 %), carried as a note on the D1
   part, no RFI.
5. **The pantry piece is its own line**, not added into the RC99C2A wet part: it is a separate physical piece (floor
   under the east counter, engine strip SITE-0a31aaa10796d33a) that no candidate line carried (the OP-003 threshold
   twin and strip lines are NOT_APPLICABLE); a line per piece keeps one owner per piece checkable.

## 5. Generic rule, code, tests

R-COMPONENT-CLOSURE-1 (rule version T-266; every villa; provenance T-258 / T-290 / T-278 / T-286; research rule, a new
rule version when adopted into the library): a candidate line's status equals the status of the merged component ledger
of its element: a quantity only when every piece is closable, at the weakest status; a held parent with closable pieces
is SPLIT (each status group its own line, the remainder blank naming the pieces still held and the lines carrying the
rest); a convention basis is HELD; a material of an element measured as area is its own material line at the element's
quantity (one per code per element); a confirmed piece no line carries is its own line at the weaker of its geometry
and class statuses; a piece is booked once.

Code: `engine/source/arch_v3018.py` (MEDIUM, not frozen; kinds SPLIT / REBASE / HOLD / MATERIAL / PIECE_LINE,
`check_splits` on finished lines), `tools/urban_boq_m9.py` (opt-in V3018 tuple and `--v3018-inputs` only; no default
switched, older method lists unchanged), `research/agents_t266/t266_inputs.py` (inputs from the merged ledgers, every
figure asserted against them), `v3018_run.py` / `v3018_direct.py`, `rules/coverage/BOQ_FAMILY_MASTER_1.13.0.json`
(1.12.0 + pending V3.0.18, no family change; builder `build_master_1_13_0.py`; manifest by `tools/m9_rules_manifest.py`).

Tests `tests/t266_component_closure` (33): villa K266 hand fixture (landing 1.20 x 1.10 x 0.15 = 0.198000; upper
flight steps 0.280500 + waist 3.448188 x 0.15 x 1.10 = 0.568951 -> 0.849451; part 1.047451 VERIFIED; owner-rule
flight 0.5; bounded landing 0.300 DC; convention flight held; marble 4.0 m2; pantry piece 1.25 m2); ADVERSE: a part
released while its parent carries a figure (inputs and finished-line check), one piece in two parts, mixed status /
convention piece in a part, mm-scale value slip, VERIFIED without a checker run, owner-approved without its answer, HOLD
with 0, held piece with 0, piece value 0, a second marble line on one element, a material value / unit that is not the
element line's, a piece already booked elsewhere, a piece line stronger than its class, stale before, unknown line,
line named twice, unmerged task, a new material line marked VERIFIED; order invariance; registry 1.13.0 normal +
adverse; Alsenan pins (r2 2.864463 not r1 2.915089, statuses, 0.4696, ST-03, marble, pantry; an edited ledger, a
mixed-status part, a closable piece named held stop the build).

## 6. Run (identity)

Own decode of Drive "Alsenan chalet project" 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from
P7757_DXF_COMPRESSED.zip (`ab54dd55`), Python 3.11.17: `research/agents_t167/v304_run.py` (V3_0_4 csv `d86de34a`
reproduced) then `research/agents_t266/v3018_run.py`: V3_0_15 csv `a4dc01dd`, V3_0_16 json `3181cf12`, V3_0_17 json
`366be2f8` / csv `429008af` / DIFF `5861cb3a` = the candidate of record (T-254 Gate B) byte for byte. V3.0.18 hashes:
see the handoff (runner and `v3018_direct.py` on the same V3.0.17 give the same files).

## 7. Who is right (proposals)

- ST-01 GF, ST-02, D1: ENGINE over-held 2.864463 m3 of closable pieces inside blank lines: now released at their own
  statuses; remainder HELD.
- MS2-LD: ENGINE over-held (bounded): 0.4696 DC (Checker own).
- ST-03: ENGINE_WRONG basis (convention) -> HELD; freelancer 1.4112 (run 1.8 vs drawn 1.2: ENGINE_RIGHT on geometry,
  thickness UNRESOLVED).
- 1F landing marble: ENGINE omission (no material line) -> 4.9225 m2 by Q-66 B.
- Pantry piece: ENGINE_WRONG_CLASS (undrawn zone line + fixture outline read as strip boundaries) -> 1.100 m2 WET.

## 8. Lessons row (proposed, ERS s.7)

2026-10-25 | A Lead note said a line was "already HELD in V3.0.17" because a Checker downgrade record held it in the
export, while the line itself still carried the convention quantity; downgrade records bind one candidate file hash and
do not carry to the next version | A status held only by a file-bound record silently re-appears as a quantity in the
next candidate | An integration package reads the LINE's own state on its own run, and every downgrade record bound to
the previous file is either resolved in the line (HOLD / REBASE) or listed for re-issue; the package names the record
it resolves (any villa) | tests/t266 test_t266_inputs_pins (ST-03 before PROVISIONAL 0.948267 -> HOLD, `resolves`
DG-5678660edb059395) | OPEN (T-266 READY).

## 9. Missing / held

Drums (no line, G3-b), DOME-3 (G3-a / D-21), MS1-L (C-ST-4 CONFLICT range), MS1-T / turn slab / MS2-TR (C-ST-3), D1 /
RS-C / E1 waists (G2-w), RS-C curved part (Q-50 / Q-51), CA level, 2CC; ST-03 steps 0.355017 DC named, not released;
the GF / 2F landing marble lines stay BOUNDED (not this package); formwork r4 findings of T-290 (MS2-LD soffit 3.000 vs
2.935 m2, RS-A 1.25 vs 1.20) belong to the formwork integration (T-293 part 2 / T-199), not changed here.
