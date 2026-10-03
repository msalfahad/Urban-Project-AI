"""Freeze round 6B's P7757 geometry for independent comparison.

§11. Five exports, each in CSV and JSON, each hashed, so that the next
operation — a supervised reconciliation against the architectural drawing
and the human measurement workbook — can be done by somebody who never
ran this engine.

Nothing here measures anything. It reads one run and writes it down.

    SPACE       one row per physical space, with all three authorities
    BOUNDARY    one row per side of every space polygon
    OPENING     one row per opening hypothesis and its host
    IDENTITY    one row per reconciled name
    DIMENSION   one row per authored dimension checked against geometry

A row says what the engine established AND what it did not. The columns
that say NOT_ESTABLISHED are the point of the export, not a gap in it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import round6a_selftest as round6a
from engine import round6b_selftest as round6b
from engine import semantic_seed as seeds_mod
from engine import single_line_partition as slp
from engine import wall_face_ownership as wface

EXPORT = "P7757_ROUND6B_GEOMETRY_EXPORT_V1"

# The engine has no floor model. Saying so in every row is more useful
# than leaving the column out and letting a reader assume one.
FLOOR_NOT_ESTABLISHED = "FLOOR_LEVEL_NOT_ESTABLISHED"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _labels(r) -> str:
    return " | ".join(str(t) for z in r.zones for t in z.label_observations)


def _basis_of(r) -> str:
    return (r.clear.basis if r.clear is not None
            else wface.BASIS_NOT_ESTABLISHED)


def _topology_of(r) -> str:
    if r.clear is not None and r.clear.topology_established:
        return slp.TOPOLOGY_ESTABLISHED
    return slp.TOPOLOGY_UNRESOLVED


def _clear_face_of(r) -> str:
    return (slp.CLEAR_FACE_ESTABLISHED
            if r.clear is not None and r.clear.basis_established
            else slp.CLEAR_FACE_NOT_ESTABLISHED)


def _material_of(r) -> str:
    return (slp.MATERIAL_ESTABLISHED
            if r.quantities.get(
                "MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM", 0.0) > 0.0
            else slp.MATERIAL_NOT_ESTABLISHED)


def _blockers(r) -> str:
    out = []
    c = r.clear
    if c is None:
        out.append("NO_CLEAR_MEASUREMENT")
    else:
        n = sum(1 for f in c.boundary_faces
                if f.basis == wface.BASIS_NOT_ESTABLISHED)
        p = sum(1 for f in c.boundary_faces
                if f.basis == wface.CLEAR_FACE_NOT_ESTABLISHED)
        if n:
            out.append(f"SIDES_NOTHING_ACCOUNTS_FOR={n}")
        if p:
            out.append(f"PARTITION_OF_UNKNOWN_THICKNESS={p}")
    rel = r._release()
    if rel.get("blocker"):
        out.append(str(rel["blocker"]))
    return " ; ".join(out)


def space_rows(rep, roles) -> list:
    role_of = ({v.space_id: v.role for v in roles.verdicts}
               if roles else {})
    ie_of = ({v.space_id: v.interior_exterior for v in roles.verdicts}
             if roles else {})
    build_of = ({v.space_id: getattr(v, "building", "")
                 for v in roles.verdicts} if roles else {})
    out = []
    for r in rep.rows:
        c = r.clear
        poly = c.polygon_wkt if c is not None else ""
        cx = cy = None
        per = None
        if poly:
            from shapely.wkt import loads

            try:
                g = loads(poly)
                cx, cy = g.centroid.x, g.centroid.y
                per = g.length / 1000.0
            except Exception:      # noqa: BLE001
                pass
        out.append({
            "space_id": r.space_id,
            "drawing_region_id": r.region_id,
            "floor": FLOOR_NOT_ESTABLISHED,
            "identity_raw": _labels(r),
            "identity_reconciled": (
                getattr(r.identity, "normalized_identity", "")
                if r.identity else ""),
            "identity_status": r.identity_status,
            "space_role": role_of.get(r.space_id, ""),
            "interior_exterior": ie_of.get(r.space_id, ""),
            "building_relationship": build_of.get(r.space_id, ""),
            "area_m2": (None if c is None else round(c.area_m2, 4)),
            "perimeter_m": (None if per is None else round(per, 3)),
            "centroid_x_mm": (None if cx is None else round(cx, 2)),
            "centroid_y_mm": (None if cy is None else round(cy, 2)),
            "principal_dim_x_mm": (None if c is None
                                   else c.principal_dims_mm[0]),
            "principal_dim_y_mm": (None if c is None
                                   else c.principal_dims_mm[1]),
            "measurement_basis": _basis_of(r),
            "TOPOLOGY_AUTHORITY": _topology_of(r),
            "CLEAR_FACE_AUTHORITY": _clear_face_of(r),
            "MATERIAL_WALL_AUTHORITY": _material_of(r),
            "material_established_length_m": round(r.quantities.get(
                "MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM", 0.0) / 1000, 3),
            "single_line_partition_length_m": round(r.quantities.get(
                "SINGLE_LINE_PARTITION_LENGTH_MM", 0.0) / 1000, 3),
            "recovered_boundary_length_m": round(r.quantities.get(
                "RECOVERED_BOUNDARY_LENGTH_MM", 0.0) / 1000, 3),
            "opening_length_m": round(r.quantities.get(
                "OPENING_LENGTH_MM", 0.0) / 1000, 3),
            "boundary_face_ids": " ".join(
                sorted({f.face_id for f in c.boundary_faces if f.face_id})
                if c else ()),
            "wall_band_ids": " ".join(
                sorted({f.wall_band_id for f in c.boundary_faces
                        if f.wall_band_id}) if c else ()),
            "opening_ids": " ".join(o.get("opening_id", "")
                                    for o in r.boundary_openings),
            "cad_provenance": " ".join(sorted({
                p for f in (c.boundary_faces if c else ())
                for p in f.cad_provenance})),
            "release_status": r._release()["status"],
            "blockers": _blockers(r),
            "polygon_wkt_mm": poly,
        })
    return out


def boundary_rows(rep) -> list:
    out = []
    for r in rep.rows:
        c = r.clear
        if c is None:
            continue
        for i, f in enumerate(c.boundary_faces, 1):
            out.append({
                "space_id": r.space_id,
                "drawing_region_id": r.region_id,
                "side_index": i,
                "axis": f.axis,
                "fixed_mm": round(f.fixed_mm, 2),
                "start_mm": round(f.interval_mm[0], 2),
                "end_mm": round(f.interval_mm[1], 2),
                "length_m": round(f.length_mm / 1000.0, 4),
                "measurement_basis": f.basis,
                "boundary_face_id": f.face_id,
                "wall_band_id": f.wall_band_id,
                "cad_provenance": " ".join(f.cad_provenance),
                "why_this_face": f.why,
            })
    return out


def opening_rows(rep) -> list:
    out = []
    status = {}
    if rep.matches is not None:
        status = {m.opening_id: m.status for m in rep.matches.matches}
    why = {}
    if rep.matches is not None:
        why = {m.opening_id: m.why for m in rep.matches.matches}
    for o in (rep.openings.openings if rep.openings else ()):
        out.append({
            "opening_id": o.opening_id,
            "drawing_region_id": getattr(o, "region_id", ""),
            "opening_class": o.opening_class,
            "evidence_grade": o.grade,
            "axis": o.axis,
            "fixed_mm": round(o.fixed_mm, 2),
            "start_mm": round(o.start_mm, 2),
            "end_mm": round(o.end_mm, 2),
            "width_mm": round(abs(o.end_mm - o.start_mm), 1),
            "wall_faces_mm": " ".join(str(round(v, 2))
                                      for v in (o.wall_faces_mm or ())),
            "may_close_boundary": o.may_close_boundary,
            "may_partition_rooms": o.may_partition_rooms,
            "host_bands": " ".join(o.host_bands),
            "host_status": status.get(o.opening_id, ""),
            "why": why.get(o.opening_id, ""),
            "cad_provenance": " ".join(o.symbol_ids),
        })
    return out


def identity_rows(rep) -> list:
    out = []
    if rep.identity is None:
        return out
    for g in rep.identity.groups:
        out.append({
            "place_id": getattr(g, "group_id", ""),
            "x_mm": round(g.x, 2),
            "y_mm": round(g.y, 2),
            "identity_status": g.identity_status,
            "normalized_identity": g.normalized_identity,
            "observations": " | ".join(o.text for o in g.observations),
            "independent_statements": g.supporting_observations,
            "cad_provenance": " ".join(
                str(getattr(o, "observation_id", "")) for o in g.observations),
        })
    return out


def dimension_rows(rep) -> list:
    out = []
    for r in rep.rows:
        for d in r.dimension_checks:
            row = {"space_id": r.space_id,
                   "drawing_region_id": r.region_id}
            row.update({k: v for k, v in dict(d).items()})
            out.append(row)
    return out


def _write(out_dir: Path, name: str, rows: list, notes: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    csv_path = out_dir / f"{name}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    payload = {"export": name, "rows": len(rows), "notes": notes,
               "records": rows}
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    json_path = out_dir / f"{name}.json"
    json_path.write_text(text + "\n", encoding="utf-8")
    return {
        "export": name,
        "rows": len(rows),
        "csv": str(csv_path),
        "json": str(json_path),
        "csv_sha256_24": _sha(csv_path.read_text(encoding="utf-8")),
        "json_sha256_24": _sha(text),
    }


def run(decode_json: str, out_dir: str) -> dict:
    # Every earlier suite must still hold before anything is written.
    r6a = round6a.assert_frozen()
    r6b = round6b.assert_frozen()

    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    roles = getattr(rep, "space_roles", None)
    out = Path(out_dir)

    exports = [
        _write(out, "P7757_ROUND6B_SPACE_EXPORT", space_rows(rep, roles),
               {"one_row_per": "physical space",
                "three_authorities": (
                    "TOPOLOGY, CLEAR_FACE and MATERIAL_WALL are three "
                    "different columns because they are three different "
                    "questions"),
                "floor": ("this engine has no floor model. The column says "
                          "so rather than being omitted")}),
        _write(out, "P7757_ROUND6B_BOUNDARY_EXPORT", boundary_rows(rep),
               {"one_row_per": "side of a space polygon",
                "measurement_basis": (
                    "CLEAR_FACE_NOT_ESTABLISHED means a single-line "
                    "partition holds this side and its thickness is "
                    "unknown. It is not the same as no face at all")}),
        _write(out, "P7757_ROUND6B_OPENING_EXPORT", opening_rows(rep),
               {"one_row_per": "opening hypothesis",
                "host_status": "an opening with no host closes no room"}),
        _write(out, "P7757_ROUND6B_IDENTITY_EXPORT", identity_rows(rep),
               {"one_row_per": "reconciled place",
                "note": "a name is attached to geometry, never the reverse"}),
        _write(out, "P7757_ROUND6B_DIMENSION_EXPORT", dimension_rows(rep),
               {"one_row_per": "authored dimension checked against a span",
                "note": ("a dimension is evidence. It has never been used "
                         "as a correction factor")}),
    ]

    manifest = {
        "export": EXPORT,
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d"},
        "engine": {
            "SINGLE_LINE_PARTITION_HASH": slp.model_hash(),
            "WALL_FACE_OWNERSHIP_HASH": wface.model_hash(),
            "ROUND_6A_SYNTHETIC_HASH": r6a["ROUND_6A_SYNTHETIC_HASH"],
            "ROUND_6B_SYNTHETIC_HASH": r6b["ROUND_6B_SYNTHETIC_HASH"],
        },
        "suites_that_passed_before_writing": {
            "round_6a": f"{r6a['passed']}/{r6a['cases']}",
            "round_6b": f"{r6b['passed']}/{r6b['cases']}",
        },
        "exports": exports,
        "what_this_is_for": (
            "an independent supervised reconciliation against the "
            "architectural drawing and the human measurement workbook. "
            "The workbook is REFERENCE EVIDENCE, not absolute truth, and "
            "the engine is not altered during that comparison"),
    }
    manifest["ROUND6B_EXPORT_MANIFEST_HASH"] = _sha(
        json.dumps(manifest, sort_keys=True, default=str))
    (out / "ROUND6B_EXPORT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str)
        + "\n", encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    man = run(a.decode_json, a.out_dir)
    print(json.dumps({
        "ROUND6B_EXPORT_MANIFEST_HASH": man["ROUND6B_EXPORT_MANIFEST_HASH"],
        "exports": [{k: e[k] for k in ("export", "rows", "csv_sha256_24")}
                    for e in man["exports"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
