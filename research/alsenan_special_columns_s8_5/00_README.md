# S8.5: special columns (turned, dead and planted)

Baseline `9a82950`. Frozen before any comparison: `17_S8_5_FREEZE_MANIFEST.json`, `references_read: []`.

## The six records

| record | family | column owner(s) | event | support / parent |
|---|---|---|---|---|
| SPC-TURN_COLUMN-GFRS-31F | TURN | COL-C8-X15-Y06-GF, COL-C8-X15-Y06-1F | TURN_ORIENTATION_CHANGE at GFRS (FFL +5.50 m) | its own chain (foundation segment, footing) |
| SPC-TURN_COLUMN-GFRS-324 | TURN | COL-C9-X13-Y08-GF, COL-C9-X13-Y08-1F | TURN_ORIENTATION_CHANGE at GFRS (FFL +5.50 m) | its own chain (foundation segment, footing) |
| SPC-DEAD_COLUMN-GFRS-38A | DEAD | COL-C11-X06-Y04-GF | TERMINATION at GFRS (FFL +5.50 m) | its own chain (foundation segment, footing) |
| SPC-PLANTED_COLUMN-GFRS-544 | PLANTED | COL-P.C-X08-Y02-1F | PLANTED_START at GFRS (FFL +5.50 m) | UNRESOLVED (NODE: BM-GF_ROOF-B27-BL002-532, BM-GF_ROOF-B4-BL022-497, BM-GF_ROOF-B5-BL022-498, SPAN:GFRS:BL002:2844-4653) |
| SPC-PLANTED_COLUMN-GFRS-548 | PLANTED | COL-P.C-X15-Y02-1F | PLANTED_START at GFRS (FFL +5.50 m) | BM-GF_ROOF-B26-BL014-4CC |
| SPC-PLANTED_COLUMN-FFRS-77C | PLANTED | COL-P.C-X?-Y?@24888-15994-2F | PLANTED_START at FFRS (FFL +9.70 m) | UNRESOLVED (NODE: BM-1F_ROOF-B1-BL014-6D0, BM-1F_ROOF-B19-BL029-6CF, BM-1F_ROOF-B6-BL014-6C5, SPAN:FFRS:BL029:26630-29105) |

Each label binds by drawing geometry. A T.C circle encloses the GF outline and meets or encloses the turned 1F outline; the D.C circle encloses the dead column. A P.C label reaches, through its leader, a circle centred on the outline, with its bar text beside it. Each label is an event on an ordinary S1 / S3.1 column, never a second column.

## Released

- Concrete: **0 m3**. Every column keeps its S2 concrete owner. No head, plinth or thickening is drawn.
- Incremental reinforcement: **0 kg** (Ø16 0, Ø8 0). No special role is both required by the source with a fixed quantity and unowned by an earlier stage.

## Already counted (not added again)

- TC-31F-05: S3.1 12.642 kg
- TC-324-05: S3.1 12.642 kg
- PC-548-08: S6.1 12.009877 kg
- The ordinary bars, anchorages and ties of all eight segments stay S3.1's: 31F 261.244 kg, 324 270.087 kg, 38A 139.077 kg, 544 109.976 kg, 548 78.65 kg, 77C 80.212 kg.

## Blocked (10_BLOCKED_COMPONENTS.csv)

- BL-TC-31F-04: SECTION_TRANSITION_BENDS (Q-03)
- BL-TC-31F-06: EXTRA_BAR_TOP_CRANK (Q-02)
- BL-TC-31F-10: SPIRAL (Q-01)
- BL-TC-324-04: SECTION_TRANSITION_BENDS (Q-03)
- BL-TC-324-06: EXTRA_BAR_TOP_CRANK (Q-02)
- BL-TC-324-10: SPIRAL (Q-01)
- BL-DC-03: TOP_TERMINATION_BENDS_AND_HOOKS (Q-07)
- BL-DC-04: SPECIAL_END_REINFORCEMENT (Q-07)
- BL-PC-544-05: STARTER_PROJECTION_ABOVE_BEAM (Q-06)
- BL-PC-544-06: STARTER_LEG_AND_FOOT_IN_BEAM (Q-06)
- BL-PC-544-07: STARTER_TOP_CRANK (Q-06)
- BL-PC-544-08: BEAM_EXTRA_4D16_PROJECTION (Q-04)
- BL-PC-544-09: BEAM_EXTRA_CRANK_HOOKS_AND_X (Q-08)
- BL-PC-544-10: BEAM_STIRRUPS_UNDER_COLUMN (Q-04)
- BL-PC-548-05: STARTER_PROJECTION_ABOVE_BEAM (Q-06)
- BL-PC-548-06: STARTER_LEG_AND_FOOT_IN_BEAM (Q-06)
- BL-PC-548-07: STARTER_TOP_CRANK (Q-06)
- BL-PC-548-09: BEAM_EXTRA_CRANK_HOOKS_AND_X (Q-08)
- BL-PC-77C-05: STARTER_PROJECTION_ABOVE_BEAM (Q-06)
- BL-PC-77C-06: STARTER_LEG_AND_FOOT_IN_BEAM (Q-06)
- BL-PC-77C-07: STARTER_TOP_CRANK (Q-06)
- BL-PC-77C-08: BEAM_EXTRA_4D16_PROJECTION (Q-05)
- BL-PC-77C-09: BEAM_EXTRA_CRANK_HOOKS_AND_X (Q-08)
- BL-PC-77C-10: BEAM_STIRRUPS_UNDER_COLUMN (Q-05)

