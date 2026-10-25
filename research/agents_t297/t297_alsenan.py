"""T-297 Alsenan: the REBAR LINE-TO-MEMBER BASIS LEDGER of candidate ARCH_TAKEOFF_V3.0.16 (read only; development villa).

Input: CANDIDATE_V3016_REBAR_LINES.json (t297_extract.py on an own V3.0.16 run of the Drive copies) and the merged
hand ledgers' own summaries (named totals). Output: LINE_BASIS_T297.csv (one row per reinforcement line) and
LINE_BASIS_SUMMARY_T297.json (per (family, basis status) totals in kg and t, residuals, findings).

    python3 -I research/agents_t297/t297_alsenan.py --write     # rebuild and write
    python3 -I research/agents_t297/t297_alsenan.py --check     # rebuild and compare with the committed files

Basis per line (rules LB-1 .. LB-8, every villa; Alsenan only supplies the data):
  LB-1 a line the candidate carries as NOT_APPLICABLE_WITH_EVIDENCE is NOT_APPLICABLE (superseded / not present).
  LB-2 a hand-ledger line released from a printed schedule row (ledger_state RELEASED, line SOURCE_DERIVED) is
       DRAWING_CONFIRMED for the component it names; VERIFIED only where the line itself cites a Checker re-measure.
       A face-to-face component is a measured COMPONENT: the bar ends it leaves out stay their own HELD lines (flag
       COMPONENT_ENDS_HELD), it is never relabelled a bound of itself.
  LB-3 a hand-ledger HELD_RANGE line (BOUNDED_EXPOSURE) is a BOUND; its datum is the range basis the line states;
       the datum is HELD unless the line cites a printed or verified chain.
  LB-4 a hand-ledger HELD_LOWER_BOUND line is a BOUND with an OPEN upper end; HELD_DEFINED / UNQUANTIFIED lines are
       HELD (the defined kg kept as audit only, never a quantity).
  LB-5 a route line (no hand ledger behind it) carrying kg is a CONVENTION: route G's V6 generic conventions (cover,
       anchorage, n/m x L + 1 links), owner 2026-10-25 10:33 (2): a provisional subtotal, never verified, never a bound.
  LB-6 a lap figure from a default factor (no printed lap) is a CONVENTION or HELD, never measured.
  LB-7 one line, one row; totals only per (family, status); kg internally, t once (OWNER_RULE_REBAR_2026-10-24 s.1).
  LB-9 a footing line released on a printed count but a straight length of side - 2 x the MINIMUM cover of the
       general notes is a CONVENTION (the minimum is not a dimension; bends not derived); per-metre footings BOUND.
  LB-8 a research bound that sits in NO candidate line (e.g. the T-280 column foundation cores) is listed as a
       coverage finding, never added to a line.
  LB-10 (r2, Checker F-T297-04) one member, one datum status across trades: a main-bar or link line whose length is
       the member's interval / concrete height takes the datum status the candidate's own concrete line of that member
       carries (t297_datum_join.py: V3.0.17 actions x the T-293 member tie, checked by mark, storey and stack). Concrete
       HELD on a datum -> the bar figure is HELD (its kg kept as audit, flag BAR_LENGTH_ON_HELD_DATUM) or a BOUND that
       names the datum; concrete RE-BASED on a new printed height -> a figure on the old height is HELD
       (BAR_HEIGHT_SUPERSEDED); member NOT_PRESENT -> its bar lines are NOT_APPLICABLE. The candidate's own released kg
       on such lines is reported as 'candidate releases, ledger holds', never dropped from the closure.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t297_datum_join as J  # noqa: E402
import t297_ledger as L  # noqa: E402

CAND_FILE = HERE / "CANDIDATE_V3016_REBAR_LINES.json"
OUT_CSV = HERE / "LINE_BASIS_T297.csv"
OUT_SUM = HERE / "LINE_BASIS_SUMMARY_T297.json"
OUT_CONS = HERE / "LINE_BASIS_CONSUMER_T297.json"
OUT_JOIN = HERE / "DATUM_JOIN_T297.json"
LEDGER_HELD_FLAGS = ("BAR_LENGTH_ON_HELD_DATUM", "BAR_HEIGHT_SUPERSEDED")

LAP_WORDS = re.compile(r"\blap", re.I)
NOTE9 = re.compile(r"note 9|40\s*d\s*\.\.\s*70\s*d|40d\.\.70d", re.I)
DEFAULT_LAP = re.compile(r"\b(40|50|60)\s*d\b.*(default|convention)|convention.*\b(40|50|60)\s*d\b", re.I)


def family_of(l):
    """the line's own physical element (COLUMNS, BEAMS, POOL, WATER_TANK, ...); never guessed from a name"""
    return (l.get("physical_element") or "UNSTATED").upper()


