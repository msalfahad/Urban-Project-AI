# Commits and branch

- **Repository:** msalfahad/Urban-Project-AI
- **Branch:** `claude/access-permissions-setup-ii24ws`. M2 work starts after M1's last commit `8e2198b` (M1 TEST_RUN).
- **Pull request:** none opened (not requested).

| commit | date | subject |
|---|---|---|
| `ed91cbd` | 2026-10-10 | M2: generic structural route - drawing model, schedule reader, member detection, slab engine, bar shapes |
| `69f6d8c` | 2026-10-10 | M2: synthetic villa generator with independent truth, evaluator, detection hardening |
| `2b92e25` | 2026-10-10 | M2: CAD heal (collinear merge, dangling-end snap), intake decimal handle fix, open-boundary faces, defect set |
| `938b0d1` | 2026-10-10 | M2: reported wide snap, unenclosed band-side check, hard-defect stress mode |
| `8c1e28e` | 2026-10-10 | M2: route G (generic engine) in the CLI, coverage-risk and rebar-completeness registers, overlays |
| `2a0246b` | 2026-10-10 | M2: Alsenan generic vs frozen replay, reinforcement completeness of the 89, ground-slab gap audit |
| `a92ded1` | 2026-10-10 | M2: tests (geometry fixtures, components, synthetic end-to-end, ownership), ellipse intake and schedule-title fixes |
| `180d9fc` | 2026-10-10 | M2: restore the frozen M1 CLI; route G moves to tools/urban_boq_m2.py; NOT DETECTED section |
| `0680c7c` | 2026-10-10 | M2: architectural room slice, generic stair flight, benchmark positions, stair scenarios |
| `d23fe92` | 2026-10-10 | M2: columns never bind to footing outlines; range-sanity metric; route G deliverables |
| `2c5ff19` | 2026-10-10 | M2: opt-in intake cache by drawing sha256 and code digest; determinism test |

The package documents, the reports test and TEST_RUN.md follow in the commits after the ones listed here; see `git log` on the branch.

**Freeze points used for evidence**
- The held-out sets were run on 69f6d8c, 2b92e25, 938b0d1 and d23fe92 (one fresh seed range each).
- The Alsenan comparison was first run on 8c1e28e, after route G was committed. It was rebuilt unchanged at each later commit.
- The frozen M1 CLI was restored byte-identical in 180d9fc, after 8c1e28e had edited it. A test pins its sha256.
