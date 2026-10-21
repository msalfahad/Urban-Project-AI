"""Run the V2 CLI in-process with opening_census.face_lines replaced by the mean-axis variant (q1_angle_axis.py),
optionally with the robust face-piece margin. usage: python3 -I probe_mean_axis.py SRC PLAN OUT MODE refs...  MODE: axis | axis+face"""
import sys, io, contextlib, math
SRC, PLAN, OUT, MODE = sys.argv[1:5]; REFS = sys.argv[5:]
sys.path.insert(0, SRC)
here = __file__.rsplit("/", 1)[0]
ns = {}
src = open(f"{here}/q1_angle_axis.py").read().split("ns = {}")[0].replace("SRC = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 400", f"SRC = {SRC!r}; N = 1")
exec(src, ns)
from engine.source import opening_census as OC
fl = ns["face_lines_mean_axis"]
if MODE == "axis+face":
    def fl2(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
        return fl(segments, ang_res_deg, off_tol, join_tol, min_len * (1 - 1e-8))
    OC.face_lines = fl2
else:
    OC.face_lines = fl
from tools import urban_boq_m9 as M9
with contextlib.redirect_stdout(io.StringIO()):
    code = M9.main(["arch", "--drawings", PLAN, "--out", OUT, "--method", "ARCH_TAKEOFF_V2", "--no-svg", "--no-m9-xlsx", "--reference-areas", *REFS])
print(MODE, code)
