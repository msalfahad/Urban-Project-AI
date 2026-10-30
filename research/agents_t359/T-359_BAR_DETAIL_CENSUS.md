# T-359 Bar-detail census for the elements outside the released rebar route (development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPncf52XxUvFXBu26XaV. A source census, not a takeoff: **no kg and
no bar count is computed** (owner 2026-10-25 10:33). Nothing is wired; no candidate line, rule or released quantity
changes. Families B11-03 (stairs / pool / domes / tank / pit / boundary wall) and B7-14 (stair reinforcement) stay
BLOCKED_BY_SOURCE / HELD_IN_CANDIDATE; this census says, attribute by attribute, why.

## Sources (re-read this run)

Drive "Alsenan chalet project" (read-only; private copies in the git-excluded folder, never committed):
'ST7757 dxf.dxf' (sha256 9f9d1179..; 1,860 text entities dumped by handle) and 'ST7757.pdf' (sha256 74da1523..; 16 pages,
no text layer; rendered at 60 / 170 / 200 / 250 / 300 dpi and read by eye): p.3 (E1 / D1 riser lines), p.4 / p.5 / p.6
slab plans, p.7 DETAIL OF SWIMMING POOL and DETAIL OF DOME, p.13, p.14 DETAIL OF LIFT WITH ISOLATED FOOTING and
TYPICAL BOUNDARY WALL (plan + section A-A), p.15, p.16 TYPICAL STEEL LAYOUT - STAIR SECTION and TYPICAL DETAIL OF
STAIR BEAM. Sheets 13 - 16 are not in the DXF: their labels are cited by sheet, detail and position.
Rules: OWNER_RULE_REBAR_2026-10-24, Q-71 (links and footings), owner option B 2026-10-29 (only drawn / printed bar parts
counted, undrawn parts HELD), Q-26 A (flat pool floor), Q-47 A, ENGINEERING_REASONING_STANDARD s.2 - s.4. RFI ids from
rfi/A_PRIORITY_RFI.md and rfi/B_REMAINING_RFI.md (validated by the code).

Files: `t359_bar_census.py` (pure module: notation reader, attribute states, countability, double-count check),
`t359_alsenan_input.py` -> `ALSENAN_BAR_DETAIL_INPUT.json` (74 populations, printed readings only), outputs
`T359_MATRIX.csv` (element x attribute matrix, acceptance (a) + (b)) and `T359_SUMMARY.json`. Tests
`tests/t359_bar_census` (16, synthetic villa + adverse + one regression on the committed input). Repeat:
`python -I t359_bar_census.py ALSENAN_BAR_DETAIL_INPUT.json --csv T359_MATRIX.csv --json T359_SUMMARY.json`.

## 1. Method (notation before arithmetic)

Each printed label is read before any number is used: `n ø d/m` = a RATE (bars per metre of distribution width, never
a count); `ø d/s cm` = a SPACING (never a count); `n ø d` = an explicit COUNT; `n ø d/s cm` = COUNT_PER_SPACING (meaning
not settled: width class or spacing, total or per face, the class of RFI-B-S19); `d/s cm` without a bar symbol =
DIAMETER_MISSING; a spacing without a unit (`ø8/15`, `ø8/20`) = spacing NOT_PRINTED. Qualifiers `(T&B)`, `(B.W)`, `/Top`
are layer notes, read separately. Seven attributes per population: mark, diameter, spacing or count, layer, direction,
extent, end shape; each PRINTED (with handle / position), PRINTED_TYPICAL (only on a typical / N.T.S. detail no project
print ties to the element), NOT_PRINTED, NOT_APPLICABLE, or RULE (an answered owner rule; the code refuses an unanswered
one). A population is COUNTABLE_NOW only when no attribute is NOT_PRINTED or PRINTED_TYPICAL; COUNTABLE_AFTER when every
blocking attribute is asked in an existing RFI; otherwise GAP with a NEW gap id; OWNED_ELSEWHERE when another ledger owns
the bars; NOT_DRAWN when nothing is printed (never 0).

