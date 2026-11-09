"""T-577 development-villa build (research, unwired): MARBLE / STONE THRESHOLDS, WINDOW SILLS, LIFT and ENTRANCE STONE
vs the freelancer by item, one table per unit (lm, m2, nr), on the candidate of record ARCH_TAKEOFF_V3.0.58 (= the
V3.0.57 lines for every code read here: arch_v3058 adds only FIN.WP.ROOF / FIN.WP.ROOF_UPTURN lines, T-507).

    .work/venv/bin/python -I research/agents_t577/t577_alsenan.py [--check]

Reads only merged repository files (sha256-pinned): the V3.0.57 line index (T-507), his rows as numbers
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, finishes workbook: cover and marble + court sheets keyed by a hash
of the title, column labels checked by hash; no workbook text is written), and the T-325 sill / threshold ledger
(Checker-merged; the lm and nr of each strip stand beside its candidate m2 line, T-327). Nothing is re-measured from a
drawing here: every figure names the merged source that measured it. Writes out/T577_MARBLE_RECONCILE.json; --check
rebuilds it byte-identical. No coordinate, no client name is written."""
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
import t577_rules as R  # noqa: E402

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
LEDGER = "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
PINS = {LINE_INDEX: "fed5141ea31bfdd9", RAW: "752c9f4e0c4546d0", LEDGER: "ef6f2cb0c0d7619e"}
OUT = HERE / "out" / "T577_MARBLE_RECONCILE.json"
D = R.D
Z = Decimal(0)


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def S(x):
    return None if x is None else str(x)


# ---- candidate lines ------------------------------------------------------------------------------------------------
def index_lines():
    return {x["line_id"]: x for x in json.loads((ROOT / LINE_INDEX).read_text())["lines"]}


def ledger():
    return list(csv.DictReader((ROOT / LEDGER).open(encoding="utf-8")))


# T-327: the five closure lines the ledger binds were retired; each strip is now booked in its successor (T-327 s.2)
RETYPED = {"L-cb2fdcac375323371bdf": ("L-791a94968230969c030f", "D-GF-02"),
           "L-95bb76ee6c98edac0179": ("L-1a229f1fead084efb881", "D-GF-10"),
           "L-8c2040d7c6ecce827316": ("L-3b166c2b5d136302f2dd", "D-GF-14"),
           "L-63c15e31faff037fcdde": ("L-bfdbdaa2d67a5c805f1e", "D-1F-04"),
           "L-a4c323cb1e402c9127d2": ("L-fcf3a49c67ae9e730028", "D-1F-03")}
NO_LEDGER_LINE = {"D-GF-15": "L-56acf34557c315f65bb1",      # gate threshold, ADDED blank by T-327
                  "W18:OUT": "L-cd88cb0d77ee82dc7259"}      # W18 sill, T-326 (ledger NO_LINE, same 0.500 x 0.080)
W03_HELD = {"W03:IN": "L-29637dbaa9fe1acc7b82", "W03:OUT": "L-30133ea5a4fb6847c519"}
A_GF_01 = "L-868aee125705bb8d17f6"


def line_of(row, L):
    """The live candidate line of one ledger strip (successor of a retired closure line), asserted."""
    lid = row["line_id"]
    if lid in RETYPED:
        new, oid = RETYPED[lid]
        if L[lid]["class"] != "EXCLUDED" or oid != row["opening"] or oid not in L[new]["element_id"]:
            raise R.RuleError(f"{row['opening']}: retired {lid} / successor {new} not as T-327 states")
        return new
    if row["opening"] in NO_LEDGER_LINE:
        return NO_LEDGER_LINE[row["opening"]]
    if not lid.startswith("L-"):
        raise R.RuleError(f"{row['opening']} {row['component']}: no candidate line")
    return lid


def _status(x):
    return {"RELEASED": "DRAWING-CONFIRMED", "HELD": "HELD", "EXCLUDED": "NOT_APPLICABLE"}[x["class"]]


