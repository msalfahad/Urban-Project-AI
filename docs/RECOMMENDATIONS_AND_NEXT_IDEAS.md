# Recommendations: how to make the engine and the BOQ better

Written after revision 3 of the Al Rashed package. Everything here is a proposal, not a change — nothing below
has been implemented, and none of it touches the frozen takeoff.

Two of these I found while preparing this package and would fix first, because they are defects rather than
improvements.

---

## A. Two defects I found in our own code this round

### A-1. Component references renumber when the geometry changes — **fix before the next villa**

`COMPONENT_REF` is built as `f"{floor[:2]}-{k:03d}"` where `k` is the index of the component in the scan order
of the grid (`research/qs_wall_treatment_01/pa09/alrashed/takeoff.py:119`).

If a wall line moves by 5 mm in a revised DWG, the grid gains or loses a line, the scan order shifts, and
**every reference after that point changes**. `GR-035` in revision A is not `GR-035` in revision B. That breaks
exactly what we will need most: comparing two drawing revisions, and holding an owner's decision ("the unnamed
space GR-071 is a store") against a re-run.

**Proposal.** Derive the reference from geometry, not from order: the rounded centroid of the component in
millimetres, hashed to a short token — `GR-7f3a21` — plus a `PREVIOUS_REF` field when a re-run matches an old
component by overlap. Cost: half a day, plus a migration note in the export. It is cheap now and expensive after
three more projects have references in circulation.

### A-2. Opening deductions are spread pro-rata across wall thicknesses

In `blockwork_audit` the openings of a floor are pooled and then shared out by length:
`share = ln / confirmed_len`, `ded = op_area * share`
(`final_takeoff.py:232`). So a door that physically sits in a 200 mm wall removes a slice of the 150 mm line too.

The **total** blockwork is right. The **split between AR-BL-01 and AR-BL-02 is not**, and those are priced at
different rates. On this villa: 190.289 m² at 150 mm and 963.188 m² at 200 mm, with 108.4 m² of openings
distributed by length rather than by host.

**Proposal.** Each opening already has a position and a host wall thickness (the glazed openings carry
`HOST_WALL_THICKNESS_M`, and the jamb openings sit inside a known wall cell). Deduct each opening from the band
it actually sits in, and publish an `OPENING_TO_WALL_BAND` register so the allocation is auditable. Expect the
200 mm line to grow and the 150 mm line to shrink; the sum stays as it is.

---

## B. The BOQ itself

### B-1. A rate library with the same travel rule as the standards
Quantities already distinguish "this villa's number" from "an Urban rule". Rates should too: an Urban rate that
travels, a project rate that does not, each with a date, a source (supplier quote, historical contract, market)
and a currency. The BOQ then references a rate id rather than holding a number, and re-pricing a project is a
library swap, not a re-type.

### B-2. Waste as a rule table, not a column someone fills in
`WASTE_PERCENT` is empty by design. It should be filled by a table — porcelain 7–10%, blockwork 3%, paint 5% —
each entry carrying who approved it and when. Then `PROCUREMENT_QUANTITY` computes itself and the difference
between *measured* and *bought* becomes visible for the first time.

### B-3. Every provisional line should name the question that unblocks it
`AR-FL-PENDING` waits on "what finish do the stairs and unnamed spaces take". `AR-CL-01` waits on the ceiling
plan. Put the question id in the line: `BLOCKED_BY: Q-02`. The owner then sees, per question, exactly how many
m² and how many BOQ lines move when they answer — 196.378 m² for Q-02, which is the strongest possible argument
for answering it.

