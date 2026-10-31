"""T-390 development-villa run: the T-388 F2 face-length residuals traced to their drawn cause (research, read-only).

Inputs: the T-250 capture pickle written OUTSIDE the repository by research/agents_t250/capture_t250.py on P7757.dxf
(Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, sha256 ab54dd55...; the capture re-runs the merged T-128 r3
walk and refuses itself unless it reproduces walk_r3.json on 32 / 32 rooms), and merged ledgers of this repository:
agents_t128/ROOMS_T128_R3.csv, agents_t250/FACE_LENGTH_T250.csv and ROOM_CLOSURE_T250.csv, and the T-388 face table
builder (agents_t388/alsenan_t388.py, merged df170b8d) for the family face lengths.

Writes ids, lengths, classes and causes only (no coordinate, no name, no drawing content):
  ROOM_FACE_T390.csv      per room: contour, open-side runs, corner VIRTUAL, the T-128 r3 face, the T-388 (d') face,
                          both residuals of every family against them (all 32 rooms)
  ARTEFACT_T390.csv       per room x band side: VIRTUAL metres a crosswalk puts on the band face line, by cause (R-T390-1 b),
                          the T-250 face metres of that band side and the corrected face metres
  T388_FACES_CORRECTED_T390.csv  the T-388 face table rows these metres touch: length, artefact, corrected length
  summary.json            counts
Usage (project venv, Python 3.11): python -I research/agents_t390/alsenan_t390.py <t250_capture.pkl> [--out DIR] [--check]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t250"))
sys.path.insert(0, str(RES / "agents_t388"))
import face_length_rule as FR  # noqa: E402
import face_crosswalk as X  # noqa: E402
import alsenan_t250 as A250  # noqa: E402
import alsenan_t388 as A388  # noqa: E402


def rd(p):
    with open(RES / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def R(x, n=4):
    return round(x, n) + 0.0


def _unit(dx, dy):
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L > 0 else (0.0, 0.0)


def artefacts(C):
    """per room: open/corner split; per (room, band, side): artefact metres by cause (open-side samples the T-250
    crosswalk puts on a band face, after its strip probe, exactly as assign_samples does)."""
    rooms, by_face = {}, defaultdict(lambda: defaultdict(float))
    for fl in ("GF", "1F", "2F"):
        bands = X.prepare(A250.straight(C["runs"][fl]["bands"]))
        for room, rows in C["samples"].items():
            if C["room_floor"][room] != fl:
                continue
            rings = defaultdict(list)
            for q in rows:
                rings[q[4]].append(q)
            ring_ids = sorted(rings)
            split = FR.open_side_split([[(q[0], q[3]) for q in rings[r]] for r in ring_ids])
            rooms[room] = {"floor": fl, "contour_m": R(sum(q[3] for q in rows)),
                           "virtual_m": R(sum(q[3] for q in rows if q[0] == "VIRTUAL")),
                           "open_m": split["open_m"], "corner_m": split["corner_m"], "open_runs": split["open_runs"]}
            polys = C["polys"][room]
            for ri, rid in enumerate(ring_ids):
                seq, flags = rings[rid], split["is_open"][ri]
                n = len(seq)
                hits = []
                for k, q in enumerate(seq):
                    if q[0] != "VIRTUAL":
                        continue
                    x, y = q[1], q[2]
                    hit = X.locate((x, y), bands)
                    if hit is None:
                        continue
                    b, s, side, _ = hit
                    ux, uy, nx, ny, L = b["_f"]
                    probe = (x + side * nx * X.PROBE_M, y + side * ny * X.PROBE_M)
                    inner = (x - side * nx * X.PROBE_M, y - side * ny * X.PROBE_M)
                    if not X._in_room(probe, polys) and X._in_room(inner, polys):
                        continue                      # inside the band strip: T-250 lists it off-line, not on a face
                    p0, p1 = seq[(k - 1) % n], seq[(k + 1) % n]
                    hits.append((k, b, s, side, L, _unit(p1[1] - p0[1], p1[2] - p0[2]), q[3]))
                # the open-side run each sample belongs to (cyclic run index), for the sides seen per band
                runs = FR.cyclic_runs([(q[0], q[3]) for q in seq])
                run_of = {}
                for j, (_c, _ln, ix) in enumerate(runs):
                    for k in ix:
                        run_of[k] = j
                sides = defaultdict(set)
                for k, b, s, side, L, d, seg in hits:
                    sides[(run_of[k], b["band"])].add(side)
                for k, b, s, side, L, d, seg in hits:
                    key = (room, b["band"], "+" if side > 0 else "-")
                    if not flags[k]:
                        by_face[key]["CORNER"] += seg
                        continue
                    cause = FR.artefact_cause(d, (b["_f"][0], b["_f"][1]), s, L, sides[(run_of[k], b["band"])])
                    by_face[key][cause] += seg
    return rooms, by_face


def build(C):
    rooms, by_face = artefacts(C)
    t128 = {r["ROW"]: r for r in rd("agents_t128/ROOMS_T128_R3.csv")}
    clos250 = {r["room"]: r for r in rd("agents_t250/ROOM_CLOSURE_T250.csv")}
    d388 = A388.build()
    fam = defaultdict(dict)
    for c in d388["closures"]:
        fam[c["room"]][c["family"]] = c
    room_rows = []
    for room in sorted(rooms):
        r, t, c = rooms[room], t128[room], clos250[room]
        face_t128 = float(t["FACE_M"])
        geo_new = FR.geometric_face_m(r["contour_m"], r["open_m"])
        geo_388 = R(float(c["walk_contour_m (T-128 r3)"]) - float(c["off: VIRTUAL (open side)"]))
        for f, cc in sorted(fam[room].items()):
            cl = FR.closure(cc["family_length_m"], r["contour_m"], r["open_m"], cc["top_m"])
            room_rows.append({
                "room": room, "family": f, "contour_m": r["contour_m"], "virtual_all_m": r["virtual_m"],
                "open_side_runs_m": " + ".join(f"{v:.3f}" for v in r["open_runs"]) or "0",
                "open_side_m": r["open_m"], "corner_virtual_m (face)": r["corner_m"],
                "t128_r3_open_sides_m": float(t["OPEN_SIDES_M"]), "t128_r3_face_m": face_t128,
                "geometric_face_m (R-T390-1 a)": geo_new, "t388_dprime_face_m": geo_388,
                "family_length_m": cc["family_length_m"], "top_m": cc["top_m"],
                "t388_residual_m": R(cc["family_length_m"] - geo_388),
                "residual_m (R-T390-1)": cl["residual_m"], "residual_m2 (R-T390-1)": cl["m2"],
                "status": ("CLOSED" if cl["ok"] else ("EXPLAINED (T-388: VERIFIED outline)" if cc.get("explained")
                                                      else "OPEN"))})
    face250 = defaultdict(lambda: {"face_m": 0.0, "finish_m": 0.0, "virtual_m": 0.0, "rows": 0})
    for r in rd("agents_t250/FACE_LENGTH_T250.csv"):
        band = r["run_id"].split("#")[0].split(" ")[0]
        e = face250[(r["room"], band, r["side"])]
        e["face_m"] += float(r["face_m"])
        e["finish_m"] += float(r["finish_m (WALL+COLUMN)"])
        e["virtual_m"] += float(r["virtual_m"] or 0)
        e["rows"] += 1
        e.setdefault("walls", set()).add(r["wall_id"])
    vrows = defaultdict(list)
    for r in rd("agents_t250/FACE_LENGTH_T250.csv"):
        if float(r["virtual_m"] or 0) > 0:
            vrows[(r["room"], r["run_id"].split("#")[0].split(" ")[0], r["side"])].append(r["wall_id"])
    f388 = {r["face_id"]: r for r in rd("agents_t388/FACES_T388.csv")}
    art_rows = []
    for key in sorted(by_face):
        room, band, side = key
        a = by_face[key]
        e = face250.get(key)
        art = sum(a[k] for k in FR.CAUSES)
        vw = vrows.get(key, [])
        wall = vw[0] if len(vw) == 1 else "; ".join(vw)
        fr = f388.get(f"{room}|{wall}")
        top = A388.num(fr["tile_top_m"] or fr["plaster_top_m"]) if fr else None
        art_rows.append({
            "room": room, "band": band, "side": side,
            "walls (T-250)": "; ".join(sorted(e["walls"])) if e else "(no T-250 row)",
            **{f"{k}_m": R(a.get(k, 0.0), 3) for k in FR.CAUSES}, "corner_m (face)": R(a.get("CORNER", 0.0), 3),
            "t250_face_m": R(e["face_m"], 3) if e else None, "t250_virtual_m": R(e["virtual_m"], 3) if e else None,
            "corrected_face_m (face - artefact)": R(e["face_m"] - art, 3) if e else None,
            "t250_finish_m (WALL+COLUMN, unchanged)": R(e["finish_m"], 3) if e else None,
            "virtual_on_wall (T-250 row)": wall or "(none)",
            "t388_face_id": fr["face_id"] if fr else "(no T-388 face)",
            "_art": art, "_top": top, "_len": (A388.num(fr["length_m"]) if fr else None),
            "status": ("UNRESOLVED (open side on a face line inside the band: drawing check)" if a.get("ON_FACE_PARALLEL")
                       else "DRAWING-CONFIRMED (artefact named; Checker to re-measure)")})
    faces = {}
    for a in art_rows:
        fid = a["t388_face_id"]
        e = faces.setdefault(fid, {"t388_face_id": fid, "band_sides": 0, "artefact_m": 0.0, "corner_m (face)": 0.0,
                                   "t388_length_m": a["_len"], "top_m": a["_top"]})
        e["band_sides"] += 1
        e["artefact_m"] += a["_art"]
        e["corner_m (face)"] += a["corner_m (face)"]
    face_rows = []
    for fid in sorted(faces):
        e = faces[fid]
        art = R(e["artefact_m"], 3)
        face_rows.append({**e, "artefact_m": art, "corner_m (face)": R(e["corner_m (face)"], 3),
                          "corrected_length_m (R-T390-1 c)": (R(e["t388_length_m"] - art, 3)
                                                              if e["t388_length_m"] is not None else None),
                          "face_m2_at_owner_top (information; no BOQ line moves)": (R(art * e["top_m"], 4)
                                                                                    if e["top_m"] and art else None),
                          "status": ("CHANGED (artefact out)" if art > 0 else "UNCHANGED (corner VIRTUAL is face)")})
    for a in art_rows:
        for k in ("_art", "_top", "_len"):
            a.pop(k)
    return room_rows, art_rows, rooms, face_rows


def check(room_rows, art_rows, rooms):
    """the reproduction guards: the capture's open-side runs = the T-128 r3 walk's virtual_m (walk_r3.json) on every room; the artefact +
    corner metres on each band side = T-250's virtual_m there; every family closes under R-T390-1 except T-388's
    explained GF-16."""
    with open(RES / "agents_t128/walk_r3.json", encoding="utf-8") as fh:
        walk = json.load(fh)["rooms"]
    bad = []
    for room, r in rooms.items():
        if abs(r["open_m"] - walk[room]["virtual_m"]) > 0.006:
            bad.append(f"{room}: open side {r['open_m']} vs T-128 r3 walk {walk[room]['virtual_m']}")
    for a in art_rows:
        if a["t250_virtual_m"] is None:
            bad.append(f"{a['room']} {a['band']} {a['side']}: no T-250 row")
            continue
        tot = sum(a[f"{k}_m"] for k in FR.CAUSES) + a["corner_m (face)"]
        if abs(tot - a["t250_virtual_m"]) > 0.006:
            bad.append(f"{a['room']} {a['band']} {a['side']}: {tot} vs T-250 virtual {a['t250_virtual_m']}")
    opn = [r for r in room_rows if r["status"] == "OPEN"]
    bad += [f"{r['room']} {r['family']}: residual {r['residual_m (R-T390-1)']} m" for r in opn]
    return bad


def write(out, name, rows):
    with open(out / name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    C = pickle.load(open(a.capture, "rb"))
    room_rows, art_rows, rooms, face_rows = build(C)
    bad = check(room_rows, art_rows, rooms)
    cause_tot = {k: R(sum(r[f"{k}_m"] for r in art_rows), 3) for k in FR.CAUSES}
    summary = {
        "rooms": len(rooms), "family_rows": len(room_rows),
        "t388_residuals_over_tol": sum(1 for r in room_rows if abs(r["t388_residual_m"]) > FR.TOL_LEN_M),
        "r_t390_open": sum(1 for r in room_rows if r["status"] == "OPEN"),
        "r_t390_explained": sum(1 for r in room_rows if r["status"].startswith("EXPLAINED")),
        "band_sides_with_virtual": len(art_rows),
        "t388_faces_changed": sum(1 for f in face_rows if f["artefact_m"] > 0),
        "t388_faces_artefact_m": R(sum(f["artefact_m"] for f in face_rows), 3), "artefact_m_by_cause": cause_tot,
        "corner_virtual_on_faces_m": R(sum(r["corner_m (face)"] for r in art_rows), 3),
        "rooms_where_t388_face_differs": sorted({r["room"] for r in room_rows
                                                 if abs(r["t388_dprime_face_m"] - r["geometric_face_m (R-T390-1 a)"]) > 0.006}),
        "guards": "PASS" if not bad else bad}
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        write(out, "ROOM_FACE_T390.csv", room_rows)
        write(out, "ARTEFACT_T390.csv", art_rows)
        write(out, "T388_FACES_CORRECTED_T390.csv", face_rows)
        (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    if a.check and bad:
        raise SystemExit("check FAIL")


if __name__ == "__main__":
    main()
