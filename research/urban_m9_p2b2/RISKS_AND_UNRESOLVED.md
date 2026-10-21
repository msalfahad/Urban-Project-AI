# Risks and unresolved questions (deliverable 13)

Only genuine questions: nothing below asks the owner to reconfirm an approved standard (the roll, the lap, the 0.20 m
upturn, the door widths and heights, the elevator exclusion are applied as approved).

## 1. Risks of using ARCH_TAKEOFF_V2.4 outputs today

| # | Risk | Where it shows | Control in place | Residual |
|---|---|---|---|---|
| K-1 | The membrane roll count is read as a purchase quantity | MEMBRANE_CUTTING_PLAN, BOQ_SCENARIOS.WATERPROOFING_PROCUREMENT | PROVISIONAL with the reasons (system not specified, withheld details); never CONFIRMED on the owner roll alone | the count excludes doorway transitions, penetrations, corners and terminations until their details exist |
| K-2 | A proposed door enlargement is priced as if approved | DOOR_FEASIBILITY, BOQ_SCENARIOS.PROPOSED_MODIFICATION | status MODIFICATION_PROPOSED_NOT_APPROVED, separate view, approvals list | a reader who sums views by hand |
| K-3 | GEOMETRICALLY_POSSIBLE read as structurally approved | door schedule | the class name and the structural-engineer approval on every MASONRY_INDICATED door | the host-wall structure is inferred, not read (INDEPENDENT_REVIEW O-5) |
| K-4 | Window thresholds upturned where the window is floor-level | FIN.WP.WALL_UPTURN | WINDOW_TYPE_AND_SILL questions | the upturn line does not yet wait for the answer (O-1) |
| K-5 | Drains missing from the BOQ | FIN.WP.PENETRATION BLOCKED_RFI, NOT_SHOWN | count None, never 0; WP_PENETRATIONS_NOT_SHOWN | no drainage drawing is read |
| K-6 | A wrong project rules file applied | PROJECT_RULES_SHEET | the sheet lists every rule with its source; the hash changes | the file is not tied to the drawing hash (O-8) |
| K-7 | Mixing V2.3 and V2.4 outputs in one folder | OUT | a V2.4 run with a changed rules sheet moves the earlier outputs to SUPERSEDED_n; OUTPUT_MANIFEST.json binds each V2.4 file by SHA-256 | a V2.3 run into a folder holding V2.4 outputs overwrites the shared files and leaves the V2.4-only files in place, stale (V2.3 is frozen, so it was not changed); their manifest hashes no longer match - use one OUT folder per method |
| K-8 | The synthetic validation set is small | tests | 63 new tests incl. metamorphic, hand calculations, CLI | one real reference plan; exterior waterproofing proved on synthetic plans only |

## 2. Unresolved questions, by who answers them

### Owner (Urban standards - Level A)

| # | Question | Why it matters | Recommendation | Affects |
|---|---|---|---|---|
| N-1 | Is there one Urban standard waterproofing detail at a wet-to-dry doorway (upturn across the threshold / continuation terminated / jamb returns)? | every such doorway is open until a detail exists (3 on the villa, 15 on the reference plan) | an Urban default; projects override it | FIN.WP.DOORWAY_TRANSITION, procurement |
| N-2 | The minimum wall pier to keep beside an enlarged door opening | the engine uses a 0.10 m review threshold, labelled ENGINE_LIMITATION | owner value | door feasibility classes |
| N-3 | Showers: the 0.20 m upturn, or a higher upturn / full height inside the shower enclosure? (the rule-store shower rule UP-WP-004 1.1.0 is PROPOSED, not promoted) | shower walls are the most exposed wet surface | a shower rule; until then 0.20 m applies | FIN.WP.WALL_UPTURN in showers |
| N-4 | The 0.10 m overlap: side laps and end laps alike? | many sheet systems require a larger end lap | confirm, or give the end lap | layout, installed membrane |

Still open from Phase 2B-1 (not re-asked, listed for completeness): OQ-02 door head allowance, OQ-03 stair hall
finishes, OQ-04 exterior scope.

### Project documents (per project - Level B evidence, never assumed)

| Need | Unlocks |
|---|---|
| the membrane system (specification / data sheet) per location | a CONFIRMED roll count; corner / penetration treatments |
| the doorway and termination details | FIN.WP.DOORWAY_TRANSITION, FIN.WP.TERMINATION |
| the drainage / plumbing layout | FIN.WP.PENETRATION counts |
| the structural plan (load-bearing walls, lintels) | the host-wall structure of every door to be enlarged |
| the entrance label or door schedule | the main entrance class and its 2.50 m jamb height |
| the window schedule (types, sills) | window-threshold upturn, sills, glazing |

### Engineering (the next phase)

The independent review objections O-1 .. O-10 (`INDEPENDENT_REVIEW.md`); the roadmap orders them
(`ROADMAP_TO_95.md`).
