# T-313: the opening reveal ledger (every opening, every side once; development villa; rule for every villa)

Research only: no engine, method, rule / knowledge version, registry or candidate quantity changed. Development villa,
not an accuracy claim. Drawings cited by Drive title and DXF handle only (no coordinate, image or name). Worker 2,
2026-10-28 (re-claim of the 2026-10-26 claim that left no branch). **r2 (same day, rework of the Verifier's 22:14 / 22:31
rejection):** the door reveals are NOT missing: 22 of the 27 doors are carried by FIN.PLASTER 'door jambs and head' lines
of the candidate (same owner rule UP-FIN-PLASTER-001); they are now bound and reconciled door by door (section 3a), the
candidate record is searched in EVERY item family by physical element before any component is called NO_LINE
(`FAMILY_SEARCH_T313.csv`), and the missing-scope total and the verdicts are restated (section 5).

## 1. Result (engineering terms)

| Side / component | Openings | Quantity | Evidence | Candidate line |
|---|---|---|---|---|
| Window ROOM side: jambs, head, sill (UP-REVEAL-001) | 27 of 29 | **0.000 m2: NONE** (frame drawn flush with the room face on every measured window) | DRAWING-CONFIRMED (no surface) | sill row bound to the window's ARCH.WINDOW_REVEAL line; jambs / head NO LINE |
| Window OUTSIDE: jambs | 26 | **6.6976 m2** (77.720 m.l of edge) | DRAWING-CONFIRMED | NO LINE (missing) |
| Window OUTSIDE: head soffit | 27 | **2.9694 m2** (34.630 m.l) | DRAWING-CONFIRMED | NO LINE (missing) |
| Window OUTSIDE: external sill (own item) | 23 | **2.5614 m2** (29.530 m.l) | DRAWING-CONFIRMED | the window's ARCH.WINDOW_REVEAL line |
| Window OUTSIDE: floor-level threshold strip (W15, W16, W25, W27) | 4 | **0.4080 m2** (floor edge, no arris) | DRAWING-CONFIRMED | the window's ARCH.WINDOW_REVEAL line |
| Door / gate reveal THROUGH the wall (UP-FIN-PLASTER-001): jambs | 27 doors | **19.920 m2** (119.400 m.l): D-GF-07 1.000 DC (printed 2.50), 26 doors 18.920 **ASSUMED — OWNER-APPROVED** (Q-55 C 2.20) | as stated | **22 doors: their FIN.PLASTER 'door jambs and head' line (IN_LINE)**; 5 doors NO LINE (missing) |
| Door head soffit | 27 doors | **4.230 m2** (25.000 m.l) | DRAWING-CONFIRMED (width x wall t) | the same FIN.PLASTER line (22 doors); 5 doors NO LINE |
| HELD / UNKNOWN (never 0) | | W02 outside jambs (height HELD, D-53); W03 (curved glazing, room side not in the engine rooms) and W17 (curved wall, T-302 developed hole) all components; D-GF-15 gate (width / height HELD); A-GF-01 arch (candidate jambs 0.660 + head 0.15 x 1.223795 = 0.183569 m2, outline pending D-45); A-1F-01 (not drawn) | HELD / UNKNOWN | NO LINE |

Window reveals measured: 12.6364 m2 outside (jambs + head + sill + threshold), 0.000 m2 room side; doors 24.150 m2
through the wall, of which **20.220 m2 (22 doors) already in FIN.PLASTER lines** and **3.930 m2 (5 doors) in no line**. Every one of the 59 census openings (29 windows, 27 doors, 1 gate, 2 arches; T-249 MERGED) is in the
ledger once; 234 side-component rows, each once (`REVEAL_LEDGER_T313.csv`).

## 2. Physical element and how each was measured (ERS s.2.1 - s.2.3)

