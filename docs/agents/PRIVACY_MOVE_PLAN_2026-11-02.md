# Privacy move plan (owner directive 2026-11-02, Q1): PREPARED, NOT EXECUTED

Status: waiting for the owner. Nothing below has been moved, deleted or rewritten. Do not run any step until the owner
approves it in the main chat. History is left alone unless the owner asks for a history purge.

## Step 0: owner actions (only the owner can do these)

1. GitHub, repository Settings, Danger Zone: change visibility to **Private** (free).
2. Confirm that the next scheduled agent run still starts. The Claude GitHub app must have access to this repository.
3. Approve, change or refuse steps 1-4 below.

## Step 0b: post-privacy access check (prepared 2026-11-02; run by the main chat after the owner switches visibility)

1. Unauthenticated `GET https://api.github.com/repos/msalfahad/Urban-Project-AI` returns 404; before the switch it
   returned `"private": false, "visibility": "public"`, 0 forks (checked 2026-11-01 22:5x UTC).
2. GitHub, Settings, Integrations, GitHub Apps, Claude: repository access still includes this repository (owner).
3. Next scheduled slots after the switch each write STARTED + a final line in RUN_LOG.md: Worker 1 (:19 odd hours),
   Worker 2 (:39 even), Worker 3 (:59 even), Checker (:49 hourly), Lead (:11 every 4 h). A clone or fetch refusal
   shows as a missing STARTED line or a 403 / "Repository not found" in the run's final line.
4. One Checker 'engine push' and one Lead board commit land on origin within 6 h of the switch.
5. RUN_LEDGER for the 6 h after the switch shows every slot SUCCESS; any BLOCKED / INCOMPLETE slot is a critical
   alert to the owner the same hour.

## Step 0c: read-only exposure assessment (main chat 2026-11-02; no file changed)

Scope: engine branch HEAD 3fe8f974 and its fetched history (1,048 commits, shallow clone), board branch HEAD.
Not scanned: the other 404 branches, the 5 pull-request refs, Drive, any external copies.
- Credentials: 0 hits for GitHub / Anthropic / AWS / Slack / Google key patterns or private-key headers in HEAD and in
  the fetched history; 8 'token = ...' hits are code constants and run ids (false positives); 2 board hits are the
  regexes of existing secret-scan tests. No credential rotation is indicated by this scan.
- Personal data CONFIRMED: tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (freelancer workbook header cells:
  names and a phone number; Checker O-T407-2); tests/r8_8/registers/NEW_QORTUBA_TOPOLOGY.json (a personal webmail
  address, benchmark villa set). The +965 numbers in docs/WHATSAPP.md and two render tests are placeholders (9000 /
  9999 series).
- Client drawing material: root file `DXF` (extensionless AutoCAD drawing, not caught by the case-sensitive `*.dxf`
  rule), research/*alsenan* (829 files), the benchmark villa's research folders (128 paths incl. BOQ and pricing).
- Exposure window: public since at least 2026-09-09 (repository creation); the freelancer file since 2026-10-20.
  0 forks reported; clones by agents / sessions exist; third-party caches cannot be ruled out.

## Step 0d: narrow history remediation (RECOMMENDATION ONLY; owner approval required for every step)

1. Go private (owner) and pass Step 0b.
2. Normal commits (via a task branch, Verifier merge): replace the two personal-data files by NEW non-frozen versions
   without the personal cells; tests read the private copy or skip (T-462).
3. Land D2 (T-463) first, so no test depends on old commit hashes that a rewrite would change.
4. Only then, if the owner wants the data out of history: a path-limited rewrite (two files + the root `DXF`) on all
   branches, GitHub Support request to purge the 5 pull-request refs and cached views, every agent re-clones, and the
   freeze baseline is re-verified on the rewritten commits (release reproducibility check).
5. A rewrite is NOT recommended for the 829 research files: private visibility is the proportionate control.

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
