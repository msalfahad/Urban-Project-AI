"""T-612 builder (research, unwired): the room skirting UNRESOLVED remainder left by T-606 (GF open room -16.913904,
1F curved -0.73933, 2F corridor -0.70 lm) split by outline into named causes (R-T612-1 on R-T606-1), from the
committed drawing read T612_DRAWN.json (handles + lengths / areas only), the merged T-574 ledger, the merged T-606
output and his tiles-sheet rows (numbers only: perimeter column C, area column D; sheet keyed by a hash of its title).

    python3 -I research/agents_t612/t612_alsenan.py            (write out/)
    python3 -I research/agents_t612/t612_alsenan.py --check    (rebuild, byte-identical)

Nothing here changes a candidate, engine, rule / knowledge version or registry file; nothing is released.
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
sys.path.insert(0, str(HERE.parent / "agents_t606"))
import t612_rules as R  # noqa: E402
import t606_alsenan as T606  # noqa: E402

D = Decimal
Z = D("0")
DRAWN = "research/agents_t612/T612_DRAWN.json"
T574 = "research/agents_t574/out/T574_SKIRTING_RECONCILE.json"
T606_OUT = "research/agents_t606/out/T606_OUTLINE_CAUSES.json"
T606_DRAWN = "research/agents_t606/T606_DRAWN.json"
PINS = {T574: "7b1e01bf83c20702", T606_OUT: "e71d85471859e284", T606_DRAWN: "aaea4a9c6116afd9"}
OUTJ = HERE / "out" / "T612_REMAINDER_CAUSES.json"
LINE = "L-71e2e002a3af624097f0"
ENGINE_GROSS = D("56.006096")      # T-460 V3.0.51 closure gross of LINE (pinned by T-606's T460 pin)
T427_OUTLINE_AREA = D("147.658")   # T-427 s.3 own polygonization less the wash lobby part and its mouth (two routes)
T606_REMAINDER = {"GF open room": D("-16.913904"), "1F curved east bed room": D("-0.73933"),
                  "2F corridor": D("-0.7")}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    T606.pins()                                   # the T-606 inputs unchanged (T-574, T-460, line index, his rows)
    bad = {p: _sha(p) for p, h in PINS.items() if _sha(p) != h}
    if bad:
        raise R.RuleError(f"inputs changed since T-612 pinned them: {bad}")
    return dict(PINS)


def _gf(drawn, his, t574):
    O = drawn["outlines"]
    face, full = O["GF-OPEN.face"], O["GF-OPEN.full"]
    # step 2 (R-T606-1): our face re-measures to the engine line's gross
    R.check_ours(face["perimeter"], ENGINE_GROSS)
    if (D(full["area"]) - T427_OUTLINE_AREA).copy_abs() > D("0.0005"):
        raise R.RuleError("the drawn gross outline is not T-427's outline")
    hp = his["13"][0] + his["15"][0]
    ha = his["13"][1] + his["15"][1]
    g = next(x for x in t574["room"]["groups"] if x["id"].startswith("GF open room"))
    unres = sum((D(c["amount"]) for c in g["causes"] if c["verdict"] == "UNRESOLVED"), Z)
    if unres != T606_REMAINDER["GF open room"] or D(face["perimeter"]) - hp != unres:
        raise R.RuleError("GF open room: engine gross - his != the T-574 / T-606 UNRESOLVED term")

    # cause 1: engine face vs drawn gross outline, edge by edge (re-measured)
    fe = {e["handle"]: D(e["lm"]) for e in face["edges"]}
    ue = {e["handle"]: D(e["lm"]) for e in full["edges"]}
    by_edge = {h: fe.get(h, Z) - ue.get(h, Z) for h in sorted(set(fe) | set(ue)) if fe.get(h, Z) != ue.get(h, Z)}
    fn = {x["handle"]: D(x["lm"]) for x in face["notches"]}
    un = {x["handle"]: D(x["lm"]) for x in full["notches"]}
    by_notch = {h: fn.get(h, Z) - un.get(h, Z) for h in sorted(set(fn) | set(un)) if fn.get(h, Z) != un.get(h, Z)}
    c1 = D(face["perimeter"]) - D(full["perimeter"])
    if sum(by_edge.values(), Z) + sum(by_notch.values(), Z) != c1:
        raise R.RuleError("face vs outline: edges + notches do not re-add")

    # his summed rows against the drawn gross outline: reading test with every drawn piece he could walk
    ad = {k: (D(v["dP"]), D(v["dA"])) for k, v in drawn["addons"].items()}
    for k, v in drawn["islands"].items():
        ad[f"walk round {k} (gross area kept)"] = (D(v["perimeter"]), Z)
        ad[f"walk round {k} (area net of it)"] = (D(v["perimeter"]), -D(v["area"]))
    bases = {"drawn gross outline": (D(full["perimeter"]), D(full["area"])),
             "engine face": (D(face["perimeter"]), D(face["area"]))}
    st, both, ponly, aonly = R.match_reading(hp, ha, bases, ad, max_addons=4)
    # R-T612-1.3: an undrawn split between his two rows, as a bound only
    walkable = sum((v[0] for k, v in ad.items() if "area net" not in k), Z)
    s_max = R.split_bound(hp, full["perimeter"])
    s_min = R.split_bound(hp, full["perimeter"], walkable)
    own = his["15"]
    rect = R.rect_from_pp(own[0], own[1])
    pure = {"split_lm": str(s_max), "entrance_outer_lm": str(own[0] - s_max),
            "reception_check": str(D(full["perimeter"]) - (own[0] - s_max) + s_max)}
    if D(pure["reception_check"]) != his["13"][0]:
        raise R.RuleError("the pure-split reading does not re-add to his reception row")
    room = R.close_room(face["perimeter"], hp, [
        {"id": "GF-FACE-VS-OUTLINE", "lm": str(c1), "verdict": "ENGINE_RIGHT", "edges": sorted(by_edge),
         "label": "engine face GF-RC99C2A vs the drawn gross outline his area re-adds to: the face's south side runs on "
                  "the band / curb line A8 13.82 + band end 30F 1.50 (both virtual, no skirting) with the columns "
                  "2FD2 / 2FC6 notched (0.30), the outline on the south facade 104 (13.82 more) + west wall AE (1.50 "
                  "more) with the facade columns 2FCF / 2FD5 notched (0.20): +15.32 + 0.30 - 13.82 - 1.50 - 0.20. "
                  "No skirting quantity: the face's virtual edges are deducted (T-574), and the facade 3.90 of the "
                  "dining piece is already the T-431 cause"},
    ])
    res = D(room["unresolved"])
    if res != D(full["perimeter"]) - hp:
        raise R.RuleError("residual != drawn outline - his")
    room["causes"][-1]["label"] = (
        "his two rows 58.16 + 14.76 against the drawn gross outline 55.906096 (area 147.657717 vs his 147.96, +0.302283 "
        "m2): no drawn reading reproduces both (reading test below); the only reading that re-adds his perimeters is an "
        "UNDRAWN split between his rows counted in both: " + str(s_max) + " lm if he walked nothing else, " + str(s_min)
        + " lm if he walked every drawn piece (bound, R-T612-1.3), and no split changes his area: the +0.302283 m2 is "
        "his row above the drawn outline (T-427 'UNEXPLAINED 0.3023', reproduced here by a second route)")
    return {"room": "GF open room (reception + dining + entrance zone + open pantry)", "his_row": "13+15",
            "his": [str(hp), str(ha)], "his_rows": {k: [str(v[0]), str(v[1])] for k, v in his.items()
                                                     if k in ("13", "15")},
            "remeasured": {"engine face": [face["perimeter"], face["area"], "engine gross " + str(ENGINE_GROSS)],
                           "drawn gross outline": [full["perimeter"], full["area"], "T-427 " + str(T427_OUTLINE_AREA)]},
            "face_vs_outline": {"by_edge": {k: str(v) for k, v in by_edge.items()},
                                "by_notch": {k: str(v) for k, v in by_notch.items()}, "total": str(c1)},
            "reading_test": {"status": st, "both": both, "p_only": ponly[:12], "p_only_count": len(ponly),
                             "a_only": aonly[:12], "a_only_count": len(aonly)},
            "split_bound": {"undrawn_split_lm_max": str(s_max), "undrawn_split_lm_min": str(s_min),
                            "pure_split_reading": pure,
                            "his_entrance_as_rectangle_sides": [str(x) for x in rect] if rect else None,
                            "grid_test": drawn["grid_test"]},
            "interior_solids": drawn["islands"], **room}


def _carried(t606, name, prefix, extra):
    r = next(x for x in t606["rooms"] if x["room"].startswith(prefix))
    if D(r["unresolved"]) != T606_REMAINDER[name]:
        raise R.RuleError(f"{name}: T-606 residual changed")
    return dict(r, t612=extra)


def build():
    pin = pins()
    drawn = json.loads((ROOT / DRAWN).read_text())
    t574 = json.loads((ROOT / T574).read_text())
    t606 = json.loads((ROOT / T606_OUT).read_text())
    t606d = json.loads((ROOT / T606_DRAWN).read_text())
    his = T606.his_rows()
    rooms = [_gf(drawn, his, t574)]

    # 1F curved: the arc / chord question answered by sign (R-T612-1.4): an arc read as its chord makes the perimeter
    # SMALLER and the area LARGER; his row is larger in lm and smaller in m2 than our arc reading
    O = t606d["outlines"]
    arc_e = next(e for e in O["1F-CUR.ours"]["edges"] if e["handle"] == "BD2")
    ours_p, ours_a = D(O["1F-CUR.ours"]["perimeter"]), D(O["1F-CUR.ours"]["area"])
    ch_p, ch_a = D(O["1F-CUR.chord"]["perimeter"]), D(O["1F-CUR.chord"]["area"])
    hp, ha = his["22"]
    cur = {"arc_edge_lm": arc_e["lm"], "chord_reading": [str(ch_p), str(ch_a)],
           "arc_minus_chord_lm": str(ours_p - ch_p), "segment_m2": str(ch_a - ours_a),
           "his_minus_ours": [str(hp - ours_p), str(ha - ours_a)],
           "sign_test": "an arc read as its chord: dP " + str(ch_p - ours_p) + ", dA +" + str(ch_a - ours_a)
                        + "; his dP +" + str(hp - ours_p) + ", dA " + str(ha - ours_a)
                        + ": opposite signs on both, so 'arc vs chord' explains none of the 0.73933 lm",
           "verdict": "UNRESOLVED (T-606 readings stand: 4 bases x 2 door reveals, none reproduces either figure)"}
    if not (ch_p < ours_p < hp and ha < ours_a < ch_a):
        raise R.RuleError("curved room: the sign test no longer holds")
    rooms.append(_carried(t606, "1F curved east bed room", "1F curved", cur))

    hp, ha = his["29"]
    corr = {"candidates_perimeter_only": "maid 2 x 0.20 + roof 2 x 0.15 = 0.70 (area 7.705, on his rounding boundary) "
                                         "and lift + roof reveals 0.70 (area 7.725): both refused (R-T606-1 step 4)",
            "verdict": "UNRESOLVED (no drawn reading reproduces both his 13.60 and his 7.70)"}
    rooms.append(_carried(t606, "2F corridor", "2F corridor", corr))

    total = sum(T606_REMAINDER.values(), Z)
    named = sum((D(c["lm"]) for r in rooms for c in r["causes"] if c["verdict"] != "UNRESOLVED"), Z)
    left = sum((D(r["unresolved"]) for r in rooms), Z)
    if named + left != total:
        raise R.RuleError(f"split {named} + {left} != {total}")
    return {"schema": "T612_REMAINDER_CAUSES_V1", "rule": R.RULE_ID, "base_rule": R.BASE_RULE,
            "governing": R.GOVERNING, "pins": pin, "released": "NOTHING RELEASED; research ledger",
            "t606_remainder": {k: str(v) for k, v in T606_REMAINDER.items()}, "t606_remainder_total": str(total),
            "rooms": rooms, "split": {"named": str(named), "unresolved": str(left)}}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    txt = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        same = OUTJ.exists() and OUTJ.read_text(encoding="utf-8") == txt
        print("T612 check:", "byte-identical" if same else "DIFFERS")
        return 0 if same else 1
    OUTJ.parent.mkdir(exist_ok=True)
    OUTJ.write_text(txt, encoding="utf-8")
    print("written", OUTJ.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
