# T-124 Membrane offcut booked once: audit of every owner Q-58 A roll count, and MEMBRANE_FOLD_V5

Worker 2, 2026-10-20. Code: `engine/source/membrane_fold_v5.py` (new; opt-in, read by no released method),
tests `tests/t124_membrane_offcut_once` (16), read-only Alsenan runner `research/agents_t124/alsenan_t124_run.py`,
every Alsenan cutting plan in `T-124_ALSENAN_Q58A_PLANS.csv` (220 rows: each piece on its roll with position and source,
each leftover). MEMBRANE_FOLD_V3 / V4, ARCH_TAKEOFF_V2.12 / V2.13 and every frozen file untouched; no rule record added.
Rules: owner Q-49 A (each area alone), Q-58 A (conditional: offcuts of the same area, a proven plan), Q-24, Q-30, Q-35 C,
UP-WP-001 / 002 / 003 / 005, UP-QTY-STATUS-001. Not an accuracy claim (Alsenan is the development villa).

## 1. The defect (general to every villa)

`MEMBRANE_FOLD_V3.counts` (V4 calls it) books the pieces it takes from offcuts in the leftovers of the main strips'
packing alone, then packs the pieces that found no offcut together with the main strips into new rolls. That second
packing can put a piece into the same roll end the first step had already promised away: the count is too low and no
cutting plan reaches it. Hand case D1: one main strip 1.00 x 7.00 m and four 1.00 x 1.00 m pieces: V3 promises three
pieces to the 3.00 m roll end, then packs the fourth on the same roll (7.00 + 1.00 = 8.00 m) and claims **1 roll**;
the roll then has 2.00 m of end for three 1.00 m pieces, and 7.00 + 4.00 = 11.00 m2 > 10.00 m2: **2 rolls** by hand.

## 2. What V5 does

One set of rolls: pack the pieces cut from rolls, lay each roll out (longest piece first), list its real offcuts (full-
width roll end; side trim beside every piece narrower than the roll), place every other piece (largest first) in the
smallest offcut that holds it, no turning; an offcut is split once (length beyond, width beside), so it shrinks after
every piece and is never used twice. A piece no offcut holds is cut from a roll and everything is packed and placed
again until every piece has a place (ends at the latest at the Q-58 B packing, so A <= B always). The plan is checked on
the rectangles (inside the roll, no overlap, every piece once) or the fold fails; a piece longer than a roll is never
counted as one roll (layout HELD on that reading). The V5 plan of fixture R, written back as a V3 count, is proven by
ARCH_TAKEOFF_V2.13's own proof code (independent check, tested).

Audit (`audit_v3`): a V3 / V4 Q-58 A count is VALID when its own-offcut pieces can be placed on the rolls V3 itself packs;
INVALID when that is proven impossible (a piece larger than every offcut; pieces wider than every trim and half the roll
needing more roll end than the rolls leave; more piece area than offcut area; a piece longer than a roll); NOT_PROVEN
otherwise. The corrected count books the same pieces once.

Ledger per layout, kept apart: installed m2 (floor + 0.20 m upturn with mitred corners + opening upturns), floor m2,
upturn m2, gross cut m2 (every piece as cut), lap m2 (side / splice laps + the upturn pieces' laps), trim m2 (strip beyond
the surface + rectangle trim of patch pieces), offcut left m2 (= rolls x 10 m2 - gross cut), rolls; balance check
installed = gross - lap - trim (all 21 Alsenan areas balanced within 0.000001 m2).

## 3. Hand fixtures (none is the development villa)

| Case | Hand | V3 / V4 | V5 |
|---|---|---|---|
| D1 1.00 x 7.00 main + four 1.00 x 1.00 | 2 rolls (11.00 m2 > 10.00) | V3 claims 1: INVALID (end 2.00 m for 3.00 m of pieces; 3.00 m2 > 2.00 m2) | 2, plan checked |
| D1' 1.00 x 8.00 main + two 0.45 x 2.00 | 1 roll: both side by side in the 1.00 x 2.00 end (y 0-0.45, 0.45-0.90) | end-length test does not misfire | 1 |
| D2 1.00 x 6.00 main, patch 0.60 x 1.50, upturn 0.30 x 2.50 | 1 roll; patch at x 6.00-7.50, end shrinks to 1.00 x 2.50, upturn at x 7.50-10.00; left 0.70 x 2.50 + 0.40 x 1.50 = 2.35 m2 | VALID | 1, exactly these positions |
| D3 patch 0.40 x 12.00 | no roll holds it | V3 counts it as a roll | HELD on A / B, never 1 roll |
| X 11.00 x 5.50 less 1.00 x 3.00, V3 layout along / lower | V3's pieces (4 x 1.00 x 1.00): 76.50 + 4.00 = 80.50 m > 80 -> 9 | claims 8: INVALID (2.50 m end, 3 x 1.00 m wide) | V3's pieces once: 9; V5's own pieces (last patch piece 3.10 - 3 x 1.00 = 0.10 m wide, into a 0.50 m trim): 8, a real plan |
| R 10.00 x 6.00 less 7.50 x 3.15 (as drawn, mirrored, 90 deg, mm) | A 5, B 6, C 6; installed 36.375 + 0.20 x 32.00 + 0.04 x 4 = 42.935 m2; gross 47.475; laps 4.205 + 0.335 = 4.54; offcut left 2.525 | VALID | identical counts and ledger |
| Rectangle 4.50 x 3.00 | 2 rolls; installed 4.90 x 3.40 = 16.66 m2; gross 3.70 x 4.90 = 18.13 | VALID | RELEASED 2 |

