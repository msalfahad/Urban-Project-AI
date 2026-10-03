"""Export round 6D: the register, the pantry, the stairs, hashed.

§18. Fifteen tables in CSV and JSON, and a manifest that carries the
commit, the source, every engine hash, the synthetic hashes and a hash
per file — so the round can be audited by somebody who never ran it.

    SPACE_REGISTER          one row per candidate, with what it IS
    FUNCTIONAL_ZONE         one row per zone. A zone creates no wall
    PANTRY_ANALYSIS         openness, host walls, and what is not known
    STAIR_ASSEMBLY          one row per staircase
    STAIR_FLIGHT            one row per flight
    STAIR_TREAD             one row per tread, from its own polygon
    STAIR_RISER             one row per riser, mostly NOT ESTABLISHED
    STAIR_LANDING           one row per landing
    FITTING_BAND            which bands are furniture, and on what
    WALL_STRETCH_OWNERSHIP  which stretches of which line each wall owns
    BOUNDARY / OPENING / IDENTITY / DIMENSION / EXCEPTIONS
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
from engine import fitting_band as fband
from engine import floor_register as freg
from engine import functional_zone as fz
from engine import physical_wall as pwall
from engine import round6d_selftest as r6d
from engine import semantic_seed as seeds_mod
from engine import single_line_partition as slp
from engine import space_register as sreg
from engine import stair_assembly as stair
from engine import wall_face_ownership as wface
from tools import export_round6b as x6b
from tools import export_round6c as x6c
from tools import run_round6c as r6c
from tools import run_round6d as r6dr

EXPORT = "P7757_ROUND6D_EXPORT_V1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:      # noqa: BLE001
        return ""


def zone_rows(zones) -> list:
    return [z.record() for z in zones.zones]


def pantry_rows(zones) -> list:
    return [p.record() for p in zones.pantries]


def fitting_rows(rep) -> list:
    out = []
    for f in rep.fittings:
        for _k, st in sorted((f.fittings or {}).items()):
            row = st.record()
            row["drawing_region_id"] = f.region_id
            out.append(row)
    return out


def stretch_rows(rep) -> list:
    out = []
    for wr in rep.walls:
        for w in wr.walls:
            for i, (lo, hi) in enumerate(w.owned_mm, 1):
                out.append({
                    "wall_band_id": w.wall_id,
                    "drawing_region_id": w.region_id,
                    "axis": w.axis,
                    "face_a_mm": round(w.face_a_mm, 2),
                    "face_b_mm": round(w.face_b_mm, 2),
                    "thickness_mm": round(w.thickness_mm, 1),
                    "stretch_index": i,
                    "start_mm": round(lo, 2),
                    "end_mm": round(hi, 2),
                    "length_m": round((hi - lo) / 1000.0, 3),
                    "both_faces_drawn": any(
                        min(hi, b) - max(lo, a) > 1.0
                        for a, b in w.drawn_mm),
                    "pairing_evidence": " ".join(w.evidence),
                })
    return out


def assembly_rows(rep) -> list:
    out = []
    for s in rep.stairs:
        for a in s.assemblies:
            rec = a.record()
            net = rec.pop("MEASURED_NET")
            rec.pop("flights", None)
            rec.pop("landings", None)
            rec.update({f"NET_{k}": v for k, v in net.items()
                        if k != "this_is"})
            out.append(rec)
    return out


def flight_rows(rep) -> list:
    out = []
    for s in rep.stairs:
        for a in s.assemblies:
            for f in a.flights:
                rec = f.record()
                rec.pop("treads", None)
                rec.pop("risers", None)
                rec["stair_id"] = a.stair_id
                rec["drawing_region_id"] = a.region_id
                out.append(rec)
    return out


def tread_rows(rep) -> list:
    return [dict(t.record(), stair_id=a.stair_id, flight_id=f.flight_id,
                 drawing_region_id=a.region_id)
            for s in rep.stairs for a in s.assemblies for f in a.flights
            for t in f.treads]


def riser_rows(rep) -> list:
    return [dict(r.record(), stair_id=a.stair_id, flight_id=f.flight_id,
                 drawing_region_id=a.region_id)
            for s in rep.stairs for a in s.assemblies for f in a.flights
            for r in f.risers]


def landing_rows(rep) -> list:
    return [dict(x.record(), stair_id=a.stair_id,
                 drawing_region_id=a.region_id)
            for s in rep.stairs for a in s.assemblies for x in a.landings]


def exception_rows(rep, register, roles, zones, report) -> list:
    out = x6c.exception_rows(
        register, roles,
        {k: v for f in rep.fittings for k, v in (f.fittings or {}).items()},
        report["C_register_changes_since_round_6c"][
            "false_negative_candidates"])
    for p in zones.pantries:
        for ex in p.exceptions:
            out.append({"exception": ex, "subject": p.pantry_zone_id,
                        "drawing_region_id": p.region_id,
                        "floor": p.floor_level, "reason": p.openness,
                        "what_was_refused": "a pantry wall-tile quantity"})
    for s in rep.stairs:
        for a in s.assemblies:
            for ex in a.exceptions:
                out.append({"exception": ex, "subject": a.stair_id,
                            "drawing_region_id": a.region_id, "floor": "",
                            "reason": "a plan carries no height",
                            "what_was_refused": "a riser or tread quantity"})
        for x in s.refused:
            out.append({"exception": x["why"], "subject": x["run_id"],
                        "drawing_region_id": s.region_id, "floor": "",
                        "reason": f"{x['lines']} parallel lines",
                        "what_was_refused": "a stair assembly"})
    return out


def run(decode_json: str, out_dir: str, *, supervised_json: str = "",
        sections_json: str = "") -> dict:
    r6ds = r6d.assert_frozen()
    report = r6dr.run(decode_json, supervised_json=supervised_json,
                      sections_json=sections_json)

    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    sections = {}
    if sections_json and Path(sections_json).exists():
        sections = json.loads(Path(sections_json).read_text(
            encoding="utf-8")).get("sections", {})
    rep = measure.measure(
        nd, cprofile.build(nd), semantic=seeds_mod.classify(nd.texts),
        sections=sections,
        project_rules={"stair_finish_rule": r6dr.P7757_STAIR_FINISH})
    supervised, note = {}, "none supplied"
    if supervised_json and Path(supervised_json).exists():
        supervised = json.loads(Path(supervised_json).read_text(
            encoding="utf-8")).get("assignments", {})
        note = supervised_json
    built = freg.assemble(nd, rep, supervised=supervised)
    register, roles = built["register"], built["roles"]
    rows = r6dr._faces(rep, built["rows"])
    zones = fz.assess(rows, register.labels, floor_of=built["floor_of"],
                      fittings=built["linings"],
                      wall_bands=[w for wr in rep.walls for w in wr.walls])

    out = Path(out_dir)
    w = x6b._write
    exports = [
        w(out, "P7757_ROUND6D_SPACE_REGISTER",
          x6c.register_rows(register, rows),
          {"one_row_per": "candidate polygon, with what it IS"}),
        w(out, "P7757_ROUND6D_FUNCTIONAL_ZONE", zone_rows(zones),
          {"one_row_per": "functional zone",
           "note": ("a zone creates no wall, no room and no quantity. "
                    "Several zones may share one open space")}),
        w(out, "P7757_ROUND6D_PANTRY_ANALYSIS", pantry_rows(zones),
          {"one_row_per": "pantry",
           "note": ("CLOSED_PANTRY, OPEN_AMERICAN_PANTRY or UNKNOWN. An "
                    "open edge tiles nothing and no tile height is "
                    "assumed")}),
        w(out, "P7757_ROUND6D_STAIR_ASSEMBLY", assembly_rows(rep),
          {"one_row_per": "staircase",
           "note": "measured net. No waste, no procurement, no price"}),
        w(out, "P7757_ROUND6D_STAIR_FLIGHT", flight_rows(rep),
          {"one_row_per": "flight"}),
        w(out, "P7757_ROUND6D_STAIR_TREAD", tread_rows(rep),
          {"one_row_per": "tread, measured from its own polygon"}),
        w(out, "P7757_ROUND6D_STAIR_RISER", riser_rows(rep),
          {"one_row_per": "riser",
           "note": ("a plan carries no height: without section evidence "
                    "the riser quantity is NOT ESTABLISHED")}),
        w(out, "P7757_ROUND6D_STAIR_LANDING", landing_rows(rep),
          {"one_row_per": "landing, between the flights it turns on"}),
        w(out, "P7757_ROUND6D_FITTING_BAND", fitting_rows(rep),
          {"one_row_per": "band that stands on another band",
           "note": ("its FRONT face bounds no room. The room it stands "
                    "in is measured to the wall behind it")}),
        w(out, "P7757_ROUND6D_WALL_STRETCH_OWNERSHIP", stretch_rows(rep),
          {"one_row_per": "stretch of its two lines that a wall owns",
           "note": ("a set of stretches, never the span between the "
                    "first and the last")}),
        w(out, "P7757_ROUND6D_BOUNDARY", x6b.boundary_rows(rep),
          {"one_row_per": "side of a space polygon"}),
        w(out, "P7757_ROUND6D_OPENING", x6b.opening_rows(rep),
          {"one_row_per": "opening hypothesis"}),
        w(out, "P7757_ROUND6D_IDENTITY", x6b.identity_rows(rep),
          {"one_row_per": "reconciled place"}),
        w(out, "P7757_ROUND6D_DIMENSION", x6b.dimension_rows(rep),
          {"one_row_per": "authored dimension checked against a span"}),
        w(out, "P7757_ROUND6D_EXCEPTIONS",
          exception_rows(rep, register, roles, zones, report),
          {"one_row_per": "refusal, of any kind, anywhere in the run"}),
    ]

    manifest = {
        "export": EXPORT,
        "exported_at_commit": _head(),
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d", "decode": decode_json},
        "supervised_floor_assignment": note,
        "section_evidence": sections_json or "none supplied",
        "engine": {
            "PHYSICAL_WALL_BAND_HASH": pwall.wall_band_hash(),
            "WALL_FACE_OWNERSHIP_HASH": wface.model_hash(),
            "SINGLE_LINE_PARTITION_HASH": slp.model_hash(),
            "FITTING_BAND_HASH": fband.model_hash(),
            "FUNCTIONAL_ZONE_HASH": fz.model_hash(),
            "STAIR_ASSEMBLY_HASH": stair.model_hash(),
            "SPACE_REGISTER_HASH": sreg.model_hash(),
        },
        "synthetic": {
            "ROUND_6D_SYNTHETIC_HASH": r6ds["ROUND_6D_SYNTHETIC_HASH"],
            "cases": f"{r6ds['passed']}/{r6ds['cases']}"},
        "areas_kept_apart": register.areas(),
        "protected_geometry": r6c._protected(rows),
        "report_hash": report["ROUND_6D_REPORT_HASH"],
        "exports": exports,
        "what_this_is_not": (
            "no TradeMeasurementZone, no floor ceramic, no wall ceramic, "
            "no waste rule, no pricing and no contractor rates"),
    }
    manifest["ROUND6D_EXPORT_MANIFEST_HASH"] = _sha(
        json.dumps(manifest, sort_keys=True, default=str))
    man = out / "ROUND6D_EXPORT_MANIFEST.json"
    man.write_text(json.dumps(manifest, indent=2, ensure_ascii=False,
                              default=str) + "\n", encoding="utf-8")
    rep_path = out / "P7757_ROUND6D_REPORT.json"
    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                   default=str) + "\n", encoding="utf-8")

    archive = out / "P7757_ROUND6D_EXPORT.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for e in exports:
            for key in ("csv", "json"):
                p = Path(e[key])
                tar.add(p, arcname=f"P7757_ROUND6D_EXPORT/{p.name}")
        for p in (man, rep_path):
            tar.add(p, arcname=f"P7757_ROUND6D_EXPORT/{p.name}")
    manifest["archive"] = str(archive)
    manifest["archive_sha256_24"] = hashlib.sha256(
        archive.read_bytes()).hexdigest()[:24]
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--sections", default="")
    a = ap.parse_args(argv)
    man = run(a.decode_json, a.out_dir, supervised_json=a.supervised,
              sections_json=a.sections)
    print(json.dumps({
        "ROUND6D_EXPORT_MANIFEST_HASH": man["ROUND6D_EXPORT_MANIFEST_HASH"],
        "archive": man["archive"],
        "archive_sha256_24": man["archive_sha256_24"],
        "exports": [{k: e[k] for k in ("export", "rows", "csv_sha256_24")}
                    for e in man["exports"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
