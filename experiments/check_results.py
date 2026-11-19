"""Check saved paired runs without re-running expensive simulations."""
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
for name in ("figure3_full_params", "figure3_kappa17", "figure3_medium",
             "figure3_scaled"):
    path = root/"results"/name/"runs.json"
    runs = json.loads(path.read_text())
    assert len(runs) % 2 == 0, path
    for baseline, optimized in zip(runs[::2], runs[1::2]):
        assert baseline["method"] == "Problem"
        assert optimized["method"] == "OptimizedProblem"
        assert baseline["seed"] == optimized["seed"]
        assert baseline["error"] is None and optimized["error"] is None
        for key in ("outer_iterations","inner_iterations","solved","feasible_flag"):
            assert baseline[key] == optimized[key], (name,key)
        assert np.allclose(baseline["dual_objective"],
                           optimized["dual_objective"], rtol=1e-10, atol=1e-7)
        assert np.allclose(baseline["per_ap_power_mw"],
                           optimized["per_ap_power_mw"], rtol=1e-10, atol=1e-7)
    print(name, len(runs)//2, "paired runs checked")
