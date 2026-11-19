# Initial Issues for a three-person team

Create these as GitHub Issues after the new repository is available. Assign owners by GitHub username once all three collaborators have joined.

## 1. Extend Figure 2 Monte Carlo reproduction

Owner: reproduction member. Run the author's full 100 setups across all 8 rates and both CSI modes, or document a justified compute budget. Save per-setup outcomes, unsolved count, exact command, package versions, random seed policy, and confidence intervals. Compare the output to paper Figure 2 without claiming a visual match from the current 3-seed sample. Reviewer: validation member.

## 2. Stress test linear-solve acceleration

Owner: method member. Profile local and centralized CSI, repeat timings to estimate variability, try more seeds and sample counts, and verify objective/power parity and stopping outcomes. Investigate the seed-4 cap and seed-6 SINR infeasibility; do not change baseline settings during comparison. Reviewer: reproduction member.

## 3. Prepare group mini-lecture and independent checks

Owner: validation/presentation member. Independently inspect the paper's definitions of power and information constraints, audit the JSON logs against plots, prepare a group presentation outline and Q&A list, and collect each member's questions. Do not generate or commit any student's personal technical report prose. Reviewer: method member.
