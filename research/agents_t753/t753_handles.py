"""T-753 read-only: print the type, layer and exact geometry (metres) of DXF entities by handle, to stdout only.
Usage: run research/agents_t753/t753_handles.py <arch.dxf> H1 H2 ..."""
import sys


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    import ezdxf
    doc = ezdxf.readfile(a[0])
    for h in a[1:]:
        e = doc.entitydb.get(h)
        if e is None:
            print(h, "MISSING")
            continue
        t = e.dxftype()
        if t == "LINE":
            s, f = e.dxf.start, e.dxf.end
            print(h, t, e.dxf.layer, [round(s.x / 1000, 4), round(s.y / 1000, 4)], [round(f.x / 1000, 4), round(f.y / 1000, 4)])
        elif t == "LWPOLYLINE":
            print(h, t, e.dxf.layer, e.closed, [[round(p[0] / 1000, 4), round(p[1] / 1000, 4), round(p[4], 3)] for p in e.get_points()])
        elif t == "INSERT":
            print(h, t, e.dxf.layer, e.dxf.name, round(e.dxf.insert.x / 1000, 4), round(e.dxf.insert.y / 1000, 4), e.dxf.rotation)
        else:
            print(h, t, e.dxf.layer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
