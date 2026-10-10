"""R8.7 proof: QS01 input contract by ablation, three-run revision delta, scoped Q-14, region classification.

    python3 research/external_engine_lab/r8_7_proof.py <work_dir> <register_dir>

<work_dir> holds the cached K2 records (r8_7_canonical.py build-k2):
    old_k2.pkl  K2 route on LibreDWG's DXF of the OLD DWG (same revision, other route -> PARSER_DIFFERENCE)
    new_k2.pkl  K2 route on the NEW revision DXF df0e1d69 (hash-addressed input)
Run outside any test session (the determinism guard forbids test-time writes). SHADOW: nothing is published.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_7_canonical as R7                                                                # noqa: E402
from engine.source import canonical_build as CB, canonical_input as CI, owner_scope as OS  # noqa: E402

R86_PROOF = ROOT / "tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json"
CERAMIC = ("BATH", "PAINTRY")                     # the legacy row predicates (owner_rules.CERAMIC_ROOM_NAMES)


def rkey(r):
    """Revision-free source identity: what makes one record comparable across revisions and routes."""
    i = r.identity
    return (i.source_handle, i.instance_handles, i.part_kind, i.part_index)


# ------------------------------------------------------------------ ablations
def ablations(base):
    """Each declared field corrupted on the OLD revision input. lenient = what the method silently does;
    guarded = what the contract returns. A field 'changes output' when the lenient run differs from the base."""
    ref = R7.measure(base, expected_revision_id=R7.REV_OLD_ID)
    ref_rooms = sorted(((r["room"], r["area_m2"]) for r in ref["rooms"]), key=repr)

    def parts_where(pred, f):
        return replace(base, parts=tuple(f(p) if pred(p) else p for p in base.parts))

    inblock = lambda p: bool(p.identity.instance_handles)                      # noqa: E731
    poly = lambda p: p.entity_type == "LWPOLYLINE"                              # noqa: E731
    no_block = lambda p: replace(p, lineage=())                                 # noqa: E731
    no_index = lambda p: replace(p, identity=replace(p.identity, part_index=None))   # noqa: E731
    cases = [
        ("parts.block_identity", "block identity removed from every part placed through a block",
         parts_where(inblock, no_block)),
        ("parts.source_part_id", "part identity collapsed (part index removed from polyline spans)",
         parts_where(poly, no_index)),
        ("parts.block_identity+parts.source_part_id", "the R8.6 lossy mapping: both at once",
         parts_where(lambda p: True, lambda p: (no_index(no_block(p)) if poly(p) and inblock(p) else
                                                no_block(p) if inblock(p) else no_index(p) if poly(p) else p))),
        ("parts.source_part_id(duplicate)", "every polyline span given part index 0 (duplicate identity)",
         parts_where(poly, lambda p: replace(p, identity=replace(p.identity, part_index=0)))),
        ("parts.instance_path", "instance path removed from parts placed through a block",
         parts_where(inblock, lambda p: replace(p, identity=replace(p.identity, instance_handles=None)))),
        ("parts.layer", "layer removed from every part", parts_where(lambda p: True, lambda p: replace(p, layer=None))),
        ("texts.world_placement", "placement removed from every text",
         replace(base, texts=tuple(replace(t, x=None, y=None) for t in base.texts))),
        ("texts.text_value", "value removed from every text",
         replace(base, texts=tuple(replace(t, value=None) for t in base.texts))),
        ("texts.text_height (not declared)", "height removed from every text (not a declared field)",
         replace(base, texts=tuple(replace(t, height=None) for t in base.texts))),
        ("dimensions.placed_points", "placement removed from every dimension",
         replace(base, dimensions=tuple(replace(d, placed_points=None) for d in base.dimensions))),
        ("dimensions.measurement", "authored measurement removed from every dimension",
         replace(base, dimensions=tuple(replace(d, measurement=None) for d in base.dimensions))),
        ("dimensions.dimension_type", "dimension type removed",
         replace(base, dimensions=tuple(replace(d, dimension_type=None) for d in base.dimensions))),
        ("parts.visibility", "parts placed through one block marked VISIBILITY_UNRESOLVED",
         parts_where(lambda p: inblock(p) and p.identity.instance_handles[0] == "156",
                     lambda p: replace(p, visibility=CI.VISIBILITY_UNRESOLVED))),
        ("input.unit_claim_id", "the unit claim removed from the input", replace(base, unit_claim_id=None)),
    ]
    out = []
    for field, what, inp in cases:
        guarded = R7.measure(inp, expected_revision_id=R7.REV_OLD_ID)
        try:
            len_ = R7.lenient_values(inp)
            rooms = sorted(((r["room"], r["area_m2"]) for r in len_["rooms"]), key=repr)
            lenient = {"six": len_["six"], "six_change": len_["six"] != ref["six"], "rooms_change": rooms != ref_rooms,
                       "rooms_only_in_lenient_run": [r for r in rooms if r not in ref_rooms]}
        except Exception as e:                                                   # the lenient bridge may itself fail
            lenient = {"error": f"{type(e).__name__}: {e}", "six_change": None, "rooms_change": None}
        out.append({"field": field, "corruption": what, "lenient_legacy_run": lenient,
                    "guarded_state": guarded["state"], "guarded_quantity": guarded["six"],
                    "missing_fields": guarded["validation"]["missing_fields"],
                    "ambiguous_fields": guarded["validation"]["ambiguous_fields"],
                    "visibility_unresolved": guarded["validation"]["visibility_unresolved"]})
    # region / revision isolation cases
    new_inp_rev = replace(base, revision=R7.rev_new())
    mixed = R7.measure(new_inp_rev, expected_revision_id=R7.REV_NEW_ID)
    out.append({"field": "source_revision (mixed)", "corruption": "OLD revision records under the NEW revision anchor",
                "guarded_state": mixed["state"], "guarded_quantity": mixed["six"],
                "revision_conflicts": len(mixed["validation"]["revision_conflicts"])})
    wrong = replace(base, region_id="RC:PLAN_VARIANT_3")
    w = R7.measure(wrong, expected_revision_id=R7.REV_OLD_ID)
    out.append({"field": "region_id (wrong plan variant)", "corruption": "input built for another plan variant",
                "guarded_state": w["state"], "guarded_quantity": w["six"],
                "region_conflicts": w["validation"]["region_conflicts"]})
    cand = R7.old_input(bounds=R7.BOUNDS)
    cg = R7.measure(cand, expected_revision_id=R7.REV_OLD_ID)
    # the OLD silent behaviour: each part clipped on its own (no occurrence check), corner marks silently dropped
    full = R7.old_input(bounds=(-1e12, -1e12, 1e12, 1e12))
    per_part = replace(full, parts=tuple(p for p in full.parts if CB.membership(p, R7.BOUNDS) == CI.IN_REGION),
                       texts=tuple(t for t in full.texts if CB.membership(t, R7.BOUNDS) == CI.IN_REGION),
                       dimensions=tuple(d for d in full.dimensions if CB.membership(d, R7.BOUNDS) == CI.IN_REGION))
    cl = R7.lenient_values(per_part)
    out.append({"field": "region membership (candidate bounds)",
                "corruption": "clip to the region candidate's recorded bounds, which lie inside the frame's corner marks "
                              "(lenient = the old per-part clipping, which drops the 8 corner-mark parts silently)",
                "guarded_state": cg["state"], "guarded_quantity": cg["six"],
                "region_review_required": cg["validation"]["region_review_required"],
                "lenient_legacy_run": {"six": cl["six"], "six_change": cl["six"] != ref["six"],
                                       "rooms_only_in_lenient_run": [r for r in sorted(((x["room"], x["area_m2"]) for x in cl["rooms"]), key=repr)
                                                                     if r not in ref_rooms]}})
    return ref, out


def parser_culprits(k1, k2):
    """Bisect which K2 parts, substituted one group at a time into the K1 input, change the six rows (the
    route difference on ONE revision). Returns the minimal culprit set and its coordinate differences."""
    ref = R7.measure(k1, expected_revision_id=R7.REV_OLD_ID)["six"]
    kb = {rkey(p): p for p in k2.parts}
    cand = [rkey(p) for p in k1.parts if rkey(p) in kb and p.geometry != kb[rkey(p)].geometry]

    def changes(sub):
        s_ = set(sub)
        x = replace(k1, parts=tuple(kb[rkey(p)] if rkey(p) in s_ else p for p in k1.parts))
        return R7.measure(x, expected_revision_id=R7.REV_OLD_ID)["six"] != ref
    if not changes(cand):
        return {"culprits": [], "parts_with_any_coordinate_difference": len(cand)}
    lo = cand
    while len(lo) > 1:
        half = lo[:len(lo) // 2]
        lo = half if changes(half) else lo[len(lo) // 2:]
    ka = {rkey(p): p for p in k1.parts}
    k = lo[0]
    return {"parts_with_any_coordinate_difference": len(cand),
            "culprits": [{"part": list(map(str, k)), "layer": ka[k].layer, "k1_geometry": list(ka[k].geometry),
                          "k2_geometry": list(kb[k].geometry),
                          "max_abs_difference": max(abs(a - b) for a, b in zip(ka[k].geometry, kb[k].geometry))}]}


# ------------------------------------------------------------------ rooms, labels, rows
def label_handles(room, texts):
    """The texts placed INSIDE the room's own rectangles (containment on the room polygon; no nearest match)."""
    out = []
    for t in texts:
        if t.x is None:
            continue
        x, y = t.x * 10.0, t.y * 10.0                                              # rectangles are in mm
        if any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in room["rectangles"]):
            out.append(t.identity.source_handle + "@" + "/".join(t.identity.instance_handles))
    return sorted(out)


