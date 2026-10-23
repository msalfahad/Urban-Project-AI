# T-225: blockwork resolution 1/4: sources, three-way reconciliation, wall register v1, before-coverage

Worker 2, 2026-10-23 15:46 - 16:10 UTC, lane A, gate 1 (owner programme BLOCKWORK_RESOLUTION_PROGRAMME.md, 15:45).
Base: working head 41847bff. **No quantity changed**: every figure is read from merged ledgers (T-108 r2
MASONRY_AREA_V1 r2 01eeafd0, T-143, T-175, T-176 41847bff, T-215 8a9b4b48). Released default unchanged (V2.9 + route G).
Development villa; not an accuracy claim. Drawings and workbooks are cited by Drive folder and title only.
ERS: read; s.2 (define, evidence hierarchy, reconstruct, reconcile in units, status), s.3 (installed vs procurement,
build before deduct, geometric scope before numbers), s.4 (rule + test) applied.

## 1. The physical element and the sources (owner items 1, 2)

Element: non-structural block walls of the three storeys (black cement / white light-weight block), measured as net
installed m2 per wall = physical length (Q-69 B) x height to the underside of the member above (Q-60 A) - the full
area of every actual opening in built masonry (Q-73); m3 = net x drawn thickness; procurement (units, waste, mortar)
is a separate output (T-176). Sources found on Drive "Alsenan chalet project" and in the repository (SOURCES.csv):

| Id | Source | Provenance class | Blockwork content | Use |
|---|---|---|---|---|
| S1 | المبانى.xlsx (sha 873308bb, verified this run = manifest) | HUMAN FREELANCER BOQ | sheet الكميات rows 14-227: count x length x height per row; sections external / internal 15 cm / internal 20 cm by floor; cover totals 559.80 + 617.25 + 83.64 = 1,260.69 m2 | comparison only |
| S2 | released V2.9 + route G, pinned run A (T-165), **reproduced this run** on 41847bff (BOQ_LINES.csv b96185d4, 1,455 lines) | OLDER AUTOMATED TAKEOFF | ARCH.WALL_RUN lm by floor x thickness, 7 lines (216.931 lm released = both faces drawn; band run 337.849 lm); 21 panel / volume / MAS.BLOCK lines BLOCKED_RFI (no masonry height): **no block m2 at all** | comparison only |
| S3 | MASONRY_AREA_V1 r2 + T-175 / T-176 / T-215 | CURRENT ENGINE (opt-in) | 74 wall rows | the register's only quantity source |
| S4 | Alsenan Chalet_by_category.xlsx / .pdf ("Cost By Category") | OWNER COST RECORD, not a takeoff | shell-stage blockwork: about 22 thousand blocks (qty 21,500, block type not stated) and white block 90 m3 (pdf p.5) | NOT COMPARABLE with m2 (procurement units, no floor / thickness / type); later cross-check for T-176 only |
| S5 | P7757.dxf (ab54dd55), ST7757 dxf.dxf (9f9d1179), ST7757.pdf, arch sheets 09 / 10 | PROJECT DRAWINGS | evidence, not a quantity source | evidence per wall |
| S6 | the five other freelancer workbooks | HUMAN FREELANCER (other trades) | no blockwork line (every non-empty row searched) | none |

