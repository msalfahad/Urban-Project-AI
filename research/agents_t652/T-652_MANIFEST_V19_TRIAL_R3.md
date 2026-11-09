# T-652 WIRING MANIFEST V19 on V3.0.59 + overlay dry run + the 10 Nov TRIAL BOQ r3 (R-T652-1 / R-T652-2; lane I, non-candidate)

Worker 3, claim 2026-11-09T11:07Z. Nothing is wired to the candidate; V3.0.59 (NOT RELEASED) and V2.9 + route G are
untouched. Outputs: `out/WIRING_MANIFEST_V19.json`, `out/TRIAL_BOQ_R3_T652.{json,md}`, `out/TRIAL_BOQ_R3_T652_LINES.csv`
(rebuilt by `tests/t652_manifest_v19` with `URBAN_T652_WRITE=1`; the tests assert committed == rebuild). No drawing,
workbook, client name or coordinate in this folder; nothing read from Drive this run (every figure comes from merged,
Checker-verdicted research files named below).

## 1. Base move V3.0.58 copy -> ARCH_TAKEOFF_V3.0.59 (R-T652-1 (a))

The 74 merged stage lines (research/agents_t498/summary_t498.json, T-498 Gate B 4c37ce2c: UNITS.BLACK 20, MORTAR.BLACK
20, GLUE.AAC 17, UNITS.WHITE 17) were carried since V15 as 74 ADD rows of the overlay package 'T-498'. Each ADD equals
its merged line (id, item, unit, element, state: BLOCKED_RFI -> HELD blank, SOURCE_DERIVED / PROVISIONAL -> RELEASED,
BOUNDED_EXPOSURE -> HELD low .. high): 74 / 74 equal, removed. The V18 overlay re-applied on the 5,073-line V3.0.59
base gives all 5,152 lines byte-equal to V18 (asserted). Origin labels moved for 8 material groups (stage = CANDIDATE
now, the chained T-498 rows after it): explained by ruling R-T652-1 (a) only where V18 had one source or the same
explained ruling. The 2 downgraded MS1-L lines sit beside the riser / flight lines of their flight: explained by the
V18 FACE_PAIRS (two distinct pieces, never one counted twice).

## 2. V19 rows (10) on V18

| package | rows | before -> after | evidence |
|---|---|---|---|
| T-498 (chained; replaces the V18 pending row) | D-1F-07 L-3111418b | HELD blank -> HELD 0.036 .. 0.04377 m3 | HELD (Checker 07:06) |
| LINTEL_RC_BOUNDS (replaces) | L-GF-01 L-8f69c407 | HELD blank (TEXT: register hold, re-measured, RC 0.072 beside) | HELD |
| CN_NOT_APPLICABLE (T-647 FR-T647-1 .. -5) | 5 STR.CONC.COLUMN | HELD (3 x 0.378 .. 1.161, 2 blank) -> EXCLUDED | DRAWING-CONFIRMED (ST p.9 CN cells struck) |
| THRESHOLD_STRIP_A_GF_01 (T-648) | L-868aee12 ARCH.THRESHOLD | HELD blank -> RELEASED 1.000 x 0.150 = 0.150 m2 | DRAWING-CONFIRMED |
| CHECKER_DOWNGRADES_F_T645_1 / STAIR_STEPS (chained) | MS1-L tread L-151d9247, step L-d4d764ae | RELEASED 3.105 m2 / 10.35 lm -> HELD 3.105 .. 3.795 / 10.35 .. 12.65 | HELD |

Listed, no row: 17 B11 COUNT-CONVENTION GAP lines (T-647 r2) are already HELD on their census bound in the index
(3 dp; 51.574073 kg at A and at A + 1, a bound, never summed into a released total). Statement op F-C-T635-1: statement
V12 B10 'GF: COUNT' -4.576422 and '1F: COUNT' -5.306035 m3 CHECKER_VERIFIED -> PARTIALLY VERIFIED (no line).

## 3. F-C-T498-1: the 0.15 m black hosts at the V3.0.59 nets (Q-80 A)

Physical element: the 0.15 m solid black block laid in 6 host lines (15 walls), 40 x 20 installed module (Q-80 A,
UPC-BLACK-BLOCK-001 1.1.0), theoretical count (procurement HELD: waste not sourced). Owner manual method: net wall m2
x 12.5. Drawing-derived method (merged R-T498-1 (1), T-615 Checker AGREE): the RC lintel faces the ST p.13 schedule
casts inside a panel are concrete (B9-02, Q-73), not laid block, so they leave the material base.

| | m2 | units pcs | panel mortar m3 |
|---|---|---|---|
| contract net, 6 hosts (V3.0.59 MAS.BLOCK lines) | 9.895 + 58.2529 + 24.2374 + 8.595 + 25.2727 + 52.318 = 178.571 | (Lead 2,232.1375) | |
| - REQUIRED RC lintel faces (9 openings; 1F ASSUMED 2.02, GF ASSUMED 0.68) | 175.871 | 2,198.3875 | 1.945572 |
| - HELD face D-1F-09 0.34 (companion 0 .. 4.25 pcs) | 175.531 | **2,194.1375 released + HELD 0 .. 4.25** | **1.941811** (+ HELD 0 .. 0.003761) |

