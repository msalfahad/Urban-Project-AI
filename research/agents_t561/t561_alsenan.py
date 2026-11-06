"""T-561 development-villa build: internal and external WALL PAINT vs the freelancer by face class on the candidate of
record (V3.0.58 = the V3.0.57 paint lines). Writes out/T561_PAINT_RECONCILE.json; --check rebuilds it byte-identical.
Run: python3 -I research/agents_t561/t561_alsenan.py [--check]. Reads only repository files (sha256-pinned)."""
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
sys.path.insert(1, str(ROOT / "research" / "agents_t552"))
import t561_inputs as I  # noqa: E402
import t561_paint_rules as R  # noqa: E402
import t552_inputs as I2  # noqa: E402

OUT = HERE / "out" / "T561_PAINT_RECONCILE.json"
PINS = {I.LINE_INDEX: "fed5141ea31bfdd9", "research/agents_t128/ROOMS_T128_R3.csv": "696333bc12f0acb9",
        "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json": "752c9f4e0c4546d0",
        "research/agents_t552/t552_inputs.py": "d15d1425eed8cb16",
        "research/agents_t552/out/T552_PLASTER_RECONCILE.json": "706ff9fde046462b",
        "research/agents_t281/summary.json": "8cce8bfc55b4c1a0"}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.PaintError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def T(x):
    return Decimal(str(x))


def line_index():
    return json.loads((ROOT / I.LINE_INDEX).read_text())["lines"]


def his_cells(file):
    """his statement sheet rows (the first sheet of the file) as {row: {col: value}}; floats read at 6 dp."""
    d = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text())
    sheet, out = None, {}
    for x in d["rows"]:
        if x["file"] != file:
            continue
        sheet = sheet or x["sheet"]
        if x["sheet"] == sheet:
            out[x["row"]] = {k[0:len(k) - len(str(x["row"]))]: (repr(round(v["v"], 6)) if isinstance(v["v"], float)
                                                                   else v["v"]) for k, v in x["cells"].items()}
    return out


def invoice_cells(file):
    d = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text())
    sheets = []
    for x in d["rows"]:
        if x["file"] == file and x["sheet"] not in sheets:
            sheets.append(x["sheet"])
    out = {}
    for x in d["rows"]:
        if x["file"] == file and x["sheet"] == sheets[-1]:
            out[x["row"]] = {k[0:len(k) - len(str(x["row"]))]: v["v"] for k, v in x["cells"].items()}
    return out


def by_element(lines, item):
    return {ln["element_id"]: ln for ln in lines if ln["item_code"] == item}


