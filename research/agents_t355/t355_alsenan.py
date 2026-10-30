"""T-355 read-only application on the development villa (every villa by R-T355-1 .. 5, t355_masonry_accessories.py).

Inputs are MERGED ledgers of this repository; no drawing coordinate, image or client name is read or written here:
  walls / pieces  research/agents_t317/t317_alsenan.build() = register v4 (T-288) x V2 census runs (T-228) x T-274 run
                  pieces (columns, beam / slab soffits, cut exactly at the drawn outlines) x T-261 r3 split x T-288
                  sunken pieces; the same block tops the merged T-317 joint census uses (storey - member depth).
  block type      register v4 block_type (BLACK conventional mortared / WHITE AAC thin-bed, owner Q-60)
  openings        research/agents_t237/OPENING_SIZES_T237.csv (merged sizes: T-175 hosts, T-201 heads, T-207, T-238)
                  with host wall and IN_GROSS from research/agents_t175/T175_OPENING_HOSTS.csv; W18's in-column part
                  from research/agents_t274/T274_OPENING_SCAN.csv
  lintels         research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv (ST7757.pdf p.13 LINTEL SCHEDULE:
                  depth by width band; MIN.40cm bearing each end)
  face classes    research/agents_t250/WALL_SIDE_CLOSURE_T250.csv (rooms on each side of each run) and
                  research/agents_t312/LINE_SUMMARY_T312.csv (tiled rooms); the joint population of T-317 (ledger())

COURSE (owner Q-77 point 1, 2026-10-29; Q-75 decision 2026-10-23): conventional mortared block with a PROVISIONAL 10 mm
bed joint; actual block dimensions where available: the owner's own 2025 sales-order record of the black solid
blocks, 39 x 19 cm face + 1 cm joint = the 40 x 20 module the Q-75 provisional rule counts with (12.5 / m2). Primary
module 0.190 + 0.010 = 0.200 m; shown beside it the owner's example 200 + 10 = 0.210 m (a 200 mm-high block), never
merged. WHITE (AAC, thin-bed adhesive): no adhesive specification and two face families (Q-60): HELD by name.
Datum: wall base = structural floor of the storey (the T-274 / T-317 block tops are above it); openings: sill / head
above FFL + 0.10 (Q-43 floor finishing); a door's hole and a sill-0 window run from the structural floor.

    python3 -I research/agents_t355/t355_alsenan.py [--write | --check]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(RES / "agents_t317"))
import t355_masonry_accessories as X  # noqa: E402
import t317_alsenan as T317  # noqa: E402

FFL = 0.10
SRC_COURSE = ("Q-77 point 1 (owner 2026-10-29: provisional 10 mm bed joint, actual block dimensions where available) + "
              "Q-75 decision 2026-10-23 (provisional 40 x 20 module; owner 2025 sales order: 39 x 19 face + 1 cm joint)")
SPEC = {"PRIMARY": X.course_spec(0.190, 0.010, SRC_COURSE, "ASSUMED — OWNER-APPROVED"),
        "ALT_210": X.course_spec(0.200, 0.010, "Q-77 point 1 example (200 mm block -> 210 mm module)",
                                 "ASSUMED — OWNER-APPROVED")}
WHITE_HELD = "WHITE (AAC) block, thin-bed adhesive: no adhesive specification, two face families (Q-60): course HELD"
ARCHED = {"W15", "W16", "W17", "W26"}       # T-238: arched outlines; a lintel over an arch is not the schedule's
TILED_EXTRA = {}
PANTRY = {"GF-07"}                           # T-312: pantry backsplash inside the pantry's plaster faces


def rd(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def schedule():
    out = []
    for r in rd(RES / "alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"):
        if r["RECORD"] == "SCHEDULE_ROW":
            out.append((float(r["WIDTH_LO_CM"]), float(r["WIDTH_HI_CM"]), float(r["D_CM"]) / 100.0))
    assert [d for _, _, d in out] == [0.20, 0.20, 0.30, 0.40, 0.55], out
    return out


def openings_by_wall():
    hosts = {r["ID"]: r for r in rd(RES / "agents_t175/T175_OPENING_HOSTS.csv")}
    sizes = {}
    for r in rd(RES / "agents_t237/OPENING_SIZES_T237.csv"):
        sizes.setdefault(r["census_id"], r)
    sch = schedule()
    scan = rd(RES / "agents_t274/T274_OPENING_SCAN.csv")
    w18_in_col = sum(float(x["in_column_m"]) for x in scan if x["band_id"] == "WB-FL0041-FL0042" and x["floor"] == "1F")
    by, named = defaultdict(list), []
    for oid, h in hosts.items():
        if h["IN_GROSS"] != "YES" or not h["HOST_ROW"]:
            named.append({"opening": oid, "why": "not in the masonry gross of a register wall (T-175 IN_GROSS NO)"})
            continue
        s = sizes.get(oid)
        w = float(s["merged_w"]) if s else float(h["WIDTH_M"])
        note = ""
        if oid == "W18":
            w = round(w - w18_in_col, 6)
            note = f"width in masonry {w} (jamb {w18_in_col} inside a column, T-274 scan)"
        sill = s["merged_sill"] if s else "HELD"
        head = s["merged_head"] if s else "HELD"
        st = s["merged_status"] if s else (h["HEIGHT_STATUS_T150"] or "HELD")
        if sill in ("", "HELD") or head in ("", "HELD"):
            bot = top = None
        else:
            sl, hd = float(sill), float(head)
            bot = 0.0 if sl == 0.0 else sl + FFL
            top = hd + FFL
        d = None if oid in ARCHED or top is None else X.lintel_depth(w, sch)
        o = X.make_opening(oid, w, bot, top, d, 0.40, st)
        by[h["HOST_ROW"]].append((o, note))
    return by, named


def side_rooms():
    out = defaultdict(dict)
    for r in rd(RES / "agents_t250/WALL_SIDE_CLOSURE_T250.csv"):
        rooms = [x.strip().split(" ")[0] for x in r["rooms"].split(";") if x.strip()]
        out[(r["wall_id"], f"{r['floor']}|{r['run_id']}")][r["side"]] = rooms
    return out


def tiled_rooms():
    t = set()
    for r in rd(RES / "agents_t312/LINE_SUMMARY_T312.csv"):
        if r["line_id"] != "NO_LINE":
            t.update(x.strip() for x in r["rooms"].split(";") if x.strip())
    return t


def finish_of(room, tiled):
    if room in PANTRY:
        return {"PLASTER", "TILE"}
    return {"TILE"} if room in tiled else {"PLASTER"}


def panels(spec_name):
    walls, unknown, t261, _ = T317.build()
    ops, named = openings_by_wall()
    reg = {r["wall_id"]: r for r in rd(RES / "agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv")}
    grouped = defaultdict(list)
    for r, rk, w, notes, src in walls:
        grouped[r["wall_id"]].append((r, rk, w, notes))
    out = []
    for wid, items in grouped.items():
        r = items[0][0]
        btype = reg[wid]["block_type"]
        course = SPEC[spec_name] if btype == "BLACK" else None
        held = ""
        if T317.level_held(r):
            held = (r["held_items"] or "")[:160]
        pcs = []
        for _, rk, w, _ in items:
            for i, p in enumerate(w.pieces):
                key = p.member if p.kind == "COLUMN" else f"{rk}@b{i}"
                pcs.append(X.make_piece(p.kind, p.length, p.top, key))
        mesh_pcs = pcs
        tie_pcs = pcs
        t261_note = ""
        if wid in t261:
            hs = [float(x["height_m"]) if x["height_m"] else None for x in t261[wid]]
            mesh_pcs = [X.make_piece("BLOCK", float(x["length_m"]), h, f"T261:{x['piece']}") for x, h in zip(t261[wid], hs)]
            known = [h for h in hs if h is not None]
            if course is not None and known and None not in hs and \
                    X.n_levels(course, min(known)) == X.n_levels(course, max(known)):
                top = min(known)
                t261_note = f"T-261 piece heights {min(known)} .. {max(known)} give the same tie count"
            else:
                top = None
                t261_note = "T-261 piece heights not tied to the column stations and not all equal in levels: HELD"
            tie_pcs = [p if p.kind == "COLUMN" else X.Piece("BLOCK", p.length, top, p.key) for p in pcs]
        o = tuple(x for x, _ in ops.get(wid, []))
        notes = "; ".join(n for _, n in ops.get(wid, []) if n)
        out.append({"wall_id": wid, "floor": r["floor"], "group": r["group"], "block_type": btype,
                    "t_m": reg[wid]["t_m"], "runs": [rk for _, rk, _, _ in items],
                    "mesh": X.Panel(wid, r["floor"], tuple(mesh_pcs), o, course, held),
                    "tie": X.Panel(wid, r["floor"], tuple(tie_pcs), o, course, held),
                    "course_held": "" if course else WHITE_HELD, "notes": "; ".join(x for x in (notes, t261_note) if x)})
    hosted = {w for w in ops}
    lost = sorted(hosted - set(grouped))
    return out, unknown, named, lost


def ledger(spec_name="PRIMARY"):
    P, unknown, named, lost = panels(spec_name)
    mesh, by_wall, tie = [], [], []
    for p in P:
        recs, state = X.mesh_levels(p["mesh"])
        if p["course_held"]:
            state = f"HELD: {p['course_held']}"
        for r in recs:
            r["group"], r["block_type"] = p["group"], p["block_type"]
        mesh += recs
        gross_run = sum(x.length for x in p["mesh"].pieces if x.kind == "BLOCK")
        by_wall.append({"wall_id": p["wall_id"], "floor": p["floor"], "group": p["group"], "block_type": p["block_type"],
                        "t_m": p["t_m"], "block_run_m": round(gross_run, 6), "levels": len(recs),
                        "net_m": round(sum(r["net_m"] for r in recs), 6) if recs else None,
                        "held_m": round(sum(r["held_m"] for r in recs), 6) if recs else None,
                        "state": ("ASSUMED — OWNER-APPROVED" if recs and state == "MEASURED" else state),
                        "notes": p["notes"]})
        ts = X.ties(p["tie"])
        if p["course_held"]:
            for t in ts:
                t.update(state="HELD", ties=None, held=p["course_held"])
        for t in ts:
            t["group"], t["block_type"] = p["group"], p["block_type"]
        tie += ts
    X.no_zero_held(tie)
    return {"mesh": mesh, "by_wall": by_wall, "ties": tie, "unknown": unknown, "named_openings": named, "lost": lost}


def joint_classes():
    """R-T355-4 on T-317's merged joint population: per run and side, INSIDE m.l under both bands, by face class."""
    L = T317.ledger()
    rooms, tiled = side_rooms(), tiled_rooms()
    reg = {r["wall_id"]: r for r in rd(RES / "agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv")}
    per = defaultdict(lambda: {"OWNER": 0.0, "DRAWING": 0.0, "held_OWNER": 0, "held_DRAWING": 0})
    for meth, js in (("OWNER", L["J_own"]), ("DRAWING", L["J_dd"])):
        for j in js:
            if meth == "DRAWING" and j["side"] == "EXT":
                continue
            k = (j["wall_id"], j["run"], j["side"])
            if j["class"] == "INSIDE":
                per[k][meth] += j["length_m"] or 0.0
            elif j["class"] == "HELD":
                per[k][f"held_{meth}"] += 1
    rows = []
    for (wid, rk, side), v in sorted(per.items()):
        sr = rooms.get((wid, rk), {})
        if side == "EXT":
            cls, rm = "C", "exterior (Sigma, OD-V3B-7)"
        else:
            if reg[wid]["group"] == "EXTERNAL":
                rs = [x for s in sr.values() for x in s]
            else:
                pair = [sr.get("+", []), sr.get("-", [])]
                rs = pair[0] if side == "INT-A" else pair[1]
            fins = set()
            for x in rs:
                fins |= finish_of(x, tiled)
            cls = X.face_class(fins) if rs else "UNKNOWN"
            rm = " ".join(rs) or "no room on this side (T-250)"
        if side == "EXT":
            v["DRAWING"] = v["OWNER"]
            v["held_DRAWING"] = v["held_OWNER"]
        rows.append({"wall_id": wid, "run": rk, "side": side, "rooms": rm, "class": cls,
                     "owner_band_m": round(v["OWNER"], 6), "drawing_band_m": round(v["DRAWING"], 6),
                     "held_joints_owner": v["held_OWNER"], "held_joints_drawing": v["held_DRAWING"]})
    return rows