- **Window depth** (plan P7757.dxf, sha `ab54dd55`, census glazing handles of T-249): frame band = the extreme offsets
  across the wall of the census glazing lines parallel to the opening; the two wall faces = the nearest lines parallel to
  it, outside the symbol, ending at a jamb within 10 mm on each side; the room side = the face whose probe point (0.30 m
  beyond it, mid-opening) lies in an engine room polygon (ARCH_ROOMS of the run; a labelled room beats an unlabelled
  space: W09 / W10 face the side passage, Q-67 A conditional exterior). Result on all 27 straight windows: wall 0.200 m
  on plan = T-150 wall thickness (27 / 27); the frame band (0.120 m on the 10-line symbols, 0.100 m on the 3-line
  symbols W01, W11 - W14, W26) is FLUSH WITH THE ROOM FACE, so the room-side reveal depth is 0.000 and the outside
  reveal depth is 0.080 m (or 0.100 m). Hand check W04 (handles 3A3 .. 3AD, wall face lines 11E / 122, sill line 3A5 on
  the outer face): frame 0.120 from the driver-room face, outer reveal 0.200 - 0.120 = 0.080 m; outer jambs 2 x 0.080 x
  0.80 = 0.128 m2, head 0.080 x 0.60 = 0.048 m2, sill 0.048 m2 (= ledger).
- **Window sizes**: T-237 OPENING_SIZES (MERGED 1cc1a153: merged heads of T-201 / T-207 / T-238); W05 height 0.800
  from T-201 (drawn, levels HELD); W11 / W12 h 2.20 (T-207 DC, sill HELD: the outside reveal does not need the sill).
- **Room-side plaster band** (owner method Q-43 / Q-48 A: T-237 owner_h 3.15 / 3.35 / 3.65, beside the drawing range
  dwg_paint_h): only decides whether a head soffit exists; with a flush frame there is no room-side reveal under EITHER
  method, so the two methods agree here (0.000 m2, no residual).
- **Doors**: one reveal through the wall thickness (owner rule UP-FIN-PLASTER-001: 2 x t x h + t x w; the frame detail
  decides how much is plastered, PROVISIONAL); t from T-150 (0.15 / 0.20, MERGED), w / h from T-237; no sill reveal.
- **Arches**: A-GF-01 head developed on its drawn arc (T-238: ARC 2422 r 0.5673 m, 28.2 .. 151.8 deg, chord 1.000 m):
  0.5673 x 2.157227 rad = 1.223795 m; kept HELD with the arch (D-45). A-1F-01 is drawn on no view: UNKNOWN.
- **Finish** (not a quantity): the owner method URBAN-REVEAL-FINISH-METHOD v1 (data/registry; default PLASTER, paint on a
  painted dry surface, porcelain only when shown, never because the room is wet) is the finish CANDIDATE; UP-REF-REVEAL-001
  is REFERENCE_ONLY in the route and the WIN-REVEAL finish decision is queued (OWNER_QUESTIONS.md), so the finish status is
  OWNER_METHOD_CANDIDATE, never DRAWING-CONFIRMED. The flush frame removes the wet-room reveal question physically (no
  room-side reveal in any WC / bath).

## 3. Line binding (V3.0.19 grain)

The candidate carries **27 ARCH.WINDOW_REVEAL m2 lines, all BLOCKED_RFI blank** ("sum of the strip faces of the opening
in the wall thickness", RFI WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED), one per engine window (W03 and W18 have none:
V2.9 misses them). Line ids are `boq_line.line_id(project, item, element, rule, version, unit)`, independent of the
method version (T-232: the 27 lines byte-identical through V3.0.10); this run read them from an engine run of the same
drawings (`BOQ_LINES.csv` sha `f5744fd4`), see section 7 for the V3.0.19 re-read. Binding: each window's sill (or
floor-level threshold) rows, room side and outside, go to its own line; jambs and head go to NO LINE; no line carries two
windows and no window two lines (27 / 27 bound). PHYSICAL MEANING of the line: the whole plan strip w x 0.20 m, of which
only the outside 0.080 (0.100) m is a finished sill surface; the 0.120 (0.100) m under the frame is the frame bed, not a
finish (finding for lane I: fill the line with the external sill / threshold surface only, 2.5614 + 0.4080 m2 on the 27
lines, never w x wall thickness). Missing for lane I (r2, after the all-family search of section 3a): window outside jambs + head
(9.6670 m2 measured), the reveals of the 5 doors without a FIN.PLASTER line (3.930 m2), W18's external sill (0.040 m2,
no line); the other 22 door reveals (20.220 m2) are already in FIN.PLASTER and must not be added again. BOQ family B4-08 'Reveals and returns' stays
NOT_IMPLEMENTED until a package integrates them.

## 3a. r2: every item family searched; door reveals bound to FIN.PLASTER and reconciled per door

