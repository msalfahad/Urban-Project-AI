# M6 executive report — completeness and discrepancy detection

**Verdict for the benchmark project: still NOT QUOTATION-READY; the gate stays INCOMPLETE.** M6 changes no
quantity. It adds the engine that tells a reviewer, sheet by sheet, what the drawing shows that the takeoff does
not hold, and it was validated on drawings it had never seen.

## A. What was built

1. **A generic completeness engine** (`engine/source/concrete_completeness.py`, policy V2) that runs inside the
   one-command BOQ (route G). Ledgers: geometry (lines, arcs, circles, fills), members, labels, schedule, storeys,
   vertical continuity, notes and dependencies, overlaps, slab coverage, unresolved items. Output: a located finding
   register, a signal register (every signal's terminal state), a scope checklist, an HTML/PDF review page and
   BOQ section E. Findings carry a volume only when drawn geometry meets a printed section or thickness.
2. **A synthetic test bench with truth from the generator**: 16 injected element kinds + 3 V2 kinds, distractors,
   storey variants, two vocabularies, hard distractors. 40 + 40 held-out drawings per engine version.
3. **A frozen, reproducible benchmark protocol**: engine freeze → held-out → blind run hashed → reconciliation →
   weaknesses traced on the drawing → new freeze → new held-out → declared post-discovery run. Both ST7757 runs
   rebuild byte for byte from the engines as committed (read from git).

## B. Results

| Measure | V1 (`090a470`) | V2 (`6c20879`) |
|---|---|---|
| Development seeds 1–16, V1 cases | 153/153, 0 false | 153/153, 0 false |
| Development seeds 1–16, with V2 cases | 159/183, 2 false | 183/183, 0 false |
| Held-out V1 seeds 101–140 (dev / held-out vocabulary) | 383/384, 2 false · 384/384, 1 false | identical |
| Held-out V2 seeds 201–240, dev vocabulary | 422/470, 15 false | **470/470, 9 false** (8 pre-existing) |
| Held-out V2 seeds 201–240, held-out vocabulary + hard | 436/470, 37 false | **470/470, 11 false** (10 pre-existing) |
| ST7757 completeness cases, matcher M1 | 19/32 (blind) | 20/32 (post-discovery) |
| ST7757 completeness cases, matcher M2 | 19/31 (blind) | 30/31 (post-discovery; 10 of them unidentified) |
| ST7757 findings supported by an external source (M2) | 42 of 76 | 58 of 93 |

"Pre-existing" false findings are present in the same seeds without any V2 case and with the V1 engine: almost
all are route slab errors (bays merged into a 17–85 m² "opening" region) that the completeness engine reports
correctly but the synthetic truth does not model.

## C. What V2 fixed (generic rules, each traced on the drawing)

| | Weakness | Evidence it was real | After V2 |
|---|---|---|---|
| W1 | An unbound route mark (AMBIGUOUS) was "consumed" by an unmarked, unresolved band beside it | CB10 ×2 on the 1F plan | reported with its route state; CB10 detected |
| W2 | Fills on hatch-named layers were thrown away as annotation; any fill inside a member counted as the member's | 7 hatched cantilever bands, 3 beams measured over them, 6 hatched panels | 14 fill-on-member findings; 6 cantilever portions linked by DXF entity, 3 beams by item; whole-plan foundation fill reported LOW |
| W3 | A footing explained everything drawn inside it | lift-pit walls + fill inside footing FF | pit reported on the foundation plan |
| W4 | No family prior for a pit; walls broken at columns left a closed outline, not a ring | the same pit | "could be LIFT or WALLS or WATER_TANK" |

## D. What is still not working

- **W5 (new, found on held-out V2):** two legend rows close together are not read (each swatch sees both captions).
- **W6:** a fill whose legend is not on the plan (another sheet, the PDF) stays UNKNOWN — 13 of 14 fills on ST7757.
- **W7 (route, not this engine):** the slab face builder merges bays into large "opening" regions on some designs.
- **Family naming lags detection** (held-out V2, detected elements that have a family: 86–88 % named right,
  10 % unknown, 3–4 % wrong).
- **One real project only.** V2 on ST7757 is post-discovery; it cannot be read as blind accuracy.
- W1 has no synthetic generator case (hand-built fixture only).

## E. Recommendations — next

1. **Second real project, blind**: freeze V2 (done), run it on a new drawing set with an independent estimate,
   reconcile only after the freeze. This is the only test that measures real-drawing accuracy.
2. **V3 legend reader**: caption nearest each swatch (row alignment), legends on notes / detail sheets and in the
   PDF evidence adapter (W5, W6); keep naming as candidates when the legend is absent.
3. **Route slab face builder** (W7): stop bay merging into "opening" regions; add slab-route-error truth to the
   evaluator so these become confirmed route errors rather than false findings.
4. **Generator**: paired parallel beams with a mark between them (W1), legends below the plan, pits beside
   columns rather than round them.
5. **Reviewer workflow**: use BOQ section E / `COMPLETENESS_REVIEW` as the RFI list for ST7757 — the 14 fills
   (cantilever portions and the 6 panel fills of unknown meaning), the lift pit, the 452 m² foundation fill
   (blinding scope), the AMBIGUOUS CB10 labels.

## Notes for ChatGPT (what worked / what did not / what next)

- **Worked:** freeze → blind → reconcile → trace on the drawing → generic rule → new freeze → fresh held-out. The
  V2 rules found every V2 case on 80 unseen drawings (73/73 in each vocabulary) without breaking any V1 result
  (V1 held-out identical), and turned 11 of the 12 RC misses on ST7757 into located findings (the 12th is a
  measurement convention, not an omission). Reproduction from git works.
- **Did not work / limits:** naming (UNKNOWN when no legend), legend rows close together, route slab errors
  dominating the remaining false findings, no second real project yet, ST7757 V2 is not blind.
- **Recommend:** a second blind real project before any further tuning; V3 legend reader; fix the route's slab
  face builder; keep the completeness pass out of every total.
