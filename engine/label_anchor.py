"""E1.4 — where a name actually sits, established before geometry is walked.

THE DEFECT THIS REPLACES

Frozen E1.3 seeded every candidate at the visible centroid of its label
group. For E1_3-LG-012 the name is WASH, and that centroid lies 291 mm on
the DEWANEYA side of the wall dividing the two. Every question after that
was asked about the wrong compartment: the walk started in the Dewaneya,
and the label-seed relation register then recorded a clear sight line
between DEWANEYA and WASH with nothing built between them - true of the
two seeds, false of the two rooms.

A centroid is an average. Average a bilingual pair of stamps, or a group
whose glyphs straddle a wall, and the average can land in a room neither
stamp is in. That an average exists is not evidence that it is inside the
space being named.

WHAT THIS DOES

Every anchor the source offers is kept, separately, and none is assumed
interchangeable with another. Before any boundary is walked, the anchors
are tested against each other: if established material stands between
them, they are in different compartments and the seed is AMBIGUOUS. An
ambiguous seed is reported, not resolved by falling back to the average.

Where the anchors agree, the anchor used is the one the source evidence
supports - a stamp's own insertion point or its own visible centroid -
and never a room area, an expected geometry or a known quantity.
"""

from __future__ import annotations

import hashlib

MODEL = "AN_AVERAGE_OF_GLYPHS_IS_NOT_EVIDENCE_OF_BEING_INSIDE_A_ROOM_V1"

# --- the kinds of anchor a source can offer ------------------------------
ENGLISH_TOKEN_ANCHOR = "ENGLISH_TOKEN_ANCHOR"
ARABIC_TOKEN_ANCHOR = "ARABIC_TOKEN_ANCHOR"
GROUP_CENTROID = "GROUP_CENTROID"
CAD_TEXT_INSERTION_POINT = "CAD_TEXT_INSERTION_POINT"
VISUAL_LABEL_LOCATION = "VISUAL_LABEL_LOCATION"
OTHER_SOURCE_ANCHOR = "OTHER_SOURCE_ANCHOR"

ANCHOR_KINDS = (ENGLISH_TOKEN_ANCHOR, ARABIC_TOKEN_ANCHOR, GROUP_CENTROID,
                CAD_TEXT_INSERTION_POINT, VISUAL_LABEL_LOCATION,
                OTHER_SOURCE_ANCHOR)

# An anchor belonging to one stamp is evidence about where that stamp is.
# A centroid is a derived average of several, and is the weakest.
ANCHOR_IS_ITS_OWN_STAMP = (ENGLISH_TOKEN_ANCHOR, ARABIC_TOKEN_ANCHOR,
                           CAD_TEXT_INSERTION_POINT)

# --- seed status ---------------------------------------------------------
SEED_ESTABLISHED = "SEED_ESTABLISHED"
AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY = "AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY"
SEED_NOT_ESTABLISHED = "SEED_NOT_ESTABLISHED"

SEED_STATUSES = (SEED_ESTABLISHED, AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY,
                 SEED_NOT_ESTABLISHED)

ANCHORS_ARE_NOT_INTERCHANGEABLE = (
    "an English stamp, an Arabic stamp, a text insertion point and the "
    "average of a group are four different pieces of evidence about where "
    "a name sits. They are recorded separately. Where they disagree, that "
    "disagreement is the finding")

AN_AMBIGUOUS_SEED_IS_NOT_RESOLVED_BY_THE_OLD_DEFAULT = (
    "when established material stands between two anchors of the same "
    "label, the label's own evidence does not say which compartment it "
    "names. Choosing the group centroid because that is what the previous "
    "pass did would be choosing the weakest anchor for no reason. The seed "
    "is reported AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY and no geometry is "
    "walked from a guess")

NO_AREA_AND_NO_EXPECTATION = (
    "an anchor is never chosen because the space it lands in has a "
    "plausible size, matches an expected geometry, or produces a "
    "convenient quantity. Only source evidence about where the name sits "
    "may select it")


def model_hash() -> str:
    parts = [MODEL] + list(ANCHOR_KINDS) + list(SEED_STATUSES) \
        + list(ANCHOR_IS_ITS_OWN_STAMP)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def anchor(kind, point, *, source, text=None) -> dict:
    return {
        "ANCHOR_KIND": kind,
        "point_mm": [round(float(point[0]), 3), round(float(point[1]), 3)],
        "source": source,
        "text": text,
        "is_its_own_stamp": kind in ANCHOR_IS_ITS_OWN_STAMP,
    }


