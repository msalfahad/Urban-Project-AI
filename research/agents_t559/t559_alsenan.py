"""T-559 development-villa run (research, unwired): T-550's UNRESOLVED 25.9224 m2 taken further to physical causes
(openings opening by opening, R-T559-1) and the parapet edge-member ownership check (R-T559-2).

    .work/venv/bin/python -I research/agents_t559/t559_alsenan.py [--his .work/private/t559/his_openings.json] [--write]

Inputs (merged repository files): research/agents_t550/out/T550_UNRESOLVED_RESTATED.json (the 25.9224 by name),
research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv (engine deductions per wall and floor), research/agents_t292/
OPENING_DEDUCTIONS_T292.csv (opening sizes and their sources, read into ENGINE_OPENINGS below and asserted),
research/agents_t507/out/LINE_INDEX_V3_0_57.json (the V3.0.58 beam lines, byte-identical), research/agents_t319/
V3_0_23_RUNS_T319.csv (parapet runs). Private (never tracked): his opening rows (count x width x height per floor and
section), read from his masonry workbook on Drive into .work/private/t559/his_openings.json. Without it the opening
table is not rebuilt (the run says so); the edge-member check needs no private file.
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t559_rules as R  # noqa: E402

T550 = ROOT / "research/agents_t550/out/T550_UNRESOLVED_RESTATED.json"
REG_V2 = ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv"
T292 = ROOT / "research/agents_t292/OPENING_DEDUCTIONS_T292.csv"
LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RUNS = ROOT / "research/agents_t319/V3_0_23_RUNS_T319.csv"
OUT = HERE / "out" / "T559_LEFTOVER.json"
PRIVATE_DEFAULT = ROOT.parent / "private" / "t559" / "his_openings.json"   # .work/private when run from a worktree

# ---- engine openings: id -> (group, width m, deduction m2 or None (HELD), height basis, source) -------------------
# Sizes from T-292 OPENING_DEDUCTIONS (merged_size / owner_ded); the deduction per wall sums to register V2.
# Group = his section: GF / 1F / 2F (external + 15 cm), '20CM' = his 20 cm section with no floor (the lift-shaft walls).
ENGINE_OPENINGS = {
    # GF (register V2 42.660 = 40.4615 + D-GF-08 2.2000 - 0.0015 print of the GF-W04 wall total 4.7115 as 4.710)
    "D-GF-01": ("GF", "1.0", "2.2000", "Q55C"), "D-GF-03": ("GF", "0.9", "1.9800", "Q55C"),
    "D-GF-05": ("GF", "1.0", "2.2000", "Q55C"), "D-GF-06": ("GF", "1.0", "2.2000", "Q55C"),
    "D-GF-09": ("GF", "0.9", "1.9800", "Q55C"), "W01": ("GF", "1.2", "2.4000", "PRINTED"),
    "W04": ("GF", "0.6", "0.4800", "PRINTED"), "W05": ("GF", "0.6", "0.4800", "PRINTED"),
    "W06": ("GF", "0.6", "0.4800", "PRINTED"), "W07": ("GF", "0.6", "0.4800", "PRINTED"),
    "W08": ("GF", "1.501", "2.2515", "PRINTED"), "W09": ("GF", "1.5", "2.2500", "PRINTED"),
    "W10": ("GF", "1.0", "1.5000", "PRINTED"), "W11": ("GF", "1.955", "4.2900", "PRINTED"),
    "W12": ("GF", "1.95", "4.2900", "PRINTED"),
    "D-GF-02": ("GF", "0.8", "1.7600", "Q55C"), "D-GF-04": ("GF", "0.8", "1.7600", "Q55C"),
    "D-GF-10": ("GF", "0.8", "1.7600", "Q55C"), "D-GF-11": ("GF", "0.8", "1.7600", "Q55C"),
    "D-GF-12": ("GF", "0.8", "1.7600", "Q55C"), "D-GF-13": ("GF", "1.0", "2.2000", "Q55C"),
    "D-GF-07": ("GF", "2.0", None, "HELD"), "D-GF-14": ("GF", "0.8", None, "HELD"),
    # 20 cm lift-shaft walls, stacked GF / 1F / 2F (GF-W08, 1F-W07, 2F-W00): landing doors HELD, lobby door D-GF-08
    "L-GF-01": ("20CM", "1.0", None, "HELD"), "L-1F-01": ("20CM", "1.0", None, "HELD"),
    "L-2F-01": ("20CM", "1.0", None, "HELD"), "D-GF-08": ("20CM", "1.0", "2.2000", "Q55C"),
    # 1F (register V2 41.851)
    "W15": ("1F", None, "4.3630", "OUTLINE"), "W16": ("1F", None, "4.3630", "OUTLINE"),
    "W18": ("1F", "0.5", "1.0800", "PRINTED"), "W13": ("1F", "1.2", "2.7600", "PRINTED"),
    "W14": ("1F", "2.45", "3.9200", "PRINTED"), "W19": ("1F", "0.6", "0.4800", "PRINTED"),
    "W20": ("1F", "0.6", "0.4800", "PRINTED"), "W24": ("1F", "1.55", "2.3250", "PRINTED"),
    "W21": ("1F", "0.6", "0.4800", "PRINTED"), "W22": ("1F", "0.6", "0.4800", "PRINTED"),
    "W23": ("1F", "0.6", "0.4800", "PRINTED"), "W25": ("1F", "1.0", "1.5000", "PRINTED"),
    "D-1F-05": ("1F", "0.9", "1.9800", "Q55C"), "D-1F-01": ("1F", "0.8", "1.7600", "Q55C"),
    "D-1F-03": ("1F", "1.0", "2.2000", "Q55C"), "D-1F-08": ("1F", "0.9", "1.9800", "Q55C"),
    "D-1F-09": ("1F", "0.9", "1.9800", "Q55C"), "D-1F-06": ("1F", "0.8", "1.7600", "Q55C"),
    "D-1F-10": ("1F", "0.8", "1.7600", "Q55C"), "D-1F-07": ("1F", "0.8", "1.7600", "Q55C"),
    "D-1F-02": ("1F", "1.0", "2.2000", "Q55C"), "D-1F-04": ("1F", "0.8", "1.7600", "Q55C"),
    "W17": ("1F", "3.286", None, "HELD"),
    # 2F (register V2 11.595)
    "W27": ("2F", "1.0", "1.5000", "PRINTED"), "W28": ("2F", "0.6", "0.4800", "PRINTED"),
    "W29": ("2F", "1.2", "1.8000", "PRINTED"), "D-2F-01": ("2F", "1.0", "2.2000", "Q55C"),
    "D-2F-02": ("2F", "0.9", "1.9800", "Q55C"), "W26": ("2F", None, "1.8750", "OUTLINE"),
    "D-2F-03": ("2F", "0.8", "1.7600", "Q55C"),
}
REGISTER_FLOOR = {"GF": "42.660", "1F": "41.851", "2F": "11.595"}
GF_W04_PRINT = Decimal("-0.0015")     # register V2 prints the GF-W04 wall total 4.7115 (D-GF-03 + W04 + W08) as 4.710

# matches by floor, wall section and size class (his rows carry no id): consistent, not proven, each named
PAIRS = {
    "GF": [("D-GF-01", "u1", "ext door 1.00"), ("D-GF-05", "u9", "ext door 1.00"), ("D-GF-06", "u13", "ext door 1.00"),
           ("D-GF-03", "u15", "his fourth ext door 1.00 vs a 0.90 door (D-GF-03 or D-GF-09: the other is engine-only)"),
           ("W04", "u2", "0.60 x 0.80"), ("W05", "u3", "0.60 x 0.80 (engine at its 0.48 m2 cap)"),
           ("W06", "u4", "0.60 x 0.80"), ("W07", "u5", "0.60 x 0.80"), ("W10", "u6", "1.00 window"),
           ("W08", "u7", "1.50 window"), ("W09", "u14", "1.50 window"),
           ("D-GF-07", "u8", "main door 2.00 (engine HELD opening in held wall GF-W15)"),
           ("W01", "u10", "1.20 window"), ("W11", "u11", "1.95 glazed (h 2.20 drawing-confirmed T-207, cap 4.29)"),
           ("W12", "u12", "1.95 glazed (h 2.20 drawing-confirmed T-207, cap 4.29)"),
           ("D-GF-02", "u16", "15 cm door 0.80"), ("D-GF-04", "u17", "15 cm door 0.80"),
           ("D-GF-10", "u18", "15 cm door 0.80"), ("D-GF-11", "u19", "15 cm door 0.80"),
           ("D-GF-12", "u20", "15 cm door 0.80"), ("D-GF-14", "u21", "15 cm door 0.80 (engine HELD, wall GF-W30)"),
           ("D-GF-13", "u22", "15 cm door 1.00")],
    "20CM": [("L-GF-01", "v1", "lift landing door, GF (HELD height, wall GF-W08)"),
             ("L-1F-01", "v2", "lift landing door, 1F (HELD, wall 1F-W07)"),
             ("L-2F-01", "v3", "lift landing door, 2F (HELD, wall 2F-W00)"),
             ("D-GF-08", "v4", "lift-lobby door in the 20 cm wall GF-W08 (engine 1.00 wide, his 1.10)")],
    "1F": [("W25", "e1", "1.00 window"), ("W19", "e2", "0.60 x 0.80"), ("W20", "e3", "0.60 x 0.80"),
           ("W21", "e4", "0.60 x 0.80"), ("W22", "e5", "0.60 x 0.80"), ("W23", "e6", "0.60 x 0.80"),
           ("W17", "e8", "arched opening 3.286 (engine outline HELD 4.4361 .. 9.858, wall 1F-W25)"),
           ("W15", "e9", "arched window: true outline (UP-OPEN-ARCH-001 v1.1) vs his rectangle"),
           ("W16", "e10", "arched window: true outline vs his rectangle"), ("W24", "e11", "1.55 window"),
           ("W14", "e12", "2.45 window"), ("W13", "e13", "1.20 window"),
           ("D-1F-01", "f1", "door 0.80"), ("D-1F-04", "f2", "door 0.80"), ("D-1F-06", "f3", "door 0.80"),
           ("D-1F-07", "f4", "door 0.80"), ("D-1F-05", "f5", "door 0.90 (20 cm wall 1F-W07; his 15 cm section)"),
           ("D-1F-08", "f6", "door 0.90"), ("D-1F-09", "f7", "door 0.90"),
           ("D-1F-03", "f8", "his fourth 0.90 door vs a 1.00 door (D-1F-02 or D-1F-03)")],
    "2F": [("W27", "s1", "1.00 window"), ("W29", "s2", "1.20 window"), ("W28", "s3", "0.60 x 0.80"),
           ("D-2F-01", "s4", "door 1.00"), ("W26", "s5", "arched outline vs his rectangle"),
           ("D-2F-03", "t1", "door 0.80"), ("D-2F-02", "t2", "door 0.90 (20 cm wall 2F-W05; his 15 cm section)")],
}

# ---- R-T559-2: structural bands under each parapet run (arch layer-5 face lines over ST7757 route G bands) ---------
# Registration: P7757 column handles -> ST7757 columns (03_ARCH_STRUCTURAL_REGISTRATION.csv pairs), one translation per
# floor plan (spread 0.0 mm on 30 / 20 / 9 columns); the GF roof slab sheet is the 1F-roof sheet + 38.724 m in x (19
# columns). A face line is over a band when >= 0.25 m of it lies inside the band outline buffered 0.12 m, parallel.
EDGE_BANDS = [
    # storey = structural roof-slab sheet; run = T-311 / T-319 run; handles = P7757 face lines; covered m along the band
    {"storey": "GF", "band": "BAND0014", "mark": "CB7 20x75", "run": "ANNEX NE-6 (+4.30)", "handles": "B34 / AC7", "covered_m": "11.800"},
    {"storey": "GF", "band": "BAND0028", "mark": "B9 20x75", "run": "ANNEX SE-1 (+4.30)", "handles": "B37 / B2D / B2E", "covered_m": "6.300"},
    {"storey": "GF", "band": "BAND0027", "mark": "B2 20x40", "run": "ANNEX SW-1 (+4.30)", "handles": "B41 / B28", "covered_m": "2.900"},
    {"storey": "GF", "band": "BAND0029.2", "mark": "CB6 20x75", "run": "ANNEX SW-3 (+4.30)", "handles": "B35 / B36", "covered_m": "5.819"},
    {"storey": "GF", "band": "BAND0039", "mark": "CB8 30x75", "run": "GF NE-4 (+5.50)", "handles": "B25 / AC7", "covered_m": "3.372"},
    {"storey": "GF", "band": "BAND0040.1", "mark": "CB8 30x75", "run": "GF NE-4 (+5.50)", "handles": "B25 / AC7", "covered_m": "5.983"},
    {"storey": "GF", "band": "BAND0040.2", "mark": "CB8 30x75", "run": "GF NE-4 (+5.50)", "handles": "B25 / AC7", "covered_m": "6.589"},
    {"storey": "GF", "band": "BAND0015", "mark": "B1 20x40", "run": "GF NE-4 (+5.50)", "handles": "B25 / AC7", "covered_m": "1.385"},
    {"storey": "GF", "band": "BAND0041.1", "mark": "CB1 35x75", "run": "GF NW-7 (+5.50)", "handles": "B33 / B30 / C85 / C86", "covered_m": "7.319"},
    {"storey": "GF", "band": "BAND0032", "mark": "B1 20x40", "run": "GF SW-9 (+5.50)", "handles": "BDB / BDC", "covered_m": "0.864"},
    {"storey": "1F", "band": "BAND0002.1", "mark": "B4 20x50", "run": "1F NE-2 (+9.70)", "handles": "127F / 1285", "covered_m": "4.050"},
    {"storey": "1F", "band": "BAND0027.1", "mark": "CB11 30x75", "run": "1F NE-2 (+9.70)", "handles": "127F / 1285", "covered_m": "6.948"},
    {"storey": "1F", "band": "BAND0027.2", "mark": "CB11 30x75", "run": "1F NE-2 (+9.70)", "handles": "127F / 1285", "covered_m": "2.891"},
    {"storey": "1F", "band": "BAND0027.3", "mark": "CB11 30x75", "run": "1F NE-2 (+9.70)", "handles": "127F / 1285", "covered_m": "3.539"},
    {"storey": "1F", "band": "BAND0014", "mark": "unlabelled 0.20 (BM-1F-034)", "run": "1F SE-1 (+9.70)", "handles": "12C4 / 12C7", "covered_m": "7.500"},
    {"storey": "1F", "band": "BAND0001.3", "mark": "CB9 20x50", "run": "1F SW-3 (+9.70)", "handles": "1273 / 1278", "covered_m": "2.340"},
    {"storey": "1F", "band": "BAND0001.4", "mark": "CB9 20x50", "run": "1F SW-3 (+9.70)", "handles": "1273 / 1278", "covered_m": "3.790"},
    {"storey": "1F", "band": "BAND0031.1", "mark": "B23 45x75", "run": "1F SW-2 (+9.70)", "handles": "12B9", "covered_m": "2.920"},
    {"storey": "1F", "band": "BAND0031.2", "mark": "B23 45x75", "run": "1F SW-2 (+9.70)", "handles": "12B9", "covered_m": "0.644"},
    {"storey": "1F", "band": "BAND0018.1", "mark": "CB12 25x75", "run": "1F NW (sea side, +9.70)", "handles": "12A7 / 1308 / 1322 / 1323", "covered_m": "5.745"},
    {"storey": "1F", "band": "BAND0018.2", "mark": "CB12 25x75", "run": "1F NW (sea side, +9.70)", "handles": "12A7 / 12A6", "covered_m": "5.195"},
    {"storey": "1F", "band": "BAND0025", "mark": "unlabelled 0.349 (BM-1F-036)", "run": "1F NW (sea side, +9.70)", "handles": "1318 / 1319", "covered_m": "3.959"},
    {"storey": "1F", "band": "BAND0023", "mark": "unlabelled 0.30 (BM-1F-035)", "run": "1F NW corner (+9.70)", "handles": "1309 / 130B", "covered_m": "0.900"},
    # +13.90 roof: its outer outline 8.10 x 6.80 (his 29.80 = 2 x (8.10 + 6.80)) is the outer face of the 2F roof-slab
    # perimeter bands (centrelines -20.255 / -12.355 and 43.148 / 49.748 m: 7.90 + 0.20 and 6.60 + 0.20)
    {"storey": "2F", "band": "BAND0006.1", "mark": "unlabelled 0.199 (BM-2F-016)", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "3.100"},
    {"storey": "2F", "band": "BAND0006.2", "mark": "B15 20x120", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "2.700"},
    {"storey": "2F", "band": "BAND0009", "mark": "B7 20x75", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "6.600"},
    {"storey": "2F", "band": "BAND0001.1", "mark": "B3 20x40", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "2.500"},
    {"storey": "2F", "band": "BAND0001.2", "mark": "B8 20x75", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "3.470"},
    {"storey": "2F", "band": "BAND0001.3", "mark": "unlabelled 0.20 (BM-2F-015)", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "1.130"},
    {"storey": "2F", "band": "BAND0003", "mark": "B2 20x40", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "2.500"},
    {"storey": "2F", "band": "BAND0004", "mark": "B1 20x40", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "1.800"},
    {"storey": "2F", "band": "BAND0005", "mark": "B2 20x40", "run": "2F (+13.90) perimeter", "handles": "outline 8.10 x 6.80", "covered_m": "3.000"},
]

# per-run printed heights behind T-550's 7.6307 m2 (1F roof: his 1.30 above finish vs each run's printed height)
RUN_HANDLES_1F = {"NE-2": "127F / 1285", "SE-1": "12C4 / 12C7", "SW-3": "1273 / 1278", "SW-2": "12B9",
                  "NW-1": "sea-side group 12A7 / 1308 .. 1313", "NW-2": "sea-side group", "NW-3": "sea-side group",
                  "NW-4": "sea-side group", "NW-5": "sea-side group", "NE-1": "run end", "SW-1": "run end"}
PRINTED_NOMINAL_1F = Decimal("1.30")


def _d(x):
    return Decimal(str(x))


def check_engine_openings() -> None:
    """sizes / deductions equal T-292's owner deduction; floor sums equal register V2 (GF with the W04 print)."""
    t292 = {}
    for r in csv.DictReader(T292.open(encoding="utf-8")):
        t292.setdefault(r["opening_id"], r)
    for oid, (_g, w, ded, basis) in ENGINE_OPENINGS.items():
        r = t292[oid]
        if basis == "HELD":
            assert "HELD" in r["owner_ded_new_m2"] or r["held"] == "yes" or oid in ("D-GF-07", "D-GF-14"), oid
            continue
        if basis == "OUTLINE":
            assert "outline" in r["merged_size"] or "OUTLINE" in r["merged_size"].upper(), oid
        if w is not None:
            assert r["merged_size"].startswith(f"w {w} ") or r["merged_size"].startswith(f"w {w},"), (oid, r["merged_size"])
        if basis == "Q55C":
            assert "Q-55 C" in r["merged_source"] or "T-237" in r["merged_source"], oid
        if r["owner_ded_new_m2"] not in ("", "HELD (room)") and "HELD" not in r["owner_ded_new_m2"]:
            assert _d(r["owner_ded_new_m2"]) == _d(ded), (oid, r["owner_ded_new_m2"], ded)
    reg = {}
    for r in csv.DictReader(REG_V2.open(encoding="utf-8")):
        reg[r["floor"]] = reg.get(r["floor"], Decimal(0)) + _d(r["deductions_m2"] or 0)
    assert {k: str(v) for k, v in reg.items()} == REGISTER_FLOOR, reg
    s = {}
    for oid, (g, w, ded, basis) in ENGINE_OPENINGS.items():
        if ded is None:
            continue
        fl = "GF" if g == "20CM" else g
        s[fl] = s.get(fl, Decimal(0)) + _d(ded)
    assert s["GF"] + GF_W04_PRINT == _d(REGISTER_FLOOR["GF"]), s
    assert s["1F"] == _d(REGISTER_FLOOR["1F"]) and s["2F"] == _d(REGISTER_FLOOR["2F"]), s


