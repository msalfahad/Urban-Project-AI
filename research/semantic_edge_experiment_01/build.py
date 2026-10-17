"""Build SEMANTIC_EDGE_EXPERIMENT_01: protocol, sample, groups, crops, Pass A.

Everything here is deterministic. E1.4 is rebuilt read-only and never
modified, and no classification produced later is fed back into it.

Order matters and is enforced by this file: the protocol is written and
hashed BEFORE the sample is selected, and the sample is selected BEFORE
any crop is rendered or looked at.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

from engine import cad_geometry as cg
from engine import interval_role as ir
from research.semantic_edge_experiment_01 import a19 as A19
from research.semantic_edge_experiment_01 import protocol as P
from research.semantic_edge_experiment_01 import sampling as S
from tools import run_e1_2 as r12
from tools import run_e1_3 as r13
from tools import run_e1_4 as r14

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")

PRIMARY_RGB = (220, 20, 60)
CONTEXT_RGB = (0, 150, 200)
LABEL_RGB = (140, 0, 40)


class Args:
    decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
    a18_dir = "data/runs/7757/blind/A18-GF-001"
    raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    rules = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"
    prior_e1_3 = "data/runs/7757/e1_3"
    sandbox = ""
    v2_sandbox = ""
    out = "data/runs/7757/e1_4"


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (body if isinstance(body, str)
            else json.dumps(body, indent=2, ensure_ascii=False,
                            default=str) + "\n")
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------- the crops

def _draw(sheet, reg, centre, half, members, labelled, path, *, marked):
    from PIL import Image, ImageDraw
    got = r12._frame(sheet, reg, centre, half, P.CROP_PIXELS)
    if got is None:
        return None
    img, to_px, box = got
    img = img.convert("RGB")
    if marked:
        draw = ImageDraw.Draw(img)
        lab_of = {iv.interval_id: k for k, iv in labelled.items()}
        for iv, parent in members:
            try:
                pts = [to_px(x, y) for x, y in cg._as_segment(
                    r12.IntervalPrim(parent, iv)).points(tol_mm=2.0)]
            except Exception:
                continue
            if len(pts) < 2:
                continue
            tag = lab_of.get(iv.interval_id)
            draw.line(pts, fill=PRIMARY_RGB if tag else CONTEXT_RGB,
                      width=4 if tag else 2)
            if tag:
                mx, my = pts[len(pts) // 2]
                draw.text((mx + 6, my + 6), tag, fill=LABEL_RGB)
    img.save(path)
    return {"path": str(path), "box_mm": [round(v, 3) for v in box],
            "pixels": list(P.CROP_PIXELS), "MARKED": bool(marked),
            "SHA256": sha(path)}


def crops_for(group, sheet, reg, by_id, labelled, dest):
    box = group["_box"]
    centre = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
    extent = max(box[2] - box[0], box[3] - box[1])
    members = [(iv, by_id.get(iv.parent_object_id))
               for iv in group["_members"]
               if by_id.get(iv.parent_object_id) is not None]

    plan = [(P.LEVEL_A, max(extent / 2.0 + P.CONTEXT_MARGIN_MM,
                            P.CONTEXT_MIN_HALF_MM), (False,)),
            (P.LEVEL_B, max(extent / 2.0 + P.FEATURE_MARGIN_MM,
                            P.FEATURE_MIN_HALF_MM), (False, True))]
    if extent <= P.DETAIL_TRIGGER_EXTENT_MM or any(
            iv.kind in ("ARC", "CIRCLE") for iv in group["_members"]):
        plan.append((P.LEVEL_C, max(extent / 2.0 + P.DETAIL_MARGIN_MM,
                                    P.DETAIL_MIN_HALF_MM), (False, True)))

    rows = []
    for level, half, marks in plan:
        for marked in marks:
            name = f"{level}{'_MARKED' if marked else '_CLEAN'}.png"
            got = _draw(sheet, reg, centre, half, members, labelled,
                        dest / name, marked=marked)
            if got:
                rows.append({"LEVEL": level, "FILE": name,
                             "half_extent_mm": round(half, 3), **got})
    return rows


# ------------------------------------------------- whole-floor context

_ID = re.compile(r"(E1_2:|CAD-\d+)")
_COORD = re.compile(r"[-+]?\d{4,}\s*[,;]\s*[-+]?\d{4,}")


def floor_context(a18_candidates) -> tuple:
    """§14 - identities and rough whereabouts. Never an entity's answer."""
    toks, boxes = {}, {}
    for c in a18_candidates:
        t = (c.get("confidence_sources") or {}).get("matched_on_label_token") \
            or c.get("label_as_drawn") or ""
        t = str(t).strip().upper()
        if not t:
            continue
        toks[t] = toks.get(t, 0) + 1
        b = c.get("box")
        if b and len(b) == 4:
            boxes.setdefault(t, []).append(
                ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0))

    xs = [p[0] for v in boxes.values() for p in v]
    ys = [p[1] for v in boxes.values() for p in v]
    x0, x1 = (min(xs), max(xs)) if xs else (0.0, 1.0)
    y0, y1 = (min(ys), max(ys)) if ys else (0.0, 1.0)

    def side(t):
        pts = boxes.get(t) or []
        if not pts:
            return "somewhere on the plan"
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        fx = (cx - x0) / (x1 - x0) if x1 > x0 else 0.5
        fy = (cy - y0) / (y1 - y0) if y1 > y0 else 0.5
        h = "left" if fx < 0.34 else "right" if fx > 0.66 else "middle"
        v = "upper" if fy < 0.34 else "lower" if fy > 0.66 else "central"
        return f"towards the {v} {h} of the plan"

    lines = [
        "WHOLE-FLOOR CONTEXT",
        "",
        "This is general orientation for the floor you are reading a small",
        "part of. It does not tell you what any line is. It is here so that",
        "you can tell an external facade from an internal partition, and a",
        "service room from a living space.",
        "",
        "Rooms and areas the drawing's own labels name on this floor:",
    ]
    for t in sorted(toks):
        lines.append(f"  {t} - {side(t)}")
    lines += [
        "",
        "The plan is a villa ground floor. It has an open outdoor court and",
        "a garden wrapping the built form, a swimming pool in the outdoor",
        "area, a stair, a service block with kitchen and driver's room, and",
        "a run of reception spaces that open into one another rather than",
        "being separated by doors.",
        "",
        "Nothing above says what any particular line, arc or entity is. Read",
        "that from the picture.",
    ]
    text = "\n".join(lines) + "\n"
    problems = []
    if _ID.search(text):
        problems.append("AN_ENTITY_ID_IS_PRESENT")
    if _COORD.search(text):
        problems.append("A_COORDINATE_PAIR_IS_PRESENT")
    return text, problems


