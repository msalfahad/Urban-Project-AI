"""ALSENAN V3 - final BOQ completion (lab adapter, project-scoped; the engines it calls are generic).

Chain: Phase A2 context (frozen chain, rerun from source) -> V3 topology per floor (text_role_v3 with the drawing's
text-style fonts, room_topology_v3 + opening_completion in two passes; the frozen result is kept beside it) ->
the Phase A3 and B2A downstream logic UNCHANGED on the V3 topology -> the V3 layers (alsenan_v3_layers).

Nothing here changes a frozen engine. Owner decisions OD-V3-1..10 (alsenan_v3_owner_decisions.json) are the only
new authority; every fallback is labelled URBAN_FALLBACK.

    python3 research/external_engine_lab/alsenan_v3.py <work_dir> <register_dir> [commit]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import alsenan_phase_a as AP                                                                     # noqa: E402
import alsenan_phase_a2 as A2                                                                    # noqa: E402
import alsenan_phase_a3 as A3                                                                    # noqa: E402
import alsenan_phase_b2a as B2A                                                                  # noqa: E402
from engine.source import benchmark_firewall as FW                                               # noqa: E402
from engine.source import legacy_text as LT, opening_completion as OPC, room_topology_v3 as RT3  # noqa: E402
from engine.source import text_role as TX, text_role_v3 as TR3                                   # noqa: E402
import cad_text_styles as TS                                                                    # noqa: E402
from engine.source import topology_closures as TC                                                # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_V3_FINAL_BOQ"
FLOORS = A2.FLOORS
DECISIONS = HERE / "alsenan_v3_owner_decisions.json"


def build(work, commit=None) -> dict:
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    fw_census = AP.firewall_census()
    fw_census["scratch_disclosure"] = AP.scratch_disclosure(work)
    loaded_before = set(sys.modules)
    with FW.OpenAudit() as audit:
        ctx = A2._build(work)
        ctx["v3_topology"] = topology(ctx, work)
        ctx["a3"] = A3._a3(ctx, work)
        ctx["_work"] = str(work)
        ctx["b2a"] = B2A._b2a(ctx, work)
        import alsenan_v3_layers as L
        ctx["v3"] = L.layers(ctx, work)
    ctx["code_commit"] = commit
    ctx["firewall"] = {"census": fw_census, "audit": audit.opened, "modules_loaded_during_build":
                       sorted(set(sys.modules) - loaded_before), "modules_all": sorted(sys.modules)}
    return ctx


def topology(ctx, work) -> dict:
    """Replace each floor's frozen TS01 result by the V3 two-pass result (the frozen one is kept as res_frozen)."""
    P = {k: Path(work) / v for k, v in ctx["paths"].items()}
    fonts = TS.font_of_handle(P["P7757.dxf"])
    unreal, _ = A2.fix_unrealised(ctx["a2"]["unrealised"]["phase_a"], A2.rtext_placements(P["P7757.dxf"]))
    raw = ctx["a2_raw"]
    inps = [raw[fl]["inp"] for fl in FLOORS]
    out = {"policies": {"text_role": TR3.policy_record(), "legacy_text": LT.policy_record(),
                        "opening_completion": OPC.policy_record(), "topology": RT3.POLICY_ID,
                        "text_styles": TS.POLICY_ID},
           "floors": {}}
    for fl in FLOORS:
        v = raw[fl]
        inp, eri = v["inp"], v["eri"]
        roles = TR3.classify(inp, inps, frame_insert=None, claims=eri["claims"], font_of_handle=fonts)
        kw = dict(frame_insert=None, expected_revision_id=inp.revision.revision_id, selected_region_id=inp.region_id,
                  unrealised=unreal, closure_policy=TC.POLICY_ID, claims=eri["claims"],
                  inferred_doors=eri["inferred_doors"], text_roles=roles,
                  provenance={"v3": [RT3.POLICY_ID, OPC.policy_record()["digest"], TR3.POLICY_ID]})
        r1 = RT3.run(inp, **kw)
        oc = OPC.derive(r1, inp)
        r2 = RT3.run(inp, extra_closures=oc["closures"], extra_opening_status=oc["opening_status"], **kw)
        v["res_frozen"], v["res"], v["text_roles_v3"], v["opening_completion"] = v["res"], r2, roles, oc
        frozen_roles = v["res_frozen"]["roles"]["text_roles"]
        changed = {k: [frozen_roles[k].role, r.role, r.rule_id] for k, r in roles.items()
                   if k in frozen_roles and frozen_roles[k].role != r.role}
        out["floors"][fl] = {
            "sites_frozen": len(v["res_frozen"]["sites"]), "sites_v3": len(r2["sites"]),
            "labels_established_frozen": v["res_frozen"]["counts"]["labels"], "labels_established_v3": r2["counts"]["labels"],
            "text_role_changes": dict(sorted(changed.items())),
            "decoded_labels": TR3.decoded_labels(inp, roles, fonts),
            "doors": {k: {kk: d[kk] for kk in ("state", "rule", "closure_a", "closure_b", "closure_b_rule", "why")
                          if kk in d} for k, d in sorted(oc["doors"].items())},
            "wall_gaps": [{k: x[k] for k in ("gap_id", "state", "why", "door_evidence", "closures", "gap_length",
                                             "affects_wall_quantity", "affects_finish_quantity")} for x in oc["records"]],
            "drafting_gaps": oc["drafting_gaps"],
            "double_leaf": {k: {kk: m[kk] for kk in ("width", "radius", "arc_parts", "kind")}
                            for k, m in oc["double_leaf"].items()},
            "closures_added": sorted(c.source_id for c in oc["closures"])}
    out["fonts_legacy"] = {h: f for h, f in fonts.items() if LT.font_family(f)}
    out["text_role_rule_counts"] = {fl: _rule_counts(raw[fl]["text_roles_v3"]) for fl in FLOORS}
    return out


def _rule_counts(roles):
    out = {}
    for r in roles.values():
        k = f"{r.role}|{r.rule_id}"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def main(work, regdir, commit=None):
    import alsenan_v3_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(REGS.summary(regs), indent=1, ensure_ascii=False))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
