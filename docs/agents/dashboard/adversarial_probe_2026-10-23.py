"""Adversarial probes of the EXISTING check modules (MAIN audit, 2026-10-23). Synthetic data only; writes nothing to the
repository. Run on Python 3.11 from the engine checkout: .venv/bin/python -I <this file> <engine checkout>; prints JSON"""
import json, random, sys, copy
sys.path.insert(0, sys.argv[1])
from engine.source import boq_line as BL
from engine.source import scope_crosswalk_v1 as XW
from tools import v30_gate_b as GB

REV_A, REV_B = "a" * 64, "b" * 64
res = []


def rec(n, probe, expected, actual, ok, weakness=""):
    res.append({"n": n, "probe": probe, "expected": expected, "actual": actual, "pass": ok, "weakness": weakness})


def line(eid, q, code="STR.CONC.FOOTING", unit="m3", project="PX", rev=REV_A, ev="MEASURED", **kw):
    return BL.make_line(project_id=project, revision_set_sha256=rev, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=q, element_id=eid, formula="L*B*H", rule_id="R-T", rule_version="1", floor="FDN",
                        **kw)


base = [line(f"F{i}", 1.0 + i / 10) for i in range(1, 6)]

# 1 missing element: drawn element with no line
els = [{"id": f"F{i}", "kind": "FOOTING", "floor": "FDN", "label": f"F{i}", "source": "ELEMENT_REGISTER_V0"}
       for i in range(1, 6)]
lines4 = base[:4]
links = {ln["line_id"]: [ln["location"]["element_id"]] for ln in lines4}
r = XW.crosswalk(els, [], {}, lines4, links)
miss = [e["id"] for e in r["elements"] if e["status"] == "MISSING_LINE"]
rec(1, "drawn element F5 in the register, no BOQ line", "F5 MISSING_LINE", f"MISSING_LINE={miss}", miss == ["F5"])

# 1b element absent from BOTH the register and the BOQ (engine never detected it)
r = XW.crosswalk(els[:4], [], {}, lines4, links)
miss = [e["id"] for e in r["elements"] if e["status"] == "MISSING_LINE"]
rec("1b", "footing never detected: absent from register AND BOQ", "detected as missing",
    f"MISSING_LINE={miss}, findings={len(r['findings'])}", bool(miss),
    "crosswalk elements come from the engine's own register: an element the engine never saw vanishes from both; "
    "needs an independent drawing inventory (tags / blocks per layer) as the element source (T-236 item 4/6)")

# 1c same, but a freelancer row names it
rows = [{"row_id": "R1", "trade": "CONCRETE", "unit": "m3", "qty": 9.9, "row_kind": "DETAIL"}]
r = XW.crosswalk(els[:4], rows, {"R1": {"select": {"kind": "FOOTING", "label_base": "F5"}}}, lines4, links)
st = [x["status"] for x in r["rows"]]
rec("1c", "undetected footing, freelancer row maps to label F5", "row flagged", f"row status {st}",
    st == ["SCOPE_UNKNOWN"], "caught only because a reference BOQ exists and names it; not available on a new villa")

# 2 duplicated element: two lines on one element id
dup = base + [BL.make_line(project_id="PX", revision_set_sha256=REV_A, item_code="STR.CONC.FOOTING", unit="m3",
    evidence_state="MEASURED", measured_net=1.1, element_id="F1", formula="L*B*H", rule_id="R-T2", rule_version="1",
    floor="FDN")]
tot = BL.totals(dup, by=("trade",))
links = {ln["line_id"]: [ln["location"]["element_id"]] for ln in dup}
r = XW.crosswalk(els, [], {}, dup, links)
f1 = [e for e in r["elements"] if e["id"] == "F1"][0]
dup_flag = len(f1["lines"]) > 1 and not any(x["finding"].startswith("DUPLICATE") and "F1" in json.dumps(x)
                                             for x in r["findings"])
rec(2, "footing F1 carried by two lines (different rule ids)", "duplicate refused or flagged",
    f"crosswalk: F1 has {len(f1['lines'])} lines, duplicate finding for lines: none; totals sum both "
    f"({sum(v['m3']['net'] for v in tot.values()):.2f} m3)", not dup_flag,
    "crosswalk flags duplicate REFERENCE rows only; duplicate engine lines are caught by element_register_v0.checks "
    "(duplicate_lines / double_concrete) only when both lines share item+unit+element key; T-236 must report it")

