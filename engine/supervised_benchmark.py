"""P7757 as a development set, kept strictly apart from the frozen scores.

Rounds 1 to 5 were blind. Their predictions are frozen, their artefacts are
immutable, and nothing here may touch them. From round 6 P7757 is a
SUPERVISED development project: the owner has disclosed what four of the
round-5 releases should have been, and those disclosures are training
examples.

    THREE SCOREBOARDS, NEVER MIXED

    historical   docs/PROJECT_2_CAD_ROUND[1-5]*.md   blind, read-only
    supervised   this module                          P7757 with answers
    synthetic    round[2-6]_selftest                  generalisation

    A SYNTHETIC TEST IS NEVER WEAKENED TO MAKE A SUPERVISED EXAMPLE PASS.

HOW AN EXAMPLE IS SCORED, AND WHAT IS DELIBERATELY NOT SCORED

Each example carries a STRUCTURAL assertion and, separately, whatever
NUMBERS the owner disclosed. The assertion is what passes or fails. The
numbers are reported beside the engine's own, with their difference, and
they are **not** a target: §13 says the goal is not to get closer to 9.675,
and a harness that scored the distance would make it one.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import wall_face_ownership as wface

HARNESS = "P7757_SUPERVISED_DEVELOPMENT_BENCHMARK_V1"

GEOMETRY = "GEOMETRY"
SPACE_ROLE = "SPACE_ROLE"
TRADE_ZONE = "TRADE_ZONE"
QUANTITY = "QUANTITY"

SCOREBOARDS = (GEOMETRY, SPACE_ROLE, TRADE_ZONE, QUANTITY)

HELD = "HELD"
NOT_HELD = "NOT_HELD"
AWAITING = "AWAITING_A_LATER_STEP"


@dataclass(frozen=True)
class Example:
    """One disclosed truth, and the structural claim it lets us test."""

    example_id: str
    scoreboard: str
    disclosed: str
    assertion: str
    figures: dict = field(default_factory=dict)
    motivated: tuple = ()          # which rules this example changed
    protected_by: tuple = ()       # which synthetic tests guard the change

    def record(self) -> dict:
        return {"example_id": self.example_id,
                "scoreboard": self.scoreboard,
                "disclosed_by_the_owner": self.disclosed,
                "structural_assertion": self.assertion,
                "figures_disclosed": dict(self.figures),
                "rules_this_example_motivated": list(self.motivated),
                "synthetic_tests_protecting_the_change":
                    list(self.protected_by),
                "note": ("the assertion is scored. The figures are reported "
                         "beside the engine's own and are NOT a target")}


EXAMPLES = (
    Example(
        example_id="P7757-MAIN-KITCHEN-GEOMETRY",
        scoreboard=GEOMETRY,
        disclosed="round 6 measured the kitchen at 2.20 x 2.55 m. The main "
                  "kitchen is 3.00 x 2.70 m; the 1.05 x 1.50 entrance "
                  "recess is a LATER trade-zone question and is not part "
                  "of this one",
        assertion="the space carrying the KITCHEN concept is released on "
                  "the CLEAR_INTERNAL_FINISH_FACE basis, with every side "
                  "of its polygon attributed to a wall face, a portal or a "
                  "recovered span",
        figures={"main_kitchen_m2": 8.10, "main_kitchen_x_m": 3.00,
                 "main_kitchen_y_m": 2.70, "round_6_steps_1_5_m2": 5.553},
        motivated=("wall_face_ownership: a wall is where the spaces stop",
                   "wall_face_ownership: a line with floor on both sides "
                   "of it bounds nothing",
                   "room_partition_graph: the flood is run again on the "
                   "lines a room may stop at"),
        protected_by=("A_TWO_ROOMS_SHARE_ONE_WALL",
                      "C_FINISH_AND_DETAIL_LINES_BESIDE_A_WALL",
                      "G_A_FINISH_LINE_INSIDE_THE_STRUCTURAL_FACE")),
    Example(
        example_id="P7757-WC-WASH-GEOMETRY",
        scoreboard=GEOMETRY,
        disclosed="the W.C is about 1.50 x 2.25 and the WASH about "
                  "1.50 x 2.10. Round 5's 1.00 x 3.50 polygon was one slot "
                  "across both of them",
        assertion="the W.C and the WASH are two separately released "
                  "spaces, each on the clear-internal basis, and neither "
                  "carries the other's identity",
        figures={"wc_m2": 3.375, "wash_m2": 3.15,
                 "frozen_round5_m2": 3.50},
        motivated=("portal_match: a claim on a door stands down when its "
                   "faces are not the two faces of any wall",),
        protected_by=("D_A_DOORWAY_DOES_NOT_SHORTEN_THE_ROOM",
                      "H_ONE_WALL_TWO_DIFFERENT_CLEAR_WIDTHS")),
    Example(
        example_id="P7757-KITCHEN",
        scoreboard=GEOMETRY,
        disclosed="the frozen 3.85 m2 polygon selected only part of the "
                  "kitchen. Manual construction measurement is 3.00 x 2.70 "
                  "plus a 1.05 x 1.50 entrance recess",
        assertion="no space carrying the KITCHEN concept is bounded by a "
                  "recovered span whose wall band was paired on nothing",
        figures={"manual_m2": 9.675, "human_workbook_m2": 9.55,
                 "frozen_round5_m2": 3.85},
        motivated=("physical_wall: one line one wall, over disjoint "
                   "stretches only",),
        protected_by=("N_A_DETAIL_LINE_BESIDE_A_WALL_FACE",
                      "O_ONE_LINE_OFFERED_THREE_PARTNERS",
                      "A_KITCHEN_WITH_AN_ENTRANCE_RECESS")),
    Example(
        example_id="P7757-WC-WASH",
        scoreboard=GEOMETRY,
        disclosed="the frozen 1.00 x 3.50 polygon is geometrically wrong "
                  "even though its area looked close. Independent review "
                  "finds two distinct spaces, about 1.50 x 2.10 and "
                  "1.50 x 2.25",
        assertion="no released space is a narrow slot cutting across two "
                  "separately labelled spaces",
        figures={"wash_m2": 3.15, "wc_m2": 3.375,
                 "frozen_round5_m2": 3.50},
        motivated=("physical_wall: a phantom face may not slice a room",),
        protected_by=("O_ONE_LINE_OFFERED_THREE_PARTNERS",
                      "B_L_SHAPED_ROOM")),
    Example(
        example_id="P7757-GARDEN-STRIP",
        scoreboard=SPACE_ROLE,
        disclosed="the frozen 5.616 m2 unknown polygon is an external or "
                  "garden strip, not an interior ceramic room",
        assertion="no space this engine calls exterior is released as an "
                  "interior room, and where a site boundary exists the "
                  "ground between it and the fabric is enumerated",
        figures={"frozen_round5_m2": 5.616},
        motivated=("interior_exterior: the fabric is what is left when the "
                   "ground is taken away",
                   "cad_space_role: EXTERIOR_SPACE_UNCLASSIFIED exists"),
        protected_by=("F_AN_EXTERIOR_STRIP_INSIDE_THE_SITE",)),
    Example(
        example_id="P7757-VOID-OVERUSE",
        scoreboard=SPACE_ROLE,
        disclosed="43 of 57 polygons were classified VOID_OR_SHAFT, which "
                  "is far too aggressive. UNKNOWN identity must not default "
                  "to VOID",
        assertion="no space is called a void or a shaft without positive "
                  "evidence, and an unnamed bounded space is unclassified "
                  "rather than void",
        figures={"frozen_round5_void_or_shaft": 43,
                 "frozen_round5_polygons": 57},
        motivated=("cad_space_role: VOID and SHAFT require positive "
                   "evidence",),
        protected_by=("G_AN_INTERIOR_ROOM_NOBODY_NAMED",
                      "H_A_SHAFT_WITH_EVIDENCE",
                      "I_AN_UNLABELLED_VERTICAL_PENETRATION",
                      "M_VALID_GEOMETRY_UNREADABLE_IDENTITY")),
    Example(
        example_id="P7757-OPEN-RECEPTION",
        scoreboard=TRADE_ZONE,
        disclosed="RECEPTION, SALOON and DINING label a large open "
                  "connected floor. They do not necessarily represent "
                  "separate physical rooms and must not automatically "
                  "become separate ceramic quantities",
        assertion="the floor trade zone is decided by floor topology and "
                  "trade rules, not by the number of labels",
        figures={},
        motivated=("trade_zone: a zone may contain several physical "
                   "spaces",),
        protected_by=("C_OPEN_SALON_DINING_RECEPTION",
                      "D_THE_SAME_LABELS_WITH_REAL_WALLS",
                      "K_TWO_ZONES_ONE_FINISH")),
)


@dataclass
class Score:
    example_id: str
    scoreboard: str
    status: str
    observed: dict = field(default_factory=dict)
    why: str = ""

    def record(self) -> dict:
        return {"example_id": self.example_id,
                "scoreboard": self.scoreboard,
                "status": self.status,
                "observed": dict(self.observed),
                "why": self.why}


def _concept_spaces(rep, concept: str) -> list:
    out = []
    for r in rep.rows:
        for z in r.zones:
            for o in (z.identity.observations if z.identity else ()):
                look = getattr(o, "lookup", None)
                if look is not None and look.is_known and \
                        look.concept == concept:
                    out.append(r)
                    break
    return out


def _paired_on_nothing(rep) -> set:
    """Wall bands that carry no pairing evidence beyond running alongside."""
    from engine import physical_wall as pw

    out = set()
    for wr in rep.walls:
        for w in wr.walls:
            tokens = [t for t in w.evidence if t != pw.EV_OVERLAP]
            if not tokens:
                out.add(w.wall_id)
    return out


def evaluate(rep) -> dict:
    """Score every example this step can reach, and say so where it cannot."""
    scores = []
    weak = _paired_on_nothing(rep)
    roles = getattr(rep, "space_roles", None)
    released = [r for r in rep.rows
                if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]

    for ex in EXAMPLES:
        if ex.scoreboard in (TRADE_ZONE, QUANTITY):
            scores.append(Score(ex.example_id, ex.scoreboard, AWAITING,
                                {}, "the trade layer is step 7 onward"))
            continue

        if ex.example_id == "P7757-MAIN-KITCHEN-GEOMETRY":
            spaces = _concept_spaces(rep, "KITCHEN")
            good = [r for r in spaces
                    if r.clear is not None and r.clear.basis_established]
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if good else NOT_HELD,
                {"kitchen_spaces": len(spaces),
                 "released_on_the_clear_internal_basis": len(good),
                 "clear_area_m2": [round(r.clear.area_m2, 3) for r in good],
                 "principal_dims_mm": [list(r.clear.principal_dims_mm)
                                       for r in good],
                 "sides_with_no_established_face": [
                     sum(1 for f in r.clear.boundary_faces
                         if f.basis == wface.BASIS_NOT_ESTABLISHED)
                     for r in good]},
                "the basis is what is scored. The measured figure is "
                "reported beside the disclosed one and was not optimised "
                "towards it"))

        elif ex.example_id == "P7757-WC-WASH-GEOMETRY":
            wc = _concept_spaces(rep, "WC") + _concept_spaces(rep, "W.C")
            seen, spaces = set(), []
            for r in wc:
                if r.space_id not in seen:
                    seen.add(r.space_id)
                    spaces.append(r)
            good = [r for r in spaces
                    if r.clear is not None and r.clear.basis_established]
            shared = [r.space_id for r in good if len(r.zones) > 1]
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if len(good) >= 2 and not shared else NOT_HELD,
                {"spaces_carrying_a_wc_concept": len(spaces),
                 "released_on_the_clear_internal_basis": len(good),
                 "clear_area_m2": sorted(round(r.clear.area_m2, 3)
                                         for r in good),
                 "principal_dims_mm": [list(r.clear.principal_dims_mm)
                                       for r in good],
                 "released_carrying_more_than_one_identity": shared},
                "two rooms, two polygons, two bases. One polygon carrying "
                "both identities is the round-5 slot"))

        elif ex.example_id == "P7757-KITCHEN":
            spaces = _concept_spaces(rep, "KITCHEN")
            bad = [r.space_id for r in spaces
                   for rec in r.recovered_boundary
                   if rec.get("wall_id") in weak]
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if not bad else NOT_HELD,
                {"kitchen_spaces": len(spaces),
                 "areas_m2": sorted(round(r.enclosure.area_m2, 3)
                                    for r in spaces
                                    if r.enclosure and r.enclosure.area_m2),
                 "bounded_by_a_band_paired_on_nothing": bad},
                "a kitchen bounded by a band paired on nothing is the "
                "round-5 failure exactly"))

        elif ex.example_id == "P7757-WC-WASH":
            bad = []
            for r in released:
                groups = len(r.zones)
                if groups > 1 and r.enclosure and r.enclosure.area_m2:
                    bad.append(r.space_id)
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if not bad else NOT_HELD,
                {"released_spaces": len(released),
                 "released_carrying_more_than_one_identity": bad},
                "a slot cutting across two labelled spaces shows up as one "
                "released polygon carrying both identities"))

        elif ex.example_id == "P7757-GARDEN-STRIP":
            exterior = ([v for v in roles.verdicts if v.is_exterior]
                        if roles else [])
            leaked = []
            if roles is not None:
                ext_ids = {v.space_id for v in exterior}
                leaked = [r.space_id for r in released
                          if r.space_id in ext_ids]
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if roles is not None and not leaked else NOT_HELD,
                {"exterior_spaces_identified": len(exterior),
                 "exterior_spaces_released_as_rooms": leaked,
                 "regions_with_an_envelope": (
                     roles.counts()["regions_with_an_envelope"]
                     if roles else 0)},
                "where no site boundary exists the ground cannot be "
                "separated from the fabric, and this reports zero rather "
                "than guessing"))

        elif ex.example_id == "P7757-VOID-OVERUSE":
            if roles is None:
                scores.append(Score(ex.example_id, ex.scoreboard, NOT_HELD,
                                    {}, "no space-role classifier"))
                continue
            unevidenced = [v.space_id for v in roles.verdicts
                           if v.is_vertical_penetration and not v.evidence]
            counts = roles.counts()["by_role"]
            scores.append(Score(
                ex.example_id, ex.scoreboard,
                HELD if not unevidenced else NOT_HELD,
                {"by_role": counts,
                 "called_a_penetration_without_evidence": unevidenced},
                "VOID and SHAFT are claims. Nobody naming a space is not "
                "one"))

    return {
        "harness": HARNESS,
        "SUPERVISED_BENCHMARK_HASH": harness_hash(),
        "scoreboards": list(SCOREBOARDS),
        "examples": [ex.record() for ex in EXAMPLES],
        "scores": [s.record() for s in scores],
        "by_scoreboard": {
            board: {
                "examples": sum(1 for s in scores if s.scoreboard == board),
                "held": sum(1 for s in scores
                            if s.scoreboard == board and s.status == HELD),
                "not_held": sum(1 for s in scores if s.scoreboard == board
                                and s.status == NOT_HELD),
                "awaiting": sum(1 for s in scores if s.scoreboard == board
                                and s.status == AWAITING),
            } for board in SCOREBOARDS},
        "kept_apart_from": (
            "the frozen round-1 to round-5 predictions, which this harness "
            "may not touch, and the synthetic suites, which may never be "
            "weakened to make an example here pass"),
        "not_a_target": (
            "the disclosed figures are reported beside the engine's own "
            "and are not optimised against. The goal is a measurement "
            "basis, not a closer number"),
    }


def harness_hash() -> str:
    parts = [HARNESS, "|".join(SCOREBOARDS)]
    for ex in EXAMPLES:
        parts.append(f"{ex.example_id}|{ex.scoreboard}|{ex.assertion}|"
                     + ",".join(f"{k}={v}"
                                for k, v in sorted(ex.figures.items())))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
