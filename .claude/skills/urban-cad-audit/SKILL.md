---
name: urban-cad-audit
description: Audit an architectural DXF/DWG plan for takeoff readiness before trusting Urban BOQ quantities - units, plan frames, layer roles (including single-instance door/column/window layers), door blocks read as passages, mirrored blocks, attached open-passage areas. Read-only on the drawing.
---

# Urban CAD audit

## Purpose
Find what in a drawing will make the engine's room, opening or finish quantities wrong *before* a BOQ is used: the
discovery gate, units, plan frames, layer roles, door symbols, attachments. The audit produces findings, never fixes
the drawing.

## Trigger
A new drawing set arrives; a BOQ line looks wrong; rooms, doors or windows are missing or typed PASSAGE; a column is
not deducted; an area seems to include a lobby or corridor.

## Inputs
- the plan DXF (or a DWG converted by the project's converter), kept in the private work area
- optional: declared layer roles (`LAYER=ROLE`), project facts (heights), project rules sheet

## Tools
1. Run the engine read-only into a private output folder:
   `python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.5`
2. Read `OUT/DRAWING_DISCOVERY.json` (gates, units, frames), `OUT/RUN_RULES.json` (`layer_roles_override`, policies),
   `OUT/ARCH_ROOMS.json` (rooms, `attached_cells`), `OUT/ARCH_OPENINGS.json` (kind, evidence, jambs),
   `OUT/DOOR_SCHEDULE.csv` (provisional doors).
3. Check, and record each as a finding:
   - layer roles: a layer holding a single door, window or column is not recognised (doors need two anchored swings,
     columns three filled squares - `engine/source/arch_plan.py` `layer_roles`). If so, re-run with
     `--layer-roles A-DOOR=DOOR A-COL=COLUMN ...` (recorded in RUN_RULES) and compare.
   - door blocks vs openings: a door block near a PASSAGE is one of three things (Phase 2B-5 D-C1): its leaf closes
     its own wall-to-wall doorway nearby (a separate, PROVISIONAL door - correct); its leaf closes a gap inside the
     passage's own gap (one opening drawn two ways - ARCH_TAKEOFF_V2.6 reconciles it as a held DOOR); or it closes
     nothing and stands off the opening (V2.6: a held DOOR within the review limits, else a note). Compare with
     DOOR_SCHEDULE rows that are PROVISIONAL_NOT_RELEASED and with `door_fit_review` / `door_symbol_note` in
     ARCH_OPENINGS (V2.6).
   - curved walls (D-D2): a room whose `area_m2` differs from its `polygon_m` area has an arc boundary; its polygon,
     `rect` and the polygon-based layouts (membrane, tiles) are on the chord, and a curved wall band is missing from
     the wall run - check `ARCH_WALLS.json` against the drawn arcs of the wall layers.
   - external references: an XREF that is not supplied blocks the run (`ADMISSION_BLOCKED.json`,
     XREF_NOT_SUPPLIED); accepting it (`--accept-missing-xref`) is an owner decision, never a default.
   - attachments: rooms with `attached_cells` (flagged ATTACHED_THROUGH_OPEN_PASSAGE) and single cells that join a
     doorless lobby to a wet room without a flag (D-C3).
   - an independent cross-check of a few rooms with the reference reader: `tests/m9_p2b5_bench/ref_reader.py`
     (ezdxf + shapely; set the plan's wall / door / glazing / text layers).
4. Write the findings (aggregate, no room ids or client data) to the project's private findings file.

## Safety
- Never write to, save or "repair" the source drawing; never run LISP or other mutating CAD commands on it.
- Private drawings, room ids, client names and coordinates stay in the private work area; only aggregates go into
  shareable documents (scan them with the project's privacy scan before committing).
- Never upload a drawing to a third-party service or an MCP server without the owner's written authorisation.

## Outputs
A findings list: finding id, evidence (file + field), class (ENGINE DEFECT / DRAWING ISSUE / RULE CONFLICT / INPUT),
BOQ impact (relative), and the next action (declare a role, raise an RFI, open an opt-in method change).

## Tests
`tests/m9_p2b5_bench/test_bench.py::test_the_engine_with_inferred_layer_roles` (single-instance layers),
`::test_openings_of_the_exact_dxf_readers` (declared roles), `::test_the_cad_encodings` (blocks, units, XREF),
`tests/m9_p2b5/test_p2b5_door_reconcile.py` (D-C1), `tests/m9_p2b5/test_p2b5_curved_wall.py` (D-D2),
`tests/m9_p2b5/test_p2b5_cli.py`.

## Escalation
Ask the owner only for genuine decisions: a layer whose role cannot be inferred or declared from the drawing's own
evidence, an attached area whose finish scope is a scope question, a drawing that fails the discovery gate.
