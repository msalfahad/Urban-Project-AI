# Baseline and gap audit (Phase N10)

## 1. Baseline verified

| Item | Reported | Verified |
|---|---|---|
| HEAD at hand-over | a5eeebe (Phase 2B-9 final) | a5eeebe is an ancestor of the branch head **504b56a** (the merge of the navigation-maps PR: 7 commits, 8 files, docs and tools only, no engine change). N10 starts at 504b56a |
| Guides | CLAUDE.md, docs/ROUTING.md, docs/CODEMAP.md, docs/RULES_INDEX.md, `tools/codemap.py route / impact` | used for every change; maps regenerated with `tools/codemap.py build` before each commit; `codemap.py check` reports no stale map at the final commit |
| V2.8 claims | heights from the drawing, opening schedule, reveals, wall geometry, curved faces | reproduced: the Phase 2B-9 final private snapshot is byte-identical for V1 – V2.8 at the N10 head (2,170 files, 0 differ) |
| Full suite | 9,331 tests, 345 failed, 32 errors (at 065f3de) | at 504b56a: **9,343 tests, 346 failed, 32 errors** (+12 codemap tests, all passing). Compared by test identity, the **one** new failure was the session guard: `tools/codemap.py` named the freeze verifier. N10 fixed it (dec6766) |
| Frozen integrity | `tools/freeze_verify.py check` | 0 frozen artefacts differ, at every N10 commit |

## 2. Gap matrix at the start of N10 (category → state → what N10 did)

| Category | State at 504b56a | N10 action | State after N10 |
|---|---|---|---|
| Curved wall openings (window, door, passage) | defect: the room closed at the glazing line (D-P9-02); curved glazing alone not a window (D-P9-01) | ARCH_TAKEOFF_V2.9: jambed curved gaps closed on both wall faces; glazing-layer inference | supported (V2.9, synthetic + reference plan) |
| Zone-bounded room verification | unverified (D-P9-04) | verifier: union of the reader's faces in the room; zone lines read by handle | verified (45 / 55 differences, 0 contradicted) |
| Masonry by thickness (m², m³) | BLOCKED_RFI | panel from the floor's T.O.S. → soffit; beam bottom → range; no beam evidence → held at the upper bound; material separate | partial (geometry measured with evidence; held on the reference plan) |
| Facade (run, area, finish) | absent | exterior outline run; F.F.L. → next F.F.L. area; finish held without a spec | partial (run measured; area needs section levels) |
| Floors, ceilings, wall finishes, skirting | supported / partial (V2.8) | unchanged except curved openings | unchanged |
| Doors and windows | supported (V2.8) | curved openings added | supported |
| Waterproofing | supported | unchanged | unchanged |
| Stairs | partial | unchanged | unchanged |
| Roofs and balconies | absent | not attempted | unsupported |
| Formwork | absent (NOT_IMPLEMENTED) | element faces from the route G register | partial / conditional (separate tool) |
| Excavation, backfill | absent (NOT_IMPLEMENTED) | footprints; volume only with stated levels | held (footprints measured) |
| Rebar mass | d²/162 used by route G | audit: unit mass vs d²/162, derivation of every row, ratio-as-measured check | audited (0 violations) |
| Independent verification | 32 / 55 (V2.6 → V2.7.1), 1 / 1 (V2.7.1 → V2.8) | + curved gaps, zone faces, outlines | 45 / 55, 1 / 1, V2.8 → V2.9 5 verified / 1 contradicted / 0 unexplained |

## 3. What was not attempted (and why)

- **Roofs and balconies.** No roof plan reader exists. Roof and balcony waterproofing are kept separate (owner decision), and nothing was invented for them.
- **Blind run.** The prompt forbids it. The sealed URBAN_BLIND_V2 protocol is unchanged.
- **Urban Projects Manager integration.** Excluded by the prompt.
- **Prices.** Excluded.
