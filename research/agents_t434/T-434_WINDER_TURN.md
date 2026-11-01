# T-434 ST-01 MS1-T winder turn: governing riser count, turn pieces, and the freelancer 63 vs 56 (development villa; method every villa)

Worker 2 (lane A), 2026-11-01. Research files `research/agents_t434/*` and `tests/t434_winder_turn/` only; no engine, rule,
knowledge, method, registry or candidate file touched; no candidate quantity changed (lane I proposal, section 8). ERS
applied (s.2.1 physical element, s.2.2 evidence hierarchy, s.2.3 first principles, s.2.4 reconciliation in units, s.2.7
escalation test, s.4 rule + test, s.7 lesson). Rules: Q-46 A (section A-A counts for ST-01; plans are checks + RFI),
Q-51 A cond (winder concrete on the drawn combined area), OWNER_RULE_STAIRS_2026-10-24 s.1 (finished riser 0.15 - 0.17,
going 0.28 - 0.30 as CHECKS), s.4 S-4 (8) (drawn dimensions govern, conflicts flagged), S-8, S-9 (winders never generated;
missing winder geometry HELD), T-267 acceptance A8 (drawn winders with a dimension missing: winder geometry AND its marble
HELD), UP-STAIR-002 / -005, R-T412-1 (one riser, one nosing), R-T425-1..3, WORKFLOW_CONTROLS s.5. No image, client name,
drawing text or workbook row text is copied here.

## 0. What was read (own reading this run)

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF), decoded into `.work/private` only, BY HANDLE | MS1-L fronts DC .. C5, 485 (= C4), riser face 486; radials 4A2 / 49E / 4A0 (riser faces 4A3 / 49F / 4A1); landing nosing 2C6 (= 49C) and riser face 49D; north wall 26E / 2AB; the well band lines 153 / 154 / 151 / 152 / 47F / 150; a sweep for any line on the inner edge north of 486 (none) |
| Drive "ST7757 dxf.dxf" (structural DXF), `.work/private` only, BY HANDLE: SECOND DRAWING | ST p.4 riser-face lines 45A .. 25E (12, layer 2), radials 2F6 / 2F4 / 2F5, closing riser face 2F3, opening band 256 / 25A |
| Drive p7757_arch_sheet10.pdf (section A-A), `.work/private` only, rasterised at 800 dpi (not stored) | the dashed winder treads under the half landing, scaled between the printed finished lines +0.30 and +3.50 (printed '320'): 314.84 px/m |
| research/agents_t412, agents_t425 (MERGED f9c80501, 6f159091), agents_t184, alsenan_stairs_s8_7c (S-04 section foot, scaled; ground-beam plan foot) | built on and cited, not re-derived; the section foot position and the ground-beam plan foot are cited from s8_7c |

## 1. Physical element (ERS s.2.1)

ST-01, GF, west lane of the dog-leg: MS1-L rises north from GF FFL +1.00; the TURN is the part between the front of the
first winder and the nosing of the half landing MS1-LD (printed +3.50, section A-A '+0.30' + '320'); MS1-U then rises
south to 1F +5.50. Installed items of the turn (trade A): winder TREADS (marble, m2 and pieces), RISERS (pieces; their m2
basis is BLOCKED_RFI in the candidate), NOSINGS (one per riser, lm), commercial STEP lm (UP-STAIR-008). Its concrete
(Q-51 A cond) is lane S.

What is drawn, by handle (architectural GF plan, layer 2 = above the cut):
- The straight part: 10 front edges at run 0 .. 2.700 in 0.300 steps, DC .. C5 and 485 (485 drawn twice, as C4; its
  riser face 486 0.050 uphill). 485 fronts the FIRST winder (T-425).
- The turn square: from riser face 486 to the north wall face (1.150) over the lane (wall face .. inner edge, 1.150). Three
  radial fronts leave the inner corner (the end of 486 on the well edge): 4A2 to the west wall 0.5115 north of 486
  (hypot(1.150, 0.5115) = 1.258652), 49E to the NW corner (hypot(1.150, 1.150) = 1.626346), 4A0 to the north wall
  0.5115 from the corner line (1.258652); each with a riser-face companion 4A3 / 49F / 4A1.
- The landing nosing: 2C6 (drawn twice, 49C) 0.100 east of the inner edge, 1.150 long from 486 to the north wall, with its
  riser face 49D 0.050 further east (uphill, the landing side): the same front + face pair as every one of the 89 edges of
  T-412. No line runs on the inner edge north of 486 (swept by handle), so the 0.100 strip between the inner edge and 2C6
  is walking surface of the last winder, not band.
