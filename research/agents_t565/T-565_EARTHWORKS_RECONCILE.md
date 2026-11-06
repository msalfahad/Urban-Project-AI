# T-565 B1 earthworks: V3.0.58 against the freelancer, by component

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPndFgNxWbFuRiHVfToF, branch
`agents/task-T-565`. Research only: no engine module, candidate line, released line, rule file or method version
changed; nothing released. Development villa, not an accuracy claim. ERS s.2 - 4 and s.7 applied; owner earthworks
sessions 2026-11-02 17:20 / 17:45 / 18:00 (150 mm lift OWNER-PROVISIONAL; 95 % Modified Proctor NOT adopted; reuse,
import and losses separate accounts), Q-21 C, R-T541-1, R-T551-1 .. 4.

## 0. Sources and run

- Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); lines = `research/agents_t507/out/
  LINE_INDEX_V3_0_57.json` (V3.0.58 moves FIN.WP.ROOF only, R-T507-1 (e)). Earthworks terms from the merged T-350 r2,
  T-484, T-497, T-320 files (sha-pinned by their own packages).
- Freelancer: Drive "Alsenan chalet project", the six workbooks (concrete + rebar, blockwork, floors / waterproofing /
  decor / marble, plaster, paint, aluminium). The concrete + rebar workbook was downloaded this run, decoded into
  `.work/private` only, sha256 equal to the B1 manifest (`ae608411`), every sheet re-read (values and formulas). The
  other five: the B1 census `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` keeps EVERY non-empty row of every
  sheet (885 rows; the Drive file sizes equal the manifest; for the concrete workbook the census row counts equal the
  re-read sheet by sheet, 8 / 8). The web-app report rows (`WEB_APP_ROWS.json`, 88 rows) were searched as well.
- Code: `t565_rules.py` (EARTHWORKS_RECONCILE_V1, R-T565-1 .. 4), `t565_alsenan.py` (build + private check) ->
  `out/T565_EARTHWORKS_RECONCILE.json` (engine figures, terms, search counts; no row of his).

## 1. The physical elements (ERS s.2.1) and units

| Element | Physical definition | Basis / unit |
|---|---|---|
| excavation | in-situ soil from EG (+-0.00, T-357 DERIVED) to the formation over the zone plan; working space only where printed | IN_SITU m3 |
| backfill | finished compacted soil returned to EG = excavation - every buried solid below EG, once by element id | COMPACTED m3 |
| displacement | the buried solids themselves (footing, neck, strap, beam, blinding, underlay) | SOLID m3 |
| disposal | in-situ soil leaving the site = E - B x k, k = compacted / in-situ dry density (sourced) | IN_SITU m3 |
| compaction | finished lifts (count) and formation footprints | nr / m2 |
| soil treatment | sprayed termiticide area | m2 |

Loose (bulked), compacted and in-situ m3 are never added or compared (R-T565-2); `E - B` is NOT a disposal quantity.

## 2. Freelancer side: no earthworks row (R-T565-1)

Keyword search (Arabic roots for excavation, backfill / filling, soil, levelling, compaction, transport, debris, sand,
termite, pesticide, site cleaning; English excavat / backfill / fill / earth / soil / compact / termite / disposal) over
every cell value and formula: **0 hits in 885 rows of the six workbooks**; the concrete workbook re-read this run: 0 hits
in 8 sheets (summary, footings, ground beams, walls + columns, beams, slabs, stairs, pool). His summary sheet totals only
plain concrete, RC families and steel tonnage. Web app: 3 'sand' rows, each read: material loads under the tiling,
plaster and black-structure bands (unit 'qty', no m3, no plan): MATERIAL_LOAD_NOT_EARTHWORKS.

So his total for every earthworks component is **NO_ROW** (not 0). The split "his total minus ours" into datum,
working space, buried deductions, bulking, HELD or ENGINE_WRONG does not exist: every cause is NOT_APPLICABLE because he
measured nothing. No percentage is stated.

## 3. Component table (engine V3.0.58; his NO_ROW on every row)

