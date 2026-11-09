"""T-526 training-villa builder (research only): the effect of every run end that COLUMN_END_CENSUS_V2 (R-T526-1) finds
against an RC column which the V1 junction censuses (T-274 pieces -> T-355 sharmat ties, T-317 joint mesh / V joints)
never list, end by end, on the merged ledgers' own code.

Inputs (committed, numbers and ids only): research/agents_t526/out/END_CENSUS_V2_T526.csv (t526_extract.py, the
drawing), the merged T-274 / T-288 / T-317 / T-355 / T-506 / T-516 / T-520 files the imported builders read.
Per end: (a) length / blockwork m2 / blocks (Q-75 12.5 per m2) along the run: the end face IS the column face (gap 0 on
every end found), so the clear length between faces does not move; (b) T-317 V-joint mesh m.l per finished side
(owner band and drawing-derived band) added by the end junction; (c) T-355 sharmat ties (R-T355-1 levels, PRIMARY course)
added; (d) B9-04 perimeter joint mortar (R-T520-1): exact before / after on the T-520 wall set (the end class F without the
column, C with it), else the bound [0, kappa b j h] of the one face, HELD by name (the wall's other ends and openings are
not in the T-520 ledger); white (AAC, thin-bed) walls: R-T520-1 is for mortared joints, HELD (Q-60).
Writes research/agents_t526/out/MISSED_ENDS_T526.csv and SUMMARY_T526.json.

    python3 -I research/agents_t526/t526_alsenan.py [--check]
"""
from __future__ import annotations

import copy
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
for p in ("agents_t520", "agents_t355", "agents_t317", "agents_t274"):
    sys.path.insert(0, str(RES / p))
sys.path.insert(0, str(HERE))
import end_census_v2 as E  # noqa: E402
import perimeter_joint_v1 as PJ  # noqa: E402
import t317_alsenan as T317  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402
import t355_alsenan as T355  # noqa: E402
import t355_masonry_accessories as X  # noqa: E402
import t520_alsenan as T520  # noqa: E402

OUT = HERE / "out"
CENSUS = OUT / "END_CENSUS_V2_T526.csv"
BLOCKS_PER_M2 = 12.5          # Q-75 (owner): 40 x 20 module, waste separate
WHITE = "white (AAC) block, thin-bed adhesive: R-T520-1 is for mortared joints and the course is HELD (Q-60)"
NOT_IN_T520 = ("wall outside the T-520 24-wall ledger (its other end and openings are not measured there): "
               "bound of the one face only")
RULE = ("R-T526-1 COLUMN_END_CENSUS_V2: a block-to-column junction exists at every run end whose end face meets a "
        "column outline across the full wall thickness within one joint, whether or not the column is a piece of the "
        "run; V1 listed only BLOCK / COLUMN boundaries between consecutive pieces of one run")


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def census():
    return _csv(CENSUS)


def missed(rows):
    return [r for r in rows if r["missed_by_v1"] in ("YES", "HELD") and r["wall_id"]]


def t317_delta(r, walls):
    """V joints added on T-317's own wall object when the column piece is put beyond the end (both bands)."""
    rk, end = r["run"], int(r["end"])
    ws = [w for (_reg, k, w, _n, _s) in walls if k == rk]
    if len(ws) != 1:
        raise E.EndCensusError(f"{rk}: {len(ws)} T-317 walls")
    w = ws[0]
    col = M.Piece("COLUMN", float(r["column_depth_mm"]) / 1000, None, f"{rk}@END{end}")
    ps = (col,) + tuple(w.pieces) if end == 0 else tuple(w.pieces) + (col,)
    w2 = M.Wall(w.wall_id, w.storey_h, ps, w.sides)
    out = {}
    for name, f in (("owner", M.joints), ("drawing", lambda x: M.joints_to_soffit(x, T317.FFL))):
        old = [j for j in f(w) if j["dir"] == "V"]
        new = [j for j in f(w2) if j["dir"] == "V"]
        add = [j for j in new if j["at"] == col.member]
        if len(new) - len(old) != len(add):
            raise E.EndCensusError(f"{rk}: V joints moved elsewhere")
        held = [j for j in add if j["class"] == "HELD"]
        known = [j for j in add if j["class"] != "HELD"]
        out[name] = {"sides": len(add), "ml": round(sum(j["length_m"] for j in known), 6) if known else None,
                     "held": len(held), "held_why": sorted({j.get("held", "") for j in held})}
    return out


