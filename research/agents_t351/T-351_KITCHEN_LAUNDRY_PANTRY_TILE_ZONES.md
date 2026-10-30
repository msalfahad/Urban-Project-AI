# T-351: KITCHEN / LAUNDRY / PANTRY TILED ZONES (BOQ family B4-02), face by face (development villa; every villa by R-T351-1 .. 5)

Worker 2 (lane A), claim 2026-10-30 04:45 UTC, run unknown. Investigation of a MISSING category (B4-02 NOT_IMPLEMENTED,
BOQ_FAMILY_MASTER 1.19.0 / 1.20.0). Research only: no engine module, rule or knowledge file, candidate line, released
line or V2.9 cell changed; nothing released, nothing VERIFIED by this task. ERS applied: s.2.1 (physical element
first), s.2.2 (owner manual method and drawing-derived method side by side), s.2.3 (own vector reading), s.2.4
(reconcile in m2), s.3 (one face one owner; a rule's scope before its arithmetic), s.4 (rules + tests), s.7 (lesson row).

## 1. Identity and run

Own run, Python 3.11.18, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 `ab54dd55`
= SOURCE_MANIFEST), decoded into .work/private only. `t351_alsenan.py --geometry <P7757.dxf>` re-reads the 20 cited
wall / counter / open-edge handles (all within 1 mm) and the three room face sums; `--write` builds the ledgers from the
committed inputs (this task's face tables: handles and lengths only, and the merged T-312 / T-329 ledgers); `--check`
rebuilds byte for byte; tests `tests/t351_tile_zones` (17 pass). No coordinate, image, client name or plot data is
committed.

## 2. The physical element

A kitchen / laundry / pantry "tiled zone" is porcelain or ceramic on a WALL FACE of that room, between a bottom and a top
level, less the openings inside that band. Two physical readings exist and are kept apart:

- FULL-HEIGHT WALL TILE: every wall face, floor to the underside of the decor ceiling (a wet room);
- SPLASHBACK BAND: only the faces behind the counter / sink / appliances, between the worktop and a band top.

Which one is built is not a drafting question here: the owner rules decide it.

| Evidence (ERS s.2.2 order) | What it says for these rooms |
|---|---|
| (1) Project drawings | **Nothing printed.** T-091 (MERGED 6319aca) read all 12 architectural pages (single sheets 3, 4, 9, 10 included), the 842 DXF texts and the 3 sanitary pages: 0 wall-tile heights or notes, 0 finish notes, no interior elevation or kitchen detail in the set. Drawn: walls, windows, doors, counter outlines (layer 5) in the kitchen and pantry, none in the laundry. |
| (3) Owner rules | **UP-WET-001 1.1.0** (OWNER_APPROVED): wet codes BATHROOM, KITCHEN, PANTRY, IRONING, LAUNDRY; scope `walls: full-height wall porcelain (UP-FIN-WALL-001)`, paint none, skirting none; precondition: a CLOSED room (an open-plan face joining wet and dry gets no wet scope without a zone extent). **UP-FIN-WALL-001 1.8.0**: locations include KITCHEN / PANTRY / LAUNDRY; height = Q-48 A (floor-to-floor - 0.60 - 0.15 - 0.10: GF 3.65, 1F 3.35); a printed tile height replaces it. **UP-PANTRY-001 .. 004** (open American pantry): host walls of the installation, each whole; an open edge nothing; height never assumed. **Q-37 A** (pantry wet), **Q-30 A** (kitchen waterproofed like a bathroom), **Q-40 A** ("the wet area will be fully tiled"), **Q-48 A**. |
| Laundry flag | UP-WET-001 lists LAUNDRY under `project_confirmation_codes`; the Alsenan wet set (T-303 MERGED: 18 rooms) carries the laundry, and Q-48 (answered A) names "kitchen, laundry" among the rooms its height governs. The flag is settled for this project by those merged records; no new question. |

**Answer to the engineering question:** Q-48 A / UP-FIN-WALL-001 DO reach these rooms (named in both). Under the owner
method the zone of the closed kitchen and the closed laundry is the full-height wall tile on every face, and the
pantry's is the full wall on each host wall. **B4-02 therefore has no physical face of its own on Alsenan: every face is
already carried, once, by a FIN.WALL.TILE line (B4-01).** Booking a B4-02 band on top would count the same tile twice.
B4-02 becomes a real separate quantity only on a villa whose drawings print a band, or whose kitchen opens onto a dry
open plan (UP-WET-001 precondition fails): then a printed band or HELD by name (R-T351-1, -3), never a default 0.60 m.

## 3. Face by face (ZONE_LEDGER_T351.csv, 24 faces; own vector reading of P7757.dxf)

| Room (engine room) | Faces / contour | Openings (merged sizes) | Owner method | Carrier |
|---|---|---|---|---|
| GF kitchen GF-06 (GF-RA3AD49), annex | 9 faces, **14.500 m** (north 2.650 with W08, column 2FB1 0.450, east 2.300, column 2FB7 0.600, east 1.300 with D-GF-05, south 1.050, W.C. wall 1.500, south 1.650, west 3.000) | W08 1.501 (sill 1.00 / head 2.50), D-GF-05 1.00 x 2.20 | **HELD** by name: annex owner height not established (G2; Q-54 B HOLD, D-39); owner 3.15 PROVISIONAL is information only | L-c330b8dc47261d5ada7e (BLOCKED_RFI, blank) |
| 1F laundry 1F-07 (1F-R26FA0D) | 9 faces, **16.940 m** (polygon perimeter 18.520 less the d220 swing notch 2 x 0.790) | W21 0.60 (1.70 / 2.50) 0.480; D-1F-05 0.90 x 2.20 1.980; D-1F-06 0.80 x 2.20 1.760 | 16.94 x 3.35 = 56.749 - 4.220 = **52.5290 m2** ASSUMED — OWNER-APPROVED | L-b2077eee5a71a975bd74 (52.5290, T-315 r2) |
| GF pantry GF-07 (GF-RC06FED), open | 5 tiled faces **10.500 m** (west 4.450, column 2FAE 0.900 + return 0.050, north 2.100 with the door, south 3.000) + open edge 4.500 | W10 1.00 / W09 1.50 (1.00 / 2.50) 1.500 + 2.250; D-GF-06 1.00 x 2.20 2.200 | 10.50 x 3.65 = 38.325 - 5.950 = **32.3750 m2** OA (line 32.3422, finding F-T351-1) | L-f5c5a1a9c9ee2b644cb5 (32.3422, T-315 r2 ADD) |

Every window head lies below its tile top (2.50 < 3.35 / 3.65), so each opening is deducted whole inside the band
(R-T351-4); none twice. Determinate owner-method total of the three rooms: 52.5290 + 32.3750 = 84.904 m2 own (lines
84.8712), kitchen HELD (never 0).

## 4. Cross-trade (CROSSCHECK_T351.csv)

| Check | Result |
|---|---|
| (b) A face in a B4-02 zone and in a wall-tile line | **0 faces, 0.0000 m2**: all 24 faces are BOUND_TO_WALL_TILE on the room's one FIN.WALL.TILE line; B4-02 adds 0 faces |
| Own contour vs the merged T-312 ledger | kitchen 14.500 / 14.500 (0.000); laundry 16.940 / 16.940 (0.000); pantry tiled 10.500 / 10.491 (+0.009 m), open 4.500 / 4.490 |
| Own net vs the line | laundry 52.5290 / 52.5290 (0.0000); pantry 32.3750 / 32.3422 (+0.0328 m2, +0.10 %); kitchen HELD / blank |
| (c) Paint under the zone | NONE on every face (UP-FIN-PAINT-001): the 'paint above wall tile' lines are NOT_APPLICABLE_WITH_EVIDENCE and the pantry HL paint line L-c3f7e68ce91a436802e2 is blank (T-315 r2 named it physically NOT APPLICABLE). Named per face, not applied |
| (c) Plaster under the zone | the tile BACKING coat to the zone top, its own line (UP-FIN-PAINT-001 substrate): kitchen L-595181aa140e7efb2ac7 (HELD, 10 faces), laundry L-2948639faa08fa1cff81 (52.5290, 11 faces), pantry L-721a0f1441436193978c (32.3422, 7 faces), T-329 / T-331 MERGED. No ordinary FIN.PLASTER line may carry these faces |
| Open-plan dining lines and the pantry | the open zone's plaster / paint lines (HL GF-08, L-8cecb1d0 / L-c0ac22c9, BOUNDED 152.05 .. 178.81 m2) stop at the named VIRTUAL line on the pantry's open edge (T-128: open sides 5.735 m reported apart, never plastered): 0 pantry faces in them |

## 5. Drawing-derived reading beside the owner method (DRAWING_DERIVED_T351.csv)

What the drawing itself would support, if no owner rule existed: a splashback only behind the drawn installations.

| Room | Drawn installation (layer 5) | Host back length | Band printed? | Status |
|---|---|---|---|---|
| Kitchen | L-shaped counter 11C / 137 (0.50 deep) along the north and west walls; W08 (sill 1.00) above the north leg | 5.150 m (north 2.650 + west 2.500) | no | HELD: TILE_BAND_NOT_PRINTED |
| Laundry | none (no outline, no washer / sink block) | 0.000 m | no | HELD (nothing drawn to host a band) |
| Pantry | west, north and south counter legs + a peninsula on the open edge (T-312) | 5.916 m (3.066 + 1.450 + 1.400) | no | HELD: TILE_BAND_NOT_PRINTED |

The difference between the two methods is a different physical element (full wall vs band), not a measurement error;
the owner rule governs (owner-approved, explicitly naming these rooms) and the drawing prints nothing that would
replace it, so there is no conflict to escalate (ERS s.2.7 not met). The drawing-derived column never fills a blank.

## 6. Engine vs freelancer

His wet-wall item ('wet rooms and kitchens', boundary lm x 3.00 m, no opening deducted; T-010 / T-086 / T-209) carries
the kitchen 14.35 x 3.00 = 43.05 m2 and the laundry 16.85 x 3.00 = 50.55 m2 as full-wall rows, the pantry not at all,
and **no splashback or kitchen-zone row**: his scope agrees that these rooms are tiled as walls, not as bands.

| Laundry | m2 |
|---|---|
| Freelancer | 50.550 |
| Length (16.94 drawn vs his 16.85, x 3.00) | +0.270 |
| Height (owner 3.35 vs his 3.00, x 16.94) | +5.929 |
| Openings (D-1F-05 1.980, D-1F-06 1.760, W21 0.480) | -4.220 |
| Own (owner method) | **52.529** (residual 0.000) |

Engine vs freelancer: laundry +1.979 m2 (+3.91 %); kitchen not compared (HELD); pantry ours 32.3422 (line), his none.
Verdict proposals: B4-02 scope (no separate band item; zones = full-height wall tile) **RULE_DIFFERENCE: none** (both
treat the rooms as tiled walls; AGREE on scope); laundry height RULE_DIFFERENCE (Q-48 A vs a 3.00 printed nowhere);
openings ENGINE_RIGHT (UP-CER-005 / Q-73 A); pantry scope ENGINE_RIGHT (Q-37 A + UP-PANTRY-003).

## 7. Findings

- **F-T351-1 (pantry tiled length, for the Lead / Checker).** The vector reading of P7757.dxf gives the pantry's tiled
  faces 10.500 m (west 4.450 from the column 2FAE underside to A6, column 0.900 + 0.050, north 0.759111 + door 1.000
  + 0.340889, south A6 3.000; printed DIMENSIONS 5D5 3000 / 5C9 4500) against the merged T-312 / T-315 r2 ledger
  10.491 m (T-250 raster walk at 5 mm: GF-W16 4.475, GF-W01 2.995, GF-W05 1.955, OFF:WALL 0.165, column 0.900,
  residual 0.001), -0.009 m. On the line: 32.3422 vs 32.3750 m2 (-0.0328 m2, -0.10 %), under the 1 % Gate B rule.
  Cause: the raster walk's piece boundaries (5 mm pixels, 2 cm inset calibration), not a scope difference; the open
  edge shows the same 0.010 m (4.490 vs 4.500). NOT applied (not this task's line; a verified line moves only through
  a Checker record): named for the Checker's next re-measure of L-f5c5a1a9.
- **F-T351-2 (kitchen per-face split).** Own face split (9 faces by drawn handle) differs from the T-250 walk pieces
  (GF-W04 2.676, GF-W23 1.330, BAND-STRETCH 0.125 ...); the room total is equal (14.500 / 14.500) and one height
  carries every face, so no line figure depends on the split (as T-315 recorded for 1F-12).
- W08 jamb to jamb on the DXF 1.500 vs the merged 1.501 (T-201): 0.0015 m2 on a HELD line; named only.

## 8. Rules (research, PROPOSED; scope every villa; provenance T-351) and tests

R-T351-1 band from a printed source or an owner rule only, a default / typical source refused; R-T351-2 under the owner
wet scope the zone of a closed kitchen / laundry / pantry IS the full-height wall tile, bound to its FIN.WALL.TILE line,
a face in two tile lines refused; R-T351-3 held = blank, never 0; R-T351-4 an opening deducted only inside the band,
once; R-T351-5 no paint under a zone, the plaster there is the tile backing (named, not applied).
Tests (`tests/t351_tile_zones/test_t351_zones.py`, 17 pass): normal: a 4.00 x 3.20 closed kitchen rotated 0 / 30 /
-112.5 degrees and mirrored, hand 14.40 x 3.35 - 1.98 - 1.44 = 44.820 m2; an open pantry 5.00 x 3.65 = 18.250 m2 (open
edge and a non-host wall nothing); a printed 0.90 .. 1.50 band 2.280 m2 with a window above it deducting 0; a laundry in
mm and in m equal. Adverse: default / typical / blank / 'assumed 600' band refused; open-plan kitchen without a
printed band HELD with no total; held written as 0 refused; a face in the wall-tile line and B4-02 refused; a face
zoned twice and an opening twice refused; no unit and no owner height refused; an unread pantry host HELD. Development
villa: the ledgers rebuild byte for byte, 0 new faces, laundry 52.5290 = line.

## 9. For the integration (lane I) and the BOQ family register

- B4-02 on Alsenan: **no new line**. Proposed family-master entry: capability `COVERED_BY_B4-01` for closed wet
  kitchens / laundries and open pantries (the zone is the wall-tile line, bound by face id: GF-06 L-c330b8dc, 1F-07
  L-b2077eee, GF-07 L-f5c5a1a9); a separate B4-02 line only where a band is printed or the wet scope does not reach the
  room. No quantity moves; nothing to integrate except the mapping row.
- HELD stays HELD: the kitchen (G2 / Q-54 B, D-39); the drawing-derived splashback on all three rooms
  (TILE_BAND_NOT_PRINTED).
- Missing / uncertain: the sanitary sheet was not re-read for the kitchen sink position (it does not change the owner
  method; it would only refine the drawing-derived host length); pantry F-T351-1 for the Checker.

## 10. Lessons-register row (proposal, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | A 'missing' BOQ family (B4-02 kitchen / laundry / pantry tiled zones) would have been built as a splashback band on faces the wall-tile family already carries full height (84.87 m2 valued + the HELD kitchen on Alsenan) (T-351) | the family list names an estimating item (a band) without checking which owner rule governs the physical element in those rooms | before a 'missing' finish family is measured, map it to the physical layer and to the owner rule that governs it; where the owner rule already gives that layer to another family, the missing family is COVERED by face id, never a second quantity (scope: every villa, every finish family; provenance T-351) | tests/t351_tile_zones (B4-02 band on a wall-tile face refused; default band refused; held as 0 refused) | PROPOSED |

Self-gate: a c d f h PASS. Checked by the worker: research files and tests only (no engine, rule, registry or candidate
file), no client drawing, image, name or coordinate committed; freeze 0 differing; every figure traced to a drawn handle
or a merged line, held blank; non-Alsenan fixture with rotation / mirror / units / missing-data cases; owner rules
searched before any question (none raised).
