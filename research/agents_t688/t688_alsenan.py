"""T-688 development-villa statement: the 1F slab difference (engine 19.756333 vs reference 19.2 m3, -0.556333 m3,
T-683 R-T683-2) traced cause by cause, and the F-V-P18-2 ownership of the ground face behind L-a7ab57d8.

Reads committed files only: the V3.0.66 line index (T-677), the M5 slab panel table (thickness per engine cell, for the
convention check of the other storeys) and this task's out/T688_OWN_1F_PANELS.json (own re-measure from the private
DXF by t688_measure.py, numbers only). The reference values are the typed constants of his slab sheet as already
quoted by T-683 (GF 207, 1F 120 x 0.16, roof 31.84 x 0.16 + 13.35 x 0.18); no derivation exists behind them.

    python3 -I research/agents_t688/t688_alsenan.py [--write] [--check]

Development villa: no accuracy claim; nothing released; no quantity changed; the reference is never a quantity.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t688_rules as R  # noqa: E402

INDEX = "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
PANELS = "research/urban_engine_m5_concrete_reconciliation/06A_SLAB_PANELS.csv"
OWN = "research/agents_t688/out/T688_OWN_1F_PANELS.json"
OUT_JSON, OUT_MD = HERE / "out" / "T688_STATEMENT.json", HERE / "out" / "T688_STATEMENT.md"
REF = {"GF": "207", "1F": "120", "2F@0.16": "31.84", "2F@0.18": "13.35"}   # typed constants (T-683 own read)
T = Decimal("0.16")
DOME_CORNERS = 8          # engine 1F cells between a dome ring and its square bay (4 per dome, 2 domes)
GROUND_LINE = "L-a7ab57d873e26a587fd9"
GB_LINE = "L-e16c98075f69532a3dc7"
MEMBER_SECTIONS_GROUND = [0.30]   # every member strip around the face reads 0.30 m (own re-measure)


def q(v, n=6):
    return str(Decimal(v).quantize(Decimal(1).scaleb(-n)))


def build():
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    own = json.loads((ROOT / OWN).read_text(encoding="utf-8"))
    tk = {r["PANEL_ID"]: Decimal(r["THICKNESS_M"]) for r in csv.DictReader((ROOT / PANELS).open(encoding="utf-8"))}
    slab = [x for x in idx["lines"] if x["item_code"] == "STR.CONC.SLAB" and x["class"] == "RELEASED"]

    def storey(tag):
        return [x for x in slab if x["element_id"].split(":")[2] == tag]
    eng_1f = {x["line_id"]: Decimal(str(x["measured_net"])) / T for x in storey("1F")}
    for x in storey("1F"):
        if tk[x["element_id"].split(":")[-1]] != T:
            raise R.Refused(f"1F cell not at 0.16: {x['line_id']}")
    own_1f = {r["line_id"]: Decimal(str(r["own_m2"])) for r in own["lines"] if r["class"] == "RELEASED"}
    # GF convention check in his own terms: engine GF m3 / his thickness 0.16 (his row is 207 x 0.16)
    gf_m2 = sum(Decimal(str(x["measured_net"])) for x in storey("GF")) / T
    st = R.typed_constant_residual(eng_1f, own_1f, REF["1F"], T, tol_m2="0.005",
                                   other_storeys=[("GF", gf_m2, REF["GF"])])
    eng_m3 = sum(Decimal(str(x["measured_net"])) for x in storey("1F"))
    if (Decimal(REF["1F"]) * T - eng_m3) != Decimal("-0.556333"):
        raise R.Refused("1F difference is not the T-683 value -0.556333 m3")
    # the two physical candidates named in the drawing (each fits the scope band; neither is unique)
    rows = {r["line_id"]: r for r in own["lines"]}
    corners = sorted((lid for lid, m2 in eng_1f.items() if m2 < Decimal("0.6")), key=str)
    if len(corners) != DOME_CORNERS:
        raise R.Refused("dome-corner census changed")
    lo, hi = st["scope_band_m2"]
    cand = []
    for name, ids in (("dome-corner fillers (8 cells between the two dome rings and their square bays)", corners),
                      ("the panel between B23 and the B6 over the west dome", ["L-af41a42f8504dd178716"])):
        m2 = sum(eng_1f[i] for i in ids)
        cand.append({"candidate": name, "lines": ids, "m2": q(m2), "m3": q(m2 * T), "fits": lo <= m2 <= hi})
    # 2F by thickness (observation outside this task's storey)
    f2 = {}
    for x in storey("2F"):
        t_ = tk[x["element_id"].split(":")[-1]]
        f2[str(t_)] = f2.get(str(t_), Decimal(0)) + Decimal(str(x["measured_net"])) / t_
    f2_rows = [{"thickness": t_, "engine_m2": q(a), "reference_m2": REF[f"2F@{t_}"],
                "ref_minus_engine_m2": q(Decimal(REF[f"2F@{t_}"]) - a),
                "m3": q((Decimal(REF[f"2F@{t_}"]) - a) * Decimal(t_))} for t_, a in sorted(f2.items())]
    # F-V-P18-2
    gf = own["f_v_p18_2"]["faces"]
    if len(gf) != 1:
        raise R.Refused("F-V-P18-2: the ground face is not unique")
    g = gf[0]
    owner = R.face_owner(g["width_m"], g["length_m"], own_level_mark=bool(g["own_marks"]),
                         member_sections_m=MEMBER_SECTIONS_GROUND)
    gl = next(x for x in idx["lines"] if x["line_id"] == GROUND_LINE)
    gb = next(x for x in idx["lines"] if x["line_id"] == GB_LINE)
    fvp = {"line": GROUND_LINE, "engine": {"item_code": gl["item_code"], "class": gl["class"], "m3": gl["measured_net"]},
           "own": {"m2": g["m2"], "width_m": g["width_m"], "length_m": g["length_m"], "own_level_marks": g["own_marks"],
                   "neighbour_widths_m": sorted({n["width_m"] for n in g["neighbours"]}),
                   "neighbours": len(g["neighbours"]), "m3_at_0.10": q(Decimal(str(g["m2"])) * Decimal("0.10"))},
           "owner": owner, "band_pairing_refused": R.band_refused(g["width_m"], MEMBER_SECTIONS_GROUND),
           "gb_line": {"line": GB_LINE, "class": gb["class"], "note": "runs = the curved exterior annex member "
                       "ARC:139+13A 1.8063 m x 0.30 (T-426 / T-242 ledger); none of them inside this face"},
           "register_proposal": "ELEMENT_REGISTER: GF / SLAB / geometry-hash of the 0.95 x 1.20 face -> owner trade "
                                "CONCRETE, line B10-05 STR.CONC.GROUND_SLAB L-a7ab57d8 (0.114 m3); kind GB only for "
                                "the four 0.30 m strips around it; BAND0042 when bounded keeps its runs outside the "
                                "face (R-T688-3 (b)); the +0.30 / +0.15 step sits on a 0.30 strip: a GB-part item",
           "verdict": "ENGINE_RIGHT (quantity line); detector label BEAM_STRIP wrong, no double release (GB HELD)"}
    split = st["split_m3"]
    return {"schema": "URBAN_T688_STATEMENT_V1", "rules": [R.R1, R.R2, R.R3], "candidate": idx["candidate_version"],
            "slab_1f": {"engine_m2": q(st["engine_m2"]), "own_m2": q(st["own_m2"]),
                        "own_minus_engine_m2": q(st["own_minus_engine_m2"]), "our_error": st["our_error"],
                        "engine_m3": q(eng_m3), "reference_m3": q(Decimal(REF["1F"]) * T),
                        "difference_m3": q(st["difference_m3"]), "reference_typed": REF["1F"],
                        "resolution_m2": str(st["resolution_m2"]),
                        "split_m3": {"our_error": q(split["our_error"]),
                                     "own_vs_engine_noise (arc chords, not a cause)": q(split["own_vs_engine_noise"]),
                                     "reference rounding band": [q(v) for v in split["rounding_band"]],
                                     "reference scope band": [q(v) for v in split["scope_band"]]},
                        "scope_band_m2": [q(v) for v in st["scope_band_m2"]],
                        "fitting_subsets": st["fitting_subsets"], "status": st["status"],
                        "convention_check": [{"storey": c["storey"], "ref_minus_engine_m2": q(c["ref_minus_engine_m2"]),
                                              "within_rounding": c["within_rounding"]}
                                             for c in st["convention_check"]],
                        "same_convention": st["same_convention"], "candidates": cand,
                        "located": len(own_1f), "census": own["census"]},
            "slab_2f_observation": f2_rows, "f_v_p18_2": fvp}


def render(s):
    a = s["slab_1f"]
    L = ["# T-688 statement (generated by t688_alsenan.py; numbers only)\n",
         f"Candidate {s['candidate']}. Rules {', '.join(s['rules'])}.\n",
         "## 1F slab (STR.CONC.SLAB, storey tag 1F, 22 released panels at 0.16)\n",
         f"- engine {a['engine_m2']} m2 = {a['engine_m3']} m3; own noding {a['own_m2']} m2 "
         f"(own - engine {a['own_minus_engine_m2']} m2, our error: {a['our_error']}); located {a['located']} / 22 "
         "by position.",
         f"- reference typed {a['reference_typed']} m2 x 0.16 = {a['reference_m3']} m3; difference "
         f"{a['difference_m3']} m3; resolution {a['resolution_m2']} m2.",
         f"- split (m3): {json.dumps(a['split_m3'])}",
         f"- scope band {a['scope_band_m2']} m2; fitting subsets of the 22 panels: {a['fitting_subsets']} -> "
         f"{a['status']}.",
         f"- convention check: {json.dumps(a['convention_check'])} -> same convention {a['same_convention']}.",
         "- named physical candidates (each fits, neither unique):"]
    L += [f"  - {c['candidate']}: {c['m2']} m2 = {c['m3']} m3, fits {c['fits']}" for c in a["candidates"]]
    L.append("- other faces of the plan >= 2 m2 (own classes): " +
             "; ".join(f"{c['class']} {c['m2']}" for c in a["census"]))
    L.append("\n## 2F observation (outside T-688's storey)\n")
    L += [f"- t {r['thickness']}: engine {r['engine_m2']} vs ref {r['reference_m2']} m2 "
          f"(ref - engine {r['ref_minus_engine_m2']} m2 = {r['m3']} m3)" for r in s["slab_2f_observation"]]
    f = s["f_v_p18_2"]
    L.append("\n## F-V-P18-2\n")
    L.append(f"- {f['line']} engine {f['engine']}; own {json.dumps(f['own'])}")
    L.append(f"- owner {json.dumps(f['owner'])}; band pairing refused {f['band_pairing_refused']}")
    L.append(f"- GB {f['gb_line']['line']} {f['gb_line']['class']}: {f['gb_line']['note']}")
    L.append(f"- proposal: {f['register_proposal']}")
    L.append(f"- verdict: {f['verdict']}")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    s = build()
    js = json.dumps(s, indent=1, default=str) + "\n"
    md = render(s)
    if a.write:
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
    if a.check:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == md
        print("T-688 check", "OK" if ok else "STALE")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
