"""T-667 development villa (Alsenan): the pool blinding (a NEW STR.CONC.BLINDING line, missing from V3.0.61; T-659
MISSING item) and the pool steps (L-b62a7065, HELD), with the one-element-once check against every existing blinding
line. Reads only committed files (inputs pinned by sha256); the drawing reads of this run are in
ALSENAN_POOL_BLINDING_INPUT.json (values only). No line of the candidate is changed here; wiring is a lane I row.

Run: python -I research/agents_t667/t667_alsenan.py  -> research/agents_t667/out/T667_LEDGER.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t659"))
import t667_rules as R  # noqa: E402
import t659_rules as R659  # noqa: E402

INPUT = HERE / "ALSENAN_POOL_BLINDING_INPUT.json"
LINE_INDEX = ROOT / "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
PINS = {LINE_INDEX: "10e5f116d30af67f"}
OUT = HERE / "out/T667_LEDGER.json"
TOL = Decimal("0.000002")

L_PITS = "L-98eb2d58075c9eddf1b4"
L_STEPS = "L-b62a7065645589011141"
NEW_LINE = "NEW:STR.CONC.BLINDING:POOL-1"          # id assigned by the integration row (hub), not here
NEW_ELEMENT = "P-C:PLAIN_CONCRETE:POOL:BLINDING_UNDER_POOL_BASE"
HELD_BLINDING = {   # the 6 HELD blinding lines of V3.0.61 and why the pool blinding does / does not touch each
    "L-16b95607fc88cda3844a": ("FF lift raft", "NOT TOUCHED: the lift raft outline 1B2B is not within 1 m of the pool "
                               "(own read: footing outlines within 1 m are F8, F4, FN, F9 only)"),
    "L-10032bf9a60368473a7b": ("beyond the plot line (footings)", "NOT TOUCHED, SAME ITEM: the pool's own strip beyond "
                               "the plot line (back wall on it) 0.037 m3 is a pool piece, reported beside under the "
                               "same designer item D-14; it is not added to this footing line"),
    "L-080c97f5f6a92452cd04": ("F10 + F", "NOT TOUCHED: F10 / F are not within 1 m of the pool"),
    "L-35382b18e2e362df3ae6": ("straps", "NOT TOUCHED: no strap line within 1 m of the pool on the foundation plan (only axes, plot line, columns 0.4911 m)"),
    "L-7a5214a334ea3559fa2d": ("ground beams", "NOT TOUCHED: nearest ground-beam line 0.4998 m from the pool outline "
                               "(curved beam round the pool); pool apron 0.10 + strip projection 0.10 leave 0.30 m clear; "
                               "a touch needs an undimensioned pool projection > 0.2998 m (flagged)"),
    "L-d0313e5d204e2758996a": ("boundary-wall base", "NOT TOUCHED: on the ground-beams plan the boundary band 7FE stops "
                               "at the pool corners (0.001 m along the 3.50 m back): the pool back wall replaces the "
                               "band there; no pad drawn under the pool"),
}


def _sha(p: Path, n=16) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:n]


def check_pins():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise R.Refused(f"{p.name}: sha {_sha(p)} is not the pinned {s} (stale input)")


def close(a, b, what, tol=TOL):
    if abs(Decimal(str(a)) - Decimal(str(b))) > tol:
        raise R.Refused(f"{what}: {a} vs {b}")


def lines_now():
    d = json.loads(LINE_INDEX.read_text())
    return {l["line_id"]: l for l in d["lines"]}


def build(inp=None):
    check_pins()
    inp = inp or json.loads(INPUT.read_text())
    pr, g = inp["printed"], inp["geometry_read"]
    o = R.outline("D", r=R.dim(*pr["outline"]["r"]), b=R.dim(*pr["outline"]["b"]))
    t = R.dim(*pr["blinding_t"])
    layers = [tuple(x) for x in pr["wrap_layers"]]
    proj = pr["projection_beyond_wrap"]
    piece = R.pool_blinding(o, t, layers, pr["floor"], edges_on_plot=("back",),
                            projection=None if proj[0] is None else proj,
                            counted_overlap_m2=g["pit_layer_union_over_pool_grown_in_plot_m2"], counted_line=L_PITS,
                            outline_clash_m2=sum(g["footing_outline_over_pool_outline_m2"].values()))
    # the analytic plan agrees with the own DXF read and with the Checker-re-measured T-597 envelope
    close(o["A"], g["pool_outline_area_m2"], "outline area analytic vs DXF")
    close(o["P"], g["pool_outline_perimeter_m"], "perimeter analytic vs DXF")
    close(piece["own_layer_in_plot_m2"], g["pool_grown_inside_plot_m2"], "grown in plot analytic vs DXF")
    close(piece["own_layer_in_plot_m2"], inp["cross_checks"]["T597_pool_envelope_in_plot_m2"][0], "vs T-597 envelope")
    close(piece["beyond_plot_m2"], g["pool_grown_beyond_plot_m2"], "beyond plot analytic vs DXF")
    close(sum(Decimal(str(v)) for v in g["pit_layer_over_pool_grown_in_plot_m2"].values()),
          g["pit_layer_union_over_pool_grown_in_plot_m2"], "pit pieces = union (no mutual overlap)")
    close(g["pit_layer_union_over_pool_grown_in_plot_m2"],
          inp["cross_checks"]["T597_pits_share_given_to_pool_envelope_m2"][0], "vs T-597 pits share")
    if g["frame_check_columns_inside_a_footing"][0] != g["frame_check_columns_inside_a_footing"][1]:
        raise R.Refused("frame shift not proven: a column of the ground-beams frame falls outside every footing")

    now = lines_now()
    if any(l["item_code"] == "STR.CONC.BLINDING" and "POOL" in l["element_id"] for l in now.values()):
        raise R.Refused("a pool blinding line already exists in V3.0.61: integrate, do not add")
    for lid in list(HELD_BLINDING) + [L_PITS, L_STEPS]:
        if lid not in now:
            raise R.Refused(f"{lid} not in V3.0.61")

    src = [pr["blinding_t"][1], pr["wrap_layers"][0][2], pr["wrap_layers"][1][2], pr["outline"]["r"][1],
           pr["floor"]["basis"]]
    blinding = R659.component(
        NEW_LINE, "STR.CONC.BLINDING", NEW_ELEMENT, "LOWER_ONLY", low=piece["plan_distinct_m3"],
        low_basis="DRAWING-CONFIRMED plan: base outline (D 3.50 x 1.75 + half circle r 1.75) grown by the printed "
                  "5 + 5 cm wrap, inside the plot, net of the VERIFIED pit blinding layer (one layer in plan) x 0.10",
        item="(1) projection beyond the wrap drawn, not dimensioned (ST p.7 N.I.S.; consultant C4); (2) founding "
             "levels of F8 / F4 / FN vs the pool formation -1.50 not printed (C6): one layer or two",
        beside=[{"what": "own layer in plot (footings deeper: both layers cast)", "m3": piece["own_layer_in_plot_m3"],
                 "status": "DRAWING-CONFIRMED plan, AT_LEAST (projection open)"},
                {"what": "beyond the plot line (back wall on it): strip 3.50 + 2 x 0.10 mitred", "m3": piece["beyond_plot_m3"],
                 "status": "existence open (same item as D-14); not in the line"},
                {"what": "T-183 B (grown, not clipped)", "m3": "1.222", "status": "superseded by the plot clip"}],
        sources=src)
    steps = R.steps_line([])
    steps_row = R659.component(L_STEPS, "STR.CONC.POOL", now[L_STEPS]["element_id"], "HELD_BLANK", item=steps["item"],
                               beside=[{"what": "freelancer row 'pool steps' 0.30 x 2.00 x 0.38", "m3": "0.228",
                                        "status": "his sizes, not drawn: RULE_DIFFERENCE (scope added), not a bound"}],
                               sources=[pr["steps"]])
    totals = R659.ledger_totals([blinding, steps_row])
    touches = [{"line_id": k, "what": v[0], "class_v3061": now[k]["class"], "held_low": now[k]["held_low"],
                "held_high": now[k]["held_high"], "touch": v[1]} for k, v in HELD_BLINDING.items()]
    touches.append({"line_id": L_PITS, "what": "24 pits (VERIFIED, released in the candidate)",
                    "class_v3061": now[L_PITS]["class"], "measured_net": now[L_PITS]["measured_net"],
                    "touch": "SHARES PLAN, NOT CHANGED: its grown layer covers 2.695761 m2 of the pool blinding plan "
                             "(F8 1.931845, F4 0.735358, FN 0.028558); the pool line nets it at its low end; the "
                             "footing outlines F8 + F4 clash with the pool outline by 1.578973 m2 (interface C6)"})
    return {"schema": "URBAN_T667_LEDGER_V1", "task": "T-667", "candidate_base": "ARCH_TAKEOFF_V3.0.61 line index",
            "input_sha16": _sha(INPUT), "piece": piece, "rows": [blinding, steps_row], "totals": totals,
            "existing_blinding_lines": touches,
            "before_after_m3": {"pool blinding": {"before": "MISSING (no line)",
                                                  "after": f"HELD LOWER_ONLY >= {piece['plan_distinct_m3']}",
                                                  "own_layer": piece["own_layer_in_plot_m3"]},
                                "pool steps": {"before": "HELD blank", "after": "HELD blank (item named)"}},
            "freelancer": {"pool blinding": "no row; his blinding is one plate 47.055 m3 = plot 31.37 x 15.00 x 0.10 "
                                            "(T-478): NOT_LIKE_FOR_LIKE", "pool steps": "0.228 m3, not drawn"}}


def main():
    res = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    p = res["piece"]
    print("pool blinding: low", p["plan_distinct_m3"], "own layer", p["own_layer_in_plot_m3"], "beyond", p["beyond_plot_m3"])


if __name__ == "__main__":
    main()
