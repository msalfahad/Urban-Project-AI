"""T-317 read-only application on the development villa (every villa by R-T317-1 .. 5, t317_spatter_mesh.py).

Inputs are MERGED, Checker-verified ledgers in this repository (no drawing coordinate is read or written here):
  walls      research/agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv (T-288, MERGED 643b310b): wall ids, group, storey, state
  runs       research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv evidence 'V2 run ...' (the census runs of each wall)
  pieces     research/agents_t274/T274_RUN_PIECES.csv (T-274, MERGED aba9399a): stations along each run, COLUMN /
             BEAM (member, depth) / slab FACE (thickness) pieces, cut exactly at the drawn outlines
  T-261 r3   research/agents_t261/T261_SPLIT.csv (MERGED 164b189f): the walls whose drawn-extent split governs
  sunken     research/agents_t288/SUNKEN_PIECES_T288.csv: pieces under a sunken slab panel, top = 4.34 - d (D-41 HELD)
  openings   research/agents_t274/T274_OPENING_GAPS.csv: the drawn opening gaps of each band (band stations)
  finishes   research/agents_t305/LINE_SUMMARY_T305.csv (exterior Sigma, MERGED 9d71ef09), research/agents_t312/
             LINE_SUMMARY_T312.csv (wall tile, MERGED 8943b5ed) and the V3.0.20 candidate's FIN.PLASTER lines
             (--plaster <dir holding V3_0_20 BOQ_LINES json of research/agents_t244/v3020_direct.py>, optional)

    python3 -I research/agents_t317/t317_alsenan.py [--plaster <dir>] [--write]

Bands (R-T317-5): OWNER (Q-43 / Q-48 A): finished floor = structural floor + 0.10; height GF 3.65, 1F / 2F 3.35 ->
band 0.10 .. 3.75 (GF) / 0.10 .. 3.45 (1F, 2F) above the structural floor. DRAWING-DERIVED: finished floor to the
soffit over each piece (joints_to_soffit: no slab thickness assumed). EXTERIOR side of an EXTERNAL wall: the Sigma face
runs over the whole storey (T-305 faces; OD-V3B-7), so every block-to-concrete joint on it is inside.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t317_spatter_mesh as M  # noqa: E402

STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}           # p7757_arch_sheet10.pdf section, T-112 (T-274 basis)
FFL = 0.10                                              # Q-43 floor finishing
OWNER_TOP = {"GF": 0.10 + 3.65, "1F": 0.10 + 3.35, "2F": 0.10 + 3.35}   # Q-43 / Q-48 A
SPATTER_SCOPE = M.Scope("B4-05", "OD-V3B-4 / OD-V3B-5 / OD-V3B-6 / OD-V3B-7 (owner 2026-10-04, Alsenan)",
                        frozenset({"PLASTER", "TILE", "SIGMA", "CLADDING"}))
MESH_SCOPE = M.Scope("B9-03", None)                     # nothing answers it (T-317 s.2): HELD by name


def rd(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def runs_of(r):
    m = re.search(r"V2 run (.*?) \(", r["evidence"].split(" || ")[-1])
    ids = m.group(1).split() if m else []
    return [f"{r['floor']}|{x}" for x in ids if x != "none"] if ids and ids[0] != "none" else []


def load():
    v4 = rd(RES / "agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv")
    v2 = {r["wall_id"]: r for r in rd(RES / "agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv")}
    P = defaultdict(list)
    for x in rd(RES / "agents_t274/T274_RUN_PIECES.csv"):
        P[x["run_key"]].append(x)
    t261 = defaultdict(list)
    for x in rd(RES / "agents_t261/T261_SPLIT.csv"):
        t261[x["wall_id"]].append(x)
    sunk = defaultdict(set)
    for x in rd(RES / "agents_t288/SUNKEN_PIECES_T288.csv"):
        sunk[x["wall_id"]].add(x["panel_face"])
    gaps = defaultdict(float)
    for x in rd(RES / "agents_t274/T274_OPENING_GAPS.csv"):
        gaps[(x["floor"], x["band_id"])] += float(x["in_runs_m"])
    return v4, v2, P, t261, sunk, gaps


def annex(r):
    return "annex datum" in (r["held_items"] or "")


def level_held(r):
    """register v4 holds that leave the block top (the joint level) unknown on the whole wall: the annex datum (Q-54 B)
    and the lift tie beam size (ST p.8 n.19). Held openings do not move a joint level and hold nothing here."""
    h = r["held_items"] or ""
    return "annex datum" in h or "lift tie beam" in h


def run_pieces(fl, rk, P, sunk_faces, held_all):
    """T-274 run pieces -> M.Piece list (slivers kept: they are exact cuts; a sliver joint is real length)."""
    out, notes = [], []
    for x in P.get(rk, []):
        L = float(x["len_m"])
        if L <= 0:
            continue
        if x["kind"] == "COLUMN":
            out.append(M.Piece("COLUMN", L, None, f"{rk}@{float(x['from_m']):.3f}"))
            continue
        top, under, mem = None, "", x["member_id"] or x["face_id"] or x["kind"]
        if x["kind"] == "BEAM":
            under = "BEAM"
            if x["depth_m"]:
                top = round(STOREY[fl] - float(x["depth_m"]), 6)
            else:
                notes.append(f"{x['mark']} {x['member_id']} depth not printed ({x['member_status']})")
        elif x["kind"] == "FACE" and x["face_cls"] == "SLAB" and x["slab_t_m"]:
            under = "SLAB"
            if x["face_id"] in sunk_faces:
                notes.append(f"under sunken panel {x['face_id']}: top 4.34 - d (D-41)")
            else:
                top = round(STOREY[fl] - float(x["slab_t_m"]), 6)
        else:
            notes.append(f"{x['kind']} {x['face_id']} {x['face_cls']}: nothing with a printed soffit")
        if held_all:
            top = None
        out.append(M.Piece("BLOCK", L, top, mem, (), under))
    return out, notes


def build(plaster_dir=None):
    v4, v2, P, t261, sunk, gaps = load()
    walls, rows, jrows = [], [], []
    for r in v4:
        wid, fl, grp = r["wall_id"], r["floor"], r["group"]
        rr = v2.get(wid)
        rks = runs_of(rr) if rr else []
        held_all = level_held(r)
        src = "T-274 run pieces"
        if wid in t261:
            src = "T-261 r3 split (heights) + T-274 run pieces (columns)"
        if not rks:
            rows.append({"wall_id": wid, "floor": fl, "group": grp, "source": "no census run (hand census, curved arc band, "
                         "glazed line or held strip)", "state": "UNKNOWN"})
            continue
        sides = []
        if grp == "INTERNAL":
            sides = [M.Side("INT-A", "PLASTER", FFL, OWNER_TOP[fl]), M.Side("INT-B", "PLASTER", FFL, OWNER_TOP[fl])]
        elif grp == "EXTERNAL":
            sides = [M.Side("INT", "PLASTER", FFL, OWNER_TOP[fl]), M.Side("EXT", "SIGMA", 0.0, STOREY[fl])]
        else:
            rows.append({"wall_id": wid, "floor": fl, "group": grp, "source": "group HELD in the register", "state": "UNKNOWN"})
            continue
        if annex(r):
            sides = [M.Side(s.side_id, s.finish, None, None) for s in sides]
        for k, rk in enumerate(rks):
            pcs, notes = run_pieces(fl, rk, P, sunk.get(wid, set()), held_all)
            if wid in t261:
                # T-261 r3 governs the heights of this wall: keep its columns (stations), take the H population and
                # tops from the T-261 pieces; V-joint heights next to a T-261 piece are not tied to a station: HELD.
                pcs = [p if p.kind == "COLUMN" else M.Piece("BLOCK", p.length, None, p.member, (), p.under) for p in pcs]
            w = M.make_wall(f"{wid}#{k}" if len(rks) > 1 else wid, STOREY[fl], pcs, sides)
            walls.append((r, rk, w, notes, src))
    return walls, rows, t261, gaps


def t261_h(wid, t261, fl, grp):
    """H joints of a T-261 wall from its own pieces (height = block top above the storey's structural floor)."""
    out = []
    for x in t261[wid]:
        h = float(x["height_m"]) if x["height_m"] else None
        out.append((float(x["length_m"]), h, x["piece"], x["piece_status"]))
    return out


def ledger(plaster_dir=None):
    walls, unknown, t261, gaps = build(plaster_dir)
    J_own, J_dd, F_own, F_ext = [], [], [], []
    per_wall = []
    claimed = {}
    for r, rk, w, notes, src in walls:
        wid, fl, grp = r["wall_id"], r["floor"], r["group"]
        jo, jd = M.joints(w), M.joints_to_soffit(w, FFL)
        if wid in t261:
            # replace the H population by the T-261 pieces (once per side), keep the V joints (HELD heights)
            jo = [j for j in jo if j["dir"] == "V"]
            jd = [j for j in jd if j["dir"] == "V"]
            if rk == runs_of_first(r, rk):
                for side in w.sides:
                    for L, h, nm, st in t261_h(wid, t261, fl, grp):
                        under = "SLAB" if nm.lower().startswith("slab") else "BEAM"
                        jo.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "H",
                                   "at": nm, "length_m": round(L, 6), "level_m": h,
                                   "class": M._h_class(h, side) if side.band_top is not None else "HELD"})
                        jd.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "H",
                                   "at": nm, "length_m": round(L, 6), "level_m": h,
                                   "class": "HELD" if h is None else ("INSIDE" if under == "BEAM" else "AT_BAND_EDGE")})
        band = rk.split("|", 1)[1].split("#")[0]
        has_open = gaps.get((fl, band), 0.0) > 0
        why = "; ".join(x for x in [(r["held_items"] or "") if level_held(r) else "", "; ".join(notes),
                                    "T-261 r3 piece heights are not tied to column stations" if wid in t261 else ""] if x)
        for j in jo + jd:
            j["wall_id"], j["floor"], j["group"], j["run"] = wid, fl, grp, rk
            if j["class"] == "HELD" and not j.get("held"):
                j["held"] = why[:200] or "level not established"
            if j["dir"] == "V" and j["class"] == "INSIDE" and has_open:
                j["bound"] = "UPPER: an opening of this band may meet the column (station alignment not checked)"
        J_own += jo
        J_dd += jd
        for s in w.sides:
            f = M.face_split(w, s, claimed)
            f.update(wall_id=wid, floor=fl, group=grp, run=rk)
            (F_ext if s.side_id == "EXT" else F_own).append(f)
        per_wall.append({"wall_id": wid, "run": rk, "floor": fl, "group": grp, "source": src,
                         "notes": "; ".join(notes), "opening_m_in_band_runs": round(gaps.get((fl, band), 0.0), 4)})
    return {"J_own": J_own, "J_dd": J_dd, "F_own": F_own, "F_ext": F_ext, "walls": per_wall, "unknown": unknown}


