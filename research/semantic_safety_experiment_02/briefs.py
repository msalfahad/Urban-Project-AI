"""The three briefs. One sandbox, three readers, three different jobs.

The reference, A19 and the checker see exactly the same crops and the
same tags. What separates them is what they are asked and what they are
told about each other, which is nothing. None of the three ever sees
another's answer, and none of them is told that another exists.

The question this experiment asks is a safety question, so all three
briefs put the relation first and the entity roles last. What a feature
IS matters less than whether space is physically divided at it.
"""

from __future__ import annotations

import hashlib

from research.semantic_safety_experiment_02 import protocol as P

_COMMON = """\
YOU ARE LOOKING AT ONE LOCAL FEATURE OF AN ARCHITECTURAL GROUND FLOOR PLAN.

The feature's members are drawn in red, each with a lettered tag on a
leader line. Everything else in the crop is context: look at it, do not
answer about it.

ONE CAD LINE IS NOT ONE ARCHITECTURAL THING. A window is glass, frame,
jambs, wall returns and sometimes mullions. A door is a leaf, a swing,
jambs, an opening and maybe a threshold. A wall body is two faces plus
returns, interrupted by openings. So read the marked group as a whole
first, and only then its individual members.

WHAT YOU HAVE
  FEATURE.png        the feature itself, marked
  CONTEXT.png        the surrounding area, so you can tell a window from
                     an internal partition and a counter from a wall
  DETAIL.png         where present, the fine detail of jambs and frames
  TASK.json          the tagged members, each with its CAD layer, entity
                     type, linetype and block, where the drawing exposes
                     them, and which questions apply here
  FLOOR_CONTEXT.txt  a general note about this floor. It does not tell
                     you what any line is

NEVER GIVE A NUMBER. No coordinates, no lengths, no areas, no
percentages, no probabilities. Confidence is a WORD: HIGH, MEDIUM, LOW
or UNRESOLVED. An answer carrying a number is refused outright and the
reading is thrown away.

UNRESOLVED IS A REAL ANSWER. If the crops do not let you decide, say
UNRESOLVED. Saying UNRESOLVED costs a person one look at the drawing.
Guessing costs a wrong building. They are not the same and they are not
scored the same.

Some features carry members drawn in red with NO tag. Those members lie
on top of one another in the source file, so no tag can point at one
without pointing at the other. Read the feature as a whole as usual, and
do not give a role for a member you cannot identify.
"""

_RELATION_VOCABULARY = """\
THE FIRST AND MOST IMPORTANT QUESTION: IS SPACE PHYSICALLY DIVIDED HERE?

Answer with exactly one of these words:

  PHYSICAL_SEPARATOR        built fabric that divides space. A masonry or
                            partition wall body. You cannot walk through
                            it and you cannot see through it
  GLAZED_PHYSICAL_SEPARATOR built fabric that divides space but is glazed.
                            A window or a glazed screen. You cannot walk
                            through it; you CAN see through it. It is not
                            a hole and it is not masonry
  OPENING_IN_SEPARATOR      a doorway, a gap, an archway, a portal. Space
                            FLOWS through here. A person walks through it
  NON_SEPARATOR_FEATURE     something built or drawn that does not divide
                            space at all: a counter face, a floor pattern,
                            a kerb line, a setting-out line
  OBSTACLE                  something that occupies floor but does not
                            define the boundary between two spaces: a
                            column in the open, a fixture, furniture
  OVERHEAD_OR_HIDDEN        geometry not in the cut plane: a beam over, a
                            dashed line for something above or below
  ANNOTATION_OR_DIMENSION   a dimension line, a witness line, a leader, a
                            grid or level mark, a hatch boundary. It is
                            drawing apparatus, not building
  UNRESOLVED                you cannot tell from these crops

THE TWO MISTAKES THAT MATTER MOST

  Calling an OPENING a SEPARATOR closes a doorway that is open. A room
  loses its door.
  Calling a SEPARATOR an OPENING opens a wall that is built. Two rooms
  merge into one.

Both produce a wrong building. If you are between those two, answer
UNRESOLVED rather than pick.

GLAZING IS NOT MASONRY AND IT IS NOT A HOLE. A window divides space -
you cannot walk through it - but it is not a solid wall. Give it
GLAZED_PHYSICAL_SEPARATOR, not PHYSICAL_SEPARATOR and not
OPENING_IN_SEPARATOR.
"""

