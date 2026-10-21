"""Phase 2B-9 test helpers: the architectural CLI under ARCH_TAKEOFF_V2.8 (V2.7.1 for before / after) on the
p2b9_fixtures drawings, and readers of its outputs. No facts by default: every height comes from the drawing's own
evidence (or is reported missing); FACTS (tests/m9_p2b6) is the synthetic 2.10 / 1.50 m S2 facts template, used only
to show what V2.7.1 did with it."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b7"))
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))

import p2b7_run as R7                                         # noqa: E402

V271, V28 = "ARCH_TAKEOFF_V2.7.1", "ARCH_TAKEOFF_V2.8"
FACTS = R7.FACTS
load, lines, rooms, totals, openings, unresolved = R7.load, R7.lines, R7.rooms, R7.totals, R7.openings, R7.unresolved


def run(dxf, out, *, roles=None, facts=False, method=V28, units=None):
    """units: the reviewer's --units confirmation (recorded by the admission), e.g. for a metres drawing whose only
    closed rectangles are its sheet frames (the member-size fit then contradicts the declared unit)."""
    if units is None:
        return R7.run(dxf, out, roles=roles, facts=facts, method=method)
    import json
    import subprocess
    import p2b6_run as R6
    argv = [sys.executable, "-I", str(R6.CLI), "arch", "--drawings", str(dxf), "--out", str(out), "--method", method,
            "--units", units]
    if facts:
        fp = Path(out).parent / "facts.json"
        fp.write_text(json.dumps(FACTS), encoding="utf-8")
        argv += ["--facts", str(fp)]
    if roles:
        argv += ["--layer-roles", *roles]
    r = subprocess.run(argv, capture_output=True, text=True, cwd=str(Path(out).parent))
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return Path(out)


def the(out, item_code, element=None, room_name=None):
    """the one line of item_code (whose element is, or else starts with, element; in the room named room_name)."""
    got = [ln for ln in lines(out) if ln["item_code"] == item_code and
           (element is None or ln["physical_element"].startswith(element)) and
           (room_name is None or (ln.get("location") or {}).get("room_name_en") == room_name)]
    if element is not None and len(got) > 1:
        got = [ln for ln in got if ln["physical_element"] == element] or got
    assert len(got) == 1, [(ln["item_code"], ln["physical_element"], ln["measured_net"]) for ln in got]
    return got[0]


def all_of(out, item_code, element=None):
    return [ln for ln in lines(out) if ln["item_code"] == item_code and
            (element is None or ln["physical_element"].startswith(element))]


def net(out, item_code, element=None, room_name=None):
    return the(out, item_code, element, room_name)["measured_net"]


def opening_schedule(out):
    return load(out, "OPENING_SCHEDULE.json")["openings"]


def opening(out, kind):
    got = [o for o in opening_schedule(out) if o["kind"] == kind]
    assert len(got) == 1, got
    return got[0]


def height_evidence(out):
    return load(out, "HEIGHT_EVIDENCE.json")


def missing(out):
    return load(out, "MISSING_HEIGHT_EVIDENCE.json")["missing"]


def reveals(out):
    return load(out, "WINDOW_REVEALS.json")["reveals"]


def wall_geometry(out):
    return load(out, "WALL_GEOMETRY.json")


def room_heights(out, name="Bedroom"):
    got = [r for r in height_evidence(out)["rooms"] if r["name_en"] == name]
    assert len(got) == 1, got
    return got[0]["heights"]
