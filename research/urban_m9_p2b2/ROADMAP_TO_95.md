# Roadmap to 95 % (deliverable 15)

## 1. What "95 %" should mean

A target that can be measured on a drawing set without trusting the engine's own opinion:

1. **Coverage**: at least 95 % of the BOQ lines of the architectural route carry a released quantity
   (MEASURED / SOURCE_DERIVED, or PROJECT_SPECIFIED through the rules sheet); every other line is a BOUNDED_EXPOSURE
   with its range or a NOT_APPLICABLE with evidence - none left BLOCKED_RFI for a document the project already has.
2. **Completeness**: the surface ledger conserves, CONFIRMED_MISSING = 0, no unclassified question.
3. **Accuracy**: on a blind test (protocol of Phase 2A, `research/urban_m9_p2a_acceptance`; formal blind testing has
   not started) every released total within its tolerance of an independent take-off.
4. **Stability**: V1 .. V2.x frozen, determinism and metamorphic tests green.

## 2. Where V2.4 stands (no project rules, no facts)

| Drawing | Lines | Released (MEASURED / SOURCE_DERIVED) | + PROVISIONAL | BOUNDED_EXPOSURE | BLOCKED_RFI |
|---|---|---|---|---|---|
| synthetic villa | 101 | 40 % | 56 % | 5 % | 33 % |
| reference plan | 497 | 29 % | 51 % | 8 % | 34 % |

Ledger: conserves on both, CONFIRMED_MISSING 0, 0 unclassified questions. The blocked lines wait for documents, not
for code: on the reference plan the largest question groups (instances) are wall finish heights 56, window types and
sills 34, floor finish specification 28, stair sections 25, waterproofing penetrations 17, waterproofing system
details 17, doorway waterproofing details 15, door evidence 13, space identity 10.

## 3. The path, in order of quantity unlocked per unit of work

| Step | Work | Closes (reference-plan instances) | Kind |
|---|---|---|---|
| 1 | **Project facts intake from sections / finish schedule**: wall finish heights, ceiling heights, sills (the facts file exists; the reading of section drawings does not) | wall finish heights 56, part of window types 34 | engine + documents |
| 2 | **Window schedule binding** (types, sills, floor-level glazing) - also makes the window-threshold upturn exact (review O-1) | window types 34 | engine |
| 3 | **Urban default doorway waterproofing detail** (owner question N-1) and the project system data sheet (UP-WP-MAT-001) | doorway details 15, system details 17, a CONFIRMED roll count | owner + documents |
| 4 | **Drainage / plumbing drawing as a second source** for penetrations (review O-4) | penetrations 17 | engine |
| 5 | **Structural plan binding for door host walls** (route G already reads walls and columns; review O-5) | the structural approvals of every enlargement; REQUIRES_ENGINEERING_REVIEW -> a decided class | engine |
| 6 | **Finish specification and stair sections** (floor tile sizes, stair finishes) | floor finish 28, stair sections 25 | documents |
| 7 | **Door evidence and space identity**: door schedule / tags, room tags (tag binding for project rules, review O-9) | door evidence 13, space identity 10, main entrance 3 | engine + documents |
| 8 | **Project rules bound to the drawing hash** (review O-8) and one OUT folder per method enforced | safety, no new quantity | engine |
| 9 | **A second and third reference plan** incl. a roof / balcony plan (review O-10), then the formal blind test | accuracy evidence | validation |

Expected effect on the reference plan, counted from its question groups: steps 1 - 4 address about 140 of the 245
B-group instances (wall finish heights 56, window types 34, waterproofing system details 17, penetrations 17,
doorway details 15); with step 6 about 190. How many blocked lines that releases is not measured yet - measuring it is
the first task of the next phase. The remainder needs the structural binding (step 5), the door / space tags (step 7)
and the owner questions (N-1 .. N-4, OQ-02 .. OQ-04).

## 4. What must not change on the way

- every new behaviour behind a new opt-in method version (V2.5 ...), the earlier outputs byte-identical;
- no assumption promoted to a released quantity: a missing document stays a bounded or blocked line with its question;
- the four door views and the waterproofing systems never summed;
- the rules sheet and its hash in every output.
