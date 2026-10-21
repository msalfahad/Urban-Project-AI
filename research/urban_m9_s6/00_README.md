# M9 S6: engine reliability and drawing intelligence, the pre-change review (generic notes)

This is a read-only review of HEAD `6eba0d2`. **No production code was changed.** The implementation plan waits for the owner's approval. These notes are generic: no drawing identity, no client figure, no benchmark value. The full findings package, including the client-derived counts, is delivered to the owner outside the repository.

## What was reproduced (synthetic fixtures from `tools/arch_synth.villa`, through the production CLI)

`S6_01_DEFECT_REPRODUCTIONS_PUBLIC.csv` lists 44 entries:
- 35 open defects: 2 critical, 11 high, 19 medium, 3 low; 30 of them silent (exit 0);
- 6 claims not reproduced;
- 3 confirmed fixed by S5.

The silent failure classes:
- **Wrong floor:** two plans in one sheet frame are split at the midpoint between their title anchors, so one plan's rooms are measured on the other floor (`arch_plan.plan_regions`).
- **Metre drawings:** two tolerances of 1.0 *drawing unit*, in `opening_census.band_gaps` (`_union(..., 1.0)`) and `drawing_model.closed_rectangles(eps=1.0)`, close every gap under 1 m. Doors and columns are lost and rooms merge. At mm both are 1 mm, so a unit-relative value is neutral on mm drawings.
- **Empty success:** paper-space frames, no frame, a frame drawn as lines, unrecognised title wording, a rotated drawing, an empty DXF, and an empty or stale DWG conversion. Same-named DWG inputs overwrite each other in `OUT/converted`.
- **Columns lost:** nested blocks, MINSERT, layer-0 block content, SOLID fills, exploded or rotated outlines, and plans with fewer than three columns.
- **Other inputs ignored:** frozen / off layers are read; unresolved XREFs are not flagged (the K2 finding is never surfaced); non-uniform door blocks become passages; Arabic diacritics unlabel a room word.
- **Structural defaults:** V3 / V5 by entry point, so the M8 scope pass needs V6 and is off by default.
- **Finishes with no line and no RFI:** paint above partial-height wet tile; stair-room walls and skirting; door / passage thresholds; window reveals counted as internal floor. Also, `wall_height.derive` subtracts non-required components.

## Files

| File | What |
|---|---|
| `S6_01_DEFECT_REPRODUCTIONS_PUBLIC.csv` | the defect register (fixture, command, expected, observed, code path, severity, silent, result) |
| `S6_02_DRAWING_DISCOVERY_SCHEMA.json` | `URBAN_DRAWING_DISCOVERY_V1` (JSON Schema 2020-12): stages 0–10 with states and FATAL / BLOCKED_ITEM / REVIEW_REQUIRED / WARNING findings |
| `S6_02_SAMPLE_DISCOVERY_REPORT_SYNTHETIC_VILLA.json` | the prototype's report on the synthetic villa |
| `repro/s6_repro.py` | 31 synthetic cases → `S6_REPRO_RESULTS.json` (`python3 -I repro/s6_repro.py REPO WORK [case ...]`) |
| `repro/s6_repro_dwg.py` | the DWG admission cases; needs a fake `dwg2dxf` on PATH (`COPY` / `SILENT` / `GARBAGE` modes, see the script docstring); never a real converter |
| `repro/s6_repro_arch.py` | finish omissions and the diacritics case on the synthetic villa + `research/urban_m9_s2/SYNTHETIC_FACTS_S2.json` |
| `repro/discovery_prototype.py` | a read-only discovery report for one DXF, reusing `urban_intake`, `drawing_model`, `arch_plan`, `capability`, `level_marks` |
| `repro/floor_finish_census.py` | every floor category of a run → one disposition (FINISH_LINE / BOUNDED_OR_BLOCKED / NOT_APPLICABLE / UNACCOUNTED) |

## Results that do not depend on the private drawing

- **The prototype gate** catches 15 of the 16 failing synthetic fixtures before any quantity (10 stop, 5 flag); both controls pass. The metre drawing is the one admission cannot see; only the tolerance fix and a units metamorphic test protect it.
- **The floor census** on the synthetic villa: the face partition closes exactly. Only the doorway strips are UNACCOUNTED (GF 1.40 m², 1F 1.02 m²), and part of them are window reveals (0.68 / 0.48 m²).
- **Python 3.13 vs 3.11:** 9 of 13 output files differ in bytes; all values agree within 1e-9 (the 3.12 `sum()` change).

## The proposal (awaiting approval)

The changes go behind an opt-in `ARCH_TAKEOFF_V2`. Shared helpers get keyword parameters that default to today's behaviour, so `ARCH_TAKEOFF_V1` and route G stay byte-identical by construction (to be proven by hashes and the full suite).

- **Phase 1:** the admission gate with exit 2; DWG admission fixes; units declared or blocked; unit-relative tolerances; the region split by wall networks; the floor-category gate with threshold RFI lines.
- **Phase 2:** the reader and finish fixes.
- **Phase 3:** paper-space viewports and the blind-villa round.

Owner rules are unchanged, and no construction detail is assumed.
