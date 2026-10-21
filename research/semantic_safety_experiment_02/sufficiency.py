"""Can this drawing answer the safety question? Decided by rule, not by eye.

The threshold was declared in the protocol and hashed BEFORE Reference A
was opened. This module applies it to the frozen reference register and
returns a verdict. It is deliberately a separate step that reads only the
frozen file, so the answer cannot drift with whatever I happen to
remember from a reader's summary.

    python3 -m research.semantic_safety_experiment_02.sufficiency
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")

# The two sides of the question. Neither can be inferred from the other,
# so neither can stand in for the other.
REQUIRED_TO_ANSWER_AT_ALL = (P.PHYSICAL_SEPARATOR, P.OPENING_IN_SEPARATOR)

# These carry a rate of their own only at the same count. Below it they
# are reported as counts and the limitation is named.
REQUIRED_TO_CARRY_A_RATE = (P.GLAZED_PHYSICAL_SEPARATOR,
                            P.NON_SEPARATOR_FEATURE)


def main() -> int:
    path = OUT / "04_REFERENCE_A.json"
    if not path.exists():
        raise SystemExit(
            "Reference A is not frozen yet, so sufficiency cannot be "
            "judged. Run record.py --stage reference_a first")

    ref = json.loads(path.read_text("utf-8"))
    dist = ref["RELATION_DISTRIBUTION"]
    need = P.MIN_EXAMPLES_TO_CARRY_A_RATE

    blocking, thin = [], []
    for cls in REQUIRED_TO_ANSWER_AT_ALL:
        got = dist.get(cls, 0)
        if got < need:
            blocking.append({"CLASS": cls, "established": got,
                             "required": need})
    for cls in REQUIRED_TO_CARRY_A_RATE:
        got = dist.get(cls, 0)
        if got < need:
            thin.append({"CLASS": cls, "established": got,
                         "required_to_carry_a_rate": need})

    answerable = not blocking
    rec = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "SAMPLE_ID": P.SAMPLE_ID,
        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_THRESHOLD_WAS_DECLARED_BEFORE_REFERENCE_A_WAS_OPENED": True,
        "SUFFICIENCY_RULE": P.SUFFICIENCY_RULE,
        "MIN_EXAMPLES_TO_CARRY_A_RATE": need,
        "REFERENCE_A_RELATION_DISTRIBUTION": dist,
        "features_read": ref.get("features_read"),
        "CLASSES_REQUIRED_TO_ANSWER_THE_QUESTION":
            list(REQUIRED_TO_ANSWER_AT_ALL),
        "CLASSES_SHORT_OF_THE_THRESHOLD": blocking,
        "CLASSES_TOO_THIN_TO_CARRY_A_RATE": thin,
        "VERDICT": ("THE_QUESTION_CAN_BE_ANSWERED_ON_THIS_SAMPLE"
                    if answerable else P.SOURCE_POPULATION_LIMITATION),
        "WHAT_HAPPENS_NEXT": (
            "continue: Reference B on every topology-critical feature, "
            "freeze the reference, then A19, then the checker, then score"
            if answerable else
            "STOP. Report the source population limitation. There is no "
            "SAFETY_SAMPLE_04"),
        "what_a_source_population_limitation_means":
            P.WHAT_A_SOURCE_POPULATION_LIMITATION_MEANS,
        "this_is_the_last_sample_redesign":
            P.THIS_IS_THE_LAST_SAMPLE_REDESIGN,
        "THE_THRESHOLD_IS_NOT_NEGOTIABLE_NOW": (
            "it was fixed before any answer existed. Lowering it here "
            "because the count came in just under would make every "
            "figure that followed a number chosen to clear a bar rather "
            "than a measurement"),
    }
    p = OUT / "10_SUFFICIENCY_VERDICT.json"
    p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    rec["SHA256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    print(json.dumps({k: rec[k] for k in (
        "SAMPLE_ID", "features_read", "REFERENCE_A_RELATION_DISTRIBUTION",
        "CLASSES_SHORT_OF_THE_THRESHOLD",
        "CLASSES_TOO_THIN_TO_CARRY_A_RATE", "VERDICT",
        "WHAT_HAPPENS_NEXT", "SHA256")}, indent=2))
    return 0 if answerable else 1


if __name__ == "__main__":
    raise SystemExit(main())
