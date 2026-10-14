"""URBAN BLIND TEST SCORER (protocol URBAN_BLIND_V1) - pre-registered before any blind drawing is received.

Scores a frozen ARCH_TAKEOFF_V2.1 prediction against a sealed benchmark, per floor, per room and per trade, with
false positives, silent and flagged omissions, duplicates and total-quantity errors kept apart. Stdlib only; reads the
published run files (BOQ_LINES.json, ARCH_ROOMS.json, ARCH_OPENINGS.json, DOOR_SCHEDULE.json) or the in-memory
(room_boq, arch) pair. It never changes a prediction and never reads a benchmark before `freeze_record` exists.

    export(out_dir)                       -> prediction (canonical rows) from a published run directory
    export_from_memory(room_boq, arch)    -> the same from arch_compute's return values
    score(prediction, benchmark)          -> metrics (see BLIND_TEST_PROTOCOL.md section 6)
    commitment(path, salt)                -> sha256 commitment of a sealed file (custodian side)
    freeze_record(out_dir, **provenance)  -> the prediction freeze record (sha256 of every published file)
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

PROTOCOL = "URBAN_BLIND_V1"

# item code -> scored trade (pre-registered; a code not listed is reported as UNSCORED, never dropped silently)
# FLOOR_AREA is scored from the room records (ARCH_ROOMS.json), not from lines: ARCH.SPACE lines repeat the area of the
# spaces the engine could not type and are reported under unscored_item_codes
TRADE_OF = {
    "FIN.FLOOR.PORCELAIN": "FLOOR_FINISH_DRY",
    "FIN.FLOOR.WET_TILE": "FLOOR_FINISH_WET",
    "FIN.WALL.TILE": "WALL_CERAMIC",
    "FIN.PLASTER": "PLASTER",
    "FIN.PAINT": "PAINT",
    "FIN.CEILING": "CEILING",
    "FIN.WP.FLOOR": "WATERPROOFING_FLOOR",
    "FIN.WP.UPTURN": "WATERPROOFING_UPTURN",
    "FIN.WP.DOORWAY": "WATERPROOFING_DOORWAY",
    "FIN.SKIRTING": "SKIRTING",
    "FIN.MARBLE.TREAD": "STAIR_TREAD_AREA",
    "FIN.MARBLE.RISER": "STAIR_RISER_AREA",
    "FIN.MARBLE.LANDING": "STAIR_LANDING_AREA",
    "FIN.RAILING": "HANDRAIL",
}
DOOR_CLASS_OF = {"DOOR.INTERNAL.PVC": "PVC", "DOOR.EXTERNAL.ALUMINIUM": "ALU", "DOOR.MAIN_ENTRANCE": "MAIN",
                 "LIFT": "LIFT", "MAIN_ENTRANCE_CANDIDATE": "MAIN_CANDIDATE", "CLASS_UNRESOLVED": "UNRESOLVED"}
# evidence state -> scoring status: only RELEASED quantities count as answers; the rest are flags
STATUS_OF = {"SOURCE_DERIVED": "RELEASED", "OWNER_APPROVED": "RELEASED", "PROVISIONAL": "PROVISIONAL",
             "BOUNDED_EXPOSURE": "PROVISIONAL", "ASSUMED": "PROVISIONAL", "BLOCKED_RFI": "FLAGGED",
             "NOT_APPLICABLE_WITH_EVIDENCE": "NOT_APPLICABLE"}

# pre-registered tolerances (BLIND_TEST_PROTOCOL.md section 6.3): an item is "within tolerance" when its absolute
# error is <= max(abs, rel * benchmark)
TOL = {"m2": (0.10, 0.02), "lm": (0.10, 0.02), "pcs": (0.0, 0.0)}
WIDTH_TOL_M = 0.02                       # door / window width agreement
POSITION_REACH_M = 0.60                  # element position match radius
CLAIM = {"coverage": 0.95, "wape": 0.05, "silent_omissions": 0, "fp_share": 0.02, "projects": 2}


# ---------------------------------------------------------------- prediction export (canonical rows)
def export_from_memory(room_boq, arch):
    unit = (arch.get("run") or {}).get("unit_m") or 1.0
    rooms = [{"floor": r["floor"], "room_id": r["room_id"], "kind": r.get("kind"), "class": r.get("class"),
              "name": r.get("name_en"), "polygon_m": [list(p) for p in r["polygon_m"]],
              "area_m2": r.get("area_m2")} for r in arch.get("rooms") or ()]
    rows, unscored = [], defaultdict(int)
    for r in arch.get("rooms") or ():
        if r.get("area_m2") is None:
            continue
        typed = r.get("class") in ("ROOM", "MIXED") and r.get("kind") is not None
        rows.append({"floor": r["floor"], "room_id": r["room_id"], "trade": "FLOOR_AREA", "item_code": "ROOM_AREA",
                     "unit": "m2", "qty": r["area_m2"], "status": "RELEASED" if typed else "PROVISIONAL",
                     "line_id": "AREA:" + r["room_id"], "element": None, "never_additive_with": []})
    for ln in room_boq.get("lines") or ():
        code = ln["item_code"]
        trade = TRADE_OF.get(code)
        if trade is None:
            unscored[code] += 1
            continue
        rows.append({"floor": ln["location"]["floor"], "room_id": ln["location"].get("room_id"), "trade": trade,
                     "item_code": code, "unit": ln["unit"], "qty": ln.get("measured_net"),
                     "status": STATUS_OF.get(ln["evidence_state"], "FLAGGED"), "line_id": ln["line_id"],
                     "element": ln["location"].get("element_id"),
                     "never_additive_with": sorted(ln.get("never_additive_with") or ())})
    elements = []
    doors = (arch.get("doors") or {}).get("elements")
    if doors is not None:
        for el in doors:
            cls = DOOR_CLASS_OF.get(el.get("boq_class") or el.get("class"), "UNRESOLVED")
            st = "RELEASED" if el.get("released") else ("EXCLUDED" if el.get("section") == "LIFT_EXCLUDED" else
                                                        "PROVISIONAL" if el["state"] != "UNRESOLVED" else "FLAGGED")
            c = el.get("centre")
            elements.append({"family": "DOOR", "floor": el["floor"], "id": el["element_id"], "class": cls,
                             "width_m": el.get("structural_opening_width_m"), "leaves": el.get("leaf_count"),
                             "xy_m": [c[0] * unit, c[1] * unit] if c else None, "status": st,
                             "height_m": el.get("height_m"), "area_m2": el.get("area_m2")})
    else:                                           # V1 / V2: doors are opening counts without a class or position
        for o in arch.get("openings") or ():
            if o["kind"] == "DOOR":
                elements.append({"family": "DOOR", "floor": o["floor"], "id": o["opening_id"], "class": "UNRESOLVED",
                                 "width_m": o.get("width_m"), "leaves": None, "xy_m": None, "status": "RELEASED",
                                 "height_m": None, "area_m2": None})
    for o in arch.get("openings") or ():
        if o["kind"] == "WINDOW":
            elements.append({"family": "WINDOW", "floor": o["floor"], "id": o["opening_id"], "class": None,
                             "width_m": o.get("width_m"), "leaves": None, "xy_m": None, "status": "RELEASED",
                             "height_m": o.get("height_m"), "area_m2": o.get("area_m2")})
    return {"protocol": PROTOCOL, "unit_m": unit, "rooms": rooms, "rows": rows, "elements": elements,
            "unscored_item_codes": dict(sorted(unscored.items()))}


def export(out_dir):
    out = Path(out_dir)
    lines = json.loads((out / "BOQ_LINES.json").read_text(encoding="utf-8"))
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text(encoding="utf-8"))
    ops = json.loads((out / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))
    arch = {"run": rooms["run"], "rooms": rooms["rooms"], "openings": ops["openings"]}
    ds = out / "DOOR_SCHEDULE.json"
    if ds.exists():
        arch["doors"] = json.loads(ds.read_text(encoding="utf-8"))["doors"]
    return export_from_memory({"lines": lines}, arch)


# ---------------------------------------------------------------- matching
def _inside(x, y, poly):
    ins = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def match_rooms(pred, bench):
    """each benchmark room -> the predicted room of its floor whose polygon holds its reference point."""
    m, by_pred = {}, defaultdict(list)
    for br in bench["rooms"]:
        x, y = br["ref_xy_m"]
        hit = [r for r in pred["rooms"] if r["floor"] == br["floor"] and _inside(x, y, r["polygon_m"])]
        hit.sort(key=lambda r: r.get("area_m2") or 0.0)         # nested faces: the smallest holder
        m[br["bench_room_id"]] = hit[0]["room_id"] if hit else None
        if hit:
            by_pred[hit[0]["room_id"]].append(br["bench_room_id"])
    merged = {p: sorted(b) for p, b in by_pred.items() if len(b) > 1}
    return m, merged


def category_confusion(pred, bench, rmap):
    kind = {r["room_id"]: r.get("kind") or r.get("class") for r in pred["rooms"]}
    out = defaultdict(int)
    for b in bench["rooms"]:
        out[f"{b.get('category')}->{kind.get(rmap.get(b['bench_room_id'])) if rmap.get(b['bench_room_id']) else 'NO_ROOM'}"] += 1
    return dict(sorted(out.items()))


def _greedy(bs, ps, dist, reach):
    pairs = sorted(((dist(b, p), i, j) for i, b in enumerate(bs) for j, p in enumerate(ps)), key=lambda t: t[0])
    ub, up, out = set(), set(), []
    for d, i, j in pairs:
        if d > reach or i in ub or j in up:
            continue
        ub.add(i)
        up.add(j)
        out.append((i, j, d))
    return out


# ---------------------------------------------------------------- scoring
def _tol(unit, ref):
    a, r = TOL.get(unit, (0.0, 0.0))
    return max(a, r * abs(ref))


def _trade_block():
    return {"bench_items": 0, "bench_total": 0.0, "released_matched": 0, "within_tolerance": 0, "abs_error_sum": 0.0,
            "flagged_omissions": 0, "silent_omissions": 0, "false_positive_items": 0, "false_positive_qty": 0.0,
            "duplicates": 0, "pred_released_total": 0.0, "covered_bench_qty": 0.0, "items": []}


def _finish(t):
    bt = t["bench_total"]
    t["wape_released_matched"] = round(t["abs_error_sum"] / t["covered_bench_qty"], 6) if t["covered_bench_qty"] else None
    t["coverage_qty"] = round(t["covered_bench_qty"] / bt, 6) if bt else None
    t["total_error_pct"] = round(100.0 * (t["pred_released_total"] - bt) / bt, 4) if bt else None
    t["fp_share"] = round(t["false_positive_qty"] / bt, 6) if bt else None
    for k in ("bench_total", "abs_error_sum", "false_positive_qty", "pred_released_total", "covered_bench_qty"):
        t[k] = round(t[k], 6)
    return t


def score(pred, bench, *, projects=1):
    """-> {"rooms": room matching, "trades": per-trade metrics (all floors), "by_floor": {floor: {trade: ...}},
    "by_category": {KITCHEN / BATHROOM / ...: {trade: ...}}, "elements": door / window metrics, "claims": ...}."""
    rmap, merged = match_rooms(pred, bench)
    cat_of = {b["bench_room_id"]: b.get("category") or "OTHER" for b in bench["rooms"]}
    floor_of = {b["bench_room_id"]: b["floor"] for b in bench["rooms"]}
    rows_of = defaultdict(list)
    for r in pred["rows"]:
        rows_of[(r["room_id"], r["trade"])].append(r)
    trades, by_floor, by_cat = defaultdict(_trade_block), defaultdict(lambda: defaultdict(_trade_block)), \
        defaultdict(lambda: defaultdict(_trade_block))
    used = set()
    for q in bench["room_quantities"]:
        bid, trade, ref, unit = q["bench_room_id"], q["trade"], float(q["qty"]), q["unit"]
        pid = rmap.get(bid)
        rows = rows_of.get((pid, trade), []) if pid else []
        rel = [r for r in rows if r["status"] == "RELEASED" and r["qty"] is not None]
        flag = [r for r in rows if r["status"] in ("PROVISIONAL", "FLAGGED")]
        shared = pid in merged
        item = {"bench_room_id": bid, "pred_room_id": pid, "trade": trade, "unit": unit, "bench": ref,
                "pred_released": round(sum(r["qty"] for r in rel), 6) if rel else None, "merged_room": shared}
        if rel:
            p = sum(r["qty"] for r in rel)
            # a merged predicted room answers several benchmark rooms at once: its quantity is scored once, against
            # the sum of those rooms (recorded on the first of them; the others are MERGED_INTO it)
            if shared:
                peers = merged[pid]
                if bid != peers[0]:
                    item["outcome"] = "MERGED_INTO " + peers[0]
                    for t in (trades[trade], by_floor[floor_of[bid]][trade], by_cat[cat_of[bid]][trade]):
                        t["bench_items"] += 1
                        t["bench_total"] += ref
                        t["items"].append(item)
                    continue
                ref_sum = sum(float(x["qty"]) for x in bench["room_quantities"]
                              if x["trade"] == trade and x["bench_room_id"] in peers)
            else:
                ref_sum = ref
            err = p - ref_sum
            item.update(outcome="RELEASED", error=round(err, 6),
                        rel_error=round(err / ref_sum, 6) if ref_sum else None,
                        within_tolerance=abs(err) <= _tol(unit, ref_sum), duplicate=len(rel) > 1)
            used.update(r["line_id"] for r in rel)
        elif flag:
            item["outcome"] = "FLAGGED_OMISSION"
            used.update(r["line_id"] for r in flag)
        else:
            item["outcome"] = "SILENT_OMISSION"
        for t in (trades[trade], by_floor[floor_of[bid]][trade], by_cat[cat_of[bid]][trade]):
            t["bench_items"] += 1
            t["bench_total"] += ref
            t["items"].append(item)
            if item["outcome"] == "RELEASED":
                t["released_matched"] += 1
                t["within_tolerance"] += bool(item["within_tolerance"])
                t["abs_error_sum"] += abs(item["error"])
                t["pred_released_total"] += sum(r["qty"] for r in rel)
                t["covered_bench_qty"] += ref_sum
                t["duplicates"] += bool(item["duplicate"])
            elif item["outcome"] == "FLAGGED_OMISSION":
                t["flagged_omissions"] += 1
            else:
                t["silent_omissions"] += 1
    # released predictions that answer no benchmark item: false positives (a quantity where the benchmark has none)
    bench_floors = {b["floor"] for b in bench["rooms"]}
    scored_trades = {q["trade"] for q in bench["room_quantities"]}
    for r in pred["rows"]:
        if r["line_id"] in used or r["status"] != "RELEASED" or r["qty"] is None or r["trade"] not in scored_trades:
            continue
        if r["floor"] not in bench_floors:
            continue
        cat = "UNMATCHED_PREDICTED_ROOM"
        for t in (trades[r["trade"]], by_floor[r["floor"]][r["trade"]], by_cat[cat][r["trade"]]):
            t["false_positive_items"] += 1
            t["false_positive_qty"] += r["qty"]
            t["pred_released_total"] += r["qty"]
            t["items"].append({"pred_room_id": r["room_id"], "trade": r["trade"], "outcome": "FALSE_POSITIVE",
                               "pred_released": r["qty"], "line_id": r["line_id"]})
    res = {"protocol": PROTOCOL,
           "rooms": {"bench_rooms": len(bench["rooms"]), "matched": sum(1 for v in rmap.values() if v),
                     "unmatched_bench_rooms": sorted(k for k, v in rmap.items() if not v),
                     "merged_predicted_rooms": merged,
                     "category_confusion": category_confusion(pred, bench, rmap),
                     "predicted_rooms_without_bench_room": sorted(
                         r["room_id"] for r in pred["rooms"] if r["floor"] in bench_floors
                         and r["room_id"] not in set(rmap.values()))},
           "trades": {k: _finish(v) for k, v in sorted(trades.items())},
           "by_floor": {f: {k: _finish(v) for k, v in sorted(d.items())} for f, d in sorted(by_floor.items())},
           "by_category": {c: {k: _finish(v) for k, v in sorted(d.items())} for c, d in sorted(by_cat.items())},
           "elements": score_elements(pred, bench),
           "unscored_item_codes": pred.get("unscored_item_codes") or {}}
    res["claims"] = claims(res, projects=projects)
    return res


def score_elements(pred, bench):
    """doors (by class, position when both sides give one) and windows (by width) per floor."""
    out = {}
    for fam in ("DOOR", "WINDOW"):
        fl = sorted({e["floor"] for e in bench.get("elements") or () if e["family"] == fam})
        res = {}
        for f in fl:
            bs = [e for e in bench["elements"] if e["family"] == fam and e["floor"] == f]
            ps = [e for e in pred["elements"] if e["family"] == fam and e["floor"] == f]
            have_xy = all(e.get("xy_m") for e in bs) and all(e.get("xy_m") for e in ps)
            if have_xy:
                pairs = _greedy(bs, ps, lambda b, p: math.dist(b["xy_m"], p["xy_m"]), POSITION_REACH_M)
            else:
                pairs = _greedy(bs, ps, lambda b, p: abs((b["width_m"] or 0) - (p["width_m"] or 0)), WIDTH_TOL_M)
            mb, mp = {i for i, _, _ in pairs}, {j for _, j, _ in pairs}
            conf = defaultdict(int)
            werr = []
            matched_released = 0
            for i, j, _ in pairs:
                b, p = bs[i], ps[j]
                conf[f"{b.get('class')}->{p.get('class')}:{p['status']}"] += 1
                if p["status"] == "RELEASED":
                    matched_released += 1
                if b.get("width_m") is not None and p.get("width_m") is not None:
                    werr.append(abs(b["width_m"] - p["width_m"]))
            res[f] = {"bench": len(bs), "pred_released": sum(1 for p in ps if p["status"] == "RELEASED"),
                      "pred_all": len(ps), "matched": len(pairs), "matched_released": matched_released,
                      "omissions": len(bs) - len(mb),
                      "false_positives_released": sum(1 for j, p in enumerate(ps)
                                                      if j not in mp and p["status"] == "RELEASED"),
                      "class_confusion": dict(sorted(conf.items())),
                      "class_correct_released": sum(v for k, v in conf.items()
                                                    if k.split("->")[0] == k.split("->")[1].split(":")[0]
                                                    and k.endswith(":RELEASED")),
                      "width_mae_m": round(sum(werr) / len(werr), 6) if werr else None,
                      "matched_by": "POSITION" if have_xy else "WIDTH"}
        out[fam] = res
    return out


def claims(res, *, projects):
    """a percentage claim is allowed only for a trade that meets every pre-registered bar on >= CLAIM projects."""
    out = {}
    for trade, t in res["trades"].items():
        why = []
        if projects < CLAIM["projects"]:
            why.append(f"{projects} project(s) scored; a claim needs {CLAIM['projects']}")
        if t["coverage_qty"] is None or t["coverage_qty"] < CLAIM["coverage"]:
            why.append(f"coverage {t['coverage_qty']} < {CLAIM['coverage']}")
        if t["wape_released_matched"] is None or t["wape_released_matched"] > CLAIM["wape"]:
            why.append(f"WAPE {t['wape_released_matched']} > {CLAIM['wape']}")
        if t["silent_omissions"] > CLAIM["silent_omissions"]:
            why.append(f"{t['silent_omissions']} silent omission(s)")
        if t["fp_share"] is not None and t["fp_share"] > CLAIM["fp_share"]:
            why.append(f"false-positive share {t['fp_share']} > {CLAIM['fp_share']}")
        out[trade] = {"claim_allowed": not why, "why_not": why}
    return out


# ---------------------------------------------------------------- sealing and freezing
def commitment(path, salt):
    """custodian side: sha256(salt || file bytes) - published before the run, the file stays sealed."""
    h = hashlib.sha256(salt.encode("utf-8"))
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def freeze_record(out_dir, **provenance):
    out = Path(out_dir)
    files = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(out.rglob("*")) if p.is_file()}
    return {"protocol": PROTOCOL, "files": files,
            "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), **provenance}
