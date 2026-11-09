"""T-574 development-villa build (research, unwired): SKIRTING vs the freelancer by room / stair group and class, lm and
nr apart, on the candidate of record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 skirting lines: arch_v3058 adds only
FIN.WP.ROOF / FIN.WP.ROOF_UPTURN lines, every other line byte-identical, T-507).

    .work/venv/bin/python -I research/agents_t574/t574_alsenan.py [--check]

Reads only merged repository files (sha256-pinned): the V3.0.57 line index (T-507), his rows as numbers
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: finishes workbook cover, tiles and marble + yard sheets; sheets
keyed by a hash of the title, unit labels checked by hash, no workbook text in the repository), the T-460 V3.0.51
skirting closure (gross / listed deductions / additions per line), and the T-501 stair-side piece table (flight
figures beside the HELD lines). Each deduction component is named with the merged source that measured it (T-296 by
opening id, T-431 / T-440 / T-422 / T-483 / T-443 / T-508); none is re-measured here. Writes
out/T574_SKIRTING_RECONCILE.json; --check rebuilds it byte-identical. No coordinate, no client name is written."""
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
import t574_rules as R  # noqa: E402

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
T460 = "research/agents_t460/SKIRTING_CLOSURE_V3051.csv"
T501 = "research/agents_t501/LINES_T501.csv"
T296R = "research/agents_t296/ROOMS_T296.csv"
PINS = {LINE_INDEX: "fed5141ea31bfdd9", RAW: "752c9f4e0c4546d0", T460: "a2f3e6caa2893c5f", T501: "1551662ca02dbca1",
        T296R: "2fc2ca2c1447e89a"}
OUT = HERE / "out" / "T574_SKIRTING_RECONCILE.json"
D = R.D
Z = Decimal(0)


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


# ---- candidate lines (V3.0.57 ids = V3.0.58) ------------------------------------------------------------------------
CODE_CLASS = {"FIN.SKIRTING": "ROOM", "FIN.STAIR.SKIRTING.ZIGZAG": "STAIR_FLIGHT",
              "FIN.STAIR.SKIRTING.SLOPED": "STAIR_FLIGHT"}


def candidate_lines():
    out = {}
    for x in json.loads((ROOT / LINE_INDEX).read_text())["lines"]:
        cls = CODE_CLASS.get(x["item_code"])
        if cls is None:
            continue
        st = {"RELEASED": "DRAWING-CONFIRMED", "HELD": "HELD", "EXCLUDED": "NOT_APPLICABLE"}[x["class"]]
        out[x["line_id"]] = {"class": cls, "code": x["item_code"], "unit": x["unit"], "element": x["element_id"],
                             "value": x["measured_net"] if x["class"] == "RELEASED" else None, "status": st}
    return out


# ---- his rows (numbers only; ids are sheet key + cell) --------------------------------------------------------------
SHEETS = {("FIN", "6329cb4ab3f1"): "COV", ("FIN", "ebc195c023cb"): "CER", ("FIN", "3a9d8cc3e07d"): "MRB"}
# sha256[:12] of a unit label with brackets and spaces removed (no workbook text in the repository)
LABEL = {"d2c6c24b21e4": "lm", "0e7699bdbc72": "m2", "a760cfd5140e": "nr"}


def his_cells():
    d = json.loads((ROOT / RAW).read_text())
    cells = {}
    for x in d["rows"]:
        key = SHEETS.get((x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]))
        if key:
            for c, v in x["cells"].items():
                cells[f"{key}.{c}"] = v["v"]
    return cells


def label_unit(cells, cell):
    s = str(cells[cell]).replace("(", "").replace(")", "").replace(" ", "").strip()
    u = LABEL.get(hashlib.sha256(s.encode()).hexdigest()[:12])
    if u is None:
        raise R.RuleError(f"unit label of {cell} not recognised: the row's unit is not established")
    return u


def _q(v):
    return D(repr(round(v, 6))) if isinstance(v, float) else D(v)