# -------------------------------------------------------------- the build

def main() -> int:
    t0 = time.time()
    a = Args()

    # 1. the protocol, written and hashed before anything is selected
    OUT.mkdir(parents=True, exist_ok=True)
    proto = P.record()
    proto_hash = write(OUT / "00_PROTOCOL.json", {
        **proto,
        "A19_BRIEF_HASH": A19.brief_hash(),
        "ANSWER_SCHEMA": A19.ANSWER_SCHEMA,
        "PASS_B_SCHEMA": A19.PASS_B_SCHEMA,
        "THE_PROTOCOL_IS_HASHED_BEFORE_THE_SAMPLE_EXISTS": True,
    })

    st = r14._core(a)
    t_core = time.time() - t0
    interp, gf = st["interp"], st["gf"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    semantics = {r["INTERVAL_ID"]: r for r in st["semantics"]["ROWS"]}
    intervals = [iv for rows_ in interp["roles"]["intervals"].values()
                 for iv in rows_]
    iv_by_id = {iv.interval_id: iv for iv in intervals}

    # 2. the sample
    rows, index = S.classify_strata(intervals)
    picked, pool_by_stratum, shortfalls = S.select(rows)
    counts = {}
    for r in rows:
        counts[r["STRATUM"]] = counts.get(r["STRATUM"], 0) + 1

    # 3. the feature neighbourhoods
    groups, collisions = [], []
    seen_group = {}
    for r in picked:
        seed = iv_by_id[r["INTERVAL_ID"]]
        g = S.assemble(seed, intervals, index, by_id=by_id)
        g["STRATUM"] = r["STRATUM"]
        g["SELECTED_BY"] = r["SELECTED_BY"]
        g["SEED_FACTS"] = r["MECHANICAL_FACTS"]
        g["SEED_WHY_ELIGIBLE"] = r["WHY_ELIGIBLE"]
        prev = seen_group.get(g["FEATURE_GROUP_ID"])
        if prev is not None:
            collisions.append({"FEATURE_GROUP_ID": g["FEATURE_GROUP_ID"],
                               "SEEDS": [prev, r["INTERVAL_ID"]],
                               "why": S.P.A_SEED_IS_NOT_THE_FEATURE})
            continue
        seen_group[g["FEATURE_GROUP_ID"]] = r["INTERVAL_ID"]
        groups.append(g)

    sel_hash = write(OUT / "01_SAMPLE_SELECTION.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_RULES_WERE_FROZEN_BEFORE_THIS_RAN": True,
        "the_sample_cannot_depend_on_the_answer":
            P.THE_SAMPLE_CANNOT_DEPEND_ON_THE_ANSWER,
        "intervals_on_the_floor": len(intervals),
        "eligible_seeds": len(rows),
        "eligible_by_stratum": counts,
        "PER_STRATUM_QUOTA": P.PER_STRATUM_QUOTA,
        "SAMPLE_TARGET": P.SAMPLE_TARGET,
        "shortfalls": shortfalls,
        "selected": len(picked),
        "distinct_feature_neighbourhoods": len(groups),
        "SEED_COLLISIONS": collisions,
        "SELECTED": picked,
    })

    # 4. crops
    reg, sheet = r13._registered_sheet(a, gf)
    if sheet is None or not getattr(sheet, "ok", False):
        raise SystemExit("the source sheet did not register; no crops")

    crops_root = OUT / "crops"
    if crops_root.exists():
        shutil.rmtree(crops_root)
    crop_rows, group_rows = [], []
    for g in groups:
        labelled = {}
        order = [iv_by_id[i] for i in g["PRIMARY_ENTITY_IDS"]]
        order += [iv_by_id[i] for i in g["CONTEXT_ENTITY_IDS"]]
        for n, iv in enumerate(order[:P.MAX_LABELLED_MEMBERS], start=1):
            labelled[f"P{n:02d}"] = iv
        dest = crops_root / g["FEATURE_GROUP_ID"]
        dest.mkdir(parents=True, exist_ok=True)
        made = crops_for(g, sheet, reg, by_id, labelled, dest)
        crop_rows.append({"FEATURE_GROUP_ID": g["FEATURE_GROUP_ID"],
                          "CROPS": made})
        g["_labelled"] = labelled
        group_rows.append({k: v for k, v in g.items()
                           if not k.startswith("_")})

    grp_hash = write(OUT / "02_FEATURE_GROUP_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "asks_only_what_to_show_together":
            P.ASSEMBLY_ASKS_ONLY_WHAT_TO_SHOW_TOGETHER,
        "RULES": list(P.ASSEMBLY_RULES),
        "feature_groups": len(group_rows),
        "GROUPS": group_rows,
    })
    crop_hash = write(OUT / "03_CROP_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "RULES": list(P.CROP_RULES),
        "a_mark_is_not_a_label": P.A_MARK_IS_NOT_A_LABEL,
        "MAX_LABELLED_MEMBERS": P.MAX_LABELLED_MEMBERS,
        "no_crop_in_this_experiment_was_placed_by_hand": True,
        "crops": sum(len(r["CROPS"]) for r in crop_rows),
        "BY_GROUP": crop_rows,
    })

    # 5. what E1.4 currently says - for PASS B only, never for PASS A
    base = []
    for g in groups:
        rowset = []
        for lab, iv in g["_labelled"].items():
            rowset.append({
                "MEMBER_LABEL": lab,
                "INTERVAL_ID": iv.interval_id,
                "E1_4_SEMANTIC_ROLE": iv.role,
                "E1_4_CONFIDENCE": iv.confidence,
                "E1_4_LINE_SEMANTICS_STATUS": (
                    semantics.get(iv.interval_id) or {}).get(
                        "LINE_SEMANTICS_STATUS"),
                "E1_4_MAY_BOUND_MATERIAL": bool(iv.may_bound_material),
            })
        base.append({"FEATURE_GROUP_ID": g["FEATURE_GROUP_ID"],
                     "STRATUM": g["STRATUM"], "MEMBERS": rowset})
    base_hash = write(OUT / "04_E1_4_BASELINE.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "E1_4_IS_READ_ONLY_HERE": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "THIS_FILE_IS_NOT_IN_THE_PASS_A_SANDBOX": True,
        "why": P.PASS_A_IS_FROZEN_BEFORE_PASS_B_EXISTS,
        "GROUPS": base,
    })

    # 6. the Pass A tasks
    a18 = json.loads((Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json")
                     .read_text(encoding="utf-8"))["candidates"]
    ctx_text, ctx_problems = floor_context(a18)
    if ctx_problems:
        raise SystemExit(f"the floor context is not clean: {ctx_problems}")

    box = OUT / "a19" / "pass_a_sandbox"
    if box.exists():
        shutil.rmtree(box)
    manifest = []
    for g, crow in zip(groups, crop_rows):
        gid = g["FEATURE_GROUP_ID"]
        d = box / gid
        d.mkdir(parents=True)
        for c in crow["CROPS"]:
            shutil.copy(c["path"], d / c["FILE"])
        members = []
        for lab, iv in g["_labelled"].items():
            parent = by_id.get(iv.parent_object_id)
            members.append({
                "MEMBER_LABEL": lab,
                "IS_PRIMARY": iv.interval_id in set(g["PRIMARY_ENTITY_IDS"]),
                "LAYER": str(iv.layer),
                "ENTITY_TYPE": str(iv.entity_type),
                "GEOMETRY_KIND": str(iv.kind),
                "LINETYPE": str(getattr(parent, "linetype", "") or ""),
                "BLOCK": str((iv.provenance or {}).get("block_id") or ""),
            })
        task = {
            "FEATURE_GROUP_ID": gid,
            "WHAT_YOU_ARE_LOOKING_AT": (
                "one local feature neighbourhood of an architectural "
                "ground floor plan"),
            "MARKED_MEMBERS": members,
            "unlabelled_members_shown_in_the_second_colour":
                max(0, g["LOCAL_TOPOLOGY"]["members"] - len(members)),
            "CROPS": [c["FILE"] for c in crow["CROPS"]],
            "FENESTRATION_READING_IS_REQUIRED":
                g["STRATUM"] in P.FENESTRATION_IS_ASKED_OF,
            "CURVE_FAMILY_IS_REQUIRED":
                g["STRATUM"] in P.CURVE_FAMILY_IS_ASKED_OF,
            "ANSWER_SCHEMA": A19.ANSWER_SCHEMA,
        }
        write(d / "TASK.json", task)
        write(d / "BRIEF.txt", A19.PASS_A_BRIEF)
        write(d / "FLOOR_CONTEXT.txt", ctx_text)
        manifest.append({
            "FEATURE_GROUP_ID": gid,
            "STRATUM": g["STRATUM"],
            "marked_members": len(members),
            "CROP_SHA256": {c["FILE"]: c["SHA256"] for c in crow["CROPS"]},
            "TASK_SHA256": sha(d / "TASK.json"),
            "BRIEF_SHA256": sha(d / "BRIEF.txt"),
            "FLOOR_CONTEXT_SHA256": sha(d / "FLOOR_CONTEXT.txt"),
        })

    man_hash = write(OUT / "a19" / "PASS_A_INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PASS": P.PASS_A,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A19_BRIEF_HASH": A19.brief_hash(),
        "WHAT_THE_SANDBOX_CONTAINS": (
            "per feature group: the source crops, the marked-member table "
            "with layer, linetype, entity type and block, the Pass A "
            "brief, and the whole-floor context. Nothing else"),
        "WHAT_IT_DOES_NOT_CONTAIN": list(P.PASS_A_NEVER_RECEIVES),
        "NO_COORDINATE_IS_GIVEN_TO_THE_READER": (
            "the marked-member table carries no coordinate, length or "
            "dimension. The crop shows where things are, which is the "
            "CAD's job, and the reader's job is what they are"),
        "the_floor_context_was_screened":
            "no entity id and no coordinate pair is present in it",
        "tasks": len(manifest),
        "TASKS": manifest,
    })

    out = {
        "PROTOCOL_HASH": P.protocol_hash(),
        "00_PROTOCOL_SHA256": proto_hash,
        "01_SAMPLE_SELECTION_SHA256": sel_hash,
        "02_FEATURE_GROUP_REGISTER_SHA256": grp_hash,
        "03_CROP_REGISTER_SHA256": crop_hash,
        "04_E1_4_BASELINE_SHA256": base_hash,
        "PASS_A_INPUT_MANIFEST_SHA256": man_hash,
        "intervals_on_the_floor": len(intervals),
        "eligible_seeds": len(rows),
        "eligible_by_stratum": counts,
        "shortfalls": shortfalls,
        "feature_groups": len(groups),
        "seed_collisions": len(collisions),
        "crops": sum(len(r["CROPS"]) for r in crop_rows),
        "seconds_rebuilding_e1_4_evidence": round(t_core, 1),
        "seconds_total": round(time.time() - t0, 1),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