class Pieces:
    """One piece per opening / station, three measures (R-T577-1 (a)); every piece once (R-T577-1 (b))."""

    def __init__(self):
        self.t = {"lm": {}, "m2": {}, "nr": {}}
        self.src = {}
        self.ids = []

    def add(self, pid, group, src, m2=None, lm=None, nr=None):
        R.pieces_once([(p, "") for p in self.ids] + [(pid, "")])
        self.ids.append(pid)
        self.src[pid] = {"group": group, **src}
        for unit, v in (("m2", m2), ("lm", lm), ("nr", nr)):
            if v is None:
                continue
            status, value, bound = v
            self.t[unit][pid] = {"unit": unit, "value": value, "status": status, "bound": bound, "group": group}


def door_group(row):
    if row["kind"] == "ARCH":
        return "DRY"
    if row["external"] == "True":
        return "EXT"
    return {"MARBLE": "WET", "FLOOR PORCELAIN": "DRY"}[row["material"]]


def build_pieces(L, led):
    P = Pieces()
    used_lines = set()
    for r in led:
        comp, oid = r["component"], r["opening"]
        if comp == "THRESHOLD":
            g = door_group(r)
            lid = line_of(r, L)
            x = L[lid]
            used_lines.add(lid)
            st = _status(x)
            if st == "DRAWING-CONFIRMED":
                if D(x["measured_net"]) != D(r["m2"]):
                    raise R.RuleError(f"{oid}: candidate {x['measured_net']} != ledger {r['m2']} m2")
                lm, m2, nr = R.threshold(r["width_m"], r["depth_m"])
                if m2 != D(r["m2"]) or lm != D(r["edge_ml"]):
                    raise R.RuleError(f"{oid}: width x depth {m2} != ledger {r['m2']}")
                P.add(oid, g, {"line": lid, "code": x["item_code"]}, m2=(st, D(x["measured_net"]), None),
                      lm=(st, lm, None), nr=(st, nr, None))
            else:   # HELD: the strip's area / width beside where measured, never a number in a sum
                if r["state"] == "MEASURED" and oid != "A-GF-01":
                    if not (D(x["held_low"]) == D(x["held_high"]) == D(r["m2"])):
                        raise R.RuleError(f"{oid}: held bound {x['held_low']}..{x['held_high']} != ledger {r['m2']}")
                    mb, lb = (D(r["m2"]), D(r["m2"])), (D(r["width_m"]), D(r["width_m"]))
                elif oid == "A-GF-01":   # T-377: held by name; T-340's 1.000 x 0.150 strip NOT applied (T-327 s.4)
                    if lid != A_GF_01:
                        raise R.RuleError("A-GF-01 line moved")
                    mb, lb = (Z, D(r["m2"])), (Z, D(r["width_m"]))
                else:   # D-GF-15 gate: width / host wall not established
                    mb, lb = (Z, None), (Z, None)
                P.add(oid, g, {"line": lid, "code": x["item_code"]}, m2=("HELD", None, mb), lm=("HELD", None, lb),
                      nr=("DRAWING-CONFIRMED", 1, None))
        elif comp in ("SILL_OUT", "THRESHOLD_OUT"):
            g = "SILL" if r["kind"] == "WINDOW" else "FLOORGLAZING"
            key = f"{oid}:OUT"
            if oid == "W03":
                continue
            lid = line_of({**r, "opening": key if oid == "W18" else oid}, L)
            x = L[lid]
            used_lines.add(lid)
            st = _status(x)
            if st == "DRAWING-CONFIRMED":
                lm, m2, nr = R.sill(r["width_m"], r["depth_m"])     # no return printed: T-325 frame flush
                if D(x["measured_net"]) != m2 or m2 != D(r["m2"]):
                    raise R.RuleError(f"{oid}: sill {m2} vs candidate {x['measured_net']} / ledger {r['m2']}")
                P.add(key, g, {"line": lid, "code": x["item_code"]}, m2=(st, m2, None), lm=(st, lm, None),
                      nr=(st, nr, None))
            else:   # W17 curved: unresolved, unbounded
                P.add(key, g, {"line": lid, "code": x["item_code"]}, m2=("HELD", None, (Z, None)),
                      lm=("HELD", None, (Z, None)), nr=("DRAWING-CONFIRMED", 1, None))
    for key, lid in W03_HELD.items():
        if L[lid]["class"] != "HELD":
            raise R.RuleError(f"{key}: {lid} no longer HELD")
        used_lines.add(lid)
        P.add(key, "FLOORGLAZING", {"line": lid, "code": L[lid]["item_code"]}, m2=("HELD", None, (Z, None)),
              lm=("HELD", None, (Z, None)), nr=("DRAWING-CONFIRMED", 1, None))
    # lift: T-475 / T-421 lines (3 stations, DRAWING-CONFIRMED census)
    for st in ("GF", "1F", "2F"):
        tm = [x for x in L.values() if x["element_id"] == f"LIFT:ELV-01-{st}"]
        tl = [x for x in L.values() if x["element_id"] == f"LIFT:ELV-01-{st}:edge"]
        su = [x for x in L.values() if x["element_id"] == f"LIFT:ELV-01-{st}:surround"]
        if not (len(tm) == len(tl) == len(su) == 1 and tm[0]["unit"] == "m2" and tl[0]["unit"] == "lm"):
            raise R.RuleError(f"lift station {st}: lines not as T-475 states")
        for x in (tm[0], tl[0], su[0]):
            used_lines.add(x["line_id"])
        P.add(f"ELV-01-{st}", "LIFT", {"line": tm[0]["line_id"], "edge_line": tl[0]["line_id"],
                                       "code": tm[0]["item_code"], "status_note": "depth 0.50 ASSUMED - OWNER-APPROVED "
                                       "(UP-ELEV-005); width DRAWING-CONFIRMED (T-475)"},
              m2=("ASSUMED - OWNER-APPROVED", D(tm[0]["measured_net"]), None),
              lm=("DRAWING-CONFIRMED", D(tl[0]["measured_net"]), None), nr=("DRAWING-CONFIRMED", 1, None))
        s = su[0]
        P.add(f"ELV-01-{st}:SURROUND", "LIFT", {"line": s["line_id"], "code": s["item_code"]},
              m2=("HELD", None, (D(s["held_low"]), D(s["held_high"]))))
    # entrance stair E1 (T-343 / T-490): treads, risers, landing; no step-lm line in the candidate
    E1 = {"E1:TREADS": "GF-COURT#E1-TREADS", "E1:RISERS": "GF-COURT#E1-RISERS", "E1:LANDING": "GF-COURT#E1-LANDING"}
    for pid, el in E1.items():
        xs = [x for x in L.values() if x["element_id"] == el]
        if len(xs) != 1 or xs[0]["class"] != "RELEASED":
            raise R.RuleError(f"{el}: not one released line")
        x = xs[0]
        used_lines.add(x["line_id"])
        nr = ("DRAWING-CONFIRMED", 4, None) if pid == "E1:TREADS" else None      # printed 4 x 0.30 x 2.80 (T-490)
        P.add(pid, "E1_LANDING" if pid == "E1:LANDING" else "E1_STEPS", {"line": x["line_id"], "code": x["item_code"]},
              m2=("DRAWING-CONFIRMED", D(x["measured_net"]), None), nr=nr)
    return P, used_lines


