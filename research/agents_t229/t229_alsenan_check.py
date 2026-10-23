"""T-229 on the development villa: evaluates ALSENAN_BEAM_SUPPORT_INPUT.json (written by t229_census.py from the private
DXF; handles, band ids, areas and shares only) with BEAM_SUPPORT_V1 and writes summary.json + CENSUS.csv.
Runs without the private drawing (the regression test calls run()).

    python3 -I research/agents_t229/t229_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import beam_support as bs  # noqa: E402

INPUT = HERE / "ALSENAN_BEAM_SUPPORT_INPUT.json"
# Reference beam register (T-110, merged): one-span records through the planted columns (m3, 'P.C carried')
T110_THROUGH = {"B27": ("BM-GF-048", 3.7872), "B26": ("BM-GF-047", 3.9048)}


def _r(x, n=4):
    return None if x is None else round(x, n)


def run(path: Path = INPUT) -> dict:
    J = json.loads(path.read_text(encoding="utf-8"))
    P = J["pieces"]
    rows, gaps, ends, under = [], [], [], []
    for g in J["gaps"]:
        if g.get("cls_hint"):
            raise bs.Refused("census holds a non-collinear gap: " + g["a"])
        c = bs.classify_gap(g)
        rec = {**{k: g[k] for k in ("storey", "a", "b", "mark_a", "mark_b", "length_m", "width_m", "area_m2",
                                    "support_share", "carried_share", "other_beam_share", "depth_m",
                                    "edges_continuous")},
               "members": g["members"], **c}
        gaps.append(rec)
        rows.append({"storey": g["storey"], "where": "cut", "piece": g["a"] + " | " + g["b"],
                     "mark": f"{g['mark_a']}/{g['mark_b']}",
                     "member": ";".join(f"{h}:{k}" for h, k, _ in g["members"]) or "-", "class": c["cls"],
                     "status": c["status"], "m3_effect": _r(c.get("short_m3")), "bound_m3": _r(c.get("bound_m3")),
                     "note": c.get("reason", "")})
    for e in J["ends"]:
        c = bs.classify_end(e)
        rec = {**e, **c}
        ends.append(rec)
        rows.append({"storey": e["storey"], "where": f"end {e['end']}", "piece": e["piece"], "mark": e["mark"],
                     "member": ";".join(f"{h}:{k}" for h, k in e["members"]) or ";".join(
                         e.get("over_support", []) + e.get("side_beams", [])) or e.get("ext_member") or "-",
                     "class": c["cls"], "status": c["status"], "m3_effect": _r(c.get("short_m3")),
                     "bound_m3": _r(c.get("bound_m3")), "note": c.get("reason", "")})
    for t in J["through"]:
        if t["kind"] == "CARRIED_COLUMN":
            res = {"released": {"result": "PASS", "owner": "beam (carries the member; billed through under it)",
                                "double_m3": 0.0}}
        else:
            rel_basis = "FULL_INTERVAL" if t.get("released_column_m3") else "NONE"
            res = {"released": bs.joint_ownership(t["share"], t["A_m2"], t["depth_m"], rel_basis)}
            if t["ledger"]:
                res["ledger_t119"] = bs.joint_ownership(t["share"], t["A_m2"], t["depth_m"], "JOINT_LINE")
            if t["outline"] == "778":       # PC-2F: the T-220 record stops at the B7 soffit (Checker 15:52)
                res["record_t220"] = bs.joint_ownership(t["share"], t["A_m2"], t["depth_m"], "TO_THROUGH_SOFFIT")
        under.append({**t, "ownership": res})
        for state, o in res.items():
            rows.append({"storey": t["storey"], "where": f"under ({state})", "piece": t["piece"], "mark": t["mark"],
                         "member": f"{t['outline']}:{t['kind']}" + (f" {t['column_mark']}" if t.get("column_mark")
                                                                     else ""),
                         "class": o["result"], "status": "PASS" if o["result"] == "PASS" else "DOUBLE",
                         "m3_effect": _r(o.get("double_m3")), "bound_m3": None, "note": o["owner"]})

    # physical beams with a confirmed shortfall, released vs drawing-derived
    beams = {}
    def add(key, piece_ids, short, what):
        b = beams.setdefault(key, {"pieces": set(), "short_m3": 0.0, "what": []})
        b["pieces"].update(piece_ids)
        b["short_m3"] += short
        b["what"].append(what)
    for g in gaps:
        if g["status"] == "BEAM_SHORT":
            add(f"{g['storey']} {g['mark_a']} ({g['a'].split(':')[1].split('.')[0]})", [g["a"], g["b"]],
                g["short_m3"], f"{g['cls']} {g['short_m3']:.4f}")
    for e in ends:
        if e["status"] == "BEAM_SHORT":
            add(f"{e['storey']} {e['mark']} ({e['piece'].split(':')[1].split('.')[0]})", [e["piece"]], e["short_m3"],
                f"{e['cls']} {e['short_m3']:.4f}")
    beam_rows = []
    carried_cut = {x for g in gaps if g["cls"] == "CUT_AT_CARRIED" for x in (g["a"], g["b"])}
    for k, b in sorted(beams.items()):
        rel = sum(P[p]["route_g_m3"] or 0.0 for p in b["pieces"] if P[p]["route_g"] == "RELEASED")
        held = sorted(p for p in b["pieces"] if P[p]["route_g"] != "RELEASED")
        held_exp = round(sum(P[p]["route_g_held_exposure_m3"] or 0.0 for p in held), 4) if held else None
        # a route G hold 'unlabelled span across support' is resolved only where the 'support' is a member the beam
        # carries (the beam is one member with one label); a hold at a real support stays HELD
        resolved = all(p in carried_cut for p in held)
        beam_rows.append({"beam": k, "pieces": sorted(b["pieces"]), "released_m3": round(rel, 4),
                          "route_g_held_pieces": held, "route_g_held_m3": held_exp,
                          "held_resolved_here": bool(held) and resolved,
                          "short_m3": round(b["short_m3"], 4),
                          "drawing_derived_m3": round(rel + (held_exp or 0.0) + b["short_m3"], 4)
                          if (not held or resolved) else None,
                          "status": "DRAWING-CONFIRMED" if (not held or resolved) else
                                    "HELD (route G hold at a real support stays; the short adds to whichever span)",
                          "causes": b["what"]})
    def tot(seq, key="short_m3", st=None, cls=None):
        return round(sum(x[key] or 0.0 for x in seq if (st is None or x["status"] == st) and
                         (cls is None or x["cls"] in cls)), 4)
    summary = {
        "schema": "T229_ALSENAN_SUMMARY_V1", "module": bs.SCHEMA, "source_dxf_sha256": J["source_dxf_sha256"],
        "counts": J["counts"], "rings_not_cut_checked": J["rings"],
        "census": {"cuts": len(gaps), "ends": len(ends), "under": len(under), "rows": len(rows),
                   "by_class": _count(rows)},
        "short": {
            "cut_at_carried_m3": tot(gaps, cls=("CUT_AT_CARRIED",)),
            "beside_support_m3": tot(gaps, cls=("SUPPORT_CUT_BESIDE",), st="BEAM_SHORT"),
            "end_short_at_carried_m3": tot(ends, cls=("END_SHORT_AT_CARRIED",)),
            "end_short_of_member_m3": tot(ends, cls=("END_SHORT_OF_MEMBER",)),
            "end_short_oblique_m3": tot(ends, cls=("END_SHORT_OBLIQUE",)),
        },
        "held": {"gaps": [{"a": g["a"], "b": g["b"], "cls": g["cls"], "bound_m3": _r(g.get("bound_m3")),
                           "plan_m2": _r(g["beside_m2"] if g["cls"] == "SUPPORT_CUT_BESIDE" else g["area_m2"])}
                          for g in gaps if g["status"] == "HELD"],
                 "ends": [{"piece": e["piece"], "cls": e["cls"]} for e in ends if e["status"] == "HELD"]},
        "double": {
            "released_m3": round(sum(u["ownership"]["released"]["double_m3"] or 0.0 for u in under), 4),
            "ledger_t119_m3": round(sum(u["ownership"].get("ledger_t119", {}).get("double_m3") or 0.0
                                        for u in under), 4),
            "lines": [{"outline": u["outline"], "piece": u["piece"], "mark": u["mark"], "column": u.get("column_mark"),
                       "share": u["share"], "released_column_m3": u.get("released_column_m3"),
                       "ledger": [l["id"] for l in u["ledger"]],
                       **{s: {"result": o["result"], "double_m3": _r(o["double_m3"])} for s, o in u["ownership"].items()}}
                      for u in under]},
        "beams": beam_rows,
        "t110_compare": {m: {"member": T110_THROUGH[m][0], "t110_m3": T110_THROUGH[m][1],
                             "this_m3": next((b["drawing_derived_m3"] for b in beam_rows if f" {m} " in b["beam"]
                                              and b["beam"].startswith("GF")), None)}
                         for m in T110_THROUGH},
        "gaps": gaps, "ends": [e for e in ends if e["cls"] not in ("END_AT_SUPPORT", "END_AT_BEAM",
                                                                    "END_AT_JUNCTION_OWNER")],
    }
    summary["short"]["total_confirmed_m3"] = round(sum(summary["short"].values()), 4)
    return {"summary": summary, "rows": rows}


def _count(rows):
    out = {}
    for r in rows:
        out[r["class"]] = out.get(r["class"], 0) + 1
    return dict(sorted(out.items()))


def write(res):
    (HERE / "summary.json").write_text(json.dumps(res["summary"], indent=1) + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(res["rows"][0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(res["rows"])
    (HERE / "CENSUS.csv").write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    res = run()
    if "--write" in sys.argv:
        write(res)
    s = res["summary"]
    print(json.dumps({k: s[k] for k in ("census", "short", "double", "t110_compare")}, indent=1))
    for b in s["beams"]:
        print(b["beam"], b["released_m3"], b["route_g_held_m3"], b["short_m3"], b["drawing_derived_m3"], b["causes"])
