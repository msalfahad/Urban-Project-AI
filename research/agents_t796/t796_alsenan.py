"""T-796 on the training villa: which MAIN FILL rows the old unconditional overlay forced over the V3.0.86 index, and
the disposal balance from the index's own B1 lines. Writes out/OVERLAY_LOG_V3_0_86.json (no client data: line ids,
item codes, numbers only).

    python3 -I research/agents_t796/t796_alsenan.py <LINE_INDEX.json> <MAIN_FILL_ALL.json> <out.json>
"""
from __future__ import annotations
import collections, copy, importlib.util, json, pathlib, sys

_D = pathlib.Path(__file__).resolve().parent


def _load(name):
    s = importlib.util.spec_from_file_location(name, _D / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


O = _load("overlay_precedence"); B = _load("disposal_balance_t796")


def _val(st):  # point value or range midpoint for the units table (labelled as such)
    c, n, lo, hi = st
    if n is not None:
        return n
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    return None


def main(idx_path, fill_path, out_path):
    idx = json.load(open(idx_path)); fill = json.load(open(fill_path))
    lines = copy.deepcopy(idx["lines"])
    log = O.apply_overlay(lines, fill)
    fam = collections.defaultdict(lambda: dict(rows=0, index_m=0.0, old_overlay_m=0.0, unit=None))
    for e in log:
        if e["action"] in (O.SKIP_NEWER, O.SKIP_CHANGED):
            f = fam[e["item_code"]]; f["rows"] += 1; f["unit"] = e["unit"]
            f["index_m"] += _val(e["index"]) or 0.0; f["old_overlay_m"] += _val(e["row_after"]) or 0.0
    for f in fam.values():
        f["old_minus_index"] = round(f["old_overlay_m"] - f["index_m"], 6)
        f["index_m"] = round(f["index_m"], 6); f["old_overlay_m"] = round(f["old_overlay_m"], 6)
    E, Z1, Z2, held = B.split_b1(idx["lines"])
    bal = B.balance(E, Z1, Z2)
    alt = B.balance(E, Z1, Z2, z2_from_excavation=False)
    res = dict(index=idx.get("candidate_version"), fill_schema=fill.get("schema"), fill_written_on=fill.get("candidate_version"),
               summary=O.summary(log), skipped_by_family=dict(sorted(fam.items())),
               disposal=dict(E=round(E, 6), Z1=round(Z1, 6), Z2=round(Z2, 6), held_b1_lines=held,
                             k1_from_excavation=bal, z2_imported_alternative=alt),
               log=[e for e in log if e["action"] != O.ALREADY])
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out_path, "w"), indent=1)
    print(json.dumps(dict(summary=res["summary"], skipped_by_family=res["skipped_by_family"], disposal=res["disposal"]), indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
