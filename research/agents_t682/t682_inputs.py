"""T-682: the URBAN_V3067_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.67 (engine.source.arch_v3067), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t678/out/T678_LEDGER.json   T-678 (MERGED f8515d4b, Verifier 2026-11-10T17:58Z Gate A PASS): the 9
      MEASURABLE NOW STR.CONC.LINTEL lines (existence REQUIRED on a soffit LOWER bound, R-T678-1): 7 bounded both
      ends, 2 with one end OPEN (R-T678-3: lower end only, blank); the planted column PC-2F (outline 778) 0.1824 ..
      0.350 m3; the annex roof column C3 0.41175 .. 0.50625 m3 on the annex slab-top lower bound (R-T678-2);
  research/agents_t677/out/LINE_INDEX_V3_0_66.json  T-677 (Gate B PASS, MERGED 8a28bce5): the class and range each
      line carries on the candidate V3.0.66 c411617d (the binding; asserted again on the live run).

Every bound is re-derived here by hand from the ledger's own fields (opening width, schedule section, end distances,
convention; section x height) and refused when it differs. The Checker's challenges are carried as records:
F-V678-1 (existence on the owner door-height fallback Q-55 C: ASSUMED - OWNER-APPROVED with its re-run trigger) and
F-V678-2 (the annex slab-top bound is transferred only through R-T682-1: one plane in plan AND in the section read).
Typed here are only the RFI questions (designer items the ledger names; ERS s.2.7 not met: no owner question).

    python3 -I research/agents_t682/t682_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t682_rules as R82  # noqa: E402

T678 = ROOT / "research/agents_t678/out/T678_LEDGER.json"
INDEX = ROOT / "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
PINS = {T678: "3c1319c5b6ceabde30273d0fcca91b1f19c06c797a5bf54dd44c95a5c89c1ebd",
        INDEX: "02065c41e79dd9df0873cd351e13801c809ca6fa1e62e8a04196af4af13724a7"}
CHECKER = ("Verifier 2026-11-10T17:58Z (Gate A PASS, run session_01E6cPneYaQmLCCbd4QPBgBq: own ST dxf re-measure: "
           "778 = PC-2F member (0.20x0.40 SFRS solid, FFRS ANSI35 + 'P.C 20x50', GFRS none) AGREE 0.1824 .. 0.350; "
           "schedule depths B2 / B6 / B7 / B19 / B20 / CB6 / CB7 AGREE; hand calc D-GF-07 0.096 .. 0.108, D-GF-03 "
           "0.052 .. 0.058 (spare 0.034), W13 0.080 .. 0.108, C3 0.41175 .. 0.50625 AGREE; positions inherited: "
           "PARTIALLY VERIFIED, all HELD; challenges F-V678-1 / F-V678-2)")
SOURCES = {"T-678": {"task": "T-678", "file": "research/agents_t678/out/T678_LEDGER.json", "sha256": PINS[T678],
                     "merge_commit": "f8515d4bbb8ae9d61ecd34ef3b5e46fd007dbf93", "checker_run": CHECKER}}
SCHEMA = "URBAN_V3067_INPUTS_V1"
OA = "ASSUMED - OWNER-APPROVED"
B_MIN = Decimal("0.40")
C3 = "L-fad18af6e7139a5e99d1"
PC2F = "L-541c7e565bb93ecdb78b"
MEM_RE = re.compile(r"w (\d+(?:\.\d+)?), L\d (\d+(?:\.\d+)?) x (\d+(?:\.\d+)?)\)$")
Q_LINTEL = ("T-516 RFI / ST p.13: the lintel end bearings are not dimensioned (MIN 40 cm printed; the drawn jamb "
            "distances are the ceilings) and a deficit end at a column or cross wall has no printed connection; the "
            "soffit over the opening is a lower bound (designer)")
Q_OPEN = ("R-T678-3: one end of this lintel has no recorded stopper (a crossing wall / no extension within the search "
          "limit): the end bearing is not drawn, the high stays OPEN (designer)")
Q_DOOR = ("Q-55 C fallback: the door head height is not printed; the owner door-height fallback 2.20 m above FFL decides "
          "existence with the spare stated; a printed head above the re-run trigger reverses it (designer: door "
          "schedule heads)")
Q_PC = ("ST: the planted column PC-2F is drawn 0.20 x 0.40 (778) and printed 'P.C 20x50' (CONFLICT); the 2F roof slab "
        "top is not printed (R-T669-2 bound 12.68 .. R-T658-4 ceiling 13.90) (designer)")
Q_ANNEX = ("Q-54 B / D-39: the annex roof slab top is not printed (finished +4.30 only); the lower bound 3.544 rests on "
           "the drawn W08 head under CB6 (R-T678-2 / R-T682-1) (designer)")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T678, INDEX))


def _d(x):
    return Decimal(str(x))


def _q6(x):
    return Decimal(x).quantize(Decimal("0.000001"))


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def lintel_hand(r):
    """R-T673-3 / R-T678-3 by hand from the ledger's own fields -> (lo, hi or None, w, B, D)."""
    m = MEM_RE.search(r["member"])
    if not m:
        raise SystemExit(f"{r['line_id']}: no width / section in {r['member']!r}")
    w, B, Dd = (_d(x) for x in m.groups())
    bd = B * Dd
    ends = r["ends"]
    # an end is OPEN when the ledger records no stopper that closes it (R-T678-3: a crossing wall, a search limit with
    # no extension): the ledger marks it by its open high; the low counts 0.40 at every end with >= 0.40 drawn
    open_end = r["high_m3"] is None
    if open_end != (r["convention"].endswith("(one end OPEN)") or any(e[1] == "SEARCH_LIMIT" for e in ends)):
        raise SystemExit(f"{r['line_id']}: open high without an open end (or the reverse)")
    lo = bd * (w + B_MIN * sum(1 for e in ends if _d(e[3]) >= B_MIN))
    if open_end:
        return _q6(lo), None, w, B, Dd
    if r["convention"] == "MIN_BEARING":
        hi = bd * (w + sum(min(_d(e[3]), B_MIN) for e in ends))
    elif r["convention"] == "CEILING":
        hi = bd * (w + sum(_d(e[3]) for e in ends))
    else:
        raise SystemExit(f"{r['line_id']}: convention {r['convention']!r}")
    return _q6(lo), _q6(hi), w, B, Dd


