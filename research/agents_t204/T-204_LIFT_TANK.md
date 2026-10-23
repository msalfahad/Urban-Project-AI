# T-204 Lift core and roof water tank as structural elements (development villa; rule for every villa)

Worker 1 (lane S), 2026-10-23. Research ledger + unwired component module, NOT wired into any method version; the
released default ARCH_TAKEOFF_V2.9 + route G and the V3.0.x candidate are unchanged; no quantity is released.
ERS applied: s.2 step 1 (element defined first, split into components), s.2 step 2 (evidence hierarchy: drawing,
schedule, detail, owner rules), s.2 step 3-4 (first principles, reconciliation in units), s.3 (one element, several
geometries; ownership; absence vs not searched), s.4 (rule + test), s.7 (lesson row below).

Files: `lift_tank_v1.py` (LIFT_TANK_V1, stdlib, imports no engine module), `alsenan_t204.py` (development-villa
readings + continuity re-run), `LEDGER_T204.csv`, `FINDINGS_T204.csv`, `summary.json`; tests `tests/t204_lift_tank/`
(villa L synthetic hand truth + adverse cases; development-villa regression). Repeat:
`python3 -I research/agents_t204/alsenan_t204.py [--write]`.

## 1. Sources read this run (private copies only, never committed; cited by handle / sheet title)

| Source (Drive "Alsenan chalet project") | What it prints for these elements |
|---|---|
| ST7757 dxf.dxf (sha 9f9d1179), FOUNDATION PLAN | pit ring S-BW 10EB 2200 x 2200 / 10EA 1800 x 1800, RC cross-hatch 10E9 (ANSI37, the hatch of the RC boundary wall); columns 1099 C1 200x500, 1093 C2 200x500, 1096 C2 200x500, 1090 C9 250x1000 (marks 109D / 109C / 109B / 109A); FF outline 1B2B 4600 x 4500 under mark 1676 |
| same, GROUND BEAMS PLAN | the same ring 7C2 / 7BE / hatch 7BD and columns 1EC / 1EF / 1F2 / 1F5; ground-beam edges (layer 1: 15C / 7CC, 7E3 / 17C, 177 / 7CD, 15E / 15F, 15D / 7C8, 17E / 17F) stop on the ring's outer face (no beam over the ring) |
| same, footing schedule INSERT 2B1E | FF: W 460, H 450, depth 55; top 6 d14/m both ways, bottom 9 d14/m both ways |
| same, GF / FIRST FLOOR ROOF SLAB | shaft opening S-OPENING 54F / 550 and 73F / 740 over the box; beams B14 / B7 / B1 (GF roof), B7 / B7 / B1 / B1 (1F roof) |
| same, SECOND FLOOR ROOF SLAB (+13.90) | NO opening over the lift box; slab bars S-REIN-SLAB 792 / 794 / 795 and callouts 791 / 793 (5 d10/m) run inside it: the roof slab closes the shaft (frame placed by the four lift columns 41E / 421 / 41B / 418; C9 is 200 x 700 there) |
| same, all text (model space + every block, EN + AR) | 'WATER TANK PLACE' (1A85) only; no LIFT / PIT / ELEV text. The DXF has one paper layout ('DETAILS'): it does not carry the PDF's DETAILS (2) sheet |
| ST7757.pdf (sha 74da1523) p.14 DETAILS (2) | **"DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)"**, Arabic subtitle: typical detail of the lift base in plots without basement. RC pit walls '20' on the footing; vertical 6 d16/m and horizontal 6 d12/m on both faces; 2 d12 at the wall top; 2 d16 + 2 d16 in the footing under each wall; pit depth "As Per Lift Manufactures recommendations"; pit width "AS ARCH."; footing depth / projection "AS PER SCHEDULE"; above the F.F.L. the shaft walls "AS PER PLAN"; waterproofing membrane under and round the footing and up the outer wall faces, protection board, "5cm Screed" under the footing, "10cm Plain con." below, "Well graded clean compacted fill from excavation material" outside |
| ST7757.pdf p.8 notes 19 / 20 | 19: beams tie the lift columns at 3.00 m where the storey is taller than 4.30 m, round the lift shaft; 20: walls containing columns are built to the column thickness |
| ST7757.pdf p.15 / p.16 | no tank and no lift item (twisted column, slab-on-beams typical, beam in casement, stair typicals) |
| P7757.dxf (sha ab54dd55), all text EN + AR | no lift / elevator / tank / pit text; the shaft is drawn unlabelled 1.80 x 1.80 inside, walls 0.20 (T-063 s.5) |