# ---- his cells (numbers only; ids are sheet key + cell) -------------------------------------------------------------
SHEETS = {("FIN", "6329cb4ab3f1"): "COV", ("FIN", "3a9d8cc3e07d"): "MRB"}
# sha256[:12] of a label with brackets and spaces removed -> unit (count / linear / area / height / total area / total
# skirting / the cover's unit words); no workbook text in the repository
LABEL = {"a760cfd5140e": "nr", "0b606bfc7e9d": "lm", "819bbf7d900c": "m2", "e6a9fbd3772e": "height",
         "a74a6e287323": "m2", "953b50582d2e": "lm", "0e7699bdbc72": "m2", "d2c6c24b21e4": "lm"}
HEAD = {"B": "MRB.B8", "C": "MRB.C9", "D": "MRB.D9", "F": "MRB.F9", "G": "MRB.G8", "H": "MRB.H8"}


def his_cells():
    d = json.loads((ROOT / RAW).read_text())
    cells = {}
    for x in d["rows"]:
        key = SHEETS.get((x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]))
        if key:
            for c, v in x["cells"].items():
                cells[f"{key}.{c}"] = v["v"]
    return cells


def label(cells, cell):
    s = str(cells[cell]).replace("(", "").replace(")", "").replace(" ", "").strip()
    u = LABEL.get(hashlib.sha256(s.encode()).hexdigest()[:12])
    if u is None:
        raise R.RuleError(f"label {cell} not recognised: the column's unit is not established")
    return u


