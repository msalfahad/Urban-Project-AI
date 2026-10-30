# T-359 Bar-detail census for the elements outside the released rebar route (development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPncf52XxUvFXBu26XaV. A source census, not a takeoff: **no kg and
no bar count is computed** (owner 2026-10-25 10:33). Nothing is wired; no candidate line, rule or released quantity
changes. Families B11-03 (stairs / pool / domes / tank / pit / boundary wall) and B7-14 (stair reinforcement) stay
BLOCKED_BY_SOURCE / HELD_IN_CANDIDATE; this census says, attribute by attribute, why.

## r2 (Worker 1, 2026-10-30, run session_01E6cPndinJ12mssGjZPY5M9): Checker r2 NEEDS (a) - (d)

The r1 counts in sections 2 - 5 below are superseded by this section (79 populations, not 74). Sources re-read this run:
'ST7757 dxf.dxf' sha256 9f9d1179.. and 'ST7757.pdf' sha256 74da1523.. (Drive 'Alsenan chalet project', private copies only).

**(a) Label census by handle, full detail extent.** Every TEXT entity inside the p.7 pool extent (x -77000 .. -56500,
y 40000 .. 56500 drawing units) and dome extent was swept by coordinates, not searched near the section: pool 31 texts
(26 bar labels + 3 build-up notes + title + N.I.S), dome 12 (10 bar labels + title + N.I.S); PDF-only p.16 stair
section 41 labels (two sections + two exploded rows), p.16 stair beam 5, p.14 lift 8, p.14 boundary wall 10; plus the 10
stair-panel callouts cited from p.4 / p.5. 117 listed, 110 bar labels, **110 / 110 cited** by a population
(`details` in ALSENAN_BAR_DETAIL_INPUT.json; the census now refuses to run on an uncited bar label). The p.7 shape row
(drawn under the section, not to scale, each bar a single polyline) ties as follows; legs are drawn, never dimensioned,
so every end_shape below is RULE option B with the shape's handle (shape drawn, legs held):

| Label (handle, text) | Shape (polyline / lines) | Population | What the shape prints |
|---|---|---|---|
| 187C 7ø14/m | 185B | POOL-R1-WV-OUT (with 1893) | L: outer-face vertical, foot into the floor BOTTOM layer (section 1879 + bend 1886 + 1870) |
| 18A8 7ø14/m | 185C | POOL-R1-WV-IN (with 1906) | top cap toward the outer face, U at the foot, leg into the floor TOP layer (section 18A2 + 1904 + 186C) |
| 1860 7ø14/m | 1867 + 1862 + hook 18AB | POOL-F-MAIN-T (with 18B0) | deep floor top, crank up into the slope, end hook (section 1872 + 189E) |
| 1869 7ø14/m | 1866 + 1861 | POOL-F-MAIN-B (with 18AA / 19B0) | deep floor bottom, crank up along the slope (section 19A9 + 19A7) |
| 18DB 6ø12/m | 185E + 18DA | POOL-F-SLOPE (with 1907 / 18D3) | slope, then horizontal into the shallow floor |
| 18D7 6ø12/m | hook 186B + 185F + 18D9 | POOL-F-SHALLOW (with 18F0 / 18F8) | hook, slope, horizontal along the shallow floor |
| 1929 6ø12/m | 184C | **POOL-R2-WV-OUT (new)** | L: outer-face vertical, foot into the floor BOTTOM layer |
| 18DD 6ø12/m | 18DC | POOL-R2-WV-IN (with 192F) | top cap toward the outer face, U at the foot, leg into the floor TOP layer (section 189F + 1922 / 1924 + 1925) |
| (none) | 1868 + 1865 + 1863 | POOL-F-SLOPE | hook + deep-floor horizontal + long slope: drawn, no label on the shape |
| (none) | 185D + 18D8 + 18DE | POOL-F-SHALLOW | slope + shallow horizontal + hook: drawn, no label on the shape |

