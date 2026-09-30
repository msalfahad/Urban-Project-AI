"""R8.4 §18-§20 — region candidates and reference-region register for the three real sources.

Research lab only (SHADOW). Candidates come from engine/source/region_candidates.py (deterministic);
existing active-path view-role registers and project-adapter plan windows are imported as CANDIDATE
or PENDING_REVIEW designations. Nothing is ACCEPTED here: accepting a designation is a review
decision (Mohammad / an authorised role), so no region gains reference authority in R8.4.

    python3 research/external_engine_lab/r8_4_regions.py <out_dir>
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import frame as FR, region_candidates as RC                   # noqa: E402
from engine.source.cad import kernel as K1, libredwg_map as L                   # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from r8_4_qualification import SOURCES, full_source_sha, load                    # noqa: E402

EXP = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01"
ROLE_REGISTERS = {"P7757": EXP / "pa07r3/supervised/SHEET_ROLE_REGISTER.json",
                  "ALRASHED": EXP / "pa09_alrashed/blind/SHEET_ROLE_REGISTER.json",
                  "QORTUBA": EXP / "pa08_qortuba/blind/SHEET_ROLE_REGISTER.json"}
ADAPTER = ROOT / "research/qs_wall_treatment_01/pa09/alrashed/geometry.py"


def adapter_windows():
    """Al Rashed's project adapter plan windows, read (not modified) from pa09/alrashed/geometry.py."""
    spec = importlib.util.spec_from_file_location("alrashed_geometry_readonly", ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.WINDOWS)


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    register = {"SCHEMA": "URBAN_R8_4_REFERENCE_REGION_REGISTER_V1",
                "rule": ("reference authority only through an ACCEPTED ReferenceRegionDesignation (frame.py); a candidate "
                         "is not a designation; an UNKNOWN region never inherits plan full-size authority"),
                "accepted_designations": [], "projects": {}}
    for name, s in SOURCES.items():
        path = next(ROOT / d for d in s["decodes"] if (ROOT / d).exists())
        src = full_source_sha(name)
        decode = load(path)
        doc = L.to_document(decode, source_sha256=src)
        real = K1.realise(doc)
        got = RC.candidates(doc, real, "MODEL_SPACE")
        cands = got["candidates"]
        by_role = {}
        for c in cands:
            by_role[c.role_candidate] = by_role.get(c.role_candidate, 0) + 1
        roles = json.loads(ROLE_REGISTERS[name].read_text()) if ROLE_REGISTERS[name].exists() else {"VIEWS": []}
        active = [{"view_id": v["VIEW_ID"], "bbox": v.get("BBOX_MM"), "final_role": v.get("FINAL_ROLE"),
                   "role_status": v.get("ROLE_STATUS"), "deterministic_role": v.get("DETERMINISTIC_ROLE"),
                   "as_designation": "CANDIDATE only (role status " + str(v.get("ROLE_STATUS")) + "; not reviewed)"}
                  for v in roles.get("VIEWS", [])]
        pending = []
        if name == "ALRASHED":
            for floor, (x0, x1, y0, y1) in adapter_windows().items():
                d = FR.ReferenceRegionDesignation(
                    f"DES:ALRASHED:{floor}", src, "MODEL_SPACE", f"ADAPTER:{floor}", FR.PROJECT_ADAPTER_CLAIM,
                    "research/qs_wall_treatment_01/pa09/alrashed/geometry.py WINDOWS (sheet-layout match score 1.000)",
                    FR.ENGINE, "PENDING_REVIEW",
                    notes="used by the published takeoff; never recorded as a reviewed designation; accepting it is a review decision")
                pending.append({**d.as_dict(), "bounds_native": [x0, y0, x1, y1],
                                "effect_if_accepted": "region VERIFIED, but the frame stays CONFLICT: the unit context is CONFLICT"})
        register["projects"][name] = {
            "source_sha256": src, "decode": str(path.relative_to(ROOT)), "parameters": got["parameters"],
            "candidate_count": len(cands), "candidates_by_role": by_role,
            "candidates": [c.as_dict() for c in cands[:200]], "candidates_truncated": max(0, len(cands) - 200),
            "active_path_view_roles": active, "pending_designations": pending,
            "accepted_designations": []}
        print(name, len(cands), by_role, len(active), len(pending))
    (out_dir / "REFERENCE_REGION_REGISTER.json").write_text(json.dumps(register, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_4")
