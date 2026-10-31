# T-394 Column height and section reconciliation: CL-GF, CL-1F, CL-LIFT of T-385 r2 traced to their causes

Worker 1 (lane S), 2026-10-31 13:20 .. UTC, run unknown, branch `agents/task-T-394`. Research only: no engine, candidate,
released line, rule or method version changed; nothing released. Development villa, not an accuracy claim. ERS s.2.1 -
2.6, s.3, s.4, s.7 applied.

## 0. Sources and runs

Own Drive copies this run (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf'
(`9f9d1179`) and the concrete + rebar workbook (sheet 'walls + columns', quantities only; its 368 cells of that sheet
equal the committed benchmark copy cell for cell). On the DXF: the merged T-248 extractor re-run (T-217 member x storey
inventory REPRODUCED, 59 / 59 members bound, 1B1B identity unchanged) and an own read of the 50 GF / 1F column outlines by
handle (`t394_extract.py`: 50 / 50 found, all closed rectangles on S-COL.BON, sizes equal to the T-248 / T-256 drawn
sizes; output private, it is drawing content).

Candidate lines: the 72 STR.CONC.COLUMN lines of the committed V3.0.21 file (`research/agents_t332`), **asserted equal**
(line ids, element ids, valued m3, states) to the V3.0.29 binding of the reproduced candidate of record
(`research/agents_t387/BINDING_T387.csv`, 6b5dc44f); the Lead states V3.0.31 carries the V3.0.29 structural lines
byte-identical (V3.0.30 / V3.0.31 not re-run here). Families reproduce T-385 exactly: GF 30 lines, 25 valued 17.9675 m3,
5 held; 1F 23 lines, 20 valued 10.248 m3, 3 not applicable.

```
python3 -I research/agents_t394/t394_extract.py <private>/ST7757_dxf.dxf --write          # -> .work/private/t394
python3 -I research/agents_t394/t394_alsenan.py --freelancer <private>/concrete_rebar.xlsx --write
```

Outputs: `.work/private/t394/RECON_T394.csv` (per line: member handle, own drawn area, schedule, datums, engine m3,
owner split, his row), `MARKS_T394.csv` (per storey x mark, the four terms), and the tracked engine-side
`summary_t394.json` (engine figures, cause terms in m3; no row, count or dimension of the workbook). Rules
`t394_rules.py` R-T394-1 .. 6; tests `tests/t394_column_recon` (21).

## 1. The physical element (ERS s.2.1)

A storey column is the solid inside its drawn outline between two structural datums: base = the ground-beam / slab top
it stands on (GF +0.95 main house, +0.25 annex ground slab; 1F +5.45; a planted column on its carrying beam top +5.45),
top = the slab top it carries (GF roof +5.45, 1F roof +9.65) - T-214 datums: the ST DXF prints the finished +1.00 (LEVEL
texts 1BE / 1C0 / 1C2 / 1CD) and +9.70 (3F4 / 3F6), less the drawn 0.05 build-up; +5.50 from the architectural set.
**Height basis (R-T394-1):** the column runs to the slab TOP only because nothing else bills the volume above the soffit:
every slab face stops at the drawn column faces (T-241 partition: 0.0000 m2 of slab inside any of the 59 outlines) and
every beam run stops at the column faces (T-229 / T-241: the 7 released double joints deducted from the beams, column
owns). Under a slab or beam billed through, the column would stop at that soffit; the rule refuses the slab-top height
there (DOUBLE). On GF / 1F no beam is billed through a column (the one case, PC-2F under B7, is 2F, held).

Owner manual method beside it (URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 + URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1):
column = A x (interval - D_ctrl), joint = A x (D_ctrl - t), head = A x t: the same solid in three lines, "never a global
depth". D_ctrl per member from the merged T-119 ledger.

## 2. Line table (acceptance a; per line in the private RECON_T394.csv)

Binding: every GF / 1F line bound to ONE drawn member by mark + storey + position (frame offset 75968 / 14448 mm between
the candidate's SH12 ids and route G's, +-3 mm), the planted HL records by their label: **53 lines -> 50 drawn outlines +
the 1F NOT_PRESENT position 10E4 + 2 route G planted lines superseded by the HL records; one to one** (this closes
T-387 F-T387-2 for the column family: the census bound columns by storey count only).

| Storey | Group | Lines | Engine m3 | Height (datums) | Section | Status |
|---|---|---|---|---|---|---|
| GF | drawn section = schedule | 19 | 14.0625 | 4.50 (+0.95 -> +5.45) | DRAWING-CONFIRMED | PROVISIONAL lines, closable component |
| GF | CB5-line C5 35F, C3 365 | 2 | 1.4300 | 5.20 (+0.25 -> +5.45, T-287 G1) | DRAWING-CONFIRMED | SOURCE_DERIVED |
| GF | section CONFLICT 344, 347, 359, 380 | 4 | 2.4750 | 4.50 | schedule (upper) end; drawn 2.0700 | CONFLICT carried as one figure |
| GF | annex 34A, 34D, 356 (C), 350, 353 (C3) | 5 | HELD blank | annex roof unprinted (Q-54 B, D-39) | 3 also CONFLICT | HELD |
| 1F | drawn section = schedule (incl. PC-1F-A / -B 1.008) | 9 | 4.2840 | 4.20 (+5.45 -> +9.65) | DRAWING-CONFIRMED | PROVISIONAL / SOURCE_DERIVED |
| 1F | section CONFLICT 667, 673, 676, 679, 685, 688, 68E, 691, 694, 697, 69A | 11 | 5.9640 | 4.20 | schedule (lower) end; drawn 7.6440 | CONFLICT carried as one figure |
| 1F | superseded route G planted lines; C3 NOT_PRESENT at 10E4 (D-65) | 3 | - | - | - | NOT_APPLICABLE |

Owner manual method on the same valued members (m3): GF column 14.3737 on 24 members with D_ctrl settled + 0.9000 on 1
member with D_ctrl open (GFRS 368 C7), joint + head 2.6938 -> 17.9675; 1F column 6.4200 on 15 settled + 2.6880 on 5 open
(664, 685, 68B, 68E, 69D), joint + head 1.1400 -> 10.2480. The solid is the same; only the line split differs.

## 3. Cause split (acceptance b; signs engine - freelancer, m3; R-T394-2 / -3 / -4)

Per storey and mark: COUNT = (drawn - his) x his section x his height; HELD = - held members x his section x his height;
SECTION = sum (engine A - his A) x his height (CONFLICT member -> UNRESOLVED, drawn = schedule -> DIMENSION); HEIGHT =
sum engine A x (engine h - his h), split into JOINT_HEAD = A x D_ctrl, BASE = A x (+0.95 - base) and GLOBAL_DEPTH = the
rest; with D_ctrl open the HEIGHT term stays one traced term, split OPEN. The four terms re-add to the residual exactly
(bookkeeping remainder 0.000000 on every mark).

**CL-GF residual +0.530 m3**

| Cause | m3 | Verdict proposal |
|---|---|---|
| count by mark (drawn outlines C1 1, C2 4, C9 2, C11 2, C3 6 against his counts) | **-0.5625** | ENGINE_RIGHT (COUNT: labelled outlines, T-217 inventory reproduced from Drive this run, 30 own outlines) |
| 5 annex columns held (his section x his height) | **-2.0625** | HELD (Q-54 B / D-39; never 0) |
| joint + head A x D_ctrl: under C1 the column line owns it to the slab top; his columns stop 0.75 below it | **+2.69375** | RULE_DIFFERENCE (line ownership; the counterpart sits in his beam rows only where they run through, T-241: for T-395) |
| his uniform 0.75 depth vs the member's own controlling depth (0.40 / 0.50 / 0.75 / 0.85) | **+0.11875** | ENGINE_RIGHT (owner method: 'never a global depth'; +0.21375 where D_ctrl 0.40 / 0.50, -0.095 on the four 0.85 members C10 371, C11 35C / 37D, C8 36E) |
| base +0.25 of the two CB5-line columns vs the +0.95 storey his one height fits | **+0.1925** | ENGINE_RIGHT (T-287 G1, merged) |
| height on GFRS 368 C7 (D_ctrl open in the owner split) | +0.1500 | traced (0.75 x 0.20 m2), split OPEN |
| section | 0.0000 | AGREE (his sections = the schedule band on every GF mark) |

Traced (named) +2.4425; split open +0.1500; HELD -2.0625; UNRESOLVED 0.0000; unexplained 0.0000.

**CL-1F residual +2.520 m3**

| Cause | m3 | Verdict proposal |
|---|---|---|
| count by mark (C6 1 drawn, no row of his: +0.504 at the engine's figure; C3 2, C7 1, C8 2, C9 2 against his counts) | **+0.9180** | ENGINE_RIGHT (COUNT, 20 own outlines; C3 NOT_PRESENT at 10E4, T-256) |
| section C9 (667, 679): engine 1ST 20 x 90 vs his 0.20 x 1.00; both members are printed-vs-drawn CONFLICTs | **-0.1380** | UNRESOLVED (designer D-63 / column band item, T-256) |
| joint + head A x D_ctrl | **+1.0800** | RULE_DIFFERENCE (as GF; for T-395) |
| his uniform 0.75 vs the member's D_ctrl (0.40 / 0.50) | **+0.1800** | ENGINE_RIGHT (owner method) |
| height on 5 members with D_ctrl open | +0.4800 | traced, split OPEN |

Traced (named) +2.1780; split open +0.4800; HELD 0.0000; UNRESOLVED -0.1380; unexplained 0.0000.

**CL-LIFT residual -2.400 m3** (no candidate line; R-T394-6): his plan 8.00 x 0.20 = 1.600 m2 = the drawn GROSS ring
2.20^2 - 1.80^2 (S-BW 10EB / 10EA, T-204 / T-322), i.e. through the four lift column pieces 0.50 m2:

| Cause | m3 | Verdict proposal |
|---|---|---|
| the four lift column pieces in his ring (0.50 m2 x his height), owned by the lift neck lines (R-CONC-OWN-1) and in his neck rows as well (his C1 / C2 / C9 neck counts equal the drawn ones, T-248) | **-0.7500** | ENGINE_RIGHT (SCOPE: a double on his side) |
| net ring 1.100 m2 x his height: the pit depth is 'as per lift manufacturer' (p.14, D-43) | **-1.6500** | HELD; the candidate has NO line for it (see P2) |

Families together (+0.650 m3): traced +3.8705, split open +0.6300, HELD -3.7125, UNRESOLVED -0.1380.
(T-385 r2 carried the three as UNRESOLVED -> unexplained.)

**Engine-side uncertainty that is not a residual term**: the 15 CONFLICT members are valued at the schedule end; the
drawn reading moves GF by -0.405 and 1F by +1.680 m3 (GF 2.070 .. 2.475, 1F 5.964 .. 7.644; T-248 / T-256 unchanged).

## 4. Intersections, each counted once (acceptance c; against the T-387 census)

| Pair | Evidence | Result |
|---|---|---|
| column / slab (GF roof SH06, 1F roof SH04) | T-241 partition (T-248 summary: slab inside 59 SOLID outlines 0.0000 m2); T-387 SH04 PASS_HELD, SH06 named items are beam / beam and beam / slab only | counted once, column line (CONCRETE) owns its footprint to the slab top |
| column / beam | T-229 'column owns' adjustments and the 7 double joints deducted from the beams (T-241); T-387: 0 column / beam DOUBLE or GAP on SH04 / SH06 | counted once, column line |
| beam billed through a column | none on GF / 1F (2F PC-2F under B7 only, held) | R-T394-1 does not stop any GF / 1F column at a soffit |
| neck / GF column; GF / 1F column | T-387 R-T387-4 OK; T-248 stack check 0 differences | counted once |
| column / column outlines | 50 own outlines, one line each (binding above) | no shared member |
| lift ring / lift columns | R-T394-6: ring net 1.100 m2 is the wall's, 0.50 m2 the columns' | counted once on the engine side (and the ring line is missing) |

## 5. Methods side by side (ERS s.2.2)

| Method | GF columns (valued members) | 1F columns | Lift pit walls |
|---|---|---|---|
| Owner manual method | column 14.3737 + 0.900 open; joint + head 2.6938 | 6.420 + 2.688 open; 1.140 | 1.100 m2 x pit depth (HELD) |
| Drawing-derived, C1 (this task = candidate on the valued members) | 17.9675 (CONFLICT part 2.070 .. 2.475) + 5 HELD | 10.248 (CONFLICT part 5.964 .. 7.644) | 1.100 m2 x h, HELD |
| Candidate V3.0.29 / V3.0.31 | 17.9675, 5 HELD | 10.248 | no line |
| Freelancer (private) | one storey height less 0.75 on every column | the same | gross ring x a height no sheet prints |

## 6. Proposals (no line edited here)

- **P1 (lane I / Checker downgrade candidate)**: the 15 CONFLICT column lines are single PROVISIONAL figures at the
  schedule end (GF 4 lines 2.475, 1F 11 lines 5.964); R-COLUMN-EVIDENCE-1 (T-256, merged) and X6 carry a printed-vs-drawn
  section as a range, never the schedule end: BOUNDED GF 2.070 .. 2.475, 1F 5.964 .. 7.644 m3 until the designer answers
  (D-16, D-63, the column-band item).
- **P2 (lane I, completeness)**: the lift pit walls (ST p.14, net ring 1.100 m2, DRAWING-CONFIRMED plan) have no
  candidate line: add a HELD line 'CONC.LIFT_PIT_WALL 1.100 m2 x pit depth (D-43)', blank, never 0.
- **P3 (to T-395, beams)**: the joint + head term +3.774 m3 (GF 2.694, 1F 1.080) is concrete the candidate bills in the
  column line and the freelancer bills in his beam rows only where a beam runs through the support; T-395 should trace
  his beam-through volume at the columns so the two families close together (bound: at most 3.774 m3 of it can be there).
- **No owner question** (ERS s.2.7 not met: D_ctrl open members are beam-depth holds, the section conflicts and the pit
  depth are designer items already on the list).

## 7. Rules, lessons row (proposed)

R-T394-1 .. 6 (`t394_rules.py`). Lessons row (ERS s.7): | 2026-10-31 | CL-GF +0.530, CL-1F +2.520 and CL-LIFT -2.400 m3
stood UNRESOLVED (T-385 r2) as 'height basis + held + marks' | three causes of different kinds (who owns the joint and
head, a global soffit depth, a mark count) and a wall ring measured through columns sat inside one storey total | a
column residual is split per storey and mark into COUNT / HELD / SECTION / HEIGHT exactly, the height part into joint +
head (A x D_ctrl: ownership), base datum and the rest (a uniform depth against the member's own D_ctrl), with D_ctrl
open the split stays OPEN, a CONFLICT section term is UNRESOLVED; the column runs to the slab top only when slab and
beams are net of its outline; a ring through columns owns its net band only (every villa; provenance T-394) |
tests/t394_column_recon (deeper beam split, count, held named, split open, base datum, conflict unresolved, ring double;
adverse: slab-top height under a slab billing the footprint refused, through-beam height refused, held as 0 refused,
ratio closure refused, mm refused) | PROPOSED |

## 8. Checker re-measure list

- Own outlines (ST DXF): GFRS 35C C11 1.10 x 0.25 (0.275 x 4.50 = 1.2375), GFRS 380 C8 0.80 x 0.25 against GR 25 x 90,
  FFRS 679 C9 0.25 x 1.00 against 1ST 20 x 90, FFRS 66A P.C 0.70 x 0.20 (0.14 x 4.20 = 0.588).
- One joint + head: GF C2 GFRS 32C, D_ctrl 0.40 (T-119 COL-GF-04, B3 / B2 D 0.40): 0.10 x 0.40 = 0.040 m3 joint + head;
  his column there stops 0.35 m lower than the owner method's (0.10 x 0.35 = 0.035 m3 GLOBAL_DEPTH).
- Lift ring: 10EB 2.20 x 2.20, 10EA 1.80 x 1.80; four column pieces 0.10 + 0.10 + 0.10 + 0.20 m2 (T-322).
- Re-run the two commands in section 0; `RECON_T394.csv` / `MARKS_T394.csv` print his rows beside the engine.

## 9. Not done / uncertain

- V3.0.30 / V3.0.31 not reproduced; the column lines are bound through the committed V3.0.21 file proven equal to the
  reproduced V3.0.29 binding.
- The freelancer's beam rows were not opened: the joint + head term's counterpart on his side is P3's (T-395).
- His C6 1F: no row; the count term carries the engine's whole 0.504 m3 for it (no height split for that member).
- 'BASE' compares with the +0.95 storey datum his one GF height fits (his row prints a height, not its datums).
