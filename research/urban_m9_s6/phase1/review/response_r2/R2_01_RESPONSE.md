# S6 review, round 2: answers to Q1–Q5, revised acceptance tests, recommended Phase 2A scope

Reviewed engine: commit `c757d8a` (the notes commit `47ed00b` changes no code).

**Phase 2A has not been started.** No production code, owner rule, frozen output, `data/` file or repository setting was changed. Every experiment ran on:
- a scratch export of the committed source; or
- a detached scratch worktree, reset to HEAD after each experiment.

The human benchmark was not opened.

## How to read the labels

Each claim carries one label.

| Label | Meaning |
|---|---|
| **[VERIFIED DEFECT]** | Reproduced on committed code, with a command that shows it. |
| **[MEASURED]** | A reproduced measurement that is not a defect (a rate, a count, a difference). |
| **[ENGINEERING INFERENCE]** | My reasoning from the evidence. Not proven; it could be wrong. |
| **[OWNER DECISION]** | Changes a measurement rule, a frozen artefact, or how freezes are enforced. Needs the owner. |
| **[MISSING SOURCE]** | The drawings do not carry the information. No algorithm can supply it. |

Door labels `U1`–`U8` are the 8 unmatched swings on the reference plan. Their mapping to drawing handles is in the PRIVATE archive only.

---

## 0. Summary

### Where I agree with ChatGPT, and where I don't

| ChatGPT decision | My position | Main reason |
|---|---|---|
| 1. A versioned robust predicate, with each threshold reviewed individually | **AGREE**, with two additions | The margin must have both a floor and an error bound (Q1). The angle-bin defect is separate, and no ε fixes it. |
| 2. Preserve V1 and the historical outputs; an append-only errata register | **AGREE**, with a prerequisite | Today a rebuild test can rewrite its own freeze manifest and then pass (F-1). Fix the harness first. |
| 3. Dual evidence for doors; a swing radius is never a BOQ width | **AGREE** | On all 7 measurable unmatched doors, the radius is 11–14 % below the wall-to-wall width. |
| 4. Element-level BOQ records; RFIs grouped by question; an engineering findings register | **AGREE** | Round 1: the 85 RFI lines are 4 questions and 14 engine defects. |
| 5. Element conservation first; a surface ledger later | **PARTLY DISAGREE** | Build the minimal ledger now, read-only. It costs little and finds 130 missing reveal/head records that element conservation cannot see (Q3). |
| 6. Separate exit codes | **AGREE** | Already proposed in round 1. |
| 7. Everything opt-in under V2.1 until the acceptance tests and the blind round pass | **AGREE** | — |

### The five answers

| Question | Answer |
|---|---|
| **Q1** | Yes: margin = max(1e-6 mm, a floating-point error bound), with an explicit UNDECIDABLE state. Either term alone fails a test the hybrid passes. |
| **Q2** | 1 confirmed (under V2.1 only), 6 provisional, 1 unresolved. 29 drawn swings = 22 leaves in 21 confirmed doors + 6 provisional + 1 unresolved. No double counting: the only double-leaf door is one element. |
| **Q3** | A 516-record ledger runs today on the reference plan as a read-only prototype: 133 MEASURED, 54 PROVISIONAL, 179 BLOCKED, 3 EXCLUDED, 147 MISSING. |
| **Q4** | 282 of 389 dimensions are usable. The cross-check matches 10 of 57 openings and 55 wall thicknesses, all with 0.0 mm difference. None of the 8 unmatched doors is dimensioned. Build it now, read-only. |
| **Q5** | Byte-identical rebuilds hold only inside one pinned environment. A comment-only source change alters output bytes through the code stamp. A two-stage migration is proposed: Stage 1 adds verification only; Stage 2 relaxes one file, with owner approval. |

### New verified defects found in this round

All four are listed in `R2_04_CLAIMS_REGISTER.csv`.