The candidate record (V3.0.20 json `097a80b6`, the candidate of record since T-244 merged; and V3.0.19 json `b35475bf`,
both reproduced byte for byte on this run from the Drive copies, 3,705 lines each) was searched line by line in EVERY item
family for each of the 59 census openings: by floor + the engine opening id (T-249 ENGINE_REF: `OP-nnn` / `COP-001`) in
the line's room / element id, by the engine door ref (`DOOR-<floor>-<hash>`), and, for opening strip lines that carry no
opening id (door closures, unattributed strips), by the census symbol handles among the line's source entities. Every
hit is listed with its physical role in `FAMILY_SEARCH_T313.csv`: ARCH.WINDOW_REVEAL 27 (BOUND: window sill / threshold
rows), FIN.PLASTER 'door jambs and head' 22 (BOUND: door jambs + head), and OTHER ELEMENTS that are not a reveal
surface: ARCH.WINDOW 27 / door sets DOOR.* 17 / ARCH.PASSAGE 2 (counts, nr), floor finish through the doorway
FIN.FLOOR.PORCELAIN 13, FIN.MARBLE.THRESHOLD 10 and ARCH.THRESHOLD 8 (floor-level strips across door / arch openings:
D-GF-01 / -03 / -06 / -07 / -09, D-2F-01 BOUNDED, A-GF-01 BLOCKED, and the closure strip of the no-line door D-GF-14
tied by its symbol handle; a door or an arch has no sill reveal, so none carries a component of this ledger), and the
waterproofing lines FIN.WP.DOORWAY / _TRANSITION / _TRANSITION_NR / TERMINATION 32 (WP family). NO threshold, marble or
porcelain strip line sits on the four floor-level windows W15 / W16 / W25 / W27 (1F OP-016 / OP-017 / OP-012, 2F OP-003):
their threshold rows (0.408 m2) stay bound to their own ARCH.WINDOW_REVEAL line, no second line. Checked beyond the
openings: the room wall-face FIN.PLASTER / FIN.PAINT lines only DEDUCT each opening by its own area (Q-73; W17's head
soffit through the curved wall HELD inside 1F_11) and add no reveal; the facade run (ARCH.FACADE_RUN, Q-64 B) states
that no return face is measured by a reveal line; the 5 FIN.CEILING 'soffit over outside air' lines are slab soffits
(PL-01 .. PL-05, 2.417 .. 19.181 m2 each, against outside window head soffits of 0.040 .. 0.5064 m2), not window heads. So no line of any family carries a window outside jamb or head. Line ids are the
record's `line_id` (a hash of project / item / element / rule / unit, version-independent): the ledger, the binding and
the family search are byte-identical on V3.0.19 and V3.0.20; the 22 FIN.PLASTER door ids and quantities also equal the
merged extract research/agents_t311/CANDIDATE_V3019_T311.json (22 / 22); the 27 window ids = the Checker's own V3.0.19
read (22:31, 27 / 27).

Door crosswalk (T-249 ENGINE_REF): GF D-GF-01 OP-009, -03 OP-005, -04 OP-026, -05 OP-025, -06 OP-008, -07 OP-021,
-08 OP-010, -09 OP-013, -11 OP-017, -12 OP-018, -13 OP-012; 1F D-1F-01 OP-004, -02 OP-020, -05 OP-008, -06 OP-010,
-07 OP-019, -08 OP-005, -09 OP-006, -10 OP-018; 2F D-2F-01 OP-001, -02 OP-007, -03 OP-006 (22). Per door
(`DOOR_PLASTER_RECONCILIATION_T313.csv`; the line's own inputs t / w / h against the ledger's T-150 / T-237 values):

| Result | Doors | Ledger m2 | Line m2 | Residual |
|---|---|---|---|---|
| EQUAL (same t, w, h = 2.20 Q-55 C) | 20 | 17.740 | 17.740 PROVISIONAL | **0.000** on every door |
| WITHIN_BOUND D-GF-01 (OP-009, 0.20 x 1.00) | 1 | 1.080 (h 2.20 ASSUMED — OWNER-APPROVED Q-55 C) | 1.08 .. 1.20 BOUNDED (main-entrance class pending 2.20 / 2.50, UP-DOOR-HGT-001) | 0.000 to the low end, -0.120 to the high end |
| WITHIN_BOUND D-GF-07 (OP-021, 0.20 x 2.00) | 1 | 1.400 (h 2.50 PRINTED, DRAWING-CONFIRMED, T-201 / T-237) | 1.28 .. 1.40 BOUNDED (same class pending) | +0.120 to the low end, 0.000 to the high end |
| NO LINE in any family (only WP transition lines name them) | 5: D-GF-02 0.78, D-GF-10 0.78, D-GF-14 0.78, D-1F-03 0.81, D-1F-04 0.78 | **3.930** (jambs 3.300 ASSUMED Q-55 C + head 0.630) | none | missing scope |
| UNRESOLVED | gate D-GF-15 | blank | none | width / height HELD |

