# PROJECT 2 — ROUND 6C · PLAN ROLE, FLOOR ASSIGNMENT AND THE UNIQUE PHYSICAL-SPACE REGISTER

Round 6B measured 69 polygons on P7757 and the round-6B report added the
40 of them that carry a measurement basis into one number — 269.1838 m² —
and called it released floor area. It is not released floor area. Seven
rows carried `RELEASE_ELIGIBLE_GEOMETRY` and they total 28.5585 m².

Round 6C is about the difference. It adds no geometry: every polygon in
this round is the polygon round 6B measured, and the round-6B freeze
replays clean under today's code. What it adds is the question **what is
this polygon**, asked before any area is added to any other.

---

## 1 · FOUR AREAS, KEPT APART

```
MEASURED_CANDIDATE_AREA        every polygon that has a boundary basis
PHYSICAL_SPACE_AREA            the ones that are spaces of the building
RELEASE_ELIGIBLE_GEOMETRY_AREA the ones the release gate passes
TRADE_MEASUREMENT_AREA         nothing. That is a later round
```

On P7757, after this round:

| | area m² | rows |
|---|---|---|
| MEASURED_CANDIDATE_AREA | 269.1838 | 40 |
| PHYSICAL_SPACE_AREA | 263.9338 | 38 |
| RELEASE_ELIGIBLE_GEOMETRY_AREA | 26.3085 | 6 |
| TRADE_MEASUREMENT_AREA | — | none |

The first number is what the drawing has measurable geometry for. Only
the last may ever price anything, and it does not exist yet.

---

## 2 · WHAT A CANDIDATE IS, AND NEVER FROM AREA ALONE

Eleven roles, decided in this order and on this evidence:

```
DRAWING_ARTIFACT   the same geometry in three or more drawing regions,
                   or thinner on the mean measure than the thinnest wall
VOID / SHAFT       round 6's positive evidence of a vertical penetration
STAIR              round 6's stair evidence
EXTERIOR           outside the building fabric
PARTIAL_SPACE      the front face of a fitting bounds it, or a partition
                   of unknown thickness does
PHYSICAL_ROOM      a clear-internal basis and an authored name
PHYSICAL_OPEN_SPACE a clear-internal basis and no name
SUPER_REGION       it contains candidates that are themselves spaces
UNRESOLVED         no basis was established for it
```

Area is not evidence for any of them. A 1,020 m² polygon is sheet content
here because it repeats in three regions, not because it is large; a 1.2
m² polygon is refused because it is a tread, not because it is small.

**A STAIR IS A SPACE AND ITS PLAN RECTANGLE IS NOT A ROOM AREA.** A stair
arrives as a run of closed cells, one per tread, and a pair of tread
lines 400 mm apart is indistinguishable from a thin wall. So a stair is
registered as a space of the building and releases no room area: its
floor is measured on its going and its rise, never as a rectangle on
plan.

---

## 3 · WHAT A DRAWING REGION SHOWS

A room quantity taken from an elevation is not a small error, so every
region is asked what it shows and which floor it is, before any room is
released from it.

```
FLOOR_PLAN ROOF_PLAN SITE_PLAN AREA_DIAGRAM ELEVATION SECTION
DETAIL SCHEDULE UNKNOWN
```

Only `FLOOR_PLAN` and `ROOF_PLAN` may release room quantities, and only
when the FLOOR is also established. `UNKNOWN` is not a floor plan by
default — a region nobody has identified releases nothing, which is the
point of asking.

A title is read only from text that is **not one of the region's own room
stamps** and is at least as big as the text the sheet repeats. Where a
string matches words belonging to several roles, the longest match wins:
`SITE PLAN` is a site plan, not a plan.

### P7757 carries no title text at all

Its 89 decoded strings are room stamps, level marks, `NEIGHBOUR`,
`STREET` and `SEA VIEW`. The sheet's titles are drawn in an SHX font this
decoder does not resolve. That is a fact about the source, not a gap in
effort, and it is why a **supervised floor assignment** exists at
`data/registry/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json`:

```
DR-002 -> GROUND / FLOOR_PLAN      SUPERVISED_AUDIT
DR-004 -> FIRST  / FLOOR_PLAN      SUPERVISED_AUDIT
DR-006 -> ROOF   / ROOF_PLAN       SUPERVISED_AUDIT
```

It is carried as supplied, with `provenance = SUPERVISED_AUDIT`, never as
`DERIVED_FROM_THE_DRAWING`. **No region id is hardcoded in any module.**
The assignment arrives as data; a region no assignment names keeps
`FLOOR_LEVEL_NOT_ESTABLISHED`, and six of the nine do.

| region | role | floor | how |
|---|---|---|---|
| DR-001 | FLOOR_PLAN | not established | geometry |
| DR-002 | FLOOR_PLAN | GROUND | supervised |
| DR-003 | FLOOR_PLAN | not established | geometry |
| DR-004 | FLOOR_PLAN | FIRST | supervised |
| DR-005 | DETAIL | not established | extent |
| DR-006 | ROOF_PLAN | ROOF | supervised |
| DR-007 | DETAIL | not established | extent |
| DR-008 | DETAIL | not established | extent |
| DR-009 | UNKNOWN | not established | — |

