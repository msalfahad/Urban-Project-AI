# Independent verification results (Phase 2B-9)

The tools are `tools/indep_reader.py` (ezdxf + shapely + arithmetic, **no engine module imported**) and
`tools/arch_change_verify.py`.

- The verifier classifies each BOQ difference between two runs as VERIFIED, EXPLAINED_UNVERIFIED, CONTRADICTED or
  UNEXPLAINED.
- **The reader is an audit tool, not the blind reference.** Each new capability was first checked against hand truth
  on a synthetic fixture (`tests/m9_p2b9/test_p2b9_indep_census.py`, 5 tests).
- Inputs the verifier takes from a run are statements, not quantities: the layer roles and the plan region boxes.
  Every length and area is read again from the drawing.

## 1. New independent checks

| Check | What it reads | Hand-truth fixture | Result |
|---|---|---|---|
| `return_census` | parallel wall-line runs per infinite line (split where a gap exceeds an opening); a pair at a band thickness overlapping 0.05–0.30 m in total, nothing between, one end closed, inside a plan region, not in a column outline | example 3R: one 0.20 m return; example 3: none (the collinear stubs are a 0.70 m band); a box away from the plan: nothing | 3 / 3 |
| arc census midpoints and inner faces | the ARC / bulge pairs' own parameters | example 4S: two stubs, inner 0.20, centreline 0.206667 m each | 2 / 2 |
| INDEPENDENT_STUB_CENSUS (verifier) | ARCH.WALL_RUN under a WALL_STUB record: the floor's short curved pairs + straight returns, in its region | example 3R V2.7.1 → V2.8: +0.20 m VERIFIED; example 4S: +0.413333 m VERIFIED | 2 / 2 |
| certain-skirting takeoff (verifier) | FIN.SKIRTING under a WINDOW_SKIRTING record (no sill established): perimeter + hole perimeters − every gap closed on the face | example 1 without a schedule: 13.00 → 11.50 m VERIFIED | 1 / 1 |

## 2. Reference plan, V2.7.1 → V2.8 (Mode A)

| Difference | Delta | Record | Independent reading | Status |
|---|---|---|---|---|
| ARCH.WALL_RUN, first floor | +0.16854 m | WALL_STUB (CURVED_STUB, 0.20 m wall) | arc census: the same pair, radii 1.935 / 2.135 m, sweep 0.082820668 rad → 0.16854 m; a second piece of 0.041407 m (inner face 0.039 m) below the 0.05 m artefact limit; return census in the region: none | **VERIFIED** |

**Summary: 1 difference, 1 VERIFIED, 0 explained-unverified, 0 contradicted, 0 unexplained.**

## 3. Synthetic villa, V2.7.1 → V2.8 (with facts)

The two layouts are the base and its mirror.

| Differences | VERIFIED | Reading |
|---|---|---|
| 7 FIN.SKIRTING rooms per layout (−8.70 m in total) | **7 / 7** | P + hole perimeters − every gap: 2 rooms with free-standing columns (holes 1.6 and 3.2 m) and every room with symbol-less passages are checked. This also closes the D-P8-05 gap for skirting under unknown sills |

## 4. The Phase 2B-8 reference attribution (V2.6 → V2.7.1), re-run with the current verifier

**55 differences: 32 VERIFIED, 23 EXPLAINED_UNVERIFIED, 0 CONTRADICTED, 0 UNEXPLAINED.** This is unchanged; no
verdict was manufactured. The 23 break down as follows:

| Group | Count | Why not verified | What would verify them |
|---|---|---|---|
| wet-evidence differences in three adjacent ground-floor spaces whose checks need the zone-bounded space | 13 | NOT_CLOSED_BY_WALL_LINES: one space is closed by a drawn zone line on a non-wall layer. Read by its own handle and added, the reader's face is 3.832 m² against the engine's 4.731 m² (D-P9-04) | a cell-by-cell reconciliation of that space (likely a recess the reader's gap rule closes) |
| door-opening differences on faces with a symbol-less gap | 4 | GAP_WITHOUT_A_DOOR_OR_WINDOW_SYMBOL | an independent passage rule for plaster / paint / tile (D-P8-05) |
| door-opening differences on faces with a window | 2 | WINDOW_SILL_NOT_IN_THE_DRAWING | sills on the drawing (not available) |
| items with no independent check yet (WP upturn ×2, door count, threshold withheld) | 4 | NO_INDEPENDENT_CHECK / NO_MEASURED_VALUE_AFTER | an upturn-run and door-class reading |

The verified share did **not** rise on this transition. The new checks cover V2.8's own changes, where they verify
all 15 (1 reference + 7 + 7 villa). The non-wall-boundary priority was investigated to the point of a measurable
disagreement (D-P9-04). It was not forced to agree.

## 5. What the verification does not show

- **It does not show accuracy against a QS.** The reader shares the drawing, and conventions such as the 0.30 m band
  and the 0.05 m stub limit are stated, not independent.
- **It does not test the heights.** No real plan carries height evidence. The heights are proven only on synthetic
  hand truth.