def _q(v):
    return D(repr(round(v, 6))) if isinstance(v, float) else D(v)


def col_unit(cells, col):
    return label(cells, HEAD[col])


DOOR_STEP_ROWS = [36, 37, 38, 39, 40, 41]


def his_tables(cells):
    """His in-scope cells per unit table (R-T577-1 (c)) and the partition of his marble totals."""
    for c, u in (("COV.F24", "m2"), ("COV.F25", "lm"), ("COV.F26", "nr")):
        if label(cells, c) != u:
            raise R.RuleError(f"cover label {c} is not {u}")
    if [col_unit(cells, c) for c in "BCDFGH"] != ["nr", "lm", "m2", "height", "lm", "m2"]:
        raise R.RuleError("marble sheet column labels not as expected")

    def row(r):
        g = lambda c: cells.get(f"MRB.{c}{r}")    # noqa: E731
        return {c: (None if g(c) is None else _q(g(c))) for c in "BCDFGH"}

    m2, lm, nr = {}, {}, {}
    for r in DOOR_STEP_ROWS + [16]:
        x = row(r)
        cls = R.classify_cell("m2", x["B"], x["C"], x["D"], x["F"], x["H"])
        if cls != "LENGTH_IN_AREA_COLUMN":
            raise R.RuleError(f"his row {r}: expected a length in the area column, got {cls}")
        m2[f"MRB.H{r}"] = {"label": "m2", "value": x["H"], "class": cls}
        lm[f"MRB.B{r}xC{r}"] = {"label": "lm", "value": R.length_of_row(x["B"], "nr", x["C"], "lm"), "class": "LENGTH"}
        nr[f"MRB.B{r}"] = {"label": "nr", "value": x["B"], "class": "COUNT"}
    x = row(17)
    if R.classify_cell("m2", x["B"], x["C"], x["D"], x["F"], x["H"]) != "AREA" or x["D"] != x["H"]:
        raise R.RuleError("his entrance landing row is not an area row")
    m2["MRB.H17"] = {"label": "m2", "value": x["H"], "class": "AREA"}
    # partition of his marble totals (cover F24 m2 / F25 lm / F26 nr), each part named with its owner
    part_m2 = [("in this table: door steps H36..H41 (length in an area column)",
                sum((m2[f"MRB.H{r}"]["value"] for r in DOOR_STEP_ROWS), Z)),
               ("in this table: entrance steps H16 (5 x 2.80, length in an area column)", m2["MRB.H16"]["value"]),
               ("in this table: entrance landing H17 (area)", m2["MRB.H17"]["value"]),
               ("other owner: court floor H13 (area; EXT.FLOOR family, OWNER_RULE_OUTDOOR_FLOORS, T-495 / T-553)",
                _q(cells["MRB.H13"])),
               ("other owner: main-stair steps H23 (63 x 1.20, length in an area column; no stair-finish "
                "reconciliation row yet)", _q(cells["MRB.H23"])),
               ("other owner: main-stair landing H24 (area)", _q(cells["MRB.H24"])),
               ("other owner: inner-stair steps H30 (28 x 1.20, length in an area column)", _q(cells["MRB.H30"])),
               ("other owner: inner-stair landing H31 (area)", _q(cells["MRB.H31"]))]
    for r in (23, 30):
        y = row(r)
        if R.classify_cell("m2", y["B"], y["C"], y["D"], y["F"], y["H"]) != "LENGTH_IN_AREA_COLUMN":
            raise R.RuleError(f"his stair row {r} not a length in the area column")
    for r in (13, 24, 31):
        y = row(r)
        if R.classify_cell("m2", y["B"], y["C"], y["D"], y["F"], y["H"]) != "AREA":
            raise R.RuleError(f"his row {r} not an area row")
    for c in ("MRB.H44", "COV.B24"):
        R.partition(_q(cells[c]), part_m2)
    area_part = sum((v for k, v in part_m2 if "(area" in k), Z)
    length_part = sum((v for k, v in part_m2 if "length in an area column" in k), Z)
    part_lm = [("other owner: stair / entrance skirting G18 + G25 + G32 (T-574 stair groups)",
                _q(cells["MRB.G18"]) + _q(cells["MRB.G25"]) + _q(cells["MRB.G32"]))]
    part_nr = [("other owner: stair-side pieces per step G19 + G26 + G33 (T-574 nr groups)",
                _q(cells["MRB.G19"]) + _q(cells["MRB.G26"]) + _q(cells["MRB.G33"]))]
    for c in ("MRB.H45", "COV.B25"):
        R.partition(_q(cells[c]), part_lm)
    for c in ("MRB.H46", "COV.B26"):
        R.partition(_q(cells[c]), part_nr)
    return {"m2": m2, "lm": lm, "nr": nr}, {
        "m2": {"total": S(_q(cells["COV.B24"])), "parts": [[k, S(v)] for k, v in part_m2],
               "area_shaped": S(area_part), "length_shaped": S(length_part),
               "note": "his 'stairs and landings' m2 total adds 130.9 of count x length (lm) to 164.54 of area "
                       "(m2): it is not an area; R-T577-1 (c) keeps each number in its own label"},
        "lm": {"total": S(_q(cells["COV.B25"])), "parts": [[k, S(v)] for k, v in part_lm],
               "note": "his lm marble total is skirting only; the door-step and entrance-step lengths sit inside "
                       "his m2 total (above) and are compared here from his own count x length cells"},
        "nr": {"total": S(_q(cells["COV.B26"])), "parts": [[k, S(v)] for k, v in part_nr],
               "note": "his nr marble total is stair-side pieces only; the door-step and entrance-step counts are his "
                       "column B cells"},
    }