**F-1 [VERIFIED DEFECT] The freeze harness heals itself.**
- The S8.6 rebuild test runs the builder inside the frozen package. The builder rewrites the package's outputs and its own freeze manifest.
- After one failing run, a second run passes both `test_frozen_before_comparison` and `test_rebuild_byte_identical` against the rewritten manifest.
- Only a downstream stage that pins an S8.6 file as its input still fails (S9 pins S8.6's summary).

**F-2 [VERIFIED DEFECT] Code stamps are entangled with output bytes.**
- 28 of the 29 output-pinning freezes write a `+code:<digest>` stamp into at least one output: 53 of 379 output files, including 6 CSV registers.
- A comment-only change in one engine file therefore changes 2 of the 15 S8.6 outputs. The 13 quantity files stay byte-identical.
- The change cascades: downstream manifests pin those files, or embed the upstream manifest's sha256.

**F-3 [VERIFIED DEFECT] The angle-bin projection loses gaps on walls off the 0.5° grid.**
- Segments are projected on their 0.5° bin axis, not on their own axis.
- A drafted 500 mm opening in a wall at an arbitrary angle is found 0 times in 400 placements, even when any width within 50 mm counts as found.
- No ε can fix this. The cause is that face pieces of one wall split into several face lines.
- A length-weighted mean axis per bin restores 400 of 400, with errors ≤ 1e-6 mm.
- Effect on the reference plan: none. A mean-axis run gives identical rooms and openings.

**F-4 [VERIFIED DEFECT] No environment is pinned.**
- `requirements.txt` has lower bounds only.
- The two interpreters on this machine carry different package sets: 3.13 lacks `pymupdf`, `scipy` and `matplotlib`, and has a different numpy and pypdf.
- Under 3.13, 16 test modules cannot be collected.

### Corrections to my round-1 notes

1. **Round 1 said "canonical formatting does not fix" the 3.11 / 3.13 difference. That was too strong.**
   - Rounding floats to 9 decimals, and writing −0.0 as 0.0, makes every JSON and CSV output of the synthetic villa equal across the two interpreters.
   - It is still not a guarantee. A value that differs by d lands on opposite sides of a rounding boundary with probability ≈ d / 10⁻⁹, so ≈ 1 % of runs on this villa would still differ (Q5, E3).
   - The conclusion stands, in a weaker form: canonical hashes are not a reliable portable freeze.
2. **"388 DIMENSIONs" is the entity count of type DIMENSION.** With the one ARC_DIMENSION there are 389 (Q4).

---

## Q1. Robust predicate: a fixed ε, a float-error bound, or both?

**Question.** Test at T−ε, T and T+ε, across units, rotations and offsets. Is a fixed absolute ε plus a float-error bound more defensible?

### Evidence

**The decision procedure test.** Script: `q1_predicate_boundary.py`, stdlib only.
- A segment drafted at T + δ (T = 100 mm) is placed through 1 or 3 nested inserts.
- The last insert moves it to a site offset of 0, 100 m, 1 km, 10 km, or 3.3e9 mm (a national-grid northing in mm).
- Units: mm, cm, m and inch. Rotations: 0°, 90°, 30°, 45° and random. 400 placements per case.
- The table gives the fraction kept, pooled over units, rotations and depths. **[MEASURED]**

| δ (mm) | FROZEN `not L < T`, origin | FROZEN, 3.3e9 mm | FIXED ε = 1e-6, origin | FIXED ε, 3.3e9 mm | FP bound only, origin | FP bound only, 1 km | HYBRID, origin | HYBRID, 3.3e9 mm |
|---|---|---|---|---|---|---|---|---|
| −1e-4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| −1e-5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1.000 |
| −1.5e-6 | 0 | 0 | 0 | 0.004 | 0 | 0 | 0 | 1.000 |
| −1e-6 (= −ε) | 0 | 0 | 0.622 | 0.540 | 0 | 0 | 0.622 | 1.000 |
| −5e-7 | 0 | 0.027 | 1.000 | 0.998 | 0 | 0 | 1.000 | 1.000 |
| −1e-9 | 0 | 0.714 | 1.000 | 1.000 | **0** | **1.000** | 1.000 | 1.000 |
| **0 (drafted exactly)** | **0.697** | **0.717** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| +1e-9 | 1.000 | 0.718 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

**Largest placement noise** |L − L_drafted| **[MEASURED]**

| Site offset | Largest noise |
|---|---|
| origin | 2.9e-12 to 3.6e-12 mm |
| 100 m | 2.5e-11 mm |
| 1 km | 2.0e-10 mm |
| 10 km | 2.0e-9 mm |
| 3.3e9 mm | 4.4e-7 to 6.9e-7 mm |

**The engine's own three sites.** Script: `q1_threshold_sites.py`, run through the frozen `face_lines`, `wall_bands` and `band_gaps`. **[MEASURED]**
- The sites are the 100 mm face piece, the 300 mm band overlap and the 500 mm opening gap.
- At 0°, 90°, 30° and 45°, the frozen comparison keeps between 0 % and 100 % of drafted-exact values, depending on unit and offset. Examples:
  - 33 % of 100 mm pieces in metres at the origin;
  - 15 % of 300 mm overlaps in metres at 45°;
  - 28 % of 500 mm gaps in metres at 30°.
- The robust margin keeps 100 % in every one of these cases.
- At random angles both fail: this is the separate defect F-3, below.

**The reference plan** (private run; aggregate values only). **[MEASURED]**

| Threshold | Values within 1e-8 mm of T (noise cluster) | Closest genuine values below / above T |
|---|---|---|
| 100 mm face piece | 5 (mm run), 8 (m run), all within 5.4e-10 mm | −0.190 / +0.028 mm |
| 300 mm band overlap | 2, within 2.9e-9 mm | −7.73 / +3.51 mm |
| 500 mm opening gap | 1, within 1.05e-9 mm | none within ±25 mm |

### Answer

**Yes. Use the hybrid margin.**

```
keep  ⇔  L ≥ T − m,   m = max(ε_abs, ε_fp)
ε_abs = 1e-6 mm, expressed in drawing units
ε_fp  = 16 · u · M · (d + 1)
        u = 2⁻⁵³
        M = the largest |coordinate| of the inputs
        d = the insert nesting depth
if ε_fp > 1e-3 mm:  UNDECIDABLE  →  a REVIEW finding, never a silent keep or drop
if |L − T| ≤ m:     the decision is kept, and an AT_THRESHOLD record is written (site, value, T, m)
```

**Why not the fixed ε alone [MEASURED + ENGINEERING INFERENCE].**
- It is correct at every offset tested.
- But its safety factor shrinks as coordinates grow. At 3.3e9 mm the noise (≤ 6.9e-7 mm) is already within 1.5× of ε.
- Noise grows linearly with M, so somewhere near 10× that magnitude drafted-exact values would start being dropped again, silently.

**Why not the error bound alone [MEASURED].**
- It has no floor, so near the origin it decides at 1e-12 mm resolution.
- At δ = −1e-9 mm the same piece is dropped at the origin and kept at 1 km.
- That breaks translation invariance, which the metamorphic suite requires.

**Why the hybrid [ENGINEERING INFERENCE].**
- It is translation-invariant for every δ outside the boundary band, as long as ε_fp ≤ ε_abs. That holds for M up to about 2.8e8 mm at depth 1 in a mm drawing, which covers every site-local drawing.
- Beyond that, the band widens to ε_fp because the precision really is lost. At 3.3e9 mm that is 1.2e-5 mm.
- The widening is reported. Past a 1e-3 mm bound the decision becomes UNDECIDABLE instead of being guessed.

**Why ε_abs = 1e-6 mm [MEASURED].**
- On the reference plan, noise is ≤ 2.9e-9 mm and the nearest genuine value is 0.028 mm from a threshold.
- Any ε between 1e-8 and 1e-3 mm gives identical decisions on this plan.
- 1e-6 mm is about 300× above the worst measured noise and about 28,000× below the closest genuine value.

**At δ = −ε every rule is a coin flip.** That is the boundary itself, not a defect. The acceptance tests therefore assert nothing for δ in (−2ε, 0).

**What it fixes [MEASURED].**
- The float-noise cluster at the three sites. On the reference plan exactly the cluster values above change decision.
- Downstream on V2: +1 door (U1), +1 window, rooms unchanged.

**What it does not fix.**
- **F-3, the angle-bin projection [VERIFIED DEFECT].** Fixed by a length-weighted doubled-angle mean axis per bin, keeping the bin's half-plane so no direction flips. Evidence from `q1_angle_axis.py` / `q1_gap_anywidth.py`, random angles, 400 per case:

  | Case | Frozen bin axis, + robust margin | Mean axis, + robust margin |
  |---|---|---|
  | 100 mm piece | found 3–6 % | 100 % |
  | 300 mm overlap | 48–53 %, width error up to 0.87 mm | 100 %, error ≤ 9.5e-7 mm |
  | 500 mm gap | **0 %, even at any width within 50 mm** | 100 % |

  - Round 1 found 103 of 768 wall / column segments off the 0.5° grid on the reference plan. Their angles include a series stepping by 5.19° (46.26°, 51.45°, 56.65°) and the slopes 1:2 and 1:2.5 (63.43°, 68.20°). This is consistent with polygonised arcs and a few raked walls **[ENGINEERING INFERENCE]**.
  - The mean-axis run changes no room and no opening there **[MEASURED]**.
- **The threshold value itself.** The 6 provisional doors (Q2) sit on 39–89 mm wall nibs, below the 100 mm minimum. That is the *value* of the threshold, not float noise. It is an individual-review item, outside Phase 2A (Q2).

**Individual review of each threshold** (agreeing with "do not globally rewrite"):

| Site | Value | Robust margin in Phase 2A? | Note |
|---|---|---|---|
| `opening_census.face_lines` min piece | 100 mm | **yes** | demonstrated defect (U1) |
| `opening_census.wall_bands` min overlap | 300 mm | **yes** | latent: 2 noise values on the reference plan, no quantity effect today |
| `band_gaps` min gap | 500 / 400 mm | **yes** | latent: 1 noise value; layer-role evidence only |
| face-line `off_tol` / `join_tol` | 2 / 5 mm | no | tolerances, not thresholds on a drafted value |
| every other `<` on the V2 path | — | no | listed in the threshold census first (P2-01). Each gets a margin only after its own review. |

---

## Q2. The 8 unmatched swings, one by one

**Evidence per door.** Script: `q2_door_probe.py` + PNG crops, all PRIVATE. For each door:
- the swing radius and the leaf line;
- the leaf-ray closure, wall to wall;
- the door block's frame span along the closure;
- the wall face pieces beyond each jamb, on both faces;
- the state under V2 and under the robust predicate.

| Door | Floor | Leaf (swing radius) | Closure, wall to wall | Frame span | Wall piece beside the free jamb | V2 state | V2.1 state (robust) | **Outcome** |
|---|---|---|---|---|---|---|---|---|
| U1 | GF | 890 mm | 1000 mm (hits a 100.0 mm face piece and a wall cap) | 1000 mm | 100 mm on one face, kept only with the margin | CLOSED, no line | MATCHED to a 1.0 m band opening, masonry jambs | **CONFIRMED (V2.1 only)** |
| U2 | GF | 690 mm | 800 mm | 800 mm | 73.6 mm nib, on both faces | CLOSED, no line | CLOSED, no line | **PROVISIONAL**, width 800 mm (closure = frame) |
| U3 | GF | 690 mm (exploded, no block) | 800 mm | 800 mm | 39.2 mm nib, on both faces | CLOSED, no line | CLOSED, no line | **PROVISIONAL**, width 800 mm (closure = frame) |
| U4 | GF | 690 mm | **797 mm** | 800 mm | 53.0 mm nib, on both faces | CLOSED, no line | CLOSED, no line | **PROVISIONAL + REVIEW**: closure and frame differ by 3 mm |
| U5 | 1F | 690 mm | 800 mm | 800 mm | 79.8 mm nib, on both faces | CLOSED, no line | CLOSED, no line | **PROVISIONAL**, width 800 mm |
| U6 | 1F | 890 mm | 1000 mm | 1000 mm | 88.5 mm nib, on both faces | CLOSED, no line | CLOSED, no line | **PROVISIONAL**, width 1000 mm |
| U7 | 1F | 690 mm | 800 mm | 800 mm | 73.3 mm nib, on both faces (one perpendicular jamb) | CLOSED, no line | CLOSED, no line | **PROVISIONAL**, width 800 mm |
| U8 | GF | 890 mm | — | — | host wall drawn on layers that are not wall-role | CLOSURE_UNRESOLVED | CLOSURE_UNRESOLVED | **UNRESOLVED** |

**What the evidence shows.**
- **[MEASURED]** None of the CLOSED doors has closure B (both faces found). Every closure hit is a collinear face line or a wall cap, so the closure evidence is one-sided.
- **[VERIFIED DEFECT] U2–U7 have no door line** although symbol, leaf, frame and closure all agree.
  - The root cause is not float noise. A real wall return of 39–89 mm sits between the door frame and a cross wall, on **both** faces.
  - It is below the 100 mm face-piece minimum, so the band stops at the frame and no gap exists.
  - This is the threshold *value*. A test for exactly this shape already exists: `test_pa07r2_guards::test_fm_r1_06b_wall_nib_between_cross_wall_and_jamb…`.
- **[VERIFIED DEFECT] U8:** the host wall is on layers the role classifier did not admit as walls. The layer-role decision blocks it, not the door logic.
- **[MEASURED] Swing radius vs wall-to-wall width:** 690 vs 800 mm (−13.8 %) and 890 vs 1000 mm (−11.0 %), on every one of the 7 measurable doors. This supports decision 3: never use the radius as a BOQ width.

### Double-leaf doors: no double counting

- **[MEASURED]** The plan has one double-leaf door: a GF 2.0 m opening.
  - Its single door insert carries two arcs.
  - `match_swings` matches it as one opening with 2 leaves.
  - No pair exists among the 8 unmatched swings.
- **Proposed rule [ENGINEERING INFERENCE]:**
  - A door *element* is keyed by its band opening if matched, otherwise by its insert occurrence.
  - Leaves are attributes of the element, never elements themselves.
  - Two exploded leaves (no insert) form one element only when both conditions hold:
    - their hinges sit at the two ends of one closure line;
    - r₁ + r₂ matches the closure width within 2 %.
  - Otherwise each leaf is its own PROVISIONAL element with a REVIEW finding.
- **Conservation, checked [MEASURED]:** 29 drawn swings = 22 leaves in 21 confirmed doors (one of them double-leaf) + 6 provisional + 1 unresolved. Each swing belongs to exactly one element.

### A provisional door must not silently become confirmed

The state is a typed field with allowed transitions only. **[ENGINEERING INFERENCE: design]**

```
PROVISIONAL ─▶ CONFIRMED   only with an evidence record naming ONE of:
                            (a) a band opening with masonry or column jambs on both faces (geometry)
                            (b) a usable DIMENSION across both jambs, |diff| ≤ 5 mm, agreeing with the closure (Q4)
                            (c) a door schedule entry                                         [MISSING SOURCE today]
                            (d) a named, dated reviewer or owner decision record              [OWNER DECISION]
UNRESOLVED  ─▶ PROVISIONAL  only with a wall-to-wall closure AND a frame span; if they differ by more than 2 mm,
                            the element is PROVISIONAL + REVIEW and its width range spans both values (U4)
```

- Every transition writes a record.
- Released BOQ door lines come only from CONFIRMED.
- PROVISIONAL doors go to a separate provisional section:
  - the width is the closure width;
  - the uncertainty is recorded as [swing radius, closure width];
  - they never enter a released total.
- The test enumerates every code path that can set CONFIRMED and asserts each one carries an evidence id.

### Where I disagree

- **U1 is confirmed only under V2.1.** Under V2 it stays PROVISIONAL, so the outcome depends on the method version, and the ledger must record which one.
- **A "nib rule" would turn U2–U7 into confirmed doors. I do not recommend it for Phase 2A.**
  - It would let pieces below 100 mm act as jamb evidence.
  - That changes the masonry face model and can create false openings.
  - It needs its own fixtures, a before/after on the synthetic suite, and the owner's approval.
  - Until then, PROVISIONAL with a bounded width is the honest state.

**Missing source.** Door heights, leaf type and frame position are not on the plan **[MISSING SOURCE]**. A door schedule would settle widths and heights for all 8.

---

## Q3. A minimal eligible-surface ledger, next to P2-04

**Prototype.** `q3_surface_ledger.py`, a read-only post-processor over the existing V2 outputs.
- **Schema:** one record per (element, surface, trade), with these fields: `element`, `element_kind`, `floor`, `surface`, `trade`, `status`, `blocker`, `line_ids`, `quantity`, `unit`, `note`.
- **Status** is one of:

| Status | Meaning |
|---|---|
| MEASURED | a released line exists |
| PROVISIONAL | a provisional line exists |
| BLOCKED | an RFI or unresolved record exists; the blocker class is recorded |
| EXCLUDED | excluded, with a reason |
| MISSING | eligible, but there is no record anywhere: an engine gap |
| NOT_APPLICABLE | the eligibility table says the surface does not apply |

- NOT_APPLICABLE pairs are implicit in the versioned eligibility table and are not written out, to keep the ledger small.
- The eligibility table `ELIGIBILITY_V0` is in `R2_06_ELIGIBILITY_V0.md`. **It is my engineering proposal and needs owner approval [OWNER DECISION].**

**Results [MEASURED]**

| | Synthetic villa | Reference plan |
|---|---|---|
| records | 114 | 516 |
| MEASURED | 31 | 133 |
| PROVISIONAL | 12 | 54 |
| BLOCKED | 39 | 179 |
| EXCLUDED | 0 | 3 (shafts) |
| MISSING | 32 | 147 |

**BLOCKED on the reference plan, by blocker class**

| Blocker | Records | Class |
|---|---|---|
| sections / heights | 78 | **[MISSING SOURCE]** |
| owner decision | 36 | **[OWNER DECISION]** |
| owner decision + heights | 16 | both |
| window schedule / elevations | 25 | **[MISSING SOURCE]** |
| space kind not established (label missing or unread) | 12 | engine / source, record by record |
| wall specification / legend | 7 | **[MISSING SOURCE]** |
| engine | 5 | **[VERIFIED DEFECT]**, in the engineering findings register |

**MISSING on the reference plan [VERIFIED DEFECT unless stated]**
- **130 reveal and head-soffit records.** That is 2 per opening for 20 doors, 25 windows, 12 passages, 7 provisional doors (U1–U7; U1 is provisional under V2) and 1 unresolved door. **No emitter exists for these at all.**
- **8 door items:** the 7 provisional doors and the 1 unresolved one.
- **5 thresholds:**
  - 2 passages with no adjacent room and no strip;
  - the unresolved door;
  - U1, which has no strip under V2;
  - U7, whose strip was attributed to a neighbouring opening.
- **4 kitchen wet trades.** The kitchen is kind SERVICE and is measured as dry, while the method register lists SERVICE rooms for full-height wall tile. **[OWNER DECISION]**: is a kitchen WET-eligible?

**What can be built now, and what needs sections or owner rules**

| Surface / trade | Buildable now from the plan | Needs |
|---|---|---|
| dry floor finish, ceiling area (plan area) | **yes** | — |
| skirting (perimeter minus openings) | **yes** | wet rooms: rule UP-CER-004 **[OWNER DECISION]** |
| wet floor tile, floor waterproofing | yes, once the space kind is established | kitchen eligibility **[OWNER DECISION]** |
| waterproofing upturn | length yes; area no | upturn height **[OWNER DECISION]** |
| wall plaster / paint / tile areas | lengths yes; areas no | ceiling heights from sections **[MISSING SOURCE]**; tile height **[OWNER DECISION]** |
| opening items (doors, windows, passages) | confirmed ones yes | provisional: Q2 rule; window sizes need the schedule or elevations **[MISSING SOURCE]** |
| thresholds | passages with an adjacent strip: yes | Q-S6-1 **[OWNER DECISION]** |
| reveals and head soffits | **no emitter today** | heights **[MISSING SOURCE]**; frame position in the wall **[MISSING SOURCE]**; whether reveals are measured to full wall depth **[OWNER DECISION]** |
| stair treads, risers, landings | plan parts yes | riser count and height from the section **[MISSING SOURCE]** |
| exterior scope | no | Q1 **[OWNER DECISION]** |

**Recommendation.** Phase 2A includes the ledger as a read-only post-processor: no quantity changes and no completeness claim.
- It is the instrument that shows what P2-04 leaves open.
- Element conservation would not have found the 130 missing reveal/head records: every opening *has* a record, but not every eligible surface of it does.
- **A conservation cross-check caught a gap in my own prototype.** Its door records did not add up to the Q2 identity: the first version skipped U1 on the V2 outputs, because U1 is confirmed only under V2.1. Under V2, U1 has no line, so 4 of its records silently vanished. That is the class of error the ledger exists to expose. Fixed: under V2, U1 is now a PROVISIONAL element noted "CONFIRMED under V2.1". The counts above are after the fix (512 → 516 records).
- This is where I part from decision 5. "Later" means the next fixes are chosen without the instrument that ranks them.

---

## Q4. The DIMENSION entities

**Census.** `q4_dimension_census.py`, reference plan, PRIVATE detail. **[MEASURED]**

**Entities**
- 389 in total: 366 LINEAR, 20 ALIGNED, 2 RADIUS (388 of type DIMENSION) and 1 ARC_DIMENSION.

**Location**
- GF plan 118, 1F plan 121, 2F plan 48.
- Other sheets (elevations / sections) 100; outside every frame 2.

**Attributes**
- 0 text overrides.
- **All non-associative:** `$DIMASSOC` = 1, and there are no DIMASSOC objects.
- **DIMLFAC = 0.1 on 388**, so the displayed values are centimetres, while the geometry is mm. The header and the dimension style agree.

**Duplicates and stored values**
- 6 duplicates (3 pairs).
- After applying DIMLFAC, the stored measurement equals the defpoint distance on all 386 linear and aligned dimensions.

**Usable: 282.**

| Excluded because | Count |
|---|---|
| not on a floor plan | 102 |
| duplicate | 6 |
| not linear | 3 |
| text override | 0 |
| stored value disagrees with its defpoints | 0 |

**Note on "exclude non-associative".** It would exclude all 389. A non-associative dimension is not stale relative to its own defpoints (checked above). It can be stale relative to the geometry, and that is exactly what the cross-check detects.

**Cross-check [MEASURED]**

| Check | Result |
|---|---|
| opening width: a usable dimension parallel to the wall, both extension origins on the two jambs (±15 mm), within 400 mm of the wall | **10 of 57 openings, all 0.0 mm difference** (11 with any offset; 21 with at least one jamb on a dimension chain) |
| wall thickness: a dimension across a band, both origins on the two faces (±5 mm) | **55 matches, all 0.0 mm difference** |
| an injected 10 mm error | flagged |
| the 8 unmatched doors | **none is dimensioned**, so dimensions cannot settle Q2 on this plan |

**Can a small read-only cross-check be built before the blind round? Yes.** It needs about 150 lines, writes `DIMENSION_CROSSCHECK.json` plus a REVIEW finding for |diff| > 5 mm, and changes no quantity.

**Limits [ENGINEERING INFERENCE].**
- **The errors are common-mode.** The drafter snapped the dimensions to the same lines the engine reads, so a match confirms the geometry, not the design intent.
- **Coverage is low:** 18 % of openings.
- **Where its value lies:**
  - unit, scale and DIMLFAC sanity: the first version of my own census read every value 10× wrong until DIMLFAC was applied;
  - stale dimensions;
  - gross misreads;
  - one of the four evidence kinds for PROVISIONAL → CONFIRMED (Q2).
- **Reuse, don't add a parallel reader.** `engine/cad_adapter.py` already models a dimension's three values (geometry, display, display ÷ DIMLFAC), with fixtures (`DIMENSION_WITH_DIMLFAC`).
  - It takes DIMLFAC from the header only. On this plan the header equals the style (0.1), so it would read correctly.
  - A drawing whose dimension styles differ from the header would be misread **[ENGINEERING INFERENCE, not demonstrated]**. The cross-check should resolve DIMLFAC per entity and style.

**Where I disagree.** The question implies that dimensions might resolve the door widths. On this plan they do not: the doors that need them carry none. Their role is a sanity check and one evidence kind, not a width source.

---

## Q5. Byte-identical history under a pinned environment, and a two-stage migration

**Question.** Demonstrate byte-identical historical outputs under a pinned Python and dependency set before any source-byte lock is relaxed. Propose a two-stage migration that avoids both parallel-code drift and accidental historical change.

**Where it was run.** In a detached scratch worktree at `c757d8a`, with the gitignored inputs linked in. `research/` was reset to HEAD after every experiment, and both trees were confirmed clean afterwards.

### E1. Inside one environment, every historical rebuild is byte-identical [MEASURED]

- **Environment:** Python 3.11.17 with ezdxf 1.4.4, numpy 2.4.6, shapely 2.2.0, openpyxl 3.1.5, scipy 1.17.1, pymupdf 1.28.2, pypdf 6.19.0, pillow 12.3.0, matplotlib 3.11.2, Jinja2 3.1.6, python-barcode 0.16.1 and pytest 9.1.1. The full list is in `evidence/pip_freeze_py311.txt`.
- **Selection:** every test whose name contains `rebuild`, `rerun` or `byte_identical`.
- **Result:**
  - **71 passed byte-identical, 0 failed.**
  - 4 skipped because their inputs are not in the repository (a freelancer workbook, two private datasets, one regression run).
  - The worktree was unchanged afterwards.
- This is the evidence ChatGPT asked for: **inside this environment, the history reproduces bit for bit.**

### E2. Across interpreters it does not [MEASURED]

Same selection under Python 3.13.16, which has no pymupdf, scipy or matplotlib, numpy 2.5.3 and pypdf 6.17.0. Per-test results are in `R2_05_REBUILD_MATRIX.csv`.

**Whole suite in one session**
- 31 passed, 39 failed, 3 skipped.
- 16 test modules could not be collected at all (pymupdf 9, scipy 7).

**The 39 failures re-run one at a time from a pristine tree**

| Result | Count | Detail |
|---|---|---|
| pass | **23** | Their whole-suite failure was a cascade: earlier rebuilds had rewritten upstream frozen files in place (F-1), and the builders' own `verify_frozen` then refused them |
| bytes differ | **10** | S4, S4.1, S5, S5.1, S6, S6.1, D1.1, D1.2, S8.3, S8.7C, all in the last one or two binary digits of a float. In the files examined: absolute difference ≤ 5e-12, relative ≤ 5e-16. The S6 bar-run register and the S8.3 / S8.7C conservation checks are among them, so quantity files differ too, not only summaries |
| missing module | **6** | ENV_MISSING_MODULE |

- **The S8.6 lintel package is byte-identical under both interpreters.**

### E3. Synthetic villa, V1 and V2, 3.11 vs 3.13 [MEASURED]

- 7 of 15 output files differ in bytes.
- 49 of 3,067 float values differ, by at most 9.1e-13.
- The workbook differs in 1 of 11,312 cells: a 14 m² space reads `14` under 3.11 and `13.99999999999998` under 3.13.
- Rounding to 9 decimals (and writing −0.0 as 0.0) makes every JSON and CSV equal.
- Expected rounding flips per run at the observed differences:
  - ≈ 0.011 at 9 decimals;
  - ≈ 1e-5 at 6 decimals;
  - ≈ 11 at 12 decimals.
- A canonical hash is therefore probabilistic, not a guarantee.
- The integer steps downstream already guard against this kind of noise: the tile layout uses ε = 1e-6 m, the link and stirrup counts use `ceil(x − 1e-9)`, and column rebar uses `Fraction`.
- **One unguarded `ceil` exists in the frozen M4 lap count** (`continuous_beams._with_laps`) **[VERIFIED DEFECT, latent]**. The M4 freeze rule says record it, don't change it: it goes to the errata register.

### E4. Code stamps entangle source bytes with output bytes: F-2 [VERIFIED DEFECT]

**The experiment.** One comment line appended to `engine/source/opening_census.py`, then the S8.6 rebuild under 3.11:
- 2 of 15 outputs differ: `00_README.md` and `14_S8_6_SUMMARY.json`. Only the `engine_commit` stamp changes, in one line each.
- The 13 quantity files are byte-identical.

**Census of the 29 output-pinning manifests**
- 28 write a `+code:` stamp into at least one output.
- That is 53 of 379 output files, including 6 CSV delta / ownership registers.

**Consequence.** Every source edit necessarily changes output bytes, whatever its behaviour. So "byte-identical after a change" is impossible for 28 of 29 freezes, unless provenance fields are masked.

### E5. A rebuild test can rewrite its own manifest and pass: F-1 [VERIFIED DEFECT]

**The experiment.** With the comment change in place, the S8.6 tests were run twice.

| Run | Result | What happened |
|---|---|---|
| 1 | 3 tests fail | the builder ran inside the package and rewrote `00_README.md`, `14_S8_6_SUMMARY.json` and `15_S8_6_FREEZE_MANIFEST.json` |
| 2 | `test_frozen_before_comparison` and `test_rebuild_byte_identical` **pass** against the rewritten manifest | only `test_every_earlier_stage_still_verifies` still fails, because S9 pins S8.6's committed summary as an input |

- Without that downstream pin, the source change would have gone unnoticed.
- `git commit -a` would have committed the rewritten "frozen" files.

### E6. Blast radius of one comment line [MEASURED]

- **Source pins** (`evidence/Q5_STAMP_AND_PIN_CENSUS.json`):
  - 32 manifests pin 111 source files.
  - 12 pins differ from today's bytes, all of them in the M6–M8 engine freezes:
    - these pin files as they were at their own commits;
    - the M7 and M8 tests allow exactly the recorded post-freeze fixes, and M8 asserts the changed set *equals* its list;
    - the M6 test checks the bytes at its commit only.
  - **Pinned among the files Phase 2A might touch:**
    - `opening_census.py`, by the S8.6 code map;
    - `topology.py` and `tools/urban_intake.py`, by the M7 and M8 engine freezes, through the exact changed-set test.
  - Not pinned: `arch_plan`, `arch_rooms`, `opening_gaps`, `lintel_measure`, `arch_intake`, `arch_discovery` and `urban_boq_m9`.
  - **Phase 2A as scoped needs to edit only `opening_census.py`:**
    - P2-04 is a V2.1 branch in `arch_rooms` that calls `topology` unchanged;
    - P2-05 reads fills through `arch_discovery`, not `urban_intake`.
  - If either of the other two must change, the same Stage 2 procedure applies, and the M7 / M8 changed-set tests are the historical tests involved.
- **Tests that call `verify_frozen`:** 36 test files.
  - Run with the rebuild tests deselected, so nothing is rewritten.
  - Before the change: 468 passed.
  - After a comment-only change to `opening_census.py`: **11 tests fail in 9 frozen packages** (S8.6, S8.6A, S8.7, S8.7A, S8.7B, S8.7C, S8.8, S9, M1).

### Answer

**1. Can byte-identical history be demonstrated under a pinned environment? Yes, inside one environment.**
- E1: 71 / 71 under Python 3.11.17 and the package set above.
- Not across interpreters (E2, E3). The pin must therefore be explicit (F-4).
- **[OWNER DECISION D5]:** this environment becomes the reference environment.

**2. That evidence is necessary but not sufficient, and this is where I add to ChatGPT's premise.**
- A byte-identity claim is credible only if both of these hold:
  - the test cannot rewrite what it compares against (F-1);
  - provenance stamps are separated from behaviour (F-2).
- Both must be in place before any source lock is relaxed.

**3. The two-stage migration.**

**Stage 1: verification only. No engine change, and no historical file changes: it adds files only.** (P2-00)

| Step | What it adds |
|---|---|
| 1a | `ENVIRONMENT_LOCK.json`: the interpreter and the exact package versions of E1. The verifier records the environment. Outside the lock it reports `VALUES_EQUAL_WITHIN_1E-9`, `BYTES_DIFFER` or `ENV_MISSING_MODULE`, **never PASS**. |
| 1b | **An out-of-tree verifier.** It runs `git archive HEAD` into a temporary directory, links the gitignored inputs, and runs each builder there. It compares the committed manifest's raw hashes, and a **behaviour hash**: the same files with declared provenance fields masked (`+code:` stamps, `code` maps, embedded upstream `manifest_sha256`). It never writes under `research/`. |
| 1c | **A session guard test.** It fails if any tracked file under `research/` changed during the test session. This catches F-1 in the existing in-place tests without editing them. |
| 1d | **Append-only registers:** `ERRATA.jsonl` (per release: defect, evidence, effect on frozen outputs, corrected-in version) and `ENGINEERING_FINDINGS.jsonl`. |

- **Stage 1 gate:**
  - the verifier reproduces every freeze in the lock environment (raw and behaviour hashes);
  - a comment-only mutation of each Phase-2A-touched pinned file (today, one file) changes raw hashes only in stamped files, and changes no behaviour hash.
- **Rollback:** delete the added files.

**Stage 2: relax one pinned file, with owner approval. One file at a time, never globally.** (P2-00 Stage 2)

| Step | What it does |
|---|---|
| 2a | The only candidate in Phase 2A is `opening_census.py`. `topology.py` and `urban_intake.py` are also pinned (by the M7 / M8 engine freezes), but the scope avoids editing them. The diff may add only **default-preserving keyword parameters** (a predicate policy and an axis policy) and the branches they guard. An AST-diff check enforces it. |
| 2b | **Proof:** in the lock environment, the behaviour hashes of S8.6 and of every freeze downstream of it are unchanged (S8.6A, S8.7, S8.7A/B/C, S8.8, S9, S9A, M1). So are the V1 / V2 synthetic hashes and the reference-plan V1 hashes. |
| 2c | **The S8.6 source pin for that file becomes provenance**, through an errata entry: old sha, new sha, reason, proof, approver. The committed S8.6 files are never rebuilt in place. The 11 tests of E6 move from source digests to behaviour hashes, through the verifier, for that one file. **This changes historical tests: [OWNER DECISION D2].** |
| 2d | **No parallel copy is created.** The existing duplicate (`opening_gaps.band_gaps`) is retired later, only after its behaviour hashes are proven equal. |

- **Rollback:** revert the keyword parameters. The default path was never changed.

**If the owner declines Stage 2, the fallback** is the round-1 design:
- a V2.1 band path in an unpinned module (`band_census_v2.py`);
- plus a delegation property test proving that, under the frozen policy, it equals `opening_census` on random, synthetic and reference inputs.
- This accepts the duplication explicitly: about 120 lines that must be kept equal.
- I recommend Stage 2, because the drift risk ChatGPT names is real and the proof cost is small once Stage 1 exists.

---

## Revised acceptance tests

All 35 are in `R2_02_ACCEPTANCE_TESTS.csv`, each with its inputs and its status on `c757d8a`. The ones that **fail today**, and must pass in Phase 2A:

| Id | What must pass |
|---|---|
| AT-Q1-01 | drafted-exact values kept at all three sites, every unit, rotation, offset and depth |
| AT-Q1-04 | gaps found at arbitrary angles |
| AT-Q1-05 | metamorphic invariance |
| AT-Q2-01 | door conservation: 8 of 29 swings without an element today |
| AT-Q5-04 | the session guard (F-1) |

The ones that **must keep passing:**
- AT-Q1-07: V1 / V2 unchanged;
- AT-Q5-02: 71 / 71 rebuilds in the lock environment;
- AT-G-02: release language: gate INCOMPLETE, no prices, no quotation-ready or accuracy claim.

## Recommended Phase 2A scope

See `R2_03_PHASE2A_SCOPE.md`. In short, in this order:

| Order | Package | What |
|---|---|---|
| 1 | **P2-00** | Stage 1, plus Stage 2 for one file if the owner approves |
| 2 | **P2-01** | hybrid robust predicate at three reviewed sites |
| 3 | **P2-01b** | mean-axis face lines |
| 4 | **P2-02** | metamorphic suite |
| 5 | **P2-03** | stable ids |
| 6 | **P2-04** | door / window conservation with evidence-typed states and closure widths |
| 7 | **P2-05** | fills from K2 |
| 8 | **P2-06** | RFI register + engineering findings |
| 9 | **P2-08a** | read-only surface ledger |
| 10 | **P2-09a** | read-only dimension cross-check |

- **Effort:** about 14–19 engineer-days.
- **Deferred:**
  - the nib rule (P2-13);
  - the reveal emitter (needs source and owner);
  - the kitchen eligibility (owner);
  - a global threshold rewrite;
  - route-G / M4 corrections.

## What worked, what did not, what I recommend next

**What worked**
- **The hybrid margin:** 0 false drops in 100 % of placements over 4 units, 5 offsets up to 3.3e9 mm, 5 rotation sets and 2 depths.
- **The mean-axis projection:** 100 % at arbitrary angles.
- **The per-door evidence:** all 8 unmatched swings explained, with the conservation identity holding.
- **The ledger prototype:** 516 records. A conservation cross-check caught a gap in its first version, now fixed.
- **The dimension census:** 282 usable, 65 checks, all 0.0 mm difference.
- **The pinned-environment rebuild:** 71 / 71 byte-identical.

**What did not work**
- The frozen strict comparison: 70 % of drafted-exact values kept.
- The frozen bin-axis projection at arbitrary angles: 0 % of gaps.
- Dimensions as a source for the doors that need them: none is dimensioned.
- Canonical hashing as a portable freeze: probabilistic.
- Rebuilding under 3.13: 10 freezes differ in the last digit, and 6 lack modules.
- The current rebuild harness: it can heal its own manifest.

**What I recommend next**
1. **The owner decides D1–D5** (`R2_03_PHASE2A_SCOPE.md`).
2. **Implement P2-00 Stage 1 first**, on its own, and re-run this round's experiments through it. The gate: the verifier reproduces every freeze, and the mutation experiment shows behaviour hashes unchanged.
3. **Then P2-01 / 01b / 02 together**, with the reference-plan before/after register reviewed by a person.
4. **Then P2-04 and P2-06**, then the read-only P2-08a / P2-09a.
5. **Then the blind round on two unseen villas.** No accuracy percentage, no quotation-ready claim, and the gate stays INCOMPLETE until that evidence exists.

## Owner decisions requested

| Id | Decision |
|---|---|
| D1 | approve Stage 1 (adds files only) |
| D2 | Stage 2 for `opening_census.py`, or the parallel-module fallback |
| D3 | `ELIGIBILITY_V0` as a diagnostic table (marked PROPOSAL); and, separately, the entries marked *(owner)* in it: kitchen / SERVICE wet eligibility, upturn and wall-tile heights, reveals measured or not, thresholds Q-S6-1, exterior scope Q1, paint above tile Q7, skirting in wet rooms UP-CER-004 |
| D4 | provisional door lines with a bounded width, in a separate non-released section |
| D5 | Python 3.11.17 and the listed package versions as the reference environment |
| later | the nib rule (P2-13), after its own review |

## Missing source information (no algorithm can supply it)

- **Heights:** ceiling heights and storey sections. They decide wall finish areas, upturns, riser heights and reveals.
- **Openings:** door heights, leaf type and frame position in the wall; a door schedule.
- **Windows:** a window schedule or elevations (sizes, sills, heads).
- **Walls:** a wall specification or legend for 7 wall groups.
- **The unresolved door U8:** its host wall's layers are not identified as walls. The drafter, or a reviewer's layer-role decision, can settle it.
