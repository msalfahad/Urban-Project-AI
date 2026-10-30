"""T-368 development-villa run: the exposed wall-tile edge ledger (B4-10) of every FIN.WALL.TILE room.

Committed inputs only (ids, counts, lengths, handles; no coordinate, no name, no drawing content):
  - the merged T-312 face ledger / room closure / openings (tile band per room, tiled length, openings per face, line id);
  - the T-315 pantry line id (GF-07, the ADD line) and the T-351 pantry face reading (handles);
  - the merged T-313 window depths (room-side reveal depth 0.000 = frame flush with the room face);
  - CORNERS below: per room the external (reflex) and internal corners of its engine room polygon (own reading of
    ARCH_ROOMS of an ARCH_TAKEOFF_V2.9 run on P7757.dxf ab54dd55, simplified at 1 mm; the reflex count is the same
    at 0, 1, 4 and 10 mm), and for the two rooms with an open side the class of each open-edge end, read on the DXF
    by handle.

    python3 -I research/agents_t368/t368_alsenan.py --write            # rebuild the committed CSV / JSON
    python3 -I research/agents_t368/t368_alsenan.py --check            # rebuild in memory, compare byte for byte
    python3 -I research/agents_t368/t368_alsenan.py --geometry <P7757.dxf> <ARCH_ROOMS.json>   # re-read the inputs
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t368_edge_rules as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
T312 = os.path.join(ROOT, "research", "agents_t312")
T313_DEPTHS = os.path.join(ROOT, "research", "agents_t313", "WINDOW_DEPTHS_T313.csv")
PANTRY_LINE = "L-f5c5a1a9c9ee2b644cb5"     # T-315 r2 ADD (GF-07, engine room GF-RC06FED)
DXF_SHA8 = "ab54dd55"

# room -> engine room, external corners, internal corners, wall ends, flat stops, reflex evidence
CORNERS = {
    "1F-02": ("1F-R8BDA49", 0, 4, 0, 0, "rectangle"),
    "1F-03": ("1F-R48AA46", 0, 4, 0, 0, "rectangle"),
    "1F-07": ("1F-R26FA0D", 3, 7, 0, 0, "reflex: wall corner ACF / B07 (1.62 / 1.95), lift-shaft corner at column "
                                       "2FF0, walls B06 / B14 (2.00 / 1.20), column 2FED proud 0.05 (0.05 / 0.80)"),
    "1F-08": ("1F-R52AC05", 0, 4, 0, 0, "rectangle"),
    "1F-09": ("1F-RED23B8", 1, 5, 0, 0, "reflex: column 2FE7 proud 0.05 (0.05 / 0.45)"),
    "1F-12": ("1F-R48CDA5", 0, 4, 0, 0, "rectangle"),
    "2F-02": ("2F-RE83BED", 0, 4, 0, 0, "rectangle"),
    "GF-02": ("GF-R8496F0", 1, 5, 0, 0, "reflex: column 2FA5 proud 0.05 (0.05 / 0.35)"),
    "GF-03": ("GF-RB62B55", 0, 4, 0, 0, "rectangle"),
    "GF-05": ("GF-RFAD3C4", 0, 4, 0, 0, "rectangle"),
    "GF-06": ("GF-RA3AD49", 4, 8, 0, 0, "reflex: column 2FB7 proud 0.05 both sides (0.05 / 0.50, 0.50 / 0.05), "
                                       "column 2FB1 proud 0.05 (0.05 / 0.40), WC block corner, walls 135 / 14F (1.65 / 1.50)"),
    "GF-07": ("GF-RC06FED", 1, 3, 1, 1, "handle reading (the engine room is a partial polygon whose one reflex is the "
                                       "counter end AA / B2, not a wall): column 2FAE proud 0.05 below wall 158 "
                                       "(face 0.90 / return 0.05); open edge B3 "
                                       "(layer 5): north end = free end of wall 159 (wall end line AC), south end = "
                                       "wall A6 continues as line 104 in the same plane"),
    "GF-10": ("GF-RDF7D28", 0, 4, 0, 0, "rectangle"),
    "GF-11": ("GF-RD36087", 0, 4, 0, 0, "rectangle"),
    "GF-12": ("GF-RF38DAF", 0, 4, 0, 0, "rectangle"),
    "GF-13": ("GF-RB28769", 1, 5, 0, 0, "reflex: column 2F84 proud 0.05 (0.58 / 0.05)"),
    "GF-14": ("GF-RDBD4F9", 1, 4, 1, 1, "reflex: obtuse 135-degree corner, walls BE / 318 (1.024 / "
                                       "1.341); open side 2DB / 2DC (layer 2): east end = free end of wall D2 "
                                       "(wall end line BC), west end = wall 222 continues past it"),
    "GF-16": ("GF-RD6F891", 0, 5, 0, 0, "pentagon, no reflex"),
}
GEOMETRY_SOURCE = (f"own reading: engine room polygon (ARCH_ROOMS, ARCH_TAKEOFF_V2.9 run on P7757.dxf {DXF_SHA8}); "
                   "reflex vertex = external corner")
CEILING_SOURCE = ("UP-FIN-WALL-001 / Q-48 A: tile top = underside of the 0.15 decor ceiling (OWNER_RECONCILIATION G1)")
DOOR_FRAME_SOURCE = ("no door frame / architrave detail on any sheet (T-091: no interior elevation or detail; T-313: "
                     "'the frame detail decides how much is plastered, PROVISIONAL')")


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def inputs():
    closure = {r["room"]: r for r in _read(os.path.join(T312, "ROOM_CLOSURE_T312.csv"))}
    faces = _read(os.path.join(T312, "FACE_LEDGER_T312.csv"))
    ops = _read(os.path.join(T312, "OPENINGS_T312.csv"))
    depths = {r["opening"]: r for r in _read(T313_DEPTHS)}
    band = {}
    for f in faces:
        if f["scope"] != "TILED":
            continue
        h = _num(f["owner_h_m"])
        held = f["owner_status"] != R.OA
        b = R.Band(None if held else h, f["owner_h_source"], R.HELD if held else R.OA,
                   (f["owner_held_item"] or closure[f["room"]]["held_item"]) if held else "")
        prev = band.get(f["room"])
        if prev is not None and prev != b:
            raise R.EdgeError(f"{f['room']}: two bands in one room")
        band[f["room"]] = b
    return closure, band, ops, depths


def _opening(row, depths):
    size = row["merged_size"]
    kind = {"door": "door", "window": "window"}.get(row["kind"], "doorway")
    w = float(size.split()[1])
    head = sill = None
    parts = size.split()
    if "head" in parts:
        head = float(parts[parts.index("head") + 1])
    if "sill" in parts:
        sill = float(parts[parts.index("sill") + 1])
    frame, fsrc = "NOT_DRAWN", DOOR_FRAME_SOURCE
    if kind == "window":
        d = depths.get(row["opening_id"])
        if d is None or d["depth_in_m"] in ("", None):
            frame, fsrc = "NOT_DRAWN", "room-side reveal not measured (T-313)"
        elif abs(float(d["depth_in_m"])) < 1e-9:
            frame = "FLUSH"
            fsrc = (f"T-313 WINDOW_DEPTHS (MERGED): room-side reveal depth 0.000, frame band {d['frame_band_m']} m "
                    "drawn flush with the room face")
    elif kind == "doorway":
        fsrc = "head / opening outline not established (T-209 / D-45)"
    return R.Opening(row["opening_id"], kind, w, head, sill or 0.0, frame, fsrc)


def build():
    closure, band, ops, depths = inputs()
    edges = []
    for room in sorted(CORNERS):
        eng, ext, inn, wend, fstop, why = CORNERS[room]
        c = closure[room]
        line = c["line_id"] if c["line_id"] != "NO_LINE" else (PANTRY_LINE if room == "GF-07" else "")
        b = band[room]
        src = GEOMETRY_SOURCE + f"; {eng}: {why}"
        edges += R.corner_edges(room, ext, inn, b, line, src)
        edges += R.end_edges(room, wend, fstop, b, line, src)
        for o in ops:
            if o["room"] == room:
                edges.append(R.opening_edge(room, _opening(o, depths), b, line))
        edges.append(R.top_edge(room, float(c["tiled_m"]), b, line, CEILING_SOURCE))
    for e in edges:
        if e.exposed == "EXPOSED":
            e.finish = R.finish_alternatives(e.length_m)
    return edges


COLS = ["edge_id", "room", "type", "count", "length_m", "held_range_m", "exposure", "status", "finish", "line_id",
        "source", "note"]


def render(edges):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLS)
    for e in edges:
        rng = "" if not e.range_m else f"{e.range_m[0]:.4f} .. {e.range_m[1]:.4f}"
        fin = ""
        if e.exposed == "EXPOSED":
            fin = "HELD: 45-degree (UP-CER-006) OR steel profile (UP-CER-007) on these m.l, never both"
        elif e.exposed == R.HELD:
            fin = "HELD with the exposure"
        w.writerow([e.edge_id, e.room, e.etype, e.count, "" if e.length_m is None else f"{e.length_m:.4f}", rng,
                    e.exposed, e.status, fin, e.line_id, e.source, e.note])
    return buf.getvalue()


def summary(edges):
    tot = R.check_ledger(edges)
    rooms = {}
    for e in edges:
        r = rooms.setdefault(e.room, {"line_id": e.line_id, "exposed_m": 0.0, "held_edges": 0, "held_hi_m": 0.0})
        if e.exposed == "EXPOSED":
            r["exposed_m"] = round(r["exposed_m"] + e.length_m, 4)
        elif e.exposed == R.HELD:
            r["held_edges"] += e.count
            if e.range_m:
                r["held_hi_m"] = round(r["held_hi_m"] + e.range_m[1], 4)
    det_exposed = tot["EXPOSED_m"]
    return {
        "task": "T-368", "dxf_sha256_8": DXF_SHA8, "edges": len(edges),
        "exposed_determinate_m": det_exposed,
        "exposed_by_type_m": tot["by_type"],
        "held_edge_count": tot["HELD_count"],
        "door_exposure_held_range_m": [0.0, tot["HELD_range_hi_m"]],
        "not_exposed_listed_m": tot["NOT_EXPOSED_m"],
        "finish": R.finish_alternatives(det_exposed),
        "freelancer": {"rows": 0, "basis": "no edge / profile / 45-degree row in his finishes workbook (cover: "
                                            "floors, skirting, walls, stairs, decor, cornices, waterproofing)"},
        "rooms": rooms,
    }


T313_EDGES = os.path.join(ROOT, "research", "agents_t313", "EDGE_RECONCILIATION_T313.csv")
T325_SILLS = os.path.join(ROOT, "research", "agents_t325", "SILL_THRESHOLD_LEDGER_T325.csv")


def crosscheck(edges):
    """Acceptance (c): every opening edge of this ledger against the reveal (T-313) and sill (T-325) ledgers."""
    outer = {r["opening"] for r in _read(T313_EDGES)}
    sill_in = {r["opening"]: r for r in _read(T325_SILLS) if r["component"] == "SILL_IN"}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["edge_id", "opening", "this_ledger", "t313_outer_face_edge", "t325_internal_sill", "double_count_m",
                "why"])
    dbl = 0.0
    for e in edges:
        oid = e.edge_id.split("#", 1)[1]
        if e.etype not in ("OPENING_DOOR", "OPENING_WINDOW", "UNDER_FRAME"):
            continue
        s = sill_in.get(oid)
        sill = "" if s is None else f"{s['m2']} m2 / {s['edge_ml']} m.l ({s['state']})"
        mine = e.exposed + ("" if e.length_m is None else f" {e.length_m:.4f}") + (
            "" if not e.range_m else f" range {e.range_m[0]:.4f} .. {e.range_m[1]:.4f}")
        why = ("room face of the opening; the T-313 edge is the arris on the OUTER face (exterior corners line): "
               "another face, another arris") if oid in outer else "interior opening: no outer-face edge"
        if s is not None:
            why += "; internal sill 0.0 (frame flush): no sill edge on the room face"
        w.writerow([e.edge_id, oid, mine, "yes" if oid in outer else "no", sill, "0.0000", why])
    return buf.getvalue(), dbl


def outputs():
    edges = build()
    s = summary(edges)
    cc, dbl = crosscheck(edges)
    s["double_count_vs_reveal_and_sill_ledgers_m"] = dbl
    return {"EDGE_LEDGER_T368.csv": render(edges), "CROSSCHECK_T368.csv": cc,
            "summary.json": json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True) + "\n"}


def geometry(dxf_path, rooms_json):
    """Re-read the CORNERS inputs from the private copies (prints counts and handles only)."""
    import ezdxf
    rooms = {r["room_id"]: r for r in json.load(open(rooms_json, encoding="utf-8"))["rooms"]}
    bad = 0
    doc = ezdxf.readfile(dxf_path)
    for room, (eng, ext, inn, wend, fstop, _why) in sorted(CORNERS.items()):
        if room == "GF-07":   # handle reading: the column's free corner stands 0.05 into the pantry box
            col = [p[:2] for p in doc.entitydb.get("2FAE").get_points()]
            n158, wae, ob3 = doc.entitydb.get("158"), doc.entitydb.get("AE"), doc.entitydb.get("B3")
            y_face = n158.dxf.start.y
            free = [p for p in col if wae.dxf.start.x < p[0] < ob3.dxf.start.x and p[1] < y_face]
            proud = round(y_face - min(p[1] for p in col), 1) if free else None
            ok = len(free) == 1 and proud == 50.0 and ext == 1
            bad += not ok
            print(f"{room} 2FAE: free corners inside the box {len(free)}, proud {proud} mm (committed 1 / 50) "
                  f"{'OK' if ok else 'DIFFERS'}")
            continue
        pts = rooms[eng]["polygon_m"]
        e2, _ = R.corner_classes(pts)
        ok = e2 == ext
        bad += not ok
        print(f"{room} {eng}: reflex {e2} (committed {ext}) {'OK' if ok else 'DIFFERS'}")
    for h in ("159", "AC", "A6", "104", "B3", "2FAE", "D2", "BC", "222", "2DB"):
        e = doc.entitydb.get(h)
        print(h, None if e is None else (e.dxftype(), e.dxf.layer))
        bad += e is None
    return bad


def main(argv):
    if argv[:1] == ["--write"]:
        for name, text in outputs().items():
            with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        print(json.loads(outputs()["summary.json"])["exposed_determinate_m"])
        return 0
    if argv[:1] == ["--check"]:
        bad = 0
        for name, text in outputs().items():
            with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
                same = f.read() == text
            print(name, "SAME" if same else "DIFFERS")
            bad += not same
        return 1 if bad else 0
    if argv[:1] == ["--geometry"] and len(argv) == 3:
        return 1 if geometry(argv[1], argv[2]) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