## Sensitivity (not released)

- SA-31F-SPI-C: circular spiral of the largest centreline diameter that fits the 200 mm side (142 mm), 12 turns at 166.667 mm -> 2.25765 kg
- SA-31F-SPI-E: elliptical spiral of the largest centreline that fits the overlap (142 x 192 mm), 12 turns -> 2.622998 kg
- SA-31F-CONT: the upper bars embedded the full 1 m below the turn instead of a 40D lap: + 360 mm per bar, 4 bars (those drawn inside the spiral) to 12 bars (every upper bar) -> 2.275556 - 6.826667 kg
- SA-324-SPI-C: circular spiral of the largest centreline diameter that fits the 200 mm side (142 mm), 12 turns at 166.667 mm -> 2.25765 kg
- SA-324-SPI-E: elliptical spiral of the largest centreline that fits the overlap (142 x 192 mm), 12 turns -> 2.622998 kg
- SA-324-CONT: the upper bars embedded the full 1 m below the turn instead of a 40D lap: + 360 mm per bar, 4 bars (those drawn inside the spiral) to 12 bars (every upper bar) -> 2.275556 - 6.826667 kg
- SA-544-EXTRA-B27: host B27 (BM-GF_ROOF-B27-BL002-532): DEPTH 850 mm, column 576.6 mm along the beam (drawn) -> 14.390334 kg
- SA-544-EXTRA-B4: host B4 (BM-GF_ROOF-B4-BL022-497): DEPTH 500 mm, column 700 mm along the beam (drawn) -> 10.745679 kg
- SA-544-EXTRA-B5: host B5 (BM-GF_ROOF-B5-BL022-498): DEPTH 500 mm, column 700 mm along the beam (drawn) -> 10.745679 kg
- SA-544-LINKS: extra links under the column by host: B27 0, B4 2.8, B5 2.8 -> 2.8 links
- SA-544-STARTER: separate starters, one per column bar (10), projection only -> 15.802469 kg
- SA-548-EXTRA-B26: the drawn footprint's length along B26 (212.9 mm at 88.51 deg) instead of S6.1's 200 mm column width (its stated lower bound); the role stays S6.1's -> 12.091513 kg
- SA-548-STARTER: separate starters, one per column bar (8), projection only -> 12.641975 kg
- SA-77C-EXTRA-B1: host B1 (BM-1F_ROOF-B1-BL014-6D0): DEPTH 400 mm, column 400 mm along the beam (drawn); 500 mm with the labelled 20x50 -> 7.585185 kg
- SA-77C-EXTRA-B19: host B19 (BM-1F_ROOF-B19-BL029-6CF): DEPTH 750 mm, column 246.7 mm along the beam (drawn); 258.7 mm with the labelled 20x50 -> 11.040676 kg
- SA-77C-EXTRA-B6: host B6 (BM-1F_ROOF-B6-BL014-6C5): DEPTH 500 mm, column 400 mm along the beam (drawn); 500 mm with the labelled 20x50 -> 8.849383 kg
- SA-77C-LINKS: extra links under the column by host: B1 1.6, B19 0, B6 1.6 -> 1.6 links
- SA-77C-STARTER: separate starters, one per column bar (8), projection only -> 12.641975 kg

## Conflicts and questions

