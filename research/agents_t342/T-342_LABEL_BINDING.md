# T-342: census binding of the room labels no candidate line cites (M2 exit, rooms)

Worker 2 (lane A), 2026-10-29 12:58-13:50 UTC. Gate 1. Development villa, not an accuracy claim. Research only: no
engine module, rule, knowledge file, candidate line or released line changes. No client name, coordinate or image is
committed; the drawing is cited by Drive title and DXF entity handle.

Inputs, own this run: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55..) and
"ST7757 dxf.dxf" (9f9d1179..). Census `tools/label_census.py` (ARCH_TAKEOFF_V2.9 room set) reproduced **41 labels =
28 MEASURED / 1 HELD / 1 UNSUPPORTED / 11 NO_ROOM, 47 UNREAD_SHX** = the Checker's 10:00 statement (acceptance c).
Candidate: own `research/agents_t331/v3022_run.py` run: V3_0_21 json `be22a4e4`, **V3_0_22 json `7199c8b6`** (3,706
lines) = the T-331 / Checker hashes. Rules: UP-QTY-STATUS-001, UP-SPACE-001 (a label alone never decides), Q-35 C /
Q-48 A (wet scope), OWNER_RULE_OUTDOOR_FLOORS (2026-10-21 + additions), Q-24 / Q-25 / Q-29 (roofs), ERS s.2.1-s.4.

## 1. Result (acceptance a, b)

| Label | Storey | Physical space (drawing evidence) | Binding on V3.0.22 | Status |
|---|---|---|---|---|
| **AT19** | GF | **The swimming pool, not a bathroom.** Its text is the Arabic compound "swimming pool" (حمام سباحة): the census vocabulary V1 reads the first word "bathroom"; ROOM_VOCAB_V2 (compound first, the vocabulary the V3.0.x candidates use) reads POOL. It lies in the layer-5 D outline of the pool water: half circle ARC 202 (r 1550, 90-270 deg) + LINEs 203 / 205 (1550 to the boundary-wall face); T-071 face 8.576 m2 / 11.068 lm = hand D 8.578838 / 11.069469 (-0.03 % / -0.01 %) = the inner area in the candidate pool lines' own formula. Same face holds AT20 (English) | pool shell STR.CONC.POOL **L-15a128c38982af899894** (walls 2.828071 m3) + **L-36efa902da4263479e0b** (base 4.374226 m3) + L-b62a7065645589011141 (steps, BLOCKED_RFI blank, not drawn) | **PARTIAL**: shell BOUND; pool membrane 29.582 m2 + screed 1.525 m3 MISSING (T-309 DRAWING-CONFIRMED, lane I FILL T-336 -> T-310); water-face finish MISSING, HELD blank, drawn bound 21.309 m2 (8.579 + 11.069 x 1.15), no finish specified; floor / wet-room tile, backing, WP, ceiling NOT_APPLICABLE (no bathroom exists) |
| AT20 | GF | same pool face (bilingual pair) | DUPLICATE_OF AT19 (counted once) | as AT19 |
| **AT21** | GF | the one open court face inside the plot boundary walls (T-071 net 167.067 m2 = filled 177.299 - pool hole 10.232 / 12.097 lm), cut along drawn lines by T-157 | **no candidate line** (the only outdoor floor line is the side passage HL:FLOOR_SCOPE:OUTDOOR GF-SIDE-PASSAGE 5.640, another face) | **MISSING**, named: west court interlock 119.542 m2 (area DRAWING-CONFIRMED, material ASSUMED — OWNER-APPROVED), covered porch 10.679 (material HELD), E1 treads 3.359 + risers 1.960 + landing 5.179 marble, north side walk 21.014 porcelain (owner manual 23.955 beside), **pool deck 7.109 (CORRECTED, was 7.939)** HELD material |
| AT22 / AT39 / AT40 | GF | same court face (T-071 "4 labels, one face") | DUPLICATE_OF AT21 | as AT21 |
| **AT225** | 1F | the 1F slab opening over the pool court (structural opening inside the B7 ring inner faces 3.690 m2, T-127, verifier 3.689; drawn faces 2.613 layer 2 / 3.820 layer 5) | its deduction is in GF soffit **L-23072352a28aeca7b051** (SOFFIT:GF:PL-03: 16.525 gross - 3.690 = 12.834 = the line); it is NOT the 16.005 m2 living-void deduction (AT215, 1F-R78C367, L-35341ff2e6a848b9436b) | **NOT_APPLICABLE** (open to below and sky: no floor, no finish; not 0) |
| **AT385** | 2F | the 1F roof at +9.70, the same T-071 face as AT379 (115.832 m2, 2 open dome skylights out) | DUPLICATE_OF AT379: **L-636fd3ff1784a12e653b** (FIN.WP.ROOF 115.832 m2) + **L-5ce5ba49792e8f9d1f6f** (upturn 92.922 lm), bound by the line's own gap entity D2:4793:0 in the face | **BOUND** (via AT379) |
| AT379 / AT216 / AT220 (the 3 carried by name) | 2F / 1F | roof faces | now bound by source entity, not by name: AT216 L-2f7502be6f501baf49b1 + L-994b88140f2ea50f1b31, AT220 L-d57d2dc2fafac8bc72d8 + L-d4c73babd2a275c28929 | BOUND |

