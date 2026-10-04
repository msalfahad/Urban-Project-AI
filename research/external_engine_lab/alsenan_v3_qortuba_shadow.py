"""V3 generic engines on Qortuba (RC1_REFERENCE) - SHADOW ONLY. The frozen Qortuba topology (room_topology.run, the
inputs and claims of r8_11_qortuba "new") is rebuilt and compared site by site with the same input run through the
V3 chain (room_topology_v3 + text_role_v3 + opening_completion, two passes). Nothing Qortuba is edited, no Qortuba
quantity is replaced: the record states what the V3 rules WOULD change on the reference project, so a change is a
regression finding to explain, never an applied result.

    python3 research/external_engine_lab/alsenan_v3_qortuba_shadow.py <work_dir> <out_json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import r8_10_claims as CL                                                                    # noqa: E402
import r8_10_qortuba as Q10                                                                  # noqa: E402
import r8_8_topology as LAB                                                                  # noqa: E402
from engine.source import opening_completion as OPC, room_topology_v3 as RT3                # noqa: E402
from engine.source import text_role_v3 as TR3, topology_closures as TC                      # noqa: E402


def _sites(r):
    u2 = (r["_unit_mm"] ** 2) / 1e6
    return sorted((round(s["area"] * u2, 4), s["status"], tuple(sorted(map(str, s["labels"]))), tuple(s["issues"]))
                  for s in r["sites"])


def shadow(work) -> dict:
    inps, _, facts = Q10.inputs(Path(work))
    pc, xc, _ = CL.load()
    inp = inps["NEW_K2"]
    u = CL.attach_xref_facts(LAB.UNREALISED["NEW_K2"], facts)
    ev = LAB.placement_for(inp.revision.revision_id)
    if ev is not None:
        import r8_9_evidence as EV
        u = EV.attach(u, ev[0], ev[1])
    kw = dict(frame_insert=LAB.C.FRAME_INSERT, expected_revision_id=inp.revision.revision_id,
              selected_region_id=LAB.C.REGION_ID, unrealised=u, part_claims=pc, xref_claims=xc,
              closure_policy=TC.POLICY_ID)
    frozen = LAB.RT.run(inp, **kw)
    roles = TR3.classify(inp, [inp], frame_insert=LAB.C.FRAME_INSERT)
    r1 = RT3.run(inp, text_roles=roles, **kw)
    oc = OPC.derive(r1, inp)
    r2 = RT3.run(inp, text_roles=roles, extra_closures=oc["closures"], extra_opening_status=oc["opening_status"], **kw)
    for r in (frozen, r1, r2):
        r["_unit_mm"] = inp.unit_native_to_mm
    a, b, c = _sites(frozen), _sites(r1), _sites(r2)
    return {"SCHEMA": "URBAN_V3_QORTUBA_SHADOW_V1", "project_state": "RC1_REFERENCE (frozen; nothing edited)",
            "text_roles_v3_identical_sites": a == b, "v3_two_pass_identical_sites": a == c,
            "frozen_sites": len(a), "v3_sites": len(c),
            "only_frozen": [list(x) for x in a if x not in c], "only_v3": [list(x) for x in c if x not in a],
            "opening_completion": {"doors": {k: {kk: v[kk] for kk in ("state", "rule") if kk in v}
                                             for k, v in oc["doors"].items()},
                                   "wall_gap_records": [{k: r[k] for k in ("gap_id", "state", "why")} for r in oc["records"]],
                                   "drafting_gaps": len(oc["drafting_gaps"]),
                                   "closures": sorted(x.source_id for x in oc["closures"])},
            "state": "UNCHANGED" if a == c else "CHANGED_IN_SHADOW_ONLY",
            "rule": "Qortuba is RC1_REFERENCE: a V3 change is reported here and explained, never applied to Qortuba"}


if __name__ == "__main__":
    rec = shadow(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("state", "frozen_sites", "v3_sites", "text_roles_v3_identical_sites",
                                          "v3_two_pass_identical_sites")}, indent=1))
    print(json.dumps(rec["opening_completion"], indent=1)[:3000])
