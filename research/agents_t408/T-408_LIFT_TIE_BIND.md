# T-408 Lift structure follow-up: GF lift tie beam, ring beams, shaft cap and pit-wall facts bound to V3.0.34 (lane S, research only)

Worker 1, 2026-11-01 03:22 .. UTC, branch `agents/task-T-408`. No quantity, line, state, method, rule or released cell is
changed. Development villa (Alsenan), not an accuracy claim; the method (LIFT_TIE_BIND_V1) is for every villa. ERS s.2.1 -
2.6, s.3, s.4, s.7 applied. Drawings named by Drive folder and title; entities by DXF handle; sizes only.

## 0. Run and sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`),
'ST7757 dxf.dxf' (`9f9d1179`), ST7757.pdf (`74da1523`), decoded into `.work/private`. `research/agents_t167/v304_run.py`
then `research/agents_t399/v3034_run.py`: **V3_0_34_BOQ_LINES.json `4c7f581c` / csv `4ba5bbe1` = candidate of record
REPRODUCED** (V3_0_33 `a545c5b3`, V3_0_32 `0c8bfbe6` reproduced in the same run). Then

```
python3 -I research/agents_t408/t408_alsenan.py --structural <private>/ST7757.dxf \
    --v3034 <run>/v3034/V3_0_34_BOQ_LINES.json --v3032 <run>/v3034/V3_0_32_BOQ_LINES.json --out research/agents_t408
```

Outputs: `summary_t408.json` (`9c5c41d2`), `BINDING_T408.csv` (`b55ad717`, 30 T-401 bindings re-checked). Rules
`lift_tie_v1.py` (LIFT_TIE_BIND_V1, R-T408-1 .. 6, stdlib, reuses the merged T-401 `ring_geometry` unchanged); tests
`tests/t408_lift_tie_bind/` (hand villa Q + development-villa pins). Verified input: T-401 MERGED 23f948bb (Verifier
21:00, Gate A PASS); not re-derived (WORKFLOW_CONTROLS s.10.5) except where stated.

**The T-399 delta touches no structural line**: own sort-keyed line diff V3.0.33 -> V3.0.34 = 1 line changed
(L-c3f7e68c FIN.PAINT), 0 STR.* lines. V3.0.32 -> V3.0.33 (T-397, Gate B PASS 19:55) changed 2 of the 72 lift-referenced
lines and added 1 (section 2).

## 1. The GF lift tie beam (ST p.8 note 19), physical element and measure

Physical element (ERS s.2.1): an RC beam between the four lift columns at 3.00 m in a storey whose F.F.L. -> F.F.L.
exceeds 4.30 m; it braces the columns and carries the shaft block wall above it. FFL chain (merged T-206): GF +1.00 ->
+5.50 = **4.50 > 4.30: required**; 1F +5.50 -> +9.70 and 2F +9.70 -> +13.90 = 4.20: none. One element, separate
geometries (ERS s.3): concrete, two side forms, soffit form, bars, block face displaced.

**Length on the GF storey's OWN columns (R-T408-1, new this task).** T-401 measured the runs on the ground-beams pit-ring
plan (necks). The tie sits in the GF storey, so its supports are the GF columns. Own read of 'ST7757 dxf.dxf', S-COL.BON
outlines on three plans that draw the GF lift columns:

| Plan | Handles (SW, NW, NE, SE) | Sections (m) | Band | Runs S / N / W / E (m) | Total |
|---|---|---|---|---|---|
| GF roof slab plan (columns under the GF roof), shaft S-OPENING 54F | 33E, 341, 33B, 338 | 0.20x0.50 x3, 0.25x1.00 | 0.20 all sides | 1.80 / 1.80 / 1.20 / 0.70 | **5.50** |
| p.1 columns plan | 834, 837, 831, 82E | same | 0.20 | 1.80 / 1.80 / 1.20 / 0.70 | **5.50** |
| ground-beams plan (pit ring, T-401) 10EB / 10EA | 1096, 1099, 1093, 1090 | same | 0.20 | 1.80 / 1.80 / 1.20 / 0.70 | **5.50** |
| 1F roof plan (for the table; no tie) 73F | 67F, 682, 67C, 679 | same | 0.20 | 1.80 / 1.80 / 1.20 / 0.70 | 5.50 |
| 2F roof plan (for the table; no tie) | 41E, 421, 41B, 418 | 0.20x0.50 x3, **0.20x0.70** | 0.20 | 1.80 / 1.80 / 1.20 / **1.00** | 5.80 |

