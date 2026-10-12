"""M9 S1 synthetic examples - rebuilt from the engine, byte for byte (tests/m9_foundation/test_m9_s1_package.py).

    python3 -I research/urban_m9_s1/build_examples.py            write the example files next to this script

01_TILE_COMPARISON_3x2_BATHROOM.csv / .md   the owner's 3.00 x 2.00 m bathroom, 120x60 / 60x60 / 160x80 cm
02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.csv / .md   the same bathroom (door 0.80 m in a 0.20 m wall) on the default roll, and
                                            the M9A fixture WP-1 (2.30 x 3.20 m, door 0.90 m)
03_SYNTHETIC_ROOM_BOQ.md                    the synthetic room schedule: lines, totals, unresolved items

Every input is a synthetic test parameter stated in the file; nothing here is a project, a drawing or product data.
"""

from __future__ import annotations

import csv
import io
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import material_spec as MS      # noqa: E402
from engine.source import membrane_layout as ML     # noqa: E402
from engine.source import room_boq as RB            # noqa: E402
from engine.source import rule_store as RS          # noqa: E402
from engine.source import tile_layout as TL         # noqa: E402

BATH = {"room_id": "SYN-BATH-3x2", "length_m": 3.0, "width_m": 2.0}
TILE_C = {"joint_m": 0.002, "min_cut_m": 0.10, "min_reusable_m": 0.10, "kerf_m": 0.0, "rotation_allowed": False,
          "wet_room": True}
ILLUSTRATIVE_BOX = {"TILE-120x60": 2, "TILE-60x60": 4, "TILE-160x80": 2}       # TEST PARAMETERS, not product data
SKILL_FLAT = {"TILE-60x60": 10, "TILE-120x60": 12, "TILE-160x80": 15}          # unconfirmed skill defaults (reference)
DOOR_3x2 = [{"door_id": "D-01", "width_m": 0.80, "depth_m": 0.20}]
WP1 = {"room_id": "WP-1", "length_m": 2.30, "width_m": 3.20}
DOOR_WP1 = [{"door_id": "D1", "width_m": 0.90, "depth_m": 0.20}]


