# T-254 Integration package: ARCH_TAKEOFF_V3.0.17, the basis correction

Worker 3 (lane I), 2026-10-25, run session_01H97b2fAEPGDsWCdGqnzXM2. Integration package for Checker Gate B. ERS read:
s.2.1 (element first), s.2.3 (owner manual method beside the drawing method), s.3 (reconcile to the cause), s.4 (rule +
normal / adverse test), s.7 (lessons row). Nothing here is a new quantity: every figure is read from a checker-merged
file (T-289, T-287, T-253), line id by line id; (i) is the one geometric reading of this run and it drops a strip.

## 1. What changed

- `engine/source/arch_v3017.py` NEW: ARCH_TAKEOFF_V3.0.17 = V3.0.16 + piece BASIS_CORRECTION (URBAN_V3017_INPUTS_V1).
  Per record, in place (same line id, so a V2 verdict or a downgrade record stays bound): REBASE (SOURCE_DERIVED on the
  element's own printed basis, DRAWING-CONFIRMED; VERIFIED only with a checker run), HOLD / CONFLICT (BLOCKED_RFI,
  BLANK, named item; readings only in V3_0_17_SCENARIOS.json), NOT_PRESENT (NOT_APPLICABLE_WITH_EVIDENCE, a drawn
  absence; never a 0 line); a drawn element the candidate omits is ADDED only HELD. Refused: a stale 'before', a
  borrowed class depth / finished level / profile default / unmerged value as support, a held figure (0 included), a
  line twice, a group whose line ids do not sum to its declared totals, a correction list that misses a line holding a
  drawn exterior run, a drawn run bound to no line. Generic binding `bind_runs` / `check_correction_list` (the lessons
  row of T-289). Every other line byte-identical to V3.0.16, project identity block included (asserted per run).
- `tools/urban_boq_m9.py`: V3017 registration, `--v3017-inputs`, innermost step after V3.0.16.
- `research/agents_t254/`: `t254_inputs.py` (inputs from the merged files), `v3017_run.py` (the run), the 1.12.0
  builder, this report. `rules/coverage/BOQ_FAMILY_MASTER_1.12.0.json` (1.11.0 + pending V3.0.17, no family change) +
  RULES_MANIFEST by its tool. `tests/t254_basis_correction` (villa K254 hand fixture, the binding pair, NOT_PRESENT,
  development-villa input pins from merged files, family master).

## 2. Run (development villa, Drive copies 'ST7757 dxf.dxf' `9f9d1179` and P7757.dxf from P7757_DXF_COMPRESSED.zip `ab54dd55`, Python 3.11.17)

