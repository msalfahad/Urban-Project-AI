# T-716 designer-list impact census: every HELD line of V3.0.70 by its printed cause (lane I, research only)

Worker 3, 2026-11-11, branch `agents/task-T-716`. Nothing wired, released, VERIFIED or summed into a total; no
quantity changed. Rules: UP-QTY-STATUS-001, R-T698-1 (derived lines carry HELD), new R-T716-1 (`t716_rules.py`,
proposed). Runner `t716_census.py` -> `out/T716_CENSUS.json` (af27f1d5) + `out/T716_CENSUS.md` (full tables). Tests
`tests/t716_designer_census` (4, synthetic, not the training villa).

## Inputs (own Drive chain this run)

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded into the private folder only: own t167 `v304_run.py` (exit 0) -> `research/agents_t693/v3070_run.py`
(exit 0, every earlier version re-run and asserted) -> **V3_0_70_BOQ_LINES e8e001de = the T-693 run of record**, 5,123
lines. The census asserts that hash and that the merged LINE_INDEX_V3_0_70 (6c12da07) was built on it (same line set).
Line classes and bounds come from the index; the cause of each HELD line from its own record (rfi.question, notes,
calculation.inputs.*.still_held). No cause text is written to the repository: only ids, codes, units, counts, bounds.

## R-T716-1 (one bucket per HELD line; every villa)

First match: (1) D-id printed -> DESIGNER, bucket = the set ('D-33+D-34'); (2) RFI code printed -> RFI (not mapped to
a D-id: the register was renumbered 2026-10-31, old S23 = new RFI-S08, and a bare code does not say which numbering);
(3) Q-nn / 'owner question OQ-nn' / ORR-nnn -> OWNER; (4) no id of its own and a HELD host named (element 'FW:L-<id>',
'waits for / source / beside L-<id>') -> the host's bucket, flagged DEPENDENT (cycle-safe; a RELEASED host gives
nothing); (5) engine reason code -> REASON_CODE; (6) 'designer / consultant' with no number -> DESIGNER_TAG; (7) method
gap words -> METHOD_GAP; (8) 'not printed / drawn / dimensioned / specified' -> NOT_PRINTED; (9) other text ->
NAMED_TEXT; (10) none -> UNNAMED. Per family and unit only, never across units; one-sided bounds on their side; blank
counted, never 0. A line held by two items is counted once (combined bucket) and listed as SHARED under each item.

## Result on V3.0.70 (2,765 HELD lines; 134 dependent; STR.REBAR 1,693 kg lines PARKED, shown apart)

| kind | active lines | parked rebar |
|---|---|---|
| DESIGNER (D-id) | 297 | 215 |
| RFI code | 7 | 0 |
| OWNER (Q / ORR) | 156 | 370 |
| REASON_CODE | 293 | 270 |
| DESIGNER_TAG (no number) | 44 | 79 |
| METHOD_GAP | 7 | 0 |
| NOT_PRINTED (no number) | 60 | 510 |
| NAMED_TEXT | 208 | 249 |
| UNNAMED | 0 | 0 |

Per designer item, SOLE lines (held by that item alone), rebar excluded; units never mixed:

