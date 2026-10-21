"""T-064: which run B concrete lines (T-036 run with the typed profile; per-line profile keys from T-044 r2,
research/agents_t044/T-044_RUN_B_LINE_DEPENDENCIES.csv) would rest only on usable values of the controlled project
data file research/urban_engine_m4_correctness/project_data_st7757_t064.json, and which stay HELD.

A line is RELEASABLE_ON_PROJECT_DATA when project_data_file.dependency(profile keys, member=<its member>) is RELEASABLE
and it names no unprinted V6 convention (STANDARD_PRACTICE / ENGINEERING_JUDGEMENT values that are not in the data
file, e.g. GB_LENGTH_BASIS, stair riser / waist): such a convention is not a typed drawing value and is outside this
file, so the line stays held for it. Floor scope: a STOREY_HEIGHT_<F> key is asked for storey
<F> (a column takes the height of the storey it stands in; 3 column lines filed on 1F / 2F name the storey below too
and are marked cross-storey); every other key is asked for the line's own floor (GF / 1F / 2F / FOUNDATION / GROUND),
so a record scoped to other floors holds the line.

Run: python3 -I research/agents_t064/classify_run_b_lines.py  (stdlib only; writes T-064_RUN_B_LINE_STATUS.csv)
"""

from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEPS = os.path.join(ROOT, "research", "agents_t044", "T-044_RUN_B_LINE_DEPENDENCIES.csv")
DATA = os.path.join(ROOT, "research", "urban_engine_m4_correctness", "project_data_st7757_t064.json")
OUT = os.path.join(ROOT, "research", "agents_t064", "T-064_RUN_B_LINE_STATUS.csv")

MEMBER = {"STR.CONC.COLUMN": "COLUMN", "STR.CONC.NECK": "NECK", "STR.CONC.GROUND_BEAM": "GROUND_BEAM",
          "STR.CONC.BLINDING": "BLINDING", "STR.CONC.SLAB": "SLAB", "STR.CONC.STAIR": "STAIR"}


STOREY = "STOREY_HEIGHT_"


def _floor_for(key, line_floor):
    # a storey height is asked for the storey it names (a column takes the height of the storey it stands in);
    # every other record is asked for the line's own floor
    return key[len(STOREY):] if key.startswith(STOREY) else line_floor


def classify(row, pdf):
    keys = [k for k in row["profile_values_used"].split(";") if k]
    conv = [k for k in row["unprinted_v6_conventions"].split(";") if k]
    if row["run_b_status"] != "RELEASED":
        return "HELD_IN_RUN_B", "held in run B already", keys
    if not keys:
        return "NO_PROFILE_VALUE", "uses no profile value", keys
    member = MEMBER.get(row["item_code"])
    inputs = [pdf.value(k, floor=_floor_for(k, row["floor"]), member=member) for k in keys]
    held = [v for v in inputs if not v["usable"]]
    if held:
        why = "; ".join("%s %s (%s)" % (v["key"], v["status"], v.get("reason")) for v in held)
        return "HELD_BY_PROJECT_DATA", why, keys
    cross = [k for k in keys if k.startswith(STOREY) and k[len(STOREY):] != row["floor"]]
    note = (" [cross-storey: line filed on %s takes %s]" % (row["floor"], ", ".join(cross))) if cross else ""
    if conv:
        return "HELD_BY_UNPRINTED_CONVENTION", "data file usable, but also rests on " + ", ".join(conv) + note, keys
    return "RELEASABLE_ON_PROJECT_DATA", "every value usable: " + ", ".join(
        "%s %s" % (v["key"], v["status"]) for v in inputs) + note, keys


def main():
    sys.path.insert(0, ROOT)
    from engine.source import project_data_file as PDF
    pdf = PDF.load_path(DATA)
    rows = list(csv.DictReader(open(DEPS, encoding="utf-8")))
    out, tot = [], defaultdict(lambda: [0, 0.0])
    for r in rows:
        cls, why, keys = classify(r, pdf)
        m3 = float(r["run_b_m3"]) if r["run_b_m3"] else 0.0
        out.append({"item_code": r["item_code"], "element_id": r["element_id"], "floor": r["floor"],
                    "run_b_status": r["run_b_status"], "run_b_m3": r["run_b_m3"], "profile_keys": ";".join(keys),
                    "t064_class": cls, "reason": why})
        t = tot[(r["item_code"], cls)]
        t[0] += 1
        t[1] += m3
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for (item, cls), (n, m3) in sorted(tot.items()):
        print("%-22s %-30s %4d %9.3f" % (item, cls, n, m3))
    # floor scope check: each storey-height record against the storey named by the key
    for fl in ("GF", "1F", "2F"):
        v = pdf.value("STOREY_HEIGHT_" + fl, floor=fl, member="COLUMN")
        print("scope STOREY_HEIGHT_%s floor %s: usable=%s value_m=%s" % (fl, fl, v["usable"], v["value_m"]))
        v = pdf.value("STOREY_HEIGHT_" + fl, floor="FOUNDATION", member="COLUMN")
        assert not v["usable"]


if __name__ == "__main__":
    main()
