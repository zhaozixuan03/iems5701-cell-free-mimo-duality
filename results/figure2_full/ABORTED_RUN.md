# Interrupted preliminary launch

The files `upstream_stdout.log` and `upstream_stderr.log` came from an initial direct run of the unmodified author script. It was interrupted deliberately while still running, after a logged setup in the second rate point, because that launch did not save the hidden `feasible_sum` flags or the plot under the noninteractive backend.

The complete instrumented run writes `run_stdout.log`, `run_stderr.log`, `attempts.jsonl`, `summary.csv`, `metadata.json`, and `figure2_official.png`. The observation wrappers do not change the author's RNG calls or solver parameters.