# ---- groups and causes ----------------------------------------------------------------------------------------------
def C(label, amount, verdict, kind, source, bound=None):
    c = {"label": label, "amount": D(amount), "verdict": verdict, "kind": kind, "source": source}
    if bound is not None:
        c["bound"] = bound
    return c


def sum_group(tab, group):
    return sum((v["value"] for v in tab.values() if v["group"] == group and v["value"] is not None), Z)


def held_bound(tab, group):
    hs = [v["bound"] for v in tab.values() if v["group"] == group and v["value"] is None]
    lo = sum((b[0] for b in hs), Z)
    hi = None if any(b[1] is None for b in hs) else sum((b[1] for b in hs), Z)
    return hs, (lo, hi)


NO_ROW = "he carries no row for this element (T-325 census: 0 of 885 rows names a threshold / sill / lift stone)"
GROUP_NAMES = {
    "WET": "wet doorway thresholds, marble (UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1)",
    "DRY": "dry doorway / arch strips, the floor porcelain continued once (UP-THR-001)",
    "EXT": "external entrance doors: threshold strip (ours) vs his 'door steps' block",
    "SILL": "window sills, raised windows (UP-REVEAL-001; material UNKNOWN, consultant A13)",
    "FLOORGLAZING": "floor-level glazing outside strips (onto a terrace: its floor finish; over air: UNKNOWN)",
    "LIFT": "lift landing threshold B6-07 and surround B6-06 (T-475)",
    "E1_STEPS": "entrance stair E1 steps (his 'entrance marble' steps)",
    "E1_LANDING": "entrance stair E1 landing (his 'entrance marble' landing)",
}


