"""E1.1 — a text insertion point is not room ownership, and one room may
be labelled twice.

Two separate errors in E1 v1 came from treating a CAD text object as a
room:

    THE DRAWING IS BILINGUAL. Every room carries an English stamp and an
    Arabic one. The Arabic stamps come back through an SHX font the
    decoder cannot map, as strings like 'ASVQBaL' beside 'RECEPTION'.
    E1 v1 counted each as a separate functional space, so a room holding
    both became MULTI_FUNCTION_PHYSICAL_REGION - one room, reported as a
    conflict, because it was labelled in two languages.

    A TEXT INSERTION POINT IS NOT THE MIDDLE OF THE TEXT. It is where the
    string STARTS, at its justification anchor, and for a right-to-left
    stamp it is at the other end. A stamp whose insertion point sits a
    few hundred millimetres across a doorway is not evidence that the
    room next door owns it.

Both corrections are general. NO TOKEN MAPPING IS ENCODED HERE. The
script of a stamp is decided from the drawing's own typography - the text
style it uses, whether it is generated backwards, and whether the decoded
glyphs read as a word at all - and a pair is decided from placement and
matching type, exactly as a person reading the sheet would.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field

MODEL = "A_TEXT_INSERTION_POINT_IS_NOT_ROOM_OWNERSHIP_V1"

# --- what a stamp is ----------------------------------------------------
ENGLISH_ROOM_STAMP = "ENGLISH_ROOM_STAMP"
ARABIC_ROOM_STAMP = "ARABIC_ROOM_STAMP"
UNRESOLVED_SHX_TEXT = "UNRESOLVED_SHX_TEXT"
NOT_A_ROOM_STAMP = "NOT_A_ROOM_STAMP"
STAMP_CLASSES = (ENGLISH_ROOM_STAMP, ARABIC_ROOM_STAMP,
                 UNRESOLVED_SHX_TEXT, NOT_A_ROOM_STAMP)

# --- how stamps relate --------------------------------------------------
BILINGUAL_LABEL_GROUP = "BILINGUAL_LABEL_GROUP"
POSSIBLE_BILINGUAL_ALIAS = "POSSIBLE_BILINGUAL_ALIAS"
SEPARATE_FUNCTIONAL_IDENTITY = "SEPARATE_FUNCTIONAL_IDENTITY"

# --- placement ----------------------------------------------------------
TEXT_INSERTION_POINT = "TEXT_INSERTION_POINT"
TEXT_RENDER_EXTENT = "TEXT_RENDER_EXTENT"
TEXT_ALIGNMENT = "TEXT_ALIGNMENT"
VISIBLE_LABEL_CENTROID = "VISIBLE_LABEL_CENTROID"
LABEL_GROUP = "LABEL_GROUP"
A18_VISUAL_LABEL_LOCATION = "A18_VISUAL_LABEL_LOCATION"

INSERTION_POINT_IS_WEAK_EVIDENCE = (
    "TEXT_INSERTION_POINT_INSIDE_POLYGON is WEAK evidence of ownership. "
    "The anchor is where the string starts, not where a reader sees it, "
    "and for a backwards-generated stamp it is at the opposite end. A "
    "label conflict may not be raised from the raw insertion point alone")

AN_UNRESOLVED_TOKEN_IS_NOT_A_SECOND_FUNCTION = (
    "an SHX token nobody can read is not a second room. Where it groups "
    "with an English stamp as an alternate-language label, the group is "
    "ONE functional identity, and where it does not it stays UNRESOLVED "
    "rather than becoming a function of its own")

NO_TOKEN_MAPPING_IS_ENCODED = (
    "no decoded token is mapped to an English word anywhere in this "
    "module. Pairing is decided from typography and placement, so the "
    "same code works on the next bilingual drawing without being told "
    "what its stamps say")

# --- typographic evidence ----------------------------------------------
EV_BACKWARD_GENERATION = "TEXT_IS_GENERATED_BACKWARDS"
EV_NON_DOMINANT_STYLE = "A_TEXT_STYLE_OTHER_THAN_THE_SHEETS_MAIN_ONE"
EV_NOT_WORD_LIKE = "THE_DECODED_GLYPHS_DO_NOT_READ_AS_A_WORD"
EV_WORD_LIKE = "THE_DECODED_GLYPHS_READ_AS_A_WORD"
EV_MATCHING_TYPE = "SAME_TEXT_HEIGHT_AND_WIDTH_FACTOR"
EV_STACKED_PLACEMENT = "PLACED_WITHIN_A_FEW_LINES_OF_THE_OTHER_STAMP"
EV_MUTUAL_NEAREST = "EACH_IS_THE_OTHERS_NEAREST_STAMP_OF_THE_OTHER_SCRIPT"
EV_NUMERIC_OR_LEVEL = "READS_AS_A_LEVEL_A_DIMENSION_OR_A_SHEET_NOTE"
EVIDENCE = (EV_BACKWARD_GENERATION, EV_NON_DOMINANT_STYLE, EV_NOT_WORD_LIKE,
            EV_WORD_LIKE, EV_MATCHING_TYPE, EV_STACKED_PLACEMENT,
            EV_MUTUAL_NEAREST, EV_NUMERIC_OR_LEVEL)

# --- GENERAL typography -------------------------------------------------
#
# A stroke font's average glyph advance, as a share of its text height.
# Used ONLY to estimate where the reader sees the string, and recorded as
# an estimate everywhere it is used.
GLYPH_ADVANCE = 0.60
RENDER_EXTENT_IS_AN_ESTIMATE = (
    "the render extent is computed from the text height, width factor and "
    "character count. The decoder does not carry glyph metrics, so this "
    "is an ESTIMATE of where the string is seen, declared as one")

# A bilingual pair sits within a few lines of its partner.
ALIAS_GAP_IN_TEXT_HEIGHTS = 10.0
TYPE_MATCH_TOL = 0.10

VOWELS = set("AEIOUaeiou")
MIN_VOWEL_SHARE = 0.12
MAX_VOWEL_SHARE = 0.72

DEFAULT_ALIGNMENT = "LEFT_BASELINE_ASSUMED_THE_DECODE_CARRIES_NO_OVERRIDE"


def model_hash() -> str:
    parts = ([MODEL] + list(STAMP_CLASSES) + list(EVIDENCE)
             + [BILINGUAL_LABEL_GROUP, POSSIBLE_BILINGUAL_ALIAS,
                f"{GLYPH_ADVANCE}", f"{ALIAS_GAP_IN_TEXT_HEIGHTS}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------- the decode's type

def typography(decoded: dict) -> dict:
    """Per-handle text typography, read straight from the decoded file.

    The normalised adapter carries a text's value, position and height,
    which is all a quantity needs. Deciding SCRIPT needs the type itself -
    which style the author used and whether the string is generated
    backwards - so E1.1 reads those from the same decode it was given,
    joined by DWG handle. Nothing is written back to the adapter.
    """
    out = {}
    for o in decoded.get("OBJECTS", ()):
        if not isinstance(o, dict):
            continue
        if o.get("entity") not in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
            continue
        h = o.get("handle")
        h = h[-1] if isinstance(h, list) and h else None
        if h is None:
            continue
        style = o.get("style")
        out[h] = {
            "text_style_handle": (style[-1] if isinstance(style, list)
                                  and style else None),
            "height": o.get("height"),
            "width_factor": o.get("width_factor"),
            "generation": o.get("generation"),
            "rotation": o.get("rotation"),
            "horiz_alignment": o.get("horiz_alignment"),
            "vert_alignment": o.get("vert_alignment"),
            "dataflags": o.get("dataflags"),
        }
    return out


# ------------------------------------------------------------ word-likeness

_LETTERS = re.compile(r"[A-Za-z]")
_ABBREV = re.compile(r"^[A-Z](\.[A-Z])+\.?$")


def word_like(text: str) -> bool:
    """Do the decoded glyphs read as an ordinary word or abbreviation?

    This asks a question about GLYPHS, not about meaning: it has no
    dictionary and does not know one room name from another.
    """
    t = (text or "").strip()
    if not t:
        return False
    if not t.isascii():
        return False
    for part in t.split():
        if _ABBREV.match(part):
            continue
        letters = _LETTERS.findall(part)
        if len(letters) < 3:
            return False
        if len(letters) / max(len(part), 1) < 0.6:
            return False
        v = sum(1 for c in letters if c in VOWELS)
        share = v / len(letters)
        if len(letters) >= 3 and not (MIN_VOWEL_SHARE <= share
                                      <= MAX_VOWEL_SHARE):
            return False
        # an upper-case letter in the middle of a lower-case run is how a
        # substituted glyph set comes back, not how a word is typed
        for a, b in zip(part, part[1:]):
            if a.islower() and b.isupper():
                return False
    return True


def looks_numeric(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if t.startswith("%%"):
        return True
    digits = sum(1 for c in t if c.isdigit())
    return digits >= max(1, len(_LETTERS.findall(t)))


# ------------------------------------------------------------------ stamps

@dataclass
class Stamp:
    """One text object, with where a READER sees it."""

    stamp_id: str = ""
    text: str = ""
    dwg_handle: int | None = None
    layer: str = ""
    x: float = 0.0                 # the CAD insertion point
    y: float = 0.0
    height: float = 0.0
    width_factor: float = 1.0
    rotation: float = 0.0
    backwards: bool = False
    text_style_handle: int | None = None
    alignment: str = DEFAULT_ALIGNMENT
    stamp_class: str = UNRESOLVED_SHX_TEXT
    evidence: tuple = ()
    group_id: str = ""
    a18_visual_label_location: object = None

    @property
    def render_extent(self) -> tuple:
        """(x0, y0, x1, y1) where the string is seen. An ESTIMATE."""
        w = (len(self.text) * self.height * (self.width_factor or 1.0)
             * GLYPH_ADVANCE)
        h = self.height
        dx = -w if self.backwards else w
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        pts = [(0.0, 0.0), (dx, 0.0), (dx, h), (0.0, h)]
        xs, ys = [], []
        for (px, py) in pts:
            xs.append(self.x + px * ca - py * sa)
            ys.append(self.y + px * sa + py * ca)
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def visible_centroid(self) -> tuple:
        x0, y0, x1, y1 = self.render_extent
        return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)

    def record(self) -> dict:
        x0, y0, x1, y1 = self.render_extent
        cx, cy = self.visible_centroid
        return {
            "stamp_id": self.stamp_id,
            "text_as_decoded": self.text,
            "dwg_handle": self.dwg_handle,
            "layer": self.layer,
            "STAMP_CLASS": self.stamp_class,
            "evidence": list(self.evidence),
            TEXT_INSERTION_POINT: [round(self.x, 2), round(self.y, 2)],
            TEXT_ALIGNMENT: self.alignment,
            TEXT_RENDER_EXTENT: [round(x0, 2), round(y0, 2),
                                 round(x1, 2), round(y1, 2)],
            "render_extent_is_an_estimate": RENDER_EXTENT_IS_AN_ESTIMATE,
            VISIBLE_LABEL_CENTROID: [round(cx, 2), round(cy, 2)],
            "text_height_mm": round(self.height, 2),
            "width_factor": self.width_factor,
            "text_style_handle": self.text_style_handle,
            "generated_backwards": self.backwards,
            LABEL_GROUP: self.group_id or None,
            A18_VISUAL_LABEL_LOCATION: self.a18_visual_label_location,
            "insertion_point_is_weak_evidence":
                INSERTION_POINT_IS_WEAK_EVIDENCE,
        }


@dataclass
class Group:
    """One functional identity, however many languages label it."""

    group_id: str = ""
    members: tuple = ()
    relation: str = BILINGUAL_LABEL_GROUP
    english_token: str = ""
    evidence: tuple = ()
    why: str = ""

    @property
    def centroid(self) -> tuple:
        pts = [m.visible_centroid for m in self.members]
        return (sum(p[0] for p in pts) / len(pts),
                sum(p[1] for p in pts) / len(pts))

    def record(self) -> dict:
        cx, cy = self.centroid
        return {
            LABEL_GROUP: self.group_id,
            "relation": self.relation,
            "english_token": self.english_token or None,
            "members": [m.stamp_id for m in self.members],
            "member_texts": [m.text for m in self.members],
            "member_classes": [m.stamp_class for m in self.members],
            "group_centroid_mm": [round(cx, 2), round(cy, 2)],
            "evidence": list(self.evidence),
            "why": self.why,
            "an_unresolved_token_is_not_a_second_function":
                AN_UNRESOLVED_TOKEN_IS_NOT_A_SECOND_FUNCTION,
        }


def build(texts, *, typo=None, a18_label_locations=None) -> dict:
    """Classify every stamp and group the bilingual pairs."""
    typo = dict(typo or {})
    a18 = dict(a18_label_locations or {})
    stamps = []
    for n, t in enumerate(texts, start=1):
        ty = typo.get(t.provenance.handle, {})
        gen = ty.get("generation") or 0
        s = Stamp(stamp_id=f"TXT-{n:03d}", text=(t.value or "").strip(),
                  dwg_handle=t.provenance.handle,
                  layer=t.provenance.layer, x=t.x, y=t.y, height=t.height,
                  width_factor=float(ty.get("width_factor") or 1.0),
                  rotation=float(ty.get("rotation") or 0.0),
                  backwards=bool(int(gen) & 2),
                  text_style_handle=ty.get("text_style_handle"))
        if ty.get("horiz_alignment") is not None or \
                ty.get("vert_alignment") is not None:
            s.alignment = (f"H{ty.get('horiz_alignment')}"
                           f"_V{ty.get('vert_alignment')}_FROM_THE_DECODE")
        stamps.append(s)

    # the sheet's main text style, taken from the word-like stamps
    counts = {}
    for s in stamps:
        if word_like(s.text) and not looks_numeric(s.text):
            counts[s.text_style_handle] = counts.get(
                s.text_style_handle, 0) + 1
    dominant = max(counts, key=counts.get) if counts else None

    for s in stamps:
        ev = []
        if looks_numeric(s.text):
            s.stamp_class = NOT_A_ROOM_STAMP
            s.evidence = (EV_NUMERIC_OR_LEVEL,)
            continue
        wl = word_like(s.text)
        ev.append(EV_WORD_LIKE if wl else EV_NOT_WORD_LIKE)
        if s.backwards:
            ev.append(EV_BACKWARD_GENERATION)
        if dominant is not None and s.text_style_handle != dominant:
            ev.append(EV_NON_DOMINANT_STYLE)
        if s.backwards or (EV_NON_DOMINANT_STYLE in ev and not wl):
            s.stamp_class = ARABIC_ROOM_STAMP
        elif wl:
            s.stamp_class = ENGLISH_ROOM_STAMP
        else:
            s.stamp_class = UNRESOLVED_SHX_TEXT
        s.evidence = tuple(ev)

    english = [s for s in stamps if s.stamp_class == ENGLISH_ROOM_STAMP]
    other = [s for s in stamps if s.stamp_class in (ARABIC_ROOM_STAMP,
                                                    UNRESOLVED_SHX_TEXT)]

    def gap(a, b):
        ax, ay = a.visible_centroid
        bx, by = b.visible_centroid
        return math.hypot(ax - bx, ay - by)

    nearest_en = {}
    for o in other:
        cands = sorted(english, key=lambda e: gap(o, e))
        nearest_en[o.stamp_id] = cands[0] if cands else None
    nearest_other = {}
    for e in english:
        cands = sorted(other, key=lambda o: gap(e, o))
        nearest_other[e.stamp_id] = cands[0] if cands else None

    groups, used = [], set()
    for o in other:
        e = nearest_en.get(o.stamp_id)
        if e is None or o.stamp_id in used:
            continue
        d = gap(o, e)
        limit = ALIAS_GAP_IN_TEXT_HEIGHTS * max(o.height, e.height, 1.0)
        ev = []
        if abs(o.height - e.height) <= TYPE_MATCH_TOL * max(o.height, 1.0) \
                and abs((o.width_factor or 1) - (e.width_factor or 1)) \
                <= TYPE_MATCH_TOL:
            ev.append(EV_MATCHING_TYPE)
        if d <= limit:
            ev.append(EV_STACKED_PLACEMENT)
        mutual = nearest_other.get(e.stamp_id) is o
        if mutual:
            ev.append(EV_MUTUAL_NEAREST)
        if EV_STACKED_PLACEMENT not in ev:
            continue
        strong = mutual and EV_MATCHING_TYPE in ev
        gid = f"LG-{len(groups) + 1:03d}"
        o.group_id = gid
        if e.group_id:
            gid = e.group_id
            o.group_id = gid
            for g in groups:
                if g.group_id == gid:
                    g.members = g.members + (o,)
                    g.evidence = tuple(sorted(set(g.evidence) | set(ev)))
                    break
            used.add(o.stamp_id)
            continue
        e.group_id = gid
        groups.append(Group(
            group_id=gid, members=(e, o),
            relation=(BILINGUAL_LABEL_GROUP if strong
                      else POSSIBLE_BILINGUAL_ALIAS),
            english_token=e.text.upper(),
            evidence=tuple(ev),
            why=(f"an unreadable stamp sits {d:.0f} mm from an English one "
                 f"in matching type. One room, labelled twice"
                 if strong else
                 f"an unreadable stamp sits {d:.0f} mm from an English one, "
                 "which is placement evidence of an alias without the "
                 "matching type to confirm it")))
        used.add(o.stamp_id)

    for s in stamps:
        if s.group_id:
            continue
        if s.stamp_class in (ENGLISH_ROOM_STAMP, ARABIC_ROOM_STAMP,
                             UNRESOLVED_SHX_TEXT):
            gid = f"LG-{len(groups) + 1:03d}"
            s.group_id = gid
            groups.append(Group(
                group_id=gid, members=(s,),
                relation=SEPARATE_FUNCTIONAL_IDENTITY,
                english_token=(s.text.upper()
                               if s.stamp_class == ENGLISH_ROOM_STAMP
                               else ""),
                evidence=s.evidence,
                why=("no stamp of the other script lies near enough to be "
                     "its alternate-language label")))

    for s in stamps:
        if s.stamp_id in a18:
            s.a18_visual_label_location = a18[s.stamp_id]

    return {
        "stamps": stamps,
        "groups": groups,
        "dominant_text_style_handle": dominant,
        "counts": {c: sum(1 for s in stamps if s.stamp_class == c)
                   for c in STAMP_CLASSES},
        "group_counts": {r: sum(1 for g in groups if g.relation == r)
                         for r in (BILINGUAL_LABEL_GROUP,
                                   POSSIBLE_BILINGUAL_ALIAS,
                                   SEPARATE_FUNCTIONAL_IDENTITY)},
        "no_token_mapping_is_encoded": NO_TOKEN_MAPPING_IS_ENCODED,
    }


def separate_functions(stamps) -> list:
    """Which of these stamps are genuinely DIFFERENT functional labels.

    Only readable room stamps in different label groups can make a region
    multi-function. An Arabic stamp or an unreadable SHX token inside the
    same polygon is the same room said twice - or said once and not
    understood - and neither is a second function.
    """
    seen, out = set(), []
    for s in stamps:
        if s.stamp_class != ENGLISH_ROOM_STAMP:
            continue
        key = s.group_id or s.text.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def same_identity(a: Stamp, b: Stamp) -> bool:
    """Are these two stamps two labels for ONE functional identity?"""
    return bool(a.group_id) and a.group_id == b.group_id


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "STAMP_CLASSES": list(STAMP_CLASSES),
        "RELATIONS": [BILINGUAL_LABEL_GROUP, POSSIBLE_BILINGUAL_ALIAS,
                      SEPARATE_FUNCTIONAL_IDENTITY],
        "PLACEMENT_FIELDS": [TEXT_INSERTION_POINT, TEXT_RENDER_EXTENT,
                             TEXT_ALIGNMENT, VISIBLE_LABEL_CENTROID,
                             LABEL_GROUP, A18_VISUAL_LABEL_LOCATION],
        "EVIDENCE": list(EVIDENCE),
        "GLYPH_ADVANCE": GLYPH_ADVANCE,
        "ALIAS_GAP_IN_TEXT_HEIGHTS": ALIAS_GAP_IN_TEXT_HEIGHTS,
        "TYPE_MATCH_TOL": TYPE_MATCH_TOL,
        "MIN_VOWEL_SHARE": MIN_VOWEL_SHARE,
        "MAX_VOWEL_SHARE": MAX_VOWEL_SHARE,
        "why": {
            "insertion_point_is_weak_evidence":
                INSERTION_POINT_IS_WEAK_EVIDENCE,
            "an_unresolved_token_is_not_a_second_function":
                AN_UNRESOLVED_TOKEN_IS_NOT_A_SECOND_FUNCTION,
            "no_token_mapping_is_encoded": NO_TOKEN_MAPPING_IS_ENCODED,
            "render_extent_is_an_estimate": RENDER_EXTENT_IS_AN_ESTIMATE,
        },
    }
