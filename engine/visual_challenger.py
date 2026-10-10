"""E1.2 §8 — a pass that actually looks, and may only say what it sees.

Two stages, because an overlay anchors a reader. Show somebody a proposed
boundary and ask "is this right?" and they will find reasons it is. So
the first pass never sees the proposal:

    PASS V1   SOURCE ONLY
              a crop of the original sheet, the identity text, and
              general architectural semantics. NO candidate boundary.
              It writes down what it can see: walls, open sides,
              doorways, glazing, counters, bars, casework, columns,
              stairs, curves, low partitions, ambiguous lines and which
              spaces read as connected. Then V1 IS FROZEN

    PASS V2   CHALLENGE
              the same crop, the FROZEN V1 observation, the candidate
              overlay and its legend. One question: does the proposed
              boundary follow actual physical enclosure?

What the challenger may do: disagree, and veto a release.

What it may NOT do, ever:

    move a CAD coordinate
    propose a corrected polygon
    calculate an area, a length or a quantity
    receive a benchmark, an expected area or any previous numeric answer

Correction is CAD's job, made after semantic evidence exists. The
challenger supplies evidence about meaning, and nothing else.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import export_provenance as prov

MODEL = "A_COLD_LOOK_FIRST_THEN_A_CHALLENGE_V1"

V1 = "PASS_V1_SOURCE_ONLY"
V2 = "PASS_V2_CHALLENGE"

# --- what V1 may report -------------------------------------------------
V1_OBSERVATIONS = ("VISIBLE_PHYSICAL_WALLS", "OPEN_SIDES", "DOORWAYS",
                   "GLAZING", "COUNTERS", "BARS", "CASEWORK", "COLUMNS",
                   "STAIRS", "CURVES", "LOW_PARTITIONS", "AMBIGUOUS_LINES",
                   "CONNECTED_FUNCTIONAL_ZONES")

# --- what V2 may answer -------------------------------------------------
VISUALLY_CONSISTENT = "VISUALLY_CONSISTENT"
POSSIBLE_UNDER_CAPTURE = "POSSIBLE_UNDER_CAPTURE"
POSSIBLE_OVER_CAPTURE = "POSSIBLE_OVER_CAPTURE"
INTERNAL_CASEWORK_USED_AS_BOUNDARY = "INTERNAL_CASEWORK_USED_AS_BOUNDARY"
COUNTER_OR_BAR_USED_AS_WALL = "COUNTER_OR_BAR_USED_AS_WALL"
OPEN_SIDE_FALSELY_CLOSED = "OPEN_SIDE_FALSELY_CLOSED"
WALL_FALSELY_REMOVED = "WALL_FALSELY_REMOVED"
COLUMN_ROLE_UNRESOLVED = "COLUMN_ROLE_UNRESOLVED"
WRONG_FUNCTIONAL_REGION = "WRONG_FUNCTIONAL_REGION"
BOUNDARY_SEMANTIC_CONFLICT = "BOUNDARY_SEMANTIC_CONFLICT"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"

V2_STATUSES = (VISUALLY_CONSISTENT, POSSIBLE_UNDER_CAPTURE,
               POSSIBLE_OVER_CAPTURE, INTERNAL_CASEWORK_USED_AS_BOUNDARY,
               COUNTER_OR_BAR_USED_AS_WALL, OPEN_SIDE_FALSELY_CLOSED,
               WALL_FALSELY_REMOVED, COLUMN_ROLE_UNRESOLVED,
               WRONG_FUNCTIONAL_REGION, BOUNDARY_SEMANTIC_CONFLICT,
               HUMAN_REVIEW_REQUIRED)

# Only this one lets a region release on the visual evidence.
V2_PERMITS_RELEASE = (VISUALLY_CONSISTENT,)

THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE = (
    "the visual pass supplies evidence about MEANING. It may say that a "
    "line reads as a counter rather than a wall, and it may veto a "
    "release. It may not move a CAD coordinate, propose a corrected "
    "polygon, or compute an area, a length or any quantity. Correction is "
    "made in CAD, by code, after the semantic evidence is established")

AN_OVERLAY_ANCHORS_A_READER = (
    "V1 never sees the proposed boundary. Shown a proposal first, a "
    "reader finds reasons it is right; asked what is there first, the "
    "same reader describes the drawing. V1 is frozen before V2 is given "
    "the overlay")

WHAT_THE_CHALLENGER_NEVER_RECEIVES = (
    "a benchmark, a human take-off, an expected area, a corrected "
    "geometry, a target quantity, or any previous numeric answer")


class VisualChallengerError(RuntimeError):
    """The challenger was asked for, or returned, something it may not."""


# A returned observation is prose. These patterns catch the two things it
# is never allowed to contain: a coordinate it invented, and a quantity.
_COORD = re.compile(r"[-+]?\d{4,}\s*[,;]\s*[-+]?\d{4,}")
_QUANTITY = re.compile(
    r"\b\d+(\.\d+)?\s*(m2|m²|sqm|square\s+met|m\b|mm\b|cm\b)", re.I)


def screen_return(text: str) -> list:
    """What a challenger's answer may not carry back."""
    problems = []
    if _COORD.search(text or ""):
        problems.append("A_COORDINATE_PAIR")
    if _QUANTITY.search(text or ""):
        problems.append("A_MEASURED_QUANTITY")
    return problems


