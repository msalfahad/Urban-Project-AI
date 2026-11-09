"""T-554: build the reconciled-quantities statement on the five merged sources (T-541, T-534 + F-C-T548-1, T-543 +
F-C-T543-1, T-546, T-542 beside) with the T-548 builder (read only). No private input.

  python3 -I research/agents_t554/t554_build.py --write   # write out/
  python3 -I research/agents_t554/t554_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import statement_adapters as SA  # noqa: E402

S = SA.S
OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T554.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T554.md"
REPORTS_COVERED = ["T-541", "T-534", "T-543", "T-546", "T-542"]
REPORTS_PENDING = ["T-545", "T-547", "T-550", "T-551", "T-552", "T-553"]


def build_from(secs: list[dict], prov: dict, index: dict, corrections: list[dict] | None = None) -> dict:
    st = S.build_statement([SA.for_builder(x) for x in secs])
    by_id = {x["section_id"]: x for x in secs}
    for c in st["sections"]:
        src = by_id[c["section_id"]]
        c["held_cross_family"] = src["engine"].get("held_cross_family", [])
        c["held_count_own_family"] = c["held_count"] - len(c["held_cross_family"])
        if "label" in src["reference"]:
            c["reference_label"] = src["reference"]["label"]
        for r, r0 in zip(c["rows"], src["rows"]):
            for k in ("depends_on", "correction"):
                if k in r0:
                    r[k] = r0[k]
        if c["section_id"] == "T-534/stair-bed":
            c["drawing_derived_beside"] = SA.t542_beside(src, index)
    SA.verify_corrections(st, SA.CORRECTIONS if corrections is None else corrections)
    st["provenance"] = prov
    st["reports_covered"] = REPORTS_COVERED
    st["reports_pending"] = REPORTS_PENDING
    st["rule"] = "R-T548-1 + R-T554-1"
    return json.loads(json.dumps(st, sort_keys=True))


def build() -> dict:
    index = SA.load_index()
    secs, prov = SA.all_sections(index)
    return build_from(secs, prov, index)


def to_markdown(st: dict) -> str:
    md = ("# T-554 reconciled-quantities statement (generated; reference - engine, + = in the reference only)\n\n"
          + S.to_markdown(st) + "\n")
    md += "| Section | Unit | Reference | Engine valued | Bounded | Diff. | % of ref. | cross-family held lines |\n"
    md += "|---|---|---|---|---|---|---|---|\n"
    for c in st["sections"]:
        b = c["engine_bounded"]
        md += (f"| {c['section_id']} | {c['unit']}{' (his ' + c['reference_label'] + ')' if c.get('reference_label') else ''}"
               f" | {c['reference_total']} | {c['engine_valued']} | AT_LEAST {b['low_at_least']} .. "
               f"{'OPEN' if b['high_open'] else b['high']} | {c['difference']} | {c['difference_pct_of_reference']} | "
               f"{len(c['held_cross_family'])} |\n")
    md += ("\nCorrections applied: " + ", ".join(st["provenance"]["corrections_applied"])
           + f". Reports covered: {', '.join(REPORTS_COVERED)}; pending: {', '.join(REPORTS_PENDING)}.\n")
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-554 statement differs from out/")
            return 1
        print("T-554 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
