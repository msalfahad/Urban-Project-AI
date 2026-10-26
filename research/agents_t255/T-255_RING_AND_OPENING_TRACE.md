# T-255 Integration package ARCH_TAKEOFF_V3.0.19: the ring ground beam closed on its drawn faces, W03 / W18 traced

Worker 3 (lane I), 2026-10-26, run session_01EawZRLfDtSqjMBPLSCd4nS. Integration package for Checker Gate B. Opt-in
candidate only: the released default stays ARCH_TAKEOFF_V2.9 + route G (no switch); nothing here is RELEASED. ERS
2026-10-22 read and applied (s.2.1 element first, s.2.3 owner manual vs drawing method, s.3 build before deduct, s.4
statuses, s.7 lessons row). Drawings named by Drive folder and title only; no coordinates, no client text committed.
Integrates: F-T254-01 (Checker 2026-10-25 16:00, closed from the drawing), T-254, T-232, T-249, T-250, T-285, T-292 r2.

## 1. What the package changes (line id by line id)

| Kind | Line | Before (V3.0.18) | After (V3.0.19) | Status | Source |
|---|---|---|---|---|---|
| END_CLOSURE (rebase in place) | L-7076482d75ca42691468 STR.CONC.GROUND_BEAM GROUND BAND0043 (ring) | 1.7349 m3 (chord-closed ends) | **1.746943 m3** | DRAWING-CONFIRMED (SOURCE_DERIVED; VERIFIED only after Gate B) | F-T254-01, T-254 |

Everything else: 3,704 lines byte-identical to V3.0.18 (asserted by the module: whole-line sha, outside-rows hash
`db7264ed`), project identity block unchanged. 3,705 -> 3,705 lines: 1 CHANGED, 0 ADDED, 0 removed. Against released
V2.9 + route G: SAME_QUANTITY 715 / QUANTITY_DIFFERS 875 / NOT_IN_RELEASED 2,115 (unchanged counts: the ring line
already differed, V2.9 1.13162 at the interior class depth).

The opening trace (section 3) changes NO line: it records, per opening and trade side, the candidate line that carries
the supply quantity or the deduction, asserted against the lines of the run (a line that does not name the opening, a
deduction found twice, a part missing or counted twice refuses the package).

## 2. The ring ground beam (F-T254-01)

**Physical element.** The curved exterior ground beam between inner ARC 157 (r 2.250) and outer ARC 158 (r 2.550), width
0.30, D 0.95 (two printed levels, T-254 Gate B). Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (9f9d1179).

**What closes its ends (the drawing, not a convention).** North: outer arc 158 ends ON the straight beam face LINE 7C3;
7C3 stops at the west face of neck column 17C0; inner arc 157 starts at 17C0's south-east corner: the band is closed by
158 -> 7C3 -> 17C0 west + south faces -> 157. South: inner arc 157 ends at neck column 17BD's north-east corner, outer arc
158 enters 17BD through its west face: closed by 17BD's north + west faces. Crown: column 17BA stands in the band and is
deducted (its own trade, STR.CONC.COLUMN).

| Reading | Net plan m2 | x D 0.95 m3 | Who |
|---|---|---|---|
| carried (V3.0.17 / V3.0.18): T-242 polygon, ends on a chord | 1.8262 | 1.7349 | T-242 / T-254 |
| chord re-measured | 1.82582 | 1.73453 | Checker 13:35 / 16:00 |
| **drawn faces (this line)** | **1.83888** | **1.746943** | Checker 16:00 |
| drawn faces, this worker (private copy, shapely, 40 000 points per arc) | 1.838859 | 1.746916 | worker 3 |

