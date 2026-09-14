# State / release audit — making the database, release and QA layers agree

Every inconsistency you found was real. All are fixed, each with a regression
test, and the workbook is regenerated from source-of-truth records.

---

## A · STATE / RELEASE AUDIT

### The four contradictions, confirmed then fixed

| # | found in the generated .xlsx | now |
|---|---|---|
| 1 | WSH-01 `4.19 m` and BED-04 `49.71 m` both `VALIDATED` / `READY` | both `OBSERVATION`, blocked, values kept |
| 2 | **17 rows** `READY` beside `primary_blocker = trade_rule` | **0** — the type refuses to construct such a row |
| 3 | `applicable=36, blocked=36, N/A=0` for every use | `applicable=23, N/A=13` |
| 4 | `Geometry ready = 36 / unresolved = 0` | four separate layers |

### 1 · Identity and topology are two questions, not one

`REGION_IDENTITY` and a new `PHYSICAL_TOPOLOGY` are now separate release
dependencies, required by **all thirteen** uses (a test asserts every one).

| space | identity | topology | why |
|---|---|---|---|
| WSH-01 | **FAILED** | UNRESOLVED | the region is the hatched shaft *beside* the wash floor |
| BED-04 | VALIDATED | **MERGED** | a real bedroom with an unseparated 1600×3000 bathroom inside it |

One dependency could not express both, and the workbook released quantities for
both spaces while it tried to. Identity failing and topology failing need
different repairs, and now they name themselves differently.

### 2 · READY may never carry a blocker

Enforced in two types, on construction:

```
READY           → no missing dependency, no blocker
BLOCKED_*       → at least one missing dependency, named
NOT_APPLICABLE  → a stated reason
```

The root cause was that `primary_blocker` was computed **once across all uses**
and stamped on every row. It now belongs to the use it blocks. `N/A` needs a
reason because the word was doing duty for both "this trade does not apply" and
"we are not measuring this".

### 3 · OUT_OF_SCOPE is N/A

| scope | treatment |
|---|---|
| IN_SCOPE | evaluate dependencies |
| AMBIGUOUS | `BLOCKED_SCOPE` — that *is* work; the work is an owner decision |
| OUT_OF_SCOPE | **N/A** — nothing measured, nothing queued, nothing to unblock |

`GROSS_PERIMETER` now returns, **derived not hard-coded**:

> **15 READY · 8 BLOCKED · 13 N/A**

which is the sanity shape you predicted.

### 4 · Four geometry layers, never one KPI

| layer | 23010 |
|---|---|
| `RASTER_REGION_AVAILABLE` | 36 |
| `WALL_GEOMETRY_AVAILABLE` | 36 |
| `REGION_IDENTITY_VALIDATED` | **35** |
| `PHYSICAL_TOPOLOGY_VALIDATED` | **33** |
| **validated physical spaces** | **33** |

"Geometry ready = 36" was true of the first layer only and was printed as
though it were the last.

### A bug the fix introduced, and how it was caught

Consulting the E27 rules fixed an **under**-report (they had been hard-coded
`False`, throwing away two signed rule sets). But asking *"does **any** rule
cover this room type"* made `WATERPROOFING_HORIZONTAL` read **13 READY** on the
strength of the **ceramic** rule. A ceramic rule saying a bedroom has a ceramic
floor says nothing about waterproofing.

The question is per trade **and** per room type. `WATERPROOFING_HORIZONTAL` now
correctly blocks on `trade_rule`. Both directions are tested.

### §11 · Rule authority — audited, nothing lost

| layer | 23010 | status |
|---|---|---|
| **1 · approved project trade rule** (E27) | `23010_ceramic` V1.0, `23010_plaster` V1.0, 15 room rules each | **intact, now used** |
| 2 · approved room/trade template (E45) | none | empty |
| 3 · nothing | — | and nothing means nothing |

The template layer displaced nothing. A template is reusable structure a
project rule may reference; it never replaces one. **NULL TEMPLATE must never
mean NULL PROJECT RULE** — tested.

### A frozen input I nearly broke

Promoting the topology facts into the space map changed its sha256, and
`test_every_frozen_input_still_hashes_to_what_was_audited` **caught it**. Run 1
was scored against that hash; editing it retroactively would have broken the
acceptance run's reproducibility.

The facts now live in `data/golden/23010/topology_overlay.json`, outside the
frozen inputs, and the original bytes were recovered exactly. A space with **no**
overlay entry gets `UNRESOLVED`, so a missing overlay fails closed rather than
releasing everything.

