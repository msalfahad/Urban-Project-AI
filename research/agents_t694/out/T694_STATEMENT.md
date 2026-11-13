# T-694 Concrete reconciliation statement round 3 (V3.0.68; concrete = V3.0.67)

Candidate ARCH_TAKEOFF_V3.0.68: `research/agents_t672/out/LINE_INDEX_V3_0_68.json` sha256 fc485958b2d1, lines d1de50cb; master `rules/coverage/BOQ_FAMILY_MASTER_1.69.0.json` census agrees on 14 families. development villa; not an accuracy claim; nothing released (the released default V2.9 + route G is unchanged); no quantity changed; the reference is never a quantity.

Partition (R-T694-1, whole STR.CONC): {'RELEASED': 317, 'HELD_BOUNDED': 110, 'HELD_BLANK': 80, 'EXCLUDED': 90}.

## Family subtotal -> trade total (m3; buckets never summed together)

| Family | Item | Lines | Released n / m3 | Bounded n / low .. high | Blank n (DESIGNER / OPEN BOUND / MEASURABLE NOW) | Excl | Engine range |
|---|---|---|---|---|---|---|---|
| B7-12 | Stair concrete | 12 | 6 / 5.368881 | 0 / 0 .. 0 | 5 (5 / 0 / 0) | 1 | 5.368881 .. OPEN |
| B9-02 | Lintels | 61 | 16 / 1.016 | 24 / 1.361 .. 2.050636 | 21 (6 / 15 / 0) | 0 | 2.377 .. OPEN |
| B10-01 | Blinding | 8 | 1 / 12.734438 | 5 / 7.640374 .. 13.466198 | 2 (2 / 0 / 0) | 0 | 20.374812 .. OPEN |
| B10-02 | Isolated / combined footings | 26 | 25 / 64.3040 | 1 / 2.176 .. 2.275 | 0 (0 / 0 / 0) | 0 | 66.4800 .. 66.5790 |
| B10-03 | Necks | 36 | 0 / 0 | 32 / 8.7724 .. 11.3460 | 4 (4 / 0 / 0) | 0 | 8.7724 .. OPEN |
| B10-04 | Strap / ground beams | 71 | 35 / 27.151055 | 11 / 1.207878 .. 5.750071 | 20 (19 / 1 / 0) | 5 | 28.358933 .. OPEN |
| B10-05 | Ground slab | 26 | 26 / 21.640885 | 0 / 0 .. 0 | 0 (0 / 0 / 0) | 0 | 21.640885 .. 21.640885 |
| B10-06 | Columns | 72 | 30 / 19.7765 | 22 / 10.26435 .. 13.27025 | 7 (7 / 0 / 0) | 13 | 30.04085 .. OPEN |
| B10-07 | Beams | 192 | 112 / 66.920678 | 14 / 5.983229 .. 8.412710 | 12 (12 / 0 / 0) | 54 | 72.903907 .. OPEN |
| B10-08 | Suspended slabs | 75 | 62 / 60.280155 | 0 / 0 .. 0 | 0 (0 / 0 / 0) | 13 | 60.280155 .. 60.280155 |
| B10-09 | Domes / rings | 5 | 2 / 5.081362 | 0 / 0 .. 0 | 1 (1 / 0 / 0) | 2 | 5.081362 .. OPEN |
| B10-10 | Pool / tank / lift pit / pump room | 7 | 2 / 7.202297 | 0 / 0 .. 0 | 3 (3 / 0 / 0) | 2 | 7.202297 .. OPEN |
| B10-11 | Boundary wall concrete | 2 | 0 / 0 | 1 / 5.6392 .. 11.0328 | 1 (1 / 0 / 0) | 0 | 5.6392 .. OPEN |
| B10-12 | RC parapets | 4 | 0 / 0 | 0 / 0 .. 0 | 4 (4 / 0 / 0) | 0 | 0 .. OPEN |
| **TRADE** | all STR.CONC | 597 | 317 / 291.476251 | 110 / 43.044431 .. 67.603665 | 80 (64 / 16 / 0) | 90 | 334.520682 .. OPEN |

Floors beside (blank lines, never in the range): L-061e18cf >= 0.355017; L-274b1125 >= 0.048; L-6bf14711 >= 0.1125; L-893c3db1 >= 0.915529; L-9ec762c0 >= 0.036; sum 1.467046 m3.

