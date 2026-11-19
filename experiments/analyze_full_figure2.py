"""Add binomial Wilson intervals to the completed official Figure 2 run."""
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figure2_full"


def wilson(successes, n, z=1.959963984540054):
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return max(0, center-half), min(1, center+half)


rows = list(csv.DictReader((OUT/"summary.csv").open()))
if len(rows) != 16 or any(int(r["setups"]) != 100 for r in rows):
    raise RuntimeError("Full 8 x 2 x 100 Figure 2 run is not complete")
for row in rows:
    n = int(row["solved"])
    for prefix, count in (("per_ap", "per_ap_feasible"),
                          ("sum", "sum_feasible")):
        lo, hi = wilson(int(row[count]), n)
        row[prefix+"_ci_low"] = lo
        row[prefix+"_ci_high"] = hi
with (OUT/"summary_with_ci.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

fig, ax = plt.subplots(figsize=(8, 4.8))
styles = [(("local","per_ap"),"tab:blue","-o"),
          (("local","sum"),"tab:blue","--o"),
          (("centr","per_ap"),"tab:red","-s"),
          (("centr","sum"),"tab:red","--s")]
for (csi, prefix), color, style in styles:
    data = sorted((r for r in rows if r["csi"] == csi),
                  key=lambda r: float(r["rate"]))
    x = [float(r["rate"]) for r in data]
    y = [int(r[prefix+"_feasible"])/int(r["solved"]) for r in data]
    lo = [float(r[prefix+"_ci_low"]) for r in data]
    hi = [float(r[prefix+"_ci_high"]) for r in data]
    ax.plot(x,y,style,color=color,label=f"{csi} {prefix}")
    ax.fill_between(x,lo,hi,color=color,alpha=0.10)
ax.set(xlabel="Minimum rate (bit/s/Hz)",
       ylabel="Feasibility fraction among solved setups",
       ylim=(-0.03,1.03),
       title="Official Figure 2 run with 95% Wilson intervals")
ax.grid(True)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT/"figure2_with_ci.png",dpi=180)
