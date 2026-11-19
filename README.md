# IEMS5701 cell-free MIMO reproducibility project

Reproduction and computational acceleration for [Miretti et al., IEEE TSP 2024](https://doi.org/10.1109/TSP.2024.3376809), using the [authors' official code](https://github.com/lorenzomiretti/duality). This repository contains **research code and experiment records**, not any student's individual technical report.

## What is included

- `upstream/`: an unmodified snapshot of the five files in the author's repository at commit [5a968b4](https://github.com/lorenzomiretti/duality/commit/5a968b40fa43e7d18b62641bb46073f57442f227). The sandbox could not run `git clone` because its network proxy was unavailable; the files were retrieved via the connected GitHub reader. File provenance is in [docs/PROVENANCE.md](docs/PROVENANCE.md).
- `experiments/run_figure3.py`: paired baseline versus optimized solver on identical seeded setups, saving raw logs, parameters, timings, iteration counts, objective trajectories, and final AP power violations.
- `optimized_problem.py`: an algebraically equivalent computational improvement: batched channel realizations and linear solves replace repeated matrix inverses. The upstream objective, constraints, update rule, and stopping criteria remain unchanged.
- `experiments/run_figure2.py`: a **reduced** Figure 2 feasibility experiment, not the paper's 100-setup Monte Carlo estimate.
- `results/`: all trial output, including exploratory scaled runs and runs that did not converge within the iteration cap.

## Reproduce

Python 3.12 was used. In a fresh environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp
python experiments/run_figure3.py --seeds 4 5 6 7 8 --L 16 --K 16 --N 4 --Q 4 --n-sim 100 --size 1000 --tol-psg 0.1 --output results/figure3_full_params
python experiments/run_figure3.py --seeds 4 --L 16 --K 16 --N 4 --Q 4 --n-sim 100 --size 1000 --tol-psg 0.1 --kappa 17 --output results/figure3_kappa17
python experiments/plot_figure3_pair.py
python experiments/run_figure2.py --seeds 0 1 2 --rates 2 3 4 --n-sim 20 --max-outer 20 --attempts 2
```

The first two commands reproduce a **Figure 3 parameter-matched subset**: seed 4 with both original step sizes, plus four more seeds at kappa 10. Figure 2 uses only 3 setups per rate, 3 rate points, 20 channel samples, and 2 retries, so its fractions have large Monte Carlo uncertainty. The authors' original scripts are preserved for exact-paper reruns.

## Measured result

On this machine with one BLAS thread, five paired Figure 3 seeds at kappa 10 used the same outer/inner iteration counts and produced at most `2.43e-10` absolute difference in dual objective and `2.94e-11 mW` in final AP powers. Total solver time was 14.08 s for the upstream routine and 8.13 s for the optimized routine (1.73× ratio). The per-seed ratio was 1.71–1.79×. This is a **compute-time improvement**, not a new rate or feasibility gain. Timings depend on hardware and library versions; these are one-run-per-seed measurements, not confidence intervals.

Seed 4 at kappa 10 reached the 20-iteration cap with +23.58 mW maximum AP power violation; kappa 17 also hit the cap, with -0.74 mW power gap but 26.53 mW surrogate dual gap. Neither is certified solved under the paper's stopping criterion. Do not count these as feasible merely because the power gap is small or negative.

The author's printed final maximum SINR gaps are also retained in each run's `trace` (rounded to four decimals). Seed 6 has a +1.0349 SINR gap and is marked infeasible. See [docs/EXPERIMENT_LOG.md](docs/EXPERIMENT_LOG.md) for all decisions and limitations, and the JSON/CSV files in `results/` for raw data. Run `python experiments/check_results.py` to verify the saved paired comparisons.

## Team workflow

Use three roles that can rotate:

1. **Reproduction owner:** verify the model and exact Figure 2/3 settings, expand seeds and check figures against the paper.
2. **Method owner:** inspect the optimization, profile bottlenecks, propose one further algorithmic idea, and independently verify constraints.
3. **Validation and presentation owner:** audit raw logs and statistical claims, prepare the group mini-lecture and Q&A. Each student writes their **own** personal report without AI-generated report text, as required by the course.

For each task, open an Issue with a specific acceptance criterion. Create a short branch (for example `experiment/figure2-more-seeds`), commit code and raw results together, then open a PR. Another member should review the commands, seed pairing, numerical checks, and claim wording before merge. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [initial Issue plan](docs/ISSUES_TO_CREATE.md).

## License and attribution

The author's package is GPL-2.0-only, and its original headers and full license are preserved. This derivative repository is distributed under GPL-2.0-only; see [LICENSE](LICENSE). Cite the paper in research or publication use. The course PDF is intentionally absent from this public repository.