| D-id | sole | shared | m3 | m2 | other |
|---|---|---|---|---|---|
| D-02 CB10 width | 4 | 0 | 2 bd 0.7438 .. 0.8925 | 2 blank (formwork, dep.) | rebar 11 |
| D-03 CB3 / B3 | 2 | 0 | 1 bd 0.212 .. 0.3975 | 1 blank | rebar 9 |
| D-04 unlabelled spans | 18 | 6 | 8: 5 bd 0.6264 .. 1.8792 + 3 blank | 7 blank | pcs 2 blank, kg 1 blank; rebar 40 |
| D-14 plot-line blinding | 2 | 0 | 2 bd 1.0693 .. 1.3655 | - | - |
| D-15 strap blinding | 1 | 1 | 1 blank | - | - |
| D-16 C8 section | 5 | 0 | 2 bd 1.656 .. 1.8525 | 3 blank | rebar 4 |
| D-27 drawn vs schedule width | 10 | 8 | 5 bd 4.4010 .. 5.2185 | 5 blank | rebar 28 |
| D-33 loaded ground beams | 21 | 4 | 9 blank | 12 blank | rebar 22 |
| D-34 GB title basis | 19 | 3 | 8 bd 1.1784 .. 1.5712 | 11 blank | rebar 22 |
| D-35 exterior GB depth | 24 | 3 | 11 blank | 12 blank | pcs 1 blank |
| D-39 roof datum / build-up | 92 | 21 | 29: 6 bd 2.0737 .. 2.8013 + 23 blank | 48: 30 bd 1,115.33 .. 1,250.82 + 18 blank | pcs 10, kg 5 blank |
| D-41 sunken panels | 9 | 8 | 3 blank | 3 blank | pcs 2, kg 1 blank |
| D-43 lift tie beam / pit | 7 | 3 | 5 blank | 2 blank | rebar 1 |
| D-53 W02 / main door | 4 | 0 | - | 2: 1 bd 5 .. 5 + 1 blank | pcs 2 bd 2 .. 3 |
| D-56 E1 riser | 3 | 0 | 1 blank | 2 blank | - |
| D-62 sheets not issued | 3 | 1 | - | 3 blank (roof layers) | - |
| D-63 lift columns | 11 | 29 | - | 11 blank | - |
| shared only | D-22 1, D-40 1, D-44 4, D-66 36 (with D-39 / D-63) | | | | |
| rebar only (parked) | D-05 10, D-26 12, D-28 5, D-36 62, D-38 2, D-57 19 | | | | |

## Findings for the Lead (DESIGNER_QUESTIONS.md)

1. D-ids in the seed DESIGNER_QUESTIONS.md that no HELD line cites by number on V3.0.70: D-06, D-08, D-09, D-13, D-17,
   D-20, D-24, D-29, D-30, D-42, D-45, D-46, D-47, D-58, D-60, D-64, D-65, D-67, D-68 (19 of 37). The stair lines cite Q-46 / Q-50 / Q-51 / ORR-007 / RFI-S27 and reason codes, not
   D-08 / D-67 / D-68; the lintel lines cite 'designer' with no number (22 lines) and Q-55 (4), not D-45 / D-58 / D-60 /
   D-64; the ceiling / build-up lines (FIN.FLOOR.BED 44, FIN.CEILING) carry no D-09 / D-22 / D-40 / D-24 number.
2. D-56 is kept OUT of the designer package (D_REMOVED_REVISED s.2) but 3 HELD lines still cite it (ST-03 E1 stair
   concrete + 2 formwork): either the package or the line text is stale.
3. Numbered-cause gaps: DESIGNER_TAG 44 active lines (STR.CONC 35: lintels 22, necks 8), NOT_PRINTED 60 (EXT.FENCE 17,
   thresholds, stair skirting), NAMED_TEXT 208 (STR.FORMWORK 53, of which 52 have a RELEASED concrete host: the face cause
   lives only in the T-332 face ledger; FIN.FLOOR.BED 44 'owner range' with no rule id), METHOD_GAP 7. Each needs a D-id, a
   Q-id or a method row; the full line lists by bucket are in T716_CENSUS.json.
4. RFI codes printed on 7 lines (RFI-S04, RFI-S08+S23, RFI-S23, RFI-S27) are ambiguous between the old and new RFI
   numbering; the Lead should restate them as D-ids.
5. Seed item 1 (STR.CONC.BEAM, 26 lines) splits by line as D-02 2, D-03 1, D-04 5, D-27 5, Q-61 1, and 12 with no
   number (11 NAMED_TEXT, mostly R-T660-3 projection strips, 1 DESIGNER_TAG): a D-id (D-05 / D-26 cover strips on the
   rebar side only) should name them.

## Owner manual method beside the drawing-derived method

Not applicable as quantities: this census measures nothing. It maps the HELD lines of the drawing-derived candidate to
the items that hold them, so the owner sends one list to the designer with the lines and quantities each answer opens.

## Lessons-register row (proposed, ERS s.7)

L-T716-1: a HELD line must print the NUMBER of what holds it (D / Q / RFI / method row), not only prose: 1,157 of 2,765
HELD lines on V3.0.70 name their cause in words only, so the designer list cannot be counted from the BOQ. Proposed rule
for new HELD lines (every villa): the cause field carries one id; regression = R-T716-1 test (normal: numbered cause
counted once; adverse: prose-only cause lands in a finding bucket, never in a D-id, never 0).
