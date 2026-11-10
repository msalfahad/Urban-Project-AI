# T-671 CONCRETE GATE B ROUND 4: integration package ARCH_TAKEOFF_V3.0.65 (roof-column lows, CN not applicable, strip split)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-671`. **Integration package for Checker Gate B.** Opt-in
candidate only: the released default V2.9 + route G is untouched; nothing is released by default; no rule, owner
decision or frozen file changes. Development villa, not an accuracy claim. ERS s.2-5, WORKFLOW_CONTROLS s.1 / s.5,
UP-QTY-STATUS-001. Base: the published T-668 merge (V3.0.64, Gate B PASS, 033b52b9 / 0ed807c3).

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-669 ledger (b) (`research/agents_t669/out/T669_LEDGER.json`, sha e3f2dd96) | 8cb64551 | Verifier 2026-11-10 09:56Z Gate A PASS | 5 + 1 | 5 2F roof columns BOUND at R-T669-2; annex C3 CONFIRM (low refused by name) |
| T-647 census FR-T647-1 .. 5 (`research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json`, sha 610c67b0) | a521da8a | Verifier 2026-11-09 06:56 Gate A PASS (CN plan level confirmed 01:54) | 5 | NOT_APPLICABLE_WITH_EVIDENCE |
| T-642 FR-T642-2 (`research/agents_t642/out/T642_FIX_ROWS.json`, sha 5ce2188f) | 1c7411a5 | Verifier 2026-11-08T21:54Z Gate A PASS (own faces by handle) | 1 + 1 new | VALUE 0.050 + ADD_COMPANION 0 .. 0.025 |
| T-668 line index V3.0.64 (`research/agents_t668/out/LINE_INDEX_V3_0_64.json`, sha 44036973) | 033b52b9 | (binding) | 5,074 | binding by FULL id (T-668 lesson), asserted again on the live run |

Not wired, named (never 0): **T-674** (5 B10-05 ground-slab lines) has not MERGED: they keep their V3.0.64 state.
**2F C2 at the tank / 2F C3 / 2F C5** blank lines: no merged ledger states a lower end (D-66 section conflict).
**Annex C3**: R-T669-2 refuses (no printed opening top, annex slab thickness or slab-top level): CONFIRM.

**F-C-T669-1 (9th S-COL.BON outline 778 in the 2F roof slab), own read of 'ST7757 dxf.dxf' (sha 9f9d1179) this run:**
778 is a 0.20 x 0.40 outline at the slab's east edge with NO column tag (nearest texts: a slab bar note 0.45 m away,
beam marks B7 / B2 2.0 m away); the same 0.20 x 0.40 outline (77B) sits at the same place on the lower roof sheet
(that sheet repeats the other 2F outlines one for one, offset 38.724 m); no model-space TEXT / MTEXT reads '20x40'
(the schedule's cell-by-cell section texts were not searched this run). The 8 other outlines are bound to the 8 2F column lines (418 / 41E / 424 by the T-668
squares; the other five by the T-669 read, one line each). **Its owner line: none of the candidate's 2F column lines;
UNRESOLVED, no quantity, never 0** (no section printed: a column not in the schedule, or a non-column element). A
lane S census item (Lead); no quantity of this package depends on it.

## 1. One physical element once (ERS s.2.4)

- **Roof column vs roof slab vs beam band (2F).** Each column line runs from its approved base datum (9.65) to the slab
  top (UP-CONC-JOINT-001); the low end stops at 12.50 + 0.18 = 12.68 (the slab underside cannot be below the highest
  printed opening top + its printed thickness), the high end at the R-T658-4 ceiling 13.90. The junction squares the
  columns own (418 / 41E / 424, T-668) are inside these lines; no slab or band line bills them.
- **A struck schedule row is evidence of absence, not a zero measurement.** The 5 CN lines become
  NOT_APPLICABLE_WITH_EVIDENCE (no quantity, their bound 1.134 .. 3.483 m3 set aside by name); the CN NECK below GF
  stays on its 6 neck lines (unchanged, HELD on Q-21 C).
- **The strip is one element.** L-efd3f780 is valued at the B4 depth it carries (0.050); the extra depth if it is the
  B7 arc lead-in (0.025) is ONE new companion line, never inside the valued line; 0.050 + 0.025 = 0.075 <= the old
  high 0.12; the B7 arc itself (BAND0049, 0.282743, T-642 (d)) is a different, unchanged line.

## 2. Owner manual method beside the drawing-derived method

