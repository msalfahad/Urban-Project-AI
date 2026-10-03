# Project 2 — round 4: openings, and the drawings they belong to

```
PROJECT_2_CAD_ROUND4_HASH        75d831180085a81a2b38506f

DRAWING_REGION_HASH              bd1c391980507d3e18f5d9db
CAD_OPENING_CLASSIFIER_HASH      336c6f1bc5bb0a3ea42bb698
PORTAL_MATCHER_HASH              42e7bb997ecbad74fa58e2cf
ROOM_PARTITION_GRAPH_HASH        6bd4f2ff9ac748948e441baa
ROUND_4_SYNTHETIC_HASH           f025dbe323a251a75b7dcc42   22/22 passing
LOCAL_ENCLOSURE_HASH             01ff128e7ffdab820805dce1   (unchanged — the
                                 frozen enclosure still does the measuring)
```

Preserved, and verified against the files that hold them:

```
PROJECT_2_CAD_BASELINE_HASH  3edf12c66f0984330d77e248  P7757_CAD_baseline.json
PROJECT_2_CAD_ROUND2_HASH    70e2f4c34a6b1374687fb20f  P7757_CAD_round2.json
PROJECT_2_CAD_ROUND3_HASH    e95a4c3c4a298339d9e0adb1  P7757_CAD_round3.json
ROUND_3_SYNTHETIC_HASH       20fd3ed87d05f40ba6cf6123  recomputes identically
```

Each Project-2 hash is a property of **the run that produced it**, and it
lives in that run's artefact, untouched. Round 4 changes what is measured,
so recomputing those chains over round-4 geometry gives different numbers —
they are reported separately under `recomputed_under_round_4` and they are
NOT the preserved values. `ROUND_3_SYNTHETIC_HASH` is the one that is a
property of the CODE rather than of a run, and it still computes to the
same value today.

---

## The result, stated plainly

**Round 4 moved the geometry and did not move the release.**

```
                         round 3      round 4
complete physical spaces       2           36
release-eligible               0            0
false releases                 0            0
synthetic cases          16 / 16      22 / 22   (plus rounds 2 and 3: 50/50)
```

Thirty-six bounded physical spaces are now measured on P7757 where round 3
measured two. None of them may be quantified from, and §17 says report that
rather than tune until a number appears.

**What blocks the release is now a different thing, and it is located.**
Round 3's blocker was `A_WHOLE_SIDE_HAS_NO_DRAWN_LINE` on 31 of 33
candidates — rooms that would not close at all. That has gone. The blocker
now is that the closed faces are the WRONG SHAPE: on the one plan that
carries readable room stamps, the whole interior polygonises as **one
194 m² face containing all 38 label observations**, because 145 grade-D
gaps and 163 ambiguous portal hosts leave its internal partitions
perforated, and a single unclosed gap merges two rooms into one.

---

## §1 · The drawings, isolated first

`STABILITY_SELECTED_DRAWING_REGION_ISOLATION_V1`

Round 3's own report named this gap: it found **0 site bands on P7757**,
because "the outermost boundary of everything the lines enclose" spanned
all twelve drawings at once. Every one of those tests is now local.

No distance is chosen. The frozen ladder sweep reports where the partition
is stable; this round adds a stated **selection rule** — the most stable
plateau, ties to the finer partition, the rung nearest that plateau's
geometric middle — and one structural correction: **a group lying wholly
inside another group's extent is merged into it.** A plot boundary and the
villa inside it are one drawing, and separating them would hide the site
line from the building it encloses.

Ties go finer on purpose. Splitting one drawing in two costs measurement.
Merging two INVENTS relationships. Those costs are not symmetric.

P7757 at the selected rung (800 mm, on the 400–800 mm plateau):

| region | marks | size | texts | dims | blocks | arcs |
|---|---|---|---|---|---|---|
| DR-001 | 2698 | 40.3 × 28.0 m | 0 | 49 | 103 | 10 |
| DR-002 | 1907 | 40.3 × 28.0 m | **59** | 118 | 316 | 305 |
| DR-003 | 1590 | 40.3 × 28.0 m | 0 | 51 | 107 | 8 |
| DR-004 | 1464 | 40.3 × 28.0 m | 14 | 121 | 284 | 79 |
| DR-005 | 853 | 3.0 × 3.5 m | 0 | 0 | 0 | 0 |
| DR-006 | 700 | 40.3 × 28.0 m | 14 | 50 | 117 | 36 |
| DR-007..009 | 157 | small | 4 | 0 | 6 | 13 |

