# Engineering invariants

Repository-level rules. They exist because each was learned by getting it
wrong more than once, in different modules, by the same reasoning.

---

## 1 · ORDER IS NEVER IDENTITY

> **Domain entities may never be joined by array position.**

Every cross-module join must use a stable id, an explicit key, or validated
geometry identity.

### Where this has already cost us

| module | what happened |
|---|---|
| `revision_entities` | a space matched by list position changes identity the moment a room is inserted |
| `connectivity` / `face_eligibility` | `cycle_capacity` sorts by cycle count, `components` sorts by length. Joining them on index scored **every component against another component's numbers** |

The second one was found only because a downstream result was absurd. There is
no reason to expect the next one to be so obliging.

### The rule in practice

```python
# NO — two lists, one index
for i, c in enumerate(components, 1):
    cycles = cycle_data[i]["independent_cycles"]

# YES — the entity carries its own value
for c in components:
    cycles = c.independent_cycles
```

Where two collections genuinely must be related, relate them by id:

```python
by_id = {c.component_id: c for c in cycles}
```

`tests/test_engineering_invariants.py` scans the engine for the shapes this
error takes.

---

## 2 · OBSERVATION → EVIDENCE → HYPOTHESIS → INDEPENDENT VALIDATION → PHYSICAL FACT

> **Do not promote a proxy into physical truth.**

Every stage must be nameable, and nothing may skip a stage. The proxies that
have tried to become facts in this project:

| proxy | was read as | actually |
|---|---|---|
| same raster region | "not a doorway" | the recovery signal |
| 60–120 mm separation | "not masonry" | evidence about thickness |
| same region both sides | "validated doorway" | topology evidence only |
| three correlated signals | three proofs | one construction seen three times |
| degree 4 | "a four-way crossing" | often an L corner |
| a 1.14 pt pen | "a wall" | style evidence, one family |
| **nearest parallel line** | **"the other face of this wall"** | **the mate is the one it runs ALONGSIDE** |
| a comment saying "the axes swap" | the transform | they swap **and flip** |

The last two are this round's. The pairing proxy cost every room on the sheet;
the frame proxy silently mirrored an entire round of geometry comparison.

### The rule in practice

- Two **independent evidence families** before anything is VALIDATED.
- Correlated observations of one construction are one observation.
- A single family is a hypothesis and is reported as such.
- `UNRESOLVED` is always an acceptable answer.

---

## 3 · MEASURE THE FRAME, DO NOT REASON ABOUT IT

A coordinate transform written as a code comment is an assumption with good
handwriting. `engine/frames.py` fits the candidate transforms against the
raster wall mask and reports the score:

```
SWAP+FLIPY   1.000        rot270   0.142
swap         0.135        rot90    0.069
```

A 1.000 against a 0.142 runner-up is a measurement. The previous inline comment
— *"on a 270-degree rotation the axes swap"* — was half right, and half right
in a transform means mirrored.

---

## 4 · NEVER INVENT THE MISSING HALF

If one wall face exists, do **not** mirror it by an assumed thickness. If a
room's boundary does not close, do **not** join its ends. If the raster says a
room is there, that says **where to look**, never **what to find**.

A printed dimension validates a candidate **after** generation. It is never an
input to the search.

---

## 5 · A LENGTH WITHOUT A BASIS IS NOT A LENGTH

A doorway is **four facts at once**:

| | BTH-05 |
|---|---|
| material present | **0 m** |
| opening | 1.054 m |
| space boundary | 1.054 m |
| host wall gross | 1.054 m |

Collapsing them into one number makes at least three trades wrong. The
previous round's *"material_length_mm is the only length a quantity engine may
read"* was one such collapse: 23010's own manual benchmark measures **gross**
perimeter and deducts openings later, so the door span belongs to the gross
line.

Every quantity engine declares which basis it consumes (`engine/lengths.py`),
and asking for an unestablished basis **raises** rather than returning zero —
an unestablished basis and a measured zero are different facts.

**Never compare unlike bases.** The 102.70 m site benchmark is a gross
perimeter; comparing it against a length that already removed doors compares
two different measurements that happen to share a unit.

---

## 6 · MATERIALS COME FROM APPROVED RECIPES, NEVER FROM AREA

Recorded now, implemented later:

```
VALIDATED QUANTITY
  → APPROVED CONSTRUCTION RECIPE
    → MATERIAL REQUIREMENT
      → PROCUREMENT ALLOWANCE
        → COST
```

Never: *AI infers materials directly from a drawing area.* The owner supplies
and approves construction recipes before they become active — block dimensions,
blocks per m², mortar, connector spacing, lintel logic, waste factor.

**CALCULATED QUANTITY and PROCUREMENT QUANTITY are always shown separately.**
A waste or safety allowance is its own approved field, never folded into a
measurement.
