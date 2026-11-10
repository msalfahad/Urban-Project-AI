"""T-665: the URBAN_V3063_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.63 (engine.source.arch_v3063), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t658/out/T658_LEDGER.json         T-658 r2 (MERGED 2cec1520, Verifier 2026-11-10T02:10Z Gate A PASS):
      61 B10 lines: 29 STR.CONC.GROUND_BEAM (9 bounded, 16 lower only, 4 blank), 29 STR.CONC.COLUMN (15 bounded,
      6 upper only, 8 blank), 2 STR.CONC.STRAP, 1 STR.CONC.FOOTING;
  research/agents_t595/out/T595_RESTATEMENTS.json   T-595 (MERGED 568ce15e, Verifier 2026-11-07T09:56Z Gate A PASS):
      the F10 + F footing line's scenario-set bound 1.960 .. 2.275 m3 (R-T595-2, owner 2026-11-02 RFI re-review (4)).
      The T-658 ledger states this line 'UNCHANGED' because its 'before' was read on the trial-BOQ r4 overlay, which
      already carries the T-595 bound; the CANDIDATE still carries the T-572 bound 2.176 .. 2.275. The line is wired
      from T-595 (its source), with T-658 as the ledger that restates it (lesson T-661: bind to the candidate);
  research/agents_t661/out/LINE_INDEX_V3_0_62.json  T-661 (Gate B PASS, MERGED ea1533e4, published 7a9ccbff): the class
      and held range each line carries on the candidate V3.0.62 (the binding; asserted again on the live run).

Every figure comes from a ledger; typed here are only the RFI question of each held class (the designer items the
ledgers name; ERS s.2.7 not met: no owner question), the reason a retired bound leaves its line and the datum
provenance of the column ceilings (T-658 READS R2_MARKS_REREAD, Checker-confirmed).

    python3 -I research/agents_t665/t665_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T658 = ROOT / "research/agents_t658/out/T658_LEDGER.json"
T595 = ROOT / "research/agents_t595/out/T595_RESTATEMENTS.json"
INDEX = ROOT / "research/agents_t661/out/LINE_INDEX_V3_0_62.json"
DGS = ROOT / "research/agents_t469/DOWNGRADES_SNAPSHOT.json"
PINS = {DGS: "817326399e5b9ffff1d727b9599dff46d1f917c930e759c37e1d5721f0f85766",T658: "6c4d96731f79ebb2a11e7d2d15ff93f0ac0a14d8a87779518fac26471a61e94d",
        T595: "80d32d7051ee9926201b252d761d20ca1c4609465eb992a67583cbbeb1567964",
        INDEX: "858eba3baca2e19450c8b78888ced615e8e68b34f0486717c1dd71e6b35a93df"}
SOURCES = {
    "T-658": {"task": "T-658", "file": "research/agents_t658/out/T658_LEDGER.json", "sha256": PINS[T658],
              "merge_commit": "2cec1520cd977957dc4760e02a98fe090df7970b",
              "checker_run": "Verifier 2026-11-10T02:10Z (Gate A PASS r2: own ST7757 dxf polygons BAND0038 / 0039 / "
                             "0037.1 / 0008.2 / 0040 AGREE; D-33 floors re-added 2.841866 AGREE; +9.65 / +0.25 not "
                             "printed AGREE, ceilings valid on either base; GB totals re-added AGREE)"},
    "T-595": {"task": "T-595", "file": "research/agents_t595/out/T595_RESTATEMENTS.json", "sha256": PINS[T595],
              "merge_commit": "568ce15eeaf548307d4e0db9b7596527db1626f1",
              "checker_run": "Verifier 2026-11-07T09:56Z (Gate A PASS: R-T595-2 3-scenario footing fixture, missing "
                             "scenario never 0; F10 + F 2.176 .. 2.275 -> 1.960 .. 2.275 m3)"},
}
SCHEMA = "URBAN_V3063_INPUTS_V1"
FOOTING_LINE = "L-164ae9d338976be9e582"
Q_GB = {"TITLES": "D-34: ST p.13 prints three ground-beam titles by span ('less than 2.5m' 30x30, 'less than 5m' 30x40, "
                  "'more than 5m' 30x60) with no precedence: which title governs a span that two titles hold "
                  "(designer)",
        "D-33": "D-33: ST p.13 prints ground-beam sections only 'without concentrated load': the section of a run that "
                "carries a landing / framing beam is not printed (designer)",
        "D-35": "D-35: the annex exterior ground-beam depth: the literal +0.25 .. N.G. reading cannot hold the printed "
                "exterior section (designer)"}
Q_COL = "D-39 / Q-54 B: the roof slab-top structural datum and the roof build-up are not printed: the column's lower " \
        "end (top of the slab it stands on / height to the soffit) stays open (designer)"
Q_FTG = "R-T595-2 / owner 2026-11-02 RFI re-review (4): whether F10 and F act as one footing or F10 alone governs the " \
        "S02 outline (designer); scenario set kept, never a picked end"
WHY_SET_ASIDE = {"D-33": "a run carrying a landing / framing beam: the unloaded ST p.13 titles are a floor, never a high "
                         "(R-T658-8, D-33; Checker T-658 r2 (h) ACCEPTED)",
                 "TITLES": "the old point sat at one end of the titles that hold (R-T658-1)"}
COL_RE = re.compile(r"\((\d+\.\d+) finished mark.*?- (\d+\.\d+) base, APPROVED structural datum")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T658, T595, INDEX, DGS))


def _f(x):
    return None if x in (None, "") else float(Decimal(str(x)))


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def _same(lo, hi, ix):
    if lo is None and hi is None:
        return ix["held_low"] is None and ix["held_high"] is None
    return ix["held_low"] is not None and lo is not None and hi is not None and abs(lo - ix["held_low"]) <= 1e-6 \
        and abs(hi - ix["held_high"]) <= 1e-6


def _member(r):
    return f"{r['item_code'].split('.')[-1].lower().replace('_', ' ')} {r['element_id']}"


def _gb_question(r):
    fl = r.get("flags") or []
    if "D-33_LOADED_SPAN" in fl:
        return Q_GB["D-33"]
    if "D-35_ANNEX" in fl:
        return Q_GB["D-35"]
    return Q_GB["TITLES"]


def _column_datums(r):
    m = COL_RE.search(r["basis"])
    if not m:
        raise SystemExit(f"{r['line_id']}: an upper-only ceiling without its two marks")
    top, base = m.group(1), m.group(2)
    return [{"kind": "PRINTED", "what": f"+{top} finished mark (arch sheet 10 section / sheet 9 elevation, re-read "
                                        f"r2, Checker AGREE)"},
            {"kind": "APPROVED_DATUM", "what": f"+{base} structural base = printed finished level - 0.05 (facts "
                                               f"register DESIGNER datum, NOT printed text; Checker: the ceiling stays "
                                               f"a valid upper bound on either base)"}]


def _applied(index, dgs):
    """{line_id: downgrade record} of the Checker downgrades the V3.0.62 index marks APPLIED (they hold released
    candidate lines at export; the index carries those lines as HELD at their record range)"""
    ok = {d["downgrade_id"] for d in index["downgrades"] if d.get("status") == "APPLIED"}
    out = {}
    for d in dgs["downgrades"] if isinstance(dgs, dict) else dgs:
        if d["downgrade_id"] in ok:
            for i in d["line_ids"]:
                out[i] = d
    return out


def _dg(d):
    return {"downgrade_id": d["downgrade_id"], "verdict_commit": d["checker"]["verdict_commit"],
            "checker_run": f"{d['checker']['routine']} {d['checker']['run_token']} ({d['time']})",
            "file": "research/agents_t469/DOWNGRADES_SNAPSHOT.json", "sha256": PINS[DGS],
            "line_ids": list(d["line_ids"]), "line_content_sha256": d["line_content_sha256"],
            "engine_qty": d["engine_qty"], "reason": d["reason"][:300]}


def _row(r, ix, dg=None):
    lo, hi = _f(r["low"]), _f(r["high"])
    st = r["status"]
    e = {"line_id": r["line_id"], "source_tasks": ["T-658"], "member": _member(r), "expect": _expect(ix)}
    if r["line_id"] == FOOTING_LINE:
        return None                                           # wired from T-595 below
    if dg is not None:
        # a released candidate line held at export by an APPLIED Checker downgrade: materialised (R-T665-1 (g))
        if r["item_code"] != "STR.CONC.GROUND_BEAM" or ix["class"] != "HELD" or ix["held_low"] is None:
            raise SystemExit(f"{r['line_id']}: downgrade {dg['downgrade_id']} on a line the index does not hold bounded")
        e["expect"] = dict(e["expect"], **{"class": "RELEASED"})
        e["downgrade"] = _dg(dg)
        if st == "BOUNDED" and _same(lo, hi, ix):
            return dict(e, action="BOUND", after={"low": lo, "high": hi}, basis=r["basis"][:900],
                        why_held="UNCHANGED range (T-658); the Checker downgrade that holds this line at export is "
                                 "materialised in the line, because its neighbours under the same downgrade change",
                        question=_gb_question(r), flags=r["flags"])
    if st in ("BOUNDED", "HELD_BLANK") and _same(lo, hi, ix):
        return dict(e, action="CONFIRM", basis=(r["basis"] or r["item"] or "")[:600])
    if st == "BOUNDED":
        if r["item_code"] != "STR.CONC.GROUND_BEAM":
            raise SystemExit(f"{r['line_id']}: a {r['item_code']} bound moves; the ledger restates ground beams only")
        return dict(e, action="BOUND", after={"low": lo, "high": hi}, basis=r["basis"][:900],
                    why_held="the titles that hold (D-34) / the drawn outline area (R-T658-7): bounded, not a value",
                    question=_gb_question(r), flags=r["flags"])
    if st == "LOWER_ONLY":
        out = dict(e, action="LOWER_ONLY", after={}, basis=r["basis"][:900], why_held=r["item"][:300],
                   question=_gb_question(r), flags=r["flags"],
                   beside={"kind": "AT_LEAST_M3", "value": lo, "basis": r["basis"][:300]})
        if ix["held_low"] is not None:
            out["set_aside"] = {"low": ix["held_low"], "high": ix["held_high"], "why": WHY_SET_ASIDE["D-33"]}
        return out
    if st == "UPPER_ONLY":
        if ix["held_low"] is not None:
            raise SystemExit(f"{r['line_id']}: an upper-only ceiling would retire a candidate bound")
        return dict(e, action="UPPER_ONLY", after={}, basis=r["basis"][:900], why_held=r["item"][:300],
                    question=Q_COL, flags=r["flags"],
                    beside={"kind": "AT_MOST_M3", "value": hi, "basis": r["basis"][:300],
                            "datums": _column_datums(r)})
    raise SystemExit(f"{r['line_id']}: {st} {lo} .. {hi} is neither the candidate's state nor a restatement")


def _footing(t595, ix):
    c = t595["footing"]["component"]
    assert c["line_id"] == FOOTING_LINE and c["kind"] == "BOUNDED", c
    return {"action": "BOUND", "line_id": FOOTING_LINE, "source_tasks": ["T-595", "T-658"],
            "member": f"footing {c['element_id']} (F10 + F, S02)", "expect": _expect(ix),
            "after": {"low": _f(c["low"]), "high": _f(c["high"])},
            "basis": f"low: {c['low_basis']}; high: {c['high_basis']}; scenarios {c['scenarios']}; "
                     f"{c['status_label']}"[:900],
            "why_held": "S02 scenario set (R-T595-2): F10 alone .. drawn outline; the governing scenario is a designer "
                        "item, the range is carried, never a picked end",
            "question": Q_FTG}


def build(project_id=None):
    t658, t595, index, dgs = _load()
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.62":
        raise SystemExit(f"index is {index['candidate_version']}")
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    held_by = _applied(index, dgs)
    ents = []
    for r in t658["rows"]:
        e = _row(r, ix[r["line_id"]], held_by.get(r["line_id"]))
        if e is not None:
            ents.append(e)
    ents.append(_footing(t595, ix[FOOTING_LINE]))
    _assert_ledger_totals(ents, t658)
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "not_wired": [], "index_sha256": PINS[INDEX]}


def _assert_ledger_totals(ents, t658):
    """the ledger's own per-code totals reproduce from the entries + the candidate binding of CONFIRM lines"""
    def s(xs):
        return round(sum(xs), 6)
    for code, t in t658["totals"].items():
        es = [e for e in ents if e["expect"]["item_code"] == code]
        assert len(es) == t["lines"], (code, len(es))
        bl, bh, nb, nl, nu, nblank, fl, cl = [], [], 0, 0, 0, 0, [], []
        for e in es:
            a = e["action"]
            if a == "BOUND" or (a == "CONFIRM" and e["expect"]["low"] is not None):
                lo, hi = (e["after"]["low"], e["after"]["high"]) if a == "BOUND" else (e["expect"]["low"],
                                                                                        e["expect"]["high"])
                if e["line_id"] == FOOTING_LINE:          # the ledger states the T-595 bound (r4 overlay)
                    lo, hi = e["after"]["low"], e["after"]["high"]
                bl.append(lo), bh.append(hi)
                nb += 1
            elif a == "LOWER_ONLY":
                nl += 1
                fl.append(e["beside"]["value"])
            elif a == "UPPER_ONLY":
                nu += 1
                cl.append(e["beside"]["value"])
            else:
                nblank += 1
        got = (nb, s(bl), s(bh), nl, s(fl), nu, s(cl), nblank)
        want = (t["bounded"], float(t["bounded_low"]), float(t["bounded_high"]), t["lower_only"],
                float(t["lower_only_floor"]), t["upper_only"], float(t["upper_only_ceiling"]), t["blank"])
        assert got == want, (code, got, want)


def summary(doc):
    from collections import Counter
    c = Counter((e["expect"]["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
