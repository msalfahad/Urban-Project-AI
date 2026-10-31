# T-401 Lift pit and lift shaft structure: element definition, components bound to V3.0.32 (lane S, research only)

Worker 3, 2026-10-31 19:06 .. UTC, branch `agents/task-T-401`. No quantity, line, state, method, rule or released cell is
changed. Development villa (Alsenan), not an accuracy claim; the method (LIFT_STRUCTURE_V1) is for every villa without a
basement. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Drawings named by Drive folder and title; entities by DXF handle; sizes,
areas and counts only.

## 0. Run and sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`),
'ST7757 dxf.dxf' (`9f9d1179`), ST7757.pdf (`74da1523`), the freelancer concrete workbook (row read only), all decoded into
`.work/private`. `research/agents_t167/v304_run.py` then `research/agents_t284/v3032_run.py`:
**V3_0_32_BOQ_LINES.json `0c8bfbe6` / csv `acd217ee` = the candidate of record** (= the T-284 Gate B figures, T-397's
reproduction). Route G geometry: `research/agents_t387/t387_geometry.py` (private). Then

```
python3 -I research/agents_t401/t401_alsenan.py --lines <run>/v3032/V3_0_32_BOQ_LINES.json \
    --geometry <private>/t401/geometry.json --freelancer <private>/<concrete workbook> --out research/agents_t401
```

Outputs (ids, codes, states, m / m2 / m3 only): `COMPONENTS_T401.csv` (a, b), `COLUMNS_T401.csv` (the four lift columns
on every storey), `FACES_T401.csv` + `OVERLAP_T401.csv` (c), `summary_t401.json` (d). Rules `lift_structure_v1.py`
(LIFT_STRUCTURE_V1, R-T401-1 .. 5, stdlib); tests `tests/t401_lift_structure/` (hand villa P + development-villa pins).
Built on, not re-derived (WORKFLOW_CONTROLS s.10.5): T-204 MERGED (ring, p.14 detail, note 19), T-322 MERGED (raft /
blinding / underlay), T-219 (pit membrane / board / screed lines), T-391 MERGED (ground cell faces), T-394 MERGED (ring
net 1.100 m2 Checker-verified, freelancer split), T-230 (ground beams end on the ring face), T-206 (level chain).

## 1. The physical element (ERS s.2.1), founding level to roof

What is built for LIFT-01 (shaft 1.80 x 1.80 inside, east of the stair hall; stops at three landings GF / 1F / 2F):

1. **Raft FF** 4.60 x 4.50 x 0.55 (1B2B, FTB 2B1E, p.9 'lift base') on 5 cm screed, membrane, 10 cm plain concrete.
2. **Pit floor = raft top** (p.14): no slab of its own.
3. **Pit walls**: RC ring '20' on the raft top (S-BW 10EB 2.20 / 10EA 1.80, = 7C2 / 7BE on the ground-beams plan), through
   the four lift columns (1096 C2, 1099 C1, 1093 C2, 1090 C9). **New reading of p.14 (own render, 220 dpi): the wall top
   is drawn flush with the slab-on-grade TOP, below the F.F.L. line; the pit-depth dimension 'As Per Lift Manufactures
   recommendations' runs from the raft top to that wall top; above it the shaft wall is 'AS PER PLAN' (thin lines, no
   bars) with the 'Lift door'.**
4. **Shaft walls above the slab-on-grade** (GF, 1F, 2F): 'AS PER PLAN' = the architectural 0.20 walls (blockwork, T-143;
   lift block walls HELD in the RFI register). Not structural concrete.
5. **Tie beam in the GF** (ST p.8 note 19, own read: beams tie the lift columns at 3.00 m where the storey exceeds 4.30 m,
   round the lift): GF 1.00 -> 5.50 = 4.50 > 4.30, required; 1F 5.50 -> 9.70 and 2F 9.70 -> 13.90 = 4.20, not required.
6. **Ring beams at each suspended floor** on the 0.20 ring band: GF roof B14 / B1 / B7 / B1, 1F roof B7 / B1 / B7 / B1,
   2F roof B2 / B1 / B1 / B1 (route G bands, marks printed on the plans).
