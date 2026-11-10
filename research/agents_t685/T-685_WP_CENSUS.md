# T-685 waterproofing HELD / blank / MISSING census and MEASURABLE NOW pieces (lane A, research, unwired)

Worker 2, 2026-11-10. Candidate ARCH_TAKEOFF_V3.0.66 (T-677 line index, file sha256 02065c41..., lines c411617d).
Nothing wired or released; V2.9 + route G unchanged; no engine module, rule / knowledge version, registry or frozen
file touched. Rules R-T685-1 (census), R-T685-2 (element totals), R-T685-3 (wet-room upturn, edge, drains) in
`t685_rules.py`; builder `t685_alsenan.py` (`--check`, `--dxf <private P7757.dxf>` re-reads the pantry handles);
outputs `out/T685_WP_CENSUS.{json,md}`; tests `tests/t685_wp_census` (22, synthetic villa W685 + development villa).
Drawings by Drive title only: "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...,
re-checked) and sanitary-7757.pdf (3 drainage sheets, image read at 220 / 400 dpi), own decode this run.

## Physical elements and scope (ERS s.2.1)

The membrane and its accessories: roof flat area (m2) and roof upturn (lm), wet-room floor (m2), wet-room wall upturn
0.20 m (m2), membrane edge on an open side (lm), floor penetrations (pcs), door threshold / transition (m2, pcs), pool
membrane / screed, substructure (footings, ground beams, necks, lift pit), planters / terraces; procurement (rolls,
product item) kept apart from installed area (UP-WP-MAT-001). Filter: every `FIN.WP.*` / `WP.*` code (160 lines);
`EXT.POOL.WATER_FACE` is the pool tile face, not a membrane, so it is outside the filter.

## Census: 58 entries = 53 HELD candidate lines + 5 MISSING rows (none twice)

| Class | Entries | What holds them |
|---|---|---|
| DESIGNER_ITEM | 29 | 15 door transitions (Q-35 C detail not printed; incl. the missing pantry one), 3 open-side edges (GF-02 / GF-11 / GF-14, Q-37 A covers the pantry only), 11 substructure (Q-21 C founding level / detail, Q-31 C 1B1B two tags, D-43 lift pit height, product not printed) |
| OPEN_BOUND | 18 | floor penetrations: AT LEAST the drains printed on the drainage plan (UP-WP-004 1.1.0 'counted from the drawings'); other pipes wait on a wet-room detail |
| MEASURABLE_NOW | 4 | pantry (GF-07, Q-37 A): wall upturn, open-side edge, door threshold, transition count (below) |
| MEASURED_NOT_WIRED | 3 | pool-court ledge membrane 0.639573 m2 (T-529), ledge upturn 0.551614 lm and window run 0.500002 lm (T-522): merged, Checker-verified, overlay only |
| OWNER_OPEN | 3 | 2F top roof membrane, upturn, rolls: Q-34 PARKED (raised at the 12-13 Nov milestone) |
| NO_PHYSICAL_ELEMENT | 1 | L-f78da96a 'termination other' on the GF core W.C. diagonal face: T-128 r3 reads it as WALL (T-303 f5): propose EXCLUDED |

5 EXCLUDED lines (2 duplicate door sides, 3 window terminations with sills above the upturn) listed apart, not held.
Families with no line: B8-04 shower tanking (UP-WP-004 1.0.0 puts the shower in the wet floor + 0.20 upturn; higher
tanking is not in force) and B8-07 terraces / planters (absence established by T-486, ENGINE_RIGHT).
Membrane system / product: printed on no sheet for wet rooms, roofs and pool: HELD by name; substructure: p.13 prints
two systems, the governing one is Q-21 C (designer): HELD. No default product, lap or coat count applied.

## Candidate totals by element (V3.0.66; flat and upturn apart, installed and procurement apart)

Released: roof flat 209.018867 m2 (4), roof upturn 186.782544 lm (4), wet floor 85.575710 m2 (18), wall upturn
25.214585 m2 (17), door threshold 1.930379 m2 + 14 pcs, pool 29.582355 m2 + 1.524503 m3, substructure 360.0282 m2 +
6.5275 m3; rolls 52 pcs (procurement). HELD: roof flat 0 .. 0.639573 + 1 blank; roof upturn 0 .. 4.028279 + 1 blank;
thresholds 0 .. 1.819408 (11) + 3 blank; edges 0 .. 3.160363 (4); penetrations 17 blank; wall upturn 1 blank;
substructure 11 blank (never 0, never summed).

