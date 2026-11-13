"""MAIN FILL 3: external render / facade area from the engine's released facade run lengths x the owner's storey heights,
minus the released / held opening areas of the same floor (windows + external doors). Plinth = GF run x printed FFL
(+1.00 above ground). Label ESTIMATE (the sample QS method: outer perimeter x slab-to-slab height - openings).

    python3 -I fill3_facade.py LINE_INDEX.json OUT_DIR
"""
from __future__ import annotations
import json, sys, os, re

STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}; PLINTH = 1.00


def main(index_path, out_dir):
    idx = json.load(open(index_path)); L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    run, opening, basis_o = {}, {}, {}
    for l in L:
        eid = str(l.get("element_id"))
        m = re.match(r"(GF|1F|2F)-FACADE:facade$", eid)
        if m and l["item_code"] == "ARCH.FACADE_RUN" and l["class"] == "RELEASED":
            run[m.group(1)] = l["measured_net"]
        m = re.match(r"OPENINGS:(ARCH_WINDOW|DOOR_EXTERNAL_ALUMINIUM|DOOR_MAIN_ENTRANCE):(GF|1F|2F):", eid)
        if m and l["unit"] == "m2":
            f = m.group(2)
            if l["class"] == "RELEASED": a = l["measured_net"]
            elif l["held_low"] is not None: a = (float(l["held_low"]) + float(l["held_high"] or l["held_low"])) / 2
            else: continue
            opening[f] = opening.get(f, 0) + a; basis_o.setdefault(f, []).append(f"{m.group(1).lower()} {a:.2f}")
    rows, notes = [], []
    def row(l, net, basis):
        rows.append({"set": "FACADE", "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l.get("element_id"),
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": {"class": "RELEASED", "net": round(net, 4)}, "label": "ESTIMATE", "basis": basis})
    for l in L:
        if l["class"] != "HELD" or l["item_code"] not in ("ARCH.FACADE", "FIN.EXT.FINISH"):
            continue
        eid = str(l.get("element_id")); m = re.match(r"(GF|1F|2F)-FACADE:facade( below F\.F\.L\. \(plinth\))?$", eid)
        if not m or m.group(1) not in run:
            notes.append(f"{l['item_code']} {eid}: no released facade run"); continue
        f = m.group(1); r = run[f]
        if m.group(2):
            row(l, r * PLINTH, f"plinth: GF facade run {r} lm x {PLINTH} m (printed F.F.L. +1.00 above ground; no openings)")
        else:
            o = opening.get(f, 0.0); net = r * STOREY[f] - o
            row(l, net, f"{f} facade run {r} lm x storey {STOREY[f]} (slab to slab) = {r * STOREY[f]:.2f} - openings {o:.2f} [{'; '.join(basis_o.get(f, []))}] (sample QS method; parapets and returns not included)")
    os.makedirs(out_dir, exist_ok=True)
    out = {"schema": "MAIN_CHAT_FIX_ROWS_V1", "candidate_version": idx.get("candidate_version"), "source": "released ARCH.FACADE_RUN x owner storey heights - opening areas", "rows": rows, "not_filled": notes}
    json.dump(out, open(os.path.join(out_dir, "MAIN_FILL_3.json"), "w"), indent=1)
    md = ["# MAIN FILL 3: facade / external render (main chat; ESTIMATE, never verified)", "", "| line | item | element | before | after | basis |", "|---|---|---|---|---|---|"]
    for r in rows: md.append(f"| {r['line_id']} | {r['item_code']} | {r['element_id']} | {r['before']['class']} | {r['after']['net']} | {r['basis']} |")
    md += ["", "## Not filled"] + [f"- {n}" for n in notes]
    open(os.path.join(out_dir, "MAIN_FILL_3.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({"rows": len(rows), "by_item": {c: round(sum(r["after"]["net"] for r in rows if r["item_code"] == c), 2) for c in ("ARCH.FACADE", "FIN.EXT.FINISH")}, "not_filled": notes}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
