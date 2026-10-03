"""REPORTING V2 - bilingual glossary and user-facing explanations of technical status codes. Project-agnostic.

Arabic authority order (the adapters apply it): (1) the register's own Arabic text; (2) this glossary; (3) nothing
(the Arabic cell stays empty - never machine-invented). Glossary sources are recorded per entry:
    BRIEF      the owner's Reporting V2 brief (Urban's own wording)
    REGISTER   wording already used by an engine register (e.g. Alsenan ARCH_BOQ 'ar', Qortuba CANONICAL_BOQ)
    REPO       wording already used elsewhere in the repository (engine/waste.py, documents/)
    LABEL      a presentation heading (no technical meaning)
"""

from __future__ import annotations

GLOSSARY_ID = "URBAN_REPORTING_GLOSSARY_V1"

LEVELS = {
    "FOUNDATION": ("FOUNDATION / SUBSTRUCTURE", "الأساسات", "BRIEF"),
    "GF": ("GROUND FLOOR", "الدور الأرضي", "BRIEF"),
    "1F": ("FIRST FLOOR", "الدور الأول", "LABEL"),
    "2F": ("SECOND FLOOR", "الدور الثاني", "LABEL"),
    "ROOF": ("ROOF", "السطح", "LABEL"),
    "EXTERNAL": ("OTHER / EXTERNAL", "الأعمال الخارجية", "LABEL"),
    "UNASSIGNED": ("LEVEL NOT ASSIGNED", "غير محدد الدور", "LABEL"),
    "PROJECT": ("TOTAL PROJECT", "إجمالي المشروع", "LABEL"),
}

TRADES = {
    "STRUCTURAL_CONCRETE": ("STRUCTURAL CONCRETE", "الخرسانة الإنشائية", "BRIEF"),
    "PLAIN_CONCRETE": ("PLAIN CONCRETE / BLINDING", "خرسانة عادية", "REPO"),
    "REBAR": ("REINFORCEMENT", "حديد التسليح", "LABEL"),
    "BLOCKWORK": ("BLOCKWORK", "المباني", "BRIEF"),
    "PLASTER": ("PLASTER", "المساح / اللياسة", "BRIEF"),
    "PAINT": ("PAINT", "الصبغ / الدهان", "BRIEF"),
    "FLOOR_TILE": ("FLOOR TILE / PORCELAIN", "بلاط الأرضيات", "BRIEF"),
    "WALL_TILE": ("WALL TILE", "بلاط الجدران", "BRIEF"),
    "SKIRTING": ("SKIRTING", "الوزرة", "REGISTER"),
    "HIDDEN_PROFILE": ("HIDDEN PROFILE", "بروفايل مخفي", "LABEL"),
    "CEILING": ("CEILING", "الأسقف", "REGISTER"),
    "WATERPROOFING": ("WATERPROOFING", "العازل", "BRIEF"),
    "MARBLE": ("MARBLE", "الرخام", "LABEL"),
    "ALUMINIUM_GLAZING": ("ALUMINIUM & GLAZING", "الألمنيوم والزجاج", "BRIEF"),
    "DOORS": ("DOORS", "الأبواب", "REGISTER"),
    "WINDOWS": ("WINDOWS", "الشبابيك", "REGISTER"),
    "RAILINGS": ("RAILINGS", "الدرابزين", "REGISTER"),
    "STAIRS": ("STAIRS", "الدرج", "REGISTER"),
    "PHYSICAL_AREA": ("PHYSICAL MEASURES (finish not assigned)", "قياسات فعلية (بدون مادة تشطيب)", "LABEL"),
}

