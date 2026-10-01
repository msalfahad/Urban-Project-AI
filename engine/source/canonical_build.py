"""Builders of CANONICAL_MEASUREMENT_INPUT (R8.7) from a realised route, and region clipping.

Two routes, one output shape:
    K1: a pinned decode -> SourceDocument -> kernel.realise; texts / dimensions placed through the K1 instance path
        with the kernel's own matrices (frame @ insert, per level).
    K2: a DXF read by ezdxf -> kernel_ezdxf.realise; texts / dimensions placed through ezdxf's insert matrices.
        The ezdxf document is used by duck typing; this module imports no third-party library.

Identity is source-derived (see canonical_input). Nothing is matched by coordinates; a record that cannot be
placed keeps its identity with world_placement None, so a method that needs it fails closed.

R8.8
    * part identity: part_index is the SOURCE sub-part (Lineage.sub_part), never an output ordinal;
    * visibility AUTHORITY for parts, texts and dimensions alike (VisibilityAuthority): the entity flag (applied by
      the kernel), the layer state (frozen / off, read from the source layer table), frozen ancestor insert layers,
      ByLayer inheritance of layer-0 children, and unresolved dynamic-block occurrences. Nothing is VISIBLE by
      default: a record whose layer state was not read is VISIBILITY_UNRESOLVED;
    * region membership is EXACT (region_membership): no sampling of curves.
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
from collections import Counter

from . import canonical_input as CI
from . import findings as F
from . import region_membership as RM
from .cad import kernel
from .cad.affine import Affine2

# DIMENSION subtype (DXF group 70 & 7) -> the source object type code a DWG reader reports
DIMTYPE_CODE = {0: "21", 1: "22", 2: "24", 3: "26", 4: "25", 5: "23", 6: "20"}
PART_KINDS = {"segments": "SEGMENT", "arcs": "ARC", "circles": "CIRCLE", "elliptical_arcs": "ELLIPTICAL_ARC"}


def _handle(obs_id: str) -> str:
    """'D1:156' -> '156'; 'D2:156[0,1]' -> '156[0,1]' (a MINSERT cell is its own occurrence)."""
    return obs_id.split(":", 1)[1]


def _base(obs_id: str) -> str:
    return _handle(obs_id).split("[")[0].split("+")[0]


def _geometry(kind, g):
    if kind == "SEGMENT":
        return (g.a[0], g.a[1], g.b[0], g.b[1])
    if kind == "ARC":
        st, en = (g.start, g.end) if g.direction == "CCW" else (g.end, g.start)
        ang = (lambda q: math.atan2(q[1] - g.center[1], q[0] - g.center[0]) % (2 * math.pi))
        return (g.center[0], g.center[1], g.radius, ang(st), ang(en))
    if kind == "CIRCLE":
        return (g.center[0], g.center[1], g.radius)
    return (g.center[0], g.center[1], g.axis_u[0], g.axis_u[1], g.axis_v[0], g.axis_v[1], g.t0, g.t1)


def effective_layer(layer, path, insert_layer):
    """(effective layer, authority, chain) by AutoCAD layer-0 semantics, innermost insert first. `insert_layer`
    gives an INSERT occurrence's own layer (None when unknown). Only the inserts actually needed are consulted."""
    if layer is None:
        return None, CI.EFFECTIVE_UNRESOLVED, ()
    if layer != "0" or not path:
        return layer, CI.EFFECTIVE_SOURCE_LAYER, ()
    eff, chain = layer, []
    for p in reversed(tuple(path)):
        if eff != "0":
            break
        own = insert_layer(p) if insert_layer is not None else None
        chain.append(p)
        if own is None:
            return None, CI.EFFECTIVE_UNRESOLVED, tuple(chain)
        eff = own
    return eff, CI.EFFECTIVE_BYLAYER_INSERT_CHAIN, tuple(chain)


def _eff_kw(layer, path, insert_layer) -> dict:
    eff, auth, _ = effective_layer(layer, path, insert_layer)
    return {"effective_layer": eff, "effective_layer_authority": auth}


