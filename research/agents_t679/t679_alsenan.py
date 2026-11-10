"""T-679 development-villa run of R-T679-1 (t679_rules): the concrete reconciliation statement of the candidate of record.

Reads committed files only (no drawing, no client data): the candidate line index (default V3.0.65, T-671), the family
master whose candidate census was built on that index, the held-line causes of the merged censuses (T-669 B10 on
V3.0.63, T-673 lintels / stairs on V3.0.64, T-678 lintels / 778 / C3 on V3.0.65), the project key map T001B and the
normalised reference cover totals, and the merged scorecard V12 (T-635) for the causes of the reference differences.

    python3 -I research/agents_t679/t679_alsenan.py [--index I] [--master M] [--write] [--check]

--write writes out/T679_STATEMENT.json + out/T679_STATEMENT.md; --check rebuilds and compares with the committed files.
Development villa: not an accuracy claim; nothing released; no quantity changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t679_rules as R  # noqa: E402

INDEX = "research/agents_t671/out/LINE_INDEX_V3_0_65.json"
MASTER = "rules/coverage/BOQ_FAMILY_MASTER_1.66.0.json"
KEYMAP = "tests/alsenan/T001B_KEY_MAP.json"
BENCH = "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json"
T669 = "research/agents_t669/out/T669_LEDGER.json"
T673 = "research/agents_t673/out/T673_LEDGER.json"
T678 = "research/agents_t678/out/T678_LEDGER.json"
SCORECARD = "research/agents_t635/out/SCORECARD_T635.json"
PREFIX, UNIT, TRADE = "STR.CONC", "m3", "CONCRETE"
OUT_JSON, OUT_MD = HERE / "out" / "T679_STATEMENT.json", HERE / "out" / "T679_STATEMENT.md"

# Two V3.0.65 HELD lines that no census row names (both added after T-669's V3.0.63 run, neither a lintel / stair):
# their class is read from the merged package that created them; quoted, flagged for the Checker (F-T679-1).
SUPPLEMENT = {
    "L-893c3db13b14dc38625e": {
        "cause_class": "DESIGNER ITEM",
        "named": "pool blinding HELD LOWER_ONLY >= 0.915529 (T-667 MERGED; wired T-668 ADD_LOWER_ONLY): projection beyond "
                 "the wrap drawn, not dimensioned (C4) and F8 / F4 / FN founding vs pool formation -1.50 not printed "
                 "(C6), both on the designer lists (T-667 s.2)",
        "source": "T-667 / T-668 (classed by T-679 from the merged text; no census row)"},
    "L-bef35462630d4b76596f": {
        "cause_class": "DESIGNER ITEM",
        "named": "BAND0030.2 depth companion 0 .. 0.025: strip depth B4 0.50 vs B7 0.75, no mark printed on the strip "
                 "(T-642 FR-T642-2; wired T-671 ADD_COMPANION)",
        "source": "T-642 / T-671 (classed by T-679 from the merged text; no census row)"},
}

# Reference key -> merged scorecard V12 sections whose class split explains that key's difference (quoted, never
# recomputed). Keys with no merged section say so.
KEY_SECTIONS = {
    "CONC.BLINDING": ["T-551/blinding"],
    "CONC.FOOTING": ["T-551/footing-line@V12"],
    "CONC.COLUMN": ["T-551/columns@V12", "T-551/necks", "T-551/lift-walls@V12"],
    "CONC.BEAM": ["T-545/beams@V12"],
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def causes(index_version: str) -> tuple[dict, list[dict]]:
    """line_id -> cause; precedence T-678 > T-673 > T-669 (the latest merged census of that line), then SUPPLEMENT."""
    out: dict[str, dict] = {}
    for r in load(T669)["c_census"]["rows"]:
        out[r["line_id"]] = {"cause_class": r["cause_class"], "named": r.get("named") or r.get("evidence"),
                             "source": "T-669 census (V3.0.63)"}
    t3 = load(T673)
    for r in t3["lintels"] + t3["stairs"]:
        out[r["line_id"]] = {"cause_class": r["cause"], "named": r.get("cause_ref"), "source": "T-673 census (V3.0.64)"}
    t8 = load(T678)
    for r in t8["lintels"]:
        out[r["line_id"]] = {"cause_class": r["cause"], "named": r.get("missing_datum") or r.get("after"),
                             "source": "T-678 (V3.0.65, merged f8515d4b, unwired)"}
    for k in ("outline_778", "annex_C3"):
        r = t8[k]
        lid = r.get("owner_line") if k == "outline_778" else r.get("line")
        lid = lid if isinstance(lid, str) else (lid or {}).get("line_id")
        if lid:
            full = [x for x in out if x.startswith(lid[:10])]
            for x in full:
                out[x] = {"cause_class": "MEASURABLE NOW",
                          "named": f"T-678 {k}: bounded in research, wiring pending (lane I)",
                          "source": "T-678 (V3.0.65, merged f8515d4b, unwired)"}
    supp = []
    for lid, c in SUPPLEMENT.items():
        if lid in out:
            raise R.Refused(f"{lid}: SUPPLEMENT shadows a census row")
        out[lid] = c
        supp.append({"line_id": lid, **c})
    return out, supp


def check_census(fams: dict, master: dict, index_sha: str) -> list[dict]:
    """counts and sums = the master's candidate census family by family (its values are 6-dp floats)."""
    cc = master["candidate_census"]
    if cc["index"].split("sha256 ")[-1].rstrip(")") != index_sha:
        raise R.Refused(f"master census built on another index ({cc['index']})")
    rows = []
    for code, acc in fams.items():
        m = cc["families"][code]["units"][UNIT]
        mine = {"lines": acc["lines"], "released_lines": acc["released_lines"],
                "released": float(round(acc["released"], 6)),
                "held_lines": acc["held_bounded_lines"] + acc["held_blank_lines"],
                "held_low": float(round(acc["held_low"], 6)), "held_high": float(round(acc["held_high"], 6)),
                "held_unknown_lines": acc["held_blank_lines"], "excluded_lines": acc["excluded_lines"],
                "verified_whole_lines": acc["verified_whole_lines"],
                "verified_component_lines": acc["verified_component_lines"]}
        bad = {k: (v, m[k]) for k, v in mine.items() if v != m[k]}
        if bad:
            raise R.Refused(f"{code}: statement != master census {bad}")
        rows.append({"family": code, "agree": sorted(mine)})
    return rows