def dry_pair(lines, his, t128):
    paint = by_element(lines, "FIN.PAINT")
    plaster = {ln["line_id"][:10]: ln for ln in lines if ln["item_code"] == "FIN.PLASTER"}
    comps, valued, rooms, his_total = [], [], [], Decimal(0)
    for key, desc, (plid, state, val), face, h_own, prow, beams, prov in I2.DRY:
        ln = paint[f"HL:WALL_FINISH:{I.PAINT_ELEMENT[key]}:PAINT"]
        pl = plaster[plid]
        assert ln["class"] == state == pl["class"], (key, ln["class"])
        assert (ln["measured_net"], ln["held_low"], ln["held_high"]) == (pl["measured_net"], pl["held_low"],
                                                                         pl["held_high"]), key
        rows = [(I.ROW_MAP[r], L, H) for r, L, H in prow]
        f, ho = T(face), T(h_own)
        g = f * ho
        his_r = Decimal(0)
        for r, L, H in rows:
            assert T(his[r]["H"]) == T(L) and T(his[r]["F"]) == T(H), (r, his[r])
            his_r += T(L) * T(H)
        his_total += his_r
        h_his = T(rows[0][2])
        ht = f * (h_his - ho)
        ln_term = his_r - f * h_his
        if state == "RELEASED":
            assert T(ln["measured_net"]) == T(val)
            valued.append({"line_id": ln["line_id"], "cls": "DRY", "qty": val, "unit": "m2"})
            comps.append({"name": f"{key} opening deductions (engine gross {g} - line net {val}; Q-73 full, each "
                          "opening by its own area inside the paint height)", "qty": str(g - T(val)), "sign": 1,
                          "cause": "RULE_DIFFERENCE", "source": f"{ln['line_id'][:10]} + {I.T128}",
                          "note": "in his gross; he deducts half of his own opening list at his net step"})
            net = val
        else:
            if val is not None:
                net = [str(ln["held_low"]), str(ln["held_high"])]
            else:
                assert ln["held_low"] is None
                net = {"bound": list(prov[0]), "source": prov[1]}
            comps.append({"name": f"{key} HELD paint line at its engine-basis gross face {face} x {h_own}",
                          "qty": str(g), "sign": 1, "cause": "HELD", "source": f"{ln['line_id'][:10]} ({state}) + "
                          f"{I.T128}", "note": f"net {net}; opening heights / annex datum not established"})
        if ht:
            comps.append({"name": f"{key} height: his {h_his} vs the owner G1 paint height {h_own} on face {face}",
                          "qty": str(abs(ht)), "sign": 1 if ht > 0 else -1, "cause": "RULE_DIFFERENCE",
                          "source": f"{I.T128}; owner Q-48 A (G1 = finished-ceiling formula, the paint height)"})
        if ln_term:
            comps.append({"name": f"{key} length: his rows vs the drawn face {face} lm (at his height)",
                          "qty": str(abs(ln_term)), "sign": 1 if ln_term > 0 else -1, "cause": "ENGINE_RIGHT",
                          "source": f"{I.T128} (two independent traces, T-106 / T-250 faces)"})
        t = t128[key]
        rooms.append({"room": key, "what": desc, "paint_line_id": ln["line_id"], "plaster_line_id": pl["line_id"],
                      "state": state, "net": net, "face_lm": face,
                      "owner_method": {"height": h_own, "gross": str(g), "basis": "owner G1 (Q-48 A), PROVISIONAL "
                                       "under Q-52 C (finished ceiling not printed, O-P8-02)"},
                      "drawing_derived": {"height": t["DWG_PAINT_TILE_H_M"], "gross": t["DWG_GROSS_M2"],
                                          "net": t["DWG_NET_M2"], "status": t["DWG_STATUS"],
                                          "basis": "interval - slab 0.16 - b 0 .. 0.10 - decor 0.15: a decor ceiling "
                                                   "hung 0.15 under the slab (upper bound where a beam drops it)"},
                      "his_rows": [r for r, _l, _h in rows], "his_gross": str(his_r), "crossing_beams": beams})
    for key, desc, face, prow, why in I2.WET_IN_HIS_DRY:
        rows = [(I.ROW_MAP[r], L, H) for r, L, H in prow]
        his_r = Decimal(0)
        for r, L, H in rows:
            assert T(his[r]["H"]) == T(L) and T(his[r]["F"]) == T(H), r
            his_r += T(L) * T(H)
        his_total += his_r
        h_his = T(rows[0][2])
        comps.append({"name": f"{key} wet space in his paint rows: drawn face {face} x his {h_his} (he also tiles it: "
                      "his ceramic sheet row 51, T-547)", "qty": str(T(face) * h_his), "sign": 1,
                      "cause": "RULE_DIFFERENCE", "source": f"{I.T128}; UP-FIN-PAINT-001 (no paint over full-height "
                      f"porcelain); owner wet-area rule 2026-11-02; {why}"})
        lt = his_r - T(face) * h_his
        comps.append({"name": f"{key} length: his row vs the drawn face {face}", "qty": str(abs(lt)),
                      "sign": 1 if lt > 0 else -1, "cause": "ENGINE_RIGHT", "source": I.T128})
        rooms.append({"room": key, "what": desc, "paint_line_id": None, "state": "WET (porcelain full height, no paint)",
                      "face_lm": face, "his_rows": [r for r, _l, _h in rows], "his_gross": str(his_r)})
    b = R.bridge(pair_class="DRY", freelancer_gross=his_total, engine_lines=valued, components=comps,
                 residual_name="DRY RESIDUAL")
    b["rooms"] = rooms
    b["two_methods"] = two_methods(rooms)
    return b


