"""T-273 Alsenan: lap rows per bar group from the governing authority (rebar_laps_v1), on committed, merged ledgers only
(no private file is read here). Development villa; no accuracy claim; nothing released or candidate changes.

Inputs (merged, cited):
  research/agents_t265/LEDGER_T265.csv   ground-beam bar populations and face-to-face runs (Gate A MERGED dd08d6b2)
  research/agents_t138/T-138_GROUND_BEAM_STRAP_STEEL.md r2 (MERGED): the bands whose bars run THROUGH their interior
      columns (p.13): south band 7D0 / FC 2.975 + 1.10 + 5.745 + 0.50 + 6.350 + 0.70 + 1.200 = 18.570 m, north band
      170 / 7C3 2.400 + 0.30 + 3.370 + 0.60 + 3.350 + 0.50 + 3.250 = 13.770 m; every other span has two ends per piece
  research/alsenan_column_rebar_s3/COLUMN_LAP_STARTER_REGISTER.json   column LAP / STARTER / ANCHORAGE (already carried)
  research/alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv               slab TEMPERATURE and TRANSITION_LAP_SPLICE items
Drawing notes (Drive "Alsenan chalet project" / "ST7757.pdf", as recorded by the merged research): p.8 note 9
'development / tie length of starter bars not less than 70 d (tension) / 40 d (compression)'; p.15 slab temperature
note 1 'LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA'; no lap schedule; no lap detail for beam bars.
Stock: URBAN-REBAR-NET-AND-PROCUREMENT@v1 stock_length_m 12.0 (rules/methods/URBAN_METHOD_REGISTER_V3.json).
Writes LAP_ROWS_T273.csv and summary.json next to this file when run as a script.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import rebar_laps_v1 as RL  # noqa: E402

T265 = ROOT / "research" / "agents_t265" / "LEDGER_T265.csv"
COLS = ROOT / "research" / "alsenan_column_rebar_s3" / "COLUMN_LAP_STARTER_REGISTER.json"
S7B = ROOT / "research" / "alsenan_slab_rebar_s7" / "02_S7_BLOCKED_ITEMS.csv"
STOCK_M, STOCK_REF = 12.0, "URBAN-REBAR-NET-AND-PROCUREMENT@v1 stock_length_m (OD-V3-3)"
UNIT_MASS = {"method": "D2_OVER_162", "authority": "as T-265 / T-138 (d^2 / 162)", "selected_by": "project"}

NOTE9 = {"tier": RL.NOTE, "tension_d": 70, "compression_d": 40, "kind": RL.MINIMUM, "governs": False,
         "ref": "ST7757.pdf p.8 note 9 (starter bars only)",
         "category": RL.STARTER_CAT}          # r2 (owner s.6.1): starter development, never a general lap rule
P15 = {"tier": RL.NOTE, "lap_d": 40, "kind": RL.EXACT, "governs": True,
       "ref": "ST7757.pdf p.15 temperature note 1 (temperature bars only)",
       "category": RL.LAP_CAT}
CHAINS = {   # T-138 r2: bars continue through the interior columns (p.13); runs that form each chain in T-265
    "GB-CHAIN-7D0/FC": {"runs": ("7D0+FC#1", "7D0+FC#2", "7D0+FC#3", "7D0+FC#4"), "L_m": 18.570,
                        "through_columns_m": (1.10, 0.50, 0.70)},
    "GB-CHAIN-170/7C3": {"runs": ("170+7C3#1", "170+7C3#2", "170+7C3#3", "170+7C3#4"), "L_m": 13.770,
                         "through_columns_m": (0.30, 0.60, 0.50)},
}
NOT_RE_MEASURED_BY_T138 = ("ARC:157+158", "145+7CA#1")      # their bar ends are not established by a merged ledger
BOUNDARY_CONTINUOUS = ("7FE#1",)        # T-265: longitudinal bars continuous through the boundary columns of the run


def _t265():
    runs = {}
    for r in csv.DictReader(T265.open(encoding="utf-8")):
        if r["component"] not in ("TOP", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE") or not r["length_m"]:
            continue
        runs.setdefault((r["member"], r["family"]), []).append(
            {"component": r["component"], "bars": int(r["n_bars"]), "dia_mm": int(r["dia_mm"]),
             "L_m": float(r["length_m"])})
    return runs


def ground_beam_rows():
    runs = _t265()
    rows = []
    in_chain = {m for c in CHAINS.values() for m in c["runs"]}
    for cid, c in CHAINS.items():
        # the chain's face-to-face runs must add with the through-column widths to the T-138 band length
        faces = sum(next(x["L_m"] for x in runs[(m, "GB_EXTERIOR")] if x["component"] == "TOP") for m in c["runs"])
        assert abs(faces + sum(c["through_columns_m"]) - c["L_m"]) < 1e-6, (cid, faces)
        comps = runs[(c["runs"][0], "GB_EXTERIOR")]
        for comp in comps:
            if comp["component"] == "SIDE":
                continue                      # side bars: continuity through the columns not printed (per run below)
            main = True
            g = {"element": f"{cid} {comp['component']}", "floor": "GROUND_BEAM", "element_kind": "GROUND_BEAM",
                 "bar_type": comp["component"], "dia_mm": comp["dia_mm"], "bars": comp["bars"], "run_m": c["L_m"],
                 "run_status": RL.DRAWING_CONFIRMED,
                 "continuity": "CONTINUOUS" if main else "NOT_ESTABLISHED",
                 "ref": ("T-138 r2 band through interior columns (p.13); runs " + " + ".join(c["runs"])
                         if main else "side bars 2 levels x 2 T12 (T-265): continuity through columns not printed")}
            rows.append(RL.lap_row(g, stock_m=STOCK_M, stock_ref=STOCK_REF,
                                   lap=RL.resolve_lap({"dia_mm": comp["dia_mm"], "zone": None,
                                                       "element_kind": "GROUND_BEAM"}, [NOTE9]),
                                   unit_mass_cfg=UNIT_MASS))
    for (m, fam), comps in sorted(runs.items()):
        for comp in comps:
            if m in in_chain and comp["component"] != "SIDE":
                continue                      # main bars of a chain run are in the chain row
            if m in in_chain:
                cont, ref = "NOT_ESTABLISHED", ("side bars of a band whose main bars run through its columns: "
                                                "continuity of the side bars through the columns not printed")
            elif fam == "BOUNDARY_GB":
                cont = "CONTINUOUS" if m in BOUNDARY_CONTINUOUS else "NOT_ESTABLISHED"
                ref = ("T-265: boundary bars continuous through the boundary columns of this run; continuation round "
                       "its corners not established (count for this run only)" if m in BOUNDARY_CONTINUOUS else
                       "boundary run: continuation round the corners into the neighbouring runs not established")
            elif m in NOT_RE_MEASURED_BY_T138:
                cont, ref = "NOT_ESTABLISHED", "bar ends not established by a merged ledger (T-138 did not re-measure)"
            else:
                cont, ref = "CONTINUOUS", "T-138 r2: two bar ends per piece (bars end at the run's faces)"
            g = {"element": f"{m} {comp['component']}", "floor": "GROUND_BEAM", "element_kind": "GROUND_BEAM",
                 "bar_type": comp["component"], "dia_mm": comp["dia_mm"], "bars": comp["bars"], "run_m": comp["L_m"],
                 "run_status": RL.DRAWING_CONFIRMED, "continuity": cont, "ref": ref}
            rows.append(RL.lap_row(g, stock_m=STOCK_M, stock_ref=STOCK_REF,
                                   lap=RL.resolve_lap({"dia_mm": comp["dia_mm"], "zone": None,
                                                       "element_kind": "GROUND_BEAM"}, [NOTE9]),
                                   unit_mass_cfg=UNIT_MASS))
    return rows


def slab_rows():
    items = list(csv.DictReader(S7B.open(encoding="utf-8")))
    rows = []
    temp = [r for r in items if r["CATEGORY"] == "TEMPERATURE"]
    trans = [r for r in items if r["CATEGORY"] == "TRANSITION_LAP_SPLICE"]
    dias = sorted({r["DIA_MM"] for r in temp})
    assert dias == [""], dias                 # S7: the temperature bar diameter itself is not established
    g = {"element": f"SLAB TEMPERATURE BARS ({len(temp)} blocked S7 items)", "floor": "ALL SLABS",
         "element_kind": "SLAB", "bar_type": "TEMPERATURE", "dia_mm": None, "bars": None, "run_m": None,
         "run_status": RL.HELD, "continuity": "NOT_ESTABLISHED",
         "ref": "S7 TEMPERATURE blocked (no 160 / 180 mm table row): diameter, count and extent not established"}
    rows.append(RL.lap_row(g, stock_m=STOCK_M, stock_ref=STOCK_REF,
                           lap=RL.resolve_lap({"dia_mm": None, "zone": None, "element_kind": "SLAB"}, [P15]),
                           unit_mass_cfg=UNIT_MASS))
    for dia in sorted({int(float(r["DIA_MM"])) for r in trans if r["DIA_MM"]}):
        n = sum(1 for r in trans if r["DIA_MM"] and int(float(r["DIA_MM"])) == dia)
        p15 = dict(P15, governs=False)          # p.15 names temperature bars only, not main-bar transitions
        g = {"element": f"SLAB MAIN-BAR TRANSITIONS d{dia} ({n} blocked S7 items)", "floor": "ALL SLABS",
             "element_kind": "SLAB", "bar_type": "TRANSITION", "dia_mm": dia, "bars": None, "run_m": None,
             "run_status": RL.HELD, "continuity": "NOT_ESTABLISHED",
             "ref": "S7 TRANSITION_LAP_SPLICE blocked: extent / count across the support not established"}
        rows.append(RL.lap_row(g, stock_m=STOCK_M, stock_ref=STOCK_REF,
                               lap=RL.resolve_lap({"dia_mm": dia, "zone": None, "element_kind": "SLAB"},
                                                  [p15, NOTE9]),
                               unit_mass_cfg=UNIT_MASS))
    return rows


def column_carried():
    d = json.loads(COLS.read_text(encoding="utf-8"))
    agg = {}
    for r in d["rows"]:
        a = agg.setdefault((r["component"], r["release_state"]), {"rows": 0, "kg": 0.0, "kg_at_alternative": 0.0})
        a["rows"] += 1
        a["kg"] += r["kg"] or 0.0
        a["kg_at_alternative"] += r.get("kg_at_alternative") or 0.0
    out = [{"component": k[0], "release_state": k[1], "rows": v["rows"], "kg": round(v["kg"], 3),
            "kg_at_70d": round(v["kg_at_alternative"], 3)} for k, v in sorted(agg.items())]
    for comp in RL.ALREADY_CARRIED:            # a second lap on a column is refused by the module
        try:
            RL.lap_row({"element": "probe", "dia_mm": 16, "already_carried": comp}, stock_m=STOCK_M,
                       stock_ref=STOCK_REF, lap={"state": RL.HELD, "basis": "-"}, unit_mass_cfg=UNIT_MASS)
            raise AssertionError("second column lap not refused")
        except RL.LapError:
            pass
    return out, d["lap_rule"]


def convention_reading(rows):
    """owner 40 d / 60 d convention applied as INFORMATION on the rows whose count is established: not a quantity."""
    info = []
    for r in rows:
        if r["status"] != RL.HELD or r["splices"] is None or r["bars"] is None:
            continue
        lap = RL.resolve_lap({"dia_mm": r["dia_mm"], "zone": None, "element_kind": "GROUND_BEAM"}, [],
                             convention_allowed=True)
        n = RL.lap_count(r["net_length_m"], lap["lap_m"], STOCK_M)
        kg = n * r["bars"] * lap["lap_m"] * RL.RUM.kg_per_m(r["dia_mm"], UNIT_MASS)
        info.append({"element": r["element"], "lap_m_60d": lap["lap_m"], "splices": n * r["bars"],
                     "kg": round(kg, 6), "t": round(kg / 1000.0, 6), "status": "INFORMATION ONLY (not a quantity)"})
    return info


def frozen_vs_v2():
    cases = [(8.708, 16, 60), (12.0, 16, 60), (12.01, 16, 60), (23.8, 16, 60), (24.0, 16, 60), (35.0, 16, 60)]
    return [RL.compare_with_frozen(L, d, f, STOCK_M) for L, d, f in cases]


COLUMNS = ("element", "floor", "type", "dia_mm", "bars", "net_length_m", "lap_per_splice_m", "lap_min_m",
           "splices_per_bar", "splices", "count_valid_up_to_lap_m", "added_length_m", "net_kg", "lap_kg",
           "installed_kg", "net_t", "lap_t", "installed_t", "count_status", "lap_status", "status", "lap_basis",
           "lap_ref", "stock_m", "drawing_ref", "findings")


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, list):
        return " | ".join(v)
    return str(v)


def build():
    rows = ground_beam_rows() + slab_rows()
    cols, col_rule = column_carried()
    return {"rows": rows, "totals": RL.totals(rows), "column_already_carried": cols, "column_lap_rule": col_rule,
            "convention_reading": convention_reading(rows), "frozen_vs_v2": frozen_vs_v2(),
            "status_counts": dict(Counter(r["status"] for r in rows)), "policy": RL.policy_record()}


def main():
    res = build()
    with (HERE / "LAP_ROWS_T273.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for r in res["rows"]:
            w.writerow([_cell(r.get(c)) for c in COLUMNS])
    summ = {k: v for k, v in res.items() if k != "rows"}
    (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    print(json.dumps({"status_counts": res["status_counts"], "totals": res["totals"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
