"""T-778 (lane S, DELIVERY MODE F-16): NON-BEAM STR.CONC candidate vs freelancer, split by element into named causes.

    python3 -I research/agents_t778/nonbeam_vs_freelancer.py            # writes research/agents_t778/out/NONBEAM_CAUSES.{json,md}
    python3 -I research/agents_t778/nonbeam_vs_freelancer.py --check    # synthetic self-test + rebuild must equal the files

Inputs (committed only; no private file is read; only per-element aggregates of his rows are written):
  research/agents_t770/out/LINE_INDEX_V3_0_81.json    newest candidate index
  research/agents_t761/out/FIX_ROWS.json, research/agents_t757/out/FIX_ROWS.json   merged fills (T-757 last, as T-757 / T-777)
  research/agents_t776/out/FIX_ROWS.json              merged boundary rows (bridge only: T-776 lines are not re-split here)
  research/agents_t777/out/BEAM_CAUSES.json           merged beam split (bridge only)
  research/agents_t170/LEDGER_T170.csv                ground-beam band footprints (plan m2 per band)
  research/agents_t391/summary_t391.json              own ground-slab network (panels, strips) of the GB plan
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json his RC workbook rows (committed by B1)

Generic rule (NONBEAM_COMPARE_V1, proposed; every villa): a concrete element family is compared with another takeoff
only (1) after both sides are bounded to the same physical scope (his summary-sheet sum may leave items out: plain
concrete, parapets, lintels), (2) per mark and storey for counted members, the difference split exactly by sequential
substitution into COUNT (n_e - n_h) A_h H_h, SECTION n_e (A_e - A_h) H_h and HEIGHT n_e A_e (H_e - H_h), (3) the
height term of a column split again into the joint head his frame leaves to the beams (A_e x his head deduction, a
RULE_DIFFERENCE that the beam comparison carries with the opposite sign) and the storey / base remainder, and (4) any
piece one side has under no row of the other kept as its own cause, never folded into a neighbour.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
INDEX = "research/agents_t770/out/LINE_INDEX_V3_0_81.json"
FIXES = ("research/agents_t761/out/FIX_ROWS.json", "research/agents_t757/out/FIX_ROWS.json")
T776 = "research/agents_t776/out/FIX_ROWS.json"
T777 = "research/agents_t777/out/BEAM_CAUSES.json"
GB_LEDGER = "research/agents_t170/LEDGER_T170.csv"
T391 = "research/agents_t391/summary_t391.json"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
MATERIALITY = 0.01          # owner: nothing below 1 % of the element is worked on (DELIVERY_MODE s.3)
HIS_HEAD = 0.75             # his column heights = storey - 0.75 on every row (GF 3.75 = 4.50 - 0.75; 1F / roof 3.45 = 4.20 - 0.75)
STOREY_H = {"GF": 4.50, "1F": 4.20, "2F": 4.20}   # printed FFL frame (T-214, AGENT_BRIEF Heights)
COL_SECTIONS = (0.08, 0.10, 0.125, 0.14, 0.15, 0.175, 0.18, 0.20, 0.225, 0.25, 0.275)   # schedule CGT + drawn 0.20 x 0.40
NECK_FOU = {"C1": 0.15, "C2": 0.15, "C3": 0.15, "C4": 0.15, "C": 0.15, "C5": 0.18, "C6": 0.21, "C7": 0.24, "C8": 0.27,
            "C9": 0.30, "C10": 0.21, "C11": 0.33, "CN": 0.09}   # ST p.9 schedule 'FOU' 30 x ..; CN drawn 0.30 x 0.30


# ------------------------------------------------------------------------------------------------ generic rules (any villa)
def split_count_section_height(n_e, A_e, H_e, n_h, A_h, H_h):
    """Exact split of sum(A_e H_e) - n_h A_h H_h for one mark: lists A_e / H_e per engine member; his one row."""
    if len(A_e) != n_e or len(H_e) != n_e:
        raise ValueError("engine member lists do not match the count")
    for v in list(A_e) + list(H_e) + [A_h, H_h]:
        if v is None or v < 0:
            raise ValueError("a dimension is missing or negative: no split (never 0 by absence)")
    count = (n_e - n_h) * A_h * H_h
    section = sum(a - A_h for a in A_e) * H_h
    height = sum(a * (h - H_h) for a, h in zip(A_e, H_e))
    return count, section, height


def split_column_height(A_e, H_e, H_h, head=HIS_HEAD):
    """Column height term = JOINT_HEAD (A x his head: the joint his frame leaves to the beams) + STOREY_BASE remainder."""
    joint = sum(a * head for a in A_e)
    rest = sum(a * (h - H_h - head) for a, h in zip(A_e, H_e))
    return joint, rest


def schedule_section(v, h, sections=COL_SECTIONS, tol=5e-4):
    """A column's section from its figure and height, accepted only when it is a printed / drawn section."""
    a = v / h
    for s in sections:
        if abs(a - s) <= tol:
            return s
    return None


def close(diff, causes):
    """Residual after the named causes (what no cause explains)."""
    return round(diff - sum(causes.values()), 6)


# ------------------------------------------------------------------------------------------------ inputs
def _load():
    L = json.load(open(ROOT / INDEX))
    fx = {}
    for f in FIXES:
        for r in json.load(open(ROOT / f))["rows"]:
            fx[r["line_id"]] = (f.split("/")[1].replace("agents_", "").upper(), r)
    raw = json.load(open(ROOT / RAW, encoding="utf-8"))
    return L, fx, raw


def engine_lines(L, fx, item):
    out = []
    for l in L["lines"]:
        if l["item_code"] != item or l["class"] == "EXCLUDED":
            continue
        src, r = fx.get(l["line_id"], (None, None))
        if r:
            a = r["after"]
            if "net" not in a or a["net"] is None:
                raise ValueError(f"{l['line_id']}: fix row leaves the line HELD")
            v, label, basis = a["net"], r["label"], r.get("basis", "")
        elif l["class"] == "RELEASED":
            v, label, src, basis = l["measured_net"], "MEASURED", "INDEX", ""
        else:
            raise ValueError(f"{l['line_id']}: HELD with no fix row (never 0)")
        out.append(dict(line_id=l["line_id"], element_id=l["element_id"], m3=v, label=label, src=src, basis=basis))
    return out


def his_sheet(raw, sheet):
    rows = {}
    for x in raw["rows"]:
        if x.get("sheet") == sheet:
            rows[int(x["row"])] = {k: c.get("v") for k, c in x["cells"].items()}
    return rows


def _num(x):
    return x if isinstance(x, (int, float)) else None