def model_hash() -> str:
    parts = ([MODEL, V1, V2] + list(V1_OBSERVATIONS) + list(V2_STATUSES)
             + list(V2_PERMITS_RELEASE))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Task:
    """One candidate's turn in front of the challenger."""

    task_id: str = ""
    candidate_id: str = ""
    identity: str = ""
    crop_path: str = ""
    overlay_path: str = ""
    legend: tuple = ()
    stage: str = V1

    def manifest(self) -> dict:
        rows = [{"kind": "SOURCE_SHEET_CROP", "path": self.crop_path,
                 "RAW_FILE_SHA256": (prov.raw_sha256(self.crop_path)
                                     if self.crop_path
                                     and Path(self.crop_path).exists()
                                     else "")},
                {"kind": "IDENTITY_TEXT_ONLY", "value": self.identity}]
        if self.stage == V2:
            rows.append({"kind": "CANDIDATE_OVERLAY",
                         "path": self.overlay_path,
                         "RAW_FILE_SHA256":
                             (prov.raw_sha256(self.overlay_path)
                              if self.overlay_path
                              and Path(self.overlay_path).exists() else "")})
            rows.append({"kind": "OVERLAY_LEGEND", "value": list(self.legend)})
            rows.append({"kind": "FROZEN_V1_OBSERVATION",
                         "value": "supplied verbatim from the frozen V1 "
                                  "register"})
        body = {"TASK_ID": self.task_id, "STAGE": self.stage,
                "CANDIDATE_ID": self.candidate_id,
                "inputs": rows,
                "what_it_never_receives": WHAT_THE_CHALLENGER_NEVER_RECEIVES,
                "it_may_not_move_a_coordinate":
                    THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE}
        body["INPUT_MANIFEST_HASH"] = prov.canonical_sha256(body)
        return body


V1_BRIEF = """\
You are looking at a crop of an architectural floor plan, as printed for a
builder. You are told only which space this crop is centred on. You have
NOT been shown anyone's proposed boundary, and you must not ask for one.

Describe what is DRAWN. For the space named, report, in plain words and
with a short reason for each:

  VISIBLE_PHYSICAL_WALLS   which sides are closed by a drawn wall
  OPEN_SIDES               which sides are open to another space
  DOORWAYS                 where a wall is broken for a door
  GLAZING                  windows or glazed panels in a wall
  COUNTERS                 a worktop or counter run
  BARS                     a bar or breakfast counter, often with seating
  CASEWORK                 fitted units, cabinets, wardrobes, vanities
  COLUMNS                  structural columns or piers
  STAIRS                   treads, a flight, a winder
  CURVES                   any curved built element
  LOW_PARTITIONS           a half-height wall, a balustrade, a planter wall
  AMBIGUOUS_LINES          double lines you genuinely cannot classify
  CONNECTED_FUNCTIONAL_ZONES  which neighbouring spaces read as continuous

Rules:
  - describe, do not measure. No areas, no lengths, no coordinates
  - where the drawing does not settle something, say so
  - a doorway is a hole in a wall; an open side has no wall at all
"""

V2_BRIEF = """\
You are shown the same crop of an architectural floor plan, your own
earlier observation of it (frozen, quoted below), and ONE proposed
boundary drawn over it with a legend.

One question: DOES THE PROPOSED BOUNDARY FOLLOW ACTUAL PHYSICAL
ENCLOSURE?

Answer with one or more of these, and a short reason for each:

  VISUALLY_CONSISTENT                 it follows the drawn enclosure
  POSSIBLE_UNDER_CAPTURE              it stops inside the real enclosure
  POSSIBLE_OVER_CAPTURE               it takes in space that is not this one
  INTERNAL_CASEWORK_USED_AS_BOUNDARY  it runs along fitted units
  COUNTER_OR_BAR_USED_AS_WALL         it runs along a counter or bar
  OPEN_SIDE_FALSELY_CLOSED            it closes a side the drawing leaves open
  WALL_FALSELY_REMOVED                it leaves out a wall that is drawn
  COLUMN_ROLE_UNRESOLVED              a loop on the ring may not be a column
  WRONG_FUNCTIONAL_REGION             this is not the space that is named
  BOUNDARY_SEMANTIC_CONFLICT          the ring mixes incompatible elements
  HUMAN_REVIEW_REQUIRED               you cannot settle it from this crop

You may VETO the release. You may NOT move a coordinate, propose a
corrected polygon, or give any area, length or quantity. If the boundary
is wrong, say WHAT is wrong and WHY, and leave the correction to CAD.
"""


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "STAGES": [V1, V2],
        "V1_OBSERVATIONS": list(V1_OBSERVATIONS),
        "V2_STATUSES": list(V2_STATUSES),
        "V2_PERMITS_RELEASE": list(V2_PERMITS_RELEASE),
        "V1_BRIEF": V1_BRIEF,
        "V2_BRIEF": V2_BRIEF,
        "why": {
            "an_overlay_anchors_a_reader": AN_OVERLAY_ANCHORS_A_READER,
            "the_challenger_may_not_move_a_coordinate":
                THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
            "what_the_challenger_never_receives":
                WHAT_THE_CHALLENGER_NEVER_RECEIVES,
        },
    }
