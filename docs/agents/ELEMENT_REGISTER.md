# Shared project element register: design v0 (Lead, 2026-10-20 20:10)

Owner management decision 2026-10-20 §4: one stable register that links every drawn element to its drawing evidence and
to the BOQ lines derived from it. Built incrementally from outputs that already exist; no working module is rewritten.
This file is the Lead's design. The code is plan item P-09 (week 2, lane I with the Lead), after the V3.0 skeleton.

## Element id

`<project>/<rev>/<floor>/<kind>/<local>`; stable across reruns of the same revision.

| Part | Values | Source today |
|---|---|---|
| project | short project key (never a client name) | run config |
| rev | drawing revision id = sha256 prefix of the source file (SOURCE_MANIFEST) | revision_set_sha256 in tools/urban_boq_m9.py |
| floor | FDN, GF, 1F, 2F, ROOF-1F, ROOF-2F, ANNEX | storey detection / room levels (finish height V2) |
| kind | ROOM, WALL, OPEN (door / window / passage), COL, BEAM, FTG, GB (ground beam), STRAP, SLAB, STAIR-FLIGHT, LANDING, ROOF, EXT (porch, passage, court), ZONE-FIN (finish zone), ZONE-WP (waterproofing zone) | room faces, wall runs, opening records, route G members, T-110 beam register, T-111 flight ledger, membrane zones |
| local | the drawing's own label when printed (B23, F10, CB10, D-03), else a geometry hash of the outline rounded to 1 mm | label census / member detection |

A label printed twice (two B7 spans) gets a span suffix `B7.1`, `B7.2` ordered by grid; a geometry-hash id survives a
rerun on the same revision only; a new revision maps old to new ids by label first, then by outline overlap >= 95 %.

## Record (one per element)

id, kind, floor, label, outline or axis (mm, project coordinates), drawing evidence (sheet, layer, entity handle or
printed text), status in the seven statuses (VERIFIED / CALCULATED / PROVISIONAL / ASSUMED / HELD / CONFLICT /
NOT APPLICABLE), conflict record or designer request id (DESIGNER_CLARIFICATIONS.md), and `boq_lines`: every BOQ line
key that takes a quantity from it, with the quantity and unit taken. Cross-trade check: the same element area may feed
one finish line per surface (for example a landing: marble OR porcelain, never both) and one concrete line.

## Build order (no rewrites)

1. V3.0 lines carry `element_ids` (T-131 extension): rooms, wall runs, openings, membrane zones first (they already have
   outlines).
2. Structural: T-110 beam register ids, T-119 column ids, T-111 flights / landings, footings and straps from route G.
3. External areas: porch, passage, pool court, roof edges (T-127 places).
4. Revision mapping test on a synthetic villa with one changed wall.

Acceptance for v0 (P-09): every V3.0 line has at least one element id and a drawing reference; no element feeds two
finish lines for the same surface; held elements stay HELD in every line they feed.

## Register state and Lead rulings (owner workflow controls 2026-10-21 §2; newest first)

Code: element_register_v0 is READY (T-134, 7053291, not merged). On the development villa V3.0 run: 652 elements,
1,504 of 1,530 lines linked, 26 UNLINKED with a reason; 0 double finishes, 0 double concrete, 0 held-released. The
checker verifies it before any ruling below becomes a code check. Evidence status per WORKFLOW_CONTROLS §5; a ruling
names the OWNER TRADE (the one trade whose line takes the quantity); every other trade lists the element without a
quantity.

### Lead 2026-10-23 04:20 (from T-179 r2, T-190, T-192, T-198 MERGED; T-191, T-196 REJECTED; T-187, T-197 READY)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Candidate line STAIRS:1F:SITE 4.451 m3 (T-196 SITE-b845 'winder approximation'; T-187: 18 lines from one point to r 2.211 m over 360 deg = a DOME outline on the 1F roof, not a stair) | concrete (stairs), concrete (domes), formwork | DOMES (the dome element of T-185 at that centre); the stair trade takes NOTHING from it; the line is HELD MISREAD in V3.0.6 and is RETIRED (not re-labelled) when the verified dome shells replace the dome conventions | HELD MISREAD (T-187 READY, Gate B to confirm) | T-187 handoff; T-185 dome detail ST p.7 | T-193 acceptance: name which dome (DOME-A / DOME-B / tower) the centre is, show the 4.451 is not ALSO counted inside the 7.372 dome convention lines or the 5.081 verified shells (one element, one line) |
| Column elements of register-v0 on V3.0.5 (about 3 COL elements per physical column: GF C2 12 elements vs 4 drawn; C4 6 vs 2; C3 18 vs 6) | concrete, formwork, rebar, scope crosswalk | COLUMNS: ONE element per physical column per storey, with its engine pieces as components (as POOL-01 base / walls); never merged across storeys | CONFLICT in the register tool (checker T-196 verdict 02:08, own count from ST7757 dxf.dxf, C2 marks x 170 .. 180) | T-196 REJECTED | T-196 r2 finds the cause and collapses; until then no register count of columns (834 elements, HAS_LINE 820) is quoted anywhere |
| ST-01 1F -> 2F flights MS2-L / MS2-U and the landing MS2-LD (D-T184-1: the candidate folded them away, -2.598 m3 in rev1) | concrete (stairs), beams B20 / B23, formwork | STAIRS for the flight solid outside the beam bands; B20 / B23 own the band (R-CONC-OWN-1 / -1a, T-189 / T-192 MERGED) | MS2-L 1.0334 VERIFIED; MS2-U 1.0014 DRAWING-CONFIRMED; MS2-LD HELD 0.4696 .. 0.4800 | T-192 MERGED 86fd5f42; T-187 READY | Gate B on T-187; stair formwork 43.777 m2 (T-192) uses the same boundaries before T-199 |
| Openings P-GF-01 / P-1F-01 / P-GF-05 and W01 / W03 datum (census r3) | openings, block deductions, lintels, reveals, plaster | OPENINGS list (ruling 00:20 stands); the census r3 list is now the one list every deducting trade reads | MERGED 57bb0411 (checker W01 1.00 / 3.00, W03 0.00 / 4.30 above FFL, own DXF) | T-198 | heads of the three openings and of the 21 headless windows HELD -> T-201 |
| Pool base mats (R1 / R2, '/m' mesh) | rebar | REBAR (pool); count A (density) .. B (max spacing + 1) as on every '/m' mesh except where an element's own evidence fixes the meaning (footings, T-171) | HELD (D-57) | checker T-191 verdict 03:58 | T-191 r2 |

