"""ALSENAN PHASE B2A - BENCHMARK EVALUATION, run only AFTER the B2A freeze. Reads the frozen B2A registers and the
frozen B1 difference register (benchmark values as already extracted from the seven hash-pinned files); never
writes anything the engines or the adapter read.

    python3 research/external_engine_lab/alsenan_b2a_evaluation.py <b2a_register_dir> <out_dir>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B1_DIR = ROOT / "tests/alsenan/registers_b1"


def _pct(u, b):
    return round((u - b) / b * 100.0, 4) if isinstance(u, (int, float)) and isinstance(b, (int, float)) and b else None


def evaluate(regdir) -> dict:
    regdir = Path(regdir)
    R = lambda n: json.loads((regdir / f"{n}.json").read_text())
    fz = R("ALSENAN_PHASE_B2A_FREEZE")
    diff = {d["id"]: d for d in json.loads((B1_DIR / "DIFFERENCE_REGISTER.json").read_text())["differences"]}
    bb = R("BEAM_BINDING_REGISTER")["sheets"]
    sv = R("STRUCTURAL_VERTICAL_INTERVAL_REGISTER")
    sl = R("SLAB_REGION_REGISTER")["sheets"]
    pc = R("PHYSICAL_CONCRETE_REGISTER")
    op = R("OPENING_AUTHORITY_REGISTER")
    cu = R("CURVED_OPENING_REGISTER")
    wh = R("WALL_HEIGHT_REGISTER")
    rows = []

    def add(cid, b2a, basis, finding, comparability=None):
        d = diff[cid]
        rows.append({"id": cid, "item": d["item"], "floor": d["floor"], "unit": d["unit"], "bench": d["bench_qty"],
                     "a3_urban": d["urban_qty"], "b2a_urban": b2a, "b2a_basis": basis,
                     "b1_comparability": d["comparability"], "b1_class": d["primary_class"],
                     "b2a_comparability": comparability or d["comparability"],
                     "pct_b2a_vs_bench": _pct(b2a, d["bench_qty"]) if (comparability or d["comparability"]) in
                     ("EXACT_COMPARABLE", "PARTIAL_SCOPE_COMPARABLE") else None, "finding": finding})

    def cb(fl, t):
        o = [x for x in bb[fl]["occurrences"] if x["type"] == t]
        return o[0] if len(o) == 1 else None
    for cid, fl, t in (("CMP-071", "GF", "CB1"), ("CMP-072", "GF", "CB2"), ("CMP-073", "GF", "CB3"), ("CMP-074", "GF", "CB8"),
                       ("CMP-076", "GF", "CB4"), ("CMP-077", "GF", "CB5"), ("CMP-079", "1F", "CB9"), ("CMP-080", "1F", "CB11"),
                       ("CMP-081", "1F", "CB12"), ("CMP-082", "1F", "CB10"), ("CMP-083", "1F", "CB13")):
        o = cb(fl, t)
        if o and o.get("lengths") and o["state"] == "MEASURED":
            L = o["lengths"]
            add(cid, L["PLAN_DRAWN_EXTENT"], f"plan drawn extent (clear {L['CLEAR_FACE_TO_FACE_LENGTH']}, centre line "
                f"{L['SUPPORT_CENTRELINE_LENGTH']}, schedule {L['SCHEDULE_SPAN_LENGTH']}; occurrence {o['state']})",
                "the A3 value was the schedule span sum; B2A publishes the measured bases beside it")
        elif o and o.get("lengths"):
            L = o["lengths"]
            add(cid, L["PLAN_DRAWN_EXTENT"], f"partial run only ({o['state']}: {o.get('tags_vs_spans')})",
                "not compared: the bound run does not cover every scheduled span", "URBAN_BLOCKED")
        else:
            add(cid, None, "no unique bound occurrence (" + ("conflict / unbound" if not o else o["state"]) + ")",
                "still blocked in B2A", "URBAN_BLOCKED")
    o = cb("GF", "B24")
    if o:
        L = o["lengths"]
        add("CMP-084", L["PLAN_DRAWN_EXTENT"], f"drawn {L['PLAN_DRAWN_EXTENT']} / clear {L['CLEAR_FACE_TO_FACE_LENGTH']} / "
            f"centre line {L['SUPPORT_CENTRELINE_LENGTH']}",
            "the source band of B24 is shorter than the manual length on every basis; not a binding defect (the tag is "
            "inside its band)")
    for cid, fl in (("CMP-087", "GF"), ("CMP-089", "1F"), ("CMP-091", "2F")):
        s = sl[fl]
        add(cid, s["volume_m3"], f"net plate {s['net_plate_area_m2']} m2 x t (plate continuous over beams; closure {s['closure']})",
            "basis differs: B2A slab owns the plate over the beams (beams counted as downstand D - t); the manual counts "
            "panels between beams and beams at full D - compare slab + beams below", "SCOPE_MISMATCH")
    tot_slab_beam = {fl: round((sl[fl]["volume_m3"] or 0) + pc["storeys"][fl]["downstand_m3"], 6) for fl in ("GF", "1F", "2F")}
    gross = round(sum(pc["storeys"][fl]["gross_beam_view_m3"] for fl in ("GF", "1F", "2F")), 6)
    add("CMP-085", gross, "GROSS_BEAM view (measured occurrences only, clear length x B x full D)",
        "partial scope: blocked beams excluded; the manual uses drawn lengths x full D", "PARTIAL_SCOPE_COMPARABLE")
    cols = sv["by_storey"]
    add("CMP-070", round(sum(v["volume_m3"] for v in cols.values()), 6),
        f"storey columns computed per controlling member ({sum(v['computed'] for v in cols.values())} occurrences); necks BLOCKED",
        "partial scope (no necks; blocked columns excluded); the manual uses f2f - 0.75 for every column and a 1.5 m neck",
        "PARTIAL_SCOPE_COMPARABLE")
    items = {r["item"]: r for r in pc["explicit_items"]}
    add("CMP-045", items["BLINDING (under computed footings)"]["volume_m3"], "typical detail p.13 under the computed footings only",
        "partial scope: the manual blinding also covers straps / ground beams / slab", "PARTIAL_SCOPE_COMPARABLE")
    sal = op["salon"]
    add("CMP-156", sal.get("height_m"), f"owner-derived 3.65 (provisional); structural soffit bound "
        f"{sal.get('structural_soffit_upper_bound_m')} m under {sal.get('beam_above', {}).get('type')}",
        "the benchmark 4.30 m exceeds the structural soffit bound of the beam over the opening (interval 4.50 - CB1 0.75 = "
        "3.75 above GF FFL, less any 1F build-up): BENCHMARK_EXCEEDS_SOURCE_BOUND unless measured from a lower level")
    g = [r for r in cu["rows"] if r["id"] == "GF-CG01"][0]
    add("CMP-158", g["commercial_m"], f"inner arc (method); centre {g['bases_m']['CENTRE']}, outer {g['bases_m']['OUTER']}",
        "the inner-face method moves the Urban length from the mean arc towards the manual; the manual is still "
        f"{round(g['bases_m']['INNER'] - 6.57, 4) if diff['CMP-158']['bench_qty'] == 6.57 else 'n/a'} m below the inner arc")
    gfw = [r for r in op["rows"] if r["floor"] == "GF" and r["id"] != "GF-W09"]
    add("CMP-161", sum(1 for r in gfw if r["function"] == "WINDOW_CANDIDATE"),
        f"GF straight window candidates; {sum(1 for r in gfw if r['function'] == 'DOOR')} former windows are doors (closure / "
        f"swing), {sum(1 for r in gfw if r['function'].startswith('GLAZED'))} UNKNOWN", "function authority (doors removed by "
        "source evidence) - not tuned to the count")
    for cid, fl in (("CMP-162", "1F"), ("CMP-163", "2F")):
        add(cid, sum(1 for r in op["rows"] if r["floor"] == fl and r["function"] == "WINDOW_CANDIDATE"),
            f"{fl} window candidates", "unchanged function on this floor (no door evidence in the gaps)")
    m = wh["mbr"]
    add("CMP-096", m["floor_area_m2"], f"{m['state']} (wardrobe = fixed joinery, floor continues under it)",
        "now certified; the area is the source site (unchanged) - the remaining difference is the manual's measurement",
        "EXACT_COMPARABLE" if m["floor_area_m2"] is not None else None)
    wet = R("WATERPROOFING_REGISTER")
    wf = round(sum(r["floor_m2"] for r in wet["wet"] if r["state"] == "COMPUTED"), 6)
    add("CMP-145", wf, f"{len(wet['wet'])} certified wet rooms (floor area)", "partial scope: only certified wet rooms",
        "PARTIAL_SCOPE_COMPARABLE")
    return {"SCHEMA": "URBAN_ALSENAN_B2A_BENCHMARK_EVALUATION_V1", "run": "AFTER_FREEZE",
            "b2a_freeze_sha256": hashlib.sha256((regdir / "ALSENAN_PHASE_B2A_FREEZE.json").read_bytes()).hexdigest(),
            "b2a_freeze_benchmark_opened": fz["BENCHMARK_OPENED"],
            "b1_difference_register_sha256": hashlib.sha256((B1_DIR / "DIFFERENCE_REGISTER.json").read_bytes()).hexdigest(),
            "rows": rows, "slab_plus_downstand_m3": tot_slab_beam,
            "rule": "evaluation only: no value here is read by any engine or adapter; no threshold, height, length, count or "
                    "formula was chosen from it"}


def main(regdir, out):
    rec = evaluate(regdir)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "BENCHMARK_EVALUATION.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    for r in rec["rows"]:
        print(r["id"], r["item"][:40], r["a3_urban"], r["b2a_urban"], r["bench"], r["pct_b2a_vs_bench"])
    return rec


if __name__ == "__main__":
    main(*sys.argv[1:3])
