"""Execute the unmodified author Figure 3 script and save both plots."""
import json
import os
import platform
import runpy
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream"
OUT = ROOT / "results" / "figure3_official"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(UPSTREAM))
started = time.time()


def saved_show(*args, **kwargs):
    for number, name in zip(plt.get_fignums(), ("dual_objective", "max_power")):
        plt.figure(number).savefig(OUT / f"{name}.png", dpi=180,
                                   bbox_inches="tight")


plt.show = saved_show
status = "completed"
error = None
try:
    runpy.run_path(str(UPSTREAM / "algorithm_convergence.py"), run_name="__main__")
except BaseException as exc:
    status = "failed"
    error = repr(exc)
    raise
finally:
    (OUT / "metadata.json").write_text(json.dumps({
        "status": status, "error": error, "started_unix": started,
        "finished_unix": time.time(),
        "official_script": "upstream/algorithm_convergence.py",
        "official_git_commit": "5a968b40fa43e7d18b62641bb46073f57442f227",
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    }, indent=2))
