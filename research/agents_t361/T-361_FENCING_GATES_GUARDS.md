# T-361 Fencing / gates (B13-04), posts / glass panels (B7-11) and the open-edge guard census (development villa; every villa)

Worker 2 (lane A), 2026-10-30, run session_01E6cPnbAuLqnGpBm9Ww5CUa. Research row: no engine, rule, knowledge, method,
registry or candidate line changed; nothing released. ERS read and applied (s.2.1 physical element first, s.2.2 evidence
hierarchy, s.2.3 first principles, s.2.4 reconciliation in units, s.4 rule + test, s.7 lesson). Rules: owner Q-63 C
(sea-side element HELD, unknowns incl. gate), Q-65 C (street fence 5.70 + 2.50 gate "subject to verification"),
OWNER_RULE_STAIRS_2026-10-24 s.4 (no code claim; private houses outside the Universal Design Code), UP-QTY-STATUS-001,
WORKFLOW_CONTROLS s.5 / s.8. Built on merged T-164 (railings, Checker re-measure 2026-10-22), T-162 (parapet chains),
T-150 / T-249 (opening census), T-253 (boundary bands); none re-derived except where this run read new evidence. Files
are cited by Drive folder and title, entities by DXF handle; no coordinates, image, client name or note text here.

## 0. What was read this run (Drive "Alsenan chalet project", read-only; private copies in .work/private only)

| Source | sha / size | Read for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip -> P7757.dxf | ab54dd55 | GF plan boundary lines, gate symbols, ST-03 edges; SE and NW elevations (sea gate, railing posts); hatch census |
| Alsenan_Architectural_P7757_Pages_11-12.pdf p.12 | 6,116,815 B | FENCE PLAN / FENCE ELEVATION / SECTION (200 dpi, by eye, nothing scaled) |
| p7757_arch_sheet03.pdf | 3,375,172 B | GF plan overview (plot sides printed) |
| freelancer blockwork workbook (sheet 'الكميات', 230 rows) and aluminium workbook (59 rows) | 6,164,004 / 6,152,749 B | fence / gate / railing / glass rows |

## 1. Results in engineering terms

**Gates (B13-04, pcs).** One gate leaf DRAWING-CONFIRMED, one gate opening with no leaf drawn:

| Id | Where | Opening | Leaf | Evidence | Status |
|---|---|---|---|---|---|
| G-01 | street fence, between the annex corner and the solid fence end | **2.50 m** (DXF HIDDEN polyline 110 = p.12 '250') | **NOT DRAWN** (no block, swing or layer-D symbol overlaps the gap; p.12 FENCE ELEVATION draws only a ground strip) | plan + p.12 plan + elevation | opening DRAWING-CONFIRMED; leaf count / type / height / material HELD, never 0, never an assumed leaf |
| G-02 | sea-side boundary at the end of the side passage, 0.30 m from the upper-neighbour corner | **1.00 m** (D120 block 2D8, single leaf, swing r 0.89) | **1 leaf drawn**: SE elevation leaf 0.90 x 2.10 with knob (23F1 / 23F2 / 23F6), frame 1.00 (23F4 / 23F3), head line 2.20 above the court line (23F8 / 23E5); NW elevation panel 1.30 x 2.50 (27FA) between pier 2880 / 2881 and the north fence end 27EA / 27EB | plan + 2 elevations | **1 pcs DRAWING-CONFIRMED (count, width)**; leaf / head sizes are DXF geometry, NOT printed; material, structure, hardware HELD (Q-63 C) |

New evidence: G-02 is the opening census's D-GF-15 (T-150 / T-249: "no sheet prints it"). Nothing PRINTS it, but the SE and
NW elevations DRAW it: RFI-B-A11 ("the fence drawing does not show it") should add that the elevations draw the gate
end (leaf 0.90 x 2.10, opening head 2.20, wall line 2.50, pier 0.20) so the designer confirms rather than re-draws. The
5.17 m solid part (8D) is not drawn in front of the pool drum on the NW elevation (height unknown, Q-63 C stands).