ROOM_ROWS = [13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 28, 29]
STAIR_LM = {"ST-03 entrance (E1)": "MRB.G18", "ST-01 main": "MRB.G25", "ST-02 round (inner)": "MRB.G32"}
STAIR_NR = {"ST-03 entrance (E1)": "MRB.G19", "ST-01 main": "MRB.G26", "ST-02 round (inner)": "MRB.G33"}


def rows_table(cells):
    """His skirting rows with the unit their own label states (R-T546-1), and his totals asserted."""
    # unit labels: tiles sheet perimeter total C33 and summary I71, cover F16 (internal), F23 (yard), F25 (stair lm),
    # F26 (stair pieces); the floors row F15 is m2 (the adverse pair).
    for c, u in (("CER.C33", "lm"), ("CER.I71", "lm"), ("COV.F16", "lm"), ("COV.F23", "lm"), ("COV.F25", "lm"),
                 ("COV.F26", "nr"), ("COV.F15", "m2")):
        if label_unit(cells, c) != u:
            raise R.RuleError(f"his label {c} is not {u}")
    rows = {}
    for r in ROOM_ROWS:
        rows[f"CER.C{r}"] = {"unit": "lm", "value": _q(cells[f"CER.C{r}"])}
    for cell in STAIR_LM.values():
        rows[cell] = {"unit": "lm", "value": _q(cells[cell])}
    for cell in STAIR_NR.values():
        rows[cell] = {"unit": "nr", "value": _q(cells[cell])}
    rows["MRB.G13"] = {"unit": "lm", "value": _q(cells["MRB.G13"])}
    room = sum((rows[f"CER.C{r}"]["value"] for r in ROOM_ROWS), Z)
    for c in ("CER.C31", "CER.H71", "COV.B16"):
        if room != _q(cells[c]):
            raise R.RuleError(f"his {c} {cells[c]} != his room rows {room}")
    st = sum((rows[c]["value"] for c in STAIR_LM.values()), Z)
    for c in ("MRB.H45", "COV.B25"):
        if st != _q(cells[c]):
            raise R.RuleError(f"his {c} != his stair lm rows {st}")
    pc = sum((rows[c]["value"] for c in STAIR_NR.values()), Z)
    for c in ("MRB.H46", "COV.B26"):
        if pc != _q(cells[c]):
            raise R.RuleError(f"his {c} != his stair piece rows {pc}")
    if rows["MRB.G13"]["value"] != _q(cells["COV.B23"]):
        raise R.RuleError("his yard row != cover B23")
    return rows


# ---- room lines: closure components (T-460 V3.0.51 gross / listed; T-508 V3.0.56 shaft) ------------------------------
def t460():
    return {r["line_id"]: r for r in csv.DictReader((ROOT / T460).open(encoding="utf-8"))}


RD, ER, HE, TO, UN, NI = "RULE_DIFFERENCE", "ENGINE_RIGHT", "HELD", "TOLERANCE", "UNRESOLVED", "NOT_IN_HIS_ROWS"
T296 = "T-296 DEDUCTIONS_BY_OPENING (opening id, width)"

