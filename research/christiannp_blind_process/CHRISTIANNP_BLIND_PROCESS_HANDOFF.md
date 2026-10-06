# christiannp-autocad blind run: forensic process handoff

Nothing in this package changes the sealed christiannp result, Urban production code or any frozen Urban register. No BOQ was rerun.

## 0. Read this first: what evidence exists

The sealed christiannp blind run was executed **outside this environment**, on the owner's AutoCAD + MCP machine. None of its records was ever delivered to Urban:

- no tool-call log;
- no AutoLISP and no local scripts;
- no raw entity dumps;
- no strip, raster-cell or pair lists;
- not the A1–A15 or R1–R5 texts.

The repository records the donor as `UNRESOLVED_EXTERNAL_REPOSITORY` (`research/external_engine_lab/DONORS.lock`).

Places searched (`process_log/EVIDENCE_INVENTORY.json`):

- every tracked file;
- the session upload folder (file names only; the credential and do-not-open files were not opened);
- this session's transcript;
- the account's cloud sessions.

**The step-by-step process record requested in §1 cannot be written from evidence held here.** I have not reconstructed tool calls, LISP or scripts from memory or plausibility. A forensic handoff that invents its own evidence is worse than none.

What this package does instead is label every statement with one of four evidence classes:

| Class | Meaning |
|---|---|
| **RELAYED** | A christiannp figure or statement as you relayed it in a brief (S3.1 §16, coverage-recovery §5–6, this brief). |
| **INFERRED** | Arithmetic that follows from relayed figures. It is not a donor record and is labelled as a hypothesis where it is not unique. |
| **URBAN_FROZEN** | Urban's own frozen registers: the coverage-recovery round and V3b. |
| **NOT_HELD** | Requested but not available here. |

The cross-checks are produced by `scripts/build_crosschecks.py`, which is deterministic, reads only frozen registers and writes `intermediate_geometry/URBAN_CROSSCHECKS.json`. To complete §1 verbatim, drop the run's export into the folders listed in §11; every folder has a README that says what belongs there.

## 1. Process record (the §1 table)

The table below lists only the stages that the relayed descriptions establish. For every stage, these fields are **NOT_HELD**:

- tool name and arguments;
- active document;
- the exact entity / layer filter;
- the LISP / script text;
- retries;
- per-object output.

The "kind" column comes from your relayed summary ("direct AutoCAD/LISP entity extraction", "manual engineering allocation still existed", "A1–A15"). It does not come from a log.

| # | Stage | Kind (RELAYED basis) | What is established | Resulting population |
|---|---|---|---|---|
| 1 | Open ST7757 / P7757, query entities | NATIVE_MCP + CUSTOM_LISP ("direct AutoCAD/LISP entity extraction") | raw LINE / ARC / POLYLINE reading | NOT_HELD |
| 2 | Footing outlines + tags + schedule ATTRIB | CUSTOM_LISP / NATIVE_MCP | footings 65.669 m³ | count NOT_HELD |
| 3 | Ground-beam strips by face pairing | CUSTOM_LISP + LOCAL_SCRIPT (pairing) + **ASSUMPTION A5** | 42 strips, 200.036 m, 36.006 m³ | 42 strips (list NOT_HELD) |
| 4 | Ground slab | **ASSUMPTION A7** (area) + text (T=10 cm) | 324.038 m² × 0.10 = 32.404 m³ | one outline |
| 5 | Slab plates: 50 mm raster of layer-1 lines + arcs, exterior flood fill | LOCAL_SCRIPT (raster) + **ASSUMPTION A1** | net GF 290.555 / 1F 179.325 / 2F 55.275 m²; slabs 58.111 / 28.692 / 9.950 m³ | cell maps NOT_HELD |
| 6 | Columns: outlines + nearest label, per floor | CUSTOM_LISP + MANUAL_REASONING + **ASSUMPTION A8** | FOU 6.150, GF 26.235, 1F 8.888, 2F 3.377 m³ | NOT_HELD |
| 7 | Beams: strips + rules R1–R5 | LOCAL_SCRIPT + **MANUAL_REASONING** ("manual engineering allocation") | GF 25.206, 1F 18.562, 2F 2.823 m³ | NOT_HELD |
| 8 | Walls: parallel-face pairing | LOCAL_SCRIPT | 150 mm 79.971 m, 200 mm 183.497 m | pair list NOT_HELD |
| 9 | Wall faces (plaster/paint) | **ASSUMPTION** ("assumed wall/finish heights") | 2364.7 m² gross | NOT_HELD |
| 10 | Rebar | CUSTOM_LISP + MANUAL_REASONING | 22.916 t, **known incomplete** | NOT_HELD |

