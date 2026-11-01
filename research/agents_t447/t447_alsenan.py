"""T-447 on the development villa (P7757): the stair-room skirting faces that T-441 left HELD / UNKNOWN, and its three
findings, settled from the drawings with STAIR_ROOM_HELD_FACES_V1. Research only: nothing is wired, no candidate or
released quantity changes (lane I proposals in the report).

    python3 -I research/agents_t447/t447_alsenan.py --extract <P7757.dxf> <dir holding V3_0_40_BOQ_LINES.json>
    python3 -I research/agents_t447/t447_alsenan.py --write     (FACES_T447.csv + summary.json from the extract)
    python3 -I research/agents_t447/t447_alsenan.py --check     (rebuild from the committed extract, byte compare)

Geometry: room-LOCAL metres in the frames of T-418 / T-441 (origin = the stair room's south-west inner corner: GF from
handles 298 / 220, 2F from 12B7 / 1282). --extract re-reads every handle below on the architectural DXF (Drive 'Alsenan
chalet project', P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55), sweeps three zones for any drawn element, and
records the candidate of record's lines that the proposals touch. Committed: handles, layers, room-local coordinates
and lengths, line ids, states and quantities only (no world coordinate, no name, no drawing text). Sections and plans
read as images (sheet 3 GF plan, sheet 10 section A-A) are cited by sheet and described in words in the report.
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
sys.path.insert(0, str(HERE.parent / "agents_t441"))
import held_faces_v1 as H  # noqa: E402
import stair_room_skirting_v1 as S441  # noqa: E402  (imported, never edited)

EXTRACT = HERE / "EXTRACT_T447.json"
FACES = HERE / "FACES_T447.csv"
SUMMARY = HERE / "summary.json"
CANDIDATE = "ARCH_TAKEOFF_V3.0.40"
CANDIDATE_SHA8 = "aa6aa927"          # board pin (T-430 MERGED 3fe8f974)
DXF_SHA8 = "ab54dd55"
ORIGIN_FROM = {"GF": ("298", "220"), "2F": ("12B7", "1282")}

# handle -> (floor, layer, expected room-local points (m)) : every one re-read at --extract, 0.002 m tolerance
HANDLES = {
    # GF divider zone and the south-west box (finding (a))
    "155": ("GF", "5", [(1.35, 1.05), (1.15, 1.05)]),        # band end at the cut
    "157": ("GF", "5", [(1.15, 1.05), (1.15, 3.126)]),
    "4A4": ("GF", "5", [(1.35, 3.85), (1.35, 1.05)]),
    "47C": ("GF", "2", [(1.35, 0.45), (1.15, 0.45)]),        # hidden outline of the band above, from y 0.45
    "499": ("GF", "2", [(1.35, 0.45), (1.15, 0.45)]),
    "47E": ("GF", "2", [(1.35, 0.45), (1.35, 3.85)]),
    "47D": ("GF", "2", [(1.3, 0.5), (1.2, 0.5)]),            # hidden rail end above
    "156": ("GF", "5", [(1.3, 1.1), (1.2, 1.1)]),            # rail end at the cut
    "151": ("GF", "5", [(1.2, 1.1), (1.2, 3.12)]),
    "47F": ("GF", "5", [(1.3, 1.1), (1.3, 3.85)]),
    "2C8": ("GF", "5", [(1.2, 1.05), (1.2, 0.0)]),            # single visible line in the zone
    "2C9": ("GF", "2", [(1.15, 1.05), (1.15, 0.0)]),
    "2F1D": ("GF", "5", [(1.15, 1.05), (0.0, 0.0)]),          # diagonal in the SW box
    "2F1E": ("GF", "2", [(1.116, 1.087), (-0.034, 0.037)]),
    "2CA": ("GF", "5", [(0.575, 0.525), (1.47, 0.525)]),      # walking-line start tick, crosses the zone at y 0.525
    "DC": ("GF", "5", [(1.15, 1.1), (0.0, 1.1)]),
    "DE": ("GF", "2", [(1.15, 1.15), (0.0, 1.15)]),
    # OP-020 reveal (item 2)
    "21C": ("GF", "1", [(2.5, 2.0), (2.5, 0.0)]),
    "21B": ("GF", "1", [(2.5, 5.0), (2.5, 2.9)]),
    "4AA": ("GF", "1", [(2.5, 2.9), (2.7, 2.9)]),
    "33C": ("GF", "2", [(2.5, 2.0), (2.5, 2.9)]),
    "33D": ("GF", "2", [(2.7, 2.0), (2.7, 2.9)]),
    # back lobby and the strip west of it (item 3)
    "2AB": ("GF", "1", [(0.0, 5.0), (1.453, 5.0)]),
    "26E": ("GF", "1", [(0.0, 5.0), (1.453, 5.0)]),
    "297": ("GF", "1", [(0.0, 5.0), (0.0, 3.95)]),
    "481": ("GF", "5", [(2.5, 3.85), (1.35, 3.85)]),
    "4A6": ("GF", "5", [(1.3, 3.85), (1.35, 3.85)]),
    # 2F: lobby north face (finding (c)) and the MS2-U top strip (finding (b))
    "1289": ("2F", "1", None), "128A": ("2F", "1", [(3.1, 1.25), (2.5, 1.25)]),
    "129A": ("2F", "1", [(2.5, 6.45), (2.5, 1.25)]),
    "1386": ("2F", "5", [(2.5, 2.3), (1.35, 2.3)]),
    "1385": ("2F", "2", [(2.5, 2.25), (1.35, 2.25)]),
    "1358": ("2F", "5", [(1.35, 1.9), (1.35, 5.3)]),
    "1359": ("2F", "5", [(1.3, 1.95), (1.3, 5.25)]),
    "138A": ("2F", "5", [(1.35, 1.9), (0.0, 1.9)]),
    "138B": ("2F", "5", [(1.3, 1.95), (0.0, 1.95)]),
    "1374": ("2F", "5", [(2.5, 2.6), (1.35, 2.6)]),
}
# level marks: block insert -> its circle centre must lie in the named strip
LEVEL_MARKS = {"4AB": ("GF", (1.15, 3.85, 1.35, 5.0)), "412": ("GF", (1.35, 0.0, 2.5, 2.95))}
# zones swept for ANY drawn element on the visible / wall layers (layer 2 is hidden, D is the window detail layer)
SWEEPS = {
    "divider_zone_y045_105": ("GF", (1.151, 0.451, 1.349, 1.049)),
    "strip_GF_ST_CN": ("GF", (1.151, 3.851, 1.349, 4.999)),
    "under_winders_x0_115": ("GF", (0.001, 3.851, 1.149, 4.999)),
}
SWEEP_LAYERS = ("1", "5", "S-COL.BON", "4", "W")
LINES = {  # candidate lines the proposals touch (T-441 / T-418 / T-421 / T-292 / T-349 ledgers)
    "L-47fa825d": "GF stair hall skirting (parent, BLOCKED_RFI)",
    "L-b8d4a7f0": "2F stair hall skirting (parent, BLOCKED_RFI)",
    "L-f53d4986": "GF stair hall floor part +1.00 (T-418 / T-421)",
    "L-b4441a1b": "GF back lobby floor part +0.30 (T-418 / T-421)",
    "L-ae0cdd79": "2F stair hall wall plaster (2F-01 faces incl. 2F-W00; T-292 / T-349)",
    "L-c74cfb4e": "2F stair hall wall paint (2F-01 faces incl. 2F-W00; T-292)",
}


def _sha(p, n=8):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


# ------------------------------------------------------------------------------------------------ extract (private)
def extract(dxf, cand_dir):
    import ezdxf  # noqa: E402  (extract only)
    from ezdxf import path as zpath  # noqa: E402
    doc = ezdxf.readfile(str(dxf))
    db = doc.entitydb
    org = {fl: (float(db[hx].dxf.start.x), float(db[hy].dxf.start.y)) for fl, (hx, hy) in ORIGIN_FROM.items()}

    def loc(fl, x, y):
        return (round((x - org[fl][0]) / 1000.0, 3), round((y - org[fl][1]) / 1000.0, 3))

    checks = []
    for h, (fl, layer, exp) in HANDLES.items():
        e = db.get(h)
        if e is None or e.dxftype() != "LINE":
            raise SystemExit(f"handle {h} missing or not a LINE")
        pts = [loc(fl, e.dxf.start.x, e.dxf.start.y), loc(fl, e.dxf.end.x, e.dxf.end.y)]
        ok_layer = e.dxf.layer == layer
        ok_pts = True
        if exp is not None:
            ok_pts = all(abs(a[0] - b[0]) <= 0.002 and abs(a[1] - b[1]) <= 0.002 for a, b in zip(pts, exp))
        L = round(((pts[1][0] - pts[0][0]) ** 2 + (pts[1][1] - pts[0][1]) ** 2) ** 0.5, 4)
        checks.append({"handle": h, "floor": fl, "layer": e.dxf.layer, "pts": pts, "length_m": L,
                       "layer_ok": ok_layer, "points_ok": ok_pts})
    marks = []
    for h, (fl, box) in LEVEL_MARKS.items():
        e = db[h]
        c = [s for s in e.virtual_entities() if s.dxftype() == "CIRCLE"][0]
        p = loc(fl, c.dxf.center.x, c.dxf.center.y)
        marks.append({"handle": h, "floor": fl, "centre": p, "radius_m": round(c.dxf.radius / 1000.0, 3),
                      "inside": box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3], "box": list(box)})
    sweeps = {}
    msp = doc.modelspace()
    for name, (fl, box) in SWEEPS.items():
        hits = []
        for e in msp:
            if not e.dxf.hasattr("layer") or e.dxf.layer not in SWEEP_LAYERS:
                continue
            if e.dxftype() in ("TEXT", "MTEXT", "DIMENSION", "HATCH"):
                continue
            try:
                pts = [((x - org[fl][0]) / 1000.0, (y - org[fl][1]) / 1000.0)
                       for x, y, _ in zpath.make_path(e).flattening(5)]
            except Exception:
                continue
            seg = list(pts)                       # densified every <= 5 mm so a line crossing the zone is caught
            for a, b in zip(pts, pts[1:]):
                n = max(1, int(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / 0.005) + 1)
                seg += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n)]
            if any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in seg):
                hits.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "type": e.dxftype()})
        sweeps[name] = {"floor": fl, "box": list(box), "hits": sorted(hits, key=lambda r: r["handle"])}
    cp = Path(cand_dir) / "V3_0_40_BOQ_LINES.json"
    raw = json.loads(cp.read_text(encoding="utf-8"))
    rows = raw["lines"] if isinstance(raw, dict) and "lines" in raw else raw
    cand = {}
    for r in rows:
        lid = str(r.get("line_id") or r.get("id") or "")
        for pre in LINES:
            if lid.startswith(pre):
                br = r.get("bounded_range") or {}
                cand[pre] = {"line_id": lid, "item_code": r.get("item_code"), "unit": r.get("unit"),
                             "measured_net": r.get("measured_net"),
                             "bounded": [br.get("low"), br.get("high")] if br else None,
                             "evidence_state": r.get("evidence_state")}
    out = {"drawing": {"P7757.dxf_sha256_8": _sha(dxf)},
           "candidate": {"run": CANDIDATE, "file": cp.name, "sha256_8": _sha(cp), "lines": cand},
           "handle_checks": checks, "level_marks": marks, "sweeps": sweeps}
    EXTRACT.write_text(json.dumps(out, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    return out


# ------------------------------------------------------------------------------------------------ build (public)
GUARD_REFS = ["GF plan (P7757.dxf): band 155 / 157 / 4A4 on layer 5 (below the cut, not a cut wall on layer 1)",
              "sheet 10 section A-A: at +1.00 the divider is posts with a top and a mid rail; the MS1-L steps and "
              "soffit are drawn visible between the floor and the lowest rail (no solid upstand)",
              "T-410 MS1-L east side OPEN 'not skirted' (RL-07 MS1-L), T-393 RL-07 / RL-08"]


def build(x):
    if x["drawing"]["P7757.dxf_sha256_8"] != DXF_SHA8:
        raise SystemExit("stale drawing")
    bad = [c["handle"] for c in x["handle_checks"] if not (c["layer_ok"] and c["points_ok"])]
    if bad:
        raise SystemExit(f"handles off: {bad}")
    hc = {c["handle"]: c for c in x["handle_checks"]}
    mk = {m["handle"]: m for m in x["level_marks"]}
    sw = x["sweeps"]
    rows = []

    # item 1: GF divider band faces (T-441 HELD 2.200 cut outline / 3.400 T-418 outline)
    band = [("BAND-E", 1.90, "east face x 1.35, y 1.05 .. 2.95 (hall side)"),
            ("BAND-W", 0.10, "west face x 1.15, y 1.05 .. 1.15 (south-west box side)"),
            ("BAND-END", 0.20, "south end y 1.05, x 1.15 .. 1.35")]
    for bid, L, where in band:
        r = H.guard_edge({"id": bid, "length": L, "refs": GUARD_REFS,
                          "evidence": {"wall_cut": False, "section_balustrade_open_below_rail": True}})
        r.update({"kind": "GUARD", "part": "GF-ST-HALL", "where": where, "was": "GUARD_HELD (T-441)"})
        rows.append(r)

    # finding (a): divider zone y 0.45 .. 1.05 (T-418 SOLID)
    zone_hits = [h["handle"] for h in sw["divider_zone_y045_105"]["hits"]]
    vis = [{"handle": h, "closed_outline": False} for h in zone_hits]
    strip_a = H.strip_class({"id": "DIV-ZONE-045-105", "w": 0.20, "d": 0.60, "visible_elements": vis,
                             "section_flat": True, "adjacent_level": 1.00, "step_line": False})

    # item 2: OP-020 reveal jambs (T-441 HELD 0.400)
    jam = H.doorless_jambs({"opening_id": "OP-020", "jambs": [0.20, 0.20],
                            "conditions": {"no_door": True, "real_jamb": True, "eligible_side": True,
                                           "floor_finish_reaches_jamb": False, "not_full_wall_tile_room": False},
                            "evidence": {
                                "floor_finish_reaches_jamb": "the reveal floor 0.900 x 0.200 is the hand-wash space's "
                                "marble threshold (owner Q-06 (a); T-409 F-T409-1 P-GF-01 = OP-020 0.180 m2), so the hall "
                                "porcelain stops on the hall face x 2.5",
                                "not_full_wall_tile_room": "the opening belongs to GF-RD36087, a basin-only hand-wash "
                                "space = WET, full-height wall porcelain (owner Q-06 (a); T-208 / T-296 GF-11)"}})
    jam.update({"id": "OP-020-JAMBS", "kind": "JAMB", "part": "GF-ST-HALL", "was": "HELD (T-441)",
                "refs": ["P7757.dxf 21C / 4AA / 33C / 33D", "Q-06 (a)", "URBAN-SKIRTING-OPENING-METHOD v1"]})
    rows.append(jam)

    # item 3: GF back lobby west side x 1.35 and the strip GF-ST-CN
    strip_c = H.strip_class({"id": "GF-ST-CN", "w": 0.20, "d": 1.15,
                             "visible_elements": [{"handle": h["handle"], "closed_outline": False}
                                                  for h in sw["strip_GF_ST_CN"]["hits"]],
                             "level_mark_inside": 0.30 if mk["4AB"]["inside"] else None})
    rows.append({"id": "LOBBY-W-x135", "kind": "SIDE", "part": "GF-ST-LOBBY030", "status": H.NO_FACE, "lm": None,
                 "was": "UNKNOWN (T-441, candidate 1.150)",
                 "cause": "no wall, guard or step on any visible / wall layer on x 1.15 .. 1.35 for y 3.85 .. 5.00 "
                          "(sweep), and the +0.30 level mark 4AB is centred inside the strip: the lobby floor continues "
                          "west; the 'face on x 1.35' alternative is refuted"})
    rows.append({"id": "LOBBY-N-STRIP", "kind": "FACE", "part": "GF-ST-LOBBY030", "status": H.FACE,
                 "lm": 0.20, "line": "GF:y=5", "t0": 1.15, "t1": 1.35, "level": 0.30,
                 "refs": ["P7757.dxf 2AB / 26E (layer 1) y 5.00, x 0 .. 1.453"],
                 "cause": "north wall face of the strip GF-ST-CN at +0.30 (closure item 'GF-ST-CN north 0.200' of T-441)"})
    rows.append({"id": "UNDER-WINDERS", "kind": "SIDE", "part": "GF-ST-LOBBY030", "status": H.UNKNOWN, "lm": None,
                 "candidate_lm": 2.20, "candidate_high_lm": 3.45,
                 "cause": "west of x 1.15 the space under the MS1-T winders: no wall or step drawn (sweep: "
                          + (", ".join(h["handle"] for h in sw["under_winders_x0_115"]["hits"]) or "nothing")
                          + "), no level mark; if the +0.30 floor continues, its faces are west wall 297 1.050 + north "
                          "wall 2AB x 0 .. 1.15 1.150 = 2.200 lm, plus the OP-022 jamb zone 0.100 and the face under the "
                          "MS1-L end (y 3.85, 1.150) if the +1.00 slab ends there: 3.450 lm high; RFI c"})

    # finding (b): 2F corridor residual 0.700 lm
    ours = [(0.0, 2.5, 1.95), (2.5, 4.5, 1.25)]
    his = [(0.0, 1.35, 1.95), (1.35, 2.5, 2.30), (2.5, 4.5, 1.25)]
    tr = H.trace(13.60, {"T-441 outline (arrival + lobby)": ours,
                         "outline over the MS2-U top going (1386 at y 2.30)": his})
    added = H.classify_added([
        {"id": "129A y 1.95 .. 2.30", "lm": 0.35, "cls": "STAIR_SIDE", "owner": "T-410 MS2-U.E (s 0 .. 3.300 from "
         "the top riser at y 1.95; 12 risers, Q-46 A)"},
        {"id": "x 1.35 y 1.95 .. 2.30 (band 1358 / 1359)", "lm": 0.35, "cls": "GUARD"}])

    # finding (c): 2F-W00 face on the lobby side. T-250 walks the engine room 2F-01 (x 0 .. 4.5, y 0 .. 1.25): its
    # 2F-W00 face = wall run x 2.7 .. 4.5 (1.800, WALL_SIDE_CLOSURE) + 0.031 past the run end onto column 2F72 = 1.831
    # (handles 128A 0.43 = 0.400 on the run + 0.031, 1289 0.40, gap 0.99); the rest of the column face (0.169) is the
    # room's off-line COLUMN row 0.175 (sampled). 128A as drawn = 0.600 = column face 0.200 + wall 0.400.
    run = 1.800
    c128 = hc["128A"]["length_m"]
    col = 0.200
    t250 = {"face_m": 1.831, "past_run_end_m": 0.031, "offline_column_m": 0.175, "handles": "128A:0.43 1289:0.40"}
    north_t250 = round(t250["face_m"] + t250["offline_column_m"], 4)
    north_drawn = round(hc["1289"]["length_m"] + 1.0 + c128, 4)
    c = {"t250": t250, "drawn_128A_m": c128, "drawn_1289_m": hc["1289"]["length_m"], "gap_OP002_m": 1.0,
         "wall_run_m": run, "column_2F72_face_m": col,
         "split_128A_m": {"on_column_2F72": col, "on_wall_run": round(c128 - col, 4)},
         "north_side_t250_m": north_t250, "drawn_face_m": north_drawn, "diff_m": round(north_t250 - north_drawn, 4),
         "height_m": 3.35, "line_effect_m2_each_bound": round((north_t250 - north_drawn) * 3.35, 4),
         "skirting_effect_lm": 0.0,
         "verdict": "ATTRIBUTION, not a wrong drawn length: 0.43 is the part of 128A on the wall run (+0.031 past "
                    "its end); the column part sits in the off-line COLUMN row; net +0.006 m sampling"}

    tot = H.settle(rows, others=[{"id": "T-410 MS1-T north (winder levels)", "line": "GF:y=5", "t0": 0.0,
                                  "t1": 1.15, "lo": 2.667, "hi": 3.50},
                                 {"id": "T-441 lobby north", "line": "GF:y=5", "t0": 1.35, "t1": 2.5, "level": 0.30}])
    return {"rows": rows, "strip_a": strip_a, "strip_c": strip_c, "trace_b": tr, "added_b": added, "c": c,
            "totals": tot, "candidate": x["candidate"]}


def write_outputs(x):
    b = build(x)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "part", "kind", "status", "lm", "candidate_lm", "was", "cause"])
    for r in b["rows"]:
        w.writerow([r["id"], r["part"], r["kind"], r["status"], "" if r.get("lm") is None else f"{r['lm']:.3f}",
                    "" if r.get("candidate_lm") is None else f"{r['candidate_lm']:.3f}", r.get("was", ""),
                    r.get("cause", "")])
    faces = buf.getvalue()
    t441 = {"GF hall": 4.650, "GF lobby": 1.400, "2F lobby": 3.350}
    summ = {
        "task": "T-447", "method": H.METHOD, "rules": list(H.RULES), "candidate": b["candidate"]["run"],
        "candidate_json_sha256_8": b["candidate"]["sha256_8"], "drawing_sha256_8": DXF_SHA8,
        "candidate_lines": b["candidate"]["lines"],
        "skirting_lm": {"t441_confirmed": t441, "t447_confirmed": {"GF hall": 4.650, "GF lobby": round(1.400 + 0.200, 3),
                                                                   "2F lobby": 3.350},
                        "gf_task_total_before": 6.050, "gf_task_total_after": 6.250},
        "settled": b["totals"], "finding_a_strip": b["strip_a"], "item3_strip": b["strip_c"],
        "finding_b_trace": b["trace_b"], "finding_b_added": b["added_b"], "finding_c": b["c"],
        "floor_m2": {"GF hall": {"t418": 4.805, "t447": round(4.805 + b["strip_a"]["m2"], 4)},
                     "GF lobby": {"t418": 1.3225, "t447": round(1.3225 + b["strip_c"]["m2"], 4)},
                     "T-418 divider SOLID": {"t418": 0.68, "t447": round(0.68 - b["strip_a"]["m2"], 4)}},
    }
    return faces, json.dumps(summ, indent=1, ensure_ascii=True) + "\n"


def main(argv):
    if argv[:1] == ["--extract"]:
        x = extract(argv[1], argv[2])
        print(json.dumps({"handle_checks": len(x["handle_checks"]), "candidate": x["candidate"]["sha256_8"],
                          "lines": sorted(x["candidate"]["lines"])}))
        return 0
    x = json.loads(EXTRACT.read_text(encoding="utf-8"))
    faces, summ = write_outputs(x)
    if argv[:1] == ["--write"]:
        FACES.write_text(faces, encoding="utf-8")
        SUMMARY.write_text(summ, encoding="utf-8")
        return 0
    if argv[:1] == ["--check"]:
        ok = FACES.read_text(encoding="utf-8") == faces and SUMMARY.read_text(encoding="utf-8") == summ
        print("check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
