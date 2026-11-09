# T-643 rebar on HELD concrete + unbound bar lines (R-T643-1; ARCH_TAKEOFF_V3.0.58 (T-630 dry run, overlay V15))

## Part 1: the 14 RELEASED column main-bar lines on HELD concrete (F-T639-1)

Decisions {'DOWNGRADE': 4, 'KEEP': 10}: kept released 595.435 kg, proposed HELD 159.288 kg, total 754.723 kg. Released B11 9375.305760 kg -> 9216.017760 kg if the proposals are applied.

| column | mark | storey | n x d | L m | kg | concrete hold rule | enters | decision |
|---|---|---|---|---|---|---|---|---|
| COL-2F-50 | C2 | 2F | 6 x T16 | 4.2 | 39.822 | R-COL-LEVEL-HEIGHT-1 | L | DOWNGRADE |
| COL-2F-51 | C2 | 2F | 6 x T16 | 4.2 | 39.822 | R-COL-LEVEL-HEIGHT-1 | L | DOWNGRADE |
| COL-2F-53 | C1 | 2F | 6 x T16 | 4.2 | 39.822 | R-COL-LEVEL-HEIGHT-1 | L | DOWNGRADE |
| COL-2F-54 | C2 | 2F | 6 x T16 | 4.2 | 39.822 | R-COL-LEVEL-HEIGHT-1 | L | DOWNGRADE |
| COL-1F-31 | C4 | 1F | 8 x T16 | 4.2 | 53.096 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-32 | C5 | 1F | 8 x T16 | 4.2 | 53.096 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-33 | C4 | 1F | 8 x T16 | 4.2 | 53.096 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-39 | C9 | 1F | 12 x T16 | 4.2 | 79.644 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-41 | C9 | 1F | 12 x T16 | 4.2 | 79.644 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-44 | C6 | 1F | 8 x T16 | 4.2 | 53.096 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-1F-47 | C5 | 1F | 8 x T16 | 4.2 | 53.096 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-GF-14 | C3 | GF | 8 x T16 | 4.5 | 56.889 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-GF-24 | C | GF | 8 x T16 | 4.5 | 56.889 | R-COL-SECTION-CONFLICT-1 | none | KEEP |
| COL-GF-30 | C | GF | 8 x T16 | 4.5 | 56.889 | R-COL-SECTION-CONFLICT-1 | none | KEEP |

Downgrade-only record proposals (Checker to issue / validate):

- DGP-T643-fdb3ed374d73bff6 L-5fca13cebe2e259988bc 39.822 kg: UNSUPPORTED BASIS: COL-2F-50 main bars 6 T16 x 4.2 m use the storey interval to the roof; LEVEL.STRUCTURAL_TOP.ROOF.MAIN: not declared for this project (D-39_ROOF_DATUM; D-44_B15_UPSTAND_DOWNSTAND); the same member's con
- DGP-T643-943b0c58b76cdde2 L-4247172eb6f60bb0b98b 39.822 kg: UNSUPPORTED BASIS: COL-2F-51 main bars 6 T16 x 4.2 m use the storey interval to the roof; LEVEL.STRUCTURAL_TOP.ROOF.MAIN: not declared for this project (D-39_ROOF_DATUM); the same member's concrete line L-919a5749ef79759
- DGP-T643-ca59159efc4663e4 L-930151c44e50a06944a6 39.822 kg: UNSUPPORTED BASIS: COL-2F-53 main bars 6 T16 x 4.2 m use the storey interval to the roof; LEVEL.STRUCTURAL_TOP.ROOF.MAIN: not declared for this project (D-39_ROOF_DATUM); the same member's concrete line L-d79d17d14f39d51
- DGP-T643-196fcf58b2f70744 L-57836098c8dc67817e1d 39.822 kg: UNSUPPORTED BASIS: COL-2F-54 main bars 6 T16 x 4.2 m use the storey interval to the roof; LEVEL.STRUCTURAL_TOP.ROOF.MAIN: not declared for this project (D-39_ROOF_DATUM); the same member's concrete line L-26f6b6f2365c72e

## Part 2: the 208 bar lines with no recorded concrete binding

By binding: {'BOUND': 185, 'UNRESOLVED': 23}; newly also class A: 56.

| binding | family | concrete | lines |
|---|---|---|---|
| BOUND | HL:BEAM_STEEL | EXCLUDED | 4 |
| BOUND | HL:BEAM_STEEL | HELD | 3 |
| BOUND | HL:BEAM_STEEL | RELEASED | 30 |
| BOUND | HL:GROUND_SYSTEM_STEEL | HELD | 49 |
| BOUND | HL:GROUND_SYSTEM_STEEL | RELEASED | 69 |
| BOUND | HL:STAIR_POOL_TANK_STEEL | RELEASED | 30 |
| UNRESOLVED | HL:GROUND_SYSTEM_STEEL | - | 13 |
| UNRESOLVED | HL:STAIR_POOL_TANK_STEEL | - | 8 |
| UNRESOLVED | LINTEL_BARS:FLAGGED | - | 1 |
| UNRESOLVED | LINTEL_BARS:PRODUCED | - | 1 |

UNRESOLVED reasons:

- 7 x * -> face-handle pair * -> T-332 run(s) *, * -> concrete line(s); T-138 span numbering (-n) is not the T-242 r
- 6 x * -> face-handle pair * -> T-332 run(s) *, *, * -> concrete line(s); T-138 span numbering (-n) is not the T-24
- 2 x landing strip: which concrete line carries it is not recorded
- 1 x no concrete line names MS1-L; candidate: the remainder line P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS (HELD) a
- 1 x turn MS1-T has no concrete line of its own (T-111 turn HELD); MS2_TR is the other flight's
- 1 x no line names ST-01b; candidate: DG5:ST-01:LOBBY#CLOSABLE:DRAWING_CONFIRMED_D1_steps (RELEASED; lobby D1 steps
- 1 x curved part (owner Q-50 HELD): candidate the remainder line P-C:STAIRS:GROUND:SITE-4df8fcd99d130701 (HELD) aft
- 1 x court stair on no slab plan: no concrete line in the candidate
- 1 x water tank: only 'WATER TANK PLACE' printed; no concrete element in the candidate
- 1 x LINTEL_BARS:FLAGGED is one aggregate over the lintel population; the STR.CONC.LINTEL lines are 16 RELEASED / 4
- 1 x LINTEL_BARS:PRODUCED is one aggregate over the lintel population; the STR.CONC.LINTEL lines are 16 RELEASED / 

NOTHING RELEASED OR ADDED; no candidate, engine, rule / knowledge version or registry file changed; the DOWNGRADE rows are downgrade-only record proposals for the Checker (owner 2026-10-24 23:57)
