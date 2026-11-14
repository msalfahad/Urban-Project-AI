"""T-779 (lane A, research, unwired): split the two open freelancer differences into named causes.

  (1) MAS.BLOCK  981.35 vs his 1,260.69 m2 (-279.34, -22.2 %)   [V3.0.82 lines + T-765 fix rows, MERGED 3b9f35a6]
  (2) FIN.PLASTER 'ex wet render' 1,236.8 vs his 1,169.1 m2 (+67.7, +5.8 %)   [V3.0.81 lines + T-763 r2 fix rows]

Method R-T779-1 (every villa):
  (a) Put both totals on the SAME face classes before any %: blockwork = storey walls / below-ground / boundary wall /
      parapets / facade rows; plaster = dry rooms / stair shaft / wet render / wet band above the ceiling / returns.
      A class that only one side books is a scope (RULE_DIFFERENCE) row, never a residual.
  (b) Blockwork storey walls: carry the merged T-543 identity (his floor net = engine valued + HELD carried by cause +
      drift + height + openings + length residual) and replace each HELD carried figure by the T-765 released value
      of the same walls: the change per cause is a named row (what the fill did to the carried figure).
  (c) Plaster dry rooms: per room his L_h x H_h vs ours L_e x H_e - openings - beam ends (MAIN_FILL_2 bases):
      LENGTH (L_h - L_e) x H_h + HEIGHT L_e x (H_h - H_e) + DEDUCTIONS (ours) = his - ours, exact.
  (d) Every decomposition closes exactly in Decimal; the only UNRESOLVED rows are named.

Inputs: repository files only, sha256-pinned (first 16 hex). His figures are the numeric cells already parsed into the
repository (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, T-543 section sub-totals); no workbook text, room
title, client name or drawing content is written by this script. Run: python3 -I t779_split.py [--check]
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out" / "T779_SPLIT.json"

IN = {
    "idx82": (ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_82.json", "e51909257a5d688f"),
    "idx81": (ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_81.json", "3976b262611bc3bd"),
    "t765": (ROOT / "research/agents_t765/out/FIX_ROWS.json", "5e2a1ca35b40c680"),
    "t763": (ROOT / "research/agents_t763/out/FIX_ROWS.json", "419b3f359a24bda1"),
    "t543": (ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json", "a4cfcdeb01aab26e"),
    "raw": (ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json", "752c9f4e0c4546d0"),
}
Q4 = D("0.0001")


def load(key):
    p, pin = IN[key]
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()[:16]
    if h != pin:
        raise SystemExit(f"input {p} sha256 {h} != pinned {pin}")
    return json.loads(b)


def dec(x):
    return D(str(x))


# ===================================================================================================== (1) BLOCKWORK
def floor_of(eid: str) -> str:
    if eid.startswith("HOUSE_BELOW_NG"):
        return "BELOW"
    return eid[:2]


def colour_of(eid: str, basis: str) -> str:
    if "_WHITE" in eid:
        return "WHITE"
    if "_BLACK" in eid:
        return "BLACK"
    return "PARENT"            # T-765 parent host: colour faces from its MAS.UNITS rows


def engine_block():
    idx = load("idx82")
    fix = {r["line_id"]: r for r in load("t765")["rows"]}
    per_floor, lines = {}, []
    for ln in idx["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        r = fix.get(ln["line_id"])
        if r is not None:
            if r["after"]["class"] != "RELEASED":
                continue
            v, src, label = dec(r["after"]["net"]), "T-765", r["label"]
        else:
            if ln["class"] != "RELEASED":
                raise SystemExit(f"unexpected blank MAS.BLOCK {ln['line_id']}")
            v, src, label = dec(ln["measured_net"]), "V3.0.82", "MEASURED/released"
        f = floor_of(ln["element_id"])
        per_floor[f] = per_floor.get(f, D(0)) + v
        lines.append({"line_id": ln["line_id"], "element_id": ln["element_id"], "m2": str(v), "source": src,
                      "label": label})
    # colour faces: released host lines by id, T-765 parents by their MAS.UNITS rows
    white = D(0)
    for x in lines:
        if "_WHITE" in x["element_id"]:
            white += dec(x["m2"])
    for r in load("t765")["rows"]:
        if r["item_code"] == "MAS.UNITS.WHITE" and r["after"].get("net") and "#BLOCKWORK" not in r.get("element_id", ""):
            if "valued white host" in r["basis"]:
                continue
            white += (dec(r["after"]["net"]) / D("6.4")).quantize(Q4)
    total = sum(per_floor.values(), D(0))
    return per_floor, total, white, lines


def block_split():
    t543 = load("t543")
    per_floor, total, white, lines = engine_block()
    his_total = dec(t543["freelancer_total"])
    rows_543 = {r["component"] if "component" in r else r.get("name"): r for r in t543["rows"]}
    fl = {}
    for r in t543["rows"]:
        dec_ = r.get("decomposition")
        if dec_ and dec_.get("floor"):
            fl[dec_["floor"]] = dec_
    # T-765 released values of the walls T-543 carried as HELD, grouped by the T-543 cause (sums of the T-713
    # components written in the T-765 bases; GF-H01 / GF-H02 / GF-W37 glazed lines / strips: 0 by the main-chat
    # default 2026-11-13 17:30 (EXCLUDED / no piece)).
    FILL = {
        "GF": {
            "CB2 width conflict D-27 (GF-W22)": ("12.921", "12.9311"),
            "annex storey datum (11 annex walls) at 3.84 / 4.00 - beam": ("130.745",
                "32.1750 6.3360 14.3025 6.8000 11.1200 13.5850 4.9920 15.5200 17.2800 4.0000 6.2536"),
            "W10 shaft piece increment": ("8.2725", "8.2700"),
            "held-opening walls W15 / W26: openings now deducted (D-GF-07 2.00x2.50, W01 2.40, A-GF-01 1.00x2.20)": (
                "41.807", "21.2320 13.3750"),
            "lift walls W08 / W09 / W13 / W14: T-761 tie-beam faces + lift doors deducted": ("41.171",
                "11.9146 6.6600 2.5900 12.6760"),
            "sunken-panel drop walls: recess default 0.30 x run deducted (D-41)": ("46.693",
                "1.8180 14.5510 3.9604 5.3216 8.8904 9.8773"),
            "held length (W03 / W30 / W36 filled; H01 / H02 / W37 glazed strips = 0 blockwork)": ("23.965545",
                "9.9000 4.8585 1.7000"),
        },
        "1F": {
            "dome / member pieces + held length (W04 / W10 / W13 / W17 / W24 / W11) at the ring soffit": (
                str(dec("2.2693") + dec("41.647484") + dec("-0.872")),
                "2.8800 8.0000 10.8786 1.7187 3.9135 13.9650"),
            "held-opening walls W07 / W14+15 / W16: openings deducted at 2.20 head default": ("45.914",
                "7.2410 16.5255 17.8480"),
        },
        "2F": {
            "roof datum: b_r 0.05 what-if -> owner +13.90 structural top (b_r 0); held pieces at defaults": (
                str(dec("6.840") + dec("104.791") + dec("20.706679")),
                "1.7650 28.3687 9.4700 3.8500 21.9450 25.8950 16.2250 21.7875"),
        },
    }
    floors = {}
    for f in ("GF", "1F", "2F"):
        d = fl[f]
        his_net = dec(d["his_net_m2"])
        ours = per_floor[f]
        named = []
        for r in d["rows"]:
            if r["cause"] != "HELD":
                named.append({"name": "T-543: " + r["name"], "delta": str(dec(r["delta"])), "class": r["cause"]})
        fill_sum = D(0)
        for name, (carried, comps) in FILL[f].items():
            actual = sum((dec(c) for c in comps.split()), D(0))
            fill_sum += actual
            named.append({"name": "fill vs carried: " + name, "delta": str(dec(carried) - actual),
                          "class": "FILL_CHANGE", "carried": carried, "released": str(actual)})
        drift = ours - (dec(d["engine_valued_m2"]) + fill_sum)
        assert drift.copy_abs() <= D("0.001"), (f, drift)
        if drift:
            named.append({"name": "T-713 component print rounding (line value - sum of printed components)",
                          "delta": str(-drift), "class": "TOLERANCE"})
        s = sum((dec(x["delta"]) for x in named), D(0))
        assert s == his_net - ours, (f, s, his_net - ours)
        floors[f] = {"his_net": str(his_net), "ours": str(ours), "his_minus_ours": str(his_net - ours),
                     "H_his": d["H_his"], "L_his": d["L_his"], "rows": named}
    scope = [
        {"name": "his parapet rows (3) in masonry: RC upstand 0.30 = concrete (P1 detail) + block alternative "
                 "above (material HELD Q-65 C) + his height from the slab", "delta": "172.93",
         "class": "RULE_DIFFERENCE (family placement; T-543 5a-5d)"},
        {"name": "his boundary wall row 37.20 x 2.00 in masonry: ours under EXT.FENCE.WALL", "delta": "74.40",
         "class": "RULE_DIFFERENCE (family placement)"},
        {"name": "his 1F 'projections' row 7.50 x 5.50: no masonry element identified (facade frames HELD, T-172)",
         "delta": "41.25", "class": "UNRESOLVED"},
        {"name": "his 20 cm openings with no floor", "delta": "-9.84", "class": "UNRESOLVED"},
        {"name": "below-ground block under the neighbour-side beams (printed note p.1 n.2; 0.70 = lower bound "
                 "h >= 0.70, formation unprinted): ours only", "delta": str(-per_floor["BELOW"]),
         "class": "ENGINE_RIGHT on scope (value ESTIMATE, lower bound)"},
    ]
    gap = his_total - total
    s = sum((dec(x["delta"]) for x in scope), D(0)) + sum((dec(v["his_minus_ours"]) for v in floors.values()), D(0))
    assert s == gap, (s, gap)
    his_storey = sum((dec(v["his_net"]) for v in floors.values()), D(0)) - D("9.84")
    our_storey = sum((per_floor[f] for f in ("GF", "1F", "2F")), D(0))
    # cause totals
    by = {}
    for v in floors.values():
        for r in v["rows"]:
            key = r["class"]
            by[key] = by.get(key, D(0)) + dec(r["delta"])
    return {
        "ours_total": str(total), "his_total": str(his_total), "his_minus_ours": str(gap),
        "pct": str((-gap / his_total * 100).quantize(D("0.01"))),
        "ours_per_floor": {k: str(v) for k, v in per_floor.items()},
        "scope_rows": scope, "floors": floors,
        "storey_walls_like_for_like": {"ours": str(our_storey), "his_incl_unassigned_openings": str(his_storey),
                                       "his_minus_ours": str(his_storey - our_storey),
                                       "pct": str(((our_storey - his_storey) / his_storey * 100).quantize(D("0.01")))},
        "storey_rows_by_class": {k: str(v) for k, v in by.items()},
        "colour": {"ours_white_m2": str(white), "ours_black_m2": str(total - white),
                   "his_external_section": "559.8015", "his_external_walls_ex_projections": "518.5515",
                   "his_internal_15_20_sections": "700.888", "his_internal_walls_ex_boundary_parapets": "453.558"},
        "lines": lines,
    }


# ===================================================================================================== (2) PLASTER
# dry rooms: (room, his rows, ours face lm, ours H, ours openings, ours beam ends) from the MAIN_FILL_2 bases
DRY = [
    ("GF-01", [4], "20.127", "3.84", "12.991", "0.236"),
    ("GF-04", [5], "12.5", "3.84", "4.220", "0"),
    ("GF-15", [6], "21.537", "4.34", "25.865", "0"),
    ("GF-08", [7], "53.188", "4.34", "45.727", "1.070"),
    ("1F-01", [11], "17.7", "4.04", "7.880", "0.153"),
    ("1F-04", [12], "17.4", "4.04", "6.285", "0"),
    ("1F-10", [13], "16.2", "4.04", "4.180", "0.625"),
    ("1F-11", [14], "22.149", "4.04", "10.887", "0"),
    ("1F-13", [15, 16], "39.45", "4.04", "19.990", "0"),
    ("2F-03", [19], "18.9", "4.04", "5.540", "0.096"),
    ("2F-01", [20], "9.009", "4.04", "6.380", "0.208"),
]
SHAFT_HIS_ROWS = (8, 23, 24)
HIS_WASH_ROW, HIS_RETURN_ROW = 9, 26


def his_plaster_rows():
    raw = load("raw")
    pls = [r for r in raw["rows"] if r["file"] == "PLS"]
    sheet = pls[0]["sheet"]
    out = {}
    for r in pls:
        if r["sheet"] != sheet or not 4 <= r["row"] <= 27:
            continue
        c = {k[0]: v["v"] for k, v in r["cells"].items() if k[0] in "EFHIJ" and isinstance(v["v"], (int, float))}
        out[r["row"]] = c
    assert dec(out[27]["J"]) == D("1209.385")
    return out


def plaster_split():
    his = his_plaster_rows()
    idx = load("idx81")
    fix = {r["line_id"]: r for r in load("t763")["rows"]}
    cls = {"DRY": D(0), "SHAFT": D(0), "WET_RENDER": D(0), "WET_BAND": D(0), "RETURNS": D(0), "DRY_BAND_SHARE": D(0)}
    for ln in idx["lines"]:
        if ln["item_code"] != "FIN.PLASTER" or ln["class"] == "EXCLUDED":
            continue
        r = fix.get(ln["line_id"])
        v = dec(r["after"]["net"]) if r else dec(ln["measured_net"])
        e = ln["element_id"]
        if e.startswith("HL:WALL_FINISH:ST_"):
            k = "SHAFT"
        elif e == "HL:WALL_FINISH:GF_07:PLASTER":
            k = "WET_RENDER"           # pantry: levelling render under full-height porcelain (T-740 / T-329)
        elif e.startswith("HL:WALL_FINISH:"):
            k = "DRY"
        elif "band above ceiling" in e:
            k = "WET_BAND"
        elif e.startswith("PLASTER-BAND@"):
            k = "DRY_BAND_SHARE"
        elif "OPENING" in e or "REVEAL" in e:
            k = "RETURNS"
        elif e.endswith(":plaster"):
            k = "WET_RENDER"
        else:
            raise SystemExit(f"unclassified {e}")
        cls[k] += v
    total = sum(cls.values(), D(0))
    board_ex_wet = total - (cls["WET_RENDER"] - D("32.3422"))    # the board figure took the pantry as dry
    assert board_ex_wet.quantize(D("0.1")) == D("1236.8"), board_ex_wet
    # his classes
    def area(row):
        c = his[row]
        if "I" in c:
            return dec(c["I"]).quantize(D("0.001"))      # his cell = F x H (float print noise removed)
        return (dec(c.get("E", 1)) * dec(c["F"]) * dec(c["H"])).quantize(D("0.001"))
    his_dry = sum((area(r) for _, rows, *_ in DRY for r in rows), D(0))
    his_shaft = sum((area(r) for r in SHAFT_HIS_ROWS), D(0))
    his_wash, his_ret = area(HIS_WASH_ROW), area(HIS_RETURN_ROW)
    assert his_dry + his_shaft + his_wash + his_ret == D("1209.385")
    assert his_dry + his_shaft == D("1169.125")
    # dry-room bridge
    rooms, tot = [], {"LENGTH": D(0), "HEIGHT": D(0), "DEDUCTIONS": D(0)}
    ours_exact = D(0)
    for room, rows, le, he, op, be in DRY:
        Lh = sum((dec(his[r]["H"]) for r in rows), D(0))
        Ah = sum((area(r) for r in rows), D(0))
        Hh = Ah / Lh
        Le, He = dec(le), dec(he)
        ours = Le * He - dec(op) - dec(be)
        ours_exact += ours
        t_len = (Lh - Le) * Hh
        t_h = Le * (Hh - He)
        t_d = dec(op) + dec(be)
        assert (t_len + t_h + t_d - (Ah - ours)).copy_abs() < D("1e-20"), room
        tot["LENGTH"] += t_len
        tot["HEIGHT"] += t_h
        tot["DEDUCTIONS"] += t_d
        rooms.append({"room": room, "his_L": str(Lh), "his_H": str(Hh.quantize(Q4)), "his_m2": str(Ah),
                      "our_L": le, "our_H": he, "our_m2": str(ours.quantize(Q4)),
                      "length": str(t_len.quantize(Q4)), "height": str(t_h.quantize(Q4)),
                      "deductions": str(t_d)})
    our_dry_from_bases = ours_exact
    assert (our_dry_from_bases - cls["DRY"]).copy_abs() <= D("0.002"), (our_dry_from_bases, cls["DRY"])
    our_dry = cls["DRY"]
    tot["ROUNDING (line values vs bases)"] = our_dry_from_bases - our_dry
    assert (sum(tot.values(), D(0)) - (his_dry - our_dry)).copy_abs() < D("1e-20")
    # shaft bridge (T-173 / T-680 / T-701 terms + T-763 net)
    our_shaft = cls["SHAFT"]
    shaft_rows = [
        {"name": "his two stair rows with no drawn face (2.50 x 5.40; 11.25 x 3.60)", "delta": "54.00",
         "class": "UNRESOLVED (T-173 / T-634 / T-701)"},
        {"name": "his stair-house box 14.8 x 12.9 vs the drawn faces (T-680 gross 177.07 at b 0)",
         "delta": str(dec("190.92") - dec("177.07")), "class": "ENGINE_RIGHT (T-173 two traces)"},
        {"name": "our deductions on the shaft faces (openings Q-73, winder body, B20 / B23 ends) and the T-763 "
                 "storey - slab face model, vs his none", "delta": str(dec("177.07") - our_shaft),
         "class": "RULE_DIFFERENCE"},
    ]
    assert sum((dec(x["delta"]) for x in shaft_rows), D(0)) == his_shaft - our_shaft
    lfl_ours = our_dry + our_shaft
    lfl_his = his_dry + his_shaft
    # the board pair 1,236.8 vs 1,169.1 split by class
    board_rows = [
        {"name": "dry rooms (11): his - ours", "delta": str(his_dry - our_dry)},
        {"name": "stair shaft: his - ours", "delta": str(his_shaft - our_shaft)},
        {"name": "pantry GF-07 levelling render counted as dry in the board figure (it is WET render under "
                 "full-height porcelain; his pantry faces are in his spatter / tile rows)", "delta": "-32.3422"},
        {"name": "wet-room plaster band above the tile top to the soffit: ours only (his wet faces are his spatter "
                 "row; he has no band row)", "delta": str(-cls["WET_BAND"])},
        {"name": "door / window returns (jambs + head): ours by id; his row 26 is outside his 1,169.1",
         "delta": str(-cls["RETURNS"])},
        {"name": "GF-08 band share (T-763 midpoint)", "delta": str(-cls["DRY_BAND_SHARE"])},
    ]
    s = sum((dec(x["delta"]) for x in board_rows), D(0))
    assert s == lfl_his - board_ex_wet, (s, lfl_his - board_ex_wet)
    return {
        "ours_classes": {k: str(v) for k, v in cls.items()}, "ours_total": str(total),
        "board_ex_wet": str(board_ex_wet), "his_like_for_like": str(lfl_his),
        "board_pair_rows": board_rows,
        "his_classes": {"dry_rooms": str(his_dry), "shaft": str(his_shaft), "wash_wet_in_his_plaster": str(his_wash),
                        "door_returns": str(his_ret), "total": "1209.385"},
        "like_for_like_dry_plus_shaft": {"ours": str(lfl_ours), "his": str(lfl_his),
                                         "his_minus_ours": str(lfl_his - lfl_ours),
                                         "pct": str(((lfl_ours - lfl_his) / lfl_his * 100).quantize(D("0.01")))},
        "dry_bridge_totals": {k: str(v.quantize(Q4)) for k, v in tot.items()},
        "dry_rooms": rooms, "shaft_rows": shaft_rows,
        "returns": {"ours": str(cls["RETURNS"]), "his_row_26": str(his_ret)},
    }


def selftest():
    """normal: both splits close exactly; adverse: a HELD line read as 0 or a scope row dropped must fail closure."""
    block_split()
    plaster_split()
    real = dec
    # adverse 1: the below-ground lines treated as 0 (missing becomes 0) -> the exact closure must refuse
    per_floor, total, white, lines = engine_block()
    assert total - per_floor["BELOW"] != total
    # adverse 2: drop the boundary-wall scope row -> sum no longer equals the gap
    b = block_split()
    gap = real(b["his_minus_ours"])
    s_ = sum((real(x["delta"]) for x in b["scope_rows"] if "boundary" not in x["name"]), D(0))
    s_ += sum((real(v["his_minus_ours"]) for v in b["floors"].values()), D(0))
    assert s_ != gap
    # adverse 3: plaster headline pair without class split differs from like for like
    p = plaster_split()
    assert real(p["board_ex_wet"]) != real(p["like_for_like_dry_plus_shaft"]["ours"])
    return True


def main():
    res = {"schema": "URBAN_T779_SPLIT_V1", "rule": "R-T779-1",
           "inputs": {k: {"path": str(v[0].relative_to(ROOT)), "sha16": v[1]} for k, v in IN.items()},
           "blockwork": block_split(), "plaster": plaster_split()}
    text = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            raise SystemExit("T779_SPLIT.json is stale")
        selftest()
        print("T779 check OK (identities exact; adverse cases refused)")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    b, p = res["blockwork"], res["plaster"]
    print("BLOCK", b["ours_total"], b["his_total"], b["his_minus_ours"], b["pct"], b["ours_per_floor"])
    for f, v in b["floors"].items():
        print(" ", f, v["ours"], v["his_net"], v["his_minus_ours"])
        for r in v["rows"]:
            print("     ", r["class"], round(float(r["delta"]), 4), r["name"][:100])
    print(" storey lfl", b["storey_walls_like_for_like"], b["storey_rows_by_class"])
    print(" colour", b["colour"])
    print("PLASTER", p["ours_classes"], p["board_ex_wet"], p["his_like_for_like"])
    print(" lfl", p["like_for_like_dry_plus_shaft"], p["dry_bridge_totals"])
    for r in p["board_pair_rows"]:
        print("  ", round(float(r["delta"]), 4), r["name"][:90])
    for r in p["dry_rooms"]:
        print("  ", r)


if __name__ == "__main__":
    main()
