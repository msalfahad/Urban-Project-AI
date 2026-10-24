# T-265 Ground-beam reinforcement by bar population: boundary G.B and main-house exterior ground beams (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24. Research piece, not wired: no engine, candidate or released line changed; integration
is lane I after the Checker's verdict. Development villa, not an accuracy claim. Drawings named by Drive folder and
title only; members by run id; lengths, counts and kg only.

## 0. Inputs

| Input | Read for |
|---|---|
| Drive "Alsenan chalet project" / "ST7757.pdf" p.14 (100 + 300 dpi, this run) | TYPICAL BOUNDARY WALL section A-A: upper G.B 20 wide x 40 deep, top at "N.G. LEVEL"; "2ø14 (T&B)" leader to the TOP layer (2 dots drawn), "3ø16 (T&B)" leader to the BOTTOM layer (3 dots drawn), "ø8/20 STIRRUPS"; "PLAIN CONC." 15 above N.G.; the lower G.B (same labels) is a different member (Q-28 band, not in scope) |
| same, p.13 (100 + 300 dpi, this run) | "Ground Beams. for exterior walls": width 30, depth "FOLLOW ARCH." from "Ground Floor slab level" to "Outer Normal ground level"; 3ø16 top; "2ø12/30cm" side (2 levels drawn, one dot on each face per level); 6ø16 bottom (two rows of 3 dots); "ø8/15cm" with a 135-degree hook drawn, hook length not printed |
| same, p.8 notes (80 dpi, this run) | note 9 development / tie length of starter bars >= 70 d tension, 40 d compression; note 21 side bars 2 / 3 / 4 ø12 by beam width in beams deeper than 60 cm "unless stated otherwise"; note 22 cover >= 2.5 cm beams, >= 7 cm against soil; no lap rule for beam bars |
| research/agents_t253/LEDGER_T253.csv (MERGED dff9cb79, Checker Gate A) | run lengths face to face: boundary 5 runs 44.07 m (Checker-measured); main-house exterior 16 runs + ring ARC:157+158 = 55.9912 m at D 0.95 (6 runs Checker own-measured, 11 on the T-242 geometry the Checker verified); annex 9 runs CONFLICT; court 3 runs no section |
| research/agents_t138/T138_MEMBERS.csv (MERGED) | the previous hand steel ledger of the same members (before) |

Files: `t265_gb_bars.py` (GB_BAR_POPULATION_V1, pure rules, stdlib), `t265_alsenan_check.py` (committed ledgers ->
`LEDGER_T265.csv`, `summary.json`); tests `tests/t265_gb_bar_population` (Villa E hand fixture + adverse + Alsenan pinned).

## 1. Physical elements

- **Boundary G.B** (upper beam of the boundary wall): a 0.20 x 0.40 RC band at natural ground on the plot line, carrying
  the brick boundary wall and the 20 x 30 boundary columns that pass through it (count not printed, M4). Its bars run
  the band; the columns' 4ø14 pass through it.
- **Main-house exterior ground beam**: 0.30 wide, from the GF structural top +0.95 down to natural ground +-0.00 (D-35
  settled by T-253: D = 0.95, Checker CONFIRMED the five readings), one run between the faces of the columns / necks it
  frames into.
- **Plain band**: the 15 cm "PLAIN CONC." over N.G. at A-A is court paving: NO rebar line (printed plain), never 0 kg.

## 2. Notation before arithmetic

**"(T&B)" on the boundary G.B.** Two readings: (L) literal, every label in both layers = 2ø14 + 3ø16 top AND bottom,
10 bars; (P) per layer by leader = 2ø14 top, 3ø16 bottom. Evidence: the section draws 2 dots in the top layer and 3 in
the bottom, each label's leader ends on its own layer (both beams of A-A the same); and (L) cannot be built: 5 bars
(76 mm of steel) with 4 clear gaps of at least 25 mm need 176 mm, the core inside 8 mm stirrups at the 2.5 cm minimum
cover is 134 mm. **Reading P, DRAWING-CONFIRMED; L REJECTED** (it would give 631.13 kg instead of 315.56 kg, x2.0).

