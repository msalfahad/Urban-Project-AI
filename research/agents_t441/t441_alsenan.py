"""T-441 on the development villa (P7757): the floor-level wall-face length of the three stair-room floor parts that
T-418 / T-421 added (GF stair hall +1.00 4.8050 m2, GF back lobby +0.30 1.3225 m2, 2F stair lobby 2.5000 m2) and, for
completeness, of the 2F arrival (B7 marble, skirting B3-06 room skirting per T-410 s.3), measured stretch by stretch
with STAIR_ROOM_SKIRTING_V1. Research only: nothing is wired, no candidate or released quantity changes.

    python3 -I research/agents_t441/t441_alsenan.py --extract <P7757.dxf> <dir holding V3_0_38_BOQ_LINES.json>
    python3 -I research/agents_t441/t441_alsenan.py --write     (FACES_T441.csv + summary.json from the extract)
    python3 -I research/agents_t441/t441_alsenan.py --check     (rebuild from the committed extract, byte compare)

Geometry: room-LOCAL metres (origin = the stair room's south-west inner corner, north = +y; the same frames as T-418
and the engine's V2.9 room polygons GF-R31F8AE / 2F-R4D1B62). --extract re-reads every handle named below on the
architectural DXF (Drive 'Alsenan chalet project', P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55) and checks
that the drawn lines cover each WALL / COLUMN stretch, that each opening is a gap in the wall line, and records the
candidate of record's lines on the two stair rooms. Committed: handles, room-local lengths, line ids, states and
quantities only (no world coordinate, no name, no drawing text).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stair_room_skirting_v1 as S  # noqa: E402

EXTRACT = HERE / "EXTRACT_T441.json"
FACES = HERE / "FACES_T441.csv"
SUMMARY = HERE / "summary.json"
CANDIDATE = "ARCH_TAKEOFF_V3.0.38"
CANDIDATE_SHA = "57cca61c9fbfc96807af52ee232bc182126b3621170db7db264192bba55cfc31"   # T-421 summary_t421.json
DXF_SHA8 = "ab54dd55"
# room-local origin = the room's south-west inner corner = x of the west wall face line, y of the south wall face line
# (read from the DXF at extract time; the same corner as the engine's V2.9 room polygon and T-418's frame)
ORIGIN_FROM = {"GF": ("298", "220"), "2F": ("12B7", "1282")}
ORIGIN_MM = {}
LINES = {   # candidate lines on the two stair rooms (T-435 join, T-296 ledger, T-418 / T-421)
    "L-47fa825d197d32754240": "GF stair hall skirting (parent, BLOCKED_RFI)",
    "L-b8d4a7f04277deb1b0b0": "2F stair hall skirting (parent, BLOCKED_RFI)",
    "L-2175a965": "GF stairwell ceiling (parent)",
    "L-dd6930fd": "2F stair hall ceiling (parent)",
    "L-10e79bd4": "2F stair hall ceiling decor part",
}
ROOMS = ("GF-R31F8AE", "2F-R4D1B62")

# --------------------------------------------------------------------------------------------- the stretch tables
HIDDEN = ("divider band at the cut starts at y 1.05 (layer 5 155 / 4A4 / 157); between y 0.45 and 1.05 only the "
          "hidden layer-2 outline 47C / 47E / 499 is drawn (the 1F band above), with single lines 2C8 (layer 5, x 1.20) "
          "/ 2C9 (layer 2, x 1.15) and the diagonal pair 2F1D / 2F1E in the south-west box; T-418 classed 0.45 .. 1.05 "
          "SOLID: whether a face stands here is not established")
GUARD = ("solid stair band between MS1-L and D1 (layer 5 4A4 / 157, rail band 151 / 47F; T-393 'GF band 157 / 151 "
         "solid to the cut', railings RL-07 MS1-L / RL-08): a guard upstand or a wall face, finish not printed; "
         "skirting along a railing / void edge is defect B12 (L-18) territory, so held, never assumed")


def gf_hall():
    return {"id": "GF-ST-HALL", "room": "GF-R31F8AE", "level": 1.00, "area_m2": 4.8050, "sides": [
        {"id": "S", "line": "GF:y=0", "t0": 0.0, "dir": 1, "length": 2.5, "stretches": [
            {"s0": 0.0, "s1": 1.4, "kind": "WALL", "handles": "220"},
            {"s0": 1.4, "s1": 2.4, "kind": "DOOR", "opening_id": "OP-010",
             "note": "door to the open room, wall gap 1.000 (door block D120, insert 2C7)"},
            {"s0": 2.4, "s1": 2.5, "kind": "WALL", "handles": "21F"}]},
        {"id": "E", "line": "GF:x=2.5", "t0": 0.0, "dir": 1, "length": 2.95, "stretches": [
            {"s0": 0.0, "s1": 2.0, "kind": "WALL", "handles": "21C",
             "note": "columns 2F90 (y -0.2 .. 0.3) and 2F93 (1.5 .. 2.0) flush with the wall face (engine COLUMN+WALL)"},
            {"s0": 2.0, "s1": 2.9, "kind": "PASSAGE", "opening_id": "OP-020",
             "note": "doorless opening to the wet wash space GF-RD36087 (wall ends 218 / 4AA, head 33C / 33D hidden)"},
            {"s0": 2.9, "s1": 2.95, "kind": "WALL", "handles": "21B"}]},
        {"id": "D1-TOP", "line": "GF:y=2.95", "t0": 2.5, "dir": -1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "OPEN", "note": "D1 top nosing 490: the flight (B7)"}]},
        {"id": "DIV-E", "line": "GF:x=1.35", "t0": 2.95, "dir": -1, "length": 2.5, "stretches": [
            {"s0": 0.0, "s1": 1.9, "kind": "GUARD_HELD", "cause": GUARD},
            {"s0": 1.9, "s1": 2.5, "kind": "HELD", "cause": HIDDEN, "candidate_lm": 0.6}]},
        {"id": "DIV-END", "line": "GF:y=0.45", "t0": 1.35, "dir": -1, "length": 0.2, "stretches": [
            {"s0": 0.0, "s1": 0.2, "kind": "GUARD_HELD", "cause": GUARD + "; the band end, at y 0.45 (T-418) or "
             "1.05 (cut outline 155)"}]},
        {"id": "DIV-W", "line": "GF:x=1.15", "t0": 0.45, "dir": 1, "length": 0.7, "stretches": [
            {"s0": 0.0, "s1": 0.6, "kind": "HELD", "cause": HIDDEN, "candidate_lm": 0.6},
            {"s0": 0.6, "s1": 0.7, "kind": "GUARD_HELD", "cause": GUARD}]},
        {"id": "MS1L-FOOT", "line": "GF:y=1.15", "t0": 1.15, "dir": -1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "OPEN", "note": "MS1-L first riser DE (layer 2) / nosing DC (layer 5): "
             "the flight (B7)"}]},
        {"id": "W", "line": "GF:x=0", "t0": 1.15, "dir": -1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 0.05, "kind": "STAIR_SIDE", "flight": "T-410 MS1-L.W1",
             "note": "wall 298 under the first nosing (y 1.10 .. 1.15): T-410 starts MS1-L.W1 at the nosing DC"},
            {"s0": 0.05, "s1": 1.15, "kind": "WALL", "handles": "298"}]},
    ], "jambs": [
        {"id": "OP-020.J-S", "opening_id": "OP-020", "depth": 0.2, "status": S.HELD,
         "cause": "passage jamb return (column 2F93 north face), URBAN-SKIRTING-OPENING-METHOD would add it "
                  "PROVISIONAL; the reveal opens onto the WET full-height-tiled GF-RD36087 (T-296 GF-11): wall tile "
                  "or skirting owner of the reveal not printed"},
        {"id": "OP-020.J-N", "opening_id": "OP-020", "depth": 0.2, "status": S.HELD,
         "cause": "passage jamb return (wall end 4AA), same as J-S"}]}


def gf_lobby():
    return {"id": "GF-ST-LOBBY030", "room": "GF-R31F8AE", "level": 0.30, "area_m2": 1.3225, "sides": [
        {"id": "S", "line": "GF:y=3.85", "t0": 1.35, "dir": 1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "OPEN", "note": "D1 bottom nosing 481: the flight (B7)"}]},
        {"id": "E", "line": "GF:x=2.5", "t0": 3.85, "dir": 1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "WALL", "handles": "21B",
             "note": "column 2F81 (y 4.7 .. 5.2) flush (engine COLUMN+WALL)"}]},
        {"id": "N", "line": "GF:y=5", "t0": 2.5, "dir": -1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 0.1469, "kind": "WALL", "handles": "26F 2AC"},
            {"s0": 0.1469, "s1": 1.0469, "kind": "DOOR", "opening_id": "OP-013",
             "note": "door to the north court, wall gap 0.900 (layer 5 3FD / layer 2 3FE; door block D120 3FF on layer "
                     "S-COL.BON, a layer slip)"},
            {"s0": 1.0469, "s1": 1.15, "kind": "WALL", "handles": "2AB"}]},
        {"id": "W", "line": "GF:x=1.35", "t0": 5.0, "dir": -1, "length": 1.15, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "UNKNOWN", "candidate_lm": 1.15,
             "cause": "no face drawn on layer 1 / 5 / S-COL.BON on x 1.35 (only hidden layer-2 lines 49C / 2C6 x 1.25, "
                      "49D x 1.30, the band above); west of it the T-418 strip GF-ST-CN (UNREAD, 0 .. 0.230 m2) and the "
                      "space under the MS1-T winders at +0.30: open or enclosed is not drawn, so the face may stand at "
                      "x 1.35, at x 1.15 or further west"}]}]}


def f2_lobby():
    return {"id": "2F-ST-LOBBY", "room": "2F-R4D1B62", "level": 9.70, "area_m2": 2.5000, "sides": [
        {"id": "S", "line": "2F:y=0", "t0": 2.5, "dir": 1, "length": 2.0, "stretches": [
            {"s0": 0.0, "s1": 2.0, "kind": "WALL", "handles": "1283"}]},
        {"id": "E", "line": "2F:x=4.5", "t0": 0.0, "dir": 1, "length": 1.25, "stretches": [
            {"s0": 0.0, "s1": 0.1016, "kind": "WALL", "handles": "1295"},
            {"s0": 0.1016, "s1": 1.0016, "kind": "DOOR", "opening_id": "OP-007",
             "note": "maid-room door, wall gap 0.900 (door block d220, insert 12C2)"},
            {"s0": 1.0016, "s1": 1.25, "kind": "WALL", "handles": "1294"}]},
        {"id": "N", "line": "2F:y=1.25", "t0": 4.5, "dir": -1, "length": 2.0, "stretches": [
            {"s0": 0.0, "s1": 0.4, "kind": "WALL", "handles": "1289"},
            {"s0": 0.4, "s1": 1.4, "kind": "LIFT_OPENING", "opening_id": "OP-002",
             "note": "lift landing ELV-01-2F, 1.000 clear between jambs 12AE / 12AF (T-413); the engine classes it "
                     "PASSAGE (V2.9 kind PASSAGE to 2F-R2BDCEE)"},
            {"s0": 1.4, "s1": 2.0, "kind": "WALL", "handles": "128A",
             "note": "column 2F72 (x 2.5 .. 2.7) flush with the face (engine COLUMN+WALL)"}]},
        {"id": "W", "line": "2F:x=2.5", "t0": 1.25, "dir": -1, "length": 1.25, "stretches": [
            {"s0": 0.0, "s1": 1.25, "kind": "OPEN", "note": "continues into the arrival 2F-ST-ARRIVAL (B7, Q-70 A)"}]}]}


def f2_arrival():
    return {"id": "2F-ST-ARRIVAL", "room": "2F-R4D1B62", "level": 9.70, "area_m2": 4.8750, "sides": [
        {"id": "S", "line": "2F:y=0", "t0": 0.0, "dir": 1, "length": 2.5, "stretches": [
            {"s0": 0.0, "s1": 0.4158, "kind": "WALL", "handles": "1282"},
            {"s0": 0.4158, "s1": 1.4158, "kind": "DOOR", "opening_id": "OP-001",
             "note": "door, wall gap 1.000 (door block D115, insert 12BA)"},
            {"s0": 1.4158, "s1": 2.5, "kind": "WALL", "handles": "1283"}]},
        {"id": "E", "line": "2F:x=2.5", "t0": 0.0, "dir": 1, "length": 1.95, "stretches": [
            {"s0": 0.0, "s1": 1.25, "kind": "OPEN", "note": "continues into the lobby 2F-ST-LOBBY"},
            {"s0": 1.25, "s1": 1.75, "kind": "COLUMN", "handles": "2F72 129A"},
            {"s0": 1.75, "s1": 1.95, "kind": "WALL", "handles": "129A"}]},
        {"id": "N", "line": "2F:y=1.95", "t0": 2.5, "dir": -1, "length": 2.5, "stretches": [
            {"s0": 0.0, "s1": 1.15, "kind": "OPEN", "note": "top of flight MS2-U (T-418 east-lane foot strip, B7)"},
            {"s0": 1.15, "s1": 2.5, "kind": "OPEN", "note": "slab-opening edge over the 1F-2F flights (T-129 O-2F; "
             "guard RL-07 G-2F 1.325)"}]},
        {"id": "W", "line": "2F:x=0", "t0": 1.95, "dir": -1, "length": 1.95, "stretches": [
            {"s0": 0.0, "s1": 1.95, "kind": "WALL", "handles": "12B7"}]}]}


# merged T-410 side table stretches on the same wall lines (stations re-expressed in the room-local frames; levels
# from T-184 / T-410): the floor parts may not share plan and level with any of them (R-T441-2)
FLIGHT_STRETCHES = [
    {"id": "T-410 MS1-L.W1", "line": "GF:x=0", "t0": 1.10, "t1": 2.75, "lo": 1.00, "hi": 2.667},
    {"id": "T-410 MS1-L.W (window)", "line": "GF:x=0", "t0": 2.75, "t1": 3.80, "lo": 1.00, "hi": 2.667},
    {"id": "T-410 MS1-T west", "line": "GF:x=0", "t0": 3.80, "t1": 5.00, "lo": 2.667, "hi": 3.50},
    {"id": "T-410 MS1-T north", "line": "GF:y=5", "t0": 0.00, "t1": 1.15, "lo": 2.667, "hi": 3.50},
    {"id": "T-410 D1 east", "line": "GF:x=2.5", "t0": 2.95, "t1": 3.85, "lo": 0.30, "hi": 1.00},
    {"id": "T-410 MS1-LD east", "line": "GF:x=2.5", "t0": 3.85, "t1": 5.00, "lo": 3.50, "hi": 3.50},
    {"id": "T-410 MS1-LD north", "line": "GF:y=5", "t0": 1.35, "t1": 2.50, "lo": 3.50, "hi": 3.50},
    {"id": "T-410 MS1-U east", "line": "GF:x=2.5", "t0": 0.55, "t1": 3.85, "lo": 3.50, "hi": 5.50},
]
LIFT_BAND_2F = {"opening_id": "OP-002", "edge_handles": ["12AE", "12AF", "12B3", "12B0"]}


def parts():
    return [gf_hall(), gf_lobby(), f2_lobby(), f2_arrival()]


# --------------------------------------------------------------------------------------------- extract (needs DXF)
def _sha(p, n=8):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


def _local(fl, p):
    o = ORIGIN_MM[fl]
    return ((p[0] - o[0]) / 1000.0, (p[1] - o[1]) / 1000.0)


def _line_axis(line):
    fl, eq = line.split(":")
    ax, v = eq.split("=")
    return fl, ax, float(v)


def extract(dxf, cand_dir):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    db = doc.entitydb
    for fl, (hx, hy) in ORIGIN_FROM.items():
        ORIGIN_MM[fl] = (float(db[hx].dxf.start.x), float(db[hy].dxf.start.y))
    checks = []
    for sp in parts():
        for sd in sp["sides"]:
            fl, ax, v = _line_axis(sd["line"])
            for st in sd["stretches"]:
                t0 = sd["t0"] + sd["dir"] * st["s0"]
                t1 = sd["t0"] + sd["dir"] * st["s1"]
                lo, hi = min(t0, t1), max(t0, t1)
                if st["kind"] in S.FACE:
                    cov = []
                    for h in st["handles"].split():
                        e = db[h]
                        segs = []
                        if e.dxftype() == "LINE":
                            segs = [(_local(fl, e.dxf.start), _local(fl, e.dxf.end))]
                        else:
                            pts = [_local(fl, q[:2]) for q in e.get_points("xy")]
                            if e.closed:
                                pts.append(pts[0])
                            segs = list(zip(pts, pts[1:]))
                        for a, b in segs:
                            i, j = (0, 1) if ax == "x" else (1, 0)
                            if abs(a[i] - v) < 0.002 and abs(b[i] - v) < 0.002:
                                cov.append((min(a[j], b[j]), max(a[j], b[j])))
                    cov.sort()
                    got, cur = 0.0, lo
                    for a, b in cov:
                        a, b = max(a, cur), min(b, hi)
                        if b > a:
                            got += b - a
                            cur = b
                    checks.append({"part": sp["id"], "side": sd["id"], "s0": st["s0"], "kind": st["kind"],
                                   "handles": st["handles"], "stretch_m": round(hi - lo, 4),
                                   "drawn_cover_m": round(float(got), 4), "agree": bool(abs(got - (hi - lo)) <= 0.002)})
                elif st["kind"] in S.OPENINGS:
                    # the wall line must be broken: no layer-1 line lies on it inside the opening
                    inside = 0.0
                    for e in doc.modelspace().query("LINE[layer=='1']"):
                        a, b = _local(fl, e.dxf.start), _local(fl, e.dxf.end)
                        i, j = (0, 1) if ax == "x" else (1, 0)
                        if abs(a[i] - v) < 0.002 and abs(b[i] - v) < 0.002:
                            inside += max(0.0, min(max(a[j], b[j]), hi - 0.002) - max(min(a[j], b[j]), lo + 0.002))
                    checks.append({"part": sp["id"], "side": sd["id"], "s0": st["s0"], "kind": st["kind"],
                                   "opening_id": st["opening_id"], "gap_m": round(hi - lo, 4),
                                   "wall_line_inside_m": round(float(inside), 4), "agree": bool(inside < 0.001)})
    band = []
    for h in LIFT_BAND_2F["edge_handles"]:
        e = db[h]
        a, b = _local("2F", e.dxf.start), _local("2F", e.dxf.end)
        band.append({"handle": h, "layer": e.dxf.layer, "length_m": round(float(math.dist(a, b)), 4),
                     "y_m": round(float(min(a[1], b[1])), 3), "y1_m": round(float(max(a[1], b[1])), 3)})
    # candidate of record
    cp = Path(cand_dir) / "V3_0_38_BOQ_LINES.json"
    raw = json.loads(cp.read_text(encoding="utf-8"))
    lines = raw if isinstance(raw, list) else raw["lines"]
    cand, on_rooms = {}, []
    for ln in lines:
        lid = ln.get("line_id", "")
        rid = (ln.get("location") or {}).get("room_id")
        if any(lid.startswith(k) for k in LINES):
            cand[lid] = {k: ln.get(k) for k in ("item_code", "unit", "evidence_state", "approval_state", "gross",
                                                "measured_net", "bounded_range")}
            cand[lid]["room_id"] = rid
        if rid in ROOMS:
            on_rooms.append({"line_id": lid, "item_code": ln.get("item_code"), "unit": ln.get("unit"),
                             "state": ln.get("evidence_state"), "net": ln.get("measured_net")})
    out = {"drawing": {"P7757.dxf_sha256_8": _sha(dxf)},
           "candidate": {"run": CANDIDATE, "file": cp.name, "sha256_8": _sha(cp), "lines": cand,
                         "lines_on_stair_rooms": sorted(on_rooms, key=lambda x: x["line_id"])},
           "handle_checks": checks, "lift_band_2F": band}
    EXTRACT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------------------------- build (no data)
COLS = ["part", "room", "level", "side", "s0", "s1", "kind", "length_m", "skirting_lm", "status", "handles",
        "opening_id", "note", "cause"]


FREELANCER_2F_CORRIDOR_LM = 13.60   # T-106 trace (merged): his 2F corridor skirting, gross perimeter, no deduction


def freelancer(by):
    """quantities only (T-106 merged trace): his 2F corridor = our 2F lobby + arrival (T-418: 7.375 m2 vs his 7.70 m2,
    -0.325 UNEXPLAINED there). His GF list has no stair-hall skirting row (T-106 table)."""
    ours = round(by["2F-ST-LOBBY"]["net_confirmed_lm"] + by["2F-ST-ARRIVAL"]["net_confirmed_lm"], 6)
    openings = round(by["2F-ST-LOBBY"]["deducted_m"] + by["2F-ST-ARRIVAL"]["deducted_m"], 6)
    open_edge = 2.5     # arrival north edge: slab opening 1.35 (guard RL-07 G-2F) + MS2-U top 1.15: no face
    comps = [
        {"component": "door / lift openings he does not deduct (OP-001 1.000, OP-007 0.900, OP-002 1.000)",
         "lm": openings, "class": "TRACED", "verdict": "RULE_DIFFERENCE (UP-CER-003 / UP-SKIRT-001: not across "
         "openings; lift jambs B6-06)"},
        {"component": "arrival north edge: slab-opening edge + top of MS2-U (no wall face)", "lm": open_edge,
         "class": "TRACED", "verdict": "RULE_DIFFERENCE (no skirting on a guarded / open edge, R-T410-1; defect B12)"},
    ]
    resid = round(FREELANCER_2F_CORRIDOR_LM - ours - sum(c["lm"] for c in comps), 6)
    comps.append({"component": "residual: his outline 13.60 vs our drawn outline 12.90 (his 7.70 m2 vs 7.375 m2, "
                  "no dimensions in his row)", "lm": resid, "class": "UNEXPLAINED", "verdict": "UNRESOLVED"})
    return {"2F corridor": {"freelancer_lm": FREELANCER_2F_CORRIDOR_LM, "engine_t441_confirmed_lm": ours,
                            "diff_lm": round(ours - FREELANCER_2F_CORRIDOR_LM, 6),
                            "diff_pct": round(100 * (ours - FREELANCER_2F_CORRIDOR_LM) / FREELANCER_2F_CORRIDOR_LM, 2),
                            "components": comps,
                            "closes": abs(sum(c["lm"] for c in comps) + ours - FREELANCER_2F_CORRIDOR_LM) < 1e-6},
            "GF stair room": {"freelancer_lm": None, "engine_t441_confirmed_lm":
                              round(by["GF-ST-HALL"]["net_confirmed_lm"] + by["GF-ST-LOBBY030"]["net_confirmed_lm"], 6),
                              "verdict": "his skirting list has no GF stair-hall row (T-106): ENGINE_RIGHT on the "
                                         "existence of the faces (drawn walls at floor level beside T-418 floor "
                                         "parts); material HELD with the floor finish"}}


def build(x):
    if x["drawing"]["P7757.dxf_sha256_8"] != DXF_SHA8:
        raise SystemExit("extract is not from P7757.dxf ab54dd55")
    bad = [c for c in x["handle_checks"] if not c["agree"]]
    if bad:
        raise SystemExit(f"drawn handles disagree with the stretch table: {bad}")
    res = [S.measure(p, FLIGHT_STRETCHES) for p in parts()]
    S.lift_band_check(f2_lobby(), LIFT_BAND_2F)
    by = {r["part"]: r for r in res}
    task = ("GF-ST-HALL", "GF-ST-LOBBY030", "2F-ST-LOBBY")

    def held_faces(r):
        """drawn face length of the held stretches: [faces present in every reading, all candidate faces]; the
        skirting itself stays blank (a guard band may carry none)."""
        lo = sum(h["candidate_lm"] for h in r["held"] if h["kind"] == "GUARD_HELD")
        hi = sum(h["candidate_lm"] for h in r["held"])
        return [round(lo, 6), round(hi, 6)]

    # closure of each stair room's wall + column boundary (engine V2.9 runs: GF wall 9.8 + column 1.3; 2F 15.4 + 1.5)
    gf_closure = {
        "engine_wall_column_lm": 11.1,
        "GF-ST-HALL confirmed": by["GF-ST-HALL"]["net_confirmed_lm"],
        "GF-ST-LOBBY030 confirmed": by["GF-ST-LOBBY030"]["net_confirmed_lm"],
        "T-410 west face y 1.10 .. 5.00, wall + column only (wall 0.40 + column 2FBD 0.60 + wall 0.75 + wall "
        "3.95 .. 5.00 1.05; window OP-022 not a face)": 2.8,
        "T-410 MS1-T north 0 .. 1.15": 1.15,
        "GF-ST-CN strip north face x 1.15 .. 1.35 (UNREAD, T-418)": 0.2,
        "T-410 D1 east 2.95 .. 3.85": 0.9,
    }
    gf_sum = round(sum(v for k, v in gf_closure.items() if k != "engine_wall_column_lm"), 6)
    gf_closure["sum"] = gf_sum
    gf_closure["residual"] = round(gf_sum - 11.1, 6)
    f2_closure = {
        "engine_wall_column_lm": 16.9,
        "2F-ST-LOBBY confirmed": by["2F-ST-LOBBY"]["net_confirmed_lm"],
        "2F-ST-ARRIVAL confirmed (outside the task's parts)": by["2F-ST-ARRIVAL"]["net_confirmed_lm"],
        "faces beside the slab opening, no floor at +9.70 (T-418 O-2F): north y 6.45 wall 0.10 + 1.40 (window "
        "OP-003 not a face)": 1.5,
        "same, west x 0 from y 1.95: wall 1.00 + column 0.60 + wall 0.75 + wall 0.75 + column-wall 0.30 (window "
        "OP-008 not a face)": 3.4,
        "same, east x 2.5 from y 1.95: wall 1.00 + column-wall 0.50 + wall 2.70 + 0.30 (the MS2-U lift wall; its "
        "flight skirting is T-410's, below +9.70)": 4.5,
    }
    f2_sum = round(sum(v for k, v in f2_closure.items() if k != "engine_wall_column_lm"), 6)
    f2_closure["sum"] = f2_sum
    f2_closure["residual"] = round(f2_sum - 16.9, 6)
    cand = x["candidate"]
    if cand["sha256_8"] != CANDIDATE_SHA[:8]:
        raise SystemExit(f"stale candidate {cand['sha256_8']}")
    summary = {
        "task": "T-441", "method": S.METHOD, "rules": list(S.RULES), "candidate": CANDIDATE,
        "candidate_json_sha256_8": cand["sha256_8"], "drawing_sha256_8": DXF_SHA8,
        "parts": [{k: r[k] for k in ("part", "room", "level", "boundary_m", "gross_face_side_m", "deducted_m",
                                       "net_confirmed_lm", "held_count", "jambs_lm", "status")}
                  | {"deductions": r["deductions"], "held_face_length_lm": held_faces(r),
                     "held": [{k: h[k] for k in ("side", "kind", "candidate_lm", "cause")} for h in r["held"]],
                     "jambs": r["jambs"], "in_task": r["part"] in task} for r in res],
        "task_confirmed_lm": round(sum(by[p]["net_confirmed_lm"] for p in task), 6),
        "task_confirmed_by_room": {"GF-R31F8AE": round(by["GF-ST-HALL"]["net_confirmed_lm"]
                                                      + by["GF-ST-LOBBY030"]["net_confirmed_lm"], 6),
                                   "2F-R4D1B62": by["2F-ST-LOBBY"]["net_confirmed_lm"]},
        "closure": {"GF-R31F8AE": gf_closure, "2F-R4D1B62": f2_closure},
        "overlap_with_stair_side_table": [],
        "lift_band_2F": x["lift_band_2F"],
        "freelancer": freelancer(by),
        "parents": {lid: cand["lines"].get(lid) for lid in sorted(cand["lines"])},
        "handle_checks": {"stretches": len(x["handle_checks"]), "agree": sum(c["agree"] for c in x["handle_checks"])},
    }
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(COLS)
    for r in res:
        for row in r["rows"]:
            w.writerow([r["part"], r["room"], f"{r['level']:+.2f}", row["side"], f"{row['s0']:.4f}", f"{row['s1']:.4f}",
                        row["kind"], f"{row['length_m']:.4f}",
                        "" if row["skirting_lm"] is None else f"{row['skirting_lm']:.4f}", row["status"],
                        row["handles"], row["opening_id"], row["note"], row["cause"]])
    return summary, s.getvalue()


def main(argv):
    if argv and argv[0] == "--extract":
        x = extract(argv[1], argv[2])
        print(json.dumps({"handle_checks": len(x["handle_checks"]), "candidate": x["candidate"]["sha256_8"]}))
        return 0
    x = json.loads(EXTRACT.read_text(encoding="utf-8"))
    summary, table = build(x)
    text = json.dumps(summary, indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        assert SUMMARY.read_text(encoding="utf-8") == text, "summary.json does not reproduce"
        assert FACES.read_text(encoding="utf-8") == table, "FACES_T441.csv does not reproduce"
        print("check OK")
        return 0
    print(text)
    if "--write" in argv:
        SUMMARY.write_text(text, encoding="utf-8")
        FACES.write_text(table, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
