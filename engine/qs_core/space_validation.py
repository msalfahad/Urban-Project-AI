"""Did the room-assembly algorithm actually get tested by this drawing, or did it merely run?

Synthetic fixtures prove that the code can merge two fragments of one room.  They cannot prove that it did so
here, and a real source in which every space happens to arrive as a single component exercises none of it.
Reporting "50 spaces assembled" from 50 single-component spaces is reporting that a loop executed.

So the real run is graded on what it encountered.  Three outcomes are distinguished and the difference between
them is the whole point: the algorithm ran; the algorithm met a multi-component case and its merge is supported
seam by seam; or this source never presented one, in which case the capability remains unvalidated HERE and the
report says so instead of implying otherwise.
"""

from __future__ import annotations

from engine.qs_core import spaces as SP

ALGORITHM_RAN = "ALGORITHM_RAN"
VALIDATED = "MULTI_COMPONENT_CASE_ENCOUNTERED_AND_VALIDATED"
NO_CASE = "THIS_DRAWING_SUPPLIED_NO_PROVEN_MULTI_COMPONENT_CASE"
CONTRADICTION = "CONTINUOUS_SEAMS_EXIST_BUT_NOTHING_MERGED"


def validate(spaces, membership, seams, floor=None):
    """Grade the assembly on this source's own evidence, and show the seam behind every decision."""
    room_of = {m["COMPONENT_REF"]: m["ROOM_ID"] for m in membership}
    kind_of = {m["COMPONENT_REF"]: m["KIND"] for m in membership}

    single = [s for s in spaces if len(s.component_refs) == 1]
    multi = [s for s in spaces if len(s.component_refs) > 1]

    seams_by_pair = {}
    for s in seams:
        seams_by_pair.setdefault((s["A"], s["B"]), []).append(s)

    detail = []
    for s in sorted(multi, key=lambda x: -x.area):
        refs = sorted(s.component_refs)
        joins = []
        for i, a in enumerate(refs):
            for b in refs[i + 1:]:
                for rec in seams_by_pair.get((a, b), []) + seams_by_pair.get((b, a), []):
                    joins.append({"A": a, "B": b, "RELATION": rec["RELATION"], "LENGTH_M": rec["LENGTH_M"],
                                  "SHARES": rec.get("SHARES"), "AXIS": rec["AXIS"],
                                  "POSITION": rec["POSITION"]})
        continuous = [j for j in joins if j["RELATION"] == SP.SEAM_CONTINUOUS]
        detail.append({
            "ROOM_ID": s.room_id, "FLOOR": s.floor, "LABEL": s.label, "LABEL_STATUS": s.label_status,
            "COMPONENTS": refs, "COMPONENT_COUNT": len(refs), "AREA_M2": round(s.area, 6),
            "STATUS": s.status,
            "SEAMS_BETWEEN_MEMBERS": sorted(joins, key=lambda j: (j["A"], j["B"], j["POSITION"])),
            "CONTINUOUS_SEAM_COUNT": len(continuous),
            "SUPPORTED": bool(continuous),
            "WHY": ("these components meet along floor with nothing physical between them, which is what one "
                    "room is" if continuous else
                    "these components are in one space and no seam between them reads as continuous; that is "
                    "a defect in the assembly, not a room")})

    kept_apart = []
    for rec in seams:
        a, b = rec["A"], rec["B"]
        if kind_of.get(a) != "FLOOR_REGION" or kind_of.get(b) != "FLOOR_REGION":
            continue
        ra, rb = room_of.get(a), room_of.get(b)
        if ra is not None and ra == rb:
            continue
        kept_apart.append({"A": a, "B": b, "ROOM_A": ra, "ROOM_B": rb, "RELATION": rec["RELATION"],
                           "LENGTH_M": rec["LENGTH_M"], "SHARES": rec.get("SHARES"),
                           "REFS": rec.get("REFS"),
                           "WHY": {SP.SEAM_WALL: "wall material stands along this seam, so these are two rooms",
                                   SP.SEAM_OPENING: "an opening connects them, which is a door between two "
                                                    "rooms and not one room",
                                   SP.SEAM_CANDIDATE_OPENING: "the wall stops here and the source does not say "
                                                              "what fills the gap; merging would be a guess",
                                   SP.SEAM_MIXED: "the seam is part material and part open; the engine does "
                                                  "not decide"}.get(rec["RELATION"], rec["RELATION"])})

    unresolved_continuations = [k for k in kept_apart
                                if k["RELATION"] in (SP.SEAM_CANDIDATE_OPENING, SP.SEAM_MIXED)]

    continuous_seams = [s for s in seams if s["RELATION"] == SP.SEAM_CONTINUOUS]
    if multi and all(d["SUPPORTED"] for d in detail):
        outcome = VALIDATED
    elif multi:
        outcome = CONTRADICTION
    elif continuous_seams:
        outcome = CONTRADICTION
    else:
        outcome = NO_CASE

    return {
        "FLOOR": floor,
        "OUTCOME": outcome,
        "OUTCOMES": [ALGORITHM_RAN, VALIDATED, NO_CASE, CONTRADICTION],
        "SPACES": len(spaces),
        "SINGLE_COMPONENT_SPACES": len(single),
        "MULTI_COMPONENT_SPACES": len(multi),
        "LARGEST_COMPONENT_COUNT": max([len(s.component_refs) for s in spaces], default=0),
        "CONTINUOUS_SEAMS_IN_THE_SOURCE": len(continuous_seams),
        "MULTI_COMPONENT_DETAIL": detail,
        "COMPONENT_TO_ROOM_LINEAGE": sorted(
            ({"COMPONENT_REF": m["COMPONENT_REF"], "ROOM_ID": m["ROOM_ID"], "KIND": m["KIND"],
              "STATUS": m["STATUS"], "AREA_M2": m["AREA_M2"], "LABEL": m.get("LABEL")}
             for m in membership), key=lambda m: m["COMPONENT_REF"]),
        "ADJACENT_FRAGMENTS_KEPT_SEPARATE": sorted(kept_apart, key=lambda k: (k["A"], k["B"])),
        "UNRESOLVED_CANDIDATE_CONTINUATIONS": sorted(unresolved_continuations,
                                                     key=lambda k: (k["A"], k["B"])),
        "WHAT_THIS_MEANS": {
            ALGORITHM_RAN: "the assembly stage executed over this drawing",
            VALIDATED: "at least one room in this drawing arrived as several components and was assembled, "
                       "with a continuous seam supporting every join",
            NO_CASE: "no two floor components in this drawing meet with nothing between them, so this source "
                     "does not exercise multi-component assembly; the capability is proved by the synthetic "
                     "fixtures and remains unproved ON THIS SOURCE",
            CONTRADICTION: "the seam evidence and the assembled spaces disagree; this is a defect to fix, not "
                           "a result to report"},
    }
