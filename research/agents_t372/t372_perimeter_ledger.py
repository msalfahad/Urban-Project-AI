"""T-372 (research part): the B9-04 PERIMETER JOINT MORTAR component bound line by line to the black-block mortar lines
of ARCH_TAKEOFF_V3.0.63 as restated by T-670 (R-T372-1, PROPOSED; research only, nothing wired, nothing released).

Physical element: the mortar between the last block and concrete (vertical at an RC column face, a beam-drop side or a
lintel end; horizontal over the last course under a beam / slab soffit), measured as the INCREMENT over the panel
module figure (R-T520-1, merged T-520; 0.15 m rows re-run on the Q-80 register module by merged T-615). It is a
separate component of the same physical mortar line: it is bound to the MAS.MORTAR.BLACK line of its wall's host,
carried BESIDE the panel figure and never summed into it (Lead acceptance (b) of T-372).

Inputs (all merged, read-only; the drawings are not read here, the per-junction figures come from T-520's own DXF
read): research/agents_t670/out/T670_MATERIALS.json (V3.0.63 mortar lines, rulebook 1.1.0), research/agents_t520/out
(per wall + per junction), research/agents_t615/out/WALLS_015_T615.csv (0.15 m perimeter on the 1.1.0 module),
rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json (UPC-BLACK-MORTAR-001: cement / sand per m3; no value typed here).

R-T372-1 (every villa):
 (1) a wall's perimeter component is bound to the mortar line whose host line id is the wall's host (one line, once);
 (2) the host's walls must add up to the host's net m2 (to 1e-4 m2); a wall whose area is NOT in its host's figure
     (its own area cause, e.g. a conflict on the parent) is carried BESIDE that line as HELD by name, never summed;
 (3) a HELD host keeps its perimeter blank with the host's committed cause, the T-520 expression in the missing datum
     beside (never 0);
 (4) per line: exact part (columns c = 2, soffits, minus top corners), RANGE part (block-to-block ends: butt or bonded,
     no junction detail printed), held bands by name; low .. high are carried as a range, never a point picked;
 (5) the lintel bearing bed (the joint between the top of the bearing course and the lintel underside, not credited by
     the panel module because the lintel face is deducted from the panel base) is a separate HELD component per
     REQUIRED lintel, bounded 0 .. kappa b j x (face length - opening width) (both bearings on block); never summed;
 (6) cement / sand of the perimeter component by UPC-BLACK-MORTAR-001 as its OWN producer key, never inside the
     panel key; rounding to bags only at the purchasing group.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T670 = ROOT / "research/agents_t670/out/T670_MATERIALS.json"
T520_WALLS = ROOT / "research/agents_t520/out/PERIMETER_BY_WALL_T520.csv"
T520_JUNCTIONS = ROOT / "research/agents_t520/out/JUNCTIONS_T520.csv"
T615_WALLS = ROOT / "research/agents_t615/out/WALLS_015_T615.csv"
T527_JAMBS = ROOT / "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv"
BEARING_M = 0.40          # the candidate's REQUIRED face basis (w + 0.80) x D (T-670 lintel = face check), per end
RB = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
INDEX = ROOT / "research/agents_t665/out/LINE_INDEX_V3_0_63.json"
TRIAL_R4 = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
OUT = ROOT / "research/agents_t372/out"

MORTAR = "MAS.MORTAR.BLACK"
PRODUCER_KEY = "B9-04 PERIMETER JOINT MORTAR (R-T520-1 / R-T372-1)"
AREA_TOL = 1e-4
FIG_TOL = 1.5e-6          # T-520 / T-615 print 6 decimals
STATUS_015 = "ASSUMED - OWNER-APPROVED"   # T-615: Q-80 module + owner 2026-10-29 10 mm joint


class T372Error(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _f(s):
    return None if s in (None, "") else float(s)


# ------------------------------------------------------------------------------------------------ rule (generic)
def kappa(face, module):
    return (face[0] * face[1]) / (module[0] * module[1])


def factor(t, face, module, joint_m):
    """m3 per metre of joint increment: kappa b j (R-T520-1)."""
    return kappa(face, module) * t * joint_m


def wall_exact(soffit_m, vertical_exact_m, top_corners, f, joint_m):
    """exact part of one wall: f (soffit + vertical c=2 - corners x j)."""
    return f * (soffit_m + vertical_exact_m - top_corners * joint_m)


def bind(lines, walls):
    """lines: [{line_id, host_line_id, host, host_class, host_net_m2, after, t}], walls: [{wall_id, host_line_id,
    area_m2, in_host (bool), low, figure, high, status, held_why, expression, held_bands, held_pieces}]
    -> per-line rows. Raises on a wall bound twice, a wall without a mortar line, an area mismatch."""
    by_host = {}
    for ln in lines:
        if ln["host_line_id"] in by_host:
            raise T372Error(f"host {ln['host_line_id']} has two {MORTAR} lines")
        by_host[ln["host_line_id"]] = ln
    seen = set()
    rows = {ln["line_id"]: {"line_id": ln["line_id"], "host_line_id": ln["host_line_id"], "host": ln["host"],
                            "host_class": ln["host_class"], "host_net_m2": ln["host_net_m2"],
                            "panel_after": ln["after"], "walls": [], "beside_held_walls": [],
                            "low": 0.0, "high": 0.0, "figure": 0.0, "range_part": 0.0}
            for ln in lines}
    for w in walls:
        if w["wall_id"] in seen:
            raise T372Error(f"wall {w['wall_id']} bound twice")
        seen.add(w["wall_id"])
        ln = by_host.get(w["host_line_id"])
        if ln is None:
            raise T372Error(f"wall {w['wall_id']}: host {w['host_line_id']} has no {MORTAR} line (white host?)")
        r = rows[ln["line_id"]]
        if ln["host_class"] != "RELEASED" or not w["in_host"] or w["status"] == "HELD":
            r["beside_held_walls"].append(w)
            continue
        for k in ("low", "figure", "high"):
            if w[k] is None:
                raise T372Error(f"wall {w['wall_id']} carried on a released host with no {k} figure (never 0)")
        r["walls"].append(w)
    for r in rows.values():
        if r["host_class"] == "RELEASED":
            area = sum(w["area_m2"] for w in r["walls"])
            if r["walls"] and abs(area - r["host_net_m2"]) > AREA_TOL:
                raise T372Error(f"{r['line_id']}: walls {area:.4f} m2 != host {r['host_net_m2']} m2")
            r["low"] = _r(sum(w["low"] for w in r["walls"]))
            r["figure"] = _r(sum(w["figure"] for w in r["walls"]))
            r["high"] = _r(sum(w["high"] for w in r["walls"]))
            r["range_part"] = _r(r["high"] - r["low"])
            r["state"] = ("VALUE" if r["low"] == r["high"] else "RANGE") if r["walls"] else "HELD"
        else:
            r["low"] = r["figure"] = r["high"] = r["range_part"] = None
            r["state"] = "HELD"
    return [rows[ln["line_id"]] for ln in lines]


def bearing_end(available_m, stopper, bearing_m=BEARING_M):
    """R-T372-1 (5), one lintel end: metres of the bearing course top (block) under the lintel.
    available >= bearing -> EXACT bearing (the lintel lies on block over its whole bearing);
    available < bearing (FLAGGED_DEFICIT, T-516 / T-527) -> RANGE: at a COLUMN stopper [0, available] (the rest of
    the bearing is on concrete, T-524 owns that volume), at a masonry end / opening [0, bearing] (the bearing may
    continue on an orthogonal block wall; position not buildable as drawn). Never 0 by default, never a picked point."""
    if available_m is None:
        return {"state": "HELD", "low": None, "high": None, "why": "masonry beyond the jamb not read"}
    if available_m < 0:
        raise T372Error("negative available masonry")
    if available_m + 1e-9 >= bearing_m:
        return {"state": "EXACT", "low": bearing_m, "high": bearing_m, "why": "available >= bearing"}
    hi = available_m if stopper == "COLUMN" else bearing_m
    return {"state": "RANGE", "low": 0.0, "high": hi, "why": f"FLAGGED_DEFICIT end ({stopper}, {available_m:.3f} m)"}


def lintel_bearing_bed(oid, ends, f):
    """one REQUIRED lintel: ends = [(side, available_m, stopper)] -> metres and m3 (f = kappa b j)."""
    if len(ends) != 2 or {e[0] for e in ends} != {"START", "END"}:
        return {"opening_id": oid, "state": "HELD", "why": "two jamb ends not both read", "low": None, "high": None}
    per = [dict(side=e[0], **bearing_end(e[1], e[2])) for e in ends]
    if any(p["state"] == "HELD" for p in per):
        return {"opening_id": oid, "state": "HELD", "why": "an end not read", "ends": per, "low": None, "high": None}
    lo, hi = sum(p["low"] for p in per), sum(p["high"] for p in per)
    return {"opening_id": oid, "state": "EXACT" if lo == hi else "RANGE", "ends": per, "bearing_low_m": _r(lo, 4),
            "bearing_high_m": _r(hi, 4), "low": _r(f * lo), "high": _r(f * hi)}


def materials(m3_low, m3_high, cement_per_m3, sand_per_m3):
    return {"producer_key": PRODUCER_KEY,
            "cement_bags_50kg": [_r(m3_low * cement_per_m3, 4), _r(m3_high * cement_per_m3, 4)],
            "sand_m3_loose": [_r(m3_low * sand_per_m3), _r(m3_high * sand_per_m3)],
            "rounding": "bags only at the purchasing group; waste HELD (not sourced)"}


# ------------------------------------------------------------------------------------------------ project
def _rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8", newline="")))


def _rulebook():
    b = json.loads(RB.read_text(encoding="utf-8"))
    rec = {r["rule_id"]: r for r in b["records"]}
    m = rec["UPC-BLACK-MORTAR-001"]["params"]
    return {"version": b["version"], "cement_bags_per_m3": m["cement_bags_per_m3"]["value"],
            "sand_m3_per_m3": m["loose_sand_m3_per_m3"]["value"]}


def project_inputs():
    t670 = json.loads(T670.read_text(encoding="utf-8"))
    if t670["candidate"] != "ARCH_TAKEOFF_V3.0.63" or t670["rulebook_after"] != "1.1.0":
        raise T372Error("T-670 statement is not V3.0.63 on rulebook 1.1.0")
    joint = t670["joint"]
    lines = []
    for r in t670["rows"]:
        if r["code"] != MORTAR:
            continue
        lines.append({"line_id": r["material_line_id"], "host_line_id": r["host_line_id"], "host": r["host"],
                      "host_class": r["host_class"], "host_net_m2": r["host_net_m2"], "after": r["after"],
                      "cause": r["cause"], "lintels": r["lintels"], "material_base_range_m2": r["material_base_range_m2"]})
    t520 = {r["wall_id"]: r for r in _rows(T520_WALLS)}
    t615 = {r["wall_id"]: r for r in _rows(T615_WALLS)}
    return t670, joint, lines, t520, t615


def wall_records(t520, t615, lines):
    """one record per T-520 wall; 0.15 m figures from T-615 (asserted equal to T-520's beside figures)."""
    hosts = {ln["host_line_id"]: ln for ln in lines}
    recs, eq = [], []
    for wid, r in t520.items():
        t = float(r["t_m"])
        h = hosts.get(r["line_id"])
        low, fig, high = _f(r["perimeter_low_m3"]), _f(r["perimeter_figure_m3"]), _f(r["perimeter_high_m3"])
        status, held_why = r["status"], r["held"]
        if wid in t615:
            s = t615[wid]
            pl, pf, ph = _f(s["perimeter_low_m3"]), _f(s["perimeter_figure_m3"]), _f(s["perimeter_high_m3"])
            d = max(abs(pl - low), abs(pf - fig), abs(ph - high))
            eq.append({"wall_id": wid, "t520": [low, fig, high], "t615": [pl, pf, ph], "max_diff": _r(d)})
            if d > FIG_TOL:
                raise T372Error(f"{wid}: T-615 perimeter differs from T-520's beside figure by {d}")
            low, fig, high, status, held_why = pl, pf, ph, STATUS_015, ""
        in_host = True
        if h is not None and h["host_class"] == "RELEASED" and wid not in t615 and t == 0.15:
            in_host = False   # 0.15 wall outside T-615's 15 (own area cause): checked by the area sum below
        recs.append({"wall_id": wid, "floor": r["floor"], "t": t, "host_line_id": r["line_id"],
                     "area_m2": float(r["established_m2"]), "in_host": in_host, "low": low, "figure": fig,
                     "high": high, "status": status if status != "COMPUTED" else "COMPUTED",
                     "held_why": held_why, "expression": r["expression"],
                     "held_bands": int(r["held_bands"] or 0), "held_pieces": r["held_pieces"],
                     "soffit_m": _f(r["soffit_m"]), "vertical_exact_m": _f(r["vertical_exact_m"]),
                     "top_corners": int(r["top_corners"]) if r["top_corners"] else None,
                     "range_block_end_m": _f(r["range_block_end_m"])})
    return recs, eq


def own_arithmetic(recs, joint_m, face, module):
    """independent re-add of every carried wall's EXACT part and RANGE part from its lengths (not T-520's code)."""
    out = []
    for w in recs:
        if w["soffit_m"] is None or w["vertical_exact_m"] is None:
            continue
        f = factor(w["t"], face, module, joint_m)
        ex = wall_exact(w["soffit_m"], w["vertical_exact_m"], w["top_corners"] or 0, f, joint_m)
        hi = ex + f * (w["range_block_end_m"] or 0.0)
        out.append({"wall_id": w["wall_id"], "own_exact": _r(ex), "carried_low": w["low"],
                    "own_high": _r(hi), "carried_high": w["high"],
                    "d_low": _r(ex - w["low"]), "d_high": _r(hi - w["high"])})
    return out


def index_check(lines):
    """second path: every ledger line and its host read straight from the V3.0.63 line index (not via T-670)."""
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    if idx["candidate_version"] != "ARCH_TAKEOFF_V3.0.63":
        raise T372Error("line index is not V3.0.63")
    by_id = {x["line_id"]: x for x in idx["lines"]}
    n = 0
    for ln in lines:
        m, h = by_id.get(ln["line_id"]), by_id.get(ln["host_line_id"])
        if m is None or h is None or m["item_code"] != MORTAR or h["item_code"] != "MAS.BLOCK":
            raise T372Error(f"{ln['line_id']}: not a {MORTAR} line on a MAS.BLOCK host in V3.0.63")
        if m["element_id"] != "MATERIAL:" + h["element_id"] or h["element_id"] != ln["host"]:
            raise T372Error(f"{ln['line_id']}: element id does not name its host")
        if h["class"] != ln["host_class"] or h["measured_net"] != ln["host_net_m2"]:
            raise T372Error(f"{ln['line_id']}: host class / net differs from the index")
        n += 1
    allm = [x for x in idx["lines"] if x["item_code"] == MORTAR]
    if len(allm) != n:
        raise T372Error(f"the index has {len(allm)} {MORTAR} lines, the ledger {n}")
    return {"lines_checked": n, "mismatches": 0}


def trial_reconcile(out_rows):
    """the trial BOQ r4 (T-654, manifest V20 overlay) already stages one perimeter line per host
    (NEW:MAS.MORTAR.BLACK:PERIMETER:<host>) at the LOW end + a HELD companion 0 .. (high - low), OPEN where named
    pieces stay HELD: compare line by line (residual in m3), and its evidence label."""
    tr = json.loads(TRIAL_R4.read_text(encoding="utf-8"))
    per = {x["line_id"]: x for x in tr["per_line"] if x["item_code"] == MORTAR}
    out = []
    for r in out_rows:
        if r["perimeter_state"] == "HELD":
            continue
        hid = r["host_line_id"]
        t = per.get(f"NEW:{MORTAR}:PERIMETER:{hid}")
        comp = [x for k, x in per.items() if k.startswith(f"NEW:{MORTAR}:") and "#FR-T615-3:RANGE" in k
                and k.split(":", 2)[2].startswith(r["host"] + "#")]
        out.append({"mortar_line_id": r["mortar_line_id"], "host_line_id": hid,
                    "trial_line": None if t is None else t["line_id"],
                    "trial_low": None if t is None else t["measured_net"],
                    "ledger_low": r["perimeter_low_m3"],
                    "residual_low": None if t is None else _r(t["measured_net"] - r["perimeter_low_m3"]),
                    "trial_evidence": None if t is None else t["evidence"],
                    "trial_companion_high": None if not comp else comp[0]["held_high"],
                    "ledger_range_part": r["perimeter_range_part_m3"],
                    "ledger_open_named": r["open_high_named_pieces"]})
    return out


def build():
    t670, joint, lines, t520, t615 = project_inputs()
    idx_chk = index_check(lines)
    rb = _rulebook()
    face, module, j = joint["unit_m"], joint["module_m"], joint["joint_mm"] / 1000.0
    recs, eq = wall_records(t520, t615, lines)
    rows = bind(lines, recs)
    f_by_t = {0.15: factor(0.15, face, module, j), 0.20: factor(0.20, face, module, j)}
    own = own_arithmetic(recs, j, face, module)
    # lintel bearing bed per REQUIRED lintel (T-527 LINTEL_BEARING_V3 jamb evidence, merged)
    jambs = {}
    for r in _rows(T527_JAMBS):
        jambs.setdefault(r["opening_id"], []).append((r["side"], _f(r["available_m"]), r["stopper"]))
    lintel = []
    for ln in lines:
        for x in ln["lintels"] or []:
            if x["kind"] != "REQUIRED":
                lintel.append({"line_id": ln["line_id"], "opening_id": x["opening_id"], "state": "HELD",
                               "why": f"lintel {x['kind']} in the candidate (face not fixed)", "low": None,
                               "high": None})
                continue
            t = 0.15 if "t=0.15" in ln["host"] else 0.20
            b = lintel_bearing_bed(x["opening_id"], jambs.get(x["opening_id"], []), f_by_t[t])
            b.update({"line_id": ln["line_id"], "face_m2": x["face_m2"], "lintel_line_id": x["lintel_line_id"]})
            lintel.append(b)
    # T-520 held junction bands, named per line with their bound (m of joint x kappa b j), never summed
    host_of = {w["wall_id"]: w["host_line_id"] for w in recs}
    tof = {w["wall_id"]: w["t"] for w in recs}
    held_j = {}
    for r in _rows(T520_JUNCTIONS):
        if r["class"] != "HELD":
            continue
        held_j.setdefault(host_of[r["wall_id"]], []).append(
            {"wall_id": r["wall_id"], "band_m": [float(r["z0_m"]), float(r["z1_m"])], "ends": r["end_ids"],
             "bound_m3": [0.0, _r(f_by_t[tof[r["wall_id"]]] * float(r["increment_high_m"]))]})
    out_rows = []
    for r in rows:
        ln = next(x for x in lines if x["line_id"] == r["line_id"])
        pa = r["panel_after"]
        panel_lo = pa[1] if pa[0] == "VALUE" else (pa[1][0] if pa[0] == "RANGE" else None)
        panel_hi = pa[1] if pa[0] == "VALUE" else (pa[1][1] if pa[0] == "RANGE" else None)
        out_rows.append({
            "mortar_line_id": r["line_id"], "host_line_id": r["host_line_id"], "host": r["host"],
            "host_class": r["host_class"], "panel_after_t670": pa, "perimeter_state": r["state"],
            "perimeter_low_m3": r["low"], "perimeter_figure_m3": r["figure"], "perimeter_high_m3": r["high"],
            "perimeter_range_part_m3": r["range_part"],
            "pct_of_panel": None if r["low"] is None or not panel_lo else
            [_r(100 * r["low"] / panel_hi, 2), _r(100 * r["high"] / panel_lo, 2)],
            "walls": [w["wall_id"] for w in r["walls"]],
            "wall_status": sorted({w["status"] for w in r["walls"]}),
            "held_bands_named": sum(w["held_bands"] for w in r["walls"]),
            "open_high_named_pieces": sorted(w["wall_id"] for w in r["walls"] if w["held_pieces"]),
            "held_junctions": [h for h in held_j.get(r["host_line_id"], [])
                               if h["wall_id"] in {w["wall_id"] for w in r["walls"]}],
            "beside_held": [{"wall_id": w["wall_id"], "why": (w["held_why"] or "")[:200],
                             "expression": w["expression"], "figure_beside": [w["low"], w["high"]]}
                            for w in r["beside_held_walls"]],
            "held_cause": None if r["host_class"] == "RELEASED" else (ln["cause"] or "")[:240],
            "materials": None if r["low"] is None else materials(r["low"], r["high"], rb["cement_bags_per_m3"],
                                                                 rb["sand_m3_per_m3"])})
    val = [x for x in out_rows if x["perimeter_state"] != "HELD"]
    tot = {"lines_valued": len(val), "lines_held": len(out_rows) - len(val),
           "low": _r(sum(x["perimeter_low_m3"] for x in val)),
           "figure": _r(sum(x["perimeter_figure_m3"] for x in val)),
           "high": _r(sum(x["perimeter_high_m3"] for x in val)),
           "by_t": {}}
    for t in ("0.15", "0.20"):
        s = [x for x in val if f"t={t}" in x["host"]]
        tot["by_t"][t] = {"lines": len(s), "low": _r(sum(x["perimeter_low_m3"] for x in s)),
                          "high": _r(sum(x["perimeter_high_m3"] for x in s))}
    pv = [x["panel_after_t670"] for x in val]
    tot["panel_t670_valued"] = [_r(sum(p[1] if p[0] == "VALUE" else p[1][0] for p in pv)),
                                _r(sum(p[1] if p[0] == "VALUE" else p[1][1] for p in pv))]
    tot["materials"] = materials(tot["low"], tot["high"], rb["cement_bags_per_m3"], rb["sand_m3_per_m3"])
    lb = [x for x in lintel if x["state"] != "HELD"]
    tot["lintel_bearing_bed_beside"] = {"lintels": len(lb), "held": len(lintel) - len(lb),
                                        "low": _r(sum(x["low"] for x in lb)), "high": _r(sum(x["high"] for x in lb))}
    hj = [h for x in out_rows for h in x["held_junctions"]]
    tot["held_junction_bands_beside"] = {"bands": len(hj), "low": 0.0, "high": _r(sum(h["bound_m3"][1] for h in hj))}
    trial = trial_reconcile(out_rows)
    pinned = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (T670, T520_WALLS, T520_JUNCTIONS, T615_WALLS, T527_JAMBS, RB, INDEX, TRIAL_R4)}
    return {"task": "T-372", "rule": "R-T372-1 (PROPOSED)", "candidate": t670["candidate"],
            "rulebook": rb["version"], "joint": joint, "factor_m3_per_m": {str(k): _r(v, 8) for k, v in f_by_t.items()},
            "pinned": pinned, "index_check": idx_chk, "trial_r4_reconcile": trial, "t615_equals_t520": eq, "own_arithmetic": own, "lines": out_rows,
            "lintel_bearing_bed": lintel, "totals": tot}