def verdict_causes(sc: dict) -> dict:
    by = {r["section_id"]: r for r in sc["reference_lines"] if r.get("section_id")}
    out = {}
    for key, sids in KEY_SECTIONS.items():
        out[key] = [OrderedDict(section_id=sid, scored_in=f"{sc['statement']['schema']} sha256 "
                                f"{sc['statement']['sha256'][:12]} (section level {by[sid]['level']})",
                                reference_total=by[sid]["reference_total"],
            engine_valued=by[sid]["engine_valued"], by_class=by[sid]["by_class"],
            status_count=by[sid]["status_count"]) for sid in sids]
    return out


def build(index_rel: str = INDEX, master_rel: str = MASTER) -> dict:
    idx = load(index_rel)
    master = load(master_rel)
    index_sha = sha(ROOT / index_rel)
    cz, supp = causes(idx["candidate_version"])
    lines = [ln for ln in idx["lines"] if ln["item_code"].startswith(PREFIX)]
    agg = R.aggregate(lines, master["families"], cz, prefix=PREFIX, unit=UNIT)
    census_rows = check_census(agg["families"], master, index_sha)
    fam_meta = {f["code"]: f for f in master["families"]}
    families = OrderedDict()
    for code, acc in agg["families"].items():
        v = R.scope_view(acc)
        v["item"] = fam_meta[code]["item_en"]
        v["item_codes"] = [c for c in fam_meta[code]["item_codes"] if c.startswith(PREFIX)]
        families[code] = v
    held_rows = []
    for ln in lines:
        if ln["class"] != R.HELD:
            continue
        c = cz[ln["line_id"]]
        held_rows.append(OrderedDict(
            family=agg["owner"][ln["item_code"]], line_id=ln["line_id"], item_code=ln["item_code"],
            element_id=ln["element_id"], bound=[R.s(R.D(ln["held_low"])), R.s(R.D(ln["held_high"]))]
            if ln["held_low"] is not None else None, cause_class=c["cause_class"], cause=c["named"],
            cause_source=c["source"]))
    held_rows.sort(key=lambda r: (r["family"], r["item_code"], r["line_id"]))
    km = load(KEYMAP)
    keys = [k for k in km["keys"] if k["trade"] == TRADE]
    refs = {r["id"]: r for r in load(BENCH)["records"] if r.get("row_kind") == "COVER_TOTAL"}
    cmp_rows = R.compare(keys, refs, agg["codes"], unit=UNIT)
    vc = verdict_causes(load(SCORECARD))
    for row in cmp_rows:
        row["causes_from_merged_verdicts"] = vc.get(row["key"]) or (
            "UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here")
    sc = load(SCORECARD)
    st = OrderedDict()
    st["schema"] = "URBAN_T679_CONCRETE_STATEMENT_V1"
    st["task"] = "T-679"
    st["rule"] = "R-T679-1 1.0.0 (research/agents_t679/t679_rules.py)"
    st["not_claimed"] = ("development villa; not an accuracy claim; nothing released (the released default V2.9 + route "
                         "G is unchanged); no quantity changed; the reference is never a quantity and agreement is "
                         "never proof")
    st["candidate"] = OrderedDict(version=idx["candidate_version"], index=index_rel, index_sha256=index_sha,
                                  lines_sha256=idx["inputs"]["lines"], master=master_rel,
                                  master_census_agrees=len(census_rows))
    st["inputs_sha256"] = OrderedDict((p, sha(ROOT / p)) for p in (KEYMAP, BENCH, T669, T673, T678, SCORECARD))
    st["trade_total"] = R.scope_view(agg["total"])
    st["families"] = families
    st["item_codes"] = OrderedDict((c, R.scope_view(a)) for c, a in agg["codes"].items())
    st["held_lines"] = held_rows
    st["held_cause_supplement"] = supp
    st["measurable_now_still_held"] = [r["line_id"] for r in held_rows if r["cause_class"] == "MEASURABLE NOW"]
    st["reference_apart"] = OrderedDict(
        rule="difference = reference - engine released; % only where the key holds no HELD line (R-T613-1 (g)); "
             "causes quoted from the merged scorecard V12 sections, scored on its own candidate (not re-classed)",
        scorecard=SCORECARD, scorecard_schema=sc.get("schema"),
        keys=cmp_rows, not_keyed_item_codes=R.not_keyed(agg["codes"], keys),
        findings=findings(cmp_rows, agg["codes"]))
    return st


