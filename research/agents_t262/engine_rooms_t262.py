"""T-262 part 2: the ENGINE's own room of each opening, crosswalked by area to the T-128 r3 rooms and checked against
the geometric join of part 1 (OPENING_ROOMS_T262.csv ROOMS_GEO). Closes the limit named in T-262_OPENING_ROOMS.md
s.5 ("the V3.0.10 window lines key each window to the ENGINE's own room ... not crosswalked"). Research code, any villa;
reads, writes only --out; ids, area shares and verdicts only (no coordinates, no names, no drawing content).

    python3 -I research/agents_t262/engine_rooms_t262.py <t262_capture.pkl> <ARCH_ROOMS.json> --out <dir>

<t262_capture.pkl> = capture_t262.py on P7757.dxf; <ARCH_ROOMS.json> = a released ARCH_TAKEOFF_V2.9 arch run on the
same DXF (tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9, as research/agents_t131/alsenan_v30_run.py); the
candidate's room ids (t232_inputs.WINDOW_ROOM) are checked to be this run's (room id = hash of the face id).

Rule (R-T262-4, proposed): an engine room R is crosswalked to the reference room T when the overlap covers at least
SHARE of T's area (R contains T) or of R's area (R lies in T); a room crosswalked to two or more reference rooms is
COARSER (an open plan / merged face). The engine's room of an opening = every engine room whose door / window / passage
list names the opening's per-floor engine id (census T-198 ENGINE_REF). Verdict per opening:
  AGREE            every engine room maps to exactly the geometric rooms, one to one;
  AGREE_COARSER    every geometric room is inside an engine room of the opening, and an engine room spans more rooms;
  ENGINE_SIDE_MISSING  a geometric room lies in no engine room of the opening (a side the engine does not give);
  ENGINE_WRONG_ROOM    an engine room of the opening contains none of the geometric rooms, on a side where the
                       geometric join found a room;
  ..._PLUS_UNREFERENCED  (suffix) the engine also gives a space that overlaps no reference room, on the side where the
                       geometric join found no room (NO_ROOM: outdoors, a passage pocket or a shaft the reference room
                       set does not carry); named with its class and area, never counted as a room match;
  NO_ENGINE_OPENING    the census names no engine opening (UNKNOWN on the engine side, never AGREE).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import pickle
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CENSUS = ROOT / "research/agents_t198/OPENINGS_T198.csv"
GEO = HERE / "OPENING_ROOMS_T262.csv"
SHARE = 0.50
OPREF = re.compile(r"\b(C?OP-\d{3})\b")


def poly(ext, holes=()):
    from shapely.geometry import Polygon
    p = Polygon(ext, [h for h in holes if len(h) >= 3])
    return p if p.is_valid else p.buffer(0)


def crosswalk(engine_rooms, ref_rooms, ref_floor, share=SHARE):
    """{engine room id: {"floor", "class", "refs": {ref id: (share of ref, share of engine)}, "mapped": [ref ids]}}"""
    from shapely.ops import unary_union
    refs = {}
    for k, parts in ref_rooms.items():
        refs[k] = unary_union([poly(p["ext"], p.get("holes") or ()) for p in parts])
    out = {}
    for r in engine_rooms:
        g = poly(r["polygon_m"], r.get("hole_polygons_m") or ())
        rec = {"floor": r["floor"], "class": r["class"], "area_m2": round(g.area, 4), "refs": {}, "mapped": []}
        for k, t in refs.items():
            if ref_floor[k] != r["floor"] or t.area <= 0 or g.area <= 0:
                continue
            a = g.intersection(t).area
            if a <= 1e-6:
                continue
            st, se = a / t.area, a / g.area
            rec["refs"][k] = (round(st, 4), round(se, 4))
            if st >= share or se >= share:
                rec["mapped"].append(k)
        rec["mapped"].sort()
        out[r["room_id"]] = rec
    return out


def engine_rooms_of(engine_rooms, floor, op_id):
    return sorted(r["room_id"] for r in engine_rooms if r["floor"] == floor
                  and op_id in set(r.get("doors") or ()) | set(r.get("windows") or ()) | set(r.get("passages") or ()))


def verdict(geo_rooms, eng_ids, xw, geo_has_no_room_side=False):
    """geo_rooms: set of reference rooms (part 1); eng_ids: engine rooms naming the opening; xw: crosswalk;
    geo_has_no_room_side: part 1 found NO_ROOM on one side of the opening."""
    if not eng_ids:
        return "ENGINE_NO_ROOM"
    unref = [e for e in eng_ids if not xw[e]["refs"]]
    if len(unref) > 1 or (unref and not geo_has_no_room_side):
        return "ENGINE_WRONG_ROOM"
    maps = {e: set(xw[e]["mapped"]) for e in eng_ids if e not in unref}
    if not maps or any(not (m & geo_rooms) for m in maps.values()):
        return "ENGINE_WRONG_ROOM"
    suffix = "_PLUS_UNREFERENCED" if unref else ""
    covered = set().union(*maps.values())
    if not geo_rooms <= covered:
        return "ENGINE_SIDE_MISSING"
    if all(len(m) == 1 for m in maps.values()) and covered == geo_rooms:
        return "AGREE" + suffix
    return "AGREE_COARSER" + suffix


def engine_ref(row):
    m = OPREF.search(row.get("ENGINE_REF") or "")
    return m.group(1) if m else None


def compute(cap, arch_rooms, census_rows, geo_rows, window_room=None):
    xw = crosswalk(arch_rooms, cap["rooms"], cap["room_floor"])
    geo = {r["ID"]: set((r["ROOMS_GEO"] or "").split()) for r in geo_rows}
    no_room = {r["ID"] for r in geo_rows if "NO_ROOM" in (r["SIDE_A_GEO"] + " " + r["SIDE_B_GEO"])}
    rows = []
    for c in census_rows:
        oid = c["ID"]
        if oid not in geo:
            continue
        op = engine_ref(c)
        eng = engine_rooms_of(arch_rooms, c["FLOOR"], op) if op else []
        v = verdict(geo[oid], eng, xw, oid in no_room) if op else "NO_ENGINE_OPENING"
        rows.append({"ID": oid, "KIND": c["KIND"], "FLOOR": c["FLOOR"], "ENGINE_OPENING": op or "",
                     "ENGINE_ROOMS": " ".join(eng),
                     "ENGINE_ROOMS_AS_T128": " | ".join(" ".join(xw[e]["mapped"]) or "-" for e in eng),
                     "UNREFERENCED": " ".join(f"{e}:{xw[e]['class']}:{xw[e]['area_m2']}" for e in eng
                                              if not xw[e]["refs"]),
                     "ROOMS_GEO": " ".join(sorted(geo[oid])), "VERDICT": v})
    wr = []
    for (fl, op), rid in sorted((window_room or {}).items()):
        names = engine_rooms_of(arch_rooms, fl, op)
        wr.append({"FLOOR": fl, "ENGINE_OPENING": op, "CANDIDATE_ROOM": rid, "RUN_ROOMS": " ".join(names),
                   "STATE": "SAME" if rid in names else "DIFFERS"})
    # no room area here: the shares carry the relation, and the folder's coordinate guard (test_t262_alsenan: no
    # number of 100 or more in a committed CSV / JSON) stays as it is
    xrows = [{"ENGINE_ROOM": k, "FLOOR": v["floor"], "CLASS": v["class"],
              "T128_MAPPED": " ".join(v["mapped"]),
              "T128_OVERLAPS": " ".join(f"{t}={a[0]:.3f}/{a[1]:.3f}" for t, a in sorted(v["refs"].items()))}
             for k, v in sorted(xw.items())]
    return rows, wr, xrows


def write_csv(rows):
    s = io.StringIO()
    if rows:
        w = csv.DictWriter(s, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return s.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("arch_rooms")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import sys
    sys.path.insert(0, str(ROOT / "research/agents_t232"))
    import t232_inputs as L10
    cap = pickle.loads(Path(a.capture).read_bytes())
    arch = json.loads(Path(a.arch_rooms).read_text(encoding="utf-8"))["rooms"]
    census = list(csv.DictReader(open(CENSUS, encoding="utf-8")))
    geo = list(csv.DictReader(open(GEO, encoding="utf-8")))
    rows, wr, xrows = compute(cap, arch, census, geo, L10.WINDOW_ROOM)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {"ENGINE_ROOMS_T262.csv": write_csv(rows), "ENGINE_ROOM_XWALK_T262.csv": write_csv(xrows),
             "CANDIDATE_WINDOW_ROOM_T262.csv": write_csv(wr)}
    for n, t in files.items():
        (out / n).write_text(t, encoding="utf-8")
    from collections import Counter
    print("verdicts", dict(Counter(r["VERDICT"] for r in rows)))
    print("candidate WINDOW_ROOM", dict(Counter(r["STATE"] for r in wr)))
    for r in rows:
        if r["VERDICT"] not in ("AGREE",):
            print(r["ID"], r["VERDICT"], r["ENGINE_ROOMS"], "->", r["ENGINE_ROOMS_AS_T128"], "| geo", r["ROOMS_GEO"])


if __name__ == "__main__":
    main()
