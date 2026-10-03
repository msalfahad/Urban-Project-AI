# Project 2 — round 2: enclosure role and room-seed qualification

```
PROJECT_2_CAD_ROUND2_HASH         70e2f4c34a6b1374687fb20f

ENCLOSURE_ROLE_CLASSIFIER_HASH    844448ed7de88dea5c27ac75
SEMANTIC_SEED_CLASSIFIER_HASH     64c01b36653f579fafc113a0
WALL_ROLE_HASH                    e2ed8a68a37d1ed74d7e2e18
ROUND_2_SYNTHETIC_HASH            de1caf07e16e738b3e34dcc5
                                  (12 cases, 12 passing, safety held)
```

> **Correction to an earlier statement.** I first reported
> `ROUND_2_SYNTHETIC_HASH` as `e9d66302a8d917ebb6176eb9`. That was the
> value **before** the `%%p` escape-regex fix, which changes
> `SEMANTIC_SEED_CLASSIFIER_HASH` and therefore the synthetic hash built
> from it. The frozen run always recorded the correct post-fix value; only
> the prose was stale. The hashes above are the ones in
> `data/runs/7757/P7757_CAD_round2.json`.

**Round 1's baseline is preserved untouched.** `P7757_CAD_baseline.json` is
byte-identical (`8323169dcad1053a`) and still records
`PROJECT_2_CAD_BASELINE_HASH 3edf12c66f0984330d77e248` with its two false
releases. It has not been rewritten, replaced or corrected — it is the
record of what the engine did then.

---

## The result

```
PRIMARY SUCCESS CRITERION      zero site / building / super-region
                               polygons released as rooms

round 1     48 candidates   2 complete   2 RELEASED   both were the plot
round 2     33 candidates   2 complete   0 RELEASED
```

**Met.** And met by structure, not by a size test: the two polygons that
round 1 released are still measured, still complete, still 205.910 m² and
443.841 m² — and both are now `UNRESOLVED`, blocked by
`ENCLOSURE_ROLE_IS_UNRESOLVED`.

### What actually caught them

Not the super-region test, as I expected. The **interior-void** test:

```
CADSP-009   443.841 m2   labelled W.C
  contains 2 room-like observation(s)      (its own English/Arabic pair)
  0 drawn partitions between them
  6 INTERIOR VOIDS  - the flood could not enter six enclosed things
                      inside this polygon. They are the building's rooms.
```

A polygon with a hole has something inside it. Whether that something is a
courtyard, a shaft, a stair core or a column cannot be settled without
comparing sizes, and comparing sizes is forbidden here — so the enclosure
is `UNRESOLVED` rather than guessed at.

This is **deliberately conservative**: a room with a column in it will not
release either. That is the intended trade, and §11's rule is why — *false
release is worse than zero release*.

The super-region test did not fire on these two because their only
observations are one room stamp's English and Arabic strings at nearly the
same point, so no material lies between them. Having two independent
structural tests is what made the difference.

---

## §2 · Enclosure role ontology

`SITE_OR_PLOT_ENCLOSURE · BUILDING_ENVELOPE · PHYSICAL_ROOM_CANDIDATE ·
VOID_OR_SHAFT · DETAIL_OR_ANNOTATION · SUPER_REGION · UNRESOLVED`

Only `PHYSICAL_ROOM_CANDIDATE` is releasable. The decision is containment,
which is scale-free — it fires the same way on a 2 m² shaft and a 500 m²
plot:

| evidence used | evidence never used |
|---|---|
| room observations contained | area |
| other enclosures contained | principal dimension |
| drawn material separating those observations | expected room size |
| interior voids in the polygon | layer or block name |
| what contains it | number of rooms expected |

A test asserts `area_m2` does not appear in `engine/enclosure_role.py`.

## §3 · Super-region invariant

> A candidate containing several independently supported physical-space
> observations **separated by supported partitions** cannot be released as
> one physical room.

Implemented as a topological question — *can you walk from this label to
that one without crossing drawn material?* — so it needs no size
comparison. Case D asserts it fires; case E (open plan, two zone labels, no
partition) asserts it does **not**, which is what distinguishes a
super-region from one open space.

## §4 · Room label ≠ room

```
TEXT_OBSERVATION  ->  SEMANTIC_SPACE_OBSERVATION  ->  SPATIAL_SEED  ->  PHYSICAL_SPACE
```

Classes: `ROOM_LIKE · ZONE_LIKE · NON_SPACE_ANNOTATION · AMBIGUOUS`.
Ambiguous releases nothing.

The tests are structural and language-independent. **No string from P7757
steers any decision** — asserted two ways: an AST check that no real word
appears in a string literal the classifier can act on, and a behavioural
check that `SALOON`, `KITCHEN`, `NEIGHBOUR`, `STREET`, `SEA VIEW`, `W.C`,
`PANTRY`, `GARDEN`, `DRIVER` each classify **identically to the nonsense
word `QQZZX`** in the same position.

| test | what it removes |
|---|---|
| **a room is not named by a number** (once CAD decoration is stripped) | levels, plot dimensions, setbacks — in any language |
| **a scale ratio marks a title** | `… 1:100` |
| **text not carried by a placed symbol** | loose notes → AMBIGUOUS |
| **outside the built fabric** | streets, neighbours, views — from geometry the caller supplies |