def runs_of_first(r, rk):
    return rk  # every run of a T-261 wall carries the wall's pieces once: T-261 walls have one run each (asserted)


# ------------------------------------------------------------------------------------------------ spatter hosts

T244_V3020 = {   # research/agents_t244/T-244_FINISH_REVISION.md s.2 (MERGED 59dbfd0e): the four FIN.PLASTER lines V3.0.20 moves
    "L-31db3c83552682d92ca3": ("HELD", None, 61.46265, 61.71775),
    "L-9b4a7bab033d677e2017": ("HELD", None, 111.0177, 114.3677),
    "L-971f0bdaf68d7fd0966c": ("ASSUMED — OWNER-APPROVED", 52.005, None, None),
    "L-4ce74fc37a08d4bdf0d8": ("ASSUMED — OWNER-APPROVED", 57.775, None, None),
}
T244_TOTALS = {"assumed": 234.9481, "held_lo": 489.4810, "held_hi": 545.4606, "bounded": 9, "blank": 21}


def plaster_hosts():
    """V3.0.20 FIN.PLASTER lines = the T-292 V3.0.15 extract (equal to V3.0.19 on this code: asserted against T-244's
    V3.0.19 totals) with T-244's four changes. PROVISIONAL = owner height / owner deductions (ASSUMED — OWNER-APPROVED,
    G1 Q-43 / Q-48 A); BOUNDED_EXPOSURE = HELD range; BLOCKED_RFI = HELD blank."""
    d = json.load(open(RES / "agents_t292/CANDIDATE_V3015_WALL_FINISH_LINES.json", encoding="utf-8"))
    L = [x for x in d["wall_finish_lines"] if x["item_code"] == "FIN.PLASTER"]
    p19 = sum(float(x["measured_net"]) for x in L if x["evidence_state"] == "PROVISIONAL")
    assert abs(p19 - 184.6192) < 1e-6, p19                       # T-244 s.4: V3.0.19 released FIN.PLASTER
    out = []
    for x in L:
        st = x["evidence_state"]
        if st == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        if x["line_id"] in T244_V3020:
            s_, q, lo, hi = T244_V3020[x["line_id"]]
        elif st == "PROVISIONAL":
            s_, q, lo, hi = "ASSUMED — OWNER-APPROVED", float(x["measured_net"]), None, None
        elif st == "BOUNDED_EXPOSURE":
            s_, q, lo, hi = "HELD", None, float(x["bounded_low"]), float(x["bounded_high"])
        else:
            s_, q, lo, hi = "HELD", None, None, None
        out.append({"line_id": x["line_id"], "item": "FIN.PLASTER", "finish": "PLASTER", "floor": x["floor"],
                    "room": x["room_id"], "faces": [f"{x['line_id']}:faces"], "state": s_, "quantity": q, "lo": lo,
                    "hi": hi, "held": (x["rfi"] or "")[:160] if s_ == "HELD" else ""})
    a = sum(h["quantity"] for h in out if h["quantity"] is not None)
    lo = sum(h["lo"] for h in out if h["lo"] is not None)
    hi = sum(h["hi"] for h in out if h["hi"] is not None)
    assert abs(a - T244_TOTALS["assumed"]) < 1e-4 and abs(lo - T244_TOTALS["held_lo"]) < 1e-4 \
        and abs(hi - T244_TOTALS["held_hi"]) < 1e-4, (a, lo, hi)   # T-244 s.4 V3.0.20 totals reproduced
    return out