### Lead 2026-10-23 00:20 (from T-181, T-194, T-163 r3, T-195 MERGED; T-179 r1 REJECTED, r2 READY)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Dome-opening band of the slab at each terrace dome (0.16 m slab-edge band, 4.446 m2 of edge form; 1.689 m2 at DOME-A) | formwork, concrete, slab edges | the DOME RING owns the face (formwork and concrete); the slab-edge chain stops at the ring (slab edges 31.058 -> 26.612 m2) | T-163 r3 MERGED 659f889f (checker narrow re-check) | ST p.7 dome detail, T-185 ring | integration with formwork lines: T-199 |
| Dome shell soffit form (S0, 2 terrace domes, 2 x 24.150 m2 intrados above the ring-top plane) | formwork, ceilings, waterproofing | FORMWORK (structure); the ring below the springing plane is its own HELD line, never added to the shell | T-163 r3 MERGED; checker own p.7 printed 442 / 190 / 10: 24.1495 m2 (0.00 %) | ST p.7 | S1 client scenario shown beside, never in totals (ScenarioLeak guard) |
| Opening P-GF-05 (1.20 m, GF SW) and P-GF-01 (0.90), P-1F-01 (1.30) | openings, block deductions, lintels, reveals, plaster / paint | OPENINGS (the list); every deducting trade reads the opening from the list, never re-derives it | DRAWN (SW elevation / plans); head of P-GF-05 HELD (D-60) | T-194 MERGED 4f2678c5 | T-198 census r3 with the downstream deltas; T-176 waits on it |
| Window count (29 in the freelancer and the T-150 list) | openings, scoreboard | OPENINGS; the count is HELD while W02 is unclassified (D-53), never shown as AGREE | HELD (checker T-181 verdict faa04202) | T-181 MERGED | T-198 states the reason on the list |
| Curved openings (W17 and every arc opening) | openings, block, facade, plaster | OPENINGS; each line names its width basis: outer arc, face arc or projected chord (W17: 3.2895 / 2.977 / 2.6917 m); an elevation dimension is a chord | DRAWING-CONFIRMED (checker 0 mm on W17 NW 2691.5) | T-194; proposed UP-OPEN-CONSIST-001 | T-197 checks every curved element family |
| Every drawing sheet (31: ARCH 12, ST 16, SAN 3) | every trade | DOCUMENT REGISTER (T-195): a quantity cites set + page; no printed revision -> FILE_PIN by sha256 | T-195 MERGED 06c2b045 | proposed UP-DOCREG-001 | D-61 (two dates in ST), D-62 (sheets not issued); scope cross-check T-196 |

