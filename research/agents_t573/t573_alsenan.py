"""T-573 development-villa build (research, unwired): CEILINGS vs the freelancer by room group and face class on the
candidate of record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 ceiling lines: arch_v3058 adds only FIN.WP.ROOF /
FIN.WP.ROOF_UPTURN lines, every other line byte-identical, T-507).

    .work/venv/bin/python -I research/agents_t573/t573_alsenan.py [--check]

Reads only merged repository files (sha256-pinned): the V3.0.57 line index (T-507), his rows as numbers
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: finishes workbook decor sheet, paint and plaster statements), the
T-283 r3 ceiling face ledger (stair zones, domes, class pieces, no-ceiling openings, cove runs) and the T-561 / T-567
outputs (stair soffit and pool soffit terms, carried, not re-measured). Writes out/T573_CEILING_RECONCILE.json; --check
rebuilds it byte-identical. No coordinate, no client name, no workbook text is written."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t573_rules as R  # noqa: E402

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
T283 = "research/agents_t283/CEILINGS_T283.csv"
T561 = "research/agents_t561/out/T561_PAINT_RECONCILE.json"
T567 = "research/agents_t567/t567_inputs.py"
PINS = {LINE_INDEX: "fed5141ea31bfdd9", RAW: "752c9f4e0c4546d0", T283: "10214b3dbffcf57a",
        T561: "f8d866b571e315ed", T567: "6fe7d700ea7e4c62"}
OUT = HERE / "out" / "T573_CEILING_RECONCILE.json"
D = R.D


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


# ---- candidate lines (V3.0.57 ids = V3.0.58) ------------------------------------------------------------------------
CODE_CLASS = {"FIN.CEILING": "BOARD", "FIN.CEILING.BULKHEAD": "BULKHEAD", "FIN.STAIR.SOFFIT": "STAIR_SOFFIT",
              "FIN.DOME.SOFFIT": "DOME", "FIN.PAINT.CEILING": "PAINT"}
STATUS = {"BOARD": "DRAWING-CONFIRMED", "BULKHEAD": "ASSUMED - OWNER-APPROVED", "PAINT": "ASSUMED - OWNER-APPROVED",
          "EXTERIOR_SOFFIT": "PROVISIONAL"}


def candidate_lines():
    lines = json.loads((ROOT / LINE_INDEX).read_text())["lines"]
    out = {}
    for x in lines:
        cls = CODE_CLASS.get(x["item_code"])
        if cls is None:
            continue
        if cls == "BOARD" and x["element_id"].startswith("SOFFIT:"):
            cls = "EXTERIOR_SOFFIT"
        held = x["class"] != "RELEASED"
        out[x["line_id"]] = {"class": cls, "unit": x["unit"], "element": x["element_id"],
                             "value": None if held else x["measured_net"],
                             "status": "HELD" if held else STATUS[cls]}
    return out


# ---- his rows (numbers only; row ids are file / sheet / cell) -------------------------------------------------------
# sheet keys: (file, sha256[:12] of the sheet title) -> our key (no workbook text in the repository)
SHEETS = {('FIN', '6e02ff830f3d'): 'DEC', ('PNT', '218bd58a9860'): 'PNT', ('PLS', '218bd58a9860'): 'PLS'}


def his_rows():
    d = json.loads((ROOT / RAW).read_text())
    cells = {}
    for x in d["rows"]:
        key = SHEETS.get((x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]))
        if key:
            for c, v in x["cells"].items():
                cells[f"{key}.{c}"] = v["v"]
    return cells


def _q(v):
    return D(repr(round(v, 6))) if isinstance(v, float) else D(v)


DEC_M2 = {"GF_DRY": [13, 14, 15, 16, 17], "1F_DRY": [21, 22, 23, 24, 25], "2F_DRY": [28, 29],
          "GF_WET": [42, 43, 44, 45, 46, 47, 48, 49, 50, 51], "1F_WET": [55, 56, 57, 58, 59, 60], "2F_WET": [63]}


def rows_table(cells):
    rows = {}
    for rr in DEC_M2.values():
        for r in rr:
            rows[f"DEC.D{r}"] = {"unit": "m2", "value": _q(cells[f"DEC.D{r}"])}
            rows[f"DEC.C{r}"] = {"unit": "lm", "value": _q(cells[f"DEC.C{r}"])}
    for c in ("I47", "I48", "I49", "I50", "I18", "I19"):
        rows[f"PNT.{c}"] = {"unit": "m2", "value": _q(cells[f"PNT.{c}"])}
    rows["PLS.I73"] = {"unit": "m2", "value": _q(cells["PLS.I73"])}
    # his own totals, asserted (decor H31 / H65 / G31 / G65; paint J51; stair rows J19)
    chk = {"DEC.H31": ("D", (13, 29)), "DEC.H65": ("D", (42, 63)), "DEC.G31": ("C", (13, 29)),
           "DEC.G65": ("C", (42, 63))}
    for cell, (col, (a, b)) in chk.items():
        s = sum((rows[f"DEC.{col}{r}"]["value"] for rr in DEC_M2.values() for r in rr if a <= r <= b), Decimal(0))
        if s != _q(cells[cell]):
            raise R.RuleError(f"his {cell} {cells[cell]} != his rows {s}")
    pnt = sum((rows[f"PNT.I{r}"]["value"] for r in (47, 48, 49, 50)), Decimal(0))
    if pnt != _q(cells["PNT.J51"]):
        raise R.RuleError(f"his paint J51 {cells['PNT.J51']} != rows {pnt}")
    if rows["PNT.I18"]["value"] + rows["PNT.I19"]["value"] != _q(cells["PNT.J19"]):
        raise R.RuleError("his stair soffit rows != J19")
    # his paint rows 47 / 48 are his decor totals; 49 / 50 his cove strips 0.10 x his cove runs
    if rows["PNT.I47"]["value"] != _q(cells["DEC.H31"]) or rows["PNT.I48"]["value"] != _q(cells["DEC.H65"]):
        raise R.RuleError("his paint decor rows are not his decor totals")
    return rows


# ---- face ledger (T-283 r3) ------------------------------------------------------------------------------------------
def t283():
    rows = list(csv.DictReader((ROOT / T283).open(encoding="utf-8")))
    cove = Decimal(0)
    cove_blank = []
    for r in rows:
        if r["SURFACE"].startswith("cove / cornice"):
            if r["QTY"]:
                cove += D(r["QTY"])
            else:
                cove_blank.append(r["FACE"])
    return {"cove_m": cove, "cove_blank": cove_blank,
            "face": {(r["FACE"], r["SURFACE"][:40]): r["QTY"] for r in rows}}


def F(ledger, face, surface_start):
    for (f, s), q in ledger["face"].items():
        if f == face and s.startswith(surface_start[:40]):
            return D(q)
    raise R.RuleError(f"T-283 face {face} / {surface_start!r} not found")


# ---- groups ---------------------------------------------------------------------------------------------------------
def L(*ids):
    return list(ids)


def board_groups(lg):
    lw = F(lg, "GF-RC99C2A/open", "no ceiling: opening in the slab above")
    st = F(lg, "GF-RC99C2A/open", "stair zone (stair face of the slab plan)") + \
        F(lg, "GF-RC99C2A/open", "stair zone beyond the stair face")
    band = F(lg, "GF-R9A05AA", "plan area under the slab")
    unl = F(lg, "GF-RF002DC", "plan area under the slab") + F(lg, "GF-R7B7A5D", "plan area under the slab")
    dome_bed = D("11.5808") + D("0.3418")       # T-283 DOMES_T283.csv: west over 1F-RB72F22, east over 1F-R3CFCFD
    dome_bath = D("1.4227") + D("1.2410") + D("0.4472")
    l1_held = F(lg, "1F-R78C367", "stair zone (stair face") + F(lg, "1F-R78C367", "under an open dome") + \
        F(lg, "1F-R78C367", "stair zone beyond the stair face")
    box = F(lg, "2F-R4D1B62", "held part of the ceiling")
    T271 = "T-271 r2b s.5 / T-283 r3 CEILINGS_T283.csv"
    G = [
        {"id": "GF reception + dining + entrance (incl. pantry, south dining piece)", "unit": "m2",
         "lines": L("L-eb3be58fc760b39f0e38", "L-1624ef49fd8b69cc2bcb", "L-ba5ea9bd4bbd2f713ea0",
                    "L-4b41debf41fff9e3faae"),
         "rows": ["DEC.D13", "DEC.D15"],
         "pairing": "his two rows name reception + dining and the entrance (no dimensions); T-271: he prices the pantry "
                    "(11.755 = 8.955 + 2.800) dry inside this row",
         "causes": [
             {"label": "no ceiling under the slab openings (light well 13.392 + pocket 1.551, S-OPENING outlines): his "
                       "row ceils them", "verdict": "ENGINE_RIGHT", "amount": -lw, "source": T271},
             {"label": "stair ST-02 zone under the slab + beyond the stair face (stair soffit class, T-281)",
              "verdict": "HELD", "amount": -st, "bound": (Decimal(0), st), "source": T271 + "; his row covers it"},
             {"label": "garden band 1.30 m under the 1F slab, class P-2 (designer D-48)", "verdict": "HELD",
              "amount": -band, "bound": (Decimal(0), band), "source": "T-283 r3 / T-427; his row covers it"},
             {"label": "west strip OP-003 3.80 x 0.20 (line L-4b41de HELD, no ceiling reading)", "verdict": "HELD",
              "amount": D("-0.760"), "bound": (Decimal(0), D("0.760")), "source": "T-431 / T-435"},
             {"label": "two unlabelled GF spaces GF-RF002DC 3.600 + GF-R7B7A5D 1.560 (class HELD; inside his row "
                       "not established)", "verdict": "HELD", "amount": Decimal(0), "bound": (Decimal(0), unl),
              "source": "T-283 r3"},
             {"label": "remainder: his row has no dimensions (T-271 at R2 found +1.182 not traceable on its own "
                       "region); not separable", "verdict": "UNRESOLVED", "amount": None, "source": "this run"}]},
        {"id": "GF service stair room ST-01 (stairwell line HELD blank)", "unit": "m2",
         "lines": L("L-2175a965bb7c48a50e6c"), "rows": [],
         "causes": [{"label": "stair top under the slab 1.750 HELD (no finish printed) + soffit pieces (counted once, "
                              "in the STAIR soffit table, never here); no decor row of his", "verdict": "HELD",
                     "amount": Decimal(0), "bound": (Decimal(0), None), "source": "T-283 r3 / T-335 FILL"}]},
        {"id": "GF diwaniya", "unit": "m2", "lines": L("L-10cea378faf69d8d60b4"), "rows": ["DEC.D16"],
         "causes": [{"label": "room size, finish vs structural face (his row has no sub-dimensions)",
                     "verdict": "TOLERANCE", "amount": None, "source": "T-271 / T-335"}]},
        {"id": "GF master bedroom", "unit": "m2", "lines": L("L-1415e7d55fbf3f25af2c"), "rows": ["DEC.D14"],
         "causes": [{"label": "room size, finish vs structural face", "verdict": "TOLERANCE", "amount": None,
                     "source": "T-271 / T-335"}]},
        {"id": "GF driver room", "unit": "m2", "lines": L("L-4a8e924113005f50aad0"), "rows": ["DEC.D17"],
         "causes": [{"label": "room size", "verdict": "TOLERANCE", "amount": None, "source": "T-271 / T-335"}]},
        {"id": "GF wet rooms (kitchen, wash, 8 baths / W.C.; 10 lines = his 10 rows)", "unit": "m2",
         "lines": L("L-99c19f55c75e05a9269d", "L-ca375a1aa007cced0c4f", "L-1872aa0960386048f846",
                    "L-c36100853e30f91fe621", "L-76e2f18fcd457f79aa2b", "L-d8d08b98c7700716d224",
                    "L-cbc44c359f812d7d498e", "L-f753591a0d8963fa0126", "L-3d50c68ce33c30b9ea7a",
                    "L-dee48a60f23266badabd"),
         "rows": [f"DEC.D{r}" for r in DEC_M2["GF_WET"]],
         "pairing": "storey + wet class: his rows carry no ids beyond kitchen / wash / baths; the group total does "
                    "not depend on a room-by-room pairing (R-T568-1 (d))",
         "causes": [{"label": "room sizes (sum of 10)", "verdict": "TOLERANCE", "amount": None,
                     "source": "T-271 (rest -0.054 agree)"}]},
        {"id": "1F living (group line + 2 blank parents)", "unit": "m2",
         "lines": L("L-43bf1f869e1588f1d3bd", "L-fc116bb666b184740090", "L-35341ff2e6a848b9436b"),
         "rows": ["DEC.D21"],
         "causes": [
             {"label": "double-height ceiling over the light-well footprint (1F roof slab closed over the void): in "
                       "ours, his row omits it; the normal / double-height split is not drawn, so the term is the "
                       "group gap (never pro rata, R-T284-1)", "verdict": "ENGINE_RIGHT", "amount": None,
              "source": "T-271 verdict (1F double-height ceiling) / T-283 r3"},
             {"label": "stair zone 10.725 + B23 foot 0.1725 + east dome 14.0359: in neither (his row is smaller)",
              "verdict": "HELD", "amount": Decimal(0), "bound": (Decimal(0), l1_held), "source": "T-283 r3"}]},
        {"id": "1F bedrooms 1-4", "unit": "m2",
         "lines": L("L-69ebc828b4c61f4ea348", "L-ac337bf041e8184a315c", "L-cbe047c180804fe1ca65",
                    "L-9da183ba435f72f62897"),
         "rows": ["DEC.D22", "DEC.D23", "DEC.D24", "DEC.D25"],
         "causes": [
             {"label": "open dome positions over the rooms (west 11.5808 over 1F-RB72F22, east 0.3418): his room rows "
                       "cover them (designer DCR-4, Q-44 A)", "verdict": "HELD", "amount": -dome_bed,
              "bound": (Decimal(0), dome_bed), "source": "T-283 DOMES_T283.csv"},
             {"label": "room sizes (T-208 UNRESOLVED; 1F-R0E919A second-room acceptance item open)",
              "verdict": "UNRESOLVED", "amount": None, "source": "T-271 / T-208"}]},
        {"id": "1F dressing (1.650 x 1.800)", "unit": "m2", "lines": L("L-d0a131bb108d5a3bb215"), "rows": [],
         "causes": [{"label": "drawn space, no row of his (T-295 finding c)", "verdict": "ENGINE_RIGHT",
                     "amount": None, "source": "T-271 / T-295 / T-284"}]},
        {"id": "1F wet rooms (laundry + 5 baths; 6 lines = his 6 rows)", "unit": "m2",
         "lines": L("L-788395228a7c93622567", "L-05b1d88f06c38f962cb6", "L-c25a76ebdaab3ec65076",
                    "L-c85ec92c5f1e50dadd11", "L-41145bdf5e4088f2fefa", "L-cf849a125a14605a4e96"),
         "rows": [f"DEC.D{r}" for r in DEC_M2["1F_WET"]],
         "causes": [
             {"label": "open dome positions over three baths (west 1.4227 + 1.2410, east 0.4472): his rows cover "
                       "them", "verdict": "HELD", "amount": -dome_bath, "bound": (Decimal(0), dome_bath),
              "source": "T-283 DOMES_T283.csv"},
             {"label": "room sizes", "verdict": "TOLERANCE", "amount": None, "source": "T-271 (+0.235)"}]},
        {"id": "2F maid room", "unit": "m2", "lines": L("L-7531772e1581b35eea5f"), "rows": ["DEC.D28"],
         "causes": [{"label": "room size", "verdict": "TOLERANCE", "amount": None, "source": "T-271"}]},
        {"id": "2F stair hall lobby (his 'corridor')", "unit": "m2",
         "lines": L("L-10e79bd48a8fbfbf14aa", "L-dd6930fd19ca1b908c56"), "rows": ["DEC.D29"],
         "causes": [
             {"label": "stair box top 12.9742 HELD (Q-72): his corridor 7.70 cannot hold the whole box (7.70 < "
                       "12.974); which part, if any, is in his row is not established", "verdict": "HELD", "amount": Decimal(0), "bound": (Decimal(0), box),
              "source": "T-271 / T-283 r3"},
             {"label": "his corridor 7.70 has no dimensions vs the drawn lobby 5.6258", "verdict": "UNRESOLVED",
              "amount": None, "source": "T-271 (-2.074)"}]},
        {"id": "2F W.C.", "unit": "m2", "lines": L("L-1bd4ec39660768d22677"), "rows": ["DEC.D63"],
         "causes": [{"label": "room size", "verdict": "TOLERANCE", "amount": None, "source": "T-271"}]},
    ]
    return G


def class_groups(lines, lg, t561):
    cove_rows = [f"DEC.C{r}" for rr in DEC_M2.values() for r in rr]
    bulk = [k for k, v in lines.items() if v["class"] == "BULKHEAD"]
    held_bulk = D("6.5428") * D("0.15")          # owner method run x 0.15 on the T-431 edge (bound only)
    soff = [k for k, v in lines.items() if v["class"] == "STAIR_SOFFIT"]
    dome = [k for k, v in lines.items() if v["class"] == "DOME"]
    ext = sorted(k for k, v in lines.items() if v["class"] == "EXTERIOR_SOFFIT")
    s_held, s_res = D(t561["held"]), D(t561["unresolved"])
    return [
        {"id": "BULKHEAD vertical faces (all rooms)", "unit": "m2", "lines": sorted(bulk), "rows": [],
         "causes": [
             {"label": "owner bulkhead faces (free beam edge x 0.15, Q-48 A + Q-43): he lists no bulkhead",
              "verdict": "NOT_IN_HIS_ROWS", "amount": None, "source": "T-283 r3 / T-284"},
             {"label": "GF-RFD4E1D bulkhead HELD (edge 6.5428 m, depth not decided; owner-method bound 6.5428 x "
                       "0.15)", "verdict": "HELD", "amount": Decimal(0), "bound": (Decimal(0), held_bulk),
              "source": "T-431"}]},
        {"id": "COVE / cornice runs (lm)", "unit": "lm", "lines": [], "rows": cove_rows,
         "causes": [{"label": "no cove / cornice detail drawn: no candidate line; T-283 ledger runs HELD "
                              f"{lg['cove_m']} m where a run is printed, {len(lg['cove_blank'])} faces blank", "verdict": "HELD", "amount": None,
                     "bound": (Decimal(0), None), "source": "T-283 r3 / T-284 (coves 288.640 m)"}]},
        {"id": "STAIR soffits ST-01 / ST-02 (his wall-paint rows 18-19)", "unit": "m2", "lines": sorted(soff),
         "rows": ["PNT.I18", "PNT.I19"],
         "causes": [
             {"label": "T-281 true soffit (method D) 17.243246 + 4.905788, lines HELD blank", "verdict": "HELD",
              "amount": -s_held, "bound": (s_held, None), "source": "T-561 out (carried)"},
             {"label": "his sizes vs the T-281 rows + T-281 rows still HELD (ST-01 1.50 plan, ST-02 RS-C 4.443156 "
                       "plan)", "verdict": "UNRESOLVED", "amount": -s_res, "source": "T-561 out (carried)"}]},
        {"id": "DOME intrados (2 lines)", "unit": "m2", "lines": sorted(dome), "rows": [],
         "causes": [{"label": "dome finish HELD blank (designer DCR-4); he prices no dome ceiling", "verdict": "HELD",
                     "amount": Decimal(0), "bound": (Decimal(0), None), "source": "T-284"}]},
        {"id": "EXTERIOR soffits (5 lines) vs his plaster row 73", "unit": "m2", "lines": ext, "rows": ["PLS.I73"],
         "causes": [
             {"label": "pool-court soffit PL-03: his 2 x 3.14 x 3.05 = 19.154 vs the measured 12.834",
              "verdict": "ENGINE_RIGHT", "amount": D("12.834") - D("19.154"), "source": "T-567 (carried)"},
             {"label": "soffits PL-01 / PL-02 / PL-04 / PL-05 over outside air (T-121 / T-127): no row of his in "
                       "his decor, paint or plaster statements", "verdict": "NOT_IN_HIS_ROWS", "amount": None,
              "source": "T-567 row map / this run"}]},
    ]


def fill_remainders(groups, lines, rows):
    """The one cause per group whose amount is None (if any) takes the exact remainder (named; never unnamed)."""
    for g in groups:
        ours = sum((D(lines[l]["value"]) for l in g["lines"] if lines[l]["value"] is not None), Decimal(0))
        his = sum((rows[r]["value"] for r in g["rows"]), Decimal(0))
        open_ = [c for c in g["causes"] if c["amount"] is None]
        if len(open_) > 1:
            raise R.RuleError(f"group {g['id']}: at most one remainder cause, {len(open_)} found")
        if not open_:
            continue                       # every term stated: R.reconcile checks the exact closure
        open_[0]["amount"] = ours - his - sum((D(c["amount"]) for c in g["causes"] if c["amount"] is not None),
                                              Decimal(0))
    return groups


def paint_check(lines):
    """FIN.PAINT.CEILING of each room = its BOARD + BULKHEAD lines (HELD bulkhead not added)."""
    by_room = {}
    for lid, v in lines.items():
        room = v["element"].split(":")[0]
        by_room.setdefault(room, []).append(v)
    rows = []
    for room, vs in sorted(by_room.items()):
        paint = [v for v in vs if v["class"] == "PAINT"]
        if not paint:
            continue
        b = sum((D(v["value"]) for v in vs if v["class"] == "BOARD" and v["value"] is not None), Decimal(0))
        k = sum((D(v["value"]) for v in vs if v["class"] == "BULKHEAD" and v["value"] is not None), Decimal(0))
        p = D(paint[0]["value"])
        if (p - (b + k)).copy_abs() > D("0.000002"):
            raise R.RuleError(f"{room}: ceiling paint {p} != board {b} + bulkhead {k}")
        rows.append({"room": room, "paint": str(p), "board": str(b), "bulkhead": str(k)})
    return rows


def S(x):
    return None if x is None else str(x)


def build():
    pins()
    lines = candidate_lines()
    rows = rows_table(his_rows())
    lg = t283()
    t = json.loads((ROOT / T561).read_text())
    blob = json.dumps(t)
    t561 = {"held": "22.149034", "unresolved": "17.840966"}
    for v in t561.values():
        if v not in blob:
            raise R.RuleError(f"T-561 term {v} not in its output")
    bg = fill_remainders(board_groups(lg), lines, rows)
    cg = fill_remainders(class_groups(lines, lg, t561), lines, rows)
    board_lines = {k: v for k, v in lines.items() if v["class"] == "BOARD"}
    board_rows = {k: v for k, v in rows.items() if k.startswith("DEC.D")}
    tb = R.reconcile(bg, board_lines, board_rows)
    other_lines = {k: v for k, v in lines.items() if v["class"] not in ("BOARD", "PAINT")}
    other_rows = {k: v for k, v in rows.items() if not k.startswith("DEC.D") and k not in
                  ("PNT.I47", "PNT.I48", "PNT.I49", "PNT.I50")}
    tc = R.reconcile(cg, other_lines, other_rows)
    # paint view
    pcheck = paint_check(lines)
    ours_p = sum((D(v["value"]) for v in lines.values() if v["class"] == "PAINT"), Decimal(0))
    his_p = sum((rows[f"PNT.I{r}"]["value"] for r in (47, 48, 49, 50)), Decimal(0))
    board_gap = tb["totals"]["m2"]["ours"] - tb["totals"]["m2"]["his"]
    bulk = sum((D(v["value"]) for v in lines.values() if v["class"] == "BULKHEAD" and v["value"] is not None),
               Decimal(0))
    cove_strip = rows["PNT.I49"]["value"] + rows["PNT.I50"]["value"]
    pg = [{"id": "CEILING PAINT (31 lines) vs his decor paint rows 47-50", "unit": "m2",
           "lines": sorted(k for k, v in lines.items() if v["class"] == "PAINT"),
           "rows": ["PNT.I47", "PNT.I48", "PNT.I49", "PNT.I50"],
           "causes": [{"label": "the board gap, room by room as the BOARD table", "verdict": "BY_TABLE",
                       "amount": board_gap, "source": "BOARD table (its own verdicts)"},
                      {"label": "bulkhead faces painted in ours; he paints none", "verdict": "NOT_IN_HIS_ROWS",
                       "amount": bulk, "source": "BULKHEAD table"},
                      {"label": "his cove-light strips 0.10 x 282.85 + 0.10 x 144.60 (no detail drawn; owner Q-57 A "
                                "mod: actual paintable surfaces)", "verdict": "RULE_DIFFERENCE", "amount": -cove_strip,
                       "source": "T-284 s.4"},
                      {"label": "GF-RFD4E1D bulkhead paint HELD with its bulkhead", "verdict": "HELD",
                       "amount": Decimal(0), "bound": (Decimal(0), D("6.5428") * D("0.15")), "source": "T-431"}]}]
    paint_lines = {k: v for k, v in lines.items() if v["class"] == "PAINT"}
    paint_rows = {k: rows[k] for k in pg[0]["rows"]}
    tp = R.reconcile(pg, paint_lines, paint_rows)
    lfl = R.like_for_like(tb)

    def G(t):
        return [{"id": g["id"], "unit": g["unit"], "ours": S(g["ours"]), "his": S(g["his"]), "gap": S(g["gap"]),
                 "pct": S(g["pct"]), "held_bound": [S(g["held_bound"][0]), S(g["held_bound"][1])],
                 "lines": g["lines"], "rows": g["rows"],
                 "causes": [{"label": c["label"], "verdict": c["verdict"], "amount": S(D(c["amount"])),
                             **({"bound": [S(c["bound"][0]), S(c["bound"][1])]} if "bound" in c else {}),
                             "source": c["source"]} for c in g["causes"]]} for g in t["groups"]]

    def tot(t):
        return {u: {"ours": S(v["ours"]), "his": S(v["his"]), "gap": S(v["ours"] - v["his"]),
                    "pct": S(((v["ours"] - v["his"]) / v["his"] * 100).quantize(Decimal("0.01"))) if v["his"] else None}
                for u, v in t["totals"].items()}

    by_verdict = {}
    for g in tb["groups"]:
        for c in g["causes"]:
            by_verdict[c["verdict"]] = by_verdict.get(c["verdict"], Decimal(0)) + D(c["amount"])
    return {
        "schema": "T573_CEILING_RECONCILE_V1", "rule": "R-T573-1", "candidate": "ARCH_TAKEOFF_V3.0.58",
        "line_index": LINE_INDEX, "pins": PINS,
        "board": {"groups": G(tb), "totals": tot(tb), "by_verdict": {k: S(v) for k, v in sorted(by_verdict.items())},
                  "like_for_like_no_held": {"ours": S(lfl[0]), "his": S(lfl[1]), "gap": S(lfl[2]), "pct": S(lfl[3])}},
        "classes": {"groups": G(tc), "totals": "none: each face class is its own comparison (R-T573-1 (d))"},
        "paint": {"groups": G(tp), "totals": tot(tp), "room_check": pcheck},
        "cove_ledger_m": S(lg["cove_m"]), "cove_ledger_blank_faces": len(lg["cove_blank"]),
        "his_cove_paint_run_note": "his paint row 50 uses 144.60 m against his decor total 144.61 m (0.001 m2)",
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != out:
            raise SystemExit("T573 output differs from a rebuild")
        print("T573 check: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
