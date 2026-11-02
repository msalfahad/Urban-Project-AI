# T-447: the stair-room skirting faces T-441 left HELD, and its three findings (development villa; method every villa)

Worker 3 (lane I, taking the lowest-gate lane A TODO while lane I had none), 2026-11-01. Research only:
`research/agents_t447/*`, `tests/t447_stair_room_held_faces/*`; no engine, rule, knowledge, method, registry or candidate
file touched; no candidate or released quantity moves (lane I proposals in s.7). ERS applied: s.2.1 element first, s.2.2
evidence (drawing before rule before reference), s.2.4 reconciliation in units, s.4 rule + test, s.7 lesson.
Rules: UP-SKIRT-001 1.4.0 (dry-room wall and column faces at floor level), URBAN-SKIRTING-OPENING-METHOD v1 (doorless
jambs: five conditions), UP-CER-003, R-T410-1, R-T441-1 .. 4 (reused by import, not edited), owner Q-06 (a) (basin-only
hand-wash spaces are WET: full-height wall porcelain, marble threshold), Q-46 A (section A-A riser counts), Q-70 A, defect
B12 (L-18: skirting along void / railing edges). No image, client name or drawing text copied.

## 0. What was read

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55), decoded into `.work/private` only; 36 handles re-read, 2 level-mark blocks, 3 zone sweeps on layers 1 / 5 / S-COL.BON / 4 / W (EXTRACT_T447.json) | every face, band, nosing / riser line, level point, wall gap |
| Drive p7757_arch_sheet03.pdf (GF plan) read as an image | the divider band drawn as a thin double line (not a poched wall), the diagonal / single lines in the south-west box, the +0.30 mark at the strip |
| Drive p7757_arch_sheet10.pdf (section A-A) read as an image, rotated | the divider at +1.00 (posts, top and mid rail, MS1-L visible behind), the flat +1.00 floor from the south wall to MS1-L's first riser, D1 and the +0.30 lobby under the +3.50 landing |
| Candidate of record ARCH_TAKEOFF_V3.0.40, own run (research/agents_t167/v304_run.py + research/agents_t430/v3040_run.py on P7757.dxf + "ST7757 dxf.dxf" 9f9d1179) | the lines the proposals touch (summary.json `candidate_lines`) |
| Merged ledgers, cited not re-derived: T-441 (face tables, closures), T-418 (floor parts), T-410 r2 (stair side table and stations), T-393 (RL-07 / RL-08), T-409 F-T409-1 and T-208 (OP-020 threshold strip), T-250 (face walk), T-292 / T-349 (face-to-line ledgers), T-106 (freelancer skirting trace) | see each row |

## 1. Physical elements (ERS s.2.1)

A room skirting is a strip fixed to a vertical finished face (wall or column) at the floor level of a floored space. It is
not fixed to a balustrade (posts and rails) or along an open edge, not across or into a door, and into a doorless opening's
reveal only when the owner method's five conditions hold. The four held items are therefore questions of PHYSICAL
CONSTRUCTION first: is the GF divider a wall, an upstand or a balustrade; whose floor and wall finish occupy the OP-020
reveal; is there a face on the back lobby's west side; and what the freelancer's extra 0.700 lm physically is.

## 2. Results, item by item

### 2.1 GF divider band faces (T-441 HELD 2.200 lm at the cut outline / 3.400 lm on the T-418 outline) -> NOT_APPLICABLE

| Evidence | Reading |
|---|---|
| Plan, P7757.dxf | the band 155 / 157 / 4A4 is on layer 5 (seen below the cut), not a cut wall on layer 1; inside it the rail pair 151 / 47F (x 1.20 / 1.30) with the rail end 156 at y 1.10; the dimension chain across the flights reads 1200 / 100 / 1200 (stair widths to the rail lines, a 0.10 rail between) |
| Plan, sheet 3 | the band is a thin double-line strip, not poched like the cut walls |
| Section A-A, sheet 10 | at +1.00 between the post at the MS1-L foot (scale ~y 1.2) and the D1 top post (y 2.95): a horizontal TOP RAIL (~0.9 m) and a MID RAIL (~0.37 m) on posts; MS1-L's first steps and its soffit are drawn VISIBLE between the floor and the lowest rail and between the rails; the rails then descend along D1 to +0.30 |
| Merged | T-410 MS1-L east side OPEN 'not skirted' (RL-07 MS1-L); T-393 RL-07 / RL-08 balustrades |

