"""T-686 builder: plaster / paint round 3 on the development villa (R-T686-1 .. -4). Research only: reads merged,
sha256-pinned research inputs (no coordinates, no client data); writes out/ only; wires nothing.

    python3 -I research/agents_t686/t686_alsenan.py [--check]

Inputs: research/agents_t677/out/LINE_INDEX_V3_0_66.json (candidate of record), research/agents_t680/out (round-2
state of the code totals), research/agents_t678/out/T678_LEDGER.json (annex slab-top lower bound, R-T678-2, Checker
MERGED f8515d4b), research/agents_t312 (wet-room contours and openings, T-250 face ledger), research/agents_t128
ROOMS_T128_R3.csv + research/agents_t292 OPENING_DEDUCTIONS_T292.csv (dry annex rooms), research/agents_t676 (census
causes, coat-material rule R-T676-3).
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t686_rules as R  # noqa: E402

CAND = ROOT / "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
T680 = ROOT / "research/agents_t680/out/T680_SHAFT_ROUND2.json"
T678 = ROOT / "research/agents_t678/out/T678_LEDGER.json"
T676 = ROOT / "research/agents_t676/out/T676_PLASTER_PAINT_CENSUS.json"
T312_ROOMS = ROOT / "research/agents_t312/ROOM_CLOSURE_T312.csv"
T312_OPS = ROOT / "research/agents_t312/OPENINGS_T312.csv"
T128_ROOMS = ROOT / "research/agents_t128/ROOMS_T128_R3.csv"
T292_OPS = ROOT / "research/agents_t292/OPENING_DEDUCTIONS_T292.csv"
OUT = HERE / "out"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R676 = _load("t676_rules", ROOT / "research/agents_t676/t676_rules.py")

D = R.D
# ---- datum terms (sources named; no value invented) -----------------------------------------------------------
ANNEX = {
    "s_hi": ("4.30", "printed annex roof mark +4.30 (section B-B, T-321 ROOF-430): a slab top never lies above its "
                     "finished roof; Q-54 B: +4.30 is NOT taken as the slab top, only as the ceiling of the bound"),
    "ffl": ("0.30", "annex FFL +0.30 printed in the four annex rooms (sheet 03; Q-54 problem statement)"),
    "slab": ("0.16", "structural general note 16 cm unless stated (owner Q-14); the GFRS annex part prints no "
                     "thickness (T-678 own read)"),
    "beam": ("0.60", "owner manual method G1 (Q-43 A: floor height - beam - ceiling 15 cm; OWNER_RECONCILIATION "
                     "2026-10-20)"),
    "ceiling": ("0.15", "owner manual method G1 (Q-43 A / Q-48 A)"),
}
STAIR_CORE = {
    "g1_abs": ("4.65", "GF main G1 ceiling: FFL +1.00 + 3.65 (G1 = 4.50 - 0.60 - 0.15 - 0.10, Q-43 A / Q-48 A); an "
                       "absolute level under the 1F slab, independent of the room's own floor"),
    "ffl_options": [("0.30", "lobby level +0.30 (T-088 / T-173 C-SH-2 reading 1)"),
                    ("1.00", "main GF level +1.00 (T-088 / T-173 C-SH-2 reading 2)")],
}
LEVELLING_RENDER = ("0.015", "MINIMUM")  # T-676 thickness_from_t489 (KSE: render not less than 1.5 cm)

PLASTER_WET = {  # room -> line id, element (wet rooms: FIN.PLASTER = the tile-backing levelling render)
    "GF-02": "L-2211463bba5eeb2e4282", "GF-03": "L-f43782d52f32b53a6f1e", "GF-05": "L-f179fc08a266294ad4a4",
    "GF-06": "L-595181aa140e7efb2ac7", "GF-10": "L-3f7fb1b37e68e6d6c7b7", "GF-11": "L-a636dabcd4bc7e59169a"}
WALL_TILE = {"GF-02": "L-d0858b30e0ea869bd047", "GF-03": "L-96d9839bd3bca4c08a67", "GF-05": "L-88c11c5d8dc1dfd7c27e",
             "GF-06": "L-c330b8dc47261d5ada7e", "GF-10": "L-1341e0410a469089c3be", "GF-11": "L-de4088e7012e655bb071"}
PAINT_DRY = {"GF-01": "L-cdf7f5cd2789b67004f1", "GF-04": "L-d7d6d2f765489a95c408"}
ANNEX_ROOMS = ("GF-02", "GF-03", "GF-05", "GF-06")
STAIR_ROOMS = ("GF-10", "GF-11")
REVEALS = {
    "L-3e19506bd9e093dfb7be": {"id": "A-GF-01", "t": "0.150", "w": "1.000", "zone": "annex",
                               "datum": "arch A-GF-01 spring and rise (crown) printed on no sheet (D-45); plan width "
                                        "1.000 / wall 0.150 DRAWING-CONFIRMED (T-648)"},
    "L-64cb94b4b8dc2cb17608": {"id": "A-1F-01", "t": "0.150", "w": "1.000", "zone": "1F", "S": "3.99",
                               "datum": "arch A-1F-01 spring and rise printed on no sheet (D-45); plan 1.000 x 0.150 "
                                        "DRAWING-CONFIRMED (T-676 own read)"},
    "L-e70e7e48b4c15b4f5a21": {"id": "D-GF-15", "datum": "gate D-GF-15 width and wall thickness not established "
                                                         "(T-313 UNRESOLVED; D-53 entrance family) and no head printed"},
}
F_T680_1 = [  # W25 (1F stair window): T-201 DWF vector vs section A-A raster (T-680 F-T680-1)
    {"id": "W25 SW elevation (DWF vector, T-201, Checker MERGED 5dade783)", "kind": "VECTOR", "sill": "5.50",
     "head": "7.00", "tol": "0.013"},
    {"id": "W25 section A-A (raster 1:100, read by T-680, never scaled into a quantity)", "kind": "RASTER",
     "sill": "5.60", "head": "7.36"},
]
W25_WIDTH = "1.00"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_op(r, size_key="merged_size", src_key="merged_source"):
    ms, src = r[size_key], r[src_key] or "merged ledger"
    op = {"id": r["opening_id"], "source": src, "exists": True}
    m = re.match(r"w ([0-9.]+) sill ([0-9.]+) head ([0-9.]+)$", ms)
    if m:
        op.update(width=m.group(1), sill=m.group(2), head=m.group(3))
        if "Q-55 C" in src:
            op["status"] = "ASSUMED - OWNER-APPROVED (Q-55 C door head 2.20)"
        return op
    m = re.match(r"w ([0-9.]+) h HELD(?: \(cap ([0-9.]+) m2\))?$", ms)
    if m:
        op["width"] = m.group(1)
        if "h 2.20 DRAWING-CONFIRMED" in src:
            op["height"] = "2.20"  # T-207 closure: hole height drawn, sill HELD
        elif m.group(2) is not None and Decimal(m.group(2)) < Decimal("4"):
            op["cap_h"] = str(Decimal(m.group(2)) / Decimal(m.group(1)))
        return op
    raise R.RuleError(f"opening {r['opening_id']}: size {ms!r} not parsed")


def build():
    cand = json.loads(CAND.read_text())
    idx = {l["line_id"]: l for l in cand["lines"]}
    t680 = json.loads(T680.read_text())
    t678 = json.loads(T678.read_text())
    t676 = {e["line_id"]: e for e in json.loads(T676.read_text())["entries"]}

    # 0. restate the counts on V3.0.66 (own filter) and the round-2 state
    census = {}
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        H = [l for l in cand["lines"] if l["item_code"] == code and l["class"] == "HELD"]
        b = [l for l in H if l["held_low"] is not None]
        census[code] = {"held": len(H), "bounded": len(b), "blank": len(H) - len(b),
                        "low": R.S(sum((D(l["held_low"]) for l in b), Decimal(0))),
                        "high": R.S(sum((D(l["held_high"]) for l in b), Decimal(0)))}
    r2 = {c: t680["code_totals_m2"][c]["after_t680_and_t676_op009"] for c in ("FIN.PLASTER", "FIN.PAINT")}
    r2_bounded_ids = {l["line_id"] for l in t680["lines"] if l["held_low"] is not None}
    blank_v366 = sorted(l["line_id"] for l in cand["lines"]
                        if l["item_code"] in ("FIN.PLASTER", "FIN.PAINT") and l["class"] == "HELD"
                        and l["held_low"] is None and l["line_id"] not in r2_bounded_ids)
    targets = set(PLASTER_WET.values()) | set(PAINT_DRY.values()) | set(REVEALS)
    if set(blank_v366) != targets:
        raise R.RuleError(f"blank set after round 2 differs from the targets: {sorted(set(blank_v366) ^ targets)}")
    for room, lid in WALL_TILE.items():  # room <-> line binding through the room's own wall-tile line
        if idx[lid]["element_id"].split(":")[0] != idx[PLASTER_WET[room]]["element_id"].split(":")[0]:
            raise R.RuleError(f"{room}: wall-tile and plaster lines name different rooms")

    # 1. annex datum bound (R-T686-1)
    sb = t678["annex_slab_top"]
    if sb["rule"] != "R-T678-2" or sb["finished_ceiling"] != ANNEX["s_hi"][0]:
        raise R.RuleError("T-678 annex record changed")
    s_lo = (sb["s_lo"], f"R-T678-2 (Checker MERGED f8515d4b): {sb['governing']} drawn head +2.80 - tol 0.006 + "
                        "CB6 0.75 under one annex plane")
    fh = R.finish_heights(s_lo, ANNEX["s_hi"], ANNEX["ffl"], ANNEX["slab"], ANNEX["beam"], ANNEX["ceiling"])
    Hs, Ss = fh["H"], fh["S"]

    t312r = {r["room"]: r for r in rows(T312_ROOMS)}
    t312o = rows(T312_OPS)
    t128 = {r["ROW"]: r for r in rows(T128_ROOMS)}
    t292 = rows(T292_OPS)
    out_lines = []

    def mats(lo, hi):
        return {"LEVELLING_RENDER (1:4, Q-79)": R676.coat_materials(lo, hi, "LEVELLING_RENDER", *LEVELLING_RENDER),
                "BOND_COAT spatter dash (1:2)": {"status": "HELD", "why": "spatter dash: T-364 row, no thickness "
                                                 "from the project, the owner or the rules", "cement_bags": None,
                                                 "sand_m3": None, "water": "HELD"}}

    for room in ANNEX_ROOMS:
        lid = PLASTER_WET[room]
        L = (t312r[room]["contour_m"], f"T-312 ROOM_CLOSURE (T-250 face ledger) {room}")
        ops = [parse_op(r) for r in t312o if r["room"] == room]
        b = R.band_bound(L, Hs, Ss, ops, "PLASTER")
        out_lines.append({"line_id": lid, "item_code": "FIN.PLASTER", "element_id": idx[lid]["element_id"],
                          "room": room, "class": "HELD", "status": "OPEN BOUND (R-T686-1, Q-54 B respected: no "
                          "point released)", "held_low": b["low"], "held_high": b["high"], "measured_net": None,
                          "before": "blank", "length_m": L[0], "height_m": [R.S(Hs[0]), R.S(Hs[1])],
                          "height_rule": "tile-backing render to the tile top = finished ceiling G1 (Q-48 A; the "
                                         "candidate convention of the released wet backing lines, T-329 / T-399)",
                          "openings": ops, "calc": b, "materials": mats(b["low"], b["high"]),
                          "still_open": "annex slab top s 3.544 .. 4.30 (Q-54 B / D-39); A-GF-01 crown (GF-02); "
                                        "door heads Q-55 C"})
    for room in STAIR_ROOMS:
        lid = PLASTER_WET[room]
        L = (t312r[room]["contour_m"], f"T-312 ROOM_CLOSURE (T-250 face ledger) {room}")
        ops = [parse_op(r) for r in t312o if r["room"] == room]
        heads = [(o["head"], o["source"]) for o in ops if o.get("head") is not None]
        lo, hi = R.wet_room_tile_top(heads, STAIR_CORE["g1_abs"], STAIR_CORE["ffl_options"])
        b = R.band_bound(L, (lo, hi), (lo, hi), ops, "PLASTER")
        out_lines.append({"line_id": lid, "item_code": "FIN.PLASTER", "element_id": idx[lid]["element_id"],
                          "room": room, "class": "HELD", "status": "OPEN BOUND (R-T686-3)",
                          "held_low": b["low"], "held_high": b["high"], "measured_net": None, "before": "blank",
                          "length_m": L[0], "height_m": [R.S(lo), R.S(hi)],
                          "height_rule": "low = highest established head (D-GF-10 2.20, ASSUMED - OWNER-APPROVED "
                                         "Q-55 C): a ceiling never lies below a door head; high = G1 ceiling +4.65 "
                                         "- the lower floor option +0.30",
                          "openings": ops, "calc": b, "materials": mats(b["low"], b["high"]),
                          "still_open": "room FFL +0.30 / +1.00 (T-088, C-SH-2); render top (stair soffit, "
                                        + ("held beam T-283 / Q-61 C; W05 height / sill" if room == "GF-10" else
                                           "OP-020 passage head (T-441)") + ")"})
    for room, lid in PAINT_DRY.items():
        rr = t128[room]
        if rr["KIND"] != "DRY" or rr["ZONE"] != "GF_ANNEX" or rr["OPEN_SIDES_M"] != "0":
            raise R.RuleError(f"{room}: expected a closed dry annex room")
        L = (rr["FACE_M"], f"T-128 r3 ROOMS (walked on the verified T-147 boundary) {room}")
        ops = [parse_op(r) for r in t292 if r["room"] == room]
        b = R.band_bound(L, Hs, Ss, ops, "PAINT", face_finish="PLASTERED")
        fl = D(rr["FREELANCER_GROSS_M2"])
        g_lo, g_hi = D(b["gross"][0]), D(b["gross"][1])
        out_lines.append({"line_id": lid, "item_code": "FIN.PAINT", "element_id": idx[lid]["element_id"],
                          "room": room, "class": "HELD", "status": "OPEN BOUND (R-T686-1, Q-54 B respected)",
                          "held_low": b["low"], "held_high": b["high"], "measured_net": None, "before": "blank",
                          "length_m": L[0], "height_m": [R.S(Hs[0]), R.S(Hs[1])],
                          "height_rule": "paint to the finished ceiling G1 = s - 0.60 - 0.15 - FFL (Q-43 A); no beam "
                                         "end inside the band (the ceiling is below the beams)",
                          "openings": ops, "calc": b,
                          "freelancer_gross_m2": R.S(fl),
                          "engine_gross_vs_freelancer_pct": [R.S(R.q((g_lo / fl - 1) * 100)),
                                                             R.S(R.q((g_hi / fl - 1) * 100))],
                          "still_open": "annex slab top s 3.544 .. 4.30 (Q-54 B / D-39); W11 / W12 sill (T-207); "
                                        "arch A-GF-01 crown (GF-01)" if room == "GF-01" else
                                        "annex slab top s 3.544 .. 4.30 (Q-54 B / D-39); door heads Q-55 C"})
    reveals = []
    for lid, rv in REVEALS.items():
        e = {"line_id": lid, "item_code": "FIN.PLASTER", "element_id": idx[lid]["element_id"], "class": "HELD",
             "held_low": None, "held_high": None, "measured_net": None, "missing_datum": rv["datum"],
             "cause_t676": t676[lid]["class"]}
        if "w" in rv:
            C = Ss[1] if rv["zone"] == "annex" else D(rv["S"])
            hi = R.q(D(rv["t"]) * (2 * D(C) + D(rv["w"])))
            e["information_upper_m2"] = R.S(hi)
            e["information_note"] = (f"crown <= soffit {R.S(C)} m and a flat head maximises 2 x t x spring + t x "
                                     "developed head for a given crown: <= t x (2 C + w); no lower bound is printed, "
                                     "so the line stays blank (never 0)")
        reveals.append(e)

    # F-T680-1
    g, res = R.governing_height(F_T680_1)
    f680 = {"governing": g["id"], "sill_head": [g["sill"], g["head"]], "residuals": res,
            "area_impact_if_raster_m2": R.S(R.q(D(W25_WIDTH) * D(res[0]["height_difference_m"]))),
            "why": "ERS evidence hierarchy: the DWF vector outline is measured geometry with the view's own level "
                   "ticks (issue check 0.006 / 0.013 m) and its height 1.501 equals the window's own outline and the "
                   "stacked W27 of the same type on both sources; the raster 1.76 m glazing contradicts that outline "
                   "and a raster is never scaled (UP-OPEN-GEOM-001 proposal). Residual 0.26 m2 per finish on the 1F "
                   "shaft lines named, not applied (designer D-45 class)."}

    # totals
    tot = {}
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        new = [l for l in out_lines if l["item_code"] == code]
        lo = sum((D(l["held_low"]) for l in new), Decimal(0))
        hi = sum((D(l["held_high"]) for l in new), Decimal(0))
        base = r2[code]
        tot[code] = {"v3_0_66": census[code], "after_round2": base,
                     "this_round": {"lines": len(new), "low": R.S(lo), "high": R.S(hi)},
                     "after_round3": {"bounded": base["bounded"] + len(new), "blank": base["blank"] - len(new),
                                      "low": R.S(D(base["low"]) + lo), "high": R.S(D(base["high"]) + hi)}}
    above_ceiling = R.q(sum((D(t312r[r]["contour_m"]) for r in ANNEX_ROOMS), Decimal(0)) * (Ss[0] - Hs[0]))
    return {
        "task": "T-686", "schema": "T686_ROUND3 v1", "candidate": "ARCH_TAKEOFF_V3.0.66 (T-677 line index)",
        "inputs": {p.name: sha(p) for p in (CAND, T680, T678, T676, T312_ROOMS, T312_OPS, T128_ROOMS, T292_OPS)},
        "annex_datum": {"s": [s_lo[0], ANNEX["s_hi"][0]], "terms": {k: v for k, v in ANNEX.items()},
                        "plaster_S_m": [R.S(Ss[0]), R.S(Ss[1])], "paint_tile_H_m": [R.S(Hs[0]), R.S(Hs[1])],
                        "owner_manual_3_15_inside": bool(Hs[0] <= Decimal("3.15") <= Hs[1])},
        "lines": out_lines, "reveals_still_blank": reveals, "f_t680_1": f680, "code_totals_m2": tot,
        "finding_above_ceiling_band": {
            "m2_gross_per_annex_wet_rooms": R.S(above_ceiling),
            "note": "wet-room FIN.PLASTER lines stop at the tile top (G1) as the released laundry / pantry backing "
                    "lines do; the owner's 'plaster to the slab underside above false ceilings' (2026-11-02) puts a "
                    "band S - H = 0.59 m above the ceiling that no wet-room line carries (34.8 m x 0.59 = this "
                    "figure for the 4 annex rooms): named for the Lead, not added"},
        "rules": ["R-T686-1", "R-T686-2", "R-T686-3", "R-T686-4"],
    }


def md(r):
    L = [f"# T-686 round 3 ({r['candidate']}): research, unwired", "",
         f"Annex slab top s {r['annex_datum']['s'][0]} .. {r['annex_datum']['s'][1]}: plaster soffit "
         f"{r['annex_datum']['plaster_S_m'][0]} .. {r['annex_datum']['plaster_S_m'][1]} m, paint / tile top "
         f"{r['annex_datum']['paint_tile_H_m'][0]} .. {r['annex_datum']['paint_tile_H_m'][1]} m above FFL.", "",
         "| line | code | room | before | after low .. high (m2) | length m | height m |", "|---|---|---|---|---|---|---|"]
    for l in r["lines"]:
        L.append(f"| {l['line_id'][:10]} | {l['item_code']} | {l['room']} | blank | {l['held_low']} .. "
                 f"{l['held_high']} | {l['length_m']} | {l['height_m'][0]} .. {l['height_m'][1]} |")
    L += ["", "Still blank (datum named):"]
    for e in r["reveals_still_blank"]:
        L.append(f"- {e['line_id'][:10]} {e['element_id']}: {e['missing_datum']}"
                 + (f" (information: <= {e['information_upper_m2']} m2)" if "information_upper_m2" in e else ""))
    L += ["", "| code | V3.0.66 | after round 2 | after round 3 |", "|---|---|---|---|"]
    for c, t in r["code_totals_m2"].items():
        a, b, n = t["v3_0_66"], t["after_round2"], t["after_round3"]
        L.append(f"| {c} | {a['low']} .. {a['high']} ({a['bounded']}) + {a['blank']} blank | {b['low']} .. "
                 f"{b['high']} ({b['bounded']}) + {b['blank']} | {n['low']} .. {n['high']} ({n['bounded']}) + "
                 f"{n['blank']} |")
    f = r["f_t680_1"]
    L += ["", f"F-T680-1: governs {f['governing']} (sill / head {f['sill_head'][0]} / {f['sill_head'][1]}); raster "
              f"residual {f['area_impact_if_raster_m2']} m2 named, not applied.", ""]
    return "\n".join(L)


def main(argv):
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True, default=str) + "\n"
    mdt = md(r)
    OUT.mkdir(exist_ok=True)
    pj, pm = OUT / "T686_ROUND3.json", OUT / "T686_ROUND3.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == mdt
        print("T-686 --check:", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    pj.write_text(js)
    pm.write_text(mdt)
    print(mdt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
