"""A19 - the visual CAD semantic reader. Its briefs, schema and screen.

A19 reads a picture and says what a local architectural feature IS. It
never says where anything is, how big it is, or how much of it there is.
The answer schema has no numeric field at all, and the screen below runs
over every returned answer anyway.
"""

from __future__ import annotations

import hashlib
import re

from research.semantic_edge_experiment_01 import protocol as P

PASS_A_BRIEF = """\
YOU ARE READING ONE LOCAL PART OF AN ARCHITECTURAL GROUND FLOOR PLAN.

Your job is to say WHAT the marked geometry represents. You are not being
asked where anything is, how big it is, or how much of it there is. The
CAD file already knows where every line is, exactly, and it is the
authority on that. You are the authority on meaning.

WHAT YOU HAVE

  LEVEL_A_CONTEXT      the surrounding area, so you can tell a window
                       from an internal partition, a counter from a wall,
                       a pool rim from a water edge
  LEVEL_B_FEATURE      the feature itself, clean and marked
  LEVEL_C_DETAIL       where present, the fine detail of jambs, frames
                       and curves
  ENTITIES             the marked members, each with an index label, its
                       CAD layer, linetype, entity type and block, if the
                       drawing exposes them
  FLOOR_CONTEXT        a general note about this floor - which rooms it
                       has, roughly where the facade and the pool and the
                       stairs are. It does not tell you what any line is

The marked members are drawn in one colour with index labels. Unlabelled
members in the second colour are context: look at them, do not answer
about them.

ONE CAD LINE IS NOT ONE ARCHITECTURAL THING

A window is usually several entities - glass, frame, jambs, wall returns,
sometimes mullions. A door is a leaf, a swing, jambs, an opening, maybe a
threshold. A wall body is two faces plus returns, interrupted by
openings. A pool is a water boundary, a coping, a rim, and often setting
out curves that mean nothing built. So answer the ASSEMBLY first, and
only then its members.

WHAT TO ANSWER

  FEATURE_ASSEMBLY_TYPE   what the marked group is, as a whole
  ASSEMBLY_CONFIDENCE     HIGH, MEDIUM, LOW or UNRESOLVED - a word, never
                          a number or a percentage
  WHY                     what in the picture makes you say it
  ENTITY_ROLES            for the labelled members you can actually place
                          within that assembly. Leave a member UNRESOLVED
                          rather than guessing its subtype
  RELATIONS               statements about how the members go together,
                          such as "these entities form one window". These
                          are often the most reliable thing you can say
  FENESTRATION_READING    required for exterior and junction groups: is
                          the marked run solid wall, a window, a door, an
                          open void, a mixture, or unresolved
  CURVE_FAMILY            required for curve groups: do these curves
                          belong to one architectural feature, and if you
                          can tell, what each one is
  NEEDS_MORE_CONTEXT      true if the crops do not let you decide

WHAT YOU MAY NOT DO

  do not state or invent a coordinate, a dimension, an area, a perimeter,
  a length or any quantity
  do not propose a corrected line, a polygon or a closed room
  do not choose a reading because it would make a space close neatly.
  Whether a region closes is not your question and not your evidence
  do not give a probability. The confidence words are the whole scale

UNRESOLVED IS A REAL ANSWER. An honest gap can be filled later by a
human; a confident wrong subtype inside a wrongly assembled group cannot
even be found.
"""

PASS_B_BRIEF = """\
SAME PICTURE, SECOND QUESTION.

You are now shown your own earlier reading of this group, frozen before
anything else was revealed, and alongside it what the deterministic CAD
classifier currently says about the same entities.

The question is not which of you is nicer. It is:

  does the deterministic classification agree with what is visibly there?

Answer with one or more of these, and say why:

  AGREES                          the classifier and the picture match
  DETERMINISTIC_FALSE_POSITIVE    it claims a role the picture does not
                                  support
  DETERMINISTIC_FALSE_NEGATIVE    the picture clearly shows something the
                                  classifier left unclassified
  ROLE_MISMATCH                   both see something, they disagree what
  FEATURE_GROUPING_MISMATCH       the classifier has split one feature or
                                  merged two, whatever the roles say
  VISION_UNRESOLVED               you cannot tell from this picture
  BOTH_UNRESOLVED                 neither source settles it

You still may not state a coordinate, a dimension, an area or any
quantity, and you may not propose corrected geometry. Nothing you say
here moves a line in the CAD file.
"""

