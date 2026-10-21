# Blind-test readiness checklist (protocol URBAN_BLIND_V1, amendment A1)

**State at the Phase 2B-0 gate:**
- Engineering readiness is done.
- Owner and process readiness are **not** done.
- **The blind round must not start until every item in section B is checked.**

## A. Engineering (done in Phase 2B-0)

- [x] **Mode A cannot abort or release a negative quantity on V2.2 (F-24).** Proved on the reference plan with heights: `test_the_reference_plan_with_heights_no_longer_stops`.
- [x] **No released midpoint for an unresolved skirting edge (F-17).** The unknown sill outcome is a range.
- [x] **Doors with a doubtful width or class are held, and none is withheld silently.** F-18, F-19 and F-20 are covered, and `withheld_without_finding` is empty. Lift candidates are flagged (F-22).
- [x] **Ledger conservation.** Every BOQ line is in exactly one record or is named out of scope, and coverage is reported by floor and trade. Completeness is never claimed (F-21).
- [x] **Window position evidence.**
  - V2.2 publishes `position.centre_m`, and the scorer matches V2.2 windows by position.
  - The scorer matches V2.1 windows by width, as before.
  - Dry run: 6 / 6 faults detected on V2.2 and on V2.1.
- [x] **Heights facts template.** `FACTS_TEMPLATE_HEIGHTS.json` holds no value, and the engine refuses it until it is filled.
- [x] **Scorer and evaluation protocol frozen before any unseen drawing.**
  - The sha256 of `blind_score.py`, `dry_run.py`, `BLIND_TEST_PROTOCOL.md` and the facts template are in `BLIND_READINESS_RECORD.json`.
  - `tests/m9_p2b0/test_p2b0_blind_freeze.py` fails on any change.
- [x] **Reproducible hashes, code version and test configuration recorded.**
  - Code-tree digest of `engine/` + `tools/` (636 files).
  - Python and package versions against `research/freeze_integrity/ENVIRONMENT_LOCK.json`.
  - The full-suite, targeted, real-plan and run commands.
  - The base commit is `981ef5f`, and the record is added by the Phase 2B-0 commit.
- [x] **V1, V2 and V2.1 are byte-identical to `981ef5f`** (168 / 168 files). V2.1 remains the round's baseline, in Mode U only.
- [x] **No tuning against benchmark answers.** No blind drawing or benchmark exists yet. The private benchmark was never opened, and the forbidden-number scan is clean.

## B. Owner and process (open: these block the round)

- [ ] **OD-14.** Amendment A1 and the hash freeze are approved.
- [ ] **OD-1, OD-2, OD-3, OD-4, OD-5** are answered, or explicitly deferred. These are the skirting convention, the held doors, the lift candidates and the main entrance. They decide what the scored skirting and door totals mean.
- [ ] **OD-15.** The QS is appointed, and the conventions sheet (protocol section 4) is agreed.
- [ ] **OD-6.** The facts preparer is named, if Mode A is run. Mode A is run on V2.2 only.
- [ ] **OD-16.** A second blind project is identified. Without it no percentage claim is allowed, and the round is diagnostic only.
- [ ] The round's commit is tagged, and `make_readiness_record.py` is re-run at that commit. Its code-tree digest is recorded in the round's custody log. This is the commit that adds the Phase 2B-0 reports, or a later one with a recorded amendment.
- [ ] The run environment matches the lock (`URBAN_REQUIRE_LOCK_ENV=1`).

## C. What the round will and will not show

**It will show, per family:**
- for released quantities: omissions, false positives and quantity error against the QS;
- for withheld quantities: whether the hold or range was justified.

**It will not show** an accuracy percentage from one project, or a quotation-ready BOQ. The protocol's claim rule needs two projects. The BOQ completeness gate stays `INCOMPLETE` / `NOT_ESTABLISHED`.
