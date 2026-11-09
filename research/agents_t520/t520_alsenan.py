"""T-520 training-villa builder: B9-04 perimeter joint mortar (column faces, beam-drop sides, soffits) of the 24 black
walls / pieces of T-367 / T-506, junction by junction, on R-T520-1 (perimeter_joint_v1.py).

Inputs (merged, read only; numbers and ids, no drawing coordinate):
  research/agents_t274/T274_RUN_PIECES.csv     every census run cut at columns / beam bands / slab faces (T-274)
  research/agents_t274/T274_SIBLING_CHECK.csv  the register basis of every wall (height basis per piece)
  research/agents_t261/T261_SPLIT.csv          drawn-extent pieces of the T-261 walls (1F-W13 / W17 / W18 / W24, 2F-W05)
  research/agents_t516/out/JAMB_EVIDENCE_T516.csv  masonry available beside each lintel jamb (bearing ranges)
  research/agents_t506/out/MORTAR_RECONCILIATION_T506.csv  the 24 walls, contract m2, bucket, T-367 m3, lintels
  research/agents_t520/out/END_CONDITIONS_T520.csv  what each run end meets (t520_extract.py, the drawing)
Writes research/agents_t520/out/: JUNCTIONS_T520.csv, PERIMETER_BY_WALL_T520.csv, SUMMARY_T520.json.
    python3 -I research/agents_t520/t520_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t274"))
import perimeter_joint_v1 as PJ  # noqa: E402
import piece_close as PC  # noqa: E402

OUT = HERE / "out"
J = 0.010                                         # owner session 2026-10-29: provisional 10 mm joint, mortared blocks
MODULE = (0.39, 0.19, 0.40, 0.20)                 # Q-75 (owner 2026-10-23 / 2026-11-02): 39 x 19 face, 40 x 20 module
BASIS = {"GF": 4.50, "1F": 4.20}                  # structural storey (T-488 s.1: GF 4.50, 1F 4.20 DRAWING-CONFIRMED)
STOREY_2F = 4.25                                  # 2F: 4.25 - b_r (T-488, D-39: b_r not printed -> HELD)
DOOR_HEAD = 2.20                                  # Q-55 C 2.20 m (ASSUMED - OWNER-APPROVED), the area ledger's basis
CEMENT_BAGS, SAND_M3 = 8.0, 1.1                   # Q-78 A (owner 2026-11-02): 1:4 with the Q-45 figures, per m3
MIX_SOURCE = "Q-78 A owner 2026-11-02: block-joint mortar 1:4, 8 bags 50 kg + 1.1 m3 loose sand per m3"
END_CLASS = {"COLUMN": "C", "COLUMN_PIECE_IN_RUN": "C", "MASONRY": "O", "MIXED": "O", "NONE": "F"}
# T-215 junction closes on the census (merged ledger, T-274 basis column): metres added at the run end that closes
T215 = {"GF-W21": (1, -0.0311), "GF-W33": (0, +0.0311)}
# openings in RUN stations (band stations + the band start offset along the run: GF-W29 0.85, 1F-W12 1.0885, 1F-W13
# 0.075, 1F-W23 0.8798, every other band 0; doorways from the T-516 own-band reading); name -> (wall, x0, x1)
OPENINGS = {
    "D-GF-13": ("GF-W28", 1.5034, 2.5034), "D-GF-10": ("GF-W29", 0.050, 0.850), "D-1F-03": ("1F-W12", 0.0885, 1.0885),
    "D-1F-08": ("1F-W13", 2.9178, 3.8178), "D-1F-09": ("1F-W13", 4.6623, 5.5623), "D-1F-10": ("1F-W17", 1.1907, 1.9907),
    "D-1F-07": ("1F-W19", 0.1093, 0.9093), "D-1F-04": ("1F-W23", 0.0798, 0.8798), "D-1F-02": ("1F-W23", 5.9748, 6.9748),
    "D-2F-02": ("2F-W05", 0.1016, 1.0016), "D-2F-03": ("2F-W08", 0.2493, 1.0493),
}
HELD_LINTEL = {"D-1F-09": "lintel HELD (T-453: inside the dome piece of unknown top)",
               "D-2F-02": "lintel HELD (T-453 D-2F-02: width / face 0 .. 0.34 m2)"}
# T-261 walls: drawn-extent pieces in run order (T-274 stations), name -> (length, top or None, held reason)
DOME = "dome opening piece: top of wall not drawn (T-227 / T-261, designer)"
T261_ORDER = {
    "1F-W13": [("slab 1F-063", 1.455, 4.04), ("B1 BM-1F-010", 0.200, 3.80), ("slab 1F-065", 1.59782, 4.04),
               ("B25 BM-1F-027", 0.550, 3.45), ("slab corner 1F-076/c0", 0.4735, 4.04),
               ("east ring west crossing", 0.29026, None), ("east dome opening 1F-077", 2.89466, None),
               ("east ring east crossing", 0.29025, None), ("slab corner 1F-076/c1", 0.42351, 4.04),
               ("CB12 BM-1F-017", 0.050, 3.45)],
    "1F-W17": [("east dome opening 1F-077", 0.46158, None), ("east ring sliver", 0.00294, None),
               ("B6 band", 0.250, 3.70), ("slab 1F-057", 1.01048, 4.04), ("B4 BM-1F-014", 0.200, 3.70),
               ("slab 1F-025", 0.175, 4.04)],
    "1F-W18": [("slab corner 1F-076/c0", 0.46452, 4.04), ("B6 band", 0.250, 3.70), ("slab 1F-057", 0.99533, 4.04),
               ("B19 sliver", 0.01515, 3.45), ("COLUMN", 1.000, "COL"), ("B5 band", 3.475, 3.70),
               ("COLUMN", 0.050, "COL")],
    "1F-W24": [("slab 1F-094", 1.14234, 4.04), ("B6 band", 0.250, 3.70), ("west dome opening 1F-073", 1.05766, None)],
    "2F-W05": [("BM-2F-017 (depth not printed, D-04)", 1.200, None), ("junction in the top band", 0.050, None),
               ("COLUMN", 0.700, "COL"), ("B1 BM-2F-009", 1.000, 0.40), ("COLUMN", 0.400, "COL")],
}
CANDIDATE = "ARCH_TAKEOFF_V3.0.58 (T-507 merged; MAS.BLOCK walls as V3.0.55 T-488)"
D39 = "2F storey 4.25 - b_r: roof-plate structural level not printed (D-39, T-488)"
D27 = "GF-W22 CONFLICT [12.9311, 12.9439] m2 on its parent (D-27, T-488): not on a part line"


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


INPUTS = ["research/agents_t274/T274_RUN_PIECES.csv", "research/agents_t261/T261_SPLIT.csv",
          "research/agents_t516/out/JAMB_EVIDENCE_T516.csv", "research/agents_t506/out/MORTAR_RECONCILIATION_T506.csv",
          "research/agents_t520/out/END_CONDITIONS_T520.csv", "research/agents_t355/SHARMAT_T355.csv"]


def bearings():
    """T-516: (low, high) bearing per side, START = lower run station; DEFICIT / HELD ends -> None (HELD)."""
    out = {}
    for r in _csv(ROOT / INPUTS[2]):
        a = float(r["available_m"])
        ok = a >= 0.40 and r["stopper"] != "SEARCH_LIMIT"
        out[(r["opening_id"], r["side"])] = (0.40, a) if ok else None
    return out


def ends():
    out = defaultdict(dict)
    for r in _csv(ROOT / INPUTS[4]):
        out[r["run"]][int(r["end"])] = END_CLASS[r["class"]]
    return out


def t274_pieces(run_key, floor, top_of):
    """raw T-274 pieces of one run -> perimeter pieces: columns kept, slivers joined between columns (R-T274-1)."""
    rows = [x for x in _csv(ROOT / INPUTS[0]) if x["run_key"] == run_key]
    out, group = [], []

    def flush():
        ps = [{"kind": x["kind"], "length_m": float(x["len_m"]), "x": x} for x in group]
        for p in PC.join_slivers(ps):
            top, held, name = top_of(p["x"], floor)
            out.append(PJ.Piece("BLOCK", p["length_m"], top, name, held))
        group.clear()
    for x in rows:
        if x["kind"] == "COLUMN":
            flush()
            out.append(PJ.Piece("COLUMN", float(x["len_m"]), None, "column"))
        else:
            group.append(x)
    flush()
    return out


def top_of(x, floor, basis=None):
    B = BASIS.get(floor) if basis is None else basis
    if x["kind"] == "BEAM" and x["depth_m"]:
        return round(B - float(x["depth_m"]), 6), None, f"{x['mark']} {x['member_id']}"
    if x["kind"] == "FACE" and x["face_cls"] == "SLAB" and x["slab_t_m"]:
        return round(B - float(x["slab_t_m"]), 6), None, f"slab {x['face_id']}"
    return None, f"{x['kind']} {x['face_cls']}: nothing with a printed soffit drawn over it (T-274 HELD piece)", \
        f"{x['kind']} {x['face_cls']}".strip()


RUNS = {
    "GF-W01": "GF|WB-FL0001-FL0002#2", "GF-W19": "GF|WB-FL0059-FL0060", "GF-W21": "GF|WB-FL0063-FL0064#1",
    "GF-W22": "GF|WB-FL0070-FL0072", "GF-W28": "GF|WB-FL0030-FL0031", "GF-W29": "GF|WB-FL0038-FL0039",
    "GF-W33": "GF|WB-FL0046-FL0047", "1F-W02": "1F|WB-FL0059-FL0061", "1F-W03": "1F|WB-FL0068-FL0070",
    "1F-W09": "1F|WB-FL0024-FL0025", "1F-W12": "1F|WB-FL0011-FL0012", "1F-W13": "1F|WB-FL0013-FL0014",
    "1F-W17": "1F|WB-FL0043-FL0044", "1F-W18": "1F|WB-FL0046-FL0047", "1F-W19": "1F|WB-FL0050-FL0051",
    "1F-W20": ("1F|WB-FL0054-FL0055#1", "1F|WB-FL0054-FL0055#2"), "1F-W21": "1F|WB-FL0059-FL0060",
    "1F-W22": "1F|WB-FL0063-FL0065", "1F-W23": "1F|WB-FL0074-FL0075", "1F-W24": "1F|WB-FL0078-FL0079",
    "2F-W01": "2F|WB-FL0006-FL0007", "2F-W05": "2F|WB-FL0024-FL0026", "2F-W06": "2F|WB-FL0031-FL0032",
    "2F-W08": "2F|WB-FL0024-FL0025",
}
# the GF-W01 2.6 mm strip between the architectural column face and the first drawn ST edge (T-274 HELD piece): the
# column is concrete over the full storey on either reading, so the face joint exists; only its station moves 2.6 mm.
# The strip's own area stays HELD in the area ledger; here it is joined to the block piece it touches (B1).
COLUMN_FACE_STRIP = {"GF-W01": "NONE"}


def wall_pieces(wid, floor, basis=None):
    if wid in T261_ORDER:
        ps = []
        for name, L, top in T261_ORDER[wid]:
            if top == "COL":
                ps.append(PJ.Piece("COLUMN", L, None, "column"))
            elif top is None:
                ps.append(PJ.Piece("BLOCK", L, None, name, DOME if "dome" in name or "ring" in name else
                                   "member depth not printed (D-04)"))
            else:
                t = top if floor != "2F" else round(basis - top, 6)
                ps.append(PJ.Piece("BLOCK", L, t, name))
        return ps
    rks = RUNS[wid] if isinstance(RUNS[wid], tuple) else (RUNS[wid],)
    out = []
    for rk in rks:
        ps = t274_pieces(rk, floor, lambda x, fl: top_of(x, fl, basis))
        if wid in COLUMN_FACE_STRIP:
            ps = _join_face_strip(ps)
        out.append(ps)
    return out if len(out) > 1 else out[0]


def _join_face_strip(ps):
    out = []
    for i, p in enumerate(ps):
        if p.kind == "BLOCK" and p.top is None and p.length < 0.005 and i > 0 and ps[i - 1].kind == "COLUMN" \
                and i + 1 < len(ps) and ps[i + 1].kind == "BLOCK" and ps[i + 1].top is not None:
            ps[i + 1].length += p.length
            ps[i + 1].name += f" (+{p.length:.4f} m column-face strip, T-274 HELD area)"
            continue
        out.append(p)
    return out


def build_wall(w, B, E, basis=None):
    wid, fl, t = w["wall_id"], w["floor"], float(w["t_m"])
    rks = RUNS[wid] if isinstance(RUNS[wid], tuple) else (RUNS[wid],)
    pieces = wall_pieces(wid, fl, basis)
    groups = pieces if isinstance(pieces[0], list) else [pieces]
    walls = []
    for k, (rk, ps) in enumerate(zip(rks, groups)):
        if wid in T215:
            end, d = T215[wid]
            blk = [p for p in ps if p.kind == "BLOCK"]
            (blk[0] if end == 0 else blk[-1]).length += d
        ops = []
        for name, (ow, x0, x1) in OPENINGS.items():
            if ow != wid:
                continue
            bs, be = B.get((name, "START")), B.get((name, "END"))
            held = HELD_LINTEL.get(name)
            ops.append(PJ.Opening(name, x0, x1, DOOR_HEAD, 0.0, None if held else 0.20, bs, be, held))
        ws = E[rk].get(0, "U")
        we = E[rk].get(1, "U")
        walls.append(PJ.Wall(f"{wid}" + (f"#{k + 1}" if len(rks) > 1 else ""), t, J, MODULE, ps, ws, we, ops,
                             w["area_status"]))
    return walls


def area_of(wall):
    a = sum(p.length * p.top for p in wall.pieces if p.kind == "BLOCK" and p.top is not None)
    return a - sum((o.x1 - o.x0) * (o.head - o.sill) for o in wall.openings
                   if not o.held)


def col_faces(wall):
    """concrete column faces met by block (each side of an in-run column + concrete run ends), and their heights."""
    n, H = 0, []
    ps = wall.pieces
    for i, p in enumerate(ps):
        if p.kind != "COLUMN":
            continue
        for j in (i - 1, i + 1):
            if 0 <= j < len(ps) and ps[j].kind == "BLOCK":
                n += 1
                H.append(ps[j].top)
    for end, j in ((wall.end_start, 0), (wall.end_end, -1)):
        if end == "C" and ps[j].kind == "BLOCK":
            n += 1
            H.append(ps[j].top)
    return n, H


def station_check(tol=0.002):
    """every T-274 piece boundary of a T-261 wall has a T-261 boundary within tol (the heights are tied to stations)."""
    for wid, order in T261_ORDER.items():
        x, mine = 0.0, [0.0]
        for _n, L, _t in order:
            x += L
            mine.append(x)
        rows = [r for r in _csv(ROOT / INPUTS[0]) if r["run_key"] == RUNS[wid]]
        theirs = sorted({float(r["from_m"]) for r in rows} | {float(r["to_m"]) for r in rows})
        theirs = [t for i, t in enumerate(theirs) if i == 0 or t - theirs[i - 1] >= 0.001]
        bad = [t for t in theirs if min(abs(t - m) for m in mine) > tol]
        if bad:
            raise PJ.PerimeterError(f"{wid}: T-274 stations {bad} not matched by the T-261 pieces")
        if abs(mine[-1] - theirs[-1]) > tol:
            raise PJ.PerimeterError(f"{wid}: T-261 sum {mine[-1]:.4f} vs run {theirs[-1]:.4f}")


def build():
    station_check()
    B, E = bearings(), ends()
    W = _csv(ROOT / INPUTS[3])
    rows, junc = [], []
    for w in sorted(W, key=lambda r: (["GF", "1F", "2F"].index(r["floor"]), r["t_m"], r["wall_id"])):
        wid, fl, t = w["wall_id"], w["floor"], float(w["t_m"])
        if fl == "2F":
            # D-39: run at two what-if b_r to read the linear expression; nothing released, wall HELD
            m = [sum(PJ.measure(x)["m3"] for x in build_wall(w, B, E, STOREY_2F - br)) for br in (0.0, 0.10)]
            r0 = [PJ.measure(x) for x in build_wall(w, B, E, STOREY_2F)]
            soffit = sum(x["soffit_m"] for x in r0)
            expr = f"{m[0]:.6f} - {(m[0] - m[1]) / 0.10:.6f} b_r m3 (figure, not a quantity)"
            rows.append(_row(w, None, "HELD", D39, soffit_m=soffit, expr=expr, junctions=r0))
            continue
        ws = build_wall(w, B, E)
        res = [PJ.measure(x) for x in ws]
        area = sum(area_of(x) for x in ws)
        established = float(w["contract_m2"])
        if wid == "GF-W22":
            # D-27: the census reads 12.9311 or 12.9439 m2 (CB2 drawn 0.25 vs schedule 0.20) on one slab soffit 4.34
            res2 = []
            for reading in (12.9311, 12.9439):
                x = build_wall(w, B, E)[0]
                blk = [p for p in x.pieces if p.kind == "BLOCK"]
                if len(blk) != 1 or blk[0].top != 4.34:
                    raise PJ.PerimeterError("GF-W22: expected one slab piece under 4.34")
                blk[0].length = reading / 4.34
                res2.append([PJ.measure(x)])
            rows.append(_row(w, res2[0], "HELD", D27, extra_hi=res2[1][0]["m3_high"], area=12.9311))
            _junc(junc, w, res2[0])
            continue
        if abs(area - established) > 0.0015:
            raise PJ.PerimeterError(f"{wid}: pieces give {area:.4f} m2, ledger {established:.4f} m2")
        hold = None if t == 0.20 else ("0.15 m black module not stated by the owner (Q-75 answer 2026-11-02 confirms "
                                       "40 x 20 for 0.20 m only; T-506 HELD-0.15-MODULE): figure beside")
        rows.append(_row(w, res, "HELD" if hold else None, hold, area=area))
        _junc(junc, w, res)
    return rows, junc


def _junc(junc, w, res):
    for r in res:
        for x in r["rows"]:
            if x["class"] == "NOT_APPLICABLE":
                continue
            junc.append({"wall_id": r["wall_id"], "floor": w["floor"], "t_m": w["t_m"],
                         "z0_m": f"{x['z0']:.4f}", "z1_m": f"{x['z1']:.4f}", "x0_m": f"{x['x0']:.4f}",
                         "x1_m": f"{x['x1']:.4f}", "ends": x["ends"], "end_ids": x["end_ids"], "class": x["class"],
                         "increment_low_m": f"{x['low_m']:.4f}", "increment_high_m": f"{x['high_m']:.4f}"})


def _row(w, res, hold_status, hold, soffit_m=None, expr="", junctions=None, extra_hi=None, area=None):
    rs = res or junctions or []
    S = lambda k: sum(x[k] for x in rs) if rs else None
    m3 = S("m3")
    hi = S("m3_high")
    if extra_hi is not None:
        hi = max(hi, extra_hi)
    status = hold_status or ("COMPUTED" if all(x["status"] == "COMPUTED" for x in rs) else
                             "COMPUTED_WITH_RANGE" if all(x["status"] != "COMPUTED_WITH_HELD_PARTS" for x in rs) else
                             "COMPUTED_WITH_HELD_PARTS")
    held_parts = "; ".join(h for x in rs for h in x.get("held_soffit", []))
    nheld = sum(x.get("held_bands", 0) for x in rs)
    n_c, Hs = 0, []
    t367 = float(w["t367_m3"]) if w["t367_m3"] else None
    out = {
        "floor": w["floor"], "t_m": w["t_m"], "wall_id": w["wall_id"], "kind": w["kind"], "line_id": w["line_id"],
        "area_status": w["area_status"], "t506_bucket": w["bucket"], "established_m2": w["contract_m2"],
        "pieces_m2": "" if area is None else f"{area:.4f}",
        "panel_t367_m3": w["t367_m3"],
        "soffit_m": f"{(soffit_m if soffit_m is not None else S('soffit_m')):.4f}",
        "soffit_m3": "" if hold_status == "HELD" and res is None else f"{S('soffit_m3'):.6f}",
        "vertical_exact_m": "" if res is None else f"{S('vertical_exact_m'):.4f}",
        "top_corners": "" if res is None else str(S("top_corners")),
        "vertical_exact_m3": "" if res is None else f"{S('vertical_exact_m3'):.6f}",
        "perimeter_m3": "" if (hold_status == "HELD" or m3 is None) else f"{m3:.6f}",
        "perimeter_figure_m3": "" if m3 is None else f"{m3:.6f}",
        "perimeter_low_m3": "" if S("m3_low") is None else f"{S('m3_low'):.6f}",
        "perimeter_high_m3": "" if hi is None else f"{hi:.6f}",
        "range_block_end_m": "" if res is None else f"{S('range_block_end_m'):.4f}",
        "held_bands": str(nheld), "held_pieces": held_parts,
        "pct_of_panel": "" if (m3 is None or not t367) else f"{100 * m3 / t367:.2f}",
        "status": status, "held": hold or "", "expression": expr,
        "mortar_status": "" if hold_status == "HELD" else
        f"ASSUMED — OWNER-APPROVED (weakest of area {w['area_status']} and the Q-75 module / 10 mm joint)",
    }
    return out


def checker_bounds(rows, junc):
    """F-T367-1 bound per wall: (soffit + every column face height) x b x j, whole joints, no module credit."""
    B, E = bearings(), ends()
    out = {}
    for w in _csv(ROOT / INPUTS[3]):
        if w["floor"] == "2F":
            continue
        tot = 0.0
        for x in build_wall(w, B, E):
            n, H = col_faces(x)
            Ls, _ = PJ.soffit(x)
            tot += (Ls + sum(h for h in H if h is not None)) * x.b * x.j
        out[w["wall_id"]] = tot
    return out


def sharmat_crosscheck(junc_walls):
    """T-355's column-junction census (same T-274 column pieces) against the column faces read here."""
    t355 = defaultdict(int)
    for r in _csv(ROOT / INPUTS[5]):
        if r["block_type"] == "BLACK":
            t355[r["wall_id"]] += 1
    return dict(t355)


