# T-792 fix rows on ARCH_TAKEOFF_V3.0.85: schedule-first vs candidate (columns, footings)

Rule: MARK_BY_OUTLINE_FIT_V1 (proposed, research/agents_t792/fill_t792.py) + company default 'schedule governs a column'

## Summary

```
{
 "lines_changed": 2,
 "lines_new": 0,
 "column_m3_before": 33.9244,
 "column_m3_after": 33.8339,
 "column_delta_m3": -0.0905,
 "freelancer_column_m3": 28.5465,
 "column_vs_freelancer_before": "+5.38 m3 (+18.8 %)",
 "column_vs_freelancer_after": "+5.29 m3 (+18.5 %)",
 "blank_lines_before_after": "0 / 0 (COLUMN, FOOTING, NECK)",
 "acceptance": "per storey schedule-first vs candidate: GF within 5 %; 1F / 2F outside only by the planted columns (like-for-like within 5 %), both figures carried with the cause"
}
```

## Changed lines

| line | before | after | label | basis | drawing-derived | other mark |
|---|---|---|---|---|---|---|
| L-694a75c84dd6e4bb4491 | 0.3100 | 0.3875 | DEFAULT | 10AE GF: mark C by MARK_BY_OUTLINE_FIT_V1 (setting-out plan (text 20D) C, foundation plan (text 1681) C3; FOU 10AE 0.50 x 0.30, GF roof slab plan GFRS 350 0.40 x 0.20 (single-storey annex); C fits every outline, C3 does not); schedule GF C 20 x 50 governs (company default) = 0.100 m2 x annex h 3.875 = +4.30 printed finished - 0.175 roof build-up default - base +0.25 (T-757 basis, kept) = 0.3875 m3; D-66 answer replaces it | 0.3100 | 0.4844 |
| L-1dc713c83bf62e525ff2 | 0.8400 | 0.6720 | DEFAULT | 10E0 1F: mark C7 by MARK_BY_OUTLINE_FIT_V1 (setting-out plan (text 24E) C7, foundation plan (text 10E1) C8; FOU 10E0 0.80 x 0.30, GFRS 380 0.80 x 0.25, FFRS 69A 0.80 x 0.25; C7 fits every outline, C8 does not); schedule 1F C7 20 x 80 governs (company default) = 0.160 m2 x 1F h 4.20 (+5.45 .. +9.65) = 0.6720 m3; D-66 answer replaces it | 0.8400 | 0.756 |

## Confirmed, no change

| line | m3 | label | basis |
|---|---|---|---|
| L-4c4496579e5bfa20ae9f | 0.9000 | DRAWING-READ | 10E0 GF: mark C7 by MARK_BY_OUTLINE_FIT_V1 (setting-out plan (text 24E) C7, foundation plan (text 10E1) C8; FOU 10E0 0.80 x 0.30, GFRS 380 0.80 x 0.25, FFRS 69A 0.80 x 0.25; C7 fits every outline, C8 does not); schedule GF C7 25 x 80 governs (company default) = 0.200 m2 x GF h 4.50 (slab tops +0.95 .. +5.45) = 0.9000 m3; drawn section = scheduled section: both methods agree, mark only (was carried as C8) |
| L-2ac3c9b3b4c2221a0299 | 0.5880 | DRAWING-READ | PC-1F-A: planted column, no schedule row by type (legend P.C); text 544 'P.C 20x70', GFRS 329 / FFRS 66A drawn 0.70 x 0.20 agree: 0.14 m2 x 4.2 = 0.5880 m3; the freelancer carries the same section; ENGINE_RIGHT vs schedule-first (which cannot see a P.C) |
| L-31a0424bd0efcc93efba | 0.4200 | DRAWING-READ | PC-1F-B: planted column, no schedule row by type (legend P.C); text 548 'P.C 20x50', GFRS 386 / FFRS 69D drawn 0.50 x 0.20 agree: 0.10 m2 x 4.2 = 0.4200 m3; the freelancer carries the same section; ENGINE_RIGHT vs schedule-first (which cannot see a P.C) |
| L-541c7e565bb93ecdb78b | 0.3325 | DEFAULT | PC-2F: planted column, no schedule row by type (legend P.C); text 77C 'P.C 20x50' (drawn FFRS 77B 0.20 x 0.40; printed size governs, T-757 DEFAULT): 0.10 m2 x 3.325 = 0.3325 m3; the freelancer carries the same section; ENGINE_RIGHT vs schedule-first (which cannot see a P.C) |

## CONFLICT members (two sheets, two marks)

| member | tags | outlines | fit by mark | mark |
|---|---|---|---|---|
| 10AE | {"setting-out plan (text 20D)": "C", "foundation plan (text 1681)": "C3"} | FOU 10AE 0.50 x 0.30, GF roof slab plan GFRS 350 0.40 x 0.20 (single-storey annex) | {"C": {"FOUNDATION": true, "GF": true}, "C3": {"FOUNDATION": true, "GF": false}} | C (FITS_EVERY_OUTLINE) |
| 10E0 | {"setting-out plan (text 24E)": "C7", "foundation plan (text 10E1)": "C8"} | FOU 10E0 0.80 x 0.30, GFRS 380 0.80 x 0.25, FFRS 69A 0.80 x 0.25 | {"C7": {"FOUNDATION": true, "GF": true, "1F": true}, "C8": {"FOUNDATION": true, "GF": true, "1F": false}} | C7 (FITS_EVERY_OUTLINE) |

