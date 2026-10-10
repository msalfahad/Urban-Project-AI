"""R8.10 lab: P7757 as the SECOND DRAWING FAMILY, used only to attack the generic R8.9 / R8.10 assumptions.

    python3 research/external_engine_lab/r8_10_p7757.py <register_dir>

Not a quantity round. No unit is assumed (UNIT_UNRESOLVED): no eps_r, so no certified topology, no near-miss band
and no NETWORK grade. Everything that needs only the source structure is run: effective layers, building-assembly
V2 contexts, text-tag V2 families, duplicate occurrences, cryptic layer names, the door-symbol family.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_9_p7757 as P9                                                                      # noqa: E402
from engine.source import canonical_input as CI, geometry_role as GR, role_authority as RA  # noqa: E402
from engine.source import text_role as TX, topology_policy as TP, trade_regions as TR       # noqa: E402
from engine.source import room_topology as RT                                                # noqa: E402


def main(regdir):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    dec, inp, unreal = P9.build()
    m = RT.max_abs_coordinate(inp.parts)
    eps_n = TP.eps_noise(m)
    adm = GR.admit(inp, frame_insert=None, eps=eps_n)
    troles = TX.classify(inp)
    ctx = RA.occurrence_contexts(inp, adm, None, text_roles=troles, eps=eps_n)
    r89 = json.loads((ROOT / "tests/r8_9/registers/P7757_R8_9_SHADOW.json").read_text())
    dup = TR.duplicate_occurrences(inp)
    blocks = Counter(p.lineage[0].block_name for p in inp.parts if p.lineage)
    door_blocks = sorted(b for b in blocks if b and b.upper().startswith("D") and b[1:].isdigit())
    tag_v2 = Counter(f"{v.role} | {v.rule_id}" for v in troles.values())
    lay = Counter(CI.effective_layer(p)[0] for p in inp.parts)
    cryptic = {k: n for k, n in lay.most_common(12) if k and (len(k) <= 3 or k.isdigit())}
    reg = {
        "SCHEMA": "URBAN_R8_10_P7757_SHADOW_V1",
        "purpose": "second drawing family: attack the generic assumptions; NOT a quantity round; no P7757 published "
                   "output changes",
        "unit": {"state": "UNIT_UNRESOLVED", "candidate": "mm (INSUNITS 4, DIMLFAC 0.1, door leaf radii) - a "
                                                          "candidate, never adopted", "owner_question": "NOT ASKED"},
        "effective_layer": {"layer0_children_inside_inserts": sum(1 for p in inp.parts if p.layer == "0"
                                                                  and p.identity.instance_handles),
                            "differs_from_source": sum(1 for p in inp.parts if CI.effective_layer(p)[0] != p.layer),
                            "reading": "unchanged from R8.9: the effective layer decides the role of 3328 parts"},
        "network_grade": {"state": "NOT_EVALUATED: NETWORK needs the authored band eps_r, which needs a unit",
                          "risk_for_this_family": "single-letter layers (W) hold both wall faces and other linework; "
                                                  "a W-layer claim would make NETWORK the only admission path - the "
                                                  "self-dimension conflict and a wall-band model would be needed "
                                                  "before any W claim is reviewed"},
        "building_assembly_v2": {"contexts": dict(Counter(v["context"] for v in ctx.values())),
                                 "r8_9": r89["occurrence_contexts"],
                                 "reading": "no occurrence becomes an assembly under either rule: P7757 draws its "
                                            "plans in model space; the door blocks are symbols"},
        "text_tags_v2": {"r8_10": dict(tag_v2), "r8_9": r89["text_roles"],
                         "reading": "TR-03 now needs repeated family use: tags whose composition carries one room name "
                                    "only fall back to candidates; the family evidence (TR-04) is kept"},
        "cryptic_layers": {"top_layers_by_parts": cryptic,
                           "reading": "single-letter / numeric layer names: the generic exact-token lexicon admits none "
                                      "of them - fail closed; source-scoped claims, not a bigger lexicon, are the "
                                      "mechanism"},
        "door_symbol_family": {"blocks": door_blocks[:20], "count": len(door_blocks),
                               "reading": "doors are blocks named by a size code (D###) on layer D; no door signature is "
                                          "proven (GR door evidence needs leaf + swing structure inside the block)"},
        "duplicate_occurrences": {"groups": len(dup), "occurrences": sum(len(g["occurrences"]) for g in dup),
                                  "examples": [{k: g[k] for k in ("occurrences", "block", "children")} for g in dup[:8]],
                                  "reading": ("exact duplicate inserts exist in this family too: never deleted; area "
                                              "topology unaffected; a count trade needs its own rule") if dup else
                                             "no exact duplicate insert in this family: the detector reports none "
                                             "(a negative result, not an assumption)"},
        "ts01_certificate": "UNIT_UNRESOLVED"}
    (regdir / "P7757_R8_10_SHADOW.json").write_text(json.dumps(reg, indent=1, default=str) + "\n")
    print(json.dumps({k: reg[k] for k in ("building_assembly_v2", "text_tags_v2", "duplicate_occurrences")},
                     indent=1, default=str)[:3000])
    return reg


if __name__ == "__main__":
    main(sys.argv[1])
