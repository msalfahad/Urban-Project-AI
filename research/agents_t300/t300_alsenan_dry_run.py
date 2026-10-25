"""T-300: Alsenan dry run of the beam reinforcement completeness safeguard (read only; values, marks and drawing handles
only - no coordinates, no client data).

    .work/venv/bin/python -I research/agents_t300/t300_alsenan_dry_run.py <structural DXF> research/agents_t300

Reads the structural DXF with the engine's own intake, runs engine.source.beam_rebar_completeness.evaluate on the beam
schedule rows (BEAM, CONTINUOUS_BEAM), with ONE evidence record: the structural PDF p.8 general note 21 (side bars in
beams deeper than 60 cm, 'unless stated otherwise'; read this run from Drive "Alsenan chalet project" / "ST7757.pdf").
Floors per mark come from route G's own plan binding (generic_route.detect). Route G (URBAN_M8_GENERIC_CONVENTIONS_V6,
no profile) is computed before and after the safeguard in the same process: its item list must be byte-identical.
The flagged list is put beside the merged T-149 hand ledger (research/agents_t149/T149_BEAMS.csv).
Writes T300_ALSENAN_FLAGS.csv (one row per beam component), T300_ALSENAN_SUMMARY.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

NOTE_21 = {"kind": "SIDE_BAR_NOTE", "depth_gt_m": 0.60,
           "source": "structural PDF p.8 general note 21: additional side bars (2 / 3 / 4 Ø12 by beam width) in beams "
                     "deeper than 60 cm unless stated otherwise (width bands not printed)"}
FIELDS = ["mark", "family", "floors", "schedule_sheet", "insert", "depth_m", "component", "span", "status", "basis",
          "reading", "quantity_kg", "quantity_state", "kg_blank_reason", "evidence_ids", "completeness",
          "t149_floors", "t149_reading", "agrees_with_t149"]


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=repr).encode()).hexdigest()


def _route_g(dxf):
    from tools import urban_boq_m2 as M2
    R = M2.compute([dxf], conventions=str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"), route="G")
    items = [{k: v for k, v in it.items()} for it in R["items"]]
    return _sha(items), R["summary"]["steel_t"], sum(float(it.get("base") or 0) for it in R["items"]
                                                      if it.get("unit") == "kg")


def _t149():
    side, nested, corner = defaultdict(set), defaultdict(set), defaultdict(set)
    floors = defaultdict(set)
    for r in csv.DictReader(open(ROOT / "research/agents_t149/T149_BEAMS.csv", encoding="utf-8")):
        mk, comp = r["mark"], r["component"]
        floors[mk].add(r["floor"])
        if comp.startswith("side bars"):
            side[mk].add(comp.replace("side bars ", "").replace("ø", "Ø"))
        m = re.search(r"\((\d+) links", r.get("note") or "")
        if comp.startswith("links") and m and int(m.group(1)) >= 2:
            nested[mk].add(f"{m.group(1)} links")
        if comp == "top corner":
            corner[(mk, r["span"].split("/")[0])].add(f"{r['count']}Ø{r['dia']}")
    return side, nested, corner, floors


def main(dxf: str, out_dir: str) -> None:
    from tools import urban_intake as UI
    from engine.source import drawing_model as DM
    from engine.source import schedule_reader as SR
    from engine.source import generic_route as GR
    from engine.source import beam_rebar_completeness as BRC

    sha_before, steel_before, kg_before = _route_g(dxf)
    I = UI.read_dxf(dxf)
    M = DM.build(I)
    S = SR.from_attribute_rows(I["attributes"], sheet_of=M["sheet_of"])
    segs = [dict(s, sheet=M["sheet_of"](*s["a"])) for s in I["segments"]]
    D = GR.detect(I)
    occ = defaultdict(list)
    for sid, rec in D["sheets"].items():
        for m in rec.get("marks") or []:
            if m.get("state", "").startswith("BOUND") and m.get("family") in BRC.BEAM_FAMILIES:
                occ[(m["family"], m["mark"])].append({"floor": rec["sheet"].get("storey"), "sheet": sid})
    occ = {k: sorted({(v["floor"], v["sheet"]) for v in vs}) for k, vs in occ.items()}
    occ = {k: [{"floor": f, "sheet": s} for f, s in vs] for k, vs in occ.items()}
    res = BRC.evaluate(M["texts"], I["attributes"], segs, S["rows"], evidence=[NOTE_21], occurrences=occ,
                       unit_mass={"method": "D2_OVER_162"})
    sha_after, steel_after, kg_after = _route_g(dxf)

    side, nested, corner, t149_floors = _t149()
    rows = []
    agree = defaultdict(int)
    for b in res["beams"]:
        mk = b["mark"]
        for c in b["components"]:
            t, ok = "", ""
            if c["kind"] == "SIDE_BARS":
                t = ";".join(sorted(side.get(mk, ()))) or "none recorded"
                if c["status"] == "DETECTED":
                    r = c["reading"]
                    got = f"{r['count']}Ø{r['dia_mm']}/{r['spacing']['value']:g}{r['spacing']['unit']}" \
                        if r.get("spacing") else f"{r['count']}Ø{r['dia_mm']}"
                    ok = "YES" if got in side.get(mk, ()) else ("T-149 has no span of this mark" if mk not in
                                                               t149_floors else "NO")
                else:
                    ok = "YES" if not side.get(mk) else "NO"
            elif c["kind"] == "NESTED_LINKS":
                t = ";".join(sorted(nested[mk])) if nested.get(mk) else "no nested link recorded"
                if c["status"] == "DETECTED":
                    ok = "YES" if nested.get(mk) else ("T-149 has no span of this mark" if mk not in t149_floors
                                                       else "NO")
                elif c["status"] == "NOT_REQUIRED":
                    ok = "YES" if not nested.get(mk) else "NO"
                else:
                    ok = "T-149 silent (single-link path used)" if not nested.get(mk) else "NO"
            else:
                if c["span"] is not None:
                    t = ";".join(sorted(corner.get((mk, str(c["span"])), ()))) or "no corner bar recorded"
                    if c["status"] == "DETECTED":
                        got = f"{c['reading']['count']}Ø{c['reading']['dia_mm']}"
                        ok = "YES" if got in corner.get((mk, str(c["span"])), ()) else \
                            ("T-149 has no span of this mark" if mk not in t149_floors else "NO")
                    else:
                        ok = "YES (both: nothing printed)" if not corner.get((mk, str(c["span"]))) else "NO"
                else:
                    t, ok = "top = schedule TOP bars", "YES" if c["status"] == "NOT_REQUIRED" else "NO"
            agree[(c["kind"], ok.split(" ")[0])] += 1
            ids = [i for ev in c["evidence"] for i in (ev.get("ids") or ev.get("loop_ids") or [])
                   if isinstance(ev, dict)]
            rows.append({"mark": mk, "family": b["family"],
                         "floors": ";".join(f"{f['floor']}" for f in b["floors"]),
                         "schedule_sheet": b["schedule"]["sheet"], "insert": b["schedule"]["insert"],
                         "depth_m": b["schedule"]["depth_m"], "component": c["kind"],
                         "span": "" if c["span"] is None else c["span"], "status": c["status"], "basis": c["basis"],
                         "reading": json.dumps(c["reading"], sort_keys=True, ensure_ascii=False) if c["reading"] else "",
                         "quantity_kg": "" if c["quantity_kg"] is None else repr(c["quantity_kg"]),
                         "quantity_state": c["quantity_state"], "kg_blank_reason": c["kg_blank_reason"] or "",
                         "evidence_ids": ";".join(str(i) for i in ids), "completeness": b["completeness"],
                         "t149_floors": ";".join(sorted(t149_floors.get(mk, ()))),
                         "t149_reading": t, "agrees_with_t149": ok})
        for f in b["flags"]:
            rows.append({"mark": mk, "family": b["family"], "floors": ";".join(f"{x['floor']}" for x in b["floors"]),
                         "schedule_sheet": b["schedule"]["sheet"], "insert": b["schedule"]["insert"],
                         "depth_m": b["schedule"]["depth_m"], "component": "FLAG " + f["code"], "span": "",
                         "status": "FLAGGED", "basis": f.get("reason") or f.get("slot") or "",
                         "reading": f.get("text") or "", "quantity_kg": "", "quantity_state": "HELD",
                         "kg_blank_reason": "unclassified drawing text: never a quantity",
                         "evidence_ids": ";".join(str(i) for i in f.get("ids") or []),
                         "completeness": b["completeness"],
                         "t149_floors": ";".join(sorted(t149_floors.get(mk, ()))), "t149_reading": "",
                         "agrees_with_t149": ""})
    out = Path(out_dir)
    with open(out / "T300_ALSENAN_FLAGS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    meta = {"dxf_sha256_8": hashlib.sha256(Path(dxf).read_bytes()).hexdigest()[:8],
            "route_g_items_sha256_before": sha_before, "route_g_items_sha256_after": sha_after,
            "route_g_byte_identical": sha_before == sha_after,
            "route_g_steel_t": {k: repr(float(v)) for k, v in steel_before.items()},
            "route_g_kg_items_base_before": repr(kg_before), "route_g_kg_items_base_after": repr(kg_after),
            "measured_digest": res["measured_digest"], "summary": res["summary"],
            "unassigned": [{k: v for k, v in u.items() if k in ("kind", "text", "state", "ids", "loop_ids")}
                           for u in res["unassigned"]],
            "association_rules": sorted({json.dumps(b["association"], sort_keys=True) for b in res["beams"]}),
            "agreement_with_t149": {f"{k[0]}|{k[1]}": v for k, v in sorted(agree.items())},
            "evidence": [NOTE_21]}
    (out / "T300_ALSENAN_SUMMARY.json").write_text(json.dumps(meta, indent=1, sort_keys=True, ensure_ascii=False)
                                                   + "\n", encoding="utf-8")
    print(json.dumps({"route_g_byte_identical": meta["route_g_byte_identical"], **res["summary"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
