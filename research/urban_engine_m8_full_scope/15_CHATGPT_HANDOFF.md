# 15 Handoff — what worked, what did not, what to do next

**Where to continue.** Branch `claude/access-permissions-setup-ii24ws`, after the M8 package commit. Read in this
order:
1. `01_EXECUTIVE_REPORT.md`
2. `11_WEAKNESS_REGISTER.csv`
3. `03_SCOPE_RULES.md`
4. this file

The engine is `engine/source/` with conventions `engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json`, run by
`tools/urban_boq_m2.py run --route G --conventions …V6.json`.

## What worked

1. **Turning findings into measured items or ranges, never into silence.**
   - The M6 completeness engine already located most of the missing scope as findings with shape magnitudes.
   - M8 adds one pass over those findings. Each becomes either measured items (settled family) or a bound with a
     basis.
   - ST7757: 85 volume-less findings → 0. Held-out: 0 without range on 80 villas.
   - That one change makes the BOQ's bounded total meaningful: on 80 of 80 held-out villas the whole RC truth lies
     inside it.
2. **A strict "settled family" rule.** Only MEDIUM / HIGH confidence, no candidate families, and no conflicting family
   word on the layer or in nearby notes. A pool with a LIFT note stays a bound, not a pool. This kept wrong-family
   measurements rare: 1 of 474 held-out elements was measured as another family (a pool, S_B seed 419,
   held-out vocabulary). The truth was still inside its range.
3. **The nearest printed note wins, otherwise a named convention.** Printed-dimension error is ≈ 0 (max 0.73 %).
   Where the dimension is a convention, the truth is in range for 17 of 18 kind rows.
4. **The synthetic generator with hidden design truth, printed in about half the elements.**
   - It found real defects before the freeze: dome ribs read as a winder stair; a pit inside a footing given a
     second base; neighbour notes; furniture as pits.
   - It also found B.W sizes in mm read as cm, which would have priced 60.9 m³ on ST7757.
5. **Freeze → held-out → post-freeze fixes in their own record.** It kept the evidence honest. The one acceptance
   miss (pit depth range) was reported, not tuned away.
6. **The metamorphic harness extended to bounded totals.** It found:
   - the 180° tread binning split;
   - a face-boundary floating-point case;
   - a furniture line joining a stair flight (P1).
7. **Ablation of each rule alone (P4).** Every ST7757 change has a named cause. The largest contributors are the
   scope pass itself (21.8 m³), the dome rule (7.4 m³), the boundary-wall row (7.2 m³) and the stair rules
   (6.2 + 3.7 m³).
8. **Positions as differences only, with a test.** The firewall test caught a chance 3-decimal match in synthetic
   truth. It now checks the synthetic records at the code level instead: the code that makes them never reads the
   M5 record.

## What did not work / is still open

1. **Still one real project, post-discovery.** There is no blind second villa, so "as strong as the freelancer" and
   "more accurate than the MCPs" cannot be proven. ST7757 total RC is within 6 % of all three external positions,
   and they lie inside V6's range. By family the gaps remain (`08_ST7757_POSITIONS.md`).
2. **Pool (W8-01).** Only the wall strip on the ground-beam plan is read. The detail sheet (depth, the other walls)
   is not. ST7757 pool is about half the stage figure.
3. **Core families untouched (W8-10).** On ST7757:
   - ground slab: −42 to −47 % against the external positions;
   - ground beams: −15 to −19 %;
   - necks: +23 to +77 %;
   - columns: +29 % against the freelance QS.

   These are M5 bridge items: a perimeter tie beam, the slab under the stairs, levels.
4. **Reinforcement for every new family is MISSING_DATA (W8-09).** It is correct not to use a ratio, but a QS BOQ
   prices that steel.
5. **Wide bounded range on ST7757** (313 – 476 m³). Parapets (0 – 44.4) and the roof tank (0 – 10) are the biggest.
   The drawing does not say RC or block / GRP.
6. **Two pre-existing property failures, now visible on the bounded total:**
   - **Mirror, 10 of 10 villas.** A mirrored HATCH keeps object-coordinate paths, so the hatch-on-member finding is
     lost (W8-02).
   - **Furniture noise, 7 of 10 villas.** Column-sized furniture rectangles become possible columns (W8-03).

   In both cases the measured items stay invariant.
7. **Convention ranges narrower than some designs (W8-05).** Pit depth goes to 1.70 m against a 1.60 m high;
   boundary-wall sections to 0.435 m²/m against 0.36. They were deliberately not widened after the freeze.
8. **The dome rule is a heuristic (W8-06).** A radial group on the top plan, with "dome" named in the set, is read
   as a dome. A radial stair to the roof would be misread.

## Recommendations (in order)

1. **A blind second villa** (structural DXF + architectural + an independent BOQ). Run it frozen with V6 through
   `tools/urban_project_run.py`, following M7 `09_SECOND_VILLA_BLIND_TEST.md`. Compare only after the freeze. This
   is the only evidence that can answer the goal.
2. **An engineer / QS review of ST7757** with the M7 release policy. Approve or reject each scope item and answer the
   five largest RFIs (`07_ST7757_BEFORE_AFTER.md`). That turns ranges into released quantities.
3. **Read detail sections** (pool, parapet, stair waist) as a gated V7 convention set. It is the largest
   under-measure and the widest bound. Validate it with a generator extension that draws the sections.
4. **Reinforcement for the scope families** from bar details. Never by ratio.
5. **Fix W8-02 and W8-03** behind conventions:
   - OCS → WCS for hatch paths;
   - layer evidence for column-presence findings.

   Then require mirror and noise to pass on the bounded total.
6. **Core-family gaps (W8-10).** Address them only with evidence from a second villa, so that ST7757 is not tuned.
7. **Keep in every milestone gate:**
   - the M8 evaluator;
   - the metamorphic harness with `--completeness`;
   - the external-figures firewall test.

## Do not

- **Quote from these numbers.** They are planning figures with ranges; nothing is released.
- **Read the freelancer / MCP figures to choose a convention or a reading.** Positions only after a freeze, as
  differences.
- **Turn an unsettled finding into a measured item.** It stays a bound under each candidate family.
- **Use a kg/m³ ratio** for any reinforcement.
- **Edit the frozen records** (`heldout/`, M2–M7 packages) or the M4 freeze.
- **Widen a convention range to pass a held-out score** after the freeze.

## Prompt for the next chat (copy as is)

> Continue the Urban Project AI engine from the M8 package (`research/urban_engine_m8_full_scope/`, branch
> `claude/access-permissions-setup-ii24ws`). Read `01_EXECUTIVE_REPORT.md`, `11_WEAKNESS_REGISTER.csv` and
> `15_CHATGPT_HANDOFF.md` first.
>
> The engine is generic: every rule is a convention in `URBAN_M8_GENERIC_CONVENTIONS_V6.json`. Keep that
> discipline:
> - new behaviour goes in a new convention set (V7);
> - V6 and the frozen packages must reproduce;
> - freeze before any held-out or external comparison.
>
> Next milestone (M9):
> - (a) the blind second-villa run if a drawing set is available, otherwise
> - (b) detail-section reading for pool / parapet / stair waist, validated on a generator that draws sections;
> - plus reinforcement for the scope families from bar details.
>
> Do not open the freelancer / MCP records before the freeze. Never use a kg/m³ ratio. Keep the verdict "not
> quotation-ready" until released quantities and a blind project exist.
