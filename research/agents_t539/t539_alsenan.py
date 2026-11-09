"""T-539 training-villa builder (research only, unwired): the masonry accessory ledgers V2 (R-T539-1) on the merged
T-355 / T-317 ledgers PLUS the 12 + 1 run ends of COLUMN_END_CENSUS_V3 (T-532 / T-526), with the 0.15 m black walls
under R-T533-1 (T-533: module HELD by name).

Inputs (committed ids and numbers only; no drawing is read here):
  research/agents_t532/out/JUNCTIONS_V3_T532.csv      the 13 END junctions (12 LISTED + 1 HELD)
  research/agents_t526/out/END_CENSUS_V2_T526.csv     column depth / gap / block type / thickness of each end
  research/agents_t526/out/MISSED_ENDS_T526.csv       T-526's per-end deltas (reconciled against, never copied)
  the merged builders' own code: t355_alsenan (panels, ties, joint classes), t317_alsenan (walls, joints),
  t533_alsenan (module register from UPC-BLACK-BLOCK-001, the S-A / S-B / S-C what-if modules)
Writes research/agents_t539/out/: TIES_V2_T539.csv, STRIP_V2_T539.csv, VJOINT_MESH_V2_T539.csv, END_ITEMS_T539.csv,
LINE_FAMILIES_T539.json, SUMMARY_T539.json. `texts()` builds them; the pins test compares them byte for byte.
"""
from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
for p in ("agents_t533", "agents_t520", "agents_t355", "agents_t317", "agents_t526"):
    sys.path.insert(0, str(RES / p))
sys.path.insert(0, str(HERE))
import accessory_ledger_v2 as V  # noqa: E402
import block_module_v1 as BM  # noqa: E402
import t317_alsenan as T317  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402
import t355_alsenan as T355  # noqa: E402
import t355_masonry_accessories as X  # noqa: E402
import t533_alsenan as T533  # noqa: E402

OUT = HERE / "out"
JUNCTIONS = RES / "agents_t532/out/JUNCTIONS_V3_T532.csv"
CENSUS = RES / "agents_t526/out/END_CENSUS_V2_T526.csv"
MISSED = RES / "agents_t526/out/MISSED_ENDS_T526.csv"
T355_FILES = ("SHARMAT_T355.csv", "MESH_BY_WALL_T355.csv", "JOINT_MESH_CLASS_T355.csv")
JOINT = 0.010
# T-488 / T-520: the 2F storey is 4.25 - b_r (roof-plate level not printed, D-39); T-317 / T-355 use 4.20 (T-112).
D39_TOP_RANGE_2F = (3.75, 3.85)     # block top under the 0.40 beam over b_r = 0.10 .. 0 (T-520 what-if pair)


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def scenarios():
    """T-533's what-if modules as courses (face height + 10 mm bed): figures beside, never quantities."""
    out = []
    for sid, label, (w, h, W, H) in T533.SCENARIOS:
        out.append((sid, X.course_spec(h, round(H - h, 6), f"T-533 {sid} what-if: {label}", "WHAT-IF (not a source)")))
    return out


def register():
    reg, _ng = T533.register()
    return reg


def x_course(c):
    return None if c is None else X.course_spec(c.block_h, c.joint, c.source, c.status)


def wall_course(reg, btype, t):
    c, held = V.course_for(BM.resolve, reg, btype, float(t))
    return c, held


def check_primary(reg):
    """the register's 0.20 entry must be exactly T-355's PRIMARY course (else the ledgers disagree on the module)."""
    c, held = wall_course(reg, "BLACK", 0.20)
    p = T355.SPEC["PRIMARY"]
    if held or abs(c.block_h - p.block_h) > 1e-9 or abs(c.joint - p.joint) > 1e-9:
        raise V.LedgerV2Error(f"R-T533-1 0.20 entry {c} differs from T-355 PRIMARY {p}")
    return c


# ------------------------------------------------------------------------------------------------- ends

