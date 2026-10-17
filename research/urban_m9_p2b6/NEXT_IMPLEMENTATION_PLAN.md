# Next implementation plan: an opt-in architectural method (proposal; not started)

**Why a new method, and why now.**

- The corrections below change quantities that V2.6 produces. V1 - V2.6 must stay byte-identical (freeze policy), so
  the corrections can only live in a new opt-in method.
- The program forbids creating one "because the name is next in sequence". So the architecture was proven first, in
  an isolated clone, with every change behind a flag (`EXPERIMENT_RESULTS.md`, patch in `experiments/`).
- Authorisation is requested as owner decision **D-14**.

**Working name.** `ARCH_TAKEOFF_V2.7`. The name follows the method series; the content is defined below and nothing
else.

## 1. Scope (every item proven tonight)

| # | change | modules | proof already obtained | expected effect |
|---|---|---|---|---|
| 1 | **door width from the symbol's jamb span** when every remainder of the wall gap is proven wall on both faces; remainders closed as zero-material wall; thresholds rebuilt; the opening's `position` recomputed; the D-V26-07 remainder no longer asks Q_WALL_BAND when the jamb evidence answers it | `arch_rooms` (after the closures), `arch_completeness` | Exp. A: 7 synthetic variants exact (turned 37°, mirrored, metres included); 1 real candidate; refusals on open / column remainders | real rooms 8 → 1 failing; synthetic threshold +28 % → 0 |
| 2 | **basin-only spaces for review** (owner Part 4): no room type from wash-basin blocks alone; a WC drawn as linework on a sanitary layer (an elongated closed curve with a cistern rectangle) still types a W.C. | `arch_rooms._evidence`; knowledge **1.2.0** (UP-WET-002) | Exp. G: real rooms 1 → 0 failing (with 1) | 3 spaces / 9.35 m2 to review on the reference plan, unless the WC-shape check types them |
| 3 | **single-instance roles by geometry**: a door with its hinge at a wall-gap jamb whose symbols explain ≥ 80 % of the layer; windows of 1 - 3 lines in gaps with no door; the door rule runs before the window rule | `arch_plan.layer_roles` | Exp. C: benchmark 15 / 15 exact; reference plan, villa and mirror unchanged; wardrobe and threshold-line adversaries rejected | D-D1 (doors / windows) and D-P6-02 closed |
| 4 | **column rectangles of any orientation, one polyline or four LINEs** (the existing ≥ 3 count rule kept; single-instance columns NOT inferred: the drain adversary) | `arch_plan` (`_small_rects`) | Exp. C: the turned villa's 3 columns and the four-line column found | D-P6-04 / 08 closed; D-P6-03 stays with the audit |
| 5 | **arc-aware room polygons** (sagitta ≤ 1 mm) and **curved wall bands** (concentric arcs; MID_BAND_ARC in the run, all bases published) | `arch_rooms._faces_of`, `arch_walls` | Exp. B: B10 exact; the reference plan's one band equal to an independent census | layouts on the arc; wall run +0.88 % on the plan |
| 6 | **nested-plan door evidence** scoped to the swing's own occurrence | `door_model` | Exp. F (as found: 5 doors held) | D-P6-05 closed |
| 7 | **zero-length pieces merged** in the room ring | `wp_geometry.segments` (a method-gated copy) | Exp. F (as found) | D-P6-06 closed |
| 8 | **per-line source entities** (the boundary items' DXF ids) | `arch_measure` | Exp. E | provenance to the drawing |

**Out of scope** (later phases, `PRIORITIZED_ROADMAP.md`):

- heights;
- formwork;
- excavation;
- windows' area items;
- roofs and external works;
- single-instance column inference;
- leaf-closed thresholds (they need their own tests first).

## 2. Design notes

1. **Hold state.** Item 1 narrows the opening but keeps the held-door review state (DOOR_SYMBOL_FIT_REVIEW) until a
   person confirms it. The doorway waterproofing stays PROVISIONAL. The quantities are right, and release stays a
   review act.
2. **WC-shape check (item 2).** Before a basin-only space is withheld, its sanitary-layer linework is tested for a WC
   footprint: a closed curve or ellipse about 0.35 - 0.45 x 0.55 - 0.75 m, plus a rectangle at one end. The test must
   pass the synthetic basin plan and a synthetic exploded-WC plan.
3. **Knowledge 1.2.0.** A new file; 1.1.0 is unchanged and stays V2.6's. The new method pins 1.2.0. New records:
   - UP-WET-002 (basin);
   - a `class` field on every record (`ENGINEERING_SKILLS_AUDIT.md` §2).
4. **Curved-run basis.** MID_BAND_ARC by default, subject to D-07. MIN and MAX are published in the line's inputs.
5. **Everything stays stdlib in `engine/`.**

## 3. Acceptance tests (written before the code)

| test | expected |
|---|---|
| V1 - V2.6 outputs on the villa, its mirror and the reference plan (Mode U and A) | byte-identical to tonight's snapshots (968 + 272 files) |
| the five real rooms (Stage C, private) | **0 of 66** failing |
| `tests/m9_p2b6/test_p2b6_found_defects.py` | unchanged for V2.6; each D-P6 case re-asserted with its **truth** for the new method |
| the benchmark with inferred roles | 15 / 15 single-instance cases exact; C06 still refused |
| tonight's adversaries | wardrobe / threshold line stay OTHER; drains stay a REVIEW (audit A04), never a silent column |
| Experiment F transformations | every quantity invariant (turned 30° and nested included) |
| the run audit on the new method's runs | A01, A02, A06 (turned / exploded), A05, A07, A08 (width), A09 and A10 no longer raised on the fixed cases |
| reference plan, no-flag-equivalent cases | every door except the one candidate, every room except the basin-only spaces, every wall except the curved band: unchanged |
| full suite | the 377 private-data failures unchanged; every other test passing; compared by test identity |

## 4. Steps

1. Write the acceptance tests above (they fail on the new method name).
2. Port the clone's experiment code into method-gated functions.
3. Add the WC-shape check, the position recomputation, and the nested-door scoping (the three pieces not prototyped
   tonight). Each gets its own synthetic test first.
4. Add knowledge 1.2.0.
5. Run:
   - byte identity of V1 - V2.6;
   - Stage C, privately;
   - the full suite by identity;
   - the freeze verifier.
6. Document, using this folder's format.

## 5. Risks

| risk | mitigation |
|---|---|
| a door set in a wider opening with a fixed side panel drawn as a wall-layer line could be narrowed wrongly | the remainder must be wall on **both** faces |
| geometry signatures could type a furniture layer DOOR | the hinge-at-jamb requirement; the adversarial fixtures stay in the test set |
| the basin rule could withhold a real W.C. | the WC-shape check; withheld means review, never dry |
| everything is proven on one real plan | D-15: a second real plan before any freeze of the new method |
