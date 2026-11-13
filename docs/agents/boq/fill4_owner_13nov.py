"""MAIN FILL 4 (owner 2026-11-13 evening): wet-room wall tiles at 3.00 m, the curved pool window at Q-76 A, the 2F roof
membrane released by materiality.

    python3 -I fill4_owner_13nov.py LINE_INDEX.json CANDIDATE_V3021_T335.json OUT_DIR

Wall tiles: the engine's released tile lines ran to the decor-ceiling underside (clear height - 0.90 = 3.44 m on GF,
3.14 m upper floors). Owner 2026-11-13: tile height 3.00 m from F.F.L. (as the freelancer). Released rooms:
net - run x (H_old - 3.00). Blank / held rooms: run x 3.00 - doorways x 2.20 m2 (door 1.00 x 2.20 default; no window).
"""
from __future__ import annotations
import json, re, sys, os, collections

TILE_H = 3.00; H_OLD = {"GF": 3.44, "1F": 3.14, "2F": 3.14}; DOOR_DEFAULT = 1.00 * 2.20


def main(index_path, cand_path, out_dir):
    idx = json.load(open(index_path)); L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    cs = open(cand_path).read()
    run = {}
    for m in re.finditer(r'"element_id": "((GF|1F|2F)-R[0-9A-F]+):wall_tile"', cs):
        seg = cs[m.start():m.start() + 900]; w = re.search(r'"wall_run_lm": ([0-9.]+)', seg)
        if w: run[m.group(1)] = float(w.group(1))
    doors = collections.Counter()
    for l in L:
        m = re.match(r"((GF|1F|2F)-R[0-9A-F]+):doorway ", str(l.get("element_id")))
        if m and l["item_code"] == "FIN.WP.DOORWAY": doors[m.group(1)] += 1
    rows, notes = [], []
    def row(l, net, label, basis, set_name):
        rows.append({"set": set_name, "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l.get("element_id"),
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": {"class": "RELEASED", "net": round(net, 4)}, "label": label, "basis": basis})
    for l in L:
        eid = str(l.get("element_id")); m = re.match(r"((GF|1F|2F)-R[0-9A-F]+):wall_tile$", eid)
        if l["item_code"] != "FIN.WALL.TILE":
            continue
        if not m:
            notes.append(f"{eid}: tile line with no wall run in the ledger (left as it is: {l['class']} {l['measured_net']})"); continue
        room, fl = m.group(1), m.group(2); r = run.get(room)
        if r is None:
            notes.append(f"{eid}: no wall run"); continue
        if l["class"] == "RELEASED":
            net = l["measured_net"] - r * (H_OLD[fl] - TILE_H)
            row(l, net, "DEFAULT", f"{room}: engine net {l['measured_net']} at decor-ceiling height {H_OLD[fl]} - run {r} lm x ({H_OLD[fl]} - {TILE_H}) = tiles to {TILE_H} m (owner 2026-11-13); openings unchanged (all below 3.00)", "TILE_300")
        else:
            d = doors.get(room, 1); net = r * TILE_H - d * DOOR_DEFAULT
            row(l, net, "DEFAULT", f"{room}: run {r} lm x {TILE_H} m (owner 2026-11-13) - {d} doorway x {DOOR_DEFAULT:.2f} m2 (door 1.00 x 2.20 default; windows not read; was {l['class']} {l['held_low']}..{l['held_high']} for the annex-height hold Q-54 B, now answered 4.00)", "TILE_300")
    for l in L:
        eid = str(l.get("element_id"))
        if l["item_code"] == "ARCH.WINDOW" and l["unit"] == "m2" and eid == "OPENINGS:ARCH_WINDOW:1F:HELD" and l["class"] == "HELD":
            row(l, 9.87, "DRAWING-READ", "W17 curved window over the pool: owner Q-76 A (2026-10-24): 3.29 x 3.00 = 9.870 m2, the 0.45 band excluded; the index still carried the range 9.87..11.515", "OWNER_ANSWERED")
        if l["item_code"] == "FIN.WP.ROOF" and eid == "2F-ROOF-AT379:wp_membrane" and l["class"] == "HELD":
            row(l, float(l["held_low"]), "DEFAULT", f"roof +9.70 membrane held {l['held_low']}..{l['held_high']} for a 0.16 m2 band question (D-BAND at the 2F west wall foot): below materiality, low end taken", "MATERIALITY")
    os.makedirs(out_dir, exist_ok=True)
    out = {"schema": "MAIN_CHAT_FIX_ROWS_V1", "candidate_version": idx.get("candidate_version"), "source": "owner 2026-11-13 evening (tiles 3.00 m; Q-76 A wired; roof band materiality)", "rows": rows, "not_filled": notes}
    json.dump(out, open(os.path.join(out_dir, "MAIN_FILL_4.json"), "w"), indent=1)
    md = ["# MAIN FILL 4: wall tiles at 3.00 m, W17 at Q-76 A, roof +9.70 membrane by materiality (main chat; never verified)", "", "| set | line | item | element | before | after | basis |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]; md.append(f"| {r['set']} | {r['line_id']} | {r['item_code']} | {r['element_id']} | {b['class']} {b['net'] if b['net'] is not None else ''}{(' ' + str(b['low']) + '..' + str(b['high'])) if b['low'] is not None else ''} | {r['after']['net']} | {r['basis']} |")
    md += ["", "## Not filled"] + [f"- {n}" for n in notes]
    open(os.path.join(out_dir, "MAIN_FILL_4.md"), "w").write("\n".join(md) + "\n")
    tot = sum(r["after"]["net"] for r in rows if r["set"] == "TILE_300")
    print(json.dumps({"rows": len(rows), "tiles_300_total_filled_rooms": round(tot, 2), "not_filled": notes}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