def ends():
    J = [r for r in _csv(JUNCTIONS) if r["source"] == "V3_END"]
    C = {(r["run"], r["end"]): r for r in _csv(CENSUS) if r["end"] != ""}
    Mi = {(r["run"], r["end"]): r for r in _csv(MISSED)}
    out = []
    for j in J:
        e = j["at"].split()[-1]
        c, m = C[(j["run"], e)], Mi[(j["run"], e)]
        if c["wall_id"] != j["wall_id"] or m["wall_id"] != j["wall_id"]:
            raise V.LedgerV2Error(f"{j['run']} end {e}: wall ids disagree")
        out.append({"run": j["run"], "end": int(e), "wall_id": j["wall_id"], "class_v3": j["class"],
                    "state_v3": j["state"], "held_v3": j["held"], "column_t119": j["column_at"],
                    "block_type": c["block_type"], "t_m": c["t_m"], "gap_mm": c["gap_mm"],
                    "column_depth_m": float(c["column_depth_mm"]) / 1000 if c["column_depth_mm"] else None,
                    "run_end_type": c["run_end_type"], "t526": m})
    if len(out) != 13:
        raise V.LedgerV2Error(f"expected 12 + 1 END junctions, found {len(out)}")
    return out


def insert_column(pieces, rk, end, depth, make):
    idx = [i for i, x in enumerate(pieces) if x.key.startswith(rk + "@")]
    col = make("COLUMN", depth, None, f"{rk}@END{end}")
    pcs = list(pieces)
    pcs.insert(idx[0] if end == 0 else idx[-1] + 1, col)
    return tuple(pcs), col.key


def end_ties(e, panel_rec, reg, scen):
    p = panel_rec["tie"]
    c, held = wall_course(reg, e["block_type"], e["t_m"])
    if e["state_v3"] != "LISTED":
        return V.tie_record(e["state_v3"], e["held_v3"], None, None, None, ()), None
    pcs, key = insert_column(p.pieces, e["run"], e["end"], e["column_depth_m"], X.make_piece)
    p2 = dataclasses.replace(p, pieces=pcs)
    add = [t for t in X.junctions(p2) if t["column_at"] == key]
    if len(add) != 1 or len(X.junctions(p2)) != len(X.junctions(p)) + 1:
        raise V.LedgerV2Error(f"{e['run']} end {e['end']}: tie junctions moved elsewhere")
    top = add[0]["top"]
    sliver = e["head"][1] if e["head"][1] == V.SLIVER_HELD else ""
    # T-355 precedence (ledger()): the white-block course hold names the junction before a wall-level hold
    if panel_rec["course_held"]:
        rec = V.tie_record("LISTED", "", None, panel_rec["course_held"], top, ())
    elif p.held:
        rec = V.tie_record("LISTED", "", None, p.held, top, scen if c is None else ())
    elif sliver:
        rec = V.tie_record("HELD", sliver, None, None, None, ())
    else:
        rec = V.tie_record("LISTED", "", c, held, top, scen if c is None else ())
    # T-355's own tie function on the PRIMARY course (what T-526 carried)
    prim = [t for t in X.ties(dataclasses.replace(p2, course=T355.SPEC["PRIMARY"] if p.course else None))
            if t["column_at"] == key][0]
    rec["t355_primary_ties"] = prim["ties"]
    rec["top"] = top
    return rec, key


