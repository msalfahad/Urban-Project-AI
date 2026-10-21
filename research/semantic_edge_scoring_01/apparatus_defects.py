"""Measure the apparatus's own defects, so the scores can be read honestly.

A reference reader reported that index labels overprint one another in
several clusters, so member-level identification - not the drawing's
clarity - is what forces UNRESOLVED at the entity level. That is a defect
of the crop renderer written for the frozen experiment, and it bounds what
any entity-role accuracy figure can mean.

Rather than take it anecdotally, this measures it: each labelled member's
label is drawn at the middle of its own drawn line, so two members whose
middles fall within a few pixels of each other in a crop have labels
printed on top of each other. The same measurement is run at every crop
level, because a label buried at feature scale may be legible at detail
scale.

Nothing here alters the frozen experiment or the frozen scoring inputs.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from research.semantic_edge_experiment_01.build import Args
from research.semantic_edge_scoring_01 import protocol as P
from tools import run_e1_4 as r14

EXP = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")

# Two labels whose anchors fall within this many pixels of each other in a
# crop are printed on top of one another. A label glyph is about this tall.
LABEL_COLLISION_PX = 12.0


def main() -> int:
    st = r14._core(Args())
    mid = {}
    for rows in st["interp"]["roles"]["intervals"].values():
        for iv in rows:
            mid[iv.interval_id] = ((iv.start_mm[0] + iv.end_mm[0]) / 2.0,
                                   (iv.start_mm[1] + iv.end_mm[1]) / 2.0)

    crops = {r["FEATURE_GROUP_ID"]: r["CROPS"] for r in json.loads(
        (EXP / "03_CROP_REGISTER.json").read_text("utf-8"))["BY_GROUP"]}
    groups = json.loads((EXP / "02_FEATURE_GROUP_REGISTER.json")
                        .read_text("utf-8"))["GROUPS"]

    rows, worst = [], {}
    for g in groups:
        gid = g["FEATURE_GROUP_ID"]
        task = json.loads((EXP / "a19" / "pass_a_sandbox" / gid
                           / "TASK.json").read_text("utf-8"))
        order = g["PRIMARY_ENTITY_IDS"] + g["CONTEXT_ENTITY_IDS"]
        labels = {m["MEMBER_LABEL"]: iv for m, iv in
                  zip(task["MARKED_MEMBERS"], order)}
        per_level = {}
        for c in crops[gid]:
            if not c["MARKED"]:
                continue
            x0, y0, x1, y1 = c["box_mm"]
            w = max(x1 - x0, 1e-9)
            px = c["pixels"][0] / w
            pts = {}
            for lab, iv in labels.items():
                m = mid.get(iv)
                if m is None:
                    continue
                pts[lab] = ((m[0] - x0) * px, (m[1] - y0) * px)
            buried = set()
            for a in pts:
                for b in pts:
                    if a >= b:
                        continue
                    if math.dist(pts[a], pts[b]) <= LABEL_COLLISION_PX:
                        buried.add(a)
                        buried.add(b)
            per_level[c["LEVEL"]] = {
                "labels_drawn": len(pts),
                "labels_printed_on_top_of_another": len(buried),
                "BURIED": sorted(buried),
            }
        # a label is recoverable if ANY marked level shows it clear
        clear = set(labels)
        for lv in per_level.values():
            pass
        for lab in list(labels):
            if all(lab in lv["BURIED"] for lv in per_level.values()) \
                    and per_level:
                clear.discard(lab)
        rows.append({
            "FEATURE_GROUP_ID": gid,
            "labelled_members": len(labels),
            "BY_CROP_LEVEL": per_level,
            "labels_buried_at_every_marked_level": sorted(
                set(labels) - clear),
        })
        worst[gid] = len(set(labels) - clear)

    total_labels = sum(r["labelled_members"] for r in rows)
    total_buried = sum(len(r["labels_buried_at_every_marked_level"])
                       for r in rows)
    body = {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "WHAT_THIS_IS": (
            "a measurement of the crop renderer's own limits, made because "
            "a reference reader reported them before this code existed"),
        "THE_DEFECT": (
            "every labelled member's index label is drawn at the middle of "
            "its own drawn line. Collinear or closely stacked members - the "
            "long parallel lines of a window run, the sides of a poche "
            "block - have middles within a few pixels of each other, so "
            "their labels print on top of one another and a reader cannot "
            "tie a label to a particular line"),
        "WHY_IT_MATTERS_FOR_SCORING": (
            "it bounds entity-role accuracy from below for reasons that "
            "have nothing to do with either reader. Where a label is buried "
            "at every marked crop level, an UNRESOLVED member role is the "
            "apparatus failing, not the drawing being ambiguous and not the "
            "reader being cautious. These counts belong beside the "
            "entity-role figures and not inside them"),
        "IT_IS_NOT_FIXED_HERE": (
            "the frozen experiment stands as it was produced and its crops "
            "are not re-rendered. A later round that wants member-level "
            "scoring needs a renderer that places labels with leader lines "
            "and a collision test"),
        "LABEL_COLLISION_PX": LABEL_COLLISION_PX,
        "feature_groups": len(rows),
        "labelled_members": total_labels,
        "labels_buried_at_every_marked_crop_level": total_buried,
        "groups_with_at_least_one_buried_label": sum(
            1 for v in worst.values() if v),
        "ROWS": rows,
    }
    p = OUT / "06_APPARATUS_DEFECT_REGISTER.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({k: v for k, v in body.items() if k != "ROWS"},
                     indent=2)[:1200])
    print("SHA256", hashlib.sha256(p.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
