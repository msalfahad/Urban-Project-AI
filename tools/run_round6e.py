"""Round 6E on P7757: stable identity, stair completeness, one truth.

§20. What this run answers, and nothing else:

    A  the lineage 6C -> 6D -> 6E, from the frozen bundles themselves
    B  the register, with ONE authoritative release state
    C  the stairs: kind, coverage per floor, quantities by unit
    D  the search for vertical evidence, and the refusal that remains
    E  MARBLE n PORCELAIN, measured
    F  report against export: every headline number, recomputed

No TradeMeasurementZone, no ceramic, no waste, no price, no Firebase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import floor_register as freg
from engine import functional_zone as fz
from engine import report_consistency as rcons
from engine import semantic_seed as seeds_mod
from engine import space_lineage as lineage
from engine import space_register as sreg
from engine import stair_assembly as stair
from engine import vertical_evidence as ve
from tools import lineage_chain as lchain
from tools import run_round6c as r6c
from tools import run_round6d as r6d

STAGE = "ROUND_6E_STABLE_LINEAGE_STAIR_COMPLETENESS_REPRODUCIBLE_EXPORT"

# §9, §16. The owner's PROJECT rule for P7757: its stairs are marble.
# Applied to the stairs the rule is about — the interior ones — and not
# to steps outside the building or to a run whose kind the drawings do
# not establish. A stair is not marble because it is a stair.
P7757_STAIR_FINISH = "STAIR_MARBLE_SURROUNDING_FLOOR_PORCELAIN"
P7757_FINISH_RULES = {
    stair.MAIN_INTERIOR_STAIR: P7757_STAIR_FINISH,
    stair.SECONDARY_INTERIOR_STAIR: P7757_STAIR_FINISH,
    stair.SERVICE_STAIR: P7757_STAIR_FINISH,
}

MANIFESTS = {
    "ROUND_6C": "data/runs/7757/round6c_export/ROUND6C_EXPORT_MANIFEST.json",
    "ROUND_6D": "data/runs/7757/round6d_export/ROUND6D_EXPORT_MANIFEST.json",
}


def _previous_areas(run_id: str) -> dict:
    """What that round EXPORTED, read from its own frozen manifest.

    Not from a constant typed into this file. A comparison against a
    number nobody can check is not a comparison.
    """
    path = Path(MANIFESTS.get(run_id, ""))
    if not path.exists():
        return {"status": "THE_FROZEN_BUNDLE_IS_NOT_HERE"}
    areas = json.loads(path.read_text(encoding="utf-8")).get(
        "areas_kept_apart", {})
    return {k: v for k, v in areas.items() if not k.startswith("why")}

BUNDLES = (
    ("ROUND_6C", "data/runs/7757/round6c_export/"
                 "P7757_ROUND6C_SPACE_REGISTER.json"),
    ("ROUND_6D", "data/runs/7757/round6d_export/"
                 "P7757_ROUND6D_SPACE_REGISTER.json"),
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _release_audit(register) -> dict:
    """§3. ONE state, and nothing that contradicts it may be released."""
    bad = []
    for e in register.entries:
        if not e.released:
            continue
        why = []
        if not e.is_space:
            why.append("IT_IS_NOT_A_PHYSICAL_SPACE")
        if not e.may_release:
            why.append("ITS_ROLE_MAY_NOT_RELEASE")
        if e.candidate_role in sreg.NEVER_A_ROOM_QUANTITY:
            why.append(f"ITS_ROLE_IS_{e.candidate_role}")
        if e.withheld_because:
            why.append("IT_CARRIES_A_WITHHOLDING_REASON")
        if why:
            bad.append({"physical_space_id": e.space_id,
                        "candidate_role": e.candidate_role,
                        "release_status": e.release_status,
                        "contradictions": why})
    released = [e for e in register.entries if e.released]
    return {
        "release_state_field": "release_status",
        "released": len(released),
        "withheld": sum(1 for e in register.entries if not e.released),
        "contradictions": len(bad),
        "detail": bad,
        "invariant": (
            "RELEASE_ELIGIBLE never coexists with may_release=false, "
            "is_physical_space=false, PARTIAL_SPACE, DRAWING_ARTIFACT, "
            "SUPER_REGION or UNRESOLVED"),
    }


def _lineage_rows(rep, rows) -> list:
    """This run's candidates, in the shape the matcher wants."""
    out = []
    band_of = {}
    for r in rep.rows:
        c = r.clear
        band_of[r.space_id] = sorted({
            f.wall_band_id for f in (c.boundary_faces if c is not None
                                     else ()) if f.wall_band_id})
    for row in rows:
        out.append({
            "space_id": row["space_id"],
            "region_id": row["region_id"],
            "polygon": row.get("polygon"),
            "area_m2": row.get("area_m2", 0.0),
            "normalized_identity": row.get("normalized_identity", ""),
            "candidate_role": row.get("candidate_role", ""),
            "wall_band_ids": tuple(band_of.get(row["space_id"], ())),
        })
    return out