On P7757: **19 observations rejected as NON_SPACE_ANNOTATION**, all by the
numeric test (`31.37`, `15.00`, `+0.15`, `%%p0.00`). 2 AMBIGUOUS (loose
text). Candidates fell 48 → 33.

## §5 · Seed qualification

A label says **where** a space might be and **what** it might be called. The
boundary comes from geometry alone. `L_LABEL_WITH_NO_VALID_ENCLOSURE`
asserts a room-like label with no enclosure around it releases nothing.

## §7 · Wall role, second stage

`SITE_BOUNDARY · BUILDING_EXTERNAL_WALL · INTERNAL_PARTITION ·
OTHER_ARCHITECTURAL_WALL · UNRESOLVED`, decided by what occupies each side
at a 1 m probe. No layer number appears in the module; a test asserts it.

```
SITE_BOUNDARY             2400
OTHER_ARCHITECTURAL_WALL   258
INTERNAL_PARTITION         219
```

**These figures are weakly grounded and should not be read as a finding.**
The occupancy test is defined by the measured enclosures, and only two
enclosures exist — so "nothing occupied on either side" is true of almost
every band for lack of measured space nearby, not because it bounds ground.
The classifier is correct; its input on this source is thin.

---

## §10 · P7757 rerun, without benchmark

| | round 1 | round 2 |
|---|---|---|
| drawing regions (finest stable partition) | 14 | 14 |
| semantic observations | — | 89 |
| permitted to seed (ROOM_LIKE) | 100 (unfiltered) | **68** |
| rejected annotation seeds | 0 | **19** |
| ambiguous | 0 | 2 |
| space candidates | 48 | **33** |
| complete | 2 | 2 |
| partial | 0 | 0 |
| unresolved | 46 | 31 |
| identity established | 15 | **0** |
| **release-eligible** | **2 (both false)** | **0** |

Enclosure roles: `UNRESOLVED` × 2 (the only two enclosures that formed).
Site/plot candidates: 0. Building-envelope candidates: 0. Super-regions: 0.
Physical-room candidates: 0.

Blockers:

```
A_WHOLE_SIDE_HAS_NO_DRAWN_LINE      31
ENCLOSURE_ROLE_IS_UNRESOLVED         2
```

**No released physical rooms, so the per-room table in §10 is empty.** That
is the reported answer, not a gap in the report.

### Why identity_established fell from 15 to 0

The gate now treats `IDENTITY_AMBIGUOUS_MULTIPLE_LABELS` as a blocker, and
every room stamp on this drawing carries an English and an Arabic string.
They are **one room's name in two languages**, not two identities — the
defect I named in round 1 and did not fix, because fixing it was
development rather than the structural correction this round was for. It
costs nothing today (nothing reaches that gate) and must be fixed before
any room can release.

---

## §12 · Success criteria

**Primary — zero false releases: MET.** Both round-1 false releases are
blocked, and the twelve synthetic cases assert that no site, building
envelope, super-region or drawing frame can be released as a physical room.

**Secondary — does the new topology create smaller, locally supported
room candidates without P7757-specific tuning? NO, not yet.** The count of
complete enclosures is unchanged at 2. Round 2 removed a class of wrong
answer; it did not add right ones. The remaining blocker is unchanged and
was named in round 1: **the wall-candidate set still includes the site
layer**, so a flood escaping a room still runs to the plot boundary instead
of stopping at a room wall. The wall-role classifier now exists to fix
that, but wiring its output back into the candidate set is a change to
measurement, and this round was for safety.

That ordering is deliberate. A round that both removed false releases and
added real rooms would leave it unclear which change did which.

---

## Anything that required a P7757-specific rule

**Nothing. The list is empty.**

- No layer-name exclusion, block-name allowlist, room-name allowlist,
  coordinate box, expected room count, expected area, or size threshold
  exists anywhere.
- The `31.37 × 15.00` plot is blocked by interior voids, not by knowing
  those numbers. Its own dimensions are never read.
- Every constant states its justification: partition material ≥ 500 mm
  (shorter than any built partition, longer than a dimension tick), probe
  offset 1000 mm (wider than any wall the profile admits, narrower than any
  room).
- The enclosure freeze `01ff128e7ffdab820805dce1` is untouched, and both
  round-1 freezes (`bd331c8074806e8b19711417`,
  `b0bf6a13f057aa1578262e3c`, 29 fixtures) still pass.

### Two defects the round-2 fixtures caught in my own work

1. **A green board that meant nothing.** The first synthetic check asserted
   on the enclosure's *role*, so when the classifier called a 450 m² site
   polygon a `PHYSICAL_ROOM_CANDIDATE`, case C passed while releasing
   exactly what it existed to forbid. The checks now assert on **what was
   released**.
2. **The `%%p` escape regex was greedy** — `[a-z0-9]{1,3}` ate the digits it
   existed to expose, so the level mark `%%p0.00` was left as `.00` and
   failed the number test. One character now.

---

## Not opened

No human Excel, no كيال, no architect area take-off, no structural or
sanitary quantities, no paint, masonry, ceramic, waterproofing or
aluminium. 43 new tests, all passing.
