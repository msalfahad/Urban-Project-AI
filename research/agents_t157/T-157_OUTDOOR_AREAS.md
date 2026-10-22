# T-157: Alsenan outdoor areas: inside / outside from the sections, and one outdoor finish line per area (NO REPO CODE)

Worker 2 (lane A), 2026-10-22 01:45-02:40 UTC. Gate 1 (no area lost, wet / dry and inside / outside right). Development
villa, not an accuracy claim. Nothing is wired and no released quantity changes: a checked piece for the consolidated
ARCH_TAKEOFF_V3.0 candidate (lane I). No engine module, rule, knowledge file, test or key map changed. No client name,
coordinate, image or drawing content is committed; sheets are cited by Drive title and page.

Self-check of this run: setup (agent_env), codemap check (stale: none), t061 (20 passed), freeze (0 differing): all PASS.

Read this run (Drive "Alsenan chalet project", copies in the git-excluded private folder): P7757_DXF_COMPRESSED.zip
(architectural DXF), p7757_arch_sheet03 (GF plan), p7757_arch_sheet04 (1F plan), Pages_05-06 (2F plan, SE elevation),
Pages_07-08 (SW, NW elevations), p7757_arch_sheet09 (NE elevation), p7757_arch_sheet10 (section A-A), Pages_11-12 p.11
(section B-B) and p.12 (fence). Freelancer: FIN workbook, sheet "رخام+حوش" rows 11-41 and the cover rows 22-26
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json).

Method: the GF plan polygonized inside the inner faces of the plot boundary walls (T-147 rooms.py, same call as T-153)
gives the same single open face 177.1154 m2 as T-153 (177.115); it is cut along drawn lines only (1F slab edge, stair
edges, landing edge, house north face line), every piece re-added. Hand route: printed chains on sheets 03 / 04.

Rules: owner rule OUTDOOR_FLOORS 2026-10-21 (answers OQ-04) with its additions 20:45 (sides never interlock; north side
walk owner manual 1.50 x 15.97) and decisions 23:20 (court interlock over the renders; porch at court level, own line,
material later; pool deck held); UP-STAIR-001 (marble on tread, riser AND landing of every stair assembly, external steps
included), UP-STAIR-002 (drawn geometry governs), UP-STAIR-003 / -006 (visible riser = rise - 0.030), owner stair rule
S-1 / S-2 (calculator as a check), Q-67 A (side passage outside, condition met), UP-SPACE-001 (a label alone never
decides), WORKFLOW_CONTROLS section 5 statuses, UP-QTY-STATUS-001 (held never 0).

## 1. Result in engineering terms (m2; Alsenan GF; freelancer = FIN workbook)

| Line | Classification (evidence) | Engine-side hand (drawn) | Finish / status | Freelancer |
|---|---|---|---|---|
| West court, open part | OUTSIDE: open sky (section B-B p.11: court +0.15 between the annex roof +4.30 and the house; sheet04 nothing over it) | **119.542** | INTERLOCK, ASSUMED — OWNER-APPROVED (owner choice; renders show stone: "owner choice, differs from render") | in yard 151.80 |
| Covered porch at court level | OUTSIDE_COVERED: B-B p.11 court +0.15 runs under the 1F slab (printed clear 5.35 to +5.50), open to the court, no wall / door / glazing | **10.680** (drawn 10.679) = 2.00 x 4.30 + 1.20 x 1.50 + 1.40 x 0.20 | area DRAWING-CONFIRMED, **material HELD** (owner: wood / ceramic / marble) | in yard 151.80 |
| Entrance steps E1, treads | OUTSIDE_COVERED; 4 treads drawn 0.30 x 2.80 (printed 280), 5 risers in B-B | **3.360** | MARBLE (owner rule + UP-STAIR-001) | "5 steps x 2.80" |
| Entrance steps E1, visible risers | rise 1.00 - 0.15 = 0.85 printed levels / 5 drawn = 0.170; - 0.030 build-up | **1.960** = 5 x 0.140 x 2.80 | MARBLE; **FLAG** drawn riser 0.170 > 0.16 (owner calculator: 6 risers of 0.142 needed; drawing governs, S-1) | (same row) |
| Entrance top landing (+1.00, outside the main door, under the 1F) | OUTSIDE_COVERED; printed 140 x 370 on sheet03 | **5.180** (drawn 5.179) | MARBLE by UP-STAIR-001 (landing of an external stair) | landing 5.10 (+0.08, +1.5 %) |
| North side walk | OUTSIDE: section A-A sheet10 strip +0.15 open to the sky; sheet04 prints 150 with nothing over it | **21.021** (drawn 21.014) = 1.30 x 16.17 | PORCELAIN / CERAMIC (side, part of the house), ASSUMED — OWNER-APPROVED | in yard 151.80 |
| North side walk, owner manual method (kept beside) | same | 23.955 = 1.50 x 15.97 | same | - |
| Pool court deck | OUTSIDE (T-127 / Q-68) | 7.939 (was 7.605: + the 0.334 mouth band, section 3) | HELD (owner: pool deck undecided) | not in his yard |
| Side passage | OUTSIDE_COVERED (Q-67 A, condition met) | 5.640 = 1.20 x 4.70 | PORCELAIN / CERAMIC (side) | not in his yard |
| GF garden band | HELD_CONFLICT, physically INSIDE (section 4) | 13.986 (T-153) | HELD (designer D-48) | in his reception row |
| Thresholds at 6 outdoor openings (level change, no step drawn) | outside | 7.30 lm | HELD (proposal P-3) | "gate steps" 7.70 lm, 6 items |

