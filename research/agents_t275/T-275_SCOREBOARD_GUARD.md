# T-275: sealed-input guard in front of the scoreboard, the scoreboard key map and census V2

Worker 2, 2026-10-25, branch agents/task-T-275, from working head aa3a7bb4. Lane I tooling, backlog-permitted
infrastructure. No engine file, no quantity, no rule, no released output changed.

## The gap this closes (Checker 15:30, T-168 NOT DONE (i) / (ii))

`tools/v30_gate_b_v2.py` refuses a sealed or unpinned input by sha256 (T-168), but `tools/scoreboard_v2.py`, the
`tools/alsenan_keymap.py` v1 / v2 path and the census V2 runs (`research/agents_t140/census_run.py`) read any run folder
and any reference file by path: a renamed sealed take-off, a run whose BOQ_LINES.json was edited after the run, or a
candidate measured on another villa's drawing could reach a scoreboard figure with nothing refusing it.

## What was built

| File | What |
|---|---|
| `tools/scoreboard_guarded.py` (NEW, DEFAULT_GUARD_CLASS TOOLING, imported by nothing; rollback = delete) | `scoreboard` (the `tools/scoreboard_v2.py` CLI + `--candidate-manifest`, `--sealed-registry`, `--guard-record`), `keymap` (every `tools/alsenan_keymap.py` v1 / v2 / `--set-bindings` option + the same three), `census` (`--released RUN_DIR`, `--candidate LINES MANIFEST`, `--out`). Every check runs BEFORE the scorer is called; refusal = exit 2, `SCOREBOARD REFUSED [CODE]: ...`, nothing written. On acceptance it calls `tools/scoreboard_v2.py main` / `tools/alsenan_keymap.py main` unchanged, so the outputs are byte-identical to a direct call. |
| `tests/t275_scoreboard_guard/` (17 tests) | hand-made non-client villa SG-1 (below) |

