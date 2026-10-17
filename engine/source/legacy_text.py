"""LEGACY CAD TEXT DECODING (V3) - Arabic written with legacy AutoCAD SHX fonts.

Old Arabic AutoCAD fonts do not store Unicode. The DXF holds Latin / cp1252 code points and the SHX font draws an
Arabic glyph for each of them, so a reader that ignores the font sees "HMam" where the drawing shows حمام. Two
font families are common in Gulf drawings and are decoded here:

    ARABIC_KEYBOARD_101  xarb / ar*.shx style fonts: the code point is the key of the Arabic (101) keyboard that
                         produces the letter; upper-case keys are the same letter (alternate glyph form), "_" is the
                         tatweel and "{" / "}" alternate forms of ج / د
    XARAB_GLYPH_V1       the X-ARAB / X-ARAB1B / X-ARABIC1 SHX family: one code point per glyph form

decode(value, font) -> {"text", "family", "unknown": [code points not in the table], "state"}.
font_family(font_file) -> the family for a text style's font file (or None: not a legacy Arabic font).

The glyph table is font knowledge, not project knowledge: it was derived from bilingual tag pairs (an English room
word and its Arabic twin in the same tag), and every entry lists the evidence that supports it. A code point that
is not in the table is never guessed: the decode state is PARTIAL and the code point is reported.

corroborate(english, arabic) checks a decoded Arabic text against the bilingual room lexicon: CORROBORATED when the
Arabic term of the English room word is found, NOT_CORROBORATED otherwise. Decoded Arabic never establishes a room
on its own; it corroborates or names (bilingual report) a room the English tag or geometry already establishes.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import re
import unicodedata

POLICY_ID = "LEGACY_CAD_TEXT_DECODE_V1"
ARABIC_KEYBOARD_101, XARAB_GLYPH = "ARABIC_KEYBOARD_101", "XARAB_GLYPH_V1"
DECODED, PARTIAL, NOT_LEGACY = "DECODED", "PARTIAL_DECODE", "NOT_A_LEGACY_ARABIC_FONT"
TATWEEL = ""

# Arabic (101) keyboard: key -> letter (unshifted layer). Upper-case keys are the alternate (final / isolated) glyph
# of the same letter in the xarb font family.
KEYBOARD_101 = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف", "y": "غ", "u": "ع", "i": "ه", "o": "خ", "p": "ح",
    "[": "ج", "]": "د", "a": "ش", "s": "س", "d": "ي", "f": "ب", "g": "ل", "h": "ا", "j": "ت", "k": "ن",
    "l": "م", ";": "ك", "'": "ط", "z": "ئ", "x": "ء", "c": "ؤ", "v": "ر", "b": "لا", "n": "ى", "m": "ة",
    ",": "و", ".": "ز", "/": "ظ", "`": "ذ", "{": "ج", "}": "د", "_": TATWEEL, " ": " "}

# X-ARAB SHX family: code point -> letter. evidence = bilingual tag pairs (English word / Arabic word) in which the
# glyph occurs with that reading; every entry is corroborated by at least one pair.
XARAB = {
    "A": ("ا", "RECEPTION/استقبال, FIRST/الأول, NORTH/شمالية"), "a": ("ا", "BATH/حمام, SALOON/صالون"),
    "B": ("ب", "RECEPTION/استقبال, KITCHEN/مطبخ"), "C": ("ث", "SECOND/الثاني"),
    "D": ("ش", "LIVING/معيشة, STREET/شارع"), "E": ("ض", "PANTRY/تحضير, GROUND/الأرضي"), "e": ("ض", "W.C/مرحاض"),
    "F": ("ف", "MASTER BED ROOM/غرفة, HORIZONTAL/أفقي"), "G": ("خ", "MAID/خادمة"), "¢": ("خ", "KITCHEN/مطبخ"),
    "H": ("ح", "BATH/حمام, PANTRY/تحضير, GARDEN/حديقة"), "h": ("ح", "ROOF/سطح"),
    "I": ("ع", "DINING/طعام"), "P": ("ع", "LIVING/معيشة"), "p": ("ع", "STREET/شارع"), "J": ("ج", "NEIGHBOUR/جار, ELEVATION/واجهة"),
    "L": ("ل", "RECEPTION/استقبال, SALOON/صالون"), "l": ("ل", "LAUNDRY/غسيل, FIRST/الأول"),
    "M": ("م", "BATH/حمام, KITCHEN/مطبخ"), "m": ("م", "BATH/حمام"), "²": ("م", "DINING/طعام, MASTER BED ROOM/نوم"),
    "N": ("ن", "VOID/منور, DEWANEYA/ديوانية"), "n": ("ن", "SALOON/صالون"),
    "O": ("غ", "LAUNDRY/غسيل, WASH/مغسلة"), "Q": ("ق", "RECEPTION/استقبال, GARDEN/حديقة"), "\x90": ("ق", "FLOOR/للطابق"),
    "R": ("ص", "SALOON/صالون"), "S": ("س", "LAUNDRY/غسيل, ROOF/سطح"), "T": ("ه", "ELEVATION/واجهة"),
    "t": ("ة", "MASTER BED ROOM/غرفة, ELEVATION/واجهة"), "y": ("ة", "LIVING/معيشة, WASH/مغسلة"),
    "V": ("ت", "RECEPTION/استقبال, PANTRY/تحضير"), "W": ("لأ", "FIRST/الأول, GROUND/الأرضي"),
    "X": ("ئ", "MASTER BED ROOM/رئيسية"), "Z": ("ي", "LAUNDRY/غسيل, DEWANEYA/ديوانية"), "z": ("ي", "HORIZONTAL/أفقي"),
    "‘": ("و", "SALOON/صالون, VOID/منور"), "—": ("ر", "W.C/مرحاض, VOID/منور"), "“": ("ط", "KITCHEN/مطبخ, DINING/طعام"),
    "™": ("د", "DEWANEYA/ديوانية, GARDEN/حديقة"), "‚": (TATWEEL, "EAST/شرقية (kashida)"), "_": (TATWEEL, "MAID/خادمة (kashida)"),
    " ": (" ", "word space")}

FONT_FAMILIES = (("X-ARAB", XARAB_GLYPH), ("XARAB", XARAB_GLYPH), ("XARB", ARABIC_KEYBOARD_101),
                 ("ARABIC101", ARABIC_KEYBOARD_101))

# generic bilingual room lexicon: English room word -> accepted Arabic terms (normalised)
LEXICON = {
    "BATH": ("حمام",), "BATHROOM": ("حمام",), "KITCHEN": ("مطبخ",), "LIVING": ("معيشة", "صالة"),
    "MAID": ("خادمة", "غرفة خادمة"), "WC": ("مرحاض", "دورة مياه", "حمام"), "WASH": ("مغسلة", "مغاسل"),
    "LAUNDRY": ("غسيل",), "RECEPTION": ("استقبال",), "DINING": ("طعام",), "DEWANEYA": ("ديوانية",),
    "DIWANIYA": ("ديوانية",), "COURT": ("حوش",), "SALOON": ("صالون",), "SALON": ("صالون",), "PANTRY": ("تحضير",),
    "VOID": ("منور", "فراغ"), "ROOF": ("سطح",), "DRIVER": ("سائق",), "GARDEN": ("حديقة",),
    "POOL": ("حمام سباحة", "مسبح"), "SWIMMING": ("حمام سباحة", "سباحة"), "MASTER": ("رئيسية",),
    "BED": ("نوم",), "BEDROOM": ("غرفة نوم", "نوم"), "STAIR": ("درج", "سلم"), "STORE": ("مخزن",),
    "CORRIDOR": ("ممر", "طرقة"), "ENTRANCE": ("مدخل",), "NEIGHBOUR": ("جار",), "STREET": ("شارع",)}


def font_family(font_file) -> str | None:
    """The legacy Arabic family of a text style's font file name, or None."""
    f = re.sub(r"[^A-Z0-9-]", "", (font_file or "").upper().rsplit("\\", 1)[-1].rsplit("/", 1)[-1].replace(".SHX", ""))
    for prefix, fam in FONT_FAMILIES:
        if f.startswith(prefix):
            return fam
    return None


