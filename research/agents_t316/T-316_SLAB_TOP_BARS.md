# T-316 Suspended-slab TOP bars: extent census by support (lane S; Alsenan; every villa)

Worker 1, 2026-10-28, branch `agents/task-T-316`. Research ledger: nothing wired, no candidate or released kg changed
(owner 2026-10-25 10:33: no reinforcement calculation code change before an approved implementation stage), no method
or rule version, nothing released. Integration dependency of the rebar line (lane I consumer file below). Development
villa, not an accuracy claim. Drawings named by Drive folder and title only. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and run

- Drawings re-read this run (private copies in the git-excluded folder only, sha256 checked): Drive "Alsenan chalet
  project" / "ST7757.pdf" (74da1523..., the file T-152 / T-306 / T-307 and the Checker used): p.15 TYP. SLAB ON BEAMS
  DETAIL at 600 dpi (top bars, dimension lines and extension lines traced), p.15 notes 1 - 3; p.4, p.5 and p.6 plan
  note 2 at 480 dpi. "ST7757 dxf.dxf" (9f9d1179...): raw S-REIN-SLAB / S-REIN-CORNER entities of the three roof-slab
  sheets against the T-139 faces (every face's area = T-139 PANELS.csv to 0.001 m2).
- Candidate lines: the 98 BOUND top lines of the T-306 decomposition (`research/agents_t306/...T306.csv`, MERGED
  01358449) and their T-152 note-2 bar geometry (`research/agents_t152/T152_INPUT.csv`).
- Code: `t316_top_bars.py` (rules R316-1 .. R316-10, stdlib), `t316_alsenan.py --geometry <private faces>` ->
  `TOP_END_DETAIL_T316.csv` (5,914 top-bar ends: line, reading, bar, end, T-152 continuity / gap / other span, T-307
  support class, band face id, neighbour; numbers and face ids only); `t316_alsenan.py --write | --check` ->
  `TOP_GROUP_LEDGER_T316.csv` (support by support), `TOP_LINE_LEDGER_T316.csv` (lane I consumer, 98 line ids),
  `TOP_SUMMARY_T316.json`.
- Cross-checks: every top segment length = T-152's (4 dp); every end's continuity = T-152's (0 mismatches on 5,914);
  end classes = T-307's top-end census (CONTINUOUS 1,362 / 1,457, EDGE_BEAM 882 / 919, STEP 376 / 401, IRREGULAR
  234 / 269, OPENING 2 / 12 at A / B).

## 1. Physical element and what the drawings print (ERS s.2.1, s.3)

One SUPPORT GROUP = the top bars over one support of a suspended slab in one bar direction: at a continuous support
the extent into each panel + the part over the band; at an edge beam the extent into the end span + the part across
the edge beam + the hook-down leg. Each side is booked by the panel line on that side, the band part half by each.

- **Raw DXF**: of 169 slab-rebar entities >= 0.30 m on the three sheets, every mesh bar line lies inside ONE slab panel
  (147 lines). **No 5 o 10/m top bar is drawn over any support.** The only drawn bars crossing a support carry their own
  '/Top' labels (GF 3 o 16/Top over GF-110; 2F 4 o 16/Top, 5 o 18/Top: beam lane T-149), plus the GF-126 6 o 14/m zone
  bar and the 1F-084 corner bars (both HELD in T-152). So no top extent on these sheets is a drawn bar length.
- **Plan note 2** (p.4, p.5, p.6, identical Arabic text, re-read on all three): top bars 5 o 10/m for the slabs over the
  beams "with a length of one third of the span in both directions" -> NOTE_BASIS. Which span (two differ at a
  continuous support) and whether the third is the whole bar or each side are not printed (T-152 i = L/6, ii = L/3 per
  side).
