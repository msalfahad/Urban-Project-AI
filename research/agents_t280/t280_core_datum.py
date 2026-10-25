"""T-280 (lane S): from which physical datum does each FOUNDATION column core run? The foundation-core bounds of the
S3 column ledger restated on the verified level chain (T-200 / T-206 r2), per chain, in kg and t.

Read only: research/alsenan_column_rebar_s3 registers (the ledger is NOT edited) and the merged level-chain evidence
quoted below with its source. No private file is read. Writes CORE_DATUM_T280.json beside this file (or --print).

Physical element. The foundation segment of a column's main bars runs from the TOP OF ITS FOOTING (where the starter
projection laps it, T-273 r2) up to the storey joint at GF FFL (the S3 joint datum, where the FOUNDATION LAP sits). The
footing top is not printed as a level. It follows only from the printed chain (T-206 r2, ST7757.pdf p.9 / p.13):

    existing plot level EGL (+-0.00, T-200 DRAWING-CONFIRMED)
    formation  <= EGL - 1.50       (p.9 note 1 'not less than 1.5 m below the existing plot level': a LIMIT, Q-21 C)
    footing bottom = formation + underlay  (p.13 isolated footings: 5 screed + 2 membrane + 10 blinding = 0.17 m)
    footing top    = footing bottom + H    (p.9 schedule depth)

so  core = GF_FFL - footing top >= GF_FFL - (EGL - 1.50 + underlay + H)  = 2.33 - H on Alsenan.

That is the only bound the drawings give: a LOWER bound (formation at its printed limit). There is no printed lowest
formation (p.8 note 12 leaves it to the contractor and the supervising engineer; the p.13 two-beam detail exists for
deeper footings), so the UPPER bound is OPEN: never a value, never the ledger's number.

The S3 ledger computes 2.50 - H, i.e. the footing UNDERSIDE at -1.50 = a formation at -1.67. That is neither bound: it
is 0.17 m above the true lower bound and below no printed upper bound. Labelled CONVENTION_NOT_A_BOUND here.

Support families (each with its own chain; nothing borrowed between them, ERS s.3):
  P13_ISOLATED   : the footing is a scheduled p.13 type with a known H -> LOWER restated, UPPER OPEN.
  P13_CONFLICT   : two scheduled p.13 types compete (F / F10): LOWER over every candidate = max H (valid for both
                   readings), UPPER OPEN; the footing type stays a finding.
  LIFT_PIT_FF    : the lift footing FF (p.14 own detail: membrane printed with NO thickness, pit floor = FF top, pit
                   depth 'As Per Lift Manufactures recommendations', T-204 / D-43) -> the p.13 0.17 is NOT carried over;
                   core = GF FFL - pit floor level = HELD on the pit depth; no lower bound.
  UNBOUND        : the support is not bound to any footing (S3 'deepest scheduled footing - unbound', STR-COL-001:
                   stub / pedestal question open) -> HELD; a CONDITIONAL lower bound (if the support is a p.13 footing,
                   deepest scheduled H) is shown, never used.
A chain whose underlay is not established in the input is HELD, never measured from the formation.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S3 = ROOT / "research" / "alsenan_column_rebar_s3"
OUT = HERE / "CORE_DATUM_T280.json"

STATUS_LOWER = "LOWER_BOUND_RESTATED"      # a bound of the printed geometry (formation at its printed limit)
STATUS_HELD = "HELD"
UPPER_OPEN = "OPEN (no printed lowest formation: p.8 note 12, Q-21 C)"

# Alsenan level chain (merged evidence; each value with its source)
ALSENAN_CHAIN = {
    "gf_ffl_m": {"value": 1.00, "status": "DRAWING-CONFIRMED", "source": "T-200 / T-206 r2 s.2.1 (GF FFL +1.00)"},
    "egl_m": {"value": 0.00, "status": "DRAWING-CONFIRMED",
              "source": "T-200 level table: existing plot level +-0.00 (P7757 LEL x6; ST SH08; SECTION A-A)"},
    "min_excavation_m": {"value": 1.50, "status": "DRAWING-CONFIRMED (a minimum)",
                         "source": "ST7757.pdf p.9 boxed note 1; Q-21 C (a limit, never a founding value)"},
    # underlay per support family: None = not printed (HELD)
    "underlay_m": {
        "P13_ISOLATED": {"value": 0.17, "status": "DRAWING-CONFIRMED",
                         "source": "T-206 r2 s.2.2: p.13 both typical details 5 cm screed + 2 cm membrane + 10 cm blinding"},
        "P13_CONFLICT": {"value": 0.17, "status": "DRAWING-CONFIRMED",
                         "source": "T-206 r2 s.2.2 (F and F10 are both p.13 isolated types)"},
        "LIFT_PIT_FF": {"value": None, "status": "HELD",
                        "source": "T-206 r2 s.2.2: p.14 lift detail prints the membrane with no thickness; pit depth to "
                                  "the lift maker (T-204, D-43)"},
        "UNBOUND": {"value": None, "status": "HELD", "source": "support not bound to a footing (S3, STR-COL-001)"},
    },
    # p.9 schedule depths as T-206 r2 lists them (cross-check of the ledger's H per footing type)
    "schedule_h_m": {"F": 0.30, "F3": 0.30, "FN": 0.30, "F2": 0.35, "F4": 0.40, "F5": 0.40, "F15": 0.40,
                     "F6": 0.50, "F7": 0.50, "F8": 0.50, "F10": 0.50, "F11": 0.50, "F13": 0.50, "F14": 0.50,
                     "F9": 0.55, "FF": 0.55, "F12": 0.70},
}
UNIT_MASS = {"method": "EXACT_DENSITY", "density_kg_m3": 7850}   # the S3 ledger's own method (steel_density 7850)


class CoreDatumError(ValueError):
    pass


def kg_per_m(d_mm, density=7850.0):
    return math.pi / 4.0 * (d_mm / 1000.0) ** 2 * density


def _val(x):
    return x["value"] if isinstance(x, dict) else x


def core_bounds(gf_ffl_m, egl_m, min_excavation_m, underlay_m, h_candidates_m, family, continues_above=True):
    """Bounds of one foundation core length (m), on the printed chain.

    h_candidates_m: the footing depths the support may have (one value, or several when the type is in conflict);
    underlay_m: the printed layers between formation and footing bottom, or None when not printed.
    continues_above: False for a column that STOPS in the foundation storey: its bars end in the closing ground beam /
    slab (below GF FFL by an unprinted build-up) and turn into their anchorage there, so GF FFL is not its top datum.
    Returns {"lower_m": float | None, "upper": str, "status": ..., "reason": ...}. Never a default, never 0."""
    for name, v in (("gf_ffl_m", gf_ffl_m), ("egl_m", egl_m), ("min_excavation_m", min_excavation_m)):
        if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise CoreDatumError(f"{name} must be a printed number, got {v!r}")
    if min_excavation_m < 0:
        raise CoreDatumError("min_excavation_m is a depth below the existing level (>= 0)")
    # units: every value is in metres; a villa's levels and depths are tens of metres at most (mm passed -> refused)
    for name, v in (("gf_ffl_m", gf_ffl_m), ("egl_m", egl_m), ("min_excavation_m", min_excavation_m),
                    ("underlay_m", underlay_m or 0.0), *((f"h[{i}]", h) for i, h in enumerate(h_candidates_m or ())
                                                          if isinstance(h, (int, float)))):
        if abs(v) > 50:
            raise CoreDatumError(f"{name} = {v!r} is not in metres (unit error)")
    if family == "LIFT_PIT_FF":
        return {"lower_m": None, "upper": "HELD", "status": STATUS_HELD,
                "reason": "PIT_DEPTH_NOT_PRINTED: core = GF FFL - pit floor (= FF top, p.14); pit depth to the lift "
                          "maker (D-43); FF underlay membrane thickness not printed"}
    if family == "UNBOUND":
        return {"lower_m": None, "upper": "HELD", "status": STATUS_HELD,
                "reason": "SUPPORT_NOT_BOUND: no footing bound to the column (stub / pedestal question open)"}
    if underlay_m is None:
        return {"lower_m": None, "upper": "HELD", "status": STATUS_HELD,
                "reason": "UNDERLAY_NOT_ESTABLISHED: footing bottom = formation + underlay; a core is never measured "
                          "from the formation"}
    if not h_candidates_m or any(h is None or h <= 0 for h in h_candidates_m):
        return {"lower_m": None, "upper": "HELD", "status": STATUS_HELD, "reason": "FOOTING_DEPTH_NOT_ESTABLISHED"}
    formation_limit = egl_m - min_excavation_m
    footing_top_max = formation_limit + underlay_m + max(h_candidates_m)
    lower = gf_ffl_m - footing_top_max
    if lower <= 0:
        raise CoreDatumError(f"footing top {footing_top_max:+.3f} reaches GF FFL {gf_ffl_m:+.3f}: chain inconsistent")
    out = {"lower_m": round(lower, 6), "upper": UPPER_OPEN, "status": STATUS_LOWER,
            "reason": f"formation at its printed limit {formation_limit:+.2f} + underlay {underlay_m:.2f} + H "
                      f"{max(h_candidates_m):.2f} -> footing top <= {footing_top_max:+.3f}",
            "footing_top_max_m": round(footing_top_max, 6)}
    if not continues_above:
        out.update(lower_m=None, upper="HELD", status=STATUS_HELD, core_to_gf_ffl_if_top_were_ffl_m=out["lower_m"],
                   reason="TOP_DATUM_NOT_PRINTED: the column stops in the foundation storey; its bars end in the closing "
                          "ground beam / slab, whose structural top (GF FFL minus an unprinted build-up) is not printed; the "
                          "ledger runs the core up to GF FFL, through the floor build-up, and then adds 40 D of "
                          "ANCHORAGE_TOP. Bottom end restated (footing top) as information only, never summed")
    return out


def _family(footing):
    """footing: the S3 starter's footing record (ref, depth_mm) or the core basis when no starter footing is bound."""
    ref = footing.get("ref")
    if isinstance(ref, str) and ref.startswith("FTG-FF-"):
        return "LIFT_PIT_FF", ["FF"]
    if isinstance(ref, str) and ref.startswith("FTG-CONFLICT_"):
        types = ref.split("FTG-CONFLICT_")[1].split("-")[0].split("_")
        return "P13_CONFLICT", types
    if isinstance(ref, str) and ref.startswith("FTG-"):
        return "P13_ISOLATED", [ref.split("-")[1]]
    return "UNBOUND", []


