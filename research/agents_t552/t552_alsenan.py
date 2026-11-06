"""T-552 development-villa build: wall plaster (internal + external) vs the freelancer by face class on the candidate
of record (V3.0.58 = the V3.0.57 plaster lines). Writes out/T552_PLASTER_RECONCILE.json; --check rebuilds it
byte-identical. Run: python3 -I research/agents_t552/t552_alsenan.py [--check]. Reads only repository files."""
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
import t552_inputs as I  # noqa: E402
import t552_plaster_rules as R  # noqa: E402

OUT = HERE / "out" / "T552_PLASTER_RECONCILE.json"
PINS = {I.LINE_INDEX: "fed5141ea31bfdd9", "research/agents_t128/ROOMS_T128_R3.csv": "696333bc12f0acb9",
        "research/agents_t337/FREELANCER_T337.csv": "0f7d962798425b8a",
        "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json": "752c9f4e0c4546d0"}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.PlasterError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def plaster_lines():
    d = json.loads((ROOT / I.LINE_INDEX).read_text())
    return [ln for ln in d["lines"] if ln["item_code"] == "FIN.PLASTER"]


def his_cells():
    """his statement rows (file PLS, sheet 1) as {row: {col: value}}; a float cell is read at 6 dp (the workbook's
    binary sums, e.g. 1502.8399999999997 -> 1502.84); only numbers are used."""
    d = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text())
    sheet = None
    out = {}
    for x in d["rows"]:
        if x["file"] != "PLS":
            continue
        sheet = sheet or x["sheet"]
        if x["sheet"] == sheet:
            out[x["row"]] = {k[0:len(k) - len(str(x["row"]))]: (repr(round(v["v"], 6)) if isinstance(v["v"], float)
                                                                   else v["v"]) for k, v in x["cells"].items()}
    return out


def classify(ln):
    e = ln["element_id"]
    if "OPENING" in e or "REVEAL" in e:
        return "RETURN"
    if e.startswith("HL:WALL_FINISH:ST_"):
        return "SHAFT"
    return None


def T(x):
    return Decimal(str(x))


def dry_pair(lines, his):
    by_id = {ln["line_id"][:10]: ln for ln in lines}
    comps, valued, room_rows, his_total = [], [], [], Decimal(0)
    for key, desc, (lid, state, val), face, h_own, rows, beams, prov in I.DRY:
        ln = by_id[lid]
        assert ln["class"] == state, (lid, ln["class"])
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
                          "opening by its own area per room side)", "qty": str(g - T(val)), "sign": 1,
                          "cause": "RULE_DIFFERENCE", "source": f"{lid} + {I.T128}",
                          "note": "in his gross; he deducts half of his own opening list at his net step"})
            net = val
        else:
            if val is not None:
                assert (T(ln["held_low"]), T(ln["held_high"])) == (T(val[0]), T(val[1])), lid
                net = list(val)
            else:
                assert ln["held_low"] is None
                net = {"bound": list(prov[0]), "source": prov[1]}
            comps.append({"name": f"{key} HELD line at its engine-basis gross face {face} x {h_own}", "qty": str(g),
                          "sign": 1, "cause": "HELD", "source": f"{lid} ({state}) + {I.T128}",
                          "note": f"net {net}; opening heights / annex datum not established"})
        if ht:
            comps.append({"name": f"{key} height: his {h_his} vs the line's owner G1 {h_own} on face {face}",
                          "qty": str(abs(ht)), "sign": 1 if ht > 0 else -1, "cause": "RULE_DIFFERENCE",
                          "source": f"{I.T128}; owner Q-43 / Q-48 A (G1 = paint height)"})
        if ln_term:
            comps.append({"name": f"{key} length: his rows vs the drawn face {face} lm (at his height)",
                          "qty": str(abs(ln_term)), "sign": 1 if ln_term > 0 else -1, "cause": "ENGINE_RIGHT",
                          "source": f"{I.T128} (two independent traces, T-106 / T-250 faces)"})
        room_rows.append({"room": key, "what": desc, "line_id": ln["line_id"], "state": state, "net": net,
                          "face_lm": face, "owner_h": h_own, "engine_gross": str(g), "his_rows": [r for r, _l, _h in rows],
                          "his_gross": str(his_r), "delta_his_minus_gross": str(his_r - g), "crossing_beams": beams})
    for key, desc, face, rows, why in I.WET_IN_HIS_DRY:
        his_r = sum((T(L) * T(H) for _r, L, H in rows), Decimal(0))
        his_total += his_r
        h_his = T(rows[0][2])
        comps.append({"name": f"{key} wet space in his dry rows: drawn face {face} x his {h_his}",
                      "qty": str(T(face) * h_his), "sign": 1, "cause": "RULE_DIFFERENCE", "source": f"{I.T128}; {why}"})
        lt = his_r - T(face) * h_his
        comps.append({"name": f"{key} length: his row vs the drawn face {face}", "qty": str(abs(lt)),
                      "sign": 1 if lt > 0 else -1, "cause": "ENGINE_RIGHT", "source": I.T128})
        room_rows.append({"room": key, "what": desc, "line_id": None, "state": "WET (render, not dry plaster)",
                          "face_lm": face, "his_rows": [r for r, _l, _h in rows], "his_gross": str(his_r)})
    b = R.bridge(pair_class="DRY", freelancer_gross=his_total, engine_lines=valued, components=comps,
                 residual_name="DRY RESIDUAL")
    b["rooms"] = room_rows
    return b