# line -> (deductions [(label, lm, verdict)], additions [(label, lm, verdict)]); the deductions re-add to the T-460
# listed figure (+ T-508's shaft on the 1F living line) and the additions to its listed additions (asserted).
ROOM_LINES = {
    "L-71e2e002a3af624097f0": (
        [("doors OP-008 / OP-010 / OP-012 (1.00 each) + OP-021 (2.00), by id (" + T296 + ")", "5.0", RD),
         ("open passages OP-003 11.22 + OP-011 1.00 less the shared run 1.40 = the engine passage run 10.82 (" + T296 +
          "; the 1.40 PASSAGE_RUN_RESIDUAL row is the T-431 addition)", "12.22", RD),
         ("floor glazing W02 whole (sill 0.00 on section B-B, T-481 / T-483; Checker AGREE)", "6.331578", ER),
         ("floor glazing W03, its edge in this room (window-only edge, T-296)", "1.627277", ER),
         ("zone line / open side (no wall or column face at floor level, T-296 OTHER_BOUNDARY)", "2.555652", ER),
         ("open pantry wall bases (7 faces, tiled: owner wet-area rule; T-315 r2 / T-440)", "3.5", ER),
         ("pantry window W09 whole (in the tiled pantry face, T-296 / T-440)", "1.5", ER)],
        [("shared passage run added back (T-431 binding: the PASSAGE_RUN_RESIDUAL row)", "1.4", RD),
         ("south dining piece faces wall 2.70 + column 1.20 (T-431 R-T431-1, DRAWING-CONFIRMED)", "3.9", ER)]),
    "L-d32414916cfbd04c27be": (
        [("door OP-009 1.00 + arch OP-027 1.00 (" + T296 + ")", "2.0", RD)], []),
    "L-c47fc614ebc3ccde1091": (
        [("doors OP-012 1.00 + D-GF-14 0.80 (en-suite closure, T-237 width)", "1.8", RD),
         ("floor glazing W03 (window-only edge, T-296; GF-15 floor glazing)", "5.10186", ER)], []),
    "L-bb0ea96508a0dc69603c": (
        [("doors OP-005 0.90 + OP-026 0.80 (" + T296 + "; W04 base released, T-422)", "1.7", RD)], []),
    "L-ba3599ec2dc82c221617": (
        [("doors OP-005 / OP-006 / OP-008 (0.90 each) + OP-020 1.00 + D-1F-03 1.00 (" + T296 + ")", "4.7", RD),
         ("open passage OP-007 1.00 (" + T296 + ")", "1.0", RD),
         ("floor glazing W15 + W16 1.55232 each (sill 0.00, T-238 / T-422)", "3.10464", ER),
         ("W13 1.20 + W25 1.00 faces owned by the stair (MS2-LD / MS2-L / MS1 pieces, T-501 / T-508: one face one "
          "owner)", "2.2", RD),
         ("1F shaft stretches at +5.50 where no floor stands (E 4.150 + W 1.050 + 2.250 + returns 0.100 + N 1.400 + "
          "0.100; T-508 R-T508-1, Checker CONFIRMED)", "9.05", ER)], []),
    "L-309f118f6fce78b6c28e": (
        [("doors OP-006 0.90 + OP-018 0.80 (" + T296 + ")", "1.7", RD),
         ("floor glazing W17 (NW elevation chain 1.00 + 4.30 + 0.20 = 5.50 = FFL, T-483)", "3.289498", ER)], []),
    "L-a8aea28451168e4032b6": (
        [("door OP-005 0.90 (" + T296 + ")", "0.9", RD),
         ("arch OP-011 1.00 to the dressing (he also leaves it out: his joined outline - 2 x 1.00)", "1.0", "AGREE")],
        []),
    "L-4a85470b3a822d6fb7bb": (
        [("door D315 0.80 (T-483 walk by handle)", "0.8", RD),
         ("arch 1.00 (dressing side; he also leaves it out)", "1.0", "AGREE")], []),
    "L-2f58111e59f0f5213c58": (
        [("doors D-1F-03 1.00 + D-1F-04 0.80 (" + T296 + "; W24 base released, T-422)", "1.8", RD)], []),
    "L-c021ae79a3740089c3fe": (
        [("doors OP-004 0.80 + OP-020 1.00 (" + T296 + "; W14 base released, T-422)", "1.8", RD)], []),
    "L-d057b5b05b9eaf131b59": (
        [("doors OP-006 0.80 + OP-007 0.90 (" + T296 + "; W29 base released, T-422)", "1.7", RD)], []),
    "L-9ff582c99c4d8e36c9a7": (
        [("door OP-007 0.90 + lift opening OP-002 1.00 whole, no jambs (T-443; register LIFT DOOR GAP)", "1.9", RD)],
        []),
    "L-dff4f49f47f341682fb3": (
        [("door OP-001 1.00 (T-443)", "1.0", RD)], []),
}
SHAFT = {"L-ba3599ec2dc82c221617": D("9.05")}     # T-508 V3.0.56, after the T-460 V3.0.51 closure