### Lead 2026-10-22 20:20 (from T-189, T-178, T-185, T-175, T-173, T-128 r3, T-186, T-182 MERGED; T-179 and T-164 READY)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Stair flight inside beams B20 (GF roof, 0.40 x 0.75) and B23 (1F roof, 0.45 x 0.75) over ST-01 | stair concrete, beam concrete, formwork, ceiling | BEAMS own the 3-D intersection (they are billed through the junction at full section: released P-C:BEAMS:GF:BAND0043.2 0.990 m3, P-C:BEAMS:1F:BAND0031.2 1.11375 m3, Checker 0.0 %); the stair is measured net from the beam face (MS1-U 0.9976, MS2-U 1.0014 m3); rule R-CONC-OWN-1 (owner of the line billed through at full section; else the element that would lose it keeps it; undefined = HELD) | T-189 MERGED 3369f30e; staircase system 6.675 m3 of which MS1-L 0.863 HELD (C-ST-4): PARTIALLY VERIFIED | ST7757 dxf GF / 1F roof slab sheets, schedule p.10, section A-A | the route G stair line CC-7390ea1139 also runs into B20 (about 0.065 m3), flight feet and landings vs slabs: T-192; candidate: T-187 uses ledger rev2 |
| Every intersection of two structural solids (beam / slab, column / beam, neck / footing, pool wall / base, stair / slab) | concrete, formwork | ONE owner per intersection by R-CONC-OWN-1; sum of owned = union is the register's double-count test for concrete (module engine/source/concrete_overlap_ownership.py, unwired) | T-189 MERGED (35 tests) | owner 18:00 | wiring as a candidate check: after T-187 (lane I) |
| Terrace domes (2) S0 shells 2 x 2.5407 = 5.081 m3; tower dome; dome rings / drums | concrete, rebar, formwork, waterproofing, roof finish | STRUCTURE (S0 approved design); the client change S1 is a scenario never released; tower dome, rings and drums HELD (no structural detail) | T-185 MERGED 94e39ee6; Checker VERIFIED the 2 shells; line PARTIALLY VERIFIED | ST p.7 printed 442 / 190 / 10; Q-29 (owner 11:50) | engine 7.372 convention ENGINE WRONG +2.291 m3: replaced in the candidate by T-193 (after T-187) |
| Pool bar populations R1 / R2 | rebar | STRUCTURE (rebar); lengths MUST follow the VERIFIED wall 1.20 m and base 0.40 (T-183 r2); T-166 rev1 lengths on 1.15 are STALE | BLOCKED in V3.0.5 (T-179) | T-183 r2 6380294 | T-191 (rev2, both details side by side, D-57 stays a designer item) |
| Railings and balustrades (roofs 19.150 m, ST-02 balustrade + 1F gallery 16.324 m, D-23 2.400, D1 1.042 DRAWING-CONFIRMED; ST-01 inner balustrade HELD) and shutters (6 leaves W14 / W11 / W12) | metalwork, stair finishes, openings, facade | METALWORK (new category, T-164); stair railings stay in this line, never in the stair concrete or marble; shutters belong to the OPENING they cover (T-150 ids), m2 HELD | T-164 READY (d849ca4) | DXF bands by handle, NW / SE elevations, p.12 fence sheet | GF sea strip RL-04 6.127 m in front of W15 / W16: plan band vs NW elevation (end piers, no infill): HELD in BOTH metalwork and the T-162 facade / parapet chain until classified, quantity in neither (never twice); 0.200 m projection on the 1F SE face = facade panel / frame over 7.500 m (FACADE trade, quantity UNKNOWN) |
| Default guard (16:20 row) | every trade | unchanged ruling | T-186 MERGED 18b12176, but it broke the rebar firewall test (default_guard.py undeclared): fix T-190 before T-187 wires it | | T-190 |
| Opening deductions (16:20 row) | | unchanged ruling | T-175 MERGED b903360c (Checker 0.0 % on GF-W32 / 1F-W23); 43 walls net 476.21 m2 candidate | | consistency plan / elevation / schedule: T-194; block units: T-176 |
| ST-01 shaft walls (16:20 row) | | unchanged ruling | T-173 MERGED 8b4d2c83 with D-T173-1 (roof panel prints T 18 not 0.16; below 1 %) | | |
| 1F-11 contour (16:20 row) | | unchanged ruling | T-128 r3 MERGED a6ac2c66 (Checker contour 22.1507 vs 22.149 m; owner gross 74.20 / net 59.45 m2, 0.0 %) | | closed |

### Lead 2026-10-22 16:20 (from T-184, T-171, T-150 r2, T-167, T-172, T-162 r2 MERGED; T-128 r2 REJECTED; T-183 r2, T-186, T-175, T-182, T-173 READY)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Staircase identity (CORRECTS the 12:20 row): ST-01 = dog-leg BESIDE THE LIFT, GF -> 1F -> 2F (ends at 2F); ST-02 = ROUND reception stair GF -> 1F; ST-01b = 4-riser lobby flight +0.30 -> +1.00 inside the ST-01 shaft; entrance stair separate | concrete, rebar, formwork, marble, handrails, shaft walls | STRUCTURE for flights / landings / waists (T-184 ids); floor arrivals 2 x 1.95 x 2.50 are FLOOR SLAB, never stair | T-184 MERGED 924c2bd; Checker 0.0 % on MS2-L 1.059 and RS-S 0.972 m3: both lines PARTIALLY VERIFIED (1 flight each) | T-184 ledger; section A-A; ST p.4 / p.5 'T 16' | engine D-T184-1 (1F -> 2F flights folded away, -2.598 m3): a fix task for the candidate (T-187); turn slabs, closing riser, curved treads HELD |
| ST-01 stair shaft walls N / W / E (one continuous face each, +0.30 / +1.00 to the roof soffit over the 4.50 m void; south side OPEN above GF) | plaster, paint, blockwork, stair concrete | WALL elements of lane A (plaster / paint faces; T-173); the stair takes no wall area; the GF south wall exists only under the 1F slab | T-173 READY (006acbd): owner manual 142.22 m2 gross beside drawing-derived 171.88 .. 175.14 m2; 7 held items | T-184 stair ids (cited, not re-derived); section A-A; ST p.4 / p.5 B2 flush, 'B3 (With Stair)' | B20 / B23 bulkhead faces and the winder soffit belong to CEILING (T-147 family) if the Checker confirms; never twice |
| Opening deductions per host wall (71 openings bound to the T-143 runs) | blockwork, plaster, paint, facade, lintels, waterproofing upturns | OPENINGS own size and count (T-150 merged); each trade deducts by its own physical scope (Q-73: masonry only where block is built and the opening lies inside the measured gross run); lintel face listed for the LINTEL line only | T-175 READY (d3e11eb); 28 openings HELD | owner Q-73 (confirmed 08:35), T-150 r2 census | 2 openings missing from the T-150 census and the mixed sill basis W01: back to OPENINGS (Checker to confirm on T-175) |
| Pool wall upstand 0.15 above the deck finish along 8.998 m (outer face 1.350 m2) | concrete, formwork, waterproofing, external finish, deck | STRUCTURE (inside the 1.20 wall, no extra m3); its outer face is a FORMWORK and EXTERNAL-FINISH face; the deck line stops at the upstand face | T-183 r2 READY (c046645) | NW cut; owner 11:50 conditions (c) | Checker re-checks condition (c) + upstand faces only |
| 1F-11 east master + entry, W17 curved inner glazing band 3.289 m | plaster, paint, openings | PLASTER / PAINT contour = drawn face length (curved band counted once, jamb fillet arcs 0.177 + 0.043 m are WALL); the frame cavity behind the glazing is never contour | REJECTED r2 (Checker 16:11: contour 22.150 vs 22.350 m, +0.9 %; owner net +1.25 %) | Checker's own polygon from the DXF | T-128 r3 |
| Default values in candidate lines (any line resting on a convention where a document prints a value) | every trade | the GUARD holds the line; a convention never releases where a printed value exists (owner pool lesson) | T-186 READY (2e8bf5c), unwired | owner 11:50; standard 2.4 | wiring into the candidate as its own package after T-179 (T-187 carries D-T184-1 with it) |
| Corners and parapets (12:20 row) | facade | unchanged ruling | T-172 and T-162 r2 MERGED 16:01 (pair) | | his parapet third line 140.27 and 1F 1.70 still UNRESOLVED (designer item) |

