# T-269 Floor-area closure blockers the drawings can settle (Alsenan; any villa)

Worker 2, 2026-10-24. Research only: nothing is applied to any BOQ line (lane I applies it in T-240 WP3); no engine,
rule, frozen or registry file touched. Inputs (private folder, never in the repository): Drive "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55), "ST7757 dxf.dxf", p7757_arch_sheet10.pdf (section A-A), one
ARCH_TAKEOFF_V2.9 run of P7757.dxf. Run: `alsenan_t269.py --arch --st --v29 --out` -> `summary_t269.json` (areas,
statuses, handles; no coordinates). Module: `floor_blockers.py` (three general checks, below). Tests:
`tests/t269_floor_blockers` (25: hand fixtures not Alsenan, mirrored / rotated / translated, adverse cases, the summary
guard, the rebuild from the private drawings).

## 1. Result (floor area, m2)

| Piece (Checker 01:12 / 03:26 blocker) | Released A | Before (own range) | This run | Status proposed | vs freelancer |
|---|---|---|---|---|---|
| 1F living / corridor / landing face 1F-R78C367 (stair residue) | 44.8694 | 38.4585 .. 38.9785 (HELD 0.520: D-13 0.4025 + D-23 0.1175) | **38.6335** (one value) | DRAWING-CONFIRMED (Checker to verify) | 38.96: -0.3265 (-0.84 %) |
| of which D-13 foot strip 1.15 x 0.35 | in floor | 0 .. 0.4025 | **0.0575 floor** (landing nosing band) + **0.345 stair** (11th tread of MS1-U) | DRAWING-CONFIRMED | - |
| of which D-23 band 0.05 x 2.35 beside RS-A | in floor | 0 .. 0.1175 | **0.1175 floor** (stands on the slab) | DRAWING-CONFIRMED | - |
| GF pantry part of GF-RC99C2A (west of the layer-5 line B3 / AD) | 8.955 in porcelain | blocked: class + tread rule | **treads inside 0.000**: only the class blocks it (Q-37 A wet, T-240 WP2) | geometry DRAWING-CONFIRMED | - |
| GF-RC06FED (pantry, 2.800) | 2.800 porcelain | blocked: class + tread rule | **treads inside 0.000**, no flight in the face: only the class blocks it | geometry DRAWING-CONFIRMED | - |
| GF round-stair treads inside GF-RC99C2A (released deducts all) | -8.1944 | rule open (T-116 NOT_ASSESSED) | **2.070 floor** under the two overhead flights F3 + F4; **6.1244 HELD** under F1 + F2 (drawn below the cut) | 2.070 DRAWING-CONFIRMED; 6.1244 HELD | not traceable (his reception row) |

1F living: released 44.8694 is over by 6.2359 m2 (+16.1 % on 38.6335); the new value sits inside the T-113 hand range
38.588 .. 38.990 and 0.3265 under the freelancer's single row 38.96 (his row is not split: not traceable further).
Under owner Q-66 B the finish split is: porcelain 33.594 + 0.1175 = **33.7115** (living, corridor, connector); landing
marble drawn 4.865 + 0.0575 = 4.9225 (the marble line keeps the printed 4.875, T-129; 0.0475 = the well end and the
landing nosing, RULE_DIFFERENCE, unchanged). GF reception: floor 118.7333 (released) -> 120.8033 .. 126.9277 m2 with
6.1244 HELD; the pantry 8.955 + 2.800 m2 stay in the line with only their class open.

## 2. D-13: the foot of the arriving flight (1F, main stair ST-01, east lane = ground-to-first upper flight MS1-U)

Physical element: the plan strip 1.15 x 0.35 between the printed landing edge (1950 from the wall face, DIMENSION
10DF) and the last drawn nosing of the flight arriving at the +5.50 landing. Is it tread (stair) or landing (floor)?

Evidence, all on the drawings:
- 1F plan (P7757.dxf): the east lane draws 11 risers on layer 2 (A93 .. ABD, every going 0.300) and 11 nosings on
  layer 5 (A92 .. ABE), each nosing 0.050 beyond its riser toward the flight's start; the lowest drawn riser is A93 at
  the turn. The west lane draws the landing nosing AC0 on the printed landing edge.
