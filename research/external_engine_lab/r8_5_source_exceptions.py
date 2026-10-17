"""R8.5 §10-§14 — SOURCE_EXCEPTION_REGISTER: every unrealised source object, every region the rows use.

Research lab only (SHADOW). Classification is engine/source/source_exceptions.py (positive evidence
only). This script supplies what engine/source must not hold: the explicit profile-relevant LAYER ROLES
with their reasons (active-path LAYER_PROFILE + each project adapter's declared layer roles, read-only),
and the regions the current rows are measured in (R8.4 shadow mapping).

    python3 research/external_engine_lab/r8_5_source_exceptions.py <out_dir>
"""

from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import cad_profile as P, source_exceptions as SX                  # noqa: E402
from engine.source import region_candidates as RC                                      # noqa: E402
from engine.source.cad import census, kernel as K1, libredwg_map as L                  # noqa: E402

from r8_4_qualification import SOURCES, full_source_sha, load                          # noqa: E402

EXP = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01"
LAYER_PROFILES = {"P7757": EXP / "pa07r3/supervised/LAYER_PROFILE.json",
                  "ALRASHED": EXP / "pa09_alrashed/blind/LAYER_PROFILE.json",
                  "QORTUBA": EXP / "pa08_qortuba/blind/LAYER_PROFILE.json"}
ADAPTER_LAYER_FILES = {
    "ALRASHED": (ROOT / "research/qs_wall_treatment_01/pa09/alrashed/geometry.py",
                 {"WALL_LAYERS": "wall", "COLUMN_LAYERS": "column", "DOOR_LAYERS": "opening (door)",
                  "WINDOW_LAYERS": "opening (window)", "STAIR_LAYERS": "stair", "BOUNDARY_LAYERS": "boundary",
                  "ROOF_LAYERS": "roof"}),
    "QORTUBA": (ROOT / "research/qs_wall_treatment_01/pa08/qortuba/boq/material_identity.py",
                {"WALL_LAYERS": "wall"}),
}
R84 = ROOT / "research/external_engine_lab/outputs/r8_4/SHADOW_ROW_DIFF.json"


def adapter_layers(name):
    """Layer-role constants of a project adapter, parsed (never imported, never modified)."""
    if name not in ADAPTER_LAYER_FILES:
        return {}
    path, names = ADAPTER_LAYER_FILES[name]
    tree = ast.parse(path.read_text())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            key = node.targets[0].id
            if key in names:
                try:
                    vals = ast.literal_eval(node.value)
                except ValueError:
                    continue
                for v in (vals if isinstance(vals, (list, tuple, set)) else [vals]):
                    out.setdefault(v, []).append(f"adapter {path.name} {key} ({names[key]})")
    return out


def relevant_layers(name):
    """{layer: reason}. Profile roles per the spec: walls, openings, columns, labels, dimensions."""
    prof = next(iter(json.loads(LAYER_PROFILES[name].read_text())["BY_SOURCE"].values()))
    rel = {}
    for key, role in (("WALL_LAYERS", "wall-like"), ("DIMENSION_LAYERS", "dimension"), ("TEXT_LAYERS", "label/text"),
                      ("GLAZING_LAYERS", "glazing")):
        for lay in prof.get(key) or []:
            rel.setdefault(lay, []).append(f"active-path LAYER_PROFILE {key} ({role})")
    if prof.get("DOOR_LAYER"):
        rel.setdefault(prof["DOOR_LAYER"], []).append("active-path LAYER_PROFILE DOOR_LAYER (opening)")
    for lay, why in adapter_layers(name).items():
        rel.setdefault(lay, []).extend(why)
    return {k: "; ".join(v) for k, v in rel.items()}