def room_components(lines, clos):
    """Per room line: gross, deductions, additions re-added against T-460 (+ T-508) and the line's index value; the
    sub-0.000002 polygon rounding is returned as its own figure (never hidden)."""
    comp = {}
    for lid, (ded, add) in ROOM_LINES.items():
        c = clos[lid]
        if c["state"] != "CLOSES":
            raise R.RuleError(f"{lid}: T-460 closure state {c['state']}")
        gross = D(c["gross"])
        d = sum((D(x[1]) for x in ded), Z)
        a = sum((D(x[1]) for x in add), Z)
        if d != D(c["listed_ded"]) + SHAFT.get(lid, Z):
            raise R.RuleError(f"{lid}: deductions {d} != T-460 listed {c['listed_ded']} + T-508 {SHAFT.get(lid, Z)}")
        if a != D(c["listed_add"]):
            raise R.RuleError(f"{lid}: additions {a} != T-460 {c['listed_add']}")
        net = D(lines[lid]["value"])
        rnd = net - (gross - d + a)
        if rnd.copy_abs() > D("0.000002"):
            raise R.RuleError(f"{lid}: net {net} != gross {gross} - {d} + {a}")
        comp[lid] = {"gross": gross, "ded": ded, "add": add, "round": rnd}
    return comp


def C(label, amount, verdict, kind, source, bound=None):
    c = {"label": label, "amount": D(amount), "verdict": verdict, "kind": kind, "source": source}
    if bound is not None:
        c["bound"] = bound
    return c


def room_group(gid, lids, rows, comp, cells, outline, note=""):
    """outline: [(label, verdict, amount or None)] the OUTLINE terms: one None takes ours_gross - his exactly."""
    causes, gross = [], Z
    for lid in lids:
        if lid not in comp:
            continue
        k = comp[lid]
        gross += k["gross"]
        for lab, v, verdict in k["ded"]:
            causes.append(C(lab, -D(v), verdict, "DEDUCTION", "T-460 V3.0.51 closure + named source"))
        for lab, v, verdict in k["add"]:
            causes.append(C(lab, D(v), verdict, "OUTLINE" if verdict == ER else "DEDUCTION",
                            "T-460 V3.0.51 closure + named source"))
        if k["round"]:
            causes.append(C(f"{lid[:10]} polygon rounding (net vs gross - listed)", k["round"], TO, "OUTLINE",
                            "line index vs T-460 closure"))
    his = sum((_q(cells[r]) for r in rows), Z)
    fixed = sum((D(a) for _, _, a in outline if a is not None), Z)
    for lab, verdict, a in outline:
        causes.append(C(lab, (gross - his - fixed) if a is None else a, verdict, "OUTLINE", "drawn outline vs his "
                        "typed perimeter (T-106 / T-218 / T-443 readings)"))
    return {"id": gid, "unit": "lm", "lines": lids, "rows": rows, "causes": causes, "note": note}