def findings(rows: list[dict], by_code: dict) -> list[dict]:
    out = []
    col = next(r for r in rows if r["key"] == "CONC.COLUMN")
    lift = by_code.get("STR.CONC.LIFT")
    if lift is not None and "STR.CONC.LIFT" not in col["item_codes"]:
        out.append({"id": "F-T679-2", "key": "CONC.COLUMN",
                    "what": "the reference row 'total walls and columns' carries the lift pit walls (T-551/lift-walls: "
                            "2.4 m3 of it), the key map's engine side does not hold STR.CONC.LIFT (B10-10): the key "
                            "is not like for like by that scope; shown beside, the key map is not changed here",
                    "beside_STR_CONC_LIFT": R.scope_view(lift)})
    beam = next(r for r in rows if r["key"] == "CONC.BEAM")
    out.append({"id": "F-T679-3", "key": "CONC.BEAM",
                "what": f"cover total {d6(beam['reference'])} m3 (key map) vs the T-545 section reference 66.093875 m3: "
                        "the merged beam section reconciles a reference that is not the cover total; its class split "
                        "is quoted against its own reference"})
    return out


def d6(x: str) -> str:
    """display only: 6 dp (the reference cover totals are stored as binary floats, e.g. 47.05500000000001)."""
    return R.s(Decimal(x).quantize(Decimal("0.000001")))


