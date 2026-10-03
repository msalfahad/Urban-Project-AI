# Project 2 — round 5: partition continuity, and what a recovery may not buy

```
PROJECT_2_CAD_ROUND5_HASH        8a90def3ac70301a1398aed5

FREEZE_MANIFEST_SCHEMA_HASH      da9588f4cbed1014d0af91ba
PHYSICAL_WALL_BAND_HASH          35449c817a74f5c1e3e45cf1
PARTITION_CONTINUITY_HASH        f9b9742aa125bfd028b75166
JUNCTION_RECOVERY_HASH           cbe777aa922d5ad948ad4189
FACE_SUBDIVISION_HASH            1313a956a735565e0905a42e
ROUND_5_SYNTHETIC_HASH           852363123a94453174791e42   23/23 passing
LOCAL_ENCLOSURE_HASH             01ff128e7ffdab820805dce1   (unchanged)
```

Run artefact `data/runs/7757/P7757_CAD_round5.json`, file sha256_16
`57edcd4f2f23206b`.

---

## §0 · Freeze semantics, corrected

Round 4's report said round 3 "did not preserve" `ROUND_2_SYNTHETIC_HASH`
and that the value "moved". **That was the wrong description**, and the
wrong description invites the wrong fix — going back and editing an old
record until a number matches. A historical freeze is immutable. Four
objects, never one:

```
HISTORICAL_ARTIFACT_HASH      what the run recorded, at the time. Immutable
CODE_HASH_AT_FREEZE           the module hashes it recorded beside it
DEPENDENCY_HASHES_AT_FREEZE   what those modules stood on, then
CURRENT_REPLAY_HASH           what the same self-test computes TODAY
```

Round 2's `ROUND_2_SYNTHETIC_HASH` is `de1caf07e16e738b3e34dcc5` and always
will be. Round 3 rewrote the semantic seed classifier, so replaying round
2's twelve cases under round-3 code computes `55b221fa624f5e2d5d8ba32b` —
which is what round 3's own artefact correctly recorded. Both are right;
they are different objects.

`engine/freeze_manifest.py` now carries rounds 1–4 in committed code — round,
source hash, commit, code hashes, dependency hashes, synthetic artefact
hash, project output hash, artefact path and file hash — because
`data/runs/` is gitignored and a record that lives only there leaves with
the container. It verifies every declared value against the artefact
whenever the artefact is present.

```
ROUND_1_CAD_BASELINE       replay diverged: none
ROUND_2_ENCLOSURE_ROLE     replay diverged: ROUND_2_SYNTHETIC_HASH,
                                            SEMANTIC_SEED_CLASSIFIER_HASH
ROUND_3_BOUNDARY_AUTHORITY replay diverged: none
ROUND_4_OPENINGS_AND_REGIONS replay diverged: none

artefacts still carrying what they were frozen at: 4 / 4
```

A PROJECT output hash is **not replayable at all** — it is a property of a
run over a client drawing. Round 5's run reports its recomputations under
`recomputed_under_round_5` and never as the preserved names. No artefact
was rewritten; the round-3 and round-4 reports were corrected in place.

---

## The result

```
                              round 4      round 5
physical-space polygons            36           57
release-eligible                    0            4
false releases                      0            0
synthetic cases               22 / 22      23 / 23   (rounds 2-5: 73/73)
```

**The 194 m² face split.** `PS-DR-002-001` — the polygon that held all
thirty-eight label observations on P7757's labelled plan — is classified
`MULTIPLE_PHYSICAL_SPACES` and became six faces, on 438 supported internal
partitions. Four of them are release-eligible: `RECEPTION` 17.08 m²,
`W.C` 3.50 m², `KITCHEN` 3.85 m², and one 5.62 m² space whose Arabic stamp
this decoder cannot read.

**And every one of those four has its blockwork blocked.** That is not a
disappointment; it is the point of §6, and the numbers say why:

| space | boundary | recovered | material authority established |
|---|---|---|---|
| RECEPTION | 17.79 m | 17.68 m | **0.11 m** |
| W.C | 9.00 m | 6.00 m | 3.00 m |
| KITCHEN | 7.85 m | 7.85 m | **0.00 m** |
| (unnamed) | 15.64 m | 15.64 m | **0.00 m** |