def to_csv(rows):
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["mortar_line_id", "host", "host_class", "panel_after_t670", "perimeter_state", "low_m3", "figure_m3",
                "high_m3", "pct_of_panel", "walls", "beside_held", "held_cause"])
    for r in rows:
        w.writerow([r["mortar_line_id"], r["host"], r["host_class"], json.dumps(r["panel_after_t670"]),
                    r["perimeter_state"], r["perimeter_low_m3"], r["perimeter_figure_m3"], r["perimeter_high_m3"],
                    json.dumps(r["pct_of_panel"]), " ".join(r["walls"]),
                    " ".join(x["wall_id"] for x in r["beside_held"]), (r["held_cause"] or "")[:160]])
    return buf.getvalue()


if __name__ == "__main__":
    res = build()
    if "--check" in sys.argv:
        old = json.loads((OUT / "T372_PERIMETER_LEDGER.json").read_text(encoding="utf-8"))
        print("REPRODUCES" if old == json.loads(json.dumps(res)) else "DIFFERS")
        sys.exit(0 if old == json.loads(json.dumps(res)) else 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "T372_PERIMETER_LEDGER.json").write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False)
                                                    + "\n", encoding="utf-8")
    (OUT / "T372_PERIMETER_LEDGER.csv").write_text(to_csv(res["lines"]), encoding="utf-8")
    print(json.dumps(res["totals"], indent=1))
    print(json.dumps([x for x in res["own_arithmetic"] if abs(x["d_low"]) > 2e-6 or abs(x["d_high"]) > 2e-6],
                     indent=1))
