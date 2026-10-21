# T-138 Ground-beam and foundation-strap steel, bar by bar (lane S, gate 3; NO REPO CODE; a checked piece for V3.0)

Worker 1, 2026-10-21. Hand ledger only: `t138_hand_ledger.py` does the arithmetic of a hand table typed from the
drawings (it imports nothing from `engine/`), `T138_MEMBERS.csv` has one row per member and bar mark (316 rows after r2:
59 ground-beam spans, 7 through-column pieces, 3 straps). Nothing released changes.

## Sources read (Drive "Alsenan chalet project"; structural DXF sha 9f9d1179, structural PDF sha 74da1523)

| What | Where | Read |
|---|---|---|
| Strap bars | PDF p.10 "Schedule of Simple Beams", rows SB1 / SB2 / SB3 (columns: B, D, bottom bars, top bars, STIRRUPS/m) | SB1 70 x 50, 7 T16 bottom, 13 T18 top, 8 T8/m; SB2 100 x 50, 10 T16, 20 T18, 10 T8/m; SB3 50 x 40, 5 T16, 5 T18, 7 T8/m |
| Ground-beam bars | PDF p.13, four sections "Ground Beams": more than 5 m (30 x 60), less than 5 m (30 x 40), less than 2.5 m (30 x 30), exterior walls (30 x FOLLOW ARCH.) | > 5 m: 3 T16 top, 3 T16 + 3 T16 bottom, T8 @ 15 cm; < 5 m: 3 T14 top, 3 T14 + 3 T14 bottom, T8 @ 15 cm; < 2.5 m: same bars, link drawn without size or spacing; exterior: 3 T16 top, 6 T16 bottom, sides 2 T12 @ 30 cm, T8 @ 15 cm |
| Ground-beam spans | PDF p.3 "GROUND BEAMS PLAN" (no marks: the section follows from length and position), DXF layer 1 band lines and S-COL.BON columns | face to face, every span named by its band edge handles (the frozen S5 occurrence ids) |
| Strap geometry | PDF p.2 foundation plan; DXF S-FOOTINGS lines 1689 / 1B1C (SB1), 1B08 / 1B09 (SB2), 1B26 / 1B27 (SB3) and the footing outlines | clear length between footing faces along the strap axis |
| Cover | PDF p.8 general note 22: 2.5 cm in columns, slabs and beams; 7 cm in concrete against soil (minimum) | used for link paths only (straight bars are measured face to face) |
| Laps / development (r2) | PDF p.8 general note 9: lap length of the bars ("Development Length") not less than 70 x bar diameter in tension zones, 40 x bar diameter in compression zones | the zone of a bar end or splice is not printed: every development and lap length is a 40 d .. 70 d RANGE, HELD |
| Side bars (r2) | PDF p.8 general note 21: additional side bars 2 / 3 / 4 T12 in beams deeper than 60 cm, by beam width, unless stated otherwise; p.13 exterior section prints sides 2 T12 @ 30 cm | the > 5 m section is exactly 60 cm (not over 60: note 21 does not apply); exterior depth not printed (D-35) and the width-to-count key not printed: HELD |
| Stock length (r2) | rule URBAN-REBAR-NET-AND-PROCUREMENT@v1, parameter stock_length_m 12.0 | procurement laps on continuous runs over 12 m |
| Unit mass | d^2 / 162 (the project method) | |

## Result: engine vs freelancer (Alsenan, rebar, kg, net)

