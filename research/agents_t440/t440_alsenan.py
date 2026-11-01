"""T-440 on the development villa (P7757): the wet-pantry wall faces inside the GF open-room skirting line
L-71e2e002 (engine room GF-RC99C2A), face by face, with the engine's OWN edge roles (second route beside the T-315 r2
drawing-entity walk), the line's state in the candidate of record, the wall-tile line that owns each base, the T-431
addition kept apart, and the villa census of engine rooms that hold a tiled room only in part. Research only: nothing
is wired, no candidate or released quantity changes.

    python3 -I research/agents_t440/t440_alsenan.py --extract <P7757.dxf> <dir holding V3_0_38_BOQ_LINES.json>
    python3 -I research/agents_t440/t440_alsenan.py --write     (FACES_T440.csv + summary.json from the extract)
    python3 -I research/agents_t440/t440_alsenan.py --check     (rebuild from the committed extract, byte compare)

--extract runs the released ARCH_TAKEOFF_V2.9 on the plan with a read-only wrapper around
engine.source.arch_rooms._one_sided_roles (the engine function that sums a face's boundary by role) that records each
boundary edge's roles; nothing in the engine is edited. Committed: face ids, drawn handles, roles, metres, line ids,
states and quantities only (no coordinate, no name, no drawing content).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import wet_base_owner_v1 as W  # noqa: E402

EXTRACT = HERE / "EXTRACT_T440.json"
FACES = HERE / "FACES_T440.csv"
SUMMARY = HERE / "summary.json"

HOST_ROOM = "GF-RC99C2A"
HOST_LINE = "L-71e2e002a3af624097f0"
RANGE_LINE = "L-e7dcdc69e1a2b24f8616"
RC06_LINES = ("L-af6fb2d3474c5fbdb80a", "L-73ff85e30e3a8c639e20")
TILE_LINE = "L-f5c5a1a9c9ee2b644cb5"           # T-315 ADD: the pantry FIN.WALL.TILE line (6 faces)
ADD_ROOM = "GF-RFD4E1D"                         # T-427 / T-431: the dining face joined back (+3.90 lm)
BOX = {"west": "AE", "east": "B3", "south": "A6", "north": "158"}   # the printed 450 x 300 pantry box (T-286)
LAYERS = ("1", "S-COL.BON", "W")
ROLE_MAP = {"WALL": "WALL", "WALL_CAP": "WALL", "COLUMN": "COLUMN", "DOOR_THRESHOLD": "DOOR", "DOOR_CLOSURE": "DOOR",
            "PASSAGE_THRESHOLD": "PASSAGE", "ZONE_LINE": "ZONE", "WINDOW": "WINDOW", "WINDOW_THRESHOLD": "WINDOW"}
PANTRY = "GF-07"
ROOMS = {   # finish class by the answered owner rules (merged T-296 ROOMS_T296 / T-315 r2)
    PANTRY: {"finish_class": W.TILED, "tile_line": TILE_LINE,
             "class_source": "owner Q-37 A (pantry wet within its printed 4.50 x 3.00 box) + Q-48 A / UP-PANTRY-003 "
                             "(full-height wall tile); T-296 GF-07 NOT_APPLICABLE; T-315 r2 tile line"},
    "GF-08": {"finish_class": W.DRY, "tile_line": None, "class_source": "T-296 GF-08 DRY"},
}
T296_GF07_BASE_LM = 7.0     # merged T-296 ROOMS_T296 GF-07 base_wc_m (wall + column base of the pantry)
T315_RC06_BASE_LM = 1.9     # merged T-315 r2: GF-RC06FED line L-af6fb2d3 (now NOT_APPLICABLE)
T315_NO_LINE_LM = 1.6       # merged T-315 r2: pantry base on no engine room boundary (counter cells)


def _sha(p, n=8):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


# --------------------------------------------------------------------------------------------- extract (needs the run)
def _segments(doc):
    out = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t not in ("LINE", "LWPOLYLINE") or e.dxf.layer not in LAYERS:
            continue
        if t == "LINE":
            ss = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))]
        else:
            p = [tuple(x[:2]) for x in e.get_points("xy")]
            if e.closed:
                p.append(p[0])
            ss = list(zip(p, p[1:]))
        for a, b in ss:
            if math.dist(a, b) > 0:
                out.append((e.dxf.handle, ((a[0] * .001, a[1] * .001), (b[0] * .001, b[1] * .001))))
    return out


def _on(seg, a, b, tol=0.005):
    """length of edge a-b lying on drawn segment seg (parallel within tol, overlapping)."""
    (p, q) = seg
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    ex, ey = b[0] - a[0], b[1] - a[1]
    le = math.hypot(ex, ey)
    if le == 0 or abs(ux * ey - uy * ex) / le > 1e-3:
        return 0.0
    for c in (a, b):
        if abs(-uy * (c[0] - p[0]) + ux * (c[1] - p[1])) > tol:
            return 0.0
    ta = ux * (a[0] - p[0]) + uy * (a[1] - p[1])
    tb = ux * (b[0] - p[0]) + uy * (b[1] - p[1])
    lo, hi = max(min(ta, tb), 0.0), min(max(ta, tb), L)
    return max(hi - lo, 0.0)


def extract(dxf, cand_dir):
    sys.path.insert(0, str(ROOT))
    import ezdxf
    from engine.source import arch_rooms as AR
    from tools.urban_boq_m9 import arch_compute

    rec = {}
    orig = AR._one_sided_roles

    def wrapped(arr, cyc, unit_m):            # read-only: records each edge's roles, returns the engine's own result
        seen = Counter(ei for ei, _ in cyc)
        for ei, n in seen.items():
            e = arr.edges[ei]
            a = tuple(round(v * unit_m, 4) for v in arr.nodes[e["n0"]])
            b = tuple(round(v * unit_m, 4) for v in arr.nodes[e["n1"]])
            rec.setdefault(frozenset((a, b)), set()).update(e["roles"])
        return orig(arr, cyc, unit_m)

    AR._one_sided_roles = wrapped
    try:
        _, A, _ = arch_compute(str(dxf), method="ARCH_TAKEOFF_V2.9")
    finally:
        AR._one_sided_roles = orig
    doc = ezdxf.readfile(str(dxf))
    ent = doc.entitydb
    west, east = ent[BOX["west"]].dxf.start.x * .001, ent[BOX["east"]].dxf.start.x * .001
    south, north = ent[BOX["south"]].dxf.start.y * .001, ent[BOX["north"]].dxf.start.y * .001
    segs = _segments(doc)

    def in_box(m, tol=0.0005):
        return west - tol <= m[0] <= east + tol and south - tol <= m[1] <= north + tol

    def faces_of(room_id, keep):
        room = next(r for r in A["rooms"] if r["room_id"] == room_id)
        P = room["polygon_m"]
        out = []
        for i in range(len(P) - 1):
            a, b = tuple(P[i]), tuple(P[i + 1])
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if not keep(m):
                continue
            key = frozenset((tuple(round(v, 4) for v in a), tuple(round(v, 4) for v in b)))
            roles = sorted(rec.get(key, ()))
            hs = sorted({h for h, s in segs if _on(s, a, b) > 0.001}, key=lambda h: (len(h), h))
            mapped = sorted({ROLE_MAP.get(r, r) for r in roles})
            out.append({"edge": i, "engine_roles": roles, "role": mapped[0] if len(mapped) == 1 else "+".join(mapped),
                        "handles": " ".join(hs), "length_m": round(math.dist(a, b), 6)})
        return out, room

    pantry_faces, host = faces_of(HOST_ROOM, in_box)
    add_faces, add = faces_of(ADD_ROOM, lambda m: True)
    add_in_box = sum(1 for i in range(len(add["polygon_m"]) - 1)
                     if in_box(((add["polygon_m"][i][0] + add["polygon_m"][i + 1][0]) / 2,
                                (add["polygon_m"][i][1] + add["polygon_m"][i + 1][1]) / 2), tol=-0.0005))
    # candidate of record
    lines = json.loads((Path(cand_dir) / "V3_0_38_BOQ_LINES.json").read_text())
    lines = lines if isinstance(lines, list) else lines["lines"]
    want = (HOST_LINE, RANGE_LINE, TILE_LINE) + RC06_LINES
    cand = {}
    for ln in lines:
        if ln.get("line_id") in want:
            cand[ln["line_id"]] = {k: ln.get(k) for k in ("item_code", "unit", "evidence_state", "approval_state",
                                                          "gross", "measured_net", "bounded_range")}
            cand[ln["line_id"]]["deductions"] = [{k: d.get(k) for k in ("id", "face", "what", "lm", "qty", "source")
                                                  if k in d} for d in (ln.get("deductions") or [])]
            cand[ln["line_id"]]["room_id"] = (ln.get("location") or {}).get("room_id")
    out = {"drawing": {"P7757.dxf_sha256_8": _sha(dxf)},
           "candidate": {"file": "V3_0_38_BOQ_LINES.json", "sha256_8": _sha(Path(cand_dir) / "V3_0_38_BOQ_LINES.json"),
                         "lines": cand},
           "v29_host_runs_lm": host["runs_lm"], "v29_add_runs_lm": add["runs_lm"],
           "pantry_faces": pantry_faces, "addition_faces": add_faces, "addition_edges_inside_box": add_in_box}
    EXTRACT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


# --------------------------------------------------------------------------------------------------- build (no data)
TILED_SPLIT = "base_ownership_v3021.on_tiled_faces"   # the T-315 r2 deduction rows of the host line


def _named(x):
    """the host line's own deduction rows that take a pantry face off (T-315 r2): {handle: lm}."""
    host = x["candidate"]["lines"].get(HOST_LINE) or {}
    out = {}
    for d in host.get("deductions") or []:
        if TILED_SPLIT in str(d.get("source", "")):
            h = str(d.get("id", "")).rsplit("#", 1)[-1]
            out[h] = round(out.get(h, 0.0) + float(d.get("qty") or 0.0), 6)
    return out