def room_groups(lines, comp, cells):
    G = [
        room_group("GF open room: reception + dining + entrance zone + open pantry (his reception + dining and entrance "
                   "rows)", ["L-71e2e002a3af624097f0", "L-e7dcdc69e1a2b24f8616", "L-af6fb2d3474c5fbdb80a",
                             "L-73ff85e30e3a8c639e20"], ["CER.C13", "CER.C15"], comp, cells,
                   [("his two rows 58.16 + 14.76 vs the line's gross 56.006096 (the pantry box face line L-af6fb2d3 "
                     "gross 7.600 is NOT_APPLICABLE wet and sits outside this gross; the stair ST-02 zone and the "
                     "garden band D-48 edges are inside his outline; his rows carry no dimensions)", UN, None)],
                   "W02 / pantry range lines NOT_APPLICABLE (carried here, 0 lm, never a number)"),
        room_group("GF dewaneya 400 x 630 with the R1.10 corner", ["L-d32414916cfbd04c27be", "L-836720153cd9a3578f63"],
                   ["CER.C16"], comp, cells,
                   [("printed 2 x (4.00 + 6.30) - 2 x 1.10 + pi x 1.10 / 2 = 20.127876 vs his 20.00 typed", ER, None)]),
        room_group("GF master bed room", ["L-c47fc614ebc3ccde1091"], ["CER.C14"], comp, cells,
                   [("drawn face run 21.534453 vs his 21.71 typed (-0.81 %; no dimensions in his row)", TO, None)]),
        room_group("GF driver room 175 x 450", ["L-bb0ea96508a0dc69603c", "L-9b43782b7324e9de5a72"], ["CER.C17"],
                   comp, cells, [("printed 2 x (1.75 + 4.50) = 12.50 = his 12.50", "AGREE", None)]),
        room_group("1F living / open stair hall", ["L-ba3599ec2dc82c221617", "L-079bc7669b2c68d5d11b"], ["CER.C21"],
                   comp, cells,
                   [("engine room outline 52.44 (incl. the shaft perimeter ST-1F) vs his 43.78; his row carries no "
                     "dimensions, so which shaft / stair edges his perimeter takes is not established", UN, None)]),
        room_group("1F curved east bed room with its lobby (his 'bed room 1')",
                   ["L-309f118f6fce78b6c28e", "L-fbba0e0db25f6b481eaa"], ["CER.C22"], comp, cells,
                   [("drawn outline 22.15067 (curved face) vs his 22.89: no reading reproduces his row (T-218)", UN,
                     None)]),
        room_group("1F bed room 380 x 430 + dressing 165 x 180 (his 'bed room 2')",
                   ["L-a8aea28451168e4032b6", "L-4a85470b3a822d6fb7bb"], ["CER.C23"], comp, cells,
                   [("his arch reveal returns 2 x 0.15 (his outline 2 x (3.80 + 4.30) + 2 x (1.65 + 1.80) - 2 x 1.00 + "
                     "2 x 0.15 = 21.40, T-218): a jamb takes no skirting (R-T443-1)", RD, D("-0.30")),
                    ("his outline already leaves the arch out on both sides (2 x 1.00): the mirror of our two arch "
                     "deductions; printed outlines 16.20 + 6.90 otherwise equal his", "AGREE", None)],
                   "dressing: 2.800 lm of its 5.100 face behind fitted joinery stay carried, classified HELD "
                   "JOINERY_SCOPE_NOT_PRINTED (T-460; register); his outline holds them too: no gap effect"),
        room_group("1F bed room 500 x 365 (his 'bed room 3')", ["L-2f58111e59f0f5213c58", "L-5438f973929f2a38004d"],
                   ["CER.C24"], comp, cells,
                   [("drawn column notch faces 2 x 0.05 beyond the printed 2 x (5.00 + 3.65) = 17.30 = his", ER,
                     None)]),
        room_group("1F west bed room 425 x 450 (his 'bed room 4')", ["L-c021ae79a3740089c3fe", "L-049dd2e6697b0fa9dba1"],
                   ["CER.C25"], comp, cells,
                   [("printed 2 x (4.25 + 4.50) = 17.50 vs his 17.45 typed", ER, D("0.05")),
                    ("drawn column notch faces 0.20 beyond the printed rectangle (T-218)", ER, None)]),
        room_group("2F maid room 300 x 645", ["L-d057b5b05b9eaf131b59", "L-b557f2847c62d90e1aa4"], ["CER.C28"], comp,
                   cells, [("printed 2 x (3.00 + 6.45) = 18.90 vs his 19.30 typed", ER, None)]),
        room_group("2F corridor = stair-room lobby + arrival (T-443 children; parent NOT_APPLICABLE)",
                   ["L-9ff582c99c4d8e36c9a7", "L-dff4f49f47f341682fb3", "L-b8d4a7f04277deb1b0b0"], ["CER.C29"], comp,
                   cells,
                   [("slab-opening / flight-top edge 2.50 with no floor (R-T410-1, B12; T-443)", RD, D("-2.5")),
                    ("his outline 13.60 vs the drawn 12.90 (his row has no dimensions)", UN, None)]),
    ]
    used = {l for g in G for l in g["lines"]}
    wet_t296 = set()
    for r in csv.DictReader((ROOT / T296R).open(encoding="utf-8")):
        if r["kind"] == "WET":
            wet_t296 |= {x.split(":")[0] for x in r["lines"].split() if x.endswith(":NOT_APPLICABLE_WITH_EVIDENCE")}
    wet = sorted(l for l, v in lines.items() if v["class"] == "ROOM" and v["status"] == "NOT_APPLICABLE"
                 and l not in used and not v["element"].startswith(("STAIR-SKIRT:", "SKIRT-T443:"))
                 and l not in GF_STAIR_ROOM)
    if set(wet) != wet_t296:
        raise R.RuleError(f"wet NOT_APPLICABLE lines {sorted(set(wet) ^ wet_t296)} differ from the T-296 wet rooms")
    G.append({"id": f"wet rooms ({len(wet)} lines NOT_APPLICABLE: full-height wall tile owns every base)",
              "unit": "lm", "lines": wet, "rows": [],
              "causes": [C("no skirting on tiled faces (owner wet-area rule 2026-11-02; T-128 r3 / T-296); he lists no "
                           "wet-room skirting either", Z, "AGREE", "DEDUCTION", "T-296 ROOMS (WET rows)")]})
    return G