7. **Shaft slab state**: GF roof and 1F roof S-OPENING 54F / 550 and 73F / 740 (shaft open); 2F roof (+13.90) **closed**:
   slab bars 792 / 794 / 795 run through the box, no opening, no upstand. No overrun box and no machine room is drawn in
   either discipline (ST 2F roof plan; architectural search T-063 / T-204): **the 'overrun / machine slab' is the +13.90
   roof panel over the shaft**; the overhead clearance (2F F.F.L. +9.70 to the roof soffit) is a lift-supplier fact.
8. **Columns** C1 / C2 / C2 / C9 from the raft to the roof (necks + GF + 1F + 2F; C9 0.25 x 1.00 below, 0.20 x 0.70 at 2F).

## 2. (a) + (b) Components, each bound to a V3.0.32 line or MISSING (COMPONENTS_T401.csv, COLUMNS_T401.csv)

| Component | Owner trade | Quantity (drawing) | Status | V3.0.32 line | Source |
|---|---|---|---|---|---|
| Raft FF | STRUCTURE | 11.385 m3 | DRAWING-CONFIRMED (= line) | L-1590b76b STR.CONC.FOOTING 11.385 | 1B2B, 2B1E, p.9 |
| Blinding under the raft | STRUCTURE | HELD, AT_LEAST 2.070 m3 | HELD (T-322) | inside L-98eb2d58 (footing blinding 15.179437, downgrade DG-3521554d) | p.14 |
| Pit membrane / board / screed | WATERPROOFING | 47.43 m2 / 26.73 m2 / 20.70 m2, 1.035 m3; wall parts HELD | as T-219 | L-d3ec1944, L-302b401e (walls, held), L-1f3aaafc, L-f0aadf70 (walls, held), L-e11f17bb, L-e4789d76 | p.14 |
| Pit floor | - | = raft top, no volume | LISTED | none (never added) | p.14 |
| Pit walls, plan | STRUCTURE | 1.600 gross - 0.500 columns = **1.100 m2**; runs 1.80 / 1.80 / 1.20 / 0.70 = 5.50 m | DRAWING-CONFIRMED (Checker T-394) | - | 10EB / 10EA + 4 columns |
| Pit walls, concrete | STRUCTURE | 1.100 m2 x (raft top -> slab-on-grade top) | **MISSING in V3.0.32** (T-397 READY adds 'LIFT_PIT:WALLS' HELD blank) | none | p.14 |
| Pit wall formwork (inner / outer face) | FORMWORK | per m of pit height | HELD | L-e3eb0057, L-6d72f51d (no concrete line to tie to yet) | T-332 |
| Shaft void at ground level | none | 3.24 m2 (1.80 x 1.80) | not slab | held cell L-41cfb82e covers 2.8125 m2 of it (route G); unbilled gap face 0.4275 | 7BE |
| Lift necks C1 / C2 / C2 / C9 | STRUCTURE | 0.10 / 0.10 / 0.10 / 0.25 m2 x neck depth | HELD (BOUNDED_EXPOSURE, D-43 / D-63) | L-12f3d8b9, L-8eb74a02, L-dd6d1141, L-953e87a3 | SH10 |
| Lift columns GF | STRUCTURE | 0.45 x 3 + 1.125 m3 (section x 4.50) | valued PROVISIONAL | L-fa1c3468 (C1), L-bcefe951 / L-a8abdc06 (C2), L-7b41af57 (C9) | column plan |
| Lift columns 1F / 2F | STRUCTURE | 0.42 x 3 + 0.756 (C9 1ST 20 x 90, CONFLICT, T-397 P1) / 4 x HELD (BLOCKED_RFI) | as candidate | L-322d1a1a, L-734dc85d, L-6f56016c, L-755eb56b / L-d79d17d1, L-26f6b6f2, L-33a9b772, L-53f223b0 | column plan |
| GF tie beam (+3.00, note 19) | STRUCTURE | length 5.500 m (clear runs between column faces) | **MISSING**; concrete HELD: section not printed (D-43, RFI S-38) | none | p.8 note 19 |
| Shaft walls GF / 1F / 2F | BLOCKWORK | architectural 0.20 | listed (T-143) | blockwork family (not concrete) | p.14 'AS PER PLAN' |
| GF roof ring beams | STRUCTURE | 0.270 + 0.056 + 0.180 + 0.144 = **0.650 m3** (= 0.20 x L x D by hand) | valued PROVISIONAL | L-9c4ad8b1 (B14 1.80 x 0.75), L-30080007 (B1 0.70 x 0.40), L-4f30f08b (B7 1.20 x 0.75), L-c82e9ff1 (B1 1.80 x 0.40) | SH06 bands 0022 / 0023.1 / 0025.1 / 0026 |
| GF roof shaft opening | none | 3.24 m2 | OPENING face, no line | - | 54F / 550 |
| 1F roof ring beams | STRUCTURE | 0.270 + 0.056 + 0.180 + 0.144 = **0.650 m3** | valued PROVISIONAL | L-b3c87fd2 (B7), L-dadbee5a (B1), L-4299f559 (B7), L-34ccc6d3 (B1) | SH04 bands 0006 / 0007.1 / 0011.1 / 0012 |
| 1F roof shaft opening | none | 3.24 m2 | OPENING face, no line | - | 73F / 740 |
| 2F roof (+13.90) ring beams | STRUCTURE | 0.144 + 0.080 + 0.096 + 0.144 = **0.464 m3** | valued PROVISIONAL | L-13031ccc (B2 1.80), L-1caceb74 (B1 1.00), L-ae4fced6 (B1 1.20), L-23275eb0 (B1 1.80) | SH02 bands 0007.1 / 0008.2 / 0011.2 / 0012 |
| Top of shaft = roof panel over the shaft | STRUCTURE | 3.24 m2 x 0.16 = **0.5184 m3** | valued PROVISIONAL (= drawing) | L-a615e1aa (SH02 SITE-29936e52) | 792 / 794 / 795 |
| Overrun / machine room | - | none drawn | NOT DRAWN (searched: ST all plans, arch T-063 / T-204) | none needed | - |

