# T-755 designer-list re-census + concrete HELD-tail sweep on ARCH_TAKEOFF_V3.0.77 (lane S, research only)

Worker 1, 2026-11-13, branch `agents/task-T-755`; **round 2 (rework of Gate A r1 fault F-V755-1, 2026-11-13 11:2x-12:4x UTC)**. Nothing wired, released, VERIFIED or summed into a total; no quantity
changed; no engine file touched. Rules: R-T716-1 (unchanged, imported), new R-T755-1 (`t755_rules.py`, proposed),
UP-QTY-STATUS-001, L-T748-1, T-380 / L-T745-1 (no scaled length), owner 2026-11-11 15:30 (rebar parked).

## Inputs (own Drive chain this run)

Drive 'Alsenan chalet project' / 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf' (9f9d1179),
decoded by the wrapper into the private folder only. Own `research/agents_t167/v304_run.py` (exit 0) ->
`research/agents_t749/v3077_run.py` (exit 0; every chain assertion ran). Line files of V3.0.70 .. V3.0.77 hash to the
merged line index of each version: e8e001de (T-693), fc0bd98f (T-704), f9578744 (T-703), c5a0b128 (T-722), bea5be02
(T-717), a1eba08f (T-729), 9b35725c (T-736), **b8524d5c (T-749) = the V3.0.77 run of record**, 5,241 lines.

## (A) Census, R-T755-1

R-T755-1 = R-T716-1 + (a) the Lead's alphanumeric item ids read from a CLOSED list only (whole token), + (b) an item
view (a D-id may sit under two items: D-44 in 1 and 3, D-63 in 3 and 6, D-45 in 2 and 12, D-62 in 5 and 13), +
**(v2) LIVE cause only**: a line whose inputs carry a cause-text record (action CAUSE_TEXT, e.g. V3.0.42 R-T433, or
RESTATE, e.g. V3.0.46 R-T419) is read from rfi.question + bounded_range.basis (+ fill still_held) only; its notes are
history (the retired 'old' value, superseded restatements and source texts) and are not read. Lines with no such record
are read exactly as R-T716-1. Ids printed only in the history are listed per line (`retired_hits`).

**r1 fault and fix.** r1 read the whole notes, so the V3.0.42 history "cause text 'D-63' -> 'D-66 (RFI-S20)'" (F-T433-2:
D-63 is the lift columns on the lift raft; the 13 band columns are D-66) put 13 STR.CONC.COLUMN + 22 dependent
STR.FORMWORK lines in 'D-63+D-66', and the V3.0.46 restatement note (pit depth 'L-1 / D-63', RFI-S09) put the lift
pit-wall line and its 2 form faces under D-63 although their live rfi (rewritten again by V3.0.73 / V3.0.75) does not
print it. v2 moves exactly those **38 lines** and no other (own diff r1 -> r2 on V3.0.77: 13 COLUMN + 22 FORMWORK
'D-63+D-66' -> 'D-66'; 2 FORMWORK 'D-43+D-63' -> 'D-43'; 1 LIFT 'D-22+D-40+D-43+D-63' -> 'D-43'). The 2 lift-pit WP lines
(membrane, board) print 'L-1 / D-63' in their LIVE rfi and stay 'D-43+D-63'.

**V3.0.70 re-derived = the merged T-716 census line by line except 27 lines** (asserted: every differing line has a
history-only id; any other difference fails the run): 26 'D-63+D-66' -> 'D-66' and 1 'D-22+D-40+D-43+D-63' ->
'D-22+D-40+D-63' (the lift pit wall, whose live rfi on V3.0.70 was the V3.0.46 restatement). T-716 carried the same
fault (its item 3 / item 6 D-63 counts are history artefacts). Every V3.0.70 -> V3.0.77 difference is attributed to the
version step that made it (residual 0 per bucket and per D-id, asserted).

HELD lines: 2,799 on V3.0.77 (2,765 on V3.0.70); 1,106 active + 1,693 STR.REBAR kg PARKED. **Every HELD line maps to
one cause; UNNAMED 0, UNMAPPED 0.** 149 dependent (cause from a HELD host).