## MEASURABLE NOW: own measure this run

**Pantry GF-07 (P7757.dxf, lengths relative to the box SW corner; Q-37 A box 4.500 x 3.000, DIMENSIONs 5E1 / 5D5).**
West face 4.500: walls B0 0-0.10, AF 1.10-2.15, AE 3.65-4.50; windows W10 0.10-1.10 (1.000) and W09 2.15-3.65
(1.500) on layer W (T-175 AGREE). North face 3.000: walls 158 0-1.659, 159 2.659-3.000; door D120 33E gap 1.000,
wall 0.200 (158 / 15A). South face A6 3.000 full. East side B3 0-4.00 + AD 4.00-4.50, layer 5, no wall: open.
Column 2FAE 0.050 proud over 0.900 steps orthogonally: run unchanged.

1. **L-8090ff20 wall upturn: blank -> 1.400 .. 1.900 m2 (OPEN BOUND).** Run 10.500 - door 1.000 = 9.500 lm; the two
   window sills are printed nowhere (D-45): low excludes them (7.000 lm), high includes them (9.500 lm); x 0.20.
   The old cause 'wall heights not printed' does not enter a 0.20 m upturn; the open side is the Q-37 A threshold line.
2. **MISSING pantry open-side edge: 4.500 lm** (Q-37 A, ASSUMED - OWNER-APPROVED; drawn layer-5 side; the candidate
   text's 4.49 is engine rounding, residual 0.010 m).
3. **MISSING pantry door threshold 0.200 m2** (1.000 x 0.200, DRAWING-CONFIRMED, AGREE T-336) and **transition
   count 1 pcs**; the transition m2 stays HELD (Q-35 C), the penetration AT LEAST 1.

**Floor penetrations (sanitary-7757, legend 'FD FLOOR DRAIN').** Every wet room prints at least one drain: GF-02 / 03
/ 05 / 06 / 07 / 10 / 11 / 12 / 13 / 14 / 16 one each; 1F-07 / 08 / 09 / 12 one each; 2F-02 one; the 1F west bath
pair prints 1 + 2 (cells not mapped to 1F-02 / 1F-03, so each AT LEAST 1). 17 blank lines + the missing pantry row
-> AT LEAST 18 pcs (19 drains printed). W.C. pans and stacks are listed beside, not counted (no wet-room detail).

## Effect if wired, engine vs freelancer

Wall upturn 25.214585 -> 26.614585 .. 27.114585 m2 (+5.6 .. +7.5 %); thresholds 1.930379 -> 2.130379 m2 (+10.4 %),
14 -> 15 pcs; edges 0 -> 4.500 lm released; penetrations blank -> AT LEAST 18 pcs; roof flat 209.018867 ->
209.658440 m2 (+0.31 %), upturn 186.782544 -> 187.834160 lm (+0.56 %) from the merged pool-court pieces. Freelancer:
no pantry membrane at all (Q-37 record); his penetration / edge rows were not searched this run; roof 285.00 m2 / 194.00 m (T-541: -26.4 % /
-3.2 % after wiring, verdicts unchanged). Verdict proposals: pantry upturn / edge / threshold ENGINE_WRONG omission
(owner Q-37 A), freelancer RULE_DIFFERENCE; penetrations UNRESOLVED vs the freelancer (not compared), engine AT LEAST from
the drawing.

## Findings for the Lead

- F-T685-1: the five T-336 pantry ADD_ROW pieces (merged c4246877) were never wired (T-310 'insert not bound').
- F-T685-2: L-f78da96a names an edge on a face the drawing shows as WALL: EXCLUDED with evidence, not HELD.
- F-T685-3: the three pool-court lines are HELD in the candidate while merged values sit in the overlay (wiring gap).
- F-T685-4: the 1F west bath pair prints 3 drains; mapping the cells raises one room to AT LEAST 2.

Lessons-register row (proposed, ERS s.7): 2026-11-10 | 17 penetration lines stayed blank 'count not tabled' and a
0.20 m upturn stayed blank on 'wall heights not printed' | a hold must name only a term the quantity physically uses:
the drainage plan prints every drain body (a firm AT LEAST), and an upturn of fixed height uses wall runs and window
sills, never wall height | before holding, list the quantity's terms and check each on every issued sheet, including
the MEP ones (every villa) | tests/t685 (normal: upturn bound / measured by sill, edge, drains; adverse: open side as a
wall, mm, all-open box, upturn lm into flat m2, HELD as 0, unprinted system) | PROPOSED.
