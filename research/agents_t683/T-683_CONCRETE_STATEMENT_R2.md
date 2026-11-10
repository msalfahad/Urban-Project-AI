# T-683 Concrete reconciliation statement round 2 (V3.0.66) + the three T-679 findings

Worker 1, 2026-11-10, branch `agents/task-T-683`. Research only: no engine module, candidate line, rule or knowledge
version file, key map or released default changed; nothing released; no new measurement of any element; the reference
is never a quantity and agreement is never proof. Development villa, not an accuracy claim. Rules R-T679-1 1.0.0
(unchanged) + R-T683-1 / -2 / -3 1.0.0 (`t683_rules.py`). Full tables: `out/T683_STATEMENT.md` / `.json`.

## 0. Sources and run

- Candidate V3.0.66 (T-677, MERGED): `research/agents_t677/out/LINE_INDEX_V3_0_66.json` (lines c411617d); master
  `rules/coverage/BOQ_FAMILY_MASTER_1.67.0.json` (census built on the same index sha, asserted family by family, 14).
- Held causes: T-669 (V3.0.63) < T-673 (V3.0.64) < T-678 (V3.0.65) via `t679_alsenan.causes`, then R-T683-1 against the
  merged integration packages T-668 (base V3.0.63), T-671 (V3.0.64), T-677 (V3.0.65): `summary_t6xx.json` rows.
- Reference: key map T001B + normalised cover totals (committed); causes quoted from scorecard V12 (T-635).
- OWN READ (this run) of Drive "Alsenan chalet project", the concrete + rebar workbook (private copy via
  `agent_env.sh decode`; numbers only committed): `t683_reference_arith.py --workbook .work/private/concrete_rebar.xlsx`
  -> `out/T683_REFERENCE_ARITH.json`. Then `t683_alsenan.py --write` (`--check` rebuilds and compares).

## 1. Engine side on V3.0.66 (m3; released, bounded and blank never summed together)

STR.CONC 597 lines: **released 317 = 291.476251**; HELD bounded 101 = **42.014281 .. 66.193191**; HELD blank 89
(DESIGNER ITEM 64, OPEN BOUND 14, MEASURABLE NOW 11); excluded 90. Engine range 333.490532 .. OPEN.
Floors beside (blank lines, never in the range): ST-03 >= 0.355017, L-6bf14711 >= 0.1125, pool blinding >= 0.915529.

Before (V3.0.65, T-679) -> after, reconciled to the T-677 changes alone:
- released 291.473824 -> 291.476251 = +0.002427 (ground-slab panels L-69527cb9 -0.009, L-8b681fda +0.010559,
  L-f192ff5f +0.000868: Checker re-measured, T-674).
- bounded 84 -> 101 lines: low 41.084313 + 0.925 (16 lintels) + 0 (new pier line) + 0.004968 (BAND0038 low) =
  42.014281; high 64.696779 + 1.493412 + 0.003 = 66.193191. Exact.
- blank 105 -> 89 = -16 lintels (16 bounded now; ST-03 stays blank with its floor beside).

## 2. R-T683-1: stale census classes (new finding F-T683-1)

'MEASURABLE NOW' means "drawn value in merged research, not wired". 19 HELD lines still carried it after a merged package
had wired them: 16 lintels + ST-03 (T-673 class, wired by T-677), the boundary band (T-669 class, wired by T-668 in
V3.0.64; T-679 flagged it), and the new W19 / W20 pier line (no census row). Each is restated with the residual cause
that keeps it HELD after the wiring, quoted from the merged text: lintels and pier = DESIGNER ITEM (cast length
between the 0.40 minimum bearing and the drawn jamb ceilings, end connection at a column / cross wall: T-516 RFI; heads
drawn not printed, N09); ST-03 = DESIGNER ITEM (waist not drawn); band = DESIGNER ITEM (Q-28 section RFI, founding
level not printed). Counts after: bounded by cause DESIGNER 68 / OPEN BOUND 33 / MEASURABLE NOW 0; the 11 MEASURABLE NOW
left are blank and all wait on T-682 (9 T-678 lintels, PC-2F, annex C3). The rule also checks that every wired HELD
line of the index equals its package after-state (BOUND = same bound to the digit; LOWER_ONLY = still blank): all pass,
so V3.0.66 is the candidate those packages built.

## 3. The three T-679 findings

**F-T679-1 closed** (census rows given): L-893c3db1 pool blinding: HELD blank, floor >= 0.915529 beside; DESIGNER ITEM
C4 (projection beyond the wrap not dimensioned) + C6 (F8 / F4 / FN founding vs pool formation -1.50 not printed);
already wired (T-668), closes only on the designer answer, then lane S re-measure + lane I. L-bef35462 BAND0030.2
companion 0 .. 0.025: DESIGNER ITEM FR-T642-2 (no mark on the strip: B4 0.50 vs B7 0.75); already wired (T-671). No
owner question (designer items, ERS 2.7).

