"""ELEMENT REGISTER V0 (T-134; owner management decision 2026-10-20 §4; design docs/agents/ELEMENT_REGISTER.md).

Reads the outputs of an ARCH_TAKEOFF_V3.0 run (or any run that writes BOQ_LINES.json beside ARCH_ROOMS.json,
ARCH_WALLS.json, ARCH_OPENINGS.json, DOOR_SCHEDULE.json, CURVED_OPENINGS.json and MEMBRANE_PIECE_PLAN.json) and writes a
register BESIDE them; it changes no input file, no line and no quantity:

    ELEMENT_REGISTER_V0.json   one record per element + the checks + the lines no element feeds (with the reason)
    ELEMENT_REGISTER_V0.csv    one row per (element, BOQ line) link

    build(lines, sources, project=None)   -> register dict          (sources: the parsed ARCH_* / schedule files)
    build_dir(run_dir, lines_file=None)    -> register dict          (reads the files of a run folder; load_run)
    checks(register)                       -> {"double_finish", "double_concrete", "duplicate_lines",
                                               "held_released", "unlinked"}
    map_revisions(old, new)                -> old element id -> new element id (label first, then overlap >= 95 %)

Element id: <project>/<rev>/<floor>/<kind>/<local> (ELEMENT_REGISTER.md). rev = the first 12 hex of the source's
revision_set_sha256 carried by the lines (architectural and structural sets keep their own rev). local = the printed
label when the source carries one (room function codes, footing / column marks, roof zone label), a label printed
more than once takes .1, .2 ... ordered by its position (x, then y); without a label: G<8 hex> of the outline / axis
rounded to 1 mm (stable on a rerun of the same revision) or, where the outputs carry no geometry, E<8 hex> of the
engine's own element key (label_basis says which; an E-id is stable on a rerun only).

Kinds in v0: ROOM, EXT (exterior space), WALL, OPEN, STAIR-FLIGHT, LANDING, ZONE-WP (wet-room and roof membrane zones),
FTG, COL (columns and necks), GB, STRAP, BEAM, SLAB. Facade outlines, domes, pool, stair concrete, boundary wall and
parapets are later kinds (build order step 3): their lines are listed UNLINKED with that reason, never dropped.

Status (seven statuses, DESIGNER_CLARIFICATIONS.md §3): an architectural element takes its status from its own source
record (outline present -> CALCULATED; an opening without a measured width -> HELD; a door assembly the schedule calls
UNRESOLVED -> HELD); a structural element from its own concrete line (SOURCE_DERIVED / MEASURED -> CALCULATED,
PROVISIONAL -> PROVISIONAL, BOUNDED_EXPOSURE / BLOCKED_RFI -> HELD, NOT_APPLICABLE_WITH_EVIDENCE -> NOT_APPLICABLE).
VERIFIED is never set here: it needs the verifier's own reconstruction. The steel lines of a structural element are
linked to it (they read its geometry); this module writes no reinforcement quantity.

Checks: (1) one finish per surface: an element feeding two different floor-finish items, or two concrete items;
(2) a HELD / NOT_APPLICABLE element feeding a line that releases a quantity (the line's own state is MEASURED,
SOURCE_DERIVED or PROVISIONAL); (3) every line is linked to at least one element or listed UNLINKED with its reason;
(4) two lines with the same element, item, unit and line element key (one surface counted twice); (5) elements
no line takes a quantity from; (6) a CONFLICT element (its own concrete line declares a *_CONFLICT convention: two
drawn sources disagree and the route chose one) whose lines release a quantity - listed for the verifier, not a defect
of the register.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "URBAN_ELEMENT_REGISTER_V0"
STATUSES = ("VERIFIED", "CALCULATED", "PROVISIONAL", "ASSUMED", "HELD", "CONFLICT", "NOT_APPLICABLE")
WEAKNESS = {"VERIFIED": 0, "CALCULATED": 1, "PROVISIONAL": 2, "ASSUMED": 3, "NOT_APPLICABLE": 4, "HELD": 5,
            "CONFLICT": 6}
KINDS = ("ROOM", "EXT", "WALL", "OPEN", "STAIR-FLIGHT", "LANDING", "ZONE-WP", "FTG", "COL", "GB", "STRAP", "BEAM",
         "SLAB")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
LINE_STATUS = {"MEASURED": "CALCULATED", "SOURCE_DERIVED": "CALCULATED", "PROVISIONAL": "PROVISIONAL",
               "BOUNDED_EXPOSURE": "HELD", "BLOCKED_RFI": "HELD", "NOT_APPLICABLE_WITH_EVIDENCE": "NOT_APPLICABLE",
               "EXCLUDED_WITH_REASON": "NOT_APPLICABLE"}
# one finish per surface (Q-66 B / Q-70 A): the floor surface of an element takes ONE of these
FLOOR_FINISH = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.LANDING", "FIN.MARBLE.TREAD",
                "FIN.MARBLE.THRESHOLD")
CONCRETE_PREFIX = "STR.CONC."
OVERLAP_MIN = 0.95
OPENING_KEY = re.compile(r"^(C?OP-\d+)$")
LATER_KINDS = {"FACADE": "facade outlines are a later kind (ELEMENT_REGISTER.md build order step 3)",
               "DOMES": "domes are a later kind (build order step 3)", "POOL": "pool is a later kind (step 3)",
               "STAIRS": "stair concrete binds to flights / landings in a later step (T-111 ledger, build order 2)",
               "BOUNDARY_WALL": "boundary wall is a later kind (step 3)", "PARAPETS": "parapets are a later kind",
               "LINTELS": "lintels are a later kind", "WATER_TANK": "tank is a later kind", "LIFT": "lift is a later kind"}


def _h(obj, n=8):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:n]


def _mm(pt, unit_m):
    return [int(round(float(c) * unit_m * 1000.0)) for c in pt]


def _safe(s):
    return re.sub(r"[^A-Za-z0-9.+_-]", "-", str(s)) or "-"


def _floor(storey):
    return "FDN" if storey == "FOUNDATION" else (storey or "NONE")


class _Reg:
    def __init__(self, project):
        self.project = _safe(project)
        self.el = {}                                  # element id -> record
        self.by_key = {}                              # engine key -> element id
        self.pending = defaultdict(list)              # (floor, kind, base label) -> [(sort key, engine key, record)]

    def add(self, key, rev, floor, kind, label, sort_key, record, geom_local=None, engine_local=None):
        """queue an element; ids are given in finish() once every repeat of a label is known."""
        assert kind in KINDS, kind
        record = dict(record, kind=kind, floor=floor, label=label, rev=rev)
        if label:
            self.pending[(rev, floor, kind, _safe(label))].append((sort_key, key, record))
        else:
            local, basis = (geom_local, "GEOMETRY_HASH_1MM") if geom_local else (engine_local, "ENGINE_KEY_HASH")
            self._put(key, record, local, basis)

    def _put(self, key, record, local, basis):
        eid = f"{self.project}/{record['rev']}/{record['floor']}/{record['kind']}/{local}"
        if eid in self.el:                            # two geometries with one hash: never merged silently
            eid = f"{eid}~{_h(key, 6)}"
        record = dict(record, id=eid, local=local, label_basis=basis, engine_key=key, boq_lines=[])
        self.el[eid] = record
        self.by_key[key] = eid

    def finish(self):
        for (_rev, _fl, _k, base), items in sorted(self.pending.items()):
            items.sort(key=lambda t: (t[0], t[1]))
            for i, (_sk, key, rec) in enumerate(items, 1):
                self._put(key, rec, base if len(items) == 1 else f"{base}.{i}", "PRINTED_LABEL")
        self.pending.clear()


# ----------------------------------------------------------------------------------------------- architectural pieces

def _room_records(reg, rooms, rev, unit_m):
    for r in rooms:
        poly = r.get("polygon_m") or []
        outline = [[int(round(x * 1000.0)), int(round(y * 1000.0))] for x, y in poly]
        codes = [c for c in (r.get("codes") or []) if c]
        label = "+".join(sorted(set(codes))) if codes and r.get("label_source") == "TEXT" else None
        kind = "EXT" if r.get("kind") == "EXTERIOR" else "ROOM"
        sk = (min((p[0] for p in outline), default=0), min((p[1] for p in outline), default=0))
        rec = {"outline_mm": outline, "status": "CALCULATED" if outline else "HELD",
               "evidence": {"file": "ARCH_ROOMS.json", "room_id": r["room_id"], "face_id": r.get("face_id"),
                            "region": r.get("region_id"), "label_source": r.get("label_source"),
                            "area_m2": r.get("area_m2")},
               "status_basis": "outline from the plan faces" if outline else "no outline in ARCH_ROOMS.json"}
        reg.add(("ROOM", r["room_id"]), rev, r["floor"], kind, label, sk, rec,
                geom_local="G" + _h(outline) if outline else None, engine_local="E" + _h(r["room_id"]))


def _wall_records(reg, floors, rev, unit_m):
    for f in floors:
        for w in f.get("walls") or []:
            axis = [_mm(p, unit_m) for p in w.get("centreline") or []]
            t_mm = int(round(float(w.get("t_m") or 0) * 1000))
            rec = {"axis_mm": axis, "t_mm": t_mm, "status": "CALCULATED" if axis and t_mm else "HELD",
                   "status_basis": "centreline and thickness from the wall topology" if axis and t_mm
                   else "no centreline or thickness", "family": w.get("family"), "net_lm": w.get("net_lm"),
                   "evidence": {"file": "ARCH_WALLS.json", "wall_id": w["wall_id"], "layer": w.get("layer"),
                                "source_handles": list(w.get("source_ids") or [])}}
            reg.add(("WALL", f["floor"], w["wall_id"]), rev, f["floor"], "WALL", None, None, rec,
                    geom_local="G" + _h([axis, t_mm]) if axis else None, engine_local="E" + _h(w["wall_id"]))


def _opening_records(reg, openings, curved, doors, rev, unit_m):
    for o in openings:
        c = (o.get("position") or {}).get("centre_m")
        centre = [int(round(v * 1000.0)) for v in c] if c else None
        width = o.get("width_m")
        held = width is None or centre is None
        rec = {"centre_mm": centre, "width_mm": int(round(width * 1000)) if width else None,
               "opening_kind": o.get("kind"), "status": "HELD" if held else "CALCULATED",
               "status_basis": "no measured width / position" if held else "width measured between drawn jambs",
               "held_attributes": ["height"] if o.get("height_state") == "NOT_ESTABLISHED" else [],
               "evidence": {"file": "ARCH_OPENINGS.json", "opening_id": o["opening_id"], "host_wall": o.get("host_wall"),
                            "rooms": list(o.get("rooms") or []), "status": o.get("status")}}
        reg.add(("OPEN", o["floor"], o["opening_id"]), rev, o["floor"], "OPEN", None, None, rec,
                geom_local="G" + _h([o.get("kind"), centre, rec["width_mm"]]) if centre else None,
                engine_local="E" + _h([o["floor"], o["opening_id"]]))
    for o in curved:
        if ("OPEN", o["floor"], o["opening_id"]) in reg.by_key:     # already read from ARCH_OPENINGS.json
            reg.el[reg.by_key[("OPEN", o["floor"], o["opening_id"])]]["evidence"]["curved_record"] = \
                {"file": "CURVED_OPENINGS.json", "jamb_handles": list(o.get("jambs") or []),
                 "width_basis": o.get("width_basis")}
            continue
        rec = {"centre_mm": None, "width_mm": int(round(o["width_m"] * 1000)) if o.get("width_m") else None,
               "opening_kind": o.get("kind"), "status": "CALCULATED" if o.get("width_m") else "HELD",
               "status_basis": f"curved opening, width basis {o.get('width_basis')}", "held_attributes": [],
               "evidence": {"file": "CURVED_OPENINGS.json", "opening_id": o["opening_id"],
                            "jamb_handles": list(o.get("jambs") or []), "rooms": list(o.get("rooms") or [])}}
        reg.add(("OPEN", o["floor"], o["opening_id"]), rev, o["floor"], "OPEN", None, None, rec,
                geom_local="G" + _h(["CURVED", sorted(o.get("jambs") or []), rec["width_mm"]]),
                engine_local="E" + _h([o["floor"], o["opening_id"]]))
    door_to = {}                                      # door assembly id -> element id it describes
    for d in doors:
        ops = [m.group(1) for e in d.get("evidence") or [] for m in [re.match(r"^EV-(C?OP-\d+)-BAND$", e.get("id") or "")]
               if m]
        closure = sorted({t for e in d.get("evidence") or [] if (e.get("id") or "").endswith("-CLOSURE")
                          for t in re.findall(r"D\d+:\d+", e["id"])})
        if len(ops) == 1 and ("OPEN", d["floor"], ops[0]) in reg.by_key_pending_or_done():
            door_to[d["element_id"]] = ("OPEN", d["floor"], ops[0])
            continue
        centre = _mm(d["centre"], unit_m) if d.get("centre") else None
        st = d.get("state")
        rec = {"centre_mm": centre, "width_mm": None, "opening_kind": "DOOR_CLOSURE" if closure else "DOOR",
               "status": "HELD" if st == "UNRESOLVED" or centre is None else
               ("PROVISIONAL" if st == "PROVISIONAL" else "CALCULATED"),
               "status_basis": f"door schedule state {st}", "held_attributes": [], "closure_handles": closure,
               "evidence": {"file": "DOOR_SCHEDULE.json", "door_element": d["element_id"],
                            "evidence_ids": [e.get("id") for e in d.get("evidence") or []]}}
        key = ("OPEN", d["floor"], d["element_id"])
        reg.add(key, rev, d["floor"], "OPEN", None, None, rec,
                geom_local="G" + _h(["DOOR", centre]) if centre else None, engine_local="E" + _h(d["element_id"]))
        door_to[d["element_id"]] = key
    return door_to


# ---------------------------------------------------------------------------------------------------- line -> element

_SEG = re.compile(r"^(?P<lab>[A-Za-z][A-Za-z0-9]*)?@(?P<x>-?\d+),(?P<y>-?\d+)")


def _structural(code, eid):
    """(kind, engine key, label, sort key, storey) of a route G line's own element, or (None, reason)."""
    parts = eid.split(":")
    if code == "STR.REBAR":
        parts = ["P-C" if parts[0] == "P-S" else "U-C"] + parts[1:-1]     # the steel's concrete element
    piece = None
    if parts and parts[-1] == "IN_OPEN_FOOTING_OUTLINE":   # V3.0: the part of a strap inside an open footing
        parts, piece = parts[:-1], parts[-1]             # outline is its own (held) piece, not the whole strap
    fam = parts[1] if len(parts) > 1 else ""
    if fam == "FTG" or fam == "COL" or fam == "NECK":
        seg_i = 3 if fam != "NECK" else 4
        seg = parts[seg_i] if len(parts) > seg_i else ""
        storey = "FOUNDATION" if fam in ("FTG", "NECK") else (seg.split("|")[1] if "|" in seg else None)
        m = _SEG.match(seg.split("|")[0])
        lab = (m.group("lab") if m else None) or None
        sk = (int(m.group("x")), int(m.group("y"))) if m else None
        kind = "FTG" if fam == "FTG" else "COL"
        if fam == "NECK":
            lab = f"{lab}.NECK" if lab else "NECK"
        return kind, ("ST", ":".join(parts[1:])), lab, sk, storey
    if fam in ("GROUND_BEAMS", "BEAMS", "SLABS", "GROUND_SLAB") and len(parts) >= 4:
        storey = parts[2]
        kind = {"BEAMS": "BEAM", "SLABS": "SLAB", "GROUND_SLAB": "SLAB"}.get(fam) or (
            "STRAP" if storey == "FOUNDATION" else "GB")
        return kind, ("ST", ":".join(parts[1:4]) + (":" + piece if piece else "")), None, None, storey
    if fam == "SCOPE" and len(parts) > 2:
        return None, LATER_KINDS.get(parts[2], f"scope family {parts[2]} is not a register v0 kind")
    if fam == "PLAIN_CONCRETE":
        return "AGG:FTG", None, None, None, "FOUNDATION"
    return None, f"route G element key family {fam or '?'} is not a register v0 kind"


