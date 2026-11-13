# T-750 stage: WATERPROOFING + ROOF H4 integration package ARCH_TAKEOFF_V3.0.80 (worker 3, lane I, 2026-11-13)

STATUS: INCOMPLETE STAGE (code + inputs + synthetic tests done; the run of record is NOT done). Integration package for
Checker Gate B once the run of record and L4 exist. Nothing is VERIFIED or released; released default V2.9 + route G
untouched.

Base: stacked on agents/task-T-314 @ 597d2820 (V3.0.79, READY Gate B; itself on T-738 r2 V3.0.78). The Lead row named
T-738 49d21678 as base with "rebase on T-314 r3 when it merges"; T-314 r3 was already READY on top of T-738 at claim, so
this package extends V3.0.79 directly (one chain T-738 -> T-314 -> T-750; Gate B order unchanged). If T-314 r3 is
rejected or changes, re-run `t750_inputs.py` against its new line index (pins) and the run script; never by hand.

Blocker of this run: the Google Drive connector failed to connect (HTTP 503), so the drawings could not be fetched and
`v3080_run.py` (the whole chain from the DXFs) could not run. Next run: fetch the Drive copies, run
`bash scripts/agent_env.sh run --tree task-T-750 research/agents_t750/v3080_run.py <plan> <structural> --out
.work/private/t750 --t167 <dir>`, then write LINE_INDEX_V3_0_80 / summary / ledger / diff into `out/`, L4 to the end.

## Files
- `engine/source/arch_v3080.py`: WP_GATE_B_V1 + ROOF_LAYER_GATE_B_V1, rule R-T750-1 (every villa).
- `tools/urban_boq_m9.py`: hub hunk (method chain .80 -> .79, `--v3080-inputs`, guard, branch, choice).
- `research/agents_t750/t750_inputs.py`: URBAN_V3080_INPUTS_V1 from pinned merged ledgers (T-691 5e4fdc33, T-702
  b90d85af, T-710 4a34ced0, T-734 3d8185fe) through the merged T-748 H4 map (071dc837), bound to LINE_INDEX_V3_0_79
  (aa0ec38a). `out/T750_WIRE_TABLE.json` = per-line before / after (`--check` rebuilds).
- `research/agents_t750/v3080_run.py`: the run of record wrapper (T-314 r3 v3079_run + V3.0.80).
- `tests/t750_wp_roof/`: villa W750 by hand (17) + the inputs builder (5): 22 pass.

## Per line, before (V3.0.79) -> after (V3.0.80), by the wire table (units never mixed)
| group | lines | before | after | status (WORKFLOW_CONTROLS s.5) |
|---|---|---|---|---|
| FIN.WP.PENETRATION firm (FD printed, no W.C.) | 5 | HELD blank | HELD point 1 pcs each | DRAWING-CONFIRMED |
| FIN.WP.PENETRATION with a W.C. pan | 12 | HELD blank | HELD 1 .. 2 pcs (11), 2 .. 3 pcs (1R8BDA49) | HELD (W.C. outlet unprinted) |
| FIN.WP.PENETRATION pantry GF-RC99C2A | +1 | no line | HELD point 1 pcs | DRAWING-CONFIRMED |
| FIN.WP.WALL_UPTURN pantry L-8090ff20 | 1 | HELD blank | HELD 1.400 .. 1.900 m2 | HELD (W09 / W10 sills, D-45) |
| FIN.WP.DOORWAY pantry D-GF-07 | +1 | no line | HELD point 0.200 m2 (1.000 x 0.200) | DRAWING-CONFIRMED |
| FIN.WP.DOORWAY_TRANSITION_NR pantry | +1 | no line | HELD point 1 pcs | DRAWING-CONFIRMED |
| FIN.WP.TERMINATION pantry open side | +1 | no line | HELD point 4.500 lm (4.000 + 0.500) | ASSUMED — OWNER-APPROVED (Q-37 A) |
| FIN.WP.DOORWAY_TRANSITION m2 pantry | +1 | no line | HELD BLANK, DESIGNER (no threshold detail) | HELD |
| FIN.ROOF.SCREED ROOF-430 / ROOF-970 / TERRACE-550 | 3 | HELD blank | HELD blank, AT LEAST 3.324832 / 4.791492 / 2.512672 m3 beside | ASSUMED — OWNER-APPROVED (Q-41 scope) |
| FIN.ROOF.INSULATION x3, PROTECTION x3 | 6 | HELD blank | HELD blank, cause named (D-39 / carried by the Q-41 screed) | HELD |
| 2F top roof ROOF-1390 screed / finish / insulation / protection | 4 | HELD blank | HELD blank, owner Q-34 PARKED named | HELD |

