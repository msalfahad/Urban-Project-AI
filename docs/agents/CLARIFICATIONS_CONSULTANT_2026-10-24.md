# Consolidated designer / consultant RFI package, Alsenan (owner 2026-10-24; DRAFT, NOT TO BE SENT YET)

OWNER 23:57: do not send. LEAD: verify every row against all drawings, schedules and sections, remove any the sources answer, and split into (1) PRIORITY RFIs that each unlock a complete BOQ line (name the line) and (2) REMAINING unresolved questions; keep each row's drawing reference, missing / conflicting information, affected quantity and the clarification required.

## 0. LEAD VERIFICATION 2026-10-25 00:15-00:40 UTC (Lead run session_01M9dY6Pw5JtHHF5a4sbrrDw) — STILL NOT TO BE SENT

STATUS: PACKAGE NOT READY TO SEND. 30 rows checked; 0 removed (no row is answered by the sources); 2 search notes closed
(S14, S5); 4 missing rows found (G1-G4 below: blockers the Checker names on a closable line that this package does not
carry); 9 PRIORITY RFIs formed, 3 of them complete only after their missing row is drafted (P-7, P-8, P-9). The owner
sends nothing until T-287 / T-286 return the G rows with their sheet search.

METHOD AND LIMIT. Each row was checked against the merged, Checker-verified evidence of the sheets it cites: the task
ledgers on the working branch (research/agents_t*), the designer register (DESIGNER_CLARIFICATIONS.md), the element
register and the Checker's CLOSABLE LINES table (SCOREBOARD v2), i.e. "was every relevant sheet read by a merged, Checker-
verified task, and does the sheet print the answer". The Lead did NOT re-open the drawings himself; where a row's search
rests on no merged task, it goes back to an investigation task (none of the 30 does; the G rows do). The unlock test for a
PRIORITY RFI: the Checker's CLOSABLE LINES table names no blocker for that line other than the RFI's rows (internal
agent work excepted and named).

ROW CHECKS (search complete = every cited sheet read by a merged, Checker-verified task):
- S1 Q-21: complete (T-206 MERGED d5df7d1f: 0.17 m build-up VERIFIED; ST p.1 note 1 fixes only a minimum excavation). Kept.
- S2 Q-28: complete (T-233 MERGED 2ecb5bf0, T-253 MERGED dff9cb79: band C1 0.20 own 44.07 m / 3.5256 m3 on the measured
  part; section and crossing level not printed). Kept.
- S3 Q-31 F10+F: complete (T-233, T-239 MERGED 3c9b1484: one outline, two tags). Kept.
- S4 D-16 / D-63 / D-66: complete (T-217 MERGED 65fef8fa, T-256 MERGED 74c966b1: no third member-specific print for any of
  the 15). Kept. (SCOREBOARD row 11 cites "D-64" among the 15: a typo for D-66; D-64 is the P-1F-01 opening.)
- S5 D-02 / D-27: search CLOSED by T-277 MERGED 9446dfcb (Checker 22:59 own band widths): 137 runs = 105 AGREE / 7 CONFLICT,
  exactly D-02 + D-27, no new conflict; CB10 label stands beside the 0.20 outer strip, so D-02 also asks WHICH band is CB10;
  CONC.BEAM on the 7 runs drawn 5.4421 vs scheduled 5.7665 m3 (-0.3244), beam soffit 8.7140 vs 9.0072 m2. Update the row's
  quantity cell to these figures. Kept.
- S6 D-03 / D-04 / D-05 / D-28: complete (T-110 MERGED 575df66, T-252 MERGED b37be82d). Kept.
- S7 D-44: complete (T-119 r2 MERGED 0f32ff8: slab plan and schedule agree on 20 x 120; no section). Kept.
- S8 D-35 / D-33 / D-34: complete (T-138 MERGED 0dec24c, T-242 MERGED 9455a63d, T-264). Carries the UNSUPPORTED-BASIS
  quantity exterior ground beams 11.930 m3 (owner 23:57). Kept.