def _rng(s):
    a = s.split(" .. ")
    return T(a[0]), T(a[-1])


def two_methods(rooms):
    """ERS s.2.2: the owner G1 column and the drawing-derived column side by side over the 11 dry paint lines."""
    og, dg, rel = Decimal(0), [Decimal(0), Decimal(0)], []
    for r in rooms:
        if "owner_method" not in r:
            continue
        og += T(r["owner_method"]["gross"])
        lo, hi = _rng(r["drawing_derived"]["gross"])
        dg[0] += lo
        dg[1] += hi
        if r["state"] == "RELEASED":
            nlo, nhi = _rng(r["drawing_derived"]["net"])
            rel.append({"room": r["room"], "line_id": r["paint_line_id"], "released_net_owner_method": r["net"],
                        "drawing_derived_net": [str(nlo), str(nhi)],
                        "difference": [str(nlo - T(r["net"])), str(nhi - T(r["net"]))]})
    return {"owner_G1_gross_11_lines": str(og), "drawing_derived_gross_11_lines": [str(dg[0]), str(dg[1])],
            "difference": [str(dg[0] - og), str(dg[1] - og)], "released_lines": rel,
            "status": "the 4 released paint lines rest on the owner G1 formula (Q-48 A), which Q-52 C calls an "
                      "approximation that never overrides the drawings; the finished-ceiling level is printed nowhere "
                      "(no reflected ceiling plan, O-P8-02), so the drawing-derived column (decor hung 0.15 under the "
                      "slab) is an UPPER bound, lowered where a crossing beam sets the ceiling or a bulkhead forms; "
                      "label the released lines PROVISIONAL (ASSUMED - OWNER-APPROVED, Q-48 A) until the designer "
                      "prints the ceiling level: a designer item, not an owner question (ERS s.2.7)"}


def shaft_pair(lines, his):
    paint = by_element(lines, "FIN.PAINT")
    his_total = Decimal(0)
    for r, L, H in I2.SHAFT_HIS_ROWS:
        pr = I.ROW_MAP[r]
        assert T(his[pr]["H"]) == T(L) and T(his[pr]["F"]) == T(H), pr
        his_total += T(L) * T(H)
    notes = []
    for k in I.SHAFT_PAINT_LINES:
        ln = paint[f"HL:WALL_FINISH:{k}:PAINT"]
        assert ln["class"] == "HELD"
        notes.append({"line_id": ln["line_id"], "element": k,
                      "candidate_bound": None if ln["held_low"] is None else [str(ln["held_low"]), str(ln["held_high"])]})
    comps = [{"name": "shaft faces, drawing-derived PAINT gross (3 HELD candidate lines; T-173 actual exposed geometry, "
                      "Q-72 full height to the decor line under the roof)", "qty": I.SHAFT_PAINT_GROSS_HI, "sign": 1,
              "cause": "HELD", "source": I.T173,
              "note": f"gross {I.SHAFT_PAINT_GROSS_LO} .. {I.SHAFT_PAINT_GROSS_HI} (b 0.10 .. 0); net "
                      f"{I.SHAFT_PAINT_NET[0]} .. {I.SHAFT_PAINT_NET[1]} (held items undeducted), "
                      f"{I.SHAFT_PAINT_NET_LO_ALL_HELD} with every held item deducted; the candidate lines still carry "
                      "the T-128 r2 storey-interval nets (restate on T-173 at integration)"}]
    comps += [{"name": n, "qty": q, "sign": s, "cause": c, "source": src} for n, q, s, c, src in I.SHAFT_COMPONENTS]
    b = R.bridge(pair_class="SHAFT", freelancer_gross=his_total, engine_lines=[], components=comps,
                 residual_name="SHAFT RESIDUAL: " + I.SHAFT_RESIDUAL)
    b["candidate_lines"] = notes
    return b


