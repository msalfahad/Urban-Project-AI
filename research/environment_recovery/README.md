# Environment recovery: missing prerequisites and proposed private input store

## Status

The full test suite is **not green** in the replacement container. At `52fa35f`:

| Result | Count |
|---|---|
| Passed | 6659 |
| Failed | 344 |
| Errors | 32 |
| Skipped | 138 |

Every one of the 376 failures and errors comes from a missing private file. None comes from code.

A re-run at `74d033d` gave 6687 passed, 344 failed, 32 errors and 138 skipped. The 376 non-passing tests are the
same ones, and the 28 extra passes are the new S8.2A and environment-recovery tests.

`RECOVERY_MANIFEST.json` lists the exact paths. There are 107 missing prerequisites. For each one it records:

- category;
- expected SHA-256 where git pins it;
- the tests that need it;
- the tracked code that names it;
- the restore route.

| Category | Missing | Restore route |
|---|---|---|
| DERIVED_EXPERIMENT (`data/experiments/...`) | 76 | Regenerate with the named tracked script once its sources are back, or restore from the private store |
| BENCHMARK_TRUTH (seals, contractor or historical figures, `site_benchmark`) | 14 | Restore from a sealed store with a separate key; never mount it for a blind run |
| DERIVED_RUN (`data/runs/...`) | 8 | Regenerate or restore. `QORTUBA_ARCHITECTURAL.json` is pinned to `7dbafb3d…` |
| SOURCE_DRAWING | 5 | Restore and verify SHA-256 (golden 23010 pins; content-addressed names) |
| GOLDEN_FIXTURE | 2 | Restore and verify |
| DELIVERED_PACKAGE | 1 | Restore |
| SESSION_UPLOAD | 1 | Not a fixture: that test should skip, not fail |

### Registered Alsenan source files

Five of the nine registered files are present:

- `P7757.dxf`
- `ST7757.dxf`
- `ST7757.pdf`
- both earlier architectural PDFs, `80b6a804…` and `281a0c3f…`. These two copies were reconstructed byte for byte
  from the S8.2A drawing set and verified against their registered SHA-256, not restored from an original store.
  - The set is `P7757_ARCH_PDF_SET_01-12`: one 12-sheet PDF in two upload parts, `cd3b8669…` and `1e7087d3…`.
  - It is registered as additional evidence, not as a replacement.
  - Each part is byte-identical to one earlier file after removing 134 bytes of added /Title and /Subject.
  - No build output depends on keeping the two reconstructed copies.
  - **Owner decision (2026-10-09): KEEP them** in private, git-ignored storage.
    - Each is marked `BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD`, with the uploaded set as its independent
      parent evidence.
    - The marking appears in three places: `RECOVERY_MANIFEST.json` (`acquisition`), the lock's `note`, and a private
      sidecar `<sha>.pdf.provenance.json` next to each copy.
    - A reconstruction is never presented as a separately obtained original.

These four are still missing:

- `P7757.dwg` (`7f61f3ac…`)
- `P7757_Architectural.dwf` (`7d440a57…`)
- `ST7757.dwg` (`3f7a556c…`)
- `sanitary-7757.pdf` (`11673687…`)

## Proposal

### 1. A git-tracked `INPUTS.lock.json`

This file holds metadata and SHA-256 only. `INPUTS.lock.proposed.json` is a draft generated here.

- Each entry is `{path, sha256, bytes, store, role}`.
- The store is one of `SOURCE`, `DERIVED` or `BENCHMARK`.
- No file content, no credential and no client name.
- It generalises what `tests/r8_6/FIXTURE_MANIFEST.json` and `runs/golden/23010_MANIFEST.json` already do for a few
  files:
  - **a missing file skips**, with the lock's reason;
  - **a present file with a different hash fails**, because drift is never absorbed.
- Derived files without a pinned hash get one recorded on their first restore.

### 2. A private, read-only restore process

- **Storage:** one private object bucket, versioned, with object lock and server-side encryption. Objects are keyed
  `by_sha256/<sha>.<ext>`. Optionally add client-side encryption (age).
- **Credentials:** the cloud environment gets a bucket-scoped, **read-only** credential and the decryption key as
  environment secrets. Nothing goes in git.
- **Restore:** a stdlib `tools/restore_inputs.py` fetches each missing lock entry and verifies its SHA-256. It writes
  only under `data/`, refuses any mismatch, and never prints content.
- **Benchmark truth:** it lives under a **separate prefix and key**, restored only by an explicit post-freeze step.
- **Network:** the environment's network policy allows only the bucket host for the restore step.

### 3. Pinned, reproducible dependencies

`requirements-lock.proposed.txt` holds the exact versions that reproduced every Alsenan frozen stage in the rebuilt
container. The environment setup script installs it with `python3 -m pip`.

The fresh container lacked four of them, and each one stopped work until it was found by hand:

| Missing | Effect |
|---|---|
| scipy | the S1 column census failed |
| cryptography + cffi | the system binding panicked under pypdf |
| PyMuPDF | 9 test modules failed at collection |
| anthropic | `test_base_models.py` failed |

### 4. A clean separation of stores

- **SOURCE:** issued drawings, content-addressed and immutable.
- **DERIVED:** experiment and run outputs, regenerable from SOURCE with tracked code, verified against the lock.
- **BENCHMARK:** sealed truth such as contractor, historical or freelancer figures and site benchmarks. It is never in
  the same store or key as SOURCE, and never mounted for a blind build.

### 5. Automatic detection of missing prerequisites

- `check_prerequisites.py` (stdlib) prints `PRESENT`, `MISSING` or `DRIFTED` for every lock entry. It exits 1 on
  drift.
- **Proposed next step:** a `conftest.py` hook reads the lock and turns a missing locked path into a skip, with its
  store and restore route. Tests then never fail with `FileNotFoundError` for private data. The SESSION_UPLOAD case is
  fixed the same way.
- Run the checker in the environment setup script, before tests, so a missing store shows up as one clear line.

### 6. Work in progress

Commit and push after every module that passes its tests. The S8.2 interruption happened because work was
uncommitted when the container was reclaimed.

## Files

| File | What it is |
|---|---|
| `build_recovery_manifest.py` | Regenerates both JSONs from a full-suite JUnit XML, a static test scan and the tracked identity records |
| `RECOVERY_MANIFEST.json` | The missing prerequisites |
| `INPUTS.lock.proposed.json` | Draft lock |
| `check_prerequisites.py` | Checker |
| `requirements-lock.proposed.txt` | Pinned dependencies |