def summarise(led, alt, jc):
    def fl(recs):
        t = defaultdict(lambda: {"net_m": 0.0, "held_m": 0.0, "levels": 0, "walls": set()})
        for r in recs:
            a = t[r["floor"]]
            a["net_m"] += r["net_m"]
            a["held_m"] += r["held_m"]
            a["levels"] += 1
            a["walls"].add(r["wall_id"])
        return {k: {"net_m": round(v["net_m"], 4), "held_m": round(v["held_m"], 4), "levels": v["levels"],
                    "walls": len(v["walls"])} for k, v in sorted(t.items())}

    def tl(ts):
        t = defaultdict(lambda: {"ties": 0, "junctions": 0, "junctions_held": 0, "held_white": 0})
        for r in ts:
            a = t[r["floor"]]
            if r["state"] == "MEASURED":
                a["ties"] += r["ties"]
                a["junctions"] += 1
            else:
                a["junctions_held"] += 1
                if r["held"].startswith("WHITE"):
                    a["held_white"] += 1
        return dict(sorted(t.items()))

    def cl(rows):
        t = defaultdict(lambda: {"owner_band_m": 0.0, "drawing_band_m": 0.0, "sides": 0})
        for r in rows:
            a = t[r["class"]]
            a["owner_band_m"] += r["owner_band_m"]
            a["drawing_band_m"] += r["drawing_band_m"]
            a["sides"] += 1
        return {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in sorted(t.items())}

    st = defaultdict(int)
    for w in led["by_wall"]:
        st[w["state"].split(":")[0] if w["state"].startswith("HELD") else w["state"]] += 1
    held_causes = defaultdict(float)
    for r in led["mesh"]:
        for c, L, _ in r["held"]:
            held_causes[c] += L
    partial = sum(1 for r in led["mesh"] if r["partial_above"])
    return {
        "schema": X.SCHEMA,
        "course_primary": {"block_h": SPEC["PRIMARY"].block_h, "joint": SPEC["PRIMARY"].joint,
                           "module": round(SPEC["PRIMARY"].module, 6), "source": SPEC["PRIMARY"].source,
                           "status": SPEC["PRIMARY"].status},
        "course_alt": {"module": round(SPEC["ALT_210"].module, 6), "source": SPEC["ALT_210"].source},
        "mesh_primary_by_floor": fl(led["mesh"]),
        "mesh_alt210_by_floor": fl(alt["mesh"]),
        "mesh_primary_total_net_m": round(sum(r["net_m"] for r in led["mesh"]), 4),
        "mesh_alt210_total_net_m": round(sum(r["net_m"] for r in alt["mesh"]), 4),
        "mesh_held_by_cause_m": {k: round(v, 4) for k, v in sorted(held_causes.items())},
        "mesh_levels_with_partial_course_above": partial,
        "mesh_partial_course_above_block_m": round(sum(r["partial_above_m"] for r in led["mesh"]), 4),
        "mesh_partial_course_above_net_m": round(sum(r["net_m"] for r in led["mesh"] if r["partial_above"]), 4),
        "walls_by_state": dict(sorted(st.items())),
        "ties_primary_by_floor": tl(led["ties"]),
        "ties_alt210_by_floor": tl(alt["ties"]),
        "ties_primary_total": sum(r["ties"] for r in led["ties"] if r["state"] == "MEASURED"),
        "ties_alt210_total": sum(r["ties"] for r in alt["ties"] if r["state"] == "MEASURED"),
        "junctions_total": len(led["ties"]),
        "joint_mesh_by_class": cl(jc),
        "walls_unknown": [u["wall_id"] for u in led["unknown"]],
        "openings_not_in_register_gross": [x["opening"] for x in led["named_openings"]],
        "hosted_walls_without_runs": led["lost"],
        "specification": "SHARMAT material / size / anchorage / embedment / fixing: SPECIFICATION HELD (no fixing "
                         "detail; owner Q-77 point 3); never a structural design approval",
        "freelancer": "no mesh-strip, sharmat or joint-mesh line in the freelancer workbooks (T-317 census)",
    }


