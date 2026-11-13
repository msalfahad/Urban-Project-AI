"""T-753 read-only: render a PDF page (or a clip of it, as fractions of the page) to a PNG outside the repository.
Usage: run research/agents_t753/t753_pdfpage.py <in.pdf> <out.png> [page=1] [dpi=60] [fx0 fy0 fx1 fy1]"""
import sys


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    import pymupdf
    doc = pymupdf.open(a[0])
    p = doc[int(a[2]) - 1 if len(a) > 2 else 0]
    dpi = int(a[3]) if len(a) > 3 else 60
    clip = None
    if len(a) > 7:
        r = p.rect
        f = [float(x) for x in a[4:8]]
        clip = pymupdf.Rect(r.x0 + f[0] * r.width, r.y0 + f[1] * r.height, r.x0 + f[2] * r.width, r.y0 + f[3] * r.height)
    p.get_pixmap(dpi=dpi, clip=clip).save(a[1])
    print("page", p.number + 1, "of", len(doc), "rect", p.rect, "rotation", p.rotation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