- Section A-A (sheet 10): 12 risers on this flight (owner Q-46 A: the section count governs; counted and VERIFIED by
  the Checker in T-111, MERGED c0e8443). New this run (raster read as a check, not a measurement): on the section
  the top riser stands 1.93 .. 2.00 m from the landing's wall face (inner face of the cut wall to the riser block,
  scaled by the flight's own drawn going, 71.3 px per 0.300 m at 600 dpi), i.e. on the 1.95 line, not at 2.25 where the
  plan's last line would put it; the floor finish projects 0.05 beyond the top riser (12 px = 0.05 m).
- Structural slab plan of the 1F floor (ST7757 dxf, the GF-roof slab sheet; frame by the column pair 2FE7 / 3008 =
  ST 332 / 374, residual 0.000 mm): its copy of the stair draws **12** riser lines in the east lane, going 0.300, the
  12th (handle **459**) exactly on the arch landing edge (0.000 mm). The architectural plan omits that one line.

Calculation (R-T269-1): top riser = first drawn riser - (12 - 1) x 0.300 = the landing edge (0.000 m). Strip 0.35 x
1.15 = 0.4025 = 11th tread seen between nosings (0.30 x 1.15 = **0.345, stair**) + the landing nosing over the top
riser (0.05 x 1.15 = **0.0575, floor of the landing**). The plan-visible convention of the face partition (every plan
point once, the topmost surface) and the riser convention give the same 0.0575 (west lane: +0.0575 under the first
tread's nosing; east lane: +0.0575 in front of the top riser; only one side is counted in each convention).

Reconciliation with earlier work: T-122 (0.4025 HELD), T-129 (0.345 tread + 0.0575 landing by plan convention, label
HELD), T-111 (12th riser on the landing edge): all three agree with this split; what was missing was drawing evidence
that is not a convention. Designer item D-13 can close (the label is now drawn on the structural sheet). Not changed:
the B20 clash (the 12th riser lies inside B20, T-111 RFI) is structural and does not move the finished floor.

## 3. D-23: the 0.05 band beside the arriving round-stair flight RS-A (1F, ST-02)

Physical element: the closed band AF5 / AF6 (layer 5, closed by D23) along the flight's east side from the column face
to the top riser; T-164 (MERGED) classes it as the balustrade RL-06 (2.400 lm, DRAWING-CONFIRMED). Question: does the
floor exist under it?

Evidence: on the structural 1F floor slab sheet the slab edge of the stair opening is ONE layer-1 line (handle **289**)
along the band's FLIGHT-side face (AF5), over its full length; nothing is drawn along its outer face (AF6). The
opening for the void is drawn separately (S-OPENING 2CF / 2D0, X 2D1 / 2D2). So the slab runs under the band; the band
is a balustrade standing on the floor edge. No upstand, kerb height, section or separate material is printed for it
(no section cuts ST-02, Q-50). Build before deduct (ERS s.3): nothing printed replaces the floor build-up there, and no
owner rule deducts a balustrade footprint (a balustrade is a lm item, RL-06). The owner's own row (Q-56 A: living
480 x 520 less the stair box 115 x 240 = 22.20) also contains it. Result: **0.1175 floor** (R-T269-2).
Residual named: if the designer states a cast upstand under RL-06, the floor finish stops at its face (-0.1175); no
drawing shows one. One discordant line, named: the architectural GF plan draws the band's OUTER face overhead (layer 2,
4AF, with its end 4B6) and no line at its inner face; read alone, that would put the edge seen from below at the outer
face. The slab edge is a structural element and the structural sheet that dimensions the slab draws it at the inner
face (289); the architectural overhead line is the band's own outline projected (it also carries the closed end at the
top riser, which a slab edge would not). Structural sheet governs the slab edge; the Checker should look at both.

## 4. GF pantry pieces and the round-stair tread rule (GF-RC99C2A, GF-RC06FED)