def end_vjoints(e, walls, classes, gaps):
    rk, end = e["run"], e["end"]
    ws = [(r, w) for (r, k, w, _n, _s) in walls if k == rk]
    if len(ws) != 1:
        raise V.LedgerV2Error(f"{rk}: {len(ws)} T-317 walls")
    r, w = ws[0]
    if e["state_v3"] != "LISTED":
        return [{"side": s.side_id, "finish": s.finish, "owner_m": None, "drawing_m": None, "t317_drawing_m": None,
                 "class": classes.get((e["wall_id"], rk, s.side_id), {}).get("class", "UNKNOWN"), "state": "HELD",
                 "held": e["held_v3"]} for s in w.sides if s.finish not in M.NOT_FINISHED]
    col = M.Piece("COLUMN", e["column_depth_m"], None, f"{rk}@END{end}")
    ps = (col,) + tuple(w.pieces) if end == 0 else tuple(w.pieces) + (col,)
    w2 = M.Wall(w.wall_id, w.storey_h, ps, w.sides)
    own = {j["side"]: j for j in M.joints(w2) if j["dir"] == "V" and j["at"] == col.member}
    drw = {j["side"]: j for j in M.joints_to_soffit(w2, T317.FFL) if j["dir"] == "V" and j["at"] == col.member}
    blk = w.pieces[0] if end == 0 else w.pieces[-1]
    if e["head"][1] == V.SLIVER_HELD:
        out = []
        for s in w.sides:
            if s.finish in M.NOT_FINISHED:
                continue
            other = own[s.side_id].get("held") or drw[s.side_id].get("held") or ""
            out.append({"side": s.side_id, "finish": s.finish, "owner_m": None, "drawing_m": None,
                        "t317_drawing_m": None, "class": classes[(e["wall_id"], rk, s.side_id)]["class"],
                        "state": "HELD", "held": V.SLIVER_HELD + (f"; also: {other}" if other else ""), "bound": ""})
        return out
    hand = {x["side"]: x for x in V.end_vjoint([V.FinishedSide(s.side_id, s.finish, s.band_bottom, s.band_top)
                                                for s in w.sides], blk.top, T317.FFL)}
    band = rk.split("|", 1)[1].split("#")[0]
    upper = gaps.get((r["floor"], band), 0.0) > 0
    out = []
    for s in w.sides:
        if s.finish in M.NOT_FINISHED:
            continue
        o, d, h = own[s.side_id], drw[s.side_id], hand[s.side_id]
        cls = classes.get((e["wall_id"], rk, s.side_id))
        if cls is None:
            raise V.LedgerV2Error(f"{e['wall_id']} {rk} {s.side_id}: no T-355 face class row")
        if o["class"] == "HELD" or d["class"] == "HELD":
            out.append({"side": s.side_id, "finish": s.finish, "owner_m": None, "drawing_m": None,
                        "t317_drawing_m": None, "class": cls["class"], "state": "HELD",
                        "held": o.get("held") or d.get("held") or "", "bound": ""})
            continue
        # independent hand formula (R-T539-1 item 5) must agree with T-317's code on the owner band and on the raw
        # drawing band of an interior side
        if abs(h["owner_m"] - o["length_m"]) > 1e-9 or (s.side_id != "EXT" and abs(h["drawing_m"] - d["length_m"]) > 1e-9):
            raise V.LedgerV2Error(f"{e['wall_id']} {s.side_id}: hand {h} vs T-317 {o['length_m']} / {d['length_m']}")
        out.append({"side": s.side_id, "finish": s.finish, "owner_m": h["owner_m"], "drawing_m": h["drawing_m"],
                    "t317_drawing_m": d["length_m"], "class": cls["class"], "state": "MEASURED", "held": "",
                    "bound": "UPPER: an opening of this band may meet the column (station alignment not checked)"
                    if upper else ""})
    return out


# ------------------------------------------------------------------------------------------------- build