def _link_targets(ln, reg, rooms, door_to, walls_by_ft):
    """-> ([(engine key, role)], reason if none). role PRIMARY = the element the line measures; HOST = the room around
    it; MEMBER = one of the elements an aggregate line sums."""
    code, loc = ln["item_code"], ln["location"]
    eid, floor = loc.get("element_id") or "", loc.get("floor")
    if code.startswith("STR."):
        s = _structural(code, eid)
        if s[0] is None:
            return [], s[1]
        if s[0] == "AGG:FTG":
            ks = [k for k, e in reg.by_key.items() if k[0] == "ST" and reg.el[e]["kind"] == "FTG"]
            return [(k, "MEMBER") for k in sorted(ks)], None if ks else "no footing element to aggregate"
        return [(s[1], "PRIMARY")], None
    if eid.startswith("DOOR-"):
        k = door_to.get(eid)
        return ([(k, "PRIMARY")], None) if k else ([], "door assembly not in DOOR_SCHEDULE.json")
    head, _, suffix = eid.partition(":")
    m = re.match(r"^(?P<fl>[^-]+)-(STRIP|OPENING)-(?P<rest>.+)$", head)
    if m:
        rest = m.group("rest")
        if OPENING_KEY.match(rest):
            return [(("OPEN", m.group("fl"), rest), "PRIMARY")], None
        if rest.startswith("SITE-"):
            return [], "threshold strip the engine left unattributed (no opening or door assembly names it)"
        toks = {t.replace("_", ":") for t in re.findall(r"D\d+_\d+", rest)}
        hits = [k for k, e in reg.by_key.items() if k[0] == "OPEN" and k[1] == m.group("fl")
                and reg.el[e].get("closure_handles") and set(reg.el[e]["closure_handles"]) <= toks]
        return ([(hits[0], "PRIMARY")], None) if len(hits) == 1 else \
            ([], f"door closure strip matches {len(hits)} door assemblies")
    if head.endswith("-WALLS"):
        t = re.search(r"t=(\d+(?:\.\d+)?)", suffix)
        ks = walls_by_ft.get((floor, int(round(float(t.group(1)) * 1000)))) if t else None
        return ([(k, "MEMBER") for k in ks], None) if ks else ([], "no wall of this floor and thickness")
    if "-FACADE" in head:
        return [], LATER_KINDS["FACADE"]
    if re.match(r"^[^-]+-ROOF-", head):
        return [(("ROOF", head), "PRIMARY")], None
    if head.endswith("-EXT") and OPENING_KEY.match(suffix):
        return [(("OPEN", floor, suffix), "PRIMARY")], None
    if head in rooms:
        host = ("ROOM", head)
        op = OPENING_KEY.match(suffix)
        if op:
            return [(("OPEN", floor, suffix), "PRIMARY"), (host, "HOST")], None
        if suffix.startswith("flight "):
            return [(("FLIGHT", head, suffix), "PRIMARY"), (host, "HOST")], None
        if suffix == "landings":
            return [(("LANDING", head), "PRIMARY"), (host, "HOST")], None
        if code.startswith("FIN.WP."):
            out = [(("ZONE", head), "PRIMARY"), (host, "HOST")]
            for o in re.findall(r"(?:^|[ :])(C?OP-\d+|DOOR-[^ :]+)$", suffix):
                k = door_to.get(o) if o.startswith("DOOR-") else ("OPEN", floor, o)
                if k:
                    out.append((k, "MEMBER"))
            return out, None
        return [(host, "PRIMARY")], None
    return [], f"element key {head!r} names no room, opening, wall, roof zone or structural element"


