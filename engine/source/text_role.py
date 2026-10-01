"""TEXT ROLE AUTHORITY (R8.9): a text is not a room identity merely because it lies inside a polygon.

R8.8 counted every visible text inside a site as a label occurrence (conservative on a drawing where no other text
sits in an apartment room, but not a generic rule). Here each text gets a role from positive evidence BEFORE it can
name a space:

  TR-01 TITLE_TEXT              in the region's sheet-frame occurrence, or on a sheet-frame layer
  TR-02 DIMENSION_TEXT          on a dimension layer
  TR-03 ROOM_LABEL_ESTABLISHED  a TAG OCCURRENCE (an insert whose content is text only) with room-vocabulary
                                corroboration in one of its texts (STRUCTURAL: the occurrence is the label)
  TR-04 ROOM_LABEL_ESTABLISHED  a tag occurrence with the same TAG COMPOSITION (text count, effective layers, entity
                                types; heights are block-local and not compared) as a TR-03 tag of the SAME source (source-scoped family; the vocabulary is
                                not required: a misspelled room name in the author's own tag is still that tag)
  TR-05 DOOR_TAG / WINDOW_TAG   a tag occurrence whose texts carry door / window vocabulary only
  TR-06 ROOM_LABEL_CANDIDATE    a tag occurrence without corroboration or family
  TR-07 ROOM_LABEL_ESTABLISHED  a text on a ROOM-LABEL layer (CORROBORATED: layer role + entity type + context,
                                the same strength as a wall line)
  TR-08 AREA_TEXT / LEVEL_MARK  loose text whose content is an area or level statement
  TR-09 GENERAL_NOTE / ANNOTATION_TEXT   loose text on an annotation layer
  TR-10 ROOM_LABEL_CANDIDATE    loose text with room vocabulary and no structure
  TR-11 a reviewed, source-scoped text-layer claim (role_authority.SourceLayerRoleClaim)
  TR-99 UNKNOWN_TEXT_ROLE

Only ROOM_LABEL_ESTABLISHED names a space. A ROOM_LABEL_CANDIDATE or UNKNOWN_TEXT_ROLE text inside a site raises
TEXT_ROLE_UNRESOLVED_IN_SITE (semantic review): never a silent identity, never a nearest-label fallback.

Project-agnostic: generic vocabulary; stdlib only.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from . import canonical_input as CI
from . import geometry_role as GR
from . import role_authority as RA

POLICY_ID = "TEXT_ROLE_POLICY_V1"
ROOM_LABEL_ESTABLISHED, ROOM_LABEL_CANDIDATE = "ROOM_LABEL_ESTABLISHED", "ROOM_LABEL_CANDIDATE"
DIMENSION_TEXT, GENERAL_NOTE, DOOR_TAG, WINDOW_TAG = "DIMENSION_TEXT", "GENERAL_NOTE", "DOOR_TAG", "WINDOW_TAG"
LEVEL_MARK, AREA_TEXT, TITLE_TEXT, ANNOTATION_TEXT = "LEVEL_MARK", "AREA_TEXT", "TITLE_TEXT", "ANNOTATION_TEXT"
UNKNOWN_TEXT_ROLE = "UNKNOWN_TEXT_ROLE"
TEXT_ROLE_UNRESOLVED_IN_SITE = "TEXT_ROLE_UNRESOLVED_IN_SITE"
UNRESOLVED = (ROOM_LABEL_CANDIDATE, UNKNOWN_TEXT_ROLE)

ROOM_WORDS = ("ROOM", "ROOMS", "BED", "BEDROOM", "MASTER", "LIVING", "HALL", "LOBBY", "SALOON", "SALON", "RECEPTION",
              "DINING", "KITCHEN", "PANTRY", "BATH", "BATHROOM", "WC", "TOILET", "SHOWER", "LAUNDRY", "STORE",
              "STORAGE", "DRESS", "DRESSING", "CLOSET", "MAID", "DRIVER", "GUARD", "OFFICE", "STUDY", "LIBRARY",
              "CORRIDOR", "PASSAGE", "ENTRANCE", "FOYER", "BALCONY", "TERRACE", "ROOF", "GARAGE", "PARKING", "MAJLIS",
              "DIWANIYA", "PRAYER", "GYM", "UTILITY", "SHAFT", "VOID", "STAIR", "STAIRS", "LIFT", "FAMILY", "GUEST",
              "SITTING", "WASH")
DOOR_WORDS, WINDOW_WORDS = ("DOOR", "DR"), ("WINDOW", "WIN", "WDW")
ROOM_LABEL_LAYER_WORDS = ("ROOM", "ROOMS", "ROOMNAME", "ROOMNAMES", "ROOMTAG", "RMTAG", "SPACE", "SPACES", "SPACENAME")
_AREA = re.compile(r"(\bm2\b|m²|\bsqm\b|\bAREA\b)", re.I)
_LEVEL = re.compile(r"(\bLEVEL\b|\bFFL\b|\bSSL\b|[+±-]\s?\d+[.,]\d{2}\b)", re.I)


@dataclass(frozen=True)
class TextRole:
    text_key: str | None
    role: str
    rule_id: str
    evidence: dict = field(default_factory=dict)


def _words(value):
    return set(GR.tokens(value or ""))


def _signature(ts):
    """Scale-free tag composition: (effective layer, entity type) per text. Heights are block-local and scale with
    each insert, so they are not part of the signature."""
    return tuple(sorted((CI.effective_layer(t)[0], t.entity_type) for t in ts))


def classify(inp: CI.CanonicalMeasurementInput, *, frame_insert=None, claims=()) -> dict:
    """{text key: TextRole} for every VISIBLE text."""
    vis = [t for t in inp.texts if t.visibility == CI.VISIBLE]
    part_occ = {p.identity.instance_handles[0] for p in inp.parts if p.identity.instance_handles}
    occ = defaultdict(list)
    for t in vis:
        path = t.identity.instance_handles or ()
        if path:
            occ[path[0]].append(t)
    tags = {o: ts for o, ts in occ.items() if o not in part_occ and o != frame_insert}   # text-only occurrences
    established_sigs = set()
    tag_role = {}
    for o, ts in tags.items():
        words = set().union(*(_words(t.value) for t in ts))
        if words & set(ROOM_WORDS):
            tag_role[o] = (ROOM_LABEL_ESTABLISHED, "TR-03", sorted(words & set(ROOM_WORDS)))
            established_sigs.add(_signature(ts))
    for o, ts in tags.items():
        if o in tag_role:
            continue
        words = set().union(*(_words(t.value) for t in ts))
        if _signature(ts) in established_sigs and not words & (set(DOOR_WORDS) | set(WINDOW_WORDS)):
            tag_role[o] = (ROOM_LABEL_ESTABLISHED, "TR-04", "same tag signature as an established room tag")
        elif words and words <= set(DOOR_WORDS) | {w for w in words if w.isdigit()}:
            tag_role[o] = (DOOR_TAG, "TR-05", sorted(words))
        elif words and words <= set(WINDOW_WORDS) | {w for w in words if w.isdigit()}:
            tag_role[o] = (WINDOW_TAG, "TR-05", sorted(words))
        else:
            tag_role[o] = (ROOM_LABEL_CANDIDATE, "TR-06", "tag occurrence without corroboration or family")
    claim_layers = {}
    for c in claims:
        if RA.claim_applies(c, inp.revision, inp.region_id)[0]:
            claim_layers[c.layer] = c
    out = {}
    for t in vis:
        path = t.identity.instance_handles or ()
        lay = CI.effective_layer(t)[0]
        lr = GR.layer_role(lay)
        ev = {"layer": lay, "source_layer": t.layer, "occurrence": path[0] if path else None,
              "entity_type": t.entity_type}
        if lay in claim_layers:
            r = (claim_layers[lay].role, "TR-11", claim_layers[lay].claim_id)
        elif (path and frame_insert is not None and path[0] == frame_insert) or lr == "SHEET_FRAME":
            r = (TITLE_TEXT, "TR-01", None)
        elif lr == "DIMENSION":
            r = (DIMENSION_TEXT, "TR-02", None)
        elif path and path[0] in tag_role:
            r = tag_role[path[0]]
        elif set(GR.tokens(lay or "")) & set(ROOM_LABEL_LAYER_WORDS):
            r = (ROOM_LABEL_ESTABLISHED, "TR-07", "room-label layer")
        elif _AREA.search(t.value or ""):
            r = (AREA_TEXT, "TR-08", None)
        elif _LEVEL.search(t.value or ""):
            r = (LEVEL_MARK, "TR-08", None)
        elif _words(t.value) & set(ROOM_WORDS):
            r = (ROOM_LABEL_CANDIDATE, "TR-10", sorted(_words(t.value) & set(ROOM_WORDS)))
        elif lr == "ANNOTATION":
            r = (GENERAL_NOTE, "TR-09", None)
        else:
            r = (UNKNOWN_TEXT_ROLE, "TR-99", None)
        role, rid, why = r
        out[t.identity.key] = TextRole(t.identity.key, role, rid, dict(ev, why=why))
    return out


def policy_record() -> dict:
    return {"id": POLICY_ID, "rules": ["TR-01 TITLE_TEXT", "TR-02 DIMENSION_TEXT", "TR-03 tag occurrence + room "
                                       "vocabulary", "TR-04 tag family (same source)", "TR-05 door / window tag",
                                       "TR-06 tag candidate", "TR-07 room-label layer", "TR-08 area / level",
                                       "TR-09 annotation", "TR-10 loose room word: candidate", "TR-11 claim",
                                       "TR-99 unknown"],
            "names_a_space": [ROOM_LABEL_ESTABLISHED], "semantic_review": list(UNRESOLVED),
            "room_vocabulary": list(ROOM_WORDS), "room_label_layers": list(ROOM_LABEL_LAYER_WORDS),
            "never": ["inside a polygon alone", "nearest label", "vocabulary alone"]}