| Family / component | Lines | Valued | Held range | Held blank | His | Class |
|---|---|---|---|---|---|---|
| B1-02 excavation, pits 24 (S01 ESTIMATED, plan 124.649555 m2 x 1.67) | 1 | 208.164757 | - | - | NO_ROW | NOT_COMPARABLE |
| B1-02 excavation, pool envelope (printed -1.50) | 1 | 17.776576 | - | - | NO_ROW | NOT_COMPARABLE |
| B1-02 ext main GB trench (T-497 ownership) | 1 | - | 1.069269 .. 1.176467 | - | NO_ROW | NOT_COMPARABLE |
| B1-02 F10 + F outline (S02 scenarios) | 1 | - | 7.264500 .. 8.391750 | - | NO_ROW | NOT_COMPARABLE |
| B1-02 FF, annex, court, straps, boundary, D-33, ZERO, lower GB row | 8 | - | - | 8 | NO_ROW | NOT_COMPARABLE |
| **B1-02 total (IN_SITU m3)** | **12** | **225.941333** | **8.333769 .. 9.568217** | **8** | NO_ROW | |
| B1-03 backfill, pits 24 | 1 | - | 119.963335 .. 128.643547 | - | NO_ROW | NOT_COMPARABLE |
| B1-03 pool, ext trench, other trenches, F10F, FF, Z2 | 6 | - | - | 6 | NO_ROW | NOT_COMPARABLE |
| **B1-03 total (COMPACTED m3)** | **7** | none | **119.963335 .. 128.643547** | **6** | NO_ROW | |
| **B1-04 disposal (IN_SITU m3)** | **1** | none | none | **1** (densities, Z2 draw, loss_reuse) | NO_ROW | NOT_COMPARABLE |
| compaction layers, pits zone (depth 1.57 / 0.15 OWNER-PROVISIONAL) | info | 11 nr | | | NO_ROW | NOT_COMPARABLE |
| formation footprints pits + pool | info | 136.500606 m2 | | | NO_ROW | NOT_COMPARABLE |
| B1-05 soil treatment / anti-termite | 0 | NOT_IN_DRAWN_SCOPE (T-354, 31 sheets) | | | NO_ROW | AGREE_ABSENT |

Every family total re-adds exactly from its zone lines (asserted, 6 dp); a family with no valued or no ranged line
reports none, never 0 (the T-512 defect class). Pits backfill closes at both ends: 208.164757 - 71.925255 (blinding
12.464956 + underlay 7.542559 + footings 51.917740, VERIFIED) - 16.276167 / 7.595955 (necks 5.154 + C8 0.24 .. 0.27 +
strap ends 0.179618 + ground-beam solids 2.022337 .. 10.672549) = 119.963335 / 128.643547 = the line.

Engine uncertainty beside (information for the 12-13 Nov statement): pits excavation S01 -0.10 / +0.10 m = 195.699801 /
220.629712; printed-minimum bound 186.974333.

## 4. Buried volume owned once by element id (R-T565-4; acceptance)

Each buried concrete line of V3.0.58 is split over the excavation zones by geometry; the shares re-add exactly to the
line (asserted by `ownership`).

| Line family | Line m3 | Pits 24 (valued backfill) | Held zones | Check |
|---|---|---|---|---|
| footings, 25 valued lines | 64.304000 | 51.917740 | pool interface 1.001260 (F8 1.615967 m2 x 0.50 + F4 0.483190 x 0.40, F-T350R2-2); FF lift raft 11.385000 (FF zone, blank) | pits share = the T-350 r2 term 51.917740 (independent route: candidate lines vs T-320 ledger) |
| footing F10 + F (held line) | 2.176 .. 2.275 | 0 | F10F zone | own zone |
| blinding, 24 pits | 12.734438 | 12.464956 | 0.269482 under the pool envelope (2.694820 m2; the under-pool band, held) | per-pit envelope parts 2.695361 m2 = line part + 0.000541 m2 F8 / FN overlap counted once |
| straps SB1 / SB2 / SB3 | 3.390500 | 0.179618 (5 ends) | F10F 0.035 (SB1 end); TRENCH-STRAPS 3.175882 (blank) | per strap closes |
| necks, 36 lines (all HELD in concrete) | 3.075 .. 15.375 | 30 necks (29 at S01 5.154 + C8 0.24 .. 0.27) | FF 4, F10F 2 | count closes 36 = 30 + 4 + 2 |
| underlay (WP family) | 109.85 m2 | 7.542559 (107.750843 m2 x 0.07) | F8 / F4 in envelope 2.099157 m2 | 109.85 = 109.99 - FN / F9 notch 0.14 m2 |

