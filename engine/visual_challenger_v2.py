"""E1.3 §2, §14, §17 — the challenger names relations and stays physical.

Three corrections to the E1.2 pass, all of them visible in Kitchen.

§2  V1 wrote its findings into a bucket called OPEN_SIDES, and the note
    it put there - that the main body continues into its own southern leg
    with no wall between them - was a true statement about the INSIDE of
    the region. Downstream it became "open to another space". V1 now
    classifies each edge into a RELATION, and the two relations that
    describe a candidate's own interior are distinguishable from the one
    that says another space begins.

§14 V2's question is physical enclosure. POSSIBLE_OVER_CAPTURE therefore
    means the boundary CROSSES A PHYSICAL BOUNDARY and takes in another
    physical region. "This continuous area might have a second name" is a
    different observation, it is recorded as POSSIBLE_FUNCTIONAL_SUBZONE,
    and it cannot veto anything.

§17 The run records what actually answered. Where the runtime does not
    expose a field, it says NOT_EXPOSED_BY_RUNTIME rather than leaving a
    blank a reader might fill in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from engine import edge_relation as edge
from engine import export_provenance as prov
from engine import visual_challenger as v1x

MODEL = "THE_CHALLENGER_NAMES_RELATIONS_AND_JUDGES_PHYSICAL_ENCLOSURE_V1"

V1 = "PASS_V1_SOURCE_ONLY"
V2 = "PASS_V2_PHYSICAL_ENCLOSURE_CHALLENGE"

# What V1 reports. The edge list replaces OPEN_SIDES; everything else is
# carried over because it was never the problem.
V1_EDGE_FINDINGS = "EDGES"
V1_OBSERVATIONS = ("EDGES", "VISIBLE_PHYSICAL_WALLS", "DOORWAYS", "GLAZING",
                   "COUNTERS", "BARS", "CASEWORK", "COLUMNS",
                   "COLUMNS_EXPOSED_INTO_THE_ROOM", "STAIRS", "CURVES",
                   "LOW_PARTITIONS", "AMBIGUOUS_LINES",
                   "CONNECTED_FUNCTIONAL_ZONES", "POSSIBLE_FUNCTIONAL_SUBZONES")

# ------------------------------------------------------------ V2 statuses
VISUALLY_CONSISTENT = "VISUALLY_CONSISTENT"
POSSIBLE_UNDER_CAPTURE = "POSSIBLE_UNDER_CAPTURE"
POSSIBLE_OVER_CAPTURE = "POSSIBLE_OVER_CAPTURE"
INTERNAL_CASEWORK_USED_AS_BOUNDARY = "INTERNAL_CASEWORK_USED_AS_BOUNDARY"
COUNTER_OR_BAR_USED_AS_WALL = "COUNTER_OR_BAR_USED_AS_WALL"
OPEN_SIDE_FALSELY_CLOSED = "OPEN_SIDE_FALSELY_CLOSED"
WALL_FALSELY_REMOVED = "WALL_FALSELY_REMOVED"
COLUMN_ROLE_UNRESOLVED = "COLUMN_ROLE_UNRESOLVED"
COLUMN_EXPOSURE_UNRESOLVED = "COLUMN_EXPOSURE_UNRESOLVED"
BOUNDARY_SEMANTIC_CONFLICT = "BOUNDARY_SEMANTIC_CONFLICT"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
# non-blocking observations about NAMING, forwarded and never a veto
POSSIBLE_FUNCTIONAL_SUBZONE = "POSSIBLE_FUNCTIONAL_SUBZONE"
WRONG_FUNCTIONAL_REGION = "WRONG_FUNCTIONAL_REGION"

V2_STATUSES = (VISUALLY_CONSISTENT, POSSIBLE_UNDER_CAPTURE,
               POSSIBLE_OVER_CAPTURE, INTERNAL_CASEWORK_USED_AS_BOUNDARY,
               COUNTER_OR_BAR_USED_AS_WALL, OPEN_SIDE_FALSELY_CLOSED,
               WALL_FALSELY_REMOVED, COLUMN_ROLE_UNRESOLVED,
               COLUMN_EXPOSURE_UNRESOLVED, BOUNDARY_SEMANTIC_CONFLICT,
               HUMAN_REVIEW_REQUIRED, POSSIBLE_FUNCTIONAL_SUBZONE,
               WRONG_FUNCTIONAL_REGION)

# §14: statuses about PHYSICAL enclosure. Only these may veto.
PHYSICAL_STATUSES = (POSSIBLE_UNDER_CAPTURE, POSSIBLE_OVER_CAPTURE,
                     INTERNAL_CASEWORK_USED_AS_BOUNDARY,
                     COUNTER_OR_BAR_USED_AS_WALL, OPEN_SIDE_FALSELY_CLOSED,
                     WALL_FALSELY_REMOVED, COLUMN_ROLE_UNRESOLVED,
                     COLUMN_EXPOSURE_UNRESOLVED, BOUNDARY_SEMANTIC_CONFLICT)

# Statuses about NAMING. Recorded, forwarded to the identity dimension,
# and structurally incapable of blocking a physical release.
FUNCTIONAL_STATUSES = (POSSIBLE_FUNCTIONAL_SUBZONE, WRONG_FUNCTIONAL_REGION)

# Neither physical evidence nor a naming question: the crop did not settle it.
UNDECIDED_STATUSES = (HUMAN_REVIEW_REQUIRED,)

V2_PERMITS_RELEASE = (VISUALLY_CONSISTENT,)

OVER_CAPTURE_IS_A_PHYSICAL_CLAIM = (
    "POSSIBLE_OVER_CAPTURE means the proposed boundary CROSSES A PHYSICAL "
    "BOUNDARY - a wall, a portal, a drawn separator - and takes in part of "
    "another physical region. A physically continuous area that might "
    "carry a second name is not over-capture; it is a question about "
    "naming, and the answer to it does not move a wall")

A_NAMING_STATUS_MAY_NOT_VETO = (
    "a status about what a space is CALLED is forwarded to the identity "
    "dimension and recorded there. It never appears among the reasons a "
    "physical boundary was withheld, because settling it would not change "
    "one coordinate of that boundary")

NOT_EXPOSED_BY_RUNTIME = "NOT_EXPOSED_BY_RUNTIME"

VisualChallengerError = v1x.VisualChallengerError
screen_return = v1x.screen_return
THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE = \
    v1x.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE
AN_OVERLAY_ANCHORS_A_READER = v1x.AN_OVERLAY_ANCHORS_A_READER
WHAT_THE_CHALLENGER_NEVER_RECEIVES = v1x.WHAT_THE_CHALLENGER_NEVER_RECEIVES


def model_hash() -> str:
    parts = ([MODEL, V1, V2] + list(V1_OBSERVATIONS) + list(V2_STATUSES)
             + list(PHYSICAL_STATUSES) + list(FUNCTIONAL_STATUSES))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def split_statuses(statuses) -> dict:
    """Sort an answer into what it says about walls and about names."""
    s = [x for x in (statuses or ()) if x in V2_STATUSES]
    unknown = sorted({x for x in (statuses or ()) if x not in V2_STATUSES})
    physical = sorted({x for x in s if x in PHYSICAL_STATUSES})
    functional = sorted({x for x in s if x in FUNCTIONAL_STATUSES})
    undecided = sorted({x for x in s if x in UNDECIDED_STATUSES})
    return {
        "PHYSICAL_STATUSES": physical,
        "FUNCTIONAL_STATUSES": functional,
        "UNDECIDED_STATUSES": undecided,
        "not_a_v2_status": unknown,
        "vetoes_physical_release": bool(physical),
        "permits_physical_release": (
            VISUALLY_CONSISTENT in s and not physical and not undecided),
        "a_naming_status_may_not_veto": A_NAMING_STATUS_MAY_NOT_VETO,
    }


def assert_no_naming_status_vetoes(failed_release_gates) -> None:
    """A naming status among the release reasons is a bug, not a result."""
    bad = sorted({c for c in failed_release_gates or ()
                  if any(f in str(c) for f in FUNCTIONAL_STATUSES)})
    if bad:
        raise VisualChallengerError(
            f"a naming status appears as a reason to withhold: {bad}. "
            + A_NAMING_STATUS_MAY_NOT_VETO)


# ---------------------------------------------------------- provenance
@dataclass
class RuntimeProvenance:
    """§17 — what actually answered, recorded when it answered."""

    provider: str = NOT_EXPOSED_BY_RUNTIME
    model_identifier: str = NOT_EXPOSED_BY_RUNTIME
    model_version_or_alias: str = NOT_EXPOSED_BY_RUNTIME
    sampling_configuration: str = NOT_EXPOSED_BY_RUNTIME
    tool_or_runtime_configuration: str = NOT_EXPOSED_BY_RUNTIME
    prompt_sha256: str = ""
    input_manifest_sha256: str = ""
    output_sha256: str = ""

    def record(self) -> dict:
        out = {
            "provider": self.provider or NOT_EXPOSED_BY_RUNTIME,
            "model_identifier": self.model_identifier or NOT_EXPOSED_BY_RUNTIME,
            "model_version_or_alias":
                self.model_version_or_alias or NOT_EXPOSED_BY_RUNTIME,
            "sampling_configuration":
                self.sampling_configuration or NOT_EXPOSED_BY_RUNTIME,
            "tool_or_runtime_configuration":
                self.tool_or_runtime_configuration or NOT_EXPOSED_BY_RUNTIME,
            "PROMPT_SHA256": self.prompt_sha256,
            "INPUT_MANIFEST_SHA256": self.input_manifest_sha256,
            "OUTPUT_SHA256": self.output_sha256,
        }
        out["fields_not_exposed_by_the_runtime"] = sorted(
            k for k, v in out.items() if v == NOT_EXPOSED_BY_RUNTIME)
        out["nothing_here_was_inferred"] = (
            "a field the runtime does not expose is recorded as "
            "NOT_EXPOSED_BY_RUNTIME. It is never filled in from what the "
            "run was probably using")
        return out


@dataclass
class Task:
    """One candidate's turn, with its provenance attached."""

    task_id: str = ""
    candidate_id: str = ""
    identity: str = ""
    crop_path: str = ""
    overlay_path: str = ""
    legend: tuple = ()
    stage: str = V1
    brief: str = ""
    provenance: RuntimeProvenance = field(default_factory=RuntimeProvenance)

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
        self.provenance.input_manifest_sha256 = body["INPUT_MANIFEST_HASH"]
        if self.brief:
            self.provenance.prompt_sha256 = prov.canonical_sha256(self.brief)
        body["RUNTIME_PROVENANCE"] = self.provenance.record()
        return body


