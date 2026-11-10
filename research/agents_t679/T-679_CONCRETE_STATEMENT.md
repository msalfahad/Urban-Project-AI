# T-679 Concrete reconciliation statement (12-13 Nov milestone input)

Worker 3, 2026-11-10, run session_01E6cPneEVyLaHV4SdLm7viQ, branch `agents/task-T-679`. Research only: no engine
module, candidate line, rule or knowledge file changed; nothing released; no new measurement; no reference value used
as a quantity. Development villa, not an accuracy claim. Rule R-T679-1 1.0.0 (`t679_rules.py`).

## 0. Sources and run

- Candidate of record at claim: ARCH_TAKEOFF_V3.0.65, `research/agents_t671/out/LINE_INDEX_V3_0_65.json` (sha256
  e1887c34..., lines 38af7909). T-677 (V3.0.66) was READY, not merged: the tool takes `--index` / `--master` and
  re-runs on V3.0.66 once it merges (with the master version built on that index; the census check refuses a master
  built on another index).
- Family census: `rules/coverage/BOQ_FAMILY_MASTER_1.66.0.json` candidate census (built on the same index sha): the
  statement asserts lines, released n and m3, held n, bounded low / high, blank n, excluded n and verified n equal,
  family by family (14 concrete families).
- Held causes: latest merged census per line: T-678 (V3.0.65; 22 lintels, outline 778 line, annex C3) > T-673
  (V3.0.64; lintels and stairs) > T-669 (V3.0.63; B10). Two V3.0.65 HELD lines are in no census (added after V3.0.63,
  not lintel / stair): classed from their merged package text, listed in `held_cause_supplement` (F-T679-1).
- Reference: key map `tests/alsenan/T001B_KEY_MAP.json` (8 concrete keys) and the cover totals of
  `tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json`. Causes: merged scorecard V12 (T-635) sections, quoted.
- `python3 -I research/agents_t679/t679_alsenan.py --write` -> `out/T679_STATEMENT.json` + `out/T679_STATEMENT.md`
  (`--check` rebuilds and compares).

## 1. Engine side (V3.0.65, m3; released, bounded and blank never summed together)

Trade total STR.CONC, 596 lines: **released 317 lines 291.473824 m3**; HELD bounded 84 lines 41.084313 .. 64.696779;
HELD blank 105 lines (DESIGNER ITEM 63, OPEN BOUND 14, MEASURABLE NOW 28); EXCLUDED 90 (NOT_APPLICABLE_WITH_EVIDENCE /
EXCLUDED_WITH_REASON, the index does not split them). Engine range 332.558137 .. OPEN. Verified: 62 VERIFIED_WHOLE
lines 60.280155 m3 (all B10-08 slabs) and 1 VERIFIED_COMPONENT 1.746943 m3 (B10-04), of 506 non-excluded lines.
Per-family table: `out/T679_STATEMENT.md`. Every subtotal re-adds to the line index exactly (Decimal of the stored
repr; families = item codes = lines, tested).

MEASURABLE NOW still HELD: 29 lines = 28 blank (25 lintels: the 16 T-673 MEASURABLE NOW lintels that T-677 wires in
V3.0.66 and the 9 T-678 REQUIRED lintels; the T-678 778 and C3 column lines; 1 T-673 stair part) + 1 bounded (the
boundary band 5.6392 .. 11.0328, already wired by T-668: its T-669 class is as of V3.0.63) = wiring only (lane I).

## 2. Reference comparison, apart (difference = reference - engine RELEASED; % only with no HELD line in the key)

| Key | Ref m3 | Released m3 | Range m3 | Held b + blank | Ref - rel | % | Causes (merged) |
|---|---|---|---|---|---|---|---|
| CONC.BLINDING | 47.055 | 12.734438 | 20.374812 .. OPEN | 5 + 2 | 34.320562 | - | T-551: HELD 34.320562 |
| CONC.FOOTING | 77.6305 | 67.6945 | 75.5392 .. 81.6556 | 4 + 0 | 9.936 | - | T-551: ENGINE_RIGHT -0.628, HELD 10.564 |
| CONC.GROUND | 75.09 | 45.399013 | 46.572423 .. OPEN | 9 + 20 | 29.690987 | - | none merged: UNRESOLVED |
| CONC.COLUMN | 39.7515 | 19.7765 | 38.2191 .. OPEN | 52 + 13 | 19.975 | - | T-551 columns / necks / lift walls (see out) |
| CONC.BEAM | 65.965875 | 66.920678 | 72.903907 .. OPEN | 14 + 12 | -0.954803 | - | T-545 (own ref 66.093875) |
| CONC.SLAB | 59.8174 | 60.280155 | closed | 0 + 0 | -0.462755 | -0.77 | none merged: UNRESOLVED |
| CONC.STAIR_DOME | 21.8328 | 10.450243 | 10.450243 .. OPEN | 0 + 6 | 11.382557 | - | none merged: UNRESOLVED |
| CONC.POOL | 12.348 | 7.202297 | 7.202297 .. OPEN | 0 + 1 | 5.145703 | - | none merged: UNRESOLVED |

Not keyed (no reference row): STR.CONC.LINTEL, PARAPET, LIFT, BOUNDARY_PAD. The slab key is the only one with every
line released and VERIFIED (62 / 62): reference - engine = -0.462755 m3 (-0.77 %), no merged section names its cause
(UNRESOLVED, not classed here).

## 3. Findings (for the Checker / Lead)

- F-T679-1: two HELD lines have no census row (pool blinding L-893c3db1, T-667 / T-668 lower-only >= 0.915529, C4 / C6
  designer items; BAND0030.2 depth companion L-bef35462 0 .. 0.025, T-642 B4 vs B7 depth, no mark printed): classed
  DESIGNER ITEM here from the merged text; a census row should own them (next concrete census).
- F-T679-2: the CONC.COLUMN reference 'total walls and columns' 39.7515 = 28.5465 columns + 8.805 necks + 2.4 lift walls
  (T-551 sections), but the key map's engine side holds only NECK + COLUMN, not STR.CONC.LIFT (2 lines, HELD blank):
  not like for like by scope; shown beside; the key map is not changed (a key map version is a Lead / lane I decision).
- F-T679-3: the beam cover total 65.965875 differs from the T-545 section reference 66.093875 (0.128 m3): the merged
  beam class split is quoted against its own reference, not the cover total.
- Causes for GROUND, SLAB, STAIR_DOME and POOL: no merged reconciliation section exists (scorecard V12); these four keys
  have no who-is-right verdict yet.

## 4. Rule, tests, lessons

R-T679-1 (a) - (f) in `t679_rules.py`; tests `tests/t679_concrete_statement` (villa V679 by hand: normal, blank never 0,
% suppressed beside HELD, 8 refusals, double owner, code in two keys, order invariance, exact Decimal; development
villa: committed outputs reproduce, subtotals = line index to the last digit, every HELD line has a cause, counts =
master census, % rule). Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | a statement must state its key-map scope: a
reference cover total can carry a scope (lift walls) that the engine key omits | key map / statement | name the
scope gap beside the key, never fold it | R-T679-1 (e), F-T679-2 |.