def his_units(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for g in ("GF", "1F", "2F", "20CM"):
        units = []
        for uid, n, w, h in d[g]:
            pre, k = uid[0], int(uid[1:])
            for i in range(n):
                units.append({"uid": f"{pre}{k + i}", "w_m": w, "h_m": h})
        out[g] = units
    return out


def openings(his: dict) -> dict:
    check_engine_openings()
    groups, rows = [], []
    for g in ("GF", "20CM", "1F", "2F"):
        eng = [{"id": oid, "w_m": w, "ded_m2": ded, "h_basis": b}
               for oid, (gg, w, ded, b) in ENGINE_OPENINGS.items() if gg == g]
        e_m2 = sum((_d(e["ded_m2"]) for e in eng if e["ded_m2"] is not None), Decimal(0))
        h_m2 = sum((_d(u["w_m"]) * _d(u["h_m"]) for u in his[g]), Decimal(0))
        res = R.opening_census(floor=g, engine=eng, his=his[g], pairs=PAIRS[g], engine_census_m2=e_m2,
                               his_census_m2=h_m2)
        groups.append(res)
        rows += res["rows"]
    rows.append({"name": "GF register V2 prints the GF-W04 wall total 4.7115 as 4.710", "term": "print",
                 "delta": str(GF_W04_PRINT), "cause": "TOLERANCE", "note": "register rounding"})
    return {"groups": groups, "rows": rows, "total": str(sum((_d(r["delta"]) for r in rows), Decimal(0)))}


def per_run_heights() -> list[dict]:
    out = []
    for r in csv.DictReader(RUNS.open(encoding="utf-8")):
        if r["chain"] != "1F":
            continue
        c = _d(r["centreline_m"].split("..")[1].strip())
        h = _d(r["h_above_finish_m"].split("..")[1].strip())
        printed = r["h_status"] != "HELD"
        out.append({"run": r["run"], "centreline_m": str(c), "h_printed_m": str(h) if printed else None,
                    "h_status": "PRINTED" if printed else f"HELD {r['h_above_finish_m']}",
                    "term_m2": str(c * (PRINTED_NOMINAL_1F - h)) if printed else None,
                    "handles": RUN_HANDLES_1F[r["run"]]})
    return out


def build(his_path: Path | None) -> dict:
    t550 = json.loads(T550.read_text(encoding="utf-8"))
    U = {x["part"]: Decimal(x["m2"]) for x in t550["unresolved_after"]}
    total = sum(U.values(), Decimal(0))
    assert total == Decimal(t550["restated_by_cause"]["UNRESOLVED"]), total
    open_parts = [k for k in U if "openings census" in k or "20 cm openings" in k]
    open_t550 = sum((U[k] for k in open_parts), Decimal(0))          # rows l x 3 + his 20 cm -9.84 = -26.2840
    lines = json.loads(LINE_INDEX.read_text(encoding="utf-8"))["lines"]
    carriage = R.edge_member_carriage(EDGE_BANDS, lines)
    runs = per_run_heights()
    run_sum = sum((_d(x["term_m2"]) for x in runs if x["term_m2"] is not None), Decimal(0))
    doc = {"method": "R-T559-1 / R-T559-2 on R-T550-1 / R-T543-1", "candidate": t550["candidate"],
           "t550_unresolved_m2": str(total), "t550_unresolved_parts": {k: str(v) for k, v in U.items()},
           "openings_t550_m2": str(open_t550), "edge_members": carriage,
           "edge_summary": {s: sum(1 for c in carriage if c["state"] == s) for s in ("CARRIED_ONCE", "OMITTED")},
           "per_run_heights_1F": runs, "per_run_sum_m2": str(run_sum)}
    assert run_sum.quantize(Decimal("0.0001")) == Decimal("7.6307"), run_sum
    if his_path is None or not his_path.exists():
        doc["openings"] = "NOT REBUILT: his opening rows are private (.work/private/t559/his_openings.json)"
        return doc
    op = openings(his_units(his_path))
    assert _d(op["total"]) == open_t550, (op["total"], open_t550)
    rest = [{"part": k, "m2": str(v), "cause": "UNRESOLVED"} for k, v in U.items() if k not in open_parts]
    table = [{"part": r["name"] + " / " + r["term"], "m2": r["delta"], "cause": r["cause"], "note": r["note"]}
             for r in op["rows"]] + rest
    bc = R.by_cause([{"delta": t["m2"], "cause": t["cause"]} for t in table])
    assert sum(map(Decimal, bc.values())) == total
    doc.update({"openings": op, "table": table, "by_cause": bc,
                "unresolved_gross_abs_m2": str(sum(abs(Decimal(t["m2"])) for t in table if t["cause"] == "UNRESOLVED")),
                "restated_b9_by_cause": _restate(t550["restated_by_cause"], bc, total)})
    return doc


def _restate(prev: dict, bc: dict, total: Decimal) -> dict:
    out = {k: Decimal(v) for k, v in prev.items()}
    out["UNRESOLVED"] -= total
    for k, v in bc.items():
        out[k] = out.get(k, Decimal(0)) + Decimal(v)
    assert sum(out.values()) == sum(Decimal(v) for v in prev.values())
    return {k: str(v) for k, v in sorted(out.items())}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    his = Path(argv[argv.index("--his") + 1]) if "--his" in argv else PRIVATE_DEFAULT
    doc = build(his)
    print("T-550 UNRESOLVED", doc["t550_unresolved_m2"], "openings part", doc["openings_t550_m2"])
    print("edge members:", doc["edge_summary"])
    for c in doc["edge_members"]:
        print(f"  {c['storey']} {c['band']:<10} {c['mark']:<28} {c['run']:<26} {c['state']:<13} "
              f"{c.get('line_class', '')} {c.get('measured_m3') or c.get('held_m3') or ''}")
    print("1F per-run printed heights sum", doc["per_run_sum_m2"])
    if isinstance(doc["openings"], dict):
        for g in doc["openings"]["groups"]:
            print(" ", g["floor"], "engine", g["engine_m2"], "his", g["his_m2"], "delta", g["delta"])
        print("by cause of the 25.9224:", doc["by_cause"])
        print("UNRESOLVED gross |m2|", doc["unresolved_gross_abs_m2"])
        print("B9 restated:", doc["restated_b9_by_cause"])
    else:
        print(doc["openings"])
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    return 0


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    raise SystemExit(main())
