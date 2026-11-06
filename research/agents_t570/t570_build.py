"""T-570: the reconciled-quantities statement V4 = the T-562 statement (rebuilt read only and checked against its
committed output) + T-561 (B6 wall paint and stair soffits, m2) as new sections, the T-564 expected-after block on the
floor tile, the T-565 earthworks NOT_COMPARABLE block, the T-566 column CONFLICT readings and beam UNTRACED marks, and
the T-567 restatement of the external plaster (gross vs gross, net vs net). No private input.

  python3 -I research/agents_t570/t570_build.py --write   # write out/
  python3 -I research/agents_t570/t570_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t570_adapters as Z  # noqa: E402

Y, X, SA, S, D = Z.Y, Z.X, Z.SA, Z.S, Z.D
sys.path.insert(0, str(Z.T562))
import t562_build as B562  # noqa: E402

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T570.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T570.md"
REPORTS_COVERED = B562.REPORTS_COVERED + ["T-561", "T-564", "T-565", "T-566", "T-567"]
REPORTS_PENDING = ["T-560", "T-568", "T-571", "T-572", "T-573", "T-574"]
NEW_SECTIONS = ("T-561/paint-internal", "T-561/stair-soffit")
TOUCHED = ("T-545/beams", "T-551/columns", "T-552/plaster-external", "T-553/floor-tile")
EXTRA_KEYS = B562.EXTRA_KEYS + ("conflict", "omission_bound_m2", "expected_after_fix", "split_range_m2")
ENGINE_WRONG_CONFIRMED = dict(B562.ENGINE_WRONG_CONFIRMED)
ROW_KEYS = B562.ROW_KEYS


def _src(name: str) -> dict:
    return json.loads(name.read_text(encoding="utf-8"))


def assemble(index: dict) -> tuple[list[dict], dict, dict]:
    secs, prov, ctx = B562.assemble(index)
    ids = [x["section_id"] for x in secs]
    d561, d564, d565, d566, d567 = (_src(p) for p in (Z.T561_JSON, Z.T564_JSON, Z.T565_JSON, Z.T566_JSON, Z.T567_JSON))
    d551 = _src(Z.T551_JSON)
    secs[ids.index("T-545/beams")] = Z.t566_beams(secs[ids.index("T-545/beams")], d566)
    secs[ids.index("T-551/columns")] = Z.t566_columns(secs[ids.index("T-551/columns")], d566, d551, index)
    secs[ids.index("T-552/plaster-external")] = Z.t567_restate(secs[ids.index("T-552/plaster-external")], d567,
                                                               Z._t567_components(), index)
    secs[ids.index("T-553/floor-tile")] = Z.t564_expected(secs[ids.index("T-553/floor-tile")], d564, index)
    new = Z.t561_sections(index)
    for x in [s for s in secs if s["section_id"] in TOUCHED] + new:
        SA.refuse_held_as_zero(x)
        SA.bind_cross_family(x, index)
        prov["valued_lines_not_in_V3_0_57_index"][x["section_id"]] = Y.A.bind_to_index(SA.for_builder(x), index)
    secs += new
    for p in (Z.T561_JSON, Z.T564_JSON, Z.T565_JSON, Z.T566_JSON, Z.T567_JSON, Z.T567_CSV, HERE / "t570_adapters.py",
              Z.T562 / "t562_adapters.py", Z.T562 / "t562_build.py", B562.JSON_OUT):
        prov["inputs"][str(p.relative_to(Z.ROOT))] = SA.sha(p)
    ctx.update({"d561": d561, "d565": d565, "earthworks": Z.t565_block(index)})
    return secs, prov, ctx


def check_unchanged(st: dict, prev: dict, by_id: dict) -> None:
    """Every T-562 section other than the four targets is identical; the targets change only where their report acts."""
    old = {c["section_id"]: c for c in prev["sections"]}
    new = {c["section_id"]: c for c in st["sections"]}
    for sid, c0 in old.items():
        c = new.get(sid)
        if c is None:
            raise Y.AdapterError(f"{sid}: section lost")
        if sid not in TOUCHED:
            if c != c0:
                raise Y.AdapterError(f"{sid}: changed outside the T-570 targets")
            continue
        for k in ("reference_total", "engine_valued", "engine_bounded", "difference", "held_count", "valued_count"):
            if c[k] != c0[k]:
                raise Y.AdapterError(f"{sid}: {k} moved ({c0[k]} -> {c[k]})")
    for sid in ("T-551/columns", "T-553/floor-tile"):            # beside / labels / notes only
        a, b = new[sid], old[sid]
        if [tuple(json.dumps(r.get(k), sort_keys=True) for k in ROW_KEYS) for r in a["rows"]] != \
                [tuple(json.dumps(r.get(k), sort_keys=True) for k in ROW_KEYS) for r in b["rows"]] or \
                a["by_class"] != b["by_class"]:
            raise Y.AdapterError(f"{sid}: rows or classes changed (only beside / labels may change)")
    bm, bm0 = new["T-545/beams"], old["T-545/beams"]
    exp = Z.beams_expected_by_class(bm0["by_class"], by_id["T-545/beams"])
    if bm["by_class"] != exp:
        raise Y.AdapterError(f"beams: class totals {bm['by_class']} != expected {exp}")
    keep0 = [r for r in bm0["rows"] if r["name"] not in Z.UNTRACED_ROWS.values() and r["name"] != Z.B2_TS_ROW]
    keep = [r for r in bm["rows"] if r.get("correction") != "T-566"]
    if [tuple(json.dumps(r.get(k), sort_keys=True) for k in ROW_KEYS) for r in keep] != \
            [tuple(json.dumps(r.get(k), sort_keys=True) for k in ROW_KEYS) for r in keep0]:
        raise Y.AdapterError("beams: rows changed outside the T-566 target")


def build_from(secs: list[dict], prov: dict, index: dict, ctx: dict, prev: dict | None = None) -> dict:
    st = B562.B554.build_from(secs, prov, index)
    by_id = {x["section_id"]: x for x in secs}
    prev = json.loads(B562.JSON_OUT.read_text(encoding="utf-8")) if prev is None else prev
    prev_by = {c["section_id"]: c for c in prev["sections"]}
    moves = list(prev["reclasses"])
    for c in st["sections"]:
        src = by_id[c["section_id"]]
        if [r["name"] for r in c["rows"]] != [r["name"] for r in src["rows"]]:
            raise Y.AdapterError(f"{c['section_id']}: row order changed in the builder")
        for r, r0 in zip(c["rows"], src["rows"]):
            for k in EXTRA_KEYS:
                if k in r0:
                    r[k] = r0[k]
        if "beside" in src:
            c["beside"] = src["beside"]
        p0 = prev_by.get(c["section_id"], {})
        for k in ("restatement", "restatement_t559"):
            if k in p0:
                c[k] = p0[k]
        if c["section_id"] in NEW_SECTIONS:
            exp = Y.expected_by_class(src["source_by_class"], src["rows"])
            if c["by_class"] != exp:
                raise Y.AdapterError(f"{c['section_id']}: class totals {c['by_class']} != report moved by the listed "
                                     f"reclasses {exp}")
        for r in src["rows"]:
            m = r.get("reclass")
            if m and m["tag"].startswith("F-T570"):
                moves.append({"section_id": c["section_id"], "row": r["name"], **m})
    # T-562's statement-level extras on untouched sections, then the T-562 verifications (unchanged), then ours
    ENGINE_WRONG_CONFIRMED[("T-561/paint-internal", "RETURN: return faces")] = Z.T561_FIX
    X.verify_engine_wrong(st, ENGINE_WRONG_CONFIRMED)
    X.verify_labels(st, B562.NEW_SECTIONS + NEW_SECTIONS + TOUCHED + ("T-547/wall-tile", "T-552/plaster-internal"))
    Y.verify_supersession(st, ctx["d556"])
    Y.verify_per_run_held(st)
    Y.add_gross(st)
    Y.verify_gross(st)
    Y.verify_blinding_apart(st)
    check_unchanged(st, prev, by_id)
    Z.verify_t561(st, ctx["d561"])
    Z.verify_expected_apart(st)
    Z.verify_conflict(st)
    Z.verify_gross_net(st)
    Z.refuse_no_row_as_number(ctx["earthworks"])
    st["not_comparable"] = [ctx["earthworks"]]
    st["reclasses"] = moves
    st["reports_covered"] = REPORTS_COVERED
    st["reports_pending"] = REPORTS_PENDING
    st["rule"] = "R-T548-1 + R-T554-1 + R-T557-1 + R-T562-1 + R-T570-1"
    return json.loads(json.dumps(st, sort_keys=True))


def build() -> dict:
    index = SA.load_index()
    if B562.build() != json.loads(B562.JSON_OUT.read_text(encoding="utf-8")):
        raise Y.AdapterError("T-562 statement does not reproduce: rebuild it before T-570")
    secs, prov, ctx = assemble(index)
    return build_from(secs, prov, index, ctx)


def to_markdown(st: dict) -> str:
    md = ("# T-570 reconciled-quantities statement V4 (generated; reference - engine, + = in the reference only)\n\n"
          + S.to_markdown(st) + "\n")
    md += ("| Section | Unit | Reference | Engine valued | Bounded | Net diff. | Gross abs | % of ref. | ENGINE_WRONG | "
           "HELD (net / gross) | UNRESOLVED (net / gross) |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    for c in st["sections"]:
        b, k, g = c["engine_bounded"], c["by_class"], c["by_class_gross_abs"]
        md += (f"| {c['section_id']} | {c['unit']} | {c['reference_total']} | {c['engine_valued']} | AT_LEAST "
               f"{b['low_at_least']} .. {'OPEN' if b['high_open'] else b['high']} | {c['difference']} | "
               f"{c['gross_abs']} | {c['difference_pct_of_reference']} | {k['ENGINE_WRONG']} | {k['HELD']} / "
               f"{g['HELD']} | {k['UNRESOLVED']} / {g['UNRESOLVED']} |\n")
    secs = {c["section_id"]: c for c in st["sections"]}
    p = secs["T-561/paint-internal"]
    om = [r for r in p["rows"] if r["source_cause"] == "ENGINE_OMISSION"][0]
    md += (f"\nPaint (T-561): wall paint {p['reference_total']} vs engine {p['engine_valued']} m2 (4 released lines, "
           f"PROVISIONAL on the owner G1 ceiling height); return paint ENGINE_OMISSION {om['delta']} m2 = ENGINE_WRONG "
           f"upper bound (omission {' .. '.join(om['omission_bound_m2'])}), fix row {om['fix_row']}, HELD once wired; "
           f"stair soffits {secs['T-561/stair-soffit']['reference_total']} m2 in their own CEILING-class section.\n")
    e = secs["T-553/floor-tile"]["beside"]["expected_after_fix_T564"]
    md += (f"Floor tile (T-564, {e['status'][:8]}): {e['statement']}; engine vs reference "
           f"{e['engine_vs_reference_pct_as_valued']} % as valued, {e['engine_vs_reference_pct_expected']} % expected "
           "(beside only).\n")
    cf = secs["T-551/columns"]["beside"]["conflict_t566"]
    md += (f"Columns (T-566): CONFLICT at {', '.join(x['position'] for x in cf['positions'])}; reading of record "
           f"{cf['reading_of_record']} (NOT a resolution); class range over {len(cf['readings'])} readings: "
           + "; ".join(f"{c} {lo} .. {hi}" for c, (lo, hi) in cf["by_class_range_over_readings"].items() if lo != hi)
           + f"; GF C3 COUNT bound {' .. '.join(cf['gf_c3_count_bound_m3'])} m3.\n")
    bm = secs["T-545/beams"]
    md += (f"Beams (T-566): UNTRACED 0.365289 m3 named by mark; UNRESOLVED now {bm['by_class']['UNRESOLVED']} m3 "
           "(GF B7); 2F B2 COUNT 0.2 m3 ENGINE_RIGHT (Checker), the rest worker-proposed.\n")
    ex = secs["T-552/plaster-external"]["beside"]
    md += (f"External plaster (T-567): gross {secs['T-552/plaster-external']['reference_total']} vs engine 0 (HELD, "
           f"T-314); net beside: his {ex['net_vs_net']['his_net_m2']} vs ours "
           f"{' .. '.join(ex['net_vs_net']['our_net_m2'])} m2 (net vs net); like for like gross "
           f"{ex['like_for_like']['gross']['his_comparable_m2']} vs {' .. '.join(ex['like_for_like']['gross']['ours_m2'])}"
           " m2; T-552 rows SUPERSEDED.\n")
    ew = st["not_comparable"][0]
    md += "\nEarthworks (T-565, NOT_COMPARABLE: his NO_ROW, no difference, no %):\n\n"
    md += "| Family | Basis | Lines | Engine valued m3 | Held range m3 | Held blank | His |\n|---|---|---|---|---|---|---|\n"
    for f in ew["families"]:
        md += (f"| {f['family']} {f['item_code']} | {f['basis']} | {f['lines']} | {f['engine_valued'] or 'none'} | "
               f"{' .. '.join(f['engine_held_range']) if f['engine_held_range'] else 'none'} | "
               f"{f['engine_held_blank_lines']} | NO_ROW |\n")
    md += "\nReclasses (R-T570-1): " + "; ".join(
        f"{m['tag']} {m['section_id']} {m['row'][:50]} {m['from']} -> {m['to']} {m['delta']}"
        for m in st["reclasses"] if m["tag"].startswith("F-T570")) + ".\n"
    md += f"\nReports covered: {', '.join(REPORTS_COVERED)}; pending: {', '.join(REPORTS_PENDING)}.\n"
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-570 statement differs from out/")
            return 1
        print("T-570 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
