"""PA08-QORTUBA-R1 §8: reconcile the independent semantic reading of the ORIGINAL SHEET with the engine's spaces.

The reader saw the PDF render only: no engine space, no band, no site, no expected number.  Its output is a model observation,
not truth.  The reconciliation is QA: it may not change geometry, and no quantity is taken from it.  Where the two disagree the
engine's state is reported as it stands and the disagreement becomes a defect row, never a silent correction.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
READER = HERE / "SEMANTIC_READER_OUTPUT.json"


def space_adjacency(grid, seals):
    """Raster adjacency of the labelled faces: for every pair of faces separated by barrier cells, the kinds of barrier between
    them and the opening sites on it."""
    label, kind, idx = grid["label"], grid["kind"], grid["idx"]
    H, W = label.shape
    pairs = defaultdict(lambda: {"KINDS": Counter(), "SITES": set(), "BANDS": set()})
    from engine.ingest.planar_faces import CODE_KINDS
    rs, cs = np.nonzero(kind)
    for r, c in zip(rs.tolist(), cs.tolist()):
        labs = set()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and label[rr, cc]:
                labs.add(int(label[rr, cc]))
        if len(labs) < 2:
            continue
        i = int(idx[r, c]); s = seals[i] if i >= 0 else None
        k = CODE_KINDS[int(kind[r, c])]
        labs = sorted(labs)
        for a in range(len(labs)):
            for b in range(a + 1, len(labs)):
                e = pairs[(labs[a], labs[b])]
                e["KINDS"][k] += 1
                if s is not None:
                    if s.get("SITE_ID"):
                        e["SITES"].add(s["SITE_ID"])
                    if s.get("BAND_ID"):
                        e["BANDS"].add(s["BAND_ID"])
    return pairs


def _match(reader_rooms, spaces):
    """Map the reader's room names to engine SPACE_IDs: unique labels by text, repeated labels by their order down the sheet."""
    by_label = defaultdict(list)
    for s in spaces:
        for t in s["LABELS"]["EN"]:
            by_label[t.strip().upper()].append(s)
    out, notes = {}, []
    groups = defaultdict(list)
    for rr in reader_rooms:
        base = rr["LABEL"].split("(")[0].strip().upper()
        groups[base].append(rr)
    for base, rrs in groups.items():
        cands = by_label.get(base, [])
        # the reader's Y grows downward on the sheet; model y grows upward
        rrs = sorted(rrs, key=lambda z: z["Y"])
        cands = sorted(cands, key=lambda s: -s["CENTROID_MM"][1])
        for k, rr in enumerate(rrs):
            if k < len(cands):
                out[rr["LABEL"]] = cands[k]["SPACE_ID"]
            else:
                notes.append({"READER_ROOM": rr["LABEL"], "MATCH": None, "WHY": f"the engine has {len(cands)} space(s) carrying the label {base} and the reader names {len(rrs)}"})
    return out, notes