def md(st: dict) -> str:
    L = []
    c = st["candidate"]
    L.append("# T-679 Concrete reconciliation statement (R-T679-1)\n")
    L.append(f"Candidate {c['version']}: `{c['index']}` sha256 {c['index_sha256'][:12]}..., lines sha "
             f"{c['lines_sha256'][:8]}; master `{c['master']}` census agrees on {c['master_census_agrees']} families. "
             f"{st['not_claimed']}.\n")
    L.append("## Engine side: family subtotal -> trade total (m3; buckets never summed together)\n")
    L.append("| Family | Item | Lines | Released n / m3 | Held bounded n / low .. high | Held blank n (DESIGNER / "
             "OPEN BOUND / MEASURABLE NOW) | Excluded n | Engine range | Verified whole / component |")
    L.append("|---|---|---|---|---|---|---|---|---|")

    def row(name, item, v):
        bb = v["held_blank"]["by_cause"]
        return (f"| {name} | {item} | {v['lines']} | {v['released']['lines']} / {v['released']['m3']} | "
                f"{v['held_bounded']['lines']} / {v['held_bounded']['low']} .. {v['held_bounded']['high']} | "
                f"{v['held_blank']['lines']} ({bb['DESIGNER ITEM']} / {bb['OPEN BOUND']} / {bb['MEASURABLE NOW']}) | "
                f"{v['excluded']['lines']} | {v['engine_range'][0]} .. {v['engine_range'][1]} | "
                f"{v['verified_share']['whole']} ({v['verified_share']['whole_m3']}) / "
                f"{v['verified_share']['component']} ({v['verified_share']['component_m3']}) |")
    for code, v in st["families"].items():
        L.append(row(code, v["item"], v))
    L.append(row("**TRADE**", "all STR.CONC", st["trade_total"]))
    L.append("")
    L.append("## Reference comparison, apart (freelancer cover totals, key map T001B)\n")
    L.append("Reference and difference shown at 6 dp; the JSON keeps the stored value exactly. The difference is "
             "reference - engine RELEASED only; the engine range is printed beside it, never netted into it.\n")
    L.append("| Key | Reference m3 | Engine released m3 | Engine range m3 | Held (bounded + blank) | Ref - released m3 "
             "| % | Verified whole |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in st["reference_apart"]["keys"]:
        e = r["engine"]
        L.append(f"| {r['key']} ({', '.join(r['item_codes'])}) | {d6(r['reference'])} | {e['released']['m3']} | "
                 f"{e['engine_range'][0]} .. {e['engine_range'][1]} | {e['held_bounded']['lines']} + "
                 f"{e['held_blank']['lines']} | {d6(r['difference_ref_minus_released'])} | "
                 f"{r['pct_of_reference'] if r['pct_of_reference'] is not None else 'suppressed'} | "
                 f"{e['verified_share']['whole']} |")
    L.append("")
    L.append("Causes (quoted from the merged scorecard V12 sections, each scored on its own candidate; m3 by class):\n")
    for r in st["reference_apart"]["keys"]:
        cz = r["causes_from_merged_verdicts"]
        if isinstance(cz, str):
            L.append(f"- {r['key']}: {cz}")
        else:
            for sct in cz:
                bc = ", ".join(f"{k} {v}" for k, v in sct["by_class"].items() if Decimal(v) != 0)
                L.append(f"- {r['key']} <- {sct['section_id']} (ref {sct['reference_total']}, engine "
                         f"{sct['engine_valued']}): {bc or 'all classes 0'}")
    L.append(f"\nNot keyed (no reference row): {', '.join(st['reference_apart']['not_keyed_item_codes'])}.\n")
    for f in st["reference_apart"]["findings"]:
        L.append(f"- {f['id']} ({f['key']}): {f['what']}")
    L.append(f"\n## HELD lines ({len(st['held_lines'])}), each with its cause\n")
    L.append("| Family | Line | Code | Bound m3 | Cause class | Cause | Source |")
    L.append("|---|---|---|---|---|---|---|")
    for h in st["held_lines"]:
        b = f"{h['bound'][0]} .. {h['bound'][1]}" if h["bound"] else "blank"
        cause = str(h["cause"]).replace("|", "/")[:160]
        L.append(f"| {h['family']} | {h['line_id'][:10]} | {h['item_code'][9:]} | {b} | {h['cause_class']} | {cause} | "
                 f"{h['cause_source']} |")
    return "\n".join(L) + "\n"


def dumps(st: dict) -> str:
    return json.dumps(st, ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=INDEX)
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    st = build(a.index, a.master)
    j, m = dumps(st), md(st)
    if a.write:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(j, encoding="utf-8")
        OUT_MD.write_text(m, encoding="utf-8")
    if a.check:
        ok = OUT_JSON.read_text(encoding="utf-8") == j and OUT_MD.read_text(encoding="utf-8") == m
        print("T679 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    t = st["trade_total"]
    print(f"{st['candidate']['version']}: released {t['released']['lines']} / {t['released']['m3']} m3; bounded "
          f"{t['held_bounded']['lines']} {t['held_bounded']['low']} .. {t['held_bounded']['high']}; blank "
          f"{t['held_blank']['lines']} {t['held_blank']['by_cause']}; excluded {t['excluded']['lines']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