SECTIONS = {
    "TOTAL_SUMMARY": ("TOTAL SUMMARY", "الملخص العام"),
    "TRADE_TOTALS": ("MAIN TOTALS BY TRADE", "الإجمالي حسب البنود"),
    "FLOOR_TOTALS": ("TOTALS BY FLOOR", "الإجمالي حسب الدور"),
    "COVERAGE": ("QUANTITY COVERAGE BY STATUS", "تغطية الكميات حسب الحالة"),
    "KEY_NOTES": ("KEY NOTES", "ملاحظات رئيسية"),
    "KPI": ("FLOOR KEY FIGURES", "مؤشرات الدور"),
    "ROOMS": ("ROOM / AREA SUMMARY", "ملخص الغرف والمساحات"),
    "STRUCTURE": ("STRUCTURAL SUMMARY", "الملخص الإنشائي"),
    "BEAMS": ("BEAMS BY TYPE", "الجسور حسب النوع"),
    "COLUMNS": ("COLUMNS BY TYPE", "الأعمدة حسب النوع"),
    "OPENINGS": ("OPENINGS / ALUMINIUM", "الفتحات والألمنيوم"),
    "FINISHES": ("MASONRY & FINISHES", "المباني والتشطيبات"),
    "ROOF_WP": ("ROOF WATERPROOFING", "عزل السطح"),
    "NOTES": ("FLOOR NOTES / BLOCKERS", "ملاحظات ومعوقات الدور"),
    "FOOTINGS": ("FOOTING TYPE SUMMARY", "ملخص القواعد"),
    "STRAPS": ("STRAP / TIE BEAMS", "الميدات الرابطة"),
    "SUBSTRUCTURE_OTHER": ("OTHER SUBSTRUCTURE ITEMS", "بنود الأساسات الأخرى"),
    "OPENING_SCHEDULE": ("OPENINGS SCHEDULE - ALL FLOORS", "جدول الفتحات - جميع الأدوار"),
    "CURVED": ("CURVED GLAZING - MEASUREMENT BASES", "الزجاج المنحني - أسس القياس"),
    "DOOR_COUNTS": ("DOORS", "الأبواب"),
    "OWNER_QUESTIONS": ("OWNER QUESTIONS (REQUIRED)", "أسئلة إلى المالك"),
    "BLOCKERS": ("BLOCKED / PARTIAL ITEMS", "البنود الموقوفة والجزئية"),
    "METHODS": ("URBAN METHODS (VERSIONED)", "منهجيات أوربن"),
    "OWNER_FACTS": ("PROJECT OWNER FACTS", "معلومات المالك للمشروع"),
    "SOURCES": ("SOURCE FILES", "ملفات المصدر"),
    "RUN": ("RUN INFORMATION", "معلومات التشغيل"),
    "STATUS_ALIAS": ("STATUS ALIAS TABLE", "جدول الحالات"),
    "CLASSES": ("ROW CLASSES", "تصنيف الأسطر"),
    "QA": ("QA RESULT", "نتيجة ضبط الجودة"),
}

STATUS_LABEL = {"COMPUTED": ("Computed", "محسوب"), "PARTIAL": ("Partial", "جزئي"), "REVIEW": ("Review", "مراجعة"),
                "BLOCKED": ("Blocked", "موقوف"), "INFO": ("Info", "معلومة")}