def parts_from_realised(revision_id: str, realised, steps, visibility=None) -> tuple:
    """CanonicalPart per realised curve. part_index = the SOURCE sub-part the curve realises (Lineage.sub_part:
    0 for a single-curve entity, the span index for a polyline span), read from source structure by the route -
    never an ordinal counted over the realised output, so emission order cannot change an identity (R8.8). A route
    that cannot name the sub-part leaves it None and the identity key is None (a method requiring it fails closed).
    `steps(path)` gives the LineageStep per path level; `visibility(layer, path)` the visibility authority."""
    out = []
    for attr, kind in PART_KINDS.items():
        for g in getattr(realised, attr):
            lin = g.lineage
            path = tuple(lin.instance_path)
            vis = visibility(lin.layer, path) if visibility is not None else CI.VISIBILITY_UNRESOLVED
            ident = CI.SourceIdentity(revision_id, _base(lin.obs_id) if lin.obs_id else None,
                                      tuple(_handle(p) for p in path), kind, getattr(lin, "sub_part", None))
            eff, auth, _ = effective_layer(lin.layer, path, getattr(visibility, "insert_layer", None))
            out.append(CI.CanonicalPart(ident, kind, _geometry(kind, g), lin.layer, vis, steps(path), lin.obs_id,
                                        lin.kind, effective_layer=eff, effective_layer_authority=auth))
    return tuple(out)


def unresolved_dynamic_occurrences(realised) -> frozenset:
    return frozenset(f.instance_path[-1] for f in realised.findings
                     if f.code == F.DYNAMIC_BLOCK_UNRESOLVED and f.instance_path)


class VisibilityAuthority:
    """Visibility of one record from source facts only.

    layer_states  {layer name: {"frozen": bool, "off": bool}} read from the source layer table, or None when the
                  route did not read it (then nothing can be VISIBLE: VISIBILITY_UNRESOLVED).
    insert_layer  callable(path entry) -> the INSERT occurrence's own layer (None when unknown).
    unresolved    instance-path entries of dynamic-block occurrences whose visibility state was not read.

    Rules (AutoCAD display semantics): a frozen layer hides its entities and, on an INSERT, the whole occurrence;
    an OFF layer hides its own entities only; an entity on layer "0" inside a block takes the layer of the insert
    that places it (ByLayer). Entity invisibility flags are applied earlier by the kernels (hidden records)."""

    def __init__(self, layer_states, insert_layer, unresolved=frozenset()):
        self.states, self.insert_layer, self.unresolved = layer_states, insert_layer, frozenset(unresolved)

    def _state(self, layer):
        if self.states is None or layer is None:
            return None
        return self.states.get(layer)

    def __call__(self, layer, path) -> str:
        if any(p in self.unresolved for p in path):
            return CI.VISIBILITY_UNRESOLVED
        if self.states is None:
            return CI.VISIBILITY_UNRESOLVED
        eff_parent = None
        for p in path:                                   # outermost first: effective layer of each insert
            own = self.insert_layer(p)
            eff = eff_parent if (own == "0" and eff_parent is not None) else own
            st = self._state(eff)
            if st is None:
                return CI.VISIBILITY_UNRESOLVED
            if st.get("frozen"):
                return CI.HIDDEN_SOURCE
            eff_parent = eff
        eff = effective_layer(layer, path, self.insert_layer)[0] if path else layer
        st = self._state(eff)
        if st is None:
            return CI.VISIBILITY_UNRESOLVED
        if st.get("frozen") or st.get("off"):
            return CI.HIDDEN_SOURCE
        return CI.VISIBLE


def k1_layer_states(decode: dict):
    """{layer: {frozen, off}} from a pinned LibreDWG decode. LibreDWG's own LAYER spec (dwg.spec, R2000+):
    frozen = flag0 & 1, on = !(flag0 & 2). None when the decode has no LAYER record with a flag0."""
    out = {}
    for o in decode.get("OBJECTS", []):
        if o.get("object") == "LAYER" and o.get("name") is not None:
            f = o.get("flag0")
            if not isinstance(f, int):
                return None
            out[o["name"]] = {"frozen": bool(f & 1), "off": bool(f & 2)}
    return out or None


def k2_layer_states(ezdoc):
    try:
        return {ly.dxf.name: {"frozen": bool(ly.is_frozen()), "off": bool(ly.is_off())} for ly in ezdoc.layers} or None
    except Exception:                                    # noqa: BLE001 - an unreadable table is "not read"
        return None


