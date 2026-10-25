# T-296: SKIRTING OPENING-TO-LINE LEDGER, every candidate skirting line with its deductions by opening id, every room once (development villa; every villa by R-T296-1)

Worker 2 (lane A), claim 2026-10-25 14:44 UTC, run session_01VC3p6Ak3e4yyZDH7jmYiDu. Integration dependency of T-246
(lane I: list every skirting deduction with its opening id; close the 9 nets short by 13.569 lm). Research only: no
engine module, rule or knowledge file, candidate line, released line or V2.9 cell changed; nothing released. ERS read and
applied: s.2.1 (physical element first), s.2.2 (evidence hierarchy: merged sills / sizes, then the engine), s.2.4
(reconcile in lm to named causes, never a plug), s.3 (one owner per wall base; existence of a base before a deduction),
s.4 (rule + tests, normal and adverse), s.7 (lesson row below). Builds on merged T-106 (the F-17 mechanism) and cites,
without re-deriving, T-128 r3, T-237 part 4, T-249, T-250, T-262.

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py, then research/agents_t254/v3017_run.py
(ARCH_TAKEOFF_V3.0.17, the candidate of record). Extract: `python3 -I research/agents_t296/t296_alsenan.py --extract
<run>/t254/v3017 <run>/t167/v29` -> CANDIDATE_V3017_SKIRTING.json (the FIN.SKIRTING lines: id, floor, engine room,
state, gross, net, listed deductions, runs by role, range; each line's room record: door / passage / window engine ids,
the V2.8 window classes; engine opening widths; no coordinate, no name). Ledger: `--write`; `--check` rebuilds byte for
byte; tests `tests/t296_skirting_ledger` (21).

## 2. Physical element and the readings

Conventional skirting is a strip at the foot of a finished DRY wall / column face, at floor level (UP-SKIRT-001 1.4.0,
UP-CER-002 lm, UP-CER-003 doors deducted). So it exists only where a dry wall base exists at floor level:

| boundary piece | skirted | evidence |
|---|---|---|
| wall / column face of a DRY room | yes | T-250 face metres (walk), engine runs wall + column |
| door / passage / lift opening | no, deducted once by opening id | T-249 census id, engine band opening, T-262 room by jambs |
| window, sill established above the floor | **yes**: the wall continues under the sill | T-237 part 4 merged sill (T-201 / T-175 / T-238) |
| window, sill at the floor (<= 0.02 m) | no: floor glazing | the same |
| window, sill not established | HELD range [0, edge] | UP-SKIRT-001 1.4.0 `sill_not_established` |
| base of a WET room (full-height wall porcelain) | no: the tile owns it | owner Q-06 A, Q-37 A, Q-48 A; T-128 r3 KIND |
| base along the stair shaft | HELD blank | no owner rule for skirting along a flight (stringer or skirting) |
| open side / zone line | no | nothing is built |

## 3. The 13.569 lm: line by line, window by window (acceptance 2)