def t355_delta(r, panels):
    rk, end = r["run"], int(r["end"])
    ps = [p for p in panels if rk in p["runs"]]
    if len(ps) != 1:
        raise E.EndCensusError(f"{rk}: {len(ps)} T-355 panels")
    p = ps[0]["tie"]
    idx = [i for i, x in enumerate(p.pieces) if x.key.startswith(rk + "@")]
    col = X.make_piece("COLUMN", float(r["column_depth_mm"]) / 1000, None, f"{rk}@END{end}")
    pcs = list(p.pieces)
    pcs.insert(idx[0] if end == 0 else idx[-1] + 1, col)
    p2 = X.Panel(p.wall_id, p.floor, tuple(pcs), p.openings, p.course, p.held, p.runs)
    old, new = X.ties(p), X.ties(p2)
    add = [t for t in new if t["column_at"] == col.key]
    if len(new) - len(old) != len(add) or len(add) != 1:
        raise E.EndCensusError(f"{rk}: tie junctions moved elsewhere")
    t = add[0]
    if t["state"] != "MEASURED" and ps[0]["course_held"]:
        t = dict(t, held=ps[0]["course_held"])
    return {"state": t["state"], "ties": t["ties"], "held": t.get("held", "") or ps[0]["course_held"]}


def perimeter_t520(r, E1):
    """exact before / after on T-520's own builder: end class F (no column: what V1 reads) vs C (with it)."""
    rk, end, wid = r["run"], int(r["end"]), r["wall_id"]
    w = next(x for x in _csv(ROOT / T520.INPUTS[3]) if x["wall_id"] == wid)
    B, Ev2 = T520.bearings(), T520.ends()
    if Ev2[rk][end] != "C":
        raise E.EndCensusError(f"{wid}: T-520 does not read the column at end {end}")
    Ev1 = copy.deepcopy(Ev2)
    mc = float(r["masonry_cover"])
    Ev1[rk][end] = "O" if mc >= 0.999 else ("F" if mc <= 1e-6 else "O")

    def m(Ex, basis=None):
        res = [PJ.measure(x) for x in T520.build_wall(w, B, Ex, basis)]
        return (sum(x["m3"] for x in res), sum(x["m3_low"] for x in res), sum(x["m3_high"] for x in res))
    if w["floor"] == "2F":
        a = [m(Ex, T520.STOREY_2F - br) for Ex in (Ev1, Ev2) for br in (0.0, 0.10)]
        ex = []
        for k in (0, 2):                     # point (m3) and high (m3_high); low = point on every end found
            d0, d1 = a[2][k] - a[0][k], a[3][k] - a[1][k]
            ex.append(f"{d0:.6f} - {(d0 - d1) / 0.10:.6f} b_r m3")
        expr = ex[0] if ex[0] == ex[1] else f"{ex[0]} .. {ex[1]}"
        return {"state": "HELD", "before_m3": "", "after_m3": "", "delta_m3": "",
                "delta_expr": expr, "held": T520.D39, "v1_class": Ev1[rk][end]}
    (b, bl, bh), (a_, al, ah) = m(Ev1), m(Ev2)
    hold = "" if float(w["t_m"]) == 0.20 else "0.15 m black module not stated (T-506 HELD-0.15-MODULE): figure beside"
    return {"state": "HELD" if hold else "COMPUTED", "before_m3": f"{b:.6f}", "after_m3": f"{a_:.6f}",
            "delta_m3": f"{a_ - b:.6f}", "delta_range_m3": f"{al - bl:.6f} .. {ah - bh:.6f}", "held": hold,
            "v1_class": Ev1[rk][end]}


def _f(v):
    return "" if v is None else f"{v:.4f}"


def end_top(r, walls):
    rk, end = r["run"], int(r["end"])
    w = next(w for (_reg, k, w, _n, _s) in walls if k == rk)
    p = w.pieces[0] if end == 0 else w.pieces[-1]
    return p.top