| kind | active | parked rebar |
|---|---|---|
| DESIGNER (D-id) | 324 | 215 |
| RFI code | 7 | 0 |
| OWNER (Q / ORR) | 223 | 370 |
| REASON_CODE | 194 | 270 |
| DESIGNER_TAG (no number) | 55 | 79 |
| METHOD_GAP | 1 | 0 |
| NOT_PRINTED (no number) | 64 | 510 |
| NAMED_TEXT | 238 | 249 |

V3.0.70 -> V3.0.77 by package (lines; full table in `out/T755_CENSUS.md`): T-722 moved +7 D-05/D-26 projections, +2
D-08, +7 D-35 (court / annex ground beams), METHOD_GAP 7 -> 0 (they were the D-35 court lines, F-V716-1); T-729 took
36 BEAM_SIDE / 35 NO_LINE / 60 SPLIT_UNRESOLVED / 12 JOINT / 8 JUNCTION formwork codes out and put 126 lines under Q-10 +
Q-13 (rebar), 12 D-33 and 11 D-34 lines out (formwork rows re-classed), 11 D-63 formwork lines out and 9 D-66 in
(formwork rows re-tied to their column hosts); T-722 1 lift pit wall 'D-22+D-40+D-63' -> 'D-43' (its V3.0.73 AT_LEAST
rewrite of the live rfi);
T-736 +10 D-39 (bead rows), T-749 +38 EXTERIOR_FINISH_NOT_SPECIFIED and +27 FRAME_* (paint edge lm); T-704 +4 D-45.

## (B) Concrete HELD tail: 194 STR.CONC.* m3 lines, **MEASURABLE_NOW 0, STILL_HELD 194**

Every line keeps the drawing fact named per family and cause (`out/T755_CONCRETE_SWEEP.md`). The merged pieces the row
named are already in V3.0.77 as beside bounds (T-711 / T-712 / T-721 wired by T-722; T-724 / T-731 by T-729): no merged,
Checker-verified piece holds a closed value that the candidate lacks. Own drawing reads:

1. **L-17953d78 lintel D-GF-14 (wall GF-W30)**, the one line carried as 'MEASURABLE NOW' since T-699. P7757 GF plan:
   masonry faces 2E5 / 2E7 stop at the door, 2E6 / 2E8 restart; frame lines 32D / 32E and 32B / 32C (layer D) and leaf
   arc 334 r 0.690: clear masonry gap **0.800 m** (T-103 hand 0.797). West pier 0.2787 (N face) .. 0.3727 m (S face) to
   the diagonal wall (325 / 319); east pier 0.0392 m to the crossing wall WB-FL0059-FL0060 (2DD / 2DE). Both ends are
   WALL JUNCTIONS = R-T678-3 OPEN ends: the cause is the junction-END ruling already open for D-GF-04 / D-1F-06 (Lead /
   Checker, not an owner question), not a missing read. Both piers < printed MIN 0.40 (deficit on any ruling).
   Conditional lo stays 0.15 x 0.20 x 0.800 = 0.024 m3 (if REQUIRED; existence OPEN, head Q-55 C ASSUMED - OWNER-
   APPROVED). If the ruling were 'junction = end of masonry': hi 0.15 x 0.20 x (0.800 + 0.3727 + 0.0392) = 0.036357 m3,
   stated only so the ruling's effect is known. Result STILL_HELD, cause restated METHOD GAP.
2. **L-d5401fa8 DOME-3 shell**: ST DXF prints one dome detail ('DETAIL OF DOME', 1A18: the terrace domes, T-193); no
   dome / ring / opening on the 2F roof slab (T-287 G3). STILL_HELD by D-21, which the line no longer cites (it prints
   SILENT_OMISSION) and which is in no list item.

