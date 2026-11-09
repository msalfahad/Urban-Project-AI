# T-536 WIRING MANIFEST V2 on ARCH_TAKEOFF_V3.0.58 (supersedes the T-530 V1 manifest)

Worker 3 (lane I, non-candidate, integration dependency, backlog-permitted), 2026-11-05, claim 17:00 UTC, run
session_01E6cPnbgdFj3zJD3XX7V15o, engine base f05abdd6. Files: `WIRING_MANIFEST_V2.json` (this folder) and
`tests/t536_wiring_manifest/` (builder `manifest_t536.py` + 21 tests). No candidate, released (V2.9 + route G), rule,
knowledge, registry or producer file is touched; nothing is wired. V1 (`research/agents_t530`, sha 3ec1843a pinned) is
read only: its builder is imported and re-run on the newer inputs; its committed JSON is the V1 side of every diff.
Every V2 figure is recomputed from the merged pieces' committed outputs or own functions; the test asserts the
committed JSON byte for byte against the rebuild. Drawing by Drive title only: "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), decoded this run into the private folder (T-517 / T-522 / T-529
read it at run time; without it stream F stays HELD and the full test skips).

## 1. Sources (each merge commit must be in the tree: an unmerged or stale source is refused)

V1 pieces (T-453, T-507, T-516 .. T-524, T-526, T-528) + T-527 cf8925df (LINTEL_BEARING_V3), T-529 5f775ba6
(exposure V2), T-530 f05abdd6 (V1). NOT a source: T-534 (READY f97634e0, Gate A pending). Every move on a line goes
through `apply_moves()`: piece, merge commit, the pieces that must have moved the line first; out of order, twice or
unmerged -> refused.

## 2. V1 -> V2, every line that changed, with its cause

| line | element | V1 | V2 | cause |
|---|---|---|---|---|
| L-31232f81 STR.CONC.LINTEL m3 | D-GF-13 | BOUNDED 0.054 .. 0.11292 (B 0.15 x D 0.20 x L 1.80 .. 3.764) | BOUNDED 0.054 .. **0.11289** (L 1.80 .. 3.763; 0.15 x 0.20 x 3.763) | T-527: END 1.261 -> 1.260 at the column (V2 area tolerance no longer lengthens the reach) |
| L-d7d1bf8c FIN.WP.ROOF_UPTURN lm | pool-court ledge | HELD 0 .. 0.551614 | **0.551614 MEASURED** (BCD 0.250804 + BD0 0.300810; 0.110323 m2 at 0.20) | T-529 R-WP-APPL-EXPOSED-2b: ledge EXPOSED, UPTURN-1 applies |
| L-2361d6ec FIN.WP.ROOF m2 | pool-court ledge | HELD 0 .. 0.639573 'unchanged, rule V2 needed' | **0.639573 MEASURED**; beside HELD: window transition 2.976663 lm, void edge 2.817214 lm, drainage RFI | T-529 (F-C-T529-1) |
| NEW FIN.WP.DOORWAY_TRANSITION m2 (V1) | ledge glazing BCE | added blank m2, 2.976663 lm beside | **no line**: WINDOW_TRANSITION lm beside L-2361d6ec | F-T530-4 (below) |
| 4 NEW ledge build-up lines (T-517) | screed / insulation / protection / finish | HELD, gaps incl. 'ZONE: exposure' | HELD, ZONE gap closed by T-529; AREA / FALLS / THICKNESS / SCOPE gaps remain | T-529 |

Unchanged V1 -> V2 (asserted): the other 15 lintel lines; the 2 staged glue hosts (L-4b9a29d4 443.27313 .. 451.60893
kg, L-d14c6c9b 23.769 .. 23.895 kg; no moved bearing on a valued host); the 2 perimeter mortar lines (0.058854 /
0.039291 m3); the AAC glue group (AT_LEAST 35.387755 .. 36.226627 bags, buy >= 36 .. 37) and cement group (131.601727
.. 173.071174, >= 132 .. 174), all HELD; the window run L-1954878b 0.500002 lm MEASURED (T-522).

HELD stays HELD by name with the new ceiling beside, never a quantity: W18 length ceiling 0.978 -> 1.077 m and D-GF-11
1.869 -> 1.865 m (both HELD_BY_NAME; their bound is the T-524 deficit-end volume, unchanged: W18 0.034692 m3, pair
0.060 .. 0.07914 m3 once). Lintel code view: AT_LEAST 0.874692 m3 unchanged; upper known part 1.183992 -> 1.183962 m3
(= -0.00003 of D-GF-13); D-2F-01 upper HELD.

