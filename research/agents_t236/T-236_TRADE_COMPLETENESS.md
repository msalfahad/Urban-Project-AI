# T-236: independent trade completeness (development villa P7757; rule and module for every villa)

Worker 1, 2026-10-23 22:23 - 23:20 UTC. Lane S, gate 2, backlog-permitted (input of T-235 part (3)). Owner 2026-10-23
19:00 trade completeness rules 1-6 and the 19:45 acceptance. ERS read: s.2 step 1 (element first: the expected
population of a trade is the drawn elements, never the engine's own list), s.3 (completeness vs accuracy, installed vs
procurement kept apart), s.4 (rule + test), s.7 row below. No quantity, line, method, rule or knowledge file changed;
nothing released. Drawings are cited by Drive title and DXF handle only; no coordinate, image or client name committed.

## 1. What was built

| File | What |
|---|---|
| `engine/source/trade_completeness_v1.py` | NEW pure check module (stdlib, `DEFAULT_GUARD_CLASS = "CHECK_ONLY"`, wired into no method). `check()` joins independent inventories, the register and the BOQ lines per principal trade; `reconcile_line()`; `reference_line_rows()` (the T-235 part (3) form); `line_trade()` |
| `tools/trade_completeness.py` | runner: input JSON -> `TRADE_COMPLETENESS.json`, per-trade CSV, element CSV, `REFERENCE_LINE_ROWS.json`; exit 2 on a refused input |
| `tests/t236_trade_completeness/` | 27 tests: the 5 ported probes (strict xfail in commit 5ebe0410, markers removed in ee4a6d2f), the synthetic villa acceptance (every injection), runner, metamorphic |
| `research/agents_t236/alsenan_t236.py` | the development-villa adapter (merged independent inventories -> check input), `SUMMARY_V29.json` / `TRADES_V29.csv` (released V2.9 run A) and `SUMMARY_V308.json` / `TRADES_V308.csv` (candidate V3.0.8) |
| `tests/structural_comparison_engine/rebar_product_registry.py` | one line: the new module declared in OTHER_REBAR_AWARE (it names the REBAR trade row only; the firewall test requires the declaration) |

Element statuses (precedence): EXCLUDED (owner rule id, or every line excluded) > VERIFIED (Checker COUNTED verdict) >
MEASURED > HELD (named reason) > UNRESOLVED (held, no reason) > INVENTORY_GEOMETRY_ONLY (untagged drawn geometry, risk
named) > CONFLICT (no line, the covering inventories disagree; never picked) > MISSING; and, for an element no
inventory found, REGISTER_ONLY / OUT_OF_INVENTORY_SCOPE (never in d). A `measurement` field keeps what the lines say
beside the inventory status. Flags: `duplicated` (two additive lines of one trade on one element, component and unit; a
never-additive pair is not a duplicate; one label on two storeys is two keys), `inventory_agreement`.
completeness % = (measured + held) / d and verified % = verified / d, d = the independent inventory count, each with
n / d in its own table; accuracy (WAPE, compared n / d) only in its own table; no combined figure is ever written.
Every principal trade (18 concrete families, masonry 100 / 150 / 200, plaster, paint, floor, wall finish, ceiling,
waterproofing, doors, windows, stairs, railings, formwork, rebar) has a row in every report; one with no line is
NOT_MEASURED; one with no independent inventory is NO_INDEPENDENT_INVENTORY with completeness "n/a", never 100 %.
Deductions: gross - sum(deductions) + sum(additions) = net within 0.001; one opening id once per face (in a line and
across the lines of one trade on the same element and face); every opening id in the opening census when given.
Inventories with an engine basis are refused; two different lines with one line id are refused.

## 2. Regression baseline (owner 19:45 (3))

| Probe | Injected fault | 5ebe0410 (merged head + tests) | ee4a6d2f (fix) |
|---|---|---|---|
| 1b | footing in the drawing, absent from register AND BOQ | XFAIL (no detection) | PASS: FDN:F5 MISSING |
| 2 | one footing on two lines | XFAIL (totals sum both, 7.6 m3) | PASS: FDN:F1 DUPLICATED |
| 3 | opening W05 deducted twice | XFAIL (boq_line accepts) | PASS: REFUSED DEDUCTION_REPEATED:W05 |
| 6 | one storey FFL +1.00 / +1.05 on two sheets | XFAIL (no sheet check) | PASS: CONFLICT row |
| 9 | whole PAINT trade absent | XFAIL (crosswalk NOT_MAPPED only) | PASS: PAINT row NOT_MEASURED |

