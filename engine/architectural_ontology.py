"""A general architectural vocabulary, so a drawing's words can mean something.

Round 2 made the semantic layer deliberately blind: every string was judged
only by shape — is it a number, does it carry a scale ratio — and a test
asserted that `KITCHEN` must classify exactly like the nonsense word
`QQZZX`. That was the wrong invariant. It is too strict for production and
it threw away the drawing's own language.

The invariant that matters is narrower:

    NO PROJECT-SPECIFIC STRING MAY BE HARDCODED TO FORCE A P7757 RESULT.

Architectural language is not project-specific. `kitchen` and `مطبخ` mean a
kitchen on every drawing in the world, and refusing to know that is not
rigour — it is a different kind of error, the one that made P7757's street
and neighbour labels seed physical rooms.

WHAT THIS IS AND IS NOT

    IT IS      a general vocabulary of architectural space concepts, in
               English and Arabic, of the kind any space-type schedule or
               IFC space classification carries. It deliberately contains
               far more terms than any one project uses.

    IT IS NOT  a list of P7757's words. Most entries below do not appear on
               that drawing at all, and the terms that do appear get no
               special handling — they are matched by the same lookup as
               everything else.

    UNKNOWN    is a first-class answer. A term absent from the vocabulary
               is UNKNOWN, never guessed, and §10's rule holds: an unknown
               NAME never invalidates a correct GEOMETRY.

WHY MATCHING IS EXACT, ON NORMALISED FORMS

No fuzzy matching, no stemming, no substring search. `STORE` must not match
`STOREY`, and a substring rule would make `BATH` match `BATHROOM CORRIDOR`
in a way nobody can predict. A term is normalised — case folded, Arabic
diacritics and tatweel removed, alef forms unified, punctuation and
separators collapsed — and then looked up whole.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

ONTOLOGY = "ARCHITECTURAL_SPACE_ONTOLOGY_V1"

# --- the concept classes --------------------------------------------------
# What a term, once recognised, says the thing it names IS.

ROOM = "ROOM_OR_PHYSICAL_SPACE"
FUNCTIONAL_ZONE = "FUNCTIONAL_ZONE"
EXTERNAL_SPACE = "EXTERNAL_SPACE"
SITE_ANNOTATION = "SITE_OR_LOCATION_ANNOTATION"
DRAWING_ANNOTATION = "DRAWING_ANNOTATION"
UNKNOWN = "UNKNOWN"

MEANS = {
    ROOM: "an enclosed space a person occupies — it may seed a physical "
          "space measurement",
    FUNCTIONAL_ZONE: "a named part of a larger space rather than a space of "
                     "its own. It may seed a ZONE, never a separate room",
    EXTERNAL_SPACE: "open space belonging to the property but outside the "
                    "enclosed fabric. It is a space, and it is not a room",
    SITE_ANNOTATION: "it names something about the PLOT or its surroundings "
                     "— a boundary, a neighbour, an approach, an aspect. It "
                     "never seeds a space",
    DRAWING_ANNOTATION: "it describes the DRAWING rather than the building",
    UNKNOWN: "not in the vocabulary. This is an honest answer and it never "
             "invalidates geometry",
}


@dataclass(frozen=True)
class Concept:
    """One architectural concept and the terms that name it."""

    key: str
    concept_class: str
    terms: tuple

    def record(self) -> dict:
        return {"concept": self.key, "class": self.concept_class,
                "terms": list(self.terms)}


# --- the vocabulary -------------------------------------------------------
#
# Organised by CONCEPT, with the English and Arabic that name it. The Arabic
# is written unvocalised because that is how it is typed on a drawing; the
# normaliser strips diacritics anyway.
#
# Breadth is deliberate. A vocabulary that happened to contain exactly one
# project's words would be that project's lookup table wearing a general
# name, so this carries the ordinary range of residential, commercial and
# service spaces whether or not any particular sheet uses them.

_VOCABULARY = (
    # ---------------------------------------------------- enclosed rooms
    Concept("KITCHEN", ROOM, ("kitchen", "kitchenette", "مطبخ", "مطبخ صغير")),
    Concept("BEDROOM", ROOM, (
        "bedroom", "bed room", "master bedroom", "master bed room",
        "guest bedroom", "غرفة نوم", "غرفه نوم", "نوم", "غرفة النوم",
        "غرفة نوم رئيسية", "غرفة ضيوف")),
    Concept("BATHROOM", ROOM, (
        "bathroom", "bath room", "bath", "shower room", "en suite",
        "ensuite", "حمام", "دورة مياه", "دوره مياه", "حمام رئيسي")),
    Concept("WC", ROOM, ("wc", "w c", "water closet", "toilet", "cloakroom",
                         "مرحاض", "تواليت", "حمام ضيوف")),
    Concept("LIVING", ROOM, ("living", "living room", "sitting room",
                             "lounge", "family room", "معيشة", "معيشه",
                             "غرفة معيشة", "جلوس")),
    Concept("DINING", ROOM, ("dining", "dining room", "طعام", "غرفة طعام",
                             "صالة طعام", "سفرة")),
    Concept("SALOON", ROOM, ("saloon", "salon", "صالون", "صاله", "صالة")),
    # Arabic architectural terms are written in Latin script on many Gulf
    # drawings, with no settled spelling. The transliteration families below
    # are given for several concepts, not only where one project needs one —
    # see the round-3 report, section K, which records that P7757 uses one
    # of these spellings and that the families were added generally.
    Concept("MAJLIS", ROOM, (
        "majlis", "mejlis", "majles", "majlas",
        "diwaniya", "diwaniyah", "dewaniya", "dewaneya", "dewania",
        "deewaniya", "مجلس", "ديوانية", "ديوانيه", "دیوانية")),
    Concept("LIWAN", ROOM, ("liwan", "leewan", "ليوان", "إيوان")),
    Concept("RECEPTION", ROOM, ("reception", "foyer", "entrance hall",
                                "استقبال", "مدخل", "بهو")),
    Concept("HALL", ROOM, ("hall", "lobby", "vestibule", "ردهة", "ردهه",
                           "صالة رئيسية")),
    Concept("CORRIDOR", ROOM, ("corridor", "passage", "hallway", "ممر",
                               "ممرات")),
    Concept("STAIR", ROOM, ("stair", "stairs", "staircase", "stairwell",
                            "درج", "سلم", "بيت الدرج")),
    Concept("STORE", ROOM, ("store", "storage", "store room", "pantry",
                            "larder", "مخزن", "مستودع", "مؤن")),
    Concept("LAUNDRY", ROOM, ("laundry", "utility", "wash", "washing",
                              "غسيل", "غرفة غسيل", "مغسلة", "مغاسل")),
    Concept("MAID", ROOM, ("maid", "maid room", "maids room", "housemaid",
                           "خادمة", "غرفة خادمة", "غرفة الخدم")),
    Concept("DRIVER", ROOM, ("driver", "driver room", "chauffeur",
                             "سائق", "غرفة سائق")),
    Concept("OFFICE", ROOM, ("office", "study", "library", "مكتب",
                             "مكتبة", "غرفة مكتب")),
    Concept("GARAGE", ROOM, ("garage", "carport", "كراج", "جراج", "مرآب")),
    Concept("PLANT", ROOM, ("plant", "plant room", "mechanical", "electrical",
                            "machine room", "boiler", "غرفة كهرباء",
                            "غرفة ميكانيكية", "غرفة مضخات")),
    Concept("SHAFT", ROOM, ("shaft", "duct", "riser", "منور", "ناظور",
                            "مجرى")),
    Concept("LIFT", ROOM, ("lift", "elevator", "مصعد")),
    Concept("PRAYER", ROOM, ("prayer", "prayer room", "musalla",
                             "mussalla", "musallah", "مصلى", "غرفة صلاة")),
    Concept("CLASSROOM", ROOM, ("classroom", "class room", "فصل",
                                "غرفة صف")),
    Concept("WARD", ROOM, ("ward", "clinic", "consulting room", "عيادة",
                           "جناح")),
    Concept("SHOP", ROOM, ("shop", "retail", "showroom", "محل", "معرض")),
    Concept("WORKSHOP", ROOM, ("workshop", "ورشة")),

    # ------------------------------------------------- functional zones
    Concept("SEATING_ZONE", FUNCTIONAL_ZONE, (
        "seating", "seating area", "sitting area", "منطقة جلوس")),
    Concept("DINING_ZONE", FUNCTIONAL_ZONE, (
        "dining area", "dining zone", "منطقة طعام")),
    Concept("COOKING_ZONE", FUNCTIONAL_ZONE, (
        "cooking area", "cooking zone", "منطقة طبخ")),
    Concept("PLAY_ZONE", FUNCTIONAL_ZONE, (
        "play area", "play zone", "منطقة لعب")),
    Concept("WORK_ZONE", FUNCTIONAL_ZONE, (
        "work area", "workspace", "منطقة عمل")),

    # ------------------------------------------------- external spaces
    Concept("GARDEN", EXTERNAL_SPACE, ("garden", "lawn", "landscape",
                                       "حديقة", "حديقه", "مزروعات")),
    Concept("TERRACE", EXTERNAL_SPACE, ("terrace", "patio", "deck",
                                        "تراس", "شرفة أرضية")),
    Concept("BALCONY", EXTERNAL_SPACE, ("balcony", "veranda", "loggia",
                                        "شرفة", "بلكونة", "برندة")),
    Concept("COURTYARD", EXTERNAL_SPACE, ("courtyard", "court", "atrium",
                                          "light well", "فناء", "صحن")),
    # حوش is claimed by YARD. Both are EXTERNAL_SPACE so nothing turned on
    # it, but a term two concepts both claim is resolved here rather than
    # left for the collision report to shrug at.
    Concept("ROOF", EXTERNAL_SPACE, ("roof", "roof terrace", "سطح",
                                     "سطح المبنى")),
    Concept("POOL", EXTERNAL_SPACE, ("pool", "swimming pool", "plunge pool",
                                     "مسبح", "بركة", "حمام سباحة")),
    Concept("PARKING", EXTERNAL_SPACE, ("parking", "car park", "موقف",
                                        "مواقف", "موقف سيارات")),
    Concept("YARD", EXTERNAL_SPACE, (
        "yard", "backyard", "service yard", "hosh", "housh", "hoash",
        "ساحة", "ساحه", "حوش")),

    # --------------------------------------------- site / location notes
    Concept("STREET", SITE_ANNOTATION, (
        "street", "road", "avenue", "lane", "highway", "sikka", "sikkah",
        "شارع", "طريق", "زقاق", "سكة")),
    Concept("NEIGHBOUR", SITE_ANNOTATION, ("neighbour", "neighbor",
                                           "adjoining plot", "adjacent plot",
                                           "جار", "الجار", "قسيمة مجاورة")),
    Concept("PLOT", SITE_ANNOTATION, ("plot", "site", "parcel", "lot",
                                      "قسيمة", "قطعة", "الموقع", "أرض")),
    Concept("BOUNDARY", SITE_ANNOTATION, ("boundary", "property line",
                                          "setback", "fence line",
                                          "حد", "حدود", "ارتداد", "سور")),
    Concept("ASPECT", SITE_ANNOTATION, ("sea view", "view", "outlook",
                                        "frontage", "إطلالة", "واجهة بحرية",
                                        "منظر")),
    Concept("ORIENTATION", SITE_ANNOTATION, ("north", "south", "east", "west",
                                             "شمال", "جنوب", "شرق", "غرب")),
    Concept("ENTRY_POINT", SITE_ANNOTATION, ("entry", "main entry",
                                             "vehicle entry", "gate",
                                             "بوابة", "مدخل رئيسي")),

    # ------------------------------------------------ drawing annotation
    Concept("PLAN_TITLE", DRAWING_ANNOTATION, (
        "plan", "floor plan", "ground floor plan", "first floor plan",
        "second floor plan", "roof plan", "site plan", "key plan",
        "مسقط", "مخطط", "مسقط أفقي", "المسقط الأرضي")),
    Concept("SECTION_TITLE", DRAWING_ANNOTATION, (
        "section", "cross section", "longitudinal section", "قطاع", "مقطع")),
    Concept("ELEVATION_TITLE", DRAWING_ANNOTATION, (
        "elevation", "front elevation", "rear elevation", "side elevation",
        "واجهة", "واجهات")),
    Concept("DETAIL_TITLE", DRAWING_ANNOTATION, ("detail", "typical detail",
                                                 "تفصيل", "تفاصيل")),
    Concept("SHEET_NOTE", DRAWING_ANNOTATION, (
        "notes", "note", "general notes", "legend", "key", "schedule",
        "revision", "scale", "drawn by", "checked by", "title",
        "ملاحظات", "مفتاح", "جدول", "مقياس", "مقياس الرسم")),
    Concept("LEVEL_MARK", DRAWING_ANNOTATION, ("level", "finished floor "
                                               "level", "ffl", "منسوب")),
)

# Built once: normalised term -> concept.
_INDEX: dict = {}
_COLLISIONS: list = []


# --- normalisation --------------------------------------------------------

# Arabic diacritics (harakat) and the tatweel elongation character carry no
# lexical content and are typed inconsistently.
_ARABIC_MARKS = re.compile(r"[ً-ْـٰ]")
# Alef and yaa have several written forms that mean the same letter.
_ALEF = re.compile(r"[آأإٱ]")
_YAA = re.compile(r"[ى]")
_TAA_MARBUTA = re.compile(r"[ة]")
# Anything that separates words on a drawing: punctuation, dots, dashes.
_SEPARATORS = re.compile(r"[\s._\-/\\,;:()\[\]{}'\"#*]+")


def normalise(text: str) -> str:
    """The comparable form of a term: case, marks and separators removed."""
    s = unicodedata.normalize("NFKC", text or "").strip().casefold()
    s = _ARABIC_MARKS.sub("", s)
    s = _ALEF.sub("ا", s)
    s = _YAA.sub("ي", s)
    s = _TAA_MARBUTA.sub("ه", s)     # ة and ه are typed interchangeably
    s = _SEPARATORS.sub(" ", s)
    return " ".join(s.split())


def _build_index() -> None:
    for concept in _VOCABULARY:
        for term in concept.terms:
            key = normalise(term)
            if not key:
                continue
            if key in _INDEX and _INDEX[key].key != concept.key:
                _COLLISIONS.append((key, _INDEX[key].key, concept.key))
                continue
            _INDEX[key] = concept


_build_index()


@dataclass(frozen=True)
class Lookup:
    """What the vocabulary says about one string."""

    text: str
    normalised: str
    concept: str
    concept_class: str
    matched_term: str = ""

    @property
    def is_known(self) -> bool:
        return self.concept_class != UNKNOWN

    def record(self) -> dict:
        return {"text": self.text, "normalised": self.normalised,
                "concept": self.concept, "concept_class": self.concept_class,
                "means": MEANS.get(self.concept_class, ""),
                "matched_term": self.matched_term}


def classify_term(text: str) -> Lookup:
    """Look one string up. Exact match on the normalised form, or UNKNOWN.

    No stemming, no substring search and no fuzzy distance: `STORE` must not
    match `STOREY`, and a substring rule makes matches nobody can predict.
    """
    key = normalise(text)
    concept = _INDEX.get(key)
    if concept is None:
        return Lookup(text, key, "UNKNOWN", UNKNOWN)
    return Lookup(text, key, concept.key, concept.concept_class, key)


def concepts() -> tuple:
    return _VOCABULARY


def term_count() -> int:
    return len(_INDEX)


def collisions() -> list:
    """Terms two concepts both claim. Reported, never silently resolved."""
    return list(_COLLISIONS)


def summary() -> dict:
    from collections import Counter

    by_class = Counter(c.concept_class for c in _VOCABULARY)
    return {
        "ontology": ONTOLOGY,
        "ONTOLOGY_HASH": ontology_hash(),
        "concepts": len(_VOCABULARY),
        "terms_indexed": term_count(),
        "concepts_by_class": dict(by_class),
        "term_collisions": collisions(),
        "matching": ("exact, on a normalised form. No stemming, no "
                     "substring search, no fuzzy distance"),
        "scope": ("a general architectural vocabulary, not one project's "
                  "words. Most entries do not appear on any given sheet, "
                  "and the ones that do get no special handling"),
        "unknown_is_an_answer": (
            "a term absent from the vocabulary is UNKNOWN and is never "
            "guessed. An unknown NAME never invalidates a correct GEOMETRY"),
    }


def ontology_hash() -> str:
    rows = sorted(f"{c.key}|{c.concept_class}|{'|'.join(sorted(c.terms))}"
                  for c in _VOCABULARY)
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]
