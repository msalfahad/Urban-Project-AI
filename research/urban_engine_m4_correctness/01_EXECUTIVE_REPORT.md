# M4 — source-evidence audit, continuous beams and structural completeness (ST7757)

Planning estimate. Not engineering-approved. Nothing in it is construction-approved or VERIFIED, and no OCR record
has been promoted. **The gate stays INCOMPLETE.**

Every number below comes from a live run:
- **M3:** commit `cbfa13e`, run in its own process from a separate worktree.
- **M4:** the frozen engine `35c0587` through the CLI pipeline (`tools/urban_boq_m2.py`).
- **Builder:** `build_m4_package.py`; the commands are in `14_COMMANDS.md`.

## 1. What was implemented in code

Every M4 behaviour is gated on the M4 convention set (`URBAN_M4_GENERIC_CONVENTIONS_V3.json`). An M2 or M3 run gives exactly what it gave before; the M3 live-reproduction test still passes.

| Module | What it does |
|---|---|
| `engine/source/continuous_beams.py` | **Span matching.** Matches a continuous beam's printed span sequence to the drawn line. Readings: forward, reversed, symmetric, ambiguous direction, count conflict, length conflict. A span takes a mark only through the printed sequence, never by alignment alone.<br>**Physical bars.** Bar groups (bottom per span, support top, top through, stirrups, laps at the stock length) are allocated to the pieces once, so mass is conserved. |
| `engine/source/arch_evidence.py` | Registers the architectural plans on the structural column outlines. Measures the wall cover on each ground beam and finds the printed floor level inside it. Supplies the opening census for lintels. |
| `engine/source/stair_measure.py` | Builds straight flights and winders from the drawn treads, using a riser rule. The flight plan is risers − 1 treads, and landings take the rest of the zone. A zone whose riser height is outside 0.14–0.20 m holds only part of a stair and is not measured. |
| `engine/source/lintel_measure.py` | **Openings:** masonry openings per wall layer; a gap is cut where a column stands in it.<br>**Rows:** the printed lintel schedule row is chosen by width. Bearings are added on masonry jambs only.<br>**Under a beam:** an opening under a beam is left UNRESOLVED (lintel need not established). |
| `engine/source/ocr_review.py` | **Check:** compares an independent second reading with every OCR record.<br>**Reject:** a disagreeing or ambiguous reading rejects the whole role.<br>**Promote:** never; only a person's confirmation can. |
| `engine/source/generic_route.py` | **Beams:** CB inheritance and CB bars; an unlabelled span across a support becomes UNRESOLVED, with the neighbour's section kept as an alternative.<br>**Ground beams:** the exterior detail applies only where a wall is evidenced (EVIDENCED / LEVEL_CONFLICT / NOT_EVIDENCED / NO_WALL).<br>**Slabs:** the project default thickness comes before the sheet tag. The member overlap is now the union over members, with face holes excluded.<br>**Blinding:** the exact union of footing outlines and beam strips.<br>**New families:** lintels and stairs. |
| `tools/m4_reports.py`, `tools/m4_overlay.py` | Generic registers for any project:<br>- missing-reinforcement register<br>- numbered unresolved-concrete exceptions<br>- CB lines and physical bars<br>- exterior ground-beam classes<br>- lintel openings<br>- slab faces<br>- OCR-derived items and conflicts<br>Also the M4 visual-QA overlays and PDF. The CLI writes them, with Excel sheets, whenever the M4 conventions are used. |
| `tools/urban_boq_m2.py` | New CLI options: `--arch` (architectural DXF) and `--evidence-review` (independent OCR readings). |
| `tools/synthetic_villa.py` | Opt-in `m4` variant for held-out testing. The other variants draw byte-for-byte as before. |

Tests: 9 files in `tests/m4_correctness/`. The hand-derived cases are:
- CB inheritance, count conflict, reversed reading, bar lengths and conservation
- exterior GB with an architectural plan
- stairs: straight, winder and partial
- lintels: census, beam-over and schedule
- slab default thickness, overlap and holes
- blinding union
- OCR review
- registers and visual QA
- generator plus held-out

## 2. Quantity errors corrected on ST7757 (M3 → M4, base)