- S9, S10, S12: complete (T-136, T-138, T-152, T-148 merged). Kept.
- S11 D-57 + pool steps: complete (T-183 merged; no step / ladder on any sheet). Kept, split: steps -> P-2, bars -> remaining.
- S13 D-41: complete (T-139 MERGED ea91168). Kept. Note for the Checker: CONC.SLAB is whole-line VERIFIED without the step
  edges; confirm which line carries the step-edge concrete before this row names a line.
  LEAD 2026-10-25 02:15: RULED by the Verifier (01:34, 02:00): CONC.SLAB is independent of the drop d (same 0.16 slab at a
  lower top; 6 panels 24.7964 m2 / 3.9674 m3 inside the verified 60.2804 m3); step-edge concrete = 0.000 m3
  DRAWING-CONFIRMED (every sunken edge is a beam or column face, T-213). What d moves: CONC.BEAM tops of the two shared
  beams (3.006 .. 3.036 x d m3), riser / beam-side formwork 41.451 x d m2, fill / screed 24.79 x d m3, WP upturn 41.451 x
  d m2, the ceiling level, and BLOCKWORK heights of 7.913 m of GF wall under the panels (7.913 x d m2; register v4 T-288).
  Row S13 restated below. The five GF-roof panels are 19.3964 m2 on the slab line's beam-face polygons (19.386 / 19.396
  were older readings). S13 stays REMAINING: no single line closes on it alone (blockwork has other held pieces).
- P-4 (LEAD 2026-10-25 02:15, Verifier 01:34): CONC.BLINDING also carries the boundary-wall base blinding (UNMEASURED,
  Q-28 A, owner 2026-10-23 21:15 (3): an export row, never omitted), whose size depends on S2; P-4 therefore closes ONLY
  together with P-3 (which carries S2). Table row amended.
- S14 D-43: SEARCH OPEN CLOSED. T-204 MERGED 4fbf7627 (ST p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING': pit depth "As Per Lift
  Manufactures recommendations") and T-227 MERGED ebce3d97 (Checker 21:05: tie beam required at GF, its section and the
  3.00 m datum printed nowhere). Split: tie-beam section -> structural designer; pit depth -> LIFT SUPPLIER (not the
  designer). Kept.
- S15 D-14 / D-15: complete (T-100, T-233). Add to the row: the SB3 / F3 strap soffit level (T-230: HELD 0.0295 .. 0.2683 m3,
  "D-15 narrowed") so the footing line can close. Kept.
- S16 D-11: raised by T-107 (REJECTED) but the note is carried by the merged registers T-225 48e6f08a / T-228 bf4dd2a9
  (black PROVISIONAL on those rows). Complete. Kept.
- S17 D-12: complete (T-226 MERGED a04f8e21). Kept.
- S18 D-61: complete (T-195 MERGED 06c2b045). No quantity; document control: the T-245 export states the structural
  revision UNCONFIRMED (owner 23:57 (4)). Kept, remaining.
- A1, A2, A4, A5, A7, A10, A12: complete (T-112, T-128, T-144, T-147, T-091, T-143, T-161, T-164, T-194, T-195, T-201, T-207,
  T-222 merged). A2: door heights carry ASSUMED - OWNER-APPROVED Q-55 C in the closed doors line (12.760 m2 / 6 pcs): the
  question stays for plaster / paint nets, it blocks no doors quantity. A5 carries two UNSUPPORTED-BASIS quantities: 2F
  columns 3.528 m3 (finished roof +13.90) and annex columns 3.7125 m3 (4.50 m). A12: add D-10 (tile sizes / finishes schedule).
- A3 D-53: complete (T-161, T-207, T-232 merged). Q-76 answered A 23:53 (W17 9.870 m2 opening area); D-53 is now the ONLY
  blocker of the windows line. Split: W02 -> P-1; main door / SX-01 -> remaining.
- A6 D-08 / C-ST-4: complete (T-111, T-184, T-189, T-192, T-258 merged). Carries UNSUPPORTED-BASIS ST-03 0.948 m3. Kept.
- A8 D-24 / D-25 / D-26: raised by T-121 (REJECTED) but re-measured by T-127 MERGED 5315d48 and T-110 / T-145 merged.
  Complete. Split: D-26 projection bands -> P-6 (a named CONC.BEAM blocker); soffits -> remaining.
- A9 D-48 / D-55: complete (T-153, T-157 merged). D-48 -> P-9.
- A11 D-01: complete (T-103 merged). Kept, remaining.

MISSING ROWS (blockers the Checker names on a closable line; draft each with its sheet search before sending):
- G1 (structural, CONC.COLUMN): CB5 line, GF C5 (35F) and C3 (365) and their necks where the annex ground slab (+0.25) meets
  the main ground slab (+0.95): the column / neck boundary is not printed (T-248 MERGED 567dc972, Checker 03:19: 1.2375 ..
  1.4300 m3 HELD, "designer item proposed", never filed). -> T-287.