def bar_group_of(l):
    inp = l.get("inputs") or {}
    if inp.get("component"):
        return str(inp["component"]) + (f" | {inp['part']}" if inp.get("part") else "")
    eid = l.get("element_id") or ""
    if "|" in eid:
        return eid.split("|", 1)[1]
    return l.get("subtrade") or "UNSTATED"


def members_of(l):
    inp = l.get("inputs") or {}
    m = inp.get("element") or (l.get("element_id") or "").split("|", 1)[0]
    return (str(m),) if m else ("UNSTATED",)


def _lap_basis(l):
    """LB-6: a lap / bar-end / development figure taken from a default factor, or from note 9 (the starter-bar
    development note, owner 2026-10-24 s.6 (1): not a general lap rule) -> DEFAULT_FACTOR / NOTE_READING"""
    inp = l.get("inputs") or {}
    comp = str(inp.get("component") or "") + " " + str(l.get("element_id") or "")
    txt = " ".join(str(x) for x in (l.get("formula"), comp, inp.get("printed"),
                                     (l.get("bounded_range") or {}).get("basis")) if x)
    if not (LAP_WORDS.search(comp) or NOTE9.search(txt) or re.search(r"\bends?\b|DEVELOPMENT|ANCHORAGE", comp, re.I)):
        return "NONE"
    if NOTE9.search(txt):
        return "NOTE_READING"
    if not inp.get("ledger_state") or DEFAULT_LAP.search(txt):
        return "DEFAULT_FACTOR"
    return "NONE"