Arches: A-GF-01 (OP-027) carries ARCH.PASSAGE, an ARCH.THRESHOLD strip and a WP termination, A-1F-01 (OP-011)
ARCH.PASSAGE and a porcelain doorway strip: none is a jamb or head surface; both arch reveals stay HELD / UNKNOWN.
Refusal now in code: `book_missing` refuses booking a component as missing when another family's line carries it
(the r1 error), and `bind_lines` refuses one opening in two lines (a plaster line plus a reveal line).

## 4. Reconciliation of the exterior reveal EDGE (acceptance 2)

The register's **189.630 m.l is the superseded r1 figure** of T-162: r2 (MERGED 4cc2847) corrected it to **137.110 m.l
measured + 32.200 ASSUMED** because r1 added 2 x height per opening a second time (-52.520 m.l). This ledger against r2's
own 36 facade openings (`EDGE_RECONCILIATION_T313.csv`):

| Term | m.l |
|---|---|
| T-162 r2 measured (36 facade openings, its known parts) | 137.110 |
| of which the 26 windows this ledger now measures whole (head + sill only for 19 of them in r2) | 85.420 |
| of which still open here: W02 12.660, W03 21.740, W17 10.290 (curved / height HELD), D-GF-07 7.000 (door, printed) | 51.690 |
| T-313 edge of the same 26 windows | **129.220** |
| = 85.420 + jambs newly DRAWING-CONFIRMED since r2 (T-201 / T-207 heights, 2 h on 19 windows) | +45.800 |
| - floor-level W25 / W27: no sill arris (r2 counted one) | -2.000 |
| Residual | **0.000** |

W18 (5.320 m.l, not on the engine outline) is among the 26. The door arrises at the outer face (32.200 ASSUMED + 7.000)
stay in the corners line; a door reveal is one surface through the wall here. The register rows 68 / 515 / 551 should
cite 137.110 (r2) and the T-313 129.220 for the 26 windows, not 189.630 (Lead).

## 5. Engine vs freelancer, verdict proposals (restated in r2)

