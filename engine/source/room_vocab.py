"""ROOM VOCABULARY V2 (T-022) - a room label's type, compound phrases before bare words (generic, bilingual).

    room_word(text) -> (code, matched)   drop-in for engine.source.arch_rooms.room_word (same contract)
    classify(text)  -> {"vocab", "text", "code", "kind", "wet", "status", "matched", "basis"}
    policy_record() -> the versioned vocabulary record (compound table + fallback lexicon id)

Why: arch_rooms.room_word (ROOM_VOCAB_V1, the lexicon of ARCH_ROOMS_V3) returns the FIRST lexicon entry that matches,
in list order. A compound name whose first word is itself a room word then takes that word's type:
    'حمام سباحة' (swimming pool)  -> BATHROOM (wet: porcelain, waterproofing) instead of POOL
    'swimming bath'                -> BATHROOM instead of POOL
    'حمام ماستر' (master bathroom) -> MASTER_BEDROOM (dry: the wet room is lost)
    'غسيل سيارات' (car wash)       -> LAUNDRY (wet) although it is not a laundry
    'مطبخ تحضيري' (prep kitchen)   -> KITCHEN instead of PANTRY
Rule (a proposal for the next knowledge version, not yet a registry rule): a label is read against the compound phrases first; among the compounds that
match, the LONGEST matched phrase wins (ties: table order). A compound may name no room (car wash): the label then
types nothing - its space stays UNLABELLED, i.e. held for review (arch_rooms._issues), never a guessed wet or dry
room. A label with no compound falls back to ROOM_VOCAB_V1 unchanged, so every label without a compound phrase keeps
its V1 type. A label that matches nothing returns (None, None) as before (UNLABELLED, held) - never a dry default.

ROOM_VOCAB_V1 (arch_rooms.LEXICON / room_word) is not changed: this module is reached only by callers that ask for
it (arch_rooms.spaces(vocab=VOCAB_ID)). Project-agnostic: Kuwait villa vocabulary, no project names. Stdlib only.
"""

from __future__ import annotations

import re

from engine.source import arch_rooms as AR
from engine.source import drawing_model as DM

VOCAB_ID = "ROOM_VOCAB_V2"
FALLBACK_ID = "ROOM_VOCAB_V1"           # arch_rooms.LEXICON (ARCH_ROOMS_V3), read through arch_rooms.room_word
MAX_LABEL_CHARS = 40                    # as V1: a note / title / sentence is not a room tag
_AL = r"(?:ال)?"                        # optional Arabic definite article

# (code or None, phrase, patterns on the normalized upper-case text, why). code None: a compound that names no room
# type of the lexicon - the label types nothing (held), whatever bare word it contains.
COMPOUNDS = (
    ("POOL", "swimming pool (Arabic: bath / basin / pond of swimming)",
     (rf"(حمام|حوض|بركة|بركه)\s*{_AL}سباح[ةه]",),
     "حمام سباحة is a swimming pool, not a bathroom: its first word is not the room it names"),
    ("POOL", "swimming bath / swimming pool",
     (r"SWIMMING\s*(BATH|POOL)",),
     "a swimming bath is a pool"),
    ("PLANT", "pool plant / pump / filter room",
     (r"(^|[^A-Z])(SWIMMING\s*)?POOL\s*(PUMP|PLANT|MACHINE|EQUIPMENT|FILTER|MECH)", rf"(غرفة\s*)?{_AL}مضخات",
      rf"(مضخة|مضخات|فلتر|فلاتر|معدات)\s*({_AL}(حمام|حوض|بركة|بركه)\s*)?{_AL}(مسبح|سباح[ةه])"),
     "the plant room of a pool is a service room, not the pool"),
    ("BATHROOM", "pool bathroom / shower / toilet",
     (rf"(حمام|دورة\s*مياه|دش|شاور)\s*{_AL}مسبح", r"(^|[^A-Z])POOL\s*(BATH|TOILET|SHOWER|W\.?\s*C)"),
     "the bathroom of a pool is a bathroom (wet)"),
    ("BATHROOM", "master bathroom",
     (rf"حمام\s*{_AL}ماستر", r"ماستر\s*(حمام|باث)", r"MASTER\s*(BATH|TOILET|SHOWER|W\.?\s*C)"),
     "حمام ماستر is the master bedroom's bathroom (wet), not the bedroom"),
    ("BATHROOM", "guest / maid / driver bathroom",
     (rf"(حمام|دورة\s*مياه)\s*{_AL}(ضيوف|خادم[ةه]|خدم|سائق|سواق)",
      r"(GUEST|MAID|DRIVER|SERVANT|NANNY)S?'?\s*(BATH|TOILET|SHOWER|W\.?\s*C)"),
     "a bathroom named after whom it serves is a bathroom"),
    ("PANTRY", "preparation kitchen",
     (rf"مطبخ\s*{_AL}تحضير(ي|ى)?", r"PREP(ARATION)?\.?\s*KITCHEN", r"KITCHEN\s*PREP"),
     "مطبخ تحضيري is the preparation kitchen (pantry, UP-PANTRY-001), not the main kitchen"),
    (None, "car wash",
     (rf"غسيل\s*{_AL}سيار(ات|ة|ه)", rf"مغسل[ةه]\s*{_AL}سيار(ات|ة|ه)", r"CAR\s*WASH"),
     "a car wash area is not a laundry: no room type is guessed (held for review)"),
)


