"""T-225 blockwork resolution 1/4: sources, three-way reconciliation, wall register v1, before-coverage.

Read-only over merged ledgers (no quantity changes):
  research/agents_t108/T108_BY_WALL.csv, T108_V2_RUN_LENGTHS.csv  MASONRY_AREA_V1 r2 (T-108 r2, MERGED 01eeafd0)
  research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv                 members above, type source, annex reason (T-143)
  research/agents_t175/T175_OPENING_HOSTS.csv                     opening -> host wall, height status (T-175)
  research/agents_t176/BLOCK_PROCUREMENT_BY_WALL.csv              product, installed units (T-176, MERGED 41847bff)
  research/agents_t215/T215_ROW_EFFECT.csv                        closed ends (T-215, MERGED 8a9b4b48; NOT applied)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json             the freelancer workbook rows (hash = Drive file)
  research/agents_t225/V29_RUN_A_MASONRY_LINES.csv                older automated run A (extract_v29.py)

Usage: python3 -I build_t225.py          (writes the files next to this script)
       python3 -I build_t225.py --check  (exit 1 if any committed output differs)
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import register_v1 as RV  # noqa: E402

f = RV.f
R3 = lambda v: f"{v:.3f}"
DRIVE = "Drive 'Alsenan chalet project'"
ARCH = f"{DRIVE} / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55)"
ST = f"{DRIVE} / ST7757 dxf.dxf (sha 9f9d1179)"
FL_TITLE = f"{DRIVE} / المبانى.xlsx (freelancer blockwork workbook, sha 873308bb), sheet الكميات"


def rd(rel):
    return list(csv.DictReader((ROOT / rel).open(encoding="utf-8")))


# ------------------------------------------------------------------------------------------------ inputs
def inputs():
    t108 = rd("research/agents_t108/T108_BY_WALL.csv")
    t143 = {r["row_id"]: r for r in rd("research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv")}
    hosts = rd("research/agents_t175/T175_OPENING_HOSTS.csv")
    t176 = defaultdict(list)
    for r in rd("research/agents_t176/BLOCK_PROCUREMENT_BY_WALL.csv"):
        t176[r["row_id"]].append(r)
    t215 = {r["row_id"]: r for r in rd("research/agents_t215/T215_ROW_EFFECT.csv")}
    v2 = rd("research/agents_t108/T108_V2_RUN_LENGTHS.csv")
    v29 = rd("research/agents_t225/V29_RUN_A_MASONRY_LINES.csv")
    v29b = rd("research/agents_t225/V29_RUN_A_WALL_BANDS.csv")
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    return t108, t143, hosts, t176, t215, v2, v29, v29b, raw


# ------------------------------------------------------------------------------------------------ freelancer
# section / floor / scope by row range of sheet الكميات (headers A11, A60, A98, A130-A174, B200-A212 of the sheet)
FL_BLOCKS = [
    ("EXTERNAL", "GF", "WALL_RUN", 14, 36), ("EXTERNAL", "GF", "DEDUCTION", 41, 51),
    ("EXTERNAL", "1F", "WALL_RUN", 63, 77), ("EXTERNAL", "1F", "PROJECTION (no wall run)", 78, 78),
    ("EXTERNAL", "1F", "DEDUCTION", 84, 90),
    ("EXTERNAL", "2F", "WALL_RUN", 101, 107), ("EXTERNAL", "2F", "DEDUCTION", 111, 115),
    ("INTERNAL 0.15", "GF", "WALL_RUN", 133, 149), ("INTERNAL 0.15", "GF", "FENCE (not a building wall)", 150, 150),
    ("INTERNAL 0.15", "1F", "WALL_RUN", 154, 170), ("INTERNAL 0.15", "1F", "PARAPET (ground-roof)", 172, 172),
    ("INTERNAL 0.15", "2F", "WALL_RUN", 176, 176), ("INTERNAL 0.15", "2F", "PARAPET (first-roof)", 177, 177),
    ("INTERNAL 0.15", "2F", "PARAPET (top roof)", 178, 178),
    ("INTERNAL 0.15", "GF", "DEDUCTION", 185, 186), ("INTERNAL 0.15", "1F", "DEDUCTION", 188, 189),
    ("INTERNAL 0.15", "2F", "DEDUCTION", 191, 192),
    ("INTERNAL 0.20", "GF", "WALL_RUN", 203, 206), ("INTERNAL 0.20", "1F", "WALL_RUN", 208, 211),
    ("INTERNAL 0.20", "2F", "WALL_RUN", 213, 216), ("INTERNAL 0.20", "ALL (not split by floor)", "DEDUCTION", 222, 223),
]
FL_TOTALS = [("H37", "GF external gross"), ("H52", "GF external deductions"), ("H54", "GF external net"),
             ("H80", "1F external gross incl. projections row 78"), ("H91", "1F external deductions"),
             ("H93", "1F external net"), ("H108", "2F external gross"), ("H116", "2F external deductions"),
             ("H118", "2F external net"), ("H121", "external net, all floors"),
             ("H180", "15 cm gross incl. fence row 150 and parapet rows 172 / 177 / 178"),
             ("H194", "15 cm deductions"), ("H196", "15 cm net"), ("H218", "20 cm gross"), ("H225", "20 cm deductions"),
             ("H227", "20 cm net")]


def freelancer_rows(raw):
    rows = {x["row"]: x["cells"] for x in raw["rows"] if x["file"] == "BLK" and x["sheet"] == "الكميات"}
    out = []
    for sec, fl, scope, a, b in FL_BLOCKS:
        for n in range(a, b + 1):
            c = rows.get(n)
            if not c or f"H{n}" not in c:
                continue
            cnt, L, h, H = (f(c.get(f"{k}{n}", {}).get("v")) for k in "BCDH")
            fx = c[f"H{n}"].get("f") or ""
            std = fx == f"=D{n}*C{n}*B{n}"
            note = "" if std else f"formula {fx} (reads another row's height; {'same value, no effect' if abs(cnt * L * h - H) < 1e-9 else 'VALUE DIFFERS'})"
            out.append({"cell_ref": f"B{n}:C{n}:D{n}:H{n}", "row": n, "section": sec, "floor": fl, "scope": scope,
                        "count": cnt, "length_m": L, "height_m": h, "area_m2": H, "length_x_count_m": cnt * L,
                        "note": note})
    tot = []
    for ref, what in FL_TOTALS:
        n = int(ref[1:])
        c = rows[n][ref]
        tot.append({"cell_ref": ref, "what": what, "value_m2": c["v"], "formula": c.get("f") or ""})
    return out, tot


def fl_sum(rows, sec, fl, scope, k):
    return sum(r[k] for r in rows if r["section"] == sec and r["floor"] == fl and r["scope"] == scope)


# ------------------------------------------------------------------------------------------------ register
def members(t143row):
    """Condensed member-above pieces of a T-143 row: 'mark id (depth / status): length m -> h'."""
    s = t143row.get("members_above", "") if t143row else ""
    out, pos = [], 0
    for m in re.finditer(r": ([\d.]+) m -> h ([\d.]+|HELD)( \(candidate [^)]*\))?", s):
        seg = s[pos:m.start()].lstrip("; ")
        pos = m.end()
        tok = seg.split()
        name = " ".join(tok[:2]) if tok else "?"
        d = re.search(r"\bh ([\d.]+) \[(\w+)\]|\bt ([\d.]+) \(|\[(HELD|CONFLICT)\]", seg)
        dep = ""
        if d:
            dep = f" (h {d.group(1)} {d.group(2)})" if d.group(1) else f" (slab t {d.group(3)})" if d.group(3) else f" ({d.group(4)})"
        if "no beam or slab underside" in seg:
            dep = " (nothing drawn to stop at)"
        out.append(f"{name}{dep}: {m.group(1)} m -> h {m.group(2)}{m.group(3) or ''}")
    rest = s[pos:].lstrip("; ")
    if rest:
        out.append(f"{' '.join(rest.split()[:2])} (no height: {rest.split(':')[-1].strip()})")
    return "; ".join(out) if out else "none recorded"


def register(t108, t143, hosts, t176, t215):
    by_host = defaultdict(list)
    for h in hosts:
        if h["HOST_ROW"]:
            by_host[h["HOST_ROW"]].append(h)
    hmap = {h["ID"]: h for h in hosts}
    reg = []
    for r in t108:
        rid = r["row_id"]
        parts = [p.strip() for p in rid.split("+")]
        tr = [t143.get(p) for p in parts]
        t143_reason = " ".join((x or {}).get("reason", "") for x in tr)
        ops = [h["ID"] for p in parts for h in by_host.get(p, []) if h["IN_GROSS"] == "YES"]
        held_ops = [o for o in r["held_openings"].split(";") if o]
        for o in held_ops:
            if o not in ops:
                ops.append(o)
        held = r["gross_status"] == "HELD" or r["net_status"] == "HELD"
        if held:
            cname, missing, pkg = RV.cause(r["hold_reason"], t143_reason)
            all_causes = [n for n, test, _, _ in RV.CAUSES if test(r["hold_reason"], t143_reason)]
            hop = "; ".join(f"{o} {hmap[o]['WIDTH_M']} m wide, height {hmap[o]['HEIGHT_STATUS_T150']}"
                            for o in held_ops if o in hmap)
            unresolved = f"{cname}: {missing}" + (f" [{'; '.join(all_causes[1:])} also]" if len(all_causes) > 1 else "") \
                + (f"; held openings: {hop}" if hop else "") + (f"; engine: {r['hold_reason']}" if r["hold_reason"] else "")
            if r["gross_status"] == "HELD":
                smallest = (f"gross {r['gross_m2'] or '0.000'} m2 on the established pieces (figure carried, not a "
                            f"quantity) + held length {r['held_length_m']} m; net not formed")
            else:
                smallest = (f"net only (gross {r['gross_m2']} m2 SOURCE-SUPPORTED): held openings' area"
                            + (f", net bounds {r['net_bounds_m2']} m2" if r["net_bounds_m2"] else ""))
        else:
            cname, pkg, smallest = "", "", ""
            unresolved = ("pending the Checker's independent re-measure of length, height and deductions"
                          + ("; door height 2.20 m by owner fallback Q-55 C (no door height printed)"
                             if r["net_status"] == "ASSUMED — OWNER-APPROVED" else ""))
        pc = t176.get(rid, [])
        e215 = t215.get(rid)
        L, hl = f(r["physical_length_m"]), f(r["held_length_m"])
        calc = (f"({R3(L)} - held {R3(hl)}) m x h_w {r['height_weighted_m'] or 'HELD'} m = gross "
                f"{r['gross_m2'] or 'HELD'} m2; - deductions {r['deducted_m2']} m2 = net {r['net_m2'] or 'HELD'} m2"
                + (f"; m3 = net x {r['t_m']} = {r['net_m3']}" if r["net_m3"] else ""))
        ev = (f"length: {ARCH} V2 run {r['v2_runs'] or 'none (hand census T-143, capped HELD)'} "
              f"({r['length_source']}); member above / height: {ST} roof-slab plan, {members(tr[0]) if tr[0] else ''}"
              f"{' | ' + members(tr[1]) if len(tr) > 1 and tr[1] else ''}; storey heights GF 4.50 / 1F 4.20 / 2F 4.20 "
              f"(p7757_arch_sheet10.pdf section, T-112); openings: {', '.join(ops) or 'none'} (T-175 hosts, T-150 / "
              f"T-198 census); type: {(tr[0] or {}).get('type_source', '')}")
        reg.append({
            "wall_id": rid, "floor": r["floor"], "group": r["group"], "block_type": r["block_type"],
            "type_class": RV.status_class(r["type_status"]), "t_m": r["t_m"],
            "length_m": r["physical_length_m"], "held_length_m": r["held_length_m"],
            "length_class": "HELD" if r["length_source"] == "HAND" else (
                "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK" if hl < L or L == 0 else "HELD"),
            "height_weighted_m": r["height_weighted_m"],
            "gross_m2": r["gross_m2"], "gross_class": RV.status_class(r["gross_status"]),
            "deductions_m2": r["deducted_m2"], "openings_in_run": ";".join(ops), "held_openings": r["held_openings"],
            "net_m2": r["net_m2"], "net_class": RV.status_class(r["net_status"]), "net_bounds_m2": r["net_bounds_m2"],
            "net_m3": r["net_m3"],
            "owner_status_class": RV.status_class(r["net_status"]),
            "held_cause_class": cname, "next_package": pkg, "smallest_held_quantity": smallest,
            "unresolved_reason": unresolved, "evidence": ev, "calculation": calc,
            "d12_flag (m3 only)": (pc[0]["d12_flag"] if pc else ""),
            "t176_products": "; ".join(f"{p['product']} {p['installed_units'] or 'HELD'} pcs ({p['installed_status']})"
                                      for p in pc),
            "t215_closed_length_m (merged, not applied in v1)": e215["closed_length_m"] if e215 else "",
            "t215_d_gross_m2 (not applied)": (f"{e215['d_gross_m2_min']} .. {e215['d_gross_m2_max']}" if e215 else ""),
            "source_ledgers": "T-108 r2 (MASONRY_AREA_V1 r2) + T-143 + T-175 + T-176 + T-215",
            "verified_by_checker": "no",
        })
    return reg


# ------------------------------------------------------------------------------------------------ tables
TYPES = ("BLACK", "WHITE", "-")


def coverage(t108, reg):
    regd = {x["wall_id"]: x for x in reg}
    keys = sorted({(r["floor"], r["t_m"], r["block_type"]) for r in t108}, key=lambda k: ("GF1F2F".index(k[0]), k[1], k[2]))
    out = []
    for k in [("ALL", "0.1", "ANY")] + keys:
        rs = [r for r in t108 if (r["floor"], r["t_m"], r["block_type"]) == k]
        held = [r for r in rs if r["net_status"] == "HELD"]
        causes = defaultdict(list)
        for r in held:
            causes[regd[r["row_id"]]["held_cause_class"]].append(r["row_id"])
        g = lambda s: sum(f(r["gross_m2"]) for r in rs if r["gross_status"] == s)
        n = lambda s: sum(f(r["net_m2"]) for r in rs if r["net_status"] == s)
        out.append({
            "floor": k[0], "t_m": k[1], "block_type": k[2], "walls": len(rs),
            "length_established_m": R3(sum(f(r["physical_length_m"]) - f(r["held_length_m"]) for r in rs)),
            "length_held_m": R3(sum(f(r["held_length_m"]) for r in rs)),
            "gross_source_supported_m2": R3(g("DRAWING-CONFIRMED")), "gross_held_figure_m2 (not a quantity)": R3(g("HELD")),
            "net_VERIFIED_m2": R3(n("VERIFIED")), "net_source_supported_m2": R3(n("DRAWING-CONFIRMED")),
            "net_project_specific_m2": R3(n("ASSUMED — OWNER-APPROVED")),
            "walls_net_held": len(held),
            "deductions_on_net_held_walls_m2 (held scope)": R3(sum(f(r["deducted_m2"]) for r in held)),
            "held_causes": "; ".join(f"{c}: {', '.join(v)}" for c, v in sorted(causes.items())),
            "note": ("no 100 mm wall in the census, the freelancer sheet or the released run: 0 walls (a count, not a "
                     "held quantity)" if k[0] == "ALL" else ""),
        })
    return out


def three_way_section(t108, fr):
    """Floor x freelancer section; the freelancer's external walls carry no printed thickness, so the engine side is
    its EXTERNAL group (all thicknesses); the released V2.9 run has no external / internal split."""
    out = []
    for fl in ("GF", "1F", "2F"):
        for sec in ("EXTERNAL", "INTERNAL 0.15", "INTERNAL 0.20"):
            if sec == "EXTERNAL":
                rs = [r for r in t108 if r["floor"] == fl and r["group"] == "EXTERNAL"]
            else:
                rs = [r for r in t108 if r["floor"] == fl and r["group"] == "INTERNAL" and f(r["t_m"]) == float(sec.split()[1])]
            hl = sum(f(r["held_length_m"]) for r in rs)
            heldnet = sum(1 for r in rs if r["net_status"] == "HELD")
            gL = fl_sum(fr, sec, fl, "WALL_RUN", "length_x_count_m")
            gA = fl_sum(fr, sec, fl, "WALL_RUN", "area_m2")
            dA = fl_sum(fr, sec, fl, "DEDUCTION", "area_m2") if sec != "INTERNAL 0.20" else None
            eL = sum(f(r["physical_length_m"]) for r in rs)
            eG = sum(f(r["gross_m2"]) for r in rs)
            eN = sum(f(r["net_m2"]) for r in rs if r["net_status"] in RV.ESTABLISHED)
            other = [(r["scope"], r["area_m2"]) for r in fr if r["section"] == sec and r["floor"] == fl
                     and r["scope"] not in ("WALL_RUN", "DEDUCTION")]
            types = sorted({r["block_type"] for r in rs})
            tset = sorted({r["t_m"] for r in rs})
            reasons = []
            if hl > 0:
                reasons.append(f"engine held length {hl:.3f} m (missing, not 0)")
            if heldnet:
                reasons.append(f"{heldnet} engine walls with net HELD")
            if dA is None:
                reasons.append("freelancer 20 cm deductions not split by floor (rows 222-223)")
            reasons.append("freelancer: one height per floor and zone (D column), engine: Q-60 A height under the "
                           "member above (RULE_DIFFERENCE on height basis, T-143)")
            like = "length only" if hl == 0 else "NO"
            out.append({
                "floor": fl, "freelancer_section": sec, "engine_scope": (f"group EXTERNAL, t {'/'.join(tset)}"
                                                                         if sec == "EXTERNAL" else f"group INTERNAL, t {'/'.join(tset)}"),
                "engine_types": "/".join(types), "freelancer_rows": "; ".join(
                    f"{a}-{b}" for s_, fl_, sc, a, b in FL_BLOCKS if s_ == sec and fl_ == fl and sc == "WALL_RUN"),
                "freelancer_length_m (sum B x C)": R3(gL), "engine_length_m (physical, incl. held)": R3(eL),
                "d_length_m": R3(eL - gL), "engine_held_length_m": R3(hl),
                "freelancer_gross_m2": R3(gA), "engine_gross_known_m2": R3(eG), "d_gross_m2": R3(eG - gA),
                "freelancer_deductions_m2": "not split" if dA is None else R3(dA),
                "freelancer_net_m2": "not split" if dA is None else R3(gA - dA),
                "engine_net_established_m2": R3(eN), "engine_walls_net_held": heldnet,
                "released_v29_run_A": "NOT COMPARABLE: the run gives ARCH.WALL_RUN lm by thickness only (no external / "
                                      "internal split); m2 BLOCKED_RFI (see the thickness table)",
                "freelancer_other_scope_in_section": "; ".join(f"{s} {a:.3f} m2" for s, a in other),
                "like_for_like": like, "scope_difference": "; ".join(reasons),
            })
    return out


def three_way_thickness(t108, v2, v29):
    v29r = {(l["floor"], float(l["physical_element"].split("=")[1])): l for l in v29 if l["item_code"] == "ARCH.WALL_RUN"}
    v29m2 = {(l["floor"], float(l["physical_element"].split("=")[1])): l for l in v29 if l["item_code"] == "MAS.BLOCK"}
    out = []
    keys = sorted({(r["floor"], f(r["t_m"])) for r in t108} | set(v29r), key=lambda k: ("GF1F2F".index(k[0]), k[1]))
    for fl, t in [("ALL", 0.10)] + keys:
        rs = [r for r in t108 if r["floor"] == fl and f(r["t_m"]) == t]
        vr = [x for x in v2 if x["floor"] == fl and f(x["t_m"]) == t]
        arch = sum(f(x["arch_run_m"]) for x in vr)
        glz = sum(f(x["glazed_line_m"]) for x in vr)
        L = sum(f(r["physical_length_m"]) for r in rs)
        hand_only = sum(f(r["physical_length_m"]) for r in rs if r["length_source"] == "HAND")
        a = v29r.get((fl, t))
        m = v29m2.get((fl, t))
        by_type = {ty: [r for r in rs if r["block_type"] == ty] for ty in TYPES}
        row = {
            "floor": fl, "t_m": f"{t:.2f}",
            "v29_line_ids": "; ".join(x["line_id"] for x in (a, m) if x) or "none",
            "v29_wall_run_gross_lm (band run)": a["gross"] if a else "none",
            "v29_wall_run_released_lm (both faces drawn)": a["measured_net"] if a else "none",
            "v29_block_m2": (f"{m['evidence_state']} ({m['rfi_head']}), no quantity" if m else "none"),
            "engine_v2_arch_run_m": R3(arch), "engine_glazed_lines_out_m": R3(glz),
            "engine_physical_length_m": R3(L), "engine_hand_only_length_m": R3(hand_only),
            "d_engine_physical_vs_v29_released_lm": R3(L - f(a["measured_net"])) if a else "",
            "d_engine_v2_arch_vs_v29_gross_lm": R3(arch + hand_only - f(a["gross"])) if a else "",
        }
        for ty in TYPES:
            q = by_type[ty]
            row[f"engine_{ty}_walls"] = len(q)
            row[f"engine_{ty}_gross_known_m2"] = R3(sum(f(r["gross_m2"]) for r in q))
            row[f"engine_{ty}_net_established_m2"] = R3(sum(f(r["net_m2"]) for r in q if r["net_status"] in RV.ESTABLISHED))
            row[f"engine_{ty}_walls_net_held"] = sum(1 for r in q if r["net_status"] == "HELD")
        row["freelancer"] = ("NOT COMPARABLE by thickness x type: his sheet splits external / internal 15 cm / internal 20 "
                             "cm, prints no thickness for the external walls and no black / white (see the section "
                             "table)")
        row["v29_vs_engine"] = ("length only: m2 NOT COMPARABLE (run A holds every block m2, MASONRY_HEIGHT_NOT_IN_THE_DRAWING; "
                                "held is not 0); type NOT COMPARABLE (run A has no black / white)" if a else
                                "no wall of this thickness in either source" if not rs else "run A has no line")
        out.append(row)
    return out


def run_a_bands(bands, v2, t108):
    """Run A wall bands against the engine's V2 runs of the same band id (T-125 / T-169 physical module): band gross =
    V2 architectural run + columns run A measures through + remainder; engine physical - run A's both-faces length =
    openings the engine keeps in the run (Q-73) + residual."""
    V = defaultdict(list)
    for r in v2:
        V[(r["floor"], r["run_id"].split("#")[0].replace("BAY|", ""))].append(r)
    rows_of = defaultdict(list)
    for r in t108:
        for run in [x for x in r["v2_runs"].split(";") if x]:
            rows_of[(r["floor"], run)].append(r["row_id"])
    seen, out, tot = set(), [], defaultdict(lambda: defaultdict(float))
    for a in bands:
        runs = V.get((a["floor"], a["wall_id"]), [])
        seen.update((r["floor"], r["run_id"]) for r in runs)
        arch = sum(f(r["arch_run_m"]) for r in runs if not r["run_id"].startswith("BAY|"))
        bay = sum(f(r["arch_run_m"]) for r in runs if r["run_id"].startswith("BAY|"))
        phys = sum(f(r["physical_q69b_m"]) for r in runs)
        ops = sum(f(x.split(":")[-1]) for r in runs for x in r["openings_in_run"].split("; ")
                  if x.count(":") == 2 and not x.startswith("GLAZED"))
        cols, g, n = f(a["columns_in_wall_lm"]), f(a["gross_lm"]), f(a["net_lm"])
        rem = g - arch - bay - cols
        if not runs:
            why = "band with no V2 run (a drawn stub; the engine row takes it from its V2 bay run)"
        elif abs(rem) <= 0.05:
            why = "band = V2 run + columns in wall" if cols else "agrees"
        elif rem > 0 and n + 0.05 < arch:
            why = ("band extent beyond the drawn wall pieces (run A joins collinear pieces across gaps with no wall "
                   "faces; its own both-faces length is below the V2 run)") if rem > 1.0 else "end convention (+)"
        else:
            why = "end convention (V2 stem to the face / corner, run A band end)"
        ids = sorted({x for r in runs for x in rows_of.get((r["floor"], r["run_id"]), [])})
        row = {"floor": a["floor"], "band": a["wall_id"], "t_m": a["family"], "kind": a["kind"],
               "runA_gross_lm": R3(g), "runA_both_faces_lm (released)": R3(n), "runA_columns_in_wall_lm": R3(cols),
               "v2_runs": ";".join(r["run_id"] for r in runs), "engine_rows": ";".join(ids),
               "v2_arch_run_m": R3(arch + bay), "engine_physical_m": R3(phys),
               "d_gross_minus_v2_arch_m": R3(g - arch - bay), "of_which_columns_m": R3(cols), "remainder_m": R3(rem),
               "openings_kept_in_engine_run_m (Q-73)": R3(ops),
               "residual_physical_minus_both_faces_minus_openings_m": R3(phys - n - ops), "class": why}
        out.append(row)
        t = tot[(a["floor"], a["family"])]
        for k, v in (("g", g), ("n", n), ("cols", cols), ("arch", arch + bay), ("phys", phys), ("ops", ops), ("rem", rem)):
            t[k] += v
    for r in v2:
        if (r["floor"], r["run_id"]) not in seen:
            out.append({"floor": r["floor"], "band": r["run_id"], "t_m": r["t_m"], "class": "V2 run with no run A band"})
    summ = []
    for (fl, fam), t in sorted(tot.items(), key=lambda kv: ("GF1F2F".index(kv[0][0]), kv[0][1])):
        summ.append({"floor": fl, "t_m": fam, "runA_gross_lm": R3(t["g"]), "v2_arch_run_m": R3(t["arch"]),
                     "d_m": R3(t["g"] - t["arch"]), "columns_in_wall_m": R3(t["cols"]),
                     "remainder_m": R3(t["rem"]), "runA_both_faces_lm": R3(t["n"]), "engine_physical_m": R3(t["phys"]),
                     "openings_in_engine_run_m": R3(t["ops"]), "residual_m": R3(t["phys"] - t["n"] - t["ops"])})
    return out, summ


def gap_table(t108):
    out = []
    for ty, t in (("BLACK", "0.15"), ("BLACK", "0.2"), ("WHITE", "0.15"), ("WHITE", "0.2")):
        rs = [r for r in t108 if r["block_type"] == ty and r["t_m"] == t]
        g = RV.gap(rs)
        fmt = lambda L: " + ".join(f"{w} {v:.3f}" for w, v in L) or "-"
        out.append({
            "block_type": ty, "t_m": t, "established_gross_m2": R3(g["established_gross"]),
            "all_deductions_m2": R3(g["all_deductions"]), "established_net_m2": R3(g["established_net"]),
            "gap_m2 (gross - deductions - net)": R3(g["gap"]),
            "A: gross of walls with established gross and HELD net": fmt(g["gross_of_established_gross_held_net"]),
            "B: deductions on those walls": fmt(g["deductions_on_established_gross_held_net"]),
            "C: deductions on HELD-gross walls": fmt(g["deductions_on_held_gross"]),
            "A - B - C m2": R3(g["reconstructed"]), "residual_m2 (rounding of 3-decimal rows)": R3(g["gap"] - g["reconstructed"]),
        })
    return out


# ------------------------------------------------------------------------------------------------ sources
SOURCES = [
    ("S1", f"{DRIVE} / المبانى.xlsx", "HUMAN FREELANCER BOQ (blockwork)",
     "the only blockwork workbook; sheets الغلاف (cover totals) and الكميات (rows 14-227: length x height x count per "
     "row); sections external / internal 15 cm / internal 20 cm by floor; no black / white, no thickness printed for "
     "external walls", "comparison column only (programme s.5)", "873308bb (sha256 verified this run = "
     "BENCHMARK_SOURCE_MANIFEST BLK)"),
    ("S2", "released V2.9 + route G, pinned run A (V29_ROUTEG_NO_PROFILE, T-165)", "OLDER AUTOMATED TAKEOFF",
     "ARCH.WALL_RUN lm by floor x thickness (7 lines, 216.931 lm released = both faces drawn); ARCH.WALL_PANEL / "
     "ARCH.WALL_VOLUME / MAS.BLOCK 21 lines BLOCKED_RFI (no masonry height, no block m2)",
     "comparison column only", "BOQ_LINES.csv b96185d4, reproduced this run on 41847bff (REPRODUCED, 1,455 lines)"),
    ("S3", "MASONRY_AREA_V1 r2 (T-108 r2, checker MERGED 01eeafd0) + T-175 + T-176 + T-215", "CURRENT ENGINE (opt-in, "
     "not released)", "74 wall rows: length, height under the member above (Q-60 A), gross, deductions (Q-73), net, "
     "m3, white units; black units T-176", "the register's only quantity source", "working head 41847bff"),
    ("S4", f"{DRIVE} / Alsenan Chalet_by_category.xlsx and .pdf ('Cost By Category', 18/10/2026)",
     "OWNER COST RECORD (contractor purchase quantities), neither the freelancer BOQ nor a takeoff",
     "category 'shell-stage blockwork': one line of about 22 thousand blocks (qty 21,500, block type not stated) and "
     "one line of white block 90 m3 (pdf page 5)", "NOT COMPARABLE with m2 (procurement units, no floor / thickness / "
     "type split); a later cross-check for T-176 procurement only", "not hashed (read from the Drive metadata text)"),
    ("S5", f"{ARCH}; {ST}; {DRIVE} / ST7757.pdf; p7757_arch_sheet09.pdf / sheet10.pdf",
     "PROJECT DRAWINGS (inputs, not quantity sources)", "plans, sections, ST roof-slab plans, schedules, notes",
     "evidence for every register row", "P7757.dxf ab54dd55 / ST7757 dxf.dxf 9f9d1179 (verified this run)"),
    ("S6", f"{DRIVE} / the other freelancer workbooks (finishes, plaster / Sigma, paint, aluminium, concrete + steel)",
     "HUMAN FREELANCER BOQ (other trades)", "no blockwork line (every non-empty row of the five files searched for "
     "طابوق / مباني: none)", "not a blockwork source", "BENCHMARK_SOURCE_MANIFEST"),
]


# ------------------------------------------------------------------------------------------------ output
def to_csv(rows, cols=None):
    buf = io.StringIO()
    cols = cols or list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else v) for k, v in r.items()})
    return buf.getvalue()


def build():
    t108, t143, hosts, t176, t215, v2, v29, v29b, raw = inputs()
    bands, bsum = run_a_bands(v29b, v2, t108)
    fr, ftot = freelancer_rows(raw)
    reg = register(t108, t143, hosts, t176, t215)
    cov = coverage(t108, reg)
    sec = three_way_section(t108, fr)
    thk = three_way_thickness(t108, v2, v29)
    gp = gap_table(t108)
    tot = RV.totals(t108)
    cause_counts = defaultdict(int)
    cause_m2 = defaultdict(float)
    for x in reg:
        if x["held_cause_class"]:
            cause_counts[x["held_cause_class"]] += 1
            cause_m2[x["held_cause_class"]] += f(x["gross_m2"]) if x["gross_class"] == "HELD" else 0.0
    est = lambda ty, t, s: sum(f(r["net_m2"]) for r in t108 if r["block_type"] == ty and r["t_m"] == t and r["net_status"] == s)
    summary = {
        "task": "T-225", "base": "41847bff", "quantities_changed": 0,
        "register_rows": len(reg), "walls_net_held": sum(1 for x in reg if x["net_class"] == "HELD"),
        "held_cause_counts": dict(sorted(cause_counts.items())),
        "held_gross_figure_by_cause_m2 (not a quantity)": {k: round(v, 3) for k, v in sorted(cause_m2.items())},
        "black": {t: {"gross_source_supported": round(sum(f(r["gross_m2"]) for r in t108 if r["block_type"] == "BLACK" and r["t_m"] == t and r["gross_status"] == "DRAWING-CONFIRMED"), 3),
                      "gross_held_figure": round(sum(f(r["gross_m2"]) for r in t108 if r["block_type"] == "BLACK" and r["t_m"] == t and r["gross_status"] == "HELD"), 3),
                      "deductions": round(sum(f(r["deducted_m2"]) for r in t108 if r["block_type"] == "BLACK" and r["t_m"] == t), 3),
                      "net_source_supported": round(est("BLACK", t, "DRAWING-CONFIRMED"), 3),
                      "net_project_specific": round(est("BLACK", t, "ASSUMED — OWNER-APPROVED"), 3)} for t in ("0.15", "0.2")},
        "net_VERIFIED_m2": 0.0, "net_VERIFIED_walls": 0,
        "gap": {f"{g['block_type']} {g['t_m']}": g["gap_m2 (gross - deductions - net)"] for g in gp},
        "freelancer_cover_totals_m2": {x["cell_ref"]: round(x["value_m2"], 4) for x in ftot},
        "v29_released_wall_run_lm": round(sum(f(l["measured_net"]) for l in v29 if l["item_code"] == "ARCH.WALL_RUN"), 3),
        "v29_block_m2_lines": sum(1 for l in v29 if l["item_code"] == "MAS.BLOCK"),
        "totals_by_floor_t_type": {"|".join(k): {a: round(b, 3) for a, b in v.items()} for k, v in sorted(tot.items())},
    }
    files = {
        "SOURCES.csv": to_csv([dict(zip(("id", "source", "provenance_class", "blockwork_content", "use", "integrity"), s))
                               for s in SOURCES]),
        "FREELANCER_BLK_LINES.csv": to_csv([{"workbook": FL_TITLE, **r} for r in fr]),
        "FREELANCER_BLK_TOTALS.csv": to_csv([{"workbook": FL_TITLE, **r} for r in ftot]),
        "THREE_WAY_BY_FLOOR_SECTION.csv": to_csv(sec),
        "THREE_WAY_BY_FLOOR_THICKNESS_TYPE.csv": to_csv(thk),
        "GAP_RECONSTRUCTION.csv": to_csv(gp),
        "RUN_A_VS_ENGINE_BY_BAND.csv": to_csv(bands, list(bands[0].keys())),
        "RUN_A_VS_ENGINE_BY_FLOOR_THICKNESS.csv": to_csv(bsum),
        "BLOCKWORK_WALL_REGISTER_V1.csv": to_csv(reg),
        "BEFORE_COVERAGE.csv": to_csv(cov),
        "summary.json": json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=False) + "\n",
    }
    return files


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    files = build()
    if "--check" in argv:
        bad = [n for n, t in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        if bad:
            print("differs:", ", ".join(bad))
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
