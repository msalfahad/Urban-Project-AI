# T-194: residential review R6, opening consistency (plan = elevation = section = schedule / list)

Worker 2, 2026-10-22 21:45 - 22:30 UTC, run session_017p3DCATVEgGxRoLFmD5eWV. Lane A, gate 1, backlog-permitted. New
pure check module OPENING_CONSISTENCY_V1 (`engine/source/opening_consistency_v1.py`, imported by nothing, not wired); no
released quantity, rule file, frozen method, registry or key map changed; **no quantity produced** (findings are issue
rows and HELD causes). Development villa (Alsenan), not an accuracy claim. No drawing, image, title-block text, client
name or drawing coordinate is committed: sheets are cited by Drive title / page, positions are relative lengths.
ERS: read; sections 2 (element, evidence hierarchy, reconstruction, status), 3 (a notation's basis before its arithmetic,
build before deduct) and 4 (rule + test) applied.

## 1. Result in engineering terms (development villa)

71 openings checked (the 65 T-150 census rows + 6 plan openings the census lacks), against 4 elevations (NW and SE from
the DXF's DIMENSION entities and jamb lines; SW and NE from the PDF scans), the SE annex section, the fence plan and
fence elevation, and the T-150 list. No schedule is issued (designer D-07).

| Finding | Openings | Status | BOQ lines touched | New? |
|---|---|---|---|---|
| Width printed on two independent sheets AGREES (plan DXF jamb to jamb vs elevation DIMENSION; worst 4.9 mm) | W01 / W13 / W26 1.200, W14 2.4498, W15 / W16 1.5523, W18 0.500, W17 chord 2.6917 vs NW "269" 2.6915, W11 / W12 1.9549 vs fence plan "195" | DRAWING-CONFIRMED (identity and width) | none | new cross-check (10 openings) |
| **The T-150 list's sill / head are on the wrong basis** (SILL_LIST_DIFFERS, HEAD_LIST_DIFFERS) | W01: list 1.85 / 3.85 vs SE elevation +2.00 / +4.00 on the +1.00 floor = 1.00 / 3.00 above FFL; W03: list 1.00 / 5.30 vs NW +1.00 / +5.30 on the +1.00 floor = 0.00 / 4.30 | list value HELD for any line that reads SILL_M; area w x h unchanged (2.400, 28.251 m2) | sill / head consumers: block deduction (T-175 already corrected), finish band, reveals | reproduces T-175 (W01, W03) by the tool |
| On the plan, missing from the opening list (MISSING_FROM_LIST) | P-GF-01 0.90 (GF stair hall), P-1F-01 1.30 (1F), **P-GF-05 1.20** | HELD (head not printed) | supply class, reveals, finishes, lintel, threshold | P-GF-01 / P-1F-01 = T-175; **P-GF-05 new** |
| Head printed on no sheet (HEAD_NOT_PRINTED), width known | 21 windows (W02, W04-W12, W16, W19-W25, W27-W29), 2 arches, 3 lift-shaft openings, 3 passages, SX-01, SX-03, the gate D-GF-15 | HELD (D-45; never 0, never a twin) | opening m2, deductions, reveals, lintel | known (T-144 / T-150 / D-45); the tool finds all 21 windows |
| Door heads printed nowhere | 26 doors | ASSUMED — OWNER-APPROVED 2.20 (Q-55 C) in the BOQ: reported, not held again | - | known |
| Drawn on an elevation, on no plan (ELEVATION_ONLY) | 3 closed 100 x 100 mm squares at +8.788 .. +8.888 above W14 (SE, DXF layer 1, 0.80 m apart); 6 small squares above W11 / W12 (fence elevation) | UNKNOWN identity (vent, sleeve or ornament?) | if through-wall: 9 x 0.01 m2 = 0.09 m2 of deduction (negligible) and possibly a missing sleeve / vent item | **new** |
| On the list, on no plan (NOT_IN_PLAN) | U-01 0.93 | HELD (identity, T-150) | all | known |
| Width printed nowhere | D-GF-15 gate | HELD | all | known |
| Not shown, reason stated (never DIFFERS) | W02, SX-01 (NW draws the GF as a section); W11, W12 (SE cuts the annex); D-GF-06 (SW: entrance steps / landing in front, occlusion not excluded) | - | - | recorded |

Binding (which drawn window is which plan opening) was done by the module from relative positions, never typed: all
four elevations bind **unmirrored** (each drawn as seen from outside); 29 features bound, 0 ambiguous, 0 rival bindings
within 0.01 m. Identity results that confirm earlier ledgers: the NW twin that carries the printed 300 + 10 chain is W15
(plan OP-016), the headless twin is W16 (OP-017); the SW elevation (Pages_07-08 p.7) shows the y-max face of the house,
i.e. the "outside (court)" windows W05-W07 / W21-W23 / W25 / W27-W29 of T-150, plus the court-facing GF set W04, W08,
D-GF-01, D-GF-03, D-GF-09, P-GF-05 and SX-03, in the plan order on all three storeys.

Against the freelancer: a check task, no quantity moves. His aluminium and finishes sheets use flat heights where the
sheets print none; the 21 headless windows stay UNRESOLVED (T-150, D-45). The W01 basis defect is in OUR list, not in his
rows (his W01 is 1.20 x 2.00, which AGREES with the printed chain).

## 2. Physical element and the rule (standard s.2 step 1, s.3)

An opening is one physical element seen on several sheets; its attributes (existence, width, sill, head, type) each
carry their own evidence. A sill or head is a VERTICAL DISTANCE FROM A DATUM: a printed chain part, an absolute level and
a height above the finished floor are three notations of it, and they are compared only after each is reduced to the
height above the finished floor (basis first, arithmetic second). A width has a BASIS: straight jamb to jamb, an arc
length on a named face, or a projected chord (what an elevation dimensions on a plan-curved opening); bases are kept
apart, never compared with each other. A derived list (a census typed from the sheets) confirms nothing: it is checked
against the sheets. A view that cannot show an opening (section cut, occlusion) is NOT_SHOWN with its reason; only an
unexplained omission is DIFFERS. Values come only from printed dimensions or CAD DIMENSION entities (printed note N09,
"not to scale"); positions read at the print scale are used for identity only, never as a quantity.

**General rule proposed (any villa; provenance: standard s.3 + UP-DOOR-HGT-001 source order + UP-OPEN-SCHED-001; new
Urban rule, not a project fact):** before an opening quantity is released, every sheet that shows the opening is bound
to it and compared attribute by attribute on a stated basis; a width or level that differs between sheets, or a list
value that differs from the sheets, holds every line that reads it; a head printed nowhere holds the area (never 0,
never a twin); an opening drawn on an elevation and on no plan is reported, not measured. Proposed for the Lead as
UP-OPEN-CONSIST-001 v1.0.0 (a new rule file, never an edit of an existing one).

## 3. Reconstruction (what was read this run, Drive "Alsenan chalet project", read-only)

| Source | How | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ARCH_TAKEOFF_V2.9 run (scratchpad, exit 0) for every plan opening's width and centre; ezdxf: the NW and SE elevation frames' 386 DIMENSION entities (measured values), jamb lines (layer 1), the W17 arcs (W layer r 2.135 = 3.2895 outer; layer 5 r 1.935 = chord 2.6917 / arc 2.9767), W18 and SX-03 plan jambs / head lines, the SE annex arch, the three squares above W14 | PLAN_T194.csv, ELEVATIONS_T194.csv (NW, SE, annex section) |
| Alsenan_Architectural_P7757_Pages_05-06 p.6 (SE), Pages_07-08 p.7 (SW) and p.8 (NW), p7757_arch_sheet09 (NE), Pages_11-12 p.12 (fence plan / elevation) | 110 / 220 dpi renders, rotated; what each view draws, the printed chains | SW / NE features, kinds (leaf + handle = door; plain frame = leafless), section / occlusion notes |
| research/agents_t150 (census), agents_t175 (hosts, open-side classes), agents_t144 (chains) | read, not re-derived | the opening LIST; ids of the engine openings |

Plan -> elevation frame relation established from the drawings, not assumed: NW elevation x = plan y (+ constant), the
W15 / W16 / W17 centres reproduce the plan spacing 2.046 / 5.510 m to 9 mm; SE elevation x = - plan y, the stair column
to W14 4.907 m on both; the stacked stair windows give the 1F / 2F plan frame shifts (44.853 / 89.705 m).

Hand examples for the Checker (re-read two openings on the elevations, acceptance):

1. **W14 (SE)**: P7757.dxf SE frame, horizontal DIMENSION 2449.8 between jamb lines (layer 1) running +6.901 .. +8.50;
   vertical 2201.4 / 1598.6 (printed 220 / 160, Pages_05-06 p.6). Plan V2.9 1F OP-022 2.4498 jamb to jamb. Sill
   +6.90 - 5.50 = 1.40, head 3.00: list 1.40 / 3.00 AGREES. Three 100 x 100 squares above it at +8.788: on no plan.
2. **W17 (NW)**: horizontal DIMENSION 2691.5 (printed "269", Pages_07-08 p.8) = the chord of the wall-face arc r 1.935
   between the jamb ends on the 1F plan (2.6917), NOT the 3.29 outer glazing arc (owner Q-39 C, the supply measure) and
   not the 2.977 face arc (T-159 facade deduction): three bases, each labelled in its own ledger. Vertical 3050.5 +
   454.3 from +5.50 = crown 3.505 (printed 305 + 45 = 3.50).
3. (optional) **W01 basis**: SE chain 185 / 200 / 250 ... from +0.15: sill level +2.00, GF FFL +1.00 -> 1.00 above FFL;
   the T-150 SILL_M cell holds 1.85 (the chain part), head 1.85 + 2.00 = 3.85 > the 3.75 clear height (T-175 guard).

## 4. Findings for the designer list / the Lead (no owner question: standard 2.7 not met)

- **P-GF-05 (1.20, GF court-facing wall line, V2.9 OP-007)**: T-175 classed it as an open side split out of the wall
  runs ("not a building opening"); the SW elevation draws it between two vertical lines with a head line across and no
  leaf: an opening under a head. It belongs in the opening list (head not printed: HELD, D-45 family). Masonry deduction
  stays NOT_APPLICABLE (outside the runs, T-175); its reveals, head soffit, lintel and finish returns are unmeasured.
- **The 9 small squares** (SE above W14; fence elevation above W11 / W12): identity not established (through-wall vent /
  AC sleeve or a decorative tile). Designer question; no opening quantity is affected beyond 0.09 m2.
- **A-GF-01 arch head**: the SE annex section draws it (DXF layer 5: jambs 1.000 apart, springing +2.50, crown +2.80 on
  the +0.30 dewaneya floor = 2.20 / 2.50 above the floor) but prints no dimension: still HELD (N09); the designer can
  confirm the drawn crown (enclosing rectangle Q-32 A would be 1.00 x 2.50 = 2.500 m2, a candidate only).
- **D-GF-07 main entrance**: SE draws ONE 1.00 m leaf from the left jamb to the door's plan centre line; the other
  half lies behind the annex section edge: one leaf vs two is not decidable from this view; D-53 / T-161 F07c stand.
- **W11 / W12 pier order**: fence plan 81 / 195 / 115 / 195 / 83 against sheet03 as T-150 recorded it (83 ... 81); the
  direction of T-150's reading is not recorded: not established (0.02 m on a pier, no opening width affected).
- **T-150 SILL_M column**: correct it (or add the basis column) when T-150's owner next touches it: W01 1.00, W03 0.00
  above FFL (T-175's SILL_ABOVE_FFL_M already carries these).

## 5. Tests and validation

- `tests/t194_opening_consistency/test_opening_consistency.py` (non-Alsenan villa T194-A, hand truth in the docstring):
  plan / elevation / section / schedule agreement on three level bases (WA, BASIS_MIXED reported); a 0.05 m plan /
  elevation width conflict (WB, six lines held); single-source head (DA); head printed nowhere (WC, held, no area);
  missing from the schedule (DI; nothing "missing" when the project has no list); an elevation-only feature;
  adverse: mirrored elevation (binds only mirrored, same identities, ORIENTATION_CONFLICT when declared otherwise);
  millimetres (same result) and millimetres given as metres (refused); symmetric twins (AMBIGUOUS, nothing bound); a
  0.10 m square 8 mm from a window does not steal its identity, and without printed widths two windows are ambiguous;
  curved bay (chord vs chord AGREES, outer arc kept apart; wrong chord DIFFERS); a list holding a raw chain part
  (SILL_LIST_DIFFERS; on its true basis it agrees); a section cut (NOT_SHOWN) vs an unexplained omission (DIFFERS);
  NOT_IN_PLAN; guards: INFERRED, LEVEL without ffl, CHAIN_PART without chain_base, missing bases, missing units,
  unknown source, missing ref, duplicate observation, unbound records.
- `tests/t194_opening_consistency/test_alsenan_ledger.py`: the committed ledger reproduces byte for byte from
  repository files (`alsenan_t194.py --check`), and the four known cases are found by the tool: P-GF-01 / P-1F-01
  missing from the list, W01 basis, the 21 headless windows incl. W16, W16 width only; all four elevations unmirrored;
  the 9 elevation-only squares; no quantity column.
- Also run: tests/t175_opening_scope, tests/m9_p2b9/test_p2b9_openings.py (pass); freeze 0; maps rebuilt, stale none.
  tests/structural_comparison_engine/test_rebar_product_firewall.py fails on the working branch too
  (`engine/source/default_guard.py` undeclared, T-186 -> T-190): not this task's, unchanged by it.

## 6. Lessons-register row proposed (standard s.7)

2026-10-22 | The T-150 list's SILL_M held a chain part (W01 1.85) and a level (W03 1.00) under one heading; it was
caught only when a downstream deduction tripped a soffit guard (T-175) | values typed without their datum; a derived list
treated as if it confirmed the sheets | every sill / head carries its level basis and datum; a list value is checked
against the sheets and never counts as independent confirmation; bind every sheet to the opening before measuring
(any villa) | T-194 `test_list_with_raw_chain_part_differs_from_the_sheet` (adverse: raw chain part; normal: the same
value on its true basis agrees) + the W01 / W03 rows of the ledger test | READY (T-194), Checker to verify.

## 7. Files

`PLAN_T194.csv` (70 plan records: V2.9 widths jamb to jamb named through the T-175 host binding, 5 hand-read plan items,
6 door elements; relative along-facade positions; built from a scratchpad V2.9 run: method in its header text and
section 3), `ELEVATIONS_T194.csv` (50 elevation / section / fence readings with their sheet and the printed value or
the reason it is not shown), `alsenan_t194.py` (runs the check from repository files; `--check` reproduces),
`CONSISTENCY_T194.csv` (one row per opening: five verdicts, values per source, held lines, the BOQ height basis),
`ISSUES_T194.csv` (78 issue rows with the BOQ lines each touches and the known cover), `summary.json`.
