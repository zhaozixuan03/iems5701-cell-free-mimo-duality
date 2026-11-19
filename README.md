# IEMS5701 cell-free MIMO reproducibility project

Reproduction and computational acceleration for [Miretti et al., IEEE TSP 2024](https://doi.org/10.1109/TSP.2024.3376809), using the [authors' official code](https://github.com/lorenzomiretti/duality). This repository contains **research code and experiment records**, not any student's individual technical report.

## What is included

- `upstream/`: an unmodified snapshot of the five files in the author's repository at commit [5a968b4](https://github.com/lorenzomiretti/duality/commit/5a968b40fa43e7d18b62641bb46073f57442f227). All five files were byte-compared with a successful clone. The authors' complete Git history is also preserved on this repository's [upstream-baseline branch](https://github.com/zhaozixuan03/iems5701-cell-free-mimo-duality/tree/upstream-baseline). File provenance is in [docs/PROVENANCE.md](docs/PROVENANCE.md).
- `experiments/run_official_figure3.py` executes the unmodified author script and saves both plots and stdout. `experiments/run_figure3.py` pairs the original and accelerated solvers on identical seeded setups; `experiments/benchmark_repeats.py` repeats this timing comparison.
- `experiments/run_official_figure2.py` instruments the unmodified author script. `experiments/finish_figure2_parallel.py` continues interrupted runs by reconstructing each setup's original NumPy random state, then schedules the remaining independent setups in parallel. It preserves the author's 8 rates, 2 CSI modes, 100 setups per rate and mode, 100 channel realizations, solver tolerances and retry sequence.
- `optimized_problem.py`: batched channel realizations and linear solves replace repeated matrix inverses in the local-CSI solver. The objective, constraints, update rule, and stopping criteria are inherited from the upstream implementation.
- `results/`: complete Figure 2 records, official Figure 3 output, paired runs, exploratory runs, logs, failures, and plots.

## Reproduce

Python 3.12 was used. In a fresh environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp
python experiments/run_official_figure3.py > results/figure3_official/run_stdout.log 2> results/figure3_official/run_stderr.log
python experiments/finish_figure2_parallel.py --workers 6
python experiments/finish_figure2_parallel.py --optimized --workers 4
python experiments/compare_full_figure2.py
python experiments/analyze_full_figure2.py
python experiments/benchmark_repeats.py
```

Run the two Figure 2 continuation commands **separately** if measuring time. They can start from an empty result folder or resume from the recorded serial/parallel attempts. The per-setup records are flushed to disk as each setup finishes. The author's unmodified Figure 2 script was also started, but the serial run was interrupted at slow edge cases; its completed setup records were retained and the remaining setups were run with restored random states. The plotted fraction uses the author's denominator of **solved setups**, not all 100 setups. Full run parameters and Python/library versions are in each result folder's `metadata_final.json`.

## Measured result

The complete Figure 2 experiment contains 1,600 setups. Both implementations marked 1,599 solved. For all 1,600 paired setups, the solved status, per-AP and sum-power feasibility, retry count, and outer iteration count agree exactly. Across shared attempts, the largest final dual-objective difference was `3.12e-7 mW` and largest final AP-power-violation difference was `2.52e-8 mW`. At 4 bit/s/Hz, the original solver's per-AP feasibility fraction among solved setups was `0.18` for local CSI and `0.43` for centralized CSI; sum-power fractions were `0.31` and `0.83`. One centralized setup at rate 2.5714 did not solve within four attempts and is excluded from the author's denominator. The full table, Wilson intervals, and plot are in `results/figure2_full/`.

The official Figure 3 script completed and saved its two original plots in `results/figure3_official/`. The final batched solver was timed on five seeds, with five repeats per seed and alternating method order. The median of the five per-seed median solve-time ratios was **7.38×** (range of individual paired ratios: 6.25–8.04×); total time across the 25 pairs was 71.02 s upstream versus 9.69 s accelerated. Every pair had identical outer and inner iteration counts. The largest dual-objective difference was `2.30e-10 mW`, and the largest final AP-power difference was `4.39e-11 mW`. See `results/figure3_repeats/` for every measurement and environment details. Timings are machine-specific repeats, not a population confidence interval. This is a **compute-time** improvement, with no claim of improved rate, feasibility, or iteration count.

Figures: [complete Figure 2 with uncertainty bands](results/figure2_full/figure2_with_ci.png), [official Figure 3 dual objective](results/figure3_official/dual_objective.png), and [official Figure 3 maximum AP power](results/figure3_official/max_power.png).

Seed 4 at kappa 10 reached the 20-iteration cap with +23.58 mW maximum AP power violation; kappa 17 also hit the cap, with -0.74 mW power gap but 26.53 mW surrogate dual gap. Neither is certified solved under the paper's stopping criterion. A negative AP-power gap alone does not certify convergence.

The author's printed final maximum SINR gaps are also retained in each run's `trace` (rounded to four decimals). Seed 6 has a +1.0349 SINR gap and is marked infeasible. See [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md) for all decisions and limitations, and the JSON/CSV files in `results/` for raw data. Run `python experiments/check_results.py` to verify the saved paired comparisons.

## Collaboration

The current work is available for inspection in a single review PR. Team members can review its commands, seed pairing, numerical checks, and claim wording before merge. Future changes can use short branches and PRs when needed. Each student writes their **own** personal report without AI-generated report text, as required by the course. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License and attribution

The author's package is GPL-2.0-only, and its original headers and full license are preserved. This derivative repository is distributed under GPL-2.0-only; see [LICENSE](LICENSE). Cite the paper in research or publication use. The course PDF is intentionally absent from this public repository.
