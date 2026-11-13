"""T-704: the URBAN_V3071_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.71 (engine.source.arch_v3071), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t699/out/T699_LEDGER.json   T-699 (MERGED 3b0e03d4, Verifier 2026-11-11T10:03Z Gate A PASS, own
      P7757 re-measure of W08 / D-2F-02 / L-GF-01 AGREE, family AT_MOST 1.321826 AGREE): R-T699-1 one-sided bounds of
      the 21 blank STR.CONC.LINTEL lines of V3.0.69;
  research/agents_t699/t699_rules.py          T-699 (same merge): the rule the ledger was built with; the ledger is
      REBUILT here by research/agents_t699/t699_alsenan.build() and must equal the committed file field by field;
  research/agents_t644/out/JAMB_EVIDENCE_T644.csv  T-644 (merged; the jamb evidence T-699 itself read): the DRAWN
      opening gap (clear_width_m) of each opening, for R-T704-2 (r2, Lead ruling F-V704-1: an AT_MOST length is
      measured on one geometry, stopper to stopper; W11 / W12 drawn gap 1.9549 vs schedule 1.95, Checker own P7757
      re-measure 2026-11-11T15:32Z AGREE);
  research/agents_t693/out/LINE_INDEX_V3_0_70.json  T-693 (Gate B PASS, MERGED 2bfa2fbe): the class and range each
      line carries on the candidate of record V3.0.70 e8e001de (the binding; asserted again on the live run).

Per line the inputs carry the TERMS (section B x D, width used, the bearing taken at each end with its stopper and the
drawn available length) so that the module recomputes the one-sided figure itself (R-T704-1); the end terms are
re-derived here from the ledger's own ends with the T-699 rule functions (unchanged) and refused when their sum is not
the ledger's length.

Actions:
  AT_MOST      16 blank lines: the AT_MOST figure beside (never a range, never 0); existence OPEN or a CONDITIONAL
               EXCLUSION naming the member; the 'if REQUIRED' lo beside as CONDITIONAL, never a bound.
  DATUM_NAMED   3 blank lines with no one-sided bound: the exact missing datum named (cause class, reference), a
               conditional lo beside where T-699 states one; no figure in the line.
  (the 2 AT_LEAST lines D-GF-04 / D-1F-06 are ALREADY carried by V3.0.67 (T-682, LOWER_ONLY, AT_LEAST 0.048 / 0.036
  beside): listed under `confirm` and asserted unchanged on the live candidate, not restated.)

    python3 -I research/agents_t704/t704_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t699", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t699_rules as R  # noqa: E402  (T-699, merged)
import t699_alsenan as A699  # noqa: E402  (T-699, merged: rebuilds the ledger)

T699 = ROOT / "research/agents_t699/out/T699_LEDGER.json"
RULES = ROOT / "research/agents_t699/t699_rules.py"
INDEX = ROOT / "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
JAMBS = ROOT / "research/agents_t644/out/JAMB_EVIDENCE_T644.csv"
PINS = {JAMBS: "8b72cfb16ad6fcf8b19842ed76db7fc9ef59232004cc8cd207e9cc354dabcf1c",T699: "c41adc99bb7e59ca012968faed2af0e589143d58d6cafc7c17631d59fff9aa77",
        RULES: "6ebc65273babc3ceeae7cf65e3d203b484093d76aeaf6b6541c00e575c895d3a",
        INDEX: "6c12da077200db176c6b81e0e869b21e731547f1e3265fb982c0be1ef7b7ec98"}
C699 = ("Verifier 2026-11-11T10:03Z (Gate A PASS, merge 3b0e03d4: own P7757 re-measure W08 1.50 + (0.85 - 0.40) + 0.55 "
        "= 2.50 -> 0.100, D-2F-02 0.252 / 0.248 -> 1.40 -> 0.056, L-GF-01 0.400 / 0.400 -> 1.80 -> 0.072 AGREE; family "
        "AT_MOST 1.367666 - 0.045840 = 1.321826 AGREE; existence UNRESOLVED, designer data)")
SOURCES = {"T-699": {"task": "T-699", "file": "research/agents_t699/out/T699_LEDGER.json", "sha256": PINS[T699],
                     "merge_commit": "3b0e03d4", "checker_run": C699}}
SCHEMA = "URBAN_V3071_INPUTS_V1"
LINTEL = "STR.CONC.LINTEL"
CONFIRM = {"D-GF-04": ("L-274b112580029084b80e", 0.048), "D-1F-06": ("L-9ec762c0bd529b924f33", 0.036)}
SHARED = ("W11", "W12", "1.145100")             # the pier both W11 / W12 take whole as their ceiling (R-T699-1 (f))
X = Decimal


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return json.loads(T699.read_text(encoding="utf-8")), json.loads(INDEX.read_text(encoding="utf-8"))


def _ends_input(r):
    out = []
    for side, stop, sid, a in r["ends"]:
        out.append({"side": side, "stopper": stop, "stopper_id": sid, "a": a})
    return out


def end_terms(row, b_min=A699.B_MIN):
    """the bearing taken at each end for the AT_MOST of one ledger row (R-T699-1 (a) on R-T673-3), replayed with the
    T-699 functions: [{side, stopper, stopper_id, available_m, taken_m, why}], width used. Sum is asserted = length."""
    lintel = {"id": row["opening"], "B": row["B_m"], "D": row["D_m"], "form": "STRAIGHT",
              "width_m": row["width_m"] if not isinstance(row["width_m"], list) else None,
              "width_range": row["width_m"] if isinstance(row["width_m"], list) else None,
              "ends": _ends_input(row)}
    m = R.at_most(lintel, A699.NEIGHBOURS, b_min)
    w = m["width_used"]
    widths = [X(str(x)) for x in (lintel["width_range"] or [lintel["width_m"]])]
    extra = w - min(widths)
    best = None
    for s0, s1 in ([(extra, X(0)), (X(0), extra)] if extra else [(X(0), X(0))]):
        ends = [dict(e, a=X(str(e["a"])) - s) for e, s in zip(lintel["ends"], (s0, s1))]
        if any(e["a"] < 0 for e in ends):
            continue
        rows = R._exact_ends({"id": row["opening"], "ends": ends}, A699.NEIGHBOURS, b_min)
        deficit = any(x[0] == R.R73.DEFICIT for x in rows)
        terms = []
        for e, (st, a, c, pier) in zip(ends, rows):
            if deficit:
                taken, why = (b_min, "bounded end, schedule bearing (deficit elsewhere: MIN_BEARING)") \
                    if st == R.R73.BOUNDED else (a, "deficit end: the whole available length")
            else:
                taken, why = c, "the drawn available length to the stopper, 1 mm up (CEILING)"
            if pier and pier[1] in ("RELEASED", "MIN_BEARING"):
                why += f"; pier to {pier[0]} ({pier[1]}) less its bearing {b_min}"
            elif pier:
                why += f"; pier to {pier[0]} ({pier[1]}): taken whole, counted once in the family"
            terms.append({"side": e["side"], "stopper": e["stopper"], "stopper_id": e.get("stopper_id"),
                          "available_m": float(R.R73.ceil_mm(a)), "drawn_m": float(a), "taken_m": float(taken),
                          "why": why})
        length = w + sum(X(str(t["taken_m"])) for t in terms)
        hi = R.BR.mul(X(str(row["B_m"])), X(str(row["D_m"])), length)
        if best is None or hi > best[0]:
            best = (hi, terms, length)
    hi, terms, length = best
    if length != X(row["length_hi_m"]) or R.BR.round_high(hi) != X(row["at_most_m3"]):
        raise SystemExit(f"{row['opening']}: replayed length {length} / {hi} is not the ledger's "
                         f"{row['length_hi_m']} / {row['at_most_m3']}")
    return terms, float(w), ("width CONFLICT " + " / ".join(str(x) for x in widths) + f": {w} used (largest; the span "
                             "between the stoppers is fixed by the drawing, R-T699-1 (a))") if extra or len(widths) > 1 \
        else None


def drawn_gaps():
    """T-644 jamb evidence: the drawn opening gap per opening (one value for both sides, else refused)."""
    import csv
    out = {}
    with JAMBS.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            g = X(r["clear_width_m"])
            if out.setdefault(r["opening_id"], g) != g:
                raise SystemExit(f"{r['opening_id']}: two drawn gaps in the jamb evidence")
    return out


def r_t704_2(row, terms, w, gap):
    """R-T704-2 (Lead ruling F-V704-1, every villa): the AT_MOST length on ONE geometry. CEILING: max(the R-T699-1
    terms, drawn gap + START drawn + END drawn); MIN_BEARING: the R-T699-1 terms + max(0, drawn gap - w).
    -> (length, at_most, basis)."""
    t699 = X(row["length_hi_m"])
    if row["convention"] == "CEILING":
        if isinstance(row["width_m"], list):
            raise SystemExit(f"{row['opening']}: a width conflict on a CEILING line (one geometry not defined)")
        s2s = gap + sum(X(str(t["drawn_m"])) for t in terms)
        length, basis = (t699, "R-T699-1_TERMS") if t699 >= s2s else (s2s, "STOPPER_TO_STOPPER")
    else:
        length, basis = (t699, "R-T699-1_TERMS") if X(str(w)) >= gap else (t699 + gap - X(str(w)), "DRAWN_GAP")
    hi = R.BR.round_high(R.BR.mul(X(str(row["B_m"])), X(str(row["D_m"])), length))
    return length, hi, basis


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def _cond_lo(r):
    """the 'if REQUIRED' lo: the lintel's least length if it exists (beside, CONDITIONAL, never a bound)."""
    if r["conditional_lo_m3"] is None:
        return None
    w = min(X(str(x)) for x in r["width_m"]) if isinstance(r["width_m"], list) else X(str(r["width_m"]))
    lo = X(r["conditional_lo_m3"])
    length = lo / (X(str(r["B_m"])) * X(str(r["D_m"])))
    n = (length - w) / A699.B_MIN
    if n not in (0, 1, 2) or R.BR.round_low(R.BR.mul(X(str(r["B_m"])), X(str(r["D_m"])), length)) != lo:
        raise SystemExit(f"{r['opening']}: conditional lo {lo} is not B x D x (w + n x {A699.B_MIN})")
    return {"value_m3": float(lo), "width_m": float(w), "bounded_ends": int(n), "b_min_m": float(A699.B_MIN),
            "meaning": "if REQUIRED (existence decided): the least length w + bounded ends x the schedule bearing; "
                       "CONDITIONAL, never a bound: the line may be 0"}