def build():
    reg, scen = register(), scenarios()
    check_primary(reg)
    panels, _un, _named, _lost = T355.panels("PRIMARY")
    P = {p["wall_id"]: p for p in panels}
    byrun = {rk: p for p in panels for rk in p["runs"]}
    led = T355.ledger("PRIMARY")
    jc = T355.joint_classes()
    classes = {(r["wall_id"], r["run"], r["side"]): r for r in jc}
    walls, _u, _t261, gaps = T317.build()
    E = ends()
    for e in E:
        ws = [w for (_r, k, w, _n, _s) in walls if k == e["run"]]
        ps = ws[0].pieces
        endp, nxt = (ps[0], ps[1] if len(ps) > 1 else None) if e["end"] == 0 else (ps[-1], ps[-2] if len(ps) > 1 else None)
        if endp.kind != "BLOCK":
            raise V.LedgerV2Error(f"{e['run']} end {e['end']}: end piece is {endp.kind}")
        tri = lambda q: None if q is None or q.kind != "BLOCK" else (q.length, q.top, q.member)
        e["head"] = V.end_head(tri(endp), tri(nxt))

    # --- ties: interior junctions (T-355 population) restated under R-T533-1, then the END junctions
    interior = []
    for t in led["ties"]:
        p = P[t["wall_id"]]
        c, held = wall_course(reg, p["block_type"], p["t_m"])
        jn = {"wall_id": t["wall_id"], "column_at": t["column_at"], "face": t["face"]}
        base = {"floor": t["floor"], "block_type": p["block_type"], "t_m": f"{float(p['t_m']):.2f}", "class_v3": "INTERIOR",
                "top": t["top"], "t355_state": t["state"], "t355_ties": t["ties"]}
        if t["state"] != "MEASURED":
            # HELD in T-355 already (white course, wall-level hold, unknown top): kept with T-355's own text
            rec = V.tie_record("HELD", t["held"], None, None, None, ())
        else:
            rec = V.tie_record("LISTED", "", c, held, t["top"], scen if (c is None and p["block_type"] == "BLACK") else ())
        if rec["state"] == "MEASURED" and rec["ties"] != t["ties"]:
            raise V.LedgerV2Error(f"{t['wall_id']} {t['column_at']}: V2 {rec['ties']} vs T-355 {t['ties']}")
        interior.append({**jn, **base, **rec})
    endrows, end_items = [], []
    for e in E:
        p = byrun[e["run"]]
        rec, key = end_ties(e, p, reg, scen if p["block_type"] == "BLACK" else ())
        face = "column_start" if e["end"] == 1 else "column_end"
        band = e["run"].split("|", 1)[1].split("#")[0]
        rec["bound"] = ("UPPER: an opening of this band may stand at the column (station alignment not checked; "
                        "no tie over the opening height there)") if gaps.get((p["floor"], band), 0.0) > 0 else ""
        endrows.append({"wall_id": e["wall_id"], "column_at": key or f"{e['run']}@END{e['end']}", "face": face,
                        "floor": p["floor"], "block_type": e["block_type"], "t_m": f"{float(e['t_m']):.2f}", "class_v3": e["class_v3"],
                        "top": rec.get("top"), "t355_state": "", "t355_ties": None,
                        "column_t119": e["column_t119"], **{k: v for k, v in rec.items() if k != "top"}})
    ties = V.merge_population(interior, endrows)
    V.no_zero_held(ties, ("ties",))

    # --- strip by wall (T-355 population) under R-T533-1; END junctions add 0 m.l (R-T539-1 item 4)
    strip = []
    for w in led["by_wall"]:
        p = P[w["wall_id"]]
        c, held = wall_course(reg, p["block_type"], p["t_m"])
        row = {"wall_id": w["wall_id"], "floor": w["floor"], "group": w["group"], "block_type": w["block_type"],
               "t_m": f"{float(w['t_m']):.2f}", "block_run_m": w["block_run_m"], "t355_state": w["state"], "t355_net_m": w["net_m"],
               "t355_held_m": w["held_m"]}
        fig = {}
        if p["block_type"] == "BLACK" and not p["mesh"].held:
            for sid, sc in scen:
                recs, _st = X.mesh_levels(dataclasses.replace(p["mesh"], course=sc))
                fig[sid] = round(sum(r["net_m"] for r in recs), 6) if recs else None
        if w["state"].startswith("HELD") or w["net_m"] is None:
            row.update(state=w["state"] if w["state"].startswith("HELD") else "HELD: " + w["state"], net_m=None,
                       held_m=None, held="(T-355 state kept)")
        elif c is None:
            row.update(state="HELD", net_m=None, held_m=None, held=held)
        else:
            # resolved module = T-355 PRIMARY (check_primary): the S-A what-if is the same course, so it must agree
            if fig.get("S-A") is None or abs(fig["S-A"] - w["net_m"]) > 1e-6:
                raise V.LedgerV2Error(f"{w['wall_id']}: S-A {fig.get('S-A')} vs T-355 {w['net_m']}")
            fig = {}
            row.update(state=w["state"], net_m=w["net_m"], held_m=w["held_m"], held="")
        row.update({f"fig_{k}_net_m": v for k, v in fig.items()})
        strip.append(row)
    V.no_zero_held(strip, ("net_m", "held_m"))

    # --- V-joint mesh: END deltas per side, classed with T-355's own face class of that (wall, run, side)
    vj = []
    for e in E:
        sides = end_vjoints(e, walls, classes, gaps)
        tie = next(r for r in endrows if r["column_at"].startswith(f"{e['run']}@END{e['end']}"))
        strip_d = V.end_strip_delta(float(e["t526"]["d_length_m"]), float(e["gap_mm"]) / 1000, JOINT) \
            if e["state_v3"] == "LISTED" else None
        for s in sides:
            vj.append({"wall_id": e["wall_id"], "run": e["run"], "end": e["end"], **s})
        own = [s["owner_m"] for s in sides if s["state"] == "MEASURED"]
        drw = [s["drawing_m"] for s in sides if s["state"] == "MEASURED"]
        t526 = e["t526"]
        end_items.append({
            "floor": tie["floor"], "wall_id": e["wall_id"], "run": e["run"], "end": e["end"],
            "run_end_type": e["run_end_type"], "class_v3": e["class_v3"], "column_t119": e["column_t119"],
            "block_type": e["block_type"], "t_m": e["t_m"], "top": tie["top"],
            "ties_state": tie["state"], "ties": tie["ties"], "ties_held": tie["held"], "ties_bound": tie["bound"],
            "fig_S-A_ties": tie["figures"].get("S-A"), "fig_S-B_ties": tie["figures"].get("S-B"),
            "fig_S-C_ties": tie["figures"].get("S-C"), "t355_primary_ties": tie.get("t355_primary_ties"),
            "t526_d_ties": t526["d_ties_nr"], "strip_added_m": strip_d,
            "vjoint_sides": len(sides), "vjoint_held_sides": sum(1 for s in sides if s["state"] == "HELD"),
            "vjoint_owner_m": round(sum(own), 6) if own else None,
            "vjoint_drawing_m": round(sum(drw), 6) if drw else None,
            "vjoint_t317_raw_drawing_m": round(sum(s["t317_drawing_m"] for s in sides if s["state"] == "MEASURED"), 6)
            if drw else None,
            "t526_d_mesh_owner": t526["d_mesh_owner_ml"], "t526_d_mesh_drawing": t526["d_mesh_drawing_ml"],
            "end_piece_sliver": e["head"][2],
            "classes": " ".join(f"{s['side']}:{s['class']}" for s in sides)})
    return {"ties": ties, "strip": strip, "vj": vj, "ends": end_items, "jc": jc, "led": led,
            "interior_slivers": interior_slivers(walls), "d39": d39_sensitivity(P, reg, ties, strip)}


