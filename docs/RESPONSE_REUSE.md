# Reusing the local linear response

The original outer and inner iteration rules are unchanged. In the local-CSI path, the beamforming parameter calculation already solves a small linear system for each AP and channel realization. The immediately following coefficient calculation needs the same solution with the same power and dual variables. `OptimizedProblem` now reuses that response if those inputs still match. A direct call with changed inputs recomputes it.

This changes per-iteration computation, not the number of iterations or the communication model. It is separate from the adaptive-step convergence experiment.

## Paired measurements

Run with `OPENBLAS_NUM_THREADS=1` and the commands below. Seeds 4–8 were each repeated five times, alternating call order. Each pair uses the same random setup. The first command compares the prior vectorized implementation with response reuse; the second compares the official baseline with the updated implementation.

```sh
OPENBLAS_NUM_THREADS=1 python3 experiments/benchmark_response_reuse.py --output results/figure3_response_reuse
OPENBLAS_NUM_THREADS=1 python3 experiments/benchmark_repeats.py --output results/figure3_repeats_cached
```

The median of the five per-seed median runtime ratios was **1.3244×** for the incremental reuse change and **8.8991×** for the full implementation versus the official baseline. These are measured solve times on this machine and workload, not a universal performance guarantee. The reuse ablation matched all reported iteration counts and status flags; its largest final dual-objective difference was 2.101e-10 mW and largest final AP-power difference was 2.774e-11 mW. See the JSONL runs, timings, metadata, stdout, and stderr under `results/figure3_response_reuse/` and `results/figure3_repeats_cached/`.
