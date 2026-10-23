# T-233 Whole-line closure: CONC.FOOTING and CONC.BLINDING, every footing once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-23, run unknown. Research piece, not wired: no engine, candidate or released line changed;
integration is a lane I package after the Checker's verdict. Development villa, not an accuracy claim. Drawings named
by Drive folder and title; entities by DXF handle; sizes, areas and counts only.

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | FOUNDATION PLAN frame: 26 outlines, tags, FT / FTB schedule attributes, S-BOUN plot polyline 1658 |
| "ST7757.pdf" | 74da1523...337e3 | p.2 foundation plan (whole sheet 110 dpi; F10 corner 440 dpi), p.9 schedule of footings (110 dpi), p.13 typical footing and ground-beam details |
| freelancer RC workbook | (committed rows) | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, footings sheet rows 11-33, 'ورقة1' rows 15 / 17 |

Runs: released baseline A `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`
on head 17ed6f92: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4. Candidate ARCH_TAKEOFF_V3.0.7: `research/agents_t167/v304_run.py` then `research/agents_t193/v307_run.py` on the same copies: V3_0_7_BOQ_LINES.csv **197c5599 REPRODUCED** (= SCOREBOARD v2 16:58). V3.0.8 (T-231) is READY, not on the working branch: not run.
Tools: `t233_extract.py` (DXF -> `ALSENAN_FOOTING_INPUT.json`, values only), `footing_line.py` (pure rules),
`t233_alsenan_check.py` (ledger + summary); tests `tests/t233_footing_line` (20).

## 1. The physical elements (ERS s.2.1)

- FOOTING (BOQ CONC.FOOTING, m3): the RC solid of one drawn outline on the foundation plan. Plan: drawn outline and
  schedule row L x W (two sources, either orientation, 5 mm tolerance); depth H: schedule p.9 only (the typical details
  print 'D' / 'AS PER SCHEDULE'; read twice, DXF FT / FTB attributes and PDF p.9, identical, one printed source).
