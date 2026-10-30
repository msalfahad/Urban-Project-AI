"""T-378 Alsenan stair bar roles (printed readings only; drawings named by Drive folder 'Alsenan chalet project' and
title: 'ST7757.pdf' p.4 / p.5 plans and p.16 TYPICAL STEEL LAYOUT-STAIR SECTION, re-read this run at 60 / 200 dpi;
'ST7757 dxf.dxf' handles as cited by the merged T-359 r2 census). Writes ALSENAN_STAIR_ROLE_INPUT.json.

What p.16 draws (both sections and both exploded rows, re-read): every stair bar is ONE shape of its own population.
Main waist bar 8ø16/m: slope + horizontal into the head + end hook (UX-MAINH), slope + horizontal into the landing
bottom at a foot on a landing (UX-MAINF), slope + vertical leg into the G.B at a foot on a ground beam (lower section,
LX-MAIN). Landing bottom 8ø16/m: horizontal + slope up the flight (UX-LAND), crossing the main bar at the knee.
Top bars 6ø14/m (head, landing foot) and 6ø16/m (G.B foot): slope + horizontal / vertical leg, own shapes. Step bar
ø8/15: tread + riser L inside the step. Distribution ø12/20cm and landing top 6ø12/m: dots / straight. No separate bar
is drawn left out of a beam, landing or G.B and overlapped (tied) with a flight bar anywhere on p.16, and no overlap is
dimensioned. Plans p.4 / p.5 print only the 8ø16/m callouts (flights along, strips across wall to wall).

    python3 -I research/agents_t378/t378_alsenan_input.py [--check]
"""

import json
import sys
from pathlib import Path

OUT = Path(__file__).with_name("ALSENAN_STAIR_ROLE_INPUT.json")
P16 = "ST p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)"


def _main(head, foot):
    return {"role": "FLIGHT_MAIN",
            "role_text": "waist bottom main bar 8ø16/m along the flight (the flight's own span steel, plan p.4 / p.5 "
                         "dxf 490 / 491 / 748 / 749 / 53D)",
            "ends": [head, foot]}


HEAD_BEAM = lambda beam: {"end": "upper end", "support": f"floor beam {beam} (T-111: head 0.20 m inside {beam})",
                          "drawn_as": "OWN_BAR_INTO_SUPPORT",
                          "ref": f"{P16} UX-MAINH: slope + horizontal into the head + end hook, one bar, no tie"}
FOOT_LANDING = lambda what: {"end": "lower end", "support": what, "drawn_as": "OWN_BAR_INTO_SUPPORT",
                             "ref": f"{P16} UX-MAINF: slope + horizontal into the landing / slab bottom, one bar; the "
                                    f"landing bottom bar UX-LAND crosses it at the knee, no tie"}
HEAD_LANDING = lambda what: {"end": "upper end", "support": what, "drawn_as": "OWN_BAR_INTO_SUPPORT",
                             "ref": f"{P16} lower section: waist bottom bar runs on into the +2.00 landing bottom, one "
                                    f"bar, no tie"}

DIST = {"role": "FLIGHT_DISTRIBUTION",
        "role_text": "distribution bar ø12/20cm under the main bars, across the flight width, parallel to the supports",
        "ends": [{"end": f"side {s}", "support": "flight side face (no support crossed)", "drawn_as": "OWN_BAR_INSIDE_ELEMENT",
                  "ref": f"{P16} U-DIST / UX-DIST: dot on the main bar (straight bar across the flight)"} for s in "AB"]}
STEP = {"role": "STEP_BAR",
        "role_text": "step bar ø8/15 (tread + riser L) inside each step, legs into the waist (T-166: undimensioned)",
        "ends": [{"end": e, "support": "the flight's own waist (same element)", "drawn_as": "OWN_BAR_INSIDE_ELEMENT",
                  "ref": f"{P16} U-STEP / UX-STEP: tread + riser L with the 1ø12 nosing at its corner"}
                 for e in ("tread-leg end", "riser-leg end")]}


def _strip(layer, label, plan_ref):
    role = "LANDING_BOTTOM" if layer == "bottom" else "LANDING_TOP"
    return {"role": role,
            "role_text": f"landing strip {layer} bar {label} across the stair, wall to wall 2.50 m (T-166 / T-111); "
                         "the landing's own span steel",
            "ends": [{"end": f"{side} end", "support": "landing support at the wall line (T-166: landings sit on "
                                                       "B2 / B3 / walls)",
                      "drawn_as": "OWN_BAR_INTO_SUPPORT",
                      "ref": f"{plan_ref}; {P16} L-LAND / L-LTOP / U-LAND / U-LTOP dot rows (straight bars), no tie"}
                     for side in ("west", "east")]}