- **p.15 TYP. SLAB ON BEAMS DETAIL** (600 dpi): continuous support: '.30"L1" OR .30"L2" WHICHEVER LARGER', the
  dimension runs from the support FACE (its right extension line is the beam's face, not the centreline), the bar is
  drawn continuous over the band to a similar extent on the L2 side -> 0.30 x max(L1, L2) each side + the band.
  Non-continuous: '.25"L1"' from the edge beam's INNER face into the span; the 'TOP ANCHOR BAR' then runs ACROSS the
  edge beam and hooks DOWN at its outer face, drawn outboard of the bottom bar that stops '40 CL.' from that face; the
  leg is drawn deeper than the slab, not dimensioned; dashed 'EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE
  POSSIBLE'. 'TOP ANCHOR BARS. FOR SIZE & SPACING SEE SCHEDULE OR PLAN': the detail delegates size and spacing to the
  plan, not the extent. **Note 3**: 'WHERE TOP REINF. DIFFERS BETWEEN ADJACENT SPANS USE LAGER [larger] REINF.' (not
  read by any earlier task). L1 / L2 are CLEAR spans (dimension lines face to face).

Basis labels kept apart (R316-5): DRAWING_DERIVED = the p.15 extent with drawn clear spans and band widths;
NOTE_BASIS = note-2 readings; UNRESOLVED = the 50 % extension and note 3; HELD = no detail.

## 2. Result 1: the T-306 top cause rows split by support class (residual = storage rounding)

| T-306 cause (kg) | CONTINUOUS | EDGE_BEAM | STEP_EDGE | IRREGULAR | OPENING | split total | T-306 row | residual |
|---|---|---|---|---|---|---|---|---|
| TOP_NOTE2_WORDING | 393.099 | 246.371 | 82.696 | 58.328 | 0.898 | 781.391 | 781.385 | -0.006 |
| TOP_NOTE2_VS_P15 | 179.336 | -13.710 | 24.996 | -5.009 | - | 185.614 | 185.612 | -0.002 |
| TOP_CROSSING | 121.983 | 0.000 | 24.702 | 0.000 | 0.000 | 146.685 | 146.686 | +0.001 |
| **the 1,113.683 kg** | **694.418** | **232.661** | **132.394** | **53.319** | **0.898** | **1,113.690** | **1,113.683** | **-0.007** |
| COUNT_CONVENTION (top) | 60.497 | 19.560 | 11.157 | 10.565 | 5.487 | 107.265 | 107.270 | +0.005 |

The residual is the 3 dp storage of the 98 T-306 line figures (R316-8 asserts each line within 0.0045 kg); no
unexplained kg. Physical causes:

- **CONTINUOUS ends, 694.418 kg (62.4 %)**: a genuine conflict between two printed documents of the set (note 2 vs
  p.15) over a drawn, continuous support. Inside its +179.336 VS_P15 sits **F-T316-02** (below): 74.169 kg at count A
  (81.746 kg at B) of the p.15 reading lies BEYOND the clear span of short panels.
- **EDGE_BEAM ends, 232.661 kg (20.9 %)**: note-2 wording only (p.15 0.25 L1 is below note-2 ii by L/12 per end:
  -13.710); no crossing booked. All three readings omit the drawn part across the edge beam (**F-T316-01**).
- **STEP / IRREGULAR / OPENING ends, 186.611 kg (16.8 %)**: no detail draws a top bar at a level step, a column /
  junction / composite support or an opening edge. This part is not a choice between readings: it is HELD.

## 3. Result 2: support-by-support p.15 ledger (each group once)

283 support groups (direction x support): 74 two-sided (58 continuous + 16 step), 209 one-sided (77 edge-beam, 118
irregular, 12 step, 9 opening, 20 continuous). Every one of the 20 one-sided continuous groups (and 1 step group)
faces a panel with NO top line: the T-152 NO_LABEL panels (GF-034 / 036 / 059 / 061 / 146, 1F-060, the 1F-073 / 076
dome corners, 1F-090 / 091 / 092), whose own side of the support is HELD with the panel (no bars printed), never 0.
Check R316-6: no group carries more than two panels, no side twice, no panel books both sides.

Per line (98, lane I consumer `TOP_LINE_LEDGER_T316.csv`): DRAWING_DERIVED_P15 7, ..._PART_WITH_HELD 68,
..._PART_WITH_HELD_LEGS 11 (all ends continuous / edge, only legs held), HELD 8 (GF-015 x, GF-016 x, GF-081 x / y,
GF-128 x / y, GF-141 x / y: every end at a step or irregular support), UNRESOLVED_TB_PANEL 4 (2F-011 / 2F-013 x / y).

p.15 valued parts on the 86 valued lines (count A low .. count B high, R316-10 applied, across-beam BOUND included,
legs / held ends / extension blank): **1,404.705 .. 1,546.858 kg** (1.404705 .. 1.546858 t at export). Same lines:
candidate 718.419 .. 1,829.432 kg, note-2 i at A .. ii + crossing at B 718.419 .. 1,640.822 kg. These are valued parts,
not a slab total; HELD stays blank, never 0.

## 4. Findings (nothing changed; for the Checker and lane I)

- **F-T316-01 the drawn top-anchor part across the edge beam is in no reading.** p.15 draws the top anchor bar from
  0.25 L1 inside the span across the edge beam to a hook at its outer face (outboard of the 40 CL. bottom bar). T-152
  books 0.25 L1 only (and note-2 i / ii book their span fraction only). Valued as a BOUND [w - 0.040, w] per end (top
  cover not printed): **122.574 .. 150.278 kg** (A low .. B high) on 882 .. 919 ends; the hook-down leg stays HELD.
- **F-T316-02 p.15 extents booked past the clear span.** At a short panel beside a long one, 0.30 x L_long from the
  continuous face plus the other end's extent exceeds the panel (e.g. 2F-047 y: 1.20 m span, 1.50 + 0.30 m). T-152's
  p.15 reading sums them: 241 / 252 bar lines, 74.318 / 82.486 kg; **81.746 kg of it is inside the candidate high
  (the 40 lines whose high reading is p.15)**. Physically the top steel cannot exceed the span: one through bar (ln) or
  two overlapping bars (each within the span), not drawn -> BOUND [ln, min(a, ln) + min(b, ln)] (R316-10).
- **F-T316-03 p.15 note 3 'where top reinf. differs between adjacent spans use larger reinf.'** At the 37 / 40 top ends
  of normal panels that face a (T&B) tank panel (top mesh 7 o 14/m, 6 o 12/m), note 3 says the larger reinforcement
  governs over that support: the 5 o 10/m note-2 bar there is open, and so is the tank panels' own note-2 line (T-306
  F-02). UNRESOLVED (designer), no value.
