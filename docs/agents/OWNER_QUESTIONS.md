# Questions for the owner (at most 5 open; answer under "Answer:")

Lead 2026-10-18 20:05 (owner session): Q-06, Q-07, Q-09 answered by the owner (see Answered); no question open. Lead 2026-10-18 21:25: Q-10 (development project 2 DWG) answered; Q-11 answered (owner uploads the Alsenan DXFs); no question open. Lead 2026-10-18 15:40: no new question; Q-06 and Q-07 still open (no owner answer yet). The T-019 wall-length basis finding is settled by UP-WALL-GEOM-001 (masonry run = centreline, owner-approved), so it became task T-027, not a question. Lead adds questions an agent cannot decide from drawings, rules or evidence. Answered questions move to the bottom.
Decisions still queued behind these (from the master study `14_OWNER_DECISIONS_QUEUE.csv`): D-17 review-space wet / dry,
WP-KITCHEN membrane scope, WP-JOINT details, WIN-REVEAL finish, STUB-LIMIT, MEAS-STD, ROOF-FIN, BLIND-AUTH.

## Open

## Answered

### Q-11 AutoCAD DXF files for the scoreboard (T-001b; added by the worker 2026-10-18 as Q-10, renumbered by the lead)
The Drive folder "Alsenan chalet project" has the DWGs but not the two DXF files the engine was always run on, and P7757.dwg cannot be
converted here: please (a) upload your existing AutoCAD exports P7757.dxf (about 17 MB) and ST7757.dxf (about 3 MB) to that folder,
(b) re-export both from AutoCAD (SAVEAS DXF 2018) and upload them, or (c) let agents score only the structural trades from a
LibreDWG conversion of ST7757.dwg (13 of 4473 entities lost) and leave the architectural rows unmeasured? Blocks T-001b (the first
real scoreboard). Lead: the same applies to development project 2 (its DWG has not been converted yet), so the DXF exports of its architectural DWG (and of the plans file its PDF title block names, if different) would avoid the same block there.
Answer (owner, 2026-10-18): (a) for Alsenan: the owner uploads the Alsenan DXF exports to the Drive folder "Alsenan chalet project". Development project 2: no DXF promised yet; a worker first tries its DWG with the pinned LibreDWG plus a read-only CAD audit, and the lead asks again only if that conversion is lossy.


### Q-10 CAD file for development project 2, the finishing-only apartment (added 2026-10-18)
Its architectural plan is only a PDF with no readable text (probably a scan): (a) you have the DWG / DXF and will add
it to the same Drive folder, or (b) there is none, so the agents read the PDF with the plan reader (T-003) and score
finishes from that. Blocks using the apartment for CAD-measured finishes (M2 / M3); (b) moves T-003 earlier.
Answer (owner, 2026-10-18): (a). The DWG is in the same Drive folder (file name ends in -STR.dwg). The first agent that opens it confirms with a read-only CAD audit (urban-cad-audit skill) that it holds the architectural floor plans; if it holds only structure, the lead re-asks.


### Q-09 Measurement basis for every BOQ line (MEAS-STD; added 2026-10-18)
Should the engine's quantities be (a) net geometric quantities from the drawing, with waste and rounding shown in a
separate column, (b) quantities with waste already included as the freelancer does, or (c) all three side by side
(measured, with waste, order quantity)? Blocks how the verifier classes freelancer differences (RULE_DIFFERENCE vs
FREELANCER_RIGHT) on every trade, from M2 onward.
Answer (owner, 2026-10-18): (c). Every BOQ line shows the measured quantity, waste in its own column, and the total (measured + waste). Task T-032.


### Q-06 Hand-wash spaces: wet or dry? (D-17; added 2026-10-18)
The three basin-only hand-wash spaces on Alsenan (9.35 m2 in all; the drawing does not establish their type) are:
(a) wet: porcelain floor, full-height wall porcelain, waterproofing, marble threshold; (b) dry: plaster, paint, skirting,
ordinary floor porcelain; or (c) answer per space. Blocks their floor, wall and waterproofing lines (Gate 1, wet vs dry).
Answer (owner, 2026-10-18): (a) wet. Basin-only hand-wash spaces are wet areas: porcelain floor, full-height wall porcelain, waterproofing, marble threshold. Task T-030.


### Q-07 Facade height convention (OQ-08 in research/urban_m9_n10/OWNER_DECISIONS_REGISTER.md; added 2026-10-18)
Is each floor's facade measured (a) F.F.L. to the next F.F.L. (engine default today), (b) slab top to slab top, or
(c) a stated height per floor? Blocks the external facade plaster / paint area (Gate 2, after section binding T-013).
Answer (owner, 2026-10-18): (b) slab top to slab top. Task T-031 (after T-013 section binding).


### Q-08 Other villas for the engine (T-012; answered 2026-10-18)
To make the engine right on every villa, the agents need 2-3 more villas (AutoCAD DWG/DXF + PDF). Where can they get
them: (a) you create the private repository msalfahad/urban-boq-private-data and upload them under dev_villas/<name>/
(agents can read it; it never goes into the public repo), (b) a Google Drive folder you name, or (c) not now (synthetic
villas only, T-019)? Blocks T-012, T-001b and every real-plan check beyond Alsenan.
Answer: (a). The owner created the private repository msalfahad/urban-boq-private-data and uploaded files to it so that every
agent reads them directly; all four agent prompts (lead, worker, verifier, scout) now attach it read-only next to
Urban-Project-AI (2026-10-18). Folder layout as the owner uploaded it; the lead lists it on its next run and moves T-001b
(and any other BLOCKED-DATA task whose files are there) to TODO.

### Q-01 Plan reader: may Claude look at the drawings? (answered 2026-10-18)
Answer: Yes, always. The visual layer of PLAN_READER.md is on for every project drawing.

### Q-02 Working accuracy targets (answered 2026-10-18)
Answer: The main target is to get everything correct. 95 %+ against the freelancer is a floor, not the goal: the engine
may become more accurate than the freelancer. So a difference from the freelancer is not automatically an engine error;
the verifier decides from the drawing who is right (MISSION.md "Who is right").

### Q-03 Waterproofing upturn (answered 2026-10-18)
Answer: 0.20 m. Already the current rule (knowledge 1.4.0 rules[41], UP-WP-003; 0.15 m is superseded, rules[47]). No change.

### Q-04 Door minimum, D-16 (answered 2026-10-18)
Answer: The minimum is the door opening: ordinary 1.00 m opening = 1.10 m wall to wall. These are minimums: when the plan
is drawn wider, the drawn size is used. The main door is measured as drawn. Matches the registry 1.1.0 reading
"wall opening = nominal + 0.10 m" (owner_questions[4], rules[13]); by the same rule a bathroom 0.90 m opening = 1.00 m
wall to wall (owner confirmed 2026-10-18, also "unless the measurements say more": drawn size when wider). Recorded
as a new knowledge version (task T-011).

### Q-05 Second villa and independent QS (answered 2026-10-18)
Answer: Yes. Other villas exist as AutoCAD and PDF, but without full concrete and rebar drawings. Use them as development
villas for architectural trades, the plan reader and silent-omission checks (Gates 1, 2, 4); not for concrete / rebar,
and not as blind proof until an independent QS measures one (task T-012).
