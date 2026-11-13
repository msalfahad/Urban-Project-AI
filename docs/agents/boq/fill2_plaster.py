"""MAIN FILL 2: dry-room plaster and paint from the committed face ledger (T556_PLASTER_HEIGHT.json) with the owner's
heights (2026-11-13: plaster H = storey - slab = 4.34 GF, 3.84 annex, 4.04 upper floors) and the company defaults
(opening head 2.20 m where no height is printed; beam-end ranges at midpoint; false ceiling = clear height - 0.90).

    python3 -I fill2_plaster.py T556_PLASTER_HEIGHT.json LINE_INDEX.json OUT_DIR

Plaster (FIN.PLASTER HL:WALL_FINISH:<room>) = face_lm x H - openings - beam ends  -> RELEASED, label DEFAULT
Paint   (FIN.PAINT   HL:WALL_FINISH:<room>) = plaster x (H - 0.90) / H                -> RELEASED, label ESTIMATE
Nothing here is verified; the Checker spot-checks; a DRAWING-READ figure replaces any row.
"""
from __future__ import annotations
import json, sys, os, re
from decimal import Decimal as D

SLAB = D("0.16"); STOREY = {"GF": D("4.50"), "1F": D("4.20"), "2F": D("4.20"), "ANNEX": D("4.00")}
HEAD_DEFAULT = D("2.20"); CEIL_DROP = D("0.90")
ANNEX_ROOMS = {"GF-01", "GF-04"}  # printed FFL +0.30 / roof +4.30 (T556 zone text)


def main(t556_path, index_path, out_dir):
    t = json.load(open(t556_path)); idx = json.load(open(index_path))
    L = {l["line_id"]: l for l in idx["lines"]}
    paint_by_room = {}
    for l in idx["lines"]:
        m = re.match(r"HL:WALL_FINISH:(\w+):PAINT$", str(l.get("element_id")))
        if m and l["item_code"] == "FIN.PAINT":
            paint_by_room[m.group(1).replace("_", "-")] = l
    rows, notes = [], []
    for r in t["rows"]:
        room = r["room"]; lid = r["line_id"]; cur = L.get(lid)
        if not cur:
            notes.append(f"{room}: line {lid} not in the index"); continue
        zone = "ANNEX" if room in ANNEX_ROOMS else room.split("-")[0]
        H = STOREY[zone] - SLAB
        H_old = D(str(r.get("H_floor_m") or r.get("H_roof_scenario_m")))
        face = D(str(r["face_lm"])); gross = face * H
        ded, basis = D(0), []
        for o in r["new"]["openings"]:
            lo, hi, b = D(str(o["lo"])), D(str(o["hi"])), o["basis"]
            if b.startswith("HELD (no height"):
                if o["id"].startswith(("A-", "L-")):      # arch / open side: width = hi / H_old, head default 2.20
                    w = hi / H_old; a = w * HEAD_DEFAULT; basis.append(f"{o['id']} {w:.3f} m wide x 2.20 head (default)")
                else:                                       # a window with no printed height: the drawn outline
                    a = hi; basis.append(f"{o['id']} drawn outline {hi} m2 (default: full outline)")
            elif b.startswith("HELD (outline"):
                a = (lo + hi) / 2; basis.append(f"{o['id']} outline range midpoint {a:.3f}")
            else:
                a = hi; basis.append(f"{o['id']} {a}")
            ded += a
        be_lo = D(str(r["new"]["beam_ends_lo"])); be_hi = D(str(r["new"]["beam_ends_hi"])); be = (be_lo + be_hi) / 2
        net = gross - ded - be
        plaster_basis = f"{room}: face {face} lm x H {H} (storey {STOREY[zone]} - slab 0.16) = {gross:.3f} - openings {ded:.3f} [{'; '.join(basis)}] - beam ends {be:.3f} (midpoint)"
        rows.append({"set": "PLASTER_DRY", "line_id": lid, "item_code": "FIN.PLASTER", "unit": "m2", "element_id": cur.get("element_id"),
                     "before": {"class": cur["class"], "net": cur["measured_net"], "low": cur["held_low"], "high": cur["held_high"]},
                     "after": {"class": "RELEASED", "net": float(round(net, 4))}, "label": "DEFAULT", "basis": plaster_basis})
        p = paint_by_room.get(room)
        if p:
            Hc = H - CEIL_DROP; paint = net * Hc / H
            rows.append({"set": "PAINT_DRY", "line_id": p["line_id"], "item_code": "FIN.PAINT", "unit": "m2", "element_id": p.get("element_id"),
                         "before": {"class": p["class"], "net": p["measured_net"], "low": p["held_low"], "high": p["held_high"]},
                         "after": {"class": "RELEASED", "net": float(round(paint, 4))}, "label": "ESTIMATE",
                         "basis": f"{room}: plaster {net:.3f} x ceiling height {Hc} / {H} (false ceiling = clear height - 0.90 default; openings taken proportionally)"})
        else:
            notes.append(f"{room}: no FIN.PAINT line in the index")
    os.makedirs(out_dir, exist_ok=True)
    out = {"schema": "MAIN_CHAT_FIX_ROWS_V1", "candidate_version": idx.get("candidate_version"), "source": "T556_PLASTER_HEIGHT.json rows + owner heights 2026-11-13", "rows": rows, "not_filled": notes}
    json.dump(out, open(os.path.join(out_dir, "MAIN_FILL_2.json"), "w"), indent=1)
    tot = {}
    for r in rows: tot[r["set"]] = tot.get(r["set"], 0) + r["after"]["net"]
    md = ["# MAIN FILL 2: dry-room plaster and paint (main chat; DEFAULT / ESTIMATE, never verified)", "", f"Totals: {tot}", "", "| set | room line | before | after | basis |", "|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]; md.append(f"| {r['set']} | {r['element_id']} | {b['class']} {b['net'] or ''} {('' if b['low'] is None else str(b['low'])+'..'+str(b['high']))} | {r['after']['net']} | {r['basis']} |")
    md += ["", "## Not filled"] + [f"- {n}" for n in notes]
    open(os.path.join(out_dir, "MAIN_FILL_2.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({"rows": len(rows), "totals": {k: round(v, 2) for k, v in tot.items()}, "not_filled": notes}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
