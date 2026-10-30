# T-378 Stair lines on note 9 (F-T373-2): bar role first, then the authority (development villa; rule for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPncAMshuuoKywPCYdDV, branch `agents/task-T-378`. A binding,
not a takeoff: **no length computed, no candidate line, rule, method or released quantity changed**. Input for a
Checker DOWNGRADE-ONLY record (owner 2026-10-24 23:57). Drawings named by Drive folder and title only.

## 0. Inputs

- The 22 lines: T-373's LISTED_ONLY rows (`research/agents_t373/T373_LAP_BINDING.csv`, the binding of the reproduced
  V3_0_27_BOQ_LINES.json **f7972540**), joined by line id to the merged V3.0.16 extract
  (`research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json`) for basis, formula and ledger inputs; the binder refuses a
  line whose figure differs between the two (none does: same 22 ids, same kg to the cent). The V3.0.27 run was not
  re-made this run (T-373 made it; its sha is in the T-373 summary).
- Drawings re-read this run: Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523..) p.16 TYPICAL STEEL
  LAYOUT-STAIR SECTION, both sections and both exploded rows at 60 / 200 dpi (private folder only). Plans p.4 / p.5
  callouts and DXF handles as cited by the merged T-359 r2 census; T-166 ledger notes for each flight's supports.
- Files: `t378_stair_note9.py` (STAIR_NOTE9_ROLE_BINDING_V1, stdlib), `t378_alsenan_input.py` ->
  `ALSENAN_STAIR_ROLE_INPUT.json` (role and both ends of each population, printed readings only), outputs
  `T378_STAIR_ROLE_LEDGER.csv` (acceptance (a), one row per line, largest first) and `T378_SUMMARY.json` ((b)).
  Tests `tests/t378_stair_note9` (8). Repeat: `python -I research/agents_t378/t378_alsenan_input.py --check`, then
  `python -I research/agents_t378/t378_stair_note9.py --csv .. --json ..`.

## 1. Physical element and the note's scope (ERS s.2.1, s.2.5)

Note 9 (ST p.8, Arabic, PDF only): 'tie / development length of the STARTER bars (اشاير) not less than 70 x dia in
tension zones, 40 x dia in compression zones'; zone not printed (T-366). A starter is a separate bar left projecting
out of an element cast first, tied (overlapped) with the next element's bar (the column starter of p.13 is the drawn
example). A stair can have them: bars left out of a ground beam, beam or slab into the flight. So each line's bar is
given its role, and each END the figure books ('2 x' = two ends) is read on the drawing:

- STARTER: a separate bar drawn out of the support and tied with the flight bar -> inside note 9 -> bound kept
  (still a range, never released);
- NOT_STARTER: the line's own bar continues / anchors into its support as one drawn shape, ends inside its own
  element, or runs on into the next flight -> note 9 is no authority (R-T373-1) -> HELD by name, BLANK;
- UNKNOWN: support / shape not printed and a starter is one alternative; the missing print is named -> HELD.

A line keeps note 9's bound only when every booked end is a STARTER (a line is never split: a downgrade record moves
whole lines only). Owner manual method vs drawing-derived: the owner has no recorded manual method for stair end
lengths (OWNER_RULE_REBAR_2026-10-24 s.2: 40 d / 60 d is a proposal under assessment, never applied; option B
2026-10-29: only what the drawings write or draw is calculated); the drawing-derived reading is the only one.

**What p.16 draws (re-read):** every stair bar is one shape of its own population. Main 8ø16/m: slope + horizontal
into the head + end hook (UX-MAINH); slope + horizontal into the landing bottom at a landing foot (UX-MAINF), crossed
at the knee by the landing bottom bar 8ø16/m (UX-LAND: horizontal + slope up the flight); at a foot on a G.B, slope +
vertical leg into the G.B (lower section). Top bars 6ø14/m (head, landing foot) and 6ø16/m (G.B foot): own shapes with
legs. Step bar ø8/15: tread + riser L. Distribution ø12/20cm and landing top 6ø12/m: dots (straight bars). **No bar
is drawn as a separate starter tied with a flight bar, and no overlap is dimensioned.** The one family that crosses a
construction-joint-like interface (6ø16/m top bar into the G.B) is the flight bar's own leg and has no candidate line.

## 2. Result (acceptance (a), (b); every row in the CSV)

| Population (lines) | Role | Ends booked and how p.16 / the plans draw them | Class | kg now (low .. high) | Proposed |
|---|---|---|---|---|---|
| Main waist bars 8ø16/m: MS1-L, MS1-U, MS2-L, MS2-U, RS-S, RS-A (6) | flight main span steel | head: own bar into beam B20 / B23 (UX-MAINH) or into the landing (lower section); foot: own bar into the landing / slab bottom (UX-MAINF); RS-S foot runs on into the curved flight RS-C (flight to flight); **MS1-L foot UNKNOWN** | NOT_STARTER | 121.38 .. 233.64 | HELD, BLANK |
| Step bars ø8/15: same six flights (6) | step bar, tread + riser L | both leg ends inside the flight's own waist (U-STEP / UX-STEP) | NOT_STARTER | 114.28 .. 224.76 | HELD, BLANK |
| Distribution ø12/20cm: same six flights (6) | distribution across the flight, parallel to the supports | both ends at the flight's side faces; crosses no support (U-DIST dot) | NOT_STARTER | 83.61 .. 155.32 | HELD, BLANK |
| Landing strips GF / 1F, bottom 8ø16/m and top 6ø12/m (4) | landing's own span steel across the stair, wall to wall 2.50 m | both ends: own bar to the landing support at the wall line (plan p.4 48F / p.5 747; p.16 dot rows) | NOT_STARTER | 54.12 .. 104.76 | HELD, BLANK |
| **Total (22)** | | 44 ends: 43 NOT_STARTER, 1 UNKNOWN, 0 STARTER | **22 NOT_STARTER** | **373.390 .. 718.480** | **22 HELD** |