Relayed as unresolved in the run: windows and room areas.

## 2. Ground beams (§3)

**The premise needs correcting first.** Urban's ground-beam *population* is not smaller:

| | christiannp (RELAYED) | Urban (URBAN_FROZEN) |
|---|---|---|
| Objects | 42 strips | 59 spans (31 interior, 28 exterior) |
| Length | 200.036 m | 198.796 m (interior 88.496 m + exterior 110.300 m) |
| Difference | | +1.240 m (+0.62 %) |

The volume gap is **section and release, not extraction**.

**INFERRED, exact:** 200.036 m × 0.30 m × 0.60 m = 36.0065 m³, which equals the relayed 36.006 m³. Every strip was given one uniform 0.30 × 0.60 section.

| Urban class | Spans | Length m | Urban m³ | At donor 0.30 × 0.60 | Donor − Urban |
|---|---|---|---|---|---|
| Interior, depth 0.30 (p.13 DETAIL) | 16 | 24.999 | 2.250 | 4.500 | +2.250 |
| Interior, depth 0.40 (DETAIL) | 11 | 40.567 | 4.868 | 7.302 | +2.434 |
| Interior, depth 0.60 (DETAIL) | 4 | 22.930 | 4.127 | 4.127 | 0.000 |
| Exterior, depth unprinted ('FOLLOW ARCH.'), Urban best 1.0 (0.90–1.30 bracket) | 28 | 110.300 | 33.090 | 19.854 | −13.236 |

So the donor's uniform section overstates the interior by 4.684 m³ against the printed details, and sits below Urban's elevation-derived bracket on the exterior. The two errors offset.

Answers to A–P:

- **A. How the 42 strips were discovered:** NOT_HELD. RELAYED: raw LINE / ARC / POLYLINE reading plus face pairing.
- **B. Layers / entities:** NOT_HELD. Urban finds the same bands on layers 1 + 2 of the GROUND BEAMS sheet.
- **C–G. Pairing algorithm, width range, parallelism tolerance, overlap requirement, de-duplication:** NOT_HELD.
- **H. Curved beams:** NOT_HELD. Urban pairs arcs separately (`_arc_bands`).
- **I. Exterior beams retained:** yes (INFERRED: 200 m needs the 110.3 m exterior run).
- **J. Region-crossing strips retained:** NOT_HELD. The length agreement within 0.6 % suggests nothing large was clipped.
- **K. Unlabelled strips included:** INFERRED yes. The exterior spans carry no section label.
- **L. Source handles:** NOT_HELD.
- **M. How 200.036 m was obtained:** the sum of the strip lengths (list NOT_HELD).
- **N. Drawing-derived part:** length, and the 0.30 width (equal to the drawn band width).
- **O. Assumed part:** depth.
- **P. Is 0.60 m assumption A5 and not measured?** **Confirmed.** It is relayed as A5, and it reproduces the total only as a uniform value. The p.13 details give 0.30 / 0.40 m on 27 of the 31 interior spans.