---

## B · ROOM / ZONE MODEL

Three things were being asked of one record:

| layer | what it is |
|---|---|
| `SEMANTIC_OBSERVATION` | a name read off the drawing. Evidence a room *exists*. Says nothing about geometry |
| `PHYSICAL_SPACE` | a polygon with validated identity **and** topology. The only thing a quantity may be attributed to |
| `FUNCTIONAL_ZONE` | a *use* of space. May share one open polygon |

Two rules are enforced in code:

- **A label is not a room.** No amount of confidence or human verification
  promotes an observation to a physical space.
- **A zone is not a wall.** `FunctionalZone(boundary_is_physical=True)`
  **raises** — a dining zone that drew its own boundary would invent wall
  length, and inventing wall length is how a takeoff becomes fiction.

---

## C · ROOM COUNT SUMMARY

| room type | observed | validated | unresolved | zones |
|---|---|---|---|---|
| **WASHROOM** | **1** | **0** | **1** | 0 |
| BEDROOM | 5 | 4 | 1 | 0 |
| SALOON | 2 | 2 | 0 | **1** |
| CORRIDOR | 3 | 3 | 0 | **1** |
| **DINING** | 0 | 0 | 0 | **1** |

`WASHROOM: 1 observed, 0 validated` is the answer you asked for. The old
workbook said `WASHROOM = 1` on the strength of a human-verified label attached
to the wrong region — telling an owner "1 washroom detected" when the engine
had recovered zero validated washroom polygons.

`DINING` appears with 0 observations and 1 **zone**: it is a real use of
OPEN-01, countable without existing as a separate polygon. OPEN-01 keeps its
dining, saloon and circulation zones and remains **one** physical space.

Manual columns are now three: expected total, expected in-scope, expected
functional.

---

## D · QUANTITY TRACE

`quantity_role` decides what a number may be *used* for:

| role | 23010 | meaning |
|---|---|---|
| `RELEASABLE_QUANTITY` | 15 | validated, attributable, usable in a takeoff |
| `CANDIDATE` | 18 | attributed, pending validation |
| `OBSERVATION` | **3** | measured, attributed to nothing, **may never be released** |

```
WSH-01  value 4.19  role OBSERVATION  release BLOCKED_REGION_IDENTITY
BED-04  value 49.71 role OBSERVATION  release BLOCKED_PHYSICAL_TOPOLOGY
```

Both keep their values. An `OBSERVATION` must say **what it measured** — "the
traced boundary of raster region 361, which is not a validated washroom" — and
may never be `READY`, because it is attributed to no space and so has nothing
to be ready *for*.

---

## E · COVERAGE MATRIX

| use | ready | blocked | N/A | commonest blocker |
|---|---|---|---|---|
| `GROSS_PERIMETER` | **15** | 8 | 13 | scope |
| `GROSS_WALL_AREA` | 0 | 23 | 13 | height |
| `GROSS_CERAMIC_WALL` | 0 | 23 | 13 | height |
| `GROSS_PLASTER` | 0 | 23 | 13 | height |
| `WATERPROOFING_HORIZONTAL` | 0 | 23 | 13 | **trade_rule** |
| `WATERPROOFING_VERTICAL` | 0 | 23 | 13 | height |
| `CEILING` | 0 | 23 | 13 | ceiling_geometry |
| `BLOCKWORK` | 0 | 23 | 13 | physical_wall_split |
| `EXTERNAL_FINISH` | 0 | 23 | 13 | external_split |
| `NET_CERAMIC_WALL`, `NET_PLASTER`, `PAINT`, `SKIRTING` | 0 | 23 | 13 | openings |

---

## F · TOP-LEVEL STATUS

Two fields, because one word was answering two questions:

| | |
|---|---|
| `TAKEOFF_COVERAGE_STATUS` | **VALIDATED_PARTIAL** — 1 of 13 uses has a ready quantity; 15 of 17 in-scope spaces validated |
| `FINAL_BOQ_STATUS` | **BLOCKED_FOR_FINAL_BOQ** |

Blockers: no opening validated · no NET quantity ready · 3 spaces with
unresolved topology · the wall graph fails its E31A gates.

Coverage is a **proportion**; BOQ readiness is a **conjunction**. A test asserts
no coverage variable appears in any condition that decides a BOQ blocker — a
takeoff that is 90% covered is 0% quotable.

---

## G · CONNECTIVITY DIAGNOSTIC

