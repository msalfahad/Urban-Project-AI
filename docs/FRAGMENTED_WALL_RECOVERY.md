# Fragmented wall recovery

*Round H. Goal: recover more physical wall geometry from what is actually
drawn — without closing an opening or inventing the missing half — and
measure whether that recovery improves space partitioning.*

The round's honest one-line result: **the recovery works and the partition
barely moves.**

---

## 1 · The evidence-independence correction

The previous round counted a junction gap's evidence as two families when
one was the vector geometry and the other was the raster render. **The
raster is rendered from the same PDF**, so those are not two independent
physical sources — they are one source observed twice, and an instrument
cannot corroborate itself.

So every evidence item now carries a `SOURCE_INDEPENDENCE_CLASS`:

```
SAME_DRAWING              GEOMETRY, DRAWN_SYMBOL, SOURCE_STRUCTURE, RASTER
SAME_DOCUMENT_SET         a schedule or a printed dimension on this set
INDEPENDENT_OF_THE_DRAWING  a CAD model, a site observation
```

`VALIDATED` now requires two evidence families **and** two independence
classes. On AR-00 that takes the validated junction patches from one to
**zero**: 1 probable, 4 refused. JP-0003 was downgraded, and the wall solid
lost material it should never have been licensed to hold.

This is a real loss of apparent progress and the correct result.

## 2 · Coverage language

No figure on this project may be read as "55.5% of physical walls
captured". Both capture figures now name their own denominator:

```
ACCEPTED_SHARE_OF_DEFINED_SOURCE_STROKE_POPULATION_PCT
ACCEPTED_SHARE_OF_CLASSIFIED_WALL_LIKE_SOURCE_STROKES_PCT
PHYSICAL_WALL_RECALL: NOT_INDEPENDENTLY_ESTABLISHED
```

A drawing cannot measure its own completeness, and the sealed site
benchmark is not opened to let it try.

## 3 · Single-line walls on AR-00

58.1 m in two runs, both lying outside the building's extent. That is
enough to say the class is not the dominant problem here — and **not** a
reason to add AR-00-specific rules to make those two disappear.

---

## 4 · The resolver

`engine/fragment_recovery.py`. Two entry points:

- `resolve(...)` — new groups: one continuous face opposite N collinear
  fragments (`1↔N`), or fragments on both sides (`M↔N`).
- `recover_extensions(...)` — converts an `UNRESOLVED_EXTENSION` interval
  the band engine itself declared unestablished into established material,
  on finding the second face was drawn there as fragments all along.

Matching is **interval-based**, never endpoint-based. The output of a group
is not "a wall from A to B" but a set of paired intervals, a set of gaps,
and a reason for each gap:

```
A_SUPPORTED_PORTAL_OCCUPIES_THIS_GAP
A_WALL_ON_THE_OTHER_AXIS_CROSSES_HERE
AN_END_CAP_CLOSES_A_FRAGMENT_AT_THIS_GAP
NOTHING_EXPLAINS_THIS_GAP          -> group is DIAGNOSTIC ONLY
```

The hard invariant: **no recovered wall interval may overlap a supported
opening interval.** A group that would is refused outright —
`THE_GROUP_WOULD_BRIDGE_A_SUPPORTED_OPENING` — rather than trimmed to fit,
because a resolver that closes doors is worse than no resolver.

Acceptance is decided by axis, collinearity, separation stability, paired
coverage, pen consistency, gap explanation and opening conflict. **Not** by
room area, room count, a benchmark, or a raster millimetre — none of which
the module can see.

### Collinearity by proximity, not by bucket

Grouping fragments with `round(fixed_mm / tolerance)` makes the geometry
depend on where a bucket edge fell: two fragments 0.6 mm apart are split
when they straddle x.5, while two 0.9 mm apart inside one bucket are kept.
Single linkage asks only what the drawing can answer. Because linkage
chains, `_judge` still measures separation stability across the whole run —
a drifting chain is not one wall. Fixing this changed no AR-00 result, which
is what a robustness fix should do.

## 5 · Synthetic self-validation, before the real sheet

`engine/fragment_selftest.py` cuts a **real accepted band's** face into
fragments, so the right answer is known: the band the pairing engine
already accepted, before one of its faces was cut up. Not a room, an area,
or a count of walls anybody expected.

Seven scenarios × three real bands = **21 cases, 21 passed**, with five
failure kinds asserted explicitly:

```
BRIDGED_THE_SYNTHETIC_OPENING
INVENTED_MATERIAL
CHANGED_THE_WALL_THICKNESS
MOVED_A_WALL_FACE
NO_GROUP_PROPOSED
```

15 validated, 6 diagnostic-only — the diagnostic ones being the scenarios
where a gap has nothing to account for it, which is the correct verdict
rather than a failure.

## 6 · What the real drawing gave up

Blind: no expected room area, room count, benchmark or raster millimetre
entered acceptance.

```
New 1↔N groups      9 attempted    6 validated     8.502 m paired
                    1 diagnostic   2 rejected      1 opening protected
Band extensions    21 examined     8 recovered     7.931 m
                                   48.015 m still unresolved
Established wall   558.284 m  ->  566.215 m
```