- **C-01** (RESOLVED_BY_FROZEN_OWNER): PRE-S8 records the twisted extras as 'none (no S3-S7 stage)' and assigns '4Ø16 + spiral' to S8. S3.1 already holds 4Ø16 x 2 m on each GF segment (31F 12.642 kg, 324 12.642 kg, LOWER_BOUND), with the spiral blocked. S8.5 adds no 4Ø16.
- **C-02** (RESOLVED_BY_FROZEN_OWNER): PRE-S8 records the planted columns as 'column not in S3.1' and assigns 'column + 4Ø16 support bars' to S8. S3.1 holds each planted column's bars, anchorages and ties, and S6.1 holds 548's beam extra. S8.5 re-adds neither.
- **C-03** (RESOLVED_BY_FROZEN_OWNER): PRE-S8 records the dead column as 'none (no S3-S7 stage)'. S3.1 holds its bars and a 40D top anchorage (PROVISIONAL). Only the undrawn termination form stays open.
- **C-04** (OPEN): S1 reads P15-PLANTED as 'column bars anchored 100 into the beam' (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.). On the plot the '100' runs from the beam top up to the bars' crank: a 1.00 m projection ABOVE the beam (VR-S8.5-04).
- **C-05** (OPEN): 77C: drawn 20x40 (FFRS 77B / SFRS 778) vs labelled and scheduled 20x50. S3.1 STR-COL-022 uses the schedule; S2 holds its concrete PROVISIONAL.
- **C-06** (OPEN): C9 1F (turn 324): drawn 20x100 vs scheduled 20x90 (S3.1 STR-COL-020). The 200 x 250 overlap is the same under both.
- **C-07** (OPEN): The twisted elevation draws 25 horizontal lines over the 2 m zone (about 12.5 per m). The stated spiral is 6Ø8/m. The drawing is consistent with 6/m ties plus 6/m spiral drawn together; the label states only the spiral. The stated rate is the only quantity statement.
- **C-08** (OPEN): Eight bars are drawn inside the spiral and '4Ø16 EXTRA' points at two of them. Which four are extra is not drawn. The straight quantity (4 x 2 m) does not depend on it.
- **C-09** (OPEN): 544: the planted-column detail shows a column on a beam spanning between two columns. The column here sits on a beam-on-beam node: BM-GF_ROOF-B27-BL002-532 (AT_END), SPAN:GFRS:BL002:2844-4653 (AT_END), BM-GF_ROOF-B4-BL022-497 (AT_END), BM-GF_ROOF-B5-BL022-498 (AT_END). S6.1 marks the planted-column extra NOT_APPLICABLE on each, and PRE-S6 found no carrying span.
- **C-10** (OPEN): 77C: the planted-column detail shows a column on a beam spanning between two columns. The column here sits on a beam-on-beam node: BM-1F_ROOF-B1-BL014-6D0 (AT_END), BM-1F_ROOF-B6-BL014-6C5 (AT_END), BM-1F_ROOF-B19-BL029-6CF (AT_END), SPAN:FFRS:BL029:26630-29105 (AT_END). S6.1 marks the planted-column extra NOT_APPLICABLE on each, and PRE-S6 found no carrying span.
- **C-11** (OPEN): 77C candidate host BM-1F_ROOF-B6-BL014-6C5 (drawn 200 vs schedule 250 mm): the drawn width conflicts with the schedule (S6 BLOCKED). The sensitivity uses the schedule depth.
- **Q-01** (OPEN): Twisted columns: the spiral's diameter (or its centreline dimensions in the 200 x 250 overlap), cover, closing turns. Does it supplement the ordinary ties in the 2 m zone or replace them?
- **Q-02** (OPEN): Twisted columns: which four of the eight bars are the 4Ø16 extras, and the length of their top crank? Is the bottom end plain?
- **Q-03** (OPEN): Twisted columns: do the upper column's bars start 1 m below the turn (as drawn) instead of a 40D lap, and what are the lower bars' top bends?
- **Q-04** (OPEN): P.C 544: which beam carries it? B27 ends, B5 ends and B4 starts under it, and BL002 continues past it as an untagged span. Does the 4Ø16 / 10 cm-link detail apply, and along which beam?
- **Q-05** (OPEN): P.C 77C: which beam carries it? B1 ends, B6 starts and B19 ends under it, and BL029 continues past it as an untagged span. Is the section 20x40 (drawn) or 20x50 (label)? Does the detail apply?
- **Q-06** (OPEN): Planted columns: are the bars rising '100' above the beam separate starters lapping the column bars, or the column bars themselves? How many, and how long are the leg, the foot and the crank?
- **Q-07** (OPEN): Dead column C11 at X06-Y04: how do its bars terminate in B27 / B1 / the GF roof (bend, hook, length)? Is any special end reinforcement required?
- **Q-08** (OPEN): Planted-column detail: what is the unlabelled X in the beam under the column (the cranked 4Ø16, or separate diagonal bars)?

## Outputs

- `00_README.md`
- `01_SOURCE_AND_ANNOTATION_REGISTER.csv`
- `02_SIX_OCCURRENCE_POPULATION.csv`
- `03_COLUMN_PARENT_CROSSWALK.csv`
- `04_TWISTED_COLUMN_REINFORCEMENT.csv`
- `05_PLANTED_COLUMN_REINFORCEMENT.csv`
- `06_DEAD_COLUMN_TERMINATION_AUDIT.csv`
- `07_CONCRETE_QTO.csv`
- `08_INCREMENTAL_REBAR_QTO.csv`
- `09_INTERFACE_RECONCILIATION.csv`
- `10_BLOCKED_COMPONENTS.csv`
- `11_SOURCE_CONFLICTS_AND_QUESTIONS.csv`
- `12_OWNERSHIP_DELTAS.csv`
- `13_SENSITIVITY_CASES.csv`
- `14_CONSERVATION_CHECKS.csv`
- `15_PROVENANCE.jsonl`
- `16_S8_5_SUMMARY.json`
- `17_S8_5_FREEZE_MANIFEST.json`

Rebuild: `python3 -I research/alsenan_special_columns_s8_5/build_s8_5.py` (byte-identical). Renders and crops of the drawings stay outside git.
