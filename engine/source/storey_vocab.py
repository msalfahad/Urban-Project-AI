"""STOREY VOCABULARY V1 (T-029) - which storey a floor-plan title names, bilingual, ordered by level (generic).

    storey_of_title(text) -> (storey id, order, basis) or (None, None, None)
    plan_like(text)       -> True when the text reads as a plan title (PLAN / مسقط / a storey word) but is not a
                             section, elevation, site, location, detail, schedule or key plan title
    classify(text)        -> {"vocab", "text", "storey", "order", "status", "basis"}
                             status RECOGNISED | HELD_UNRECOGNISED (plan-like, no storey) | NOT_A_PLAN | NOT_A_TITLE
    policy_record()       -> the versioned vocabulary record

Why (T-018 P-05): arch_plan.FLOOR_TITLES (ARCH_PLAN_V1) knows BASEMENT / GF / MEZZANINE / 1F / 2F / 3F / ROOF in a
few spellings only. A frame titled '1ST FL. PLAN', '4TH FLOOR PLAN', 'الدور الرابع', 'الطابق الأول' or 'الدور الاول'
(alef without hamza, the common CAD spelling) is not a floor plan for it: every room, wall, opening and finish on
that sheet is silently not measured.

Rule of this vocabulary:
  1 ARCH_PLAN_V1 first: a title arch_plan.floor_of_title recognises keeps exactly that storey id (frozen methods and
    every drawing read so far are unchanged); only the order numbers are this vocabulary's own (below).
  2 Otherwise the storey table below, on the normalized text (Arabic alef / yaa / taa-marbuta forms folded, tatweel
    and diacritics removed): English ordinal words and numerals FIRST .. TENTH / 1ST .. 10TH with FLOOR or FL. and
    PLAN; Arabic الدور / الطابق + ordinal word الأول .. العاشر, not followed by عشر (a teen ordinal is not 1F-10F
    here; a text V1 already reads, e.g. 'الدور الثاني عشر' -> 2F, keeps its V1 reading by step 1).
  3 A text that reads as a plan title but names no storey of the table (PENTHOUSE PLAN, LEVEL 00, 'الدور 4',
    '2ND BASEMENT PLAN' ...) is HELD_UNRECOGNISED: the caller holds the sheet (reason UNRECOGNISED_FLOOR_TITLE) for
    review - never dropped, never placed on a guessed storey. Conventions with more than one reading (is LEVEL 00 the
    ground floor or LEVEL 01? is a penthouse the roof annex?) are not decided here.
Order numbers (V1 vocabulary only; comparisons between regions of one run): BASEMENT 0, GF 10, MEZZANINE 15,
nF 10 + 10 n (1F 20 ... 10F 110), ROOF 1000. Project-agnostic: no project names or layers. Stdlib only.
"""

from __future__ import annotations

import re

from engine.source import drawing_model as DM

VOCAB_ID = "STOREY_VOCAB_V1"
FALLBACK_ID = "ARCH_PLAN_V1"            # arch_plan.FLOOR_TITLES / floor_of_title, read first and unchanged
HELD_REASON = "UNRECOGNISED_FLOOR_TITLE"
MAX_TITLE_CHARS = 60                    # a longer text is a note or a sentence, not a sheet title (held test only)

_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ـ": None})
_DIACRITICS = re.compile("[ً-ْٰ]")
_FL = r"(FLOOR|FL\.?)"
_PLAN = r"\s*PLAN"
_AR_STOREY = r"(الدور|الطابق)\s*"
_EN_ORD = ("FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH", "TENTH")
_EN_SUF = ("ST", "ND", "RD", "TH", "TH", "TH", "TH", "TH", "TH", "TH")
_AR_ORD = ("الاول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر")
_NOT_TEEN = r"(?!\s*عشر)"               # 'الثاني عشر' is the twelfth, not the second


def _numbered():
    out = []
    for n in range(1, 11):
        w, suf, ar = _EN_ORD[n - 1], _EN_SUF[n - 1], _AR_ORD[n - 1]
        out.append((f"{n}F", 10 + 10 * n,
                    (rf"(^|[^A-Z]){w}\.?\s*{_FL}{_PLAN}", rf"(^|[^0-9]){n}\s*{suf}\.?\s*{_FL}{_PLAN}"),
                    (rf"{_AR_STOREY}{ar}{_NOT_TEEN}",)))
    return tuple(out)