def his_rows(rows, lo, hi, cols="BCDF", vcol="I"):
    """His member rows lo..hi: mark, three dims, count, net m3 (his own cell)."""
    out = []
    for r in range(lo, hi + 1):
        c = rows.get(r, {})
        v = _num(c.get(f"{vcol}{r}"))
        if v is None:
            continue
        b, l_, d, n = (_num(c.get(f"{k}{r}")) for k in cols)
        out.append(dict(row=r, mark=(c.get(f"A{r}") or "").strip(), b=b, l=l_, d=d, n=n or 1, m3=v))
    return out


# ------------------------------------------------------------------------------------------------ families
def fam_footings(L, fx, raw):
    """Isolated / combined footings (STR.CONC.FOOTING) vs his footings sheet rows F .. F.N (rows 13-28)."""
    eng = engine_lines(L, fx, "STR.CONC.FOOTING")
    his = his_rows(his_sheet(raw, "القواعد"), 13, 28)
    e = sum(x["m3"] for x in eng)
    h = sum(x["m3"] for x in his)
    by_e = defaultdict(list)
    for x in eng:
        m = re.search(r"FTG:SH10:([A-Z0-9]+)@", x["element_id"])
        by_e[m.group(1) if m else "F10+F"].append(x["m3"])
    n_f3_e, n_f3_h = len(by_e["F3"]), next(r["n"] for r in his if r["mark"] == "F3")
    a_f3 = next(r["b"] * r["l"] * r["d"] for r in his if r["mark"] == "F3")
    f10_h = next(r["m3"] for r in his if r["mark"] == "F10")
    fn_e, fn_h = sum(by_e["FN"]), next(r["m3"] for r in his if r["mark"] == "F.N")
    combo = sum(by_e["F10+F"])
    causes = {
        "F-1 F3 count (2 drawn outlines vs his 1)": (n_f3_e - n_f3_h) * a_f3,
        "F-2 F10 + F one drawn outline 3.25 x 1.40 x 0.50 vs his F10 row only": combo - f10_h,
        "F-3 FN 180C clipped by F9 (0.86 m2 drawn) vs his 4 full FN": fn_e - fn_h,
    }
    verd = {
        "F-1 F3 count (2 drawn outlines vs his 1)": ("ENGINE_RIGHT", "T-233 (Checker-verified): F3 1.60 x 1.40 / 1.40 x 1.60 drawn twice on p.2, schedule 1.60 x 1.40 x 0.30 = 0.672 each"),
        "F-2 F10 + F one drawn outline 3.25 x 1.40 x 0.50 vs his F10 row only": ("RULE_DIFFERENCE", "owner Q-31 C 'the bigger area' = the drawn outline (DEFAULT, T-757); of +0.315: the F pad 0.216 he leaves out of his 4 F rows (ENGINE_RIGHT, 5 F tags drawn) and 0.099 outline vs schedule rows (Q-31 rule)"),
        "F-3 FN 180C clipped by F9 (0.86 m2 drawn) vs his 4 full FN": ("ENGINE_RIGHT", "T-233: the notch 0.40 x 0.35 is the F9 / FN intersection drawn once, F9 (0.55 deep) owns it (R-CONC-OWN-1); he counts it twice"),
    }
    return dict(engine=e, his=h, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="footings sheet rows 13-28 (F .. F.N)")