- **Missing scope (no line in any family): 13.637 m2**, was 36.7834 m2 as printed in r1 (its own parts 12.6364 +
  24.150 sum to 36.7864: a 0.003 m2 addition slip in r1's text, corrected here); 36.7864 - 13.637 = 23.1494 m2: the 22
  doors' 20.220 m2 are IN_LINE in FIN.PLASTER, and r1 had also counted the 2.5214 m2 external sills + 0.408 m2
  thresholds that its own binding put in the ARCH.WINDOW_REVEAL lines. It is: window outside jambs 6.6976 + heads 2.9694 = **9.6670 m2**
  (26 / 27 windows, DRAWING-CONFIRMED), W18 external sill **0.040 m2** (W18 has no reveal line), the 5 doors above
  **3.930 m2** (3.300 of it ASSUMED — OWNER-APPROVED Q-55 C). **ENGINE_WRONG (missing scope)** for these only.
- **Doors in FIN.PLASTER: ENGINE_RIGHT** on 20 doors (residual 0.000 each, same owner rule and inputs); D-GF-01 and
  D-GF-07 are inside the line's bound. For D-GF-07 the drawing PRINTS 2.50 m (DRAWING-CONFIRMED, T-201 / T-237), so the
  line's low end 1.28 m2 (h 2.20) is excluded by the drawing: proposal for lane I, narrow that line to 1.400 m2
  (ENGINE_WRONG range width only, 0.120 m2). D-GF-01: no printed height; the class stays pending (UNRESOLVED), the line's
  bound 1.08 .. 1.20 stands.
- The 27 ARCH.WINDOW_REVEAL strip lines: their w x wall t basis includes the frame bed (ENGINE_WRONG as a finish
  quantity); fill them with the external sill / threshold surface, 2.5214 + 0.4080 m2 (unchanged from r1, confirmed by
  the Checker).
- Room-side window reveal: NOT_APPLICABLE with evidence (frame flush), never a default depth.
- Freelancer: no reveal surface row in his workbooks (merged T-128 / T-162 records: his plaster sheet deducts openings,
  his corner m.l is one lumped Sigma line); this run did not re-open his workbooks: **RULE_DIFFERENCE (scope)**,
  UNRESOLVED per cell.

## 6. Rule, test, lessons (ERS s.4, s.7)

- **R-T313-REVEAL-1** (research rule, every villa; a rule version only when adopted): a reveal is measured per opening
  and per SIDE from the drawn frame position: depth = wall face to frame line on the plan (a flush frame = depth 0 with
  that evidence, no surface), never a typical depth; window: room side (jambs in the plaster band, head only with wall
  above, internal sill own item) and outside (jambs, head, external sill own item; floor-level: threshold, no arris);
  door: ONE reveal through the wall (no sill); arch: head on its developed arc; the outside EDGE goes to the corners m.l
  line, the SURFACE never to a facade face; a strip line of w x wall thickness is not a finish quantity.
- Code `research/agents_t313/t313_reveal_ledger.py` (generic) and `t313_alsenan.py` (development-villa run).
- Tests `tests/t313_reveal_ledger` (28): villa R313 hand fixture (W1 1.20 x 1.50 in a 0.20 wall, frame 0.05 .. 0.12
  off the outer face: IN 0.240 / 0.096 / 0.096, OUT 0.150 / 0.060 / 0.060 m2, edge 5.40 m.l; D1 0.880 + 0.180; A1 head
  0.244759 m2), normal (band clip, floor glazing, flush frame, sill / height unknown, mirror and mm units, binding,
  totals) and adverse (default depth, missing depth as 0, door sill reveal, reveal in the facade face, one opening in two
  lines, two openings in one line, binding to a non-row, duplicate opening, unknown unit / negative length, arch at the
  chord, residual not named); Alsenan pins on the committed ledger (census once, 27 lines one window each, HELD never 0,
  depths close to the wall, edge reconciliation closes).
- r2 tests (+7, 35 in all): fixture door bound to its plaster line and reconciled 1.060 / 0.000, a second door 0.780 m2 missing;
  a bounded line WITHIN_BOUND with both residuals named and DIFFERS against a point value; ADVERSE: a door reveal already
  carried in a plaster jamb line booked again as missing refused, the same door bound to a plaster AND a reveal line
  refused, a HELD component never reconciled as 0; development-villa pins: 27 window + 22 door lines each one opening,
  every door's line EQUAL or WITHIN_BOUND, no missing-scope row carried by another family, the four floor-level
  windows' thresholds in their own reveal line only, every search hit named BOUND or OTHER ELEMENT.
- Lessons row r2 (proposed, Verifier's wording kept): 2026-10-28 | The door reveals were booked missing although
  FIN.PLASTER carried them | the search covered only the family the task named (ARCH.WINDOW_REVEAL) | Before booking a
  component NO_LINE, search every item family of the candidate of record by physical element (code: `family_search` +
  `book_missing` refuses a second count) | tests/t313_reveal_ledger | PROPOSED.
- Lessons row (proposed): 2026-10-28 | A reveal family sat blank because the engine's only reveal line is the plan strip
  w x wall thickness, and a register figure (189.630 m.l) survived its own correction (137.110, T-162 r2) | The strip was
  taken as the reveal and the frame position was never read; a superseded revision was cited | Measure each reveal per
  side from the drawn frame position (flush = 0 with evidence); cite a figure with its ledger revision (every villa) |
  tests/t313_reveal_ledger | PROPOSED.

## 7. Run identity, missing / held

r2: P7757.dxf `ab54dd55` and 'ST7757 dxf.dxf' `9f9d1179` (Drive "Alsenan chalet project"); own run t167 v304_run ->
t255 v3019_run (V3_0_19_BOQ_LINES json `b35475bf` / csv `ef63b73b` = the record) -> t244 v3020_direct (V3_0_20 json
`097a80b6` = the Checker's T-244 reproduction); ARCH_ROOMS of the V3.0.19 run `06ac74eb`; Python 3.11.18. (r1 read an
engine run `0b48da21` / `f5744fd4`; the ledger rows are unchanged by r2, only the binding and the search.)
Not done here: curved W03 / W17 developed reveals (T-302 method), W02 height (D-53), gate D-GF-15, A-1F-01; the door
outer arrises stay with T-162; passages P-GF-01 / P-GF-05 / P-1F-01 (not in the T-249 census; T-207 head terms
0.180 / 0.240 / 0.195 m2) and lift openings are outside this census.