These rooms are measurable as AREAS and are not measurable as BLOCKWORK,
because almost every side of them is a wall face nobody drew. Round 4 would
have produced no rooms at all here; a less careful round 5 would have
produced four rooms and four sets of wall quantities.

---

## §2, §3, §5 · The physical wall

`FRAGMENT_TOLERANT_PHYSICAL_WALL_BAND_V1`

The chain is kept whole — primitives, face observations, wall band,
physical wall, opening subtraction, room boundary — and no link is skipped.
**Two collinear lines never invent a wall**: pairing is required, using the
profile's own structural test.

A wall's extent is then described in three registers that never merge:

```
OBSERVED_FACE                  what is drawn, per face, with provenance
INFERRED_PHYSICAL_WALL_EXTENT  what the wall appears to occupy
MATERIAL_QUANTITY_AUTHORITY    only the spans where BOTH faces are drawn
```

Every stretch is labelled `BOTH_FACES_DRAWN`, `ONE_FACE_DRAWN` or
`NEITHER_FACE_DRAWN`, and a short overhang — where a ring's outer face
wraps past its inner one — is a corner, not a missing face. The boundary
between an overhang and a genuine one-face continuation is the wall's own
thickness, measured there.

On P7757: **3,272 wall bands, 1,804 with a half-drawn span, 1,965 with an
undrawn gap.**

## §4, §7, §8 · Five answers, and the default is unhelpful

`NAMED_EVIDENCE_PARTITION_CONTINUITY_V1`

```
ESTABLISHED_CONTINUATION   one face runs across it, or another wall's
                           material occupies it
SUPPORTED_CONTINUATION     another wall terminates into it
OPENING_INTERRUPTION       a door, window or supported archway is there
NO_CONTINUATION            the wall ends
UNRESOLVED_GAP             none of the above
```

**There is no `bridge_collinear_gap()` and a test asserts there is none.**
Ten evidence tokens are recorded on every span and none is weighted or
summed. Only two of them may RAISE a verdict — another wall's material
occupying the span, or another wall terminating into it. Collinearity,
matching ends, a repeated band and shared CAD provenance are all
consequences of one fact, that runs exist either side, and a rule resting
on them is `bridge_collinear_gap()` under another name. A first version let
them through and promptly recovered a plain unexplained gap; the synthetic
case caught it.

**Openings are tested FIRST and outrank every positive sign** (§7). A door
drawn across a span is the reason the span is empty, and no material is
ever recovered there — asserted across all twenty-three drawings.

On P7757: **4,139 established, 20 supported, 5,185 protected by an opening,
4,212 unresolved — and not one of those 4,212 was bridged.**

## §6 · Two authorities, never one

```
TOPOLOGY_AUTHORITY   may this close a room boundary
MATERIAL_AUTHORITY   may blockwork, plaster, paint or ceramic be taken
```

`topology = VALIDATED, material = CANDIDATE` is the normal result of a
one-face recovery, and it is what stops geometry repair from quietly
creating a bill of quantities. A junction's occupancy gets
`MATERIAL_BELONGS_TO_ANOTHER_WALL`, so the same blockwork is never counted
twice. §10's lengths gained a third subtraction:

```
SPACE_BOUNDARY_LENGTH
OPENING_LENGTH                            zero material across an opening
RECOVERED_BOUNDARY_LENGTH                 a side nobody drew
MATERIAL_AUTHORITY_ESTABLISHED_LENGTH     what is actually measurable
```

On P7757: **17 of 57 spaces have material authority; 40 do not.**

## §12, §13 · Junctions, and a tolerance that is derived

`DERIVED_TOLERANCE_JUNCTION_RECOVERY_V1`

```
tolerance = max(drafting_resolution_mm, min(thickness_a, thickness_b))
```