def _q(ln):
    br = ln.get("bounded_range") or {}
    return {"measured_net": ln.get("measured_net"), "low": br.get("low"), "high": br.get("high"), "unit": ln["unit"],
            "evidence_state": ln["evidence_state"]}


def build(lines, sources, project=None):
    """lines: the run's BOQ lines (V3_0_BOQ_LINES.json); sources: {"rooms", "walls", "openings", "curved", "doors",
    "membrane", "unit_m", "arch_rev"} as parsed from the run's files (missing pieces may be empty)."""
    arch_lines = [ln for ln in lines if not ln["item_code"].startswith("STR.")]
    revs = Counter(ln["project"]["revision_set_sha256"][:12] for ln in arch_lines)
    arch_rev = sources.get("arch_rev") or (revs.most_common(1)[0][0] if revs else "norev")
    project = project or (arch_lines[0]["project"]["project_id"] if arch_lines else "project")
    unit_m = float(sources.get("unit_m") or 0.001)
    reg = _Reg(project)
    reg.by_key_pending_or_done = lambda: {k for k in reg.by_key} | {it[1] for v in reg.pending.values() for it in v}
    rooms = {r["room_id"]: r for r in sources.get("rooms") or []}
    _room_records(reg, rooms.values(), arch_rev, unit_m)
    _wall_records(reg, sources.get("walls") or [], arch_rev, unit_m)
    door_to = _opening_records(reg, sources.get("openings") or [], sources.get("curved") or [],
                               sources.get("doors") or [], arch_rev, unit_m)
    for p in sources.get("membrane") or []:
        rid = p["room_id"]
        if rid in rooms:
            reg.add(("ZONE", rid), arch_rev, p["floor"], "ZONE-WP", None, None,
                    {"status": "CALCULATED" if p.get("state") == "COMPUTED" else "HELD", "host_room_key": rid,
                     "status_basis": f"membrane piece plan state {p.get('state')}",
                     "evidence": {"file": "MEMBRANE_PIECE_PLAN.json", "room_id": rid, "rolls": (p.get("balance") or {})
                                  .get("rolls")}},
                    geom_local=None, engine_local="WP" + _h(rid))
    # elements that exist only through the lines' own keys (structural members, flights, landings, roof zones)
    pending_lines = []
    # concrete lines first: an element's status comes from its own concrete line, never from its steel
    for ln in sorted(lines, key=lambda x: x["item_code"] == "STR.REBAR"):
        code, loc = ln["item_code"], ln["location"]
        eid = loc.get("element_id") or ""
        rev = ln["project"]["revision_set_sha256"][:12]
        if code.startswith("STR."):
            s = _structural(code, eid)
            if not (s[0] and s[0] in KINDS):
                continue
            own = code != "STR.REBAR"
            if s[1] in reg.by_key_pending_or_done():
                if own:
                    pending_lines.append((s[1], ln))   # a second concrete line of the same element: weakest governs
                continue
            conflict = sorted(c for c in ln["rule"].get("conventions_used") or [] if "CONFLICT" in c) if own else []
            st = LINE_STATUS[ln["evidence_state"]] if own else "HELD"
            reg.add(s[1], rev, _floor(s[4]), s[0], s[2], s[3],
                    {"status": "CONFLICT" if conflict and st != "HELD" else st, "conflicts": conflict,
                     "status_basis": (f"own concrete line {ln['evidence_state']}"
                                      + (f"; the line settles a declared conflict by convention ({', '.join(conflict)})"
                                         if conflict else "")) if own
                     else "only steel lines read this element: no concrete line states its geometry",
                     "evidence": {"engine_storey": s[4], "route_g_key": ":".join(map(str, s[1][1:])),
                                  "documents": [d.get("file") for d in ln["source"]["documents"]]}},
                    engine_local="E" + _h(s[1]))
            continue
        head, _, suffix = eid.partition(":")
        if head in rooms and (suffix.startswith("flight ") or suffix == "landings"):
            key = ("FLIGHT", head, suffix) if suffix != "landings" else ("LANDING", head)
            if key not in reg.by_key_pending_or_done():
                host = rooms[head]
                kind = "STAIR-FLIGHT" if key[0] == "FLIGHT" else "LANDING"
                hl = "+".join(sorted(set(host.get("codes") or []))) or "R" + _h(head, 6)
                lab = f"{hl}.{suffix.replace('flight ', 'F')}" if kind == "STAIR-FLIGHT" else f"{hl}.LANDING"
                reg.add(key, arch_rev, host["floor"], kind, None, None,
                        {"status": "CALCULATED", "status_basis": "drawn inside its room (ARCH_ROOMS symbols_inside)",
                         "host_room_key": head, "evidence": {"file": "ARCH_ROOMS.json", "room_id": head,
                                                             "piece": suffix}},
                        geom_local=None, engine_local=_safe(lab) + "~" + _h(head, 4))
        elif re.match(r"^[^-]+-ROOF-", head) and ("ROOF", head) not in reg.by_key_pending_or_done():
            inp = ln["calculation"].get("inputs") or {}
            reg.add(("ROOF", head), arch_rev, loc.get("floor"), "ZONE-WP", inp.get("label"), (0, 0),
                    {"status": "HELD" if ln["evidence_state"] not in QUANTITY_STATES else "CALCULATED",
                     "status_basis": f"roof zone line {ln['evidence_state']}",
                     "evidence": {"region": inp.get("region"), "layer": inp.get("layer"), "zone_key": head}},
                    engine_local="E" + _h(head))
    reg.finish()
    for key, ln in pending_lines:                     # weakest concrete line governs a structural element's status
        e = reg.el[reg.by_key[key]]
        st = LINE_STATUS[ln["evidence_state"]]
        if WEAKNESS[st] > WEAKNESS[e["status"]]:
            e["status"], e["status_basis"] = st, f"weakest own concrete line {ln['evidence_state']}"
    walls_by_ft = defaultdict(list)
    for k, e in reg.el.items():
        if e["kind"] == "WALL":
            walls_by_ft[(e["floor"], e["t_mm"])].append(e["engine_key"])
    unlinked, links = [], 0
    for ln in lines:
        targets, why = _link_targets(ln, reg, rooms, door_to, walls_by_ft)
        ok = [(reg.by_key[k], role) for k, role in targets if k in reg.by_key]
        if not ok:
            unlinked.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"]["floor"],
                             "element_key": ln["location"]["element_id"], "unit": ln["unit"],
                             "evidence_state": ln["evidence_state"],
                             "reason": why or "the element it names is not in the register sources"})
            continue
        for eid, role in ok:
            reg.el[eid]["boq_lines"].append(dict(_q(ln), line_id=ln["line_id"], item_code=ln["item_code"], role=role,
                                                 line_element_key=ln["location"]["element_id"]))
            links += 1
    els = sorted(reg.el.values(), key=lambda e: e["id"])
    for e in els:
        e["boq_lines"].sort(key=lambda b: (b["item_code"], b["line_id"]))
        if e["kind"] == "WALL":
            e["share_lm"] = e.get("net_lm")       # its own net run inside an aggregate ARCH.WALL_RUN line
    out = {"schema": SCHEMA, "project": reg.project, "revisions": {"architectural": arch_rev,
                                                                  "all": sorted({ln["project"]["revision_set_sha256"][:12]
                                                                                 for ln in lines})},
           "elements": els, "unlinked_lines": sorted(unlinked, key=lambda u: (u["item_code"], u["line_id"])),
           "lines": len(lines), "links": links}
    out["checks"] = checks(out)
    out["summary"] = summary(out)
    return out


