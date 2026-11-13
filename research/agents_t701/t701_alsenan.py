"""T-701 development-villa builder: PLASTER / PAINT reference reconciliation on ARCH_TAKEOFF_V3.0.69 (research, unwired).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t687/out/LINE_INDEX_V3_0_69.json   candidate of record V3.0.69 (T-687 Gate B PASS, merge 12bf5b8c)
  research/agents_t556/out/T556_PLASTER_HEIGHT.json  per dry room face lm, gross at the plaster height, deductions
                                                      (T-556 MERGED 655b9eac; wired by T-563, unchanged since)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json his plaster (PLS) and paint (PNT) workbooks as parsed cells
Typed here (cited): the drawn faces of T-128 r3 / T-552 (dry rooms), T-686 annex datum (R-T678-2 bound), T-173 /
T-680 shaft terms, the owner G1 paint heights (Q-48 A). No coordinate, client name or workbook text is stored.

    python3 -I research/agents_t701/t701_alsenan.py           # writes out/T701_RECONCILE.json and .md
    python3 -I research/agents_t701/t701_alsenan.py --check   # rebuilds in memory, compares byte for byte
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
import t701_rules as R  # noqa: E402

INDEX = ROOT / "research/agents_t687/out/LINE_INDEX_V3_0_69.json"
T556 = ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json"
RAW = ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {INDEX: "e908a5f105197d44277c8e1d2a2ef79c67b45681ca874d8c405e85d3b97602f1",
        T556: "8169a1953c386ccab7bbd9283404c100dc9d8105e6c10b7244593c9af442cd84",
        RAW: "752c9f4e0c4546d00ab9707c19dc5c3761187ba56b9e96a674d68a39edf8adea"}
OUT_JSON = HERE / "out" / "T701_RECONCILE.json"
OUT_MD = HERE / "out" / "T701_RECONCILE.md"
D = R.D
q6 = R.q6

# ---- typed, cited inputs -------------------------------------------------------------------------------------------
# DRY rooms: room, element key, drawn face lm (T-128 r3 walked faces; T-634 own re-measure on 4), owner G1 paint
# height (Q-48 A), his plaster rows, his paint rows (his paint rows = his plaster rows 1:1, T-561 ROW_MAP).
DRY = [
    ("GF-01", "GF_01", "20.127", "3.15", [4], [4]),
    ("GF-04", "GF_04", "12.5", "3.15", [5], [5]),
    ("GF-15", "GF_15", "21.537", "3.65", [6], [6]),
    ("GF-08", "GF_08", "53.188", "3.65", [7], [7]),
    ("1F-01", "1F_01", "17.7", "3.35", [11], [11]),
    ("1F-04", "1F_04", "17.4", "3.35", [12], [12]),
    ("1F-10", "1F_10", "16.2", "3.35", [13], [13]),
    ("1F-11", "1F_11", "22.149", "3.35", [14], [14]),
    ("1F-13", "1F_13", "39.45", "3.35", [15, 16], [15, 16]),
    ("2F-03", "2F_03", "18.9", "3.35", [19], [21]),
    ("2F-01", "2F_01", "9.009", "3.35", [20], [22]),
]
# Annex datum (T-686 R-T686-1 on R-T678-2, Checker MERGED f8515d4b): slab top s 3.544 .. 4.30 above the +0.30 FFL;
# plaster soffit S = s - 0.16 - 0.30 = 3.084 .. 3.84; paint / tile top H = s - 1.05 = 2.494 .. 3.25 (Q-54 B: no point).
ANNEX_S = ("3.084", "3.84")
ANNEX_H = ("2.494", "3.25")
ANNEX_PAINT_ROOMS = {"GF-01", "GF-04"}
# R-T701-2 terms of the two annex dry plaster lines (T-556 rows: openings with a fixed area, held arch width, beam ends)
ANNEX_PLASTER_TERMS = {
    "GF-01": {"fixed": "10.791", "fixed_note": "W11 4.301 + W12 4.29 (hole areas below S, T-686) + D-GF-01 2.20",
              "held_width": "1.0", "held_note": "A-GF-01 arch, no printed height: 0 .. 1.0 x S (T-556 / D-45)",
              "beam_ends": "0.236", "beam_note": "CB6 2 ends (T-556)"},
    "GF-04": {"fixed": "4.22", "fixed_note": "W04 0.6 x (2.5 - 1.7) = 0.48 (S >= 2.5) + D-GF-03 1.98 + D-GF-04 1.76",
              "held_width": "0", "held_note": "-", "beam_ends": "0", "beam_note": "-"},
}
# GF-02 wash: a WET space in his dry rows (row 9); engine line = the tile-backing render (T-686), face 7.200 lm.
WASH = {"room": "GF-02", "his_row": 9, "face_lm": "7.2", "plaster_line": "L-2211463b",
        "ends": {"low": ANNEX_H[0], "high": ANNEX_H[1]}}
# SHAFT (T-173 model + T-680 R-T680-1/-2): drawn plaster gross 177.07 (b 0) / 173.82 (b 0.10); paint 175.14 / 171.88;
# pier returns by band added by T-680 (plaster 1.213 .. 1.223, paint 1.198 .. 1.208).
SHAFT = {"his_plaster_rows": [23, 24, 8], "his_paint_rows": [24, 25, 8],
         "box_to_drawing": "13.85", "box_note": "his box vs the drawn faces: south +20.11 (open void side above +5.50), "
                                                 "north -2.64, west / east -3.62 (T-173)",
         "residual": "54.00", "residual_note": "his row 2.50 x 5.40 and row 'stair wall' 11.25 x 3.60: no drawn face "
                                                "(T-173; T-634 re-read the GF stair hall / lobby outlines)",
         "plaster_gross": ("173.82", "177.07"), "paint_gross": ("171.88", "175.14"),
         "plaster_returns": ("1.213", "1.223"), "paint_returns": ("1.198", "1.208")}
DOOR_RETURN_WET_BOTH_SIDES = "3.899556"   # T-634: 5 doors with wet rooms on both sides (no paint established)
HIS_HALF = "58.2475"                      # his invoice row 16 'half' column, both workbooks


def _pinned(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {h[:16]} is not the pinned merged file")
    return json.loads(p.read_text(encoding="utf-8"))


def _cells(raw, file_code, anchor):
    """his statement sheet of one workbook: the sheet that carries the anchor total cell."""
    rows = [r for r in raw["rows"] if r["file"] == file_code]
    sheets = {r["sheet"] for r in rows if anchor in r["cells"]}
    if len(sheets) != 1:
        raise SystemExit(f"{file_code}: statement sheet not unique ({len(sheets)})")
    sh = sheets.pop()
    return {k: v["v"] for r in rows if r["sheet"] == sh for k, v in r["cells"].items()}


def _num(c, key):
    v = c.get(key)
    if not isinstance(v, (int, float)):
        raise SystemExit(f"his cell {key} not a number")
    return D(repr(v)).quantize(Decimal("0.0001"))


def _his_row(c, row):
    return (_num(c, f"H{row}"), _num(c, f"F{row}"))


def _lines(index):
    by = {}
    for x in index["lines"]:
        if x["item_code"] in ("FIN.PLASTER", "FIN.PAINT"):
            by[x["line_id"]] = x
    return by


def _val(x):
    if x["class"] == "RELEASED":
        v = D(repr(x["measured_net"]))
        return v, v
    if x["class"] == "HELD" and x["held_low"] is not None:
        return D(repr(x["held_low"])), D(repr(x["held_high"]))
    return None


def _find(lines, code, element):
    hits = [x for x in lines.values() if x["item_code"] == code and x["element_id"] == element]
    if len(hits) != 1:
        raise SystemExit(f"{code} {element}: {len(hits)} lines")
    return hits[0]


def classify(x):
    e = x["element_id"]
    if x["class"] == "EXCLUDED":
        return "EXCLUDED"
    if ":plaster band above ceiling" in e:
        return "WET_BAND"
    if "-OPENING-" in e or "-REVEAL-" in e:
        return "RETURN"
    if e.startswith("HL:WALL_FINISH:ST_"):
        return "SHAFT"
    if e == "HL:WALL_FINISH:GF_07:PLASTER":
        return "WET_RENDER"           # GF-07: paint EXCLUDED (full-height tile), its room-route line EXCLUDED
    if e.startswith("HL:WALL_FINISH:"):
        return "DRY"
    return "WET_RENDER"               # engine room lines left after the T-331 / T-454 route: tile-backing render


def build():
    idx = _pinned(INDEX)
    t556 = {r["room"]: r for r in _pinned(T556)["rows"]}
    raw = _pinned(RAW)
    pls, pnt = _cells(raw, "PLS", "J27"), _cells(raw, "PNT", "J28")
    lines = _lines(idx)
    out = {"schema": "URBAN_T701_PLASTER_PAINT_RECONCILE_V1", "candidate": idx["candidate_version"],
           "inputs_sha256_16": {str(p.relative_to(ROOT)): PINS[p][:16] for p in PINS}}

    # ---- census by face class (every non-excluded line exactly once) --------------------------------------------
    census = {}
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        c = {}
        for x in sorted((x for x in lines.values() if x["item_code"] == code), key=lambda x: x["element_id"]):
            k = classify(x)
            v = _val(x)
            r = c.setdefault(k, {"lines": 0, "released": Decimal(0), "held_low": Decimal(0), "held_high": Decimal(0),
                                 "blank": []})
            r["lines"] += 1
            if k == "EXCLUDED":
                continue
            if v is None:
                r["blank"].append(x["line_id"][:10])
            elif x["class"] == "RELEASED":
                r["released"] += v[0]
            else:
                r["held_low"] += v[0]
                r["held_high"] += v[1]
        census[code] = {k: {"lines": r["lines"], "released": str(q6(r["released"])), "held": [str(q6(r["held_low"])),
                            str(q6(r["held_high"]))], "blank": r["blank"]} for k, r in sorted(c.items())}
    tot = {}
    for code in census:
        rel = sum(D(v["released"]) for v in census[code].values())
        lo = sum(D(v["held"][0]) for v in census[code].values())
        hi = sum(D(v["held"][1]) for v in census[code].values())
        tot[code] = (rel, lo, hi)
    # the candidate figures the board states (T-687 / Verifier 2026-11-11 07:45)
    assert tot["FIN.PLASTER"] == (D("388.58436"), D("1131.965876"), D("1300.69428")), tot["FIN.PLASTER"]
    assert tot["FIN.PAINT"] == (D("217.2081"), D("601.645338"), D("682.3313")), tot["FIN.PAINT"]
    out["census"] = census

    his = {"plaster_gross": _num(pls, "J27"), "plaster_net": D("1151.1375"), "paint_gross": _num(pnt, "J28"),
           "paint_net": D("1191.1275"), "half": D(HIS_HALF), "wet_spatter": _num(pls, "J47"),
           "decor_paint": _num(pnt, "J51")}
    assert his["plaster_gross"] - his["half"] == his["plaster_net"]
    assert his["paint_gross"] - his["half"] == his["paint_net"]

    # ---- DRY rooms, both layers (R-T701-1) -------------------------------------------------------------------------
    dry = []
    pl_dry = [Decimal(0), Decimal(0)]
    pt_dry = [Decimal(0), Decimal(0)]
    sums = {"plaster": {}, "paint": {}}
    for room, key, le, g1, prow, nrow in DRY:
        t = t556[room]
        assert D(t["face_lm"]) == D(le), (room, t["face_lm"])
        pl = _find(lines, "FIN.PLASTER", f"HL:WALL_FINISH:{key}:PLASTER")
        pt = _find(lines, "FIN.PAINT", f"HL:WALL_FINISH:{key}:PAINT")
        plv, ptv = _val(pl), _val(pt)
        assert plv == (D(t["new_lo"]), D(t["new_hi"])), (room, plv)
        h_pl = D(t["new"]["gross"]) / D(le)
        b_pl = R.room_bridge([_his_row(pls, r) for r in prow], le, {"low": (h_pl, plv[0]), "high": (h_pl, plv[1])})
        if room in ANNEX_PAINT_ROOMS:
            ends = {"low": (ANNEX_H[0], ptv[0]), "high": (ANNEX_H[1], ptv[1])}
        else:
            ends = {"low": (g1, ptv[0]), "high": (g1, ptv[1])}
        b_pt = R.room_bridge([_his_row(pnt, r) for r in nrow], le, ends)
        for b, acc, s in ((b_pl, pl_dry, sums["plaster"]), (b_pt, pt_dry, sums["paint"])):
            acc[0] += b["low"]["net"]
            acc[1] += b["high"]["net"]
            for end in ("low", "high"):
                for term in ("LENGTH", "HEIGHT", "DEDUCTIONS"):
                    s.setdefault(term, {"low": Decimal(0), "high": Decimal(0)})[end] += b[end][term]
        dry.append({"room": room, "plaster_line": pl["line_id"][:10], "plaster_class": pl["class"],
                    "paint_line": pt["line_id"][:10], "paint_class": pt["class"], "plaster_height_basis":
                    "slab / roof underside (Q-72; T-556 gross / face)", "paint_height_basis":
                    "finished ceiling (owner G1, Q-48 A)" + ("; annex H 2.494 .. 3.25 (T-686, Q-54 B)"
                                                           if room in ANNEX_PAINT_ROOMS else ""),
                    "plaster": _s(b_pl), "paint": _s(b_pt)})
    his_dry_pl = sum((D(d["plaster"]["his_gross"]) for d in dry), Decimal(0))
    his_dry_pt = sum((D(d["paint"]["his_gross"]) for d in dry), Decimal(0))
    assert his_dry_pl == his_dry_pt == D("924.205"), (his_dry_pl, his_dry_pt)
    out["dry_rooms"] = dry
    out["dry_sums"] = {lay: {t: {e: str(q6(v)) for e, v in x.items()} for t, x in s.items()} for lay, s in sums.items()}

    # ---- R-T701-2 annex dry plaster coverage ---------------------------------------------------------------------
    cov = {}
    for room, tm in ANNEX_PLASTER_TERMS.items():
        pl = _find(lines, "FIN.PLASTER", f"HL:WALL_FINISH:{room.replace('-', '_')}:PLASTER")
        lo, hi = _val(pl)
        le = D(t556[room]["face_lm"])
        # reproduce the wired value at the T-556 scenario S = 3.79 before testing coverage
        g = D(t556[room]["new"]["gross"])
        assert g == le * D("3.79"), (room, g)
        b = R.datum_bound(le, ANNEX_S[0], ANNEX_S[1], tm["fixed"], tm["held_width"], tm["beam_ends"])
        at379 = (q6(le * D("3.79") - D(tm["fixed"]) - D(tm["held_width"]) * D("3.79") - D(tm["beam_ends"])),
                 q6(le * D("3.79") - D(tm["fixed"]) - D(tm["beam_ends"])))
        assert at379 == (q6(lo), q6(hi)), (room, at379, lo, hi)
        c = R.coverage(lo, hi, b)
        cov[room] = {"line": pl["line_id"][:10], "terms": tm, "reproduced_at_S_3.79": [str(x) for x in at379],
                     "status": c["status"], "line_range": [str(x) for x in c["line"]],
                     "datum_bound": [str(x) for x in c["bound"]],
                     "change": [str(x) for x in c.get("change", [])]}
    out["annex_plaster_coverage"] = cov

    # ---- WASH (his row 9) ------------------------------------------------------------------------------------------
    wl = lines[[k for k in lines if k.startswith(WASH["plaster_line"])][0]]
    wv = _val(wl)
    bw = R.room_bridge([_his_row(pls, WASH["his_row"])], WASH["face_lm"],
                       {"low": (WASH["ends"]["low"], wv[0]), "high": (WASH["ends"]["high"], wv[1])})
    his_wash_pt = R.his_gross([_his_row(pnt, 9)])[0]
    out["wash"] = {"room": WASH["room"], "plaster": _s(bw), "paint": {"his_gross": str(q6(his_wash_pt)), "engine":
                   "EXCLUDED (GF-02 'paint above wall tile': full-height porcelain, no paint face)",
                   "cause": "RULE_DIFFERENCE"}}

    # ---- SHAFT --------------------------------------------------------------------------------------------------------
    sh = {}
    for lay, code, rows_, gross, ret, extra in (
            ("plaster", "FIN.PLASTER", SHAFT["his_plaster_rows"], SHAFT["plaster_gross"], SHAFT["plaster_returns"], None),
            ("paint", "FIN.PAINT", SHAFT["his_paint_rows"], SHAFT["paint_gross"], SHAFT["paint_returns"],
             ("paint top: 0.15 decor line under the roof vs his plaster top (T-173 177.07 - 175.14)", "1.93"))):
        c = pls if lay == "plaster" else pnt
        g = sum((a * b for a, b in (_his_row(c, r) for r in rows_)), Decimal(0))
        el = [x for x in lines.values() if x["item_code"] == code and classify(x) == "SHAFT"]
        assert len(el) == 3
        lo = sum(_val(x)[0] for x in el)
        hi = sum(_val(x)[1] for x in el)
        comps = [("his rows with no drawn face", SHAFT["residual"], SHAFT["residual"], "UNRESOLVED"),
                 ("his box vs the drawn faces (T-173)", SHAFT["box_to_drawing"], SHAFT["box_to_drawing"],
                  "ENGINE_RIGHT")]
        if extra:
            comps.append((extra[0], extra[1], extra[1], "RULE_DIFFERENCE"))
        comps.append(("pier returns (T-680 R-T680-2): built faces he omits", str(-D(ret[0])), str(-D(ret[1])),
                      "ENGINE_RIGHT"))
        comps.append(("build-up b 0 .. 0.10 (not printed)", str(D(gross[1]) - D(gross[0])), "0", "HELD"))
        top = D(gross[1]) + D(ret[1])
        rem_hi = top - hi
        rem_lo = D(gross[0]) + D(ret[0]) - lo
        comps.append(("drawn deductions + held items (contacts, W25 / W27, held heads, beam ends; full Q-73 vs his "
                      "half list), remainder of the T-173 / T-680 gross", str(rem_lo), str(rem_hi), "HELD"))
        pc = R.pair_close(g, lo, hi, comps)
        sh[lay] = {"his_gross": str(q6(g)), "engine": [str(q6(lo)), str(q6(hi))],
                   "components": [{"name": n, "at_engine_low": str(q6(D(a))), "at_engine_high": str(q6(D(b))),
                                   "cause": k} for n, a, b, k in comps], **_j(pc)}
    out["shaft"] = sh

    # ---- RETURNS -----------------------------------------------------------------------------------------------------
    rets = [x for x in lines.values() if x["item_code"] == "FIN.PLASTER" and classify(x) == "RETURN"]
    rv = sum(_val(x)[0] for x in rets if _val(x))
    rblank = sorted(x["line_id"][:10] for x in rets if not _val(x))
    his_ret = _num(pls, "J26")
    assert his_ret == _num(pnt, "J27") == D("15.96")
    out["returns"] = {
        "plaster": {"his_gross": str(his_ret), "engine_released": str(q6(rv)), "engine_lines": len(rets),
                    "engine_blank": rblank, **_j(R.pair_close(his_ret, rv, rv, [
                        ("his 14 doors x 0.20 x 5.70 not by id vs the engine's 27 valued return lines by id "
                         "(T-552 -7.11 + OP-009 1.08 now valued)", str(his_ret - rv), str(his_ret - rv),
                         "UNRESOLVED")]))},
        "paint": {"his_gross": str(his_ret), "engine": "no FIN.PAINT return line (T-561 ENGINE_OMISSION, T-569 "
                  "fix row not wired)", "physical_bound": [str(q6(rv - D(DOOR_RETURN_WET_BOTH_SIDES) -
                                                                  D("1.08"))), str(q6(rv - D(DOOR_RETURN_WET_BOTH_SIDES)))],
                  "bound_note": "painted part <= plastered returns - 5 doors with wet rooms both sides (T-634); "
                                "low end also without the external door OP-009 (its outer reveal side is facade "
                                "render, side not established); frame-covered depth not printed: HELD",
                  "cause": "ENGINE_OMISSION"}}

    # ---- KEY SCOPE: wet render + bands in the engine plaster key, not in his internal plaster ---------------------
    wet = [x for x in lines.values() if x["item_code"] == "FIN.PLASTER" and classify(x) in ("WET_RENDER", "WET_BAND")
           and not x["line_id"].startswith(WASH["plaster_line"])]
    wlo = sum(_val(x)[0] for x in wet)
    whi = sum(_val(x)[1] for x in wet)
    render_all = [x for x in lines.values() if x["item_code"] == "FIN.PLASTER" and classify(x) == "WET_RENDER"]
    r_lo = sum(_val(x)[0] for x in render_all)
    r_hi = sum(_val(x)[1] for x in render_all)
    out["key_scope_wet"] = {
        "engine_lines": len(wet), "engine": [str(q6(wlo)), str(q6(whi))], "his_in_key": "0",
        "cause": "RULE_DIFFERENCE",
        "why": "his internal plaster prices dry faces only; his wet faces are his spatter row (J47 = his wall-tile "
               "total, T-317) and the levelling render is in his tile rate (owner wet-wall rule 2026-11-02: spatter by "
               "the plasterer, render by the tiler). The engine's FIN.PLASTER carries the render (T-331 / T-454) and "
               "the band above the ceiling (T-690, Q-72), so the PLASTER.INTERNAL key compares different scopes",
        "beside_not_summed": {"his_wet_spatter": str(his["wet_spatter"]),
                              "engine_wet_render_faces_incl_GF-02": [str(q6(r_lo)), str(q6(r_hi))]}}

    # ---- whole bridges ---------------------------------------------------------------------------------------------
    def split(prefix, s_low, s_high):
        """LENGTH / HEIGHT / DEDUCTIONS of one bridge -> components; deductions split into the engine's minimum
        (openings in full per room, Q-73, against his gross: his statement deducts half once) and the held range."""
        return [(f"{prefix} LENGTH (his lengths vs the drawn faces)", s_low["LENGTH"], s_high["LENGTH"], "ENGINE_RIGHT"),
                (f"{prefix} HEIGHT (his flat height vs the layer's basis)", s_low["HEIGHT"], s_high["HEIGHT"],
                 "RULE_DIFFERENCE"),
                (f"{prefix} DEDUCTIONS at the engine minimum (openings in full, Q-73)", s_high["DEDUCTIONS"],
                 s_high["DEDUCTIONS"], "RULE_DIFFERENCE"),
                (f"{prefix} DEDUCTIONS held range (heads / arches / beam ends not established)",
                 str(D(s_low["DEDUCTIONS"]) - D(s_high["DEDUCTIONS"])), "0", "HELD")]

    def comp_dry(lay):
        s = sums[lay]
        return split("DRY", {t: str(s[t]["low"]) for t in s}, {t: str(s[t]["high"]) for t in s})

    pl_eng = (tot["FIN.PLASTER"][0] + tot["FIN.PLASTER"][1], tot["FIN.PLASTER"][0] + tot["FIN.PLASTER"][2])
    pt_eng = (tot["FIN.PAINT"][0] + tot["FIN.PAINT"][1], tot["FIN.PAINT"][0] + tot["FIN.PAINT"][2])
    shp = out["shaft"]["plaster"]["components"]
    shn = out["shaft"]["paint"]["components"]
    pl_comps = comp_dry("plaster") + split("WASH row 9 (wet render)", {t: str(bw["low"][t]) for t in
                                                                        ("LENGTH", "HEIGHT", "DEDUCTIONS")},
                                           {t: str(bw["high"][t]) for t in ("LENGTH", "HEIGHT", "DEDUCTIONS")}) + [
        ("SHAFT " + c["name"], c["at_engine_low"], c["at_engine_high"], c["cause"]) for c in shp] + [
        ("RETURNS his doors not by id", str(his_ret - rv), str(his_ret - rv), "UNRESOLVED"),
        ("KEY SCOPE wet render + bands (his spatter row, not his plaster)", str(-wlo), str(-whi), "RULE_DIFFERENCE")]
    pt_comps = comp_dry("paint") + [
        ("WASH row 9: wet face, no paint (one finish per face)", str(his_wash_pt), str(his_wash_pt), "RULE_DIFFERENCE")
    ] + [("SHAFT " + c["name"], c["at_engine_low"], c["at_engine_high"], c["cause"]) for c in shn] + [
        ("RETURNS: no engine paint return line", str(his_ret), str(his_ret), "ENGINE_OMISSION"),
        ("SOFFITS his rows 18-19 (stair flight soffits = CEILING class, Q-57)", str(_num(pnt, "J19")),
         str(_num(pnt, "J19")), "RULE_DIFFERENCE")]
    # his gross bridge, then his half step to his net (his step on the whole statement)
    out["whole"] = {}
    for lay, g, net, eng, comps in (("plaster", his["plaster_gross"], his["plaster_net"], pl_eng, pl_comps),
                                    ("paint", his["paint_gross"], his["paint_net"], pt_eng, pt_comps)):
        pc = R.pair_close(g, eng[0], eng[1], comps)
        pct = [q6((eng[0] - net) / net * 100), q6((eng[1] - net) / net * 100)]
        out["whole"][lay] = {"his_gross": str(g), "his_half_step": str(his["half"]), "his_net": str(net),
                             "engine": [str(q6(eng[0])), str(q6(eng[1]))], "engine_vs_his_net_pct": [str(x) for x in pct],
                             "components": [{"name": n, "at_engine_low": str(q6(D(a))), "at_engine_high":
                                             str(q6(D(b))), "cause": k} for n, a, b, k in comps], **_j(pc)}
    # like for like (same faces, same layer): drop the key-scope wet pair and his non-wall rows
    ll_eng_pl = (pl_eng[0] - wlo - wv[0] - rv, pl_eng[1] - whi - wv[1] - rv)
    ll_his_pl = his_dry_pl + D(sh["plaster"]["his_gross"])
    out["like_for_like_dry_plus_shaft"] = {
        "plaster": {"his_gross": str(q6(ll_his_pl)), "engine_net": [str(q6(x)) for x in ll_eng_pl],
                    "pct": [str(q6((x - ll_his_pl) / ll_his_pl * 100)) for x in ll_eng_pl]},
        "paint": {"his_gross": str(q6(his_dry_pt + D(sh["paint"]["his_gross"]))),
                  "engine_net": [str(q6(x)) for x in pt_eng],
                  "pct": [str(q6((x - his_dry_pt - D(sh["paint"]["his_gross"])) /
                                 (his_dry_pt + D(sh["paint"]["his_gross"])) * 100)) for x in pt_eng]}}
    out["his"] = {k: str(v) for k, v in his.items()}
    return out


def _j(pc):
    return {"gap_at_engine_low": str(pc["gap_at_engine_low"]), "gap_at_engine_high": str(pc["gap_at_engine_high"]),
            "by_cause": {k: [str(a), str(b)] for k, (a, b) in pc["by_cause"].items()}}


def _s(b):
    return {k: ({kk: str(vv) for kk, vv in v.items()} if isinstance(v, dict) else str(v)) for k, v in b.items()}


def md(o):
    L = [f"# T-701 plaster / paint reference reconciliation ({o['candidate']}): generated tables", "",
         "m2 unless stated. gap = his gross - engine net at the engine's low / high end; HELD ranges never summed as 0.",
         ""]
    for lay in ("plaster", "paint"):
        w = o["whole"][lay]
        L += [f"## {lay.upper()}: his gross {w['his_gross']} (net {w['his_net']} after his half step "
              f"{w['his_half_step']}) vs engine {w['engine'][0]} .. {w['engine'][1]} "
              f"({w['engine_vs_his_net_pct'][0]} .. {w['engine_vs_his_net_pct'][1]} % vs his net)", "",
              "| component | at engine low | at engine high | cause |", "|---|---|---|---|"]
        L += [f"| {c['name']} | {c['at_engine_low']} | {c['at_engine_high']} | {c['cause']} |" for c in w["components"]]
        L += [f"| **sum = his gross - engine** | **{w['gap_at_engine_low']}** | **{w['gap_at_engine_high']}** | |", "",
              "By cause: " + "; ".join(f"{k} {a} .. {b}" for k, (a, b) in w["by_cause"].items()), ""]
    L += ["## DRY rooms by room (R-T701-1)", "",
          "| room | layer | his gross | engine net | LENGTH | HEIGHT (his F vs H) | DEDUCTIONS |", "|---|---|---|---|---|---|---|"]
    for d in o["dry_rooms"]:
        for lay in ("plaster", "paint"):
            b = d[lay]
            L.append(f"| {d['room']} | {lay} | {b['his_gross']} | {b['low']['net']} .. {b['high']['net']} | "
                     f"{b['low']['LENGTH']} | {b['low']['HEIGHT']} .. {b['high']['HEIGHT']} (F {b['his_weighted_height_m']}"
                     f" vs H {b['low']['H_m']} .. {b['high']['H_m']}) | {b['low']['DEDUCTIONS']} .. "
                     f"{b['high']['DEDUCTIONS']} |")
    L += ["", "Per floor (dry rooms; his gross vs engine net low .. high):", ""]
    for fl in ("GF", "1F", "2F"):
        for lay in ("plaster", "paint"):
            rs = [d[lay] for d in o["dry_rooms"] if d["room"].startswith(fl)]
            g = sum(Decimal(b["his_gross"]) for b in rs)
            lo = sum(Decimal(b["low"]["net"]) for b in rs)
            hi = sum(Decimal(b["high"]["net"]) for b in rs)
            L.append(f"- {fl} {lay}: his {q6(g)} vs engine {q6(lo)} .. {q6(hi)} (gap {q6(g - hi)} .. {q6(g - lo)})")
    L += ["", "## Annex dry plaster: datum coverage (R-T701-2)", "", "| room | line | line range | datum bound S 3.084 .. 3.84 | status |",
          "|---|---|---|---|---|"]
    for r, c in o["annex_plaster_coverage"].items():
        L.append(f"| {r} | {c['line']} | {c['line_range'][0]} .. {c['line_range'][1]} | {c['datum_bound'][0]} .. "
                 f"{c['datum_bound'][1]} | {c['status']} |")
    ll = o["like_for_like_dry_plus_shaft"]
    L += ["", "## Like for like (dry rooms + shaft, same layer, his gross vs engine net)", "",
          f"- plaster: his {ll['plaster']['his_gross']} vs engine {ll['plaster']['engine_net'][0]} .. "
          f"{ll['plaster']['engine_net'][1]} ({ll['plaster']['pct'][0]} .. {ll['plaster']['pct'][1]} %)",
          f"- paint: his {ll['paint']['his_gross']} vs engine {ll['paint']['engine_net'][0]} .. "
          f"{ll['paint']['engine_net'][1]} ({ll['paint']['pct'][0]} .. {ll['paint']['pct'][1]} %)", ""]
    return "\n".join(L) + "\n"


def main(argv):
    o = build()
    js = json.dumps(o, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    m = md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == m
        print("T701 check:", "byte-identical" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(m, encoding="utf-8")
    print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
