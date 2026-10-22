# T-165: one pinned definition of "released V2.9 + route G" (development villa check)

Worker 3, 2026-10-22. No quantity changed, no released default changed, no method touched. The Lead rules which of the
two pinned runs is THE released baseline (this task gives the evidence; it does not pick one).

## What was built

| File | What |
|---|---|
| `tools/release_baseline.py` | NEW runner, imported by nothing (rollback: delete). `run SPEC --plan --structural --out`: refuses (exit 2, nothing run, nothing written) on a malformed spec, a missing pinned file, ANY sha256 difference (drawings, conventions, profile, facts), a drawing given that the spec does not pin (or the reverse), a Python major.minor other than the pinned one, or a non-empty --out. Runs `tools/urban_boq_m9.py arch` with exactly the pinned items (method, conventions, profile, facts, project id, as-of date, options) and writes `BASELINE_MANIFEST.json` beside the run: spec + spec sha, engine commit + clean / modified tree, inputs by name / size / sha, line count, evidence-state counts, sha256 of BOQ_LINES.csv / .json, MATERIAL_RESULTS.json, COVERAGE.json, and per item code AND unit: lines, released lines + quantity, held lines (no quantity; bounded low / high only where the line gives both), excluded lines. Absent figure = null, never 0. No timestamp, no path: two runs on one commit give byte-identical manifests. `compare A B`: configuration differences + every differing item code / unit + identical outputs or not. |
| `research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` | spec of run A (below), expected 1,455 lines, BOQ_LINES.csv b96185d4... |
| `research/agents_t165/baselines/V29_ROUTEG_PROFILED.json` | spec of run B (below), expected 1,621 lines, BOQ_LINES.csv 7d9ccb8a... |
| `research/agents_t165/baselines/v29_profiled_facts.json` + `make_profiled_facts.py` | run B's facts file, byte-for-byte the T-131 runner's `facts()` (repository data only; `--check` proves it) |
| `research/agents_t165/baseline_explain.py` | read-only: one profiled run per profile value with that value removed (17 runs) + the side-by-side attribution table |
| `tests/t165_release_baseline/` | 16 tests on a synthetic villa (arch_synth plan + synthetic_villa_m8 seed 21 with its printed-storey-height profile) and hand-made line lists |

## (1) Provenance: which run produced the figures the board reports as released

Both runs are on the board, under the same name.

| Where | Run | Evidence |
|---|---|---|
| PROGRESS.md row "Concrete, 3 lines compared ... 92.77 / 111.81 / -19.04 (-17.03 %)"; SCOREBOARD.md tables (concrete "compared 3, WAPE 17.03 %, signed -17.03 %") | **A, no profile** | SCOREBOARD.md (agents/control) verifier 2026-10-19 19th run: "ARCH_TAKEOFF_V2.9 + route G, conventions V6, no facts file, no profile ... 1455 lines ... Commit measured: 8774071. Concrete compared lines: engine 92.77 vs freelancer 111.81 m3"; same wording in the 11th run (b5475db, "no facts file, no route G profile") |
| BOQ_FAMILY_MASTER 1.1.0 `run_evidence.released_run` (`rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json:29`), T-130, census V2 (T-140) | **A** | "--conventions V6, no facts file: exit 0, 1455 lines, BOQ_LINES.csv sha256 b96185d4..." |
| SCOREBOARD.md notes 2026-10-21 17:45 and 2026-10-22 00:40 ("RELEASED V2.9 + route G: compared 5 / held 3, WAPE 18.17 %, signed -17.16 %") | **B, profiled** | the notes say "with the route G profile"; reproduced below exactly |
| Every V3.0.x Gate B diff (T-131 .. T-151 runners; checker T-133 / T-142 / T-156 diffs) | **B** | `research/agents_t131/alsenan_v30_run.py:54-56` refuses to run without `--profile` (Gate B defect D1, checker 2026-10-21 17:40); ELEMENT_REGISTER.md Lead 00:20: "the checker's T-156 / T-133 diffs used the PROFILED run" |

