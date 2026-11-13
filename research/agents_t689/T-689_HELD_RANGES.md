# T-689 Concrete held ranges: STR.CONC.COLUMN and STR.CONC.BEAM narrowed from the drawings or their datum named

Worker 1 (lane S), 2026-11-11, branch `agents/task-T-689`. Research only, unwired: no engine module, candidate line,
rule / knowledge version file, key map or released default changed; nothing released; development villa, not an
accuracy claim. Drawings cited by Drive folder / title and DXF handle; no coordinate committed. Rules R-T689-1 / -2 /
-3 1.0.0 (`t689_rules.py`), built on R-T678-2 and R-T669-2 (not edited). Table: `out/T689_HELD_RANGES.md` / `.json`.

## 0. Inputs and runs

- Candidate of record V3.0.67 (`research/agents_t682/out/LINE_INDEX_V3_0_67.json`, T-682 head 0bdf3131, merged);
  restated on the working head adef31c5 (same index file). Causes: T-683 statement (V3.0.66) + T-682 for PC-2F / annex C3.
- OWN READ this run of Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (3,153,037 B, sha256 9f9d1179 = manifest),
  decoded into `.work/private` only: `t689_extract.py` -> `out/T689_OWN_READ.json` (values only).
- `t689_alsenan.py --write` / `--check`; tests `tests/t689_held_ranges` (21).

Note on the task text: its BEAM figures 6.023229 .. 8.507710 are the V3.0.63 (T-669) census. On V3.0.66 and V3.0.67
the 14 bounded BEAM lines are **5.983229 .. 8.412710 m3 (width 2.429481)**; COLUMN on V3.0.67 is 22 lines
**10.264350 .. 13.270250 (width 3.005900)** (T-682 added PC-2F and annex C3). Both re-add to the index to the digit.

## 1. Ranking (R-T689-3) and the 80 % sets

COLUMN: 16 of 22 lines make 82.5 % of the width; BEAM: 8 of 14 make 81.3 %. Every line, its member, before / after,
cause and item is in the table. By cause, top sets:

| Cause | Lines (top 80 %) | Width m3 | Item | Why the drawings cannot close it (searched) |
|---|---|---|---|---|
| column section: slab-plan outline vs schedule band | 9 (1F 679, 688, 673, 694, 68E, 676, 697, 691; GF 344) | 1.5405 | D-66 | T-256 (Checker-verified): no third member-specific print on any sheet; owner X6 (Q-61 (1)) forbids picking the printed one |
| column section C8 at F14 | GF 380 | 0.1125 | D-16 | CAP 30X80 + drawn 0.80 vs schedule 90 deep |
| 2F roof slab-top datum | 5 (C9 418, C2 41B / 41E / 412, C1 421) + PC-2F height | 0.6588 + PC-2F 0.1676 (before) | D-39 | finished +13.90 only; lower end from drawn heads (section 2) |
| PC-2F section: drawn 0.20 x 0.40 vs FFRS text 77C 'P.C 20x50' | PC-2F | (in its 0.1676) | **none** | register gap (section 3) |
| unlabelled beam depth (0.40 .. 1.20 set envelope) | 5 (2F BAND0006.1 / 0011.1 / 0008.1 / 0001.3, 1F 0005.1) | 1.2528 | D-04 | T-402 r2: none of the 14 section cuts reaches them, no plan dimension, no mark within 1.2 m |
| beam width schedule vs drawn | 2 (GF BM-GF-056, BM-GF-054) | 0.5362 | D-27 | T-402 r2: no cut, no dimension |
| two marks on one span | GF CB3 / 'B3 (With Stair)' | 0.1855 | D-03 | one row each, never both |

## 2. The one drawn datum found: 2F roof slab top >= +12.937 at beam B8 (R-T689-1)

Physical element: a 2F column runs from its base +9.65 (APPROVED) to the 2F roof slab top (UP-CONC-JOINT-001); the
slab top is not printed (D-39), the finished mark +13.90 is the ceiling. The current low 12.68 is R-T669-2 (W26 apex
+12.50 printed + T 18). Own read this run:

