"""T-566 development-villa run (research, unwired): GF column MARK REGISTRATION per position from the drawings alone
(R-T566-1 .. 4), its effect on the T-551 column component split, and the B10-07 beam UNTRACED residual -0.365289 m3 of
T-545 named per mark (R-T566-5).

    .work/venv/bin/python -I research/agents_t566/t566_alsenan.py [--freelancer .work/private/concrete_rebar.xlsx
        --bands .work/private/t566/bands.json] [--write]

Committed inputs only for the registration: POSITION_INPUT_T566.json (this task's own read of 'ST7757 dxf.dxf', see
t566_extract.py), the V3.0.57 line index (= V3.0.58 for columns and beams, R-T507-1 (e)), the T-394 per-line member
handles (to name the line of each drawn member; the MARK of T-394 is compared, never used), T-205's FP binding (compared
only). With --freelancer the T-551 column tables are re-split under every CONFLICT reading and the beam row checks are
re-run (his rows stay in memory; the tracked output carries engine figures and m3 terms only).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t566_rules as R  # noqa: E402

INPUT = HERE / "POSITION_INPUT_T566.json"
OUT = HERE / "out" / "T566_REGISTRATION.json"
T205 = RES / "agents_t205" / "ALSENAN_NECK_INPUT.json"
T394 = RES / "agents_t394" / "summary_t394.json"
T545 = RES / "agents_t545" / "out" / "T545_BEAM_RECONCILE.json"
LABEL_SHEETS = ("FP", "CAP", "GBP")
BAND_OF = {"FOUNDATION": "FOU", "GF": "GR", "1F": "1ST", "2F": "2ND"}
STOREY_OF_SHEET = {"GFRS": "GF", "FFRS": "1F", "SFRS": "2F"}


def load_input():
    return json.loads(INPUT.read_text(encoding="utf-8"))


def member_lines():
    """{('GF', 'GFRS:350'): line_id, ...} from the T-394 per-line records (handles only)."""
    out = {}
    for r in json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]:
        m = r.get("member") or ""
        if ":" in m and m.split(":")[0] in STOREY_OF_SHEET:
            out[(r["storey"], m)] = r["line_id"]
    return out


def line_class():
    d = json.loads((RES / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json").read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return {x["line_id"]: x for x in d["lines"] if x["item_code"] == "STR.CONC.COLUMN"}


def registration(inp=None):
    inp = inp or load_input()
    sched = {k: v["bands"] for k, v in inp["schedule"].items()}
    t205 = {n["outline_handle"]: n["type"] for n in json.loads(T205.read_text(encoding="utf-8"))["necks"]}
    ml, lc = member_lines(), line_class()
    rows = []
    for p in inp["positions"]:
        labs = {s: ({"text": p["labels"][s]["text"], "kind": "PRINTED_LABEL"} if s in p["labels"] else None)
                for s in LABEL_SHEETS}
        # a sheet that draws no outline at the position is not a missing label: it is left out of the support count
        drawn_on = p.get("drawn_on", {})
        labs = {s: v for s, v in labs.items() if s in drawn_on}
        reg = R.register_position(labs)
        cands = list(reg["candidates"]) or []
        drawn = {"FOUNDATION": p["neck_drawn_mm"]}
        for st in ("GF", "1F", "2F"):
            mem = p["members"].get(st)
            drawn[st] = mem["section_mm"] if mem else None
        vec = R.section_vector({m: {st: sched[m][BAND_OF[st]] for st in drawn} for m in cands}, drawn, unit="mm")
        txt = p.get("size_text_cm")
        txt_vec = None
        if txt:
            txt_vec = R.section_vector({m: {"FOUNDATION": sched[m]["FOU"]} for m in cands},
                                       {"FOUNDATION": (txt["W"], txt["D"])}, unit="cm")
        mems = {}
        for st in ("GF", "1F", "2F"):
            mem = p["members"].get(st)
            if not mem:
                continue
            lid = ml.get((st, f"{mem['sheet']}:{mem['handle']}"))
            mems[st] = {"handle": f"{mem['sheet']}:{mem['handle']}", "section_mm": mem["section_mm"],
                        "line_id": lid, "line_class": lc[lid]["class"] if lid in lc else None}
        rows.append({"position": p["position"], "labels": {s: p["labels"][s]["text"] + " (" + p["labels"][s]["handle"] + ")"
                                                         for s in p["labels"]},
                     "class": reg["class"], "mark": reg["mark"], "candidates": reg["candidates"],
                     "support": reg["support"], "merged_T205_mark": t205.get(p["position"]),
                     "neck_drawn_mm": p["neck_drawn_mm"],
                     "size_text_cm": [txt["W"], txt["D"]] if txt else None,
                     "section_vs_schedule": {m: {**vec[m], **({"FOU_size_text": txt_vec[m]["FOUNDATION"]} if txt_vec else {})}
                                             for m in cands},
                     "members": mems,
                     "carries": R.continuity(reg["mark"] or "|".join(cands), mems)})
    return rows


def gf_counts(rows):
    reg = Counter(r["mark"] for r in rows if r["class"] == "REGISTERED" and "GF" in r["members"])
    conf = [r for r in rows if r["class"] == "CONFLICT" and "GF" in r["members"]]
    return {"registered": dict(sorted(reg.items())),
            "conflict_positions": [{"position": r["position"], "candidates": r["candidates"],
                                    "gf_line": r["members"]["GF"]["line_id"],
                                    "gf_line_class": r["members"]["GF"]["line_class"]} for r in conf]}


def conflict_bounds(rows, inp=None):
    inp = inp or load_input()
    sched = {k: v["bands"] for k, v in inp["schedule"].items()}
    out = []
    for r in rows:
        if r["class"] != "CONFLICT":
            continue
        for st, mem in r["members"].items():
            b = R.conflict_area_bound({m: sched[m] for m in r["candidates"]}, BAND_OF[st],
                                      tuple(Decimal(v) / 1000 for v in mem["section_mm"]))
            out.append({"position": r["position"], "storey": st, "line_id": mem["line_id"],
                        "line_class": mem["line_class"], **{k: (str(v) if isinstance(v, Decimal) else v)
                                                            for k, v in b.items()}})
    return out


# ------------------------------------------------------------------------------------------------ T-551 re-split
def t551_resplit(freelancer, rows):
    """The T-551 GF / 1F column component split under every combination of CONFLICT readings (m3 terms only)."""
    sys.path.insert(0, str(RES / "agents_t551"))
    import itertools
    import t551_alsenan as A
    his, _ = A.his_rows(freelancer)
    base = A.column_lines()
    conf = [r for r in rows if r["class"] == "CONFLICT"]
    choices = [[(r["position"], m) for m in r["candidates"]] for r in conf]
    lid_pos = {mem["line_id"]: r["position"] for r in conf for mem in r["members"].values()}
    out = []
    for combo in itertools.product(*choices):
        pick = dict(combo)
        cols = [dict(c, mark=pick[lid_pos[c["line_id"]]]) if c["line_id"] in lid_pos else dict(c) for c in base]
        tbl, det, _ = A.columns_by_storey(cols, his)
        per = {}
        for st in ("GF", "1F"):
            comps = {k: v["m3"] for k, v in tbl[st]["components"].items()}
            marks = {d["mark"]: {k: v for k, v in d.items() if k not in ("storey", "mark", "engine_m3")}
                     for d in det if d["storey"] == st}
            per[st] = {"residual_m3": tbl[st]["residual_m3"], "components": comps,
                       "by_mark": {m: v for m, v in sorted(marks.items()) if v}}
        out.append({"reading": {p: m for p, m in combo}, "tables": per})
    return out


# ------------------------------------------------------------------------------------------------ beams (R-T566-5)
# Evidence read this run (bands from research/agents_t110/scripts/bands.py on route G, T-545 run objects; his rows in
# memory only). Drawn lengths are the band pieces / line values; his lengths are never written to the tracked file.
BEAM_NAMED = [
    ("GF", "B11", "DRAWING_PRECISION", "ENGINE_RIGHT",
     "one row of his against one drawn run (BAND0001); the row and the drawn line differ by < 0.05 m"),
    ("GF", "B8", "DRAWING_PRECISION", "ENGINE_RIGHT",
     "one row of his against one drawn run (BAND0003, drawn 0.200 x 3.52014, T-392); difference < 0.05 m"),
    ("1F", "B11", "DRAWING_PRECISION", "ENGINE_RIGHT",
     "one row of his against one drawn run (BAND0004); difference < 0.05 m"),
    ("1F", "B6", "DRAWING_PRECISION", "ENGINE_RIGHT",
     "his one row bound to run BAND0021 by the T-395 run binding; difference < 0.05 m"),
    ("2F", "B2", "COUNT", "ENGINE_RIGHT (proposal; Checker re-counts the 2F B2 labels)",
     "his rows equal the four drawn face-to-face B2 runs (BAND0003 2.499, BAND0005 3.000, BAND0007.1 1.800, "
     "BAND0007.2 3.000) run by run, plus one more row of the 2.5 m run: no fifth drawn B2 run, and every 2F B2 end "
     "frames into a perpendicular beam (no collinear continuation). The mark residual -0.200 is that one row: "
     "UNTRACED -0.08724 + the T-545 THROUGH_SUPPORT -0.11276 of this mark (his lengths are face to face here)"),
    ("GF", "B2", "MARK_BOUNDARY", "ENGINE_RIGHT (drawn labels)",
     "BAND0020.2 (B2) continues collinearly through column 36B (gap 0.498 m) into BAND0020.1 (0.200 x 0.803 m) which "
     "the drawing labels B1 and the engine bills once under B1 (L-c254e0d17c22fcae49fe); his B2 excess beyond the B2 "
     "support allowance (0.139 m) fits inside that B1 piece; GF B1 carries a RUN_COUNT term of its own (T-545)"),
    ("1F", "CB12", "BEYOND_EXTENT", "ENGINE_RIGHT (proposal)",
     "drawn CB12 = BAND0018.1 5.626 + gap over 664 0.899 + BAND0018.2 5.025, end supports 69D 0.20 and 676 0.25: outer-"
     "face extent 12.00 m; his one row is longer than that extent; no collinear beam continues CB12 at either end "
     "(B6 BAND0021 and B4 BAND0015 are perpendicular; BM-1F-036 BAND0025 lies beside BAND0018.2, sharing its long "
     "face, not beyond its end). Schedule spans 6.1 / 5.5 c/c (T-110) are also shorter than his row"),
    ("GF", "B7", "UNRESOLVED", "UNRESOLVED (named)",
     "his two B7 rows; the longer has no location on his sheet (T-252 / T-392 s.3); drawn B7 = three straight runs "
     "(BAND0025.1, BAND0049, BAND0006) + the void ring RING-B7 0.499805 m3 measured between its own drawn edges "
     "(T-392); his total exceeds the drawn B7 outer-face extent incl. the ring by 0.80 m at 0.20 x 0.75"),
]


def beam_named():
    t = json.loads(T545.read_text(encoding="utf-8"))
    by = {(m["floor"], m["mark"]): m for m in t["marks"]}
    named = []
    for fl, mk, cause, verdict, ev in BEAM_NAMED:
        u = Decimal(by[(fl, mk)].get("UNTRACED", "0"))
        rec = R.name_untraced(f"{fl} {mk}", u, cause, verdict, ev)
        if cause == "COUNT":
            ts = Decimal(by[(fl, mk)].get("THROUGH_SUPPORT", "0"))
            rec["reclassed_from_THROUGH_SUPPORT_m3"] = str(R.d6(ts))
            rec["mark_residual_m3"] = str(R.d6(u + ts))
        named.append(rec)
    total = Decimal(t["total"]["components"]["UNTRACED"]["m3"])
    close = R.close_named(total, named)
    return {"untraced_total_m3": str(R.d6(total)), "named": named, "closure": close}


def beam_row_checks(freelancer, bands):
    """Private re-run of the row-to-run evidence behind BEAM_NAMED (returns booleans and drawn figures only)."""
    sys.path.insert(0, str(RES / "agents_t545"))
    import t545_alsenan as A
    runs, marks, his, *_ = A.run_build(freelancer, bands)
    rows = defaultdict(list)
    for r in his:
        rows[(r["floor"], r["mark"])].extend([Decimal(str(r["L"]))] * int(r["n"]))
    runL = defaultdict(list)
    for r in runs:
        if r["status"] == "VALUED" and r.get("L"):
            runL[(r["floor"], r["mark"])].append(Decimal(str(r["L"])))
    mk = {(m["floor"], m["mark"]): m for m in marks}
    res = {}
    for fl, m in (("GF", "B11"), ("GF", "B8"), ("1F", "B11")):
        eng_L = Decimal(str(mk[(fl, m)]["split"]["L_engine_valued"]))
        res[f"{fl} {m}"] = len(rows[(fl, m)]) == 1 and R.precision_class(rows[(fl, m)][0], eng_L)
    b6 = mk[("1F", "B6")]["split"]
    bound = [Decimal(str(r["L"])) for r in runs if "1F:BAND0021" in r["pieces"]]          # T-395 run binding of his row
    res["1F B6"] = len(bound) == 1 and R.precision_class(b6["L_his"], bound[0])
    his_b2, drawn_b2 = sorted(rows[("2F", "B2")]), sorted(runL[("2F", "B2")])
    extra = list(his_b2)
    for L in drawn_b2:
        hit = [x for x in extra if abs(x - L) < Decimal("0.005")]
        if not hit:
            extra = None
            break
        extra.remove(hit[0])
    res["2F B2 runs equal f2f, one extra row"] = extra is not None and len(extra) == 1
    res["2F B2 extra row x section = mark residual"] = bool(extra) and R.d6(
        extra[0] * Decimal("0.2") * Decimal("0.4")) == R.d6(-Decimal(str(mk[("2F", "B2")]["split"]["residual"])))
    return res


def build(freelancer=None, bands=None):
    inp = load_input()
    rows = registration(inp)
    doc = {"schema": "T566_REGISTRATION_V1",
           "candidate": "ARCH_TAKEOFF_V3.0.58 (column / beam lines = V3.0.57 LINE_INDEX, R-T507-1 (e)); NOT RELEASED",
           "source": inp["source_file"], "binding": inp["binding"],
           "positions": rows, "gf_counts": gf_counts(rows), "conflict_bounds": conflict_bounds(rows, inp),
           "agreement_with_merged_T205": {
               "positions": len(rows),
               "fp_label_equal": sum(1 for r in rows if "FP" in r["labels"] and
                                     r["labels"]["FP"].split(" ")[0].split("/")[0] == r["merged_T205_mark"]),
               "registered_equal": sum(1 for r in rows if r["class"] == "REGISTERED" and r["mark"] == r["merged_T205_mark"]),
               "conflict_here": [r["position"] for r in rows if r["class"] == "CONFLICT"]},
           "slab_frame_mark_like_texts": inp["slab_frame_mark_like_texts"],
           "beam_untraced": beam_named(),
           "note": "engine figures, drawing handles and m3 terms only; no row, length or count of the freelancer"}
    if freelancer:
        doc["t551_resplit"] = t551_resplit(freelancer, rows)
        if bands:
            doc["beam_row_checks_private_run"] = beam_row_checks(freelancer, bands)
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer")
    ap.add_argument("--bands")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build(a.freelancer, a.bands)
    for r in doc["positions"]:
        print(r["position"], r["class"], r["mark"] or r["candidates"], r["support"], r["merged_T205_mark"],
              {k: v["line_class"] for k, v in r["members"].items()})
    print(json.dumps({k: doc[k] for k in doc if k not in ("positions",)}, indent=1, ensure_ascii=False)[:9000])
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("->", OUT)


if __name__ == "__main__":
    main()