def groups_for(unit, P, H):
    t = P.t[unit]
    G = []

    def g(gid, cells, causes, note=""):
        G.append({"id": gid, "name": GROUP_NAMES[gid], "pieces": sorted(k for k, v in t.items() if v["group"] == gid),
                  "cells": cells, "causes": causes, "note": note})

    def held(gid, label, src):
        hs, b = held_bound(t, gid)
        return [C(label, 0, "HELD", "HELD", src, bound=b)] if hs else []

    ours = {k: sum_group(t, k) for k in GROUP_NAMES}
    # WET
    g("WET", [], [C(f"{NO_ROW}: every wet doorway takes a marble strip by owner rule; his omission", ours["WET"],
                    "ENGINE_RIGHT", "SCOPE", "T-325 / T-327 (14 strips, Checker-merged ledger)")])
    # DRY
    g("DRY", [], [C(f"{NO_ROW}; the strip is the floor porcelain continued, so it may sit inside his room floor rows "
                    "(not established: his rows carry no strip)", ours["DRY"], "RULE_DIFFERENCE", "SCOPE",
                    "T-325 / T-327; floor rows in T-553")]
      + held("DRY", "D-GF-15 gate strip (width / host wall not established, unbounded) and A-GF-01 arch strip "
                    "(held by name, T-377; 1.000 x 0.150 beside, NOT applied, T-327)", "T-327 s.4"))
    # EXT
    if unit == "m2":
        ext_cells = [f"MRB.H{r}" for r in DOOR_STEP_ROWS]
        ext = [C("his H36..H41 are count x length in an area column (no width cell): 7.70 of length booked as m2; never "
                 "compared as m2 and never converted (R-T577-1 (c))", -sum((H["m2"][c]["value"] for c in ext_cells), Z),
                 "RULE_DIFFERENCE", "UNIT", "his own cells (B x C = H, D / F blank)")]
    elif unit == "lm":
        ext_cells = [f"MRB.B{r}xC{r}" for r in DOOR_STEP_ROWS]
        ext = [C("his 'door steps' are step pieces outside the external doors (EXT_STEP), ours the strip inside the "
                 "wall thickness: different elements (T-325 RULE_DIFFERENCE, element); no EXT_STEP piece is in the "
                 "candidate, and whether a step stands outside each of the six doors (outside level vs F.F.L.) is not "
                 "established in a merged reading: a possible ENGINE_OMISSION named for the Lead, never valued here",
                 -sum((H["lm"][c]["value"] for c in ext_cells), Z), "UNRESOLVED", "SCOPE",
                 "his own count x length cells; T-325 s.4")]
    else:
        ext_cells = [f"MRB.B{r}" for r in DOOR_STEP_ROWS]
        ext = [C("six external doors drawn (T-325 census: D-GF-01 / 03 / 06 / 07 / 09, D-2F-01) = his six door-step "
                 "pieces: the count agrees; the elements differ (strip vs step), so the agreement is a count only",
                 Z, "AGREE", "MEASURE", "T-325 ledger; his B36..B41")]
    ext += held("EXT", "external entrance strips: area / width measured (T-325), material by specification, so each "
                       "line is HELD at its point bound (never 0)", "T-325 / T-327")
    g("EXT", ext_cells, ext, "at the bound the strip widths are 6.800 lm vs his piece lengths 7.700 lm (-0.900): two "
                             "elements, not a gap; his 1.30 / 2.50 exceed every 1.00 / 2.00 jamb gap, and matching his "
                             "rows to doors by figure is refused (his rows carry no door id)" if unit == "lm" else "")
    # SILL
    g("SILL", [], [C(f"{NO_ROW}: a sill is its own item (UP-REVEAL-001); quantity from the drawn frame (no return "
                     "printed: length = opening width), material UNKNOWN", ours["SILL"], "ENGINE_RIGHT", "SCOPE",
                     "T-325 / T-326 / T-327")]
      + held("SILL", "W17 curved sill (T-302: radius / chord basis not established, unbounded)", "T-327 s.4"))
    g("FLOORGLAZING", [], [C(f"{NO_ROW}: W15 / W16 outside strips onto the 1F terrace take its floor finish; W25 / "
                             "W27 over air, material UNKNOWN", ours["FLOORGLAZING"], "ENGINE_RIGHT", "SCOPE",
                             "T-325 R-T325-1")]
      + held("FLOORGLAZING", "W03 inner / outer floor strips (GF-15 floor glazing; frame position not established, "
                             "unbounded)", "T-325 / T-327"))
    g("LIFT", [], [C(f"{NO_ROW}: B6-07 per landing door by owner rule (UP-ELEV-005), 3 stations drawn on two drawings",
                     ours["LIFT"], "ENGINE_RIGHT", "SCOPE", "T-475 (Checker-merged census)")]
      + held("LIFT", "B6-06 surrounds: door clear height not printed (RFI L-1), 2F right band 0 .. 0.400",
             "T-475 / T-421"))
    # E1
    if unit == "m2":
        g("E1_STEPS", ["MRB.H16"],
          [C("his H16 = 5 steps x 2.80 = 14.00 of length in an area column: never compared as m2 (R-T577-1 (c))",
             -H["m2"]["MRB.H16"]["value"], "RULE_DIFFERENCE", "UNIT", "his B16 x C16 = H16, D / F blank"),
           C("our tread 3.3594 (4 x 0.30 x 2.80 printed = 3.3600; drawn -0.0006) + riser 1.96 (5 x (0.85 / 5 - 0.030) x 2.80) m2 "
             "have no area counterpart in his row", ours["E1_STEPS"], "ENGINE_RIGHT", "SCOPE", "T-343 / T-490")])
        land = H["m2"]["MRB.H17"]["value"]
        g("E1_LANDING", ["MRB.H17"],
          [C("printed 1.40 x 3.70 = 5.18 vs his 5.10 typed", D("5.18") - land, "ENGINE_RIGHT", "MEASURE",
             "sheet 03 print (T-343 / T-490)"),
           C("drawn polygon 5.1794 vs printed 5.18 (4-dp vertices)", ours["E1_LANDING"] - D("5.18"), "TOLERANCE",
             "MEASURE", "line index vs print")])
    elif unit == "lm":
        g("E1_STEPS", ["MRB.B16xC16"],
          [C("E1 has no FIN.STAIR.STEP_LM line while the other flights carry one (per tread x width): printed 4 treads "
             "x 2.80 = 11.20 lm; ENGINE_OMISSION named for the Lead, not valued here", D("-11.2"), "ENGINE_OMISSION",
             "MEASURE", "T-490 print 4 x 0.30 x 2.80; index codes"),
           C("his 5th step x 2.80 = the top step to the landing, which the candidate books as the landing 1.40 x 3.70 "
             "(T-534: the top E1 step is the landing edge, not a tread)", D("-2.8"), "RULE_DIFFERENCE", "MEASURE",
             "T-534 / T-343")])
    else:
        g("E1_STEPS", ["MRB.B16"],
          [C("4 treads printed (T-490) vs his 5 steps: his top step is our landing edge", D("-1"), "RULE_DIFFERENCE",
             "MEASURE", "T-490 / T-534")])
    return G


