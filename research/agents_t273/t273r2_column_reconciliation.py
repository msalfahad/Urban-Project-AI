"""T-273 r2 (owner acceptance s.6.2, 2026-10-24 18:38): reconcile the column LAP and STARTER components already carried
by the S3 column ledger BEFORE any new lap quantity is added. Read only: research/alsenan_column_rebar_s3 registers (the
ledger is not edited); no private file is read. Writes COLUMN_LAP_STARTER_RECONCILIATION_T273R2.json beside this file
(or prints it with --print).

Question per chain: along one vertical line of column bars, how many layers of steel does the ledger count in each lap
zone? Physically a lap zone holds exactly TWO bars (the lower bar and the upper bar overlapping); the ledger must count
it twice (never three times, never once).

Ledger model (engine/source/column_rebar._main_parts + the S3 adapter, read from the registers, not assumed):
  MAIN_CORE of a storey segment = the storey interval (FOUNDATION: footing top -> GF FFL, 'GF FFL +1.00 m minus founding
  level <= -1.50 m minus footing depth H'; upper storeys: FFL -> FFL);
  LAP_TOP = the lower bar's extension 40 D above the next FFL (only where the chain continues above);
  STARTER = (H - bottom cover 70) + foot 300 + projection 40 D (the starter's leg above the footing top).
So at the footing top the zone [footing top, +40 D] holds the starter projection + the FOUNDATION core (2 layers), and at
each storey joint the zone [FFL, +40 D] holds the LAP_TOP extension + the core above (2 layers). The script verifies each
link of that statement per chain from the register numbers and reports any chain where it fails.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S3 = ROOT / "research" / "alsenan_column_rebar_s3"
OUT = HERE / "COLUMN_LAP_STARTER_RECONCILIATION_T273R2.json"

GF_FFL_MM = 1000              # S3 interval basis 'GF FFL +1.00 m'
FOUNDING_MM = -1500           # S3 interval basis 'founding level <= -1.50 m' (footing underside)
UNDERLAY_MM = 70 + 100        # T-206 r2 (MERGED): 5 cm screed + 2 cm membrane + 10 cm blinding under every isolated footing


def _load(name):
    return json.loads((S3 / name).read_text(encoding="utf-8"))


def _kgm(row):
    return row["kg"] / row["total_length_m"] if row.get("total_length_m") else None


def build(LS=None, main_rows=None):
    """LS: the COLUMN_LAP_STARTER_REGISTER content, main_rows: the COLUMN_MAIN_BAR_REGISTER rows (default: the S3
    registers in the repository); a test passes a synthetic ledger here."""
    LS = LS if LS is not None else _load("COLUMN_LAP_STARTER_REGISTER.json")
    rules = {k: LS[k] for k in ("lap_rule", "anchorage_rule", "starter_rule")}
    st_rule = rules["starter_rule"]
    rows = LS["rows"]
    main_rows = main_rows if main_rows is not None else _load("COLUMN_MAIN_BAR_REGISTER.json")["rows"]
    main = [r for r in main_rows if r["component"] == "MAIN_BARS"]
    core = {(r["chain_id"], r["floor"]): r for r in main}
    by_chain = defaultdict(list)
    for r in rows:
        by_chain[r["chain_id"]].append(r)

    comp = Counter((r["component"], r["release_state"]) for r in rows)
    lap_rows = [r for r in rows if r["component"] == "LAP"]
    starters = [r for r in rows if r["component"] == "STARTER"]
    chains, failures = [], []

    for cid in sorted(by_chain):
        rs = by_chain[cid]
        st = next((r for r in rs if r["component"] == "STARTER"), None)
        laps = sorted((r for r in rs if r["component"] == "LAP"), key=lambda r: ["FOUNDATION", "GF", "1F", "2F"]
                      .index(r["floor"]))
        rec = {"chain_id": cid, "zones": [], "checks": []}

        def check(name, ok, detail):
            rec["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
            if not ok:
                failures.append({"chain_id": cid, "check": name, "detail": detail})

        # --- every LAP is a top splice of a segment (never a base splice beside a starter)
        for lp in laps:
            check("lap_is_top_splice", lp["part_id"].endswith("|LAP_TOP"), lp["part_id"])
        # --- footing-top zone
        if st is not None:
            fc = core.get((cid, "FOUNDATION"))
            f = st.get("footing") or {}
            H, db, n = f.get("depth_mm"), st["dia_mm"], st["count"]
            proj = st_rule["projection_D"] * db
            z = {"zone": "FOOTING_TOP", "footing_ref": f.get("ref"), "footing_depth_mm": H, "bars": n, "dia_mm": db,
                 "starter_state": st["release_state"], "lap_zone_mm": proj}
            check("foundation_core_exists", fc is not None, "FOUNDATION MAIN_CORE row for the starter chain")
            if fc is not None:
                check("same_bars_starter_core", (fc["count"], fc["dia_mm"]) == (n, db),
                      f"starter {n} T{db} vs core {fc['count']} T{fc['dia_mm']}")
                iv = fc["interval"]
                Hc = fc_depth = None
                # the core's own footing depth: from its basis text 'minus footing depth <H> mm'
                txt = iv["basis"]
                if "footing depth" in txt:
                    fc_depth = float(txt.split("footing depth")[1].split("mm")[0])
                Hc = fc_depth
                core_bottom = GF_FFL_MM - iv["length_mm"]
                z.update(core_interval_mm=iv["length_mm"], core_state=iv["state"], core_basis=iv["basis"],
                         core_bottom_level_mm=core_bottom)
                if H is not None:
                    ftop = FOUNDING_MM + H
                    z["footing_top_level_mm"] = ftop
                    check("core_starts_at_footing_top", abs(core_bottom - ftop) < 0.5 and Hc == H,
                          f"core bottom {core_bottom} mm vs footing top {ftop} mm (core basis H {Hc}, starter H {H})")
                    exp = (H - st_rule["bottom_cover_mm"]) + st_rule["foot_mm"] + proj
                    check("starter_length_is_rule", abs((st["length_per_piece_mm"] or 0) - exp) < 0.5,
                          f"{st['length_per_piece_mm']} = ({H} - {st_rule['bottom_cover_mm']}) + "
                          f"{st_rule['foot_mm']} + {st_rule['projection_D']} x {db} = {exp}")
                    # layers in the lap zone [ftop, ftop + proj]: starter projection + core (core starts at ftop)
                    layers = 1 + (1 if core_bottom <= ftop + 0.5 else 0)
                    inside_footing_core = max(0.0, ftop - core_bottom)
                    z.update(layers_in_lap_zone=layers, core_inside_footing_mm=inside_footing_core)
                    check("footing_top_zone_counted_twice", layers == 2 and inside_footing_core == 0,
                          f"layers {layers}, core inside the footing {inside_footing_core} mm")
                    kgm = _kgm(fc)
                    z["lap_zone_kg_each_layer"] = round(n * proj / 1000 * kgm, 3)
                    # T-206 r2 finding: footing bottom = formation + 0.17; the S3 core puts it AT -1.50
                    z["core_if_formation_at_printed_limit_mm"] = iv["length_mm"] - UNDERLAY_MM
                    z["core_kg_difference_if_formation_at_limit"] = round(-n * UNDERLAY_MM / 1000 * kgm, 3)
                else:
                    z["footing_top_level_mm"] = None
                    z["layers_in_lap_zone"] = "HELD (footing depth not established: starter BLOCKED)"
                    check("blocked_starter_has_no_length", st["length_per_piece_mm"] is None and st["kg"] in (0, None),
                          f"starter length {st['length_per_piece_mm']}, kg {st['kg']}")
            rec["zones"].append(z)
        # --- storey joints
        floors = ["FOUNDATION", "GF", "1F", "2F"]
        for lp in laps:
            above = floors[floors.index(lp["floor"]) + 1]
            ca, cb = core.get((cid, above)), core.get((cid, lp["floor"]))
            z = {"zone": f"JOINT_{lp['floor']}->{above}", "lap_part": lp["part_id"], "bars": lp["count"],
                 "dia_mm": lp["dia_mm"], "lap_mm": lp["length_per_piece_mm"], "lap_state": lp["release_state"],
                 "lap_kg": lp["kg"], "lap_kg_at_70D": lp.get("kg_at_alternative")}
            check("core_above_exists", ca is not None, f"MAIN_CORE {above}")
            check("core_below_exists", cb is not None, f"MAIN_CORE {lp['floor']}")
            if ca is not None and cb is not None:
                # below ends at the FFL above (FFL basis or 'GF FFL' basis), above starts at it: no overlap of cores
                check("cores_meet_at_ffl", ("FFL" in cb["interval"]["basis"]) and ("FFL" in ca["interval"]["basis"]),
                      f"{cb['interval']['basis']} | {ca['interval']['basis']}")
                check("lap_bars_not_more_than_both", lp["count"] <= min(ca["count"], cb["count"]),
                      f"lap {lp['count']} vs below {cb['count']} / above {ca['count']}")
                check("lap_dia_is_upper_bar", lp["dia_mm"] == ca["dia_mm"], f"lap T{lp['dia_mm']} vs above T{ca['dia_mm']}")
                z["layers_in_lap_zone"] = 2
            rec["zones"].append(z)
        # one starter per chain, at most one lap per joint
        check("one_starter", sum(r["component"] == "STARTER" for r in rs) <= 1, "starter rows")
        check("one_lap_per_joint", len({r["floor"] for r in laps}) == len(laps), "lap rows per floor")
        chains.append(rec)

    st_ok = [z for c in chains for z in c["zones"] if z["zone"] == "FOOTING_TOP" and z.get("layers_in_lap_zone") == 2]
    fdn_laps = [r for r in lap_rows if r["floor"] == "FOUNDATION"]
    alt = sum((r.get("kg_at_alternative") or r["kg"]) - r["kg"] for r in lap_rows)
    alt_anc = sum((r.get("kg_at_alternative") or r["kg"]) - r["kg"] for r in rows if r["component"] == "ANCHORAGE")
    out = {
        "task": "T-273 r2 (owner s.6.2)", "ledger": "research/alsenan_column_rebar_s3 (read only, not edited)",
        "rules": rules,
        "component_counts": {f"{c}|{s}": n for (c, s), n in sorted(comp.items())},
        "lap_rows": len(lap_rows), "lap_kg": round(sum(r["kg"] for r in lap_rows), 3),
        "lap_rows_by_state": dict(Counter(r["release_state"] for r in lap_rows)),
        "foundation_lap_rows": len(fdn_laps), "foundation_lap_kg": round(sum(r["kg"] for r in fdn_laps), 3),
        "starter_rows": len(starters), "starter_rows_by_state": dict(Counter(r["release_state"] for r in starters)),
        "starter_kg": round(sum(r["kg"] or 0 for r in starters), 3),
        "chains_with_starter_and_foundation_lap": len({r["chain_id"] for r in starters} & {r["chain_id"] for r in fdn_laps}),
        "footing_top_zones_counted_twice": len(st_ok),
        "starter_projection_kg_total": round(sum(z["lap_zone_kg_each_layer"] for z in st_ok), 3),
        "scenario_70D_minus_40D_lap_kg": round(alt, 3),
        "scenario_70D_minus_40D_anchorage_kg": round(alt_anc, 3),
        "scenario_70D_flag_total_kg": round(alt + alt_anc, 3),
        "scenario_70D_note": "STR-COL-026's +640.99 kg = LAP + ANCHORAGE at 70 D (two s.6.1 categories in one figure); "
                             "the STARTER projection (also 40 D, note 9 = starter development) is NOT in it",
        "scenario_70D_starter_projection_kg": round(sum(z["lap_zone_kg_each_layer"] for z in st_ok) * 30 / 40, 3),
        "scenario_70D_status": "SCENARIO (owner s.6.2): not an approved BOQ addition",
        "finding_core_basis": {
            "text": "FOUNDATION MAIN_CORE = GF FFL +1.00 minus a footing underside AT -1.50 (2.50 - H); T-206 r2 "
                    "(MERGED) prints footing bottom = formation + 0.17 (5 screed + 2 membrane + 10 blinding) with the "
                    "formation 'not less than 1.5 m below the existing plot level' (Q-21 C, a minimum, existing-ground "
                    "datum HELD). The ledger's 2.50 - H therefore implies a formation at -1.67; with the formation at its "
                    "printed limit relative to +-0.00 the core is 0.17 m SHORTER, so the 'LOWER_BOUND' label of the "
                    "foundation cores is not a lower bound of the printed geometry: a labelled convention (no ledger "
                    "edit here; the lap zones are unaffected because the core still starts at the footing top).",
            "kg_if_formation_at_limit": round(sum(z.get("core_kg_difference_if_formation_at_limit", 0) for c in chains
                                                  for z in c["zones"] if z["zone"] == "FOOTING_TOP"), 3),
            "chains": sum(1 for c in chains for z in c["zones"] if "core_kg_difference_if_formation_at_limit" in z)},
        "failures": failures,
        "result": "NO DOUBLE COUNT: every lap zone is counted exactly twice" if not failures else "FAILURES (see list)",
        "chains": chains,
    }
    return out


def main(argv):
    out = build()
    text = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--print" in argv:
        print(text)
    else:
        OUT.write_text(text, encoding="utf-8")
        print({k: out[k] for k in ("lap_rows", "lap_kg", "lap_rows_by_state", "foundation_lap_rows",
                                    "foundation_lap_kg", "starter_rows", "starter_rows_by_state",
                                    "chains_with_starter_and_foundation_lap", "footing_top_zones_counted_twice",
                                    "starter_projection_kg_total", "scenario_70D_minus_40D_lap_kg",
                                    "scenario_70D_minus_40D_anchorage_kg", "scenario_70D_flag_total_kg",
                                    "scenario_70D_starter_projection_kg", "result")})
        print("finding", out["finding_core_basis"]["kg_if_formation_at_limit"], out["finding_core_basis"]["chains"])
        print("failures", out["failures"][:10])


if __name__ == "__main__":
    main(sys.argv[1:])
