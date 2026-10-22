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