**Against the freelancer's yard** ("ارضيات الحوش" 151.80 m2, one row, no dimensions): open court 119.542 + porch 10.679
+ north side walk 21.014 = **151.234 vs 151.80, -0.566 m2 (-0.37 %)**. His entrance-marble block holds the steps (5 x
2.80) and the landing (5.10) apart, and his yard has neither the pool deck nor the side passage. The T-153 difference
"courts 167.714 vs 151.80, +15.91 (+10.5 %)" is therefore fully explained, term by term: 167.714 - steps 3.359 - landing
5.179 - deck 7.605 - mouth band 0.334 (moved to the deck) = 151.237. Verdict proposal: **AGREE / RULE_DIFFERENCE** (same
scope within 0.4 %; the remaining 0.57 m2 is not traceable in a single-row entry). His perimeter 81.32 m ("نعلات الحوش")
is not reproduced by this composition (outline 84.13 m); the outline of the open court + side walk alone is 81.33 m:
UNRESOLVED (skirting is not this task's line).

Under the new lines the yard paving no longer is one number: interlock 119.542, porcelain / ceramic 21.021 + 5.640 =
26.661, porch 10.680 material held, deck 7.939 held, outside marble 3.360 + 1.960 + 5.180 = 10.500. No finish quantity
is released (WORKFLOW_CONTROLS: only the owner releases; the Checker verifies first).

## 2. The north side walk: owner manual 23.955 vs drawing 21.021, term by term (both kept)

| Term | m2 | Evidence |
|---|---|---|
| Owner manual 1.50 x 15.97 | 23.955 | printed 1500 and 15970 |
| - width: the printed 1500 runs from the house north face to the **outer** face of the 0.20 north boundary wall (DXF dimension end points on the wall's outer line; sheet04 prints the same 150) | -3.194 | 0.20 x 15.97 |
| + length: the printed 15970 starts at the inner face of the 0.20 north-west corner column of the stair block; the walk starts at its outer face, where the west court ends | +0.260 | 0.20 x 1.30 |
| = drawing-derived floor area 1.30 x 16.17 | **21.021** | Checker 2026-10-21: 21.021 (confirmed) |
| polygon on the DXF | 21.014 | -0.007 (-0.03 %): wall-line buffers at the window reveals |
| T-153 21.348 | +0.327 | the 1.30 x 0.20-0.25 band at the pool-court mouth, under a 0.20 element of the 1F (sheet04: the 1F north wall line runs on to the east boundary; GF draws it as two thin lines + the column) south of the house north-face line: it is the pool court's mouth, not the walk. Moved to the deck; the T-153 / Checker split is now settled at the house north-face line |

The 1.28 x 0.29 outline the Checker found inside the strip (0.37 m2) is **not an object**: it is the leader of the
"mecvent" label (open 3-vertex polyline on the outline layer from the W.C. vent circle inside the house to the label,
closed only by the wall line). The same symbol appears twice on the annex W.C.s, where the leader runs over the south
boundary out of the plot, and the PDF prints "تهوية صناعية" (mechanical ventilation) at all three. No deduction; the
walk stays 21.021.

Verdict proposal: RULE_DIFFERENCE (the manual method measures to the plot line incl. the boundary-wall thickness; the
floor finish is laid to the wall faces). The owner's method stays beside the drawing line, never replaced.

## 3. The four spaces of the task: classification and surfaces

| Space | Floor | Soffit over it | Walls facing it (lengths; heights and finishes are the facade lines, T-159) | Class |
|---|---|---|---|---|
| West court (open part) | 119.542 interlock | none (open sky) | boundary walls 14.80 (north) + 5.60 (west, less the 2.50 street gate); annex north faces and house west face | OUTSIDE |
| Covered porch + E1 + landing | 10.680 + 3.360 + 5.180 = 19.220 (= 4.60 x 4.30 - the 0.40 x 1.40 wall stub) | 1F slab, T-121 soffit 19.181 (verifier 19.198): +0.039 to this floor envelope (T-121 took 4.096 to the beam faces) | house west face behind the landing 3.70 (main door 2.00), pantry north face, the 0.40 wall stub | OUTSIDE_COVERED |
| North side walk | 21.021 porcelain / ceramic | none (section A-A: open sky) | boundary wall 16.17 + east 0.30 (sea-side gate 1.00); house north face 16.17 (stair door 0.90, windows) | OUTSIDE |
| Side passage | 5.640 porcelain / ceramic | 5.640 (Q-67 A exterior soffit, T-121 / Q-68) | 9.40 m of passage walls (Q-67) | OUTSIDE_COVERED |
| Garden band | 13.986 HELD | interior ceiling | south facade wall with 2 windows | HELD_CONFLICT |

Re-adds (all to 0.01 m2, `t157_outdoor.py --check`): west court 119.542 + 10.679 + 3.359 + 5.179 = 138.759 vs T-153
138.761; open face 138.759 + 21.014 + 17.341 = 177.115 vs T-153 177.115; north strip + pool court 38.356 vs T-153 21.348
+ 17.007 = 38.355; deck 17.341 - pool to its outer shell 9.402 = 7.939. Second route (T-153 hand): west court 14.80 x 9.90
- 4.20 x 1.80 + corner = 138.96 vs 138.76 (-0.20, column notches).

## 4. Garden band (defect B9): what the sections say

Section A-A (sheet10) cuts the band (its cut line crosses the 10.82 m band): the GF floor +1.00 runs unbroken to the
inner face of the south facade wall, which carries two windows; the +5.50 slab is over it; no curb, soil, planter edge
or level change is drawn. Sheet04 draws the +5.50 roof strip, printed 150 wide, outside the 1F south wall exactly over
the band. Only the plan word GARDEN / حديقة says otherwise. So: physically INSIDE (enclosed and roofed), use HELD_CONFLICT
under UP-SPACE-001 until the designer answers D-48 (planter or porcelain floor). New evidence for D-48: the section
draws it as floor; the freelancer floors it in his reception row. Area unchanged 13.986.

## 5. Outside steps and thresholds

- E1 (the only drawn outside stair): 5 risers / 4 treads 0.30 x 2.80, +0.15 -> +1.00 (printed levels), landing 1.40 x 3.70.
  Tread 3.360, visible riser 1.960, landing 5.180, 4 tread pieces, 5 riser pieces: MARBLE. FLAG for the Checker: drawn
  riser 0.170 > 0.16 (owner calculator check: 6 risers of 0.1417 and 1.50 m going vs the 1.20 m drawn); the drawing
  governs (S-1), so this is a finding, not a change.
- Six outdoor openings have a printed level change but **no step drawn**: street gate 2.50 (±0.00 -> +0.15), sea-side
  gate 1.00 (±0.00 -> +0.15), dewaneya door 1.00, driver door 0.90, annex lobby door off the passage 1.00 (+0.15 ->
  +0.30), stair-hall door to the north walk 0.90 (+0.30 -> +0.15): 7.30 lm. The freelancer prices "درج البوابات" 6 items,
  7.70 lm (1.3 / 2.5 / 1.0 / 1.0 / 0.9 / 1.0): same count, -0.40 lm. HELD: UP-STAIR-002 takes stair geometry from the
  drawing, none is drawn, and no rule says whether a 0.15 m threshold is a marble step (owner stair rule S-1 applies to an
  undrawn stair, but whether these are stairs at all is not stated). Proposal P-3 below.

## 6. Who is right (proposals for the Checker)

- Yard 151.234 vs 151.80: AGREE / RULE_DIFFERENCE (-0.37 %; his entrance steps and landing in his marble block).
- Entrance landing 5.180 vs 5.10: ENGINE_RIGHT (printed 1.40 x 3.70 = 5.18).
- North side walk 21.021 vs owner manual 23.955: RULE_DIFFERENCE (boundary-wall thickness and corner column), both kept.
- Gate / door thresholds 7.30 vs 7.70 lm: UNRESOLVED (no step drawn; P-3).
- Garden band: UNRESOLVED (designer D-48), section A-A evidence added.

## 7. Held, missing and proposals for the Lead (no owner question added by this run)

- Porch material (owner deciding), pool deck (owner), garden band (designer D-48).
- **P-3 (thresholds)**: six outdoor openings change level by 0.15 m with no step drawn (7.30 lm). Options: (A) one marble
  riser + threshold per opening, measured from the opening width (the freelancer's reading); (B) no step line (a ramped or
  flush threshold detail by the designer); (C) designer list. Blocks 7.30 lm of outside marble. Lead: fold into the owner
  package if it is worth his time.
- Not done here: wall and soffit FINISHES of the outdoor spaces (facade lines, T-159 / Q-68), skirting of the yard
  (his 81.32 m), boundary-wall heights (sheet p.12 fence elevation).

Files: `AREAS_T157.csv` (one row per outdoor line + 6 threshold rows: classification, sheet evidence, drawn and hand m2,
formula, finish, status, rule, freelancer row), `summary.json`, `t157_outdoor.py` (method + Alsenan ledger;
`--check`: synthetic chalet NOT Alsenan (open court with a planter, covered porch with outside steps, roofed side passage,
side strip, enclosed GARDEN band) in m, mm, rotated 37 deg, mirrored and mirrored + rotated in mm, plus missing porch
level (HELD, area kept), unknown project type, villa court, no roof evidence, step checks incl. the 4.48 m -> 28 risers
case: **133 of 133 PASS**, and the Alsenan re-adds above).
