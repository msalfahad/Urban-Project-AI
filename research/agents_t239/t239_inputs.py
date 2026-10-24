"""T-239 (V3.0.11): the project inputs of ARCH_TAKEOFF_V3.0.11 (URBAN_V3011_INPUTS_V1) for the development villa.
Research code; it reads the checker-merged T-233 footing input as committed (values only: outline id, sides, area, the
schedule rows of the tags and the blinding detail) and changes none of its quantities. No coordinates, no names, no
drawing content.

MULTI_TAG_OUTLINE (owner Q-31 C; Lead / main chat 2026-10-23 21:15 items 9-10):
  T-233 (MERGED 2ecb5bf0, Verifier 2026-10-23 20:14 UTC: Gate A PASS, 'F10 + F: one open outline 1B1B 3.25 x 1.40
  (4.55 m2) vs rows 3.92 + 0.72 = 4.64 m2: CONFLICT, HELD 2.176 .. 2.275 (Q-31 C); A's F10 line 0.216 .. 1.960 excludes
  both readings (lane I)'). The one drawn outline carries the two schedule tags F10 (2.80 x 1.40 x 0.50) and F (0.90 x
  0.80 x 0.30); blinding detail projection 0.10 each side, thickness 0.10 (the typical footing detail sheet).
  Candidate lines it replaces (identity checked by worker 3 on 'ST7757 dxf.dxf', T-239 run): the route's footing line
  P-C:FTG:SH10:T652:10A5 is the route's FOOTING_LABEL_CONFLICT line of the label 'F' (TEXT 10A5) that lies INSIDE outline
  1B1B together with the label 'F10' (TEXT 168B); the route quantified the conflict once there (the F10 label is its
  secondary). Its blinding is the route's bounded blinding line of the same footing (U-C:...:BLINDING_FOOTING:FTG:SH10:
  T652:10A5, 0.480 .. 0.590); the candidate's released footing blinding 15.179437 is the union under the 25 other
  outlines only (T-233, Checker 20:14: 15.179 = 0.0 %), so the F10 + F blinding is in no other line (no double count).
  The footing rebar line of the same footing (FRP:FTG:SH10:T652:10A5:ALL) is already BLOCKED_RFI (Q-31 C): unchanged.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T233 = ROOT / "research/agents_t233"
T233_INPUT_SHA = "b9a81599509233e4d9ea9b1779d0ca1caf6e32568934e1e08da1ae60cf10e135"
T233_LEDGER_SHA = "ea4f099282dc001d4462a574df9afb30a47214d618a00297c391839ae7acd4c8"
OUTLINE = "1B1B"
FOOT, BLIND = "STR.CONC.FOOTING", "STR.CONC.BLINDING"
FLOOR = "FOUNDATION"
FOOT_LINE = "P-C:FTG:SH10:T652:10A5"          # the route's two-label footing line (label 'F' inside outline 1B1B)
FOOT_CARRIED = 1.96                           # PROVISIONAL 1.960 in V3.0.10 (= V2.9 / V3.0.x route figure)
BLIND_LINE = "U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTING:FTG:SH10:T652:10A5"   # its blinding (route, bounded)
BLIND_CARRIED = [0.48, 0.59]                  # BOUNDED 0.480 .. 0.590 in V3.0.10 (unchanged since the route)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _t233():
    p = T233 / "ALSENAN_FOOTING_INPUT.json"
    if _sha(p) != T233_INPUT_SHA or _sha(T233 / "LEDGER_T233.csv") != T233_LEDGER_SHA:
        raise SystemExit("T-233 merged files changed: re-check the inputs before integrating")
    return json.loads(p.read_text(encoding="utf-8"))


def record():
    d = _t233()
    o = next(x for x in d["outlines"] if x["id"] == OUTLINE)
    assert sorted(o["tags"]) == ["F", "F10"], o["tags"]
    rows = {t: d["schedule"][t] for t in o["tags"]}
    sch = {t: {"L": r["L"], "W": r["W"], "H": r["H"],
               "source": f"ST7757 dxf.dxf FT schedule INSERT {r['insert']} (W / H / DEPHT in cm) = ST7757.pdf p.9 "
                         f"row {t}"} for t, r in rows.items()}
    src = d["source"]
    # the readings as the T-233 ledger states them (recomputed by the module from the values above; must agree)
    f_rows = sum(r["L"] * r["W"] * r["H"] for r in rows.values())               # 1.960 + 0.216 = 2.176
    f_out = o["area"] * max(r["H"] for r in rows.values())                       # 4.55 x 0.50 = 2.275
    p, t = src["projection_m"], src["thickness_m"]
    b_rows = sum((r["L"] + 2 * p) * (r["W"] + 2 * p) for r in rows.values()) * t  # (4.80 + 1.10) x 0.10 = 0.590
    b_out = (o["a"] + 2 * p) * (o["b"] + 2 * p) * t                              # 5.52 x 0.10 = 0.552
    assert abs(o["blind_m2"] - (o["a"] + 2 * p) * (o["b"] + 2 * p)) < 1e-9       # T-233 blind_m2 5.52
    return {
        "outline": OUTLINE, "tags": o["tags"], "floor": FLOOR, "owner_item": "Q-31 C",
        "reasons": ["one drawn footing outline (open where strap SB1 enters) carries the two schedule tags F10 and F: "
                    "the schedule rows (3.92 + 0.72 = 4.64 m2, 3.70 m long side by side) and the drawn outline "
                    "(3.25 x 1.40 = 4.55 m2) disagree; the designer has not said whether it is one combined footing "
                    "or the two rows (owner Q-31 C: HELD, RFI, flagged)"],
        "schedule": sch,
        "drawn": {"a": o["a"], "b": o["b"], "area": o["area"], "rectangular": True,
                  "source": "ST7757 dxf.dxf LWPOLYLINE 1B1B (S-FOOTINGS, open 0.70 where SB1 enters; bounding "
                            "rectangle 3.25 x 1.40) = ST7757.pdf p.2 foundation plan"},
        "blinding": {"projection_m": p, "thickness_m": t, "source": src["projection_source"]},
        "footing": {"item_code": FOOT, "floor": FLOOR, "element_id": FOOT_LINE, "unit": "m3",
                    "carried": FOOT_CARRIED,
                    "why": "the route found the two labels but no outline and carried one schedule type "
                           "(PROVISIONAL 1.960, own range 0.216 .. 1.960 = F alone .. F10 alone): a range that "
                           "excludes both drawing readings",
                    "readings": {"ROWS_SEPARATELY": round(f_rows, 6), "OUTLINE_AT_DEEPEST_DEPTH": round(f_out, 6)},
                    "range": [round(min(f_rows, f_out), 6), round(max(f_rows, f_out), 6)], "state": "HELD",
                    "downstream": [
                        {"line_id": "L-3f2cfc1d95f03b54f256", "element_id": "FRP:FTG:SH10:T652:10A5:ALL",
                         "why": "footing rebar of this outline: BLOCKED_RFI by the route already (TWO_MARKS_ONE_FOOTING, "
                                "Q-31 C); stays held, not changed here"},
                        {"line_id": "L-abd65e1b745315dd17c2", "element_id": "HL:STRAP_CONCRETE:SB1:IN_FOOTING:F10_F",
                         "why": "strap SB1 inside this outline: its V3.0.8 HELD line 0 .. 0.385 m3 follows the same "
                                "Q-31 answer (which footing owns the piece); stays held, not changed here"}]},
        "blinding_line": {"item_code": BLIND, "floor": FLOOR, "element_id": BLIND_LINE, "unit": "m3",
                          "carried": BLIND_CARRIED,
                          "earlier_change": "ADDED by V3.0.1 piece ROUTE_G_SCOPE (T-126, cd34bd0) as BOUNDED 0.480 .. "
                                            "0.590 when it split the footing blinding into the released union under "
                                            "the other 25 outlines and this held piece; replaced here because its "
                                            "low end is F10 alone, not a reading of the outline",
                          "why": "its low 0.480 is F10 alone grown 0.10 ((2.80 + 0.20) x (1.40 + 0.20) x 0.10): not a "
                                 "reading of the drawn outline",
                          "readings": {"ROWS_SEPARATELY": round(b_rows, 6), "OUTLINE_AT_DEEPEST_DEPTH": round(b_out, 6)},
                          "range": [round(min(b_rows, b_out), 6), round(max(b_rows, b_out), 6)], "state": "HELD"},
        "provisional_view": "OUTLINE_AT_DEEPEST_DEPTH",
        "info": {"blinding_inside_plot_line_outline_reading_m3": round((o["blind_m2"] - o["blind_outside_m2"]) * t, 6),
                 "blinding_beyond_plot_line_m2": o["blind_outside_m2"],
                 "plot_line_clip": "designer item D-14 (blinding beyond the plot line), held by its own item; the "
                                   "range above is before that clip, as every footing blinding in the candidate",
                 "rows_side_by_side_m": round(sum(r["L"] for r in rows.values()), 3),
                 "rows_note": "reading ROWS_SEPARATELY is the two schedule rows as printed; side by side they are "
                              "3.70 m long against the 3.25 m outline, so the drawing does not place them either: "
                              "this is why it is a CONFLICT and not a reading to pick"},
    }


def piece():
    rec = record()
    src = {"file": "research/agents_t233/ALSENAN_FOOTING_INPUT.json", "sha256": T233_INPUT_SHA, "task": "T-233",
           "merge_commit": "2ecb5bf0", "checker_run": "Verifier 2026-10-23 20:14 UTC (Gate A PASS, all 26 outlines "
                                                      "re-measured; F10 + F CONFLICT HELD 2.176 .. 2.275, Q-31 C)"}
    led = {"file": "research/agents_t233/LEDGER_T233.csv", "sha256": T233_LEDGER_SHA, "task": "T-233",
           "merge_commit": "2ecb5bf0", "checker_run": src["checker_run"]}
    return {"piece": "MULTI_TAG_OUTLINE", "source": src, "sources": [led], "records": [rec],
            "declared": {"footing": [2.176, 2.275], "blinding": [0.552, 0.59]}}


def inputs(project_id=None):
    import sys
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.10)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3011_INPUTS_V1", "project": project_id, "pieces": [piece()], "guard": g}


if __name__ == "__main__":
    print(json.dumps(piece()["records"][0], indent=1, ensure_ascii=False)[:3000])