- Exact intersection of the tread union of all 4 GF flights of ST-02 (engine run: F1 radial 4.0944, F2 2.030, F3 1.035,
  F4 1.035 = 8.1944 m2 = the Checker's 'drawn treads 8.1944') with the pantry part of GF-RC99C2A (west of the layer-5
  line B3 / AD: 8.955 m2) and with GF-RC06FED (2.800 m2): **0.000 m2 each**; the nearest tread lies 3.858 m east of the
  pantry line. The tread rule does not touch the pantry pieces: their only blocker is the class (pantry = wet floor,
  owner Q-37 A), which T-240 WP2 applies. Residual named: my pantry part 8.955 vs the Checker's 8.925 (+0.030, the
  north end of the box; not traced, no class effect).
- The tread rule itself (floor under a stair rising from the lowest storey; R-T269-3): F3 and F4 are drawn only as
  dashed overhead lines (layer 2; no solid stair line inside them; beyond the cut symbol 147 / 13C) and nothing closed
  (wall, window, column) is drawn under them on the GF plan: the reception floor runs under them, **2.070 m2 floor**.
  F1 (12 solid lines inside) and F2 (10 solid lines inside, and the column 2FD2's face 0.05 into its outline) are drawn
  below the cut: whether floor finish exists under them depends on the stair's structure (where its soffit leaves the
  floor, supports), which no sheet draws for ST-02 (no section, T-111 'held on a missing drawing', Q-50): **6.1244 HELD**,
  designer item proposed below. Engine note: the V2.9 record says F2 is drawn on layer 2 only (`also_drawn_on` misses
  its 10 solid lines); the classification here reads the drawing, not that field.

## 5. Rules proposed (research; a rule record needs a new rule version, lane I / Lead)

- R-T269-1 (any villa): the top riser of a flight whose plan draws fewer risers than the governing count is placed from
  its drawn first riser, the governing count and the drawn going; the undrawn strip splits into missing treads (stair)
  and the landing's nosing band (floor); a top riser beyond the printed landing edge is a design conflict (HELD), never
  absorbed by the landing.
- R-T269-2 (any villa): a band beside a flight is floor only when the structural slab edge runs along its flight-side
  face and no upstand is printed; a slab edge along its outer face puts it in the opening; otherwise HELD.
- R-T269-3 (any villa): on the lowest storey, a flight drawn only overhead with nothing closed under it leaves the floor
  under it as floor; flights drawn below the cut are HELD until a section / structural detail fixes where the soffit
  leaves the floor.

## 6. Verdict proposals and what the Checker should re-measure

- 1F living 38.6335: FLOOR (this run) vs released 44.869 ENGINE_WRONG (stair footprint not deducted: known, T-116); vs
  freelancer 38.96 UNRESOLVED (row not split; -0.84 %).
- D-13 split 0.345 / 0.0575: re-measure from ST7757 handle 459 (12th line, on the landing edge) with the frame pair
  2FE7 / 3008 -> 332 / 374, and the 1F plan lines A93 .. ABD / A92 .. ABE and DIMENSION 10DF.
- D-23 0.1175 floor: re-read ST7757 line 289 against the band AF5 / AF6 (and column 3008 for the band's start).
- GF pantry pieces: tread intersection 0.000 (F1 .. F4 vs the B3 / AD box); F3 / F4 overhead (no layer-5 line inside;
  lines 13B, 13F, 140, 141, 144 - 146 are layer 2).

## 7. Designer / owner items

No owner question (ERS 2.7 not met: the drawings settle D-13 and D-23). Designer list: D-13 can be closed (drawn on the
structural sheet); D-23 closed for the floor area (a stated upstand would reopen it); NEW item proposed for the Lead:
'ST-02 under-stair on the GF: is the space under flights F1 / F2 floor-finished, closed or solid? (6.1244 m2 HELD)'.

## 8. Lessons row (ERS s.7, proposed)

2026-10-24 | The 1F living floor stayed a 0.520 m2 range for four days on two 'designer' strips | Both were read only on
the architectural plan, where one riser line is omitted and the slab edge is not drawn | Before a plan strip goes to the
designer, read the other discipline's sheet of the same floor (the structural slab plan draws stair lines and slab
edges) and the section count; a strip is settled by drawn evidence, a convention only labels it (any villa) |
tests/t269_floor_blockers | READY (Gate A pending)