def _f(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, bool):
        return "YES" if v else ""
    if isinstance(v, list):
        return " | ".join(f"{c} {L:.4f} ({w})" for c, L, w in v)
    return str(v)


def outputs():
    led, alt, jc = ledger("PRIMARY"), ledger("ALT_210"), joint_classes()
    S = summarise(led, alt, jc)
    altmap = {(r["wall_id"], r["k"]): r for r in alt["mesh"]}
    files = {}
    mc = ["wall_id", "floor", "group", "block_type", "k", "course_below", "level_m", "course_above_h_m", "partial_above",
          "partial_above_m",
          "gross_m", "cut_opening_m", "cut_lintel_m", "held_m", "net_m", "held"]
    files["MESH_LEVELS_T355.csv"] = (mc, led["mesh"])
    wc = ["wall_id", "floor", "group", "block_type", "t_m", "block_run_m", "levels", "net_m", "held_m", "state", "notes",
          "alt210_levels", "alt210_net_m"]
    for w in led["by_wall"]:
        a = [r for (wid, _), r in altmap.items() if wid == w["wall_id"]]
        w["alt210_levels"] = len(a)
        w["alt210_net_m"] = round(sum(r["net_m"] for r in a), 6) if a else None
    files["MESH_BY_WALL_T355.csv"] = (wc, led["by_wall"])
    alt_t = {(r["wall_id"], r["column_at"], r["face"]): r for r in alt["ties"]}
    tc = ["wall_id", "floor", "group", "block_type", "column_at", "face", "block_segment_m", "top", "state", "ties",
          "alt210_ties", "held"]
    for t in led["ties"]:
        t["alt210_ties"] = alt_t[(t["wall_id"], t["column_at"], t["face"])]["ties"]
    files["SHARMAT_T355.csv"] = (tc, led["ties"])
    jcc = ["wall_id", "run", "side", "rooms", "class", "owner_band_m", "drawing_band_m", "held_joints_owner",
           "held_joints_drawing"]
    files["JOINT_MESH_CLASS_T355.csv"] = (jcc, jc)
    txt = {}
    for name, (cols, rows) in files.items():
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: _f(r.get(k)) for k in cols})
        txt[name] = buf.getvalue()
    txt["summary.json"] = json.dumps(S, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    return txt, S, led, alt, jc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    txt, S, *_ = outputs()
    if a.write:
        for n, t in txt.items():
            (HERE / n).write_text(t, encoding="utf-8")
    if a.check:
        bad = [n for n, t in txt.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        if bad:
            raise SystemExit(f"stale: {bad}")
        print("check: every output reproduced")
    print(json.dumps({k: S[k] for k in ("mesh_primary_by_floor", "mesh_alt210_by_floor", "ties_primary_by_floor",
                                         "ties_alt210_by_floor", "joint_mesh_by_class", "walls_by_state",
                                         "mesh_held_by_cause_m")}, indent=1, ensure_ascii=False))
    return S


if __name__ == "__main__":
    main()
