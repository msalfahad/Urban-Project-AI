# T-371 erratum (written by T-374 r2; the merged T-371 files are NOT edited)

Worker 1 (lane S), 2026-10-31, T-374 r2. Applies to the merged T-371 bar-shape census
(`research/agents_t371/T371_MATRIX.csv`, `T371_SUMMARY.json`, `T-371_BAR_SHAPE_CENSUS.md`, merged 8f2b0354). The Lead /
lane I applies it; nothing in those files is changed here. Drawings are named by sheet only.

## E-1 FTG-BOT-MESH: SCHEDULABLE_NOW was wrong (blind spot: unresolved Checker downgrade record)

- **Matrix row**: `FTG-BOT-MESH, ISOLATED_FOOTING, ... status SCHEDULABLE_NOW, candidate_lines 51` (body / ends
  'PRINTED_TYPICAL: straight', p.13 TYP. DETAIL OF ISOLATED FOOTING).
- **Record it missed**: `DG-a97ec2ea66e02194` (verdicts/V3.0.20 .. V3.0.29 DOWNGRADES.json on agents/control, state HELD,
  resolved false, basis label UNSUPPORTED BASIS; re-issue of DG-eba2b0b8c7397b9a (V3.0.19), DG-d0012905259e345c
  (V3.0.18), DG-1b0eacce2d68f2a5 (V3.0.17), same 38 line ids). Its basis: the 38 count-printed footing mesh lines
  (BOTTOM_LONG + BOTTOM_SHORT) run side - 2 x 70 mm, i.e. the p.8 note 22 MINIMUM cover used as the bar-end position,
  with a drawn boxed-bar leg of unprinted diameter between bar end and face (p.13): the weights are UPPER values with no
  printed lower bound.
- **Why it matters for a shape census**: the shape (straight) is right; but SCHEDULABLE_NOW was used downstream (T-374)
  as "a cut length can be scheduled now". A cutting length is exactly the quantity the record says has no supported
  basis. The census never read the downgrade records.
- **Also the 10 '/m' footing lines** (F8, F12, F13, F14, FF; BOUNDED_EXPOSURE, count Q-71 readings) carry the same
  basis in their own formula and cover text ("n x (side - 2 x 70 mm)", cover "MINIMUM 70 mm ... note 22"); they are not
  in the record's line list. T-374 r2 books them HELD_SAME_BASIS (R-T374-6b) and proposes the record's extension to the
  Checker (DGP-T374-FTGM). The 3 remaining lines were already HELD (two-mark footing, clipped outlines).
- **Corrected status**: FTG-BOT-MESH = SHAPE straight, **CUT LENGTH HELD by DG-a97ec2ea66e02194** (not schedulable
  now) until the record is resolved (printed bar length, or the boxed-bar diameter and end position).

## E-2 COL-TWIST-EXTRA (F-T374-1, already Checker-confirmed 2026-10-30 21:08)

p.15 TYP. DETAIL OF TWISTED COLUMN, both elevations: the 4 extra bars end at the top in a short inward inclined bend,
no leg length, no bend diameter. Status GAP (G-T371-0), not SCHEDULABLE_NOW; 12.642 kg released net carried by name.

## Corrected count

| | populations | lines |
|---|---|---|
| T-371 as merged | 7 | 442 |
| after E-2 | 6 | 440 |
| after E-1 (this erratum) | **5** (COL-MAIN-BODY, CB-BOTTOM, CB-SUPPORT-TOP, GB-MAIN, SLAB-TEMP) | **389** |

Of the 389, the lines that actually carry a schedulable straight bar are 157 (125 exact + 32 run parts); the rest are
HELD / HELD_DEFINED / BOUNDED_NO_ROW / NA (route G superseded), as T-374 lists them line by line.

## Rule for the census (proposed, every villa)

A population is SCHEDULABLE_NOW only if, in addition to a printed straight shape, **no line of it sits under an
unresolved Checker downgrade record** (every verdicts/V3.0.x/DOWNGRADES.json bound to the candidate) and no line carries
a record's stated unsupported basis. Test in T-374: `test_line_under_an_unresolved_downgrade_record_is_never_scheduled`.