| Line | Hand (this ledger) | Frozen S5 / S5.1 (engine, opt-in research) | Route G (released route, provisional) | Freelancer |
|---|---|---|---|---|
| Ground-beam longitudinal bars, released spans | **1,194.60 RELEASED** (31 spans, lower bound: face-to-face straight run) | 1,238.56 (S5) | default run (no project profile): **0, no ground-beam steel line**; 59 concrete lines all UNRESOLVED (exposure 17.80 .. 59.34 m3). With the typed ST7757 profile: 58 concrete lines (27.36 m3) and 3,526.92 kg on 128 lines + 46 unresolved (see r2 item 4) | in "ground beams + ground floor" 9.75 t (75.09 m3: 0.30 x 0.60 x 253 m of beams + slab), no split |
| Bars through 7 interior columns (continuous released bands) | **58.31 RELEASED** | 25.60 (S5.1, 6 columns at the schedule side) | 0 | |
| Strap SB1 | **168.63 RELEASED** (lower bound) | 168.63 | 305.74 (with STANDARD_PRACTICE anchorage, links with code hooks) | in "footings total" 5.8 t |
| Strap SB3 | **58.32 RELEASED** (clear 3.258 m) | 50.80 (clear 2.838 m) | 99.43 | in 5.8 t |
| Strap SB2 | **HELD 127.96** (issued-sheet row 100 x 50; 91.72 under the off-sheet 80 x 50 row) | HELD (SOURCE_CONFLICT) | 231.46 | in 5.8 t |
| **Released total** | **1,479.86 kg** | 1,458.00 (S5) / 1,483.60 (S5.1 bars only) / 1,550.85 (S5.1 incl. 67.26 kg links) | 636.63 (straps only) | 5.8 t + 9.75 t lumps, scope differs |
| Held, longitudinal, defined candidates | 1,069.83 .. 1,192.48 + 6 spans with no bar run + every span with a concentrated-load candidate (no detail) | | | |
| Held, links (count = owner Q-71) | A 693 / B 723 links; 89.61 / 93.03 / 88.33 kg (A / B / C) on the spans whose depth is printed + straps; 33 spans unquantified | 67.26 kg RELEASED in S5.1 (see verdict 4) | | |
| Held, strap bars over the footings | 0 .. 270.92 kg (drawn band less 2 x 70 mm; information only) | blocked | in its anchorage | |
| Held, development at bar ends (r2, note 9, 40 d .. 70 d) | ground-beam ends of released spans 383.00 .. 670.26; of held spans 109.58 .. 254.86 (+ 20 spans whose bars are not established); straps SB1 + SB3 76.11 .. 133.20; SB2 77.83 .. 136.20 | blocked | convention anchorage (STANDARD_PRACTICE) | |
| Held, procurement laps (r2, PROCUREMENT_WEIGHT_INCL_LAPS) | 18.20 .. 31.86 (two continuous runs over 12 m: 7D0 / FC 18.57 m and 170 / 7C3 13.77 m, 9 T16 x 1 lap each, 9.10 .. 15.93 per run) | | | |
| Held, unquantified | side bars 2 T12 @ 30 (exterior depth not printed; p.8 note 21), hook / bend shape at every bar end (D-36), link hooks, the < 2.5 m link | same | | |

**Net / held / procurement kept apart (r2, re-added by the script):** NET RELEASED **1,479.86 kg** = ground-beam
spans 1,194.60 + bars through 7 interior columns 58.31 + SB1 168.63 + SB3 58.32 (unchanged from r1, all confirmed by the
checker). HELD (net, ranges): longitudinal 1,069.83 .. 1,192.48 + SB2 91.72 .. 127.96 + links (Q-71) 88.33 .. 93.03 +
development 646.53 .. 1,194.51 (383.00 .. 670.26 + 109.58 .. 254.86 + 76.11 .. 133.20 + 77.83 .. 136.20), plus the named
unquantified items. PROCUREMENT (laps only, on top of net, HELD): 18.20 .. 31.86 kg; procurement weight of the released
runs = 1,479.86 + 18.20 .. 31.86 = 1,498.07 .. 1,511.72 kg once the zone is settled.

No % against the freelancer: both his lines are lumps of a different scope (his "footings total" 5.8 t holds the
straps; his "ground beams + ground floor" 9.75 t holds the ground slab and prices every beam as 0.30 x 0.60, which the
drawing gives only to the > 5 m section). Engine (S5) vs hand on the same 31 released spans: 1,238.56 vs 1,194.60 kg,
**+43.96 kg (+3.7 %) over the hand figure**, although S5 calls each value a lower bound.

## What the hand reading found (verdict proposals for the checker)

1. **Three founded columns sit on ground-beam bands but are not supports in the frozen S5 register** (ENGINE_RIGHT for
   the hand, i.e. S5 wrong): column 228 (C6 on F6) on band 109 / 7CB, column 1E0 (C2 on F2) on band 170 / 7C3, column 211
   (C3 on F3) on band 13E / 7D6. S5 runs one span straight across each: 9.50 -> 4.40 + 4.40 m; 6.22 -> 2.40 + 3.37 m;
   5.10 -> 4.30 + 0.50 m. All three columns appear at the same place on the foundation plan over a footing (checked by
   shifting the foundation plan 38,724.4 mm in x, the offset of the two plot outlines). Two spans change their p.13 class
   from "more than 5 m" to "less than 5 m"; the third (170 / 7C3) is exterior, so only its length changes (88.46 ->
   82.06 kg). Hand check: band 170 / 7C3 edges y 49,548 / 49,848; column 1E0 x 98,518 .. 98,818, y 49,348 .. 49,848 crosses
   the full band; 98,518 - 96,118 = 2.400 m and 102,188 - 98,818 = 3.370 m.