def _compound(u):
    """-> (entry, matched text) of the longest matching compound phrase, or (None, None)."""
    best, best_len, best_txt = None, 0, None
    for entry in COMPOUNDS:
        for p in entry[2]:
            m = re.search(p, u)
            if m and len(m.group(0).strip()) > best_len:      # longest phrase first; ties keep table order
                best, best_len, best_txt = entry, len(m.group(0).strip()), m.group(0).strip()
    return best, best_txt


def classify(text):
    """the type of one label text: status TYPED (a room code), HELD_COMPOUND (a compound naming no room type: held),
    NO_ROOM_WORD (nothing matched: held as an unlabelled space, never dry) or NOT_A_TAG (longer than a room tag)."""
    u = DM.normalize(text or "").upper()
    rec = {"vocab": VOCAB_ID, "text": text, "code": None, "kind": None, "wet": None, "matched": None}
    if not u:
        return dict(rec, status="NO_ROOM_WORD", basis="empty")
    if len(u) > MAX_LABEL_CHARS:
        return dict(rec, status="NOT_A_TAG", basis=f"longer than {MAX_LABEL_CHARS} characters")
    entry, txt = _compound(u)
    if entry is not None:
        code, phrase, _p, why = entry
        if code is None:
            return dict(rec, status="HELD_COMPOUND", matched=txt, basis=f"compound '{phrase}': {why}")
        code_, basis = code, f"compound '{phrase}': {why}"
    else:
        code_, txt = AR.room_word(text or "")
        if not code_:
            return dict(rec, status="NO_ROOM_WORD", basis="no room word (held as an unlabelled space)")
        basis = f"{FALLBACK_ID} word"
    kind = AR.LEX[code_][2]
    from engine.source import knowledge as K
    return dict(rec, code=code_, kind=kind, wet=code_ in K.wet_codes(), status="TYPED", matched=txt, basis=basis)


def room_word(text):
    """-> (code, matched): same contract as arch_rooms.room_word; compound phrases first (longest first), then V1."""
    u = DM.normalize(text or "").upper()
    if len(u) > MAX_LABEL_CHARS:
        return None, None
    entry, txt = _compound(u)
    if entry is not None:
        return (entry[0], txt) if entry[0] else (None, None)
    return AR.room_word(text or "")


def policy_record():
    return {"id": VOCAB_ID, "fallback": FALLBACK_ID, "rule": "compound phrases before bare words; the longest "
            "matched compound wins (ties: table order); a compound naming no room types nothing (held); no compound "
            "-> the V1 lexicon unchanged; nothing matched -> no code (UNLABELLED, held), never a dry default",
            "max_label_chars": MAX_LABEL_CHARS,
            "compounds": [{"code": c, "phrase": ph, "patterns": list(ps), "why": w} for c, ph, ps, w in COMPOUNDS]}
