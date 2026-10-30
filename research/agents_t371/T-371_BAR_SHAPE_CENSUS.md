# T-371 Bar-shape source census for B11-02 (bar bending schedule): released route + candidate (development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPneg2NH3Dxjb6GFmCmA, branch `agents/task-T-371`. A source
census, not a takeoff: **no kg, no bar count and no length is computed** (owner 2026-10-25 10:33); no candidate line,
rule, method or released quantity changes. B11-02 stays PARTIAL. Drawings named by Drive folder and title only.

## 0. Sources read this run

Drive "Alsenan chalet project" (read-only; private copy in the git-excluded folder, never committed): 'ST7757.pdf'
(sha256 74da1523.., 16 pages, no text layer) rendered at 110 / 220 / 400 dpi and read by eye: p.3 (ground-slab label),
p.8 (notes 1 - 24: no hook, bend or BBS note), p.9 (schedules; DETAILS OF COLUMN REINFORCEMENT), p.10 (simple beams,
strap rows), p.11 / p.12 (continuous-beam rows + typical span diagram, 400 dpi), p.13 (both TYP. DETAIL OF ISOLATED
FOOTING, the four Ground Beams sections, 220 dpi), p.15 (twisted column, BEAM CARRYING PLANTED COL., TYP. SLAB ON BEAMS
DETAIL, 400 dpi). Candidate lines: the merged T-297 extract (ARCH_TAKEOFF_V3.0.16 = V3.0.17, 2,505 reinforcement lines,
sha256 2f28367b..), pinned in the builder. Built on, cited not re-derived: T-149, T-171 / T-299 (footings), T-148 /
T-273 (columns), T-307 / T-316 / T-318 (slab ends), T-359 (special elements), T-366 (lap authority, READY).

Files: `t371_shape_census.py` (BAR_SHAPE_SOURCE_CENSUS_V1, stdlib), `t371_alsenan_input.py` ->
`ALSENAN_BAR_SHAPE_INPUT.json` + `LINE_BINDING_T371.json`; outputs `T371_MATRIX.csv` (population x 7 shape attributes,
state + sheet / detail ref) and `T371_SUMMARY.json`. Tests `tests/t371_shape_census` (19). Repeat:
`python -I t371_alsenan_input.py --check`, then `python -I t371_shape_census.py ALSENAN_BAR_SHAPE_INPUT.json
LINE_BINDING_T371.json --csv T371_MATRIX.csv --json T371_SUMMARY.json`.

## 1. Engineering question and method (ERS s.2.1: notation before arithmetic)

Physical element: one bar of a population as it would be bent and cut for a bar bending schedule: its body (straight,
L, U, closed link, spiral), each end (straight, leg, hook, up / down bend), leg length, hook, bend diameter, crank. A
BBS shape is a different geometry from the net bar of the released kg (installed length between faces); the census
asks only which of those attributes the drawings PRINT. Seven attributes per population, each PRINTED (sheet / detail),
PRINTED_TYPICAL (on a typical whose own title names that element class: the code refuses a typical of another element),
PRINTED_MINIMUM ('Min. 30cm': a bound, never an exact length), DRAWN_UNDIMENSIONED (owner option B: drawn part HELD,
never given a length), NOT_PRINTED, NOT_APPLICABLE, RULE (answered rule only), CONFLICT. A population is SCHEDULABLE_NOW
only when no attribute blocks; SCHEDULABLE_AFTER when every block names an RFI of rfi/A or rfi/B; GAP when one names a
NEW gap; OWNED_ELSEWHERE when the open item is another census's (T-366 lap length). Labels are read as notation first:
'n ø d' is a count; 'n ø d/m' a rate; 'ø d/s cm' a spacing; '2ø12/30cm' count-per-spacing (RFI-B-S19): the code
refuses a rate or a spacing as a count.

Owner manual method vs drawing-derived method: the owner has no recorded BBS / bar-shape method (OWNER_RULE_REBAR sets
units and keeps laps under assessment; option B 2026-10-29 counts drawn parts only). The drawing-derived reading is the
only one and is shown in full in the matrix.

