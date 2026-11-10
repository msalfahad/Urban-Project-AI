"""T-684 development villa: the MS2 1F north-west corner square of the dog-leg stair ST-01, and every line that
depends on it, on candidate V3.0.66 (research only, unwired; nothing is released or changed in the candidate).

Readings (relative geometry only: metres from each storey's turn-square inner corner; no absolute coordinate, text,
name or drawing content), re-derived this run by research/agents_t684/t684_probe.py from the Drive folder 'Alsenan
chalet project' files 'P7757_DXF_COMPRESSED.zip' (P7757.dxf), 'ST7757 dxf.dxf', and read by eye on
'p7757_arch_sheet10.pdf' (section A-A, rendered at 600 dpi) and 'p7757_arch_sheet04.pdf' (1F plan).

Usage: bash scripts/agent_env.sh run --tree task-T-684 research/agents_t684/t684_alsenan.py [--write]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t684_rules as R  # noqa: E402

LINE_INDEX = ROOT / "research" / "agents_t677" / "out" / "LINE_INDEX_V3_0_66.json"
T680 = ROOT / "research" / "agents_t680" / "out" / "T680_SHAFT_ROUND2.json"   # MERGED 707c624e, research (unwired)
OUT = HERE / "out"

# the three radiating lines from the inner corner, far ends relative to the corner (x west negative, y north positive)
# layer '5' (CONTINUOUS = visible) and their 0.05 companions on layer '2' (HIDDEN), as the probe prints them
GF_TURN = [  # GF plan: the MS1-T winders, ABOVE the GF cut -> drawn on the hidden layer '2' (both sets)
    R.Seg(0, 0, -0.511, 1.150, "HIDDEN"), R.Seg(0, 0, -1.150, 1.150, "HIDDEN"), R.Seg(0, 0, -1.150, 0.512, "HIDDEN"),
    R.Seg(0.046, 0.021, -0.466, 1.171, "HIDDEN"), R.Seg(0.035, 0.036, -1.115, 1.186, "HIDDEN"),
    R.Seg(0.020, 0.046, -1.130, 0.558, "HIDDEN"),
]
F1_LINES = [  # 1F plan, same square of the same shaft: the same lines, now on the VISIBLE layer '5' (+ '2' twins)
    R.Seg(0, 0, -0.511, 1.150, "VISIBLE"), R.Seg(0, 0, -1.150, 1.150, "VISIBLE"), R.Seg(0, 0, -1.150, 0.512, "VISIBLE"),
    R.Seg(0.046, 0.021, -0.465, 1.171, "HIDDEN"), R.Seg(0.036, 0.036, -1.114, 1.186, "HIDDEN"),
    R.Seg(0.021, 0.046, -1.129, 0.558, "HIDDEN"),
    # orthogonal lines of the square (not radiating): closing-riser nosing x +0.10 (layer 5) / riser face +0.15 (2)
    R.Seg(0.10, 0, 0.10, 1.15, "VISIBLE"), R.Seg(0.15, 0, 0.15, 1.15, "HIDDEN"),
]

READINGS = {
    "storeys": {
        "GF": dict(height_m=4.50, flights={"MS1-L": 10, "MS1-U": 12}, riser_m=4.50 / 27, section_turn_risers=5,
                   src="A-A: 4 dashed + 1 solid riser in the north 1.20 m zone between +2.667 and +3.50 (0.833 m); "
                       "T-111 / T-184 counts; levels +1.00 / +5.50 printed"),
        "1F": dict(height_m=4.20, flights={"MS2-L": 12, "MS2-U": 12}, riser_m=0.168, section_turn_risers=1,
                   src="A-A: printed 420; cut flight MS2-U 12 risers, MS2-L seen beyond 12, risers 0.168 (scaled "
                       "~40 px of 237 px/m at 600 dpi); the north 1.20 m zone draws NO riser line: only the west "
                       "quarter's slab edge seen one riser below the cut NE landing (the closing riser)"),
    },
    "open_below_1F_NW": "the 1F plan draws no floor, landing or slab in the NW square between the 1F cut and the GF "
                        "turn: the 1F arrival landing (1.95 x 2.50) is at the SOUTH end; the NW square on 1F is open "
                        "down to the GF winders (T-173 shaft model: the NW floor is the GF one, +0.30 / +1.00)",
    "corroboration": [
        "2F plan (looks down on the MS2 north strip): NO radiating line in the NW square; the 1.15 m closing-riser "
        "line at +0.10 east of the corner (layer 5) with its 0.05 twin (layer 2) only",
        "ST p.5 (1F roof slab, carries MS2): NO radiating line in the NW square (probe: 3 non-orthogonal pieces in "
        "the north zone, none in NW: a 45 deg pair in the NE half and two column outlines)",
        "ST p.4 (GF roof slab, carries MS1, the sheet that also draws the round stair): the 3 radiating lines "
        "(156 / 135 / 114 deg, 1.259 / 1.626 / 1.259 m) at the same corner",
        "layer logic: the GF plan draws its own winders on the HIDDEN layer (above the GF cut); the 1F plan draws "
        "the same lines on the VISIBLE layer (below the 1F cut): the plan convention for an object seen below",
        "T-425 / T-429 (MERGED) already bound the engine's 1F 'flight 5' (4-tread RADIAL, width 1.247) to MS1-T "
        "with role SEEN_THROUGH; this run re-derives it independently and closes F-V680-1 on it",
    ],
}

# every dependent line on V3.0.66 (line ids from the merged censuses; value read from the line index, not typed)
DEPENDENT = [
    ("STR.CONC.STAIR", "L-67e4b0485135f84acc46", "MS2-L flight (steps + waist)", "T-184"),
    ("STR.CONC.STAIR", "L-2416e65f053a14199cfc", "MS2-LD half landing incl. the NW square (west part +7.516)", "T-184"),
    ("STR.CONC.STAIR", "L-659243ed9fc2831c3ae8", "MS2-TR closing riser +7.516 -> +7.684", "T-184"),
    ("STR.CONC.STAIR", "L-bb0e57b1948175a3d5b8", "MS2-U flight", "T-184"),
    ("STR.FORMWORK.STAIR", None, "MS2-LD soffit / sides (FW:L-2416e65f...)", "formwork"),
    ("FIN.MARBLE.TREAD", None, "1F flight 2 = MS2-L treads", "T-412 / T-425"),
    ("FIN.STAIR.STEP_LM", None, "1F flight 2 = MS2-L step lm", "T-412 / T-425"),
    ("FIN.MARBLE.TREAD", "L-b4660de0ddd98ad0ffc2", "1F flight 5 = MS1-T winders SEEN_THROUGH (GF element)", "T-429"),
    ("FIN.STAIR.STEP_LM", "L-e085c168dee5fb19a7fb", "1F flight 5 step lm (MS1-T seen through)", "T-429"),
    ("FIN.MARBLE.RISER", "L-820baecf7f726b4d8f1e", "1F flight 5 risers (MS1-T seen through)", "T-429"),
    ("FIN.SKIRTING", "L-b442a00bf07405eaaa93", "MS2-LD landing skirting", "T-508 / T-681"),
    ("FIN.SKIRTING", "L-760bfa8dd00061361695", "MS2-LD.W25 (N 1.400 .. 2.400)", "T-681"),
    ("FIN.SKIRTING", "L-33f2018c987f782d1c91", "MS2-LD.W13 (W 1.050 .. 1.200)", "T-681"),
    ("FIN.STAIR.SKIRTING.SLOPED", "L-76de75ce9a315998be99", "MS2-TR.N (closing riser on the N wall)", "T-508"),
    ("FIN.STAIR.SKIRTING.ZIGZAG", "L-5021b820dba41f631dde", "MS2-TR.N", "T-508"),
    ("FIN.RAILING", "L-1c899e8cc696d9c32490", "RL-07 at MS2-LD", "T-421"),
]

UNCHANGED_WHY = {
    "STR.CONC.STAIR": "flat landing confirmed: the T-184 model (landing plate T 16, closing riser) stands",
    "STR.FORMWORK.STAIR": "flat landing soffit confirmed",
    "FIN.MARBLE.TREAD": "tread counts by flight unchanged (MS2-L 11 + landing; no winder tread on 1F -> 2F)",
    "FIN.STAIR.STEP_LM": "as treads",
    "FIN.MARBLE.RISER": "MS1-T risers stay HELD on the GF element (S-9 / Q-51 / C-ST-3), never counted on MS2",
    "FIN.SKIRTING": "landing skirting runs at a flat +7.516 / +7.684 (no stepped profile in the NW square)",
    "FIN.STAIR.SKIRTING.SLOPED": "closing-riser profile on the N wall at the drawn riser line; height not printed",
    "FIN.STAIR.SKIRTING.ZIGZAG": "as sloped",
    "FIN.RAILING": "unchanged (railing held on its own causes)",
}


def storey(name, segs, lower=None, open_below=None):
    s = READINGS["storeys"][name]
    return R.StoreyTurn(storey=name, height_m=s["height_m"], flight_risers=list(s["flights"].values()),
                        riser_m=s["riser_m"], segs=segs, section_turn_risers=s["section_turn_risers"],
                        lower_turn_segs=lower, open_below=open_below)


def build():
    gf = R.classify(storey("GF", GF_TURN))
    f1 = R.classify(storey("1F", F1_LINES, lower=GF_TURN, open_below=True))
    idx = json.loads(LINE_INDEX.read_text())["lines"]
    by_id = {l["line_id"]: l for l in idx}
    rows = []
    for code, lid, what, src in DEPENDENT:
        if lid is None:
            if code == "STR.FORMWORK.STAIR":
                hits = [l for l in idx if l["item_code"] == code and "L-2416e65f053a14199cfc" in l["element_id"]]
            else:
                hits = [l for l in idx if l["item_code"] == code and l["element_id"] == "1F-R78C367:flight 2"]
        else:
            hits = [by_id[lid]] if lid in by_id else []
        if not hits:
            rows.append(dict(item_code=code, line_id=lid, what=what, before=None, after=None, change="LINE ABSENT",
                             src=src))
            continue
        for l in hits:
            v = dict(cls=l["class"], net=l["measured_net"], low=l["held_low"], high=l["held_high"], unit=l["unit"])
            rows.append(dict(item_code=code, line_id=l["line_id"], element_id=l["element_id"], what=what, before=v,
                             after=v, change="NONE", why=UNCHANGED_WHY[code], src=src))
    # the T-680 shaft bands (research bounds, not yet wired): the 1F band holds the N face contact u 0 .. 1.25 that
    # F-V680-1 said would become stepped under winders; it stays flat (+7.516), so both 1F lines keep their bounds
    for l in json.loads(T680.read_text())["lines"]:
        if l["band"] == "1F":
            v = dict(cls=l["class"], net=None, low=l["held_low"], high=l["held_high"], unit="m2")
            rows.append(dict(item_code="T-680 " + l["finish"], line_id=l["line_id"], element_id=l["element_id"],
                             what="ST-01 shaft 1F band (T-680 research bound, unwired)", before=v, after=v,
                             change="NONE", why="the N face contact over the NW square stays FLAT at +7.516 (no "
                             "stepped winder profile): the 0.1 .. 0.2 m2 per finish raised by F-V680-1 does not arise",
                             src="T-680"))
    proposals = [
        dict(item="B7-05 nosing MS2-TR", before="HELD blank 'position not drawn' (T-412 census)",
             after="1.150 lm DRAWING-CONFIRMED (proposed for the B7-05 package, T-424): the closing-riser nosing is "
                   "drawn on the 1F AND 2F plans, x +0.10 east of the NW inner corner over the full 1.15 m square "
                   "(layer 5), its riser face 0.05 further east (layer 2; uphill east = NE quarter +7.684), the "
                   "structural split at the same line on ST p.5 (T-493 5E2)", unit="lm", delta=1.150),
        dict(item="STR.CONC.STAIR MS2-TR", before="HELD blank", after="HELD blank (unchanged): the riser line is drawn "
             "but the two landing levels +7.516 / +7.684 are scaled, not printed, and the soffit under the step is "
             "not drawn", unit="m3", delta=None),
    ]
    released_delta = sum(0 for r in rows if r["change"] != "NONE")
    return dict(
        schema="T684_MS2_TURN_V1", candidate="ARCH_TAKEOFF_V3.0.66 (line index of T-677)",
        element=dict(
            id="ST-01 MS2 1F north-west corner square (1.15 x 1.15 clear, 1.25 x 1.20 to the closing riser)",
            definition="FLAT west part of the split-level half landing MS2-LD at +7.516 (scaled), reached by the "
                       "12th riser of MS2-L; one closing riser MS2-TR on the drawn line x +0.10 east of the corner up "
                       "to the east part +7.684; NOT winders",
            gf_turn=gf, f1_turn=f1,
            radiating_lines_on_1F="SEEN_BELOW: the GF MS1-T winders seen through the open shaft (counted once, on GF)",
            cross_trade_owner="structure (lane S): element definition and STR.CONC.STAIR MS2-LD / MS2-TR; finishes "
                              "take it as a STAIR_LANDING (B7-04 marble, T-493 2.9325 m2) and never re-decide it",
        ),
        readings=READINGS, lines=rows, proposals=proposals,
        released_change_m3=released_delta,
        verdict=dict(
            F_V680_1="CLOSED, no quantity change: the T-184 / T-173 / T-680 flat-landing model is ENGINE_RIGHT on "
                     "three independent drawn facts (riser budget, section A-A, the 2F plan and ST p.5)",
            freelancer="no freelancer line keys the NW square separately (his '2 landings' 6.20 m2 row, T-493: "
                       "UNRESOLVED, no breakdown); not used as evidence",
        ),
    )


def main():
    res = build()
    if "--write" in sys.argv:
        OUT.mkdir(exist_ok=True)
        (OUT / "T684_MS2_TURN.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(dict(gf=res["element"]["gf_turn"], f1=res["element"]["f1_turn"]), indent=1))
    for r in res["lines"]:
        b = r["before"]
        print(f"{r['item_code']:26s} {r['line_id']}  {r.get('element_id', '')[:44]:44s} "
              f"{b['cls'] if b else '-':9s} net {b['net'] if b else '-'} [{b['low'] if b else ''} .. "
              f"{b['high'] if b else ''}] {b['unit'] if b else ''} -> {r['change']}")
    for p in res["proposals"]:
        print("PROPOSAL", p["item"], ":", p["before"], "->", p["after"][:90])


if __name__ == "__main__":
    main()
