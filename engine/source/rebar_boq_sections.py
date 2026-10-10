"""Structural BOQ reinforcement presentation: two visibly separate sections (generic, report layer).

  SECTION 1  ACCURATE BOQ REBAR    حديد التسليح الفعلي من المخططات      released / provisional / blocked + official status
  SECTION 2  ROUGH REBAR SUMMARY   تقدير تقريبي للحديد حسب حجم الخرسانة  concrete x ratio = rough steel, with the
                                                                        mandatory note
  (optional) SANITY VARIANCE       labelled SANITY_VARIANCE / REBAR_SANITY_REVIEW only

No row, column or total crosses sections: the accurate section never shows a rough figure and the rough section never
shows an accurate one. Tonnes are engine kg / 1000. Stdlib only.
"""

from __future__ import annotations

from engine.source import accurate_boq_rebar as AB
from engine.source import rough_rebar_sanity as RR

ACCURATE_COLUMNS = ("CATEGORY", "RELEASED_T", "PROVISIONAL_T", "BLOCKED_MODELLED_T", "BLOCKED_UNQUANTIFIED_PARTS",
                    "OFFICIAL_STATUS")
ROUGH_COLUMNS = ("CATEGORY", "CONCRETE_M3", "RATIO_KG_M3", "ROUGH_STEEL_T")
VARIANCE_COLUMNS = ("CATEGORY", "ACCURATE_PROJECTED_T", "ROUGH_REFERENCE_T", "SANITY_VARIANCE_T",
                    "SANITY_VARIANCE_PERCENT", "STATE", "FLAGS")


def _t(kg):
    return None if kg is None else round(kg / 1000.0, 3)


def build(accurate, rough, variance=None):
    if accurate.get("product") != AB.PRODUCT or rough.get("product") != RR.PRODUCT:
        raise ValueError("build needs an ACCURATE_BOQ_REBAR summary and a ROUGH_REBAR_SUMMARY")
    acc_rows = [{"CATEGORY": c, "RELEASED_T": _t(r["released_kg"]), "PROVISIONAL_T": _t(r["provisional_kg"]),
                 "BLOCKED_MODELLED_T": _t(r["blocked_modelled_kg"]),
                 "BLOCKED_UNQUANTIFIED_PARTS": r["blocked_unquantified_parts"],
                 "OFFICIAL_STATUS": r["official_status"]} for c, r in accurate["categories"].items()]
    p = accurate["project"]
    sec1 = {"section_id": AB.PRODUCT, "title_en": AB.TITLE_EN, "title_ar": AB.TITLE_AR,
            "columns": list(ACCURATE_COLUMNS), "rows": acc_rows,
            "project": {"RELEASED_T": _t(p["released_kg"]), "PROVISIONAL_T": _t(p["provisional_kg"]),
                        "BLOCKED_MODELLED_T": _t(p["blocked_modelled_kg"]),
                        "BLOCKED_UNQUANTIFIED_PARTS": p["blocked_unquantified_parts"],
                        "FINAL_REBAR": p["final_rebar"], "FINAL_REBAR_T": _t(p["final_rebar_kg"])},
            "note": "Bar-by-bar from drawings, schedules and details. Released, provisional and blocked are never "
                    "added together."}
    rough_rows = [{"CATEGORY": c, "CONCRETE_M3": round(r["modelled_concrete_m3"], 3),
                   "RATIO_KG_M3": r["ratio_kg_per_m3"],
                   "ROUGH_STEEL_T": _t(r["rough_kg_modelled_basis"]),
                   "RATIO_STATE": r["ratio_state"]} for c, r in rough["categories"].items()]
    sec2 = {"section_id": RR.PRODUCT, "title_en": RR.TITLE_EN, "title_ar": RR.TITLE_AR,
            "columns": list(ROUGH_COLUMNS), "rows": rough_rows, "authority": RR.AUTHORITY, "use": RR.USE,
            "not_configured": [{"occurrence_id": x["occurrence_id"], "element_class": x["element_class"],
                                "state": x["state"]} for x in rough["not_configured"]],
            "note": RR.MANDATORY_NOTE}
    sections = [sec1, sec2]
    if variance is not None:
        sections.append({"section_id": "REBAR_SANITY_VARIANCE", "title_en": "REBAR SANITY VARIANCE",
                         "title_ar": "مقارنة تحقق (ليست كمية)", "columns": list(VARIANCE_COLUMNS),
                         "rows": [{"CATEGORY": r["category"], "ACCURATE_PROJECTED_T": _t(r["ACCURATE_PROJECTED_KG"]),
                                   "ROUGH_REFERENCE_T": _t(r["ROUGH_REFERENCE_KG"]),
                                   "SANITY_VARIANCE_T": _t(r["SANITY_VARIANCE_KG"]),
                                   "SANITY_VARIANCE_PERCENT": None if r["SANITY_VARIANCE_PERCENT"] is None
                                   else round(r["SANITY_VARIANCE_PERCENT"], 1),
                                   "STATE": r["state"], "FLAGS": list(r["flags"])} for r in variance["rows"]],
                         "note": "A sanity variance only raises REBAR_SANITY_REVIEW; it never changes the accurate "
                                 "quantity."})
    return {"sections": sections,
            "rule": "two separate sections; no total, row or column crosses them"}