def build():
    rows = census()
    walls, _u, _t261, _g = T317.build()
    panels, _un, _named, _lost = T355.panels("PRIMARY")
    kap = PJ.kappa(T520.MODULE)
    out = []
    for r in missed(rows):
        t = float(r["t_m"])
        held_end = r["missed_by_v1"] == "HELD"
        rec = {"floor": r["floor"], "wall_id": r["wall_id"], "block_type": r["block_type"], "t_m": r["t_m"],
               "run": r["run"], "end": r["end"], "run_end_type": r["run_end_type"], "class_v2": r["class_v2"],
               "gap_mm": r["gap_mm"], "cover": r["cover"], "column_t119": r["t119_id"], "mark": r["mark"],
               "drawn": r["drawn"], "st_handle": r["st_handle"], "arch_column": r["arch_column"]}
        if held_end:
            rec.update(state="HELD", held=r["held"], d_length_m="", d_blockwork_m2="", d_blocks_nr="",
                       d_mesh_owner_ml="", d_mesh_drawing_ml="", d_ties_nr="", d_perimeter_m3="")
            out.append(rec)
            continue
        if float(r["gap_mm"]) != 0.0:
            raise E.EndCensusError(f"{r['run']}: gap {r['gap_mm']} mm: length effect not evaluated here")
        dm = t317_delta(r, walls)
        dt = t355_delta(r, panels)
        top = end_top(r, walls)
        rec.update(d_length_m="0.0000", d_blockwork_m2="0.0000", d_blocks_nr="0.0",
                   d_mesh_owner_ml=_f(dm["owner"]["ml"]), mesh_owner_sides=dm["owner"]["sides"],
                   mesh_owner_held=dm["owner"]["held"], d_mesh_drawing_ml=_f(dm["drawing"]["ml"]),
                   mesh_drawing_held=dm["drawing"]["held"],
                   mesh_held_why="; ".join(sorted(set(dm["owner"]["held_why"]) | set(dm["drawing"]["held_why"]))),
                   d_ties_nr="" if dt["ties"] is None else str(dt["ties"]), ties_state=dt["state"],
                   ties_held=dt["held"], end_block_top_m="" if top is None else f"{top:.4f}")
        if r["block_type"] == "WHITE":
            rec.update(perimeter_state="HELD", d_perimeter_m3="", perimeter_held=WHITE)
        elif r["wall_id"] in T520.RUNS:
            p = perimeter_t520(r, None)
            rec.update(perimeter_state=p["state"], perimeter_v1_class=p["v1_class"], perimeter_before_m3=p["before_m3"],
                       perimeter_after_m3=p["after_m3"], d_perimeter_m3=p["delta_m3"],
                       d_perimeter_range_m3=p.get("delta_range_m3", ""), d_perimeter_expr=p.get("delta_expr", ""),
                       perimeter_held=p["held"])
        else:
            hi = "" if top is None else f"{kap * t * T520.J * top:.6f}"
            rec.update(perimeter_state="HELD", d_perimeter_m3="", d_perimeter_range_m3=f"0 .. {hi}" if hi else "",
                       perimeter_held=NOT_IN_T520 + ("" if hi else "; block top beside the column not established"))
        rec["state"] = "COMPUTED"
        out.append(rec)
    return rows, out


def summarise(rows, out):
    from collections import Counter
    num = lambda k: round(sum(float(x[k]) for x in out if x.get(k) not in ("", None)), 6)
    s = {"rule": RULE, "joint_m": T520.J, "census_ends": sum(1 for r in rows if r["end"] != ""),
         "runs_not_probed": [r["run"] + ": " + r["held"] for r in rows if r["class_v2"] == "NO_STRAIGHT_RUN"],
         "classes": dict(sorted(Counter(r["class_v2"] for r in rows if r["end"] != "").items())),
         "missed_by_v1": [f"{x['wall_id']} end {x['end']} ({x['run_end_type']}) -> {x['column_t119']} {x['mark']}"
                          for x in out if x["state"] == "COMPUTED"],
         "held_ends": [f"{x['wall_id']} end {x['end']}: {x['held']}" for x in out if x["state"] == "HELD"],
         "f_t520_1_four": [f"{x['wall_id']} end {x['end']}" for x in out if x["wall_id"] in
                           ("1F-W09", "1F-W23", "2F-W01", "2F-W08")],
         "unregistered_runs_with_end_column": [f"{r['run']} end {r['end']} ({r['class_v2']}, t {r['t_m']})"
                                               for r in rows if r["missed_by_v1"] == "YES" and not r["wall_id"]],
         "structural_only_columns": json.load(open(OUT / "ALIGN_T526.json")),
         "structural_only_contacts": [f"{r['wall_id'] or r['run']} end {r['end']}: {r['structural_only']}" for r in rows
                                      if r.get("structural_only")],
         "totals": {"d_length_m": num("d_length_m"), "d_blockwork_m2": num("d_blockwork_m2"),
                    "d_blocks_nr": num("d_blocks_nr"), "d_mesh_owner_ml": num("d_mesh_owner_ml"),
                    "d_mesh_drawing_ml": num("d_mesh_drawing_ml"), "d_ties_nr_measured": num("d_ties_nr"),
                    "d_perimeter_m3_computed_020": round(sum(float(x["d_perimeter_m3"]) for x in out
                                                             if x.get("perimeter_state") == "COMPUTED"), 6)},
         "sha256_census": __import__("hashlib").sha256(CENSUS.read_bytes()).hexdigest()}
    return s


def texts():
    rows, out = build()
    keys = []
    for r in out:
        keys += [k for k in r if k not in keys]
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=keys, lineterminator="\n", restval="")
    w.writeheader()
    w.writerows(out)
    return {"MISSED_ENDS_T526.csv": b.getvalue(),
            "SUMMARY_T526.json": json.dumps(summarise(rows, out), indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    T = texts()
    if "--check" in argv:
        bad = [k for k, v in T.items() if (OUT / k).read_text(encoding="utf-8") != v]
        print("reproduce:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    for k, v in T.items():
        (OUT / k).write_text(v, encoding="utf-8")
    print(T["SUMMARY_T526.json"][:5000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
