# Project 2 — round 3: room-boundary authority and multilingual identity

```
PROJECT_2_CAD_ROUND3_HASH        e95a4c3c4a298339d9e0adb1

ROOM_BOUNDARY_AUTHORITY_HASH     2a79508559556c622fd0dabe
LOCAL_ENCLOSURE_HASH             01ff128e7ffdab820805dce1  (the frozen
                                 enclosure, unchanged — round 3 changed
                                 WHICH LINES it is given, never the algorithm)
MULTILINGUAL_IDENTITY_HASH       0611990f77db86d2d4854830
ONTOLOGY_HASH                    1f157903072fd3531a2ef079
ROUND_3_SYNTHETIC_HASH           20fd3ed87d05f40ba6cf6123   16/16 passing
```

Preserved unchanged, as required:

```
PROJECT_2_CAD_BASELINE_HASH      3edf12c66f0984330d77e248
PROJECT_2_CAD_ROUND2_HASH        70e2f4c34a6b1374687fb20f
ROUND_2_SYNTHETIC_HASH           de1caf07e16e738b3e34dcc5
```

> **NOTE ADDED IN ROUND 5 (this replaces a round-4 note that used the
> wrong words).** `ROUND_2_SYNTHETIC_HASH de1caf07e16e738b3e34dcc5` above
> is round 2's freeze, and a freeze is immutable — it is correct here and
> it will not change. What this heading should not have called "preserved"
> is the fact that round 3 rewrote the semantic seed classifier
> (`64c01b36653f579fafc113a0` → `356ad3ea44f5b1cefec31208`), so replaying
> round 2's twelve cases under round-3 code computes
> `55b221fa624f5e2d5d8ba32b` — a CURRENT_REPLAY_HASH, recorded correctly in
> round 3's own run artefact. Two different objects, both correct, now both
> carried by `engine/freeze_manifest.py`. Round 2's safety result is
> unaffected: 12/12 then, 12/12 now. See `docs/PROJECT_2_CAD_ROUND5.md` §0
> and `docs/ENGINEERING_INVARIANTS.md` §58.

---

## The result, stated plainly

**Round 3 succeeded on the synthetics and did NOT move P7757's measurement.**

```
                        synthetic (16 cases)      P7757
rooms measured          yes - A,B,C,E,G,H,        complete   2  (unchanged)
                        I,J,K,M,N,O,P release     released   0  (unchanged)
false releases          0                         0
round-2 safety          12/12 still holding       holding
```

On the synthetic buildings the machinery now does what round 3 asked: it
measures rooms from local partitions, lets external walls form room sides,
refuses to leak through doorways, and keeps a site line out of every room
polygon. On P7757 it changes nothing, and §15 says report that rather than
tune until a number appears.

What DID move on P7757 is identity: **0 → 17 established, 0 conflicts.**

---

## §1 · The correction to semantics, accepted

The round-2 test demanding that `KITCHEN` classify **exactly** like `QQZZX`
was wrong and has been replaced. It made the semantic layer blind, which is
why a street label seeded a physical room.

