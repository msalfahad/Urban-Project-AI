# T-307 Suspended-slab bar ends classified by support from the typical detail (lane S; Alsenan; every villa)

Worker 1, 2026-10-26, branch `agents/task-T-307`. Research ledger: nothing wired, no candidate or released kg changed,
no method or rule version, nothing released. Integration dependency of the rebar line (lane I splits the development
lines with `LANE_I_CONSUMER_T307.csv`). Development villa, not an accuracy claim. Drawings named by Drive folder and
title only. ERS s.2.1 - 2.6, s.3, s.4 applied.

## 0. Sources and run

- Candidate lines: the 294 BOUND suspended-slab lines (98 per population) of the T-306 decomposition
  (`research/agents_t306/SLAB_SPREAD_DECOMPOSITION_T306.csv`, MERGED 01358449) and their T-152 bar geometry
  (`research/agents_t152/T152_INPUT.csv`, MERGED 798e3b9).
- Drawings re-read this run (private copies in the git-excluded folder only): Drive "Alsenan chalet project" /
  "ST7757.pdf" (sha256 74da1523, the file T-152 / T-306 / the Checker used): p.15 TYP. SLAB ON BEAMS DETAIL at 600 dpi,
  bar lines traced pixel by pixel; "ST7757 dxf.dxf": the three roof-slab plans polygonised by T-139 `slab_faces.py`
  (every face's area agrees with T-139 `PANELS.csv` to 0.001 m2, dome corners split as T-139 / T-152).
- Code: `t307_bar_ends.py` (rules R307-1 .. 8, stdlib), `t307_geometry.py` (support class of each end from the drawn
  faces, shapely; bar placement = T-152's own `_segments`, read only), `t307_alsenan.py --geometry <private faces>`
  -> `BAR_END_CENSUS_T307.csv` (per line) + `BAR_END_DETAIL_T307.csv` (6,746 ends: line, reading, bar, end, class,
  support width, T-139 face id beyond; numbers only, no coordinates); `t307_alsenan.py --write | --check` ->
  `BAR_END_SUMMARY_T307.json`, `LANE_I_CONSUMER_T307.csv` (294 line ids).
- Cross-checks: every bar segment length equals T-152's (4 dp) and every end's continuity flag equals T-152's
  (0 mismatches on 6,746 bottom ends and the top-bar ends); continuous ends 1,947 (A) / 2,060 (B) = the T-306 census.

## 1. Physical element and what the detail draws (ERS s.2.1, s.3)

One END of one bottom bar of a suspended slab panel, where the bar meets the support at the panel edge. p.15 (own trace,
600 dpi; the Checker's T-306 read at 220 dpi agrees on every point except the last bullet):

- **Continuous support** (slab on both sides of the beam): 50 % of the bottom bars stop 0.125 L short of the face, the
  balance runs on across the beam (the crossing half already booked in the bottom line). **No development, no lap is
  drawn** -> 0 m, NOT_APPLICABLE_WITH_EVIDENCE.
- **Non-continuous support (edge beam)**: the continuing bottom bar runs straight past the beam's inner face to
  **'40 CL.' of the outer face** (no hook on that bar); the curtailed bar reaches the same point and **turns up to the
  top of the slab** (leg drawn, not dimensioned). Straight part = support width along the bar - 0.040 m (DRAWN basis);
  the up-turn leg is HELD. The top anchor bar (0.25 L1) hooks DOWN into the edge beam (leg not dimensioned), and the
  detail prints **"EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE"** (dashed): a conditional top-bar
  extension with no printed length (O-T306-01).
- Reading difference named, not chosen: the Checker read "both layers carried to 40 CL. ... with a turned leg"; my trace
  shows the leg on the curtailed bar only. Both agree the leg is undimensioned, so it is HELD either way; the count of
  legs is stated as a range (50 % .. 100 % of the edge-beam ends) in the consumer file.
- **Not drawn anywhere**: a bar end at a sunken-panel level step, at an opening edge with no beam, against a column or
  junction piece, across an oblique or composite support. Those ends are HELD (never 0, never a default).

## 2. Result: every end classified, every kg of the development line re-booked (residual = storage rounding)

| Support class (R307-1) | Ends A / B | Candidate note-9 kg on these ends (low A 40 d .. high B 70 d) | Drawn basis |
|---|---|---|---|
| CONTINUOUS | 1,591 / 1,683 | 468.304 .. 864.408 | 0 (NOT_APPLICABLE_WITH_EVIDENCE, p.15) |
| EDGE_BEAM (one square band, width checked against the schedule mark where printed) | 1,004 / 1,044 | 298.750 .. 541.472 | straight w - 0.040 m: **136.573 .. 150.696 kg** (DRAWING-DERIVED length, count BOUND A / B) + up-turn leg HELD |
| STEP_EDGE (one side sunken, or two sunken panels; drops not printed, D-41) | 414 / 437 | 102.222 .. 188.827 | HELD |
| IRREGULAR_SUPPORT (composite 176 / 193, short column / junction piece 75 / 90, oblique 151 / 174, mark width conflict B21 23 / 24, support not crossed 67 / 75; an end can carry several) | 259 / 298 | 70.031 .. 145.538 | HELD |
| OPENING_EDGE (no beam face beyond) | 4 / 12 | 0.988 .. 5.185 | HELD |
| CONTINUOUS_WIDE_BEAM (one square band > 0.80 m with slab beyond) | 0 / 0 | 0 | 0 (rule tested on the fixture; none on this villa) |
| less: opening-segment ends the candidate does not book (2 per bar line) | 2 / 8 extra | -0.494 .. -3.457 | in the classes above |
| **Candidate development line** | | **939.794 .. 1,741.976** (closure residual +0.006 / -0.003 kg = 3 dp storage of 98 lines) | |

Reconciliation to T-306: the spread on T-152-continuous ends (CONTINUOUS + the STEP_EDGE ends the T-152 probe found)
= 471.104 kg = T-306's 471.105 (0.001 rounding).

Development lines, proposed status (98): NOT_APPLICABLE_WITH_EVIDENCE 8 (every end continuous), BOUND_PART_WITH_HELD
59 (valued straight part + held legs / held ends), HELD 31 (no edge-beam end; step / irregular / opening ends only).

## 3. Findings (nothing changed; for the Checker and lane I)

- **F-T307-01 the note-9 basis on edge-beam ends overstates the drawn straight part ~2.2 .. 3.6 x** (298.750 .. 541.472
  kg booked vs 136.573 .. 150.696 kg drawn, before the HELD up-turn legs): 40 d .. 70 d of a d10 bar is 0.40 .. 0.70 m;
  the drawn straight part on these villas' bands (0.20 .. 0.55 m wide; 536 of 1,004 A ends at 0.20) is 0.16 .. 0.51 m.
  The legs are a designer item, so the re-based line is a partial bound, not a smaller total.
- **F-T307-02 sunken-panel steps booked as continuous.** 414 / 437 bottom ends (and 376 / 401 top ends) meet a support
  across which one or both panels are sunken (GF-015, GF-016, GF-081, GF-128, GF-141, 1F-018 per T-213, and their
  neighbours). T-152 booked the p.15 continuous case there (50 % curtailment + crossing half in the bottom line; 0.30
  max L + crossing in the top p.15 reading); no detail draws a bar at a level step: those bottom / top lines are FLAGGED
  in the consumer file (35 bottom lines), their kg unchanged pending lane I / the designer (D-41).
- **F-T307-03 slab beyond a support wider than the T-152 0.80 m probe.** 84 / 93 bottom and 79 / 87 top ends (26 / 33
  irregular + 58 / 60 step) have a slab panel past a 1.10 .. 1.78 m composite support (B27 0.90 band crossed with a
  junction or obliquely, GF-039 / GF-052 / GF-078 / GF-124 / GF-126 / GF-169 / GF-172 / GF-176 / 1F-025). T-152 booked
  them non-continuous (no curtailment, no crossing, 0.25 L1 top). Classified IRREGULAR / STEP (HELD), flagged.
- **F-T307-04 top anchor bars at edge beams carry an undimensioned hook-down leg not in any top reading** (882 / 919 top
  ends), and **153 / 163 top ends meet an edge beam with concrete beyond** (EDGE_HELD strip / another level / NOT_SLAB):
  O-T306-01's "extend 50 % ... where possible" applies there as a printed conditional extension, UNRESOLVED (blank).
  At edge beams with nothing beyond (perimeter, opening, stair) the extension is not possible.
- **F-02 / F-03 / F-04 corrected bounds** (each reading now inside its bound, R307-7): F-02 the 4 tank '(T&B)' top lines
  low 0 (was 28.663 kg in total): 0 .. 19.526 / 19.846 / 12.963 / 18.271 kg; F-03 GF-126 y top 16.223 .. 34.821 kg (was
  16.484 .. 34.543); F-04 the 3 bare-label development lines: on the old basis the '5 bars in all' low is 2.469 kg each;
  on the drawn basis GF-020 y 0 .. 2.469, 1F-041 y 0 .. 5.852 (5 bars could all be bars with no edge-beam end),
  GF-076 x 0.957 .. 1.340 kg.

## 4. Slab bound restated (valued parts only; HELD parts listed, never summed as 0)

| Population | T-306 candidate kg | Restated kg | Change |
|---|---|---|---|
| Bottom mesh | 2,922.577 .. 3,088.002 | 2,922.577 .. 3,088.002 | none (35 lines flagged, F-T307-02 / 03) |
| Top bars | 781.395 .. 2,002.348 | 752.471 .. 2,002.626 | F-02 low -28.663; F-03 low -0.261, high +0.278 |
| Development | 939.794 .. 1,741.976 | **136.573 .. 150.696 valued** + HELD: up-turn legs (1,004 .. 1,044 ends x 50 .. 100 %), step 414 .. 437, irregular 259 .. 298, opening 4 .. 12 ends, T&B top-layer ends | re-based end by end |
| **Slab total (valued)** | **4,643.766 .. 6,832.326** (spread 2,188.560) | **3,811.621 .. 5,241.324** (spread 1,429.703) | spread -758.857 |

The -758.857 kg is NOT a resolved spread. Development spread by class: continuous ends -396.104 (no bar drawn);
step ends -86.605 (now HELD; 75.000 of it on ends T-152 called continuous, so continuous + that part = the 471.104 T-306
expected); edge-beam ends -228.599 (note-9 spread 242.722 replaced by the drawn straight spread 14.123); irregular and
opening ends -79.705 (now HELD); unbooked opening-segment ends +2.963; then top F-02 / F-03 +29.202 (28.663 + 0.539).
Sum -758.848 = -758.857 less 0.009 storage rounding of the T-306 figures. The valued total is lower partly because
quantities moved to HELD; it is a range of the valued parts, not a slab total.
Freelancer: one lump 5,400 kg for all slabs, no bar population: RULE_DIFFERENCE, no % (T-152). Rebar in t at the
export boundary only: valued 3.811621 .. 5.241324 t.

## 5. Who is right (proposals for the Checker)

- Development at continuous ends: ENGINE_WRONG in basis (T-152 / T-179 research line; F-T306-01 confirmed end by end).
- Development at edge-beam ends: ENGINE_WRONG in basis (note 9 names starter bars; p.15 draws w - 0.040 + a leg);
  the drawn straight part is the measured part, the leg is UNRESOLVED (designer).
- Step / composite / opening ends: UNRESOLVED (no detail).

## 6. Designer items (ERS s.6 format, for the Lead's consultant list; not owner questions: ERS 2.7 not met)

1. **Up-turn / hook legs at edge beams.** Issue: the length of the turned leg of the bottom bar (and the hook-down leg of
   the top anchor bar) at a non-continuous support. Evidence: p.15 draws both legs, dimensions neither; two readings of
   which bottom bars carry the leg (curtailed half vs every bar). Investigation: 1,004 .. 1,044 bottom ends and 882 ..
   919 top ends sit on square edge beams. Alternatives: the leg to the top / bottom layer (slab depth less covers,
   covers are minima so not fixed) or a stated hook length. Impact: leg kg not measured (no length to apply); the count
   of legs is 1,004 .. 1,044 bottom-bar ends x 50 .. 100 % plus 882 .. 919 top ends. Recommendation: designer states the leg length and which bars carry it. HELD.
2. **Bar ends at sunken-panel steps (D-41).** Issue: bottom / top bars at a support where the slab level changes.
   Evidence: T-213 six sunken panels, drops not printed; p.15 draws one level. Impact: 414 .. 437 development ends
   (candidate note-9 102.222 .. 188.827 kg) and the curtailment / crossing booked on 35 bottom lines. HELD.
3. **Composite / irregular supports and openings without a beam** (259 .. 298 + 4 .. 12 ends). Issue: which end detail
   applies against a column, a junction or a 1.1 .. 1.8 m composite support, and at an opening edge. HELD.
4. **'EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE'** at 153 .. 163 top ends with concrete beyond the edge
   beam: length and whether it applies to cantilever strips / other-level slabs. UNRESOLVED blank.

## 7. Rules, tests, lesson

Rules R307-1 .. R307-8 (module docstring; research rules, no rule-file version). Tests `tests/t307_slab_bar_ends`
(21 PASS): villa V307 (invented two-span slab S1 / S2 over a 0.20 m internal beam, 0.25 m edge beams, '5 ø 10/m'):
x bars A 20 / B 21: 20 continuous + 20 edge ends, straight 0.21 m -> 2.592593 .. 2.722222 kg; y bars A 15 / B 16 both
ends at 0.20 m beams -> 2.962963 .. 3.160494 kg; the candidate's 9.876543 .. 18.148148 kg re-booked end by end closes;
mirror and 90 degree rotation invariant; sunken neighbour -> STEP_EDGE; 0.90 m square band -> CONTINUOUS_WIDE_BEAM;
no beam -> OPENING_EDGE; schedule width 0.30 vs drawn 0.25 or a 'schedule / drawn' conflict -> IRREGULAR. Adverse
(refused): development at a continuous end, an up-turn leg given a value, the 40 d / 60 d lap and note 9 as a basis, a
length at an opening edge, an end with no / an unknown support class, a bound that excludes its own reading, a width in
mm, a non-closing census, fewer ends than 2 per bar. Alsenan pins: class counts, class kg, 471.104 reconciliation,
F-02 .. F-04, restated bound, 294 consumer rows (HELD rows blank, never 0), summary reproduces.

Lessons-register row proposed (ERS s.7): 2026-10-26 | the slab development line booked note-9 40 d .. 70 d on every bar
end; end by end, 50 % of its low sits on continuous ends (no bar drawn), 32 % on edge-beam ends where the detail draws a
straight bar to 40 mm of the far face (0.16 .. 0.51 m drawn vs 0.40 .. 0.70 m booked) and 18 % on step / composite /
opening ends no detail covers (T-307) | a general note's length was applied without classifying each end by the support
it meets; continuity was decided by a fixed 0.80 m probe that misses wider supports and ignores level steps | classify
every bar end by its support from the drawn faces (continuous / edge beam with its drawn width / step / irregular /
opening), apply only the typical detail's drawn length to the classes it draws, hold the rest; check continuity against
level steps and supports wider than the probe (every villa; slabs, and the same method for beams / ground beams) |
tests/t307_slab_bar_ends (normal: two-span fixture; adverse: continuous-end length, undrawn leg value, lap / note-9
basis, missing class, bound excluding a reading) | OPEN until lane I splits the development line and the designer items
return.

## 8. Not done / uncertain

- No candidate kg changed (acceptance 3): the consumer file is the lane I input.
- Support widths are the drawn band widths (T-139 faces); a mark-to-schedule check runs only where a mark is printed
  inside the band (B21 0.40 drawn vs 0.45 schedule caught). Unmarked bands are not tied to a schedule row.
- The top-line end census uses the note-2 rate-5 / m bar placement of T-152; the top lines' kg are not re-based here
  (only F-02 / F-03), because their extent (note 2 vs p.15) is itself open (T-306 designer item 1).
- The T-152 continuity probe's own effect on the bottom / top kg at the flagged ends (F-T307-02 / 03) is not computed.
