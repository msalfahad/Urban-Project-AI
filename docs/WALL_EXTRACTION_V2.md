# Wall extraction V2 — the root cause, and how far it got

You were right that the face walker was not the problem. The measurement found
two defects, both in how walls are recognised, and one of them silently
corrupted the previous round's geometry comparison.

---

## The finding that matters most

> **Every side of every control room DOES have its two parallel heavy-pen
> faces, ~150 mm apart. Pairing rejected them anyway.**

Because `wall_pairs` ranked candidate mates **by gap alone**:

| candidate | gap | overlap | |
|---|---|---|---|
| a scrap of fixture linework | **105 mm** | 100 mm | ← won |
| the actual other face of the wall | 151 mm | **2400 mm** | ← lost |

The scrap is 46 mm nearer and has one twenty-fourth of the overlap. *"Nearest
parallel line"* is a proxy for *"the other face of this wall"*, and on a drawing
full of fixtures it is a bad one.

**A mate is now the face a wall runs ALONGSIDE.** And note which part of the
score does the work: a short scrap wholly covered by a long face has a
*perfect* overlap **ratio**, so the ratio ties at 1.0 — the absolute **overlap
length** separates them. Distance points the wrong way in both.

## The defect that corrupted the last round

The vector↔raster transform lived as a code comment:

> *"on a 270-degree rotation the axes swap"*

They swap **and flip**. Measured against the raster wall mask:

| | fit |
|---|---|
| **SWAP + FLIP-Y** | **1.000** |
| rot270 | 0.142 |
| swap | 0.135 |
| everything else | ≤ 0.077 |

**Last round's G8 result and every vector↔raster correspondence were computed
mirrored.** The BTH-01/02/03 diagnosis — *"no wall pair within 2 m"* — was an
artifact of that mirror, not a fact about the drawing. `engine/frames.py` now
fits the transform and **refuses** an ambiguous or poor one rather than picking.

---

## A · Wall representation distribution

| type | bands |
|---|---|
| `DOUBLE_FACE_WALL` | **243** |
| `SINGLE_LINE_WALL` (candidates, never mirrored) | 49 |
| filled / rectangular / composite / curved | 0 on this sheet |

AR-00 is drawn entirely with double-face walls. The vocabulary exists so the
next architect's filled-band drawing does not fail for it.

## B/C · Forensics — controls and hard cases

All six rooms inspected have **two heavy-pen faces on every side**, ~150 mm
apart, at the sheet's wall pen. BTH-01's north: 1.14 pt at −175 and −26.3.
South: +38.7 and +190.1. This is a clean, regular, machine-readable drawing —
the extraction was the problem, not the drawing.

## D · Pairing rejections, on the probable-wall population only

948 probable wall faces (not 35,835 glyph strokes):

| reason | count |
|---|---|
| `FRAGMENTED_MATE` | 259 |
| `INSUFFICIENT_OVERLAP` | 154 |
| `NO_PARALLEL_FACE` | 49 |

`FRAGMENTED_MATE` was 402 before I replaced strict mutual-best with **global
greedy** matching: where A's best is B and B's best is C, A was discarded even
with a good mate still free.

## E · Heavy-pen precision

| | |
|---|---|
| wall pen (measured, not chosen) | **1.14 pt** |
| strokes at that pen | 462 |
| that became a band face | ~40% |

**Precision well below 1.0 — so it stays `WALL_STYLE_EVIDENCE`, one family of
four,** and never classifies alone. That is the measurement you asked for, and
it argues against promotion.

## F · End-cap contribution

333 caps recovered; they contribute the `CLOSURE` evidence family and help
`END_CAP_INTERRUPTION` be distinguishable from a genuine gap. They do **not**
create walls.

## G · Wall band candidates

| | |
|---|---|
| bands | **243** |
| `VALIDATED` (2+ families) | **190** |
| `PROBABLE` | 53 |
| total length | **615.1 m** (was 387 m) |
| separations | 62 × 120–180, 109 × 180–260, 33 × 260–400, 26 × 60–120 |

### A second fix: a band spans the UNION of its faces

At an L corner the outer face runs past the inner one by a wall thickness — the
inner face stops early *because the perpendicular wall occupies that corner*.
Taking the intersection made every band stop short of every junction, so
perpendicular bands never met.

| | intersection | union |
|---|---|---|
| band length | 446 m | **615 m** |
| components | 90 | **42** |
| cycles | 26 | **62** |
| T-junctions | 20 | **53** |

## H · Rebuilt graph health

| | before V2 | after V2 |
|---|---|---|
| edges | 264 | **369** |
| T-junctions | 8 | **53** |
| components | 115 | **42** |
| independent cycles | 43 | **62** |
| termini | 228 | **145** |
| length drift | 0.2 mm | **0.0 mm** |

## I · Positive controls — **still 0 of 4. The gate is not met.**

Bounded faces went 6 → 14, but every one is ≤ 2 m² apart from the 989 m²
building outline. **No normal room closes yet.** 145 termini and 48 unclosed
walks remain.

Per your §12, I have **not** returned to BED-04 or the washroom. Hard cases do
not drive the basic wall model, and the gate is the gate.

## J · Building envelope

Unchanged and deliberately not loosened. The two-family requirement stands.

---

## K · Wall Extraction QA sheet

New sheet, 140 rows: every band with its faces, caps, pen evidence, raster
support and validation status, plus every unpaired face with its rejection
reason and the best mate it saw (gap and overlap). This is the sheet that would
have made the pairing defect visible without reading raw vectors.

## M · Engineering invariants — now repository-level

`docs/ENGINEERING_INVARIANTS.md`, enforced by
`tests/test_engineering_invariants.py` across **every** engine module:

1. **ORDER IS NEVER IDENTITY** — a static scan for entity collections
   subscripted by a loop index.
2. **OBSERVATION → EVIDENCE → HYPOTHESIS → INDEPENDENT VALIDATION → PHYSICAL
   FACT** — every `MIN_FAMILIES_*` constant must be ≥ 2; every classifier must
   have an `UNRESOLVED` state.
3. **MEASURE THE FRAME** — a transform in a comment is an assumption with good
   handwriting.
4. **NEVER INVENT THE MISSING HALF** — no module may mirror a lone face by an
   assumed thickness.

The proxy table now has nine entries. Two are this round's.

---

## Where this leaves us

Wall **extraction** is substantially better and the root cause is fixed and
tested. Room **closure** is not solved: the remaining 145 termini and 48
unclosed walks are the next target, and they are now a much smaller and better
characterised problem than 228 termini across 115 components.

No pricing. No material recipes. No E34. No BOQ. The face walker was not
touched.
