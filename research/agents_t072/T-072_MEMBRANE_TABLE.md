# T-072 Membrane purchase table (owner requirement 2026-10-19)

Worker 2, 2026-10-19. Branch `agents/task-T-072` from working head 97c4bfc. Python 3.11 venv from requirements.txt.
Areas, lengths, counts and engine room ids only; no coordinates, no client data.

## What was built

- `engine/source/membrane_purchase_table.py` (new, opt-in): one row per waterproofed area (floor, room name, net area,
  upturn run and area, doorway piece, floor + upturn surface, strips, laps, installed membrane, consumed membrane,
  cutting waste, rolls if alone, gross offcuts) and, per membrane system, the rolls to buy from the engine's shared
  cutting plan next to the rolls-if-alone sum. Every number is read from `waterproofing_system` (schedule rows, cutting
  plan), the area's layout and `wp_install.junction` (continuous fold); nothing is laid out again. Both junction methods
  are shown: SEPARATE_UPSTAND (the engine's V2.5 plan) and CONTINUOUS_FOLD (the owner's Q-30 words "folded from the same
  membrane"); the engine keeps the junction UNRESOLVED (N-11) and the table selects neither. HELD rows: reason shown,
  every quantity None (never 0), outside the roll totals, counted beside them.
- `tools/membrane_table.py` (new): writes MEMBRANE_TABLE.json / .csv / .md from a run folder; HELD rows from
  FIN.WP.FLOOR lines without a quantity, from wet-review spaces (REVIEW_SPACES.json) whose wet scenario carries a
  membrane, from open plans with a wet function (finish scope REVIEW), and from a `--held` file (roofs held elsewhere).
- No released method, no frozen file and no released quantity changed (freeze check 0). Wiring the table into the
  released output is an owner step after verification.

## Hand fixtures (tests/t072_membrane_table, 15 tests, all pass; synthetic, not Alsenan)

| Case | Hand | Table (engine) |
|---|---|---|
| Owner's kitchen 3.00 x 4.00, door 0.90 (Q-30) | 4 strips 0.80+0.90+0.90+0.40 = 3.00 floor, last cut 0.70 wide, each 4.40 m; cut 16.28 m2; surface 14.80; 2 rolls; offcuts 3.72 | continuous fold: ALONG_Y, 4 strips, last 0.70, 4.40 m, installed 16.28, required 14.80, 2 rolls, gross offcuts 3.72: **every number reproduced** |
| same, other strip direction | 5 strips of 3.40 m (last 0.80) = 17.00 m of roll, 3 rolls | reported as the fold's ALONG_X alternative: 3 rolls (direction changes the roll count) |
| same, engine's separate upstand | 5 floor strips of 3.00 (last 0.40); upturn 14.00 - 0.90 door = 13.10 lm = 2.62 m2; doorway piece 0.18; surface 14.80; laps 1.20 + 1.31 + 0.12 + 0.09 = 2.72; installed 17.52; 2 rolls | equal; **+1.24 m2 (+7.6 %) installed against the owner's 16.28, same 2 rolls** |
| closed 3.00 x 4.00 | floor 15.00 m of roll + band segment 2.84 (8.50 m of lanes / 3) = 17.84 consumed; installed 17.55; waste 0.29 | equal |
| Owner's 3 x 3 bathroom picture | by his own Q-30 method: developed 3.40 x 3.40, 4 strips (last 0.70) x 3.40 = 13.60 m of roll, **2 rolls**, installed 12.58, surface 11.40; even 3 strips (10.20 m) exceed one roll | fold equal; separate upstand 13.65 installed, 2 rolls. The picture's "3 strips x 3.20 = 9.60 m2, 1 roll" leaves out the upturn on two walls and the laps |
| Toilet 2.40 x 1.70, door 0.80 | upturn 7.40 lm = 1.48; surface 5.72; fold 3 x 2.10 = 6.30 = 5.72 + laps 0.42 + corners 0.16; 1 roll | equal |
| L-shaped bathroom | 6.00 m2, 11.00 lm, surface 8.20 | equal; fold NOT computed (rectangles only), reason in the row |
| Roof 6 x 5 with a 1 x 1 skylight (Q-29) | net 29.00, upturn (22 + 4) x 0.20 = 5.20, surface 34.20 | equal; own exterior system, never added to the wet-area rolls |
| mm vs m; rotated 37 deg; mirrored | same numbers | equal for the separate upstand; the fold is NOT computed when rotated (engine: axis-parallel only), computed and equal when mirrored |
| Two showers 0.60 x 7.60 and 0.60 x 1.60 | fold strips 8.00 + 2.00 m: alone 1 + 1 = 2 rolls, together one 10 m roll | fold 1 roll to buy vs 2 alone; separate upstand 2 to buy vs 3 alone |
| HELD rows, duplicates, an unbalanced fold record | never 0, outside totals, refused | as hand |

## Alsenan run (ARCH_TAKEOFF_V2.9 on the P7757 DXF from Drive; table from the run's own files)

14 measured wet areas (GF 7, 1F 6, 2F 1), 9 HELD rows (3 wet-review spaces, 2 open plans with a pantry, 4 roofs).

| Quantity | Engine | Freelancer | Difference |
|---|---|---|---|
| Wet floor, all areas he lists | 62.77 m2 measured + 3 held spaces (4.73, 3.13, 1.49 m2 in the run's wet scenario) | 72.01 m2 (17 areas) | -9.24 m2 (-12.8 %) measured; the held 9.35 m2 are exactly his 3 hand-wash spaces (T-010 releases them: 72.12, +0.2 %) |
| Wet floor, the 14 areas both have | 62.77 m2 | 62.43 m2 (72.01 - hand-wash 4.73 + 1.70 + 3.15) | +0.34 m2 (+0.5 %) |
| per floor (same areas) | GF 26.08 (kitchen 9.63 + 6 baths 16.45), 1F 31.14, 2F 5.55 | GF 25.90 (9.55 + 16.35), 1F 30.91, roof floor 5.62 | GF +0.7 %, 1F +0.8 %, 2F -1.2 % |
| Upturn, full room boundary (doorway included) | 123.13 lm | 122.61 lm (144.61 - hand-wash 22.00) | +0.52 lm (+0.4 %) |
| Upturn the engine bills (walls, columns, sills; UP-WP-003 excludes doorways) | 110.33 lm = 22.07 m2 | 122.61 lm | -12.28 lm (-10.0 %): RULE_DIFFERENCE (see below) |
| Floor + upturn + doorway pieces (surface) | 86.77 m2 | not given | - |
| Installed membrane (laps included) | 105.22 m2 | not given | - |
| Membrane cut from rolls | 119.54 m2 | not given | - |
| Rolls to buy, wet areas | **13 rolls** (shared cutting plan; 16 if each area alone, 3 saved by reusing offcuts), PROVISIONAL (system not named, 45 withheld details) | not given (he has no roll count) | - |
| Roofs | 4 roofs HELD (outlines not closed / not drawn; T-071 not wired) | 285 m2, 194 lm | not compared (held, never 0) |

Who is right (proposals for the verifier):
- Per-area floor: ENGINE_RIGHT / RULE_DIFFERENCE within 1 % on the 14 common areas (the run measures the wall-face
  outline; the largest gap is the 2F bathroom 5.55 vs 5.62 m2: engine outline 1.85 x 3.00 = 5.55; not re-checked on the printed sheet in this run).
- Upturn lm: RULE_DIFFERENCE. The freelancer bills the whole boundary (his lm match the engine's full perimeters within
  0.4 %); the engine's UP-WP-003 bills walls only and treats each doorway as a transition item (UP-WP-DOOR-001, left
  UNRESOLVED). Note for the Lead: owner Q-30 answer A reads "0.20 m upturn on the whole boundary, doorway included"
  for kitchens "like a bathroom", which is the freelancer's basis and conflicts with the UP-WP-003 registry example;
  if the Lead reads Q-30 as setting the doorway detail to UPTURN_ACROSS_THRESHOLD, that is a new rule version, not a
  table change.
- Rolls: no freelancer figure; the engine's 13 rolls rest on its separate-upstand plan.

## What we learned

1. The engine's continuous fold is the owner's method exactly (his kitchen reproduced to the cm2), but on Alsenan it is
   computed for **none** of the 14 wet areas: every room ring carries 6 to 24 vertices (door jambs and wall joints
   leave collinear points), 2 rooms are drawn at 45 deg, and the fold also refuses a doorway whose depth is not the
   upturn height (most Alsenan doorway pieces are 0.12 m deep against the 0.20 m upturn). After removing collinear points,
   9 of the 14 rooms are plain rectangles (bounding box = net area). A proposed follow-up (new version beside
   `wp_install.continuous_fold`, never in place): drop collinear ring points, work in the room's own frame, and give the
   doorway flap its own piece, so the owner's method is computed on real drawings; until then the table shows the
   separate-upstand rolls and says why the fold is missing.
2. The owner's 3 x 3 picture cannot be reproduced by his own Q-30 method: with the 0.20 m upturn on all four walls and
   the 0.10 m laps it needs 4 strips of 3.40 m and 2 rolls, not 3 x 3.20 m and 1 roll.
3. Strip direction changes the roll count (owner's kitchen: 2 rolls one way, 3 the other); both are in every row.

## Missing

- T-074 hand table (not yet done) to check every Alsenan row by hand; the comparison above uses the freelancer's rows.
- Roof rows stay HELD until the exterior-space module (T-071) is wired; skylight sizes (Q-29) are not printed.
- The fold method on real rooms (follow-up above); a named membrane system and the withheld details keep the roll count
  PROVISIONAL.