- Structural ST p.4 (own handle read): 12 riser-FACE lines 45A .. 25E at 0.300 over 3.300; its three radials 2F6 / 2F4 /
  2F5 coincide within 1 mm with the architectural riser faces 4A3 / 49F / 4A1 once 25E is put on 486; its closing line 2F3
  coincides with 49D. So ST p.4 draws the SAME turn (3 radials + closing riser) and the same landing edge, and 12 straight
  risers whose foot lies 0.600 south of the architectural DC.

So the turn REGION (front 485 to front 2C6) is drawn identically on both plans; what differs is the riser COUNT (section)
and where the extra straight risers go (ST p.4).

## 2. Reading table (winder_turn.governing; ALSENAN_TURN_T434.json)

Rise GF FFL +1.00 -> half landing +3.50 = 2.500 m, uniform finished risers; going 0.300 on every sheet.

| Reading | Straight + turn risers | Riser (check 0.150 - 0.170) | Straight run (drawn plan run 2.700) | Foot (other drawings) | Winder tread levels vs section's drawn dashed treads | Verdict |
|---|---|---|---|---|---|---|
| Section A-A | 10 + 5 = 15 | 0.166667 PASS | 2.700 | -2.734 (scaled, s8_7c S-04) agrees with the arch plan -2.700 (34 mm, scaled) | predicted 2.6667 / 2.8333 / 3.0000 / 3.1667 / 3.3333; drawn 2.6663 / 2.8314 / 3.0013 / 3.1665 (+3.333 lies on the cut landing slab's soffit line): worst miss **0.0019 m** PASS | **GOVERNING** |
| Arch GF plan | 10 + 4 = 14 | 0.178571 **FAIL** | 2.700 | -2.700 agrees with the section | 2.7857 / 2.9643 / 3.1429 / 3.3214: miss **0.1549 m** FAIL | REJECTED (riser, levels) |
| ST p.4 | 12 + 4 = 16 | 0.156250 PASS | 3.300 | -3.300: agrees with no other drawing (0.600 south; the ground-beam plan also puts the foot at DC, s8_7c) **FAIL** | 2.8750 / 3.0312 / 3.1875 / 3.3438: miss **0.2087 m** FAIL | REJECTED (levels, foot) |

Own scaling of the section (not a quantity): the two finished-level lines sit 1,007.5 px apart for the printed 3.20 m
(314.84 px/m at 800 dpi = 1:100 on the sheet); the four dashed treads lie 52 - 54 px apart (one riser = 52.5 px). They
match 15 uniform risers from +1.00 within 2 mm and miss both other readings by 0.15 - 0.21 m.

## 3. Governing reading and its reason (ERS s.2.2; never "best fit")

**Section A-A governs the turn count: 5 risers (11 .. 15), GF -> 1F 27 = 10 + 5 + 12, finished riser 166.7 mm.**
Governing reason: the answered owner rule Q-46 A names the section for ST-01. Its acceptance here is not "it fits best":
it is consistent with the other drawn evidence (its own dashed treads within 2 mm; its foot agrees with the
architectural plan; its straight run equals the drawn 2.700). The checks are reported, never used to choose: ST p.4
passes the riser check (156.25 mm) and still is not taken, because its foot and its tread levels contradict three other
drawings. The architectural plans' 4-riser turn gives 178.6 mm and misses the section's drawn treads by 155 mm.

What this settles and what it does not:
- SETTLED (DRAWING-CONFIRMED): 5 turn risers, 5 turn nosings (4 winder fronts + the landing nosing), 5 winder treads
  (W1 behind 485, which is MS1-L's 10th front, W2 .. W5 behind turn risers 11 .. 14; riser 15 reaches the landing).
- SETTLED (DRAWING-CONFIRMED): the landing nosing 2C6, **1.150 lm**: drawn as a front + riser-face pair on the
  architectural GF plan and at the same position (riser face 2F3 = 49D) on ST p.4; its position does not depend on the
  count (every reading reaches the landing at it).
- NOT SETTLED: the plan SUBDIVISION of five winders. Every plan draws three radial fronts (a 4-riser turn); no sheet draws
  the four winder fronts a 5-riser turn has. Winders are never generated (S-9) and a missing winder dimension holds the
  winder geometry and its marble (A8). So the 4 winder fronts (lm), the turn tread marble (m2), the turn step lm and the
  per-piece shapes stay **HELD**, with the drawn figures beside: drawn fronts of the 4-riser subdivision 4.144 lm (never
  the 5-riser figure); the drawn turn region **1.495 m2** = 1.150 x 1.200 (front 485 to the north wall over the lane) +
  0.100 x 1.150 (the head strip to front 2C6) = 1.380 + 0.115. The region is the same whatever the subdivision (all five
  winders lie between front 485 and front 2C6), so it is the combined installed area once the subdivision is drawn; it
  is not released now because A8 holds winder marble while the winder geometry is missing.

## 4. Before / after (installed quantities; nothing released; no candidate change in this task)

| Item (B7 owner row) | Before (T-412 / T-425 MERGED) | After (T-434) | Change |
|---|---|---|---|
| Turn riser count | CONFLICT: 5 (A-A) vs 4 (plans) vs 12 + 3 split (ST p.4), all HELD | **5** DRAWING-CONFIRMED (section A-A, Q-46 A, consistent) | conflict closed |
| B7-05 nosing, turn | 5 edges HELD (count conflict) | 5 pieces confirmed; landing nosing **1.150 lm DRAWING-CONFIRMED**; 4 winder fronts HELD (beside 4.144 lm on the drawn 4-riser subdivision) | +1.150 lm confirmed |
| B7-05 nosing, all ST | 87.350 lm confirmed (7.400 on landing / floor edges), 20 edges HELD (21.444 lm beside) | **88.500 lm** confirmed (**8.550** on landing / floor edges), **19** edges HELD (20.294 lm beside) | +1.150 lm (+1.32 %) |
| B7-02 tread marble, turn | HELD beside 1.495 m2 (candidate 1F F5 L-b4660de0ddd98ad0ffc2 PROVISIONAL 1.495, 4 RADIAL treads) | HELD (A8), beside **1.495 m2** now traced to the drawn region (hand above); **5** pieces | m2 unchanged (HELD); pieces 4 -> 5 |
| B7-06 step lm, turn | HELD beside 4.7815 (L-e085..) | HELD: needs the 4 winder fronts; only the landing nosing 1.150 is drawn | unchanged |
| B7-03 riser pieces, GF -> 1F | 27 (A-A) with the turn in conflict | 27 = 10 + 5 + 12 confirmed; riser m2 stays BLOCKED_RFI (height basis open in the candidate) | count confirmed |

Engine vs drawing: the candidate's 1F F5 reading (the turn seen from 1F, T-425) carries 4 RADIAL treads where the
governing count gives 5 winder treads: **ENGINE_WRONG -1 piece** (it reads the 4-riser subdivision the plans draw); its
1.495 m2 equals the drawn region (its own footprint basis not traced here); it stays HELD (A8), as T-425 proposed.

Cross-trade note (lane S, not this task's quantity): Q-51 A cond accepts the winder concrete as 0.5 x riser x the real
combined plan area of the five steps. The drawn combined area is not 1.44 (1.20 x 1.20) but, between the riser faces 486
and 49D, 1.150 x 1.300 = **1.495 m2**, with no landing or void inside (no line on the inner edge north of 486). Lane S
decides its own concrete with its own evidence (waist).

## 5. Freelancer ST-01 63 pieces vs drawn 56 (quantities only)

Drawn ST-01 risers (section A-A, Q-46 A): GF -> 1F 27 (10 + 5 + 12) + 1F -> 2F 25 (12 + 1 + 12) + D1 4 = **56**; his
row: **63** pieces (+7, +12.5 %). Restated on the governing turn: every combination of drawn readings, per storey
GF -> 1F 25 .. 28 (arch / section / ST p.4), 1F -> 2F 24 .. 27, D1 4, gives **53 .. 59** pieces (`reach`): 63 is no
reading of any sheet and no mixture of them, so the turn conflict cannot be its cause (it moves the total by at most
1 piece between readings, and the governing reading is already in the 56). The only reproduction remains T-425's
storey-rise / 150 - 155 mm riser estimate (5 + 30 + 28 = 63). Proposal: **ENGINE_RIGHT on 56** (all drawings bound it
to 53 .. 59; the governing one gives 56), freelancer +7 **RULE_DIFFERENCE (estimate by assumed riser), cause not proven**
(his row has no breakdown); residual named: 7 pieces x 1.20 = 8.400 lm of his step basis.

## 6. Designer RFI draft (ERS s.6 format; NOT an owner question: ERS s.2.7 not met, the count is settled by Q-46 A
and the subdivision is a missing designer dimension; the Lead places it on the designer list beside C-ST-3)

- Issue: the five winders of the ST-01 GF turn (section A-A) have no plan subdivision.
- Evidence: section A-A dashed winder treads at +2.667 / +2.833 / +3.000 / +3.167 (+3.333 behind the landing slab),
  half landing +3.50; architectural GF plan and ST p.4 draw three radial fronts + the landing nosing (a 4-riser turn) in
  the same 1.150 x 1.150 square at the riser face of the 10th riser.
- Investigation: 15 risers of 166.7 mm to +3.50 established (Q-46 A + the section's own treads within 2 mm); the 4-riser
  plan turn gives 178.6 mm and misses the drawn treads by 155 mm; the 12 + 4 structural reading moves the foot 0.600 south
  against three drawings.
- Alternatives: (a) the designer draws the five winder fronts in plan; (b) the designer confirms a 4-riser turn and
  revises the section and levels (then the GF -> 1F riser is no longer uniform 166.7 mm).
- Quantity impact: 4 winder nosings (beside 4.144 lm on the drawn 4-riser fan), turn tread marble 1.495 m2 in 5 pieces,
  turn step lm, 5 riser pieces; concrete wedge (lane S).
- Recommendation: (a), because the section is the governing count (Q-46 A) and is internally consistent.
- Status: those items HELD; landing nosing 1.150 lm, the counts and every straight-flight quantity continue.
- Next action: none needed from the owner.

## 7. Rule, test, lesson

- **R-T434-1** (research, any villa): a stair count governs only by a governing reason: the source an answered owner
  rule names, accepted when consistent with the drawn evidence of the other sheets (its drawn tread levels, the foot
  position another drawing draws); the owner riser / going ranges and the run are reported per reading as CHECKS and
  never select a reading; no rule or an inconsistent governing source -> HELD with the conflict named.
- **R-T434-2**: a winder turn's subdivision is measured only where a plan draws (governing count - 1) winder fronts;
  otherwise every winder front, the turn marble and its step lm are HELD (S-9, A8) with the drawn region area and the
  drawn fronts beside; the landing nosing is confirmed on its own when two drawings draw it at one position.
- **R-T434-3**: the turn region is front of the first winder to the landing nosing (front to front, as every straight
  tread); a strip with no line between the last winder and the landing nosing is walking surface, not band.
- Tests `tests/t434_winder_turn`: Villa K434 hand fixture (FFL +0.15, landing +2.55; section 9 + 6, plan 9 + 5, structural
  11 + 4 with the foot 0.600 south); normal: section governs, plan rejected on riser and levels, structural rejected on
  levels and foot although its riser passes; subdivision drawn for the governing count -> fronts 5.794168 lm and marble
  1.050 m2 confirmed. Adverse: 'winder count taken from the drawing that fits best without a governing reason' -> HELD,
  every quantity blank; rule source missing -> HELD (no fall-back to the passing structural riser); governing source
  inconsistent (levels / foot) -> CONFLICT; generated winder front refused; mm as m, missing values, a reading twice,
  zero counts refused; landing nosing on one drawing -> HELD (beside, never 0); rotation / mirror invariance; reach.
  Alsenan pins: reproduces from the committed JSON, the three readings, the section levels, the radial lengths by
  Pythagoras, the turn quantities and the freelancer reach.
- Lessons-register row proposed:

| 2026-11-01 | ST-01 GF winder turn held for days as a three-way count conflict (A-A 10 + 5, plans 10 + 4, ST p.4 12 + 3) although Q-46 A had answered which source counts | each reading was compared with the others, never tested against the physical checks and the governing rule together; 'conflict' was recorded where the rule plus one consistency test settle it | a count governs by the owner rule's source when it is consistent with the other drawn evidence (tread levels, foot); checks never choose; what stays open is named narrowly (here the plan subdivision of 5 winders, not the count) (any villa) | tests/t434_winder_turn | T-434 |

## 8. Lane I proposal (no candidate change in this task)

- MS1-T: keep the 1F F5 tread / step / riser lines (L-b4660de0ddd98ad0ffc2, L-e085.., L-820baecf7f726b4d8f1e) HELD with
  cause WINDER_SUBDIVISION_NOT_DRAWN (replacing the count conflict), pieces 5, beside 1.495 m2 (drawn region) and the
  drawn 4-riser fan 4.144 lm; never valued.
- B7-05 nosing set (T-412 proposal): the turn's landing nosing ST01-MS1T-N05 moves to DRAWING-CONFIRMED 1.150 lm in
  `landing_floor_edge_lm` (8.550 lm outside any step); ST01-MS1T-N01 .. N04 stay HELD (counts confirmed).
- Riser count GF -> 1F 27 confirmed for B7-03 pieces (m2 still BLOCKED_RFI).

## 9. Self-gate and what is missing

self-gate: a (research + tests only; no engine / rule / candidate file) c (non-Alsenan K434 hand fixture, normal and
adverse incl. the named best-fit case) d (reproducible: `python3 -I research/agents_t434/t434_alsenan.py --dxf
<P7757.dxf> --st <ST7757.dxf> --pdf <sheet10.pdf> --write`; `--check` without private input prints REPRODUCED) f
(nothing wired, no item code created) h (handles, run positions relative to the turn, lengths, levels and counts only;
no drawing coordinates, no image, no drawing text, no client data) PASS.
Missing / uncertain: the plan subdivision of the five winders (designer); the section foot is a cited scaled reading
(s8_7c S-04), not re-measured here; the freelancer's +7 has no breakdown in his row; the 1F -> 2F counts in the reach are
the merged Q-46 figures, not re-read in this task.