def return_pair(lines, his):
    r, n, w, L = I.RETURN_HIS
    assert (T(his[r]["E"]), T(his[r]["F"]), T(his[r]["H"])) == (T(n), T(w), T(L))
    paint_returns = [ln for ln in lines if ln["item_code"] == "FIN.PAINT" and
                     ("OPENING" in ln["element_id"] or "REVEAL" in ln["element_id"])]
    assert not paint_returns, "a paint return line exists: restate the RETURN pair"
    plaster_returns = [ln for ln in lines if ln["item_code"] == "FIN.PLASTER" and
                       ("OPENING" in ln["element_id"] or "REVEAL" in ln["element_id"])]
    faces = sum((T(ln["measured_net"]) for ln in plaster_returns if ln["measured_net"] is not None), Decimal(0))
    nval = sum(1 for ln in plaster_returns if ln["measured_net"] is not None)
    outside = [{"line_id": ln["line_id"], "qty": None, "why": f"plaster return {ln['class']} {ln['element_id']} blank"}
               for ln in plaster_returns if ln["measured_net"] is None]
    comps = [{"name": f"return faces (jambs + head) of {nval} doors: no FIN.PAINT return line in the candidate "
                      "(ENGINE_OMISSION); the plastered return face of each opening (UP-FIN-PLASTER-001) is the upper "
                      "bound of its painted part", "qty": str(faces), "sign": 1, "cause": "HELD",
              "source": f"{nval} valued FIN.PLASTER OPENING lines (2 x t x door height + t x width, PROVISIONAL)",
              "note": "painted part = return face - the depth the frame / architrave covers (frame detail not "
                      "printed): HELD, bounded above by this figure, never 0"}]
    b = R.bridge(pair_class="RETURN", freelancer_gross=T(n) * T(w) * T(L), engine_lines=[], components=comps,
                 residual_name=(f"RETURN RESIDUAL: door count / size: {nval} openings by id (T-292) against his {n} "
                                f"doors x {w} x {L}; his doors are not listed by id"), outside=outside)
    b["engine_omission"] = ("no FIN.PAINT line for door returns although every return is plastered and its exposed "
                            "part is painted; proposed at integration: FIN.PAINT return lines from the plaster return "
                            "geometry, HELD until the frame detail sets the covered depth")
    return b


def soffit_pair(lines, his):
    stair = by_element(lines, "FIN.STAIR.SOFFIT")
    t281 = json.loads((ROOT / "research/agents_t281/summary.json").read_text())["totals"]
    his_total, comps, notes = Decimal(0), [], []
    for r, w, L, what, sid, true_d, lid in I.SOFFIT_ROWS:
        assert T(his[r]["G"]) == T(w) and T(his[r]["H"]) == T(L), r
        assert T(repr(t281[sid]["true_D_measured"])) == T(true_d), sid
        his_total += T(w) * T(L)
        ln = stair[f"STAIR:{sid}:soffit"]
        assert ln["line_id"].startswith(lid) and ln["class"] == "HELD" and ln["held_low"] is None
        comps.append({"name": f"his row {r} ({what}, {w} x {L}): {sid} soffit, T-281 measured true area (method D)",
                      "qty": true_d, "sign": 1, "cause": "HELD", "source": f"{ln['line_id'][:10]} (HELD blank) + "
                      f"{I.T281}", "face_class": "CEILING"})
        notes.append({"his_row": r, "stair": sid, "candidate_line": ln["line_id"], "candidate": "HELD blank"})
    b = R.bridge(pair_class="CEILING", freelancer_gross=his_total, engine_lines=[], components=comps,
                 residual_name="SOFFIT RESIDUAL: his widths x lengths vs the T-281 rows, plus the T-281 rows still "
                               "HELD (ST-01 two rows 1.50 m2 plan; ST-02 RS-C curved flight 4.443156 m2 plan, helicoid "
                               "not drawn); his row-to-stair reading from his labels")
    b["candidate_lines"] = notes
    b["why_not_wall_paint"] = ("a flight / landing underside is a soffit: CEILING class (Q-57; FIN.STAIR.SOFFIT, "
                               "arch_v3032); he prices it inside his wall-paint total (rows 18-19, not in his plaster "
                               "sheet), so it is split out here and never enters a wall pair")
    return b


