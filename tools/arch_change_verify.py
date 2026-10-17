"""BOQ CHANGE ATTRIBUTION WITH INDEPENDENT VERIFICATION (Phase 2B-8) - every BOQ total that differs between two runs of
one drawing, the correction records that cover it, and whether an independent reading of the drawing
(tools/indep_reader: ezdxf + shapely + arithmetic, no engine module) reproduces it. A correction record explains why a
quantity changed; it is not proof that the new quantity is right.

    python3 tools/arch_change_verify.py --before OUT_A --after OUT_B --dxf DRAWING [--facts FACTS.json]
                                        [--layer-roles LAYER=ROLE ...] [--out FILE.json]

Each difference is one of
    VERIFIED              a record covers it and every independent check that applies agrees with the new value
    EXPLAINED_UNVERIFIED  a record covers it; no independent check applies (the reason is stated)
    CONTRADICTED          a record covers it but an independent check disagrees
    UNEXPLAINED           no record covers it
exit 1 when any difference is UNEXPLAINED or CONTRADICTED.

Totals: the sum of measured_net, the line count and the count of lines with no value, per (item_code, location). A
room is matched between the runs by its polygon (largest overlap, at least half of either), so a room whose id
changed with its geometry is one location; walls, openings and strips keep their ids.

The records that explain: those of the after run (CORRECTIONS_V2_7.json) that the before run does not already carry
(same kind, floor, subject, decision and every field both share) - a correction already applied before cannot explain
a difference. The scope of a record, by kind (narrowed from tools/arch_v27_explain: a floor-wide record covers only
the locations its drawn entities touch):
    LAYER_ROLE                  the rooms whose polygon lies within 0.35 m of an entity of its layer, their openings,
                                the openings / strips within 0.35 m of those entities, and the floor's walls only
                                when the layer is (or was) a WALL or COLUMN layer - the wall run is read from wall
                                and column linework only (engine.source.arch_walls.walls)
    COLUMN_SHAPES, TURNED_COLUMN the rooms within 0.35 m of a column-layer entity, their openings, the record's
                                jamb openings, the floor's walls
    DOOR_OPENING, DOOR_FRAME, CURVED_WALL_BAND, WET_EVIDENCE, ARC_POLYGON, SLIVER_MERGE   as tools/arch_v27_explain
    REVIEW_INVARIANT_RELEASE    its room, its released item only
    WALL_STUB / WINDOW_SKIRTING (Phase 2B-9) the floor's walls, ARCH.WALL_RUN only / its room, FIN.SKIRTING only
    CURVED_OPENING (Phase N10)  its rooms, the opening and every strip line of it; CURVED_GLAZING_LAYER the rooms within
                                0.35 m of the layer's entities and their openings; MASONRY_PANEL the floor's walls,
                                ARCH.WALL_PANEL / ARCH.WALL_VOLUME / MAS.BLOCK only (no independent masonry reading:
                                EXPLAINED_UNVERIFIED; the arithmetic is proved on hand-truth fixtures, tests/m9_n10);
                                FACADE the floor's facade, ARCH.FACADE_RUN / ARCH.FACADE / FIN.EXT.FINISH only
    PROVENANCE                  nothing
Independent checks (heights from the facts file, a stated project input; widths and lengths from the drawing):
    INDEPENDENT_FACE            FIN.CEILING, FIN.FLOOR.*, FIN.WP.FLOOR, ARCH.SPACE: the face area at the room
    INDEPENDENT_TAKEOFF         FIN.PLASTER / FIN.PAINT = P x H - doors x H_door - windows x H_window;
                                FIN.WALL.TILE = P x H_tile - doors x min(H_door, H_tile) (no window on the face);
                                FIN.SKIRTING = P - doors (no window on the face; under WINDOW_SKIRTING, whose
                                windows have no established sill, P - every gap closed on the face: doors,
                                passages and windows alike are not certainly skirted); FIN.WP.DOORWAY = sum of door width x wall thickness;
                                at an opening: FIN.MARBLE.THRESHOLD = w x t, FIN.PLASTER = 2 t H_door + w t
                                (the face must have no hole and no gap without a door or window symbol)
    INDEPENDENT_ARC_CENSUS      ARCH.WALL_RUN under CURVED_WALL_BAND: the change equals the curved bands'
                                mid-radius length (concentric wall-layer arc pairs read from their own parameters,
                                both faces over 0.30 m - the wall run's convention; shorter stubs reported apart)
    INDEPENDENT_STUB_CENSUS     ARCH.WALL_RUN under WALL_STUB (Phase 2B-9): the change equals the floor's short
                                curved pairs (inner face 0.05 - 0.30 m) plus its straight returns (return_census),
                                both read again inside the floor's plan region (plus the curved bands under
                                CURVED_WALL_BAND)
    INDEPENDENT_FIXTURE_CENSUS  under WET_EVIDENCE: the fixture inserts and loose sanitary-layer pieces inside the
                                face equal the evidence the record states (it verifies the evidence, not the rule)
    INDEPENDENT_OUTLINE         ARCH.FACADE_RUN under FACADE (Phase N10): the exterior ring of the union of the
                                reader's faces inside the floor's plan region that holds the most of its rooms
    INDEPENDENT_OPENING_COUNT   ARCH.WINDOW at a room under CURVED_OPENING (Phase N10): the windows on the reader's
                                face of the room (straight window symbols and glazed curved gaps)
    Under CURVED_OPENING the reader closes every jambed curved gap on both faces and reads a glazed one on a face as a
    window of that face's arc (indep_reader curved_closures); INDEPENDENT_TAKEOFF then uses that width, and
    FIN.SKIRTING skips every gap of the face when no window of the room has an established sill.
The seed of a face is a point inside the run's room polygon: it selects which independent face; the face's area,
perimeter and openings come from the raw drawing only. A room the run joined through clear passages (attached cells)
is the union of the reader's own faces inside its polygon, only when that union is one polygon of the room's area
(Phase N10); otherwise no wall-face check applies to it. A space the wall lines leave open but the run closes with a
drawn zone line (DRAWN_LINE_ZONES) is read with that line, taken again from the drawing by its own handle, the same
way (Phase N10, D-P9-04): the boundary is then the run's zone-line decision, the area and lengths the reader's own."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import indep_reader as IR                                     # noqa: E402

POLICY = "URBAN_BOQ_CHANGE_VERIFY_V1"
TOL = 1e-6
REACH_M = 0.35
UNCLOSED_FACTOR, UNCLOSED_EXTRA_M2 = 3.0, 20.0
AREA_ITEMS = ("FIN.CEILING", "FIN.WP.FLOOR", "ARCH.SPACE")
STATUSES = ("VERIFIED", "EXPLAINED_UNVERIFIED", "CONTRADICTED", "UNEXPLAINED")


def _load(d, name):
    p = Path(d) / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _tol(v):
    return max(0.005, 0.001 * abs(v))


class Run:
    def __init__(self, d):
        self.dir = Path(d)
        self.lines = _load(d, "BOQ_LINES.json") or []
        self.rooms = {r["room_id"]: r for r in (_load(d, "ARCH_ROOMS.json") or {}).get("rooms") or []}
        self.openings = (_load(d, "ARCH_OPENINGS.json") or {}).get("openings") or []
        ds = _load(d, "DOOR_SCHEDULE.json") or {}
        self.doors = ((ds.get("doors") or {}).get("elements")) or []
        self.corrections = (_load(d, "CORRECTIONS_V2_7.json") or {}).get("corrections") or []
        plan = _load(d, "ARCH_PLAN.json") or {}
        self.roles = {}
        self.boxes = {}                               # the plan region of each floor (drawing units): a stated layout
        for reg in plan.get("regions") or ():
            for lay, role in (reg.get("layer_roles") or {}).items():
                self.roles.setdefault((reg.get("floor"), lay), role)
            if reg.get("box"):
                self.boxes.setdefault(reg.get("floor"), reg["box"])


def _polygon(room):
    from shapely.geometry import Polygon
    pts = room.get("polygon_m") or []
    if len(pts) < 3:
        return None
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)


def match_rooms(before, after):
    """before room id -> after room id (same floor, the largest overlap, at least half of either polygon)."""
    out = {}
    aps = {k: _polygon(r) for k, r in after.rooms.items()}
    for bid, br in before.rooms.items():
        if bid in after.rooms:
            out[bid] = bid
            continue
        bp = _polygon(br)
        if bp is None or bp.area <= 0:
            continue
        best = None
        for aid, ap in aps.items():
            if ap is None or after.rooms[aid].get("floor") != br.get("floor"):
                continue
            ov = bp.intersection(ap).area
            if ov >= 0.5 * max(bp.area, ap.area) and (best is None or ov > best[0]):
                best = (ov, aid)
        if best:
            out[bid] = best[1]
    return out


def _signature(c, other_keys):
    det = c.get("detail") or {}
    keep = {k: det[k] for k in sorted(det) if k in other_keys}
    return (c["correction"], c.get("floor"), c.get("subject"), c.get("decision"), json.dumps(keep, sort_keys=True))


def new_records(before, after):
    """the after run's records the before run does not already carry."""
    out = []
    for c in after.corrections:
        if c["correction"] == "PROVENANCE":
            continue
        same = False
        for b in before.corrections:
            if (b["correction"], b.get("floor"), b.get("subject"), b.get("decision")) != \
                    (c["correction"], c.get("floor"), c.get("subject"), c.get("decision")):
                continue
            common = set(b.get("detail") or {}) & set(c.get("detail") or {})
            if _signature(b, common) == _signature(c, common):
                same = True
                break
        if not same:
            out.append(c)
    return out