## Before (V3.0.66, T-683) -> after (V3.0.68)

released 291.476251 -> 291.476251; bounded 101 42.014281 .. 66.193191 -> 110 43.044431 .. 67.603665 (line moves: low +1.030150, high +1.410474, exact); blank 89 -> 80.

| Line | Element | Before | After | Cause class |
|---|---|---|---|---|
| L-1a078491 | LINTEL:D-GF-01 | blank | 0.056 .. 0.066716 | DESIGNER ITEM |
| L-3af715c6 | LINTEL:W01 | blank | 0.08 .. 0.108 | DESIGNER ITEM |
| L-47882fa3 | LINTEL:W13 | blank | 0.08 .. 0.108 | DESIGNER ITEM |
| L-541c7e56 | HL:PLANTED_COLUMN:PC-2F:CONCRETE | blank | 0.1824 .. 0.35 | DESIGNER ITEM |
| L-71998da6 | LINTEL:D-GF-02 | blank | 0.036 .. 0.042708 | DESIGNER ITEM |
| L-a7848a35 | LINTEL:D-GF-03 | blank | 0.052 .. 0.058 | DESIGNER ITEM |
| L-a7b8b292 | LINTEL:D-1F-05 | blank | 0.036 .. 0.0628 | DESIGNER ITEM |
| L-fad18af6 | P-C:COL:SH12:C3@238374,54773|GF | blank | 0.41175 .. 0.50625 | DESIGNER ITEM |
| L-fd68db05 | LINTEL:D-GF-07 | blank | 0.096 .. 0.108 | DESIGNER ITEM |

Restated (R-T683-1): 11 lines, MEASURABLE NOW -> L-1a078491 DESIGNER ITEM, L-274b1125 OPEN BOUND, L-3af715c6 DESIGNER ITEM, L-47882fa3 DESIGNER ITEM, L-541c7e56 DESIGNER ITEM, L-71998da6 DESIGNER ITEM, L-9ec762c0 OPEN BOUND, L-a7848a35 DESIGNER ITEM, L-a7b8b292 DESIGNER ITEM, L-fad18af6 DESIGNER ITEM, L-fd68db05 DESIGNER ITEM.

## After T-693 (PROPOSED until wired (T-693, lane I, Checker Gate B); never the candidate, never released)

| Line | Element | Before | After | Source |
|---|---|---|---|---|
| L-919a5749 | P-C:COL:SH12:C2@252679,64225|2F | ['0.303000', '0.425000'] | 0.328700 .. 0.425000 | T-689 R-T689-1 (B8 joint, merged 66ffd421) |
| L-9f5a6470 | P-C:COL:SH12:C@238150,57853|GF | blank (OPEN) | 0.263520 .. 0.405000 | T-689 conflict_bound (merged 66ffd421) |
| L-c0b3340a | P-C:COL:SH12:C@233893,56561|GF | blank (OPEN) | 0.263520 .. 0.405000 | T-689 conflict_bound (merged 66ffd421) |
| L-e6c1c9a7 | P-C:COL:SH12:C@235241,51296|GF | blank (OPEN) | 0.263520 .. 0.405000 | T-689 conflict_bound (merged 66ffd421) |
| L-694a75c8 | P-C:COL:SH12:C3@241094,51256|GF | blank (OPEN) | 0.263520 .. 0.506250 | T-689 conflict_bound (merged 66ffd421) |
| L-bc01297b | P-C:COL:SH12:C5@255627,63526|2F | blank (OPEN) | 0.328700 .. 0.510000 | T-689 conflict_bound (merged 66ffd421) |
| B10-06 PROPOSED | Columns | 72 | 30 / 19.7765 | 27 / 11.67283 .. 15.50150 | 2 (2 / 0 / 0) | 13 | 31.44933 .. OPEN |
| **TRADE PROPOSED** | all STR.CONC | 597 | 317 / 291.476251 | 115 / 44.452911 .. 69.834915 | 75 (59 / 16 / 0) | 90 | 335.929162 .. OPEN |

## Reference comparison, apart (key map T001B)