def summarise(rows, junc):
    num = lambda r, k: float(r[k]) if r[k] not in ("", None) else 0.0
    sel = lambda f: [r for r in rows if f(r)]
    c20 = sel(lambda r: r["t_m"] == "0.2" and r["floor"] != "2F")
    c15 = sel(lambda r: r["t_m"] == "0.15" and r["floor"] != "2F" and r["wall_id"] != "GF-W22")
    s = {
        "rule": PJ.RULE, "candidate": CANDIDATE, "kappa": PJ.kappa(MODULE), "joint_m": J,
        "factor_m3_per_m": {"0.20": PJ.kappa(MODULE) * 0.20 * J, "0.15": PJ.kappa(MODULE) * 0.15 * J},
        "computed_020": {
            "walls": [r["wall_id"] for r in c20],
            "panel_m3": round(sum(num(r, "panel_t367_m3") for r in c20), 6),
            "perimeter_m3": round(sum(num(r, "perimeter_m3") for r in c20), 6),
            "perimeter_high_m3": round(sum(num(r, "perimeter_high_m3") for r in c20), 6),
            "soffit_m3": round(sum(num(r, "soffit_m3") for r in c20), 6),
            "vertical_m3": round(sum(num(r, "vertical_exact_m3") for r in c20), 6),
        },
        "beside_015_held_module": {
            "walls": len(c15), "panel_m3": round(sum(num(r, "panel_t367_m3") for r in c15), 6),
            "perimeter_figure_m3": round(sum(num(r, "perimeter_figure_m3") for r in c15), 6),
            "perimeter_high_m3": round(sum(num(r, "perimeter_high_m3") for r in c15), 6)},
        "held_2f_d39": [r["wall_id"] + ": " + r["expression"] for r in rows if r["floor"] == "2F"],
        "held_gf_w22_d27": [r["perimeter_figure_m3"] + " .. " + r["perimeter_high_m3"] for r in rows
                            if r["wall_id"] == "GF-W22"],
    }
    p = s["computed_020"]
    p["t498_stage_panel_m3"] = 1.269444
    p["t498_stage_plus_perimeter_m3"] = round(1.269444 + p["perimeter_m3"], 6)
    p["pct_on_t498_stage"] = round(100 * p["perimeter_m3"] / 1.269444, 3)
    m = PJ.materials(p["perimeter_m3"], CEMENT_BAGS, SAND_M3, MIX_SOURCE)
    s["materials_perimeter_020"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}
    s["materials_perimeter_020"]["producer_key"] = "B9-04 PERIMETER JOINT MORTAR (T-520) cement / sand: own key, " \
        "never inside the T-453 / T-498 panel mortar key"
    gf1f = [r for r in rows if r["floor"] != "2F"]
    s["gf_1f_20_walls"] = {"panel_t367_m3": round(sum(num(r, "panel_t367_m3") for r in gf1f), 6),
                           "perimeter_figure_m3": round(sum(num(r, "perimeter_figure_m3") for r in gf1f), 6),
                           "perimeter_low_m3": round(sum(num(r, "perimeter_low_m3") for r in gf1f), 6),
                           "perimeter_high_m3": round(sum(num(r, "perimeter_high_m3") for r in gf1f), 6)}
    s["t367_2f_4_walls_panel_m3"] = round(sum(num(r, "panel_t367_m3") for r in rows if r["floor"] == "2F"), 6)
    s["t367_total_m3"] = 3.870113
    cb = checker_bounds(rows, junc)
    s["checker_bound_by_wall_m3"] = {k: round(v, 6) for k, v in sorted(cb.items())}
    s["t355_black_junctions"] = sharmat_crosscheck(None)
    s["sha256_inputs"] = {p: _sha(ROOT / p) for p in INPUTS}
    return s


def texts():
    rows, junc = build()
    s = summarise(rows, junc)

    def to_csv(rs):
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=list(rs[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rs)
        return b.getvalue()
    return {"PERIMETER_BY_WALL_T520.csv": to_csv(rows), "JUNCTIONS_T520.csv": to_csv(junc),
            "SUMMARY_T520.json": json.dumps(s, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    T = texts()
    if "--check" in argv:
        bad = [k for k, v in T.items() if (OUT / k).read_text(encoding="utf-8") != v]
        print("reproduce:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for k, v in T.items():
        (OUT / k).write_text(v, encoding="utf-8")
    print(json.dumps({k: v for k, v in json.loads(T["SUMMARY_T520.json"]).items() if k != "sha256_inputs"},
                     indent=1, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
