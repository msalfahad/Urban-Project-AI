# T-325: sills and thresholds as their own item (every opening once; development villa; rule for every villa)

Research only: no engine, method, rule / knowledge version, registry or candidate quantity changed. Development villa,
not an accuracy claim. Drawings cited by Drive title and DXF handle only. Worker 2, 2026-10-29.

Run identity: P7757.dxf `ab54dd55` (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip), 'ST7757 dxf.dxf'
`9f9d1179`; own run t167 v304_run -> t244 v3020_run: V3_0_20_BOQ_LINES.json `097a80b6` (= the candidate of record, the
Checker's T-244 reproduction), 3,705 lines; ARCH_ROOMS `06ac74eb`, ARCH_FLOOR_AREAS `7ee4f297`; Python 3.11.18.
Command: `python3 -I research/agents_t325/t325_alsenan.py <P7757.dxf> <V3_0_20_BOQ_LINES.json> --floor-areas ...
--rooms ... --out research/agents_t325`.

## 1. Result (engineering terms)

| Component (physical element) | Openings | Quantity | Material (source) | Evidence | Candidate line |
|---|---|---|---|---|---|
| Window ROOM-side sill surface | 23 raised windows | **0.000: NONE** (frame flush with the room face on every measured window, T-313) | - | DRAWING-CONFIRMED (no surface) | none needed |
| Window EXTERNAL sill surface (frame to outer face) | 23 | **2.5614 m2**, front edge **29.530 m.l**, 23 pcs | **UNKNOWN**: no printed specification, no owner rule (no finish schedule exists) | DRAWING-CONFIRMED geometry | 22 in their own ARCH.WINDOW_REVEAL line (BLOCKED blank); **W18 0.040 m2 NO LINE** |
| Floor-level window, room side (W15, W16, W25, W27) | 4 | **0.000: NONE** (flush frame) | the room floor (UP-REVEAL-001) | DRAWING-CONFIRMED | room floor line |
| Floor-level window, outside, onto a floor: W15 / W16 -> TERRACE-550 (printed +5.50 = 1F F.F.L. +5.50) | 2 | **0.248 m2** (2 x 1.55 x 0.08), 3.100 m.l | the terrace finish (itself HELD in T-321: no paving type printed) | DRAWING-CONFIRMED geometry | own ARCH.WINDOW_REVEAL line; NOT inside the terrace's 31.643 / 32.721 m2 (outline to the wall faces) |
| Floor-level window, outside over air: W25 (1F stair), W27 (2F stair) | 2 | **0.160 m2** (2 x 1.00 x 0.08), 2.000 m.l: an external sill AT FLOOR LEVEL, not a walking threshold | **UNKNOWN** | DRAWING-CONFIRMED geometry | own ARCH.WINDOW_REVEAL line |
| Door threshold, wet doorway (UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1) | 14 | **1.820 m2**, 14 pcs, width 11.500 m.l; rise 0.020 m VERTICAL (never a plan depth) | **MARBLE** (owner rule, OWNER_APPROVED) | DRAWING-CONFIRMED (w T-237, t T-150) | 10 FIN.MARBLE.THRESHOLD lines EQUAL (1.340 m2, residual 0.000 each); **4 doors D-GF-02, D-GF-10, D-GF-14, D-1F-04 = 0.480 m2 sit in BLOCKED ARCH.THRESHOLD closure lines** (see s.3) |
| Door threshold, dry doorway | 7 | **1.100 m2** | floor porcelain continued, once (UP-THR-001) | DRAWING-CONFIRMED | 6 FIN.FLOOR.PORCELAIN strips EQUAL (0.950); D-1F-03 0.150 in a BLOCKED closure line |
| Door threshold, external entrance (D-GF-01, -03, -06, -07, -09, D-2F-01) | 6 | **1.310 m2** (6.800 m.l) | **HELD**: an exterior sill is by specification (none printed); the marble rule lists external entrances as not applicable | DRAWING-CONFIRMED geometry (Checker 01:12 widths, T-240) | 6 ARCH.THRESHOLD BOUNDED lines, each WITHIN_BOUND (point range = ledger, residual 0.000) |
| Arch / doorless opening (A-GF-01, A-1F-01): floor continues | 2 | 0.300 m2 | floor finish continued | as the line | A-GF-01 BLOCKED ARCH.THRESHOLD, A-1F-01 porcelain strip EQUAL |
| Finish-change edge (tile cut line at a material change) | 29 | 29.800 m.l (marble 2 edges x 11.50, external 1 x 6.80) | NOT AN ITEM (no rule, no specification makes a transition profile an item) | geometry | none (by design) |
| UNRESOLVED (never 0) | | gate D-GF-15 (width / wall HELD); W03 curved floor glazing both sides; W17 room side (curved, T-302) | | UNKNOWN | |

Every one of the 59 census openings (T-249) is in the ledger, 118 component rows, each once
(`SILL_THRESHOLD_LEDGER_T325.csv`); 52 bound to one line each, no line carries two openings, no component sits in
two lines; 5 components NO LINE: W18 external sill 0.040 m2 (missing) and the 4 UNRESOLVED rows above.

## 2. Physical elements and how each was established (ERS s.2.1 - s.2.3)

- **What is built at a window sill**: the frame sits flush with the room face on all 27 straight windows (T-313,
  plan wall faces vs census glazing lines), so there is no internal sill board / stone surface; outside, the strip from
  the frame to the outer face (0.080 m on the 10-line symbols, 0.100 m on the 3-line symbols) is the external sill
  surface. Its MATERIAL is not printed anywhere: the decoded plan texts (276 records, `engine/source/cad/shx_arabic`)
  carry room names, levels and titles only; no finish schedule exists ('the supplied files are all the files'); no
  answered owner question names a window sill finish. So the quantity is DRAWING-CONFIRMED and the material UNKNOWN,
  never a default stone and never 'marble because thresholds are marble' (refused in code).
- **What lies beyond a floor-level window** (new here): each window's far side is probed 0.30 m beyond its outer face
  (T-313 method: the room side = the probe in an engine room polygon) against the roof / terrace outlines that T-321
  traced from named entities (handles in `research/agents_t321/t321_measure.py`). W15 / W16 (1F living, NW) open onto
  TERRACE-550, whose printed level +5.50 equals the 1F F.F.L. +5.50 (P7757 level marks: +1.00 GF, +5.50 1F, +9.70 2F; storey chain GF 4.50 / 1F 4.20, merged research): their
  0.08 m outside strip is the terrace floor continued to the frame, outside the terrace outline (which stops at the
  wall face), so it is not double counted. W25 / W27 (stair, SW) stand over outside air (W25: no zone within 10.5 m; W27: outside
  ROOF-1390, its own block, and not in ROOF-970): their strip is an external sill at floor level.
- **Door thresholds**: one strip through the wall, clear width x wall thickness (UP-THR-001; width T-237, thickness
  T-150, both merged); wet when a side is a WC / bath / wash / basin / kitchen / laundry space (the candidate's own
  marble line where it exists, else the T-237 room names; Q-06: a basin space is wet). External doors: the T-240
  TO_THRESHOLD records (merged, Checker 01:12 widths) moved their strip out of porcelain into ARCH.THRESHOLD as
  EXTERIOR_SILL; the marble rule does not cover them, so the material is HELD with the area kept.
- **No double count with the floor-tile lines**: every strip polygon of ARCH_FLOOR_AREAS with an opening or threshold class (138) against
  every room floor polygon of its storey: largest overlap 0.000394 m2 (a numeric edge sliver; the strips are in no room
  floor by construction, owner_finish_scope). `STRIP_FLOOR_OVERLAP_T325.csv`.

## 3. Correction to T-313 (merged): the five "no-line" doors DO have a threshold line

T-313 listed D-GF-02, D-GF-10, D-GF-14, D-1F-03, D-1F-04 as carried by no line except WP transitions (true for their
REVEAL, which this does not change). For the THRESHOLD, the candidate carries a BLOCKED ARCH.THRESHOLD 'threshold strip
CLOSURE|D2:<n>' line for each: the decimal handle n is the door symbol's handle (495 = 1EF D-GF-02, 825 = 339 D-GF-10,
820 = 334 D-GF-14, 3118 = C2E D-1F-04, 3122 = C32 D-1F-03; T-249 HANDLES). T-313 had tied only D-GF-14. Bound here by
that handle (`census_by` column). Their own strip polygons are not geometry-verified and are larger than clear width x
wall t by 0.012 .. 0.099 m2 (D-GF-02 0.1535 vs 0.120; D-GF-10 0.1575 vs 0.120; D-GF-14 0.2188 vs 0.120; D-1F-03
0.1858 vs 0.150; D-1F-04 0.1320 vs 0.120): the closure polygon spans the wall gap the door symbol closes, which is wider
than the clear opening (jamb nibs / frame); cause per door NOT traced in this run (UNRESOLVED residual, named). The
owner rule measures the FULL CLEAR DOOR WIDTH x the physical depth, so the ledger value stands as the fill proposal.

Other threshold-family lines that are not census openings (`LINES_T325.csv`, census NOT_IN_CENSUS): 3 lift landing
sills ARCH.THRESHOLD BOUNDED (GF OP-011, 1F OP-007, 2F OP-002; 'the landing sill comes with the lift', T-240), the GF
OP-001 / OP-003 NOT_APPLICABLE pair (no opening, T-240 NO_FLOOR / NO_OPENING_SPLIT), the GF OP-020 passage under wet
review (BLOCKED), and 5 BLOCKED WALL_BAND_REMAINDER / STRIP_NOT_ATTRIBUTED strips (wall bodies, not thresholds).

## 4. Engine vs freelancer (cells, committed FREELANCER_RAW_ROWS.json, 885 rows)

- Wet-door marble thresholds: engine 14 pcs / 1.820 m2 (10 lines carry 1.340, 4 blocked lines 0.480) vs freelancer
  **no row** (0 of 885 rows names a threshold / sill term; marble appears only in his stair sheet). Verdict proposal:
  **ENGINE_RIGHT by owner rule** (UP-THR-001 / URBAN-WET-SERVICE-MARBLE-THRESHOLD: every wet doorway), freelancer
  omission; -100 % on his side.
- Window sills: engine 2.5614 + 0.160 m2 (UNKNOWN material) vs freelancer no row: NOT COMPARED (no counterpart; his
  aluminium sheet counts window areas only).
- His 'door steps' block (FIN 'marble + court' rows 36 - 41: 1.3, 2.5, 1.0, 1.0, 0.9, 1.0 = **7.70**, column C
  'length', copied into column H 'areas' by =C x B and summed into his stair marble 295.44 m2): six external step pieces
  booked by LENGTH in an AREA column, a unit mix (7.70 m.l counted as 7.70 m2). It is the outside entrance steps
  (marble, owner outdoor rule), not the door threshold strip; engine external-door strips 6 doors / 6.800 m.l / 1.310
  m2. **RULE_DIFFERENCE (element)**, not like-for-like; the unit mix is a freelancer finding for the stair trade.

## 5. Rules, tests, lessons (ERS s.4, s.7)

- **R-T325-1** (research rule, every villa; a rule version only when adopted): a sill / threshold is its own item per
  opening and per side, measured from the drawn frame position; window sills in m2 + front edge m.l + pcs, material
  only from a printed specification or an owner rule (else UNKNOWN with the quantity kept); a floor-level window's
  outside strip is the adjoining floor when a floor at the same printed level lies beyond, an external sill at floor
  level over air; door thresholds by UP-THR-001 (wet marble, dry porcelain once, external by specification); the
  finish-change edge is geometry, never a line.
- Code: `research/agents_t325/sills_thresholds.py` (generic), `t325_alsenan.py` (development-villa run).
- Tests `tests/t325_sills_thresholds` (21): non-Alsenan villa R325 hand fixture (bath door 0.80 x 0.15 marble 0.120
  m2 + 1.600 m.l edges; dry door 0.180; arch 0.200; raised window sills 0.060 / 0.096; floor-level window over air
  0.120 UNKNOWN; onto a terrace 0.100), spec sets a material only where printed, mirror and mm units; ADVERSE: default
  sill depth refused, the 20 mm rise as a plan depth refused, missing depth UNRESOLVED never 0, outside not
  established HELD, threshold in a reveal line AND a threshold line refused, one component in two lines / two openings
  in one line refused, a room-floor strip or an edge bound to a line refused, door sill / duplicate opening / bad unit
  / negative length / unnamed residual refused, external entrance never marble by the wet rule; development-villa pins
  on the committed ledger (59 openings once, one line one opening, floor-level window thresholds only in their reveal
  line, HELD never 0, no DIFFERS, strips in no room floor, totals).
- Lessons row (proposed): 2026-10-29 | Five doors were booked 'no line' in the merged reveal ledger although the
  candidate carries a BLOCKED threshold-strip line for each, named by a decimal door-symbol handle (CLOSURE|D2:495 =
  handle 1EF) | The family search matched openings by engine opening id only; a closure strip carries no opening id,
  only the door symbol handle in another number base | Bind a strip line to its opening by EVERY identity it carries
  (opening id, census handle, closure handle after base conversion) before calling an opening unlined (every villa) |
  tests/t325_sills_thresholds (pins: every census opening once; one line one opening) | PROPOSED.

## 6. For lane I (fill proposals, nothing moved here)

- 10 FIN.MARBLE.THRESHOLD and 6 FIN.FLOOR.PORCELAIN strips: ENGINE_RIGHT (EQUAL, residual 0.000).
- 4 BLOCKED closure lines -> MARBLE thresholds 0.120 m2 each (D-GF-02, D-GF-10, D-GF-14, D-1F-04) and 1 -> porcelain
  strip 0.150 (D-1F-03), clear width x wall t; the item code is ARCH.THRESHOLD today (finish to be confirmed), the
  owner rule sets marble / porcelain: an integration retypes them, never adds a second line.
- 22 ARCH.WINDOW_REVEAL lines: fill with the external sill 2.5214 m2 (raised windows, 22) / floor-level outside strips
  0.408 m2 (4) as T-313 proposed, MATERIAL UNKNOWN; W18 external sill 0.040 m2 needs a line (missing scope).
- 6 external-door ARCH.THRESHOLD BOUNDED lines: area confirmed, material HELD (by specification).
- Missing / held: gate D-GF-15; W03; W17 room side; the five closure-polygon residuals (cause not traced).
