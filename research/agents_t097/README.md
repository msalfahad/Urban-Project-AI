# T-097: concrete ledger V3 (beam binding V2 + rings + upstands + neck-only column types), measured on the development villa

Worker 1, 2026-10-20. New method version `engine/source/concrete_ledger_v3.py` (CONCRETE_LEDGER_V3). Not wired into a
released method: only `research/agents_t097/run_v3.py` and `tests/t097_concrete_ledger_v3/` call it. No frozen file and
no existing method file changed. Development reference, not an accuracy claim.

## What the version does

V3 = CONCRETE_LEDGER_V2 (T-060: strip guard, curved strips; its boundary-wall band and pool lines are HELD by owner
Q-12 / Q-19 / Q-26) plus:

1. **Beams re-bound by BEAM_BINDING_V2 (T-085).** For every slab and ground-beam plan the route's own beam pipeline is
   replayed from the route's records (edge layers, column boxes, widths, the same CAD healing, `beam_bands`). The V1
   replay must reproduce the route's bands, marks and inherited sections exactly, else the sheet keeps its V1 items
   (REPLAY_MISMATCH, tested). Then V2: a column outline linked by its leader to a planted-column label and lying inside
   the beam width no longer cuts the beam; a mark is direction-tested against arc bands. The beam items are rebuilt by
   the route's own `generic_route.items_from` on that sheet record (same conventions, same depth reading, same held
   reasons; an unlabelled span across a support stays HELD, owner Q-16 A). Only CONCRETE beam items are replaced.
   Safety check: `items_from` on the unchanged records must reproduce every route item, and every non-beam concrete
   item of the rebuild must equal the route's (side effects: 0 on every run here).