The drafting resolution is READ OFF the drawing — the finest unit nearly
all of its coordinates sit on. The thickness is the thinner of the two
walls meeting. A miss smaller than that lands inside the junction's own
material; a larger one is a space between two walls, and a space between
two walls is a space. **Every junction reports the tolerance it was judged
by, and a test asserts the string `7757` appears nowhere in the module.**

A 2 mm miss recovers. A 1.5 m separation does not. On P7757: **269
recovered, 401 not, 235 column-like figures observed** — a column may not
become a room and may not break a partition that dies into it, and no
structural quantity begins there.

## §9, §10, §11, §16 · Subdivision, and the trap in it

`SUPPORTED_PARTITION_FACE_SUBDIVISION_V1`

It is obvious that a 194 m² polygon holding thirty-eight room stamps has
more than one room in it, and the obviousness is the trap.

    SEMANTIC OBSERVATIONS MAY DIAGNOSE UNDER-SEGMENTATION.
    THEY MAY NOT CREATE THE MISSING GEOMETRY.

Every multi-observation face is flagged `POSSIBLE_UNDERSEGMENTED_SPACE` and
reported with its observations, its supported internal partitions, its
unresolved internal hypotheses, its open-plan evidence and its portals —
then classified on geometry alone:

| P7757 polygon | area | observations | classification |
|---|---|---|---|
| PS-DR-002-001 | 194.0 m² | 38 | **MULTIPLE_PHYSICAL_SPACES** (438 supported partitions, became 6) |
| PS-DR-004-001 | 631.2 m² | 4 | **ONE_PHYSICAL_SPACE** (no partition of any kind inside it) |
| PS-DR-006-001 | 19.4 m² | 6 | **ROOM_PARTITION_UNRESOLVED** (4 hypotheses, none resolved) |

The arrangement is built **twice** — once from what is drawn, once with the
recovered spans — because the difference is the only honest evidence that a
recovery subdivided anything.

§11's protection holds: a face holding several identities with no supported
partition between them stays one physical space with functional zones, and
a test runs that assertion over every one of the twenty-three drawings.

---

## §14 · Twenty-three synthetic drawings, frozen before P7757

`ROUND_5_SYNTHETIC_HASH 852363123a94453174791e42` — 23/23, with rounds 2, 3
and 4 still at 12/12, 16/16 and 22/22 under the same code.

```
A one continuous face, one fragmented   M three rooms, fragmented faces
B both fragmented, overlapping          N external wall around a window
C the same gap with a door in it        O corridor with repeated doors
D the same gap with a window in it      P envelope containing rooms
E a true wall termination               Q a courtyard
F an unresolved collinear gap           R a shaft
G T-junction, 2 mm miss                 S a title-block line
H T-junction, 1.5 m separation          T an annotation line
I wall terminating into a column        U collinear walls, real space between
J one missing face would merge rooms    V two spaces, ambiguous gap
K open plan, no partition at all        W topology recovered, material not
L two rooms, a wall and a door
```

Six invariants are checked on **every** case, not only on the ones that
exist to test them: no opening filled with material; no unsupported gap
bridged; no face subdivided by its labels; topology authority never grants
material authority; nothing but a physical room releases; and an unresolved
or terminated span may never subdivide.

---

## §15 · P7757, after the freeze. No benchmark opened

```
drawing regions                              9
observed wall bands                       3272
  with a half-drawn span                  1804
  with an undrawn gap                     1965
established physical partitions           4139
supported continuations                     20
unresolved gaps                           4212
no continuation                              0
protected openings                        5185
junction recoveries                        269
junctions not recovered                    401
columns observed                           235
room-partition cycles                     5694

physical-space polygons                     57
possible undersegmented polygons             3
functional-zone groups                       5
complete                                    57
partial                                      0
unresolved                                   0
identity established                         5
identity unknown                            47
release-eligible                             4
spaces closed with a recovered span         40
spaces with material authority              17
recovered partition length                3743 m
```

Blockers on the 53 that did not release:

```
ENCLOSURE_ROLE_IS_VOID_OR_SHAFT                          43
ENCLOSURE_ROLE_IS_UNRESOLVED                              6
ENCLOSURE_ROLE_IS_SUPER_REGION                            2
RECOVERED_SPAN_TOPOLOGY_AUTHORITY_IS_TOPOLOGY_SUPPORTED   2
```

