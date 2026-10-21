"""Round 5 post-freeze architectural benchmark comparison (FINDING ONLY).

Runs only after the Round-5 registers are frozen: it first re-hashes every
register and refuses unless each hash equals INDEX.json. Then it reads the
normalised human benchmark records (Phase B1 register, already parsed from the
workbooks; the workbooks themselves are not opened here) and classifies each
comparison as one of

    AGREES / ENGINE_HIGH / ENGINE_LOW / DIFFERENT_SCOPE / DIFFERENT_METHOD /
    HUMAN_FORMULA_ERROR / UNRESOLVED

Nothing here feeds back into the engine. Any engine change after reading this
file starts a new controlled round.

usage: python3 research/alsenan_arch_truth_05/post_freeze_arch_benchmark.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).resolve().parent / "registers"
BENCH = ROOT / "tests" / "alsenan" / "registers_b1" / "BENCHMARK_NORMALISED.json"
QA = ROOT / "tests" / "alsenan" / "registers_b1" / "MANUAL_BOQ_QA.json"
OUT = Path(__file__).resolve().parent / "POST_FREEZE_ARCH_BENCHMARK.json"

AGREE_PCT = 5.0
AGREE_ABS_M2 = 0.25
MATCH_MAX_REL = 0.25   # an area assignment further apart than this is no match (kept UNRESOLVED, region left as engine-only)
CLASSES = ("AGREES", "ENGINE_HIGH", "ENGINE_LOW", "DIFFERENT_SCOPE",
           "DIFFERENT_METHOD", "HUMAN_FORMULA_ERROR", "UNRESOLVED")
BENCH_FLOOR = {"GF": "GF", "1F": "1F", "ROOF": "2F"}   # the workbook calls the 2F annex "ROOF"


def verify_freeze():
    idx_text = (REG / "INDEX.json").read_text()
    idx = json.loads(idx_text)
    if not idx.get("frozen_before_benchmark") or not idx.get("built_twice_identical"):
        sys.exit("refuse: INDEX does not record a frozen, twice-identical build")
    bad = [k for k, h in idx["files"].items()
           if hashlib.sha256((REG / f"{k}.json").read_text().encode()).hexdigest() != h]
    if bad:
        sys.exit(f"refuse: register hash mismatch {bad}")
    return hashlib.sha256(idx_text.encode()).hexdigest(), len(idx["files"])


def g(name):
    return json.loads((REG / f"{name}.json").read_text())


def pct(engine, bench):
    return round(100.0 * (engine - bench) / bench, 1) if bench else None


def numeric_class(engine, bench, abs_tol=0.0):
    if engine is None:
        return "UNRESOLVED"
    d = engine - bench
    if abs(d) <= max(abs_tol, AGREE_PCT / 100.0 * abs(bench)):
        return "AGREES"
    return "ENGINE_HIGH" if d > 0 else "ENGINE_LOW"


def engine_totals():
    ff, sk, wp = g("FLOOR_FINISH_REGISTER_V2"), g("SKIRTING_PATH_REGISTER_V3"), g("WATERPROOFING_REGISTER_V2")
    wt, pp, bw = g("WALL_TILE_REGISTER_V2"), g("PLASTER_PAINT_REGISTER_V2"), g("BLOCKWORK_AREA_REGISTER_V2")
    ce, st = g("CEILING_AREA_REGISTER_V2"), g("STAIR_ARCHITECTURAL_REGISTER")
    s = lambda d: round(sum(v for v in d.values() if isinstance(v, (int, float))), 3)
    by_fin = ff["internal_m2_by_finish_state"]
    internal = round(sum(s(v) for v in by_fin.values()), 3)
    stair = s(by_fin.get("MARBLE_STAIR_FINISH", {}))
    bw_cls = {"MASONRY_150": 0.0, "MASONRY_200": 0.0}
    for fl in bw["by_floor"].values():
        for k, v in fl.items():
            c, state = k.split("|")
            if state != "BLOCKED_LENGTH_m":
                bw_cls[c] = round(bw_cls[c] + v, 3)
    around = round(sum(r["net_m2"] for r in bw["over_under_openings"] if r["net_m2"] is not None), 3)
    ceil = {}
    for fl in ce["by_floor"].values():
        for k, v in fl.items():
            ceil[k] = round(ceil.get(k, 0.0) + v, 3)
    fac = pp["external_facade"]["floors"] if isinstance(pp["external_facade"], dict) else pp["external_facade"]
    return {
        "floor_internal_m2": internal,
        "floor_internal_ex_stair_m2": round(internal - stair, 3),
        "floor_by_finish": {k: s(v) for k, v in by_fin.items()},
        "skirting_included_m": s({k: v for k, v in sk["included_m"].items() if k != "BLOCKED"}),
        "skirting_blocked_region_m": sk["included_m"].get("BLOCKED", 0.0),
        "skirting_blocked_glazing_m": sk["blocked_m_total"],
        "wp_floor_m2": s(wp["floor_membrane_m2"]),
        "wp_upturn_path_m": s(wp["upturn_path_m"]),
        "wall_tile_net_m2": s(wt["net_m2"]),
        "plaster_net_m2": s(pp["plaster_net_m2"]),
        "paint_net_m2": s(pp["paint_net_m2"]),
        "blockwork_m2_by_class": bw_cls,
        "blockwork_m2": round(sum(bw_cls.values()), 3),
        "blockwork_around_openings_m2": around,
        "ceiling_m2_by_state": ceil,
        "ceiling_m2": round(sum(v for k, v in ceil.items() if k != "NOT_IN_SCOPE"), 3),
        "facade_net_m2": round(sum((f.get("net_external_face_m2") or f.get("gross_external_face_m2") or 0.0)
                                   for f in fac), 3),
        "handrail_m": st["handrail_m"],
        "stair_skirting_m": st["stair_skirting_m"],
    }


def bench_records():
    recs = json.loads(BENCH.read_text())["records"]
    cover = {(r["trade"], r["subtrade"]): r for r in recs if r["row_kind"] == "COVER_TOTAL"}
    return recs, cover


def total_rows(E, cover):
    rows = []

    def add(key, engine, cls, why, engine_basis):
        r = cover[key]
        rows.append({"benchmark_id": r["id"], "benchmark": f"{key[0]} / {key[1]}", "benchmark_qty": round(r["qty"], 3),
                     "benchmark_formula": r.get("formula"), "engine_qty": engine, "engine_basis": engine_basis,
                     "diff_pct": pct(engine, r["qty"]) if isinstance(engine, (int, float)) else None,
                     "classification": cls, "why": why})

    b = cover[("FLOOR", "ALL")]["qty"]
    add(("FLOOR", "ALL"), E["floor_internal_ex_stair_m2"], "DIFFERENT_SCOPE",
        "benchmark = named dry rooms + wet rooms only; engine internal (stair excluded) also carries the GF-Z04 "
        "mixed zone as one 121.5 m2 region, the unlabelled 2F region (18.6), recovered unlabelled GF regions and "
        f"UNASSIGNED wall-band pieces; raw delta {pct(E['floor_internal_ex_stair_m2'], b)} %. Room-level rows below.",
        "FLOOR_FINISH_REGISTER_V2 internal (VC + PROV) minus MARBLE_STAIR_FINISH")
    for sub, why in (("POOL", "pool is NOT_IN_SCOPE for the internal floor engine (recovered as EXTERNAL 8.57 m2 region only)"),
                     ("EXTERNAL_YARD", "external yard is not measured in Round 5")):
        add(("FLOOR", sub), None, "DIFFERENT_SCOPE", why, "not measured")
    add(("WATERPROOFING", "WET_ROOM:FLOOR"), E["wp_floor_m2"],
        numeric_class(E["wp_floor_m2"], cover[("WATERPROOFING", "WET_ROOM:FLOOR")]["qty"]),
        "wet + service floors (kitchen, pantry, laundry) incl. the PROVISIONAL recovered 1F BATH",
        "WATERPROOFING_REGISTER_V2 floor membrane VC + PROV")
    up = cover[("WATERPROOFING", "WET_ROOM:UPTURN")]["qty"]
    add(("WATERPROOFING", "WET_ROOM:UPTURN"), E["wp_upturn_path_m"], numeric_class(E["wp_upturn_path_m"], up),
        "compared as path length: the human row is perimeter x 1.0 m reported in m.t (QA UNIT_AMBIGUITY, "
        "numerically the perimeter); engine path counts door crossings (not deducted), upturn 0.15 m",
        "WATERPROOFING_REGISTER_V2 upturn path VC + PROV")
    for sub in ("ROOF:FLOOR", "ROOF:UPTURN"):
        add(("WATERPROOFING", sub), None, "DIFFERENT_SCOPE", "roof waterproofing is a separate method not re-measured in Round 5",
            "not measured")
    sk_b = cover[("SKIRTING", "ALL")]["qty"]
    env = round(E["skirting_included_m"] + E["skirting_blocked_region_m"], 3)
    add(("SKIRTING", "ALL"), E["skirting_included_m"], "UNRESOLVED",
        f"engine released path {E['skirting_included_m']} m is a lower bound (ENGINE_LOW, {pct(E['skirting_included_m'], sk_b)} %); "
        f"released + region-blocked = {env} m ({pct(env, sk_b)} %), + glazing-blocked {E['skirting_blocked_glazing_m']} m. "
        "The human figure equals the dry cornice figure (282.85) - one perimeter reused for two trades.",
        "SKIRTING_PATH_REGISTER_V3 VC + LOWER_BOUND")
    add(("SKIRTING", "EXTERNAL_YARD"), None, "DIFFERENT_SCOPE", "yard not measured", "not measured")
    add(("SKIRTING", "STAIR"), None, "UNRESOLVED", "stair skirting BLOCKED in STAIR_ARCHITECTURAL_REGISTER", "BLOCKED")
    wt_b = cover[("WALL_TILE", "WET_ROOMS")]["qty"]
    add(("WALL_TILE", "WET_ROOMS"), E["wall_tile_net_m2"], "DIFFERENT_METHOD",
        f"human cover = B17-D17 and equals the plaster sheet subtotal 'bathrooms and kitchens' (spatter coat, "
        f"433.83) - a backing-coat area, not a tile area; engine = full-height tile to the finished ceiling, "
        f"openings deducted, reveals added (direction ENGINE_LOW, {pct(E['wall_tile_net_m2'], wt_b)} %)",
        "WALL_TILE_REGISTER_V2 net (PROVISIONAL)")
    add(("WALL_TILE", "POOL"), None, "DIFFERENT_SCOPE", "pool NOT_IN_SCOPE", "not measured")
    cb = cover[("CEILING", "GYPSUM:DRY")]["qty"] + cover[("CEILING", "GYPSUM:WET")]["qty"]
    rows.append({"benchmark_id": "FIN:الغلاف:34+36", "benchmark": "CEILING / GYPSUM DRY + WET", "benchmark_qty": round(cb, 3),
                 "benchmark_formula": "=B34 (+) =B36", "engine_qty": E["ceiling_m2"],
                 "engine_basis": "CEILING_AREA_REGISTER_V2 VC + PROV (void, stair well, shaft excluded)",
                 "diff_pct": pct(E["ceiling_m2"], cb), "classification": numeric_class(E["ceiling_m2"], cb),
                 "why": "human gypsum dry + wet equals the human floor total 409.58 (floor areas reused); "
                        "engine ceiling is its own register; agreement is numeric, scope differs as for FLOOR"})
    rows.append({"benchmark_id": "FIN:الغلاف:35+37", "benchmark": "CEILING / CORNICE DRY + WET",
                 "benchmark_qty": round(cover[("CEILING", "CORNICE:DRY")]["qty"] + cover[("CEILING", "CORNICE:WET")]["qty"], 3),
                 "benchmark_formula": "=B35 (+) =B37", "engine_qty": None, "engine_basis": "not a Round-5 trade",
                 "diff_pct": None, "classification": "DIFFERENT_SCOPE",
                 "why": "cornice not measured in Round 5; note human cornice dry = skirting 282.85 and cornice wet = WP upturn 144.61"})
    add(("RAILING", "INTERNAL"), None, "UNRESOLVED", "handrail BLOCKED (no railing source geometry admitted in Round 5)", "BLOCKED")
    bwc = E["blockwork_m2_by_class"]
    add(("BLOCKWORK", "ALL"), E["blockwork_m2"], "ENGINE_LOW",
        f"engine net masonry (one face x height to beam/slab soffit) {E['blockwork_m2']} m2 + around openings "
        f"{E['blockwork_around_openings_m2']} m2 (PROV). Part DIFFERENT_SCOPE: engine excludes boundary walls, "
        "parapets and roof structures outside the floor plate; the 150 mm row below is the large gap.",
        "BLOCKWORK_AREA_REGISTER_V2 (PROVISIONAL)")
    ext20 = cover[("BLOCKWORK", "EXTERNAL")]["qty"] + cover[("BLOCKWORK", "INTERNAL_200")]["qty"]
    rows.append({"benchmark_id": "BLK:الغلاف:15+17", "benchmark": "BLOCKWORK / EXTERNAL + 20 cm", "benchmark_qty": round(ext20, 3),
                 "benchmark_formula": "=B15 (+) =B17-D17", "engine_qty": bwc["MASONRY_200"], "engine_basis": "MASONRY_200 net",
                 "diff_pct": pct(bwc["MASONRY_200"], ext20), "classification": numeric_class(bwc["MASONRY_200"], ext20),
                 "why": "human splits external / 20 cm; engine classifies by measured band width only (external 20 cm by convention)"})
    b15 = cover[("BLOCKWORK", "INTERNAL_150")]["qty"]
    rows.append({"benchmark_id": "BLK:الغلاف:16", "benchmark": "BLOCKWORK / 15 cm", "benchmark_qty": round(b15, 3),
                 "benchmark_formula": "=B16", "engine_qty": bwc["MASONRY_150"], "engine_basis": "MASONRY_150 net",
                 "diff_pct": pct(bwc["MASONRY_150"], b15), "classification": numeric_class(bwc["MASONRY_150"], b15),
                 "why": "engine 150 mm centreline 82.9 m vs roughly 150-160 m implied by the human area; candidate causes "
                        "(not tested): partitions on non-wall layers, 23.55 m ambiguous width, both faces vs one face basis"})
    for key, eng, name in ((("PLASTER", "INTERNAL_WALL"), E["plaster_net_m2"], "plaster"),
                           (("PAINT", "INTERNAL_WALL"), E["paint_net_m2"], "paint")):
        add(key, eng, numeric_class(eng, cover[key]["qty"]),
            f"engine {name} excludes wet full-tile walls (NIS) and uses the Urban height method; the human sheet "
            "subtotal path (1209.385 / 1249.375 less 116.495 deductions) is not reproducible from the cover formula alone",
            "PLASTER_PAINT_REGISTER_V2 net")
    add(("PLASTER", "EXTERNAL"), E["facade_net_m2"], "DIFFERENT_SCOPE",
        "engine facade = registered floor-plate envelope only (PROVISIONAL); boundary / party walls, parapets, plinth, "
        "roof annex and finish system are not in Round 5", "PLASTER_PAINT_REGISTER_V2 external_facade")
    return rows


DRY_NAME = {  # benchmark English label -> engine label (one-to-one, by name)
    ("GF", "reception + dining"): "RECEPTION", ("GF", "master bedroom"): "MASTER BED ROOM",
    ("GF", "diwaniya"): "DEWANEYA", ("GF", "driver's room"): "DRIVER", ("1F", "living"): "LIVING AREA",
    ("2F", "maid's room"): "MAID R.",
}


def room_rows(recs):
    from scipy.optimize import linear_sum_assignment
    regions = g("TRADE_REGION_REGISTER_V2")["rows"]
    out = []
    used = set()
    bench = [r for r in recs if r["trade"] == "FLOOR" and r["row_kind"] == "DETAIL" and r["subtrade"] in ("DRY_ROOM", "WET_ROOM")]
    for r in bench:
        r["_fl"] = BENCH_FLOOR.get(r["floor"], r["floor"])
    # 1. dry rooms matched by name
    for r in [r for r in bench if r["subtrade"] == "DRY_ROOM"]:
        lab = DRY_NAME.get((r["_fl"], r["label_en"]))
        cand = [e for e in regions if e["floor"] == r["_fl"] and lab and lab in e["labels"] and e["region_id"] not in used]
        if r["label_en"].startswith("bedroom"):
            continue
        if not cand:
            out.append(_room(r, None, "UNRESOLVED", "room name not present as an engine label (likely inside a mixed / unassigned region)"))
            continue
        e = cand[0]
        used.add(e["region_id"])
        if e["class"] == "MIXED_UNRESOLVED":
            out.append(_room(r, e, "DIFFERENT_SCOPE", f"engine region is MIXED_UNRESOLVED {e['labels']} (wash lobby inside; not split)"))
        elif r["_fl"] == "1F" and lab == "LIVING AREA":
            out.append(_room(r, e, "DIFFERENT_SCOPE", "engine LIVING AREA includes the landing / corridor around the void (void excluded)"))
        else:
            out.append(_room(r, e, numeric_class(e["area_m2"], r["qty"], AGREE_ABS_M2), "matched by room name"))
    # 2. 1F bedrooms and wet rooms: optimal one-to-one by area within floor + family (labels are generic)
    groups = {}
    for r in bench:
        if r["subtrade"] == "WET_ROOM":
            groups.setdefault((r["_fl"], "WET"), []).append(r)
        elif r["label_en"].startswith("bedroom"):
            groups.setdefault((r["_fl"], "BED"), []).append(r)
    for (fl, fam), brs in sorted(groups.items()):
        if fam == "BED":
            cands = [e for e in regions if e["floor"] == fl and "MASTER BED ROOM" in e["labels"] and e["region_id"] not in used]
        else:
            cands = [e for e in regions if e["floor"] == fl and e["class"] in ("WET", "SERVICE") and e["region_id"] not in used]
        if cands:
            cost = [[abs(e["area_m2"] - b["qty"]) for e in cands] for b in brs]
            ri, ci = linear_sum_assignment(cost)
            pair = dict(zip(ri.tolist(), ci.tolist()))
        else:
            pair = {}
        for i, b in enumerate(brs):
            if i in pair and abs(cands[pair[i]]["area_m2"] - b["qty"]) <= MATCH_MAX_REL * b["qty"]:
                e = cands[pair[i]]
                used.add(e["region_id"])
                out.append(_room(b, e, numeric_class(e["area_m2"], b["qty"], AGREE_ABS_M2),
                                 "one-to-one area assignment within floor + family (generic labels)"))
            else:
                out.append(_room(b, None, "UNRESOLVED", "no engine region of this family on this floor within the match window"))
    for e in regions:
        if e["region_id"] in used or e["class"] in ("SHAFT", "VOID", "COLUMN", "EXTERNAL", "STAIR") or e["area_m2"] < 1.0:
            continue
        out.append({"benchmark_id": None, "floor": e["floor"], "benchmark_label": None, "benchmark_qty": None,
                    "engine_region": e["region_id"], "engine_labels": e["labels"], "engine_class": e["class"],
                    "engine_m2": round(e["area_m2"], 3), "diff_pct": None, "classification": "DIFFERENT_SCOPE",
                    "why": "engine region with no human row"})
    return out


def _room(b, e, cls, why):
    return {"benchmark_id": b["id"], "floor": b["_fl"], "benchmark_label": b["label_en"], "benchmark_qty": b["qty"],
            "engine_region": e["region_id"] if e else None, "engine_labels": e["labels"] if e else None,
            "engine_class": e["class"] if e else None, "engine_m2": round(e["area_m2"], 3) if e else None,
            "diff_pct": pct(e["area_m2"], b["qty"]) if e else None, "classification": cls, "why": why}


def human_lines():
    qa = json.loads(QA.read_text())["findings"]
    rows = []
    for f in qa:
        if f.get("file") != "FIN" and f.get("file") != "BLK":
            continue
        if f["check"] == "TOTAL_CONTAINS_ANOTHER_REPORTED_TOTAL":
            rows.append({"source": f"{f['file']}:{f['sheet']}:{f['cell']}", "classification": "HUMAN_FORMULA_ERROR",
                         "finding": f"total {f['formula']} contains {f['contains']} ({f['contained_value']}) which is also "
                                    f"reported separately on the cover ({', '.join(f['both_reported_on_cover'])}) - double count candidate"})
        elif f["check"] == "UNIT_AMBIGUITY":
            rows.append({"source": f"{f['file']}:{f['label']}", "classification": "DIFFERENT_METHOD",
                         "finding": f["detail"]})
    rows += [
        {"source": "FIN cover rows 16 / 35", "classification": "DIFFERENT_METHOD",
         "finding": "skirting 282.85 lm = dry cornice 282.85 lm: one perimeter used for two trades"},
        {"source": "FIN cover rows 27 / 36", "classification": "DIFFERENT_METHOD",
         "finding": "wet gypsum ceiling 72.01 = wet-room floor waterproofing 72.01 = wet floor area"},
        {"source": "FIN cover rows 28 / 37", "classification": "DIFFERENT_METHOD",
         "finding": "wet cornice 144.61 = WP upturn 144.61"},
        {"source": "FIN cover row 17 / PLS sheet subtotal 'bathrooms and kitchens'", "classification": "DIFFERENT_METHOD",
         "finding": "wall tile 433.83 = the plaster spatter-coat subtotal; a backing area, not a tile area"},
    ]
    return rows


def main():
    frozen_sha, n = verify_freeze()
    E = engine_totals()
    recs, cover = bench_records()
    rows = total_rows(E, cover)
    rooms = room_rows(recs)
    for r in rows + rooms:
        assert r["classification"] in CLASSES, r
    count = lambda rs: {c: sum(1 for r in rs if r["classification"] == c) for c in CLASSES}
    out = {
        "SCHEMA": "URBAN_ALSENAN_ARCH_R5_POST_FREEZE_BENCHMARK",
        "use": "FINDING_ONLY",
        "frozen_index_sha256": frozen_sha,
        "registers_hash_verified": n,
        "agree_rule": f"|engine - human| <= {AGREE_PCT} % (rooms: or <= {AGREE_ABS_M2} m2)",
        "benchmark_source": "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json (records parsed in Phase B1)",
        "engine_totals": E,
        "rows": rows,
        "room_rows": rooms,
        "human_lines": human_lines(),
        "counts": {"rows": count(rows), "room_rows": count(rooms)},
        "rule": "post-freeze finding only; no engine code or register changed after this comparison",
        "comparison_script_note": "first run printed duplicate rows for unnamed dry rooms and forced a PANTRY 9.54 vs "
                                  "washroom 4.73 pairing; the reporting script (not the engine) was corrected: "
                                  "duplicates removed, area pairing capped at 25 %",
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(out["counts"]))
    for r in rows:
        print(f"{r['benchmark']:<34} human {r['benchmark_qty']:>9} engine {str(r['engine_qty']):>9} {str(r['diff_pct']):>7}%  {r['classification']}")
    for r in rooms:
        print(f"  {r['floor']} {str(r['benchmark_label']):<20} {str(r['benchmark_qty']):>7} | {str(r['engine_labels']):<40} {str(r['engine_m2']):>8} {str(r['diff_pct']):>6}% {r['classification']}")


if __name__ == "__main__":
    main()