### Lead 2026-10-22 12:20 (from T-183 and T-163 REJECTED, T-171, T-172, T-162 r2 READY, T-177 / T-169 / T-140 MERGED; owner 09:40 teaching case and 11:50 response)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Swimming pool shell POOL-01 (D-shaped: base 10.9356 m2 x 0.40 printed = 4.374 m3; wall ring 2.3568 m2, curved part 1.0367 m2) | concrete, rebar, formwork, waterproofing, pool finishes, external floor (deck), excavation | STRUCTURE for the shell (one concrete line, base and walls once at the junction); waterproofing and tiles take the water faces as surfaces, no volume; the deck is a separate EXTERNAL line (7.605 m2), never also a pool face | base VERIFIED (checker 12:05); walls DRAWING-CONFIRMED at 1.200 m (structure line) pending T-183 r2; line as a whole PARTIALLY VERIFIED (owner 11:50: verified only on all 8 checks) | ST p.7 (0.40, "AS PER ARCH"), architectural NW cut (inner face -0.90 to rim +0.30, 50 mm build-up), owner Q-26 A (flat floor) | wall height basis: STRUCTURAL 1.20 governs concrete / formwork / rebar; the printed 1.15 is the FINISHED water depth and governs only the water-face finish line, both labelled; 0.15 m upstand above the deck finish (outer face formwork / waterproofing / finish) to be added by T-183 r2; pump room and steps NOT DRAWN in any document read (NOT APPLICABLE WITH EVIDENCE, not 0 by default); rebar R1 / R2 HELD (designer, two-zone detail) |
| Main stair ST-01 and the stair beside the lift ST-02 (identity of ST-02 vs the reception round stair OPEN) | concrete, rebar, formwork, marble, handrails, ceilings, lift-shaft walls (blockwork, plaster) | STRUCTURE for flights / landings / waists (T-184); MARBLE + handrails by OWNER_RULE_STAIRS (lane A); the shaft walls round the lift and the stair are WALL elements of lane A (T-173), never also stair concrete; landings never also a floor-slab line | T-184 TODO (owner priority) | owner teaching case 09:40 (his cells 7.123 + 1.008 / 5.510 / 1.411) | T-173 reads T-184's stair inventory before fixing the shaft wall geometry when T-184 is READY; if T-173 lands first, it names the stair element ids it assumes and T-184 checks them |
| Domes D1 .. D3 (approved design S0) | concrete, rebar, formwork, roofing, waterproofing, skylights | STRUCTURE in S0 (2 by ST p.7 detail, third HELD); S1 (client request, no shell) a separate NOT RELEASED scenario; S2 UNKNOWN (no consultant revision, owner 11:50) | S0 kept; HELD where no detail | owner Q-27 A, Q-29 as refined 09:40 / 11:50 | T-185; T-049's "dome part closed" text is superseded (domes stay in S0) |
| Column joint faces (30 columns; COL-GF-19 own 1.004 vs ledger 1.124 m2) | formwork | FORMWORK (structure); a face covered by a framing member counts that member's own width only | REJECTED (D-T163-1); line 14.224 m2 NOT VERIFIED | checker re-measure 12:05 | T-163 r2 (through / flush beams and oblique members) |
| Parapets and exterior corners (one physical element set, two tasks) | facade plaster, beads, Sigma comparison | FACADE corners and parapet faces: T-172 owns the PHYSICAL items (m.l and m2); T-162 r2 is the comparison to his Sigma rows and takes its figures from T-172 (never a second measurement) | both READY; checked as one pair | owner notes 07:10 / Q-73 / Q-74 | his parapet third line 140.27 and 1F 1.70 height UNRESOLVED (designer: ST p.14 three parapet types deferred to the architectural detail) |

