"""T-335 Alsenan (development villa): the Checker-verified ceiling ledgers (T-283 r3 via the T-295 face-to-line
ledger, both MERGED) bound to the CANDIDATE OF RECORD ARCH_TAKEOFF_V3.0.21 FIN.CEILING line ids, and cross-checked
against the V3.0.20 / V3.0.21 interior plaster / paint / wall-tile lines of the same rooms (R-T335-1). Research only:
no engine module, candidate line or released line changes; lane I (T-284) applies the FILL table.

    python3 -I research/agents_t335/t335_alsenan.py --extract <run>/v3021   # writes CANDIDATE_V3021_T335.json
    python3 -I research/agents_t335/t335_alsenan.py --write                 # writes the ledger files
    python3 -I research/agents_t335/t335_alsenan.py --check                 # rebuilds in memory, compares bytes

Inputs (committed): research/agents_t295/CEILING_FACE_LINE_LEDGER_T295.csv + LINE_SUMMARY_T295.csv +
CANDIDATE_V3015_CEILING_LINES.json (T-295 MERGED 964c5ebe, Gate A 2026-10-25 15:33), research/agents_t271/
VS_FREELANCER_T271.csv (the freelancer's ceiling cells, T-271 r2b MERGED 789ebbb4) and CANDIDATE_V3021_T335.json
(extracted here from an own V3.0.21 run: ids, item codes, room / element ids, units, states, quantities, wall runs,
formulas; no coordinates, no names).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import ceiling_cross_trade as X  # noqa: E402

T295 = ROOT / "research" / "agents_t295"
LEDGER = T295 / "CEILING_FACE_LINE_LEDGER_T295.csv"
SUMMARY = T295 / "LINE_SUMMARY_T295.csv"
CAND15 = T295 / "CANDIDATE_V3015_CEILING_LINES.json"
FREEL = ROOT / "research" / "agents_t271" / "VS_FREELANCER_T271.csv"
CANDIDATE = HERE / "CANDIDATE_V3021_T335.json"
SCHEMA = "T335_CEILING_V3021_BINDING_V1"
CEIL = ("FIN.CEILING",)
WALL = ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE")
LAYER = {"FIN.PLASTER": X.PLASTER, "FIN.PAINT": X.PAINT, "FIN.WALL.TILE": X.TILE}
# owner wall height = underside of the 0.15 decor ceiling (Q-48 A; Q-43): plaster, paint and tile stop there
DECOR_UNDERSIDE = {"GF": 3.65, "1F": 3.35, "2F": 3.35}
DECOR_DEPTH = 0.15
HORIZONTAL = re.compile(r"plan area|floor area|floor face|soffit area|ceiling area", re.I)
FACE = re.compile(r"([0-9.]+) m face x ([0-9.]+) m owner height")
Q48 = "Q-48 A + Q-43 (owner 2026-10-19/20: wall finish to the underside of the 0.15 decor ceiling, GF 3.65, 1F / 2F 3.35)"
Q52 = ("Q-52 C MODIFIED: plaster MAY run above the false ceiling depending on the specification; no specification or "
       "section prints it -> the band (wall run x 0.15) is HELD 0 .. run x 0.15, in no line")
SRC295 = "T-295 MERGED 964c5ebe (Verifier 2026-10-25 15:33, Gate A)"
OUT = {
    "rebind": HERE / "LINE_REBIND_T335.csv",
    "fill": HERE / "FILL_T284_T335.csv",
    "cross": HERE / "CROSS_TRADE_T335.csv",
    "freel": HERE / "FREELANCER_T335.csv",
    "summary": HERE / "summary.json",
}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(s):
    s = (s or "").strip()
    return float(s) if s else None


# ----------------------------------------------------------------------------------------------- extraction
def extract(run_dir):
    run = Path(run_dir)
    src = run / "V3_0_21_BOQ_LINES.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    L = d if isinstance(d, list) else d["lines"]
    keep = []
    for l in L:
        if l["item_code"] not in CEIL + WALL:
            continue
        c = l.get("calculation") or {}
        inp = c.get("inputs") or {}
        loc = l.get("location") or {}
        om = inp.get("owner_manual_method") if isinstance(inp.get("owner_manual_method"), dict) else {}
        keep.append({"line_id": l["line_id"], "item_code": l["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": l["unit"],
                     "evidence_state": l["evidence_state"], "measured_net": l.get("measured_net"),
                     "gross": l.get("gross"), "bounded_range": l.get("bounded_range"),
                     "formula": c.get("formula"),
                     "wall_run_lm": inp.get("wall_run_lm"),
                     "owner_height_m": om.get("height_m", om.get("owner_wall_height_m")),
                     "ceiling_type": inp.get("ceiling_type")})
    keep.sort(key=lambda x: (x["item_code"], x["floor"] or "", x["room_id"] or "", x["element_id"] or "",
                             x["line_id"]))
    csv_p = run / "V3_0_21_BOQ_LINES.csv"
    out = {"task": "T-335", "candidate": "ARCH_TAKEOFF_V3.0.21",
           "candidate_lines_json_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
           "candidate_lines_csv_sha256": hashlib.sha256(csv_p.read_bytes()).hexdigest() if csv_p.exists() else None,
           "lines_total": len(L), "lines": keep}
    CANDIDATE.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


# ----------------------------------------------------------------------------------------------- build
def build():
    cand = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    c15 = json.loads(CAND15.read_text(encoding="utf-8"))
    ledger = _rows(LEDGER)
    lsum = _rows(SUMMARY)
    L21 = {l["line_id"]: l for l in cand["lines"]}
    ceil21 = {k: l for k, l in L21.items() if l["item_code"] in CEIL}
    ceil15 = {l["line_id"]: l for l in c15["lines"] if l["item_code"] in CEIL}

    # (1) rebind: every T-295 line id against V3.0.21 (id, state, quantity, gross)
    rebind = []
    for lid in sorted(set(ceil15) | set(ceil21)):
        a, b = ceil15.get(lid), ceil21.get(lid)
        same = bool(a and b and a["evidence_state"] == b["evidence_state"] and a["measured_net"] == b["measured_net"]
                    and a["gross"] == b["gross"] and a["room_id"] == b["room_id"] and a["element_id"] == b["element_id"])
        rebind.append({"line_id": lid, "element_id": (b or a)["element_id"], "role": X.ceiling_role((b or a)["element_id"]),
                       "v3015_state": a and a["evidence_state"], "v3015_m2": a and a["measured_net"],
                       "v3021_state": b and b["evidence_state"], "v3021_m2": b and b["measured_net"],
                       "verdict": "SAME" if same else ("GONE" if not b else "NEW" if not a else "CHANGED")})

    # (2) faces -> surfaces and ceiling claims (R-T335-1 rule 1 / 2 / 4)
    lines = {}
    for lid, l in ceil21.items():
        lines[lid] = {"line_id": lid, "item_code": l["item_code"], "role": X.ceiling_role(l["element_id"])}
    kind_of = {"DECOR": X.DECOR, "BULKHEAD": X.BULKHEAD, "HELD_CEILING": X.HELD_CEILING, "STAIR_TOP": X.HELD_CEILING,
               "STAIR_SOFFIT": X.STAIR_SOFFIT, "VOID": X.VOID, "DOME": X.DOME}
    surfaces, claims = {}, []
    for r in ledger:
        if r["binding"].startswith("ALTERNATIVE"):
            continue
        sid = r["face_id"]
        st = r["status"]
        surfaces[sid] = {"surface_id": sid, "room_id": r["room_id"], "kind": kind_of[r["owner"]],
                         "m2": _f(r["plan_m2"]) if r["owner"] != "BULKHEAD" else _f(r["carried"]),
                         "status": st if st != "CONFLICT" else "HELD",
                         "held_item": r["held_item"] or None}
        if st in X.DETERMINATE:
            for lid in [x for x in (r["line_id"], *(r["line_group"] or "").split(" + ")) if x][:1]:
                claims.append({"surface_id": sid, "layer": X.BOARD if r["owner"] != "STAIR_SOFFIT" else X.PLASTER,
                               "line_id": lid})

    # (3) wall lines of every room that has a ceiling line: one WALL surface per line, its layer claim.
    #     A line with a quantity (PROVISIONAL) is determinate (owner height method: ASSUMED - OWNER-APPROVED, Q-43 /
    #     Q-48 A); a BOUNDED / BLOCKED line is HELD with its range (never 0); a NOT_APPLICABLE_WITH_EVIDENCE line is
    #     superseded (by the HL:WALL_FINISH line of the same room) or a full-height-tile 'paint above tile' line: listed.
    ceil_rooms = sorted({l["room_id"] for l in ceil21.values() if lines[l["line_id"]]["role"] != "EXTERIOR"})
    walls = []
    for lid, l in sorted(L21.items()):
        if l["item_code"] not in WALL or l["room_id"] not in ceil_rooms:
            continue
        floor = l["floor"]
        f = l["formula"] or ""
        horizontal = bool(HORIZONTAL.search(f))
        m = FACE.search(f)
        length = float(m.group(1)) if m else l["wall_run_lm"]
        top = float(m.group(2)) if m else (l["owner_height_m"] or DECOR_UNDERSIDE.get(floor))
        q = l["measured_net"]
        st = l["evidence_state"]
        rng = l["bounded_range"] or {}
        walls.append({"line_id": lid, "item_code": l["item_code"], "room_id": l["room_id"], "floor": floor,
                      "element_id": l["element_id"], "state": st, "m2": q,
                      "range": (rng.get("low"), rng.get("high")) if rng else None,
                      "formula": f, "length_m": length, "top_m": top, "horizontal_term": horizontal})
        if st == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        sid = f"{l['room_id']}|wall|{lid}"
        held = q is None
        surfaces[sid] = {"surface_id": sid, "room_id": l["room_id"], "kind": X.WALL, "m2": q,
                         "status": "HELD" if held else X.DETERMINATE[2],
                         "held_item": (f"{st} wall line (its own RFI / held openings)" if held else None),
                         "top_m": top, "length_m": length}
        lines[lid] = {"line_id": lid, "item_code": l["item_code"]}
        if not held:
            claims.append({"surface_id": sid, "layer": LAYER[l["item_code"]], "line_id": lid})
        if horizontal:          # a wall line whose formula measures a plan area would book the ceiling plane
            dec = [k for k, v in surfaces.items() if v["room_id"] == l["room_id"] and v["kind"] == X.DECOR]
            for k in dec:
                claims.append({"surface_id": k, "layer": LAYER[l["item_code"]], "line_id": lid})
    X.validate(claims, surfaces, lines)                       # refuses any double count / misplaced layer

    # (4) per room cross-trade; the hidden band per FACE (plaster / tile lines; paint repeats the plaster face)
    cross = []
    for rid in ceil_rooms:
        floor = next(l["floor"] for l in ceil21.values() if l["room_id"] == rid)
        du = DECOR_UNDERSIDE[floor]
        r = X.cross_trade(rid, surfaces, claims, lines)
        mine = [w for w in walls if w["room_id"] == rid]
        live = [w for w in mine if w["state"] != "NOT_APPLICABLE_WITH_EVIDENCE"]
        band_hi, gap, band_basis, faces_seen = 0.0, 0.0, [], set()
        for w in live:
            if w["item_code"] == "FIN.PAINT" or w["length_m"] is None or w["top_m"] is None:
                continue
            if round(w["length_m"], 3) in faces_seen:     # the tile line repeats the plaster face: one band per face
                continue
            faces_seen.add(round(w["length_m"], 3))
            if w["state"] == "BLOCKED_RFI" and abs(w["top_m"] - du) > X.TOL_H:
                band_basis.append(f"{w['line_id']} top {w['top_m']:.2f} HELD (its own RFI)")
                continue
            b = X.wall_band({"surface_id": w["line_id"], "length_m": w["length_m"], "top_m": w["top_m"]}, du,
                            du + DECOR_DEPTH)
            band_hi += b["band_m2"][1]
            gap += b["gap_m2"]
            band_basis.append(f"{w['item_code'][4:]} {w['length_m']:.3f} x {DECOR_DEPTH}")
        cross.append({"room_id": rid, "floor": floor, "decor_underside_m": du,
                      "ceiling_lines": " ".join(sorted(l["line_id"] for l in ceil21.values() if l["room_id"] == rid)),
                      "decor_board_m2": r["carried_m2"].get("DECOR / BOARD / FIN.CEILING", 0.0),
                      "bulkhead_board_m2": r["carried_m2"].get("BULKHEAD / BOARD / FIN.CEILING", 0.0),
                      "wall_lines": len(mine), "wall_lines_live": len(live),
                      "wall_states": " ".join(sorted({f"{w['item_code'][4:]}:{w['state']}" for w in live})),
                      "wall_tops_m": " ".join(sorted({f"{w['top_m']:.2f}" for w in live if w["top_m"]})),
                      "horizontal_in_wall_lines_m2": 0.0 if not any(w["horizontal_term"] for w in mine) else None,
                      "band_held_hi_m2": round(band_hi, 4) if band_basis else None,
                      "band_basis": "; ".join(band_basis),
                      "gap_m2": round(gap, 4), "double_count_m2": r["double_count_m2"],
                      "held": "; ".join(sorted({h["held_item"][:70] for h in r["held"] if h["kind"] != X.WALL}))})

    # (5) FILL table for T-284: one row per V3.0.21 FIN.CEILING line (or line group), from T-295 unchanged
    fill = []
    for s in lsum:
        key = s["line_key"]
        rows = [r for r in ledger if r["line_id"] == key or r["line_group"] == key]
        st21 = " + ".join(ceil21[x]["evidence_state"] for x in key.split(" + "))
        before = None if any(ceil21[x]["measured_net"] is None for x in key.split(" + ")) else \
            round(sum(ceil21[x]["measured_net"] for x in key.split(" + ")), 6)
        dec = round(sum(_f(r["carried"]) for r in rows if r["owner"] == "DECOR" and r["status"] in X.DETERMINATE), 6)
        blk = round(sum(_f(r["carried"]) for r in rows if r["owner"] == "BULKHEAD" and r["status"] in X.DETERMINATE), 6)
        sof = round(sum(_f(r["carried"]) for r in rows if r["owner"] == "STAIR_SOFFIT" and r["status"] in X.DETERMINATE), 6)
        held = [r for r in rows if r["status"] in ("HELD", "UNKNOWN", "CONFLICT")]
        role = X.ceiling_role(ceil21[key.split(" + ")[0]]["element_id"])
        if role == "EXTERIOR":
            action = "UNCHANGED: exterior soffit over outside air (T-121 / T-127), no interior face; check P-2 overlap"
        elif len(key.split(" + ")) > 1:
            action = "LINE GROUP: carry the group total; never split pro rata (void overlay split not established)"
        elif before is None:
            action = "BLOCKED line: before BLANK; fill the determinate faces, HELD faces stay BLANK by item"
        else:
            action = "REPLACE plan area by decor (DRAWING-CONFIRMED) + bulkhead (ASSUMED - OWNER-APPROVED) apart"
        fill.append({"line_key": key, "elements": s["elements"], "role": role, "v3021_state": st21,
                     "before_m2": before, "decor_dc_m2": dec or None, "bulkhead_aoa_m2": blk or None,
                     "stair_soffit_dc_m2": sof or None,
                     "after_horizontal_m2": round(dec + sof, 6) if (dec or sof) else None,
                     "horizontal_change_m2": (round(dec + sof - before, 6) if before is not None and (dec or sof)
                                              else None),
                     "held_blank": "; ".join(f"{r['face_id']} {r['plan_m2']} ({r['held_item'][:60]})" for r in held),
                     "action": action})
    no_line = [r for r in ledger if r["binding"].startswith("NO_LINE") and r["owner"] == "DECOR"]
    for r in no_line:
        fill.append({"line_key": "NEW LINE NEEDED", "elements": f"{r['room_id']}:ceiling", "role": "CEILING",
                     "v3021_state": "NO LINE", "before_m2": None, "decor_dc_m2": _f(r["carried"]),
                     "bulkhead_aoa_m2": None, "stair_soffit_dc_m2": None, "after_horizontal_m2": _f(r["carried"]),
                     "horizontal_change_m2": None, "held_blank": "",
                     "action": "ADD one FIN.CEILING line (missing scope, T-295 finding c; Gate B hand check)"})

    # (6) freelancer by cell (never proof)
    piece_decor = {}
    for r in ledger:
        if r["owner"] == "DECOR" and r["status"] in X.DETERMINATE:
            p = r["piece"] or r["room_id"]
            piece_decor[p] = round(piece_decor.get(p, 0.0) + _f(r["carried"]), 6)
    freel = []
    for r in _rows(FREEL):
        ps = r["PIECES"].split()
        dec = round(sum(piece_decor.get(p, 0.0) for p in ps), 4)
        fq = float(r["FREELANCER_M2"])
        held = sorted({x["held_item"][:48] for x in ledger if (x["piece"] in ps or x["room_id"] in ps)
                       and x["status"] in ("HELD", "CONFLICT") and x["owner"] != "STAIR_SOFFIT"})
        freel.append({"freelancer_row": r["FREELANCER_ROW"], "pieces": r["PIECES"], "freelancer_m2": fq,
                      "decor_dc_m2": dec, "diff_m2": round(dec - fq, 4),
                      "diff_pct": round(100 * (dec - fq) / fq, 2), "held_in_pieces": "; ".join(held)})

    double = round(sum(c["double_count_m2"] for c in cross), 6)
    tot = {"decor_dc_m2": round(sum(_f(r["carried"]) for r in ledger if r["owner"] == "DECOR"
                                    and r["status"] in X.DETERMINATE), 6),
           "bulkhead_aoa_m2": round(sum(_f(r["carried"]) for r in ledger if r["owner"] == "BULKHEAD"
                                        and r["status"] in X.DETERMINATE), 6),
           "engine_interior_ceiling_m2": round(sum(l["measured_net"] for l in ceil21.values()
                                                   if l["measured_net"] is not None
                                                   and X.ceiling_role(l["element_id"]) != "EXTERIOR"), 6),
           "wall_band_held_hi_m2": round(sum(c["band_held_hi_m2"] or 0.0 for c in cross), 4),
           "double_count_m2": double}
    return {"cand": cand, "rebind": rebind, "fill": fill, "cross": cross, "walls": walls, "freel": freel,
            "tot": tot, "claims": claims, "surfaces": surfaces, "lines": lines}


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return buf.getvalue()


def outputs(B):
    c = B["cand"]
    reb = _csv(B["rebind"], ["line_id", "element_id", "role", "v3015_state", "v3015_m2", "v3021_state", "v3021_m2",
                             "verdict"])
    fil = _csv(B["fill"], ["line_key", "elements", "role", "v3021_state", "before_m2", "decor_dc_m2",
                           "bulkhead_aoa_m2", "stair_soffit_dc_m2", "after_horizontal_m2", "horizontal_change_m2",
                           "held_blank", "action"])
    cro = _csv(B["cross"], ["room_id", "floor", "decor_underside_m", "ceiling_lines", "decor_board_m2",
                            "bulkhead_board_m2", "wall_lines", "wall_lines_live", "wall_states", "wall_tops_m",
                            "horizontal_in_wall_lines_m2", "band_held_hi_m2", "band_basis", "gap_m2",
                            "double_count_m2", "held"])
    fre = _csv(B["freel"], ["freelancer_row", "pieces", "freelancer_m2", "decor_dc_m2", "diff_m2", "diff_pct",
                            "held_in_pieces"])
    verdicts = {}
    for r in B["rebind"]:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    summ = {"schema": SCHEMA, "rule": X.RULE_ID, "candidate": c["candidate"],
            "candidate_lines_json_sha256": c["candidate_lines_json_sha256"],
            "candidate_lines_csv_sha256": c["candidate_lines_csv_sha256"], "lines_total": c["lines_total"],
            "inputs_sha256": {p.name: _sha(p)[:16] for p in (LEDGER, SUMMARY, CAND15, FREEL, CANDIDATE)},
            "ceiling_lines_v3021": sum(1 for r in B["rebind"] if r["v3021_state"]),
            "rebind_verdicts": dict(sorted(verdicts.items())),
            "wall_lines_in_ceiling_rooms": len(B["walls"]),
            "wall_lines_with_a_horizontal_term": sum(1 for w in B["walls"] if w["horizontal_term"]),
            "claims": len(B["claims"]), "totals": B["tot"],
            "owner_rules": [Q48, Q52, SRC295],
            "released": "NOTHING RELEASED; candidate and released lines unchanged (research ledger)"}
    return {OUT["rebind"].name: reb, OUT["fill"].name: fil, OUT["cross"].name: cro, OUT["freel"].name: fre,
            OUT["summary"].name: json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract")
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        o = extract(a.extract)
        print(f"extracted {len(o['lines'])} lines of {o['lines_total']}; json {o['candidate_lines_json_sha256'][:8]}")
        return 0
    F = outputs(build())
    if a.write:
        for n, t in F.items():
            (HERE / n).write_text(t, encoding="utf-8")
        print("written", ", ".join(F))
        return 0
    bad = [n for n, t in F.items() if (HERE / n).read_text(encoding="utf-8") != t]
    print("check", "OK" if not bad else f"DIFFERS {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
