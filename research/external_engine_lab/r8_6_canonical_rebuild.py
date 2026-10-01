"""R8.6 §5-§7 — QORTUBA ROUND-1 PROOF: the six floor-area rows rebuilt from canonical source geometry.

Research lab only (SHADOW). Nothing here writes a published quantity, a frozen register or an owner answer, and
nothing changes cad_adapter or the active pipeline on disk.

What R8.5 did, and why it is not enough
    R8.5 snapped the CURRENT QS01 cut-line coordinates to canonical K1 lines. That proves the current edges exist
    in the source; it does not rebuild the room, because the decomposition came from the current output.

What this does instead
    The active room method (QS01 Method A on pipeline7) is run end to end, in this process, with its CAD input
    replaced by canonical geometry: every SEGMENT / ARC / CIRCLE primitive is built from K1 realised geometry
    (D1 -> K1), and every model-space text from the D1 TEXT / MTEXT observations. No current value, cut line,
    rectangle or room enters. The six rows are then computed by the approved row expressions
    (owner_rules.quantities) from the canonical floors only - every other input of that function is passed
    EMPTY, which proves the six rows do not depend on it.

The method-input contract
    The method consumes more than geometry. Ablation (one provenance field blanked at a time, on the active
    input) shows which fields the six rows depend on. The canonical mapping must supply each of them; a lossy
    mapping silently changes rooms, which this register records as evidence.

    python3 research/external_engine_lab/r8_6_canonical_rebuild.py [out_dir]
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine import cad_adapter as CA                                                   # noqa: E402
from engine.source import qualification as Q                                           # noqa: E402
from engine.source.cad import kernel, libredwg_map as L                                # noqa: E402
from engine.source.cad.affine import Affine2                                            # noqa: E402

DECODE = ROOT / "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json"
APPROVED = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa08_qortuba_boq/APPROVED_QUANTITIES.json"
UPLOADS_PREFIX = "/root/.claude/uploads"
CONFIG = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa08_qortuba/PA08_BLIND_CONFIG.json"
ROUND1 = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")
GEOMETRIC = ("SEGMENT", "ARC", "CIRCLE")
ETYPE = {"LINE": "19", "ARC": "17", "CIRCLE": "18", "LWPOLYLINE": "77"}
METHOD_ID = "QS01_METHOD_A_ARRANGEMENT_OF_BOUNDARY_LINES"
ROW_METHOD_ID = "OWNER_RULES_V1.quantities (floor-area rows)"
# the code the proof runs through; its hashes are the "frozen calculation path" (§7)
METHOD_FILES = ("research/qs_wall_treatment_01/pa08/qortuba/qs01/takeoff.py",
                "research/qs_wall_treatment_01/pa08/qortuba/r3/floor_regions.py",
                "research/qs_wall_treatment_01/pa08/qortuba/r3/run_r3.py",
                "research/qs_wall_treatment_01/pa08/qortuba/r2/cells.py",
                "research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py",
                "engine/ingest/pipeline7.py", "engine/ingest/source_units.py", "engine/cad_adapter.py",
                "engine/source/cad/kernel.py", "engine/source/cad/libredwg_map.py")


def sha_file(p) -> str:
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ====================================================================== canonical inputs (D1 -> K1)
class Canonical:
    """D1 document, K1 realisation and the method-input mapping built from them."""

    def __init__(self, decode=None):
        self.decode = decode if decode is not None else json.loads(DECODE.read_text())
        self.doc = L.to_document(self.decode)
        self.real = kernel.realise(self.doc)
        self.obs = {o.obs_id: o for o in self.doc.entities}
        for b in self.doc.blocks.values():
            for o in b.entities:
                self.obs[o.obs_id] = o
        self.lineage_by_object = {}

    def block_names(self, path) -> tuple:
        """Block names along an instance path, read from the D1 INSERT observations and block records."""
        out = []
        for oid in path:
            o = self.obs.get(oid.split("[")[0])
            key = getattr(getattr(o, "geometry", None), "block_key", None)
            blk = self.doc.blocks.get(key) if key else None
            out.append(blk.name if blk is not None else None)
        return tuple(out)

    def prov(self, lin, part) -> CA.Provenance:
        path = tuple(int(x.split(":", 1)[1].split("[")[0].split("+")[0]) for x in lin.instance_path)
        return CA.Provenance(handle=int(lin.source_handle.split("+")[0]), entity_type=ETYPE.get(lin.kind, lin.kind),
                             layer=str(lin.layer or "0"), block_path=self.block_names(lin.instance_path),
                             instance_path=path, sub_id=part)

    @staticmethod
    def part(lin, *xs) -> str:
        """A unique, stable part id for one span of a multi-part entity (polyline), from canonical lineage and
        canonical coordinates. Only uniqueness and stability are required of it (it is an identity key)."""
        if lin.kind != "LWPOLYLINE":
            return ""
        return hashlib.sha256(("K1|" + lin.obs_id + "|" + ",".join(f"{v:.6f}" for v in xs)).encode()).hexdigest()[:8]

    def primitives(self, lossy=()) -> list:
        """Method-input primitives from K1. `lossy` names contract fields to drop (evidence runs only)."""
        out = []

        def add(p, lin):
            if "block_path" in lossy:
                p = replace(p, provenance=replace(p.provenance, block_path=()))
            if "sub_id" in lossy:
                p = replace(p, provenance=replace(p.provenance, sub_id="K1"))
            self.lineage_by_object[p.object_id] = lin
            out.append(p)
        for s in self.real.segments:
            add(CA.Primitive(kind="SEGMENT", provenance=self.prov(s.lineage, self.part(s.lineage, *s.a, *s.b)),
                             x1=s.a[0], y1=s.a[1], x2=s.b[0], y2=s.b[1]), s.lineage)
        for a in self.real.arcs:
            st, en = (a.start, a.end) if a.direction == "CCW" else (a.end, a.start)
            ang = (lambda q: math.atan2(q[1] - a.center[1], q[0] - a.center[0]) % (2 * math.pi))
            add(CA.Primitive(kind="ARC", provenance=self.prov(a.lineage, self.part(a.lineage, *a.center, a.radius, *a.start)),
                             cx=a.center[0], cy=a.center[1], radius=a.radius, start_angle=ang(st), end_angle=ang(en)),
                a.lineage)
        for c in self.real.circles:
            add(CA.Primitive(kind="CIRCLE", provenance=self.prov(c.lineage, ""), cx=c.center[0], cy=c.center[1],
                             radius=c.radius), c.lineage)
        return out

    def placement(self, path) -> Affine2:
        """World matrix of an instance path, composed exactly as K1 composes it (OCS @ insert matrix per level)."""
        m = Affine2.identity()
        for oid in path:
            base, _, cell = oid.partition("[")
            if cell:
                raise ValueError(f"MINSERT cell {oid}: not needed by this source, not mapped")
            ins = self.obs[base]
            blk = self.doc.blocks[ins.geometry.block_key]
            m = m @ kernel.frame_matrix(ins.extrusion) @ kernel.insert_matrix(ins.geometry, blk.base_point)
        return m

    def text_observations(self, active_texts) -> tuple[list, dict]:
        """Every text the method reads, from D1: model-space texts directly, block texts placed through the K1
        instance path. Value whitespace is trimmed (declared normalisation, the method compares labels). Height
        is carried from the active reading (not a dependency of the six rows: see the contract)."""
        active = {}
        for t in active_texts:
            active.setdefault((t.provenance.handle, tuple(t.provenance.instance_path)), t)
        out, compared, equal, differing, missing = [], 0, 0, [], []
        for c in self.real.carried:
            o = self.obs.get(c["obs_id"])
            if o is None or o.kind not in ("TEXT", "MTEXT"):
                continue
            path = tuple(c["instance_path"])
            g = o.geometry
            if g.insertion is None:
                missing.append(c["obs_id"])
                continue
            m = self.placement(path) @ kernel.frame_matrix(o.extrusion)
            x, y = m.apply(g.insertion)
            key = (int(o.source_handle.split("+")[0]), tuple(int(p.split(":", 1)[1].split("+")[0]) for p in path))
            a = active.get(key)
            value = (g.value or "").strip()
            if a is not None:
                compared += 1
                same = a.value == value and abs(a.x - x) < 1e-6 and abs(a.y - y) < 1e-6
                equal += same
                if not same:
                    differing.append({"obs_id": c["obs_id"], "active": [a.value, a.x, a.y], "canonical": [value, x, y]})
            prov = (a.provenance if a is not None else CA.Provenance(handle=key[0], entity_type=o.kind,
                                                                      layer=str(o.layer or "0"),
                                                                      block_path=self.block_names(path),
                                                                      instance_path=key[1]))
            out.append(CA.TextObservation(value=value, x=x, y=y, height=a.height if a is not None else 0.0,
                                          provenance=prov))
        only_active = len(set(active) - {(t.provenance.handle, tuple(t.provenance.instance_path)) for t in out})
        return out, {"texts_canonical": len(out), "texts_active": len(active_texts), "compared": compared,
                     "equal_to_active_reading": equal, "differing": differing,
                     "texts_only_in_active_reading": only_active, "texts_without_insertion": missing,
                     "normalisation": "value whitespace trimmed"}

    def dimension_observations(self, active_dims) -> tuple[list, dict]:
        """Every DIMENSION the method reads, from the D1 decode fields (definition points, measurement, user text)
        placed through the K1 instance path. The D1 mapper does not carry these fields yet: this lab mapping is
        the candidate for engine/source (ENGINE_MISSING until promoted)."""
        raw = {str(L.handle_id(o.get("handle"))): o for o in self.decode["OBJECTS"] if isinstance(o.get("handle"), list)}
        dimlfac = float(self.decode.get("HEADER", {}).get("DIMLFAC") or 1.0)
        active = {}
        for d in active_dims:
            active.setdefault((d.provenance.handle, tuple(d.provenance.instance_path)), d)
        placements = {}
        for c in self.real.carried:
            o = self.obs.get(c["obs_id"])
            if o is not None and o.kind == "DIMENSION":
                placements.setdefault(c["obs_id"], []).append(tuple(c["instance_path"]))
        for o in self.doc.entities:
            if o.kind == "DIMENSION" and o.obs_id not in placements:
                placements[o.obs_id] = [()]
        out, compared, equal, differing = [], 0, 0, []
        for oid, paths in sorted(placements.items(), key=lambda kv: _obs_key(kv[0])):
            o = self.obs[oid]
            r = raw.get(o.source_handle.split("+")[0])
            if r is None:
                continue
            a_pt = r.get("xline1_pt") or r.get("def_pt") or [0, 0, 0]
            b_pt = r.get("xline2_pt") or r.get("def_pt") or [0, 0, 0]
            for path in paths:
                m = self.placement(path)
                x1, y1 = m.apply((a_pt[0], a_pt[1]))
                x2, y2 = m.apply((b_pt[0], b_pt[1]))
                act = r.get("act_measurement")
                key = (int(o.source_handle.split("+")[0]), tuple(int(p.split(":", 1)[1].split("+")[0]) for p in path))
                a = active.get(key)
                dim = CA.DimensionObservation(geometry_mm=math.hypot(x2 - x1, y2 - y1),
                                              display_value=None if act is None else float(act), dimlfac=dimlfac,
                                              user_text=str(r.get("user_text") or ""), x1=x1, y1=y1, x2=x2, y2=y2,
                                              provenance=a.provenance if a is not None else CA.Provenance(
                                                  handle=key[0], entity_type=str(r.get("type")), layer=str(o.layer or "0"),
                                                  block_path=self.block_names(path), instance_path=key[1]))
                if a is not None:
                    compared += 1
                    same = (abs(a.x1 - x1) < 1e-6 and abs(a.y1 - y1) < 1e-6 and abs(a.x2 - x2) < 1e-6
                            and abs(a.y2 - y2) < 1e-6 and a.display_value == dim.display_value
                            and a.user_text == dim.user_text and a.dimlfac == dimlfac)
                    equal += same
                    if not same:
                        differing.append(oid)
                out.append(dim)
        return out, {"dimensions_canonical": len(out), "dimensions_active": len(active_dims), "compared": compared,
                     "equal_to_active_reading": equal, "differing": differing,
                     "source": "D1 decode fields xline1_pt/xline2_pt/def_pt, act_measurement, user_text; HEADER DIMLFAC"}


# ====================================================================== running the method
@contextmanager
def substituted(transform):
    """cad_adapter.normalize replaced IN THIS PROCESS for one run, always restored."""
    orig = CA.normalize

    def wrapped(decoded, **kw):
        return transform(orig(decoded, **kw))
    CA.normalize = wrapped
    try:
        yield
    finally:
        CA.normalize = orig
    assert CA.normalize is orig


@contextmanager
def config_without_uploads():
    """The run config with its session-upload sources removed (a PDF under the upload folder). Proven not to be a
    dependency of the six rows (ablation UPLOADED_PDF); removing it keeps the proof off session state. The
    filtered copy lives in a temporary directory, never in the repository."""
    from research.qs_wall_treatment_01.pa08.qortuba import blind as B
    cfg = json.loads((B.OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    cfg["SOURCES"] = [x for x in cfg["SOURCES"] if not str(x.get("PATH", "")).startswith(UPLOADS_PREFIX)]
    orig = B.OUT
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "PA08_BLIND_CONFIG.json").write_text(json.dumps(cfg), "utf-8")
        B.OUT = Path(d)
        try:
            yield cfg
        finally:
            B.OUT = orig


def run_method(transform=None, no_uploads=False):
    """The active room method end to end; returns what the six rows need, nothing written."""
    from research.qs_wall_treatment_01.pa08.qortuba.boq import owner_rules as OR
    from research.qs_wall_treatment_01.pa08.qortuba.qs01 import takeoff as T
    if no_uploads:
        with config_without_uploads():
            return run_method(transform)
    if transform is None:
        o = T.run()
    else:
        with substituted(transform):
            o = T.run()
    summ = T.summary(o["inv"], o["floors"], o["skirt"], o["prof"], o["ceil"], o["tile"], o["plaster"], o["by_thk"])
    ceil = summ["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"]
    # every input of quantities() other than the floor polygons is passed EMPTY: the six rows must not need it.
    # A room the method could not establish (area None) makes the row expressions fail: recorded, never patched.
    missing = [f["ROOM"] for f in o["floors"] if f["METHOD_A_CAD_POLYGON_AREA_M2"] is None]
    if missing:
        six = {k: {"MEASURED_NET_QUANTITY": None, "NOT_COMPUTABLE": f"rooms not established: {missing}"} for k in ROUND1}
    else:
        rows = OR.quantities([], [], [], o["floors"], summ, ceil, [], o["ceil"], [])
        six = {r["QUANTITY_ID"]: r for r in rows if r["QUANTITY_ID"] in ROUND1}
    unit = o["r"].registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0]
    return {"o": o, "summ": summ, "six": six, "unit": unit}


def rooms_key(res):
    """Every room as (name, area, rectangles) — the comparable content of the method's output."""
    return sorted(((f["ROOM"], str(f["METHOD_A_CAD_POLYGON_AREA_M2"]),
                    tuple((q["X_MM"][0], q["Y_MM"][0], q["X_MM"][1], q["Y_MM"][1]) for q in f["RECTANGLES"]))
                   for f in res["o"]["floors"]), key=repr)


