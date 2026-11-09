"""T-617 builder (research, unwired): LIFT LANDING HEAD HEIGHT bounded from the drawn members, training villa.

Reads T617_DRAWN.json (handles / marks only), the merged T-608 scope table (pinned sha256) and the worker's readings of
the raster / text-less PDF sheets listed in READINGS (each with its sheet; values only, no drawing content). Writes
out/T617_HEAD_BOUNDS.json / .md. No candidate, engine, rule, knowledge or registry file is touched; nothing released.

    python3 -I research/agents_t617/t617_alsenan.py --write | --check
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
import t617_rules as R  # noqa: E402

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "T617_HEAD_BOUNDS.json"
MD_OUT = OUT / "T617_HEAD_BOUNDS.md"
INPUTS = {"DRAWN": "research/agents_t617/T617_DRAWN.json",
          "T608": "research/agents_t608/out/T608_SCOPE_TABLE.json",
          "T556": "research/agents_t556/T-556_PLASTER_HEIGHT_METHOD.md",
          "T401": "research/agents_t401/T-401_LIFT_STRUCTURE.md"}
PINNED = {"T608": "e138a0f3f7c6d9729f68399a10223ffb7ae6cfd9d859a7bca9a3a58befddd4a8"}

# Worker readings (2026-11-08) of sheets that carry no text layer / are not in the DXF; values and sheet only.
READINGS = {
    "schedule_depth_m": {"B1": "0.40", "B2": "0.40", "B7": "0.75", "B14": "0.75",
                         "_src": "ST PDF p.10 'Schedule of Simple Beams', column D-(Depth) cm (B1 20x40, B2 20x40, "
                                 "B7 20x75, B14 20x75); overall depth with the slab inside it (FULL basis, R-T395-1)"},
    "slab_t_m": {"v": "0.16", "_src": "ST p.8 note 18 (normal slab 16 cm unless stated) + 'T 16' on the GF / 1F roof "
                                      "plans at the shaft; the 2F roof plan marks T18 only on the tank panels"},
    "ffl": {"GF": "1.00", "1F": "5.50", "2F": "9.70", "ROOF": "13.90",
            "_src": "architectural sheet 10 section A-A levels (T-556 table, Verifier-checked)"},
    "b_floor_m": {"v": "0.05", "_src": "T-214 floor build-up, Verifier re-measured (reused by T-556); bound b >= 0"},
    "r_roof_m": {"v": None, "scenario": "0.05",
                 "_src": "roof build-up NOT printed (D-39 / DCR-6); drawn-section scenario 0.05 (T-556); bound r >= 0"},
    "note19": {"level_m": "3.00", "applies_if_interval_gt_m": "4.30",
               "_src": "ST p.8 recommendation 19 (raster, Arabic): beams to tie the LIFT COLUMNS at a height of 3.00 m "
                       "where the storey height exceeds 4.30 m; no section, no datum point, no sides drawn (no tie-beam "
                       "label on any structural plan: DXF text search 'T.B' / 'TIE' = 0)"},
    "p14": {"_src": "ST p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING' (vector, no text layer): 'Lift door' leader at the "
                    "F.F.L. on the shaft-front wall drawn 'AS PER PLAN' above the slab-on-grade, broken off above; "
                    "pit depth 'As Per Lift Manufactures recommendations'; no landing-door height or head level"},
    "arch_sections": {"_src": "architectural sheet 10 section A-A does not cut the shaft (T-608); sheet 9 = NORTH EAST "
                              "ELEVATION (exterior only; the shaft is internal); P7757.dxf holds plans + SOUTH EAST / "
                              "NORTH WEST elevations, no section through the shaft"},
}
STOREYS = [("GF", "GF_ROOF", "1F"), ("1F", "1F_ROOF", "2F"), ("2F", "2F_ROOF", "ROOF")]
# Q-72 plaster face height per storey under a slab (T-556 R-T556-1): interval - b - t; under the roof the scenario r.
HIS_H = D("2.40")


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def q(x, n="0.0001"):
    return None if x is None else str(D(x).quantize(D(n)))


def build():
    for k, v in PINNED.items():
        if sha(INPUTS[k]) != v:
            raise SystemExit(f"{INPUTS[k]} changed since T-617 pinned it: re-read before using this table")
    drawn = json.loads((ROOT / INPUTS["DRAWN"]).read_text(encoding="utf-8"))
    t608 = json.loads((ROOT / INPUTS["T608"]).read_text(encoding="utf-8"))
    faces = {}
    for r in t608["rows"]:
        if r["family"] == "WALL_FACES":
            faces[r["storey"]] = {"face_h": D(r["expected"]["bound"][1]),
                                  "lines": [{k: l[k] for k in ("line_id", "item_code", "held_low", "held_high")}
                                            for l in r["lines"]]}
    rd, depth = READINGS, READINGS["schedule_depth_m"]
    t, b = D(rd["slab_t_m"]["v"]), D(rd["b_floor_m"]["v"])
    r_scen = D(rd["r_roof_m"]["scenario"])
    rows, totals = [], {"candidate_m2_narrowed": D("0"), "candidate_m2_narrowed_scenario": D("0")}
    for st, plan, nxt in STOREYS:
        arch = drawn["architectural"][st]
        side = arch["door_side"]
        mem = drawn["structural"][plan]["sides"][side]
        mark = mem["mark"]
        Dp = D(depth[mark])
        H = D(rd["ffl"][nxt]) - D(rd["ffl"][st])
        is_roof = nxt == "ROOF"
        firm = R.beam_soffit(H, "0", Dp)                         # b or r >= 0: firm upper bound
        at_drawn = R.beam_soffit(H, r_scen if is_roof else b, Dp)
        members = [{"id": f"{mark} ({plan}, {side} side, DXF {mem['handle']})", "soffit": at_drawn,
                    "on_wall_line": True}]
        tie = None
        if H > D(rd["note19"]["applies_if_interval_gt_m"]):
            tie = R.note_member_soffit(rd["note19"]["level_m"])
            members.append({"id": "note 19 tie beam at 3.00 m (sides not drawn)", "soffit": tie,
                            "on_wall_line": "SCENARIO"})
        hb = R.head_bound(members)
        f = faces[st]
        face_h = f["face_h"]
        cand = R.face_deduction_bound("1.00", face_h, hb["high"])
        cand_s = R.face_deduction_bound("1.00", face_h, hb["high_scenario"])
        plaster_q72 = H - (r_scen if is_roof else b) - t
        q72 = R.face_deduction_bound("1.00", plaster_q72, hb["high"])
        q72_s = R.face_deduction_bound("1.00", plaster_q72, hb["high_scenario"])
        totals["candidate_m2_narrowed"] += cand["narrowing"] * len(f["lines"])
        totals["candidate_m2_narrowed_scenario"] += cand_s["narrowing"] * len(f["lines"])
        lines_after = []
        for l in f["lines"]:
            lo = D(l["held_low"])
            lines_after.append({**l, "held_low_after": q(lo + cand["narrowing"]),
                                "held_low_after_note19_scenario": q(lo + cand_s["narrowing"])})
        his = "UNRESOLVED (admissible: 2.40 <= every drawn bound; printed nowhere, so neither ENGINE_RIGHT nor " \
              "FREELANCER_RIGHT)" if HIS_H <= hb["high_scenario"] else "CONTRADICTED by a drawn member (ENGINE_RIGHT)"
        rows.append({
            "storey": st, "opening": {"GF": "GF OP-011 (L-GF-01)", "1F": "1F OP-007 (L-1F-01)",
                                      "2F": "2F OP-002 (L-2F-01)"}[st],
            "door_side_arch": side, "member_over_door": {"mark": mark, "dxf_handle": mem["handle"], "plan": plan,
                                                         "depth_m": str(Dp), "src": depth["_src"]},
            "interval_m": str(H), "slab_top_term": ("roof build-up r (not printed; scenario 0.05; r >= 0)" if is_roof
                                                    else "floor build-up b 0.05 (T-214; b >= 0)"),
            "head": {"printed": None, "low": "0 (nothing printed; named)",
                     "high_firm": q(firm, "0.01"), "high_at_drawn_buildup": q(hb["high"], "0.01"),
                     "high_note19_scenario": q(hb["high_scenario"], "0.01") if tie is not None else None,
                     "status": "BOUNDED (DRAWING-BOUNDED above; lower bound not printed)" if not is_roof else
                               "BOUNDED (firm r >= 0; value at the ESTIMATED roof scenario)"},
            "candidate_faces": {"face_h_G1_m": str(face_h), "deduction_m2": [q(cand["low"]), q(cand["high"])],
                                "narrowing_m2_per_line": q(cand["narrowing"]),
                                "narrowing_m2_per_line_note19": q(cand_s["narrowing"]), "lines": lines_after},
            "q72_plaster_for_T558": {"face_h_m": q(plaster_q72, "0.01"), "deduction_cap_m2": q(q72["high"]),
                                     "always_plastered_above_head_m2": q(q72["narrowing"]),
                                     "note19_scenario_m2": q(q72_s["narrowing"]),
                                     "check_D_minus_t": q(Dp - t, "0.01")},
            "freelancer_2_40": his,
            "lintel": "count 0 .. 1 unchanged: the head may meet the beam soffit (no lintel) or sit lower (lintel L1 "
                      "under the masonry above); nothing drawn decides it",
            "blockwork": "no narrowing: the host-wall deduction bound (T-175 wall height) is below the beam soffit "
                         "measured from the structural slab top (1F 4.20 - 0.75 = 3.45 >= 3.35; GF slab-on-grade top "
                         "not printed, T-401 RFI 1; 2F >= 3.80 - r)"})
    findings = [
        {"id": "F-T617-1", "what": "every landing-door head is bounded ABOVE by a drawn ring beam on the door side "
                                   "(GF roof B14 20x75, 1F roof B7 20x75, 2F roof B2 20x40; DXF marks 45F / 6CC / 78A, "
                                   "schedule p.10): GF <= 3.70 (3.75 at b = 0), 1F <= 3.40 (3.45), 2F <= 3.80 - r. No "
                                   "printed value bounds it BELOW: the height stays HELD, never a default"},
        {"id": "F-T617-2", "what": "the candidate paint / plaster lines (G1 face heights GF 3.65, 1F 3.35, 2F 3.35) all "
                                   "sit at or below those soffits: the drawn members do NOT narrow 1F-13 / 2F-01 / "
                                   "GF-08 (0.000 m2); only the note-19 GF tie-beam reading would (GF-08 low end +0.65 "
                                   "m2 per line) and its sides are not drawn (SCENARIO, structural RFI item 38)"},
        {"id": "F-T617-3", "what": "for T-558 (Q-72 plaster to the slab soffit): an opening under a member of overall "
                                   "depth D in a slab t can never deduct the (D - t) band: GF 0.59, 1F 0.59, 2F 0.24 m2 "
                                   "per landing face stay plastered whatever the head (1.00 m wide); independent of "
                                   "b / r"},
        {"id": "F-T617-4", "what": "T-608's text census could not see ST p.8 (raster) or ST p.14 (vector, no text "
                                   "layer): note 19 and the p.14 'Lift door' / 'As Per Lift Manufactures "
                                   "recommendations' leaders exist on the PDF only; a DXF-only census is not a census of "
                                   "the set (lesson row proposed)"},
    ]
    return {"schema": "T617_HEAD_BOUNDS_V1", "task": "T-617", "rule": R.RULE_ID, "governing": R.GOVERNING,
            "inputs": {k: sha(v) for k, v in INPUTS.items()}, "readings": READINGS, "rows": rows,
            "summary": {"candidate_m2_narrowed_all_lines": q(totals["candidate_m2_narrowed"]),
                        "candidate_m2_narrowed_note19_scenario": q(totals["candidate_m2_narrowed_scenario"]),
                        "released_quantities_changed": 0, "candidate_files_touched": 0},
            "findings": findings}


def md(d):
    L = ["# T-617 lift landing head bounds (generated; see T-617_LIFT_LANDING_HEAD.md)", "",
         "| Storey | Member over door | Interval | Head high (firm / at drawn b, r) | Note-19 scenario | Face G1 | "
         "Candidate narrowing / line | Q-72 plaster kept above head | His 2.40 |", "|" + "---|" * 9]
    for r in d["rows"]:
        h = r["head"]
        L.append(f"| {r['storey']} | {r['member_over_door']['mark']} D {r['member_over_door']['depth_m']} "
                 f"({r['member_over_door']['dxf_handle']}) | {r['interval_m']} | {h['high_firm']} / "
                 f"{h['high_at_drawn_buildup']} | {h['high_note19_scenario'] or '-'} | "
                 f"{r['candidate_faces']['face_h_G1_m']} | {r['candidate_faces']['narrowing_m2_per_line']} "
                 f"(note 19: {r['candidate_faces']['narrowing_m2_per_line_note19']}) | "
                 f"{r['q72_plaster_for_T558']['always_plastered_above_head_m2']} | {r['freelancer_2_40'].split(' (')[0]} |")
    L += ["", f"Candidate m2 narrowed (all lines): {d['summary']['candidate_m2_narrowed_all_lines']}; with the note-19 "
              f"scenario: {d['summary']['candidate_m2_narrowed_note19_scenario']}.", ""]
    L += [f"- {f['id']}: {f['what']}" for f in d["findings"]]
    return "\n".join(L) + "\n"


def main(argv):
    d = build()
    j = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    m = md(d)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(j, encoding="utf-8")
        MD_OUT.write_text(m, encoding="utf-8")
        print("wrote", JSON_OUT.name, MD_OUT.name)
        return 0
    ok = JSON_OUT.exists() and JSON_OUT.read_text(encoding="utf-8") == j and MD_OUT.read_text(encoding="utf-8") == m
    print("byte-identical" if ok else "DIFFERS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
