"""T-342 Alsenan (development villa): census binding of the room labels the label census finds in no room (NO_ROOM),
on the CANDIDATE ARCH_TAKEOFF_V3.0.22 (R-T342-BIND-1, t342_label_binding.py). Research only: no engine module,
candidate line or released line changes.

    python3 -I research/agents_t342/t342_alsenan.py --extract <run>/v3022 --census <census.json>  # writes the extracts
    python3 -I research/agents_t342/t342_alsenan.py --write                                       # writes the ledger
    python3 -I research/agents_t342/t342_alsenan.py --check                                       # rebuild, compare bytes

Inputs (committed): CENSUS_T342.json (tools/label_census.py on Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip,
P7757.dxf sha256 ab54dd55.., ARCH_TAKEOFF_V2.9 room set: text ids, room-vocabulary words and statuses only),
CANDIDATE_V3022_T342.json (ids, item codes, element ids, units, states, quantities and the entity handles / element
tokens of each line's own inputs: no coordinates, no names), research/agents_t071/alsenan_exterior_spaces.json (the
exterior faces round the held labels: label lists, closure / hole handles, areas), research/agents_t157/AREAS_T157.csv
(the court pieces). Drawing readings added here are cited by DXF entity handle.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT):
    sys.path.insert(0, str(p))
import t342_label_binding as B  # noqa: E402

CENSUS = HERE / "CENSUS_T342.json"
CAND = HERE / "CANDIDATE_V3022_T342.json"
T071 = ROOT / "research" / "agents_t071" / "alsenan_exterior_spaces.json"
OUT = {"binding": HERE / "LABEL_BINDING_T342.csv", "scopes": HERE / "SCOPES_T342.csv", "summary": HERE / "summary.json"}
DXF = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, P7757.dxf"
TARGET = ("AT19", "AT20", "AT21", "AT22", "AT39", "AT40", "AT225", "AT385")
KEEP = ("STR.CONC.POOL", "FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "FIN.CEILING", "FIN.FLOOR.", "FIN.MARBLE.", "FLOOR.",
        "WP.POOL", "FIN.WP.POOL", "ARCH.EXTERIOR", "ARCH.SPACE", "FIN.EXT")

# ---- drawing readings of this task (P7757.dxf, GF plan, layer 5) ------------------------------------------------
# pool outline: half circles ARC 200 (r 1750) and ARC 202 (r 1550), both 90 -> 270 deg about one centre, closed east by
# LINEs 203 / 205 (water, y -/+1550) and 204 / 206 (outer, y -/+1750), each 1550 long to the boundary-wall face: a D,
# not a circle (the r 1.55 / 1.75 'circle' reading of T-153 / T-157 is not the drawn outline)
WATER_M2 = math.pi * 1.55 ** 2 / 2 + 3.10 * 1.55            # 3.773838 + 4.805 = 8.578838
WATER_LM = math.pi * 1.55 + 3.10 + 2 * 1.55                 # 4.869469 + 6.200 = 11.069469
OUTER_CUT_M2 = math.pi * 1.75 ** 2 / 2 + 3.50 * 1.55        # 4.810563 + 5.425 = 10.235563 (to the boundary-wall face)
OUTER_CUT_LM = math.pi * 1.75 + 3.50 + 2 * 1.55             # 5.497787 + 6.600 = 12.097787
FIN_DEPTH = 0.30 + 0.85                                     # rim +0.30 -> finished floor -0.85 (T-183 r2 NW cut 1150)
POOL_COURT_FACE = 17.3414                                   # T-157 pool court piece (DRAWING-CONFIRMED, merged)
T157 = {"open": 119.5416, "porch": 10.679, "e1": 3.3594, "landing": 5.1794, "walk": 21.0142, "deck_old": 7.9392,
        "walk_manual": 23.955, "riser": 1.96, "pool_outer_old": 9.4022}


def _r(x, n=6):
    return None if x is None else round(x, n)


# ---- extract (needs the private run; writes only ids, codes, quantities, handles) --------------------------------
def extract(run_dir, census_json):
    lines = json.loads((Path(run_dir) / "V3_0_22_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines = lines if isinstance(lines, list) else lines["lines"]
    keep = []
    for ln in lines:
        code = ln["item_code"]
        if not any(code == k or (k.endswith(".") and code.startswith(k)) for k in KEEP):
            continue
        loc = ln.get("location") or {}
        if code.startswith(("FIN.FLOOR.", "FIN.MARBLE.", "ARCH.SPACE", "FIN.CEILING")) and loc.get("room_id") and \
                not str(loc.get("room_id")).startswith(("PL-", "HL", "EXT")) and "OUTDOOR" not in json.dumps(ln):
            continue                                     # interior room lines: covered by their own rooms
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        src = sorted({g.get("from_line") for g in inp.get("gaps_closed") or () if g.get("from_line")})
        eid = loc.get("element_id") or ""
        toks = sorted({t for t in eid.replace("/", ":").split(":") if t[:3] in ("POO", "PL-", "SOF") or
                       t.startswith(("POOL-", "PL-"))})
        cites = sorted({t.split("-")[-1] for t in eid.split(":") if "-AT" in t} |
                       ({inp["label"]} if inp.get("label") else set()))
        keep.append({"line_id": ln["line_id"], "item_code": code, "floor": loc.get("floor"), "element_id": eid,
                     "room_id": loc.get("room_id"), "unit": ln.get("unit"), "state": ln.get("evidence_state"),
                     "quantity": ln.get("measured_net"), "source": src + toks, "cites": cites})
    keep.sort(key=lambda x: x["line_id"])
    import hashlib
    raw = (Path(run_dir) / "V3_0_22_BOQ_LINES.json").read_bytes()
    CAND.write_text(json.dumps({"source": "V3_0_22_BOQ_LINES.json (ARCH_TAKEOFF_V3.0.22 run, own)",
                                "lines_json_sha256": hashlib.sha256(raw).hexdigest(), "lines_total": len(lines),
                                "kept": len(keep), "lines": keep}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    c = json.loads(Path(census_json).read_text(encoding="utf-8"))
    rows = [{k: l[k] for k in ("text_id", "text", "code", "floor", "region_id", "room_id", "status", "cause")}
            for l in c["labels"]]
    CENSUS.write_text(json.dumps({"source": f"tools/label_census.py on {DXF} (sha256 ab54dd55..), "
                                            "method ARCH_TAKEOFF_V2.9", "summary": c["summary"], "labels": rows},
                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---- faces (T-071 records + this task's readings) ------------------------------------------------------------------
def _t071():
    out = {}
    for fr in json.loads(T071.read_text(encoding="utf-8")):
        for r in fr["records"]:
            out[r["text_id"]] = r
    return out


def faces():
    x = _t071()
    pool = x["AT19"]["candidates"]["5"]
    court = x["AT21"]["candidates"]["5"]
    roof = x["AT379"]["candidates"]["5"]
    void = x["AT225"]["candidates"]
    hole = court["holes"][0]

    def handles(c):
        h = {cl["from_line"] for cl in c.get("closures") or ()}
        h |= {m for cl in c.get("closures") or () for m in cl.get("meets_lines") or ()}
        h |= {ln for ho in c.get("holes") or () for ln in ho.get("lines") or ()}
        return sorted(h)

    return [
        {"face_id": "GF-POOL-WATER", "floor": "GF", "code": "POOL", "labels": sorted(pool["labels_in_face"]),
         "source": ["D2:200", "D2:202", "D2:203", "D2:205"], "area_m2": pool["A_net_m2"],
         "perimeter_lm": pool["A_perimeter_lm"]["own_layer_edge"],
         "corresponds": [{"element": "POOL-1", "face_m2": pool["A_net_m2"], "element_m2": WATER_M2,
                          "face_lm": pool["A_perimeter_lm"]["own_layer_edge"], "element_lm": WATER_LM,
                          "evidence": "layer-5 D outline (ARC 202 r 1550 90-270 + LINEs 203 / 205, 1550 to the "
                                      "boundary-wall face) = the structural POOL-1 water D of the candidate pool lines "
                                      "(inner 8.578838 m2)"}],
         "evidence": f"{DXF}: T-071 layer-5 face {pool['A_net_m2']} m2 / {pool['A_perimeter_lm']['own_layer_edge']} lm "
                     f"round AT19 / AT20 (bilingual pair); the layer-2 faces (1.113 / 1.066 m2) are the X of LINEs "
                     "2C3 / 2C4 over the water, not a space"},
        {"face_id": "GF-COURT", "floor": "GF", "code": "GARDEN",
         "labels": sorted(t for t in court["labels_in_face"] if t in ("AT21", "AT22", "AT39", "AT40")),
         "source": handles(court), "area_m2": court["A_net_m2"],
         "evidence": f"{DXF}: T-071 one open face inside the plot boundary walls, net {court['A_net_m2']} m2 = filled "
                     f"{court['A_filled_m2']} - pool hole {hole['area_m2']} m2 / {hole['perimeter_lm']} lm (the pool's "
                     "outer D cut at the boundary-wall face: hand 10.235563 / 12.097787)"},
        {"face_id": "2F-ROOF-1", "floor": "2F", "code": "ROOF", "labels": ["AT379", "AT385"], "source": handles(roof),
         "area_m2": roof["A_net_m2"],
         "evidence": f"{DXF}: T-071 one roof face (+9.70) holds AT379 and AT385, net {roof['A_net_m2']} m2 (2 open dome "
                     "skylights out, Q-29); closure D2:4793:0 is the line's own gap"},
        *[{"face_id": f"1F-ROOF-{t}", "floor": "1F", "code": "ROOF", "labels": [t], "source": handles(x[t]["candidates"]["5"]),
           "area_m2": x[t]["candidates"]["5"]["A_net_m2"],
           "evidence": f"{DXF}: T-071 roof face round {t} (1F plan), net {x[t]['candidates']['5']['A_net_m2']} m2"}
          for t in ("AT216", "AT220")],
        {"face_id": "1F-VOID-POOLCOURT", "floor": "1F", "code": "VOID", "labels": ["AT225"],
         "source": sorted(set(handles(void["2"])) | set(handles(void["5"]))), "area_m2": None,
         "evidence": f"{DXF}: 1F slab opening over the pool court; T-071 layer 2 {void['2']['A_net_m2']} / layer 5 "
                     f"{void['5']['A_net_m2']} m2 (ambiguous drawn faces), structural opening inside the B7 ring "
                     "inner faces 3.690 m2 (T-127, verifier 3.689)"},
    ]


def scopes():
    deck = POOL_COURT_FACE - _t071()["AT21"]["candidates"]["5"]["holes"][0]["area_m2"]
    pool_fin = WATER_M2 + WATER_LM * FIN_DEPTH
    na_wet = ("AT19 reads 'swimming pool' (compound phrase, ROOM_VOCAB_V2) and lies in the pool-water D face: no "
              "bathroom is drawn there, so no wet-room floor / wall tile, backing plaster, wet-area WP or ceiling exists")
    return {
        "GF-POOL-WATER": [
            {"scope": "pool shell concrete (walls + base)", "item_codes": ["STR.CONC.POOL"], "status": "BOUND",
             "evidence_status": "Checker-verified record (T-183 r2)"},
            {"scope": "pool tank membrane", "item_codes": ["WP.POOL_TANK", "FIN.WP.POOL"], "status": "MISSING",
             "quantity": 29.582355, "bound": [29.582355, 29.582355 + 1.349668], "unit": "m2",
             "evidence_status": "DRAWING-CONFIRMED (T-309 merged; held part 0 .. 1.349668)",
             "integration": "lane I FILL of T-336 FILL_T310_T336.csv (row T-310)"},
            {"scope": "pool protection screed", "item_codes": ["WP.POOL_TANK", "FIN.WP.POOL"], "status": "MISSING",
             "quantity": 1.524503, "bound": [1.524503, 1.524503 + 0.068072], "unit": "m3",
             "evidence_status": "DRAWING-CONFIRMED (T-309 merged)",
             "integration": "lane I FILL of T-336 FILL_T310_T336.csv (row T-310)"},
            {"scope": "pool water-face finish (floor + walls to the rim)", "item_codes": ["FIN.POOL.FINISH"],
             "status": "MISSING", "quantity": None, "bound": [_r(pool_fin), _r(pool_fin)], "unit": "m2",
             "evidence_status": "HELD: finish not specified (no Urban rule, no sheet names it); surface "
                                f"{WATER_M2:.6f} + {WATER_LM:.6f} x {FIN_DEPTH:.2f} = {pool_fin:.6f} m2 DRAWING-DERIVED",
             "integration": "owner / designer specification first (no line until a finish is named)"},
            {"scope": "floor area / floor tile", "item_codes": [], "status": "NOT_APPLICABLE",
             "evidence": "pool water is never a floor (OWNER_RULE_OUTDOOR_FLOORS; T-153 EXCLUDED)"},
            {"scope": "wet-room tile / backing / WP / ceiling", "item_codes": [], "status": "NOT_APPLICABLE",
             "evidence": na_wet},
        ],
        "GF-COURT": [
            {"scope": "west court open part: interlock", "item_codes": ["ARCH.SPACE", "FLOOR.OUTDOOR", "FIN.EXT.PAVING"],
             "status": "MISSING", "quantity": T157["open"], "unit": "m2",
             "evidence_status": "area DRAWING-CONFIRMED (T-157 merged); interlock ASSUMED — OWNER-APPROVED "
                                "(OWNER_RULE_OUTDOOR_FLOORS 23:20, owner choice, differs from render)",
             "integration": "new lane I row: outdoor floor lines"},
            {"scope": "covered porch at court level", "item_codes": ["ARCH.SPACE", "FLOOR.OUTDOOR", "FIN.EXT.PAVING"],
             "status": "MISSING", "quantity": T157["porch"], "unit": "m2",
             "evidence_status": "area DRAWING-CONFIRMED; material HELD (owner: wood / ceramic / marble)",
             "integration": "new lane I row: outdoor floor lines (material blank)"},
            {"scope": "entrance steps E1 treads (marble)", "item_codes": ["FIN.MARBLE.TREAD"], "status": "MISSING",
             "quantity": T157["e1"], "unit": "m2", "evidence_status": "DRAWING-CONFIRMED; marble by owner rule + "
                                                                       "UP-STAIR-001",
             "integration": "new lane I row: outdoor floor lines"},
            {"scope": "entrance steps E1 visible risers (marble)", "item_codes": ["FIN.MARBLE.RISER"],
             "status": "MISSING", "quantity": T157["riser"], "unit": "m2",
             "evidence_status": "DRAWING-CONFIRMED (5 x 0.140 x 2.80; FLAG riser 0.170 > 0.16, S-1 check only)",
             "integration": "new lane I row: outdoor floor lines"},
            {"scope": "entrance top landing (marble)", "item_codes": ["FIN.MARBLE.LANDING"], "status": "MISSING",
             "quantity": T157["landing"], "unit": "m2", "evidence_status": "DRAWING-CONFIRMED (printed 140 x 370)",
             "integration": "new lane I row: outdoor floor lines"},
            {"scope": "north side walk: porcelain / ceramic", "item_codes": ["ARCH.SPACE", "FLOOR.OUTDOOR", "FIN.EXT.PAVING"],
             "status": "MISSING", "quantity": T157["walk"], "unit": "m2",
             "evidence_status": "DRAWING-CONFIRMED (Checker 21.021); owner manual method 1.50 x 15.97 = 23.955 kept "
                                "beside (RULE_DIFFERENCE); porcelain ASSUMED — OWNER-APPROVED (sides rule)",
             "integration": "new lane I row: outdoor floor lines"},
            {"scope": "pool deck", "item_codes": ["ARCH.SPACE", "FLOOR.OUTDOOR", "FIN.EXT.PAVING"], "status": "MISSING",
             "quantity": _r(deck, 4), "unit": "m2",
             "evidence_status": f"DRAWING-DERIVED, CORRECTED: pool court {POOL_COURT_FACE} - drawn pool D cut at the "
                                f"boundary {_t071()['AT21']['candidates']['5']['holes'][0]['area_m2']} = {deck:.4f} "
                                f"(T-157 {T157['deck_old']} took a circle 9.4022); material HELD (owner)",
             "integration": "new lane I row: outdoor floor lines (material blank)"},
        ],
        "2F-ROOF-1": [
            {"scope": "roof membrane", "item_codes": ["FIN.WP.ROOF"], "status": "BOUND",
             "evidence_status": "SOURCE_DERIVED (owner Q-24 / Q-25 / Q-29)"},
            {"scope": "roof membrane upturn", "item_codes": ["FIN.WP.ROOF_UPTURN"], "status": "BOUND",
             "evidence_status": "SOURCE_DERIVED"},
        ],
        **{f"1F-ROOF-{t}": [{"scope": "roof membrane", "item_codes": ["FIN.WP.ROOF"], "status": "BOUND",
                              "evidence_status": "SOURCE_DERIVED (owner Q-24 / Q-25)"},
                             {"scope": "roof membrane upturn", "item_codes": ["FIN.WP.ROOF_UPTURN"], "status": "BOUND",
                              "evidence_status": "SOURCE_DERIVED"}] for t in ("AT216", "AT220")},
        "1F-VOID-POOLCOURT": [
            {"scope": "floor / finishes of the opening", "item_codes": [], "status": "NOT_APPLICABLE",
             "evidence": "slab opening open to below and to the sky (T-127 / T-153 EXCLUDED: no floor, not 0); its "
                         "deduction lives in the GF pool-court soffit line SOFFIT:GF:PL-03 (16.525 gross - 3.690 = "
                         "12.834 = the line, exact); it is NOT the 16.005 living-void deduction (AT215, 1F-R78C367)"},
        ],
    }


def build():
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    from engine.source import room_vocab as RV
    no_room = [l for l in cen["labels"] if l.get("cause") == "NO_ROOM"]
    res = B.bind(no_room, faces(), cand["lines"], scopes(), word=RV.room_word)
    return cen, cand, res


def _csv(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else v)
                    for k, v in r.items()})
    return b.getvalue()


def render():
    cen, cand, res = build()
    s = cen["summary"]
    summ = {"census": {"labels": s["labels"], **s["by_status"], "unread_shx": s["unread_shx"], "method": s.get("method")},
            "candidate": {"lines_json_sha256": cand["lines_json_sha256"], "lines_total": cand["lines_total"]},
            "binding": res["summary"], "target": list(TARGET),
            "rows": {r["text_id"]: {"binding": r["binding"], "face": r["face_id"], "lines": r["lines"],
                                    "duplicate_of": r["duplicate_of"], "retype": r["retype"]} for r in res["rows"]}}
    return {"binding": _csv(res["rows"], ["text_id", "floor", "census_code", "code", "retype", "face_id", "binding",
                                          "duplicate_of", "lines", "scopes", "elements", "elements_refused"]),
            "scopes": _csv(res["scopes"], ["face_id", "scope", "status", "lines", "refused", "quantity", "bound",
                                           "unit", "evidence_status", "evidence", "integration", "note"]),
            "summary": json.dumps(summ, ensure_ascii=False, indent=1, sort_keys=True) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract")
    ap.add_argument("--census")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        extract(a.extract, a.census)
    out = render()
    if a.write:
        for k, p in OUT.items():
            p.write_text(out[k], encoding="utf-8")
    if a.check:
        bad = [k for k, p in OUT.items() if p.read_text(encoding="utf-8") != out[k]]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    print(out["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