def compartments(anchors, *, material_between) -> dict:
    """Group anchors by compartment, splitting where material stands between.

    `material_between(a, b)` answers whether established material lies on
    the straight line from a to b. It is supplied by the caller because
    what counts as established material is not this module's question.
    """
    pts = [tuple(a["point_mm"]) for a in anchors]
    n = len(pts)
    group = list(range(n))

    def find(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i

    separations = []
    for i in range(n):
        for j, b in enumerate(pts[i + 1:], start=i + 1):
            blocked, by = material_between(pts[i], b)
            if blocked:
                separations.append({
                    "between": [anchors[i]["ANCHOR_KIND"],
                                anchors[j]["ANCHOR_KIND"]],
                    "material_between": by,
                })
                continue
            ri, rj = find(i), find(j)
            if ri != rj:
                group[rj] = ri

    buckets = {}
    for i in range(n):
        buckets.setdefault(find(i), []).append(anchors[i]["ANCHOR_KIND"])
    return {
        "compartments": [sorted(v) for v in buckets.values()],
        "compartment_count": len(buckets),
        "anchor_pairs_with_material_between_them": separations,
    }


def assess(candidate_id, anchors, *, material_between) -> dict:
    """One candidate's anchors, whether they agree, and the seed to use."""
    anchors = list(anchors or ())
    base = {
        "CANDIDATE_ID": candidate_id,
        "ANCHORS": anchors,
        "anchor_count": len(anchors),
        "anchors_are_not_interchangeable": ANCHORS_ARE_NOT_INTERCHANGEABLE,
        "no_area_and_no_expectation": NO_AREA_AND_NO_EXPECTATION,
    }
    if not anchors:
        return {**base, "LABEL_SEED_STATUS": SEED_NOT_ESTABLISHED,
                "SEED_MM": None,
                "why": "the source offers no anchor for this label"}

    split = compartments(anchors, material_between=material_between)
    if split["compartment_count"] > 1:
        return {
            **base, **split,
            "LABEL_SEED_STATUS": AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY,
            "SEED_MM": None,
            "SEED_ANCHOR_KIND": None,
            "why": ("this label's own anchors fall in "
                    f"{split['compartment_count']} compartments separated by "
                    "established material, so the label does not say which "
                    "space it names"),
            "an_ambiguous_seed_is_not_resolved_by_the_old_default":
                AN_AMBIGUOUS_SEED_IS_NOT_RESOLVED_BY_THE_OLD_DEFAULT,
        }

    # They agree. Use the strongest anchor: a stamp's own point before an
    # average of several stamps.
    order = {k: i for i, k in enumerate(
        (ENGLISH_TOKEN_ANCHOR, ARABIC_TOKEN_ANCHOR, CAD_TEXT_INSERTION_POINT,
         VISUAL_LABEL_LOCATION, OTHER_SOURCE_ANCHOR, GROUP_CENTROID))}
    chosen = sorted(anchors, key=lambda a: order.get(a["ANCHOR_KIND"], 99))[0]
    return {
        **base, **split,
        "LABEL_SEED_STATUS": SEED_ESTABLISHED,
        "SEED_MM": chosen["point_mm"],
        "SEED_ANCHOR_KIND": chosen["ANCHOR_KIND"],
        "why": ("every anchor this label offers stands in one compartment, "
                "so they agree about which space is named. The seed is the "
                f"{chosen['ANCHOR_KIND']}, which is a stamp's own position "
                "rather than an average of several"
                if chosen["is_its_own_stamp"] else
                "every anchor this label offers stands in one compartment. "
                "No stamp's own position was available, so the seed is the "
                f"{chosen['ANCHOR_KIND']}"),
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ANCHOR_KINDS": list(ANCHOR_KINDS),
        "ANCHOR_IS_ITS_OWN_STAMP": list(ANCHOR_IS_ITS_OWN_STAMP),
        "SEED_STATUSES": list(SEED_STATUSES),
        "why": {
            "anchors_are_not_interchangeable":
                ANCHORS_ARE_NOT_INTERCHANGEABLE,
            "an_ambiguous_seed_is_not_resolved_by_the_old_default":
                AN_AMBIGUOUS_SEED_IS_NOT_RESOLVED_BY_THE_OLD_DEFAULT,
            "no_area_and_no_expectation": NO_AREA_AND_NO_EXPECTATION,
        },
    }
