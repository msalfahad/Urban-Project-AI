# T-306 Suspended-slab reinforcement: the 2,188.560 kg bound spread split by cause (lane S; Alsenan; every villa)

Worker 1, 2026-10-26, branch `agents/task-T-306`. Research ledger: nothing wired, no candidate or released line changed,
no method or rule version, nothing released. Integration dependency of the rebar line (lane I). Development villa, not
an accuracy claim. Drawings named by Drive folder and title only. ERS s.2.1 - 2.6, s.3, s.4 applied.

## 0. Sources and run

- Candidate lines: the 294 BOUND SLABS rows of the T-297 r2 basis ledger (`research/agents_t297/LINE_BASIS_T297.csv`,
  MERGED 1647711d; V3.0.16 = V3.0.17 line by line) and their source rows in the T-152 ledger
  (`research/agents_t152/T152_SLAB_STEEL.csv` + `T152_INPUT.csv`, MERGED 798e3b9; lines built by T-179
  `slab_records`).
- Drawing re-read this run: Drive "Alsenan chalet project" / "ST7757.pdf" (sha256 74da1523..., the same file T-152
  used): p.15 TYP. SLAB ON BEAMS DETAIL and its notes, p.4 GF roof-slab plan note 2 (Arabic). Private copy in the
  git-excluded folder only.
- Code: `t306_slab_bounds.py` (rules R306-1 .. 8, stdlib), `t306_alsenan.py --write | --check` ->
  `SLAB_SPREAD_DECOMPOSITION_T306.csv` (one row per line, one column per cause) and `SLAB_SPREAD_SUMMARY_T306.json`.
- Tests: `tests/t306_slab_bound_decomposition` (villa V306 hand fixture, normal + adverse; Alsenan pins).

## 1. Physical element (ERS s.2.1)

One suspended slab panel, one bar direction, three bar populations, each its own candidate line and its own geometry:
(a) the BOTTOM MESH printed on the plan as 'n o d/m' (bars between the beam faces, p.15: 50 % stop 0.125 L short of a
continuous support, the balance runs on across the beam = the crossing half); (b) the TOP BARS over the supports
(plan note 2: "top 5 o 10/m over the beams for one third of the span in both directions"; p.15: 0.30 x the larger
clear span each side of a continuous support, 0.25 L1 anchor bars at a non-continuous support, hooked down into the edge
beam); (c) the DEVELOPMENT / ANCHORAGE at the bar ends (candidate: note 9, 2 x 40 d .. 2 x 70 d per bar).
49 panels x 2 directions x 3 populations = 294 lines; 18 HELD lines (13 panels with no bars printed, GF-126 6o14/m
zone, 1F-084 corner bars, temperature bars x 3 storeys) and 72 NOT_APPLICABLE route lines are not ranges and are not
part of the spread.

## 2. Result: every kg of the spread named, residual 0.000 kg

Candidate: low 4,643.766 kg, high 6,832.326 kg, spread **2,188.560 kg** (4.643766 .. 6.832326 t). Causes (kg; summed per
cause only, never into a quantity):

| Cause (the one unprinted value that opens it) | Bottom mesh | Top bars | Development | Total | Share |
|---|---|---|---|---|---|
| TOP_NOTE2_WORDING: note 2 'one third of the span' = whole bar (L/6 each side) or each side (L/3) | - | 781.385 | - | **781.385** | 35.7 % |
| ANCHORAGE_LENGTH: slab bar-end length not dimensioned; note 9 40 d .. 70 d is the starter-bar note | - | - | 746.560 | **746.560** | 34.1 % |
| COUNT_CONVENTION: first / last bar position of an 'n o d/m' mesh (A = ceil(rate x W) vs B = A + 1) | 155.344 | 107.270 | 55.613 | **318.227** | 14.5 % |
| TOP_NOTE2_VS_P15: note 2 extent vs the p.15 detail extent (two drawings disagree) | - | 185.612 | - | **185.612** | 8.5 % |
| TOP_CROSSING: top bar over the beam band (exists under the 'each side' / p.15 readings only) | - | 146.686 | - | **146.686** | 6.7 % |
| LABEL_MEANING: '5 o 10' printed without '/m' (GF-020 y, GF-076 x, 1F-041 y): 5 in all or 5 per metre | 10.081 | - | - | **10.081** | 0.5 % |
| STORAGE_ROUNDING (3 dp ledger figures; not a cause) | 0.000 | 0.000 | 0.009 | 0.009 | 0.0 % |
| **Total** | **165.425** | **1,220.953** | **802.182** | **2,188.560** | 100 % |

By storey: GF 1,146.652, 1F 672.491, 2F 369.417 kg. Residual after the named causes: 0.000000 kg (closure asserted per
line: R306-7 refuses a line whose causes do not sum to its spread within storage rounding).

Order of the split (stated, because the parts of an interaction depend on it): bottom = |B - A| (count) + the label
reading outside [A, B]; development = count part at 40 d, then 40 -> 70 d at count B; top = reading i -> ii (note-2
wording) -> the governing high reading (note 2 vs p.15) at count A, then count A -> B, then the crossing.

