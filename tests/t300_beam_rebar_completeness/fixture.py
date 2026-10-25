"""Hand fixture (NOT Alsenan) for the T-300 beam reinforcement completeness safeguard.

Drawing units mm. Sheet 'S1': a simple-beam schedule with rows B41 .. B44 (row height 600, grid lines at the row
boundaries), sheet 'S2': a two-span continuous-beam schedule with rows CB21, CB22 (row height 4000).

Simple table, mark column x = 1000, attribute rows anchored 250 above each row's lower grid line:
    row  mark  W x H (cm)  BOT     TOP     LINK      remark column (x = 9000)         link symbol (x = 10000)
    1    B41   25 x 50     3Ø16    2Ø12    6Ø8       -                                 -
    2    B42   30 x 80     5Ø18    2Ø14    6Ø10      '2%%C14/25cm'                     3 nested loops
    3    B43   30 x 90     6Ø18    2Ø14    8Ø10      -                                 -
    4    B44   25 x 70     4Ø16    2Ø12    6Ø8       '2%%C12/30cm' (row 4, inside)     1 loop
Continuous table: CB21 (25 x 75) spans 1 / 2 with BOT1 3Ø16 (x 3000 .. 3600), BOT2 4Ø16 (x 7000 .. 7600), MID 5Ø18
(x 5000 .. 5600), STR1 / STR2; corner callouts above the slots: span 1 split '2' '%%C' '12', span 2 '3%%C16'; MIDDLE
REINT. column (x 11000): '2%%C12' with a separate '20cm' piece. CB22 (25 x 50): MID slot EMPTY with '4%%C16' written
on it as text, span 1 corner '2%%C12', span 2 has no corner callout, and an unclassified '3%%C14' at slot level in the
middle of span 2.
General note record: side bars in beams deeper than 60 cm unless stated otherwise.
"""
from __future__ import annotations

NOTE = {"kind": "SIDE_BAR_NOTE", "depth_gt_m": 0.60, "source": "fixture general note 7"}
UNIT_MASS = {"method": "D2_OVER_162"}


def _attrs(owner, x0, y, vals, step=600.0):
    out = []
    for i, (tag, v) in enumerate(vals):
        out.append({"owner": owner, "tag": tag, "value": v, "x": x0 + i * step, "y": y})
    return out


def _rect(eid, x0, y0, x1, y1, sheet, path=()):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [{"id": f"{eid}:{k}", "a": pts[k], "b": pts[(k + 1) % 4], "sheet": sheet, "path": list(path),
             "layer": "L"} for k in range(4)]


def _hline(eid, y, x0, x1, sheet):
    return {"id": eid, "a": (x0, y), "b": (x1, y), "sheet": sheet, "path": [], "layer": "L"}


def _t(tid, v, x, y, h, sheet, owner=None):
    return {"id": tid, "value": v, "x": x, "y": y, "height": h, "sheet": sheet, "owner": owner}


def simple_table(*, boundary_text=False):
    """Rows top -> bottom B41 (y 1800 .. 2400), B42 (1200 .. 1800), B43 (600 .. 1200), B44 (0 .. 600)."""
    attrs, texts, segs = [], [], []
    rows = [("41", "B41", "25", "50", ("3", "16"), ("2", "12"), ("6", "8")),
            ("42", "B42", "30", "80", ("5", "18"), ("2", "14"), ("6", "10")),
            ("43", "B43", "30", "90", ("6", "18"), ("2", "14"), ("8", "10")),
            ("44", "B44", "25", "70", ("4", "16"), ("2", "12"), ("6", "8"))]
    for i, (own, mk, w, h, bot, top, link) in enumerate(rows):
        lo = 1800 - 600 * i
        y = lo + 250
        attrs += _attrs(own, 1000, y, [("MARK", mk), ("W", w), ("H", h), ("BOT-N", bot[0]), ("BOT-DIA", bot[1]),
                                        ("TOP-N", top[0]), ("TOP-DIA", top[1]), ("LINK-N", link[0]),
                                        ("LINK-DIA", link[1])])
        texts.append(_t(f"G{own}a", "%%C", 3300, y + 80, 150, "S1", owner=f"D2:{own}"))   # the row's own glyph
    for k, gy in enumerate((2400, 1800, 1200, 600, 0)):
        segs.append(_hline(f"H{k}", gy, 800, 10600, "S1"))
    segs.append(_hline("H9", 2700, 800, 10600, "S1"))                                     # header top line
    texts += [_t("HDR1", "REMARKS", 9050, 2550, 150, "S1"), _t("HDR2", "LINKS/m", 5900, 2550, 150, "S1")]
    texts.append(_t("R42", "2%%C14/25cm", 9000, 1450, 120, "S1"))
    texts.append(_t("R44", "2%%C12/30cm", 9000, 300, 120, "S1"))
    segs += _rect("LA@SYM1", 10000, 1300, 10400, 1700, "S1", ["D2:SYM1"])
    segs += _rect("LB@SYM1", 10050, 1350, 10200, 1700, "S1", ["D2:SYM1"])
    segs += _rect("LC@SYM1", 10200, 1350, 10350, 1700, "S1", ["D2:SYM1"])
    segs += _rect("LD@SYM2", 10000, 100, 10400, 500, "S1", ["D2:SYM2"])
    if boundary_text:
        texts.append(_t("RX", "2%%C16/20cm", 9000, 1205, 120, "S1"))                     # on the B42 / B43 line
    return attrs, texts, segs