Findings: (a) the T-320 ledger bills the FN / F9 notch 0.042 m3 inside FN; the candidate FN line (0.258) is net of it
and T-350 r2 nets it once: no double count. (b) The candidate footing lines and the T-320 pit groups sit in two frames
(offset 75.968 / 14.448 m, one pair 1 mm off) and 2 of the 24 pits carry another DXF handle (F11, F6: outline vs
insertion entity): the join is by mark + position, never by handle alone. (c) Ground beams are split at zone level
only (T-484 categories); the per-element split of the 61 GB lines over the trench zones is not done here (the trench
zones are held blank).

## 5. Who is right (verdict proposals)

- SCOPE, every B1-02 / B1-03 / B1-04 component: **ENGINE_RIGHT** that the work exists (ST p.9 note 1 founding depth not
  less than 1.50 m below the plot level; p.13 compacted fill / compacted soil; p.13 / p.14 10 cm blinding + 5 cm screed
  + membrane under footings): the freelancer's BOQ omits a drawn category. QUANTITY: **UNRESOLVED / NOT_COMPARABLE** (no
  row of his; no figure of his can be inferred: his buried-structure rows are concrete, not earthworks).
- B1-05 soil treatment: **AGREE_ABSENT** (NOT_IN_DRAWN_SCOPE on both sides).
- No ENGINE_WRONG found; no quantity changed; no owner question (ERS s.2.7 not met: nothing is contradictory or
  safety-critical; the held causes are already on the designer / owner lists: OQ-13 working space, D-33 / D-35, D-43,
  Q-31 C, S06 / D-14, densities).

## 6. Rules, tests, lessons row (proposed)

R-T565-1 (NO_ROW never 0, never a percentage; scope verdict separate), R-T565-2 (one basis per sum / comparison),
R-T565-3 (valued / held apart, absent parts none, exact closure), R-T565-4 (buried volume owned once by element id,
join by mark + position). `tests/t565_earthworks_reconcile` (20): hand villa E565 (pad 2.00 x 2.00 x 0.60 on blinding
0.10, NGL 1.20 above the pad base: excavation 5.200, backfill 5.200 - 2.400 - 0.400 - 0.054 = 2.346, displacement
2.854; mirror / rotation; working space only when printed 8.788), adverse (bulked vs in-place, compacted + in-situ in
one sum, buried volume deducted twice / in two zones / in none, NO_ROW summed or as 0, mm as m, disposal without a
sourced k), development villa from committed files, and the private re-read.

Lessons row (ERS s.7): | 2026-11-06 | earthworks had no engine-vs-freelancer statement section although three families
carry quantities | a benchmark with no row was left uncompared instead of being stated NO_ROW with its search evidence |
a missing benchmark row is NO_ROW with the files / rows searched, never 0, never a percentage; the scope verdict
(drawing evidence that the work exists) is separate from the quantity comparison; buried volumes are owned once by
element id joined by mark + position (every villa; T-565, R-T565-1 .. 4) | tests/t565_earthworks_reconcile | PROPOSED |

## 7. Checker re-measure list

- Re-run `test_private_workbook_has_no_earthworks_row` with the workbook at `.work/private/concrete_rebar.xlsx`.
- Footing ownership: F8 and F4 envelope footprints (1.615967 / 0.483190 m2) and the FF raft line 11.385.
- Blinding 0.269482 under the pool envelope vs the held under-pool band (0.458211 m3, F-T350R2-2).
