# T-515: B9-02 lintel bar split (research rule proposal R-T515-1, Gate A)

Worker 1, 2026-11-05. Lane S. Research only: `research/agents_t515/t515_lintel_bars.py`, its build
`out/LINTEL_BAR_SPLIT_T515.json` and `tests/t515_lintel_bar_split/`. No hub, master, candidate, engine, rule or knowledge
file changed. The released default (V2.9 + route G) and the candidate of record are untouched.

## 1. Physical element (ERS s.2.1)

An RC lintel over an opening in a block wall carries the masonry above the head and bears on the wall each side. Its
steel, as the structural set prints it (ST7757 p.13 LINTEL SCHEDULE + LINTEL DETAIL + SECT 2-2; I re-read it this run
from the Drive copy "Alsenan chalet project / ST7757.pdf", decoded into .work/private only):

- bottom and top bars per opening-width band: L1 0-100 cm 2Ø12 / 2Ø10, L2 101-200 2Ø14 / 2Ø12, L3 201-300 3Ø16 / 3Ø14,
  L4 3Ø18 / 3Ø14, L5 4Ø18 / 3Ø14; links 5Ø8/M in every band; B = wall width;
- the detail draws the bars along the lintel, across the opening and into both 'MIN.40cm' bearings, with the ends turned
  inside the bearing; no cover, no bend length and no hook length is printed anywhere on the sheet;
- SECT 2-2 draws one closed link with hooks, no cover.

Correction to the row text / F-C-T487-1: "bottom 2 x 12, top 2 x 10" is the L1 row only. W15 is L2 (2Ø14 / 2Ø12) and
W14 is L3 (3Ø16 / 3Ø14); the ledger carries the band's own bars and the builder asserts every ledger bar text equals
its printed schedule row.

## 2. Owner manual method and drawing-derived method, side by side

| | Owner manual method | Drawing-derived method (this record) |
|---|---|---|
| Rule | OWNER_RULE_REBAR_2026-10-24: kg = L x d^2/162, stock 12 m, laps 60 d beams only where L > S; t at the boundary. Owner 2026-10-29 (B): only drawn / printed bar parts; an undrawn part HELD unless physically certain from the drawings | same unit mass (rebar_unit_mass D2_OVER_162, Urban default R3), same lap rule (rebar_lap_rule_v2, stock 12, class BEAM) |
| Main bar length | not printed as a cut length | SPAN segment = clear opening width w: COMPUTED (the bar is drawn across the opening into both bearings, so w is installed in full). IN-BEARING straight segment = 2 x (0.40 - end cover): end cover not printed -> HELD, ceiling 2 x 0.40 beside (a straight bar cannot leave the concrete length L). END BENDS drawn, not dimensioned -> HELD |
| Links | 5Ø8/M | count RATE_COUNT ceil(5 x L) (engine column_rebar policy), ceil(5 x w) beside; kg HELD (cut length needs cover + hooks; B20) |
| Laps | 60 d where L > 12 m | L at most 3.25 m here (8.30 m for the largest printed band L5): NOT_REQUIRED on every lintel, a genuine 0 |
| Figure | - | AT_LEAST (span parts only), never a full figure |

