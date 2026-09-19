# URBAN PROJECTS — OPENING SPIKE · SPACE×USE MATRIX · TRUTH DOMAINS

Project 23010 · AR-00 rev MAR.2023 · commit `c88395f` · **773 tests passing**

The headline is a negative result: **the vector opening spike is not strong
enough to proceed to E34 as built.** Details in section B.

---

## A. BUILDING ENVELOPE / EXTERNAL CLASSIFICATION

Three iterations, reported as they happened.

| version | INTERNAL | UNRESOLVED | EXTERNAL |
|---|---|---|---|
| corner pixel, fall-through to INTERNAL | **703** | 0 | 0 |
| border connectivity, fail closed | 161 | 542 | 0 |
| + march crosses wall cavities | **564** | **139** | **0** |

**Border connectivity changed nothing about which regions count as outside.**
Exactly one region touches the sheet border on AR-00, and it is the region the
corner pixel sat in. My "dimension-line slivers create a fake outside"
hypothesis was wrong.

What it changed was the failure mode: classification no longer defaults to
INTERNAL, so 542 segments that were claiming a fact stopped claiming it.

**Those 542 then named their own cause.** They terminated in regions 43, 159,
163, 338 and similar — every one of which the space map already lists under
`not_a_space` as a **wall cavity**. The march stopped at the first non-ink pixel,
and in a double-line wall the gap between the two drawn faces is not ink, so it
was stopping *inside the wall*. It now continues until it reaches something
recognised. 403 segments moved from unresolved to correctly INTERNAL.

### EXTERNAL is still 0 of 703

Not fixed. Beyond an exterior wall lies the dimension and annotation zone, which
is neither a mapped space nor border-connected, so the march crosses it as cavity
and exhausts its 600 mm reach before arriving anywhere recognised. A longer march
would walk through an entire room.

Per-space: **5 VALIDATED, 31 BOUNDED_ERROR.** `EXTERNAL_SPLIT` is blocked on 22
in-scope-or-ambiguous spaces, which is why `EXTERNAL_FINISH` shows 1 ready.

The envelope test itself — union of mapped spaces and their walls, with a segment
whose outward direction leaves that envelope classified external — is **not
built**. Per review guidance it must not assume `union(mapped spaces)` is the
true envelope, since this segmentation is already known to miss a real room.

### Also fixed

`peek()` was reproducing `np.roll`'s wrap-around, inherited when it replaced a
roll. A march off the sheet edge reappeared on the far side and reported whatever
room sat there. It now returns `None` at the edge and the caller treats that as
unresolved.

---

## B. OPENING SPIKE — VERDICT: NOT STRONG ENOUGH TO PROCEED

### What was built

Six independent signals, seeded on **paired** wall faces so a fixture cannot
start a candidate: gap in a paired-face run, jambs both ends, door leaf line,
swing arc, two different mapped spaces, plausible width band.

`VALIDATED` requires three strong signals **and** two genuinely different mapped
spaces. A width band is explicitly not strong evidence. A swing arc is supporting
evidence and never a condition — sliding, pocket, double and open transitions may
have no arc at all.

### Two defects in my own spike, found by running it

**Swing arc fired on 82 of 94 candidates** at a 1500 mm tolerance. With 2,399
arcs on a villa floor almost every gap has one within a metre and a half. *A
signal that agrees with 87% of candidates carries no information about any of
them.* Tightened to 400 mm → 27 of 94.

**Two-mapped-spaces fired on only 2 of 94.** I sampled 250 mm perpendicular from
the wall line, but the gap sits on one *face* of a paired wall, so 250 mm often
lands in the wall body or the cavity between its faces. Now marches outward
150→900 mm until a mapped space appears → 4 of 94.

### Results after both fixes

| | |
|---|---|
| axis-aligned vector lines | 35,355 |
| **paired** wall faces retained | **533 (1.5%)** |
| gaps in collinear paired-face runs, 500–6000 mm | **94** |

| status | count |
|---|---|
| VALIDATED | **4** |
| PROBABLE | 67 |
| AMBIGUOUS | 22 |
| REJECTED | 1 |

| evidence | hits |
|---|---|
| PAIRED_WALL_FACE_GAP | 94 |
| PLAUSIBLE_WIDTH | 93 |
| JAMBS_BOTH_ENDS | 55 |
| JAMB_ONE_END | 34 |
| SWING_ARC | 27 |
| DOOR_LEAF_LINE | 7 |
| **TWO_MAPPED_SPACES** | **4** |

### The diagnostic that decides the verdict

Adjacency breakdown of the 94 gaps:

