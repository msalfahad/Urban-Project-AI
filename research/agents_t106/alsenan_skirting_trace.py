"""T-106 Alsenan trace (research only; reads a run and the drawing, writes nothing but stdout).

For every FIN.SKIRTING line with a quantity in one ARCH_TAKEOFF run (canonical BOQ_LINES.json + ARCH_ROOMS.json),
it prints gross, the listed deductions, the net, the unlisted difference found by engine/source/
skirting_deduction_audit.py and its component(s), the room's held range [0, high], and the door / passage run of the
room set against the door widths drawn in the plan's door blocks (block extents along the wall, read with ezdxf from
the DXF itself, not from the engine). It then compares room groups with the freelancer's dry-room skirting rows
(gross perimeters, no deduction; typed below from his floors workbook, metres only).

    python3 -I research/agents_t106/alsenan_skirting_trace.py --run RUN_DIR [--dxf PLAN.dxf] [--freelancer]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.source import skirting_deduction_audit as A  # noqa: E402

# freelancer dry-room skirting rows (gross room perimeter, m; his floors workbook, sheet "ceramic", total 282.85 lm,
# no door deduction) grouped against the engine rooms they cover; "-" = no engine skirting line for that room
FREELANCER = [
    ("GF open plan: reception + dining (+ entrance hall)", 58.16 + 14.76, ("GF-RC99C2A", "GF-RC06FED")),
    ("GF master bedroom", 21.71, ("GF-R75FBAE",)),
    ("GF majlis / diwaniya", 20.00, ("GF-R7512EA",)),
    ("GF driver room", 12.50, ("GF-R51E127",)),
    ("1F living", 43.78, ("1F-R78C367",)),
    ("1F four bedrooms", 22.89 + 21.40 + 17.30 + 17.45, ("1F-RB72F22", "1F-R3CFCFD", "1F-RED0D19", "1F-R0E919A")),
    ("2F maid room", 19.30, ("2F-R1DB2D2",)),
    ("2F corridor (engine: stair hall, BLOCKED_RFI)", 13.60, ()),
]


def door_block_widths(dxf):
    """{block name: width along the wall (m)} of the door blocks inserted in model space (block extents in x; every
    insert is scaled +-1, i.e. mirrored at most)."""
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(dxf)
    out = {}
    for ins in doc.modelspace().query("INSERT"):
        b = doc.blocks.get(ins.dxf.name)
        if b is None or not any(e.dxftype() == "ARC" for e in b):
            continue
        ext = bbox.extents(list(b))
        sx = abs(ins.dxf.xscale)
        w = round((ext.extmax.x - ext.extmin.x) * sx / 1000.0, 3)
        out.setdefault(ins.dxf.name, {"width_m": w, "inserts": 0})["inserts"] += 1
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--dxf")
    ap.add_argument("--freelancer", action="store_true")
    a = ap.parse_args(argv)
    run = Path(a.run)
    doc = json.loads((run / "BOQ_LINES.json").read_text(encoding="utf-8"))
    lines = doc if isinstance(doc, list) else doc["lines"]
    rooms = json.loads((run / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    rid = {r["room_id"]: r for r in rooms}
    res = A.audit(lines, rooms)
    hi = {}
    for ln in lines:
        if ln.get("item_code") == "FIN.SKIRTING" and ln.get("evidence_state") == "BOUNDED_EXPOSURE":
            hi[ln["location"]["room_id"]] = ln["bounded_range"]["high"]
    print("| Floor | Room | Gross m | Listed deductions m | Net m | Unlisted m | Component | Range [0, high] m | "
          "Door + passage run m | Status |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    net = {}
    for r in res["records"]:
        if r.get("reason") == "SKIRTING_DECOMPOSITION_MISMATCH":
            continue
        rm = rid.get(r["room_id"], {})
        ru = rm.get("runs_lm") or {}
        comp = ", ".join(f"{c['what']} {c['lm']:.3f}" for c in (r.get("candidate") or {}).get("components") or ())
        net[r["room_id"]] = (r["gross_lm"], r["net_lm"], hi.get(r["room_id"], 0.0))
        print(f"| {r['floor']} | {r['room_name_en']} | {r['gross_lm']:.3f} | {r['listed_deductions_lm']:.3f} | "
              f"{r['net_lm']:.3f} | {r.get('unexplained_lm', 0.0):.3f} | {comp or '-'} | "
              f"{hi.get(r['room_id'], 0.0):.3f} | {ru.get('door', 0.0) + ru.get('passage', 0.0):.3f} | "
              f"{r['status']}{':' + r['reason'] if r.get('reason') else ''} |")
    s = dict(res["summary"])
    s.pop("not_net")
    print("\nsummary", json.dumps(s))
    if a.dxf:
        print("\ndoor blocks", json.dumps(door_block_widths(a.dxf), sort_keys=True))
    if a.freelancer:
        print("\n| Room group | Freelancer gross m | Engine gross m | Engine certain net m | Engine net + range "
              "high m | Gross diff % |")
        print("|---|---|---|---|---|---|")
        tf = tg = tn = th = 0.0
        for name, fl, ids in FREELANCER:
            g = sum(net[i][0] for i in ids if i in net)
            n = sum(net[i][1] for i in ids if i in net)
            h = sum(net[i][2] for i in ids if i in net)
            tf, tg, tn, th = tf + fl, tg + g, tn + n, th + n + h
            pct = f"{(g - fl) / fl * 100:+.1f}" if ids else "held"
            print(f"| {name} | {fl:.2f} | {g:.3f} | {n:.3f} | {n + h:.3f} | {pct} |")
        print(f"| total | {tf:.2f} | {tg:.3f} | {tn:.3f} | {th:.3f} | {(tg - tf) / tf * 100:+.1f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