2. **Ring beams round circular openings (owner Q-44 A).** `ring_beams` on the drawn concentric faces; a ring with its
   own printed mark, or with an owner rule passed by the caller (`ring_rule`: family, mark, storey, basis), becomes one
   line (net annulus x H, the route's BEAM_DEPTH_READING) and replaces the items of its arc-band pieces. A ring without
   either is listed HELD with its annulus; never 0.
3. **Upstands from printed sections.** Section title -> nearest dimensioned outline above it (mutual) -> its cut line
   found once on the plans -> the crossed span at the printed width: w x h x clear span. A drawn upstand whose size is
   not printed is a HELD line (UPSTAND_HELD), never 0. Outlines are read in world coordinates (a polyline mirrored by
   its extrusion is read correctly; found by the mirrored fixture).
4. **Neck-only column types typed as text (T-075).** A column-plan occurrence of a type whose every level above the
   foundation is struck out on the schedule leaves the held list as NOT_PRESENT (listed with its evidence); its neck
   stays HELD on the founding datum (owner Q-21 C) and gains the printed section.

## Development villa (structural DXF from Drive "Alsenan chalet project", sha256 9f9d1179...38079 = manifest)

Run: `python3 -I research/agents_t097/run_v3.py <ST dxf> OUT.json --ring-rule "BEAM:B4:1F:owner Q-44 A"` (route G,
conventions V6, completeness on). All four plan sheets replayed identically (2F, 1F, GF, ground beams); side effects 0.
Structural lines 949 -> 943: 930 unchanged, 2 changed, 17 removed, 11 added.

### Beam concrete (key CONC.BEAM, freelancer 65.97 m3)

| | Released m3 | Released lines | Held lines |
|---|---|---|---|
| Route (V1) | 64.82 | 112 | 24 |
| V3 | **68.84** | 116 | **18** |

Released +4.018 m3 (engine vs freelancer from -1.15 m3 / -1.7 % to +2.87 m3 / +4.4 %, with 18 lines still HELD, so the
scoreboard key stays HELD: not compared). Line by line, each hand-checked from the printed / drawn sizes:

| Line | V1 | V3 | Hand |
|---|---|---|---|
| GF B26 (0.65 x 0.85) | 3.104 released + 0.683 held (split at the 'P.C 20x50' planted column) | one span 7.0675 m: 3.905 | 7.0675 x 0.65 x 0.85 = 3.905 |
| GF B27 (0.90 x 0.85) | 2.503 released + 0.841 held (split at 'P.C 20x70') | one span 4.9505 m: 3.787 | 4.9505 x 0.90 x 0.85 = 3.787 |
| GF B7 strip (0.20 x 0.75) | held (mark AMBIGUOUS with an arc) | 0.255 | 1.70 x 0.20 x 0.75 = 0.255 |
| GF B7 arc piece BAND0053 | held | 0.066 | 0.08755 m2 x 0.75 |
| GF CB8 junction with the longer B27 | 0.776 | 0.774 | -0.0026 (junction square now B27's) |
| 1F ring with printed B4 (0.20 x 0.50) | 2 arc pieces released 0.129 + 0.152, 2 held | one line 0.755 | annulus pi (2.411^2 - 2.211^2) = 2.904 m2; 1.511 m2 not in straight beams / columns x 0.50 |
| 1F ring, inner face a full circle, no mark | no band at all (silent) | 0.900 (owner Q-44 A rule: B4) | 1.799 m2 x 0.50 |
| GF upstand on the B20 span, section A-A | absent | 0.120 | 0.20 x 0.20 x 3.00 |
| 1F upstand on the B23 span, section B-B | absent | 0.120 | 0.20 x 0.20 x 3.00 |

Sum: +0.801 + 1.285 + 0.255 + 0.066 - 0.003 + (0.755 - 0.281) + 0.900 + 0.240 = **+4.018 m3** (T-085 estimated
+4.30 m3: the difference is the 0.281 m3 of the two ring-1 arc pieces that V1 already released, which T-085 counted as
"in no total"; the ring line replaces them, so they are not added twice).

The 24 held spans of the T-043 hand table: 6 resolved (B26 and B27 pieces, B7 strip, BAND0053, the two ring-arc
pieces inside the B4 ring line), 18 still HELD with the route's reasons: B23 / B20 west spans (section printed, the
section prints no mark; T-043 matched them by bars: a section-to-span binding rule is a follow-up, 1.0125 + 0.900 m3
proposed), CB10 x2 (printed 0.25 vs drawn 0.30), 1F outer strip, the four 0.20 strips north of B23 / B20, CB3 / B3 two
marks, B24 east span, 1F B2 piece, four 2F unlabelled spans, two 1F facade strips. Sections C-C (cut line on two plans)
and D-D (two segments carry the letter on one plan: AMBIGUOUS) stay HELD, as in T-085.

### Columns and necks

5 CN column lines (held TYPE_NOT_IN_SCHEDULE) leave as NOT_PRESENT: the schedule row CN typed as text has GF / 1F / 2F
struck out (freelancer: 0 CN columns, agree). 6 CN neck lines stay HELD, now with the printed 0.30 x 0.30 section
(0.540 m2 together); freelancer 0.810 m3 rests on an unprinted 1.50 m height (owner Q-21 C). CONC.COLUMN held lines
118 -> 113, released 0 (unchanged).

### Concrete total

Scored lines (a key with any held line is HELD): route 92.77 vs 111.81 m3 on 3 keys (footings, pool, stairs + domes).
V3 inherits the V2 ledger's holds (footing band MEMBER_TYPE_PENDING, owner Q-12; pool walls / floor not printed beside
the pool, Q-19 / Q-26), so only stairs + domes stays compared: 12.01 vs 21.83 m3. Released over all concrete keys:
route 236.27 m3, V3 229.57 m3 (beams +4.02, footing band -7.22 held, pool -3.50 held); freelancer 399.49 m3 over the
same eight keys (most of the gap is held, not released: columns, blinding, ground beams).

## Hand fixture (not the development villa): tests/t097_concrete_ledger_v3

Synthetic villas from tools/synthetic_villa, seed 3 (mm) and seed 7 (m), seed 3 also mirrored, with four cases drawn
from the design numbers: a planted column 'P.C 20x60' / 'P.C 25x50' with landing line and leader to a circle (V3 one
span 4.50 x 0.20 x 0.50 = 0.450 m3 / 4.95 x 0.25 x 0.50 = 0.619 m3), a ring with printed mark and a ring with a full
circle and no mark (pi (1.20^2 - 1.00^2) x 0.50 = 0.691 m3; HELD without a rule), SECTION A-A with an upstand 0.10 x
0.15 (x 4.35 = 0.06525 m3, x 3.975 = 0.059625 m3), and the generator's own untagged span and unscheduled beam type
(stay HELD). Adversarial: label without leader (nothing changes), upstand height not printed (HELD, no number), replay
mismatch (sheet kept), ring rule without basis (refused), neck rule on hand records. 24 tests.

## Not done / follow-ups

- Beam reinforcement items stay the route's (they still name the V1 pieces BAND0047.1 / .2, BAND0048.1 / .2): a rebar
  follow-up should rebuild them from the same V2 records.
- The section-to-span binding (B23 / B20 west spans by the section's printed bars) is not in BEAM_BINDING_V2.
- The ring basis polygon (256 segments a quarter) leaves the net plan under the exact annulus by < 1e-4 m2.
- Wiring V3 into a released method (and the typed project data file T-064) is a later version.