Owner manual method vs drawing-derived method: the owner has no recorded manual method for the reinforcement of these
special elements (OWNER_RULE_REBAR_2026-10-24 sets units and keeps laps under assessment); the drawing-derived reading is
the only one, and it is shown in full in the matrix.

## 2. Result (74 populations; acceptance (a) / (b))

| Element | Populations | COUNTABLE_NOW | COUNTABLE_AFTER (RFI) | GAP (new) | OWNED_ELSEWHERE | NOT_DRAWN |
|---|---|---|---|---|---|---|
| Stair ST-01 (GF->1F p.4, 1F->2F p.5) | 14 | 0 | 0 | 11 (G-T359-1) | 2 (stair beams B3 BM-GF-015, BM-1F-001, T-149 HELD_DEFINED) | 1 (winder MS1-T, RFI-S24) |
| Stair ST-02 (round) | 12 | 0 | 0 | 10 (G-T359-1; extents also RFI-A03 / RFI-S27) | 2 (GF-126 slab 6ø14/m T-152; stair beam BM-GF-057) | 0 |
| Stair E1 / D1 | 2 | 0 | 0 | 0 | 0 | 2 (RFI-S26) |
| Pool | 16 | 0 | 15 (RFI-B-S11) | 0 | 0 | 1 (R2 outer vertical, no label; RFI-B-S11) |
| Terrace domes A / B | 12 | 0 | 3 (east ring T / B / links: RFI-S17) | 5 (shell x 4, east ring side bars: G-T359-3) | 4 (west ring = released BM-1F-028) | 0 |
| Tower dome | 1 | 0 | 0 | 0 | 0 | 1 (RFI-S28) |
| Roof water tank | 2 | 0 | 0 | 0 | 1 (slab 2F-011, T-152 HELD) | 1 (walls / base / cover, G-T359-4) |
| Lift pit | 5 | 0 | 0 | 4 (depth L-1 + G-T359-5) | 1 (raft FF, T-136 HELD) | 0 |
| Boundary wall | 10 | 0 | 1 (pad 7ø12: RFI-S04) | 8 (G-T359-6 / -7; extents RFI-S03 / RFI-S04) | 0 | 1 (column links, G-T359-6) |
| **Total** | **74** | **0** | **19** | **38** | **10** | **7** |

What each element PRINTS (handles / positions in the matrix):

- **ST-01**: plan main bars 8ø16/m along both flights (p.4 dxf 490 / 491; p.5 dxf 748 / 749) and across the landing strip
  (p.4 48F; p.5 747): mark, diameter, rate, direction and the drawn extent PRINTED on the project plan; the LAYER is only on
  the typical p.16. Everything else (top bars at head / foot, ø12/20cm distribution, ø8/15 step bars, 1ø12 nosing, 6ø12/m
  landing top) is printed only on the N.T.S. typical: PRINTED_TYPICAL, lengths and legs drawn, never dimensioned.
- **ST-02**: 8ø16/m on the straight flight (dxf 53D), along the arc (dxf 5BC) and along the straight run east of CA (PDF
  only; no modelspace text entity found for it); curved part soffit / thickness RFI-S27, levels RFI-A03.
- **E1, D1**: no bar text within 3 m of their riser lines (dxf 18A .. 179, 1C4 .. 1C7): NOT_DRAWN (RFI-S26 asks whether
  they are steps on fill or a waist slab).
- **Pool** (p.7, all with handles): R1 deep wall 7ø14/m outer vertical (1893), 7ø12/m water vertical (1906), ø12/20cm
  horizontal both faces (188D outer, 18FC water), R2 shallow wall 6ø12/m water vertical (192F), ø10/20cm both faces
  (191F, 192E), rim 3ø16 (1896), corner 3ø16 (1881), step 4ø16 (192B); floor 7ø14/m top / bottom (18B0, 18AA / 19B0),
  6ø14/m distribution (18AD), slope 6ø12/m (1907 / 18D3), shallow 6ø12/m (18F0 / 18F8). Every diameter, rate, face and
  direction is PRINTED; the blocking attribute is the EXTENT: which zone's population the flat 1.15 m pool (Q-26 A) takes
  is exactly RFI-B-S11. Bar legs and ring laps: option B (drawn part counted, legs HELD).