| Family | M3 | M4 | Change | Cause (source evidence) |
|---|---|---|---|---|
| Beams | 70.02 m³ | 64.82 m³ | −5.20 | **What M3 did:** 10 spans had no label of their own. M3 gave each the section of the collinear beam across a support, from alignment alone.<br>**What M4 does:** holds them UNRESOLVED, with exposure 4.63–5.88 m³ and the neighbour's section kept as an alternative (5.20 m³). |
| Ground beams | 41.05 m³ | 34.48 m³ | −6.56 | **What M3 did:** applied the exterior detail to every perimeter band, at the main floor level +1.00.<br>**What M4 found** (the architectural ground-floor plan, registered on 28 of its 30 columns):<br>- 8 bands with a wall and the main level inside (7 read +1.00 on the plan, 1 with no level found, so the profile's +1.00): exterior depth kept<br>- 13 bands with a wall and +0.30 / +0.15 inside: no deeper than the class section, so the class section applies (conflict flagged)<br>- 2 bands at +0.00: class section<br>- 1 perimeter band without a wall: class section |
| Slabs | 61.67 m³ | 60.97 m³ | −0.71 | The printed project default of 16 cm replaces the sheet's one "T 18" tag on 7 untagged 2F panels. Member overlap is deducted on 2 panels. |
| Ground slab | 16.78 m³ | 16.75 m³ | −0.02 | Overlap of the slab face with beams and columns. |
| Blinding | 26.41 m³ | 22.16 m³ | −4.26 | Each square metre is now counted once:<br>- 42.2 m² of beam strip on footing blinding<br>- 5.9 m² where strips cross<br>- 0.3 m² where footing projections meet |
| Lintels | — | 0.46 m³ (+65 kg) | +0.46 | 57 openings were found on the architectural plans. 10 have no beam over them and are measured. 46 are UNRESOLVED (exposure ≤ 3.42 m³). 1 is wider than the schedule. |
| Beam steel | 7,564 kg | 8,359 kg | +795 | **Added:** 1,835 kg on 23 CB pieces from the physical bar model; 31 kg on the span the sequence assigns.<br>**Removed:** 1,070 kg, the bars of the 10 alignment-only spans (now unresolved). |
| Ground-beam steel | 4,918 kg | 4,738 kg | −179 | The exterior detail's bars now follow the evidenced case. |

The independent checks found three engine defects; all were fixed and covered by tests:
- **CB bars dropped:** 30.2 kg of CB3 bars were silently dropped on a span printed with two marks. They are now held as an exposure.
- **Slab hole deducted twice:** a member inside a slab-face hole was deducted again (0.25 m²).
- **Blinding double counts:** strip and footing overlaps, shown in the table above.

## 3. Differences that are still assumptions

**Exterior ground beams**
- The inside floor level is the nearest printed level on the inside, within 8 m.
- Build-up is 0.10 m (0–0.20) and the outer ground is 0.00 (0–0.15).
- The 13 level conflicts are an RFI.

**Slabs and blinding**
- The project default slab thickness of 16 cm is a local OCR reading of a general note, not reviewed.
- The blinding projection of 0.10 m and its scope under beams are read visually from p.13, not reviewed.

**Continuous-beam bars**

| Value | Basis |
|---|---|
| Support-bar extent 0.22 Ln, measured from the axis | printed, plus a reading of its basis |
| Bottom extension 0.075 m | printed |
| Anchorage 40 d, lap 50 d, 12 m stock | conventions |
| Larger reading for the 2 lines with ambiguous direction | convention |

**Beams**
- Beam depth is read as total depth, a convention.
- The ground-beam length basis is centre to centre.

**Lintels**
- Bearing 0.20 m (0.15–0.25).
- An opening under a beam is held UNRESOLVED.

**Typical-detail bars**
- All 14 records are OCR-derived and unreviewed.

## 4. New totals (ST7757, provisional, planning base with low – high)

- **Concrete: 312.05 m³ (305.64–331.97).** Plus 86 unresolved items with exposure 17.71–30.74 m³, held out of every total. M3: 328.34 m³ with 30 unresolved.
- **Steel: 27,168 kg (24,109–29,384).** Plus 61 unresolved steel items:
  - 31 ground-beam links
  - 24 CB top-through roles
  - 4 CB support-top roles
  - 2 exposure items holding 29.5–30.4 kg on the two-mark span

  M3: 26,488 kg.

## 5. Unresolved concrete components

There are **86**, numbered and located in `07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv` and on the overlays:

| Class | Count | What they are |
|---|---|---|
| Lintel need not established | 46 | a beam covers the opening fully (43) or partly (3) |
| Missing label | 13 | unbound beam bands |
| Missing source | 13 | column necks / column types without a schedule row |
| Source ambiguity | 12 | 10 unlabelled spans across a support, 1 band with two marks, 1 ground-slab cell with free columns |
| Not slab | 2 | stair zones; each holds part of a stair, with risers outside 0.14–0.20 m |

**Structural (non-lintel): 40**, exposure 17.71–27.33 m³. M3 had 30; the +10 are the alignment-only spans.

## 6. Components still without full reinforcement data

There are **169** (114 MISSING_DATA + 55 PARTIAL_MISSING), split by whether the component itself is measured:

| Group | Count |
|---|---|
| Measured component, bars missing | 83 |
| Section unresolved | 40 |
| Lintel need unresolved | 46 |

Like for like with M3's 110 (82 + 28):
- every one of the 110 still lacks at least one bar role;
- 24 moved from MISSING_DATA to PARTIAL_MISSING (CB bars added);
- 10 became MISSING_DATA (alignment-only spans);
- 3 became PARTIAL_MISSING (ground beams);
- 46 are new lintel candidates.

Missing roles:

| Role | Components |
|---|---|
| All bars | 114 |
| Ground-beam links | 31 |
| CB top-through | 24 |
| CB support top | 4 |

Measured concrete without full bars: 31.56 m³. This is a count of what is missing, never a kg/m³ ratio.

## 7. Did CB modelling reduce missing steel?

Partly. All 24 pieces on the 11 mapped CB lines moved from MISSING_DATA to PARTIAL_MISSING, gaining 1,835 kg of bottom, support-top and stirrup bars. None is complete:
- the schedule prints no top-through bars (24 pieces);
- four support-top cells are blank.

In count terms, components with no bar data went from 82 to 114: 82 − 24 + 10 + 46. The rise is the honest bookkeeping of the 10 alignment spans and the 46 lintel candidates.

## 8. Independent accuracy evidence

**On ST7757: 33 / 33 independent checks pass** (`10_INDEPENDENT_VALIDATION.csv`).
- **Second method:** shapely, a geometry library the engine never uses. It checks:
  - slab net areas and member overlaps
  - band conservation (no region in two bands)
  - footing volumes
  - CB bar arithmetic and per-line mass conservation
  - item-level conservation
  - the blinding union
  - lintel and exterior-GB arithmetic
- **Shared code:** what each check shares with the engine is stated per row. All checks use the detected polygons; detection is not redone.
- **Third method:** grid sampling settled the one slab difference the second method could not explain.
- **Limitation:** arc-bounded slab faces (65 m² of 4 sheets) are not compared, because their stored ring is a chord polygon.

**On 40 new synthetic villas (seeds 601–640, never used before; `11_HELDOUT_EVALUATION.md`):**

| Measure | M3 | M4 |
|---|---|---|
| Unlabelled-span precision | 0.70 (72 wrong sections) | **1.00** |
| Unlabelled-span recall | 0.70 | 0.53 |
| Exposure contains the truth | — | 112 / 112 held spans |
| CB concrete MAE | 16.8 % | **0 %** |
| Drawings whose base-to-exposure envelope contains the truth (m4 variant) | 13 / 40 | **39 / 40** |
| Beam base MAE (m4 variant) | 1.2 % | 9.1 % |
| Beam base MAE (clean drawings) | 0.22 % | 6.1 % |

- **Price of the precision:** M4's base error is larger because the spans it holds leave the base.
- **Not measured:** there is no reviewed ground truth for ST7757 itself. The checks prove internal consistency and arithmetic, not the reading of the drawing.

## 9. Can the engine process a genuinely new villa without project-specific data?

**Pipeline: yes.** On all 80 held-out drawings, end to end, with no manual step:
- generic V3 conventions;
- a profile holding only the printed storey heights.

There are no hidden defaults:
- every value is a named convention with provenance;
- `engine/source` holds no project tokens, enforced by the r8_1 boundary test;
- the ST7757 profile is a separate file of 17 entries, each with its printed source.

**Coverage: limited by printed evidence.** A new villa gets what its own drawings and profile print. Without a profile, these stay UNRESOLVED or excluded, never guessed:
- typical ground-beam classes
- exterior levels
- the lintel schedule
- default slab thickness
- blinding thickness
- the stair waist

## 10. Next highest-impact task

A person's review of the source items that block the largest quantities (`12_RFIS.csv`). Each confirmation moves the quantity into the base:

| RFI | Question | Scope |
|---|---|---|
| RFI-M4-01 | CB top-through bars | 24 pieces |
| RFI-M4-07 | links of the ground-beam class under 5 m (EV-0007; the second reading gives Ø8/15cm) | 18 bands |
| RFI-M4-03 | sections of the 10 unlabelled spans | 4.6–5.9 m³ |
| RFI-M4-11 | lintel need under beams | 46 openings |
| RFI-M4-06 | exterior ground beams at the annex / court levels | 13 bands |

On the engineering side, the highest-impact work is a review workflow: a sheet a person fills in, which `detail_evidence` records as MANUALLY_CONFIRMED with who and when.