Totals expected (to be confirmed by the run): FIN.WP.PENETRATION 17 -> 18 lines, blank 17 -> 0, held 19 .. 31 pcs
(T-691 low_pcs / high_pcs). Screed lower ends 10.628996 m3 beside only (= T-646 AT_LEAST 10.63; never in a total).
Released quantities: none move (asserted in integrate / check_lines / check_totals).

Hand checks (from the merged ledgers' printed dimensions): pantry box 4.500 x 3.000; released wet floor 13.455 m2 =
13.500 - column 0.050 x 0.900 (consistent); termination = the open east side 4.000 + 0.500 = 4.500 lm; doorway = gap
1.000 x wall 0.200 = 0.200 m2; wall upturn low 1.400 = 7.000 m wall run x 0.200 (box perimeter 15.000 - open side 4.500 -
door 1.000 - window gaps 1.000 + 1.500), high 1.900 = + the two window gaps 2.500 x 0.200 while the sills are unprinted;
penetrations 5 x 1 + 1 + 11 x (1 .. 2) + (2 .. 3) = 19 .. 31.

## Owner manual method vs drawing-derived method
- WP: owner = membrane floor + upturn (run x height less door gaps) + one transition per door + one penetration per
  floor outlet; drawing = box line from the dimensioned plan, drains from the sanitary layout, W.C. outlet open.
- Roof: owner = screed m3 = area x mean thickness (t0 + half the falls rise); drawing = finish hatch areas measured,
  1 % falls printed, t0 and layer thicknesses unprinted (D-39): screed AT LEAST its falls volume, other layers blank.

## Not wired (statements, named in `out/T750_WIRE_TABLE.json`)
- IGNORED_SMALL (owner materiality 2026-11-13, below 1 % of the line): roof upturn L-5ce5ba49 92.922 -> 92.925396 lm
  (+0.003 lm, 0.004 %, would raise a released value: stays 92.922); ledge membrane L-2361d6ec 0 .. 0.639573 m2; ledge
  upturn L-d7d1bf8c 0 .. 3.528277 lm; window-run upturn L-1954878b 0 .. 0.500002 lm.
- CARRIED: roof membrane L-636fd3ff already HELD 115.656474 .. 115.813974 m2 (V3.0.76 carried the Checker downgrade;
  D-BAND 0.1575 m2 inside the band).
- T-710 duplicates (22) of the T-691 rows; state-only rows (33: DESIGNER / NEEDS_OWNER_RULE / NO_PHYSICAL_ELEMENT);
  T-702 finish rows KEEP (released 54.9203 / 115.65646 / 31.643 m2).
- D-41 sunken wet-room panels 0 .. 13.335040 m2 (loop 51.8980 m): HELD component, no line (DESIGNER_QUESTIONS item 9),
  listed in WAITING; never 0 by omission.

## Validation on this stage
- tests/t750_wp_roof 22 pass; freeze 0; codemap stale none (maps rebuilt by the tool).
- Registry tests t199 / t284 / t310 / t328 / t459 fail 29 + 1 IDENTICALLY on the clean T-314 r3 head 597d2820 (pending
  1.79.0 / 1.80.0 promotion; the T-314 handoff said 2): pre-existing, not this package's. BOQ_FAMILY_MASTER next version
  for V3.0.80 is built at promotion time (merge-order rule), as T-314 r3 does.
- NOT DONE: the run of record (Drive 503), L4 full suite, per-line hand check on the real lines, LINE_INDEX_V3_0_80.

## Verdict proposals vs freelancer
Not formed in this stage (no run): the WP family carries no freelancer comparison until the run exists.