The last two are §18 working: a span supported well enough to subdivide and
not well enough to release blocked the release, and said so by name. The
two SUPER_REGION rejections are round 2's safety still catching merged
rooms twenty-one months of rounds later.

### §17 · The dimension cross-check, stated without flattering it

```
associations ATTEMPTED  114
AGREE                    10
DISAGREE                  0
AMBIGUOUS                 0
NOT_APPLICABLE          102
NOT_PRESENT               2
```

**Ten agreements, not 114 validations.** Round 4's report gave "72
associations, 11 AGREE" without separating the two, which overstated what
had been established; §17 is right to call that out. `NOT_APPLICABLE` is
new and is the honest majority: most of these polygons are not rectangular,
so their bounding span is not a SIDE that anything could have dimensioned,
and calling that "no dimension present" implied a search that was never
possible. No geometry was adjusted to make a dimension agree, and no
dimension is required for release.

### §19 · Success criteria

**SAFETY — met.** 0 false site / building / super-region releases. 0
unsupported gap bridges — 4,212 unresolved gaps, none closed. 0 openings
filled with invented material, asserted on every synthetic case and on
P7757.

**TOPOLOGY — met.** Fragmented but independently supported wall geometry
restored physical-space subdivision: 36 polygons became 57, the 194 m²
face became six, and 40 spaces are held shut by a recovered span.

**OPEN PLAN — met.** 0 semantic-only subdivisions. The 631 m² face holding
four observations stayed one physical space because no partition of any
kind lies inside it.

No target room count and no target release count was used.

---

## K · Everything introduced or changed after inspecting P7757

**Nothing in this round was changed after looking at P7757's round-5
output.** The synthetics were frozen first and the P7757 run was made once,
then once more after two corrections that came from the synthetic suite and
from a round-4 test, described below. That is a better record than round 4,
where five changes followed the client run, and it is the reason this
section is shorter.

Changes made after SYNTHETIC failures, all disclosed:

1. **Only two tokens may raise a verdict.** The first continuity model let
   collinearity, matching ends, a repeated band and shared entity
   provenance raise a `SUPPORTED_CONTINUATION` — and promptly recovered a
   plain unexplained gap in case F. Those four are consequences of one
   fact; the rule now names the two that are not.
2. **A short overhang is a corner.** The first physical-wall model treated
   every ring corner as a wall with a missing face and "recovered" all of
   them. The trim boundary is the wall's own thickness.
3. **A recovered span is attributed geometrically.** The frozen enclosure
   names one drawn piece per side — the one covering most of it — so
   reading recoveries off its edges missed every recovery sharing a side
   with a longer drawn run. Asked of the geometry instead.
4. **`MATERIAL_AUTHORITY_ESTABLISHED_LENGTH` was added** after the first
   P7757 run showed released rooms reporting their whole perimeter as
   material while their boundaries were almost entirely recovered. This
   one WAS prompted by looking at the client output — it is a reporting
   correction, it releases nothing new, and it is disclosed here for that
   reason.
5. **`NOT_APPLICABLE` was added to the dimension verdicts**, as §17 asked.

Carried forward from round 4's section K and still true: the
`DEWANEYA` vocabulary entry (round 3), and round 4's five post-inspection
corrections to the opening classifier. Nothing new was added to the
vocabulary this round — §1 forbade it and nothing needed it.

**Otherwise empty.** No layer-name exclusion, no block allowlist, no
room-name allowlist, no coordinate box, no expected room count, no expected
area, no floor total, no size threshold, and no millimetre constant taken
from this drawing. Every tolerance in the three new geometric modules is
either an earlier round's frozen constant or derived per-junction from the
drawing and reported. Project 23010's `calibrate` constant is still unused.

---

## Not opened

No human Excel, no كيال, no architect take-off totals, no manual
measurements, no structural quantities, no sanitary quantities. 29 new
tests; 73 synthetic cases across rounds 2, 3, 4 and 5; 1839 tests passing.
