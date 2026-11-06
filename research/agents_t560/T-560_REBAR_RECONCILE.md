# T-560 B11 reinforcement: candidate V3.0.58 against the freelancer, by scope group (metric tons)

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPnbzrczrQeBPZVfV83g, branch
`agents/task-T-560`. Research only: no engine module, candidate line, released line, rule file or method version
changed; nothing released; no rebar calculation code changed (owner 2026-10-25 10:33 (1)). Development villa, not an
accuracy claim. ERS s.2 - 4 and s.7 applied; Q-71, OWNER_RULE_REBAR_2026-10-24 (kg inside, t at the boundary), owner
2026-10-25 10:33 / 11:51 (16.39 t route G = provisional subtotal; ledgers never added), R-T541-1, R-T543-1.

## 0. Sources and run

- Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED). STR.REBAR lines from
  `research/agents_t507/out/LINE_INDEX_V3_0_57.json` (sha256 fed5141e, pinned): V3.0.58 = V3.0.57 + 5 FIN.WP.ROOF lines,
  the 4,994 others byte-identical (T-507 s.6), so all 2,644 STR.REBAR lines are the V3.0.58 lines. Cross-check: the
  T-471 matrix C-B11-01 states the same 9,375.306 kg valued + 14,278.249 .. 19,646.878 kg held.
- Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook, downloaded this run, decoded into
  `.work/private` only, sha256 ae608411 = the B1 manifest; all 8 sheets re-read (values, formulas, comments, sheet
  state). The build reads only his seven family totals from the committed B1 census
  (`tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`, sha 752c9f4e); no element row of his is used or copied.
- Code: `t560_rules.py` (REBAR_TONNAGE_RECONCILE_V1, R-T560-1 .. 5), `t560_alsenan.py` (build; `--check` rebuilds and
  compares) -> `out/T560_REBAR_RECONCILE.json` (per family, per bar group, per scope group). Run:
  `.work/venv/bin/python -I research/agents_t560/t560_alsenan.py --check`.

## 1. Physical element and units (ERS s.2.1)

A bar group of one structural element (main / bottom / top bars, links, side bars, starters and laps where a note
governs, bar ends and anchorages), mass = developed length x unit mass. kg inside; t = kg / 1000 once, 6 dp. Installed
(net) and procurement (waste, offcuts, transport laps; B11-04, no line yet) are separate accounts. A ratio (kg per m3
of concrete) is not a bar population and is never compared as if counted.

## 2. What his rebar rows are (the engineering question)

- **Per element or per m3?** Neither is printed. His workbook has **no bar row**: no diameter, count, spacing, length or
  kg anywhere in 8 sheets (re-read cell by cell). Steel appears only in the summary sheet: header "steel quantities (t)"
  and seven family cells beside his concrete totals, each a **typed constant with no formula** (2 dp), and a typed
  total 44.19 t that equals their sum.
- **Unit**: t (header and total label print t). Plausibility (R-T560-2): implied 74.71 .. 199.99 kg per m3 of his own
  family concrete, all far below the steel density: no kg/t mix-up.
- **Waste / laps inside?** Not printed: UNKNOWN (never assumed either way).
- **Basis class**: TYPED_LUMP (R-T560-1). Observation only, not adopted as his method: a round rate of 200 kg/m3
  reproduces his walls + columns value and 150 kg/m3 his beams value after rounding to 2 dp; for the other five no rate
  on a 5 kg/m3 grid does (intervals: footings 74.65 .. 74.78, ground 129.78 .. 129.91, slabs 90.19 .. 90.36, stairs +
  dome 178.40 .. 178.86, pool 121.07 .. 121.88 kg/m3).

So every comparison below is **RULE_DIFF** (typed lump vs counted bars): no agreement, no percentage.

## 3. Scope groups (R-T560-4)

His footings family holds pads, raft, the four FN pads, the three strap beams and a perimeter ground beam; his ground
family holds the ground slab, the ground beams and the fence ground beam. The engine splits the same bars into footings
(FRP:FTG), ground system (HL:GROUND_SYSTEM_STEEL: ground beams, straps SB1 - SB3, bars through columns, bands) and the
ground-slab mesh. The two splits cross, so they are compared as ONE substructure group; his lump is never split by an
invented proportion. Necks are in his walls + columns family and in engine P-S:NECK: same group as the columns.

## 4. Group table (t; candidate parts kept apart, R-T560-3)