# ---------------------------------------------------------------- K1
class K1:
    def __init__(self, revision_id, decode: dict, document, realised):
        self.rev, self.decode, self.doc, self.real = revision_id, decode, document, realised
        self.obs = {o.obs_id: o for o in document.entities}
        for b in document.blocks.values():
            for o in b.entities:
                self.obs[o.obs_id] = o
        from .cad import libredwg_map as L
        self.raw = {str(L.handle_id(o.get("handle"))): o for o in decode.get("OBJECTS", [])
                    if isinstance(o.get("handle"), list)}
        self.dimlfac = float(decode.get("HEADER", {}).get("DIMLFAC") or 1.0)
        self.layer_states = k1_layer_states(decode)
        self.vis = VisibilityAuthority(self.layer_states, self._insert_layer, unresolved_dynamic_occurrences(realised))

    def _insert_layer(self, path_entry):
        o = self.obs.get(path_entry.split("[")[0])
        return o.layer if o is not None else None

    def steps(self, path) -> tuple:
        out = []
        for oid in path:
            o = self.obs.get(oid.split("[")[0])
            key = getattr(getattr(o, "geometry", None), "block_key", None)
            blk = self.doc.blocks.get(key) if key else None
            out.append(CI.LineageStep(_handle(oid), (key[1:] if key and key.startswith("H") else key) if blk else None,
                                      blk.name if blk is not None else None))
        return tuple(out)

    def placement(self, path):
        m = Affine2.identity()
        for oid in path:
            base, _, cell = oid.partition("[")
            if cell:
                return None                          # MINSERT cell placement not mapped: unplaced, not guessed
            ins = self.obs.get(base)
            blk = self.doc.blocks.get(ins.geometry.block_key) if ins is not None else None
            if blk is None:
                return None
            m = m @ kernel.frame_matrix(ins.extrusion) @ kernel.insert_matrix(ins.geometry, blk.base_point)
        return m

    def parts(self):
        return parts_from_realised(self.rev, self.real, self.steps, self.vis)

    def _carried_and_hidden(self, kinds):
        """(entry, visibility) for every carried record of these kinds, and every entity-flag-hidden one
        (HIDDEN_SOURCE: listed so a consumer can see it exists and must not use it)."""
        for c in self.real.carried:
            if c["kind"] in kinds:
                o = self.obs.get(c["obs_id"])
                yield c, o, self.vis(o.layer if o is not None else None, tuple(c["instance_path"]))
        for h in self.real.hidden:
            if h["kind"] in kinds:
                yield h, self.obs.get(h["obs_id"]), CI.HIDDEN_SOURCE

    def texts(self):
        out = []
        for c, o, vis in self._carried_and_hidden(("TEXT", "MTEXT")):
            if o is None:
                continue
            path = tuple(c["instance_path"])
            m = self.placement(path)
            ins = getattr(o.geometry, "insertion", None)
            if m is None or ins is None:
                x = y = None
            else:
                x, y = (m @ kernel.frame_matrix(o.extrusion)).apply(ins)
            raw = self.raw.get(_base(o.obs_id), {})
            h = raw.get("height")
            eff, auth, _ = effective_layer(o.layer, path, self.vis.insert_layer)
            out.append(CI.PlacedText(CI.SourceIdentity(self.rev, _base(o.obs_id), tuple(_handle(p) for p in path), o.kind, 0),
                                     (o.geometry.value or "").strip() if getattr(o.geometry, "value", None) is not None else None,
                                     x, y, None if h is None else float(h), o.layer, vis, self.steps(path), o.kind,
                                     effective_layer=eff, effective_layer_authority=auth))
        return tuple(out)

    def dimensions(self):
        placements = {}
        for c, o, vis in self._carried_and_hidden(("DIMENSION",)):
            if o is not None:
                placements.setdefault(c["obs_id"], []).append((tuple(c["instance_path"]), vis))
        for o in self.doc.entities:
            if o.kind == "DIMENSION" and o.obs_id not in placements:
                placements[o.obs_id] = [((), self.vis(o.layer, ()))]
        out = []
        for oid, paths in sorted(placements.items(), key=lambda kv: int(_base(kv[0]))):
            o = self.obs[oid]
            r = self.raw.get(_base(oid))
            for path, vis in paths:
                ident = CI.SourceIdentity(self.rev, _base(oid), tuple(_handle(p) for p in path), "DIMENSION", 0)
                if r is None:
                    out.append(CI.PlacedDimension(ident, None, None, None, None, self.dimlfac, None, o.layer,
                                                  vis, self.steps(path), **_eff_kw(o.layer, path, self.vis.insert_layer)))
                    continue
                a = r.get("xline1_pt") or r.get("def_pt")
                b = r.get("xline2_pt") or r.get("def_pt")
                m = self.placement(path)
                placed = None if (m is None or a is None or b is None) else (m.apply((a[0], a[1])), m.apply((b[0], b[1])))
                act = r.get("act_measurement")
                out.append(CI.PlacedDimension(ident, None if a is None or b is None else ((a[0], a[1]), (b[0], b[1])),
                                              placed, None if act is None else float(act), str(r.get("user_text") or ""),
                                              self.dimlfac, None if r.get("type") is None else str(r.get("type")),
                                              o.layer, vis, self.steps(path),
                                              **_eff_kw(o.layer, path, self.vis.insert_layer)))
        return tuple(out)