def tile_hosts():
    """T-312 (MERGED): one host per wall-tile line, the owner-method face m2 of its room (lines themselves blank)."""
    out = []
    for r in rd(RES / "agents_t312/LINE_SUMMARY_T312.csv"):
        room = r["engine_room"].split(" ")[0]
        q = float(r["ledger_owner_m2"]) if r["ledger_owner_m2"] else None
        st = r["ledger_status"] if q is not None else "HELD"
        lid = r["line_id"] if r["line_id"] != "NO_LINE" else f"NO_LINE:pantry {r['rooms']}"
        out.append({"line_id": lid, "item": "FIN.WALL.TILE", "finish": "TILE", "floor": r["floor"], "room": room,
                    "faces": [f"{lid}:faces"], "state": st, "quantity": q, "lo": None, "hi": None,
                    "held": r["held_item"]})
    return out


def exterior_hosts():
    """T-305 (MERGED): the three FIN.EXT.FINISH lines (net, openings at full, OD-V3B-3) and the NO LINE face groups."""
    out = []
    st_map = {"DRAWING-CONFIRMED": "DRAWING-CONFIRMED"}
    for r in rd(RES / "agents_t305/LINE_SUMMARY_T305.csv"):
        lo, hi = float(r["net_lo_m2"]), float(r["net_hi_m2"])
        if r["status"].startswith("HELD"):
            h = {"state": "HELD", "quantity": None, "lo": lo, "hi": hi, "held": r["status"]}
        elif r["status"].startswith("ASSUMED"):
            h = {"state": "ASSUMED — OWNER-APPROVED", "quantity": lo, "lo": None, "hi": None, "held": ""}
        else:
            h = {"state": st_map[r["status"]], "quantity": lo, "lo": None, "hi": None, "held": ""}
        out.append({"line_id": r["finish_line_id"], "item": "FIN.EXT.FINISH", "finish": "SIGMA", "floor": r["floor"],
                    "room": "EXT", "faces": [f"{r['finish_line_id']}:faces"], **h})
    S = json.load(open(RES / "agents_t305/summary.json", encoding="utf-8"))
    for g in S["by_state_and_line"]:
        if g["state"] != "NO_LINE" or g["m2"] <= 0:
            continue
        cause = g["line_or_cause"]
        lid = f"NO_LINE:{cause}"
        if g["held_hi"] > 0:
            h = {"state": "HELD", "quantity": None, "lo": round(g["m2"] + g["held_lo"], 6),
                 "hi": round(g["m2"] + g["held_hi"], 6), "held": "T-305 held part of the face group"}
        else:
            h = {"state": "DRAWING-CONFIRMED", "quantity": g["m2"], "lo": None, "hi": None, "held": ""}
        # the plinth's final finish (Sigma or stone) is not printed; spatter applies under both (OD-V3B-6 / 7)
        out.append({"line_id": lid, "item": "FIN.EXT.FINISH (no line)", "finish": "SIGMA" if "plinth" not in cause
                    else "CLADDING", "floor": "", "room": "EXT", "faces": [f"{lid}:faces"], **h})
    return out


