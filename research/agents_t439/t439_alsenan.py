"""T-439 on the development villa: ceiling and skirting owners of the two GF pantry strips that T-435 found SILENT
(GF-SITE-0a31aaa10796d33a 1.100 m2, GF-OP-003-NO-OPENING 0.600 m2), by R-T439-1 (strip_owner_v1.py). Research only:
nothing is wired, no candidate or released quantity changes.

    python3 -I research/agents_t439/t439_extract.py ...  (drawings -> EXTRACT_T439.json; see its docstring)
    python3 -I research/agents_t439/t439_alsenan.py --write    # TABLE_T439.csv + summary.json from the extract
    python3 -I research/agents_t439/t439_alsenan.py --check    # rebuild from the committed extract, byte compare
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import strip_owner_v1 as S  # noqa: E402

EXTRACT = HERE / "EXTRACT_T439.json"
TABLE = HERE / "TABLE_T439.csv"
SUMMARY = HERE / "summary.json"
S1, S2 = "GF-SITE-0a31aaa10796d33a", "GF-OP-003-NO-OPENING"

# the room the strips lie in, from merged ledgers (cited, not re-measured here)
ROOM = {"id": "GF-07 open pantry (printed 450 x 300; engine faces GF-RC06FED + GF-RC99C2A part)", "class": "WET",
        "class_source": "owner Q-37 A (pantry wet within its printed box; T-286 MERGED, T-427)",
        "full_height_tile": True, "tile_source": "Q-48 A / UP-PANTRY-003; T-312 / T-315 r2 MERGED: L-f5c5a1a9 "
        "FIN.WALL.TILE 32.3422 m2, all pantry walls but the open edge (10.491 m x 3.65), faces GF-07|GF-W01 (A6) and "
        "GF-07|GF-W16 (AF) included",
        "wall_tile_line": "L-f5c5a1a9", "skirting_line": None}
FLOOR_LINES = {S1: "L-6c83b9fc (FIN.FLOOR.WET_TILE 1.1000, T-414 table)",
               S2: "L-50307dd9 (FIN.FLOOR.WET_TILE 0.6000, T-414 table)"}
# what existing lines already carry over the same box (T-271 / T-283 merged, CEILINGS_T271.csv): per beam mark, lm
CARRIED = {"B27": {"GF-RC06FED": (0.3524, "L-1624ef49"), "GF-RC99C2A part": (6.8969, "L-eb3be58f")},
           "CB8": {"GF-RC06FED": (1.6000, "L-1624ef49")}}
CARRIED_CEILING = {"GF-RC06FED": (2.800, "L-1624ef49 (decor 2.800 DRAWING-CONFIRMED + bulkhead 0.3281 OA)"),
                   "GF-RC99C2A part": (8.955, "L-eb3be58f (pantry part of the open-room line, T-271 / T-283)")}


def _neighbour(seg):
    if seg["neighbour_cls"] == "SLAB":
        return "SLAB", None, None
    if seg["neighbour_member"] and seg["neighbour_r2_depth"] is not None:
        return "BEAM", seg["neighbour_r2_depth"], "CALCULATED"
    return "UNREGISTERED", None, None


def _depth(b):
    try:
        return float(b["r2_depth"]) if b.get("r2_status") == "CALCULATED" else None
    except (TypeError, ValueError):
        return None


def build(ex):
    bf = ex["box"]["beam_faces"]
    seg_by_strip = {S1: [], S2: []}
    zone_held, carried_check = [], {}
    for b in bf:
        mark = b["mark"] or f"unregistered {b['slab_face']}"
        for z in b["segments"]:
            nb, nd, ns = _neighbour(z)
            two_sided = nb == "UNREGISTERED" or b["member"] is None   # the same line is listed from both pieces
            w = 0.5 if two_sided else 1.0
            if z["on_zone_line_between"]:
                if b["member"] is None or nb == "UNREGISTERED":
                    zone_held.append({"beam": mark, "m": round(z["m"] * w, 4),
                                      "between": "/".join(z["on_zone_line_between"])})
                continue
            for pid, m in z["by_piece_m"].items():
                if m <= 0:
                    continue
                if pid in seg_by_strip:
                    seg_by_strip[pid].append({"beam": mark, "m": round(m * w, 4), "unit": "m",
                                              "beam_depth_m": _depth(b), "beam_status": b.get("r2_status"),
                                              "neighbour": nb, "neighbour_depth_m": nd, "neighbour_status": ns,
                                              "carried_by": None})
                else:
                    carried_check.setdefault(mark, {}).setdefault(pid, 0.0)
                    carried_check[mark][pid] += m
    res, rows = [], []
    for s in ex["strips"]:
        edges = [{"length_m": e["length_m"], "role": e["role"], "unit": "m",
                  "refs": [d["handle"] for d in e["drawn"]]} for e in s["edges"] if e["length_m"] >= 0.0005]
        rec = {"id": s["id"], "floor_m2": s["area_m2"], "unit": "m2", "in_room_box_m2": s["in_box_m2"],
               "edges": edges}
        d = S.decide(rec, ROOM, seg_by_strip[s["id"]])
        d["engine_v29"] = s["engine"]
        d["floor_line"] = FLOOR_LINES[s["id"]]
        d["counter_m2"] = {"east": s["in_east_counter_m2"], "west": s["in_west_counter_m2"]}
        d["above_m2"] = s["above"]["above"]
        res.append(d)
        for e, r in zip(edges, d["skirting"]["rows"]):
            rows.append([s["id"], "SKIRTING", e["role"], "/".join(e["refs"]) or "-", f"{e['length_m']:.4f}", "lm",
                         r["owner"], r["line"] or "", r["status"]])
        c = d["ceiling"]
        rows.append([s["id"], "CEILING", "decor (plan area, incl. bulkhead undersides)", "-", f"{c['decor_m2']:.4f}",
                     "m2", c["code"], "NEW LINE (lane I)", c["decor_status"]])
        for b in c["bulkhead_faces"]:
            rows.append([s["id"], "CEILING", f"bulkhead face {b['beam']} h {b['height_m']:.2f}", "-",
                         f"{b['m']:.4f}", "m", f"{b['m2']:.6f} m2", "NEW LINE (lane I)", S.ST_OA])
        for b in c["held_edges"]:
            rows.append([s["id"], "CEILING", f"beam edge {b['beam']} (neighbour {b['neighbour']})", "-",
                         f"{b['m']:.4f}", "m", "HELD_EDGE", "", S.ST_H])
        for b in c["no_face"]:
            rows.append([s["id"], "CEILING", f"beam edge {b['beam']} (no face)", "-", f"{b['m']:.4f}", "m",
                         "NO_FACE", "", "REASON"])
    for z in zone_held:
        rows.append(["ZONE LINE " + z["between"], "CEILING", f"beam edge {z['beam']} on an engine zone line", "-",
                     f"{z['m']:.4f}", "m", "HELD_EDGE", "", S.ST_H])
    # reconciliation in units
    box_net = ex["box"]["net_of_column_m2"]
    pieces = dict(ex["box"]["pieces_m2"])
    clos = S.room_closure(box_net, pieces)
    ceil_after = round(sum(v[0] for v in CARRIED_CEILING.values()) + sum(d["ceiling"]["decor_m2"] for d in res), 6)
    recon = {}
    for b in bf:
        if b["mark"] in CARRIED:
            car = sum(v[0] for v in CARRIED[b["mark"]].values())
            strips = sum(z["by_piece_m"].get(S1, 0) + z["by_piece_m"].get(S2, 0) for z in b["segments"]
                         if not z["on_zone_line_between"])
            zone = sum(z["m"] for z in b["segments"] if z["on_zone_line_between"])
            recon[b["mark"]] = {"box_free_edge_m": b["free_edge_on_box_m"], "carried_m": round(car, 4),
                                "measured_in_carried_pieces_m": {k: round(v, 4) for k, v in
                                                                 carried_check.get(b["mark"], {}).items()},
                                "in_strips_m": round(strips, 4), "on_zone_lines_m": round(zone, 4),
                                "residual_m": round(b["free_edge_on_box_m"] - car - strips - zone, 4)}
    tot_b = round(sum(d["ceiling"]["bulkhead_m2"] for d in res), 6)
    held_m = round(sum((d["ceiling"]["held_edge_m"] or 0) for d in res) + sum(z["m"] for z in zone_held), 4)
    summ = {
        "task": "T-439", "inputs": ex["inputs"], "rule": "R-T439-1 (strip_owner_v1.py)",
        "room": ROOM, "box": {"net_m2": box_net, "pieces_m2": pieces, "closure_m2": clos,
                              "ceiling_m2_carried_plus_strips": ceil_after},
        "strips": res, "zone_line_held_edges": zone_held,
        "totals": {"ceiling_decor_new_m2": round(sum(d["ceiling"]["decor_m2"] for d in res), 6),
                   "ceiling_bulkhead_new_m2": tot_b, "ceiling_held_edges_m": held_m,
                   "paintable_owner_new_m2": round(sum(d["ceiling"]["paintable_owner_m2"] for d in res), 6),
                   "skirting_lm": None, "skirting_tile_owned_lm": round(sum(
                       (d["skirting"]["tile_owned_lm"] or 0) for d in res), 4)},
        "beam_reconciliation": recon,
        "v29_ceiling_lines_on_strips": ex["ceiling_lines_on_pieces_v29"],
        "jamb_search": ex["inserts_near_box"],
    }
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["space_id", "layer", "element", "drawn_refs", "qty", "unit", "owner_or_code", "line", "status"])
    w.writerows(rows)
    return buf.getvalue(), summ


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    ex = json.load(open(EXTRACT))
    table, summ = build(ex)
    summ["table_sha256_8"] = hashlib.sha256(table.encode()).hexdigest()[:8]
    js = json.dumps(summ, indent=1, sort_keys=True) + "\n"
    if "--write" in a:
        TABLE.write_text(table)
        SUMMARY.write_text(js)
        print(table)
        print(json.dumps(summ["totals"]), json.dumps(summ["box"]), json.dumps(summ["beam_reconciliation"]))
        return 0
    if "--check" in a:
        ok = TABLE.read_text() == table and SUMMARY.read_text() == js
        print("T-439 committed table and summary reproduce:", ok)
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