| Key | Reference | Engine released | Engine range | Held | Ref - released | % | After T-693 range (PROPOSED) |
|---|---|---|---|---|---|---|---|
| CONC.BLINDING | 47.055000 | 12.734438 | 20.374812 .. OPEN | 5 + 2 | 34.320562 | suppressed | 20.374812 .. OPEN |
| CONC.FOOTING | 77.630500 | 67.6945 | 75.5392 .. 81.6556 | 4 + 0 | 9.936000 | suppressed | 75.5392 .. 81.6556 |
| CONC.GROUND | 75.090000 | 45.401440 | 46.579818 .. OPEN | 9 + 20 | 29.688560 | suppressed | 46.579818 .. OPEN |
| CONC.COLUMN | 39.751500 | 19.7765 | 38.81325 .. OPEN | 54 + 11 | 19.975000 | suppressed | 40.22173 .. OPEN |
| CONC.BEAM | 65.965875 | 66.920678 | 72.903907 .. OPEN | 14 + 12 | -0.954803 | suppressed | 72.903907 .. OPEN |
| CONC.SLAB | 59.817400 | 60.280155 | 60.280155 .. 60.280155 | 0 + 0 | -0.462755 | -0.77 | 60.280155 .. 60.280155 |
| CONC.STAIR_DOME | 21.832800 | 10.450243 | 10.450243 .. OPEN | 0 + 6 | 11.382557 | suppressed | 10.450243 .. OPEN |
| CONC.POOL | 12.348000 | 7.202297 | 7.202297 .. OPEN | 0 + 1 | 5.145703 | suppressed | 7.202297 .. OPEN |

- CONC.SLAB -0.462755 m3 (-0.77 %): UNRESOLVED (ambiguous scope), residual named. T-683 storey bridge: GF +0.050478, 1F -0.556333, 2F +0.043100 (re-add exactly). T-688 (merged a62b3024) 1F: engine geometry = own re-measure (ENGINE_RIGHT on every drawn panel, noise +0.000263); his typed 120 m2 rounding -0.080 .. +0.080; scope 2.977 .. 3.977 m2 of drawn panels not in his 120 = -0.636333 .. -0.476333 m3 UNRESOLVED (62 panel subsets fit; none named). 2F: a thickness-zone split (0.16: 31.25 vs 31.84 m2; 0.18: 13.635 vs 13.35 m2), not investigated.
- CONC.BEAM cover 65.965875 vs his rows 66.093875: omitted 0.128 (0.20 x 0.40 x 1.60, first 1F row outside his 1F sub-total; R-T683-3); engine released 66.920678: cover - released -0.954803, rows - released -0.826803; REFERENCE ARITHMETIC (his rows), % suppressed: the key holds HELD lines.

## PC-2F section (R-T694-3)

Own read this run of Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (3153037 B, sha256 9f9d1179; decoded into .work/private only): every 'P.C' text in the file = ['P.C 20x50', 'P.C 20x70'] (handles 544, 548, 77C), each with a 3-vertex leader on S-TEXT-SLAB; outlines and leader ends relative to the text

- text 544: ASSOCIATED -> 329 (LEADER; gap 311 mm, next 1059 mm; outline nearest the text itself: ['359', 989])
- text 548: ASSOCIATED -> 386 (LEADER; gap 311 mm, next 939 mm; outline nearest the text itself: ['371', 1547])
- text 77C: ASSOCIATED -> 77B (LEADER; gap 298 mm, next 2652 mm; outline nearest the text itself: ['67C', 348])

Searched: this run: every TEXT / MTEXT / DIMENSION of the ST DXF (no 'PLANT' / 'CARRYING' text, no size text or dimension within 0.60 m of 77B / 778); merged: T-220 (ST p.15 'beam carrying planted col.' detail, generic, no size; legend p.3-p.6; no schedule row for P.C), T-217 / T-256 (Checker-verified: p.9 schedule, slab plans, sections A-A .. D-D, PDF plot = copy of the DXF)

Result: no section, detail, dimension or schedule row fixes the PC-2F section: the only print is its own leader text 77C 'P.C 20x50' (leader to 77B, R-T694-3), against the outline 0.20 x 0.40 drawn on both FFRS 77B and SFRS 778; the p.15 'beam carrying planted col.' detail is generic (no size; T-220). DESIGNER ITEM: proposed addition to D-66 (which section is built), quantity 0.08 .. 0.10 m2 x 2.28 .. 3.50 m, already inside L-541c7e56 0.1824 .. 0.35.