By floor: GF 14 lines 228.95 .. 440.88 kg; 1F 8 lines 144.44 .. 277.60 kg. Hand check (MS1-U main, the T-166 count
10 .. 11 bars): 10 x 2 x 40 x 0.016 = 12.80 m x 1.5802 = 20.23 kg; 11 x 2 x 70 x 0.016 = 24.64 m x 1.5802 = 38.94 kg,
the line's figures. The UNKNOWN end: MS1-L foot at the GF hall +1.00 (T-166 s.5: 'the hall foot is not detailed';
p.3 draws the stair outline only); if p.16's lower section governs it (G-T359-1) the bar's own leg goes into a G.B,
still not a starter; a starter splice there is printed nowhere. It does not change the line's class (its head end is
NOT_STARTER).

**Downgrade set: 22 lines, BOUNDED_EXPOSURE 373.390 .. 718.480 kg -> BLANK by name.** None is released: released
STR.REBAR **10,250.167987 kg unchanged**. Candidate bounded STR.REBAR after T-373's record 11,276.569488 ..
14,287.667938 kg -> **10,903.179488 .. 13,569.187938 kg** (-3.3 % .. -5.0 %), plus 22 more BLANK lines. This is
an unsupported basis removed, not steel removed: the bars' anchorage parts exist on the drawing (option B: drawn,
undimensioned, HELD) and stay HELD until a dimension or a designer answer is printed. The stair's net bar lengths
(T-166, measured / count held) are untouched.

Engine vs freelancer: the freelancer prices reinforcement as a kg/m3 lump (44.19 t) with no stair end or lap row:
**RULE_DIFFERENCE, no %**. Verdict proposal on the 22 lines: ENGINE_WRONG in basis (note 9 outside its group; bounds
only, none released).

## 3. Rule, tests

**R-T378-1 (every villa; provenance T-373 F-T373-2, T-378), an application of R-T373-1:** before a starter-bar note
values a stair bar end, the bar's physical role and each booked end's drawn shape are recorded with sheet / detail /
label; only a separate starter drawn out of the support and tied with the flight bar is inside the note's scope; the
flight's own anchorage, a bar ending inside its own element and a flight-to-flight continuation are not; a line keeps
the note's bound only when every booked end is a starter, and is otherwise HELD by name, BLANK, never 0.

Tests `tests/t378_stair_note9` (8 pass; with t373 / t359 / t366: 63 pass): normal (a drawn starter tied into a flight
keeps note 9's range, never released); adverse (flight main bar end at note 9 -> HELD; UNKNOWN without the missing
print refused, with it HELD; a landing lap at the p.15 temperature note -> HELD, an unprinted 'code default' refused;
HELD written as 0 refused, a line bound twice refused, a kept bound changed refused; role undefined, tonnes, a
released note 9 line, an end count different from the figure's, a non-note-9 line and an end without a reference all
refused); non-Alsenan villa V378 by hand (Urban bar table): starters 7 ø12 tied 2.98368 .. 5.22144 kg KEPT; main bars
8 ø16 x 2 ends 16.15872 .. 28.27776 kg HELD; step bars 10 ø8 x 2 ends 2.528 .. 4.424 kg HELD; valued 21.6704 ..
37.9232 -> 2.98368 .. 5.22144 kg; regression on the committed Alsenan binding (22 / 373.39 / 718.48 / the new range).

## 4. For the Checker (acceptance (d)) and the Lead

- Largest five lines to re-read on p.16 (CSV order): the step-bar lines of MS2-L, MS2-U, MS1-U (43.80 kg high each)
  and RS-S (39.82), then the main-bar lines (38.94 each). For a step bar: the L sits inside the step, no support.
- No owner question: ERS s.2.7 is not met (the owner rule is answered: option B; the gaps are designer items:
  G-T359-1 typical applicability, T-376's bend / lap rows).
- What would move a line back: a designer detail that draws a stair starter tied with the flight bar (it would be a
  new starter population with its own line, valued at note 9 or p.13 as printed), or dimensioned anchorages.

## 5. Lessons-register row proposed (ERS s.7)

| 2026-10-30 | 22 stair lines (373.390 .. 718.480 kg bounded) valued every bar end of flights, steps, distribution and
landings at a STARTER note since V3.0.5 | the stair ledger took 'development' as a generic length and the starter note
as its source; no step asked which end of which bar is a starter | define the bar's role and read each booked end's drawn
shape before a starter note values it; a line keeps the note only when every booked end is a drawn tied starter (every
villa; provenance T-378) | tests/t378_stair_note9 (flight end refused, drawn starter kept, HELD never 0) | PROPOSED |
