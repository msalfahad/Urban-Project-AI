# T-598 B7-05 stair nosing: the 20 HELD edges of the T-412 census closed by name (development villa; method every villa)

Worker 2 (lane A), 2026-11-07. Research files `research/agents_t598/*` and `tests/t598_nosing_held_edges/` only; no
engine, rule, knowledge, method, registry or candidate file touched; nothing released, no candidate quantity changed
(feeds T-424 B7-05). ERS applied: s.2.1 physical element, s.2.2 evidence hierarchy, s.2.3 first principles, s.2.4
reconciliation in units, s.2.6 statuses, s.2.7 escalation test (not met: no owner question), s.4 rule + test, s.7 lesson.
Rules: R-T412-1..4, R-T434-1 / -2, OWNER_RULE_STAIRS_2026-10-24 S-9 / A8 / (4), Q-46 A, Q-50 A cond, Q-51 A cond.
No image, client name, drawing text or workbook row text is copied here; the JSON holds handles, run positions (m from
the stair's north wall face), lengths, radii and sweeps only.

## 0. What was read (own reading this run, by handle; `t598_alsenan.py`)

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF), decoded into `.work/private` only | 1F plan MS1-U fronts A92 .. ABE (11), lane bound A8F, east wall B16; 2F plan MS2-U fronts 135B .. 1386 (11), lane bound 1358, wall 129A, closing-riser pair 12B4 / 12B5, diagonal pair 2F1F / 2F20; GF plan RS-C radial fronts 256 .. 240 (12) + faces 257 .. 241, bands 239 / 23F / 23D / 23E, curtail arcs 258 / 25A + faces 259 / 25B |
| Drive "ST7757 dxf.dxf" (structural DXF), `.work/private` only: SECOND DRAWING | ST p.4 east lane 12 riser faces 25B .. 459, opening 25A, turn face 2F3; ST p.5 east lane 11 riser faces 62F .. 644, closing-riser face 5E2, opening 62E; RS-C radial faces 2EA .. 2DF (12), curtail faces 2EB / 2EC |
| research/agents_t412, t434, t493, t415, t578 (MERGED) | the starting census, the governed turn count, the landing partition, the curved-flight reconstruction, the freelancer figures (quantities only) |

Starting point: T-412 named 20 HELD edges (MS1-T 5, MS1-U floor, MS2-TR, MS2-U floor, RS-C 12). T-434 (MERGED a6b325b3)
already confirmed the MS1-T landing nosing N05 (2C6, 1.150 lm): 19 remain, 88.500 lm confirmed before this task.

## 1. Physical element and the rule (R-T598-1)

A nosing is the exposed front edge at the top of each riser (one riser, one nosing). A held edge is closed by two
separate questions: (1) EXISTENCE: does the governing riser count put a riser here? (2) LENGTH: is the length fixed by
drawn geometry whatever the open item is? An open POSITION (head clash) never holds a length that the drawn lane fixes;
an undrawn GEOMETRY (winder subdivision) holds it with a first-principles bound; two drawn LENGTHS hold it as a conflict
with its bound. A front edge continuing as an arc is measured on the developed arc (R-T598-2).

## 2. Result: 20 / 20 classed (ALSENAN_EDGES_T598.json)