## 2. Result (acceptance (a) and (b)): 38 populations, 2,417 lines + 88 to T-359 = 2,505 bound

| Status | Populations | Candidate lines |
|---|---|---|
| SCHEDULABLE_NOW (shape) | 7 | 442 |
| SCHEDULABLE_AFTER (named RFI) | 10 | 767 |
| GAP (new gap id) | 19 | 1,150 |
| OWNED_ELSEWHERE (T-366 laps) | 2 | 58 |
| T-359 (stairs / pool / tank) | - | 88 |

| Population | Lines | What the drawings print (shape) | Status (blocking) |
|---|---|---|---|
| FTG-BOT-MESH | 51 | p.13 both footing typicals: 'Long bars' / 'Short bars' straight, no end bend | **NOW** (end position vs boxed legs is a length item, T-299) |
| FTG-TOP-MESH (F8, F12 - F14, FF) | 10 | no top layer on either typical | AFTER RFI-B-S09 |
| FTG-TOP-END-LEGS | 4 | p.9 REMARKS cage symbol only | GAP G-T371-0 + RFI-B-S09 |
| FTG-BOXED | 20 | p.13 'Boxed bars': inverted U, legs down to the mesh; leg end level, diameter, the corner marks not printed | GAP G-T371-1, -0 |
| STARTER | 28 | p.13: L foot 'Min. 30cm', foot end bent up, 'Max. 10cm' position, '40 ø' projection (right); cranks drawn (left) | GAP G-T371-2, -0 |
| COL-MAIN-BODY | 120 | straight verticals (p.13 'Column reinforcement', p.15 elevations) | **NOW** |
| COL-TOP-END | 46 | no column-head detail | GAP G-T371-3 |
| COL-SECTION-TRANSITION | 44 | size change per storey printed, crank / new bar not | GAP G-T371-3 |
| COL-STOREY-LAP | 56 | straight overlap | OWNED T-366 |
| COL-LINKS (incl. necks) | 207 | p.9: closed link, 3 arrangements by L, corner hook tick undimensioned | GAP G-T371-3, -0 |
| COL-TWIST-EXTRA | 2 | p.15 '4ø16 EXTRA' straight, '1M' + '1M' | **NOW** |
| COL-TWIST-SPIRAL | 2 | p.15 spiral 6ø8/m; diameter, end turns not printed | GAP G-T371-4 |
| SB-BOTTOM / SB-TOP | 187 / 187 | p.10 count and diameter only, no elevation of any simple beam | AFTER RFI-B-S21 |
| SB-BOTTOM-ENDS / SB-TOP-ENDS | 98 / 98 | nothing | AFTER RFI-B-S21 |
| BM-UNSCHEDULED | 12 | projection bands / upstands: no bars | GAP G-T371-5 + RFI-S18 |
| BEAM-LINKS | 243 | p.15 slab-on-beam section: closed link, corner tick; p.10 nested symbol | GAP G-T371-0 + RFI-B-S20 / S21 |
| BEAM-SIDE-BARS | 54 | remark text only | AFTER RFI-B-S19 / S21 |
| PLANTED-COL-EXTRA | 2 | p.15 4ø16 hooked ends, 'DEPTH' extent | GAP G-T371-0 + RFI-B-S22 |
| CB-BOTTOM | 58 | p.11 / p.12 straight, no end leg, overlap drawn | **NOW** (overlap length T-366 F-T366-3) |
| CB-TOP-CORNER | 55 | every CB row: DOWN leg at each end support, undimensioned; interior end straight at 0.22 Ln | GAP G-T371-0 + RFI-B-S21 |
| CB-TOP-ENDS / CB-BOTTOM-ENDS | 29 / 29 | the drawn end is the leg / a straight end; nothing beyond | AFTER RFI-B-S21 |
| CB-SUPPORT-TOP | 77 | straight, '0.22 Ln' / '0.3 Ln2' printed | **NOW** |
| GB-MAIN | 131 | p.13: straight through the column (footing details), dots in the 4 sections | **NOW** |
| GB-BAR-ENDS | 62 | ends shown broken | AFTER RFI-B-S09 |
| GB-STIRRUPS (incl. SB1 - SB3) | 65 | p.13: closed link, corner tick; p.10 nested symbols | GAP G-T371-3, -0 + RFI-B-S20 |
| GB-SIDE | 30 | p.13 exterior G.B: straight; an unlabelled X between them | GAP G-T371-6 + RFI-B-S09 |
| GB-BOTTOM-TIES | 0 | unlabelled verticals in all 4 G.B sections (no line; never added) | GAP G-T371-6 |
| GB-LAPS | 2 | straight overlap | OWNED T-366 |
| SLAB-BOTTOM | 170 | p.15 straight, 50 % stop at .125 L, up-turn at a non-continuous support ('40 CL.') | GAP G-T371-7, -0 |
| SLAB-DEVELOPMENT | 98 | straight to 40 mm of the face; up-turn leg at edge beams | GAP G-T371-7, -0 |
| SLAB-TOP | 98 | '.25 L1' / '.30 L' straight; hook-down leg at the outer face | GAP G-T371-7, -0 |
| SLAB-UNPRINTED-PANELS | 13 | no bars printed on the panel | AFTER RFI-B-S10 |
| SLAB-TEMP | 3 | straight (p.15 section + schedule) | **NOW** |
| SLAB-EXTRA | 2 | zone hatches only | GAP G-T371-7 |
| GROUND-SLAB-MESH | 24 | p.3 '5ø10/m E.W. T=10cm' (a RATE), straight mesh; edges not printed | GAP G-T371-7 |

