# Collaboration rules

1. Claim an Issue before starting a branch. Keep branches focused and name them `experiment/*`, `method/*`, or `docs/*`.
2. In every PR, state the exact command, package versions, machine/BLAS setting, seeds, input configuration, raw output path, and numerical check. Link the Issue.
3. Keep `upstream/` unchanged. Proposed changes belong in separate files so baseline comparisons stay meaningful.
4. Include incomplete runs and failures. A solver reaching its iteration limit is not “converged.” Report feasibility flags, final AP power violation, and surrogate gap separately.
5. One other team member reviews code and result interpretation before merge. The author resolves comments; reviewers do not approve their own PRs.
6. Do not commit credentials, the instructor's course PDF, or individual report drafts. Each student writes their own report as required by the course.
