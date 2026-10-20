"""T-056: the development villa's stairs as a STAIR_CONCRETE_V1 census, and the run of the piece on it.

Project facts only (printed dimensions, counts and their sheets), each with its source; nothing here enters engine code.
Every value is a reading already verified and merged (research/agents_t084, hand table by section A-A / B-B and the
plans; research/alsenan_stairs_s8_7c, the frozen structural study by DXF handle, as the second source for the GF -> 1F
count and the turn). Owner answers applied: Q-46 A (section counts), Q-47 A ('T 16' in a stair panel = waist and landing
thickness). Open and therefore HELD: Q-50 (round stair, no section), Q-51 (winder / tapered steps).

Run: .venv/bin/python -I research/agents_t056/alsenan_stair_census.py   (prints the lines and totals; writes nothing)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.source import stair_steps_concrete as SC  # noqa: E402


def v(x, src):
    return {"value": x, "source": src}


T16_GF = {"value": 0.16, "basis": "PANEL_TAG",
          "source": "ST7757.pdf p.4 GF roof slab: 'T 16' + '8 d16/m' inside the stair panel (owner Q-47 A)"}
T16_1F = {"value": 0.16, "basis": "PANEL_TAG",
          "source": "ST7757.pdf p.5 1F roof slab: 'T 16' + '8 d16/m' inside the stair panel (owner Q-47 A)"}
SEC_AA = "p7757_arch_sheet10.pdf section A-A"

MAIN = {"id": "MAIN_STAIR", "unit": "m", "runs": [
    {"id": "GF-1F", "bottom_level": v(1.00, SEC_AA + " +1.00"), "top_level": v(5.50, SEC_AA + " +5.50"),
     "section_risers": v(27, SEC_AA + ": 10 + 5 winders + 12 (frozen study S8.7c B-27-S agrees by DXF handle)"),
     "plan_risers": [v(25, "p7757_arch_sheet03.pdf GF plan 10 + 4 + 11"),
                     v(28, "ST7757 GF roof slab 12 + 4 + 12")],
     "parts": [
         {"id": "MS1-L", "kind": "FLIGHT", "risers": 10, "goings": 10, "tread": v(0.30, "GF plan riser-line pitch"),
          "width": v(1.20, "GF plan '120'"), "thickness": T16_GF},
         {"id": "MS1-T", "kind": "WINDER", "risers": 5,
          "plan_area": v(1.44, "NE quarter 1.20 x 1.20 (S8.7c by handle)")},
         {"id": "MS1-LD", "kind": "LANDING", "length": v(1.25, "GF plan '125'"), "width": v(1.20, "GF plan '120'"),
          "thickness": T16_GF},
         {"id": "MS1-U", "kind": "FLIGHT", "risers": 12, "goings": 11, "tread": v(0.30, "GF plan riser-line pitch"),
          "width": v(1.20, "GF plan '120'"), "thickness": T16_GF},
         {"id": "1F-FLOOR", "kind": "FLOOR_LANDING"}]},
    {"id": "1F-2F", "bottom_level": v(5.50, SEC_AA + " +5.50"), "top_level": v(9.70, SEC_AA + " +9.70"),
     "section_risers": v(25, SEC_AA + ": 12 + closing riser at a flat quarter + 12"),
     "plan_risers": [v(27, "p7757_arch_sheet04.pdf 1F plan 12 + 4 + 11"),
                     v(24, "ST7757 1F roof slab 12 + 1 + 11")],
     "parts": [
         {"id": "MS2-L", "kind": "FLIGHT", "risers": 12, "goings": 11, "tread": v(0.30, "1F plan run '330' / 11"),
          "width": v(1.20, "1F plan '120'"), "thickness": T16_1F},
         {"id": "MS2-TR", "kind": "TURN_RISER", "risers": 1},
         {"id": "MS2-LD", "kind": "LANDING", "length": v(2.50, "1F plan '250'"), "width": v(1.25, "1F plan '125'"),
          "thickness": T16_1F},
         {"id": "MS2-U", "kind": "FLIGHT", "risers": 12, "goings": 11, "tread": v(0.30, "1F plan run '330' / 11"),
          "width": v(1.20, "1F plan '120'"), "thickness": T16_1F},
         {"id": "2F-FLOOR", "kind": "FLOOR_LANDING"}]}],
    "not_present": [{"id": "2F-ROOF", "evidence": "section A-A draws no flight above +9.70; the 2F roof slab over the "
                                                  "hall is a closed T18 slab"}],
    "beams": [{"id": "B3-WITH-STAIR-GF", "width": 0.20, "depth": 0.40,
               "source": "ST7757 p.4 'B3 (With Stair)', p.10 B3 row 20 x 40, p.16 cranked stair beam detail"},
              {"id": "B3-WITH-STAIR-1F", "width": 0.20, "depth": 0.40,
               "source": "ST7757 p.5 'B3 (With Stair)', p.10 B3 row 20 x 40"}]}

ENTRANCE = {"id": "ENTRANCE_FLIGHT", "unit": "m", "runs": [
    {"id": "COURT-GF", "bottom_level": v(0.15, "section B-B +0.15"), "top_level": v(1.00, "section B-B +1.00"),
     "section_risers": v(5, "Pages_11-12 sheet 11 section B-B"), "plan_risers": [v(5, "GF plan riser lines")],
     "parts": [{"id": "E1", "kind": "FLIGHT", "risers": 5, "goings": 4, "tread": v(0.30, "GF plan pitch / B-B going"),
                "width": v(2.80, "GF plan '280'")},
               {"id": "GF-FLOOR", "kind": "FLOOR_LANDING"}]}]}

LOBBY = {"id": "LOBBY_FLIGHT", "unit": "m", "runs": [
    {"id": "LOBBY-GF", "bottom_level": v(0.30, SEC_AA + " +0.30"), "top_level": v(1.00, SEC_AA + " +1.00"),
     "section_risers": v(4, SEC_AA), "plan_risers": [v(4, "GF plan solid riser lines under the dashed flight")],
     "parts": [{"id": "D1", "kind": "FLIGHT", "risers": 4, "goings": 3, "tread": v(0.30, "GF plan pitch / A-A going"),
                "width": v(1.20, "GF plan '120'")},
               {"id": "GF-HALL", "kind": "FLOOR_LANDING"}]}]}

ROUND = {"id": "ROUND_STAIR", "unit": "m", "runs": [
    {"id": "GF-1F", "bottom_level": v(1.00, "GF +1.00"), "top_level": v(5.50, "1F +5.50"),
     "section_risers": None,                       # no section cuts it (owner Q-50 open)
     "plan_risers": [v(28, "GF / 1F plans 12 curved + 11 straight + 5")],
     "parts": [{"id": "RS-C", "kind": "CURVED", "risers": 12},
               {"id": "RS-S", "kind": "FLIGHT", "risers": 11, "tread": v(0.30, "plan pitch"),
                "width": v(1.20, "GF plan '120'"),
                "thickness": {"value": 0.16, "basis": "PANEL_TAG",
                              "source": "ST7757 p.4: 'T 16' in the round-stair panel (owner Q-47 A)"}},
               {"id": "RS-LD", "kind": "LANDING", "width": v(1.25, "1F plan '125'"),
                "thickness": {"value": 0.16, "basis": "PANEL_TAG", "source": "ST7757 p.4 'T 16'"}},
               {"id": "RS-A", "kind": "FLIGHT", "risers": 5, "tread": v(0.30, "plan pitch"),
                "width": v(1.25, "1F plan '125'")},
               {"id": "1F-ARRIVAL", "kind": "FLOOR_LANDING"}]}],
    "beams": [{"id": "B3-WITH-STAIR-RS", "width": 0.20, "depth": 0.40,
               "source": "ST7757 p.4 'B3 (With Stair)' along the straight flight"}]}

FREELANCER = {"MAIN_STAIR": 8.131, "ENTRANCE_FLIGHT": 1.411, "ROUND_STAIR": 5.510, "LOBBY_FLIGHT": None}

if __name__ == "__main__":
    res = SC.measure_all([MAIN, ENTRANCE, LOBBY, ROUND])
    for st in res["stairs"]:
        print(f"== {st['stair']}")
        for ln in st["lines"]:
            print(f"  {ln['part'] or '-':18s} {ln['element']:22s} {ln['status']:30s} "
                  f"{'' if ln['quantity_m3'] is None else format(ln['quantity_m3'], '.4f'):>8s}  {ln['reason'] or ''}")
        for c in st["checks"]:
            print("  check", json.dumps({k: c[k] for k in c if k not in ("note",)}, ensure_ascii=False))
        m, f = st["totals"]["measured_m3"], FREELANCER[st["stair"]]
        if m is None:
            print(f"  nothing measured: every line HELD (not 0); freelancer {f} m3")
            continue
        diff = "" if f is None else f"  vs freelancer {f:.3f}: {m - f:+.3f} m3 ({(m - f) / f * 100:+.1f} %)"
        print(f"  measured {m:.4f} m3 by element {st['totals']['measured_by_element_m3']}{diff}")
    print("PROJECT measured", res["totals"]["measured_m3"], "m3; held lines:",
          sum(len(h) for h in res["totals"]["held"].values()))
