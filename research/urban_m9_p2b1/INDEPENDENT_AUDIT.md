# Independent engineering audit - objections and remaining risks (WP-6; deliverable 14)

This audit challenges ARCH_TAKEOFF_V2.3 as an adversary would. It does not approve the implementation: each case
states what the engine does, whether that can produce a wrong quantity, the safeguard and what remains. Section 2
lists the defects the audit found in this phase's own work (all fixed with a failing-before / passing-after test).

## 1. Counterexamples (the owner's list and more)

| # | Case | What V2.3 does | Wrong quantity possible? | Safeguard | Remaining risk |
|---|---|---|---|---|---|
| 1 | An accessible bathroom door needs a wider clear opening | the bathroom standard (0.90 / 1.00) applies to every bathroom door | the OWNER_REQUIRED view under-states the enlargement | the OWNER_REQUIRED view is a proposal, never a BOQ line; a schedule width governs (precedence 1-2) | no accessibility attribute is read; a label / schedule flag is needed (roadmap) |
| 2 | An external-looking door leads into an enclosed connecting corridor | an unlabelled space with a doorless facade opening is POSSIBLY_EXTERIOR; its door is CLASS_REVIEW and withheld; a project decision settles it either way | a withheld door is absent from the released totals (shown in UNRESOLVED) | the connecting-space candidate is reported; one decision per space, bound by floor and point | until the decision is given the door count is incomplete, visibly |
| 3 | A main entrance is single-leaf | main-entrance identification does not depend on leaf count (entrance word in or near its space); a single-leaf door with no entrance word into a hall / living room is a candidate, withheld | an unidentified main entrance is not released | MAIN_ENTRANCE B request; candidates listed | a single-leaf main entrance opening into a room that is not a hall / living space and with no entrance word would be released as ordinary aluminium and given the 1.00 / 1.10 standard in the OWNER_REQUIRED view (a proposal only) |
| 4 | The wall opening is constrained by a structural column | dependency map: a column jamb -> STRUCTURAL_INTERFACE_REVIEW (one) / BLOCKS_ENLARGEMENT (two) | no - enlargement is never released | REVIEW_REQUIRED on every enlargement | only plan-visible columns are seen; a beam / lintel or a column on another drawing is not |
| 5 | A fully tiled room has a partially untiled feature wall | full-height porcelain on every face of a wet room | yes: wall tile over-stated, paint under-stated on that face | an explicit source height governs (facts) | facts heights are per floor and trade, not per face: a per-face override is needed (roadmap) |
| 6 | An elevator lobby door is mistaken for a lift landing door | a lift entrance needs a lift space or a lift door block; a candidate needs an opening into a SHAFT space; a lobby door is an ordinary door | low | the shaft must be a stacked footprint or carry a lift word; a door into a shaft is a CLASS_REVIEW (F-22) | a lift landing drawn as a door swing into an unlabelled, non-stacked space would be an ordinary door (labels required) |
| 7 | An assumed door height disagrees with a section | the section height is used when transcribed into the facts (SOURCE); otherwise 2.20 / 2.50 ASSUMED | an assumed area can be wrong, but it is never CONFIRMED | HEIGHT_ASSUMED / AREA_ASSUMED; the jamb plaster line is PROVISIONAL | the engine does not read sections itself; a section on the drawing set but not in the facts is not used |
| 8 | The CAD opening is the leaf, not the wall opening (some CAD conventions draw the door leaf only) | the CAD wall opening is the jamb-to-jamb gap of the wall band, not the leaf | if a drawing shows no jambs, the closure-based width is PROVISIONAL and the door is withheld | width source and state recorded per row; leaf and frame kept apart | none for band openings; closure-based widths remain provisional |
| 9 | The 0.10 m allowance differs from a manufacturer's installation detail | the owner rule is applied as a planning rule | the OWNER_REQUIRED view could be off by the difference | recorded in the rule as "not a verified manufacturer requirement"; a schedule value governs | none for released quantities (the view is a proposal) |
| 10 | A laundry is not a wet area in this project | LAUNDRY keeps the wet scope (as V1 .. V2.2) and is flagged WET_SCOPE_PROJECT_CONFIRMATION (B) | yes if it is dry: tile / waterproofing over-stated | the flag is a document request for the finish schedule | until answered the laundry is treated wet (unchanged from V2.2) |
| 11 | An open-plan kitchen | the dry treatment is kept and the zone line is requested (B) | yes: wet scope under-stated | flagged per space (OPEN_PLAN_WET_SCOPE_EXTENT) | needs a drawn zone or a finish plan |
| 12 | A door to a ground-floor terrace or garden | aluminium; still a possible main-entrance candidate when it opens from a hall / living space | it may be withheld as a candidate | V2.3 excludes balcony / roof doors only (an entrance can open onto a terrace or garden) | a terrace door from a living room is withheld until the main entrance is named |
| 13 | The main-entrance jamb plaster | the jamb plaster line uses the internal reference height (2.20 m) for every door without a source height | the main entrance jambs (2.50 m reference) are under-stated | PROVISIONAL line, HEIGHT_ASSUMED | a per-category height for jamb plaster (roadmap) |
| 14 | A pantry doorway | marble threshold measured PROVISIONAL with the conflict named (CF-03) | if the owner chooses porcelain, the marble line is wrong (small area) | OQ-01; PROVISIONAL, never released as confirmed | the question is open |