## 4. Development villa (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip, ARCH_TAKEOFF_V2.13 with the pantry
4.50 x 3.00 typed as in T-120): every audited count

The run reproduces the verifier's V2.13 figures (wet areas 21 rolls, 2F roof 17 RELEASED_Q58_A, 1F roofs 6 + 8; 579 lines).

| Count audited | Claimed | Audit | V5 (one set of rolls) |
|---|---|---|---|
| 18 wet areas incl. the pantry (V2.11 / V2.12 19 rolls, 21 with the pantry) | 21 | all 72 V3 layouts VALID; every V4 wall-frame layout VALID | 21 (GF 11 + 2 pantry, 1F 7, 2F 1), each = its lower bound |
| 1F roof 32.72 m2 | 6 | VALID | 6 (A = B = C) |
| 1F roof 55.56 m2 | 8 | VALID | 8; one corner piece 0.12 x 0.17 in the 0.60 x 3.76 trim of strip 8 |
| 2F roof 115.83 m2 (T-114 hand plan 17) | 17 (A), 18 (B / C) | VALID in the chosen V3 layout and in every other V3 layout | 17 (lower bound 16), plan checked: the 0.30 x 4.60 step band in the 0.70 x 6.97 side trim of strip 24 (roll 17, 0.40 x 4.60 and 0.70 x 2.37 left), the 8 dome-opening pieces (4 x 0.118 x 0.277 and 4 x 0.049 x 0.028) side by side in roll 7's 1.00 x 0.33 end; rolls 15-17 each 6.97 used, 3.03 m end left |
| T-104 wall-frame layouts (V4) | - | all VALID except one layout not chosen anywhere: 2F roof, frame 0.82 deg, opposite wall: V4 counts A 19 / B 19 with a 0.38 x 12.38 m corner piece longer than a roll | that layout HELD on A / B (C 18); choice unchanged |

No released or proven count was wrong: the double booking needs an area where some pieces fit an offcut and others do
not, which no Alsenan area has. 2F roof ledger (V5, the 17-roll layout): installed 134.33 m2 (floor 115.83 + upturn
18.49), gross cut 154.73 m2, laps 14.14 m2, trims 6.27 m2, offcut left 15.27 m2, 170.00 m2 bought. All wet areas:
installed 120.51 m2 (floor 85.62 + upturn 34.89), gross 134.43, laps 9.55, trims 4.37, offcut left 75.57, 21 rolls =
210 m2. Roofs (2F top roof held, owner Q-34): installed 240.65 m2, gross 277.75, laps 25.28, trims 11.81, offcut left
32.25, 31 rolls.

Freelancer (development reference only): wet floor 72.01 m2 vs engine 85.62 m2 (+13.61 m2, +18.9 %; RULE_DIFFERENCE:
owner Q-37 A waterproofs the 13.50 m2 pantry, the freelancer does not; unchanged from T-120). Roof membrane 285.00 m2
vs engine installed 240.65 m2 on the three released roofs (-44.35 m2, -15.6 %; not comparable while the 2F top roof is
HELD on Q-34). The freelancer gives no roll counts: rolls not comparable.

## 5. Learned, missing

- A roll count is only as good as its plan: count and placement must be made on the same rolls. V2.13's proof already
  guards releases; V5 makes the A count itself constructive.
- Second V3 / V4 defect found: a patch longer than a roll (a 0.82 deg frame leaves a 12.38 m sliver along a wall) is
  counted as if it fitted one roll. V5 holds such a layout; the sliver itself (a frame-angle artefact or a real strip)
  is not settled here.
- V3 cuts every piece of a patch wider than the roll at the full roll width; V5 cuts the last piece only as wide as is
  left (fixture X: 8 rolls instead of 9 with V3's pieces).
- Not done: wiring V5 into a method version (V2.14) and the purchase table; V5's placement is greedy (largest first,
  smallest offcut), so a count above its lower bound is not proven minimal (2F roof 17 vs bound 16, as by hand).
