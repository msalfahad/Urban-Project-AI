# Privacy move plan (owner directive 2026-11-02, Q1): PREPARED, NOT EXECUTED

Status: waiting for the owner. Nothing below has been moved, deleted or rewritten. Do not run any step until the owner
approves it in the main chat. History is left alone unless the owner asks for a history purge.

## Step 0: owner actions (only the owner can do these)

1. GitHub, repository Settings, Danger Zone: change visibility to **Private** (free).
2. Confirm that the next scheduled agent run still starts. The Claude GitHub app must have access to this repository.
3. Approve, change or refuse steps 1-4 below.

## Step 1: what moves to the private data repository (counted on engine HEAD 2f63773e, 2026-11-02)

The target is the private data repository. Only generic code and synthetic fixtures stay here.

| Group | Paths | Count at HEAD |
|---|---|---|
| Client findings document and the files that name the client | `docs/ALSENAN_FINDINGS.md`, plus about 9 files that carry the client's name. The list is made by a grep in the private repository; names are never printed here | about 10 |
| Training-villa research | `research/*alsenan*/**` | 829 files. 1,558 tracked paths contain the project word anywhere: tests, tools and docs included |
| Freelancer figures | every path with `FREELANCER` in its name: 18 under `research/agents_t*/`, the rest under `tests/` and docs | 25 |
| Freelancer raw rows (privacy finding 1 Nov: header cells with names and a phone number) | `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` (frozen test input) | 1 |
| Project registries | `data/registry/P7757_PROJECT_RULES.json`, `data/registry/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json`, `data/registry/23010_groups.json`, `data/registry/23010_heights.json` | 4 |
| Second-project run output | `runs/current/23010.json` (35.4 MB) | 1 |
| AutoCAD drawings that slip past `*.dxf` | root file `DXF` (no extension) | 1 |
| External drawing sample | `research/external_engine_lab/MINSERT_REFLECTION_ORACLE.dxf` | 1 |

## Step 2: how, without breaking frozen methods or tests

1. Copy each group into the private repository first, with the same relative paths and a manifest of SHA-256 hashes.
2. Frozen files and tests that read them do not change in place. A NEW non-frozen version of each register is made
   without the personal header cells. Tests then read the private copy when present and `pytest.skip("private data not
   available: <name>")` when absent (task D1, T-462).
3. Delete the originals in ONE normal commit per group, on a task branch merged by the Verifier, never by force-push.
   After the deletion: the freeze check must print 0, and the full suite is compared test by test with the baseline.
4. The data stays in the git history. Only a history rewrite, or the repository staying private, removes it from view.
   That decision is the owner's alone.

## Step 3: keep it from coming back

- `.gitignore`: add `/DXF`, `/DWG`, `*.DXF`, `*.DWG`, plus a rule for extensionless drawing files (task T-470). Today
  `*.dxf` misses a file named `DXF`.
- A test that fails when a tracked file starts with the AutoCAD header (`AC10`), or when a tracked text file holds a
  phone-number or name pattern from the freelancer workbook header.

## Step 4: open decisions for the owner

- Execute steps 1-3 now, or after the repository is private?
- History purge: yes or no? It rewrites every branch, and agents must re-clone.