2. **Where a column edge is collinear with a band edge, S5 measures the span centreline minus 0.30 m instead of face to
   face** (ENGINE_RIGHT for the hand): the south band 7D0 / FC (columns 249 = 1.10 m, 251, 255 along it): 3.375 / 6.245 /
   6.650 / 1.400 -> 2.975 / 5.745 / 6.350 / 1.200 m (hand: 96,293 - 93,318 = 2.975; 103,138 - 97,393 = 5.745; 109,988 -
   103,638 = 6.350; 111,888 - 110,688 = 1.200). Same cause on 170 / 7C3 spans 2 and 3, 184 / 7CF, 114 / 7DF, 185 / 7C7,
   13D / 7D2, 137 / 138, 7D4 / F8: 13 released spans shorter by 0.05 .. 0.50 m, 2 longer (10A / 7C9 4.20 -> 4.30, 17B / 7E5
   1.05 -> 1.20). Net -43.96 kg on the released spans. One more class change: 177 / 7CD span 1 5.32 -> 4.97 m (column
   1EC face x 100,768 to column 245 face x 105,738), and 184 / 7CF span 3 is exactly 5.00 m face to face, which neither
   p.13 title covers.
3. **Oblique straps: S5's clear lengths are short** (ENGINE_RIGHT for the hand): SB2 1.829 -> 2.293 m (faces y 37,848 and
   40,098, axis slope 0.9813: 2,250 / 0.9813 = 2,293 mm; both footing outlines are drawn broken exactly where the strap
   edges cross, at x 134,829 / 135,835 and 134,389 / 135,395); SB3 2.838 -> 3.258 m (3,050 / 0.9361). SB3 50.80 -> 58.32 kg.
   SB1 (vertical) agrees exactly: 4.550 m, 168.63 kg.
4. **S5.1 releases 67.26 kg of links whose count comes from a spacing / per-metre notation** (ceil(rate x run)): that
   count is owner Q-71, still open, so those kg should be HELD (UNRESOLVED), not released. This ledger shows readings
   A (ceil), B (A + 1) and C (fractional) and holds them.
5. **SB2 has one row on the issued schedule** (UNRESOLVED, proposal: the issued row governs): the second SB2 insert
   (80 x 50, 10 T18 / 10 T18) lies 2.88 m below the schedule frame (frame bottom y -6,670, insert y -9,548) and is not on
   the printed p.10; the plan draws SB2 0.987 m wide. Two sources (issued sheet, plan width) agree on 100 x 50. Kept
   HELD here because S5 recorded a source conflict; the checker or the designer (D-38) settles it: 127.96 kg vs 91.72 kg.
6. **Route G, default run (no typed project profile), gives the ground-beam spans no steel at all** (its 59 concrete
   lines are UNRESOLVED with no steel line beside them; with the typed profile it gives 58 concrete lines, see r2 item 4)
   and gives the straps anchorage and hook lengths from its convention file (STANDARD_PRACTICE), which the
   Urban rule does not allow: route G 636.63 kg vs hand 226.95 released + held. ENGINE_RIGHT for the hand on the strap
   lower bounds; the route G extra is held items, not steel the drawings print.
7. **Freelancer**: RULE_DIFFERENCE / scope: two lumps, no diameter, no member split; kg/m3-type allowances are never
   copied. His beam take-off (0.30 x 0.60 everywhere, 253 m) differs from the drawing's four sections.

## Owner manual method and drawing-derived method side by side

| | Owner / Urban manual method (this ledger) | Drawing-derived engine (frozen S5 / S5.1) | Route G |
|---|---|---|---|
| Count | as printed (n T d) | as printed | as printed |
| Spacing / per-metre count | HELD, readings A / B / C (owner Q-71) | ceil(rate x run) released (S5.1) | (n / m x L + 1) |
| Bar length | face-to-face straight run read from the plan; bars through an interior column added where the band continues with the same bars | register "bar straight run lower bound" (defects 1-3) + S5.1 through-support at the schedule side | clear span + 2 anchorage (convention) |
| Ends, laps | development / lap length 40 d .. 70 d from p.8 note 9 (zone not printed), HELD; procurement laps on runs over 12 m stock, HELD; net kept apart | blocked | convention values |
| Hooks / bend shape | HELD, D-36 (not printed) | blocked | convention values |
| Section of an unmarked ground beam | p.13 class from the face-to-face length and the exterior wall above; candidates kept when two titles hold | same rule, its own lengths | - (no steel) |
| Mass | d^2 / 162 | d^2 / 162 | d^2 / 162 |