SCHEDULABLE_NOW is a statement about the SHAPE only: those lines can carry a straight shape code; their lengths keep
their own ledger status (column datum D-39, footing end position T-299, CB overlap T-366). No line moves.

## 3. Gaps for the Lead (each asked in no RFI of rfi/A or rfi/B)

| Gap | What is not printed | Lines blocked (as sole or joint block) |
|---|---|---|
| G-T371-0 | bend diameter / hook extension for every bent shape (p.8 notes 1 - 24, no BBS legend) | every drawn leg, hook, link, spiral |
| G-T371-1 | footing boxed bars: diameter, leg end level, upper-corner marks (T-171 / T-299 item never reached the RFI pack: F-T371-4) | 20 |
| G-T371-2 | starter foot exact length ('Min. 30cm'), foot up-bend, deep-detail crank | 28 |
| G-T371-3 | column / neck / ground-beam link hook; column head and section-change bar shape (RFI-B-S21 asks beam links only) | 362 |
| G-T371-4 | twisted-column spiral diameter and end turns | 2 |
| G-T371-5 | upstand bars on B20 / B23 | 12 (with RFI-S18) |
| G-T371-6 | unlabelled G.B marks: X between exterior side bars; second-layer verticals | 30 |
| G-T371-7 | slab end legs, corner / extra bar shapes, ground-slab edges (RFI-B-S10 asks the top extent only) | 392 |

