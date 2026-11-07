"""T-606 builder (research, unwired): the T-574 room skirting UNRESOLVED 9.693234 lm split by room outline into named
causes (R-T606-1), from the committed drawing read T606_DRAWN.json (handles + lengths only), the merged T-574 ledger,
the T-460 V3.0.51 closure grosses, the V3.0.57 line index (candidate V3.0.58 skirting) and his tiles-sheet rows
(numbers only: perimeter column C, area column D; sheet keyed by a hash of its title as T-574 does).

    python3 -I research/agents_t606/t606_alsenan.py            (write out/)
    python3 -I research/agents_t606/t606_alsenan.py --check    (rebuild, byte-identical)

Nothing here changes a candidate, engine, rule / knowledge version or registry file; nothing is released.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t606_rules as R  # noqa: E402

D = Decimal
Z = D("0")
DRAWN = "research/agents_t606/T606_DRAWN.json"
T574 = "research/agents_t574/out/T574_SKIRTING_RECONCILE.json"
T460 = "research/agents_t460/SKIRTING_CLOSURE_V3051.csv"
LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {T574: "7b1e01bf83c20702", T460: "a2f3e6caa2893c5f", LINE_INDEX: "fed5141ea31bfdd9", RAW: "752c9f4e0c4546d0"}
OUTJ = HERE / "out" / "T606_OUTLINE_CAUSES.json"
CER = ("FIN", "ebc195c023cb")
UNRESOLVED_T574 = D("-9.693234")

# engine line (T-460 id prefix) re-measured by the drawn outline
REMEASURE = {"2F-MAID": "L-d057b5b05b9eaf131b59", "1F-380x430": "L-a8aea28451168e4032b6",
             "1F-500x365": "L-2f58111e59f0f5213c58", "GF-DRIVER": "L-bb0ea96508a0dc69603c",
             "GF-DEWANEYA": "L-d32414916cfbd04c27be", "1F-LIV.ours": "L-ba3599ec2dc82c221617",
             "1F-CUR.ours": "L-309f118f6fce78b6c28e"}
# T-574 group id prefix -> (his row, our drawn outline or None when not re-measured this run)
GROUPS = {"GF open room": ("13+15", None), "1F living": ("21", "1F-LIV.ours"),
          "1F curved east bed room": ("22", "1F-CUR.ours"), "2F corridor": ("29", "2F-CORR.ours")}
# the 2F corridor gross = lobby 5.25 + arrival 5.15 (T-460, MEASURED) + the 2.50 slab-opening edge (T-443 / T-574)
CORR_PARTS = ["L-9ff582c99c4d8e36c9a7", "L-dff4f49f47f341682fb3"]
CORR_EDGE = D("2.5")


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    bad = {p: _sha(p) for p, h in PINS.items() if _sha(p) != h}
    if bad:
        raise R.RuleError(f"inputs changed since T-606 pinned them: {bad}")
    return dict(PINS)


def his_rows():
    d = json.loads((ROOT / RAW).read_text())
    out = {}
    for x in d["rows"]:
        if (x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]) == CER:
            for c, v in x["cells"].items():
                out[c] = v["v"]
    rows = {}
    for r in (13, 15, 21, 22, 29):
        rows[str(r)] = (R.q6(out[f"C{r}"]), R.q6(out[f"D{r}"]))
    return rows


def build():
    pin = pins()
    drawn = json.loads((ROOT / DRAWN).read_text())
    O = drawn["outlines"]
    clos = {r["line_id"]: r for r in csv.DictReader((ROOT / T460).open(encoding="utf-8"))}
    idx = {x["line_id"]: x for x in json.loads((ROOT / LINE_INDEX).read_text())["lines"]}
    t574 = json.loads((ROOT / T574).read_text())
    his = his_rows()

    # 1. independent re-measures vs the engine gross (R-T606-1 step 2)
    rem = []
    for oid, lid in REMEASURE.items():
        d = R.check_ours(O[oid]["perimeter"], clos[lid]["gross"])
        rem.append({"outline": oid, "line": lid, "drawn": O[oid]["perimeter"], "engine_gross": clos[lid]["gross"],
                    "diff": str(d), "area": O[oid]["area"], "edges": [e["handle"] for e in O[oid]["edges"]]})
    corr = sum((D(clos[x]["gross"]) for x in CORR_PARTS), Z) + CORR_EDGE
    R.check_ours(O["2F-CORR.ours"]["perimeter"], corr)
    rem.append({"outline": "2F-CORR.ours", "line": "+".join(x[:10] for x in CORR_PARTS) + " + slab edge 2.50",
                "drawn": O["2F-CORR.ours"]["perimeter"], "engine_gross": str(corr), "diff": "0",
                "area": O["2F-CORR.ours"]["area"], "edges": [e["handle"] for e in O["2F-CORR.ours"]["edges"]]})

    # 2. the T-574 UNRESOLVED terms, by room
    unres = {}
    for g in t574["room"]["groups"]:
        for k in GROUPS:
            if g["id"].startswith(k):
                u = [D(c["amount"]) for c in g["causes"] if c["verdict"] == "UNRESOLVED"]
                unres[k] = sum(u, Z)
    if sum(unres.values(), Z) != UNRESOLVED_T574:
        raise R.RuleError(f"T-574 UNRESOLVED {sum(unres.values(), Z)} != {UNRESOLVED_T574}")

    P = {k: D(v["perimeter"]) for k, v in O.items()}
    A = {k: D(v["area"]) for k, v in O.items()}
    ad = drawn["addons"]
    rooms = []

    # ---- 1F living
    hp, ha = his["21"]
    if P["1F-LIV.ours"] - hp != unres["1F living"]:
        raise R.RuleError("1F living: ours gross - his != the T-574 UNRESOLVED term")
    st, both, ponly, aonly = R.match_reading(hp, ha, {"floor_drawn": (P["1F-LIV.floor_drawn"], A["1F-LIV.floor_drawn"]),
                                                       "floor_printed": (P["1F-LIV.floor_printed"],
                                                                         A["1F-LIV.floor_printed"])}, {})
    liv = R.close_room(P["1F-LIV.ours"], hp, [
        {"id": "LIV-WELL", "lm": str(P["1F-LIV.ours"] - P["1F-LIV.well_cut"]), "verdict": "ENGINE_RIGHT",
         "edges": ["B16", "ADE", "C21"],
         "label": "dog-leg well walls above the drawn landing edge (E B16 4.15, N ADE 2.50, W C21 4.50, column 3005 "
                  "returns 0.10) in our gross, his outline closes on the landing edge 2.85 (ABE 1.15 + A8F 0.35 + AC0 "
                  "1.35): no floor at +5.50 there, our net already removes them (T-508 shaft 9.05 + W13 / W25)"},
        {"id": "LIV-VOID", "lm": str(P["1F-LIV.well_cut"] - P["1F-LIV.floor_drawn"]), "verdict": "ENGINE_WRONG",
         "edges": ["AF7", "AEC"],
         "label": "stair-opening zone: our gross walks the walls AF7 4.00 + AEC 7.02 with columns 300E / 3008 "
                   "(notches 0.20), his the opening edges B74 5.87 + B75 1.60 + D24 1.15 + AF5 2.40 (11.02): the 0.20 "
                   "of notch faces is the gross difference; the 11.22 lm of wall face itself is F-T606-1"},
    ])
    rooms.append({"room": "1F living / open stair hall", "his_row": "21", "his": [str(hp), str(ha)],
                  "reading_test": {"status": st, "both": both, "p_only": ponly, "a_only": aonly},
                  "closest": {"floor_drawn": [str(P["1F-LIV.floor_drawn"]), str(A["1F-LIV.floor_drawn"])]},
                  **liv})

    # ---- 1F curved bed room
    hp, ha = his["22"]
    if P["1F-CUR.ours"] - hp != unres["1F curved east bed room"]:
        raise R.RuleError("1F curved: ours gross - his != the T-574 UNRESOLVED term")
    bases = {k.split(".")[1]: (P[k], A[k]) for k in O if k.startswith("1F-CUR.")}
    adds = {k: (D(v["dP"]), D(v["dA"])) for k, v in ad["1F-CUR"].items()}
    st, both, ponly, aonly = R.match_reading(hp, ha, bases, adds)
    cur = R.close_room(P["1F-CUR.ours"], hp, [])
    rooms.append({"room": "1F curved east bed room + lobby", "his_row": "22", "his": [str(hp), str(ha)],
                  "reading_test": {"status": st, "both": both, "p_only": ponly, "a_only": aonly},
                  "readings": {k: [str(v[0]), str(v[1])] for k, v in bases.items()}, **cur})

    # ---- 2F corridor
    hp, ha = his["29"]
    if P["2F-CORR.ours"] - hp != unres["2F corridor"]:
        raise R.RuleError("2F corridor: ours gross - his != the T-574 UNRESOLVED term")
    bases = {k.split(".")[1]: (P[k], A[k]) for k in O if k.startswith("2F-CORR.")}
    adds = {k: (D(v["dP"]), D(v["dA"])) for k, v in ad["2F-CORR"].items()}
    st, both, ponly, aonly = R.match_reading(hp, ha, bases, adds)
    corr_r = R.close_room(P["2F-CORR.ours"], hp, [])
    rooms.append({"room": "2F corridor = lobby + arrival", "his_row": "29", "his": [str(hp), str(ha)],
                  "reading_test": {"status": st, "both": both, "p_only": ponly, "a_only": aonly},
                  "readings": {k: [str(v[0]), str(v[1])] for k, v in bases.items()}, **corr_r})

    # ---- GF open room: not re-measured this run (carried by name, never 0)
    hp = his["13"][0] + his["15"][0]
    ha = his["13"][1] + his["15"][1]
    rooms.append({"room": "GF open room (reception + dining + entrance zone + open pantry)", "his_row": "13+15",
                  "his": [str(hp), str(ha)], "ours": None, "gap": str(unres["GF open room"]),
                  "causes": [{"id": "residual", "lm": str(unres["GF open room"]), "verdict": "UNRESOLVED",
                              "residual": True,
                              "label": "not re-measured this run: his two rows' AREA re-adds to the room's gross "
                                       "outline (T-427, 0.30 m2) so his 72.92 is two sub-outline perimeters whose "
                                       "shared edge he counts twice, round pantry, garden band and stair zone that "
                                       "our face cuts off; follow-up row proposed"}],
                  "unresolved": str(unres["GF open room"])})

    named = sum((D(c["lm"]) for r in rooms for c in r["causes"] if c["verdict"] != "UNRESOLVED"), Z)
    left = sum((D(r["unresolved"]) for r in rooms), Z)
    if named + left != UNRESOLVED_T574:
        raise R.RuleError(f"split {named} + {left} != {UNRESOLVED_T574}")

    # F-T606-1: the stair-opening wall faces in our released 1F living net (no +5.50 floor beside them)
    liv_line = idx["L-ba3599ec2dc82c221617"]
    wc, fd = O["1F-LIV.well_cut"], O["1F-LIV.floor_drawn"]
    faces = D(wc["wall_lm"]) - D(fd["wall_lm"])
    released = D(t574["candidate_fin_skirting_released_lm"])
    finding = {"id": "F-T606-1", "line": "L-ba3599ec2dc82c221617", "line_net": str(R.q6(liv_line["measured_net"])),
               "lm": str(faces), "edges": ["AF7 (4.00 of 5.15)", "AEC (7.02 of 10.67)", "columns 300E / 3008 notches"],
               "verdict_proposal": "ENGINE_WRONG",
               "why": "the printed stair opening 5.87 x 4.00 (void B7A + round-stair treads, T-113 O1 / O2 / O3) and "
                      "the stair box 1.15 x 2.40 (arriving flight, T-113 L1) leave no room floor at +5.50 against "
                      "these faces; none of the line's deductions (doors 4.70, passage 1.00, glazing 3.10464, stair "
                      "W13 / W25 2.20, dog-leg shaft 9.05) lies on them",
               "released_V3_0_58": str(released), "if_confirmed": str(released - faces),
               "pct": str((-(faces) / released * 100).quantize(D("0.01")))}
    return {"schema": "T606_OUTLINE_CAUSES_V1", "rule": R.RULE_ID, "governing": R.GOVERNING, "pins": pin,
            "candidate": t574["candidate"], "released": "NOTHING RELEASED; research ledger",
            "t574_unresolved": str(UNRESOLVED_T574), "remeasured": rem, "rooms": rooms,
            "split": {"named": str(named), "unresolved": str(left)}, "finding": finding}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    txt = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        same = OUTJ.exists() and OUTJ.read_text(encoding="utf-8") == txt
        print("T606 check:", "byte-identical" if same else "DIFFERS")
        return 0 if same else 1
    OUTJ.parent.mkdir(exist_ok=True)
    OUTJ.write_text(txt, encoding="utf-8")
    print("written", OUTJ.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