## Cause register (R-T694-4)

- GAP L-541c7e56 FFRS 77B SECTION: cause with no designer item (None)
- GAP L-9f5a6470 GFRS 34A SECTION: member not in D-66's registered list (D-66)
- GAP L-c0b3340a GFRS 34D SECTION: member not in D-66's registered list (D-66)
- GAP L-e6c1c9a7 GFRS 356 SECTION: member not in D-66's registered list (D-66)
- GAP L-694a75c8 GFRS 350 SECTION: member not in D-66's registered list (D-66)
- GAP L-bc01297b SFRS 415 SECTION: member not in D-66's registered list (D-66)
- SPURIOUS L-fad18af6 D-66 readings ['0.125', '0.125']: SECTION cause on a line whose readings agree

## Checker re-measure list (not re-measured before)

1. L-541c7e56: PC-2F section association: text FFRS 77C 'P.C 20x50' with leader 77F; the leader far end is 298 mm from outline 77B (0.20 x 0.40) and 2,652 mm from the next outline; the text itself is 348 mm from 67C (0.20 x 0.50, the 1F C2); compare 544 / 545 -> 329 and 548 / 549 -> 386 (311 mm each)
2. L-bc01297b: SFRS 415 drawn 0.60 x 0.20 (schedule C5 2ND 20 x 50): no size text and no dimension within 0.60 m (only 79F '4ø16/Top', a slab bar text, 434 mm)
3. L-694a75c8: GFRS 350 drawn 0.40 x 0.20 (schedule C3 GR 25 x 50): no text and no dimension within 0.60 m

## HELD lines (190)

