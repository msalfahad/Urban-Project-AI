"""T-550 development-villa run (research, unwired): the T-543 B9 table restated with its UNRESOLVED 101.43 m2 taken to
physical causes (R-T550-1 for the parapet rows), H1 measured on the drawings.

    .work/venv/bin/python -I research/agents_t550/t550_alsenan.py [--write]

Reads merged repository files only (research/agents_t543 inputs and table) plus the drawing readings recorded in
DRAWING_READINGS below (numbers and entity handles only: no coordinate, no drawing content, no client data).
--write stores out/T550_UNRESOLVED_RESTATED.json.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
T543 = HERE.parent / "agents_t543"
for p in (HERE, T543):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t543_alsenan as A  # noqa: E402
import t543_inputs as I  # noqa: E402
import t550_parapet_split as P  # noqa: E402

OUT = HERE / "out" / "T550_UNRESOLVED_RESTATED.json"

# ---- drawing readings this run (metres relative to the printed finished level of each roof) --------------------------
DRAWING_READINGS = {
    "DWF SECTION A-A (t550_section_parapets.py on the architectural .dwf, datum by 4 level markers, spread 1.8 mm)": {
        "+5.50 parapet": "hatch +0.499 .. -0.549 (top 0.50 above finish; hatched edge member to 0.55 below finish)",
        "+13.90 parapet": "hatch +0.50 .. -0.55; outline vertical up to +0.50",
        "+9.70 parapet (cut run)": "hatch +1.599 .. -0.549",
        "slab band (t214 section_bands.py)": "build-up line 0.05 below each level, hatch 0.05 .. 0.20 below it",
    },
    "DWF SECTION B-B": {
        "+4.30 annex parapets": "hatch top +0.499; bottoms -0.468 / -0.551 / -1.099 (edge members of two depths)",
    },
    "P7757.dxf NORTH WEST ELEVATION (cut at the +5.50 terrace edge)": {
        "lines": "27E2 layer 5 at +5.50 (finished level); 27E5 +5.45 (hatched slab top); 27E4 +5.30 (soffit); "
                 "27E6 +4.95 (edge member bottom); 27E3 +6.00 (parapet top); hatch 27D1 +4.95 .. +6.00",
        "printed": "dimension 29D0 5500 (+-0.00 to +5.50) and 29DE 500 (parapet above +5.50)",
    },
    "P7757.dxf SOUTH EAST ELEVATION (annex +4.30 edge)": {
        "lines": "241A layer 5 at +4.30; 2419 / 241D +4.25 (slab top); 241C +4.10; 241E +3.75 (edge member bottom); "
                 "241B +4.80 (parapet top); hatch 1C01 +3.75 .. +4.80; dimension 24BC 500",
    },
}
H1 = ("MEASURED: his parapet heights are the printed heights above the finished roof plus 0.50 m on every row: "
      "1.00 = 0.50 + 0.50 (GF / annex chain), 1.80 = 1.30 + 0.50 (1F roof), 1.00 = 0.50 + 0.50 (+13.90 roof). The "
      "architect's cuts draw the hatched edge member to 0.55 m below the finished level (0.50 m below the hatched slab "
      "top) on the +4.30, +5.50, +9.70 and +13.90 roofs; the drawn roof layer is a constant 0.05 m (refused as a roof "
      "build-up, T-214). So his +0.50 is the edge-member depth below the slab top, not the roof build-up b_edge; "
      "T-543's '+0.63 on the 1F roof' was his 1.80 against the engine's MEAN run height 1.171 m: the printed nominal "
      "is 1.30 (elevation dimensions 130), the 0.13 is the per-run printed heights (NW-5 0.448, SE-1 1.041, ...).")
BELOW_FINISH = ("the face below the finished roof is concrete in every printed alternative: architect's cuts hatch the "
                "edge member to -0.55 m (DWF A-A / B-B; P7757.dxf 27D1 / 1C01), and ST p.14 P1 puts an RC upstand "
                "above the slab top 'more than the height of roof finishing' (T-311 / T-319): beam lines own the "
                "member to the slab top, STR.CONC.PARAPET (HELD) the upstand")

CHAINS = {   # his row -> engine chains, his length m, his height m, printed nominal height above finish m
    "GF+ANNEX (his 1F-page row 'الدروه' 66.00 x 1.00)": (("ANNEX", "GF"), "66.00", "1.00", "0.50"),
    "1F ROOF +9.70 (his roof-page row 'الدروه' 42.85 x 1.80)": (("1F",), "42.85", "1.80", "1.30"),
    "+13.90 ROOF (his roof-page unlabelled row 29.80 x 1.00)": (("2F",), "29.80", "1.00", "0.50"),
}
LENGTH_CAUSE = {
    "+13.90 ROOF (his roof-page unlabelled row 29.80 x 1.00)": (
        "RULE_DIFFERENCE", "his 29.80 = 2 x (8.10 + 6.80), the printed OUTER dimensions of the +13.90 roof; the engine "
                           "measures the 0.20 / 0.15 parapet on its centreline 29.050 m (T-311 / T-541)"),
    "1F ROOF +9.70 (his roof-page row 'الدروه' 42.85 x 1.80)": (
        "UNRESOLVED", "his 42.85 m is 6.383 m short of the drawn 1F chain 49.233 m; the chain minus NW-5 (6.625 m, the "
                      "low 0.448 m run) is 42.608 m (+0.242 m to his): consistent with omitting NW-5, not proven "
                      "(his row names no run)"),
    "GF+ANNEX (his 1F-page row 'الدروه' 66.00 x 1.00)": (
        "UNRESOLVED", "his 66.00 m exceeds the drawn annex + GF terrace chains 58.555 m (outer faces about 59.4 m) by "
                      "7.445 m; no further parapet run is drawn at +4.30 / +5.50 (layer 5 runs, T-311 / T-324)"),
}
PROJECTIONS_NOTE = (
    "his row 7.50 x 5.50, booked on his 1F external-walls page, no opening. 5.50 = the printed +-0.00 to +5.50 "
    "dimension (NW elevation 29D0); the only 7.50 printed is the GF plan dimension 4E9 along the sea-side SALOON "
    "facade, a run of 0.70 m wall + a 6.33 m glazed opening (window layer W, 262 / 263 / 264 / 265, 6.232 m) + 0.47 m "
    "wall (P7757.dxf B5 / B6). No 7.50 x 5.50 masonry face exists on any of the four elevations or the two sections; "
    "candidates checked: NW pool-court arch frame (T-172), SE stair-tower frame, the SW 1F overhang (about 4.5 m). "
    "Stays UNRESOLVED (physical element not identified; if it is that facade it is mostly glazing).")
OPENINGS_NOTE = (
    "rows l (per floor -16.444) + his unassigned 20 cm openings (-9.84): his 122.39 m2 vs engine 96.106 m2. Named "
    "parts that cannot be moved to a number: (1) door height: he takes every door at 2.40 m (25.40 m of door width), "
    "the engine the owner fallback 2.20 m where no head is printed (Q-55 C): at most 25.40 x 0.20 = 5.08 m2; (2) HELD "
    "openings (lift L-*, arch A-*, panel P-*, D-GF-07 / D-GF-14) are not deducted by the engine but sit inside the "
    "HELD wall figures of row d, while he deducts them: their sizes are HELD, so the coupling is named, not moved; "
    "(3) his 4 openings in the 20 cm section (3 x 1.00 + 1.10 at 2.40) name no floor. Matching his openings to engine "
    "walls one by one is not done here.")


def engine_runs(chains: tuple) -> list[dict]:
    out = []
    for r in I.parapet_runs():
        if r["chain"] not in chains:
            continue
        out.append({"run": f"{r['chain']}:{r['run']}", "centreline_m": r["centreline_hi"], "h_m": r["h_hi"],
                    "h_datum": "FINISH", "h_status": "HELD" if r["h_status"].startswith("HELD") else "PRINTED"})
    return out


def build() -> dict:
    base = A.build()
    par = next(r for r in base["rows"] if r["name"].startswith("parapets"))
    old = [x for x in par["decomposition"]["rows"] if x["name"].startswith("RESIDUAL: parapet")]
    assert len(old) == 1
    old_resid = Decimal(old[0]["delta"])
    splits, new_rows = [], []
    for name, (chains, Lh, Hh, hn) in CHAINS.items():
        cause, basis = LENGTH_CAUSE[name]
        s = P.split_chain(chain=name, his_length_m=Lh, his_height_m=Hh, printed_nominal_h_m=hn,
                          runs=engine_runs(chains), below_finish_evidence=BELOW_FINISH, length_cause=cause,
                          length_basis=basis)
        splits.append(s)
        new_rows += s["rows"]
    new_sum = sum(Decimal(x["delta"]) for x in new_rows)
    assert new_sum == old_resid, (new_sum, old_resid)           # the split closes T-543 row 5d exactly
    # restated by-cause totals of the whole B9 table
    bc = {k: Decimal(v) for k, v in base["by_cause"].items()}
    bc["UNRESOLVED"] -= old_resid
    for k, v in P.by_cause(new_rows).items():
        bc[k] = bc.get(k, Decimal(0)) + Decimal(v)
    assert sum(bc.values()) == Decimal(base["gap"])
    unresolved_named = []
    for r in base["rows"]:
        dec = r["decomposition"]
        items = dec["rows"] if dec else [{"name": r["name"], "delta": r["difference_m2"], "cause": r["cause"]}]
        for x in items:
            if x["cause"] == "UNRESOLVED" and not x["name"].startswith("RESIDUAL: parapet"):
                unresolved_named.append({"part": f"{r['name']} / {x['name']}", "m2": x["delta"]})
    for x in new_rows:
        if x["cause"] == "UNRESOLVED":
            unresolved_named.append({"part": x["name"], "m2": x["delta"], "basis": x["basis"]})
    u = sum(Decimal(x["m2"]) for x in unresolved_named)
    assert u == bc["UNRESOLVED"], (u, bc["UNRESOLVED"])
    return {"method": "R-T550-1 on R-T543-1", "candidate": base["candidate"], "freelancer_total": base["freelancer_total"],
            "engine_valued_total": base["engine_valued_total"], "gap": base["gap"],
            "t543_by_cause": base["by_cause"], "restated_by_cause": {k: str(v) for k, v in sorted(bc.items())},
            "t543_unresolved": base["by_cause"]["UNRESOLVED"], "parapet_residual_t543": str(old_resid),
            "parapet_split": splits, "unresolved_after": unresolved_named,
            "unresolved_after_gross_abs_m2": str(sum(abs(Decimal(x["m2"])) for x in unresolved_named)),
            "H1": H1, "below_finish_evidence": BELOW_FINISH, "drawing_readings": DRAWING_READINGS,
            "projections_note": PROJECTIONS_NOTE, "openings_note": OPENINGS_NOTE}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    res = build()
    print("gap", res["gap"], "T-543 UNRESOLVED", res["t543_unresolved"], "parapet residual", res["parapet_residual_t543"])
    for s in res["parapet_split"]:
        print(" ", s["chain"], "his", s["his_m2"], "face", s["engine_face_m2"], "diff", s["difference_m2"])
        for x in s["rows"]:
            print(f"      {Decimal(x['delta']):>12.4f} {x['cause']:<16} {x['name'][:90]}")
    print("restated by cause:", res["restated_by_cause"])
    for x in res["unresolved_after"]:
        print(f"  UNRESOLVED {Decimal(x['m2']):>10.4f}  {x['part'][:110]}")
    print("unresolved gross |m2|", res["unresolved_after_gross_abs_m2"])
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(HERE.parents[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
