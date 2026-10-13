# S6 review, round 2: response to ChatGPT's decisions and questions Q1–Q5 (public-safe notes)

- Reviewed engine: `c757d8a`.
- Round-1 notes: `../` (commit `47ed00b`).
- **Phase 2A has not been started.**
- No production code, owner rule, frozen output, `data/` file or repository setting was changed.
- Every experiment ran on:
  - a scratch export of the committed source; or
  - a detached scratch worktree, reset to HEAD after each experiment.
- The human benchmark was not opened.

These notes carry no drawing identity, no client figure beyond engine counts, and no benchmark value. The reference-plan evidence is in the PRIVATE archive, which is never committed:
- the per-door table with drawing handles and the U1–U8 mapping;
- crops;
- the real ledger and the dimension census;
- the raw test logs.

## Read first

1. `R2_01_RESPONSE.md`. The answers to Q1–Q5, each claim labelled VERIFIED DEFECT / MEASURED / ENGINEERING INFERENCE / OWNER DECISION / MISSING SOURCE. It covers where I disagree, what worked and what did not, and the recommendation.
2. `R2_03_PHASE2A_SCOPE.md`. The recommended Phase 2A scope, for approval, with the owner decisions D1–D5.
3. `R2_02_ACCEPTANCE_TESTS.csv`. 35 revised acceptance tests, each with its status on `c757d8a`.
4. `R2_04_CLAIMS_REGISTER.csv`. Every claim with its label, evidence file and reproduction command.
5. `R2_05_REBUILD_MATRIX.csv`. Each historical rebuild test under Python 3.11.17 and 3.13.16 (whole suite and isolated).
6. `R2_06_ELIGIBILITY_V0.md`. The proposed surface-eligibility table. It is a proposal; owner approval is needed.

## Here

| Folder | Contents |
|---|---|
| `evidence/` | **Synthetic or aggregate results only.** Q1: the predicate keep-rate tables, the threshold sites, the angle-axis runs, the any-width gap test. Q3: the synthetic villa ledger. Q5: the villa 3.11 / 3.13 comparisons and flip risk, the stamp and pin census, the two `pip freeze` lists. |
| `scripts/` | Every harness used in this round. Stdlib plus ezdxf. Each takes its paths as arguments; run them with `python3 -I`. The reference-plan harnesses (`threshold_probe_win.py`, `probe_mean_axis.py`, `q2_door_probe.py`, `q2_door_crops.py`, `q4_dimension_census.py`) need the private inputs. |

## The archives (outside the repository)

| Archive | Contents |
|---|---|
| `URBAN_M9_S6_R2_RESPONSE.zip` | These notes, plus `R2_ALL_IN_ONE.md` for single-file readers |
| `URBAN_M9_S6_R2_RESPONSE_PRIVATE.zip` (`PRIVATE_DO_NOT_COMMIT/`) | The reference-plan evidence |

- Each archive carries its own `SHA256SUMS.txt`.
- Entry timestamps are fixed, so a rebuild from the same inputs reproduces the archive bytes.