Closure on the GF plan: 5.50 x 0.20 + columns in band 0.500 = 1.600 m2 = 2.20^2 - 1.80^2: the tie band and the columns
partition the ring band, 0 overlap (the columns own the joints, T-394 / ELEMENT_REGISTER 2026-10-31 20:20). **Length
5.500 m DRAWING-CONFIRMED on three sheets.** T-401's note that "NW C1 has no bound outline on the column plan" concerns
the mark-to-outline binding only: outline 837 (0.20 x 0.50) is drawn there.

**D-63 sensitivity (R-T408-5).** The lift columns carry a printed-vs-schedule CONFLICT (plan 20x50 / 25x100, schedule
FOUNDATION row 30x50 / 30x100). The dimension along the ring (0.50 / 1.00) is the same in both readings; only the
across-ring dimension grows 0.20 -> 0.30. The inner faces lie on the drawn 1.80 x 1.80 shaft clear (10EA, 54F / 73F), so
growth can only go outwards (as C9 already stands 0.05 proud): **tie length 5.500 m under both D-63 readings (0.000 m
change)**; growth into the shaft is refused (SHAFT_CLEAR_REDUCED).

**Section (R-T408-3).** Printed nowhere (note 19 gives the level only; no section, no schedule row; D-43, RFI-B-S14).
Neither a ring-beam section (B1 20x40, B7 / B14 20x75), a ground-beam section nor the freelancer's is admissible.

**Vertical separation from the GF roof ring beams (R-T408-4).** Tie at GF F.F.L. + 3.00 = +4.00; the GF roof ring beams on
the same plan band are B14 (S) and B7 (W) 0.75 deep, B1 (E, N) 0.40 deep, hung from the GF roof slab whose structural top
is +5.50 less the 1F floor build-up (unprinted). So the tie is a separate member only while d < 0.75 - build-up on S / W
(< 1.10 - build-up on E / N): a physical upper bound on the depth, **not** a section. Check OPEN by name.

Components (MISSING in V3.0.34, own search: no STR line names a tie beam; held by the section):

| Component | Owner trade | Quantity | Status | Missing fact |
|---|---|---|---|---|
| TIE_BEAM:GF concrete | STRUCTURE | 5.500 m x b x d | MISSING (no line), value blank | section b x d |
| side forms (shaft + outer face) | FORMWORK | 2 x 5.500 x d | MISSING | section d |
| soffit form | FORMWORK | 5.500 x b | MISSING | section b |
| bars | STRUCTURE | - | MISSING | bar detail (none printed); never a rate |
| block face displaced (GF-W08 / W09 / W13 / W14) | BLOCKWORK | 5.500 x d | PAIRED HELD: the three GF block lines MAS.BLOCK L-4165954c, ARCH.WALL_VOLUME L-4423d85b, ARCH.WALL_PANEL L-63fa7862 already hold these four walls on 'lift tie beam size (ST p.8 n.19)' | section d |