| what is on either side | count |
|---|---|
| two **different** mapped spaces | **4** |
| the **same** space on both sides | **32** |
| one mapped space only | 2 |
| no mapped space either side | **56** |

**32 gaps have the same room on both sides.** That is not a doorway — it means
the collinear grouping (12 mm tolerance) is joining lines that belong to
different walls, or to features inside one room, and inventing a gap between
them. **56 touch no mapped room at all** — external wall runs, dimension-zone
linework, title block.

So only 4 of 94 seeds are even candidates for being a door between two rooms,
against perhaps 25–30 real doors on this floor. **Low recall and a candidate pool
that is ~95% not-between-two-rooms.**

### The four VALIDATED candidates need manual verification

| id | width | spaces | plausible? |
|---|---|---|---|
| OC-0037 | 1300 mm | BED-03 ↔ BED-04 | **doubtful** — a double door between two bedrooms |
| OC-0043 | 1973 mm | MBTH-04 ↔ COR-02 | plausible open transition |
| OC-0052 | 1300 mm | KIT-01 ↔ BED-03 | **doubtful** |
| OC-0053 | 1000 mm | KIT-01 ↔ BED-03 | **doubtful** — a kitchen with two openings into a bedroom |

KIT-01, BED-03 and BED-04 sit in a row along the south of the plan. Doors
directly between a kitchen and two bedrooms, with no corridor, is not a layout I
would accept without looking at the sheet. **I am reporting these as probable
false positives rather than as four successes.**

### Acceptance cases

**WSH-01 / SHF-01 — ZERO nearby candidates.** The spike does not recover the
washroom boundary at all, and the reason is structural: the earlier E25 notes
record that the washroom "isolates only when proven door gaps are closed", and
its threshold is a **dashed line**. A dashed line is not a pair of parallel wall
faces, so this detector cannot see it by construction.

`engine/walls.dashed_runs()` already exists for exactly this and the spike did
not use it. That is the single clearest next improvement.

**BED-04 — 9 nearby candidates, none of them the bathroom.** The only VALIDATED
one is OC-0037 (BED-03 ↔ BED-04), not the printed 1600 × 3000 boundary. Two
nearby PROBABLE candidates report the same space on both sides
(`['BTH-06','BTH-06']`, `['BED-04','BED-04']`) — the phantom-gap failure again.

**OPEN-01 — 15 nearby candidates**, none resolving its topology.

### Recommendation

**Do not proceed to E34 on paired-face gaps alone.** Next iteration, in order:

1. **Add `dashed_runs()` as a second seed source.** The one acceptance case that
   matters most is invisible to paired faces by construction.
2. **Fix the phantom gaps** — 32 same-space candidates mean the collinear
   grouping is wrong. Require that the two faces bounding a gap belong to the
   *same* paired wall, not merely the same line within 12 mm.
3. **Investigate the 1.5% pairing retention.** 533 faces may be dropping real
   walls, which would explain the low recall directly.
4. Only then re-assess whether vector evidence is sufficient, or whether openings
   fall back to the door schedule / DWG blocks / human review.

---

## C. WASHROOM RECOVERY — NOT RECOVERED

The formal result, on dimensional evidence alone:

| | |
|---|---|
| region currently labelled WSH-01 | **0.583 × 1.740 m = 1.006 m²** |
| printed washroom | **1.500 × 2.400 m = 3.600 m²** |
| verdict | **geometrically incompatible** |

The ergonomic observation about basin depth is dropped from the proof, per
review: a printed dimension settles it and construction geometry should not lean
on furniture assumptions.

Separately, on what the current region *is*: it is one of four near-identical
540–594 × 1740 mm slots (`WSH-01`, `SHF-01`, `REC-01`, `REC-02`), all with a
0.991 fill ratio. `WSH-01` and `SHF-01` share the same x and sit 490 px apart
vertically — a stack of two identical ducts.

**Where the true washroom is: still unknown.** Region 441, the candidate named in
the earlier notes, is absent from this segmentation, and there are **no unmapped
regions anywhere between 3.2 and 4.0 m²**. Its floor area is absorbed into a
neighbour. Status: **`WASHROOM_GEOMETRY_UNRESOLVED`**, and all its trade
quantities stay blocked.

## D. BED-04 BATHROOM — NOT RECOVERED

49.71 m over 41 segments, one merged region. The printed 1600 × 3000 bathroom has
not separated. Blocked on `REGION_IDENTITY`.

## E. OPEN-01 TOPOLOGY — PARTIAL

`REC-01` and `REC-02` are **independent regions with their own closed
boundaries** (4.28 m and 4.13 m over 4 segments each), not holes inside the
122.88 m polygon. Evidence against the double-count theory. Not yet confirmed
against the area figure, so ceramic and plaster stay blocked.

