# T-589 Structural closable-component pack (B10 / B11 / B1) for the 12-13 Nov scorecard

Worker 1 (lane S, non-candidate, research), 2026-11-07, branch `agents/task-T-589`. Research only: no engine module,
candidate line, released line, rule file or method version changed; nothing released; no quantity moves. Development
villa, not an accuracy claim. ERS s.2 - 4 and s.7 applied; R-T545-1 .. 3, R-T551-1 .. 4, R-T566-1 .. 5, R-T572-1 .. 4,
R-T576-1 .. 4, R-T583-1 .. 6, OWNER_RULE_REBAR_2026-10-24, RFI re-review 2026-11-02 (B-S12 / B-S18 / S19 and the owner
Checker conditions), MISSION no-assumptions.

## 0. Sources and run

- Statement V6 (T-586) `RECONCILED_STATEMENT_T586.json`, and the merged T-572 / T-576 / T-583 outputs, each sha256-pinned
  in `t589_alsenan.py` (a changed source refuses the build).
- Drawing read this run: Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523, the T-575 / T-583 file),
  decoded into `.work/private` only: p.7 DETAIL OF DOME (both ring sections at 400 dpi), page roles of p.3 (GROUND BEAMS
  PLAN), p.9 (schedules: footings, columns, depth table + note 1) and p.12 (continuous beams, three span).
- Code: `t589_rules.py` (R-T589-1), `t589_alsenan.py` -> `out/T589_CLOSABLE_PACK.json` / `.md` (`--check` rebuilds
  identical). Tests `tests/t589_closable_pack`.

## 1. The physical elements and the classes (ERS s.2.1)

A component is what its statement row defines: a member family by mark and storey (beams, columns, necks, footings,
blinding), a bar group by family or by face (rebar), an earthworks zone (B1). Per component the question is only **what
is missing for VERIFIED**: a Checker re-measure of something the drawings print (CLOSABLE_FROM_DRAWINGS, sheet + pack), a
value the drawings do not print or print twice (DESIGNER_ITEM, D-nn / RFI id), or a measurement no Urban rule governs
(OWNER_RULE_GAP). A component already re-measured by the Checker himself is VERIFIED_ON_RECORD; a confirmed CLASS or a
confirmed group TOTAL is not (the 1F column head total is confirmed, its per-mark split is CLOSABLE). Where a designer
value blocks VERIFIED the component is DESIGNER even if part of its geometry is closable (named `also_closable`).

## 2. Tables (n per class; quantities per source section only, never added across overlapping sources)

| Section | n | VERIFIED | CLOSABLE | DESIGNER | OWNER GAP |
|---|---|---|---|---|---|
| B10 concrete (m3) | 59 | 10 | 30 | 19 | 0 |
| B11 rebar (t) | 13 | 0 | 1 | 12 | 0 |
| B1 earthworks (m3) | 19 | 0 | 1 | 15 | 3 |

B10 by source (reference - engine, m3; every source re-adds exactly to its statement difference, asserted):

| Source | VERIFIED | CLOSABLE | DESIGNER | Statement |
|---|---|---|---|---|
| T-545 beams | 2: +0.200 (2F B2) | 17: -7.803597 (gross 18.218881) | 3: +7.376418 (held runs) | -0.227179 |
| T-551 columns | 4: +1.03125 (GF C1 / C2 / C9 / C11) | 6: -2.7275 | 9: +10.46625 | +8.770 |
| T-551 footing line | 2: -0.630 (F3, FN) | 1: +0.002 (SB2 / SB3) | 2: +10.564 (F10 + F, band) | +9.936 |
| T-551 lift walls | 1: +0.750 (scope double) | 0 | 1: +1.650 (D-43) | +2.400 |
| T-551 necks / blinding | 0 | 0 | 1 + 1: +8.805 / +34.320562 | |
| T-572 measured GF / 1F | 1: +1.03125 | 3 + 2: -2.055 / -0.480 | 1 + 1: -0.150 / -0.075 | |
| T-572 measured necks | 0 | 1: engine >= 8.8695 HELD (high open) vs his 8.805 | 0 | one-sided |

B11: T-560 G1 .. G6 (TYPED_LUMP, NOT_COMPARABLE as a figure) all DESIGNER, +34.814694 t; T-583 rows DESIGNER, low
0.767783 t, highs HELD, 2 rows HELD blank (DOME-3, lift walls kg(h)); the east-ring second-face side bars CLOSABLE
+0.021771 t low. B1: excavation valued 225.941333 m3 DESIGNER (S01 ESTIMATED founding; plan also closable P13), 14 held
zones DESIGNER (known lows 137.220011 m3, 9 without a low, highs HELD), exterior GB trench CLOSABLE 1.069269 .. 1.176467,
3 OWNER_RULE_GAP (two working-space backfill highs, disposal densities). Freelancer: NO_ROW, NOT_COMPARABLE.

