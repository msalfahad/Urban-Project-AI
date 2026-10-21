"""T-136 runner for the verifier: FOOTING_REBAR_POPULATION_V1 on a structural DXF read outside the clone.

    .venv/bin/python -I research/agents_t136/run_t136_alsenan.py <repo root> <structural.dxf> <out dir> \
        --size-unit cm --cover-mm 70 --cover-wording MINIMUM --cover-source "<sheet, note>" \
        --bottom-end-source "<sheet, detail>"

1. route G (run B: V6 conventions + the typed profile, completeness on, as T-126) gives the released footings;
2. the footing schedule is read from the DXF itself: every INSERT whose attributes carry a footing mark (FO-TY) and
   the bar cells (SH-* / LO-*), as printed;
3. the size unit, the cover and the bottom-bar end come from the printed sheets the caller names (the script holds
   no project value); the top-bar ends get no source (none drawn) and stay held.
Writes per-occurrence and per-mark CSVs (marks and kg only, no coordinates) and a JSON with component ids to <out dir>
(keep it outside the public clone). Prints route G vs the new piece per mark."""

import argparse
import collections
import csv
import json
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument("root")
ap.add_argument("dxf")
ap.add_argument("out")
ap.add_argument("--size-unit", required=True)
ap.add_argument("--cover-mm", type=float)
ap.add_argument("--cover-wording", default="MINIMUM")
ap.add_argument("--cover-source", default="")
ap.add_argument("--bottom-end-source")
a = ap.parse_args()
sys.path.insert(0, a.root)

import ezdxf  # noqa: E402

from engine.source import footing_rebar_population_v1 as P  # noqa: E402
from tools import urban_boq_m2 as M2  # noqa: E402

R = M2.compute([a.dxf], conventions=a.root + "/engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json",
               profile=a.root + "/research/urban_engine_m4_correctness/profile_st7757_m4.json", route="G",
               completeness=True)
items = R["items"]
foot = P.footings_from_route_items(items)

doc = ezdxf.readfile(a.dxf)
rows = []
for e in doc.modelspace().query("INSERT"):
    at = {x.dxf.tag: x.dxf.text for x in e.attribs}
    if at.get("FO-TY") and any(k.startswith(("SH-", "LO-")) for k in at):
        rows.append(P.rows_from_block_attributes(at, a.size_unit, source=f"INSERT {e.dxf.handle} block {e.dxf.name}"))

cover = {"value_mm": a.cover_mm, "wording": a.cover_wording, "source": a.cover_source} if a.cover_mm else None
ends = {"BOTTOM": {"state": "STRAIGHT", "source": a.bottom_end_source} if a.bottom_end_source else None, "TOP": None}
res = P.run(foot, rows, cover=cover, end_treatment=ends, unit_mass={"method": "D2_OVER_162"})

# route G footing steel per occurrence (its own P-S lines)
rg = collections.defaultdict(float)
for it in items:
    if it.get("trade") == "REINFORCEMENT" and it.get("family") == "FOOTINGS":
        cid = it.get("component_id") or ""
        rg[cid] += it.get("base") or 0.0

occ_out, per_mark = [], collections.defaultdict(lambda: collections.Counter())
for o in res["occurrences"]:
    cs = [c for c in res["components"] if c["occurrence_id"] == o["occurrence_id"]]
    rd = collections.Counter()
    for c in cs:
        for k, v in (c.get("readings") or {}).items():
            rd[k] += v["kg"]
    lo, hi = o["held_kg_range"] or (0.0, 0.0)
    row = {"mark": o["mark"] or "(two marks)", "status": o["status"], "held_reason": o["held"] or "",
           "route_g_kg": round(rg.get(o["occurrence_id"], 0.0), 3), "released_kg": round(o["released_kg"], 3),
           "held_low_kg": round(lo, 3), "held_high_kg": round(hi, 3),
           "count_reading_A_kg": round(rd["A_ceil_inside_cover"], 3),
           "count_reading_B_kg": round(rd["B_A_plus_edge_bar"], 3),
           "count_reading_C_kg": round(rd["C_rate_x_full_side"], 3),
           "held_unquantified": " ".join(o["held_unquantified"]), "boxed_printed": o.get("boxed_raw") or ""}
    occ_out.append(row)
    m = per_mark[row["mark"]]
    m["n"] += 1
    for k in ("route_g_kg", "released_kg", "held_low_kg", "held_high_kg", "count_reading_A_kg",
              "count_reading_B_kg", "count_reading_C_kg"):
        m[k] += row[k]

comp_out = [{"mark": c["mark"] or "(two marks)", "component": c["component"], "status": c["status"],
             "printed": c.get("raw") or "", "dia_mm": c.get("dia_mm"), "count": c.get("count"),
             "count_range": c.get("count_range"), "bar_length_m": c.get("bar_length_m"),
             "net_kg": None if c.get("net_kg") is None else round(c["net_kg"], 3),
             "net_kg_range": None if not c.get("net_kg_range") else [round(x, 3) for x in c["net_kg_range"]],
             "reasons": " | ".join(c["reasons"])} for c in res["components"]]

with open(a.out + "/T136_OCCURRENCES.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(occ_out[0]))
    w.writeheader()
    w.writerows(sorted(occ_out, key=lambda r: (r["mark"], r["status"])))
with open(a.out + "/T136_COMPONENTS.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(comp_out[0]))
    w.writeheader()
    w.writerows(sorted(comp_out, key=lambda r: (r["mark"], r["component"])))
with open(a.out + "/T136_RUN.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, default=str)

key = lambda k: (re.sub(r"\d", "", k), int(re.sub(r"\D", "", k) or 0))  # noqa: E731
print(f"{'mark':12s} n  routeG   released  held_lo  held_hi   A        B        C")
for k in sorted(per_mark, key=key):
    m = per_mark[k]
    print(f"{k:12s} {m['n']:2d} {m['route_g_kg']:8.2f} {m['released_kg']:9.2f} {m['held_low_kg']:8.2f} "
          f"{m['held_high_kg']:8.2f} {m['count_reading_A_kg']:8.2f} {m['count_reading_B_kg']:8.2f} "
          f"{m['count_reading_C_kg']:8.2f}")
t = res["totals"]
print("TOTAL route G", round(sum(rg.values()), 2), "| released", round(t["released_kg"], 2), "| held range",
      round(t["held_kg_low"], 2), "..", round(t["held_kg_high"], 2), "| readings", {k: round(v, 2) for k, v in
                                                                                 res["count_readings_kg"].items()})
print("unquantified held components", t["held_unquantified_components"], "| rows without footing",
      res["schedule_rows_without_footing"], "| checks", res["check"])
