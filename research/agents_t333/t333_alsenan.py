"""T-333 Alsenan (development villa) BLOCKWORK FILL TABLE on the candidate of record ARCH_TAKEOFF_V3.0.21: the T-291
wall-to-line ledger (register v4, MERGED 0c6b2ba5) rebound to the V3.0.21 masonry line ids, the Checker's own values
on the walls it re-measured, the T-311 parapet blockwork alternative and plinth wall course placed once (R-T333-1).
Research only: no engine module, candidate line or released line changes; lane I (T-279) wires the FILL table.

    python3 -I research/agents_t333/t333_alsenan.py --extract <run>/t315   # writes CANDIDATE_V3021_MASONRY_LINES.json
    python3 -I research/agents_t333/t333_alsenan.py --write                # writes the fill files
    python3 -I research/agents_t333/t333_alsenan.py --check                # rebuilds in memory, compares bytes

<run>/t315 is a finished research/agents_t315/v3021_run.py run on the Drive copies (outside the repository). Inputs
(committed): research/agents_t291/* (ledger rule, register v4 binding, opening table), research/agents_t288/
BLOCKWORK_WALL_REGISTER_V4.csv, research/agents_t285/BLOCKWORK_WALL_REGISTER_V3.csv (v2 / v3 nets for the per-wall
history), research/agents_t311/PARAPET_RUN_LEDGER_T311.csv and PLINTH_SEGMENT_LEDGER_T311.csv, and the extract above
(line id, item code, storey, element, unit, state, quantity, RFI text; no coordinate, no name).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T291 = ROOT / "research" / "agents_t291"
T311 = ROOT / "research" / "agents_t311"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(T291))
import binding_fill as F        # noqa: E402
import t291_alsenan as A291     # noqa: E402
import wall_line_ledger as R    # noqa: E402

CANDIDATE = HERE / "CANDIDATE_V3021_MASONRY_LINES.json"
CANDIDATE_NAME = "ARCH_TAKEOFF_V3.0.21"
SCHEMA = "T333_BLOCKWORK_FILL_V1"
REG_V3 = ROOT / "research" / "agents_t285" / "BLOCKWORK_WALL_REGISTER_V3.csv"
REG_V4 = ROOT / "research" / "agents_t288" / "BLOCKWORK_WALL_REGISTER_V4.csv"
T175 = ROOT / "research" / "agents_t175" / "T175_OPENING_CONSEQUENCES.csv"

# The Checker's own values on the walls the row names (BOARD Verifier T-180 slot notes; SCOREBOARD BLOCKWORK row).
# A wall is carried at the Checker's own value; where the Checker re-measured twice, the later whole-wall value rules.
CHECKER_OWN = {
    "1F-W20": (24.5073, "VERIFIED", "Checker 2026-10-25 02:00 own whole-wall 24.5073 (reported 24.507)"),
    "1F-W22": (20.401, "VERIFIED", "Checker 2026-10-25 01:43 own whole-wall 20.401 (supersedes its 15:59 piece value "
                                   "20.402: B4 0.1245 read in the 01:43 re-measure)"),
    "GF-W16": (15.4356, "HELD ON DROP", "Checker 2026-10-25 02:00: 15.4356 - 2.950 d under sunken GF-141 (D-41; the "
                                        "d = 0 bound, never a quantity); register v4 15.4360 = +0.0004 from the drawn B5 "
                                        "band edge (T-288 s.3, Gate A PASS 643b310b)"),
}


# --- extract (needs a finished V3.0.21 run, outside the repository) --------------------------------------------
def extract(run_dir):
    run = Path(run_dir)
    src = run / "V3_0_21_BOQ_LINES.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    L = d if isinstance(d, list) else d["lines"]
    keep = []
    for l in L:
        if l["item_code"] not in A291.MASONRY_ITEMS and l.get("trade") != "MASONRY":
            continue
        c = l.get("calculation") or {}
        i = c.get("inputs") or {}
        keep.append({"line_id": l["line_id"], "item_code": l["item_code"], "trade": l.get("trade"),
                     "floor": l["location"]["floor"], "element_id": l["location"]["element_id"], "unit": l["unit"],
                     "evidence_state": l["evidence_state"], "measured_net": l.get("measured_net"),
                     "bounded_range": l.get("bounded_range"), "formula": c.get("formula"),
                     "walls_in_line": i.get("walls"), "rfi_question": (l.get("rfi") or {}).get("question"),
                     "project_id": (l.get("project") or {}).get("project_id"),
                     "revision_set_sha256": (l.get("project") or {}).get("revision_set_sha256")})
    csv_p = run / "V3_0_21_BOQ_LINES.csv"
    out = {"task": "T-333", "candidate": CANDIDATE_NAME,
           "candidate_lines_json_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
           "candidate_lines_csv_sha256": hashlib.sha256(csv_p.read_bytes()).hexdigest() if csv_p.exists() else None,
           "lines_total": len(L), "masonry_lines": keep}
    CANDIDATE.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def candidate():
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def _f(v):
    return None if v in (None, "") else float(v)


# --- build -----------------------------------------------------------------------------------------------------
def build():
    B = A291.build()                                   # the merged T-291 ledger on V3.0.15 ids (register v4)
    cand = candidate()
    new_lines = [dict(l, family=A291._family(l["element_id"])) for l in cand["masonry_lines"]]
    old_lines = B["lines"]
    mapping, unbound, actions = F.rebind(old_lines, new_lines)
    walls = {w["wall_id"]: w for w in B["walls"]}
    thick = {k: float(w["t_m"]) for k, w in walls.items()}

    rows = []
    for r in B["rows"]:
        n = mapping[r["line_id"]]
        rows.append(dict(r, line_id=n["line_id"], line_id_v3015=r["line_id"]))
    F.check_rows(rows, thick)
    basis = opening_height_basis(B["openings"])
    deducted = {}
    for o in basis:
        deducted.setdefault(o["host"], []).append(o)
    rows_r1 = rows
    rows = F.apply_fallback_labels(rows, deducted)          # rule 6 (r2, D-T333-1): labels only
    relabelled = sorted({(a["wall_id"], a["part_status"], b["part_status"]) for a, b in zip(rows_r1, rows)
                         if a["part_status"] != b["part_status"]})
    for a, b in zip(rows_r1, rows):                         # quantities are never touched by rule 6
        assert all(a[k] == b[k] for k in a if k != "part_status")
    closures = {it: R.closure(B["walls"], rows, it, "m3" if it == "ARCH.WALL_VOLUME" else "m2")
                for it in A291.AREA_VOLUME}

    # Checker-own values must equal what the fill carries (never the register where the Checker's own differs)
    checker = []
    for wid, (val, st, src) in CHECKER_OWN.items():
        rr = [r for r in rows if r["wall_id"] == wid and r["item_code"] == "MAS.BLOCK"]
        assert len(rr) == 1
        r = rr[0]
        carried = r["carried"] if r["carried"] is not None else r["upper"]
        diff = round(carried - val, 4)
        if r["status"] != st or abs(diff) > 0.0005:
            raise F.FillError(f"CHECKER_VALUE: {wid} fill {r['status']} {carried} vs Checker {st} {val}")
        checker.append({"wall_id": wid, "checker_value_m2": val, "checker_status": st, "fill_status": r["status"],
                        "fill_m2": carried, "difference_m2": diff, "source": src})

    components = components_t311(mapping, new_lines)
    F.check_components(components)

    # per line totals, before / after
    lsum = []
    for l in sorted(new_lines, key=lambda x: (x["item_code"], x["floor"], x["family"] or "")):
        if l["item_code"] not in A291.AREA_VOLUME:
            continue
        rr = [r for r in rows if r["line_id"] == l["line_id"]]
        t = F.line_totals(rr, l["unit"])
        old = next(k for k, v in mapping.items() if v["line_id"] == l["line_id"])
        lsum.append({"line_id": l["line_id"], "line_id_v3015": old, "same_id": old == l["line_id"],
                     "item_code": l["item_code"], "unit": l["unit"], "floor": l["floor"], "family": l["family"],
                     "before_state": l["evidence_state"], "before_quantity": l["measured_net"],
                     "action": actions[l["line_id"]], "walls": len(rr),
                     "verified": t["verified"], "drawing_confirmed": t["drawing_confirmed"],
                     "owner_approved": t["owner_approved"], "determinate": t["determinate"],
                     "established_parts": t["established_parts"], "drop_upper_at_d0": t["drop_upper_at_d0"],
                     "drop_coefficient": t["drop_coefficient"], "held": " ".join(t["held"]),
                     "after_expression": t["expression"]})
    # per block type x thickness (MAS.BLOCK m2 and WALL_VOLUME m3 apart)
    tsum = []
    for it, unit in (("MAS.BLOCK", "m2"), ("ARCH.WALL_VOLUME", "m3")):
        keys = sorted({(r["block_type"] or "-", r["family"]) for r in rows if r["item_code"] == it})
        for bt, fam in keys:
            rr = [r for r in rows if r["item_code"] == it and (r["block_type"] or "-") == bt and r["family"] == fam]
            t = F.line_totals(rr, unit)
            tsum.append({"item_code": it, "unit": unit, "block_type": bt, "thickness_m": fam, "walls": len(rr),
                         "before": "BLANK (every line BLOCKED_RFI)" if all(
                             l["measured_net"] is None for l in new_lines if l["item_code"] == it) else "FIGURE",
                         "verified": t["verified"], "drawing_confirmed": t["drawing_confirmed"],
                         "owner_approved": t["owner_approved"], "determinate": t["determinate"],
                         "established_parts": t["established_parts"], "drop_upper_at_d0": t["drop_upper_at_d0"],
                         "drop_coefficient": t["drop_coefficient"], "held_or_part_walls": len(rr) - sum(
                             1 for r in rr if r["status"] in F.DETERMINATE or r["status"] == F.HELD_ON_DROP),
                         "after_expression": t["expression"]})
    return {"base": B, "candidate": cand, "new_lines": new_lines, "mapping": mapping, "unbound": unbound,
            "actions": actions, "rows": rows, "closures": closures, "checker": checker, "components": components,
            "line_summary": lsum, "type_summary": tsum, "walls": walls, "opening_basis": basis,
            "relabelled": relabelled}


def opening_height_basis(openings):
    """rule 6 input: the height basis of every DEDUCTED opening of the merged T-291 opening table. An opening rests on
    the Q-55 fallback (ASSUMED — OWNER-APPROVED) when T-175 gives its height that status AND the deduction T-291
    carries is still width x that height (to 0.00005 m2), i.e. no later drawing reading superseded it; otherwise the
    deduction comes from the later drawing reading T-291 cites (T-227 s.6 heights, T-261 split, T-274 / T-288 jambs:
    DRAWING-CONFIRMED). A Q-55-status opening whose deduction differs from width x 2.20 without a drawing source is
    refused."""
    t175 = {r["opening"]: r for r in csv.DictReader(open(T175, encoding="utf-8"))}
    out = []
    for o in openings:
        if o["state"] != "DEDUCTED":
            continue
        r = t175.get(o["opening_id"])
        hs = r["height_status"] if r else None
        if hs == F.OWNER_APPROVED and abs(float(r["width_m"]) * float(r["height_m"]) - o["deduction_m2"]) <= 0.00005:
            b, why = F.OWNER_APPROVED, (f"Q-55 fallback height {r['height_m']} m (OWNER_QUESTIONS_ANSWERED Q-55; T-175 "
                                        f"height_status); {r['width_m']} x {r['height_m']} = {o['deduction_m2']:.4f}")
        elif hs == F.OWNER_APPROVED:
            raise F.FillError(f"STATE_UNKNOWN: {o['opening_id']} T-175 Q-55 height but T-291 deducts "
                              f"{o['deduction_m2']} from {o['source']!r}")
        else:
            b, why = "DRAWING-CONFIRMED", f"T-291 source: {o['source']}" + (
                f" (T-175 height_status {hs}, superseded)" if hs and hs != "DRAWING-CONFIRMED" else "")
        out.append({"opening_id": o["opening_id"], "host": o["host"], "kind": r["kind"] if r else None,
                    "deduction_m2": o["deduction_m2"], "height_basis": b, "basis_source": why})
    return out


def components_t311(mapping, new_lines):
    """rule 4: the T-311 parapet blockwork alternative per run (NO line, material HELD, outside every total) and the
    plinth wall course per segment (CONTAINED in the GF t=0.20 MAS.BLOCK line's wall heights, never added)."""
    gf20 = [l for l in new_lines if l["item_code"] == "MAS.BLOCK" and l["floor"] == "GF" and l["family"] == "0.2"]
    assert len(gf20) == 1
    gf20 = gf20[0]["line_id"]
    out = []
    for r in csv.DictReader(open(T311 / "PARAPET_RUN_LEDGER_T311.csv", encoding="utf-8")):
        run = f"{r['chain']} {r['side']}"
        lo, hi = float(r["block_m2_lo"]), float(r["block_m2_hi"])
        out.append({"component_id": f"PARAPET-BLOCK {run}", "run_or_zone": run, "kind": "ALTERNATIVE_BLOCK",
                    "line_id": None, "low": lo, "high": hi, "unit": "m2",
                    "volume_m3_low": round(lo * float(r["t_m"]), 6), "volume_m3_high": round(hi * float(r["t_m"]), 6),
                    "b_edge_increment_m2_per_m": round(float(r["centreline_m"]), 6),
                    "material_status": "HELD (Q-65 C designer: P1 block on a 0.30 RC upstand OR all RC)",
                    "added": False, "exclusive_with": "T-319 parapet RC part above the 0.30 upstand",
                    "source": "T-311 PARAPET_RUN_LEDGER_T311.csv (MERGED bd7b8c23)"})
        out.append({"component_id": f"PARAPET-RC {run}", "run_or_zone": run, "kind": "ALTERNATIVE_RC",
                    "line_id": None, "low": float(r["concrete_m3_lo"]), "high": float(r["concrete_m3_hi"]),
                    "unit": "m3", "material_status": "upstand 0.30 RC always; above it HELD", "added": False,
                    "above_upstand_carried": False, "exclusive_with": "PARAPET-BLOCK of the same run",
                    "source": "T-311 -> T-319 (lane I, the CONCRETE owner)"})
    for r in csv.DictReader(open(T311 / "PLINTH_SEGMENT_LEDGER_T311.csv", encoding="utf-8")):
        seg = f"{r['floor']} {r['side']} {r['portion']}"
        wc = _f(r["wall_course_m2"])
        held = None
        if wc is None:
            held = "passage face: no beam top read (T-311 s.4)"
        elif r["zone"] == "annex":
            held = "inside the annex GF walls, HELD on the annex datum (Q-54 B): blank with those walls"
        out.append({"component_id": f"PLINTH-COURSE {seg}", "run_or_zone": seg, "kind": "CONTAINED",
                    "line_id": gf20 if wc is not None else None, "low": wc, "high": wc, "unit": "m2", "zone": r["zone"],
                    "held_item": held, "added": False, "material_status": "",
                    "source": "T-311 PLINTH_SEGMENT_LEDGER_T311.csv: the GF wall starts at the structural top (house "
                              "beam / slab +0.95, annex beam +0.25), so the course up to the F.F.L. (+1.00 / +0.30) "
                              "is inside the wall height"})
    return out


# --- outputs ---------------------------------------------------------------------------------------------------
FILL_COLS = ["schema", "project_id", "revision_set_sha256", "candidate", "line_id", "line_id_v3015", "item_code", "unit",
             "floor", "family", "wall_id", "block_type", "status", "share", "carried", "upper_at_d0", "drop_length_m",
             "drop_coefficient", "part_status", "verified_by", "held_item", "conflict", "conflict_increment_outside",
             "opening_deductions"]


def _csv(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return b.getvalue()


def _num(v, nd=4):
    return None if v is None else f"{v:.{nd}f}"


def wall_table(X):
    """acceptance (a): per wall, its V3.0.21 MAS.BLOCK line, candidate before (blank), register v2 / v3 / v4 net and
    the cause, type / thickness, opening ids, status."""
    v3 = {r["wall_id"]: r for r in csv.DictReader(open(REG_V3, encoding="utf-8"))}
    v4 = {r["wall_id"]: r for r in csv.DictReader(open(REG_V4, encoding="utf-8"))}
    ops = {}
    for o in X["base"]["openings"]:
        for h in [x.strip() for x in o["host"].split("+")]:
            if h:
                ops.setdefault(h, []).append(f"{o['opening_id']} {o['state']}")
    out = []
    for r in sorted((r for r in X["rows"] if r["item_code"] == "MAS.BLOCK"), key=lambda r: (r["floor"], r["wall_id"])):
        w3, w4 = v3.get(r["wall_id"], {}), v4[r["wall_id"]]
        est = r["carried"] if r["carried"] is not None else None
        n3 = _f(w4["net_m2_v3"])
        out.append({"wall_id": r["wall_id"], "floor": r["floor"], "thickness_m": r["family"],
                    "block_type": r["block_type"], "line_id_v3021": r["line_id"],
                    "candidate_before": "BLANK (line BLOCKED_RFI, no wall key)",
                    "register_v2_net_m2": w3.get("net_m2_v2") or None, "register_v3_net_m2": w4["net_m2_v3"] or None,
                    "established_v4_m2": _num(est), "upper_at_d0_m2": _num(r["upper"]),
                    "drop_length_m": _num(r["drop_length_m"]),
                    "v4_minus_v3_m2": None if est is None or n3 is None else f"{est - n3:+.4f}",
                    "cause_v4": w4["cause_v4"] or None, "status": r["status"], "part_status": r["part_status"],
                    "verified_by": r["verified_by"], "held_item": r["held_item"],
                    "openings": "; ".join(ops.get(r["wall_id"], [])) or None})
    return out


def outputs(X):
    proj = X["candidate"]["masonry_lines"][0]
    fill = []
    for r in sorted(X["rows"], key=lambda r: (r["item_code"], r["floor"], r["family"], r["wall_id"])):
        nd = 6 if r["unit"] == "m3" else 4
        base = {"schema": SCHEMA, "project_id": proj.get("project_id"),
                "revision_set_sha256": proj.get("revision_set_sha256"), "candidate": CANDIDATE_NAME}
        ops = [f"{o['opening_id']} {'' if o['deduction_m2'] is None else format(o['deduction_m2'], '.4f')} "
               f"{o['state']}".replace("  ", " ") for o in X["base"]["openings"]
               if o["host"] == r["wall_id"] and o["state"] in ("DEDUCTED", "ON_HELD_WALL", "IN_HELD_PIECE", "HELD")]
        fill.append({**base, "line_id": r["line_id"], "line_id_v3015": r["line_id_v3015"],
                     "item_code": r["item_code"], "unit": r["unit"], "floor": r["floor"], "family": r["family"],
                     "wall_id": r["wall_id"], "block_type": r["block_type"], "status": r["status"],
                     "share": f"{r['share']:g}", "carried": _num(r["carried"], nd), "upper_at_d0": _num(r["upper"], nd),
                     "drop_length_m": _num(r["drop_length_m"]), "drop_coefficient": _num(r["drop_coefficient"], nd),
                     "part_status": r["part_status"], "verified_by": r["verified_by"], "held_item": r["held_item"],
                     "conflict": r["conflict"], "conflict_increment_outside": _num(r["conflict_increment"], nd),
                     "opening_deductions": "; ".join(ops)})
    rebind = [{"line_id_v3015": k, "line_id_v3021": v["line_id"], "same_id": k == v["line_id"],
               "item_code": v["item_code"], "unit": v["unit"], "floor": v["floor"], "family": v["family"],
               "state_v3021": v["evidence_state"], "quantity_v3021": v["measured_net"],
               "action": X["actions"][v["line_id"]] if v["item_code"] in A291.AREA_VOLUME else "NOT_FILLED (run lm)"}
              for k, v in sorted(X["mapping"].items(), key=lambda kv: (kv[1]["item_code"], kv[1]["floor"],
                                                                         kv[1]["family"] or ""))]
    comps = [{k: c.get(k) for k in ("component_id", "kind", "line_id", "low", "high", "unit", "volume_m3_low",
                                    "volume_m3_high", "b_edge_increment_m2_per_m", "material_status", "held_item",
                                    "exclusive_with", "source")} for c in X["components"]]
    for c in comps:
        for k in ("low", "high", "volume_m3_low", "volume_m3_high", "b_edge_increment_m2_per_m"):
            c[k] = _num(c[k], 6 if (k.startswith("volume") or c["unit"] == "m3") else 4)
    files = {
        "FILL_T333.csv": _csv(fill, FILL_COLS),
        "LINE_REBIND_T333.csv": _csv(rebind, list(rebind[0])),
        "LINE_BEFORE_AFTER_T333.csv": _csv(X["line_summary"], list(X["line_summary"][0])),
        "TYPE_BEFORE_AFTER_T333.csv": _csv(X["type_summary"], list(X["type_summary"][0])),
        "WALL_TABLE_T333.csv": _csv(wall_table(X), list(wall_table(X)[0])),
        "COMPONENTS_T333.csv": _csv(comps, list(comps[0])),
        "CHECKER_VALUES_T333.csv": _csv(X["checker"], list(X["checker"][0])),
        "OPENING_HEIGHT_BASIS_T333.csv": _csv(
            [dict(o, deduction_m2=_num(o["deduction_m2"])) for o in
             sorted(X["opening_basis"], key=lambda o: (o["host"], o["opening_id"]))], list(X["opening_basis"][0])),
    }
    par = [c for c in X["components"] if c["kind"] == "ALTERNATIVE_BLOCK"]
    pl = [c for c in X["components"] if c["kind"] == "CONTAINED"]
    mb = [r for r in X["line_summary"] if r["item_code"] == "MAS.BLOCK"]
    vol = [r for r in X["line_summary"] if r["item_code"] == "ARCH.WALL_VOLUME"]

    av_ids = {l["line_id"] for l in X["new_lines"] if l["item_code"] in A291.AREA_VOLUME}

    def tot(rs, k):
        return round(sum(r[k] for r in rs), 6)
    summary = {
        "task": "T-333", "rule": F.RULE_ID, "candidate": CANDIDATE_NAME,
        "candidate_lines_csv_sha256": X["candidate"]["candidate_lines_csv_sha256"],
        "candidate_lines_json_sha256": X["candidate"]["candidate_lines_json_sha256"],
        "candidate_lines_total": X["candidate"]["lines_total"],
        "base_ledger": "T-291 MERGED 0c6b2ba5 (V3.0.15 csv a4dc01dd, register v4 T-288 643b310b)",
        "masonry_lines": len(X["new_lines"]), "lines_same_id_as_v3015": sum(
            1 for k, v in X["mapping"].items() if k == v["line_id"]),
        "lines_unbound_in_v3021": X["unbound"],
        "filled_lines_actions": {a: sum(1 for lid, x in X["actions"].items() if x == a and lid in av_ids)
                                 for a in sorted({x for lid, x in X["actions"].items() if lid in av_ids})},
        "run_lines_not_filled_lm": sorted(lid for lid in X["actions"] if lid not in av_ids),
        "area_volume_lines_with_quantity_before": sum(1 for l in X["new_lines"] if l["item_code"] in A291.AREA_VOLUME
                                                      and l["measured_net"] is not None),
        "fill_rows": len(X["rows"]), "walls": len(X["walls"]), "closures": X["closures"],
        "MAS.BLOCK_m2_after": {"verified": tot(mb, "verified"), "drawing_confirmed": tot(mb, "drawing_confirmed"),
                               "owner_approved": tot(mb, "owner_approved"), "determinate": tot(mb, "determinate"),
                               "established_parts": tot(mb, "established_parts"),
                               "drop_upper_at_d0": tot(mb, "drop_upper_at_d0"),
                               "drop_coefficient_m2_per_m_of_d": tot(mb, "drop_coefficient"),
                               "held_walls": sum(1 for r in X["rows"] if r["item_code"] == "MAS.BLOCK"
                                                 and r["status"] == F.HELD),
                               "established_part_plus_held_walls": sum(
                                   1 for r in X["rows"] if r["item_code"] == "MAS.BLOCK" and r["status"] == F.PART_PLUS_HELD),
                               "held_on_drop_walls": sum(1 for r in X["rows"] if r["item_code"] == "MAS.BLOCK"
                                                         and r["status"] == F.HELD_ON_DROP),
                               "conflict_increments_outside": round(sum(
                                   r["conflict_increment"] or 0 for r in X["rows"] if r["item_code"] == "MAS.BLOCK"), 6)},
        "ARCH.WALL_VOLUME_m3_after": {"determinate": tot(vol, "determinate"),
                                      "established_parts": tot(vol, "established_parts"),
                                      "drop_upper_at_d0": tot(vol, "drop_upper_at_d0"),
                                      "drop_coefficient_m3_per_m_of_d": tot(vol, "drop_coefficient")},
        "checker_values": X["checker"],
        "parapet_block_alternative_m2": [round(sum(c["low"] for c in par), 4), round(sum(c["high"] for c in par), 4)],
        "parapet_block_alternative_m3": [round(sum(c["volume_m3_low"] for c in par), 6),
                                         round(sum(c["volume_m3_high"] for c in par), 6)],
        "parapet_runs": len(par),
        "plinth_course_contained_m2": round(sum(c["low"] for c in pl if c["low"] is not None), 4),
        "plinth_course_house_zone_m2 (inside the GF 0.20 exterior wall heights; T-311 gives no per-wall split, so "
        "it rides each wall's own status)": round(sum(c["low"] for c in pl if c["low"] is not None
                                                     and not c["held_item"]), 4),
        "plinth_course_annex_zone_inside_held_walls_m2": round(sum(c["low"] for c in pl if c["low"] is not None
                                                                   and c["held_item"]), 4),
        "plinth_segments": len(pl), "plinth_segments_held": sum(1 for c in pl if c["low"] is None),
        "rule6_r2_D-T333-1": {
            "deducted_openings": len(X["opening_basis"]),
            "on_q55_fallback_height": sorted(o["opening_id"] for o in X["opening_basis"]
                                             if o["height_basis"] == F.OWNER_APPROVED),
            "part_status_relabelled (wall, r1, r2)": [list(x) for x in X["relabelled"]],
            "established_parts_m2_by_part_status": {
                s: round(sum(r["carried"] for r in X["rows"] if r["item_code"] == "MAS.BLOCK"
                             and r["status"] == F.PART_PLUS_HELD and r["part_status"] == s), 4)
                for s in sorted({r["part_status"] for r in X["rows"] if r["status"] == F.PART_PLUS_HELD})},
            "quantities_changed": "none (labels only)"},
    }
    files["summary.json"] = json.dumps(summary, indent=1, ensure_ascii=False) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract")
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        out = extract(a.extract)
        print(f"masonry lines {len(out['masonry_lines'])} of {out['lines_total']}; "
              f"csv {(out['candidate_lines_csv_sha256'] or '')[:8]}")
        return 0
    files = outputs(build())
    if a.write:
        for n, s in files.items():
            (HERE / n).write_text(s, encoding="utf-8")
        print("written:", ", ".join(files))
        return 0
    bad = [n for n, s in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != s]
    print("CHECK", "FAIL " + ", ".join(bad) if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
