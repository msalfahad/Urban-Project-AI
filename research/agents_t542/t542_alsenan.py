"""T-542 on the training villa: the whole stair marble (treads, risers, landings) classed to its bed rule, checked once
against the floor-bed family, and FINISH V7 run per component, so the stair bed covers more than the 35.4313 m2 of
released candidate lines (T-534).

Reads only merged research and the candidate line index (no drawing, no workbook, no private file):
  parts        research/agents_t534 scope_c(): the drawing-derived stair marble (treads T-425, risers T-412 x T-184
               levels x UP-STAIR-003 / 006, landings T-493), recomputed, never retyped
  classes      research/agents_t493/CENSUS_T493.csv (landing element class, line, floor host note; MERGED)
  floor beds   research/agents_t507/out/LINE_INDEX_V3_0_57.json: every FIN.FLOOR.BED.* line (element id -> line), and
               the stair lines (element ids, released or held)

  python3 -I research/agents_t542/t542_alsenan.py           # print the summary
  python3 -I research/agents_t542/t542_alsenan.py --write   # (re)write research/agents_t542/out/*
  python3 -I research/agents_t542/t542_alsenan.py --check   # recompute and compare with out/ (exit 1 on a difference)
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t534"))

import stair_bed_classes as C  # noqa: E402
import t534_alsenan as T534  # noqa: E402

CENSUS = ROOT / "research/agents_t493/CENSUS_T493.csv"
INDEX = T534.INDEX
OUT = HERE / "out"
SCHEMA = "URBAN_T542_STAIR_BED_CLASSES_V1"
SOURCES = {
    "riser": T534.RISER_BED_SOURCE,
    "landing": ("Q-53 (answered C, owner 2026-10-20 12:02): its scope 'cement bags and sand for every stair (marble "
                "treads, risers, landings)' and its worked figure with the two main-stair landings at 0.03 m 1:3; "
                "V1 OWNER_VALUES STAIR_LANDING 0.03 / 1:3 (T-086, the owner's finishing table)"),
}
# C key -> T-493 census id (landing class, line, host note)
LANDING_IDS = {"MS1-LD": "ST01-MS1-LD", "1F-ARR": "ST01-1F-ARRIVAL", "MS2-LD": "ST01-MS2-LD",
               "2F-ARR": "ST01-2F-ARRIVAL", "RS-LD": "ST02-RS-LD", "E1-LD": "ST03-E1-LANDING",
               "GF-HALL": "ST01-GF-HALL", "GF-LOBBY": "ST01-GF-LOBBY030"}
ARRIVAL_SOURCE = {"1F-ARR": "Q-66 B (landing marble, own element)",
                  "2F-ARR": "Q-70 A (condition met, T-129)",
                  "E1-LD": "OWNER_RULE_OUTDOOR_FLOORS 2026-10-21 (outside stairs marble; T-490)"}
# a stair surface lying in plan inside a floor finish host: how that host leaves it out (T-493 s.3, T-490, T-240)
FLOOR_HOST = {
    "1F-ARR": {"host": "1F living porcelain L-b06400d4 (1F-R78C367)", "deducted_m2": 4.9225,
               "source": "T-240 / T-122: porcelain kept 38.633536 - 4.9225 = 33.711036 (then - 0.300, T-421)"},
    "RS-LD": {"host": "1F porcelain, piece R04 (T-345)", "deducted_m2": 1.352454,
              "source": "T-493 F-2 / T-490: RS-LD is the 1F porcelain deduction R04 1.352454 (grid 0.00005)"},
    "MS1-LD": {"host": "1F porcelain (void V01 / footprint R03)", "void": True,
               "source": "T-493 s.3: lies over the 1F void the 1F porcelain line deducts; stacked over the +0.30 "
                         "lobby (different level, surface overlap 0)"},
    "MS2-LD": {"host": "1F / 2F porcelain (void V01 / footprint R03)", "void": True,
               "source": "T-493 s.3: in the stair void; stacked over MS1-LD and the lobby (surface overlap 0)"},
    "2F-ARR": {"host": "2F lobby porcelain L-9bd25c0c (x 2.50 .. 4.50)", "outside": True,
               "source": "T-493 s.3: 2F arrival vs the 2F lobby porcelain 0.000 m2"},
    "E1-LD": {"host": "GF court outdoor floors (north walk, porch, pool deck)", "outside": True,
              "source": "T-490 census: GF-E1-LANDING carried only by L-3dd82a57 (CARRIED_ELSEWHERE, no other carrier)"},
}
# C key / surface -> the candidate stair line that carries it (released or held); None = no line (T-493 / T-412)
LINE_OF = {
    ("MS1-L", "TREAD"): "L-151d92470a81dd1c450b", ("MS1-L", "RISER"): "L-ecc450d6cc865617f8f6",
    ("D1", "TREAD"): "L-a4aeb32035d11684f1a2", ("D1", "RISER"): "L-8938aa3b25bf605e4b9d",
    ("MS1-U", "TREAD"): "L-e1eb8b9a7cb92508ccc9", ("MS1-U", "RISER"): "L-07e0855f961a839c1277",
    ("MS2-L", "TREAD"): "L-65806b4d02d476603bc5", ("MS2-L", "RISER"): "L-0f060e9951c28c4cf074",
    ("MS2-U", "TREAD"): "L-07f00d5b0c4e1924aaf5", ("MS2-U", "RISER"): "L-12f56cbfe750f8b30c41",
    ("MS1-T", "TREAD"): "L-b4660de0ddd98ad0ffc2", ("MS1-T", "RISER"): "L-820baecf7f726b4d8f1e",
    ("RS-C", "TREAD"): "L-fa534ec5f9dc14947899", ("RS-C", "RISER"): "L-913cda8eb6d73f6e28cc",
    ("RS-S", "TREAD"): "L-89c84fdd4964dec8a323", ("RS-S", "RISER"): "L-099fe9fcfa5667fb8b99",
    ("RS-A", "TREAD"): "L-1dac5d9b574d7608d80d", ("RS-A", "RISER"): "L-16e0c6682725260f28e7",
    ("E1", "TREAD"): "L-314c3ac6d45431b687c5", ("E1", "RISER"): "L-0afa7bd369ec489ebfc2",
    ("E1-LD", "LANDING"): "L-3dd82a576dce1beb4250", ("1F-ARR", "LANDING"): "L-8011889d84788553a6b1",
    ("GF-HALL", "LANDING"): "L-f53d498668da3dc7c228", ("GF-LOBBY", "LANDING"): "L-b4441a1b55eda53d98ea",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load():
    d = json.loads(INDEX.read_text(encoding="utf-8"))
    if d.get("candidate_version") != "ARCH_TAKEOFF_V3.0.57":
        raise C.BedClassError(f"STALE_CANDIDATE: {d.get('candidate_version')}")
    by_id = {ln["line_id"]: ln for ln in d["lines"]}
    floor_bed = {}
    for ln in d["lines"]:
        if ln["item_code"].startswith("FIN.FLOOR.BED.") and ln["class"] == "RELEASED":
            el = ln["element_id"]
            if not el.endswith(":bed"):
                raise C.BedClassError(f"floor-bed line {ln['line_id']} element {el!r} has no ':bed' suffix")
            floor_bed[el[:-4]] = ln["line_id"]
    with open(CENSUS, encoding="utf-8") as fh:
        census = {r["id"]: r for r in csv.DictReader(fh)}
    return d, by_id, floor_bed, census


def parts_alsenan(by_id, census):
    out = []
    for p in T534.scope_c():
        key = p["key"].split("#")[0]
        q = {"key": p["key"], "surface": p["surface"], "m2": p["m2"], "status": p["status"],
             "beside": p["beside"], "reason": p["reason"], "basis": p["basis"]}
        lid = LINE_OF.get((key, p["surface"])) if "#" not in p["key"] else None
        if lid:
            ln = by_id[lid]
            q["element_id"], q["line_id"], q["line_class"] = ln["element_id"], lid, ln["class"]
        else:
            q["element_id"], q["line_id"], q["line_class"] = None, None, None
        if p["surface"] == C.LANDING:
            row = census[LANDING_IDS[key]]
            q["landing_class"] = row["element"]
            if row["line"] and lid and not lid.startswith(row["line"]):
                raise C.BedClassError(f"{key}: T-493 line {row['line']} vs {lid}")
            if q["landing_class"] == C.STAIR_ARRIVAL:
                q["arrival_source"] = ARRIVAL_SOURCE.get(key)
            if key in FLOOR_HOST:
                q["floor_host"] = FLOOR_HOST[key]
        out.append(q)
    return out


def build():
    d, by_id, floor_bed, census = load()
    parts = parts_alsenan(by_id, census)
    rows = C.materials(C.classify_all(parts, SOURCES, floor_bed))
    for r, p in zip(rows, parts):
        r["line_id"], r["line_class"], r["basis"] = p["line_id"], p["line_class"], p["basis"]
        r["in_v7_wire"] = bool(p["line_id"] and p["line_class"] == "RELEASED" and r["bed_class"] == C.STAIR_BED)
    no_src = C.materials(C.classify_all(parts, {"riser": None, "landing": None}, floor_bed))
    out = {
        "schema": SCHEMA, "guard_class": "UNWIRED_RESEARCH", "released_quantities_changed": 0,
        "inputs": {"line_index_v3_0_57": sha(INDEX), "t493_census": sha(CENSUS),
                   "t534_module": sha(ROOT / "research/agents_t534/t534_alsenan.py"),
                   "candidate": d["candidate_version"],
                   "candidate_of_record_note": "V3.0.58 (T-507) adds FIN.WP.ROOF lines only: stair and floor-bed lines "
                                               "= V3.0.57"},
        "sources": SOURCES,
        "floor_bed_family_elements": len(floor_bed),
        "rows": rows,
        "summary": {
            "whole_stair_bed": C.summarise(rows, None, "every stair marble surface (drawing-derived, T-534 C)"),
            "tread": C.summarise(rows, lambda r: r["surface"] == C.TREAD, "treads"),
            "riser": C.summarise(rows, lambda r: r["surface"] == C.RISER, "risers"),
            "landing": C.summarise(rows, lambda r: r["surface"] == C.LANDING, "landings and arrivals"),
            "in_v7_wire": C.summarise(rows, lambda r: r["in_v7_wire"], "parts already carried by a RELEASED candidate "
                                                                         "line (the V7 wire, T-534 B basis)"),
            "beyond_v7_wire": C.summarise(rows, lambda r: not r["in_v7_wire"] and r["bed_class"] == C.STAIR_BED,
                                          "bedded parts with no released candidate line yet (T-412 risers, T-502 "
                                          "landings)"),
        },
        "adverse_no_sources": C.summarise(no_src, None, "no riser / landing bed source (adverse view)"),
    }
    # the V7 wire runs on the candidate's own measured_net; the drawing-derived parts above differ only by polygon
    wire = [r for r in rows if r["in_v7_wire"]]
    net = sum(by_id[r["line_id"]]["measured_net"] for r in wire)
    released = [ln for ln in d["lines"] if ln["item_code"] in T534.STAIR_BED_CODES and ln["class"] == "RELEASED"]
    if {ln["line_id"] for ln in released} != {r["line_id"] for r in wire}:
        raise C.BedClassError("the released stair-bed lines and the in-V7 parts differ")
    out["v7_wire_candidate_net"] = {
        "area_m2": C._r(net), "lines": len(wire),
        "polygon_residual_m2": C._r(out["summary"]["in_v7_wire"]["area_m2"] - net),
        "polygon_note": "E1 treads printed 3.3600 vs line 3.3594; E1 landing printed 5.1800 vs line 5.1794 (T-490 / "
                        "T-534 POLY AGREE)"}
    return out


def write(o):
    OUT.mkdir(exist_ok=True)
    (OUT / "T542_STAIR_BED_CLASSES.json").write_text(json.dumps(o, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    with open(OUT / "STAIR_BED_COMPONENTS_T542.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "surface", "landing_class", "bed_class", "line_id", "line_class", "in_v7_wire", "bed_m2",
                    "bed_m", "mix", "mortar_m3_installed", "cement_bags_installed", "sand_m3_installed",
                    "loss_m3_5pct", "mortar_m3_procurement", "cement_bags_procurement", "sand_m3_procurement",
                    "beside_m2", "reason_or_rule"])
        for r in o["rows"]:
            w.writerow([r["key"], r["surface"], r["landing_class"] or "", r["bed_class"], r["line_id"] or "",
                        r["line_class"] or "", r["in_v7_wire"], r["bed_m2"] if r["bed_m2"] is not None else "",
                        r.get("bed_m", ""), r.get("mix", ""), r.get("mortar_m3_low", ""),
                        r.get("cement_bags_low", ""), r.get("sand_m3_low", ""), r.get("bed_loss_m3_low", ""),
                        r.get("bed_procurement_m3_low", ""), r.get("cement_bags_procurement_low", ""),
                        r.get("sand_m3_procurement_low", ""),
                        r["beside_m2"] if r["beside_m2"] is not None else "", r["reason"] or r["rule"] or ""])


def main(argv):
    o = build()
    if "--write" in argv:
        write(o)
    if "--check" in argv:
        old = json.loads((OUT / "T542_STAIR_BED_CLASSES.json").read_text(encoding="utf-8"))
        new = json.loads(json.dumps(o, sort_keys=True))
        if old != new:
            print("T542 CHECK FAIL: out/ differs from the recomputation")
            return 1
        print("T542 CHECK PASS")
    for k, s in o["summary"].items():
        print(f"{k:16s} {s['print']:34s} mortar {s['mortar_m3_low']} m3, cement {s['cement_bags_low']} bags, sand "
              f"{s['sand_m3_low']} m3 | procurement {s['bed_procurement_m3_low']} m3, {s['cement_bags_procurement_low']}"
              f" bags, {s['sand_m3_procurement_low']} m3")
    a = o["adverse_no_sources"]
    print(f"adverse (no riser / landing source) {a['print']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
