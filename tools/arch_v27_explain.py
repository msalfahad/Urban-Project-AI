"""ARCH_TAKEOFF_V2.6 -> V2.7 BOQ difference explainer (Phase 2B-7): every BOQ total that differs between the two runs
of one drawing, with the V2.7 correction records (CORRECTIONS_V2_7.json of the V2.7 run) whose scope covers it. A
difference no record covers is UNEXPLAINED. Stdlib only.

    python3 tools/arch_v27_explain.py --before OUT_V26 --after OUT_V27 [--out FILE.json]

A total is the sum of measured_net, the line count and the count of lines with no measured value, per (item_code,
location.room_id). The scope of a correction, by kind:
    LAYER_ROLE, COLUMN_SHAPES   every location of its floor (a role or a column changes the floor's topology)
    DOOR_OPENING                the opening's rooms (either run), its opening / strip locations, the floor's walls
    DOOR_FRAME                  the door's rooms and its opening / strip locations
    CURVED_WALL_BAND            the floor's walls
    WET_EVIDENCE, ARC_POLYGON   the rooms of the face(s) (either run), their openings and the rooms beyond them
    SLIVER_MERGE                its room
    PROVENANCE                  nothing (no quantity changes)
The attribution is by location, not by item: a covered difference is one a record CAN explain; the record's own
detail says how."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

POLICY = "URBAN_V27_BOQ_EXPLAIN_V1"
TOL = 1e-6


def _load(d, name):
    p = Path(d) / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def totals(lines):
    t = defaultdict(lambda: [0.0, 0, 0])
    floor_of = {}
    for ln in lines:
        loc = ln.get("location") or {}
        k = (ln["item_code"], loc.get("room_id"))
        v = ln.get("measured_net")
        t[k][0] += v or 0.0
        t[k][1] += 1
        t[k][2] += v is None
        floor_of[k] = loc.get("floor")
    return t, floor_of


def _rooms_of(runs, pred):
    return {r["room_id"] for rr in runs for r in rr if pred(r)}


def scopes(corrections, runs):
    """correction id -> {"floor": f or None, "locations": set or None (None: the whole floor)}."""
    rooms = [r["rooms"] for r in runs]
    ops = {}
    for r in runs:
        for o in r["openings"]:
            ops.setdefault((o["floor"], o["opening_id"]), set()).update(o.get("rooms") or ())
    els = {e["element_id"]: e for r in runs for e in r["doors"]}
    out = {}
    for c in corrections:
        kind, fl, sub = c["correction"], c.get("floor"), c.get("subject")

        def op_keys(f, oid):
            return {f"{f}-OPENING-{oid}", f"{f}-STRIP-{oid}"} | ops.get((f, oid), set())

        if kind in ("LAYER_ROLE", "COLUMN_SHAPES"):
            out[c["id"]] = {"floor": fl, "locations": None}
        elif kind == "DOOR_OPENING":
            out[c["id"]] = {"floor": fl, "locations": op_keys(fl, sub) | {f"{fl}-WALLS"}}
        elif kind == "DOOR_FRAME":
            e = els.get(sub) or {}
            locs = {x for x in (e.get("from_room"), e.get("to_room")) if x}
            oid = (c.get("detail") or {}).get("opening_id")
            out[c["id"]] = {"floor": fl, "locations": locs | (op_keys(fl, oid) if oid else set())}
        elif kind == "CURVED_WALL_BAND":
            out[c["id"]] = {"floor": fl, "locations": {f"{fl}-WALLS"}}
        elif kind in ("WET_EVIDENCE", "ARC_POLYGON"):
            faces = set((c.get("detail") or {}).get("faces") or ()) if kind == "ARC_POLYGON" else {sub}
            rids = _rooms_of(rooms, lambda r: r.get("face_id") in faces and r.get("floor") == fl)
            locs = set(rids)
            for rr in rooms:
                for r in rr:
                    if r["room_id"] in rids:
                        for oid in list(r.get("doors") or ()) + list(r.get("passages") or ()) + \
                                list(r.get("windows") or ()):
                            locs |= op_keys(fl, oid)
            out[c["id"]] = {"floor": fl, "locations": locs}
        elif kind == "SLIVER_MERGE":
            out[c["id"]] = {"floor": fl, "locations": {sub}}
        else:
            out[c["id"]] = {"floor": fl, "locations": set()}
    return out


def explain(before, after):
    a_lines, b_lines = _load(before, "BOQ_LINES.json"), _load(after, "BOQ_LINES.json")
    corr = (_load(after, "CORRECTIONS_V2_7.json") or {}).get("corrections") or []
    runs = []
    for d in (before, after):
        ds = _load(d, "DOOR_SCHEDULE.json") or {}
        runs.append({"rooms": (_load(d, "ARCH_ROOMS.json") or {}).get("rooms") or [],
                     "openings": (_load(d, "ARCH_OPENINGS.json") or {}).get("openings") or [],
                     "doors": ((ds.get("doors") or {}).get("elements")) or []})
    ta, fa = totals(a_lines)
    tb, fb = totals(b_lines)
    sc = scopes(corr, runs)
    rows = []
    for k in sorted(set(ta) | set(tb), key=lambda x: (str(x[0]), str(x[1]))):
        va, vb = ta.get(k, [0.0, 0, 0]), tb.get(k, [0.0, 0, 0])
        if abs(va[0] - vb[0]) <= TOL and va[1:] == vb[1:]:
            continue
        fl = fb.get(k) or fa.get(k)
        by = sorted(cid for cid, s in sc.items() if s["floor"] == fl and
                    (s["locations"] is None or k[1] in s["locations"]))
        rows.append({"item_code": k[0], "location": k[1], "floor": fl,
                     "v26": {"net": round(va[0], 6), "lines": va[1], "no_value": va[2]},
                     "v27": {"net": round(vb[0], 6), "lines": vb[1], "no_value": vb[2]},
                     "delta": round(vb[0] - va[0], 6),
                     "explained_by": by, "kinds": sorted({c["correction"] for c in corr if c["id"] in by}),
                     "state": "EXPLAINED" if by else "UNEXPLAINED"})
    return {"policy": POLICY, "before": str(before), "after": str(after), "differences": rows,
            "summary": {"differences": len(rows), "unexplained": sum(r["state"] == "UNEXPLAINED" for r in rows),
                        "by_kind": {k: sum(k in r["kinds"] for r in rows)
                                    for k in sorted({c["correction"] for c in corr})},
                        "corrections": len(corr)}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rep = explain(a.before, a.after)
    txt = json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    print(json.dumps(rep["summary"], sort_keys=True))
    return 1 if rep["summary"]["unexplained"] else 0


if __name__ == "__main__":
    sys.exit(main())