Reconciliation, zero residual by cause: drawn net = chord net 1.82582 + the NORTH TRIANGLE 0.01306 m2 (between the chord,
beam face 7C3 and 17C0's west face; inside the closed drawn boundary; in no other line: not in the 7C3 / 170 band, which
lies outside the face, not in 17C0). The neck-column parts the chord already left out (17C0 0.01205 + 17BD 0.05380 =
0.06585 m2) are left out by both readings; 17BA 0.08961 m2 is deducted by both. The carried 1.7349 sits +0.00039 m2 above
the re-measured chord (T-242's own polygon, rounded): named on the line as `retired_residual`, not a drawn piece. This
worker's read is 0.000028 m2 (0.000027 m3, 0.0015 %) below the Checker's: his named 2 mm drawing-gap sliver under 17BD
(0.00002 m2) and rounding; the line carries the Checker's figure (lane I wires what the Checker verified).

**Owner manual method vs drawing method (ERS s.2.3).** Owner: a ground beam is plan area between its drawn faces x the
printed depth, columns deducted as their own trade. Drawing: the band polygon closed on the faces that meet the arcs. They
agree; the chord reading is neither (it is an arc-end convention) and is retired.

**Engineering effect (candidate, NOT RELEASED).** Ring 1.7349 -> 1.746943 m3 (+0.012043 m3, +0.69 %). STR.CONC.GROUND_BEAM
released 29.557243 -> 29.569286 m3 on 59 lines (12 blank, never 0). No other code moves. Freelancer ground-beam
comparison: not restated here (no ring-by-ring freelancer line; the scoreboard key map restates the trade, T-304).

**Downstream (named, not changed):** the ring's formwork (T-293 / T-199: the triangle's formed faces follow the drawn
faces), its buried waterproofing (T-276), excavation / backfill (not in the candidate).

## 3. W03 and W18: each opening once per trade side (the T-255 engineering question)

Read on the V3.0.18 lines of this run (json `ec741004`, the candidate of record byte for byte), line by line; the module
re-asserts every row against the lines (`V3_0_19_OPENING_TRACE.csv`).

**W03** (GF curved pool glazing band, 6.57 printed Q-38 A x 4.30 NW elevation, host GF-W37 a glazed line):

| Trade side | State | Line | Value | Evidence / item |
|---|---|---|---|---|
| window pcs | CARRIED_ONCE | L-a224c9fbabd0c366a6b0 (GF 11 pcs) | 1 pcs | opening_ids include W03 (T-232) |
| window m2 | CARRIED_ONCE | L-34a0aa9987a3e094d0de (GF 47.151 m2) | 28.251 m2 | formula 'W03 28.251' = 6.57 x 4.30 |
| window reveal | NO_LINE | - | - | the 27 reveal lines are the engine's own openings (all BLOCKED_RFI) |
| masonry | NOT_APPLICABLE | - | - | glazed host, nothing built (T-175 / T-249 s.3); MAS.BLOCK lines blank anyway |
| plaster room side, GF-15 part 5.106 m | CARRIED_ONCE | L-0d93f2209cd9bb827c0a (56.0131 m2) | 18.6369 m2 | 'W03 pool glazing band (bed-room part)' in the owner deductions |
| plaster room side, GF-08 part 1.625 m | HELD | L-8cecb1d010d5aafbf25d (BOUNDED) | 5.93125 m2 | GF-08 bounded (W02, lift door); deduction named once; T-244 |
| paint room side (same two parts) | CARRIED_ONCE / HELD | L-7f083d3e2c2702d14356 / L-c0ac22c964a42e7d71b1 | 18.6369 / 5.93125 m2 | as plaster |
| external finish | HELD | L-b05f70c92405dbcfbe62 (BLOCKED_RFI) | - | exterior finish not specified; T-305 |

Room side parts close: 18.6369 + 5.93125 = 24.56815 m2 = 6.731 x 3.65 (T-128 r3 developed room face x owner height G1);
0 double deductions (each part in one line, the two lines disjoint), 0 missing.

**W18** (1F sea-side bath window 0.50 x 2.16, sill / head printed, a glazed stretch in wall 1F-W00):