Every quantity line (11) re-adds once its unlisted part is named (LINE_TRAIL_T296.csv: residual <= 0.000001 lm). The 9
short lines are short by exactly the F-17 equal-split credit of the window-frame edges (release_safety.skirting: an edge
carrying both WINDOW and WINDOW_THRESHOLD roles is split 50 / 50; the WINDOW half is listed as "glazing edge", the
threshold half is taken off unlisted; the room's BOUNDED_EXPOSURE range line holds the whole edge). Per census window
(WINDOW_CAUSES_T296.csv; engine id -> census id by T-249 ENGINE_REF, room by T-262):

| Line (engine room) | Window (engine id) | Edge lm | Unlisted half lm | Merged sill | Reading (physical) |
|---|---|---|---|---|---|
| L-71e2e002 GF open plan | W02 (OP-019) | 6.3316 | 3.1658 | HELD | HELD range |
| | W09 (OP-024), in pantry GF-07 | 1.5000 | 0.7500 | 1.00 | NOT SKIRTED: wet pantry base |
| L-d3241491 GF-01 majlis | W11 (OP-028), W12 (OP-029) | 1.9549 x 2 | 0.9775 x 2 | HELD | HELD range |
| L-bb0ea965 GF-04 driver | W04 (OP-004) | 0.6000 | 0.3000 | 1.70 (T-201) | **SKIRTED** |
| L-af6fb2d3 GF pantry part | W10 (OP-023) | 1.0000 | 0.5000 | 1.00 | NOT SKIRTED: wet pantry |
| L-ba3599ec 1F living + shaft | W15 (OP-016), W16 (OP-017) | 1.5523 x 2 | 0.7762 x 2 | 0.00 (T-238) | NOT SKIRTED: floor glazing |
| | W13 (OP-021), W25 (OP-012), shaft ST-1F | 1.2000 / 1.0000 | 0.6000 / 0.5000 | 1.00 / 0.00 | HELD: stair shaft |
| L-c021ae79 1F-01 | W14 (OP-022) | 2.4498 | 1.2249 | 1.40 (printed) | **SKIRTED** |
| L-309f118f 1F-11 | W17 (COP-001) | 3.2895 | 1.6447 | HELD (T-238 archivolt) | HELD range |
| L-2f58111e 1F-04 | W24 (OP-003) | 1.5523 | 0.7762 | 1.00 (T-201) | **SKIRTED** |
| L-d057b5b0 2F-03 | W29 (OP-005) | 1.2000 | 0.6000 | 1.00 (T-201) | **SKIRTED** |
| **9 lines, 14 windows** | | **27.1376** | **13.5688** | | |

Doors and passages (DEDUCTIONS_BY_OPENING_T296.csv): the engine's single "door / passage openings" entry is split by
id: band doors at their ARCH_OPENINGS width (OP id -> census id), plus the drawn door blocks with no band opening (the
engine DOOR_CLOSURE role: D-GF-14, D-1F-03, D-1F-04 at their T-237 width), which T-106 could not name. Every door run
closes to 0.000 lm. The passage run closes in all rooms but the two GF open-plan faces, where the one band passage OP-003
(11.22 m) is longer than its stretch on each boundary: -1.400 lm (L-71e2e002) and -8.720 lm (L-af6fb2d3), named
PASSAGE_RUN_RESIDUAL (a shared zone line), never absorbed.

**T-246 consumer shape:** DEDUCTIONS_BY_OPENING_T296.csv, one row per (line, opening id or named cause): kind, length,
listed (as the engine lists it) or not, source, cause, the window's sill state and room. gross - sum(rows) = net to
0.000001 lm on every line. T-246 writes these rows as the line's deduction list; the threshold halves go in as
"window threshold, sill not established: held whole in range line L-..." (T-106 fix proposal), nets unchanged.

## 4. The physical reading per line (before -> after, LINE_LEDGER_T296.csv)

| Line | Room | Candidate net / range hi | Ledger lo .. hi | Cause | Status |
|---|---|---|---|---|---|
| L-bb0ea965 | GF-04 driver | 10.200 / 0.600 | **10.800** | W04 sill 1.70: skirted (+0.600) | DRAWING-CONFIRMED |
| L-c021ae79 | 1F-01 | 13.450 / 2.450 | **15.900** | W14 sill 1.40: skirted (+2.450) | DRAWING-CONFIRMED |
| L-2f58111e | 1F-04 | 14.048 / 1.552 | **15.600** | W24 sill 1.00: skirted (+1.552) | DRAWING-CONFIRMED |
| L-d057b5b0 | 2F-03 maid | 16.000 / 1.200 | **17.200** | W29 sill 1.00: skirted (+1.200) | DRAWING-CONFIRMED |
| L-c47fc614, L-a8aea284 | GF-15, 1F-10 | 14.633, 14.300 | unchanged | no window threshold | DRAWING-CONFIRMED |
| L-d3241491 | GF-01 majlis | 14.218 / 3.910 | 14.218 .. 18.128 | W11 / W12 sill not printed | HELD |
| L-309f118f | 1F-11 | 17.161 / 3.289 | 17.161 .. 20.451 | W17 archivolt (T-238) | HELD |
| L-ba3599ec | 1F living + ST-1F | 41.435 / 5.305 | **31.203 .. 43.635** | W15 / W16 floor glazing leave the range (-3.105); the shaft part's walls 10.232 lm (T-250 walk) and W13 / W25 2.200 have no skirting rule | HELD |
| L-71e2e002 | GF open plan | 28.172 / 7.832 | 28.172 .. 34.503 (not a lower bound) | W09 is a pantry window (-1.500 off the range); the wet pantry's wall bases inside this engine room (engine REVIEW, OPEN_PLAN_WET_SCOPE_EXTENT) are in no merged face split: GF-07 walks 7.000 lm of base (T-250), the pantry-only engine room carries 1.900 of it, so about 5.1 lm of this line is a wet base (information, not a quantity) | HELD |
| L-af6fb2d3 | GF pantry part | 1.900 / 1.000 | **NOT_APPLICABLE** | the engine room lies wholly in GF-07 (T-262 0.209 / 1.000), a WET area: full-height wall porcelain | ASSUMED - OWNER-APPROVED (Q-37 A, Q-48 A) |

Sum over the 11 lines: candidate certain 185.517 lm, + range lines 27.138 lm (212.654 hi). Ledger: the four sill windows
add **+5.802 lm** to determinate lines; 5.605 lm of window edges are no skirting at all (W15 / W16 floor glazing
3.105, W09 / W10 wet pantry 2.500); 1.900 lm of pantry skirting is not applicable; 10.232 lm of shaft walls and 15.731 lm of window edges
(W02, W11, W12, W17, W13, W25) stay HELD. No line's quantity is changed here.

## 5. Every room once and the independent walk (acceptance 1)

ROOMS_T296.csv: the 32 T-128 rooms + the 6 engine cells outside T-128, each with its candidate line(s) or the reason it
has none. 17 WET rooms NOT_APPLICABLE (V3.0.17 writes the record for all 17; the released V2.9 run omits it for the
three unlabelled cells GF-02 / GF-11 / GF-14: no quantity lost); 3 shafts HELD; 3 lift shafts and 2
outdoor cells nothing to skirt. Findings:

- **2F-01 stair lobby: 6.138 lm determinate** (T-250 walk, 3 doors deducted), but the candidate has it only inside the
  stair room's BLOCKED_RFI line 2F-R4D1B62 (engine room = lobby + ST-2F). Proposal: ENGINE_BLOCKED; the lobby part is
  measurable now.
- **1F dressing 1F-RFFE7AF: a dry room with no skirting line (MISSING).** Engine boundary 6.90 m (engine figure, not
  independent; no T-128 walk of the cell): HELD, never 0.

LINE_ROOM_JOIN_T296.csv: for the 9 lines whose engine room is a union of WHOLE T-128 rooms, the walk-derived run
(T-250 wall + column metres + the windows the same evidence skirts) against the ledger figure: **+0.019 .. +0.032 lm per
line**, decomposed into contour vs gross, door block extent vs the walked jamb gap (**+0.020 lm per two doors**:
the walk stops 0.01 m short at each jamb sample), window edges, open sides vs 'other', T-250 closure; residual
**<= 0.002 lm** (3-decimal rounding). So every determinate ledger figure is confirmed by an engine-independent walk to
within 0.032 lm (0.2 %). Not comparable: the two GF open-plan lines (engine rooms cut GF-07 / GF-08: no face split).

## 6. Engine vs freelancer

The freelancer's skirting is 282.85 lm = 12 dry-room gross perimeters with no door deduction (T-106). Candidate certain
185.52 lm (212.65 with every held range); this ledger 179.19 lm determinate-or-low on the same lines plus 2F-01 6.14 lm
and the dressing MISSING; the four sill windows move +5.80 lm toward him, the floor glazing and wet-pantry edges move
-5.61 lm of range away. RULE_DIFFERENCE dominates (owner UP-CER-003: doors and passages are deducted; he deducts none),
so no percentage is a measure of accuracy. Verdict proposals: W04 / W14 / W24 / W29 ENGINE (candidate) WRONG to hold the
threshold (merged sills printed or drawing-confirmed above the floor); W15 / W16 ENGINE WRONG to range floor glazing;
L-af6fb2d3 ENGINE WRONG (dry skirting in an owner wet area); 2F-01 ENGINE_BLOCKED; dressing ENGINE_OMISSION; W02 / W11 /
W12 / W17 / shaft UNRESOLVED (no sill / no rule).

## 7. Statuses, holds, no owner question

Lengths: DRAWING-CONFIRMED (engine runs re-added; T-250 walk agrees within 0.032 lm). Window readings: DRAWING-CONFIRMED
where the merged sill is printed / drawing-confirmed; ASSUMED - OWNER-APPROVED for the wet-pantry base (Q-37 A, Q-48 A);
HELD where the sill is not established (W02, W11, W12, W17) or the base is on the stair shaft. Nothing VERIFIED or released
here. No owner question (ERS s.2.7 not met: the open items are named designer items, sills of W02 / W11 / W12 (T-144 /
T-207) and W17 (T-238), and the stair skirting, which the stair rule set may settle with the Lead).

## 8. Rule (R-T296-1, scope every villa, provenance UP-SKIRT-001 1.4.0 + ERS s.3; research rule, not a rule-file version)

A skirting line's trail lists every length it takes off by opening id or named cause, each once; a window edge is
skirted when its sill is established above the floor, not skirted at the floor, and held whole in a range when the sill
is unknown; a wall base owned by another finish (full-height wet tile, stair) carries no skirting; a residual of an
aggregate is named and signed, never absorbed; a held run is blank, never 0 (skirting_opening_rules.py; tests normal and
adverse on villa K296).

## 9. Lessons register row (ERS s.7, proposed)

| 2026-10-25 | 13.569 lm of skirting taken off 9 lines without a trail; four windows already proved sill-above-floor (W04, W14, W24, W29: 5.802 lm) and two floor-glazing windows (W15, W16) stayed in held ranges; one dry skirting line sat in an owner wet area | the F-17 split took the threshold half off unlisted, and the V2.8 window classes were never re-read when T-201 / T-238 merged the sills; the room's finish owner was read from the engine cell, not the room | a skirting line lists every deduction by opening id; window readings follow the merged sill record, re-read whenever a sill merges; one owner per wall base, decided by the room function (wet list), not by the engine cell | tests/t296_skirting_ledger | PROPOSED (T-296) |