### Lead 2026-10-22 08:20 (from T-163, T-169, T-158, T-150 r2, T-151 r2, T-128 r2 READY; T-166, T-160, T-165 MERGED; owner-notes correction 07:10; owner directive 08:05)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Exterior corners / arrises / stop-ends (Sigma "corners") | facade plaster, beads, parapets | FACADE, ONE m.l line: physical length 457.095 m.l measured (vertical 128.984 + parapet top edges 138.481 + reveals 189.630) + 58.600 door jambs ASSUMED — OWNER-APPROVED (Q-55 C) + 20 jamb pairs HELD. CORRECTS the 04:20 line: nothing is "for the owner to decide" any more; the owner-notes correction (07:10) shows "2 m = 1 m" is a half-rate payment convention, so contract / payable quantity (his half) and the Urban PDF rate basis (1,300 m.l x 1.25 KD) are separate columns, never m2 and never a change to the physical length (standard section 3). Parapet decomposition (two faces, top surface, arrises) is T-172 | DRAWING-CONFIRMED (m.l) | OWNER_NOTES_SIGMA correction; standard s.3 | T-172 |
| Door D-GF-06 (GF, to the +1.00 landing) | openings, facade, plaster reveals | OPENINGS: 2.200 m2 = printed width x 2.20 (ASSUMED — OWNER-APPROVED, Q-55 C), FLAG; the render's arched head (T-161 F22) is NOT IN THE DRAWING and contradicts no printed value, so it is not quantified: HELD as its own item | ASSUMED — OWNER-APPROVED + HELD increment | WORKFLOW_CONTROLS s.8; contrast main door (render contradicts a printed size: HELD) | D-58; T-150 r2 |
| Formwork faces (all RC elements above and below ground) | formwork, concrete | FORMWORK: derived from the verified concrete faces (T-139 slabs, beam register, T-119 columns); one face belongs to one element; junctions deducted (beam into column, slab over beam); below-ground sides FORMED vs EARTH_CAST both shown (OQ-10 open alternatives, not a new question) | CALCULATED, pending checker | T-163 | checker RUN B |
| Owner stair rule calculator (UP-STAIR-015, every villa) | stair finish, stair concrete | STAIR: check mode only; the drawn count governs (owner S-1); entrance flight E1 5 x 0.170 FLAGGED (same as D-56), not changed | rule recorded, not wired | OWNER_RULE_STAIRS | checker RUN C |
| Stair shaft walls (Q-72) | plaster, paint, block | PLASTER / PAINT: HELD; Q-72 is now investigation T-173 (owner directive 08:05), not an owner question; T-128 r2 keeps the shaft out of both methods | HELD | standard s.2 | T-173 |
| Angled straps SB2 / SB3 (Q-74 answered 08:05) | concrete, rebar, formwork, excavation | CONCRETE at the beam-axis length (2.293 / 3.258 m between established faces, footing overlap counted once); bars, formwork and excavation derived separately | HELD until T-174 merges | owner directive s.7 | T-174 |
| Block / plaster / paint openings (Q-73 answered 08:05) | block, plaster, paint, openings, waterproofing | each opening id has separate consequences per trade; full opening deducted only where that trade is physically built round it; no masonry invented behind full-height glazing | HELD until T-175 merges | owner directive s.6 | T-175 |

### Lead 2026-10-22 04:20 (from T-151, T-157, T-160, T-162, T-165, T-166 READY; T-150 / T-128 REJECTED; T-142, T-152, T-143, T-147, T-159, T-161, T-154 MERGED)

