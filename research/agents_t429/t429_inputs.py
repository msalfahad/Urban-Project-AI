"""T-429: the URBAN_V3039_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.39 (engine.source.arch_v3039), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every line id, figure, role and action is
READ from those files; typed here are only the column wiring, the flight levels (each cited below) and the dispositions
the Checker verdicts name for the riser lines and the winder turn.

  research/agents_t425/LINE_TABLE_T425.csv, FLIGHT_TABLE_T425.csv, BINDING_T425.json   T-425 (MERGED 6f159091, Verifier
      2026-11-01 09:56 UTC Gate A PASS on 552aed5d): per candidate tread / step line the drawn flight, role, action
      (KEEP / CORRECT / DOUBLE_COUNT / FOLDED / HELD), before / after, beside figure and cause; per flight the drawn
      tread count; the riser lines of every reading (BINDING other_stair_lines). Verdict: 2F F1 DOUBLE_COUNT VERIFIED and
      'riser line L-7adf1ccd0c407b61221a takes the same disposition'; MS1-L 3.105 / 10.350 and MS2-L 3.795 / 12.650
      VERIFIED; MS1-T and RS-C HELD by name.
  research/agents_t434/ALSENAN_TURN_T434.json   T-434 (MERGED a6b325b3, Verifier 2026-11-01T14:00Z Gate A PASS on
      78d45c25): the ST-01 MS1-T turn governed by section A-A, 5 winders; WINDER_SUBDIVISION_NOT_DRAWN (S-9, A8); tread
      region 1.495 m2 and drawn winder fronts 4.14365 lm beside, never valued; landing nosing 1.150 lm DRAWING-CONFIRMED.

Flight levels (F-C-T425-1 level test), all from merged, Checker-verified readings: T-184 (R-STAIR-CONT-1; levels
+0.30 / +1.00 / +3.50 / +5.50 / +9.70), T-425 report s.2 (MS1-L +1.00 -> +2.667, MS2-L +5.50 -> +7.516, MS1-U +3.50 ->
+5.50, MS2-U +7.684 -> +9.70, D1 +0.30 -> +1.00, RS-S +2.929 -> +4.696, RS-A +4.696 -> +5.50), T-434 (MS1-T +2.667 ->
+3.50), T-415 / T-184 (RS-C +1.00 -> +2.929).

    python3 -I research/agents_t429/t429_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LINE_T = ROOT / "research/agents_t425/LINE_TABLE_T425.csv"
FLIGHT_T = ROOT / "research/agents_t425/FLIGHT_TABLE_T425.csv"
BIND = ROOT / "research/agents_t425/BINDING_T425.json"
TURN = ROOT / "research/agents_t434/ALSENAN_TURN_T434.json"
PINS = {LINE_T: "78971213df9750712686d98565796ed4f4b4630e3276a5fde2dd8dd2694ec44c",
        FLIGHT_T: "e24334102a09a343fef0af4b96408fb1a311d5f7dd5e8c84b574665806ce7639",
        BIND: "11e2f275da1448c473642d03bb33396cf82213fc342169681a12694cac08b88c",
        TURN: "d2f987402f51102982b4c53b88aded306b13ab1208bce0a6432649f615fb454f"}
SOURCES = {
    "T-425": {"task": "T-425", "file": "research/agents_t425/LINE_TABLE_T425.csv; research/agents_t425/"
                                       "FLIGHT_TABLE_T425.csv; research/agents_t425/BINDING_T425.json",
              "sha256": f"{PINS[LINE_T]}; {PINS[FLIGHT_T]}; {PINS[BIND]}",
              "merge_commit": "6f15909181d9628303e982d3e8af953703e91671",
              "checker_run": "Verifier 2026-11-01 09:56 UTC session_01E6cPndSzmUJYfDXUS3tWDx (Gate A PASS on 552aed5d; "
                             "own 1F -> 2F registration dx -44.852655 by shaft wall A90 = 1359; DOUBLE COUNT "
                             "CONFIRMED; finding F-C-T425-1 level test)"},
    "T-434": {"task": "T-434", "file": "research/agents_t434/ALSENAN_TURN_T434.json",
              "sha256": PINS[TURN], "merge_commit": "a6b325b3a8f4743a6fe0873d28163aeebf6d686f",
              "checker_run": "Verifier 2026-11-01T14:00Z session_01E6cPncyHeHtzGhoGMh5nuk (Gate A PASS on 78d45c25; "
                             "section A-A governs 5 winders; subdivision HELD)"},
}
LEVELS = {"D1": (0.30, 1.00), "MS1-L": (1.00, 2.667), "MS1-T": (2.667, 3.50), "MS1-U": (3.50, 5.50),
          "MS2-L": (5.50, 7.516), "MS2-U": (7.684, 9.70), "RS-C": (1.00, 2.929), "RS-S": (2.929, 4.696),
          "RS-A": (4.696, 5.50)}
GOING = 0.300               # T-425 s.3: straight goings 0.300 front to front by handle (Checker re-measured MS1-L / MS2-L)
PLAN_OF = {"SITE-3759f2457b22cb4a": "GF", "SITE-735e111dcf9b22c8": "GF", "SITE-a95bf979baf4cfae": "1F",
           "SITE-d7254c68fd33723d": "2F"}     # engine site ids of the storey plans (BINDING readings' basis)
VERIFIED = {"L-151d92470a81dd1c450b", "L-d4d764ae7bb07b474b6f", "L-65806b4d02d476603bc5", "L-23651ecfef77992ec8d4"}
FAMILY = {"B7-02": "B7-02", "B7-06": "B7-06"}
RISER_SUPERSEDE = ("L-7adf1ccd0c407b61221a", "L-0f060e9951c28c4cf074")   # (2F F1 riser, carrier 1F F2 riser)
RISER_HOLD = "L-820baecf7f726b4d8f1e"                                      # 1F F5 riser (MS1-T)


def _rel(p):
    return str(p.relative_to(ROOT))


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (an edited ledger stops)")
    return b.decode("utf-8")


def _f(x):
    return None if x in (None, "") else float(x)


def _plan(reading):
    return PLAN_OF[reading.split(":")[0]]


def build(project_id=None):
    rows = list(csv.DictReader(io.StringIO(_read(LINE_T))))
    frows = {r["flight"]: r for r in csv.DictReader(io.StringIO(_read(FLIGHT_T)))}
    bind = json.loads(_read(BIND))
    turn = json.loads(_read(TURN))
    tt = turn["result"]["turn"]
    if turn["result"]["governing"]["governing"] != "SECTION_A_A" or tt["winder_tread_pieces"] != 5:
        raise SystemExit("T-434: the governing turn count is not the merged section A-A 5")
    held = {
        "MS1-T": {"cause": tt["cause"], "count": tt["winder_tread_pieces"],
                  "source": "OWNER_RULE_STAIRS_2026-10-24 s.4 S-9, A8; Q-46 A (section A-A governs); T-434 a6b325b3; "
                            "designer list C-ST-3"},
        "RS-C": {"cause": "CURVED_PART_HELD: the curved flight of the round stair is reconstructed from the plans "
                          "(owner Q-50 A conditional: curved part HELD)", "count": int(frows["RS-C"]["drawn_treads"]),
                 "source": "Q-50 A cond; RFI-S27; T-425 6f159091"},
    }
    flights = []
    for name, fr in frows.items():
        if name not in LEVELS:            # E1 is a separate line with no flight reading (T-425 s.3.2: AGREE, no change)
            continue
        n = int(fr["drawn_treads"])
        if name == "MS1-T":
            n = tt["winder_tread_pieces"]
        f = {"flight": name, "stair": fr["stair"], "levels": list(LEVELS[name]), "drawn_treads": n,
             "width": float(turn["cad"]["lane_m"]), "held": held.get(name),
             "going": None if name in held else GOING, "source_tasks": ["T-425"] + (["T-434"] if name == "MS1-T" else [])}
        flights.append(f)
    readings = []
    for r in rows:
        act = {"KEEP": "KEEP", "CORRECT": "CORRECT", "DOUBLE_COUNT": "SUPERSEDE", "FOLDED": "SUPERSEDE",
               "HELD": "HOLD"}[r["action"]]
        carrier = None
        if act == "SUPERSEDE":
            same = [x for x in rows if x["flight"] == r["flight"] and x["code"] == r["code"] and x["line_id"] !=
                    r["line_id"] and x["action"] in ("KEEP", "CORRECT") and _f(x["after"]) is not None]
            if len(same) != 1:
                raise SystemExit(f"{r['line_id']}: {len(same)} valued carriers for {r['flight']} {r['code']}")
            carrier = same[0]["line_id"]
        beside = []
        if act == "HOLD":
            beside.append({"value": _f(r["beside"]), "unit": "m2" if r["code"] == "B7-02" else "lm",
                           "basis": "the candidate's own figure for this reading (T-425 LINE_TABLE beside)"})
            if r["flight"] == "MS1-T" and r["code"] == "B7-02" and abs(tt["tread_marble"]["beside_m2"] - beside[0][
                    "value"]) > 1e-9:
                raise SystemExit("T-434 region 1.495 m2 differs from the T-425 beside figure")
            if r["flight"] == "MS1-T" and r["code"] == "B7-06":
                beside.append({"value": tt["winder_fronts"]["beside_lm"], "unit": "lm",
                               "basis": f"drawn winder fronts ({tt['winder_fronts']['drawn_count']} radials, T-434; a "
                                        f"B7-05 nosing basis, not a step count); governing pieces "
                                        f"{tt['winder_tread_pieces']}: the candidate reads 4 (ENGINE_WRONG -1 piece)"})
        hb = None
        if r["action"] == "CORRECT" and _f(r["beside"]):
            hb = {"value": _f(r["beside"]), "why": "TREAD_GOING_NOT_DRAWN: " + r["cause"][:240]}
        ev = ("VERIFIED" if r["line_id"] in VERIFIED else "HELD" if act == "HOLD" else
              "NOT_APPLICABLE" if act == "SUPERSEDE" else r["status"])
        readings.append({"line_id": r["line_id"], "family": FAMILY[r["code"]], "reading": r["engine_flight"],
                         "flight": r["flight"], "role": r["role"], "plan": _plan(r["engine_flight"]), "action": act,
                         "before": _f(r["before"]), "after": _f(r["after"]),
                         "supersede": ({"kind": r["action"], "carrier_line": carrier} if carrier else None),
                         "held_beside": hb, "beside": beside, "cause": r["cause"][:400],
                         "evidence_status": ev, "source_tasks": ["T-425"] + (["T-434"] if r["flight"] == "MS1-T"
                                                                              else [])})
    # the riser lines the Checker verdicts name (B7-03: no quantity today, BLOCKED_RFI; same disposition as the treads)
    risers = {x["line_id"]: x for x in bind["other_stair_lines"]["FIN.MARBLE.RISER"]}
    sup, car = RISER_SUPERSEDE
    for lid, flight, role, act in ((car, "MS2-L", "OWN", "KEEP"), (sup, "MS2-L", "SEEN_THROUGH", "SUPERSEDE"),
                                   (RISER_HOLD, "MS1-T", "SEEN_THROUGH", "HOLD")):
        x = risers[lid]
        if x["state"] != "BLOCKED_RFI" or x["net"] is not None:
            raise SystemExit(f"{lid}: the merged binding lists a riser line with a figure")
        readings.append({"line_id": lid, "family": "B7-03", "reading": x["flight_id"], "flight": flight, "role": role,
                         "plan": _plan(x["flight_id"]), "action": act, "before": None, "after": None,
                         "supersede": ({"kind": "DOUBLE_COUNT", "carrier_line": car} if act == "SUPERSEDE" else None),
                         "held_beside": None, "beside": [],
                         "cause": ("Checker T-425: riser line takes the same disposition as the 2F F1 tread line"
                                   if act == "SUPERSEDE" else "T-425 s.3.1: the riser line of the MS1-T reading takes "
                                   "the tread line's disposition (HELD); governing risers 5 (T-434)"
                                   if act == "HOLD" else "the 1F F2 riser line of MS2-L (carrier; BLOCKED_RFI kept)"),
                         "evidence_status": {"KEEP": "DRAWING-CONFIRMED", "SUPERSEDE": "NOT_APPLICABLE",
                                             "HOLD": "HELD"}[act],
                         "source_tasks": ["T-425"] + (["T-434"] if flight == "MS1-T" else [])})
    return {"schema": "URBAN_V3039_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "flights": flights, "readings": readings}


def main(argv):
    doc = build(argv[0] if argv else None)
    print(json.dumps({k: v for k, v in doc.items() if k not in ("sources",)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
