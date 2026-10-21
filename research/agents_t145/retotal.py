"""T-145 re-add check (research only, reads no drawing): the 13 non-slab engine faces of T-139 against their new homes.

Usage: python -I retotal.py ITEMS.csv
Checks: (1) the 13 faces re-add to the T-139 engine excess 0.686 m3 (engine slab 60.966 - hand slab 60.280);
(2) every face has a home line or a named HOLD; (3) the slab, beam and not-concrete movements in m3."""
import csv
import sys

ENGINE_SLAB, HAND_SLAB = 60.966, 60.280          # T-139 section 1 (engine route G panel table; hand 62 panels)


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 13, len(rows)
    out = sum(float(r["slab_m3_engine_today"]) for r in rows)
    print(f"13 faces leave the slab line: {out:.4f} m3 (T-139 excess {ENGINE_SLAB - HAND_SLAB:.3f})")
    assert abs(out - (ENGINE_SLAB - HAND_SLAB)) < 0.002
    by = {}
    for r in rows:
        assert r["home_line"] and r["status"] in ("CALCULATED", "HELD", "NOT_CONCRETE"), r
        if r["status"] == "HELD":
            assert r["register_ref"].startswith("BM-"), r          # a named hold, never a bare 0
        by.setdefault(r["status"], [0, 0.0, 0.0])
        by[r["status"]][0] += 1
        by[r["status"]][1] += float(r["slab_m3_engine_today"])
        by[r["status"]][2] += float(r["hand_m3"] or 0)
    for k, (n, s, h) in sorted(by.items()):
        print(f"  {k:12} {n:2} faces, slab m3 leaving {s:.4f}, hand m3 in the home line {h:.4f}"
              + ("" if k != "HELD" else " (candidate ranges stay in the beam register, never 0)"))
    beam_add = by.get("CALCULATED", [0, 0, 0])[2]
    print(f"slab line {ENGINE_SLAB:.3f} -> {ENGINE_SLAB - out:.3f} m3; beam line +{beam_add:.4f} m3 (CB5 span 2); "
          f"released concrete net {beam_add - out:+.4f} m3")


if __name__ == "__main__":
    main(sys.argv[1])