def decode(value, family) -> dict:
    if family not in (ARABIC_KEYBOARD_101, XARAB_GLYPH):
        return {"text": value, "family": family, "unknown": [], "state": NOT_LEGACY}
    out, unknown = [], []
    for ch in value or "":
        if family == ARABIC_KEYBOARD_101:
            k = ch.lower() if ch.isalpha() and ch.isascii() else ch
            if k in KEYBOARD_101:
                out.append(KEYBOARD_101[k])
                continue
        else:
            if ch in XARAB:
                out.append(XARAB[ch][0])
                continue
        unknown.append(ch)
        out.append("?")
    text = re.sub(r" {2,}", " ", "".join(out)).strip()
    return {"text": text, "family": family, "unknown": sorted(set(unknown)),
            "state": DECODED if not unknown else PARTIAL}


def normalise(ar) -> str:
    """Arabic comparison form: hamza-alef variants -> ا, ى -> ي, no tatweel / diacritics / spaces."""
    s = unicodedata.normalize("NFKC", ar or "")
    s = re.sub("[ً-ْـ]", "", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    return re.sub(r"\s+", "", s)


def corroborate(english, arabic) -> dict:
    words = [w for w in re.findall(r"[A-Z]+", (english or "").upper().replace("W.C", "WC"))]
    terms = sorted({t for w in words for t in LEXICON.get(w, ())})
    a = normalise(arabic)
    hit = [t for t in terms if normalise(t) in a]
    if not terms:
        return {"state": "NO_LEXICON_ENTRY", "english_words": words}
    return {"state": "CORROBORATED" if hit else "NOT_CORROBORATED", "matched": hit, "expected_any_of": terms}


def policy_record() -> dict:
    return {"id": POLICY_ID, "families": {ARABIC_KEYBOARD_101: "xarb-style SHX fonts (Arabic 101 keyboard keys)",
                                          XARAB_GLYPH: "X-ARAB SHX family (one code point per glyph form)"},
            "xarab_table": {k: {"letter": v[0], "evidence": v[1]} for k, v in sorted(XARAB.items())},
            "keyboard_table": dict(sorted(KEYBOARD_101.items())),
            "rule": "a code point not in the table is reported, never guessed; decoded Arabic corroborates or names a "
                    "room that English / geometry already establishes - it never establishes one on its own",
            "lexicon": {k: list(v) for k, v in sorted(LEXICON.items())}}