| Element | Owner / freelancer manual method | Drawing-derived method (wired) |
|---|---|---|
| 2F roof column | printed storey 4.20 x section (0.42 / 0.588) | 0.10 x 3.03 .. 4.25 = 0.303 .. 0.425; C9 0.14 x the same = 0.4242 .. 0.595 |
| CN column above GF | not taken off (freelancer 0 CN columns) | NOT_APPLICABLE_WITH_EVIDENCE (ST p.9 row struck) |
| GF strip | one depth over the strip | 0.20 x 0.50 x B4 0.50 = 0.050 + companion 0.100 x (0.75 - 0.50) = 0 .. 0.025 |

## 3. Evidence status (WORKFLOW_CONTROLS s.5)

- VERIFIED: L-efd3f780 0.050 m3 (Checker own re-measure, T-642 Gate A). DRAWING-CONFIRMED: the 5 CN absences.
- HELD BOUNDED (DRAWING-CONFIRMED bounds): 5 2F roof columns (D-39 decides inside 3.03 .. 4.25 m); NEW companion
  0 .. 0.025 (no mark on the strip).
- UNCHANGED (CONFIRM): annex C3 (upper only <= 0.50625). ASSUMED - OWNER-APPROVED: none. UNKNOWN: outline 778.

## 4. B10 before -> after (m3; candidate code totals, V3.0.64 d227173a -> V3.0.65 38af7909)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) | Lines |
|---|---|---|---|---|
| STR.CONC.COLUMN | 19.7765 (unchanged) | 9.168 .. 13.602 (18) -> **9.6702 .. 12.414 (20)** | 16 -> **9** | 64 -> **59** (5 N/A) |
| STR.CONC.BEAM | 66.870678 -> **66.920678** (+0.05) | 6.023229 .. 8.50771 (14) -> **5.983229 .. 8.41271 (14)** | 12 (unchanged) | 137 -> **138** |
| every other code | unchanged | unchanged | unchanged | |

Reconciliation (exact, asserted by `check_totals` from the changes alone): COLUMN low 9.168 + 1.6362 - 1.134 = 9.6702,
high 13.602 + 2.295 - 3.483 = 12.414, bounded 18 + 5 - 3 = 20, blank 16 - 5 - 2 = 9; BEAM released +0.05, low 6.023229
- 0.04 + 0 = 5.983229, high 8.50771 - 0.12 + 0.025 = 8.41271. B10 total: released +0.050, held low +0.4622, held high
-1.283 m3. The 5 roof-column highs equal the AT_MOST ceilings the V3.0.63 records carried (0.425 x 4, 0.595): the
range only gains its floor.

## 5. Line-by-line diff vs V3.0.64 (every other line byte-identical, asserted: 5,063 SAME)

| Line | Code | Action | Member | V3.0.64 | V3.0.65 | Hand check |
|---|---|---|---|---|---|---|
| L-d79d17d1 | COLUMN | BOUND | C1 2F 20x50 | blank (<= 0.425) | 0.303 .. 0.425 | 0.10 x (12.50 + 0.18 - 9.65) .. 0.10 x (13.90 - 9.65) |
| L-26f6b6f2 | COLUMN | BOUND | C2 2F 20x50 | blank (<= 0.425) | 0.303 .. 0.425 | same |
| L-33a9b772 | COLUMN | BOUND | C2 2F 20x50 | blank (<= 0.425) | 0.303 .. 0.425 | same |
| L-919a5749 | COLUMN | BOUND | C2 2F 20x50 | blank (<= 0.425) | 0.303 .. 0.425 | same |
| L-53f223b0 | COLUMN | BOUND | C9 2F 20x70 | blank (<= 0.595) | 0.4242 .. 0.595 | 0.14 x 3.03 .. 0.14 x 4.25 |
| L-0d4cd54c | COLUMN | NOT_APPLICABLE | CN | 0.378 .. 1.161 | N/A with evidence | 0.09 x 4.2 .. 12.9 set aside |
| L-1850e278 | COLUMN | NOT_APPLICABLE | CN | blank | N/A with evidence | |
| L-53a35abf | COLUMN | NOT_APPLICABLE | CN | blank | N/A with evidence | |
| L-d33f7498 | COLUMN | NOT_APPLICABLE | CN | 0.378 .. 1.161 | N/A with evidence | set aside |
| L-de9383f7 | COLUMN | NOT_APPLICABLE | CN | 0.378 .. 1.161 | N/A with evidence | set aside |
| L-efd3f780 | BEAM | VALUE | GF BAND0030.2 (B4) | 0.04 .. 0.12 | 0.05 (MEASURED) | 0.20 x 0.50 x 0.50 |
| L-bef35462 | BEAM | ADD_COMPANION (NEW) | BAND0030.2 depth B4 vs B7 | (none) | 0 .. 0.025 | 0.100 x (0.75 - 0.50) |
| L-fad18af6 | COLUMN | CONFIRM | C3 GF annex | blank (<= 0.50625) | byte-identical | no lower end printed |