Each test first asserts the probe's "actual today" on the existing module (unchanged), then the new detection. Suite on
the final head: 0 XPASS, 0 XFAIL.

## 3. Development villa: per-trade report (inventories named; Drive "Alsenan chalet project")

Runs on the Drive copies (P7757.dxf from P7757_DXF_COMPRESSED.zip sha ab54dd55..., "ST7757 dxf.dxf" sha 9f9d1179...):
released ARCH_TAKEOFF_V2.9 run A (research/agents_t167/v304_run.py v29, 1,621 lines) and the opt-in candidate
ARCH_TAKEOFF_V3.0.8 (research/agents_t231/v308_run.py, 3,553 lines). Independent inventories (merged, drawing-derived,
none built from the engine's register):

| Trade | Inventory (d) | Source | Join to the BOQ |
|---|---|---|---|
| CONCRETE.FOOTING | 26 outlines | T-233 LEDGER_T233.csv (FOUNDATION PLAN outlines by handle) | mark count per storey (the engine id prints the type, not the handle) |
| CONCRETE.NECK | 36 | T-217 LEDGER_T217.csv, FOUNDATION, DRAWN | EXACT: one solved plan translation (75968, 14448) maps 36 / 36 ledger ids onto this run's ids |
| CONCRETE.COLUMN | 59 = GF 30 + 1F 20 (18 + 2 planted) + 2F 9 (8 + 1 planted) | T-217 ledger GF / 1F / 2F DRAWN + T-220 members starting on a slab (the two over necks 10D0 / 10DA are the ledger's C8 / C9, not counted twice) | EXACT 56 / 56 by the same translation; planted records by printed handle (GFRS 329 / 386, FFRS 77B) |
| DOORS | 27 = GF 14 + 1F 10 + 2F 3 | T-198 OPENINGS_T198.csv KIND DOOR | EXACT by engine token (DOOR-<storey>-<hash>) |
| WINDOWS | 29 = GF 12 + 1F 13 + 2F 4 | T-198, KIND WINDOW | EXACT by token (OP-nnn on that storey) |

| Trade | V2.9 completeness | V2.9 verified | V3.0.8 completeness | V3.0.8 verified | Status / gaps |
|---|---|---|---|---|---|
| CONCRETE.FOOTING | 25 / 26 (96.15 %) | 0 / 26 | 25 / 26 (96.15 %) | 0 / 26 | 1 MISSING by label + 1 REGISTER_ONLY (one footing, see F1) |
| CONCRETE.NECK | 36 / 36 (28 measured + 8 held) | 0 / 36 | 36 / 36 (36 held) | 0 / 36 | complete against the inventory |
| CONCRETE.COLUMN | 59 / 59 | 0 / 59 | 59 / 59 (57 + 2 held) | 0 / 59 | 5 REGISTER_ONLY (F2), 5 OUT_OF_INVENTORY_SCOPE (F3) |
| DOORS | 27 / 27 (17 lines + 10 held) | 0 / 27 | 27 / 27 | 0 / 27 | 10 doors held in the engine's door schedule, no BOQ line (F4) |
| WINDOWS | 27 / 29 (93.10 %) | 0 / 29 | 27 / 29 | 0 / 29 | W18, W03 MISSING (F5) |
| levels (FFL per storey) | GF / 1F / 2F AGREED across sheets, ANNEX single sheet | | same | | no CONFLICT (F7) |
| all other principal trades | NO_INDEPENDENT_INVENTORY or NOT_MEASURED (next source in SUMMARY_*.json `next_source`) | | | | |

Verified share 0 / d everywhere: no COUNTED verdict exists in a structured file for these elements (the Checker's
column re-measures are board text; T-235 needs them in research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json). No
accuracy figure is written (accuracy table compared 0 / 0 in this run; the scoreboard owns it).

## 4. Findings in engineering terms (each for the Checker; nothing changed)

- **F1 footing identity (both runs).** Outline 1B1B (tags F and F10, T-233 HELD 2.176 .. 2.275 m3, one outline two
  types) has no engine line by label; the engine carries one footing with no printed type,
  `P-C:FTG:SH10:T652:10A5`, PROVISIONAL 1.960 m3 (own range 0.216 .. 1.960, FOOTING_LABEL_CONFLICT, schedule F
  0.90 x 0.80 x 0.30). Count: 26 drawn = 25 typed engine lines + this one, so EXISTENCE agrees; the IDENTITY does not
  (handle 10A5 is not a T-233 outline). If it is the same footing, the candidate's 1.960 m3 lies 0.216 m3 (-9.9 %)
  below the low end of T-233's range; T-233 merged after V3.0.8 and is not yet integrated. Verdict proposal:
  UNRESOLVED (identity), integration via the next lane I package.
- **F2 columns on a storey whose slab plan does not draw them.** Released V2.9 releases 1F C3 x1, 2F C3 x2, 2F C5 x1,
  2F C8 x1 = 4 x 0.420 + 0.588 = **2.268 m3** PROVISIONAL on members for which T-217 has no DRAWN row on that storey's
  roof-slab plan (the exact join leaves them unmatched). V3.0.8 holds all five (BLOCKED_RFI, T-220 existence holds; its own held_total_info 2.268 m3):
  the independent check reproduces the candidate's fix exactly. Verdict proposal: ENGINE_RIGHT for V3.0.8, released
  V2.9 over-measures 2.268 m3.
- **F3 five column lines with storey UNKNOWN** (`U-C:COL:SH12:CN`, 2 BLOCKED_RFI + 3 BOUNDED 0.378 .. 1.161 m3 each) in
  both runs: no inventory storey to judge them against; T-217 prints CN only as six FOUNDATION necks. Listed
  OUT_OF_INVENTORY_SCOPE, never counted.
- **F4 doors.** 27 drawn doors, 17 door lines in both runs; the other 10 sit in the engine's DOOR_SCHEDULE.json as
  PROVISIONAL_NOT_RELEASED (5 CONFIRMED by geometry but class not released or CLASS_UNRESOLVED / CLASS_REVIEW, 5
  PROVISIONAL), with no BOQ line. Reported HELD with that reason (an engine hold outside the BOQ); without the schedule
  they would be MISSING. The BOQ therefore prices 17 of 27 door assemblies (-10 pcs vs the drawing).
- **F5 windows W18 (1F, 0.50 x 2.16 = 1.080 m2) and W03 (GF, 6.57 x 4.30 = 28.251 m2)** have no window line in either
  run (T-198: DRAWING-CONFIRMED, no engine element): 2 pcs and 29.331 m2 of window area absent from both BOQs.
  Verdict proposal: drawing right, engine omission (released and candidate).
- **F6 skirting deductions do not reconcile (9 FIN.SKIRTING lines, both runs).** gross - listed deductions exceeds the
  net by exactly each line's `window_threshold` input: 3.916 + 1.955 + 0.300 + 0.500 (GF) + 2.652 + 1.225 + 1.645 +
  0.776 (1F) + 0.600 (2F) = **13.569 lm**. Cause: the sill-window threshold length is left out of the net ("skirted
  under one reading and not under the other ... a separate range line") but not listed as a deduction, so the line's
  own record cannot be re-derived. Quantity not judged; traceability defect: the reading-dependent length belongs in the
  deduction list (or the net). The other 75 (V2.9) / 77 (V3.0.8) gross / deduction / net lines reconcile within 0.001.
- **F7 storey datums.** FFL GF +1.00 (P7757 LEVEL, ST SH08, section A-A), 1F +5.50, 2F +9.70 (P7757 and ST SH02) agree
  on every sheet that prints them (T-206 r2 datums); ANNEX +0.30 is read from one print in the adapter. Probe 6 finds
  no sheet-to-sheet conflict on this villa.

## 5. Limits and residual risk

- The footing join is a mark count: it says how many of a type are missing, not which outline.
- T-198 was seeded from the engine's opening list and corrected by drawing reads (three openings added): an opening
  that BOTH missed is not excluded. Doors / windows completeness is against that census, not a fresh tag read.
- Beams, slabs, ground beams, straps, masonry, finishes, stairs, railings, rebar: no merged independent inventory on
  the working head (T-229 binds route G bands, so it is engine-derived and not used; T-234 and T-017 are READY, not
  merged). Their rows are present with the next source named; nothing there is called complete.

## 6. Lessons register row (ERS s.7, proposed)

| 2026-10-23 | 5 released column lines (2.268 m3) on storeys whose plan draws no member, 2 drawn windows (29.331 m2) and a footing identity were invisible to every existing check | The crosswalk and the census took their elements from the engine's own register, so an element the engine never produced, or produced where nothing is drawn, could not appear as a gap | Completeness is measured against an inventory built WITHOUT the engine (printed schedules, plan tags, outlines by handle, censuses), joined to the BOQ by an exact key where one exists (a solved, verified plan translation or a printed handle) and by a stated count join otherwise; completeness, verified share and accuracy are three tables, never one figure (every villa, every principal trade) | tests/t236_trade_completeness (probes 1b / 2 / 3 / 6 / 9 strict-xfail history; synthetic villa with every injection; metamorphic) | PROPOSED (T-236) |
