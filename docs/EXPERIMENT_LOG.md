# Experiment and decision log

Date: 2026-11-19 (Asia/Hong_Kong).

## Requirements and source audit

The IEMS5701 course project asks for paper reproduction plus a new idea supported by simulations; the individual technical report must be written by each student without generative-AI prose. The authors link Figure 2 to `local_vs_centralized_rate.py` and Figure 3 to `algorithm_convergence.py`. The source code has GPLv2 headers and a license file. Only NumPy, SciPy, and Matplotlib are imported by the official code; there is no package manifest upstream.

## Environment and failed starts

- The initial shell `git clone` failed because the configured 127.0.0.1:1086 proxy was unreachable. Removing the proxy inside the restricted command environment did not help. A connected GitHub reader supplied the exact five-file snapshot. A later direct-network clone succeeded; all five files were byte-compared and the complete official history was pushed as `upstream-baseline`.
- `gh auth status` showed an invalid CLI credential; `gh auth login --web` failed at the proxy before receiving a device code. The user created the new public repository in their browser. Direct-network `git push` succeeded using the machine's Git credential helper. Three workflow Issues were created prematurely and then closed as not planned after the user clarified that the priority is full reproduction and optimization. PR #4 remains open for code review. The connected GitHub API reader had read access but returned 403 for write calls.
- Homebrew Python 3.13 lacked NumPy. Experiments used the installed Python 3.12 at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`.
- The first Matplotlib import warned that its default cache was not writable; runs use `MPLCONFIGDIR=/tmp`. Fontconfig printed a cache warning on the first smoke run; plots were generated and inspected.

## Improvement hypothesis

The local TMMSE routine repeatedly forms explicit matrix inverses and loops over channel realizations. Replacing inverse-multiply operations with linear solves, and batching the covariance calculation across realizations, should reduce computation while preserving the mathematical iteration. This is a computational acceleration; it does not claim a new beamforming objective or better radio performance.

## Run sequence

1. Smoke test, L=4, K=4, N=2, 3 channel samples, seed 4: original solver ran and solved in one outer iteration. No scientific claim from this tiny check.
2. Exploratory `results/figure3_scaled`, L=4/K=6/N=2/Q=2/10 samples, seeds 4–8: both versions finished in one outer iteration each. Good functional check, weak timing evidence.
3. Exploratory `results/figure3_medium`, L=16/K=16/N=4/Q=4/20 samples, seeds 4–6: identical iterations and outcomes. Seed 4 reached the 20-iteration cap.
4. Main `results/figure3_full_params`, author's Figure 3 physical dimensions and 100 samples, kappa 10, seeds 4–8: all five paired runs completed without exceptions. Outer/inner counts match for each pair: 20/149, 1/16, 1/5, 2/52, 1/12. Upstream versus optimized total solver time: 14.0814 s versus 8.1296 s; median paired solver time: 0.9315 s versus 0.5321 s. Paired ratios are 1.71–1.79×. Absolute objective differences are at most 2.43e-10, final AP power differences at most 2.94e-11 mW. These time observations are limited to one Mac/Python environment and one timed run per seed.
5. `results/figure3_kappa17`, seed 4 with original paper's second step size: 20/150 outer/inner iterations in both implementations. Original versus optimized solve time: 9.0754 s versus 5.3198 s. Both reached the cap. The original's final maximum AP power gap is -0.7397 mW, but its surrogate dual gap is +26.5254 mW, above the 0.1 mW stopping tolerance.
6. `results/figure3_paper_pair/figure3_pair.png` plots the original solver's kappa 10 and 17 seed-4 trajectories. The maximum power trace was recovered from the original printed max-power gap, rounded by the author's print format to 4 decimals.
7. Reduced `results/figure2_scaled`: 3 seeds per rate, rates 2/3/4, both local and centralized CSI, 20 channel samples and 20 outer iterations max per attempt. At rate 4, per-AP feasibility was 1/3 local and 2/3 centralized; sum-power feasibility was 1/3 local and 3/3 centralized. All 18 cases were marked solved. These tiny fractions are illustrative only and **cannot** stand in for the paper's 100-setup Figure 2.

The author's progress print reports maximum SINR gap rounded to four decimals. The final gap for seed 6, kappa 10, is +1.0349, consistent with its infeasible flag. Full-precision final SINR vectors are not retained by the upstream solver.

After the runs, the saved Figure 3 JSON/CSV summaries were augmented from their already captured stdout traces with `final_sinr_gap_reported`; the simulations and timings were not rerun. The reduced Figure 2 experiment was rerun with identical parameters to add an explicit `environment.json`; all 18 solved/feasible outcomes matched the initial run.

## Interpretation and remaining work

The acceleration preserves observed outputs and iteration counts at tested seeds, and improved solve time in this environment. It has no demonstrated convergence-iteration gain; that should not be claimed. Feasibility is a property of the original optimization outcome, not of this algebraic speedup. Seed 4's 20-iteration Figure 3 curves are informative traces but not certified converged. The original inner fixed-point loop has no iteration cap, so harder new seeds may require an external runtime limit. More seeds, repeated timing trials, full Figure 2 Monte Carlo, independent checks of numerical tolerance and other hardware are worthwhile future checks.