# ------------------------------------------------------------------------------------------------------------- checks

def checks(register):
    els = register["elements"]
    dbl_fin, dbl_conc, held, dup, conf = [], [], [], [], []
    for e in els:
        prim = [b for b in e["boq_lines"] if b["role"] == "PRIMARY"]
        fin = sorted({b["item_code"] for b in prim if b["item_code"] in FLOOR_FINISH})
        if len(fin) > 1:
            dbl_fin.append({"element": e["id"], "items": fin, "lines": sorted(b["line_id"] for b in prim
                                                                              if b["item_code"] in FLOOR_FINISH)})
        conc = sorted({b["item_code"] for b in prim if b["item_code"].startswith(CONCRETE_PREFIX)})
        if len(conc) > 1 and not (e["kind"] == "COL" and set(conc) <= {"STR.CONC.COLUMN", "STR.CONC.NECK"}):
            dbl_conc.append({"element": e["id"], "items": conc})
        if e["status"] in ("HELD", "NOT_APPLICABLE"):
            for b in e["boq_lines"]:
                if b["role"] != "HOST" and b["evidence_state"] in QUANTITY_STATES:
                    held.append({"element": e["id"], "element_status": e["status"], "line_id": b["line_id"],
                                 "item_code": b["item_code"], "role": b["role"], "line_state": b["evidence_state"],
                                 "quantity": b["measured_net"], "unit": b["unit"]})
        if e["status"] == "CONFLICT":                  # two drawn sources disagree; the line chose one by convention
            conf += [{"element": e["id"], "conflicts": e.get("conflicts"), "line_id": b["line_id"],
                      "item_code": b["item_code"], "line_state": b["evidence_state"], "quantity": b["measured_net"],
                      "unit": b["unit"]} for b in prim if b["evidence_state"] in QUANTITY_STATES]
        seen = Counter((b["item_code"], b["unit"], b["line_element_key"]) for b in prim)
        dup += [{"element": e["id"], "item_code": k[0], "unit": k[1], "line_element_key": k[2], "lines": n}
                for k, n in sorted(seen.items()) if n > 1]
    idle = [{"element": e["id"], "kind": e["kind"], "status": e["status"], "evidence": e.get("evidence")}
            for e in els if not e["boq_lines"]]           # drawn, but no BOQ line takes a quantity from it
    return {"double_finish": dbl_fin, "double_concrete": dbl_conc, "held_released": held, "duplicate_lines": dup,
            "elements_without_lines": idle, "conflict_released": conf,
            "unlinked": len(register["unlinked_lines"]),
            "all_lines_accounted": register["lines"] == len({b["line_id"] for e in els for b in e["boq_lines"]})
            + len(register["unlinked_lines"])}


