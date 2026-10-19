"""MEMBRANE TABLE (task T-072, opt-in) - writes the owner's membrane purchase table from the output files of an
architectural run (ARCH_TAKEOFF_V2.6 or later); it reads the engine's files and computes no quantity of its own
(engine/source/membrane_purchase_table.py). Nothing in the run folder is changed.

Reads from RUN_DIR:
    WATERPROOFING_SCHEDULE.json   the schedule rows (waterproofing_system.schedule)            required
    MEMBRANE_CUTTING_PLAN.json    the cutting plan per membrane system                          required
    WP_INSTALLATION.json          the junction alternatives (continuous fold)                   optional
    MATERIAL_RESULTS.json         the membrane layouts (strips of the separate upstand)        optional
    BOQ_LINES.json                FIN.WP.FLOOR lines without a quantity become HELD rows        optional
--held FILE: further HELD areas as a JSON list of {floor, room_id, reason[, name_en, name_ar, kind, source]} (for
example roofs or roomless labels another module holds); never a quantity, never 0.

Writes to --out: MEMBRANE_TABLE.json, MEMBRANE_TABLE.csv, MEMBRANE_TABLE.md.

CLI: python3 -I tools/membrane_table.py RUN_DIR --out OUT_DIR [--held HELD.json] [--project-id ID]"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import membrane_purchase_table as MT       # noqa: E402


def _load(p, required=True):
    if not p.exists():
        if required:
            raise SystemExit(f"membrane_table: {p.name} not found in the run folder")
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def build(run_dir, held_file=None, project_id=None):
    run = Path(run_dir)
    sched = _load(run / "WATERPROOFING_SCHEDULE.json")["waterproofing"]
    systems = _load(run / "MEMBRANE_CUTTING_PLAN.json")["systems"]
    inst = {(x["floor"], x["room_id"]): x for x in
            ((_load(run / "WP_INSTALLATION.json", False) or {}).get("installation") or ())}
    lays = {}
    for m in (_load(run / "MATERIAL_RESULTS.json", False) or {}).get("results") or ():
        loc = m.get("location") or {}
        if str(m.get("method") or "").startswith("MEMBRANE") and loc.get("room_id") is not None:
            lays[(loc.get("floor"), loc["room_id"])] = m
    roll = {s["system_id"]: s["roll_width_m"] * s["roll_length_m"] for s in systems}
    rows = [MT.area_row(r, lays.get((r["floor"], r["room_id"])), inst.get((r["floor"], r["room_id"])),
                        roll_area_m2=roll.get(r["system_id"])) for r in sched["areas"]]
    measured = {(r["floor"], r["room_id"]) for r in rows}
    lines = _load(run / "BOQ_LINES.json", False) or []
    held = MT.held_from_lines(lines, measured)
    seen = measured | {(h["floor"], h["room_id"]) for h in held}
    # spaces whose wet / dry type is under review (UP-REVIEW-001): their wet scenario carries a membrane
    for s in (_load(run / "REVIEW_SPACES.json", False) or {}).get("spaces") or ():
        wet = [i for i in (s.get("conditional") or {}).get("WET_SCOPE") or () if i.get("item_code") == "FIN.WP.FLOOR"]
        key = (s.get("floor"), s.get("room_id"))
        if wet and key not in seen:
            q = wet[0].get("quantity")
            held.append(MT.held_row(floor=key[0], room_id=key[1], name_en=s.get("name_en"), kind="WET_REVIEW",
                                    reason=f"wet / dry under review ({s.get('issue_code')}, UP-REVIEW-001): if wet, "
                                           f"floor {q} m2 by the run's wet scenario; not in any roll total",
                                    source="REVIEW_SPACES.json"))
            seen.add(key)
    # open plans that join a wet function with a dry one (UP-WET-001 REVIEW): the wet zone is not drawn
    for r in (_load(run / "ARCH_ROOMS.json", False) or {}).get("rooms") or ():
        fs = r.get("finish_scope") if isinstance(r.get("finish_scope"), dict) else {}
        key = (r.get("floor"), r.get("room_id"))
        if fs.get("scope") == "REVIEW" and r.get("class") in ("ROOM", "MIXED") and key not in seen:
            held.append(MT.held_row(floor=key[0], room_id=key[1], name_en="+".join(r.get("codes") or ()),
                                    kind="OPEN_PLAN_WET_REVIEW", reason="; ".join(fs.get("flags") or ()) or
                                    fs.get("basis") or "finish scope REVIEW (UP-WET-001)", source="ARCH_ROOMS.json"))
            seen.add(key)
    if held_file:
        for h in json.loads(Path(held_file).read_text(encoding="utf-8")):
            held.append(MT.held_row(**{k: h.get(k) for k in ("floor", "room_id", "reason", "name_en", "name_ar",
                                                              "kind", "source")}))
    return MT.table(rows, systems, held=held, project_id=project_id)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--held")
    ap.add_argument("--project-id")
    a = ap.parse_args(argv)
    t = build(a.run_dir, a.held, a.project_id)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "MEMBRANE_TABLE.json").write_text(json.dumps(t, indent=1, ensure_ascii=False, default=str) + "\n",
                                             encoding="utf-8")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=MT.CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in MT.csv_rows(t):
        w.writerow(r)
    (out / "MEMBRANE_TABLE.csv").write_text(buf.getvalue(), encoding="utf-8")
    (out / "MEMBRANE_TABLE.md").write_text(MT.markdown(t), encoding="utf-8")
    print(json.dumps({"rows": len(t["rows"]), "held": t["held_count"],
                      "systems": {s["system_id"]: {"separate_upstand_rolls": s[MT.SEPARATE]["rolls_to_buy"],
                                                   "if_alone": s[MT.SEPARATE]["rolls_if_each_area_alone"],
                                                   "continuous_fold_rolls": s[MT.FOLD].get("rolls_to_buy"),
                                                   "fold_complete": s[MT.FOLD].get("complete")}
                                  for s in t["systems"]}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
