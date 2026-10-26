# T-300 Beam reinforcement completeness safeguard (lane S, owner Stage C 2026-10-25 11:51, safeguard only)

Worker 1, 2026-10-25. A new opt-in, unwired module `engine/source/beam_rebar_completeness.py`
(BEAM_REBAR_COMPLETENESS_SAFEGUARD_V1); no frozen module, released V2.9 cell, route G item or measured bar group
changed. Development villa, not an accuracy claim.

Repeat: `.work/venv/bin/python -I research/agents_t300/t300_alsenan_dry_run.py <structural DXF> research/agents_t300`
(Drive "Alsenan chalet project" / "ST7757 dxf.dxf", sha 9f9d1179; note 21 read on "ST7757.pdf" p.8 this run).

## Physical elements and what route G reads

| Component | Physical element | How the drawing prints it | Route G today |
|---|---|---|---|
| SIDE_BARS | longitudinal face bars of a deep beam | remark text in the row ('2Ø12/30cm' in REMARKS; '2Ø12' + '30cm' in MIDDLE REINT.), or general note | not read: 0, silent (CB11 0.303 t carries none) |
| NESTED_LINKS | inner links of a multi-leg stirrup | link symbol of n closed loops in the row (block of polylines) | not read: one outer link, silent |
| TOP_CORNER | continuous-beam top bars per span between the support bars | model-space callout 'n', 'Ø', 'd' in the span column (not an attribute) | CB_TOP_THROUGH UNRESOLVED, blank, no evidence |

Statuses: DETECTED (evidence ids), NOT_REQUIRED (named evidence), UNRESOLVED (HELD, blank). kg only from supplied
printed inputs (count, Ø, length, source; a spaced notation also needs its count basis), else blank. A beam is COMPLETE
only for these three kinds and only when nothing is HELD or flagged; COMPLETE is never a verification of the measured
groups.

Text association: row bands from the table's own horizontal grid lines (fallback: half-way between row anchors); an item
within max(half its height, 5 % of the band) of a boundary, or outside every band, is AMBIGUOUS and never assigned.
Texts owned by a row insert and callouts lying on a FILLED attribute slot are that slot's glyph (never a second group);
a callout on an EMPTY slot is flagged EMPTY_SLOT_TEXT_VALUE; any other callout that is neither a side remark (right of
the bar slots under a MIDDLE / REINT / SIDE / REMARKS header) nor a corner callout (above every bar slot by > 1.5 text
heights, in exactly one span column) is flagged UNCLASSIFIED_CALLOUT.

## Alsenan dry run (43 beam rows: 30 simple + 13 continuous; route G items sha before = after, byte-identical)

| Component | DETECTED | NOT_REQUIRED | UNRESOLVED (HELD, blank) | Beside merged T-149 |
|---|---|---|---|---|
| SIDE_BARS | 30 (23 simple: 2Ø12/30cm x 19, 2Ø16/20cm B16 B26 B27, 2Ø14/20cm B19; 7 CB MIDDLE REINT. 2Ø12 + 30cm) | 13 (depth <= 0.60 m, p.8 note 21: B1-B6, CA, CB2 CB4 CB5 CB9 CB10 CB13) | 0 | agrees 41 / 43; B10, B12 have no plan occurrence in T-149 |
| NESTED_LINKS | 9 (B17, B19-B26: 2-loop symbol, 4 legs) | 21 (simple rows without the symbol; the table prints it on 9 rows) | 13 (all CB: no symbol column, no link detail read) | agrees 30 / 30 simple; CB: T-149 used a single-link path (silent) |
| TOP_CORNER | 28 spans (count / Ø = T-149 on all 28) | 30 (simple beams: TOP attribute, measured) | 2: CB3 span 2, CB8 span 1 (no callout) | agrees 60 / 60 |

Flags: CB3 '3Ø16' and CB8 '5Ø18' at support-bar level outside every attribute slot (UNCLASSIFIED_CALLOUT): T-149 reads
them from the PDF as the one 3 ø16 over both CB3 supports and CB8's 5 ø18 hooked from the end support over support 1;
route G's MID1 / MID2 attribute cells are empty there, so these support bars are not in route G at all. Unassigned: 3
lone glyphs of a schedule insert the reader did not read as a row (SH09, owner 8101, strap section).
Completeness: 7 COMPLETE (B1-B6, CA), 36 INCOMPLETE; kg measured 0 (no printed inputs supplied: nothing invented).

Engine vs freelancer: no quantity changes (safeguard only). The freelancer's beams line is a 150 kg/m3 lump (9.89 t,
RULE_DIFFERENCE, no %, T-149). What the safeguard makes visible as HELD in route G: side bars on 30 marks (T-149 lower
bound at least 361.94 kg + 25.28 kg on held members, notation count basis open), nested inner links on 9 marks (T-149
links path upper reading), corner bars on 28 spans (count / Ø now evidenced), 2 support bars not read (CB3, CB8).

## Verdict proposals

- ENGINE_RIGHT (safeguard) on detection: every side remark, nested symbol and corner callout T-149 read by hand from the
  PDF is found at the same mark / span with the same count and Ø (hand check on SH09 rows B7 '2%%C12/30cm', B16
  '2%%C16/20cm', B17 STR2 block 2 loops; SH07 CB11 span 1 '2' 'Ø' '12').
- UNRESOLVED (designer): '2Ø12/30cm' count basis (2 in all or 2 per face per 30 cm), nested-link sizes, CB link
  section, CB3 / CB8 support-bar runs; note 21 width bands (2 / 3 / 4 Ø12 'by width') are not printed.

## Lessons-register row (proposed, ERS s.7)

"A schedule that mixes block attributes and model-space text: a reader that takes attributes only drops every group
printed as text (side remarks, corner bars, a support bar written over an empty cell) silently. Rule: every bar callout
in a schedule row is either matched to an attribute slot, classified, or flagged; an empty slot with text on it is a
finding. Scope: any schedule; provenance: T-300 Alsenan dry run vs T-149. Test: tests/t300_beam_rebar_completeness
(normal + adverse)."

## Not done / uncertain

- Link symbols drawn as four separate LINEs (not one polyline) are not recognised as loops (none on Alsenan); a symbol
  outside a row band is unassigned, not guessed.
- Floors come from route G's plan binding (B10, B12 unbound); T-149 floors are shown beside.
- CB nested links stay UNRESOLVED until a link section / LINK_DETAIL evidence record is supplied.
