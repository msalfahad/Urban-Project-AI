"""T-245: the development villa's ARCH_TAKEOFF_V3.0.16 inputs (URBAN_V3016_INPUTS_V1): ONE project id and ONE revision
set over the two drawing files the candidate is computed from. Values only from the drawings' own evidence, the Drive
copies (pinned by sha256) and owner decisions; no drawing content is copied here. Every file is named by its Drive
title (the board's convention); the sha256 values are those the Verifier read from Drive on 2026-10-25 04:15 and this
run re-read (T-245 report s.2).

Project id: the architectural route's id, under which every V3.0.x project input of this villa is already bound
(research/agents_t131/alsenan_v30_run.PID); the structural route's id is the name of the structural route's
known-drawing entry (tools/urban_structural_boq.py), the SAME file sha256 -> both are routes of this one project.
Evidence: the owner's project folder (one Drive subfolder per project, owner 2026-10-18) holds both files; both file
titles carry the same drawing number; merged ledgers measure one building on both sets (column outlines of the
two frames agree to 0.001 m, T-261 r2 hand-in). Revision: the structural set's issue is UNCONFIRMED (D-61, owner
2026-10-24 23:57 (4));
the architectural DXF prints no revision mark or issue date as model-space text (this run's search for REV / DATE /
ISSUE: none), so its revision is UNCONFIRMED too: never an invented revision, never "approved set".
"""

ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STR_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STR_ROUTE_ID = "ST7757 villa (structural set)"
D61 = ("D-61 issue-date conflict: ST p.1-7 dated May 06 2025, p.9-10 / 13-16 May 06 2026, p.11-12 no title block; "
       "owner 2026-10-24 23:57 (4)")


def inputs(project_id):
    return {"schema": "URBAN_V3016_INPUTS_V1",
            "project": {"project_id": project_id,
                        "evidence": "owner's Drive project folder holds both drawing files (one subfolder per project, "
                                    "owner 2026-10-18); both file titles carry the same drawing number; merged "
                                    "ledgers measure one building on both sets (T-261 r2: column outlines agree to 0.001 m)"},
            "documents": [
                {"discipline": "ARCHITECTURAL", "title": "P7757.dxf (P7757_DXF_COMPRESSED.zip)",
                 "sheet": "architectural DXF (all floors)", "revision": "NOT PRINTED IN THE DXF TEXT",
                 "revision_state": "UNCONFIRMED",
                 "reason": "no revision mark or issue date in the DXF model-space text (T-245 search: REV / DATE / "
                           "ISSUE, none); the PDF title blocks were not read for a revision",
                 "sha256": ARCH_SHA},
                {"discipline": "STRUCTURAL", "title": "ST7757 dxf.dxf", "sheet": "structural DXF (all sheets)",
                 "revision": "UNCONFIRMED", "revision_state": "UNCONFIRMED", "reason": D61, "sha256": STR_SHA}],
            "routes": [
                {"route_project_id": project_id, "documents": [ARCH_SHA],
                 "evidence": "architectural route (tools/urban_boq_m9.py arch --project): the plan file alone"},
                {"route_project_id": STR_ROUTE_ID, "documents": [STR_SHA],
                 "evidence": "structural route G (tools/urban_structural_boq.py known-drawing entry, matched by the "
                             "file sha256): the structural file alone"}]}
