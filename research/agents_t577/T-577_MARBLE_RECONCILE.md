# T-577 Marble / stone thresholds, window sills, lift and entrance stone vs the freelancer (lane A, research only)

Worker 2, 2026-11-06, branch `agents/task-T-577`, candidate of record ARCH_TAKEOFF_V3.0.58 (= V3.0.57 for every code
read here). No quantity, line, method, rule or registry file changed. Development villa, not an accuracy claim; the
method R-T577-1 is for every villa. Build: `research/agents_t577/t577_alsenan.py [--check]` ->
`out/T577_MARBLE_RECONCILE.json` (pinned inputs: line index V3.0.57, FREELANCER_RAW_ROWS, T-325 ledger).

## 1. Physical elements (ERS s.2.1)

One piece per opening / station, three measures never mixed: THRESHOLD (clear width lm; width x wall t m2; 1 nr),
SILL (width + printed returns lm; x depth m2; 1 nr), LIFT_THRESHOLD / LIFT_SURROUND (T-475), EXT_STEP (a step outside an
external door: its own element, never the strip in the wall), E1 entrance steps / landing (T-343 / T-490).

## 2. His marble sheet (cells by label, R-T546-1)

His cover 'stairs and landings' **295.44 m2** = 164.54 of AREA cells (court 151.8, landings 5.1 + 6.2 + 1.44) +
**130.9 of count x length booked in the area column** (door steps 7.70, entrance steps 5 x 2.80 = 14.00, main 63 x 1.20,
inner 28 x 1.20). It is not an area. His lm total 29.87 and nr total 96 are skirting / stair-side pieces (T-574). This
task's cells: H36..H41, H16, H17 (m2), B x C of rows 36..41 and 16 (lm), B36..B41, B16 (nr); the rest is partitioned to
its owner and closes exactly.

## 3. Tables (ours - his; causes close exactly; % only where no HELD / SCOPE / UNIT cause)

| Group | m2 ours / his | lm ours / his | nr ours / his | Verdict proposal |
|---|---|---|---|---|
| Wet door marble thresholds (14) | 1.82 / - | 11.50 / - | 14 / - | ENGINE_RIGHT (owner rule; his omission) |
| Dry porcelain strips (8 + 2 HELD) | 1.250 / - | 7.70 / - | 10 / - | RULE_DIFFERENCE (scope; may sit in his room floors) |
| External doors: strip vs his 'door steps' | HELD 1.31 / 7.70 (length in area col) | HELD 6.80 / 7.70 | 6 / 6 | UNIT (m2); UNRESOLVED element (lm): possible ENGINE_OMISSION of EXT_STEP; count AGREE |
| Window sills (23 + W17 HELD) | 2.5614 / - | 29.53 / - | 24 / - | ENGINE_RIGHT on scope (UP-REVEAL-001), material UNKNOWN |
| Floor-glazing outside strips (4 + W03 HELD) | 0.408 / - | 5.10 / - | 6 / - | ENGINE_RIGHT on scope |
| Lift B6-07 (3) + B6-06 HELD 2.75 .. 13.98 | 1.5 / - | 3.0 / - | 3 / - | ENGINE_RIGHT on scope (T-475) |
| E1 steps | 5.3194 / 14.00 (length in area col) | - / 14.00 | 4 / 5 | m2 UNIT; lm ENGINE_OMISSION -11.20 (no step-lm line; printed 4 x 2.80) + RULE_DIFFERENCE -2.80 (his top step = our landing edge); nr -1 same cause |
| E1 landing | 5.1794 / 5.10 (+1.56 %) | - | - | ENGINE_RIGHT +0.08 (printed 1.40 x 3.70 = 5.18) + TOLERANCE -0.0006 |
| **Totals** | **18.0382 / 26.80** | **56.83 / 21.70** | **67 / 11** | % withheld |

Code closure: FIN.MARBLE.THRESHOLD 14/14 lines, LIFT_THRESHOLD 6/6, LIFT_SURROUND 3/3; ARCH.THRESHOLD 8 used, 16 named
not-this-element (T-325 s.3); ARCH.WINDOW_REVEAL 30 sill / strip lines used, 32 jamb-head reveal lines named.

## 4. Findings for the Lead (nothing valued here)

- F-T577-1 ENGINE_OMISSION: E1 carries no FIN.STAIR.STEP_LM line (printed 4 x 2.80 = 11.20 lm) while every other flight
  does.
- F-T577-2 UNRESOLVED / possible ENGINE_OMISSION: an EXT_STEP piece outside each external door; outside levels at the six
  doors are not established in a merged reading (his six pieces 7.70 lm; our strips 6.80 lm are a different element).
- F-T577-3 freelancer unit mix: 130.9 of his 295.44 'm2' are step / door-step lengths; the stair flights' share (109.2)
  has no reconciliation row yet (stair tread / step marble by unit) - proposed row.

## 5. Rule, tests, lessons row (proposed)

R-T577-1 (t577_rules.py): element first; one opening one piece; a number's unit is its own column label;
LENGTH_IN_AREA_COLUMN classed and never compared as m2 or lm; his lm = his count x his length cells; causes close
exactly; HELD amount 0 with a bound; % only where comparable. Tests `tests/t577_marble_reconcile` (30): fixture 3 doors
0.90 in 0.20 walls = 2.70 lm / 0.54 m2 / 3 nr, 2 windows 1.20 + 2 x 0.05 printed returns = 2.60 lm, mm, jamb width under
rotation 0/37/90/180/211 and mirror; adverse: m2 cell compared as lm refused, one opening on two plans refused, unprinted
return refused, missing width never 0, HELD with a value, VERIFIED, unnamed residual, piece twice / unused, partition
remainder; Alsenan pins (byte-identical, totals, partition, edited input stops the build, no workbook text).

Lessons row: | 2026-11-06 | a reference 'm2' total compared as an area when 44 % of it is count x length | the column
label was read for the total, not for each row's dimension cells | R-T577-1 (c): class every reference cell by its own
label and its row's dimension cells; a length in an area column closes his total with a UNIT cause, never compared |
tests/t577_marble_reconcile (fixture + m2-as-lm refused) | PROPOSED |