def d39_sensitivity(P, reg, ties, strip):
    """2F datum (D-39): T-317 / T-355 put every 2F block top on a 4.20 m storey (T-112); T-488 / T-520 read 4.25 - b_r
    with b_r not printed. The 2F tops therefore move by 0.05 - b_r. Ties and strip of the MEASURED 2F rows are re-run
    with every block top shifted by -0.05 and +0.05 m (b_r = 0.10 and 0): a count that moves is named, not chosen."""
    def shift(panel, d):
        return dataclasses.replace(panel, pieces=tuple(
            x if x.kind != "BLOCK" or x.top is None else dataclasses.replace(x, top=round(x.top + d, 6))
            for x in panel.pieces))
    out = {"basis": "2F block top + (0.05 - b_r), b_r in [0, 0.10] (D-39)", "ties": {}, "strip_net_m": {}}
    for wid, p in sorted(P.items()):
        if p["floor"] != "2F":
            continue
        c, held = wall_course(reg, p["block_type"], p["t_m"])
        if c is None or p["tie"].held:
            continue
        xc = x_course(c)
        base_t = [r for r in ties if r["wall_id"] == wid and r["population"] == "INTERIOR" and r["state"] == "MEASURED"]
        if base_t:
            keys = {(r["column_at"], r["face"]) for r in base_t}
            rng = []
            for d in (-0.05, 0.05):
                ts = X.ties(dataclasses.replace(shift(p["tie"], d), course=xc))
                rng.append(sum(t["ties"] for t in ts if (t["column_at"], t["face"]) in keys and t["ties"] is not None))
            out["ties"][wid] = {"v2": sum(r["ties"] for r in base_t), "low": rng[0], "high": rng[1]}
        srow = next((r for r in strip if r["wall_id"] == wid and r["net_m"] is not None), None)
        if srow:
            rng = []
            for d in (-0.05, 0.05):
                recs, _st = X.mesh_levels(dataclasses.replace(shift(p["mesh"], d), course=xc))
                rng.append(round(sum(r["net_m"] for r in recs), 6))
            out["strip_net_m"][wid] = {"v2": srow["net_m"], "low": rng[0], "high": rng[1]}
    out["ties_moving"] = sorted(w for w, v in out["ties"].items() if not v["v2"] == v["low"] == v["high"])
    out["strip_moving"] = sorted(w for w, v in out["strip_net_m"].items() if not v["v2"] == v["low"] == v["high"])
    return out