Three regions may release room quantities. Six may not.

---

## 4 · GEOMETRY REPEATED ON EVERY SHEET IS THE SHEET

Geometry whose bounds are identical **relative to its own region's
origin** in three or more regions is sheet content — a title strip, a
north point, a key plan. Two could be a pair of identical flats; three of
the same thing in three plans of one villa is the sheet.

Nine candidates on P7757 are `DRAWING_ARTIFACT`, and the 28.2688 m² strip
that appeared once in every region is among them. No dimension of it is
written anywhere in the engine.

---

## 5 · A PARENT NEVER RELEASES WITH ITS CHILDREN

Containment is geometric and it is not the same question as release. A
candidate that CONTAINS candidates which are themselves spaces is a
`SUPER_REGION` and releases nothing: counted both ways, a floor's area is
its own double.

A room with a decorative rectangle drawn inside it also contains a
candidate — and it is still a room, because that rectangle is not a
space and releasing the room double-counts nothing. This is decided in a
second pass, after every candidate has a role.

On P7757 two candidates contain another candidate. Neither contains a
space, so neither is a super-region, and both are sheet content anyway.

---

## 6 · A LABEL BELONGS TO A ROOM, NOT TO THE SMALLEST BOX AROUND THE TEXT

A counter, a wardrobe, a vanity and a stair cell all contain text. The
room that text names is the one those things stand IN. So the candidates
for a label are the spaces that contain it, and among them the smallest
that is not a super-region wins — never the smallest polygon.

Two refusals, both exceptions rather than guesses:

* the only candidate is a subcell of something unresolved →
  `THE_ONLY_CANDIDATE_IS_A_SUBCELL_INSIDE_A_LARGER_UNRESOLVED_SPACE`
* two candidates claim it and neither is inside the other →
  `SEVERAL_PHYSICAL_SPACES_CONTAIN_THIS_LABEL`

**An unknown term is not guessed.** A word the vocabulary does not know
keeps `UNKNOWN_TERM` as its identity: not translated, not matched to the
nearest known word, and not dropped. The space it names is still
measured.

---

## 7 · THE PANTRY, ELIMINATED GENERICALLY

Round 6B released `PS-DR-002-011`, 0.90 × 2.50 m, 2.25 m², labelled
PANTRY. The independent review says that is not the pantry: it is a strip
inside it.

The generic fact is that **a band standing on another band is a fitting,
not a wall** — two established bands that share a face line over
overlapping stretches with their other faces on opposite sides of it are
stacked, and the one that runs further is the wall. Seven bands on P7757
are fittings on that test.

A fitting has two faces and they do not mean the same thing:

```
the SHARED face  is where it meets the wall. A space bounded there is
                 bounded by the WALL BEHIND, and the wall owns that face
the FRONT face   stands out into the room. A candidate that stops at it
                 is the strip the fitting leaves over, not a room
```

This distinction is the whole rule, and getting it wrong costs a room:
the first version of it blocked anything a fitting touched, which took
the KITCHEN — 8.100 m², bounded at the shared face by the wall behind its
counter — out of release along with the pantry strip.

With the rule as written, `PS-DR-002-011` is a `PARTIAL_SPACE`, the
PANTRY label is an `IDENTITY_UNRESOLVED_EXCEPTION`, and the kitchen is
untouched.

**The true pantry is still a false negative.** The room the label belongs
to, roughly 3.00 × 4.50 m, never forms as a candidate at all: two 500 mm
cabinet bands (from CAD-177 and CAD-284) outrank the 200 mm walls they
stand against, and the cabinet's own back line denies the real wall its
`OPEN_SPACE_LIES_OUTSIDE_EACH_FACE` evidence. That is a geometry defect
in round 6B's band assignment, named here and not fixed here.

---

## 8 · KNOWN GOOD GEOMETRY DID NOT REGRESS

| what | m² | dims mm | status |
|---|---|---|---|
| KITCHEN | 8.1000 | 2700 × 3000 | HELD, released |
| DRIVER | 7.8750 | 1750 × 4500 | HELD, released |
| W.C | 3.3750 | 1500 × 2250 | HELD, released |
| W.C | 2.3625 | 1350 × 1750 | HELD, released |
| W.C | 1.9500 | 1500 × 1300 | HELD, released |
| W.C (first floor) | 2.6460 | 1470 × 1800 | HELD, released |

Six rows, 26.3085 m². They are exactly the six the review named, and
they are the whole of `RELEASE_ELIGIBLE_GEOMETRY` after this round: the
seventh row of round 6B was the pantry strip.

---

## 9 · THE FALSE NEGATIVES THE REVIEW NAMED