Concrete m3 per cause (bounded lines only; blanks counted, never 0): NECK founding level not printed 32 lines 8.7724 ..
11.346 (no D-number: 24 NO_SINGLE_VALUE + 8 DESIGNER_TAG); LINTEL 45 (20 bounded 1.181 .. 1.82041 on 'designer'
bearings with no D-number, 4 Q-55 0.18 .. 0.230224, 21 blank); COLUMN 29 (27 bounded 11.80007 .. 15.5015); GROUND_BEAM
29 (8 bounded 1.17838 .. 1.57117 D-34, 20 blank D-33 / D-35 (AT_LEAST beside where T-712 formed one; the 3 court lines none), 1 Q-28 capped blank); BEAM 30 (14
bounded, 16 blank D-05 / D-26 / D-28).

## (C) Proposed refreshed item table for DESIGNER_QUESTIONS.md (the Lead writes it; counts = active lines, V3.0.77)

| # | D-ids | sole / shared active lines | change vs the V3.0.70 figures |
|---|---|---|---|
| 1 beams | D-02, D-03, D-04, D-27, D-30, D-44 (+ propose D-05, D-26, D-28) | 36 / 18 (+ 88 rebar parked) | add D-05 / D-26 (21 / 28 lines incl. rebar, edge projections) and D-28 (dome ring): today in no item |
| 2 lintels | D-45, D-58, D-60, D-64 | 0 / 6 | 30 lintel lines say 'designer' with no number (bearings MIN 40 cm): give them D-58 / D-64 or a new D-id |
| 3 columns | D-16, D-46, D-63, D-65, D-66, D-44 | 40 / 16 (m3 15 sole bounded 8.034 .. 10.119; m2 25 sole, 10 bounded 59.2623 .. 68.0029 + 15 blank; shared m3 7, m2 9) | r1 5 / 54 was a history artefact (F-V755-1); D-66 alone holds 35 lines (13 COLUMN m3 6.378 .. 8.2665 + 22 dependent FORMWORK); **D-63 holds no column line live** |
| 4 ground beams | D-33, D-34, D-35 | 47 / 1 (+ 22 rebar) | D-33 / D-34 formwork rows re-classed by T-729 |
| 5 roof datum | D-06, D-17, D-39, D-62 | 105 / 21 | D-39 +10 bead rows (T-736); still the largest item |
| 6 lift | D-43, D-63 | 11 / 2 (+1 rebar) (sole m3 7 blank: LIFT 2, NECK 4, LINTEL 1; m2 4 blank FORMWORK; shared 2 WP m2 blank) | r1 8 / 40 was a history artefact; D-63 live only on the 2 lift-pit WP lines; restate RFI-S08 / S23 (lift raft blinding) as D-43; see F-T755-5 |
| 7 stairs | D-08, D-13, D-29, D-56, D-67, D-68 | 5 / 0 | D-56 still cited by 3 lines (it is OUT); D-67 / D-68 cited by none |
| 8 floor build-up | D-09, D-22, D-24, D-40, D-47 | 0 / 1 | the 44 FIN.FLOOR.BED lines cite no D-id (NAMED_TEXT): they need D-09 / D-22 |
| 9 sunken panels | D-41 | 9 / 9 | - |
| 10, 11, 14 - 18 | none / D-20, D-42 / D-GF-07 / D-BAND / D-DRAIN / D-M1 / D-J1..3 | 0 / 0 | cited by no HELD line (16 - 18 have no candidate line by design) |
| new | D-14 blinding past the plot line; D-21 DOME-3; founding level per footing (necks, 32 lines) | - | propose list items |

## Findings for the Lead

- **F-T755-1 (id collision).** Item 14's id 'D-GF-07' is also the drawing's mark of the GF main entrance door (door
  schedule; 92 records print it as the door). It cannot be read as a designer id from line text; it is the same
  physical question as D-53 (main door / W02 width). Proposal: give item 14 a D-number (or merge it with D-53) and
  never use the D-<floor>-nn shape for list items (door / opening marks use it).
- F-T755-2: D-ids in no list item that hold active lines: D-05 (11), D-14 (2), D-15 (2), D-26 (16), D-28 (6), D-53 (4);
  rebar-only: D-36 62, D-57 19, D-38 2.