**Why Urban's ground-beam *release* was small, and which capability the donor used that Urban lacked.** Urban did not lack an extraction capability: V3 already measured all 59 spans. What Urban lacked until the coverage round was a **publication rule that keeps a measured population when one dimension is missing**. The exterior spans went to technical BLOCKED, and comparisons read the technical layer, so they showed 0. The donor's "capability" was to *fill* the missing depth with a constant. Urban now keeps the same population and carries the missing depth as a BOUNDED scenario (`ground_beam_recovery`, already in the coverage round). The boundary-wall beam (Urban 5.289 m³, C-BWALL) is in Urban's 49.624 best but apparently not in the donor's 200 m.

## 3. Ground slab (§4)

Thickness authority and area authority are classified separately, as asked.

| | THICKNESS_AUTHORITY | AREA_AUTHORITY |
|---|---|---|
| Donor value | 0.10 m | 324.038 m² |
| Basis | the T=10 cm note. Urban finds the same text on the GROUND BEAMS sheet (texts H5782\|5776, H5782\|5789). The exact donor source object is NOT_HELD. | **ASSUMPTION A7**: GF gross outline |
| Status | SOURCE text; its *scope* (all panels or labelled panels) is unresolved | CANDIDATE scope, not verified |

- **A. Why 0.10 m:** the T=10 cm text (RELAYED).
- **B. Exact source object:** NOT_HELD.
- **C. Why the area is the GF gross outline:** A7 (RELAYED).
- **D. Stated as slab-on-grade, or assumed?** Assumed. No source statement equates the GF slab outline with the slab on grade.
- **E. How the outline was built:** INFERRED as the 50 mm raster outer boundary of the GF slab plan. Donor 324.038 m² against Urban's vector gross 322.413 m² is +1.625 m² (+0.5 %), consistent with raster edge cells.
- **F. Openings / external areas:** none deducted from the ground slab (324.038 is the gross).
- **G. Alternative boundaries considered:** NOT_HELD.
- **H. Why Urban released less:** Urban measures the founded cells *between* ground beams, net of beam and column footprints. Until the coverage round it released only cells holding a `T=` label (11.5 m³). It now carries the 9 unlabelled cells as CANDIDATE: best 21.701 m³, about 217 m².

The remaining ~10.7 m³ to the donor is the A7 scope: the ground-beam and column footprints, plus the area under openings in the suspended outline. That is an area-authority difference, not missed geometry.

## 4. Slab polygon / raster method (§5)

RELAYED: 50 mm cells; layer-1 lines + arcs; exterior flood fill. **NOT_HELD:**

- grid origin and bounding region;
- line and arc rasterisation;
- stroke thickness;
- seed;
- the beam-interior, slab-labelled, opening and unresolved-enclosed classes;
- edge-cell allocation;
- area formula;
- duplicate prevention.

Why GF / 1F / 2F come out at 290.555 / 179.325 / 55.275 m², without using those areas as targets. This is INFERRED, set against Urban's own openings:

| Floor | Implied thickness (m³ / m²) | Gross used | Donor deductions | Best-fit Urban openings | Residual |
|---|---|---|---|---|---|
| GF | 58.111 / 290.555 = **0.200** (A1) | 324.038 (donor, A7) | 33.483 | 3 VOIDs (4.584 + 27.076 + 3.240), stair well kept | −1.417 |
| 1F | 28.692 / 179.325 = **0.160** | 217.201 (Urban; donor gross not relayed) | 37.876 | 3 VOIDs (3.240 + 17.127 + 16.357), stair well kept | +1.152 |
| 2F | 9.950 / 55.275 = **0.180** | 55.478 | 0.203 | none | +0.203 |

- **Hypothesis H-SLAB-1:** the raster deducts VOID openings and keeps the 10.725 m² stair well on both floors.
  - Both floors fit within raster edge tolerance.
  - It is NON_UNIQUE: the second-ranked fit on GF drops the 3.24 m² void instead.
  - If it holds, the donor counts the stair well as slab while also measuring stairs separately (5.048 m³), which is a double-count risk.