def spatter_ledger():
    pl, ti, ex = plaster_hosts(), tile_hosts(), exterior_hosts()
    tiled_rooms = {h["room"] for h in ti if not h["line_id"].startswith("NO_LINE")}
    hosts, carried = [], []
    for h in pl:
        if h["room"] in tiled_rooms and h["quantity"] is None and h["lo"] is None:
            # OD-V3B-4: a tiled face takes spatter -> tile preparation -> tile, no plaster under tile: the face is
            # the wall-tile host's; the blank plaster line of the same room hosts nothing (one face once)
            carried.append({"plaster_line": h["line_id"], "room": h["room"], "carried_by": "FIN.WALL.TILE host"})
            continue
        hosts.append(h)
    pantry_plaster = [h for h in hosts if h["room"] == "GF-RC06FED"]
    for h in ti:
        if h["line_id"].startswith("NO_LINE:pantry"):
            # the pantry backsplash lies INSIDE the pantry's own plaster faces (blank line): not a second host
            carried.append({"plaster_line": pantry_plaster[0]["line_id"] if pantry_plaster else "", "room": h["room"],
                            "carried_by": f"pantry backsplash {h['quantity']} m2 inside the pantry plaster faces"})
            continue
        hosts.append(h)
    hosts += ex
    recs = M.spatter_records(hosts, SPATTER_SCOPE)
    M.check_no_zero_held(recs)
    return hosts, recs, carried