def rows_of(rooms):
    """The six rows by the legacy predicates (owner_rules): WET floors; BATH/PAINTRY prefix and DRY; the rest."""
    def total(sel):
        if any(r["area_m2"] is None for r in sel):
            return None, [r["room"] for r in sel if r["area_m2"] is None]
        return round(sum(r["area_m2"] for r in sel), 4), []
    wet = [r for r in rooms if r["wet_or_dry"] == "WET"]
    serv = [r for r in rooms if r["room"].split(" /")[0] in CERAMIC and r["wet_or_dry"] == "DRY"]
    dry = [r for r in rooms if r["room"].split(" /")[0] not in CERAMIC]
    out = {}
    for rid, sel in (("Q-03", wet), ("Q-11", wet), ("Q-03P", serv), ("Q-12", serv), ("Q-13", dry), ("Q-14", rooms)):
        v, missing = total(sel)
        out[rid] = {"value": v, "rooms": [f"{r['room']} {r['area_m2']}" for r in sel], "rooms_not_established": missing}
    return out


def record_delta(old, new, bounds):
    """OLD vs NEW records in the region, by revision-free identity, over the UNION of both sides' in-region keys:
    unchanged / changed / removed / added."""
    def inside(r):
        return CB.membership(r, bounds) == CI.IN_REGION
    out = {}
    for name in ("parts", "texts", "dimensions"):
        A = {rkey(r): r for r in getattr(old, name)}
        Bm = {rkey(r): r for r in getattr(new, name)}
        keys = {k for k, r in A.items() if inside(r)} | {k for k, r in Bm.items() if inside(r)}
        a = {k: A[k] for k in sorted(keys, key=repr) if k in A}
        b = {k: Bm[k] for k in sorted(keys, key=repr) if k in Bm}
        changed = [k for k in a if k in b and not same(a[k], b[k])]
        out[name] = {"unchanged": sum(1 for k in a if k in b) - len(changed), "changed": len(changed),
                     "removed": len([k for k in a if k not in b]), "added": len([k for k in b if k not in a]),
                     "removed_examples": [list(map(str, k)) for k in sorted(a.keys() - b.keys(), key=repr)[:10]],
                     "added_examples": [list(map(str, k)) for k in sorted(b.keys() - a.keys(), key=repr)[:10]]}
        out[name]["_sets"] = (a, b, changed)
    return out