- **The GF 27.076 m² void carries a T16 tag.** Urban holds it as OPENING_CONFLICT; the donor deducts it under either hypothesis.
- **A1 effect:** 290.555 × (0.20 − 0.16) = **+11.622 m³** on GF slabs.

**Could a raster become an independent Urban geometry oracle?** Yes, as an **oracle-only** second route for gross outline, opening and enclosed-region areas. It must never be a production authority:

- it is independent of Urban's vector topology;
- it fails differently, so agreement between the two raises confidence.

Risks of a 50 mm raster:

- Edge cells: ±(perimeter × 25 mm) per boundary is ≈ ±1.7 m² on a 70 m perimeter, which is the size of the residuals above.
- Gaps narrower than one cell close, and thin voids vanish.
- Arcs are quantised.
- Flood fill leaks through a single missing pixel, or through a gap at a door.
- Text, hatch and dimension strokes become false walls unless layers are filtered.
- Results depend on the grid origin.

Convergence protocol:

- Rasterise the same floor at 100 / 50 / 25 / 10 mm, and at each size under two grid origins offset by half a cell.
- Record the following per class (outside, slab, opening, beam-interior, unresolved): area, perimeter, and connected-component count.
- **Pass:**
  - each class's area changes by less than 0.5 % between 25 and 10 mm;
  - component counts are stable from 50 mm down;
  - the two origins agree within one edge-cell band (perimeter × cell / 2).
- **Fail (route the region to review):**
  - a component count changes with resolution, which means a leak or a closed gap;
  - area moves monotonically with resolution, which means stroke-thickness bias.

Tests are listed in `CHRISTIANNP_RECOMMENDATIONS.md`.

## 5. Beam strip allocation (§6)

The rules R1–R5 exist in the sealed report, but their texts are **NOT_HELD**, so condition, reason, example and failure mode per *donor* rule cannot be given. The behaviours this brief names are assessed below as **techniques**: the analysis is Urban's, the exact donor conditions are unknown.

| Behaviour | Generic? | Safe to adopt? | Urban view / failure mode |
|---|---|---|---|
| Parallel-face strip creation | yes | yes, as geometry | Same as Urban Method B / `pair_parallel_faces`. Fails on fragmented faces and on finish lines at beam width. |
| Label-to-strip matching | yes | with ambiguity records | A nearest label can bind to the wrong strip at T-junctions. Urban's tag-band ladder records the binding level. |
| Repeated same-mark labels < 2 m apart → one occurrence | partly | as a candidate de-dup only | The threshold is drawing-scale-specific. Two real short beams can be merged. |
| Schedule width vs drawn width check | yes | **yes** | A strong consistency gate. A mismatch should flag the binding, not force it. |
| Sharing remaining length among simple labels | no | **no** | Allocation by arithmetic, not geometry. This is the clearest manual-reasoning point. |
| Continuous-beam schedule-span capping | partly | as a QA check | The span count must come from geometry. Capping hides a missing support. |
| Unlabelled strips | yes | as CANDIDATE | Urban: CANDIDATE_QUANTIFIED with identity (coverage round). |
| Fragments | yes | with a continuity proof | Urban `beam_occurrence_recovery` continuity route. |
| Curved beams | yes | yes | Arc length per strip; NOT_HELD how the donor handled them. |
| Support-to-support vs face-to-face length | convention | declare it | Urban: clear length × B × (D − t). The donor basis is NOT_HELD; per-floor gaps are below. |

Per floor (INFERRED vs URBAN_FROZEN):

| Floor | Donor | Urban technical | + residue (commercial) | + dome ring beams |
|---|---|---|---|---|
| GF | 25.206 | 21.414 | 27.694 | — |
| 1F | 18.562 | 13.523 | 15.192 | 19.170 |
| 2F | 2.823 | 2.650 | 2.650 | 4.639 |