- **F-T316-04 'L1 = the longer span' confirmed, no own-span substitution occurred.** Every one of the 1,362 / 1,457
  continuous ends has its other span on the bar line (0 OTHER_SPAN_UNKNOWN); T-152's fallback to the own span was never
  used on this villa, but R316-2 now refuses it.
- **Count asymmetry across a support (named, small).** On two-sided continuous supports the two panels place 5 / m over
  their own widths: 11 (A) / 29 (B) two-sided group-readings differ by exactly 1 bar; the unpaired half-crossings are
  0.898 (A) .. 3.020 (B) kg, part of COUNT_CONVENTION.
- **B14 (de-dup of identical labels): checked, not present.** 98 top lines, one per (panel, direction); every top end
  once in the detail (5,914 rows = the group ledger); the (T&B) lines are separate two-layer panels (T-306 check_keys).

## 5. Hand re-measure for the Checker (acceptance 2: a panel other than GF-135)

2F-047 y (0.16 slab, 3.00 m across, top 5 o 10/m: A = ceil(5 x 3.00) = 15, B = 16; u = 100 / 162 kg/m):
- **Continuous support to 2F-016 over a 0.20 m band**: L1 = 1.20 (this panel, face to face), L2 = 5.00 -> 0.30 x 5.00 =
  1.50 m into 2F-047 + 0.10 over the band (+ 1.50 and 0.10 booked by 2F-016's y line). One B bar line meets a 0.50 m
  part of 2F-016: 0.30 x 1.20 = 0.36.
- **Edge beam (0.20 m, slab beyond: dashed extension UNRESOLVED)**: 0.25 x 1.20 = 0.30 m + across [0.16, 0.20] +
  leg HELD.
- 1.50 + 0.30 = 1.80 > 1.20 (F-T316-02): in-span BOUND [1.20, 1.50]. Line: A 15 x (1.20 + 0.10 + 0.16) x u =
  **13.519 kg**; B 15 x (1.50 + 0.10 + 0.20) + (0.36 + 0.10 + 0.30 + 0.20) = 27.96 m x u = **17.259 kg** (T-152 p.15
  16.667 at A books 15 x 0.60 m beyond the span).

A second panel for an independent pick: GF-018 y (9 continuous + 9 edge ends at A), rows in the group ledger.

## 6. Owner manual method vs drawing-derived method (ERS s.2.2), who is right

No owner manual method for slab top bars (owner rebar decisions: t at export; lap proposal not approved, not used; Q-71
not extended to slabs). Drawing-derived = p.15 by support class; note 2 = NOTE_BASIS alternative. Freelancer: one lump
5,400 kg for all slabs, no bar population: RULE_DIFFERENCE, no %. Verdict proposals: F-T316-01 ENGINE_WRONG (omission:
the drawn across-beam part, all readings); F-T316-02 ENGINE_WRONG (an extent past the span is not a physical bar);
note 2 vs p.15 on continuous / edge ends UNRESOLVED (designer: two documents of the set); step / irregular / opening
ends UNRESOLVED (no detail).

## 7. Designer items (ERS s.6 format; for the Lead's consultant list, not owner questions: ERS 2.7 not met)

1. **Top-bar extent: plan note 2 vs p.15 (694.418 kg on continuous ends + 232.661 kg on edge ends of the spread).**
   Evidence: note 2 'length one third of the span'; p.15 0.30 max(L1, L2) from the face / 0.25 L1, and p.15 delegates
   only size and spacing to the plan. Investigation: per end, per support (this ledger). Alternatives: note 2 whole
   bar, note 2 each side, p.15. Recommendation: none between documents (designer). HELD as a BOUND; lane I continues.
2. **Short spans (F-T316-02)**: one through bar or two overlapping bars where the two p.15 extents exceed the span.
3. **Hook-down leg and top cover at the edge beam (F-T316-01)**; the 50 % extension where concrete lies beyond.
4. **Note 3 at the tank panels (F-T316-03)** and whether note 2 adds bars over a (T&B) mesh.
5. **Top bars at level steps, composite / irregular supports and opening edges** (186.611 kg of the spread, HELD).

## 8. Rules, tests, lesson

Rules R316-1 .. R316-10 (module docstring; research rules, no rule-file version). Tests `tests/t316_slab_top_bars`
(22 PASS): villa V316 (two spans 4.00 + 5.00 m on B1 0.25 / B2 0.20 / B3 0.25, 1.20 m cantilever, 3.00 m wide,
5 o 10/m): B1 group [1.21, 1.25] m/bar -> 11.203704 .. 12.345679 kg; B2 3.20 m/bar -> 29.629630 .. 31.604938 kg; B3
[1.46, 1.50] -> 13.518519 .. 14.814815 kg; cantilever root HELD; mirror invariant; short-span bound. Adverse (refused):
0.25 / 0.30 x the SHORTER span, own span for an unknown other span, a note length on a drawn bar, a hook-leg value, a
group booked on both sides / a side twice / three sides, mm units, an unknown class, a held class given an extent, a
cause split that does not close. Alsenan pins: committed files reproduce, 98 lines / 5,914 ends / 283 groups, class
split of the 1,113.683 kg, F-01 .. F-03 figures, HELD blank, the 2F-047 y hand example.

Lessons-register row proposed (ERS s.7): 2026-10-28 | the slab top-bar spread (1,113.683 kg) was carried as one
'designer reading' item, but end by end 16.8 % of it sits on supports no detail draws, the drawn top anchor across the
edge beam (122.574 .. 150.278 kg) is in no reading, and 81.746 kg of the high reading lies past the clear span of
short panels (T-316) | top extents were applied per bar end from formulas without classifying the support or closing
the two ends of one span against the span | classify every top-bar end by its support before any extent; apply the
typical detail's extent from the face with the LONGER clear span, add the drawn crossing / across-beam part, hold
undrawn legs and classes, and never let the two ends of one bar line exceed its clear span (every villa; slabs; the
same check for beam top bars over supports) | tests/t316_slab_top_bars (shorter span refused, past-span bound, leg value
refused, both-sides refused) | OPEN until lane I re-bases the top line and the designer items return.

## 9. Not done / uncertain

- No candidate kg changed; the consumer file is the lane I input (owner 10:33).
- The across-beam bound uses the T-307 drawn band width (unmarked bands are not tied to a schedule row, T-307 s.8).
- The top count stays the T-152 note-2 placement (rate 5 / m over each panel's own extent); the physical bar count over
  a support shared by two panels of different widths is the count convention (COUNT_CONVENTION, 107.270 kg).
- The p.15 detail is not to scale; only its dimension text and the drawn order of bars (hook outboard of the 40 CL.
  end) are used.
