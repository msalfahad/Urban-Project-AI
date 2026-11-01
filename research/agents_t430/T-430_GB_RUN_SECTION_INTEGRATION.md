# T-430 integration package: ground-beam section per run and neck cut (T-426 + T-416) into ARCH_TAKEOFF_V3.0.40

Worker 3 (lane I), 2026-11-01, branch `agents/task-T-430`. **Integration package for Checker Gate B.** Integrates:
T-426 (MERGED 1f298735, Gate A PASS 11:59: printed section per run, F-1 answered, F-T426-1 accepted) and T-416 (MERGED
b7bb914a, Gate A PASS 07:54 with finding F-C-T416-1: exact cuts). Candidate of record before: ARCH_TAKEOFF_V3.0.39
(json `8d1bbe5d`, T-429 Gate B, merge a2a2e080). NOT RELEASED; the released default V2.9 + route G is unchanged;
rollback = V3.0.39 / V2.9. Development villa (Alsenan), not an accuracy claim; the method (R-T430-1) is for every
villa. Drawings are cited by Drive folder and title only.

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`), 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t430/v3040_run.py` (Python 3.11.18): **V3_0_36 `d462203f`, V3_0_37 `733f2efb`, V3_0_38 `57cca61c` and
V3_0_39 `8d1bbe5d` reproduced** (the T-246 / T-420 / T-421 / T-429 Gate B figures), **V3_0_40_BOQ_LINES.json
`aa6aa927`** written beside them (4,831 lines; `summary_t430.json`, built by `t430_summary.py` from that run). Inputs:
`research/agents_t430/t430_inputs.py` reads ONLY the merged files, each pinned by sha256 (CENSUS_T426.json `b297bb14`,
summary_t416.json `37934957`); typed there: the neck length 0.300 m (the Checker's own exact cut, F-C-T416-1), which
lines are split / held (the T-426 Gate A verdict) and the causes' wording.

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t430/v3040_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t430 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t430/t430_summary.py <private>/t430/v3040 --write
```

## 1. The physical element and who owns it (ERS s.2.1)

A ground-beam RUN is b x D x L of its own concrete between the faces of what supports it (founded neck / column, ring,
the face of the band it ends against). Its section is what the drawings print for THAT run (ST p.13 titles by the run's
own clear span: '> 5 m' 30 x 60, '< 5 m' 30 x 40, both 'without concentrated load'; '< 2.5 m' 30 x 30 with no load
qualifier). A founded neck (CN on FN, T-205 ledger) that a band crosses is a support: it splits the band into runs and
owns the joint (R-CONC-OWN-1). A beam landing on a run is a concentrated load (D-33): the printed title then does not
describe the run.

Owner trade: B10-04 STR.CONC.GROUND_BEAM for every line here (the neck joint stays with the CN neck lines, which are
bounds / BLOCKED_RFI in the candidate and are not touched; no cross-trade move).

## 2. What the package does, per line (ERS s.2.2: owner manual method and drawing-derived method side by side)

| | Owner manual method | Drawing-derived method (merged ledgers) |
|---|---|---|
| GB run m3 | b x D x L between the faces of its supports, member by member (Q-61 C); D = the printed section of that member | runs between founded necks / columns read per frame (T-416 band read, exact cuts F-C-T416-1); title per run from its own span (T-426) |
| Loaded run | the printed section does not cover a concentrated load: designer / consultant (D-33) | HELD, unloaded printed figure .. candidate's own depth beside |
| Two titles hold | no rule picks one (D-34 / reading) | HELD with the printed range beside |
| No printed section | nothing to measure | HELD blank |

Actions (`V3_0_40_INTEGRATION_LEDGER.csv`): SPLIT_VALUED (same id, the unloaded run at its printed section,
SOURCE_DERIVED), SPLIT_HELD (an ADDED line `<element>:<run>`, BLOCKED_RFI blank, range beside), HOLD_RANGE / HOLD_BLANK
(same id, BLOCKED_RFI blank).

| Line | Run / element | Action | V2.9 | V3.0.39 | V3.0.40 | Evidence status | Beside (m3) / cause |
|---|---|---|---|---|---|---|---|
| L-fe78ae283abfb6256358 | 7DC+7DD#2 (BAND0023) | SPLIT_VALUED | 1.323 PROVISIONAL | 1.323 | **0.423** SOURCE_DERIVED | VERIFIED (T-426 Checker hand) | - |
| L-95a1f198cfe7f398d6ae (ADDED) | 7DC+7DD#1 (BAND0023:7DC+7DD#1) | SPLIT_HELD | not in V2.9 | - | HELD blank | HELD | 0.4230 .. 0.6435; D-33 (7E1+7E2 lands) |
| L-0e30aadba2eebc6c3ede | 7E7+7E8#1 (BAND0032) | SPLIT_VALUED | 1.323 PROVISIONAL | 1.323 | **0.423** SOURCE_DERIVED | VERIFIED (T-426 Checker hand) | - |
| L-cfb4555cb26b39934bff (ADDED) | 7E7+7E8#2 (BAND0032:7E7+7E8#2) | SPLIT_HELD | not in V2.9 | - | HELD blank | HELD | 0.4230 .. 0.6345; D-33 (114+115+7DF land) |
| L-e24946df436cbc25fca6 | 177+7CD#1 (BAND0008.1) | HOLD_RANGE | 0.9036 PROVISIONAL | 0.9036 | HELD blank | HELD | 0.5964 .. 0.9036; reading 4.97 / 5.02 + D-33 |
| L-be6708e07b40efa02779 | annex arc sliver (BAND0013.1) | HOLD_BLANK | 0.009 PROVISIONAL | 0.009 | HELD blank | HELD | none (no printed section, D-35) |

Arithmetic (by hand, from the T-426 census spans and the Checker's own re-measure):
- 7DC+7DD (band 7.350 = run #1 3.525 GBP / 3.575 FP-CAP + neck 7F5 0.300 + run #2 3.525): run #2 nothing lands ->
  0.30 x 0.40 x 3.525 = **0.4230** (VERIFIED, Checker T-426 own hand); run #1 7E1+7E2 lands (D-33) -> HELD beside
  0.30 x 0.40 x 3.525 = 0.4230 .. 0.30 x 0.60 x 3.575 = 0.6435.
- 7E7+7E8 (7.350 = 3.525 + neck 7ED 0.300 + 3.525, every frame): run #1 nothing lands -> **0.4230** (VERIFIED); run #2
  114 / 7DF land -> HELD beside 0.4230 .. 0.30 x 0.60 x 3.525 = 0.6345.
- 177+7CD#1: 5.020 (band end) or 4.970 (face of column 1EC) by reading -> '> 5 m' 30 x 60 or '< 5 m' 30 x 40; 175+7DE,
  176+7E6 and 7DC+7DD land on it (D-33): HELD, beside 0.30 x 0.40 x 4.97 = 0.5964 .. 0.30 x 0.60 x 5.02 = 0.9036 (the
  candidate's value is the high end: a picked end).
- annex-arc sliver BAND0013.1 0.10 m (0.009 at 0.30): no printed section (D-35 annex CONFLICT): HELD blank.

## 3. Reconciliation in units (ERS s.2.4)

GB valued (STR.CONC.GROUND_BEAM, V3.0.39 -> V3.0.40): 47 valued lines 29.569286 m3 -> 45 valued lines **26.856686 m3** (-2.712600 m3, -9.17 %); lines 59 -> 61 (2
added), blocked 12 -> 16; HELD beside the new holds 1.4424 .. 2.1816 m3 (runs 0.846 .. 1.278, 177+7CD#1 0.5964 ..
0.9036) plus the sliver blank.

Per cause, m3 (sum = -2.712600):
- section ENGINE_WRONG on the two unloaded runs: 2 x 0.30 x (0.60 - 0.40) x 3.525 = **-0.423000** (T-426 VERIFIED);
- neck length ENGINE_WRONG (T-416, exact cut F-C-T416-1): 2 x 0.30 x 0.60 x 0.300 = **-0.108000**;
- loaded runs moved from valued to HELD (their candidate share 0.30 x 0.60 x 3.525 each): **-1.269000** (HELD
  0.846 .. 1.278 beside, never 0);
- 177+7CD#1 moved to HELD: **-0.903600** (beside 0.5964 .. 0.9036);
- sliver moved to HELD: **-0.009000** (blank).
Check: -0.423 - 0.108 - 1.269 - 0.9036 - 0.009 = -2.7126. The row's -1.800 (T-426 s.6) is the first three terms
exactly; the other -0.9126 are the two holds the same row names (177+7CD#1, L-be6708e0).

Downgrade-only proposal (F-T426-1, never a promotion; the Checker issues or refuses): `DOWNGRADE_PROPOSAL_T430.json`
`DGP-T430-GB-D34-SHORT` names the 4 short-run lines L-0bb78acc / L-0e852cca / L-1487bdda / L-c0b7102a (valued at the 0.40
end of the unanswered D-34 pair, 1.152231 m3) bound by LINE_CONTENT_V1 to their V3.0.40 content (unchanged from
V3.0.39), audit range 0.864171 .. 1.152231 m3. No EXCLUDED row and no other line is named (F-T245-01). The candidate
line file keeps them valued, exactly as it keeps the 9 lines DG-a31a0d7e holds at export.

## 4. Rule and check (R-T430-1, module docstring; every villa)

(a) a ground-beam section is read per run, never from the band or the neighbour; (b) the runs and the necks of a split
band add up to the candidate band length exactly (no length lost, none borrowed; refused otherwise); (c) a run is valued
only on ONE printed title, ONE span on every frame and no load on it; (d) a picked end of a printed range is HELD, not a
value; (e) held is blank with its figure(s) beside, never 0. `check_runs()` runs on the integrated lines (valued run =
b x printed D x run length; spans equal on every frame; held blank with its reason and a positive range; no run carried
twice per band).

## 5. Diffs and regression

- vs V3.0.39: **4,829 -> 4,831 lines; 2 ADDED, 4 CHANGED (all named in section 2), 4,825 byte-identical** (asserted
  in `integrate()` and `write()`; outside-rows sha256 `b385d886aca2df14..` in the run identity). Totals moved only in
  STR.CONC.GROUND_BEAM m3 (asserted): valued 29.569286 -> 26.856686, blocked lines 12 -> 16; every other code total
  identical (`summary_t430.json` `code_totals_other_than_gb_identical: true`).
- vs released V2.9 + route G: the 4 changed lines exist in V2.9 at their V3.0.39 figures (PROVISIONAL); they now differ
  (QUANTITY_DIFFERS); the 2 added run lines are NOT_IN_RELEASED. Whole file: {'NOT_IN_RELEASED': 3241,
  'QUANTITY_DIFFERS': 980, 'SAME_QUANTITY': 610} (V3.0.39: 3239 / 976 / 614).
- Older chain guards: every V3.0.14 .. V3.0.39 guard (`_family_guards`, roof, ceilings, corrections, zones, fence, lists,
  beds, lift, landing, flights) runs unchanged on the V3.0.40 lines and passes; `check_runs()` (new): 2 valued runs
  0.846 m3, 2 held runs, 2 held lines, bands 7DC+7DD / 7E7+7E8 each run once.
- T-330 deductions check (`tools/t330_deductions_check.py`, unchanged): V3.0.39 4,829 lines 6 FLAG / 0 REFUSED ->
  V3.0.40 4,831 lines the same 6 / 0: no new finding.
- Export (`tools/boq_export_v1.py`, unchanged, with V3.0.29/DOWNGRADES.json) on V3.0.40: 4,831 rows; the two valued runs
  MEASURED UNVERIFIED 0.423; the two added runs, 177+7CD#1 and the sliver HELD with the reason, blank; nothing shown as
  0; the 4 D-34 short lines still exported as valued (the proposal is not a record until the Checker issues it).
- Tests: `tests/t430_gb_run_section_integration` (hand villa K430, not Alsenan: 31 method tests incl. 2 development-villa
  pins + 6 registry tests); L3: the 36 test folders `impact` lists for tools/urban_boq_m9.py plus t130 / t246 / t416 /
  t421 / t426 / t429 / t430 pass to 100 % (0 FAILED / ERROR; skips = private inputs absent, 1 xfail pre-existing);
  freeze 0; codemap stale none; rules manifest drift none; registry 1.35.0 equals its builder, FMC problems none.
- Coverage registry: `rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json` (new version file; 1.34.0 untouched) = 1.34.0 + the
  pending V3.0.40 package (B10-04: evidence, opt-in reader, missing text; no owner, capability or candidate state
  change).

## 6. Downstream BOQ impacts

- STR.FORMWORK: 9 ground-beam formwork lines name the changed lines (FW:<line id>:FACES / :OQ10, FW:FACE:R4-147 for
  the sliver); all are BLOCKED_RFI (OQ10: formed or earth-cast faces) with no figure: no quantity moves. When OQ10 is
  answered they must follow the run split (faces per run; the 2 x 0.300 m neck faces are the neck's, not the beam's).
- Reinforcement: no ground-beam rebar line exists in the candidate (the route G STR.REBAR lines named BAND0032 are 1F /
  GF BEAMS, a different element with the same band index): nothing to follow.
- Blinding / waterproofing of buried concrete: T-445 / T-263 own them; none reads these line values today.
- CN neck lines (6, BOUNDED_EXPOSURE / BLOCKED_RFI): own the 0.300 m joint (0.054 m3 per band at 0.60, 0.036 at the
  printed 0.40); unchanged here; no double count once they are valued.
- Concrete roll-up (T-428 / T-433): the valued ground-beam term falls by 2.7126 m3 and the held term gains the two runs,
  177+7CD#1 and the sliver; the T-433 blocker split should restate D-33 (+2 runs, +177+7CD#1) and D-35 (+sliver) on the
  next roll-up.

## 7. Missing / held (never 0)

- 7DC+7DD#1 and 7E7+7E8#2: HELD on D-33 (consultant: a loaded run's section is not printed), beside 0.4230 .. 0.6435 /
  0.4230 .. 0.6345 m3.
- 177+7CD#1: HELD on its reading range (T-141 GAP_TO_COLUMN) + D-33, beside 0.5964 .. 0.9036 m3.
- BAND0013.1 sliver: HELD blank (D-35; ownership UNRESOLVED, T-416).
- The 4 D-34 short runs stay valued in the line file until the Checker rules on DGP-T430-GB-D34-SHORT (1.152231 m3,
  audit 0.864171 .. 1.152231).
- 12 other valued lines bill a D-33 run (T-426 R-T426-5: 14 of 38 incl. the two split here); not moved: T-426 named
  them so no section on them is read as VERIFIED; no Checker verdict moves them.
- Route G still reads the 'clear 7.35 m' band through a founded neck (T-426 s.6 (4)): the defect is corrected in the
  candidate lines here; the route itself is a later engine task.

## 8. Engine vs freelancer (quantities only; T-391 / T-426 s.5; workbooks not re-opened)

| Term (GB-MAIN, engine - freelancer, m3) | V3.0.39 | V3.0.40 | Verdict proposal |
|---|---|---|---|
| section, interior 0.40 runs | -3.443815 | -3.866815 (the two unloaded runs join it) | ENGINE_RIGHT at the printed 0.40 (both were at 0.60 before: engine and freelancer WRONG there, Checker T-426) |
| interior 0.60 runs | 0.000 "AGREE" (4 lines) | 7E1+7E2 only (6.72 m, '> 5 m', AGREE) | the "agreement" on 7DC+7DD / 7E7+7E8 was both above the drawing |
| length (necks) | includes +0.108 | -0.108 removed | ENGINE_WRONG fixed (T-416) |
| held | -9.690354 | more held: 2 loaded runs + 177+7CD#1 + sliver | UNRESOLVED (D-33 / D-35 / reading), never 0 |
| headline | -10.354614 | engine valued side -2.7126 lower | the freelancer's per-run section is not recoverable (one section, two lumps): restated on the engine side only |

## 9. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | wiring a verified per-run section into a band line could have kept the loaded half valued at the band's 0.60, kept the 0.30 m neck inside the beam, or valued the run on one frame while the other frame gives another length | the candidate line is per BAND; the verified evidence is per RUN; route G does not see a founded neck as a support | a band crossed by a founded neck is billed per run: runs + necks = band exactly; a run is valued only on one title, one span on every frame and no load; otherwise HELD with its range beside (any villa) | tests/t430_gb_run_section_integration (normal: K430 hand figures, neck owns the joint, held blank with range or nothing beside, check_runs summary, outside lines byte-identical, only GB totals move, input order invariance, files; adverse: a founded neck ignored (one span through it), split without neck, unfounded neck, length lost / borrowed, held run without range, range 0, mm as m, frames differ, two titles, stale candidate, census vs candidate, range not containing the value, blank with range, line named twice, wrong code, unknown source, applied twice, change outside the code, held line valued, run carried twice, schema / project) | proposed |

## 10. Gate B hand-check list (always by hand)

1. Every moved line (all are B10-04 structural, all moved >= 5 %): L-fe78ae28 0.4230 (7DC+7DD#2: 7F5 -> 177 face 3.525
   on GBP / FP / CAP, nothing lands); its ADDED run #1 line HELD (24D face -> 7F5 3.525 GBP / 3.575 FP-CAP, 7E1+7E2
   lands at 2.772 .. 3.072); L-0e30aadb 0.4230 (7E7+7E8#1: 7CF face -> 7ED 3.525); its ADDED run #2 HELD (114 / 7DF land
   at 5.800 .. 6.100); necks 7F5 / 7ED 0.300 x 0.300 on 'ST7757 dxf.dxf'; p.13 titles on ST7757.pdf.
2. Holds: L-e24946df (5.020 / 4.970, column 1EC 0.050 beside the band face) and L-be6708e0 (no printed section).
3. Totals: section 3 arithmetic; the 4 new / changed rows' figures in the ledger.
4. The proposal DGP-T430-GB-D34-SHORT: 4 line ids, LINE_CONTENT_V1 hash, audit range (validate or refuse).
5. Random lines: Checker's own selection (WORKFLOW_CONTROLS s.1.2) from the remaining lines.
