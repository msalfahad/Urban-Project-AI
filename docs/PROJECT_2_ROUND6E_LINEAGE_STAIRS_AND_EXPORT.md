# ROUND 6E — stable lineage, stair completeness, a reproducible export

What an independent audit of the frozen 6C and 6D bundles found, what
each finding actually was when reproduced against the bundles, and what
this round changed. Nothing here prices anything, applies a waste factor
or writes a BOQ.

---

## §0 · The findings, reproduced before anything was changed

| # | The audit said | Reproduced against the bundles |
|---|---|---|
| 1 | ids move between rounds | 68 `physical_space_id` values appear in both bundles; 17 change area by >5%, 15 by >20%. Area **swapped** between ids: 26.58 m² from `PS-DR-004-014` to `-004`, 13.83 m² from `-015` to `-017` |
| 2 | the release state contradicts itself | a candidate carried `PARTIAL_SPACE`, `is_physical_space=false`, `may_release=false` **and** `RELEASE_ELIGIBLE_GEOMETRY` — the last of those came from the measurement layer and nothing revised it |
| 3 | a report number the export does not add up to | the 6D report and the 6D tables disagreed on a headline figure with nothing in the run noticing |
| 4 | the stair quantity is not the project's stair quantity | 3.2854 m² of tread on one four-tread run; the curved main stair was measured as SECONDARY, and 0 landings were exported |
| 5 | provenance | the manifests carried a short commit and a pile of hashes, and could not answer *was this built from committed code* or *is this file what that commit produces* |

The ids were the order the flood enumerated faces in. That is the whole
of finding 1, and it is why §4–§6 exist.

---

## §1, §2 · The export gate, and what a hash means

`engine/export_provenance.py`. Before a single table is written: the
worktree is `CLEAN`, `HEAD` in full, the **tree** hash, the tests as a
counted pass, and the input drawing hashed by its own bytes. An unclean
worktree is refused, because such a bundle cannot be reproduced from its
commit.

Every file carries **two** hashes: `RAW_FILE_SHA256` (the bytes — is
this the same FILE) and `CANONICAL_CONTENT_SHA256` (sorted keys, no
insignificant whitespace — is this the same ANSWER, however written
out). The manifest prints how to reproduce the bundle and what to
compare.

## §3 · One authoritative release state

`RELEASE_STATUS` is computed last, from everything the register knows.
The measurement layer's verdict sits beside it as `geometry_gate_status`
under a name that cannot be mistaken for it. `RELEASED_FOR_ROOM_QUANTITY`
may never coexist with `may_release=false`, `is_physical_space=false`,
`PARTIAL_SPACE`, `DRAWING_ARTIFACT`, `SUPER_REGION` or `UNRESOLVED`, and
a withheld candidate always says why. Synthetic cases **J, K, L** exist
to fail if it ever does. P7757: **0 contradictions**.

## §4, §5, §6 · Two ids, and a lineage computed from the frozen bundles

`engine/space_lineage.py`, seeded from the bundles that were actually
exported:

| | UNCHANGED | RESHAPED | ROLE_CHANGED | NEW | REMOVED | ids carried |
|---|---|---|---|---|---|---|
| 6C → 6D | 54 | 8 | 5 | 2 | 2 | 67 / 69 |
| 6D → 6E | 69 | — | — | — | — | 69 / 69 |

Nothing matches on area. A split gives **neither** child the parent's
id; a merge keeps **every** predecessor; where the evidence does not
settle it the answer is `UNRESOLVED_LINEAGE` and no id is carried.

## §7 · The report against the export

Ten headline numbers, each declared as an aggregation over a named table
and recomputed from the rows written: **REPORT_AND_EXPORT_AGREE**.
Neither number is ever adjusted to reach that.

---

## §8 – §13 · The stairs

**Coverage, per floor** — `STAIR_COVERAGE_FAILED` overall:

| floor | plans | observations | mapped | unresolved | assemblies | coverage |
|---|---|---|---|---|---|---|
| GROUND | DR-002 | 10 | 3 | 0 | 2 | INCOMPLETE (riser) |
| FIRST | DR-004 | 9 | 1 | 0 | 1 | INCOMPLETE (riser) |
| ROOF | DR-006 | 5 | 0 | 0 | 0 | **FAILED** |
| not established | DR-001/3/8/9 | 125 | 2 | 4 | 1 | INCOMPLETE |

Two of the four unresolved observations are LARGE against the staircases
the same drawings did reconstruct, and both are listed by id and area.

**The three staircases**, each measured once however many plans draw it:

| | configuration | role | floors | width | TREAD m² | NOSING lm | finish |
|---|---|---|---|---|---|---|---|
| PS-STAIR-001 | U_SHAPED | UNKNOWN | — | 1.956 m | NOT ESTABLISHED (flights overlap) | 11.714 | NOT CONFIRMED |
| PS-STAIR-002 | L_SHAPED (curved + straight) | **MAIN_INTERIOR** | GROUND → FIRST | 1.25 m | 5.4999 | 8.058 | project rule: marble |
| PS-STAIR-003 | STRAIGHT | UNKNOWN | GROUND only | 2.80 m | 3.2854 | 11.200 | NOT CONFIRMED |

The 2.80 m four-tread run is no longer the main stair of the building
(§9): a main stair carries a storey. The owner's marble rule is applied
to the interior roles it is about and not to a run whose kind the
drawings do not establish.

**Landings (§13).** The 11.93 m² Round 6D called a landing is 7.0 m long
beside a 1.25 m flight. It is reported as
`FLOOR_BETWEEN_THE_FLIGHTS_NOT_STAIR_M2`, split into a 10.27 m² floor
plate, a 1.66 m² piece the drawing does not settle, and a sliver.
**LANDING_M2 = 0.00** for P7757, and the synthetic case P proves a real
1.80 m² landing IS detected where the flights meet end to end.