def f3(x):
    return "" if x is None else f"{x:.3f}"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def csv_text(head, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(head)
    w.writerows(rows)
    return buf.getvalue()


def tiles():
    specs = [MS.tile(s) for s in MS.OWNER_TILE_SIZES]
    main = TL.compare(BATH, specs, "TILE-120x60", TILE_C)
    owner_obj = {r["spec_id"]: r for r in TL.compare(BATH, specs, "TILE-120x60", dict(TILE_C, objective="CUTTING_WASTE"))}
    noreuse = {r["spec_id"]: r for r in TL.compare(BATH, specs, "TILE-120x60", dict(TILE_C, min_reusable_m=None))}
    boxed = {s["spec_id"]: TL.best(BATH, MS.with_packaging(s, pieces_per_box=ILLUSTRATIVE_BOX[s["spec_id"]],
                                                          source="TEST PARAMETER - not product data"), TILE_C)["selected"]
             for s in specs}
    head = ["SIZE", "ROLE", "LAYOUT (min consumed, same constraints)", "NET_M2", "FULL", "CUT", "CONSUMED_PCS",
            "MATERIAL_CONSUMED_M2", "PLACED_M2", "JOINT_M2", "REUSABLE_OFFCUTS_M2", "CUTTING_WASTE_M2", "WASTE_PCT",
            "WASTE_IF_OFFCUTS_DISCARDED_M2", "BOXES", "PACKAGING_SURPLUS_M2", "PROCUREMENT", "FEASIBLE", "CONCERNS",
            "RECOMMENDATION"]
    rows = []
    for r in main:
        rows.append([r["spec_id"], r["role"], r["layout"], f3(r["net_m2"]), r["full"], r["cut"], r["consumed"],
                     f3(r["material_consumed_m2"]), f3(r["placed_m2"]), f3(r["joint_m2"]), f3(r["reusable_offcuts_m2"]),
                     f3(r["cutting_waste_m2"]), f"{r['cutting_waste_pct']:.2f}",
                     f3(r["waste_if_offcuts_discarded_m2"]), "UNRESOLVED (no box data in the registry)", "UNRESOLVED",
                     f"{r['procurement_pcs']} pcs (boxes UNRESOLVED)", "YES" if r["feasible"] else "NO",
                     "; ".join(r["concerns"]), r["recommendation"]])
    csv_out = csv_text(head, rows)
    md = ["# 01 Tile size comparison - synthetic 3.00 x 2.00 m bathroom", "",
          "Synthetic room given by the owner for the S1 check (not a project room). Engine: "
          "`engine/source/tile_layout.py` (TILE_RECT_EXACT_V1, rectangle exact). Rebuilt by `build_examples.py`.", "",
          "## Assumptions (every one a stated test parameter; nothing defaulted)", "",
          table(["Parameter", "Value", "Source"], [
              ["room", "3.00 x 2.00 m, net 6.000 m2", "owner S1 example (synthetic)"],
              ["sizes", "120x60 (SELECTED), 60x60, 160x80 cm", "owner-approved sizes, rules/materials 1.0.0"],
              ["joint", "2 mm", "test parameter"], ["minimum cut", "0.10 m (a smaller cut makes a layout infeasible)",
                                                    "test parameter"],
              ["minimum reusable offcut", "0.10 m on both sides", "test parameter"],
              ["kerf", "0 m", "test parameter"], ["offcut rotation", "not allowed", "test parameter"],
              ["layout search", "orientations 0 / 90 deg x start CORNER / CENTRED_TILE / CENTRED_JOINT per axis (18; 9 "
                                "for a square tile), the same for every size", "tile_layout.best"],
              ["objective", "fewest tiles opened, then the least owner-defined cutting waste", "S1 default (see note)"],
              ["perimeter gap", "not modelled (pieces run to the finished wall line)", "S1 limit"],
              ["falls to the drain", "not modelled (flat plane)", "S1 limit, flagged"],
              ["packaging", "the registry has no pieces-per-box: boxes UNRESOLVED", "rules/materials 1.0.0"]]), "",
          "Definitions (owner, M9 S1 addendum): cutting waste = material consumed - placed tile area - reusable offcuts "
          "retained; waste % = cutting waste / net installed area x 100; packaging surplus, procurement and any spare "
          "allowance are kept apart.", "",
          "## Result per candidate (same constraints)", "",
          table(["Size", "Role", "Layout", "Full", "Cut", "Consumed", "Material m2", "Placed m2", "Joint m2",
                 "Reusable offcuts m2", "Cutting waste m2", "Waste %", "Boxes", "Recommendation"],
                [[r["spec_id"], r["role"], r["layout"], r["full"], r["cut"], r["consumed"], f3(r["material_consumed_m2"]),
                  f3(r["placed_m2"]), f3(r["joint_m2"]), f3(r["reusable_offcuts_m2"]), f3(r["cutting_waste_m2"]),
                  f"{r['cutting_waste_pct']:.2f}", "UNRESOLVED", r["recommendation"] or "-"] for r in main]), "",
          "The selected size (120x60) stays the BOQ basis. An alternative that consumes less material is reported as a "
          "recommendation only; the engine never substitutes it.", "",
          "## Cutting plans of the chosen layouts", ""]
    for r in main:
        res = TL.best(BATH, MS.tile(r["spec_id"]), TILE_C)["selected"]
        L = res["layout"]
        md += [f"**{r['spec_id']}** - {r['layout']}: pieces along 3.00 m {L['pieces_x_m']}, along 2.00 m "
               f"{L['pieces_y_m']}; {L['positions']} positions = {L['full_tiles']} full + {L['cut_pieces']} cut; "
               f"{L['cut_from_offcuts']} cut piece(s) taken from offcuts, {L['tiles_opened_for_cuts']} tile(s) opened "
               f"for cuts; offcuts kept {L['offcuts_retained_m']}; scrap {f3(L['scrap_m2'])} m2.", ""]
    md += ["## The same rooms under two other readings (for the owner's decision Q-TILE-1)", "",
           table(["Size", "Owner-waste objective: layout", "consumed", "cutting waste m2",
                  "No offcut reuse (grid upper bound): consumed", "cutting waste m2"],
                 [[s, owner_obj[s]["layout"], owner_obj[s]["consumed"], f3(owner_obj[s]["cutting_waste_m2"]),
                   noreuse[s]["consumed"], f3(noreuse[s]["cutting_waste_m2"])] for s in MS.OWNER_TILE_SIZES]), "",
           "Ranking layouts by the owner-defined cutting waste alone credits retained offcuts as if they were saved, "
           "and so prefers layouts that open MORE tiles (120x60: 12 tiles against 9). Until cross-room offcut reuse is "
           "planned (S2), S1 ranks by the material consumed and reports the owner-defined waste of that layout.", "",
           "## Illustrative packaging (TEST PARAMETERS - not product data)", "",
           table(["Size", "pcs / box (test)", "Consumed pcs", "Boxes", "Box area m2", "Packaging surplus m2"],
                 [[s, ILLUSTRATIVE_BOX[s], boxed[s]["units"]["consumed_units"], boxed[s]["packaging"]["packs"],
                   f3(boxed[s]["packaging"]["pack_area_m2"]), f3(boxed[s]["packaging"]["packaging_surplus_m2"])]
                  for s in MS.OWNER_TILE_SIZES]), "",
           "## Reference only: the takeoff skill's flat percentages (unconfirmed defaults, never used)", "",
           table(["Size", "Flat % (skill)", "Net x (1 + %) m2", "Layout material consumed m2"],
                 [[r["spec_id"], SKILL_FLAT[r["spec_id"]], f3(6.0 * (1 + SKILL_FLAT[r["spec_id"]] / 100.0)),
                   f3(r["material_consumed_m2"])] for r in main]), "",
           "A flat percentage ignores the room: here it overstates the 120x60 and 160x80 material and cannot say how "
           "many tiles to open. UP-CER-010 keeps it as a reference only.", ""]
    return csv_out, "\n".join(md)


def membrane_rows(tag, r):
    rows = []
    L = r["layout"]
    for s in L["surfaces"]:
        rows.append([tag, "SURFACE", s["item_code"] + (f" {s['doorway']}" if s.get("doorway") else ""), f3(s["net_m2"]),
                     s["formula"]])
    for k, v in L["seams"].items():
        rows.append([tag, "SEAM", k, f3(v["running_lm"]), f"count {v.get('count', '-')}, lap {v['lap_m']:g} m"])
    for rl in L["rolls"]:
        for sg in rl["segments"]:
            rows.append([tag, "ROLL_SEGMENT", f"roll {rl['roll']}: {sg['for']}", f3(sg["length_m"]), "length m x 1.00 m"])
        rows.append([tag, "ROLL_TAIL", f"roll {rl['roll']} untouched", f3(rl["untouched_tail_m"]), "packaging surplus"])
    for i, p in enumerate(L["band_pieces_m"], 1):
        rows.append([tag, "BAND_PIECE", f"upturn piece {i}", f3(p), f"length m x {L['band_width_m']:g} m"])
    for w, ln, why in L["offcuts_retained"]:
        rows.append([tag, "OFFCUT_RETAINED", why, f3(w * ln), f"{w:g} x {ln:g} m"])
    for w, ln, why in L["scrap"]:
        rows.append([tag, "CUTTING_WASTE", why, f3(w * ln), f"{w:g} x {ln:g} m"])
    p = r["packaging"]
    for k, v in (("net installed", r["net_installed_m2"]), ("overlap", r["overlap_m2"]),
                 ("cutting waste", r["cutting_waste_m2"]), ("reusable offcuts", r["reusable_offcuts_m2"]),
                 ("packaging surplus", p["packaging_surplus_m2"]), ("rolls x roll area", p["pack_total_m2"])):
        rows.append([tag, "BALANCE", k, f3(v), "rolls x 10 m2 = net + overlap + cutting waste + offcuts + surplus"])
    return rows


def membrane():
    spec = MS.membrane()
    h = RS.rule("UP-WP-002")["value"]
    base = {"upturn_h_m": h, "doorways": DOOR_3x2, "doorway_detail": "NOT_ESTABLISHED", "direction": "MIN_MATERIAL",
            "min_reusable_m": 0.30, "penetrations": 1}
    a = ML.plan(BATH, spec, constraints=base)
    w = ML.plan(BATH, spec, constraints=dict(base, doorway_detail="UPTURN_WITHIN_DOORWAY_PIECE"))
    f = ML.plan(WP1, spec, constraints={"upturn_h_m": h, "doorways": DOOR_WP1, "direction": "ALONG_Y",
                                        "min_reusable_m": 0.30})
    head = ["EXAMPLE", "ROW", "WHAT", "VALUE (m2 / lm / m)", "NOTE"]
    rows = membrane_rows("BATH-3x2", a) + membrane_rows("BATH-3x2-DOORWAY-IN-PIECE", w) + membrane_rows("WP-1", f)
    L = a["layout"]
    md = ["# 02 Membrane roll layout - synthetic 3.00 x 2.00 m bathroom", "",
          "Engine: `engine/source/membrane_layout.py` (MEMBRANE_RECT_EXACT_V1, rectangle exact). Rebuilt by "
          "`build_examples.py`.", "",
          "## Inputs", "",
          table(["Parameter", "Value", "Source"], [
              ["room", "3.00 x 2.00 m (synthetic)", "owner S1 example"],
              ["door", "0.80 m wide in a 0.20 m wall", "test parameter"],
              ["roll", "1.00 x 10.00 m (10 m2)", "MEM-URBAN-DEFAULT-1x10, owner default (UP-WP-005)"],
              ["side / end lap", "0.10 / 0.10 m minimum", "owner minimum (a stricter data sheet would win)"],
              ["upturn", f"{h:g} m on the full boundary, doorway included", "UP-WP-002 v2.0.0"],
              ["doorway detail", "NOT_ESTABLISHED: both rows kept and flagged", "UP-WP-003 v1.1.0, Q-WP-1 open"],
              ["upturn band", "0.20 m + 0.10 m lap onto the floor = 0.30 m, cut as 3 lanes across the roll", "S1 method"],
              ["strip direction", "both tried; fewer rolls, then less material, wins", "S1 method"],
              ["minimum reusable offcut", "0.30 m on both sides", "test parameter"],
              ["corners / penetrations", "counted, not quantified (system not named)", "UP-WP-005 note"]]), "",
          "## Net surfaces (the BOQ lines)", "",
          table(["Item", "Net m2", "Formula"], [[s["item_code"] + (f" {s['doorway']}" if s.get("doorway") else ""),
                                                f3(s["net_m2"]), s["formula"]] for s in L["surfaces"]]), "",
          f"Net installed {f3(a['net_installed_m2'])} m2. The doorway piece lies in the wall thickness, outside the "
          "floor polygon, so it is never inside the floor area; whether the doorway 0.20 m is a separate return or sits "
          "inside the doorway piece is the open detail (flags DOORWAY_UPTURN_DETAIL_REQUIRED, "
          "DOORWAY_DOUBLE_COVERAGE_REVIEW). With the detail UPTURN_WITHIN_DOORWAY_PIECE the doorway segment is billed "
          f"once and the net reads {f3(w['net_installed_m2'])} m2.", "",
          "## Roll plan", "",
          f"Direction {L['direction']}: {L['floor_strips']} floor strips of {L['strip_length_m']:g} m across "
          f"{L['cross_width_m']:g} m (each further strip adds 0.90 m; the last one trimmed to "
          f"{L['last_strip_width_m']:g} m); upturn band {L['band_width_m']:g} m in {len(L['band_pieces_m'])} pieces "
          f"{L['band_pieces_m']}.", "",
          table(["Seam", "Count", "Lap m", "Running lm"], [[k, v.get("count", "-"), f"{v['lap_m']:g}", f3(v["running_lm"])]
                                                           for k, v in L["seams"].items()]), "",
          table(["Roll", "Segments (m)", "Cut m", "Untouched tail m"],
                [[rl["roll"], "; ".join(f"{s['length_m']:g} {s['for']}" for s in rl["segments"]), f3(rl["cut_m"]),
                  f3(rl["untouched_tail_m"])] for rl in L["rolls"]]), "",
          "Alternatives tried: " + "; ".join(f"{x['direction']} {x['rolls']} rolls, consumed {f3(x['consumed_m2'])} m2, "
                                             f"cutting waste {f3(x['cutting_waste_m2'])} m2" for x in L["alternatives"])
          + ".", "",
          "## Material balance", "",
          table(["Component", "m2"], [["net installed", f3(a["net_installed_m2"])], ["overlap (laps)", f3(a["overlap_m2"])],
                                      ["cutting waste", f3(a["cutting_waste_m2"])],
                                      ["reusable offcuts retained", f3(a["reusable_offcuts_m2"])],
                                      ["packaging surplus (untouched roll tails)", f3(a["packaging"]["packaging_surplus_m2"])],
                                      [f"= {a['packaging']['packs']} rolls x 10 m2", f3(a["packaging"]["pack_total_m2"])]]),
          "", f"Cutting waste {a['cutting_waste_pct']:.2f} % of the net installed area (owner definition). Overlap, "
              "cutting waste, offcuts and surplus are separate rows; none of them enters the BOQ net.", "",
          "## What the forbidden shortcuts would have said (reference only)", "",
          table(["Shortcut", "Rolls", "Why it is wrong here"],
                [["net / 10 m2", math.ceil(a["net_installed_m2"] / 10.0), "ignores laps, trims and the band lanes"],
                 ["net + 10 %", math.ceil(a["net_installed_m2"] * 1.1 / 10.0), "a flat rate, not the cutting plan"],
                 ["roll plan (S1)", a["packaging"]["packs"], "strips, laps, band lanes and whole rolls"]]), "",
          "## M9A fixture WP-1 (2.30 x 3.20 m, door 0.90 m) on the same roll", "",
          f"Strips along 3.20 m: {f['layout']['floor_strips']} (covering 2.80 m), floor strip material "
          f"{f3(sum(s['length_m'] for rl in f['layout']['rolls'] for s in rl['segments'] if s['for'].startswith('floor')))}"
          f" m2 against {f3(2.3 * 3.2)} m2 net; net installed {f3(f['net_installed_m2'])} m2; "
          f"{f['packaging']['packs']} rolls; overlap {f3(f['overlap_m2'])} m2; cutting waste {f3(f['cutting_waste_m2'])} m2.",
          ""]
    return csv_text(head, rows), "\n".join(md)


def rooms():
    b = RB.build(HERE / "SYNTHETIC_ROOMS_S1.json")
    md = ["# 03 Synthetic room BOQ (the S1 room schedule)", "",
          "Input `SYNTHETIC_ROOMS_S1.json` (geometry source SYNTHETIC_FIXTURE): 6 rooms on two floors - two wet rooms, "
          "a polygon kitchen (layout BLOCKED for S2), and a store with no dimensions (BLOCKED_RFI). The room-by-room "
          "workbook is built by `tools/urban_boq_m9.py rooms` (xlsx: in the S1 ZIP only, never committed).", "",
          "## Lines", "",
          table(["Floor", "Room", "Item", "Net m2", "Evidence", "Rule"],
                [[ln["location"]["floor"], ln["location"]["room_id"], ln["item_code"], f3(ln["measured_net"]) or "-",
                  ln["evidence_state"], f"{ln['rule']['rule_id']}@{ln['rule']['version']}"] for ln in b["lines"]]), "",
          "## Material results", "",
          table(["Room", "Method", "State", "Units", "Consumed m2", "Cutting waste m2", "Offcuts m2", "Packs", "Blocked by"],
                [[m["location"].get("room_id"), m["method"], m["state"],
                  (m.get("units") or {}).get("consumed_units", "-"), f3(m["consumed_m2"]) or "-",
                  f3(m["cutting_waste_m2"]) or "-", f3(m["reusable_offcuts_m2"]) or "-",
                  (m.get("packaging") or {}).get("packs") if (m.get("packaging") or {}).get("state") == "RESOLVED"
                  else "UNRESOLVED", m.get("blocked_by") or ""] for m in b["materials"]]), "",
          "## Unresolved", "",
          table(["Room", "Item", "Question / reason"], [[u["room_id"], u["item"], u["reason"]] for u in b["unresolved"]]),
          ""]
    return "\n".join(md)


def build():
    t_csv, t_md = tiles()
    m_csv, m_md = membrane()
    return {"01_TILE_COMPARISON_3x2_BATHROOM.csv": t_csv, "01_TILE_COMPARISON_3x2_BATHROOM.md": t_md,
            "02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.csv": m_csv, "02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.md": m_md,
            "03_SYNTHETIC_ROOM_BOQ.md": rooms()}


def main():
    for name, text in build().items():
        (HERE / name).write_text(text, encoding="utf-8")
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