### B-4. A confidence grade per line, not per project
Three grades would do: **MEASURED** (from drawn geometry), **DERIVED** (from a measured quantity plus an owner
input — anything using the 3.60 m height), **ASSUMED** (a standard's fallback). Today a reader has to infer this
from `RULE_LEVEL` and `MEASUREMENT_BASIS`. A grade column makes a priced BOQ honest at a glance, and it makes
the sensitivity obvious: change the wall height and every DERIVED line moves.

### B-5. Procurement packages, not just trades
A trade is how we measure; a package is how Urban buys. Blockwork 150 + 200 + their mortar is one subcontract;
porcelain floor + wall + preparation + skirting is another. A `PACKAGE` column lets the same BOQ print as a
tender document per subcontractor without a second takeoff.

### B-6. An explicit no-double-count matrix
We assert that a tiled face takes no paint and that a stair takes no floor finish. Those relationships should be
a published matrix — trade × trade × "may overlap / must not overlap / must be complementary" — checked by QA
rather than by reading the notes. It is the cheapest protection against the most expensive BOQ error.

### B-7. Bilingual item master
`AR-FL-01` should resolve to one Arabic name and one English name in a project-independent master. Today the
Arabic lives in the workbook and the English in the JSON, and they are kept in step by hand.

---

## C. The engine

### C-1. Heights from sections and elevations
The single largest source of "owner input" in this project. Every vertical quantity currently rests on AR-01's
3.60 m. Reading level marks off the section sheets would move those lines from DERIVED to MEASURED.

### C-2. A polygon path for non-orthogonal plans
The exact decomposition assumes axis-aligned walls. It is right to refuse rather than approximate, but the
refusal means the engine simply cannot quote a villa with an angled wing. The P7757 work already has the harder
machinery; wiring it in behind the same closure check is the unlock for "any villa", not just "an orthogonal one".

### C-3. Role candidates with one-click review
128.816 m² is `UNNAMED_ON_DRAWING`. Adjacency and shape can *propose* (a 1.2 m² cell off a bedroom with one door
is a wardrobe, not a lobby) as long as a proposal never becomes a quantity without a click. That is a review
screen, not an inference engine.

### C-4. Drawing-revision diff as a first-class output
Given two DWGs, the engine should publish what changed: components added, removed, resized, and the quantity
delta per BOQ line. With A-1 fixed this is nearly free, and it is the feature a contractor will value most.

### C-5. Run the same villa twice, deliberately
We have never run the engine twice on the same inputs and diffed the outputs byte for byte. It should be
deterministic; we have not proved it. One command, one assertion — worth doing before the next project.

---

## D. What I would do in what order

| | Item | Why first | Size |
|---|---|---|---|
| 1 | A-1 stable component references | everything downstream depends on ids that currently move | S |
| 2 | A-2 per-opening deduction | a real mis-split between two priced lines | S |
| 3 | C-5 determinism check | cheap, and it protects every claim we make | XS |
| 4 | B-3 blocked-by on every provisional line | turns the owner's eight questions into a prioritised list | S |
| 5 | B-1 + B-2 rate and waste libraries | the BOQ cannot be priced without them | M |
| 6 | B-4 confidence grades, B-6 overlap matrix | make the priced BOQ defensible | M |
| 7 | C-1 heights from sections | removes the biggest assumption in the model | L |
| 8 | C-2 non-orthogonal path | removes the biggest scope limit | L |

---

# R5 round — where the engine should go next

## 1. The 35 unexplained gaps are the whole bottleneck, and they are cheap to close

Every masonry subtotal on this villa is null for one reason: 35 breaks in wall
lines that nothing in the DWG names as an opening. Three sources could answer
them without touching the engine:

- the **door and window schedule**, if it exists as a table in the PDF — the
  admission stage already takes schedule rows and reconciles them against the
  geometry, so this is a data connection, not new logic;
- the **sections and elevations**, where a doorway and an archway look nothing
  alike;
- the **owner**, for the handful the drawings genuinely do not settle.

Closing them turns 19 blocked rows into final rows and makes 150 mm and 200 mm
publishable. Nothing else in the pipeline has anything like that leverage.

## 2. Teach the admission stage to read an opening schedule table

`normalize_opening_population` already accepts `schedule_rows` and reports
`SCHEDULE_ROWS_WITHOUT_GEOMETRY`. What is missing is the extractor that turns a
PDF schedule table into those rows. That single piece of work converts the
largest class of open questions into evidence on every future project, not just
this one.

## 3. Let a candidate inherit provenance from an identical twin

Several of the 35 gaps are the same width, on the same layer, in the same wall
family, as gaps that *do* carry a door block. A generic rule — a candidate whose
geometry and context match a confirmed opening within tolerance inherits its
classification, at `STRONG` rather than `PROVEN`, and says which twin it copied
— would resolve a good share of them on evidence rather than assumption, and is
falsifiable by a reviewer reading the twin reference.

## 4. Vertical continuity is still missing

Identity, spaces and quantities are per floor. Stairs, voids and double-height
rooms have no cross-floor relation, so a void is floor area the adapter must
exclude by hand — the same class of manual patch this round removed for walls.
A `LEVEL_RELATION` register (this space is open to that one above) is the next
structural gap.

## 5. Ceilings and finishes are where the next R4-shaped failure is waiting

Wall quantities now have identity, basis, provenance and a blocking graph.
Ceilings have an area and a type nobody established. If ceilings are priced
before they get the same treatment, the review that follows will be this one
again, in a different trade.

## 6. For the BOQ itself

- Publish **blocked rows as visible bill lines with null quantities and the
  question attached**, not as omissions. A bill with 19 explicit gaps is
  auditable; a bill quietly 19 rows shorter is not.
- Carry `DIAGNOSTIC_ONLY_*` figures into the workbook in a separate,
  differently-formatted column. Estimators need a size to plan around; the
  format has to make it impossible to add that column to a total.
- Add the **seam evidence** and the **wall identity** as columns on the
  measured rows. They are the two decisions a human reviewer can most usefully
  falsify, and both are currently only in JSON.
