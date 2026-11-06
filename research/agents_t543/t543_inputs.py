"""T-543 development-villa inputs (research, unwired): engine values from MERGED repository files, the freelancer's
section sub-totals, and drawing-derived parapet runs. No coordinate, drawing content, client name or workbook row.

Freelancer: Drive "Alsenan chalet project", the masonry workbook (one sheet, read this run with the Drive text reader
as T-541 R-T541-1 did; formulas not shown, cell values shown). Only SECTION SUB-TOTALS are kept here (per floor:
summed length, gross, openings; and the four non-wall rows by name). His printed grand total is 1,260.69 m2; the exact
sum of his row products is 1,260.6895 m2 (his three printed section totals 559.80 / 617.25 / 83.64 are rounded prints
of 559.8015 / 617.2480 / 83.6400: checked by `freelancer_check()`).

Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (T-507). V3.0.58 changes FIN.WP.ROOF / FIN.WP.ROOF_UPTURN only (its
R-T507-1 (e): every V3.0.57 line byte-identical), so the MAS.BLOCK lines are those of
research/agents_t507/out/LINE_INDEX_V3_0_57.json (13 valued lines, 467.7925 m2; 15 HELD lines, blank).
Per wall: research/agents_t288/REGISTER_V4_EXPORT.json (the per-wall fill the T-449 r3 register reproduces) with the
T-488 changes applied (2F walls HELD on the roof datum D-39; GF-W22 HELD as CONFLICT D-27) -> sums asserted equal to
the line index per floor and thickness. Held-wall figures (carried, NOT quantities): research/agents_t228/
BLOCKWORK_WALL_REGISTER_V2.csv (length, gross on the established pieces, deductions, held length, held cause).
Parapets: research/agents_t319/V3_0_23_RUNS_T319.csv (25 runs; T-324 C3 NW-2 3.1672 m and C5 NE-6x as T-488 restated).
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
REG_V4 = ROOT / "research/agents_t288/REGISTER_V4_EXPORT.json"
REG_V2 = ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv"
PARAPET_RUNS = ROOT / "research/agents_t319/V3_0_23_RUNS_T319.csv"

FLOORS = ("GF", "1F", "2F")
ENGINE_RELEASED_M2 = "467.7925"            # MAS.BLOCK valued, V3.0.58 (= V3.0.57)

# ---- freelancer: section sub-totals only (summed from his rows this run, exact Decimal) -----------------------------
FREELANCER_TOTAL = "1260.6895"             # printed 1260.69
FREELANCER_PRINTED = {"external": "559.80", "15cm": "617.25", "20cm": "83.64", "grand": "1260.69"}
FREELANCER_SECTIONS_EXACT = {"external": "559.8015", "15cm": "617.2480", "20cm": "83.6400"}
# storey walls per floor (his external + 15 cm + 20 cm wall rows; non-wall rows below are excluded)
FREELANCER_FLOOR = {
    "GF": {"length_m": "134.28", "gross_m2": "515.3950", "openings_m2": "48.4400"},
    "1F": {"length_m": "120.31", "gross_m2": "441.4095", "openings_m2": "50.3500"},
    "2F": {"length_m": "39.10", "gross_m2": "137.6950", "openings_m2": "13.7600"},
}
FREELANCER_20CM_OPENINGS_NO_FLOOR = "9.8400"   # his 20 cm section deducts 4 openings without naming a floor
# non-wall rows inside his masonry sections (gross, no opening): name -> (m2, his section, his length m, his height m)
FREELANCER_NON_WALL = {
    "BOUNDARY_WALL": ("74.40", "15cm", "37.20", "2.00"),
    "PARAPET_1F_ROW": ("66.00", "15cm", "66.00", "1.00"),
    "PARAPET_ROOF_ROW": ("77.13", "15cm", "42.85", "1.80"),
    "ROOF_ROW_UNLABELLED": ("29.80", "15cm", "29.80", "1.00"),
    "PROJECTIONS_1F": ("41.25", "external", "7.50", "5.50"),
}


def freelancer_check() -> dict:
    """his floors + non-wall rows - unallocated openings == his exact total; printed section totals are roundings."""
    t = sum((Decimal(v["gross_m2"]) - Decimal(v["openings_m2"]) for v in FREELANCER_FLOOR.values()), Decimal(0))
    t += sum((Decimal(v[0]) for v in FREELANCER_NON_WALL.values()), Decimal(0))
    t -= Decimal(FREELANCER_20CM_OPENINGS_NO_FLOOR)
    assert t == Decimal(FREELANCER_TOTAL), t
    assert sum(map(Decimal, FREELANCER_SECTIONS_EXACT.values())) == Decimal(FREELANCER_TOTAL)
    for k, v in FREELANCER_SECTIONS_EXACT.items():
        assert Decimal(v).quantize(Decimal("0.01")) == Decimal(FREELANCER_PRINTED[k]) or k == "external", k
    # external prints 559.80 for 559.8015 (his cell rounding of three floor nets 266.355 / 206.8715 / 86.575)
    return {"total": str(t)}


def _dec(x):
    return None if x in (None, "") else Decimal(str(x))


def engine_lines() -> list[dict]:
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    out = []
    for ln in d["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        out.append({"line_id": ln["line_id"], "element_id": ln["element_id"], "class": ln["class"],
                    "qty": None if ln["measured_net"] is None else str(ln["measured_net"]), "unit": ln["unit"]})
    return sorted(out, key=lambda r: r["line_id"])


def other_family_lines(prefix: str) -> list[dict]:
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    return [{"item_code": ln["item_code"], "line_id": ln["line_id"], "element_id": ln["element_id"],
             "class": ln["class"], "qty": None if ln["measured_net"] is None else str(ln["measured_net"])}
            for ln in d["lines"] if ln["item_code"].startswith(prefix)]


def engine_walls() -> list[dict]:
    """one record per register wall: V3.0.58 valued m2 (or None) and the V2 carried figures."""
    v4 = {w["wall_id"]: w for w in json.loads(REG_V4.read_text(encoding="utf-8"))["walls"]}
    v2 = {r["wall_id"]: r for r in csv.DictReader(REG_V2.open(encoding="utf-8"))}
    assert set(v4) == set(v2), set(v4) ^ set(v2)
    out = []
    for wid, w in v4.items():
        r = v2[wid]
        valued = _dec(w["net_m2"])
        state = w["state"]
        if w["floor"] == "2F" and valued is not None:      # T-488 ROOF_DATUM (D-39)
            valued, state = None, "HELD ON ROOF DATUM (D-39)"
        if wid == "GF-W22":                                # T-488 WIDTH_CONFLICT (D-27)
            valued, state = None, "CONFLICT [12.9311, 12.9439] (D-27)"
        gross = _dec(r["gross_m2"])
        ded = _dec(r["deductions_m2"]) or Decimal(0)
        out.append({
            "wall_id": wid, "floor": w["floor"], "t_m": str(w["t_m"]), "group": r["group"],
            "valued_m2": None if valued is None else str(valued), "state_v3_0_58": state,
            "length_m": str(_dec(r["length_m"])), "held_length_m": str(_dec(r["held_length_m"]) or Decimal(0)),
            "gross_v2_m2": None if gross is None else str(gross), "deductions_v2_m2": str(ded),
            "held_cause_v2": r["held_cause_class"], "held_items_v4": w["held_items"] or "",
        })
    return sorted(out, key=lambda x: (FLOORS.index(x["floor"]), x["wall_id"]))


def parapet_runs() -> list[dict]:
    out = []
    for r in csv.DictReader(PARAPET_RUNS.open(encoding="utf-8")):
        lo, hi = (Decimal(x.strip()) for x in r["centreline_m"].split(".."))
        hlo, hhi = (Decimal(x.strip()) for x in r["h_above_finish_m"].split(".."))
        if r["run"] == "NW-2" and r["chain"] == "1F":
            ba = Decimal("3.1672")                         # T-488 PARAPET_RUN restatement (T-324 C3)
        elif r["block_alternative_m2"] == "not booked":
            ba = Decimal("0.25999")                        # NE-6x, T-488 (T-324 C5)
        else:
            ba = Decimal(r["block_alternative_m2"].split("..")[1].strip())
        out.append({"chain": r["chain"], "run": r["run"], "t_m": r["t_m"], "centreline_lo": str(lo),
                    "centreline_hi": str(hi), "h_lo": str(hlo), "h_hi": str(hhi), "h_status": r["h_status"],
                    "block_alt_hi_m2": str(ba)})
    return out


S_LINES = "LINE_INDEX_V3_0_57 (V3.0.58 MAS.BLOCK lines byte-identical, R-T507-1 (e))"
S_V4 = "REGISTER_V4_EXPORT (T-288) + T-488 changes"
S_V2 = "BLOCKWORK_WALL_REGISTER_V2 (T-228) carried figure, not a quantity"
S_PARAPET = "V3_0_23_RUNS_T319 + T-488 PARAPET_RUN"
S_P1 = "ST7757.pdf p.14 P1 parapet detail: RC upstand 0.30 above the slab (T-319 / T-482 own reads)"
