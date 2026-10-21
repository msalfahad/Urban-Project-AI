"""T-087 read-only Alsenan run: tile count per room (TILE_COUNT_V1) on the ARCH_TAKEOFF_V2.9 rooms, and the census of
printed tile sizes in the architectural DXF texts (SHX Arabic decoded).

Released BOQ result: every room HELD TILE_SIZE_NOT_GIVEN (the drawings print no tile size; no project data file; no
owner value). The CANDIDATE columns lay each owner-approved size (UP-CER-010: 60x60, 120x60, 160x80) with the owner
joint (Q-42: 1 mm, every room here is a closed room inside the building) to show what the count would be once a size
is given, with no offcut reuse and, as an owner-question scenario, with offcuts of 0.20 m or more reused in the room: they are not BOQ values and are never summed into a released line.
Usage (Python 3.11, the drawing outside the clone):
    python3 -I research/agents_t087/alsenan_tile_count.py --v29 <scratch>/v29.pkl --dxf <P7757.dxf> --out <dir>
Writes only to --out. Engine room ids, English / Arabic room labels, areas and counts only (no client data)."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import tile_count as T  # noqa: E402

REUSE_SCENARIO_M = 0.20     # owner-question scenario only (offcuts >= 0.20 m reused inside the same room)
SIZES = {"60x60": (0.6, 0.6), "120x60": (1.2, 0.6), "160x80": (1.6, 0.8)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    boq, arch, _ = pickle.load(open(a.v29, "rb"))
    floor_lines = {}
    for ln in boq["lines"]:
        if ln["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"):
            floor_lines[ln["location"]["room_id"]] = ln
    rows, recs = [], []
    for room in arch["rooms"]:
        ln = floor_lines.get(room["room_id"])
        if ln is None:
            continue
        geo = {"polygon": room["polygon_m"], "holes": room["hole_polygons_m"], "room_id": room["room_id"],
               "floor": room["floor"], "name_en": room["name_en"], "name_ar": room["name_ar"], "line_id": ln["line_id"]}
        held = T.count_room(geo, units="m", size=None, exposure="INSIDE")
        recs.append(held)
        row = {"floor": room["floor"], "room_id": room["room_id"], "name_en": room["name_en"],
               "name_ar": room["name_ar"], "floor_line": ln["item_code"], "floor_line_m2": ln["measured_net"],
               "outline_net_m2": held.get("net_m2"), "status": held["status"], "held_reason": held["held_reason"]}
        gap = abs((held.get("net_m2") or 0) - ln["measured_net"]) / ln["measured_net"]
        row["candidate_basis"] = ("OUTLINE = FLOOR LINE" if gap <= 0.005 else
                                  "HELD: the floor line deducts stair treads / a void that V2.9 gives as m2 only, no "
                                  f"outline ({held.get('net_m2'):.2f} outline vs {ln['measured_net']:.2f} m2 line)")
        for k, (L, W) in SIZES.items():
            if gap > 0.005:
                for f in ("fewest", "most", "fewest_layout", "0deg", "90deg", "bought_m2", "reuse20_fewest"):
                    row[f"cand_{k}_{f}"] = None
                continue
            c = T.count_room(geo, units="m", exposure="INSIDE", offcut_reuse=False,
                             size={"length_m": L, "width_m": W, "origin": "CANDIDATE",
                                   "source": "owner-approved size list UP-CER-010 (candidate only)", "concerns": []})
            row[f"cand_{k}_fewest"] = c["tiles_to_buy"]
            row[f"cand_{k}_most"] = max(x["tiles_to_buy"] for x in c["layouts"])
            row[f"cand_{k}_fewest_layout"] = c["fewest"]["layout"]
            row[f"cand_{k}_0deg"] = "{fewest}-{most}".format(**c["by_direction"]["0deg"])
            row[f"cand_{k}_90deg"] = "{fewest}-{most}".format(**c["by_direction"]["90deg"])
            row[f"cand_{k}_bought_m2"] = round(c["tiles_to_buy"] * L * W, 4)
            c2 = T.count_room(geo, units="m", exposure="INSIDE", offcut_reuse=REUSE_SCENARIO_M,
                              size={"length_m": L, "width_m": W, "origin": "CANDIDATE",
                                    "source": "owner-approved size list UP-CER-010 (candidate only)", "concerns": []})
            row[f"cand_{k}_reuse20_fewest"] = c2["tiles_to_buy"]
        rows.append(row)
    with open(out / "ALSENAN_TILE_COUNT.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cand = [r for r in rows if r["candidate_basis"] == "OUTLINE = FLOOR LINE"]
    net = sum(r["outline_net_m2"] for r in cand)
    summ = {"rooms": len(rows), "table": T.project_table(recs),
            "floor_lines_m2": round(sum(r["floor_line_m2"] for r in rows), 4),
            "candidate_rooms": len(cand), "candidate_net_m2": round(net, 4),
            "candidate_held_rooms": [r["room_id"] for r in rows if r not in cand], "candidates": {}}
    for k, (L, W) in SIZES.items():
        fe = sum(r[f"cand_{k}_fewest"] for r in cand)
        mo = sum(r[f"cand_{k}_most"] for r in cand)
        ru = sum(r[f"cand_{k}_reuse20_fewest"] for r in cand)
        summ["candidates"][k] = {"tiles_fewest": fe, "tiles_most": mo, "bought_m2_fewest": round(fe * L * W, 3),
                                 "over_net_pct_fewest": round((fe * L * W / net - 1) * 100, 2),
                                 "over_net_pct_most": round((mo * L * W / net - 1) * 100, 2),
                                 "reuse20_tiles_fewest": ru,
                                 "reuse20_over_net_pct": round((ru * L * W / net - 1) * 100, 2)}
    # census of printed tile sizes in the DXF texts
    from ezdxf import recover
    from engine.source.cad import shx_arabic as SA
    doc, _ = recover.readfile(a.dxf)
    texts = [{"text": r["text"] or r["raw"], "layer": r["layer"], "status": r["status"]}
             for r in SA.records_from_doc(doc)]
    cen = T.census(texts)
    summ["census"] = {"texts_read": cen["texts_read"], "tile_size_notes": cen["tile_size_notes"],
                      "other_size_texts": cen["other_size_texts"],
                      "rows": [{"text": x["text"], "kind": x["kind"], "layer": x["layer"]} for x in cen["rows"]],
                      "joint_texts": [t["text"] for t in texts if "joint" in (t["text"] or "").lower()
                                      or "فاصل" in (t["text"] or "")]}
    (out / "alsenan_tile_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
