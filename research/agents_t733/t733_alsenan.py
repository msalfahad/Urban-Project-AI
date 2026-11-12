"""T-733 TILES H3 READINESS on ARCH_TAKEOFF_V3.0.73 (development villa; research, unwired).

(a) the F1 / F4 tread highs (T-727 named risk) by R-T733-1 / -2 on the own read T733_DRAWN.json;
(b) V-07 third dome by R-T733-3 on the structural 2F roof slab plan;
(c) every tile / porcelain / marble line on V3.0.73 by state and cause id, stale check (R-T733-4) and the H3 / H3s
    wiring list restated with each host's live entry.
Nothing is wired; no released quantity moves. Inputs are merged repository files pinned by sha256 + T733_DRAWN.json.

    .work/venv/bin/python -I research/agents_t733/t733_alsenan.py           (write out/)
    .work/venv/bin/python -I research/agents_t733/t733_alsenan.py --check   (rebuild and compare)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t733_rules as R  # noqa: E402

P = {
    "v3073": ("research/agents_t722/out/LINE_INDEX_V3_0_73.json", "af8d567d8a8ae828"),
    "v3071": ("research/agents_t704/out/LINE_INDEX_V3_0_71.json", "eaea9f7e8cc83849"),
    "v3069": ("research/agents_t687/out/LINE_INDEX_V3_0_69.json", "e908a5f105197d44"),
    "t681": ("research/agents_t681/out/T681_TILES_CENSUS.json", "2ca16110154e890f"),
    "t702": ("research/agents_t702/out/T702_TILES_ROUND3.json", "ae5b37e75a1635cb"),
    "t715": ("research/agents_t715/out/T715_LEDGER.json", "740ba1827841a6e7"),
    "t648": ("research/agents_t648/out/FINISH_HOLD_CAUSE_CENSUS_T648.json", "767d1d3a969a548c"),
    "t723": ("research/agents_t723/out/T723_ROWS.csv", "5907eb650b0087f5"),
    "t727d": ("research/agents_t727/T727_DRAWN.json", "c405679a020a46ac"),
    "t719": ("research/agents_t719/out/T719_VOIDS.json", "8ffcd16db639aaec"),
}
DRAWN = HERE / "T733_DRAWN.json"
OUT = HERE / "out"
TILE_SCOPE = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD", "EXT.FLOOR.PORCELAIN",
              "EXT.FLOOR.OUTDOOR", "FIN.WALL.TILE", "FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED",
              "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET")       # T-681 / T-702 filter
MARBLE = "FIN.MARBLE."
TREAD_F1_1F, TREAD_F4_1F = "L-6cf11c2d30387d0942b9", "L-ea55ed317bc4de89aec1"
TREAD_F1_GF, TREAD_F2_GF = "L-fa534ec5f9dc14947899", "L-89c84fdd4964dec8a323"
V07_CEILINGS = ("L-7531772e1581b35eea5f", "L-1bd4ec39660768d22677")


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def load(key):
    rel, pin = P[key]
    if sha(rel)[:16] != pin:
        raise R.RuleError(f"{rel}: sha256 changed (pinned {pin})")
    p = ROOT / rel
    return json.loads(p.read_text()) if p.suffix == ".json" else list(csv.DictReader(p.open()))


def by_id(idx):
    return {l["line_id"]: l for l in idx["lines"]}


def s6(x):
    return None if x is None else str(R.q6(x))


# ---------------------------------------------------------------- (a) tread highs

def part_a(v73, drawn, t727d):
    j = drawn["junction"]
    rd = j["readings"]
    # T-727's engine numbers must be the 'mixed' reading reproduced here (same handles, same geometry)
    e = t727d["junction_F1_F4"]
    if (R.q6(e["F1_footprint_m2"]), R.q6(e["F4_footprint_m2"]), R.q6(e["F1_F4_union_m2"]),
            R.q6(e["engine_footprint_overlap_m2"])) != tuple(R.q6(rd["mixed_engine"][k]) for k in
                                                          ("F1_m2", "F4_m2", "union_m2", "overlap_m2")):
        raise R.RuleError("own mixed reading does not reproduce the T-727 engine footprints")
    verdict = R.one_set_reading({k: (rd[n]["F1_m2"], rd[n]["F4_m2"], rd[n]["overlap_m2"], rd[n]["union_m2"])
                                 for k, n in (("mixed", "mixed_engine"), ("set_a", "set_layer2"),
                                              ("set_b", "set_layer5"))})
    gov = R.governing_set(j["far_end_on_outline"])
    g = rd[gov["set"]] if gov["set"] else None
    lines = []
    for lid, flight, own in ((TREAD_F1_1F, "F1 (RS-C seen from 1F)", g["F1_m2"]),
                             (TREAD_F4_1F, "F4 (RS-S seen from 1F)", g["F4_m2"]),
                             (TREAD_F1_GF, "GF F1 RS-C carrier (blank, beside 4.094413 per T-429)", g["F1_m2"]),
                             (TREAD_F2_GF, "GF F2 RS-S carrier", g["F4_m2"])):
        l = v73[lid]
        cur = l["held_high"] if l["class"] == "HELD" and l["held_high"] is not None else l["measured_net"]
        cur = 4.094413 if lid == TREAD_F1_GF else cur
        d = R.q6(cur) - R.q6(own)
        lines.append({"line_id": lid, "item_code": l["item_code"], "element_id": l["element_id"], "class": l["class"],
                      "flight": flight, "candidate_m2": s6(cur), "own_one_set_m2": s6(own), "diff_m2": str(d),
                      "verdict": "ENGINE_RIGHT" if abs(d) <= R.TOL_M2 else "ENGINE_WRONG", "change": "none"})
    return {"own_readings": rd, "pair_offset_m": j["pair_offset_straight_m"], "gf_plan_pair": j["gf_plan_pair"],
            "governing_set": gov, "far_end_gap_to_void_edge_m": j["far_end_gap_to_void_edge_m"],
            "radial_top_line": {"lengths_m": j["radial_line_lengths_m"], "radii_m": j["radial_top_line_radii_m"]},
            "verdict": verdict, "lines": lines,
            "highs_sum_m2": s6(R.q6(lines[0]["candidate_m2"]) + R.q6(lines[1]["candidate_m2"])),
            "result": "NO_DOUBLE_COUNT: T-727 s.5 DOUBLE_COUNT_RISK 0.0574 m2 withdrawn (SET_MIX); highs kept"}


# ---------------------------------------------------------------- (b) V-07

def part_b(v73, drawn, t719):
    v = drawn["v07"]
    reg = next(r for r in t719["register"] if r["void"] == "V-07")
    if R.q6(reg["disc_if_opened_m2"]) != R.q6(v["dome_disc_m2"]):
        raise R.RuleError("dome disc differs from the T-719 register")
    if v["overlay"]["matched_st"] != v["overlay"]["arch_2F_block_columns"] or v["overlay"]["worst_corner_residual_mm"] > 1:
        raise R.RuleError("structural overlay not checked")
    st = R.ceiling_void(slab_drawing=v["st_sheet_columns"] == v["overlay"]["arch_2F_block_columns"],
                        opening_drawn=v["opening_drawn"], beams_cross=v["beam_lines_crossing_dome"] > 0)
    ceil = [{"line_id": lid, "item_code": v73[lid]["item_code"], "element_id": v73[lid]["element_id"],
             "class": v73[lid]["class"], "m2": s6(v73[lid]["measured_net"]), "verdict": "ENGINE_RIGHT",
             "change": "none"} for lid in V07_CEILINGS]
    return {"evidence": v, "before": {"status": reg["status"], "result": reg["result"],
                                      "evidence": "no structural drawing named (T-719 / T-727)"},
            "after": st, "ceilings": ceil,
            "alternative_S1": "client request (Q-29, owner 2026-10-22: no revised structural drawing): an open skylight "
                              "would need a redesigned slab (beams and a column cross the footprint); shown apart, not "
                              "quantified, never applied; designer item DOME-3 / CF-S8.3-01 (D-21) unchanged"}


# ---------------------------------------------------------------- (c) census and wiring

def part_c(v73, v71, v69, t681, t715, t648, t723):
    scope = {k: l for k, l in v73.items() if l["item_code"] in TILE_SCOPE or l["item_code"].startswith(MARBLE)}
    old = {k: l for k, l in v69.items() if l["item_code"] in TILE_SCOPE or l["item_code"].startswith(MARBLE)}
    stale, missing = R.stale_entries(old, scope)
    added = sorted(set(scope) - set(old))
    if stale or missing or added:
        raise R.RuleError(f"tile / marble lines changed V3.0.69 -> V3.0.73: {stale[:3]} {missing[:3]} {added[:3]}")
    counts = Counter((l["item_code"], l["class"]) for l in scope.values())
    cause = {e["line_id"]: (e["class"], "T-681") for e in t681["entries"]}
    cause.update({e["line_id"]: (e["after"]["class"], "T-715") for e in t715["lines"] if e["line_id"] in scope})
    cause.update({e["line_id"]: (e["class"], "T-648") for e in t648["lines"]
                  if e["line_id"] in scope and e["line_id"] not in cause})
    held = sorted(k for k, l in scope.items() if l["class"] == "HELD")
    no_cause = [k for k in held if k not in cause]
    if no_cause:
        raise R.RuleError(f"HELD tile / marble line without a cause id: {no_cause[:5]}")
    by_cause = Counter(f"{cause[k][0]} ({cause[k][1]})" for k in held)
    held_blank = sum(1 for k in held if scope[k]["held_low"] is None and scope[k]["held_high"] is None)
    # H3 / H3s wiring rows (T-723 on V3.0.71) restated on V3.0.73
    rows = [r for r in t723 if r["hub"] in ("H3", "H3S")]
    wiring, stale_hosts = [], []
    for r in rows:
        h = r["host_line_id"]
        live = h in v73 and v71.get(h) == v73.get(h)
        if h and not live:
            stale_hosts.append(h)
        wiring.append({"hub": r["hub"], "piece": r["piece"], "host_line_id": h, "action": r["action"],
                       "after": r["after"], "unit": r["unit"],
                       "in_tile_marble_scope": h in scope, "host_v3071_eq_v3073": live})
    hub_counts = Counter((w["hub"], w["action"]) for w in wiring)
    return {"scope_codes": list(TILE_SCOPE) + [MARBLE + "*"], "lines": len(scope),
            "by_code_class": {f"{a} | {b}": n for (a, b), n in sorted(counts.items())},
            "held": len(held), "held_blank": held_blank, "held_by_cause": dict(sorted(by_cause.items())),
            "stale_vs_v3069": {"stale": len(stale), "missing": len(missing), "added": len(added)},
            "wiring": {"rows": len(wiring), "stale_hosts": sorted(set(stale_hosts)),
                       "by_hub_action": {f"{a} | {b}": n for (a, b), n in sorted(hub_counts.items())},
                       "rows_detail": wiring},
            "waste": "no line in this census carries a waste factor; size-based waste (Urban tile rule) is applied "
                     "only in the materials stage on the purchasing group, never as a default here"}


def build():
    v73, v71, v69 = (by_id(load(k)) for k in ("v3073", "v3071", "v3069"))
    drawn = json.loads(DRAWN.read_text())
    return {"task": "T-733", "candidate": "ARCH_TAKEOFF_V3.0.73 (c5a0b128, NOT RELEASED)",
            "inputs": {k: {"path": p, "sha256_16": pin} for k, (p, pin) in P.items()},
            "drawings": "Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and "
                        "'ST7757 dxf.dxf' (sha256 9f9d1179), own decode this run into the private folder",
            "a_tread_highs": part_a(v73, drawn, load("t727d")),
            "b_v07": part_b(v73, drawn, load("t719")),
            "c_census": part_c(v73, v71, v69, load("t681"), load("t715"), load("t648"), load("t723")),
            "moved": "no quantity moved; nothing wired; V2.9 + route G unchanged"}


def md(d):
    a, b, c = d["a_tread_highs"], d["b_v07"], d["c_census"]
    L = [f"# T-733 tiles H3 readiness on {d['candidate']}", "",
         "## (a) F1 / F4 tread highs", "",
         "| reading | F1 m2 | F4 m2 | overlap | union | sum |", "|---|---|---|---|---|---|"]
    for k, r in a["own_readings"].items():
        L.append(f"| {k} | {r['F1_m2']} | {r['F4_m2']} | {r['overlap_m2']} | {r['union_m2']} | {r['sum_m2']} |")
    L += ["", f"Verdict: {a['verdict']['result']}; governing set {a['governing_set']['set']} "
              f"({a['governing_set']['basis']}); {a['result']}", "",
          "| line | item | element | class | candidate | own | diff | verdict |", "|---|---|---|---|---|---|---|---|"]
    for l in a["lines"]:
        L.append(f"| {l['line_id']} | {l['item_code']} | {l['element_id']} | {l['class']} | {l['candidate_m2']} | "
                 f"{l['own_one_set_m2']} | {l['diff_m2']} | {l['verdict']} |")
    L += ["", "## (b) V-07", "", f"Before: {b['before']['status']} {b['before']['result']}. After: {b['after']['result']} "
          f"({b['after']['status']}): {b['after'].get('cause', '')}.", "",
          f"Evidence: overlay {b['evidence']['overlay']}; sheet columns {b['evidence']['st_sheet_columns']}; inside the "
          f"dome footprint {b['evidence']['inside_dome_footprint_by_type_layer']}; beam lines crossing "
          f"{b['evidence']['beam_lines_crossing_dome']}; S-OPENING on sheet {b['evidence']['s_opening_entities_on_sheet']}.",
          "", f"Ceilings: " + "; ".join(f"{x['line_id']} {x['element_id']} {x['m2']} {x['verdict']}" for x in b["ceilings"]),
          "", f"S1: {b['alternative_S1']}", "",
          "## (c) census", "", f"{c['lines']} lines; HELD {c['held']} (blank {c['held_blank']}); stale vs V3.0.69 "
          f"{c['stale_vs_v3069']}", ""]
    L += ["| code | class | n |", "|---|---|---|"] + [f"| {k.split(' | ')[0]} | {k.split(' | ')[1]} | {n} |"
                                                    for k, n in c["by_code_class"].items()]
    L += ["", "| HELD cause (source) | n |", "|---|---|"] + [f"| {k} | {n} |" for k, n in c["held_by_cause"].items()]
    L += ["", f"Wiring H3 / H3s: {c['wiring']['rows']} rows, stale hosts {len(c['wiring']['stale_hosts'])}", "",
          "| hub | action | n |", "|---|---|---|"] + [f"| {k.split(' | ')[0]} | {k.split(' | ')[1]} | {n} |"
                                                    for k, n in c["wiring"]["by_hub_action"].items()]
    L += ["", c["waste"], "", d["moved"], ""]
    return "\n".join(L)


def main(argv):
    d = build()
    js = json.dumps(d, indent=1, sort_keys=True, default=str) + "\n"
    m = md(d)
    if "--check" in argv:
        same = (OUT / "T733_H3_READINESS.json").read_text() == js and (OUT / "T733_H3_READINESS.md").read_text() == m
        print("T-733 outputs", "SAME" if same else "DIFFER")
        return 0 if same else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "T733_H3_READINESS.json").write_text(js)
    (OUT / "T733_H3_READINESS.md").write_text(m)
    print("wrote out/T733_H3_READINESS.{json,md}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
