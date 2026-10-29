"""T-346 builder: the freelancer's exterior plaster rows 65 / 68 / 69 (93.150 m2, 'no face drawn' in T-162 / T-337)
read as physical elements of the development villa and reconciled to the drawn faces in named parts.

    python3 -I research/agents_t346/t346_alsenan.py --write     # ROWS_T346.csv, BANDS_T346.csv, summary.json
    python3 -I research/agents_t346/t346_alsenan.py --check     # rebuild byte for byte

Inputs (committed, Checker-merged): research/agents_t337/BINDING_T337.csv (every T-305 face once, its owner line),
research/agents_t337/OPENINGS_T337.csv, tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (his E / F / H / I cells,
numbers only). Face portions are split from the plan DXF read this run (Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip -> P7757.dxf, T-159 rings): only lengths and levels are written here.

Drawing evidence for the splits (no coordinates committed):
  * the 1F NE face stands 1.500 m behind the GF NE face (printed '1500' twice on the 1F plan across the GF roof band,
    at its passage end and at its sea end, and once on the GF plan) and 1.500 m behind the GF sea face (printed
    '1500' on the 1F plan); GF NW-7 7.900 = 1.500 (its NE-band end, nothing above +6.00) + 6.400 (under 1F NW-5);
  * 1F NW-5 6.725 (+5.50 -> +9.70, parapet CAD wave 3.0134 m2), 0.325 of it over open air (slab edge HELD, Q-68 C);
  * passage face P-2 (house side, Q-67 A cond.): 4.700 m from the boundary wall's inner face; its first 1.300 m (0.100
    wall + 1.000 W10 + 0.200 wall) lies inside the 1.500 m GF roof band; the band's other 0.200 m is the boundary wall
    that closes the passage (T-123 section 3), not a house face; the GF roof slab +5.50 runs on over the passage (T-123
    section 4: 0 .. 1300 under the exposed GF roof), so no face stands at that line above +5.50.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import freelancer_rows as FR  # noqa: E402

T337 = ROOT / "research" / "agents_t337"
RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"

GF_LINE = "L-b05f70c92405dbcfbe62"
F1_LINE = "L-8bb83e16cc7b104ab88b"
PLINTH = "NEW FIN.EXT.FINISH PLINTH GF"
PAR_GF = "NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50"
PAR_1F = "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70"

NW7_BAND_END = 1.500      # GF NW-7 beyond the 1F NE face line (printed 1500)
NW7_UNDER_1F = 6.400      # 7.900 - 1.500
P2_IN_BAND = 1.300        # P-2 pieces 0.100 + 1.000 (W10) + 0.200 inside the 1.500 m band
NW5_PARAPET_M2 = 3.0134   # T-305 / T-337 (CAD wave, no printed height)


def r6(x):
    return None if x is None else f"{x:.6f}"


def binding():
    rows = list(csv.DictReader((T337 / "BINDING_T337.csv").open(encoding="utf-8")))
    return {r["key"]: r for r in rows}


def his_rows():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    out = {}
    for r in raw["rows"]:
        if r["file"] == "PLS" and r["row"] in (65, 68, 69):
            c = {k[0]: v["v"] for k, v in r["cells"].items() if k[0] in "EFHI" and isinstance(v["v"], (int, float))}
            out[r["row"]] = {"E": c.get("E", 1.0), "F": c["F"], "H": c["H"], "I": c["I"]}
    return out


def faces(B):
    """Face portions, each checked against its T-337 binding row (line and full-face area)."""
    nw5_top = 9.70 + NW5_PARAPET_M2 / 6.725
    F = {
        "NW7_END_plinth": FR.face("GF/NW-7/NE-BAND-END/plinth", NW7_BAND_END, 0.00, 1.00, line=PLINTH),
        "NW7_END_storey": FR.face("GF/NW-7/NE-BAND-END/storey", NW7_BAND_END, 1.00, 5.50, line=GF_LINE),
        "NW7_END_parapet": FR.face("GF/NW-7/NE-BAND-END/parapet", NW7_BAND_END, 5.50, 6.00, line=PAR_GF),
        "NW7_U_plinth": FR.face("GF/NW-7/UNDER-1F/plinth", NW7_UNDER_1F, 0.00, 1.00, line=PLINTH),
        "NW7_U_storey": FR.face("GF/NW-7/UNDER-1F/storey", NW7_UNDER_1F, 1.00, 5.50, line=GF_LINE),
        "NW7_U_parapet": FR.face("GF/NW-7/UNDER-1F/parapet", NW7_UNDER_1F, 5.50, 6.00, line=PAR_GF),
        "NW5_storey": FR.face("1F/NW-5/STOREY/storey", 6.725, 5.50, 9.70, line=F1_LINE),
        "NW5_parapet": FR.face("1F/NW-5/PARAPET/parapet", 6.725, 9.70, nw5_top, line=PAR_1F),
        "P2_plinth": FR.face("GF/P-2/NE-BAND-1.30/plinth", P2_IN_BAND, 0.15, 1.00, line=PLINTH),
        "P2_storey": FR.face("GF/P-2/NE-BAND-1.30/storey", P2_IN_BAND, 1.00, 5.50, line=GF_LINE),
    }
    # closure against T-337 (Checker-merged): the portions add up to the bound faces, on the bound lines
    chk = [("GF/NW-7/EDGE/plinth", ("NW7_END_plinth", "NW7_U_plinth")),
           ("GF/NW-7/EDGE/storey", ("NW7_END_storey", "NW7_U_storey")),
           ("GF/NW-7/EDGE/parapet", ("NW7_END_parapet", "NW7_U_parapet")),
           ("1F/NW-5/STOREY/storey", ("NW5_storey",)), ("1F/NW-5/PARAPET/parapet", ("NW5_parapet",))]
    closure = []
    for key, parts in chk:
        b = B[key]
        mine = sum(FR.face_m2(F[p]) for p in parts)
        bound = float(b["hi"])
        if abs(mine - bound) > 1e-4:
            raise FR.RuleError(f"{key}: portions {mine} vs T-337 {bound}")
        for p in parts:
            if F[p]["line"] != b["line"]:
                raise FR.RuleError(f"{key}: line {F[p]['line']} vs T-337 {b['line']}")
        closure.append((key, b["line"], bound, mine, mine - bound))
    # P-2: a portion of the 4.700 m face, same bands and lines
    for key, p in (("GF/P-2/COVERED/plinth", "P2_plinth"), ("GF/P-2/COVERED/storey", "P2_storey")):
        b = B[key]
        if (float(b["bottom"]), float(b["top"])) != (F[p]["lo"], F[p]["hi"]) or F[p]["line"] != b["line"]:
            raise FR.RuleError(f"{key}: band or line differs from T-337")
        whole = float(b["hi"])
        closure.append((key + " (1.300 of 4.700 m)", b["line"], whole, FR.face_m2(F[p]), None))
    return F, closure


def build():
    B = binding()
    F, closure = faces(B)
    H = his_rows()
    L = FR.Ledger()
    # row 68: the GF sea face's 1.50 m at the NE band's end (nothing above its +6.00 parapet)
    L.match(68, H[68]["I"], [F["NW7_END_plinth"], F["NW7_END_storey"], F["NW7_END_parapet"]],
            H[68]["H"], 0.00, H[68]["F"], "GF NW-7 NE-band end 1.50 m, +-0.00 -> +6.00")
    # row 69: GF NW-7 under the 1F + 1F NW-5 as one plane from +1.00 (his practice, as row 64)
    L.match(69, H[69]["I"], [F["NW7_U_storey"], F["NW7_U_parapet"], F["NW5_storey"], F["NW5_parapet"],
                             F["NW7_U_plinth"]],
            H[69]["H"], 1.00, 1.00 + H[69]["F"],
            "sea face: GF NW-7 6.40 m under the 1F + 1F NW-5 6.725 m, one plane +1.00 -> +10.80")
    # row 65: the two end returns of the 1.50 m GF roof band along the NE face
    half = H[65]["H"] * H[65]["F"]
    L.double_count(65, half, "GF/NW-7/NE-BAND-END/storey",
                   "NW end return = the same GF NW-7 1.50 m portion as row 68")
    L.match(65, half, [F["P2_plinth"], F["P2_storey"]], H[65]["H"], 0.00, H[65]["F"],
            "SE end return at the passage: P-2 first 1.30 m (+0.15 -> +5.50) + 0.20 boundary wall, roof runs on")
    st = L.statement({r: H[r]["I"] for r in (65, 68, 69)})
    return L, st, H, closure


CAUSE = {
    (69, 1.00, 5.50): "width: his 6.75 against GF NW-7 6.40 under the 1F",
    (69, 5.50, 6.00): "one plane hides the 0.50 m band where the GF parapet stands 1.50 m in front of the 1F face",
    (69, 6.00, 9.70): "width: his 6.75 against 1F NW-5 6.725",
    (69, 9.70): "width over the drawn parapet mean height",
    (69, "top"): "height: his top +10.80 (6.75 x 9.80 from +1.00) above the CAD wave's mean top; +10.80 is not printed",
    (65, 0.00, 0.15): "his +-0.00 against the passage floor +0.15",
    (65, 0.15, 1.00): "0.20 m of his 1.50 is the boundary wall closing the passage (no house face, Q-65 C)",
    (65, 1.00, 5.50): "0.20 m of his 1.50 is the boundary wall closing the passage (no house face, Q-65 C)",
    (65, 5.50, 6.00): "the GF roof slab runs on over the passage (T-123): no face at that line above +5.50",
}


def cause(row, a, b, dw):
    if row == 69 and a >= 9.70 and dw == 0:
        return CAUSE[(69, "top")]
    if row == 69 and a >= 9.70:
        return CAUSE[(69, 9.70)]
    return CAUSE.get((row, round(a, 2), round(b, 2)), "")


def outputs():
    L, st, H, closure = build()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["his_row", "his_cells", "part", "kind", "his_m2", "drawn_m2_in_his_band", "drawn_m2_outside_his_band",
                "named_terms_m2", "faces", "owner_lines", "classification", "verdict_proposal"])
    cls = {
        (68, "MATCHED"): ("drawn face already bound once in T-337 (GF storey line, PLINTH, PARAPET-OUTER GF): "
                          "no new T-314 FILL row", "MAPPED (agrees 0.000 m2)"),
        (69, "MATCHED"): ("drawn faces already bound once in T-337 (GF storey line, PARAPET-OUTER GF, 1F storey line, "
                          "PARAPET-OUTER 1F; plinth below his band in PLINTH): no new T-314 FILL row",
                          "RULE_DIFFERENCE (one plane for set-back faces, as row 64) + his height UNRESOLVED (+10.80 "
                          "not printed)"),
        (65, "DOUBLE_COUNT"): ("double count in his sheet: no face, no FILL row", "ENGINE_RIGHT (the face once)"),
        (65, "MATCHED"): ("drawn face already bound once in T-337 (P-2, GF storey line and PLINTH; Q-67 A cond.): no "
                          "new T-314 FILL row; the 0.20 m boundary wall part is OTHER_TRADE (Q-65 C)",
                          "RULE_DIFFERENCE (datum +-0.00, boundary wall thickness, height to +6.00 over a "
                          "continuous roof)"),
    }
    lines_of = {}
    for p in L.parts:
        h = H[p["row"]]
        cells = f"E{h['E']} F{h['F']} H{h['H']} = {h['I']:.4f}"
        c, v = cls[(p["row"], p["kind"])]
        w.writerow([p["row"], cells, p["name"], p["kind"], r6(p["his_m2"]), r6(p["drawn_m2"]),
                     r6(p["drawn_outside_his_band_m2"]), r6(p["residual_terms_m2"]), "; ".join(p["faces"]),
                     "; ".join(p.get("lines", [])), c, v])
    rows_csv = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["his_row", "band_bottom", "band_top", "his_width_m", "drawn_width_m", "his_minus_drawn_m2", "cause"])
    for p in L.parts:
        for a, b, hw, dw, d in p["bands"]:
            w.writerow([p["row"], r6(a), r6(b), r6(hw), r6(dw), r6(d), cause(p["row"], a, b, dw)])
    bands_csv = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["t337_key", "line", "t337_m2", "portions_m2", "difference_m2"])
    for k, line, b, m, d in closure:
        w.writerow([k, line, r6(b), r6(m), r6(d)])
    closure_csv = s.getvalue()
    summ = {
        "task": "T-346",
        "rows": {str(r): H[r]["I"] for r in (65, 68, 69)},
        "statement_m2": {k: round(v, 6) for k, v in st.items()},
        "new_t314_fill_rows": 0,
        "t162_drawn_faces_in_no_row_m2": {"before": 210.761, "now_in_rows_68_69": 47.400,
                                         "now_in_row_65": 6.955, "after": round(210.761 - 47.400 - 6.955, 3)},
        "t162_rows_70_71_74_lose_nw5_m2": 31.2584,
        "his_walls_net_of_half_openings_m2": {"t337": 935.365, "less_double_count": round(935.365 - 9.0, 3)},
        "drawing_net_m2": [897.720, 938.606],
    }
    return {"ROWS_T346.csv": rows_csv, "BANDS_T346.csv": bands_csv, "CLOSURE_T346.csv": closure_csv,
            "summary.json": json.dumps(summ, indent=1, sort_keys=True) + "\n"}


def main(argv):
    out = outputs()
    if "--write" in argv:
        for n, t in out.items():
            (HERE / n).write_text(t, encoding="utf-8")
    elif "--check" in argv:
        bad = [n for n, t in out.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-346 rebuild:", "identical" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    print(json.dumps(json.loads(out["summary.json"])["statement_m2"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