| Family | Line | Code | Bound m3 | Cause class | Cause | Source |
|---|---|---|---|---|---|---|
| B10-01 | L-080c97f5 | BLINDING | 0.435 .. 0.59 | DESIGNER ITEM | Q-31 C (F10 + F readings A / B) | T-669 census (V3.0.63) |
| B10-01 | L-10032bf9 | BLINDING | 0.0 .. 0.189 | DESIGNER ITEM | D-14 (blinding beyond the plot line) | T-669 census (V3.0.63) |
| B10-01 | L-16b95607 | BLINDING | 2.256 .. 2.352 | OPEN BOUND | FF lift-raft blinding projection drawn, not dimensioned (ST p.14) | T-669 census (V3.0.63) |
| B10-01 | L-35382b18 | BLINDING | 0.0 .. 0.912684 | DESIGNER ITEM | D-15 (blinding under straps) | T-669 census (V3.0.63) |
| B10-01 | L-7a5214a3 | BLINDING | 4.949374 .. 9.422514 | DESIGNER ITEM | D-33 / D-35 (ground-beam sections under the blinding) | T-669 census (V3.0.63) |
| B10-01 | L-893c3db1 | BLINDING | blank | DESIGNER ITEM | pool blinding HELD LOWER_ONLY >= 0.915529 (T-667 MERGED; wired T-668 ADD_LOWER_ONLY): projection beyond the wrap drawn, not dimensioned (C4) and F8 / F4 / FN fo | T-667 / T-668 (classed by T-679 from the merged text; no census row) |
| B10-01 | L-d0313e5d | BLINDING | blank | DESIGNER ITEM | Q-28 (pad count; pad blinding projections not dimensioned) | T-669 census (V3.0.63) |
| B10-02 | L-164ae9d3 | FOOTING | 2.176 .. 2.275 | DESIGNER ITEM | Q-31 C readings under the V3.0.11 conflict record (F10 + F); T-595 third reading named WAITING | T-669 census (V3.0.63) |
| B10-03 | L-05a99150 | NECK | 0.235 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-12f3d8b9 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-132cf605 | NECK | 0.5874 .. 0.66 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-15b8ad39 | NECK | 0.4272 .. 0.54 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-15d9da9b | NECK | 0.0972 .. 0.18 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-1a9e4696 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-31494639 | NECK | 0.267 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-34346cb4 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-3f7b9501 | NECK | 0.2895 .. 0.3225 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-46f2b702 | NECK | 0.282 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-486cd9a0 | NECK | 0.3384 .. 0.378 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-48f2e06e | NECK | 0.267 .. 0.3 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-4ec473f7 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-4ef35980 | NECK | 0.1062 .. 0.189 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-516989b8 | NECK | 0.267 .. 0.3 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-53d0b6af | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-5aec8a00 | NECK | 0.2895 .. 0.3225 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-5efd9ac6 | NECK | 0.3384 .. 0.378 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-6a2040e0 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-734ff1a7 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-85df35f1 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-8eb74a02 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-953e87a3 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-995eca94 | NECK | 0.3792 .. 0.432 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-ae1bd9cb | NECK | 0.237 .. 0.27 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-b21cbf65 | NECK | 0.519 .. 0.585 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-b4c234c8 | NECK | 0.5874 .. 0.66 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-bbad8cdb | NECK | 0.3738 .. 0.462 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-bd741a3f | NECK | 0.2376 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-c1e80218 | NECK | 0.1944 .. 0.36 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-c8c07db4 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-dd3c32e4 | NECK | 0.177 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-dd6d1141 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-efe50185 | NECK | 0.3738 .. 0.42 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-f54b7b2a | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-fc622ff3 | NECK | 0.4806 .. 0.54 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-04 | L-00465df9 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-0bb78acc | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-0c5ede7f | GROUND_BEAM | 0.1125 .. 0.15 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-0e852cca | GROUND_BEAM | 0.216 .. 0.288 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-1487bdda | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-21795b35 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-3284f440 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-402dbe61 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-4783c6e1 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-5af89b9f | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-62243c74 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-6bf14711 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-81444e22 | GROUND_BEAM | 0.1305 .. 0.174 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-95a1f198 | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-970bac56 | GROUND_BEAM | 0.098008 .. 0.130678 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-a55bfa01 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-a8c5c32c | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-b4a13a43 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-be6708e0 | GROUND_BEAM | blank | OPEN BOUND | neck-cut sliver section not printed (R-GB-NECK-CUT-1) | T-669 census (V3.0.63) |
| B10-04 | L-c0b7102a | GROUND_BEAM | 0.20925 .. 0.279 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-cfb4555c | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-d53e5eb0 | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-d8b98b14 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-e16c9807 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-e2134034 | GROUND_BEAM | 0.108 .. 0.144 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-e24946df | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-f0e25ad2 | GROUND_BEAM | 0.108 .. 0.144 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-f24cf117 | GROUND_BEAM | 0.19612 .. 0.261493 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-fb7a6431 | GROUND_BEAM | 0.0 .. 3.5256 | DESIGNER ITEM | Q-28 (RFI) | T-669 census (V3.0.63) |
| B10-04 | L-abd65e1b | STRAP | 0.0 .. 0.385 | DESIGNER ITEM | Q-31 C (SB1 end inside F10 + F) | T-669 census (V3.0.63) |
| B10-04 | L-c823e0db | STRAP | 0.0295 .. 0.2683 | DESIGNER ITEM | D-15 (strap soffit) | T-669 census (V3.0.63) |
| B10-06 | L-0ede77cf | COLUMN | blank | DESIGNER ITEM | D-39 / D-44 | T-669 census (V3.0.63) |
| B10-06 | L-1dc713c8 | COLUMN | 0.756 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-26f6b6f2 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-291ba2dd | COLUMN | 0.42 .. 0.504 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-33a9b772 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-43dae3d6 | COLUMN | 0.36 .. 0.45 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-4aed92c1 | COLUMN | 0.756 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-4c449657 | COLUMN | 0.9 .. 1.0125 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-53f223b0 | COLUMN | 0.4242 .. 0.595 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-541c7e56 | COLUMN | 0.1824 .. 0.35 | DESIGNER ITEM | PC-2F: section drawn 0.20 x 0.40 (FFRS 77B, SFRS 778) vs its own leader text FFRS 77C 'P.C 20x50' (T-694 own read: the leader reaches 77B) -> proposed D-66 addi | T-694 restatement of T-682 s.2 + T-689 s.3 (register gap F-T689-2) |
| B10-06 | L-694a75c8 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-755eb56b | COLUMN | 0.756 .. 1.05 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-831f6fe3 | COLUMN | 0.42 .. 0.63 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-85809d3d | COLUMN | 0.672 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-8de64040 | COLUMN | 0.45 .. 0.5625 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-8f8ad257 | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-919a5749 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-9cb26d86 | COLUMN | 0.36 .. 0.45 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-9f5a6470 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-a87ea657 | COLUMN | 0.504 .. 0.735 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-bc01297b | COLUMN | blank | DESIGNER ITEM | D-39 / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c0b3340a | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c10e2945 | COLUMN | blank | DESIGNER ITEM | D-39 / D-44 / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c677b628 | COLUMN | 0.42 .. 0.63 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-cc702b85 | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-d79d17d1 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-e112e2ad | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-e6c1c9a7 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-fad18af6 | COLUMN | 0.41175 .. 0.50625 | DESIGNER ITEM | annex C3 (GFRS 353 drawn 0.25 x 0.50 = schedule C3 GR 25 x 50, AGREE): top datum only, the annex roof slab top is not printed (D-39 / Q-54 B); low from R-T678-2 | T-694 restatement of T-682 s.2 + T-678 s.1 + T-566 registration |
| B10-07 | L-17c4238c | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-1fd49f3e | BEAM | 2.262872 .. 2.545691 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-2c7b0b1e | BEAM | 0.347 .. 0.4338 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-331d4bbe | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-377cb988 | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-39ca5340 | BEAM | 0.44255 .. 0.55323 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-43e804ba | BEAM | 0.4563 .. 0.5475 | DESIGNER ITEM | D-02 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-50667f69 | BEAM | 0.2875 .. 0.345 | DESIGNER ITEM | D-02 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-54e397fe | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-56d278be | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-60f09eec | BEAM | 0.335 .. 0.4188 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-634cefe5 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-67f3d325 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-7c3edce2 | BEAM | 0.112 .. 0.336 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-88ccf8d4 | BEAM | 0.212 .. 0.3975 | DESIGNER ITEM | D-03 (TWO_MARKS) | T-669 census (V3.0.63) |
| B10-07 | L-8d031491 | BEAM | 0.0904 .. 0.2712 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-9e489566 | BEAM | 1.013607 .. 1.266989 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-a9d5e7dc | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-ab37afa1 | BEAM | blank | DESIGNER ITEM | D-28 (RING) | T-669 census (V3.0.63) |
| B10-07 | L-aba59a21 | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-bb49e831 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-bef35462 | BEAM | 0.0 .. 0.025 | DESIGNER ITEM | BAND0030.2 depth companion 0 .. 0.025: strip depth B4 0.50 vs B7 0.75, no mark printed on the strip (T-642 FR-T642-2; wired T-671 ADD_COMPANION) | T-642 / T-671 (classed by T-679 from the merged text; no census row) |
| B10-07 | L-d62d2fcf | BEAM | 0.248 .. 0.744 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-dc8cbfc1 | BEAM | 0.112 .. 0.336 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-f83c4a46 | BEAM | 0.064 .. 0.192 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-fbb65dfd | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-09 | L-d5401fa8 | DOME | blank | DESIGNER ITEM | consultant 2026-10-24 G3 (upper-roof dome: no structural detail) | T-669 census (V3.0.63) |
| B10-10 | L-5ae06fda | LIFT | blank | DESIGNER ITEM | D-43 (lift tie beam section not printed) | T-669 census (V3.0.63) |
| B10-10 | L-684fcad3 | LIFT | blank | DESIGNER ITEM | D-43 (lift pit depth 'as per manufacturer') | T-669 census (V3.0.63) |
| B10-10 | L-b62a7065 | POOL | blank | DESIGNER ITEM | consultant 2026-10-23 row 3 / P-2 (pool steps not drawn) | T-669 census (V3.0.63) |
| B10-11 | L-cda8f415 | BOUNDARY_PAD | blank | DESIGNER ITEM | Q-28 (boundary columns 'SEE ARCH PLAN', none drawn: pad count) | T-669 census (V3.0.63) |
| B10-11 | L-6290a9f3 | BOUNDARY_WALL | 5.6392 .. 11.0328 | DESIGNER ITEM | boundary band 5.6392 .. 11.0328 wired by T-668: section B.W 20x60 vs typical 20x40 (designer RFI, Q-28; owner provisional A 8.4588 beside, not a released value) | T-683 from the T-669 census row ('wire in T-668; then Q-28 keeps it bounded') + Q-28 |
| B10-12 | L-030538dd | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-1d419b64 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-9a2c8116 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-b5ffc172 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B7-12 | L-061e18cf | STAIR | blank | DESIGNER ITEM | ST-03 E1 waist slab not drawn (S-9); the steps part AT_LEAST 0.355017 is beside (T-677 LOWER_ONLY, T-258 DRAWING-CONFIRMED risers) | T-683 from T-673 stairs row + T-677 s.1 (the split was wired as a floor beside) |
| B7-12 | L-659243ed | STAIR | blank | DESIGNER ITEM | C-ST-3 (junction section of the two plates 0.168 apart not drawn) | T-673 census (V3.0.64) |
| B7-12 | L-7863355d | STAIR | blank | DESIGNER ITEM | C-ST-4 / RFI-A04 (MS1-L: arch 10 fronts vs ST p.4 12; owner 2026-10-22 'MS1-L HELD'), D-67 / C-ST-3 (winder, turn soffit not drawn) | T-673 census (V3.0.64) |
| B7-12 | L-821032bc | STAIR | blank | DESIGNER ITEM | S-9 (waist thickness / support not printed) | T-673 census (V3.0.64) |
| B7-12 | L-b6b0354b | STAIR | blank | DESIGNER ITEM | D-08 / owner Q-50 / Q-51 (curved parts HELD), C-ST-3; CA level not stated (0 .. 0.09) | T-673 census (V3.0.64) |
| B9-02 | L-005334b6 | LINTEL | 0.04 .. 0.055 | DESIGNER ITEM | lintel W28: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-072bc37c | LINTEL | blank | DESIGNER ITEM | D-GF-09 (T-581 DRAWING CONFLICT: D120 1.00 frame in a 0.90 gap) | T-673 census (V3.0.64) |
| B9-02 | L-0d5e2e3a | LINTEL | blank | OPEN BOUND | the lift tie beam depth and level (D-43) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-1313767d | LINTEL | blank | OPEN BOUND | annex roof slab top (Q-54 B / D-39) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-17953d78 | LINTEL | blank | OPEN BOUND | the GF-W30 run (band) and its jamb evidence | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-1a078491 | LINTEL | 0.056 .. 0.066716 | DESIGNER ITEM | lintel D-GF-01: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-1c0e7646 | LINTEL | blank | OPEN BOUND | BM-2F-017 depth: REQUIRED for any depth <= 0.52 m on the drawn 2F slab-top bound (12.68 - 9.70 - D >= 2.20 + 0.20 + 0.06); above that the D-39 slab top decides | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-274b1125 | LINTEL | blank | OPEN BOUND | lintel D-GF-04: LOWER_ONLY wired by T-682: one end has no recorded stopper within the search limit (R-T678-3), so its high end is OPEN; the floor beside is the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-2c1c49db | LINTEL | blank | OPEN BOUND | dome ring soffit over 1F-W11 (T-227, designer) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-2efe4809 | LINTEL | 0.063 .. 0.12042 | DESIGNER ITEM | lintel P-1F-01 (T-650 bound): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceil | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-3af715c6 | LINTEL | 0.08 .. 0.108 | DESIGNER ITEM | lintel W01: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the cast | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-40e8c259 | LINTEL | 0.094 .. 0.26828 | DESIGNER ITEM | lintel W24: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-441ae5fe | LINTEL | 0.04 .. 0.055 | DESIGNER ITEM | lintel W05: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-47882fa3 | LINTEL | 0.08 .. 0.108 | DESIGNER ITEM | lintel W13: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the cast | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-4a12b894 | LINTEL | 0.054 .. 0.1185 | DESIGNER ITEM | lintel A-1F-01 (T-650 bound): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceil | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-53ef44d8 | LINTEL | 0.078 .. 0.081732 | DESIGNER ITEM | lintel W16: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-6057028f | LINTEL | 0.056 .. 0.069 | DESIGNER ITEM | lintel W19 (pier side 0.40): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceili | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-6692d02c | LINTEL | 0.056 .. 0.08048 | DESIGNER ITEM | lintel W20 (pier side 0.40): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceili | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-71998da6 | LINTEL | 0.036 .. 0.042708 | DESIGNER ITEM | lintel D-GF-02: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-78634467 | LINTEL | 0.092 .. 0.118 | DESIGNER ITEM | lintel W09: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-7d90a0fe | LINTEL | 0.0 .. 0.003 | DESIGNER ITEM | W19 / W20 pier remainder 0 .. 0.2 x 0.2 x (0.875 - 2 x 0.40) = 0.003: which of the two lintels runs over the 0.075 m is not drawn (owned once, never inside eith | T-683 from T-677 s.1 / s.3 (line added by T-677; no census row could exist) |
| B9-02 | L-7f9eb7cc | LINTEL | blank | OPEN BOUND | annex roof slab top (Q-54 B / D-39) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-882717b0 | LINTEL | 0.056 .. 0.06 | DESIGNER ITEM | lintel W10 (START 0.100 deficit at a column): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-8f69c407 | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
| B9-02 | L-96160886 | LINTEL | blank | OPEN BOUND | T-227 (designer) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-9ec762c0 | LINTEL | blank | OPEN BOUND | lintel D-1F-06: LOWER_ONLY wired by T-682: one end has no recorded stopper within the search limit (R-T678-3), so its high end is OPEN; the floor beside is the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-a500f10e | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
| B9-02 | L-a7848a35 | LINTEL | 0.052 .. 0.058 | DESIGNER ITEM | lintel D-GF-03: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-a7b8b292 | LINTEL | 0.036 .. 0.0628 | DESIGNER ITEM | lintel D-1F-05: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-aca2db3c | LINTEL | 0.064 .. 0.064 | DESIGNER ITEM | lintel W29 (low = high): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-b699ce0d | LINTEL | blank | DESIGNER ITEM | D-39 (2F roof datum / build-up) | T-673 census (V3.0.64) |
| B9-02 | L-b729bd63 | LINTEL | blank | OPEN BOUND | the A-GF-01 crown level (with the annex bound c_lo 2.744 above +0.30 under B4: REQUIRED if crown <= 2.484 above FFL) and its width | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-bf76c173 | LINTEL | 0.056 .. 0.134 | DESIGNER ITEM | lintel W23: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-bf88bf6f | LINTEL | blank | OPEN BOUND | the 1F stair-shaft landing member level / depth over W25 | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-c1e57b06 | LINTEL | blank | OPEN BOUND | W11 sill level (REQUIRED if head <= 2.234 above +0.30 under B9 0.75) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-d887eecf | LINTEL | blank | DESIGNER ITEM | D-45 | T-673 census (V3.0.64) |
| B9-02 | L-dd5b41a7 | LINTEL | 0.04 .. 0.055 | DESIGNER ITEM | lintel W21: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-df32d6f4 | LINTEL | blank | OPEN BOUND | side-passage FFL (REQUIRED if <= +0.30: CB7 bound c_lo 2.494, spare 0.034) and the START jamb stopper | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-e3917519 | LINTEL | blank | OPEN BOUND | W12 sill level (as W11) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-ed7aadd0 | LINTEL | 0.056 .. 0.134 | DESIGNER ITEM | lintel W07: bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; the length a | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-f269fabb | LINTEL | 0.04 .. 0.04 | DESIGNER ITEM | lintel W06 (low = high: deficit end 0.000): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the d | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-f68444ed | LINTEL | 0.04 .. 0.04 | DESIGNER ITEM | lintel W22 (low = high): bound wired by T-677 (R-T673-1 / -3, DRAWING-CONFIRMED bounds): low = opening + 0.40 bearing each side, high = the drawn jamb ceilings; | T-683 restatement of T-673 s.3 + T-677 s.3 (MEASURABLE NOW = 'wire it', done in V3.0.66) |
| B9-02 | L-f892163c | LINTEL | blank | OPEN BOUND | the 2F stair-shaft member level / depth over W27 | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-fd68db05 | LINTEL | 0.096 .. 0.108 | DESIGNER ITEM | lintel D-GF-07: bound wired by T-682 (R-T678-1 / -3, T-678 ledger): low = opening + 0.40 bearing at each end with >= 0.40 drawn, high = the drawn ceilings; the  | T-694 restatement of T-682 s.0 / s.3 (MEASURABLE NOW = 'wire it', done in V3.0.67) |
| B9-02 | L-fd8aaedc | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