ANSWER_SCHEMA = {
    "FEATURE_GROUP_ID": "string, copied from the task",
    "FEATURE_ASSEMBLY_TYPE": f"one of {list(P.FEATURE_ASSEMBLY_TYPES)}",
    "ASSEMBLY_CONFIDENCE": f"one of {list(P.CONFIDENCE_CLASSES)}",
    "WHY": "prose",
    "ENTITY_ROLES": [{"MEMBER_LABEL": "P01",
                      "SUB_ROLE": f"one of {list(P.ENTITY_SUB_ROLES)}",
                      "CONFIDENCE": f"one of {list(P.CONFIDENCE_CLASSES)}",
                      "WHY": "prose"}],
    "RELATIONS": [{"RELATION": f"one of {list(P.RELATIONS)}",
                   "MEMBER_LABELS": ["P01", "P02"], "WHY": "prose"}],
    "FENESTRATION_READING": f"one of {list(P.FENESTRATION_READINGS)} "
                            f"or null when not asked",
    "CURVE_FAMILY": {
        P.CURVE_FAMILY_QUESTION: f"one of {list(P.CURVE_FAMILY_ANSWERS)}",
        "PER_CURVE": [{"MEMBER_LABEL": "P01",
                       "READING": f"one of {list(P.CURVE_READINGS)}"}],
    },
    "NEEDS_MORE_CONTEXT": "true or false",
}

PASS_B_SCHEMA = {
    "FEATURE_GROUP_ID": "string, copied from the task",
    "STATUSES": f"one or more of {list(P.PASS_B_STATUSES)}",
    "WHY": "prose",
}

# The two things an answer may never carry back, plus the number screen
# the no-numeric-field schema is supposed to make unnecessary.
_COORD = re.compile(r"[-+]?\d{4,}\s*[,;]\s*[-+]?\d{4,}")
_QUANTITY = re.compile(
    r"\b\d+(\.\d+)?\s*(m2|m²|sqm|square\s+met|metre|meter|m\b|mm\b|cm\b)",
    re.I)
_PERCENT = re.compile(r"\b\d+(\.\d+)?\s*%")
_PROBABILITY = re.compile(r"\b(0\.\d+|1\.0+)\b")


def screen_answer(text: str) -> list:
    """What a semantic answer may not carry back."""
    problems = []
    if _COORD.search(text or ""):
        problems.append("A_COORDINATE_PAIR")
    if _QUANTITY.search(text or ""):
        problems.append("A_MEASURED_QUANTITY")
    if _PERCENT.search(text or ""):
        problems.append("A_PERCENTAGE")
    if _PROBABILITY.search(text or ""):
        problems.append("A_PROBABILITY")
    return problems


def validate_pass_a(row, *, labels) -> list:
    """Vocabulary only. A word outside the vocabulary is not an answer."""
    bad = []
    if row.get("FEATURE_ASSEMBLY_TYPE") not in P.FEATURE_ASSEMBLY_TYPES:
        bad.append(f"NOT_A_FEATURE_ASSEMBLY_TYPE:"
                   f"{row.get('FEATURE_ASSEMBLY_TYPE')}")
    if row.get("ASSEMBLY_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
        bad.append(f"NOT_A_CONFIDENCE_CLASS:{row.get('ASSEMBLY_CONFIDENCE')}")
    for e in row.get("ENTITY_ROLES") or ():
        if e.get("MEMBER_LABEL") not in labels:
            bad.append(f"NOT_A_LABELLED_MEMBER:{e.get('MEMBER_LABEL')}")
        if e.get("SUB_ROLE") not in P.ENTITY_SUB_ROLES:
            bad.append(f"NOT_A_SUB_ROLE:{e.get('SUB_ROLE')}")
        if e.get("CONFIDENCE") not in P.CONFIDENCE_CLASSES:
            bad.append(f"NOT_A_CONFIDENCE_CLASS:{e.get('CONFIDENCE')}")
    for r in row.get("RELATIONS") or ():
        if r.get("RELATION") not in P.RELATIONS:
            bad.append(f"NOT_A_RELATION:{r.get('RELATION')}")
        for m in r.get("MEMBER_LABELS") or ():
            if m not in labels:
                bad.append(f"NOT_A_LABELLED_MEMBER:{m}")
    f = row.get("FENESTRATION_READING")
    if f is not None and f not in P.FENESTRATION_READINGS:
        bad.append(f"NOT_A_FENESTRATION_READING:{f}")
    cf = row.get("CURVE_FAMILY") or {}
    if cf:
        a = cf.get(P.CURVE_FAMILY_QUESTION)
        if a is not None and a not in P.CURVE_FAMILY_ANSWERS:
            bad.append(f"NOT_A_CURVE_FAMILY_ANSWER:{a}")
        for c in cf.get("PER_CURVE") or ():
            if c.get("READING") not in P.CURVE_READINGS:
                bad.append(f"NOT_A_CURVE_READING:{c.get('READING')}")
            if c.get("MEMBER_LABEL") not in labels:
                bad.append(f"NOT_A_LABELLED_MEMBER:{c.get('MEMBER_LABEL')}")
    return bad


def validate_pass_b(row) -> list:
    bad = [s for s in (row.get("STATUSES") or ())
           if s not in P.PASS_B_STATUSES]
    return [f"NOT_A_PASS_B_STATUS:{sorted(bad)}"] if bad else []


def brief_hash() -> str:
    return hashlib.sha256(
        (PASS_A_BRIEF + "|" + PASS_B_BRIEF).encode("utf-8")).hexdigest()
