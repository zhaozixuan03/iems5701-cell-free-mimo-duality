"""Plot the two original Figure 3 step sizes from saved, real runs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parents[1]
paths = {10: root/"results/figure3_full_params/runs.json",
         17: root/"results/figure3_kappa17/runs.json"}
out = root/"results/figure3_paper_pair"
out.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for kappa, path in paths.items():
    runs = json.loads(path.read_text())
    run = next(r for r in runs if r["seed"] == 4 and r["method"] == "Problem")
    iterations = range(1, len(run["dual_objective"])+1)
    axes[0].plot(iterations, 10*np.log10(run["dual_objective"]), label=f"kappa={kappa}")
    # The author's routine stores all AP powers per outer iteration only in stdout.
    # Parse max power from the power gap, which is max(P_AP-P_max).
    power = [1000 + x["power_gap"] for x in run["trace"]]
    axes[1].plot(iterations, 10*np.log10(power), label=f"kappa={kappa}")
for ax, ylabel in zip(axes, ("Dual objective (dBm)", "Maximum AP power (dBm)")):
    ax.set_xlabel("Outer iteration")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend()
fig.suptitle("Figure 3 reproduction: original solver, seed 4")
fig.tight_layout()
fig.savefig(out/"figure3_pair.png", dpi=180)
