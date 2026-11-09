"""T-563: the URBAN_V3061_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.61 (engine.source.arch_v3061), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Read from those files: every line id,
element, room, the candidate value / range the line carries before, the new held range, its height basis and its
cause; typed here are only the line states the candidate of record carries (asserted by the module's binding: a
different candidate refuses) and the RFI question each held line keeps:

  research/agents_t556/out/T556_PLASTER_HEIGHT.json   T-556 (MERGED 655b9eac, Verifier 2026-11-06 10:20Z Gate A PASS):
      PLASTER_HEIGHT_METHOD_V1 (R-T556-1) per line: face lm, floor / roof split, H floor / roof scenario, gross,
      openings and beam ends low / high, net low / high, the held cause;
  research/agents_t558/WIRING_MANIFEST_V6.json        T-558 (MERGED 3b46332d, Verifier 2026-11-06 12:00Z Gate A PASS):
      PLASTER_HEIGHT_V1_WIRING: per line before (class, value) and v6_expected_after (held_low / held_high), the
      paint pair of each room, the 22 binding expectations;
  research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json  T-634 (MERGED 52230429, Verifier 2026-11-08T19:59Z Gate A
      PASS): an independent re-measure beside (own net vs T-556) on the rooms it covers; never the wired value;
  research/agents_t651/out/LINE_INDEX_V3_0_59.json    T-651 (MERGED 26af97af): the class, released net and held
      range each line carries on the candidate of record V3.0.59 (the binding; V3.0.60 moves no plaster quantity).

The inputs builder asserts, before anything is written: T-556 new_lo / new_hi rounded to 5 decimals = the manifest's
held_low / held_high; the manifest's before = T-556's candidate class and old value; every paint pair is the room's.

    python3 -I research/agents_t563/t563_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T556 = ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json"
T558 = ROOT / "research/agents_t558/WIRING_MANIFEST_V6.json"
T634 = ROOT / "research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json"
INDEX = ROOT / "research/agents_t651/out/LINE_INDEX_V3_0_59.json"
PINS = {T556: "8169a1953c386ccab7bbd9283404c100dc9d8105e6c10b7244593c9af442cd84",
        T558: "b44b919e4ef749e7d283da6d080e1a806f590a9eba9ef474eeb833c23c78cfe9",
        INDEX: "2cd0ebd8e39db84510ba7a4a4f257cd3b2c1176f650ca7094ed71741fb698ab0",
        T634: None}     # T-634 pinned below (read beside only)
SOURCES = {
    "T-556": {"task": "T-556", "file": "research/agents_t556/out/T556_PLASTER_HEIGHT.json", "sha256": PINS[T556],
              "merge_commit": "655b9eac399fee2f9e325437682d90cd4baa2640",
              "checker_run": "Verifier 2026-11-06 10:20Z (Gate A PASS: own raw-DXF re-measure 1F-04 63.141 and 2F-03 "
                             "69.775 m2 AGREE, GF-15 66.529 by hand; PARTIALLY VERIFIED 2 / 11)"},
    "T-558": {"task": "T-558", "file": "research/agents_t558/WIRING_MANIFEST_V6.json", "sha256": PINS[T558],
              "merge_commit": "3b46332dbc9b9dfc8e21875eacb7c0729ef3cfe2",
              "checker_run": "Verifier 2026-11-06 12:00Z (Gate A PASS: WIRING MANIFEST V6, PLASTER_HEIGHT_V1_WIRING row)"},
}
SCHEMA = "URBAN_V3061_INPUTS_V1"
# the RFI each line keeps (the designer items the T-556 cause names; ERS 2.7 not met: no owner question)
QUESTION = ("D-39 / DCR-6 (designer): the roof build-up over this room is not printed (only the drawn-section 0.05 "
            "layer): confirm the roof finish build-up so the plaster height under the roof slab is DRAWING-CONFIRMED")
BEFORE_STATE = {"RELEASED": "PROVISIONAL", "HELD": None}    # read on the V3.0.60 chain run; asserted by the module


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _pinned(p):
    if PINS.get(p) and _sha(p) != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return json.loads(p.read_text(encoding="utf-8"))


def _d5(s):
    return float(Decimal(str(s)).quantize(Decimal("0.00001")))


def rows():
    """-> one dict per moved plaster line (11), cross-asserted T-556 vs T-558."""
    t556 = {r["line_id"]: r for r in _pinned(T556)["rows"]}
    man = _pinned(T558)
    pairs = {p["plaster_line"]: p for p in man["paint"]["pairs"]}
    out = []
    for m in man["plaster_lines"]["rows"]:
        lid = m["line_id"]
        r = t556.get(lid)
        if r is None:
            raise SystemExit(f"{lid}: in the manifest, not in T-556")
        x = m["v6_expected_after"]
        lo, hi = _d5(r["new_lo"]), _d5(r["new_hi"])
        if (lo, hi) != (x["held_low"], x["held_high"]) or x["class"] != "HELD" or x["value"] is not None:
            raise SystemExit(f"{lid}: T-556 {lo} .. {hi} is not the manifest's {x}")
        if m["before"]["class"] != r["candidate_class"]:
            raise SystemExit(f"{lid}: manifest before {m['before']['class']} vs T-556 {r['candidate_class']}")
        if m["before"]["class"] == "RELEASED" and abs(float(r["old_paint_height_basis"]["value"][0]) -
                                                       m["before"]["value"]) > 1e-9:
            raise SystemExit(f"{lid}: T-556 old value is not the manifest's before")
        p = pairs.get(lid)
        if p is None or p["room"] != m["room"] or p["paint_expected_after"] != p["paint_before"]:
            raise SystemExit(f"{lid}: no paint pair of the room, or the manifest moves paint")
        n = r["new"]
        out.append({"line_id": lid, "room": m["room"], "element_id": m["element_id"], "before": m["before"],
                    "low": lo, "high": hi, "paint_line_id": p["paint_line"], "paint_before": p["paint_before"],
                    "basis": {"zone": r["zone"], "H_floor_m": r["H_floor_m"], "H_roof_scenario_m": r["H_roof_scenario_m"],
                              "roof_share": r["roof_share"], "face_lm": r["face_lm"],
                              "face_floor_lm": n["face_floor_lm"], "face_roof_lm": n["face_roof_lm"],
                              "gross_m2": n["gross"], "openings_m2": [n["openings_lo"], n["openings_hi"]],
                              "openings": n["openings"], "beam_ends_m2": [n["beam_ends_lo"], n["beam_ends_hi"]],
                              "beam_ends": n["beam_ends"], "open_sides_lm": r["open_sides_lm"],
                              "openings_head_above_G1": r["openings_head_above_G1"],
                              "roof_sensitivity_m2_per_0.01m": n["roof_sensitivity_m2_per_0.01m"],
                              "old_paint_height_basis": r["old_paint_height_basis"]},
                    "why_held": r["status"]})
    if len(out) != 11 or len({o["line_id"] for o in out}) != 11:
        raise SystemExit(f"{len(out)} lines (the manifest names 11)")
    return out, man


def remeasure_beside():
    """T-634 own re-measure beside the wired T-556 value (rooms it covers): {line_id: {own, own_minus_t556}}."""
    d = json.loads(T634.read_text(encoding="utf-8"))
    out = {}
    for room, r in sorted(d["rooms"].items()):
        p = r.get("plaster_Q72_beside") if isinstance(r, dict) else None
        if p and r.get("line_id"):
            out[r["line_id"]] = {"room": room, "own_net_m2": p["net_own"], "own_minus_t556_m2": p["own_minus_t556"]}
    return out, _sha(T634)


def index_expect():
    """line id -> (class, released net, held low / high) on the V3.0.59 candidate of record (T-651 line index)."""
    return {r["line_id"]: r for r in _pinned(INDEX)["lines"]}


def build(project_id=None):
    rs, man = rows()
    idx = index_expect()
    beside, s634 = remeasure_beside()
    ents = []
    for r in rs:
        rel = r["before"]["class"] == "RELEASED"
        ix = idx.get(r["line_id"])
        if ix is None or ix["class"] != r["before"]["class"] or ix["item_code"] != "FIN.PLASTER" or \
                ix["element_id"] != r["element_id"] or (rel and abs(ix["measured_net"] - r["before"]["value"]) > 1e-9):
            raise SystemExit(f"{r['line_id']}: the V3.0.59 index row {ix} is not the manifest's before {r['before']}")
        held = {} if rel else {"low": ix["held_low"], "high": ix["held_high"]}
        ents.append({"action": "PLASTER_HEIGHT", "line_id": r["line_id"], "source_tasks": ["T-556", "T-558"],
                     "expect": {"item_code": "FIN.PLASTER", "element_id": r["element_id"], "unit": "m2",
                                "class": r["before"]["class"],
                                "measured_net": r["before"]["value"] if rel else None, **held},
                     "room": r["room"], "after": {"low": r["low"], "high": r["high"]}, "basis": r["basis"],
                     "why_held": r["why_held"], "question": QUESTION, "paint_line_id": r["paint_line_id"],
                     "remeasure_beside": beside.get(r["line_id"])})
    return {"schema": SCHEMA, "project_id": project_id,
            "sources": list(SOURCES.values()),
            "remeasure_beside_source": {"task": "T-634", "file": "research/agents_t634/out/"
                                        "T634_PLASTER_PAINT_REMEASURE.json", "sha256": s634,
                                        "merge_commit": "52230429",
                                        "checker_run": "Verifier 2026-11-08T19:59Z (Gate A PASS)",
                                        "use": "beside only (never the wired value)"},
            "expect_totals": {"released_before_m2": man["plaster_lines"]["released_before_m2"],
                              "released_after_bound_m2": man["plaster_lines"]["released_after_bound_m2"],
                              "all_11_after_bound_m2": man["plaster_lines"]["all_11_after_bound_m2"],
                              "code_released_before_m2": man["plaster_lines"]["code_view"]["FIN.PLASTER_released_now_m2"],
                              "code_released_after_m2": man["plaster_lines"]["code_view"]["FIN.PLASTER_released_after_m2"]},
            "entries": ents}


def main(argv):
    doc = build(argv[1] if len(argv) > 1 else None)
    for e in doc["entries"]:
        b = e["remeasure_beside"]
        print(e["room"], e["line_id"], e["expect"]["class"], e["expect"]["measured_net"], "->", e["after"]["low"], "..",
              e["after"]["high"], "| paint", e["paint_line_id"], "| T-634", b and b["own_minus_t556_m2"])
    print(json.dumps(doc["expect_totals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
