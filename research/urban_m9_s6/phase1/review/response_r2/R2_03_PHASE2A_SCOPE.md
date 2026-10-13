# Recommended Phase 2A scope ("reliability core"), for approval

**This is a plan. Nothing in it is implemented.**

**Principles**
- Every engine change is behind `--method ARCH_TAKEOFF_V2.1` (opt-in).
- V1, V2, route G and every historical freeze keep their outputs.
- No item is accepted on the reference plan alone: each needs its synthetic fixture.
- The set as a whole needs the blind round (P2-12) before V2.1 is proposed as a default.
- No tuning against benchmark or human quantities. No prices. No accuracy percentage. The gate stays INCOMPLETE.

**Effort:** S ≤ 1 day, M 2–3 days, L 4–6 days (one engineer, tests included).

## Changes from the round-1 plan

| Change | Why |
|---|---|
| **P2-00 is widened into "Stage 1" of the freeze migration.** It adds: an environment lock, an out-of-tree verifier, behaviour hashes with provenance masked, a session guard, and the errata and findings registers. | F-1 (a rebuild can heal its own manifest), F-2 (code stamps in outputs), F-4 (no pinned environment). Without this, "byte-identical" is not a trustworthy statement. |
| **P2-01 now specifies the hybrid margin and the UNDECIDABLE state, applied to three reviewed sites only.** | Q1 evidence; ChatGPT decision 1: no global rewrite |
| **New: P2-01b, a mean-axis face-line projection.** | F-3: at arbitrary angles gaps are lost entirely, and no ε fixes it |
| **P2-04: the provisional width is the wall-to-wall closure, never the swing radius. Confirmation needs a named evidence kind.** | ChatGPT decision 3 + Q2: the radius is 11–14 % below the width. **This corrects my round-1 text**, which proposed the swing radius as the provisional width. |
| **The minimal, read-only ledger moves into Phase 2A (P2-08a).** The full ledger with exit 3 stays later (P2-08). | Q3: it finds 130 missing reveal/head records that conservation alone cannot see |
| **The read-only dimension cross-check moves into Phase 2A (P2-09a).** | Q4: cheap, and one of the four promotion evidence kinds |
| **A "nib rule" (pieces < 100 mm as jamb evidence) is deferred to its own individual review (P2-13).** | Q2: it would confirm U2–U7, but it changes the masonry face model |

## Work packages, in order

| Order | Id | What | Files (proposed) | Depends on | Effort | Acceptance tests | Rollback |
|---|---|---|---|---|---|---|---|
| 1 | **P2-00** (Stage 1) | **Environment and freeze integrity.** No engine change, and no historical file changes: this package only adds files. (1) `ENVIRONMENT_LOCK.json`: the interpreter and exact package versions under which all 71 rebuilds reproduce. (2) `tools/freeze_verify.py`: exports HEAD to a temporary tree, rebuilds each freeze there, compares raw hashes and behaviour hashes (provenance fields masked), and writes nothing under `research/`. (3) A session guard test: no tracked file under `research/` may change during a test session. (4) `research/errata/ERRATA.jsonl` and `ENGINEERING_FINDINGS.jsonl`, append-only. First entries: S6R-A1, S6R-A2, S6R-B1, F-1..F-4, and the unguarded `ceil` in the M4 lap count (record only). | `tools/freeze_verify.py`, `tests/freeze_integrity/` (all new) | — | M | AT-Q5-01..05, AT-Q5-07 | delete the new files |
| 1b | **P2-00 Stage 2** *(owner decision)* | Relax the source pin for **one** file, `engine/source/opening_census.py`. `topology.py` and `tools/urban_intake.py` are also pinned, by the M7 / M8 engine freezes; Phase 2A is scoped not to edit them. Allowed: default-preserving keyword parameters only. The S8.6 pin becomes provenance through an errata entry. The S8.6 in-place rebuild test is re-pointed to the verifier: one historical test changes, with the owner's approval. | `engine/source/opening_census.py` (keyword parameters only), `tests/lintels_s8_6/…` (one test) | P2-00 | S | AT-Q5-06 | revert the keyword parameters |
| 2 | **P2-01** | **Robust predicate policy `ROBUST_PREDICATE_V1`.** m = max(1e-6 mm, 16·u·M·(d+1)), with AT_THRESHOLD records and UNDECIDABLE above 1e-3 mm. Applied at the 100 mm face piece, the 300 mm overlap and the 500 / 400 mm gap. A threshold census lists every other `<` on the V2 path, for later individual review. | with Stage 2: keyword parameters in `opening_census`; without it: `engine/source/band_census_v2.py` (stdlib) + a delegation test | P2-00 | M | AT-Q1-01, 02, 03, 06, 07, 08 | `--method ARCH_TAKEOFF_V2` |
| 3 | **P2-01b** | **Mean-axis face lines.** Bins only group segments; each group's axis is its length-weighted doubled-angle mean, with the bin's half-plane kept. | same as P2-01 | P2-01 | S | AT-Q1-04, 05 | policy flag off |
| 4 | **P2-02** | **Metamorphic suite:** random angles, offsets 1e5–1e7 mm and 3.3e9 mm, mirror, mm ↔ m | `tests/m9_s6p2/test_metamorphic.py` | P2-01, 01b | S–M | AT-Q1-05 | remove the tests |
| 5 | **P2-03** | Unit- and translation-stable content ids | `arch_completeness` ids | — | S | ids equal in mm, m and translated drawings | old helper |
| 6 | **P2-04** | **Door / window element conservation**, with the state machine CONFIRMED / PROVISIONAL / UNRESOLVED. Every transition carries a typed evidence record. The double-leaf rule. Provisional door lines with width = closure and range [radius, closure], kept out of released totals. Exit 3 on non-conservation. | `arch_rooms` (V2.1 branch), `arch_completeness`, the workbook's provisional section | P2-01 | M–L | AT-Q2-01..07, AT-G-01 | V2.1 branch off |
| 7 | **P2-05** | Fills from K2 at every depth (MINSERT, layer 0, SOLID / TRACE, arc-edged hatches) | `arch_discovery.shapes` → V2.1 `ents["hatches"]` | — | M | round-1 variants r13 / 14 / 17 / 18 / 19 / 20 / 22 NOT_REPRODUCED | V2.1 branch off |
| 8 | **P2-06** | **RFI register by distinct question; engineering findings channel.** The element-level BOQ records are kept, each pointing to its question id. | `arch_completeness`, `urban_boq_m9` (`RFI_REGISTER.json`, `ENGINEERING_FINDINGS.json`) | P2-04 | S–M | reference plan: the 85 RFI lines become 4 client questions + 14 engineering findings; every line is referenced once | V2.1 branch off |
| 9 | **P2-08a** | **Minimal surface ledger, read-only.** One record per (element, surface, trade), using the versioned table `ELIGIBILITY_V0`, marked PROPOSAL. No exit-code change, no completeness claim. | `engine/source/surface_ledger.py` (new, stdlib), `SURFACE_LEDGER.json/.csv` | P2-04 | S–M | AT-Q3-01..06 | do not write the file |
| 10 | **P2-09a** | **Dimension cross-check, read-only.** Reuses the dimension model in `engine/cad_adapter.py`; resolves DIMLFAC per entity and style; writes REVIEW for \|diff\| > 5 mm. It is the DIMENSION evidence kind for P2-04. | `engine/source/dimension_evidence.py` (new), `DIMENSION_CROSSCHECK.json` | P2-00 | S | AT-Q4-01..05 | do not write the file |