So the board currently reports two different concrete scores as "released": -17.03 % on 3 lines (A) in its tables
and PROGRESS, -17.16 % on 5 lines (B) in its latest notes. No record names either as THE released configuration:
1.1.0 `released_configuration` says only "ARCH_TAKEOFF_V2.9 + route G (conventions V6) (the scored configuration of
SCOREBOARD.md)", and the scoreboard itself used A until 2026-10-21 and B since. Status: **UNKNOWN by the records;
both pinned below**.

Owner rule that bears on the ruling (not decided here): Q-17 answered A (2026-10-19): typed drawing values may be used
only when a check (T-044) finds them printed, recorded in a controlled project data file (file, number, revision, sheet,
note, value, verification status, reviewer); a line needing an unprinted value stays held. Against that:
- run A holds lines whose values T-044 found PRINTED (storey heights, ground-beam typical sections, blinding 0.10 m);
- run B releases on the M4 profile file, which is not in the Q-17 A data-file format, and which includes the two values
  T-044 classed DIFFERENT (CB_SUPPORT_BAR_EXTENT_FRAC 0.22: the drawing also prints 0.3 Ln2) and NOT_PRINTED
  (CB_SUPPORT_BAR_SPAN_BASIS); both reach released steel (below: 36.06 kg and 27.69 kg), and FOUNDING_DEPTH_M's high
  2.00 m (not printed) bounds the held necks. Neither run is Q-17 A exactly; a third spec (profile restricted to the
  T-044 PRINTED values, as a project data file) would be the compliant one. That is the Lead's / owner's call.

## Both runs reproduced (own runs on the Drive copies, sha = SOURCE_MANIFEST)

Inputs: architectural DXF from Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (sha ab54dd55...31cc4,
17,227,946 bytes), structural "ST7757 dxf.dxf" (sha 9f9d1179...38079, 3,153,037 bytes); Python 3.11.17; head d54cfac.

| Spec | Configuration | Lines | BOQ_LINES.csv | Status |
|---|---|---|---|---|
| V29_ROUTEG_NO_PROFILE (A) | V2.9, conventions V6, no profile, no facts, no project id | 1,455 | b96185d4... (= 1.1.0) | REPRODUCED |
| V29_ROUTEG_PROFILED (B) | + profile_st7757_m4.json (f482b5be...), T-131 facts (f70170d6...), project development-villa-t131 | 1,621 | 7d9ccb8a... | REPRODUCED |

Evidence states: A released 970 (PROVISIONAL 782 + SOURCE_DERIVED 188), held 457 (BLOCKED_RFI 297, BOUNDED 160),
not applicable 28; B released 1,303 (1,115 + 188), held 290 (217 + 73), not applicable 28.

Engine vs freelancer through tools/alsenan_keymap.py (key map tests/alsenan/T001B_KEY_MAP.json), concrete m3, 8 keyed
reference lines:

| Key | Freelancer | A (no profile) | B (profiled) |
|---|---|---|---|
| footings | 77.631 | 77.265 | 77.265 |
| stairs + domes | 21.833 | 12.007 | 17.326 |
| pool | 12.348 | 3.495 | 3.495 |
| blinding | 47.055 | HELD | 22.155 |
| slabs | 59.817 | HELD (one face held) | 60.919 |
| ground (beams, slab, straps, necks) | 75.090 | HELD | HELD |
| columns | 39.752 | HELD | HELD |
| beams | 65.966 | HELD | HELD |
| compared | | 3 lines: 92.767 vs 111.811, -19.044 m3 (-17.03 %) | 5 lines: 181.161 vs 218.684, -37.523 m3 (-17.16 %) |

Both numbers on the board are therefore real and reproducible; they are different runs, not a drift.

## (3) The 8 differing figures and the cause of each

