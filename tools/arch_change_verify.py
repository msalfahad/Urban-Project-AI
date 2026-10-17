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
    PROVENANCE                  nothing
Independent checks (heights from the facts file, a stated project input; widths and lengths from the drawing):
    INDEPENDENT_FACE            FIN.CEILING, FIN.FLOOR.*, FIN.WP.FLOOR, ARCH.SPACE: the face area at the room
    INDEPENDENT_TAKEOFF         FIN.PLASTER / FIN.PAINT = P x H - doors x H_door - windows x H_window;
                                FIN.WALL.TILE = P x H_tile - doors x min(H_door, H_tile) (no window on the face);
                                FIN.SKIRTING = P - doors; FIN.WP.DOORWAY = sum of door width x wall thickness;
                                at an opening: FIN.MARBLE.THRESHOLD = w x t, FIN.PLASTER = 2 t H_door + w t
                                (the face must have no hole and no gap without a door or window symbol)
    INDEPENDENT_ARC_CENSUS      ARCH.WALL_RUN under CURVED_WALL_BAND: the change equals the curved bands'
                                mid-radius length (concentric wall-layer arc pairs read from their own parameters)
    INDEPENDENT_FIXTURE_CENSUS  under WET_EVIDENCE: the fixture inserts and loose sanitary-layer pieces inside the
                                face equal the evidence the record states (it verifies the evidence, not the rule)
The seed of a face is a point inside the run's room polygon: it selects which independent face; the face's area,
perimeter and openings come from the raw drawing only."""

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
        for reg in plan.get("regions") or ():
            for lay, role in (reg.get("layer_roles") or {}).items():
                self.roles.setdefault((reg.get("floor"), lay), role)


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
            self._D = IR.Drawing(self.dxf, roles=self.roles)
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
        elif kind in ("WET_EVIDENCE", "ARC_POLYGON"):
            faces = set(det.get("faces") or ()) if kind == "ARC_POLYGON" else {sub}
            rooms = {self.canon(rid) for r in (self.a, self.b) for rid, rm in r.rooms.items()
                     if rm.get("face_id") in faces and rm.get("floor") == fl}
            locs = rooms | self._room_openings(fl, rooms)
        elif kind == "SLIVER_MERGE":
            locs = {self.canon(sub)}
        elif kind == "REVIEW_INVARIANT_RELEASE":
            locs, items = {self.canon(sub)}, {det.get("item_code")}
        return {"floor": fl, "locations": locs, "items": items}

    # ------------------------------------------------------------------------------------------ checks
    def _h(self, group, key, floor):
        tab = self.facts.get(group) or {}
        if group == "wall_heights":
            tab = tab.get(floor) or tab.get("*") or {}
        v = tab.get(key)
        return v.get("value_m") if isinstance(v, dict) else v

    def _face(self, key):
        rm = self.room(key)
        p = _polygon(rm) if rm else None
        if p is None:
            return None, "NO_ROOM_POLYGON"
        f = self.D.face_at(p.representative_point().coords[0])
        if f is None:
            return None, "NO_CLOSED_INDEPENDENT_FACE"
        return f, None

    def check_quantity(self, item, key, floor, after_net):
        """the independent value of a measured line, or (None, reason)."""
        if key and (key.endswith("-WALLS")):
            return None, "NO_INDEPENDENT_CHECK_FOR_THIS_ITEM"
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

    def check_census(self, c):
        """INDEPENDENT_FIXTURE_CENSUS of a WET_EVIDENCE record: the census of its face against its stated evidence."""
        det = c.get("detail") or {}
        rm = next((rm for r in (self.a, self.b) for rm in r.rooms.values()
                   if rm.get("face_id") == c.get("subject") and rm.get("floor") == c.get("floor")), None)
        p = _polygon(rm) if rm else None
        if p is None:
            return None, "NO_ROOM_POLYGON"
        f = self.D.face_at(p.representative_point().coords[0])
        if f is None:
            return None, "NO_CLOSED_INDEPENDENT_FACE"
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
            if "CURVED_WALL_BAND" in kinds and item == "ARCH.WALL_RUN":
                ac = self.D.arc_census()
                checks.append({"method": "INDEPENDENT_ARC_CENSUS", "independent_delta": ac["mid_lm"],
                               "delta": row["delta"], "tolerance": _tol(ac["mid_lm"]),
                               "agrees": abs(ac["mid_lm"] - row["delta"]) <= _tol(ac["mid_lm"]),
                               "evidence": {"bands": ac["bands"]}})
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
                res, why = self.check_quantity(item, key, fl, vb[0])
                if res is None:
                    checks.append({"method": "INDEPENDENT_TAKEOFF", "agrees": None, "reason": why})
                else:
                    meth = "INDEPENDENT_FACE" if (item in AREA_ITEMS or item.startswith("FIN.FLOOR.")) else \
                        "INDEPENDENT_TAKEOFF"
                    v = round(res["value"], 6)
                    checks.append({"method": meth, "independent": v, "after": row["after"], "tolerance": _tol(v),
                                   "agrees": abs(v - row["after"]) <= _tol(v), "evidence": res["evidence"]})
            elif not measured:
                checks.append({"method": "INDEPENDENT_TAKEOFF", "agrees": None,
                               "reason": "NO_MEASURED_VALUE_AFTER (the line was withheld, held or removed)"})
            applied = [x for x in checks if x.get("agrees") is not None]
            bad = [x for x in applied if not x["agrees"]]
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
