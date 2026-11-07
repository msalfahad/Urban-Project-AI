# T-586 reconciled-quantities statement V6 (generated; reference - engine, + = in the reference only)

V6 = statement V5 (T-579, rebuilt and equal to its committed output; every V5 section unchanged except the pads label) + the sections below. Development villa; not an accuracy claim; nothing released.

## New sections (V6)

| Section | Kind | Unit | Reference | Engine valued | Difference | % of ref. | By class (non-zero, net) |
|---|---|---|---|---|---|---|---|
| T-571/lintel-count-implied | IMPLIED_COUNT | nr | 54 (implied) | 60 | -6 | none | UNRESOLVED -6 |
| T-574/skirting-room | DIFFERENCE | lm | 282.85 | 197.278592 | 85.571408 | none | ENGINE_RIGHT 32.082629, RULE_DIFFERENCE 43.62, TOLERANCE 0.175545, UNRESOLVED 9.693234 |
| T-574/skirting-stairs | DIFFERENCE | lm | 29.87 | 12.15 | 17.72 | none | HELD 17.009049, UNRESOLVED 0.710951 |
| T-574/skirting-pieces | DIFFERENCE | nr | 96 | 0 | 96 | none | RULE_DIFFERENCE 96 |
| T-574/skirting-outdoor | DIFFERENCE | lm | 81.32 | 0 | 81.32 | none | UNRESOLVED 81.32 |
| T-577/marble-m2 | DIFFERENCE | m2 | 5.1 | 18.0382 | -12.9382 | none | ENGINE_RIGHT -11.6888, RULE_DIFFERENCE -1.250, TOLERANCE 0.0006 |
| T-577/marble-lm | DIFFERENCE | lm | 21.7 | 56.83 | -35.13 | none | ENGINE_RIGHT -49.13, RULE_DIFFERENCE -4.9, UNRESOLVED 18.9 |
| T-577/marble-nr | DIFFERENCE | nr | 11 | 67 | -56 | none | ENGINE_RIGHT -47, RULE_DIFFERENCE -9 |

### Lintels by stock length (T-571, nr; implied = his openings through the owner rule, not his figure)

| Length (m) | Implied | Engine AT_MOST | Implied - engine |
|---|---|---|---|
| 1.2 | 27 | 30 | -3 |
| 1.5 | 17 | 20 | -3 |
| 2.5 | 8 | 9 | -1 |
| 3.0 | 1 | 1 | 0 |
| 4.0 | 1 | 0 | 1 |

Established engine lintels 16 nr; lm beside (never summed with nr): implied 84.9 vs engine 91.5 lm. No %.

Skirting rooms (T-574): gross vs gross (outline terms) 282.85 vs 276.159097 lm, difference 6.690903 (2.37 % of ref.); deduction terms 78.880505 lm (he deducts none); net 30.25 % is NOT a verdict.

### B11 dome / ring / lift-wall rebar (T-575, t; beside: V8 manifest rows, not candidate lines)

| Row | Status | Range (t) / blank | T-560 group |
|---|---|---|---|
| DG5:DOME-3:SHELL:REBAR | HELD_BLANK | HELD_BLANK (no structural drawing of the third (tower) dome: architectur) | G5_STAIRS_DOME |
| HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY:REBAR | HELD_RANGE | 0.096638 .. 0.155966 | G5_STAIRS_DOME |
| HL:DOME_RING:DOME-1F-W:RING:RING_BEAM_B4_IN_BAY:REBAR | HELD_RANGE | 0.061166 .. 0.155966 | G5_STAIRS_DOME |
| HL:DOME_SHELL:DOME-A:SHELL:REBAR | HELD_RANGE | 0.287994 .. 0.425 | G5_STAIRS_DOME |
| HL:DOME_SHELL:DOME-B:SHELL:REBAR | HELD_RANGE | 0.287994 .. 0.425 | G5_STAIRS_DOME |
| LIFT_PIT:WALLS:REBAR | HELD_BLANK | HELD_BLANK (pit depth / wall height h not printed ('as per lift manufact) | G2_COLUMNS_NECKS_WALLS |
| Total | valued 0 | 0.733792 .. 1.161932 | |

EXPECTED after the V8 REBAR_OMISSION rows (beside only): G5 held 1.039160 .. 1.443671 + 0.733792 .. 1.161932 = 1.772952 .. 2.605603 t, residual after bounded held 1.294397 .. 2.127048 t (his TYPED_LUMP, no %).

V5 T-572/measured-footing_pads_and_straps: not split (F-C-T579-1): the -0.628000 m3 difference carries no cause rows in V5; its split lives in V4 T-551/footing-line (T-551 classes), never repeated here

## NOT_COMPARABLE blocks added in V6 (no difference, no %)

- T-571/lintel-figure (nr): reference NO_ROW
- T-577/length-in-area-column (lm (in his m2 column)): reference 21.7

Reclasses (R-T586-1 (e)): F-T586-1 T-577/marble-lm E1_STEPS: E1 has no FIN.STAIR.STEP_LM line while the other f ENGINE_OMISSION -> UNRESOLVED 11.2.

Reports covered: T-541, T-534, T-543, T-550, T-546, T-542, T-545, T-547, T-552, T-551, T-553, T-556, T-559, T-561, T-564, T-565, T-566, T-567, T-560, T-568, T-569, T-572, T-573, T-571, T-574, T-575, T-577; pending: T-576, T-578.