def interior_slivers(walls):
    """R-T539-1 item 6 over the INTERIOR population: every sub-5 mm masonry piece beside a column piece. The merged
    T-355 / T-317 code takes the head from the piece next to the column; that is safe only when the sliver is a cut of
    the same member as the next piece, or its own top is not established (the junction is then HELD there)."""
    out = {"SAME_MEMBER": 0, "OTHER_MEMBER": 0, "other_member_with_known_top": [], "other_member": []}
    for r, rk, w, _n, _s in walls:
        ps = w.pieces
        for i, c in enumerate(ps):
            if c.kind != "COLUMN":
                continue
            for d in (-1, 1):
                j = i + d
                if not (0 <= j < len(ps)) or ps[j].kind != "BLOCK" or ps[j].length >= V.SLIVER_M - V.TOL:
                    continue
                k = j + d
                nxt = ps[k] if 0 <= k < len(ps) and ps[k].kind == "BLOCK" else None
                h = V.end_head((ps[j].length, ps[j].top, ps[j].member),
                               None if nxt is None else (nxt.length, nxt.top, nxt.member))
                kind = h[2].split(" ")[0].rstrip(":")
                out[kind] += 1
                if kind == "OTHER_MEMBER":
                    out["other_member"].append(f"{r['wall_id']} {c.member} {h[2]}")
                    if ps[j].top is not None:
                        out["other_member_with_known_top"].append(f"{r['wall_id']} {c.member}")
    return out


# ------------------------------------------------------------------------------------------------- summary

def _num(rows, k):
    return round(sum(float(r[k]) for r in rows if r.get(k) not in (None, "")), 6)