- G2 (structural, CONC.STAIR_DOME): C-ST-3 the ST-01 winder turn MS1-T (5 risers on section A-A, 4 wedges on the plans, no
  winder outline or soffit) and the unprinted waist thickness per flight (ST-03 "thickness UNRESOLVED") (T-184, T-258). -> T-287.
- G3 (structural, CONC.STAIR_DOME): tower dome, rings and drums: architectural only, no structural detail (DOME-3; T-185
  MERGED 94e39ee6, element register DOME-B row). -> T-287.
- G4 (architect, floor area): the GF pantry doorway zone about 1.100 m2, carried "RFI" in T-240 WP2 (MERGED d07af773) with no
  question text on any register. -> T-286.

### 0.1 PRIORITY RFIs (each unlocks one complete BOQ line; Alsenan)

| P | Line unlocked (unit) | Rows to send together | Quantity now held / conflicting | Unlock evidence (Checker CLOSABLE LINES) | Ready |
|---|---|---|---|---|---|
| P-1 | Windows (aluminium), m2 and pcs | A3 part: D-53 W02 (one 6.33 m window or two with a pier) | W02 pcs 1 .. 2, no m2; line 76.256 m2 DRAWING-CONFIRMED on 27 + W17 9.870 (Q-76 A) | row 6: "Q-76, D-53"; Q-76 answered 23:53 | YES |
| P-2 | CONC.POOL, m3 | S11 part: pool access (steps / bench / ladder: none drawn) | pool steps; base + walls VERIFIED components | row 12: "pool steps" only | YES |
| P-3 | CONC.FOOTING, m3 | S3 (F10+F) + S2 (band C1 section and level where it crosses footings) + S15 part (SB3 / F3 strap soffit level) | F10+F 2.176 .. 2.275; SB3 0.0295 .. 0.2683; SB1 in F10+F 0 .. 0.385; 25 footings 64.304 VERIFIED | row 8: "F10 + F Q-31 C, band C1 Q-28 A, SB3 / SB1 ranges" (SB1 follows S3) | YES |
| P-4 | CONC.BLINDING, m3 | S15 (D-14, D-15) + S3 + S1 (formation, for the ground-beam blinding) + S2 (boundary-wall base blinding, via P-3) | D-14 0 .. 0.189; D-15 0 .. 0.913; F10+F 0.552 .. 0.590; boundary-wall base blinding UNMEASURED (export row); footing blinding 14.990 measured | row 10: "D-14, D-15, Q-21 C, F10 + F, Q-28 / S2" (Verifier 01:34) | YES, closes ONLY with P-3 (S2) |
| P-5 | CONC.GROUND, m3 | S8 (D-33, D-34, D-35) + S2 (boundary band, boundary-wall columns M4) | exterior 24 beams 11.930 UNSUPPORTED BASIS, HELD in the export; 17 tee runs, 13 title-basis runs, 9 annex runs | row 9: "D-33, D-34, D-35 annex, M4" | YES |
| P-6 | CONC.BEAM, m3 | S5 (D-02, D-27) + S6 (D-03 / D-04 / D-05 / D-28 east 1F ring) + A8 part D-26 (projection bands) | CONFLICT 7 runs drawn 5.4421 / scheduled 5.7665; HELD 3.228 .. 7.6685 + 5 runs | row 7: "D-27, D-02, D-26, D-04, D-05, Q-61 C(3) east 1F ring" | YES |
| P-7 | CONC.COLUMN, m3 (necks included) | S4 (D-16, D-63, D-66) + S7 (D-44) + A5 part D-39 (structural roof levels: 2F to +13.90, annex) + S1 (neck start) + G1 (CB5) | CONFLICT 15 = 8.034 .. 10.119; HELD 16 incl. 2F <= 3.155 and annex <= 2.2275; UNSUPPORTED BASIS 2F 3.528, annex 3.7125; necks >= 9.2568 | row 11 (D-65 not sent: drawing-confirmed absence) | NO: G1 row to draft |
| P-8 | CONC.STAIR_DOME, m3 | A6 (D-08 round stair, C-ST-4 MS1-L) + A7 part D-21 (2F maid-room dome) + G2 (C-ST-3, waists) + G3 (tower dome) | ST-03 0.948 UNSUPPORTED BASIS; round stair 2.089 unresolved; closable component 10.805 settled | row 13: "C-ST-3 / C-ST-4, unprinted waists, DOME-3, ST-02 curved part" | NO: G2, G3 rows to draft |
| P-9 | Floor area (internal), m2 | A9 part D-48 (garden band) + A6 part D-08 (ST-02 / under-stair F1 / F2) + G4 (pantry doorway zone) + A12 part D-10 (dressing finish) | under-stair 6.124; garden band 1.364; doorway zone 1.100 | row 2 | NO: G4 row to draft |

