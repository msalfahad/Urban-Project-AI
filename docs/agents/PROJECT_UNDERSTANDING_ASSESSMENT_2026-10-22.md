# Project understanding & engineering review: read-only assessment (main chat, 2026-10-22)

Status: ASSESSMENT ONLY. The owner asked for a read-only discovery; nothing below is approved for implementation, no task,
agent or prompt was created from it. Full answer given in the owner's main chat on 2026-10-22; this file keeps the record and
collects the evidence that later findings add (section 4).

## 1. Today (evidence on claude/access-permissions-setup-ii24ws)

- No project-level entry point: tools/urban_boq_m9.py runs a takeoff method on one architectural + one structural DXF, with
  the admission gate (engine/source/discovery.py). Other sources are read by agents task by task.
- Formats: DXF deep (ezdxf); DWG via external converter (tools/dwg_adapter.py); vector PDF for specific pieces only
  (opening_height_pdf.py, tools/align_sanitary.py, not wired); DWF vector-presence audit only (tools/audit_dwf_source.py);
  scans only after proved scale (raster_evidence.py), OCR never promoted (ocr_review.py); images: agent review, no module.
- Pieces that exist: drawing_inventory.py (one DXF), tools/audit_submission_set.py (per-page readability of a set),
  section_binding.py / level_marks.py / elevation_binding.py (levels; not wired), stair_fit_checks.py (headroom; not called
  project-wide), element_register_v0.py (reads finished run outputs only), trade_dependency.py, structural_census.py.
- Missing: whole-project document and revision register; one issue register linked to BOQ lines (today: DESIGNER_CLARIFICATIONS
  57 items, OWNER_QUESTIONS, research defect registers, discovery report); level chain FFL -> slab -> footing (T-170 queued);
  ramp, drainage-completeness and regulatory checks (none; no verified Kuwait source in the repository).
- Coverage registry BOQ_FAMILY_MASTER 1.1.0: 99 families, 0 INTEGRATED_AND_TESTED, 47 PARTIAL, 18 NOT_IMPLEMENTED,
  17 BLOCKED_BY_SOURCE, 13 IMPLEMENTED_NOT_INTEGRATED, 4 EXPERIMENTAL.

## 2. Proposal (not approved)

Option B: the Lead owns the project model and the issue register (extension of the element register it already owns); Worker 3
builds the document register, issue register, issue -> BOQ-line holds and the check library; Workers 1 / 2 run discipline checks
as tasks; the Checker verifies findings like quantities; the Scout builds the Kuwait residential source library; the main chat
audits. Phases: (1) document / revision register + issue register + holds wired into the V3.0 export; (2) level chain, per-element
levels, column -> support trace, stair headroom, excavation depth; (3) ramps, openings across plan / elevation / schedule,
drainage completeness, photo findings; (4) regulation library and checks; (5) report pack. Recommendation: phases 1-2 in parallel
with V3.0 before 3 Nov; 3-5 after.

## 3. Open owner questions from the assessment (not answered)

Official residential regulation PDFs on Drive; permit set and plot data per project; RFI recipient and language; DWF / scan
reader effort vs an intake requirement.

## 4. Evidence from the scoreboard (owner review 2026-10-22: findings feed this assessment)

| Date | Finding | What it says about project understanding |
|---|---|---|
| 2026-10-22 | SCOREBOARD v2: verified share 0 / 8 concrete reference lines (released and V3.0.3), 0 / 1 for floor, plaster, paint | No reference line yet has an independent drawing quantity: accuracy is NOT YET MEASURED; T-180 reconciles the 8 concrete lines |
| 2026-10-22 | Concrete compared 3 / 8: footing + straps 77.27 vs 77.63, stair / dome 12.01 vs 21.83, pool 3.50 vs 12.35 m3 | The two large gaps are elements that need cross-drawing understanding (stair / dome geometry from sections, pool walls and floor from plan + section + detail); T-180 names the cause per line |
| 2026-10-22 | Doors / windows not comparable: engine pcs, freelancer m2 | A classification and unit coordination gap between the opening census, the elevations and the BOQ; T-181 |
| 2026-10-22 | Released and profiled runs both called "released" until T-165 | Revision / configuration control was missing at run level, the same gap the document register addresses at drawing level |
| 2026-10-22 | Pool concrete (Checker T-180, own 7.084 m3 from the drawing): engine 3.495 = -3.589 m3, freelancer 12.348 = +5.264 m3 | Two drawing-interpretation gaps in the engine: it read only the straight wall strip (6.20 m) and missed the curved half of the pool ring (ring centreline 11.784 m), and it used conventions (floor 0.25 m, wall 1.60 m, floor plan 6.045 m2) instead of the printed structural detail (0.40 m) and the architectural levels (rim +0.30, floor -0.85: 1.15 m; floor plan 10.935 m2): architecture and structure were never read together. The freelancer side is scope, not measurement: a pump room (3.480 m3) that no drawing shows, a 1.80 m wall height, steps 0.228 |

Rows are added when T-180 / T-181 / T-182 or other verdicts show that a quantity difference comes from drawing interpretation or
missing cross-discipline coordination.