Five plans of the same footprint, 45 m apart along one strip, plus four
small fragments. The same rooms recur across regions with the same areas
(15.36 m², 12.91 m² in five of them) — which is the isolation working, not
a duplication bug. **Floor naming stays UNKNOWN**, as §1 permits.

## §2–§5 · What the holes are, and what each grade may do

`CAD_OPENING_EVIDENCE_CLASSIFIER_V1`

```
GRADE A   one transformed INSERT supplies the door, and the reveals agree
GRADE B   a leaf or a swing, in a supported wall interruption
GRADE C   the wall is pierced and its reveals are drawn — but no door is
GRADE D   a gap, and nothing else
```

`MAY_CLOSE_BOUNDARY_FROM = GRADE_C`, `MAY_PARTITION_FROM = GRADE_B`, doors
only. **A grade-D wall gap closes nothing, anywhere, ever** — a test
asserts it across all twenty-two drawings, and P7757's 145 grade-D
hypotheses closed nothing.

The class comes from the evidence, never from the width. There is **no
table of plausible door widths** in the module and a test asserts there is
none: a 2.4 m opening with a leaf and an 800 mm opening with a leaf are
both `DOOR_WITH_LEAF`, and the same two holes without a leaf are both
something else.

Every tolerance is an earlier round's frozen constant — the enclosure's
junction reach and collinearity tolerance, the profile's wall-thickness
band. A test asserts each equality. **No new number was introduced.**

## §4 · Three widths, compared and never averaged

```
GEOMETRIC_OPENING_WIDTH_MM     jamb to jamb, from the drawn faces
BLOCK_NAME_WIDTH_OBSERVATION   the digits in the name, read BOTH ways,
                               with "which reading agrees" — authority NONE
DIMENSION_WIDTH_OBSERVATION    an authored dimension bracketing the gap
```

On the synthetic door block `D90` against a 900 mm measured opening, the
name is reported as raw `90`, as 90 mm, as 900 mm, and the verdict is
`AS_CENTIMETRES`. The geometry is the measurement; the name cross-checks
it. A block named `D090` whose geometry pierces nothing produces no door at
all — a test holds that.

## §6, §7 · Three topologies, and a doorless opening that decides nothing

Through the frozen `space_topologies` model, unchanged. A validated door
closes the room boundary with `MATERIAL_PRESENT_LENGTH = 0`, is navigable,
and establishes `TWO_DISTINCT_PHYSICAL_SPACES`. A **doorless archway closes
the polygon and leaves the relation `ROOM_PARTITION_RELATION_UNRESOLVED`**,
which blocks release and asserts neither one space nor two. A **window
closes the boundary, is NOT navigable, and never becomes a room-to-room
passage** — tested on every fixture.

## §8 · Several labels in one face

One physical space, `FUNCTIONAL ZONE` per identity, `identity_status =
IDENTITY_IS_SEVERAL_FUNCTIONAL_ZONES`, no release, **no manufactured wall
and no discarded identity.** Case H: `KITCHEN` and `DINING AREA` in one
face produce one space, two zones, zero openings. P7757 has 3 such groups.

## §11 · Geometry first, names afterwards

`REGION_LOCAL_ROOM_PARTITION_GRAPH_V1`

The order is inverted from every previous round. The region's eligible
bands plus the portals that earned the right to close something are
assembled into one local arrangement; **its bounded faces ARE the
physical-space candidates**; the frozen enclosure measures each from a
point inside it; identity is attached last.

A face whose **mean thickness** (twice area over perimeter) is no more than
the profile's own maximum wall thickness is the inside of a wall, not a
space. A bounding box will not do this: a perimeter wall's ring has the
bbox of the whole building and is still 200 mm of blockwork.

An unlabelled bounded face reports `PHYSICAL_SPACE_VALIDATED_IDENTITY_-
UNKNOWN`. It may not RELEASE — round 2's safety is untouched, and a face
with no label can never be a `PHYSICAL_ROOM_CANDIDATE` — but refusing to
admit it exists was what made measurement hostage to the text layer. On
P7757 that is 30 of the 36 spaces.

## §12 · A host, an ambiguity, or nothing

Six named checks, no global nearest-wall search. Where two openings claim
the same door geometry the answer is `PORTAL_HOST_AMBIGUOUS`, which blocks
release through that portal and does not decay into a guess. Case O — one
swing at a corner where a vertical and a horizontal wall are both pierced
under it — produces two ambiguous hosts and releases nothing through
either.

---

## §13 · Twenty-two synthetic drawings, frozen before P7757

`ROUND_4_SYNTHETIC_HASH f025dbe323a251a75b7dcc42` — 22/22, with rounds 2
and 3 still at 12/12 and 16/16 under the same code.