# ---- stair groups (his marble sheet; level skirting released, flights HELD by form) ---------------------------------
STAIR_OF = {"MS1": "ST-01 main", "MS2": "ST-01 main", "D1": "ST-01 main", "RS": "ST-02 round (inner)",
            "E1": "ST-03 entrance (E1)"}
GF_STAIR_ROOM = {  # T-443 children of L-47fa825d: value lines and HELD lines with the figure beside (bound hi)
    "L-af8221bd2d33bde80c67": None, "L-ca1bee789deafaf045c1": None,
    "L-4e7d3bef5e6ac89252ff": ("GF stair-hall divider band (RFI a): 2.200 cut / 3.400 outline beside", "3.4"),
    "L-6ff876aefb5a3631565c": ("OP-020 jambs 0.400 beside (RFI b: reveal owner; a jamb is not skirted by rule)", "0.4"),
    "L-d589222eace010fefa69": ("back-lobby west face 1.150 beside if on the drawn line (RFI c)", "1.15"),
    "L-47fa825d197d32754240": ("parent remainder GF-ST-CN strip north face 0.200 (unread, T-418)", "0.2"),
}
LANDING_HELD = {"STAIR-SKIRT:MS1-LD.N": "1.15", "STAIR-SKIRT:MS2-LD.W13": "0.15", "STAIR-SKIRT:MS2-LD.W25": "1.0"}


def t501():
    return {r["pid"]: r for r in csv.DictReader((ROOT / T501).open(encoding="utf-8"))}


def stair_of(element):
    pid = element.split(":", 1)[1]
    return STAIR_OF[pid.split("-")[0].split(".")[0]], pid


