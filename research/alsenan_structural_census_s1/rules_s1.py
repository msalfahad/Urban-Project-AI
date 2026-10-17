"""ST7757 structural project rules (Round S1). Data only: every rule carries its source, raw wording, normalised rule,
scope, precedence and override behaviour. Text channels:

    DXF_TEXT          the DXF holds the text (handle given); legacy Arabic decoded by engine.source.legacy_text
    PDF_RASTER        the PDF page is an image (p.8) - visual transcription (AI); OCR corroboration from Round 4 where
                      the Round-4 VISUAL_SOURCE_CLAIM register holds it (claim id given)
    PDF_VECTOR        the PDF page is vector glyphs without a text layer (pp.13-16) - visual transcription (AI)

Status: EXACT_RULE (printed, unambiguous, two channels or a DXF text) / CANDIDATE (one AI channel) /
SOURCE_CONFLICT (two printed rules disagree) / BLOCKED_METHOD (printed but not executable as written).
"""

PDF = "ST7757.pdf"
DXF = "ST7757.dxf"

# precedence vocabulary (engine.source.structural_census.PRECEDENCE + typical details / schedules)
P_LOCAL, P_FLOOR, P_PROJECT, P_TYPICAL, P_SCHEDULE, P_GENERAL = (
    "LOCAL_PANEL_NOTE", "FLOOR_SPECIFIC_NOTE", "PROJECT_DEFAULT", "TYPICAL_DETAIL", "SCHEDULE_DEFINITION",
    "GENERAL_SPECIFICATION")


def R(rule_id, page, raw, english, normalised, scope, priority, override, status, *, arabic=None, bbox=None,
      handles=None, channels=None, r4_claim=None, topic=None, values=None):
    return {"rule_id": rule_id, "topic": topic, "arabic_wording": arabic, "english_interpretation": english,
            "source_file": PDF if not handles else f"{PDF} + {DXF}", "page": page, "crop_bbox_pdf_pt": bbox,
            "dxf_handles": handles or [], "raw_text": raw, "normalized_rule": normalised, "values": values or {},
            "element_scope": scope, "priority": priority, "override_behaviour": override, "status": status,
            "channels": channels or [], "round4_claim": r4_claim}


