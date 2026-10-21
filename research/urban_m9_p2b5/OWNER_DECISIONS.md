# Outstanding genuine owner decisions (Phase 2B-5)

Only decisions the engine must not take for itself are listed. Each one names what it unblocks and the evidence
behind it. None was assumed in this program.

| # | decision | options | what it unblocks | evidence |
|---|---|---|---|---|
| 1 | floor-to-wall waterproofing junction detail | separate upstand (owner's B) at a stated flange; continuous fold (owner's A) | releases the V2.6 procurement figure (now PROVISIONAL_DETAILS_OPEN); a flange of 0.16 m or more adds a roll in the 3 x 4 m reference case | `V26_IMPLEMENTATION_REPORT.md`, `JUNCTION_ALTERNATIVES.md` |
| 2 | skirting in wet rooms whose wall tile is not full height (2.40 m tile, 3.00 m finish) | keep UP-CER-004's exception (skirting released) or apply "no skirting in wet rooms" | about 41 lm of skirting in the four wet rooms of the sample (D-C4) | `REAL_ROOM_VERIFICATION.md` §4 |
| 3 | finish scope of a doorless lobby merged into a wet room | wet scope (as now, without a note) or dry lobby | the lobby's share of the room's waterproofing and wall porcelain (44 % of the room's area in the sample) (D-C3) | idem |
| 4 | project heights (finish, wall tile, door, window) | supply project values (sections / schedules) or authorise labelled fallbacks | every wall-area line (plaster, wall porcelain, paint, masonry); the Mode A heights are synthetic test parameters (D-C5) | idem; UP-DOOR-HGT-001 |
| 5 | bathroom door openings below the owner standard | enlarge (structural / adjacent-trade check first, UP-DOOR-DEP-001) or accept the drawn openings | the three bathroom doors: 0.80 m CAD openings take a 0.70 m door; the 0.90 m standard needs +0.20 m (ENLARGEMENT_REQUIRED, UNRESOLVED) | door feasibility view |
| 6 | *(withdrawn in Stage G)* the width of the reconciled two-way door | - | the drawing settles it: the door symbol's own jamb lines are 0.80 m apart, the rest of the 1.023 m gap is a wall return and a wall crossing; applying it is an engine step (`ROADMAP.md` 1), not a decision | `REAL_ROOM_VERIFICATION.md` §8 |
| 7 | PyMuPDF licence | AGPL compliance (no distribution or network service to third parties) or an Artifex commercial licence | the vector-PDF route for PDF-only drawing sets (already used internally for PDF evidence) | `FLOORPLAN_AI_RESEARCH.md` §1, `LICENCE_ASSESSMENT.md` |
| 8 | offcut reuse and selection-order scope (N-7, N-9, from Phase 2B-4) | allow reuse of classed offcuts across areas / keep each area alone | the REUSABLE_SUBJECT_TO_N7 offcuts; no quantity is affected until decided | Phase 2B-4 audit |
| 9 | (optional) connect a CAD MCP server | which server, on synthetic fixtures first | an MCP benchmark row; native DWG without conversion | `MCP_SKILLS_AUDIT.md` |
| 10 | (optional) a trained floor-plan model | a commercially licensed or self-annotated training set, local inference only | scans: from review candidates towards measured rooms | `FLOORPLAN_AI_RESEARCH.md` §6 |
| 11 | whether a basin lobby (a space with wash basins and no WC) is a wet area under UP-WET-001 | wet (as the engine types it from its fixtures, flagged for review) or dry | the lobby's own wet scope (waterproofing, wall porcelain) and which room carries the doorway piece it shares with a W.C. | one lobby on the reference plan; `REAL_ROOM_VERIFICATION.md` §8 (G-F1) |

Not an owner decision, and therefore not asked: anything the drawing, a dimension or a rule already settles; any
test parameter; the engine's tolerances.