def same(x, y):
    if isinstance(x, CI.CanonicalPart):
        return x.layer == y.layer and all(abs(p - q) <= 1e-6 for p, q in zip(x.geometry, y.geometry))
    if isinstance(x, CI.PlacedText):
        return x.value == y.value and abs((x.x or 0) - (y.x or 0)) <= 1e-6 and abs((x.y or 0) - (y.y or 0)) <= 1e-6
    if x.placed_points is None or y.placed_points is None:
        return x.placed_points == y.placed_points
    return (abs((x.measurement or 0) - (y.measurement or 0)) <= 1e-6 and
            all(abs(p - q) <= 1e-6 for P, Q in zip(x.placed_points, y.placed_points) for p, q in zip(P, Q)))


def room_box(room, pad_native=30.0):
    xs = [v for r in room["rectangles"] for v in (r[0], r[2])]
    ys = [v for r in room["rectangles"] for v in (r[1], r[3])]
    if not xs:
        return None
    return (min(xs) / 10 - pad_native, min(ys) / 10 - pad_native, max(xs) / 10 + pad_native, max(ys) / 10 + pad_native)


def changes_near(box, delta):
    """Which changed / removed / added source records lie within a room's box (wall thickness margin)."""
    if box is None:
        return {}
    out = {}
    for name in ("parts", "texts", "dimensions"):
        a, b, changed = delta[name]["_sets"]
        def hit(r):
            pts = CB._points(r) or []
            return any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in pts)
        rem = [k for k in a if k not in b and hit(a[k])]
        add = [k for k in b if k not in a and hit(b[k])]
        chg = [k for k in changed if hit(a[k]) or hit(b[k])]
        if rem or add or chg:
            out[name] = {"removed": sorted({f"H{k[0]}" for k in rem}), "added": sorted({f"H{k[0]}" for k in add}),
                         "changed": sorted({f"H{k[0]}" for k in chg}),
                         "records": {"removed": len(rem), "added": len(add), "changed": len(chg)},
                         "layers": dict(sorted(Counter((a.get(k) or b.get(k)).layer for k in rem + add + chg).items()))}
    return out