| Edge(s) | Class | lm | Status | Evidence (sheet, handles) |
|---|---|---|---|---|
| ST01-MS1T-N05 landing nosing | (closed by T-434) | 1.150 | DRAWING-CONFIRMED | arch GF 2C6 + ST p.4 2F3 |
| ST01-MS1T-N01 .. N04 winder fronts | DESIGNER ITEM | HELD | HELD | section A-A 5 turn risers (governing, T-434) vs every plan 3 radial fronts (a 4-riser fan); subdivision not drawn (S-9, A8, R-T434-2). Bound 4 x 1.150 = **4.600 .. 4 x 1.735655 = 6.943 lm** (each front crosses the 1.150 lane; none exceeds the diagonal of the 1.150 x 1.300 turn region) |
| ST01-MS1U-FLOOR (1F +5.50) | VALUE | **1.150** | DRAWING-CONFIRMED | count 12 (A-A, Q-46 A); arch 1F 11 fronts s 1.15 .. 4.15 at 0.300 -> front s 4.45; ST p.4 draws its riser face 459 at s 4.50 (exact); lane A8F (s 1.15 .. 4.55) / B16 covers the whole open range |
| ST01-MS2U-FLOOR (2F +9.70) | VALUE | **1.150** | DRAWING-CONFIRMED (edge line itself on no plan) | count 12 (A-A, Q-46 A); arch 2F and ST p.5 both draw 11; lane 1358 (s 1.15 .. 4.55) / 129A covers the open range s 4.25 .. 4.45 |
| ST01-MS2TR closing riser | VALUE | **1.150** | DRAWING-CONFIRMED | arch 2F 12B4 (front) / 12B5 (face, 0.050); ST p.5 5E2 = the same face (0.050 from the east lane edge, 1.150 long); section one closing riser |
| ST02-RSC-252 .. 240 (10) | VALUE | **11.500** | ASSUMED - OWNER-APPROVED (count Q-50 A cond) | radial fronts r 1.5805 .. 2.7305 = 1.150; ST p.4 12 radial faces 2EA .. 2DF |
| ST02-RSC-256 (tread 1) | VALUE | **2.099440** = 1.150 + curtail 0.949440 | ASSUMED - OWNER-APPROVED | radial 256 + front arc 258 (r 0.354001, sweep 153.668724 deg) joining its inner end (0.0 mm); face 259 = ST 2EB exactly |
| ST02-RSC-254 (tread 2) | VALUE | **1.822000** = 1.150 + curtail 0.672000 | ASSUMED - OWNER-APPROVED | radial 254 + front arc 25A (r 0.243547, sweep 158.091733 deg); face 25B = ST 2EC exactly |
| ST02-RSC-256-BAND | DESIGNER ITEM | HELD | HELD | the 0.050 of 256 over the outer band 23D / 23E (the band starts on 256): stringer cap, upstand or tread not printed (RL-09); bound 0 .. 0.050 |

Hand checks (independent of the code): 0.354001 x 153.668724 x pi / 180 = 0.949440; 0.243547 x 158.091733 x pi / 180 =
0.672000 (chords 0.689 / 0.478 never used); hypot(1.150, 1.300) = 1.735655; 2F diagonal hypot(1.150, 1.150) = 1.626346.