def stair_groups(lines, cells):
    pieces = t501()
    groups = {k: {"lines": [], "lo": Z, "hi": Z, "unb": [], "lvl_held": [], "notes": []} for k in STAIR_LM}
    flight_seen = {}
    for lid, ln in sorted(lines.items()):
        el = ln["element"]
        if lid in GF_STAIR_ROOM:
            groups["ST-01 main"]["lines"].append(lid)
            continue
        if not el.startswith("STAIR-SKIRT:"):
            continue
        st, pid = stair_of(el)
        g = groups[st]
        g["lines"].append(lid)
        if ln["class"] == "ROOM":
            if ln["value"] is None:
                g["lvl_held"].append((el, LANDING_HELD[el]))
            continue
        flight_seen.setdefault(pid, []).append(ln["code"])
    for pid, codes in sorted(flight_seen.items()):
        if sorted(codes) != ["FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG"]:
            raise R.RuleError(f"flight piece {pid}: expected one line per form, got {codes}")
        p = pieces[pid]
        z = p["zigzag_lm"] or None
        s = p["sloped_lm"] or None
        lo, hi = R.flight_bound(z, s, p["status"])
        st = STAIR_OF[pid.split("-")[0].split(".")[0]]
        g = groups[st]
        g["lo"] += lo
        if hi is None:
            g["unb"].append(pid)
        else:
            g["hi"] += hi
    out = []
    for st, cell in STAIR_LM.items():
        g = groups[st]
        ours = sum((D(lines[l]["value"]) for l in g["lines"] if lines[l]["value"] is not None), Z)
        his = _q(cells[cell])
        causes = []
        hi = None if g["unb"] else g["hi"]
        causes.append(C(f"flight skirting, form not chosen (ORR-007; one line per form, never additive): HELD-FORM "
                        f"pieces count at their smaller form, HELD / CONFLICT pieces 0 .. their figure"
                        + (f", unbounded: {', '.join(g['unb'])}" if g["unb"] else ""),
                        -g["lo"], HE, "HELD", "T-501 LINES (figures beside the blank lines)", bound=(g["lo"], hi)))
        for el, b in g["lvl_held"]:
            causes.append(C(f"held landing face {el.split(':')[1]} (sill / head vs the landing not printed)", Z, HE,
                            "HELD", "T-501 / T-508", bound=(Z, D(b))))
        if st == "ST-01 main":
            for lid, v in GF_STAIR_ROOM.items():
                if v is not None:
                    causes.append(C(v[0], Z, HE, "HELD", "T-443 / T-441", bound=(Z, D(v[1]))))
        rest = ours - his - sum((c["amount"] for c in causes), Z)
        lab = {"ST-01 main": "his main-stair row 23.10 unsplit (landing vs flight runs, plan vs pitch, whether the GF "
                             "stair hall / back lobby 6.050 sit in it: T-553 refused a match by figure) vs our level "
                             "skirting (landings MS1-LD 1.150 + MS2-LD 3.700, GF hall 4.650 + back lobby 1.400) and the "
                             "smallest form of the held flights",
               "ST-02 round (inner)": "his inner-stair row 2.40 vs our RS-LD landing 1.250 and the smallest form of "
                                      "RS-S; RS-C outer band and RS-S.S0 not established",
               "ST-03 entrance (E1)": "his entrance row 4.37 vs one drawn wall side E1.S (5 risers, plan 1.20) at its "
                                      "smallest form; whether he runs both sides or the 1.40 x 3.70 landing edge is not "
                                      "established (a landing base on a drawn wall would be an ENGINE_OMISSION: named "
                                      "for the Lead, not valued)"}[st]
        causes.append(C(lab, rest, UN, "OUTLINE", "his marble sheet rows carry no breakdown"))
        out.append({"id": st, "unit": "lm", "lines": sorted(g["lines"]), "rows": [cell], "causes": causes})
    nr = []
    risers = {"ST-03 entrance (E1)": "drawn risers 5 = his 5 (E1.S)", "ST-02 round (inner)": "the plan's 28 = his 28 "
              "(T-084)", "ST-01 main": "his 63 vs 52 .. 54 risers drawn (T-084: +9 .. +11 not on any drawing read)"}
    for st, cell in STAIR_NR.items():
        nr.append({"id": f"{st}: stair-side pieces per step (nr)", "unit": "nr", "lines": [], "rows": [cell],
                   "causes": [C(f"his pieces per step are counted in nr; our flight skirting is lm (B7-07 / B7-08), "
                                f"never converted (no printed piece size); count check: {risers[st]}",
                                -_q(cells[cell]), RD, "UNIT", "R-T574-1 (b)")]})
    return out, nr


def outdoor_group(cells):
    return [{"id": "OUTDOOR court / yard skirting (his yard row)", "unit": "lm", "lines": [], "rows": ["MRB.G13"],
             "causes": [C("no outdoor skirting item in the candidate and no owner outdoor rule on a court base; the "
                          "court is interlock (OWNER_RULE_OUTDOOR_FLOORS), only the side walk is porcelain 21.0142 m2 "
                          "(T-553); whether the court walls take a base is not printed: completeness item for the Lead "
                          "(a possible ENGINE_OMISSION on the side-walk walls), never 0", -_q(cells["MRB.G13"]), UN,
                          "SCOPE", "this run")]}]


def S(x):
    return None if x is None else str(x)