def classify(l):
    """one candidate line -> one Row (rules LB-1 .. LB-6)"""
    inp = l.get("inputs") or {}
    ev = l["evidence_state"]
    st = inp.get("ledger_state")
    rng = l.get("bounded_range") or {}
    base = dict(line_id=l["line_id"], family=family_of(l), members=members_of(l), bar_group=bar_group_of(l),
                line_state=ev, sources=(inp.get("ledger") or (f"{inp['policy']} (candidate method)" if inp.get("policy")
                                                              else f"route: {l.get('rule_id')}"),))
    reasons = "; ".join(inp.get("reasons") or ()) or (l.get("rfi") or "") or (l.get("notes") or "")
    printed = inp.get("printed") or ""
    lap = _lap_basis(l)
    flags = []
    if ev == "NOT_APPLICABLE_WITH_EVIDENCE":                                                    # LB-1
        return L.Row(status="NOT_APPLICABLE", reason=(l.get("notes") or "not applicable")[:400], **base)
    if inp.get("policy") == "FOOTING_REBAR_POPULATION_V1":                                    # LB-9
        cov = str(inp.get("cover") or "")
        why = (f"count {printed!r} from the footing schedule; straight bar = side - 2 x cover with cover "
               f"{cov or 'not stated'}: a printed MINIMUM used as the exact cover (ERS lesson 2026-10-23: a minimum "
               f"printed in the notes is never a member dimension); bends / developed length of the p.13 / p.14 "
               f"details not derived (owner 2026-10-25 13:16 F2 - F5; T-299 part F)")
        if "MINIMUM" in cov.upper():
            flags.append("MIN_COVER_AS_EXACT")
        if ev in L_QTY:
            return L.Row(status="CONVENTION", quantity_kg=l["measured_net"], line_kg=l["measured_net"],
                         reason=why[:400], evidence=(l.get("formula") or "")[:300], flags=tuple(flags), **base)
        if ev == "BOUNDED_EXPOSURE":
            return L.Row(status="BOUND", bound_low_kg=rng.get("low"), bound_high_kg=rng.get("high"),
                         line_kg=rng.get("low"), datum=(str(rng.get("basis")) + "; length on cover " + cov)[:300],
                         datum_status="HELD", reason=("Q-71 footing '/m' reading unresolved (owner 12:36 / 13:16: "
                                                      "F8 / F12 / F13 / F14 / FF stay HELD); " + why)[:400],
                         evidence=(l.get("formula") or "")[:300], flags=tuple(flags), **base)
        return L.Row(status="HELD", reason=(reasons or ev)[:400], flags=tuple(flags), **base)
    if st:                                                                                     # hand ledger
        if ev in L_QTY and st == "RELEASED":                                                    # LB-2
            vb = inp.get("verified_by")
            if "face to face" in printed or "face to face" in (l.get("formula") or ""):
                flags.append("COMPONENT_ENDS_HELD")
            return L.Row(status="VERIFIED" if vb else "DRAWING_CONFIRMED", quantity_kg=l["measured_net"],
                         line_kg=l["measured_net"], evidence=(f"{printed} [{inp.get('ledger')}]" + (
                             f" verified by {vb}" if vb else ""))[:400], flags=tuple(flags), **base)
        if ev == "BOUNDED_EXPOSURE":                                                            # LB-3
            return L.Row(status="BOUND", bound_low_kg=rng.get("low"), bound_high_kg=rng.get("high"),
                         line_kg=rng.get("low"), datum=str(rng.get("basis") or reasons)[:300],
                         datum_status="CONVENTION" if lap == "DEFAULT_FACTOR" else "HELD", lap_basis=lap,
                         reason=reasons[:400], evidence=printed[:300], **base)
        if st == "HELD_LOWER_BOUND" and (inp.get("lower_bound_kg") or 0.0) <= 0.0:              # LB-4
            return L.Row(status="HELD", reason=("HELD_LOWER_BOUND at 0 with the upper end open carries no quantity: "
                                                + reasons)[:400], line_kg=inp.get("lower_bound_kg"),
                         evidence=printed[:300], flags=("LOWER_BOUND_ZERO_OPEN",), **base)
        if st == "HELD_LOWER_BOUND" and inp.get("lower_bound_kg") is not None:                 # LB-4
            return L.Row(status="BOUND", bound_low_kg=inp["lower_bound_kg"], bound_high_kg=None,
                         line_kg=inp["lower_bound_kg"], datum=reasons[:300] or "lower bound, upper not established",
                         datum_status="HELD", reason=reasons[:400], evidence=printed[:300], **base)
        held_kg = inp.get("held_defined_kg", inp.get("would_be_kg"))
        return L.Row(status="HELD", reason=(f"{st}: " + reasons)[:400], line_kg=held_kg, evidence=printed[:300],
                     **base)
    if ev in L_QTY:                                                                             # LB-5 / LB-6
        return L.Row(status="CONVENTION", quantity_kg=l["measured_net"], line_kg=l["measured_net"], lap_basis=lap,
                     reason=("route convention: " + (l.get("formula") or ""))[:400],
                     evidence=(l.get("notes") or "")[:300], **base)
    if ev == "BOUNDED_EXPOSURE":
        return L.Row(status="BOUND", bound_low_kg=rng.get("low"), bound_high_kg=rng.get("high"), line_kg=rng.get("low"),
                     datum=str(rng.get("basis") or l.get("formula") or "route range")[:300], datum_status="CONVENTION",
                     lap_basis=lap, reason=(l.get("formula") or "")[:400], **base)
    return L.Row(status="HELD", reason=(reasons or ev)[:400], **base)


L_QTY = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")


def _sheet_key(eid):
    """'P-S:COL:SH12:C5@243102,55481|2F:TIES:D8' / 'P-C:COL:SH12:C5@243102,55481|2F' -> ('C5@243102,55481', '2F')"""
    m = re.search(r":COL:SH12:(C[\w.]*@\d+,\d+)\|(\w+)", eid or "")
    return (m.group(1), m.group(2)) if m else None


