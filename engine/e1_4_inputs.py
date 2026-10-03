"""E1.4 — the run's identity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

MODEL = "E1_4_SOURCE_ROLE_LABEL_SEED_OPENING_FRAGMENT_FOUNDATION_REPAIR_V1"

RUN_CLASS = "CONTROLLED_INTEGRATION_REGRESSION"

WHAT_E1_4_REPAIRS = (
    "the evidence supplied TO the boundary walk, and the representation of "
    "partial results. The walk itself and every invariant E1.3 established "
    "for it are preserved: room-side paired-face selection, no nearest "
    "face, no area or closure optimisation, no challenger owning a "
    "coordinate, exact curves, raw-chain continuity, a ring that is only "
    "its own chain and contains its seed, a polygon repair that cannot "
    "invent closure, portal direction following traversal, and open "
    "regions that may remain unclosed")

WHAT_E1_4_DOES_NOT_DO = (
    "no E2, no workbook, no benchmark quantity, no reconciliation to a "
    "known area, no manually corrected geometry, and no quantity of any "
    "kind. E1.4 does not overwrite E1, E1.1, E1.2 or E1.3")

WHAT_SUCCESS_MEANS = (
    "not more released rooms, not a matched Kitchen or Pantry, not a "
    "higher closure rate and not a satisfied challenger. E1.4 succeeds "
    "when every executed source file is bound, semantic role is separate "
    "from boundary capability, a seed belongs to the label evidence it "
    "claims, door evidence can find an opening without a wall-end gap, an "
    "open room keeps every independently established fragment without "
    "inventing the missing side, visual uncertainty blocks only geometry "
    "it could actually change, and every released region is reproducible "
    "and auditable from source evidence")


@dataclass(frozen=True)
class E1_4Run:
    run_id: str = "E1_4-P7757-GF-001"
    pass_id: str = "E1.4"
    subject: str = ("source role, label seed, opening and fragment "
                    "foundation repair")
    run_class: str = RUN_CLASS

    def record(self) -> dict:
        return {
            "RUN_ID": self.run_id,
            "PASS_ID": self.pass_id,
            "SUBJECT": self.subject,
            "E1_4_RUN_CLASS": self.run_class,
            "E1_4_MODEL": MODEL,
            "what_e1_4_repairs": WHAT_E1_4_REPAIRS,
            "what_e1_4_does_not_do": WHAT_E1_4_DOES_NOT_DO,
            "what_success_means": WHAT_SUCCESS_MEANS,
        }


def model_hash() -> str:
    return hashlib.sha256(MODEL.encode("utf-8")).hexdigest()[:24]