The pit-wall height is held by **two** facts, not one (R-T401-2): (1) the pit depth (lift supplier, RFI L-1, which asks
for it 'below the lowest landing finished floor'), (2) the GF floor build-up F.F.L. +1.00 -> slab-on-grade top (not
printed on any sheet, T-206). Wall height = depth below F.F.L. - build-up. The supplier's answer alone does not value the
wall. The wall concrete stays HELD with the plan 1.100 m2 beside it; never a neck height, never a default.

## 3. (c) Exact-outline overlap check (route G faces of V3.0.32; OVERLAP_T401.csv, FACES_T401.csv)

| Level | Ring band 1.600 m2 | Shaft 3.24 m2 | Result |
|---|---|---|---|
| GF roof, 1F roof | beam strips 1.100 (0.36 + 0.14 + 0.24 + 0.36) + column faces 0.500 | OPENING face, no line | **0 DOUBLE**, 0 GAP |
| 2F roof | beam strips 1.160 + column faces 0.440 (C9 0.20 x 0.70 there) | slab panel 3.24, one line (L-a615e1aa) | **0 DOUBLE**, 0 GAP |
| Ground (pit top) | columns 0.500; net ring 1.100 = 0.880 in held cell L-41cfb82e + 0.220 in junction-gap face SITE-47d689fe (NO_LINE) | 2.8125 in the held cell + 0.4275 in the gap face | **0 DOUBLE (valued)**; HELD overlaps named: cell over shaft 2.8125, ring 0.880, C9 piece 0.25 (and ground beams BAND0028 / 0036.1 0.09 each, T-391's member overlap); GAP: the ring 1.100 has no concrete line (MISSING -> T-397) |
| Pit walls vs raft / ground beams / columns | wall starts on the raft top; ground beams end on the ring's outer face (no band on the ring, T-230); columns out of the ring (net) | - | 0 DOUBLE |

Cross-check of two partitions of the same ground ring: route G (0.880 cell + 0.220 gap) and T-391's own faces (OWN-082
0.36 + OWN-083 0.36 + OWN-086 0.24 in the cell, OWN-094 0.14 outside) both give **1.100 m2**. T-391 classed the three
in-cell pieces as 'BEAM' strips by its width rule (eq. width 0.20 < 0.36): they are the S-BW pit ring, i.e. the
pit-wall line's, not a ground beam's. No quantity changes: T-397's held bound 0 .. 3.560540 (own slab panels only)
already excludes shaft, ring and column pieces, so after V3.0.33 the ring band is owned once (LIFT_PIT:WALLS, HELD).

