# PROJECT 2 — ROUND 6A: WHICH FACE DOES A ROOM STOP AT?

**Geometry only.** No TradeMeasurementZone, no floor ceramic, no wall
ceramic, no waste, no pricing, no BOQ export. Round-6 steps 6–12 remain
unstarted, and the 1.05 × 1.50 m kitchen recess is deliberately **not**
merged — §7 says that separation is intentional.

Round 6 steps 1–5 (commit `bc8e96f`) are preserved. They are now a Freeze
in the manifest, `ROUND_6_GEOMETRY_STEPS_1_TO_5`, and round 6A is compared
**against** that record rather than overwriting it.

---

## 1 · THE DIAGNOSIS — THE POLYGON WAS STOPPING AT A WORKTOP

Not a tolerance, not a trade grouping. Four CAD entities:

```
CAD-310  x = -152339.9   the kitchen's WEST WALL inner face   layer 1
CAD-311  x = -151839.9   a 500 mm deep COUNTER in front of it layer 5
CAD-283  y = -800593.5   the kitchen's NORTH WALL inner face  layer 1
CAD-284  y = -801093.5   a 500 mm deep COUNTER in front of it layer 5
```

2700 − 500 = **2200**. 3000 − 500 = **2500**. Those are exactly the
dimensions round 6 reported. The flood stops at the first line it meets,
and the first line it meets is the front of a kitchen counter.

The same disease, twice more:

- **The W.C / WASH pair.** A vanity front (CAD-462, 500 mm) cut the WASH,
  and the door between W.C and WASH was left open because two openings
  claimed the same door symbol — one whose faces are the real 150 mm
  partition, one whose faces are a 550 mm separation nothing paired.
- **A window's glazing lines.** The wall's 200 mm band lost its pairing to
  a 120 mm one, because a glazing line 120 mm away is nearer than the
  wall's own opposite face.

**No layer is the culprit and no layer is the fix.** Layer 5 carries
genuine wall pieces elsewhere in the same drawing; layer 1 carries detail.
Nothing in this round reads a layer name.

---

## 2 · THE RULE — A WALL IS WHERE THE SPACES STOP

`SPACE_STOPS_AT_THE_FACE_WALL_OWNERSHIP_V1`. Two questions, asked of the
drawn coordinates rather than of a polygon:

> **IS THERE OPEN SPACE ON THE OTHER SIDE OF YOU?**
> **IS THERE OPEN SPACE OUTSIDE EACH OF YOU, AND NONE BETWEEN YOU?**

A new pairing token, ranked below a hosted opening and a two-ended reveal
and above nearness, a repeated thickness and a junction:

```
OPEN_SPACE_LIES_OUTSIDE_EACH_FACE_AND_NONE_BETWEEN_THEM
```

It is deliberately not top of the order: it is also true of a pair that
straddles a wall **and** the detail line drawn beside it, which is exactly
synthetic case C. A hosted opening and a reveal at both ends are evidence
about one specific pair; this is evidence about a shape.