def _carried(x, f, named):
    """lm of the face's base the host line still carries in the candidate: 0 when one of the line's own tiled-face
    deduction rows names a drawn handle the face lies on (and the rows close on the base in the box, checked in
    build); otherwise the whole face (the engine net is wall + column)."""
    if x["candidate"]["lines"].get(HOST_LINE) is None:
        return None
    if f["role"] not in W.BASE_ROLES:
        return 0.0
    return 0.0 if (x["pantry_part_off"] and set(f["handles"].split()) & set(named)) else f["length_m"]


def census():
    """villa census from the merged ledgers: an engine room that holds a FULL-HEIGHT-TILE room in part together with a
    room that is not tiled (each with a non-zero share of the engine room, T-262 'T128=a/b', b = share of the engine
    room). Only such an engine room's skirting line can carry a tiled base."""
    xw = list(csv.DictReader(open(ROOT / "research/agents_t262/ENGINE_ROOM_XWALK_T262.csv", encoding="utf-8")))
    r296 = {r["room"]: r for r in csv.DictReader(open(ROOT / "research/agents_t296/ROOMS_T296.csv", encoding="utf-8"))}
    out = []
    for r in xw:
        parts = []
        for p in r["T128_OVERLAPS"].split():
            if "=" in p:
                rid, sh = p.split("=")
                if float(sh.split("/")[1]) > 0.001:
                    parts.append(rid)
        tiled = [p for p in parts if r296.get(p, {}).get("finish_class") == W.TILED]
        if tiled and len(tiled) < len(parts):
            out.append({"engine_room": r["ENGINE_ROOM"], "t128": r["T128_OVERLAPS"], "tiled_in_part": tiled})
    return out


