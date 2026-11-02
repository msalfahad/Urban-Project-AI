# T-474 part 1: formwork piece census, candidate line map, verified-geometry split, stream S proposal

Worker 3 (stream S), 2026-11-02 UTC, run session_01E6cPnasdmAaAhLoXHgky2j. Development villa, research only: no engine,
rule, knowledge, registry or candidate file changes; no quantity moves; nothing released (default V2.9 + route G).
Drawings cited by Drive title only; outputs carry line ids, face ids, codes, states and m2 (no coordinates, no names).

Files: `t474_rules.py` (R-T474-1 .. 7, every villa), `t474_alsenan.py` (census + line map from the merged ledgers, pinned
by sha256), `out/FORMWORK_LINE_MAP_T474.csv` (643 lines), `out/summary_t474.json`, `out/LIVE_V3_0_43_STATES.json`
(state / m2 of the 643 formwork lines and their concrete lines on the reproduced V3.0.43, nothing else),
tests `tests/t474_formwork_census` (villa V474 by hand + adverse + development-villa pins).

## 1. Physical element (ERS s.2.1)

A formwork piece is one concrete surface cast against a temporary form. It bounds one member and sits beside the
candidate line that carries that member's concrete, never inside its m3. No piece where the face is cast against
blinding, masonry, an earlier-cast member, screed / fill, or earth where a detail prints it (R-T474-2). Below the
existing ground the FORMED / EARTH_CAST reading is the open owner question OQ-10 (no answered rule measures formwork;
OWNER_QUESTIONS_ANSWERED: only Q-74 A, strap axis geometry): both readings on one blank piece, never summed or chosen.
Physical (contact m2) is kept apart from procurement (form panels, reuse cycles: not measured here) and from rate.

## 2. Piece census per element class (R-T474-1; source: T-332 r2 face ledger + T-352 stair faces)

| Class | Piece (face kind) | Formed / no form | Faces: CALC / HELD / ALT / other | Valued m2 (G) | Drawing reference |
|---|---|---|---|---|---|
| Footing | sides, cover band, notch | base on blinding: no form; below EG: OQ-10 | 0 / 3 / 57 / 1 NA | - (OQ-10 FORMED 183.696 beside, all classes) | ST p.9 schedule, footing outlines |
| Neck | 4 sides | OQ-10 | 0 / 1 / 0 | - | ST p.9 / p.14 |
| Ground beam | sides, arc face, free end, cover | above N.G. formed; below OQ-10; base on blinding | 17 / 93 / 46 | 47.947713 | ST ground-beam plan, p.14 sections |
| Strap | sides, soffit | OQ-10 (Q-74 A axis lengths) | 0 / 3 / 6 | - | ST foundation plan |
| Boundary wall / beam | sides, end, edge band | 5 EARTH-contact faces held, rest OQ-10 | 0 / 13 / 0 (+1 INFO) | - | ST p.14 section A-A |
| Column | shaft to the controlling soffit | formed; joint strips apart | 18 / 41 / 0 | 117.461 | ST column schedule + plans |
| Joint | column strip inside beam depth | formed where no beam frames in | 18 / 73 / 0 | 8.712728 | slab plans |
| Beam | soffit + sides below slab | side against wall / member: no form | 450 / 142 / 0 | 390.251472 | ST p.4 / p.5 / p.6 roof-slab plans, SBT schedule |
| Slab | soffit, net panel between member faces | formed | 62 / 2 / 0 | 375.0481 | ST p.4 / p.5 / p.6 |
| Slab edge | thickness band at free edges / openings | formed | 133 / 43 / 0 (+1 owned by another line) | 25.201745 | slab plans |
| Stair | waist soffit, risers, flight sides, landing edge, junction strip | wall side: no form | 22 / 33 / 0 (+1 CONFLICT, 1 NA) | 36.927436 | ST stair sections p.4, T-345 flights |
| Lift pit | inner face per m height (FORMED), outer (OQ-10) | height D-43 not printed | 0 / 2 / 0 | - | ST p.14 lift detail |
| Parapet | both faces of the RC part from the slab top | formed | 0 / 24 / 0 | - (81.589 .. 202.782 beside) | A elevations, T-311 runs |
| Dome | shell soffit forms, drum sides | formed (S0) | 2 / 9 / 0 (+7 S1 never) | 48.300 | ST p.7 dome detail |
| Pool | water face, outer above EG | base on blinding; below EG OQ-10 | 2 / 2 / 4 | 15.982699 | T-320 pool envelope |