**Total:** about 15–19 engineer-days without Stage 2, about 14–17 days with it. Stage 2 removes the parallel module and its delegation test.

## Not in Phase 2A

| Item | Why not now | Meanwhile |
|---|---|---|
| **P2-13 nib rule** (wall pieces < 100 mm as jamb evidence) | changes the masonry face model; may create false openings; needs individual review, fixtures and the owner | U2–U7 PROVISIONAL with bounded widths |
| Reveal / head-soffit emitter | heights and frame position are **[MISSING SOURCE]**; whether reveals are measured is an **[OWNER DECISION]** | ledger MISSING records (130 on the reference plan) |
| Kitchen (SERVICE) as WET-eligible | **[OWNER DECISION]** | ledger MISSING (4) |
| Full ledger with exit 3 (P2-08), wall-face ledger | after P2-08a has run on the blind drawings | read-only ledger |
| Global threshold rewrite | ChatGPT decision 1; Q1 census first | the three reviewed sites only |
| Route-G / M4 corrections (incl. the unguarded `ceil` in the M4 lap count) | frozen structural results; owner decision; a new route-G version | errata entries |
| P2-07, P2-10, P2-11 (round-1 ranks 4, 7, 8) | not needed for the reliability core | unchanged |
| A local-origin shift before measuring | removes coordinate-magnitude noise entirely, but changes float bytes everywhere on V2.1; the margin covers it meanwhile | AT-Q1-03 REVIEW finding |

## Owner decisions needed before Phase 2A starts

| # | Decision | Default if not decided |
|---|---|---|
| D1 | Approve Stage 1 (P2-00): it adds files only | — (prerequisite) |
| D2 | Stage 2 for `opening_census.py`: keyword-only change; the S8.6 pin becomes provenance; one historical test is re-pointed | parallel module `band_census_v2.py` + a delegation test (accepts duplication) |
| D3 | `ELIGIBILITY_V0` used as a diagnostic table (marked PROPOSAL) | the ledger is not written |
| D4 | Provisional door lines (bounded width) shown in a separate, non-released workbook section | provisional doors as RFIs only |
| D5 | The pinned environment: Python 3.11.17 and the package versions in `R2_05` | — (prerequisite for any byte-identical claim) |

## GO / NO-GO for Phase 2A as a whole

These are the round-1 criteria, amended.

**GO (all required)**
1. Every acceptance test listed above for P2-00 … P2-09a passes.
2. The verifier reproduces every freeze in the lock environment. The session guard is green.
3. On the reference plan, every V2.1 change is listed in a before/after register and accepted by a reviewer. Expected: +1 door, +1 window, +0.20 m wall, 6 provisional door lines, 1 unresolved door.

**NO-GO (any one)**
- a V1 or V2 byte change;
- a freeze whose behaviour hash changes;
- an unexplained metamorphic difference;
- a CONFIRMED element without evidence;
- a swing radius used as a width;
- any tuning against benchmark or human quantities.

The blind round (P2-12) follows. It is the only evidence that generalises.