AT19 answered first and fully (b): the wet-room scope it leaves open is **none** (NOT_APPLICABLE with evidence: no
bathroom is drawn there; no V3.0.22 wet line, WET_TILE included, names that face). What it does leave open is pool
scope: membrane 29.582355 m2 (bound 29.582 .. 30.932) and screed 1.524503 m3 (1.525 .. 1.593), both already measured
and Checker-merged (T-309), waiting for the lane I FILL (T-336 FILL_T310_T336.csv, row T-310); and the water-face
finish, HELD blank (no material named on any sheet) with a drawn surface of 21.308727 m2.

## 2. Finding: the pool is a D, not a circle (corrected quantity)

T-153 / T-157 read the pool as circles r 1.55 / 1.75 "clipped at the boundary" (water 7.548, outer 9.402). The DXF
draws half circles (ARC 200 r 1750 and ARC 202 r 1550, both 90 -> 270 deg about one centre) closed by straight LINEs
203 - 206 1550 long to the boundary-wall face: a D. Water D = pi 1.55^2 / 2 + 3.10 x 1.55 = 8.578838 m2 (T-071 face
8.576, perimeter 11.068 vs 11.069); outer D cut at the wall face = pi 1.75^2 / 2 + 3.50 x 1.55 = 10.235563 m2 / 12.097787
lm (T-071 court hole 10.232 / 12.097). The structural record (T-183 r2, verified) already used the D (base 10.935564 =
the full outer D incl. the back wall). Effect: **pool deck = pool court 17.3414 - 10.232 = 7.1094 m2, not 7.9392
(-0.830 m2, -10.5 %)**; T-153's "pool water 7.548" is 8.579 (+1.031). Re-add: 119.5416 + 10.679 + 3.3594 + 5.1794 +
21.0142 + 7.1094 = 166.883 = 177.115 - 10.232. The deck stays HELD on material (owner: undecided); only its area moves.
Rule (proposal, R-T342-POOL-OUTLINE-1, general): a pool's plan footprint is the drawn outline, accepted only when its
area AND perimeter agree with the element it is bound to; a printed radius never makes a circle. Regression:
`test_adverse_cross_drawing_by_name_only_or_circle_reading_is_refused` (D vs circle area, same area wrong perimeter).

## 3. The binding rule (R-T342-BIND-1, research/agents_t342/t342_label_binding.py; every villa)

1. Re-type the label with the compound vocabulary first; a bare-word reading the compound contradicts never gives
   wet-room scope. 2. One face per physical space; further labels in it are DUPLICATE_OF the first (counted once).
3. A line binds only when its item code is the scope's AND its own source names an entity of the face (or an element
   of another drawing the face is geometrically the same space as: area and perimeter within 0.5 %). Refused: name
   only (REFUSED_NAME_ONLY), wrong trade (a court on an interior floor-tile line), a 0 line on a held scope, a
   cross-drawing match by name or by a different outline. 4. MISSING / HELD never carries 0; NOT_APPLICABLE needs
   drawing evidence.

Tests (d): tests/t342_label_binding/test_binding.py, a hand-made villa (not Alsenan): compound pool label, two-label
court, repeated roof label, a bathroom label outside every face (MISSING_NO_FACE, never 0), void; adverse: name-only
binding, court on a floor-tile line, held space as 0 (both a MISSING scope at 0 and a 0 line), BOUND with no line,
NOT_APPLICABLE without evidence, cross-drawing by name / circle area / circle perimeter, mm2 figures, order reversed.
test_alsenan.py: byte rebuild, census 41/28/1/1/11/47, every target bound, AT19 = pool, deck, held finish blank.

## 4. For the Checker (e) and the Lead

- M2 on rooms: with this ledger every one of the 11 NO_ROOM labels has a binding: 4 faces BOUND (3 roofs, pool shell),
  1 NOT_APPLICABLE (1F void), 6 duplicates counted once, and the open scopes NAMED with quantities (court 6 pieces
  166.883 m2 + 1.960 m2 risers, pool membrane / screed / finish): 0 silent. The Checker can state M2 MET on rooms once it
  accepts this binding; what remains is integration, not omission: (i) T-310 FILL of the pool WP (T-336 table), (ii) a
  NEW lane I row for the outdoor floor lines (6 court pieces, deck 7.109 corrected, porch and deck material blank).
- The census tool reads labels with ROOM_VOCAB_V1; run with ROOM_VOCAB_V2 it would type AT19 POOL (no tool change here:
  this task's files are research / tests only). Proposed small tooling row: census `--vocab ROOM_VOCAB_V2`.
- Verdict proposals: AT19 BATHROOM reading ENGINE_WRONG (census vocabulary), pool = D: ENGINE_RIGHT (T-071 faces,
  T-183 shell) vs T-153 / T-157 circle (deck 7.939 -> 7.109, ENGINE_RIGHT by the hand D); freelancer: his yard 151.80 has
  no pool deck (unchanged, T-157 AGREE / RULE_DIFFERENCE stands).
- Lessons register row (proposal): "a compound room name is read before its first word, and a pool outline is read
  from its drawn segments, never from its printed radius" (scope: every villa; provenance T-342).
- Uncertain: the arch layer-5 void oval 3.820 vs the structural ring opening 3.690 (0.130 m2) is named, not resolved
  (the soffit line uses the structural face; no quantity of this task depends on it).