def shaft_pair(lines, his):
    by_id = {ln["line_id"][:10]: ln for ln in lines}
    his_total = Decimal(0)
    for r, L, H in I.SHAFT_HIS_ROWS:
        assert T(his[r]["H"]) == T(L) and T(his[r]["F"]) == T(H), r
        his_total += T(L) * T(H)
    notes = []
    for lid, name, bound in I.SHAFT_LINES:
        ln = by_id[lid]
        assert ln["class"] == "HELD"
        notes.append({"line_id": ln["line_id"], "element": name,
                      "candidate_bound": None if ln["held_low"] is None else [str(ln["held_low"]), str(ln["held_high"])]})
    comps = [{"name": "shaft faces, drawing-derived plaster gross (3 HELD candidate lines; T-173 actual exposed "
                      "geometry, Q-72 full height)", "qty": I.SHAFT_GROSS_HI, "sign": 1, "cause": "HELD",
              "source": I.T173, "note": f"gross {I.SHAFT_GROSS_LO} .. {I.SHAFT_GROSS_HI} (b 0.10 .. 0); net "
                                        f"{I.SHAFT_NET[0]} .. {I.SHAFT_NET[1]}; the candidate lines still carry the "
                                        "T-128 r2 storey-interval nets (restate on T-173 at integration)"}]
    comps += [{"name": n, "qty": q, "sign": s, "cause": c, "source": I.T173} for n, q, s, c in I.SHAFT_COMPONENTS]
    b = R.bridge(pair_class="SHAFT", freelancer_gross=his_total, engine_lines=[], components=comps,
                 residual_name="SHAFT RESIDUAL: " + I.SHAFT_RESIDUAL)
    b["candidate_lines"] = notes
    return b


def return_pair(lines, his):
    r, n, w, L = I.RETURN_HIS
    assert (T(his[r]["E"]), T(his[r]["F"]), T(his[r]["H"])) == (T(n), T(w), T(L))
    valued, outside = [], []
    for ln in lines:
        if classify(ln) != "RETURN":
            continue
        if ln["measured_net"] is not None:
            valued.append({"line_id": ln["line_id"], "cls": "RETURN", "qty": ln["measured_net"], "unit": "m2"})
        else:
            outside.append({"line_id": ln["line_id"], "qty": None,
                            "why": f"{ln['class']} {ln['element_id']}" + (f" bound {ln['held_low']} .. {ln['held_high']}"
                                                                          if ln["held_low"] is not None else " blank")})
    b = R.bridge(pair_class="RETURN", freelancer_gross=T(n) * T(w) * T(L), engine_lines=valued, components=[],
                 residual_name=(f"RETURN RESIDUAL: door count / size: the engine values {len(valued)} openings by id "
                                "(2 x wall t x head + wall t x width, UP-FIN-PLASTER-001, PROVISIONAL) against his "
                                f"{n} doors x {w} x {L}; his doors are not listed by id"), outside=outside)
    b["valued_lines"] = len(valued)
    return b


def wet_listing(lines):
    wet = [ln for ln in lines if ln["class"] != "EXCLUDED" and classify(ln) is None and
           (ln["element_id"].endswith(":plaster") or ln["element_id"].endswith("GF_07:PLASTER"))]
    return {"lines": len(wet), "valued_m2": str(sum((T(ln["measured_net"]) for ln in wet
                                                     if ln["measured_net"] is not None), Decimal(0))),
            "held_blank": sum(1 for ln in wet if ln["measured_net"] is None),
            "note": "wet-room FIN.PLASTER backing lines = the levelling render (tiler), T-331 / T-454; their faces are "
                    "the wall-tile faces of T-547 (tile) and T-317 / T-349 (spatter); never in a DRY pair",
            "freelancer_spatter_wet_m2": I.FREELANCER_WET_SPATTER}


