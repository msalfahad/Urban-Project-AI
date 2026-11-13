"""T-677: the URBAN_V3066_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.66 (engine.source.arch_v3066), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t673/out/T673_LEDGER.json   T-673 (MERGED 15d03afc, Verifier 2026-11-10 14:03 UTC Gate A PASS): the
      16 MEASURABLE NOW STR.CONC.LINTEL lines (14 heads drawn on merged T-201 / T-238 reads, R-T673-1; 2 T-650
      bounds) HELD BOUNDED at R-T673-3, 0.925 .. 1.493412 m3 on their lines + the W19 / W20 shared pier remainder
      0 .. 0.003 on ONE new line (R-T677-1 (o)) = the ledger's family 0.925 .. 1.496412; ST-03 E1 steps part
      0.355017 m3 DRAWING-CONFIRMED beside its HELD waist (S-9): LOWER_ONLY, blank;
  research/agents_t674/summary_t674.json  T-674 (MERGED bb4ec90b, Verifier 2026-11-10T16:0xZ Gate A PASS, own
      polygonisation): the 5 B10-05 ground-slab lines re-derived from the drawn panels: 3 REVALUE (-0.009 /
      +0.010559 / +0.000868 m3), the court pair CONFIRM; the 0.090 m2 end triangles of the oblique beam BAND0038 move
      slab -> beam in the same inputs (both or neither, Checker 16:00);
  research/agents_t658/out/T658_BAND_AREAS.json  T-658 (MERGED 2cec1520, Verifier 2026-11-10T02:10Z Gate A PASS r2):
      the two outline readings of BAND0038 (AS_DRAWN 0.310134 m2, EXTENDED to the carriers 0.326694 m2) its V3.0.63
      bound 0.310134 x 0.30 .. 0.326694 x 0.40 rests on; T-674 + its Checker fix the strip at 0.326694 (C1: the beam
      runs to its carriers' faces), so the low reading 0.310134 leaves and the bound becomes 0.326694 x 0.30 .. 0.40;
  research/agents_t671/out/LINE_INDEX_V3_0_65.json  T-671 (Gate B PASS, MERGED 271ba60f): the class and range each
      line carries on the candidate V3.0.65 (the binding; asserted again on the live run).

Typed here are only the RFI question of each held class (the designer items the ledgers name; ERS s.2.7 not met: no
owner question) and the reasons. Every line id is the ledger's full id, bound to the index by id AND element.

    python3 -I research/agents_t677/t677_inputs.py [project_id]      # prints the inputs summary
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

T673 = ROOT / "research/agents_t673/out/T673_LEDGER.json"
T674 = ROOT / "research/agents_t674/summary_t674.json"
T658 = ROOT / "research/agents_t658/out/T658_BAND_AREAS.json"
INDEX = ROOT / "research/agents_t671/out/LINE_INDEX_V3_0_65.json"
PINS = {T673: "fc0939bf1b1c6f524726015710c3dcdb271f353f5a2a8a475132c0d93023b410",
        T674: "0f162475b0436af25f9dbc124e40f64dfd0466b47e14a3ac1c92b7edd2c70ac7",
        T658: "e9e3871a9ae7a50bfb389623b365ba068b1197315957fbdbfca738429ce2e93a",
        INDEX: "e1887c34362b9d2f6558eab7bf825be958ee87206403995abef42be62a335ce1"}
SOURCES = {
    "T-673": {"task": "T-673", "file": "research/agents_t673/out/T673_LEDGER.json", "sha256": PINS[T673],
              "merge_commit": "15d03afc4d918a12c1fe0da6891c25a2a3447ec7",
              "checker_run": "Verifier 2026-11-10 14:03 UTC (Gate A PASS, run session_01E6cPneJTqxSgACrB8dHgik: "
                             "census 49 = V3.0.64 index; own W16 P7757.dxf read 0.078 .. 0.081732 AGREE; W24 sheet 09 "
                             "0.094 .. 0.268280 AGREE; ST-03 E1 ST p.3 5 x 1/2 x 0.30 x 0.17 x 2.80 = 0.357 AGREE; "
                             "nothing VERIFIED, existence DRAWING-CONFIRMED)"},
    "T-674": {"task": "T-674", "file": "research/agents_t674/summary_t674.json", "sha256": PINS[T674],
              "merge_commit": "bb4ec90b98cc263e2be17c5467368c15e9a3098b",
              "checker_run": "Verifier 2026-11-10T16:0xZ (Gate A PASS, run session_01E6cPneC95WJNrb9QgLWXnA: own "
                             "polygonisation, 1 mm snap, finer arc chords: L-69527cb9 strip to the carriers 0.326696 "
                             "m2 -> 0.350768 AGREE; L-8b681fda 2.721160 AGREE; L-f192ff5f 2.253380 AGREE; court pair "
                             "10.905276 / 2.050207 m2 ENGINE_RIGHT; five lines own 2.143771 vs 2.143747 m3, +0.000024 "
                             "arc flattening named; the 0.090 m2 moves slab -> GB BAND0038, both or neither)"},
    "T-658": {"task": "T-658", "file": "research/agents_t658/out/T658_BAND_AREAS.json", "sha256": PINS[T658],
              "merge_commit": "2cec1520cd977957dc4760e02a98fe090df7970b",
              "checker_run": "Verifier 2026-11-10T02:10Z (Gate A PASS r2: own ST7757 dxf polygons BAND0038 / 0039 / "
                             "0037.1 / 0008.2 / 0040 AGREE)"},
}
SCHEMA = "URBAN_V3066_INPUTS_V1"
ST03 = "L-061e18cf35a4b6b33d68"
GB38 = "L-970bac563cbcd69e2a30"
SLAB_CUT = "L-69527cb9affdad474268"
SEC_RE = re.compile(r"L\d (\d+(?:\.\d+)?) x (\d+(?:\.\d+)?)\)$")
Q_LINTEL = ("T-516 RFI / ST p.13: the lintel end bearings are not dimensioned (MIN 40 cm printed; the drawn jamb "
            "distances are the ceilings) and a deficit end at a column or cross wall has no printed connection; the "
            "heads are drawn, not printed (N09 'not to scale') (designer)")
Q_PIER = ("R-T673-3: which of the two lintels runs over the pier remainder between them (pier minus both 0.40 "
          "bearings) is not drawn (designer)")
Q_ST03 = ("S-9: the ST-03 entrance flight E1 waist slab (thickness / soffit) is not drawn; riser 0.170 confirmation "
          "D-56 (designer)")
Q_GB = ("D-34: ST p.13 prints three ground-beam titles by span with no precedence; the oblique BAND0038 (span 0.789 m) "
        "is held by 30x30 and 30x40 alike: which title governs (designer)")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T673, T674, T658, INDEX))


def _f(x):
    return None if x in (None, "") else float(Decimal(str(x)))


def _d(x):
    return Decimal(str(x))


def _q6(x):
    return float(Decimal(x).quantize(Decimal("0.000001")))


def _expect(ix):
    x = {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
         "low": ix["held_low"], "high": ix["held_high"]}
    if ix["class"] == "RELEASED":
        x = dict(x, value=ix["measured_net"])
        x.pop("low"), x.pop("high")
    return x


def _lintel(r, ix):
    ln = ix.get(r["line_id"])
    if ln is None or ln["item_code"] != "STR.CONC.LINTEL" or ln["class"] != "HELD" or ln["held_low"] is not None:
        raise SystemExit(f"{r['line_id']}: {ln} is not a blank HELD lintel line")
    if ln["element_id"] != f"LINTEL:{r['opening']}":
        raise SystemExit(f"{r['line_id']}: element {ln['element_id']} is not the ledger's opening {r['opening']}")
    m = SEC_RE.search(r["member"])
    if not m:
        raise SystemExit(f"{r['line_id']}: no schedule section in {r['member']!r}")
    bd = _d(m.group(1)) * _d(m.group(2))
    lo, hi = _d(r["low_m3"]), _d(r["high_m3"])
    if r.get("length_m"):                                     # R-T673-3: B x D x (w + 0.80) .. B x D x (w + ceilings)
        l0, l1 = (_d(x) for x in r["length_m"])
        if bd * l0 != lo or bd * l1 != hi:
            raise SystemExit(f"{r['line_id']}: {lo} .. {hi} is not {bd} m2 x {l0} .. {l1} m")
        basis = (f"{m.group(1)} x {m.group(2)} (ST p.13 band) x {r['length_m'][0]} .. {r['length_m'][1]} m "
                 f"(opening + 0.40 bearing each side .. the drawn jamb ceilings, {r['convention']}); ends "
                 + "; ".join(f"{e['side']} {e['a']} {e['state']}" for e in r["ends"]) + f"; {r['existence']}")
    else:
        if "T-650" not in r["cause_ref"]:
            raise SystemExit(f"{r['line_id']}: no length and no merged T-650 bound")
        basis = f"{m.group(1)} x {m.group(2)} (ST p.13 band): {r['cause_ref']}; {r['existence']}"
    return {"action": "BOUND", "line_id": ln["line_id"], "source_tasks": ["T-673"], "member": r["member"],
            "expect": _expect(ln), "after": {"low": float(lo), "high": float(hi)}, "basis": basis[:900],
            "why_held": f"{r['status']}; {r.get('why') or r['cause_ref']}"[:600], "question": Q_LINTEL}


def _pier(p, lint):
    by = {e["member"].split(" ")[1]: e for e in lint}
    a, b = p["pair"]
    if a not in by or b not in by or _f(p["lo_m3"]) != 0.0:
        raise SystemExit(f"pier remainder {p}: its sharers are not bounded lintels here")
    pier = _d(p["pier_m"])
    rem = pier - 2 * _d("0.40")
    sec = SEC_RE.search(by[a]["member"])
    hi = _d(sec.group(1)) * _d(sec.group(2)) * rem
    if hi != _d(p["hi_m3"]):
        raise SystemExit(f"pier remainder: {p['hi_m3']} is not B x D x ({pier} - 0.80) = {hi}")
    return {"action": "ADD_SHARED", "key": f"PIER-{a}-{b}", "source_tasks": ["T-673"],
            "shared_by": [by[a]["line_id"], by[b]["line_id"]], "template_line": by[a]["line_id"],
            "add": {"item_code": "STR.CONC.LINTEL", "unit": "m3", "element_id": f"LINTEL:{a}+{b}:PIER_REMAINDER",
                    "floor": None, "physical_element": f"lintel concrete over the {p['pier_m']} m pier between {a} and "
                                                      f"{b} beyond both 0.40 bearings (owned by one of the two)"},
            "after": {"low": 0.0, "high": float(hi)},
            "basis": f"{sec.group(1)} x {sec.group(2)} x ({p['pier_m']} - 2 x 0.40) = {p['hi_m3']} m3 ({p['why']})",
            "why_held": "the pier remainder belongs to one of the two lintels, which one not drawn; neither sharer's "
                        "high carries it (R-T677-1 (o))", "question": Q_PIER}


def _st03(s, ix):
    ln = ix[ST03]
    if s["line_id"] != ST03 or ln["class"] != "HELD" or ln["held_low"] is not None or s["high_m3"] is not None:
        raise SystemExit(f"ST-03: ledger {s} / candidate {ln}")
    hand = Decimal(5) * Decimal("0.5") * _d("0.30") * _d("0.17") * _d("2.80") - _d("0.001983")
    if hand != _d(s["low_m3"]):
        raise SystemExit(f"ST-03: {s['low_m3']} is not 5 x 1/2 x 0.30 x 0.17 x 2.80 - 0.001983 = {hand}")
    return {"action": "LOWER_ONLY", "line_id": ST03, "source_tasks": ["T-673"], "member": s["member"],
            "expect": _expect(ln), "basis": f"{s['hand']}; {s['cause_ref']}"[:900],
            "beside": {"kind": "AT_LEAST_M3", "value": float(hand),
                       "basis": "ST-03 E1 steps part DRAWING-CONFIRMED (5 drawn risers, T-258): " + s["hand"]},
            "why_held": "the waist S-9 is not drawn: the flight is at least its steps part, its total stays open "
                        "(owner 2026-10-22: the staircase system is never VERIFIED)", "question": Q_ST03}


REMEASURE = {"L-69527cb9affdad474268": "strip to the carriers own 0.326696 m2 (worker 0.326694): 3.834377 - 0.326694 "
                                       "= 3.507683 m2 x 0.10 = 0.350768 AGREE",
             "L-8b681fdaa3b3910b2b7b": "own face 2.721160 m2 (edge on the drawn lift-ring face) x 0.10 = 0.272116 AGREE",
             "L-f192ff5f4962efa8d08f": "own face 2.253380 m2 x 0.10 = 0.225338 AGREE",
             "L-1031c9be9aaae364fef4": "own panel 10.905276 m2 (engine 10.905052, +0.0002 arc chords): ENGINE_RIGHT",
             "L-5e881fd31885949d4e66": "own panel 2.050207 m2 (engine 2.050202): ENGINE_RIGHT"}
WHY = {"L-69527cb9affdad474268": "R-T674-1: the oblique ground beam BAND0038 (drawn faces 180 / 181, 0.300 apart; 181 "
                                 "drafted 0.078 m short of carrier face 180D) owns its strip to both carriers' faces "
                                 "(C1, T-282 closure): the square-cut deduction 0.236694 left two end triangles "
                                 "0.090 m2 in the slab",
       "L-8b681fdaa3b3910b2b7b": "R-T674-3: route G's junction box (lift corner, NO_LINE) crossed the drawn lift ring "
                                 "face: 0.105587 m2 returned to the panel",
       "L-f192ff5f4962efa8d08f": "R-T674-3: the same junction box took a 0.0282 m strip along the ring's top face: "
                                 "0.008684 m2 returned"}


def _slab(lid, row, t, ix):
    ln = ix[lid]
    if ln["item_code"] != "STR.CONC.GROUND_SLAB" or ln["class"] != "RELEASED" or \
            ln["element_id"] != f"P-C:GROUND_SLAB:GROUND:{row['cell']}" or \
            abs(ln["measured_net"] - row["candidate_m3"]) > 1e-9:
        raise SystemExit(f"{lid}: ledger {row} / candidate {ln}")
    m2 = _d(row["corrected_m2"])
    if _q6(m2 * _d(t)) != row["corrected_m3"]:
        raise SystemExit(f"{lid}: {row['corrected_m2']} m2 x {t} is not {row['corrected_m3']}")
    base = {"line_id": lid, "source_tasks": ["T-674"], "member": f"ground slab panel {row['cell']} (T {t})",
            "expect": _expect(ln)}
    if row["delta_m3"] == 0:
        return dict(base, action="CONFIRM", basis=f"re-derived {row['corrected_m2']} m2 x {t} = {row['corrected_m3']} "
                    f"m3 = the candidate (own face {row['own_face_m2']} m2; split on the drawn beam, ends on the "
                    f"true arc)")
    d = _q6(_d(row["corrected_m3"]) - _d(row["candidate_m3"]))
    if d != row["delta_m3"]:
        raise SystemExit(f"{lid}: delta {row['delta_m3']} is not {d}")
    e = dict(base, action="REVALUE", after={"value": row["corrected_m3"]}, delta=d,
             basis=f"{WHY[lid]}; panel {row['corrected_m2']} m2 x {t} = {row['corrected_m3']} m3 (was "
                   f"{row['candidate_m3']})", remeasure=f"Verifier 2026-11-10T16:0xZ own polygonisation: {REMEASURE[lid]}")
    if lid == SLAB_CUT:
        tri = _q6(_d(row["strip_to_carriers_m2"]) - _d(row["deduction_m2"]))
        e["moves_to"] = {"line_id": GB38, "plan_m2": tri,
                         "why": "the two end triangles of the oblique beam strip (C1: the beam owns its strip to its "
                                "carriers' faces); the beam line's plan is that strip"}
    return e


def _band0038(row, areas, ix):
    ln = ix[GB38]
    runs = areas["runs"]
    a0, a1 = runs["BAND0038:AS_DRAWN"]["area_m2"], runs["BAND0038:EXTENDED"]["area_m2"]
    if ln["class"] != "HELD" or ln["element_id"] != "P-C:GROUND_BEAMS:GROUND:BAND0038" or \
            (ln["held_low"], ln["held_high"]) != (_q6(_d(a0) * _d("0.30")), _q6(_d(a1) * _d("0.40"))):
        raise SystemExit(f"BAND0038: candidate {ln} is not {a0} x 0.30 .. {a1} x 0.40")
    if a1 != row["strip_to_carriers_m2"]:
        raise SystemExit(f"BAND0038: EXTENDED {a1} is not the T-674 strip {row['strip_to_carriers_m2']}")
    lo, hi = _q6(_d(a1) * _d("0.30")), _q6(_d(a1) * _d("0.40"))
    return {"action": "BOUND", "line_id": GB38, "source_tasks": ["T-674", "T-658"],
            "member": "ground beam BAND0038 (oblique, 0.30 wide, between its two carriers)", "expect": _expect(ln),
            "after": {"low": lo, "high": hi},
            "basis": (f"plan = the strip to both carriers' faces {a1} m2 (T-658 EXTENDED reading = T-674 R-T674-1, "
                      f"Checker 0.326696); the AS_DRAWN reading {a0} m2 (stopping at face 181's drafted end) leaves: "
                      f"a beam does not stop short of its carrier (C1). x the titles that hold 0.30 .. 0.40 (D-34) = "
                      f"{lo} .. {hi} m3; the slab's 0.090 m2 end triangles are inside this plan, once"),
            "why_held": "depth: two ST p.13 titles hold the span (D-34); the plan is now one drawn figure",
            "question": Q_GB}


def build(project_id=None):
    t673, t674, t658, index = _load()
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.65":
        raise SystemExit(f"index is {index['candidate_version']}")
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    lint = [_lintel(r, ix) for r in t673["lintels"] if r["cause"] == "MEASURABLE NOW"]
    tot = t673["totals_m3"]["lintel_measurable_now"]
    if len(lint) != tot["lines"]:
        raise SystemExit(f"lintels: {len(lint)} is not the ledger's {tot['lines']}")
    piers = [_pier(p, lint) for p in t673["pier_remainders"]]
    lo = sum(_d(e["after"]["low"]) for e in lint) + sum(_d(e["after"]["low"]) for e in piers)
    hi = sum(_d(str(e["after"]["high"])) for e in lint) + sum(_d(str(e["after"]["high"])) for e in piers)
    if (lo, hi) != (_d(tot["low"]), _d(tot["high"])):
        raise SystemExit(f"lintels: {lo} .. {hi} is not the ledger's family {tot['low']} .. {tot['high']}")
    st = [s for s in t673["stairs"] if s["cause"] == "MEASURABLE NOW"]
    if [s["line_id"] for s in st] != [ST03]:
        raise SystemExit(f"stairs MEASURABLE NOW: {[s['line_id'] for s in st]}")
    ents = lint + piers + [_st03(st[0], ix)]
    t = t674["t_m"]
    slabs = [_slab(lid, row, t, ix) for lid, row in sorted(t674["lines"].items())]
    fl = t674["five_lines"]
    if len(slabs) != 5 or _q6(sum(_d(r["corrected_m3"]) for r in t674["lines"].values())) != fl["corrected_m3"]:
        raise SystemExit("T-674: five lines do not add to the ledger's corrected total")
    ents += slabs + [_band0038(t674["lines"][SLAB_CUT], t658, ix)]
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "index_sha256": PINS[INDEX],
            "not_wired": [
                {"what": "28 STR.CONC.LINTEL lines (6 DESIGNER ITEM, 22 OPEN BOUND by the T-673 census)",
                 "task": "T-673", "why": "no drawn quantity: they keep their V3.0.65 state (blank, never 0)"},
                {"what": "4 STR.CONC.STAIR lines (ST-01 remainder, ST-01 MS2 turn riser, ST-02 curved remainder, "
                         "ST-01b waist)", "task": "T-673", "why": "DESIGNER ITEM: unchanged (the ST-01 remainder's "
                                                                  "1.213429 .. 1.434413 census bound is not wired: "
                                                                  "a CONFLICT component, never releasable)"},
                {"what": "route G junction face at the lift corner (0.7112 m2 after the 0.114271 m2 returned)",
                 "task": "T-674", "why": "NO_LINE (lift ring, shaft, beam ends BAND0008.1 / BAND0003): named"},
                {"what": "R-T674-1 / -3 as slab / junction method changes", "task": "T-674",
                 "why": "proposals: route G and the released default unchanged; only the named lines move"}]}


def summary(doc):
    from collections import Counter
    c = Counter((e.get("expect", e.get("add"))["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