def apply_datum(row, line, join_rows):
    """LB-10: one member, one datum status across trades (see the module docstring); returns the row to keep"""
    eff = J.effect_of(join_rows)
    absent = {_sheet_key(j["element_id"]) for j in join_rows if j["length_datum_status"] == "NOT_PRESENT"}
    key = _sheet_key(line.get("element_id"))
    if key and key in absent:
        row.length_datum, row.length_datum_status = "NOT_PRESENT (T-256; V3.0.17 concrete line NOT_APPLICABLE)", \
            "NOT_PRESENT"
        return row
    if row.family != "COLUMNS" or not J.length_on_height(row.bar_group) or row.members[0] not in eff:
        return row
    datum, dst = eff[row.members[0]]
    row.length_datum, row.length_datum_status = datum, dst
    if row.status in ("VERIFIED", "DRAWING_CONFIRMED", "ASSUMED_OWNER_APPROVED", "CONVENTION"):
        flag = "BAR_LENGTH_ON_HELD_DATUM" if dst == "HELD" else "BAR_HEIGHT_SUPERSEDED"
        return L.Row(**{**row.__dict__, "status": "HELD", "quantity_kg": None, "flags": row.flags + (flag,),
                        "reason": (f"LB-10: the bar length rests on the member's datum, which the candidate's concrete "
                                   f"holds: {datum}; was {row.status} {row.quantity_kg:.6f} kg on the hand ledger "
                                   f"(line_kg kept as audit, never a quantity)")[:400]})
    if row.status == "BOUND" and dst == "SUPERSEDED":
        return L.Row(**{**row.__dict__, "status": "HELD", "bound_low_kg": None, "bound_high_kg": None,
                        "flags": row.flags + ("BAR_HEIGHT_SUPERSEDED",),
                        "reason": (f"LB-10: bound {row.bound_low_kg} .. {row.bound_high_kg} kg on a superseded "
                                   f"height; {datum}; re-derive on the re-based height")[:400]})
    if row.status == "BOUND":
        row.datum = (row.datum + " | length datum: " + datum)
        row.datum_status = "HELD"
    elif row.status == "HELD":
        row.reason = (row.reason + " | length datum: " + datum)[:600]
    return row


def candidate_named_totals(lines, rows):
    """the candidate's own sums by (family, line evidence state), to be closed by the row sums"""
    fam = {r.line_id: r.family for r in rows}
    out = defaultdict(float)
    for l in lines:
        if l["evidence_state"] in L_QTY:
            out[(fam[l["line_id"]], "qty")] += l["measured_net"]
        elif l["evidence_state"] == "BOUNDED_EXPOSURE":
            out[(fam[l["line_id"]], "low")] += (l.get("bounded_range") or {}).get("low") or 0.0
    return out


def residuals_vs_candidate(lines, rows):
    named = candidate_named_totals(lines, rows)
    got = defaultdict(float)
    for r in rows:
        if r.status in ("VERIFIED", "DRAWING_CONFIRMED", "ASSUMED_OWNER_APPROVED", "CONVENTION"):
            got[(r.family, "qty")] += r.quantity_kg
        elif r.status == "BOUND" and r.line_state == "BOUNDED_EXPOSURE":
            got[(r.family, "low")] += r.bound_low_kg or 0.0
        elif set(r.flags) & set(LEDGER_HELD_FLAGS):       # LB-10: candidate releases / bounds, the ledger holds
            got[(r.family, "qty" if r.line_state in L_QTY else "low")] += r.line_kg or 0.0
    keys = sorted(set(named) | set(got))
    return {f"{k[0]}|{k[1]}": round(got[k] - named[k], 6) for k in keys}


def source_named_totals():
    """each hand ledger's own named released total (its SUMMARY file) -> {ledger file: (kg, tolerance kg)}"""
    out = {}
    s148 = json.loads((ROOT / "research/agents_t148/T148_SUMMARY.json").read_text(encoding="utf-8"))
    out["research/agents_t148/T148_COLUMNS.csv"] = (s148["net_released_kg"], 0.0005 + 0.0005 * 1)
    s149 = json.loads((ROOT / "research/agents_t149/T149_SUMMARY.json").read_text(encoding="utf-8"))
    out["research/agents_t149/T149_BEAMS.csv"] = (s149["totals"]["RELEASED"], 0.005)
    return out


def residuals_vs_sources(rows):
    named = source_named_totals()
    got, n = defaultdict(float), defaultdict(int)
    for r in rows:
        if r.status in ("VERIFIED", "DRAWING_CONFIRMED") and r.sources:
            got[r.sources[0]] += r.quantity_kg
            n[r.sources[0]] += 1
        elif "BAR_LENGTH_ON_HELD_DATUM" in r.flags and r.line_state in L_QTY and r.sources:
            got[r.sources[0]] += r.line_kg          # the source ledger released it; this ledger holds it (LB-10)
            n[r.sources[0]] += 1
    out = {}
    for src, (kg, tol) in named.items():
        if src in got:
            # tolerance: the named total's own rounding + half a unit of the 3rd decimal per row (ledger storage)
            t = round(tol + 0.0005 * n[src], 6)
            out[src] = {"rows_kg": round(got[src], 6), "named_kg": kg, "residual_kg": round(got[src] - kg, 6),
                        "tolerance_kg": t, "rows": n[src]}
    return out


