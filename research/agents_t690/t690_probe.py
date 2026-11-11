"""T-690 own probe (d): the MS2-TR closing-step edge in the dog-leg shaft's north turn zone, per plan.

Prints only RELATIVE geometry (metres from the west tread set's west end / first line), layer, linetype, length and
angle; no absolute coordinate and no drawing text. Reuses only the merged T-684 entity flattener and tread-set finder
(research/agents_t684/t684_probe.py: flat, vertical_sets, plan_of); the selection and the reading below are this run's.
    bash scripts/agent_env.sh run --tree task-T-690 research/agents_t690/t690_probe.py --arch <P7757.dxf>
"""
from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t684"))
import ezdxf  # noqa: E402
from t684_probe import flat, plan_of, vertical_sets  # noqa: E402


def main(argv):
    path = argv[argv.index("--arch") + 1]
    print("arch sha256", hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8])
    doc = ezdxf.readfile(path)
    segs, titles = flat(doc)
    sets = vertical_sets(segs)
    for w in sets:
        for e in sets:
            dx = e[0] - w[0]
            if not 1200 <= dx <= 1400 or plan_of(titles, w[0]) != plan_of(titles, e[0]):
                continue
            plan = plan_of(titles, w[0])
            ytop = max(w[2][-1], e[2][-1])
            print(f"\n== {plan}: west set {len(w[2])} tread lines (pitch {(w[2][-1]-w[2][0])/1000/(len(w[2])-1):.3f}), "
                  f"east set {len(e[2])}; west lane x 0 .. {(w[1]-w[0])/1000:.3f}, east lane x {dx/1000:.3f} .. "
                  f"{(e[1]-w[0])/1000:.3f}; north end of the longer set y {(ytop-w[2][0])/1000:.3f}")
            # every N-S (vertical) segment >= 0.5 m on any layer in the west lane's north square
            rows = set()
            for lay, lt, sa, sb, sc, sd, t in segs:
                ln = math.hypot(sc - sa, sd - sb)
                if ln < 500 or abs(sc - sa) > 1:
                    continue
                x = (sa - w[0]) / 1000
                y0, y1 = sorted(((sb - w[2][0]) / 1000, (sd - w[2][0]) / 1000))
                if -0.40 <= x <= (w[1] - w[0]) / 1000 + 0.40 and y1 >= (ytop - w[2][0]) / 1000 - 0.05 \
                        and y0 <= (ytop - w[2][0]) / 1000 + 1.60:
                    rows.add((lay, lt, t, round(x, 3), round(y0, 3), round(y1, 3), round(ln / 1000, 3)))
            print("  N-S segments >= 0.5 m in the west lane's north square (layer, linetype, type, x, y0, y1, len):")
            for r in sorted(rows, key=lambda r: (r[3], r[0])):
                print("    ", r)
            # E-W segments in the same square (the north wall face and the last tread line)
            rows = set()
            for lay, lt, sa, sb, sc, sd, t in segs:
                ln = math.hypot(sc - sa, sd - sb)
                if ln < 500 or abs(sd - sb) > 1:
                    continue
                y = (sb - w[2][0]) / 1000
                xa, xb = sorted(((sa - w[0]) / 1000, (sc - w[0]) / 1000))
                if (ytop - w[2][0]) / 1000 - 0.05 <= y <= (ytop - w[2][0]) / 1000 + 1.60 and xb >= -0.4 \
                        and xa <= (w[1] - w[0]) / 1000 + 0.4:
                    rows.add((lay, lt, t, round(y, 3), round(xa, 3), round(xb, 3), round(ln / 1000, 3)))
            print("  E-W segments >= 0.5 m there (layer, linetype, type, y, x0, x1, len):")
            for r in sorted(rows, key=lambda r: (r[3], r[0])):
                print("    ", r)


if __name__ == "__main__":
    main(sys.argv[1:])
