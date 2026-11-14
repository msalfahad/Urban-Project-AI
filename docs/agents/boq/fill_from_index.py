"""MAIN-CHAT FILL from the candidate line index alone (owner 2026-11-13 DELIVERY MODE, fallback order steps 3-4).

Reads one LINE_INDEX_V3_0_x.json and writes a FIX_ROWS set (JSON + Markdown) that gives a figure to lines the index
leaves blank or ranged, using only (a) company defaults and (b) ratios / areas of THIS villa. Every row carries its
label (DEFAULT / ESTIMATE) and its basis. Nothing here is verified: Worker 3 wires the set (T-770), the Checker spot
checks three lines, and a MEASURED or DRAWING-READ figure replaces a row whenever one exists.

    python3 -I fill_from_index.py LINE_INDEX.json OUT_DIR

Sets produced:
  FLOOR_BED      FIN.FLOOR.BED.DRY / .WET m3 ranges -> points at 3.5 cm (dry) / 5 cm (wet) x the paired m2 line (DEFAULT)
  FORMWORK_RATIO HELD formwork lines whose host concrete line is RELEASED -> host m3 x the villa's own m2/m3 ratio for
                 that element type (ESTIMATE); ratio from the RELEASED formwork / concrete pairs of the same index
  ROOF_LAYERS    insulation and protection m2 = the roof zone's finish / membrane area; screed m3 = area x 0.075;
                 top roof (+13.90) area = 2F slab panels m3 / 0.16 (ESTIMATE until the 2F slab panels are read)
  EARTH_DISPOSAL disposal = excavation (released + held low..high) - backfill (held low..high) (ESTIMATE, net, no bulking)
"""
from __future__ import annotations
import json, re, sys, collections, os

DRY_BED, WET_BED, SCREED_AVG, SLAB_T = 0.035, 0.05, 0.075, 0.16


