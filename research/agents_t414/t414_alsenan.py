"""T-414 on the development villa: B3-05 floor bed / screed per room from the candidate of record ARCH_TAKEOFF_V3.0.34
(its V3_0_34_BOQ_LINES.json, produced by research/agents_t399/v3034_run.py on the Drive copies, kept in .work/private),
with the T-214 build-up (research/agents_t214, merged) and the owner rules Q-41 / Q-45. Research only.

    python3 -I research/agents_t414/t414_alsenan.py <dir holding V3_0_34_BOQ_LINES.json>            # prints
    python3 -I research/agents_t414/t414_alsenan.py <dir> --write    # writes ROOM_TABLE_T414.csv + summary.json
    python3 -I research/agents_t414/t414_alsenan.py --check          # summary.json closes on ROOM_TABLE_T414.csv

Committed outputs carry engine ids, line ids, item codes, states and quantities only (no coordinates, no names).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t214"))
import floor_bed_v1 as FB  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.34"
CANDIDATE_JSON_SHA256 = "4c7f581cf13b28c166cf93532cbce2a79d1ad711bb0f6e9f3915fc8f279f5402"  # T-399 summary, Checker
TABLE = HERE / "ROOM_TABLE_T414.csv"
SUMMARY = HERE / "summary.json"
# candidate evidence state -> evidence status of the AREA (WORKFLOW_CONTROLS s.5); anything else -> HELD (never 0)
AREA_STATUS = {"SOURCE_DERIVED": "DRAWING-CONFIRMED", "VERIFIED": "VERIFIED", "PROVISIONAL": FB.STATUS_OWNER,
               "MEASURED": "DRAWING-CONFIRMED",          # a Checker-run threshold item (V3.0.29, T-340)
               "NOT_APPLICABLE_WITH_EVIDENCE": "NOT_APPLICABLE"}
FLOOR_CODES = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")
# floor-type codes that are NOT a B3-05 room bed: they belong to another family's own bed / build-up
OWNED_CODES = {"FIN.MARBLE.TREAD": "STAIR", "FIN.MARBLE.RISER": "STAIR", "FIN.MARBLE.LANDING": "STAIR",
               "FIN.STAIR.FLIGHT": "STAIR", "FIN.STAIR.STEP_LM": "STAIR", "FIN.ROOF.SCREED": "ROOF",
               "FIN.ROOF.FINISH": "ROOF", "FIN.ROOF.PROTECTION": "ROOF", "FIN.ROOF.INSULATION": "ROOF",
               "EXT.PAVING.INTERLOCK": "OUTDOOR_GROUND", "EXT.FLOOR.PORCELAIN": "OUTDOOR_GROUND",
               "EXT.FLOOR.OUTDOOR": "OUTDOOR_GROUND"}
OTHER_LAYER_CODES = {"FIN.WP.FLOOR": ("B8-01", "MEMBRANE"), "FIN.WP.DOORWAY": ("B8-02", "MEMBRANE"),
                     "FIN.WP.WALL_UPTURN": ("B8-03", "MEMBRANE_UPTURN"), "FIN.WP.ROOF": ("B8-06", "MEMBRANE"),
                     "FIN.ROOF.SCREED": ("B13-01", "FALLS_SCREED")}
# T-214 zone per floor; a wet room never takes the dry layer (FLOOR_BUILDUP_V1 rule, ERS s.3)
DRY_ZONE = {"GF": "GF-DRY", "1F": "1F-DRY", "2F": "2F-DRY"}
WET_ZONE = {"GF": "GF-WET", "1F": "1F-SUNKEN", "2F": "2F-SUNKEN"}
GF_ANNEX_NOTE = "GF main +1.00 and annex +0.30 both draw b 0.05 (T-214): the bed bound does not depend on which"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(d):
    p = Path(d) / "V3_0_34_BOQ_LINES.json"
    h = sha256(p)
    if h != CANDIDATE_JSON_SHA256:
        raise SystemExit(f"stale candidate: {p.name} sha256 {h[:8]} is not V3.0.34 {CANDIDATE_JSON_SHA256[:8]}")
    raw = json.loads(p.read_text(encoding="utf-8"))
    return raw["lines"] if isinstance(raw, dict) else raw


def _zones():
    import t214_alsenan_check as T214
    return {z["zone"]: z for z in T214.build()["zones"]}


def _loc(l):
    loc = l.get("location") or {}
    return loc.get("room_id") or loc.get("element_id", "").split(":")[0], loc.get("element_id"), loc.get("floor")


def rooms_from(lines):
    zones = _zones()
    wp_area = {}
    for l in lines:
        if l["item_code"] == "FIN.WP.FLOOR":
            wp_area[_loc(l)[0]] = wp_area.get(_loc(l)[0], 0.0) + (l.get("measured_net") or 0.0)
    wp_rooms = set(wp_area)
    rooms, owned, other = [], {}, []
    for l in lines:
        code = l["item_code"]
        rid, eid, floor = _loc(l)
        if code in OWNED_CODES:
            owned.setdefault(OWNED_CODES[code], set()).add(l["line_id"])
        if code in OTHER_LAYER_CODES:
            fam, layer = OTHER_LAYER_CODES[code]
            other.append({"element_id": eid, "room": rid, "family": fam, "layer": layer, "line_id": l["line_id"]})
        if code not in FLOOR_CODES:
            continue
        # wet = the wet-room tile code, or a whole room under the membrane (a kitchen, Q-30 A); a membrane over PART of a
        # dry room (the open room's pantry, Q-37 A) does not make the whole room wet: that part has its own line
        net = l.get("measured_net")
        whole = rid in wp_area and net is not None and abs(wp_area[rid] - net) <= 1e-3 * max(net, 1.0)
        wet = code == "FIN.FLOOR.WET_TILE" or whole
        kind = "WET" if wet else "DRY"
        st = l.get("evidence_state")
        area_status = AREA_STATUS.get(st, "HELD")
        z = zones[(WET_ZONE if wet else DRY_ZONE)[floor]]
        bu = {"zone_type": "WET" if wet else "DRY", "b": z["drawing_b_m"], "status": z["drawing_status"],
              "ref": f"T-214 {z['zone']}: {z['drawing_basis']}", "missing": z["drawing_basis"]}
        if bu["b"] is None:
            bu.pop("ref")
        rooms.append({"element_id": eid, "room": rid, "floor": floor, "kind": kind, "finish_line": l["line_id"],
                      "finish_code": code, "candidate_state": st, "area_status": area_status,
                      "area_m2": l.get("measured_net") if area_status not in ("HELD", "NOT_APPLICABLE") else None,
                      "bounded": (l.get("bounded_range") or [l.get("bounded_low"), l.get("bounded_high")]) if area_status == "HELD" else None,
                      "ffl": z["ffl"], "slab_top": z["slab_top_drawing"], "build_up": bu,
                      "membrane_in_room": ("WHOLE" if whole else f"PART {wp_area[rid]:.4f}") if rid in wp_rooms
                      else "NONE"})
    return rooms, {k: sorted(v) for k, v in owned.items()}, other


def build(d):
    lines = _lines(d)
    rooms, owned, other = rooms_from(lines)
    res = FB.evaluate({"units": "m", "rooms": rooms})
    by = {r["element_id"]: r for r in rooms}
    for r in res["rows"]:
        src = by[r["element_id"]]
        r.update(room=src["room"], candidate_state=src["candidate_state"], slab_top=src["slab_top"],
                 bounded=src["bounded"], membrane_in_room=src["membrane_in_room"])
    # another family's layer on the same ROOM (its own element id differs: ':wp_floor' vs ':floor')
    rows_by_room = {}
    for r in res["rows"]:
        rows_by_room.setdefault(r["room"], []).append(r["element_id"])
    ov = FB.overlap_check(res["rows"], [dict(o, element_id=e) for o in other for e in rows_by_room.get(o["room"], [])])
    return res, owned, other, ov, len(lines)


COLS = ["element_id", "room", "floor", "kind", "layer", "finish_line", "finish_code", "candidate_state", "m2_status",
        "area_m2", "area_bound_low", "area_bound_high", "ffl", "slab_top", "build_up_b", "build_up_status",
        "finish_thickness", "m3_drawing_status", "m3_drawing_low", "m3_drawing_high", "m3_owner_status",
        "m3_owner_low", "m3_owner_high", "owner_check", "membrane_in_room", "missing"]


def _f(v):
    return "" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))


def table_csv(res):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(COLS)
    for r in sorted(res["rows"], key=lambda r: (r["floor"], r["kind"], r["element_id"])):
        d, md, mo = r["drawing"], r["m3_drawing"], r["m3_owner"]
        lo_hi = md.get("range") or md.get("bound") or [None, None]
        miss = sorted(set(md.get("missing", []) + mo.get("missing", [])))
        w.writerow([_f(x) for x in [
            r["element_id"], r["room"], r["floor"], r["kind"], r["layer"], r["finish_line"], r["finish_code"],
            r["candidate_state"], r["m2_status"], r["area_m2"], (r["bounded"] or [None, None])[0],
            (r["bounded"] or [None, None])[1], r["ffl"], r["slab_top"], d.get("b"), d["status"],
            "NOT PRINTED", md["status"], lo_hi[0], lo_hi[1], mo["status"], mo.get("low"), mo.get("high"),
            r["owner_manual"].get("check"), r["membrane_in_room"], " | ".join(miss)]])
    return s.getvalue()


def summary(res, owned, other, ov, n, table):
    return {"task": "T-414", "method": FB.METHOD, "family": FB.FAMILY, "candidate": CANDIDATE,
            "candidate_lines": n, "candidate_json_sha256": CANDIDATE_JSON_SHA256,
            "table_sha256": hashlib.sha256(table.encode()).hexdigest(), "rows": len(res["rows"]),
            "totals": res["totals"], "owned_elsewhere_lines": {k: len(v) for k, v in owned.items()},
            "other_layer_lines_on_b3_05_rooms": sorted({(o["family"], o["layer"]) for o in other
                                                        if o["room"] in {r["room"] for r in res["rows"]}}),
            "double_counted": ov["double_counted"], "gf_annex_note": GF_ANNEX_NOTE,
            "freelancer": {"screed_or_bed_rows": 0, "tiled_floor_rows_m2": {"dry_rooms_and_halls": 337.57,
                                                                          "wet_areas": 72.01, "total": 409.58},
                           "basis": "Drive 'Alsenan chalet project' floors / waterproofing / decor / marble workbook, "
                                    "quantities only"}}


def check():
    t = TABLE.read_text()
    s = json.loads(SUMMARY.read_text())
    assert s["table_sha256"] == hashlib.sha256(t.encode()).hexdigest(), "table changed without the summary"
    rows = list(csv.DictReader(io.StringIO(t)))
    assert len(rows) == s["rows"]
    for kind, tot in s["totals"].items():
        rs = [r for r in rows if r["kind"] == kind and r["area_m2"]]
        assert abs(sum(float(r["area_m2"]) for r in rs) - tot["m2"]) < 1e-3, kind
    return s


def main(argv):
    if argv[:1] == ["--check"]:
        print(json.dumps(check()["totals"], indent=1))
        return 0
    res, owned, other, ov, n = build(argv[0])
    t = table_csv(res)
    s = summary(res, owned, other, ov, n, t)
    if "--write" in argv:
        TABLE.write_text(t)
        SUMMARY.write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