Rounding rule: none on the theoretical count (UPC-BLACK-BLOCK-001 'waste separate'; whole units only at procurement =
ceil(theoretical x (1 + sourced waste)), waste HELD); per-line q6 gives 1.941811 vs T-615's 1.941812 (per-wall
rounding, 1e-6). The overlay already carries these values (FR-T615-1 / -2 chained in T-498): re-derived and asserted
equal, no row added. The candidate's text 'installed module ... not stated' on these 12 lines is answered by Q-80 A:
retired (the lines are valued in the overlay; F-T652-2 finds 0 HELD lines still citing it). WHO IS RIGHT vs the Lead's
2,232.14: ENGINE_RIGHT by rule: 2.70 .. 3.04 m2 = 33.75 .. 38.0 pcs are RC lintel faces, counting them as block would
count that concrete twice. Freelancer: blockwork in m2 only, no unit row: no comparison.

**F-T652-1 (for the Lead, cross-trade, not wired):** T-615 deducted D-1F-07's face in 1F-W19 as (0.80 + 2 x 0.40) x
0.20 = 0.32 m2; the Checker's 07:06 re-measure gives that lintel 1.20 .. 1.459 m (START 0.259 < MIN 0.40), so its face
is 0.240 .. 0.2918 m2: host 1F ASSUMED base +0.0282 .. +0.080 m2 = units +0.3525 .. +1.0 pcs, mortar +0.000312 ..
+0.000885 m3. Also: R-T498-1 (1) as written deducts only faces bound to VALUED lintel lines; in the overlay every
lintel line is HELD (V2 classes), yet the merged T-615 deducts 2.70 m2 of REQUIRED faces. Physically those lintels exist
(schedule) and their faces are determinate at the printed MIN 0.40 bearing, so the deduction stands; the rule text
should say 'REQUIRED face' rather than 'VALUED lintel'. Both need a fix row; nothing here changes them.

## 4. Trial BOQ r3 (master 1.58.0; 1.59.0 = T-651 READY changes no family group or item code)

HELD with cause 2,351 / 2,744 (r2) -> **2,728 / 2,740**; F-T636-1 393 -> **12** (all UNCODED register lines
ARCH.WALL_VOLUME 6 / ARCH.WALL_PANEL 6, NOT_A_BOQ_LINE); released lines 1,566 -> 1,565; excluded 842 -> 847. HELD never
0, never summed; no unit grand is a total; three-column re-add exact at every level.

By hand (Checker acceptance, from the inputs):
- B9 pcs released 3,269.9375 = WIRED IN V3.0.59 777.05 (62.164 x 12.5) + 298.75 (23.9 x 12.5) = 1,075.80 (Gate B,
  DRAWING-CONFIRMED) + OVERLAY 123.6875 + 698.66125 + 294.4675 + 107.4375 + 315.90875 + 653.975 = 2,194.1375 (FR-T615-1,
  ASSUMED — OWNER-APPROVED); HELD 0 .. 4.25 + 29 blank.
- B9 m3 mortar 3.387982 = WIRED 0.916919 + 0.352525 = 1.269444 + OVERLAY 0.15 m panel 1.941811 + 0.15 m perimeter
  0.078582 = 2.020393 + UNVERIFIED 0.20 m perimeter keys 0.039291 + 0.058854 = 0.098145 (no stamp). B9 kg glue 20.061
  WIRED; 4 bounded 852.22278 .. 885.60468. B9-02 lintel HELD 0.991692 .. OPEN (= T-650 summary low; D-2F-01 open).
- B11 kg released 9,628.462205 (= r2; 9,216.017760 + 412.444445), 1,699 HELD all with cause (r2 1,561).
- r2 -> r3 per trade x unit: B3 m2 781.13387 -> 781.28387 (+0.150 threshold); B7 m2 79.194772 -> 76.089772 (-3.105
  tread to HELD); B7 lm 125.733094 -> 115.383094 (-10.35 step to HELD); B10 m3 HELD lines 145 -> 140 (5 CN EXCLUDED);
  B9 columns WIRED 0 -> 1,075.80 pcs / 1.269444 m3 / 20.061 kg (unverified -> Gate B status; released unchanged).

What the 10 Nov BOQ contains and does not contain: section 'contains' of the JSON / md (every trade with lines, HELD
by cause, no total over a HELD line; 38 MISSING families named).

## 5. Rule, tests, lesson

R-T652-1 / R-T652-2 in the module docstrings. Tests `tests/t652_manifest_v19` (synthetic villa K652 by hand: base
move identity, 0.15 host 9.30 x 12.5 = 116.25 .. 120.5, re-measure 0.036 .. 0.04377, CN EXCLUDED, threshold 0.150,
downgrade 3.105 .. 3.795; adverse: ADD unequal to the stage, blank stage with a figure, freelancer figure as source,
HELD as 0, NOT_APPLICABLE on a released line, unvalidated downgrade, re-measure bound not the Checker's, stale cause on
an answered decision flagged, Gate B line without a status) + training-villa rebuild and hand closures.
Proposed lessons row (s.7): "a merged Gate B stage enters the overlay base only by equality with the rows that carried
it, and the whole overlay re-applied on the new base must be byte-equal | base move after a Gate B merge | R-T652-1 (a)
(every villa) | tests/t652_manifest_v19 | PROPOSED".