def external(lines, his):
    ext_rows = [r for r, c in his.items() if any(isinstance(v, str) and "خارج" in v for v in c.values())]
    held = []
    for code in ("FIN.EXT.FINISH", "ARCH.FACADE", "EXT.FENCE.PAINT"):
        for ln in lines:
            if ln["item_code"] == code:
                assert ln["measured_net"] is None, ln["line_id"]
                held.append({"line_id": ln["line_id"], "item": code, "class": ln["class"], "element": ln["element_id"]})
    return {"freelancer_paint_workbook_external_m2": "0", "engine_valued_m2": "0", "gap": "0",
            "his_rows_labelled_external_in_paint_sheet": ext_rows,
            "note": "his paint workbook prices no exterior face (his row 29 'windows external spaces' is an opening "
                    "of his internal list). His exterior coating (Sigma) is measured as his exterior plaster area in "
                    "the plaster workbook (OWNER_NOTES_SIGMA_2026-10-21: 1,502.84 gross / 1,469.97 net), reconciled "
                    "once by T-552 s.4 / T-567, never again here. Every candidate exterior finish line is HELD blank "
                    "(T-314 QUEUED); boundary-wall paint EXT.FENCE.PAINT is another trade (Q-65 C).",
            "held_lines": held}


def ceiling_listing(lines, inv):
    v = [ln for ln in lines if ln["item_code"] == "FIN.PAINT.CEILING"]
    tot = sum((T(ln["measured_net"]) for ln in v if ln["measured_net"] is not None), Decimal(0))
    return {"freelancer_decor_paint_m2": I.FREELANCER_DECOR, "candidate_FIN_PAINT_CEILING_lines": len(v),
            "candidate_valued_m2": str(tot), "reconciled_here": False,
            "note": "ceiling paint (decor ceilings, cove strips) is a CEILING item (Q-57 A modified); listed beside so "
                    "no ceiling face enters the wall pairs; its reconciliation belongs to the ceiling family"}


def plaster_vs_paint(lines):
    q = json.loads((ROOT / "research/agents_t552/out/T552_PLASTER_RECONCILE.json").read_text())
    rows = []
    for r in q["q72_dry_plaster_height"]["rows"]:
        rows.append({"room": r["room"], "plaster_line_id": r["line_id"],
                     "plaster_height": {"basis": "slab / roof underside (owner 2026-11-02, Q-72; T-552 / T-556)",
                                        "m": r["plaster_height"], "corrected_net": r["corrected_net"]},
                     "paint_height": {"basis": "finished ceiling: owner G1 (Q-48 A), drawing-derived beside",
                                      "m": r["line_height_basis"].split()[2]},
                     "today": "FIN.PLASTER = FIN.PAINT per room (one height in the code path)"})
    return {"register": "WALL PLASTER HEIGHT vs PAINT HEIGHT", "rows": rows,
            "finding": "the paint lines carry the right basis (finished ceiling); the plaster lines do not (T-552 "
                       "ENGINE_WRONG). Restating plaster must not move paint: the two heights stay separate fields."}


