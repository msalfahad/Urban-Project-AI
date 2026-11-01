# T-412 B7-05 nosing / edge finishing and the tread / riser piece census per flight (development villa; method every villa)

Worker 2 (lane A), 2026-11-01. Research files `research/agents_t412/*` and `tests/t412_nosing_census/` only; no engine,
rule, knowledge, method, registry or candidate file touched; no candidate quantity changed (lane I proposal in section
7). ERS applied (s.2.1 physical element first, s.2.2 evidence, s.2.4 reconciliation in units, s.4 rule + test, s.7
lesson). Rules: OWNER_RULE_STAIRS_2026-10-24 s.1 (nosing is a listed BOQ item; one verified geometry; a landing never
both a tread and a landing), s.4 S-9 (never generate winders; N-1 only where demonstrated; release per quantity; HELD
blank), UP-STAIR-002 (drawing governs), UP-STAIR-004 (nosing in lm, never summed with m2 / pcs), UP-STAIR-008 (the
commercial step lm covers tread + riser + nosing), Q-46 A (section A-A counts for ST-01), Q-50 A cond (round stair:
straight parts reconstructed from the plans, curved part HELD), Q-51 A cond (winders), WORKFLOW_CONTROLS s.5. No image,
client name, title text or workbook row text is copied here.

## 0. What was read

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF, sha ab54dd55), decoded into `.work/private` only, read BY HANDLE (own read this run) | every front edge (layers 5 / 2), its companion line, its length, spacing, the lane between wall and well band, the three proud columns on S-COL.BON |
| Drive "Alsenan chalet project" ST7757 dxf.dxf (structural DXF, sha 9f9d1179), decoded into `.work/private` only: SECOND DRAWING, own count by handle | the same lanes on the slab plans: p.4 west 45A .. 25E 12 lines + radial 2F6 / 2F4 / 2F5, p.4 east 459 .. 25B 12, p.5 west 646 .. 632 12, p.5 east 644 .. 62F 11, D1 1C7 .. 1C4 4, RS-C 2DF .. 2EA 12 radial; every line 1.150 (`st_cross_read` in ALSENAN_EDGES_T412.json) |
| research/agents_t184 (MERGED; riser counts by section A-A, Q-46 A; ST-02 / ST-03 / D1 reconstruction) | riser counts per flight (cited, not re-derived) |
| research/agents_t410 (MERGED 2fb91300; side table, column census) | side ids (overlap check), the proud columns 2FBD / 3005 / 2FD2 (re-read here on the front edges) |
| research/agents_t415 (MERGED 8c8372a4: RS-C 12 risers, tread lines 1.150 inset 0.050 from the opening edges), research/agents_t398 (MERGED), T-135 FLIGHTS_ONCE, T-418 candidate binding (MERGED) | RS-C status (RFI-S27), engine flight readings, V3.0.35 stair line ids |
| Freelancer FIN workbook (23.6 MB, over the connector limit): his stair rows read from the Drive search content (read-only) | his piece counts and width per piece (section 5) |

## 1. Physical element and the engineering question (ERS s.2.1)

A NOSING is the exposed front edge of a stepped surface, across the stair width, at the top of a riser: **one riser,
one nosing**. What lies behind it decides what it is: a TREAD (a going), a WINDER (a tapered tread; its front edge is the
RADIAL edge, never the lane width and never the going arc), a LANDING EDGE (an intermediate landing reached by the
riser) or a FLOOR EDGE (the floor reached by the last riser). A landing edge and a floor edge are nosings, NOT treads.
So per flight: risers = nosings (drawn or held); treads = TREAD + WINDER nosings; nothing is derived by n - 1 / n.

