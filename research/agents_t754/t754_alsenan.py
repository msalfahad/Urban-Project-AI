"""T-754 exterior paint edge residuals on the development villa (research; nothing wired, no candidate line moves).

Inputs (committed, sha-pinned): the T-754 DXF census (in/T754_CENSUS.json, from t754_census.py), the T-751 bounds, the
T-747 exterior paint ledger, the T-746 door frame census, T-159 facade sides, T-164 railing census, T-348 constants.
Writes out/T754_EDGE_RESIDUALS.{json,md}.  `--check` rebuilds and compares with the committed outputs.

    python -I research/agents_t754/t754_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t754_rules as R  # noqa: E402

CENSUS = "research/agents_t754/in/T754_CENSUS.json"
T751 = "research/agents_t751/out/T751_EDGE_BOUNDS.json"
T747 = "research/agents_t747/out/T747_EXT_PAINT.json"
T746 = "research/agents_t746/DOOR_FRAMES_T746.csv"
T159 = "research/agents_t159/FACADE_SIDES_T159.csv"
T164 = "research/agents_t164/RAILINGS_T164.csv"
T348 = "research/agents_t348/t348_alsenan.py"
PINS = [CENSUS, T751, T747, T746, T159, T164, T348]
OUT_J = HERE / "out" / "T754_EDGE_RESIDUALS.json"
OUT_M = HERE / "out" / "T754_EDGE_RESIDUALS.md"
SCHEMA = "URBAN_T754_EDGE_RESIDUALS_V1"

# T-348 (merged) plan constants for the NW-1 / NW-2 / NW-3 screen-front plane (1F plan B61 / CB3 / B62; 2F plan 1319)
NW3_FRONT, CHORD, NW1_KEY = "0.578", "3.059412", "1.170294"
NW1_ROUND_R = "0.298259"   # T-348 NW1_ARC: the SW-3 / NW-1 corner quarter arc r (1F plan CA4, 2F plan 1313)
HEAD_FACT = ("door head section or door schedule (head member depth against the wall depth): designer item 13 / D-62 "
             "(door schedule not issued); no plan, no vector elevation draws it")
PLAN_FACT = "the 1F plan outline at the passage mouth (GF parapet end free or abutting) was not traced this run"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def jload(p):
    return json.loads((ROOT / p).read_text())


def rows(p):
    with open(ROOT / p, newline="") as f:
        return list(csv.DictReader(f))


def doors(cen, t747):
    frames = {r["opening"]: r for r in rows(T746)}
    out = []
    for o in t747["edges"]["openings"]:
        if o.get("kind") != "DOOR":
            continue
        d = o["opening"]
        ring = next(x for x in o["others"] if x["source"] == "T-737 ring")
        w = R.D(o["lm"][1])                       # head 0 .. w in T-747 = the opening width
        f = frames[d]
        jamb_w = R.D(f["masonry_w_m"])
        if f["frame_at_jambs"] == "True":
            js = "FULL_DEPTH_AT_JAMBS"
        else:
            js = "POSITION_CONFLICT"
            w = jamb_w                            # the masonry governs the opening (T-746 F-T746-3)
        h = (R.D(ring["lm"][0]) - w) / 2         # ring = 2h + w (T-737, rectangle)
        fact = HEAD_FACT
        if d == "D-GF-07":
            dd = cen["door_gf07_se"]
            fact += ("; the SE frame draws D-GF-07 beyond (layer 5) as a frame outline only: jamb faces %s / %s from "
                     "the jamb 1C00, head faces %s / %s below the head 220F +%s (2234 / 223A): a face width is not a "
                     "depth" % (dd["1CF1"]["offset_from_jamb_1C00"], dd["1CF3"]["offset_from_jamb_1C00"],
                                R.s6(R.D(dd["220F"]["lv_hi"]) - R.D(dd["2234"]["lv_hi"])),
                                R.s6(R.D(dd["220F"]["lv_hi"]) - R.D(dd["223A"]["lv_hi"])), dd["220F"]["lv_hi"]))
        r = R.door_edges(w, h, js, "NOT_DRAWN", fact)
        before = o["lm"]
        if r["lm"] != [R.s6(before[0]), R.s6(before[1])]:
            raise R.RuleError(f"{d}: R-T754-1 {r['lm']} differs from the T-747 bound {before}")
        out.append({"door": d, "face": o["face_id"], "plan_handle": f["handle"], "block": f["block"],
                    "w": R.s6(w), "h": R.s6(h), "wall_depth": f["wall_depth_m"], "jamb_state": js,
                    "jamb_evidence": f["evidence"], **r, "before": before})
    tot = R.sum_bounds([x["lm"] for x in out])
    return {"doors": out, "total_lm": tot, "before_lm": t747["edges"]["summary"]["doors"]["lm"]}


def nw_corners(cen, t751):
    band = cen["nw_parapet_band"]
    dx = band["top_line"]["dx"]
    v = band["verticals_inside_band"]
    # the round of the SW-3 / NW-1 corner (2737 + its shading 2A51..2A53) lies beyond NW-1's key width: only verticals
    # inside the NW-3 + chord + NW-1 key span (offset < the sum) can be a NW-1/NW-2 or NW-2/NW-3 arris
    span = R.D(NW3_FRONT) + R.D(CHORD) + R.D(NW1_KEY)
    round_start = min(R.D(x["offset_from_27CB_start"]) for x in v)
    round_at = R.D(dx) - R.D(NW1_ROUND_R)
    if abs(round_start - round_at) > R.TOL:
        raise R.RuleError(f"the first vertical in the span ({round_start}) is not the SW-3 / NW-1 round start ({round_at})")
    inner = [x["handle"] for x in v if R.D(x["offset_from_27CB_start"]) < round_at - R.TOL]
    verdict = R.coplanar_junction([NW3_FRONT, CHORD, NW1_KEY], dx, inner)
    ends = {e["corner"]: e for e in t751["corners"]["parapet_ends"]}
    removed = [ends["NW-1/NW-2"]["lm"], ends["NW-2/NW-3"]["lm"]] if verdict == "NOT_A_CORNER" else []
    rem = R.sum_bounds(removed) if removed else ["0.000000", "0.000000"]
    return {"verdict": verdict, "top_line": band["top_line"]["handle"], "projected_dx": dx,
            "true_lengths": {"NW-3 front": NW3_FRONT, "NW-2 chord (screen front)": CHORD, "NW-1 key": NW1_KEY},
            "sum_true": R.s6(span), "diff": R.s6(R.D(dx) - span), "verticals_inside_span": inner,
            "verticals_at_round": [x["handle"] for x in v], "round_starts_at": R.s6(round_start),
            "removed_lm": rem, "corners": ["NW-1/NW-2", "NW-2/NW-3"]}


def no_host(t751, t747):
    faces = {f["face_id"]: f for f in t747["faces"]}
    cand = []
    for k in ("GF/P-1/COVERED/storey", "GF/P-2/COVERED/storey", "GF/NE-6/EDGE/storey", "GF/NE-6/EDGE/parapet"):
        f = faces[k]
        cand.append((k, f["line_key"], f["bottom"], f["top"]))
    state, hosts, line = R.host_by_band("4.80", "5.50", cand)
    lm = t751["corners"]["no_host"]["lm"]
    return {"row": "EXT#GF-MOUTHS -> NO_HOST", "lm": lm, "interval": ["4.800000", "5.500000"], "state": state,
            "host_faces": hosts, "host_line": line,
            "why": "2 x (+4.80 .. +5.50) passage-wall end arrises at the mouth (NE-5 is NOT_A_FACE, 1.20 gap, T-159): "
                   "above the annex parapet top +4.80 only the passage faces P-1 (+0.30 .. +5.50) and P-2 (+1.00 .. "
                   "+5.50) stand at the wall ends; both are on the GF storey line, so either pairing gives one host"}


def slab_edges(cen):
    se = cen["se_over_mouth"]
    over = [h["handle"] for h in se["horizontals_4p70_5p60"] if h["overlaps_mouth_span"]]
    mouth = R.D(se["mouth_top"]["dx"])
    nwb = cen["nw_bands"]
    hidden = ("NW frame: the only horizontals at +5.30 .. +5.50 are the GF roof strip band 27E4 / 27E5 (%s m, between the "
              "end columns 27D6 / 27E0) and the pool-court front 2841 / 2842 + 2845 / 2846 (beyond) + 2840 / 27B1, both "
              "in front of the 1F wall line (T-393 RL-04 strip; T-348 1.50 m): the 1F wall's underside there is hidden; "
              "missing: a section through the 1F NW edge (sheet 10 A-A is raster) or the structural edge-beam schedule"
              % nwb["27E4"]["dx"])
    raster = "the face is seen only on a raster elevation (NE sheet 09 / SW Pages_07-08): never scaled, no vector view"
    out = []
    for r in rows(T159):
        if r["PORTION"] != "SLAB_EDGE_BELOW" or r["FLOOR"] != "1F":
            continue
        side, L = r["SIDE"], r["PORTION_LEN_M"]
        if side in ("NW-1", "NW-3"):
            out.append({"face": side, "len": L, "state": "NOT_A_FACE", "lm": ["0.000000", "0.000000"],
                        "cause": "T-348 (merged): the pier stands on the GF roof band running 1.50 m seaward"})
        elif side == "NW-2":
            out.append({"face": side, "len": L, "state": "CITED", "lm": None,
                        "cause": "T-348 (merged): void ring landward arc 2.675 m, depth 0.20 .. 0.75 HELD bounded; "
                                 "not restated"})
        elif side == "SE-1":
            if over:
                raise R.RuleError("a line over the porch-mouth span: SE-1 is not one plane")
            a = R.slab_edge_arris(mouth, "ONE_PLANE", "SE frame: no horizontal line between the porch-mouth piece top "
                                  "2232 (+4.70) and +5.60 over its %s m span (the only ones in that level band, %s, lie "
                                  "outside it): the wall above, the slab edge and the mouth face are one plane; the "
                                  "+4.70 edge is the porch-mouth opening's head (T-360 C-1), not a slab edge"
                                  % (R.s6(mouth), ", ".join(h["handle"] for h in se["horizontals_4p70_5p60"])))
            rest = R.D(L) - mouth
            out.append({"face": side, "len": L, "state": "PART: %s m ONE_PLANE / %s m HELD" % (R.s6(mouth), R.s6(rest)),
                        "lm": None, "part_lm": a["lm"], "cause": a["cause"] + "; the other %s m of the portion lies "
                        "behind the annex in the SE frame (beyond layer 5 boxes 2428 / 2426): HELD blank" % R.s6(rest)})
        elif side in ("NW-4", "NW-5"):
            a = R.slab_edge_arris(L, "NOT_VISIBLE", hidden)
            out.append({"face": side, "len": L, "state": a["state"], "lm": None, "cause": a["cause"]})
        else:
            a = R.slab_edge_arris(L, "NOT_VISIBLE", raster)
            out.append({"face": side, "len": L, "state": a["state"], "lm": None, "cause": a["cause"]})
    return out


def railings():
    by = {}
    for r in rows(T164):
        by.setdefault(r["RUN"], []).append(r)
    rl03 = by["RL-03"]
    rl10 = by["RL-10"]
    return [{"where": "annex parapet top (p.12 X-lattice band)", "id": "RL-03", "line": "L-b75c30fcd5e3b5607433",
             "segments": [x["SEGMENT"] for x in rl03],
             "lm": R.s6(sum(R.D(x["LENGTH_LM"]) for x in rl03)),
             "why": "T-164: the annex (dewaneya) roof guard, 1F plan bands B2D / B2E + B27 / B28, drawn on p.12 FENCE "
                    "ELEVATION, p.7 SW and p.9 NE: the same element, its own id (not RL-10)"},
            {"where": "street fence top (p.12 X-lattice in the wall's dip)", "id": "RL-10",
             "line": "L-78babf2c6da600cb800e", "segments": [x["SEGMENT"] for x in rl10], "lm": None,
             "why": "T-164 / T-400: the street-fence X railing, length not printed (p.12 raster, never scaled): HELD"}]


def paint_low(t751):
    p = t751["paint"]
    parts = []
    for fc in p["face_changes"]:
        parts.append((fc["face_id"], R.D(fc["paint_after"][0]) - R.D(fc["paint_before"][0])))
    delta = sum((x[1] for x in parts), R.D(0))
    lo = R.D(p["total_before"]["paint"][0]) + delta
    if lo != R.D(p["total_after"]["paint"][0]):
        raise R.RuleError("T-751 paint low end does not re-add")
    return {"before": p["total_before"]["paint"], "after": p["total_after"]["paint"], "low_end_delta": R.s6(delta),
            "parts": [[f, R.s6(x)] for f, x in parts], "residual": "0.000000",
            "note": "T-754 moves no m2: every item here is an lm edge (UP-FIN-PAINT-002 reading B); the T-751 paint "
                    "low end restatement stands as merged"}


def build():
    cen, t751, t747 = jload(CENSUS), jload(T751), jload(T747)
    dr = doors(cen, t747)
    nw = nw_corners(cen, t751)
    nh = no_host(t751, t747)
    c = t751["corners"]
    lo = R.D(c["after_lm"][0]) - R.D(nw["removed_lm"][0])
    hi = R.D(c["after_lm"][1]) - R.D(nw["removed_lm"][1])
    hosted = R.D(nh["lm"]) if nh["state"] == "HOSTED" else R.D(0)
    corners = {"before_hosted": c["after_lm"], "before_physical": c["after_physical_lm"],
               "not_a_corner_lm": nw["removed_lm"], "no_host_rehosted_lm": R.s6(hosted),
               "after_hosted": [R.s6(lo + hosted), R.s6(hi + hosted)],
               "after_physical": [R.s6(lo + R.D(nh["lm"])), R.s6(hi + R.D(nh["lm"]))],
               "parapet_ends_after": R.s6(R.D(c["parapet_ends_lm"][0]) - R.D(nw["removed_lm"][0])),
               "stop_end": {"lm": c["stop_end"]["lm"], "state": "HELD", "cause": c["stop_end"]["cause"] + "; " + PLAN_FACT}}
    # reconciliation: before physical - NOT_A_CORNER = after physical (the re-hosting moves no metre)
    for i in (0, 1):
        if R.D(c["after_physical_lm"][i]) - R.D(nw["removed_lm"][i]) != R.D(corners["after_physical"][i]):
            raise R.RuleError("corner reconciliation residual")
    return {"schema": SCHEMA, "rules": list(R.RULE_IDS), "version": R.VERSION,
            "pins": {p: sha(p)[:16] for p in PINS}, "census_dxf_sha16": cen["dxf_sha16"],
            "doors": dr, "nw_parapet": nw, "no_host": nh, "corners": corners, "slab_edge_1f": slab_edges(cen),
            "railing_ids": railings(), "paint": paint_low(t751)}


def md(d):
    c, dr, nw, nh = d["corners"], d["doors"], d["nw_parapet"], d["no_host"]
    L = ["# T754 exterior paint edge residuals (generated by t754_alsenan.py; do not edit)", "",
         f"Pins: {', '.join(f'{k} {v}' for k, v in d['pins'].items())}; DXF {d['census_dxf_sha16']}.", "",
         "## Doors (R-T754-1)", "", "| door | face | block | w | h | jambs | head | lm | state |", "|---|---|---|---|---|---|---|---|---|"]
    for x in dr["doors"]:
        L.append(f"| {x['door']} | {x['face']} | {x['block']} ({x['plan_handle']}) | {x['w']} | {x['h']} | "
                 f"{x['jamb_state']} {x['jambs'][0]} .. {x['jambs'][1]} | {x['head'][0]} .. {x['head'][1]} | "
                 f"{x['lm'][0]} .. {x['lm'][1]} | {x['state']} |")
    L += ["", f"Total {dr['total_lm'][0]} .. {dr['total_lm'][1]} lm (T-747 {dr['before_lm'][0]} .. {dr['before_lm'][1]}: "
          "residual 0). Missing per door: " + "; ".join(f"{x['door']}: {' | '.join(x['missing'])}" for x in dr["doors"][:1])
          + " (same head fact on all 7; D-GF-09 also the frame-in-gap conflict).", "",
          "## NW-1 / NW-2 / NW-3 parapet band (R-T754-3)", "",
          f"Top line {nw['top_line']} projected {nw['projected_dx']} vs true {nw['sum_true']} (diff {nw['diff']}); "
          f"verticals inside the span {nw['verticals_inside_span'] or 'none'} (the round's {nw['verticals_at_round']} "
          f"start at {nw['round_starts_at']}): {nw['verdict']} for {', '.join(nw['corners'])}, -{nw['removed_lm'][0]} lm.",
          "", "## NO_HOST arris (R-T754-4)", "",
          f"{nh['lm']} lm {nh['interval'][0]} .. {nh['interval'][1]}: {nh['state']} on {nh['host_line']} via "
          f"{', '.join(nh['host_faces'])}.", "", "## Corners (lm)", "",
          f"Hosted {c['before_hosted'][0]} .. {c['before_hosted'][1]} -> **{c['after_hosted'][0]} .. "
          f"{c['after_hosted'][1]}**; physical {c['before_physical'][0]} .. {c['before_physical'][1]} -> "
          f"**{c['after_physical'][0]} .. {c['after_physical'][1]}** (no NO_HOST left); parapet ends 9.185812 -> "
          f"{c['parapet_ends_after']}; stop-end {c['stop_end']['lm'][0]} .. {c['stop_end']['lm'][1]} HELD.", "",
          "## 1F slab edge below (R-T754-2)", "", "| face | portion m | state | lm | cause |", "|---|---|---|---|---|"]
    for s in d["slab_edge_1f"]:
        lm = s.get("part_lm") or s.get("lm")
        L.append(f"| {s['face']} | {s['len']} | {s['state']} | {lm[0] + ' (part)' if s.get('part_lm') else (lm[0] if lm else 'blank')} | {s['cause']} |")
    L += ["", "## Railing ids for the p.12 X-lattice (B13-07 exclusion)", ""]
    for r in d["railing_ids"]:
        L.append(f"- {r['where']}: **{r['id']}** ({r['line']}, {r['lm'] or 'HELD'} lm): {r['why']}")
    pa = d["paint"]
    L += ["", f"Paint m2 low end re-added: {pa['before'][0]} + {pa['low_end_delta']} ("
          + " + ".join(f"{f} {x}" for f, x in pa["parts"]) + f") = {pa['after'][0]} (residual {pa['residual']}); "
          f"high {pa['after'][1]}. {pa['note']}.", ""]
    return "\n".join(L)


def main(check=False):
    d = build()
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    mds = md(d)
    if check:
        ok = OUT_J.read_text() == js and OUT_M.read_text() == mds
        print("check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_J.write_text(js)
    OUT_M.write_text(mds)
    print("written", OUT_J.relative_to(ROOT), OUT_M.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
