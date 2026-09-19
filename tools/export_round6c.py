"""Freeze round 6C's P7757 register for independent audit.

§0. The register is the deliverable of round 6C and no bundle of it was
ever handed over. This writes one, in CSV and JSON, hashed, and refuses
to write anything if the engine has moved since the round-6C freeze:

    SPACE_REGISTER        one row per candidate, with what it IS
    BOUNDARY              one row per side of every space polygon
    OPENING               one row per opening hypothesis and its host
    IDENTITY              one row per reconciled name
    DIMENSION             one row per authored dimension checked
    DRAWING_REGION_ROLE   one row per region: what it shows
    FLOOR_ASSIGNMENT      one row per region: which floor, and on whose say
    UNMAPPED_LABELS       one row per label that resolved to no room
    UNRESOLVED_SPACES     one row per candidate nobody could classify
    NON_SPACE_ARTIFACTS   one row per polygon that is the sheet talking
    SUPER_REGIONS         one row per container of spaces
    FALSE_NEGATIVE_CANDIDATES  the four the review named, and the verdict
    EXCEPTIONS            every refusal in the run, in one table

Nothing here measures anything. It reads one run and writes it down, and
the columns that say NOT_ESTABLISHED are the point of the export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import drawing_role as drole
from engine import floor_register as freg
from engine import round6a_selftest as round6a
from engine import round6b_selftest as round6b
from engine import round6c_selftest as round6c
from engine import semantic_seed as seeds_mod
from engine import single_line_partition as slp
from engine import space_register as sreg
from engine import wall_face_ownership as wface
from tools import export_round6b as x6b
from tools import run_round6c as r6c

EXPORT = "P7757_ROUND6C_REGISTER_EXPORT_V1"
ROUND_6C_COMMIT = "b5a2ce1"

# The engine state this bundle claims to be. If the live code does not
# compute these, the bundle would not be round 6C and is not written.
ROUND_6C_HASHES = {
    "DRAWING_ROLE_HASH": "db18783807179a48ccfd57a7",
    "SPACE_REGISTER_HASH": "a0e9ecb7a1aa008da91a5da9",
    "ROUND_6C_SYNTHETIC_HASH": "c59e81b1ea572539377804da",
    "SINGLE_LINE_PARTITION_HASH": "2b9480e67e799c2b3d1f837f",
    "WALL_FACE_OWNERSHIP_HASH": "b2529201eefb569dc651db84",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _live_hashes() -> dict:
    return {
        "DRAWING_ROLE_HASH": drole.model_hash(),
        "SPACE_REGISTER_HASH": sreg.model_hash(),
        "ROUND_6C_SYNTHETIC_HASH": round6c.freeze_hash(),
        "SINGLE_LINE_PARTITION_HASH": slp.model_hash(),
        "WALL_FACE_OWNERSHIP_HASH": wface.model_hash(),
    }


def _head_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, check=True).stdout.strip()
    except Exception:      # noqa: BLE001
        return ""


# ------------------------------------------------------------ the tables

def register_rows(register, rows) -> list:
    dims = {r["space_id"]: r for r in rows}
    out = []
    for e in register.entries:
        r = dims.get(e.space_id, {})
        poly = r.get("polygon")
        rec = e.record()
        out.append({
            "physical_space_id": e.space_id,
            "drawing_region_id": e.region_id,
            "floor": e.floor_level,
            "candidate_role": e.candidate_role,
            "is_physical_space": e.is_space,
            "may_release": e.may_release,
            "register_relation": e.relation,
            "parent_super_region": e.parent_id,
            "children": " ".join(e.children),
            "duplicates": " ".join(e.duplicates),
            "overlaps": " ".join(e.overlaps),
            "repeated_in_regions": " ".join(e.repeated_in),
            "area_m2": round(e.area_m2, 4),
            "principal_dim_x_mm": (rec["principal_dims_mm"] or [None])[0],
            "principal_dim_y_mm": (rec["principal_dims_mm"] + [None, None])[1],
            "perimeter_m": (round(poly.length / 1000.0, 3)
                            if poly is not None else None),
            "measurement_basis": e.basis,
            "raw_label": e.label_raw,
            "normalized_identity": e.normalized_identity,
            "identity_authority": e.identity_authority,
            "geometry_authority": e.geometry_authority,
            "release_status": e.release_status,
            "geometry_gate_status": e.geometry_gate_status,
            "withheld_because": " ".join(e.withheld_because),
            "blockers": " ".join(e.blockers),
            "cad_provenance": " ".join(e.cad_provenance),
            "why": e.why,
            "polygon_wkt_mm": (poly.wkt if poly is not None else ""),
        })
    return out


def region_role_rows(roles) -> list:
    out = []
    for r in roles.roles:
        rec = r.record()
        out.append({
            "drawing_region_id": r.region_id,
            "drawing_role": r.drawing_role,
            "role_provenance": r.role_provenance,
            "confidence": r.confidence,
            "may_release_room_quantities": r.may_release_rooms,
            "x0_mm": rec["extent_mm"][0] if rec["extent_mm"] else None,
            "y0_mm": rec["extent_mm"][1] if rec["extent_mm"] else None,
            "x1_mm": rec["extent_mm"][2] if rec["extent_mm"] else None,
            "y1_mm": rec["extent_mm"][3] if rec["extent_mm"] else None,
            "spaces": rec["counts"].get("spaces"),
            "openings": rec["counts"].get("openings"),
            "wall_bands": rec["counts"].get("wall_bands"),
            "room_stamps": rec["counts"].get("room_stamps"),
            "site_boundary": rec["counts"].get("site_boundary"),
            "title_evidence": " | ".join(r.title_evidence),
            "plan_evidence": " ".join(r.evidence),
            "why": r.why,
        })
    return out


def floor_rows(roles, supervised_note: str) -> list:
    return [{
        "drawing_region_id": r.region_id,
        "floor_level": r.floor_level,
        "floor_provenance": r.floor_provenance,
        "drawing_role": r.drawing_role,
        "may_release_room_quantities": r.may_release_rooms,
        "supervised_source": (supervised_note
                              if r.floor_provenance == drole.SUPERVISED
                              else ""),
        "why": ("no title text in this drawing decodes, so no floor is "
                "derived from it" if r.floor_provenance == drole.DERIVED
                and r.floor_level == drole.FLOOR_NOT_ESTABLISHED
                else r.why),
    } for r in roles.roles]


def label_rows(register, only_exceptions: bool) -> list:
    out = []
    for v in register.labels:
        if only_exceptions and v.status != sreg.LABEL_EXCEPTION:
            continue
        out.append({
            "raw_text": v.text,
            "x_mm": round(v.x, 2),
            "y_mm": round(v.y, 2),
            "drawing_region_id": v.region_id,
            "floor": v.floor_level,
            "label_status": v.status,
            "physical_space_id": v.space_id,
            "candidate_spaces": " ".join(v.candidates),
            "why": v.why,
        })
    return out


def _entries(register, role) -> list:
    return [{
        "physical_space_id": e.space_id,
        "drawing_region_id": e.region_id,
        "floor": e.floor_level,
        "candidate_role": e.candidate_role,
        "area_m2": round(e.area_m2, 4),
        "measurement_basis": e.basis,
        "raw_label": e.label_raw,
        "release_status": e.release_status,
        "children": " ".join(e.children),
        "repeated_in_regions": " ".join(e.repeated_in),
        "blockers": " ".join(e.blockers),
        "why": e.why,
    } for e in register.entries if e.candidate_role == role]


def exception_rows(register, roles, linings, false_negatives) -> list:
    """Every refusal in the run, in one table, with what was refused."""
    out = []
    for v in register.labels:
        if v.status == sreg.LABEL_EXCEPTION:
            out.append({"exception": "LABEL_RESOLVED_TO_NO_ROOM",
                        "subject": v.text, "drawing_region_id": v.region_id,
                        "floor": v.floor_level, "reason": v.why,
                        "what_was_refused": "an identity for this label"})
    for e in register.entries:
        for b in e.blockers:
            out.append({"exception": "RELEASE_BLOCKED",
                        "subject": e.space_id,
                        "drawing_region_id": e.region_id,
                        "floor": e.floor_level, "reason": b,
                        "what_was_refused": (
                            f"{round(e.area_m2, 4)} m2 of geometry")})
        if e.candidate_role == sreg.UNRESOLVED:
            out.append({"exception": "CANDIDATE_UNRESOLVED",
                        "subject": e.space_id,
                        "drawing_region_id": e.region_id,
                        "floor": e.floor_level, "reason": e.why,
                        "what_was_refused": "a role for this polygon"})
    for r in roles.roles:
        if not r.may_release_rooms:
            out.append({
                "exception": "REGION_MAY_NOT_RELEASE_ROOMS",
                "subject": r.region_id, "drawing_region_id": r.region_id,
                "floor": r.floor_level,
                "reason": (f"role {r.drawing_role}, floor {r.floor_level}"),
                "what_was_refused": "every room quantity in this region"})
    for _k, st in sorted(linings.items()):
        out.append({
            "exception": "BAND_IS_A_FITTING_NOT_A_WALL",
            "subject": st.lining_id, "drawing_region_id": "",
            "floor": "",
            "reason": (f"it stands on {st.wall_id}; shared face "
                       f"{round(st.shared_face_mm, 1)}, front face "
                       f"{round(st.far_face_mm, 1)}"),
            "what_was_refused": ("a clear-face authority on its front "
                                 "side")})
    for fn in false_negatives:
        out.append({
            "exception": f"AUDIT_AREA_{fn['verdict']}",
            "subject": fn.get("space_id", str(fn["audit_area_m2"])),
            "drawing_region_id": fn.get("region_id", ""),
            "floor": "",
            "reason": " ".join(fn.get("gates_holding_it", ())),
            "what_was_refused": f"{fn['audit_area_m2']} m2 the audit names"})
    return out


# ---------------------------------------------------------------- the run

def run(decode_json: str, out_dir: str, *, supervised_json: str = "") -> dict:
    """Write the bundle, after proving the engine is still round 6C."""
    live = _live_hashes()
    moved = {k: {"round_6c": v, "live": live.get(k, "")}
             for k, v in ROUND_6C_HASHES.items() if live.get(k) != v}
    if moved:
        raise SystemExit(
            "the engine has moved since the round-6C freeze, so this "
            "bundle would not be round 6C: "
            + json.dumps(moved, indent=2))

    r6a = round6a.assert_frozen()
    r6b = round6b.assert_frozen()
    r6cs = round6c.assert_frozen()

    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))

    supervised, note = {}, "none supplied"
    if supervised_json and Path(supervised_json).exists():
        data = json.loads(Path(supervised_json).read_text(encoding="utf-8"))
        supervised = data.get("assignments", {})
        note = supervised_json

    built = freg.assemble(nd, rep, supervised=supervised)
    register, roles, rows = built["register"], built["roles"], built["rows"]
    false_negatives = r6c._false_negative_analysis(rows, register)

    out = Path(out_dir)
    w = x6b._write
    exports = [
        w(out, "P7757_ROUND6C_SPACE_REGISTER",
          register_rows(register, rows),
          {"one_row_per": "candidate polygon, with what it IS",
           "four_areas": ("MEASURED_CANDIDATE, PHYSICAL_SPACE, "
                          "RELEASE_ELIGIBLE_GEOMETRY and "
                          "TRADE_MEASUREMENT are four different numbers "
                          "and only the last may price anything"),
           "may_release": ("a space, not a duplicate, not a container of "
                           "spaces, and not a stair")}),
        w(out, "P7757_ROUND6C_BOUNDARY", x6b.boundary_rows(rep),
          {"one_row_per": "side of a space polygon",
           "note": "unchanged from round 6B; no geometry moved in 6C"}),
        w(out, "P7757_ROUND6C_OPENING", x6b.opening_rows(rep),
          {"one_row_per": "opening hypothesis",
           "note": "an opening with no host closes no room"}),
        w(out, "P7757_ROUND6C_IDENTITY", x6b.identity_rows(rep),
          {"one_row_per": "reconciled place",
           "note": "a name is attached to geometry, never the reverse"}),
        w(out, "P7757_ROUND6C_DIMENSION", x6b.dimension_rows(rep),
          {"one_row_per": "authored dimension checked against a span",
           "note": ("a dimension is evidence. It has never been used as a "
                    "correction factor")}),
        w(out, "P7757_ROUND6C_DRAWING_REGION_ROLE", region_role_rows(roles),
          {"one_row_per": "drawing region",
           "note": ("only FLOOR_PLAN and ROOF_PLAN may release room "
                    "quantities, and only with a floor")}),
        w(out, "P7757_ROUND6C_FLOOR_ASSIGNMENT", floor_rows(roles, note),
          {"one_row_per": "drawing region",
           "note": ("P7757 carries no decodable title text, so its floors "
                    "are SUPERVISED_AUDIT, carried as supplied")}),
        w(out, "P7757_ROUND6C_UNMAPPED_LABELS",
          label_rows(register, True),
          {"one_row_per": "authored label that resolved to no room"}),
        w(out, "P7757_ROUND6C_UNRESOLVED_SPACES",
          _entries(register, sreg.UNRESOLVED),
          {"one_row_per": "candidate nobody could classify"}),
        w(out, "P7757_ROUND6C_NON_SPACE_ARTIFACTS",
          _entries(register, sreg.DRAWING_ARTIFACT),
          {"one_row_per": "polygon that is the sheet talking about itself"}),
        w(out, "P7757_ROUND6C_SUPER_REGIONS",
          _entries(register, sreg.SUPER_REGION),
          {"one_row_per": "container of candidates that are spaces",
           "note": ("a container of candidates that are NOT spaces is not "
                    "a super-region: nothing would be counted twice")}),
        w(out, "P7757_ROUND6C_FALSE_NEGATIVE_CANDIDATES", false_negatives,
          {"one_row_per": "area the independent review believes is a room",
           "verdicts": ("CORRECTLY_BLOCKED means no geometry was ever "
                        "established. FALSE_NEGATIVE_RELEASE_GATE means "
                        "the geometry IS established and a classification "
                        "the review contradicts is holding it")}),
        w(out, "P7757_ROUND6C_EXCEPTIONS",
          exception_rows(register, roles, built["linings"], false_negatives),
          {"one_row_per": "refusal, of any kind, anywhere in the run"}),
    ]

    manifest = {
        "export": EXPORT,
        "round_6c_commit": ROUND_6C_COMMIT,
        "exported_at_commit": _head_commit(),
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d",
                   "decode": decode_json},
        "supervised_floor_assignment": note,
        "engine": live,
        "synthetic": {
            "ROUND_6A_SYNTHETIC_HASH": r6a["ROUND_6A_SYNTHETIC_HASH"],
            "ROUND_6B_SYNTHETIC_HASH": r6b["ROUND_6B_SYNTHETIC_HASH"],
            "ROUND_6C_SYNTHETIC_HASH": r6cs["ROUND_6C_SYNTHETIC_HASH"],
        },
        "suites_that_passed_before_writing": {
            "round_6a": f"{r6a['passed']}/{r6a['cases']}",
            "round_6b": f"{r6b['passed']}/{r6b['cases']}",
            "round_6c": f"{r6cs['passed']}/{r6cs['cases']}",
        },
        "areas_kept_apart": register.areas(),
        "completeness_per_floor": sreg.completeness(register),
        "exports": exports,
        "what_this_is_for": (
            "an independent audit of the round-6C register before round 6D "
            "changes anything. The engine is not altered during that audit"),
        "what_this_is_not": (
            "no FunctionalZone, no TradeMeasurementZone, no ceramic, no "
            "waste, no pricing and no BOQ"),
    }
    manifest["ROUND6C_EXPORT_MANIFEST_HASH"] = _sha(
        json.dumps(manifest, sort_keys=True, default=str))
    man_path = out / "ROUND6C_EXPORT_MANIFEST.json"
    man_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str)
        + "\n", encoding="utf-8")

    archive = out / "P7757_ROUND6C_EXPORT.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for e in exports:
            for key in ("csv", "json"):
                p = Path(e[key])
                tar.add(p, arcname=f"P7757_ROUND6C_EXPORT/{p.name}")
        tar.add(man_path,
                arcname="P7757_ROUND6C_EXPORT/ROUND6C_EXPORT_MANIFEST.json")
    manifest["archive"] = str(archive)
    manifest["archive_sha256_24"] = hashlib.sha256(
        archive.read_bytes()).hexdigest()[:24]
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--supervised", default="")
    a = ap.parse_args(argv)
    man = run(a.decode_json, a.out_dir, supervised_json=a.supervised)
    print(json.dumps({
        "ROUND6C_EXPORT_MANIFEST_HASH": man["ROUND6C_EXPORT_MANIFEST_HASH"],
        "archive": man["archive"],
        "archive_sha256_24": man["archive_sha256_24"],
        "exports": [{k: e[k] for k in ("export", "rows", "csv_sha256_24")}
                    for e in man["exports"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
