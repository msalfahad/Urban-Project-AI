# Discovery schema `URBAN_DRAWING_DISCOVERY_V1`

The full JSON schema is `discovery/S6_02_DRAWING_DISCOVERY_SCHEMA.json` (committed at `6b7a2e4`). The implementation is `source_changed/engine/source/discovery.py`.

## Stages

| Stage | Admission? | What it decides |
|---|---|---|
| 0_intake | yes | readable file; DWG conversion; `--structural` needs `--conventions`; plan ≠ structural drawing |
| 1_inventory | yes | entity census per layout; nesting depth; MINSERT; XREFs; hidden layers; kinds not measured; K2 disposition of every top-level entity |
| 2_sheets | yes | sheet frames (polylines or lines); paper-space sheets; titles inside frames |
| 3_identity | yes | drawing identity, title block, revision (**NOT_RUN**) |
| 4_units | yes | declared vs inferred unit; reviewer `--units`; V1 strict: a unit too coarse for 1-unit tolerances |
| 5_floors | yes | plan regions (EMPTY_BANDS split, frames from lines), cuts through geometry, reviewer `--region` |
| 6_geometry_readiness | no | K2 degenerate / unhandled; column evidence; fills unread; distorted door symbols |
| 7_vertical_model | no | levels, sections (`NO_SECTION_SOURCE`) |
| 8_features | no | feature census (**NOT_RUN**) |
| 9_finish_zones | no | finish zones, coverage |
| 10_boq_readiness | no | the summary of what may be released |

## Levels and the gate

- **FATAL** anywhere → stop: exit 2, no BOQ.
- **BLOCKED_ITEM** in stages 0–5 → stop (exit 2). In stages 6–10 it blocks only the items it names.
- **REVIEW_REQUIRED** and **WARNING** travel with the BOQ as flags.
- Completeness (stage 9 coverage) failing → exit 3. Nothing is published; `diagnostics/` holds the computed lines.
- Reviewer inputs (`--units`, `--region`, `--accept-missing-xref`) are recorded in `reviewer_inputs`, never silently applied.

## Finding

```json
{"level": "BLOCKED_ITEM", "code": "UNITS_NOT_DECLARED", "message": "...", "evidence": {...}, "remedy": "..."}
```

## Examples

The examples are in `discovery/`:
- `S6P1_04_DISCOVERY_SYNTHETIC_VILLA_V2.json`: the synthetic villa, admitted;
- `S6P1_04_DISCOVERY_BLOCKED_EXAMPLE_UNITS.json` with `S6P1_04_ADMISSION_BLOCKED_EXAMPLE_UNITS.json`: a units stop;
- `S6P1_04_DISCOVERY_FLAGGED_EXAMPLE_NESTED.json`: nested plan fills flagged;
- `S6_02_SAMPLE_DISCOVERY_REPORT_SYNTHETIC_VILLA.json`: the pre-change prototype.

The reference plan's report is in the PRIVATE package.

## Review findings on the schema (see files 07 and 08)

- **Stage 1 counts entities but does not conserve them** (NSD-1). DIMENSION (388 on the reference plan) and undecoded SHX texts (51) are not first-class records.
- **No post-measurement stage** for element conservation (NSD-2) or independent totals (NSD-8). Proposed: a stage `11_reconciliation`.
- **No `readiness` field** for automation (Investigation E.5).