| Trade side | State | Line | Value | Evidence / item |
|---|---|---|---|---|
| window pcs | CARRIED_ONCE | L-221fdc86146248f1b67b (1F 13 pcs) | 1 pcs | opening_ids include W18 |
| window m2 | CARRIED_ONCE | L-ba28ba2da13f62445c9f (1F 23.285 m2) | 1.08 m2 | formula 'W18 1.08' = 0.50 x 2.16 |
| window reveal | NO_LINE | - | - | as W03 |
| masonry | HELD | L-5ffa7157a2fe483dd008 (MAS.BLOCK 1F t=0.20, BLOCKED_RFI) | 1.0094 m2 | register v3: 0.4673 inside the masonry x 2.160 (T-285, Checker own 1F-W00 12.935); T-279 |
| wall tile room side (1F-12) | HELD | L-82cd58d4a16fb94ddfc6 (BLOCKED_RFI) | 1.08 m2 | T-292 r2 face 1F-12, 1F-W00 deducts W18; NO lane I row carries FIN.WALL.TILE yet |
| plaster room side | HELD | L-12b83d399be186804faf (BLOCKED_RFI) | - | plaster under full-height tile: substrate HELD (T-211 s.5.4); T-244 |
| paint room side | NOT_APPLICABLE | - | - | tiled to full height ('paint above wall tile' line NOT_APPLICABLE_WITH_EVIDENCE) |
| external finish | HELD | L-8bb83e16cc7b104ab88b (BLOCKED_RFI) | 1.08 m2 | T-305 |

**Answer to the row's question:** windows pcs / m2 unchanged from V3.0.10 (W03 28.251, W18 1.08 already in the GF / 1F
lines; the '27 windows' were 29 drawn minus W17 HELD (Q-76) and W02 HELD (D-53)). No released line deducts W03 or W18
twice, and no released line that is built around them misses the deduction: the only released lines that touch them are
the window lines and the GF-15 plaster / paint lines (each deducts the W03 bed-room part once). Every other side is HELD
in a blank line with its carrier named, NOT_APPLICABLE (nothing built), or a NO_LINE finding. Nothing to apply; no line
changes for W03 / W18.

RULE_DIFFERENCE kept visible (no quantity moves): the finishes deduct W03 on the room-side developed line 6.731 m x 3.65
(T-250 verdict, T-128 right for plaster / paint), the window line takes the printed 6.57 x 4.30 (Q-38 A / Q-32 A);
masonry deducts W18 by its 0.4673 m inside the masonry (1.0094 m2), the window and finishes by 0.50 (1.080 m2).

## 4. Generic rules, code, tests

- **R-ARC-BAND-END-1** (T-255; every villa; provenance F-T254-01 + ERS s.2.1; research rule, a new rule version when
  adopted into the library): an arc band's ends close on the drawn faces that meet it (adjoining beam face, column faces),
  never on a chord between its arc ends and never on an arc span; an end no drawn face closes is not established (HELD);
  columns standing in the band are deducted as their own trade; the closing piece is owned by the band's line only; the
  retired reading is reconciled on the line (drawn = retired + closing pieces - excluded pieces; any carried residual
  named).
- **R-OPENING-ONCE-1** (T-255; every villa; provenance T-237 / T-249 / T-250): each drawn opening is carried once in its
  supply line and deducted once per trade side; an opening split between lines names its parts, which close to the side's
  value, one line per part; the trace reads the line's own record, never a ledger's word.

Code: `engine/source/arch_v3019.py` (MEDIUM, not frozen; `arc_band_net`, `check_end_reading`, END_CLOSURE record,
`trace_rows`), `tools/urban_boq_m9.py` (opt-in V3019 tuple and `--v3019-inputs` only; no default switched, older method
lists unchanged), `research/agents_t255/t255_inputs.py` (inputs; the T-254 row asserted), `v3019_run.py` /
`v3019_direct.py`, `rules/coverage/BOQ_FAMILY_MASTER_1.14.0.json` (1.13.0 + pending V3.0.19, no family change; builder
`build_master_1_14_0.py`; manifest by `tools/m9_rules_manifest.py`).

