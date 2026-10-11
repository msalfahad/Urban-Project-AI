"""M7 METAMORPHIC HARNESS - properties a quantity engine must keep when the drawing changes in ways that do not change
the building (independent of the engine's own formulas: only the DXF is changed, never the expected quantity).

    python3 -I tools/m7_metamorphic.py OUT.json DXF [--profile P.json] [--conventions C.json] [--ops op,op,...]

Each operation writes a transformed copy of the drawing and runs route G on it; the quantities (concrete and
reinforcement base / low / high by family and storey, and the item count by category) must equal the original's
within a relative 1e-6 (a geometric operation) or exactly (a reordering). Operations:

  translate     every entity moved by (+1 234 567, -765 432) drawing units
  rot90 / rot180 / rot270   the whole drawing rotated about the origin (frames, texts, blocks with it)
  mirror_x      the drawing mirrored about the y axis (x -> -x); lengths, areas and volumes are kept
  reorder       the model-space entities written in reverse order
  explode       every closed / open LWPOLYLINE replaced by its LINE / ARC pieces (same shape)
  dup_text      every TEXT / MTEXT drawn twice at the same place (a duplicated annotation)
  noise_layer   a furniture-like layer ('Z-FURNITURE-UNRELATED') of rectangles and circles inside every sheet
  units_m       the drawing re-expressed in the other unit: millimetres -> metres (x 0.001, $INSUNITS 6), a metre
                drawing -> millimetres (x 1000, $INSUNITS 4)

A difference is a finding about the engine (or a documented limitation), never a reason to change an expected value.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OPS = ("translate", "rot90", "rot180", "rot270", "mirror_x", "reorder", "explode", "dup_text", "noise_layer",
       "units_m")
GEOMETRIC = ("translate", "rot90", "rot180", "rot270", "mirror_x", "explode", "units_m")


def _matrix(op):
    from ezdxf.math import Matrix44
    if op == "translate":
        return Matrix44.translate(1234567.0, -765432.0, 0.0)
    if op.startswith("rot"):
        return Matrix44.z_rotate(math.radians(int(op[3:])))
    if op == "mirror_x":
        return Matrix44.scale(-1.0, 1.0, 1.0)
    if op == "units_m":
        return Matrix44.scale(0.001, 0.001, 0.001)
    return None


def transform(src, dst, op, seed=7):
    """write the transformed copy of `src` to `dst`; returns notes (entities that could not be transformed)."""
    import ezdxf
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    notes = defaultdict(int)
    m = _matrix(op)
    if op == "units_m" and int(doc.header.get("$INSUNITS", 0) or 0) == 6:
        from ezdxf.math import Matrix44
        m = Matrix44.scale(1000.0, 1000.0, 1000.0)
    if m is not None:
        for e in list(msp):
            try:
                e.transform(m)
            except Exception as ex:                   # noqa: BLE001 - recorded, never hidden
                notes[f"{e.dxftype()}:{type(ex).__name__}"] += 1
        if op == "units_m":
            ins = int(doc.header.get("$INSUNITS", 0) or 0)
            if ins not in (4, 0, 6):
                notes[f"INSUNITS_{ins}_READ_AS_MM"] += 1
            doc.header["$INSUNITS"] = 4 if ins == 6 else 6
    elif op == "reorder":
        ents = list(msp)
        for e in ents:
            msp.unlink_entity(e)
        for e in reversed(ents):
            msp.add_entity(e)
    elif op == "explode":
        for e in list(msp.query("LWPOLYLINE")):
            try:
                e.explode()
            except Exception as ex:                   # noqa: BLE001
                notes[f"EXPLODE:{type(ex).__name__}"] += 1
    elif op == "dup_text":
        for e in list(msp.query("TEXT MTEXT")):
            msp.add_entity(e.copy())
    elif op == "noise_layer":
        R = random.Random(seed)
        if "Z-FURNITURE-UNRELATED" not in doc.layers:
            doc.layers.add("Z-FURNITURE-UNRELATED")
        xs = [p for e in msp.query("LINE") for p in (e.dxf.start.x, e.dxf.end.x)]
        ys = [p for e in msp.query("LINE") for p in (e.dxf.start.y, e.dxf.end.y)]
        if xs:
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            span = max(x1 - x0, y1 - y0)
            s = span / 400.0
            for _ in range(160):
                cx, cy = R.uniform(x0, x1), R.uniform(y0, y1)
                w, h = R.uniform(2, 8) * s, R.uniform(2, 8) * s
                if R.random() < 0.5:
                    msp.add_lwpolyline([(cx, cy), (cx + w, cy), (cx + w, cy + h), (cx, cy + h)], close=True,
                                       dxfattribs={"layer": "Z-FURNITURE-UNRELATED"})
                else:
                    msp.add_circle((cx, cy), w / 2, dxfattribs={"layer": "Z-FURNITURE-UNRELATED"})
    else:
        raise ValueError(f"unknown operation {op}")
    doc.saveas(str(dst))
    return dict(notes)


def quantities(items):
    """(trade, family, storey, category) -> {n, base, low, high, exposure_low, exposure_high} - what a BOQ prints."""
    q = defaultdict(lambda: defaultdict(float))
    for i in items:
        k = f"{i['trade']}|{i['family']}|{i.get('storey')}|{i['category']}"
        q[k]["n"] += 1
        for f in ("base", "low", "high", "exposure_low", "exposure_high"):
            q[k][f] += float(i.get(f) or 0.0)
    return {k: {f: round(v, 9) for f, v in sorted(d.items())} for k, d in sorted(q.items())}


def compare(a, b, rel=1e-6, exact=False):
    """the keys whose values differ (beyond rel, or at all when exact)."""
    out = []
    for k in sorted(set(a) | set(b)):
        if k not in a or k not in b:
            out.append({"key": k, "original": a.get(k), "transformed": b.get(k)})
            continue
        for f in sorted(set(a[k]) | set(b[k])):
            x, y = a[k].get(f, 0.0), b[k].get(f, 0.0)
            tol = 0.0 if (exact or f == "n") else rel * max(abs(x), abs(y), 1.0)
            if abs(x - y) > tol:
                out.append({"key": k, "field": f, "original": x, "transformed": y, "delta": round(y - x, 9)})
    return out


def run(dxf, *, profile=None, conventions=None, arch=None, ops=OPS, work=None):
    from tools import urban_boq_m2 as CLI
    kw = dict(route="G", profile=profile, conventions=conventions)
    base = CLI.compute([str(dxf)], arch=[str(arch)] if arch else None, **kw)
    q0 = quantities(base["items"])
    res = {"drawing_sha256": hashlib.sha256(Path(dxf).read_bytes()).hexdigest(), "items": len(base["items"]),
           "ops": {}}
    with tempfile.TemporaryDirectory(dir=work) as td:
        for op in ops:
            dst = Path(td) / f"{op}.dxf"
            rec = {"notes": transform(dxf, dst, op)}
            try:
                R = CLI.compute([str(dst)], arch=[str(arch)] if arch else None, **kw)
                q1 = quantities(R["items"])
                d = compare(q0, q1, exact=op not in GEOMETRIC)
                rec.update(ok=True, items=len(R["items"]), differences=d, n_differences=len(d))
            except Exception as ex:                   # noqa: BLE001 - a crash is a finding
                rec.update(ok=False, error=f"{type(ex).__name__}: {ex}")
            res["ops"][op] = rec
    res["passed"] = [op for op, r in res["ops"].items() if r.get("ok") and not r["n_differences"]]
    res["failed"] = [op for op in res["ops"] if op not in res["passed"]]
    return res


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a}
    ops = tuple(opt["--ops"].split(",")) if "--ops" in opt else OPS
    res = run(args[1], profile=opt.get("--profile"), conventions=opt.get("--conventions"), arch=opt.get("--arch"),
              ops=ops)
    Path(args[0]).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"passed": res["passed"], "failed": res["failed"],
                      "n_differences": {k: v.get("n_differences", "CRASH") for k, v in res["ops"].items()}}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