def build(main_rows=None, ls=None, chain=None):
    chain = chain or ALSENAN_CHAIN
    main_rows = main_rows if main_rows is not None else json.loads(
        (S3 / "COLUMN_MAIN_BAR_REGISTER.json").read_text(encoding="utf-8"))["rows"]
    ls = ls if ls is not None else json.loads((S3 / "COLUMN_LAP_STARTER_REGISTER.json").read_text(encoding="utf-8"))
    gf, egl, mx = _val(chain["gf_ffl_m"]), _val(chain["egl_m"]), _val(chain["min_excavation_m"])
    sched = chain["schedule_h_m"]
    starters = {r["chain_id"]: r for r in ls["rows"] if r["component"] == "STARTER"}
    found = sorted((r for r in main_rows if r["component"] == "MAIN_BARS" and r["floor"] == "FOUNDATION"),
                   key=lambda r: r["chain_id"])
    rows, findings = [], []
    for r in found:
        st = starters.get(r["chain_id"])
        ftg = (st or {}).get("footing") or {}
        fam, types = _family(ftg)
        hs = [sched.get(t) for t in types]
        # the ledger's own H (from its basis text) must be one of the schedule H of the bound types
        basis = r["interval"]["basis"]
        h_ledger = float(basis.split("footing depth")[1].split("mm")[0]) / 1000.0
        if fam in ("P13_ISOLATED", "P13_CONFLICT", "LIFT_PIT_FF"):
            if None in hs or abs(max(hs) - h_ledger) > 1e-9:
                findings.append({"chain_id": r["chain_id"], "finding": "LEDGER_H_NOT_SCHEDULE_H",
                                 "detail": f"ledger H {h_ledger} vs schedule {dict(zip(types, hs))}"})
        und = _val(chain["underlay_m"][fam])
        b = core_bounds(gf, egl, mx, und, hs if fam != "UNBOUND" else [], fam, r.get("chain_continues_above", True))
        kgm = kg_per_m(r["dia_mm"])
        n = r["count"]
        ledger_m = r["interval"]["length_mm"] / 1000.0
        ledger_kg_exact = n * ledger_m * kgm
        rec = {
            "chain_id": r["chain_id"], "type": r["type"], "bars": n, "dia_mm": r["dia_mm"],
            "kg_per_m": round(kgm, 6), "support_family": fam, "footing_ref": ftg.get("ref"), "footing_types": types,
            "h_m": hs if fam != "UNBOUND" else None,
            "ledger": {"length_m": ledger_m, "kg": r["kg"], "label": r["interval"]["state"],
                       "label_restated": "CONVENTION_NOT_A_BOUND", "implied_formation_m": round(gf - ledger_m - h_ledger
                                                                                                - und, 6)
                       if fam in ("P13_ISOLATED", "P13_CONFLICT") and und is not None else None, "basis": basis},
            "lower": b, "upper": b["upper"], "status": b["status"],
            "starter": None if st is None else {"state": st["release_state"], "length_mm": st["length_per_piece_mm"]},
        }
        if b["lower_m"] is not None:
            low_kg = n * b["lower_m"] * kgm
            rec.update(lower_length_m=b["lower_m"], lower_kg=round(low_kg, 3), lower_t=round(low_kg / 1000, 6),
                       delta_kg_vs_ledger=round(low_kg - ledger_kg_exact, 3),
                       delta_cause="ledger footing underside at -1.50 (formation -1.67); printed chain: footing "
                                   "bottom = formation + 0.17 with formation <= -1.50 -> core 0.17 m shorter at least")
        else:
            rec.update(lower_length_m=None, lower_kg=None, lower_t=None, delta_kg_vs_ledger=None,
                       delta_cause=b["reason"])
            if fam == "UNBOUND":
                hmax = max(sched.values())
                cond = core_bounds(gf, egl, mx, _val(chain["underlay_m"]["P13_ISOLATED"]), [hmax], "P13_ISOLATED")
                rec["conditional_lower_if_p13_footing"] = {"length_m": cond["lower_m"], "h_m": hmax,
                                                           "kg": round(n * cond["lower_m"] * kgm, 3),
                                                           "status": "CONDITIONAL (not used)"}
        rows.append(rec)

    # starters and laps: the datum each reuses (checked, not changed)
    st_checks, lap_checks = [], []
    for r in ls["rows"]:
        if r["component"] == "STARTER":
            f = r.get("footing") or {}
            H = f.get("depth_mm")
            exp = None if H is None else (H - ls["starter_rule"]["bottom_cover_mm"]) + ls["starter_rule"]["foot_mm"] \
                + ls["starter_rule"]["projection_D"] * r["dia_mm"]
            st_checks.append({"chain_id": r["chain_id"], "state": r["release_state"],
                              "datum": "FOOTING BODY (bottom cover from the footing underside, projection above the "
                                       "footing top); independent of the formation",
                              "length_mm": r["length_per_piece_mm"], "rule_length_mm": exp,
                              "ok": (exp is None and r["length_per_piece_mm"] is None)
                              or (exp is not None and abs((r["length_per_piece_mm"] or 0) - exp) < 0.5),
                              "delta_kg": 0.0})
        elif r["component"] == "LAP":
            lap_checks.append({"chain_id": r["chain_id"], "floor": r["floor"], "part_id": r["part_id"],
                               "datum": "STOREY JOINT (FFL above the segment)", "ok": r["part_id"].endswith("|LAP_TOP"),
                               "delta_kg": 0.0})
    by_fam = Counter(x["support_family"] for x in rows)

    def s(key, fams=None):
        return round(sum(x[key] for x in rows if x[key] is not None and (fams is None or x["support_family"] in fams)), 3)

    restated = [x for x in rows if x["lower_kg"] is not None]
    held = [x for x in rows if x["lower_kg"] is None]
    t273 = [x for x in rows if x["support_family"] in ("P13_ISOLATED", "LIFT_PIT_FF")]
    t273_formula = round(sum(-x["bars"] * 0.17 * x["kg_per_m"] for x in t273), 3)

    def _part(group, reason):
        return round(sum(-x["bars"] * 0.17 * x["kg_per_m"] for x in group if x["delta_cause"].startswith(reason)), 3)
    out = {
        "task": "T-280 (lane S): foundation column cores on the verified level chain",
        "ledger": "research/alsenan_column_rebar_s3 (read only, not edited)",
        "chain": chain, "unit_mass": UNIT_MASS,
        "rule": "R-COL-CORE-DATUM-1 (proposed): a column's foundation core starts at the footing top; footing top = "
                "formation + printed underlay + H; with the formation printed only as a limit the core has a LOWER "
                "bound (formation at the limit) and an OPEN upper bound; underlay not printed for the support -> HELD; "
                "never measured from the formation, never a ledger convention called a bound",
        "foundation_core_rows": len(rows), "by_support_family": dict(sorted(by_fam.items())),
        "ledger_kg_all": round(sum(x["ledger"]["kg"] for x in rows), 3),
        "restated_rows": len(restated),
        "ledger_kg_restated_rows": round(sum(x["ledger"]["kg"] for x in restated), 3),
        "lower_kg_restated_rows": s("lower_kg"), "lower_t_restated_rows": round(s("lower_kg") / 1000, 6),
        "delta_kg_restated_rows": s("delta_kg_vs_ledger"),
        "delta_kg_by_family": {f: s("delta_kg_vs_ledger", (f,)) for f in ("P13_ISOLATED", "P13_CONFLICT")},
        "held_rows": len(held), "ledger_kg_held_rows": round(sum(x["ledger"]["kg"] for x in held), 3),
        "held_by_reason": dict(Counter(x["delta_cause"].split(":")[0] for x in held)),
        "t273_finding_reconciled": {
            "t273_kg": -74.381, "t273_chains": 31,
            "recomputed_same_formula_kg": t273_formula,
            "rounding_residual_kg": round(-74.381 - t273_formula, 3),
            "rounding_cause": "T-273 r2 took kg/m from the ledger's row kg (rounded to 3 decimals) / total length; here "
                              "kg/m = pi/4 d^2 x 7850 unrounded (the ledger's own method)",
            "of_which_restated_p13_continuing_kg": _part(t273, "ledger footing underside"),
            "of_which_lift_ff_withdrawn_kg": _part(t273, "PIT_DEPTH_NOT_PRINTED"),
            "of_which_stopping_cn_withdrawn_kg": _part(t273, "TOP_DATUM_NOT_PRINTED"),
            "note": "T-273 r2 applied the p.13 0.17 m underlay to all 31 chains with a known footing. Withdrawn here: "
                    "the 4 lift chains on FF (p.14 prints the membrane with no thickness: FF underlay HELD, T-206 r2; "
                    "footing top = pit floor, pit depth HELD, D-43) and the 3 CN columns on p.13 footings that stop in "
                    "the foundation storey (top datum = closing member top, not printed). Added: the 2 F / F10 "
                    "conflict chains it left out, restated on max H (valid for both readings)."},
        "starters_checked": len(st_checks), "starters_ok": sum(c["ok"] for c in st_checks),
        "laps_checked": len(lap_checks), "laps_ok": sum(c["ok"] for c in lap_checks),
        "findings": findings,
        "rows": rows, "starter_checks": st_checks, "lap_checks": lap_checks,
    }
    return out


def main(argv):
    out = build()
    text = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--print" in argv:
        print(text)
        return
    OUT.write_text(text, encoding="utf-8")
    keys = ("foundation_core_rows", "by_support_family", "ledger_kg_all", "restated_rows", "ledger_kg_restated_rows",
            "lower_kg_restated_rows", "lower_t_restated_rows", "delta_kg_restated_rows", "delta_kg_by_family",
            "held_rows", "ledger_kg_held_rows", "held_by_reason", "t273_finding_reconciled", "starters_checked",
            "starters_ok", "laps_checked", "laps_ok", "findings")
    print(json.dumps({k: out[k] for k in keys}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