def fam_straps(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.STRAP")
    his = his_rows(his_sheet(raw, "القواعد"), 29, 31)
    e, h = sum(x["m3"] for x in eng), sum(x["m3"] for x in his)
    causes = {"S-1 SB3 part inside the F3 outline above the F3 top + net plan vs his rounded axis lengths": e - h}
    verd = {"S-1 SB3 part inside the F3 outline above the F3 top + net plan vs his rounded axis lengths":
            ("ENGINE_RIGHT", "T-233 / T-230: SB1 1.5925 equal; SB2 net plan 1.1464 vs his 0.5 x 1.0 x 2.30 = 1.15; SB3 0.6516 + 0.0295 above the F3 top (one solid, D-15) vs his 0.65; below materiality (1 % = 0.034 m3)")}
    return dict(engine=e, his=h, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="footings sheet rows 29-31 (STB1-3)")


def _col_key(x):
    e = x["element_id"]
    m = re.search(r"COL:SH12:([A-Z0-9]+)@[^|]*\|(GF|1F|2F)", e)
    if m:
        return m.group(2), m.group(1)
    pc = {"PC-1F-A": ("1F", "PC2"), "PC-1F-B": ("1F", "PC1"), "PC-2F": ("2F", "PC")}
    for k, v in pc.items():
        if k + ":" in e:
            return v
    raise KeyError(e)


def column_member(x, storey):
    """(A, H, how) of one engine column line: H from its basis when printed there, else the storey frame; a figure that
    is not a printed section at the storey height is tried at the T-576 base (+0.25 annex level: 5.20 m on GF)."""
    b = x["basis"]
    m = re.search(r"(?:\bh|storey) ([\d.]+)", b)
    if m:
        H = float(m.group(1))
        a = re.search(r"= ([\d.]+) m2", b) or re.search(r"section ([\d.]+) m2", b) or re.search(r"drawn [\d.]+ x [\d.]+ .*?: ([\d.]+) m2", b)
        A = float(a.group(1)) if a else schedule_section(x["m3"], H)
        return A, H, "basis"
    H = STOREY_H[storey]
    A = schedule_section(x["m3"], H)
    if A is None and storey == "GF":
        H = 5.20                                    # T-576 BASE: column 35F family from +0.25 to +5.45
        A = schedule_section(x["m3"], H)
    if A is None:
        raise ValueError(f"{x['line_id']}: no printed section fits {x['m3']} at the storey heights")
    return A, H, "frame"


def fam_columns(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.COLUMN")
    sh = his_sheet(raw, "الحوائط + الأعمدة")
    his = {"GF": his_rows(sh, 36, 47), "1F": his_rows(sh, 52, 61), "2F": his_rows(sh, 66, 71)}
    e_by = defaultdict(list)
    for x in eng:
        s, mk = _col_key(x)
        A, H, how = column_member(x, s)
        if abs(A * H - x["m3"]) > 5e-4:
            raise ValueError(f"{x['line_id']}: A x H {A * H:.4f} != figure {x['m3']}")
        e_by[(s, mk)].append((A, H, x))
    h_by = {(s, r["mark"]): r for s, rs in his.items() for r in rs}
    causes = defaultdict(float)
    per = []
    for k in sorted(set(e_by) | set(h_by), key=lambda k: ({"GF": 0, "1F": 1, "2F": 2}[k[0]], k[1])):
        es, hr = e_by.get(k, []), h_by.get(k)
        A_e, H_e = [a for a, _, _ in es], [hh for _, hh, _ in es]
        if hr is None:
            causes["C-1 COUNT engine-only mark"] += sum(a * hh for a, hh in zip(A_e, H_e))
            per.append(dict(storey=k[0], mark=k[1], n_e=len(es), n_h=0, engine=round(sum(a * hh for a, hh in zip(A_e, H_e)), 4), his=0.0))
            continue
        A_h, H_h = hr["b"] * hr["l"], hr["d"]
        c, s_, hgt = split_count_section_height(len(es), A_e, H_e, hr["n"], A_h, H_h) if es else (-hr["m3"], 0.0, 0.0)
        joint, rest = split_column_height(A_e, H_e, H_h) if es else (0.0, 0.0)
        causes[f"C-2 COUNT {k[0]}"] += c
        causes["C-3 SECTION (drawn / CONFLICT reading vs his row)"] += s_
        causes["C-4 JOINT_HEAD his columns stop under the beams (A x 0.75)"] += joint
        causes[f"C-5 STOREY_BASE {k[0]}"] += rest
        per.append(dict(storey=k[0], mark=k[1], n_e=len(es), n_h=hr["n"], engine=round(sum(a * hh for a, hh in zip(A_e, H_e)), 4),
                        his=round(hr["m3"], 4), count=round(c, 4), section=round(s_, 4), joint=round(joint, 4), storey_base=round(rest, 4),
                        A_e=sorted({a for a in A_e}), H_e=sorted({hh for hh in H_e}), A_h=round(A_h, 4), H_h=H_h))
    e = sum(x["m3"] for x in eng)
    h = sum(r["m3"] for rs in his.values() for r in rs)
    verd = {
        "C-2 COUNT GF": ("ENGINE_RIGHT", "T-576 (merged): the GF roof plan draws 30 SOLID members, all on registered positions; his GF rows carry C1 x2 / C2 x6 / C9 x3 that his own neck rows (C1 x1, C2 x4, C9 x2) and the drawing do not, and miss one drawn C11 (35C / 37D) and the 10AE position"),
        "C-2 COUNT 1F": ("UNRESOLVED", "mark assignment, not traced member by member: engine 20 x 1F members vs his 19; per mark C3 -1, C7 -1, C8 +1, C9 +1 (+ C6 +1 in C-1): the 10E0 member is the C8 / C7 CONFLICT (T-566; he lists C7 x2 / C8 x1, the engine C7 x1 / C8 x2), the rest moves between C3 / C6 / C9 positions; designer mark answer (D-66) settles it"),
        "C-2 COUNT 2F": ("ENGINE_RIGHT", "2F columns on the SFRS positions his roof rows omit (C9 second position, C2 / C3 / C5 tank columns; T-757 / T-761 schedule CGT 2ND rows)"),
        "C-3 SECTION (drawn / CONFLICT reading vs his row)": ("UNRESOLVED", "C8 10E0 drawn 0.25 x 0.80 (fits C7, T-566 CONFLICT) vs his C8 / C7 rows; 1F / 2F CGT sections vs his 0.20 widths; designer mark answer replaces it"),
        "C-4 JOINT_HEAD his columns stop under the beams (A x 0.75)": ("RULE_DIFFERENCE", "joint ownership (R-CONC-OWN-1): the candidate's column runs slab top to slab top and owns the joint; his stops 0.75 below and his beams run through the support. The same volume sits in T-777 C2c2 -8.32 m3 with the opposite sign: compare beams + columns together"),
        "C-5 STOREY_BASE GF": ("ENGINE_RIGHT", "annex columns to the annex roof (+4.30 printed - 0.175 roof build-up DEFAULT - base +0.25 = 3.875 m) vs his 3.75 + 0.75 frame (-0.625 m each), and the 35F family from the +0.25 base (5.20 m, T-576 BASE)"),
        "C-5 STOREY_BASE 2F": ("UNRESOLVED", "2F height 4.075 = +13.90 printed - 0.175 roof build-up company DEFAULT - 9.65 vs his frame 4.20 (-0.125 m each); the roof build-up is a DEFAULT, the designer's roof section replaces it"),
        "C-5 STOREY_BASE 1F": ("AGREE", "1F 4.20 both frames"),
        "C-1 COUNT engine-only mark": ("UNRESOLVED", "1F C6 (schedule CGT 1ST 20 x 60, DEFAULT section): his 1F rows carry no C6; part of the 1F mark assignment in C-2 COUNT 1F"),
    }
    return dict(engine=e, his=h, causes=dict(causes), verdicts=verd, lines=[x["line_id"] for x in eng], per_mark=per,
                his_rows="walls + columns sheet rows 36-47 (GF), 52-61 (1F), 66-71 (roof)")


def neck_member(x):
    b = x["basis"]
    m = re.search(r"NECK:COL:SH10:([A-Z0-9]+)@", x["element_id"])
    mk = m.group(1)
    a = re.search(r"section ([\d.]+) m2", b)
    if a:
        A = float(a.group(1))
    elif "drawn 30 x 80" in b:
        A = 0.24
    else:
        A = NECK_FOU[mk]
    return mk, A, x["m3"] / A


def fam_necks(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.NECK")
    his = his_rows(his_sheet(raw, "الحوائط + الأعمدة"), 16, 28)
    e_by = defaultdict(list)
    for x in eng:
        mk, A, H = neck_member(x)
        e_by[mk].append((A, H, x))
    causes = defaultdict(float)
    per = []
    for r in his:
        es = e_by.get(r["mark"], [])
        A_h, H_h = r["b"] * r["l"], r["d"]
        c, s_, hgt = split_count_section_height(len(es), [a for a, _, _ in es], [h for _, h, _ in es], r["n"], A_h, H_h)
        causes["N-1 COUNT"] += c
        causes["N-2 SECTION (C11 schedule FOU 30 x 110 vs his 40 x 110)"] += s_
        dr = sum(a * (h - H_h) for a, h, x in es if x["label"] == "DRAWING-READ")
        causes["N-3 HEIGHT drawing-read (founding at the printed minimum, footing H)"] += dr
        causes["N-4 HEIGHT default / low-bound lines"] += hgt - dr
        per.append(dict(mark=r["mark"], n_e=len(es), n_h=r["n"], engine=round(sum(x["m3"] for _, _, x in es), 4), his=round(r["m3"], 4),
                        count=round(c, 4), section=round(s_, 4), height=round(hgt, 4), H_e=sorted({round(h, 3) for _, h, _ in es})))
    if set(e_by) - {r["mark"] for r in his}:
        raise ValueError("engine neck mark with no row of his: keep it as its own cause")
    e, h = sum(x["m3"] for x in eng), sum(r["m3"] for r in his)
    verd = {
        "N-1 COUNT": ("ENGINE_RIGHT", "C11 two drawn positions (10BA / 10DD; GF columns 35C / 37D, T-576) vs his one row; one more C3 / C position (10AE CONFLICT C3 vs C: the position is drawn whatever its mark)"),
        "N-2 SECTION (C11 schedule FOU 30 x 110 vs his 40 x 110)": ("ENGINE_RIGHT", "ST p.9 schedule FOU row C11 30 x 110 (company default: the schedule governs a column); his 0.40 is the C11 storey width, not the neck row"),
        "N-3 HEIGHT drawing-read (founding at the printed minimum, footing H)": ("ENGINE_RIGHT", "neck = top +0.95 down to the footing top over a founding at the printed minimum 1.50 below EG (ST p.9 n.1) less the 0.17 stack and the scheduled footing H (0.30 .. 0.70): his flat 1.50 ignores the footing depth printed per type (T-657); a deeper formation (Q-21 C) raises both sides"),
        "N-4 HEIGHT default / low-bound lines": ("UNRESOLVED", "route G base heights (lift raft level D-43) and low bounds kept under the 0.05 m3 materiality (widths in SAFETY)"),
    }
    return dict(engine=e, his=h, causes=dict(causes), verdicts=verd, lines=[x["line_id"] for x in eng], per_mark=per,
                his_rows="walls + columns sheet rows 16-28 (necks)")


def fam_ground_beams(L, fx, raw):
    """Building ground beams (STR.CONC.GROUND_BEAM without the boundary band) vs his longitudinal + transverse rows."""
    eng = [x for x in engine_lines(L, fx, "STR.CONC.GROUND_BEAM") if "BOUNDARY_GB_NG" not in x["element_id"]]
    led = {r["id"]: r for r in csv.DictReader(open(ROOT / GB_LEDGER))}
    his = his_rows(his_sheet(raw, "الشناجات"), 13, 14)
    A_h = his[0]["b"] * his[0]["d"]
    L_h = sum(r["l"] for r in his)
    groups = defaultdict(lambda: [0, 0.0, 0.0])
    unbound = []
    for x in eng:
        k = x["element_id"].split(":", 1)[1].split("#")[0]
        k = re.sub(r":7[0-9A-F]{2}\+7[0-9A-F]{2}$", "", k)
        m = re.search(r"drawn plan ([\d.]+) m2", x["basis"])
        if m:
            fp = float(m.group(1))
        elif k in ("GROUND_BEAMS:GROUND:BAND0023", "GROUND_BEAMS:GROUND:BAND0032"):
            fp = 1.0575            # the band's other half (#1 / #2 lines print 1.0575 m2 each); the ledger row is the whole band
        elif k in led and led[k]["footprint_m2"]:
            fp = float(led[k]["footprint_m2"])
        else:
            unbound.append(x)
            continue
        D = round(x["m3"] / fp, 2)
        cls = ("exterior main house D 0.95 (two printed levels; ring 157 / 158 with end pieces)" if D >= 0.9 else
               f"interior p.13 class D {D:.2f}")
        g = groups[(x["label"] if x["label"] != "DRAWING-READ" else "MEASURED", cls)]
        g[0] += 1
        g[1] += fp / 0.30
        g[2] += x["m3"]
    L_e = sum(g[1] for g in groups.values())
    causes = {}
    for (lab, cls), (n, Lg, V) in sorted(groups.items()):
        causes[f"G-1 SECTION {lab} {cls}"] = V - A_h * Lg
    causes["G-2 LENGTH his lump 211 m vs the engine's bound runs face to face"] = A_h * (L_e - L_h)
    causes["G-3 unbound piece (no footprint in the band ledger)"] = sum(x["m3"] for x in unbound)
    e, h = sum(x["m3"] for x in eng), sum(r["m3"] for r in his)
    verd = {}
    for k in causes:
        if "0.95" in k:
            verd[k] = ("ENGINE_RIGHT", "T-289 / T-391 (Checker-verified basis): top +0.95 to N.G. +-0.00 printed by two levels on the exterior main-house beams; his 0.60 everywhere")
        elif "MEASURED" in k and "0.60" in k:
            verd[k] = ("AGREE", "p.13 typical 30 x 60 both sides")
        elif "MEASURED" in k:
            verd[k] = ("ENGINE_RIGHT", "ST p.13 typical sections by clear span (< 2.5 m 30 x 30, < 5 m 30 x 40, > 5 m 30 x 60; T-242 / T-391): his one 30 x 60 section on every run")
        elif "DEFAULT" in k and "0.60" in k:
            verd[k] = ("AGREE", "typical 30 x 60 by clear span (DEFAULT on held runs) = his section")
        elif "DEFAULT" in k:
            verd[k] = ("UNRESOLVED", "held runs valued at the p.13 class by clear span (company default 'exterior GB = same mark'; designer D-33 / D-34 / D-35 replace it) or kept at the low bound under materiality")
    verd["G-2 LENGTH his lump 211 m vs the engine's bound runs face to face"] = ("UNRESOLVED", "his 100 + 111 m lies inside the drawn envelope (face to face 193.76 .. through every support 231.91 m, T-391): which supports he runs through cannot be split from two lumps")
    verd["G-3 unbound piece (no footprint in the band ledger)"] = ("UNRESOLVED", "BAND0009 0.1037 m3: valued run with no T-170 footprint row; below materiality")
    return dict(engine=e, his=h, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="ground-beam sheet rows 13-14 (longitudinal 100 m + transverse 111 m at 0.30 x 0.60)",
                engine_length_m=round(L_e, 3), his_length_m=L_h)


def fam_boundary_gb(L, fx, raw):
    eng = [x for x in engine_lines(L, fx, "STR.CONC.GROUND_BEAM") if "BOUNDARY_GB_NG" in x["element_id"]]
    his = his_rows(his_sheet(raw, "الشناجات"), 15, 15)[0]
    e = sum(x["m3"] for x in eng)
    L_e, A_e = 8.814 / 0.20, 0.20 * 0.40            # basis: 8.8140 m2 (Checker own) / 0.20 printed width; 'GROUND BEAM (20x40)'
    A_h, L_h = his["b"] * his["d"], his["l"]
    causes = {"B-1 SECTION ST p.14 'GROUND BEAM (20x40)' vs his 0.30 x 0.60": (A_e - A_h) * L_h,
              "B-2 LENGTH 5 drawn runs 44.07 m vs his 42 m": A_e * (L_e - L_h)}
    verd = {"B-1 SECTION ST p.14 'GROUND BEAM (20x40)' vs his 0.30 x 0.60": ("ENGINE_RIGHT", "printed section on ST p.14 A-A (T-761 DRAWING-READ, Checker plan 8.814 m2)"),
            "B-2 LENGTH 5 drawn runs 44.07 m vs his 42 m": ("ENGINE_RIGHT", "drawn fence-side runs 44.07 m (T-254 / T-761); his 42 m a round figure")}
    return dict(engine=e, his=his["m3"], causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="ground-beam sheet row 15 (fence ground beam)")


def fam_ground_slab(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.GROUND_SLAB")
    hr = his_sheet(raw, "الشناجات")[11]
    his_m2, t = _num(hr["B11"]), _num(hr["D11"])
    s = json.load(open(ROOT / T391))["slab"]
    e = sum(x["m3"] for x in eng)
    causes = {"GS-1 his plate over the beam / column / lift strips the beams own": -s["own_strips_m2"] * t,
              "GS-2 his area beyond the whole drawn network": -(his_m2 - s["own_network_m2"]) * t,
              "GS-3 engine faces vs own panels (T-391 F3 small reads)": e - s["own_panels_m2"] * t}
    verd = {"GS-1 his plate over the beam / column / lift strips the beams own": ("ENGINE_RIGHT", "T-391 (merged): 71.8821 m2 of strips under his one 295.5 m2 plate; the ground beams already carry that concrete full depth from the slab top (C1)"),
            "GS-2 his area beyond the whole drawn network": ("ENGINE_RIGHT", "his 295.5 m2 exceeds the own network 289.1136 m2 (panels + strips) of the GB plan: 6.39 m2 on no drawn element"),
            "GS-3 engine faces vs own panels (T-391 F3 small reads)": ("UNRESOLVED", "member overlap in 49a7dae5, court-side split at arc 158, lift-side oblique panels (T-391 F3); below 1 %")}
    return dict(engine=e, his=his_m2 * t, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="ground-beam sheet row 11 (ground slab 295.5 m2 x 0.10)")


STAIR_GROUP = {"L-e37d81a8": "ST-01", "L-7863355d": "ST-01", "L-67e4b048": "ST-01", "L-bb0e57b1": "ST-01", "L-2416e65f": "ST-01",
               "L-659243ed": "ST-01", "L-056402f9": "ST-02", "L-b6b0354b": "ST-02", "L-061e18cf": "ST-03",
               "L-85f64587": "ST-01b", "L-821032bc": "ST-01b"}


def fam_stairs(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.STAIR")
    sh = his_sheet(raw, "السلم")
    g = defaultdict(float)
    for x in eng:
        g[STAIR_GROUP[x["line_id"][:10]]] += x["m3"]
    his = {"ST-03": _num(sh[11]["G11"]), "ST-02": _num(sh[12]["G12"]), "ST-01": _num(sh[20]["G20"]) + _num(sh[21]["G21"])}
    # T-258 (merged) component steps, his minus drawing, m3
    st01_t258 = dict(length=2.275333, thickness=0.812307, heads_in_beams=0.140161, landing_area=0.133, landing_t=0.175)
    causes = {
        "ST-1 ST-01 his 4 x 5.30 m sloped length vs drawn 14.428 m": -st01_t258["length"],
        "ST-2 ST-01 his 0.28 / 0.20 plates vs drawn equivalent 0.2331 / T 16": -(st01_t258["thickness"] + st01_t258["landing_t"]),
        "ST-3 ST-01 landing area 5.04 vs drawn 4.375 m2": -st01_t258["landing_area"],
        "ST-4 ST-01 flight heads / foot billed in the beams B20 / B23": -st01_t258["heads_in_beams"],
        "ST-5 ST-02 5.537 m of his 16.4 m run on no drawing": -1.860373,
        "ST-6 ST-02 curved part: his flat 1.2 x 0.28 vs wedges + helicoid waist (ESTIMATE)": g["ST-02"] - (his["ST-02"] - 1.860373),
        "ST-7 ST-03 his run 1.80 vs drawn 1.20 m": -0.4704,
        "ST-8 ST-03 his 0.28 flat vs steps + 0.16 waist on the slope (ESTIMATE)": g["ST-03"] - (his["ST-03"] - 0.4704),
        "ST-9 ST-01b lobby flight not in his sheet": g["ST-01b"],
    }
    # ST-01 remainder: the turn pieces (winder wedges, flat turn, turn riser) the T-258 drawing table held without value
    causes["ST-10 ST-01 turn pieces (winders, flat turn, turn riser) DEFAULT"] = (g["ST-01"] - his["ST-01"]) - sum(
        causes[k] for k in causes if k.startswith(("ST-1 ", "ST-2 ", "ST-3 ", "ST-4 ")))
    verd = {
        "ST-1 ST-01 his 4 x 5.30 m sloped length vs drawn 14.428 m": ("ENGINE_RIGHT", "T-258 (merged): his 5.30 m per flight includes the floor landing; drawn sloped flights 14.428 m"),
        "ST-2 ST-01 his 0.28 / 0.20 plates vs drawn equivalent 0.2331 / T 16": ("RULE_DIFFERENCE", "his flat 'slab + steps' plate vs the drawn waist T 16 + step triangles (T-258)"),
        "ST-3 ST-01 landing area 5.04 vs drawn 4.375 m2": ("ENGINE_RIGHT", "T-258: landings 3 x 1.2 x 1.4 vs drawn MS1-LD + MS2-LD W / E"),
        "ST-4 ST-01 flight heads / foot billed in the beams B20 / B23": ("RULE_DIFFERENCE", "joint ownership: the flight ends inside B20 / B23 are beam concrete in the candidate"),
        "ST-5 ST-02 5.537 m of his 16.4 m run on no drawing": ("ENGINE_RIGHT", "T-258: outer string sloped 10.863 m drawn; 5.537 m of his run on no sheet"),
        "ST-6 ST-02 curved part: his flat 1.2 x 0.28 vs wedges + helicoid waist (ESTIMATE)": ("UNRESOLVED", "curved treads + helicoid waist 0.16 ESTIMATE (T-761); D-08 replaces it"),
        "ST-7 ST-03 his run 1.80 vs drawn 1.20 m": ("ENGINE_RIGHT", "T-258: drawn run 1.20 m (5 risers 0.170)"),
        "ST-8 ST-03 his 0.28 flat vs steps + 0.16 waist on the slope (ESTIMATE)": ("UNRESOLVED", "ST-03 prints no waist; 0.16 = the ST-01 printed plate (ESTIMATE, S-9 / D-56 replace it)"),
        "ST-9 ST-01b lobby flight not in his sheet": ("ENGINE_RIGHT", "0.1003 drawn steps (T-258); the 0.1656 waist is an ESTIMATE (0 if on compacted fill)"),
        "ST-10 ST-01 turn pieces (winders, flat turn, turn riser) DEFAULT": ("UNRESOLVED", "winder wedges + flat turn 1.44 x 0.16 + turn riser (T-711 / T-761 DEFAULT); the T-258 table held them without value"),
    }
    e, h = sum(x["m3"] for x in eng), sum(his.values())
    return dict(engine=e, his=h, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng],
                his_rows="stair sheet rows 11, 12, 20, 21", by_flight={k: round(v, 4) for k, v in sorted(g.items())},
                his_by_flight={k: round(v, 4) for k, v in sorted(his.items())})


def fam_domes(L, fx, raw):
    eng = engine_lines(L, fx, "STR.CONC.DOME")
    r = his_rows(his_sheet(raw, "السلم"), 13, 13, cols="BCDF", vcol="G")[0]
    e = sum(x["m3"] for x in eng)
    mid = 2.540681 / 0.10                              # T-185 mid-surface area of the printed shell (442 / 190 / 10)
    causes = {"D-1 his typed 22.6 m2 per dome vs the shell mid-surface 25.407 m2": r["n"] * (mid - r["l"]) * r["d"] + (e - 3 * 2.540681)}
    verd = {"D-1 his typed 22.6 m2 per dome vs the shell mid-surface 25.407 m2": ("ENGINE_RIGHT", "T-185 (Checker re-derived): ST p.7 DETAIL OF DOME rise 1.90 / span 4.42 / 0.10 shell = 2.5407 m3; the tower dome DEFAULT at the same shell (D-21); his 22.6 m2 is not the shell area")}
    return dict(engine=e, his=r["m3"], causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng], his_rows="stair sheet row 13 (3 domes)")


def fam_pool(L, fx, raw):
    eng = {x["element_id"].split(":")[-1]: x for x in engine_lines(L, fx, "STR.CONC.POOL")}
    hs = his_rows(his_sheet(raw, "حمام السباحة"), 11, 15)
    floor = hs[0]["m3"]
    walls, pump_w, steps, room_f = hs[1]["m3"], hs[2]["m3"], hs[3]["m3"], hs[4]["m3"]
    causes = {"P-1 pump room walls + floor not drawn": -(pump_w + room_f),
              "P-2 pool walls: base thickness carried into the wall, 0.20 above the rim, length": eng["WALLS"]["m3"] - walls,
              "P-3 pool floor: drawn D outline 10.9356 m2 vs his typed 10.8 m2 (both 0.40)": eng["BASE"]["m3"] - floor,
              "P-4 steps": eng["STEPS"]["m3"] - steps}
    verd = {"P-1 pump room walls + floor not drawn": ("ENGINE_RIGHT", "T-183 r2 / T-193 (merged): no pump room on any ST / arch sheet read; consultant P-2"),
            "P-2 pool walls: base thickness carried into the wall, 0.20 above the rim, length": ("ENGINE_RIGHT", "T-183: walls = band 2.3567 m2 x 1.20 (rim to base top); his 12 x 1.80 x 0.20 carries the base thickness +0.96, 0.20 above the drawn rim +0.48, length +0.05"),
            "P-3 pool floor: drawn D outline 10.9356 m2 vs his typed 10.8 m2 (both 0.40)": ("ENGINE_RIGHT", "drawn D outline 3.50 x 1.75 + pi 1.75^2 / 2 (T-385)"),
            "P-4 steps": ("AGREE", "the candidate's SAFETY block copies his size (never VERIFIED; steps not drawn)")}
    e, h = sum(x["m3"] for x in eng.values()), sum(r["m3"] for r in hs)
    return dict(engine=e, his=h, causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng.values()], his_rows="pool sheet rows 11-15")


def fam_lift(L, fx, raw):
    eng = {x["element_id"]: x for x in engine_lines(L, fx, "STR.CONC.LIFT")}
    r = his_rows(his_sheet(raw, "الحوائط + الأعمدة"), 11, 11)[0]
    pit, tie = eng["LIFT_PIT:WALLS"]["m3"], eng["LIFT_TIE_BEAM:GF"]["m3"]
    causes = {"L-1 pit wall ring plan 1.10 m2 (drawn, T-401) vs his 8 m x 0.20 = 1.60 m2, both 1.50 high": pit - r["m3"],
              "L-2 GF tie beam (ST p.8 n.19) not in his sheet": tie}
    verd = {"L-1 pit wall ring plan 1.10 m2 (drawn, T-401) vs his 8 m x 0.20 = 1.60 m2, both 1.50 high": ("ENGINE_RIGHT", "the 1.80 x 1.80 shaft ring 1.10 m2 drawn (T-401, Checker T-394): two sides are the GB / beam strips already owned; his 8 m centre-line ring counts them again. Height 1.50 SAFETY on both sides (D-43)"),
            "L-2 GF tie beam (ST p.8 n.19) not in his sheet": ("UNRESOLVED", "printed note, section not printed: DEFAULT nearest printed (shaft ring beams); D-43")}
    return dict(engine=pit + tie, his=r["m3"], causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng.values()], his_rows="walls + columns sheet row 11 (lift walls)")


def fam_blinding(L, fx, raw):
    eng = [x for x in engine_lines(L, fx, "STR.CONC.BLINDING") if "BOUNDARY_WALL_BASE" not in x["element_id"]]   # T-776 line
    r = his_rows(his_sheet(raw, "القواعد"), 11, 11)[0]
    e = sum(x["m3"] for x in eng)
    causes = {"BL-1 his plate 15.00 x 31.37 x 0.10 over the whole plot vs plain concrete under each member": e - r["m3"]}
    verd = {"BL-1 his plate 15.00 x 31.37 x 0.10 over the whole plot vs plain concrete under each member": ("RULE_DIFFERENCE", "owner table 13 Nov / T-233: he blinds the whole plot (no sheet draws a plate; P7 compacted soil under the slab); the candidate blinds under footings, ground beams, straps, pool, lift raft (boundary pads: T-776 line, in the boundary bridge part) (p.13 '10 | L x W | 10'). Outside his RC total 352.44 (his summary row 15, plain concrete)")}
    return dict(engine=e, his=r["m3"], causes=causes, verdicts=verd, lines=[x["line_id"] for x in eng], his_rows="footings sheet row 11 (outside his RC total)")


FAMILIES = (("STR.CONC.FOOTING", fam_footings), ("STR.CONC.STRAP", fam_straps), ("STR.CONC.NECK", fam_necks),
            ("STR.CONC.COLUMN", fam_columns), ("STR.CONC.GROUND_BEAM (building)", fam_ground_beams),
            ("STR.CONC.GROUND_BEAM (boundary at N.G.)", fam_boundary_gb), ("STR.CONC.GROUND_SLAB", fam_ground_slab),
            ("STR.CONC.STAIR", fam_stairs), ("STR.CONC.DOME", fam_domes), ("STR.CONC.POOL", fam_pool),
            ("STR.CONC.LIFT", fam_lift), ("STR.CONC.BLINDING", fam_blinding))


# ------------------------------------------------------------------------------------------------ build
def build():
    L, fx, raw = _load()
    fams = []
    for name, fn in FAMILIES:
        d = fn(L, fx, raw)
        diff = d["engine"] - d["his"]
        res = close(diff, d["causes"])
        fams.append(dict(family=name, engine_m3=round(d["engine"], 4), his_m3=round(d["his"], 4), diff_m3=round(diff, 4),
                         diff_pct=round(100 * diff / d["his"], 2) if d["his"] else None,
                         causes={k: round(v, 4) for k, v in d["causes"].items()},
                         verdicts={k: d["verdicts"].get(k, ("UNRESOLVED", "unnamed"))[0] for k in d["causes"]},
                         reasons={k: d["verdicts"].get(k, ("UNRESOLVED", "unnamed"))[1] for k in d["causes"]},
                         residual_m3=res, residual_pct=round(100 * abs(res) / d["his"], 4) if d["his"] else None,
                         lines=sorted(d["lines"]), his_rows=d["his_rows"],
                         **{k: d[k] for k in ("per_mark", "by_flight", "his_by_flight", "engine_length_m", "his_length_m") if k in d}))
    # ---- whole-trade bridge (engine - his RC total), every family once
    rc = his_sheet(raw, "ورقة1")
    his_total = _num(rc[24]["F24"])
    eitem = lambda it: sum(x["m3"] for x in engine_lines(L, fx, it))  # noqa: E731
    beams = json.load(open(ROOT / T777))
    slab_h = _num(rc[21]["E21"])
    parapet = eitem("STR.CONC.PARAPET")
    upstand = 1.6245 + 1.7991 + 2.9495 + 1.6779                        # ST p.14 P1 typical RC 0.30 upstand per zone (T-761 bases)
    lintel = eitem("STR.CONC.LINTEL")
    bw, bp = eitem("STR.CONC.BOUNDARY_WALL"), eitem("STR.CONC.BOUNDARY_PAD")
    bwb = sum(x["m3"] for x in engine_lines(L, fx, "STR.CONC.BLINDING") if "BOUNDARY_WALL_BASE" in x["element_id"])
    band_h = _num(his_sheet(raw, "القواعد")[32]["I32"])
    safety = json.load(open(ROOT / FIXES[1]))["safety_line"]["after"]
    t776 = json.load(open(ROOT / T776))["summary"]["delta_by_item"]
    fam_by = {f["family"]: f for f in fams}
    bridge = [
        ("T-777 beams (merged split, not re-split)", beams["engine_m3"] - beams["freelancer_total_cell"]),
        ("suspended slabs (T-694 / T-688: +0.46 named, UNRESOLVED scope of 2.98 .. 3.98 m2 1F panels)", eitem("STR.CONC.SLAB") - slab_h),
    ]
    for f in fams:
        if f["family"] != "STR.CONC.BLINDING":
            bridge.append((f["family"], f["diff_m3"]))
    bridge += [
        ("boundary wall band + pads + pad blinding (T-776 lines, not re-split; his perimeter tie beam 8.604)", bw + bp + bwb - band_h),
        ("blinding: in the candidate's concrete, outside his RC total (his plain concrete 47.055 on its own row)", fam_by["STR.CONC.BLINDING"]["engine_m3"]),
        ("parapet RC: ST p.14 typical RC 0.30 upstand his sheet omits", upstand),
        ("parapet RC above the upstand: A-A / B-B cut RC vs his parapets in blockwork (Q-65 C)", parapet - upstand),
        ("lintels: in-situ concrete figure, his lintels not in his RC sheet", lintel),
        ("STR.CONC.SAFETY line (ignored pieces + T-757 widths)", safety),
    ]
    e_total = sum(eitem(it) for it in sorted({l["item_code"] for l in L["lines"] if l["item_code"].startswith("STR.CONC.")
                                              and l["item_code"] != "STR.CONC.SAFETY"})) + safety
    diff = e_total - his_total
    resid = round(diff - sum(v for _, v in bridge), 6)
    nb = [f for f in fams if f["family"] != "STR.CONC.BLINDING"]
    return dict(schema="T778_NONBEAM_CAUSES_V1", candidate=INDEX, fixes=list(FIXES),
                engine_concrete_m3=round(e_total, 4), his_rc_total_m3=his_total, diff_m3=round(diff, 4),
                diff_pct=round(100 * diff / his_total, 2), bridge={k: round(v, 4) for k, v in bridge}, bridge_residual_m3=resid,
                nonbeam_paired=dict(engine=round(sum(f["engine_m3"] for f in nb), 4), his=round(sum(f["his_m3"] for f in nb), 4),
                                    diff=round(sum(f["diff_m3"] for f in nb), 4)),
                t776_deltas_not_in_this_base={k: v for k, v in t776.items() if k.startswith("STR.CONC")},
                beams_plus_columns_joint=dict(t777_C2c2=beams["causes"]["C2c2_LENGTH_HIS_LONGER"],
                                              t778_C4=fam_by["STR.CONC.COLUMN"]["causes"]["C-4 JOINT_HEAD his columns stop under the beams (A x 0.75)"]),
                families=fams, verdict_totals=_verdict_totals(fams))


def _verdict_totals(fams):
    t = defaultdict(float)
    for f in fams:
        for k, v in f["causes"].items():
            t[f["verdicts"][k]] += v
    return {k: round(v, 4) for k, v in sorted(t.items())}


# ------------------------------------------------------------------------------------------------ self-test (synthetic)
def selftest():
    # normal: count / section / height sum exactly; synthetic villa (not Alsenan): 3 columns 0.20 x 0.50 x 4.00 vs his 2 x 0.25 x 0.50 x 3.40
    c, s, h = split_count_section_height(3, [0.10] * 3, [4.00] * 3, 2, 0.125, 3.40)
    assert abs((c + s + h) - (3 * 0.10 * 4.00 - 2 * 0.125 * 3.40)) < 1e-12
    j, r = split_column_height([0.10] * 3, [4.00] * 3, 3.40, head=0.60)
    assert abs(j + r - h) < 1e-12 and abs(j - 0.18) < 1e-12 and abs(r) < 1e-12
    # units: mm in, m3 x 1e9 out, same split (no silent unit mix)
    c2, s2, h2 = split_count_section_height(3, [1e5] * 3, [4000] * 3, 2, 1.25e5, 3400)
    assert abs((c2 + s2 + h2) / 1e9 - (c + s + h)) < 1e-9
    # adverse: missing / negative dimension refused; member list shorter than the count refused
    for bad in ((1, [None], [4.0], 1, 0.1, 3.0), (1, [0.1], [-4.0], 1, 0.1, 3.0), (2, [0.1], [4.0], 1, 0.1, 3.0)):
        try:
            split_count_section_height(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError("bad member data accepted")
    # a figure that is no printed section at any frame height is refused (never back-filled)
    assert schedule_section(0.45, 4.50) == 0.10 and schedule_section(0.47, 4.50) is None
    # rotation / mirror do not enter (scalar dims); a closed split leaves residual 0
    assert close(1.0, {"a": 0.4, "b": 0.6}) == 0.0
    return True


def write_md(d):
    o = ["# T-778 NON-BEAM CONCRETE: candidate vs freelancer by element and named cause (Alsenan; method every villa)", "",
         f"Candidate {d['candidate']} + T-761 / T-757 fix rows (the T-757 base of 405.60 + 1.20 SAFETY). Concrete "
         f"**{d['engine_concrete_m3']:.2f} m3** vs his RC total **{d['his_rc_total_m3']:.2f} m3** (his summary sheet SUM(E17:E23); "
         f"plain concrete 47.06 sits on its own row outside it): **{d['diff_m3']:+.2f} m3 ({d['diff_pct']:+.1f} %)**. "
         f"Bridge residual **{d['bridge_residual_m3']:+.6f} m3**.", "",
         f"Non-beam elements he also carries (paired families without blinding): engine {d['nonbeam_paired']['engine']:.2f} vs "
         f"his {d['nonbeam_paired']['his']:.2f} m3 = **{d['nonbeam_paired']['diff']:+.2f} m3**. Most of the +40 m3 the Lead "
         "named is scope, not measurement: blinding, RC parapets and lintels are in the candidate's concrete and outside "
         "his RC total.", "",
         "## Bridge (engine - his RC total, m3)", "", "| part | m3 |", "|---|---|"]
    for k, v in d["bridge"].items():
        o.append(f"| {k} | {v:+.4f} |")
    o += [f"| residual | {d['bridge_residual_m3']:+.6f} |", "",
          f"T-776 (merged after the T-757 base) moves the boundary lines by {d['t776_deltas_not_in_this_base']} m3: not re-split here.",
          f"Beams + columns joint: T-777 C2c2 {d['beams_plus_columns_joint']['t777_C2c2']:+.4f} and T-778 C-4 "
          f"{d['beams_plus_columns_joint']['t778_C4']:+.4f} m3 are the same joint volume on opposite lines.", "",
          "## By verdict (all families, m3)", "", "| verdict | m3 |", "|---|---|"]
    for k, v in d["verdict_totals"].items():
        o.append(f"| {k} | {v:+.4f} |")
    o += ["", "## Fix rows", "",
          "None. Every DEFAULT / ESTIMATE / SAFETY figure inside these families was checked for a printed schedule or "
          "section that could replace it: none exists (neck base heights wait on the lift raft level D-43; 2F column "
          "heights on the roof section; held ground-beam depths on D-33 / D-34 / D-35; the stair turn pieces and waists "
          "on D-08 / D-56 / S-9; the tower dome on D-21; lift pit and tie beam on D-43; pool steps not drawn). No candidate "
          "line changes.", "",
          "## Three lines for the Checker (hand)", "",
          "1. GROUND SLAB (largest paired family difference, -7.91 m3): his 295.5 m2 x 0.10 = 29.55 vs the GB plan network "
          "289.1136 m2 = 27 panels 217.2315 + strips 71.8821 (T-391): 29.55 - 7.1882 (strips) - 0.6386 (beyond the network) "
          "= 21.7232 vs candidate 21.6409 (-0.0823 small reads).",
          "2. GF column C11 (Drive 'Alsenan chalet project' / ST7757 dxf, schedule CGT GR 25 x 110): 2 drawn x 0.275 x "
          "4.50 = 2.475 vs his 1 x 0.25 x 1.10 x 3.75 = 1.03125: COUNT +1.03125 (second drawn C11), JOINT_HEAD 2 x 0.275 x "
          "0.75 = +0.4125.",
          "3. Ground beam BAND0011.3 (exterior main house): T-170 footprint 1.905 m2 (6.35 m x 0.30) x 0.95 (top +0.95 to "
          "N.G. +-0.00, two printed levels) = 1.8097 = candidate L-e9a885323ad6; his section on the same run 6.35 x 0.18 = "
          "1.143 (-0.667)."]
    for f in d["families"]:
        o += ["", f"## {f['family']}", "",
              f"Engine **{f['engine_m3']:.4f}** vs his **{f['his_m3']:.4f} m3** ({f['his_rows']}): **{f['diff_m3']:+.4f} m3"
              + (f" ({f['diff_pct']:+.1f} %)" if f["diff_pct"] is not None else "") + f"**; residual {f['residual_m3']:+.6f} m3"
              + (f" ({f['residual_pct']:.3f} % of the element)" if f["residual_pct"] is not None else "") + ".", "",
              "| cause | m3 | verdict | reason |", "|---|---|---|---|"]
        for k, v in f["causes"].items():
            o.append(f"| {k} | {v:+.4f} | {f['verdicts'][k]} | {f['reasons'][k]} |")
        if f.get("per_mark"):
            o += ["", "| " + " | ".join(f["per_mark"][0].keys()) + " |", "|" + "---|" * len(f["per_mark"][0])]
            for r in f["per_mark"]:
                o.append("| " + " | ".join(str(r.get(k, "")) for k in f["per_mark"][0]) + " |")
        if f.get("by_flight"):
            o.append(f"\nEngine by flight {f['by_flight']}; his by flight {f['his_by_flight']}.")
        if f.get("engine_length_m"):
            o.append(f"\nEngine bound run length {f['engine_length_m']} m (plan / 0.30) vs his {f['his_length_m']} m.")
        o.append(f"\nLines ({len(f['lines'])}): " + ", ".join(f["lines"]))
    return "\n".join(o) + "\n"


def main(argv):
    selftest()
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    md = write_md(d)
    if "--check" in argv:
        ok = (OUT / "NONBEAM_CAUSES.json").read_text(encoding="utf-8") == js and \
             (OUT / "NONBEAM_CAUSES.md").read_text(encoding="utf-8") == md
        print("T778 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "NONBEAM_CAUSES.json").write_text(js, encoding="utf-8")
    (OUT / "NONBEAM_CAUSES.md").write_text(md, encoding="utf-8")
    print(json.dumps({k: d[k] for k in ("engine_concrete_m3", "his_rc_total_m3", "diff_m3", "bridge", "bridge_residual_m3",
                                        "nonbeam_paired", "verdict_totals")}, indent=1, ensure_ascii=False))
    for f in d["families"]:
        print(f"{f['family']}: {f['engine_m3']} vs {f['his_m3']} = {f['diff_m3']:+} residual {f['residual_m3']} ({f['residual_pct']} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