def build(spaces, grid, seals, sites, faces_by_space):
    reader = json.loads(READER.read_text("utf-8"))
    match, notes = _match(reader["ROOMS"], spaces)
    lab_of_space = {s["SPACE_ID"]: faces_by_space[s["SPACE_ID"]]["RUN_LABEL_NOT_A_KEY"] for s in spaces}
    adj = space_adjacency(grid, seals)
    site_by = {s["SITE_ID"]: s for s in sites}
    rows, agree, disagree, unmatched = [], 0, 0, 0
    for a in reader["ADJACENCIES"]:
        sa, sb = match.get(a["ROOM_A"]), match.get(a["ROOM_B"])
        if sa is None or sb is None:
            rows.append({"READER": a, "ENGINE": {"RELATION": "ROOM_NOT_MATCHED", "WHY": "one or both of the reader's rooms has no engine space carrying that label (unlabelled area, or a room the engine did not separate)"},
                         "VERDICT": "NOT_COMPARABLE"})
            unmatched += 1
            continue
        if sa == sb:
            eng = {"RELATION": "SAME_SPACE", "SPACE_ID": sa, "WHY": "the engine holds these two labels in one space: it did not separate them"}
            verdict = "AGREE" if a["RELATION"] == "INTENTIONALLY_OPEN" else "DISAGREE_ENGINE_MERGED"
        else:
            la, lb = lab_of_space[sa], lab_of_space[sb]
            e = adj.get((min(la, lb), max(la, lb)))
            if e is None:
                eng = {"RELATION": "SEPARATE_SPACES_NOT_ADJACENT", "SPACE_A": sa, "SPACE_B": sb, "WHY": "two different spaces with no shared boundary in the raster"}
                verdict = "AGREE" if a["RELATION"].startswith("SEPARATED") else "DISAGREE_ENGINE_SEPARATED"
            else:
                kinds = dict(e["KINDS"])
                site_classes = sorted({site_by[i]["CLASS"] for i in e["SITES"] if i in site_by})
                has_open = any(k in kinds for k in ("OPENING_CHORD",))
                has_unres = "UNRESOLVED_CHORD" in kinds
                rel = "SEPARATED_BY_OPENING_SITE" if has_open else ("SEPARATED_BY_UNRESOLVED_BOUNDARY" if has_unres else "SEPARATED_BY_MATERIAL_WALL")
                eng = {"RELATION": rel, "SPACE_A": sa, "SPACE_B": sb, "BOUNDARY_KINDS_CELLS": kinds, "SITE_CLASSES": site_classes, "SITES": sorted(e["SITES"])}
                if a["RELATION"] == "SEPARATED_WALL_WITH_DOOR":
                    verdict = "AGREE" if (has_open and any("DOOR" in c for c in site_classes)) else ("PARTIAL_ENGINE_PROVISIONAL" if has_unres or has_open else "DISAGREE_ENGINE_SEES_NO_OPENING")
                elif a["RELATION"] == "SEPARATED_WALL_WITH_DOORLESS_OPENING":
                    verdict = "AGREE" if (has_open or has_unres) else "DISAGREE_ENGINE_SEES_NO_OPENING"
                elif a["RELATION"] == "SEPARATED_WALL_NO_OPENING":
                    verdict = "AGREE" if rel == "SEPARATED_BY_MATERIAL_WALL" else ("PARTIAL_ENGINE_PROVISIONAL" if has_unres else "DISAGREE_ENGINE_SEES_AN_OPENING")
                elif a["RELATION"] == "INTENTIONALLY_OPEN":
                    verdict = "DISAGREE_ENGINE_SEPARATED"
                else:
                    verdict = "NOT_COMPARABLE"
        rows.append({"READER": a, "ENGINE": eng, "VERDICT": verdict})
        agree += verdict == "AGREE"
        disagree += verdict.startswith("DISAGREE")
    return {"ARTIFACT": "PA08_QORTUBA_R1_SEMANTIC_RECONCILIATION", "READER_INPUT": reader["INPUT_SHOWN"], "READER_NOT_SHOWN": reader["INPUT_NOT_SHOWN"],
            "READER_STATUS": reader["STATUS"], "USE": reader["USE"], "ROOM_MATCHING": match, "MATCHING_NOTES": notes,
            "ROWS": rows, "COUNT": len(rows), "AGREE": agree, "DISAGREE": disagree, "NOT_COMPARABLE": unmatched,
            "BY_VERDICT": dict(Counter(x["VERDICT"] for x in rows)),
            "READER_NOTES": reader["READER_NOTES"], "READER_BATHS": reader["BATHS"], "READER_VESTIBULE": reader["VESTIBULE"], "READER_WET_AREAS": reader["WET_AREAS"],
            "RULE": "QA only: a disagreement is recorded as a defect, never resolved by editing geometry towards the reader; the reader can be wrong and it saw no engine output"}
