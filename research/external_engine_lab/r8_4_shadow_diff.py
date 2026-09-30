"""R8.4 §23-§27 — SHADOW row-by-row diff: current published / register rows vs canonical frame + profile.

Research lab only. Reads (never writes) the current row sets:
    Al Rashed  pa09_alrashed/ALRASHED_DETAILED_QUANTITY_EXPORT.json         (265 records)
    Qortuba    pa08_qortuba_boq/APPROVED_QUANTITIES.json                    (28 rows)
    P7757      pa07r3/PA07_QUANTITY_SAFETY_REGISTER.json                    (585 rows)
and computes, per row, what the canonical engine/source stack (frame release V2, CAD profile V2,
parser policy V2, reference designation) would permit. Values are NOT recomputed: the shadow
changes status only, so every value delta is VALUE_IDENTICAL or NOT_COMPARABLE, and that is stated.

Delta classes (one primary per row):
    VALUE_IDENTICAL_STATUS_IDENTICAL / _DOWNGRADED / _UPGRADED   level comparison (FINAL > PREVIEW > BLOCKED)
    FRAME_BLOCKS_CURRENT_FINAL        a current FINAL row whose canonical frame does not permit FINAL
    SOURCE_PROFILE_BLOCKS             frame would permit FINAL, a CAD_PROFILE requirement does not
    DOWNSTREAM_UNSUPPORTED            only I_DOWNSTREAM blocks
    COUNT_UNAFFECTED                  a count method (scale_dependent False) whose count gate holds
    NOT_COMPARABLE                    no current value / not applicable / method undeclared
    VALUE_CHANGED_SOURCE_GEOMETRY     reserved: needs a canonical re-measurement (not done in R8.4)

    python3 research/external_engine_lab/r8_4_shadow_diff.py <out_dir>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import cad_profile as P, decoder_pins as PINS, frame as FR          # noqa: E402
from engine.source import qualification as Q, region_candidates as RC                  # noqa: E402
from engine.source.cad import census, kernel as K1, libredwg_map as L, unit_evidence as UE   # noqa: E402
from engine.source.conservation import conservation                                     # noqa: E402

from r8_4_qualification import SOURCES, full_source_sha, load, sha                      # noqa: E402
from r8_4_regions import ROLE_REGISTERS, adapter_windows                                # noqa: E402

EXP = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01"
ROWS = {"ALRASHED": EXP / "pa09_alrashed/ALRASHED_DETAILED_QUANTITY_EXPORT.json",
        "QORTUBA": EXP / "pa08_qortuba_boq/APPROVED_QUANTITIES.json",
        "P7757": EXP / "pa07r3/PA07_QUANTITY_SAFETY_REGISTER.json"}
LAYER_PROFILES = {"P7757": EXP / "pa07r3/supervised/LAYER_PROFILE.json",
                  "ALRASHED": EXP / "pa09_alrashed/blind/LAYER_PROFILE.json",
                  "QORTUBA": EXP / "pa08_qortuba/blind/LAYER_PROFILE.json"}
LEVEL = {"FINAL": 3, "PREVIEW": 2, "COUNT_ONLY": 1, "BLOCKED": 0}
SCALE_UNITS = {"m2": True, "M2": True, "lm": True, "LM": True, "m": True, "m3": True, "M3": True,
               "nr": False, "NR": False, "NO": False, "no": False, "EA": False}


def current_level(project, row):
    st = row.get("STATUS") or row.get("QUANTITY_STATUS")
    if project == "P7757":
        return ("NON_FINAL" if not row.get("BRIDGE_ALLOWED") else "FINAL"), st
    if st in ("FINAL_QUANTITY_AVAILABLE", "FINAL"):
        return "FINAL", st
    if st in ("NOT_APPLICABLE",):
        return "NOT_APPLICABLE", st
    return "NON_FINAL", st


def overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def dominant_candidate(bounds, cands):
    best = max(cands, key=lambda c: overlap(bounds, c.bounds), default=None)
    return best if best is not None and overlap(bounds, best.bounds) > 0 else None


class Project:
    def __init__(self, name):
        s = SOURCES[name]
        self.name = name
        self.path = next(ROOT / d for d in s["decodes"] if (ROOT / d).exists())
        self.src = full_source_sha(name)
        self.decode = load(self.path)
        self.doc = L.to_document(self.decode, source_sha256=self.src)
        self.real = K1.realise(self.doc)
        cons = conservation(self.doc, self.real, raw_entity_rows=self.doc.notes.get("raw_entity_rows"))
        self.balanced = all(cons[k]["BALANCED"] for k in ("source_level", "observation_level", "visit_level"))
        self.census = census.capability_register(self.doc, self.real)
        self.profile = Q.source_feature_profile(self.doc, self.decode)
        ex = UE.extract(self.decode, self.src)
        ins = self.decode.get("HEADER", {}).get("INSUNITS")
        self.uc = {pid: FR.unit_context(self.src, "MODEL_SPACE", FR.MODEL_SPACE, ex["evidence"], insunits=ins, policy=pol)
                   for pid, pol in (("V1", FR.RELEASE_V1), ("V2", FR.RELEASE_V2))}
        self.unit_findings = tuple(ex["findings"])
        self.cands = RC.candidates(self.doc, self.real, "MODEL_SPACE")["candidates"]
        roles = json.loads(ROLE_REGISTERS[name].read_text()) if ROLE_REGISTERS[name].exists() else {"VIEWS": []}
        self.views = {v["VIEW_ID"]: v for v in roles["VIEWS"]}
        self.decode_sha = sha(self.path)
        self.pin = PINS.decode_status(self.decode_sha)
        self.ctx = P.SourceValidationContext(self.balanced, self.pin, PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"],
                                             tuple(f for f in self.doc.findings if f.obs_id is None),
                                             feature_profile=self.profile)
        self._region_cache = {}
        self._layers_by_cand = self._layers()
        self._insert_at = {o.obs_id: o.geometry.insertion for o in self.doc.entities
                           if o.kind == "INSERT" and hasattr(o.geometry, "insertion")}

    def locator(self, bounds, unplaceable_in_scope=True):
        """Place a census row: inside a block instance -> the root INSERT's insertion point;
        top-level without realisable geometry -> None (kept in scope: fail closed), or False in the
        sensitivity variant."""
        def where(row):
            path = row.get("instance_path") or []
            at = self._insert_at.get(path[0]) if path else None
            if at is None:
                return None if unplaceable_in_scope else False
            if bounds is None:
                return None if unplaceable_in_scope else False
            return bounds[0] <= at[0] <= bounds[2] and bounds[1] <= at[1] <= bounds[3]
        return where

    def _layers(self):
        """V-CAD-5 profile-relevant layers: the active path's own deterministic LAYER_PROFILE roles
        (walls, openings, dimensions, labels). Columns have no role in that profile: recorded as a gap."""
        prof = json.loads(LAYER_PROFILES[self.name].read_text())["BY_SOURCE"]
        v = next(iter(prof.values()))
        layers = set(v.get("WALL_LAYERS") or []) | set(v.get("DIMENSION_LAYERS") or []) | \
            set(v.get("TEXT_LAYERS") or []) | set(v.get("GLAZING_LAYERS") or []) | ({v["DOOR_LAYER"]} if v.get("DOOR_LAYER") else set())
        self.relevant_layers = sorted(layers)
        return {c.candidate_id: layers for c in self.cands}

    # ---- region mapping (candidate ≠ designation; no designation is ACCEPTED in R8.4)
    def region_of(self, row):
        if self.name == "QORTUBA":
            label = "SECOND FLOOR PLAN"
            c = next((c for c in self.cands if any(label in e[2] for e in c.role_evidence)), None)
            return c, "engine PLAN candidate labelled " + repr(label) if c else "no candidate carries the row's title"
        if self.name == "ALRASHED":
            win = adapter_windows().get(row.get("FLOOR"))
            if win is None:
                return None, f"floor {row.get('FLOOR')!r} has no adapter plan window"
            x0, x1, y0, y1 = win
            return dominant_candidate((x0, y0, x1, y1), self.cands), "adapter window (PENDING_REVIEW) -> dominant cluster"
        v = self.views.get(row.get("VIEW_ID"))
        if not v:
            return None, "view not in the active-path role register"
        f = self.uc["V2"].declared_native_to_mm or 1.0
        b = [x / f for x in v["BBOX_MM"]]
        return dominant_candidate(b, self.cands), "active-path view bbox / declared unit -> dominant cluster"

    def plan_hint(self, row, cand):
        """An active-path FLOOR_PLAN role is a candidate hint for the dominant cluster of its view."""
        if self.name != "P7757":
            return False
        v = self.views.get(row.get("VIEW_ID")) or {}
        return v.get("FINAL_ROLE") == "FLOOR_PLAN"

    def evaluate(self, cand, hint, policy_id="V2"):
        key = (cand.candidate_id if cand else None, hint, policy_id)
        if key in self._region_cache:
            return self._region_cache[key]
        uc = self.uc[policy_id]
        pol = FR.RELEASE_V1 if policy_id == "V1" else FR.RELEASE_V2
        if cand is None:
            rt = FR.region_transform(uc, "UNMAPPED", FR.MODEL_SPACE_UNKNOWN, policy=pol)
            layers = set(next(iter(self._layers_by_cand.values()), set()))
        else:
            role = RC.PLAN if hint and cand.role_candidate == RC.UNKNOWN else cand.role_candidate
            kind = RC.KIND_FOR_ROLE[role]
            rt = FR.region_transform(uc, cand.candidate_id, kind, bounds=cand.bounds, policy=pol,
                                     reference=(policy_id == "V1" and kind == FR.MODEL_SPACE_PLAN))
            layers = self._layers_by_cand.get(cand.candidate_id, set())
        fr = FR.measurement_frame(uc, rt, policy=pol)
        parser = P.PARSER_POLICY_V1 if policy_id == "V1" else P.PARSER_POLICY_V2
        method = P.MeasurementMethod("SCALE_DEPENDENT", True)
        bounds = cand.bounds if cand is not None else None
        variants = {}
        for label, keep in (("FAIL_CLOSED", True), ("UNPLACEABLE_EXCLUDED", False)):
            rfind = P.region_class_findings(self.census, rt.region_id, layers, self.locator(bounds, keep)) + \
                list(self.unit_findings)
            res = P.evaluate("LINE", "REGION_REPRESENTATIVE", (), method, self.ctx, fr, uc, rt, region_findings=rfind,
                             parser_policy=parser)
            variants[label] = (res, rfind)
        res, rfind = variants["FAIL_CLOSED"]
        out = {"region_id": rt.region_id, "region_kind": rt.region_kind, "region_status": rt.status,
               "region_reason": rt.status_reason, "unit_status": uc.status, "frame_status": fr.status,
               "frame_uses": list(fr.allowed_use), "profile": res, "v_cad": P.v_cad_view(res, rfind),
               "release": P.region_release(res),
               "vcad5_findings": sum(1 for f in rfind if f.code in P.UNREALISED_CLASS_CODES and f.blocking_domains),
               "vcad5_detail": [f.detail for f in rfind if f.code in P.UNREALISED_CLASS_CODES and f.blocking_domains][:10],
               "sensitivity_release_unplaceable_excluded": P.region_release(variants["UNPLACEABLE_EXCLUDED"][0]),
               "sensitivity_blocking_unplaceable_excluded": [r[0] for r in variants["UNPLACEABLE_EXCLUDED"][0].blocking]}
        self._region_cache[key] = out
        return out


def classify(cur_level, canon, method_scale, has_value):
    if cur_level == "NOT_APPLICABLE" or method_scale is None:
        return "NOT_COMPARABLE", "NOT_COMPARABLE"
    if method_scale is False:
        return ("COUNT_UNAFFECTED" if canon["release"] != "BLOCKED" else "SOURCE_PROFILE_BLOCKS"), "COUNT"
    rel = canon["release"]
    cl = "FINAL" if cur_level == "FINAL" else "PREVIEW"          # a non-final current row is visible as a preview
    d = LEVEL[rel] - LEVEL[cl]
    status_delta = "IDENTICAL" if d == 0 else ("DOWNGRADED" if d < 0 else "UPGRADED")
    if cur_level == "FINAL" and rel != "FINAL":
        req = {r[0]: r[1] for r in canon["profile"].requirements}
        if FR.FINAL_MEASUREMENT not in canon["frame_uses"]:
            primary = "FRAME_BLOCKS_CURRENT_FINAL"
        elif [k for k, v in req.items() if v == "FAIL"] == ["I_DOWNSTREAM"]:
            primary = "DOWNSTREAM_UNSUPPORTED"
        else:
            primary = "SOURCE_PROFILE_BLOCKS"
    else:
        primary = f"VALUE_IDENTICAL_STATUS_{status_delta}" if has_value else "NOT_COMPARABLE"
    return primary, status_delta


def row_value(project, row):
    if project == "P7757":
        return None, None
    return row.get("MEASURED_QUANTITY"), row.get("MEASURED_UNIT")


def row_id(project, row, i):
    if project == "ALRASHED":
        return f"{row.get('ITEM_CODE')}|{row.get('COMPONENT_REF')}|{row.get('TRADE')}|{i}"
    if project == "QORTUBA":
        return f"{row.get('SUBITEM')}|{row.get('ITEM')}"
    return row.get("SAFETY_ID")


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    diff, status = {}, {}
    for name in ("QORTUBA", "ALRASHED", "P7757"):
        proj = Project(name)
        data = json.loads(ROWS[name].read_text())
        rows = data.get("RECORDS") or data.get("ROWS")
        out = []
        for i, row in enumerate(rows):
            cand, how = proj.region_of(row)
            hint = proj.plan_hint(row, cand)
            canon = proj.evaluate(cand, hint)
            cur, raw = current_level(name, row)
            val, unit = row_value(name, row)
            scale = SCALE_UNITS.get(unit) if unit is not None else (True if name == "P7757" else None)
            primary, sd = classify(cur, canon, scale, val is not None)
            blockers = [r[0] for r in canon["profile"].blocking]
            out.append({"row_id": row_id(name, row, i), "current_status": raw, "current_level": cur,
                        "current_value": val, "unit": unit,
                        "method_scale_dependent": scale,
                        "region_mapping": how, "region_candidate": cand.candidate_id if cand else None,
                        "region_role_candidate": (RC.PLAN if hint and cand and cand.role_candidate == RC.UNKNOWN
                                                  else (cand.role_candidate if cand else None)),
                        "canonical": {"UNIT_CONTEXT": canon["unit_status"], "REGION": canon["region_status"],
                                      "REGION_REASON": canon["region_reason"], "FRAME": canon["frame_status"],
                                      "CAD_PROFILE": "FINAL_ELIGIBLE" if canon["profile"].final_eligible else
                                      ("PREVIEW_ELIGIBLE" if canon["release"] == "PREVIEW" else "BLOCKED"),
                                      "CAD_PROFILE_BLOCKING": blockers, "V_CAD": canon["v_cad"]},
                        "eligibility": canon["release"],
                        "eligibility_if_unplaceable_unrealised_excluded": canon["sensitivity_release_unplaceable_excluded"],
                        "canonical_value": val, "value_delta": "VALUE_IDENTICAL (not recomputed in R8.4)"
                        if val is not None else "NOT_COMPARABLE (no current value)",
                        "status_delta": sd, "delta_class": primary})
        final_rows = [r for r in out if r["current_level"] == "FINAL"]
        summary = {"rows": len(out), "current_FINAL": len(final_rows),
                   "current_FINAL_becomes": dict(Counter(r["eligibility"] for r in final_rows)),
                   "delta_class": dict(Counter(r["delta_class"] for r in out)),
                   "eligibility": dict(Counter(r["eligibility"] for r in out)),
                   "method_undeclared": sum(1 for r in out if r["method_scale_dependent"] is None
                                            and r["current_level"] != "NOT_APPLICABLE"),
                   "count_methods": sum(1 for r in out if r["method_scale_dependent"] is False),
                   "current_FINAL_becomes_if_unplaceable_excluded": dict(Counter(
                       r["eligibility_if_unplaceable_unrealised_excluded"] for r in final_rows)),
                   "eligibility_if_unplaceable_excluded": dict(Counter(
                       r["eligibility_if_unplaceable_unrealised_excluded"] for r in out)),
                   "value_changes": 0}
        diff[name] = {"rows_source": str(ROWS[name].relative_to(ROOT)), "rows_source_sha256": sha(ROWS[name]),
                      "summary": summary, "rows": out}
        regions = {}
        for (cid, hint, pid), v in proj._region_cache.items():
            regions[f"{cid}|hint={hint}|{pid}"] = {k: (v[k] if k != "profile" else v[k].as_dict()) for k in v}
        for pid in ("V1",):
            for cid in {r["region_candidate"] for r in out}:
                cand = next((c for c in proj.cands if c.candidate_id == cid), None)
                v = proj.evaluate(cand, False, pid)
                regions[f"{cid}|hint=False|{pid}"] = {k: (v[k] if k != "profile" else v[k].as_dict()) for k in v}
        status[name] = {"source_sha256": proj.src, "decode": str(proj.path.relative_to(ROOT)),
                        "decode_sha256": proj.decode_sha, "decode_pin_status": proj.pin,
                        "conservation_balanced": proj.balanced,
                        "unit_context_V2": proj.uc["V2"].as_dict(), "unit_context_V1": proj.uc["V1"].as_dict(),
                        "feature_profile": proj.profile.as_dict(),
                        "decoder_qualification": Q.qualification_for(proj.ctx.decoder_binary_sha256, proj.profile, ()),
                        "regions_evaluated": regions, "human_confirmations_supplied": 0,
                        "accepted_designations": 0, "profile_relevant_layers": proj.relevant_layers,
                        "profile_relevant_layers_basis": "active-path LAYER_PROFILE roles (walls, doors, glazing, dimensions, text); "
                                                         "no column role in that profile"}
        print(name, json.dumps(summary))
    (out_dir / "SHADOW_ROW_DIFF.json").write_text(json.dumps(
        {"SCHEMA": "URBAN_R8_4_SHADOW_ROW_DIFF_V1", "policies": {"frame": FR.DEFAULT_POLICY.policy_id,
                                                                "cad_profile": P.DEFAULT_CAD_PROFILE.profile_id,
                                                                "parser": P.DEFAULT_PARSER_POLICY.policy_id},
         "outputs_modified": False, "values_recomputed": False, "projects": diff}, indent=1, ensure_ascii=False,
        default=str))
    (out_dir / "REAL_PROJECT_R8_4_STATUS.json").write_text(json.dumps(
        {"SCHEMA": "URBAN_R8_4_REAL_PROJECT_STATUS_V1", "projects": status}, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_4")