ROLES = {
    "ST-01:MS1-L|main bottom bars along the waist": _main(
        HEAD_LANDING("GF strip (winder turn MS1-T + well + landing MS1-LD)"),
        {"end": "lower end", "support": "flight foot at the GF hall +1.00", "drawn_as": "NOT_PRINTED",
         "ref": f"T-166 s.5 'MS1-L foot at the GF hall: the hall foot is not detailed'; {P16} lower section draws a "
                "foot on a G.B as the bar's own vertical leg (LX-MAIN), no tie",
         "missing": "the support under the MS1-L foot at the GF hall +1.00 (ground-beam plan p.3 draws the stair outline "
                    "only) and whether p.16's lower section governs it (G-T359-1); a starter splice there is printed "
                    "nowhere"}),
    "ST-01:MS1-U|main bottom bars along the waist": _main(HEAD_BEAM("B20"), FOOT_LANDING("GF strip landing MS1-LD")),
    "ST-01:MS2-L|main bottom bars along the waist": _main(
        HEAD_LANDING("1F strip landing MS2-LD"), FOOT_LANDING("1F floor at the stair start (GF roof slab, p.4)")),
    "ST-01:MS2-U|main bottom bars along the waist": _main(HEAD_BEAM("B23"), FOOT_LANDING("1F strip landing MS2-LD")),
    "ST-02:RS-S|main bottom bars along the waist": _main(
        {"end": "upper end", "support": "the landing / slab the straight flight meets", "drawn_as": "OWN_BAR_INTO_SUPPORT",
         "ref": f"plan 8ø16/m along the straight flight (dxf 53D) drawn to the flight end; {P16} UX-MAINH / UX-MAINF "
                "shapes, one bar, no tie"},
        {"end": "lower end", "support": "the curved flight RS-C (HELD, Q-50)", "drawn_as": "FLIGHT_TO_FLIGHT",
         "ref": "T-166: 'foot runs on from the HELD curved part'; plan 8ø16/m along the curve (dxf 5BC): the same "
                "stair's flight bars run on (continuous or lapped flight to flight), not a starter"}),
    "ST-02:RS-A|main bottom bars along the waist": _main(
        {"end": "upper end", "support": "corner landing RS-LD / slab", "drawn_as": "OWN_BAR_INTO_SUPPORT",
         "ref": f"plan 8ø16/m along the short flight (PDF p.4, T-359); {P16} UX-MAINH, one bar, no tie"},
        {"end": "lower end", "support": "landing / slab at the flight foot", "drawn_as": "OWN_BAR_INTO_SUPPORT",
         "ref": f"{P16} UX-MAINF, one bar, no tie"}),
    "ST-01:GF-STRIP|landing strip bottom bars across the stair": _strip("bottom", "8ø16/m", "plan p.4 8ø16/m strip callout (dxf 48F)"),
    "ST-01:1F-STRIP|landing strip bottom bars across the stair": _strip("bottom", "8ø16/m", "plan p.5 8ø16/m strip callout (dxf 747)"),
    "ST-01:GF-STRIP|landing strip top bars across the stair": _strip("top", "6ø12/m", "no plan callout (T-166: p.16 typical landing only)"),
    "ST-01:1F-STRIP|landing strip top bars across the stair": _strip("top", "6ø12/m", "no plan callout (T-166: p.16 typical landing only)"),
}
for fl in ("ST-01:MS1-L", "ST-01:MS1-U", "ST-01:MS2-L", "ST-01:MS2-U", "ST-02:RS-S", "ST-02:RS-A"):
    ROLES[f"{fl}|distribution under the main bars"] = DIST
    ROLES[f"{fl}|step bars (tread + riser shape)"] = STEP

DOC = {"schema": "ALSENAN_STAIR_ROLE_INPUT_V1", "project": "Alsenan (development villa; drawings on Drive only)",
       "starter_criterion": "note 9 (ST p.8, Arabic 'اشاير': tie / development length of STARTER bars >= 70 d tension / "
                            ">= 40 d compression, zone not printed) is in scope only where a separate bar is drawn left "
                            "out of the supporting element into the flight and tied with the flight bar",
       "p16_census": "no stair bar on p.16 is drawn as a separate tied starter; the one bar that crosses into a G.B "
                     "(6ø16/m top bar and LX-MAIN at a foot on a G.B) is drawn as the flight bar's own leg and has no "
                     "candidate line (T-359 ST-0x-T-TOPG, F-T359-1)",
       "roles": ROLES}


def main(argv):
    text = json.dumps(DOC, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("ALSENAN_STAIR_ROLE_INPUT.json", "up to date" if ok else "STALE")
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
