"""M7 legend reader V3 (concrete_completeness._legend_swatches, nearest=True) on adversarial hand-built legends.
States per swatch: MATCHED (one caption, one family), AMBIGUOUS (equally near captions naming different families, or
a caption naming two), NO_CAPTION. A swatch is a small fill off the building whose pattern and layer are used again
on the sheet (a pattern used once is not a legend). The V2 reader (vote over every caption within 3 m) is run beside
it where the two differ."""

from __future__ import annotations

from engine.source import concrete_completeness as CC

U = 1e-3                                                    # millimetre drawing
WORDS, _ = CC._note_words()
P = CC._p(None)
BUILDING = [{"poly": [(0, 0), (20000, 0), (20000, 15000), (0, 15000)]}]


def _fill(x, y, w=500, h=300, pattern="ANSI31", layer="S-HATCH"):
    ring = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return {"type": "HATCH", "pattern": pattern, "layer": layer, "ring": ring, "box": (x, y, x + w, y + h),
            "area": float(w * h)}


def _text(s, x, y):
    return {"norm": s, "x": x, "y": y, "height": 150.0}


def _uses():                          # the same patterns used on the plan (inside the building)
    return [_fill(2000, 2000, 3000, 2000, "ANSI31"), _fill(8000, 2000, 3000, 2000, "ANSI37")]


def _read(swatches, texts, nearest=True):
    rec = []
    out, ids = CC._legend_swatches(swatches + _uses(), BUILDING, texts, WORDS, U, P, nearest=nearest, records=rec)
    return out, rec


def test_close_rows_each_take_their_own_caption():
    sw = [_fill(25000, 10000, pattern="ANSI31"), _fill(25000, 10600, pattern="ANSI37")]       # rows 0.6 m apart
    tx = [_text("SUNKEN SLAB", 25700, 10150), _text("CANTILEVER", 25700, 10750)]
    v3, rec = _read(sw, tx)
    assert v3 == {("ANSI31", "S-HATCH"): ("SLAB_STEP", "SUNKEN SLAB"), ("ANSI37", "S-HATCH"): ("CANTILEVER", "CANTILEVER")}
    assert [r["state"] for r in rec] == ["MATCHED", "MATCHED"]
    v2, _ = _read(sw, tx, nearest=False)
    assert v2 == {}                                          # W5: both captions within 3 m of both swatches, a tie


def test_caption_on_the_left_and_a_nearer_decoy_off_the_row():
    sw = [_fill(25000, 10000)]
    tx = [_text("CANTILEVER", 23900, 10150),                 # on the row, 1.1 m to the left
          _text("LIFT PIT", 25250, 10900)]                   # nearer (0.6 m) but above the row
    v3, rec = _read(sw, tx)
    assert v3 == {("ANSI31", "S-HATCH"): ("CANTILEVER", "CANTILEVER")} and rec[0]["state"] == "MATCHED"


def test_equally_near_captions_naming_different_families_stay_ambiguous():
    sw = [_fill(25000, 10000)]
    tx = [_text("CANTILEVER", 25700, 10150), _text("SUNKEN SLAB", 24300, 10150)]   # 0.2 m right, 0.7 m left
    v3, rec = _read(sw, tx)
    assert v3 == {("ANSI31", "S-HATCH"): ("CANTILEVER", "CANTILEVER")}            # clearly nearer: matched
    tx = [_text("CANTILEVER", 25700, 10150), _text("SUNKEN SLAB", 24800, 10150)]     # 0.2 m on either side
    v3, rec = _read(sw, tx)
    assert v3 == {} and rec[0]["state"] == "AMBIGUOUS"


def test_a_caption_naming_two_families_is_ambiguous_and_no_caption_is_recorded():
    sw = [_fill(25000, 10000)]
    v3, rec = _read(sw, [_text("CANTILEVER / LIFT PIT", 25700, 10150)])
    assert v3 == {} and rec[0]["state"] == "AMBIGUOUS"
    v3, rec = _read(sw, [_text("SEE DETAIL 4", 25700, 10150)])
    assert v3 == {} and rec[0]["state"] == "NO_CAPTION"


def test_a_pattern_used_once_is_not_a_legend_and_a_fill_on_the_building_is_never_a_swatch():
    lone = _fill(25000, 10000, pattern="ANSI35")             # ANSI35 appears nowhere else
    on_plan = _fill(5000, 5000, pattern="ANSI31")             # inside the building outline
    v3, rec = _read([lone, on_plan], [_text("CANTILEVER", 25700, 10150), _text("CANTILEVER", 5600, 5150)])
    assert v3 == {} and rec == []