Why not "span + bearings" as the straight length (the row's wording): that length is the CONCRETE length L; the bar
stops one end cover short of each end face, so count x L x kg/m overstates every bar by 2 x cover x kg/m, and the cover is
not printed. L is therefore the ceiling of the straight part, shown beside, never the quantity. Never picked because it
is larger or smaller: the span is the only part whose length the drawing fixes.

## 3. Training villa (16 REQUIRED lintels of the merged T-453 r2 ledger = the V3.0.53 STR.CONC.LINTEL lines, element LINTEL:<id>)

| Opening | Floor | Band | Bars B / T | w m | L m | AT_LEAST kg | straight ceiling kg (beside) | links over L / span |
|---|---|---|---|---|---|---|---|---|
| D-1F-02 | 1F | L1 | 2Ø12 / 2Ø10 | 1.00 | 1.80 | 3.012346 | 5.422222 | 9 / 5 |
| D-1F-03 | 1F | L1 | 2Ø12 / 2Ø10 | 1.00 | 1.80 | 3.012346 | 5.422222 | 9 / 5 |
| D-1F-04 | 1F | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-1F-07 | 1F | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-1F-08 | 1F | L1 | 2Ø12 / 2Ø10 | 0.90 | 1.70 | 2.711111 | 5.120988 | 9 / 5 |
| D-1F-10 | 1F | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-2F-01 | 2F | L1 | 2Ø12 / 2Ø10 | 1.00 | 1.80 | 3.012346 | 5.422222 | 9 / 5 |
| D-2F-03 | 2F | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-GF-06 | GF | L1 | 2Ø12 / 2Ø10 | 1.00 | 1.80 | 3.012346 | 5.422222 | 9 / 5 |
| D-GF-10 | GF | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-GF-11 | GF | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-GF-12 | GF | L1 | 2Ø12 / 2Ø10 | 0.80 | 1.60 | 2.409877 | 4.819753 | 8 / 4 |
| D-GF-13 | GF | L1 | 2Ø12 / 2Ø10 | 1.00 | 1.80 | 3.012346 | 5.422222 | 9 / 5 |
| W14 | 1F | L3 | 3Ø16 / 3Ø14 | 2.45 | 3.25 | 20.507407 | 27.203704 | 17 / 13 |
| W15 | 1F | L2 | 2Ø14 / 2Ø12 | 1.55 | 2.35 | 6.506173 | 9.864198 | 12 / 8 |
| W18 | 1F | L1 | 2Ø12 / 2Ø10 | 0.50 | 1.30 | 1.506173 | 3.916049 | 7 / 3 |
| **16** | | | | **15.95** | **26.80** | **63.161728 kg = 0.063162 t AT_LEAST** | **106.954321** | **146 / 82** |

Hand check (any line): kg/m 12 = 0.888889, 10 = 0.617284, 14 = 1.209877, 16 = 1.580247. L1 = 488/162 = 3.012346 kg per
metre of span; W14 = (3 x 256 + 3 x 196)/162 x 2.45 = 20.507407 kg; W15 = (2 x 196 + 2 x 144)/162 x 1.55 = 6.506173 kg.
Total 3.012346 x 12.00 + 6.506173 + 20.507407 = 63.161728 kg.

HELD by name on every one of the 16: TOP / BOTTOM IN_BEARING (end cover), TOP / BOTTOM END_BENDS (bend length), LINKS kg
(cover + hooks). The installed steel is at least 63.16 kg (span parts); the straight parts alone are at most
106.95 kg (both bounds conditional on the minimum bearing 0.40 m as measured). The 44 HELD / FLAGGED lintels (W13, W26
FLAGGED; 42 HELD by the ledger's reasons) carry no bar figure (blank, never 0); an 'if built' span figure is beside only.

## 4. Freelancer comparison

The freelancer RC workbook keys one project rebar total (RC:ورقة1:25, 44.19 t) and no lintel row or lintel concrete
row (tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json). Verdict proposal: **UNRESOLVED** (no element-level figure;
whether lintel steel sits inside the 44.19 t is not stated). Engine side: ENGINE_RIGHT proposal for the 63.161728 kg
AT_LEAST by the hand calculation above. Against the earlier S8.6 research (research/alsenan_lintels_s8_6/07, not wired):
RULE_DIFFERENCE, S8.6 took a 25 mm end cover that the sheet does not print; refused here (owner (B)).

## 5. Tests

tests/t515_lintel_bar_split: synthetic villa S by hand (3 lintels, LC with no printed bearing: 21.970370 kg AT_LEAST,
links 9 / 12 / HELD), printed cover / bend sources compute; adverse: cover / bend / hook defaulted refused (4), HELD
summed as 0 refused, HELD lintel with a figure refused, width in mm / cm / 0 / negative / None refused, width outside
its band refused, bad bar / link text refused, second record refused, lap beyond the stock HELD with its count (1 splice,
60 d = 0.72 m), order invariance; training villa by hand (totals, 5 lintels, band bars, held blank, no lap, freelancer
UNRESOLVED, committed build = build, edited input refused).

## 6. Open / not done

- End cover, bend and hook lengths: not printed on ST7757; they unlock the IN_BEARING / END_BENDS / LINKS kg (a
  designer RFI item, not an owner question: ERS 2.7 not met, a drawing / consultant fact).
- Wiring into the candidate (a STR.REBAR component per B9-02 line) is integration work for a later package; this record
  is the Checker-verifiable piece.
- Jamb bearing availability (MIN 40 cm) still not measured (T-487 open check): the ceiling and the link count over L
  depend on it; the span AT_LEAST does not.

Lessons row (proposed, ERS s.7): | 2026-11-05 | a printed bar with undrawn ends was HELD as a whole | blanket HELD
hides a certain quantity; 'span + bearing' overstates by the cover | split each bar into its drawn-certain segment
(COMPUTED, AT_LEAST), its unprinted segments (HELD by name) and a ceiling beside; the concrete length is never the bar
length | tests/t515_lintel_bar_split | T-515 |