def ext_pair():
    rows = list(csv.DictReader((ROOT / "research/agents_t337/FREELANCER_T337.csv").open()))
    out = {}
    for pas in ("lo", "hi"):
        comps, his_total, resid_rows = [], Decimal(0), []
        for x in rows:
            m, st = T(x["his_m2"]), x["t162_status"]
            his_total += m
            dw = x["drawing_m2"].strip()
            src = "T-337 FREELANCER_T337.csv row " + x["his_rows"]
            if dw:
                lo, hi = (dw.split(" .. ") + [dw])[:2] if " .. " in dw else (dw, dw)
                v = T(lo if pas == "lo" else hi)
                comps.append({"name": f"his row {x['his_rows']}: drawn faces ({x['owner_lines_here'][:60]})",
                              "qty": str(v), "sign": 1, "cause": "HELD", "source": src,
                              "note": "measured faces, not in the candidate (FIN.EXT.FINISH / ARCH.FACADE HELD, T-314)"})
                dd = m - v
                if dd:
                    comps.append({"name": f"his row {x['his_rows']} vs the drawn faces", "qty": str(abs(dd)),
                                  "sign": 1 if dd > 0 else -1, "cause": I.EXT_CAUSE[st], "source": src + " / T-159"})
            elif st in I.EXT_SCOPE:
                c, s = I.EXT_SCOPE[st]
                comps.append({"name": f"his row {x['his_rows']} ({st}): no wall face drawn", "qty": str(m), "sign": 1,
                              "cause": c, "source": s, "his_scope_row": True})
            elif st.startswith("ACCEPTED"):
                r_, lid, q, why = I.POOL_SOFFIT
                comps.append({"name": "his row 73 pool-court soffit: the engine's CEILING line", "qty": q, "sign": 1,
                              "cause": "RULE_DIFFERENCE", "source": f"{lid}; {why}"})
                comps.append({"name": "his row 73 (2 x 3.14 x 3.05) vs the measured soffit", "qty": str(m - T(q)),
                              "sign": 1, "cause": "ENGINE_RIGHT", "source": why})
            else:
                resid_rows.append(x["his_rows"])
        assert his_total == T(I.FREELANCER_EXTERNAL_GROSS)
        out[pas] = R.bridge(pair_class="EXTERNAL", freelancer_gross=his_total, engine_lines=[], components=comps,
                            residual_name="EXTERNAL RESIDUAL: his rows " + ", ".join(resid_rows) +
                            " match no drawn face (T-337 UNRESOLVED: possible double counts of the 1F set-back ends "
                            "and the 2F sea face)")
    return out


def q72_correction(lines):
    """ENGINE_WRONG under the owner rule of 2 Nov (Q-72): each dry room line's height basis is the owner G1 room
    formula (= the paint height); plaster runs to the slab / roof underside. Missing m2 = face x (soffit - G1)."""
    by_id = {ln["line_id"][:10]: ln for ln in lines}
    rows, tot = [], [Decimal(0), Decimal(0)]
    for key, desc, (lid, state, val), face, h_own, _rows, beams, prov in I.DRY:
        iv, ivs = I.INTERVALS[I.ZONE[key]]
        lo, hi = R.plaster_height(basis="SLAB_UNDERSIDE" if I.UNDER_ROOF[key] == "0.0" else "ROOF_UNDERSIDE"
                                  if I.UNDER_ROOF[key] == "1.0" else "SLAB_UNDERSIDE", interval=iv, slab=I.SLAB[0],
                                  buildup=tuple(I.BUILDUP[0]),
                                  sources={"interval": ivs, "slab": I.SLAB[1], "buildup": I.BUILDUP[1]})
        add = (T(face) * (lo - T(h_own)), T(face) * (hi - T(h_own)))
        tot[0] += add[0]
        tot[1] += add[1]
        ln = by_id[lid]
        if state == "RELEASED":
            cur = (T(val), T(val))
        elif val is not None:
            cur = (T(val[0]), T(val[1]))
        else:
            cur = tuple(T(x) for x in prov[0])
        rows.append({"room": key, "line_id": ln["line_id"], "state": state, "face_lm": face,
                     "line_height_basis": f"owner G1 {h_own} (= paint height)",
                     "plaster_height": [str(lo), str(hi)], "interval": iv, "missing_m2": [str(add[0]), str(add[1])],
                     "corrected_net": [str(cur[0] + add[0]), str(cur[1] + add[1])],
                     "status": "HELD (BOUNDED): build-up b not printed" +
                               ("; PROVISIONAL-DATUM (under a roof, share " + I.UNDER_ROOF[key] + ")"
                                if I.UNDER_ROOF[key] != "0.0" else ""),
                     "beam_end_sections_held": beams})
    return {"verdict": "ENGINE_WRONG (candidate plaster at the paint height after the 2 Nov owner rule)",
            "rule": "plaster to the underside of the structural slab / roof (owner 2026-11-02, Q-72; rulebook "
                    "'Plaster and paint heights')", "rows": rows, "missing_total": [str(tot[0]), str(tot[1])],
            "beam_ends": "a crossing beam framing into a wall above the G1 height removes its end section (width x "
                         "depth below the slab) from the wall face; widths not in this table: HELD per beam end; its "
                         "sides and soffit are CEILING items (Q-57)"}


