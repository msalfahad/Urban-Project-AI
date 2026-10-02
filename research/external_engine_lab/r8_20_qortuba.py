"""R8.20 lab: Qortuba with the owner's human closure reviews and the I1471 construction rationale - authority / review
state only. The R8.19 rebuild is recomputed (every quantity must equal the committed R8.19 registers); the closure
records are recomputed and their digests compared with the reviewed packet digests; CLOSURE_RELEASE_MODEL_V1 is
evaluated with the review evidence; the I1471 wall / column evidence is re-derived from the admitted geometry.

    python3 research/external_engine_lab/r8_20_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_19_qortuba as Q19                                                                   # noqa: E402
import r8_19_registers as R19G                                                                # noqa: E402
from engine.source import closure_release as CR, closure_review as RV, owner_facts as OF      # noqa: E402
from engine.source import topology as T                                                       # noqa: E402

REG18, REG19 = ROOT / "tests/r8_18/registers", ROOT / "tests/r8_19/registers"
FACT = "QORTUBA-NEW-I1471-200MM-WALL-COLUMN-CONCEALMENT-OWNER-001"
TOL = 1e-6


def jl(p):
    return json.loads(Path(p).read_text())


def i1471_evidence(new, inp):
    """The 200 / 150 mm hosting walls, the stagger and the column alignment, from the admitted geometry only."""
    u = inp.unit_native_to_mm
    bands = [b for b in new["wall_bands"]["bands"] if b["state"] == "WALL_BAND_ESTABLISHED" and
             any("CLOSURE|I1471|" in o for e in b["ends"] for o in (e.get("opening") or []))]
    rec = {b["band_id"]: {"faces": [b["face_a"], b["face_b"]], "width_mm": round(b["width"] * u, 3),
                          "jamb_end": next({"face_a_end": e["face_a_end"], "face_b_end": e["face_b_end"],
                                            "closures": e["opening"]} for e in b["ends"]
                                           if any("CLOSURE|I1471|" in o for o in (e.get("opening") or [])))}
           for b in bands}
    parts = {p.identity.key: p for p in inp.parts}
    roles = new["roles"]["roles"]
    thick = next((b for b in bands if abs(b["width"] * u - 200.0) < 0.5), None)
    ent, cand = {}, {}
    if thick:
        fa, fb = parts[thick["face_a"]].geometry, parts[thick["face_b"]].geometry
        fy = sorted({round(fa[1], 6), round(fb[1], 6)})
        bx = (min(fa[0], fa[2], fb[0], fb[2]), max(fa[0], fa[2], fb[0], fb[2]))
        for k, p in parts.items():
            r = roles.get(k)
            if p.kind == "SEGMENT" and r is not None and r.role == "STRUCTURAL_OBSTACLE":
                cand.setdefault(k.rsplit("|", 1)[0], []).append(k)
        for e, keys in sorted(cand.items()):
            segs = {k: parts[k].geometry for k in keys}
            ys = sorted({round(v, 6) for g in segs.values() for v in (g[1], g[3])})
            xs = (min(min(g[0], g[2]) for g in segs.values()), max(max(g[0], g[2]) for g in segs.values()))
            long = sorted(k for k, g in segs.items() if abs(g[1] - g[3]) < TOL and round(g[1], 6) in fy)
            both = {round(segs[k][1], 6) for k in long} == set(fy)
            overlap = min(xs[1], bx[1]) - max(xs[0], bx[0])
            depth = round((ys[-1] - ys[0]) * u, 3)
            if long:
                ent[e] = {"depth_mm": depth, "length_mm": round((xs[1] - xs[0]) * u, 3), "collinear_faces": long,
                          "both_long_faces_collinear": both, "overlaps_band_faces_mm": round(max(overlap, 0) * u, 3),
                          "depth_equals_band_width": abs(depth - thick["width"] * u) < 0.5}
                ent[e]["matches"] = both and overlap > 0 and ent[e]["depth_equals_band_width"]
    matches = sorted(e for e, v in ent.items() if v["matches"])
    stagger = None
    if len(bands) == 2:
        tops = sorted(max(parts[f].geometry[1] for f in (b["face_a"], b["face_b"])) for b in bands)
        stagger = round((tops[1] - tops[0]) * u, 3)
    door = new["openings"]["I1471"]
    return {"bands": rec, "stagger_mm": stagger, "door_record": {k: door.get(k) for k in
                                                                ("state", "closure_a", "closure_b", "closure_b_rule",
                                                                 "closure_b_evidence", "width")},
            "column": {"deterministic": len(matches) == 1, "column": matches[0] if len(matches) == 1 else None,
                       "candidates": ent,
                       "rule": "a STRUCTURAL_OBSTACLE column whose two long faces are collinear with the two faces of "
                               "the 200 mm band, whose depth equals the band width and whose extent overlaps the band "
                               "faces"}}


def closures(cr19):
    """The CURRENT closure packets (rebuilt by the R8.19 construction from this run) with review states and the release
    model. cr19: the freshly rebuilt CLOSURE_RELEASE_STATUS register."""
    base, pk = cr19, cr19["review_packets"]
    reviews = {r["closure_name"]: r for r in jl(ROOT / "data/registry/OWNER_CLOSURE_REVIEWS.json")["reviews"]}
    fz18 = jl(REG18 / "R8_18_FREEZE.json")["unchanged"]
    door_frozen = [T.DOOR_CLOSURE_POLICY_ID, T.door_closure_policy_record()["digest"]] == fz18["door_opening_closure"]
    out = {}
    for name, p in pk.items():
        cid = p.get("closure_id", name)
        rs = RV.review_state(reviews.get(name), closure=cid, current_digest=RV.record_digest(p["record"]))
        if name == "I1471":
            ev = {"POLICY_FROZEN": door_frozen, "CROSS_ROUTE_AGREEMENT": None,
                  "OWNER_OR_SOURCE_CORROBORATION": True, "SOURCE_ANCHOR": False,
                  "HUMAN_REVIEW": rs["satisfies_human_review"]}
            base_level = CR.LEVELS[2]
        else:
            b = base["closures"][cid]
            ev = {"POLICY_FROZEN": b["evidence"]["POLICY_FROZEN"], "CROSS_ROUTE_AGREEMENT": None,
                  "OWNER_OR_SOURCE_CORROBORATION": b["evidence"]["OWNER_OR_SOURCE_CORROBORATION"],
                  "SOURCE_ANCHOR": False, "HUMAN_REVIEW": rs["satisfies_human_review"]}
            base_level = b["level"]
        out[name] = {"closure_id": cid, "packet_digest_now": RV.record_digest(p["record"]),
                     "packet_digest_reviewed": (reviews.get(name) or {}).get("packet_digest"),
                     "packet_digest_r8_19": p["closure_digest"], "review": rs, "base_level": base_level,
                     "evaluation": CR.evaluate(base_level, ev), "record": p["record"]}
    return out


def regression(ctx):
    """Every published quantity of the rebuild vs the committed R8.19 registers (must be identical)."""
    s19 = jl(REG19 / "QORTUBA_R8_19_STATUS.json")
    rb, rows = ctx["r8_19"], ctx["rows_new"]
    now = {rid: rows[rid]["value"] for rid in s19["six_rows"]}
    now |= {k: v["COMPLETE_M2"] for k, v in rb["trade_rows"].items()}
    now |= {"SKIRTING": ctx["skirting_v4"]["PAYABLE_LM"], "HIDDEN_PROFILE": ctx["skirting_v4"]["PAYABLE_LM"]}
    now |= {k: ctx["marble_quantities"][k] for k in ("MARBLE_THRESHOLD_PLAN_AREA_M2", "MARBLE_THRESHOLD_LENGTH_LM")}
    now |= dict(rb["waterproofing"]["totals"])
    ex = s19["extra_rows"]
    was = {rid: v["VALUE"] for rid, v in s19["six_rows"].items()}
    was |= {k: ex[k]["COMPLETE_M2"] for k in rb["trade_rows"]}
    was |= {"SKIRTING": ex["SKIRTING"]["value_lm"], "HIDDEN_PROFILE": ex["HIDDEN_PROFILE"]["value_lm"],
            "MARBLE_THRESHOLD_PLAN_AREA_M2": ex["MARBLE_THRESHOLD"]["MARBLE_THRESHOLD_PLAN_AREA_M2"],
            "MARBLE_THRESHOLD_LENGTH_LM": ex["MARBLE_THRESHOLD"]["MARBLE_THRESHOLD_LENGTH_LM"],
            "WATERPROOFING_FLOOR_M2": ex["WATERPROOFING_FLOOR_M2"]["value_m2"],
            "WATERPROOFING_UPTURN_LM": ex["WATERPROOFING_UPTURN_LM"]["value_lm"]}
    rows_cmp = {k: {"R8.19": was[k], "R8.20": now[k], "unchanged": was[k] == now[k]} for k in sorted(was)}
    six = {rid: R19G.R18G.R17G.R16G.R15G._row_view(rid, rows[rid], ctx["dig"][rid]) for rid in s19["six_rows"]}
    dig = {rid: {k: ("SAME" if six[rid][k] == s19["six_rows"][rid][k] else "CHANGED")
                 for k in ("TOPOLOGY_DIGEST", "ROW_AUTHORITY_DIGEST", "RELEASE_INPUT_DIGEST")} for rid in six}
    return {"rows": rows_cmp, "all_unchanged": all(v["unchanged"] for v in rows_cmp.values()), "digests": dig,
            "all_digests_same": all(set(v.values()) == {"SAME"} for v in dig.values()),
            "reproduces_r8_19_blind": ctx["reproduces_r8_19_blind"]}


def build(work, commit=None):
    ctx = Q19.build(work, commit)
    new, inp = ctx["new"], ctx["inp_new"]
    phys = {f["fact_id"]: f for f in jl(ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json")["facts"]}
    f = OF.from_record(phys[FACT])
    ctx["i1471_fact"], ctx["i1471_fact_binding"] = phys[FACT], OF.bind(f, inp)
    ctx["i1471_fact_domains"] = list(f.allowed_domains)
    ctx["i1471_evidence"] = i1471_evidence(new, inp)
    ctx["regression_20"] = regression(ctx)
    return ctx


def main(work, regdir, commit=None):
    import r8_20_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))                  # closures_20 is set by the registers
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["evaluation"]["level"], v["review"]["state"], v["evaluation"]["missing_for_reviewed"])
                      for k, v in ctx["closures_20"].items()} | {"unchanged": ctx["regression_20"]["all_unchanged"]},
                     indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