# ---- code closure: every line of the codes read here, used or named -------------------------------------------------
CODES = ("FIN.MARBLE.THRESHOLD", "FIN.MARBLE.LIFT_THRESHOLD", "FIN.MARBLE.LIFT_SURROUND", "ARCH.THRESHOLD",
         "ARCH.WINDOW_REVEAL")
OTHER_ARCH_THRESHOLD = "T-325 s.3: not census openings (GF OP-020 passage under wet review; 5 WALL_BAND_REMAINDER / " \
                       "STRIP_NOT_ATTRIBUTED wall bodies; 3 lift landing sills and the OP-001 / OP-003 pair " \
                       "NOT_APPLICABLE; 5 closure lines retired by T-327)"


def code_closure(L, used):
    out = {}
    for code in CODES:
        xs = [x for x in L.values() if x["item_code"] == code]
        u = [x for x in xs if x["line_id"] in used]
        rest = [x for x in xs if x["line_id"] not in used]
        if code.startswith("FIN.MARBLE.") and rest:
            raise R.RuleError(f"{code}: lines outside this reconciliation {[x['line_id'] for x in rest]}")
        if code == "ARCH.WINDOW_REVEAL" and any(":JAMBS_HEAD:" not in x["element_id"] for x in rest):
            raise R.RuleError("a window reveal line that is neither a sill / strip nor a jamb-head reveal")
        if code == "ARCH.THRESHOLD":
            if any(x["class"] == "RELEASED" for x in rest) or len(rest) != 16:
                raise R.RuleError("ARCH.THRESHOLD lines outside the census changed")
        units = sorted({x["unit"] for x in xs})
        rel = {un: S(sum((D(x["measured_net"]) for x in xs if x["class"] == "RELEASED" and x["unit"] == un), Z))
               for un in units}
        rel_u = {un: S(sum((D(x["measured_net"]) for x in u if x["class"] == "RELEASED" and x["unit"] == un), Z))
                 for un in units}
        out[code] = {"lines": len(xs), "used": len(u), "released_total": rel, "released_used": rel_u,
                     "not_this_element": len(rest),
                     "why": {"ARCH.THRESHOLD": OTHER_ARCH_THRESHOLD,
                             "ARCH.WINDOW_REVEAL": "jamb + head reveal lines (finish of the reveal faces, plaster / "
                                                   "paint trade), not a sill"}.get(code, "")}
    return out