def build():
    pins()
    lines = plaster_lines()
    his = his_cells()
    assert T(his[27]["J"]) == T(I.FREELANCER_INTERNAL_GROSS) and T(his[93]["J"]) == T(I.FREELANCER_EXTERNAL_GROSS)
    assert T(his[45]["J"]) == T(I.FREELANCER_OPENING_LIST) and T(his[97]["J"]) == T(I.FREELANCER_EXTERNAL_OPENINGS)
    dry, sh, rt = dry_pair(lines, his), shaft_pair(lines, his), return_pair(lines, his)
    internal_his = T(dry["freelancer_gross"]) + T(sh["freelancer_gross"]) + T(rt["freelancer_gross"])
    assert internal_his == T(I.FREELANCER_INTERNAL_GROSS), internal_his
    half = T(I.FREELANCER_OPENING_LIST) / 2
    assert T(I.FREELANCER_INTERNAL_GROSS) - half == T(I.FREELANCER_INTERNAL_NET)
    eng_int = T(dry["engine_valued"]) + T(rt["engine_valued"])
    ext = ext_pair()
    ehalf = T(I.FREELANCER_EXTERNAL_OPENINGS) / 2
    assert T(I.FREELANCER_EXTERNAL_GROSS) - ehalf == T(I.FREELANCER_EXTERNAL_NET)
    counted = {r["line_id"] for r in dry["rooms"] if r.get("line_id")} | {x["line_id"] for x in sh["candidate_lines"]}
    census = {}
    for ln in lines:
        k = ("DRY room line" if ln["line_id"] in counted and classify(ln) is None else classify(ln) or
             ("EXCLUDED (superseded route room line)" if ln["class"] == "EXCLUDED" else "WET render line"))
        c = census.setdefault(k, {"lines": 0, "valued_m2": "0", "held_lines": 0})
        c["lines"] += 1
        if ln["measured_net"] is not None:
            c["valued_m2"] = str(T(c["valued_m2"]) + T(ln["measured_net"]))
        elif ln["class"] == "HELD":
            c["held_lines"] += 1
    total_valued = sum((T(ln["measured_net"]) for ln in lines if ln["measured_net"] is not None), Decimal(0))
    assert sum((T(c["valued_m2"]) for c in census.values()), Decimal(0)) == total_valued
    return {
        "schema": "URBAN_T552_PLASTER_RECONCILE_V1", "candidate": "ARCH_TAKEOFF_V3.0.58 (V3.0.57 plaster lines)",
        "inputs_sha256_16": PINS,
        "census_FIN_PLASTER": census, "candidate_valued_FIN_PLASTER_m2": str(total_valued),
        "internal": {"freelancer_gross": I.FREELANCER_INTERNAL_GROSS, "freelancer_net": I.FREELANCER_INTERNAL_NET,
                     "his_half_deduction": str(half), "engine_valued_dry_plus_returns": str(eng_int),
                     "gap_gross": str(internal_his - eng_int),
                     "gap_net": str(T(I.FREELANCER_INTERNAL_NET) - eng_int),
                     "pairs": {"DRY": dry, "SHAFT": sh, "RETURN": rt}, "WET": wet_listing(lines)},
        "external": {"freelancer_gross": I.FREELANCER_EXTERNAL_GROSS, "freelancer_net": I.FREELANCER_EXTERNAL_NET,
                     "his_half_deduction": str(ehalf), "engine_valued": "0", "bridge_lo": ext["lo"],
                     "bridge_hi": ext["hi"]},
        "q72_dry_plaster_height": q72_correction(lines),
    }


def main(argv):
    txt = json.dumps(build(), indent=1, ensure_ascii=True, sort_keys=True) + "\n"
    if "--check" in argv:
        if OUT.read_text() != txt:
            print("T552 output differs")
            return 1
        print("T552 output byte-identical")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt)
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