`research/agents_t167/v304_run.py` (V3.0.4 csv `d86de34a` reproduced), then `research/agents_t254/v3017_run.py` (tools/
urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.17`): V3_0_15 csv `a4dc01dd`, **V3_0_16 json `3181cf12` / csv `a4dc01dd`
(= the T-245 r2 candidate of record)**, V3_0_17 json `366be2f8`, csv `429008af`, DIFF `5861cb3a`, INTEGRATION_LEDGER.csv
`847dbf4d`, SCENARIOS `02f667f6` (the step alone, v3017_direct.py, gives the same json byte for byte). 3,699 -> 3,700
lines: 48 CHANGED (in place, same line ids), 1 ADDED, 3,651 SAME (byte-identical, asserted; outside-rows sha `7c4284a9`). One project id and one revision set kept (`5e369075`).
Export (`tools/boq_export_v1.py --lines V3_0_17_BOQ_LINES.json --candidate-version ARCH_TAKEOFF_V3.0.17 --identity
V3_0_16_IDENTITY.json`): BOQ.csv `1f6736b0`, xlsx `6376dd7d`, manifest `633d157c` (code commit 9cffa596); 3,700 rows VERIFIED 0 (no
promotion: verdicts are the Checker's), MEASURED UNVERIFIED 1,024 (was 1,047: -24 to HELD, +1 PC-1F-B), HELD 1,897 (was
1,878: +24, +1 added, -5 NOT_PRESENT, -1 PC-1F-B), EXCLUDED 779 (was 774: +5 NOT_PRESENT). Direct re-run of the step alone: `python3 -I research/agents_t254/v3017_direct.py <run>/v3017 --released
<t167>/v29/BOQ_LINES.json --out <dir>` (re-binds the five NOT_PRESENT lines against every candidate column line).

## 3. What the candidate now gives (m3), line group by line group

| Group | Lines | Released V2.9 | V3.0.16 | V3.0.17 released | V3.0.17 state | Source |
|---|---|---|---|---|---|---|
| Main-house exterior ground beams (13 'exterior' + 3 typed interior) | 16 | 8.1642 (interior depths, no printed basis) | 8.1642 | **15.9575** | DRAWING-CONFIRMED (D 0.95 = top +0.95 to N.G. +-0.00, two printed levels) | T-289 / T-253 |
| Annex exterior ground beams | 8 | 4.9740 | 4.9740 | blank | CONFLICT (D-35: literal 0.25 vs the printed section; literal reading only in the scenario) | T-289 |
| Court ground beams | 3 | 0.6270 | 0.6270 | blank | HELD (no printed section, GS-16; 0.627 .. 1.410 in the scenario) | T-289 |
| Boundary ground beam at N.G. (omitted by the engine) | +1 | absent | absent | blank | HELD (M4 column count; band 3.5256 only in the scenario) | T-253 |
| 2F columns | 8 | 3.5280 | 3.5280 | blank | HELD (D-39 roof datum; D-44 on 2) | T-289 |
| Annex columns 34A / 34D / 356 / 350 / 353 | 5 | 2.4750 | 2.4750 | blank | HELD (Q-54 B, D-39) | T-289 |
| CB5 columns C3 (365) / C5 (35F) | 2 | 1.2375 | 1.2375 | **1.4300** | DRAWING-CONFIRMED (base +0.25, h 5.20; Checker own 1.430 at 07:59) | T-287 |
| Upper columns no sheet draws (10BD / 10C5 / 10E0 @2F, 10E4 @1F / 2F) | 5 | 2.2680 | blocked | none | NOT_APPLICABLE_WITH_EVIDENCE (DRAWING-CONFIRMED absence) | T-256 |
| Planted 1F column PC-1F-B (P.C 20x50 on B26) | 1 | absent | blocked (D-26) | **0.4200** | VERIFIED component (solid 0.20 x 0.50 x 4.20; Checker 28 / 28 at 03:19); owner split column / joint stays HELD on D-26 | T-248 |

Totals: STR.CONC.GROUND_BEAM m3 released 27.3649 -> **29.5572** (+2.1923 m3, +8.0 %; 58 -> 59 lines, 12 blank);
STR.CONC.COLUMN m3 released 33.6060 -> **28.2155** (-5.3905 m3, -16.0 %; 69 -> 64 counted lines, blocked 9 -> 16, the
three bounded CONFLICT lines 1.134 .. 3.483 unchanged; the 28 closable columns 18.3465 are all now carried at their
verified volume: 25 + C8 turned matched line by line, PC-1F-A already, PC-1F-B here). Main house exterior: 8.1642 -> 15.9575 (+7.7933, +95.5 %); the
merged T-253 figure 15.9600 less the 107+7CE stub 0.0025 (item (i), s.4). Freelancer: not re-scored in this run (the
Checker scores at Gate B); released V2.9 carries the same 21.9540 m3 on these 43 lines as V3.0.16 plus 2.2680 on the
five absent columns.

(i) RESOLVED by entity handle: neck outline 17BD (layer S-COL.BON) spans both face lines of run 107+7CE (107 and 7CE)
over its full 0.300 m width and 0.300 m along the run; 7CE ends 0.0261 m and 107 0.2911 m inside it and neither passes
its far face, so the 0.0026 m2 'strip beside neck 17BD' is neck concrete: dropped from the beam (0.1118 -> 0.1092 m2,
0.1062 -> 0.1037 m3), as the Checker's T-180 slot found (Verifier 2026-10-24 12:10).

Per line (V2.9 / V3.0.16 / V3.0.17, m3; BLOCKED_RFI = blank, never 0):

| Line id | Item | Floor | Group | Released V2.9 | V3.0.16 | V3.0.17 | Evidence status | Source |
|---|---|---|---|---|---|---|---|---|
| L-0ede77cfd0badc4c7d62 | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-26f6b6f2365c72e42291 | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-33a9b7728781fcba12e2 | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-53f223b06db14ac41d47 | COLUMN | 2F | COL_2F | 0.588 | 0.588 | BLOCKED_RFI | HELD | T-289 |
| L-919a5749ef79759e01ca | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-bc01297b1c4a4c45a15f | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-c10e2945d582b5a03126 | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-d79d17d14f39d5148cb8 | COLUMN | 2F | COL_2F | 0.42 | 0.42 | BLOCKED_RFI | HELD | T-289 |
| L-694a75c84dd6e4bb4491 | COLUMN | GF | COL_ANNEX_7 | 0.5625 | 0.5625 | BLOCKED_RFI | HELD | T-289 |
| L-7d70692d03102a2dc306 | COLUMN | GF | COL_ANNEX_7 | 0.5625 | 0.5625 | 0.65 | DRAWING-CONFIRMED | T-287 |
| L-84bf7fb482a98fdbe482 | COLUMN | GF | COL_ANNEX_7 | 0.675 | 0.675 | 0.78 | DRAWING-CONFIRMED | T-287 |
| L-9f5a647014bbf83359f9 | COLUMN | GF | COL_ANNEX_7 | 0.45 | 0.45 | BLOCKED_RFI | HELD | T-289 |
| L-c0b3340a906c2c7650f8 | COLUMN | GF | COL_ANNEX_7 | 0.45 | 0.45 | BLOCKED_RFI | HELD | T-289 |
| L-e6c1c9a7feec10f64975 | COLUMN | GF | COL_ANNEX_7 | 0.45 | 0.45 | BLOCKED_RFI | HELD | T-289 |
| L-fad18af6e7139a5e99d1 | COLUMN | GF | COL_ANNEX_7 | 0.5625 | 0.5625 | BLOCKED_RFI | HELD | T-289 |
| L-2bf336912a62859834b3 | COLUMN | 2F | COL_NOT_PRESENT | 0.42 | BLOCKED_RFI | NOT_APPLICABLE_WITH_EVIDENCE | DRAWING-CONFIRMED (absence) | T-256 |
| L-73e82692ffb24059d95b | COLUMN | 2F | COL_NOT_PRESENT | 0.588 | BLOCKED_RFI | NOT_APPLICABLE_WITH_EVIDENCE | DRAWING-CONFIRMED (absence) | T-256 |
| L-7d98b1c0ac80787d0b51 | COLUMN | 2F | COL_NOT_PRESENT | 0.42 | BLOCKED_RFI | NOT_APPLICABLE_WITH_EVIDENCE | DRAWING-CONFIRMED (absence) | T-256 |
| L-99e7e45631f6ddf3c7e2 | COLUMN | 1F | COL_NOT_PRESENT | 0.42 | BLOCKED_RFI | NOT_APPLICABLE_WITH_EVIDENCE | DRAWING-CONFIRMED (absence) | T-256 |
| L-eb3bd5ba496a207f04f7 | COLUMN | 2F | COL_NOT_PRESENT | 0.42 | BLOCKED_RFI | NOT_APPLICABLE_WITH_EVIDENCE | DRAWING-CONFIRMED (absence) | T-256 |
| L-31a0424bd0efcc93efba | COLUMN | 1F | COL_PLANTED_1F | NOT_IN_RELEASED | BLOCKED_RFI | 0.42 | VERIFIED | T-248 |
| L-00465df980165c529476 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.336 | 0.336 | BLOCKED_RFI | CONFLICT | T-289 |
| L-1146bdecd41491ce9382 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.402 | 0.402 | 0.9547 | DRAWING-CONFIRMED | T-289 |
| L-21795b350fbd09150c43 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.456 | 0.456 | BLOCKED_RFI | HELD | T-289 |
| L-3284f44000c02179ace7 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.276 | 0.276 | BLOCKED_RFI | CONFLICT | T-289 |
| L-402dbe61d1c924144a3c | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.8234 | 1.8234 | BLOCKED_RFI | CONFLICT | T-289 |
| L-46f25f72b44e8bc3e2e0 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.324 | 0.324 | 0.7695 | DRAWING-CONFIRMED | T-289 |
| L-4783c6e18002c3a8a37e | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.152 | 1.152 | BLOCKED_RFI | CONFLICT | T-289 |
| L-62243c74c430d383be86 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.054 | 0.054 | BLOCKED_RFI | HELD | T-289 |
| L-62f712462a36d4ad1b32 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.516 | 0.516 | 1.2255 | DRAWING-CONFIRMED | T-289 |
| L-6bf14711798e5af93594 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.135 | 0.135 | BLOCKED_RFI | CONFLICT | T-289 |
| L-9e28c7012784a8dc33c8 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.242 | 1.242 | 1.881 | DRAWING-CONFIRMED | T-289 |
| L-a55bfa01b726ef11650c | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.117 | 0.117 | BLOCKED_RFI | HELD | T-289 |
| L-b4a13a43967ee4765662 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.045 | 0.045 | BLOCKED_RFI | CONFLICT | T-289 |
| L-bde0257c24588948167f | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.288 | 0.288 | 0.684 | DRAWING-CONFIRMED | T-289 |
| L-c9bb2eca50a2a2c8b569 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.108 | 0.108 | 0.342 | DRAWING-CONFIRMED | T-289 |
| L-cc6aaa99e1892f34b92f | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.357 | 0.357 | 0.8479 | DRAWING-CONFIRMED | T-289 |
| L-d08e7a9d809a56733ff9 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.09 | 0.09 | 0.285 | DRAWING-CONFIRMED | T-289 |
| L-d8b98b143e293d30833b | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.044 | 1.044 | BLOCKED_RFI | CONFLICT | T-289 |
| L-dac43ee18f55433b57e7 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.39 | 0.39 | 0.9263 | DRAWING-CONFIRMED | T-289 |
| L-e16c98075f69532a3dc7 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.162577 | 0.162577 | BLOCKED_RFI | CONFLICT | T-289 |
| L-e8536bc4f2699a24e2ab | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.0341 | 1.0341 | 1.6373 | DRAWING-CONFIRMED | T-289 |
| L-e9a885323ad6ec3ea32b | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 1.143 | 1.143 | 1.8097 | DRAWING-CONFIRMED | T-289 |
| L-efbed17455bb224e126e | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.4044 | 0.4044 | 0.9605 | DRAWING-CONFIRMED | T-289 |
| L-ff727b2a52e39509a659 | GROUND_BEAM | GROUND | GB_EXTERIOR_24 | 0.035102 | 0.035102 | 0.103712 | DRAWING-CONFIRMED | T-289 |
| L-26fcfbbb143269e7bb58 | GROUND_BEAM | GROUND | GB_MAIN_EXTERIOR_IN_INTERIOR_LINES | 0.171 | 0.171 | 0.5415 | DRAWING-CONFIRMED | T-289 |
| L-27d104ca6fc3556d16e6 | GROUND_BEAM | GROUND | GB_MAIN_EXTERIOR_IN_INTERIOR_LINES | 0.528 | 0.528 | 1.254 | DRAWING-CONFIRMED | T-289 |
| L-7076482d75ca42691468 | GROUND_BEAM | GROUND | GB_MAIN_EXTERIOR_IN_INTERIOR_LINES | 1.13162 | 1.13162 | 1.7349 | DRAWING-CONFIRMED | T-289 |
| L-fb7a6431fede62e93fd5 | GROUND_BEAM | GROUND | ADD | NOT_IN_RELEASED | NOT_IN_V3_0_16 | BLOCKED_RFI | HELD | T-253 |

Every line's printed support, sheets, engine basis, owner manual method and drawing method side by side, held item and
checker run are in V3_0_17_INTEGRATION_LEDGER.json (rows) and in each line's `calculation.inputs.basis_correction_v3017`.

## Verdict proposals (for the Checker)

- 16 main-house exterior lines: ENGINE_WRONG basis in V2.9 / V3.0.16 (interior class depth on exterior runs), corrected
  to the printed D 0.95; re-measure at least L-e9a885323ad6ec3ea32b (BAND0011.3: 6.35 x 0.30 x 0.95 = 1.8097) and the
  stub line L-ff727b2a52e39509a659 (0.1037).
- CB5 C3 / C5: ENGINE_WRONG basis (4.50 m profile storey), corrected to 5.20 m (T-287 G1).
- 5 NOT_PRESENT: ENGINE_RIGHT for the V3.0.x hold direction; V2.9 / route G carry 2.268 m3 on members the set lacks.
- Annex / court / 2F / annex columns / boundary: UNRESOLVED (designer items), blank.

## Lessons row (proposed)

2026-10-25 | A correction list taken from an engine flag misses members the flag never saw (3 exterior runs in interior
lines, T-289) | the list was the engine's OUTSIDE side test | `bind_runs` + `check_correction_list`: the list comes from
the drawn runs bound by geometry; a drawn run with no line, or a line holding a drawn run of the corrected class that the
list omits, refuses the integration (any villa, any trade) | tests/t254_basis_correction (normal: E2 found in an
interior-typed line; adverse: the engine-flag list refused, an unmatched drawn run reported) | CLOSE on Gate B.


## 4. What is missing / open

- (ii) ring ARC:157+158 end closure: NOT closed in this package. Own readings on the drawing (shapely, private copy):
  band between the two arcs, columns 17BA / 17BD / 17C0 deducted: 1.7633 m2 with the outer-arc span (radial ends at the
  outer arc ends), 1.8536 m2 with the inner-arc span; the merged T-242 figure 1.8262 m2 and the Checker's own 1.8385 m2
  (+0.0123, +0.67 %) both lie between. The span of the ends moves the plan area by 0.09 m2: the end rule decides it, and
  'an arc end inside a neck closes on the neck face' does not settle it here because the necks (0.30 square, centred
  2.419 m from the arc centre) leave a 19 mm sliver against the inner arc. The ring line carries the merged 1.7349 m3;
  the rule + its tests stay a row for the Lead (ERS s.4).
- ST-03 (L-061e18cf35a4b6b33d68, 0.948267 PROVISIONAL): left byte-identical for T-266 (Lead 08:15).
- The 28 closable columns (18.3465 m3, T-248): checked line by line on the V3.0.17 lines (binding by mark, storey and
  the T-289 frame within 2 mm): 25 columns 16.5825 + C8 turned 0.756 + PC-1F-A 0.588 equal their verified figures;
  PC-1F-B was held whole and is rebased here (0.420). The 5 interior ground-beam runs (2.2683 m3, T-242) are untouched
  (byte-identical); this package writes no verdict on a line (a verdict is the Checker's V2 record).
- Cross-trade named, not changed (T-289 s.4): no formwork line and no ground-storey GB rebar line on these bands
  (T-293 / T-199); the 30 column rebar lines NOT_APPLICABLE take the same heights when built; buried WP 45.4682 m2 already
  reads D 0.95.
- F-T289-01: C1 is 0.20 x 0.50 (0.10 m2); this package cites no '0.30 x 0.30' C1 text (the T-289 report s.5 does: the
  Checker's own correction stands; the research file of a merged task is not edited here).
- Guard re-check (DEFAULT_GUARD) not re-run in V3.0.17: the piece adds no default value; every rebase names a printed
  basis and every other change is a hold.