| audit m² | candidate | verdict | what is holding it |
|---|---|---|---|
| 4.7250 | PS-DR-004-013 | FALSE_NEGATIVE_RELEASE_GATE | `ENCLOSURE_ROLE_IS_VOID_OR_SHAFT` |
| 5.0225 | PS-DR-004-026 | FALSE_NEGATIVE_RELEASE_GATE | `ENCLOSURE_ROLE_IS_VOID_OR_SHAFT` |
| 19.3500 | PS-DR-006-003 | CORRECTLY_BLOCKED | no basis was established |
| 5.5500 | PS-DR-006-004 | CORRECTLY_BLOCKED | no basis was established |

The distinction is deliberate. A gate saying *this candidate has no
established geometry* is a fact about the measurement, and there is no
area there to withhold. A gate saying *this candidate is a shaft* is a
CLASSIFICATION, and where the review says the same polygon is a room, the
classification is what is holding correct geometry back. The first two
rows are measured at the clear internal finish face and are being refused
by a verdict, not by a missing measurement.

---

## 10 · COMPLETENESS, PER FLOOR

| | GROUND | FIRST | ROOF |
|---|---|---|---|
| authored room labels | 30 | 6 | 6 |
| mapped to exactly one space | 2 | 0 | 0 |
| mapped to a space several labels claim | 10 | 2 | 0 |
| unmapped | 18 | 4 | 6 |
| physical spaces established | 12 | 18 | 1 |
| of which unidentified | 5 | 17 | 1 |
| partial spaces | 2 | 0 | 0 |
| non-space artifacts | 1 | 2 | 2 |
| unresolved | 2 | 6 | 2 |
| MEASURED_CANDIDATE m² | 58.7604 | 119.1165 | 2.9766 |
| PHYSICAL_SPACE m² | 53.5104 | 119.1165 | 2.9766 |
| RELEASE_ELIGIBLE m² | 23.6625 | 2.6460 | 0 |

**The first floor is 18 spaces with 17 of them unnamed.** Its six labels
are SHX text this decoder reads as mojibake; geometry has outrun naming
by a wide margin there, and the roof plan is worse.

---

## 11 · THE FOURTEEN SYNTHETIC DRAWINGS, FROZEN BEFORE THE RERUN

```
A  a room label inside the room it names
B  a room label standing in the units fitted along two of its walls
C  a room label inside a decorative rectangle drawn in the room
D  a plan holding three valid rooms
E  a staircase drawn as many closed cells
F  the same sheet strip repeated in three drawing regions
G  a floor plan and an elevation on one sheet
H  a floor plan and a site plan on one sheet
I  a room with correct geometry and no name
J  a name with no room boundary under it
K  one label claimed by two candidates, neither inside the other
L  two labels inside one legitimate open space
M  one open space with two functional zones in it
N  a parent and its children may never both release
```

Four requirements are checked on every one of them, whatever else the
case is about: nothing that is not a space releases; a container of
spaces never releases with its children; no label attaches to sheet
content or to the strip in front of a fitting; and nothing releases from
a region that is not an established plan of an established floor.

K and N build register rows directly rather than a drawing. Two
candidates that overlap without either containing the other, and a plate
that contains three rooms, both occur on P7757 and neither can be drawn
on purpose without drawing the enclosure engine's own failure instead.

**All fourteen pass. They were written before the P7757 rerun and six of
them failed on the first run**, which is what they were for.

---

## 12 · WHAT IS STILL NOT RIGHT

**34 of 53 labels are terms the vocabulary does not know** — SHX text
this decoder reads as mojibake. Each is carried as `UNKNOWN_TERM` rather
than guessed at.

**39 of 53 labels are unmapped.** Ten more mapped this round than before
it, but the SHX stamps remain the limit: most unmapped labels have no
candidate under them at all.

**The true pantry never forms** — §7. A 500 mm cabinet band outranks the
200 mm wall it stands against.

**`overlap_mm` on a wall band is a hull, not a set.** A pair whose owned
stretches are disjoint reports the span from the first to the last, so a
band can appear to own line it does not. Two bands on P7757 —
`PW-DR-002-V--148239.9-200.0` and `PW-DR-002-V--148039.9-500.0` — both
appear to own x = −148039.9 over overlapping stretches because of it.
Diagnosed, not fixed: it is round-6B code and round 6B is frozen.

**Two rooms are being refused by a classification, not a measurement** —
§9.

---

## 13 · FROZEN THIS ROUND

```
DRAWING_ROLE_HASH            db18783807179a48ccfd57a7
SPACE_REGISTER_HASH          a0e9ecb7a1aa008da91a5da9
ROUND_6C_SYNTHETIC_HASH      c59e81b1ea572539377804da
ROUND_6C_REGISTER_HASH       03d5d98e4ed78ab6878e4e5f
```

The register itself is written to
`data/runs/7757/P7757_ROUND6C_REGISTER.json` — under `data/runs/`, which
is gitignored by the standing rule because it is derived from the
client's drawing and carries room dimensions. It is produced on disk and
not committed.

The round-6B freeze (commit 931a1ae) is recorded in the manifest and
replays clean: every geometry hash under it matches.

**STOP.** `FunctionalZone`, `TradeMeasurementZone`, floor ceramic, wall
ceramic, the 5% waste rule, pricing and BOQ export are not implemented
and are not started, until this register is independently reviewed.
