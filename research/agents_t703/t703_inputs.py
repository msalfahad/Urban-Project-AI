"""T-703: the URBAN_V3072_INPUTS_V1 document of ARCH_TAKEOFF_V3.0.72 (MASONRY GATE B ROUND 4), built ONLY from the
Checker-merged ledgers (sha-pinned; a tampered or rebuilt file is refused):

  T-696 (merge 5b51924e, Verifier 2026-11-11 05:55 GATE A PASS): out/T696_B9_CENSUS.json (the one-ended material
        figures beside the blank B9 lines: six 2F roof-datum part hosts AT_MOST, MAIN_S AT_LEAST) and
        out/T696_B9_BOUNDS.json (R-T696-1: the 15 bounded B9 lines, exact ends and the restated range);
  T-713 (merge aa4d8979, Verifier 2026-11-11T17:58Z GATE A PASS, own re-measure AGREE): out/T713_MASONRY_REST.json
        (R-T713-1: 2F 0.15 parent AT_MOST, GF 0.15 parent AT_LEAST, their material figures).

Rates (stated once, each with its source; the module recomputes every figure from area x rate):
  units black 12.5 per m2 (UPC-BLACK-BLOCK-001 1.1.0, Q-75 / Q-80), laying mortar per m2 = t x 0.07375 m3/m2/m
  (T-670 joint rate: 0.15 -> 0.0110625, 0.20 -> 0.01475; Q-78 1:4, owner 10 mm joint), AAC glue 3.5 / 4.5 kg per m2
  (owner 2026-11-02, 15 / 20 cm).

    python3 -I research/agents_t703/t703_inputs.py [--out <file>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CENSUS = "research/agents_t696/out/T696_B9_CENSUS.json"
BOUNDS = "research/agents_t696/out/T696_B9_BOUNDS.json"
REST = "research/agents_t713/out/T713_MASONRY_REST.json"
PINS = {CENSUS: "6810a8ea", BOUNDS: "e9835de4", REST: "0be1ddcd"}
PROJECT = None                      # the run's project id is checked by the hub, not named here
SOURCES = [
    {"task": "T-696", "file": f"{CENSUS}; {BOUNDS}", "sha256": f"{PINS[CENSUS]}; {PINS[BOUNDS]}",
     "merge_commit": "5b51924e8", "checker_run": "Verifier 2026-11-11 05:55 session_01E6cPnd5KnfZDzxWcQgb47z "
                                                 "GATE A PASS"},
    {"task": "T-713", "file": REST, "sha256": PINS[REST], "merge_commit": "aa4d89791",
     "checker_run": "Verifier 2026-11-11T17:58Z session_01E6cPnc2hFBXtv8wJXBRFR3 GATE A PASS (own re-measure 2F 0.15 "
                    "parent AGREE)"},
]
RATES = {
    "units_black_per_m2": {"value": "12.5", "source": "UPC-BLACK-BLOCK-001 1.1.0 (Q-75 / Q-80: 40 x 20 face, 15 and "
                                                      "20 cm)"},
    "mortar_black_m3_per_m2": {"by_t": {"0.15": "0.0110625", "0.20": "0.01475"},
                               "source": "T-670 joint rate (Q-78 1:4, owner 2026-10-29 10 mm joint, PROVISIONAL): "
                                         "t x 0.07375 m3 per m2 per m"},
    "glue_aac_kg_per_m2": {"by_t": {"0.15": "3.5", "0.20": "4.5"}, "source": "owner 2026-11-02 (25 kg bag: 15 cm "
                                                                            "3.5 kg/m2, 20 cm 4.5 kg/m2)"},
}
CAUSE_2F = {"class": "DESIGNER ITEM", "ref": "D-39 main-roof structural level / build-up b_r not printed (T-482 / "
            "T-488): wall = U - L b_r", "deciding_datum": "the roof build-up b_r over the 2F walls (b_r >= 0 gives the "
            "upper end only)"}
CAUSE_MAIN_S = {"class": "OPEN BOUND", "ref": "ST p.1 note 2 black block below the neighbour-side beams: h >= 0.70 m "
                "only, leaf thickness not printed (T-407 / T-675)", "deciding_datum": "the formation level and the leaf "
                "thickness below N.G."}
CAUSE_2F015 = {"class": "DESIGNER ITEM", "ref": "D-04 unlabelled member depth not printed (Q-61 C(4)); D-39 roof "
               "build-up b_r", "deciding_datum": "the depths of BM-2F-016 / -017 / -018 and b_r (upper end at depth 0 "
               "and b_r 0)"}
CAUSE_GF015 = {"class": "DESIGNER ITEM", "ref": "annex datum D-06 / D-17 (owner Q-54 B HOLD), GF-W30 no piece "
               "(T-125), A-GF-01 width not drawn: no upper end; GF-W22 D-27 conflict low end drawn",
               "deciding_datum": "the annex roof structural datum, the GF-W30 piece and the A-GF-01 width"}


def _load(rel):
    p = ROOT / rel
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if not sha.startswith(PINS[rel]):
        raise SystemExit(f"{rel}: sha {sha[:8]} is not the merged {PINS[rel]} (tampered or rebuilt)")
    return json.loads(p.read_text(encoding="utf-8"))


def _host_line(census_rows, host):
    """the MAS.BLOCK host line id of a census host (from T-713's census, which lists the MAS.BLOCK lines)"""
    ids = [r["line_id"] for r in census_rows if r["item_code"] == "MAS.BLOCK" and r["host"] == host]
    if len(ids) != 1:
        raise SystemExit(f"host {host}: {len(ids)} MAS.BLOCK lines in the T-713 census")
    return ids[0]


def build():
    cen, bnd, rest = _load(CENSUS), _load(BOUNDS), _load(REST)
    blocks = rest["census"]
    one = []
    for r in cen["rows"]:
        b = r.get("beside") or {}
        if b.get("kind") not in ("AT_MOST", "AT_LEAST"):
            continue
        e = {"line_id": r["line_id"], "source_tasks": ["T-696"], "item_code": r["item_code"], "unit": r["unit"],
             "kind": b["kind"], "host": r["host"], "host_line_id": _host_line(blocks, r["host"]),
             "area_m2": b["base_m2"], "exact": b["exact"], "printed": b["printed"],
             "cause": CAUSE_2F if r["cause_class"] == "DESIGNER ITEM" else CAUSE_MAIN_S,
             "basis": b.get("why") or b.get("condition") or ""}
        if b["kind"] == "AT_LEAST":
            e.update(min_colour="BLACK", t_conditional="0.15", condition=b["condition"])
        one.append(e)
    for pid, cause in (("L-246f3c09de4c6b90efe5", CAUSE_2F015), ("L-0d9b9e89bb6455da475d", CAUSE_GF015)):
        p = rest["parents"][pid]
        bd = p["bound"]
        comps = [{"id": c["id"], "class": c["class"], "upper": (c.get("end") or {}).get("upper"),
                  "lower": (c.get("end") or {}).get("lower")} for c in p["components"]]
        one.append({"line_id": pid, "source_tasks": ["T-713"], "item_code": "MAS.BLOCK", "unit": "m2",
                    "kind": bd["kind"], "host": p["host"], "host_line_id": pid, "components": comps,
                    "exact": bd["exact_m2"], "printed": bd["printed_m2"], "cause": cause,
                    "basis": "R-T713-1 parent one end; named, not carried: " +
                             ", ".join(x["wall"] for x in p.get("named_not_carried") or ()) or "none"})
        for lid, m in sorted(p["materials"].items()):
            if m["kind"] not in ("AT_MOST", "AT_LEAST"):
                continue
            unit = {"MAS.UNITS.BLACK": "pcs", "MAS.MORTAR.BLACK": "m3", "MAS.GLUE.AAC": "kg"}[m["code"]]
            e = {"line_id": lid, "source_tasks": ["T-713"], "item_code": m["code"], "unit": unit, "kind": m["kind"],
                 "host": p["host"], "host_line_id": pid, "area_m2": bd["exact_m2"], "exact": m["exact"],
                 "printed": m["printed"], "cause": cause, "basis": m["why"]}
            if m["kind"] == "AT_LEAST":
                cols = sorted((bd.get("low_by_colour") or {}))
                if cols != ["BLACK"]:
                    raise SystemExit(f"{lid}: minimum colours {cols}")
                e["min_colour"] = "BLACK"
            one.append(e)
    forms = {"base_m2": "BASE_X_RATE", "bearing_m": "BEARING_X_F", "drawn": "DRAWN_PLUS_HELD"}
    rnd = []
    for r in bnd["rows"]:
        f = [v for k, v in forms.items() if k in r["inputs"]]
        if len(f) != 1:
            raise SystemExit(f"{r['line_id']}: form of {sorted(r['inputs'])}")
        rnd.append({"line_id": r["line_id"], "source_tasks": ["T-696"], "item_code": r["item_code"], "unit": r["unit"],
                    "form": f[0], "inputs": r["inputs"], "exact": r["exact"], "was": r["v3_0_68"],
                    "restated": r["r_t696_1"], "what": r["what"]})
    return {"schema": "URBAN_V3072_INPUTS_V1", "project_id": PROJECT, "sources": SOURCES, "rates": RATES,
            "one_sided": one, "rounding": rnd}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    doc = build()
    from engine.source import arch_v3072 as A
    v = A.load_inputs(doc)
    print("one-sided", len(v["_one_sided"]), "rounding", len(v["_rounding"]),
          "moving", sum(1 for e in v["_rounding"] if e["_moves"]))
    for e in v["_one_sided"]:
        print(e["line_id"], e["item_code"], e["kind"], e["_value"], e["unit"], e["host"])
    if a.out:
        Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
