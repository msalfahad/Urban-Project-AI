# T-531: B9-02 lintel bars on the measured lintel ends (R-T531-1, Gate A, research only)

Worker 1, lane S, 2026-11-05, base engine f05abdd6. Files: `t531_lintel_bars_produced.py` (project-agnostic rule +
training-villa builder over committed records), `out/LINTEL_BARS_T531.json`, `tests/t531_lintel_bars_produced/` (39
tests). R-T515-1 and the merged T-516 / T-519 / T-524 / T-527 modules are imported read-only. No engine, rule,
knowledge, hub, master or candidate file changed; released default (V2.9 + route G) untouched.

## 1. Physical element and engineering question (ERS s.2.1)

One cast RC lintel per opening. Bar marks per lintel: B1 bottom, T1 top (n x d of the printed band), S1 closed links
(5Ø8/M). A main bar = SPAN over the lintel's own clear span + one straight EXTENSION beyond each jamb + one drawn END BEND
each end. Question: with the ends now measured (T-516 / T-519 / T-524 / T-527), does the bar length
"span + 2 x built bearing - covers + bends" become measured?

## 2. Drawing re-read this run (second source checked)

Drive 'Alsenan chalet project' / ST7757.pdf, decoded into .work/private only:
- p.13 LINTEL SCHEDULE: L1 0-100 B x 20 2Ø12 / 2Ø10; L2 101-200 B x 20 2Ø14 / 2Ø12; L3 201-300 B x 30 3Ø16 / 3Ø14;
  L4 301-500 B x 40 3Ø18 / 3Ø14; L5 501-750 B x 55 4Ø18 / 3Ø14; stirrups 5Ø8/M every band (= the pinned S8.6 transcription).
- LINTEL DETAIL: 'MIN.40cm' both ends; top bar drawn turned DOWN at both ends, bottom bar turned UP, inside the
  bearing; links drawn inside both bearings as well as over the span (so links run over the whole lintel length L, not
  the span only); SECT 2-2 one closed link with hooks. NO cover, bend length, hook length or first-link position.
- p.8 notes: 3 = dimensions are read, the contractor may not scale (so no length is taken off the detail); 9 = 70 d /
  40 d development of STARTER bars only (owner 2026-10-24: not a general rule); 22 = cover NOT LESS THAN 2.5 cm in
  columns, slabs, beams (a minimum; lintels not named). No hook / bend note.
- Second source: the structural DXF on Drive ('ST7757 dxf.dxf') holds plans and the column / footing / beam schedules
  only; the p.13 detail sheet is not in it (searched every layout and block for LINTEL / MIN 40 / SECT 2-2 / cover).

Answer: the bar ends cannot be measured from this set. Extension = built bearing - end cover: the bearing is a range
[0.40, a] (MIN is a lower bound, T-516) and the cover is unprinted; bends are drawn and undimensioned. They stay HELD by
name (unchanged from T-515). What the measured ends DO give is a physical ceiling per end, and one correction to the span.

## 3. Rule R-T531-1 (every villa; provenance T-531 / F-C-T487-1 / T-515 open item)

Per end, the straight-bar ceiling beyond the jamb (never a value, never summed in):
- BOUNDED masonry end (a >= printed minimum): the detail applies, the bar stays in the lintel concrete: <= a.
- DEFICIT end at a COLUMN: the lintel concrete stops at the column face (R-T524-1) but its bars may be anchored into the
  column (designer item): <= max(drawn gap in either frame) + column depth along the wall (a bar cannot pass the far face).
- DEFICIT end at the end of the masonry: <= a. DEFICIT shared pier: <= p. HELD end or search-capped pier: no ceiling.
Span = own clear span w_net (opening width minus any strip of the opening inside a column outline).
COMPUTED only with printed sources: extension = EXACT printed bearing - printed end cover; bend = printed length;
link count = printed spacing + printed first-link offset (Q-71, N = 1 + floor((L - 2 o) / s)); link kg = printed cover +
hook. Otherwise PROVISIONAL count (RATE_COUNT ceil(L / s) over the concrete range, 1 + floor(L / s) beside) and kg HELD.
Line = PRODUCED part + FLAGGED part, each AT_LEAST, never one number.

## 4. Owner manual method vs drawing-derived method

| | Owner manual (OWNER_RULE_REBAR_2026-10-24, Q-71) | Drawing-derived (this record) |
|---|---|---|
| kg | L x d^2 / 162, stock 12 m, 60 d beam laps where L > 12 | same; every straight ceiling < 12 m -> laps NOT_REQUIRED |
| Bar length | only drawn / printed parts (owner (B)) | span COMPUTED; extensions, bends HELD; ceiling per end beside |
| Links | drawing positions, never n L + 1 by default | no first-link offset printed for lintels -> PROVISIONAL count, kg HELD |

## 5. Training villa (16 REQUIRED lintels; before = T-515 r1, after = R-T531-1)