def summary(register):
    per = defaultdict(Counter)
    for e in register["elements"]:
        per[e["kind"]][e["status"]] += 1
        per[e["kind"]]["_total"] += 1
        per[e["kind"]]["_linked"] += 1 if e["boq_lines"] else 0
    unl = Counter((u["item_code"], u["reason"]) for u in register["unlinked_lines"])
    return {"per_kind": {k: dict(v) for k, v in sorted(per.items())},
            "unlinked_by_reason": [{"item_code": k[0], "reason": k[1], "lines": n} for k, n in sorted(unl.items())]}


# --------------------------------------------------------------------------------------------------- revision mapping

def _shape(e):
    from shapely.geometry import LineString, Polygon
    if e.get("outline_mm") and len(e["outline_mm"]) >= 3:
        p = Polygon(e["outline_mm"])
        return p if p.is_valid else p.buffer(0)
    if e.get("axis_mm") and len(e["axis_mm"]) >= 2 and e.get("t_mm"):
        return LineString(e["axis_mm"]).buffer(e["t_mm"] / 2.0, cap_style=2)
    if e.get("centre_mm") and e.get("width_mm"):
        from shapely.geometry import Point
        return Point(e["centre_mm"]).buffer(e["width_mm"] / 2.0)
    return None


def map_revisions(old, new):
    """-> {"mapping": [{old, new, how}], "new": [...], "removed": [...]}. how: SAME_LOCAL (local id unchanged),
    LABEL (same printed label, other repeat suffix), OVERLAP (outline / wall strip overlap >= 95 % of the larger)."""
    o_els = {e["id"]: e for e in old["elements"]}
    n_els = {e["id"]: e for e in new["elements"]}
    key = lambda e: (e["floor"], e["kind"])
    used, mapping = set(), []
    n_by_local = {(key(e), e["local"]): i for i, e in n_els.items()}
    for i, e in sorted(o_els.items()):
        j = n_by_local.get((key(e), e["local"]))
        if j and j not in used:
            mapping.append({"old": i, "new": j, "how": "SAME_LOCAL"})
            used.add(j)
    done = {m["old"] for m in mapping}
    for i, e in sorted(o_els.items()):
        if i in done or not e.get("label"):
            continue
        cand = [j for j, f in n_els.items() if j not in used and key(f) == key(e) and f.get("label") == e["label"]]
        if len(cand) == 1:
            mapping.append({"old": i, "new": cand[0], "how": "LABEL"})
            used.add(cand[0])
            done.add(i)
    for i, e in sorted(o_els.items()):
        if i in done:
            continue
        a = _shape(e)
        best = None
        for j, f in n_els.items():
            if j in used or key(f) != key(e):
                continue
            b = _shape(f)
            if a is None or b is None or a.area <= 0 or b.area <= 0:
                continue
            r = a.intersection(b).area / max(a.area, b.area)
            if r >= OVERLAP_MIN and (best is None or r > best[0]):
                best = (r, j)
        if best:
            mapping.append({"old": i, "new": best[1], "how": "OVERLAP", "overlap": round(best[0], 4)})
            used.add(best[1])
            done.add(i)
    return {"mapping": sorted(mapping, key=lambda m: m["old"]), "removed": sorted(set(o_els) - done),
            "new": sorted(set(n_els) - used)}


