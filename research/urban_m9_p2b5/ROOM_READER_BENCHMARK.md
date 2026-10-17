# Room-reader benchmark: method and reading (Phase 2B-5 Stages D / F)

Generated figures: `bench/BENCHMARK_RESULTS.md` and `.json`. Runner: `tests/m9_p2b5_bench/bench_run.py`. Assertions:
`tests/m9_p2b5_bench/test_bench.py`. Synthetic drawings only.

## 1. Cases and truth

- **Plans.** Sixteen synthetic plans in millimetres with 200 mm walls, wall faces cut at openings and closed by jambs.
  - B01 - B10 are geometric cases. B01 - B09 are drawn by `tools/arch_synth`'s plan writer, then mirrored and / or
    turned. B10 is drawn from its own primitives.
  - C01 - C06 are the same plans written in other CAD encodings.
- **Truth.** It is written by hand as typed literals in `bench_cases.py`, a file that imports nothing:
  - rectangle and L areas, the column deduction, the splay;
  - the arc's circular segment `r^2 (θ − sin θ) / 2`;
  - the outer perimeters, and the opening widths and kinds.
- **Checks on the truth itself:**
  - `test_the_hand_truth_matches_the_coordinates` checks the literals against the coordinates by shoelace and by
    the arc formula, never by a reader.
  - `test_an_encoding_case_keeps_its_base_truth` checks that an encoding case keeps its base case's truth.
  - `test_the_mirrored_plan_mirrors_every_point` checks the mirrored plan.

| case | what it tests |
|---|---|
| B01 | rectangle 4.00 x 3.00 m, door 0.80, window 0.60 |
| B02 | B01 with the door a mirrored block (xscale −1) |
| B03 | L-shape 8.00 m2 |
| B04 | a free-standing 0.40 x 0.40 m column (7.34 m2 net) |
| B05 | two rooms sharing a door |
| B06 | B01 turned 27 degrees |
| B07 | a 45-degree splayed corner |
| B08 | an unlabelled lobby joined by a 1.00 m passage |
| B09 | B05 mirrored as a whole plan |
| B10 | an arc wall (chord 3.00 m, rise 0.50 m, r 2.50 m): 13.021882 m2 |
| C01 | B01's walls in nested blocks: mirrored, turned 90, non-uniform scale 2.0 / 0.5 |
| C02 | B01 in metres |
| C03 | B04's walls as closed and open LWPOLYLINEs |
| C04 | B05 with Arabic room words and linear DIMENSIONs |
| C05 | B01 with a window block |
| C06 | B01's walls in an XREF not supplied: the truth is a refusal |

The vision methods run on B01 - B10; an encoding case draws the same picture as its base.

## 2. Readers

| method | reader | independence |
|---|---|---|
| NATIVE_AUTO / NATIVE_DECLARED | the engine (`tools/urban_boq_m9.py arch`, ARCH_TAKEOFF_V2.5), with layer roles inferred / declared | run as a separate process; nothing of the engine is imported by the benchmark |
| REF_DXF | ezdxf + shapely: wall-face closure rules + polygonise; doors by swing arcs, windows by glazing lines | its own rules, no engine code |
| RASTER_10MM / SCAN_25MM | the deterministic raster prototype on a 10 mm / px render / a degraded 25 mm / px scan | image only |
| PDF_VECTOR | the vector-PDF prototype on a 1:100 PDF of the same linework | PDF paths only |
| MCP adapters | NOT_AVAILABLE (none connected) | - |

## 3. Metrics

- **Rooms:**
  - recall over labelled rooms;
  - false rooms;
  - IoU against the truth polygon (outer rings on both sides; holes are counted in area);
  - area and perimeter error (%);
  - boundary error (Hausdorff, mm);
  - corner error (mean distance from each truth corner to the reader's ring, mm);
  - label correctness.
- **Openings:** matched by kind and width within 0.06 m (correct / wrong kind / missed / spurious).
- **Other:** the raster scale check (measured wall thickness − 200 mm) and runtime.
- **Refusals:** a case whose truth is a refusal is scored as refused or not refused, never on rooms.

## 4. Reading the results

- **Engine.**
  - **Declared roles:** exact on every straight-walled case and every encoding, with every opening. The XREF is
    refused (no BOQ published).
  - **Inferred roles:** a door, window or column layer drawn only once is not recognised (D-D1). Eleven
    single-door drawings type their openings as passages, and B04 / C03 keep the column in the floor (+2.18 %).
  - **B10:** exact area and boundary length, but a chord polygon (IoU 0.92, boundary 0.50 m) (D-D2). The BOQ
    consequences are in `MCP_SKILLS_AUDIT.md` §3.
- **Independent reader:** exact everywhere. On B10 the 0.5 mm arc flattening costs 0.008 % of area. It misses only
  B08's door on the unlabelled lobby, because it reads labelled rooms only.
- **Vector PDF:** exact (B10 within 0.002 %); all 12 labels read from text objects; openings not supported.
- **Raster, 10 mm / px:**
  - area within 0.75 % and IoU at least 0.989;
  - perimeter within 0.4 % on straight walls and 1.6 % on the arc;
  - openings exact on the straight, unrotated plans, but on the 27-degree plan one opening is found with 5 spurious
    gaps, and the arc wall gives one spurious passage;
  - OCR labels 8 of 12.
- **Scan, 25 mm / px:**
  - area within 4.1 %, IoU at least 0.959;
  - every case has spurious gaps (4 - 9);
  - no label read;
  - on B09 the unread room word joins the east wall and cuts a 1.45 m spur into the room (perimeter +23 %).

  These are review candidates only.
- **Hybrid** (the CAD reading = REF_DXF):

  | vision source | AGREE | REVIEW_CANDIDATE | VISUAL_OMISSION |
  |---|---|---|---|
  | PDF | 12 | - | - |
  | raster | 12 | - | 1 (the unlabelled lobby) |
  | scan | 0 | 12 | 1 |

  No value is averaged and no BOQ quantity comes from vision.
- **Runtime** (median per case, indicative): engine 1.1 s, independent reader 0.01 s, raster 0.6 s, scan 0.24 s,
  PDF 0.01 s.

## 5. What a failure here means for the BOQ

| failure | BOQ effect | status |
|---|---|---|
| D-D1 (inferred roles, single instance) | doors / windows typed as passages: door lines, thresholds and doorway waterproofing missing; a column not deducted from floor / ceiling | remedy available (`--layer-roles`); inference rework in the roadmap |
| D-D2 (arc chord) | layouts (membrane, tiles) planned on the chord; curved walls missing from wall run, masonry, plaster | asserted as found; fix in the roadmap (opt-in) |
| C06 (XREF) | none: the run is blocked, no BOQ published | correct behaviour |
| raster / scan errors | none: vision is never a BOQ basis | by design |

## 6. Reproducibility

- Every drawing is deterministic: fixed DXF metadata, fixed seeds and fixed matplotlib metadata.
- The results JSON omits runtimes, and a regeneration is byte-identical.
- `test_the_prototypes_are_deterministic` checks both prototypes.