## 4. (d) Freelancer lift rows (quantities only)

His concrete workbook has ONE lift row: 'lift walls 20 cm' 8.00 x 0.20 x 1.50 = **2.400 m3** (walls + columns sheet,
row 11). Engine V3.0.32: no line. Residual -2.400 m3:

| Cause | m3 | Verdict proposal |
|---|---|---|
| his gross ring 8.00 x 0.20 = 1.600 m2 = drawn gross ring (plan difference 0.000); the four column pieces 0.500 m2 x 1.50, also in his neck rows | **-0.750** | ENGINE_RIGHT (ownership, R-CONC-OWN-1; T-394 verified) |
| net ring 1.100 m2 x his 1.50 (his uniform neck height, not a printed pit depth) | **-1.650** | HELD (pit depth + GF build-up) |

Traced -0.750, HELD -1.650, unexplained 0.000. Ring beams with a unique mark on their floor: his GF B14 0.20 x 0.75 x
1.80 = 0.270 = L-9c4ad8b1 0.270 (AGREE); his 1F B7 0.20 x 0.75 x 1.80 = 0.270 = L-b3c87fd2 0.270 (AGREE). He has no tie-beam
row (the engine has none either: MISSING both sides) and his slab rows are one gross area per floor (no shaft deduction or
roof shaft panel can be traced in them: slab family, not a residual of this element).

## 5. Methods side by side (ERS s.2.2)

| Method | Pit walls | Ring beams GF / 1F / 2F | Tie beam GF | Shaft cap |
|---|---|---|---|---|
| Owner manual method (column > beam > slab, R-CONC-OWN-1; heights only from printed levels, Q-21 C) | 1.100 m2 x H, HELD | 0.650 / 0.650 / 0.464 | 5.50 m x section, HELD | 0.5184 |
| Drawing-derived (this task) | 1.100 m2 x (raft top -> slab-on-grade top), HELD by depth AND build-up | 0.650 / 0.650 / 0.464 | 5.50 m, section HELD (D-43) | 0.5184 |
| Candidate V3.0.32 | no line | 0.650 / 0.650 / 0.464 | no line | 0.5184 |
| Freelancer | gross ring x 1.50 = 2.400 | B14 0.270, B7 0.270 traced | no row | not traceable |

## 6. Proposals for a lane I row (nothing edited here)

- **P1** (completeness, NEW HELD line): `STR.CONC.LIFT 'LIFT_TIE_BEAM:GF'`, value blank, length 5.500 m DRAWING-CONFIRMED
  beside (runs 1.80 / 1.80 / 1.20 / 0.70 between column faces), missing fact: tie-beam section (D-43, RFI S-38); never 0.
  Owner trade STRUCTURE; the GF lift block walls deduct it when it is valued (blockwork, T-143).