def annex_plane(led):
    """R-T682-1 over R-T678-2 on the ledger's annex slab-top record; the section read is the Checker's (F-V678-2),
    corroborated here: the A-A cut line is drawn north-east of every CB5 / CB6 / CB7 mark of the annex part."""
    a = led["annex_slab_top"]
    plane = {"outline": "GF roof slab, annex part (beams CB6 / CB7 / B9 / B4 / CB5 / B2 / B1)",
             "plan_texts_inside": [],                     # ledger plane_reads: no level / step / thickness text
             "section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": False,
                                "evidence": "Verifier 2026-11-10T17:58Z own ST dxf read: the GFRS section A-A 0.20 "
                                            "step lies outside the annex (F-V678-2); T-682 own read: the A-A cut line "
                                            "(S-SEC.LINE) is drawn north-east of every CB5 / CB6 / CB7 mark"}]}
    heads = [dict(h, head_abs=h["head_abs"], tol=h["tol"]) for h in a["heads"]]
    r = R82.slab_top_lower_bound(heads=heads, plane=plane, finished_ceiling=a["finished_ceiling"])
    if r["state"] != "BOUNDED" or _d(r["s_lo"]) != _d(a["s_lo"]) or r["governing"] != a["governing"]:
        raise SystemExit(f"annex slab top: R-T682-1 gives {r} vs the ledger's {a['s_lo']} ({a['governing']})")
    rec = dict(r["plane"], section_steps=plane["section_steps"], s_lo_m=float(r["s_lo"]), rule="R-T682-1 1.0.0",
               governing=r["governing"], finished_ceiling_m=float(_d(a["finished_ceiling"])),
               not_read="sections B-B / C-C / D-D are not recorded against the annex plane by T-678 or its Checker")
    return rec