The divider is a BALUSTRADE on the edge of the MS1-L flight: no solid face stands on the hall floor along it. East face
1.900, west face 0.100 and end 0.200 -> **NOT_APPLICABLE** (R-T447-1; UP-SKIRT-001 wall / column faces only; B12). Status:
DRAWING-CONFIRMED (plan + section). Hall skirting stays **4.650 lm DRAWING-CONFIRMED**, nothing held on the band.

Railing note for the railing owner (no quantity here): section A-A draws the horizontal +1.00 rails between the MS1-L foot
post and the D1 top post (about 1.75 m by scale, not printed); T-393 lists RL-08 (D1, 1.042) and RL-07 MS1-L (inclined);
whether this horizontal run is in either is not checked here.

### 2.2 Finding (a): the divider zone y 0.45 .. 1.05 (T-418 SOLID 0.120 m2) -> FLOOR +1.00, +0.120 m2

| Evidence | Reading |
|---|---|
| Sweep `divider_zone_y045_105` (x 1.15 .. 1.35, y 0.45 .. 1.05) | no closed outline, no layer-1 wall, no column: only the single layer-5 line 2C8 (x 1.20, y 0 .. 1.05) and the walking-line start tick 2CA (y 0.525, x 0.575 .. 1.47) with its two short marks 2CB / 2CC |
| Hidden lines | 47C / 499 / 47E (layer 2) are the band ABOVE (1F) from y 0.45; 47D / 49A the rail end above at y 0.50 |
| Band at the cut | closes at y 1.05 (155 visible) |
| Section A-A | the +1.00 floor is flat from the south wall to MS1-L's first riser (no step line, no upstand); the first balustrade post stands at the band end |
| South-west box (2F1D / 2F1E diagonal, 2C8 / 2C9) | read: NOT a level change. Section A-A shows no step south of MS1-L's first riser, and the riser counts close (MS1-L 10 + 5 winders = 15 risers of 0.1667 m from +1.00 to the printed +3.50, T-434 / Q-46 A); the lines' meaning (finish border or drafting line) is not printed: no quantity hangs on it |

A walking line does not cross a solid upstand: the zone is open floor at +1.00 (R-T447-3). T-418's hall floor part is
**4.805 -> 4.925 m2 (+0.120 m2, +2.50 %)**; its SOLID divider 0.680 -> 0.560 m2; the stair room face 12.475 m2 still re-adds.
No skirting face is created (the zone is open on both sides). Status: DRAWING-CONFIRMED (plan sweep + section A-A).

### 2.3 OP-020 reveal jambs (T-441 HELD 2 x 0.200 = 0.400 lm) -> NOT_APPLICABLE by the owner method

OP-020 is a doorless 0.900 m opening in the 0.200 east wall (21C / 21B, wall end 4AA, column 2F93; head lines 33C / 33D
hidden) from the hall into GF-RD36087, a basin-only hand-wash niche. URBAN-SKIRTING-OPENING-METHOD v1 includes doorless
jambs only when all five conditions hold (R-T447-2):

| Condition | Value | Evidence |
|---|---|---|
| no door | TRUE | no door block, no leaf (T-198 P-GF-01) |
| real vertical jamb | TRUE | column 2F93 north face, wall end 4AA |
| skirting-eligible side | TRUE | dry hall side |
| floor finish reaches the jamb | **FALSE** | the reveal floor 0.900 x 0.200 is the niche's MARBLE threshold (owner Q-06 (a); T-409 F-T409-1 P-GF-01 = OP-020 0.180 m2, merged); the hall porcelain stops on the hall face x 2.5 |
| not a full-wall-tile room | **FALSE** | the opening belongs to GF-RD36087 = WET, full-height wall porcelain (owner Q-06 (a); T-208 / T-296 GF-11) |