- F-T755-3: list D-ids cited by no HELD line: D-06, D-09, D-13, D-17, D-20, D-24, D-29, D-30, D-42, D-46, D-47, D-58,
  D-60, D-64, D-65, D-67, D-68 + all named ids of items 14 - 18.
- F-T755-4: the D-GF-14 lintel's 'MEASURABLE NOW' class is stale: it is the junction-END method gap (read above).
- **F-T755-5 (r2, live cause re-read of the 3 lift lines).** The lift pit-wall height (raft top -> slab-on-grade top)
  depends on two facts: the pit depth below the GF lift landing (lift supplier, RFI L-1) and the GF build-up (D-22 / D-40,
  RFI-S09). The designer register gives D-43 = the GF lift tie-beam size (ST p.8 n.19) and D-63 = the lift column / neck
  section conflict, yet: (i) V3.0.42 retired D-43 from L-684fcad3 (F-T433-1) and V3.0.73 (T-722 AT_LEAST rewrite) put
  'DESIGNER ITEM D-43 (upper end open: supplier pit depth)' back in its live rfi; its 2 form faces L-6d72f51d / L-e3eb0057
  print 'pit depth D-43'; (ii) the V3.0.46 restatement and the 2 live WP lines print 'L-1 / D-63' for the same pit depth;
  (iii) the D-63 register row itself says the pit depth is D-43. The pit depth therefore has no single id (D-43 or D-63
  or the supplier RFI L-1, by line). No count of item 6 changes (both ids are in item 6) and no quantity moves; the Lead
  names one id for the supplier pit depth in the list and the next lift package restates the 5 lines (cause text only).

## Owner manual method beside the drawing-derived method

Not applicable as quantities: the census measures nothing; the sweep found no line where a drawn dimension closes a
value (the one read confirms an open method ruling). The owner manual lintel rule (precast 1.20 m for D-GF-14: 0.800 +
2 x 0.15 = 1.10 -> 1.20) is beside the line already and does not depend on the junction ruling.

## Tests

`tests/t755_designer_recensus` (8, synthetic, not the training villa; r2 adds 3 + the runner check): closed-list named ids (door mark of the same
shape never read; whole token only), normal (two lines on one item, one shared through a two-item D-id, dependent
formwork follows its host), adverse (blank never 0, an AT_LEAST never closed into a range, kg apart from m3, an
unlisted D-id reported, duplicate line refused), version-step reconciliation (residual 0). r2 (R-T755-1 v2):
normal `test_normal_live_cause_after_a_correction_lands_in_one_bucket` (live D-66 -> one bucket; a line with no record
reads as R-T716-1); adverse `test_adverse_a_retired_old_id_left_in_history_or_superseded_text_is_ignored` (retired
'old' D-91 in the history and in a superseded source note -> ignored; the dependent form face follows the LIVE bucket;
an id a live field still prints is kept; history-only ids listed) and
`test_adverse_a_restatement_superseded_by_a_later_rewrite_is_history` (a RESTATE note naming D-63 / RFI-S09, rfi later
rewritten to D-43 -> 'D-43'; the same restatement still live -> 'D-43+D-63').

## Lessons-register row (proposed, ERS s.7)

L-T755-1: a designer-list id must not share the shape of a drawing mark (D-GF-07 = the main door mark): an id that
collides cannot be counted from the BOQ and silently double-reads door rows. Rule: list ids are D-<number> only;
regression = `test_named_ids_are_read_only_from_the_closed_list` (normal: a listed id is read; adverse: a door mark of
the same shape is not).

L-T755-2 (r2): a census reads a line's LIVE cause fields only. Cause-text records (CAUSE_TEXT old -> new, RESTATE)
rewrite rfi.question / bounded_range.basis and leave the old text in the notes as history; reading the notes after a
rewrite counts retired ids (35 column / formwork lines double-listed under D-63 + D-66 in r1 and in T-716) and
superseded restatements (3 lift lines). Rule R-T755-1 v2; regression = the two r2 adverse tests above (normal: live
D-66 -> one bucket; adverse: retired 'old' D-63 in the history -> ignored).