V1_BRIEF = """\
You are looking at a crop of an architectural floor plan, as printed for a
builder. You are told only which space this crop is centred on. You have
NOT been shown anyone's proposed boundary, and you must not ask for one.

Describe what is DRAWN.

FIRST, and most important: go round the named space and, for EVERY side of
it, say which ONE of these relations holds, with a short reason:

  PHYSICAL_BOUNDARY_WALL                     a drawn wall closes this side
  PHYSICAL_BOUNDARY_DOOR_PORTAL              a wall here is broken for a door
  PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE      no wall, and ANOTHER space begins
  INTERNAL_CONTINUITY_WITHIN_CANDIDATE       no wall, and THIS SAME space
                                             continues - round a corner, past
                                             a nib, into its own leg
  FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL   nothing is built here, but the
                                             area beyond might be given its
                                             own name
  EXTERNAL_OPENING                           it opens to outside the building
  GLAZING                                    a window or glazed panel
  UNRESOLVED_EDGE_RELATION                   the crop does not settle it

The difference between the third and the fourth is the single most useful
thing you can tell us. "No wall here, and this is still the same room" and
"no wall here, and the next room starts" look alike and mean opposite
things. If you cannot tell which, say UNRESOLVED_EDGE_RELATION.

Then report, in plain words and with a short reason for each:

  VISIBLE_PHYSICAL_WALLS          which sides are closed by a drawn wall
  DOORWAYS                        where a wall is broken for a door, and
                                  whether a leaf, a swing arc or a door
                                  block is actually drawn there
  GLAZING                         windows or glazed panels in a wall
  COUNTERS / BARS / CASEWORK      worktops, breakfast bars, fitted units
  COLUMNS                         structural columns or piers
  COLUMNS_EXPOSED_INTO_THE_ROOM   of those, which ones visibly STAND IN the
                                  room - the finish wraps them, or they
                                  project past the wall face - as against
                                  sitting inside or behind a wall whose face
                                  runs straight past them
  STAIRS / CURVES / LOW_PARTITIONS
  AMBIGUOUS_LINES                 double lines you genuinely cannot classify
  CONNECTED_FUNCTIONAL_ZONES      which neighbouring spaces read as continuous
  POSSIBLE_FUNCTIONAL_SUBZONES    parts of this space that might be named
                                  separately, and whether ANYTHING is drawn
                                  between them

Rules:
  - describe, do not measure. No areas, no lengths, no coordinates
  - where the drawing does not settle something, say so
  - a doorway is a hole in a wall; an open side has no wall at all
"""

