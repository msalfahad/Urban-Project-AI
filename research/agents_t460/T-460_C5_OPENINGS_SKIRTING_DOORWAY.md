# T-460 (owner C5): small openings, skirting line closure, wet doorway overlap, joinery-backed skirting

Worker 1, claim 2026-11-04T11:21Z (`date -u`), branch agents/task-T-460, engine base aa79343a. Research only: no engine
module, rule / knowledge version file, registry, candidate line or released line changed; nothing released. ERS applied:
s.2.1 physical element first, s.2.2 evidence hierarchy (drawing, then merged ledgers, then engine), s.2.4 reconcile to
named causes, s.4 rule + normal / adverse tests. Inputs: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip
(P7757.dxf `ab54dd55`) and 'ST7757 dxf.dxf', decoded only into .work/private. Outputs hold widths, m2, lm, classes and
entity handles only.

## 1. Openings narrower than 0.50 m (C5 item 1): REPRODUCED, general defect, no Alsenan quantity change

**Physical element.** A hole through a wall's masonry between two jambs, at any width. A gap in a wall band's face lines
is not always such a hole: where a perpendicular wall crosses the band, both band faces stop although masonry is
continuous (a junction).

**Defect (engine read only).** `lintel_measure.openings` / `robust_geometry.openings` (the band path behind
`arch_rooms.spaces()["openings"]`, hence every opening deduction of blockwork, plaster, paint, tiles and skirting) keep a
gap only when `g >= min_gap_m = 0.50` (`opening_gaps.band_gaps`: `if g < min_gap: continue`) and drop every column-cut
piece under 0.50 m (`lintel_measure._split_at_columns`). Curved wall bands use `arch_v29.MIN_GAP_M = 0.40`. A 0.40 m
window or vent between masonry jambs gets no opening record: its masonry and finish area stay in the wall, against Q-73
(CONFIRMED 2026-10-22: deduct the full area of every actual opening, only from masonry that physically exists).
Reproduced on the hand fixture: `LM.openings` on villa K returns the 1.000 m door only; the 0.400 m window is absent
(`tests/t460_small_openings::test_reproduction_engine_band_path_loses_the_040_window`).

**Method (R-T460-1, `small_opening_census_v1.py`).** The engine's own band path run twice, at 0.50 m and at a 2 mm
numerical floor (twice the 1 mm cover merge tolerance; not an engineering threshold); every gap under 0.50 m classified
by drawing evidence, first that holds: SMALL_WINDOW (WINDOW-layer glazing >= 0.5 x width, arch_rooms' own WINDOW test)
-> DEDUCT; SMALL_DOOR (a swing fits, arch_rooms.match_swings) -> DEDUCT; WALL_JUNCTION (at both jambs a crossing wall face
runs beyond BOTH band faces by more than the 30 mm jamb tolerance) -> NOT_AN_OPENING; else SUB_MIN_GAP_UNEXPLAINED ->
HELD. A deduction is width x scheduled height; a height not printed keeps the area HELD with the width measured, never 0.

**Development villa (same frames and path as the candidate: V2.7 layer roles, column shapes, robust geometry).**
GF 29 / 29 and 2F 8 / 8 engine openings, no gap under 0.50 m. 1F: 22 engine openings, 2 more gaps:

| probe | width | class | evidence | candidate today |
|---|---|---|---|---|
| 1F-SG-001 | 0.4673 m, t 0.20, column jamb + masonry jamb, column-cut piece | SMALL_WINDOW | 1.940 m of layer W glazing (8 handles D2:3126 .. D2:3134) | this is W18 (T-249: absent from V2.9 / V3.0.8). Restored by per-project ledgers only: blockwork 0.4673 x 2.160 = 1.0094 m2 (T-274 rule 5, Checker own 12.935 on 1F-W00), external plaster 1.009 (T-305), wall tile / internal faces 1.080 (T-175 / T-388) |
| 1F-SG-002 | 0.150 m, t 0.15, masonry both ends | WALL_JUNCTION | crossing faces D2:2769 / D2:2770 and D2:2774 / D2:2775 (a 0.150 m wall crossing, a 73 mm nib on one side before a door) | correctly no opening |

Effect on the candidate: **0.000 m2** (the one lost window is already deducted through merged project ledgers; the junction
is not an opening). Effect on any other villa: every window, vent or door narrower than 0.50 m (0.40 m on a curved wall)
is undeducted from blockwork, plaster, paint and tiles, and its skirting / lintel is not considered, unless a project
ledger repairs it by hand. Verdict proposal: ENGINE_WRONG (general, every villa), Alsenan quantity effect 0.

**Engine follow-up (a NEW version file in a follow-up row, never in this claim):** pass the census into the opening list
of the next ARCH_TAKEOFF V3.0.x so SMALL_WINDOW / SMALL_DOOR records become openings (kind by the same tests, height by
the opening schedule chain, HELD when unprinted), WALL_JUNCTION records are listed as refused gaps, and
SUB_MIN_GAP_UNEXPLAINED records hold the host wall's net as a named range. Curved bands under 0.40 m: not covered by V1
(the curved reader has its own minimum; named, not measured here).

## 2. Skirting lines: line-by-line closure (C5 item 2)

`skirting_closure_v1.py` (R-T460-2): per FIN.SKIRTING line, gross - listed deductions + listed additions = net within
0.0005 lm; CLOSES / UNLISTED_DEDUCTION / UNLISTED_ADDITION / NO_GROSS / NO_QUANTITY. A residual is a piece that is in the
net but not on the line, so a reviewer cannot add it back; it is named, never plugged. Results on the candidate run: see
section 2.1 (SKIRTING_CLOSURE_T460.csv).

## 3. Wet-room doorway floor vs upturn (C5 item 3): NOT REPRODUCED, 0.000 m2 overlap

**Physical elements** (UP-WP-001 .. 003, Q-35 C): the floor membrane on the room's floor face (bounded by the room-side
wall faces and the opening closures); the doorway piece in the door's wall thickness (width x wall thickness, or the face
between the door's two closures); the wall upturn 0.20 m on walls only plus one doorway transition per physical door.

