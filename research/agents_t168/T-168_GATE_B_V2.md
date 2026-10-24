# T-168: Gate B v2 (pinned sides, verified-change flag, change log, sealed guard by sha256): Checker how-to

Worker 1, 2026-10-24, branch agents/task-T-168, from working head c8dba740. Checker tooling only: no engine file, no
quantity, no rule changed. `tools/v30_gate_b.py` (T-156) is unchanged and still runs; `tools/v30_gate_b_v2.py` is new
beside it (the T-156 CLI test diffs without manifests, so the refusal "manifest missing" could not go into v1 without
breaking a pinned test). Nothing imports v2 (rollback: delete it).

## Regression baseline (owner 19:45 (3))

| Commit | What | Probe tests (tests/t168_gate_b_v2/test_probes_t168.py) |
|---|---|---|
| 76b44a38 (first) | the six probes ported as `xfail(strict=True)`; v2 only delegates to T-156 + the name guard | 6 xfailed; with `--runxfail` each fails as the probe recorded: 4a `['STRUCTURAL']` only, 4c `[]`, 7 / 10 / 12b DID NOT RAISE, 8 no verdict carry |
| fix commit | v2 implemented, markers removed | 6 passed, 0 XPASS, 0 XFAIL |

Check from the history: `git show 76b44a38:tests/t168_gate_b_v2/test_probes_t168.py` has the markers; run it against
`git show 76b44a38:tools/v30_gate_b_v2.py` (6 xfailed) and against the fix commit (6 passed).

## Checker procedure (one Gate B package)

1. Release side (run B, comparison base; run A, released baseline): `tools/release_baseline.py run SPEC --plan --structural --out DIR`
   writes BASELINE_MANIFEST.json (T-165). Candidate side: run the package's runner, then
   `python3 -I tools/v30_gate_b_v2.py manifest --lines V3_0_x_BOQ_LINES.json --candidate-version ARCH_TAKEOFF_V3.0.x
   --code-commit <merge sha> --project-id development-villa-t131 --drawing plan=<P7757 dxf> --drawing structural=<ST7757 dxf>
   [--document-register research/agents_t195/REGISTER_T195.csv] [--verdicts VERDICTS_V2.json] --out CANDIDATE_MANIFEST.json`.
   The drawings are hashed only; the manifest holds their file name, size and sha256, never their content.
2. `python3 -I tools/v30_gate_b_v2.py diff <B or previous candidate>/BOQ_LINES.json V3_0_x_BOQ_LINES.json
   --before-manifest <its manifest> --after-manifest CANDIDATE_MANIFEST.json --baseline-a <A>/BOQ_LINES.json
   --baseline-a-manifest <A>/BASELINE_MANIFEST.json --verdicts VERDICTS_V2.json [--changes ESTABLISHED_QUANTITY_CHANGES.json]
   [--register ELEMENT_REGISTER_V0.json] [--ledger LEDGER.json] --sha <merge-candidate sha> --out DIR`
   -> GATE_B_DIFF_V2.json / .csv (T-156 rows and flags + VERIFIED_CHANGED, verified_by, verdict_carry, change_log),
   GATE_B_ELEMENT_DIFF_A.json (element by element against A), ESTABLISHED_QUANTITY_CHANGES_REQUIRED.json.
   Exit 2 = refused, every reason printed as `GATE B REFUSED [CODE]: ...`, nothing written.
3. Read `summary.status`: REVIEW_REQUIRED whenever a COUNTED verdict's line changed (any change; the row says whether
   the scoreboard's 0.0005 would still count it). Each such row needs a change-log record (author:
   `change-add ... --cause ... --evidence SHEET=VALUE --checker-verdict ID|NONE`); NONE keeps the line STALE (out of
   VERIFIED); only a new V2 verdict bound to the after side and cited in the record makes it REVERIFIED.
4. Verdict JSON names both sides: kind, spec id (baseline_id / candidate version), manifest sha256, BOQ_LINES sha256,
   project id, line identities (label, revision set, drawing roles, alias), drawings, engine commit.

## Identity rule, checked on the real candidate's recorded hashes

A line identity (project label, revision set) is accepted only when its revision set is the revision set of a subset
of the side's pinned drawings (`sha256('|'.join(sorted(drawing sha256s)))`, the engine's own function). Recorded hashes
(T-165 spec, T-235 section 3): plan ab54dd55... gives db7b3eb8 (the 579 architectural lines), structural 9f9d1179...
gives 297e913d (the 3,004 route lines): both derive, so the real two-identity candidate passes with its route label
listed as an alias; the candidate-wide revision set of the two drawings is 5e369075.... A line from any drawing the side
does not pin is REVISION_MIX whatever project id it prints (probe 10 is refused by identity, not by label).

## Refusal codes

MANIFEST_MISSING, MANIFEST_INVALID (unknown schema; release run not REPRODUCED / RUN_NO_EXPECTED_FIGURES),
MANIFEST_MISMATCH (lines sha256, line count, spec sha256), PROJECT_MIX (two project ids across sides, or an
undeclared label), REVISION_MIX (a revision set no pinned drawing subset gives; without manifests: more than one),
DRAWING_MISMATCH (same role or file name, different sha256, without --new-revision-set; run A drawings not pinned by
the after side), SEALED (sha256 or name of a sealed file; a SEALED_PROJECT id), VERDICTS_INVALID (tools/boq_export_v1.py
V2 form checks), CHANGES_INVALID (empty cause, no evidence, edited / removed / reordered record, wrong candidate).

## Sealed registry

research/agents_t168/SEALED_REGISTRY.json: 23010 site benchmark by sha256 (e8d43f65..., from the recovery manifest);
the P7757 printed area take-off and the Qortuba seal + PA08 take-off by NAME only, because their sha256 is not recorded
in the repository (owner item: record them; the files are never opened to compute it). Any agent may add a
SEALED_PROJECT entry for a sealed test villa before its one use.

## Not done here / for other rows

- Wiring the sha256 guard into tools/release_baseline.py, tools/scoreboard_v2.py and tools/boq_export_v1.py (owner 19:00
  (8)): those files belong to other rows (release_baseline is READ ONLY in this row and its test forbids any tool from
  naming it); each can call `guard_inputs` / `guard_projects` of v2 in its own package.
- The census V2 / scoreboard keymap through the baseline runner (row title) is not part of items (1)-(9) and is not done.
- No real-drawing run in this package (the Drive connector returns the 3.1 MB structural DXF as base64 into the agent's
  context); acceptance names the Checker's re-run of V3.0.2 -> V3.0.3 with manifests (T-151 counts: 3,132 rows, 1,880
  changed, 0 changed-unflagged; with no V2 verdict the v2 rows and flags equal v1's, test
  test_t156_flags_and_counts_unchanged_without_verdicts).

## Lessons-register row proposed (ERS s.7)

"A comparison is pinned by the identity of what it compares (drawing sha256, line file sha256, manifest), never by a
label or a file name: a renamed sealed file, a line of another drawing set and a drifted run all pass a name check."
General, lane I tooling, provenance T-168 probes 7 / 10 / 12b; tests test_probes_t168.py.
