# T-041: trace of the "lost" ground band (T-036 F4), route G run A vs run B

Worker 3, 2026-10-19. Diagnostic only: no engine, rule, knowledge, test or data file changed. Development reference,
not an accuracy claim. No drawing coordinates, labels or client data: bands are named by sheet number, run-local id,
width and length only.

## Inputs and runs (outside the clone, nothing private committed)

| Input | Where | sha256 |
|---|---|---|
| structural DXF | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" | 9f9d1179...38079 (= SOURCE_MANIFEST.json) |
| architectural DXF | Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 (= SOURCE_MANIFEST.json) |

Working branch 2748ffe, Python 3.11 venv from requirements.txt.

- Run A and run B: exactly T-036's commands (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --structural ...
  --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json --no-m9-xlsx --no-svg`, run B + `--profile
  research/urban_engine_m4_correctness/profile_st7757_m4.json`). Both exit 0. Reproduced T-036: in run A the SH08 band
  "BAND0044" has the HELD line `U-C:GROUND_BEAMS:GROUND:BAND0044` (exposure 0.566 - 1.886 m3); in run B no output file
  contains `GROUND_BEAMS:GROUND:BAND0044`.
- Band trace: `research/agents_t041/band_trace.py` (new, read only) calls route G the same way the arch command does
  (`tools/urban_boq_m2.compute(route="G", completeness=True)`, structural drawing only, as `urban_boq_m9.py:2831`)
  and matches every SH08 ground band of run A to run B by its **source face handles + length + width**, not by id;
  a run A band with no match is looked up in run B's slab faces. Totals reproduce T-036 exactly (run A exposure
  17.801 - 59.337 m3 over 59 bands; run B 27.365 m3 over 58 released lines).

## Finding: no silent omission. The id moved, and one run A "band" is a slab cell

**Band ids are not stable between runs.** `member_detection.beam_bands` (`engine/source/member_detection.py:743-777`,
FROZEN) numbers bands in width order (`:776`). With the profile, `generic_route.detect`
(`engine/source/generic_route.py:318-330`, FROZEN) adds the printed typical width (0.30) and rejects the drawn width
modes that no schedule row or typical section prints (run B `width_basis`: REJECTED_DRAWN_MODES 0.20, 0.60, 0.65,
0.85, 0.90, 0.95). One run A band at a rejected width disappears from the band list, so every later id shifts by one.
T-036 matched run A to run B by element id and so saw a band "lost".

SH08 ground bands, run A 59 -> run B 58, every one accounted for:

| Run A bands | Run B | Count | m3 |
|---|---|---|---|
| same id, same faces | PROVISIONAL ground-beam line (BOUND_TYPICAL_CLASS) | 56 | |
| renumbered: A BAND0043 -> B BAND0042, **A BAND0044 -> B BAND0043** | PROVISIONAL ground-beam line (BOUND_TYPICAL_CLASS) | 2 | |
| subtotal ground-beam lines | | 58 | 27.365 (= T-036 run B) |
| A BAND0042 (width 0.95 m, length 1.20 m, `width_conflict` = True) | **no band**: a ground-slab panel `P-C:GROUND_SLAB:GROUND:SITE-2870ca7b...` (PROVISIONAL, 1.14 m2 x 0.10 m) | 1 | 0.114 |
| **total** | released / provisional, none held, none dropped | **59** | |

Count check: 56 + 2 + 1 = 59.

### The band T-036 named (A BAND0044 = B BAND0043)

A curved ground beam (ARC band, faces paired on two concentric arcs). Run B line `P-C:GROUND_BEAMS:GROUND:BAND0043`,
same two source faces, PROVISIONAL **1.1316 m3**, binding BOUND_TYPICAL_CLASS.

Hand check from the drawn geometry (DXF arc radii and the faces' overlap angle, not the engine's quantity):
inner radius 2.250 m, outer 2.550 m (width 0.30 m), overlap angle 2.61949 rad.
Plan area = (2.550^2 - 2.250^2) / 2 x 2.61949 = 0.720 x 2.61949 = **1.8860 m2** (= centreline 2.400 m x 2.61949 =
6.2868 m long x 0.30 m). Span 6.29 m > 5 m -> the profile's printed typical class '>5m (30x60)' (GB_TYPICAL_SECTIONS,
READING_OF_PRINTED_VALUE, ST7757.pdf p.13) -> H 0.60 m -> 1.8860 x 0.60 = **1.1316 m3** = the run B line.
Uncertain: the span basis for a curved beam (arc length between supports) is the engine's; no Urban rule states it.

### The band that really left the band list (A BAND0042)

Run A paired the inner face of one 0.30 m ground beam with the inner face of the parallel 0.30 m ground beam next
to it (the same two faces are also faces of A BAND0012.x and A BAND0021, hence `width_conflict` = True) and called
the 0.95 m gap a 0.95 m wide "band" (HELD, exposure 0.342 - 1.14 m3). No schedule row and no typical section prints a
0.95 m ground beam (schedule widths 0.50 / 0.70 / 0.80 / 1.00, typical 0.30). In run B the 0.95 m width is rejected
and the same 0.95 x 1.20 m area is a closed slab face bounded by beam faces (perimeter 4.30 m = 2 x (0.95 + 1.20))
classed PANEL, region GROUND_SLAB, released as ground slab.

Hand check: 0.95 x 1.20 = **1.14 m2** x 0.10 m (sheet uniform ground slab thickness) = **0.114 m3** = the run B line.

Verdict proposal (run A vs run B, no freelancer line involved): **ENGINE_RIGHT for run B**: a cell between two
parallel beam faces with no printed section at its width is a slab cell, not a beam; run A's held 0.34 - 1.14 m3
was a false beam exposure. Nothing double counted in run A (the same face was a BEAM_STRIP with no slab line).

## Rule check (UP-QTY-STATUS-001)

Every run A ground band is released, held or a named exclusion in run B: 58 as ground-beam lines, 1 as a ground-slab
line. No silent omission. T-036's census row C3 "1 band absent from every run B output" should read "1 band
(0.95 m, width conflict) became a ground-slab panel; BAND0044 is run B BAND0043".

## For the lead (proposals, not tasks I opened)

1. Any census that compares two route G runs must match bands by source handles + length + width (as
   `band_trace.py` does), never by BAND id: ids depend on the set of widths searched.
2. Transparency, low money: run B's `width_basis` (REJECTED_DRAWN_MODES) reaches no output file (grep of every run B
   output). Here the rejected cell is still measured as slab, so it is not an omission; a later run-log field in a new
   output version could list per sheet the drawn width modes rejected and where their area went. No fixture designed:
   no defect found.

## Uncertain

- Run B rests on the typed route G profile (T-044 audit, owner Q-17); this trace says nothing about whether the 30x60
  class is right for the curved beam beyond the profile's own reading.
- Only SH08 (the only GROUND_BEAM_PLAN sheet) was traced.