def summarise(B):
    ties, strip, vj, E, jc = B["ties"], B["strip"], B["vj"], B["ends"], B["jc"]
    t355 = [r for r in ties if r["population"] == "INTERIOR"]
    ends_ = [r for r in ties if r["population"] == "END"]

    def tt(rows):
        d = V.tie_totals(rows)
        d["by_held_cause"] = {}
        for r in rows:
            if r["state"] != "MEASURED":
                k = r["held"].removeprefix("HELD: ").split(":")[0][:60]
                d["by_held_cause"][k] = d["by_held_cause"].get(k, 0) + 1
        d["by_held_cause"] = dict(sorted(d["by_held_cause"].items()))
        d["figures_015"] = {sid: sum(r["figures"].get(sid) or 0 for r in rows if r["t_m"] == "0.15" and r["figures"])
                            for sid in ("S-A", "S-B", "S-C")}
        d["figures_015_junctions"] = sum(1 for r in rows if r["t_m"] == "0.15" and r["figures"])
        d["figures_015_unknown_top"] = sum(1 for r in rows if r["t_m"] == "0.15" and r["figures"]
                                           and r["figures"].get("S-A") is None)
        return d
    t355_before = sum(r["t355_ties"] for r in t355 if r["t355_state"] == "MEASURED")
    moved_015 = [r for r in t355 if r["t355_state"] == "MEASURED" and r["state"] != "MEASURED"]
    cl_before, cl_after = defaultdict(lambda: [0.0, 0.0, 0]), defaultdict(lambda: [0.0, 0.0, 0])
    for r in jc:
        cl_before[r["class"]][0] += r["owner_band_m"]
        cl_before[r["class"]][1] += r["drawing_band_m"]
        cl_after[r["class"]][0] += r["owner_band_m"]
        cl_after[r["class"]][1] += r["drawing_band_m"]
    for s in vj:
        if s["state"] == "MEASURED":
            cl_after[s["class"]][0] += s["owner_m"]
            cl_after[s["class"]][1] += s["drawing_m"]
        else:
            cl_after[s["class"]][2] += 1
    rcl = lambda d: {k: {"owner_band_m": round(v[0], 4), "drawing_band_m": round(v[1], 4), "held_end_sides": v[2]}
                     for k, v in sorted(d.items())}
    s_meas = [r for r in strip if r["net_m"] is not None]
    s_015 = [r for r in strip if r["t_m"] == "0.15" and r["block_type"] == "BLACK" and r["t355_net_m"] is not None]
    reg = register()
    c020, _ = wall_course(reg, "BLACK", 0.20)
    d39 = {e["wall_id"]: list(V.tie_range(c020, *D39_TOP_RANGE_2F)) for e in E
           if e["floor"] == "2F" and abs(float(e["t_m"]) - 0.20) < 1e-9}
    d39_draw = {e["wall_id"]: f"2 x ({D39_TOP_RANGE_2F[1]:.2f} - b_r - {T317.FFL:.2f}) = "
                f"{2 * (D39_TOP_RANGE_2F[1] - T317.FFL):.2f} - 2 b_r m (T-488 basis) vs {e['vjoint_drawing_m']} (T-317 4.20)"
                for e in E if e["floor"] == "2F" and e["vjoint_drawing_m"] is not None}
    S = {
        "rule": V.RULE, "schema": V.SCHEMA,
        "module_register": {"0.20": "RESOLVED (UPC-BLACK-BLOCK-001, 0.19 + 0.010 = 0.200 m = T-355 PRIMARY)",
                            "0.15": "HELD (R-T533-1: no sourced entry)", "white": "HELD (Q-60)"},
        "what_if_modules": {sid: round(sc.module, 6) for sid, sc in scenarios()},
        "ends": {"listed": sum(1 for e in E if e["class_v3"] != "BEAM-PARTIAL_COLUMN"),
                 "held": [f"{e['wall_id']} end {e['end']}" for e in E if e["class_v3"] == "BEAM-PARTIAL_COLUMN"]},
        "end_ties": {"measured_nr": sum(e["ties"] for e in E if e["ties_state"] == "MEASURED"),
                     "measured_ends": [f"{e['wall_id']} e{e['end']} {e['ties']}" for e in E if e["ties_state"] == "MEASURED"],
                     "held_015_figures": {e["wall_id"]: {"S-A": e["fig_S-A_ties"], "S-B": e["fig_S-B_ties"],
                                                         "S-C": e["fig_S-C_ties"]}
                                          for e in E if e["t_m"] == "0.15" and e["fig_S-A_ties"] is not None},
                     "measured_with_upper_bound": [f"{e['wall_id']} e{e['end']}" for e in E
                                                   if e["ties_state"] == "MEASURED" and e["ties_bound"]],
                     "t526_carried_nr": _num(E, "t526_d_ties"),
                     "t355_primary_on_ends_nr": sum(e["t355_primary_ties"] or 0 for e in E),
                     "d39_2f_tie_range_0200": d39},
        "interior_slivers": B["interior_slivers"],
        "d39_2f_sensitivity": B["d39"],
        "end_piece_slivers": {f"{e['wall_id']} e{e['end']}": e["end_piece_sliver"] for e in E if e["end_piece_sliver"]},
        "end_strip_added_m": round(sum(e["strip_added_m"] or 0.0 for e in E), 6),
        "end_vjoint": {"owner_m": _num(E, "vjoint_owner_m"), "drawing_m_classed": _num(E, "vjoint_drawing_m"),
                       "drawing_m_t317_raw": _num(E, "vjoint_t317_raw_drawing_m"),
                       "t526_owner": _num(E, "t526_d_mesh_owner"), "t526_drawing": _num(E, "t526_d_mesh_drawing"),
                       "held_end_sides": sum(e["vjoint_held_sides"] for e in E),
                       "by_class": {k: v for k, v in rcl({c: [sum(s["owner_m"] for s in vj if s["class"] == c and
                                                                   s["state"] == "MEASURED"),
                                                               sum(s["drawing_m"] for s in vj if s["class"] == c and
                                                                   s["state"] == "MEASURED"),
                                                               sum(1 for s in vj if s["class"] == c and s["state"] == "HELD")]
                                                          for c in sorted({s["class"] for s in vj})}).items()},
                       "d39_2f_drawing": d39_draw},
        "ties_t355_interior": {"measured_nr_t355": t355_before,
                               "moved_to_held_015": {"junctions": len(moved_015),
                                                     "ties_t355": sum(r["t355_ties"] for r in moved_015),
                                                     "walls": sorted({r["wall_id"] for r in moved_015})}},
        "ties_v2": tt(ties),
        "ties_v2_interior": tt(t355), "ties_v2_end": tt(ends_),
        "strip_v2": {"t355_net_m": round(sum(r["t355_net_m"] or 0 for r in strip), 4),
                     "v2_measured_net_m": round(sum(r["net_m"] for r in s_meas), 4),
                     "v2_measured_walls": len(s_meas),
                     "held_015": {"walls": len(s_015), "t355_net_m": round(sum(r["t355_net_m"] for r in s_015), 4),
                                  "figures_net_m": {sid: round(sum(r.get(f"fig_{sid}_net_m") or 0 for r in s_015), 4)
                                                    for sid in ("S-A", "S-B", "S-C")}},
                     "end_added_m": 0.0},
        "vjoint_by_class_before": rcl(cl_before), "vjoint_by_class_after": rcl(cl_after),
        "reconcile_board": {
            "ties_+30": "T-526 +30 nr = 18 MEASURED (0.20 m: 1F-W09, 2F-W00, 2F-W01, 6 each) + 12 HELD by name "
                        "(0.15 m 1F-W23 / 2F-W08, module HELD R-T533-1; figures beside)",
            "mesh_+40.90_owner": "the T-317 plaster-stage V joints (B9-03), not the bed-joint strip; strip +0 m.l",
            "mesh_+44.10_drawing": "T-317 raw drawing band; classed as T-355 R-T355-4 (exterior Sigma side one band) "
                                   "it is +44.20: GF-W16 EXT side 3.75 (owner = drawing) vs raw 3.65"},
        "sha256_inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (JUNCTIONS, CENSUS, MISSED)}
        | {n: hashlib.sha256((RES / "agents_t355" / n).read_bytes()).hexdigest() for n in T355_FILES},
    }
    return S