def summarise(L):
    def tot(js, d, side_pred=lambda j: True):
        t = defaultdict(lambda: [0.0, 0])
        for j in js:
            if j["dir"] != d or not side_pred(j):
                continue
            k = (j["floor"], j["class"])
            t[k][1] += 1
            if j["length_m"] is not None:
                t[k][0] += j["length_m"]
        return {f"{a}|{b}": [round(v[0], 4), v[1]] for (a, b), v in sorted(t.items())}

    def ftot(fs):
        t = defaultdict(lambda: {"face": 0.0, "conc": 0.0, "blk": 0.0, "n": 0, "held": 0})
        for f in fs:
            a = t[f["floor"]]
            if f["state"] == "MEASURED":
                a["face"] += f["face_m2"]
                a["conc"] += f["concrete_m2"]
                a["blk"] += f["block_m2"]
                a["n"] += 1
            else:
                a["held"] += 1
        return {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(t.items())}

    ext = lambda j: j["side"] == "EXT"  # noqa: E731
    inn = lambda j: j["side"] != "EXT"  # noqa: E731
    return {
        "joints_owner_interior": {"H": tot(L["J_own"], "H", inn), "V": tot(L["J_own"], "V", inn)},
        "joints_drawing_interior": {"H": tot(L["J_dd"], "H", inn), "V": tot(L["J_dd"], "V", inn)},
        "joints_exterior": {"H": tot(L["J_own"], "H", ext), "V": tot(L["J_own"], "V", ext)},
        "faces_owner_interior": ftot(L["F_own"]),
        "faces_exterior": ftot(L["F_ext"]),
        "walls_in_runs": len({w["wall_id"] for w in L["walls"]}),
        "walls_unknown": [u["wall_id"] for u in L["unknown"]],
        "v_upper_bound_joints": sum(1 for j in L["J_own"] if j.get("bound")),
    }


