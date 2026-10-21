# Executive engineering summary (deliverable 1) - Phase 2B-1, ARCH_TAKEOFF_V2.3

## What was done

The owner's approved engineering knowledge is now a permanent, machine-readable registry the engine reads, and a new
opt-in method, **ARCH_TAKEOFF_V2.3**, applies it. V1, V2, V2.1, V2.2, route G and every frozen artefact are
unchanged: 308 of 308 snapshot files are byte-identical, and the freeze-baseline check reports 0 differing
artefacts.

| Work package | Result |
|---|---|
| WP-1 knowledge audit | 25 rule records (23 owner-approved, 1 project-specific, 1 deprecated), 11 conflicts, a precedence policy, a 35-pattern question catalogue, 4 genuine owner questions; every record linked to its authority, its code and its tests; a source index of every rule / fact / question location with a crosswalk of 21 earlier question-id rows; 7 root causes of the repeated questions |
| WP-2 reasoning model | a space connectivity model (interior status from evidence, building parts, connecting spaces, one-space project decisions) and a question register (A established / B document request / C conflict / D owner policy / E engine defect), with per-element evidence |
| WP-3 doors | the owner correction (wall opening = nominal + 0.10 m: 1.10 / 1.00 / 1.10 m), never a second 0.10 m, the CAD value kept apart; AS_DRAWN and OWNER_REQUIRED views never added; heights 2.20 / 2.50 m as labelled fallbacks; main entrance as drawn; elevators on a separate quotation schedule; a dependency map of every enlargement |
| WP-4 finishes | kitchens, pantries and ironing rooms take the wet scope; full-height wall porcelain; no paint over porcelain; no skirting on full-height tile; marble thresholds at wet doorways, porcelain through other doorways (once); door-jamb plaster and passage-jamb skirting (PROVISIONAL); balcony / roof waterproofing |
| WP-5 tests | 78 new tests, all passing; the owner's 23-case QA list covered; metamorphic (move, mirror, turn, nested blocks, attribute labels, mm vs m) and determinism |
| WP-6 audit | 14 counterexamples with safeguards; 9 defects of this phase's own work found and fixed with failing-before tests |

## Headline numbers (the same classifier applied to the V2.2 and V2.3 registers)

| Drawing | Questions already answered by an approved rule, still raised | Unresolved items | Owner questions |
|---|---|---|---|
| synthetic villa | 13 -> **0** | 51 -> 39 | 2 (OQ-02, OQ-03) |
| reference plan (no heights) | 66 -> **0** | 271 -> 213 | 3 (OQ-02, OQ-03, OQ-04) |
| reference plan (heights given) | 47 -> **0** | 230 -> 226 | 3 |

On the reference plan the share of blocked BOQ lines fell from 48 % to 33 % (no heights); released and provisional
lines rose accordingly; no quantity is negative; every line is in exactly one ledger record; nothing is a confirmed
omission. The 16 released doors there are all below the owner standard (+2.80 m of proposed enlargement in the
OWNER_REQUIRED view, never released).

## What is not claimed

- **No accuracy figure.** Nothing in this phase measures the BOQ against an independent take-off; the blind
  evaluation is not started (it needs separate owner authorization). No 95 % claim is made.
- **The full suite is not passing**: 345 failures and 32 errors remain - the same tests as the baseline (missing
  git-ignored datasets), with 0 new failures.

## Remaining owner questions (4)

OQ-01 pantry doorway threshold (conflict between two approved statements); OQ-02 head height of an enlarged wall
opening; OQ-03 stair-hall finishes; OQ-04 exterior scope. Everything else unresolved is a document request (B) or
engineering backlog (E). See `OWNER_QUESTIONS.md`.

## Next

The schedule / section reader (heights, window sills, door schedule) is the largest unlock; the blind evaluation is
the only route to an accuracy figure. See `ROADMAP.md`.