class Source:
    def __init__(self, name):
        s = SOURCES[name]
        self.name = name
        self.path = next(ROOT / d for d in s["decodes"] if (ROOT / d).exists())
        self.src = full_source_sha(name)
        self.decode = load(self.path)
        self.doc = L.to_document(self.decode, source_sha256=self.src)
        self.real = K1.realise(self.doc)
        self.census = census.capability_register(self.doc, self.real)
        self.unrealised = [r for r in self.census if r["code"] in P.UNREALISED_CLASS_CODES]
        self.raw = {str(L.handle_id(o.get("handle"))): o for o in self.decode["OBJECTS"] if isinstance(o.get("handle"), list)}
        self.classes = {c["number"]: c for c in self.decode.get("CLASSES", [])}
        self.cands = {c.candidate_id: c for c in RC.candidates(self.doc, self.real, "MODEL_SPACE")["candidates"]}
        self.rel = relevant_layers(name)

    def regions(self):
        rows = json.loads(R84.read_text())["projects"][self.name]["rows"]
        used = Counter(r["region_candidate"] for r in rows)
        return [(cid, self.cands[cid].bounds if cid in self.cands else None, n) for cid, n in sorted(used.items(), key=str)]

    def classify(self, region_id, bounds):
        out = []
        for r in self.unrealised:
            raw = self.raw.get(str(r["handle"])) or {}
            e = SX.classify(r, raw, self.classes.get(r["type_code"]), self.doc, region_id or "UNMAPPED", bounds, self.rel)
            out.append((e, tuple((i["domain"], i["severity"]) for i in r.get("impacts", ()))))
        return out

    def raw_summary(self, r):
        raw = self.raw.get(str(r["handle"])) or {}
        keep = ("entity", "dxfname", "_subclass", "type", "ownerhandle", "entmode", "invisible", "pt0", "uvec", "vvec",
                "size", "imagedef", "preview_exists", "preview_size", "mode")
        d = {k: raw.get(k) for k in keep if k in raw}
        cr = self.classes.get(r["type_code"])
        d["class_record"] = {k: cr.get(k) for k in ("number", "dxfname", "cppname", "appname", "proxyflag")} if cr else None
        if raw.get("entity") == "IMAGE" and isinstance(raw.get("imagedef"), list):
            idef = self.raw.get(str(raw["imagedef"][-1])) or {}
            d["imagedef_file_path"] = idef.get("file_path")
        d["text_content"] = SX.text_content_class(raw)
        return d


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    register = {"SCHEMA": "URBAN_R8_5_SOURCE_EXCEPTION_REGISTER_V1", "states": list(SX.STATES),
                "rule": ("V-CAD-5 unchanged; an unrealised object is non-blocking only in a state established by positive "
                         "source evidence (engine/source/source_exceptions.py); unresolved = blocking on a profile-relevant "
                         "layer (fail closed)"), "projects": {}}
    for name in ("P7757", "ALRASHED", "QORTUBA"):
        s = Source(name)
        objs = {}
        for r in s.unrealised:
            objs[r["obs_id"]] = {"obs_id": r["obs_id"], "handle": r["handle"], "code": r["code"],
                                 "source_type": r["source_type"], "layer": r["layer"],
                                 "layer_relevance": s.rel.get(r["layer"]), "instance_path": r["instance_path"],
                                 "capability_impacts": r["impacts"], "raw": s.raw_summary(r), "by_region": {}}
        regions = s.regions()
        vcad = {}
        for cid, bounds, nrows in regions:
            cl = s.classify(cid, bounds)
            for e, _ in cl:
                objs[e.obs_id]["by_region"][e.region_id] = {k: v for k, v in e.as_dict().items()
                                                            if k not in ("obs_id", "handle", "code", "source_type", "layer",
                                                                         "instance_path")}
            f = SX.region_findings(cl)
            blocking = [e.as_dict() for (e, _), ff in zip(cl, f) if ff.blocking_domains]
            vcad[cid or "UNMAPPED"] = {"rows": nrows, "bounds": bounds, "V-CAD-5": "FAIL" if blocking else "PASS",
                                       "blocking_objects": [(b["handle"], b["source_type"], b["state"]) for b in blocking],
                                       "states": dict(Counter(e.state for e, _ in cl))}
        register["projects"][name] = {"source_sha256": s.src, "relevant_layers": s.rel,
                                      "unrealised_objects": len(s.unrealised), "objects": list(objs.values()),
                                      "regions": vcad}
        print(name, len(s.unrealised), {k: (v["V-CAD-5"], v["states"]) for k, v in vcad.items()})
    (out_dir / "SOURCE_EXCEPTION_REGISTER.json").write_text(json.dumps(register, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_5")