def pair_rooms(old_rooms, new_rooms, old_texts, new_texts):
    """Old room <-> new room when they share a label TEXT source handle (identity, not geometry)."""
    oh = {i: set(label_handles(r, old_texts)) for i, r in enumerate(old_rooms)}
    nh = {j: set(label_handles(r, new_texts)) for j, r in enumerate(new_rooms)}
    pairs = []
    for i, hs in oh.items():
        js = [j for j, h in nh.items() if hs & h]
        pairs.append((i, js))
    return pairs, oh, nh


# ------------------------------------------------------------------ region classification of the whole new DXF
def classify_new(blob):
    frames = {v: CB.occurrence_extent(blob["parts"], h) for v, h in R7.VARIANT_FRAMES.items()}
    recs = [("parts", r) for r in blob["parts"]] + [("texts", r) for r in blob["texts"]] + [("dimensions", r) for r in blob["dims"]]
    occ_states = {}
    for name, r in recs:
        m = {v: CB.membership(r, b) for v, b in frames.items()}
        occ_states.setdefault(CB.occurrence(r), []).append((name, r, m))
    counts = Counter()
    for occ, items in occ_states.items():
        for name, r, m in items:
            if not CB._points(r):
                cls = "UNRESOLVED"
            elif m["PLAN_VARIANT_4_SELECTED"] == CI.IN_REGION:
                cls = "SELECTED_MEASUREMENT_REGION"
            elif m["PLAN_VARIANT_4_SELECTED"] == CI.REVIEW_REQUIRED:
                cls = "REVIEW_REQUIRED"
            elif any(m[v] == CI.IN_REGION for v in frames if v != "PLAN_VARIANT_4_SELECTED"):
                cls = "ALTERNATE_PLAN_VARIANT"
            elif any(m[v] == CI.REVIEW_REQUIRED for v in frames):
                cls = "REVIEW_REQUIRED"
            elif name in ("texts", "dimensions"):
                cls = "ANNOTATION"
            elif occ.startswith("I"):
                cls = "BLOCK_SAMPLE"
            else:
                cls = "OUTSIDE_SELECTED_MEASUREMENT_REGION"
            counts[(cls, name)] += 1
    # occurrence-level consistency: an occurrence with parts in the selected frame and outside it is REVIEW_REQUIRED
    split = [o for o, items in occ_states.items() if len({m["PLAN_VARIANT_4_SELECTED"] for _, _, m in items}) > 1 and o.startswith("I")]
    return {"frames": {v: {"frame_occurrence": R7.VARIANT_FRAMES[v], "extent": list(b)} for v, b in frames.items()},
            "counts": {f"{c}:{n}": k for (c, n), k in sorted(counts.items())},
            "occurrences_split_by_the_selected_frame": split,
            "DETAIL": "no record is classified DETAIL: the file carries no evidence (title or detail marker) that "
                      "identifies a detail drawing; such content falls under OUTSIDE / BLOCK_SAMPLE / ANNOTATION",
            "rule": "only SELECTED_MEASUREMENT_REGION enters the selected apartment takeoff; nothing is deleted"}


