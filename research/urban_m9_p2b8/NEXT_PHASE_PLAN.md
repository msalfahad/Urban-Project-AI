# Recommended next implementation phase (after Phase 2B-8)

**Position.** ARCH_TAKEOFF_V2.7.1 is an opt-in development method. A production freeze is **not** recommended before the blind second-villa round:
- one real plan cannot show general accuracy;
- 23 of 55 V2.6 → V2.7.1 changes on that plan are still only explained, not independently verified.

## Ranked work

| Rank | Work | Why now | Done when | Depends on |
|---|---|---|---|---|
| 1 | **Heights and sills from evidence** (D-04, D-C5, D-P8-06): read storey and ceiling heights, wall-tile height and window sill / head heights from sections, elevations and schedules; keep the facts file only as a labelled fallback | every plaster, paint, wall-tile, skirting-at-window, reveal and riser line rests on heights. It is the largest remaining source of error, and the main reason Mode U holds so much | on the reference plan the heights come from its sections, every value carries its source, and the independent reader re-reads them from the same sections | the sections in the drawing set |
| 2 | **Blind second-villa round** under the sealed URBAN_BLIND_V2 | the only route to an accuracy statement | reference committed, criteria approved, frozen V2.7.1 / V2.7 run once (Modes U and A), scored, every error classified | OD-P8-01, OD-P8-02 |
| 3 | **Verification coverage** (D-P8-04, D-P8-05): an independent passage rule (a gap with no symbol is a passage, deducted by its width); a declared rule for non-wall boundary layers (a glazed screen, a counter line), never taken from the engine; independent upturn and threshold checks with the rule parameters declared | a change the reader cannot check stays EXPLAINED_UNVERIFIED; the goal is to verify, not to explain | on the reference plan, at least 80 % of the V2.6 → V2.7.1 differences VERIFIED, 0 CONTRADICTED left unexplained, every unverified one with a stated reason | none |
| 4 | **Wall stubs and block walls** (D-P8-03, MAS.BLOCK): measure both-face stretches shorter than 0.30 m between openings as wall (QS practice), straight and curved; with heights (rank 1), block-wall areas by thickness | short piers and stubs beside openings are real masonry; block walls are BLOCKED_RFI today | stubs measured and reconciled with the arc / band census; block areas released where heights are evidenced | rank 1 |
| 5 | **Owner decisions into lines** (D-16, D-17): once answered, the door reading turns the reconciliation into required openings (still never applied to the as-drawn BOQ), and the type of each review space turns its conditional set into BOQ lines | the conditional sets are complete and tested; they wait only for the decision | the reference plan's 3 review spaces and 28 doors reconciled to the answers | D-16, D-17 |
| 6 | **Catalogue gaps**: roof and balcony finishes, external works and paving, formwork and excavation from the structural member geometry, a combined architectural + structural export | breadth of the BOQ | each family measured on the synthetic villa with hand truth, then on the reference plan | site and roof plans; structural route |

## Rules to keep

- Each change ships as a new opt-in method. The frozen methods stay byte-identical.
- Acceptance tests come first, written against hand truth or the independent reader, never against the engine's own output.
- The independent reader stays engine-free. Each new check gets its own hand-truth test, as in `test_p2b8_indep_reader.py`.
- A floor-wide correction record never explains a location its entities do not touch.
- Nothing about a second villa is committed or exported. The blind protocol's order is never broken.
