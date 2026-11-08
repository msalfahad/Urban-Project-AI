# T-643 B11 rebar on HELD concrete (F-T639-1) + 208 unbound bar lines (R-T643-1)

Worker 1, 2026-11-08, branch `agents/task-T-643`. Research ledger, unwired: nothing released or added, no candidate /
engine / rule / knowledge version / registry file changed; owner gate 2026-10-25 10:33 (no reinforcement calculation
code change) respected. Development villa only; drawings referred to by Drive folder and title only. Outputs:
`out/REBAR_ON_HELD_CONCRETE_T643.json` (every line, its inputs, the concrete hold, the decision / binding and basis)
and `out/REBAR_ON_HELD_CONCRETE_T643.md` (tables).

## 1. Physical element

The vertical main bars of one column over one storey interval: n bars x L x d^2/162 (net, kg; t at display;
OWNER_RULE_REBAR_2026-10-24 s.1), n and d from the schedule row of the printed mark, L = the storey interval between
two declared structural levels (the bars run through the beam-column joint, so the split of the interval into clear
height + controlling depth does not enter L). Laps never added (s.2 proposal, s.4 item 3). The concrete of the same
column is a different quantity: cross-section x clear height + joint; it can be HELD on an input the bars never use.

## 2. Rule R-T643-1 (t643_rules.py; every villa: rebar never more certain than the inputs it uses)

Reduce the concrete hold to the facts it rests on (rule + facts_used + declared levels of its latest effective T-449
register entry). DOWNGRADE when one of them enters n, L or d; KEEP when none does AND every bar input is printed AND L
equals the declared interval the concrete rule itself used (facts_h); anything else REFUSED (unknown hold rule, L not
reconciled, missing input, schedule re-read differing). Binding: BOUND only by an exact id route; an inferred link is
UNRESOLVED with the candidate named; a group of pieces with mixed states cannot give a piece its state (UNRESOLVED).

## 3. Part 1: the 14 lines (754.723 kg), 14 / 14 decided

| decision | columns | concrete hold (T-449 register) | enters | kg |
|---|---|---|---|---|
| KEEP | 1F-31/32/33/39/41/44/47, GF-14/24/30 | R-COL-SECTION-CONFLICT-1 (T-397, V3.0.33): printed schedule section vs drawn outline (T-256 list, D-63); facts_used none; levels declared, facts_h 4.20 (1F) / 4.50 (GF) = bar L | none | 595.435 |
| DOWNGRADE (proposal) | 2F-50/51/53/54 | R-COL-LEVEL-HEIGHT-1 (T-254, V3.0.17): LEVEL.STRUCTURAL_TOP.ROOF.MAIN not declared (D-39 roof datum; 2F-50 also D-44) | L (interval 2F -> roof) | 159.288 |

Re-add: 595.435 + 159.288 = 754.723 kg. KEEP lines by hand: C9 1F 12 x 4.20 x 1.580247 = 79.644 (x2); C4/C5/C6 1F
8 x 4.20 x 1.580247 = 53.096 (x5); C3 / C GF 8 x 4.50 x 1.580247 = 56.889 (x3). DOWNGRADE: C1 / C2 2F 6 x 4.20 x
1.580247 = 39.822 (x4). Independent drawing check: the 'Schedule of Columns' (Drive 'Alsenan chalet project', 'ST7757
dxf.dxf') re-read row by row: C GF 8 ø16, C3 GF 8 ø16, C4 / C5 1F 8 ø16, C6 1F 8 ø16, C9 1F 12 ø16, C1 / C2 2F 6 ø16:
8 / 8 cells agree with the records (private test re-reads them from the block attributes). The section conflict
changes the m3 of the column (low = schedule, high = drawn) but not one of n, L, d: the 10 lines stay released, cited.
The 2F four use the interval to a roof level the candidate does not declare (T-297 LB-10 already named it: one member,
one datum status across trades): 4 downgrade-only record proposals DGP-T643-* (Checker to issue / validate; owner
2026-10-24 23:57). Effect if applied: released B11 9,375.306 -> 9,216.018 kg (-1.70 %); never more released.

## 4. Part 2: the 208 unbound lines, 208 / 208 classed

| binding | family | concrete | lines |
|---|---|---|---|
| BOUND | beams (T-110 band -> P-C:BEAMS line; 4 bands not split in the candidate -> parent band) | RELEASED 30 / HELD 3 / EXCLUDED 4 | 37 |
| BOUND | ground beams (face-handle pair -> T-332 runs) + straps SB1-3 + arc bands | RELEASED 69 / HELD 49 | 118 |
| BOUND | pool R1 / R2 zones -> the one pool's walls / base; ST-01 MS1-U / MS2-L / MS2-U, ST-02 RS-A / RS-S / RS-LD -> the lines that name them | RELEASED 30 | 30 |
| UNRESOLVED | ground-beam pairs 114+115+7DF, 13E+7D6, 184+7CF: pieces HELD and RELEASED, T-138 span number is not the T-242 run number | - | 13 |
| UNRESOLVED | ST-01 MS1-L / MS1-T / two landing strips, ST-01b, ST-02 RS-C, ST-03, tank (no line names them; candidates named where inferred) | - | 8 |
| UNRESOLVED | lintel bars produced / flagged: one aggregate over 16 RELEASED / 44 HELD lintel lines, no per-lintel split | - | 2 |

56 bound lines are now also class A (concrete HELD / EXCLUDED); every one of the 208 stays HELD on its own T-639 cause:
no quantity changes. The old census band id of the arc GSO-A-157-158 (BAND0044) is superseded by T-332 (BAND0043).

## 5. Verdict proposals, lessons

No freelancer comparison (status census). Proposals: KEEP 10 = ENGINE_RIGHT (schedule counts x declared interval,
re-read from the drawing); DOWNGRADE 4 = ENGINE_WRONG until D-39 is declared (bars released on an undeclared level).
Lessons-register row (ERS s.7): "A concrete hold is inherited by a bar line only through the facts it rests on: a
section conflict does not touch main bars over a declared interval; an undeclared bounding level does. Bars are never
released on a level the concrete of the same member holds." Scope: every villa; provenance T-639 F-T639-1 + T-297
LB-10 + this task.

## 6. Tests

tests/t643 (12 + writer): V643 column K7 2F 10 T16 x 3.80 = 60.049383 by hand; section hold -> KEEP, roof-level hold ->
DOWNGRADE; mirror / units; adverse: bar length from an unprinted height kept released REFUSED, L not equal to the
declared interval, missing n / d / L (never 0), schedule re-read differing, released kg not reproduced, unknown hold
rule, unknown population, fractional count; binding rules (mixed group -> UNRESOLVED, worst state). Development villa:
14 decided (4 / 10), kg re-add 754.723, 3 by hand, 208 classed (185 / 23), outputs current; private schedule re-read.