Two facts first:
- **The facts file changes nothing on V2.9.** Run B without facts and without project id (profile only) gives the same
  1,621 lines, identical in every field except `line_id` and `project`; and all 506 non-structural lines of A and B are
  identical apart from those two fields. Every quantity difference comes from the route G profile.
- **The project id changes every line id** (it enters the line-id hash). A Gate B diff of A against a V3.0.x run
  (project development-villa-t131) pairs no line by id (tools/v30_gate_b.py stage 1) and falls back to element pairing:
  the baseline must pin the project id too, and the specs do.

Cause = the profile value whose single removal from run B moves the figure (17 ablation runs + one double removal
GF_FLOOR_LEVEL_M + OUTER_GROUND_LEVEL_M, all exit 0). A difference no single removal moves is NO_SINGLE_VALUE: one
(ground slab +0.114 m3). Where several values each move part of a figure (columns: the three storey heights), A's
figure is reached only with all of them removed. T-044 class = its audit of that value on the printed sheets.

| Family | Item, unit | A: no profile | B: profiled | Caused by (removing it from B gives) | T-044 class |
|---|---|---|---|---|---|
| B10-01 blinding | STR.CONC.BLINDING m3 | 1 line HELD 7.276 .. 16.887 | 2 lines released 22.155 | BLINDING_THICKNESS_M 0.10 (both held 11.078 .. 22.155); BLINDING_UNDER footings + ground beams (1 line, 15.693: the under-beam line goes) | PRINTED (PDF p.13 only) |
| B10-06 columns | STR.CONC.COLUMN m3 | 82 lines all HELD (BLOCKED_RFI, no quantity) | 69 lines: 64 released 36.714, 5 HELD 1.134 .. 3.483 | STOREY_HEIGHT_GF 4.50 (released 32 = 15.456), _1F 4.20 (44 = 26.634), _2F 4.20 (51 = 30.918) | PRINTED |
| B10-04 ground beams | STR.CONC.GROUND_BEAM m3 | 59 lines HELD 17.801 .. 59.337 | 58 lines released 27.365 | GB_TYPICAL_SECTIONS (<2.5 m 30x30, <5 m 30x40, else 30x60): without it 58 HELD 17.459 .. 58.197 | PRINTED (PDF p.13) |
| B10-05 ground slab | STR.CONC.GROUND_SLAB m3 | 23 released 17.127 + 2 HELD 4.767 | 24 released 17.241 + 1 HELD 3.930 | two parts. (a) GF_FLOOR_LEVEL_M 1.00 / OUTER_GROUND_LEVEL_M 0.00 (each alone, and both together: 26 lines, 2 HELD 4.767): A's held 0.837 m3 ground cell becomes part of the ground stair. (b) one released cell 1.14 m2 x 0.10 m (sheet-uniform thickness convention) = +0.114 m3: present in B and in every single removal, absent in A: **NO_SINGLE_VALUE** (it needs two or more profile values together; not traced further) | PRINTED |
| B10-03 necks | STR.CONC.NECK m3 | 36 lines HELD 3.075 .. 15.375 | 28 released 10.855 + 8 HELD 0.405 .. 2.025 | FOUNDING_DEPTH_M (1.50 base / low, 2.00 high) and NECK_TOP_LEVEL_M 1.00: either removal holds all 36 again | base PRINTED as a minimum; high 2.00 NOT printed; neck top = GF level is the profile's reading |
| B10-08 slabs | STR.CONC.SLAB m3 | 76 lines: 75 released 61.551 + 1 HELD 2.740 | 75 released 60.919 | SLAB_PROJECT_DEFAULT_THICKNESS_M 0.16 (-0.632 m3 on default-thickness faces); STOREY_HEIGHT_1F (the 2.740 face leaves the slab item) | PRINTED (PDF p.8 note 18) |
| B7-12 stairs | STR.CONC.STAIR m3 | 3 lines 4.635 | 4 lines 9.954 | STOREY_HEIGHT_1F (without it 3 lines 5.504: the 1F flight's rise); GF_FLOOR_LEVEL_M / OUTER_GROUND_LEVEL_M (without either 9.086: the ground stair) | PRINTED |
| B11-01 reinforcement | STR.REBAR kg | 497 lines: 467 released 16,392.647 + 30 HELD (2 bounded 29.537 .. 32.571) | 676 lines: 646 released 23,032.514 + 30 HELD (2 bounded 29.537 .. 30.438) | the column and neck heights: STOREY_HEIGHT_GF (-60 lines, 20,143.338), _1F (-38, 21,483.830), _2F (-24, 22,247.907), FOUNDING_DEPTH_M / NECK_TOP_LEVEL_M (-56 each, 21,603.943); beam steel: CB_SUPPORT_BAR_EXTENT_FRAC (23,068.571 without), CB_SUPPORT_BAR_SPAN_BASIS (23,004.820 without), CB_BOTTOM_EXTENSION_M (23,046.136 without; the bounded high 30.438 -> 32.571) | storey heights PRINTED; CB extent DIFFERENT (0.22 vs 0.3 Ln2 printed); CB span basis NOT_PRINTED; CB 7.5 cm extension PRINTED |

GB_EXTERIOR_DETAIL, BLINDING_PROJECTION_M and LINTEL_SCHEDULE move none of the 8 figures (as T-044 found on 56820cb).
What A holds and B releases is, by quantity: columns 36.714 m3, ground beams 27.365 m3, blinding 22.155 m3, necks
10.855 m3, stair +5.319 m3, reinforcement +6,639.867 kg; slab -0.632 m3 (thickness default) and ground slab +0.114 m3.

## Checks

- Synthetic villa (tests/t165_release_baseline, 16 pass): manifest byte-identical across two runs; a profile with one
  printed value retyped (4.0 -> 4.1) refused; a missing facts file refused; swapped / missing / unpinned drawings, a
  size difference, a missing key ("no profile" must be written as null), a candidate method, a wrong interpreter and a
  non-empty --out refused with nothing run; engine failure recorded (exit 4, null figures, never 0); expected figures
  REPRODUCED / NOT_REPRODUCED (exit 3); hand truth: seed 21's 24 columns HELD without the profile (null, not 0) and
  released at the generator's hand truth 12.54 m3 with it; footings 21.84 m3 equal in both; compare names the profile as
  the only configuration difference and only STR.* figure sets as differing; per-code figures on a hand-made line list
  (two units of one code kept apart, bounded + unbounded held, a quantity state without a number counted held).
- Development villa: both specs REPRODUCED (line count and BOQ_LINES.csv sha). On the committed code 146fffb (tree
  CLEAN) each spec was run twice: the two manifests are byte-identical, BASELINE_MANIFEST.json sha256
  V29_ROUTEG_NO_PROFILE 694d5f5d39fd096c..., V29_ROUTEG_PROFILED edbc84036de1770f.... On another commit (a merge) the
  manifest differs only in `engine`; `compare` then shows 0 configuration and 0 figure differences and identical
  hashed outputs = reproduced.
- L2: tests/t165_release_baseline + m9_foundation + structural_comparison_engine (rebar firewall) + t061 + t156 (Gate B
  tool) + t130: 233 pass, 0 fail; freeze 0; codemap check stale none.

## Missing / for the Lead

- The ruling: which spec is the released baseline (or a third, Q-17 A compliant one: the T-044 PRINTED values as a
  project data file, the CB extent / span basis left out), recorded in ELEMENT_REGISTER.md / DELIVERY_PLAN_30D.md.
- Then: the scoreboard tables and PROGRESS restated on that baseline; BOQ_FAMILY_MASTER (next version) and census V2
  runs, and every Gate B diff, run through `tools/release_baseline.py` with that spec and cite its manifest sha.
- `tools/v30_gate_b.py` does not read a manifest yet (out of this task's files); the Gate B package names the spec id.
- No second drawn villa: the synthetic villa is the only non-Alsenan check.