# ---------------------------------------------------------------- K2 (ezdxf document by duck typing)
class K2:
    def __init__(self, revision_id, ezdoc, realised):
        self.rev, self.doc, self.real = revision_id, ezdoc, realised
        self.dimlfac = float(ezdoc.header.get("$DIMLFAC", 1.0) or 1.0)
        self._steps = {}
        self.layer_states = k2_layer_states(ezdoc)
        self.vis = VisibilityAuthority(self.layer_states, self._insert_layer, unresolved_dynamic_occurrences(realised))

    def entity(self, obs_id):
        return self.doc.entitydb.get(format(int(_base(obs_id)), "X"))

    def _insert_layer(self, path_entry):
        e = self.entity(path_entry)
        return e.dxf.get("layer", None) if e is not None else None

    def steps(self, path) -> tuple:
        if path not in self._steps:
            out = []
            for oid in path:
                ins = self.entity(oid)
                blk = self.doc.blocks.get(ins.dxf.name) if ins is not None else None
                rec = str(int(blk.block_record.dxf.handle, 16)) if blk is not None else None
                out.append(CI.LineageStep(_handle(oid), rec, ins.dxf.name if ins is not None else None))
            self._steps[path] = tuple(out)
        return self._steps[path]

    def apply(self, path, p):
        """Block-local point -> world through the insert matrices (innermost first). None when unplaceable."""
        mats = []
        for oid in path:
            if "[" in oid:
                return None
            ins = self.entity(oid)
            if ins is None:
                return None
            mats.append(ins.matrix44())
        v = p
        for m in reversed(mats):
            v = m.transform(v)
        return (float(v[0]), float(v[1]))

    def parts(self):
        return parts_from_realised(self.rev, self.real, self.steps, self.vis)

    def _carried_and_hidden(self, kinds):
        for c in self.real.carried:
            if c["kind"] in kinds:
                e = self.entity(c["obs_id"])
                yield c, e, self.vis(e.dxf.get("layer", None) if e is not None else None, tuple(c["instance_path"]))
        for h in self.real.hidden:
            if h["kind"] in kinds or (h["kind"] == "MTEXT" and "MTEXT" in kinds):
                yield h, self.entity(h["obs_id"]), CI.HIDDEN_SOURCE

    def texts(self):
        out = []
        for c, e, vis in self._carried_and_hidden(("TEXT", "MTEXT")):
            path = tuple(c["instance_path"])
            if e is None:
                continue
            t = e.dxftype()
            if t == "TEXT":
                local, value, h = e.ocs().to_wcs(e.dxf.insert), e.dxf.get("text", None), e.dxf.get("height", None)
            else:
                local, value, h = e.dxf.insert, e.text, e.dxf.get("char_height", None)
            p = self.apply(path, (local[0], local[1], local[2] if len(local) > 2 else 0.0))
            out.append(CI.PlacedText(CI.SourceIdentity(self.rev, _base(c["obs_id"]), tuple(_handle(q) for q in path), t, 0),
                                     None if value is None else value.strip(), None if p is None else p[0],
                                     None if p is None else p[1], None if h is None else float(h),
                                     e.dxf.get("layer", None), vis, self.steps(path), t,
                                     **_eff_kw(e.dxf.get("layer", None), path, self.vis.insert_layer)))
        return tuple(out)

    def dimensions(self):
        out = []
        for c, e, vis in self._carried_and_hidden(("DIMENSION",)):
            if e is None:
                continue
            path = tuple(c["instance_path"])
            ident = CI.SourceIdentity(self.rev, _base(c["obs_id"]), tuple(_handle(q) for q in path), "DIMENSION", 0)
            g = e.dxf
            a = g.get("defpoint2", None) if g.hasattr("defpoint2") else g.get("defpoint", None)
            b = g.get("defpoint3", None) if g.hasattr("defpoint3") else g.get("defpoint", None)
            pa = None if a is None else self.apply(path, (a[0], a[1], 0.0))
            pb = None if b is None else self.apply(path, (b[0], b[1], 0.0))
            act = g.get("actual_measurement", None) if g.hasattr("actual_measurement") else None
            code = DIMTYPE_CODE.get(int(g.get("dimtype", 0)) & 7) if e.dxftype() == "DIMENSION" else None
            out.append(CI.PlacedDimension(ident, None if a is None or b is None else ((a[0], a[1]), (b[0], b[1])),
                                          None if pa is None or pb is None else (pa, pb),
                                          None if act is None else float(act), str(g.get("text", "") or ""),
                                          self.dimlfac, code, g.get("layer", None), vis, self.steps(path),
                                          g.get("dimstyle", None),
                                          **_eff_kw(g.get("layer", None), path, self.vis.insert_layer)))
        return tuple(out)