def main(index_path, out_dir):
    idx = json.load(open(index_path))
    ver = idx.get("candidate_version", "?")
    L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    byid = {l["line_id"]: l for l in L}
    rows, notes = [], []

    def row(l, after, label, basis, set_name, low=None, high=None):
        rows.append({"set": set_name, "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
                     "element_id": l.get("element_id"), "before": {"class": l["class"], "net": l["measured_net"],
                     "low": l["held_low"], "high": l["held_high"]},
                     "after": ({"class": "HELD", "low": low, "high": high} if after is None else {"class": "RELEASED", "net": round(after, 6)}),
                     "label": label, "basis": basis})

    # 1. floor bed m3 points
    for code, t in (("FIN.FLOOR.BED.DRY", DRY_BED), ("FIN.FLOOR.BED.WET", WET_BED)):
        m2 = {str(l["element_id"]): l for l in L if l["item_code"] == code and l["unit"] == "m2" and l["class"] == "RELEASED"}
        for l in L:
            if l["item_code"] == code and l["unit"] == "m3" and l["class"] == "HELD":
                p = m2.get(str(l["element_id"]))
                if p and p["measured_net"]:
                    row(l, p["measured_net"] * t, "DEFAULT", f"{p['measured_net']} m2 x {t} m bed (owner default {t*100:g} cm, Q-45 range)", "FLOOR_BED")
                else:
                    notes.append(f"{code} {l['line_id']}: no released m2 pair; left as it is")

    # 2. formwork by the villa's own ratio: DISABLED 2026-11-14 (a member's ratio was applied to each of its partial face lines; T-762 fills formwork face by face)
    fw=[]; host_of={}; ratios={}
    if False:
        pairs = collections.defaultdict(lambda: [0.0, 0.0, 0])
        fw = [l for l in L if l["item_code"] in ("STR.FORMWORK", "STR.FORMWORK.STAIR")]
        host_of = {}
        for l in fw:
            m = re.search(r"FW:(L-[0-9a-f]{20})", str(l.get("element_id")))
            host_of[l["line_id"]] = byid.get(m.group(1)) if m else None
        for l in fw:
            h = host_of[l["line_id"]]
            if h and h["class"] == "RELEASED" and l["class"] == "RELEASED" and h["measured_net"]:
                r = pairs[h["item_code"]]; r[0] += l["measured_net"] or 0; r[1] += h["measured_net"]; r[2] += 1
        ratios = {k: (v[0] / v[1], v[2]) for k, v in pairs.items() if v[1] > 0 and v[2] >= 2}
        for l in fw:
            if l["class"] != "HELD":
                continue
            h = host_of[l["line_id"]]
            if h is None:
                notes.append(f"formwork {l['line_id']} ({str(l.get('element_id'))[:40]}): no host concrete line in the index; needs the element's own faces")
            elif h["class"] != "RELEASED":
                notes.append(f"formwork {l['line_id']}: host {h['item_code']} {h['line_id']} is HELD; fill after the concrete (T-761)")
            elif h["item_code"] not in ratios:
                notes.append(f"formwork {l['line_id']}: no ratio for host type {h['item_code']} (fewer than 2 released pairs)")
            else:
                r, n = ratios[h["item_code"]]
                row(l, h["measured_net"] * r, "ESTIMATE", f"host {h['item_code']} {h['line_id']} {h['measured_net']} m3 x {r:.3f} m2/m3 (this villa, {n} released pairs)", "FORMWORK_RATIO")

    # 3. roof layers
    def zone(eid):
        m = re.search(r"ROOF:([A-Z]+-\d+)", str(eid)); return m.group(1) if m else None
    area = {}
    for l in L:
        z = zone(l.get("element_id"))
        if z and l["item_code"] == "FIN.ROOF.FINISH" and l["class"] == "RELEASED":
            area[z] = (l["measured_net"], f"finish area of {z} (RELEASED {l['line_id']})", "ESTIMATE")
    slab2f = sum((l["measured_net"] or 0) for l in L if l["item_code"] == "STR.CONC.SLAB" and l["class"] == "RELEASED" and ":2F:" in str(l.get("element_id")))
    if slab2f and "ROOF-1390" not in area:
        area["ROOF-1390"] = (slab2f / SLAB_T, f"2F slab panels {slab2f:.3f} m3 / {SLAB_T} m slab = plan area (top roof +13.90)", "ESTIMATE")
    for l in L:
        z = zone(l.get("element_id"))
        if not z or l["class"] != "HELD" or z not in area:
            continue
        a, basis, lab = area[z]
        if l["item_code"] in ("FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.ROOF.FINISH"):
            row(l, a, lab, basis + " (layer = the area it covers; roof build-up default)", "ROOF_LAYERS")
        elif l["item_code"] == "FIN.ROOF.SCREED":
            row(l, a * SCREED_AVG, lab, basis + f" x {SCREED_AVG} m average falls screed (default)", "ROOF_LAYERS")
    for l in L:  # top-roof membrane blank: same area
        if l["item_code"] == "FIN.WP.ROOF" and l["class"] == "HELD" and l["held_low"] is None and "2F-ROOF-TOP" in str(l.get("element_id")) and "ROOF-1390" in area:
            a, basis, lab = area["ROOF-1390"]; row(l, a, lab, basis + " (membrane = roof area)", "ROOF_LAYERS")

    # 4. disposal
    ex_lo = ex_hi = bf_lo = bf_hi = 0.0; blank_ex = blank_bf = 0
    for l in L:
        if l["item_code"] == "STR.EARTH.EXCAVATION":
            if l["class"] == "RELEASED": ex_lo += l["measured_net"]; ex_hi += l["measured_net"]
            elif l["held_low"] is not None: ex_lo += float(l["held_low"]); ex_hi += float(l["held_high"] or l["held_low"])
            else: blank_ex += 1
        if l["item_code"] == "STR.EARTH.BACKFILL":
            if l["class"] == "RELEASED": bf_lo += l["measured_net"]; bf_hi += l["measured_net"]
            elif l["held_low"] is not None: bf_lo += float(l["held_low"]); bf_hi += float(l["held_high"] or l["held_low"])
            else: blank_bf += 1
    for l in L:
        if l["item_code"] == "STR.EARTH.DISPOSAL" and l["class"] == "HELD":
            lo, hi = max(ex_lo - bf_hi, 0.0), max(ex_hi - bf_lo, 0.0)
            row(l, None, "ESTIMATE", f"excavation {ex_lo:.2f}..{ex_hi:.2f} - backfill {bf_lo:.2f}..{bf_hi:.2f} m3 (net, no bulking; {blank_ex} excavation and {blank_bf} backfill lines still blank -> the range widens when they are filled)", "EARTH_DISPOSAL", low=round(lo, 3), high=round(hi, 3))

    os.makedirs(out_dir, exist_ok=True)
    summary = collections.Counter(r["set"] for r in rows)
    out = {"schema": "MAIN_CHAT_FIX_ROWS_V1", "candidate_version": ver, "defaults": {"dry_bed_m": DRY_BED, "wet_bed_m": WET_BED, "screed_avg_m": SCREED_AVG, "slab_t_m": SLAB_T},
           "formwork_ratios_m2_per_m3": {k: {"ratio": round(v[0], 4), "pairs": v[1]} for k, v in ratios.items()}, "rows": rows, "not_filled": notes, "counts": dict(summary)}
    json.dump(out, open(os.path.join(out_dir, "MAIN_FILL_1.json"), "w"), indent=1)
    md = [f"# MAIN FILL 1 on {ver} (main chat, from the line index alone; DEFAULT / ESTIMATE, never verified)", "",
          f"Rows: {dict(summary)}; not filled: {len(notes)}", "",
          "Formwork ratios (this villa, released pairs): " + ", ".join(f"{k.split('.')[-1]} {v[0]:.2f} m2/m3 ({v[1]})" for k, v in sorted(ratios.items())), "",
          "| set | line | item | unit | before | after | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]; a = r["after"]
        bs = f"{b['class']} {b['net'] if b['net'] is not None else ''}{(' ' + str(b['low']) + '..' + str(b['high'])) if b['low'] is not None else ''}".strip()
        as_ = f"{a['net']}" if "net" in a else f"HELD {a['low']}..{a['high']}"
        md.append(f"| {r['set']} | {r['line_id']} | {r['item_code']} | {r['unit']} | {bs} | {as_} | {r['label']} | {r['basis']} |")
    md += ["", "## Not filled (reason)"] + [f"- {n}" for n in notes]
    open(os.path.join(out_dir, "MAIN_FILL_1.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({"rows": dict(summary), "not_filled": len(notes), "ratios": {k: round(v[0], 2) for k, v in ratios.items()}}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