# 3 double-deducted opening: the canonical line records deductions; nothing checks one opening twice
refused = False
try:
    BL.make_line(project_id="PX", revision_set_sha256=REV_A, item_code="MAS.BLOCK", unit="m2",
                 evidence_state="MEASURED", measured_net=6.8, element_id="W1", gross=10.0,
                 deductions=[{"opening": "W05", "area": 1.6}, {"opening": "W05", "area": 1.6}], formula="g-d",
                 rule_id="R", rule_version="1")
except BL.LineError:
    refused = True
rec(3, "one opening W05 deducted twice in one wall line", "refused or flagged", f"line accepted={not refused}",
    refused, "the canonical line does not check deductions for repeated opening ids or gross-sum(d)=net; T-236 "
    "gross/deduction/net reconciliation must (one opening id -> one deduction per face)")

# 4 changed beam depth -> quantity moves 1 % and 8 %
before = [line(f"B{i}", 2.0, code="STR.CONC.BEAM") for i in range(1, 201)]
for pct, n in ((1.0, "4a"), (8.0, "4b")):
    after = copy.deepcopy(before)
    after[0] = line("B1", 2.0 * (1 + pct / 100), code="STR.CONC.BEAM")
    d = GB.diff(before, after)
    row = [x for x in d["rows"] if x["element_id"] == "B1"][0]
    rec(n, f"beam B1 depth changed -> volume +{pct}%", "flagged for review",
        f"flags={row['flags']} changed={row['changed']}", "MOVED_5PCT" in row["flags"] or pct < 5,
        "under 5 % and under 2 % share: only STRUCTURAL + changed=true, no change-specific flag; a VERIFIED line "
        "that moves 1 % is not singled out (T-168: VERIFIED_CHANGED flag from the verdict file)" if pct < 5 else "")

# 5 missing window dimension -> a MEASURED line without a quantity, and a zero quantity
for n, kw, exp in (("5a", dict(q=None), "refused"),
                   ("5b", dict(q=0.0), "refused or held")):
    try:
        line("WIN-W14", kw["q"], code="ARCH.WINDOW", unit="m2")
        rec(n, f"window with no height emitted MEASURED qty={kw['q']}", exp, "accepted", False,
            "a zero MEASURED quantity is valid for the schema; HELD-shown-as-0 is only refused where a test asserts it "
            "(T-233 adverse case); T-235 export must refuse a 0 on a line whose inputs are missing")
    except BL.LineError as e:
        rec(n, f"window with no height emitted MEASURED qty={kw['q']}", exp, f"refused: {str(e)[:60]}", True)
try:
    BL.make_line(project_id="PX", revision_set_sha256=REV_A, item_code="STR.CONC.FOOTING", unit="m3",
                 evidence_state="BLOCKED_RFI", element_id="W14", formula="h missing", rule_id="R", rule_version="1")
    rec("5c", "BLOCKED line without its question", "refused", "accepted", False)
except BL.LineError:
    rec("5c", "BLOCKED line without its question", "refused", "refused", True)

# 7 stale revision: same element, after side from another drawing revision
after = copy.deepcopy(base)
after[0] = line("F1", 1.1, rev=REV_B)
d = GB.diff(base, after)
row = [x for x in d["rows"] if x["element_id"] == "F1"][0]
rec(7, "one line re-measured on a different drawing revision", "flagged (revision mix)",
    f"flags={row['flags']} changed_fields={row['changed_fields']}",
    any("REVISION" in f for f in row["flags"]),
    "Gate B has no revision flag; the change shows only in changed_fields. boq_line has INVALIDATED and "
    "document_register_v1 checks citations, but nothing refuses a BOQ mixing two revision sets (T-168 / T-235)")

# 9 omitted trade: a freelancer trade with no candidate line at all
rows = [{"row_id": "P1", "trade": "PAINT", "unit": "m2", "qty": 900, "row_kind": "DETAIL"}]
r = XW.crosswalk(els, rows, {}, base, {ln["line_id"]: [ln["location"]["element_id"]] for ln in base})
rec(9, "whole PAINT trade absent from the BOQ, freelancer has it", "trade flagged",
    f"row status {[x['status'] for x in r['rows']]}", r["rows"][0]["status"] == "NOT_MAPPED",
    "flagged as NOT_MAPPED (join pending), not as TRADE_OMITTED; without a reference BOQ only the 99-family "
    "coverage census shows it, and only if the family is in the master list (T-236: a per-trade row for every "
    "principal trade, never silent)")