def _role(r):
    """one audit role per edge: an edge the engine gives two base roles (a column face flush with a wall face, split
    in halves by the engine) is a base edge either way; it is listed as COLUMN."""
    parts = set(r.split("+"))
    if len(parts) > 1 and parts <= set(W.BASE_ROLES):
        return "COLUMN"
    return r


def build(x):
    x = dict(x, pantry_faces=[dict(f, role=_role(f["role"])) for f in x["pantry_faces"]],
             addition_faces=[dict(f, role=_role(f["role"])) for f in x["addition_faces"]])
    host = x["candidate"]["lines"].get(HOST_LINE) or {}
    net, gross = host.get("measured_net"), host.get("gross")
    base_in_box = round(sum(f["length_m"] for f in x["pantry_faces"] if f["role"] in W.BASE_ROLES), 6)
    v29_net = round(x["v29_host_runs_lm"]["wall"] + x["v29_host_runs_lm"]["column"], 6)
    # the pantry part is off when the candidate net equals the V2.9 wall + column net less exactly the base faces
    named = _named(x)
    x = dict(x, pantry_part_off=(net is not None and abs((v29_net - base_in_box) - net) <= W.TOL_M
                                 and abs(sum(named.values()) - base_in_box) <= W.TOL_M))
    faces = []
    for f in x["pantry_faces"]:
        role = f["role"]
        faces.append({"face_id": f"{HOST_ROOM}#e{f['edge']:03d}", "line_id": HOST_LINE, "room": PANTRY,
                      "role": role, "length_m": f["length_m"], "handles": f["handles"],
                      "engine_roles": " ".join(f["engine_roles"])})
    for f in faces:
        f["carried_lm"] = _carried(x, f, named)
    aud = W.audit([{k: v for k, v in f.items() if k != "engine_roles"} for f in faces], ROOMS)
    for r, f in zip(aud["rows"], faces):
        r["engine_roles"] = f["engine_roles"]
    adds = [{"face_id": f"{ADD_ROOM}#e{f['edge']:03d}", "room": "GF-08", "role": f["role"]}
            for f in x["addition_faces"]]
    clos = W.closure(T296_GF07_BASE_LM, {"GF-RC06FED (T-315 r2)": T315_RC06_BASE_LM,
                                          "GF-RC99C2A in box (this walk)": base_in_box,
                                          "no engine room (T-315 r2)": T315_NO_LINE_LM})
    add_base = round(sum(f["length_m"] for f in x["addition_faces"] if f["role"] in W.BASE_ROLES), 6)
    summary = {
        "task": "T-440", "rule": W.RULE_ID, "method": W.METHOD, "drawing": x["drawing"], "candidate": x["candidate"],
        "host_line": HOST_LINE, "v29_host_net_wall_plus_column_lm": v29_net,
        "pantry_base_in_host_lm": base_in_box, "candidate_host_net_lm": net, "candidate_host_gross_lm": gross,
        "v29_net_minus_pantry_base_lm": round(v29_net - base_in_box, 6), "pantry_part_off_in_candidate": x["pantry_part_off"],
        "host_tiled_face_deductions_lm": named, "host_tiled_face_deductions_sum_lm": round(sum(named.values()), 6),
        "over_count_lm": aud["over_count_lm"], "unknown_faces": aud["unknown_faces"],
        "window_W09_on_range_line": {k: x["candidate"]["lines"].get(RANGE_LINE, {}).get(k)
                                     for k in ("evidence_state", "bounded_range")},
        "rc06fed_lines": {k: (x["candidate"]["lines"].get(k) or {}).get("evidence_state") for k in RC06_LINES},
        "tile_line": {"line_id": TILE_LINE, **{k: (x["candidate"]["lines"].get(TILE_LINE) or {}).get(k)
                                                for k in ("item_code", "unit", "evidence_state", "measured_net")}},
        "closure_gf07_base": clos,
        "t431_addition": {"room": ADD_ROOM, "v29_runs_lm": x["v29_add_runs_lm"], "base_lm": add_base,
                          "edges_inside_pantry_box": x["addition_edges_inside_box"],
                          "flags": W.additions_clear(adds, ROOMS)},
        "census_partial_tiled_engine_rooms": census(),
    }
    buf = io.StringIO()
    cols = ["face_id", "line_id", "room", "role", "engine_roles", "handles", "length_m", "finish_class", "base_lm",
            "carried_lm", "owner", "over_lm", "status"]
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in aud["rows"]:
        w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})
    table = buf.getvalue()
    summary["faces_csv_sha256_8"] = hashlib.sha256(table.encode()).hexdigest()[:8]
    return table, json.dumps(summary, indent=1, sort_keys=True) + "\n"


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1], argv[2])
        return 0
    x = json.loads(EXTRACT.read_text())
    table, summ = build(x)
    if argv[:1] == ["--write"]:
        FACES.write_text(table)
        SUMMARY.write_text(summ)
        print(summ)
        return 0
    if argv[:1] == ["--check"]:
        ok = FACES.read_text() == table and SUMMARY.read_text() == summ
        print("T-440 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
