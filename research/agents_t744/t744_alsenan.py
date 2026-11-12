"""T-744 read-only census: which spaces, and so which candidate lines, change when fixture blocks are typed by their
CONTENT (WET_ROOM_EVIDENCE_V2, engine/source/wet_room_evidence.py plan_evidence_v2 / classify_v2) instead of their
name (V1). Runs ARCH_TAKEOFF_V2.11 (the step of the candidate chain that reads WET_ROOM_EVIDENCE_V1 through
arch_v211.wet_classes) on the architectural DXF with the chain's own project facts (research/agents_t131 facts: the
T-010 sanitary reading), keeps the room builder's capture, and classifies every classed space twice: V1 exactly as the
chain does, V2 with the block table of the same drawing. Then lists every line of the candidate line index whose
element names a space whose (class, reason, basis) differs.

    bash scripts/agent_env.sh run --tree <tree> research/agents_t744/t744_alsenan.py <P7757.dxf> --out <scratch>.json \
        [--line-index research/agents_t729/out/LINE_INDEX_V3_0_75.json]

Output: block names, DXF handles, engine room ids, classes and line ids only: no client data."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t131"))

KEYS = ("class", "reason", "basis")


def block_types(doc, max_depth=8):
    """{block name: flattened entity types} of every block definition (nested INSERTs expanded)."""
    memo = {}

    def flat(name, depth):
        if name in memo:
            return memo[name]
        if depth > max_depth or name not in doc.blocks:
            return []
        out = []
        for e in doc.blocks[name]:
            if e.dxftype() == "INSERT":
                out += flat(e.dxf.name, depth + 1)
            else:
                out.append(e.dxftype())
        memo[name] = out
        return out
    return {b.name: flat(b.name, 0) for b in doc.blocks if not b.name.startswith("*")}


def v2_classes(rooms, cap, sanitary_by_room, btypes):
    """arch_v211.wet_classes with plan_evidence_v2 / classify_v2 (same inputs, same skips)."""
    from engine.source import arch_rooms as AR
    from engine.source import arch_v211 as AV
    from engine.source import wet_room_evidence as W
    out = {}
    for r in rooms:
        if r["class"] not in AV.CLASSED:
            continue
        c = cap.get(r.get("region_id")) or {}
        if "ents" not in c:
            out[r["room_id"]] = {"class": AV.HELD, "reason": "REGION_NOT_CAPTURED", "basis": "-"}
            continue
        geo = None
        if r["codes"] and r.get("label_source") not in ("TEXT",) and \
                all(AR.LEX[x][2] in W.NO_FINISH_KINDS for x in r["codes"]):
            geo = AR.LEX[r["codes"][0]][2]
        ev = W.plan_evidence_v2(r["polygon"], c["ents"], c["roles"], c["unit_m"], r.get("hole_polygons") or (),
                                block_types=btypes)
        san = None
        if sanitary_by_room is not None and r["room_id"] in sanitary_by_room:
            san = [{"kind": k} for k in sanitary_by_room[r["room_id"]]]
        rec = W.classify_v2(ev, san, space_kind=geo)
        out[r["room_id"]] = {"class": rec["class"], "reason": rec["reason"], "basis": rec["basis"],
                             "coordination_checks": rec["coordination_checks"], "labels": ev["labels"]["codes"],
                             "label_source": ev["labels"]["source"],
                             "plan_fixtures": sorted({x["kind"] for x in ev["fixtures"]}),
                             "plan_fixture_blocks": len(ev["fixtures"]),
                             "unconfirmed": sorted(x["kind"] for x in ev["fixtures_unconfirmed"]),
                             "readings": [{k: x[k] for k in ("id", "name", "kind", "content", "verdict")}
                                          for x in ev["fixture_readings"]]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--line-index", default=str(ROOT / "research/agents_t729/out/LINE_INDEX_V3_0_75.json"))
    a = ap.parse_args(argv)
    import ezdxf
    from alsenan_v30_run import PID, facts as t131_facts
    from engine.source import arch_v211 as AV
    from engine.source import wet_room_evidence as W
    from tools import urban_boq_m9 as M

    doc = ezdxf.readfile(a.drawing)
    btypes = block_types(doc)
    kept = {}
    o_capture = AV.capture

    @contextmanager
    def capture():
        with o_capture() as cap:
            kept["cap"] = cap
            yield cap
    AV.capture = capture
    try:
        f = t131_facts(Path(a.drawing).name)
        _boq, arch, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.11", facts=f, project_id=PID)
    finally:
        AV.capture = o_capture
    cap = kept["cap"]
    san = f.get("sanitary_by_room")
    chain = (arch.get("v211") or {}).get("classes") or {}
    v1 = AV.wet_classes(arch["rooms"], cap, san)
    v2 = v2_classes(arch["rooms"], cap, san, btypes)
    v1_equals_chain = all({k: v1[r][k] for k in KEYS} == {k: chain[r][k] for k in KEYS} for r in chain) and \
        set(v1) == set(chain)

    # every fixture-named insert of the captured plans, read by content (the tag inventory by handle)
    floor_of = {g.get("region_id"): g.get("floor") for g in arch.get("regions") or ()}
    inv, seen = [], set()
    for rid, c in cap.items():
        for i in (c.get("ents") or {}).get("inserts") or ():
            rd = W.fixture_reading(i, btypes)
            if rd["kind"] is None and rd["verdict"] != W.TAG:
                continue
            h = str(i["id"]).split(":")[1] if str(i["id"]).startswith("I:") else str(i["id"])
            if (rid, h) in seen:
                continue
            seen.add((rid, h))
            room = None
            for r in arch["rooms"]:
                if r.get("region_id") == rid and W._pip(i["x"], i["y"], r["polygon"]):
                    room = r["room_id"]
            inv.append({"region": rid, "floor": floor_of.get(rid), "handle": h, "block": i["name"],
                        "layer": i.get("layer"), "kind_by_name": rd["kind"], "content": rd["content"],
                        "verdict": rd["verdict"], "room_id": room,
                        "content_types": dict(Counter(btypes.get(i["name"]) or []))})

    diffs = []
    for r in sorted(set(v1) | set(v2)):
        a1, a2 = v1.get(r) or {}, v2.get(r) or {}
        fx1 = (a1.get("plan_fixtures") or [])
        if {k: a1.get(k) for k in KEYS} != {k: a2.get(k) for k in KEYS} or fx1 != a2.get("plan_fixtures") or \
                a1.get("labels") != a2.get("labels") or a1.get("coordination_checks") != a2.get("coordination_checks"):
            diffs.append({"room_id": r, "v1": {k: a1.get(k) for k in KEYS + ("labels", "plan_fixtures",
                                                                              "coordination_checks")},
                          "v2": {k: a2.get(k) for k in KEYS + ("labels", "label_source", "plan_fixtures",
                                                              "unconfirmed", "coordination_checks")},
                          "class_or_reason_or_basis_changed": {k: a1.get(k) for k in KEYS} !=
                          {k: a2.get(k) for k in KEYS}})
    changed_rooms = {d["room_id"] for d in diffs if d["class_or_reason_or_basis_changed"]}
    li = json.loads(Path(a.line_index).read_text(encoding="utf-8"))
    lines = [ln for ln in li["lines"] if any(r in (ln.get("element_id") or "") for r in changed_rooms)]
    res = {"method_v1": W.METHOD_ID, "method_v2": W.METHOD_ID_V2, "chain_method": "ARCH_TAKEOFF_V2.11",
           "v1_reproduces_chain_classes": v1_equals_chain, "spaces_classed": len(v1),
           "class_counts_v1": dict(Counter(x["class"] for x in v1.values())),
           "class_counts_v2": dict(Counter(x["class"] for x in v2.values())),
           "plan_fixtures_in_spaces_v1": dict(Counter(k for x in v1.values() for k in x["plan_fixtures"])),
           "plan_fixtures_in_spaces_v2": dict(Counter(k for x in v2.values() for k in x["plan_fixtures"])),
           "fixture_named_inserts": [x for x in inv if x["kind_by_name"]],
           "text_only_blocks_any_name": len([x for x in inv if not x["kind_by_name"]]),
           "room_builder_label_sources": dict(Counter(str(r.get("label_source")) for r in arch["rooms"])),
           "inventory_verdicts": dict(Counter(x["verdict"] for x in inv if x["kind_by_name"])),
           "spaces_whose_evidence_differs": diffs,
           "spaces_whose_class_reason_basis_changed": sorted(changed_rooms),
           "line_index": {"candidate": li.get("candidate_version"), "lines": len(li["lines"]),
                          "lines_naming_a_changed_space": [ln["line_id"] for ln in lines]}}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("v1_reproduces_chain_classes", "spaces_classed", "class_counts_v1",
                                           "class_counts_v2", "plan_fixtures_in_spaces_v1",
                                           "plan_fixtures_in_spaces_v2", "inventory_verdicts",
                                           "room_builder_label_sources",
                                           "spaces_whose_class_reason_basis_changed")}, indent=1))
    print("spaces with any evidence difference:", len(diffs), "| lines naming a changed space:",
          len(res["line_index"]["lines_naming_a_changed_space"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