def G_out(t):
    return [{"id": g["id"], "unit": g["unit"], "ours": S(g["ours"]), "his": S(g["his"]), "gap": S(g["gap"]),
             "pct": S(g["pct"]), "outline_gap": S(g["outline_gap"]),
             "held_bound": [S(g["held_bound"][0]), S(g["held_bound"][1])], "lines": g["lines"], "rows": g["rows"],
             "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"], "amount": S(c["amount"]),
                         **({"bound": [S(c["bound"][0]), S(c["bound"][1])]} if "bound" in c else {}),
                         "source": c["source"]} for c in g["causes"]],
             **({"note": g["note"]} if g.get("note") else {})} for g in t["groups"]]


def tot(t):
    return {u: {"ours": S(v["ours"]), "his": S(v["his"]), "gap": S(v["ours"] - v["his"]),
                "pct": (S(((v["ours"] - v["his"]) / v["his"] * 100).quantize(Decimal("0.01")))
                        if v["his"] and v["comparable"] else None),
                **({} if v["comparable"] else {"pct_withheld": "a group of this unit carries a HELD, scope or unit "
                                                               "cause (R-T574-1 (e))"})}
            for u, v in t["totals"].items()}


def build():
    pins()
    lines = candidate_lines()
    cells = his_cells()
    rows = rows_table(cells)
    comp = room_components(lines, t460())
    rg = room_groups(lines, comp, cells)
    room_ids = {l for g in rg for l in g["lines"]}
    room_lines = {k: v for k, v in lines.items() if k in room_ids}
    room_rows = {k: v for k, v in rows.items() if k.startswith("CER.")}
    tr = R.reconcile(rg, room_lines, room_rows)
    sg, ng = stair_groups(lines, cells)
    st_lines = {k: v for k, v in lines.items() if k not in room_ids}
    st_rows = {k: v for k, v in rows.items() if k.startswith("MRB.") and k != "MRB.G13"}
    ts = R.reconcile(sg + ng, st_lines, st_rows)
    to = R.reconcile(outdoor_group(cells), {}, {"MRB.G13": rows["MRB.G13"]})
    if set(room_lines) | set(st_lines) != set(lines) or set(room_lines) & set(st_lines):
        raise R.RuleError("a skirting line outside both tables or in both")
    gross_ours = sum((comp[l]["gross"] for l in comp if l in room_ids), Z)
    outline = sum((g["outline_gap"] for g in tr["groups"]), Z)
    bv = {f"{u} {v}": S(a) for (u, v), a in sorted(R.by_verdict(tr).items())}
    lfl = R.like_for_like(tr)
    released = sum((D(v["value"]) for v in lines.values() if v["value"] is not None), Z)
    return {
        "schema": "T574_SKIRTING_RECONCILE_V1", "rule": "R-T574-1", "candidate": "ARCH_TAKEOFF_V3.0.58",
        "line_index": LINE_INDEX, "pins": PINS,
        "candidate_fin_skirting_released_lm": S(released),
        "room": {"groups": G_out(tr), "totals": tot(tr), "by_verdict": bv,
                 "gross_vs_gross": {"ours_line_gross": S(gross_ours), "his": S(tr["totals"]["lm"]["his"]),
                                    "ours_outline": S(tr["totals"]["lm"]["his"] + outline),
                                    "outline_gap": S(outline),
                                    "pct": S((outline / tr["totals"]["lm"]["his"] * 100).quantize(Decimal("0.01"))),
                                    "note": "outline = line gross + faces added (T-431 dining piece) + polygon "
                                            "rounding; his rows are gross perimeters (no deduction)"},
                 "like_for_like_net": {"ours": S(lfl[0]), "his": S(lfl[1]), "gap": S(lfl[2]), "pct": S(lfl[3]),
                                       "note": "every room group has a % (no HELD cause); the net % is dominated by the "
                                               "door / passage RULE_DIFFERENCE and is not a verdict"}},
        "stairs": {"groups": G_out(ts), "totals": tot(ts),
                   "note": "level skirting (FIN.SKIRTING landings + GF stair room) and the HELD flight lines vs his "
                           "marble rows (lm); his pieces per step (nr) are their own groups, never converted"},
        "outdoor": {"groups": G_out(to), "totals": tot(to)},
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != out:
            raise SystemExit("T574 output differs from a rebuild")
        print("T574 check: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    main(sys.argv[1:])
