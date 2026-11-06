# T-545 B10-07 beam concrete: V3.0.58 against the freelancer's beam sheet, by component

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPndh75mDJ4CqaZuTs6y, branch
`agents/task-T-545`. Research only: no engine, candidate, released line, rule file or method version changed; nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Builds on T-395 (merged):
its per-mark split R-T395-1 .. 5 is reused as a library, re-run on the V3.0.58 lines.

## 0. Sources and run

- Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED). Its beam lines are those of
  `research/agents_t507/out/LINE_INDEX_V3_0_57.json` (V3.0.58 changes the roof WP lines only, R-T507-1 (e)): 191
  STR.CONC.BEAM lines = 110 RELEASED **66.321054 m3**, 27 HELD (22 bounded **8.372829 .. 13.779510 m3**, 5 UNKNOWN), 54
  EXCLUDED. Joined line by line to the committed V3.0.21 file (dimensions, floor; T-395's input): ids, element ids and
  statuses equal; values equal to 6 dp except the four T-397 VERIFIED corrections (+0.003174 m3, s.3).
- Marks / runs / supports: T-252 ledger r2, T-110 member register, T-229 support input (as T-395); route G bands from
  `research/agents_t110/scripts/bands.py` (fit <= 0.6 mm).
- Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook, beam sheet, read this run with openpyxl
  (formulas and values, R-T541-1). Every row is b x D x L x n (his column headers 'length' / 'height' carry the depth
  and the length; the depth equals the schedule depth on every common mark). Decoded into `.work/private` only; his
  rows stay in `.work/private/t545`.

```
python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <private>/t545/bands.json
python3 -I research/agents_t545/t545_alsenan.py --freelancer <private>/concrete_rebar.xlsx --bands <private>/t545/bands.json --write
```

Tracked output `out/T545_BEAM_RECONCILE.json`: engine figures, component terms in m3 per storey and mark, his per-storey
sums; no row, length or count of his.

## 1. The physical element (ERS s.2.1)

A beam is its drawn plan between the faces of the members that own the crossings (columns to the slab top, R-CONC-OWN-1 /
T-394 R-T394-1; carrier beams), times the printed overall depth, with the slab NET of the beam plan (T-189 ownership,
R-T395-1). Stair beams B20 / B23 own their 0.20 x 0.20 upstand lines (T-189); the dome ring B4 0.20 x 0.50 is a beam that
stays in both dome scenarios (owner Q-44 A; Q-29 S0 / S1); RC lintels are their own family (STR.CONC.LINTEL, B9-02) and
the lift tie beam its own HELD line (STR.CONC.LIFT 'LIFT_TIE_BEAM:GF', D-43). Ground beams are B10 ground system
(STR.CONC.GROUND_BEAM), his 'ground beams' sheet: neither enters this residual (s.5).

## 2. Component table (R-T545-1; engine - his, m3; sums exact)

His rows sum to **66.093875 m3**; his printed total is 65.965875 (his 1F sub-total starts one row late: -0.128000,
BM-ARITH, ENGINE_RIGHT as T-385). Residual vs his rows **+0.227179 m3 (+0.34 %)**; vs his printed total +0.355179.

| Component | GF | 1F | 2F | Total | Verdict proposal | Evidence |
|---|---|---|---|---|---|---|
| COUNT: labelled drawn marks with no row of his (GF B27 4.1918, B28 0.2121, CA 0.1725; 1F B25 2.8500, B19 1.6236, B5 0.8325) | +4.576422 | +5.306035 | 0 | **+9.882457** | ENGINE_RIGHT | T-229 / T-241 merged, drawn and tagged |
| RUN_COUNT: drawn runs of a mark beyond his rows (GF B1; 1F B4, B6) | +0.210119 | +1.908946 | 0 | **+2.119065** | ENGINE_RIGHT | labelled runs; run binding by length (heuristic) |
| UPSTAND: stair beam upstands B20 / B23 0.20 x 0.20 x 3.00 | +0.120000 | +0.120000 | 0 | **+0.240000** | ENGINE_RIGHT | T-189, drawn; no row of his |
| DOME_RING: west ring B4 in bay (1F) | 0 | +0.755200 | 0 | **+0.755200** | ENGINE_RIGHT | Q-44 A (ring stays); T-398: his dome row is a 0.10 shell plate, ring and shell never meet |
| THROUGH_SUPPORT: his lengths run through the column / carrier footprint | -2.901714 | -1.593362 | -0.532760 | **-5.027836** | RULE_DIFFERENCE | R-T395-2 / -4, within the drawn support allowance per mark |
| HELD: engine blank, his rows at his section on the held runs | -5.430918 | -0.808000 | -1.137500 | **-7.376418** | HELD (never 0) | s.4 |
| SECTION | 0 | 0 | 0 | 0 | AGREE | his b x D = drawn on every common mark |
| UNTRACED (GF B7 -0.1205, B2 -0.0112, B11 +0.0041, B8 +0.0030; 1F CB12 -0.1610, B11 +0.0072, B6 +0.0003; 2F B2 -0.0872) | -0.124533 | -0.153516 | -0.087240 | **-0.365289** | UNRESOLVED | named per mark (s.6) |
| **Residual** | **-3.550624** | **+5.535303** | **-1.757500** | **+0.227179** | | |

Engine per storey GF 39.332251 / 1F 22.690303 / 2F 4.298500; his rows 42.882875 / 17.155000 / 6.056000.
The near-zero total residual is a cancellation, not an agreement: +12.997 m3 of drawn solids he omits against -5.028 of
length convention and -7.376 the engine holds.

## 3. Since T-395 (V3.0.29 -> V3.0.58)

Only four GF lines moved, all T-397 VERIFIED corrections: CB8 BAND0039 0.7163 -> 0.716937, CB1 BAND0041.2 1.337922 ->
1.33875, B8 BAND0003 0.526665 -> 0.528021, B7 BAND0006 0.254647 -> 0.255 (T-392 R-T392-1 ring-overlap gap restored; T-387
CB8 end DOUBLE / GAP): **+0.003174 m3**, landing in GF THROUGH_SUPPORT +0.001465 and GF UNTRACED +0.001709. No line
changed status; the beam family is otherwise byte-equal to the T-395 input.

## 4. Held lines beside his rows (R-T545-3)

| Group | Lines | Engine bound m3 | His share m3 | Class |
|---|---|---|---|---|
| Held runs that a row of his carries (GF B21, B29, CB2 x2, CB3, B24 ext.; 1F CB10 x2, B2 ext.; 2F B15, B1 x2, B8 ext.) | 13 | 5.915279 .. 8.396780 | 7.376418 | 12 INSIDE, 1 ABOVE |
| Held runs no row of his can be (GF BM-GF-058 x2, BAND0030.2; 1F BM-1F-030 (B6, left over by the run binding), -033 x2, -034, -035, -036) | 9 | 2.457550 .. 5.382730 | 0 | NO_ROW_OF_HIS (designer D-05 / D-27) |
| Unknown (2F BM-2F-019, 1F BM-1F-037 / -038, GF BM-GF-061: D-26 projection strips; 1F east dome ring) | 5 | none | 0 | UNBOUNDED |

His figure lies inside the engine's own held bound on 12 of 13 runs. The one ABOVE is GF B24 extension BM-GF-059:
his 0.5 x 0.75 x 1.501 = 0.562875 against the bound high 0.5625, which the ledger computes on 1.500 m while its drawn
length is 1.501 m: **F-T545-1** (0.000375 m3, 0.07 %; ledger-side bound print, proposal only, no line changed). The class
is information for the Checker, never a reason to release or move a held line. Full family exposure if every bounded
held line resolves: 66.321 + [8.373, 13.780] = [74.694, 80.101] m3 plus 5 unknown, against his 66.094: the omitted
drawn marks (s.2) are why the engine family ends above his, not the held runs (his share sits inside their bound).

## 5. Overlaps counted once (R-T545-2) and the neighbouring families

| Pair | Evidence | Result |
|---|---|---|
| beam / slab | his slab area per storey is NET of the beam plan (GF 206.684 / 1F 123.477 / 2F 44.885 m2 engine NET; beam plan 60.309 / 42.155 / 9.745); both sides take FULL depth | depth-basis term **0.000** on every storey; exposure had one side read DOWNSTAND 9.185 / 5.631 / 1.265 m3 |
| beam / column | T-229 DOUBLE joints deducted from the beam, column owns: CB7 col 350 -0.0598, B2 col 356 -0.0318, CB8 col 359 -0.0600, CB1 col 347 -0.0600 (sum -0.2116); each column handle once | owned once |
| beam pieces | 129 band pieces over 127 beam lines, every piece in one line | owned once |
| ring / slab, ring / shell | T-252 / T-392 (ring billed by the beam, no slab under it); T-398 (shell starts at the springing) | owned once |

Outside the residual (each its own family, no row of his on any sheet: no lintel, tie or ring label in the workbook):
STR.CONC.LINTEL 16 released 1.016 m3 + 44 HELD; LIFT_TIE_BEAM:GF HELD (concrete, rebar, formwork; D-43: required on GF,
section not printed); STR.CONC.GROUND_BEAM 32 released 23.760555 m3 + 29 HELD (his 'ground beams' sheet; not this task).
D-39 (roof datum) does not enter a beam volume: every beam depth is printed overall; no held beam line cites D-39.

## 6. Who is right, what is open

- ENGINE_RIGHT +12.997 m3: COUNT 9.882, RUN_COUNT 2.119, UPSTAND 0.240, DOME_RING 0.755; his 1F sub-total slip -0.128.
- RULE_DIFFERENCE -5.028 m3: length through supports (the support owns the footprint, R-T395-2). His columns stop below
  the beam (T-394: +2.694 GF / +1.080 1F in the column family) so the two families net -0.208 GF / -0.513 1F; the
  per-crossing pairing (T-395 P1) belongs with T-551 (columns vs freelancer), not done here.
- HELD -7.376 m3 (13 lines, his inside the bound on 12) + 9 bounded runs he has no row for + 5 unknown: designer items
  D-02 / D-03 / D-04 / D-05 / D-26 / D-27, already in the RFI package; ERS s.2.7 not met: **no owner question**.
- UNRESOLVED -0.365 m3 named per mark: GF B7 (one of his B7 rows has no location, T-252), 1F CB12 (his length 0.64 m
  beyond the drawn supports), 2F B2 (1.09 m beyond); +0.015 of 6-dp / sub-cm lengths on GF B11 / B8, 1F B11 / B6.
- Uncertain: RUN_COUNT binds his rows to runs by length; his two 1F B4 rows (0.20 x 0.50) are bound to the straight B4
  runs, the same section as the ring B4: the Checker should look at whether one is his ring reading (moves at most
  +0.331 between RUN_COUNT and DOME_RING; total unchanged).
- No ENGINE_WRONG found: no fix proposal, no quantity change.

## 7. Rules, tests, lessons row (proposed)

`t545_rules.py` R-T545-1 (component table, exact closure, HELD never closed as 0, no percentage), R-T545-2 (overlap once:
FULL + NET or DOWNSTAND + GROSS only; one owner per joint / piece; mm refused), R-T545-3 (held bound beside his row).
`tests/t545_beam_concrete_reconcile`: hand villa V545 (one beam 0.25 x 0.60, f2f 5.00 m, between two 0.40 x 0.25
columns under a 30 m2 slab 0.15: engine 0.750 + 0.700 + 4.2825 = through 0.870 + 0.580 + 4.2825 = 5.7325 m3; component
table -0.080 = +0.240 - 0.120 - 0.200), adverse (FULL + GROSS / DOWNSTAND + NET refused, joint billed twice refused,
held as 0, percentage, mm, missing, open sum, low > high refused, mirror / rotation invariant), development villa from
committed files (released / bound / since-T-395 delta recomputed, tables close per storey and total, held lines once
and never 0, no his row tracked) and a rebuild from the private workbook (runs only where present).

Lessons row (ERS s.7): | 2026-11-06 | B10-07 beam residual +0.227 m3 (0.34 %) on V3.0.58 read as agreement | it is
+12.997 drawn solids he omits, -5.028 length convention and -7.376 held, cancelling | a small family residual is split
into components before it is reported; a held run is compared with the engine's own bound, never closed by his figure
(every villa; provenance T-545, R-T545-1 .. 3) | tests/t545_beam_concrete_reconcile | PROPOSED |

## 8. Checker re-measure list

- Re-run s.0 (private workbook + bands); `MARKS_T545.csv` shows his rows beside the engine per mark.
- GF B24 extension BM-GF-059 drawn 1.501 m vs bound basis 1.500 (F-T545-1).
- 1F B4 rows vs the dome ring B4 (s.6); GF B27 4.1918 / 1F B25 2.8500 (largest COUNT marks, T-229 hand values).