Two of BED-01's three blockers were among them: XR-0014 recovered 1849 mm
of WB-00160 and XR-0003 752 mm of WB-00030.

New geometry enters `ESTABLISHED` only through
`RECOVERED_FRAGMENTED_MATE`, per interval, via the same wall authority as
everything else. An unresolved extension does not quietly become masonry.

---

## 7 · Did it improve the partition?

Three arms on one frozen input, differing only in the named repairs:

```
                        S0 established   S1 + validated   S2 + hypotheses
wall solid  (m²)            104.425         109.833          121.238
free-space components            13              14               19
single-room candidates            4               5                8
largest blob (labels)            32              31               23
largest blob (m²)             886.4           872.8            740.4
frozen controls inside         3 of 3          3 of 3       BED-01 alone
```

Verdict: **`REPAIRS_ARE_CAUSAL_BUT_NOT_DOMINANT`.** One more single-room
candidate, and the 32-label blob lost exactly one label.

`GEOMETRY_RECOVERED` and `PARTITION_IMPROVED` are reported apart on
purpose. 7.931 m of wall is a real gain in the solid; only the second
number unlocks a room, and it moved by one.

## 8 · Recalls after recovery

```
DIAGNOSTIC_SPACE_GEOMETRY_RECALL        9 / 17   52.9%
RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL  0 / 17    0.0%
```

Release recall did not move off zero, and no diagnostic hypothesis is
allowed to inflate it.

`DOMINANT_REMAINING_RELEASE_BLOCKER = WALL_GEOMETRY` (6 spaces), with
`PORTAL_VALIDATION` on 4 and `OTHER` on 4. The number that should drive the
next round is what each dependency would unlock **alone**: wall geometry
would release **one** room (MBTH-03); portal validation, by itself,
**none**.

## 9 · The portal bottleneck

`assess()` was dropping the blocking portal ids, so §15's report had been
structurally empty — it could never have named a portal. Fixed:

```
6 portals block 4 spaces (BED-03, BED-01, BTH-02, BTH-05)
every one   PORTAL_EXISTENCE_PROBABLE
families    DRAWN_SYMBOL + GEOMETRY  — both SAME_DRAWING
```

So not one of them has an independent evidence family, which is exactly the
§1 correction showing up in the release path. What each needs is named: a
door/window schedule row, an identified symbol block, a printed dimension,
a CAD entity, or a site observation. No document is read here — this is
preparation, not extraction.

## 10 · The 214.5 m still unresolved

Ranked by measured separation failure, never by length (invariant 31). Of
204 strokes and 214.5 m:

```
LIES_ON_A_FRONTIER_..._A_FROZEN_CONTROL     2 strokes   1.838 m
LIES_ON_A_FRONTIER_THAT_DID_NOT_SEPARATE    7 strokes   5.242 m
NOT_AT_ANY_MEASURED_SEPARATION_FAILURE    195 strokes 207.456 m
both aperture tiers                         EMPTY
```

**7.08 m of 214.5 m** sits anywhere near a separation that failed, and
nothing at all sits in an aperture. Where this plan's partition is open,
there is no stray wall-pen mark waiting to be recognised — nothing is drawn
there. None of these is resolved this round.

## 11 · BED-01 stays frozen

Held at **21.034 m²**. The hash quoted in the directive,
`6ef3d4fc44a410d0fb1f2452`, is one round stale: it was superseded at
`162a7de` (the Round 1.5 geometry-authority unification) by
`415a3d1f0b56188cdd2c9ff4`, with the **area unchanged**. Both are on record
in `engine/freeze_guard.py`, which asserts the pin on every run rather than
trusting a docs table (invariant 32).

Nothing this round touched it. XR-0014 and XR-0003 recovered two of its
three blockers, and it remains blocked by the third plus two probable
portals.

## 12 · Raster stays a localiser

The raster still points at where a separation failed. It may not draw the
wall, supply a thickness, or supply a released millimetre — and after §1 it
may not serve as a second independent evidence family either, because it is
rendered from the same PDF.

---

## 13 · The decision gate

The kill criterion was stated in advance: if deterministic recovery
recovers source strokes but produces little or no improvement in actual
space partitioning, stop expanding deterministic PDF wall reconstruction.

Measured against it:

```
established wall     +7.931 m recovered of 55.946 m unresolved  (14.2%)
                     +8.502 m in new validated groups
single-room cands    4 -> 5                     (+1)
largest blob         32 -> 31 labels of 32       (-1)
frozen controls unlocked                          0
release recall       0/17 -> 0/17                 unchanged
unresolved strokes near a failed separation   7.08 m of 214.5 m
```

The deterministic path is working correctly and is close to exhausted on
this drawing. The remaining unresolved population is overwhelmingly **not**
where the partition is broken, so more of the same will not unlock rooms.
The gate's condition is met.

What is *not* claimed: that the recovery was worthless. 16.4 m of wall
material was established from marks already on the sheet, the self-test
proves the resolver does not close doors, and the portal bottleneck is now
nameable. Those results stand whatever the next round does.