### 0.2 REMAINING unresolved questions (real, kept; none unlocks a complete line on its own)

Reinforcement (the rebar line also has internal blockers: lap lengths not printed, T-273; so no RFI alone closes it): S9, S10,
S11 part D-57 (bar population), S12. Blockwork (internal held pieces remain, T-274 / T-279): S14 tie beam (+ pit depth to the
LIFT SUPPLIER), S16, S17, A4, A5 annex datum part, A7 partitions part, A10. Ceilings / plaster / paint / soffits / finishes: A1,
A2, A5 build-up part, A7 dome openings part, A8 soffits (D-24, D-25), A12. Other: S13 (line to confirm), S18 document control
(stated UNCONFIRMED in the export), A3 main door / SX-01, A11 sea-side element, A9 D-55 level changes.

Main chat, 2026-10-24 23:55 UTC. SUPERSEDES CLARIFICATIONS_CONSULTANT_2026-10-23.md (its 12 rows are carried here with
their status). Source register: DESIGNER_CLARIFICATIONS.md (D-nn rows, each raised by a task that read the sheets named
there) and the owner answers that leave a designer item (Q-21, Q-28, Q-31). Owner rules (2026-10-23 / 2026-10-24): only
genuinely unresolved designer matters; nothing the drawings already answer; no previously answered owner decision
reopened; no structural design decision invented. The "Readings" column lists what the drawings themselves allow; it is
never a proposed design, and the designer may answer with something else. Until an answer arrives every affected quantity
stays HELD or CONFLICT, visible, never 0.

Drawing set as issued: architectural p7757_arch_sheet01 .. 12 (P7757.dxf), structural ST7757.pdf p.1 .. 16 ('ST7757 dxf.dxf'),
3 sanitary sheets. Sheet numbers below are those prints.

LEAD, before the owner sends: confirm for each row that the search column is complete (every relevant sheet read by a
merged, Checker-verified task) or move the row back to an investigation task. Rows marked SEARCH OPEN must not be sent yet.

## A. Structural (structural designer)

