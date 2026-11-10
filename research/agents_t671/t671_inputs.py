"""T-671: the URBAN_V3065_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.65 (engine.source.arch_v3065), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t669/out/T669_LEDGER.json   T-669 (MERGED 8cb64551, Verifier 2026-11-10 09:56Z Gate A PASS): part
      (b) R-T669-2: the 5 2F roof-column lines get their drawn lower ends (0.303 .. 0.425 m3 x 4, 0.4242 .. 0.595 m3),
      HELD BOUNDED under D-39; the annex C3 line has no printed lower end (refused by name): CONFIRM, unchanged;
  research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json  T-647 (MERGED a521da8a, Verifier 2026-11-09 06:56 Gate A
      PASS; CN plan level Checker-confirmed 2026-11-09 01:54): FR-T647-1 .. 5, the 5 CN column lines above the neck:
      ST p.9 schedule row CN struck on GF / 1F / 2F, CN on no slab or roof plan: NOT_APPLICABLE_WITH_EVIDENCE;
  research/agents_t642/out/T642_FIX_ROWS.json  T-642 (MERGED 1c7411a5, Verifier 2026-11-08T21:54Z Gate A PASS, own
      re-measure of the strip by handle): FR-T642-2, GF BAND0030.2 strip north of the column: 0.20 x 0.50 = 0.100
      m2 x B4 0.50 = 0.050 m3 released low end + companion HELD 0 .. 0.025 (B7 0.75 alternative, R-T619-1 (c));
  research/agents_t668/out/LINE_INDEX_V3_0_64.json  T-668 (Gate B PASS, MERGED 033b52b9): the class and range each
      line carries on the candidate V3.0.64 (the binding; asserted again on the live run).

Typed here are only the RFI question of each held class (the designer items the ledgers name; ERS s.2.7 not met: no
owner question) and the reasons. Every line id is read from the line index by its full id (T-668 lesson: a prefix
alone is refused unless the member agrees).

    python3 -I research/agents_t671/t671_inputs.py [project_id]      # prints the inputs summary
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

T669 = ROOT / "research/agents_t669/out/T669_LEDGER.json"
T647 = ROOT / "research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json"
T642 = ROOT / "research/agents_t642/out/T642_FIX_ROWS.json"
INDEX = ROOT / "research/agents_t668/out/LINE_INDEX_V3_0_64.json"
PINS = {T669: "e3f2dd96b133de85ee2bae7b9bb2667dce6a478bcf3e707746f9851ec828ef3a",
        T647: "610c67b00aab02008db78c30f2056b685e3917a6135071c64b6affb5b3ef0d66",
        T642: "5ce2188f8862d7ab449e8bc89f7ef5c8b8b4ea23bdd7040df0c73860159f028d",
        INDEX: "4403697305f428b11c754e95af5258207d7ce3663fe7de1d687b5e2e5d879548"}
SOURCES = {
    "T-669": {"task": "T-669", "file": "research/agents_t669/out/T669_LEDGER.json", "sha256": PINS[T669],
              "merge_commit": "8cb64551ce8b27223a9fa9c5fd20f67974d3609a",
              "checker_run": "Verifier 2026-11-10 09:56Z (Gate A PASS: own ST7757 dxf / sheet 10 reads: one 2F roof "
                             "slab, T 18 the only thickness, W26 apex +12.50; 5 2F column lows 1.6362 .. 2.295 m3 "
                             "AGREE; annex C3 low refused AGREE; F-C-T669-1 9 column outlines in the 2F slab, not 8)"},
    "T-647": {"task": "T-647", "file": "research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json", "sha256": PINS[T647],
              "merge_commit": "a521da8a2c15c9d70fff109313b3dc176f386e03",
              "checker_run": "Verifier 2026-11-09 06:56 (Gate A PASS on r2 30d8a19e; FR-T647-1 .. 5 CN NOT_APPLICABLE "
                             "by the 01:54 verdict: ST7757.pdf p.9 row CN 'FOUNDATION 30 30 4 o14', one ruled line "
                             "through the GF / 1st / 2nd floor cells; ST dxf: 12 CN texts, none on a GF / 1F / 2F slab "
                             "or roof plan: CHECKER-CONFIRMED)"},
    "T-642": {"task": "T-642", "file": "research/agents_t642/out/T642_FIX_ROWS.json", "sha256": PINS[T642],
              "merge_commit": "1c7411a5144f60d028874d2f1bbee22e8d654973",
              "checker_run": "Verifier 2026-11-08T21:54Z (Gate A PASS: own ST7757 dxf re-measure by handle, faces "
                             "2B2 / 2B3 to the closing line 484: 0.20 x 0.50 = 0.100 m2; FR-T642-2 0.050 SET + HELD "
                             "0 .. 0.025 per R-T619-1 AGREE)"},
}
SCHEMA = "URBAN_V3065_INPUTS_V1"
ANNEX_C3 = "L-fad18af6e7139a5e99d1"
STRIP = "L-efd3f7806bf10b6a8e98"
Q_D39 = ("D-39: the 2F roof slab-top level / build-up is not printed: the column height lies inside 3.03 m (W26 apex "
         "+12.50 + printed T 18 - 9.65 base) .. 4.25 m (13.90 finished - 9.65) (designer)")
Q_STRIP = ("FR-T642-2: no mark is printed on the GF strip north of the column: B4 (its face entities, 0.50 deep) or "
           "the B7 arc lead-in (0.75 deep); a section through the annex corner settles it (designer)")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T669, T647, T642, INDEX))


def _f(x):
    return None if x in (None, "") else float(Decimal(str(x)))


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def _full(ix, prefix, member):
    """the one candidate line whose id starts with the ledger's short id AND whose element carries the member's
    type and storey (refused otherwise: a prefix alone is not a binding)"""
    hits = [ln for lid, ln in ix.items() if lid.startswith(prefix)]
    typ, storey = member.split(" ")[0], member.split(" ")[1]
    if len(hits) != 1:
        raise SystemExit(f"{prefix}: {len(hits)} candidate lines")
    el = hits[0]["element_id"]
    if f":{typ}@" not in el or not el.endswith(f"|{storey}"):
        raise SystemExit(f"{prefix}: element {el} is not the ledger's member {member}")
    return hits[0]


def _column(r, ix):
    ln = _full(ix, r["line"], r["member"])
    if ln["class"] != "HELD" or ln["held_low"] is not None or ln["item_code"] != "STR.CONC.COLUMN":
        raise SystemExit(f"{ln['line_id']}: {ln} is not the blank upper-only column the ledger read")
    sec, (h0, h1) = _f(r["section_m2"]), (_f(x) for x in r["height_m"])
    lo, hi = _f(r["low_m3"]), _f(r["high_m3"])
    if abs(sec * h0 - lo) > 1e-9 or abs(sec * h1 - hi) > 1e-9:
        raise SystemExit(f"{ln['line_id']}: {lo} .. {hi} is not {sec} m2 x {h0} .. {h1} m")
    return {"action": "BOUND", "line_id": ln["line_id"], "source_tasks": ["T-669"],
            "member": f"column {r['member']} (roof storey)", "expect": _expect(ln), "after": {"low": lo, "high": hi},
            "basis": (f"{r['section_m2']} m2 x {r['height_m'][0]} .. {r['height_m'][1]} m; low: {r['low_basis']}; "
                      f"high: {r['high_basis']}")[:900],
            "why_held": f"{r['still_open']} (R-T669-2: the drawings fix the lower end only)",
            "question": Q_D39}


def _annex(r, ix):
    ln = ix[ANNEX_C3]
    if not ANNEX_C3.startswith(r["line"]) or r["low_m3"] is not None or ln["class"] != "HELD" or \
            ln["held_low"] is not None:
        raise SystemExit(f"annex C3: ledger {r} / candidate {ln}")
    return {"action": "CONFIRM", "line_id": ANNEX_C3, "source_tasks": ["T-669"], "member": f"column {r['member']}",
            "expect": _expect(ln), "basis": f"no lower end printed: {r['why_no_low']}"[:900]}


def _cn(fr, rec, ix):
    ln = ix[fr["line_id"]]
    if rec["line_id"] != fr["line_id"] or ":CN@" not in ln["element_id"] or ln["item_code"] != "STR.CONC.COLUMN" or \
            ln["class"] != "HELD" or fr["proposed_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or not fr["inputs_printed"]:
        raise SystemExit(f"{fr['id']}: {fr} / {ln}")
    if (rec["held_low"], rec["held_high"]) != (ln["held_low"], ln["held_high"]):
        raise SystemExit(f"{fr['id']}: census bound {rec['held_low']} .. {rec['held_high']} is not the candidate's "
                         f"{ln['held_low']} .. {ln['held_high']}")
    e = {"action": "NOT_APPLICABLE", "line_id": ln["line_id"], "source_tasks": ["T-647"],
         "member": "column CN above the neck (GF / 1F / 2F)", "expect": _expect(ln),
         "basis": f"{fr['id']}: {fr['hand_calculation']}"[:900],
         "evidence": {"status": "DRAWING-CONFIRMED",
                      "drawing": "Drive 'Alsenan chalet project' / 'ST7757.pdf' p.9 and 'ST7757 dxf.dxf' (schedule "
                                 "segment, slab / roof plans)",
                      "reading": "Schedule of Columns row CN 'FOUNDATION 30 30 4 o14' with the GF, 1st and 2nd floor "
                                 "cells struck; CN drawn on no GF / 1F / 2F slab or roof plan (the 5 column-plan tags "
                                 "are setting-out of the foundation size); the CN neck below GF stays on its 6 neck "
                                 "lines",
                      "checker_run": SOURCES["T-647"]["checker_run"], "fix_row": fr["id"],
                      "verdict_proposal": fr["verdict_proposal"]}}
    if ln["held_low"] is not None:
        e["set_aside"] = {"low": ln["held_low"], "high": ln["held_high"],
                          "why": "0.09 m2 x 4.2 .. 12.9 m above-GF column heights for a member the schedule prints as "
                                 "absent above the neck (TYPE_NOT_IN_SCHEDULE of the frozen reader)"}
    return e


def _strip(t642, ix):
    fr = next(r for r in t642["fix_rows"] if r["id"] == "FR-T642-2")
    ln = ix[STRIP]
    if fr["line_id"] != STRIP or ln["class"] != "HELD" or (ln["held_low"], ln["held_high"]) != (0.04, 0.12):
        raise SystemExit(f"FR-T642-2: {fr} / {ln}")
    v, c = _f(fr["change_m3"]), fr["companion"]
    lo, hi = (_f(x) for x in c["held_m3"])
    if abs(0.20 * 0.50 * 0.50 - v) > 1e-9 or lo != 0.0 or abs(0.20 * 0.50 * (0.75 - 0.50) - hi) > 1e-9:
        raise SystemExit("FR-T642-2: 0.050 + 0 .. 0.025 is not 0.100 m2 x B4 0.50 .. B7 0.75")
    val = {"action": "VALUE", "line_id": STRIP, "source_tasks": ["T-642"],
           "member": "GF beam strip BAND0030.2 (route G piece north of the column, mark B4)", "expect": _expect(ln),
           "after": {"value": v},
           "basis": "faces 2B2 / 2B3 to the closing line 484: 0.20 x 0.50 = 0.100 m2 x B4 0.50 (its face entities, "
                    "route G mark) = 0.050 m3, the drawn low end of the old 0.04 .. 0.12 range (R-T619-1 (c))",
           "remeasure": "Verifier 2026-11-08T21:54Z own ST7757 dxf faces by handle: 0.100 m2 x 0.50 = 0.050 AGREE"}
    comp = {"action": "ADD_COMPANION", "key": "BAND0030.2-DEPTH", "source_tasks": ["T-642"], "companion_of": STRIP,
            "template_line": STRIP,
            "add": {"item_code": "STR.CONC.BEAM", "unit": "m3", "element_id": c["element"], "floor": "GF",
                    "physical_element": "depth remainder of the GF strip north of the column if it is the B7 arc "
                                        "lead-in (0.75) and not B4 (0.50)"},
            "after": {"low": lo, "high": hi},
            "basis": "0.100 m2 x (B7 0.75 - B4 0.50) = 0.025 m3 (FR-T642-2 companion)",
            "why_held": c["cause"], "question": Q_STRIP}
    return [val, comp]


def build(project_id=None):
    t669, t647, t642, index = _load()
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.64":
        raise SystemExit(f"index is {index['candidate_version']}")
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    rows = t669["b_roof_columns"]["rows"]
    cols = [_column(r, ix) for r in rows if r["low_m3"] is not None]
    lo, hi = round(sum(e["after"]["low"] for e in cols), 6), round(sum(e["after"]["high"] for e in cols), 6)
    b = t669["b_roof_columns"]
    if len(cols) != 5 or (lo, hi) != (_f(b["five_2f_low_m3"]), _f(b["five_2f_high_m3"])):
        raise SystemExit(f"2F columns: {len(cols)} lines {lo} .. {hi} is not the ledger's 5 lines")
    ents = cols + [_annex(r, ix) for r in rows if r["low_m3"] is None]
    recs = {r["line_id"]: r for r in t647["records"]}
    frs = [r for r in t647["fix_rows"] if r["id"] in {f"FR-T647-{i}" for i in range(1, 6)}]
    if len(frs) != 5:
        raise SystemExit(f"T-647: {len(frs)} CN fix rows")
    ents += [_cn(fr, recs[fr["line_id"]], ix) for fr in frs]
    ents += _strip(t642, ix)
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "index_sha256": PINS[INDEX],
            "not_wired": [
                {"what": "T-674 the 5 B10-05 ground-slab lines (T-180 P18 drawing-only fix)", "task": "T-674",
                 "why": "not MERGED at hand-in: the lines keep their V3.0.64 state"},
                {"what": "2F C2 at the tank, 2F C3, 2F C5 blank column lines (T-669 'MEASURABLE NOW' list)",
                 "task": "T-669", "why": "no merged ledger states their lower ends (section conflict D-66): unchanged"},
                {"what": "annex C3 column lower end", "task": "T-669", "why": "R-T669-2 refused (no printed opening "
                 "top, slab thickness or slab-top level on the annex): CONFIRM, low open by name"}]}


def summary(doc):
    from collections import Counter
    c = Counter((e.get("expect", e.get("add"))["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