## Held items (never 0) and the designer requests they need

- D-33 concentrated load: which ground beams count as carrying a concentrated load (another beam ending on them, the
  stair start)? p.13 prints sections only "without concentrated load". 15 spans held (CONC candidate).
- D-34 length basis of the p.13 titles (clear or centreline), which title governs below 2.5 m, the < 2.5 m link (drawn,
  not labelled), and the span exactly 5.00 m long (184 / 7CF span 3).
- D-35 depth of the exterior ground beams ("FOLLOW ARCH.": floor build-up not printed): side bars 2 T12 @ 30 cm and the
  exterior link path stay unquantified.
- D-36 (narrowed in r2 to hooks / bar ends): the development LENGTH is printed (p.8 note 9, 40 d .. 70 d by zone), so
  D-36 now asks only for the zone of each end (or one length) and the end shape (straight, hook, bend-down). SB3 is drawn
  only 0.649 m past each footing face after cover, less than 40 d of its T18 top bars (0.72 m): its bars cannot end
  straight inside the drawn band (SB1 1.330 m and SB2 1.336 m fit 70 d = 1.26 m). The drawn-band figure 0 .. 270.92 kg is
  kept as information only.
- D-37 link hooks and the strap link legs (inner legs not drawn).
- D-38 SB2: confirm the issued 100 x 50 row (the 80 x 50 insert is off the sheet).
- Owner Q-71 (open): every link count here, and the exterior side bars.
- Not re-measured (frozen S5 run carried, named in the CSV): 2 arc bands, 3 oblique bands, the boundary end 1811 / 1812,
  145 / 7CA (the plan gives 1.900 m column to column through the 178 / 7DB junction, S5 cuts 0.40 + 2.30).

## Ten bars for the checker (count x length x d^2/162)

SB1 top 13 x 4.550 x 2.0000 = 118.300; SB1 bottom 7 x 4.550 x 1.5802 = 50.331; SB3 top 5 x 3.258 x 2.0000 = 32.580;
SB3 bottom 5 x 3.258 x 1.5802 = 25.742; 7D0 / FC span 2 top 3 x 5.745 x 1.5802 = 27.236 and bottom 6 x 5.745 x 1.5802 =
54.471; 170 / 7C3 first piece top 3 x 2.400 x 1.5802 = 11.378; 7E9 / 7EA bottom row 1 3 x 4.225 x 1.2099 = 15.335;
184 / 7CF span 2 top 3 x 2.650 x 1.2099 = 9.619; 185 / 7C7 bottom 6 x 0.600 x 1.5802 = 5.689.

## Non-Alsenan hand fixture (two straps; asserted by the script)

Strap A, count notation, 4 T16 top + 4 T16 bottom, clear 3.20 m: 8 x 3.20 x 1.5802 = 40.454 kg (a mirrored plan gives the
same length). Strap B, rotated 30 deg off the y axis, footing faces 2.000 m apart in y: clear 2.000 / cos 30 = 2.309 m;
6 T18 top + 3 T16 bottom = 27.713 + 10.948 = 38.661 kg. Its links "7 T8 / m": A 17, B 18, C 16.166 (HELD, Q-71); written
"T8 @ 150" instead: A 16, B 17, C 15.396 (HELD). Missing data: a strap with no schedule row or two different rows gets no
released steel (HELD with both readings), never 0.

## r2 rework (verifier 2026-10-21 04:10 reasons), worker 1

