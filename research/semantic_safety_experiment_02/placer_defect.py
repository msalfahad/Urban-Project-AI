"""The placer defect, measured before and after, and written down.

Two members of the regression feature - E1_2:CAD-1021#02 at a measured
coincident share of 0.00 and E1_2:CAD-361@1023#01 at 0.04 - were left
untagged by the v4 placer while being fully distinguishable in the
drawing. Under the owner's resolution of the tagging collision a member
may go untagged only because its source geometry is COINCIDENT with
another's; the renderer gate remains absolute for every member that is
geometrically distinguishable. So those two were the placer failing the
rule, not the drawing forcing an exception.

This module reproduces the failure on the shape that caused it, shows the
repaired placer on the same shape under the same tests, and verifies every
placement it claims. It changes nothing; it only measures. Run it with
    python3 -m research.semantic_safety_experiment_02.placer_defect
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P
from research.semantic_safety_experiment_02 import render as R

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")
W = H = 1400


def v4_anchors(pts, size):
    """v4: feet chosen by VERTEX INDEX among the returned points."""
    w, h = size
    inside = [p for p in pts if 0 <= p[0] <= w and 0 <= p[1] <= h]
    n = len(inside)
    if n < 2:
        return []
    picks, seen = [], set()
    for frac in (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9):
        k = min(n - 1, max(0, int(round(frac * (n - 1)))))
        if k not in seen:
            seen.add(k)
            picks.append(inside[k])
    return picks


def v4_place(anchor_candidates, size):
    """v4: one greedy pass in label order, no backtracking, then a
    re-check that could fail a tag the pass had already accepted."""
    w, h = size
    hw, hh = P.TAG_BOX_W_PX / 2.0, P.TAG_BOX_H_PX / 2.0
    m = P.TAG_MARGIN_PX
    best = {l: p[0] for l, p in anchor_candidates.items() if p}
    placed, failed = {}, {}
    for lab in sorted(anchor_candidates):
        cands = anchor_candidates[lab]
        if not cands:
            failed[lab] = "A_TAGGED_MEMBER_IS_NOT_INSIDE_THE_CROP"
            continue
        others = [v for k, v in best.items() if k != lab]
        got = None
        for ax, ay in cands:
            for r in P.TAG_RADII_PX:
                for deg in P.TAG_DIRECTIONS_DEG:
                    cx = ax + r * math.cos(math.radians(deg))
                    cy = ay + r * math.sin(math.radians(deg))
                    box = (cx - hw, cy - hh, cx + hw, cy + hh)
                    if box[0] < m or box[1] < m or box[2] > w - m \
                            or box[3] > h - m:
                        continue
                    if any(R._overlap(R._inflate(box, P.TAG_MIN_GAP_PX),
                                      o["box"]) for o in placed.values()):
                        continue
                    if any(R._seg_box((ax, ay), (cx, cy), o["box"])
                           for o in placed.values()):
                        continue
                    if any(R._point_seg_dist(o, (ax, ay), (cx, cy))
                           <= P.LEADER_CLEAR_PX for o in others):
                        continue
                    got = {"box": box, "centre": (cx, cy),
                           "anchor": (ax, ay)}
                    break
                if got:
                    break
            if got:
                break
        if got is None:
            failed[lab] = "NO_POSITION_PASSES_EVERY_TEST"
        else:
            placed[lab] = got
            best[lab] = got["anchor"]
    for lab, o in placed.items():
        rest = [v for k, v in placed.items() if k != lab]
        if any(R._overlap(R._inflate(o["box"], P.TAG_MIN_GAP_PX), q["box"])
               for q in rest):
            failed[lab] = "TWO_TAG_BOXES_OVERLAP"
        elif any(R._seg_box(o["anchor"], o["centre"], q["box"])
                 for q in rest):
            failed[lab] = "A_LEADER_CROSSES_ANOTHER_TAG_BOX"
        elif any(R._point_seg_dist(q["anchor"], o["anchor"], o["centre"])
                 <= P.LEADER_CLEAR_PX for q in rest):
            failed[lab] = "A_LEADER_PASSES_TOO_CLOSE_TO_ANOTHER_ANCHOR"
    return placed, failed


def verify(placed, size):
    """Independently: does every tag this placer CLAIMS is legible really
    pass every declared test? A claim that a reader can read a tag is the
    one claim this apparatus must not make wrongly."""
    w, h = size
    m = P.TAG_MARGIN_PX
    bad = []
    for lab, o in sorted(placed.items()):
        b = o["box"]
        if b[0] < m or b[1] < m or b[2] > w - m or b[3] > h - m:
            bad.append([lab, "A_TAG_BOX_FALLS_OUTSIDE_THE_CROP"])
        for other, q in sorted(placed.items()):
            if other == lab:
                continue
            why = R._incompatible(o, q)
            if why:
                bad.append([lab, why, other])
    return bad


def cases():
    """The shape that caused the failure: a run of parallel members a wall
    thickness apart, sharing their ends, which is what a wall run, a
    window layer and a poche block all look like in the source."""
    out = {}
    for n in (6, 10, 14):
        mem = {}
        for i in range(n):
            y = 500.0 + i * 9.0
            mem[f"M{i + 1:02d}"] = [(420.0, y), (980.0, y)]
        out[f"{n}_PARALLEL_MEMBERS_SHARING_THEIR_ENDS"] = mem
    return out


def measure():
    rows = []
    for name, mem in cases().items():
        a4 = {l: v4_anchors(p, (W, H)) for l, p in mem.items()}
        p4, f4 = v4_place(a4, (W, H))
        a5 = {l: R.anchor_candidates(p, (W, H)) for l, p in mem.items()}
        p5, f5 = R.place_tags(a5, (W, H))
        keep4 = {k: v for k, v in p4.items() if k not in f4}
        keep5 = {k: v for k, v in p5.items() if k not in f5}
        rows.append({
            "CASE": name,
            "members": len(mem),
            "V4_TAGGED": len(keep4),
            "V5_TAGGED": len(keep5),
            "V4_UNTAGGED": sorted(f4),
            "V5_UNTAGGED": sorted(f5),
            "V4_CLAIMS_THAT_DO_NOT_PASS_THE_TESTS": verify(keep4, (W, H)),
            "V5_CLAIMS_THAT_DO_NOT_PASS_THE_TESTS": verify(keep5, (W, H)),
            "anchor_feet_offered_per_straight_member": {
                "V4_by_vertex_index": len(v4_anchors(
                    [(420.0, 500.0), (980.0, 500.0)], (W, H))),
                "V5_by_arc_length": len(R.anchor_candidates(
                    [(420.0, 500.0), (980.0, 500.0)], (W, H))),
            },
        })
    return rows


def main():
    rows = measure()
    rec = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SUPERSEDED_PROTOCOL_V4_HASH": P.SUPERSEDED_PROTOCOL_V4_HASH,
        "WHAT_WAS_WRONG": P.WHY_V4_WAS_SUPERSEDED,
        "THE_RULE_THAT_WAS_BEING_BROKEN": (
            "a member may go untagged only because its source geometry is "
            "coincident with another member's. The renderer gate remains "
            "absolute for every member that is geometrically "
            "distinguishable"),
        "THE_TWO_MEMBERS_THAT_EXPOSED_IT": [
            {"SOURCE_INTERVAL_ID": "E1_2:CAD-1021#02",
             "largest_coincident_share": 0.0},
            {"SOURCE_INTERVAL_ID": "E1_2:CAD-361@1023#01",
             "largest_coincident_share": 0.04},
        ],
        "NO_TEST_WAS_RELAXED_AND_NO_TEST_WAS_ADDED": (
            "TAG_BOX_W_PX, TAG_BOX_H_PX, TAG_MARGIN_PX, TAG_MIN_GAP_PX, "
            "LEADER_CLEAR_PX, TAG_RADII_PX and TAG_DIRECTIONS_DEG are "
            "byte-identical to v4. Both repairs widen the search only, so "
            "wherever v4 succeeded v5 returns the same placement"),
        "MEASURED_BEFORE_AND_AFTER": rows,
        "TIMING_STATED_PLAINLY": (
            "measured and repaired BEFORE any reader saw the round-2 "
            "sample, and before the round-2 sample was rendered"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "08_PLACER_DEFECT_AND_REPAIR.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    for r in rows:
        print(f"{r['CASE']:42} v4 {r['V4_TAGGED']:>3}/{r['members']:<3} "
              f"v5 {r['V5_TAGGED']:>3}/{r['members']:<3} "
              f"v5 unsound claims: "
              f"{len(r['V5_CLAIMS_THAT_DO_NOT_PASS_THE_TESTS'])}")
    print("\nwritten:", path)


if __name__ == "__main__":
    main()
