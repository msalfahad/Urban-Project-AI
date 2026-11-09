# T-657 B10-03 neck concrete: the 36 HELD neck lines restated from the drawings

Worker 1 (lane S), 2026-11-09, branch `agents/task-T-657`. Research only: no engine module, candidate line, rule file or
method version changed; nothing released; wiring is T-661. ERS s.2-5, R-NECK-ENDS-1, Q-21 answer C, no-assumptions.

## Physical element and evidence (ERS s.2.1)

Neck = the column below the GF, from the footing TOP (the footing owns its depth) to the ground-beam / GF column base
(same datum). Re-read this run from the ST7757 PDF (Drive 'Alsenan chalet project', read-only; private copy only):

- ST p.9 note 1: excavation level not less than 1.5 m below the existing plot level (a MINIMUM). Footing schedule H for
  all 17 types re-read: equal to the T-205 input. Column FOUNDATION sizes re-read: equal to the T-205 sections.
- ST p.13 isolated-footing detail (single ground-beam row): dimension 'LESS THAN 2.5m' from the footing underside (top
  of the 5 cm screed; 5 + 2 + 10 cm stack below it) to the upper ground-beam / GF slab line. Second detail: '(When the
  level difference between upper ground beam and footing is more than 2.5m)' adds a lower ground-beam row.
- The structural set has one ground-beam plan with one row; no 'lower' beam is labelled anywhere in the dxf (and T-572 /
  T-350 found none drawn).

No sheet prints a founding or footing level, so no neck has both ends printed: 0 lines valued (R-T657-4).

## Method (owner manual method beside the drawing-derived method)

- Owner / freelancer manual method: one flat neck height (1.50 m, the note-1 number) x section. Not a drawn datum.
- Drawing-derived, low end (R-T572-2, unchanged): h >= top + 1.50 - 0.17 - H_max, smallest section.
- Drawing-derived, high end (NEW, R-T657-1): the drawn design is the single-row detail, so GB top - footing underside
  < 2.50 m and h <= 2.50 - H_min, largest section. Valid whichever line the 2.5 m dimension reaches at its top (it is
  the largest height). A deeper formation means the second detail + an undrawn lower beam row + engineering approval
  (Q-21 C: 'no change of founding level ... without engineering approval'): a design change, named beside, not in the
  drawn neck. Unsuitable soil is measured as extra excavation / approved fill (Q-21 C), not as longer necks.
- Lift FF necks (4): pit raft depth 'as per lift manufacturer' (D-43): R-T657-2, upper end open by name.

For a +0.95 neck the footing underside lies between -1.33 (note 1) and -1.55 (p.13): a 0.22 m band.

## Result (m3)

| | lines | low | high |
|---|---|---|---|
| Before: generic T-167 0.50 .. 2.50 m | 35 ranged + 1 blank | 3.075 | 15.375 (+ blank) |
| After: bounded as drawn | 32 | 8.7724 | 11.3460 |
| After: lift necks, lower only (D-43) | 4 | 0.9515 | open (D-43) |
| After: family | 36 | 9.7239 | not stateable (4 lift necks) |

Every line is accounted for once (`out/T657_NECK_LEDGER.json`: mark, position, footing, H, section, top, h low / high,
m3 low / high, status, bases). Every new bound lies inside the old generic range. The blank line (CN 17C5) now carries
0.0972 .. 0.1800.

Freelancer beside (family total already tracked by T-551): 8.805 m3 on his 34 necks, below the drawn family low 9.7239
(36 necks) and below the drawn low on his own count (T-572: 8.8695). Proposal: ENGINE_RIGHT on the low end (his flat
1.50 m is shorter than 2.28 - H for every main-house neck on a footing shallower than 0.78 m).

## For the Checker (re-measure)

1. ST p.13 'LESS THAN 2.5m': bottom tick at the footing underside, top tick at the slab / GB line; second-detail title.
2. Whether 'one ground-beam row drawn' makes R-T657-1 a drawn bound (the proposal) or only the drawn scenario.
3. Five necks by hand from the dxf / schedule: C11 10BA, C3 10CC, C9 10DA, C 10B7, CN 17C5.
4. Annex / CN tops (+0.25 vs +0.95, T-572 flags) do not change the high end (2.50 - H holds for either top).

## Lessons row (ERS s.7, proposed)

| 2026-11-09 | the neck upper end was left open (or generic 2.50 m) although the project's own typical footing details print a
single / two ground-beam condition | a printed conditional detail was read only as a picture, not as a level limit |
where the sheets print 'level difference < D_max' for the drawn single-row arrangement, the neck high end is D_max -
H_min; a deeper formation is a design change named beside; pit rafts of supplier depth stay open (every villa;
provenance T-657, R-T657-1 .. 4) | tests/t657_neck_ledger | PROPOSED |
