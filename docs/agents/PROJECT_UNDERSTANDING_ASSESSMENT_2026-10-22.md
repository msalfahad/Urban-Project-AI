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

## 5. Owner lesson recorded 2026-10-22 (pool)

The engine used defaults and incomplete geometry although the information was present across the architectural and structural drawings. Prevention: the default guard (T-186) is the first concrete piece of the project-understanding engine (phase 2: cross-drawing reconciliation before measurement). Its regression tests cover curved pool walls, printed thickness ignored, partial footprints, a missed staircase, a dropped upper flight, double-counted landings / pool junctions, and a client request treated as an approved revision.

## 6. Residential engineering-review plan (owner approval 2026-10-22 15:00: continue in parallel, V3.0 not delayed; Kuwait specification PDFs deferred)

Order by what prevents a wrong BOQ: (1) missing elements, (2) wrong defaults, (3) incomplete geometry, (4) cross-drawing
inconsistency. Each check is a pure, unwired module with a non-Alsenan fixture, run as a lane S / A task in its own run;
its findings are HELD lines and issue rows, never quantities. None waits on a specification PDF.

| # | Check | Prevents | Sources it needs (all present for Alsenan) | Evidence so far | Next task size |
|---|---|---|---|---|---|
| R1 | Default guard: no convention value where any project document prints one (T-186) | wrong defaults | every sheet's printed dimensions, levels, schedule values | pool 0.25 / 1.60 conventions vs printed 0.40 / 1.20 (T-183) | READY, wiring after T-167 |
| R2 | Element inventory across disciplines: every architectural element (stair, pool, tank, dome, lift, ramp, parapet) has a structural counterpart and a BOQ owner, and the reverse | missing elements | ARCH plans + sections, ST plans + details, element register (T-134) | 1F->2F flights folded away (D-T184-1, -2.598 m3); pump room in freelancer but on no drawing | one run: register cross-join + report |
| R3 | Storey continuity: an element that spans floors (stair, lift, shaft, void, column) appears on every storey it crosses | missing elements, incomplete geometry | per-storey plans, section A-A / B-B | ST-01 ends at 2F, ST-02 at 1F (T-184) | one run |
| R4 | Curved / partial geometry completeness: plan area and length of an element equal its outline (arcs included), never a straight strip | incomplete geometry | DXF arcs and polylines, structural outlines | pool ring curved half missed (11.784 m centreline) | one run per element family |
| R5 | Level chain: FFL -> structural top -> soffit -> footing, each level a named physical datum | incorrect heights, depths | level marks, sections, structural notes (T-170 queued) | pool wall 1.15 finished vs 1.20 structural (T-183 r2) | two runs |
| R6 | Opening consistency: plan opening = elevation opening = schedule row (width, sill, head, type) | inconsistency, deduction errors | plans, elevations, door / window schedule if issued | 20 windows print no head (T-144); Q-73 deductions (T-175) | one run |
| R7 | Scope vs drawings: every BOQ / freelancer line maps to a drawn element, and every drawn element to a line | missing and invented scope | BOQ lines, element register, freelancer rows | freelancer pump room 3.480 m3 and pool steps 0.228 not drawn | one run |
| R8 | Client change vs approved design: a client request is a scenario (S1), never a revision until the consultant issues one | wrong scope released | owner notes, revision register | domes S0 / S1 / S2 (Q-29) | in place (scenario rule) |
| R9 | Document / revision register: every sheet with title, number, revision, date, discipline; the BOQ cites the revision it used | stale-drawing errors | Drive file list and title blocks | not built | one run (phase 1) |

Project-specific information that will eventually be required (asked of the owner only when a project needs it and no
drawing or rule settles it; nothing below blocks current work):

1. Per project: the issued drawing set with revision letters and dates (architectural, structural, MEP, sanitary), and
   which revision is "for construction".
2. Door / window schedule, or confirmation that none was issued (otherwise heights stay ASSUMED / HELD).
3. Finishes schedule or specification sheet (floor, wall, ceiling, exterior finishes; waterproofing system).
4. Soil report / founding depth, where the drawings do not print it (Q-21 C for Alsenan: founding depth HELD).
5. Plot data: plot area, setbacks, ground level relative to the road and the datum of +0.00 (for excavation and
   external works).
6. Client requests not yet issued as consultant revisions (scenario S1 list), with the date of each.
7. Special elements' supplier data where the drawings defer to it: pool equipment and pump room, lift pit, water tanks,
   skylights replacing domes.
8. Later (deferred by the owner): Kuwait residential regulation and specification PDFs, for phase 4 checks.