**Totals.** DRAWING-CONFIRMED +3.450 lm (3 edges); ASSUMED - OWNER-APPROVED 15.421440 lm (RS-C 12 edges incl. 1.621440
lm of curtail); HELD 4 winder fronts (4.600 .. 6.943) + the 256 band end (0 .. 0.050). B7-05 nosing **88.500 -> 107.371440
lm valued (85 edges), 4 edges HELD** (was 19 HELD). Nothing released; RS-C stays behind the owner's Q-50 A cond release
condition (the Checker decides whether the straight drawn radial edges and the two-drawing curtail meet "curved
geometry supported").

## 3. New finding: the curtail is a nosing (R-T598-2)

T-412 R-T412-2 stated "every front edge is straight" on this villa. The round stair's first two treads continue round a
curtail into the well: arcs 258 and 25A are drawn as front + riser-face PAIRS exactly like every straight edge, their
faces coincide with the structural curtail arcs 2EB / 2EC (radius and sweep identical), and each front arc starts at its
radial front's inner end (0.0 mm) and returns to the inner edge at riser face 251. The developed fronts add **1.621440
lm** (ENGINE_OMISSION in the census, not a new riser: 28 nosings stay 28). The curtail's concrete / finish material stays
HELD per T-415 (unchanged).

## 4. Engine vs freelancer (his 123.20 lm = 63 x 1.20 + 28 x 1.20 + 5 x 2.80, T-578), signed his - ours, no %

| Stair | his | ours valued | his - ours | causes (lm) |
|---|---|---|---|---|
| ST-01 (+ D1) | 75.60 | 59.700 (52 edges) | +15.900 | count +8.400 (7 pieces beyond the 56 drawn risers, UNRESOLVED, T-434) / HELD +4.800 (his share opposite N01 .. N04) / width +2.600 (52 x 0.050, ENGINE_RIGHT) / notches +0.100 (ENGINE_RIGHT) |
| ST-02 round | 33.60 | 33.671440 (28 edges) | -0.071440 | width +1.400 (28 x 0.050) / notches +0.150 / curtail -1.621440 (he carries count x width, no curtail: ENGINE_RIGHT on the drawn pairs) |
| ST-03 E1 | 14.00 | 14.000 | 0 | AGREE |
| **Total** | **123.20** | **107.371440** | **+15.828560** | count 8.400, HELD 4.800, width 4.000, notches 0.250, curtail -1.621440; unexplained 0.000 |

Was (T-578): +35.85 with HELD 24.00. Verdict proposals: floor edges and MS2-TR ENGINE_RIGHT (governed count, drawn
length); RS-C AGREE on count, ENGINE_RIGHT on width and curtail; MS1-T UNRESOLVED (designer); ST-01 +7 pieces stays
RULE_DIFFERENCE / UNRESOLVED (T-434).

## 5. Designer items (drafts for the Lead; no owner question: ERS s.2.7 not met)

1. Existing C-ST-3 / T-434 RFI: plan subdivision of the five ST-01 winders (N01 .. N04; bound 4.600 .. 6.943 lm).
2. Existing Q-46 RFI: head clash B20 / B23: the governing 12th riser face lies 0.200 inside the slab opening end on ST p.4
   and p.5; affects the floor edges' POSITION only (their 1.150 lm is fixed by the drawn lane).
3. Existing Q-ST-11: the 2F diagonal pair 2F1F / 2F20 (1.626 lm, front + face) across the east half of MS2-LD; on one
   drawing only; the section admits one closing riser; never added (beside: 1.626 if it were the riser instead).
4. RL-09 addendum: the kind of the RS-C outer band where 256 crosses it (0 .. 0.050 lm).

## 6. Lane I note for T-424 (no candidate change here)

Wire per edge id: the 3 ST-01 edges as DRAWING-CONFIRMED (`landing_floor_edge_lm` +2.300 for the two floor edges and
+1.150 MS2-TR, outside any step: 8.550 -> 12.000 lm outside the step basis); RS-C 12 edges ASSUMED - OWNER-APPROVED with
their curtail split (`in_step_basis_lm` 13.800 + curtail 1.621440, see UP-STAIR-008: the commercial step lm does not
contain the curtail); N01 .. N04 and the band end HELD blank with bounds; T-424's "20 HELD" list is superseded by the
4 + 1 here once the Checker agrees.

## 7. Rule, test, lesson

- R-T598-1 / -2 / -3 in `edge_classes.py` (docstring; research, unwired).
- Tests `tests/t598_nosing_held_edges`: Villa K598 hand fixture (floor edge on an invariant lane 1.000, closing riser,
  3 winders not drawn bound 3.000 .. 4.459821, curtail pi x 0.300 = 0.942478 vs chord 0.600); adverse: winder count
  conflict stays DRAWING_CONFLICT with bound (1.200, 1.414214), held as 0 / None refused, generated winder refused, a lane
  bound not covering the open position refused, no governing count never a VALUE, equal / missing readings, cm,
  unknown sources, zero sweep; rotation / mirror invariance. Alsenan pins: reproduces from the committed JSON, private
  re-read equals the committed JSON (skipped without private input), 19 + 1 classes, curtail by hand, totals and every
  stair's causes close to 0.000, no coordinate / non-ASCII text in the JSON.
- Lessons-register row proposed:

| 2026-11-07 | 20 nosing edges sat HELD for a week, 15 of them with a drawn or lane-fixed length; the round stair's curtail fronts were missed | 'held' was kept for any open item on a flight (position clash, release hold, count source) instead of asking separately whether the edge exists and whether its LENGTH is drawn; R-T412-2 asserted all fronts straight without sweeping arcs | close a held edge by EXISTENCE (governing count) and LENGTH (drawn edge, second-drawing face, or a lane invariant over the open position) separately; sweep arcs drawn as front + face pairs and measure them developed (any villa) | tests/t598_nosing_held_edges | PROPOSED |

Self-gate: research + tests only; non-Alsenan fixture with adverse cases; reproducible (`--check` REPRODUCED, `--compare`
SAME AS COMMITTED on the Drive copies); nothing wired or released; no client data. Missing: the 4 winder fronts and
the band end (designer); the MS2-U floor edge line is drawn on no plan (its existence rests on the governing section
count, its length on the drawn lane: the Checker may downgrade it to HELD 1.150 .. 1.150 if it reads S-9 (4) stricter).