Lift door: wall GF-W08 carries the lift opening L-GF-01 (1.00 m, height HELD) inside the W run 1.20 m; whether the tie
(soffit +4.00) also acts as its head or a separate lintel is needed is OPEN until the door height is known (not this
line's quantity; named for the lintel owner).

## 2. Binding of the T-401 components to V3.0.34 (BINDING_T408.csv, R-T408-6)

30 bindings re-checked by id, code, state and value: **29 BOUND unchanged**, 1 drift.

| Component | V3.0.34 line(s) | Value | Result |
|---|---|---|---|
| Raft FF | L-1590b76b | 11.385 m3 | BOUND |
| 12 ring beams GF / 1F / 2F roof | L-9c4ad8b1, L-30080007, L-4f30f08b, L-c82e9ff1 / L-b3c87fd2, L-dadbee5a, L-4299f559, L-34ccc6d3 / L-13031ccc, L-1caceb74, L-ae4fced6, L-23275eb0 | 0.650 + 0.650 + 0.464 = **1.764 m3** | 12 / 12 BOUND, = Verifier's own 1.764 |
| Shaft cap (+13.90 roof panel) | L-a615e1aa | **0.5184 m3** (1.80 x 1.80 x 0.16) | BOUND |
| GF / 1F shaft | - | 3.24 m2 each | OPENING, no line (unchanged) |
| Lift columns GF / 1F / 2F (16 concrete lines) | as T-401 COLUMNS | | 15 BOUND; **L-755eb56b (1F C9) PROVISIONAL 0.756 -> BOUNDED 0.756 .. 1.050 m3** |
| Pit walls | **L-684fcad3 STR.CONC.LIFT** (added V3.0.33) | blank BLOCKED_RFI, 1.100 m2 beside | bound (was MISSING in V3.0.32) |
| Ground held cell over the shaft | L-41cfb82e | 3.929788 -> 0 .. 3.560540 | shaft / ring out (T-397, as T-401 stated) |

The drift is explained: T-397 P1 (Verifier Gate B 19:55) made the 15 column CONFLICT lines ranges; 1F C9 is printed
20x90 (0.20 x 0.90 x 4.20 = 0.756) and drawn 0.25 x 1.00 (x 4.20 = 1.050). Not a lift finding; the T-401 table's
"valued PROVISIONAL 0.756" now reads BOUNDED 0.756 .. 1.050.

## 3. The pit-wall height facts in V3.0.34 (findings)

The pit-wall height is raft top -> slab-on-grade top (ST p.14, Verifier-confirmed at T-401): held by TWO facts, pit depth
below the landing F.F.L. (lift supplier) AND the GF build-up F.F.L. +1.00 -> slab top (unprinted). ERS lesson 2026-10-31
(ADOPTED): a held quantity names every fact it depends on.

- **F-T408-1**: L-684fcad3 (pit walls) names only the pit depth ('as per lift manufacturer ... D-43 / D-63'); the GF
  build-up is not named. Same for the two height-dependent WP wall lines L-302b401e (membrane, walls) and L-f0aadf70
  (board, walls). Quantity effect 0 (all blank); a reader who gets the supplier's depth would value the wall at the
  wrong height by the build-up (1.100 m3 per metre of build-up).
- **F-T408-2**: the formwork faces L-e3eb0057 / L-6d72f51d still say "no candidate concrete line for the lift-pit walls
  (V3.0.21)" although L-684fcad3 exists since V3.0.33, and name neither fact. Quantity effect 0.

## 4. Overlap (0 DOUBLE) and the freelancer

| Pair | Result |
|---|---|
| tie beam vs lift columns (GF) | 0: runs between faces; band closes 1.100 + 0.500 = 1.600 m2 |
| tie beam vs GF roof ring beams (same plan band) | separate level bands while d < 0.75 - build-up (S / W): OPEN by name |
| tie beam vs pit walls | different level bands: walls end at the slab-on-grade top (below +1.00), tie at +4.00 |
| tie beam vs GF lift block walls | displacement paired: both HELD on the same fact (no double, no gap) |
| ring beams / cap vs columns / openings | T-401 census on V3.0.32, unchanged in V3.0.34 (0 STR line changed on those bands) |

Freelancer (T-401 read, quantities only): no tie-beam row, no engine line: MISSING both sides (not a residual); his lift
walls 2.400 m3 = 0.750 ENGINE_RIGHT + 1.650 HELD (unchanged).

## 5. Methods side by side (ERS s.2.2)

| Method | Tie beam GF | Ring beams | Cap | Pit walls |
|---|---|---|---|---|
| Owner manual method (column > beam > slab; section only as printed) | 5.50 m between column faces x printed section: HELD | 1.764 | 0.5184 | 1.100 m2 x H, HELD |
| Drawing-derived (this task) | 5.500 m on the GF columns (3 sheets), section HELD, d < 0.75 - build-up | 1.764 | 0.5184 | H = depth below F.F.L. - build-up: two facts |
| Candidate V3.0.34 | no line | 1.764 (12 lines) | 0.5184 | blank, one fact named |
| Freelancer | no row | B14 0.270, B7 0.270 traced | not traceable | 2.400 (gross ring x 1.50) |

## 6. Proposals for ONE lane I row (nothing edited here)

- **P1** NEW HELD line STR.CONC.LIFT `LIFT_TIE_BEAM:GF`, value blank (never 0), 5.500 m DRAWING-CONFIRMED beside (GF roof
  plan 33E / 341 / 33B / 338 = p.1 834 / 837 / 831 / 82E), missing fact: section b x d (D-43, RFI-B-S14); owner trade
  STRUCTURE; never in a column line; invariant under D-63.
- **P2** two NEW HELD formwork lines (`LIFT_TIE_BEAM:GF:SIDES` 2 x 5.500 x d, `:SOFFIT` 5.500 x b) and one NEW HELD rebar
  line (no bar detail): blank, tied to P1.
- **P3** text only: L-684fcad3, L-302b401e, L-f0aadf70 name BOTH facts (pit depth below the landing F.F.L., lift
  supplier; GF build-up F.F.L. +1.00 -> slab-on-grade top, structural / architect); L-e3eb0057 / L-6d72f51d tied to
  L-684fcad3 with the same two facts (F-T408-1 / -2). No quantity moves.
- **P4** no change: 12 ring beams 1.764 m3 and cap 0.5184 m3 stay bound; the GF block lines keep the tie hold (paired).
- No owner question (ERS s.2.7 not met: section = designer RFI-B-S14; depth = lift supplier L-1; build-up = RFI-S09).

## 7. Rules, tests, lessons row (proposed)

R-T408-1 .. 6 in `lift_tie_v1.py`. Tests `tests/t408_lift_tie_bind/` (hand villa Q, not Alsenan: ring 2.30 x 2.10, shaft
1.80 x 1.60, runs 1.80 + 1.80 + 0.90 + 0.80 = 5.30 m; tie 0.25 x 0.45 printed: 0.596250 m3, forms 4.770 + 1.325 m2, block
2.385 m2; 2F own columns 5.50 m -> 0.618750; clash gap 0.45; adverse: section borrowed (ring beam, neighbour, ground beam,
default, freelancer, none) refused, own section without a sheet ref refused, tie in the column line refused, tie through
the columns (7.80 m centre line) refused, tie in the ring beam refused, unprinted slab level OPEN not CLEAR, outline
missing refused, column growth outwards same runs / inwards refused, held never 0, binding drift found, held line naming
one fact found, mirror / quarter turn / mm identical; development villa: 5.50 on three plans, closure, ring 1.764 / cap
bound, only drift L-755eb56b, pit-wall line one fact, block walls paired).

Lessons row (ERS s.7): | 2026-11-01 | the lift tie beam's length was taken on the pit-ring plan and the pit-wall line
named one of its two facts | a member's supports were read on the plan of another level; a held reason copied from the
first finding (pit depth) and not updated when a second fact was found (T-401 after T-397) | a member is measured between
the supports drawn at ITS level (the plan of that storey), cross-checked on every sheet that draws them; a section
alternative of a support moves the member only by what it changes along the member; when a later verified finding adds a
fact to a held line, the line's reason is restated (every villa, all trades) | tests/t408_lift_tie_bind (outline missing
refused; growth across the ring same length; held line naming one fact found) | PROPOSED

## 8. Checker re-measure list

1. GF roof slab plan S-COL.BON 33E / 341 / 33B / 338 and S-OPENING 54F: runs 1.80 / 1.80 / 1.20 / 0.70 = 5.50 m; same on
   p.1 834 / 837 / 831 / 82E.
2. 2F roof 418 = 0.20 x 0.70 (E run 1.00 there; no tie at 2F, 4.20 < 4.30).
3. V3.0.34 own line search: no STR line for a lift tie beam; L-684fcad3 held text names the pit depth only.
4. L-755eb56b range 0.756 .. 1.050 = T-397 (not a lift change).

## 9. Not done / uncertain

- The datum of note 19's "3.00 m" (from the F.F.L. or from the slab top) is the merged T-401 verdict's reading, not
  re-read on the PDF this run; it changes only the clash bound, not the length.
- The lift door head vs the tie soffit (lintel ownership) is OPEN (door height HELD).
- The freelancer workbooks were not opened this run (T-401's reading reused).
