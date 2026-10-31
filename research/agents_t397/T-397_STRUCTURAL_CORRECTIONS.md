# T-397: structural corrections of Checker-verified reconciliations into the SAME candidate (ARCH_TAKEOFF_V3.0.33; integration package, Gate B)

Worker 3 (lane I), claim 2026-10-31 17:05 UTC. Development villa, not an accuracy claim; NOTHING RELEASED; the released
default stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only.
integrates: T-391 (MERGED c3fe8ec8), T-392 (MERGED cc3c7f08), T-394 (MERGED e27c5d78), T-256 (MERGED 74c966b1).
Not in this package (row scope): T-394 P3 joint + head 3.774 m3 and anything of T-395 / T-398 (merged after the row
was written; their quantities are not taken here).

## 0. Sources and runs

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), decoded into `.work/private` only. Own chain run on the task head:

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t397/v3033_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t397 --t167 <private>/t167
python3 -I research/agents_t397/t397_summary.py <private>/t397/v3033 --write
```

The run writes V3_0_5_* .. V3_0_32_* (V3.0.32 reproduced: the candidate of record this package binds to) and
V3_0_33_*; `summary_t397.json` holds the engine side (line ids, codes, units, quantities; no element id with a
position, no coordinate, no name). Inputs: `t397_inputs.py` builds URBAN_V3033_INPUTS_V1 ONLY from the four merged
files pinned by sha256 (summary_t391.json, summary_t392.json, summary_t394.json, LEDGER_T256.csv) and the committed
binding `BINDING_V3032_T397.json` (item, floor, state per line id; the module stops on any line that does not stand
in V3.0.32 exactly as bound).

## 1. Physical elements and what each line now carries (ERS s.2.1)

| Element (drawn) | Line(s) | V3.0.32 | V3.0.33 | Evidence status (WORKFLOW_CONTROLS s.5) |
|---|---|---|---|---|
| Ground-slab cell around the lift shaft (T=10cm on the GROUND BEAMS PLAN), engine cell SITE-c1089bdb | L-41cfb82e STR.CONC.GROUND_SLAB | BOUNDED 3.929788 .. 3.929788 (net cell 39.2979 m2 x 0.10: holds the 1.80 x 1.80 shaft and strips) | BOUNDED **0 .. 3.560540** (own slab panels 35.6054 m2 x 0.10; shaft 3.24 + strips / column pieces 2.9883 = 6.2283 m2 out) | HELD (the shaft-corner columns read as free columns, T-042; the line carries no value) |
| GF beam B8 (BAND0003), straight B7 (BAND0006), CB1 span 2 (BAND0041.2) | L-9a55aadc / L-cbf53752 / L-9270e8b8 STR.CONC.BEAM | 0.526665 / 0.254647 / 1.337922 | **0.528021 / 0.255000 / 1.338750** | B8 VERIFIED (Checker own cell 0.704028 m2, 0 m2 shared with the ring); B7 / CB1 DRAWING-CONFIRMED (Checker accepted the T-146 GAP; cells 0.340 / band 1.785 m2 not re-measured by the Checker) |
| GF beam CB8 (BAND0039) to the oblique B27 face 326 | L-7c1a1da8 STR.CONC.BEAM | 0.7163 (square band) | **0.716937** = (1.046136 - 0.08 - 0.01022) m2 x 0.75 | VERIFIED (Checker: DOUBLE 0.002767 AGREE, GAP 0.00336 vs 0.003406, 37D oblique 0.00005 immaterial) |
| 15 columns whose schedule section differs from the drawn outline (GF 344 / 347 / 359 / 380; 1F 667 / 673 / 676 / 679 / 685 / 688 / 68E / 691 / 694 / 697 / 69A) | 15 STR.CONC.COLUMN | PROVISIONAL at the schedule end: GF 2.475, 1F 5.964 m3 | **BOUNDED** per member (schedule x h | drawn x h): GF **2.070 .. 2.475**, 1F **5.964 .. 7.644** m3 | HELD (designer D-16 / D-63 / column-band item; Checker T-256 15 / 15 outlines own = drawn, range 8.034 .. 10.119; Checker T-394 GF drawn 2.070) |
| Formwork of those columns: the 10 valued EDGE_BAND faces beside them (V3.0.30) | 10 STR.FORMWORK | PROVISIONAL, 0.928054 m2 | **HELD BLANK**, figures beside | HELD (DEPENDENT: a quantity on a held line is held, WORKFLOW_CONTROLS s.1; the V3.0.30 guard keeps valued formwork only beside a live concrete line of its own state) |
| Lift pit walls: S-BW ring 2.20^2 - 1.80^2 = 1.600 m2 less the four lift column pieces 0.500 m2 (neck lines own them) | NEW STR.CONC.LIFT 'LIFT_PIT:WALLS' (FOUNDATION) | no line (MISSING) | **HELD BLANK**, plan ring net 1.100 m2 beside | HELD (pit depth 'as per lift manufacturer', ST p.14; lift-supplier RFI 1; board refs D-43 / D-63); ELEMENT_REGISTER: structural concrete, lane S; never also blockwork or WP (pit membrane = T-353) |

Every other line: byte-identical to V3.0.32 (4659 of 4689; asserted by the module, sha in summary_t397.json).

## 2. Methods side by side (ERS s.2.2)

| Element | Owner manual method | Drawing-derived method | V3.0.33 |
|---|---|---|---|
| Ground slab | Q-61 C member by member: the panel between the ground-beam faces x T | own polygonisation, 180 faces: the cell's four slab panels 35.6054 m2 (T-391) | held 0 .. 3.560540 (the cell's hold stays: T-042) |
| Beams | Q-61 C: to the carrier faces, a deduction only where another line owns the concrete | drawn cells / bands to the faces (T-252 r2, T-392) | drawn cell values |
| Columns | column = A x storey interval (joint + head owned by the column under C1, T-394 s.1) | A from the drawn outline (T-256), the schedule prints another A | the two readings as a range (R-COLUMN-EVIDENCE-1), never one end, never a mid value |
| Lift pit walls | 1.100 m2 x pit depth | the ring net of the column pieces (R-T394-6) | HELD: no printed depth |

## 3. Result in engineering terms (development villa, own run; freelancer side = the merged T-385 r2 / T-391 / T-394 residuals, his figures stay private)

| Family | V3.0.32 | V3.0.33 | Freelancer (engine - his residual, from the merged tasks) | Engine - freelancer |
|---|---|---|---|---|
| GF columns CL-GF | 17.9675 m3 valued (+ 5 annex HELD) | 15.4925 valued + BOUNDED 2.070 .. 2.475 = **17.5625 .. 17.9675** (+ 5 HELD) | 17.4375 | was +0.530 (+3.0 %); now **+0.125 .. +0.530 (+0.7 .. +3.0 %)** |
| 1F columns CL-1F | 10.248 | 4.284 valued + BOUNDED 5.964 .. 7.644 = **10.248 .. 11.928** | 7.728 | was +2.520 (+32.6 %); now **+2.520 .. +4.200** (the joint + head +1.080 RULE_DIFFERENCE and the counts +0.918 ENGINE_RIGHT stand; T-394) |
| Lift pit walls CL-LIFT | no line | **HELD BLANK** (1.100 m2 beside) | 2.400 (gross ring through the lift columns) | was -2.400 as a missing line; now -0.750 ENGINE_RIGHT (his ring double-counts the column pieces) + 1.650 HELD on the pit depth: no longer a silent gap |
| Ground slab GS-SLAB | 17.240684 valued + held 3.929788 | 17.240684 valued + held **0 .. 3.560540** | (residual -12.309316) | valued unchanged; the held bound no longer carries 0.369248 m3 of shaft and strips |
| GF beams (four lines) | 2.835534 | **2.838708** | not compared line by line (T-385 / T-395 carry the family) | +0.003174 m3 (+0.11 % of the four lines): GAP 0.002566 (T-146 fit artefact) + CB8 GAP 0.003406 - DOUBLE 0.002767 + 4-dp ledger prints -0.000031 |
| Formwork (10 column edge faces) | 0.928054 m2 valued | HELD BLANK | | -0.928054 m2 valued, +10 held lines (released with their columns) |

Structural concrete valued across the touched codes: -8.435826 m3 leaves the valued total (8.439 to ranges, +0.003174
restored); ranges +8.034 .. +10.119 m3; nothing becomes 0.

## 4. Gate B data (WORKFLOW_CONTROLS s.1)

- Per line before / after (V3.0.32, released V2.9) and evidence status: `summary_t397.json` rows and V3_0_33_INTEGRATION_
  LEDGER.json / .csv of the run (private run dir); line-by-line diff vs V3.0.32 and vs V2.9: V3_0_33_DIFF.csv (counts in
  summary_t397.json: diff_vs_v3_0_32, diff_vs_released_v2_9).
- Always-hand-check set (s.1 rule 2): the 15 column lines (structural, every one moves >= 5 %, a new state), the
  held slab bound, the CB8 line (oblique face), the new lift-pit line (new scope), the 10 formwork lines (dependency).
  The three GAP lines move < 0.3 % each (B8 +0.26 %, B7 +0.14 %, CB1 +0.06 %) but are structural: hand-check too.
- Re-measure list (sources): GF CONFLICT drawn 344 0.10 / 347 0.08 / 359 0.08 / 380 0.20 m2 x 4.50 = 2.070 (ST GF roof
  sheet S-COL.BON outlines); 1F 667 0.20 x 1.00 x 4.20 = 0.840 vs schedule 1ST 20x90 0.756; lift ring 10EB / 10EA and
  S-COL.BON 1090 / 1093 / 1096 / 1099; held cell panels OWN-007 / -009 / -010 / -047 = 35.6054 m2; CB8 cell to S-BEAM
  326 with columns 359 / 37D.
- Regression: L4 on the task head (section 6).

## 5. Downstream impacts and double count

- Formwork: 10 valued column-face lines held with their columns (section 1); the 15 already-held formwork lines of the
  same columns keep their V3.0.32 text (byte-identical; their bounds were read at the schedule section and stay HELD).
  The four beam formwork lines stay valued and identical (the restores change no formed face).
- Rebar, finishes, blockwork: no line names a touched element (searched every V3.0.33 line's calculation and location).
- Double count: the lift-pit line owns the ring NET of the four column pieces (the neck lines own those); the pit
  membrane / protection stay FIN.WP (T-353); the CB8 part beyond face 326 stays B27's (B27 unchanged).
- Coverage registry: BOQ_FAMILY_MASTER 1.28.0 = 1.27.0 + pending V3.0.33 (no new code; STR.CONC.LIFT is B10-10's).

## 6. Rule, lessons row (proposed, ERS s.7)

R-T397-1 (engine/source/arch_v3033.py). | 2026-10-31 | Verified reconciliations (T-391 / T-392 / T-394) left their
corrections as proposals; the column CONFLICT lines sat as single schedule figures and the lift-pit walls had no line
| a correction lives in research until lane I binds it to line ids; a conflict carried as one figure looks valued |
a lane I correction binds by line id and the state / figure the verified ledger read (stale stops); a conflict is the
range of its two readings (each its print x height, units checked against the print); a held bound covers the
element's own pieces only; a missing element is a HELD BLANK line with its plan beside; a valued dependent
(formwork) is held with its concrete line (scope every villa; provenance T-397) | tests/t397_structural_corrections
(hand villa V397 normal; stale binding, wrong element, bound raised, held 0, GAP terms not closing, unnamed cause,
candidate at neither reading, mm reading, reading not its print, missing with a value, 0 beside, non-structural code,
unmerged source, line twice, applied twice, valued conflict, dependent beside a valued line, change outside rows
refused) | PROPOSED |

## 7. Not done / uncertain

- T-394 P3 (joint + head 3.774 m3) and T-395 / T-398 results: not in this row.
- The 5 annex GF columns stay HELD as before (3 of them are also CONFLICT; their hold is the annex roof, Q-54 B).
- B7 straight / CB1 span 2 cells: DRAWING-CONFIRMED only (the Checker re-measured the B8 cell and the CB8 end).
- The 15 held column formwork lines still say 'the concrete line is PROVISIONAL' in their own V3.0.30 text (not
  restated: byte-identical outside the rows); their state (HELD) is right.
