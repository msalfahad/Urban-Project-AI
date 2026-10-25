"""T-296 on the development villa (P7757): the SKIRTING OPENING-TO-LINE LEDGER, every candidate FIN.SKIRTING line with
its deductions by opening id, and every room once against an engine-independent skirting run (research only; prints and
writes ids, states, lengths; no coordinate, no name, no drawing content).

Sources (merged unless stated):
  candidate lines    research/agents_t296/CANDIDATE_V3017_SKIRTING.json (--extract <own V3.0.17 run dir> <base v29 dir>:
                     the FIN.SKIRTING lines of V3_0_17_BOQ_LINES.json + each line's room record from ARCH_ROOMS.json
                     (runs by role, doors / passages / windows by engine opening id, the V2.8 window classes) + the
                     engine opening widths of ARCH_OPENINGS.json)
  opening identity   research/agents_t249/OPENINGS_T249.csv ENGINE_REF (census id <- engine 'OP-nnn' per storey)
  opening -> room    research/agents_t262/OPENING_ROOMS_T262.csv (by jamb geometry; label joins corrected)
  sills / sizes      research/agents_t237/OPENING_SIZES_T237.csv merged (T-175 -> T-201 -> T-207 -> T-238)
  rooms / walk       research/agents_t128/ROOMS_T128_R3.csv (KIND), OPENINGS_T128_R3.csv (walked length per opening),
                     research/agents_t250/FACE_LENGTH_T250.csv + ROOM_CLOSURE_T250.csv (wall + column base metres)
  room identity      research/agents_t262/ENGINE_ROOM_XWALK_T262.csv

    python3 -I research/agents_t296/t296_alsenan.py --extract <run>/t254 <run>/t167/v29
    python3 -I research/agents_t296/t296_alsenan.py --write      (ledger CSVs + summary.json)
    python3 -I research/agents_t296/t296_alsenan.py --check      (rebuild in memory, byte compare)
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
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
import skirting_opening_rules as R  # noqa: E402

CAND = HERE / "CANDIDATE_V3017_SKIRTING.json"
LINES_FILE = "V3_0_17_BOQ_LINES.json"


def read(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f_(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------------------------- extract (needs the run)
def _load_lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def extract(run_dir, base_dir):
    run_dir, base_dir = Path(run_dir), Path(base_dir)
    lp = run_dir / LINES_FILE
    if not lp.exists():                       # a released-route run (v29) writes BOQ_LINES.json
        lp = run_dir / "BOQ_LINES.json"
    lines = _load_lines(lp)
    rooms = {r["room_id"]: r for r in json.loads((base_dir / "ARCH_ROOMS.json").read_text())["rooms"]}
    ops = json.loads((base_dir / "ARCH_OPENINGS.json").read_text())["openings"]
    widths = {f"{o['floor']}:{o['opening_id']}": {"kind": o.get("kind"), "width_m": o.get("width_m")} for o in ops}
    out, rec_rooms = [], {}
    for ln in lines:
        if ln.get("item_code") != "FIN.SKIRTING":
            continue
        loc = ln.get("location") or {}
        br = ln.get("bounded_range") or None
        calc = ln.get("calculation") or {}
        out.append({"line_id": ln["line_id"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                    "element": loc.get("element_id", "").split(":", 1)[-1], "evidence_state": ln.get("evidence_state"),
                    "approval_state": ln.get("approval_state"), "gross": ln.get("gross"),
                    "net": ln.get("measured_net"), "deductions": ln.get("deductions") or [],
                    "additions": ln.get("additions") or [],
                    "range": None if not br else [br.get("low"), br.get("high")],
                    "range_inputs": calc.get("inputs") if ln.get("evidence_state") == "BOUNDED_EXPOSURE" else None,
                    "runs_lm": calc.get("inputs") if ln.get("evidence_state") != "BOUNDED_EXPOSURE" else None,
                    "rule": (ln.get("rule") or {}).get("rule_id"), "rfi": ((ln.get("rfi") or {}).get("question") or "")[:200]})
        rid = loc.get("room_id")
        r = rooms.get(rid)
        if r is not None and rid not in rec_rooms:
            rec_rooms[rid] = {"floor": r["floor"], "kind": r.get("kind"), "class": r.get("class"),
                              "codes": r.get("codes"), "runs_lm": r.get("runs_lm"),
                              "finish_scope": (r.get("finish_scope") or {}).get("scope"),
                              "doors": r.get("doors") or [], "passages": r.get("passages") or [],
                              "windows": r.get("windows") or [],
                              "skirting_windows_v28": r.get("skirting_windows_v28")}
    all_rooms = {rid: {"floor": r["floor"], "kind": r.get("kind"), "class": r.get("class"), "codes": r.get("codes"),
                       "finish_scope": (r.get("finish_scope") or {}).get("scope"), "runs_lm": r.get("runs_lm"),
                       "doors": r.get("doors") or [], "passages": r.get("passages") or [],
                       "windows": r.get("windows") or []}
                 for rid, r in rooms.items()}
    doc = {"source": "own V3.0.17 run (research/agents_t254/v3017_run.py on research/agents_t167/v304_run.py) on Drive "
                     "'Alsenan chalet project' P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55) and 'ST7757 dxf.dxf' "
                     "(9f9d1179); room records from the same run's v29 ARCH_ROOMS.json",
           "lines_sha256_8": hashlib.sha256(lp.read_bytes()).hexdigest()[:8], "lines_total": len(lines),
           "skirting_lines": out, "line_rooms": rec_rooms, "engine_rooms": all_rooms,
           "opening_widths": {k: widths[k] for k in sorted(widths)}}
    CAND.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def candidate():
    return json.loads(CAND.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------- identities
def census_by_engine():
    """{(floor, engine opening id): census id} from T-249 ENGINE_REF ('DOOR-.. / OP-nnn', 'OP-nnn', 'COP-nnn')."""
    out = {}
    for r in read(RES / "agents_t249/OPENINGS_T249.csv"):
        for tok in (r["ENGINE_REF"] or "").split("/"):
            tok = tok.strip()
            if tok.startswith(("OP-", "COP-")):
                out[(r["FLOOR"], tok)] = r["ID"]
    return out


def no_op_doors(floor):
    """census doors of a storey whose ENGINE_REF carries no band-opening token (drawn leaf, no OP-nnn)."""
    return [r["ID"] for r in read(RES / "agents_t249/OPENINGS_T249.csv")
            if r["FLOOR"] == floor and r["KIND"] == "DOOR" and "OP-" not in (r["ENGINE_REF"] or "")]


def merged_sizes():
    """{census id: {w, sill, head, status, src}} (T-237 merged; one row per room side, identical per id)."""
    out = {}
    for r in read(RES / "agents_t237/OPENING_SIZES_T237.csv"):
        out.setdefault(r["census_id"], {"w": f_(r["merged_w"]), "sill": f_(r["merged_sill"]),
                                         "sill_txt": r["merged_sill"], "status": r["merged_status"],
                                         "src": r["merged_src"]})
    return out


def opening_rooms():
    return {r["ID"]: r["ROOMS_GEO"].split() for r in read(RES / "agents_t262/OPENING_ROOMS_T262.csv")}


def t128_rooms():
    return {r["ROW"]: r for r in read(RES / "agents_t128/ROOMS_T128_R3.csv")}


def xwalk():
    """{engine room: [T-128 rows]} (T-262)."""
    return {r["ENGINE_ROOM"]: r["T128_MAPPED"].split() for r in read(RES / "agents_t262/ENGINE_ROOM_XWALK_T262.csv")}


# room function of a T-128 row for the skirting owner (T-128 r3 KIND; owner Q-06 / Q-37 A / Q-48 A: wet areas carry
# full-height wall porcelain, no skirting; shaft: no owner rule for skirting along a stair -> HELD)
def t128_class(kind):
    return {"DRY": "DRY", "WET": "WET_FULL_HEIGHT_TILE", "SHAFT": "UNKNOWN"}[kind]


# --------------------------------------------------------------------------------------------- window reading
def window_evidence(cid, sizes):
    """(sill_state, sill_m, source) for a census window from the merged sizes."""
    m = sizes.get(cid)
    if m is None:
        return "UNKNOWN", None, "no merged size row"
    if m["sill"] is not None and not m["status"].startswith("HELD"):
        return "ESTABLISHED", m["sill"], f"{m['status']} ({m['src']})"
    return "HELD", None, f"{m['status']} ({m['src']})"


# --------------------------------------------------------------------------------------------- 1. line trails
def line_trails(C):
    """per candidate quantity line: the deductions by opening id; the F-17 credit named by window id."""
    cen, sizes, oroom = census_by_engine(), merged_sizes(), opening_rooms()
    W = C["opening_widths"]
    ranges = {(l["room_id"]): l for l in C["skirting_lines"] if l["evidence_state"] == "BOUNDED_EXPOSURE"}
    trails, ded_rows = [], []
    for ln in C["skirting_lines"]:
        if ln["net"] is None or ln["gross"] is None:
            continue
        rid, fl = ln["room_id"], ln["floor"]
        rr = C["line_rooms"][rid]
        runs = ln["runs_lm"]
        rows = []
        # doors and passages: the engine lists them as ONE aggregate ('door / passage openings' = runs door +
        # passage); split by opening id: band doors at their engine width, + the drawn door blocks with no band
        # opening (engine DOOR_CLOSURE role; census doors with no OP token whose jambs bind to this room, T-262) at the
        # census width; passages at their band width; what is left is named per role (signed), never absorbed
        t128_here = set(xwalk().get(rid, []))
        for kind, ids, agg in (("DOOR", rr["doors"], runs["door"]), ("PASSAGE", rr["passages"], runs["passage"])):
            part = 0.0
            for oid in ids:
                w = W.get(f"{fl}:{oid}", {}).get("width_m")
                cid = cen.get((fl, oid), "")
                rows.append({"line_id": ln["line_id"], "opening_id": oid, "census_id": cid, "kind": kind,
                             "length_m": round(w, 6) if w is not None else None, "listed": True,
                             "listed_as": "door / passage openings", "source": "ARCH_OPENINGS width_m (band opening)",
                             "cause": "" if cid else "engine opening with no T-249 census id"})
                part += w or 0.0
            if kind == "DOOR":
                for cid in no_op_doors(fl):
                    if t128_here & set(oroom.get(cid, [])) and sizes.get(cid, {}).get("w") is not None:
                        w = sizes[cid]["w"]
                        if part + w <= agg + 1e-5:
                            rows.append({"line_id": ln["line_id"], "opening_id": cid, "census_id": cid,
                                         "kind": "DOOR", "length_m": round(w, 6), "listed": True,
                                         "listed_as": "door / passage openings",
                                         "source": "census door block with no band opening (engine DOOR_CLOSURE "
                                                   "role); T-237 merged width", "cause": ""})
                            part += w
            if abs(agg - part) > 1e-5:
                rows.append({"line_id": ln["line_id"], "opening_id": "", "census_id": "",
                             "kind": f"{kind}_RUN_RESIDUAL", "length_m": round(agg - part, 6), "listed": True,
                             "signed": True, "listed_as": "door / passage openings",
                             "source": f"engine runs {kind.lower()} {agg:.6f} - the openings listed",
                             "cause": ("a band passage longer than its stretch on this room's boundary (shared "
                                       "zone line)" if kind == "PASSAGE" else "a door on this boundary with no id "
                                                                              "in any merged inventory")})
        # windows: F-17 splits a frame edge WINDOW+WINDOW_THRESHOLD equally; one half is listed as glazing edge, the
        # other half is the unlisted credit; the range line holds the whole edge
        bw = ((rr.get("skirting_windows_v28") or {}).get("by_window") or {})
        half_sum = 0.0
        for oid in sorted(bw):
            lm = bw[oid]["lm"]
            cid = cen.get((fl, oid), "")
            st, sill, src = window_evidence(cid, sizes) if cid else ("UNKNOWN", None, "no census id")
            for listed, as_ in ((True, "glazing edge (floor-level window line)"), (False, "")):
                rows.append({"line_id": ln["line_id"], "opening_id": oid + ("#glazing-half" if listed else
                                                                             "#threshold-half"),
                             "census_id": cid, "kind": "WINDOW_EDGE_HALF", "length_m": round(lm / 2, 6),
                             "listed": listed, "listed_as": as_, "source": f"ARCH_ROOMS skirting_windows_v28 {oid} "
                             f"{bw[oid]['class']} {lm:.6f} m (range line holds it whole)",
                             "cause": "" if listed else "F-17 equal-split credit (release_safety.skirting), not listed",
                             "sill_state": st, "sill_m": sill, "sill_src": src,
                             "rooms_geo": " ".join(oroom.get(cid, []))})
            half_sum += lm / 2
        gl = sum(d["lm"] for d in ln["deductions"] if d["what"].startswith("glazing edge"))
        if gl - half_sum > 1e-5:
            rows.append({"line_id": ln["line_id"], "opening_id": "", "census_id": "", "kind": "GLAZING_ONLY_EDGE",
                         "length_m": round(gl - half_sum, 6), "listed": True,
                         "listed_as": "glazing edge (floor-level window line)",
                         "source": "glazing edge - the window halves", "cause": "a WINDOW-only edge (no threshold role)"})
        oth = sum(d["lm"] for d in ln["deductions"] if d["what"].startswith("boundary that is not"))
        if oth > 1e-6:
            rows.append({"line_id": ln["line_id"], "opening_id": "", "census_id": "", "kind": "OTHER_BOUNDARY",
                         "length_m": round(oth, 6), "listed": True, "listed_as": "boundary that is not a wall / column "
                         "face", "source": "engine runs 'other'", "cause": "zone line / open side"})
        t = R.line_trail({"line_id": ln["line_id"], "gross": ln["gross"], "net": ln["net"]},
                         [{"opening_id": r["opening_id"] or (r["kind"] + ":" + ln["line_id"]),
                           "length_m": r["length_m"], "listed": r["listed"], "signed": r.get("signed", False)}
                          for r in rows])
        t.update(floor=fl, room_id=rid, evidence_state=ln["evidence_state"],
                 listed_engine=round(sum(d["lm"] for d in ln["deductions"]), 6),
                 range_line=(ranges.get(rid) or {}).get("line_id", ""),
                 range_hi=((ranges.get(rid) or {}).get("range") or [None, None])[1],
                 unlisted_windows=" + ".join(f"{r['census_id'] or r['opening_id'].split('#')[0]} "
                                             f"{r['length_m']:.6f}" for r in rows
                                             if r["kind"] == "WINDOW_EDGE_HALF" and not r["listed"]))
        trails.append(t)
        ded_rows += rows
    return trails, ded_rows


# --------------------------------------------------------------------------------------------- 2. independent rooms
def t250_base():
    """{T-128 room: wall + column base metres} = straight finish metres + off-line WALL + COLUMN (T-250)."""
    fin, win, door, virt = {}, {}, {}, {}
    for r in read(RES / "agents_t250/FACE_LENGTH_T250.csv"):
        k = r["room"]
        fin[k] = fin.get(k, 0.0) + float(r["finish_m (WALL+COLUMN)"] or 0)
        win[k] = win.get(k, 0.0) + float(r["window_m"] or 0)
        door[k] = door.get(k, 0.0) + float(r["door_m"] or 0) + float(r["gap_m"] or 0)
        virt[k] = virt.get(k, 0.0) + float(r["virtual_m"] or 0)
    out = {}
    for r in read(RES / "agents_t250/ROOM_CLOSURE_T250.csv"):
        k = r["room"]
        out[k] = {"straight_wc": round(fin.get(k, 0.0), 3),
                  "off_wall": f_(r["off: WALL"]) or 0.0, "off_col": f_(r["off: COLUMN"]) or 0.0,
                  "contour": f_(r["walk_contour_m (T-128 r3)"]),
                  "window_t": round(win.get(k, 0.0) + (f_(r["off: WINDOW"]) or 0.0), 3),
                  "door_t": round(door.get(k, 0.0) + (f_(r["off: DOOR+GAP"]) or 0.0), 3),
                  "virtual_t": round(virt.get(k, 0.0) + (f_(r["off: VIRTUAL (open side)"]) or 0.0), 3),
                  "closure": f_(r["closure_m"]) or 0.0}
    return out


T128_TO_CENSUS = {"W05-07": None, "W19-23": None}      # resolved per room through T-237 (room, t128_opening)


def t128_openings():
    """{T-128 room: [(census id, class, walked length)]} using T-237's room-side join of the T-128 names to census ids
    (with T-262's geometry corrections: W19 / D-1F-01 in 1F-03, W20 / D-1F-04 in 1F-02)."""
    join = {}
    for r in read(RES / "agents_t237/OPENING_SIZES_T237.csv"):
        join[(r["room"], r["t128_opening"])] = r["census_id"]
    out = {}
    for r in read(RES / "agents_t128/OPENINGS_T128_R3.csv"):
        cid = join.get((r["ROOM_ROW"], r["OPENING"]))
        if cid is None:
            for (rm, nm), c in join.items():
                if rm == r["ROOM_ROW"] and nm and r["OPENING"].startswith(nm):
                    cid = c
                    break
        walked = f_(r["WALKED_FACE_M"])
        out.setdefault(r["ROOM_ROW"], []).append({"census_id": cid or "", "t128_name": r["OPENING"],
                                                  "cls": r["CLASS"], "walked_m": walked})
    return out


def room_rows(C):
    """every T-128 room once, + every engine room the T-128 ledger lacks, with its skirting reading and its line."""
    sizes, t128, base, ops = merged_sizes(), t128_rooms(), t250_base(), t128_openings()
    xw = xwalk()
    eng_of = {}
    for e, rows in xw.items():
        for t in rows:
            eng_of.setdefault(t, []).append(e)
    # T-211 / T-292 routes for rooms whose engine room is merged or not 1:1 (T-262 has no single map for them)
    eng_of.setdefault("1F-13", []).append("1F-R78C367") if "1F-R78C367" not in eng_of.get("1F-13", []) else None
    lines_by_room = {}
    for ln in C["skirting_lines"]:
        lines_by_room.setdefault(ln["room_id"], []).append(ln)
    rows = []
    for rid in t128:
        tr = t128[rid]
        fc = t128_class(tr["KIND"])
        pieces = []
        b = base.get(rid)
        if b is not None:
            pieces.append({"piece_id": "WALL+COLUMN (T-250)", "kind": "WALL",
                           "length_m": round(b["straight_wc"] + b["off_wall"] + b["off_col"], 3)})
        seen = set()
        for o in ops.get(rid, []):
            L = o["walked_m"]
            key = o["census_id"] or o["t128_name"]
            if L is None:                         # GF-16 keeps the T-074 hand outline: the merged width, named
                L = (sizes.get(o["census_id"]) or {}).get("w")
            if key in seen:                       # the T-128 list names one opening once per room
                continue
            seen.add(key)
            if o["cls"] == "window":
                st, sill, _ = window_evidence(o["census_id"], sizes)
                pieces.append({"piece_id": key, "kind": "WINDOW", "opening_id": key, "length_m": L,
                               "sill_state": st, "sill_m": sill})
            elif o["cls"] == "virtual":
                pieces.append({"piece_id": key, "kind": "OPEN_SIDE", "length_m": L})
            elif o["cls"] == "wall":
                continue                          # a wall face already in the T-250 base
            elif L is None:
                # no walked length (GF-16: the room keeps the T-074 hand outline): the merged width, named
                w = (sizes.get(o["census_id"]) or {}).get("w")
                pieces.append({"piece_id": key, "kind": "PASSAGE" if o["cls"] in ("arch", "doorway") else "DOOR",
                               "opening_id": key, "length_m": w})
            else:
                pieces.append({"piece_id": key, "kind": "PASSAGE" if o["cls"] in ("arch", "doorway") else "DOOR",
                               "opening_id": key, "length_m": L})
        led = R.room_ledger({"room_id": rid, "finish_class": fc, "pieces": pieces})
        eng = eng_of.get(rid, [])
        lns = [l for e in eng for l in lines_by_room.get(e, [])]
        rows.append({"room": rid, "kind": tr["KIND"], "finish_class": fc, "engine_rooms": " ".join(eng),
                     "contour_m": (b or {}).get("contour"), "base_wc_m": pieces[0]["length_m"] if b else None,
                     "status": led["status"], "certain_lm": led["certain_lm"],
                     "range_hi_lm": None if led["range_lm"] is None else led["range_lm"][1],
                     "windows_skirted": " ".join(p["piece_id"] for p in led["pieces"] if p["kind"] == "WINDOW"
                                                 and p["skirted"] == "YES"),
                     "windows_held": " ".join(p["piece_id"] for p in led["pieces"] if p["kind"] == "WINDOW"
                                              and p["skirted"] == "HELD"),
                     "windows_floor_glazing": " ".join(p["piece_id"] for p in led["pieces"] if p["kind"] == "WINDOW"
                                                       and p["skirted"] == "NO"),
                     "deducted_openings": " ".join(f"{d['opening_id']} {d['length_m']:.3f}" for d in led["deductions"]
                                                   if d["basis"] == "DEDUCTED"),
                     "lines": " ".join(f"{l['line_id']}:{l['evidence_state']}" for l in lns),
                     "_pieces": led["pieces"]})
    # engine rooms outside every T-128 row
    mapped = {e for t in eng_of.values() for e in t}
    for e, r in sorted(C["engine_rooms"].items()):
        if e in mapped:
            continue
        lns = lines_by_room.get(e, [])
        rows.append({"room": f"(engine {e})", "kind": r.get("kind") or "", "finish_class": "", "engine_rooms": e,
                     "contour_m": (r.get("runs_lm") or {}).get("boundary"), "base_wc_m": None, "status": "",
                     "certain_lm": None, "range_hi_lm": None, "windows_skirted": "", "windows_held": "",
                     "windows_floor_glazing": "", "deducted_openings": "",
                     "lines": " ".join(f"{l['line_id']}:{l['evidence_state']}" for l in lns), "_pieces": []})
    return rows


# --------------------------------------------------------------------------------------------- 3. line ledger
def _room_fn(cid_rooms, t128):
    """the finish owner of a window's wall base from the room(s) its jambs bind to (T-262): DRY / WET / SHAFT."""
    kinds = {t128[r]["KIND"] for r in cid_rooms if r in t128}
    return kinds


def line_ledger(C, trails, deds):
    """per candidate skirting line: before (candidate) -> after (ledger) with each window's cause by census id."""
    t128 = t128_rooms()
    by_line = {}
    for d in deds:
        if d["kind"] == "WINDOW_EDGE_HALF" and not d["listed"]:
            by_line.setdefault(d["line_id"], []).append(d)
    out, causes = [], []
    for t in trails:
        ln = next(l for l in C["skirting_lines"] if l["line_id"] == t["line_id"])
        runs = ln["runs_lm"]
        base = runs["wall"] + runs["column"]
        add_certain = 0.0
        held_hi = 0.0
        held_items = []
        for d in by_line.get(t["line_id"], []):
            edge = round(2 * d["length_m"], 6)
            cid = d["census_id"]
            kinds = _room_fn(d["rooms_geo"].split(), t128)
            if "SHAFT" in kinds:
                verdict, why, status = "HELD", "window of the stair shaft: no owner rule for skirting along a stair " \
                                               "(stringer / landing): HELD", "HELD"
                held_hi += edge
                held_items.append(f"{cid} shaft")
            elif kinds and kinds <= {"WET"}:
                verdict, why, status = "NOT_SKIRTED", (f"window of a wet room ({' '.join(d['rooms_geo'].split())}): "
                                                       "full-height wall porcelain owns the base (Q-37 A / Q-48 A)"), \
                    "ASSUMED - OWNER-APPROVED"
            elif d["sill_state"] == "ESTABLISHED" and d["sill_m"] > R.FLOOR_GLAZING_MAX_SILL_M:
                verdict, why, status = "SKIRTED", (f"sill {d['sill_m']:.2f} m above the floor ({d['sill_src']}): the "
                                                   "wall base continues under the window"), "DRAWING-CONFIRMED"
                add_certain += edge
            elif d["sill_state"] == "ESTABLISHED":
                verdict, why, status = "NOT_SKIRTED", (f"sill {d['sill_m']:.2f} m: floor-level glazing "
                                                       f"({d['sill_src']})"), "DRAWING-CONFIRMED"
            else:
                verdict, why, status = "HELD", f"sill not established ({d['sill_src']})", "HELD"
                held_hi += edge
                held_items.append(f"{cid} sill")
            causes.append({"line_id": t["line_id"], "floor": t["floor"], "engine_room": t["room_id"],
                           "opening_id": d["opening_id"].split("#")[0], "census_id": cid,
                           "rooms_geo": d["rooms_geo"], "edge_lm": edge, "f17_credit_lm": d["length_m"],
                           "sill": "" if d["sill_m"] is None else f"{d['sill_m']:.2f}", "reading": verdict,
                           "status": status, "why": why})
        led_lo = round(base + add_certain, 6)
        led_hi = round(led_lo + held_hi, 6)
        shaft = [r for r in xwalk().get(t["room_id"], []) if r.startswith("ST-")]
        held_shaft = round(sum(t250_base()[r]["straight_wc"] + t250_base()[r]["off_wall"] + t250_base()[r]["off_col"]
                               for r in shaft), 6) if shaft else None
        if held_shaft:
            led_lo = round(led_lo - held_shaft, 6)
            held_items.append(f"{'+'.join(shaft)} walls {held_shaft:.3f} (T-250 walk)")
        rng = t["range_hi"]
        flags = []
        rr = C["line_rooms"][t["room_id"]]
        if rr.get("finish_scope") == "REVIEW":
            flags.append("OPEN_PLAN_WET_SCOPE_EXTENT (engine REVIEW): the wet pantry's wall bases inside this engine "
                         "room are not separable from the dry ones in any merged ledger: HELD")
        if held_shaft:
            flags.append(f"the engine room includes the stair shaft part {'+'.join(shaft)} (T-262 overlap "
                         f"{_overlaps(t['room_id'])}): its wall bases ({held_shaft:.3f} lm on the T-250 walk) carry "
                         "skirting under no owner rule (stair stringer / landing): HELD, taken out of the low figure")
        st = "HELD" if (held_hi > 1e-6 or flags) else "DRAWING-CONFIRMED"
        if rr.get("finish_scope") == "REVIEW" and set(xwalk().get(t["room_id"], [])) <= {"GF-07"}:
            st, led_lo, led_hi = "NOT_APPLICABLE", None, None
            flags = ["the engine room lies wholly in the pantry GF-07 (T-262 GF-07=0.209/1.000), a WET area (owner Q-37 "
                     "A, T-128 r3): full-height wall porcelain, no skirting (one owner per base)"]
        out.append({"line_id": t["line_id"], "floor": t["floor"], "engine_room": t["room_id"],
                    "t128_rooms": " ".join(xwalk().get(t["room_id"], [])),
                    "cand_state": t["evidence_state"], "cand_gross": t["gross"], "cand_listed": t["listed_engine"],
                    "cand_net": t["net"], "cand_unlisted": round(t["gross"] - t["listed_engine"] - t["net"], 6),
                    "range_line": t["range_line"], "cand_range_hi": rng,
                    "named_unlisted": t["unlisted_lm"], "trail_residual": t["residual_lm"],
                    "ledger_lo": led_lo, "ledger_hi": led_hi, "ledger_status": st, "held_shaft_lm": held_shaft,
                    "delta_lo": None if led_lo is None else round(led_lo - t["net"], 6),
                    "held": "; ".join(held_items), "flags": " | ".join(flags)})
    return out, causes


# --------------------------------------------------------------------------------------------- 4. room join
UNMAPPED_REASON = {
    "SHAFT": "lift shaft cell (engine SHAFT 3.24 m2): no floor finish, no skirting: NOT_APPLICABLE, no line",
    "GF-R7B7A5D": "UNLABELLED cell beyond D-GF-05 / W10 (T-262 UNREFERENCED, outdoor side): no room function, no line",
    "GF-RF002DC": "UNLABELLED cell beyond W09 (T-262 UNREFERENCED, outdoor side): no room function, no line",
    "1F-RFFE7AF": ("1F dressing (dry by the absence of fixtures, T-223; Checker 22:05 2.970 m2): a DRY room with NO "
                   "skirting line: MISSING (an omission, never 0); engine boundary 6.90 m is the engine's own figure, "
                   "not an independent measure (no T-128 / T-250 walk of this cell): HELD"),
}


def _overlaps(eng):
    for r in read(RES / "agents_t262/ENGINE_ROOM_XWALK_T262.csv"):
        if r["ENGINE_ROOM"] == eng:
            return r["T128_OVERLAPS"]
    return ""


def room_join(rows, lines):
    """every room once with the candidate line(s) that carry it and the reason when none does."""
    out = []
    for r in rows:
        rec = {k: v for k, v in r.items() if not k.startswith("_")}
        if r["room"].startswith("("):
            e = r["engine_rooms"]
            rec["reason"] = UNMAPPED_REASON.get(e) or UNMAPPED_REASON.get(r["kind"], "no T-128 row, no line")
        elif r["finish_class"] == "WET_FULL_HEIGHT_TILE":
            rec["reason"] = ("WET (T-128 r3; owner Q-06 / Q-37 A / Q-48 A): full-height wall porcelain owns every "
                             "wall base: NOT_APPLICABLE" + ("" if r["lines"] else "; the candidate writes no "
                                                            "NOT_APPLICABLE line for it (unlabelled engine cell)"))
        elif r["finish_class"] == "UNKNOWN":
            rec["reason"] = ("stair shaft: skirting along the flights / landings has no owner rule (stringer or "
                             "skirting; OWNER_RULE_STAIRS silent): HELD blank")
        elif "BLOCKED_RFI" in r["lines"] and r["status"] == "DETERMINATE":
            rec["reason"] = (f"DRY lobby with a determinate run {r['certain_lm']:.3f} lm (T-250), but the candidate "
                             "carries it only inside the stair room's BLOCKED_RFI line (engine room = lobby + shaft)")
        else:
            rec["reason"] = "DRY: carried by the line(s) named"
        out.append(rec)
    return out


def line_room_join(C, rows, lines):
    """per candidate quantity line whose engine room is a union of WHOLE T-128 rooms (T-262 overlap 1.000 of each):
    the engine-independent run beside the ledger figure, the difference decomposed into named causes."""
    t128ops = t128_openings()
    R_ = {r["room"]: r for r in rows}
    base = t250_base()
    out = []
    for ln in lines:
        ov = _overlaps(ln["engine_room"])
        parts = [x.split("=") for x in ov.split()] if ov else []
        whole = bool(parts) and all(p[1].split("/")[0] == "1.000" for p in parts)
        rooms = [p[0] for p in parts]
        rec = {"line_id": ln["line_id"], "engine_room": ln["engine_room"], "t128_rooms": " ".join(rooms),
               "overlaps": ov, "ledger_lo": ln["ledger_lo"], "comparable": "YES" if whole else "NO"}
        if not whole or ln["ledger_lo"] is None:
            rec["why_not"] = ("engine room is not a union of whole T-128 rooms (" + ov + "): no face split in any "
                              "merged ledger") if not whole else "line NOT_APPLICABLE"
            out.append(rec)
            continue
        cand = next(l for l in C["skirting_lines"] if l["line_id"] == ln["line_id"])
        runs = cand["runs_lm"]
        ind_base = sum((R_[r]["base_wc_m"] or 0.0) for r in rooms)
        lo_full = ln["ledger_lo"] + (ln["held_shaft_lm"] or 0.0)     # the shaft part back in, for a like join
        win_ledger = lo_full - (runs["wall"] + runs["column"])
        # windows the independent walk skirts (same merged evidence), at their walked lengths
        win_walk = 0.0
        for r in rooms:
            for o in t128ops.get(r, []):
                if o["census_id"] and o["census_id"] in R_[r]["windows_skirted"].split() \
                        and R_[r]["finish_class"] == "DRY":
                    win_walk += o["walked_m"] or 0.0
        indep = ind_base + win_walk
        a = sum(base[r]["contour"] for r in rooms) - cand["gross"]                 # walked contour vs boundary
        b = runs["door"] + runs["passage"] - sum(base[r]["door_t"] for r in rooms)  # door extents vs walked gaps
        c = runs["glazing_edge"] + runs["window_threshold"] - sum(base[r]["window_t"] for r in rooms)
        d = runs["other"] - sum(base[r]["virtual_t"] for r in rooms)                # 'other' vs open sides
        e = sum(base[r]["closure"] for r in rooms)                                   # T-250 room closure
        f = win_walk - win_ledger                                                     # skirted windows
        diff = indep - lo_full
        resid = diff - (a + b + c + d - e + f)
        rec.update(indep_lm=round(indep, 3), diff_lm=round(diff, 3), contour_minus_gross=round(a, 3),
                   door_extent_minus_walk=round(b, 3), window_walk_minus_engine=round(c, 3),
                   other_minus_open_side=round(d, 3), residual_lm=round(resid, 3),
                   closure_t250=round(e, 3), residual_cause=("3-decimal rounding of the T-250 / T-128 columns"
                                                              if abs(resid) > 0.0005 else ""))
        if "ST-1F" in rooms or "ST-2F" in rooms or "ST-GF" in rooms:
            rec["note"] = "includes a stair-shaft part: its base is HELD in the ledger (shaft), counted here as walked"
        out.append(rec)
    return out


# --------------------------------------------------------------------------------------------- outputs
def _csv(rows, cols):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=list(cols), lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return s.getvalue()


DED_COLS = ("line_id", "opening_id", "census_id", "kind", "length_m", "listed", "listed_as", "source", "cause",
            "sill_state", "sill_m", "rooms_geo")


def build():
    C = candidate()
    trails, deds = line_trails(C)
    lines, causes = line_ledger(C, trails, deds)
    rr = room_rows(C)
    join = line_room_join(C, rr, lines)
    rows = room_join(rr, lines)
    return C, trails, deds, lines, causes, rows, join


def summary(C, trails, deds, lines, causes, rows, join):
    sk = C["skirting_lines"]
    by_state = {}
    for l in sk:
        by_state[l["evidence_state"]] = by_state.get(l["evidence_state"], 0) + 1
    unl = round(sum(t["unlisted_lm"] for t in trails if t["unlisted_lm"] > 1e-6), 6)
    nlines = [t for t in trails if t["unlisted_lm"] > 1e-6]
    cand_net = round(sum(l["cand_net"] for l in lines), 6)
    cand_rng = round(sum(l["cand_range_hi"] or 0 for l in lines), 6)
    det = [l for l in lines if l["ledger_status"] != "NOT_APPLICABLE"]
    return {"policy": R.POLICY, "rules": list(R.RULES), "candidate": {"lines_sha256_8": C["lines_sha256_8"],
            "lines_total": C["lines_total"], "skirting_lines": len(sk), "by_state": dict(sorted(by_state.items()))},
            "trail": {"quantity_lines": len(trails),
                      "readds_as_listed": sum(1 for t in trails if t["readds_as_listed"]),
                      "readds_with_named": sum(1 for t in trails if t["readds_with_named"]),
                      "lines_with_unlisted": len(nlines), "unlisted_lm": unl,
                      "max_abs_residual_lm": max(abs(t["residual_lm"]) for t in trails)},
            "ledger": {"cand_net_lm": cand_net, "cand_range_hi_sum_lm": cand_rng,
                       "ledger_lo_lm": round(sum(l["ledger_lo"] for l in det), 6),
                       "ledger_hi_lm": round(sum(l["ledger_hi"] for l in det), 6),
                       "lines_not_applicable": [l["line_id"] for l in lines if l["ledger_status"] == "NOT_APPLICABLE"],
                       "by_status": {s: sum(1 for l in lines if l["ledger_status"] == s)
                                     for s in sorted({l["ledger_status"] for l in lines})}},
            "window_readings": {v: round(sum(c["edge_lm"] for c in causes if c["reading"] == v), 6)
                                for v in sorted({c["reading"] for c in causes})},
            "rooms": {"t128_rooms": sum(1 for r in rows if not r["room"].startswith("(")),
                      "engine_rooms_outside_t128": sum(1 for r in rows if r["room"].startswith("("))}}


def outputs():
    C, trails, deds, lines, causes, rows, join = build()
    TR = ("line_id", "floor", "room_id", "evidence_state", "gross", "listed_engine", "net", "listed_lm",
          "unlisted_lm", "residual_lm", "readds_as_listed", "readds_with_named", "range_line", "range_hi",
          "unlisted_windows")
    LL = tuple(lines[0].keys())
    CC = tuple(causes[0].keys())
    RR = tuple(k for k in rows[0].keys() if not k.startswith("_"))
    JC = ("line_id", "engine_room", "t128_rooms", "overlaps", "comparable", "why_not", "ledger_lo", "indep_lm",
          "diff_lm", "contour_minus_gross", "door_extent_minus_walk", "window_walk_minus_engine",
          "other_minus_open_side", "closure_t250", "residual_lm", "residual_cause", "note")
    return {"LINE_TRAIL_T296.csv": _csv(trails, TR), "DEDUCTIONS_BY_OPENING_T296.csv": _csv(deds, DED_COLS),
            "LINE_LEDGER_T296.csv": _csv(lines, LL), "WINDOW_CAUSES_T296.csv": _csv(causes, CC),
            "ROOMS_T296.csv": _csv(rows, RR),
            "LINE_ROOM_JOIN_T296.csv": _csv(join, JC),
            "summary.json": json.dumps(summary(C, trails, deds, lines, causes, rows, join), indent=1,
                                       sort_keys=True) + "\n"}


def main(argv):
    if argv[:1] == ["--extract"]:
        d = extract(argv[1], argv[2])
        print(f"extracted {len(d['skirting_lines'])} skirting lines of {d['lines_total']} ({d['lines_sha256_8']})")
        return 0
    outs = outputs()
    if argv[:1] == ["--write"]:
        for k, v in outs.items():
            (HERE / k).write_text(v, encoding="utf-8")
        print(outs["summary.json"])
        return 0
    if argv[:1] == ["--check"]:
        bad = [k for k, v in outs.items() if (HERE / k).read_text(encoding="utf-8") != v]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 1 if bad else 0
    print(outs["summary.json"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
