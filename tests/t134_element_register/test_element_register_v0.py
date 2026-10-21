"""T-134: element register v0 (engine.source.element_register_v0) on a synthetic two-storey villa (not a client
drawing). Hand expectations:

ARCHITECTURAL (rev A = "a1" * 32; drawing units mm, unit_m 0.001)
  GF rooms: BEDROOM 4.00 x 3.00 at x 0..4 and BEDROOM 3.00 x 3.00 at x 4.2..7.2 (printed twice; the engine ids run east to west -> BEDROOM.1 west,
  BEDROOM.2 east, ordered by x), STAIR 2.40 x 4.00 with flight 1 and a landing; an unlabelled store (no text) ->
  local G<hash of its outline>. 1F: LIVING 6.00 x 5.00 with a landing that the engine feeds BOTH to marble
  (FIN.MARBLE.LANDING) and to porcelain (FIN.FLOOR.PORCELAIN, same landing key) -> one double-finish flag (Q-66 B).
  Walls GF: W1 (0,0)->(7200,0) t 0.20, W2 (0,0)->(0,3000) t 0.20, W3 (4100,0)->(4100,3000) t 0.15. The two
  ARCH.WALL_RUN lines (t 0.20 = 10.20 lm, t 0.15 = 3.00 lm) link to 2 and 1 walls; the walls' own net runs add to them.
  Openings GF: OP-001 door 0.90 m (CALCULATED); OP-002 window with no measured width -> HELD; its ARCH.WINDOW count
  line is released (PROVISIONAL 1 pcs) -> one held_released finding.
STRUCTURAL (rev B = "b2" * 32): footings F1 @ (12000,1000) and F1 @ (2000,1000) -> F1.1 (x 2000), F1.2 (x 12000): numeric, not text order; F2
  single, printed with two types (the line declares FOOTING_LABEL_CONFLICT and takes one by convention) -> CONFLICT,
  listed once in conflict_released (1.2 m3). Column C1 GF: concrete BOUNDED (height not printed) -> HELD; its steel line PROVISIONAL 40.0 kg -> one
  held_released finding (steel released on a held column). Strap BAND0001 released 0.800 m3 + its V3.0 piece
  BAND0001:IN_OPEN_FOOTING_OUTLINE held 0..0.200 m3 -> two elements, no finding. Blinding (aggregate) -> member of
  all 3 footings.
UNLINKED: one facade line (later kind) and one line naming nothing -> 2 unlinked, each with its reason; every line
  is linked or unlinked (none lost).
REVISION 2: W3 moved 20 mm east (strip overlap 130 / 150 = 0.867 < 0.95 -> NEW + REMOVED) and in a second case 5 mm
  (overlap 145 / 150 = 0.967 >= 0.95 -> OVERLAP); every other element keeps its local id (SAME_LOCAL).
Mirror (x -> -x), a quarter turn and metres (unit_m 1.0): the same counts, statuses and findings; metres give the same
local ids as mm.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL  # noqa: E402
from engine.source import element_register_v0 as E  # noqa: E402

REV_A, REV_B = "a1" * 32, "b2" * 32
PID = "synthetic-villa-t134"


def line(code, unit, element_id, *, floor=None, room_id=None, ev="PROVISIONAL", net=1.0, rng=None, rev=REV_A,
         inputs=None, conv=()):
    kw = {}
    if ev == "BOUNDED_EXPOSURE":
        kw = {"bounded_range": {"low": rng[0], "high": rng[1], "basis": "test"}, "rfi": {"question": "height?"}}
        net = None
    if ev == "BLOCKED_RFI":
        kw = {"rfi": {"question": "?"}}
        net = None
    return BL.make_line(project_id=PID, revision_set_sha256=rev, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=element_id, floor=floor, room_id=room_id, formula="test",
                        inputs=inputs, rule_id="T134", rule_version="test", conventions_used=conv, item_en=code, item_ar=code,
                        trade=None if code in BL.ITEMS else "OTHER", **kw)


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def room(rid, floor, codes, poly_m, kind="DRY"):
    return {"room_id": rid, "floor": floor, "codes": codes, "label_source": "TEXT" if codes else None,
            "polygon_m": poly_m, "kind": kind, "face_id": "SITE-" + rid, "region_id": "SHX:" + floor, "area_m2": 1.0}


def villa(t=lambda x, y: (x, y), unit_m=0.001):
    """sources + lines; t maps a point in metres (mirror / rotation); drawing units = metres / unit_m."""
    def P(x, y):
        return list(t(x, y))

    def poly(x0, y0, x1, y1):
        return [P(*p) for p in rect(x0, y0, x1, y1)]

    def D(x, y):                                   # drawing units
        a, b = t(x, y)
        return [a / unit_m, b / unit_m]
    rooms = [room("GF-RB", "GF", ["BEDROOM"], poly(0, 0, 4, 3)), room("GF-RA", "GF", ["BEDROOM"], poly(4.2, 0, 7.2, 3)),
             room("GF-RS", "GF", ["STAIR"], poly(0, 3.2, 2.4, 7.2), kind="STAIR"),
             room("GF-RU", "GF", [], poly(2.6, 3.2, 4.0, 4.6)),
             room("1F-RL", "1F", ["LIVING"], poly(0, 0, 6, 5))]
    walls = [{"floor": "GF", "walls": [
        {"wall_id": "WB-1", "centreline": [D(0, 0), D(7.2, 0)], "t_m": 0.20, "net_lm": 7.20, "family": "0.20",
         "layer": "A-WALL", "source_ids": ["H1"]},
        {"wall_id": "WB-2", "centreline": [D(0, 0), D(0, 3.0)], "t_m": 0.20, "net_lm": 3.00, "family": "0.20",
         "layer": "A-WALL", "source_ids": ["H2"]},
        {"wall_id": "WB-3", "centreline": [D(4.1, 0), D(4.1, 3.0)], "t_m": 0.15, "net_lm": 3.00, "family": "0.15",
         "layer": "A-WALL", "source_ids": ["H3"]}]}]
    openings = [{"opening_id": "OP-001", "floor": "GF", "kind": "DOOR", "width_m": 0.90, "height_state": "ASSUMED",
                 "position": {"centre_m": P(2.0, 0.0)}, "host_wall": "WB-1", "rooms": ["GF-RB"], "status": "OK"},
                {"opening_id": "OP-002", "floor": "GF", "kind": "WINDOW", "width_m": None,
                 "height_state": "NOT_ESTABLISHED", "position": {"centre_m": P(6.0, 0.0)}, "host_wall": "WB-1",
                 "rooms": ["GF-RA"], "status": "WIDTH_NOT_MEASURED"}]
    doors = [{"element_id": "DOOR-GF-d1", "floor": "GF", "state": "CONFIRMED", "centre": D(2.0, 0.0),
              "evidence": [{"id": "EV-OP-001-BAND"}, {"id": "EV-H9-SWING"}]}]
    membrane = []
    src = {"rooms": rooms, "walls": walls, "openings": openings, "curved": [], "doors": doors, "membrane": membrane,
           "unit_m": unit_m, "arch_rev": REV_A[:12]}
    S = dict(rev=REV_B)
    lines = [
        line("FIN.FLOOR.PORCELAIN", "m2", "GF-RA:floor", floor="GF", room_id="GF-RA", net=12.0),
        line("FIN.FLOOR.PORCELAIN", "m2", "GF-RB:floor", floor="GF", room_id="GF-RB", net=9.0),
        line("FIN.MARBLE.TREAD", "m2", "GF-RS:flight 1", floor="GF", room_id="GF-RS", net=2.0),
        line("FIN.MARBLE.LANDING", "m2", "GF-RS:landings", floor="GF", room_id="GF-RS", net=2.4),
        line("FIN.FLOOR.PORCELAIN", "m2", "1F-RL:floor", floor="1F", room_id="1F-RL", net=25.0),
        line("FIN.MARBLE.LANDING", "m2", "1F-RL:landings", floor="1F", room_id="1F-RL", net=2.4),
        line("FIN.FLOOR.PORCELAIN", "m2", "1F-RL:landings", floor="1F", room_id="1F-RL", net=2.4),
        line("FIN.PLASTER", "m2", "GF-RU:plaster", floor="GF", room_id="GF-RU", net=15.0),
        line("ARCH.WALL_RUN", "lm", "GF-WALLS:walls t=0.20", floor="GF", room_id="GF-WALLS", net=10.20),
        line("ARCH.WALL_RUN", "lm", "GF-WALLS:walls t=0.15", floor="GF", room_id="GF-WALLS", net=3.00),
        line("DOOR.INTERNAL.PVC", "pcs", "DOOR-GF-d1", floor="GF", room_id="GF-RA", net=1),
        line("ARCH.WINDOW", "pcs", "GF-RA:OP-002", floor="GF", room_id="GF-RA", net=1),
        line("ARCH.WINDOW_REVEAL", "m2", "GF-STRIP-OP-002:window reveal strip", floor="GF", ev="BLOCKED_RFI"),
        line("ARCH.FACADE", "m2", "GF-FACADE:facade", floor="GF", room_id="GF-FACADE", net=80.0),
        line("ARCH.SPACE", "m2", "XX-NOWHERE:space", floor="GF", net=3.0),
        line("STR.CONC.FOOTING", "m3", "P-C:FTG:SH1:F1@12000,1000:aa", floor="FOUNDATION", net=0.9, **S),
        line("STR.CONC.FOOTING", "m3", "P-C:FTG:SH1:F1@2000,1000:bb", floor="FOUNDATION", net=0.9, **S),
        line("STR.CONC.FOOTING", "m3", "P-C:FTG:SH1:F2@9000,1000:cc", floor="FOUNDATION", net=1.2,
             conv=("FOOTING_LABEL_CONFLICT",), **S),
        line("STR.CONC.BLINDING", "m3", "U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS", floor="FOUNDATION",
             net=0.5, **S),
        line("STR.CONC.COLUMN", "m3", "U-C:COL:SH2:C1@1000,1000|GF", floor="GF", ev="BOUNDED_EXPOSURE",
             rng=(0.3, 0.5), **S),
        line("STR.REBAR", "kg", "U-S:COL:SH2:C1@1000,1000|GF:D16", floor="GF", net=40.0, **S),
        line("STR.CONC.STRAP", "m3", "P-C:GROUND_BEAMS:FOUNDATION:BAND0001", floor="FOUNDATION", net=0.8, **S),
        line("STR.CONC.STRAP", "m3", "P-C:GROUND_BEAMS:FOUNDATION:BAND0001:IN_OPEN_FOOTING_OUTLINE",
             floor="FOUNDATION", ev="BOUNDED_EXPOSURE", rng=(0.0, 0.2), **S),
    ]
    return lines, src


def reg_of(**kw):
    lines, src = villa(**kw)
    return E.build(lines, src, project=PID), lines


def by_local(reg):
    return {(e["floor"], e["kind"], e["local"]): e for e in reg["elements"]}


def test_ids_labels_repeats_and_hash():
    reg, _ = reg_of()
    L = by_local(reg)
    w, e = L[("GF", "ROOM", "BEDROOM.1")], L[("GF", "ROOM", "BEDROOM.2")]
    assert w["evidence"]["room_id"] == "GF-RB" and e["evidence"]["room_id"] == "GF-RA"   # by x, not by engine id
    assert w["id"] == f"{PID}/{REV_A[:12]}/GF/ROOM/BEDROOM.1"
    store = [x for x in reg["elements"] if x["kind"] == "ROOM" and x["evidence"]["room_id"] == "GF-RU"][0]
    assert store["label_basis"] == "GEOMETRY_HASH_1MM" and store["local"].startswith("G")
    f11, f12 = L[("FDN", "FTG", "F1.1")], L[("FDN", "FTG", "F1.2")]
    assert "F1@2000,1000" in f11["evidence"]["route_g_key"] and "F1@12000" in f12["evidence"]["route_g_key"]
    assert ("FDN", "FTG", "F2") in L and f11["rev"] == REV_B[:12]
    assert {x["kind"] for x in reg["elements"]} >= {"ROOM", "WALL", "OPEN", "STAIR-FLIGHT", "LANDING", "FTG", "COL",
                                                     "STRAP"}
    assert all(x["status"] in E.STATUSES for x in reg["elements"])
    assert all(x["status"] != "VERIFIED" for x in reg["elements"])        # never set without the verifier


def test_links_roles_and_wall_shares():
    reg, lines = reg_of()
    L = by_local(reg)
    walls = [x for x in reg["elements"] if x["kind"] == "WALL"]
    t20 = [x for x in walls if x["t_mm"] == 200]
    assert len(t20) == 2 and abs(sum(x["share_lm"] for x in t20) - 10.20) < 1e-9
    assert all(b["role"] == "MEMBER" for x in walls for b in x["boq_lines"])
    door = [x for x in reg["elements"] if x["kind"] == "OPEN" and x["evidence"].get("opening_id") == "OP-001"][0]
    assert [b["item_code"] for b in door["boq_lines"]] == ["DOOR.INTERNAL.PVC"]    # assembly -> its opening
    for f in ("F1.1", "F1.2", "F2"):
        assert any(b["item_code"] == "STR.CONC.BLINDING" and b["role"] == "MEMBER"
                   for b in L[("FDN", "FTG", f)]["boq_lines"])
    col = [x for x in reg["elements"] if x["kind"] == "COL"][0]
    assert col["status"] == "HELD" and {b["item_code"] for b in col["boq_lines"]} == {"STR.CONC.COLUMN", "STR.REBAR"}
    straps = [x for x in reg["elements"] if x["kind"] == "STRAP"]
    assert sorted(x["status"] for x in straps) == ["HELD", "PROVISIONAL"]    # the held piece stays its own element
    assert reg["checks"]["all_lines_accounted"]


def test_checks_find_exactly_the_planted_defects():
    reg, _ = reg_of()
    c = reg["checks"]
    assert len(c["double_finish"]) == 1
    assert c["double_finish"][0]["items"] == ["FIN.FLOOR.PORCELAIN", "FIN.MARBLE.LANDING"]
    assert "/1F/LANDING/" in c["double_finish"][0]["element"]
    held = sorted((h["item_code"], h["line_state"]) for h in c["held_released"])
    assert held == [("ARCH.WINDOW", "PROVISIONAL"), ("STR.REBAR", "PROVISIONAL")]
    assert c["double_concrete"] == [] and c["duplicate_lines"] == []
    assert [(x["item_code"], x["quantity"], x["conflicts"]) for x in c["conflict_released"]] == \
        [("STR.CONC.FOOTING", 1.2, ["FOOTING_LABEL_CONFLICT"])]
    assert by_local(reg)[("FDN", "FTG", "F2")]["status"] == "CONFLICT"
    reasons = sorted(u["reason"] for u in reg["unlinked_lines"])
    assert len(reasons) == 2 and "later kind" in reasons[0] + reasons[1]
    assert all(u["reason"] for u in reg["unlinked_lines"])


def test_no_finding_without_a_defect():
    lines, src = villa()
    lines = [x for x in lines if not (x["item_code"] == "FIN.FLOOR.PORCELAIN" and "landings" in
                                      x["location"]["element_id"])]
    lines = [x for x in lines if x["item_code"] not in ("ARCH.WINDOW", "STR.REBAR")]
    reg = E.build(lines, src, project=PID)
    assert reg["checks"]["double_finish"] == [] and reg["checks"]["held_released"] == []


def test_duplicate_surface_is_flagged():
    lines, src = villa()
    lines.append(copy.deepcopy([x for x in lines if x["location"]["element_id"] == "GF-RA:floor"][0]))
    lines[-1]["line_id"] = "L-duplicate"
    reg = E.build(lines, src, project=PID)
    assert len(reg["checks"]["duplicate_lines"]) == 1


@pytest.mark.parametrize("name,t", [("mirror", lambda x, y: (-x, y)), ("quarter turn", lambda x, y: (-y, x))])
def test_mirror_and_rotation_keep_counts_and_findings(name, t):
    base, _ = reg_of()
    reg, _ = reg_of(t=t)
    assert reg["summary"]["per_kind"] == base["summary"]["per_kind"]
    for k in ("double_finish", "held_released", "duplicate_lines"):
        assert len(reg["checks"][k]) == len(base["checks"][k])
    assert reg["checks"]["unlinked"] == base["checks"]["unlinked"]


def test_metres_give_the_same_ids_as_mm():
    a, _ = reg_of()
    b, _ = reg_of(unit_m=1.0)
    assert [e["id"] for e in a["elements"]] == [e["id"] for e in b["elements"]]


def test_rerun_is_deterministic():
    a, _ = reg_of()
    b, _ = reg_of()
    assert a == b


def _moved_w3(dx_m):
    lines, src = villa()
    src = copy.deepcopy(src)
    w3 = src["walls"][0]["walls"][2]
    w3["centreline"] = [[(4.1 + dx_m) * 1000, 0.0], [(4.1 + dx_m) * 1000, 3000.0]]
    return E.build(lines, src, project=PID)


def test_revision_mapping_one_changed_wall():
    old, _ = reg_of()
    far = _moved_w3(0.020)                          # overlap 0.130 / 0.150 = 0.867 -> new wall
    m = E.map_revisions(old, far)
    assert len(m["new"]) == 1 and len(m["removed"]) == 1 and "/WALL/" in m["new"][0]
    assert all(x["how"] == "SAME_LOCAL" for x in m["mapping"])
    assert len(m["mapping"]) == len(old["elements"]) - 1
    near = _moved_w3(0.005)                         # overlap 0.145 / 0.150 = 0.967 -> remapped
    m2 = E.map_revisions(old, near)
    hows = [x for x in m2["mapping"] if x["how"] != "SAME_LOCAL"]
    assert m2["new"] == [] and m2["removed"] == [] and len(hows) == 1
    assert hows[0]["how"] == "OVERLAP" and abs(hows[0]["overlap"] - 0.145 / 0.150) < 1e-3


def test_new_revision_sha_keeps_local_ids():
    old, _ = reg_of()
    lines, src = villa()
    src = dict(src, arch_rev="c3" * 6)
    new = E.build(lines, src, project=PID)
    m = E.map_revisions(old, new)
    assert m["new"] == [] and m["removed"] == []
    moved = [x for x in m["mapping"] if x["old"] != x["new"]]
    assert moved and all("/" + "c3" * 6 + "/" in x["new"] for x in moved)


def test_writes_beside_the_run_and_reads_nothing_else(tmp_path):
    reg, _ = reg_of()
    E.write(tmp_path, reg)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["ELEMENT_REGISTER_V0.csv", "ELEMENT_REGISTER_V0.json"]
    rows = (tmp_path / "ELEMENT_REGISTER_V0.csv").read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("element_id,kind,floor") and len(rows) > len(reg["elements"])
