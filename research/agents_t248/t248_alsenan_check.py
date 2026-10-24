"""T-248 development-villa ledger: CONC.COLUMN (columns + necks), every member once, from committed inputs only.

Inputs (all committed; drawings are read only by t248_extract.py / t217_extract.py on the private Drive copy):
  research/agents_t248/ALSENAN_COLUMN_INPUT.json   members x storey with slab-plan handles, T-119 id binding, 1B1B
  research/agents_t217/ALSENAN_SECTION_INPUT.json  T-217 inventory (FP neck -> storey outlines, planted members)
  research/agents_t217/LEDGER_T217.csv             section class per member x storey (merged 65fef8fa)
  research/agents_t205/LEDGER_T205.csv             necks: footing, H, section (merged 5f40dfdb)
  research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv   owner-method split (merged, Checker 0.0 % on 2)
  research/urban_engine_m4_correctness/st7757_route_g/PROVISIONAL_REGISTER.csv  route G column / neck lines
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json  freelancer 'الحوائط + الأعمدة' rows 11-72
Writes LEDGER_T248.csv (one row per member), BY_MARK_T248.csv (storey x mark vs freelancer), summary.json.

    python3 -I research/agents_t248/t248_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
ROOT = RES.parent
sys.path.insert(0, str(HERE))
import t248_column_line as CL  # noqa: E402

# --- structural datums (each with its source; T-214 MERGED b29060c2, T-206 MERGED d5df7d1f, T-220 MERGED 579e613d) ---
GF_MAIN_TOP_OF_GROUND = CL.Level.at(0.95, "GF structural slab top = ground-beam top 'Ground Floor slab level' (ST p.13); "
                                         "FFL +1.00 - drawn dry build-up 0.05 (T-214)")
ANNEX_GROUND = CL.Level.at(0.25, "annex ground slab top: FFL +0.30 - drawn build-up 0.05 (T-214)")
GF_ROOF = CL.Level.at(5.45, "GF roof slab top = 1F floor slab top: FFL +5.50 - 0.05 (T-214); one 0.16 plate on ST p.4, "
                            "no step drawn (T-220 reading)")
F1_ROOF = CL.Level.at(9.65, "1F roof slab top = 2F floor slab top: FFL +9.70 - 0.05 (T-214); one plate on ST p.5 (T-220)")
ROOF_2F = CL.Level.held(None, 13.90, "2F roof structural top: only the finished +13.90 is printed (upper bound: "
                                     "build-up >= 0); roof build-up / falls not printed", ["D-39_ROOF_DATUM"])
ROOF_2F_TANK = CL.Level.held(None, None, "2F roof at the water tank: B15 20x120 upstand or downstand not printed",
                             ["D-39_ROOF_DATUM", "D-44_B15_UPSTAND_DOWNSTAND"])
ANNEX_ROOF = CL.Level.held(None, 4.30, "annex roof structural top: only the finished +4.30 is printed (upper bound)",
                           ["Q-54B_ANNEX_ROOF_DATUM", "D-39_ROOF_DATUM"])
TWO_GROUND = CL.Level.held(0.25, 0.95, "column on the annex / main boundary: ground slabs +0.25 and +0.95 meet; the "
                                       "column / neck boundary is not printed", ["TWO_GROUND_SLAB_LEVELS"])
FORMATION = CL.Level.held(None, -1.50, "formation: at least 1.50 below the existing +-0.00 (ST p.9 note 1, owner Q-21 C); "
                                       "founding level not printed", ["FORMATION_NOT_PRINTED_Q21C"], kind=CL.LIMIT)
UNDERLAY = 0.17                     # 0.05 screed + 0.02 membrane + 0.10 blinding, ST p.13 (T-206 VERIFIED)
PIT_RAFT = CL.Level.held(None, None, "lift-pit raft top: pit depth 'as per lift manufacturer' (ST p.14)",
                         ["PIT_DEPTH_NOT_PRINTED_D43"])

ANNEX_ONLY = {"GFRS:34A", "GFRS:34D", "GFRS:350", "GFRS:353", "GFRS:356"}    # T-119 LEVEL_Q54B, annex roof beams only
ANNEX_DUAL = {"GFRS:35F", "GFRS:365"}     # T-119 LEVEL_Q54B on the CB5 line: main-roof B1 / B5 / CB5 and annex CB6
TANK = {"SFRS:40F", "SFRS:424"}           # T-119 UPSTAND_DOWNSTAND_D44
THROUGH = {"SFRS:778": ("BM-2F-011 B7 20x75", 0.75)}   # T-220: B7 billed through PC-2F, column stops at its soffit
DOUBLE_JOINTS_RELEASED = ["GFRS:347", "GFRS:34A", "GFRS:34D", "GFRS:350", "GFRS:356", "GFRS:359", "FFRS:667"]  # T-241
PLANTED_SECTION = {"FFRS:66A": CL.Section.of(0.20, 0.70, "AGREE", source="GFRS 544 'P.C 20x70', both outlines (T-220)"),
                   "FFRS:69D": CL.Section.of(0.20, 0.50, "AGREE", source="GFRS 548 'P.C 20x50', both outlines (T-220)"),
                   "SFRS:778": CL.Section.conflict(0.08, 0.10, "FFRS 77C 'P.C 20x50' vs drawn 0.20 x 0.40 (T-220)")}


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _section(row):
    # the governing area per metre of height (T-217 per_m_m3): a DRAFTING_NOTE takes the drawing's own printed section,
    # never the drawn slip; a CONFLICT keeps both candidates
    lo, hi = (float(x) for x in row["per_m_m3"].split(".."))
    cls = row["status"]
    if cls == "CONFLICT":
        return CL.Section.conflict(lo, hi, row["candidates"])
    return CL.Section(lo, hi, cls, row["candidates"])


def build():
    inp = json.loads((HERE / "ALSENAN_COLUMN_INPUT.json").read_text(encoding="utf-8"))
    sec = json.loads((RES / "agents_t217" / "ALSENAN_SECTION_INPUT.json").read_text(encoding="utf-8"))
    l217 = {(r["member"], r["storey"]): r for r in _rows(RES / "agents_t217" / "LEDGER_T217.csv")}
    l205 = {r["outline_handle"]: r for r in _rows(RES / "agents_t205" / "LEDGER_T205.csv")}
    t119 = {r["id"]: r for r in _rows(RES / "agents_t119" / "COLUMNS_TO_CONTROLLING_MEMBER.csv")}
    reg = {r["ITEM_ID"]: r for r in _rows(RES / "urban_engine_m4_correctness" / "st7757_route_g" / "PROVISIONAL_REGISTER.csv")
           if r["FAMILY"] == "COLUMNS" and r["UNIT"] == "m3"}
    inst = {i["fp_outline"]: i for i in sec["instances"]}
    turned = {m["own_outline"]["handle"] for m in sec["members_starting_on_a_slab"] if m["on_neck"]}
    bind = inp["t119_binding"]
    members, rows, reg_used = [], [], set()
    gf_zone = {}   # FP handle -> zone of the GF column on it
    for m in inp["members"]:
        key = f"{m['sheet']}:{m['handle']}"
        st = m["storey"]
        b = bind[key]
        o119 = t119[b["t119_id"]]
        if m["kind"] == "PLANTED":
            section, fp, mark, released = PLANTED_SECTION[key], None, o119["mark"], None
            kind = "PLANTED"
        else:
            fp = m["key"]
            r = l217[(fp, st)]
            section, mark, released = _section(r), r["mark"], r["released_line"] or None
            kind = "TURNED" if m["handle"] in turned else "COLUMN"
        top_owner, framing, base, top = "COLUMN", (), None, None
        if st == "GF":
            if key in ANNEX_ONLY:
                base, top, zone = ANNEX_GROUND, ANNEX_ROOF, "ANNEX"
            elif key in ANNEX_DUAL:
                base, top, zone = TWO_GROUND, GF_ROOF, "BOUNDARY"
            else:
                base, top, zone = GF_MAIN_TOP_OF_GROUND, GF_ROOF, "MAIN"
            gf_zone[fp] = zone
        elif st == "1F":
            base, top = GF_ROOF, F1_ROOF
        else:
            base = F1_ROOF
            top = ROOF_2F_TANK if key in TANK else ROOF_2F
            if key in THROUGH:
                beam, depth = THROUGH[key]
                top = top.minus(depth, f"soffit of {beam}")
                top_owner, framing = "BEAM_THROUGH", ((beam, "THROUGH"),)
        mem = CL.Member(id=key, storey=st, mark=mark, kind=kind, section=section, base=base, top=top,
                        top_owner=top_owner, framing=framing, handles=(key,) + ((f"FP:{fp}",) if fp else ()))
        s = CL.solid(mem)
        interval = {"GF": 4.50, "1F": 4.20, "2F": 4.20}[st]
        owner = {"t119_id": b["t119_id"], "column_lo": o119["col_m3_lo"], "column_hi": o119["col_m3_hi"],
                 "joint_lo": o119["joint_m3_lo"], "joint_hi": o119["joint_m3_hi"], "status": o119["status"],
                 "hold": o119["hold_cause"], "d_ctrl": o119["D_ctrl"], "t119_section": o119["section"]}
        rg = reg.get(released) if released else None
        if rg:
            reg_used.add(released)
        rows.append({"member": key, "storey": st, "mark": mark, "kind": kind, "fp_neck": fp or "",
                     "section_class": section.cls, "a_lo": section.a_lo, "a_hi": section.a_hi,
                     "base_lo": base.lo, "base_hi": base.hi, "top_lo": top.lo, "top_hi": top.hi,
                     "h_lo": s["h_lo"], "h_hi": s["h_hi"], "m3_lo": s["m3_lo"], "m3_hi": s["m3_hi"],
                     "status": s["status"], "causes": "|".join(s["causes"]), "top_owner": top_owner,
                     "route_g_line": released or "", "route_g_m3": float(rg["BASE"]) if rg else None,
                     "owner_t119": owner, "release": "NOT RELEASED"})
        members.append(mem)
    # route G lines on members no storey plan draws (T-217 SCHEDULE_TYPE_ONLY with a released line; T-220 NOT_DRAWN)
    for (fp, st), r in sorted(l217.items()):
        if r["existence"].startswith("SCHEDULE_TYPE_ONLY") and r["released_line"]:
            mem = CL.Member(id=f"NOT_DRAWN:{fp}:{st}", storey=st, mark=r["mark"], kind="COLUMN",
                            section=_section_from_reg(reg[r["released_line"]]), base=F1_ROOF, top=ROOF_2F,
                            existence="NOT_DRAWN", extra_causes=("D-65",))
            s = CL.solid(mem)
            reg_used.add(r["released_line"])
            rows.append({"member": mem.id, "storey": st, "mark": r["mark"], "kind": "COLUMN", "fp_neck": fp,
                         "section_class": "", "a_lo": None, "a_hi": None, "base_lo": None, "base_hi": None,
                         "top_lo": None, "top_hi": None, "h_lo": None, "h_hi": None, "m3_lo": None, "m3_hi": None,
                         "status": s["status"], "causes": "|".join(s["causes"]), "top_owner": "",
                         "route_g_line": r["released_line"], "route_g_m3": float(reg[r["released_line"]]["BASE"]),
                         "owner_t119": {}, "release": "NOT RELEASED"})
    # necks
    stack = []
    for fp, n in sorted(l205.items()):
        r = l217[(fp, "FOUNDATION")]
        section = _section(r)
        zone = gf_zone.get(fp)
        if zone is None:      # CN neck-only (no column above)
            z = inp["neck_only_zone"][fp]["zone"]
            zone = z if z != "NOT_ESTABLISHED" else "BOUNDARY"
        top = {"MAIN": GF_MAIN_TOP_OF_GROUND, "ANNEX": ANNEX_GROUND, "BOUNDARY": TWO_GROUND}[zone]
        causes = []
        if n["footing"] == "FF":
            base = PIT_RAFT
        elif n["footing"] == "F10|F":
            # one outline 1B1B, tags F10 + F (Q-31 C): C10 sits in the F10 part (H 0.50 on both readings); the corner
            # C sits in the F part: 0.30 (rows separately) or 0.50 (one outline at the deepest tagged depth)
            h_lo, h_hi = (0.50, 0.50) if n["type"] == "C10" else (0.30, 0.50)
            base = CL.neck_base(FORMATION, UNDERLAY, h_lo, h_hi, "footing 1B1B F10 + F, Q-31 C")
            causes.append("FOOTING_IDENTITY_Q31C")
        else:
            h = float(n["footing_H_m"])
            base = CL.neck_base(FORMATION, UNDERLAY, h, h, f"footing {n['footing']} H {h:g} (schedule FT / FTB)")
        mem = CL.Member(id=f"FP:{fp}", storey="FOUNDATION", mark=n["type"], kind="NECK", section=section, base=base,
                        top=top, extra_causes=tuple(causes))
        s = CL.solid(mem)
        rg_id = r["released_line"] or None
        rg = reg.get(rg_id) if rg_id else None
        if rg:
            reg_used.add(rg_id)
        rows.append({"member": mem.id, "storey": "FOUNDATION", "mark": n["type"], "kind": "NECK", "fp_neck": fp,
                     "section_class": section.cls, "a_lo": section.a_lo, "a_hi": section.a_hi,
                     "base_lo": base.lo, "base_hi": base.hi, "top_lo": top.lo, "top_hi": top.hi,
                     "h_lo": s["h_lo"], "h_hi": s["h_hi"], "m3_lo": s["m3_lo"], "m3_hi": s["m3_hi"],
                     "status": s["status"], "causes": "|".join(s["causes"]), "top_owner": "COLUMN",
                     "route_g_line": rg_id or "", "route_g_m3": float(rg["BASE"]) if rg else None,
                     "owner_t119": {}, "release": "NOT RELEASED"})
        members.append(mem)
        # stack: the GF column on this neck starts at the neck top
        for c in members:
            if c.storey == "GF" and f"FP:{fp}" in c.handles:
                stack.append((fp, mem, c))
    unused = sorted(set(reg) - reg_used)
    return rows, members, stack, unused, inp, sec


def _section_from_reg(r):
    w, d = json.loads(r["DIMENSIONS"])["section_m"]
    return CL.Section.of(w, d, "AGREE", source="route G schedule band (the member is not drawn: no section is measured)")


def freelancer():
    d = json.loads((ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    sheet = "الحوائط + الأعمدة"
    out = defaultdict(list)
    blocks = {"FOUNDATION": range(16, 29), "GF": range(36, 48), "1F": range(52, 62), "2F": range(66, 72)}
    totals = {}
    for r in d["rows"]:
        if r["sheet"] != sheet:
            continue
        c = r["cells"]
        n = r["row"]
        for st, rng in blocks.items():
            if n in rng:
                mark = c[f"A{n}"]["v"].strip()
                out[st].append({"row": n, "mark": mark, "b": c[f"B{n}"]["v"], "l": c[f"C{n}"]["v"], "h": c[f"D{n}"]["v"],
                                "n": c[f"F{n}"]["v"], "m3": round(c[f"I{n}"]["v"], 6)})
        if n == 11:
            totals["lift_walls"] = {"row": 11, "l": c["B11"]["v"], "b": c["C11"]["v"], "h": c["D11"]["v"],
                                    "m3": round(c["I11"]["v"], 6)}
        if n in (29, 48, 62, 72):
            totals[{29: "FOUNDATION", 48: "GF", 62: "1F", 72: "2F"}[n]] = round(c[f"I{n}"]["v"], 6)
        if n == 74:
            totals["line"] = round(c["B74"]["v"], 6)
    return out, totals


FL_MARK = {"PC1": "P.C 20x50", "PC2": "P.C 20x70", "PC": "P.C 20x50"}


def by_mark(rows, fl):
    """storey x mark: drawing members (closable / conflict / held) vs his rows; scope, count, section, height named."""
    out = []
    keys = set()
    for r in rows:
        if r["status"] != "UNKNOWN":
            keys.add((r["storey"], r["mark"]))
    for st, lst in fl.items():
        for f in lst:
            keys.add((st, FL_MARK.get(f["mark"], f["mark"])))
    order = {"FOUNDATION": 0, "GF": 1, "1F": 2, "2F": 3}
    for st, mark in sorted(keys, key=lambda k: (order[k[0]], k[1])):
        mine = [r for r in rows if r["storey"] == st and r["mark"] == mark and r["status"] != "UNKNOWN"]
        his = [f for f in fl.get(st, []) if FL_MARK.get(f["mark"], f["mark"]) == mark]
        hn = sum(f["n"] for f in his)
        hm = round(sum(f["m3"] for f in his), 6)
        dc = [r for r in mine if r["status"] == "DRAWING-CONFIRMED"]
        cf = [r for r in mine if r["status"] == "CONFLICT"]
        hd = [r for r in mine if r["status"] == "HELD"]
        out.append({"storey": st, "mark": mark, "drawn_n": len(mine), "his_n": hn,
                    "his_section": "; ".join(f"{f['b']}x{f['l']}" for f in his), "his_h": "; ".join(str(f["h"]) for f in his),
                    "his_m3": hm,
                    "dc_n": len(dc), "dc_m3": round(sum(r["m3_lo"] for r in dc), 6),
                    "conflict_n": len(cf), "conflict_m3": f"{sum(r['m3_lo'] for r in cf):.4f}..{sum(r['m3_hi'] for r in cf):.4f}" if cf else "",
                    "held_n": len(hd),
                    "held_bound": _held_bound(hd),
                    "count_diff": len(mine) - hn,
                    "his_rows": ",".join(str(f["row"]) for f in his)})
    return out


def reconcile_storey(rows, fl, st):
    """freelancer -> count -> section -> height basis -> drawing, per storey, both ends; open ends stay open."""
    his = fl.get(st, [])
    mine = [r for r in rows if r["storey"] == st and r["status"] != "UNKNOWN"]
    unit = {}
    for f in his:
        unit[FL_MARK.get(f["mark"], f["mark"])] = (f["b"] * f["l"], f["h"])
    h_his_storey = his[0]["h"]
    count = sec_lo = sec_hi = 0.0
    hgt_lo, hgt_hi = 0.0, 0.0
    by = defaultdict(list)
    for r in mine:
        by[r["mark"]].append(r)
    marks = set(by) | set(unit)
    for mk in sorted(marks):
        a_his, h_his = unit.get(mk, (None, h_his_storey))
        n_his = sum(f["n"] for f in his if FL_MARK.get(f["mark"], f["mark"]) == mk)
        mem = by.get(mk, [])
        if a_his is None:          # a mark he has no row for: count step at the drawing's low section, his height
            a_his = min(r["a_lo"] for r in mem)
        count += (len(mem) - n_his) * a_his * h_his
        for r in mem:
            sec_lo += (r["a_lo"] - a_his) * h_his
            sec_hi += (r["a_hi"] - a_his) * h_his
            hgt_lo = None if hgt_lo is None or r["h_lo"] is None else hgt_lo + r["a_lo"] * (r["h_lo"] - h_his)
            hgt_hi = None if hgt_hi is None or r["h_hi"] is None else hgt_hi + r["a_hi"] * (r["h_hi"] - h_his)
    his_m3 = round(sum(f["m3"] for f in his), 6)
    lo = [r["m3_lo"] for r in mine]
    hi = [r["m3_hi"] for r in mine]
    d_lo = None if any(v is None for v in lo) else round(sum(lo), 6)
    d_hi = None if any(v is None for v in hi) else round(sum(hi), 6)
    rnd = lambda v: None if v is None else round(v, 6)
    out = {"freelancer": his_m3, "count": rnd(count), "section": [rnd(sec_lo), rnd(sec_hi)],
           "height_basis": [rnd(hgt_lo), rnd(hgt_hi)], "drawing": [d_lo, d_hi]}
    for end, (sc, hg, dv) in {"lo": (sec_lo, hgt_lo, d_lo), "hi": (sec_hi, hgt_hi, d_hi)}.items():
        out[f"residual_{end}"] = None if hg is None or dv is None else round(dv - (his_m3 + count + sc + hg), 6)
    return out


def _held_bound(hd):
    if not hd:
        return ""
    lo = [r["m3_lo"] for r in hd]
    hi = [r["m3_hi"] for r in hd]
    slo = "?" if any(v is None for v in lo) else f"{sum(lo):.4f}"
    shi = "open" if any(v is None for v in hi) else f"{sum(hi):.4f}"
    return f">= {slo} .. <= {shi}"


def slab_sheet_partition():
    """Each column footprint against the T-241 partition of the three roof-slab sheets (committed values-only input,
    re-derived from the Drive DXF by T-241, merged f0250164): area of the footprint inside SLAB-class faces (a slab
    panel carrying a column = DOUBLE), inside beam bands (billed by a beam band too), and the part of the outline no
    face of the partition covers (outline at a slab edge / under a turned outline: no quantity, named)."""
    d = json.loads((RES / "agents_t241" / "ALSENAN_PARTITION_INPUT.json").read_text(encoding="utf-8"))
    sheet = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
    cols = {(c["storey"], c["h"]): c for c in d["columns"] if c["hatch"] == "SOLID"}
    cov, slab, band = defaultdict(float), defaultdict(float), defaultdict(float)
    for f in d["faces"]:
        bs = sum(b[1] for b in f["bands"])
        for h, hat, a in f["columns"]:
            k = (f["storey"], h)
            cov[k] += a
            if f["cls"] == "SLAB":
                slab[k] += a
            if bs > 1e-3:
                band[k] += min(a, bs)
    out = {"solid_outlines": len(cols), "slab_overlap": {}, "band_overlap": {}, "uncovered": {},
           "note": "band_overlap = face-level estimate (min of the face's column and band shares): it identifies the "
                   "outlines a band crosses; the joint m2 are T-241's polygon values (GF 0.4401, 1F 0.0090, 2F 0.0799)"}
    for k, c in sorted(cols.items()):
        key = f"{sheet[k[0]]}:{k[1]}"
        if slab[k] > 1e-3:
            out["slab_overlap"][key] = round(slab[k], 4)
        if band[k] > 1e-3:
            out["band_overlap"][key] = round(band[k], 4)
        if c["area_m2"] - cov[k] > 2e-3:
            out["uncovered"][key] = round(c["area_m2"] - cov[k], 4)
    return out


def summarise(rows, stack, unused, inp, fl, ft):  # noqa: C901
    def comp(sel):
        return CL.components([r for r in rows if sel(r)])
    cols = lambda r: r["storey"] != "FOUNDATION"
    st_comp = {st: comp(lambda r, st=st: r["storey"] == st) for st in ("GF", "1F", "2F", "FOUNDATION")}
    reg_by = defaultdict(float)
    for r in rows:
        if r["route_g_m3"] is not None:
            reg_by[r["storey"]] += r["route_g_m3"]
    # closable component (DRAWING-CONFIRMED) vs route G on the same members, named per member
    same = [(r["member"], r["m3_lo"], r["route_g_m3"]) for r in rows if r["status"] == "DRAWING-CONFIRMED" and cols(r)]
    dc_vs_reg = {"members": len(same), "drawing": round(sum(a for _, a, _ in same), 6),
                 "route_g_on_them": round(sum(b for _, _, b in same if b is not None), 6),
                 "no_route_g_line": [m for m, _, b in same if b is None],
                 "differ": [(m, a, b) for m, a, b in same if b is not None and abs(a - b) > 1e-6]}
    joints = {k: next((r["status"] for r in rows if r["member"] == k), None) for k in DOUBLE_JOINTS_RELEASED}
    s = {"schema": "T248_COLUMN_LINE_V1", "method": CL.METHOD, "rule": CL.RULE,
         "convention": "C1 (T-234 / T-241): slab panels stop at column faces, beams billed to the column face (NET); "
                       "the column owns its footprint from its base datum to the slab top; a beam billed THROUGH owns "
                       "its piece (PC-2F under B7)",
         "inventory": {"columns": sum(1 for r in rows if cols(r) and r["status"] != "UNKNOWN"),
                       "by_storey": {st: sum(1 for r in rows if r["storey"] == st and r["status"] != "UNKNOWN")
                                     for st in ("GF", "1F", "2F")},
                       "necks": sum(1 for r in rows if r["storey"] == "FOUNDATION"),
                       "not_drawn_route_g_lines": [r["member"] for r in rows if r["status"] == "UNKNOWN"],
                       "t217_reproduced_from_drive": inp["t217_inventory_reproduced"]},
         "components_by_storey": st_comp,
         "columns_all_storeys": comp(cols),
         "necks": st_comp["FOUNDATION"],
         "route_g_register_m3": {k: round(v, 6) for k, v in reg_by.items()},
         "route_g_unbound_lines": unused,
         "closable_vs_route_g": dc_vs_reg,
         "stack_check_neck_to_gf_column": CL.stack_check(stack),
         "ownership_check": CL.ownership({r["member"]: r["top_owner"] for r in rows if cols(r) and r["status"] != "UNKNOWN"},
                                         True, {k: [(v[0], "THROUGH")] for k, v in THROUGH.items()}),
         "released_double_joints_now_column_owned": joints,
         "slab_sheet_partition": slab_sheet_partition(),
         "footing_identity_1B1B": inp["footing_identity"],
         "freelancer": ft,
         "reconcile_freelancer": {st: reconcile_storey(rows, fl, st) for st in ("FOUNDATION", "GF", "1F", "2F")}}
    return s


def write(rows, bym, summ):
    cols = ["member", "storey", "mark", "kind", "fp_neck", "section_class", "a_lo", "a_hi", "base_lo", "base_hi",
            "top_lo", "top_hi", "h_lo", "h_hi", "m3_lo", "m3_hi", "status", "causes", "top_owner", "route_g_line",
            "route_g_m3", "owner_t119_id", "owner_column_m3", "owner_joint_m3", "owner_status", "release"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        o = r["owner_t119"]
        rr = {k: r.get(k) for k in cols if k in r}
        rr.update({"owner_t119_id": o.get("t119_id", ""),
                   "owner_column_m3": f"{o['column_lo']}..{o['column_hi']}" if o else "",
                   "owner_joint_m3": f"{o['joint_lo']}..{o['joint_hi']}" if o else "",
                   "owner_status": (o.get("status", "") + (":" + o["hold"] if o.get("hold") else "")) if o else ""})
        w.writerow({k: ("" if v is None else v) for k, v in rr.items()})
    (HERE / "LEDGER_T248.csv").write_text(buf.getvalue(), encoding="utf-8")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(bym[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(bym)
    (HERE / "BY_MARK_T248.csv").write_text(buf.getvalue(), encoding="utf-8")
    (HERE / "summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main():
    rows, members, stack, unused, inp, sec = build()
    fl, ft = freelancer()
    bym = by_mark(rows, fl)
    summ = summarise(rows, stack, unused, inp, fl, ft)
    if "--write" in sys.argv:
        write(rows, bym, summ)
    print(json.dumps({k: summ[k] for k in ("inventory", "components_by_storey", "route_g_register_m3",
                                           "route_g_unbound_lines", "stack_check_neck_to_gf_column", "ownership_check")},
                     indent=0, ensure_ascii=False))
    return rows, bym, summ


if __name__ == "__main__":
    main()