**Check (`doorway_overlap_v1.py`, `t460_doorway_alsenan.py`)** on the engine's own spaces for every room with a candidate
FIN.WP.FLOOR line (18 rooms): 104 pairs (every band-opening box of the room's doors, passages and windows, and every
DOORWAY-class face within 20 mm of the room): **0 overlaps, maximum 0.000004 m2** (shared-edge numerics). Each band box
touches the floor face along one edge (the room-side wall face) and lies in the wall thickness: e.g. 1F-R48AA46 floor
5.0225 m2 (= candidate) and doorway OP-004 0.800 x 0.150 = 0.120 m2 (= candidate FIN.WP.DOORWAY) share no area. The five
closure doorways (CLOSURE|...) are separate faces of the planar partition, overlap 0.

**Upturn reading** (candidate FIN.WP.WALL_UPTURN against the merged T-296 room runs): 14 / 18 rooms = (perimeter - door
- passage) x 0.20 exactly (walls only, Q-35 C), none = perimeter x 0.20 (the reading that would double the 0.20 m doorway
transition), 1 HELD (GF wet zone). Three lines lower than walls only, none higher: 1F-R48CDA5 1.480 vs 1.580 (-0.100 m2,
the W18 deduction from the upturn, ENGINE_WRONG already owned by T-310), GF-RB28769 1.20102 vs 1.201962 (-0.000942 m2,
0.0047 lm), GF-RDBD4F9 1.32864 vs 1.579771 (-0.251131 m2, 1.2557 lm of the walk not under the upturn): not overlaps;
residuals named in section 3.1 from the candidate run. Verdict proposal: NO DOUBLE COUNT on the candidate (DOORWAY vs
FLOOR 0.000 m2; DOORWAY_TRANSITION vs UPTURN 0.000 m2 by Q-35 C walls only); the old flag DOORWAY_DOUBLE_COVERAGE_REVIEW
on V2.x FIN.WP.UPTURN (perimeter incl. doorways) is superseded on the candidate path by the walls-only line.

## 4. Joinery-backed dressing faces (F-C-T483-1)

1F dressing 1F-RFFE7AF (T-481 walk 5.100 lm): the wardrobe is drawn on layer 5 as a 0.500 m deep box, front line B0A
1.800 m parallel to the E wall B00 and one corner-to-corner diagonal BE3 1.868 m. Joinery-backed faces: E B00 1.800 +
N B20 0.500 (the box end) + S AD4 0.500 (the box end) = **2.800 lm**; open faces W 1.000 + N 1.150 + S 0.150 =
**2.300 lm** (2.300 + 2.800 = 5.100, AGREES with T-481). Evidence read: every one of the 665 plan texts (no wardrobe,
joinery, cupboard, plinth or skirting word in English or Arabic), the insert names, and the merged finding that no finish
schedule exists (T-325). The diagonal is a drafting symbol, not a printed specification: whether the wardrobe is fitted
joinery in the contract and whether it carries its own plinth is NOT printed.

| face | lm | class | basis |
|---|---|---|---|
| W B03 / B04 | 1.000 | SKIRTED | open wall face, door D315 deducted (T-481) |
| N B20 (open part) | 1.150 | SKIRTED | open wall face |
| S AD5 | 0.150 | SKIRTED | open wall face west of the arch |
| E B00 | 1.800 | HELD JOINERY_SCOPE_NOT_PRINTED | wardrobe front B0A in front; no text, schedule or owner rule |
| N B20 (box end) | 0.500 | HELD JOINERY_SCOPE_NOT_PRINTED | the same box |
| S AD4 | 0.500 | HELD JOINERY_SCOPE_NOT_PRINTED | the same box |

Stream F proposal: split the V3.0.51 dressing walk into 2.300 lm SKIRTED (DRAWING-CONFIRMED) and a named piece 2.800 lm
bounded [0, 2.800] HELD JOINERY_SCOPE_NOT_PRINTED (FIN.SKIRTING certain -2.800 lm, held high +2.800 lm), never 0, never
dropped; it is released either way by a drawing note, the joinery specification or an owner rule. No owner question is
raised (ERS s.2.7: a 2.8 lm scope item, not safety-critical; the Lead may add it to an owner package).

## 5. Lessons-register row (proposed, ERS s.7)

| date | issue | cause | general rule | test | status |
|---|---|---|---|---|---|
| 2026-11-04 | A 0.467 m window (W18) had no engine opening on any version; every trade repaired it by its own ledger (T-175, T-274, T-305) | the band opening minimum 0.50 m (and 0.40 m on curved bands) drops narrower gaps silently; repairs were per project, not in the engine | every jambed wall gap of any width is reported once and classed by drawing evidence (window / door -> deducted, junction -> not an opening, unexplained -> HELD); no width minimum decides that an opening does not exist (every villa, all opening-based trades) | tests/t460_small_openings (0.40 m window reproduced and deducted; rotation, mirror, m units; junction; bare gap HELD; height missing HELD) | PROPOSED |