The donor sits between Urban's technical and residue-inclusive figures on GF. Whether the 1F donor figure includes the dome ring beams is unknown.

Manual reasoning was *necessarily* required at these points, judged from the method (the log is NOT_HELD):

- label ambiguity at junctions;
- length sharing;
- span capping;
- CN continuation;
- opening classes in the raster;
- the wall height choice.

## 6. Columns: occurrence and floor membership (§7)

- **NOT_HELD per floor:** outlines, labels, nearest-label logic, coordinate transforms, stopping logic, schedule joins, CN and planted-column treatment.
- **INFERRED** from relayed volumes over Urban's S1 section sums (assuming the same population):

| Floor | Urban occ. | Urban ΣA m² | Urban net m³ | Donor m³ | Donor ÷ Urban ΣA | Class |
|---|---|---|---|---|---|---|
| FOUNDATION | 36 | 6.24 | 12.626 | 6.150 | 0.99 m | DIFFERENT CONVENTION (storey split) |
| GF | 30 | 4.50 | 19.527 | 26.235 | 5.83 m (> 4.50 storey) | SOURCE_CONFLICT / convention: donor GF carries volume Urban books under FOU |
| 1F | 20 | 2.44 | 9.857 | 8.888 | 3.64 m | DONOR_ASSUMPTION likely (clear of beams; joints excluded) |
| 2F | 9 | 0.94 | 3.779 | 3.377 | 3.59 m | as 1F |

- FOU + GF: donor 32.385, Urban 32.153 m³ (+0.232). The census totals agree; the split does not.
- **URBAN_CORRECT:** the 95-occurrence census with explicit chains, and no CN propagation.
- **DONOR_ASSUMPTION:** A8, CN continues FOU + GR. This conflicts with the later Urban and human review.
- **Note:** FOU 6.150 / GF 26.235 / 1F 8.888 are *identical* in the U-C4N and christiannp blind results; only 2F differs. Two independent routes producing three identical values to the litre needs an explanation (a shared helper, or a shared figure in the brief) before either is treated as corroboration.

## 7. Footings (§8)

- **NOT_HELD:** outline detection, tag assignment, threshold, duplicate prevention, ATTRIB extraction, and the F / F10, F3, FN and multi-column handling.
- **URBAN_FROZEN, occurrence by occurrence:** 25 released occurrences, 64.346 m³. The full table is in `URBAN_CROSSCHECKS.json → footings.urban_occurrences_table`.

| Type | Count | Each m³ |
|---|---|---|
| F | 4 | 0.216 |
| F2 | 2 | 1.131 |
| F3 | 2 | 0.672 |
| F4 | 2 | 1.760 |
| F5 | 2 | 2.016 |
| F6 | 1 | 2.860 |
| F8 | 1 | 7.200 |
| F9 | 1 | 5.049 |
| F11 | 1 | 2.625 |
| F12 | 1 | 9.856 |
| F13 | 1 | 5.160 |
| F14 | 1 | 6.270 |
| F15 | 1 | 0.720 |
| FF | 1 | 11.385 |
| FN | 4 | 0.300 |

Also held: the F / F10 outline (handles H4261, H5771), BLOCKED as a source conflict, with scenarios 2 × F = 0.432 or 1 × F10 = 1.960.

The donor total is 65.669 m³, a difference of **+1.323 m³**. Without the donor occurrence list the difference cannot be assigned occurrence by occurrence. Ranked arithmetic candidates:

1. F/F10 as 2 × F, plus one extra F and one extra F3: +1.320 (residual 0.003).
2. Two extra F3: +1.344 (−0.021).
3. One extra F + one extra F2: +1.347 (−0.024).

The leading candidate matches the causes you named earlier (F3 count, F / F10), but it is **NON_UNIQUE**.

## 8. Wall pairing (§9)

