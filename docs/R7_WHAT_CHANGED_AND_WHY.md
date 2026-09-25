# R7: one coherent state, and language that matches the calculation

R6 was not accepted. Ten grounds, and — checked against R6's own registers
before any code was touched — all ten hold. This is what each one was, what
replaced it, and what it costs.

**Every number in this document is a declared claim.** Each one carries a
register path, is re-read from the register that decides it, and fails the gate
if it disagrees. The claim register is
`ALRASHED_REPORT_CLAIM_REGISTER.json`; the sentences it generates are in
`GENERATED_PROSE`. What that proves is that every *declared* claim agrees. It
does not prove that no undeclared number exists in this prose, and no part of
this round describes it as if it did.

## The defect that produced the others

R6's pipeline resolved window heights from the room standard **after** it had
already built the opening register, the deductions, the dependency graph and the
question register. The height evidence lived in a dict the opening object shared
with its admission record, so that dict updated in place and read `ESTABLISHED`
— while the serialised registers beside it still carried the pre-category
snapshot, with a null area and a question asking for the height that had just
been answered. Four windows were in that state. Each record was internally
consistent. Together they described two different moments.

The fix is not to reorder the calls by hand. It is to make "the evidence is
final" an explicit, checkable event:

```
admit → resolve hosts → assemble the spaces room use needs → resolve room
evidence → resolve every remaining dimension → FREEZE → derive areas,
deductions, dependencies, questions and documents
```

`freeze` publishes a version derived from the state's own contents. Every
register built afterwards records that version, and the live objects are re-read
afterwards to confirm they still say what the frozen state says. A register
carrying a different version is describing a different moment, and the gate says
so.

## The ten, one line each

1. **Stale derived state.** The barrier above. No window is patched
   individually; `engine/qs_core/final_state.py` is generic and every floor goes
   through it.
2. **No cross-register coherence check.** Ten new document-level checks
   (A22–A31), each with a mutation test that must fail it. A22's mutation is the
   R6 defect performed deliberately: resolve a height after the register exists
   and do not rebuild.
3. **Questions asked of a derived field.** The question register now reads the
   frozen evidence. An established dimension carries no question; an unresolved
   one carries exactly one; answering one removes it and its blockers
   deterministically, which is tested by running the same fixture with and
   without the standard.
4. **An external roof competed with a room.** Host rooms are resolved from the
   two sides of the host wall, using its axis and normal, and classified by a
   role the *caller* supplies — the engine holds no vocabulary for "outside".
   One enclosed room facing one open area resolves to the room; two enclosed
   rooms is a real ambiguity; no enclosed room means no room-use standard
   applies. Six synthetic cases, including rotation, translation and
   resegmentation.
5. **Impacts counted construction paths.** Impacts are a set keyed by fact,
   node, node kind and effect. Every node publishes `BLOCKER_IDS`,
   `BLOCKER_COUNT`, `DIRECTLY_AFFECTED_BY`, `ANSWER_ALONE_RELEASES_NODE`,
   `REMAINING_BLOCKERS_IF_ANSWERED`, `NODE_STATUS` and its downstream nodes.
6. **"Unblocks all 127 rows" was asserted, not calculated.** Three words are now
   distinguished and defined in the register itself: *affects*, *removes one
   blocker*, *releases*. A question may be said to release a node only when it
   is that node's last blocker. Every release sentence in this round is
   generated from the simulation in
   `ALRASHED_BLOCKER_SET_AND_ANSWER_IMPACT_REGISTER.json`.
7. **Thickness used as a wall type.** A material claim carries an explicit
   applicability scope and answers a band only where every attribute it names
   matches. An unscoped claim propagates project-wide only when the evidence
   says that is its scope. The question is asked about a *group* — the bands
   sharing every attribute the source states — and every row says the group is
   not a wall type.
8. **Twenty-three bands left the trade on their shape.** Exclusion needs
   positive evidence: the source naming a column, a proven duplicate, or a
   junction already inside the crossing walls. A short band is a question, not
   an artefact, and weak confidence may never exclude anything. Seven fixtures.
9. **A20 described as verifying the narrative.** The claim register above. The
   gate reports "all declared claims agree" and never calls it anything else.
10. **The gate had no check for any of this.** A22–A31 with ten mutations, and
    the whole gate still scores 0 on the committed R4 output.

## What it costs, and why the cost is the correction

The twenty-three bands R6 excluded are now twenty-three open questions, and the
material questions are asked per scope group rather than per thickness, so there
are more of both than in R6. Neither number is a regression: R6's smaller
figures came from two inferences the source had not made — that a short band is
not a wall, and that one thickness is one material. Removing an unsupported
inference makes the work list longer and the quantity honest.

The nothing-is-published outcome is unchanged and unchanged for the same reason:
this drawing annotates no wall material anywhere, at any scope.

## What was not touched

The frozen blind takeoff (file SHA-256 `7e9a3eba…5493f`) was read and never
written; its digest is asserted equal before and after every run. Qortuba, the
pricing, the owner answers and the web app are untouched. No quantity was tuned
toward the frozen takeoff, the historical workbook, or any previously reported
figure, and the anti-calibration audit is part of the package.