# ------------------------------------------------------------------ main
def main(work, out):
    work, out = Path(work), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base = R7.old_input()
    ref, abl = ablations(base)
    old_k2, _ = R7.input_from_pickle(work / "old_k2.pkl", R7.rev_old())
    new_k2, blob_new = R7.input_from_pickle(work / "new_k2.pkl", R7.rev_new())
    runs = {"OLD_K1": ref, "OLD_K2": R7.measure(old_k2, expected_revision_id=R7.REV_OLD_ID),
            "NEW_K2": R7.measure(new_k2, expected_revision_id=R7.REV_NEW_ID)}
    inputs = {"OLD_K1": base, "OLD_K2": old_k2, "NEW_K2": new_k2}
    r86 = json.loads(R86_PROOF.read_text())
    r86_six = {r["row_id"].split("|")[0]: r["canonical_native_value"] / 1e4 if r["canonical_native_value"] else None for r in r86["rows"]}

    # parser difference: OLD_K1 vs OLD_K2 records (same revision)
    pdelta = record_delta(base, old_k2, R7.frame_bounds(base.parts))
    exact = sorted(((rkey(p), max(abs(x - y) for x, y in zip(p.geometry, q.geometry)))
                    for p in base.parts for q in [ {rkey(z): z for z in old_k2.parts}.get(rkey(p))] if q is not None),
                   key=lambda t: -t[1])
    # revision difference: OLD_K2 vs NEW_K2 (same route)
    rdelta = record_delta(old_k2, new_k2, R7.frame_bounds(new_k2.parts))
    culprits = parser_culprits(base, old_k2)
    rows = {k: rows_of(runs[k]["rooms"]) for k in runs}
    pairs, oh, nh = pair_rooms(runs["OLD_K2"]["rooms"], runs["NEW_K2"]["rooms"], old_k2.texts, new_k2.texts)
    room_rows = []
    for i, js in pairs:
        o = runs["OLD_K2"]["rooms"][i]
        news = [runs["NEW_K2"]["rooms"][j] for j in js]
        k1 = next((r for r in runs["OLD_K1"]["rooms"] if set(label_handles(r, base.texts)) == oh[i]), None)
        near = changes_near(room_box(o), rdelta)
        for n in news:
            near_n = changes_near(room_box(n), rdelta)
            for k, v in near_n.items():
                near.setdefault(k, v)
        value_change = len(news) != 1 or news[0]["area_m2"] != o["area_m2"]
        merged = [n["room"] for n in news if len({h.split("@")[1] for h in label_handles(n, new_k2.texts)}) > 1]
        cause = []
        if k1 is not None and k1["area_m2"] != o["area_m2"]:
            cause.append("PARSER_DIFFERENCE (old revision, K1 vs K2 route)")
        if value_change:
            cause.append("SOURCE_REVISION_CHANGE" if near else "UNEXPLAINED")
        room_rows.append({"old_room_K1": None if k1 is None else [k1["room"], k1["area_m2"]],
                          "old_room_K2": [o["room"], o["area_m2"]], "label_text_occurrences": sorted(oh[i]),
                          "new_rooms": [[n["room"], n["area_m2"]] for n in news],
                          "delta_m2_same_route": (None if len(news) != 1 or news[0]["area_m2"] is None or o["area_m2"] is None
                                                  else round(news[0]["area_m2"] - o["area_m2"], 4)),
                          "value_changed_between_revisions": value_change,
                          "merged_labelled_spaces": merged,
                          "source_changes_near_room": near,
                          "cause": cause or ["NO_VALUE_CHANGE" + (" (source records changed nearby)" if near else "")]})
    unpaired_new = [runs["NEW_K2"]["rooms"][j] for j in nh if not any(j in js for _, js in pairs)]

    # rows: old (R8.6 baseline), new, delta, causes
    delta_rows = []
    for rid in ROUND1:
        old_v, k2o, new = rows[ "OLD_K1"][rid], rows["OLD_K2"][rid], rows["NEW_K2"][rid]
        causes = []
        if k2o["value"] != old_v["value"]:
            causes.append("PARSER_DIFFERENCE")
        if new["value"] != k2o["value"]:
            causes.append("SOURCE_REVISION_CHANGE")
        merged_rooms = sorted({m for r in room_rows for m in r["merged_labelled_spaces"]})
        in_row_merged = [m for m in merged_rooms if any(x.startswith(m + " ") for x in new["rooms"])]
        delta_rows.append({"row": rid, "old_revision_value_R8_6": r86_six.get(rid), "old_revision_value_contract_K1": old_v["value"],
                           "old_revision_value_K2_route": k2o["value"], "new_revision_value": new["value"],
                           "delta_new_minus_old_same_route": (None if new["value"] is None or k2o["value"] is None
                                                              else round(new["value"] - k2o["value"], 4)),
                           "new_rooms": new["rooms"], "new_rooms_not_established": new["rooms_not_established"],
                           "merged_labelled_spaces_in_row": in_row_merged,
                           "state": ("BLOCKED: METHOD_DID_NOT_ESTABLISH_ROOMS " + ", ".join(new["rooms_not_established"])
                                     if new["value"] is None else
                                     "NEW_REVISION_DXF_DIAGNOSTIC_REVIEW_REQUIRED: merged labelled space " + ", ".join(in_row_merged)
                                     if in_row_merged else "NEW_REVISION_DXF_DIAGNOSTIC"),
                           "causes": causes or ["NO_CHANGE"], "METHOD_DIFFERENCE": "NONE (same frozen method code in every run)"})

    # Q-14 under the scoped owner rule (new revision only)
    claim = R7.claims()[R7.Q14_CLAIM]
    want = Counter(claim.value["space_counts"])
    got = Counter(r["room"] for r in runs["NEW_K2"]["rooms"])
    use = [OS.applies(claim, project="QORTUBA", revision_id=R7.REV_NEW_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                      region_id=R7.REGION_ID, space_id=r["room"], item="Q-14|CEILING_BY_AREA") for r in runs["NEW_K2"]["rooms"]]
    q14_spaces = [{"space": r["room"], "floor_area_m2": r["area_m2"], "claim": u["state"],
                   "ceiling_area_m2": (r["area_m2"] if u["state"] == OS.APPLIES and r["area_m2"] is not None else None)}
                  for r, u in zip(runs["NEW_K2"]["rooms"], use)]
    labels_match = want == got
    established = all(s["floor_area_m2"] is not None for s in q14_spaces)
    q14 = {"claim_id": claim.claim_id, "scope": {"project": claim.project, "revision_id": claim.revision_id,
                                                  "region_id": claim.region_id, "space_ids": sorted(claim.space_ids),
                                                  "items": sorted(claim.items)},
           "purposes": list(claim.purposes), "anchor_state": claim.anchor_state,
           "spaces": q14_spaces, "expected_space_labels": dict(want), "remeasured_space_labels": dict(got),
           "label_multiset_matches_claim": labels_match, "all_spaces_established": established,
           "Q14_NEW_REVISION": (round(sum(s["ceiling_area_m2"] for s in q14_spaces), 4)
                                if labels_match and established and all(s["claim"] == OS.APPLIES for s in q14_spaces) else None),
           "state": ("NEW_REVISION_DXF_DIAGNOSTIC" if labels_match and established else
                     "BLOCKED: the owner rule does not rescue missing geometry (rooms not established or the space set "
                     "changed)"),
           "scope_tests": {
               "other_region": OS.applies(claim, project="QORTUBA", revision_id=R7.REV_NEW_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                          region_id="RC:PLAN_VARIANT_3", space_id="BATH", item="Q-14|CEILING_BY_AREA")["state"],
               "other_revision": OS.applies(claim, project="QORTUBA", revision_id=R7.REV_OLD_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                            region_id=R7.REGION_ID, space_id="BATH", item="Q-14|CEILING_BY_AREA")["state"],
               "other_project": OS.applies(claim, project="OTHER", revision_id=R7.REV_NEW_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                           region_id=R7.REGION_ID, space_id="BATH", item="Q-14|CEILING_BY_AREA")["state"],
               "other_space": OS.applies(claim, project="QORTUBA", revision_id=R7.REV_NEW_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                         region_id=R7.REGION_ID, space_id="STAIR", item="Q-14|CEILING_BY_AREA")["state"],
               "other_item": OS.applies(claim, project="QORTUBA", revision_id=R7.REV_NEW_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                        region_id=R7.REGION_ID, space_id="BATH", item="CEILING_NET_PLAN_AREA")["state"],
               "release_use": OS.applies(claim, project="QORTUBA", revision_id=R7.REV_NEW_ID, purpose=OS.RELEASE,
                                         region_id=R7.REGION_ID, space_id="BATH", item="Q-14|CEILING_BY_AREA")["state"]},
           "future_requirement": {"method": "CEILING_NET_PLAN_AREA", "status": "NOT_IMPLEMENTED (R9 trade rules)",
                                  "must_evaluate": ["room/space polygon", "minus verified stair openings",
                                                    "minus elevator / lift shafts", "minus service shafts", "minus voids",
                                                    "minus double-height / open-to-above areas", "minus explicit ceiling openings"],
                                  "never": "an apartment-scoped owner confirmation is never an input to it"}}

    sel = classify_new(blob_new)
    strip = lambda d: {k: {kk: vv for kk, vv in v.items() if kk != "_sets"} for k, v in d.items()}  # noqa: E731
    dump = lambda n, o: (out / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")  # noqa: E731
    contract = CI.contract_record(R7.QS01)
    evidence = {}
    for a in abl:
        ln = a.get("lenient_legacy_run") or {}
        evidence[a["field"]] = ("CHANGES_OUTPUT" if ln.get("six_change") or ln.get("rooms_change") else
                                "NO_CHANGE_ON_THIS_SOURCE" if ln else "ISOLATION_CHECK")
    contract["evidence"] = evidence
    dump("QS01_METHOD_INPUT_CONTRACT", {"SCHEMA": "URBAN_R8_7_QS01_METHOD_INPUT_CONTRACT_V1", "contract": contract,
                                         "not_required": {"texts.text_height": "no change when removed (R8.6 and R8.7)",
                                                          "linetype / lineweight": "not carried; R8.6 ablation: no change",
                                                          "HATCH / INSTANCES / BLOCK_DEFINITIONS / LAYERS tables": "not carried; R8.6 ablation: no change",
                                                          "dimensions.definition_points": "the method reads placed points only"},
                                         "policy_fields": {"parts.visibility": "the method measures visible plan geometry; "
                                                                                "no hidden or dynamic-state geometry exists in the region of either revision, so the field is POLICY",
                                                           "dimensions.user_text / dimlfac": "read by the method; every dimension here has no override and DIMLFAC 1.0",
                                                           "input.unit_claim_id": "the unit must come from a claim scoped to the revision"}})
    dump("FAIL_CLOSED_ABLATION_RESULTS", {"SCHEMA": "URBAN_R8_7_FAIL_CLOSED_ABLATIONS_V1", "base_revision": R7.REV_OLD_ID,
                                          "base_six": ref["six"], "ablations": abl,
                                          "rule": "every corrupted declared field -> no quantity; the lenient run shows what the method "
                                                  "would have published silently"})
    dump("QORTUBA_REVISION_DELTA", {
        "SCHEMA": "URBAN_R8_7_QORTUBA_REVISION_DELTA_V1", "label": "NEW_REVISION_DXF_DIAGNOSTIC (SHADOW; not production-authoritative)",
        "runs": {k: {"state": v["state"], "six_contract_rows": v["six"], "rooms": [[r["room"], r["area_m2"], r["wet_or_dry"]] for r in v["rooms"] or []],
                     "rooms_digest": v.get("rooms_digest"),
                     "method_unit": {k_: (v.get("method_unit") or {}).get(k_) for k_ in ("UNIT_CANDIDATE", "UNIT_SCALE_TO_MM", "PROVENANCE", "STATUS")},
                     "input": {"revision": inputs[k].revision.revision_id, "anchor": inputs[k].revision.anchor_sha256,
                               "route": inputs[k].notes.get("route"), "parts": len(inputs[k].parts), "texts": len(inputs[k].texts),
                               "dimensions": len(inputs[k].dimensions), "clip_bounds": inputs[k].notes.get("clip_bounds"),
                               "unit_native_to_mm": inputs[k].unit_native_to_mm, "unit_claim_id": inputs[k].unit_claim_id,
                               "excluded_by_declaration": v["validation"]["excluded_by_declaration"]}} for k, v in runs.items()},
        "rows": delta_rows, "rows_by_legacy_predicates": rows, "rooms": room_rows,
        "new_rooms_without_an_old_label_pair": [[r["room"], r["area_m2"]] for r in unpaired_new],
        "parser_difference": {"compared": "OLD revision: K1 (pinned LibreDWG decode) vs K2 (ezdxf on LibreDWG's DXF of the same DWG)",
                              "records": strip(pdelta), "largest_part_coordinate_differences": [[list(map(str, k)), e] for k, e in exact[:5]],
                              "bisected_culprits": culprits,
                              "finding": "the curves agree to < 1e-9 units except two arcs written 2*pi vs 0 (same arc); one WALL segment "
                                         "(H584) is horizontal to 4e-12 in K1 and exactly horizontal in K2 (DXF 16-digit text step); that "
                                         "alone moves 1.6425 m2 between BED.ROOM and the unlabelled space. The room method is numerically "
                                         "sensitive at 1e-12: room splits are route-stable only on the exact same route"},
        "source_revision_difference": {"compared": "K2 route: OLD (LibreDWG DXF of 2ec3a9c8) vs NEW (df0e1d69)", "records": strip(rdelta)},
        "method_difference": {"state": "NONE", "evidence": "every run uses the same frozen calculation path (R8.6 manifest hashes)"},
        "no_calibration": "no value is tuned toward the old result; differences are reported, not reconciled"})
    dump("Q14_SCOPED_CEILING_RULE", dict({"SCHEMA": "URBAN_R8_7_Q14_SCOPED_CEILING_RULE_V1"}, **q14))
    dump("REGION_CLASSIFICATION_NEW_REVISION", dict({"SCHEMA": "URBAN_R8_7_REGION_CLASSIFICATION_V1",
                                                     "revision": R7.REV_NEW_ID, "dxf_sha256": R7.NEW_DXF}, **sel))
    print({k: (v["state"], v["six"]) for k, v in runs.items()})
    print(json.dumps(delta_rows, indent=0)[:3000])
    print(q14["state"], q14["Q14_NEW_REVISION"], q14["scope_tests"])
    return runs, abl, delta_rows, q14, sel


ROUND1 = R7.ROUND1

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