- **P2** (T-397's 'LIFT_PIT:WALLS', same candidate): record the height basis 'raft top -> slab-on-grade top (ST p.14)' and
  BOTH missing facts (pit depth below the F.F.L. from the lift supplier; GF build-up F.F.L. -> slab top); tie the two held
  formwork faces L-e3eb0057 / L-6d72f51d to it (they stay HELD).
- **P3** (no quantity change): the 12 ring-beam lines (1.764 m3), the roof shaft panel L-a615e1aa (0.5184 m3) and the two
  shaft openings are equal to the hand values above: re-measure candidates for the Checker.
- **P4** (label only): T-391 OWN-082 / -083 / -086 (0.96 m2) are the pit-wall ring, not ground-beam strips.
- **No owner question** (ERS s.2.7 not met: the pit depth is a lift-supplier item, the build-up and the tie-beam section
  are designer / architect items). **RFI facts (s.6 form, for the RFI register):**
  1. Structural / architect: the GF slab-on-grade top level at the lift (or the GF floor build-up below F.F.L. +1.00).
     Drawing: ST p.14 (wall top flush with the slab-on-grade top, F.F.L. above it, no dimension between). Impact: pit
     walls 1.100 m3 per metre of height; with the supplier's depth it fixes the wall height. Pairs with RFI-S09.
  2. Lift supplier (with L-1): the overhead clearance needed above the 2F landing (+9.70 to the +13.90 roof slab) and
     whether the selected lift is machine-room-less; no overrun is drawn. Impact: none on V3.0.32 unless an overrun is
     required (then a new element).

## 7. Rules, tests, lessons row (proposed)

R-T401-1 .. 5 (`lift_structure_v1.py`): one line per component or MISSING; wall height on the governing detail's datum
(supplier depth to the F.F.L. less the printed build-up; defaults refused); ring band = wall, column sections = columns,
shaft void = nobody (three named doubles refused); HELD / MISSING = None with the exact missing fact; overlap census per
level band, 0 DOUBLE. Tests `tests/t401_lift_structure/` (31): hand villa P (raft 10.080, ring 1.850 / 0.450 / 1.400 m2,
runs 5.60 m, wall 1.28 m -> 1.792 m3, tie beam 0.560 m3, cap / openings), adverse: depth from a neck height / default /
freelancer / missing basis refused, supplier depth without build-up HELD, held as 0 refused, missing line named not
valued, tie section missing HELD with its length, mirror / quarter turn / mm identical, unit / raft / ring / column-in-
shaft / datum guards, line bound twice refused, shaft opening billed as slab refused, pit wall in slab and wall refused,
lift columns in the ring twice refused, shaft void as ground slab refused, a valued double named; development villa: ring
1.100 / 5.50 m, pit wall MISSING by two facts, tie beam MISSING 5.500 m, 12 ring beams bound = hand, raft / cap /
openings, 0 DOUBLE with both ground partitions closing, freelancer 2.400 = 0.750 + 1.650, columns on every storey,
dependent WP / formwork lines.

Lessons row (ERS s.7): | 2026-10-31 | the lift pit walls were held on 'the pit depth' alone and the GF lift tie beam had
no line in any state | p.14 draws the wall top at the slab-on-grade top below the F.F.L. while the supplier is asked for
the depth below the landing F.F.L.; note 19 is a text note, not a drawn member | define the lift from raft to roof as one
element with one line or MISSING per component; read the governing detail's datum before naming the missing fact (a
depth quoted to a finished level needs the build-up); a member required by a note is a MISSING line with its drawn
length, never absent (every villa) | tests/t401_lift_structure (supplier depth without build-up HELD; depth defaulted
refused; tie beam MISSING with length) | PROPOSED

## 8. Checker re-measure list

1. ST p.14 (PDF render): pit-depth dimension from the raft top to the wall top; wall top level with the slab-on-grade top;
   F.F.L. line above; 'AS PER PLAN' above.
2. ST p.8 note 19 (3.00 m, 4.30 m); FFL chain GF +1.00, 1F +5.50, 2F +9.70, roof +13.90.
3. Ring runs between column faces: 10EB / 10EA with 1096 (0.20 x 0.50), 1099, 1093, 1090 (0.25 x 1.00): S 1.80, N 1.80,
   W 1.20, E 0.70 = 5.50 m.
4. One ring beam per floor: GF B14 (band 0022) 0.20 x 1.80 x 0.75 = 0.270; 2F B1 (band 0008.2) 0.20 x 1.00 x 0.40 = 0.080
   (C9 0.20 x 0.70 at 2F, 418).
5. 2F roof slab over the box: no S-OPENING, bars 792 / 794 / 795 inside; panel 3.24 x 0.16 = 0.5184.

## 9. Not done / uncertain

- The blockwork shaft walls and their landing openings were not re-measured (T-143 / lift block walls in the RFI
  register); the freelancer's blockwork workbook was not opened.
- Rebar of the pit walls / tie beam (T-204 per-metre figures) not carried: concrete only.
- The NW lift column C1 has no bound outline on the column plan (its mark sits 1.2 m north of outline 837); it is billed
  through the C1 mark lines at the schedule section 0.20 x 0.50 (GF 0.45 m3 = 0.10 x 4.50): same value as the drawn
  outline; a binding note for T-256's owner, not a quantity issue.