BASELINE RULING (from T-165, which reproduced both runs and traced the provenance). THE RELEASED BASELINE is spec
`V29_ROUTEG_NO_PROFILE` (run A: ARCH_TAKEOFF_V2.9 + route G, conventions V6, no profile, no facts, no project id; 1,455
lines; BOQ_LINES.csv b96185d4...). Reasons: (1) it is the configuration the scoreboard recorded when released figures were
first reported (verifier 19th run, commit 8774071, "no facts file, no profile": concrete 92.77 vs 111.81 m3, -17.03 %) and
the one BOQ_FAMILY_MASTER 1.1.0 `run_evidence.released_run` names; (2) it releases nothing on a value outside owner Q-17 A,
while run B releases on the M4 profile, which is not a Q-17 A data file and carries two values the T-044 audit classed
DIFFERENT / NOT_PRINTED. Spec `V29_ROUTEG_PROFILED` (run B, 1,621 lines) is the COMPARISON BASE: V3.0.x candidates run on
the same profile and project id, so Gate B pairs lines against B; every Gate B verdict ALSO gives the element diff against
A. The "-17.16 % on 5 lines" figure is reported only as "profiled comparison run". This names an unrecorded configuration;
it does not switch the released default (V2.9 + route G, owner only). T-167 removes the dependence of candidate lines on
DIFFERENT / NOT_PRINTED profile values (spec C = PRINTED values in a Q-17 A data file); T-168 makes the Gate B tool check
the manifests.

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| Main entrance door, printed 2.00 x 2.50 double (5.000 m2) | openings, facade, block deduction | OPENINGS; CORRECTS the 00:20 line: the line is HELD with cause T-161 F07c (render single leaf vs printed double); 5.000 m2 kept as the candidate value | HELD | WORKFLOW_CONTROLS s.8 (a DIFFERS finding that affects a quantity holds it); checker T-150 verdict 04:05 | D-53; T-150 r2 |
| W16 (twin of a printed window) | openings, facade, plaster reveals | OPENINGS: width 1.55 m only, NO area | HELD | no rule for a twin; INFERRED is not a s.5 status | D-45; T-150 r2 |
| GF covered porch: floor at court level 10.680 m2 (2.00 x 4.30 + 1.20 x 1.50 + 1.40 x 0.20, T-157) | external floor, ceiling, stair | FLOOR: porch line 10.680, material HELD, never in the court interlock line. SOFFIT 19.181 m2 (CEILING trade) covers porch floor + entrance treads 3.360 + top landing 5.180 = 19.220 (checker settles 0.039). The owner's "about 19.181" (23:20 note) was the covered area, not the porch floor | floor DRAWING-CONFIRMED, not VERIFIED | owner 23:20 (court level); sections B-B / A-A | checker RUN 2 |
| Entrance stair E1: treads 3.360, visible risers 1.960 (5 x 0.140 x 2.80), top landing 5.180 | stair finish, external floor, ceiling | STAIR finish, MARBLE (outside stairs rule); never also in the porch or court line; drawn riser 0.170 > 0.16 = FLAG under owner stair rule S-1 (drawn governs) | DRAWING-CONFIRMED | OWNER_RULE_OUTDOOR_FLOORS; OWNER_RULE_STAIRS S-1 / S-2; UP-STAIR-001 / -003 | D-56 |
| GF north side walk | external floor | FLOOR FINISH porcelain: measured 21.021 DRAWING-CONFIRMED (checker 21.021) beside owner manual 23.955 ASSUMED — OWNER-APPROVED; difference = boundary wall 0.20 x 15.97 (his 1.50 runs to the wall's outer face) less corner column 0.20 x 1.30; both shown, neither replaces the other; the 0.327 band T-153 put here belongs to the pool deck | both shown | owner additions 20:45; T-157 | none |
| Pool deck 7.939 m2 (7.605 + the 0.334 mouth band under the 1F edge) | external floor, pool | EXTERNAL FLOOR, material HELD | HELD | owner 20:45 / 23:20 | none (owner, not asked again) |
| Six outdoor openings with a printed 0.15 m level change, no step drawn (7.30 m) | external floor, stair, openings | none until the designer says how the level change is made (step, sloped sill, ramp): locations and widths DRAWING-CONFIRMED, finish HELD; the owner stair rule is NOT applied (nothing shows a stair); his "gate steps" 6 items 7.70 m comparison only | HELD | MISSION.md drawing-first; OWNER_RULE_STAIRS S-1 applies to an undrawn STAIR, not to an unknown threshold detail | D-55 |
| GF garden band 13.986 m2 | floor area, landscape | none until classified; section A-A draws floor +1.00 to the facade under the +5.50 slab (new evidence) | HELD, CONFLICT | defect B9 | D-48 |
| Stair landing steel strip over A1-L1 (18.204 kg) | rebar (frozen S8.7 line and the T-166 ledger) | REBAR, ONE line: lane I takes the T-166 ledger line and the frozen S8.7 line never enters the same total | DRAWING-CONFIRMED (0.0 % to frozen S8.7) | T-166 | lane I |
| Pool walls / floor steel (R1 deep 888.90 .. 927.54, R2 shallow 615.34 .. 639.45 kg) | rebar, pool concrete | REBAR; HELD: the p.7 detail draws two zones, the owner fixed a flat floor (Q-26 A): which population serves the flat floor is for the designer | HELD | Q-26 A; T-166 | D-57 |
| Dome ring beams | beam concrete, slab | confirmed (20:20 ruling): ring = in-bay part only (west 0.7552 m3 DRAWING-CONFIRMED; east HELD 0.8997 candidate, no mark); full annulus would double count 0.697 / 0.552 m3 | DRAWING-CONFIRMED / HELD | Q-44 A; T-160 | checker RUN 1 |
| Exterior corners (Sigma "corners") | facade plaster beads / corner treatment | FACADE, in m.l: 457.095 measured (vertical 128.984 + parapet top edges 138.481 + reveals 189.630) + 58.600 door jambs ASSUMED — OWNER-APPROVED (Q-55 C height) + 20 jamb pairs HELD; m2 conversion NOT applied | DRAWING-CONFIRMED (m.l) | owner Sigma notes item 2 (owner decides) | OWNER PACKAGE 04:20 |
| 0.200 m projecting outline outside the 1F / GF SE faces (layer D / layer 2) | facade, possibly shutters / ledge | none until classified | UNKNOWN | checker 04:05 observation | T-164 |
| Column, ground-beam / strap and beam steel in V3.0.3 (1,371 ledger lines + 497 superseded route lines) | rebar | REBAR from the Gate-A-verified ledgers only; route G convention lines kept as SUPERSEDED (never deleted, never summed); straps HELD on Q-74 A / B / C; planted columns HELD (D-46) | DRAWING-CONFIRMED / HELD / UNKNOWN, NOT RELEASED | T-148, T-138 r2, T-141, T-149 MERGED | T-151 Gate B (3 slices) |

### Lead 2026-10-22 00:20 (from T-142, T-152, T-159, T-161, T-140 READY; T-149 / T-144 / T-155 / T-134 MERGED; owner outdoor-floor decisions 20:45 / 23:20)

Code: element_register_v0 MERGED 0c8eae7 (checker 22:40). Baseline note: two runs are both called "released V2.9 + route
G" (T-140: without the route G profile 1,455 lines; with profile + facts 1,621 lines; 8 family figures differ). Until T-165
pins one by provenance, every register row and every Gate B diff names the run it uses; the checker's T-156 / T-133 diffs
used the PROFILED run.

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| GF north side walk (the strip between the north neighbour wall and the house; T-153 "north court strip") | external floor, court | FLOOR FINISH, porcelain / ceramic, part of the house; NOT interlock and NOT in the court line. Owner manual 1.50 x 15.97 = 23.955 m2 beside the measured 21.348 (checker 21.021) | owner manual ASSUMED — OWNER-APPROVED (rule file, additions 20:45); measured DRAWING-CONFIRMED, split HELD | OWNER_RULE_OUTDOOR_FLOORS additions 20:45 (supersedes the 20:25 line that put the north strip in interlock) | T-157 reconciles 2.6 m2 term by term |
| GF west court less the porch (138.761 - 19.181 m2, less the 3.360 element footprint per the measured geometry) | external floor | EXTERNAL FLOOR, interlock ("owner choice, differs from render": T-161 renders show stone) | DRAWING-CONFIRMED area, not VERIFIED | owner 23:20 | T-157 |
| GF covered porch about 4.60 x 4.10 = 19.181 m2, at court level | external floor, soffit, court | FLOOR: its own line, material HELD; never also in the court interlock line. Its SOFFIT 19.181 m2 is a separate surface: CEILING trade (T-142 FIN.CEILING line, finish HELD Q-68 C) | floor DRAWING-CONFIRMED area, material HELD | owner 23:20; Q-68 C | owner decides material later (not asked again) |
| GF side passage 5.640 m2 | floor, soffit, external walls | FLOOR: porcelain / ceramic (sides rule); SOFFIT: CEILING trade (T-142 line 5.640); walls: external plaster / paint (Q-67 A) | PROVISIONAL external (Q-67 A cond) | owner 20:45 sides rule; Q-67 A | D-48 |
| Pool deck 7.605 m2 | external floor, pool | EXTERNAL FLOOR; material HELD | HELD (owner not sure) | owner 20:45 / 23:20 | none (owner) |
| Entrance steps (outside stairs) | stairs, external floor | STAIR finish, marble | DRAWING-CONFIRMED geometry where printed | owner rule (outside stairs marble), UP-STAIR-001 | T-157 / T-158 check mode |
| Footing steel (19 printed-count footings 874.86 kg; F8 / F12 / F13 / F14 / FF) | rebar, footing concrete | REBAR; count-printed footings DRAWING-CONFIRMED in V3.0.2; per-metre five HELD 2,742.51 .. 2,836.40 kg; 20 BOXED cells HELD | DRAWING-CONFIRMED / HELD, NOT RELEASED | T-136 MERGED, T-142 READY (Gate B), T-155 r2 MERGED 15fd913 | Q-71 |
| Suspended-slab steel, 62 panels | rebar, slab concrete | REBAR per panel and direction; the 8 dome corner pieces and 5 other unbarred panels HELD (D-51); top bars HELD range (D-49) | bottom lengths DRAWING-CONFIRMED (not VERIFIED), counts HELD on Q-71 | T-152 READY | Q-71, D-49 .. D-52 |
| Soffits over outside air 44.446 m2 (porch 19.181, passage 5.640, pool court 12.834, 1F edges 4.374 + 2.417) | ceiling, slab, external plaster | CEILING (area lines); finish HELD; SX-01..03 (1.665 m2) listed, never added | VERIFIED pool court (checker 12.8343); others DRAWING-CONFIRMED | Q-68 C; T-127 / T-142 | T-142 Gate B |
| Exterior faces per side and storey (T-159: 1,022.534 m2 measured + 6.822 .. 13.261 HELD + 13.079 m slab edge) | facade plaster / paint (freelancer "Sigma"), parapets, blockwork, openings | FACADE finish per face; parapet faces and roof faces are FACADE lines of their own; a face standing on a lower roof starts at that roof; boundary / street fence NOT facade (Q-65 HELD); domes EXCLUDED (owner Sigma item 3, client change Q-29); openings listed apart (T-150 owns count and size) | DRAWING-CONFIRMED (printed levels), wavy-parapet heights from the CAD top line flagged for the checker | Q-07 B, Q-64 B, owner Sigma notes | T-162 reconciles his 1,502.84 / 1,469.97 m2 term by term; corners m.l FLAGGED (R-11 c) |
| Railings / balustrades and shutters | stairs, facade, openings, metal works | none yet: a missing BOQ category; T-164 builds the census of what is DRAWN | NOT IN THE DRAWING for the rendered ones (no quantity); UNKNOWN for the category | T-161 READY | D-54, T-164 |
| Main entrance door 2.00 x 2.50 (double, printed) [CORRECTED by the Lead 04:20: HELD, see the 04:20 table] | openings, facade, block deduction | OPENINGS: printed size governs (5.000 m2); render single leaf is a DIFFERS note only | DRAWING-CONFIRMED | Q-55 C (2.50 printed governs) | D-53 |

### Lead 2026-10-21 20:20 (from T-119 r2, T-133 MERGED, T-149, T-150, T-153 MERGED, T-159, T-160)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| 2F columns C2 / C3 at the water tank | column concrete, beam B15 / B3, rebar | COLUMN concrete, height range 3.00 .. 3.80 m (joint +0.160 m3 at the high end) | HELD (range) | T-119 r2; D-44 open | designer D-44 (B15 upstand or downstand) |
| 1F column C9 framing incl. B19 40 x 75 (oblique) | column, beam | COLUMN takes the joint once; B19 takes its span to the column face | DRAWING-CONFIRMED, not VERIFIED | URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 | checker run A |
| 5 columns above the necks with no column on the slab plan above (2.268 m3) | column concrete, column steel | COLUMN: NOT APPLICABLE WITH EVIDENCE in V3.0.1; their 10 steel lines STALE until T-151 | VERIFIED (checker 17:40, by hand) | T-126 / T-133 Gate B | T-151 rewires steel |
| Blinding under footings 15.179 m3 | blinding concrete | BLINDING, released in the candidate only | VERIFIED (hand 15.213, -0.2 %) | T-126 / T-133 Gate B | ground-beam and strap blinding stay HELD; lower bounds over hand (T-142 D3) |
| Beam spans running over end columns (5 register spans) and GF CB7 (2 spans, not 1) | beam concrete, beam steel | BEAM: span to the column face, column takes the joint | DRAWING-CONFIRMED (T-149), not VERIFIED | URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 | T-160 corrects the register with the dome rings |
| Dome ring beams (each dome opening) | slab, beam, ceiling | BEAM: in-square ring part only; the parts inside B6 / B25 / CB12 belong to those beams; the 8 dome corner pieces are SLAB | DRAWING-CONFIRMED (checker 16:45), not VERIFIED | owner Q-44 A; non-overlapping model | T-160 |
| Windows W01 .. W26 and doors (65 openings) | openings, block deduction, plaster / paint reveals, facade | OPENINGS trade owns count and size; block, plaster and facade list the opening and deduct only under their own rule | 8 windows DRAWING-CONFIRMED, 20 HELD (D-45), W16 HELD (no rule for a twin), doors ASSUMED — OWNER-APPROVED 2.20 m (Q-55 C) | T-150 | D-45, D-07 |
| Facade sides (exterior wall faces per side and storey) | facade plaster / paint, blockwork, openings | FACADE finish per side; openings listed apart; boundary / street fence NOT a facade (Q-65 HELD) | to be measured | owner request 2026-10-21; Q-64 B | T-159 |
| GF north court strip (21.021 checker vs 21.348 worker) and the 0.37 m2 duct outline in it | external area | EXTERNAL area; split with the west court HELD | HELD (split) | checker 18:40 on T-153 | T-157 |

### Lead 2026-10-21 16:20 (from the CLAIMED / READY tasks T-133, T-134, T-148, T-153, T-154, T-155)

| Element (Alsenan unless said) | Trades that touch it | Owner trade (ruling) | Status | Basis | Open item |
|---|---|---|---|---|---|
| 1F arrival landing 4.875 m2 | floor finish (porcelain, marble), stair | floor finish: MARBLE line only, once; porcelain total excludes it | DRAWING-CONFIRMED area, not VERIFIED | owner Q-66 B | V3.0 has no outline for it, so the one-finish check cannot see it (T-133b landing reader) |
| 1F east-flight foot piece 0.4025 m2, closed element 0.1175 m2 | floor finish | HELD until D-13 / D-23 settle landing or flight | HELD | owner instruction 2026-10-20 17:54 (4) | D-13, D-23 |
| Pool-court soffit PL-03 12.834 m2 (net of void 3.690) | ceiling, slab soffit paint | CEILING trade (area); finish HELD | DRAWING-CONFIRMED (T-127 merged, T-154 READY) | owner Q-68 C | the CAD census basis 14.704 m2 must never feed a ceiling line: it holds the opening heads and wall tops below (1.665 + 0.276 m2 would be counted twice) |
| Pool-court wall openings SX-01 (4.521 x 0.200 head, under CB1) and SX-03 (1.000 x 0.200, under B24) | ceiling census, plaster / paint reveals, openings | PLASTER / PAINT as opening-head reveal lines; listed as OPENINGS in T-150 | HELD (jamb heights not printed) | UP-GEN-003 opening table | neither V2.9 nor V3.0 records them as openings (T-150 scope; D-45) |
| Curved-glazing outer reveal SX-02 0.561 m2 | ceiling census, external plaster / paint | external PLASTER / PAINT reveal strip (T-123 family) | HELD | Q-64 B reveal treatment | which finish item the reveal belongs to in CAD (owner 2026-10-20 17:54 (3)) |
| Court wall tops 0.276 m2 (east piers, north pier, NE corner) | ceiling census | none: NOT APPLICABLE (no finish line) | NOT APPLICABLE | T-154 classification | checker confirms on Gate A |
| Turned 1F column 0.200 x 0.900 over the pool court (face 0.065 m2) | structure, soffit census | COLUMN concrete (structure); the B28 soffit around it stays in the ceiling line | DRAWING-CONFIRMED | ST GF roof-slab sheet column mark | a soffit census must test slab-sheet column faces against the plan below |
| GF side passage 5.640 m2 (3.600 + 1.560 strip) | floor area, soffit, external plaster | EXTERNAL area (floor and soffit as external lines); NOT internal floor | PROVISIONAL (Q-67 A conditional until the drawings confirm open to air) | owner Q-67 A | V2.9 counts it internal (defect, T-153); D-48; T-157 |
| GF garden band 13.986 m2 | floor area, landscape | none until classified | HELD, CONFLICT | label "garden" vs enclosed and roofed drawing (defect B9) | D-48; T-157 |
| Courts 167.714 m2 (west court 138.761 incl. porch 19.181 and E1 footprint 3.360; north strip 21.348; pool deck 7.605; pool water 7.548 is NOT a floor) | external works, waterproofing, pool | EXTERNAL area line; finish HELD | DRAWING-CONFIRMED area | OQ-04 (open, re-asked 2026-10-21) | his yard 151.80 m2: UNRESOLVED until OQ-04 sets the scope |
| Pantry 13.50 m2 | floor finish, waterproofing | WET floor (waterproofing zone + one floor finish line) | DRAWING-CONFIRMED | owner Q-37 A | none |
| Footing F10-type (FOOTING_LABEL_CONFLICT, 1.960 m3) and 5 beams (WIDTH_CONFLICT_SECTION, 5.022 m3 + 685.225 kg) | structure, rebar | STRUCTURE; status CONFLICT | CONFLICT, released by a route convention in V2.9 and V3.0 | none found: no owner rule names the convention | checker (Gate A on T-134) states whether an owner rule backs the convention; if none, lane I holds these lines in the next V3.0 package (a new task, never an edit of V2.9) |
| 3 planted columns (172.56 kg released by frozen S3.1 from a duplicated schedule row) | structure, rebar | REBAR line HELD in V3.0 | HELD | T-148 finding; D-46 | T-151 wires the hold |
| Footing bars printed per metre (F8, F12, F13, F14, FF) | rebar | REBAR; count rule HELD (A / B / C = 2,742.51 / 2,836.40 / 2,797.81 kg) | DRAWING-CONFIRMED notation (bars per metre); count UNKNOWN | owner Q-71 open | FF lift footing top / bottom legs drawn but not dimensioned: HELD |
