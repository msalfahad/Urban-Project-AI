"""T-445 on the development villa: the FOOTING BLINDING piece ledger, the four candidate STR.CONC.BLINDING lines
re-added from their pieces, the lane I proposal per line id and the roll-up's blinding item (-47.055 m3) split term
by term. Research only, unwired: no engine, candidate, released or rule file changes.

Inputs (read only, all asserted):
  research/agents_t445/ALSENAN_BLINDING_INPUT.json   own read this task (values only: per-outline sizes and areas)
  research/agents_t233/ALSENAN_FOOTING_INPUT.json    merged T-233 per-outline blinding areas (must agree)
  research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json   the 4 blinding lines (= V3.0.41: T-469 scoreboard held
                                                     21.059 .. 25.964 on 4 lines, asserted below)
  research/agents_t433/summary_t433.json             item I-01 (BL-1) -47.055 m3 on the same 4 line ids
  research/agents_t469/out/T469_SCOREBOARD_V3_0_41.json  CONC.BLINDING keyed row (reference 47.055 m3)
Optional: --geometry <private extract from t445_extract.py> re-derives every area from the DXF polygons.

    .work/venv/bin/python -I research/agents_t445/t445_alsenan.py [--geometry .work/private/t445_outlines.json] [--write]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import blinding_piece_ledger_v1 as B  # noqa: E402

LINES = {"FOOTINGS": "L-98eb2d58075c9eddf1b4", "F10F": "L-080c97f5f6a92452cd04",
         "GB": "L-7a5214a334ea3559fa2d", "STRAP": "L-35382b18e2e362df3ae6"}
T322_VERDICT = "Checker T-322 verdict 2026-10-29 01:55 (DG-3521554d2fd011b9 reason text: 24 pits 12.734438 VERIFIED)"
REFERENCE_M3 = 47.055


def _j(rel):
    return json.loads((RES / rel).read_text())


def close(a, b, what, tol=1e-6):
    if abs(a - b) > tol:
        raise B.Refused("CLOSURE", f"{what}: {a} vs {b}")


def candidate_lines():
    d = _j("agents_t347/CANDIDATE_V3024_BURIED_LINES.json")
    rows = d["lines"] if isinstance(d, dict) else d
    got = {r["line_id"]: r for r in rows if r["line_id"] in LINES.values()}
    if len(got) != 4:
        raise B.Refused("CANDIDATE_LINE_MISSING", repr(sorted(got)))
    sc = _j("agents_t469/out/T469_SCOREBOARD_V3_0_41.json")
    s = json.dumps(sc)
    lo = sum(r["bounded_low"] for r in got.values())
    hi = sum(r["bounded_high"] for r in got.values())
    # V3.0.41 keyed CONC.BLINDING: held 4 lines 21.059 .. 25.964 (T-469 MERGED); the same 4 lines
    keyed = None
    for blk in sc.get("keyed", []):
        for r in blk.get("rows", []):
            if r.get("key") == "CONC.BLINDING" and "V3.0.41" in blk.get("label", "") + json.dumps(blk.get("label")):
                keyed = r
    if keyed is None:
        for blk in sc.get("keyed", []):
            for r in blk.get("rows", []):
                if r.get("key") == "CONC.BLINDING" and r.get("held_lines") == 4:
                    keyed = r
    if keyed is None or keyed["held_lines"] != 4:
        raise B.Refused("V3041_KEYED_ROW_NOT_FOUND")
    close(keyed["held_low"], lo, "V3.0.41 held low = the 4 lines", 0.0005)
    close(keyed["held_high"], hi, "V3.0.41 held high = the 4 lines", 0.0005)
    close(keyed["reference_qty"], REFERENCE_M3, "reference 47.055", 1e-6)
    assert "STR.CONC.BLINDING" in s
    return got, {"v3041_held_low": keyed["held_low"], "v3041_held_high": keyed["held_high"],
                 "reference_m3": REFERENCE_M3}


def t433_item():
    d = _j("agents_t433/summary_t433.json")
    item = next(i for i in d["items"] if "BL-1" in i["parts"])
    close(d["parts"]["BL-1"], -REFERENCE_M3, "T-433 BL-1")
    if sorted(d["part_lines"]["BL-1"]) != sorted(LINES.values()):
        raise B.Refused("T433_LINES_DIFFER")
    return item


def plan_records(inp, geometry=None):
    """per-outline areas: from the committed own-read values; with --geometry recomputed from the polygons."""
    rec = {o["id"]: o for o in inp["outlines"]}
    if geometry is not None:
        g = json.loads(Path(geometry).read_text())
        pits = [{"id": k, "outline": g["outlines"][k]["vertices"], "depth_m": rec[k]["H"]} for k in inp["pits"]]
        pr = B.plan_from_geometry(pits, g["plot"], "m", inp["projection_m"])
        for k in inp["pits"]:
            for f in ("outline_m2", "grown_m2", "own_m2", "inside_m2", "outside_m2"):
                close(pr[k][f], rec[k][f], f"geometry {k} {f}", 1e-6)
        close(pr["_union"]["inside_m2"], inp["pits_union_inside_m2"], "union inside", 1e-6)
        # FF and F10+F outlines: grown plans in their readings touch no neighbour (rule 3)
        nb = {k: [tuple(v) for v in B.grow(B._poly(g["outlines"][k]["vertices"], 1.0),
                                           inp["projection_m"]).exterior.coords[:-1]] for k in inp["pits"]}
        B.clearance_ok(g["outlines"]["1B2B"]["vertices"], [0.0, 0.10, 0.15], nb, "m")
        rec["_geometry"] = "re-derived from the DXF polygons: AGREE"
    return rec


def t233_agree(inp):
    t = {o["id"]: o for o in _j("agents_t233/ALSENAN_FOOTING_INPUT.json")["outlines"]}
    for o in inp["outlines"]:
        close(o["grown_m2"], t[o["id"]]["blind_m2"], f"T-233 grown {o['id']}")
        close(o["outside_m2"], t[o["id"]]["blind_outside_m2"], f"T-233 outside {o['id']}")


def spec_for(inp, rec, ff_estimate=None):
    t = inp["thickness_m"]
    pits = []
    for k in inp["pits"]:
        o = rec[k]
        pits.append({"id": k, "element": f"blinding under footing {o['type']} (outline {k})", "line": LINES["FOOTINGS"],
                     "inside_m2": o["inside_m2"], "outside_m2": o["outside_m2"],
                     "source": "ST DXF FOUNDATION PLAN outline + ST p.13 '10 | L x W | 10', '10cm Plain con.'",
                     "verdict": T322_VERDICT})
    a, b = 4.60, 4.50
    ff = {"id": "1B2B:FF", "element": "blinding under the FF lift raft (outline 1B2B)", "line": LINES["FOOTINGS"],
          "outline_m2": a * b, "basis": B.INHERITED, "readings": {"p0.10_inherited_p13": 0.10, "p0.15_scaled_p14": 0.15},
          "plan_fn": lambda p: (a + 2 * p) * (b + 2 * p),
          "blocker": "RFI-S08 (projection under the lift raft not printed on its governing detail ST p.14)"}
    if ff_estimate:
        ff["estimate"] = ff_estimate
    c = inp["f10f"]
    return {"thickness": {"value": t, "basis": B.PRINTED, "source": "ST p.13 / p.14 '10cm Plain con.'"},
            "projection": {"value": inp["projection_m"], "basis": B.PRINTED,
                           "source": "ST p.13 TYP. DETAIL OF ISOLATED FOOTING '10 | L x W | 10' (governing for the 24 pits)"},
            "measured": pits,
            "beyond_boundary": {"line": LINES["FOOTINGS"],
                                "blocker": "RFI-S06 (blinding beyond the plot line at the 8 footings on it, D-14)"},
            "held_projection": [ff],
            "conflict": [{"id": "1B1B:F10+F", "element": "blinding under the F10 + F outline 1B1B", "line": LINES["F10F"],
                          "scenarios": c["scenarios_m3"],
                          "blocker": "RFI-S02 (one outline, two tags; owner 2026-11-02: three scenarios F10 alone / "
                                     "F10 + F / drawn outline, each consistent across trades)"}],
            "held_range": [
                {"id": "GB", "element": "blinding under the ground beams (p.13 four sections '10 / 30 / 10')",
                 "line": LINES["GB"], "low": inp["candidate"]["GB"]["low"], "high": inp["candidate"]["GB"]["high"],
                 "blocker": "RFI-S09 (D-35 exterior depth 'FOLLOW ARCH.') + RFI-S11 (D-34 length basis / title)"},
                {"id": "STRAP", "element": "blinding under the straps SB1-SB3 (no strap section on any sheet)",
                 "line": LINES["STRAP"], "low": inp["candidate"]["STRAP"]["low"],
                 "high": inp["candidate"]["STRAP"]["high"],
                 "blocker": "RFI-S07 (D-15: whether the straps sit on blinding); ledger 0 .. 0.913 (F-T347-2)"}],
            "unmeasured": [
                {"id": "BW_BASE", "element": "blinding under the boundary-wall base (ST p.14 TYPICAL BOUNDARY WALL "
                                             "SECTION (A-A): 10 thick, 80 + 10 past the toe, flush on the outer face)",
                 "line": "MISSING",
                 "blocker": "pad count not printed (M2, column spacing 'SEE ARCH PLAN', RFI-S04); blinding under the "
                            "band between pads not drawn; per pad AT_LEAST 1.30 x 0.90 x 0.10 = 0.117 m3",
                 "source": "ST p.14 own read this task", "readings": {"per_pad_at_least_m3": 0.117}}]}


def run(geometry=None):
    inp = json.loads((HERE / "ALSENAN_BLINDING_INPUT.json").read_text())
    got, v3041 = candidate_lines()
    item = t433_item()
    t233_agree(inp)
    rec = plan_records(inp, geometry)
    # the 24 pits re-add exactly to the T-322 / T-320 VERIFIED layer
    pits_in = sum(rec[k]["inside_m2"] for k in inp["pits"])
    close(pits_in, inp["pits_union_inside_m2"], "24 pits own plans = union inside")
    close(pits_in * inp["thickness_m"], 12.7344375, "24 pits m3", 1e-9)
    # candidate figures in the input = the candidate file
    for key, lid in LINES.items():
        r = got[lid]
        close(r["bounded_low"], inp["candidate"][key]["low"], f"{key} low")
        close(r["bounded_high"], inp["candidate"][key]["high"], f"{key} high")
    out = {}
    for state, est, valued in (
            ("NOW (V3.0.41: no blinding valued)", None, []),
            ("PROPOSAL A (value the 24 VERIFIED pits only)", None, "PITS"),
            ("PROPOSAL B (A + FF ESTIMATED 2.352 under the RFI-S08 label, never VERIFIED)",
             {"label": "RFI RE-REVIEW 2026-11-02 S08 ESTIMATED (p.14 scaled 0.15; range low = p.13 typical 0.10)",
              "reading": "p0.15_scaled_p14"}, "PITS+FF")):
        pieces = B.build(spec_for(inp, rec, est))
        lines = {
            LINES["FOOTINGS"]: {"value": got[LINES["FOOTINGS"]]["measured_net"],
                                "reading": {"1B2B:FF": "p0.10_inherited_p13"}, "at_high": ("BEYOND_BOUNDARY",)},
            LINES["F10F"]: {"low": got[LINES["F10F"]]["bounded_low"], "high": got[LINES["F10F"]]["bounded_high"],
                            "reading_range": True},
            LINES["GB"]: {"low": got[LINES["GB"]]["bounded_low"], "high": got[LINES["GB"]]["bounded_high"]},
            LINES["STRAP"]: {"low": got[LINES["STRAP"]]["bounded_low"], "high": got[LINES["STRAP"]]["bounded_high"]}}
        # the candidate F10 + F line carries two of the three scenarios (rows separately / outline)
        lines[LINES["F10F"]]["reading"] = {}
        maps = B.map_lines(_with_candidate_f10f(pieces, inp), lines)
        vids = []
        if valued:
            vids = [p["id"] for p in pieces if p["status"] == B.VERIFIED]
            if valued == "PITS+FF":
                vids.append("1B2B:FF")
        rec_ref = B.reconcile_reference(pieces, vids, REFERENCE_M3,
                                        "one plain layer over the plot rectangle 31.37 x 15.00 (= plot line 1658, own "
                                        "read) x 0.10; no sheet draws it (ST p.13 'COMPACTED SOIL' under the slab)")
        out[state] = {"pieces": pieces, "lines": maps, "reference": rec_ref}
    return inp, rec, out, v3041, item


def _with_candidate_f10f(pieces, inp):
    """For the line re-add only: the candidate F10 + F line carries 0.552 .. 0.590 (outline / rows separately); the
    owner's third scenario (F10 alone 0.480) is outside it. The re-add uses the two scenarios the line names, the
    piece keeps all three (finding F-T445-2)."""
    out = []
    for p in pieces:
        if p["id"] == "1B1B:F10+F":
            q = dict(p)
            sc = {k: v for k, v in p["readings"].items() if k in inp["f10f"]["candidate_scenarios"]}
            q["low"], q["high"] = min(sc.values()), max(sc.values())
            out.append(q)
        else:
            out.append(p)
    return out


def write(inp, rec, out):
    rows = []
    now = out["NOW (V3.0.41: no blinding valued)"]
    prop = out["PROPOSAL A (value the 24 VERIFIED pits only)"]["lines"]
    for p in now["pieces"]:
        o = rec.get(p["id"].split(":")[0], {})
        rows.append({"piece": p["id"], "element": p["element"], "handle": p["id"].split(":")[0] if o else "",
                     "type": o.get("type", ""), "outline_m2": o.get("outline_m2", ""), "plan_m2": p["plan_m2"] or "",
                     "t_m": p["t_m"], "m3": p["value"] if p["value"] is not None else "",
                     "range_m3": "" if p["value"] is not None else
                     (f"{p['low']} .. {p['high']}" if p["low"] is not None else "no figure"),
                     "status": p["status"], "line": p["line"],
                     "lane_I": (prop[p["line"]]["proposal"] if p["line"] in prop else "NEW LINE (MISSING)"),
                     "blocker_or_verdict": p["verdict"] or p["blocker"]})
    with open(HERE / "LEDGER_T445.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summ = {k: {"lines": v["lines"], "reference": v["reference"],
                "pieces": [{x: p[x] for x in ("id", "status", "value", "low", "high", "line")} for p in v["pieces"]]}
            for k, v in out.items()}
    (HERE / "summary_t445.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    inp, rec, out, v3041, item = run(a.geometry)
    for k, v in out.items():
        r = v["reference"]
        print(k, "| engine valued", r["engine_valued_m3"], "residual", r["residual_m3"])
        for t in r["terms"][-6:]:
            print("   ", t["piece"], t["term_low"], t["term_high"])
        print("    RD", r["rule_difference"]["term_low"], r["rule_difference"]["term_high"])
        for lid, m in v["lines"].items():
            print("   line", lid, m["proposal"], m["value_m3"], m["pieces_low"], m["pieces_high"])
    print("geometry:", rec.get("_geometry", "committed values only"))
    if a.write:
        write(inp, rec, out)
