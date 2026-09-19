# A doorway is four facts

Your correction was right and the statement it replaced was mine:

> *"material_length_mm is the only length a quantity engine may read"*

That is true of actual material present and wrong for professional QS practice.
23010's own manual benchmark measures **gross** perimeter and deducts openings
later, so the door span belongs to the gross host-wall line even though no wall
material stands in it.

---

## A · Length ontology (`engine/lengths.py`)

| basis | includes | used by |
|---|---|---|
| `SPACE_BOUNDARY_LENGTH` | physical wall + supported portal closures | room polygon, floor area, room perimeter |
| `HOST_WALL_GROSS_LENGTH` | physical wall + wall-hosted opening spans | gross plaster, gross ceramic, gross blockwork — gross-then-deduct trades |
| `MATERIAL_PRESENT_LENGTH` | actual wall material only | trades genuinely needing existing material |
| `OPENING_LENGTH` | supported opening width | deductions, lintels, frames, thresholds |
| `SKIRTING_ELIGIBLE_LENGTH` | per approved skirting rule | skirting — **`RULE_REQUIRED`, not yet derivable** |

Every use declares its basis, and asking for an unestablished one **raises**:

> `SKIRTING_ELIGIBLE_LENGTH is not established for this interval. It is NOT
> zero — an unestablished basis and a measured zero are different facts, and a
> quantity built on the wrong one is wrong in a way nobody notices.`

Three portal boundary types, **not interchangeable**:

| type | space boundary | host wall gross | material |
|---|---|---|---|
| `HOST_WALL_OPENING_BOUNDARY` | > 0 | **> 0** | 0 |
| `OPEN_PLAN_VIRTUAL_BOUNDARY` | — | **0** | 0 |
| `OTHER_VIRTUAL_TOPOLOGY_BOUNDARY` | reserved | reserved | 0 |

Constructing an open-plan boundary with host-wall length **raises**: *"there is
no wall here to be gross about"*.

## B · Portal evidence combination matrix

You were right that GEOMETRY and TOPOLOGY are correlated — the same gap
geometry produces both *"there is a gap"* and *"closing it closes the room"*.
One observation seen twice is one observation.

| combination | status |
|---|---|
| GEOMETRY + SYMBOL | **VALIDATED** |
| GEOMETRY + DOCUMENT | **VALIDATED** |
| SYMBOL + DOCUMENT | **VALIDATED** |
| **GEOMETRY + TOPOLOGY** | **PROBABLE** (correlated) |
| GEOMETRY + SEMANTIC | PROBABLE |
| TOPOLOGY + SEMANTIC | CANDIDATE |
| any single family | **CANDIDATE — never more** |
| nothing | UNRESOLVED |

Unlisted combinations cap at PROBABLE with 3+ families, CANDIDATE otherwise.
**Nothing reaches VALIDATED by accumulating correlated observations.**

Width is now evidence only — the code says so explicitly: *"WIDTH IS EVIDENCE,
NOT A PHYSICAL RULE. Large openings exist."* A 6 m gap simply gets no support
from the span family; the others decide.

## C · Union-extension audit — implemented

| reason | count |
|---|---|
| `JUNCTION_OVERHANG` | **173** |
| `END_CAP_SUPPORTED` | 47 |
| `UNRESOLVED_EXTENSION` | **21** |
| total | 241 across 152 bands |

**Extensions crossing a supported portal: 0. The invariant holds.**

Each band now records `face_a_intervals`, `face_b_intervals` and
`both_faces_interval`, so a union can be audited rather than trusted.

## D/E · Length reconciliation

`HOST_WALL_GROSS = MATERIAL_PRESENT + supported HOST-WALL OPENINGS`

| space | closes | space boundary | **gross host wall** | material present | opening | identity |
|---|---|---|---|---|---|---|
| **BTH-05** | ✓ | 7.592 | **7.592** | 6.538 | 1.054 | ✓ |
| **BED-01** | ✓ | 22.268 | **22.268** | 20.919 | 1.349 | ✓ |
| BTH-01 | ✓ | 8.522 | 8.522 | 7.397 | 1.125 | ✓ |
| BTH-02 | ✓ | 8.802 | 8.802 | 7.570 | 1.232 | ✓ |
| BTH-03 | ✓ | 8.392 | 8.392 | 7.284 | 1.108 | ✓ |
| STR-01 | ✗ | 5.674 | 5.674 | 5.674 | 0.000 | ✓ |
| OPEN-01 | ✗ | 37.190 | 37.190 | 37.190 | 0.000 | ✓ |

BTH-05 is your worked example exactly: **6.538 + 1.054 = 7.592**.

The identity is **reported, not enforced** — an open-plan edge carries no host
wall, so it does not apply to every room.

## F · STR-01's 2606 mm — the answer is my error, not the drawing's

The east line has **one 0.36 pt stroke 378 mm away** and raster wall support of
**0.10**. There is genuinely nothing there.

Then the real cause:

| space | geometry type | region fills its bbox |
|---|---|---|
| **STR-01** | COMPOSITE_RECTANGLE | **67.6%** |
| BED-01 | COMPOSITE_RECTANGLE | 77.3% |
| OPEN-01 | CLOSED_POLYGON | 69.4% |
| BTH-05 | RECTANGLE | 89.4% |

**STR-01 is L-shaped. Its bounding-box east edge cuts through open space where
no wall was ever meant to be.** I was measuring the room against a rectangle it
isn't.

So the classification is **G/H — a defect in my expected-boundary model**, not
A–F. Every gap map is now flagged with its `bbox_fill_ratio` and a caveat below
85%. The fix — following the region outline instead of its bbox — is next
round's work, named rather than half-done.

This also means **BED-01's "3 of 4 sides at 100%" is partly luck**, and BTH-05
at 89.4% is the only near-rectangular control.

## G/H · Space-boundary results

Material graph: 42 components, 62 cycles, 145 termini, 0.0 mm drift.
Space-boundary graph adds 7 zero-material portal edges.

Five rooms close on the space-boundary model — BTH-05, BED-01, BTH-01, BTH-02,
BTH-03 — each on one ~1.1 m portal, with zero material invented.

**Per-room area accuracy is not reported this round.** The closures are
per-space interval models, not yet planar faces in the global space graph, so
an area comparison would be measuring the bbox rectangle rather than the room.
Given the bbox finding above, reporting areas now would compound the same
error. That is the honest state.

## I · Portals

7 PROBABLE, 10 CANDIDATE, 4 UNRESOLVED — now under the combination matrix, so
GEOMETRY+TOPOLOGY can no longer reach VALIDATED.

## J/K · Manifest

Extended with `space_boundary_graph` and `measurement_basis_version =
LENGTH_ONTOLOGY_V1`. Six stages, one run, coherent. The workbook still refuses
to build on a mixed or missing manifest.

## Recorded, not implemented

The material-engine principle is in `docs/ENGINEERING_INVARIANTS.md` §6:

```
VALIDATED QUANTITY → APPROVED CONSTRUCTION RECIPE → MATERIAL REQUIREMENT
  → PROCUREMENT ALLOWANCE → COST
```

Never AI-inferred from area. **CALCULATED and PROCUREMENT quantities always
shown separately.**

No pricing, no materials, no structural quantities, no BOQ, no production E34.