The narrower invariant now holds instead: a real project's word must be
judged by the **general vocabulary**, through the same lookup any other term
takes, never by a rule naming it. Two tests enforce it — one asserts each
real word reaches its class via the vocabulary, the other asserts no concept
is named by a single term (a one-term concept matching one project's
spelling would be that project's rule wearing a general name).

`engine/architectural_ontology.py`: **53 concepts, 332 terms**, English and
Arabic, matched exactly on a normalised form (no stemming, no substring —
`STORE` must not match `STOREY`).

| class | concepts |
|---|---|
| `ROOM_OR_PHYSICAL_SPACE` | 27 |
| `EXTERNAL_SPACE` | 8 |
| `SITE_OR_LOCATION_ANNOTATION` | 7 |
| `DRAWING_ANNOTATION` | 6 |
| `FUNCTIONAL_ZONE` | 5 |

Breadth is the evidence that it is a vocabulary rather than a lookup table:
a test requires it to recognise **ward, classroom, workshop, showroom, plant
room, riser, elevator, loggia, atrium, cloakroom, larder, vestibule, مصعد,
عيادة, ورشة, بهو, شرفة, مستودع** — none of which appears on any drawing in
this repository.

## §2 · Multilingual identity — the round-2 blocker removed

`SAME_CONCEPT · COMPATIBLE · DIFFERENT_FUNCTIONAL_ZONE · CONFLICT · UNKNOWN`

Grouped by spatial coincidence **and block lineage** — lineage matters,
because two stamps of different rooms can fall within two metres of each
other near a shared wall, and merging those would invent a conflict out of a
layout accident.

| case | result |
|---|---|
| `KITCHEN` + `مطبخ` | `SAME_CONCEPT`, established, **2 independent statements** |
| `KITCHEN` + `BEDROOM` | `CONFLICT`, releases nothing |
| `KITCHEN` + `QQZZX` | `COMPATIBLE`, established as KITCHEN |
| `KITCHEN` + `DINING AREA` | `DIFFERENT_FUNCTIONAL_ZONE`, established |
| two unknown labels | `UNKNOWN`, honest |

**On P7757: 17 identities established, 0 conflicts, 1 bilingual pair
reconciled.** Round 2 had 0 established and blocked every room.

The 16 that remain `IDENTITY_UNKNOWN` are Arabic stored in SHX fonts, which
this decoder returns as mojibake. §11 is respected: that is a decoder limit,
recorded, never guessed at — and §10 means it costs no geometry.

## §3–§6 · Room-boundary authority

`SITE_BOUNDARY · BUILDING_ENVELOPE · INTERNAL_PARTITION ·
ROOM_BOUNDARY_ELIGIBLE · DETAIL_GEOMETRY · UNRESOLVED`, multiple roles
permitted.

§6's rule is implemented **directly** rather than approximated:

> Take the outermost boundary of everything the drawn lines enclose. Remove
> the bands lying on it and look again. If every room observation is still
> enclosed, that ring was never holding a room in — it bounds ground and may
> not close a room. If removing it leaves a room unenclosed, the building
> boundary coincides with it and §6's exception applies.

That is containment. It reads no area — a test asserts `area_m2` does not
appear in the module — so a plot far larger than its building and one barely
larger are handled identically.

**§5's warning is satisfied without a special case.** Where there is no site
line the outermost boundary IS the envelope, removing it opens the rooms, and
it stays eligible. Case B (a corner room on two external walls) asserts a
released room actually used a `BUILDING_ENVELOPE` band.

## §7 · Local enclosure, not global flood

Each seed is enclosed **twice**. The first pass offers only bands that divide
the fabric; if the seed closes on those, that is the nearest supported cycle
and no outer boundary was involved — §6 satisfied by construction. Only when
the inner pass fails is the outermost boundary offered.

"Smallest" is topological throughout: the nearest cycle the drawn partitions
support. No area is compared and no room-size prior exists.

The enclosure algorithm itself is untouched —
`SUPPORTED_LINE_ARRANGEMENT_FLOOD_FILL_V1`, freeze
`01ff128e7ffdab820805dce1`. Round 3 changed which lines it is handed.

## §10 · Four separate statuses

```
GEOMETRY_STATUS        did the boundary close
PHYSICAL_SPACE_STATUS  is this a physical room, separately from its name
IDENTITY_STATUS        what it is called
RELEASE_STATUS         may a quantity be taken from it
```

Case M asserts the pairing that matters: an `UNKNOWN` label inside a valid
room leaves `PHYSICAL_SPACE_VALIDATED` with `IDENTITY_UNKNOWN`, and the room
releases. Inability to read a name does not destroy correct geometry.

---

## §13 · P7757 rerun, no benchmark opened

| | round 2 | round 3 |
|---|---|---|
| plan-region candidates | 14 | 14 |
| semantic observations | 89 | 89 |
| ROOM_LIKE | 68 | **53** |
| NON_SPACE_ANNOTATION | 19 | **31** |
| EXTERNAL_SPACE_LIKE | — | **4** |
| space candidates | 33 | 33 |
| **identity established** | **0** | **17** |
| identity conflicts | 33 (false) | **0** |
| bilingual reconciled | — | **1** |
| wall-like bands | 2877 | 2877 |
| room-boundary eligible | — | 2877 |
| site-boundary rejections | — | **0** |
| super-region rejections | 0 | 0 |
| complete | 2 | 2 |
| partial | 0 | 0 |
| unresolved | 31 | 31 |
| validated geometry, unknown identity | — | 0 |
| portal boundaries | 0 | 0 |
| **release eligible** | **0** | **0** |

Blockers:

```
A_WHOLE_SIDE_HAS_NO_DRAWN_LINE      31
ENCLOSURE_ROLE_IS_UNRESOLVED         2
```

**§14's per-room table is empty, because no physical space was released.**

### Why, located precisely

The authority stage found **0 site bands on P7757** — every band stayed
eligible. The reason is honest and worth stating: P7757's model space holds
twelve drawings side by side across 808 m, so "the outermost boundary of
everything the lines enclose" spans the whole strip, and removing it does not
free the rooms because some labels (on elevations and sections) are never
enclosed by anything. The test is correct; its global framing does not fit a
model space containing twelve unrelated drawings. **Applying it per drawing
region is the obvious next step and was not done this round.**

But that is not what blocks measurement. Tracing one real room settles it —
`SALOON` at (−133029, −800874):

```
nearest wall below    4220 mm      nearest wall above   4730 mm
nearest wall left     2391 mm      nearest wall right   3959 mm
```

so the seed does sit in a plausible 6.3 × 9.0 m region. Its left side, at
x = −135419.9, is drawn in exactly two pieces:

```
y −803593 .. −802443    1150 mm
y −802393 .. −799643    2750 mm     then nothing
```

The room needs that side to reach y ≈ −796143. **It stops 3.5 m short.** The
remaining 3.5 m is an opening — a saloon opening to a hall — and there is no
wall-like geometry there on any layer. The enclosure's refusal is correct.

This is the same finding as AR-00's, reached from the other end: the blocker
is not wall selection any more, it is **unclosed openings**. §8 states the
remedy — a validated portal may close a room topologically without pretending
material exists across it — and P7757 carries the evidence for it: door
blocks `D115 D120 D200 D315 d220 arch120`, arcs on layer `D`, 931 block
placements. **Wiring CAD-authored door geometry into portal closure is the
next round's work and was not attempted here.**

---

## §15 · Success criteria

**PRIMARY SAFETY — met.** 0 site / building / super-region false releases, on
P7757 and across all 28 synthetic cases (round 2's 12 and round 3's 16).

**PRIMARY MEASUREMENT — met on synthetics, not on P7757.** The synthetic
buildings produce locally supported room polygons from authored geometry,
never flooding to plot geometry; case A releases four rooms inside a site
sixty metres across, case G inside one eighty metres across. P7757 produces
none, for the reason traced above.

No tuning was done to make a number appear. Zero released rooms on P7757 is
the reported answer.

---

## K · Anything that required a P7757-specific rule

**One item, disclosed rather than buried.**

`DEWANEYA` — P7757's Latin transliteration of ديوانية — was UNKNOWN when the
vocabulary was first written. I added it, **and I added it knowing this
project uses that spelling.** What I did to keep that honest:

- the whole transliteration family went in, not P7757's spelling alone:
  `majlis, mejlis, majles, majlas, diwaniya, diwaniyah, dewaniya, dewaneya,
  dewania, deewaniya`;
- transliteration families were added for **other** concepts at the same
  time, where no project here needs them: `musalla/mussalla/musallah`,
  `hosh/housh/hoash`, `sikka/sikkah`, `liwan/leewan`;
- a test forbids any concept named by a single term, so a one-spelling
  concept could not survive.

It changed nothing about P7757's result — that stamp releases no geometry.
You should still judge whether the disclosure is sufficient; the alternative
was leaving a standard Gulf architectural term out of a Gulf vocabulary.

**Everything else is empty.** No layer-name exclusion, block allowlist,
room-name allowlist, coordinate box, expected room count, expected area,
floor total, or size threshold. No `31.37 × 15.00` exclusion. Project
23010's `calibrate` constant is still unused.

### Two defects my own fixtures caught this round

1. **The first boundary-authority model counted ray crossings** and was
   wrong: an open partition adds crossings on one side only, so a point
   between the plot and the building scored the same depth as a point inside
   a room. Cases B, I, K and N failed; the model was replaced with the
   containment test above.
2. **Excluding short runs from room boundaries emptied the drawing.** A
   300 mm minimum, meant to keep ticks out of ring detection, stripped
   **1,313 of 2,877 bands** from a drawing whose wall runs average 462 mm,
   after which nothing enclosed at all. Short runs are now kept out of the
   ring model and still allowed to form a room side.

---

## Not opened

No human Excel, no كيال, no architect take-off totals, no structural or
sanitary quantities, no manual measurements. 62 new tests; 28 synthetic
cases across rounds 2 and 3, all passing.