Tests `tests/t255_end_closure` (51): villa K255 hand fixture (ring r 2.00 / 2.30, outer arc ending on a beam face y 2.20,
inner arc at a column corner: gross 1.981408, triangle 0.067082, crown column 0.040000, net 1.941408 m2 x 0.80 =
1.553126 m3; chord 1.874326): normal (triangle counted once, columns closing the ends not deducted, crown column
deducted; mirror, rotation and mm units give the same area); adverse (chord / arc-span end refused where a drawn face
closes it; an end with no drawn face refused; the triangle in the ring AND the straight beam refused (geometry and
record); a column in the band left in refused; reconciliation not closing; value not net x depth; depth in mm; stale
before; unnamed residual; value 0; unknown line); trace normal (window carried once, masonry HELD, reveal NO_LINE, a
split band across two rooms with one part HELD) and adverse (one opening in two lines of one side, a line not naming the
opening, CARRIED in a held line, HELD without its carrier, a held side on a quantity line without saying what the line
covers, NOT_APPLICABLE with a line, unknown line, supply / masonry missing, a value not the line's, parts not closing,
one line carrying two parts, a deduction named twice in one line); registry 1.14.0 normal + adverse; Alsenan pins (the
Checker figures, the T-254 row, an edited ledger / chord reading / moved triangle stop the build, W03 / W18 sides).

## 5. Run (identity)

Own decode of Drive "Alsenan chalet project" 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from P7757_DXF_COMPRESSED.zip
(`ab54dd55`), Python 3.11.17: `research/agents_t167/v304_run.py` (V3_0_4 csv `d86de34a` reproduced) then
`research/agents_t255/v3019_run.py`: V3_0_15 csv `a4dc01dd`, V3_0_16 json `3181cf12`, V3_0_17 json `366be2f8` / csv
`429008af` / DIFF `5861cb3a`, **V3_0_18 json `ec741004` / csv `af577422` / DIFF `499348f4`** = the candidate of record
(T-266 Gate B) byte for byte. V3.0.19: BOQ_LINES json `b35475bf` / csv `ef63b73b`, DIFF `f988e898`, INTEGRATION_LEDGER
csv `2db0134e`; OPENING_TRACE csv `531d2a9a` (from `v3019_direct.py` on the same V3.0.18; the lines are byte-identical to
the m9 run's).

## 6. Who is right (proposals)

- Ring BAND0043: ENGINE_WRONG (chord-closed end) -0.012043 m3 -> corrected to the drawn faces (Checker's reading).
- W03 / W18: ENGINE_RIGHT on supply (in the window lines since V3.0.10) and on every released deduction; the held sides
  wait on T-279 (masonry), T-244 (plaster / paint), T-305 (facade) and a wall-tile row the board does not have yet.

## 7. Lessons row (proposed, ERS s.7)

2026-10-26 | A row asked whether two windows are deducted once per trade; 'once' cannot be read from one line when an
opening spans two rooms (W03: GF-15 5.106 m + GF-08 1.625 m) | A per-line search finds the opening in two lines and calls
it a double count, or finds one and calls the other part missing | Trace an opening per trade SIDE with named parts that
close to the side's value, one line per part, each read from the line's own record (any villa) | tests/t255
test_normal_split_opening_parts_close_once_each + adverse parts / two-parts tests | OPEN (T-255 READY).

## 8. Missing / held

Window reveal lines for W03 / W18 (and every reveal line: 27 BLOCKED_RFI): no line names them (finding for the Lead).
FIN.WALL.TILE has no lane I integration row (T-292 r2 is the merged ledger). Masonry (T-279), plaster / paint GF-08 and
the wet-room substrate (T-244), exterior finish (T-305): HELD, never 0. The ring line becomes VERIFIED only with the
Checker's Gate B. Formwork / WP of the ring: downstream packages.
