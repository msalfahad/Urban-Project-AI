# Current engine capability (architectural route, after Phase 2B-5)

The states used below:

| state | meaning |
|---|---|
| VERIFIED | checked against independent truth (hand-derived synthetic truth, or the Stage C independent reading of real rooms) |
| WORKS / LIMITED | behaves as designed, with the stated limits |
| OPEN | a known defect |

| capability | state | evidence | limits |
|---|---|---|---|
| DXF intake: units, plan frames, layer roles, blocks (nested, mirrored, non-uniform), polylines, arcs / bulges, Arabic text, DIMENSIONs | VERIFIED (synthetic) | benchmark C01 - C05, B02, B06, B09, B10 | layer roles inferred from a count (D-D1): declare roles for single-instance layers |
| missing XREF, no unit, unread entities | WORKS (refuses) | C06: BLOCKED XREF_NOT_SUPPLIED, no BOQ published | accepting a missing XREF is an owner act |
| room polygons, straight walls (rectangle, L, splay, column holes, adjacent rooms, rotation, mirroring) | VERIFIED | benchmark exact (IoU 1.0); Stage C: floor, ceiling and perimeter exact in all 5 real rooms incl. a splayed W.C. and two attached areas | - |
| arc-walled rooms | LIMITED | B10: area and boundary exact | polygon / rect on the chord; layouts and wall run inherit it (D-D2) |
| openings: doors, windows, passages | VERIFIED (synthetic, declared roles) / WORKS (real) | benchmark exact; Stage C windows exact | a door drawn two ways at one opening is reconciled only in V2.6 and held (D-V26-06); its width still follows the wall gap, not its symbol (roadmap 1) |
| door BOQ: classes (PVC, aluminium, main entrance, lift excluded), states, held doors, feasibility (owner nominal + 0.10 m) | WORKS | V2.3 - V2.5 door examples; Stage C | heights are inputs |
| floor, ceiling, waterproofing floor quantities | VERIFIED | exact in every synthetic case and the 5 real rooms | - |
| wall-area quantities (plaster, wall porcelain, paint, masonry) | LIMITED | formula and openings verified in Stage C | rest on heights: synthetic in tests, project values needed (D-C5) |
| skirting | WORKS | Stage C | rule conflict in wet rooms with part-height tile (D-C4) |
| waterproofing net / installed / procurement (V2.4 - V2.5) and the construction layer (V2.6): piece plan, offcuts, joints, seams, corners, penetrations, junction alternatives | VERIFIED (synthetic, 297 checks) / PROVISIONAL (procurement) | 10 worked examples; 17 real areas computed | the floor-to-wall junction is open (owner decision); layout on the chord for arc rooms |
| doorway thresholds (marble, wet doorways) and doorway waterproofing pieces | WORKS (V2.6) / LIMITED (V2.5) | Stage C thresholds 4 of 5 in V2.6 (2 of 5 in V2.5); D-V26-07 boxes confirmed by a raw jamb reading | a face running past a jamb drawn only with the door symbol is split in V2.6 only (D-V26-07); thresholds of leaf-closed doors stay withheld (roadmap 5) |
| traceability: rule id, formula, inputs, evidence state per line; run rules; rules sheet; drawing hash; byte-identical frozen methods | WORKS | freeze verifier; 968 files byte-identical V1 - V2.5 | - |
| vision (raster / scan / vector PDF) | RESEARCH ONLY | benchmark | never a BOQ basis |
| accuracy on unseen villas | NOT MEASURED | - | the formal blind evaluation has not started |