| Part | Lintels | AT_LEAST kg before | after | straight ceiling kg (beside) |
|---|---|---|---|---|
| PRODUCED | D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15 | 38.761728 | 38.761728 | 85.080148 on 5 (D-2F-01 HELD: END pier >= 3.0 m, capped) |
| FLAGGED | D-1F-03/04/07/10, D-2F-03, D-GF-06/10/11/12, W18 | 24.400000 | 24.301496 | 69.534578 on 9 (D-GF-12 HELD: END junction) |
| Line | 16 | 63.161728 | 63.063224 (two parts) | - |

Reconciliation in units to the cause:
- W18 -0.098504 kg = 0.0327 m x 3.012346 kg/m: the START jamb lies 32.7 mm inside column C8 (ELEMENT_REGISTER, two
  routes; T-524 w_net 0.4673): that strip is column, not the lintel's own span; a bar there exists only if anchored into
  the column (HELD). T-515 counted the full 0.50 m. Only W18 moves.
- Ceilings vs T-516 V3 (concrete-length ceilings applied to bars): equal on the 10 lintels whose ends are all masonry /
  cross wall / pier (to 1e-5 kg, T-516 rounding); HIGHER on the 4 column-deficit lintels, where T-516's figure was a
  concrete ceiling, not a bar ceiling: W18 3.244297 -> 5.856904 (1.077 -> 1.9443 m), D-1F-04 9.034026 -> 9.638602,
  D-2F-03 9.636495 -> 11.143269, D-GF-06 5.720445 -> 6.551852 kg.
- Links (PROVISIONAL count, kg HELD): PRODUCED 65 .. (hi on 5) e.g. W14 17 .. 21, D-1F-02 9 .. 22 (alt 10 .. 22).

Hand check: L1 488/162 = 3.012346 kg/m; PRODUCED 3.90 x 3.012346 + 1356/162 x 2.45 + 680/162 x 1.55 = 11.748148 +
20.507407 + 6.506173 = 38.761728; FLAGGED 8.0673 m x 3.012346 = 24.301496; W18 ceiling (0.4673 + 0.90 + 0.577) x
3.012346 = 5.856904.

## 6. Verdicts (proposals for the Checker)

- W18 span: ENGINE_WRONG (T-515 AT_LEAST over the full width into the column) -> 1.407669 kg, hand above.
- Column-end ceilings: T-516 straight ceiling is a concrete ceiling, not a bar ceiling at 4 column ends (beside only;
  no released or candidate quantity uses it).
- Freelancer: one project rebar total, no lintel row: UNRESOLVED.
- Checker re-measure suggestion: W14 (L3: 3Ø16 / 3Ø14 over 2.45 m = 20.507407 kg; ceiling 4.10 m = 34.318519 kg) and
  W18 (0.4673 m own span; C8 depth 0.90 from the p.9 schedule 20 x 90).

## 7. Tests (L2, 39 pass) and checks

Non-Alsenan fixture: 1.20 m opening, exact printed 0.20 m bearings, 2Ø12 + 2Ø10 + R8@150 with every detail printed ->
COMPLETE 9.049383 kg (main 1.85 m cut, 11 links of 0.80 m); same lintel on MIN 0.40 bearings with piers 0.55 / 0.70 ->
AT_LEAST 3.614815, ceiling 7.380247, links 14 .. 17; adverse: hook not printed -> HELD; FLAGGED column end -> bar ceiling
to the far face; HELD / capped end -> no ceiling; mirror; 15 refusals (defaulted / borrowed / scaled lengths, units, band,
notation, HELD piece, 'MIN' read as exact, cover leaving no bar); HELD summed as 0 refused. Villa: parts by hand, the
W18 reconciliation, column ceilings, T-516 equality elsewhere, named holds, committed build = build.
Regression: t515 / t516 / t519 / t524 / t527 / t487 pass unchanged (1 skip: private DXF re-run). Freeze 0 differing;
codemap built and check clean.

## 8. Open (designer RFI, not an owner question: ERS 2.7 not met)

B_REMAINING_RFI (d) / (e) already ask the bend / hook / link closure; for lintels add: "lintel bar end cover and end
bend length (or a BBS), link hook and first-link position; at a lintel end against a column (W18, D-1F-04, D-2F-03,
D-GF-06): are the lintel bars anchored into the column, and how far?". Each answer moves a HELD part to COMPUTED through
R-T531-1 without a new rule. Not wired: a later S package binds B1 / T1 / S1 to the B9-02 lines (manifest T-530 / T-536).

Lessons row (proposed, ERS s.7): | 2026-11-05 | a concrete-length ceiling was used as the bar ceiling, and the span of
an opening whose jamb is inside a column was taken as the lintel's own span | a 'ceiling' that is not one at column ends
(up to 2.6 kg on W18) and an AT_LEAST 0.0985 kg high | ceiling each bar end by what physically stops a bar (masonry end,
cross wall, pier, or a column's far face); measure the span from the lintel's own end face | tests/t531_lintel_bars_produced | T-531 |