def continuous_table():
    """CB21 row y 4000 .. 8000, CB22 row y 0 .. 4000 (sheet S2)."""
    attrs, texts, segs = [], [], []
    for own, mk, w, h, lo, mid in (("21", "CB21", "25", "75", 4000, ("5", "18")), ("22", "CB22", "25", "50", 0,
                                                                                     ("", ""))):
        a = [{"owner": own, "tag": "BEAM-NAME", "value": mk, "x": 500, "y": lo + 1500},
             {"owner": own, "tag": "W", "value": w, "x": 9000, "y": lo + 2000},
             {"owner": own, "tag": "H", "value": h, "x": 9600, "y": lo + 2000},
             {"owner": own, "tag": "L1-M", "value": "4.0", "x": 3300, "y": lo + 3500},
             {"owner": own, "tag": "L2-M", "value": "4.5", "x": 7300, "y": lo + 3500},
             {"owner": own, "tag": "BOT1-B", "value": "3", "x": 3000, "y": lo + 1000},
             {"owner": own, "tag": "BOT1-D", "value": "16", "x": 3600, "y": lo + 1000},
             {"owner": own, "tag": "BOT2-B", "value": "4", "x": 7000, "y": lo + 1000},
             {"owner": own, "tag": "BOT2-D", "value": "16", "x": 7600, "y": lo + 1000},
             {"owner": own, "tag": "MID-B", "value": mid[0], "x": 5000, "y": lo + 2200},
             {"owner": own, "tag": "MID-D", "value": mid[1], "x": 5600, "y": lo + 2200},
             {"owner": own, "tag": "STR1-B", "value": "6", "x": 3000, "y": lo + 400},
             {"owner": own, "tag": "STR1-D", "value": "8", "x": 3600, "y": lo + 400},
             {"owner": own, "tag": "STR2-B", "value": "6", "x": 7000, "y": lo + 400},
             {"owner": own, "tag": "STR2-D", "value": "8", "x": 7600, "y": lo + 400}]
        attrs += a
        texts.append(_t(f"G{own}b1", "%%C", 3300, lo + 1250, 300, "S2", owner=f"D2:{own}"))
    for k, gy in enumerate((8000, 4000, 0)):
        segs.append(_hline(f"C{k}", gy, 0, 12500, "S2"))
    texts += [_t("HC1", "MIDDLE", 11000, 8600, 250, "S2"), _t("HC2", "REINT.", 11050, 8300, 250, "S2"),
              _t("HC3", "B", 9000, 8400, 250, "S2")]
    # CB21: corner span 1 split in three pieces, span 2 one text; MIDDLE REINT. in two pieces; a slot glyph on MID
    texts += [_t("C1a", "2", 2900, 7100, 300, "S2"), _t("C1b", "%%C", 3300, 7100, 300, "S2"),
              _t("C1c", "12", 3650, 7100, 300, "S2"), _t("C2", "3%%C16", 7300, 7100, 300, "S2"),
              _t("M1", "2%%C12", 11000, 7400, 280, "S2"), _t("M2", "20cm", 11050, 5000, 250, "S2"),
              _t("MG", "%%C", 5300, 6450, 300, "S2")]
    # CB22: the empty MID slot carries its value as text; span 1 corner; an unclassified callout in span 2
    texts += [_t("E1", "4%%C16", 5300, 2450, 300, "S2"), _t("K1", "2%%C12", 3300, 3100, 300, "S2"),
              _t("U1", "3%%C14", 7300, 2450, 300, "S2")]
    return attrs, texts, segs


def build(*, boundary_text=False, shift=(0.0, 0.0), scale=1.0):
    """attributes, texts, segments of both sheets, optionally translated (shift) and rescaled (drawing in m: 0.001)."""
    a1, t1, s1 = simple_table(boundary_text=boundary_text)
    a2, t2, s2 = continuous_table()
    attrs, texts, segs = a1 + a2, t1 + t2, s1 + s2
    sx, sy = shift

    def P(p):
        return (p[0] * scale + sx, p[1] * scale + sy)

    attrs = [dict(a, x=a["x"] * scale + sx, y=a["y"] * scale + sy) for a in attrs]
    texts = [dict(t, x=t["x"] * scale + sx, y=t["y"] * scale + sy, height=t["height"] * scale) for t in texts]
    segs = [dict(s, a=P(s["a"]), b=P(s["b"])) for s in segs]
    return attrs, texts, segs


def rows_for(attrs):
    from engine.source import schedule_reader as SR

    def sheet_of(x, y):
        return None

    S = SR.from_attribute_rows(attrs)
    sheet = {"41": "S1", "42": "S1", "43": "S1", "44": "S1", "21": "S2", "22": "S2"}
    for r in S["rows"]:
        r["sheet"] = sheet[r["source"].split()[-1]]
    return S["rows"]