| # | Ref | Element / location | Drawing reference | Conflict or missing information | Quantity held | Readings the drawings allow | Search |
|---|---|---|---|---|---|---|---|
| S1 | Q-21 | Founding level of every footing; 28 necks | ST p.1 general note 1 (excavation not less than 1.50 m below the existing plot level); p.13 blinding / underlay (0.17 m build-up VERIFIED, T-206) | the note fixes a minimum excavation, not the footing underside or neck start level | necks 10.856 m3; excavation / backfill; column cores and starters (T-280 effect up to 74.381 kg) | footing underside at the 1.50 m formation + 0.17 build-up, or the 1.50 m is the footing underside (excavation deeper); the designer states the level | Q-21 C (owner) |
| S2 | Q-28 | Plot-perimeter band 91.94 m (21.45 m through 10 footings); boundary-wall columns | ST p.2 foundation plan (hatched 0.20 band); p.10 row B.W 20 x 60; p.14 TYPICAL BOUNDARY WALL (G.B 20 x 40, pads 130 x 80 x 30, spacing SEE ARCH PLAN); p.1 note 2 | which section the band is (B.W 20 x 60 or the typical 20 x 40), its level where it crosses the footings, and the boundary-column positions | band 8.459 m3 (owner A, provisional, not released) vs 11.033; boundary-wall bases C1 UNMEASURED | B.W 20 x 60 on the full band; typical G.B 20 x 40 plus pads; band stopped or continuous through footings at a different level | Q-28 (owner) |
| S3 | Q-31 / F10+F | South-east combined footing (tags F10 and F on one outline) | ST p.2 foundation plan; p.9 footing schedule (F10 280 x 140 x 50, F 90 x 80 x 30) | one outline carries two tags; outline 3.25 x 1.40 vs two schedule pads; no combined-footing note | 2.176 .. 2.275 m3 HELD; blinding 0.552 .. 0.590 m3 | two pads as scheduled; one combined footing to the drawn outline at the F10 depth | T-233, T-239 |
| S4 | D-16, D-66, D-63 | 15 columns whose plan outline and schedule section differ (C8; 13 columns; lift columns / necks on FF) | ST storey plans (outline, text, dimension chain) vs p.9 column schedule; foundation plan 20X50 / 25X100 vs schedule FOUNDATION 30 x 50 / 30 x 100 | two printed sources give different sections | CONC.COLUMN 8.034 .. 10.119 m3 CONFLICT (15 columns); lift 0.55 vs 0.75 m3 per m of height | plan outline or schedule section, column by column | T-217, T-256 (Checker own ST read) |
| S5 | D-02, D-27 (+ T-277) | Beams whose drawn width differs from the schedule (CB10, GF B29, CB2, B21, 1F B6, and the T-277 census when merged) | ST roof slab plans (two edge lines) vs p.10 / p.11 schedules | schedule width vs drawn width; no section cuts them | 5.022 vs 4.549 m3 (D-27) and CB10 0.744 / 0.893 m3 | schedule width or drawn width, beam by beam | T-110, T-226; T-277 READY |
| S6 | D-03, D-04, D-05, D-28 | GF CB3 vs "B3 (with stair)"; six unlabelled spans; west / SE / CB12 strips; east dome ring | ST GF and 1F roof slab plans; dome detail (ring 20 wide, depth AS PER ARCH) | two labels on one line; spans with no label; strips without section; ring without mark | each HELD with candidate volume (east ring 0.900 m3 at B4) | for each: the type and section | T-110 |
| S7 | D-44 | Beam B15 20 x 120 at the water tank | ST slab plan + p.10 schedule (agree on the size) | upstand or downstand not shown | 2F tank-column heights 3.00 .. 3.80 m, +0.160 m3 at the joint | upstand; downstand | 10-23 pack row 2 (send-ready) |
| S8 | D-35, D-33, D-34 | Exterior ground beams; loaded spans; p.13 section titles | ST p.13 ('FOLLOW ARCH.'; sections 'without concentrated load'; > 5 m / < 5 m / < 2.5 m) | exterior depth not printed; loaded spans have no section; length basis and title precedence not stated; < 2.5 m link not sized | 24 exterior beams 11.93 m3 (wrong-basis in the candidate, held in the export); 15 spans' bars; < 2.5 m links; 5.00 m span | for each: the depth / section / basis the designer states | T-138, T-242 |
| S9 | D-36, D-37, D-31, D-38 | Bar ends and links: ground beams, straps, five per-metre footings, SB2 row | ST p.8 note 9 (development 70 d tension / 40 d compression, zone not stated); p.9 footing schedule; p.10 SB2 row (plus an off-sheet SB2 insert in the DXF) | end zone and shape, hook / leg details, top-bar ends of F8 / F12 / F13 / F14 / FF, which SB2 row governs | ground-beam ends 383.00 .. 670.26 kg; straps 76.11 .. 133.20; SB2 127.96; footing top layers inside 2,742.51 .. 2,836.40 kg | the designer's detail or a stated length per end | T-136, T-138 |
| S10 | D-49, D-50, D-51, D-52 | Slab top bars over supports; GF-126 zone; 13 panels with no bars; tank slab | ST slab sheets note 2 ('one third of the span'); p.15 typical slab detail (0.30 max(L1, L2) / 0.25 L1); ST p.4 / 5 / 7 / 16 | two printed rules for the top-bar extent; zone not delimited; panels without bars; note 2 vs the tank's T&B mesh | 752.73 .. 1,931.52 kg (top over supports); 7.89 .. 19.55 kg; 13 panels HELD; tank 28.66 .. 70.61 kg | note 2 per side or whole bar; p.15 detail; the bars of each unprinted panel | T-152 |
| S11 | D-57, pool steps | Pool floor and walls; pool access | ST p.7 (two-zone pool R1 / R2, slope, step) vs owner Q-26 A flat floor 1.15 m; GF plan, ST p.7, sections (no step / ladder drawn) | which bar population the flat floor takes; access not drawn | pool steel R1 888.90 .. 927.54 / R2 615.34 .. 639.45 kg; CONC.POOL whole line | R1, R2 or another population; steps / bench / ladder and their drawing | 10-23 pack rows 3, 4 |
| S12 | D-46 | 3 planted columns | ST p.15 planted-column details | no schedule row or bar count | column steel unquantified (frozen route 172.56 kg from a duplicated row) | the bar count and links | T-148 |
| S13 | D-41 | Sunken slab panels (1F floor 19.3964 m2 in 5 panels, 2F 5.400 m2; lowered at full thickness, T-213) | ST slab plans mark the panels | the drop d is not printed | slab concrete UNAFFECTED (VERIFIED 60.2804 m3 for any d); step-edge concrete 0.000 DRAWING-CONFIRMED; HELD on d: CONC.BEAM top of the 2 shared beams 3.006 .. 3.036 x d m3, riser / beam-side formwork 41.451 x d m2, fill / screed 24.79 x d m3, WP upturn 41.451 x d m2, ceiling level, blockwork heights of 7.913 m of GF wall (7.913 x d m2) (Lead 2026-10-25 02:15 from Verifier 01:34 / 02:00) | the drop per panel (and whether the shared beams' tops drop with the panels) | T-139, T-213, T-288 |
| S14 | D-43 | GF lift-wall tie beam at 3.00 m (note 19); pit depth 'as per lift manufacturer' | ST p.8 note 19; p.14 lift details | size not printed; pit depth not printed | lift block walls 43.37 m2 gross HELD; tie-beam concrete; neck depth | the section; the pit depth or the lift data | T-143, T-227 (SEARCH OPEN until T-227 result confirmed) |
| S15 | D-14, D-15 | Blinding at the 8 plot-line footings; blinding under straps | ST p.13 (blinding 10 cm past each face; none drawn under straps) | projection past the plot line; straps not covered | 0.189 m3 and 0.913 m3 HELD | stop at the plot line or project; blinding under straps or not | T-100 |
| S16 | D-11 | Black block on the neighbour-side ground beams 'above and below, built from foundation level' | ST p.1 notes box, note 2 | how far 'above' reaches | 26.37 m GF wall + 31.17 m north fence, block type PROVISIONAL | to the GF slab only; the whole GF wall / fence | T-107 |
| S17 | D-12 | Walls that contain columns | ST p.8 recommendation 20 (built at column thickness) vs arch plans printing 0.15 / 0.20 | wall thickness where a column sits inside | block m3 on 19 rows 23.407 .. 31.737 m3 | column thickness; as drawn | T-143, T-226 |
| S18 | D-61 | Structural set issue | ST p.1-7 dated May 06, 2025; p.9-10, 13-16 May 06, 2026; p.11-12 no title block | which date is the issue, whether the beam schedules belong to it, revision marks | none held, but it defines the revision set every BOQ line is bound to (T-245) | the issue date and a revision per sheet | T-195 |
| S19 | T-149 (owner 2026-10-25) | Beam side reinforcement 'MIDDLE REINT.' / side bars | ST PDF p.10 Schedule of Simple Beams remarks: 2ø12/30cm (B7 .. B15, B17, B18, B20 .. B25, B28, B29), 2ø14/20cm (B19), 2ø16/20cm (B16, B26, B27); p.11 / p.12 continuous beams 'MIDDLE REINT. 2ø12/30cm' (CB1, CB3, CB6, CB7, CB8, CB11, CB12); p.8 note 21 (side bars 2 / 3 / 4 ø12 in beams deeper than 60 cm 'unless stated otherwise') | the notation does not state whether '2ø12/30cm' is two bars in all, or two bars per face at 30 cm vertical spacing; how note 21 and the remark combine | side bars HELD, at least 0.362 t on released members (2-bar minimum, T-149); not in the active calculation | the count per face and the vertical spacing the designer intends | T-149 (MERGED 4972ac5) | SEARCH: Lead to confirm |
| S20 | T-149 | Nested / multi-leg links | ST PDF p.10 link symbol with two nested links on B17, B19 .. B26 | the inner link's size, legs and position are not dimensioned | links HELD (T-149 lower / upper path 2.035 .. 2.199 t incl. nested reading); the active calculation counts one perimeter link only | inner-link dimensions and leg arrangement per beam | T-149 | SEARCH: Lead to confirm |
| S21 | T-149, T-191, D-36 / D-37 (extends S9 to superstructure beams) | Hooks, bends and bar-end anchorage of superstructure beams and links | ST p.8 note 9 (development 70 d tension / 40 d compression, written for starter bars 'اشاير'); p.11 / p.12 typical details (0.22 Ln support bars, first link 7.5 cm from the face); no hook or end detail for beam bars or links | whether note 9 governs beam bar ends / anchorage into supports and laps; end shape of bottom / top bars at end supports; link hook type and length | beam bar ends HELD 1.61 .. 2.82 t (40 d .. 70 d, T-149); link hooks unquantified | the anchorage / end detail of beam bars and the link closure detail | T-149, T-273 r2 | SEARCH: Lead to confirm |
| S22 | T-149 (finding 7, detail p.16) | Stair beams B3 '(With Stair)' (GF and 1F) and planted-column carrying beams B26 / B27 | ST p.16 TYPICAL DETAIL OF STAIR BEAM (cranked profile, no dimensions); p.15 BEAM CARRYING PLANTED COL. DETAIL (4 ø16 extra, length not dimensioned) | crank geometry of the stair beam; length of the planted-column extra bars | stair beams HELD_DEFINED 20.25 kg each (plan length lower bound); planted-column extra unquantified | the crank dimensions; the extra-bar length | T-149 | SEARCH: Lead to confirm |

## B. Architectural (architect)

| # | Ref | Element / location | Drawing reference | Conflict or missing information | Quantity held | Readings the drawings allow | Search |
|---|---|---|---|---|---|---|---|
| A1 | D-22, D-40, D-09, D-47 | Ceiling level per room, ceiling types, coves, drops, wet-room boards | no reflected ceiling plan or ceiling section in the set (D-62); arch sheet10 levels only | ceiling level per room; floor build-up per floor; board type in wet rooms; drop heights over 47.00 m of openings | drawing-derived plaster / paint heights PROVISIONAL / HELD (plaster bounded 531.8 .. 597.6 m2, paint 529.5 .. 595.0 m2); 14 wet-wall tile lines; wet-room ceiling board on 82.51 m2 | a reflected ceiling plan, or a level per room | T-112, T-128, T-147 |
| A2 | D-45, D-07 (D-62) | Window and door schedule | elevations / sections print sill and head for 9 openings only (W01, W03, W13, W14, W15, W17, W18, W26, D01); one printed door height (main entrance 2.00 x 2.50) | sill, head, arch rise of 20 windows and 3 arches; door heights and types | plaster / paint nets 104.1 m2 of range; window m2 HELD; door heights ASSUMED 2.20 m (owner Q-55 fallback) | a door / window schedule | T-144, T-091 |
| A3 | D-53 | W02 (6.33 m), main entrance door, pool-court opening SX-01 | plans: W02 one window, main door 2.00 x 2.50 double, SX-01 4.521 m straight head; renders differ (two windows with a pier; single leaf; round arch over a low wall) | built intent (renders are design intent, never a quantity) | W02 pcs 1 .. 2; main door HELD (5.000 m2 candidate); SX-01 HELD | as drawn; as rendered | T-161 |
| A4 | D-18, D-19 | W03 head +5.30 under beam B8 (soffit at most +4.75); W17 crown +9.20 against CB12 | arch elevations / sections vs ST GF / 1F roof slab plans | the opening head is above the beam soffit drawn on the same line | W03 and W17 CONFLICT (window and the wall above) | beam moved or upturned; a lower head | T-112 |
| A5 | D-06, D-17, D-39 | Roof datums and build-up (annex +4.30; GF terraces +5.50; 1F roofs +9.70; main roof +13.90) | section B-B (+4.30 on one ~0.23 band), section A-A (+13.90 on the roof band), plans (finished levels), sanitary (1 % falls) | structural slab-top level of each roof; roof build-up (falls screed, insulation, protection) | annex walls 83.82 m2 black + 29.30 m2 white HELD; 17 rooms under roofs PROVISIONAL-DATUM; roof finishes | the structural levels and the build-up | T-112, T-128 |
| A6 | D-08, C-ST-4 | Round reception stair (no section); main stair MS1-L riser count | arch sheet03 / 04 plans; sections A-A / B-B do not cut the round stair; structural stair linework vs arch plan / section for MS1-L | riser count, landing levels, curved geometry; MS1-L count and landing edge as built | round stair curved part HELD (2.089 unresolved), straight flights 0.469 m3 to be checked; staircase system 6.648 m3 PARTIALLY VERIFIED (MS1-L HELD); ST-03 0.948 m3 held in the export (convention riser) | a section of the round stair; the MS1-L count | T-111, T-184, T-189, T-192 |
| A7 | D-20, D-21, D-42 | Dome openings on the 1F roof; 2F maid-room dome; 1F partitions under the openings (10.67 m) | arch plans / sections vs ST 1F roof slab (flat, no ring at the 2F maid room) | ceiling / glazing under each opening; is there a dome at the 2F maid room; the top of the partitions | HELD; 2F dome CONFLICT; 10.67 m of block HELD with no candidate height | as drawn on each discipline | T-112, T-143 |
| A8 | D-24, D-25, D-26 | Soffits over outside air (porch 19.181, side passage 5.640, pool court 12.834, roof edges 6.791 m2); two wet floors over outside air; roof-edge bands and projections (البروزات) | no plan / section / elevation / detail draws a soffit finish or insulation; slab note 1 (contractor matches projection details to the arch drawings) | soffit finish and build-up; insulation / waterproofing under the two wet floors; depth and material of each projection | soffit areas CALCULATED, finish HELD; projection plan areas listed, no m3 | the finish / build-up per place; the section of each projection | T-121, T-110 |
| A9 | D-48, D-55 | GF garden band (13.986 m2) and side passage (5.64 m2); six outdoor openings with a 0.15 m level change (7.30 m of width) | arch GF plan | band drawn enclosed and roofed but labelled garden; passage without door / glazing; level changes without step / sill / ramp drawn | classification and finish HELD; floor-area garden band 1.364 m2 in the floor line | open / roofed / enclosed, planter or paved; step, sloped sill or ramp | T-153, T-157 |
| A10 | D-58, D-64 | Door D-GF-06 head; opening P-1F-01 head level | arch plan / census (rectangular, height not printed) vs renders (round arch); P-1F-01: no head on any sheet | arched head and its levels; the head level | D-GF-06 arched increment HELD; 1F-W14 + W15 nets 10.971 .. 16.223 m2, masonry above 0 .. 4.992 m2 | rectangular / arched; the head level | T-161, T-222 |
| A11 | D-01 | Sea-side boundary element 7.00 m (6.00 solid + 1.00 gate) | arch GF plan (drawn 0.20); the fence drawing does not show it | material, height, structure, foundation, finishes, gate | visible HELD line (owner Q-63 C) | the element's drawing | T-103 |
| A12 | D-54, D-59, D-62 | Railings / balustrades / shutters; nine small squares on two elevations; sheets not in the set | renders vs drawings (shutters only at W14); SE / fence elevations; the issued set has no site plan, top-roof plan, finishes schedule, specification, wet-room / kitchen or stair details, MEP | schedules and sheets not issued | railings / shutters: no quantity (not drawn); squares UNKNOWN; finishes, tile sizes, MEP out of scope until issued | issue the sheets, or confirm they do not exist | T-161, T-164, T-194, T-195 |

## C. Carried from the 2026-10-23 pack

Rows 1 (D-16), 2 (D-44), 3 (pool steps), 4 (D-57), 5 (C-ST-4), 6 (D-63), 10 (D-12), 11 (D-02 / D-27) are in S4, S7, S11,
A6, S4, S17 and S5 above. Row 7 (D-43) is S14 (SEARCH OPEN). Row 8 (D-06 / D-17) is A5. Row 9 is narrowed to D-64's head
level only (A10; P-GF-05 / D-60 resolved from the drawing, T-222). Row 12 (D-65) is NOT sent: the Checker confirmed from the
drawings that the five upper columns are not drawn (DRAWING-CONFIRMED absence); it is re-opened only if the designer says
they exist.

## D. Not included (resolved from the drawings, owner decisions, or no quantity effect)

D-13, D-23, D-29 (stair-foot strips: the V3.0.14 floor line settles the 1F living range; marble in every reading, 0 m2 added);
D-30 (no quantity effect); D-32 (resolved from the drawing, T-233); D-56 (drawn stair governs; an owner-preference deviation,
not a designer conflict, owner S-8); D-60 (resolved, T-222); D-65 (drawing-confirmed absence). Answered owner decisions
(Q-60, Q-48, Q-52, Q-50, Q-55, Q-76 and the rest) are not reopened; only the designer facts they leave open appear above.