Valued total 1,065.832893 m2 = T-199 Gate B (0.000 %); the class split is face by face (summary `by_class_valued_m2`).

## 3. Line map: every candidate formwork line by id

643 lines = 612 STR.FORMWORK + 31 STR.FORMWORK.STAIR, each mapped to its faces, element classes and concrete line
(`out/FORMWORK_LINE_MAP_T474.csv`). Line ids are the engine formula `boq_line.line_id(project, item, element id,
R-T199-1, T-199, m2)` on the T-199 element ids (test pins it); the map is checked against the reproduced V3.0.43 run:
own Drive copies this run ('ST7757 dxf.dxf' 9f9d1179, P7757.dxf from P7757_DXF_COMPRESSED.zip ab54dd55), T-167 base
run, then `research/agents_t350/v3043_run.py`: **V3_0_42 json 1793266d and V3_0_43 json 6f534d5e REPRODUCED** (= the
candidate of record, T-350 Gate B). All 643 candidate formwork ids = the 643 mapped ids (0 unmapped, 0 extra); every
face booked once.

| | V3.0.30 (T-199 Gate B) | V3.0.43 (candidate of record) |
|---|---|---|
| STR.FORMWORK (B10-13) | 612 lines, 254 valued 1,028.905457 m2, 358 blank | 612 lines, **244 valued 1,027.977403 m2**, 368 blank |
| STR.FORMWORK.STAIR (B7-13) | 31 lines, 10 valued 36.927436 m2, 21 blank | unchanged |

The difference is named line by line: V3.0.33 (T-397 DEPENDENT_HELD) took 10 slab-edge bands booked on column lines to
HELD BLANK when their column lines went to BOUNDED_EXPOSURE: -0.928054 m2 (1,028.905457 - 0.928054 = 1,027.977403, =
the T-471 matrix row C-B10-13). No valued formwork line changed its figure; none went from held to valued.

FINDING F-T474-3 (binding drift since the face ledger, 37 formwork lines): 25 column lines PROVISIONAL -> BOUNDED_EXPOSURE
(V3.0.33; 10 valued faces held as above, 15 were held already), 8 ground-beam lines PROVISIONAL -> SOURCE_DERIVED (6) or
BLOCKED_RFI (2) (their formwork is HELD / OQ-10 blank on both sides), and **4 VALUED beam formwork lines (17.784948 m2)
sit on GF beam runs that V3.0.33 restated to the drawn cell (T-392)**: BM-GF-040 0.7163 -> 0.716937 m3 (+0.09 %),
BM-GF-042 .2 1.337922 -> 1.33875 (+0.06 %), BM-GF-003 0.526665 -> 0.528021 (+0.26 %), BM-GF-006 0.254647 -> 0.255
(+0.14 %); formwork lines L-5db3bf6439ebfa2a7d61 5.312740, L-82b8e8bf610932c84e9d 6.992909, L-9b68c460329caf2c6d29
3.724102, L-da4abbc0be2d97a8081d 1.755197 m2 still carry the pre-restatement faces. Cause: the restated cell moves run
ends by millimetres; the face ledger was not re-derived. The m2 effect is not computed here (never a proportional
estimate): part 2 re-derives the four lines from the T-392 cell or holds them. The map marks them STALE BINDING.

## 4. Verified geometry vs calculated vs held (R-T474-6)

On V3.0.43 (643 lines): **VERIFIED_GEOMETRY 62 lines 375.048100 m2** | CALCULATED 192 lines 689.856739 m2 (of it 31
lines on a VERIFIED concrete line whose face geometry the verdict does not cover: 30 slab-edge / beam faces on slab lines
and the ring arc face; 4 STALE BINDING lines 17.784948) | HELD 388 lines (blank, bounds beside) | NOT_APPLICABLE 1.