**"2ø12/30cm" side bars.** "2" = one bar on each face per level (the section draws 2 levels x 2 dots, not 2 bars in
all and not 2 per face per level, which would draw 4 dots a level). "/30cm" = level pitch not exceeding 0.30 m between
the top layer and the upper bottom row. Levels = ceil(gap / 0.30) - 1 over the whole envelope of what is not printed
(cover 0.025 .. 0.10 m, clear gap between the two bottom rows 0.025 .. 0.05 m): at D 0.95 the gap is 0.652 .. 0.827 m
-> **2 levels at every corner** (the drawn section also shows 2): 4ø12 per run, invariant. Note 21 does not add side
bars: its own words "unless stated otherwise" give way to p.13, which states them.

**Stirrups "ø8/15cm" / "ø8/20".** Count A = ceil(L / s) (the frozen S5 lower bound) .. B = A + 1 (a stirrup at both
faces is not printed) = the T-138 A / B pair. Mass HELD: the hook length is not printed (the 135-degree hook is drawn)
and the covers are minimums.

## 3. Result (kg, net, lower bound: straight bars over the face-to-face run; ends / through-support pieces apart)

| Members | Length (m) | Component | Bars | kg | Status |
|---|---|---|---|---|---|
| Boundary G.B, 5 runs | 44.07 | TOP | 2ø14 | **106.639** | DRAWING-CONFIRMED (lower bound) |
| | | BOTTOM | 3ø16 | **208.925** | DRAWING-CONFIRMED (lower bound) |
| | | stirrups ø8/20 | count HELD (columns M4: at most 157..158 on 7FE#1, full run) | HELD | HELD |
| Main exterior, 16 runs + ring | 55.9912 | TOP | 3ø16 | **265.438** | DRAWING-CONFIRMED (lower bound) |
| | | BOTTOM row 1 / row 2 | 3ø16 + 3ø16 | **265.438 + 265.438** | DRAWING-CONFIRMED (lower bound) |
| | | SIDE | 2 levels x 2ø12 | **199.082** | DRAWING-CONFIRMED (lower bound) |
| | | stirrups ø8/15 | 380 .. 397 pieces (17 runs, A .. B) | mass HELD | count DRAWING-CONFIRMED |
| **Net released-candidate** | | | | **1,310.960** (boundary 315.564 + exterior 995.396) | not released |
| Annex exterior, 9 runs | 29.7063 | ALL | - | HELD (CONFLICT; reading if p.13 applied: top + bottom 422.49, not a quantity) | HELD |
| Court, 3 runs | 5.70 | ALL | - | HELD (no section) | HELD |
| Plain concrete 15 over N.G. | - | - | - | no rebar line | NO_REBAR (printed) |

Hand check (one run, for the Checker to recount): 7D0+FC#2 L 5.745: top 3 x 5.745 x 256/162 = 27.236; bottom 6 x ... =
54.471; side 4 x 5.745 x 144/162 = 20.427; total 102.13 kg; stirrups ceil(5.745 / 0.15) = 39 .. 40. Boundary 7FE#1
L 31.37: top 2 x 31.37 x 196/162 = 75.908; bottom 3 x 31.37 x 256/162 = 148.717.

Curved ring ARC:157+158: every bar set is symmetric about the beam centreline (3 top, 3 + 3 bottom, one side bar each
face), and arc length is linear in radius, so the sum of the bar arcs = count x the centreline arc 6.0873 m exactly.

HELD beside the net (never 0): bar ends / development (note 9 is written for starter bars; zone not printed),
stirrup mass (hooks), boundary stirrup count (M4), procurement splices: 7FE#1 31.37 m > 12 m stock (T-149) -> at
least 2 splices on each of its 5 bars = 10 splices, lap length not printed (never in the net).

## 4. Before / after and reconciliation (same members)

| | TOP + BOTTOM kg | SIDE kg | Boundary kg |
|---|---|---|---|
| Before: T-138 hand ledger (merged), main-house exterior runs released | 572.500 on 40.254 m | HELD, unquantified (depth D-35) | absent |
| After: this ledger | 796.319 on 55.9912 m | 199.082 | 315.564 |
| Change | **+223.819** | **+199.082** | **+315.564** |

+223.819 = 15.7373 m x 9 x 256/162 exactly: the runs T-138 held or did not re-measure, now on the Checker-verified
geometry with the exterior class (T-242 / T-253): 7E0+FD#1 3.35 (held in T-138), 145+7CA#1 1.90 (held as 0.40 + 2.30),
109+7CB#2 4.40 (inside the held 8.80 CONC/EXT run), ARC:157+158 6.0873 (not re-measured); residual 0.0014 kg (T-138
rounds 107+7CE#1 to 0.364 m). T-138's bars through the six interior columns of the 7D0/FC and 170/7C3 chains (52.62 kg)
are outside this task's face-to-face scope and are not re-counted here. Released A / candidate V3.0.12: no rebar line
carries the boundary band (ENGINE omission, 315.56 kg lower bound) and none carries the exterior side bars.

**Versus the freelancer**: his steel is a kg/m3 lump over a different scope (about 9.75 t "ground beams + ground
floor", T-141): no like-for-like line, **RULE_DIFFERENCE, no %** (URBAN-REBAR-NET-AND-PROCUREMENT@v1: never kg/m3).

## 5. Verdict proposals

| Item | Proposal |
|---|---|
| boundary "(T&B)" | per layer (2ø14 top, 3ø16 bottom) DRAWING-CONFIRMED; literal 10-bar reading REJECTED (does not fit, not drawn) |
| boundary steel 315.564 kg | DRAWING-CONFIRMED lower bound; ENGINE_WRONG (omission) in A and V3.0.12 |
| exterior side bars 4ø12 per run, 199.082 kg | DRAWING-CONFIRMED (2 levels invariant over the envelope); was HELD (T-138) |
| exterior top / bottom 796.319 kg | DRAWING-CONFIRMED lower bound on the verified geometry (+223.819 vs T-138, causes above) |
| stirrups | counts DRAWING-CONFIRMED ranges; mass HELD (hooks) |
| annex / court | HELD (CONFLICT / no section); nothing borrowed from the p.13 section |
| freelancer | RULE_DIFFERENCE (kg/m3 lump) |

## 6. Rule proposed (every villa; provenance T-265; adopted only as a new rule version)

**R-GB-BARS-1**: a ground-beam run takes the bars of the printed section that names its family, counted x its
face-to-face length x d^2/162 (lower bound; ends and through-support pieces apart); a "(T&B)" label pair is read from
the drawn dots and leaders, and a reading that cannot fit the section is rejected; side bars "n ø d / s" are n per
level with levels = ceil(gap / s) - 1, released only when invariant over the unprinted cover / row envelope; a general
note that says "unless stated otherwise" gives way to the member's detail; a plain-concrete band has no rebar line;
CONFLICT / no section -> HELD, never 0.

## 7. Lessons-register row (proposed)

2026-10-24 | Boundary-wall ground-beam steel: a literal reading of "2ø14 (T&B)" + "3ø16 (T&B)" doubles it (631.13 vs
315.56 kg) | "(T&B)" read as "both layers" without looking at the drawn bars | The section draws 2 dots top and 3 bottom
with each leader on its own layer, and 10 bars cannot fit a 0.20 m beam: a label's meaning is settled from the drawn
bars and the physical fit before any arithmetic (any villa) | tests/t265_gb_bar_population
test_boundary_band_with_corner_and_tb_reading + test_adverse_tb_literal_when_drawn_and_fitting_else_conflict | PROPOSED.

## 8. Not done / uncertain (designer items, no owner question: ERS 2.7 not met)

- Note 22 asks >= 7 cm cover against soil; at 7 cm the 0.20 m boundary G.B cannot hold 3ø16 in one layer (44 mm core).
  Counts and lengths do not depend on cover, so the steel stands; the cover / width clash goes to the designer list.
- Stirrup hooks, bar ends at supports and beam lap length are not printed (masses HELD).
- Boundary column count (M4) holds the boundary stirrup count only; the longitudinal bars are continuous through them.
- Annex (CONFLICT) and court runs (no section) stay HELD with their concrete (T-253).