**Boundary lines (conservation, R-T361-2):**

| Line | Drawn (m) | Solid | Gates | Infill | Status |
|---|---|---|---|---|---|
| F-STREET | 8.30 (10F) | 5.80 | 2.50 (G-01) | X railing in the dip of the solid wall (p.12 elevation): length NOT PRINTED -> **HELD** (= T-164 RL-10) | lengths DRAWING-CONFIRMED; Q-65 C's 5.70 is 5.80 on the drawing (+0.10 m, already noted by T-164) |
| F-NORTH | 31.37 outer (99 + 98) / 30.97 inner (13A) | 31.37 | 0 | none drawn | blockwork lane (material Q-65 C HELD) |
| F-LOWER | 1.20 (86 / 106) | 1.20 | 0 | none drawn | blockwork lane (T-253 810#1) |
| F-SEA | 7.10 outer line, column face 2F96 -> plot corner | 6.10 | 1.00 (G-02) | NOT DRAWN | **HELD (Q-63 C)**; 7.10 outer = Q-63's 7.00 on the centreline to the north fence centreline (+0.10, half its 0.20): 0.000 residual |

**Fence infill / railing on fences:** street fence X railing HELD (length not printed, never scaled); sea element infill
NOT DRAWN (Q-63 C); north and lower fences: none drawn.

**Posts / glass panels (B7-11):** glass panels **NOT DRAWN** anywhere (DXF hatch patterns SOLID 59 / LINE 14 / NET 11 /
AR-PARQ1 2 / MUDST 1 / ANGLE 1, none glass; 24 distinct DXF texts, none names glass; no specification issued, RFI-B-A12):
m2 None, never a default. Posts are drawn only in the X railings of the roof elevations: RL-02 (NW, 4.921 m) **6 posts**
(pairs at 0.401 / 1.438 / 2.475 / 3.512 / 3.666 / 4.703 m from the rail end, panel 1.037 m; the single line 251F is not a
post); RL-01 street face (SE, 3.753 m) **4 posts** (0.10 / 0.96 / 1.84 / 2.71 m, panel 0.877 m). They are components of the
railing lm (T-164), reported as a drawn count, not a separate priced line (B7-11 needs a specification). RL-03 / fence
railing posts: raster only, not counted; stair balusters: not drawn on the plans (continuous 50 mm bands).

**Open edges (13; guard DRAWN 8, WALL 1, UNKNOWN 2, NONE_DRAWN 2):**

| Edge | Plan m | Guard | Reference |
|---|---|---|---|
| E-01 annex roof +4.30 | 28.428 | DRAWN | parapet +4.30 -> +4.80 (T-162) + RL-03 7.967 lm |
| E-02 GF roof +5.50 | 27.970 | DRAWN | parapet (T-162); RL-04 6.127 HELD (plan vs NW elevation); passage stop-end HELD 0 .. 1.20 |
| E-03 1F roof +9.70 | 48.784 | DRAWN | parapet + RL-01 6.262 + RL-02 4.921 |
| E-04 2F roof +13.90 | 28.300 | DRAWN | parapet closed ring |
| E-05 ST-02 inner + 1F void gallery | 16.324 | DRAWN | RL-05 |
| E-06 1F floor edge beside RS-A | 2.400 | DRAWN | RL-06 (D-23) |
| E-07 ST-02 outer side | - | UNKNOWN | RL-09 band 4.035 .. 4.455 (guard or string) |
| E-08 ST-01 well side | 16.153 | DRAWN | RL-07, two turns HELD |
| E-09 ST-01b D1, drawn side | 1.042 | DRAWN | RL-08 (section A-A) |
| E-10 ST-01b D1, second side | - | UNKNOWN | not established in this run |
| **E-11 ST-03 entrance stair, north (court) side** | **1.200** | **NONE_DRAWN** | layer-5 edge 368, drop 0 .. 0.85 m |
| **E-12 ST-03 top strip at +1.00** | **0.200** | **NONE_DRAWN** | layer-5 edge 367, drop 0.85 m |
| E-13 ST-03 south side | 1.200 | WALL | wall 15A / 158 (0.20) + column 2FAE |

The two NONE_DRAWN edges (1.40 m plan) are a finding for the Lead / designer list (T-164 RL-11 named the edge; this run
gives its length and that the SOUTH side is a wall); a guard requirement is CODE NOT VERIFIED and never a quantity.

**Cross-checks (d):** ids shared with the blockwork fence, the B7-10 handrail and the T-164 railing runs: **0**. The gate
widths are inside the fence lines, never solid metres (8.30 = 5.80 + 2.50; 7.10 = 6.10 + 1.00). G-02 = D-GF-15: the SAME
element as the door census row (SITE.GATE_HELD, no door line carries it): one gate.

## 2. Freelancer (who is right, proposals for the Checker)

| His row | Ours | Proposal |
|---|---|---|
| blockwork 'fence' 1 x 37.20 x 2.00 = 74.40 m2 | north 31.37 + street solid 5.80 = 37.17 m (+ lower 1.20, sea 7.10 HELD) | AGREE on his scope (+0.03 m, 0.08 %); no gate, infill or sea element in his sheet: RULE_DIFFERENCE (scope) |
| aluminium GF 'external door' 4 x 1.00 x 2.40 = 9.60 m2 | sea gate G-02 1.00 (leaf 0.90 x 2.10, head 2.20 drawn) | UNRESOLVED: his sheet has no location column; his 2.40 is not the drawn head 2.20 |
| none | street gate opening G-01 2.50, leaf HELD | HAND_FOUND (no row; neither side has a leaf quantity) |
| none | glass panels NOT DRAWN | AGREE (nothing to count) |

## 3. Rules, tests, lesson (ERS s.4 / s.7)

Rules (research, every villa) in `t361_rules.py`: R-T361-1 gate vs gate opening (a leaf counted only where drawn);
R-T361-2 one element, one quantity (solid + gates close on the drawn line; a gate in plan and elevation is one gate);
R-T361-3 open edges DRAWN / WALL / NONE_DRAWN / UNKNOWN, NONE_DRAWN never a guard quantity; R-T361-4 renders never make a
gate, infill, railing or guard; R-T361-5 glass only where drawn / specified, posts are railing components.

Tests `tests/t361_fencing_gates` (17): synthetic Villa F with hand values (12.00 = 8.50 + 3.50; 1.10 gate 1 pcs; 1.20 m
NONE_DRAWN edge), adverse (render gate, assumed double leaf, missing / zero width, leaf without count, gate inside the
solid fence, invented guard, contradictory guard, mm vs m, posts mirror-invariant, glass with a missing size), the
committed ledgers reproduce, pinned development-villa values, no coordinates committed.

Lessons-register row proposed: | 2026-10-30 | the sea-side gate recorded as "no sheet prints it" (T-150) and the
sea-side element as "the fence drawing does not show it" (RFI-B-A11) | only the plan and the fence sheet were searched; the
elevations draw the gate seen through the side passage | a gate / boundary census reads every elevation that looks along
the boundary, including views through a passage; "not printed" and "not drawn" are kept apart | t361 pinned G-02 evidence
| PROPOSED |

## 4. Missing / uncertain

- G-01 leaf (type, count, height, material) and G-02 material / structure / hardware: designer (RFI-B-A11 / Q-63 C,
  Q-65 C); nothing invented.
- Street fence railing length (not printed) and RL-03 / fence posts (raster only): HELD / not counted.
- E-07 / E-10 guard state; E-11 / E-12 guard (none drawn): designer list.
- The 0.232 m between the column face 2F96 and the wall end 39F (layer-D rectangle 39D) is taken as part of the solid sea
  element; its nature (pier or wall end) is not printed.

Reproduce: `python3 -I research/agents_t361/t361_extract.py <P7757.dxf>` (checks the committed input, `--write` to
rebuild), `python3 -I research/agents_t361/t361_alsenan.py --check`, `python3 -I research/agents_t361/t361_rules.py`.
