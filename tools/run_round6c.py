"""Round 6C. Classify the drawing, then build one register per floor.

Nothing here measures geometry. It runs the frozen round-6B measurement,
asks what each drawing region SHOWS, builds the unique physical-space
register, reconciles every authored label to exactly one space or an
exception, and reports completeness per floor.

A room quantity from a region that is not an established FLOOR_PLAN is
refused before it is computed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import drawing_role as drole
from engine import floor_register as freg
from engine import semantic_seed as seeds_mod
from engine import space_register as sreg

STAGE = "ROUND_6C_REGISTER_ONLY"

# §8. These must not regress. Areas in m2, as round 6A/6B established them.
PROTECTED = {
    "KITCHEN_MAIN": 8.100, "DRIVER": 7.875, "WC_1500x2250": 3.375,
    "WC_1500x1300": 1.950, "WC_1350x1750": 2.3625, "WC_1470x1800": 2.646,
}
# §9. Geometry the audit believes is correct but blocked.
FALSE_NEGATIVE_CANDIDATES = (4.725, 5.0225, 19.350, 5.550)
TOL = 0.002


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


# A gate that says "this candidate has no established geometry" is a fact
# about the measurement. A gate that says "this candidate is a shaft" or
# "nobody resolved what this is" is a CLASSIFICATION — and where the audit
# says the same polygon is a room, the classification is what is holding a
# correct piece of geometry back.
CLASSIFICATION_GATES = ("ENCLOSURE_ROLE_IS_VOID_OR_SHAFT", "CANDIDATE_ROLE:",
                        "REGISTER:")


def _classification_only(gates) -> bool:
    return bool(gates) and all(
        any(g.startswith(k) or g == k for k in CLASSIFICATION_GATES)
        for g in gates)


def _false_negative_analysis(rows, reg) -> list:
    """§9. For each blocked candidate the audit names: why, and is it valid."""
    entry = {e.space_id: e for e in reg.entries}
    out = []
    for want in FALSE_NEGATIVE_CANDIDATES:
        hits = [r for r in rows if abs((r["area_m2"] or 0) - want) <= TOL]
        if not hits:
            out.append({
                "audit_area_m2": want,
                "verdict": "NOT_PRESENT_AS_A_CANDIDATE",
                "reason": ("no polygon of this area exists in the run at "
                           "all, so no release gate is holding it: the "
                           "geometry itself was never formed"),
            })
            continue
        for r in hits:
            e = entry.get(r["space_id"])
            released = bool(e is not None and e.released)
            gates = list(r["blockers"])
            if e is not None:
                gates.extend(e.withheld_because)
            measured = r["basis"].startswith("CLEAR_INTERNAL")
            if released and not gates:
                verdict, why = "RELEASED", "nothing is holding it"
            elif not gates:
                verdict = "FALSE_NEGATIVE_RELEASE_GATE"
                why = ("nothing is holding it and it is not released, "
                       "which is a gate defect")
            elif measured and _classification_only(gates):
                verdict = "FALSE_NEGATIVE_RELEASE_GATE"
                why = ("its geometry IS established and what holds it is a "
                       "classification the audit contradicts: this round "
                       "calls it a shaft, a void or unresolved, and the "
                       "audit calls it a room. The gate is doing its job "
                       "on a verdict that is wrong")
            else:
                verdict = "CORRECTLY_BLOCKED"
                why = ("its own measurement never established a boundary "
                       "basis, so there is no area here to withhold or "
                       "release" if not measured else
                       "the gate names a fact about this candidate that "
                       "is true")
            out.append({
                "audit_area_m2": want,
                "space_id": r["space_id"],
                "region_id": r["region_id"],
                "measurement_basis": r["basis"],
                "release_status": r["release_status"],
                "candidate_role": (e.candidate_role if e else ""),
                "gates_holding_it": gates,
                "verdict": verdict,
                "reason": why,
            })
    return out


def _unknown_terms(reg) -> list:
    """§12. A term this project's vocabulary does not know is not guessed.

    The label is still carried, the space it names is still measured, and
    the identity stays UNKNOWN_TERM until a human says otherwise.
    """
    from engine import architectural_ontology as onto

    out = []
    for v in reg.labels:
        text = (v.text or "").strip()
        if not text or onto.classify_term(text).is_known:
            continue
        out.append({"raw_text": text, "at_mm": [round(v.x, 1),
                                                round(v.y, 1)],
                    "drawing_region_id": v.region_id,
                    "floor": v.floor_level,
                    "normalized_identity": "UNKNOWN_TERM",
                    "label_status": v.status,
                    "physical_space_id": v.space_id,
                    "why": ("the vocabulary does not know this term. It is "
                            "not translated, not matched to the nearest "
                            "known word and not dropped")})
    return out


def _protected(rows) -> dict:
    out = {}
    for name, want in PROTECTED.items():
        hits = [r for r in rows
                if abs((r["area_m2"] or 0) - want) <= TOL
                and r["basis"].startswith("CLEAR_INTERNAL")]
        out[name] = {
            "expected_m2": want,
            "found": len(hits),
            "space_ids": [r["space_id"] for r in hits],
            "dims_mm": [r["principal_dims_mm"] for r in hits],
            "status": "HELD" if hits else "REGRESSED",
        }
    return out


def run(decode_json: str, *, supervised_json: str = "") -> dict:
    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))

    supervised = {}
    supervised_note = "none supplied"
    if supervised_json and Path(supervised_json).exists():
        data = json.loads(Path(supervised_json).read_text(encoding="utf-8"))
        supervised = data.get("assignments", {})
        supervised_note = supervised_json

    built = freg.assemble(nd, rep, supervised=supervised)
    roles = built["roles"]
    rows = built["rows"]
    lining = built["linings"]
    register = built["register"]
    refused = built["release_refused_for_drawing_role"]

    floors = {}
    for fl, entries in register.by_floor().items():
        floors[fl or drole.FLOOR_NOT_ESTABLISHED] = [
            e.record() for e in sorted(entries, key=lambda x: -x.area_m2)]

    out = {
        "stage": STAGE,
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d"},
        "supervised_floor_assignment": supervised_note,
        "drawing_regions": roles.record(),
        "register": register.record(),
        "completeness_per_floor": sreg.completeness(register),
        "areas_kept_apart": register.areas(),
        "release_refused_for_drawing_role": refused,
        "bands_standing_on_another_band": [
            {
                "lining_band_id": st.lining_id,
                "stands_on_wall_band_id": st.wall_id,
                "axis": st.axis,
                "shared_face_mm": round(st.shared_face_mm, 1),
                "front_face_mm": round(st.far_face_mm, 1),
                "what_it_blocks": ("only a candidate that stops at the "
                                   "front face; a candidate bounded at the "
                                   "shared face is bounded by the wall"),
            }
            for _k, st in sorted(lining.items())],
        "tables_per_floor": floors,
        "UNKNOWN_TERM_LABELS": _unknown_terms(register),
        "UNMAPPED_LABELS": [v.record() for v in register.labels
                            if v.status == sreg.LABEL_EXCEPTION],
        "UNRESOLVED_SPACES": [e.record() for e in register.entries
                              if e.candidate_role == sreg.UNRESOLVED],
        "NON_SPACE_ARTIFACTS": [e.record() for e in register.entries
                                if e.candidate_role ==
                                sreg.DRAWING_ARTIFACT],
        "SUPER_REGIONS": [e.record() for e in register.entries
                          if e.candidate_role == sreg.SUPER_REGION],
        "CONTAINERS_OF_NOTHING_THAT_IS_A_SPACE": [
            {"physical_space_id": e.space_id, "area_m2": round(e.area_m2, 4),
             "candidate_role": e.candidate_role,
             "children": list(e.children),
             "why_it_is_not_a_super_region": (
                 "it contains candidates and none of them is a space, so "
                 "nothing would be released twice by releasing it")}
            for e in register.entries
            if e.relation == sreg.REL_PARENT
            and e.candidate_role != sreg.SUPER_REGION],
        "FALSE_NEGATIVE_CANDIDATES": _false_negative_analysis(rows,
                                                              register),
        "protected_geometry": _protected(rows),
        "what_this_run_is_not": (
            "no FunctionalZone, no TradeMeasurementZone, no ceramic, no "
            "waste, no pricing and no BOQ export. The register is the "
            "deliverable and it is frozen for independent review"),
    }
    out["ROUND_6C_REGISTER_HASH"] = _sha(
        json.dumps(out, sort_keys=True, default=str))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    rec = run(a.decode_json, supervised_json=a.supervised)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False, default=str)
            + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({
        "ROUND_6C_REGISTER_HASH": rec["ROUND_6C_REGISTER_HASH"],
        "drawing_regions": rec["drawing_regions"]["counts"],
        "register": rec["register"]["counts"],
        "completeness_per_floor": rec["completeness_per_floor"],
        "protected_geometry": {k: v["status"]
                               for k, v in rec["protected_geometry"].items()},
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