```
A two rooms, one hinged door          M door block scaled 1.2
B two rooms, double door              N nested door INSERT
C room with an external window        O opening near two possible hosts
D two windows and a door              P window symbol in an interruption
E wall gap with no door evidence      Q site gate in a plot boundary
F wide doorless opening               R building entrance door
G archway between two identities      S swing touching no wall
H open plan, no separator             T annotation arc resembling a swing
I corridor, doors to three rooms      U two unrelated drawing regions
J unlabelled room with a door         V external wall + partitions + door
K bilingual labelled room, door
L door block rotated 90 degrees
```

Every required result holds: a wall gap never becomes a validated portal; a
window never becomes a room-to-room portal; a site gate never becomes an
internal separator; a door opening does not leak adjacent rooms; open-plan
geometry is not artificially split; transformed and nested inserts resolve;
no portal matches across a drawing region; an unlabelled physical room is
still measured; **false release remains zero.**

---

## §14 · P7757, after the freeze. No benchmark opened

```
DRAWING_REGION count                      9
wall-boundary candidates               2877   (wall-like before authority 2877)
door candidates                          60
window candidates                        71
validated portals                        60
openings that may close a boundary      135
doorless openings                         4
unresolved gaps                          99
ambiguous portal hosts                  163
room-partition graph cycles             746
physical-space candidates                36
complete spaces                          36
partial spaces                            0
unresolved spaces                         0
identity established                      1
identity unknown                         32
functional-zone groups                    3
release-eligible                          0
false / super-region rejections           0
```

```
openings by class                    openings by grade
UNRESOLVED_WALL_GAP      99          GRADE_D  145
WINDOW_OPENING           71          GRADE_C   75
DOOR_WITH_LEAF           60          GRADE_B   56
NON_OPENING_GEOMETRY     60          GRADE_A    4
UNKNOWN                  46          (no opening evidence) 60
DOORLESS_ARCHWAY          4

portal hosts: HOST_ESTABLISHED 177 · PORTAL_HOST_AMBIGUOUS 163
door symbols matched to no interruption at all: 233
```

### §15 · The complete spaces

36 complete, 0 released. Blockers:

```
ENCLOSURE_ROLE_IS_VOID_OR_SHAFT    30      no readable label inside the face
ENCLOSURE_ROLE_IS_UNRESOLVED        6      several labels, or an interior void
```

| space | region | area m² | labels inside |
|---|---|---|---|
| PS-DR-001-001 | DR-001 | 1032.8 | 0 |
| PS-DR-003-001 | DR-003 | 959.7 | 0 |
| PS-DR-004-001 | DR-004 | 631.2 | 4 |
| **PS-DR-002-001** | **DR-002** | **194.0** | **38** |
| PS-DR-004-004 | DR-004 | 141.4 | 2 |
| PS-DR-003-004 | DR-003 | 23.1 | 0 |

**PS-DR-002-001 is the finding.** One 194 m² face holds every room stamp on
the labelled plan — `SALOON`, `KITCHEN`, `MASTER BED ROOM`, `DEWANEYA`,
`RECEPTION`, `DINING`, `PANTRY`, `DRIVER`, four `W.C`, and their Arabic
pairs. The internal partitions are drawn, and they are perforated: 99
unresolved gaps and 163 ambiguous hosts mean the arrangement never divides
the interior. One unclosed gap merges two rooms, and merging cascades
across a floor.

Full per-space records — boundary trace with CAD provenance and material
vs virtual, opening table with class, grade, three widths and all three
topologies, quantity ontology, and identity kept separate — are in
`data/runs/7757/P7757_CAD_round4.json` (`complete_physical_spaces`, file
sha256_16 `2d9028a7831db27b`).

### §16 · The dimension cross-check, and the first thing it has ever agreed with

```
72 associations   AGREE 11   DISAGREE 0   AMBIGUOUS 0   NOT_PRESENT 61
```

Eleven authored CAD dimensions bracket a measured span and agree with it to
within a millimetre, with `DIMLFAC = 0.1` applied and the three values kept
apart throughout. **This is the first time on this project that authored
dimensions have independently confirmed a measured polygon.** No dimension
was required for release, and none corrected any geometry.

### §17 · Success criteria

**SAFETY — met.** 0 site / building / super-region false room releases, on
P7757 and across all 50 synthetic cases.

**PORTAL SAFETY — met.** 0 unsupported wall gaps converted into validated
room portals. 145 grade-D hypotheses on P7757 closed nothing.

**MEASUREMENT — partially met.** The first locally supported physical-space
polygons from authored wall + opening topology exist: 36 of them, 2 → 36.
None is release-eligible, and the reason is stated above rather than tuned
away.