- **NOT_HELD:** every donor parameter and every donor pair. `CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json` says so explicitly. Its 166 rows are **Urban's Method B reconstruction**, run on the P7757 wall layer through the unchanged generic classifier:
  - 150 / 200 mm ± 15 mm, overlap > 200 mm;
  - fields per pair: face handles, width, overlap length, floor, accepted reason (PAIRED_WALL / OPENING_SPAN / COLUMN_OVERLAP_POLICY / DUPLICATE_FACE) and confidence.
- **200 mm, Method B gross 184.897 m** breaks down as:
  - paired wall 111.615;
  - opening spans 34.570;
  - column overlap 28.819;
  - duplicate faces 9.893.

  christiannp's 183.497 m is **1.400 m below that unclassified gross**. INFERENCE: the donor figure is raw pairing before classification. It includes ~35 m across openings, ~29 m along column faces and ~10 m of duplicates.
- **150 mm:** Method B gross 85.728 m against the donor's 79.971 m. Urban established 77.507 m, best 78.401 m.
- The three 200 mm figures measure different populations:
  - Urban established bands (89.74 m frozen; you quoted ≈ 79 m, which I could not trace to a frozen register here);
  - U-C4N 148.1 m: partially classified pairs, basis NOT_HELD;
  - christiannp 183.5 m: raw pairs.

## 9. Plaster / wall area (§10)

| Input | Donor value | Class |
|---|---|---|
| Wall length | 79.971 + 183.497 = 263.468 m | DERIVED (raw pairs, see §8) |
| Height | 2364.7 / (2 × 263.468) = **4.488 m** (INFERRED) | ASSUMED ("assumed wall/finish heights" RELAYED). Equal to the GF storey applied everywhere |
| Faces | 2 per wall (INFERRED) | DERIVED |
| Door / window deduction | none (INFERRED; "windows unresolved" RELAYED) | UNRESOLVED |
| Ceramic exclusion | NOT_HELD | UNRESOLVED |
| External / internal split | NOT_HELD | UNRESOLVED |

Urban `physical_wall_faces`:

- 266 faces with handles;
- two faces per masonry band, height = structural interval − terminating member, net of openings;
- verified 1220.508 m², best 1618.18 m²;
- split by floor and by interior / exterior role.

The lesson is to preserve **PHYSICAL_WALL_FACE_AREA** first and assign finishes afterwards, not to copy the donor's finish total.

## 10. Assumptions (§11), gap register (§12), classification (§13)

- `CHRISTIANNP_ASSUMPTION_FORENSICS.json`:
  - A1, A5, A7 and A8 are RELAYED and fully treated, with sensitivity: A1 +11.622 m³; A5 ±6.0 m³ per 0.10 m of depth; A7 +0.163 m³ against Urban's gross outline.
  - A2–A4, A6 and A9–A15 are **NOT_HELD**; their texts were never relayed.
- `CHRISTIANNP_VS_URBAN_GAP_REGISTER.json`: 11 trades, every row classified A–E.
  - No row is **A** (more complete *and* source-supported).
  - Ground beams, ground slab and plaster are **B** (assumption-dependent).
  - Columns, slab net area and 150 mm walls are **C** (different basis).
  - 200 mm walls are **D** (non-wall length counted as wall).
  - Beams, slab openings, footings and stairs are **E** (unknown).

## 11. To finish §1 verbatim

Export the christiannp session from the machine where it ran, and drop each item into its folder unchanged:

| Item | Folder |
|---|---|
| Conversation / tool log (.jsonl or .md) | `tool_calls/` |
| `.lsp` / `.scr` files and evaluated expressions | `lisp/` |
| `.ps1` / `.py` scripts | `scripts/` |
| Entity dumps | `raw_extractions/` |
| Strips, raster maps, pairs | `intermediate_geometry/` |
| The sealed report with A1–A15 and R1–R5 | `process_log/` |
| Errors and retries | `failed_attempts/` |

Record each file's sha256 in `process_log/INTAKE_LOG.json`. A second pass can then fill every NOT_HELD field in this document without touching the sealed result.