## Per storey (m3)

| storey | candidate before | after | schedule-first | after vs schedule | planted | like-for-like | freelancer | after vs freelancer | cause |
|---|---|---|---|---|---|---|---|---|---|
| GF | 19.8119 | 19.8894 | 20.0250 | -0.7 % | 0.0000 | -0.7 % | 17.4374 | +2.45 m3 (+14.1 %) | storey frame: candidate drawing-read bases (annex 3.875 on 4 C members incl. 10AE, +0.25 base 5.20 on C3 / C5) vs the flat 4.50 schedule-first frame: ENGINE_RIGHT (T-576; heights are not in the schedule) |
| 1F | 10.3320 | 10.1640 | 9.1560 | +11.0 % | 1.0080 | -0.0 % | 7.7280 | +2.44 m3 (+31.5 %) | PC-1F-A / PC-1F-B planted columns 1.008: no schedule row by type; ENGINE_RIGHT (printed P.C size texts, the freelancer carries both) |
| 2F | 3.7805 | 3.7805 | 3.5280 | +7.2 % | 0.3325 | -2.3 % | 3.3810 | +0.40 m3 (+11.8 %) | PC-2F 0.3325 (no schedule row by type, ENGINE_RIGHT) and the 2F frame 4.075 (13.90 - 0.175 roof DEFAULT - 9.65) vs 4.20 on six members -0.075: ENGINE_RIGHT (closer drawing read, both DEFAULT) |

## Footings (no fix row)

Candidate 66.5790 vs schedule-first 66.5220: +0.057 m3 (+0.09 %); vs freelancer 65.634: +0.945 m3 (+1.44 %). Hand check: F12: schedule 4.40 x 3.20 x 0.70 = 9.8560 m3, one drawn outline TAGGED.

- F10 + F drawn as one outline 3.25 x 1.40 x 0.50 (owner Q-31 C 'bigger area') vs schedule rows F10 1.96 + F 0.216: +0.099 RULE_DIFFERENCE (Q-31 C governs)
- FN clipped by F9: notch 0.40 x 0.35 x 0.30 owned by F9 (R-CONC-OWN-1): -0.042 ENGINE_RIGHT
- F7: schedule row, no plan symbol: no member, no line (designer list)

## Necks (count only)

Candidate 36 vs schedule-first 36: totals agree 36 = 36; per mark only the two CONFLICT members move (10AE C3 -> C, 10E0 C8 -> C7); their neck lines already carry the 30 x 50 / 30 x 80 sections of the resolved marks (L-15b8ad39 0.4272 = 0.24 x 1.78): mark only, no m3 change; heights stay (Q-21).

| mark | candidate | schedule-first |
|---|---|---|
| C | 5 | 6 |
| C1 | 1 | 1 |
| C10 | 1 | 1 |
| C11 | 2 | 2 |
| C2 | 4 | 4 |
| C3 | 6 | 5 |
| C4 | 2 | 2 |
| C5 | 3 | 3 |
| C6 | 1 | 1 |
| C7 | 1 | 2 |
| C8 | 2 | 1 |
| C9 | 2 | 2 |
| CN | 6 | 6 |

## Storey outlines with no schedule mark (all named; no missing member)

| storey | outline | status | size m | reading |
|---|---|---|---|---|
| GF | P322@67413,45123 | UNSCHEDULED_OUTLINE | [0.2, 1.0] | GF start of the turned T.C at C9 / F9 (note 324; T-217 s.7 item 4): the GF member is the SOLID 37A, carried |
| GF | P329@56705,37848 | UNSCHEDULED_OUTLINE | [0.7, 0.2] | GF start outline of PC-1F-A (text 544 'P.C 20x70'): line L-2ac3c9b3 |
| GF | P344@73263,43748 | AMBIGUOUS_OUTLINE | [0.2, 0.5] | GF C3 at FP 10A0, drawn 0.20 x 0.50 vs GR 25 x 50 (T-256 row 55): carried as a candidate C3 line at the schedule section; schedule-first bound that C3 tag to 31B instead (31B = ANSI35 start of the turned C8 T.C at F8, T-217 s.2): count and m3 neutral (one C3 at GR 25 x 50 x 4.50 either way) |
| GF | P386@71463,37848 | AMBIGUOUS_OUTLINE | [0.5, 0.2] | GF start outline of PC-1F-B (text 548 'P.C 20x50'): line L-31a0424b |
| 1F | P66A@17981,37848 | UNSCHEDULED_OUTLINE | [0.7, 0.2] | 1F PC-1F-A body: line L-2ac3c9b3 |
| 1F | P69D@32739,37848 | AMBIGUOUS_OUTLINE | [0.5, 0.2] | 1F PC-1F-B body: line L-31a0424b |
| 1F | P77B@26269,44830 | UNSCHEDULED_OUTLINE | [0.2, 0.4] | 1F roof start outline of PC-2F (text 77C 'P.C 20x50'): line L-541c7e56 |
| 2F | P778@-12455,44830 | UNSCHEDULED_OUTLINE | [0.2, 0.4] | 2F PC-2F body: line L-541c7e56 |

Not changed: formwork of 10AE / 10E0 (face-ledger ESTIMATE lines L-7fe93376 / L-ae0d688f): perimeter +0.20 x 3.875 = +0.78 m2 and -0.10 x 4.20 = -0.42 m2 (net +0.36, gross 1.20 m2 = 0.3 % of the 384.1 m2 column formwork line set, below 1 %): logged, not restated