**It is read from coordinates, not from polygons.** A wall's interior is a
closed cell only if every line around it meets every other, and drawings
are not drawn that way — one 50 mm slot at a window turns the inside of a
wall into the whole floor plate, and the first version of this module
therefore read P7757's own kitchen wall as open floor. The distance to the
next parallel line does not care. A strip wider than the thickest wall
this project recognises (the profile's own `MAX_WALL_THICKNESS_MM`) is
space; anything narrower is not. **No new constant was introduced.**

### 2.1 The drawing is read TWICE

The question cannot be answered while a tile joint is still treated as
something a room might stop at. So:

1. pair the faces with no topology evidence at all (round 6's rule),
2. set aside every line that is a face of no wall **and** has floor on
   both sides of it,
3. read the arrangement again without them, and pair again.

"Floor on both sides" is itself structural: a strip is the inside of a
wall only when the two lines bounding it are the **two faces of one
established band**. That is what separates a 200 mm wall from the 500 mm
gap between a worktop and the wall behind it. Both are narrow; only one
has a wall's two faces around it.

### 2.2 One line, several stretches

Round 6 let a pair own the hull of its overlap. P7757 draws its east wall
as one line past the kitchen and another past the corridor, and the hull
made a single pair claim nine metres of a line it is alongside for three —
which robbed the wall that really is drawn there. A pair now owns a **set**
of stretches, and its spans are trimmed at the first stretch either of its
lines gives to a different wall.

### 2.3 A door in dispute

An opening whose two faces **are** the two faces of an established wall is
not in competition with one whose faces are not: the first names a wall,
the second names a coincidence. Where the established claim is unique, the
rest stand down. Where two established claims remain, the ambiguity is
real and is kept.

---

## 3 · §3 SIDE OWNERSHIP AND §4 MEASUREMENT BASIS

Every established face records which side it faces and what is there:

```
SPACE_LEFT / SPACE_RIGHT        the lower or higher coordinate on its axis
INTERIOR / EXTERIOR / UNKNOWN   from the envelope model
OPEN_SPACE / INSIDE_A_WALL / OUTSIDE_THE_DRAWN_ARRANGEMENT
```

One wall therefore gives its low face to one room and the **opposite** face
to the other. No boundary is ever drawn down the middle of a wall to be
shared. On P7757 this round establishes **804 wall faces**.

Four bases exist and are never silently switched:

```
CLEAR_INTERNAL_FINISH_FACE   the only basis round 6A releases
STRUCTURAL_FACE              not measured: nothing separates render from block
WALL_CENTERLINE              never a floor area
EXTERNAL_FACE                envelope quantities only
MEASUREMENT_BASIS_NOT_ESTABLISHED
```

Every physical space reports `measurement_basis`, `boundary_face_ids`,
`wall_band_ids` and the CAD provenance and selection reason of **every**
side. A side nobody can attribute is `MEASUREMENT_BASIS_NOT_ESTABLISHED`,
and that blocks the release rather than being filled in.

The frozen enclosure is untouched. Its flood still runs and is reported as
the `OBSTRUCTED_EXTENT` — a diagnostic, never a floor area.

---

## 4 · §9 THE BUILDING AND THE SITE ARE TWO QUESTIONS

```
INSIDE_BUILDING / OUTSIDE_BUILDING / BUILDING_EXTENT_UNKNOWN   the envelope
SITE_EXTENT_ESTABLISHED / SITE_EXTENT_UNKNOWN                  the site ring
```

Outside the envelope with no site boundary is now a role of its own,
`EXTERIOR_EXTENT_UNRESOLVED`: enough to keep the ground out of an internal
floor finish, and not enough to measure a yard. **No site polygon is
invented.** Synthetic case I draws exactly that situation and holds.

---

## 5 · THE P7757 RESULT

`data/runs/7757/P7757_ROUND6A_GEOMETRY.json`, stage `ROUND_6A_GEOMETRY_ONLY`.

### 5.1 The three spaces §8 and §11 asked for

| | round 5 | round 6 | **round 6A** | disclosed |
|---|---|---|---|---|
| KITCHEN (main) | 3.85 | 5.553 | **8.100 m², 2700 × 3000** | 3.00 × 2.70 = 8.10 |
| W.C | 3.50 (1000 × 3500) | — | **3.375 m², 1500 × 2250** | 1.50 × 2.25 = 3.375 |
| WASH | (same slot) | — | **3.150 m², 1500 × 2100** | 1.50 × 2.10 = 3.15 |

All three on the `CLEAR_INTERNAL_FINISH_FACE` basis, every side attributed.

**KITCHEN** `PS-DR-002-009`, obstructed extent 5.500 m²:

| side | face | band | CAD |
|---|---|---|---|
| west | x = −152339.9 | `PW-DR-002-V--152489.9-150.0` | CAD-306, CAD-307 |
| north | y = −800593.5 | `PW-DR-002-H--800593.5-120.0` | CAD-287, CAD-940 |
| east | x = −149639.9 | `PW-DR-002-V--149639.9-200.0` | CAD-165, CAD-164 |
| south | y = −803593.5 | `PW-DR-002-H--803793.5-200.0` | CAD-335, CAD-168 |

**W.C** `PS-DR-002-015`: west x = −155889.9 (`PW-DR-002-V--156039.9-150.0`,
CAD-297/298), east x = −154389.9 (`PW-DR-002-V--154389.9-150.0`,
CAD-301/302), north y = −802843.5 (`PW-DR-002-H--802843.5-150.0`,
CAD-277/278), south y = −805093.5 (`PW-DR-002-H--805578.0-484.4`,
CAD-276/281).

**WASH** `PS-DR-002-012`: the same two vertical bands, north
y = −800593.5 (`PW-DR-002-H--800593.5-200.0`, CAD-287/940), south
y = −802693.5 (the other face of the W.C's north band). Obstructed extent
2.100 m² — the missing 1.05 m² is the vanity it used to stop at.

Each face was selected because it is the face of that band **facing this
space**, and open space stops at it.

### 5.2 The whole drawing

| | round 5 | round 6 steps 1–5 | **round 6A** |
|---|---|---|---|
| physical-space polygons | 57 | 67 | **70** |
| release eligible | 4 | 6 | **7** |
| on the clear-internal basis | — | — | **36 of 70** |
| observed wall bands | 3,272 | 389 | **423** |
| established wall faces | — | — | **804** |
| lines standing inside a space | — | — | **845** |
| recovered partition spans | 4,159 | 511 | **431** |
| recovered length | 3,743.0 m | 566.1 m | **312.0 m** |
| unresolved gaps | 4,212 | 299 | **295** |

Roles: `INTERIOR_SPACE_UNCLASSIFIED` 47, `VOID_OR_SHAFT_ON_EVIDENCE` 13,
`INTERIOR_ROOM` 10. Identity established 9, unknown 58.

---

## 6 · THE FOUR SCOREBOARDS, KEPT APART (§12)

**A · Historical, round 5 frozen.** `8a90def3ac70301a1398aed5` untouched;
`assert_no_artifact_was_rewritten()` passes. Every replay divergence is
predicted; `UNPREDICTED_DIVERGENCE` is empty for all six rounds.

**B · Round 6A geometry.** The table above.

**C · Supervised P7757.** Six of seven examples HELD; the seventh
(`P7757-OPEN-RECEPTION`, TRADE_ZONE) is `AWAITING_A_LATER_STEP`.

| example | board | status |
|---|---|---|
| P7757-MAIN-KITCHEN-GEOMETRY | GEOMETRY | **HELD** |
| P7757-WC-WASH-GEOMETRY | GEOMETRY | **HELD** |
| P7757-KITCHEN | GEOMETRY | **HELD** |
| P7757-WC-WASH | GEOMETRY | **HELD** |
| P7757-GARDEN-STRIP | SPACE_ROLE | **HELD** |
| P7757-VOID-OVERUSE | SPACE_ROLE | **HELD** |
| P7757-OPEN-RECEPTION | TRADE_ZONE | AWAITING |

**D · Later trade-zone benchmark.** Not scored. The 9.675 m² kitchen trade
quantity is not evaluated in this round, by §12.

**Synthetic.** round 2 12/12 · round 3 16/16 · round 4 22/22 ·
round 5 23/23 · round 6 geometry 15/15 (3 trade awaiting) ·
**round 6A 9/9**. pytest 2,109 passed.

---

## 7 · WHAT IS STILL NOT RIGHT

**P7757 still yields zero exterior spaces.** An envelope is established in
5 of 9 regions and a site boundary in none. Round 6A's §9 machinery means
a missing site can no longer make something interior — but on P7757 no
measured space falls outside the fabric ring either, so there is nothing
for the new role to label. The machinery is exercised only by synthetic
case I. The disclosed 5.616 m² garden strip is still not separable on this
drawing, and that is reported rather than forced.

**34 of 70 spaces have no established basis.** Mostly the large blobs where
a partition is drawn as a single unpaired line: round 6A sets such a line
aside, the two rooms behind it become one space, and the resulting polygon
has a side nothing accounts for — so it is not released. That is the
intended failure mode (it withholds rather than invents), and it is the
next thing to work on.

**The WASH carries only one of its two names.** Its English "Wash" label is
reconciled into a group with the DEWANEYA beside it, and only the Arabic
observation falls inside the room. Identity, not geometry.

**845 lines were set aside as standing inside a space.** Each is recorded
with its length and its reason. A genuine one-line partition would be set
aside by the same rule; where that happens the two rooms merge and the
merged polygon is refused a basis, so nothing false is released — but
nothing true is either.

---

## 8 · BENCHMARK-INFORMED CHANGES, DISCLOSED

| change | what the benchmark told me | what I did NOT do |
|---|---|---|
| `wall_face_ownership` (new) | the kitchen was 800 × 150 mm short | no layer rule, no depth rule, no P7757 coordinate |
| `physical_wall` V3: the spaces-stop token | the 200 mm band lost to a 120 mm glazing line | it ranks below a hosted opening and a two-ended reveal |
| `physical_wall`: stretch sets | a 400 mm band claimed 8.8 m of a line | no new tolerance |
| `room_partition_graph`: the second flood | the counter was the first line met | the frozen enclosure is unchanged and still reported |
| `portal_match`: claims stand down | the W.C/WASH door was left open | a genuine two-way ambiguity is still kept |
| `interior_exterior` + `cad_space_role` §9 | disclosed in the round-6A directive | no site ring is invented |

Nothing opened: the Excel, the كيال, architect take-off totals, structural
or sanitary quantities. The sealed 23010 benchmark was not read.

---

## 9 · FROZEN THIS ROUND

```
WALL_FACE_OWNERSHIP_HASH     a36a3169568d9858ca913fda   SPACE_STOPS_AT_THE_FACE_WALL_OWNERSHIP_V1
PHYSICAL_WALL_BAND_HASH      550e36a8e313a7d0955a2cf9   SPACE_BOUNDED_ONE_LINE_ONE_WALL_PHYSICAL_BAND_V3
CAD_SPACE_ROLE_HASH          bba19efe2c70dcba1e96f078
INTERIOR_EXTERIOR_HASH       5f5bd575cb14541a2679ab00
SUPERVISED_BENCHMARK_HASH    1330ff34ee82740c00d299c2
ROUND_6A_SYNTHETIC_HASH      57bf8257e7ff4051e2f77652
ROUND_6_SYNTHETIC_HASH       6460d1ce80518b49736318d0   (a REPLAY; the freeze records ac4752e4fc44ce02932586a3)
```