- VERIFIED_GEOMETRY = the 62 suspended-slab soffit lines. Each sits on a slab line of Checker record V2-0c71eb8f0ae7dae0
  (CONC.SLAB WHOLE, 75 lines, 60.2804 m3 own GF 33.0695 + 1F 19.7566 + 2F 7.4543; still bound by content on V3.0.43:
  the 75 lines total 60.280158 m3 there) and its m2 IS the verified net panel area (dimensions.area_m2 of the slab line;
  m3 / area = the slab thickness, 0.16 on 60 panels and 0.18 on 2). 52 agree to 1e-6 m2; 10 differ by 0.0001 .. 0.0006 m2 (sum +0.0019): two
  independent 4-dp roundings of the same T-139 panel and the split halves 1F-073 / 1F-076 c0 / c1 (concrete line halves
  0.352 / 0.5817 equal, faces the actual halves); residual named on each line, the figures stay as merged. These lines
  stay CALCULATED formwork (no independent formwork re-measure), never VERIFIED.
- Ring ground beam BAND0043 (V2-66ef133c13150687, 1.746916 m3): its arc faces are R4-148 CALCULATED 6.239008 (above N.G.)
  and R4-149 OQ-10 FORMED: the verdict proves plan area x depth, not the arc face height above N.G.: CALCULATED.
- HELD (blank, never 0), by reason: 150 lines faces HELD in the ledger (joints, sunken edges D-41, stair wall sides,
  BAND0049), 60 OQ-10 FORMED / EARTH_CAST pairs, 43 on BLOCKED_RFI concrete lines, 17 on BOUNDED_EXPOSURE lines, the 10
  V3.0.33 DEPENDENT_HELD lines, 108 untied (69 SPLIT_UNRESOLVED, 24 parapet T-311, 3 with no candidate line incl. the
  lift-pit faces D-43, 10 r5 pieces with no member, 2 named aggregates (neck, sunken panels)). Each line's reason is in the map's `basis` column.

## 5. The earlier item-code refusal and how part 2 avoids it

Cause (T-199 r1 / r2, Checker 2026-10-31): (1) r1: tests/t130_family_master compared the code with the frozen registry
snapshot 1.1.0, where B10-13 / B7-13 owned NO item code, so the new STR.FORMWORK / STR.FORMWORK.STAIR / ARCH.SHUTTER
literals were "written codes no family owns" and B6-05 / B7-10 "NOT_IMPLEMENTED with a module" (F-T199-3); (2) r2: the
guard scanned a fixed prefix list, so MET.RAILING.GUARD was owned by nothing and not scanned (F-T199-4). Resolved by
BOQ_FAMILY_MASTER 1.25.0 (STR.FORMWORK -> B10-13, STR.FORMWORK.STAIR -> B7-13) and the 1.26.0 scan of every prefix in
the arch_v30* modules (still in force in 1.38.0). Part 2 avoids it by construction: it writes ONLY STR.FORMWORK and
STR.FORMWORK.STAIR (parapet, lift-pit and dome faces included: no STR.FORMWORK.PARAPET or similar new code), binds
lift-pit faces to the existing STR.CONC.LIFT line (B10-10, V3.0.33) and parapet faces to the T-319 parapet RC lines,
and its registry version adds no item code; a test asserts every code literal of the new module is owned in the
governing registry. FINDING F-T474-1: in 1.38.0 the `candidate` block of B10-13 and B7-13 still reads NOT_IN_CANDIDATE
"as of T-193 / V3.0.7" although 643 lines are in the candidate since V3.0.30 (T-199 Gate B); `in_v3_0_candidate` "no".
Part 2's registry version must record the candidate state (with T-199 and the part 2 package) or the coverage census
under-reports both families.

## 6. Stream S integration proposal (part 2, after T-382 per the Lead order)