-> **NOT_APPLICABLE** (status ASSUMED — OWNER-APPROVED, Q-06 (a); geometry DRAWING-CONFIRMED). The reveal's two 0.200 m
faces are wall-porcelain returns of the wet niche: cross-trade item for the wall-tile owner (are the 2 x 0.200 x full height
reveal returns in the GF-11 wall tile line? not checked here). No designer RFI is needed for the skirting.

### 2.4 GF back lobby west side (T-441 UNKNOWN, candidate 1.150 lm on x 1.35)

| Evidence | Reading |
|---|---|
| Sweep `strip_GF_ST_CN` (x 1.15 .. 1.35, y 3.85 .. 5.00) | nothing on layers 1 / 5 / S-COL.BON / 4 / W |
| Level mark 4AB ('+0.30') | its point (circle centre) lies INSIDE the strip, 0.039 m west of x 1.35 |
| Band | ends at y 3.85 (4A4, cap 4A6); the rail 47F ends at 3.85 |
| Cut plane | MS1-L treads up to +2.667 are drawn solid, the MS1-T winders hidden: the plan cut is between them, so a wall enclosing the space under the winders (from +0.30 to the winder soffit, about +2.4 by the section) would be cut and drawn on layer 1: none is |
| Sweep `under_winders_x0_115` | no wall, step or column inside (see summary.json) |

So: (i) the 'face on x 1.35' alternative is REFUTED: the lobby side x 1.35 has **no face**; (ii) the T-418 strip GF-ST-CN
(0.200 x 1.150, HELD 0 .. 0.230 m2 UNREAD) is **floor at +0.30** (level point inside, nothing drawn): lobby floor part
**1.3225 -> 1.5525 m2 (+0.230)**, and its north face on wall 2AB / 26E (x 1.15 .. 1.35) joins the lobby skirting:
**1.400 -> 1.600 lm (+0.200) DRAWING-CONFIRMED** (it is T-441's closure item 'GF-ST-CN north 0.200'; T-410 MS1-T north
x 0 .. 1.15 lies at the winder levels +2.667 .. +3.50: no overlap, level-aware test); (iii) west of x 1.15, under the
winders, nothing is drawn and no level is printed: **UNKNOWN**, blank. If the +0.30 floor continues there, its faces are
west wall 297 (y 3.95 .. 5.00) 1.050 + north wall 2AB / 26E (x 0 .. 1.15) 1.150 = candidate **2.200 lm**, up to
**3.450 lm** with the OP-022 jamb zone (y 3.85 .. 3.95, 0.100) and a face under the MS1-L end (y 3.85, 1.150) if the +1.00
slab ends there. Only the designer can say: RFI c (s.6).

### 2.5 Finding (b): the 2F corridor residual 0.700 lm (T-441 UNRESOLVED) -> traced, RULE_DIFFERENCE

His row: 13.60 lm (gross perimeter, no dimensions in the row). Constructions from drawn lines only (R-T447-4):

| Construction | Outline (x from the arrival's west wall, heights from the south wall) | Perimeter | Area | Reproduces 13.60? |
|---|---|---|---|---|
| T-441 outline (arrival 2.5 x 1.95 + lobby 2.0 x 1.25) | x 0 .. 2.5: 1.95; 2.5 .. 4.5: 1.25 | 12.900 | 7.375 | no |
| the same over the MS2-U top going (east lane x 1.35 .. 2.5 to the top nosing 1386 at y 2.30) | 0 .. 1.35: 1.95; 1.35 .. 2.5: 2.30; 2.5 .. 4.5: 1.25 | **13.600** | 7.7775 | **yes (exact)** |

The 0.700 = the two 0.350 sides of the strip between y 1.95 and the MS2-U top nosing 1386 (y 2.30; riser 1385 at 2.25, up
direction south):
- east 0.350 on the lift wall 129A (y 1.95 .. 2.30): a real face, but on the flight's TOP GOING (12 risers per section A-A,
  Q-46 A; the plan draws 11 nosings, the 12th riser is the arrival edge at 1.95): T-410 MS2-U.E owns it from s 0 (the top
  riser) over 3.300 = 11 x 0.30 (= the printed 3300). Same physical base counted once on our side as STAIR skirting
  (B7-07 / B7-08): **RULE_DIFFERENCE (ownership / boundary), not an omission**;