def build(project_id=None):
    led, index = _load()
    rebuilt = A699.build()
    if json.loads(json.dumps(rebuilt, sort_keys=True, default=str)) != json.loads(json.dumps(led, sort_keys=True)):
        raise SystemExit("T-699 ledger: the merged builder does not reproduce the committed file")
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.70":
        raise SystemExit("candidate of record moved")
    ix = {r["line_id"]: r for r in index["lines"]}
    lin = [r for r in index["lines"] if r["item_code"] == LINTEL]
    blank = [r for r in lin if r["measured_net"] is None and r["held_low"] is None]
    if len(lin) != 61 or len(blank) != 21:
        raise SystemExit(f"V3.0.70 lintel census {len(lin)} / {len(blank)} blank, expected 61 / 21")
    if {r["line_id"] for r in blank} != {r["line_id"] for r in led["lines"]}:
        raise SystemExit("the 21 blank lintel lines of V3.0.70 are not the ledger's")
    ents, confirm = [], []
    gaps = drawn_gaps()
    for r in led["lines"]:
        x = ix[r["line_id"]]
        if x["class"] != "HELD" or x["held_low"] is not None or x["element_id"] != f"LINTEL:{r['opening']}":
            raise SystemExit(f"{r['line_id']}: not the HELD blank LINTEL:{r['opening']} on V3.0.70")
        if r["opening"] in CONFIRM:
            lid, v = CONFIRM[r["opening"]]
            if lid != r["line_id"] or X(r["at_least_m3"]) != X(str(v)) or r["at_most_m3"] is not None:
                raise SystemExit(f"{r['opening']}: AT_LEAST {r['at_least_m3']} is not the V3.0.67 beside {v}")
            confirm.append({"line_id": lid, "opening": r["opening"], "kind": "AT_LEAST_M3", "value": v,
                            "carried_by": "ARCH_TAKEOFF_V3.0.67 (T-682, LOWER_ONLY, record concrete_ledger_v3067)",
                            "cause": f"{r['cause_class']}: {r['cause_ref']}", "deciding_datum": r["deciding_datum"]})
            continue
        base = {"line_id": r["line_id"], "source_tasks": ["T-699"], "expect": _expect(x),
                "member": f"lintel {r['opening']} ({r['storey']}, {r['block']}, w {r['width_m']}, "
                          f"{r['B_m']} x {r['D_m']})",
                "opening": r["opening"], "existence": r["existence"],
                "excluded_by": r["conditional_exclusion_member"],
                "cause": {"class": r["cause_class"], "ref": r["cause_ref"], "deciding_datum": r["deciding_datum"]},
                "if_required": _cond_lo(r), "owner_manual": r["owner_manual"]}
        base["section"] = {"B_m": r["B_m"], "D_m": r["D_m"], "source": "wall thickness x ST p.13 schedule depth "
                           "(R-T519-1 reading, T-650)"}
        if r["at_most_m3"] is not None:
            terms, w, wnote = end_terms(r)
            gap = gaps[r["opening"]]
            length, hi, lb = r_t704_2(r, terms, w, gap)
            if lb == "R-T699-1_TERMS":
                basis = (f"R-T699-1 (a): {r['B_m']} x {r['D_m']} x ({w} + "
                         + " + ".join(f"{t['taken_m']:g}" for t in terms)
                         + f") = {r['at_most_m3']} m3 AT_MOST ({r['convention']}; drawn gap {gap} <= the terms, "
                           f"R-T704-2); existence {r['existence']}")
            else:
                basis = (f"R-T704-2 ({lb}): {r['B_m']} x {r['D_m']} x {length} = {hi} m3 AT_MOST (drawn gap {gap} vs "
                         f"schedule {w}; the merged R-T699-1 figure {r['at_most_m3']} lost the drawn gap excess); "
                         f"existence {r['existence']}")
            base.update(action="AT_MOST", width_m=w, width_note=wnote, drawn_gap_m=float(gap), end_terms=terms,
                        length_m=float(length), convention=r["convention"], at_most_m3=float(hi), basis=basis)
            if hi != X(r["at_most_m3"]):
                base["ledger_at_most_m3"] = float(X(r["at_most_m3"]))
        else:
            base.update(action="DATUM_NAMED", why_no_bound=r["why_no_at_most"],
                        basis=f"R-T699-1: no one-sided bound ({r['why_no_at_most']}); existence {r['existence']}")
        ents.append(base)
    rows = {e["opening"]: e for e in ents}
    a, b, pier = SHARED
    B, D = X(str(rows[a]["section"]["B_m"])), X(str(rows[a]["section"]["D_m"]))
    if X(led["family"]["pier_counted_once"]["W11/W12"]) != R.BR.mul(B, D, R.R73.ceil_mm(pier)):
        raise SystemExit("shared pier double count moved")
    # R-T704-2: the pier is counted once at the length both lines take it with (drawn on a stopper-to-stopper line)
    took = set()
    for o in (a, b):
        e = rows[o]
        s2s = e["basis"].startswith("R-T704-2 (STOPPER_TO_STOPPER)")
        t = next(t for t in e["end_terms"] if t["stopper"] == "OPENING" and t["stopper_id"] == (b if o == a else a))
        took.add(X(str(t["drawn_m"] if s2s else t["taken_m"])))
    if len(took) != 1:
        raise SystemExit(f"shared pier taken at two lengths {took}: name the overlap")
    pm = took.pop()
    dbl = R.BR.mul(B, D, pm)
    exact = sum(R.BR.mul(X(str(e["section"]["B_m"])), X(str(e["section"]["D_m"])), X(str(e["length_m"])))
                for e in ents if e["action"] == "AT_MOST")
    fam = {"at_most_m3": float(R.BR.round_high(exact - dbl)), "lines": led["family"]["at_most_lines"],
           "ledger_at_most_m3": float(X(led["family"]["at_most_sum_m3"])),
           "shared_piers": [{"lines": [rows[a]["line_id"], rows[b]["line_id"]], "pier_m": float(pm),
                             "double_counted_m3": float(dbl)}],
           "at_least_m3": float(X(led["family"]["at_least_sum_m3"])), "at_least_lines": [c["line_id"] for c in confirm]}
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "confirm": confirm, "family": fam, "index_sha256": PINS[INDEX],
            "not_wired": [
                {"what": "existence of the 16 AT_MOST lintels (designer items D-39 / Q-54 B, T-207, R-T228-3, D-43, "
                         "T-581, T-227, D-04, D-45)", "task": "T-699", "why": "UNRESOLVED: the lines stay blank"},
                {"what": "D-GF-04 / D-1F-06 high end (junction END)", "task": "T-699",
                 "why": "METHOD GAP: a Lead / Checker ruling on a junction end (no owner question)"},
                {"what": "D-GF-14 jambs (GF-W30)", "task": "T-699", "why": "MEASURABLE NOW: a lane S read, not wiring"}]}


def summary(doc):
    from collections import Counter
    c = Counter(e["action"] for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_action": dict(c), "confirm": len(doc["confirm"]),
            "family": doc["family"],
            "rows": [(e["action"], e["opening"], e["line_id"], e.get("at_most_m3"), e["existence"])
                     for e in doc["entries"]]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