What the drawing says about the nosing (own reading, every flight): each edge is drawn as a PAIR of parallel lines
0.050 apart, the downhill line solid (or hidden above the cut) and a companion 0.050 UPHILL (MS1-L DC / DE, MS2-L AC0 /
AC2, MS1-U A92 / A93, MS2-U 135B / 135C, D1 481 / 482, E1 36E / 36F, RS-S B43 / B4E, RS-A B59 / B6E, RS-C 256 / 257 at
+1.33 deg = 0.050 at the mid radius): the front edge and the riser face behind it, i.e. a **drawn nosing projection of
0.050 m** on every flight. The plans print nothing about the nosing's FORM (profile, separate strip or worked edge), and
no Urban rule fixes it: the drawn LENGTH is a geometry quantity (DRAWING-CONFIRMED where drawn), the SPECIFICATION is
HELD by name (NOSING_FORM_NOT_PRINTED).

Length per edge = the drawn front edge, less any face standing proud inside the stair width ON that edge. Three columns
stand 0.050 proud inside a lane (T-410 R-T410-4): the edge is shortened when the tread behind it starts inside the
column, interval [c0, c1) (the edge on the column's uphill face is not). A curved front edge would be measured on its
developed arc; on this villa every front edge is straight (the round stair's are radial lines).

## 2. Result: flight table (a) (FLIGHT_TABLE_T412.csv, 11 flights; NOSING_TABLE_T412.csv, 89 edges with handles)

| Flight (levels) | Risers (source) | Treads | Landing / floor edges | Nosing lm DRAWING-CONFIRMED | HELD (beside, never the quantity) | Evidence |
|---|---|---|---|---|---|---|
| ST-01 MS1-L +1.00 -> +2.667 | 10 (A-A, plan 10) | 10 (9 + the first winder, front 485) | 0 | **11.450** = 10 x 1.150 - 0.050 | | DC DD CE CF C6 C7 C9 (5), C8 (5, drawn 0.575 to the cut break, edge = lane 298 .. 157 1.150), C5 485 (2; 485 also drawn as C4: once); CE notched by 2FBD |
| MS1-T winder turn +2.667 -> +3.50 | 5 (A-A) vs 4 wedges (arch plans) vs 12 + 3 split (ST p.4) | 4 | 1 | | 5 edges HELD: radial fronts 4A2 1.259, 49E 1.626, 4A0 1.259; 4th none; MS1-LD edge at band 2C6 (1.150) | CONFLICT (three sources, section 6): A-A 10 + 5, arch plans 10 + 4 wedges, ST p.4 12 straight + 3 radial, all 15 risers to +3.50; winders never generated (S-9) |
| MS1-U +3.50 -> 1F +5.50 | 12 (A-A), arch plans 11 lines, ST p.4 12 | 11 | floor 1 | **12.650** = 11 x 1.150 | floor edge HELD (1.150 beside): not on the arch plans, drawn on ST p.4 (459 at s 3.30), in the B20 head clash (Q-46 RFI) | A92 A95 AA5 .. AAC ABE |
| MS2-L 1F +5.50 -> MS2-LD +7.516 | 12 (A-A, plan 12) | 11 | landing 1 (A97) | **13.750** = 12 x 1.150 - 0.050 | | AC0 .. A97; AAE (s 1.2) notched by 3005 |
| MS2-TR closing riser +7.516 -> +7.684 | 1 (A-A) | 0 | landing 1 | | HELD: position not drawn | T-184 / T-393 / T-410 |
| MS2-U +7.684 -> 2F +9.70 | 12 (A-A), arch plans 11 lines, ST p.5 11 | 11 | floor 1 | **12.650** | floor edge HELD (1.150 beside): not drawn, B23 head clash | 135B 135E 136D .. 1374 1386 |
| D1 lobby +0.30 -> +1.00 | 4 (plan) | 3 | floor 1 (490) | **4.600** = 4 x 1.150 | | 481 484 48F 490 |
| ST-03 E1 +0.15 -> +1.00 | 5 (plan) | 4 | landing 1 (30A) | **14.000** = 5 x 2.800 | | 36E 36C 36A 30B 30A |
| ST-02 RS-C curved +1.00 -> +2.929 | 12 (plan, no section) | 12 | 0 | | 12 HELD (Q-50 A cond): radial fronts 11 x 1.150 + 256 1.200 (runs over the 50 mm outer band, RL-09) = 13.850 beside | 256 254 .. 240 radial (r 1.581 .. 2.731), NOT arcs |
| RS-S +2.929 -> RS-LD +4.696 | 11 (plan, no section) | 10 | landing 1 (B4D) | **12.500** = 11 x 1.150 - 3 x 0.050 | | B43 B4A .. B4D; B4A B49 B48 notched by 2FD2 |
| RS-A +4.696 -> 1F +5.50 | 5 (plan, no section) | 4 | floor 1 (D22) | **5.750** = 5 x 1.150 | | B59 B5A B5B B5C D22 |

Annex: no stair is drawn there (T-184 inventory); no row.

**Totals.** Risers 89 (ST-01 56, ST-02 28, ST-03 5) = nosings 89 (69 DRAWING-CONFIRMED, 20 HELD). Treads 80 (64
confirmed). Nosing **87.350 lm DRAWING-CONFIRMED** (ST-01 55.100, ST-02 18.250, ST-03 14.000): of it **79.950 lm on
treads** (inside the B7-06 commercial step basis, UP-STAIR-008) and **7.400 lm on landing / floor edges** (MS2-LD 1.150,
D1 floor 1.150, E1 platform 2.800, RS-LD 1.150, RS-A floor 1.150; outside any step). HELD 20 edges, 21.444 lm drawn
beside the blanks (winder fronts 4.144 + band 1.150, two floor edges 2.300, RS-C 13.850). Nothing is released.

Hand checks (independent of the code, every term a drawn length): 11.45 + 12.65 + 13.75 + 12.65 + 4.60 = 55.10; 12.50 +
5.75 = 18.25; 5 x 2.80 = 14.00; 55.10 + 18.25 + 14.00 = 87.35. Winder fronts by Pythagoras on the drawn ends: 49E from
the inner corner to the outer corner hypot(1.150, 1.150) = 1.626; 4A2 / 4A0 hypot(1.150, 0.512) = 1.259.

Second drawing (structural DXF, own count): every stair line on the slab plans is 1.150 too; MS2-L 12, D1 4, RS-C 12
radial lines agree with the architectural plans (handles 2DF .. 2EA are 12 lines, as T-415 MERGED 8c8372a4 counts them;
T-398's '13' is superseded there); MS1-U shows its 12th
(floor) edge on ST p.4 where the architectural plans stop at 11; MS2-U has 11 on both. MS1-L is the one disagreement:
ST p.4 draws 12 straight lines over 3.30 m ending at the same inner winder corner as the architectural 485, i.e. two
more straight steps at the foot and only three radial fronts, where the architectural plan draws 10 over 2.70 (wall
220 1.10 m south of DC, nothing between) and section A-A five winders. The 10 architectural edges lie at the same
positions from the corner in both readings, so they stay DRAWING-CONFIRMED; the two edges that are straight steps in one
reading and winders in the other are inside the HELD turn.

Width correction worth naming: the merged inventory (T-184) gives ST-01 / RS-S a width of 1.20 (the structural lane);
every drawn marble front edge is **1.150** (wall face to the well band; RS-S from the outer band A7 to the void band).
The 0.050 is the band, not tread. This touches B7-02 / B7-06 too (cross-trade note, section 6).

## 3. Checks of acceptance (c): one edge, one item

- Nosings are FRONT edges across the width; railings (B7-09) and skirting (B7-07 / B7-08) run along the SIDES: no edge
  id of this table is a T-410 side id or bound to one (pin test), and every edge binds to B7-05 only (refused in code).
- B7-06 commercial step (UP-STAIR-008) "covers tread, riser and nosing together": the 79.950 lm of tread nosings are
  INSIDE that basis and must never be priced beside it; only the 7.400 lm of landing / floor edges lie outside any step.
  This is the real overlap risk of B7-05 and the reason the lane I line carries the split (section 7).
- A landing is never also a tread: a LANDING / FLOOR edge in the middle of a flight is refused in code; every landing /
  floor edge here is the top nosing of its flight.

## 4. Binding to the candidate V3.0.35 and who is right per flight (CANDIDATE_BINDING_T412.json)

Candidate of record reproduced this run (research/agents_t400/v3035_run.py on the Drive copies; V3_0_35_BOQ_LINES.json
sha256 b011bace.., 4730 lines, the same file T-418 bound): **no nosing line exists** (0 lines; B7-05 NOT_IN_CANDIDATE).
Its stair lines come from the engine's tread polygons, whose own note reads "the n drawn tread lines bound n - 1 treads;
if the top line is a nosing ... one more tread is not drawn". Each engine flight is bound to a drawn flight by the
engine's cross-plan repeat record (overlap 1.0) and its kind / lines / run / layer:

| Drawn flight | Candidate TREAD line (state) / STEP_LM line | Engine treads | Drawn treads | Verdict proposal (B7-02 / B7-06 owner row; B7-05 binds here) |
|---|---|---|---|---|
| MS1-L | L-151d92470a81dd1c450b (PROVISIONAL 2.415) / L-d4d764ae7bb07b474b6f 8.050 | 7 | 9 straight + first winder | ENGINE_WRONG -2 straight treads: it reads the 8 hidden riser-face lines DE .. CD; C5 and 485 (hidden, above the cut) front two more treads (A-A 10 risers) |
| D1 | L-a4aeb32035d11684f1a2 (PROVISIONAL 1.035) / L-f20f8544a42807c0cfcf | 3 | 3 | AGREE |
| MS1-U | L-e1eb8b9a7cb92508ccc9 (PROVISIONAL 3.450) / L-0aa47300a16de572c967 11.500 | 10 | 11 | ENGINE_WRONG -1: 11 front edges A92 .. ABE; the 11th tread ends on the undrawn floor edge (A-A 12 risers, ST p.4 459) |
| MS2-L | L-65806b4d02d476603bc5 (PROVISIONAL 3.795) / L-23651ecfef77992ec8d4 12.650 | 11 | 11 | AGREE |
| MS2-L seen from 2F | L-79beb9688604887c59c5 (PROVISIONAL 3.450) / L-1e88ac0d4ba0b4e8a950 11.500 | 10 | 0 (no flight of 2F) | ENGINE_WRONG: the same flight valued twice (T-129, R-STAIR-CONT-1) |
| MS2-U | L-07f00d5b0c4e1924aaf5 (PROVISIONAL 3.450) / L-60fc97c4306696c74c38 11.500 | 10 | 11 | ENGINE_WRONG -1 (11 lines 135B .. 1386) |
| RS-C | L-fa534ec5f9dc14947899 (PROVISIONAL 4.094) / L-95b9555dd144951b071e 13.796; 1F exposure L-6cf11c2d30387d0942b9 | 12 | 12 (HELD, Q-50 A cond) | count AGREE; valued where the owner holds the curved part (B7-02 row) |
| RS-S | GF L-89c84fdd4964dec8a323 (6) + L-0ec429f1783f1f15e700 (3, bound by elimination) PROVISIONAL; 1F exposure L-ea55ed317bc4de89aec1 (10) | 9 valued | 10 | ENGINE_WRONG -1 on the valued GF reading; the 1F reading (10) agrees |
| RS-A | GF L-1dac5d9b574d7608d80d (PROVISIONAL 1.035, 3); 1F exposure L-5d338389185d72a6fb16 (4) | 3 valued | 4 | ENGINE_WRONG -1 on the valued GF reading; the 1F reading (4) agrees |
| (none) | 1F flight 5 L-b4660de0ddd98ad0ffc2 (PROVISIONAL 1.495, RADIAL 4, width 1.247) | 4 | - | UNBOUND: matches no drawn flight on 1F (no radial line at RS-LD); B7-02 owner row |
| E1 | L-314c3ac6d45431b687c5 (SOURCE_DERIVED 3.3594 = 4 x 0.30 x 2.80) | 4 | 4 | AGREE |

The risers (FIN.MARBLE.RISER) and flight lines of each element are in the binding file beside the tread lines.

## 5. Freelancer comparison (b), quantities only

His stair rows are PIECES ('count'), one per step, with a width per piece and no nosing row at all (his nosing is inside
his step piece, as UP-STAIR-008's commercial step): entrance 5 x 2.80, main stair 63 x 1.20, inner (round) stair 28 x
1.20.

| Stair | His pieces | Ours: risers = nosings (treads + landing / floor edges) | Difference | Verdict proposal |
|---|---|---|---|---|
| ST-03 entrance | 5 (x 2.80) | 5 = 4 treads + platform edge 30A (x 2.800) | 0 | AGREE (count and width): his piece = one riser / nosing |
| ST-02 round | 28 (x 1.20) | 28 = 26 treads + RS-LD edge + 1F floor edge (12 + 11 + 5 risers) | 0 pieces; width 1.20 vs drawn 1.150 (-0.050 per piece) | AGREE on count; on width ENGINE_RIGHT on the drawn front edge (the 0.050 is the outer / void band, RL-09 open) |
| ST-01 main (+ D1) | 63 (x 1.20) | 56 = 50 treads + 6 landing / floor edges (27 GF -> 1F + 25 1F -> 2F + D1 4) | **+7 his (+12.5 %)** | UNRESOLVED: every reading of 63 tested fails (risers 56, treads 50, risers without D1 52, 4 flights x 12 + 5 winders + D1 4 = 57); no breakdown in his row. Width: ENGINE_RIGHT 1.150 drawn vs his 1.20 |
| B7-05 nosing | no row | 87.350 lm confirmed (7.400 lm outside any step) | n/a | RULE_DIFFERENCE: he carries no separate nosing (inside his step piece); the owner lists nosing as an item (s.1) |

## 6. What stays open (designer / owner facts; no owner question raised)

ERS s.2.7 is not met for a new question: the counts conflicts are designer facts already on the list, and the nosing form
is a specification not printed. Proposed rfi rows (drafts, nothing sent; the Lead places them):

1. Nosing specification (architect): the plans draw a 0.050 projection on every flight; profile and whether the nosing is
   a separate piece or the tread's worked edge are not printed. Affects the B7-05 specification only (87.350 lm stand).
2. NEW evidence for C-ST-3 (architect + structural): GF -> +3.50 of ST-01 is 15 risers on every source, split 10 straight + 5
   winders on section A-A, 10 straight + 4 wedges on the GF plan, 12 straight + 3 radial on the structural GF roof slab
   plan (45A .. 25E, 2F6 / 2F4 / 2F5): which is built? Affects 5 nosings (4.144 lm of drawn radial fronts or 2 x 1.150
   straight), the turn's marble and concrete. Nothing measured from either reading until answered.
3. Existing, unchanged: the ST-01 winder turn (A-A 5 risers vs plans 4 wedges, C-ST-3), the 1F / 2F arrival edges in the
   B20 / B23 head clash (Q-46 RFI), MS2-TR position, RS-C (RFI-S27) and the RS-C first edge over the outer band (RL-09).

Cross-trade notes (not this task's quantity; owner trade A):
- B7-02 / B7-06: the engine's GF stair room flight reads 7 of the 9 straight MS1-L treads (-2 x 1.150 = -2.300 lm of step,
  -0.690 m2 of tread): a tread above the plan cut is still a tread (layer 2); each east lane (MS1-U, MS2-U) 10 of 11
  (-1.150 lm, -0.345 m2 each): the last tread is bounded by an undrawn floor edge.
- B7-02 / B7-04: tread / landing marble at the 5 notched edges is short by 0.050 x going (T-410 note, 0.1175 m2).

## 7. Lane I proposal (no candidate change in this task)

One B7-05 line set bound per flight to the candidate's stair lines (the tread / step line of the same flight, T-418
binding where it exists), never valued twice:
- a FIN.STAIR.NOSING (name for lane I) line per flight valued at the DRAWING-CONFIRMED lm of NOSING_TABLE_T412.csv, with
  two fields: `in_step_basis_lm` (tread nosings: NOT priced where B7-06 FIN.STAIR.STEP_LM is priced, UP-STAIR-008) and
  `landing_floor_edge_lm` (7.400 lm, outside any step); specification HELD NOSING_FORM_NOT_PRINTED;
- HELD lines blank with their cause and the beside figure: MS1-T (5 edges), MS1-U / MS2-U floor edges, MS2-TR, RS-C (12);
- the tread count findings for B7-02 / B7-06 (section 4: MS1-L +2, MS1-U +1, MS2-U +1, RS-S +1 and RS-A +1 on the valued
  GF readings, MS2-L valued twice, 1F flight 5 unbound) go to the B7-02 owner row, not into B7-05.

## 8. Rule, test, lesson

- **R-T412-1** (proposed, research, any villa): one riser, one nosing: per flight, nosings (drawn or held) = risers from
  the governing count; the top nosing is a landing or floor edge, never a tread, and a landing / floor edge in the middle
  of a flight is refused; treads are the TREAD / WINDER nosings, never n - 1 / n arithmetic.
- **R-T412-2**: the nosing length is the drawn FRONT edge (straight: its length; arc: the developed arc, never the chord;
  winder: the radial edge, never the lane width), less a face proud inside the width on that edge over [c0, c1).
- **R-T412-3**: a drawn tread above the plan cut (hidden layer) is a tread; a front edge drawn twice is one edge; a
  front edge broken by the cut symbol is the lane width, asserted against the flight's other edges.
- **R-T412-4**: the commercial step lm (UP-STAIR-008) contains the tread nosings: B7-05 reports them split from the
  landing / floor edges, so the nosing is never priced twice.
- Tests `tests/t412_nosing_census` (normal + adverse): Villa K412 hand fixture (7.920 / 8.000 lm, a column notch, landing
  and floor edges); adverse: curved edge on the chord refused, landing counted as a tread refused, generated winder and
  a section-only winder refused, count mismatch refused, held as 0 / held without cause refused, mm as m and 'cm'
  refused, edge bound to a railing or to B7-06 refused, non-parallel edges refused; rotation / mirror / mm invariance;
  Alsenan pins (reproduces from the committed edges, totals hand-checked, 89 edges = 89 risers, notched set, no edge
  shared with T-410).
- Lessons-register row proposed:

| 2026-11-01 | the engine reads 7 of the 9 straight treads of MS1-L and 10 of 11 on each east lane; T-184 gives 1.20 lanes where every marble front edge is 1.150 | tread polygons taken between solid lines only (a tread above the plan cut is drawn hidden; a last tread ends on an undrawn floor edge); the structural lane width reused for marble | one riser, one nosing; treads from every drawn front edge on BOTH layers (solid and hidden), duplicates once; marble width from the drawn front edge, never the structural lane (any villa) | tests/t412_nosing_census | T-412 |

## 9. Self-gate and what is missing

self-gate: a (research + tests only; no engine / rule / candidate file) c (non-Alsenan K412 hand fixture, adverse cases)
d (reproducible: `python3 -I research/agents_t412/t412_alsenan.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf>
--candidate <run>/v3035/V3_0_35_BOQ_LINES.json --write`; `--check` without private input) f (nothing wired, no item code created) h (handles, run positions and lengths only; no coordinates, no drawing
text, no client data) PASS.
Missing: the nosing form (not printed); the winder count conflict; the two arrival edges in the head clash; MS2-TR; RS-C.
