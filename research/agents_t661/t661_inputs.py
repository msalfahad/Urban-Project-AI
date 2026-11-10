"""T-661: the URBAN_V3062_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.62 (engine.source.arch_v3062), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t657/out/T657_NECK_LEDGER.json  T-657 (MERGED d96a2958, Verifier 2026-11-09T21:56Z Gate A PASS):
      36 B10-03 neck lines: 32 bounded as drawn (R-T657-1, ST p.9 note 1 .. ST p.13 single-row detail), 4 lift necks
      lower only (D-43, R-T657-2);
  research/agents_t659/out/T659_LEDGER.json       T-659 (MERGED 907ace46, Verifier 2026-11-09T21:54Z Gate A PASS):
      16 small B10 lines: 15 stated exactly as the candidate carries them (CONFIRM) + the boundary band, NOT wired
      (the Checker's cross-trade residual, see WAITING T661_BOUNDARY_BAND);
  research/agents_t660/out/T660_BEAM_LEDGER.json  T-660 (MERGED 9c91709f, Verifier 2026-11-09T23:57Z Gate A PASS):
      27 B10-07 beam lines: 1 valued (Checker re-measure), 5 unlabelled pieces bounded face to face, 8 confirmed,
      12 held blank with the plan area beside (R-T660-3), 1 trial-overlay companion not in the candidate (not wired);
  research/agents_t655/out/LINE_INDEX_V3_0_61.json  T-655 (MERGED bfea3449): the class and held range each line
      carries on the candidate V3.0.61 (the binding; asserted again by the module on the live run).

Typed here are only the RFI question of each held class (the designer items the ledgers name; ERS s.2.7 not met: no
owner question) and the reason a retired bound leaves its line. Every figure comes from a ledger.

    python3 -I research/agents_t661/t661_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T657 = ROOT / "research/agents_t657/out/T657_NECK_LEDGER.json"
T659 = ROOT / "research/agents_t659/out/T659_LEDGER.json"
T660 = ROOT / "research/agents_t660/out/T660_BEAM_LEDGER.json"
INDEX = ROOT / "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
PINS = {T657: "06555295b59345b9febaa47139bff8bebb01cfc43982527613fd7c5f7880cd94",
        T659: "50e51242f4c39bc74ec34f370db67e50297c6bcc18c1038dc3fdeb20797a743f",
        T660: "807dfb5b2da3e9df1be726d377e3aa4121044707d52fa960ba0f94e0c7d561a4",
        INDEX: "10e5f116d30af67f991a233388100c2575c87d9cbd9f8ce464fe78ee0ca1f0ec"}
SOURCES = {
    "T-657": {"task": "T-657", "file": "research/agents_t657/out/T657_NECK_LEDGER.json", "sha256": PINS[T657],
              "merge_commit": "d96a2958c8a72754e930fa04b8449d930450b861",
              "checker_run": "Verifier 2026-11-09T21:56Z (Gate A PASS: ST p.9 / p.13 own read; five necks by hand C11 "
                             "10BA, C3 10CC, C9 10DA, C 10B7, CN 17C5 AGREE)"},
    "T-659": {"task": "T-659", "file": "research/agents_t659/out/T659_LEDGER.json", "sha256": PINS[T659],
              "merge_commit": "907ace4674b91de176419d3fd02628fde6d86b45",
              "checker_run": "Verifier 2026-11-09T21:54Z (Gate A PASS: ST p.7 / p.10 / p.14 own read; band, pad, 2F "
                             "parapet floor AGREE; band cross-trade residual named)"},
    "T-660": {"task": "T-660", "file": "research/agents_t660/out/T660_BEAM_LEDGER.json", "sha256": PINS[T660],
              "merge_commit": "9c91709fc2873b981752c93bed70628e133a59e4",
              "checker_run": "Verifier 2026-11-09T23:57Z (Gate A PASS: own ST7757 dxf re-measure 5 of 5; BM-GF-059 "
                             "0.549624 AGREE; 12 strips HELD BLANK with plan area, never the old envelope)"},
}
SCHEMA = "URBAN_V3062_INPUTS_V1"
NOT_WIRED = {
    "L-6290a9f3d93f38cd46d6": "T661_BOUNDARY_BAND (Checker T-659 residual: band below the building's own plot-line "
                              "G.B not settled; the drawn bound's low end may not be a lower bound)",
}
Q_NECK = ("founding level not printed (ST p.9 note 1 is a minimum 1.50 m below EG; ST p.13 'LESS THAN 2.5m' single-row "
          "detail): print the footing underside level per footing so the neck height is DRAWING-CONFIRMED (designer)")
Q_LIFT = ("D-43 (designer / lift supplier): lift pit raft depth 'as per lift manufacturer' (ST p.14) not printed: the "
          "neck's upper end stays open until the pit depth is printed")
Q_BEAM = {"UNLABELLED": "Q-61 C(4): the unlabelled piece past a support has no mark: which schedule row (breadth 0.20, "
                        "depth 0.40 .. 1.20) governs it (designer)",
          "PROJECTION": "R-T660-3: a strip outside a scheduled beam's face with no mark, bars or printed depth: its "
                        "depth is the architect's parapet / projection detail ('CHECK ARCHITECTURAL DETAIL OF PARAPET, "
                        "BEFORE CASTING'); valued in ONE family only (beam or parapet)",
          "RING": "Q-61 C(3): the east dome ring depth is printed 'AS PER ARCH' (ST p.7 dome detail): the architect's dome "
                  "section is the missing fact"}
WHY_SET_ASIDE = {"NECK_LIFT": "generic T-167 neck height 0.50 .. 2.50 m: no drawn basis for the upper end of a lift "
                              "neck (pit raft depth 'as per lift manufacturer', D-43; R-T657-2)",
                 "PROJECTION": "beam-schedule depth envelope applied to a strip whose depth no sheet prints (T-402 P1; "
                               "R-T660-3): NOT DRAWN, kept beside, never the quantity",
                 "RING": "no drawn depth (R-T660-3)"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T657, T659, T660, INDEX))


def _f(x):
    return None if x in (None, "") else float(Decimal(str(x)))


def _expect(ix):
    lo, hi = ix["held_low"], ix["held_high"]
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": lo, "high": hi}


def _neck(n, ix):
    member = f"neck {n['mark']} at {n['position']} on {n['footing']}"
    e = {"line_id": n["line_id"], "source_tasks": ["T-657"], "member": member, "expect": _expect(ix)}
    if n["status"] == "HELD_BOUNDED_AS_DRAWN":
        return dict(e, action="BOUND", after={"low": _f(n["m3_low"]), "high": _f(n["m3_high"])},
                    basis=f"low: {n['low_basis']}; high: {n['high_basis']}"[:900],
                    why_held="founding level not printed: h between the printed minimum and the single-row detail "
                             "(R-T657-1); a deeper formation is a design change beside (Q-21 C), not in the neck",
                    question=Q_NECK)
    if n["status"] == "HELD_LOWER_ONLY":
        r = dict(e, action="LOWER_ONLY", after={}, basis=f"low: {n['low_basis']}"[:900],
                 why_held="lift neck: upper end open by the pit raft depth (D-43, R-T657-2)", question=Q_LIFT,
                 beside={"kind": "AT_LEAST_M3", "value": _f(n["m3_low"]), "basis": n["low_basis"][:300]})
        if ix["held_low"] is not None:
            r["set_aside"] = {"low": ix["held_low"], "high": ix["held_high"], "why": WHY_SET_ASIDE["NECK_LIFT"]}
        return r
    raise SystemExit(f"{n['line_id']}: neck status {n['status']}")


def _small(r, ix):
    """T-659: every wired line is stated exactly as the candidate carries it (CONFIRM); the band is not wired"""
    lo, hi = _f(r.get("low")), _f(r.get("high"))
    same = (lo is None and ix["held_low"] is None) or (lo is not None and ix["held_low"] is not None and abs(
        lo - ix["held_low"]) <= 1e-6 and abs(hi - ix["held_high"]) <= 1e-6)
    if not same or r.get("value") is not None:
        raise SystemExit(f"{r['line_id']}: T-659 states {lo} .. {hi}, the candidate {ix['held_low']} .. "
                         f"{ix['held_high']}: not a CONFIRM and not listed as not wired")
    return {"action": "CONFIRM", "line_id": r["line_id"], "source_tasks": ["T-659"], "expect": _expect(ix),
            "member": r["element_id"], "basis": f"T-659 {r['status']}: {r.get('item') or r.get('low_basis') or ''}"[:600]}


def _beam(b, ix):
    member = f"beam {b['element_id']} ({b['cls']}, {b['floor']})"
    e = {"line_id": b["line_id"], "source_tasks": ["T-660"], "member": member, "expect": _expect(ix)}
    st = b["status"]
    if st == "VALUED_AS_DRAWN":
        return dict(e, action="VALUE", after={"value": _f(b["m3_value"])}, basis=b["basis"][:900],
                    remeasure="Verifier T-660 own ST7757 dxf re-measure: edges 274 / 277 0.500, column 335 face .. "
                              "end 2A8 1.500, D-D 55 + 20 = 0.75 with the R20 round: 1.500 x (0.500 x 0.75 - 0.20^2 x "
                              "(1 - pi/4)) = 0.549624 m3 AGREE")
    if st == "HELD_BOUNDED_AS_DRAWN":
        lo, hi = _f(b["m3_low"]), _f(b["m3_high"])
        if ix["held_low"] is not None and abs(lo - ix["held_low"]) <= 1e-6 and abs(hi - ix["held_high"]) <= 1e-6:
            return dict(e, action="CONFIRM", basis=b["basis"][:600])
        if b["cls"] != "UNLABELLED":
            raise SystemExit(f"{b['line_id']}: a {b['cls']} bound moves; only the unlabelled pieces restate")
        return dict(e, action="BOUND", after={"low": lo, "high": hi}, basis=b["basis"][:900],
                    why_held="unlabelled piece past a support: breadth-0.20 schedule rows 0.40 .. 1.20 deep x face-to-"
                             "face length (R-T660-2)", question=Q_BEAM["UNLABELLED"])
    if st == "HELD_NO_DRAWN_DEPTH":
        r = dict(e, action="HELD_BLANK", after={}, basis=b["basis"][:900],
                 why_held=(b.get("guard") or "no drawn depth")[:300], question=Q_BEAM[b["cls"]],
                 beside={"kind": "PLAN_AREA_M2", "value": _f(b["plan_area_m2"]),
                         "basis": f"drawn plan {b.get('drawn_width_m')} x {b.get('f2f_length_m')} m face to face "
                                  f"(T-660); no m3 bound"})
        if ix["held_low"] is not None:
            r["set_aside"] = {"low": ix["held_low"], "high": ix["held_high"], "why": WHY_SET_ASIDE[b["cls"]]}
        return r
    raise SystemExit(f"{b['line_id']}: beam status {st}")


def build(project_id=None):
    n657, s659, b660, index = _load()
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.61":
        raise SystemExit(f"index is {index['candidate_version']}")
    ents, not_wired = [], []
    for n in n657["necks"]:
        ents.append(_neck(n, ix[n["line_id"]]))
    for r in s659["rows"]:
        if r["line_id"] in NOT_WIRED:
            not_wired.append({"line_id": r["line_id"], "task": "T-659", "why": NOT_WIRED[r["line_id"]]})
            continue
        ents.append(_small(r, ix[r["line_id"]]))
    for b in b660["beams"]:
        if b["line_id"] not in ix:
            not_wired.append({"line_id": b["line_id"], "task": "T-660", "why": "T661_T642_COMPANION (a trial-BOQ overlay "
                              "line, not a candidate line)"})
            continue
        ents.append(_beam(b, ix[b["line_id"]]))
    _assert_ledger_totals(ents, n657, b660)
    doc = {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
           "not_wired": not_wired, "index_sha256": PINS[INDEX]}
    return doc


def _assert_ledger_totals(ents, n657, b660):
    """the ledgers' own totals reproduce from the entries (exact to 1e-6)"""
    def s(xs):
        return round(sum(xs), 6)
    nk = [e for e in ents if e["source_tasks"] == ["T-657"]]
    bnd = s(e["after"]["low"] for e in nk if e["action"] == "BOUND"), s(e["after"]["high"] for e in nk
                                                                        if e["action"] == "BOUND")
    t = n657["totals"]["bounded_part"]
    assert bnd == (float(t["low_m3"]), float(t["high_m3"])), bnd
    assert s(e["beside"]["value"] for e in nk if e["action"] == "LOWER_ONLY") == float(
        n657["totals"]["lift_lower_only_m3"])
    bm = [e for e in ents if e["source_tasks"] == ["T-660"]]
    a = b660["totals"]["after"]
    assert s(e["after"]["value"] for e in bm if e["action"] == "VALUE") == float(a["valued_m3"])
    assert s(e["beside"]["value"] for e in bm if e["action"] == "HELD_BLANK") == float(
        a["held_no_drawn_depth_plan_m2"])
    assert sum(e["action"] == "HELD_BLANK" for e in bm) == a["held_no_drawn_depth"]


def summary(doc):
    from collections import Counter
    c = Counter((e["source_tasks"][0], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_task_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
