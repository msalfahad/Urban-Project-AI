"""PA07I: independent validation protocol, and the SECOND_REGRESSION_SOURCE_REQUIRED record.

No PA / E1 result, no contractor workbook and no AI reader is truth.  Truth is a second villa the architecture never
saw, with manually verified dimensions, or a withheld hand-verification pack from the original sources sealed before
the run.  Tolerances are predeclared here and never changed after a comparison.  When no suitable source exists the
protocol is frozen unexecuted and the phase records exactly what to upload; nothing is fabricated.
"""

from __future__ import annotations

from pathlib import Path

TOLERANCES = {"STRAIGHT_DEVELOPED_LENGTH": {"ABS_MM": 10.0, "REL": 0.005, "RULE": "pass if |engine - truth| <= 10 mm or <= 0.5 %"},
              "CURVED_DEVELOPED_LENGTH": {"REL": 0.005, "RULE": "pass if |engine - truth| <= 0.5 % of the developed length"},
              "OPENING_WIDTH": {"ABS_MM": 10.0, "RULE": "pass if |engine - truth| <= 10 mm"},
              "ROLE_AND_CLASS": {"RULE": "exact match of band status (ACCEPTED / REJECTED / UNRESOLVED) and site class"},
              "SPACE_COUNT": {"RULE": "exact match of the number of planar faces that are spaces inside the pack's region"},
              "MATERIAL_PRESENT": {"RULE": "exact match of MATERIAL_PRESENT on every edge and chord of the pack"}}

TRUTH_PACK_FIELDS = ["SOURCE_PAGE", "LOCATOR (sheet, grid reference or detail bubble)", "ENDPOINTS_MM (both ends, from the original source; hand verified)", "CLASS (wall band / column / opening / passage / glazing / not material)",
                     "RADIUS_MM (curved elements)", "OPENING_SPAN_MM", "DEVELOPED_LENGTH_MM", "RELATIONSHIP (which band hosts the opening, which band meets which)", "VERIFIER", "VERIFIED_ON"]
DIVERSITY = ["rectangular room", "room with a door", "L-shaped room", "curved wall", "open-plan region", "column beside a wall"]


def protocol():
    return {"ARTIFACT": "PA07_INDEPENDENT_VALIDATION_PROTOCOL", "VERSION": "PA07-IV-1",
            "TRUTH_SOURCES_ALLOWED": ["A) a second villa never used to develop the architecture, with manually verified dimensions", "B) a withheld hand-verification pack from the original sources, sealed before the run"],
            "TRUTH_SOURCES_FORBIDDEN": ["any PA / E1 result", "the contractor workbook", "an AI reader as the only truth", "the engine's own previous output"],
            "PREFERRED": "SECOND_REGRESSION_VILLA", "MINIMUM_CASES": 5, "DIVERSITY": DIVERSITY, "TRUTH_PACK_FIELDS": TRUTH_PACK_FIELDS,
            "PACK_CONTENT_RULE": "the pack holds locators, endpoints, classes, spans, radii, developed lengths and relationships; never areas, never results",
            "TOLERANCES": TOLERANCES, "TOLERANCES_FROZEN_BEFORE_COMPARISON": True, "TOLERANCE_CHANGE_AFTER_COMPARISON": "forbidden",
            "SEALING": "the pack's sha256 is recorded in FREEZE_PA07 before the engine runs on the second source; the pack is opened only by the comparison step",
            "COMPARISON": "per case: engine value vs truth value, tolerance, PASS / FAIL, CRITICAL when a FAIL would change a quantity (band status, site class, space count, material present)",
            "RESULT_ARTIFACT": "PA07_INDEPENDENT_VALIDATION_RESULT.json (STATUS EXECUTED, SOURCE_INDEPENDENT, CASES, CRITICAL_MISMATCHES)",
            "STATUS": "FROZEN_UNEXECUTED", "REASON": "no independent source available in the repository or the uploads (see SECOND_REGRESSION_SOURCE_REQUIRED.json)"}


def second_source_required():
    up = Path("/root/.claude/uploads")
    seen = {"data/golden/23010/inputs/AR-00_MAR2023.pdf": "a plotted PDF only (no CAD), used in six earlier rounds (E1 / AE01 / SSE02), seen by Claude, benchmark files beside it never opened in this phase; not independent and not vector",
            "uploads/10eb2876-20230331-STR.dwg": "a structural DWG (AC1021); no DWG decoder in this environment (no dwgread / dwg2dxf; ezdxf reads DXF only); structural, not architectural",
            "uploads/2885c79f-R_01 ... .pdf": "a five-page company quotation on letterhead, not drawings",
            "uploads/37e75bb6 / 484f8d86 ... .dwf": "P7757 itself (DWF)", "uploads/4a9be682-sanitary-77573.pdf": "P7757 sanitary sheets"}
    return {"ARTIFACT": "SECOND_REGRESSION_SOURCE_REQUIRED", "STATUS": "SOURCE_REQUIRED", "GATE_V3_EFFECT": "conditions 5 and 6 NOT_READY (correct result, not a failure)",
            "CANDIDATES_EXAMINED": [{"SOURCE_SET": k, "WHY_UNSUITABLE": v} for k, v in seen.items()],
            "WHY_NOT_FABRICATED": "a synthetic villa written by the same author as the engine is not independent; P7757 is the development project; the 23010 PDF was used to develop earlier rounds and is raster / plotted only",
            "WHAT_IS_SEALED": "nothing yet: the protocol and its tolerances are frozen in FREEZE_PA07; the truth pack will be sealed (sha256 in the freeze) before the engine runs on the new source",
            "WHETHER_CLAUDE_HAS_SEEN_IT": "no second villa exists to have been seen; every examined candidate is listed above with its exposure",
            "UPLOAD_REQUEST": {"REQUIRED": ["architectural plans as DWG or DXF (or a LibreDWG JSON decode, since no DWG converter exists here)", "the original plotted PDF of the same sheets"],
                               "OPTIONAL": ["structural plans (DWG / DXF / PDF)"], "NOT_NEEDED": ["any Excel benchmark or BOQ", "any pricing"],
                               "CONDITIONS": ["a villa never used in this repository", "the person preparing the truth pack measures from the original sheets, not from any engine output", "the pack follows TRUTH_PACK_FIELDS and covers the DIVERSITY list, at least five cases"]},
            "GEOMETRY_ADDED_BY_SUCH_A_SOURCE": DIVERSITY}