Reused with citation (WORKFLOW_CONTROLS s.10 rule 5): T-065 (FF 11.385 m3 in the footing line), S8.1A (ring regions
0.36 / 0.36 / 0.24 / 0.14 m2), T-184 s.2 (lift box, storey levels), S8.4 + T-166 s.4 + T-152 (tank panels and steel),
T-188 (inventory), D-43 / D-44 / D-52, freelancer row ids of T-196.

**Correction to the T-188 inventory (and the Checker's 08:02 note "no LIFT / PIT / TANK detail"):** the statement is
true of the DXF only. The structural PDF p.14 prints a lift pit detail (typical, for exactly this case: isolated lift
base, no basement). The pit WALLS are drawn (plan ring on two foundation-level plans + the detail); only the pit DEPTH is
left to the lift manufacturer. The tank finding stands (no tank member in either discipline).

## 2. Physical elements and components (ERS s.2 step 1)

LIFT-01 (lift box 1.80 x 1.80 inside, east of the ST-01 shaft; occupies FDN pit, GF, 1F, 2F; closed by the +13.90 slab):

| Component | Printed / drawn value | Owner line | Status |
|---|---|---|---|
| Pit base = FF footing | 4.60 x 4.50 x 0.55 = 11.385 m3; pit floor = top of FF (p.14) | CONC.FOOTING (existing): listed, never re-added | DRAWING-CONFIRMED (T-065) |
| Lift columns C1 / C2 / C2 / C9 | sections 0.10 / 0.10 / 0.10 / 0.20 m2 inside the ring band | neck / column lines (existing), billed at full section through the pit height | listed (R-CONC-OWN-1) |
| Pit ring, plan | gross 2.20^2 - 1.80^2 = 1.600 m2 (= 8.00 m centreline x 0.20); net of the column sections **1.100 m2** (= 0.20 x (1.20 + 0.70 + 1.80 + 1.80); = S8.1A's four wall regions) | CONC.LIFT_PIT_WALL (new) | DRAWING-CONFIRMED |
| Pit wall concrete | 1.100 m2 x pit height | CONC.LIFT_PIT_WALL (new) | **HELD**: pit height (base top to ring top) not printed ("as per lift manufacturer"); the foundation level chain is HELD too (T-200) |
| Pit wall formwork | (inner 5.50 + outer 5.50 m of wall face between column faces) x pit height | FORMWORK.LIFT_PIT_WALL (new) | HELD (height); column faces stay in the column formwork |
| Pit wall bars | vertical 6 d16/m both faces: counts C 66.0 / A 70 / B 78 bars (open runs 1.20 / 0.70 / 1.80 / 1.80 between column faces) = 104.30 / 110.62 / 123.26 kg per metre of pit height; horizontal 6 d12/m both faces on 11.00 m of run = 58.67 kg per metre of height before anchorage; 2 d12 top on 5.50 m = 9.78 kg and 4 d16 in the base on 8.00 m = 50.57 kg before laps | BAR_STEEL.LIFT_PIT_WALL (new) | HELD (height, embedment, anchorage, laps not printed in the typical detail) |
| Membrane, fixed part | base soffit 4.60 x 4.50 = 20.700; base sides 2 x 9.10 x (0.55 + 0.05 screed) = 10.920; base top outside the pit envelope 20.700 - 4.890 = 15.810 m2 (47.430 m2) | WP.LIFT_PIT (new; lane A owner method for laps / procurement) | DRAWING-CONFIRMED geometry |
| Membrane, pit walls | envelope outline 8.90 m (8.80 + C9's two 0.05 returns) x pit height | WP.LIFT_PIT (new) | HELD (height) |
| Protection board | base sides + top 26.730 m2; walls 8.90 m x pit height | WP.LIFT_PIT (new) | 26.730 DRAWING-CONFIRMED; walls HELD |
| Screed under the base | 20.700 x 0.05 = 1.035 m3 | WP.LIFT_PIT / screed (new) | DRAWING-CONFIRMED |
| Plain concrete 10 cm under | - | blinding line (existing) | listed |
| Backfill round the pit | "clean compacted fill from excavation material" | excavation / backfill (T-170) | HELD with the foundation levels |
| GF lift tie beams (note 19) | GF storey 4.50 > 4.30: clear runs between column faces 5.50 m at +3.00; 1F / 2F 4.20 <= 4.30: not required (FFL intervals; T-200 caveat) | CONC.LIFT_TIE_BEAM (new) | length DRAWING-CONFIRMED, concrete HELD (D-43 section) |
| Shaft walls above F.F.L. | p.14 "AS PER PLAN"; no RC ring drawn above the ground-beam plan; architecture 0.20 | BLOCKWORK (lane A, T-143 GF W08 / W09 / W13 / W14) | listed, not structural |
| Shaft openings 1F / 2F floors, landing doors | S-OPENING 54F / 550, 73F / 740; lift doors supplier item | slab deductions; lane A (T-128) | listed |

TANK-01 ("WATER TANK PLACE" on the +13.90 roof):

| Component | Evidence | Owner line | Status |
|---|---|---|---|
| Supporting roof panels 2F-011 / 2F-013 (T 18, T&B) | S8.4 1.4823 + 0.972 m3; T-152 steel | slab lines (existing) | listed, never re-added |
| Tank walls / base / cover | not drawn in either discipline (sheets searched above + T-166 s.4) | CONC.ROOF_TANK, BAR_STEEL.ROOF_TANK, WP.ROOF_TANK (new placeholders) | **HELD**, designer item (S8.4 Q-S8.4-01 / -07: type, size, supports), never 0 |
| C2 / C3 at the tank, B15 20x120 | heights 3.00 .. 3.80 (D-44), up / downstand (D-44), note 2 on T&B (D-52) | column / beam / slab lines | HELD as before |

## 3. Engine vs freelancer (development reference; units first)

- **Lift pit walls**: engine (released A, V3.0.5, V3.0.6) NO line (silent omission, T-188); freelancer RC:S13:11 "lift walls
  20 cm" 8.00 x 0.20 x 1.50 = **2.400 m3**. Reconciled to the cause, in units:
  plan 8.00 x 0.20 = 1.600 m2 = the drawn ring (0.000 m2 difference: same scope); of it 0.500 m2 is the four lift columns,
  which his neck rows also bill at 1.50 m (RC:S13:16 C1 x1, :17 C2 x4 incl. the two lift C2, :24 C9 x2 incl. the lift
  C9): 0.500 x 1.50 = **0.750 m3 counted twice** (R-CONC-OWN-1); the remaining 1.100 x 1.50 = 1.650 m3 rests on his 1.50 m,
  which is his neck height, not a printed pit depth. 1.650 + 0.750 = 2.400: no residual.
  Verdicts proposed: scope AGREE; ownership ENGINE_RIGHT (0.750 m3 at his height, hand calculation above from the drawn
  sections); height UNRESOLVED (designer / lift supplier: pit depth). Line proposal: HELD, 1.100 m2 x pit height.
- **Roof tank**: freelancer no row; engine no line. Now a HELD placeholder line set with the designer item (scope found,
  never 0). No comparison.
- **New scope found** (not in any engine state; the freelancer waterproofing / screed workbooks were NOT read this run, so
  no comparison): lift-base membrane 47.430 m2, protection board 26.730 m2, screed 1.035 m3 DRAWING-CONFIRMED from p.14 +
  FF schedule; their wall parts HELD with the pit height.
- Nothing released; scoreboard lines unchanged (concrete reference lines do not include the lift).

## 4. ELEMENT_CONTINUITY_V1 re-run (T-188 module, unchanged)

| State | LIFT-01 / TANK-01 findings |
|---|---|
| V3.0.6 (as T-188) | LIFT NO_BOQ_LINE HELD, COMPONENT_HELD (pit), END_NOT_EVIDENCED REVIEW; TANK NO_BOQ_LINE HELD, NO_STRUCTURAL_DETAIL HELD |
| V3.0.6 + T-204 proposals (HELD lines, p.14 detail recorded, +13.90 slab end evidence) | LIFT COMPONENT_HELD (pit depth only); TANK NO_STRUCTURAL_DETAIL HELD |

Whole-villa counts 17 -> 14 findings (HELD 7 -> 5, REVIEW 7 -> 6, NOT_DRAWN 3).

## 5. Rules (proposed, general, labelled; a rule change is a new rule version)

- **R-LIFT-PIT-1** (any villa without a basement; provenance: ST p.14 typical detail of this set, R-CONC-OWN-1): a lift pit
  is an RC ring standing on the lift base; plan from the drawn ring (gross = centreline x t), measured NET of the lift
  column sections in its band (the columns / necks are billed at full section); height = top of the base to the
  structural top of the ring, taken only from a printed level chain or the lift supplier's pit depth, never from a neck
  height, a finished level or a default; the base is the footing line's; formwork, bars, membrane, board and screed
  each from their own geometry; anything height-dependent is HELD until the height is printed.
- **R-ABSENT-SHEET-1** (any project file set): an absence ("no detail", "not drawn") names the FILES and SHEETS searched;
  a CAD file whose layouts do not cover every PDF sheet does not stand for the set: the missing sheets are read before
  the absence is recorded.
- **R-TANK-1** (any villa): a tank place over slab panels with no member drawn gives HELD wall / base / cover lines with
  the designer item; the panels stay slab lines.

## 6. Tests (tests/t204_lift_tank, 30)

Villa L (1.60 x 2.00 pit, 0.25 walls, four corner columns one 0.10 proud, 3.10 x 3.40 x 0.60 base, printed 1.35 height,
5 d12/m + 5 d10/m bars; a drawn roof tank 2.00 x 1.50 x 1.50): every value by hand in the test (gross 2.05, net 1.65,
runs 6.60 / 6.60, envelope 5.29 / 9.40, concrete 2.2275, formwork 17.82, membrane 10.54 / 8.45 / 5.25 / 12.69, screed
0.527, tie beam 0.528, bar counts A 34 / B 38 per face, tank walls 2.34, cover 0.63). Adverse: height not printed ->
HELD with no value; columns forgotten -> the 0.40 m2 double count shown; ring without columns = closed loop A = B;
mirror, 90-degree turn and mm give identical results; column into the pit flagged; no base -> HELD; tie-beam section
not printed -> HELD; undrawn tank -> 3 HELD + designer item, refused without it or without the sheets searched; 8 input
guards. Development villa: ring 1.60 / 1.10 / 0.50, fixed membrane parts, bar counts 35 / 39 per face, freelancer
reconciliation closes (1.65 + 0.75 = 2.40), continuity re-run, committed CSVs current.

## 7. Not done / uncertain

- Pit height, tie-beam section (D-43), the tank (Q-S8.4-01 / -07, D-44, D-52): designer items; nothing owner-level
  (ERS 2.7 not met: the drawings leave them to the designer / lift supplier).
- Proposed designer item (for the Lead's list): "Lift pit: depth from the top of FF to the GF slab (or the lift
  supplier's pit depth and the FF top level); vertical bar embedment in FF and laps / corner anchorage of the 2 d12 / 2 d16".
- The typical detail is N.T.S.: its arrangement is used, never a dimension scaled from it.
- Ground beams stop on the ring's outer face (drawn): no overlap with the ring in plan; the beam lines' own end
  basis is theirs.
- Whether the freelancer prices the lift-base membrane / screed was not checked (his waterproofing workbook not read).
- Checker re-measure suggestion: FF 4600 x 4500 (1B2B) + schedule 2B1E; the west pit wall run 1.20 m between C1 (1099)
  and C2 (1096) and the ring 10EB / 10EA; p.14 detail text.

## 8. Lessons-register row proposed (ERS s.7)

| 2026-10-23 | Lift called "no LIFT / PIT detail" (T-188, Checker 08:02) while ST PDF p.14 prints "DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)"; the freelancer's lift walls 2.40 m3 also bill the four lift columns already in his neck rows (0.75 m3) | The DXF (one DETAILS layout) was searched as if it were the whole set; ring ownership never set against the column / neck lines | An absence names files AND sheets searched; CAD layouts are reconciled to the PDF sheet list first (R-ABSENT-SHEET-1); a lift pit is an RC ring net of the lift column sections, height only from a printed chain or the lift supplier (R-LIFT-PIT-1) (any villa) | tests/t204_lift_tank (adverse: columns forgotten = double count 0.40 m2; height not printed = HELD, never 0; mirror / turn / mm) | READY (T-204) |
