"""T-575 development villa build: one row per WIRING MANIFEST V8 REBAR_OMISSION row (dome shells, dome rings,
lift-pit walls), each a bounded HELD range in t with its bar-group table, or HELD BLANK with the missing item named.

Inputs: values only (no drawing text). Own reads this run of Drive 'Alsenan chalet project' / 'ST7757.pdf' p.7 (DETAIL
OF DOME, N.I.S), p.10 (simple-beam schedule, row B4), p.14 (lift detail); ring geometry from the merged S8.3 / T-160
registers (research/alsenan_dome_ring_s8_3/04_RING_GEOMETRY.csv); lift ring from the merged T-322 input.
Run: .work/venv/bin/python -I research/agents_t575/t575_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t575_rebar as R  # noqa: E402

OUT = HERE / "out" / "T575_DOME_LIFT_REBAR.json"
V8 = ROOT / "research" / "agents_t569" / "WIRING_MANIFEST_V8.json"
RING_CSV = ROOT / "research" / "alsenan_dome_ring_s8_3" / "04_RING_GEOMETRY.csv"
LIFT = ROOT / "research" / "agents_t322" / "ALSENAN_LIFT_BASE_INPUT.json"
STOCK_M = 12.0  # owner proposal s.2 stock length: used only to say whether a lap is needed, never its length

SHELL = {"chord": 4.42, "rise": 1.90, "thickness": 0.10, "d_mm": 12, "s": 0.15,
         "src": "ST p.7 DETAIL OF DOME: chord / rise / thickness dims; one mesh, two directions, d12 at 0.15 (both labels)"}
RING_DETAIL = {"layers": [{"role": "RING_TOP", "n": 3, "d_mm": 16}, {"role": "RING_BOTTOM", "n": 3, "d_mm": 18}],
               "links_per_m": 8, "link_d": 8, "side": {"n_per_face": 2, "d_mm": 14, "s": 0.20},
               "depth": None, "src": "ST p.7 DETAIL OF DOME ring section (both cuts); depth dimensioned 'as per arch'"}
RING_B4 = {"layers": [{"role": "RING_TOP", "n": 2, "d_mm": 12}, {"role": "RING_BOTTOM", "n": 4, "d_mm": 16}],
           "links_per_m": 6, "link_d": 8, "side": None, "depth": 0.50,
           "src": "ST p.10 simple-beam schedule row B4 20 x 50 (plan tag on the west ring, S6 / T-160)"}
LIFT_BARS = {"horiz": {"d_mm": 12, "per_m": 6}, "vert": {"d_mm": 16, "per_m": 6}, "top": {"n": 2, "d_mm": 12},
             "src": "ST p.14 lift detail: leader to the bar dots = horizontals d12 6/m each face; leader crossing the "
                    "vertical lines = verticals d16 6/m each face, drawn down to the raft bottom mat; 2 d12 in the "
                    "wall top; 2 d16 at the wall foot are raft bars (footing line, not here); pit depth not printed"}


def ring_readings(dome: str) -> list:
    rows = {r["ROW_ID"]: r for r in csv.DictReader(RING_CSV.open(encoding="utf-8"))}
    out = []
    for kind, tag in (("PLAN", "RING-PLAN"), ("DETAIL", "RING-DETAIL")):
        r = rows[f"{dome}-{tag}"]
        r1, r2 = float(r["R1_MM"]) / 1000.0, float(r["R2_MM"]) / 1000.0
        out.append({"id": f"{dome}:{kind}", "r_c": (r1 + r2) / 2.0, "width": r2 - r1, "inbay_area": float(r["PLAN_AREA_M2"])})
    return out


def lift_segments() -> dict:
    d = json.loads(LIFT.read_text(encoding="utf-8"))
    (ox0, oy0, ox1, oy1), (ix0, iy0, ix1, iy1) = d["ring"]["outer"], d["ring"]["inner"]
    w = (ix0 - ox0) / 1000.0
    cols = d["ring"]["columns"]
    # walls between the column faces (mm): N and S walls along x, W and E walls along y
    def free(lo, hi, spans):
        covered = sum(max(0.0, min(hi, b) - max(lo, a)) for a, b in spans)
        return (hi - lo - covered) / 1000.0
    north = free(ox0, ox1, [(c[0], c[2]) for c in cols if c[3] >= oy1 - 1 and c[1] <= iy1 + 1])
    south = free(ox0, ox1, [(c[0], c[2]) for c in cols if c[1] <= oy0 + 1 and c[3] >= iy0 - 1])
    west = free(iy0, iy1, [(c[1], c[3]) for c in cols if c[0] <= ox0 + 1])
    east = free(iy0, iy1, [(c[1], c[3]) for c in cols if c[2] >= ox1 - 1])
    # N / S: outer width minus the corner columns; W / E: between the inner faces minus the column parts (both faces
    # of a 0.20 wall between full-band-width columns have the same free length)
    segs = {"N": north, "S": south, "W": west, "E": east}
    return {"w": w, "segments": segs, "outer_perimeter": 2 * ((ox1 - ox0) + (oy1 - oy0)) / 1000.0,
            "centre_perimeter": 2 * ((ox1 - ox0) + (oy1 - oy0)) / 1000.0 - 4 * w,
            "raft_H": d["raft"]["H"]["value"] / 1000.0}


def t(kg):
    return float(R.to_t(kg))


def build() -> dict:
    v8 = json.loads(V8.read_text(encoding="utf-8"))["rebar_omission"]["rows"]
    rows = []
    shell = R.dome_shell(SHELL["chord"], SHELL["rise"], SHELL["thickness"], SHELL["d_mm"], SHELL["s"])
    for r in v8:
        el = r["concrete_element"]
        base = {"row_id": r["expected_after"]["element_id"], "concrete_line": r["concrete_line"],
                "concrete_class": r["concrete_class"], "unit": "t"}
        if el.startswith("HL:DOME_SHELL:"):
            g = shell["groups"]
            lo = g["SHELL_HOOP"]["kg"][0] + g["SHELL_MERIDIONAL"]["kg"][0]
            hi = g["SHELL_HOOP"]["kg"][1] + g["SHELL_MERIDIONAL"]["kg"][1]
            base.update(status="HELD_RANGE", t_low=t(lo), t_high=t(hi), groups=[
                {"group": k, "d_mm": 12, "spacing_m": 0.15, "m": [round(x, 4) for x in v["m"]],
                 "t": [t(x) for x in v["kg"]], "status": v["status"], "why": v["why"]} for k, v in g.items()] + [
                {"group": "SHELL_ANCHORAGE_INTO_RING", "status": "HELD_BLANK",
                 "why": "leg into the ring follows the ring depth ('as per arch'); detail N.I.S"},
                {"group": "SHELL_HOOP_LAPS", "status": "HELD_BLANK",
                 "why": f"longest hoop {shell['longest_hoop_m']:.3f} m > {STOCK_M} m stock: laps needed, no lap printed "
                        "for shell bars (owner 2026-10-24 15:31 (3): every other lap HELD)"}],
                source=SHELL["src"], geometry={"R_out": round(shell["R_out"], 6), "a": round(shell["a"], 6),
                                               "rho_bounds": [round(x, 6) for x in shell["rho_bounds"]]})
        elif el.startswith("HL:DOME_RING:"):
            west = "DOME-1F-W" in el
            dome = "DOME-A" if west else "DOME-B"
            rd = ring_readings(dome)
            readings = [("DETAIL", RING_DETAIL)] + ([("B4", RING_B4)] if west else [])
            groups, los, his = [], [], []
            for name, spec in readings:
                mains = R.ring_mains(spec["layers"], rd)
                los.append(mains["kg"][0]); his.append(mains["kg"][1])
                groups.append({"group": f"RING_MAINS[{name}]", "status": "HELD_RANGE",
                               "layers": [f"{l['n']} x d{l['d_mm']} ({l['role']})" for l in spec["layers"]],
                               "kg_per_m": round(mains["kg_per_m"], 6),
                               "readings": [{"position": x["id"], "inbay_m": round(x["inbay_m"], 4),
                                             "circle_m": round(x["circle_m"], 4), "t": [t(k) for k in x["kg"]]}
                                            for x in mains["readings"]],
                               "t": [t(k) for k in mains["kg"]], "source": spec["src"]})
                n_lo = R.ring_link_count(spec["links_per_m"], min(x["inbay_m"] for x in mains["readings"]))
                n_hi = R.ring_link_count(spec["links_per_m"], max(x["circle_m"] for x in mains["readings"]))
                groups.append({"group": f"RING_LINKS[{name}]", "status": "HELD_BLANK", "count": [n_lo, n_hi],
                               "why": "count by the printed rate; mass needs cover + hooks (not printed)"
                                      + ("" if spec["depth"] else " + ring depth ('as per arch')")})
                if spec["side"]:
                    groups.append({"group": f"RING_SIDE[{name}]", "status": "HELD_BLANK",
                                   "why": "rows at the printed spacing over a depth 'as per arch'"})
            circle = max(x["circle_m"] for x in R.ring_mains(RING_DETAIL["layers"], rd)["readings"])
            groups.append({"group": "RING_LAPS_AND_JUNCTIONS", "status": "HELD_BLANK",
                           "why": f"closed ring {circle:.3f} m > {STOCK_M} m stock; no lap / junction detail with "
                                  "the framing beams and columns"})
            conflict = ("B4 tag + schedule vs DETAIL OF DOME (R-T575-5; S8.3 CF-S8.3-04): both evaluated; Q-44 A chose "
                        "B4 for a skylight with the dome removed, S0 keeps the dome (Q-29 refined 2026-10-22)") if west \
                else "no member tag (Q-61 C(3)): DETAIL OF DOME only"
            base.update(status="HELD_RANGE", t_low=t(min(los)), t_high=t(max(his)), groups=groups,
                        ring_position_readings=[{"id": x["id"], "r_c": round(x["r_c"], 6),
                                                 "inbay_area_m2": x["inbay_area"]} for x in rd],
                        bar_source_conflict=conflict)
        elif el.startswith("DG5:DOME-3"):
            base.update(status="HELD_BLANK", t_low=None, t_high=None, groups=[], missing=(
                "no structural drawing of the third (tower) dome: architectural only (S8.3 CF-S8.3-01, Q-27 / "
                "Q-S8.3-03); the p.7 detail is not referenced to it and its size differs (chord 4.41, rise 2.15): "
                "applying it would be a borrowed value"))
        elif el.startswith("LIFT_PIT:WALLS"):
            L = lift_segments()
            segs = [L["segments"][k] for k in ("N", "S", "W", "E")]
            pw = R.pit_walls(segs, LIFT_BARS["horiz"], LIFT_BARS["vert"], LIFT_BARS["top"], L["raft_H"],
                             L["w"] / 2.0, [L["outer_perimeter"], L["centre_perimeter"]], L["centre_perimeter"])
            base.update(status="HELD_BLANK", t_low=None, t_high=None, missing=(
                "pit depth / wall height h not printed ('as per lift manufacturer'); bars only as kg(h)"),
                formula={"kg(h)": "A x h + B", "A_t_per_m": [t(x) for x in pw["A_kg_per_m_height"]],
                         "B_t": [t(x) for x in pw["B_kg"]], "n_vertical": pw["n_vertical"],
                         "net_wall_m": round(pw["net_wall_m"], 4),
                         "segments_m": {k: round(v, 4) for k, v in L["segments"].items()},
                         "horizontal_run_per_row_m": [round(x, 4) for x in pw["horizontal_run_per_row_m"]]},
                groups=[{"group": "WALL_HORIZONTAL", "d_mm": 12, "per_m": 6, "status": "HELD_BLANK", "why": "h"},
                        {"group": "WALL_VERTICAL", "d_mm": 16, "per_m": 6, "status": "HELD_BLANK",
                         "why": "h; embedment into the raft bounded 0 .. raft depth (cover not printed)"},
                        {"group": "WALL_TOP_BARS", "d_mm": 12, "n": 2, "status": "HELD_BLANK",
                         "why": "bounded in B; part of a wall that has no height"},
                        {"group": "WALL_LAPS_AND_COLUMN_JUNCTIONS", "status": "HELD_BLANK",
                         "why": "not printed: bars stopping at or running through the lift columns is the A range"}],
                source=LIFT_BARS["src"])
        else:
            raise R.T575Error(f"unmapped V8 row {el}")
        rows.append(base)
    rng = [r for r in rows if r["status"] == "HELD_RANGE"]
    return {"schema": "URBAN_T575_DOME_LIFT_REBAR_V1", "task": "T-575", "method": "DOME_LIFT_REBAR_V1 (R-T575-1 .. 6)",
            "unit_mass": "d^2 / 162 kg/m (rebar_unit_mass.D2_OVER_162)", "candidate": "ARCH_TAKEOFF_V3.0.58 (unchanged)",
            "rows": rows, "totals": {"rows": len(rows), "held_range_rows": len(rng),
                                     "held_blank_rows": len(rows) - len(rng),
                                     "t_low": round(sum(r["t_low"] for r in rng), 6),
                                     "t_high": round(sum(r["t_high"] for r in rng), 6), "valued_t": 0.0},
            "freelancer": "TYPED_LUMP 44.19 t, no bar row (T-560): NOT_COMPARABLE, no %"}


def main():
    res = build()
    txt = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        ok = OUT.read_text(encoding="utf-8") == txt
        print("CHECK", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    for r in res["rows"]:
        print(r["row_id"], r["status"], r["t_low"], r["t_high"], r.get("formula", {}).get("A_t_per_m"))
    print(res["totals"])


if __name__ == "__main__":
    main()