1. **Laps / development (p.8 note 9, read on the issued sheet):** not less than 70 d (tension) / 40 d (compression).
   The zone of a bar end is not printed, so each end is a 40 d .. 70 d range, HELD (rule: laps from the structural
   notes; never a practice value). One CSV row per span ("BAR ENDS (development 40d..70d, note 9)") with its number of
   ends: a band whose bars run through its interior columns (7D0 / FC, 170 / 7C3, 7D4 / F8) has two ends in all; every
   other span has two ends per piece (a span cut by a column it did not see has four). Hand check 7D0 / FC end: 9 T16 x
   0.640 .. 1.120 m x 1.5802 = 9.102 .. 15.929 kg; 13C / 7D9 (9 T14, 2 ends) 2 x 9 x 0.560 .. 0.980 x 1.2099 = 12.196 ..
   21.342 kg; SB1 2 x (13 x 0.72 x 2.0 + 7 x 0.64 x 1.5802) = 51.599 kg (40 d).
2. **PROCUREMENT_WEIGHT_INCL_LAPS:** continuous released runs over the 12 m stock: south band 7D0 / FC 93,318 ->
   111,888 = 2.975 + 1.10 + 5.745 + 0.50 + 6.350 + 0.70 + 1.200 = 18.570 m and north band 170 / 7C3 2.400 + 0.30 + 3.370
   + 0.60 + 3.350 + 0.50 + 3.250 = 13.770 m: ceil(L / 12) - 1 = 1 lap per bar, 9 T16 bars (exterior section 3 top + 6
   bottom) x 0.640 .. 1.120 m x 1.5802 = 9.102 .. 15.929 kg per run, 18.20 .. 31.86 kg in all, HELD on the same 40 d ..
   70 d range. 7D4 / F8 (5.45 + 0.40 + 4.25 = 10.10 m) and every strap are under 12 m: no lap. Net is not changed.
3. **D-36 narrowed** to hooks / bar ends (DESIGNER_CLARIFICATIONS.md); **side bars:** p.8 note 21 (2 / 3 / 4 T12 by
   width in beams deeper than 60 cm) cited beside the p.13 exterior "2 T12 @ 30": the > 5 m section is exactly 60 cm, so
   note 21 does not add side bars to it; the exterior beams stay HELD (depth not printed D-35, spacing count Q-71, and
   note 21's width-to-count key not printed).
4. **Route G history (4,101.77 kg PROVISIONAL on 164 lines).** That figure is
   `research/urban_engine_m7_reliability/st7757/BY_FAMILY.csv` (commit a99974d, 2026-10-11), produced by
   `st7757_run.py` with the TYPED project profile `research/urban_engine_m4_correctness/profile_st7757_m4.json` (it
   carries GB_TYPICAL_SECTIONS) and the architectural DXF. **No commit removed it:** route G takes the ground-beam
   typical sections only from a typed profile (`engine/source/generic_route.py:936`, branch `elif ground and ... and
   "GB_TYPICAL_SECTIONS" in conv.items`, unchanged since b059ba2 / ed91cbd per `git log -L`); without it every span goes
   to the UNRESOLVED branch with no bar line. Re-run today on the working head with the Drive structural DXF (sha
   9f9d1179), conventions V5, no architectural DXF: default run 59 GB concrete lines UNRESOLVED (17.80 .. 59.34 m3), 0 kg
   GB steel, straps 636.63 kg; with the typed profile 58 GB concrete lines PROVISIONAL (27.36 m3), 3,526.92 kg GB steel
   on 128 lines + 46 unresolved, straps 636.63 kg. The 4,101.77 vs 3,526.92 kg gap is the architectural DXF input (not
   re-run here). The 59th line in the default run is band BAND0044, which has no ground-beam concrete line at all under
   the typed profile (not traced; reported to the Lead as a possible silent drop). So: **ground-beam concrete lines are
   58 under the profile (the checker is right), 59 in the default run; r1's "59 lines, 31.15 m3, none with steel" mixed
   the two runs and is corrected above.** The gap that matters for every villa stands: a new villa has no typed profile,
   so route G prints no ground-beam steel (T-045 owns that fix).
5. **Totals re-added** by the script and stated apart (net released / held / procurement) under the result table.

## Validation

`python3 -I research/agents_t138/t138_hand_ledger.py` (fixture asserts pass; totals above; r2 adds the development, procurement and note-21 rows: 316 rows). No engine, rule, test or
frozen file changed; freeze check 0 differing; maps rebuilt for the new files.

r2 fixture (non-Alsenan, asserted): strap A's 8 T16 developed at both ends 2 x 8 x 0.640 .. 1.120 x 1.5802 = 16.182 ..
28.318 kg; laps on continuous runs: 12.00 m -> 0, 12.01 m -> 1, 24.00 m -> 1 (exact multiple), 25.00 m -> 2.
