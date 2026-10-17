# Owner / project rule sheet (registry 1.4.0)

Every rule below is an **Urban Projects owner standard or method**, recorded with its source and date in
`knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json`.

- **None is presented as Kuwait building-code compliance.** No code source has been verified for any of them.
- Rules already recorded are **not asked again**.
- "Project override" means a project-specific rule (level B, UP-RULES-001). It replaces the owner standard only
  within its stated scope and is listed on that project's PROJECT_RULES_SHEET.

## Heights and openings (new or amended in 1.4.0)

| Rule | Standard | Status | How the engine applies it |
|---|---|---|---|
| UP-HGT-001 | heights come from the drawing by the evidence hierarchy (annotation > schedule > section / elevation > derived > floor note > project note > project facts > Urban default); plaster to the soffit, paint / tile to the finished ceiling; floor-to-floor never a wall height | engineering method (Phase 2B-9) | ARCH_TAKEOFF_V2.8; every height carries source, value, unit, scope, rank |
| UP-DOOR-HGT-001 (amended) | door height: the door's own evidence first; owner reference **2.20 m** ordinary doors, **2.50 m** main entrance as **labelled fallbacks** (HEIGHT_ASSUMED) | owner approved | the fallback is used only when no annotation, schedule, section or project fact exists, and is never shown as measured |
| UP-OPEN-SCHED-001 | the opening schedule: width (checked against the schedule), height, sill, head, class; each opening deducted by its own band; floor glazing not skirted; unknown sill a range; no height → width released, area held | engineering method | ARCH_TAKEOFF_V2.8 |
| UP-REVEAL-001 / UP-REF-REVEAL-001 (amended) | reveal depth = measured distance from the wall face to the glazing; jambs and head plastered by default (owner method); the sill surface is its own item; the floor-glazing strip is floor | owner method (reference only) + engineering method | PROVISIONAL lines: the frame detail can change the finish |
| UP-WALL-GEOM-001 | wall geometry per face; short returns and curved stubs (0.05–0.30 m) are wall; inner / centreline / outer arcs kept apart | engineering method | ARCH_TAKEOFF_V2.8 |
| UP-SKIRT-001 (amended) | conventional skirting on eligible dry-room boundaries; sill windows skirted under the sill, floor glazing never, unknown sill a range | owner approved | V2.8 edge by edge against F-17 |

## Doors (unchanged; recorded)

| Rule | Standard | Status |
|---|---|---|
| UP-DOOR-OPEN-003 | owner **minimum** openings: ordinary **1.00 m**, bathroom **0.90 m**, kept apart from every measured and derived width | owner approved |
| UP-DOOR-OPEN-002 | a universal +0.10 m wall-opening allowance | **requires confirmation**: not applied (no universal allowance) |
| UP-DOOR-AREA-001 | as-drawn and owner-required door areas kept separate, confirmed and assumed never mixed | owner approved |
| UP-DOOR-FEAS-001 | feasibility check: does the owner-standard door fit; can the opening be enlarged (reported for review, never auto-released) | owner approved |
| UP-DOOR-CLS-001 / -002 / -003 | internal doors PVC; doors to genuine outdoor spaces **aluminium**; bathroom doors PVC with the bathroom opening standard | owner approved |
| UP-DOOR-CLS-004 | the main entrance is its own category, measured as drawn | owner approved |
| UP-DOOR-CLS-005, UP-ELEV-SCHED-001 | lift entrances are not ordinary doors: they go in the separate **elevator schedule** | owner approved |

## Wet areas and waterproofing (unchanged; recorded)

| Rule | Standard | Status |
|---|---|---|
| UP-WET-001 | owner wet areas include bathrooms / W.C., **kitchens, pantries and iron / laundry rooms** (the finish scope of each) | owner approved |
| UP-FIN-WALL-001 | full-height wall porcelain in wet areas (to the finished ceiling) | owner approved |
| UP-CER-004 | **no skirting** where the wall porcelain is full height | owner approved |
| UP-FIN-PAINT-001 | no paint over full-height porcelain | owner approved |
| UP-WP-001 / -002 / -003 | membrane roll **1.00 × 10.00 m**; overlap **0.10 m**; upturn **0.20 m** | owner approved |
| UP-WP-004 | penetrations, corners and interruptions counted from the drawings, treated by the detail (never invented) | owner approved |
| UP-WP-DOOR-001 | doorway waterproofing transitions modelled on their own | owner approved |
| UP-THR-001 | wet-room doorways take a **marble threshold**; other doorways continue the floor porcelain | owner approved |
| UP-WP-ROOF-001 | roofs, balconies and terraces are waterproofed as **their own scope**, separate from the wet rooms | owner approved |

## Open owner decisions (not invented; listed in `DEFECT_AND_EVIDENCE_REGISTER.md`)

- **D-16:** apply the owner door minimum to the BOQ quantity.
- **D-17:** the type of the three review spaces.
- **Kitchen membrane** scope.
- **Reveal finish** by window type: marble or plaster sill.
- **Junction / corner / penetration** details for waterproofing.
- **Wall stubs under 0.05 m:** artefact or masonry. V2.8 treats them as artefacts, a stated convention.
