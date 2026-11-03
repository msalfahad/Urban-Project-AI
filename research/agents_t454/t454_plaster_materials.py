"""T-454: the B2 PLASTER MATERIAL LEDGER beside the candidate (ARCH_TAKEOFF_V3.0.45), NOT in it.

Reader tool (stdlib + engine.source.plaster_materials_table_v1). It measures nothing: each material row traces
    candidate plaster line id -> face class (merged T-349 spatter binding) -> line m2 and label -> layer -> thickness
    (sourced, with its level) -> mortar m3 -> cement / sand (HELD while no mix is sourced).
No candidate module, no released (V2.9 + route G) line and no BOQ_FAMILY_MASTER family changes here.

Inputs (committed, sha256-pinned; no drawing content):
  research/agents_t479/out/LINE_INDEX_V3_0_45.json   candidate V3.0.45 line index (plaster lines, nets, held ranges,
                                                      verdict binding)
  research/agents_t349/SPATTER_BINDING_T349.csv       merged face-by-face spatter binding (family per face row:
                                                      INT_DRY_LINE / INT_WET_FACE / INT_WET_RESIDUAL / EXT_*)

Rules (research rules of this task; project-independent):
  R-T454-1 CLASS   a FIN.PLASTER line is DRY_WALL_PLASTER when every merged binding row on it is INT_DRY_LINE, WET_WALL_
           RENDER when every row is INT_WET_FACE / INT_WET_RESIDUAL (the wet-room backing line IS the tiler's
           levelling render, T-331 / T-457); no row or a mixture -> CLASS_NOT_ESTABLISHED, every layer HELD with its
           area beside. Exterior fence plaster (EXT.FENCE.PLASTER) is not in the interior reference -> HELD by name.
  R-T454-2 AREA    the layer area is the candidate line's measured_net, unchanged; label VERIFIED-NET only for a line
           bound VERIFIED_WHOLE by a Checker V2 verdict, else PROVISIONAL-NET; a HELD line gives HELD (never 0) with
           its held range carried beside as a mortar BOUND (range x thickness), never a figure. EXCLUDED lines carry
           no material (listed).
  R-T454-3 LAYERS  every plastered or rendered face carries the BOND_COAT (spatter, OD-V3B-4 .. 7) on the same m2 as
           the coat above it (T-349 R-T349 carrier rule: one face, one carrier); dry faces add WALL_PLASTER, wet faces
           LEVELLING_RENDER. Thickness, mix and labels: PLASTER_MATERIALS_TABLE_V1 docstring.

    python3 -I research/agents_t454/t454_plaster_materials.py [OUT_DIR]     # writes the ledger (default: ./out)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import plaster_materials_table_v1 as P  # noqa: E402

SCHEMA = "URBAN_T454_PLASTER_MATERIALS_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.45"
LINE_INDEX = ROOT / "research/agents_t479/out/LINE_INDEX_V3_0_45.json"
BINDING = ROOT / "research/agents_t349/SPATTER_BINDING_T349.csv"
PINS = {LINE_INDEX: "16920d3c682399541f8fa84d31f39bca171e3d4e7f362bcb1eb0b05b3f4269f4",
        BINDING: "c8da1b8ada514a63bf6eba066f6cd4097f7d5a24a28142e47a70f8b2a2df0f54"}
INTERIOR = "FIN.PLASTER"
EXTERIOR = "EXT.FENCE.PLASTER"
NOT_IN_SCOPE = {"FIN.EXT.FINISH": "facade finish system (Sigma / exterior render): T-162 / B4 exterior rows",
                "FIN.STAIR.SOFFIT": "stair soffit finish: the stair finish rows (B7)"}
DRY_FAM, WET_FAM = {"INT_DRY_LINE"}, {"INT_WET_FACE", "INT_WET_RESIDUAL"}


class LedgerError(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _pinned(p):
    h = _sha(p)
    if h != PINS[p]:
        raise LedgerError(f"{Path(p).relative_to(ROOT)}: sha256 {h[:8]} is not the pinned {PINS[p][:8]}")
    return p


def classify(families):
    """R-T454-1: a set of merged binding families on one line -> (class or None, reason)."""
    fam = set(families)
    if not fam:
        return None, "no merged binding row names this line: dry plaster or wet render not established"
    if fam <= DRY_FAM:
        return P.DRY, "every binding row is INT_DRY_LINE (T-349)"
    if fam <= WET_FAM:
        return P.WET, "every binding row is a wet tiled face (T-349 INT_WET_*): the line is the levelling render"
    return None, f"binding rows mix {sorted(fam)}: never split by guess"


def area_label(line):
    """R-T454-2"""
    b = line.get("binding") or {}
    return P.VNET if b.get("binding") == "VERIFIED_WHOLE" else P.PNET


def build(line_index=None, binding=None):
    li = json.loads(Path(_pinned(LINE_INDEX) if line_index is None else line_index).read_text(encoding="utf-8"))
    rows = list(csv.DictReader(io.StringIO(Path(_pinned(BINDING) if binding is None else binding)
                                           .read_text(encoding="utf-8"))))
    fams = defaultdict(set)
    for r in rows:
        fams[r["target"]].add(r["family"])
    lines = [ln for ln in li["lines"] if ln["item_code"] in (INTERIOR, EXTERIOR)]
    excluded, elements, meta = [], [], {}
    for ln in sorted(lines, key=lambda x: (x["item_code"], x["element_id"], x["line_id"])):
        if ln["class"] == "EXCLUDED":
            excluded.append({"line_id": ln["line_id"], "element_id": ln["element_id"],
                             "why": "EXCLUDED in the candidate: no plaster face, no material"})
            continue
        if ln["item_code"] == EXTERIOR:
            cls, why = None, "exterior fence plaster: the interior reference values do not apply (exterior render HELD)"
        else:
            cls, why = classify(fams.get(ln["line_id"], ()))
        held = ln["measured_net"] is None
        if not held and ln["class"] != "RELEASED":
            raise LedgerError(f"{ln['line_id']}: a figure on a {ln['class']} line")
        e = {"id": ln["line_id"], "class": cls, "area_m2": ln["measured_net"],
             "area_label": None if held else area_label(ln),
             "area_reason": None if not held else f"line HELD in {CANDIDATE} (never 0)", "source": ln["element_id"]}
        elements.append(e)
        meta[ln["line_id"]] = {"item_code": ln["item_code"], "element_id": ln["element_id"], "line_class": ln["class"],
                               "class_reason": why, "held_low": ln["held_low"], "held_high": ln["held_high"]}
    t = P.table(elements)
    for r in t["rows"]:
        m = meta[r["id"]]
        r.update(m)
        for x in r["layers"]:
            ref = P.REFERENCE.get(x["layer"]) or {}
            if m["held_low"] is not None and ref.get("thickness_m") is not None and r["class"] in P.CLASSES:
                x["mortar_m3_bound_beside"] = [P._r(m["held_low"] * ref["thickness_m"], 9),
                                               P._r(m["held_high"] * ref["thickness_m"], 9)]
                x["bound_note"] = ("held line range x reference thickness: a bound beside the HELD line, never a "
                                   "figure" + (" (render: both ends are minimums)" if ref["kind"] == "MINIMUM" else ""))
    census = {"lines_read": len(lines), "excluded": len(excluded), "in_table": len(elements),
              "by_class": {str(k): sum(1 for r in t["rows"] if r["class"] == k) for k in (P.DRY, P.WET, None)},
              "not_in_scope": {code: [ln["line_id"] for ln in li["lines"] if ln["item_code"] == code]
                               for code in NOT_IN_SCOPE},
              "not_in_scope_why": NOT_IN_SCOPE,
              "exterior_spatter_faces_not_in_this_table": sum(1 for r in rows if r["family"].startswith("EXT"))}
    return {"schema": SCHEMA, "candidate": CANDIDATE, "method": P.METHOD_ID,
            "inputs": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
            "census": census, "excluded": excluded, "table": t}


CSV_COLS = ("line_id", "element_id", "item_code", "class", "layer", "area_m2", "area_label", "thickness_m",
            "thickness_kind", "thickness_basis", "status", "label", "mortar_m3", "mortar_m3_at_least",
            "mortar_m3_bound_beside", "sensitivity_m3_per_mm", "cement_bags", "sand_m3", "materials_status", "reason")


def to_csv(led):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in led["table"]["rows"]:
        for x in r["layers"]:
            v = {"line_id": r["id"], "element_id": r["element_id"], "item_code": r["item_code"],
                 "class": r["class"] or "CLASS_NOT_ESTABLISHED", **x}
            b = x.get("mortar_m3_bound_beside")
            v["mortar_m3_bound_beside"] = "" if b is None else f"{b[0]} .. {b[1]}"
            w.writerow(["" if v.get(c) is None else v.get(c) for c in CSV_COLS])
    return buf.getvalue()


def write(led, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "PLASTER_MATERIALS_T454.json").write_text(json.dumps(led, indent=1, ensure_ascii=False, sort_keys=True)
                                                     + "\n", encoding="utf-8")
    (out / "PLASTER_MATERIALS_T454.csv").write_text(to_csv(led), encoding="utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    led = build()
    write(led, argv[0] if argv else HERE / "out")
    print(json.dumps({"census": led["census"], "sums": led["table"]["sums"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