| Group | His (t) | Engine VALUED | Engine HELD range | HELD blank lines | his - VALUED | Residual after the bounded held part | Class |
|---|---|---|---|---|---|---|---|
| G1 substructure (footings 5.80 + ground beams / slab 9.75) | 15.550000 | 2.317147 | 4.039645 .. 5.105957 | 196 | 13.232853 | 8.126896 .. 9.193208 | RULE_DIFF |
| G2 necks, columns, lift walls | 7.950000 | 1.887128 | 1.280992 .. 2.119349 | 238 | 6.062872 | 3.943523 .. 4.781880 | RULE_DIFF |
| G3 beams (incl. lift tie beam) | 9.890000 | 5.171031 | 4.247223 .. 6.120242 | 128 | 4.718969 | -1.401273 .. +0.471746 | RULE_DIFF |
| G4 slabs | 5.400000 | none | 3.671229 .. 4.857659 | 199 | 5.400000 | 0.542341 .. 1.728771 | RULE_DIFF |
| G5 stairs + dome | 3.900000 | none | 1.039160 .. 1.443671 | 17 | 3.900000 | 2.456329 .. 2.860840 | RULE_DIFF |
| G6 pool | 1.500000 | none | none | 20 | 1.500000 | 1.500000 (nothing bounded) | RULE_DIFF |
| G7 tank | NO_ROW | none | none | 1 | - | - | NO_ROW |
| **Total** | **44.190000** | **9.375306** | **14.278249 .. 19.646878** | **799** | **34.814694** | **15.167816 .. 20.536445** | |

Closures (asserted in the build and the tests): his groups re-add to his typed total 44.19 exactly; the engine groups
re-add to the candidate totals exactly in every part (valued 9,375.305760 kg on 374 lines; range 14,278.248488 ..
19,646.877938 kg on 894 lines; 799 blank; 577 EXCLUDED superseded rows carrying nothing; 2,644 lines). No two
alternative ledgers are added: the candidate already holds one row per (element, bar group); S3 / S3.1 / T-280 / T-138 /
T-265 / T-273 / route G are not re-read here (T-299 reconciled them; route G 16.39 t is not a term of this table).

## 5. Signed causes per group (R-T560-5)

The residual is carried jointly by (a) HELD-blank bar groups, (b) scope in one list only, (c) his method (basis not
printed) and (d) laps / waste (not printed by him; engine net). It is a named residual, not split further: no evidence
supports any proportion between (a) - (d).

- **G1 (8.13 .. 9.19 t open).** (a) footings 65 of 85 FRP:FTG lines blank (BOXED 20, bottom long 20 + short 20 whose bar
  read is held, top end legs 4, one ALL; 20 top / bottom lines bounded), ground-system 128 GSO + 3 strap lines blank (stirrup masses: Q-71, no first-link
  offset printed for ground beams, S9; side bars 2T12; bar ends note 9 40d .. 70d; longitudinal section candidates);
  bounded part already includes straps SB1 - SB3 0.491709 .. 0.975554 t. Engine VALUED basis note: 1.064240 t of it is
  the ground-slab mesh (24 panels: route G's 23 CONVENTION_ONLY panels 1.057203 t + 1 panel 0.007037 t added in the
  candidate), panel area x printed bars per metre, no laps; the rest is face-to-face counted bars (T-265 / T-138).
- **G2 (3.94 .. 4.78 t open).** (a) 28 neck positions x MAIN / TIES = 56 lines blank (P-S:NECK), 28 column main-bar
  lines blank, 59 links-in-the-joint, 46 bar ends at the stopping roof, 44 section transitions; (b) **lift pit walls**:
  the candidate carries their concrete (STR.CONC.LIFT LIFT_PIT:WALLS, HELD) and **no STR.REBAR line**; his family
  includes them.
- **G3 (-1.40 .. +0.47 t).** The only group whose bounded range contains his figure. NOT agreement: 128 lines stay
  blank (side bars 54 lines, ends over end columns 32, planted-column extra 2, top / bottom held marks, the lift tie
  beam), so the engine can only rise. The valued figure is face to face (T-149 basis): e.g. BM-GF-039 R043 bottom
  5 ø18 x 1.15 m x 18^2/162 = 11.500 kg valued, its note-9 ends 10 x 2.0 x 0.72 .. 1.26 m = 14.4 .. 25.2 kg held beside:
  on short beams the ends outweigh the span bars.
