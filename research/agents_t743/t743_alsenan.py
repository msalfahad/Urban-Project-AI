"""T-743 read-only development-villa run: B12-01 sanitary fixtures and floor drains per room, architectural plan and
sanitary plan side by side (t743_census.SANITARY_FIXTURE_CENSUS_T743_V1). Nothing in the repository is written.

Usage (from the checkout root, through the wrapper):
  bash scripts/agent_env.sh run --tree task-T-743 research/agents_t743/t743_alsenan.py <arch.dxf> <sanitary.pdf> \
      <private reading.json> --out <scratch>/t743_alsenan.json [--arch-json <t743_arch_dump output>]

<private reading.json> is the person's reading of the sanitary sheets (symbol kinds, page points, printed drain sizes,
fit anchors); it stays in .work/private (drawing coordinates are never committed). Independent machine check: the
floor-drain squares of each sheet are counted from the PDF vector paths (orange 4.6 pt squares, the legend excluded)
and compared with the reading. Output: counts, kinds and engine room ids only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import t743_census as C  # noqa: E402

FD_COLOUR = (1.0, 0.75, 0.0)
FD_SIZE_PT = (4.3, 5.0)           # the FD square of this sheet set, both sides, in page points
LEGEND_X_FRACTION = 0.885          # the legend column of the rendered sheet (right of this fraction of the width)


def arch_symbols(dxf_path, rooms_floor_of_point):
    """fixture blocks of the arch plan whose CONTENT is not a room tag; kind from the engine's block vocabulary."""
    import ezdxf
    from ezdxf import bbox
    from engine.source import wet_room_evidence as W
    doc = ezdxf.readfile(str(dxf_path))
    out, tags = [], {}
    for e in doc.modelspace().query("INSERT"):
        name = e.dxf.name
        kind = W._fixture_kind(name)
        if kind is None:
            continue
        blk = doc.blocks.get(name)
        if C.is_tag_block([x.dxftype() for x in blk]):
            tags[name] = tags.get(name, 0) + 1
            continue
        ext = bbox.extents([e])
        cx, cy = (ext.center.x, ext.center.y) if ext.has_data else (e.dxf.insert.x, e.dxf.insert.y)
        x, y = cx / 1000.0, cy / 1000.0                      # this plan is in mm ($INSUNITS 4)
        fl = rooms_floor_of_point(x, y)
        if fl is None:
            continue
        k = {W.BASIN: C.BASIN, W.WC: C.WC, W.SHOWER: C.SHOWER_TRAY, W.BATH: C.BATH, W.URINAL: C.URINAL,
             W.KITCHEN_SINK: C.KITCHEN_SINK, W.FLOOR_DRAIN: C.FLOOR_DRAIN}.get(kind, C.UNTYPED)
        out.append(C.Symbol(kind=k, at_m=(x, y), source=C.ARCH, floor=fl, ref=f"{name}#{e.dxf.handle}"))
    return out, tags


def machine_fd_count(pdf_path):
    """floor-drain squares per page from the vector paths (independent of the person's reading)."""
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    res = {}
    for p in doc:
        rs = [pymupdf.Rect(g["rect"]) for g in p.get_drawings()
              if g.get("color") and tuple(round(c, 2) for c in g["color"]) == FD_COLOUR]
        par = list(range(len(rs)))

        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        for i, a in enumerate(rs):
            A = pymupdf.Rect(a.x0 - 0.3, a.y0 - 0.3, a.x1 + 0.3, a.y1 + 0.3)
            for j in range(i):
                if A.intersects(rs[j]) or A.contains(rs[j]):
                    par[f(i)] = f(j)
        groups = {}
        for i, r in enumerate(rs):
            groups.setdefault(f(i), pymupdf.Rect(r))
            groups[f(i)] |= r
        n = 0
        for r in groups.values():
            q = r * p.rotation_matrix
            if (FD_SIZE_PT[0] <= r.width <= FD_SIZE_PT[1] and FD_SIZE_PT[0] <= r.height <= FD_SIZE_PT[1]
                    and (q.x0 + q.x1) / 2 < LEGEND_X_FRACTION * p.rect.width):
                n += 1
        res[p.number + 1] = n
    return res


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("arch_dxf")
    ap.add_argument("sanitary_pdf")
    ap.add_argument("reading")
    ap.add_argument("--out", required=True)
    ap.add_argument("--arch-json", help="output of t743_arch_dump.py for the same drawing (saves the 40 s run)")
    a = ap.parse_args(argv)
    if a.arch_json:
        arch = json.loads(Path(a.arch_json).read_text(encoding="utf-8"))
    else:
        tmp = Path(a.out).with_suffix(".arch.json")
        subprocess.run([sys.executable, "-I", str(HERE / "t743_arch_dump.py"), a.arch_dxf, "--out", str(tmp)],
                       check=True)
        arch = json.loads(tmp.read_text(encoding="utf-8"))
    rooms = [C.Room(room_id=r["room_id"], floor=r["floor"], polygon_m=[tuple(p) for p in r["polygon_m"]],
                    codes=tuple(r["codes"] or r["labels"])) for r in arch["rooms"] if r["class"] != "MERGED"]

    def floor_of(x, y):
        best = None
        for r in rooms:
            d = C._dist(x, y, r.polygon_m)
            if d <= 1.0 and (best is None or d < best[0]):
                best = (d, r.floor)
        return best[1] if best else None
    a_syms, tags = arch_symbols(a.arch_dxf, floor_of)

    rd = json.loads(Path(a.reading).read_text(encoding="utf-8"))
    fits, s_syms, per_page = {}, [], {}
    for fl, pairs in rd["anchors"].items():
        fit, res = C.fit_sheet([(tuple(p[0]), tuple(p[1])) for p in pairs])
        C.check_fit(res)
        fits[fl] = {"scale_m_per_px": round(fit.s, 6), "residual_m_max": round(max(res), 3),
                    "residual_m_mean": round(sum(res) / len(res), 3), "pairs": len(pairs)}
        for i, (kind, u, v, size, _note) in enumerate(rd["symbols"].get(fl, []), 1):
            s_syms.append(C.Symbol(kind=kind, at_m=fit.to_plan(u, v), source=C.SANITARY, floor=fl,
                                   ref=f"SAN-{fl}-{i:02d}", size_in=size))
            if kind == C.FLOOR_DRAIN:
                pg = rd["pages"][fl]
                per_page[pg] = per_page.get(pg, 0) + 1
    c = C.census(rooms, a_syms, s_syms, sanitary_floors_read=set(rd["symbols"]))
    machine = machine_fd_count(a.sanitary_pdf)
    out = {"method": C.METHOD_ID, "arch_method": arch.get("method"),
           "arch_fixture_blocks": len(a_syms), "arch_tag_blocks_not_fixtures": tags, "sheet_fits": fits,
           "fd_check": {"reading_per_page": per_page, "machine_squares_per_page": machine},
           "totals_measured": dict(sorted(c.totals.items())), "held": dict(sorted(c.held_totals.items())),
           "floor_drains_by_size": c.drains_by_size, "unassigned": c.unassigned, "rows": C.table(c),
           "rooms": c.rooms}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("arch_fixture_blocks", "arch_tag_blocks_not_fixtures", "sheet_fits",
                                          "fd_check", "totals_measured", "held", "floor_drains_by_size")},
                     ensure_ascii=False))
    print("unassigned:", c.unassigned)
    for r in out["rows"]:
        print(r["room_id"], r["pcs"], "arch", r["arch"], "san", r["sanitary"], r["recon"], r["held"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