Proposed homes: G-T371-0 one line added to RFI-B-S21 ("bend diameter and hook extension for all bar marks, or the
standard governing them"); G-T371-1 / -2 a footing-detail RFI beside RFI-B-S09; G-T371-3 extend RFI-B-S21 to column,
neck and ground-beam links; G-T371-6 / -7 extend RFI-B-S09 / RFI-B-S10. No owner question: each is a drawing gap
(ERS s.2.7 not met).

## 4. F-T318-1 slab-end legs (acceptance (c)): PROPOSAL only, never a value

| Leg | Drawn (p.15 TYP. SLAB ON BEAMS) | Bound basis proposed | Status |
|---|---|---|---|
| Bottom up-turn at a non-continuous support | inside the slab, bottom layer up to the top layer, '40 CL.' from the outer face | D - bottom cover ('25 CL' printed in the same detail) - top cover (p.8 note 22 >= 2.5 cm, a minimum: an UPPER bound only); D = panel thickness from the plan | PROPOSAL, HELD blank (option B) |
| Top anchor bar hook-down at the outer face | **passes below the slab soffit into the edge beam** (F-T371-1) | NOT 'D less covers' (Checker F-T318-1): the drawn bound is the edge-beam depth (p.10 / p.11 schedule D) less its bottom cover and the beam's own bar layers | PROPOSAL, HELD blank |

F-T371-1 corrects the scope of F-T318-1: the 'D less note-22 covers' bound holds for the bottom up-turn only.

## 5. Findings for the Checker / Lead (no quantity changed)

- **F-T371-1** (above): the top hook-down leg is drawn into the edge beam.
- **F-T371-2**: p.13 G.B sections draw unlabelled marks (X between the exterior-G.B side bars; short verticals from the
  second bottom layer in all four sections). Neither has a candidate line; never added before G-T371-6 is answered.
- **F-T371-3**: no bend diameter or hook extension is printed anywhere (G-T371-0): no bent BBS shape is schedulable now,
  even where every leg is drawn (CB top corner legs, links, starters).
- **F-T371-4**: the footing BOXED-bar request recorded by T-171 / T-299 as a designer item reached neither rfi/A nor
  rfi/B.
- Continuous beams: every CB row draws the top corner bars with a down leg at each END support (incl. CB8 span 1 5 ø18,
  T-149) and the bottom bars with NO leg; the 254 beam bar-end lines on note 9 (T-366 F-T366-2) therefore have a drawn
  shape at the top (leg, undimensioned) and none at the bottom.

## 6. Engine vs freelancer; verdict proposals

No BOQ line moves (no kg). The freelancer's reinforcement is a kg/m3 lump (44.19 t) with no bar shape:
**RULE_DIFFERENCE, no %**. Verdict proposals: F-T371-1 ENGINE_WRONG in basis for any future top-leg bound taken from
'D less covers' (none exists: HELD); the shape gaps UNRESOLVED (designer).

## 7. Rule proposed (every villa; provenance T-371; a rule version only when adopted)

**R-BBS-SHAPE-1**: before any BBS line, census each population's shape attributes (body, each end, leg, hook, bend
diameter, crank) as PRINTED / PRINTED_TYPICAL (own element class only) / PRINTED_MINIMUM / DRAWN_UNDIMENSIONED /
NOT_PRINTED; a shape is schedulable only when no attribute blocks; a drawn undimensioned leg, a minimum and a typical of
another element never give a length; bend diameter / hook extension is a separate attribute that blocks every bent
shape until printed or ruled.

## 8. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | the slab top-leg bound 'D less covers' was proposed for both slab-end legs, but the top leg is drawn into the edge
beam; and a footing boxed-bar designer item never reached the RFI pack | a bound was stated from the slab thickness
without re-reading where the drawn leg ends; designer items in reports were not carried to rfi/ | read each drawn leg's
end against the member it enters before proposing a bound; census every shape attribute against the RFI register (every
villa, T-371) | tests/t371_shape_census (borrowed typical refused; undimensioned leg or minimum given a length refused;
rate / spacing as a count refused) | PROPOSED |

## 9. Self-gate and not done

self-gate: a (real code + 19 tests), c (villa K371 by hand + adverse), d (research files only, freeze 0), f (held stays
held, no kg, no value), h (every candidate line bound once) PASS. Not done: the binding uses the V3.0.16 extract (=
V3.0.17); later integrations (T-318 V3.0.27 slab ends: 138 part lines added) are not in it: lane I re-binds by the same
component rules. Route G beam items carry no mark: BOT / TOP bound to the simple-beam populations (shape status equal
to the CB-ends status: AFTER RFI-B-S21). Corner / extra slab bars: legend hatches only read on p.3; the slab plans
p.4 - p.6 were not re-read this run for bar lines inside those zones.