# ---------------------------------------------------------------------------------------------------------- run files

def _load(p, *path, default=None):
    if not p.exists():
        return default
    d = json.loads(p.read_text(encoding="utf-8"))
    for k in path:
        d = d.get(k) if isinstance(d, dict) else None
        if d is None:
            return default
    return d


def load_run(run_dir, lines_file=None):
    """-> (lines, sources, lines file) of a run folder; nothing is written."""
    run = Path(run_dir)
    lf = Path(lines_file) if lines_file else (run / "V3_0_BOQ_LINES.json" if (run / "V3_0_BOQ_LINES.json").exists()
                                              else run / "BOQ_LINES.json")
    lines = json.loads(lf.read_text(encoding="utf-8"))
    rooms_run = _load(run / "ARCH_ROOMS.json", "run", default={}) or {}
    src = {"rooms": _load(run / "ARCH_ROOMS.json", "rooms", default=[]),
           "walls": _load(run / "ARCH_WALLS.json", "floors", default=[]),
           "openings": _load(run / "ARCH_OPENINGS.json", "openings", default=[]),
           "curved": _load(run / "CURVED_OPENINGS.json", "curved_openings", default=[]),
           "doors": _load(run / "DOOR_SCHEDULE.json", "doors", "elements", default=[]),
           "membrane": _load(run / "MEMBRANE_PIECE_PLAN.json", "piece_plans", default=[]),
           "unit_m": rooms_run.get("unit_m"),
           "arch_rev": (rooms_run.get("revision_set_sha256") or "")[:12] or None}
    return lines, src, lf


