"""T-285 builder: blockwork wall register v3 = register v2 (T-228 r2) + the T-274 piece closure (R-T274-1) + the T-261 r3
wall-by-wall established parts (R-T261-1) + the Checker-VERIFIED walls at the Checker's own value + the T-277 crossing
strips carried as CONFLICT with both readings (R-T285-1, register_v3.py). Read-only over the merged ledgers; writes only
research/agents_t285/*. Numbers and ids only: no drawing coordinate, image or client name.

Inputs (all merged, cited by merge commit in the report):
  research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv   register v2 (T-228 r2, MERGED bf4dd2a9)
  research/agents_t274/T274_NET_BEFORE_AFTER.csv        established net after the exact piece cut (T-274, MERGED aba9399a)
  research/agents_t274/T274_CORRECTED.csv / T274_SIBLING_CHECK.csv / T274_TEXT_CORRECTIONS.csv
  research/agents_t261/T261_SPLIT.csv                   established pieces of the 11 split walls (T-261 r3, MERGED 164b189f)
  research/agents_t285/CHECKER_VERIFIED.csv             the 13 walls the Checker re-measured whole (SCOREBOARD 00:06)
  research/agents_t285/CONFLICT_STRIPS_T277.csv         crossing strips under width-CONFLICT bands (T-277, MERGED 9446dfcb)
Drawings behind them: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and
'ST7757 dxf.dxf' (sha 9f9d1179). Usage: python3 -I research/agents_t285/build_t285.py [--check]"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import register_v3 as R3  # noqa: E402

V2 = ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv"
T274_NET = ROOT / "research/agents_t274/T274_NET_BEFORE_AFTER.csv"
T274_COR = ROOT / "research/agents_t274/T274_CORRECTED.csv"
T274_SIB = ROOT / "research/agents_t274/T274_SIBLING_CHECK.csv"
T274_TXT = ROOT / "research/agents_t274/T274_TEXT_CORRECTIONS.csv"
T261 = ROOT / "research/agents_t261/T261_SPLIT.csv"
VER = HERE / "CHECKER_VERIFIED.csv"
CONF = HERE / "CONFLICT_STRIPS_T277.csv"
MERGES = {"T-228 r2": "bf4dd2a9", "T-261 r3": "164b189f", "T-274": "aba9399a", "T-277": "9446dfcb"}
NUM = re.compile(r"^\s*(-?[0-9]+(?:\.[0-9]+)?)")
BASIS_A = "A: register v2 + T-274 piece closure (walls established in v2)"
BASIS_B = "B: A + T-261 r3 established parts of 11 v2-HELD walls"


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def num(x):
    m = NUM.match(x or "")
    return float(m.group(1)) if m else None


def f4(x):
    return "" if x is None else f"{x:.4f}"


def readings_for(c, base, cor=None):
    """the readings of one wall's figure under a width-CONFLICT band. STRIP (T-277): from its T-274 (drawn) basis, strip
    delta x (h_beyond - h_under). T274_RANGE (T-215 junction bound): the two ends T-274's exact pieces give, the drawn
    width reading first (the junction under the wider drawn band is the lower)."""
    if c["kind"] == "T274_RANGE":
        lo, hi = [float(x) for x in cor["exact_gross_m2"].split("..")]
        return {"drawn width " + c["drawn_width_m"]: round(lo, 4), "schedule width " + c["schedule_width_m"]: round(hi, 4)}
    dh = float(c["h_beyond_m"]) - float(c["h_under_beam_m"])
    drawn_under = float(c["under_wall_drawn_m"])
    out = {"drawn width " + c["drawn_width_m"]: round(base, 4)}
    for i, u in enumerate(c["under_wall_schedule_m"].split("|")):
        tag = "schedule width " + c["schedule_width_m"] + (f" (face {'kept' if i == 0 else 'moved'})"
                                                              if "|" in c["under_wall_schedule_m"] else "")
        out[tag] = round(base + (drawn_under - float(u)) * dh, 4)
    return out


def build():
    v2 = rd(V2)
    R3.one_wall_once(v2)
    net274 = {r["wall_id"]: r for r in rd(T274_NET)}
    cor = {r["wall_id"]: r for r in rd(T274_COR)}
    sib = {r["wall_id"]: r for r in rd(T274_SIB)}
    txt = {r["wall_id"]: r for r in rd(T274_TXT)}
    ver = {r["wall_id"]: r for r in rd(VER)}
    conf = {r["wall_id"]: r for r in rd(CONF)}
    split = defaultdict(list)
    for r in rd(T261):
        split[r["wall_id"]].append(r)

    rows, causes_a, causes_b, diffs = [], [], [], []
    for r in v2:
        w = r["wall_id"]
        t = float(r["t_m"])
        net_v2 = num(r["net_m2"])
        cls_v2 = r["net_class"]
        ded_v2 = num(r["deductions_m2"]) or 0.0
        gross_v2 = num(r["gross_m2"])
        row = {"wall_id": w, "floor": r["floor"], "group": r["group"], "block_type": r["block_type"], "t_m": r["t_m"],
               "length_m": r["length_m"], "net_m2_v2": f4(net_v2) if net_v2 is not None else "", "net_class_v2": cls_v2,
               "layer": "v2", "held_items": [], "conflict": "", "differences_listed": [], "verified_by": "",
               "cause_of_change": "", "unresolved_reason_v3": r["unresolved_reason"]}
        sstat = sib.get(w, {}).get("status", "")
        row["t274_piece_status"] = sstat
        if w in txt:
            row["unresolved_reason_v3"] = txt[w]["corrected_text"]
        if net_v2 is not None:                                     # established in v2: basis A
            assert abs(net_v2 - (gross_v2 - ded_v2)) < 0.0015, w
            n = net274[w]
            prop = float(n["net_after_m2"])
            range_cause = None
            if w in conf and conf[w]["kind"] == "T274_RANGE":        # established = the part in every reading
                common, _, _ = R3.conflict_part(readings_for(conf[w], None, cor[w]))
                if common < net_v2 - 1e-9:
                    raise R3.RegisterError(f"BELOW_V2: {w} common reading {common} below register v2 {net_v2}")
                prop = round(common - ded_v2, 4)
                range_cause = ("R-T274-1 rule 1-3: exact closing pieces (register v2 figure was the sampled base + the "
                               "T-215 junction minimum, below every CB2 reading); CB2 increment stays CONFLICT")
            cur = {"value": net_v2, "class": cls_v2, "source": "register v2"}
            if w in ver:
                vv = float(ver[w]["net_m2"])
                if abs(vv - net_v2) > 1e-9:
                    diffs.append({"wall_id": w, "what": "Checker value differs from register v2",
                                  "delta_m2": round(vv - net_v2, 4)})
                cur = {"value": vv, "class": R3.VERIFIED, "source": ver[w]["checker_run"]}
                row["verified_by"] = ver[w]["checker_run"] + ": " + ver[w]["what_was_remeasured"]
            kept, d = R3.apply_value(cur, {"value": prop, "class": cur["class"] if cur["class"] != R3.VERIFIED else
                                           (cls_v2 if cls_v2 != R3.VERIFIED else R3.SS), "source": "T-274"})
            if d and d["delta_m2"] and abs(d["delta_m2"]) > 1e-9:
                row["differences_listed"].append(f"T-274 proposal {d['proposed']:.4f} ({d['delta_m2']:+.4f}) not applied: "
                                                 "VERIFIED kept")
            # exact-piece differences T-274 already listed on kept walls (VERIFIED value or VERIFIED gross)
            if w in cor and abs(float(n["delta_m2"])) < 1e-9 and not range_cause:
                eg = num(cor[w]["exact_gross_m2"])
                if eg is not None and abs(eg - gross_v2) > 1e-6:
                    row["differences_listed"].append(
                        f"T-274 exact pieces gross {cor[w]['exact_gross_m2'][:60]} vs kept {gross_v2:.4f} "
                        f"({eg - gross_v2:+.4f}); kept: {'VERIFIED net' if w in ver else 'VERIFIED gross (T-143)' if r['gross_class'] == R3.VERIFIED else 'figure'}")
            val = kept["value"]
            delta = round(val - net_v2, 6)
            ded = ded_v2
            if w == "1F-W00":                                       # W18 by its part inside the masonry (R-T274-1 r5)
                ded = round(ded_v2 - 0.0706, 4)
            if abs(delta) > 1e-9:
                cause = ("R-T274-1 rule 5: W18 deducted by its 0.4673 m inside the masonry, not 0.500" if w == "1F-W00"
                         else range_cause or "R-T274-1 rule 1-2: exact closing height pieces")
                causes_a.append({"wall_id": w, "cause": cause, "delta_m2": delta})
                row["cause_of_change"] = cause + f" ({delta:+.4f} m2)"
                row["layer"] = "v2 + T-274"
            cls = kept["class"]
            row.update({"net_m2_v3": f4(val), "net_class_v3": cls, "completeness": "ESTABLISHED",
                        "established_part_m2": f4(val), "deductions_m2_v3": f4(ded),
                        "gross_m2_v3": f4(val + ded if cls != R3.VERIFIED else gross_v2), "basis": "A"})
            if w in ver:
                row["layer"] = "v2 + Checker VERIFIED" + (" + T-274" if row["layer"] == "v2 + T-274" else "")
        elif w in split:                                            # T-261 r3 established part: basis B
            est_g = sum(float(p["gross_m2"]) for p in split[w] if p["piece_status"] != R3.HELD)
            est_d = sum(float(p["deductions_m2"] or 0) for p in split[w] if p["piece_status"] != R3.HELD)
            held = [R3.held_item(f"{p['piece']} {p['length_m']} m: {p['held_item']}",
                                 p["held_figure_not_a_quantity"] or None) for p in split[w] if p["piece_status"] == R3.HELD]
            val = round(est_g - est_d, 4)
            causes_b.append({"wall_id": w, "cause": "R-T261-1: T-261 r3 established part (drawn member extents)",
                             "delta_m2": val})
            row.update({"net_m2_v3": f4(val), "net_class_v3": R3.SS,
                        "completeness": "ESTABLISHED_PART_PLUS_HELD" if held else "ESTABLISHED",
                        "established_part_m2": f4(val), "deductions_m2_v3": f4(est_d), "gross_m2_v3": f4(est_g),
                        "basis": "B", "layer": "v2 + T-261 r3",
                        "cause_of_change": f"R-T261-1 established part {'of a split wall' if held else '(whole wall)'} "
                                           f"(+{val:.4f} m2)"})
            row["held_items"] = [h["held_item"] + (f" [figure, not a quantity: {h['figure_not_a_quantity']}]"
                                                   if h["figure_not_a_quantity"] else "") for h in held]
            if not held:
                row["unresolved_reason_v3"] = "no held item: whole wall from drawn member extents (T-261 r3)"
        else:                                                       # HELD wall: figure only
            g = num(cor[w]["exact_gross_m2"]) if w in cor else gross_v2
            row.update({"net_m2_v3": "", "net_class_v3": R3.HELD, "completeness": "HELD", "established_part_m2": "",
                        "deductions_m2_v3": r["deductions_m2"], "gross_m2_v3": "", "basis": "",
                        "gross_figure_not_a_quantity": f4(g) if g else ""})       # no figure is blank, never 0
            if w in cor:
                row["layer"] = "v2 + T-274 (figure)"
            hi = R3.held_item(r["held_cause_class"] or r["unresolved_reason"][:120] or "held (register v2)")
            row["held_items"] = [hi["held_item"]]
            if sstat == "CLOSED WITH HELD PIECES":
                row["held_items"].append("T-274 held piece(s): " + sib[w]["exact_gross_m2"].split("+", 1)[-1].strip()[:200])
        if w in conf:                                               # T-277: CONFLICT carried with both readings
            c = conf[w]
            base = num(row["net_m2_v3"]) if row["net_m2_v3"] else (num(cor[w]["exact_gross_m2"]) if w in cor
                                                                    else num(sib[w]["exact_gross_m2"]))
            rds = readings_for(c, base, cor.get(w))
            common, inc, _ = R3.conflict_part(rds)
            what = "net" if row["net_m2_v3"] else ("gross figure" if w in cor else "established-part figure")
            if row["net_m2_v3"]:
                assert abs(common - float(row["gross_m2_v3"])) < 1e-9 if c["kind"] == "T274_RANGE" else \
                    abs(common - float(row["net_m2_v3"])) < 1e-9, (w, common)
            row["conflict"] = (f"{c['member']} width CONFLICT ({c['designer_item']}): {what} readings "
                               + "; ".join(f"{k} {v:.4f}" for k, v in rds.items())
                               + f"; established = part in every reading {common:.4f}, CONFLICT increment {inc:.4f} m2 "
                               "by name (never added, never 0, none chosen)")
            row["conflict_increment_m2"] = f4(inc)
        row["net_m3_v3"] = f4(float(row["net_m2_v3"]) * t) if row["net_m2_v3"] else ""
        row["evidence_status_v3"] = R3.EVIDENCE_STATUS[row["net_class_v3"]]
        rows.append(row)
    R3.one_wall_once(rows)
    return rows, causes_a, causes_b, diffs


def totals(rows, basis):
    keep = [r for r in rows if r.get("net_m2_v3") and (r["basis"] == "A" or basis == "B")]
    by = defaultdict(float)
    for r in keep:
        by[r["net_class_v3"]] += float(r["net_m2_v3"])
    return {"net_m2": round(sum(float(r["net_m2_v3"]) for r in keep), 4),
            "net_m3": round(sum(float(r["net_m3_v3"]) for r in keep), 4),
            "by_class_m2": {k: round(v, 4) for k, v in sorted(by.items())},
            "walls": len(keep)}


COLS = ["wall_id", "floor", "group", "block_type", "t_m", "length_m", "net_m2_v2", "net_class_v2", "net_m2_v3",
        "net_class_v3", "evidence_status_v3", "completeness", "established_part_m2", "gross_m2_v3", "deductions_m2_v3",
        "net_m3_v3", "basis", "layer", "cause_of_change", "verified_by", "conflict", "conflict_increment_m2",
        "held_items", "gross_figure_not_a_quantity", "t274_piece_status", "differences_listed", "unresolved_reason_v3"]


def csv_text(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (" || ".join(r[k]) if isinstance(r.get(k), list) else r.get(k, "")) for k in cols})
    return b.getvalue()


def outputs():
    rows, ca, cb, diffs = build()
    v2_tot = round(sum(num(r["net_m2_v2"]) for r in rows if r["net_m2_v2"]), 4)
    ta, tb = totals(rows, "A"), totals(rows, "B")
    res_a = R3.reconcile(v2_tot, ta["net_m2"], ca)
    res_b = R3.reconcile(ta["net_m2"], tb["net_m2"], cb)
    rec = ([{"step": BASIS_A, "wall_id": c["wall_id"], "cause": c["cause"], "delta_m2": f4(c["delta_m2"])} for c in ca]
           + [{"step": BASIS_B, "wall_id": c["wall_id"], "cause": c["cause"], "delta_m2": f4(c["delta_m2"])} for c in cb])
    rec += [{"step": "TOTAL A", "wall_id": "", "cause": f"v2 {v2_tot:.4f} -> {ta['net_m2']:.4f}; residual {res_a:.4f}",
             "delta_m2": f4(ta["net_m2"] - v2_tot)},
            {"step": "TOTAL B", "wall_id": "", "cause": f"A {ta['net_m2']:.4f} -> {tb['net_m2']:.4f}; residual {res_b:.4f}",
             "delta_m2": f4(tb["net_m2"] - ta["net_m2"])}]
    # floor x thickness x type before / after
    fa = defaultdict(lambda: [0.0, 0.0, 0.0, 0, 0])
    for r in rows:
        k = (r["floor"], r["t_m"], r["block_type"])
        if r["net_m2_v2"]:
            fa[k][0] += float(r["net_m2_v2"])
        if r.get("net_m2_v3") and r["basis"] == "A":
            fa[k][1] += float(r["net_m2_v3"])
        if r.get("net_m2_v3"):
            fa[k][2] += float(r["net_m2_v3"])
        fa[k][3] += r["net_class_v3"] == R3.HELD
        fa[k][4] += r["completeness"] == "ESTABLISHED_PART_PLUS_HELD"
    ba = [{"floor": k[0], "t_m": k[1], "block_type": k[2], "net_v2_m2": f4(v[0]), "net_v3_basis_A_m2": f4(v[1]),
           "net_v3_basis_B_m2": f4(v[2]), "delta_A_m2": f4(v[1] - v[0]), "delta_B_m2": f4(v[2] - v[0]),
           "walls_held_v3": v[3], "walls_part_plus_held_v3": v[4]} for k, v in sorted(fa.items())]
    reg = csv_text(rows, COLS)
    sha = hashlib.sha256(reg.encode()).hexdigest()
    export = {"schema": "URBAN_BLOCKWORK_REGISTER_V3_EXPORT_V1", "rule": R3.RULE_ID, "register_sha256": sha,
              "unit": "m2 (net installed block area; m3 = net x thickness)", "integrates": dict(MERGES),
              "status_note": "research register; NOT RELEASED; procurement (block units, mortar) is not here (T-176)",
              "records": [], "declared_totals": {"basis_A": ta, "basis_B": tb}}
    for r in rows:
        rec_ = {"wall_id": r["wall_id"], "floor": r["floor"], "block_type": r["block_type"], "t_m": float(r["t_m"]),
                "state": r["completeness"], "owner_class": r["net_class_v3"], "evidence_status": r["evidence_status_v3"],
                "basis": r["basis"] or None,
                "net_m2": float(r["net_m2_v3"]) if r["net_m2_v3"] else None,
                "net_m3": float(r["net_m3_v3"]) if r["net_m3_v3"] else None,
                "held": r["held_items"] or [],
                "conflict": ({"text": r["conflict"], "increment_m2": float(r["conflict_increment_m2"])}
                             if r["conflict"] else None),
                "verified_by": r["verified_by"] or None}
        export["records"].append(rec_)
    summ = {"task": "T-285", "rule": R3.RULE_ID, "walls": len(rows), "register_v2_net_m2": v2_tot,
            "basis_A": ta, "basis_B": tb, "residual_A_m2": res_a, "residual_B_m2": res_b,
            "changed_walls_A": len(ca), "established_parts_B": len(cb),
            "verified_walls": sorted(r["wall_id"] for r in rows if r["net_class_v3"] == R3.VERIFIED),
            "verified_net_m2": ta["by_class_m2"].get(R3.VERIFIED),
            "conflict_walls": sorted(r["wall_id"] for r in rows if r["conflict"]),
            "conflict_increment_established_walls_m2": round(sum(float(r["conflict_increment_m2"]) for r in rows
                                                                  if r["conflict"] and r["net_m2_v3"]), 4),
            "walls_held_v3": sum(r["net_class_v3"] == R3.HELD for r in rows),
            "walls_part_plus_held_v3": sum(r["completeness"] == "ESTABLISHED_PART_PLUS_HELD" for r in rows),
            "differences_listed": diffs + [{"wall_id": r["wall_id"], "what": d} for r in rows
                                            for d in r["differences_listed"]],
            "register_sha256": sha, "integrates": MERGES, "applied": "register v3 (research); no BOQ line moved; "
            "released default V2.9 + route G unchanged"}
    return {"BLOCKWORK_WALL_REGISTER_V3.csv": reg,
            "RECONCILIATION_V3.csv": csv_text(rec, ["step", "wall_id", "cause", "delta_m2"]),
            "BEFORE_AFTER_V3.csv": csv_text(ba, list(ba[0].keys())),
            "REGISTER_V3_EXPORT.json": json.dumps(export, indent=1, ensure_ascii=False) + "\n",
            "summary.json": json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="refuse if a committed output differs")
    a = ap.parse_args(argv)
    bad = []
    for name, text in outputs().items():
        p = HERE / name
        if a.check:
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                bad.append(name)
        else:
            p.write_text(text, encoding="utf-8")
    if bad:
        print("STALE:", ", ".join(bad))
        return 1
    print("T-285 outputs", "reproduce" if a.check else "written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