# (storey id, order, English patterns, Arabic patterns) on the normalized, folded, upper-case text
STOREYS = (
    ("BASEMENT", 0, (rf"BASEMENT\s*{_FL}?{_PLAN}",), (r"السرداب", r"القبو", r"البدروم")),
    ("GF", 10, (rf"GROUND\s*{_FL}{_PLAN}", r"(^|[^A-Z])G\.?\s*F\.?\s*PLAN"), (rf"{_AR_STOREY}الارضي",)),
    ("MEZZANINE", 15, (rf"MEZZ?ANINE\s*({_FL}|LEVEL)?{_PLAN}",), (r"الميزانين", r"الميزانيين", r"الميزنين")),
) + _numbered() + (
    ("ROOF", 1000, (rf"(TOP\s*)?ROOF\s*(TOP\s*)?(ANNEX\s*)?{_FL}?{_PLAN}", rf"(^|[^A-Z])ANNEX\s*{_FL}?{_PLAN}"),
     (r"مسقط\s*السطح", r"الملحق")),
)
ORDER = {sid: order for sid, order, _e, _a in STOREYS}

# a plan title: these words, in a text that is short enough to be a title
PLAN_WORDS = (r"(^|[^A-Z])PLAN($|[^A-Z])", r"مسقط", r"(^|\s)(الدور|الطابق)($|\s)", r"(^|[^A-Z])MEZZ?ANINE",
              r"(^|[^A-Z])PENTHOUSE", r"(^|[^A-Z])BASEMENT", r"^LEVEL\s*[-+]?\d{1,2}(?![\d.,])",
              r"الميزانين", r"السرداب", r"الملحق")
# never a floor plan, even when the word PLAN is in it (ARCH_PLAN_V1 NOT_A_PLAN + detail / schedule / key plan)
NOT_A_PLAN = (r"ELEVATION", r"SECTION", r"SITE\s*PLAN", r"LOCATION", r"KEY\s*PLAN", r"DETAIL", r"SCHEDULE",
              r"واجهة", r"قطاع", r"الموقع", r"تفاصيل", r"تفصيل", r"جدول")
# the patterns are matched on folded text, so they are folded the same way (e.g. واجهة -> واجهه)
STOREYS = tuple((sid, order, en, tuple(p.translate(_FOLD) for p in ar)) for sid, order, en, ar in STOREYS)
PLAN_WORDS = tuple(p.translate(_FOLD) for p in PLAN_WORDS)
NOT_A_PLAN = tuple(p.translate(_FOLD) for p in NOT_A_PLAN)


def fold(text):
    """normalized (drawing_model.normalize), Arabic letter forms folded, diacritics removed, upper case."""
    return _DIACRITICS.sub("", DM.normalize(text).translate(_FOLD)).upper()


def _table(u):
    for sid, order, en, ar in STOREYS:
        for p in en + ar:
            if re.search(p, u):
                return sid, order, p
    return None, None, None


def storey_of_title(text):
    """-> (storey id, order, basis): ARCH_PLAN_V1 first (same id as today), then the storey table."""
    from engine.source import arch_plan as AP          # lazy: arch_plan reaches this module only on request
    fl, _o = AP.floor_of_title(text)
    if fl:
        return fl, ORDER[fl], FALLBACK_ID
    sid, order, pat = _table(fold(text))
    if sid:
        return sid, order, f"{VOCAB_ID}:{pat}"
    return None, None, None


def plan_like(text):
    u = fold(text)
    if not u or len(u) > MAX_TITLE_CHARS:
        return False
    if any(re.search(p, u) for p in NOT_A_PLAN):
        return False
    return any(re.search(p, u) for p in PLAN_WORDS)


def classify(text):
    sid, order, basis = storey_of_title(text)
    if sid:
        status = "RECOGNISED"
    elif plan_like(text):
        status, basis = "HELD_UNRECOGNISED", HELD_REASON
    elif any(re.search(p, fold(text)) for p in NOT_A_PLAN):
        status = "NOT_A_PLAN"
    else:
        status = "NOT_A_TITLE"
    return {"vocab": VOCAB_ID, "text": text, "storey": sid, "order": order, "status": status, "basis": basis}


def policy_record():
    return {"id": VOCAB_ID, "fallback": FALLBACK_ID, "held_reason": HELD_REASON, "max_title_chars": MAX_TITLE_CHARS,
            "storeys": [{"storey": sid, "order": order, "english": list(en), "arabic": list(ar)}
                        for sid, order, en, ar in STOREYS],
            "plan_words": list(PLAN_WORDS), "not_a_plan": list(NOT_A_PLAN),
            "never": ["a plan-like title placed on a guessed storey", "a plan-like sheet dropped without a record",
                      "a storey id of ARCH_PLAN_V1 changed"]}