def build():
    cand = json.loads(CAND_FILE.read_text(encoding="utf-8"))
    lines = cand["lines"]
    join_rows = J.build_join()
    rows = [apply_datum(classify(l), l, join_rows) for l in lines]
    s = L.build(rows, [l["line_id"] for l in lines])
    res_c = residuals_vs_candidate(lines, rows)
    res_s = residuals_vs_sources(rows)
    by_src = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_src[r.sources[0] if r.sources else "ROUTE (no hand ledger)"][r.status] += 1
    flags = defaultdict(int)
    for r in rows:
        for f in r.flags:
            flags[f] += 1
    summary = {"schema": "T297_LINE_BASIS_SUMMARY_V1",
               "candidate": {k: cand[k] for k in ("candidate", "candidate_lines_csv_sha256",
                                                  "candidate_lines_json_sha256", "project", "lines_in_candidate",
                                                  "rebar_lines")},
               "rows": s["rows"], "totals_by_family_status": s["totals"],
               "residuals_vs_candidate_kg": res_c, "residuals_vs_sources_kg": res_s,
               "lines_by_source_and_status": {k: dict(sorted(v.items())) for k, v in sorted(by_src.items())},
               "flags": dict(sorted(flags.items())),
               "coverage_findings": coverage_findings(lines, rows),
               "datum_join": datum_join_summary(join_rows, rows)}
    return cand, rows, summary, join_rows


def datum_join_summary(join_rows, rows):
    """LB-10 / F-T297-04 and F-T297-05: what the member datum join changed, line by line and in kg (never one figure
    over statuses)"""
    held = [r for r in rows if "BAR_LENGTH_ON_HELD_DATUM" in r.flags]
    sup = [r for r in rows if "BAR_HEIGHT_SUPERSEDED" in r.flags]
    named = [r for r in rows if r.length_datum_status == "HELD" and r.status == "BOUND"]
    absent = [r for r in rows if r.length_datum_status == "NOT_PRESENT"]
    return {
        "candidate": "ARCH_TAKEOFF_V3.0.17 concrete actions (research/agents_t254/t254_inputs.py build(), T-254 MERGED "
                     "7c49e890) x the T-293 member tie; reinforcement lines of V3.0.16 = V3.0.17 (REBAR_EQUIVALENCE)",
        "joined_concrete_lines": len(join_rows),
        "by_group": {g: sum(1 for j in join_rows if j["group"] == g) for g in sorted({j["group"] for j in join_rows})},
        "storey_shift_m": join_rows[0]["storey_shift_m"] if join_rows else None,
        "storey_shift_votes": join_rows[0]["storey_shift_votes"] if join_rows else None,
        "F-T297-04 candidate releases, ledger holds (bar length on a held datum)": {
            "lines": sorted(r.line_id for r in held), "members": sorted({r.members[0] for r in held}),
            "candidate_kg": round(sum(r.line_kg for r in held), 6),
            "candidate_t": L.kg_to_t(sum(r.line_kg for r in held))},
        "F-T297-05 bound on a superseded concrete height -> HELD": {
            "lines": sorted(r.line_id for r in sup), "members": sorted({r.members[0] for r in sup}),
            "bound_low_kg_withdrawn": round(sum(r.line_kg or 0.0 for r in sup), 6)},
        "bounds that now name the member's held datum": {"lines": len(named),
                                                         "low_kg": round(sum(r.bound_low_kg or 0 for r in named), 6)},
        "bar lines of NOT_PRESENT members (NOT_APPLICABLE)": len(absent),
        "held_rows_naming_the_datum": sum(1 for r in rows if r.length_datum_status == "HELD" and r.status == "HELD"),
    }