No automated **workbook** exists on Drive: the only older automated blockwork output is run A (S2). The freelancer and
the automated sources are never mixed: each has its own column. FREELANCER_BLK_LINES.csv lists every freelancer row
with its cell reference (B / C / D / H of the row) and scope class; FREELANCER_BLK_TOTALS.csv his total cells.
Found in his sheet: H74 = D75 x C74 x B74 (reads the next row's height; both 3.45, no numeric effect); the 20 cm section
is the same four rows on every floor (rows 203-206 = 208-211 = 213-216 in length, 8.20 m), and its 9.84 m2 of
deductions is not split by floor (rows 222-223).

## 2. Three-way reconciliation (owner item 2), in units

Like-for-like is possible on almost nothing, and that is the finding: the three sources measure different scopes.

- **Freelancer vs engine** (THREE_WAY_BY_FLOOR_SECTION.csv): his sections are external / internal 15 / internal 20 per
  floor; he prints no thickness for external walls and never splits black / white; one height per floor and zone
  (GF 4.00, annex 3.50, 1F 3.70 / 3.45, 2F 3.45 / 3.70) against Q-60 A member-by-member heights (RULE_DIFFERENCE,
  ENGINE_RIGHT under the owner's rule, T-143); his 15 cm section also carries the fence (row 150, 74.40 m2) and three
  parapet rows (172 / 177 / 178, 172.93 m2), and his 1F external section the "projections" row 78 (41.25 m2, no wall
  run): scopes the engine rows do not hold (Q-65 C, T-103 / T-144), named, never added or subtracted.

| Floor / his section | His length (sum B x C) | Engine length | d | Engine held length | His gross | Engine gross (known) | Like for like |
|---|---|---|---|---|---|---|---|
| GF external | 78.550 | 75.543 | -3.007 m | 7.545 | 300.875 | 250.058 | NO (held) |
| GF internal 15 | 47.530 | 39.313 | -8.217 m | 1.525 | 181.720 | 152.025 | NO |
| GF internal 20 | 8.200 | 15.000 | +6.800 m | 2.650 | 32.800 | 49.707 | NO |
| 1F external | 54.970 | 50.401 | -4.569 m | 6.899 | 199.651 | 155.467 | NO |
| 1F internal 15 | 57.140 | 56.736 | -0.404 m | 10.719 | 211.418 | 179.490 | NO |
| 1F internal 20 | 8.200 | 9.620 | +1.420 m | 0 | 30.340 | 35.221 | length only |
| 2F external | 27.900 | 26.850 | -1.050 m | 4.451 | 96.255 | 79.509 | NO |
| 2F internal 15 | 3.000 | 3.000 | 0.000 m | 0 | 11.100 | 11.400 | length only (gross +0.300 = height 3.80 vs 3.70, T-108 reconciled to 0) |
| 2F internal 20 | 8.200 | 9.750 | +1.550 m | 1.246 | 30.340 | 32.317 | NO |

  Verdict proposals: GF internal 20 +6.800 m ENGINE_RIGHT on thickness (the plans draw and print 0.20 for the annex WC
  wall, the wall under the reception stair and the lift-lobby walls; T-143 finding 4); 1F / 2F internal 20 +1.420 /
  +1.550 m UNRESOLVED (his rows are one GF row set copied to 1F and 2F; which walls it covers is his split, never his
  number); 2F internal 15: length FREELANCER_RIGHT = ENGINE (3.00 m), height RULE_DIFFERENCE (T-108 s.3, residual 0).
  External and internal 15 cm: not like for like while held length remains (held is missing, not 0).
- **Older automated (run A) vs engine** (THREE_WAY_BY_FLOOR_THICKNESS_TYPE.csv): run A has lengths only; its block m2
  is BLOCKED_RFI on every line (MASONRY_HEIGHT_NOT_IN_THE_DRAWING), so **m2 is NOT COMPARABLE** (held is not 0) and
  black / white is NOT COMPARABLE (run A has no type). **Length, reconciled band by band** (run A's ARCH_WALLS bands
  carry the same band ids as the engine's V2 runs; RUN_A_VS_ENGINE_BY_BAND.csv, RUN_A_VS_ENGINE_BY_FLOOR_THICKNESS.csv):

  | Floor / t | Run A band gross | Engine V2 arch run | d | = columns run A measures through | + remainder | Run A both faces (released) | Engine physical | openings the engine keeps in the run (Q-73) | residual |
  |---|---|---|---|---|---|---|---|---|---|
  | GF 0.15 | 39.078 | 37.788 | +1.289 | 1.090 | +0.200 | 30.335 | 37.788 | 5.997 | 1.457 |
  | GF 0.20 | 124.975 | 96.775 | +28.200 | 11.160 | +17.040 | 66.704 | 90.443 | 21.210 | 2.529 |
  | GF 0.40 | 1.400 | 0.600 | +0.800 | 0.800 | 0.000 | 0.600 | 0.600 | 0 | 0 |
  | 1F 0.15 | 56.467 | 56.736 | -0.268 | 1.700 | -1.968 | 44.260 | 56.736 | 10.100 | 2.376 |
  | 1F 0.20 | 72.779 | 63.599 | +9.180 | 8.817 | +0.362 | 44.032 | 60.020 | 14.207 | 1.781 |
  | 2F 0.15 | 10.700 | 10.900 | -0.200 | 0 | -0.200 | 8.700 | 10.900 | 1.800 | 0.400 |
  | 2F 0.20 | 32.450 | 28.700 | +3.750 | 3.500 | +0.250 | 22.300 | 28.700 | 5.900 | 0.500 |

  Causes: (i) run A measures each band THROUGH the columns standing in it (27.067 m in all); the physical run stops at
  the column faces (a column is concrete, not block: Q-69 B, T-125 verified): ENGINE_RIGHT for block length; (ii) GF
  0.20 remainder 17.040 m: band WB-FL0007-FL0008 alone 13.270 m (run A's band is one 17.57 m collinear line joining the
  two drawn pieces GF-W02 1.65 + GF-W03 2.65 m across a stretch with no wall faces, its own both-faces length 4.15 m
  confirms; ENGINE_RIGHT), WB-FL0001-FL0002 1.650 and WB-FL0017-FL0018 1.600 m (same kind), 0.520 m end conventions;
  (iii) the 0.15 m remainders -1.968 .. +0.200 m are end conventions (the V2 stem runs to the face of the wall it meets,
  run A's band stops at the band end), within T-125's verified convention. Run A's *released* length (both faces drawn,
  216.931 lm) is shorter than the engine's physical length by the openings the engine keeps in the run (Q-73 deducts
  their area later) plus a residual of 0 .. 2.529 m per floor and thickness (junction pieces and one-face-drawn
  stretches): named, UNRESOLVED at piece level, for the independent census T-017.
- **100 mm**: no 100 mm wall in the engine census, the freelancer's sheet or run A (a count of 0 walls, not a quantity).

## 3. Why established gross - deductions is not the net (owner item 6): reproduced wall by wall

GAP_RECONSTRUCTION.csv (computed by `register_v1.gap` from T108_BY_WALL.csv, not from the main chat's trace):

| Type / t | Established gross | All deductions | Established net | Gap | = A gross with net HELD | - B their deductions | - C deductions on HELD-gross walls |
|---|---|---|---|---|---|---|---|
| BLACK 0.15 | 215.721 | 29.920 | 182.337 | **3.464** | 1F-W14 + 1F-W15 16.223 | 0 | GF-W24 1.760, GF-W27 1.760, 1F-W11 1.760, 1F-W13 3.960, 1F-W16 1.760, 1F-W17 1.760 = 12.760 (residual 0.001 rounding) |
| BLACK 0.20 | 125.876 | 6.160 | 107.715 | **12.001** | 1F-W07 11.321 + 2F-W00 6.840 | 1F-W07 1.980 | GF-W08 2.200 + 2F-W05 1.980 |
| WHITE 0.15 | 0 | 2.200 | 0 | -2.200 | - | - | 2F-W03 2.200 |
| WHITE 0.20 | 225.654 | 27.565 | 47.358 | 150.731 | GF-W15, GF-W16, 1F-W00, 1F-W06, 1F-W10 (176.096) | 8.285 | 17.080 on 7 walls |

Both owner figures are reproduced exactly (the main chat's "9.341 for 1F-W07" is its gross 11.321 less its own 1.980).
**Rule R-T225-1 (any villa; provenance Q-73 + WORKFLOW_CONTROLS s.5):** a deduction belongs to its host wall and
carries that wall's net status; a net total per status sums (gross - deductions) only over walls whose net has that
status; deductions booked on a wall whose gross or net is HELD are reported in the HELD scope and never subtracted from
an established gross or net. "Established gross - all deductions" mixes statuses and is never reported as a net.

## 4. Wall register v1 (owner items 6, 7)

BLOCKWORK_WALL_REGISTER_V1.csv: 74 rows (one per T-108 r2 wall row; 1F-W14 + 1F-W15 is one physical run), every
programme s.5 column: wall id, floor, black / white (with its own class), thickness, length (+ held length, class),
weighted height, gross, deductions, openings in the run, net, net bounds, m3, evidence (Drive title of the plan / ST
file + the V2 run id, the member above each piece with its depth and status, storey heights, the hosted openings, the
type source), calculation, owner status class (from the net), held cause class + exact missing item + next package +
smallest held quantity, D-12 flag (m3 only), T-176 products and units, and T-215's closed ends (merged, **not applied**:
v1 equals T-108 r2 to 0.001 m2 per floor x thickness x type, test). `register_v1.py` holds the mappings: DRAWING-CONFIRMED
-> SOURCE-SUPPORTED PENDING INDEPENDENT CHECK, ASSUMED — OWNER-APPROVED -> PROJECT-SPECIFIC, HELD / UNKNOWN -> HELD;
OWNER DECISION REQUIRED is never produced by mapping (none in v1).

## 5. Before-coverage (owner item 9, before) by floor x thickness x type (BEFORE_COVERAGE.csv)

| Floor | t | Type | Walls | Net SOURCE-SUPPORTED | Net PROJECT-SPECIFIC | Net VERIFIED | Walls net HELD | Gross HELD figure (not a quantity) |
|---|---|---|---|---|---|---|---|---|
| GF | 0.15 | BLACK | 16 | 51.026 | 32.632 | 0 | 6 | 60.887 |
| GF | 0.20 | BLACK | 8 | 62.155 | 0 | 0 | 7 | 81.882 |
| GF | 0.20 | WHITE | 14 | 4.459 | 5.590 | 0 | 11 | 95.693 |
| GF | 0.20 / 0.40 | - | 2 | 0 | 0 | 0 | 2 | 0 (1.500 m held length) |
| 1F | 0.15 | BLACK | 13 | 52.306 | 36.733 | 0 | 7 | 66.307 |
| 1F | 0.20 | BLACK | 4 | 23.900 | 0 | 0 | 1 | 0 |
| 1F | 0.20 | WHITE | 8 | 15.833 | 0 | 0 | 5 | 11.324 |
| 2F | 0.15 | BLACK | 1 | 0 | 9.640 | 0 | 0 | 0 |
| 2F | 0.15 | WHITE | 1 | 0 | 0 | 0 | 1 | 27.993 |
| 2F | 0.20 | BLACK | 4 | 21.660 | 0 | 0 | 2 | 3.817 |
| 2F | 0.20 | WHITE | 3 | 21.476 | 0 | 0 | 2 | 30.040 |
| **All** | | | **74** | **252.817** | **84.595** | **0** | **44** | **377.943** |

Held causes (44 walls): annex datum Q-54 B 9 (113.118 m2 held gross figure) -> T-227; beam depth / register conflict 10
(118.007) -> T-226; held opening 12 (54.412 on held-gross walls; the other 8 hold only their net) -> T-227 / T-222;
no member drawn above 6 (49.035) -> T-226 / T-227; lift tie beam ST p.8 note 19 4 (43.371) -> T-227; no wall band /
member bound 3 (1.600 m held length) -> T-227. Independently VERIFIED net: 0 m2 on 0 walls.

## 6. Checker: what to re-measure (Gate A)

1. Re-add the register: per floor x thickness x type, gross / deductions / net by class = T108_BY_WALL.csv (test
   `test_register_sums_equal_t108_r2`), and the 3.464 / 12.001 gaps wall by wall from T108_BY_WALL.csv yourself.
2. Re-trace 3 freelancer lines in المبانى.xlsx sheet الكميات: row 14 (1 x 3.55 x 4 = 14.20), row 176 (1 x 3.00 x 3.70 =
   11.10), row 222 (3 x 1.00 x 2.40 = 7.20 deduction), and the cover cells H37 300.875, H196 617.248, H227 83.64.
3. Re-run run A (`tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`) and
   `extract_v29.py <run> --check`: 7 ARCH.WALL_RUN lines, 216.931 lm released, 21 block lines BLOCKED_RFI.
4. Band WB-FL0007-FL0008 on the GF plan (P7757.dxf): run A's 17.57 m band vs the two drawn pieces GF-W02 1.65 + GF-W03
   2.65 m; and one column-in-wall band (WB-FL0001-FL0002: 30.80 = 26.37 + 2.78 columns + 1.65).

## 7. Lessons row proposed (ERS s.7)

2026-10-23 | blockwork "source-supported gross - deductions" 3.464 / 12.001 m2 above the source-supported net (T-225) |
deductions booked on walls whose gross or net is HELD were subtracted from an established total | R-T225-1: a deduction
carries its host wall's status; net totals per status sum only walls of that status; a deduction on a held wall stays
in the held scope (any villa) | tests/t225_wall_register (fixture T225-F: normal 8.000 net; adverse: the naive
12.500 refused as a net, net on a HELD gross refused) | rule proposed.

Files: `extract_v29.py`, `build_t225.py` (`--check`), `register_v1.py`, SOURCES.csv, FREELANCER_BLK_LINES.csv,
FREELANCER_BLK_TOTALS.csv, THREE_WAY_BY_FLOOR_SECTION.csv, THREE_WAY_BY_FLOOR_THICKNESS_TYPE.csv, GAP_RECONSTRUCTION.csv,
RUN_A_VS_ENGINE_BY_BAND.csv, RUN_A_VS_ENGINE_BY_FLOOR_THICKNESS.csv, BLOCKWORK_WALL_REGISTER_V1.csv, BEFORE_COVERAGE.csv,
V29_RUN_A_MASONRY_LINES.csv, V29_RUN_A_WALL_BANDS.csv, summary.json; tests/t225_wall_register.