def G_out(t):
    return [{"id": g["id"], "name": GROUP_NAMES[g["id"]], "ours": S(g["ours"]), "his": S(g["his"]), "gap": S(g["gap"]),
             "pct": S(g["pct"]), "held_bound": [S(g["held_bound"][0]), S(g["held_bound"][1])],
             "pieces": g["pieces"], "cells": g["cells"],
             "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"], "amount": S(c["amount"]),
                         **({"bound": [S(c["bound"][0]), S(c["bound"][1])]} if "bound" in c else {}),
                         "source": c["source"]} for c in g["causes"]],
             **({"note": g["note"]} if g.get("note") else {})} for g in t["groups"]]


def build():
    pins()
    L = index_lines()
    P, used = build_pieces(L, ledger())
    cells = his_cells()
    H, part = his_tables(cells)
    tables = {}
    for unit in ("m2", "lm", "nr"):
        pcs = {k: {"unit": v["unit"], "value": v["value"], "status": v["status"]} for k, v in P.t[unit].items()}
        t = R.reconcile(unit, groups_for(unit, P, H), pcs, H[unit])
        tot = t["totals"]
        tables[unit] = {"groups": G_out(t),
                        "totals": {"ours": S(tot["ours"]), "his": S(tot["his"]), "gap": S(tot["ours"] - tot["his"]),
                                   "pct": None, "pct_withheld": "a group carries a HELD, SCOPE or UNIT cause "
                                                                "(R-T577-1 (e))"},
                        "his_marble_total": part[unit]}
    pieces = {pid: {"group": P.src[pid]["group"], "line": P.src[pid]["line"], "code": P.src[pid]["code"],
                    **{u: ({"value": S(P.t[u][pid]["value"]), "status": P.t[u][pid]["status"],
                            **({"bound": [S(P.t[u][pid]["bound"][0]), S(P.t[u][pid]["bound"][1])]}
                               if P.t[u][pid]["bound"] else {})} if pid in P.t[u] else None)
                       for u in ("m2", "lm", "nr")}} for pid in sorted(P.ids)}
    return {
        "schema": "T577_MARBLE_RECONCILE_V1", "rule": "R-T577-1", "candidate": "ARCH_TAKEOFF_V3.0.58",
        "line_index": LINE_INDEX, "pins": PINS,
        "tables": tables, "pieces": pieces, "code_closure": code_closure(L, used),
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != out:
            raise SystemExit("T577 output differs from a rebuild")
        print("T577 check: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