## §14 · The search for a rise

The DWF's W2D streams carry `+0.15`, `+0.30`, `+1.00`, `+4.30`, `+5.50`,
`+9.70`, `+13.90`, `SECTION A-A`, `SECTION B-B` and four elevations.
This project has no W2D reader, so none of it can be attributed to a
floor or to a stair: **RISER_HEIGHT_NOT_ESTABLISHED**, with
`NO_READER_PLACES_THE_VERTICAL_EVIDENCE_THIS_SET_CARRIES` as what would
settle it. No rise is borrowed from a habit.

**Disclosed:** the same search surfaced area take-off totals printed on
the drawing (319.99, 208.20, 55.08, 583.27 m²). They are refused by name
as `REFUSED_IT_IS_A_TAKE_OFF_TOTAL` and appear in the
`VERTICAL_EVIDENCE` table as refusals. They were not used for anything.

## §15, §16 · Units, and the same square metre

Each stair figure in its own unit — m, pcs, m², lm — totalled only within
a unit. m² + lm + pcs is never written. `MARBLE ∩ PORCELAIN = 0.0000 m²`,
measured as the intersection of the released room floor with every stair
footprint and landing over 6 released rooms and 4 stair parts.

## §17, §18 · The pantry stands

P7757's pantry remains `PANTRY_OPENNESS_UNKNOWN` with an owner rule
request. The 2.25 m² false pantry stays rejected, and the 2.70 m²
`PARTIAL_SPACE` is not presented as the pantry.

## §19 · Seventeen synthetic cases, frozen before P7757

A–H and Q on identity, I–L on the release state, M–N on report
consistency, O–P on stairs. J, K, L, N and Q exist to fail if the engine
ever says otherwise. **17/17 pass before the rerun.**

## §20, §21 · The register, and the bundle

| | 6C | 6D | 6E |
|---|---|---|---|
| MEASURED_CANDIDATE_AREA_M2 | 269.1838 | 279.7944 | 279.7944 |
| MEASURED_CANDIDATES | 40 | 43 | 43 |
| RELEASE_ELIGIBLE_GEOMETRY_AREA_M2 | 26.3085 | 26.3085 | 26.3085 |
| RELEASE_ELIGIBLE_GEOMETRY | 6 | 6 | 6 |

The geometry did not move this round; what moved is what can be said
about it. `P7757_ROUND6E_EXPORT.tar.gz` carries the nineteen named
tables, the six carried from 6D, the report and the manifest with its
provenance block.

## Owner rule addendum, 2026-09-17 — what it changed in this round

The owner's addendum arrived after the first 6E bundle. It is recorded in
`data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json` (14 rules, versioned,
dated, sourced) with P7757's own answers in
`data/registry/P7757_PROJECT_RULES.json`, and three of its rules changed
what this round reports.

**§A, §B — the pantry.** P7757's pantry is `OPEN_AMERICAN_PANTRY` by the
owner's confirmation, and the engine now says so with the evidence
`THE_OWNER_CONFIRMED_THIS_PANTRY_FOR_THIS_PROJECT` instead of
`PANTRY_OPENNESS_UNKNOWN`. The confirmation settles *which* answer is
true and supplies no geometry: the pantry label still resolves to no
physical space in the drawing, so the tiled walls are
`PANTRY_TILE_WALLS_REQUIRE_OWNER_REVIEW` with
`WALL_TILE_LENGTH = 0.00 m` — not the perimeter of the space it sits in,
which belongs to the dining as much as to the pantry. The tile height
remains an `OWNER_RULE_REQUEST`.

**§C — the stair finish.** The marble rule now reaches **every** stair
assembly the engine detected, not the interior roles only: all three
P7757 staircases carry `STAIR_MARBLE_SURROUNDING_FLOOR_PORCELAIN` from
`UP-STAIR-001@1.0.0`, applied through the owner's project override.
Role detection is unchanged and still separate — the 2.80 m four-tread
run is marble *and* `STAIR_ROLE_UNKNOWN`, because what it is and what it
is finished in are two questions.

**§E — the visible riser.** `RISER_VISIBLE_M2` is now its own quantity:
the step rise less the tread build-up, times the width. For P7757 both
the rise and the build-up are unestablished, so it reports
`VISIBLE_RISER_HEIGHT_NOT_ESTABLISHED` rather than a number. The owner's
0.516 m² per step is in the tests as arithmetic, never as a constant.

**§F.** `GEOMETRIC_MEASUREMENT_UNIT` and
`CONTRACTOR_COMMERCIAL_PRICING_BASIS` are separate fields on the stair
quantity table; P7757 has no commercial basis stated, so it reads
`CONTRACTOR_PRICING_BASIS_NOT_ESTABLISHED`.

**§H–§L — the elevator.** `engine/elevator_marble.py` declares
`ELEVATOR_LANDING_MARBLE_ASSEMBLY`, `ELEVATOR_DOOR_SURROUND` and
`ELEVATOR_THRESHOLD_MARBLE` with the owner's method — the surround as the
union area of its polygon (3.10 m² for the worked example, against 2.60
and 3.60 for the two naive ways of getting it wrong) and the threshold as
its own object with its depth asked for. **No elevator is detected in any
drawing**: P7757 reports `ELEVATOR_STATIONS_NOT_ESTABLISHED`, and the
full elevator BOQ waits for the trade phase.

## §22 · What this round did NOT start

No TradeMeasurementZone, no ceramic BOQ, no waste rule, no pricing, no
manager or Firebase integration.