# 10 cross-project contamination: one line from project PY in a PX BOQ
after = base + [line("F9", 3.0, project="PY", rev=REV_B)]
try:
    d = GB.diff(base, after)
    row = [x for x in d["rows"] if x["element_id"] == "F9"][0]
    tot = BL.totals(after, by=("trade",))
    rec(10, "a line of project PY inside the PX candidate", "refused",
        f"accepted; flags={row['flags']}; totals include it ({sum(v['m3']['net'] for v in tot.values()):.2f} m3)", False,
        "neither Gate B nor totals() check project_id / revision_set across lines; T-235 export and T-168 must refuse "
        "a BOQ with more than one project_id or an unpinned revision set")
except ValueError as e:
    rec(10, "a line of project PY inside the PX candidate", "refused", f"refused: {e}", True)

# 11 non-deterministic order
shuf = base[:]
random.Random(7).shuffle(shuf)
same = BL.dumps(base) == BL.dumps(shuf)
rows_a = list(BL.csv_rows(base)); rows_b = list(BL.csv_rows(shuf))
rec(11, "same lines in a different producer order -> dumps / csv bytes", "identical bytes",
    f"json identical={same}, csv row order identical={rows_a == rows_b}", same,
    "dumps sorts keys but not the list: export bytes depend on producer order; T-235 must sort by a canonical "
    "key (trade, item, floor, element, line_id) and test semantic + byte identity")

# 11b determinism of the same input twice
rec("11b", "same lines, same order, twice", "identical bytes", f"identical={BL.dumps(base) == BL.dumps(base)}",
    BL.dumps(base) == BL.dumps(base))

# 8 change to a previously verified quantity (scoreboard verdict file)
from tools import scoreboard_v2 as SB
v = {"scope": "WHOLE", "unit": "m3", "engine_qty": 2.0, "checker_qty": 2.0}
for n, q in (("8a", 2.0), ("8b", 2.02)):
    ok, why = SB._remeasure_status(v, {"outcome": SB.S.OUT_COMPARED, "unit": "m3", "engine_qty": q})
    rec(n, f"verified line 2.000 m3, this run {q} m3", "verdict counts only if the quantity is unchanged",
        f"counts={ok} ({why[:60]})", ok == (q == 2.0),
        "detected on the scoreboard only (the line silently drops out of 'verified'); Gate B does not tie the "
        "change to the verdict, and no change log names its cause (T-168)" if q != 2.0 else "")
# 4c a non-structural verified quantity moves 4 %
wl = [BL.make_line(project_id="PX", revision_set_sha256=REV_A, item_code="MAS.BLOCK", unit="m2", evidence_state="MEASURED",
                   measured_net=10.0, element_id=f"W{i}", formula="g-d", rule_id="R", rule_version="1") for i in range(200)]
wa = copy.deepcopy(wl)
wa[0] = BL.make_line(project_id="PX", revision_set_sha256=REV_A, item_code="MAS.BLOCK", unit="m2", evidence_state="MEASURED",
                     measured_net=10.4, element_id="W0", formula="g-d", rule_id="R", rule_version="1")
d = GB.diff(wl, wa)
row = [x for x in d["rows"] if x["element_id"] == "W0"][0]
rec("4c", "blockwork wall W0 (as if VERIFIED) net +4 %", "flagged for review", f"flags={row['flags']} changed={row['changed']}",
    bool(row["flags"]), "below 5 % and 2 % share, a non-structural line gets NO flag (only summary.changed_rows_unflagged)")

# 12 sealed benchmark guard by file name only
from engine.reference_mapping import refuse_if_sealed, SealedReferenceError
for n, path in (("12a", "data/golden/7757/sealed/site_benchmark.json"), ("12b", "private/site_benchmark (1).json")):
    try:
        refuse_if_sealed(path); got = "not refused"
    except SealedReferenceError:
        got = "refused"
    rec(n, f"open sealed benchmark as {path.rsplit('/', 1)[-1]!r}", "refused", got, got == "refused",
        "" if n == "12a" else "the guard matches the file NAME only; a renamed copy passes; Qortuba is not named; Gate B, "
        "scoreboard and baseline tools do not call it (T-168: guard by project id + sha256 in every comparison tool)")
print(json.dumps(res, indent=1))