# ---------------------------------------------------------------- input assembly and region clipping
def _points(rec):
    """The finite point set of a text / dimension record (None when unplaced)."""
    if isinstance(rec, CI.PlacedText):
        return None if rec.x is None or rec.y is None else [(rec.x, rec.y)]
    return None if rec.placed_points is None else list(rec.placed_points)


MEMBERSHIP = {RM.FULLY_INSIDE: CI.IN_REGION, RM.FULLY_OUTSIDE: CI.OUTSIDE_REGION,
              RM.CROSSES_BOUNDARY: CI.REVIEW_REQUIRED, RM.UNRESOLVED: CI.REVIEW_REQUIRED}


def exact_state(rec, bounds, eps: float = 0.0) -> str:
    """FULLY_INSIDE / FULLY_OUTSIDE / CROSSES_BOUNDARY / UNRESOLVED, exactly (region_membership; no sampling)."""
    if isinstance(rec, CI.CanonicalPart):
        return RM.classify(rec.kind, rec.geometry, bounds, eps)
    pts = _points(rec)
    return RM.classify_points(pts, bounds, eps) if pts else RM.UNRESOLVED


def membership(rec, bounds, eps: float = 0.0) -> str:
    return MEMBERSHIP[exact_state(rec, bounds, eps)]


def occurrence(rec) -> str:
    """The top-level occurrence a record belongs to: its outermost insert, or the entity itself."""
    path = rec.identity.instance_handles
    return ("I" + path[0]) if path else ("E" + str(rec.identity.source_handle))


def assemble(revision: CI.SourceRevision, region_id: str, bounds, frame_id, unit_native_to_mm, unit_claim_id,
             parts, texts, dimensions, notes=None, eps: float = 0.0) -> CI.CanonicalMeasurementInput:
    """Keep the records inside the selected region. Membership is judged per top-level OCCURRENCE: a block
    occurrence partly inside and partly outside is never cut in two - every one of its records is listed
    REVIEW_REQUIRED (an occurrence cut by the region boundary changed a room decomposition silently, R8.7).
    Unplaceable records are REVIEW_REQUIRED too; outside records are counted."""
    recs = [("parts", r) for r in parts] + [("texts", r) for r in texts] + [("dimensions", r) for r in dimensions]
    member = {id(r): membership(r, bounds, eps) for _, r in recs}
    by_occ = {}
    for _, r in recs:
        by_occ.setdefault(occurrence(r), set()).add(member[id(r)])
    kept, review, outside = {"parts": [], "texts": [], "dimensions": []}, {}, Counter()
    for name, r in recs:
        states = by_occ[occurrence(r)]
        m = member[id(r)]
        if m == CI.REVIEW_REQUIRED:
            review[f"{name}:{r.identity.key}"] = ("crosses the region boundary (exact test) or has no placement: "
                                                  + exact_state(r, bounds, eps))
        elif len(states) > 1 and occurrence(r).startswith("I"):
            review[f"{name}:{r.identity.key}"] = f"occurrence {occurrence(r)[1:]} is partly inside the region"
        elif m == CI.IN_REGION:
            kept[name].append(r)
        else:
            outside[name] += 1
    n = dict(notes or {})
    n["outside_region"] = dict(outside)
    n["region_membership_policy"] = RM.POLICY["id"]
    return CI.CanonicalMeasurementInput(revision, region_id, frame_id, unit_native_to_mm, unit_claim_id,
                                        tuple(kept["parts"]), tuple(kept["texts"]), tuple(kept["dimensions"]),
                                        review, n)


def occurrence_extent(parts, insert_handle: str):
    """EXACT bounds of every part placed through one top-level insert occurrence (e.g. a sheet frame)."""
    boxes = [RM.exact_bbox(p.kind, p.geometry) for p in parts
             if p.identity.instance_handles and p.identity.instance_handles[0] == insert_handle]
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
