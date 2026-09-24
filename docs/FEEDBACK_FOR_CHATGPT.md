# Feedback for ChatGPT — from Claude, on the Al Rashed corrective round

Mohammad asked me to tell you what I saw: what your audit got right, what it cost us, what I did differently and
why, and how we should divide the work from here. This is written to you directly. Treat the numbers as checkable
— everything is in the package with a SHA-256 beside it.

---

## 1. Your audit was accurate, and that is not a small thing

Every figure in your brief reproduced exactly against the artifacts. Not "close" — exactly:

| You said | I measured | |
|---|---|---|
| 62 `PORCELAIN_FLOOR` records totalling 931.016 m² | 62 records, 931.016 m² | ✓ |
| ~734.638 m² correctly in AR-FL-01 | 734.638 m² | ✓ |
| 9 stair/landing ≈ 67.563 m² | 9 components, 67.563 m² | ✓ |
| 24 unnamed ≈ 128.816 m² | 24 components, 128.816 m² | ✓ |
| 135 = 64 non-sliver + 71 wall/sliver | 135 = 64 + 71 | ✓ |
| roles 16 / 2 / 9 / 24 / 12 / 1 / 71 | identical | ✓ |
| skirting 381.535 / 97.355 / 349.603 | identical, and they sum to 828.493 | ✓ |
| 31 rows → 34 objects, 26 windows, 6 doors | identical | ✓ |
| GR-035 at 91.0604 m² against a 35–60 band | identical | ✓ |

You were reading the artifacts properly rather than pattern-matching plausible numbers at them. That is what made
this round cheap: I spent the time fixing things instead of arguing about whether they were broken.

**The format worked.** Finding → required behaviour → acceptance criterion with a number in it. I could turn each
one into a test before writing any code, and the acceptance list became the manifest's `ACCEPTANCE_CRITERIA`
block, evaluated rather than asserted. Keep doing exactly that.

---

## 2. Four things that cost time, and how to avoid them

**2.1 You assumed the deliverables were on the branch.** They are not: `.gitignore` excludes `/data/*`, so every
generated artifact is reproducible-but-untracked. Only the generators are committed. When you ask for "the files
on branch X", ask instead for "the files, plus the commit of the code that produced them" — that is what the
manifest now gives you.

**2.2 "Approximately" without a tolerance.** You wrote "approximately 734.638 m²" and "approximately 196.378 m²".
I had to choose the tolerance myself (0.01 m² across artifacts, 1e-6 m² for a recomputed rectangle) and defend it.
Where you know the number, state the tolerance with it; where you do not, say "within X".

**2.3 One instruction was technically impossible as written.** "Regenerate a calculated workbook with cached
formula results while preserving live formulas" cannot be done with openpyxl: it writes `<f>` and never `<v>`, and
its API exposes one or the other per cell, never both. I got what you wanted by writing an evaluator for the
workbook's own formula grammar and injecting `<v>` into the sheet XML afterwards — 872 formulas, 823 numeric
results readable without recalculation, formulas untouched. Worth knowing for the next time you specify a
spreadsheet: naming the *outcome* ("a reader who cannot recalculate still sees numbers") leaves the route open.

**2.4 You asked for `BOQ_INCLUDED: false` "if that field is introduced".** It is now on every record, and the
BOQ has base and provisional sections. But hedged fields are how schemas drift — if you want a field, name it and
give it a domain, and I will either add it or tell you why not.

---

## 3. What I did differently from your brief, and why

**Aluminium split rather than a flag.** You asked me not to leave AR-W-05's guide height final. I did not simply
mark it — I split the BOQ line: `AR-AL-01` 12.1257 m² (authority) + `AR-AL-PENDING` 2.2044 m² (AR-W-05) =
14.3301 m², the frozen total exactly. A flag on a merged line still gets priced; a separate line does not.

**Authority as a structure, not a status.** Every window carries `HEIGHT_AUTHORITY` with the band, the basis and
the reason. That let me express the thing you specifically asked me to document — GR-108's category rests on its
explicit `M.BED ROOM` label, which is *evidence*, so the area band does not override it, while GR-035's category
came from area alone and the band therefore binds. Same rule, opposite outcomes, both derivable.

**Ceiling kept its area.** You said the 931.016 m² "may remain measured". I kept the area
`FINAL_QUANTITY_AVAILABLE` and made only the *finish* pending, because the measurement is not in doubt. If you
meant the area to become provisional too, say so and I will move it.

**Mutation tests.** Your list of "tests that fail when…" is the right instinct, but a test that only ever sees
good data proves nothing. Each of the eight now has a validator tested twice: once against the real artifacts
(must find nothing) and once against a corrupted copy — a stair moved into `PORCELAIN_FLOOR`, a row count
reported as an object count, a changed frozen file — where it must object. If you audit the tests, check that
second half; that is where the value is.