- west 0.350 along the well band 1358 / 1359 (RL-07 MS2-U): no face: **RULE_DIFFERENCE** (guard edge, B12).
His area 7.70 m2 vs this outline 7.7775 m2: -0.0775 m2 UNRESOLVED (area, not this task's lm; recorded for the floor owner).

Engine vs freelancer, 2F corridor skirting: his 13.60 vs ours 7.500 lm = -6.100 lm (-44.85 %) = openings he does not deduct
2.900 (RULE_DIFFERENCE, UP-CER-003) + arrival north edge with no face 2.500 (RULE_DIFFERENCE, R-T410-1 / B12) + top-going
strip 0.700 (0.350 stair-side ownership + 0.350 guard edge, both RULE_DIFFERENCE) = 6.100, **residual 0.000**. The
percentage is not an accuracy figure: every component is an owner-rule difference.

### 2.6 Finding (c): T-250 2F-W00 '128A 0.43, drawn 0.600' -> ATTRIBUTION, net +0.006 m (sampling)

T-250 walks the engine room 2F-01 (x 0 .. 4.5, y 0 .. 1.25). Its 2F-W00 face = the wall run x 2.7 .. 4.5 (1.800, its
WALL_SIDE_CLOSURE row) + 0.031 m past the run end onto column 2F72 = 1.831 (handles 128A 0.43 = 0.400 on the run + 0.031;
1289 0.40; gap 0.99); the rest of the column's south face sits in the room's off-line COLUMN row (0.175, sampled). 128A as
drawn = 0.600 = column 2F72 face 0.200 + wall 0.400. North side: T-250 1.831 + 0.175 = 2.006 vs drawn 0.400 + 1.000 + 0.600
= 2.000: **+0.006 m**.

Lines carrying the figure: the 2F stair hall wall finishes L-ae0cdd794cc5fdbe0c29 (FIN.PLASTER) and L-c74cfb4e07bc
(FIN.PAINT), BOUNDED 22.6502 .. 26.0002 m2 each (T-292 face rows '2F-01|2F-W00' 1.8310 x 3.35 and 'OFF:COLUMN' 0.1750 x
3.35; T-349 substrate row; T-388 face row): effect **+0.0201 m2 on each bound (0.08 %)**, sampling, HELD lines (lift door
height), nothing released. Skirting: unaffected (T-441's 2F lobby north 1.000 lm is by handle). No 0.43 enters any
quantity as a wrong drawn length; the T-441 wording 'records 0.43, drawn 0.600' is an attribution difference.
Recommendation for the next ledger re-issue (lane I, no new task): face rows by handle (wall run 1.800 + column 2F72 face
0.200) instead of the sampled 1.831 + 0.175.

## 3. Closure in units (ERS s.2.4)

GF stair room wall + column run 11.100 lm (V2.9): hall 4.650 + lobby 1.400 + GF-ST-CN north 0.200 (now a lobby face) +
T-410 west 2.800 + MS1-T north 1.150 + D1 east 0.900 = **11.100, residual 0.000** (unchanged; one item moves from 'unread'
to the lobby). The band and the OP-020 jambs were never in this run (band = rails; jambs = reveal returns).

2F: lobby 3.350 + arrival 4.150 + faces with no floor at +9.70 9.400 = 16.900 (T-441, unchanged); the 0.350 of 129A at
y 1.95 .. 2.30 is inside T-410 MS2-U.E (stair skirting), as T-441's 'east 4.500 ... flight skirting is T-410's' states.

## 4. Candidate binding (V3.0.40, own run)

Own run reproduced V3_0_40_BOQ_LINES.json sha256 **aa6aa927** (= board pin, T-430 MERGED). Lines the proposals touch:

| Line | Item | V3.0.40 | State |
|---|---|---|---|
| L-47fa825d197d32754240 | FIN.SKIRTING lm, GF stair room (parent) | net blank | BLOCKED_RFI |
| L-b8d4a7f04277deb1b0b0 | FIN.SKIRTING lm, 2F stair hall (parent) | net blank | BLOCKED_RFI |
| L-f53d498668da3dc7c228 | FIN.FLOOR.FINISH_HELD m2, GF hall +1.00 | 4.805 | SOURCE_DERIVED |
| L-b4441a1b55eda53d98ea | FIN.FLOOR.FINISH_HELD m2, GF back lobby +0.30 | 1.3225 | SOURCE_DERIVED |
| L-ae0cdd794cc5fdbe0c29 | FIN.PLASTER m2, 2F stair hall | 22.6502 .. 26.0002 | BOUNDED_EXPOSURE |
| L-c74cfb4e07bcc47bc5d6 | FIN.PAINT m2, 2F stair hall | 22.6502 .. 26.0002 | BOUNDED_EXPOSURE |

Nothing in this task changes them; the proposals of s.7 are for lane I.

## 5. Engine vs freelancer (quantities only; T-106 merged trace)

| Space | Freelancer | Ours (confirmed) | Difference | Components | Verdict proposal |
|---|---|---|---|---|---|
| 2F corridor | 13.60 lm | 7.500 lm | -6.100 lm (-44.85 %) | openings 2.900 + open north edge 2.500 + top-going strip 0.700 (0.350 stair side + 0.350 guard) | RULE_DIFFERENCE 6.100, residual 0.000 (was 0.700 UNRESOLVED) |
| GF stair hall + back lobby | no row | 6.250 lm (was 6.050) | +6.250 lm (engine only) | his open-plan row runs round reception, dining and entrance only | ENGINE_RIGHT on the existence of the faces (T-441), material HELD with the floor finish |

## 6. RFI draft (ERS s.6 format; for the Lead's designer list; nothing sent)

RFI c (narrowed; replaces T-441's 'under-winder space open or closed'):
- Issue: the floor of the space under the GF MS1-T winders, west of the +0.30 back lobby (x 0 .. 1.15 in the stair-room
  frame): its level, whether it is open to the lobby or enclosed, and its finish.
- Evidence: GF plan (P7757.dxf / sheet 3): no wall, step or column between the lobby and that space; the '+0.30' mark sits
  in the 0.20 m strip beside it; the winders are drawn hidden (above the cut). Section A-A: the winder soffit at about +2.4,
  nothing drawn below it.
- Investigation: the strip x 1.15 .. 1.35 is settled as +0.30 floor (level point inside); the lobby has no face on x 1.35;
  the slab-on-grade level under the winders is not printed on the architectural sheets read.
- Alternatives: (A) +0.30 floor continues under the winders, open to the lobby; (B) the space is enclosed or filled
  (no floor finish).
- Quantity impact: lobby skirting +0 (B) .. +2.200 lm (A; up to 3.450 with the OP-022 jamb zone and a slab-edge face at
  the MS1-L end); lobby floor +0 .. +1.3225 m2 (T-418 counts the winders' plan 1.3225 m2 as STAIRS).
- Recommendation: (A) is what the plan shows (nothing drawn between the lobby and the space), but no level or finish is
  printed for it; ask the designer rather than assume.
- Status: HELD (blank, never 0). Next action: everything else in this task is settled without the designer.

No owner question: ERS s.2.7 is not met (the open item is a designer fact; every other item is settled by drawings and
existing owner answers Q-06 (a) / Q-46 A).

## 7. Lane I proposals (no candidate change in this task)

| Line / item | Now | Proposal | Evidence status |
|---|---|---|---|
| GF stair hall skirting child (T-441 split of L-47fa825d) | 4.650 + HELD band 2.200 .. 3.400 + HELD jambs 0.400 | 4.650 lm, band and jambs NOT_APPLICABLE (no held note) | DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED (Q-06 a) |
| GF back lobby skirting child (from L-47fa825d) | 1.400 + UNKNOWN west 1.150 | 1.600 lm + UNKNOWN under-winder 2.200 .. 3.450 (RFI c), blank | DRAWING-CONFIRMED; remainder UNKNOWN |
| GF stair hall floor part L-f53d4986 (FINISH_HELD) | 4.805 m2 | 4.925 m2 (+0.120) | area DRAWING-CONFIRMED, finish HELD |
| GF back lobby floor part L-b4441a1b (FINISH_HELD) | 1.3225 m2 | 1.5525 m2 (+0.230, strip GF-ST-CN) | area DRAWING-CONFIRMED, finish HELD |
| 2F stair hall plaster / paint L-ae0cdd794cc5fdbe0c29 / L-c74cfb4e07bcc47bc5d6 | 22.6502 .. 26.0002 m2 | -0.0201 m2 on each bound at the next ledger re-issue (face rows by handle) | DRAWING-CONFIRMED geometry; HELD line |
| 2F corridor skirting vs freelancer | 0.700 UNRESOLVED | 0.700 RULE_DIFFERENCE (0.350 T-410 MS2-U.E ownership + 0.350 guard edge) | verdict proposal |

Deductions by opening id unchanged (T-441). No face here is shared with T-443's children or B7-07 / B7-08: own overlap test
(R-T447-5, level-aware) against T-410 MS1-T north (+2.667 .. +3.50) and T-441's lobby north (x 1.35 .. 2.5) passes; the
2F 0.350 on 129A is assigned to T-410 MS2-U.E, not to a room line.

## 8. Rule, test, lesson

- **R-T447-1 .. 5** (proposed, research, any villa; module docstring): guard edge FACE only with a solid surface to the
  floor, NOT_APPLICABLE when a section draws a balustrade with the flight visible below the rail, else held; doorless jambs
  by the owner method's five conditions (one FALSE with evidence -> NOT_APPLICABLE, one UNKNOWN -> HELD); a strip with a
  level point inside and nothing drawn is floor, hidden overhead outlines never make it SOLID; a freelancer outline is
  traced by drawn-line constructions that reproduce his figure exactly, each added stretch classed; held blank, never 0.
- Tests `tests/t447_stair_room_held_faces` (15): hand villa K447 normal cases; adverse **'balustrade edge skirted as a
  wall face'** refused, held guard carried as 0 refused, contradictory / unreferenced evidence refused, unit slip refused,
  jamb FALSE without evidence refused, conditions missing refused, opening without id refused, step line keeps a strip
  HELD, solid outline keeps it SOLID, non-contiguous outline refused, mirror invariance of the trace, stair-side stretch
  without owner refused, face overlap at the same level refused (a landing above at another level is not an overlap);
  Alsenan pins rebuilt from the committed extract.
- Lessons-register row proposed (ERS s.7):

| 2026-11-01 | Three stair-room skirting items sat HELD as 'guard upstand or wall', 'tile or skirting' and 'open or closed', and a 0.700 lm freelancer residual was UNRESOLVED (T-441), although the section, a level mark and the owner's wet-space answer settled them | the plan was read alone; a band drawn below the cut was treated as a possible wall; the doorless-jamb rule was not run condition by condition; a level mark's position was not used as evidence | read the section before holding a guard edge (a balustrade with the flight visible below the rail is not a skirting face); run URBAN-SKIRTING-OPENING-METHOD's five conditions per jamb; a level point inside an undrawn strip makes it floor; trace a freelancer outline with drawn-line constructions that reproduce his figure exactly; every villa, skirting / floor parts | tests/t447_stair_room_held_faces | T-447 |

## 9. Self-gate and what is missing

self-gate: a (research + tests + CODEMAP only; no engine / rule / candidate file) c (non-Alsenan fixture K447, adverse
cases incl. 'balustrade edge skirted as a wall face') d (reproducible: `--extract <P7757.dxf> <V3.0.40 run dir>`, `--check`
without private input) f (no new item code, nothing valued, nothing wired) h (handles and room-local lengths only; no world
coordinate, no drawing text, no client data; sheets cited by number and described in words) PASS.
Missing: the under-winder space (RFI c); the skirting materials (follow the HELD floor finishes); whether the reveal returns
of OP-020 are in the GF-11 wall tile line; the horizontal +1.00 rail run in section A-A against RL-07 / RL-08; his 2F
corridor area residual -0.0775 m2.

Checker re-read suggestion: the divider in section A-A (sheet 10, the +1.00 rails with MS1-L visible below the lowest rail)
and the level point of 4AB inside the strip x 1.15 .. 1.35.