def build():
    pins()
    lines = line_index()
    his = his_cells("PNT")
    inv = invoice_cells("PNT")
    assert T(his[28]["J"]) == T(I.FREELANCER_GROSS) and T(his[45]["J"]) == T(I.FREELANCER_OPENING_LIST)
    assert T(his[51]["J"]) == T(I.FREELANCER_DECOR)
    assert T(repr(inv[16]["F"])) == T(I.FREELANCER_NET) and T(repr(inv[22]["F"])) == T(I.FREELANCER_INVOICE_TOTAL)
    assert T(I.FREELANCER_GROSS) - T(I.FREELANCER_OPENING_LIST) / 2 == T(I.FREELANCER_NET)
    assert T(I.FREELANCER_NET) + T(I.FREELANCER_DECOR) == T(I.FREELANCER_INVOICE_TOTAL)
    for r in range(29, 46):  # his paint opening list = his plaster opening list, cell by cell
        pls = his_cells("PLS")
        if r in his and "I" in his[r]:
            assert T(his[r]["I"]) == T(pls[r]["I"]), r
    pls = his_cells("PLS")
    plaster_same = all(T(his[pr][c]) == T(pls[r][c]) for r, pr in I.ROW_MAP.items() for c in ("F", "H")
                       if c in pls[r])
    assert plaster_same
    t128 = {r["ROW"]: r for r in csv.DictReader((ROOT / "research/agents_t128/ROOMS_T128_R3.csv").open())}
    dry, sh, rt, so = dry_pair(lines, his, t128), shaft_pair(lines, his), return_pair(lines, his), soffit_pair(lines, his)
    tot = sum((T(x["freelancer_gross"]) for x in (dry, sh, rt, so)), Decimal(0))
    assert tot == T(I.FREELANCER_GROSS), tot
    eng = sum((T(x["engine_valued"]) for x in (dry, sh, rt, so)), Decimal(0))
    paint = [ln for ln in lines if ln["item_code"] == "FIN.PAINT"]
    valued = sum((T(ln["measured_net"]) for ln in paint if ln["measured_net"] is not None), Decimal(0))
    assert valued == eng
    census = {}
    for ln in paint:
        k = ("SHAFT" if ":ST_" in ln["element_id"] else "DRY room line" if ln["element_id"].startswith("HL:WALL_FINISH")
             and ln["class"] != "EXCLUDED" else "EXCLUDED (" + ("wet: paint above wall tile, none under full-height "
                                                                "porcelain" if "above wall tile" in ln["element_id"]
                                                                else "superseded route room line") + ")")
        c = census.setdefault(k, {"lines": 0, "valued_m2": "0", "held_lines": 0})
        c["lines"] += 1
        if ln["measured_net"] is not None:
            c["valued_m2"] = str(T(c["valued_m2"]) + T(ln["measured_net"]))
        elif ln["class"] == "HELD":
            c["held_lines"] += 1
    t552 = json.loads((ROOT / "research/agents_t552/out/T552_PLASTER_RECONCILE.json").read_text())
    pdry = t552["internal"]["pairs"]["DRY"]
    cross = {"paint_minus_plaster_his_gross": str(tot - T(t552["internal"]["freelancer_gross"])),
             "equals_his_soffit_rows": str(T(so["freelancer_gross"])),
             "dry_pair_identical_to_T552": dry["by_cause"] == pdry["by_cause"] and dry["gap"] == pdry["gap"]}
    assert T(cross["paint_minus_plaster_his_gross"]) == T(so["freelancer_gross"]) and cross["dry_pair_identical_to_T552"]
    by = {}
    for x in (dry, sh, rt, so):
        for k, v in x["by_cause"].items():
            by[k] = str(T(by.get(k, "0")) + T(v))
    assert sum((T(v) for v in by.values()), Decimal(0)) == tot - eng
    return {
        "schema": "URBAN_T561_PAINT_RECONCILE_V1", "candidate": "ARCH_TAKEOFF_V3.0.58 (V3.0.57 paint lines)",
        "inputs_sha256_16": PINS, "census_FIN_PAINT": census, "candidate_valued_FIN_PAINT_m2": str(valued),
        "internal": {"freelancer_gross": I.FREELANCER_GROSS, "freelancer_net": I.FREELANCER_NET,
                     "his_half_deduction": str(T(I.FREELANCER_OPENING_LIST) / 2), "engine_valued": str(eng),
                     "gap_gross": str(tot - eng), "gap_net": str(T(I.FREELANCER_NET) - eng), "by_cause": by,
                     "pairs": {"DRY": dry, "SHAFT": sh, "RETURN": rt, "CEILING (stair soffits in his wall paint)": so}},
        "cross_check_T552": cross,
        "external": external(lines, his),
        "ceiling_paint_beside": ceiling_listing(lines, inv),
        "plaster_vs_paint_height": plaster_vs_paint(lines),
        "coats": "his paint rows carry no coats factor (area only); coats are a rate in the price build-up, never an "
                 "area multiplier (R-T561-1 c)",
    }


def main(argv):
    txt = json.dumps(build(), indent=1, ensure_ascii=True, sort_keys=True) + "\n"
    if "--check" in argv:
        if OUT.read_text() != txt:
            print("T561 output differs")
            return 1
        print("T561 output byte-identical")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt)
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