What one designer answer would close: the two top-bar items (note 2 wording + note 2 vs p.15 + crossing) are **1,113.683
kg (50.9 %)**; the slab bar-end detail 746.560 kg (34.1 %); the mesh boundary-bar convention 318.227 kg (14.5 %).

## 3. Components raised to DRAWING_CONFIRMED: none (acceptance 2)

No component of the 294 lines has every input printed: every bottom and top count rests on the unprinted boundary-bar
position (a rate, never a count, R306-1); every top length on the note-2 / p.15 extent; every development length on an
undimensioned end. The bar lengths face to face and the continuity of each end are drawing-derived (T-152 geometry),
but no kg figure is free of an open input, so nothing is relabelled (LB-2: a component is DRAWING_CONFIRMED only when
its count AND length are printed). Q-71: the owner's answers govern links / stirrups (11:51) and footings (12:36); they
are not extended to suspended slabs without their own evidence (ERS s.3), and the owner's own footing point 9 ("if the
drawing does not establish the boundary bar positions ... keep PROVISIONAL or HELD") would leave the slab count a BOUND
anyway. The slab reading stays a BOUND; no owner decision is needed (ERS 2.7 not met: these are designer items, s.6).

## 4. Findings (nothing changed; for the Checker and lane I)

**F-T306-01 development at continuous ends has no physical bar on the p.15 detail (basis, material).** Re-read this
run: at a continuous support the TYP. SLAB ON BEAMS DETAIL stops 50 % of the bottom bars 0.125 L short of the face and
runs the balance continuous across the beam (already booked as the crossing half of the bottom line); no development or
lap is drawn there. At a non-continuous support the bar runs into the edge beam to 40 mm clear of its far face ('40
CL.') and turns up (hook leg not dimensioned). The candidate's development lines book 2 x 40 d .. 2 x 70 d on every
bar at both ends. End census from the merged T-152 bar lines (3,272 ends at count A, 1,947 continuous; 3,474 at B,
2,060 continuous), at the candidate's own per-end figure:

| End kind | low (count A, 40 d) | high (count B, 70 d) | Drawing-derived status |
|---|---|---|---|
| continuous support | 556.205 | 1,027.310 | no development bar (NOT PRESENT on p.15): the 50 % stop short, the 50 % continue = crossing half |
| non-continuous support | 384.089 | 718.120 | bar present: length = edge-beam width - 0.040 + an undimensioned hook leg (HELD on that basis, not note 9) |
| model total | 939.800 | 1,741.973 | candidate 939.794 .. 1,741.976 (storage rounding) |

So the development BOUND's low 939.794 kg is not a lower bound of anything drawn: 556.205 kg of it (59 %) books
anchorage where the detail draws none. Opening edges: 4 lines (GF-081 y, GF-124 y, GF-139 y, 1F-023 x) have bar lines
cut by an opening: 2 ends at A and 8 at B that the 2-per-bar model does not book (no detail prints an end at an opening
edge: HELD, not 0). Verdict proposal: ENGINE_WRONG in basis (research ledger T-152 / T-179 development line); the fix is
a lane I row: split the line into continuous ends NOT_APPLICABLE_WITH_EVIDENCE (p.15) and non-continuous ends HELD on
"edge-beam width - 40 mm + hook leg (not dimensioned)", with the edge-beam widths from the merged beam ledger; never a
note-9 figure. Spread effect if applied: the 471.105 kg of the development spread that lies on continuous ends goes.

**F-T306-02 four tank-panel top lines (2F-011 x / y, 2F-013 x / y, '(T&B)') carry a low of 28.663 kg** although the
reading "note 2 adds no bars over a panel that already carries a full top mesh" gives 0; T-152 itself named this a
separate HELD item (28.66 .. 70.61 kg). The bound excludes a defensible reading (R306-6): low should be 0 on those 4
lines until the designer says whether note 2 applies over a T&B mesh.

**F-T306-03 skewed panel GF-126 y top line (L-b10f318a155d5ee1b289) bound 16.484 .. 34.543 kg excludes two of its own
readings**: reading i at count B 16.223 (-0.261) and reading ii at count A + its crossing 34.821 (+0.278): on a skewed
panel the B bar lines run where the panel is narrow (T-152 lesson 4), but the line took its low at count A and its high
at count B only. Correct envelope 16.223 .. 34.821 kg (spread +0.539 kg). Bottom lines already use min / max (the same
panel's bottom y has B 52.129 < ... flagged SKEW_B_BELOW_A, inside its bound).

**F-T306-04 the 3 unlabelled-rate lines' development lows exclude the '5 bars in all' reading** (GF-020 y, GF-076 x,
1F-041 y: 2.469 kg each at 2 x 40 d against lows 4.444 / 2.963 / 10.370 kg): the count reading of the label was carried
into the bottom line only.

**B14 (identical slab labels de-dup may merge two layers): checked, not present.** Every (panel, direction, layers,
population) appears once (294 keys); every '(T&B)' label sits on a two-layer record and no single-layer label on a
two-layer one (`check_keys`); panels printing the same label in both directions keep two lines.

## 5. Owner manual method vs drawing-derived method (ERS s.2.2)

There is no owner manual method for slab bars: the owner's rebar decisions are the metric-ton unit (s.1), the lap
proposal 40 d / 60 d (s.2, NOT approved, never applied: R306-4 refuses it) and Q-71 for links and footings. The
drawing-derived method is the T-152 bar population with the p.15 detail; this task adds the p.15 end reading (F-01).
Freelancer: one lump 5,400 kg for all slabs (90.3 kg/m3 on 59.817 m3), no bar population: RULE_DIFFERENCE, no % (T-152).
The freelancer figure sits inside the candidate range 4,643.766 .. 6,832.326 kg, which is no evidence for either.

## 6. Designer items (ERS s.6 format, for the Lead's consultant list; not owner questions)

1. **Top bars over supports (1,113.683 kg of the spread).** Issue: the extent of the top bars over the beams. Evidence:
   plan note 2 (p.4 / p.5 / p.6, Arabic) "top 5 o 10/m over the beams for one third of the span in both directions"; p.15
   detail 0.30 x the larger clear span each side, 0.25 L1 at a non-continuous support. Investigation: three readings
   measured per line (i 781.395 .. ii / p.15 2,002.348 kg incl. crossings). Alternatives: (i) 1/3 span is the whole bar,
   (ii) 1/3 span each side, (p.15) the detail governs; also whether note 2 applies over the '(T&B)' tank panels.
   Quantity impact: 1,113.683 kg. Recommendation: none between drawings (a designer's call; the detail and reading ii
   agree to 0.2 %, T-152). Status: HELD as a BOUND. Next action: the rest of the slab line continues.
2. **Slab bar ends at non-continuous supports and opening edges (part of 746.560 kg).** Issue: the hook leg at the edge
   beam and any end detail at openings. Evidence: p.15 '40 CL.' and an upturned end, no leg dimension; no opening
   detail. Impact: non-continuous ends 384.089 .. 718.120 kg on the note-9 figures (the drawn basis replaces them).
   Status: HELD. Next: lane I splits the line (F-01).
3. **Mesh boundary bars (318.227 kg).** Issue: the first / last bar position of an 'n o d/m' slab mesh from the support
   face. Evidence: plans p.4 - p.6, p.15; nothing printed. Alternatives A (bars centred in their strips) and B (a bar at
   each edge). Status: BOUND. Note: the same question was answered by the owner for footings and links only.
4. **Labels without '/m' (10.081 kg):** GF-020 y, GF-076 x, 1F-041 y '5 o 10': 5 bars in all or 5 per metre.

## 7. Rules, tests, lesson

Rules R306-1 .. R306-8 (module docstring; research rules, no rule-file version). Tests (`tests/t306_slab_bound_
decomposition`, 21 PASS): villa V306 (S1 4.00 x 3.00 m): printed count '16 o 10' x 4.00 m = 39.506173 kg DRAWING_
CONFIRMED; top '6 o 12' x 1.60 m = 8.533333 kg DRAWING_CONFIRMED; rate '5 o 10/m' over 4.00 m -> 20 .. 21 bars,
37.037037 .. 38.888889 kg BOUND; development decomposition 0.493827 + 7.777778 = 8.271605 kg; top decomposition 3.0 +
0.4 + 0.6 = 4.0 kg. Adverse (refused): 'n/m' read as a count; two layers under one key / a T&B label on a one-layer
record; the 40 d / 60 d lap proposal as a basis; an unprinted extent given a value; a width in mm; a non-closing
decomposition; an unknown cause; a note-9 length on a continuous end; a bound excluding a reading is named (skew, T&B 0). Alsenan pins: 294 lines, spread
2,188.560, residual 0, cause totals, findings F-01 .. F-04.

Lessons-register row proposed (ERS s.7): 2026-10-26 | a slab development bound booked 2 x 40 d .. 2 x 70 d on every
bar end, 556.205 kg of its 939.794 kg low at continuous supports where the typical detail draws no anchorage (T-306) |
the bar-end length was taken from a general note (note 9, starter bars) per bar, without reading the typical detail
end by end | a bar end is classified by the support it meets on the typical detail (continuous: stop short / run on,
no development; non-continuous: the drawn anchorage; opening edge: its own detail or HELD) before any length is
applied; a general note's length applies only to the situations it names (every villa; slabs, beams, ground beams) |
tests/t306_slab_bound_decomposition (test_bar_end_by_support_kind: normal, continuous end -> no development, edge
beam 0.25 m -> 0.21 m drawn; adverse: note-9 length on a continuous end refused; end census pin) | OPEN until lane I
splits the development line.

## 8. Not done / uncertain

- No candidate kg changed (acceptance 3): F-01 .. F-04 need a lane I row. Edge-beam widths at non-continuous ends were
  not joined (beam ledger), so the drawn anchorage length is not computed here.
- The p.15 reading of 'balance continuous' rests on the detail's text and drawn bar; no lap length is drawn at the
  continuous support. A Checker re-read of p.15 is the independent check of F-01.
- Note 2 was re-read on p.4 only (p.5 / p.6 carry the same note per T-152, not re-read this run).