- B8 on SECOND FLOOR ROOF SLAB: label 79E inside the clear span between columns 412 and 415; edges 38D / 38E 0.200
  apart; clear span 412 east face -> 415 west face **3.470 m**; schedule row 1EBA (SBT block): **B8 W 20, H 75**,
  bottom 4 d16, top 2 d12 (the sagging pattern; B15, the one beam whose stand is an open item (D-44), has top 6 d18 >
  bottom 4 d16). Width drawn = schedule, no D-27 conflict on B8.
- Supports (T-566 position map, own handle check): 412 = 2F C2 (FP 1087), 415 = 2F C5 (FP 108A); both on the band.
- Heads under B8 (merged evidence, not re-derived): T-261 r2 places W28 at 0.375 .. 0.975 and W29 at 2.270 .. 3.470 of
  the 2F-W02 B8 piece 3.470 (its net 11.9715 - 0.48 - 1.80); T-201 draws W28 / W29 heads at **+12.200**
  (DRAWING-CONFIRMED, read tolerance 0.013 / 0.019 m, SW elevation).

top_B8 >= max(12.200 - 0.013, 12.200 - 0.019) + 0.75 = **12.937** (W28 governs; <= 13.90, no contradiction). B8's top
at a support is the top of the supporting column (one joint node), so for 412 and 415, h >= 12.937 - 9.65 =
**3.287 m** (was 3.03), with no one-plane premise.

- **L-919a5749 (C2 2F, 412): 0.303 .. 0.425 -> 0.3287 .. 0.425 m3** (0.10 x 3.287). The only range moved.
- 2F C5 at 415 (L-bc01297b) is blank (section D-66): it gains the height floor only, no m3.
- Plate transfer to the other 2F columns is REFUSED under R-T678-2 as written: 'T 18' is printed inside the 2F roof
  outline (7B3 / 7B4, 1A7D / 1A7E, the two tank panels), so one plane is not established. Named, not applied: on the
  one-plate premise that the current R-T669-2 low of those same lines already uses, their lows would rise by
  **0.133640 m3** (C9 418 0.4242 -> 0.46018, C2 41B / 41E and C1 421 0.303 -> 0.3287 each, PC-2F 0.1824 -> 0.20296).
  **Finding F-T689-1 (rule consistency, for the Lead / Checker):** R-T669-2 bounds these lines plate-wide on a plate
  that R-T678-2's own clause ('no thickness printed inside it') would refuse; either both stand (and the 0.133640
  applies) or the R-T669-2 lows of the non-support columns lose their plate basis. Not decided here.

Result: COLUMN width 3.005900 -> **2.980200 m3 (-0.025700)**; BEAM width 2.429481 unchanged. Every other top line is
tied to its designer item; none is closed, none moved to a midpoint, the freelancer is not used.

## 2a. Next related item: 5 BLANK column lines bounded (OPEN -> bounded; `conflict_bound`)

Five COLUMN lines were HELD blank only because 'their section waits for D-66' (T-678 / T-682 follow-up). A section
CONFLICT with both readings known bounds the volume exactly as the 20 bounded conflict lines already are (smaller
reading x lower height .. larger reading x upper height; one reading is never chosen). Readings: own read of the
outlines this run (GFRS 34A / 34D / 356 / 350 0.20 x 0.40, SFRS 415 0.60 x 0.20) vs the schedule (C GR 20 x 50, C3 GR
25 x 50, C5 2ND 20 x 50), each classed CONFLICT PRINTED_VS_DRAWN by T-217 (merged). Heights: annex 3.294 .. 4.05 m
(R-T678-2, Checker-verified: W08 head under CB6, base 0.25 APPROVED, one plane, finished +4.30); 2F C5 at 415 3.287 ..
4.25 m (R-T689-1 above, B8 east support; D-39 ceiling).

| Line | Member | Areas m2 | Height m | Before | After m3 |
|---|---|---|---|---|---|
| L-9f5a6470 / L-c0b3340a / L-e6c1c9a7 | C GF annex trio (34A / 34D / 356; identical readings, pairing not asserted) | 0.08 .. 0.10 | 3.294 .. 4.05 | blank | 0.26352 .. 0.405 each |
| L-694a75c8 | C3 GF annex, 350 | 0.08 .. 0.125 | 3.294 .. 4.05 | blank | 0.26352 .. 0.50625 |
| L-bc01297b | C5 2F, 415 | 0.10 .. 0.12 | 3.287 .. 4.25 | blank | 0.3287 .. 0.51 |