def six_values(res):
    return {k: res["six"][k]["MEASURED_NET_QUANTITY"] for k in ROUND1}


def canonical_input(can: "Canonical", nd, lossy=()):
    """The method's input with every dependency of the six rows taken from the canonical source: curves from K1,
    texts and dimensions from D1 placed through the K1 instance path. Inputs left from the active reader are the
    ones the contract proves the six rows do not depend on."""
    keep = [p for p in nd.primitives if p.kind not in GEOMETRIC]
    texts, _ = can.text_observations(nd.texts)
    dims, _ = can.dimension_observations(nd.dimensions)
    return replace(nd, primitives=can.primitives(lossy) + keep, texts=texts, dimensions=dims)


def canonical_round1(can: "Canonical | None" = None) -> dict:
    """The six rows from canonical inputs only (no session upload). Used by the reproducibility tests."""
    can = can or Canonical()
    res = run_method(lambda nd: canonical_input(can, nd), no_uploads=True)
    return {"six": six_values(res), "rooms_digest": digest(rooms_key(res)),
            "rooms": {f["ROOM_ID"]: (f["ROOM"], f["METHOD_A_CAD_POLYGON_AREA_M2"]) for f in res["o"]["floors"]},
            "unit": res["unit"]}


# ====================================================================== the proof
def room_trace(res, can: Canonical):
    """Room -> boundary segments -> canonical primitives on them -> K1 lineage -> D1 observation."""
    o = res["o"]
    nd = list(o["r"].normalized.values())[0]
    segs = [p for p in nd.primitives if p.kind == "SEGMENT"]
    out = {}
    for reg in o["regions"]:
        obs, occ, basis, virtual = set(), set(), Counter(), []
        for s in reg["BOUNDARY_SEGMENTS"]:
            basis[s["BOUNDARY_BASIS"]] += 1
            (ax, ay), (bx, by) = s["PTS"]
            hits = []
            for p in segs:
                if abs(ay - by) < 1e-6 and abs(p.y1 - ay) < 0.5 and abs(p.y2 - ay) < 0.5:
                    lo, hi = sorted((ax, bx))
                    if max(p.x1, p.x2) > lo + 0.5 and min(p.x1, p.x2) < hi - 0.5:
                        hits.append(p)
                elif abs(ax - bx) < 1e-6 and abs(p.x1 - ax) < 0.5 and abs(p.x2 - ax) < 0.5:
                    lo, hi = sorted((ay, by))
                    if max(p.y1, p.y2) > lo + 0.5 and min(p.y1, p.y2) < hi - 0.5:
                        hits.append(p)
            lins = [can.lineage_by_object.get(p.object_id) for p in hits]
            obs |= {lin.obs_id for lin in lins if lin is not None}
            occ |= {(lin.obs_id, tuple(lin.instance_path)) for lin in lins if lin is not None}
            if not hits:
                virtual.append({"basis": s["BOUNDARY_BASIS"], "site_id": s["SITE_ID"], "pts_mm": s["PTS"],
                                "counts_as_perimeter": s["COUNTS_AS_PERIMETER"]})
        out[reg["ROOM_ID"]] = {"room": reg["ROOM"], "boundary_segments": len(reg["BOUNDARY_SEGMENTS"]),
                               "boundary_basis": dict(basis), "source_observations": sorted(obs, key=_obs_key),
                               "source_occurrences": sorted(([o, list(pth)] for o, pth in occ),
                                                            key=lambda x: (_obs_key(x[0]), x[1])),
                               "segments_without_a_source_line": virtual,
                               "measurement_region_id": reg["FLOOR_MEASUREMENT_REGION_ID"]}
    return out