REFERENCE_BRIEF = _COMMON + "\n" + _RELATION_VOCABULARY + """
YOU ARE ESTABLISHING WHAT IS ACTUALLY THERE.

Read carefully and slowly. Your reading is the standard another reading
will be measured against, so an answer you are not sure of is worse than
no answer. You may not guess. If the crops do not settle it, say
UNRESOLVED and say what would have settled it.

ANSWER, one JSON object per feature:

  CANONICAL_FEATURE_ID    copied exactly from TASK.json
  REFERENCE_RELATION      one word from the list above
  REFERENCE_CONFIDENCE    HIGH, MEDIUM, LOW or UNRESOLVED
  WHY                     what in the picture makes you say it
  ASSEMBLY_TYPE           what the marked group is as a whole, from
                          SECONDARY_ASSEMBLY_TYPES in TASK.json, or null
  ENTITY_REFERENCE        [] or a list of
                          {MEMBER_LABEL, REFERENCE_ROLE, WHY} using only
                          tags that appear in TASK.json and roles from
                          TERTIARY_ENTITY_SUB_ROLES
  NEEDS_ADDITIONAL_CONTEXT  true or false
  WHAT_WOULD_RESOLVE_IT    a sentence, or null

Answer only the questions TASK.json marks as applying here.
"""

A19_BRIEF = _COMMON + "\n" + _RELATION_VOCABULARY + """
YOU ARE READING THE DRAWING AND SAYING WHAT IT MEANS.

You are not being asked where anything is, how big it is, or how much of
it there is. The CAD file already knows where every line is, exactly,
and it is the authority on that. You are the authority on meaning, and
only over what is tagged.

If one crop does not let you decide, you may ask ONCE for a wider view of
a feature by setting ESCALATION. Use it for the feature you most need it
for; you do not get a second.

ANSWER, one JSON object per feature:

  CANONICAL_FEATURE_ID    copied exactly from TASK.json
  A19_RELATION            one word from the list above
  A19_CONFIDENCE          HIGH, MEDIUM, LOW or UNRESOLVED
  WHY                     what in the picture makes you say it
  ASSEMBLY_TYPE           from SECONDARY_ASSEMBLY_TYPES, or null
  ASSEMBLY_CONFIDENCE     a word, or null
  ASSEMBLY_WHY            a sentence, or null
  ENTITY_ASSERTIONS       [] or a list of
                          {MEMBER_LABEL, A19_SUB_ROLE, CONFIDENCE, WHY}
                          using only tags that appear in TASK.json
  NEEDS_ADDITIONAL_CONTEXT  true or false
  ESCALATION              null, or {WHY} on at most one feature

Say HIGH only when you would stake the building on it. A HIGH answer that
is wrong about separation is the worst outcome this reading can produce.
"""

CHECKER_BRIEF = _COMMON + """
YOU HAVE ONE QUESTION TO ANSWER, AND ONLY ONE.

  IS THERE A PHYSICAL SEPARATOR AT THIS FEATURE?

That is: does built fabric divide space here, so that a person cannot
walk from one side to the other?

Answer with exactly one of:

  YES       built fabric divides space here. A wall body, a partition
  GLAZED    built fabric divides space here and it is glazed. A window,
            a glazed screen. You cannot walk through it, you can see
            through it
  NO        nothing here divides space. Annotation, a floor line, a
            counter face, geometry that is not in the cut plane
  OPENING   space FLOWS through here. A doorway, a gap, an archway
  OBSTACLE  something occupies the floor but does not form the boundary
            between two spaces: a column in the open, a fixture
  UNRESOLVED  you cannot tell from these crops

Do not answer any other question. Do not describe the assembly, do not
name the members, do not give roles. One word and your reason.

ANSWER, one JSON object per feature:

  CANONICAL_FEATURE_ID    copied exactly from TASK.json
  CHECKER_ANSWER          one of the words above
  CHECKER_CONFIDENCE      HIGH, MEDIUM, LOW or UNRESOLVED
  WHY                     what in the picture makes you say it
"""

BRIEFS = {
    "REFERENCE": REFERENCE_BRIEF,
    "A19": A19_BRIEF,
    "CHECKER": CHECKER_BRIEF,
}

WHAT_NO_BRIEF_MENTIONS = (
    "no brief tells its reader that the other readers exist, what any of "
    "them answered, or that its own answer will be compared with "
    "anything. A reader that knew it was being checked could agree its "
    "way to a good score without ever being right",
)


def brief_hash(name: str) -> str:
    return hashlib.sha256(BRIEFS[name].encode("utf-8")).hexdigest()


def record() -> dict:
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "BRIEF_SHA256": {k: brief_hash(k) for k in sorted(BRIEFS)},
        "WHAT_NO_BRIEF_MENTIONS": list(WHAT_NO_BRIEF_MENTIONS),
        "THE_SAME_CROPS_AND_THE_SAME_TAGS_SERVE_ALL_THREE": True,
        "checker_question": P.CHECKER_QUESTION,
        "checker_answers": list(P.CHECKER_ANSWERS),
        "no_voting": P.NO_VOTING,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(record(), indent=2))
