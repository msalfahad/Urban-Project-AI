"""T-763 r2: stair-shaft ST-01 plaster / paint storey-band POINTS (no midpoint) from the merged T-173 / T-680 face model,
every held cause resolved by the owner's height rule, a company default or a named drawing reading.

Research only; reads the merged, sha-pinned shaft model (research/agents_t173, research/agents_t680, research/agents_t201
heads); writes nothing. Called by t763_fill.py.

Causes of the T-680 bound and how each is closed here (one consistent case, never a bound end picked for size):
  build-up b 0 .. 0.10       -> b = 0: owner 2026-11-13 plaster height = storey - slab thickness (4.34 / 4.04): the
                                face runs from the F.F.L. to the slab soffit F.F.L. - 0.16 (DEFAULT, owner rule)
  NW floor +0.30 / +1.00     -> +0.30: T-441 GF-ST-LOBBY030 west side has no face drawn (layer 1 / 5 / S-COL.BON), so the
                                +0.30 lobby floor runs on under the winders (ESTIMATE, C-SH-2 open with the designer)
  winder soffit MS1-T        -> the held winder zone is deducted as the winders' body (flight last-riser soffit 2.317 to
                                landing +3.50); a pitched soffit would expose at most 0.5 x 1.15 x 0.64 = 0.37 m2 per
                                face, below 1 % of the GF line (ESTIMATE, logged)
  OP-020 passage head        -> head 2.20 company default ('head = nearest printed else 2.20') above the +1.00 floor:
                                z 1.00 .. 3.20 (DEFAULT)
  B20 / B23 (Q-46)           -> the structural plan governs a member: B20 / B23 across the stair head (ST7757 roof slab
                                plans), so their ends are deducted on W / E, and no B20 lies over the GF south wall
                                (ESTIMATE until Q-46 is answered)
  W25 / W27                  -> T-201 vector heads (already DRAWING-CONFIRMED in T-680)
  2F top                     -> T-640 D-T173-1 (roof panel prints T 18: soffit +13.72) on all four faces and the roof B3
                                downstand on the structural plan (CORR_2F low)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

B_DEFAULT = 0.0          # owner: plaster height = storey - slab (no floor build-up between F.F.L. and the soffit face)
NW_FLOOR = 0.30          # lobby floor under the winders (T-441: the lobby's west side has no face)
PASSAGE_HEAD = 2.20      # company default head
FLOOR_GF = 1.00          # the shaft's GF floor, printed (section A-A)
LINE_OF = {  # line id -> (band, finish), as T-680
    "L-95f2c45c2eccaaeccb08": ("GF", "plaster"), "L-145bd2394f2907558243": ("GF", "paint"),
    "L-0eac839f9132da7bd116": ("1F", "plaster"), "L-2ab93d5029a4b7cc4dca": ("1F", "paint"),
    "L-418121a4b223cb4e8646": ("2F", "plaster"), "L-5a7a5c6f070ec7142ca5": ("2F", "paint"),
}


def _t680():
    name = "t680_alsenan"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "research/agents_t680/t680_alsenan.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def resolve_faces(faces: list[dict]) -> list[dict]:
    """Close every HELD contact / opening of the T-173 faces by the causes above; refuse anything left HELD."""
    out = []
    for f in faces:
        f = dict(f)
        cons = []
        for c in f.get("contacts", []):
            if c.get("status") != "HELD":
                cons.append(c)
            elif c["id"].startswith("MS1-T winders") or c["id"].startswith(("B20 end", "B23 end")):
                cons.append({**c, "status": "KNOWN"})
            elif c["id"].startswith("B20 over the wall"):
                continue        # the structural plan puts B20 across the stair head, not over the GF south wall
            else:
                raise ValueError(f"{f['id']}: held contact {c['id']} has no closing rule")
        f["contacts"] = cons
        ops = []
        for o in f.get("openings", []):
            if o.get("status") != "HELD":
                ops.append(o)
            elif o["id"] == "GF-passage-E":
                u0, u1 = o["rect"][0], o["rect"][1]
                ops.append({**o, "status": "ASSUMED", "rect": [u0, u1, FLOOR_GF, FLOOR_GF + PASSAGE_HEAD]})
            else:
                raise ValueError(f"{f['id']}: held opening {o['id']} has no closing rule")
        f["openings"] = ops
        out.append(f)
    return out


def default_faces(finish: str) -> list[dict]:
    T = _t680()
    A, R = T.A, T.R
    top = R.face_top(A.INP["levels"]["roof_mark"], B_DEFAULT, A.T)
    if finish == "paint":
        top -= A.DECOR
    faces = A.faces(B_DEFAULT, NW_FLOOR, top)
    H = T.heads()
    north = next(f for f in faces if f["id"].startswith("N "))
    north["openings"] = [R.opening_from_geometry({"id": o["id"], "u": [o["rect"][0], o["rect"][1]], "status": "HELD"},
                                                 H[o["id"]], north["region"]) if o["id"] in H else o
                         for o in north["openings"]]
    return resolve_faces(faces)


def points() -> dict:
    """{line id: (band, finish, value m2)}: the default case of the T-680 model, returns included, 2F corrected."""
    T = _t680()
    res = {}
    for finish in ("plaster", "paint"):
        a = T.band_areas(default_faces(finish))
        if abs(a["whole"][0] - a["whole"][1]) > 1e-9:
            raise ValueError("a held item survived: hi != lo")
        for i, band in enumerate(T.BANDS):
            v = a["hi"][i] + a["ret_hi"][i]
            if band == "2F":
                v -= float(T.CORR_2F["low"])
            res[(band, finish)] = v
    return {lid: (b, f, res[(b, f)]) for lid, (b, f) in LINE_OF.items()}


if __name__ == "__main__":
    for lid, (b, f, v) in points().items():
        print(lid, b, f, round(v, 3))
