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

## Complete Figure 2 reproduction

The unmodified `upstream/local_vs_centralized_rate.py` was started through `experiments/run_official_figure2.py` so its decisions and hidden sum-power flags could be logged. It used the author's eight rates, 100 setups for each rate and CSI mode, 100 channel realizations, per-AP limit 1000 mW, kappa retries 10/30/90/270, and original tolerances. Sequential execution became slow on a few boundary setups. Both serial runs were interrupted deliberately; partial logs and interruption notes remain in `results/figure2_full/` and `results/figure2_full_optimized/`.

`experiments/finish_figure2_parallel.py` reconstructed the exact NumPy state immediately before each original setup by replaying the author's sequential Problem constructions. Solver execution itself does not draw random numbers. Independent unfinished setups were then scheduled in parallel, with all original solver calls and retry rules unchanged. Already completed serial setup records were retained. The last serial setup was rerun to avoid including a partially interrupted record. Exact setup IDs 1, 420, and 690 were separately checked against the serial records before the full continuation; flags and iteration counts matched, and final dual values differed by at most `3.6e-12 mW` in those spot checks.

The full run completed all **1600** setups for both methods. Both marked **1599 solved**. Every setup matched between original and optimized methods for solved status, per-AP and sum-power feasibility, final retry number, and outer iteration count. The largest difference across shared attempts was `3.1147e-7 mW` in final dual objective and `2.5239e-8 mW` in final AP-power violation. These are numerical differences, not feasibility changes. The single unsolved case was setup 570, rate 2.5714, centralized CSI, after all four attempts. Following the author's script, its classification is excluded from that curve's denominator (99 rather than 100). At rate 4, the original per-AP probabilities were 0.18 local and 0.43 centralized; sum-power probabilities were 0.31 and 0.83. `summary.csv`, `summary_with_ci.csv`, `figure2_full.png`, `figure2_with_ci.png`, individual attempt records and logs contain the complete evidence. Wilson bands show sampling uncertainty; 100 setups per rate are still finite Monte Carlo estimates.

## Final acceleration test

The initial 1.73× result in `results/figure3_full_params/` predates batched equivalent-channel calculations. The final implementation batches the local-CSI covariance and channel calculations over 100 channel realizations and replaces inverse-multiply operations with linear solves. It retains the author's objective, update rules, constraints, and stopping criteria. Centralized CSI uses the inherited original routines.

`experiments/benchmark_repeats.py` timed five Figure 3 parameter-matched seeds (4–8) five times each, alternating method order. Each paired run saw the same seeded setup. All 25 pairs had equal outer and inner iteration counts and equal solver outcomes. The median of per-seed median solve-time ratios was **7.3811×**; individual pair ratios were 6.2478–8.0390×. Total solve time across pairs was 71.0221 s original versus 9.6862 s optimized. The largest absolute dual-objective difference was `2.2919e-10 mW` and final AP-power difference was `4.3883e-11 mW`. Timing is specific to macOS arm64, Python 3.12.2, NumPy 1.26.4, SciPy 1.17.1, and one OpenBLAS thread; it is not evidence of iteration-count improvement or hardware-independent acceleration. Raw timing, seed order, parity metrics and environment are saved in `results/figure3_repeats/`.

The second Figure 3 step size, kappa 17, was also rerun with the final implementation on seed 4 (`results/figure3_vectorized_kappa17/`). Both methods used 20 outer and 150 inner iterations, reached the cap, and had the same feasibility and solved flags. Solve times in this single pair were 9.7556 s original and 1.2024 s optimized; this one pair is not used in the repeated timing estimate. Final AP power violation differed by `4.32e-12 mW`.

## Interpretation and limitations

The acceleration preserves observed outputs and iteration counts at tested seeds and improves solve time in this environment. It has no demonstrated convergence-iteration gain. Feasibility is a property of the original optimization outcome, not of this algebraic speedup. Seed 4's 20-iteration Figure 3 curves are informative traces but not certified converged. The original inner fixed-point loop has no iteration cap, so harder new seeds may require an external runtime limit. Independent checks on other hardware and with different numerical libraries remain useful. The project provides code, data, and experimental decisions; each student must write their own technical report text under the course restriction.
