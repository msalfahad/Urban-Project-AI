"""T-220 development-villa check: the three planted columns and the five released storey lines with no member.

Reads ALSENAN_PLANTED_INPUT.json (readings by handle / BOQ id, no coordinates) and writes summary.json.
    python3 -I research/agents_t220/t220_alsenan_check.py [--write]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import planted_columns as pcm  # noqa: E402


def load():
    return json.loads((HERE / "ALSENAN_PLANTED_INPUT.json").read_text(encoding="utf-8"))


def column(inp, p, basis_key):
    lv = inp["levels"]
    top = lv[p["slab_top_key"]]
    sup = p["support"]
    return pcm.PlantedColumn(
        id=p["id"], storey=p["storey"],
        sources=[pcm.Source(*s) for s in p["sources"]],
        support=pcm.Member(sup["id"], sup["depth_m"], sup[basis_key]),
        support_top=lv["GF_roof_slab_top"]["value"] if p["storey"] == "1F" else lv["1F_roof_slab_top"]["value"],
        slab_top=top["value"], slab_top_upper=top.get("upper"), slab_t=lv["slab_t"]["value"],
        top_members=[pcm.Member(m[0], m[1], m[2]) for m in p["top_members"]],
        interval=lv[p["interval_key"]], ledger_joint_m3=p["ledger_joint_m3"], bars=p["bars"])


def run():
    inp = load()
    out = {"schema": "T220_SUMMARY_V1", "planted": [], "released_lines": []}
    for p in inp["planted"]:
        ref = pcm.evaluate(column(inp, p, "basis_reference"))
        rel = pcm.evaluate(column(inp, p, "basis_released"))
        out["planted"].append({"id": p["id"], "t119_id": p["t119_id"], "storey": p["storey"],
                               "start": p["start_outline"], "own": p["own_outline"],
                               "on_reference_beam_register": ref, "on_released_route_g": rel})
    req = inp["required_sheets_for_absence"]
    for r in inp["released_lines_without_member"]:
        searched = req[:len(r["searched"])]
        ex = pcm.classify_existence(r["drawn_on"], searched, req)
        out["released_lines"].append({"line": r["line"], "storey": r["storey"], "released_m3": r["released_m3"],
                                      "existence": ex["class"], "state": pcm.released_line_state(r["released_m3"], ex),
                                      "evidence": r["searched"], "roof_over": r["roof_over"]})
    rl = out["released_lines"]
    out["totals"] = {
        "released_without_member_m3": round(sum(r["released_m3"] for r in rl), 6),
        "not_drawn_count": sum(r["existence"] == "NOT_DRAWN" for r in rl),
    }
    return out


if __name__ == "__main__":
    res = run()
    txt = json.dumps(res, indent=1, ensure_ascii=False, default=float) + "\n"
    if "--write" in sys.argv:
        (HERE / "summary.json").write_text(txt, encoding="utf-8")
    for p in res["planted"]:
        a, b = p["on_reference_beam_register"], p["on_released_route_g"]
        print(p["id"], a["status"], "solid", a["solid_m3"], "bound", a["solid_upper_bound_m3"], "owner",
              a["owner_method"].get("column_m3", a["owner_method"].get("column_m3_upper")),
              [(o["pair"], o["result"], o.get("beam_short_m3") or o.get("double_m3")) for o in b["ownership"] + a["ownership"]
               if o["result"] != "PASS"])
    print(res["totals"])