- **Domes** (p.7): shell ø12/15cm two directions (1A0E meridians, 1A15 hoops), one mat drawn; shell 10 (19B1), span
  442 (1A38), rise 190 (1A6D) printed; NOT printed: bar position in the 10 cm shell, crown curtailment, anchorage into the
  ring, hoop laps. Ring 3ø16 top (1A47 / 1A68), 3ø18 bottom (1A4B / 1A6C), 2ø14/20cm sides (1A37 / 1A66, meaning not
  settled), 8ø8/m links (1A29 / 1A58); ring depth AS PER ARCH (182F).
- **Tank**: only the slab under it is printed (p.6 'WATER TANK PLACE' 1A85; T 18 (T&B), 7ø14/m 7A7, 6ø14/m 7A8, (T&B)
  7AF / 7B0), owned by the slab ledger; the tank itself is drawn in neither discipline.
- **Lift pit** (p.14, a detail whose Arabic subtitle calls it typical; the only lift detail): wall 20 thick, 6ø16/m
  vertical and 6ø12/m horizontal on both faces, 2ø12 at the top, two '2 ø16' at the wall foot, raft 'AS PER SCH.' (FF);
  pit depth 'As per Lift Manufactures recommendations' (L-1); embedment, laps and corner anchorage not printed.
- **Boundary wall** (p.14): column 20 x 30 4ø14 (links drawn, unlabelled), upper G.B 20 x 40 at N.G. and lower G.B at
  'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL', both labelled 2ø14 (T&B) / 3ø16 (T&B) / ø8/20 STIRRUPS, pad 130 x 80 x 30
  7ø12 (across the 80, up-turned ends drawn) and 4ø12 (B.W); positions 'SEE ARCH PLAN' (none marked, RFI-S04).

## 3. Double count (acceptance (c)): 0

Released STR.REBAR lines that touch these elements: only BM-1F-028 (west dome ring = beam B4, RELEASED with the schedule
bars 4ø16 bottom / 2ø12 top, links held on Q-71). The dome detail's ring bars for that ring are OWNED_ELSEWHERE and never
added (the detail vs schedule difference is CF-S8.3-04, already recorded). Every other neighbour is HELD in its own
ledger and listed here as OWNED_ELSEWHERE with its id: stair beams BM-GF-015 / BM-1F-001 / BM-GF-057 (T-149,
HELD_DEFINED, crank RFI-B-S22), slab GF-126 (T-152), slab 2F-011 under the tank (T-152 HELD 143.382 .. 149.310 kg), lift
raft FF (T-136 HELD). `double_count` over the 74 populations returns [] (test).

## 4. Findings for the Checker / Lead (no quantity changed)

- **F-T359-1 (stair top bars at a foot on a ground beam).** p.16 lower section prints the top bars over the flight foot
  that sits on the 3ø14 / 4ø16 G.B as **6ø16/m** (label above the G.B and the exploded bar with its leg into the G.B,
  re-read at 300 dpi); the upper section's foot on the +2.00 landing and both heads print 6ø14/m. The merged T-166 stair
  ledger (HELD, B7-14) carries 6ø14/m at every foot and no foot top bar on MS1-L and RS-S. Effect only inside the held
  stair range (diameter 16 vs 14 on that population: x 1.306 per metre of bar); whether the typical governs a given
  Alsenan flight is G-T359-1. Proposed verdict: UNRESOLVED (reading confirmed, applicability not ruled).
