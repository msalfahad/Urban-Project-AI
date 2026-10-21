"""T-097 read-only run: route G (frozen, conventions V6, completeness on) vs CONCRETE_LEDGER_V3 on one structural DXF.

    python3 -I research/agents_t097/run_v3.py ST.dxf OUT.json [--conventions CONV.json] [--ring-rule FAMILY:MARK:STOREY:basis]

Prints per concrete key (tests/alsenan/T001B_KEY_MAP.json) the released sum / held count of the frozen structural
lines and of the V3 lines, and writes OUT.json: beam / ring / upstand / neck records and the line diff (marks, band
ids, lengths and volumes only; no drawing coordinates). Writes only OUT.json. Names no project, sheet or layer."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import concrete_ledger_v3 as V3      # noqa: E402
from tools import alsenan_keymap as K                    # noqa: E402
from tools import urban_boq_m2 as M2                     # noqa: E402
from tools import urban_boq_m9 as M9                     # noqa: E402


def by_key(lines, km, ref):
    rows, _ = K.engine_rows(lines, None, km)
    refs = {r["key"]: r["qty"] for r in K.reference_rows(ref, km)}
    agg = defaultdict(lambda: {"released_m3": 0.0, "released_lines": 0, "held_lines": 0})
    for r in rows:
        if r["key"] and r["key"].startswith("CONC."):
            a = agg[r["key"]]
            if r["status"] == "RELEASED":
                a["released_m3"] += r["qty"]
                a["released_lines"] += 1
            else:
                a["held_lines"] += 1
    return {k: dict(v, released_m3=round(v["released_m3"], 4), reference_m3=round(refs[k], 4))
            for k, v in sorted(agg.items())}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    conv = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
    ring = None
    if "--conventions" in argv:
        i = argv.index("--conventions")
        conv = argv[i + 1]
        del argv[i:i + 2]
    if "--ring-rule" in argv:
        i = argv.index("--ring-rule")
        fam, mk, st, basis = argv[i + 1].split(":", 3)
        ring = {"family": fam, "mark": mk, "storey": st, "basis": basis}
        del argv[i:i + 2]
    dxf, out = argv[:2]
    R = M2.compute([dxf], conventions=conv, route="G", completeness=True)
    v3 = V3.measure(R, ring_rule=ring, dxf_path=dxf)
    R3 = dict(R, items=V3.apply(R, v3))
    km = json.loads((ROOT / "tests/alsenan/T001B_KEY_MAP.json").read_text(encoding="utf-8"))
    ref = json.loads((ROOT / "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json").read_text(encoding="utf-8"))
    L0, L3 = M9.structural_lines(R), M9.structural_lines(R3)
    k0, k3 = by_key(L0, km, ref), by_key(L3, km, ref)
    ids0, ids3 = {ln["line_id"]: ln for ln in L0}, {ln["line_id"]: ln for ln in L3}

    def brief(ln):
        loc = ln.get("location") or {}
        return {"item_code": ln["item_code"], "element": loc.get("element_id"), "state": ln["evidence_state"],
                "m3": ln.get("measured_net")}
    diff = {"removed": [brief(ids0[k]) for k in ids0 if k not in ids3],
            "added": [brief(ids3[k]) for k in ids3 if k not in ids0],
            "changed": [{"v1": brief(ids0[k]), "v3": brief(ids3[k])} for k in ids0 if k in ids3 and
                        (brief(ids0[k]) != brief(ids3[k]) or ids0[k].get("bounded_range") != ids3[k].get("bounded_range"))],
            "unchanged": sum(1 for k in ids0 if k in ids3 and brief(ids0[k]) == brief(ids3[k]))}
    beam_items = [{"item_id": i["item_id"], "category": i["category"], "base": i["base"], "blocker": i["blocker"],
                   "mark_source": i["source"].split("; mark ")[-1] if "; mark " in i["source"] else None,
                   "dims": {k: i["dimensions"].get(k) for k in ("width_m", "length_m", "net_plan_m2", "depth_m",
                                                                  "basis", "mark", "section", "w_m", "h_m")
                            if i["dimensions"].get(k) is not None}} for i in v3["beam_items"]]
    rep = {"method": V3.METHOD, "lines_frozen": len(L0), "lines_v3": len(L3), "by_key_frozen": k0, "by_key_v3": k3,
           "sheets": v3["sheets"], "supersedes": v3["supersedes"], "beam_items": beam_items,
           "rings": [{k: v for k, v in r.items() if k not in ("formula",)} for r in v3["rings"]],
           "sections": v3["sections"], "upstands": v3["upstands"], "not_present": v3["not_present"],
           "neck_items": [{"item_id": i["item_id"], "blocker": i["blocker"]} for i in v3["neck_items"]],
           "side_effects": v3["side_effects"], "line_diff": diff}
    Path(out).write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"by_key_frozen": k0, "by_key_v3": k3, "line_diff_counts": {
        "removed": len(diff["removed"]), "added": len(diff["added"]), "changed": len(diff["changed"]), "unchanged": diff["unchanged"]},
        "sheets": [{k: s.get(k) for k in ("sheet", "storey", "state", "bands_v1", "bands_v2")} for s in v3["sheets"]],
        "side_effects": len(v3["side_effects"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