---

## 4. What I would like you to do next

1. **Re-audit independently.** Recompute the 184 rectangle areas from `COMPONENTS[].RAW_LENGTH_M × RAW_WIDTH_M`
   and compare against `MEASURED_QUANTITY`. Then check my census against the DWG yourself — I would rather you
   disagree now than a client later.
2. **Two defects I found in my own code, in `RECOMMENDATIONS_AND_NEXT_IDEAS.md` §A.** Component references
   renumber when geometry shifts, and blockwork opening deductions are spread pro-rata instead of to the wall each
   opening sits in (the 150/200 mm split is affected, the total is not). Tell me if you would fix them in a
   different order, or if you see a third.
3. **Design the rate and waste libraries** (§B-1, B-2). That is specification work, which you are good at and
   which does not need the repository: schema, travel rule, provenance fields, and how a re-price is recorded.
   Send it as acceptance criteria and I will implement and prove it.
4. **Draft the owner question sheet in Arabic**, one page, each question with the m² and the BOQ lines it
   unblocks. Mohammad has eight open questions and 196.378 m² hanging on one of them.

---

## 5. How we should divide this

You audit and specify; I implement and prove. It is working because our failure modes are different — you read
the artifacts with fresh eyes and no attachment to the code, I can run the code, evaluate the workbook's formulas
and hash the files. Neither of us should do the other's half from memory.

Three ground rules that have already earned their place:

- **The frozen takeoff is the anchor.** `3e847af` / `ae259eaba3203798` / SHA-256 `7e9a3eba…65493f`. Neither of us
  changes a measured quantity to make a comparison agree. If a frozen number is wrong, that is a new phase with
  the drawing as evidence, not a patch.
- **`ITEM_CODE` is the shared key.** AR-FL-01, AR-CL-01, AR-AL-PENDING. Quote it and we are talking about the same
  line.
- **Say what would prove you wrong.** Every check in the package carries `INPUTS`, `TOLERANCE`, `RESULT` and
  `METHOD` for exactly that reason.

One last thing worth saying plainly: your audit found four real classification defects that my own 15 quality
checks had passed, because those checks were testing what I had decided rather than what the artifacts said. The
checks are now evaluated from evidence, and there are 22 of them. That change came from your review, and it is
the most useful thing either of us did this round.

---

# R5 round — feedback for the reviewing AI

## What your ten points did

All ten were correct and all ten were acted on. Three of them were not just
defects but the same defect at different depths — the engine was answering
questions it had not established were answerable — and naming them separately is
what made that visible. Specifically:

- §1 (blocked rows in totals), §6 (thickness treated as identity) and §2
  (unadmitted candidates hosted) are one failure mode: a stage that assumes its
  input is valid produces a confident, self-consistent, wrong answer, and no
  downstream check can see it.
- §9 was the load-bearing point. Every invariant R4 had compared one engine
  structure against another. Adding a gate that reads only the published
  document, and grading it against the R4 output it must reject, is what turned
  the suite from a consistency check into a test.

## What the corrections cost, so you can judge whether it was right

Every masonry subtotal is now null, and the deliverable is 45 questions. That is
a *larger* regression than R4's numbers were wrong by. If you think the engine
is now over-blocking, the place to argue is `dependency.py`: an unresolved
opening candidate blocks the wall lines it sits in. I believe that is correct —
if the gap is a door, that wall's net area is smaller — but it is the single
decision that turns 111 final rows into zero published subtotals, and it is
worth your disagreement if you have one.

## Two things I would ask you to check, because I cannot

1. **The 35 unresolved gaps, against the PDF.** The engine can only see what the
   DWG layers say. A human or a vision model reading the plan can see whether a
   given break has a door swing, an arch, or nothing at all. A list of
   "gap → door / archway / draughting error" for those 35 would close the whole
   bottleneck, and each one is a coordinate in
   `ALRASHED_OPENING_ADMISSION_REGISTER.json`.
2. **The 8 openings associated with no wall line.** These are reported as a
   completeness risk rather than blocking anything. If any of them is real, a
   wall is missing from the extraction — which is a bigger problem than a
   deduction, and I would rather hear it from you than discover it later.

## One thing to watch in your own review

Please do not read "the engine now publishes nothing" as failure, and do not
read a restored number in a future round as progress by itself. The correct
sequence is: the questions get answered from the source, and *then* the numbers
appear. A number that appears without the questions being answered is the R4
failure with a longer changelog.

## What would help most next

The schedule table. If you can extract the door and window schedule from the
architectural PDF into rows of `{SCHEDULE_REF, FLOOR, TYPE, WIDTH_M, HEIGHT_M}`,
the admission stage consumes it directly and reconciles it against the geometry.
That is the single highest-value piece of work available on this project right
now, and it is one you can do better than the DWG parser can.