The slope and shallow 6ø12/m are one cranked bar per mat on the shape row; which shape is which mat is not printed.
Dome: no shape row; the r2 sweep found **no bar line in the shell at all** (only the concrete arcs 182B / 182E on
S-EXTL.D; the leaders 1A0E / 1A15 end inside the 10 cm shell, with identical text): r1's "layer PRINTED, one mat drawn"
and "direction PRINTED" are corrected to NOT_PRINTED (status unchanged, GAP G-T359-3). p.16: each exploded shape tied to
its family (head top bar slope + horizontal + hook; foot-on-landing top bar horizontal + slope + hook; main bar
horizontal into the head + hook / into the landing bottom / vertical leg into a G.B; foot-on-G.B 6ø16/m slope + vertical
leg to the T.O.B; step bar L; nosing dot); the typical's landing edge beam (2ø12 / 4ø16) and its G.B (3ø14, 2ø14/30cm,
ø8/15cm, 4ø16) are now their own NOT_DRAWN populations (no such member on the Alsenan plans; never added). p.14 lift:
the vertical bars are drawn closed over the wall top and down to the raft bottom bars, so LIFT-WV moves GAP ->
COUNTABLE_AFTER L-1 (only the pit depth is open); the 4ø12 (B.W) leader reaches four dots (bars along the 1.30 m pad),
but '(B.W)' stays undefined (G-T359-7). r1 misnamed 192B 4ø16 'bars at the floor step': its leader reaches the dots at
the shallow-end wall foot (POOL-R2-CORNER); the shallow wall top carries two unlabelled dots 1842 / 1923 (POOL-R2-RIM,
new, COUNTABLE_AFTER RFI-B-S11; 2 dots drawn is not a printed count).

**(b) POOL R2 outer vertical re-decided: PRINTED, COUNTABLE_AFTER RFI-B-S11 (r1 NOT_DRAWN reversed).** 1929 '6ø12/m'
sits on polyline 184C, whose vertical is at x -59086, the x of the section's outer-face bar 1928 (-59080; the water-face
bar 189F is at -59910). Its return runs toward the pool along the lower line, and the section itself turns 1928 at its
foot (bend arc 1849) into the floor bottom bar 18E0: the return serves the **outer (soil) face of the floor, bottom
layer**, an L corner bar lapping the floor bottom mat, the mirror of the deep end's 187C. The water face is the separate
shape 18DD (cap over the top toward the outer face, U at the foot, leg into the floor top). T-166 read the shallow end as
"one U bar over the top, both faces"; the shape row draws two bars. Its 6ø12/m value equals the existing blank candidate
line POOL:R2:WALL_VERTICAL_OUTER_FACE (12 mm): no line changes. **New finding F-T359-5 (CONFLICT, G-T359-8):** the
deep-end water-face vertical prints d 12 in the section (1906 '7ø12/m') and d 14 on its own shape (18A8 '7ø14/m' on the
single polyline 185C: vertical + U + floor-top leg, i.e. the floor-top value 18B0); one bar cannot be both, so
POOL-R1-WV-IN moves to GAP on diameter (blank line POOL:R1:WALL_VERTICAL_INNER_FACE carries 12 mm; at 7 bars/m the
two readings differ by 1.208 / 0.888 = x1.36 per metre of that population; no kg computed). Verdict proposal UNRESOLVED
(designer item, to be added to RFI-B-S11's text by the Lead).

Counts restated: **0 COUNTABLE_NOW, 21 COUNTABLE_AFTER, 38 GAP, 10 OWNED_ELSEWHERE, 10 NOT_DRAWN (79)**. Moves from r1
(19 / 38 / 10 / 7, 74): +R2-WV-OUT (NOT_DRAWN -> AFTER), +R2-RIM (new, AFTER), LIFT-WV (GAP -> AFTER), R1-WV-IN (AFTER
-> GAP), +4 NOT_DRAWN typical members (ST-01 / ST-02 landing edge beam and G.B).

**(c) Test.** tests/t359_bar_census: a detail with an uncited bar label inside its extent (an exploded shape label, a
schedule pointer) is refused, a fully cited detail passes; a cited label missing from its detail and an orphan unlabelled
shape are refused; a CONFLICT needs both references and blocks.

**(d) Candidate binding (lane I).** Every population names the blank V3.0.16 lines it would fill
(`candidate_lines`, prefix HL:STAIR_POOL_TANK_STEEL:): **88 / 88** in-scope lines bound (20 pool, 67 stair, 1 tank), each
existing and blank (measured_net null); the binding refuses an unknown line, a valued line and an unbound in-scope line.
Populations with no line carry `no_line_reason` (dome shells / east ring, lift walls, boundary wall: not in the
candidate; the foot-on-G.B 6ø16/m: no line in T-166 (F-T359-1), an integration must not add one before G-T359-1 is
answered). Matrix columns `labels` and `candidate_lines` added (T359_MATRIX.csv).

Proposed lessons row (ERS s.7): '2026-10-30 | a bar-detail census missed the detail's own exploded bar-shape row | labels
searched near the section only | census every bar label inside the detail's extent by coordinates and tie each to one
population or name it; tie each drawn shape to its population (every villa, T-359 r2) | t359 adverse: uncited label
refused | PROPOSED'.

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
