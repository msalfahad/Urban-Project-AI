"""T-346 rules (research, not a method): read a freelancer facade row as the physical element it describes, never as a
quantity, and reconcile it to the drawn faces in named parts with residual 0.

R-T346-1  A freelancer figure is evidence to trace, never a quantity: a FILL row is made only from a drawn face
          (`fill_row` refuses any other source).
R-T346-2  One plane per elevation (his practice for set-back blocks) is compared with the drawn faces band by band:
          bands are cut at every face bottom / top and at his own bottom / top; in each band his width minus the sum of
          the drawn widths that stand in it gives a named m2 term (width, hidden overlap, height). Drawn parts outside
          his band are reported apart (never netted into his row).
R-T346-3  A projection band (a lower block standing out beyond the block above it) has two ends; a row of
          (band depth x lower-block height) x 2 is the two end returns. Each return is mapped to the face at that end.
          A return that is the same physical face portion as another of his rows is a DOUBLE COUNT: its share keeps his
          m2 visible and adds no drawn m2. A face portion is MATCHED by at most one of his rows.
R-T346-4  A site / boundary wall is never a house-facade face (OTHER_TRADE, owner Q-65 C); a row part with no drawn
          face stays UNRESOLVED with drawn m2 None, never 0.
"""

from __future__ import annotations

EPS = 1e-9
HOUSE = "HOUSE_FACE"
SITE = ("SITE_WALL", "BOUNDARY_WALL")


class RuleError(ValueError):
    pass


def face(key, width_m, bottom_m, top_m, element=HOUSE, line=None):
    if width_m is None or bottom_m is None or top_m is None:
        raise RuleError(f"{key}: a face needs width, bottom and top (HELD faces are not compared here)")
    if top_m <= bottom_m + EPS or width_m <= 0:
        raise RuleError(f"{key}: empty face")
    if element in SITE and line is not None and "FIN.EXT" in line:
        raise RuleError(f"{key}: a {element} is OTHER_TRADE (Q-65 C), never in a house facade line")
    return {"key": key, "w": float(width_m), "lo": float(bottom_m), "hi": float(top_m), "element": element,
            "line": line}


def face_m2(f, lo=None, hi=None):
    a = max(f["lo"], lo if lo is not None else f["lo"])
    b = min(f["hi"], hi if hi is not None else f["hi"])
    return 0.0 if b <= a else f["w"] * (b - a)


def plane_bands(his_w, his_lo, his_hi, faces):
    """R-T346-2. Returns (bands, drawn_in, drawn_out): bands = [(lo, hi, his_w, drawn_w, his_minus_drawn_m2)]."""
    if his_hi <= his_lo or his_w <= 0:
        raise RuleError("his plane must have a width and a height")
    cuts = {his_lo, his_hi}
    for f in faces:
        for z in (f["lo"], f["hi"]):
            if his_lo < z < his_hi:
                cuts.add(z)
    cuts = sorted(cuts)
    bands = []
    for a, b in zip(cuts, cuts[1:]):
        dw = sum(f["w"] for f in faces if f["lo"] <= a + EPS and f["hi"] >= b - EPS)
        bands.append((a, b, his_w, dw, (his_w - dw) * (b - a)))
    drawn_in = sum(face_m2(f, his_lo, his_hi) for f in faces)
    drawn_out = sum(face_m2(f) for f in faces) - drawn_in
    return bands, drawn_in, drawn_out


class Ledger:
    """His rows split into parts; every face portion matched once (R-T346-3)."""

    def __init__(self):
        self.parts = []
        self.owner = {}          # face key -> his row that matched it

    def match(self, row, share_m2, faces, his_w, his_lo, his_hi, name):
        for f in faces:
            if f["element"] in SITE:
                raise RuleError(f"{f['key']}: site / boundary wall in a house facade reconciliation (Q-65 C)")
            if f["key"] in self.owner:
                raise RuleError(f"{f['key']} already matched by row {self.owner[f['key']]}: use double_count")
        bands, d_in, d_out = plane_bands(his_w, his_lo, his_hi, faces)
        if abs(his_w * (his_hi - his_lo) - share_m2) > 1e-6:
            raise RuleError(f"row {row} {name}: share {share_m2} is not his {his_w} x {his_hi - his_lo}")
        for f in faces:
            self.owner[f["key"]] = row
        p = {"row": row, "name": name, "kind": "MATCHED", "his_m2": share_m2, "drawn_m2": d_in,
             "drawn_outside_his_band_m2": d_out, "bands": bands, "faces": [f["key"] for f in faces],
             "lines": sorted({f["line"] for f in faces if f["line"]}),
             "residual_terms_m2": sum(b[4] for b in bands)}
        self.parts.append(p)
        return p

    def double_count(self, row, share_m2, face_key, name):
        if face_key not in self.owner:
            raise RuleError(f"{face_key} is not matched yet: a double count needs the first claim")
        p = {"row": row, "name": name, "kind": "DOUBLE_COUNT", "his_m2": share_m2, "drawn_m2": 0.0,
             "drawn_outside_his_band_m2": 0.0, "bands": [], "faces": [face_key], "residual_terms_m2": 0.0,
             "first_claim": self.owner[face_key]}
        self.parts.append(p)
        return p

    def unresolved(self, row, share_m2, name):
        p = {"row": row, "name": name, "kind": "UNRESOLVED", "his_m2": share_m2, "drawn_m2": None,
             "drawn_outside_his_band_m2": None, "bands": [], "faces": [], "residual_terms_m2": None}
        self.parts.append(p)
        return p

    def statement(self, rows_m2):
        """Reconciliation: his total = matched drawn + double counts + named band terms (+ UNRESOLVED shares)."""
        out = {}
        for r, m2 in rows_m2.items():
            ps = [p for p in self.parts if p["row"] == r]
            if abs(sum(p["his_m2"] for p in ps) - m2) > 1e-6:
                raise RuleError(f"row {r}: parts {sum(p['his_m2'] for p in ps)} do not add up to his {m2}")
        tot = sum(rows_m2.values())
        drawn = sum(p["drawn_m2"] for p in self.parts if p["kind"] == "MATCHED")
        dbl = sum(p["his_m2"] for p in self.parts if p["kind"] == "DOUBLE_COUNT")
        terms = sum(p["residual_terms_m2"] for p in self.parts if p["kind"] == "MATCHED")
        unres = sum(p["his_m2"] for p in self.parts if p["kind"] == "UNRESOLVED")
        out.update(his_total=tot, drawn_matched=drawn, double_count=dbl, named_terms=terms, unresolved=unres,
                   residual=tot - drawn - dbl - terms - unres)
        return out


def fill_row(source, face_key, line, m2, status):
    """R-T346-1: only a drawn face makes a FILL row; a HELD / UNKNOWN row carries no point value."""
    if source != "DRAWING":
        raise RuleError(f"{face_key}: a FILL row comes from the drawing, never from '{source}'")
    if status in ("HELD", "UNKNOWN") and m2 is not None and not isinstance(m2, tuple):
        raise RuleError(f"{face_key}: {status} carries a range or blank, never a point value")
    if m2 is None and status not in ("HELD", "UNKNOWN"):
        raise RuleError(f"{face_key}: missing is never 0 and never DRAWING-CONFIRMED")
    return {"face": face_key, "line": line, "m2": m2, "status": status}