RULES = [
    # ------------------------------------------------------------------ p.8 RECOMMENDATIONS (raster page)
    R("P8-N01", 8, "1. هذه المخططات استرشادية ولا تصلح للتنفيذ الا بعد مراجعة مهندس الاشراف .",
      "Drawings are for guidance; not for construction until reviewed by the supervising engineer.",
      "administrative", ["ALL"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="ADMIN",
      channels=["PDF_RASTER"]),
    R("P8-N02", 8, "2. يجب على المقاول مراجعة و مطابقة المخططات الانشائية مع المخططات المعمارية ... وفي حالة وجود اي "
                   "اختلاف يجب على المقاول الرجوع الى المهندس المشرف قبل البدء بالتنفيذ .",
      "Structural, architectural and services drawings complement each other; any discrepancy goes to the "
      "supervising engineer.", "discrepancy -> engineer (supports SOURCE_CONFLICT handling, never auto-resolve)",
      ["ALL"], P_GENERAL, "conflicts are escalated, not resolved by the contractor", "EXACT_RULE", arabic=True,
      topic="ADMIN", channels=["PDF_RASTER"]),
    R("P8-N03", 8, "3. يجب على المقاول التقيد بالابعاد المذكورة ... ولا يحق للمقاول القياس من المخططات وإنما الابعاد تقرأ "
                   "من المخططات .", "Use printed dimensions; do not scale the drawings.",
      "printed dimension > scaled dimension (scaled values stay PROVISIONAL)", ["ALL"], P_GENERAL,
      "a printed dimension overrides a measured one", "EXACT_RULE", arabic=True, topic="DIMENSIONS",
      channels=["PDF_RASTER"]),
    R("P8-N04", 8, "4. يجب على المقاول التأكد من أن جميع الفتحات الموجودة بالمخططات المعمارية أو مخططات الخدمات موجودة "
                   "بالمخططات الانشائية ...", "All architectural / services openings must appear on the structural "
                                                 "drawings; refer to the engineer for details.",
      "openings: cross-check architectural vs structural", ["SLAB", "BEAM", "WALL"], P_GENERAL, "none",
      "EXACT_RULE", arabic=True, topic="OPENINGS", channels=["PDF_RASTER"]),
    R("P8-N05", 8, "5. جميع أعمال الخرسانات المسلحة والعادية يجب أن تكون صب جاهز ...", "All concrete ready-mix.",
      "material", ["CONCRETE"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="MATERIAL",
      channels=["PDF_RASTER"]),
    R("P8-N06", 8, "6. جهد الخرسانة المسلحة f'c ... لا يقل عن 300 كجم/سم2 ... 150 كجم/سم2 للخرسانات العادية ...",
      "f'c >= 300 kg/cm2 reinforced, 150 kg/cm2 plain, unless the engineer raises some beams / columns.",
      "fc_RC >= 300 kg/cm2; fc_plain >= 150 kg/cm2", ["CONCRETE"], P_GENERAL, "engineer may increase locally",
      "EXACT_RULE", arabic=True, topic="MATERIAL", channels=["PDF_RASTER"], values={"fc_rc": 300, "fc_plain": 150}),
    R("P8-N07", 8, "7. ... أخذ مكعبات من خرسانات المشروع ...", "Concrete cube testing.", "QA", ["CONCRETE"], P_GENERAL,
      "none", "EXACT_RULE", arabic=True, topic="QA", channels=["PDF_RASTER"]),
    R("P8-N08", 8, "8. يجب استخدام حديد تسليح بالمشروع لايقل جهده عن (4200 كجم/سم2) ...",
      "Reinforcing steel yield >= 4200 kg/cm2, tested before delivery.", "fy >= 4200 kg/cm2", ["REBAR"],
      P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="MATERIAL", channels=["PDF_RASTER"], values={"fy": 4200}),
    R("P8-N09", 8, "9. يجب ان لايقل طول رباط اشاير حديد التسليح (Development Length) عن (70) مرة قطر السيخ بمناطق الشد ، "
                   "(40) مرة قطر السيخ بمناطق الضغط .",
      "Development length of STARTER bars >= 70 D in tension zones, >= 40 D in compression zones.",
      "starter (dowel) development length: tension 70D, compression 40D", ["COLUMN_STARTER", "STARTER"],
      P_PROJECT, "a local detail length (e.g. p.13 starter 40D projection) is specific to its member",
      "EXACT_RULE", arabic=True, topic="LAP_DEVELOPMENT", channels=["PDF_RASTER", "OCR(R4)"],
      r4_claim="P8-N09-STARTER-DEVELOPMENT", values={"tension_D": 70, "compression_D": 40}),
    R("P8-N10", 8, "10. يجب عدم تنفيذ أية أساسات على أرض دفان ... التأكد من جهد التربة ...",
      "No foundations on fill; verify soil capacity by test.", "foundation bearing check", ["FOOTING"], P_GENERAL,
      "none", "EXACT_RULE", arabic=True, topic="FOUNDATION", channels=["PDF_RASTER"]),
    R("P8-N11", 8, "11. يجب على المقاول زيادة عرض الجسور التي يمر بها بايبات صحي او تغذية او كهرباء او تكييف بمقدار 5 سم .",
      "Beams crossed by service pipes are widened by 5 cm.", "beam width +5 cm where pipes pass (occurrences not "
                                                            "marked on plans)", ["BEAM"], P_PROJECT,
      "applies only where services cross - locations not on the structural plans", "BLOCKED_METHOD", arabic=True,
      topic="BEAM_GEOMETRY", channels=["PDF_RASTER"]),
    R("P8-N12", 8, "12. ... التأكد من منسوب التأسيس ...", "Confirm founding level with architect / soil test.",
      "founding level to be confirmed", ["FOOTING"], P_GENERAL, "none", "EXACT_RULE", arabic=True,
      topic="FOUNDATION", channels=["PDF_RASTER"]),
    R("P8-N13", 8, "13. ... استخدام أسمنت مقاوم للاملاح والكبريتات للخرسانات ... الملاصقة للتربة ...",
      "Sulphate-resisting cement for concrete in contact with soil / groundwater.", "material", ["SUBSTRUCTURE"],
      P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="MATERIAL", channels=["PDF_RASTER"]),
    R("P8-N14", 8, "14. في حال وجود مياه جوفية ... شركة سحب مياه ...", "Dewatering when groundwater is present.",
      "temporary works", ["SUBSTRUCTURE"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="TEMPORARY",
      channels=["PDF_RASTER"]),
    R("P8-N15", 8, "15. ... دراسة فنية ... إجراءات الحماية والتدعيم ...", "Excavation support study.", "temporary works",
      ["SUBSTRUCTURE"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="TEMPORARY", channels=["PDF_RASTER"]),
    R("P8-N16", 8, "16. تنفذ الخرسانة العادية بنسبة 1:3:6 خلط جاهز .", "Plain concrete mix 1:3:6 ready-mix.",
      "material", ["PLAIN_CONCRETE"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="MATERIAL",
      channels=["PDF_RASTER"]),
    R("P8-N17", 8, "17. لايقوم المقاول بفك الشدادات الخشبية ... إلا بعد ... الفترة الزمنية المطلوبة على ان لا تقل عن 14 يوم ...",
      "Formwork stripping not before 14 days (with re-propping for long-span beams).", "formwork >= 14 days",
      ["FORMWORK"], P_PROJECT, "p.1 plan note says 21 days", "SOURCE_CONFLICT", arabic=True, topic="FORMWORK",
      channels=["PDF_RASTER"], values={"days": 14}),
    R("P8-N18", 8, "18. سمك بلاطات الاسقف العادية 16 سم ما لم يذكر خلاف ذلك .",
      "Normal suspended slabs are 16 cm thick unless stated otherwise.",
      "NORMAL_SUSPENDED_SLAB_THICKNESS = 160 mm; precedence LOCAL PANEL NOTE > FLOOR NOTE > PROJECT DEFAULT",
      ["SUSPENDED_SLAB"], P_PROJECT, "a panel 'T xx' note or a floor note overrides; never applied to ground slabs",
      "EXACT_RULE", arabic=True, topic="SLAB_THICKNESS", channels=["PDF_RASTER", "OCR(R4)", "DXF_TEXT p.1 note"],
      r4_claim="P8-N18-SLAB-THICKNESS", values={"t_mm": 160}),
    R("P8-N19", 8, "19. يتم عمل جسور لربط اعمدة المصعد على ارتفاع 3.00m اذا كان ارتفاع الدور أكثر من 4.30m وذلك حول بيت "
                   "المصعد .", "Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than "
                               "4.30 m.", "LIFT_TIE_BEAM required where storey height > 4.30 m; at +3.00 m",
      ["LIFT_SHAFT_COLUMNS"], P_PROJECT, "applies per storey by height", "EXACT_RULE", arabic=True,
      topic="LIFT_TIE_BEAMS", channels=["PDF_RASTER", "OCR(R4)"], r4_claim="P8-N19-LIFT-TIE-BEAMS",
      values={"trigger_storey_height_m": 4.30, "beam_height_m": 3.00}),
    R("P8-N20", 8, "20. تنفذ جميع الحوائط المتضمنة اعمدة بنفس سماكة الاعمدة المتضمنة لها.",
      "Walls containing columns are built to the column thickness.", "architectural coordination", ["WALL"],
      P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="WALLS", channels=["PDF_RASTER"]),
    R("P8-N21", 8, "21. يتم أستخدام حديد اضافي جانبي ( 2Φ12 ، 3Φ12 ، 4Φ12 ) في الجسور ذات العمق أكبر من 60 سم حسب عرض "
                   "الجسر ما لم يذكر خلاف ذلك.",
      "Side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm, according to the beam width, unless stated otherwise.",
      "deep-beam side bars (D > 60 cm): 2/3/4 Ø12 by width - width -> count mapping NOT printed; schedule REMARKS "
      "override", ["BEAM_D_GT_60"], P_PROJECT, "schedule REMARKS (e.g. 2Ø12/30cm, 2Ø16/20cm) override",
      "BLOCKED_METHOD", arabic=True, topic="SIDE_BARS", channels=["PDF_RASTER", "OCR(R4)"],
      r4_claim="P8-N21-SIDE-BARS"),
    R("P8-N22", 8, "22. يجب أن لا يقل سمك الغطاء الخرساني عن 2.5 سم في الأعمدة والبلاطات والجسور وعن 7سم في الخرسانة "
                   "الملاصقة للتربة.", "Cover >= 2.5 cm columns / slabs / beams; >= 7 cm in contact with soil.",
      "cover: members 25 mm; soil-contact 70 mm", ["COLUMN", "SLAB", "BEAM", "SUBSTRUCTURE"], P_PROJECT, "none",
      "EXACT_RULE", arabic=True, topic="COVER", channels=["PDF_RASTER", "OCR(R4)"],
      r4_claim="P8-N22-COVER-GENERAL", values={"member_mm": 25, "soil_mm": 70}),
    R("P8-N23", 8, "23. ... رفع الشدات الخشبية للبلاطات الكبيرة والجسور ذات البحور الطويلة من المنتصف ...",
      "Camber formwork of large slabs / long beams at mid-span.", "formwork camber", ["FORMWORK"], P_GENERAL,
      "none", "EXACT_RULE", arabic=True, topic="FORMWORK", channels=["PDF_RASTER"]),
    R("P8-N24", 8, "24. ... التنسيق بين مخططات التكييف و المخططات الانشائية ...", "Coordinate HVAC and structure.",
      "coordination", ["ALL"], P_GENERAL, "none", "EXACT_RULE", arabic=True, topic="ADMIN",
      channels=["PDF_RASTER"]),
    # ------------------------------------------------------------------ plan notes (DXF legacy Arabic + PDF)
    R("P1-NOTE-A", 1, "وجوب صب جميع الاسقف بسماكة (16 سم) مالم يذكر خلاف ذلك",
      "All roofs / slabs cast 16 cm thick unless stated otherwise.", "same as P8-N18 (second printed source)",
      ["SUSPENDED_SLAB"], P_PROJECT, "local panel / floor note overrides", "EXACT_RULE", arabic=True,
      topic="SLAB_THICKNESS", handles=["7D"], channels=["DXF_TEXT (legacy Arabic decoded)", "PDF_VECTOR"],
      values={"t_mm": 160}),
    R("P1-NOTE-B", 1, "وجوب صب الشناجات الخارجية جهة الجار, فوق و تحت طابوق أسود مبنى من منسوب الاساس",
      "External ground beams on the neighbour side cast above and below a black-brick wall built up from "
      "foundation level.", "neighbour-side external ground beams: upper + lower beam over a black-brick wall",
      ["GROUND_BEAM_EXTERIOR", "BOUNDARY"], P_PROJECT, "applies on neighbour sides only", "CANDIDATE",
      arabic=True, topic="GROUND_BEAMS", handles=["B8"], channels=["DXF_TEXT (legacy Arabic decoded)"]),
    R("P1-NOTE-C", 1, "عدم فك شدات الخشب للاسقف والكمرات قبل مرور فترة زمنية لاتقل عن 21 يوم",
      "Do not strip slab / beam formwork before 21 days.", "formwork >= 21 days", ["FORMWORK"], P_PROJECT,
      "conflicts with p.8 note 17 (14 days)", "SOURCE_CONFLICT", arabic=True, topic="FORMWORK", handles=["7E"],
      channels=["DXF_TEXT (legacy Arabic decoded)"], values={"days": 21}),
    R("P4-6-NOTE-1", 4, "1- على المقاول مطابقة تفاصيل الدروة و البروزات المعمارية قبل تنفيذها / CHECK ARCHITECTURAL "
                        "DETAIL OF PARAPET, BEFORE CASTING", "Check parapet / projection details against architecture "
                                                             "before casting.",
      "parapet geometry from the architectural drawings", ["PARAPET", "PROJECTION"], P_FLOOR, "none",
      "EXACT_RULE", arabic=True, topic="PARAPETS", handles=["D5", "D7", "DF", "E0", "E8", "E9"],
      channels=["DXF_TEXT (legacy Arabic decoded)", "DXF_TEXT (English)"]),
    R("P4-6-NOTE-2", 4, "2- يجب وضع حديد علوى 5Ø10/m للبلاطات فوق الجسور بطول ثلث البحر في الاتجاهين",
      "Top steel 5Ø10/m over beams for the slabs, length one third of the span, in both directions.",
      "SLAB_TOP_OVER_BEAM = 5Ø10/m, extending L/3 (span) each side? / total? - 'بطول ثلث البحر' = length one third "
      "of the span; both directions", ["SUSPENDED_SLAB_SUPPORT_TOP"], P_FLOOR,
      "a drawn top bar on the plan ('/Top') overrides at that support; interaction with p.15 0.25L / 0.30L top "
      "extension is NOT stated", "CANDIDATE", arabic=True, topic="SLAB_TOP_SUPPORT",
      handles=["D8", "DA", "E1", "E3", "EA", "EC"], channels=["DXF_TEXT (legacy Arabic decoded)", "PDF_VECTOR"],
      values={"count_per_m": 5, "dia_mm": 10, "length_fraction_of_span": "1/3"}),
    # ------------------------------------------------------------------ p.9 schedules sheet
    R("P9-SOIL", 9, "١- منسوب الحفر لا يقل عن 1.5 م من منسوب ارض القسيمة الحالي / ٢- اجهاد التربة المصمم عليه 2.20 kg/cm2 "
                    "/ ٣- صممت الاساسات لتتحمل ارضي + اول + ثاني / ٤- مياه جوفية على عمق 4.5م",
      "Excavation >= 1.5 m below existing plot level; design soil stress 2.20 kg/cm2; foundations designed for "
      "GF + 1F + 2F; groundwater at 4.5 m depth.", "founding depth >= 1.5 m; q_allow 2.20 kg/cm2",
      ["FOOTING"], P_PROJECT, "none", "EXACT_RULE", arabic=True, topic="FOUNDATION",
      handles=["1E11", "1E12", "1B33", "1E10", "1E0E"], channels=["DXF_TEXT (legacy Arabic decoded)", "PDF_VECTOR"],
      values={"min_depth_m": 1.5, "q_allow_kg_cm2": 2.2, "groundwater_m": 4.5}),
    R("P9-COL-TIES", 9, "ST. OF COLUMN- 6Ø8/m", "Column ties Ø8, 6 per metre (all column types).",
      "COLUMN_TIE = Ø8 @ 6/m - per-metre count applies to a tie SET (all closed ties of the topology band) or to "
      "single ties: NOT stated", ["COLUMN"], P_PROJECT, "a twisted-column detail (p.15) adds spiral stirrups 6Ø8/m",
      "EXACT_RULE", topic="COLUMN_TIES", handles=["1BAA"], channels=["DXF_TEXT", "PDF_VECTOR"],
      values={"dia_mm": 8, "per_m": 6}),
    R("P9-COL-L", 9, "L=LENGTH OF COLUMN.", "L is the long side of the column section (tie topology selector).",
      "L = long section dimension", ["COLUMN"], P_PROJECT, "none", "EXACT_RULE", topic="COLUMN_TIES",
      handles=["1BA9"], channels=["DXF_TEXT"]),
    R("P9-COL-BAND-1", 9, "L≤ 50cm", "L ≤ 50 cm: one closed perimeter tie.", "TIE_L_LE_50: 1 closed tie",
      ["COLUMN"], P_TYPICAL, "none", "EXACT_RULE", topic="COLUMN_TIES", handles=["1BB5", "1BB4", "1BAB", "1BA8"],
      channels=["DXF_TEXT", "DXF_GEOMETRY", "PDF_VECTOR"]),
    R("P9-COL-BAND-2", 9, "50cm < L < 80cm", "50 < L < 80 cm: two overlapping closed ties.",
      "TIE_50_LT_L_LT_80: 2 overlapping closed ties", ["COLUMN"], P_TYPICAL,
      "L = 80 exactly is in no band (BOUNDARY_GAP)", "EXACT_RULE", topic="COLUMN_TIES",
      handles=["1BB8", "1BBA", "1BBF", "1BCA", "1BCB"], channels=["DXF_TEXT", "DXF_GEOMETRY", "PDF_VECTOR"]),
    R("P9-COL-BAND-3", 9, "80cm < L <120cm", "80 < L < 120 cm: two overlapping closed ties + one small central tie.",
      "TIE_80_LT_L_LT_120: 3 closed ties", ["COLUMN"], P_TYPICAL,
      "L = 80 exactly is in no band (BOUNDARY_GAP)", "EXACT_RULE", topic="COLUMN_TIES",
      handles=["1BE5", "1BE6", "1BB6", "1BD3", "1BDA", "1BD2", "1BE7", "1BE8"],
      channels=["DXF_TEXT", "DXF_GEOMETRY", "PDF_VECTOR"]),
    R("P9-COL-TMIN", 9, "H = HIEGHT OF FLOOR / T = THICKNESS OF COLUMN / H ≤ 4.3 m -> T min = 20 cm / 4.7 m ≥ H ≥ 4.3 m "
                        "-> T min = 25 cm / 5 m ≥ H ≥ 4.7 m -> T min = 30 cm",
      "Minimum column thickness by floor height.", "T_min(H): <=4.3 -> 20; 4.3..4.7 -> 25; 4.7..5.0 -> 30 (cm)",
      ["COLUMN"], P_PROJECT, "a check only - schedule sizes are not changed by the census",
      "EXACT_RULE", topic="COLUMN_SIZE_CHECK", handles=["1BEF", "1BF0", "1BF2", "1BF3", "1BF4", "1BF5", "1BF6", "1BF7"],
      channels=["DXF_TEXT", "PDF_VECTOR"]),
    # ------------------------------------------------------------------ p.10-12 schedules (typical notes)
    R("P10-SBT-REMARKS", 10, "REMARKS 2Ø12/30cm, 2Ø14/20cm, 2Ø16/20cm (+ box symbol)",
      "Beam schedule REMARKS give side bars per beam type (pairs at a vertical spacing); a box symbol marks some "
      "rows.", "SIDE_BARS per beam row (overrides P8-N21 for that row); box-symbol meaning not printed",
      ["SIMPLE_BEAM"], P_SCHEDULE, "row remark > project note 21", "CANDIDATE", topic="SIDE_BARS",
      channels=["DXF_TEXT", "PDF_VECTOR"]),
    R("P11-12-CB-TYPICAL", 11, "0.22 Ln / 0.3 Ln2 / 7.5cm / 0.15L (typical continuous-beam bar figure)",
      "Continuous-beam figure: support top bars to 0.22 Ln (0.3 Ln2 at an end span), first stirrup 7.5 cm, bottom "
      "bar stop 0.15 L.", "CB support-top extension 0.22Ln / 0.3Ln2; stirrup start 75 mm; bottom stop 0.15L",
      ["CONTINUOUS_BEAM"], P_TYPICAL, "per-row bars from the schedule", "CANDIDATE", topic="CB_TYPICAL",
      channels=["PDF_VECTOR", "DXF_GEOMETRY (C-BEAM template)"]),
    # ------------------------------------------------------------------ p.13
    R("P13-FOOTING-TYP", 13, "TYP. DETAIL OF ISOLATED FOOTING: Long bars / Short bars / Boxed bars / Min. 30cm / Max. 10cm "
                             "/ 40Ø / column stirrups in footing",
      "Isolated footing: bottom long + short bars, a BOXED bar cage, column starters with a minimum 30 cm foot, "
      "max 10 cm, 40Ø projection.", "FOOTING components: bottom long, bottom short, BOXED cage (semantics of "
                                     "'3+4' NOT printed), starter foot >= 30 cm, starter 40D",
      ["FOOTING"], P_TYPICAL, "schedule bars per type", "CANDIDATE", topic="FOOTING",
      channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P13-FOOTING-BOXED-BARS"),
    R("P13-FOOTING-DEEP", 13, "TYP. DETAIL OF ISOLATED FOOTING (WITH OUT BASEMENT) (When the level difference between "
                              "upper ground beam and footing is more than 2.5m) / أكثر من 2,5 م",
      "Where the upper ground beam is more than 2.5 m above the footing, an additional LOWER ground beam is "
      "provided.", "LOWER_GROUND_BEAM required if (upper GB level - footing level) > 2.5 m", ["GROUND_BEAM"],
      P_TYPICAL, "applies by founding depth (founding level BLOCKED)", "BLOCKED_METHOD", topic="GROUND_BEAMS",
      channels=["PDF_VECTOR"], r4_claim="P13-FOOTING-DEEP-LOWER-GB"),
    R("P13-GB-GT5", 13, "Ground Beams. More than 5m length without concentrated load: 3Ø16 top, Ø8/15cm, 3Ø16 + 3Ø16 "
                        "bottom, 30 wide x 60", "Ground beam > 5 m.", "GB_GT_5M: 30x60, top 3Ø16, bottom 2 rows "
                                                                    "3Ø16, links Ø8@150",
      ["GROUND_BEAM"], P_TYPICAL, "selection by span length (basis not printed: clear vs c/c)", "EXACT_RULE",
      topic="GROUND_BEAMS", channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P13-GB-GT5M"),
    R("P13-GB-LT5", 13, "Ground Beams. Less than 5m length: 3Ø14 top, Ø8/15cm, 3Ø14 + 3Ø14 bottom, 30 x 40",
      "Ground beam < 5 m.", "GB_LT_5M: 30x40, top 3Ø14, bottom 2 rows 3Ø14, links Ø8@150", ["GROUND_BEAM"],
      P_TYPICAL, "selection by span length", "EXACT_RULE", topic="GROUND_BEAMS", channels=["PDF_VECTOR", "OCR(R4)"],
      r4_claim="P13-GB-LT5M"),
    R("P13-GB-LT2_5", 13, "Ground Beams. Less than 2.5m length: 3Ø14 / 3Ø14 / 3Ø14, 30 x 30",
      "Ground beam < 2.5 m.", "GB_LT_2_5M: 30x30, 3Ø14 top + 2 x 3Ø14", ["GROUND_BEAM"], P_TYPICAL,
      "selection by span length", "CANDIDATE", topic="GROUND_BEAMS", channels=["PDF_VECTOR", "OCR(R4)"],
      r4_claim="P13-GB-LT2_5M-BARS"),
    R("P13-GB-EXT", 13, "Ground Beams for exterior walls: 3Ø16 top, 2Ø12/30cm sides, Ø8/15cm, 6Ø16 bottom, 30 wide, depth "
                        "FOLLOW ARCH. to the ground-floor slab level",
      "Ground beams under exterior walls (outer normal ground level to GF slab level).",
      "GB_EXTERIOR: 30 x (FOLLOW ARCH), top 3Ø16, bottom 6Ø16, side 2Ø12@300, links Ø8@150", ["GROUND_BEAM"],
      P_TYPICAL, "exterior selection by position on the building perimeter", "EXACT_RULE", topic="GROUND_BEAMS",
      channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P13-GB-EXTERIOR"),
    R("P13-LINTEL", 13, "LINTEL SCHEDULE: 0-100 B x 20 2Ø12/2Ø10 5Ø8/M; 101-200 B x 20 2Ø14/2Ø12; 201-300 B x 30 3Ø16/3Ø14; "
                        "301-500 B x 40 3Ø18/3Ø14; 501-750 B x 55 4Ø18/3Ø14; MIN.40cm bearing; B = block wall width",
      "Lintels by opening width; width = wall width; 40 cm minimum bearing each side.",
      "LINTEL(type by opening width) - occurrences come from the architectural openings, not the structural plans",
      ["LINTEL"], P_SCHEDULE, "none", "EXACT_RULE", topic="LINTELS", channels=["PDF_VECTOR", "OCR(R4)"],
      r4_claim="P13-LINTEL-SCHEDULE"),
    # ------------------------------------------------------------------ p.14
    R("P14-LIFT", 14, "DETAIL OF LIFT WITH ISOLATED FOOTING: walls 20 cm, 6Ø12/m + 6Ø16/m, 2Ø16, 2Ø12, AS PER SCHEDULE, "
                      "pit depth 'As Per Lift Manufactures recommendations'",
      "Lift pit on the FF raft: 20 cm walls with 6Ø12/m and 6Ø16/m, pit depth by the lift manufacturer.",
      "LIFT_PIT: walls 200 mm, 6Ø12/m + 6Ø16/m; depth BLOCKED (manufacturer)", ["LIFT_PIT"], P_TYPICAL,
      "none", "BLOCKED_METHOD", topic="LIFT", channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P14-LIFT-VALUES"),
    R("P14-BOUNDARY", 14, "TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 "
                          "STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12 (B.W); 130x80x30 pads",
      "Boundary wall typical detail.", "BOUNDARY_WALL typical (conflicts with schedule row B.W 20x60 4Ø16/2Ø14)",
      ["BOUNDARY_WALL"], P_TYPICAL, "schedule B.W row disagrees", "SOURCE_CONFLICT", topic="BOUNDARY_WALL",
      channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P14-BOUNDARY-WALL-TYPICAL"),
    R("P14-PARAPETS", 14, "TYPICAL DETAIL OF PARAPET SECTION / DETAIL OF PARAPET SECTION (5Ø12/m, 5Ø10/m, 6Ø10/m, 6Ø12/m; "
                          "30 x 130; 15/15 x 105)", "Parapet sections.", "PARAPET typical sections (applicability by "
                                                                          "architecture)",
      ["PARAPET"], P_TYPICAL, "plan note: check architectural parapet detail", "CANDIDATE", topic="PARAPETS",
      channels=["PDF_VECTOR"], r4_claim="P14-PARAPETS"),
    # ------------------------------------------------------------------ p.15
    R("P15-TEMP-TABLE", 15, "TEMPERATURE REINFORCEMENT SCHEDULE: 100 Y10@200; 125 Y10@200; 150 Y10@200; 175 Y12@200; "
                            "200 Y12@200; 250 Y12@200; 300 Y12@200",
      "Temperature reinforcement by slab thickness.", "TEMP(t): exact rows only; 160 / 180 mm are NOT rows -> "
                                                       "RULE_NOT_EXACT_MATCH (no interpolation)",
      ["SUSPENDED_SLAB"], P_TYPICAL, "never rounded to a neighbouring row", "EXACT_RULE", topic="TEMPERATURE",
      channels=["PDF_VECTOR", "OCR(R4)"], r4_claim="P15-TEMPERATURE-SCHEDULE",
      values={"rows": {100: "Y10@200", 125: "Y10@200", 150: "Y10@200", 175: "Y12@200", 200: "Y12@200",
                       250: "Y12@200", 300: "Y12@200"}}),
    R("P15-TEMP-NOTES", 15, "1. LAP LENGHT FOR ALL TEMPERATURE BARS SHALL BE 40xDIA. 2. WHERE BEAMS ARE PARALLEL TO MAIN SLAB "
                            "REINFORCEMENT PROVIDE TEMP. REINF. X 2000 TOP OF SLAB AT RIGHT ANGLES TO BEAMS. 1000 Ø "
                            "SPANDREL 3. WHERE TOP REINF. DIFFERS BETWEEN ADJACENT SPANS USE LAGER REINF.",
      "Temperature bars lap 40D; top temp bars x2000 across beams parallel to main bars (1000 at spandrels); use "
      "the larger top bars where adjacent spans differ.", "TEMP lap 40D; 2000 mm top strip over beams parallel to "
                                                          "main bars (1000 spandrel); max(top) at shared supports",
      ["SUSPENDED_SLAB"], P_TYPICAL, "none", "CANDIDATE", topic="TEMPERATURE", channels=["PDF_VECTOR", "OCR(R4)"],
      r4_claim="P15-TEMPERATURE-NOTES"),
    R("P15-SLAB-ON-BEAMS", 15, "TYP. SLAB ON BEAMS DETAIL: TOP ANCHOR BARS .25'L1' (non-continuous support); .30'L1' OR .30'L2' "
                               "WHICHEVER LARGER (continuous support); EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE "
                               "POSSIBLE; STOP 50% OF BOT. REINF. BALANCE CONTINUOUS .125'L1' / .125'L2'; 40 CL; 150; "
                               "BOTTOM BARS FOR SIZE & SPACING SEE SCHEDULE OR PLAN",
      "Slab-on-beam typical: top anchor 0.25 L1 at a non-continuous support; 0.30 x max(L1, L2) at a continuous "
      "support; 50% of top bars extend into the adjacent slab; 50% of bottom bars stop 0.125 L short of a "
      "continuous support, the balance continues.", "TOP_NONCONT=0.25L1; TOP_CONT=0.30max(L1,L2); BOT 50% stop "
                                                    "0.125L at continuous supports",
      ["SUSPENDED_SLAB"], P_TYPICAL, "plan bars / plan note 2 (5Ø10/m L/3) interaction NOT stated",
      "EXACT_RULE", topic="SLAB_CURTAILMENT", channels=["PDF_VECTOR", "OCR(R4)"],
      r4_claim="P15-SLAB-TOP-CONTINUOUS"),
    R("P15-TWISTED", 15, "TYP. DETAIL OF TWISTED COLUMN: COLUMN IN GROUND / COLUMN IN FIRST; 4Ø16 EXTRA; Spiral Stirrups "
                         "6Ø8/m; 1M above / 1M below", "Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side "
                                                       "of the floor, 4Ø16 extra.",
      "TURN_COLUMN extras: 4Ø16 + spiral 6Ø8/m over 2 x 1 m", ["TURN_COLUMN"], P_TYPICAL, "applies to T.C columns",
      "CANDIDATE", topic="SPECIAL_COLUMNS", channels=["PDF_VECTOR"], r4_claim="P15-TWISTED-CASEMENT"),
    R("P15-CASEMENT", 15, "BEAM IN CASEMENT WITH COLUMN: 6Ø8/m; 5Ø18; 120; AS PER PLAN", "Beam in casement with column.",
      "special beam-column casement detail (occurrence not marked on plans)", ["BEAM"], P_TYPICAL, "none",
      "CANDIDATE", topic="SPECIAL_BEAMS", channels=["PDF_VECTOR"]),
    R("P15-PLANTED", 15, "BEAM CARRYING PLANTED COL. DETAIL: 4Ø16; 100; DEPTH; STIRRUPS; 10 10",
      "Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.",
      "PLANTED_COLUMN support detail", ["PLANTED_COLUMN", "BEAM"], P_TYPICAL, "applies at P.C locations",
      "CANDIDATE", topic="SPECIAL_COLUMNS", channels=["PDF_VECTOR"], r4_claim="P15-PLANTED-COLUMN"),
    # ------------------------------------------------------------------ p.16
    R("P16-STAIR", 16, "TYPICAL STEEL LAYOUT-STAIR SECTION: 6Ø14/m, 8Ø16/m, 6Ø12/m, Ø12/20cm, Ø8/15, 1Ø12, 2Ø12, 4Ø16, "
                       "3Ø14, 2Ø14/30cm, 6Ø16/m; landing S.S.L +2.00; +4.00 / +3.95; TYPICAL DETAIL OF STAIR BEAM 2Ø12, "
                       "6Ø8/m, 4Ø16", "Typical stair and stair-beam reinforcement (N.T.S.).",
      "STAIR typical (applicability to each plan stair NOT established)", ["STAIR", "STAIR_BEAM"], P_TYPICAL,
      "plan stair bars (8Ø16/m) where printed", "BLOCKED_METHOD", topic="STAIRS", channels=["PDF_VECTOR"],
      r4_claim="P16-STAIR-TYPICAL"),
    R("P16-BEAM-OPENING", 16, "TYPICAL DETAIL FOR OPENING IN BEAM: 3 NO.Ø10 STIRR. AT 5cm c/c ADJACENT TO OPENING (EXTRA); "
                              "STIRR.Ø10/10cm ABOVE THE OPENING; 3Ø20 EXTRA; 20cm MIN. ABOVE; 35cm MAX; 15cm MIN. BELOW; "
                              "L=100cm Max", "Opening in beam detail.", "BEAM_OPENING extras (no opening marked on the "
                                                                         "plans)",
      ["BEAM"], P_TYPICAL, "applies where an opening exists", "CANDIDATE", topic="BEAM_OPENINGS",
      channels=["PDF_VECTOR"], r4_claim="P16-OPENING-RIBS"),
    R("P16-RIBS", 16, "TORSION STEEL FOR RIBS: A 30 4Ø16 6Ø8; B 35 4Ø16 7Ø8; C 40 4Ø16 8Ø8; D 45 4Ø18 8Ø10; E 50 6Ø16 9Ø10; "
                      "F 55 6Ø18 10Ø10; G 60 6Ø18 10Ø10", "Rib solid-part torsion steel.",
      "RIBS (no ribbed slab on the plans: legend only)", ["RIBBED_SLAB"], P_TYPICAL, "none", "CANDIDATE",
      topic="RIBS", channels=["PDF_VECTOR"]),
    # ------------------------------------------------------------------ p.7 + p.3
    R("P7-POOL", 7, "DETAIL OF SWIMMING POOL (N.I.S): 7Ø14/m, 7Ø12/m, 6Ø12/m, 12/20cm, Ø12/20cm, Ø10/20cm, 6Ø14/m, 3Ø16, "
                    "4Ø16; 5cm screed / 5cm insulation membrane / 10cm plain concrete; AS PER ARCH",
      "Swimming pool reinforcement (not in scope - N.I.S).", "POOL detail; dimensions 'AS PER ARCH'", ["POOL"],
      P_TYPICAL, "N.I.S label", "CANDIDATE", topic="POOL", channels=["DXF_TEXT", "PDF_VECTOR"]),
    R("P7-DOME", 7, "DETAIL OF DOME (N.I.S): Ø12MM/15cm (two layers); 10 cm; span 442; rise 190; ring beam 3Ø16 top, 8Ø8/m, "
                    "2Ø14/20cm, 3Ø18 bottom", "Dome reinforcement.", "DOME: shell 100 mm, Ø12@150 two layers; ring beam "
                                                                    "3Ø16/3Ø18, 2Ø14@200 sides, 8Ø8/m",
      ["DOME"], P_TYPICAL, "rise / span from the detail vs architecture", "CANDIDATE", topic="DOME",
      channels=["DXF_TEXT", "PDF_VECTOR"]),
    R("P3-GROUND-SLAB", 3, "5Ø10/m E.W. T=10cm (hatched circle symbol, twice on the ground-beam plan)",
      "Ground slab note: 10 cm, 5Ø10/m each way.", "GROUND_SLAB: t 100 mm, 5Ø10/m each way (extent of application "
                                                   "not drawn)", ["GROUND_SLAB"], P_FLOOR,
      "not covered by the 16 cm suspended-slab default", "CANDIDATE", topic="GROUND_SLAB",
      channels=["DXF_TEXT (TT1 block)", "PDF_VECTOR"], values={"t_mm": 100, "count_per_m": 5, "dia_mm": 10}),
    R("P3-LEGEND", 3, "LEGEND: Cantilever portion / Sunken slab / Bearing wall (B.W) / Planted column (P.C) / Foam "
                      "Concrete / Open To Below / Normal Slab Reinforcement / Corner Reinforcement / Extra Reinforcement "
                      "/ Cross Rib Reinforcement / Ribs Slab Reinforcement / Typical Boundary Wall; T.C turn column, "
                      "D.C dead column, P.C planted column, C.A cantilever, F.C false column, C.S change section",
      "Plan legend (pp.3-6).", "symbol vocabulary for the census", ["ALL_PLANS"], P_GENERAL, "none", "EXACT_RULE",
      topic="LEGEND", channels=["DXF_TEXT", "PDF_VECTOR"]),
]