**F-T679-2 closed by a scope bridge** (R-T683-2). Own read: the column cover 39.7515 = his lift-wall sub-total 2.4
(ring 8 x 0.20 x 1.50) + necks 8.805 + columns 17.4375 + 7.728 + 3.381 (= 28.5465), each re-adding exactly.

| Component | Ref | Engine scope | Engine | Ref - released | Status |
|---|---|---|---|---|---|
| lift pit walls | 2.4 | STR.CONC.LIFT [LIFT_PIT:WALLS] | 1 blank (D-43) | 2.4 | HELD inside |
| necks | 8.805 | STR.CONC.NECK | 32 bounded 8.7724 .. 11.3460 + 4 blank | 8.805 | HELD inside |
| columns | 28.5465 | STR.CONC.COLUMN | 19.7765 released + 20 bounded 9.6702 .. 12.4140 + 9 blank | 8.7700 | HELD inside |

Lift 2.4 = 0.75 SCOPE_DOUBLE (his ring is gross 1.600 m2; the four column pieces 0.500 m2 inside it are also in his neck
rows; the engine NECK lines own them once: ENGINE_RIGHT, Checker re-measured T-628) + 1.65 HELD (net ring 1.100 x his
1.50; pit depth 'as per manufacturer', D-43). LIFT_TIE_BEAM:GF (same item code) has no row of his on any sheet:
NOT_COMPARABLE, never folded in. PROPOSED key-map change (not applied): CONC.COLUMN answers NECK + COLUMN + STR.CONC.LIFT
element LIFT_PIT:WALLS only; needs element-level key scope in the keymap / scoreboard tools; no numeric effect today.

**F-T679-3 closed: REFERENCE ARITHMETIC** (R-T683-3). Own read of the beam sheet formulas: his 1F carry-forward cell
sums the 1F rows from the first 1F row, but his 1F sub-total (the one the cover total adds) starts one row later; the
first 1F row (0.20 x 0.40 x 1.60 = 0.128 m3) is reached by no path to the cover. Cover 65.965875 = his rows
66.093875 - 0.128000 exactly. Reproduces T-545's row sum from the formulas, not from T-545's output. The same audit of
all eight keyed concrete cover chains finds no other omitted or doubled row. Engine released 66.920678: cover -
released -0.954803, rows - released -0.826803; % stays suppressed (26 HELD beam lines). No engine verdict, no quantity
moved; who is right on the arithmetic: the reference's own rows (FREELANCER arithmetic slip, -0.128).

## 3a. Next related item: CONC.SLAB localised by storey (R-T683-2)

The slab key is the only one with every line released and VERIFIED (62 / 62); its -0.462755 m3 (-0.77 %) had no
merged cause. Own read of his slab sheet: three storey sub-totals, each ONE gross row (GF 207 m2 x 0.16 = 33.12; 1F
120 m2 x 0.16 = 19.2; roof 31.84 x 0.16 + 13.35 x 0.18 = 7.4974). Against the engine lines of the same storey tag:
GF +0.050478 (+0.15 %), **1F -0.556333 (-2.90 %)**, 2F +0.043100 (+0.57 %); the three re-add to -0.462755 exactly.
His 1F row computes a 0.081 m3 deduction (0.40 x 0.15 x 1.35) and multiplies it by a count of 0 (not applied). Status
UNRESOLVED, residual named by storey: his areas carry no panel split, so no class is given; next step a 1F panel-area
bridge (22 engine panels vs his 120 m2) on the candidate lines file (needs the chain run on the private drawings).

## 4. Rules, tests, lessons

R-T683-1 / -2 / -3 in `t683_rules.py`. Tests `tests/t683_concrete_statement` (23): villa V683 by hand (stale class
refused, added line, restating an unwired line refused, restating to MEASURABLE NOW refused, index != package refused,
LOWER_ONLY turned into a bound refused, re-census after wiring not stale, package order invariance, bridge with a HELD
line where ref = released is not agreement, components must re-add, NO_ENGINE_LINE, a line in two components refused,
omitted first row after a page break, carry chain reached once, doubled row, unexplained residual refused) +
development villa (outputs reproduce, totals = index to the last digit and = master census, no wired line left
MEASURABLE NOW, findings closed).

Tooling note: the Drive connector saved the workbook as raw bytes (not base64 / JSON); `agent_env.sh decode` assumes
base64 and wrote a 9,666-byte corrupt file without error. Work-around used: base64-encode the raw download in the
scratchpad, then decode. Proposed: decode should accept a file that already starts with the zip / PDF magic.

Lessons rows (ERS s.7, PROPOSED):
| 2026-11-10 | a census class 'MEASURABLE NOW' goes stale the moment a package wires the line | statement / census |
restate the residual cause on the candidate read; refuse a wired line still classed 'wire it' | R-T683-1, F-T683-1 |
| 2026-11-10 | a reference cover total can drop a row through a sub-total range after a page break | reference audit |
expand the cover cell's chain to its rows before quoting a reference difference | R-T683-3, F-T679-3 |