def build_dir(run_dir, lines_file=None, project=None):
    lines, src, lf = load_run(run_dir, lines_file)
    reg = build(lines, src, project=project)
    reg["lines_file"] = lf.name
    return reg


CSV_COLUMNS = ("element_id", "kind", "floor", "label", "label_basis", "status", "line_id", "item_code", "role", "unit",
               "measured_net", "low", "high", "evidence_state")


def to_csv(register):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for e in register["elements"]:
        for b in e["boq_lines"] or [{}]:
            w.writerow({"element_id": e["id"], "kind": e["kind"], "floor": e["floor"], "label": e.get("label"),
                        "label_basis": e["label_basis"], "status": e["status"], **{k: b.get(k) for k in CSV_COLUMNS[6:]}})
    return buf.getvalue()


def write(run_dir, register):
    run = Path(run_dir)
    (run / "ELEMENT_REGISTER_V0.json").write_text(json.dumps(register, indent=1, sort_keys=True, ensure_ascii=False)
                                                  + "\n", encoding="utf-8")
    (run / "ELEMENT_REGISTER_V0.csv").write_text(to_csv(register), encoding="utf-8")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="element register v0 beside a run's outputs (reads only)")
    ap.add_argument("run_dir")
    ap.add_argument("--lines", help="lines file (default V3_0_BOQ_LINES.json, else BOQ_LINES.json)")
    ap.add_argument("--project")
    a = ap.parse_args(argv)
    reg = build_dir(a.run_dir, a.lines, a.project)
    write(a.run_dir, reg)
    print(json.dumps({"summary": reg["summary"]["per_kind"], "checks": {k: (v if isinstance(v, (int, bool)) else len(v))
                                                                         for k, v in reg["checks"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
