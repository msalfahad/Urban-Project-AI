"""T-416 Alsenan run: every ground-beam band of the GROUND BEAMS PLAN against the candidate's 58 ground-beam lines,
frame by frame, and the T-391 GB-MAIN length term (-3.007980 m3) split by R-T416-4.

    .work/venv/bin/python -I research/agents_t416/t416_alsenan.py                       # check summary_t416.json
    .work/venv/bin/python -I research/agents_t416/t416_alsenan.py --write               # rebuild it
    .work/venv/bin/python -I research/agents_t416/t416_alsenan.py \
        --freelancer "<.work/private>/<concrete + rebar workbook>.xlsx" --out <checkout>/.work/private/t416   # private

Inputs: ALSENAN_T416_INPUT.json (t416_extract.py, own read of the structural DXF by handle), the candidate ground-beam
lines as T-391 bound them (research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json with the V3.0.29 downgrades; the 58
ids are those of V3.0.35: V3.0.30 .. V3.0.35 moved no STR.CONC.GROUND_BEAM line, per the merged T-397 / T-399 / T-400
statements), research/agents_t391/summary_t391.json (the length term). The freelancer workbook is read only with
--freelancer and only in the private step: his two lump lengths and his one section stay in --out; the summary carries
engine-side figures, terms in m3 and the position tests only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t391"))
import t416_rules as R  # noqa: E402

INPUT = HERE / "ALSENAN_T416_INPUT.json"
SUMMARY = HERE / "summary_t416.json"
T391 = ROOT / "research" / "agents_t391" / "summary_t391.json"

# own band (face-line pair) -> engine bands (T-289 BAND_PAIRING run handles; the four no-run / three-handle bands by
# their face handles: 114+115+7DF = two own bands, 0037.1 / 0038 / 0039 = the three oblique pairs, 0013.1 = the 0.1 m
# sliver the engine keeps beside column 211 at the annex arc)
BINDING = {
    "170+7C3": ["BAND0001.1", "BAND0001.2", "BAND0001.3", "BAND0001.4"], "185+7C7": ["BAND0002.1"],
    "15D+7C8": ["BAND0003"], "10A+7C9": ["BAND0004.1"], "145+7CA": ["BAND0005.1"],
    "109+7CB": ["BAND0006.1", "BAND0006.2", "BAND0006.3"], "15C+7CC": ["BAND0007"],
    "177+7CD": ["BAND0008.1", "BAND0008.2"], "107+7CE": ["BAND0009"],
    "184+7CF": ["BAND0010.1", "BAND0010.2", "BAND0010.3"],
    "FC+7D0": ["BAND0011.1", "BAND0011.2", "BAND0011.3", "BAND0011.4"], "10B+7D1": ["BAND0012.1", "BAND0012.2"],
    "13D+7D2": ["BAND0013.2"], "ARC:139+13A": ["BAND0042", "BAND0013.1"], "13F+7D3": ["BAND0014"],
    "F8+7D4": ["BAND0015"], "136+7D5": ["BAND0016"], "13E+7D6": ["BAND0017.1", "BAND0017.2"],
    "140+7D7": ["BAND0018"], "142+7D8": ["BAND0019"], "13C+7D9": ["BAND0020"], "141+7DA": ["BAND0021"],
    "178+7DB": ["BAND0022"], "7DC+7DD": ["BAND0023"], "175+7DE": ["BAND0024"], "114+7DF": ["BAND0025.1"],
    "114+115": ["BAND0025.2"], "FD+7E0": ["BAND0026.1"], "7E1+7E2": ["BAND0027"], "17C+7E3": ["BAND0028"],
    "17D+7E4": ["BAND0029"], "17B+7E5": ["BAND0030"], "176+7E6": ["BAND0031"], "7E7+7E8": ["BAND0032"],
    "7E9+7EA": ["BAND0033"], "16F+7FF": ["BAND0034"], "137+138": ["BAND0035"], "15E+15F": ["BAND0036.1"],
    "17E+17F": ["BAND0037.1"], "180+181": ["BAND0038"], "182+183": ["BAND0039"], "180D+180E": ["BAND0040"],
    "1811+1812": ["BAND0041"], "ARC:157+158": ["BAND0043"],
}
B_OTHER, D_OTHER = 0.30, 0.60      # the other side's one section on both lumps (T-391 s.3, his rows 13 / 14)


def load_engine():
    import t391_alsenan as A
    _gs, gb, held = A.load_engine()
    runs = {r["id"]: r for r in A.beam_runs(gb, held)}
    out = {}
    for ln in gb:
        band = ln["element_id"].split(":")[-1]
        r = runs[ln["line_id"]]
        out[band] = {"line_id": ln["line_id"], "length_m": ln["dimensions"]["length_m"],
                     "net_plan_m2": ln["dimensions"]["net_plan_m2"], "state": r["state"],
                     "value_m3": r["value_m3"], "D_m": round(r["D_m"], 4) if r["state"] == "VALUED" else None,
                     "D_print_m": printed_depth(r["value_m3"], ln["dimensions"]["net_plan_m2"])
                     if r["state"] == "VALUED" else None,
                     "group": r["group"]}
    return out


def band_rows(inp, eng):
    rows = []
    bound = set()
    for b in inp["bands"]:
        f = b["frames"]
        cuts = [{"id": c["handle"], "kind": "COLUMN", "a_m": c["a_m"], "b_m": c["b_m"]} for c in f["GBP"]["columns"]]
        cuts += [{"id": c["handle"], "kind": "RING", "a_m": c["a_m"], "b_m": c["b_m"]} for c in b["supports"]["rings"]]
        cuts += [{"id": j["band"], "kind": "JUNCTION", "a_m": j["a_m"], "b_m": j["b_m"]}
                 for j in b["supports"]["junctions"] if not j["owned_here"]]
        n = R.net_of_supports(b["drawn_m"], cuts)
        if abs(n["net_m"] - f["GBP"]["net_m"]) > 0.0002:
            raise SystemExit(f"{b['id']}: rule net {n['net_m']} != extract net {f['GBP']['net_m']}")
        rng = R.frame_range({k: f[k]["net_with_end_faces_m"] for k in ("GBP", "FP", "CAP", "GFRS")})
        ends = [{"m": e["m"], "shared": e["stop"] == "THROUGH"} for e in (b["end_support_m"] or []) if not e["ring"]]
        rd = R.readings(n["net_m"], b["drawn_m"] - n["net_m"], ends)
        lines = [dict(eng[x], band=x) for x in BINDING[b["id"]]]
        bound |= set(BINDING[b["id"]])
        e_len = sum(x["length_m"] for x in lines)
        e_plan_len = sum(x["net_plan_m2"] for x in lines) / 0.30
        cols = {k: [(c["handle"], c["m"]) for c in f[k]["columns"]] for k in ("GBP", "FP", "CAP", "GFRS")}
        rows.append({
            "band": b["id"], "dir": b["dir"], "width_m": b["width_m"], "drawn_m": b["drawn_m"],
            "columns_by_frame_m": cols,
            "net_by_frame_m": {k: f[k]["net_with_end_faces_m"] for k in ("GBP", "FP", "CAP", "GFRS")},
            "end_columns": b["end_columns"],
            "net_range_m": rng, "net_cut_by_kind_m": n["by_kind"],
            "end_supports": b["end_support_m"], "readings_m": rd,
            "engine_lines": [{"line_id": x["line_id"], "band": x["band"], "length_m": x["length_m"],
                              "state": x["state"], "D_print_m": x["D_print_m"], "value_m3": x["value_m3"]}
                             for x in lines],
            "engine_length_m": round(e_len, 4), "engine_minus_net_m": round(e_len - n["net_m"], 4),
            "engine_value_length_beyond_net_m": round(e_plan_len - n["net_m"], 4),
        })
    missing = set(eng) - bound
    if missing:
        raise SystemExit(f"engine lines not bound to a drawn band: {sorted(missing)}")
    return rows


def totals(rows, dirs):
    t = {"net_m": 0.0, "net_lo_m": 0.0, "net_hi_m": 0.0, "drawn_m": 0.0, "axis_m": 0.0, "gross_m": 0.0,
         "engine_length_m": 0.0}
    for r in rows:
        if r["dir"] not in dirs:
            continue
        t["net_m"] += r["readings_m"]["net_m"]
        t["net_lo_m"] += r["net_range_m"][0]
        t["net_hi_m"] += r["net_range_m"][1]
        t["drawn_m"] += r["readings_m"]["drawn_m"]
        t["axis_m"] += r["readings_m"]["axis_m"]
        t["gross_m"] += r["readings_m"]["gross_m"]
        t["engine_length_m"] += r["engine_length_m"]
    return {k: round(v, 4) for k, v in t.items()}


CLASS_D = (0.30, 0.40, 0.60, 0.95)


def printed_depth(value_m3, plan_m2):
    """the depth a valued line carries: V / A when it is one of the printed classes (p.13 0.30 / 0.40 / 0.60, the
    exterior main house 0.95 by two levels); an exterior line whose net plan is shorter than its plan area (T-230
    ends) gives V / A under 0.95 and above 0.85: its depth is 0.95 (T-289 / T-391 group)."""
    q = value_m3 / plan_m2
    for d in CLASS_D:
        if abs(q - d) < 0.0006:
            return d
    if 0.85 < q < 0.95:
        return 0.95
    raise SystemExit(f"value / plan {q:.4f} is no printed depth")


def engine_findings(rows):
    """per band: the engine's VALUE length (value / (b x printed D)) against the drawn net range (R-T416-1 / -3), and
    every band whose engine length differs from the drawn net by more than 5 mm, with the cut kinds that explain it."""
    out = []
    for r in rows:
        lo, hi = r["net_range_m"]
        valued = [x for x in r["engine_lines"] if x["state"] == "VALUED"]
        vlen = None
        if valued and len(valued) == len(r["engine_lines"]):
            vlen = round(sum(x["value_m3"] / (0.30 * x["D_print_m"]) for x in valued), 4)
        d = r["engine_minus_net_m"]
        if abs(d) <= 0.005 and (vlen is None or abs(vlen - r["readings_m"]["net_m"]) <= 0.005):
            continue
        over = None
        if vlen is not None:
            over = round(sum(x["D_print_m"] for x in valued) / len(valued) * 0.30 * max(0.0, vlen - hi), 6)
        out.append({"band": r["band"], "lines": [x["line_id"] for x in r["engine_lines"]],
                    "states": sorted({x["state"] for x in r["engine_lines"]}),
                    "engine_length_minus_net_m": d, "value_length_m": vlen, "net_range_m": [lo, hi],
                    "value_length_position": (None if vlen is None else "ABOVE_RANGE" if vlen > hi + 0.005 else
                                              "BELOW_RANGE" if vlen < lo - 0.005 else "IN_RANGE"),
                    "valued_m3_beyond_range": over,
                    "columns_inside_m": r["net_cut_by_kind_m"].get("COLUMN", 0.0),
                    "columns_inside": r["columns_by_frame_m"]["GBP"],
                    "junction_cut_m": r["net_cut_by_kind_m"].get("JUNCTION", 0.0)})
    return out


def freelancer(path):
    import openpyxl  # private step only
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[2]
    gl, gt = [ws.cell(13, c).value for c in (2, 3, 4)], [ws.cell(14, c).value for c in (2, 3, 4)]
    if not (gl[0] == gt[0] == B_OTHER and gl[2] == gt[2] == D_OTHER):
        raise SystemExit("his two ground-beam rows are not the one section 0.30 x 0.60")
    return {"long_m": float(gl[1]), "trans_m": float(gt[1])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer")
    ap.add_argument("--out")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    eng = load_engine()
    rows = band_rows(inp, eng)
    t391 = json.loads(T391.read_text(encoding="utf-8"))["beams"]
    L_eng = sum(x["length_m"] for x in eng.values())
    if abs(L_eng - t391["engine_length_m"]) > 1e-6:
        raise SystemExit("engine length differs from T-391")
    term = t391["cause_terms_m3"]["length_basis_untraced"]
    L_other = L_eng - term / (B_OTHER * D_OTHER)            # his total, from the merged T-391 term (no workbook needed)
    all_t = totals(rows, "XYOC")
    r_all = {"net_m": all_t["net_m"], "drawn_m": all_t["drawn_m"], "axis_m": all_t["axis_m"], "gross_m": all_t["gross_m"]}
    split = R.length_term_split(B_OTHER, D_OTHER, L_other, L_eng, r_all)
    if abs(split["length_term_m3"] - term) > 1e-6:
        raise SystemExit("split does not reproduce the T-391 length term")
    by_dir = {k: totals(rows, k) for k in ("X", "Y", "O", "C")}
    summ = {
        "schema": "T416_SUMMARY_V1", "candidate_ids": "ARCH_TAKEOFF_V3.0.35 (= V3.0.29 for STR.CONC.GROUND_BEAM)",
        "bands": rows, "totals_all_m": all_t, "totals_by_dir_m": by_dir,
        "engine_findings": engine_findings(rows),
        "length_term": {"t391_term_m3": term, "engine_length_m": round(L_eng, 4), **split},
        "guards": inp["guards"],
    }
    if a.freelancer:
        fl = freelancer(a.freelancer)
        if abs(fl["long_m"] + fl["trans_m"] - L_other) > 1e-6:
            raise SystemExit("his lump total differs from the merged T-391 term")
        tests = {}
        # which plan direction each lump is cannot be read from his rows: both assignments, curved / oblique bands
        # in either lump, are placed (the test is only that no assignment needs a length beyond the drawn gross)
        for name, (dl, dt) in {"H1 long=X": ("X", "Y"), "H2 long=Y": ("Y", "X")}.items():
            for co, (extra_l, extra_t) in {"OC->long": ("OC", ""), "OC->trans": ("", "OC"),
                                           "O->long,C->trans": ("O", "C"), "C->long,O->trans": ("C", "O")}.items():
                tl, tt = totals(rows, dl + extra_l), totals(rows, dt + extra_t)
                pl = R.place_lump(fl["long_m"], {k: tl[k] for k in ("net_m", "drawn_m", "axis_m", "gross_m")})
                pt = R.place_lump(fl["trans_m"], {k: tt[k] for k in ("net_m", "drawn_m", "axis_m", "gross_m")})
                tests[f"{name}; {co}"] = {"long": pl, "trans": pt}
        summ["direction_tests"] = tests
        if a.out:
            out = Path(a.out).resolve()
            if ROOT.resolve() in out.parents or out == ROOT.resolve():
                raise SystemExit("--out inside the repository: the freelancer's values stay in .work/private")
            out.mkdir(parents=True, exist_ok=True)
            (out / "T416_PRIVATE.json").write_text(json.dumps({"freelancer": fl, "tests": tests}, indent=1) + "\n",
                                                   encoding="utf-8")
    else:
        old = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
        if "direction_tests" in old:
            summ["direction_tests"] = old["direction_tests"]      # private step result, kept as committed
    txt = json.dumps(summ, indent=1, sort_keys=True) + "\n"
    if a.write:
        SUMMARY.write_text(txt, encoding="utf-8")
        print("written", SUMMARY.name)
    else:
        same = SUMMARY.exists() and SUMMARY.read_text(encoding="utf-8") == txt
        print("REPRODUCED" if same else "DIFFERS")
        if not same:
            raise SystemExit(1)
    print(json.dumps({"totals": all_t, "length_term": summ["length_term"],
                      "tests": summ.get("direction_tests")}, indent=1))


if __name__ == "__main__":
    main()
