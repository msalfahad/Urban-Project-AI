# Research log (Research scout writes; newest first)

Each entry: date, what it is (link), licence, what it could improve in the engine or the workflow, risk, verdict
(ADOPT idea / TRY in sandbox / WATCH / REJECT). Never install or run downloaded code from here; the lead decides.

## 2026-10-17: BOQ engines study (owner-supplied; verdicts PROPOSED, scout to confirm)

Full study, with file evidence: [research/2026-10-17_BOQ_ENGINES_STUDY.md](research/2026-10-17_BOQ_ENGINES_STUDY.md)

| Date | What (link) | Licence | Could improve | Risk | Verdict (proposed) |
|---|---|---|---|---|---|
| 2026-10-17 | [OpenConstructionERP](https://github.com/datadrivenconstruction/OpenConstructionERP): recipes (assemblies) with per-unit factors and formulas, waste factors, explainable cost matching, revision change flags, contract quantity baseline | AGPL-3.0 | Recipe layer for blockwork, plaster and tiles; three-quantity lines; revision flags | AGPL: copying code would force publishing ours. Its Middle East pack has no Kuwait rules | ADOPT idea |
| 2026-10-17 | [OpenTakeoff](https://github.com/Kentucky-ai/opentakeoff): role-based shapes, order of xN then waste then rounding, skirting from perimeter minus stated openings, overlap check (sum - union = 0), review stamps | AGPL-3.0 | Deduction and skirting traceability, double-count check, withheld-item list | AGPL; it works in feet and covers US interior finishes only | ADOPT idea |
| 2026-10-17 | [CostX](https://www.rib-software.com/en/blogs/rib-costx-functions): dimension groups feeding workbook functions, composite rates, auto-revisioning | Commercial | Wall-area-by-group-height; revision re-match with review warnings | Closed; public docs only | WATCH |
| 2026-10-17 | [PlanSwift](https://constructconnect-help.atlassian.net/wiki/spaces/PSUPPORT/pages/48431425/Useful+Formulas+for+PlanSwift): parent/child formula tree, openings as children of the wall | Commercial | Openings modelled as children of their host wall | Closed; public docs only | ADOPT idea |
| 2026-10-17 | [Togal.AI](https://help.togal.ai/en/articles/15602901-ai-powered-area-and-wall-detection): net, gross, footprint, centreline and door widths per room at once | Commercial | Store several quantity variants per room or wall | Closed; public docs only | ADOPT idea |
| 2026-10-17 | [Bluebeam](https://support.bluebeam.com/revu/how-to/tips-and-tricks/improve-takeoffs-with-quantity-link.html), Cubit, PriMus, [Autodesk Takeoff](https://help.autodesk.com/cloudhelp/ENU/Takeoff-Takeoff/files/Symbol_Detect.html): filter-linked quantities, measurement rows with negative openings, pending-until-accepted detection | Commercial | Measurement-row audit format; pending state for detections | Closed; public docs only; some internals uncertain | WATCH |