# ------------------------------------------------------------------ user-facing explanations
# technical code -> (what it means for the user, effect on quantity, what is needed, priority family)
# Priority families (a reporting rule, not an engine output): STRUCTURE / FOUNDATION -> HIGH;
# ENVELOPE / OPENINGS / FINISHES / ROOMS -> MEDIUM; INFO -> LOW.
EXPLAIN = {
    "BLOCKED_HEIGHT": ("A height or level needed for this item is not in the drawings.",
                       "The item is not released (no volume / area).", "Provide the level or height (section or owner value).", "STRUCTURE"),
    "BLOCKED_WITH_REASON": ("The source does not define this element well enough to measure it.",
                            "Not measured; excluded from the total.", "Provide a plan / section that defines it.", "STRUCTURE"),
    "BLOCKED_INPUT_MISSING": ("One or more required inputs are not printed in the drawings.",
                              "Not measured; excluded from the total.", "Provide the missing inputs listed.", "STRUCTURE"),
    "NO_BAND_ADJACENT_TO_TAG": ("A beam tag on the plan has no beam outline next to it.",
                                "That beam occurrence is not measured.", "Confirm which beam the tag belongs to.", "STRUCTURE"),
    "NO_BAND_AT_SCHEDULED_BREADTH": ("No beam outline of the scheduled width was found at the tag.",
                                     "That beam occurrence is not measured.", "Confirm the beam size or its location.", "STRUCTURE"),
    "NO_BAND_PARALLEL_TO_TAG": ("No beam outline runs in the direction of the tag.",
                                "That beam occurrence is not measured.", "Confirm the beam run for the tag.", "STRUCTURE"),
    "TAG_INSIDE_SUPPORT": ("The beam tag sits inside a column / support, so its span is ambiguous.",
                           "That beam occurrence is not measured.", "Confirm the span the tag refers to.", "STRUCTURE"),
    "SPAN_COUNT_MISMATCH": ("The number of spans drawn differs from the schedule.",
                            "That beam occurrence is not measured.", "Confirm the spans of this beam.", "STRUCTURE"),
    "BAND_TYPE_CONFLICT": ("Two different beam types are tagged on the same beam outline.",
                           "That beam occurrence is not measured.", "Confirm which type applies.", "STRUCTURE"),
    "BLOCKED_TAG_NOT_BOUND": ("A column tag could not be matched to a drawn column of the printed size.",
                              "Column concrete for it is not released.", "Confirm the column location / size.", "STRUCTURE"),
    "BLOCKED_UPPER_MEMBER_UNBOUND": ("Upper beam / slab could not be uniquely matched.",
                                     "Column concrete is not released.", "Confirm upper framing member or provide structural detail.", "STRUCTURE"),
    "BLOCKED_SEVERAL_OUTLINES_ON_STOREY_SHEET": ("Several column outlines match one tag on the storey sheet.",
                                                 "Column concrete is not released.", "Confirm which outline is the column.", "STRUCTURE"),
    "SOURCE_CONFLICT": ("Two drawings disagree about this element.",
                        "Not measured until the conflict is resolved.", "Owner / consultant decision on which drawing governs.", "FOUNDATION"),
    "UNRESOLVED": ("A project value needed by several trades is not in the drawings.",
                   "Dependent finishes stay blocked.", "Provide the value (e.g. floor build-up per storey).", "FINISHES"),
    "NOT_CLOSED": ("The open-plan zone has no closed boundary in the drawings.",
                   "Room areas of the zone are not released.", "Confirm the entrance (door, screen or open).", "ROOMS"),
    "BLOCKED": ("Not measurable from the current source.", "Not measured.", "See the reason given.", "STRUCTURE"),
    "BLOCKED_MATERIAL": ("The finish / material is not specified in the drawings.",
                         "The physical measure exists but the material quantity is not released.", "Provide the finish schedule.", "FINISHES"),
    "BLOCKED_GEOMETRY": ("The geometry of this item is not established.", "Not measured.", "Provide the drawing detail.", "FINISHES"),
    "BLOCKED_FLOOR_BUILDUP": ("The floor build-up above the slab is not in the drawings.",
                              "Paint and wall-tile heights cannot be fixed.", "Provide the floor build-up per storey.", "FINISHES"),
    "TOPOLOGY_ROLE_UNRESOLVED": ("Lines inside the room could not be identified (wall, joinery or symbol).",
                                 "Room area not certified.", "Confirm what the lines are.", "ROOMS"),
    "LABEL_OCCURRENCE_SPLIT": ("One room label is split across two drawn spaces.", "Room area not certified.",
                               "Confirm the room boundary.", "ROOMS"),
    "MULTIPLE_SEMANTIC_LABELS": ("One drawn space carries several room names.", "Room area not certified.",
                                 "Confirm the room division.", "ROOMS"),
    "GEOS_CROSSCHECK_DISAGREES": ("Two independent area calculations disagree for this space.", "Room area not certified.",
                                  "Engineering review of the boundary.", "ROOMS"),
    "NEAR_MISS_BOUNDARY_GAP": ("A small gap in the drawn boundary leaves the room open.", "Room area not certified.",
                               "Confirm the wall is continuous.", "ROOMS"),
    "OPENING_CLOSURE": ("An opening closure is ambiguous.", "Room area not certified.", "Confirm the opening.", "ROOMS"),
    "OWNER_DERIVED_REVIEW_REQUIRED": ("The value comes from an owner-derived project dimension that is provisional.",
                                      "Shown, but needs confirmation.", "Confirm the final value.", "OPENINGS"),
    "NOT_TAGGED_ON_PLAN": ("The schedule lists this type but no plan occurrence carries it.", "Nothing to measure.",
                           "None (information).", "INFO"),
    "GLAZED_OPENING_FUNCTION_UNKNOWN": ("The glazed opening could be a window, a door or a screen.",
                                        "Counted as an opening only; not added to windows or doors.", "Confirm its function.", "OPENINGS"),
    "WINDOW_CANDIDATE": ("Glazing in a wall gap; window function not yet confirmed by a schedule.",
                         "Counted as a window candidate; area blocked until a height exists.", "Provide the window schedule / heights.", "OPENINGS"),
    "COMPUTED_PARTIAL": ("Measured for the elements the source defines; the rest is listed as blocked.",
                         "The total is partial.", "Resolve the listed blockers.", "STRUCTURE"),
    "PARTIAL": ("Only part of the scope could be measured.", "The total is partial.", "Resolve the listed blockers.", "FINISHES"),
    "SOURCE_ANCHOR": ("The DXF the quantities come from is not yet proved identical to the issued DWG.",
                      "Quantities stay SHADOW (not released); values unchanged.", "Controlled re-export of the DWG (anchor plan).", "INFO"),
    "CROSS_ROUTE_AGREEMENT": ("A second, independent decoding route has not yet confirmed the geometry.",
                              "Quantities stay SHADOW (not released).", "Run the second route on the anchored source.", "INFO"),
    "SHADOW_ONLY": ("No baseline approval exists for these quantities.", "Shown for review only.", "Owner approval of a baseline.", "INFO"),
    "HEIGHT_NOT_PROVED": ("The wall height is not proved by the source.", "Wall area not released.",
                          "Provide the structural termination / ceiling level.", "FINISHES"),
}

