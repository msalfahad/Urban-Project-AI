"""T-585 development-villa build (research only; nothing released, no candidate / engine / rule file changed).

Inputs (pinned): YARD_FACES_T585.json (face table read from the architectural DXF by worker 2 on 2026-11-07, lengths and
handles only), research/agents_t501/LINES_T501.csv (flight pieces), research/agents_t574/out/T574_SKIRTING_RECONCILE.json
(the table this task restates) and tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (his yard / stair numbers only,
read through the T-574 sheet / label hashes). Usage: python -I t585_alsenan.py [--check | --write]
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t585_rules as R  # noqa: E402

FACES = "research/agents_t585/YARD_FACES_T585.json"
T501 = "research/agents_t501/LINES_T501.csv"
T574 = "research/agents_t574/out/T574_SKIRTING_RECONCILE.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {T501: "1551662ca02dbca1", RAW: "752c9f4e0c4546d0", T574: "7b1e01bf83c20702"}
SELF_PINS = (FACES,)
OUT = HERE / "out" / "T585_SKIRTING_FOLLOWUPS.json"
D = R.D
Z = Decimal(0)
E1_RISE = "0.85"


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")
    return {**PINS, **{p: _sha(p) for p in SELF_PINS}}


def _t574_module():
    spec = importlib.util.spec_from_file_location("t574_alsenan", ROOT / "research/agents_t574/t574_alsenan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def S(x):
    if x is None:
        return None
    return str(D(x).quantize(R.Q6).normalize()) if D(x) != 0 else "0"


# ---- (1) yard ----------------------------------------------------------------------------------------------------------
ZONE_NAME = {"WC": "west court (interlock)", "NS": "north side walk (porcelain)", "PO": "covered porch (finish HELD)",
             "PC": "pool court deck (finish HELD)"}


def yard(cells, t574):
    doc = json.loads((ROOT / FACES).read_text())
    faces = doc["faces"]
    res = R.yard_totals(faces)
    per = {}
    for f, r in zip(faces, res["rows"]):
        z = per.setdefault(f["zone"], {"zone": ZONE_NAME[f["zone"]], "finish": doc["zones"][f["zone"]]["finish"],
                                       "faces": 0, "length": Z, "by_class": {}, "by_host": {}})
        z["faces"] += 1
        z["length"] += r["length"]
        z["by_class"][r["class"]] = z["by_class"].get(r["class"], Z) + r["length"]
        z["by_host"][f["host"]] = z["by_host"].get(f["host"], Z) + r["length"]
    stair = sum((D(x["length"]) for x in doc["stair_owned"]), Z)
    stair_open = sum((D(x["length"]) for x in doc["stair_owned_openings"]), Z)
    resid = D(doc["yard_face"]["polygon_residual_lm"])
    perim = D(doc["yard_face"]["perimeter_lm"])
    if res["perimeter_lm"] + stair + stair_open + resid != perim:
        raise R.RuleError("yard faces + stair-owned faces + named residual do not close to the yard face perimeter")
    # wall-foot lengths by class (sill windows apart: their wall foot is a range)
    nid_wall = sum((r["length"] for f, r in zip(faces, res["rows"])
                    if r["class"] == "NOT_IN_DRAWING" and f["host"] != "SILL_WINDOW"), Z)
    nid_sill = sum((r["length"] for f, r in zip(faces, res["rows"])
                    if r["class"] == "NOT_IN_DRAWING" and f["host"] == "SILL_WINDOW"), Z)
    unres = res["unresolved_bound"][1]
    # his yard row: C13 perimeter (lm), D13 area (m2), G13 = C13 (formula) -> his skirting is his paving perimeter
    his_lm, his_m2 = D(cells["MRB.C13"]), D(cells["MRB.D13"])
    if D(cells["MRB.G13"]) != his_lm:
        raise R.RuleError("his yard skirting G13 is no longer his yard perimeter C13")
    gap = res["drawing_confirmed_lm"] - his_lm
    causes = [{"label": "his yard skirting is the perimeter typed for his yard paving row (C13 81.32 lm beside D13 151.80 "
                        "m2; G13 '=C13'): a paving outline, not a wall-face measure; no sheet prints a base, so every "
                        "drawn yard face is NOT_IN_DRAWING or UNRESOLVED: his extra is scope",
               "verdict": "RULE_DIFFERENCE", "kind": "SCOPE", "amount": S(gap),
               "note": "FREELANCER_SCOPE until an owner / designer text puts a base on the yard walls; never an "
                       "ENGINE_OMISSION"}]
    if sum((D(c["amount"]) for c in causes), Z) != gap:
        raise R.RuleError("yard causes do not close")
    old = t574["outdoor"]["groups"][0]
    return {
        "faces": [{"id": f["id"], "zone": f["zone"], "host": f["host"], "length": S(r["length"]),
                   "class": r["class"], "finish_basis": f["finish_basis"], "ref": f["ref"],
                   "bound": [S(r["lo"]), S(r["hi"])] if r["class"] == "UNRESOLVED" else None,
                   "physical_beside": S(r.get("physical"))} for f, r in zip(faces, res["rows"])],
        "zones": {k: {**v, "length": S(v["length"]), "by_class": {c: S(x) for c, x in v["by_class"].items()},
                      "by_host": {h: S(x) for h, x in v["by_host"].items()}} for k, v in per.items()},
        "closure": {"yard_faces_lm": S(res["perimeter_lm"]), "stair_owned_lm": S(stair),
                    "stair_owned_openings_lm": S(stair_open), "polygon_residual_lm": S(resid),
                    "yard_face_perimeter_lm": S(perim), "yard_face_area_m2": doc["yard_face"]["area_m2"]},
        "totals_lm": {"DRAWING-CONFIRMED": S(res["drawing_confirmed_lm"]),
                      "NOT_IN_DRAWING_physical_wall_foot": S(nid_wall),
                      "NOT_IN_DRAWING_under_unprinted_sills_range_hi": S(nid_sill),
                      "UNRESOLVED_bound": [S(Z), S(unres)],
                      "NO_FACE": S(res["by_class"]["NO_FACE"]["length"])},
        "base_evidence": doc["base_evidence"],
        "his": {"yard_skirting_lm": S(his_lm), "yard_area_m2": S(his_m2), "basis": "G13 = C13 (his paving perimeter)"},
        "ours_same_basis": {"yard_face_perimeter_lm": S(perim), "yard_face_area_m2": doc["yard_face"]["area_m2"],
                            "note": "the yard face (west court + porch + side walk + pool court) vs his one paving row: "
                                    "his outline is undimensioned, so no term-by-term match (T-153 P-1)"},
        "reconcile": {"ours": S(res["drawing_confirmed_lm"]), "his": S(his_lm), "gap": S(gap), "causes": causes,
                      "pct": None, "pct_withheld": "scope cause (R-T574-1 (e))"},
        "t574_before": {"ours": old["ours"], "his": old["his"], "verdict": old["causes"][0]["verdict"]},
    }


# ---- (2) stairs --------------------------------------------------------------------------------------------------------
STAIR_OF = {"E1": "ST-03 entrance (E1)", "MS1": "ST-01 main", "MS2": "ST-01 main", "D1": "ST-01 main",
            "RS": "ST-02 round (inner)"}


def _stair(pid):
    for k, v in STAIR_OF.items():
        if pid.startswith(k):
            return v
    raise R.RuleError(f"flight piece {pid} has no stair")


def stairs(t574):
    rows = list(csv.DictReader((ROOT / T501).open()))
    by = {}
    checks = []
    winders = [r for r in rows if r["pid"] in ("MS1-T.W", "MS1-T.N")]
    for r in rows:
        if r["kind"] not in ("FLIGHT", "STEP"):
            continue
        st = _stair(r["pid"])
        g = by.setdefault(st, {"pieces": [], "steps": []})
        if r["kind"] == "STEP":
            g["steps"].append({"pid": r["pid"], "status": r["status"], "lo": "0", "hi": S(r["zigzag_lm"]),
                               "cause": r["cause"]})
            continue
        if r["pid"] in ("MS1-T.W", "MS1-T.N"):
            continue
        p = {"pid": r["pid"], "status": r["status"], "cause": r["cause"] or None,
             "pitch": r["sloped_lm"] or None, "zigzag": r["zigzag_lm"] or None}
        if r["status"] == "UNKNOWN" and not r["sloped_lm"]:
            p["pitch"] = None
        if r["status"] == "HELD-FORM" and r["level0"]:
            plan, rise = D(r["plan_lm"]), abs(D(r["level1"]) - D(r["level0"]))
            own = R.pitch(plan, rise) + D(r["returns_lm"] or 0)
            if abs(own - D(r["sloped_lm"])) > Decimal("0.000002"):
                raise R.RuleError(f"{r['pid']}: pitch {own} != T-501 sloped {r['sloped_lm']}")
            checks.append({"pid": r["pid"], "plan": S(plan), "rise": S(rise), "returns": S(r["returns_lm"] or 0),
                           "pitch": S(own)})
        g["pieces"].append(p)
    # winder corner MS1-T: both faces are walls (GF 49E / 4A0 / 4A2, 26E); the rise 2.667 -> 3.50 is shared, split unknown
    lv = sorted({D(w["level0"]) for w in winders} | {D(w["level1"]) for w in winders})
    h = lv[-1] - lv[0]
    plans = {w["pid"]: D(w["plan_lm"]) for w in winders}
    lo, hi = R.winder_bound(plans["MS1-T.W"], plans["MS1-T.N"], h)
    by["ST-01 main"]["pieces"].append({"pid": "MS1-T.W + MS1-T.N", "status": "HELD", "lo": lo, "hi": hi, "pitch": None,
                                       "cause": "winder corner S-9 (5 risers on A-A vs 4 wedges); both faces walls; "
                                                f"pitch sum between the plans {S(lo)} and the whole rise {S(h)} on one "
                                                f"side {S(hi)}"})
    for p in by["ST-01 main"]["pieces"]:
        if p["pid"] == "MS1-T.W + MS1-T.N":
            p["hi_fixed"] = True
    out = {}
    for st, g in by.items():
        pieces = []
        for p in g["pieces"]:
            if p.get("hi_fixed"):
                pieces.append({"pid": p["pid"], "class": "HELD", "lo": p["lo"], "hi": p["hi"], "cause": p["cause"]})
            else:
                pieces.append(R.flight_line(p))
        two = [x for x in pieces if x["class"] == "MEASURED_TWO_FORMS"]
        rest = [x for x in pieces if x["class"] != "MEASURED_TWO_FORMS"]
        lo_ = sum((x["pitch"] for x in two), Z) + sum((D(x["lo"]) for x in rest), Z)
        hi_ = None if any(x["hi"] is None for x in rest) else (sum((x["zigzag"] for x in two), Z)
                                                             + sum((D(x["hi"]) for x in rest), Z))
        out[st] = {"two_form_pieces": len(two), "pitch_lm": S(sum((x["pitch"] for x in two), Z)),
                   "zigzag_lm": S(sum((x["zigzag"] for x in two), Z)),
                   "held": [{"pid": x["pid"], "class": x["class"], "bound": [S(x["lo"]), S(x["hi"])],
                             "cause": x.get("cause")} for x in rest],
                   "steps_held": g["steps"], "flight_lo": S(lo_), "flight_hi": S(hi_)}
    allp = sum((D(v["pitch_lm"]) for v in out.values()), Z)
    allz = sum((D(v["zigzag_lm"]) for v in out.values()), Z)
    if allp != D("17.009049") or allz != D("23.300481"):
        raise R.RuleError(f"two-form totals {allp} / {allz} differ from T-501 17.009049 / 23.300481")
    lo_all = sum((D(v["flight_lo"]) for v in out.values()), Z)
    return {"by_stair": out, "pitch_check": checks, "two_form_pitch_lm": S(allp), "two_form_zigzag_lm": S(allz),
            "flight_lo": S(lo_all), "t574_flight_lo": "17.009049",
            "flight_hi": None if any(v["flight_hi"] is None for v in out.values()) else
            S(sum((D(v["flight_hi"]) for v in out.values()), Z))}


def e1_landing():
    doc = json.loads((ROOT / FACES).read_text())
    land = [x for x in doc["stair_owned"] if x["id"].startswith("E1-L")]
    flight = [x for x in doc["stair_owned"] if x["id"] == "E1-F"][0]
    lm = sum((D(x["length"]) for x in land), Z)
    # E1 rise +0.15 -> +1.00 (T-412 FLIGHT_TABLE E1 / T-184 ST-03); plan 1.200 = 4 treads 0.30 between riser lines
    e1 = R.flight_sides(flight["length"], E1_RISE, ("WALL", "OPEN"))[0]
    if e1["pitch"].quantize(R.Q6) != D("1.470544") or e1["zigzag"] != D("2.05"):
        raise R.RuleError("E1 flight side does not reproduce T-501 E1.S 1.470544 / 2.05")
    return {"landing_faces": land, "landing_lm": S(lm), "status": "PROVISIONAL (research measure, not released)",
            "verdict_proposal": "ENGINE_OMISSION (level stair skirting of the E1 landing walls: the candidate carries "
                                "the E1 flight side E1.S but no line for the landing walls; same treatment as the ST-01 "
                                "landings MS1-LD / MS2-LD)",
            "flight_check": {"plan": flight["length"], "rise": E1_RISE, "pitch": S(e1["pitch"]),
                             "zigzag": S(e1["zigzag"]), "sides": "one wall side (pantry 15A), north side open"}}


def restate(t574, st, land, yd):
    rows = []
    gst = {g["id"]: g for g in t574["stairs"]["groups"] if g["unit"] == "lm"}
    for sid, g in gst.items():
        s = st["by_stair"][sid]
        add = D(land["landing_lm"]) if sid.startswith("ST-03") else Z
        # T-574's other HELD causes of the group (landing faces, stair-room RFI pieces): carried with their bounds
        other = [c for c in g["causes"] if c["kind"] == "HELD" and not c["label"].startswith("flight skirting")]
        o_lo = sum((D(c["bound"][0]) for c in other), Z)
        o_hi = None if any(c["bound"][1] is None for c in other) else sum((D(c["bound"][1]) for c in other), Z)
        steps_hi = sum((D(x["hi"]) for x in s["steps_held"]), Z)
        ours_lo = D(g["ours"]) + add + D(s["flight_lo"]) + o_lo
        ours_hi = (None if s["flight_hi"] is None or o_hi is None
                   else D(g["ours"]) + add + D(s["flight_hi"]) + o_hi + steps_hi)
        rows.append({"group": sid, "his": g["his"], "t574_ours_valued": g["ours"], "t574_bound": g["held_bound"],
                     "t585_landing_added": S(add) if add else None,
                     "t585_two_forms": {"pitch": s["pitch_lm"], "zigzag": s["zigzag_lm"]},
                     "t574_other_held_carried": [S(o_lo), S(o_hi)], "steps_held_hi": S(steps_hi),
                     "t585_ours_range": [S(ours_lo), S(ours_hi)],
                     "gap_range": [S(ours_lo - D(g["his"])), None if ours_hi is None else S(ours_hi - D(g["his"]))],
                     "changes": ["flight pieces: open bound 'HELD >= smaller form' restated as two measured forms "
                                 "(pitch | zigzag, ORR-007 picks one) + bounded held pieces"]
                     + (["E1 landing walls 3.500 lm measured (ENGINE_OMISSION proposal)"] if add else [])
                     + (["winder corner MS1-T bounded [2.35, %s] (was blank)" % st["by_stair"][sid]["held"][-1]["bound"][1]]
                        if sid == "ST-01 main" else [])})
    o = yd["reconcile"]
    rows.append({"group": "OUTDOOR yard", "his": o["his"], "t574_ours_valued": "0",
                 "t574_verdict": yd["t574_before"]["verdict"], "t585_ours": o["ours"],
                 "t585_verdict": "RULE_DIFFERENCE (SCOPE, FREELANCER_SCOPE): 0 DRAWING-CONFIRMED; physical wall foot "
                                 f"{yd['totals_lm']['NOT_IN_DRAWING_physical_wall_foot']} NOT_IN_DRAWING (+ "
                                 f"{yd['totals_lm']['NOT_IN_DRAWING_under_unprinted_sills_range_hi']} under sills), "
                                 f"UNRESOLVED 0 .. {yd['totals_lm']['UNRESOLVED_bound'][1]}"})
    rows.append({"group": "ROOM (12 dry rooms + 17 wet)", "his": "282.85", "t574_ours_valued": "197.278592",
                 "t585": "unchanged (not in scope)"})
    rows.append({"group": "PIECES (nr)", "his": "96", "t574_ours_valued": "0",
                 "t585": "unchanged: kept in nr; no sheet prints a piece length (conversion refused, R-T585-1 (d))"})
    return rows


def build():
    p = pins()
    t574 = json.loads((ROOT / T574).read_text())
    cells = _t574_module().his_cells()
    yd = yard(cells, t574)
    st = stairs(t574)
    land = e1_landing()
    return {"schema": "T585_SKIRTING_FOLLOWUPS_V1", "rule": "R-T585-1", "pins": p, "yard": yd, "stairs": st,
            "e1_landing": land, "t574_restated": restate(t574, st, land, yd),
            "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)"}


def dump(obj):
    def enc(o):
        if isinstance(o, Decimal):
            return S(o)
        raise TypeError(type(o))
    return json.dumps(obj, indent=1, ensure_ascii=False, default=enc) + "\n"


def main(argv):
    text = dump(build())
    if "--write" in argv:
        OUT.write_text(text)
        print("written", OUT.relative_to(ROOT))
    elif "--check" in argv:
        if OUT.read_text() != text:
            print("DIFFERS")
            return 1
        print("byte-identical")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