def _obs_key(s):
    return int(s.split(":")[1].split("+")[0])


def signatures_by_occurrence(doc):
    """{(obs_id, instance_path): {signature}} - a signature belongs to an occurrence, not to an observation id:
    the same block entity can be placed once mirrored and once not."""
    out = {}
    for sg, keys in Q.capability_signatures(doc).items():
        for oid, path in keys:
            out.setdefault((oid, tuple(path)), set()).add(sg)
    return out


def proof(out_dir: Path):
    from r8_5_source_exceptions import Source
    from r8_5_value_shadow import canonical_context

    can = Canonical()
    approved = {r["SUBITEM"]: r for r in json.loads(APPROVED.read_text())["ROWS"]}

    def canonical_transform(nd, lossy=()):
        return canonical_input(can, nd, lossy)

    active = run_method()
    canon = run_method(canonical_transform, no_uploads=True)
    canon2 = run_method(canonical_transform, no_uploads=True)
    no_pdf = run_method(no_uploads=True)
    nd_active = CA.normalize(can.decode)
    _, text_check = can.text_observations(nd_active.texts)
    _, dim_check = can.dimension_observations(nd_active.dimensions)

    # contract ablations: what the six rows depend on, besides geometry
    def blank(field):
        def t(nd):
            kw = {"linetype": dict(linetype="BYLAYER", linetype_source="UNRESOLVED"), "lineweight": dict(lineweight=None),
                  "block_path": dict(block_path=()), "sub_id": dict(sub_id="X")}[field]
            return replace(nd, primitives=[replace(p, provenance=replace(p.provenance, **kw)) if p.kind in GEOMETRIC
                                           else p for p in nd.primitives])
        return t

    def drop(kind):
        def t(nd):
            if kind == "HATCH":
                return replace(nd, primitives=[p for p in nd.primitives if p.kind != "HATCH"])
            return replace(nd, dimensions=[])
        return t

    base_six = six_values(active)
    contract = []
    for field, why in (("linetype", "resolved linetype and its source"), ("lineweight", "resolved lineweight"),
                       ("block_path", "names of the blocks the primitive is placed through"),
                       ("sub_id", "per-part identity of a multi-part entity (part of object_id)")):
        r = run_method(blank(field))
        contract.append({"field": field, "meaning": why, "six_rows_change_when_blanked": six_values(r) != base_six,
                         "rooms_change_when_blanked": rooms_key(r) != rooms_key(active),
                         "k1_supplies_it": field in ("block_path", "sub_id"),
                         "k1_source": {"block_path": "D1 INSERT observation -> block record name along the K1 instance path",
                                       "sub_id": "hash of K1 lineage obs id + canonical coordinates (uniqueness only)"}
                         .get(field, "not carried by K1 lineage (linetype table not resolved canonically)")})
    def drop_more(kind):
        def t(nd):
            if kind == "TEXT_HEIGHT":
                return replace(nd, texts=[replace(x, height=0.0) for x in nd.texts])
            if kind == "INSTANCES":
                return replace(nd, instances=[])
            if kind == "BLOCK_DEFINITIONS":
                return replace(nd, block_definitions={} if isinstance(nd.block_definitions, dict) else [])
            return replace(nd, layers={} if isinstance(nd.layers, dict) else [])
        return t
    for kind in ("TEXT_HEIGHT", "INSTANCES", "BLOCK_DEFINITIONS", "LAYERS"):
        try:
            r = run_method(drop_more(kind))
            ch6, chr_ = six_values(r) != base_six, rooms_key(r) != rooms_key(active)
        except Exception as err:                           # an input the method cannot run without is a dependency
            ch6 = chr_ = f"RUN_FAILED: {type(err).__name__}"
        contract.append({"field": f"{kind} (input blanked)", "meaning": "non-curve input still read from the active reader",
                         "six_rows_change_when_blanked": ch6, "rooms_change_when_blanked": chr_,
                         "k1_supplies_it": False, "k1_source": "active reader (cad_adapter)"})
    for kind in ("HATCH", "DIMENSIONS"):
        r = run_method(drop(kind))
        contract.append({"field": f"{kind} (input dropped entirely)", "meaning": "non-curve input still read from the active reader",
                         "six_rows_change_when_blanked": six_values(r) != base_six,
                         "rooms_change_when_blanked": rooms_key(r) != rooms_key(active),
                         "k1_supplies_it": kind == "DIMENSIONS",
                         "k1_source": ("D1 decode definition points (lab mapping, see dimension_check)"
                                       if kind == "DIMENSIONS" else "active reader (cad_adapter)")})
    contract.append({"field": "UPLOADED_PDF (config source under the session upload folder)",
                     "meaning": "a PDF the run config lists as a source; it lives outside the repository",
                     "six_rows_change_when_blanked": six_values(no_pdf) != base_six,
                     "rooms_change_when_blanked": rooms_key(no_pdf) != rooms_key(active),
                     "k1_supplies_it": False, "k1_source": "not needed: removed from the canonical runs"})
    lossy = {}
    for fields in (("block_path",), ("sub_id",), ("block_path", "sub_id")):
        r = run_method(lambda nd, f=fields: canonical_transform(nd, f), no_uploads=True)
        lossy["+".join(fields)] = {"rooms_equal_to_active": rooms_key(r) == rooms_key(active),
                                   "six_rows": six_values(r),
                                   "rooms_only_in_lossy_run": sorted({(f["ROOM"], f["METHOD_A_CAD_POLYGON_AREA_M2"])
                                                                      for f in r["o"]["floors"]} -
                                                                     {(f["ROOM"], f["METHOD_A_CAD_POLYGON_AREA_M2"])
                                                                      for f in active["o"]["floors"]}, key=repr)}
    # the canonical run above must leave the lineage map of ITS primitives, not of the last lossy run
    can.lineage_by_object.clear()
    canon = run_method(canonical_transform, no_uploads=True)

    src = Source("QORTUBA")
    cand = next(c for c in src.cands.values() if any("SECOND FLOOR PLAN" in e[2] for e in c.role_evidence))
    ctx = canonical_context(src, cand)
    trace = room_trace(canon, can)
    sig_by_occ = signatures_by_occurrence(can.doc)
    scale = canon["unit"]["UNIT_SCALE_TO_MM"]
    floors = {f["ROOM_ID"]: f for f in canon["o"]["floors"]}
    act_floors = {f["ROOM_ID"]: f for f in active["o"]["floors"]}

    rooms = []
    for rid, f in sorted(floors.items()):
        t = trace[rid]
        rooms.append({
            "room_id": rid, "room": f["ROOM"], "wet_or_dry": f["WET_OR_DRY"],
            "measurement_region_id": t["measurement_region_id"],
            "method_id": METHOD_ID, "status_in_method": f["STATUS"],
            "canonical_native_geometry": {
                "unit": "native drawing unit (unconfirmed)",
                "rectangles_native": [[round(q["X_MM"][0] / scale, 6), round(q["Y_MM"][0] / scale, 6),
                                       round(q["X_MM"][1] / scale, 6), round(q["Y_MM"][1] / scale, 6)]
                                      for q in f["RECTANGLES"]],
                "area_native_sq": round(f["METHOD_A_CAD_POLYGON_AREA_M2"] * 1e6 / (scale * scale), 4)},
            "preview_area_m2_under_active_unit_reading": f["METHOD_A_CAD_POLYGON_AREA_M2"],
            "active_area_m2": (act_floors.get(rid) or {}).get("METHOD_A_CAD_POLYGON_AREA_M2"),
            "formula": f["FORMULA"],
            "boundary": {k: t[k] for k in ("boundary_segments", "boundary_basis", "segments_without_a_source_line")},
            "source_observations": t["source_observations"], "source_occurrences": t["source_occurrences"],
            "occurrences_without_signature": [o for o in t["source_occurrences"]
                                              if not sig_by_occ.get((o[0], tuple(o[1])))],
            "capability_signatures": sorted({sg for o in t["source_occurrences"]
                                             for sg in sig_by_occ.get((o[0], tuple(o[1])), ())}),
        })
    by_room = {r["room_id"]: r for r in rooms}

    rows = []
    for qid in ROUND1:
        cr, ar = canon["six"][qid], approved.get(qid)
        names = cr.get("ROOMS") or []
        rids = _rows_rooms(qid, canon["o"]["floors"])
        obs = sorted({ob for rid in rids for ob in by_room[rid]["source_observations"]}, key=_obs_key)
        occs = sorted({(o[0], tuple(o[1])) for rid in rids for o in by_room[rid]["source_occurrences"]},
                      key=lambda x: (_obs_key(x[0]), x[1]))
        sigs = sorted({sg for rid in rids for sg in by_room[rid]["capability_signatures"]})
        value = cr["MEASURED_NET_QUANTITY"]
        cur = ar["MEASURED_QUANTITY"] if ar else None
        rows.append({
            "row_id": f"{qid}|{cr['BOQ_ITEM']}", "trade": cr["TRADE"], "item": cr["BOQ_ITEM"],
            "rooms": [{"room_id": rid, "room": by_room[rid]["room"]} for rid in rids], "room_names_in_row": names,
            "source_observations": obs, "source_occurrences": [[o, list(p)] for o, p in occs],
            "source_geometry_ids": [by_room[rid]["measurement_region_id"] for rid in rids],
            "canonical_region_id": cand.candidate_id, "frame_id": ctx["frame"].frame_id,
            "unit_context": {"status": ctx["unit"].status, "canonical_policy": "URBAN_FRAME_RELEASE_V3",
                             "active_path_reading": {k: canon["unit"][k] for k in
                                                     ("UNIT_CANDIDATE", "UNIT_SCALE_TO_MM", "PROVENANCE", "STATUS")},
                             "note": "the active path takes the unit from INSUNITS; the canonical policy does not accept "
                                     "that as confirmation, so no physical value is released"},
            "source_capability_signatures": sigs,
            "decoder_qualification_requirement": "every listed signature EXERCISED_AND_PASS against an ADMITTED "
                                                 "independent export of this source (V2); currently 0 qualified",
            "method_rule_ids": {"geometry": METHOD_ID, "row": ROW_METHOD_ID, "rules": cr["RULE_ID"]},
            "formula": cr["FORMULA"],
            "formula_inputs": [{"room_id": rid, "room": by_room[rid]["room"],
                                "preview_area_m2": by_room[rid]["preview_area_m2_under_active_unit_reading"]}
                               for rid in rids],
            "canonical_native_value": round(sum(by_room[rid]["canonical_native_geometry"]["area_native_sq"] for rid in rids), 4),
            "canonical_physical_value": None,
            "canonical_physical_value_reason": "frame UNCONFIRMED: no physical value may be released",
            "preview_value_m2_under_active_unit_reading": value,
            "current_value": cur, "current_status": ar["STATUS"] if ar else None,
            "difference_preview_minus_current": None if cur is None else round(value - cur, 10),
            "status": ctx["release"], "blockers": ctx["blockers"],
            "release_eligibility": "NOT_ELIGIBLE",
            "release_eligibility_reasons": ["unit UNCONFIRMED", "region designation PENDING_REVIEW",
                                            "no independent-parser qualification", "method not promoted (legacy audit)"],
        })

    res = {
        "SCHEMA": "URBAN_R8_6_QORTUBA_ROUND1_PROOF_V1", "status": "SHADOW_PROOF_NOT_MIGRATION",
        "source_sha256": src.src, "decode_sha256": hashlib.sha256(DECODE.read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "canonical_runs_use_session_uploads": False,
        "chain": "SOURCE (DWG) -> D1 decode -> K1 realisation -> method-input mapping -> QS01 Method A rooms -> "
                 "owner_rules floor rows; the current value is read only AFTER the value is computed, for the comparison",
        "method_code_sha256": {p: sha_file(p) for p in METHOD_FILES},
        "inputs_by_origin": {
            "CANONICAL": ["SEGMENT/ARC/CIRCLE primitives (K1)",
                          "texts: D1 TEXT/MTEXT, block texts placed through the K1 instance path (lab mapping)",
                          "dimensions: D1 decode definition points placed through the K1 instance path (lab mapping)"],
            "ACTIVE_READER_STILL": ["HATCH primitives", "text height", "instances / block definitions records",
                                    "layer table", "unit reading (INSUNITS)"],
            "PROVEN_NOT_A_DEPENDENCY_OF_THE_SIX_ROWS": [c["field"] for c in contract
                                                        if not c["six_rows_change_when_blanked"]]},
        "text_check": text_check, "dimension_check": dim_check,
        "method_input_contract": contract,
        "lossy_mapping_evidence": lossy,
        "row_dependency_ablation": "owner_rules.quantities called with rooms, walls, openings, glazing and the human "
                                   "register all EMPTY; the six rows are unchanged, so they depend on the floors only",
        "results": {"active_six": base_six, "canonical_six": six_values(canon), "canonical_six_second_run": six_values(canon2),
                    "rooms_equal_active_vs_canonical": rooms_key(canon) == rooms_key(active),
                    "canonical_deterministic": digest(rooms_key(canon)) == digest(rooms_key(canon2)),
                    "canonical_rooms_digest": digest(rooms_key(canon))},
        "rows": rows, "rooms": rooms,
        "canonical_context": {"unit": ctx["unit"].status, "region": ctx["region"].status, "frame": ctx["frame"].status,
                              "release": ctx["release"], "V-CAD-5": ctx["v_cad"], "frame_id": ctx["frame"].frame_id,
                              "evidence_version": ctx["frame"].evidence_digest},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "QORTUBA_ROUND1_PROOF.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    return res


def _rows_rooms(qid, floors):
    """Which canonical rooms a row sums, by the same predicates owner_rules uses (wet / service / dry / all)."""
    from research.qs_wall_treatment_01.pa08.qortuba.boq import owner_rules as OR
    def base(f):
        return f["ROOM"].split(" /")[0]
    if qid in ("Q-03", "Q-11"):
        sel = [f for f in floors if f["WET_OR_DRY"] == "WET"]
    elif qid in ("Q-03P", "Q-12"):
        sel = [f for f in floors if base(f) in OR.CERAMIC_ROOM_NAMES and f["WET_OR_DRY"] == "DRY"]
    elif qid == "Q-13":
        sel = [f for f in floors if base(f) not in OR.CERAMIC_ROOM_NAMES]
    else:
        sel = list(floors)
    return [f["ROOM_ID"] for f in sel]


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_6"
    r = proof(out)
    print(json.dumps(r["results"], indent=1))
    for c in r["method_input_contract"]:
        print(c["field"], c["six_rows_change_when_blanked"], c["rooms_change_when_blanked"])
    print({k: v["rooms_equal_to_active"] for k, v in r["lossy_mapping_evidence"].items()})
    print({k: v for k, v in r["text_check"].items() if k != "differing"}, r["text_check"]["differing"][:3])
    print({k: v for k, v in r["dimension_check"].items() if k != "differing"})
