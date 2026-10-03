"""Test-side REFERENCE realiser, used only for mutation-sensitivity tests.

It is NOT the R8 kernel and nothing under engine/ may import it. It exists
for one job: to show that every R8.0 fixture DETECTS the deliberate break
named by its mutation. A mutation is switched on by a flag; the fixture must
then fail against the hand-derived truth in ``scenes.py``.

Its own correctness is not assumed: ``test_r8_0_truth.py`` checks the
unmutated realiser against the hand truth on every scene, so a bug here
shows up as a truth failure, not as a silent pass.

Method (deliberately different from engine/cad_adapter.py): 3x3 affine
matrices; OCS by the Arbitrary Axis Algorithm; curves realised by mapping
sample POINTS (start, mid, end, centre) through the full composed map; sweep
direction from the sign of the composed determinant. No angle arithmetic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

MUTATIONS = {
    "SKIP_BASE_POINT",               # MT-01
    "MIRROR_AS_ROTATION",            # MT-02 (this is what current cad_adapter does)
    "DROP_OCS",                      # MT-03
    "BULGE_FLIP_ONLY_ON_EXTRUSION",  # MT-49
    "MINSERT_FIRST_CELL_ONLY",       # MT-06 variant used for F06
    "UNREADABLE_FRAME_AS_WCS",       # fail-open OCS (what U-C4N's ocs.py does)
    "IGNORE_XREF",                   # XREF silently empty
}


def mat(a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
    """x' = a x + c y + e ; y' = b x + d y + f"""
    return (a, b, c, d, e, f)


def mul(m2, m1):
    """m2 after m1."""
    a2, b2, c2, d2, e2, f2 = m2
    a1, b1, c1, d1, e1, f1 = m1
    return (a2 * a1 + c2 * b1, b2 * a1 + d2 * b1, a2 * c1 + c2 * d1, b2 * c1 + d2 * d1,
            a2 * e1 + c2 * f1 + e2, b2 * e1 + d2 * f1 + f2)


def apply(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def det(m):
    return m[0] * m[3] - m[1] * m[2]


def translate(x, y):
    return mat(e=x, f=y)


def rotate_deg(deg):
    t = math.radians(deg)
    return mat(math.cos(t), math.sin(t), -math.sin(t), math.cos(t))


def scale(sx, sy):
    return mat(sx, 0.0, 0.0, sy)


class FrameError(Exception):
    def __init__(self, code, detail):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def ocs_plan_matrix(extrusion, mutations=()):
    """OCS -> WCS plan map by the Arbitrary Axis Algorithm.

    Fail closed: an unreadable extrusion raises FRAME_UNREADABLE; a frame
    whose normal is not +/-Z raises UNSUPPORTED_FRAME (an (x, y) pair does not
    determine a point on a tilted plane in plan)."""
    if "DROP_OCS" in mutations:
        return mat()
    n = extrusion
    ok = isinstance(n, (list, tuple)) and len(n) == 3 and all(
        isinstance(v, (int, float)) and math.isfinite(v) for v in n)
    if not ok or math.sqrt(sum(v * v for v in n)) == 0.0:
        if "UNREADABLE_FRAME_AS_WCS" in mutations:
            return mat()
        raise FrameError("FRAME_UNREADABLE", repr(extrusion))
    L = math.sqrt(sum(v * v for v in n))
    nz = tuple(v / L for v in n)
    if abs(nz[0]) < 1.0 / 64 and abs(nz[1]) < 1.0 / 64:
        ax = _cross((0.0, 1.0, 0.0), nz)
    else:
        ax = _cross((0.0, 0.0, 1.0), nz)
    ax = _unit(ax)
    ay = _unit(_cross(nz, ax))
    if abs(nz[0]) > 1e-12 or abs(nz[1]) > 1e-12:
        raise FrameError("UNSUPPORTED_FRAME", repr(extrusion))
    # plan part of the OCS basis: WCS = x*Ax + y*Ay
    return mat(ax[0], ax[1], ay[0], ay[1])


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _unit(v):
    L = math.sqrt(sum(c * c for c in v))
    return tuple(c / L for c in v)


@dataclass
class Realised:
    arcs: list = field(default_factory=list)
    bulges: list = field(default_factory=list)
    segments: list = field(default_factory=list)
    findings: list = field(default_factory=list)


def realise(scene, mutations=()):
    mutations = set(mutations)
    assert mutations <= MUTATIONS, mutations - MUTATIONS
    out = Realised()
    blocks = scene.get("blocks", {})

    def emit(e, m, path):
        k = e["kind"]
        try:
            if k == "LINE":                       # WCS-native: extrusion never applies
                out.segments.append((apply(m, e["a"]), apply(m, e["b"])))
                return
            if k in ("ARC", "LWPOLYLINE", "CIRCLE"):
                o = ocs_plan_matrix(e.get("extrusion", (0.0, 0.0, 1.0)), mutations)
                full = mul(m, o)
                if k == "ARC":
                    out.arcs.append(_arc(full, e, m, o, mutations))
                elif k == "LWPOLYLINE":
                    _lwpoly(full, e, m, o, mutations, out)
                return
            if k in ("INSERT", "MINSERT"):
                blk = blocks[e["block"]]
                if blk.get("xref"):
                    if "IGNORE_XREF" not in mutations:
                        out.findings.append({"code": "XREF", "block": e["block"], "path": list(path)})
                    return
                o = ocs_plan_matrix(e.get("extrusion", (0.0, 0.0, 1.0)), mutations)
                bx, by = blk.get("base", (0.0, 0.0))
                if "SKIP_BASE_POINT" in mutations:
                    bx, by = 0.0, 0.0
                sx, sy = e.get("scale", (1.0, 1.0))
                rot = e.get("rot", 0.0)
                cells = [(0, 0)]
                if k == "MINSERT":
                    cells = [(c, r) for c in range(e["cols"]) for r in range(e["rows"])]
                    if "MINSERT_FIRST_CELL_ONLY" in mutations:
                        cells = cells[:1]
                for c, r in cells:
                    off = apply(rotate_deg(rot), (c * e.get("col_sp", 0.0), r * e.get("row_sp", 0.0)))
                    local = mul(translate(e["at"][0] + off[0], e["at"][1] + off[1]),
                                mul(rotate_deg(rot), mul(scale(sx, sy), translate(-bx, -by))))
                    placed = mul(m, mul(o, local))
                    for child in blk.get("entities", []):
                        emit(child, placed, path + [e["block"]])
                return
            out.findings.append({"code": "UNREALISED_KIND", "kind": k, "path": list(path)})
        except FrameError as err:
            out.findings.append({"code": err.code, "kind": k, "path": list(path)})

    for e in scene.get("entities", []):
        emit(e, mat(), [])
    return out


def _arc(full, e, parent, o, mutations):
    cx, cy = e["c"]
    r = e["r"]
    a0, a1 = e["a0"], e["a1"]
    sweep = (a1 - a0) % 360.0 or 360.0
    pt = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    if "MIRROR_AS_ROTATION" in mutations:
        # the defect under test: centre mapped, angles advanced by the
        # composed rotation, no reflection (current cad_adapter L688-695)
        rot = math.degrees(math.atan2(full[1], full[0]))
        c = apply(full, (cx, cy))
        s = math.hypot(full[0], full[1])
        p = lambda a: (c[0] + r * s * math.cos(math.radians(a + rot)), c[1] + r * s * math.sin(math.radians(a + rot)))
        return {"CENTER": c, "P0": p(a0), "PM": p(a0 + sweep / 2), "P1": p(a1), "DIR": "CCW", "RADIUS": r * s}
    d = det(full)
    return {"CENTER": apply(full, (cx, cy)), "P0": apply(full, pt(a0)), "PM": apply(full, pt(a0 + sweep / 2)),
            "P1": apply(full, pt(a1)), "DIR": "CCW" if d > 0 else "CW", "RADIUS": r * math.sqrt(abs(d))}


def _lwpoly(full, e, parent, o, mutations, out):
    pts = e["pts"]
    bul = e.get("bulges", [0.0] * len(pts))
    n = len(pts)
    spans = range(n) if e.get("closed") else range(n - 1)
    for i in spans:
        a, b = pts[i], pts[(i + 1) % n]
        g = bul[i] if i < len(bul) else 0.0
        A, B = apply(full, a), apply(full, b)
        if abs(g) < 1e-12:
            out.segments.append((A, B))
            continue
        theta = 4.0 * math.atan(abs(g))                 # included angle
        chord = math.hypot(b[0] - a[0], b[1] - a[1])
        rad = chord / (2.0 * math.sin(theta / 2.0))
        # local centre: left of a->b for positive bulge (CCW), right for negative
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        lx, ly = -(b[1] - a[1]) / chord, (b[0] - a[0]) / chord
        h = rad * math.cos(theta / 2.0) * (1.0 if g > 0 else -1.0)
        c_loc = (mx + lx * h, my + ly * h)
        # local arc midpoint: opposite side of the chord from the centre, sagitta away
        sag = rad - rad * math.cos(theta / 2.0)
        m_loc = (mx - lx * sag * (1.0 if g > 0 else -1.0), my - ly * sag * (1.0 if g > 0 else -1.0))
        d = det(full)
        dir_ab = "CCW" if (g > 0) == (d > 0) else "CW"
        C, M = apply(full, c_loc), apply(full, m_loc)
        if "BULGE_FLIP_ONLY_ON_EXTRUSION" in mutations:
            # flip keyed on extrusion alone: a negative-scale mirror is missed,
            # so the curve is rebuilt on the WORLD chord with the local sign
            flip = det(o) < 0
            s_eff = (g > 0) != flip
            wl = ((-(B[1] - A[1]) / math.hypot(B[0] - A[0], B[1] - A[1])),
                  ((B[0] - A[0]) / math.hypot(B[0] - A[0], B[1] - A[1])))
            wr = rad * math.sqrt(abs(d))
            wh = wr * math.cos(theta / 2.0) * (1.0 if s_eff else -1.0)
            wm = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
            C = (wm[0] + wl[0] * wh, wm[1] + wl[1] * wh)
            ws = wr - wr * math.cos(theta / 2.0)
            M = (wm[0] - wl[0] * ws * (1.0 if s_eff else -1.0), wm[1] - wl[1] * ws * (1.0 if s_eff else -1.0))
            dir_ab = "CCW" if s_eff else "CW"
        out.bulges.append({"VERTEX_A": A, "VERTEX_B": B, "ARC_MIDPOINT": M, "CENTER": C, "DIR_A_TO_B": dir_ab})