class Verifier:
    def __init__(self, before, after, dxf, facts=None, roles=None):
        self.b, self.a = Run(before), Run(after)
        self.dxf = dxf
        self.facts = facts or {}
        self.roles = roles or {}
        self._D = None
        self.match = match_rooms(self.b, self.a)

    @property
    def D(self):
        if self._D is None:
            # Phase N10: the reader closes curved gaps only when the after run carries a curved opening record
            curved = any(c["correction"] == "CURVED_OPENING" for c in self.a.corrections)
            self._D = IR.Drawing(self.dxf, roles=self.roles, **({"curved_closures": True} if curved else {}))
        return self._D

    # ------------------------------------------------------------------------------------------ locations
    def canon(self, rid):
        if rid in self.a.rooms:
            return rid
        if rid in self.b.rooms:
            return self.match.get(rid, "BEFORE:" + rid)
        return rid

    def room(self, key):
        if key in self.a.rooms:
            return self.a.rooms[key]
        if key.startswith("BEFORE:"):
            return self.b.rooms.get(key[7:])
        return None

    def totals(self, run):
        t = defaultdict(lambda: [0.0, 0, 0])
        floor = {}
        for ln in run.lines:
            loc = ln.get("location") or {}
            k = (ln["item_code"], self.canon(loc.get("room_id")))
            v = ln.get("measured_net")
            t[k][0] += v or 0.0
            t[k][1] += 1
            t[k][2] += v is None
            floor[k] = loc.get("floor")
        return t, floor

    # ------------------------------------------------------------------------------------------ scopes
    def _op_keys(self, f, oid):
        keys = {f"{f}-OPENING-{oid}", f"{f}-STRIP-{oid}"}
        for r in (self.a, self.b):
            for o in r.openings:
                if o["floor"] == f and o["opening_id"] == oid:
                    keys |= {self.canon(x) for x in o.get("rooms") or ()}
        return keys

    def _room_openings(self, f, keys):
        out = set()
        for r in (self.a, self.b):
            for rid, rm in r.rooms.items():
                if self.canon(rid) in keys:
                    for oid in list(rm.get("doors") or ()) + list(rm.get("passages") or ()) + \
                            list(rm.get("windows") or ()):
                        out |= self._op_keys(f, oid)
        return out

    def _near(self, f, geoms):
        """canonical room keys and opening keys of floor f within REACH_M of any of the geometries."""
        from shapely.geometry import Point
        from shapely.ops import unary_union
        if not geoms:
            return set(), set()
        u = unary_union(geoms)
        rooms, ops = set(), set()
        for r in (self.a, self.b):
            for rid, rm in r.rooms.items():
                p = _polygon(rm)
                if rm.get("floor") == f and p is not None and p.buffer(REACH_M).intersects(u):
                    rooms.add(self.canon(rid))
            for o in r.openings:
                c = (o.get("position") or {}).get("centre_m")
                if o["floor"] == f and c and Point(c).distance(u) <= REACH_M:
                    ops |= self._op_keys(f, o["opening_id"])
        return rooms, ops

    def _layer_geoms(self, layer=None, role=None):
        from shapely.geometry import LineString, Point
        out = []
        for p in self.D.pieces(role=role, layer=layer):
            out.append(LineString(p["pts"]) if len(p["pts"]) > 1 else Point(p["pts"][0]))
        return out

    def scope(self, c):
        """-> {"floor", "locations": set, "items": set or None}."""
        kind, fl, sub = c["correction"], c.get("floor"), c.get("subject")
        det = c.get("detail") or {}
        locs, items = set(), None
        if kind == "LAYER_ROLE":
            rooms, ops = self._near(fl, self._layer_geoms(layer=sub))
            locs = rooms | ops | self._room_openings(fl, rooms)
            if {c.get("decision"), c.get("before")} & {IR.WALL, IR.COLUMN}:
                locs.add(f"{fl}-WALLS")
        elif kind in ("COLUMN_SHAPES", "TURNED_COLUMN"):
            cols = []
            for (f2, lay), role in list(self.a.roles.items()) + list(self.b.roles.items()):
                if f2 == fl and role == IR.COLUMN:
                    cols += self._layer_geoms(layer=lay)
            rooms, ops = self._near(fl, cols)
            locs = rooms | ops | self._room_openings(fl, rooms) | {f"{fl}-WALLS"}
            for j in det.get("jamb_openings") or ():
                locs |= self._op_keys(fl, j.get("opening_id") if isinstance(j, dict) else j)
        elif kind == "DOOR_OPENING":
            locs = self._op_keys(fl, sub) | {f"{fl}-WALLS"}
        elif kind == "DOOR_FRAME":
            els = {e["element_id"]: e for r in (self.a, self.b) for e in r.doors}
            e = els.get(sub) or {}
            locs = {self.canon(x) for x in (e.get("from_room"), e.get("to_room")) if x}
            if det.get("opening_id"):
                locs |= self._op_keys(fl, det["opening_id"])
        elif kind == "CURVED_WALL_BAND":
            locs = {f"{fl}-WALLS"}
        elif kind == "WALL_STUB":
            locs, items = {f"{fl}-WALLS"}, {"ARCH.WALL_RUN"}
        elif kind == "WINDOW_SKIRTING":
            locs, items = {self.canon(sub)}, {"FIN.SKIRTING"}
        elif kind in ("WET_EVIDENCE", "ARC_POLYGON"):
            faces = set(det.get("faces") or ()) if kind == "ARC_POLYGON" else {sub}
            rooms = {self.canon(rid) for r in (self.a, self.b) for rid, rm in r.rooms.items()
                     if rm.get("face_id") in faces and rm.get("floor") == fl}
            locs = rooms | self._room_openings(fl, rooms)
        elif kind == "SLIVER_MERGE":
            locs = {self.canon(sub)}
        elif kind == "REVIEW_INVARIANT_RELEASE":
            locs, items = {self.canon(sub)}, {det.get("item_code")}
        elif kind == "CURVED_OPENING":
            locs = {self.canon(x) for x in det.get("rooms") or ()} | self._op_keys(fl, sub)
            locs |= {(ln.get("location") or {}).get("room_id") for r in (self.a, self.b) for ln in r.lines
                     if sub in str((ln.get("location") or {}).get("room_id") or "") and
                     (ln.get("location") or {}).get("floor") == fl}
        elif kind == "FACADE":
            locs, items = {f"{fl}-FACADE"}, {"ARCH.FACADE_RUN", "ARCH.FACADE", "FIN.EXT.FINISH"}
        elif kind == "MASONRY_PANEL":
            locs, items = {f"{fl}-WALLS"}, {"ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK"}
        elif kind == "CURVED_GLAZING_LAYER":
            rooms, ops = set(), set()
            for (f2, lay), role in self.a.roles.items():
                if f2 == fl and role == IR.WINDOW and self.b.roles.get((f2, lay)) != IR.WINDOW:
                    r_, o_ = self._near(fl, self._layer_geoms(layer=lay))
                    rooms, ops = rooms | r_, ops | o_
            locs = rooms | ops | self._room_openings(fl, rooms)
        return {"floor": fl, "locations": locs, "items": items}

    # ------------------------------------------------------------------------------------------ checks
    def _h(self, group, key, floor):
        tab = self.facts.get(group) or {}
        if group == "wall_heights":
            tab = tab.get(floor) or tab.get("*") or {}
        v = tab.get(key)
        return v.get("value_m") if isinstance(v, dict) else v

    def _face_of(self, rm):
        p = _polygon(rm) if rm else None
        if p is None:
            return None, "NO_ROOM_POLYGON"
        if rm.get("attached_cells"):
            # Phase N10: the run joined cells through clear passages into one room; the reader's face is then the
            # union of its own faces lying inside the room (it must close as one polygon of the room's area)
            from shapely.ops import unary_union
            u = unary_union(self.D.faces_within(p))
            if u.is_empty or u.geom_type != "Polygon" or abs(u.area - p.area) > max(0.05, 0.01 * p.area):
                return None, "ROOM_JOINS_CELLS_THROUGH_A_PASSAGE (the reader's faces inside it do not make the room)"
            return self.D.face_of(u), None
        f = self.D.face_at(p.representative_point().coords[0])
        if f is None:
            return None, "NO_CLOSED_INDEPENDENT_FACE"
        # the wall and column lines do not enclose the space: the face holds most of the run's polygon and runs on far
        # beyond it (UNCLOSED_FACTOR times and UNCLOSED_EXTRA_M2 more: the space is closed by a line of another layer,
        # the face is the open region around it) - a reading the independent reader cannot make, not a disagreement;
        # a face a little larger (two rooms merged, a missed closure) stays a disagreement
        if f["area_m2"] > max(UNCLOSED_FACTOR * p.area, p.area + UNCLOSED_EXTRA_M2) and \
                f["polygon"].intersection(p).area >= 0.5 * p.area:
            zf = self._zone_face(rm, p)
            if zf is not None:
                return zf, None
            return None, "NOT_CLOSED_BY_WALL_LINES (the space is bounded by a line of a non-wall layer)"
        return f, None

    def _zone_face(self, rm, p):
        """Phase N10 (D-P9-04): the drawn zone lines the run closes its spaces with on this floor (DRAWN_LINE_ZONES),
        read again from the drawing by their own handles; the space is the reader's face at its seed, or the union of
        the reader's faces inside it, when that closes as one polygon of the space's area (the reader's own gap rule
        can split a recess off). None when no such line or no such face."""
        from shapely.geometry import Point
        from shapely.ops import unary_union
        fl = rm.get("floor")
        handles = set()
        for r in (self.a, self.b):
            for x in r.rooms.values():
                if x.get("floor") != fl:
                    continue
                for ln in ((x.get("zone") or {}).get("lines") or ()):
                    src = str(ln.get("source") or "").split(":")
                    if len(src) >= 2 and src[1].isdigit():
                        handles.add(format(int(src[1]), "X"))
        if not handles:
            return None
        faces, used = self.D.faces_closed_by(sorted(handles))
        if not used:
            return None
        tol = max(0.05, 0.01 * p.area)
        seed = [g for g in faces if g.contains(Point(p.representative_point()))]
        cand = min(seed, key=lambda g: g.area) if seed else None
        if cand is None or abs(cand.area - p.area) > tol:
            u = unary_union([g for g in self.D.faces_within(p, faces=faces) if g.area > 1e-3])
            cand = u if (not u.is_empty and u.geom_type == "Polygon" and abs(u.area - p.area) <= tol) else None
        if cand is None:
            return None
        f = self.D.face_of(cand)
        f["zone_lines"] = sorted(x["handle"] for x in used)
        return f

    def _face(self, key):
        return self._face_of(self.room(key))

    def check_outline(self, floor):
        """the independent facade run of a floor: the exterior ring of the union of the reader's faces (every 0.30 -
        2.60 m wall gap closed on both faces) inside the floor's plan region that holds the most of the run's rooms of
        that floor (the region box is the run's stated layout, as the seeds are its rooms: it selects, never measures).
        None unless that outline holds every room of the floor."""
        from shapely.geometry import box as _box
        from shapely.ops import unary_union
        b = [v * self.D.k for v in self.a.boxes.get(floor) or ()]
        region = _box(*b) if len(b) == 4 else None
        faces = [f for f in self.D.faces() if f.area > 1e-6 and (region is None or region.contains(f))]
        if not faces:
            return None, "NO_INDEPENDENT_FACES"
        u = unary_union(faces)
        polys = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
        pts = [g.representative_point() for g in (_polygon(rm) for rm in self.a.rooms.values()
                                                   if rm.get("floor") == floor) if g is not None]
        if not pts:
            return None, "NO_ROOM_OF_THE_FLOOR"
        n, _, i = max((sum(1 for p in pts if g.contains(p)), g.area, i) for i, g in enumerate(polys))
        if n < len(pts):
            # an outline that leaves rooms of the floor outside is not the building's: a wall gap wider than the
            # reader's closure limit (or a gap it cannot close) leaks
            return None, f"INDEPENDENT_OUTLINE_INCOMPLETE: the reader's outline holds {n} of the floor's {len(pts)} rooms"
        g = polys[i]
        return {"method": "INDEPENDENT_OUTLINE", "value": g.exterior.length,
                "evidence": {"outline_area_m2": round(g.area, 6), "holes": len(g.interiors), "rooms_inside": n,
                             "rooms_of_the_floor": len(pts), "outlines": len(polys),
                             "within_region": region is not None}}, None

    def check_quantity(self, item, key, floor, after_net, kinds=(), win_classes=()):
        """the independent value of a measured line, or (None, reason). kinds: the explaining records' kinds
        (WINDOW_SKIRTING: no window's sill is established, so no window threshold is certainly skirted)."""
        if key and (key.endswith("-WALLS")):
            return None, "NO_INDEPENDENT_CHECK_FOR_THIS_ITEM"
        if key and key.endswith("-FACADE"):
            return self.check_outline(floor) if item == "ARCH.FACADE_RUN" else \
                (None, "NO_INDEPENDENT_CHECK_FOR_THIS_ITEM")
        if "-OPENING-" in (key or "") or "-STRIP-" in (key or ""):
            oid = key.split("-OPENING-")[-1] if "-OPENING-" in key else key.split("-STRIP-")[-1]
            op = next((o for r in (self.a, self.b) for o in r.openings
                       if o["floor"] == floor and o["opening_id"] == oid), None)
            c = (op or {}).get("position", {}).get("centre_m")
            if not op or op.get("kind") != "DOOR" or not c:
                return None, "NOT_A_DOOR_OPENING"
            d = self.D.opening_near(c, "DOOR")
            if d is None:
                return None, "NO_INDEPENDENT_DOOR_SYMBOL_AT_THE_OPENING"
            w, t, hd = d["width_m"], d["wall_t_m"], self._h("opening_heights", "DOOR", floor)
            if item == "FIN.MARBLE.THRESHOLD":
                return {"value": w * t, "evidence": {"door_m": round(w, 6), "wall_t_m": t}}, None
            if item == "FIN.PLASTER" and hd:
                return {"value": 2 * t * hd + w * t,
                        "evidence": {"door_m": round(w, 6), "wall_t_m": t, "door_h_m": hd,
                                     "formula": "2 x t x H_door + w x t"}}, None
            return None, "NO_INDEPENDENT_CHECK_FOR_THIS_ITEM"
        if item == "ARCH.WINDOW" and "CURVED_OPENING" in kinds:
            f, why = self._face(key)
            if f is None:
                return None, why
            ops, _free = self.D.openings_on(f)
            wins = [o for o in ops if o["kind"] == "WINDOW"]
            return {"value": float(len(wins)), "method": "INDEPENDENT_OPENING_COUNT",
                    "evidence": {"windows_on_face": [{"width_m": round(o["width_m"], 6),
                                                      "curved_face": o.get("curved_face")} for o in wins]}}, None
        area_item = item in AREA_ITEMS or item.startswith("FIN.FLOOR.")
        wall_item = item in ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE", "FIN.SKIRTING", "FIN.WP.DOORWAY")
        if not (area_item or wall_item):
            return None, "NO_INDEPENDENT_CHECK_FOR_THIS_ITEM"
        rm = self.room(key) or {}
        f, why = self._face(key)
        if f is None:
            return None, why
        if area_item:
            if (rm.get("void_m2") or 0) > 0 or (rm.get("double_height_m2") or 0) > 0 or \
                    (rm.get("obstruction_m2") or 0) > 0:
                return None, "VOID_OR_OBSTRUCTION_NOT_READ_INDEPENDENTLY"
            return {"value": f["area_m2"],
                    "evidence": {"face_area_m2": round(f["area_m2"], 6), "holes": f["holes"]}}, None
        if item == "FIN.SKIRTING" and "CURVED_OPENING" in kinds:
            # Phase N10: the room's windows (straight and curved) with an established sill, from the after run
            win_classes = set(win_classes) | {(o.get("v28") or {}).get("class") for o in self.a.openings
                                              if o["floor"] == floor and o.get("kind") == "WINDOW" and
                                              key in {self.canon(x) for x in o.get("rooms") or ()}}
            kinds = tuple(kinds) + ("WINDOW_SKIRTING",)
        if item == "FIN.SKIRTING" and "WINDOW_SKIRTING" in kinds and "WINDOW" not in win_classes:
            # Phase 2B-9: no window's sill is established, so the certain skirting skips every gap of the face - a
            # door, a passage (a gap without a symbol) and a window alike are not certainly skirted; a hole of the
            # face (a free-standing column or wall, read from wall and column lines only) is skirted all round
            clos = f.get("closure_geom")
            gaps = 0.0 if clos is None or clos.is_empty else clos.length
            _ops, free = self.D.openings_on(f)
            return {"value": f["perimeter_m"] + f["holes_perimeter_m"] - gaps,
                    "evidence": {"perimeter_m": round(f["perimeter_m"], 6), "gaps_m": round(gaps, 6),
                                 "holes": f["holes"], "holes_perimeter_m": round(f["holes_perimeter_m"], 6),
                                 "symbol_less_gaps_m": round(free or 0.0, 6),
                                 "formula": "P + hole perimeters - every gap closed on the face (doors, passages, "
                                            "windows without an established sill)"}}, None
        if f["holes"]:
            return None, "FACE_HAS_A_HOLE"
        ops, free = self.D.openings_on(f)
        if free > 0.05:
            return None, "GAP_WITHOUT_A_DOOR_OR_WINDOW_SYMBOL"
        P = f["perimeter_m"]
        doors = [o for o in ops if o["kind"] == "DOOR"]
        wins = [o for o in ops if o["kind"] == "WINDOW"]
        dw, ww = sum(o["width_m"] for o in doors), sum(o["width_m"] for o in wins)
        ev = {"perimeter_m": round(P, 6), "doors_m": [round(o["width_m"], 6) for o in doors],
              "windows_m": [round(o["width_m"], 6) for o in wins]}
        if item == "FIN.SKIRTING":
            if wins:
                return None, "WINDOW_SILL_NOT_IN_THE_DRAWING (skirting runs under a sill window, not floor glazing)"
            return {"value": P - dw, "evidence": dict(ev, formula="P - doors")}, None
        if item == "FIN.WP.DOORWAY":
            return {"value": sum(o["width_m"] * o["wall_t_m"] for o in doors),
                    "evidence": dict(ev, wall_t_m=[o["wall_t_m"] for o in doors], formula="sum door w x t")}, None
        hd, hw = self._h("opening_heights", "DOOR", floor), self._h("opening_heights", "WINDOW", floor)
        if item == "FIN.WALL.TILE":
            H = self._h("wall_heights", "WALL_TILE", floor)
            if not H or not hd:
                return None, "NO_HEIGHT_FACT"
            if wins:
                return None, "WINDOW_SILL_NOT_IN_THE_DRAWING"
            return {"value": P * H - dw * min(hd, H),
                    "evidence": dict(ev, H_m=H, door_h_m=hd, formula="P x H - doors x min(H_door, H)")}, None
        key_h = "PLASTER" if item == "FIN.PLASTER" else "PAINT"
        H = self._h("wall_heights", key_h, floor)
        if not H or not hd or (wins and not hw):
            return None, "NO_HEIGHT_FACT"
        if item == "FIN.PAINT" and any(ln["item_code"] == "FIN.WALL.TILE" and ln.get("measured_net") and
                                       self.canon((ln.get("location") or {}).get("room_id")) == key
                                       for ln in self.a.lines):
            return None, "PAINT_ABOVE_TILE_HEIGHT_RULE_NOT_INDEPENDENT"
        return {"value": P * H - dw * hd - ww * (hw or 0),
                "evidence": dict(ev, H_m=H, door_h_m=hd, window_h_m=hw,
                                 formula="P x H - doors x H_door - windows x H_window")}, None

    def check_stubs(self, fl):
        """the wall stubs of one floor read again from the drawing: the arc census's short curved pairs (inner face
        at least STUB_MIN_M, their middle inside the floor's plan region) and the straight return census in that
        region. -> {"lm", "curved", "returns", "excluded_curved"}"""
        box = [v * self.D.k for v in self.a.boxes.get(fl) or ()]
        if len(box) != 4:
            return {"lm": 0.0, "curved": [], "returns": [], "reason": "NO_PLAN_REGION"}
        ac = self.D.arc_census()

        def inside(p):
            return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
        curved = [x for x in ac["short_stubs"] if inside(x["mid"]) and x["inner_lm"] >= IR.STUB_MIN_M - 1e-9]
        small = [x for x in ac["short_stubs"] if inside(x["mid"]) and x["inner_lm"] < IR.STUB_MIN_M - 1e-9]
        rc = self.D.return_census(regions=[box])
        lm = round(sum(x["mid_lm"] for x in curved) + rc["returns_lm"], 6)
        strip = lambda x: {k: v for k, v in x.items() if k not in ("handles", "centre", "mid")}  # noqa: E731
        return {"lm": lm, "curved": [strip(x) for x in curved], "returns": [strip(x) for x in rc["returns"]],
                "below_stub_minimum": [strip(x) for x in small], "stub_min_m": IR.STUB_MIN_M}

    def check_census(self, c):
        """INDEPENDENT_FIXTURE_CENSUS of a WET_EVIDENCE record: the census of its face against its stated evidence."""
        det = c.get("detail") or {}
        rm = next((rm for r in (self.a, self.b) for rm in r.rooms.values()
                   if rm.get("face_id") == c.get("subject") and rm.get("floor") == c.get("floor")), None)
        f, why = self._face_of(rm)
        if f is None:
            return None, why
        census = self.D.fixture_census(f["polygon"])
        stated = {k: 0 for k in IR.FIXTURE_WORDS}
        for x in det.get("fixtures") or ():
            k = IR.fixture_kind(str(x))
            if k:
                stated[k] += 1
        if det.get("wc_shapes"):
            return {"independent": census, "stated": stated, "agrees": None,
                    "reason": "WC_LINEWORK_SHAPE_NOT_REDERIVED"}, None
        agrees = all(census[k] == stated[k] for k in stated)
        return {"independent": census, "stated": dict(stated, wc_shapes=0), "agrees": agrees}, None

    # ------------------------------------------------------------------------------------------ report
    def report(self):
        ta, fa = self.totals(self.b)
        tb, fb = self.totals(self.a)
        recs = new_records(self.b, self.a)
        scopes = {c["id"]: self.scope(c) for c in recs}
        census = {}
        rows = []
        names = defaultdict(set)
        for k in set(ta) | set(tb):
            rm = self.room(k[1]) if k[1] else None
            if rm:
                names[(fb.get(k) or fa.get(k), rm.get("name_en"))].add(k[1])
        for k in sorted(set(ta) | set(tb), key=lambda x: (str(x[0]), str(x[1]))):
            va, vb = ta.get(k, [0.0, 0, 0]), tb.get(k, [0.0, 0, 0])
            if abs(va[0] - vb[0]) <= TOL and va[1:] == vb[1:]:
                continue
            item, key = k
            fl = fb.get(k) or fa.get(k)
            rm = self.room(key) if key else None
            label = key
            if rm:
                label = rm.get("name_en") or key
                if len(names[(fl, rm.get("name_en"))]) > 1:
                    label = f"{label} [{key}]"
            by = sorted(cid for cid, s in scopes.items() if s["floor"] == fl and key in s["locations"] and
                        (s["items"] is None or item in s["items"]))
            kinds = sorted({c["correction"] for c in recs if c["id"] in by})
            row = {"item_code": item, "location": label, "room_key": key, "floor": fl,
                   "before": round(va[0], 6), "after": round(vb[0], 6), "delta": round(vb[0] - va[0], 6),
                   "lines": {"before": va[1], "after": vb[1]}, "no_value": {"before": va[2], "after": vb[2]},
                   "explained_by": by, "kinds": kinds}
            if not by:
                row.update(status="UNEXPLAINED", verification=None, checks=[])
                rows.append(row)
                continue
            checks = []
            if "WALL_STUB" in kinds and item == "ARCH.WALL_RUN":
                res = self.check_stubs(fl)
                ind = res["lm"]
                if "CURVED_WALL_BAND" in kinds:
                    ac = self.D.arc_census()
                    ind = round(ind + ac["mid_lm"], 6)
                    res = dict(res, curved_bands_lm=ac["mid_lm"])
                checks.append({"method": "INDEPENDENT_STUB_CENSUS", "independent_delta": ind, "delta": row["delta"],
                               "tolerance": _tol(ind), "agrees": abs(ind - row["delta"]) <= _tol(ind),
                               "evidence": res})
            elif "CURVED_WALL_BAND" in kinds and item == "ARCH.WALL_RUN":
                ac = self.D.arc_census()
                checks.append({"method": "INDEPENDENT_ARC_CENSUS", "independent_delta": ac["mid_lm"],
                               "delta": row["delta"], "tolerance": _tol(ac["mid_lm"]),
                               "agrees": abs(ac["mid_lm"] - row["delta"]) <= _tol(ac["mid_lm"]),
                               "evidence": {"bands": ac["bands"], "min_run_m": ac["min_run_m"],
                                            "short_stubs_not_in_the_run_lm": ac["short_stubs_mid_lm"],
                                            "short_stubs": ac["short_stubs"]}})
            for cid in by:
                c = next(x for x in recs if x["id"] == cid)
                if c["correction"] == "WET_EVIDENCE":
                    if cid not in census:
                        census[cid] = self.check_census(c)
                    res, why = census[cid]
                    if res is None:
                        checks.append({"method": "INDEPENDENT_FIXTURE_CENSUS", "agrees": None, "reason": why})
                    else:
                        checks.append({"method": "INDEPENDENT_FIXTURE_CENSUS", "record": cid, **res})
            measured = vb[1] > 0 and vb[2] < vb[1]
            if measured and item != "ARCH.WALL_RUN":
                wcls = {v for cid in by for c in recs if c["id"] == cid and c["correction"] == "WINDOW_SKIRTING"
                        for v in ((c.get("detail") or {}).get("windows") or {}).values()}
                res, why = self.check_quantity(item, key, fl, vb[0], kinds, wcls)
                if res is None:
                    checks.append({"method": "INDEPENDENT_TAKEOFF", "agrees": None, "reason": why})
                else:
                    meth = res.get("method") or ("INDEPENDENT_FACE" if (item in AREA_ITEMS or
                                                                        item.startswith("FIN.FLOOR.")) else
                                                 "INDEPENDENT_TAKEOFF")
                    v = round(res["value"], 6)
                    checks.append({"method": meth, "independent": v, "after": row["after"], "tolerance": _tol(v),
                                   "agrees": abs(v - row["after"]) <= _tol(v), "evidence": res["evidence"]})
            elif not measured:
                checks.append({"method": "INDEPENDENT_TAKEOFF", "agrees": None,
                               "reason": "NO_MEASURED_VALUE_AFTER (the line was withheld, held or removed)"})
            applied = [x for x in checks if x.get("agrees") is not None]
            bad = [x for x in applied if not x["agrees"]]
            # the check shown: a quantity reading for a quantity correction, the fixture census for an evidence one
            census_first = set(kinds) <= {"WET_EVIDENCE"}
            applied.sort(key=lambda x: (x["method"] == "INDEPENDENT_FIXTURE_CENSUS") != census_first)
            if bad:
                status, ver = "CONTRADICTED", bad[0]
            elif applied:
                status, ver = "VERIFIED", applied[0]
            else:
                status, ver = "EXPLAINED_UNVERIFIED", (checks[0] if checks else
                                                       {"method": None, "reason": "NO_INDEPENDENT_CHECK"})
            row.update(status=status, verification=ver, checks=checks)
            rows.append(row)
        summary = {s: sum(r["status"] == s for r in rows) for s in STATUSES}
        summary.update(differences=len(rows), records_considered=len(recs),
                       records_already_in_before=len([c for c in self.a.corrections
                                                      if c["correction"] != "PROVENANCE"]) - len(recs),
                       by_kind={k: {s: sum(r["status"] == s and k in r["kinds"] for r in rows) for s in STATUSES}
                                for k in sorted({c["correction"] for c in recs})})
        return {"policy": POLICY, "reader": IR.POLICY, "before": str(self.b.dir.name), "after": str(self.a.dir.name),
                "rooms_matched": {k: v for k, v in sorted(self.match.items()) if k != v},
                "records": [{"id": c["id"], "correction": c["correction"], "floor": c.get("floor"),
                             "subject": c.get("subject"),
                             "scope": sorted(scopes[c["id"]]["locations"]),
                             "items": sorted(scopes[c["id"]]["items"]) if scopes[c["id"]]["items"] else None}
                            for c in recs],
                "differences": rows, "summary": summary,
                "never": "a correction record taken as proof of a quantity; a difference called verified without an "
                         "independent reading that agrees"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--facts")
    ap.add_argument("--layer-roles", nargs="*", default=[])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    facts = json.loads(Path(a.facts).read_text(encoding="utf-8")) if a.facts else {}
    roles = dict(x.split("=", 1) for x in a.layer_roles)
    rep = Verifier(a.before, a.after, a.dxf, facts, roles).report()
    txt = json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    print(json.dumps(rep["summary"], sort_keys=True))
    return 1 if rep["summary"]["UNEXPLAINED"] or rep["summary"]["CONTRADICTED"] else 0


if __name__ == "__main__":
    sys.exit(main())