## 3. Code totals (stream F, V3.0.58 -> after the F package)

FIN.WP.ROOF 209.018867 -> **209.658440 m2** (+0.639573, +0.306 %; 1 HELD line left: 2F block roof, Q-34).
FIN.WP.ROOF_UPTURN 186.782544 -> **187.834160 lm** (+1.051616, +0.563 %: window 0.500002 + ledge 0.551614).
FIN.ROOF.FINISH 202.219760 -> 206.738932 m2 (+2.235 %, T-517 open sky 4.519172). FIN.ROOF.SCREED / INSULATION /
PROTECTION / FIN.WP.DOORWAY_TRANSITION: no valued line, printed HELD, never 0.0; DOORWAY_TRANSITION lines 16 -> 16.

## 4. F-T530-4: the unit of a line comes from its item

Physical element: the frame line of the bay glazing BCE standing on the ledge slab (2.976663 lm). Evidence: the item
code FIN.WP.DOORWAY_TRANSITION is m2 on all 16 candidate lines (boq_line ITEMS, UP-WP-DOOR-001: a doorway of a wet area,
B8-07); the candidate method of record (arch_v3058, R-T507-1, Gate B) refuses a doorway on a B8-06 zone and names
WINDOW_TRANSITION as a HELD item beside the zone's membrane line, in lm, treatment by detail. An m2 line would need a
transition width that is printed nowhere (invented). Rule applied (`line_unit`, every line): a line's unit is the unit
its code already carries on the candidate; a measure in another unit is refused, never converted. Result: no line, a
beside item in its own unit; no quantity moves (the V1 line was blank).

## 5. T-526 column end census and FINISH V7

T-526 (R-T526-1): 12 V1-missed ends, 0 candidate lines moved: run length / blockwork / blocks +0 (end face = column
face, gap 0.0 mm); 1F-W09 perimeter 0.010355 m3 = the V1 / T-520 value (one write); ties +30 nr and crack mesh +40.90
m.l (owner band) / +44.10 (drawing band) have NO line in V3.0.58 or the T-498 stage (F-T536-1): they wait for T-355 /
T-317 ledger versions reading END_CENSUS_V2 (T-532). FINISH V7 stair: installed 1.062939 m3 = 10.178704 bags agrees,
procurement C-V7 open; area HELD BY NAME until T-534 passes Gate A (F-T536-2). V6: reader of the T-500 keys (unchanged).

## 6. Evidence status (WORKFLOW_CONTROLS s.5) and packages

Lintel lows DRAWING-CONFIRMED, highs HELD where no pier ceiling; deficit lintels HELD (designer RFI); ledge membrane and
upturn DRAWING-CONFIRMED (Checker re-measure AGREE 16:02); perimeter ASSUMED - OWNER-APPROVED (10 mm joint, Q-75, Q-78);
build-up HELD. Package S (on T-498 r3 after T-525): 16 lintel + 2 glue lines moved, 2 perimeter added; step 5 (host
faces) needs T-537 (RG-1). Package F (on V3.0.58): 3 lines moved (2 upturn, 1 membrane), 8 build-up added, 0
transition lines; V7 after T-534 + F-T518-2. Both blocked by the wrapper allow-list.

## 7. Verdicts, lessons

Engine vs freelancer: roof waterproofing 285.00 m2 single line (cells not read, T-494): -26.7 % -> -26.4 %, no verdict
change; no freelancer lintel / mortar / glue / screed row: UNRESOLVED / RULE_DIFFERENCE unchanged. Ledge membrane
ENGINE_RIGHT once wired (T-529 hand 0.639573). Lessons row (proposed, ERS s.7): | 2026-11-05 | the V1 manifest went
stale within an hour (2 pieces merged after it) and proposed a line in a unit its code does not carry | a manifest is a
snapshot, and a new line's unit was taken from the piece's measure, not from the item | every manifest names its sources
by merge commit (refused when not in the tree), composes moves per line in order, diffs against its predecessor, and
takes a line's unit from its item code (a measure in another unit becomes a beside item, never a converted line; every
villa) | tests/t536_wiring_manifest | proposed |
