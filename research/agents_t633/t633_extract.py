"""T-633 drawing read (research, unwired): the masonry opening of every door / window behind the B9 blockwork
statement's opening rows (T-543/blockwork, scorecard V11 UNKNOWN rows), read independently from the architectural DXF.

Source (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded by the wrapper into
.work/private only; nothing of it is committed). Output: T633_DRAWN.json (metres and DXF entity handles; no coordinate,
no drawing text).

Method (every villa), re-using the read-only plan readers of research/agents_t627/t627_extract.py:
  door width   = gap between the wall-face line ends on BOTH faces of the wall at the door block (faces must agree);
  window width = distance between the two masonry jamb lines that cap the window symbol band;
  window height (printed) = an elevation DIMENSION bound to the opening (t627 PRINTED handles);
  rectangular part of the twin NW windows = the layer-1 jamb verticals of the NW elevation (their length), paired with
  the printed NW width chain segment (1552) that spans exactly the two jambs;
  1F straight-window census = every distinct jamb pair the symbol-group reader finds from any W-layer line of the
  1F plan frame.
Run: bash scripts/agent_env.sh run --tree task-T-633 research/agents_t633/t633_extract.py <P7757.dxf>
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t627"))
sys.path.insert(0, str(ROOT / "research" / "agents_t201"))
import t627_extract as X  # noqa: E402  (read only)

SCHEMA = "T633_DRAWN/1"
OUT = HERE / "T633_DRAWN.json"
# insert handle -> census id (research/agents_t581/t581_width_basis.py INSERT_TO_OPENING, read only)
DOORS = {"D-GF-03": ("GF", "1B5"), "D-GF-06": ("GF", "33E"), "D-GF-08": ("GF", "2C7"), "D-GF-09": ("GF", "3FF"),
         "D-GF-10": ("GF", "339"), "D-GF-13": ("GF", "2F2"),
         "D-1F-02": ("1F", "C31"), "D-1F-03": ("1F", "C32"), "D-1F-04": ("1F", "C2E"), "D-1F-07": ("1F", "BEE"),
         "D-1F-08": ("1F", "C18"), "D-1F-09": ("1F", "BEF"), "D-1F-10": ("1F", "C12")}
WINDOWS = {k: X.WINDOW_SYMBOL[k] for k in ("W13", "W14", "W15", "W16", "W18", "W24", "W25")}
# NW elevation twin windows: (jamb a, jamb b, printed width chain segment spanning exactly a..b)
NW_TWIN = {"pair_east": ("2566", "256A", "2E22"), "pair_west": ("2889", "288A", "2DE7")}


def _v(doc, h):
    e = doc.entitydb[h]
    s, t = e.dxf.start, e.dxf.end
    if abs(s.x - t.x) > 1:
        raise ValueError(f"{h}: not a vertical jamb line")
    return s.x, min(s.y, t.y), abs(s.y - t.y)


def nw_twin(doc):
    out = {}
    for key, (a, b, dim) in NW_TWIN.items():
        xa, ya, la = _v(doc, a)
        xb, yb, lb = _v(doc, b)
        d = doc.entitydb[dim]
        k = sorted((d.dxf.defpoint2.x, d.dxf.defpoint3.x))
        if abs(ya - yb) > 1 or abs(la - lb) > 1:
            raise ValueError(f"{key}: jambs differ")
        if abs(k[0] - min(xa, xb)) > 5 or abs(k[1] - max(xa, xb)) > 5:
            raise ValueError(f"{key}: width chain does not span the jambs")
        out[key] = {"jamb_handles": [a, b], "jamb_height": X.q3(la / 1000), "width": X.q3(abs(xb - xa) / 1000),
                    "width_dim": dim, "width_shown": X.shown(d), "width_measured": X.q3(d.get_measurement() / 1000)}
    return out


def window_census(doc, msp, frame):
    """every straight window of a plan frame: each W-layer line seeds the t627 symbol-group reader; distinct jamb
    pairs are distinct openings (a curved-on-plan opening has no straight group and is not in this census)."""
    seen = {}
    for e in msp.query("LINE[layer=='W']"):
        if not (frame[0] < e.dxf.start.x < frame[1]):
            continue
        try:
            r = X.window_plan(doc, msp, e.dxf.handle)
        except (ValueError, KeyError):
            continue
        seen.setdefault(tuple(r["jamb_handles"]), r["width"])
    return sorted(({"jamb_handles": list(k), "width": w} for k, w in seen.items()),
                  key=lambda r: (r["width"], r["jamb_handles"]))


def read(dxf_path):
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    if doc.header.get("$INSUNITS") != 4:
        raise ValueError("drawing units are not mm")
    msp = doc.modelspace()
    plan = {}
    for oid, (fl, h) in DOORS.items():
        d = X.door_plan(doc, msp, h)
        plan[oid] = {"floor": fl, "kind": "DOOR", **{k: v for k, v in d.items() if not k.startswith("_")}}
    for oid, (fl, h) in WINDOWS.items():
        w = X.window_plan(doc, msp, h)
        plan[oid] = {"floor": fl, "kind": "WINDOW", **{k: v for k, v in w.items() if not k.startswith("_")}}
    pr, _ = X.printed(doc)
    return {"schema": SCHEMA, "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
            "units": "m", "plan": plan, "printed": {k: pr[k] for k in ("W13", "W14", "W18")},
            "nw_twin": nw_twin(doc), "census_1f_windows": window_census(doc, msp, X.FLOORS["1F"])}


if __name__ == "__main__":
    OUT.write_text(json.dumps(read(sys.argv[1]), indent=1, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print("written", OUT.name)