def _f(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, dict):
        return " ".join(f"{k}={'' if x is None else x}" for k, x in v.items())
    return str(v)


def _table(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _f(r.get(k)) for k in cols})
    return b.getvalue()


def texts():
    B = build()
    S = summarise(B)
    fam = V.line_families()
    q = {"MAS.TIE.SHARMAT": {"measured_nr": S["ties_v2"]["ties_measured"], "held_junctions": S["ties_v2"]["held_junctions"]},
         "MAS.MESH.BED_JOINT": {"measured_net_m": S["strip_v2"]["v2_measured_net_m"],
                                "held_015_walls": S["strip_v2"]["held_015"]["walls"]},
         "MAS.MESH.JOINT": {"by_class_after": S["vjoint_by_class_after"]}}
    for f in fam:
        f["quantity_v2_alsenan"] = q[f["proposed_code"]]
    tc = ["population", "wall_id", "floor", "block_type", "t_m", "class_v3", "column_at", "face", "column_t119", "top",
          "t355_state", "t355_ties", "state", "ties", "held", "bound", "figures"]
    for r in B["ties"]:
        r["figures"] = {k: v for k, v in r["figures"].items()} if r["figures"] else None
    sc = ["wall_id", "floor", "group", "block_type", "t_m", "block_run_m", "t355_state", "t355_net_m", "t355_held_m",
          "state", "net_m", "held_m", "held", "fig_S-A_net_m", "fig_S-B_net_m", "fig_S-C_net_m"]
    vc = ["wall_id", "run", "end", "side", "finish", "class", "state", "owner_m", "drawing_m", "t317_drawing_m", "bound",
          "held"]
    ec = ["floor", "wall_id", "run", "end", "run_end_type", "class_v3", "column_t119", "block_type", "t_m", "top",
          "ties_state", "ties", "ties_held", "ties_bound", "fig_S-A_ties", "fig_S-B_ties", "fig_S-C_ties", "t355_primary_ties",
          "t526_d_ties", "strip_added_m", "vjoint_sides", "vjoint_held_sides", "vjoint_owner_m", "vjoint_drawing_m",
          "vjoint_t317_raw_drawing_m", "t526_d_mesh_owner", "t526_d_mesh_drawing", "end_piece_sliver", "classes"]
    return {"TIES_V2_T539.csv": _table(B["ties"], tc), "STRIP_V2_T539.csv": _table(B["strip"], sc),
            "VJOINT_MESH_V2_T539.csv": _table(B["vj"], vc), "END_ITEMS_T539.csv": _table(B["ends"], ec),
            "LINE_FAMILIES_T539.json": json.dumps(fam, indent=1, ensure_ascii=False) + "\n",
            "SUMMARY_T539.json": json.dumps(S, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    T = texts()
    if "--check" in argv:
        bad = [k for k, v in T.items() if not (OUT / k).exists() or (OUT / k).read_text(encoding="utf-8") != v]
        print("reproduce:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for k, v in T.items():
        (OUT / k).write_text(v, encoding="utf-8")
    print(T["SUMMARY_T539.json"][:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