## 6. Regression and validation

- Run of record (Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) / 'ST7757
  dxf.dxf' 9f9d1179, decoded into the private folder only): own fresh t167 `v304_run.py` -> `research/agents_t671/v3065_run.py`
  (exit 0): every earlier version re-run and asserted, V3_0_63 09ec4c1a, **V3_0_64 d227173a (asserted = T-668 run of
  record)** -> **V3_0_65 38af7909**, 5,075 lines; replaced 11, added 1, outside 5,063 byte-identical (asserted); diff vs
  V3.0.64: ADDED 1, CHANGED 11, SAME 5,063; vs released V2.9: QUANTITY_DIFFERS 1,046, SAME_QUANTITY 546,
  NOT_IN_RELEASED 3,483. Every earlier version's check re-ran on the result (V3.0.10 .. V3.0.63 chain + the V3.0.64
  state check).
- **Found by the chain run (fixed, regression test):** re-running `A3064.integrate(out, [])` passes the lines as their
  own base and refuses V3.0.64's own added pool blinding line as "already a candidate line". V3.0.65 re-runs the
  V3.0.63 chain and the V3.0.64 state check without a base (`test_base_carrying_an_earlier_added_line_integrates`).
- `t479_registry_census.py` (unchanged; verdict set V3.0.44 b3b08dd7, downgrade snapshot 81732639) on V3_0_64
  reproduces `research/agents_t668/out/LINE_INDEX_V3_0_64.json` byte for byte; on V3_0_65 -> `out/LINE_INDEX_V3_0_65.json`,
  issues {}, complete map, 0 stale blocks.
- `t671_package_families.py` (T-483 attribute unchanged, chain 64 -> 65): B10-06 10 changed, B10-07 1 changed + 1
  added.
- Tests `tests/t671_concrete_gate_b4`: hand villa V671 (a roof column with a printed opening top + slab, an annex
  column with neither, a struck schedule row with and without a bound, a strip with two admissible marks) + adverse
  (absence only ASSUMED, N/A with a quantity / on a released line / without or with a stale set-aside, companion with a
  floor / past the old range / without its VALUE / already carried / twice, tampered states, applied twice, the earlier
  added line); inputs builder (sha pins, full-id binding, member agreement); master 1.66.0. Results in the handoff.

## 7. Registry: BOQ_FAMILY_MASTER_1.66.0 (pending now, promoted IN the merge)

`research/agents_t671/build_master_1_66_0.py`: 1.65.0 + V3.0.65 pending + B10-06 / B10-07 text (0 problems). In the
merge the Verifier runs (as T-668):

    python3 -I research/agents_t671/t671_promotions_source.py --board .work/board/docs/agents --out research/agents_t671/out/PROMOTIONS_SOURCE_1_66_0.json
    python3 -I research/agents_t671/build_master_1_66_0.py --promote --write
    python3 -I research/agents_t671/write_manifest.py

## 8. Who is right (freelancer beside, never proof)

2F roof columns: the flat-storey 4.20 m figure (0.42 / 0.588) lies inside the drawn bound: UNRESOLVED (D-39). CN
columns: ENGINE_WRONG before (held lines for a member printed absent), now AGREE with the freelancer (0 CN columns).
Strip: NOT_COMPARABLE (his rows carry no location); B10 low end +0.05 m3.

## 9. Rule and lessons row (proposed)

R-T671-1 (engine/source/arch_v3065.py) = R-T668-1 + (j) a printed absence is a state with DRAWING-CONFIRMED evidence,
never a zero; (k) a range whose drawing fixes its low end is valued there with ONE companion line 0 .. x inside the old
range; (l) a restated line keeps the earlier versions' records under `superseded`.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | the V3.0.65 chain run failed where the synthetic villa passed: the
earlier version's state check was re-run with the new lines as their own base and refused that version's own added
line | a synthetic base carried no line an earlier version had added | every integration fixture carries one line
of each kind every earlier version wrote (changed, added, confirmed), and the re-run of earlier checks never passes
the new lines as their own base (every package; provenance T-671) |
tests/t671_concrete_gate_b4/test_arch_v3065.py::test_base_carrying_an_earlier_added_line_integrates | PROPOSED |