## 2. Defects found in this phase's own implementation (all fixed, regression-tested)

| # | Defect | Found by | Effect before the fix | Fix | Test (fails before, passes after) |
|---|---|---|---|---|---|
| D1 | several strip faces of one opening made one line each, with the same line id | the ledger conservation check on the reference plan | a doorway strip counted twice in the ledger; conservation failed | one line per opening, faces summed and named | `test_several_strip_faces_of_one_opening_make_one_line` |
| D2 | a project decision making a space INTERIOR still retyped its doors as exterior | reading the classifier while writing tests | an internal door would have become aluminium | only EXTERIOR decisions retype a side; any decided space leaves the "possibly external" set | `test_a_pantry_door_to_an_indoor_corridor_stays_pvc` |
| D3 | the stair-hall finish pattern was shadowed by a broader stair pattern | the per-entry catalogue examples | a genuine owner question (OQ-03) was filed as a document request | the broad pattern excludes stair halls | `test_every_catalogue_entry_is_reached_by_its_example` |
| D4 | the paint band above an explicit lower tile was classified "established" | the reference-plan question probe | an answered-rule count that was not true; the real conflict hidden | reworded as part of the tile-height conflict (C) | `test_an_explicit_lower_tile_height_wins_and_is_flagged` |
| D5 | the balcony upturn RFI line raised no unresolved item | test writing | the question would never reach the register | the RFI is raised and catalogued (B) | `test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed` |
| D6 | a balcony door was withheld as a main-entrance candidate | the balcony fixture | an aluminium door missing from released totals | V2.3: a balcony / roof door is never a main-entrance candidate | same test |
| D7 | owner question OQ-02 had a catalogue entry but no emitter | the dead-pattern test | an open policy gap never asked | raised once per run when an enlargement exists | `test_established_rules_are_never_asked` |
| D8 | strips left to the V2 register still asked for the finish UP-THR-001 answers | the reference-plan question probe | answered questions re-asked | reworded: the open item is the door (B) or the attribution (E) | `test_a_door_closure_strip_asks_for_the_door_not_the_finish` |
| D9 | three FINISH_SCOPE reasons matched no catalogue pattern | the reference-plan question probe | unclassified items | patterns added (B) | `test_an_unknown_reason_is_reported_unclassified_never_dropped` + catalogue examples |

## 3. Objections that remain open

1. **No accuracy measurement.** Nothing here measures the BOQ against an independent take-off. The phase changes
   what is measured and what is asked, under approved rules; it does not establish accuracy. No 95 % claim is made.
2. **Synthetic validation dominates.** Hand truth exists for the synthetic plans; on the reference plan the checks
   are invariants (conservation, no negative quantity, no released assumption, determinism, frozen identity), not a
   comparison with a reviewed quantity.
3. **Room function still depends on words.** A space with no word and no decisive connectivity is UNKNOWN /
   POSSIBLY_EXTERIOR and its doors are withheld. That is safe but incomplete.
4. **Per-face finish heights are not modelled.** Heights are per floor and trade.
5. **The owner-required view is narrow.** It covers doors only; no other owner-required modification is defined.
6. **Self-audit limits.** This audit was written by the implementer; an independent review of the registry records
   against the owner's original texts is still recommended before the blind evaluation.
