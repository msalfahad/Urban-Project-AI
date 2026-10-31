# T-393 Railing scope reconciliation, run by run (development villa; method every villa)

Worker 2 (lane A), 2026-10-31. Research files `research/agents_t393/*` and `tests/t393_railing_runs/` only; no engine,
rule, knowledge, method, registry or candidate file touched; no candidate quantity changed (corrections are a lane I fix
proposal, section 6). ERS applied (s.2.1 physical element first, s.2.2 evidence, s.2.4 reconciliation, s.4 rule + test,
s.7 lesson). Rules: UP-STAIR-012 v2.0.0 (installed 3D path), UP-STAIR-013 (wall handrail only where shown), owner stair
rules S-1 .. S-9 (OWNER_RULE_STAIRS_2026-10-24, S-9 (4) "release BOQ quantities individually according to their own
required evidence", correction 2 "HELD quantities remain blank"), Q-46 A (section A-A counts), WORKFLOW_CONTROLS s.5.
No image, client name or title-strip text is copied here.

## 0. What was read

| Source (Drive "Alsenan chalet project", read-only; private copies in .work/private) | Used for |
|---|---|
| P7757_DXF_COMPRESSED.zip (architectural DXF), by handle | ST-01 well bands GF / 1F / 2F, riser lines, turns, 2F guard; RL-04 plan band; NW elevation piers |
| p7757_arch_sheet10.pdf (section A-A), rendered 250 dpi, read by eye | rails drawn on every ST-01 flight and on D1; 5 winder risers at the GF -> 1F turn |
| research/agents_t184 (MERGED; flights, landings, Q-46 A) and research/agents_t164 (MERGED; run census) | riser counts, run lengths (cited, not re-derived) |
| Freelancer FIN workbook (23.6 MB) | NOT downloadable (connector limit); his 18.95 lm is a typed cover constant (`=B39`, research/alsenan_control_plane_01 BENCHMARK_CONFIDENCE_REGISTER: "not traceable to a detail row"): his own rows cannot be rebuilt |

T-164 reproduced first from the private DXF (`t164_alsenan.py`): every run figure identical (16.324, 2.400, 1.042,
16.153, 6.127).

## 1. Result: run table (a), lm

| Run / segment | Physical element | Installed lm | Status | Evidence / exact missing fact |
|---|---|---|---|---|
| RL-07 MS1-L | ST-01 GF -> +2.667 flight, inner (well) side | 3.089 | DRAWING-CONFIRMED (proposal) | GF band 157 / 151 solid to the cut, section A-A rail; 10 risers 0.1667 / 0.30 (T-184) |
| RL-07 MS1-U | +3.50 -> 1F +5.50 flight, inner side | 3.775 | DRAWING-CONFIRMED (proposal) | 1F band A8F / A90; A-A rail; 12 risers (Q-46 A; the plan draws 11 lines) |
| RL-07 MS2-L | 1F +5.50 -> +7.516 flight, inner side | 3.782 | DRAWING-CONFIRMED (proposal) | 1F band A8D / A8E, DXF dimension 3300; A-A rail; 12 x 0.168 |
| RL-07 MS2-U | +7.684 -> 2F +9.70 flight, inner side | 3.782 | DRAWING-CONFIRMED (proposal) | 2F band 1358 / 1359, dimension 3300; A-A rail; 12 x 0.168 |
| RL-07 T-1F-S | south well-end turn at 1F, both ends at +5.50 | 0.200 | DRAWING-CONFIRMED (proposal) | AC3 / AC4, dimension 200; R-T393-1: across 0.150 + legs 0.025 + 0.025, rise 0 |
| RL-07 G-2F | 2F floor-edge guard over the MS2-L opening | 1.325 | DRAWING-CONFIRMED (proposal) | 2F 138A / 138B centreline, horizontal at +9.70 |
| **RL-07 confirmed** | | **15.953** | | was 16.153 measured, all HELD |
| RL-07 T-MS2-LD | north well-end turn on the MS2-LD half landing | blank (plan 0.200, rise 0.168) | HELD | closing riser MS2-TR +7.516 -> +7.684: its place against the turn and the rail profile over it not drawn; landing levels scaled, not printed (T-184 MS2-TR held) |
| RL-07 T-MS1-N | GF -> 1F north turn: 5 winders MS1-T + the corner MS1-LD = ONE turn | blank (plan 0.200, rise 0.833) | HELD | rail profile over 5 winders converging at a 0.10 m well (ramp, newels or wreath) and its end heights not drawn |
| RL-04 | 1F sea balcony edge (+5.50) in front of W15 / W16 | blank (plan band 6.127) | HELD | what stands on the edge, its height and extent (section 3) |
| RL-05 | ST-02 round stair + 1F gallery (one drawn band) | 16.324 | DRAWING-CONFIRMED (T-164, unchanged) | in the candidate (FIN.RAILING) |
| RL-06 | 1F floor edge D-23 | 2.400 | DRAWING-CONFIRMED (T-164, unchanged) | in the candidate (MET.RAILING.GUARD) |
| RL-08 | ST-01b lobby flight D1, one rail | 1.042 | DRAWING-CONFIRMED (T-164, unchanged) | A-A only; second side not drawn, not added |
| GF-EXT (new) | GF: the well band continued SOUTH of its closure 155 / 156 to the shaft wall | none | UNKNOWN | 2C8 layer 5 (solid) 1.050 m with 2C9 layer 2 (hidden) beside it, plus the diagonal pair 2F1D / 2F1E 1.557 m; no level change printed across it; guard, edge line or cut-line convention not established; no figure, no line |

Each segment binds one physical key (BINDS column, RUN_TABLE_T393.csv); the table passes the single-binding check.

## 2. ST-01 (b): what changed and why

- **Physical element.** ST-01 is a dog-leg in a 2.50 m shaft: two 1.20 m flight lanes either side of a 0.10 m well, each
  lane edge on the well carries a 50 mm band (plan) = a rail on each flight (section A-A draws top and mid rail on every
  flight). GF -> 1F: MS1-L up the west lane, the north corner turns with 5 winder risers (Q-50 / Q-46 A text: "5 winder
  steps in its 1.20 x 1.20 corner"), MS1-U down the east lane to 1F. 1F -> 2F: MS2-L, half landing MS2-LD at the north,
  MS2-U to 2F, where a guard closes the opening over MS2-L.
- **Per-segment release (S-9 (4)).** T-164 held the whole 16.153 lm because two turns were undetermined. Each flight's
  pitch line has its own complete evidence (drawn band, drawn rail on A-A, merged riser counts), and the 1F south turn
  joins two ends at one level (+5.50), so it is measurable without a profile. 15.953 lm move from HELD to
  DRAWING-CONFIRMED (proposal for Gate A); 2 turns stay HELD, blank.
- **Turn geometry checked from first principles (R-T393-1).** Band outer edges A8D / A8F 0.200 apart, band 0.050 ->
  centres 0.150 apart; closing band centreline 0.025 beyond the first / last riser lines (AC0 / A97 stand 0.050 inside
  the band ends) -> turn = 0.150 + 0.025 + 0.025 = 0.200 m on both ends. T-164 took the closing band's OUTER line (0.200);
  the centreline path gives the same 0.200 here only because the risers stand 0.050 inside the band end: on another
  villa the two differ, so the method now computes the centreline path, never the outer line.
- **Double listing removed (R-T393-2).** T-164 held "MS1-T winder turn" and "MS1-LD half-landing turn" as two parts. MS1-LD
  (T-184, 1.20 x 1.20 at +3.50) is the corner the 5 winders turn in: the rail turns round the well end once. They are one
  held segment T-MS1-N (plan 0.200, rise 0.833). Releasing each later as a turn would have counted that corner twice.
- **Why the two turns stay HELD.** Each contains a rise (0.833 over the winders; 0.168 at the MS2-TR closing riser) inside a
  0.200 m plan path. The installed length depends on how the rail is built over that rise, which no sheet draws; a range
  (0.200 .. 0.261 for MS2-LD, or any figure for the winders) is not a quantity (owner correction 2). Size of what is held:
  plan 0.400 m, i.e. at most a few tenths of a metre on a 15.953 lm run.

## 3. RL-04 (b): why it stays HELD

The 1F plan draws a closed 50 mm band C85 / C86 (layer 5, the railing layer of every other run) 6.127 m long, with a
0.20 m pier outline (B32 / C7F) at its north end. The NW elevation (DXF, same drawing) draws the +5.50 slab edge 7.500 m
between two 0.20 m piers 0.50 m high above the slab (printed '50', DIM 29DE; 27D7 / 27DD), NO infill and no rail between
them except a single 1.000 m layer-5 line at pier-top level from the left pier (27E7), which reads as an unfinished rail,
not a drawn one. The French windows W15 / W16 are drawn down to +5.50, so the edge is reachable and open. Three facts are
missing: what stands there (railing / glazing / parapet), its height, and its extent (6.127 plan vs 7.500 elevation,
1.373 m apart). T-162's +5.50 -> +6.00 parapet chain reads the 0.50 piers as a parapet: cross-trade conflict stays with
the Lead (register). No figure in the candidate (correct); RFI below.

## 4. Internal railing vs the freelancer (c)

Ours valued interior in the candidate: RL-05 16.324 + RL-06 2.400 + RL-08 1.042 = **19.766 lm**; his 'internal railing'
**18.95 lm** (typed constant, no rows). Difference +0.816 lm (+4.3 %).

| Decomposition (his scope, a hypothesis, none proven) | Named measured causes | Unexplained |
|---|---|---|
| A: his row = ST-02 system + D-23 (RL-05 + RL-06 = 18.724) | RL-08 D1 lobby rail 1.042 (a flight in the other shaft) | **-0.226 lm** (he has more) |
| B: his row = ST-02 system only (16.324) | RL-06 D-23 2.400; RL-08 1.042 | -2.626 lm |
| C: his row = ST-01 (any figure) | - | not consistent: ST-01 alone is 15.953 confirmed + held turns + D1 |
| also tested: plan projection of RL-05 (15.118) + D-23 + D1 = 18.560 | - | +0.390 (does not close) |

Verdict proposal per cause: RL-08 1.042 **ENGINE_RIGHT on scope** (A-A draws it); the -0.226 remainder
**UNRESOLVED** (his row has no breakdown; candidates: a slightly longer gallery, a volute counted differently; none
measurable). Beyond the 0.816: ST-01's 15.953 lm (now confirmable) is outside his 18.95 under every decomposition: two
balustraded staircases are drawn (A-A for ST-01, the plan band for ST-02), his single number covers at most one ->
**ENGINE_RIGHT on scope, freelancer omission of one staircase** (proposal), never adopted because 18.724 is "close".

## 5. Designer RFI facts (rfi/B row proposals; nothing sent)

1. RL-04: on the 1F sea balcony edge (+5.50) in front of W15 / W16: railing, glazing or parapet? Height above +5.50?
   Extent: the 6.127 m plan band or the 7.500 m between the elevation piers?
2. ST-01 GF -> 1F winder corner: the inner rail over the 5 winders at the 0.10 m well (continuous ramp, newel posts or
   wreath) and its heights at both ends.
3. ST-01 MS2-LD half landing: printed levels of the landing and the position of the closing riser (+7.516 -> +7.684)
   against the rail turn (already open as T-184 MS2-TR; one RFI line, not two).
4. GF: the band 2C8 / 2C9 south of the well end to the shaft wall (1.050 m): a guard, an edge or a drafting line?

## 6. Lane I fix proposal (no candidate change in this task)

In the candidate, RL-07 carries no figure (16.153 HELD). Proposed: split RL-07 into the 8 segments of
RUN_TABLE_T393.csv; FIN.RAILING gains 15.953 lm DRAWING-CONFIRMED (after Gate A) and two HELD blank lines (T-MS2-LD,
T-MS1-N) instead of the two old held parts (MS1-T, MS1-LD), which must not both be carried (R-T393-2). FIN.RAILING would
move 17.366 -> 33.319 lm; MET.RAILING.GUARD unchanged 21.550; RL-04 stays blank. F-T199-1 (the 14 per-flight blank lines
of the plan reader) still needs its retirement decision before the split is wired, or the four ST-01 flights would have
two homes.

## 7. Rule, test, lesson

- **R-T393-1** (proposed, research, any villa): a well-end turn's plan path is the band centreline from the last riser of
  one flight to the first riser of the next; it is measured only when its rise is 0 or its rail profile is drawn,
  otherwise HELD with plan length and rise reported beside the blank. **R-T393-2**: one physical turn / return binds one
  segment (refuse duplicates). **R-T393-3**: a guard only on an open side or where drawn (UP-STAIR-013 kept).
- Tests: `tests/t393_railing_runs` (synthetic Villa D, hand calculation 9.104826 lm; adverse: return bound on both flights
  refused, winder turn without profile HELD None with the flights still released, undrawn walled-side guard refused, mm
  as m refused, mirrored / translated turn invariant, HELD with a number refused, reconciliation remainder printed).
- Lessons-register row proposed:

| 2026-10-31 | 16.153 lm of drawn ST-01 balustrade held for 9 days because two turns were undetermined; the two turns were one physical corner listed twice | the run was the unit of release and a held part held the whole run; landing and winder records came from different ledgers | release per segment on its own evidence (S-9 (4)); one physical turn binds one segment (any villa) | tests/t393_railing_runs | T-393 |

## 8. Self-gate and what is missing

self-gate: a (no engine / rule / candidate file; research + tests only) c (hand fixture non-Alsenan, adverse cases)
d (files on the branch, reproducible with `python3 -I research/agents_t393/t393_alsenan.py <DXF> --write`) f (no new item
code, nothing wired) h (no client data in tracked files) PASS.
Missing: the freelancer's breakdown (his row is a constant; the FIN workbook is over the connector limit); the four RFI
facts; heights and materials of every interior railing (not printed).
