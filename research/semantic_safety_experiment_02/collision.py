"""The protocol collision, the owner's resolution, and what it costs.

THE COLLISION

Two rules of the hashed protocol could not both hold for one feature:

    the render gate          no selected scored feature may contain an
                             unreadable entity tag
    the regression rule      the feature holding the prior critical error
                             is admitted whatever the quotas do

The feature holding that error is a doorway whose wall opening the drawing
overlays with a door block's linework. Several of its members are drawn on
top of each other, so no tag can point at one without pointing at another.
The placer - ten radii by eight directions by seven anchor feet per
member, at up to 3600 pixels - placed five of fourteen.

THE RESOLUTION, AS THE OWNER RULED IT

    admit it, tag what can be tagged, declare the rest
    feature grouping is not changed
    the regression case is not dropped
    the feature stays fully eligible for PRIMARY feature-level
    physical-relation scoring
    only the individually unresolvable coincident members are excluded
    from TERTIARY entity sub-role scoring
    each such member records MEMBER_TAG_STATUS and keeps its CAD identity
    no member role may be inferred because a coincident neighbour was
    tagged
    the gate stays absolute for every member that is geometrically
    distinguishable

WHAT THIS MODULE CHECKS RATHER THAN ASSUMES

The last of those is a claim about the drawing, and it is tested here: for
every untagged member, how much of its own length lies within
COINCIDENT_MM of another member of the same feature. A member that is NOT
coincident with anything and still failed placement would be the placer
failing, not the source, and it is reported as such rather than excused.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import cad_geometry as cg
from research.semantic_safety_experiment_02.build import Args
from research.semantic_safety_experiment_02 import protocol as P
from tools import run_e1_2 as r12
from tools import run_e1_4 as r14

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")

COINCIDENT_MM = 2.0
COINCIDENT_SHARE = 0.5

UNRESOLVABLE = "UNRESOLVABLE_DUE_TO_COINCIDENT_SOURCE_GEOMETRY"
DISTINGUISHABLE_BUT_UNPLACED = "GEOMETRICALLY_DISTINGUISHABLE_BUT_UNPLACED"
TAGGED = "TAGGED_AND_LEGIBLE"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    from shapely.geometry import LineString

    man = json.loads((OUT / "03_REFERENCE_INPUT_MANIFEST.json")
                     .read_text("utf-8"))
    feats = json.loads((OUT / "01_CANONICAL_FEATURE_REGISTER.json")
                       .read_text("utf-8"))
    qa = json.loads((OUT / "02_RENDER_QA_REGISTER.json").read_text("utf-8"))

    # the sandbox the readers are looking at must not have moved
    drift = []
    for t in man["TASKS"]:
        fid = t["CANONICAL_FEATURE_ID"]
        d = OUT / "blind_sandbox" / fid
        for name, want in (("TASK.json", t["TASK_SHA256"]),
                           ("FLOOR_CONTEXT.txt", t["FLOOR_CONTEXT_SHA256"])):
            if not (d / name).exists() or _sha(d / name) != want:
                drift.append(f"{fid}/{name}")
        for name, want in t["CROP_SHA256"].items():
            if not (d / name).exists() or _sha(d / name) != want:
                drift.append(f"{fid}/{name}")

    reg = next(f for f in feats["SELECTED"] if f["IS_THE_REGRESSION_FEATURE"])
    fid = reg["CANONICAL_FEATURE_ID"]
    row = next(r for r in qa["ROWS"]
               if r["CANONICAL_FEATURE_ID"] == fid)
    untagged = set(row["MEMBERS_SHOWN_WITHOUT_AN_INDIVIDUAL_TAG"])
    labels = {f"M{n:02d}": iv for n, iv in
              enumerate(reg["SOURCE_INTERVAL_IDS"], start=1)}

    st = r14._core(Args())
    by_id = {p.object_id: p for p in st["gf"]["primitives"]}
    iv_by_id = {iv.interval_id: iv
                for rows in st["interp"]["roles"]["intervals"].values()
                for iv in rows}

    geom = {}
    for lab, ivid in labels.items():
        iv = iv_by_id.get(ivid)
        parent = by_id.get(iv.parent_object_id) if iv else None
        if iv is None or parent is None:
            continue
        try:
            pts = cg._as_segment(r12.IntervalPrim(parent, iv)).points(
                tol_mm=2.0)
        except Exception:
            continue
        if len(pts) >= 2:
            geom[lab] = (iv, LineString([tuple(p) for p in pts]))

    rows = []
    for lab in sorted(labels):
        ivid = labels[lab]
        iv, g = geom.get(lab, (iv_by_id.get(ivid), None))
        partners = []
        if g is not None:
            for other, (oiv, og) in geom.items():
                if other == lab:
                    continue
                share = (g.intersection(og.buffer(COINCIDENT_MM)).length
                         / g.length) if g.length else 0.0
                if share >= 0.01:
                    partners.append({"MEMBER_LABEL": other,
                                     "SOURCE_INTERVAL_ID": labels[other],
                                     "share_of_this_member_within_"
                                     "the_coincidence_tolerance":
                                         round(share, 4)})
        partners.sort(key=lambda x: -x["share_of_this_member_within_"
                                       "the_coincidence_tolerance"])
        worst = (partners[0]["share_of_this_member_within_"
                             "the_coincidence_tolerance"]
                 if partners else 0.0)
        if lab not in untagged:
            status = TAGGED
        elif worst >= COINCIDENT_SHARE:
            status = UNRESOLVABLE
        else:
            status = DISTINGUISHABLE_BUT_UNPLACED
        rows.append({
            "MEMBER_LABEL": lab,
            "MEMBER_TAG_STATUS": status,
            "SOURCE_INTERVAL_ID": ivid,
            "SOURCE_ENTITY_ID": getattr(iv, "parent_object_id", None),
            "LAYER": str(getattr(iv, "layer", "")),
            "ENTITY_TYPE": str(getattr(iv, "entity_type", "")),
            "GEOMETRY_KIND": str(getattr(iv, "kind", "")),
            "DWG_HANDLE": (getattr(iv, "provenance", None) or {}).get(
                "dwg_handle"),
            "BLOCK": (getattr(iv, "provenance", None) or {}).get(
                "instance_path") or (getattr(iv, "provenance", None)
                                     or {}).get("block_path"),
            "length_mm": round(getattr(iv, "length_mm", 0.0), 3),
            "COINCIDENT_WITH": partners[:4],
            "largest_coincident_share": round(worst, 4),
            "EXCLUDED_FROM_TERTIARY_SCORING": status != TAGGED,
            "ELIGIBLE_FOR_PRIMARY_SCORING": True,
        })

    bad = [r for r in rows
           if r["MEMBER_TAG_STATUS"] == DISTINGUISHABLE_BUT_UNPLACED]

    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_PROTOCOL_HASH_IS_UNCHANGED_BY_THIS_RECORD": (
            "the owner's clarification adds RECORDING obligations. It "
            "changes no admission rule, no grouping rule and no scoring "
            "rule, so the frozen protocol stands and its hash is not "
            "bumped"),

        "THE_COLLISION": {
            "RULE_A": "the render gate: no selected scored feature may "
                      "contain an unreadable entity tag",
            "RULE_B": P.REGRESSION_RULE,
            "WHERE_THEY_MET": fid,
            "WHY": ("the drawing overlays a door block's linework on the "
                    "wall opening, so several members are drawn on top of "
                    "one another and no tag can point at one without "
                    "pointing at another"),
            "TAGS_PLACED": row["FEATURE_LEVEL_QA"]["tags_placed"],
            "TAGS_REQUIRED": row["FEATURE_LEVEL_QA"]["tags_required"],
            "PIXELS_TRIED_UP_TO": row["FEATURE_LEVEL_QA"]["pixels_used"],
        },

        "THE_RESOLUTION": {
            "DECIDED_BY": "the owner",
            "ADMIT_IT_TAG_WHAT_CAN_BE_TAGGED": True,
            "FEATURE_GROUPING_IS_NOT_CHANGED": True,
            "THE_REGRESSION_CASE_IS_NOT_DROPPED": True,
            "FULLY_ELIGIBLE_FOR_PRIMARY_RELATION_SCORING": True,
            "ONLY_UNRESOLVABLE_MEMBERS_LEAVE_TERTIARY_SCORING": True,
            "NO_ROLE_IS_INFERRED_FROM_A_COINCIDENT_NEIGHBOUR": (
                "scoring joins a reader's answer to a member by that "
                "member's own label. An untagged member has no label in "
                "any answer, so no role can reach it from a neighbour, "
                "and none is copied to it anywhere"),
            "THE_GATE_REMAINS_ABSOLUTE_FOR_DISTINGUISHABLE_MEMBERS": True,
            "AVAILABLE_ONLY_TO_A_REGRESSION_FEATURE": True,
        },

        "HOW_COINCIDENCE_IS_MEASURED": (
            "the share of a member's own length lying within "
            f"{COINCIDENT_MM} mm of another member of the same feature. A "
            f"member with at least {COINCIDENT_SHARE} of its length so "
            "covered is unresolvable in the source; one with less that "
            "still failed placement would be the placer failing, not the "
            "drawing, and is reported as that"),
        "COINCIDENT_MM": COINCIDENT_MM,
        "COINCIDENT_SHARE": COINCIDENT_SHARE,

        "CANONICAL_FEATURE_ID": fid,
        "members": len(rows),
        "tagged_and_legible": sum(1 for r in rows
                                  if r["MEMBER_TAG_STATUS"] == TAGGED),
        "unresolvable_due_to_coincident_source_geometry": sum(
            1 for r in rows if r["MEMBER_TAG_STATUS"] == UNRESOLVABLE),
        "geometrically_distinguishable_but_unplaced": len(bad),
        "EVERY_UNTAGGED_MEMBER_IS_COINCIDENT_IN_THE_SOURCE": not bad,
        "MEMBERS": rows,

        "TIMING_STATED_PLAINLY": {
            "PROTOCOL_V3_WITH_PARTIAL_TAGGING_WAS_HASHED_AND_COMMITTED_"
            "BEFORE_ANY_READER_LAUNCHED": True,
            "THE_PER_MEMBER_RECORD_IN_THIS_FILE_WAS_WRITTEN_AFTER_THE_"
            "REFERENCE_READERS_HAD_STARTED": True,
            "WHY_THAT_IS_SAFE": (
                "this file is a register. No reader reads it. The blind "
                "sandbox the readers are looking at was not touched, and "
                "every one of its files was re-hashed against the input "
                "manifest to prove it"),
            "BLIND_SANDBOX_FILES_THAT_DRIFTED": drift,
            "THE_SANDBOX_IS_BYTE_IDENTICAL_TO_THE_MANIFEST": not drift,
        },
    }
    p = OUT / "04_PROTOCOL_COLLISION_AND_RESOLUTION.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({k: v for k, v in body.items()
                      if k not in ("MEMBERS", "THE_RESOLUTION",
                                   "THE_COLLISION")}, indent=2)[:1800])
    print("\nMEMBER STATUS")
    for r in rows:
        print(" ", r["MEMBER_LABEL"], r["MEMBER_TAG_STATUS"],
              r["SOURCE_INTERVAL_ID"], "coincident_share",
              r["largest_coincident_share"])
    print("SHA256", _sha(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