- **G4 (0.54 .. 1.73 t open).** No valued slab line: bottom mesh X / Y 2.922577 .. 3.088002 t and the slab bar ends
  (owner 2026-10-29 decision B) 0.701958 .. 1.629410 t are held ranges; development anchorage 90 lines and 91 top bars
  over supports blank, 13 ALL_BARS, 3 temperature-bar lines.
- **G5 (2.46 .. 2.86 t open).** ST-01 / ST-02 bounded; ST-01b and ST-03 all families blank; top bars at head / foot
  blank; (b) **dome**: the candidate carries dome shell and ring concrete (DOME-A shell 2.540681 m3 valued, rings) and
  **no STR.REBAR line with a dome element id** (whether a ring's bars sit under a beam mark is not
  checked here); his family is stairs + dome.
- **G6 (1.50 t open).** Every pool bar group (20 lines) blank: nothing bounded.
- **G7.** Tank rebar: engine line HELD blank; his workbook has no tank family: NO_ROW, never 0.

## 6. Who is right (verdict proposals)

- Every group total: **RULE_DIFF -> quantity UNRESOLVED.** A typed lump with no bar row is not evidence for any
  bar quantity; the engine side is incomplete (799 blank groups), not shown wrong. No ENGINE_RIGHT / FREELANCER_RIGHT
  on a total.
- Lift pit wall rebar and dome (shell + ring) rebar: **ENGINE_OMISSION of a line** (the candidate carries the RC element
  and no reinforcement line; his scope has it). Proposal for lane I: add HELD-blank STR.REBAR lines tied to the
  concrete lines (never 0); the bar detail on the structural sheets is not read in this run.
- Tank: scope in the engine list only; his NO_ROW: **UNRESOLVED (NOT_COMPARABLE)**.
- No ENGINE_WRONG found on a valued line (hand check R043 above reproduces 11.5 kg). No owner question: ERS s.2.7 not met
  (no contradiction, nothing safety-critical decided by an estimator; the blanks are designer items S9, S19 - S22, D-38,
  Q-71 already on the lists).

## 7. Rules, tests, lessons row (proposed)

R-T560-1 benchmark basis (COUNTED / RATIO / TYPED_LUMP; only counted vs counted is like-for-like; a reproducing rate
is an interval observation, never his method), R-T560-2 units (kg inside, t once; relabelled unit and > 7,850 kg/m3
refused), R-T560-3 engine parts apart (valued / range / blank / excluded, exact closure, absent = none), R-T560-4
smallest common scope group, R-T560-5 signed causes with a named residual. `tests/t560_rebar_reconcile` (23): hand villa
K560 (pad 2.00 x 2.00 T16 @ 200, cover 0.075: N = 1 + floor(1.85 / 0.20) = 10 each way, 2 x 10 x 1.85 x 1.578 =
58.386 kg; 2.40 x 1.60 rotation 65.0136 kg both ways; d^2/162 alternative 58.469 kg named and never mixed), adverse
(missing spacing HELD, mm, kg relabelled as t, 5,800 'kg as t' above the steel density, lump called agreement, held
with a value, half range, excluded with a value, family in two groups / none, NO_ROW), development villa (rebuild equals
the committed output, closures, one hand-checked line), private re-read (no bar row; typed constants) when present.

Lessons row (ERS s.7): | 2026-11-06 | reinforcement had no engine-vs-freelancer table; his 44.19 t looked comparable with
route G 16.39 t or the candidate 9.38 t | his tonnage is seven typed family constants with no bar row, while the engine
holds most bar groups as ranges or blanks | classify the benchmark basis first (COUNTED / RATIO / TYPED_LUMP), compare
only on the smallest common scope group, keep valued / held range / held blank apart and report the residual as named
causes, never a % (every villa; T-560, R-T560-1 .. 5) | tests/t560_rebar_reconcile | PROPOSED |

## 8. Checker re-measure list and what is missing

- Re-run `test_private_workbook_has_no_bar_rows` with the workbook at `.work/private/concrete_rebar.xlsx`.
- Confirm the G1 grouping from his footings and ground sheets (perimeter / fence ground beams on both of his sheets).
- Missing (not done here): bar detail of the lift pit walls and domes; the 799 blank groups (each its designer item);
  procurement tonnage B11-04 (T-382); waste / laps on his side are not printed and cannot be recovered.