- The keyed reference line CONC.FOOTING (tests/alsenan/T001B_KEY_MAP.json) is WIDER than the footings: STR.CONC.FOOTING
  + STR.CONC.STRAP + STR.CONC.BOUNDARY_WALL (the freelancer's 'footings + straps + perimeter tie beam'). A whole-line
  verdict covers all three.
- BLINDING (CONC.BLINDING, m3): the 10 cm plain-concrete layer under each footing, plan = outline + 0.10 each side
  (p.13 second typical detail '10 | L x W | 10', '10cm Plain con.'); between blinding and footing a 2 cm membrane and
  a 5 cm screed (T-206 vector read): UNDERLAY, another trade (T-219 waterproofing), never concrete. The keyed line
  STR.CONC.BLINDING also carries the ground-beam and strap blinding (p.13 ground-beam sections '10 | 30 | 10').

## 2. Footing table (each outline once; ALSENAN_FOOTING_INPUT.json, LEDGER_T233.csv)

Population: 26 outlines in the foundation frame (12 unit-square F inserts scaled to size, 11 S-FOOTINGS polylines of
which 3 open where a strap enters, 3 four-LINE squares). The ground-beam plan frame draws 3 neck-footing squares and
CN / FN tags again on S-FOOTINGS: outside the foundation frame, excluded (one element, one sheet; ERS 2023-10-23 lesson
of T-193). Every tag bound to one outline (inside, else the nearest outline within 1.0 m whose drawn size equals the
tag's schedule row; ties never guessed): 0 unbound. Visual check on p.2: same 26 outlines and tags.

| Type | n | Schedule L x W x H | Drawn (each) | Status | m3 by hand |
|---|---|---|---|---|---|
| F (C/F) | 4 | 0.90 x 0.80 x 0.30 | 0.90 x 0.80 / 0.80 x 0.90 | AGREE | 4 x 0.216 = 0.864 |
| F2 | 2 | 1.90 x 1.70 x 0.35 | 1.90 x 1.70 | AGREE | 2.261 |
| F3 | 2 | 1.60 x 1.40 x 0.30 | 1.60 x 1.40 / 1.40 x 1.60 | AGREE | 1.344 |
| F4 | 2 | 2.20 x 2.00 x 0.40 | 2.20 x 2.00 | AGREE | 3.520 |
| F5 | 2 | 2.40 x 2.10 x 0.40 | 2.40 x 2.10 | AGREE | 4.032 |
| F6 | 1 | 2.60 x 2.20 x 0.50 | 2.20 x 2.60 (open, SB2 enters) | AGREE | 2.860 |
| F7 | 0 | 3.00 x 2.50 x 0.50 | not drawn | scheduled, not on the plan: count 0 (not HELD) | 0 |
| F8 | 1 | 4.00 x 3.60 x 0.50 | 4.00 x 3.60 | AGREE | 7.200 |
| F9 | 1 | 3.40 x 2.70 x 0.55 | 3.40 x 2.70 | AGREE | 5.049 |
| F11 | 1 | 3.50 x 1.50 x 0.50 | 3.50 x 1.50 (open, SB2 enters) | AGREE | 2.625 |
| F12 | 1 | 4.40 x 3.20 x 0.70 | 4.40 x 3.20 (also dimensioned on p.2) | AGREE | 9.856 |
| F13 | 1 | 4.30 x 2.40 x 0.50 | 4.30 x 2.40 | AGREE | 5.160 |
| F14 | 1 | 3.80 x 3.30 x 0.50 | 3.80 x 3.30 | AGREE | 6.270 |
| F15 | 1 | 1.80 x 1.00 x 0.40 | 1.80 x 1.00 | AGREE | 0.720 |
| FF (lift) | 1 | 4.60 x 4.50 x 0.55 | 4.60 x 4.50 | AGREE (pit base = FF, T-204: listed once) | 11.385 |
| FN | 4 | 1.00 x 1.00 x 0.30 | 3 x 1.00 x 1.00 + 1 drawn clipped (180C, 0.86 m2) | 3 AGREE + 1 CLIPPED | 0.900 + 0.258 = 1.158 |
| **measured** | **25** | | | | **64.304** |
| F10 + F | 1 outline (1B1B) | F10 2.80 x 1.40 x 0.50; F 0.90 x 0.80 x 0.30 | ONE rectangle 3.25 x 1.40 round C10 and corner column C, tags F10 and F, open where SB1 enters | **HELD** (owner Q-31 C) | (A) rows separately 2.176 .. (B) outline at 0.50 = 2.275 |

FN 180C: its drawn outline is notched 0.40 x 0.35 exactly where the F9 outline lies; all footing bottoms share one
stack above the formation (T-206: footing bottom = formation + 0.17 for every type), so F9 (0.55) contains FN (0.30)
in that piece: the designer drew the intersection once and F9 owns it (R-CONC-OWN-1). DRAWING-CONFIRMED.
F10 reading B uses the deepest tagged depth: one outline cast at F's 0.30 would leave F10's printed 0.50 unbuilt under
C10, against its own schedule row, so it is not a reading (rule in `footing_line.footing_row`).

## 3. Blinding table

| Component | m2 | m3 | Status |
|---|---|---|---|
| 25 measured outlines grown 0.10 (mitred), sum | 151.990 | | |
| blinding overlap counted once (FN 180C / F9 projections) | -0.196 | | one layer (union) |
| union = the candidate's released footing blinding 15.179437 (T-193) to the cm2 | 151.794 | 15.179 | |
| of it beyond the plot line: 8 footings on the plot line (3 F, F11, F14, F8, F15, FN) | 1.890 | 0 .. 0.189 | HELD (designer D-14) |
| **measured inside the plot** | **149.904** | **14.990** | DRAWING-CONFIRMED |
| F10 + F outline | 5.025 inside / 5.520 all; rows separately 5.90 | 0.5025 .. 0.590 | HELD (follows its footing) |
| ground-beam blinding (T-100 hand, not re-measured here) | 96.91 (reading R) | 9.691 | HELD (section 4) |
| strap blinding | 9.13 | 0 .. 0.913 | HELD (D-15: none printed under straps) |

## 4. Engineering findings

1. **The two lines are NOT closable from the drawings alone** (the Lead's premise 'neither depends on an open designer
   item' holds for the 25 measured footings and their blinding only, not for the keyed lines):
   - CONC.FOOTING blockers: F10 + F outline (Q-31 C, two printed sources disagree: schedule rows vs one drawn outline),
     the foundation-level boundary band (Q-28 A PROVISIONAL: section C1 B.W 20 x 60 vs typical 20 x 40, crossing
     levels), SB3 / F3 strap soffit (T-230, D-15 narrowed), SB1 end into F10 + F (follows Q-31).
   - CONC.BLINDING blockers: D-14 (projection beyond the plot line), F10 + F (follows its footing), ground-beam
     blinding (detail selection waits on the formation, Q-21 C), D-15 (straps).
   - None of F10 / C1 / D-14 / D-15 is on CLARIFICATIONS_CONSULTANT_2026-10-23.md: proposed rows in the handoff.
2. **T-100's ground-beam blinding range L 5.534 .. R 9.691 narrows to R for the drawn beams**: T-230 (MERGED) shows
   every ground-beam soffit at least 0.28 m above every footing top in every admissible formation (footing top <= -0.63,
   beam soffit >= -0.35), so a beam's blinding over a footing is its own layer on the compacted fill, never merged with
   the footing's (reading L needs the beam at footing level). It stays HELD only because the two-beam detail (formation
   below about -1.67, T-206) would add lower ground beams that no plan draws. Not re-measured here (T-100 hand area).
3. **Engine A F10 line misses the drawn outline**: 'one footing labelled with two types and no outline found' with
   bound 0.216 .. 1.960, PROVISIONAL and inside the compared 77.27 m3; the open polyline 1B1B is the outline and both
   printed readings (2.176, 2.275) lie above its bound. The same miss leaves strap SB1 undeducted inside it: engine SB1
   1.995 = 0.70 x 0.50 x 5.70 m, drawn 7.35 m less 1.65 m in F8 = 5.70 m; with the F10 outline 1.15 m more is inside a
   footing: +0.4025 m3. Both belong to the integration package (opt-in candidate), not to released V2.9.
4. Engine A blinding: one BOUNDED line 7.2755 .. 16.887 m3 'BLINDING_THICKNESS_NOT_PRINTED': superseded in the
   candidate (V3.0.7 EV-BLINDING-T, p.13 '10cm Plain con.'); our 15.179 total equals the candidate line.

## 5. Line totals vs released A, candidate V3.0.7 and the freelancer (m3)

| Line / component | Drawing (this task) | Released A (b96185d4) | Candidate V3.0.7 | Freelancer | Difference and cause |
|---|---|---|---|---|---|
| isolated footings, 25 | **64.304** DRAWING-CONFIRMED | 64.304 | 64.304 (same 25 lines) | 65.634 (with F10 1.960) | A: 0.000 (ENGINE_RIGHT). Freelancer +1.330 = F10 at schedule +1.960 (held here) - one F3 omitted -0.672 (2 drawn) + FN / F9 piece twice +0.042; residual 0.000 |
| F10 + F | HELD 2.176 .. 2.275 | PROVISIONAL 1.960 (0.216 .. 1.960) | PROVISIONAL 1.960 (0.216 .. 1.960), same line | 1.960 (F10 only; the F pad of this outline in none of his 4 F) | engine bound excludes both readings (finding 3); freelancer below both readings by 0.216 .. 0.315 |
| straps SB1-SB3 | 3.3905 + HELD (SB3 excess 0.0295 .. 0.2683; SB1 / F10 end) | 3.7809 (2.6494 + 1.1315 PROVISIONAL) | 3.3904 (0.6515 + 1.5925 + 1.1464 PROVISIONAL) + BOUNDED 0 .. 0.4025 (SB1 inside the open F10 outline) and 0 .. 1.4062 (inside open outlines; T-230, merged after V3.0.7, gives the footing that piece at e = 0) | 3.3925 | A +0.3904: SB1 +0.4025 inside the unseen F10 outline, SB2 -0.0155 / SB3 +0.0024 net-plan vs axis, residual 0.001. Freelancer +0.002: axis lengths rounded (2.30 / 3.25 vs 2.294 / 3.259) |
| boundary band | HELD 5.639 .. 11.033 (Q-28 A provisional 8.459) | 7.2204 (60.17 m, side 1 lost, T-065) | 7.2204 | 8.604 (71.7 m x 0.20 x 0.60) | T-065: 91.94 m drawn, 70.49 m free; owner Q-28: not released |
| **CONC.FOOTING line** | **67.6945 measured + HELD** (range 75.54 .. 81.27, SB1 end unbounded) | **77.2653** (1.96 + 1.1315 provisional inside) | **76.8748** (1.96 + 1.1464 provisional inside) + BOUNDED 0 .. 1.8087 | **77.6305** | not comparable as a whole line while held; measured components agree with A on footings to 0.000 |
| footing blinding | **14.990** + HELD 0 .. 0.189 (D-14) + F10 0.5025 .. 0.590 | BOUNDED 7.2755 .. 16.887 (thickness 'not printed') | 15.179437 PROVISIONAL line (incl. the D-14 part) | 47.055 (15.00 x 31.37 x 0.10, whole plot) | candidate = ours + the D-14 part 0.189 exactly (V3.0.7 reproduced: 15.179437); freelancer: a plate under the whole plot no sheet draws (P7 compacted soil under the slab): RULE_DIFFERENCE, basis -32.0 m3 |
| ground-beam + strap blinding | HELD (9.691 R; straps 0 .. 0.913) | (in the bounded line) | BOUNDED 4.9494 .. 9.4225 (FOOTING_DETAIL_CHOICE_OPEN) + straps 0.3778 .. 0.7719 + F10 0.48 .. 0.59 | (in his plate) | finding 2 |
| **CONC.BLINDING line** | **14.990 measured + HELD** | BOUNDED | 15.1794 PROVISIONAL + BOUNDED 5.807 .. 10.784 | **47.055** | basis difference, not a count difference |

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 25 isolated footings 64.304 m3 | ENGINE_RIGHT (A = drawing 0.0 %); freelancer WRONG on F3 count (-0.672) and FN / F9 piece (+0.042) |
| F10 + F | UNRESOLVED (designer: one combined footing 3.25 x 1.40 x ? or F10 + F separately); engine A bound WRONG basis |
| straps | drawing 3.3905 (T-230); engine A +0.4025 ENGINE_WRONG (SB1 inside F10 outline); freelancer within rounding |
| footing blinding 14.990 + D-14 | candidate 15.179437 = ours + D-14: CLOSABLE AFTER D-14; freelancer plate RULE_DIFFERENCE |
| CONC.FOOTING line | BLOCKED BY CONSULTANT (F10 + F, band C1 / crossing levels, strap soffit); 64.304 component re-measurable now |
| CONC.BLINDING line | BLOCKED BY CONSULTANT (D-14, D-15, F10) and the formation (Q-21 C, ground-beam detail); 14.990 component re-measurable now |

Checker re-measure list (whole line, not a sample): every one of the 26 outlines (handles in LEDGER_T233.csv) against
p.2 and p.9; the 180C notch against 180F; the F10 corner on p.2; the blinding union and the 1.890 m2 beyond 1658.

## 7. Rule, test, lessons row

General rule proposed (every villa; provenance T-233; a new rule version when adopted, R-FOOT-OUTLINE-1): a footing's
plan is its drawn outline checked against its schedule row (either orientation); an outline clipped exactly where a
neighbour's outline lies is the one-owner intersection (the deeper footing keeps it); an outline carrying two types is
HELD with the readings 'rows separately' and 'outline at the deepest tagged depth', never one picked; a scheduled type
with no outline is count 0, not HELD; blinding = union of the outlines grown by the printed projection, a part beyond a
boundary it cannot cross HELD; underlay never concrete; a keyed line is closable only when every keyed component is.
Test: tests/t233_footing_line (villa Q fixture: three types incl. a combined row, rotation, clip, plot line; adverse:
outline under two types refused, two tags held never in the total, blinding without the printed projection refused,
underlay refused, mm input refused, HELD never 0, size conflict a range, clip without neighbour a conflict; Alsenan
ledger pinned).
Lessons row (proposed): 2026-10-23 | 'CONC.FOOTING and CONC.BLINDING need no designer item' (T-233 premise) | the
keyed reference line was read as its first component (footings) while the key map carries straps and the boundary
band, and the blinding key carries beam and strap blinding | before a whole-line verdict, expand the key map's item
codes and list every physical component with its own status (every villa) | tests/t233_footing_line
test_lines_not_closable_and_why (adverse: a held component keeps the line NOT CLOSABLE) | PROPOSED.

## 8. Not done / uncertain

- Ground-beam blinding area not re-measured (T-100 hand figure); the engine's 0.49 m2 against T-100 not traced.
- Band and boundary-wall members not re-measured (T-065 figures quoted).
- No engine or candidate line changed; nothing released.