PRIORITY = {"STRUCTURE": "HIGH", "FOUNDATION": "HIGH", "ROOMS": "MEDIUM", "OPENINGS": "MEDIUM", "FINISHES": "MEDIUM",
            "ENVELOPE": "MEDIUM", "INFO": "LOW"}


def explain(code: str) -> dict:
    """Generic explanation of a technical code (exact match, else the longest known prefix). Unknown -> KeyError."""
    key = code if code in EXPLAIN else max((k for k in EXPLAIN if code.startswith(k)), key=len, default=None)
    if key is None:
        raise KeyError(f"no user-facing explanation for technical code {code!r}")
    why, effect, need, fam = EXPLAIN[key]
    return {"code": code, "explained_as": key, "why": why, "effect": effect, "needed": need, "family": fam,
            "priority": PRIORITY[fam]}


def level(key: str) -> tuple:
    return LEVELS[key][:2]


def trade(key: str) -> tuple:
    return TRADES[key][:2]


def section(key: str) -> tuple:
    return SECTIONS[key]


def glossary_record() -> dict:
    return {"id": GLOSSARY_ID,
            "levels": {k: {"en": v[0], "ar": v[1], "source": v[2]} for k, v in LEVELS.items()},
            "trades": {k: {"en": v[0], "ar": v[1], "source": v[2]} for k, v in TRADES.items()},
            "sections": {k: {"en": v[0], "ar": v[1], "source": "LABEL"} for k, v in SECTIONS.items()},
            "explanations": sorted(EXPLAIN), "priority_rule": PRIORITY,
            "rule": "register Arabic first, then this glossary, else empty - never machine-invented"}