OUT = HERE


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def write_all(L, S, hosts, recs, carried, check=False):
    files = {}
    jcols = ["method", "floor", "wall_id", "run", "group", "side", "finish", "dir", "at", "length_m", "level_m", "class",
             "bound", "held"]
    rows = []
    for meth, js in (("OWNER", L["J_own"]), ("DRAWING-DERIVED", L["J_dd"])):
        for j in js:
            if meth == "DRAWING-DERIVED" and j["side"] == "EXT":
                continue                       # the exterior side is one band (whole storey) under both methods
            rows.append({**{k: _fmt(j.get(k)) for k in jcols}, "method": meth if j["side"] != "EXT" else "EXTERIOR"})
    files["JOINTS_T317.csv"] = (jcols, rows)
    fcols = ["floor", "wall_id", "run", "group", "side", "finish", "state", "face_m2", "concrete_m2", "block_m2", "held"]
    files["FACES_T317.csv"] = (fcols, [{k: _fmt(f.get(k)) for k in fcols} for f in L["F_own"] + L["F_ext"]])
    scols = ["host_line", "host_item", "finish", "floor", "candidate_line", "item", "unit", "state", "quantity", "lo",
             "hi", "held"]
    files["SPATTER_T317.csv"] = (scols, [{k: _fmt(r.get(k)) for k in scols} for r in recs])
    ccols = ["plaster_line", "room", "carried_by"]
    files["CARRIED_T317.csv"] = (ccols, carried)
    import io
    bad = []
    for name, (cols, rr) in files.items():
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rr:
            w.writerow(r)
        txt = buf.getvalue()
        p = OUT / name
        if check:
            if not p.exists() or p.read_text(encoding="utf-8") != txt:
                bad.append(name)
        else:
            p.write_text(txt, encoding="utf-8")
    js = json.dumps(S, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if check:
        if (OUT / "summary.json").read_text(encoding="utf-8") != js:
            bad.append("summary.json")
        if bad:
            raise SystemExit(f"stale: {bad}")
        print("check: every output reproduced")
    else:
        (OUT / "summary.json").write_text(js, encoding="utf-8")


def full_summary(L, recs, carried):
    S = summarise(L)

    def steps(js, pred):
        t = defaultdict(lambda: [0.0, 0])
        for j in js:
            if j["dir"] == "STEP" and pred(j):
                k = f"{j['floor']}|{j['class']}"
                t[k][1] += 1
                t[k][0] += j["length_m"] or 0.0
        return {k: [round(v[0], 4), v[1]] for k, v in sorted(t.items())}

    S["steps_owner_interior"] = steps(L["J_own"], lambda j: j["side"] != "EXT")
    S["steps_drawing_interior"] = steps(L["J_dd"], lambda j: j["side"] != "EXT")
    S["steps_exterior"] = steps(L["J_own"], lambda j: j["side"] == "EXT")
    ub = defaultdict(float)
    for j in L["J_own"]:
        if j.get("bound"):
            ub[f"{'EXT' if j['side'] == 'EXT' else 'INT'}|{j['floor']}"] += j["length_m"]
    S["v_joints_upper_bound_m_owner"] = {k: round(v, 4) for k, v in sorted(ub.items())}
    S["spatter_totals"] = M.spatter_totals(recs)
    det = sum(r["quantity"] for r in recs if r["quantity"] is not None)
    lo = sum(r["lo"] for r in recs if r["lo"] is not None)
    hi = sum(r["hi"] for r in recs if r["hi"] is not None)
    S["spatter_villa"] = {"determinate_m2": round(det, 4), "held_bounded_m2": [round(lo, 4), round(hi, 4)],
                          "held_blank_hosts": sum(1 for r in recs if r["state"] == "HELD" and r["lo"] is None),
                          "hosts": len(recs), "carried_by_another_host": len(carried),
                          "candidate_line": "NO LINE (B4-05 NOT_IMPLEMENTED in BOQ_FAMILY_MASTER 1.15.0)"}
    S["freelancer"] = {"spatter_wet_rooms_kitchens_m2": 433.83, "spatter_under_skirting_m2": 70.7125,
                       "under_skirting_basis": "282.85 m skirting run x 0.25 m (no formula in the cell: 282.85 / 4)",
                       "dry_interior_line": "none (in his plaster rate)", "exterior_line": "none",
                       "joint_mesh_line": "none"}
    S["scope"] = {"B4-05": SPATTER_SCOPE.source, "B9-03": "NOT ANSWERED: no owner rule, drawing note or specification "
                  "(P7757 / ST7757 text census: no mesh / spatter / plaster note; no finishes specification issued)"}
    return S


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    L = ledger()
    hosts, recs, carried = spatter_ledger()
    S = full_summary(L, recs, carried)
    if a.write or a.check:
        write_all(L, S, hosts, recs, carried, check=a.check)
    print(json.dumps({k: S[k] for k in ("spatter_villa", "v_joints_upper_bound_m_owner", "steps_owner_interior",
                                         "steps_drawing_interior", "steps_exterior")}, indent=1, ensure_ascii=False))
    return L, S


if __name__ == "__main__":
    main()