V2_BRIEF = """\
You are shown the same crop of an architectural floor plan, your own
earlier observation of it (frozen, quoted below), and ONE proposed
boundary drawn over it with a legend.

One question, and it is about PHYSICAL ENCLOSURE only:

    DOES THE PROPOSED BOUNDARY FOLLOW THE ENCLOSURE THE DRAWING BUILDS?

Answer with one or more of these, and a short reason for each:

  VISUALLY_CONSISTENT                 it follows the drawn enclosure
  POSSIBLE_UNDER_CAPTURE              it stops inside the real enclosure
  POSSIBLE_OVER_CAPTURE               it CROSSES A PHYSICAL BOUNDARY - a
                                      wall, a portal, a drawn separator -
                                      and takes in part of another PHYSICAL
                                      region
  INTERNAL_CASEWORK_USED_AS_BOUNDARY  it runs along fitted units
  COUNTER_OR_BAR_USED_AS_WALL         it runs along a counter or bar
  OPEN_SIDE_FALSELY_CLOSED            it closes a side the drawing leaves open
  WALL_FALSELY_REMOVED                it leaves out a wall that is drawn
  COLUMN_ROLE_UNRESOLVED              a loop on the ring may not be a column
  COLUMN_EXPOSURE_UNRESOLVED          a column deforms the ring, and you
                                      cannot tell whether it actually stands
                                      in the room or sits behind a wall face
  BOUNDARY_SEMANTIC_CONFLICT          the ring mixes incompatible elements
  HUMAN_REVIEW_REQUIRED               you cannot settle it from this crop

And, separately, these say something about the NAME rather than the walls.
They are recorded and passed on. They do NOT veto the boundary:

  POSSIBLE_FUNCTIONAL_SUBZONE         this area is physically continuous, but
                                      part of it might be called something
                                      else
  WRONG_FUNCTIONAL_REGION             this is not the space that is named

Be careful with POSSIBLE_OVER_CAPTURE. If nothing is built between two
parts of the proposed area - no wall, no portal, no drawn separator - then
the boundary has not crossed a physical boundary, whatever the two parts
might be called. That is POSSIBLE_FUNCTIONAL_SUBZONE, not over-capture.

You may VETO the release on a PHYSICAL finding. You may NOT move a
coordinate, propose a corrected polygon, or give any area, length or
quantity. If the boundary is wrong, say WHAT is wrong and WHY, and leave
the correction to CAD.
"""


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "STAGES": [V1, V2],
        "V1_OBSERVATIONS": list(V1_OBSERVATIONS),
        "EDGE_RELATIONS": list(edge.EDGE_RELATIONS),
        "V2_STATUSES": list(V2_STATUSES),
        "PHYSICAL_STATUSES": list(PHYSICAL_STATUSES),
        "FUNCTIONAL_STATUSES": list(FUNCTIONAL_STATUSES),
        "UNDECIDED_STATUSES": list(UNDECIDED_STATUSES),
        "V2_PERMITS_RELEASE": list(V2_PERMITS_RELEASE),
        "NOT_EXPOSED_BY_RUNTIME": NOT_EXPOSED_BY_RUNTIME,
        "V1_BRIEF": V1_BRIEF,
        "V2_BRIEF": V2_BRIEF,
        "why": {
            "over_capture_is_a_physical_claim":
                OVER_CAPTURE_IS_A_PHYSICAL_CLAIM,
            "a_naming_status_may_not_veto": A_NAMING_STATUS_MAY_NOT_VETO,
            "an_overlay_anchors_a_reader": AN_OVERLAY_ANCHORS_A_READER,
            "the_challenger_may_not_move_a_coordinate":
                THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
            "what_the_challenger_never_receives":
                WHAT_THE_CHALLENGER_NEVER_RECEIVES,
        },
    }