def _lintel(r, ix, plane):
    ln = ix.get(r["line_id"])
    if ln is None or ln["item_code"] != "STR.CONC.LINTEL" or ln["class"] != "HELD" or ln["held_low"] is not None:
        raise SystemExit(f"{r['line_id']}: {ln} is not a blank HELD lintel line")
    if ln["element_id"] != f"LINTEL:{r['opening']}":
        raise SystemExit(f"{r['line_id']}: element {ln['element_id']} is not the ledger's opening {r['opening']}")
    if not r["existence"].startswith("REQUIRED (spare "):
        raise SystemExit(f"{r['line_id']}: existence {r['existence']!r}")
    lo, hi, w, B, Dd = lintel_hand(r)
    if lo != _d(r["low_m3"]) or (hi is None) != (r["high_m3"] is None) or (hi is not None and hi != _d(r["high_m3"])):
        raise SystemExit(f"{r['line_id']}: hand {lo} .. {hi} is not the ledger's {r['low_m3']} .. {r['high_m3']}")
    spare = _d(r["existence"].split("spare ")[1].split(" ")[0])
    ends = "; ".join(f"{e[0]} {e[1]} {e[3]}" for e in r["ends"])
    head, hs = r["head"]
    basis = (f"{B} x {Dd} (ST p.13 band) x (w {w} + ends: {ends}; {r['convention']}) = {lo} .. "
             f"{hi if hi is not None else 'OPEN'} m3; existence on the soffit lower bound (R-T678-1): clear "
             f"{r['clear'][0]} .. {r['clear'][1]} above FFL {r['ffl']}, head {head} {hs}, spare {spare} m; "
             f"{r['detail']['c']}; owner manual beside: {r['owner_manual']}")
    e = {"line_id": ln["line_id"], "source_tasks": ["T-678"], "member": r["member"], "expect": _expect(ln),
         "basis": basis[:900], "why_held": f"{r['cause']}; {r['why']}"[:600],
         "question": Q_OPEN if hi is None else (Q_DOOR if hs == OA else Q_LINTEL)}
    if hi is None:
        e.update(action="LOWER_ONLY", beside={"kind": "AT_LEAST_M3", "value": float(lo),
                                              "basis": f"existence REQUIRED (R-T678-1), {B} x {Dd} x (w {w} + bounded "
                                                       f"ends' 0.40) = {lo} m3; the other end OPEN (R-T678-3)"})
    else:
        e.update(action="BOUND", after={"low": float(lo), "high": float(hi)})
    if hs == OA:
        trig = _d(head) + spare
        e["existence"] = {"status": OA, "basis": f"head {head} m = the owner door-height fallback (Q-55 C); the soffit "
                                                 f"lower bound leaves {spare} m spare (R-T678-1)"}
        e["assumption"] = {"status": OA, "source": "Q-55 C (owner door-height fallback)",
                           "what": f"door head {head} m above FFL (not printed)", "assumed_m": float(_d(head)),
                           "spare_m": float(spare), "trigger_m": float(trig),
                           "rerun_trigger": f"a drawn or printed head above {trig:.3f} m over FFL reverses existence "
                                            f"(re-run R-T678-1 for {r['opening']})"}
    else:
        e["existence"] = {"status": "DRAWING-CONFIRMED", "basis": f"head {head} m {hs} (R-T678-1, spare {spare} m)"}
    if "s_lo" in r["detail"]:
        if _d(r["detail"]["s_lo"]) != _d(plane["s_lo_m"]):
            raise SystemExit(f"{r['line_id']}: s_lo {r['detail']['s_lo']} is not the plane's {plane['s_lo_m']}")
        e["plane"] = plane
    return e


def _pc2f(o, ix):
    ln = ix[PC2F]
    if o["owner_line"] != PC2F or ln["class"] != "HELD" or ln["held_low"] is not None or \
            ln["element_id"] != o["element_id"] or ln["item_code"] != "STR.CONC.COLUMN":
        raise SystemExit(f"778: ledger {o['owner_line']} / candidate {ln}")
    h0, h1 = (_d(x) for x in o["height_m"])
    if h0 != _d("12.68") - _d("0.75") - _d("9.65") or h1 != _d("13.90") - _d("0.75") - _d("9.65"):
        raise SystemExit(f"778: heights {h0} .. {h1}")
    lo, hi = _q6(_d("0.20") * _d("0.40") * h0), _q6(_d("0.20") * _d("0.50") * h1)
    if (lo, hi) != (_d(o["lo_m3"]), _d(o["hi_m3"])):
        raise SystemExit(f"778: hand {lo} .. {hi} is not {o['lo_m3']} .. {o['hi_m3']}")
    return {"action": "BOUND", "line_id": PC2F, "source_tasks": ["T-678"],
            "member": "planted column PC-2F (slab outline 778, T-220 COL-2F-59)", "expect": _expect(ln),
            "after": {"low": float(lo), "high": float(hi)},
            "basis": f"0.20 x 0.40 (drawn) x {h0} .. 0.20 x 0.50 (text 'P.C 20x50') x {h1} = {lo} .. {hi} m3: "
                     f"{o['basis']}"[:900],
            "why_held": "section CONFLICT (drawn 20x40 vs printed 20x50) and the 2F roof slab top not printed",
            "question": Q_PC,
            "existence": {"status": "DRAWING-CONFIRMED", "basis": o["verdict"][:300]}}