`tools/scoreboard_v2.py`, `tools/alsenan_keymap.py`, `tools/v30_gate_b_v2.py`, the T-165 baseline runner and
`tools/boq_export_v1.py` are NOT touched (lane I file ownership, WORKFLOW_CONTROLS s.10 (6): workers add new unwired
modules only; the export boundary is T-273's). The guard reuses `guard_inputs`, `guard_projects`, `manifest_view`,
`check_side`, `drawing_conflicts` and `build_candidate_manifest` of `tools/v30_gate_b_v2.py` as they are, so the scoreboard
and Gate B refuse by the same identity rule.

## Rules (each is a test)

1. **Pinned run.** The run folder must hold BASELINE_MANIFEST.json (URBAN_BASELINE_MANIFEST_V1, T-165) with status
   REPRODUCED / RUN_NO_EXPECTED_FIGURES and at least one pinned drawing (MANIFEST_MISSING / MANIFEST_INVALID);
   BOQ_LINES.json (and, for the census, MATERIAL_RESULTS.json and COVERAGE.json) must have the manifest's sha256
   (MANIFEST_MISMATCH).
2. **Pinned candidate.** Candidate lines need their URBAN_CANDIDATE_MANIFEST_V1 (MANIFEST_MISSING); sha256 and line count
   are the manifest's (MANIFEST_MISMATCH).
3. **Identity by drawing sha256.** Every line's revision set must be that of a subset of its side's pinned drawings
   (REVISION_MIX, also for a line without any identity); its project id the manifest's or a declared route label
   (PROJECT_MIX).
4. **One project.** Two sides with two non-null project ids: PROJECT_MIX. The same drawing role / file name with two
   sha256s: DRAWING_MISMATCH. A candidate scored beside a run's release report must pin every drawing the run pins
   (DRAWING_MISMATCH: another villa or another revision). A release run without a project id (run A writes "new
   project") is accepted beside a candidate on the same drawings, as in the T-168 baseline-A rule.
5. **Sealed.** Every input file hashed and refused when its sha256 is a sealed file's whatever its name; a sealed name
   refused unopened (the test file is not even valid JSON); a pinned drawing with a sealed sha256 or name; a
   SEALED_PROJECT id in a manifest or a line label.
6. **Guard record** (URBAN_SCOREBOARD_GUARD_RECORD_V1): command, registry sha256, every input by role / name / sha256,
   each side (kind, spec id, manifest sha256, project, identities, drawings), and the NOT PINNED files. No path, no
   timestamp: byte-identical on a repeat (tested).

## Hand-calculated fixture (villa SG-1, not a client villa)

Footings F1 2.00 x 2.00 x 0.50 = 2.000 m3 + F2 1.50 x 1.50 x 0.50 = 1.125 m3 = 3.125 m3; slab SL1 BLOCKED_RFI (held,
no bound); paint R1 2 x (4.00 + 3.00) x 2.80 = 39.200 m2. Comparison list (made up): FOOT 3.000 m3, SLAB 6.000 m3,
WALL 40.000 m2. Through the guard: CONCRETE m3 coverage 100.00, compared 1, WAPE 0.125 / 3.0 = 4.17 %, signed +4.17 %,
held "1 ref line HELD; 1 engine line: 1 UNKNOWN (no bound)" (never 0), verified 1 / 2; PAINT m2 WAPE 0.8 / 40 = 2.00 %,
signed -2.00 %. Candidate SG-1.C (F2 1.60 x 1.60 x 0.50 = 1.280): 3.280 m3, WAPE 9.33 %. Census V2 through the guard:
footing family FOUND 3.125 m3 (released) / 3.280 m3 (candidate), slab family HELD with 0 found lines.
Adverse: sealed sha256 under another name; sealed name (default registry and engine/reference_mapping.py names); two
projects; a line of an unpinned drawing; a line without identity; no manifest; a manifest with no drawing; a failed run;
lines edited after the run; candidate without manifest; candidate on plan revision B; sealed pinned drawing; sealed
project; drifted MATERIAL_RESULTS.json in the census. Each refused with its code, nothing written, the scorer never
called (monkeypatched to fail if reached).

## Checker commands (development villa)

    # run side: the pinned baseline run (T-165 runner, unchanged), then
    python3 -I tools/scoreboard_guarded.py scoreboard --run <RUN_DIR> --label "<label>" \
        --reference <BENCHMARK_NORMALISED.json> --key-map tests/alsenan/T001B_KEY_MAP.json --verdicts <VERDICTS.json> \
        [--candidate-lines <V3_0_x_BOQ_LINES.json> --candidate-label "<label>" --candidate-manifest <CANDIDATE_MANIFEST.json>] \
        --out OUT.json --markdown OUT.md --heading "<UTC>" [--layout five] --guard-record GUARD.json
    python3 -I tools/scoreboard_guarded.py keymap <the same tools/alsenan_keymap.py options as today> --guard-record GUARD.json
    python3 -I tools/scoreboard_guarded.py census --released <RUN_DIR> --candidate <LINES> <MANIFEST> --out <EMPTY_DIR>

Acceptance check on real data: the guarded and the direct scoreboard on the same pinned run give byte-identical
OUT.json / OUT.md (`cmp`). Not run in this package: the architectural DXF archive (17.2 MB) is over the Drive
connector's download limit for this run, so no real pinned run was produced here; the byte identity is proven on the
synthetic villa by construction (the wrapper calls the unchanged `main` with the same argv) and by test.

## (3) Proposal for the T-165 baseline runner (written only; that file is not touched)

The runner hashes BOQ_LINES.csv / .json, MATERIAL_RESULTS.json and COVERAGE.json. Two files the scorer and the census
read from the same folder are NOT hashed: BOQ_RELEASE_REPORT.json (the scoreboard's release classes and CONDITIONAL
sets) and structural/FAMILY_COVERAGE.csv (census V2 route G families). Proposal for its owner row: add both to
HASHED_OUTPUTS (a new manifest field set; old manifests stay valid because a missing key reads as "not pinned"), and
call `guard_inputs` of `tools/v30_gate_b_v2.py` on the spec's pinned files before the run. Until then this guard reads
them as written and lists them under `not_pinned` with their sha256 in the guard record (tested). Its t165 hygiene
test (no other engine / tools file names the runner) still passes: this wrapper reads the manifest by file name only.

## Lessons-register row proposed (ERS s.7)

"A figure is only as pinned as every file it is computed from: guard the reader, not only the comparison. A scorer
that reads a run folder by path scores a drifted, foreign or sealed file as readily as the pinned one; the guard
hashes every input, binds each side to its manifest, refuses before the scorer runs, and lists every file it could
not pin." General, lane I tooling; provenance T-168 gap (Checker 15:30), T-275; tests tests/t275_scoreboard_guard.

## Rework r2 (Checker rejection 2026-10-25 05:55, narrow)

Gap the Checker proved: the census read three files that no manifest hashes (the run's structural/FAMILY_COVERAGE.csv;
MATERIAL_RESULTS.json and structural/FAMILY_COVERAGE.csv beside candidate lines). They were listed NOT PINNED with their
sha256 but never compared with the sealed registry, so a sealed take-off saved under one of those names reached the
census (probe: exit 0, census written).

Fix: `census_extra_files()` in tools/scoreboard_guarded.py lists every file `census_rows` opens that no manifest hashes
(only files that exist, as `census_rows` reads only those); `guard()` puts each into `G.guard_inputs` (sealed sha256
under any name, sealed name unopened) before any side is pinned, scored or written, and the same list feeds `not_pinned`
(NOT PINNED stays for the manifest-hash gap only). Reader sweep of the other two paths (no change needed): the
scoreboard and key-map paths open the run's BOQ_LINES.json and BOQ_RELEASE_REPORT.json, the reference, key map, set
bindings and verdicts, all already in `guard_inputs`; scoreboard_v2 only hashes a candidate's sibling .csv for its
provenance text, it does not read figures from it.

Tests (+4, tests/t275_scoreboard_guard, 21 in all): normal, the three extra files present: hashed in `inputs`, listed in
`not_pinned` with the same sha256, two calls give byte-identical GUARD_RECORD.json, candidate footings 2.000 + 1.280 =
3.280 m3 by hand; adverse: a registered sealed sha256 as candidate-side MATERIAL_RESULTS.json, as run-side
FAMILY_COVERAGE.csv and as candidate-side FAMILY_COVERAGE.csv each refused SEALED (exit 2), the census never called,
--out not created. The four fail on the rejected head 6fef94bf and pass on the rework. No quantity: tooling only.
