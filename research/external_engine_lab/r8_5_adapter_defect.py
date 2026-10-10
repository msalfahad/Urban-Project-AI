"""R8.5 follow-up — ACTIVE-PATH DEFECT REPORT: the Al Rashed project reader's LWPOLYLINE closed test.

Report only. Nothing here changes the adapter, a published BOQ, a frozen quantity or an owner answer.

research/qs_wall_treatment_01/pa09/alrashed/geometry.py `_segments` closes an LWPOLYLINE when
`flag & 1`. In the decoded DWG the closed bit is 512 (engine/cad_adapter.py reads `& 0x200`); bit 1
is not the closed bit. Closed wall / column outlines therefore lose their closing edge in that reader.

Measured here, from the adapter's own functions (read-only, patched in memory for the counterfactual
and restored):
  * the closing edges the reader drops, per floor and layer, inside the floor windows;
  * the room-level effect of correcting ONLY that bit (everything else in the adapter unchanged);
  * the cross-reference to the R8.5 canonical native comparison (K1 geometry vs the adapter reading),
    which shows which canonical deltas the defect alone explains.

    python3 research/external_engine_lab/r8_5_adapter_defect.py [register_path]
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.qs_wall_treatment_01.pa09.alrashed import geometry as G, takeoff as TK   # noqa: E402

GEOMETRY_PY = ROOT / "research/qs_wall_treatment_01/pa09/alrashed/geometry.py"
CAD_ADAPTER = ROOT / "engine/cad_adapter.py"
R85_DIFF = ROOT / "research/external_engine_lab/outputs/r8_5/SHADOW_VALUE_DIFF.json"
OUT = ROOT / "tests/r8_5/registers/R8_ADAPTER_DEFECT_CLOSED_FLAG.json"
EPS = 5e-5          # adapter areas are printed to 1e-4 m2
PRINT_TOL = 1.0001e-4   # one unit of the printed precision: the R8.5 NATIVE_WITHIN_NUMERIC_TOLERANCE bound


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _line_of(path: Path, needle: str) -> int | None:
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if needle in line:
            return i
    return None


def _flag(o) -> int:
    return int(o.get("flag", 0) or 0)


def dropped_closing_edges(ents):
    """Closed (bit 512) wall / column LWPOLYLINEs whose closing edge the reader drops, and of those the
    closing edges `_segments` would have kept (inside the floor window, axis-aligned, non-zero)."""
    layers = G.WALL_LAYERS + G.COLUMN_LAYERS
    affected = [o for o in ents if o.get("entity") == "LWPOLYLINE" and o.get("_layer") in layers
                and _flag(o) & 512 and not _flag(o) & 1 and len(o.get("points") or []) > 2]
    per_floor = {}
    for floor in TK.FLOORS:
        edges = Counter()
        for o in affected:
            pts = o["points"]
            closing = {"entity": "LINE", "_layer": o["_layer"], "start": pts[-1], "end": pts[0]}
            if G._segments([closing], (o["_layer"],), G.WINDOWS[floor]):
                edges[o["_layer"]] += 1
        per_floor[floor] = dict(edges)
    return affected, per_floor


def rooms(ents):
    """{floor: {bbox: room}} for the rows the adapter publishes. ROOM_REF is positional (renumbered when
    cells change), so rooms are compared by their grid bounding box, never by ref."""
    out = {}
    for floor in TK.FLOORS:
        comps = G.rooms(G.grid(ents, G.WINDOWS[floor]))
        _, _, _, rows, closure = TK.floor_rows(ents, floor)
        by_ref = {r["ROOM_REF"]: r for r in rows}
        rs = {}
        for k, c in enumerate(comps):
            r = by_ref.get(f"{floor[:2]}-{k:03d}")
            if r is not None:
                rs[tuple(round(v, 4) for v in c["BBOX"])] = {"room_ref": r["ROOM_REF"], "name": r.get("NAME"),
                                                           "area_m2": r["AREA_M2"]}
        out[floor] = {"rows": rs, "closure_residual_m2": closure["RESIDUAL_M2"]}
    return out


def counterfactual(ents):
    """Rooms as the adapter computes them, then with ONLY the closed bit read correctly (in memory)."""
    orig = G._segments

    def corrected(ents_, layers, window):
        patched = []
        for o in ents_:
            if o.get("entity") == "LWPOLYLINE" and _flag(o) & 512 and not _flag(o) & 1:
                o = dict(o)
                o["flag"] = _flag(o) | 1        # make the reader's own test see the DWG closed bit
            patched.append(o)
        return orig(patched, layers, window)

    base = rooms(ents)
    G._segments = corrected
    try:
        fixed = rooms(ents)
    finally:
        G._segments = orig
    assert G._segments is orig
    return base, fixed


def room_effect(base, fixed):
    out = []
    for floor in TK.FLOORS:
        b, f = base[floor]["rows"], fixed[floor]["rows"]
        for key in sorted(set(b) | set(f)):
            rb, rf = b.get(key), f.get(key)
            if rb and rf:
                d = rf["area_m2"] - rb["area_m2"]
                state = ("UNCHANGED" if abs(d) <= EPS else "WITHIN_NUMERIC_TOLERANCE" if abs(d) <= PRINT_TOL
                         else "AREA_CHANGED")
            else:
                d, state = None, "ONLY_IN_ADAPTER" if rb else "ONLY_WHEN_CORRECTED"
            out.append({"floor": floor, "bbox": list(key), "adapter_room_ref": rb["room_ref"] if rb else None,
                        "name": (rb or rf)["name"], "state": state,
                        "adapter_area_m2": rb["area_m2"] if rb else None,
                        "corrected_area_m2": rf["area_m2"] if rf else None,
                        "delta_m2": round(d, 4) if d is not None else None})
    return out


def cross_reference(effect):
    """R8.5 canonical-vs-adapter native comparison (keyed by the adapter's published ROOM_REF), against
    the defect-only counterfactual (keyed by bounding box)."""
    if not R85_DIFF.exists():
        return {"status": "NOT_RUN", "reason": f"{R85_DIFF.relative_to(ROOT)} not generated in this checkout"}
    can = json.loads(R85_DIFF.read_text())["ALRASHED"]["rooms"]
    eff = {(e["floor"], e["adapter_room_ref"]): e for e in effect if e["adapter_room_ref"]}
    rows = []
    for r in can:
        if r["native_check"] not in ("CHANGED_NATIVE_AREA", "CHANGED_NATIVE_TOPOLOGY"):
            continue
        e = eff.get((r["floor"], r["room_ref"]))
        if e is None:
            explained = None
        elif r["native_check"] == "CHANGED_NATIVE_AREA":
            explained = e["state"] == "AREA_CHANGED" and abs(e["corrected_area_m2"] - r["canonical_native_area"]) <= EPS
        else:                                             # canonical lost this room: so must the corrected reader
            explained = e["state"] == "ONLY_IN_ADAPTER"
        rows.append({"floor": r["floor"], "room_ref": r["room_ref"], "r8_5_native_check": r["native_check"],
                     "r8_5_canonical_native_area": r.get("canonical_native_area"),
                     "adapter_area_m2": e["adapter_area_m2"] if e else r.get("current_native_area"),
                     "defect_only_corrected_area_m2": e["corrected_area_m2"] if e else None,
                     "defect_only_state": e["state"] if e else "NOT_FOUND",
                     "explained_by_defect_alone": explained})
    return {"status": "RUN", "native_checks": dict(Counter(r["native_check"] for r in can)),
            "changed_rooms": rows,
            "explained_by_defect_alone": sum(1 for x in rows if x["explained_by_defect_alone"]),
            "not_explained": sum(1 for x in rows if x["explained_by_defect_alone"] is False),
            "not_found": sum(1 for x in rows if x["explained_by_defect_alone"] is None)}


def main(out: Path = OUT):
    sha_before = _sha(GEOMETRY_PY)
    ents = G.load()
    affected, per_floor = dropped_closing_edges(ents)
    base, fixed = counterfactual(ents)
    effect = room_effect(base, fixed)
    changed = [e for e in effect if e["state"] != "UNCHANGED"]
    sha_after = _sha(GEOMETRY_PY)
    ba092 = next((e for e in effect if e["adapter_room_ref"] == "BA-092"), None)
    reg = {
        "SCHEMA": "URBAN_R8_5_ACTIVE_PATH_DEFECT_V1",
        "defect_id": "ADAPTER-LWPOLYLINE-CLOSED-BIT",
        "status": "REPORTED_NOT_FIXED",
        "location": {"file": str(GEOMETRY_PY.relative_to(ROOT)), "function": "_segments",
                     "line": _line_of(GEOMETRY_PY, 'o.get("flag", 0) & 1'),
                     "reads": "flag & 1"},
        "reference_reading": {"file": str(CAD_ADAPTER.relative_to(ROOT)),
                              "line": _line_of(CAD_ADAPTER, "& 0x200)"), "reads": "flag & 0x200 (512)"},
        "mechanism": ("the decoded LWPOLYLINE closed bit is 512; the project reader tests bit 1, so a closed wall or "
                      "column outline loses its closing edge and the grid can merge or split cells across it"),
        "affected_closed_outlines": {"total_on_wall_or_column_layers": len(affected),
                                     "by_layer": dict(Counter(o["_layer"] for o in affected))},
        "dropped_closing_edges_in_floor_windows": per_floor,
        "dropped_closing_edges_total": sum(sum(v.values()) for v in per_floor.values()),
        "defect_only_counterfactual": {
            "method": "adapter functions unchanged except that `_segments` sees the closed bit; patched in memory and restored",
            "rooms_compared": len(effect), "states": dict(Counter(e["state"] for e in effect)),
            "closure_residual_m2": {fl: [base[fl]["closure_residual_m2"], fixed[fl]["closure_residual_m2"]]
                                    for fl in TK.FLOORS},
            "changed": changed},
        "r8_5_cross_reference": cross_reference(effect),
        "coincidence_with_protected_value": {
            "room": "BA-092",
            "adapter_area_m2": ba092["adapter_area_m2"] if ba092 else None,
            "defect_only_corrected_area_m2": ba092["corrected_area_m2"] if ba092 else None,
            "note": ("the corrected value 146.7697 is the column-net figure on the R8.3 anti-calibration list; the "
                     "closing edges of the col.str outlines are what deduct the column footprints from the room. "
                     "Whether columns are deducted from this room is an UNDECIDED trade-rule question: correcting the "
                     "reader would silently decide it. The defect fix and the column-deduction decision must be "
                     "taken separately, the decision first, by its owner."),
            "decides_trade_rule": False},
        "no_change_attestation": {
            "geometry_py_sha256_before": sha_before, "geometry_py_sha256_after": sha_after,
            "geometry_py_unchanged": sha_before == sha_after,
            "published_boqs_changed": False, "frozen_quantities_changed": False, "owner_answers_changed": False,
            "benchmark_truth_changed": False},
        "required_before_any_fix": [
            "owner decision on column deduction for the affected rooms (trade rule; R9 scope, not R8)",
            "fix through the migration path (canonical K1 geometry), not by editing the adapter in place",
            "re-issue of any affected quantity under a new version with supersession, never an overwrite",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: reg[k] for k in ("affected_closed_outlines", "dropped_closing_edges_in_floor_windows",
                                          "dropped_closing_edges_total")}, indent=1))
    print("states", reg["defect_only_counterfactual"]["states"])
    for c in changed:
        print("  ", c)
    xr = reg["r8_5_cross_reference"]
    print("xref", {k: v for k, v in xr.items() if k != "changed_rooms"})
    return reg


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