No target room count was used. Zero released rooms is the reported answer.

---

## K · Everything introduced or changed after inspecting P7757

**This section is longer than round 3's, and it should be read carefully.**
Five changes were made to code after looking at P7757's round-4 output.
Every one is a correctness fix that also changes a synthetic result, and
none contains a number taken from this drawing — but they were all
FOUND by looking at it, and that is the disclosure.

1. **One opposite face, not all of them.** The first classifier accepted
   every parallel line inside the wall band as a face of the same wall. A
   wall near two others collected three faces, the opening's extent spread
   across the lot, and the same door symbol was claimed by several
   openings — 638 of 841 hosts came back ambiguous. It now takes the single
   best opposite face, by interval overlap.

2. **A door symbol must span its opening.** `CAD-133` is a 10.23 m wall
   line on layer `1`. It ended near a jamb, so it was read as a door leaf,
   and it graded doors across the drawing. A leaf now has to account for
   the opening: leaf (or leaves) plus the measured frame inset either side
   must equal the measured width, within the frozen reach. This compares
   two lengths measured on the drawing; it contains no idea of how wide a
   door ought to be. Before this rule a 9.45 m gap graded GRADE_B and
   released a 5.5 m² "room" whose entire boundary was opening.

3. **The symbol sits IN the opening, not ON its corner.** The first rule
   required a swing centre to coincide with a jamb point within the frozen
   50 mm reach. **P7757's door leaves hang 60 mm inside the reveal** — a
   frame lining — so almost every real door missed by ten millimetres. The
   test is now containment in the opening's own footprint, grown by the
   thickness of that same wall. I did not raise 50 to 60: that would have
   been this drawing's number. But I would not have found the rule without
   this drawing, and the allowance is now a measured property of each wall.

4. **A gap narrower than the wall it pierces is a break in a line.**
   Forty-two of DR-002's interruptions are about 200 mm wide in 200 mm
   walls. Nothing passes through an opening narrower than the wall around
   it, so these are classed `NON_OPENING_GEOMETRY`. They are **not
   bridged** — 60 such on P7757, and they still leave the wall perforated.
   The comparison is gap against that wall's own thickness; no absolute
   number.

5. **An opening's contribution to a room is the part that lies on it.**
   Summing whole widths produced 11.05 m of opening on a 9.4 m perimeter.
   The contribution is now the intersection of the opening with that face's
   boundary.

Two further changes were made after looking at SYNTHETIC failures, not at
P7757, and are disclosed for completeness:

6. **Nested groups merge into one drawing region** — round 3's cases A and
   G failed because a plot and its building were split apart.
7. **Zone labels identify zones** — case H released an open-plan face as
   `KITCHEN` because `DINING AREA` had been filtered out as a non-seed.
8. **A region with no readable room label anchors the boundary authority on
   its own faces instead.** This is a P7757 property (DR-001 and DR-003
   carry zero readable text), and it is disclosed as such. It can release
   nothing by itself: a face with no label is never a
   `PHYSICAL_ROOM_CANDIDATE`.

**Otherwise empty.** No layer-name exclusion, no block allowlist, no
room-name allowlist, no coordinate box, no expected room count, no expected
area, no floor total, no size threshold. No `31.37 × 15.00`. Project
23010's `calibrate` constant is still unused.

### A note on round 3's report

> **CORRECTED IN ROUND 5.** The paragraph that stood here said round 3
> "did not preserve" `ROUND_2_SYNTHETIC_HASH` and that the value "moved".
> That was the wrong description. **A historical freeze is immutable**:
> round 2's `ROUND_2_SYNTHETIC_HASH` is `de1caf07e16e738b3e34dcc5` and
> always will be. Round 3 rewrote the semantic seed classifier
> (`64c01b36653f579fafc113a0` → `356ad3ea44f5b1cefec31208`), so REPLAYING
> round 2's twelve cases under round-3 code computes
> `55b221fa624f5e2d5d8ba32b` — a `CURRENT_REPLAY_HASH`, which is a
> different object from a freeze. Round 3's document listed the replay
> value under the heading "Preserved unchanged", which is a naming error in
> a report, not a change to a freeze.
>
> Both numbers are correct and both are now carried by
> `engine/freeze_manifest.py`. No artefact was edited. See
> `docs/PROJECT_2_CAD_ROUND5.md` §0 and
> `docs/ENGINEERING_INVARIANTS.md` §58.

---

## Not opened

No human Excel, no كيال, no architect take-off totals, no manual
measurements, no structural quantities, no sanitary quantities. 28 new
tests; 50 synthetic cases across rounds 2, 3 and 4; 1810 tests passing.
