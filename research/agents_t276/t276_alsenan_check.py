"""T-276 development-villa ledger (Alsenan; not an accuracy claim): buried ground-beam faces on TRACED lengths.

Built ONLY from committed values-only inputs:
- research/agents_t276/ALSENAN_FACE_TRACE.json (this task, t276_extract.py on Drive "Alsenan chalet project" /
  "ST7757 dxf.dxf" sha 9f9d1179; the 29 T-242 panels reproduced): every boundary piece of the ground-beam solid with
  its owner, face and the drawn face LINE handle;
- the T-263 run inputs (research/agents_t263/t263_alsenan_check.py build_runs: depths from T-242 / T-253, tops T-214,
  panel states), neck sections T-205 (LEDGER_T205.csv).

Repeat: `python3 -I research/agents_t276/t276_alsenan_check.py [--write]`.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import buried_faces_v2 as F  # noqa: E402

_spec = importlib.util.spec_from_file_location("t263", ROOT / "research/agents_t263/t263_alsenan_check.py")
T263 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T263)
W = F.W
LIFT_COLUMNS = {"COL:1EC", "COL:1EF", "COL:1F2", "COL:1F5"}   # inside the p.14 lift system (T-219 / T-263: lift necks)
T263_DC_M2 = 35.404365                                         # T-263 summary, MERGED c0ab564d


def panel_state(pid):
    return T263.panel_state([pid])


def main(write=False):
    trace = json.loads((HERE / "ALSENAN_FACE_TRACE.json").read_text(encoding="utf-8"))
    runs, gi = T263.build_runs()
    R = {r["id"]: r for r in runs}
    band_of = {sid: v["band"] for sid, v in trace["spans"].items()}
    assert set(R) == set(trace["spans"]), "trace spans differ from the T-263 runs"
    arcs = {a["arc_band"]: a for a in gi["arc_bands"]}

    def span_member(sid):
        r = R[sid]
        return {"id": sid, "band": band_of[sid], "depth": r["depth"], "depth_range": r["depth_range"],
                "top": r["top"], "slab_t": r["slab_t"], "natural_ground": r["natural_ground"]}

    def arc_member(aid):
        part = arcs[aid]["part"]
        if part == "MAIN":   # T-253 R-GB-DATUM-1: ring at the N.G. datum, D 0.95 (the 11 main exterior DC faces' basis)
            return {"depth": 0.95, "depth_range": None, "top": 0.95, "slab_t": T263.SLAB_T, "natural_ground": 0.0}
        return {"depth": None, "depth_range": None, "top": 0.25, "slab_t": T263.SLAB_T, "natural_ground": 0.0}

    def piece_member(pid):
        p = trace["pieces"][pid]
        return F.piece_member(p["in_bands"], [span_member(s) for s in p["touches_spans"]])

    rows, closures, per_side = [], [], {}
    for bd in trace["boundaries"]:
        pieces = [f for f in trace["faces"] if f["boundary"] == bd["boundary"]]
        closures.append((bd["boundary"], F.check_closure(bd["boundary"], bd["length_m"], pieces)))
        ps = panel_state(bd["boundary"]) if bd["kind"] == "PANEL" else None
        for f in pieces:
            k, m = f["member_kind"], f["member"]
            el = f"{m} | {bd['boundary']}"
            if k == "COLUMN":
                rows.append(W.Row(el, "NECK", f"column face in the beam zone on {bd['boundary']}", "m", f["length_m"],
                                  W.HELD, "neck face (T-205 neck = footing top -> ground-beam top): neck line only",
                                  {"length_m": f["length_m"]},
                                  "NECK_HEIGHT_HELD (Q-21 C); never in the ground-beam line"))
                continue
            if k == "SPAN":
                mem = span_member(m)
                face = "end face" if f["face"] == "END" else f"side {f['face']} (LINE {f.get('face_line_handle')})"
                per_side.setdefault((m, f["face"]), 0.0)
                per_side[(m, f["face"])] += f["length_m"]
            elif k == "PIECE":
                mem = piece_member(m)
                face = "junction / GAP piece face"
            elif k == "ARC":
                mem = arc_member(m)
                face = f"{f['face'].lower()} face (ARC {f.get('arc_handle')})"
            else:
                mem = {}
                face = "lift ring face"
            row = F.face_row(el, k, face, bd["kind"], ps, f["length_m"], mem)
            if k == "PIECE" and row.status == W.HELD and mem.get("why"):
                row.held_why = mem["why"]
            rows.append(row)

    # per span side: traced earth-face length vs the run length T-263 used
    side_cmp = []
    t263 = {}
    with open(ROOT / "research/agents_t263/LEDGER_T263.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["member"] == "GROUND_BEAM" and r["face"].startswith("side") and r["status"] == W.DC:
                t263[(r["element"], r["face"][5])] = float(r["qty"])
    for (sid, side), L in sorted(per_side.items()):
        if side not in ("A", "B"):
            continue
        side_cmp.append({"span": sid, "side": side, "run_L": R[sid]["L"], "traced_L": round(L, 4),
                         "covered_L": round(R[sid]["L"] - L, 4), "t263_m2": t263.get((sid, side)),
                         "beyond_face_line": json.dumps(trace["span_side_cover"][f"{sid}|{side}"], sort_keys=True)})

    # necks: beam-zone deduction from the T-263 'perimeter x neck height' reading
    def depth_of(kind, oid):
        if kind == "SPAN":
            return span_member(oid)["depth"]
        if kind == "PIECE":
            return piece_member(oid)["depth"]
        if kind == "ARC":
            return arc_member(oid)["depth"]
        return None
    nl = {r["outline_handle"]: r for r in csv.DictReader(open(ROOT / "research/agents_t205/LEDGER_T205.csv",
                                                              encoding="utf-8"))}
    necks = []
    for cid, c in sorted(trace["column_contacts"].items()):
        n = nl[c["foundation_plan_outline"]]
        rng = tuple(float(x) for x in n["section_range_m2"].strip("()").split(","))
        if cid in LIFT_COLUMNS:
            necks.append({"column": cid, "neck": f"{n['type']} {n['outline_handle']}", "status": W.EXCLUDED,
                          "why": "lift neck inside the p.14 sheet system (T-219)"})
            continue
        parts_of = set()
        for p in c["parts"]:
            if p["kind"] == "SPAN":
                parts_of.add(R[p["with"]]["class"].split()[-1])
            elif p["kind"] == "PIECE":
                parts_of |= {R[s]["class"].split()[-1] for s in trace["pieces"][p["with"]]["touches_spans"]}
            elif p["kind"] == "ARC":
                parts_of.add(arcs[p["with"]]["part"])
        part_main = parts_of == {"MAIN"}
        zone_top = T263.TOP["MAIN"]
        ded, basis, why = F.neck_beam_zone_deduction(
            cid, c["parts"], zone_top=zone_top, slab_t=T263.SLAB_T, natural_ground=0.0,
            member_depth=depth_of) if part_main else (None, "", "ANNEX_DEPTH_CONFLICT (D-35): beam-zone depths held")
        plan_differs = abs(c["plan_m2"] - rng[1]) > 1e-6 and abs(c["plan_m2"] - rng[0]) > 1e-6
        necks.append({"column": cid, "neck": f"{n['type']} {n['outline_handle']}", "gb_plan_m2": c["plan_m2"],
                      "neck_section_m2": n["section_range_m2"], "gb_plan_perimeter_m": c["perimeter_m"],
                      "gb_plan_differs_from_section": plan_differs,
                      "deduction_m2": None if ded is None else round(ded, 6), "basis": basis,
                      "status": W.DC if ded is not None and not plan_differs else W.HELD,
                      "why": why or ("GB_PLAN_SECTION_DIFFERS: the ground-beam plan outline is not the scheduled "
                                     "foundation section" if plan_differs else "")})


    gb = [r for r in rows if r.member == "GROUND_BEAM"]
    dc = [r for r in gb if r.status == W.DC]
    held = [r for r in gb if r.status == W.HELD]
    summary = {
        "method": F.METHOD,
        "sources": {"trace": "ALSENAN_FACE_TRACE.json (ST7757 dxf.dxf 9f9d1179)", "t263": "c0ab564d",
                    "t242": "9455a63d", "t253": "dff9cb79", "t205": "5f40dfdb"},
        "boundaries": len(closures), "boundary_length_m": round(sum(c[1] for c in closures), 4),
        "gb_faces_drawing_confirmed": {"pieces": len(dc), "m2": W.measured_total(dc)},
        "gb_faces_held": {"pieces": len(held), "length_m": round(sum(r.readings["length_m"] for r in held), 4)},
        "gb_faces_excluded_above_ground": {"pieces": sum(1 for r in gb if r.status == W.EXCLUDED),
                                           "length_m": round(sum(r.readings["length_m"] for r in gb
                                                                 if r.status == W.EXCLUDED), 4)},
        "neck_faces_in_beam_zone_m": round(sum(r.qty for r in rows if r.member == "NECK"), 4),
        "lift_ring_faces_excluded_m": round(sum(r.readings["length_m"] for r in rows if r.member == "LIFT_PIT"), 4),
        "t263_dc_m2": T263_DC_M2,
        "neck_deduction": {"dc_necks": sum(1 for n in necks if n["status"] == W.DC),
                           "dc_m2": round(sum(n["deduction_m2"] for n in necks if n["status"] == W.DC), 6),
                           "held_necks": sum(1 for n in necks if n["status"] == W.HELD),
                           "excluded_lift": sum(1 for n in necks if n["status"] == W.EXCLUDED)},
    }
    by = {}
    for r in dc:
        key = r.element.split(" | ")[0]
        kind = "ARC" if key.startswith("ARC:") else ("PIECE" if key.startswith("PIECE:") else
                                                     ("INTERIOR" if R.get(key, {}).get("class", "").startswith("INTERIOR")
                                                      else "EXTERIOR MAIN"))
        by.setdefault(kind, [0, 0.0])
        by[kind][0] += 1
        by[kind][1] = W.r6(by[kind][1] + r.qty)
    summary["gb_faces_drawing_confirmed"]["by_kind"] = by
    if write:
        with open(HERE / "LEDGER_T276.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["element", "member", "face", "unit", "qty", "status", "basis",
                                               "readings", "held_why"])
            w.writeheader()
            for r in rows:
                d = r.as_dict()
                d["readings"] = json.dumps(d["readings"], sort_keys=True)
                w.writerow(d)
        with open(HERE / "SIDE_COMPARE_T276.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["span", "side", "run_L", "traced_L", "covered_L", "t263_m2",
                                               "beyond_face_line"])
            w.writeheader()
            w.writerows(side_cmp)
        with open(HERE / "NECK_ZONE_T276.csv", "w", newline="", encoding="utf-8") as fh:
            keys = ["column", "neck", "gb_plan_m2", "neck_section_m2", "gb_plan_perimeter_m",
                    "gb_plan_differs_from_section", "deduction_m2", "basis", "status", "why"]
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for n in necks:
                w.writerow({k: n.get(k) for k in keys})
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rows, side_cmp, necks, summary


if __name__ == "__main__":
    _, _, _, s = main(write="--write" in sys.argv)
    print(json.dumps(s, indent=1, sort_keys=True))