def join_text(join_rows):
    doc = {"schema": "T297_DATUM_JOIN_V1", "rule": "LB-10 one member, one datum status across trades",
           "rows": join_rows}
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def coverage_findings(lines, rows):
    """LB-8: research results that sit in no candidate line or that restate a line's source (listed, never added)"""
    st = {r.line_id: r.status for r in rows}
    fnd = defaultdict(lambda: defaultdict(int))
    for l in lines:
        if l["physical_element"] == "COLUMNS" and l.get("floor") == "FOUNDATION":
            grp = (l.get("element_id") or "").rsplit(":", 2)[-2] if ":" in (l.get("element_id") or "") else "?"
            fnd[grp][f"{l['evidence_state']} -> {st[l['line_id']]}"] += 1
    t138 = sum(r.quantity_kg for r in rows if r.status == "DRAWING_CONFIRMED" and r.sources[0].endswith("T138_MEMBERS.csv"))
    return [
        {"finding": "F-T297-01 column foundation storey: the candidate's only column lines on the FOUNDATION floor are "
                    "route G neck lines, all without quantity; the T-280 cores (26 LOWER bounds 734.781 kg on the "
                    "printed level chain, 10 HELD; MERGED 86fdc315) sit in no candidate line: a later lane I row "
                    "carries them as BOUND lines with their datum, never as measured kg",
         "foundation_column_lines_by_bar_group": {k: dict(v) for k, v in sorted(fnd.items())}},
        {"finding": "F-T297-02 ground-beam steel: the candidate's released ground-beam lines rest on T-138 r2 "
                    "(DRAWING_CONFIRMED components); T-265 (MERGED) restates 13 axis pairs of T-138 (T-299 READY: "
                    "572.500 kg -> T-265 released rows, 320.440 kg -> HELD); the candidate lines are not yet re-based "
                    "(lane I), so their DRAWING_CONFIRMED label stands for T-138 only",
         "t138_drawing_confirmed_kg_in_candidate": round(t138, 6)},
        {"finding": "F-T297-03 footings: the 38 released footing lines (FOOTING_REBAR_POPULATION_V1) take the straight "
                    "bar as side - 2 x 70 mm where note 22 prints cover 'not less than 7 cm' (a minimum) and derive no "
                    "bend: basis CONVENTION, never DRAWING_CONFIRMED (owner 13:16 F2 - F5; T-299 part F)",
         "lines": sum(1 for r in rows if "MIN_COVER_AS_EXACT" in r.flags and r.status == "CONVENTION")},
    ]


CSV_COLS = ("line_id", "family", "members", "bar_group", "basis_status", "quantity_kg", "quantity_t",
            "bound_low_kg", "bound_high_kg", "datum", "datum_status", "lap_basis", "line_state", "line_kg",
            "sources", "flags", "evidence", "reason", "length_datum", "length_datum_status")


def _f(x):
    return "" if x is None else f"{x:.6f}"


def csv_text(rows):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in sorted(rows, key=lambda x: (x.family, x.line_id)):
        w.writerow([r.line_id, r.family, ";".join(r.members), r.bar_group, r.status, _f(r.quantity_kg),
                    "" if r.quantity_kg is None else f"{L.kg_to_t(r.quantity_kg):.6f}", _f(r.bound_low_kg),
                    _f(r.bound_high_kg), r.datum, r.datum_status, r.lap_basis, r.line_state, _f(r.line_kg),
                    ";".join(r.sources), ";".join(r.flags), r.evidence, r.reason, r.length_datum,
                    r.length_datum_status])
    return b.getvalue()


def consumer_text(cand, rows):
    """acceptance (4): the shape a later lane I rebar row consumes (one record per line; t once; bounds as bounds)"""
    doc = {"schema": "T297_LINE_BASIS_CONSUMER_V1", "candidate": cand["candidate"],
           "candidate_lines_csv_sha256": cand["candidate_lines_csv_sha256"], "unit": "t (from kg once, 6 decimals)",
           "rules": "a BOUND record carries bound_t {low, high, datum, datum_status} and quantity_t null; HELD / "
                    "NOT_APPLICABLE carry neither; totals only per (family, basis_status); never one figure over "
                    "statuses", "records": L.consumer(rows)}
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    cand, rows, summary, join_rows = build()
    txt, js = csv_text(rows), json.dumps(summary, indent=1, ensure_ascii=False) + "\n"
    cons, jn = consumer_text(cand, rows), join_text(join_rows)
    if a.write:
        OUT_CSV.write_text(txt, encoding="utf-8")
        OUT_SUM.write_text(js, encoding="utf-8")
        OUT_CONS.write_text(cons, encoding="utf-8")
        OUT_JOIN.write_text(jn, encoding="utf-8")
    else:
        ok = (OUT_CSV.read_text(encoding="utf-8") == txt and OUT_SUM.read_text(encoding="utf-8") == js
              and OUT_CONS.read_text(encoding="utf-8") == cons and OUT_JOIN.read_text(encoding="utf-8") == jn)
        print("check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps(summary["totals_by_family_status"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