- **F-T359-2 (pool outer horizontal bar diameter).** DXF text 188D on the pool detail prints **ø12/20cm**; the PDF clips the
  bar symbol at the sheet edge ('12/20cm'). T-191 read ø12 by analogy with the water-face label 18FC; the diameter is now
  directly PRINTED. No quantity change; T-191's reading confirmed from a second print.
- **F-T359-3 (unit-less spacings).** 'ø8/15' (stair step bars, p.16) and 'ø8/20 STIRRUPS' (boundary G.B, p.14) print no
  unit; elsewhere on the same sheets the unit is printed ('ø8/15cm' G.B links p.16, 'ø12/20cm'). Read as NOT_PRINTED,
  never defaulted to cm.
- **F-T359-4 (qualifiers).** The boundary-wall G.B labels both carry '(T&B)' (2ø14 (T&B) and 3ø16 (T&B)) while the section
  draws 2 bars top and 3 bottom; the pad label '4ø12 (B.W)' does not define B.W (both ways, or the B.W beam row of p.10).
  Both are notation questions before any count (G-T359-7).

## 5. NEW gaps for the Lead (each blocking attribute asked in no RFI)

| Gap | Populations | What is not printed | Proposed home |
|---|---|---|---|
| G-T359-1 | 21 stair populations (ST-01, ST-02) | whether the p.16 TYPICAL section governs each Alsenan flight (layer of the plan's 8ø16/m; every other stair bar exists only on the typical, lengths and legs undimensioned) | one structural RFI in list B beside S24 / S27 / A03, or a Lead ruling if the set's own notes settle typical applicability |
| G-T359-3 | 5 dome populations | shell bar position / cover in the 10 cm shell, crown curtailment, anchorage into the ring, hoop laps; '2ø14/20cm' meaning | RFI-B list (dome detail), beside RFI-S17 |
| G-T359-4 | tank structure | walls, base, cover of the roof tank: drawn in neither discipline (T-204) | RFI-B (designer item; T-204 placeholders) |
| G-T359-5 | 4 lift-pit wall populations | vertical-bar embedment in the raft, laps, corner anchorage (pit depth itself is L-1) | RFI-B beside RFI-B-S14 |
| G-T359-6 | boundary columns | column links (drawn, unlabelled), column height, starters into the G.B | RFI-S04 extension |
| G-T359-7 | boundary G.B and pad | '(T&B)' on both G.B labels vs 2 top / 3 bottom drawn; 'ø8/20' unit; '(B.W)' on the pad bars | RFI-S03 / RFI-S04 extension |

No owner question: each gap is a designer drawing item (ERS s.2.7), not an owner decision.

## 6. Proposed lessons-register row (ERS s.7)

| 2026-10-30 | Special-element steel (stairs, pool, domes, tank, pit, boundary wall) stayed 'BLOCKED_BY_SOURCE: bar details' for days without a statement of which bar attribute is missing; a typical-section bar, a unit-less spacing and a '(T&B)' qualifier could each be read as a value | blocking was recorded per family, not per population and attribute | every bar population is read attribute by attribute (mark, diameter, spacing / count, layer, direction, extent, end shape) before arithmetic; a value printed only on a typical / N.T.S. detail is PRINTED_TYPICAL, never a project value; a spacing without a unit and an undefined qualifier are NOT_PRINTED; a population is countable only with no NOT_PRINTED / PRINTED_TYPICAL attribute, or after a named RFI (scope: every villa, every bar population; provenance T-359) | tests/t359_bar_census (spacing as count refused, diameter-less mark refused, typical-only stair bar refused, unknown RFI / unanswered rule refused, double count against a released line) | PROPOSED |

## 7. Not done / uncertain

No kg, no count (by design). The ST-02 horizontal 8ø16/m label is read from the PDF only (no modelspace text; it may sit
in a block). The lift and boundary details are typical-titled; they are treated as the project's own details because they
are the only ones for those elements (the lift detail's applicability falls under G-T359-5 if the Lead rules otherwise).
B7-14 / B11-03 capability unchanged; the census is a research piece for lane I, not an integration.