One V3.0.x package (next free version at merge), Gate B, every other line byte-identical:
1. Record only, no quantity: the 62 slab-soffit lines carry `basis = VERIFIED_GEOMETRY V2-0c71eb8f0ae7dae0` beside their
   CALCULATED status (status unchanged: no independent formwork re-measure; never VERIFIED until the Checker re-measures
   formwork itself).
2. Parapet faces (24 untied, 81.589 .. 202.782 m2): re-bind to the T-319 parapet RC lines only after a Gate A binding piece
   (T-199 s.4); until then they stay untied HELD.
3. Lift-pit faces: bind the inner face (5.500 m2 per m height) to the STR.CONC.LIFT pit-wall line; height D-43 HELD, so the
   line stays blank with the per-metre figure beside.
4. The 69 SPLIT_UNRESOLVED faces (member in two candidate lines, no length per line): split by the beam ledger span lengths
   (T-149) where both lines carry a printed span; otherwise HELD.
5. F-T474-2: the CALCULATED 0.000 m2 face T282-7E0+FD#2-END (an end closing on a drawn face: no form, R-FACE-END-3) becomes
   a named NO_FORM record, not a valued face of 0.
6. Registry version: candidate blocks of B10-13 / B7-13 (F-T474-1); no new item code.
Regression: lines outside the package byte-identical to the candidate of record; V2.9 + route G unchanged.

## 7. Hand fixture (non-Alsenan, villa V474) and Checker pick

V474 by hand: beam B1 0.20 x 0.60 under a 0.15 slab, span 4.00, north side on a block wall: soffit 0.800 + south side
1.800 = 2.600 m2 (not 4.400); slab S1 4.00 x 3.00 soffit 12.000 (VERIFIED geometry), free edge 4.00 x 0.15 = 0.600; RC
parapet 1.00 above the slab top 4.000 (given from the soffit 1.15 -> netted, 0.600 booked once on S1); total 19.200 m2.
Adverse: a figure on a masonry / blinding face, a piece on a NOT_PRESENT column, a 0 on a held piece, an OQ-10 piece
valued, an unknown face kind, mm input, a member-less piece, a parapet wholly inside the slab band: all refused; held
never summed; a valued piece on a BLOCKED_RFI concrete line goes HELD with the figure beside; rotation / mirror invariant.

Checker pick (one beam's sides + soffit): line **L-08f5357536a3d9319ec0** (4.268000 m2, PROVISIONAL) beside concrete
line L-785ce1a08953de7d421e (1F roof, P-C:BEAMS:1F:BAND0017, 0.485 m3): faces R4-278.1F-087.BEAM_SOFFIT 0.970 and
R4-280.1F-087.BEAM_SIDE 3.298. By hand from the bound concrete geometry: W 0.20 x clear L 4.85 = 0.970 (= the line's net
plan 0.97 m2); sides 2 x 4.85 x (D 0.50 - 1F slab 0.16) = 3.298; concrete 0.20 x 0.50 x 4.85 = 0.485 m3 consistent.
The Checker re-measures band, span and schedule size on 'ST7757 dxf.dxf' (1F roof-slab plan, ST p.5, SBT schedule).

## 8. Against the freelancer

No formwork row in any of his six workbooks (T-163: 885 raw rows): FREELANCER_NO_ROW (no %). Not proof either way.

## 9. Lessons-register row (proposed, ERS s.7)

| date | discrepancy | cause | rule | regression | status |
|---|---|---|---|---|---|
| 2026-11-02 | slab soffit forms 375.048 m2 carried as plain CALCULATED although every panel is the Checker-verified slab geometry (V2-0c71eb8f0ae7dae0); 10 panels differ by <= 0.0006 m2 | the formwork ledger and the slab line round the same T-139 panel independently (4 dp, split halves c0 / c1) and no record tied the derived trade to the verdict | a derived piece is labelled VERIFIED_GEOMETRY only when its concrete line is in a VERIFIED record AND the piece is that geometry within 0.001 m2 (residual named); the piece stays CALCULATED (R-T474-6, PROJECT-INDEPENDENT) | tests/t474_formwork_census (V474 12.000 normal; 11.900 adverse -> CALCULATED) | PROPOSED |