---

## F. HEIGHT REGISTRY — TRUTH DOMAINS

The single source ladder is gone. `SITE_MEASURED` and `SECTION_DRAWING` are not
two sources for one fact; they are facts about different things, and ranking them
together would let a site tape silently overwrite the architect's intent.

| domain | sources |
|---|---|
| DESIGN | SECTION_DRAWING > SPECIFICATION > APPROVED_PROJECT_RULE |
| SITE | SITE_MEASURED > AS_BUILT_SURVEY |
| COMMERCIAL | CONTRACT_BASIS > BOQ_BASIS |
| *(none)* | ASSUMED — never releasable |

The registry is keyed on `(domain, name)`, so DESIGN plaster 3.20 and SITE
plaster 3.15 coexist. Production reads DESIGN. `variance()` returns both with
neither corrected toward the other. A source may only be filed under its own
domain. Ranking is within a domain; no global rank is offered.

**`OWNER_RULE` → `APPROVED_PROJECT_RULE`**, requiring `approval_status=APPROVED`
plus `approved_by`, `approved_on` and `rule_version`. A model may propose a
project rule; **it may not sign one.**

Project 23010 DESIGN: **2 RELEASABLE** (ceramic 3.00, plaster 3.20, both approved
by the owner and both recording that they were *not* read from a section on
AR-00), **6 HEIGHT_REQUIRED**. SITE: 8 absent.

---

## G. SPACE × USE RELEASE MATRIX

36 spaces. Scope split: 17 IN_SCOPE, 6 AMBIGUOUS, 13 OUT_OF_SCOPE.

An OUT_OF_SCOPE space is **N/A, not blocked** — there is genuinely no quantity to
release, and counting it as blocked would hide both facts.

| USE | READY | BLOCKED | N/A |
|---|---|---|---|
| GROSS_PERIMETER | **15** | 8 | 13 |
| GROSS_WALL_AREA | **15** | 8 | 13 |
| GROSS_PLASTER | **15** | 8 | 13 |
| CEILING | **15** | 8 | 13 |
| WATERPROOFING_HORIZONTAL | **15** | 8 | 13 |
| WATERPROOFING_VERTICAL | **15** | 8 | 13 |
| GROSS_CERAMIC_WALL | **8** | 1 | 27 |
| EXTERNAL_FINISH | 1 | 22 | 13 |
| BLOCKWORK | 0 | 23 | 13 |
| NET_CERAMIC_WALL | 0 | 9 | 27 |
| NET_PLASTER | 0 | 23 | 13 |
| PAINT | 0 | 23 | 13 |
| SKIRTING | 0 | 23 | 13 |

Blocked spaces, by primary blocker:

- **`BLOCKED_REGION_IDENTITY` — 2** on every use: `WSH-01`, `BED-04`
- **`BLOCKED_SCOPE` — 6**: `COR-02`, `COR-03`, `REC-01`, `REC-02`, `SRV-01`,
  `STA-01` (the owner's brief does not reach them; AMBIGUOUS is the correct answer)
- **`BLOCKED_OPENINGS` — 8** on `NET_CERAMIC_WALL`, **15** on `NET_PLASTER` /
  `PAINT` / `SKIRTING`
- **`BLOCKED_PHYSICAL_WALL_SPLIT` — 15** on `BLOCKWORK`
- **`BLOCKED_EXTERNAL_SPLIT` — 14** on `EXTERNAL_FINISH`

**Nothing is a complete project takeoff.** What exists is
**`VALIDATED_PARTIAL`**: 15 spaces with releasable gross perimeter, wall area,
plaster and ceiling; 8 with releasable gross ceramic wall. No net quantity is
releasable anywhere, and no material or price is attached to anything.

---

## H. TESTS

**773 passing**, from 731 at the start of this round. New: 21 opening-spike tests
(no single signal validates; a swing is never required; a candidate never invents
a height), 11 per-space release-matrix tests, 10 height truth-domain and
approval tests.

---

## WHAT THIS REPORT DOES NOT CLAIM

- Not that the opening spike works. 4 validated of ~25–30 expected doors, three
  of the four architecturally doubtful, and the primary acceptance case invisible
  to it by construction.
- Not that EXTERNAL classification works. 0 of 703, cause stated, fix not built.
- Not that the washroom is recovered. Its polygon does not exist in this
  segmentation and its area is inside a neighbour.
- Not that the 15 READY spaces are *verified correct* — only that their stated
  dependencies are satisfied. The geometry reproduces a prior run of the same
  engine; both could share an error, and the manual 102.70 m has not been used to
  calibrate anything.