def _vertical(decode_json: str, dwf: str = "", pdfs=()) -> dict:
    from tools import scan_vertical_evidence as scan

    found = scan.from_cad(decode_json)
    if dwf and Path(dwf).exists():
        found += scan.from_dwf(dwf, start=len(found) + 1)
    for p in pdfs or ():
        if Path(p).exists():
            found += scan.from_pdf(p, start=len(found) + 1)
    return ve.assess(found)


def run(decode_json: str, **kw) -> dict:
    """The report alone. `run_full` also hands back what made it."""
    return run_full(decode_json, **kw)[0]


def run_full(decode_json: str, *, supervised_json: str = "",
             sections_json: str = "", dwf: str = "", pdfs=(),
             bundles=BUNDLES) -> tuple:
    from engine import round6e_selftest as r6e

    frozen = r6e.assert_frozen()

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
        project_rules={"stair_finish_rule": P7757_STAIR_FINISH})

    supervised, note = {}, "none supplied"
    if supervised_json and Path(supervised_json).exists():
        data = json.loads(Path(supervised_json).read_text(encoding="utf-8"))
        supervised = data.get("assignments", {})
        note = supervised_json
    built = freg.assemble(nd, rep, supervised=supervised)
    register, roles = built["register"], built["roles"]
    rows = r6d._faces(rep, built["rows"])
    zones = fz.assess(rows, register.labels, floor_of=built["floor_of"],
                      fittings=built["linings"],
                      wall_bands=[w for wr in rep.walls for w in wr.walls])

    # ---- A. 6C -> 6D -> 6E, from the bundles that were exported ------
    regions = rep.regions.regions
    chain = lchain.chain([(k, v) for k, v in bundles if Path(v).exists()],
                         regions, floor_of=built["floor_of"])
    mine = _lineage_rows(rep, rows)
    lrep = lineage.assign(mine, regions, previous=chain["registry"],
                          run_id="ROUND_6E", floor_of=built["floor_of"])
    stable_of = {x.run_candidate_id: x.stable_space_id for x in lrep.links}

    # ---- C. the stairs -----------------------------------------------
    interior = ({v.space_id: v.interior_exterior
                 for v in rep.space_roles.verdicts}
                if rep.space_roles else {})
    stairs = stair.reconcile(rep.stairs, regions=regions,
                             floor_of=built["floor_of"],
                             interior_of=interior,
                             finish_rules=P7757_FINISH_RULES)
    coverage = stair.coverage(rep.stairs, stairs["physical_stairs"],
                              floor_of=built["floor_of"])
    quantities = stair.quantities(stairs["physical_stairs"], rep.stairs)
    wkt_of = {r.space_id: (r.clear.polygon_wkt if r.clear is not None
                           else "") for r in rep.rows}
    clash = stair.finish_clash(
        [(e.space_id, wkt_of.get(e.space_id, ""))
         for e in register.entries if e.released], rep.stairs)

    areas = register.areas()
    out = {
        "stage": STAGE,
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d"},
        "supervised_floor_assignment": note,
        "section_evidence": (sections_json or "none supplied"),
        "synthetics_that_passed_first": {
            "round_6e": f"{frozen['passed']}/{frozen['cases']}",
            "ROUND_6E_SYNTHETIC_HASH": frozen["ROUND_6E_SYNTHETIC_HASH"]},
        "A_lineage": {
            "steps": [{"from": s["from"], "to": s["to"],
                       "counts": s["counts"]} for s in chain["steps"]]
            + [{"from": chain["previous_run_id"], "to": "ROUND_6E",
                "counts": lrep.counts()}],
            "this_run": lrep.record(),
            "two_ids": (
                "RUN_CANDIDATE_ID is this run's enumeration and may "
                "change. STABLE_PHYSICAL_SPACE_ID is the identity of a "
                "space of the building and is carried only on evidence"),
        },
        "B_register": {
            "areas_kept_apart": areas,
            "release_state": _release_audit(register),
            "by_candidate_role": register.counts()["by_candidate_role"],
            "labels": {k: v for k, v in register.counts().items()
                       if k.startswith("labels")},
            "completeness_per_floor": sreg.completeness(register),
            "round_6c": _previous_areas("ROUND_6C"),
            "round_6d": _previous_areas("ROUND_6D"),
            "round_6e": {k: v for k, v in areas.items()
                         if not k.startswith("why")},
            "protected_geometry": r6c._protected(rows),
        },
        "C_stairs": {
            "counts": stairs["counts"],
            "coverage": coverage,
            "physical_stairs": [x.record()
                                for x in stairs["physical_stairs"]],
            "quantities": quantities,
            "project_finish_rule": {
                "rule": P7757_STAIR_FINISH,
                "applied_to": sorted(P7757_FINISH_RULES),
                "not_applied_to": [stair.EXTERIOR_STEPS,
                                   stair.LANDSCAPE_STEPS,
                                   stair.STAIR_ROLE_UNKNOWN],
                "why": ("the owner's rule is about this project's "
                        "stairs. A run of steps whose kind the drawings "
                        "do not establish is not marble because it is "
                        "drawn as steps"),
            },
        },
        "D_vertical_evidence": _vertical(decode_json, dwf=dwf, pdfs=pdfs),
        "E_marble_and_porcelain": clash,
        "F_pantry": zones.record(),
        "drawing_regions": roles.counts(),
        "stable_ids": stable_of,
        "what_this_run_is_not": (
            "no TradeMeasurementZone engine, no floor ceramic, no wall "
            "ceramic, no waste rule, no pricing, no contractor rates "
            "and no Firebase"),
    }
    out["ROUND_6E_REPORT_HASH"] = _sha(
        json.dumps(out, sort_keys=True, default=str))
    context = {
        "nd": nd, "rep": rep, "built": built, "register": register,
        "roles": roles, "rows": rows, "zones": zones,
        "stairs": stairs, "coverage": coverage,
        "quantities": quantities, "clash": clash,
        "lineage": lrep, "chain": chain, "stable_of": stable_of,
        "supervised": note, "sections": sections,
    }
    return out, context


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--sections", default="")
    ap.add_argument("--dwf", default="")
    ap.add_argument("--pdf", action="append", default=[])
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    rec = run(a.decode_json, supervised_json=a.supervised,
              sections_json=a.sections, dwf=a.dwf, pdfs=a.pdf)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False, default=str)
            + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({
        "ROUND_6E_REPORT_HASH": rec["ROUND_6E_REPORT_HASH"],
        "A": rec["A_lineage"]["steps"],
        "B": {"areas": rec["B_register"]["round_6e"],
              "release_contradictions":
                  rec["B_register"]["release_state"]["contradictions"]},
        "C": {"counts": rec["C_stairs"]["counts"],
              "coverage": rec["C_stairs"]["coverage"]["stair_coverage"],
              "totals": rec["C_stairs"]["quantities"]["totals"]},
        "D": {k: v for k, v in rec["D_vertical_evidence"].items()
              if k in ("riser_height_status", "what_would_settle_it",
                       "level_marks_placed", "take_off_totals_refused")},
        "E": rec["E_marble_and_porcelain"]["status"],
    }, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