Unchanged from the last round (the graph itself was not touched):
115 components · 7 major holding 57.9% · 228 termini (109 unresolved, 31
repairable) · 23 unexplained disconnects · 17 stitches validated, 12 rejected
by an end cap · length drift 0.2 mm.

### Gates corrected

| gate | before | now |
|---|---|---|
| G1 | *"drift == 0.0 mm"* while accepting 0.2 | `abs(drift) <= ABSOLUTE_NUMERICAL_EPSILON_MM` (1.0 mm, **absolute**, never a percentage) |
| G4 | gating on a ≥80% concentration I chose | **DIAGNOSTIC_ONLY** — never gates |
| G8 | `NOT_MEASURED` | **measured** |

You were right about G4: a component holding 90% of the metres and no cycle
bounds nothing, and one holding 3% around a shaft bounds a real room.

**G8, now measured** — 43 independent cycles in 12 components; **14 of 17**
in-scope regions could be enclosed. **3 cannot: BTH-01, BTH-02, BTH-03.** For
those the graph contains no cycle that could possibly enclose them.

It is reported as `NECESSARY_CONDITION_ONLY`: a failure is conclusive, passing
is *not* proof — only face extraction can upgrade it.

| gate | status |
|---|---|
| G1 length, G2 clusters, G6 junctions, G7 fragmentation | **PASS** |
| **G3 termini, G5 unexplained disconnects, G8 cycles** | **FAIL** |
| G4 concentration | diagnostic only |

**Verdict: NOT READY — 3 failing, 0 unmeasurable.** E31A not started.

---

## H · DASHED TOPOLOGY — a clean negative

**The sheet contains zero PDF-level dashed strokes.** Every stroke path is
`[] 0`; every fill path has no dash array. `VectorPath.is_dashed` is correct and
finds nothing: the dashed thresholds are **exploded linetypes**, rows of short
solid segments, so a pattern has to be recovered geometrically.

Built that: collinear same-pen short marks with regular gaps. Fill paths are
excluded — a hatch body is regularly spaced *by construction*, and admitting
fills put 197 glyph-outline runs into the candidate list.

**536 candidates, 177.1 m.** Every one is `TOPOLOGY_BOUNDARY_CANDIDATE` with
`boundary_type = UNKNOWN`. A dashed run is not a door and not a wall.

### Washroom acceptance case: FAILED, and the failure is informative

- Region **441** (the true wash floor) is **not found by the segmentation at all**.
- The runs near WSH-01's region 361 are **8 mm marks with 8 mm gaps** over 165 mm,
  and **24 mm marks with 5 mm gaps** over 84 mm. That is the shaft symbol's
  **hatch fill**, not a threshold.
- Nothing near the washroom has the span or mark size a drawn threshold has.

**Dashed evidence does not recover the washroom boundary.** It was not told to
look for 1500 × 2400 and it did not find it. The washroom stays unresolved.

---

## I · BUILDING ENVELOPE — not built

`EXTERIOR_END = 0` still, and terminus classification is still incomplete
because of it. I did not start the envelope this round: the state/release audit
was the stated priority and it took the whole round. It is named as the
engineering next action on the "Unclassified wall ends" finding, so it is not
lost.

---

## J · QA WORKBOOK — regenerated, verified

All 11 sheets from source-of-truth records. Verified in the emitted file:

- ✅ WSH-01 is **not** presented as a validated washroom quantity
- ✅ BED-04's merged topology blocks its release
- ✅ OUT_OF_SCOPE = 13 N/A on every use
- ✅ 0 READY rows carry a blocker
- ✅ four geometry layers shown separately
- ✅ physical-room counts differ from semantic observations where they should
- ✅ OPEN-01 keeps dining / saloon / circulation zones
- ✅ coverage and final-BOQ statuses distinct
- ✅ exception narratives generated from **this** run, each carrying
  `finding_id`, `diagnostic_run_id` and `evidence_reference`

The disproved sentence — *"wall faces are drawn as thousands of short
segments"* — is gone, replaced by the measurement that disproved it:
*"source-path fragmentation is NOT the cause — only 993 of 55,144 short marks
share a path with a long run. 333 wall end caps were recovered…"*

And **three** action columns, so a stronger source never looks mandatory:
`engineering_next_action` (always present) · `owner_input_required` (none on
the graph finding) · `owner_input_helpful_if_available` ("a DWG would make wall
connectivity exact rather than reconstructed. It is **NOT** required — the PDF
pipeline continues either way").

---

No pricing. No material recipes. E31A not started.