def _c3(c, ix, plane):
    ln = ix[C3]
    if c["line"] != C3[:10] or ln["class"] != "HELD" or ln["held_low"] is not None or \
            ln["item_code"] != "STR.CONC.COLUMN":
        raise SystemExit(f"C3: ledger {c['line']} / candidate {ln}")
    base = _d("0.25")
    h0, h1 = _d(plane["s_lo_m"]) - base, _d(str(plane["finished_ceiling_m"])) - base
    if (h0, h1) != tuple(_d(x) for x in c["height_m"]):
        raise SystemExit(f"C3: heights {h0} .. {h1} vs {c['height_m']}")
    lo, hi = _q6(_d("0.125") * h0), _q6(_d("0.125") * h1)
    if (lo, hi) != (_d(c["after_lo_m3"]), _d(c["after_hi_m3"])):
        raise SystemExit(f"C3: hand {lo} .. {hi} is not {c['after_lo_m3']} .. {c['after_hi_m3']}")
    return {"action": "BOUND", "line_id": C3, "source_tasks": ["T-678"], "member": "GF annex roof column C3",
            "expect": _expect(ln), "after": {"low": float(lo), "high": float(hi)},
            "basis": f"0.125 m2 x ({plane['s_lo_m']} - 0.25 base APPROVED) .. (4.30 - 0.25) = {lo} .. {hi} m3: "
                     f"{c['basis']}"[:900],
            "why_held": "the annex roof slab top is not printed: top bounded below by R-T678-2 / R-T682-1, above by "
                        "the finished +4.30 (was: AT_MOST 0.50625, low open by name)",
            "question": Q_ANNEX, "plane": plane,
            "existence": {"status": "DRAWING-CONFIRMED", "basis": "column C3 drawn on the ST p.9 column schedule"}}


def build(project_id=None):
    led, index = _load()
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.66":
        raise SystemExit(f"index is {index['candidate_version']}")
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    plane = annex_plane(led)
    meas = [r for r in led["lintels"] if r["cause"] == "MEASURABLE NOW"]
    if len(meas) != led["counts"]["measurable_now"] or \
            sum(1 for r in led["lintels"] if r["cause"] == "OPEN BOUND") != led["counts"]["open_bound_after"]:
        raise SystemExit("T-678 counts")
    lint = [_lintel(r, ix, plane) for r in meas]
    lo = sum(_d(e["after"]["low"]) if e["action"] == "BOUND" else _d(e["beside"]["value"]) for e in lint)
    hi = sum(_d(str(e["after"]["high"])) for e in lint if e["action"] == "BOUND")
    tot = led["lintel_totals_m3"]
    if lo != _d(tot["low"]) or hi != _d(tot["high_of_closed_lines"]):
        raise SystemExit(f"lintels {lo} .. {hi} vs the ledger's {tot}")
    if sorted(e["member"].split(" ")[1] for e in lint if e["action"] == "LOWER_ONLY") != sorted(tot["open_high_lines"]):
        raise SystemExit("open-high lines")
    ents = lint + [_pc2f(led["outline_778"], ix), _c3(led["annex_C3"], ix, plane)]
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "index_sha256": PINS[INDEX],
            "not_wired": [
                {"what": "13 STR.CONC.LINTEL lines OPEN BOUND by the T-678 census", "task": "T-678",
                 "why": "each names its missing datum: they keep their V3.0.66 state (blank, never 0)"},
                {"what": "6 STR.CONC.LINTEL lines DESIGNER ITEM by the T-673 census", "task": "T-673",
                 "why": "unchanged"},
                {"what": "4 other GF annex column lines (height bound 3.294 .. 4.05 m)", "task": "T-678",
                 "why": "their section waits for D-66 (follow-up named by T-678, not a ledger quantity)"}]}


def summary(doc):
    from collections import Counter
    c = Counter((e["expect"]["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "assumed_owner_approved": [(e["member"].split(" ")[1], e["assumption"]["trigger_m"])
                                       for e in doc["entries"] if e.get("assumption")],
            "plane": sum(1 for e in doc["entries"] if e.get("plane")), "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