COLUMN blank 7 -> **2** (left: 2F tank C2 40F and C3 424, D-44 up / down-stand of B15 refuses their ceiling). The
bounded set gains **1.382780 .. 2.231250 m3**; the COLUMN family moves from 10.264350 .. 13.270250 + 7 OPEN to
**11.672830 .. 15.501500 + 2 OPEN** (22 + 5 = 27 bounded lines). Width of the five 0.848470, closing an OPEN end each.
**Register gap F-T689-3:** none of 34A / 34D / 356 / 350 / 415 is in D-66's registered list of 13 outlines, though the
census cites 'D-66' for them; proposal: add the five to D-66 (same question: plan outline or schedule band).

## 3. Register gap (R-T689-3): PC-2F section has no designer item (F-T689-2)

L-541c7e56 (PC-2F, rank 7, 0.1824 .. 0.350) carries two independent causes: height (D-39) and section, drawn FFRS 77B /
SFRS 778 0.20 x 0.40 vs the member's own text FFRS 77C 'P.C 20x50' (T-217 PC:77B; Checker re-read the CONFLICT,
0.08 .. 0.10 m2). T-217's original band question ('D-64', renumbered D-66) listed PC:77B, but D-66 as registered names
13 outlines (GF 347 / 359 / 344, 1F 691 / 676 / 697 / 673 / 694 / 685 / 688 / 68E / 679 / 667) and D-46 covers only the
planted columns' bars. Proposal for the Lead: add 'PC-2F (FFRS 77B / SFRS 778, text 77C P.C 20x50): which section is
built' to D-66. Impact: section 0.08 .. 0.10 m2 x 2.28 .. 3.50 m (part of the line's 0.1676 width).

## 4. Methods side by side (ERS s.2.2)

Owner manual method: member by member, a conflict is held with both readings and a designer request (Q-61 C, X6); a
height without a printed datum is held (no generic storey value). Drawing-derived: the same, plus the bound from drawn
heads under printed beams (R-T669-2 / R-T678-2 / R-T689-1). Both give the same holds; the drawing-derived method moves
one low end by 0.0257 m3. Freelancer: not used for any bound (his columns are per type x count, T-248 / T-683).

## 5. Verdict proposals and what stays held

- L-919a5749 low 0.3287: ENGINE (drawing) bound DRAWING-CONFIRMED end; line stays HELD (D-39 high end open).
- Every other top line: UNRESOLVED (designer: D-66, D-16, D-39, D-04, D-27, D-03), quantities unchanged.
- No owner question: ERS 2.7 not met (designer items; no owner method / contract decision).

## 6. Lessons rows (ERS s.7, PROPOSED)

| 2026-11-11 | a slab-top lower bound from a drawn head under a printed beam was applied only through a plate premise | the
beam-column joint gives the bound to the beam's own supports with no plane premise | transfer to support columns first
(R-T689-1); plate-wide only under R-T678-2 | tests/t689_held_ranges |
| 2026-11-11 | a held line with two causes was registered under one item; the other cause had no D number after a
renumbering | one item per cause, checked on every top-share line (R-T689-3) | tests/t689_held_ranges |

## 7. Checker re-measure list (two largest moves)

1. B8: 79E between 412 / 415; 38D / 38E 200 apart; 412 east face to 415 west face 3,470; SBT 1EBA W 20 H 75.
2. W28 / W29 inside the 3.470 span (T-261 r2 jambs 133D / 133C, 1330 / 132F) and heads +12.200 (T-201 SW elevation).
3. 'T 18' texts 7B3 / 7B4 / 1A7D / 1A7E inside the 2F roof outline (397 / 39A / 392 / 38D); no LEVEL text inside.
4. 412 = C2 (FP 1087), 415 = C5 (FP 108A) on SFRS (T-566 map).
