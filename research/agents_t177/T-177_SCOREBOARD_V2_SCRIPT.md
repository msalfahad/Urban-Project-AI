# T-177: SCOREBOARD v2 columns by script (worker 3, 2026-10-22)

Tools only, no quantity change, no released-default change. Development reference only: no product accuracy claim.

## What it is

`tools/scoreboard_v2.py` (new; nothing in `engine/` imports it) builds the SCOREBOARD v2 table of the owner session
2026-10-22 07:30 (T-132) with exactly the columns

`| Trade | Unit | Baseline | Ref lines | Coverage % | Compared | WAPE % | Signed % | Verified share % | Held or UNKNOWN | Rule difference share % |`

from the same inputs as `tools/alsenan_keymap.py` (one engine run + the normalised freelancer rows + the key map) plus a
checker verdict file. Coverage / Compared / WAPE / Signed are `tools/alsenan_scoreboard.py score` unchanged. The three
columns the checker filled by hand at 08:15 are now computed (definitions in the module docstring; one test each in
`tests/t177_scoreboard_v2/`):

- **Held or UNKNOWN**: per HELD reference line, the same-unit engine lines answering it that are not released, split
  into complete `bounded_range` lines (summed low .. high in the line's unit) and lines without a complete bound
  (UNKNOWN, never 0; a bound with only one end is UNKNOWN); CONDITIONAL review sets counted apart (UNKNOWN); lines
  excluded with evidence counted apart; unit-refused or silent lines give NOT YET MEASURED with the reason. Released
  lines inside a held reference line are in the JSON (`released_part_lines`, `released_part_qty`), never compared.
- **Verified share**: whole-scope checker re-measures from the drawing of THIS run's compared quantity only. A
  re-measure on another engine quantity (STALE), on a held line, in another unit, or more than 1 % from the engine
  (DISCREPANCY, WORKFLOW_CONTROLS s.1) is listed in `verdict_audit` and not counted. A "freelancer agreement" method is
  refused outright; partial re-measures are listed and never counted.
- **Rule difference share**: whole-scope standing RULE_DIFFERENCE verdicts / reference lines; NOT YET MEASURED while
  the bucket has no whole-scope rule assessment (RULE_DIFFERENCE or NO_RULE_DIFFERENCE).
- **Baseline cell**: the label given, plus `manifest <sha8>, BOQ_LINES.csv <sha8>` from a `BASELINE_MANIFEST.json`
  (tools/release_baseline.py), after checking that the scored BOQ_LINES.json has the sha256 the manifest records
  (refused otherwise); for a candidate, the sha8 of its lines file and of the sibling CSV.
- **Candidate**: `--v2-candidate-lines V3_0_x_BOQ_LINES.json` scores the candidate beside the base run's release report
  (no symlinked run folder needed); rows are grouped by trade and unit, one per side.

## How the checker runs it (through the pre-approved wrapper)

Paths are relative to the tree (`--tree T`); outputs go to a scratch folder.

```
bash scripts/agent_env.sh run tools/alsenan_keymap.py --run <RUN_A> \
  --reference tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json --key-map tests/alsenan/T001B_KEY_MAP.json \
  --out <scratch>/A_v1.json --v2-out <scratch>/A_v2.json --v2-markdown <scratch>/A_v2.md \
  --v2-label "A (released V29_ROUTEG_NO_PROFILE)" --v2-verdicts research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json \
  [--v2-candidate-lines <CAND_RUN>/v303/V3_0_3_BOQ_LINES.json --v2-candidate-label "ARCH_TAKEOFF_V3.0.3 (candidate)"] \
  [--v2-heading "<UTC date time>"]
```

Without `--v2-out` the key-map tool is byte-identical to before (test). `python3 -I tools/scoreboard_v2.py` takes the
same inputs directly.

**Verdict file** (`URBAN_SCOREBOARD_CHECKER_VERDICTS_V1`): `research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json`
was seeded ONLY from merged checker notes in SCOREBOARD.md, each cited by note heading and board commit: blinding
RULE_DIFFERENCE (whole), partial re-measures (blinding released part 15.179 vs hand 15.213 m3, columns above necks
34.446 m3, main stair 4.920 m3) and partial rule differences (plaster / paint 4 rooms, wet floor). The Checker owns it
from here: a whole-scope re-measure needs `unit`, `engine_qty` (the run's quantity it re-measured), `checker_qty`,
`method: CHECKER_REMEASURE_FROM_DRAWING`, `source` and `commit`.

## Reproduction of the 2026-10-22 08:15 rows (own runs of the Drive DXFs this run)

Inputs: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55), ST7757 dxf.dxf (9f9d1179).
Baseline A: `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` on engine
554c1c4: REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4 (manifest file 461ae7f7 here: the manifest records the engine
commit; the checker's 58521e21 was written on 37124da). Candidate: `research/agents_t151/v303_run.py` + route G profile:
V3_0_3_BOQ_LINES.csv 5ba4ae93 (= the checker's), scored beside its own base run B's release report.

| Row | Checker 08:15 (by hand) | Script | Same? |
|---|---|---|---|
| Concrete m3, A | 8 / 100.00 / 3 / 17.03 / -17.03; 0.00 (0/8); 5 held, 205 lines: 122 bounded 44.108 .. 113.540 + 83 UNKNOWN; 12.50 (1/8) | identical (+ "3 partial re-measures not counted") | yes |
| Concrete m3, V3.0.3 | 3 / 15.38 / -13.04; 5 held, 43 lines: 40 bounded 19.725 .. 36.465 + 3 UNKNOWN; 12.50 | identical (+ "5 more excluded with reason") | yes |
| Plaster m2, A / V3.0.3 | 29 lines: 2 bounded 2.360 .. 2.600 + 27 UNKNOWN / 32 lines: 2 + 30 | identical; rule share NOT YET MEASURED (1 partial) | yes |
| Paint m2, A / V3.0.3 | 13 UNKNOWN (14 excluded) / 13 UNKNOWN | identical; V3.0.3 also "17 more excluded with reason" | yes (more detail) |
| Floor area m2, A | held by 3 conditional sets, UNKNOWN | identical | yes |
| Floor area m2, V3.0.3 | 1 line bounded 38.459 .. 38.979 | 1 bounded 38.459 .. 38.979 **+ 3 conditional review sets UNKNOWN** | finding 1 |
| Doors / Windows m2 | NOT YET MEASURED (unit refused, pcs) | identical text cause | yes |
| Concrete m3, run B (comparison base) | note: compared 5, 18.17 / -17.16 | 5 / 18.17 / -17.16 | yes |

## Findings

1. **Candidate floor area**: the V3.0.3 lines carry one bounded floor line (38.459 .. 38.979 m2; 46 released floor
   lines 340.765 m2 against base B's 44 lines 376.286 m2), but the candidate has no release report of its own, so the
   base run's 3 CONDITIONAL wet / dry review sets still hold the key when it is scored beside that report (the
   checker's 08:15 cell names only the bounded line). Either way the reference line stays HELD (no quantity changes);
   whether the bounded line and the review sets are the same spaces is for the integration of the floor piece to
   state (V3.0.x run report), not for the scorer to guess. Lane I follow-up: a V3.0.x candidate should emit its own
   CONDITIONAL set list (or state "none") so the scorer does not borrow the base run's.
2. Excluded-with-evidence lines are now reported in every held cell (V3.0.3 concrete 5, paint 17): context, never a
   quantity.
3. Verified share is 0 / n in every bucket: no whole-scope checker re-measure of a compared reference line exists yet
   (T-180 is the checker task that can change this; each whole re-measure must cite the run quantity it checked).

## Limits

The key map, the reference rows and the verdict file are project inputs (the development villa's are committed); the
scorer itself is general. No second drawn villa. T-182 (five separate measures) and T-181 (doors / windows pcs and m2)
build on this table and are not done here.
