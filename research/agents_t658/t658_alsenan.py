"""T-658 development villa (Alsenan): the 61 HELD B10 lines of trial BOQ r4 (candidate V3.0.61) for columns (29),
ground beams (29), straps (2) and footing (1), member by member (R-T658-1 .. 6, t658_rules.py).

Inputs are committed, sha-pinned files only; the drawing reads of this run are recorded below as printed facts with their
sheet (Drive 'Alsenan chalet project' / ST7757 dxf.dxf, decoded into .work/private only). No client name, coordinate
beyond the committed element ids, or drawing content beyond the cited printed figures is tracked. Research only: nothing
wired, nothing released, no candidate / registry / rule-version file written.

Run: python -I research/agents_t658/t658_alsenan.py  -> research/agents_t658/out/T658_LEDGER.json
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
import t658_rules as R  # noqa: E402

TRIAL_R4 = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
CENSUS = ROOT / "research/agents_t426/CENSUS_T426.json"
T449 = ROOT / "research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.json"
T572 = ROOT / "research/agents_t572/out/T572_HELD_BOUNDS.json"
FACTS = ROOT / "research/agents_t449/DEVELOPMENT-VILLA-T131.concrete_facts.json"
LINE_INDEX = ROOT / "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
AREAS = HERE / "out/T658_BAND_AREAS.json"      # r2: drawn plan areas, t658_measure_bands.py on the ST dxf (derived only)
PINS = {TRIAL_R4: "9e032726257c4961", CENSUS: "b297bb1402f53942", T449: "a15bb04b2109e29a",
        T572: "a39e7b4b838e3590", FACTS: "16a5273ac0b9103f",
        LINE_INDEX: "10e5f116d30af67f", AREAS: "e9e3871a9ae7a50b"}
DXF_SHA16 = "9f9d1179a5d2a663"                 # 'ST7757 dxf.dxf' (Drive 'Alsenan chalet project'), the Checker's own file
OUT = HERE / "out/T658_LEDGER.json"
CODES = ("STR.CONC.COLUMN", "STR.CONC.GROUND_BEAM", "STR.CONC.STRAP", "STR.CONC.FOOTING")
D = Decimal

# Printed facts read this run (own reads of the ST dxf, schedule text; figures in cm as printed).
READS = {
    "ST_COL_SCHEDULE": "ST 'Schedule of Columns' (FOUNDATION / GROUND FLOOR / 1st floor / 2nd floor & Top): C1 2F 20x50; "
                       "C2 2F 20x50; C3 GF 25x50, 2F 20x50; C5 2F 20x50; C9 2F 20x70; C GF 20x50, 1F / 2F blank; "
                       "CN FOUNDATION 30x30 only",
    "ST_P13_GB_TITLES": "ST p.13 ground-beam sections (without concentrated load): 'Less then 2.5m length' 30x30, "
                        "'Less than 5m length' 30x40, 'More than 5m' 30x60; no precedence printed (D-34)",
    "ARCH_SECTION_LEVELS": "arch sheet 10 section: main roof +13.90 (top of the roof band, 0.50 parapet above), annex "
                           "roof +4.30; finished marks, no roof build-up printed (D-39, Q-54 answer B)",
    "R2_MARKS_REREAD": "re-read 2026-11-10 from the drawings (not the facts file): arch sheet 10 SECTION A-A prints "
                       "+/-0.00, +1.00, +5.50, +9.70, +13.90 (storeys 450 / 420 / 420, parapet 50, total 1440); arch "
                       "sheet 9 NORTH EAST ELEVATION prints the annex +0.30 floor, +4.30 roof (storey 400); the ST dxf "
                       "LEVEL layer prints +0.15 / +0.30 / +1.00 (GF plan) and +9.70 (twice, SFRS sheet). +13.90 and "
                       "+4.30 AGREE. +9.65 and +0.25 are NOT printed as text on either set: they are the APPROVED "
                       "structural datums of the facts register (DESIGNER 2026-10-24 / -25), = printed finished level "
                       "- 0.05 (9.70, 0.30) and consistent with the printed storeys (13.90 - 9.65 = 4.20 + 0.05; "
                       "4.30 - 0.25 = 4.00 + 0.05)",
}
GB_TITLES = [("LT2_5M", "<", "2.5", ("0.30", "0.30")), ("LT5M", "<", "5", ("0.30", "0.40")),
             ("GT5M", ">", "5", ("0.30", "0.60"))]
MAIN_ROOF_MARK = D("13.90")
ANNEX_ROOF_MARK = D("4.30")
# R-T658-7 / -8 (r2). Unloaded oblique bands measured on the drawn plan area (both outline readings where the drawn end
# is open); loaded (D-33) runs carried LOWER_ONLY on the least applicable title x the drawn area.
OBLIQUE = {"BAND0038": ("BAND0038:AS_DRAWN", "BAND0038:EXTENDED"), "BAND0039": ("BAND0039",)}
LOADED = {"BAND0037.1": ("182+183",), "BAND0019": ("141+7DA",), "BAND0010.3": ("7E7+7E8",), "BAND0040": ("180+181",),
          "BAND0008.2": ("7E7+7E8",), "BAND0008.1": ("175+7DE", "176+7E6", "7DC+7DD"),
          "BAND0023:7DC+7DD#1": ("7E1+7E2",), "BAND0032:7E7+7E8#2": ("114+115+7DF",)}
SPAN_READINGS = {"BAND0008.1": (("BAND0008.1", "5.02"), (None, "4.97"))}   # T-141 / T-430: band end vs column-face frame
CEILING_SECTIONS = {  # non-conflict blanks: one printed schedule section (no SECTION_CONFLICT in the T-449 record)
    "L-d79d17d14f39d5148cb8": ("0.10", "C1 2F 20x50"),
    "L-33a9b7728781fcba12e2": ("0.10", "C2 2F 20x50"),
    "L-919a5749ef79759e01ca": ("0.10", "C2 2F 20x50"),
    "L-26f6b6f2365c72e42291": ("0.10", "C2 2F 20x50"),
    "L-53f223b06db14ac41d47": ("0.14", "C9 2F 20x70"),
    "L-fad18af6e7139a5e99d1": ("0.125", "C3 GF 25x50 (annex)"),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def check_pins() -> None:
    for p, h in PINS.items():
        got = _sha(p)
        if got != h:
            raise R.Refused(f"input {p.name} changed: {got} != pinned {h}")


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def before_lines() -> dict:
    eids = {x["line_id"]: x["element_id"] for x in _load(LINE_INDEX)["lines"]}
    out = {}
    for x in _load(TRIAL_R4)["per_line"]:
        if x["item_code"] in CODES and x["unit"] == "m3" and x["class"] == "HELD":
            out[x["line_id"]] = dict(x, element_id=eids[x["line_id"]])
    return out


def _fact(fid):
    return [f for f in _load(FACTS)["facts"] if f["fact_id"] == fid][0]["value"]


def _readings(key, census_line, areas):
    """Drawn readings of one run: span (census L, Checker T-426 Gate A, else the drawn edge), area, width, edges."""
    b = (census_line or {}).get("runs", [{}])[0].get("printed_b_m") or "0.30"
    out = []
    for rid, span in SPAN_READINGS.get(key, ((k, None) for k in OBLIQUE.get(key, (key,)))):
        if rid is None:          # a span reading on another frame of the same orthogonal band: rectangle span x width
            out.append({"span": span, "area_m2": D(span) * D(str(b)), "width_m": b, "printed_b_m": b,
                        "edges_m": [span, span]})
            continue
        a = areas[rid]
        sp = span or (census_line["runs"][0]["L_m"] if census_line and len(census_line["runs"]) == 1
                      else min(a["band_edges_m"]))
        out.append({"span": sp, "area_m2": a["area_m2"], "width_m": a["width_m"], "printed_b_m": b,
                    "edges_m": a["band_edges_m"]})
    return out


def build() -> dict:
    check_pins()
    areas_doc = _load(AREAS)
    if areas_doc["dxf_sha256_16"] != DXF_SHA16:
        raise R.Refused("band areas not measured on the pinned ST dxf")
    areas = areas_doc["runs"]
    before = before_lines()
    assert len(before) == 61, len(before)
    census = {x["line_id"]: x for x in _load(CENSUS)["lines"]}
    reg = {x["line_id"]: x for x in _load(T449)["entries"] if x.get("line_id")}
    t572 = {c["line_id"]: c for c in _load(T572)["components"] if c.get("line_id")}
    s2f = D(str(_fact("LEVEL.STRUCTURAL_TOP.2F.MAIN")))
    annex_top = D(str(_fact("LEVEL.STRUCTURAL_TOP.GF.ANNEX")))
    ng = D(str(_fact("LEVEL.NATURAL_GROUND.OUTER")))
    rows = []
    for lid, b in sorted(before.items(), key=lambda kv: (kv[1]["item_code"], kv[0])):
        ic, eid = b["item_code"], b["element_id"]
        bef = (b["held_low"], b["held_high"])
        cause = b.get("cause") or ""
        src = b.get("cause_source") or ""
        key = eid.split("GROUND:", 1)[1] if "GROUND:" in eid else ""
        if ic == "STR.CONC.GROUND_BEAM" and key in LOADED:
            c = census.get(lid)
            rds = _readings(key, c, areas)
            lo = R.loaded_floor(rds, GB_TITLES, "T-426 census span / T-658 drawn outline (ST dxf)")
            oblique = any(D(str(x["edges_m"][0])) != D(str(x["edges_m"][1])) for x in rds)
            rows.append(R.row(lid, ic, eid, "LOWER_ONLY", low=lo, before=bef,
                              flags=["D-33_LOADED_SPAN", "R-T658-8"] + (["AREA_NOT_RECTANGLE"] if oblique else []),
                              item=f"D-33 run carrying a landing beam ({' / '.join(LOADED[key])} lands): ST p.13 prints "
                                   "sections only 'without concentrated load'; high NOT ESTABLISHED by the drawings",
                              basis="R-T658-8: least of drawn plan area x least title depth over the readings "
                                    + "; ".join(f"span {x['span']} m, area {x['area_m2']} m2" for x in rds)))
        elif ic == "STR.CONC.GROUND_BEAM" and key in OBLIQUE:
            c = census.get(lid)
            rds = _readings(key, c, areas)
            lo, hi, fl = R.area_bound(rds, GB_TITLES, "T-426 census span / T-658 drawn outline (ST dxf)")
            rows.append(R.row(lid, ic, eid, "BOUNDED", low=lo, high=hi, before=bef,
                              flags=fl + ["R-T658-7", "AREA_NOT_RECTANGLE"],
                              basis="R-T658-7: drawn plan area x the titles that hold; "
                                    + "; ".join(f"area {x['area_m2']} m2 (edges {x['edges_m']} m), span {x['span']} m"
                                                for x in rds)))
        elif ic == "STR.CONC.GROUND_BEAM":
            c, r = census.get(lid), reg.get(lid)
            is_range = bef[0] is not None and D(str(bef[0])) < D(str(bef[1]))
            if r and r["action"] == "HOLD_RANGE" and r["patch"].get("range") and bef[0] is None:
                rg = r["patch"]["range"]
                rows.append(R.row(lid, ic, eid, "BOUNDED", low=rg["low"], high=rg["high"], before=bef,
                                  flags=["T430_RANGE_NOT_WIRED", "D-33_LOADED_SPAN"],
                                  basis=f"R-T658-2 / R-GB-NECK-CUT-1: {rg['low_basis']} .. {rg['high_basis']} "
                                        "(T-430 register HOLD_RANGE; candidate line carries no bound)"))
            elif (not is_range and c and len(c["runs"]) == 1
                  and c["runs"][0]["section_status"] in ("RANGE", "ON_LIMIT")):
                run = c["runs"][0]
                lo, hi, fl = R.span_range(D(str(run["L_m"])), GB_TITLES, "T-426 census span (Checker T-426 Gate A)")
                if run["d33_held"]:
                    fl.append("D-33_LOADED_SPAN")
                if bef[0] is not None and D(str(bef[0])) == D(str(bef[1])) and "ON_LIMIT" not in fl:
                    lo = R.d6(bef[0])          # keep the line's own drawn low (width / depth to the drawn mm)
                    hi = R.d6(lo * D("0.40") / D(str(c["candidate_D_m"])))
                rows.append(R.row(lid, ic, eid, "BOUNDED", low=lo, high=hi, before=bef, flags=fl,
                                  basis=f"R-T658-{'2' if 'ON_LIMIT' in fl else '1'}: span {run['L_m']} m x 0.30 x the "
                                        f"titles that hold ({src})"))
            elif r and r["rule"] == "R-GB-EXT-DEPTH-1" and r["action"] == "CONFLICT":
                runs = [x["L_m"] for x in r["evidence"]["runs"]]
                floor = R.literal_floor(runs, r["evidence"]["runs"][0]["b_m"], annex_top, ng,
                                        "T-449 register runs (T-289)")
                lit = (r["rule_result"].get("readings") or {}).get("literal_two_levels_m3")
                if lit is not None:
                    assert abs(R.d6(lit) - floor) <= D("0.000002"), (lid, lit, floor)
                rows.append(R.row(lid, ic, eid, "LOWER_ONLY", low=floor, before=bef, flags=["D-35_ANNEX"],
                                  item="D-35 annex exterior ground-beam depth (literal +0.25 .. N.G. 0.00 cannot hold "
                                       "the printed exterior section): high open",
                                  basis=f"R-T658-3: runs {runs} m x 0.30 x ({annex_top} - {ng}) literal floor"))
            elif bef[0] is not None:
                rows.append(R.row(lid, ic, eid, "BOUNDED", low=bef[0], high=bef[1], before=bef,
                                  flags=["EXISTENCE_OPEN"] if D(str(bef[0])) == 0 else [],
                                  basis=f"UNCHANGED: {src}: {cause[:160]}"))
            else:
                rows.append(R.row(lid, ic, eid, "HELD_BLANK", before=bef, item=f"UNCHANGED: {cause[:200]} ({src})"))
        elif ic == "STR.CONC.COLUMN":
            k = (t572.get(lid) or {}).get("kind")
            if k == "BOUNDED":
                rows.append(R.row(lid, ic, eid, "BOUNDED", low=bef[0], high=bef[1], before=bef,
                                  flags=["SECTION_CONFLICT_D-16_D-66"],
                                  basis="UNCHANGED, R-T658-5: schedule vs drawn outline held as CONFLICT (owner "
                                        "answer: hold, member by member); no third print found (D-66 search)"))
            elif lid in CEILING_SECTIONS:
                sec, lab = CEILING_SECTIONS[lid]
                annex = "annex" in lab
                base, mark = (annex_top, ANNEX_ROOF_MARK) if annex else (s2f, MAIN_ROOF_MARK)
                ceil = R.column_ceiling(D(sec), base, mark)
                rows.append(R.row(lid, ic, eid, "UPPER_ONLY", high=ceil, before=bef,
                                  item=("Q-54 B / D-39 annex roof slab-top datum" if annex else
                                        "D-39 main roof slab-top datum and build-up") + ": low blank",
                                  basis=f"R-T658-4: {lab} {sec} m2 x ({mark} finished mark, printed and re-read r2 - {base} base, "
                                        "APPROVED structural datum, not printed text: READS R2_MARKS_REREAD) ceiling"))
            else:
                hi_item = (t572.get(lid) or {}).get("high_item") or cause
                rows.append(R.row(lid, ic, eid, "HELD_BLANK", before=bef,
                                  item=f"UNCHANGED (R-T658-4 refuses a ceiling): {hi_item}"))
        else:   # straps and footing: drawn bounds already carried (T-572 / R-T595-2), Q-74 checked
            rows.append(R.row(lid, ic, eid, "BOUNDED", low=bef[0], high=bef[1], before=bef,
                              flags=["EXISTENCE_OPEN"] if D(str(bef[0])) == 0 else [],
                              basis=f"UNCHANGED: {src}: {cause[:200]}"))
    assert len(rows) == 61 and len({r["line_id"] for r in rows}) == 61
    findings = [
        {"id": "F-T658-1", "what": "8 short ground-beam spans (0.789 .. 2.1 m) are carried as points at the 30x30 "
                                   "end while the 'less than 5m' 30x40 title also holds (D-34, DG-a31a0d7e audit "
                                   "range): restated 30x30 .. 30x40"},
        {"id": "F-T658-2", "what": "r2 (D-33 ruling): every run carrying a landing beam is LOWER_ONLY, low = drawn "
                                   "area x the least title that holds, high not established: BAND0010.3 (5.00 m "
                                   "ON_LIMIT, point 0.9 -> floor 0.6), BAND0008.1, BAND0008.2, BAND0040, the two "
                                   "T-430 landing runs (blank -> floor 0.4230 each) and, by the same census tee, "
                                   "BAND0037.1 (182+183 lands) and BAND0019 (141+7DA lands)"},
        {"id": "F-T658-3", "what": "L-e24946df: the T-430 register holds 0.5964 .. 0.9036 that the candidate line "
                                   "does not carry (blank): r2 carries the 0.5964 floor (4.97 m reading x 30x40) "
                                   "LOWER_ONLY under D-33"},
        {"id": "F-T658-4", "what": "8 annex exterior ground beams: the literal +0.25 .. N.G. reading is a floor "
                                   "(R-T658-3), carried LOWER_ONLY; high stays D-35"},
        {"id": "F-T658-5", "what": "r2 (Checker r1 defect e): an oblique band measured on its short edge understates "
                                   "its plan area; 4 runs are not rectangles: BAND0038 (45 deg; edge 181 drawn open "
                                   "0.078 m short of face 180D: two outline readings 0.310134 / 0.326694 m2), "
                                   "BAND0039 (0.653733 m2, the corner piece between faces 7C8 / 7C3 owned once, "
                                   "0.021280 m2), BAND0037.1 (0.807695 m2, column 1EF netted), BAND0008.2 (ends "
                                   "on the curved band's outer face R 2.55: 0.492189 m2); every other run of the 61 "
                                   "is orthogonal (drawn area = span x 0.30, 7 controls measured) or an annex arc "
                                   "carried on its centreline (exact for an annulus)"},
        {"id": "F-T658-6", "what": "r2 column marks re-read from the drawings: +13.90 / +4.30 AGREE; the bases "
                                   "+9.65 / +0.25 are APPROVED datums, not printed text (the sets print finished "
                                   "+9.70 / +0.30): ceilings kept, provenance stated"},
    ]
    return {"schema": "T658_LEDGER_V1", "candidate": "ARCH_TAKEOFF_V3.0.61 / trial BOQ r4 (T-654); NOT RELEASED, "
            "nothing wired", "pins": {p.name: h for p, h in PINS.items()}, "reads": READS, "rows": rows,
            "totals": R.totals(rows), "findings": findings}


def main() -> None:
    out = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out["totals"], indent=1))


if __name__ == "__main__":
    main()