## 3. Re-measure packs (14; sheets, what to measure, expected value from merged sources)

P01 beam COUNT marks (GF B28 0.2121, CA 0.1725; 1F B25 2.8500, B19 1.6236, B5 0.8325; ST p.4 / p.5 / p.10 - p.12),
P02 THROUGH_SUPPORT allowance per mark (GF -2.901714 / -3.022166 after T-576, 1F -1.593362, 2F -0.420), P03 RUN_COUNT
(GF B1, 1F B4 / B6; B4 vs ring <= 0.331 m3 between components), P04 five small terms named by T-566 (1F CB12 extent
12.00 m), P05 GF B7 12 piece ends (T-576 allowance 3.55 vs 2.363 m), P06 stair-beam upstands, P07 west ring B4 7.552 m,
P08 column head split per mark (D_ctrl), P09 GF column base drop, P10 1F C3 count, P11 SB2 / SB3 lengths, P12 dome-ring
side bars (done this run, below), P13 B1 plan side (16 pits, pool envelope, exterior GB cut), P14 necks on his count.
Full text in `out/T589_CLOSABLE_PACK.md`.

## 4. T-583 restated (F-C-T583-1), own read of ST p.7

Both ring sections of DETAIL OF DOME draw side bars on **both** vertical faces, at two levels (2 + 2 dots), labelled
'2ø14/20cm' on a leader that passes through both dots of one level. Read as the drawn population: 4 d14 over the in-bay
length 8.9974 m = 4 x 8.9974 x 196 / 162 = 43.543 kg (T-583 took 2 bars, 21.771 kg). **East ring row low 0.122518 ->
0.144289 t; bounded-rows low 0.767783 -> 0.789554 t; west row low unchanged 0.063897** (its low is the B4 reading; the
detail reading becomes 0.103011 + 0.018275 = 0.121286, still above). Further rows over the unprinted ring depth stay
HELD. Status PROPOSED (worker read); the Checker confirms on p.7; the row itself changes only in lane S's next ring
package (new method version, not in place).

## 5. Findings, who is right, what is open

- **F-T589-1** (statement / T-572 bound): the F10 + F footing line carries S02 **2.176 .. 2.275 m3**, but the owner
  (2026-11-02, Checker condition 4, accepted) set S02 to **1.960 .. 2.275 m3** (F10 alone 2.80 x 1.40 x 0.50 = 1.960,
  F10 + F 2.176, drawn outline 3.25 x 1.40 x 0.50 = 2.275), each interpretation one consistent scenario. Effect: low
  -0.216 m3; T-572 footing-line bounded part 7.8445 -> 7.6285 m3 low; his 1.960 moves from BELOW to AT the low. A held
  line: no released quantity moves. Lead: lane S fix row.
- **F-T589-2**: the court ground-beam zone (no section printed, T-350) has no RFI of its own (nearest RFI-S09).
- No ENGINE_WRONG found; no quantity changed. ERS s.2.7 not met on any row: **no owner question** (designer items are on
  the D / RFI lists; the three OWNER_RULE_GAP rows are already governed by owner rulings: backfill method 2026-11-02 17:45
  and placement density 2026-11-02 18:00).
- Uncertain: the HELD beam-run D ids (2F B1 x2 / B8 ext.) are taken from the T-545 group text, not per line; T-560 G rows
  are DESIGNER because their held blank lines rest on bar-end / lap items, the comparison itself stays NOT_COMPARABLE.

## 6. Rule, tests, lessons row (proposed)

R-T589-1 (`t589_rules.py`, every villa). `tests/t589_closable_pack`: hand villa K589 (column 0.30 x 0.60 x 3.00 = 0.540
m3 CLOSABLE on S-02; column under an unprinted roof level DESIGNER D-01, HELD, never 0; split re-add), adverse (closable
without sheet / with a sheet-less text / without pack refused; unknown class; kg / mm / % / float refused; designer
without D / RFI id; held as a point; VERIFIED without Checker; owner question without ERS 2.7; low > high; unit in the
wrong table), development villa (rebuild = committed, counts, packs, every source re-adds to V6, F-C-T583-1 numbers by
hand, findings, an unclassified component refused, source hash pinned).

Lessons row (ERS s.7): | 2026-11-07 | the scorecard counted structural rows as PARTIALLY VERIFIED without saying which
the drawings can close | a confirmed class or group total was read as a verified component, and designer blocks were
not separated from re-measure work | classify every non-verified component by what is missing (drawing re-measure with
sheet + pack / designer id / owner-rule gap); VERIFIED only for a component the Checker re-measured himself; never add
class quantities across overlapping sources | R-T589-1 (every villa) | tests/t589_closable_pack | PROPOSED |
